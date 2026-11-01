"""Core-window mode pooling (PLAN 1.3).

Turns an anti-aliased, grid-shifted generative image into a clean true-pixel
sprite: every output pixel is chosen by a majority vote of the central core
window of its cell, background cells become transparent, and the surviving
colour is snapped to the master palette.
"""
from __future__ import annotations

import numpy as np
from PIL import Image
from scipy import ndimage

from config.pipeline_config import BG_TOL_LAB, BG_VOTE_RATIO, CORE_WINDOW_RATIO
from core.palette_quantizer import (
    PALETTE_LAB,
    PALETTE_RGB,
    lock_palette,
    nearest_palette_indices,
    rgb_to_lab,
)


def estimate_background(img: Image.Image) -> np.ndarray:
    """Detect the dominant border colour (robust to slight API colour drift)."""
    arr = np.array(img.convert("RGB"))
    h, w, _ = arr.shape
    ring = np.concatenate(
        [
            arr[:4].reshape(-1, 3),
            arr[-4:].reshape(-1, 3),
            arr[:, :4].reshape(-1, 3),
            arr[:, -4:].reshape(-1, 3),
        ]
    )
    q = (ring // 8) * 8
    values, counts = np.unique(q, axis=0, return_counts=True)
    return values[int(np.argmax(counts))].astype(np.float64) + 4.0


def background_mask(rgb: np.ndarray, bg_rgb: np.ndarray, tol: float = BG_TOL_LAB) -> np.ndarray:
    """Near-background pixels connected to the image border."""
    lab = rgb_to_lab(rgb)
    dist = np.linalg.norm(lab - rgb_to_lab(bg_rgb.reshape(1, 3)), axis=-1)
    near = dist < tol
    # Magenta chroma-key spill: anti-aliased sprite edges blended with #FF00FF
    # are not within the LAB tolerance yet still read as violet once quantised.
    # Their red/blue-vs-green signature identifies them reliably.
    bg = np.asarray(bg_rgb).reshape(3)
    if bg[0] > 180 and bg[2] > 180 and bg[1] < 80:
        rf = rgb.astype(np.int32)
        affinity = np.minimum(rf[..., 0], rf[..., 2]) - rf[..., 1]
        near = near | (affinity > 70)
    labels, n = ndimage.label(near)
    if n == 0:
        return np.zeros(near.shape, dtype=bool)
    border = np.concatenate([labels[0], labels[-1], labels[:, 0], labels[:, -1]])
    keep = set(int(v) for v in np.unique(border) if v != 0)
    if not keep:
        return np.zeros(near.shape, dtype=bool)
    lut = np.zeros(n + 1, dtype=bool)
    lut[list(keep)] = True
    return lut[labels]


def background_mask_all(rgb: np.ndarray, bg_rgb: np.ndarray,
                        tol: float = BG_TOL_LAB, affinity: int = 60) -> np.ndarray:
    """Background mask for *every* background-coloured pixel, not only the
    border-connected ones.

    The old border flood was the right first pass, but a magenta pocket trapped
    inside a silhouette (between an arm and the torso, under a blade, between
    hair strands) survived and became an opaque purple block after pooling.
    This version marks the key colour anywhere in the frame; the character
    matting then uses foreground coverage, so thin blades/limbs survive.
    """
    bg = np.asarray(bg_rgb, dtype=np.float64).reshape(3)
    lab = rgb_to_lab(rgb)
    near = np.linalg.norm(lab - rgb_to_lab(bg.reshape(1, 3)), axis=-1) < tol
    if bg[0] > 180 and bg[2] > 180 and bg[1] < 90:
        r = rgb.astype(np.int16)
        near |= (np.minimum(r[..., 0], r[..., 2]) - r[..., 1]) > affinity
    return near


def remove_detached_specks(alpha: np.ndarray, min_area: int = 6,
                           near: int = 2) -> np.ndarray:
    """Drop tiny detached specks but keep blades, hair strands and gear.

    ``remove_small_components`` used a flat area threshold (24 px), which
    deleted the 1px katana blade and thin hair locks.  A component is kept if
    it is large enough, elongated, or close to the main body; only genuinely
    isolated tiny blobs are removed.
    """
    lab, n = ndimage.label(alpha)
    if n <= 1:
        return alpha
    sizes = np.bincount(lab.ravel())
    sizes[0] = 0
    main = int(np.argmax(sizes))
    main_mask = lab == main
    near_main = ndimage.binary_dilation(main_mask, iterations=near)
    out = alpha.copy()
    for k in range(1, n + 1):
        if k == main:
            continue
        comp = lab == k
        area = int(sizes[k])
        if area < min_area:
            out[comp] = False
            continue
        if near_main[comp].any():
            continue
        ys, xs = np.nonzero(comp)
        diag = float(np.hypot(xs.max() - xs.min() + 1, ys.max() - ys.min() + 1))
        if diag < 6:
            out[comp] = False
    return out


def resample_sprite_coverage(img: Image.Image, target: tuple[int, int],
                             bg_rgb: np.ndarray | None = None,
                             alpha_threshold: float = 0.18) -> Image.Image:
    """Coverage-based character resampler (for thin limbs / blades).

    The generic core-window mode pool marks a cell transparent when >50% of the
    core window is background, which erases a 1-2px blade, a forearm or a hair
    lock.  Here alpha is the *foreground coverage* of the whole cell, and RGB is
    the mode of the **foreground** pixels only.  All key-coloured pixels are
    excluded, including trapped pockets not connected to the border.
    """
    rgb_img = img.convert("RGB")
    tw, th = target
    if rgb_img.width % tw or rgb_img.height % th:
        raise ValueError(f"non-integer cell size for {rgb_img.size} -> {target}")
    rgb = np.array(rgb_img)
    h, w = rgb.shape[:2]
    M = w // tw
    if M != h // th:
        raise ValueError(f"non-square cells: {M}x{h // th}")

    bg = estimate_background(rgb_img) if bg_rgb is None else np.asarray(bg_rgb, dtype=np.float64)
    bgmask = background_mask_all(rgb, bg)
    fg = ~bgmask

    fg_blocks = _blocks(fg, M)                       # (th, tw, M, M)
    cov = fg_blocks.mean(axis=(2, 3))
    alpha = cov >= alpha_threshold

    n_cells = th * tw
    idx = nearest_palette_indices(rgb.reshape(-1, 3), PALETTE_LAB).reshape(h, w)
    idx_blocks = _blocks(idx, M).reshape(n_cells, -1)
    fg_flat = fg_blocks.reshape(n_cells, -1)
    counts = np.zeros((n_cells, len(PALETTE_RGB)), dtype=np.int32)
    cell_ids = np.repeat(np.arange(n_cells), idx_blocks.shape[1]).reshape(n_cells, -1)
    np.add.at(counts, (cell_ids[fg_flat], idx_blocks[fg_flat]), 1)
    out_idx = np.argmax(counts, axis=1)

    out_rgb = PALETTE_RGB[out_idx].reshape(th, tw, 3).copy()
    out_alpha = np.where(alpha, 255, 0).astype(np.uint8)

    # Reject cells whose only surviving foreground is magenta/background spill.
    bg_colors = np.array([(255, 0, 255), (145, 105, 196), (183, 140, 224),
                          (219, 188, 255), (214, 214, 230)], dtype=np.uint8)
    bgish = np.zeros((th, tw), dtype=bool)
    for c in bg_colors:
        bgish |= np.all(out_rgb == c, axis=-1)
    out_alpha[bgish & (cov < 0.45)] = 0

    out_alpha = remove_detached_specks(out_alpha > 0, min_area=6, near=2)
    out_alpha = np.where(out_alpha, 255, 0).astype(np.uint8)
    out = np.dstack([out_rgb, out_alpha])
    out[out_alpha == 0, :3] = PALETTE_RGB[0]
    return lock_palette(Image.fromarray(out, "RGBA"))


def matte_keyed(big: Image.Image, bg_rgb: np.ndarray | None = None) -> Image.Image:
    """Matte a 512-px character canvas against a flat key colour.

    Key-colour pixels are removed anywhere (including pockets trapped inside
    the silhouette); tiny detached specks are dropped while blades/hair locks
    survive.  This high-res RGBA frame is the single source of truth for both
    the 512-px animation and the 64-px downsample, so the two cannot disagree
    about which pixels are character.
    """
    rgb = np.array(big.convert("RGB"))
    bg = estimate_background(big) if bg_rgb is None else np.asarray(bg_rgb, dtype=np.float64)
    mask = background_mask_all(rgb, bg)
    rgba = np.dstack([rgb, np.where(mask, 0, 255).astype(np.uint8)])
    rgba[..., 3] = np.where(
        remove_detached_specks(rgba[..., 3] > 0, min_area=8, near=2), 255, 0)
    return lock_palette(Image.fromarray(rgba, "RGBA"))


def resample_from_hi(hi: Image.Image, target: tuple[int, int],
                     alpha_threshold: float = 0.18) -> Image.Image:
    """Coverage resample an already-matted 512-px frame to 64x64.

    Alpha comes from the high-res alpha, so a cell is opaque when at least
    ``alpha_threshold`` of its area is character.  RGB is the palette mode of
    the cell's opaque pixels.  This preserves a 1-px katana blade and never
    resurrects a key-colour pocket the high-res matte removed.
    """
    rgba = np.array(hi.convert("RGBA"))
    h, w = rgba.shape[:2]
    tw, th = target
    if w % tw or h % th:
        raise ValueError(f"non-integer cell size for {(w, h)} -> {target}")
    M = w // tw
    if M != h // th:
        raise ValueError(f"non-square cells: {M}x{h // th}")
    alpha = rgba[..., 3] > 0
    fg_blocks = _blocks(alpha, M)
    cov = fg_blocks.mean(axis=(2, 3))
    out_alpha = cov >= alpha_threshold

    n_cells = th * tw
    idx = nearest_palette_indices(rgba[..., :3].reshape(-1, 3), PALETTE_LAB).reshape(h, w)
    idx_blocks = _blocks(idx, M).reshape(n_cells, -1)
    fg_flat = fg_blocks.reshape(n_cells, -1)
    counts = np.zeros((n_cells, len(PALETTE_RGB)), dtype=np.int32)
    cell_ids = np.repeat(np.arange(n_cells), idx_blocks.shape[1]).reshape(n_cells, -1)
    np.add.at(counts, (cell_ids[fg_flat], idx_blocks[fg_flat]), 1)
    out_idx = np.argmax(counts, axis=1)
    out_rgb = PALETTE_RGB[out_idx].reshape(th, tw, 3).copy()
    out_alpha = remove_detached_specks(out_alpha, min_area=6, near=2)
    # Kill single-pixel background-key spill that survived the high-res matte.
    bg_colors = np.array([(255, 0, 255), (145, 105, 196), (183, 140, 224),
                          (219, 188, 255), (214, 214, 230)], dtype=np.uint8)
    for c in bg_colors:
        out_alpha &= ~(np.all(out_rgb == c, axis=-1) & (cov < 0.2))
    out = np.dstack([out_rgb, np.where(out_alpha, 255, 0).astype(np.uint8)])
    out[out[..., 3] == 0, :3] = PALETTE_RGB[0]
    return lock_palette(Image.fromarray(out, "RGBA"))


def shift_inside(img: Image.Image, margin_x: int = 1, margin_y: int = 0) -> Image.Image:
    """Shift a sprite minimally so it does not touch the left/right border.

    Used for the run-and-gun pistol frames: the body size/alignment stays
    exactly the same, the muzzle just gets a 1px margin instead of a flat cut
    at x=63.
    """
    arr = np.array(img.convert("RGBA"))
    alpha = arr[..., 3] > 0
    ys, xs = np.nonzero(alpha)
    if len(xs) == 0:
        return img
    w, h = img.size
    dx = 0
    if xs.min() < margin_x:
        dx = margin_x - int(xs.min())
    elif xs.max() >= w - margin_x:
        dx = (w - margin_x - 1) - int(xs.max())
    dy = 0
    if margin_y > 0:
        if ys.min() < margin_y:
            dy = margin_y - int(ys.min())
        elif ys.max() >= h - margin_y:
            dy = (h - margin_y - 1) - int(ys.max())
    if dx == 0 and dy == 0:
        return img
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    out.alpha_composite(img.convert("RGBA"), (dx, dy))
    return lock_palette(out)


def fit_with_margin(img: Image.Image, margin: int = 2) -> Image.Image:
    """Shrink a sprite just enough to keep it inside a transparent margin.

    Used for the roll, where the AI tends to fill the panel and clip the ball
    at the right edge.  The content is scaled down only when it touches the
    border; frames already inside the margin are returned unchanged.
    """
    arr = np.array(img.convert("RGBA"))
    alpha = arr[..., 3] > 0
    ys, xs = np.nonzero(alpha)
    if len(xs) == 0:
        return img
    x0, x1 = int(xs.min()), int(xs.max()) + 1
    y0, y1 = int(ys.min()), int(ys.max()) + 1
    w, h = img.size
    if x0 >= margin and y0 >= margin and x1 <= w - margin and y1 <= h - margin:
        return img
    crop = img.convert("RGBA").crop((x0, y0, x1, y1))
    scale = min((w - 2 * margin) / crop.width, (h - 2 * margin) / crop.height, 1.0)
    nw = max(1, int(round(crop.width * scale)))
    nh = max(1, int(round(crop.height * scale)))
    resized = crop.resize((nw, nh), Image.NEAREST)
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    out.alpha_composite(resized, ((w - nw) // 2, (h - nh) // 2))
    return lock_palette(out)


def keep_main_component(img: Image.Image) -> Image.Image:
    """Keep only the largest alpha component (used for the roll).

    The roll is a single tumbling body; any other component is a detached hair
    or gear fragment created by the AI at the panel edge.  Removing them is
    safer than letting them float.
    """
    arr = np.array(img.convert("RGBA"))
    alpha = arr[..., 3] > 0
    lab, n = ndimage.label(alpha)
    if n > 1:
        sizes = np.bincount(lab.ravel())
        sizes[0] = 0
        main = int(np.argmax(sizes))
        alpha = lab == main
    arr[..., 3] = np.where(alpha, 255, 0).astype(np.uint8)
    return lock_palette(Image.fromarray(arr, "RGBA"))


def remove_detached_specks_image(img: Image.Image, min_area: int = 6,
                                 near: int = 2) -> Image.Image:
    arr = np.array(img.convert("RGBA"))
    alpha = remove_detached_specks(arr[..., 3] > 0, min_area=min_area, near=near)
    arr[..., 3] = np.where(alpha, 255, 0).astype(np.uint8)
    return lock_palette(Image.fromarray(arr, "RGBA"))


def _blocks(arr: np.ndarray, cell: int) -> np.ndarray:
    """(H, W, ...) -> (H/cell, W/cell, cell, cell, ...)."""
    h, w = arr.shape[:2]
    rest = arr.shape[2:]
    return arr.reshape(h // cell, cell, w // cell, cell, *rest).transpose(0, 2, 1, 3, *range(4, 4 + len(rest)))


def resample_to_true_pixel(
    img: Image.Image,
    target: tuple[int, int],
    bg_rgb: np.ndarray | None = None,
    core_ratio: float = CORE_WINDOW_RATIO,
    bg_vote: float = BG_VOTE_RATIO,
    tol: float = BG_TOL_LAB,
) -> Image.Image:
    """Core-window mode pooling.

    ``target`` is (width, height) in true pixels.  Each output pixel takes the
    modal palette colour of the non-background pixels in the central core window
    of its cell; a cell that is mostly background becomes fully transparent.
    """
    rgb_img = img.convert("RGB")
    tw, th = target
    if rgb_img.width % tw or rgb_img.height % th:
        rgb_img = rgb_img.resize((tw * (rgb_img.width // tw or 1), th * (rgb_img.height // th or 1)), Image.NEAREST)
    rgb = np.array(rgb_img)
    h, w = rgb.shape[:2]
    cw, ch = w // tw, h // th
    if cw != ch:
        raise ValueError(f"non-square cells: {cw}x{ch} for target {target}")
    M = cw

    bg = estimate_background(rgb_img) if bg_rgb is None else np.asarray(bg_rgb, dtype=np.float64)
    # Chroma key only makes sense for magenta-backed call sheets.  A terrain
    # tile's border colour is its own material; flood-filling it would punch a
    # dark ring into the tile.
    is_key = bg[0] > 180 and bg[2] > 180 and bg[1] < 90
    bg_mask = background_mask(rgb, bg, tol=tol) if is_key else np.zeros(rgb.shape[:2], dtype=bool)

    rgb_blocks = _blocks(rgb, M)                      # (th, tw, M, M, 3)
    bg_blocks = _blocks(bg_mask, M)                   # (th, tw, M, M)
    inset = int(round(M * (1.0 - core_ratio) / 2))
    core = max(1, int(round(M * core_ratio)))
    rgb_core = rgb_blocks[:, :, inset:inset + core, inset:inset + core, :]
    bg_core = bg_blocks[:, :, inset:inset + core, inset:inset + core]

    n_cells = th * tw
    flat_rgb = rgb_core.reshape(n_cells, -1, 3)
    flat_bg = bg_core.reshape(n_cells, -1)
    fg_counts = (~flat_bg).sum(axis=1)

    idx = nearest_palette_indices(flat_rgb.reshape(-1, 3), PALETTE_LAB)
    idx = idx.reshape(n_cells, -1)

    counts = np.zeros((n_cells, len(PALETTE_RGB)), dtype=np.int32)
    valid = ~flat_bg
    cell_ids = np.repeat(np.arange(n_cells), valid.shape[1]).reshape(n_cells, -1)
    np.add.at(counts, (cell_ids[valid], idx[valid]), 1)

    out_idx = np.argmax(counts, axis=1)
    out_alpha = np.where(fg_counts > valid.shape[1] * bg_vote, 255, 0).astype(np.uint8)
    out_alpha[fg_counts == 0] = 0

    out = np.zeros((n_cells, 4), dtype=np.uint8)
    out[:, :3] = PALETTE_RGB[out_idx]
    out[:, 3] = out_alpha
    out[out_alpha == 0, :3] = PALETTE_RGB[0]
    return Image.fromarray(out.reshape(th, tw, 4), "RGBA")


def upscale_nearest(img: Image.Image, factor: int) -> Image.Image:
    return img.resize((img.width * factor, img.height * factor), Image.NEAREST)


def prepare_api_input(img: Image.Image, size: int, bg=(255, 0, 255)) -> Image.Image:
    """Place a true-pixel sprite on a square API canvas with nearest scaling."""
    factor = max(1, size // max(img.width, img.height))
    big = upscale_nearest(img, factor)
    canvas = Image.new("RGB", (size, size), bg)
    canvas.paste(big.convert("RGBA"), ((size - big.width) // 2, (size - big.height) // 2), big.convert("RGBA"))
    return canvas


def content_bbox(img: Image.Image, alpha_threshold: int = 8) -> tuple[int, int, int, int] | None:
    arr = np.array(img.convert("RGBA"))
    mask = arr[..., 3] > alpha_threshold
    if not mask.any():
        return None
    ys, xs = np.nonzero(mask)
    return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1


def split_sheet(sheet: Image.Image, frames: int, frame_w: int, frame_h: int) -> list[Image.Image]:
    return [sheet.crop((i * frame_w, 0, (i + 1) * frame_w, frame_h)) for i in range(frames)]
