"""CIE-LAB nearest-neighbour palette locking, ordered dithering and hard alpha.

All shipped assets pass through :func:`lock_palette`, which guarantees the two
hard acceptance rules of the project:

* every opaque pixel colour is one of the 64 master-palette entries;
* alpha is exactly 0 or 255 (no semi-transparent pixels anywhere).
"""
from __future__ import annotations

import numpy as np
from PIL import Image

from config.pipeline_config import BAYER4, PALETTE_HEX, RAMP_SIZE


# ----------------------------------------------------------------------------
# Colour space helpers (sRGB D65 <-> CIE-LAB), vectorised numpy implementation.
# ----------------------------------------------------------------------------
_RGB2XYZ = np.array(
    [
        [0.4124564, 0.3575761, 0.1804375],
        [0.2126729, 0.7151522, 0.0721750],
        [0.0193339, 0.1191920, 0.9503041],
    ]
)
_WHITE = np.array([0.95047, 1.00000, 1.08883])


def _srgb_to_linear(rgb: np.ndarray) -> np.ndarray:
    rgb = rgb.astype(np.float64) / 255.0
    return np.where(rgb <= 0.04045, rgb / 12.92, ((rgb + 0.055) / 1.055) ** 2.4)


def _f(t: np.ndarray) -> np.ndarray:
    delta = 6.0 / 29.0
    return np.where(t > delta**3, np.cbrt(t), t / (3 * delta**2) + 4.0 / 29.0)


def rgb_to_lab(rgb: np.ndarray) -> np.ndarray:
    """rgb: (..., 3) uint8/float in 0..255 -> (..., 3) float64 LAB."""
    shape = rgb.shape
    flat = np.asarray(rgb, dtype=np.float64).reshape(-1, 3)
    lin = _srgb_to_linear(flat)
    xyz = lin @ _RGB2XYZ.T
    xyz = xyz / _WHITE
    f = _f(xyz)
    lab = np.empty_like(f)
    lab[:, 0] = 116.0 * f[:, 1] - 16.0
    lab[:, 1] = 500.0 * (f[:, 0] - f[:, 1])
    lab[:, 2] = 200.0 * (f[:, 1] - f[:, 2])
    return lab.reshape(shape)


def hex_to_rgb(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))


def rgb_to_hex(rgb) -> str:
    r, g, b = (int(round(float(v))) for v in rgb[:3])
    return f"#{r:02X}{g:02X}{b:02X}"


PALETTE_RGB = np.array([hex_to_rgb(h) for h in PALETTE_HEX], dtype=np.uint8)
PALETTE_LAB = rgb_to_lab(PALETTE_RGB)


def nearest_palette_indices(rgb: np.ndarray, palette_lab: np.ndarray | None = None) -> np.ndarray:
    """Map (..., 3) colours to palette indices by nearest LAB distance."""
    lab = palette_lab if palette_lab is not None else PALETTE_LAB
    flat = np.asarray(rgb, dtype=np.float64).reshape(-1, 3)
    lab_px = rgb_to_lab(flat)
    # (N, 1, 3) - (1, P, 3) -> (N, P, 3)
    d = lab_px[:, None, :] - lab[None, :, :]
    dist = np.einsum("npk,npk->np", d, d)
    return np.argmin(dist, axis=1)


def quantize_rgb(rgb: np.ndarray, palette_lab: np.ndarray | None = None) -> np.ndarray:
    """Return palette-snapped RGB image with the same leading shape."""
    rgb = np.asarray(rgb)
    idx = nearest_palette_indices(rgb, palette_lab)
    out = PALETTE_RGB[idx]
    return out.reshape(rgb.shape).astype(np.uint8)


def bayer_threshold(shape: tuple[int, int], strength: float = 1.0) -> np.ndarray:
    """4x4 Bayer ordered-dither threshold map in [0,1) for the given shape."""
    b = np.array(BAYER4, dtype=np.float64) / 16.0
    tiles_y = int(np.ceil(shape[0] / 4))
    tiles_x = int(np.ceil(shape[1] / 4))
    tiled = np.tile(b, (tiles_y, tiles_x))[: shape[0], : shape[1]]
    return 0.5 + (tiled - 0.5) * float(np.clip(strength, 0, 1))


# ----------------------------------------------------------------------------
# Palette ladder helpers (ramp-aware shading)
# ----------------------------------------------------------------------------
def ramp_of(index: int) -> tuple[int, int]:
    base = (int(index) // RAMP_SIZE) * RAMP_SIZE
    return base, base + RAMP_SIZE - 1


def shade_index(index: int, steps: int) -> int:
    """Move an index up/down its own hue ramp by ``steps`` shades."""
    lo, hi = ramp_of(index)
    return int(np.clip(int(index) + int(steps), lo, hi))


def shade_rgb(rgb: np.ndarray, steps: int) -> np.ndarray:
    """Palette-aware darken (negative steps) / lighten (positive steps)."""
    rgb = np.asarray(rgb)
    idx = nearest_palette_indices(rgb)
    lo = (idx // RAMP_SIZE) * RAMP_SIZE
    hi = lo + RAMP_SIZE - 1
    new = np.clip(idx + steps, lo, hi)
    return PALETTE_RGB[new].reshape(rgb.shape)


def darkest_of_ramp(rgb: np.ndarray, steps: int = 2) -> np.ndarray:
    return shade_rgb(rgb, -abs(steps))


# ----------------------------------------------------------------------------
# Hard alpha + palette lock
# ----------------------------------------------------------------------------
def binarize_alpha(alpha: np.ndarray, threshold: int = 128) -> np.ndarray:
    a = np.asarray(alpha)
    return np.where(a >= threshold, 255, 0).astype(np.uint8)


def lock_palette(img: Image.Image, alpha_threshold: int = 128) -> Image.Image:
    """Snap an RGBA image to palette P and force binary alpha."""
    rgba = np.array(img.convert("RGBA"))
    alpha = binarize_alpha(rgba[..., 3], alpha_threshold)
    rgb = quantize_rgb(rgba[..., :3])
    out = np.dstack([rgb, alpha])
    # PLAN hard metric 1 is literal: *every* pixel colour must belong to P,
    # including fully transparent pixels.  Use the first palette colour as the
    # canonical transparent RGB instead of (0,0,0), which is off-palette.
    out[alpha == 0, :3] = PALETTE_RGB[0]
    return Image.fromarray(out.astype(np.uint8), "RGBA")


def palette_violations(img) -> tuple[int, int]:
    """Return (n_partial_alpha, n_off_palette_pixels).

    The off-palette count covers *all* pixels, transparent included, matching
    PLAN hard metric 1's "every pixel colour is in P" wording.
    """
    if not isinstance(img, Image.Image):
        img = Image.fromarray(np.asarray(img), "RGBA")
    rgba = np.array(img.convert("RGBA"))
    alpha = rgba[..., 3]
    partial = int(np.count_nonzero((alpha > 0) & (alpha < 255)))
    rgb = rgba[..., :3].reshape(-1, 3)
    if rgb.size == 0:
        return partial, 0
    idx = nearest_palette_indices(rgb)
    snapped = PALETTE_RGB[idx]
    off = int(np.count_nonzero(np.any(snapped != rgb, axis=-1)))
    return partial, off


def palette_unique_colors(img: Image.Image) -> list[str]:
    rgba = np.array(img.convert("RGBA"))
    mask = rgba[..., 3] == 255
    cols = np.unique(rgba[..., :3][mask].reshape(-1, 3), axis=0)
    return [rgb_to_hex(c) for c in cols]
