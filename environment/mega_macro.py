"""Module 4: Mega-structure pipeline (PLAN 模块四).

4.1 – 9-slice kit generation from a mother image, with 1D / 2D seamless
     enforcement and centre-piece variants.
4.2 – Cross-grid decal generation (cracks, vines, gargoyles) extracted as
     independent alpha-layered overlays.
4.3 – Deterministic macro-assembly from a binary blueprint with
     bitmask-topology placement, graph-coloured centre variation,
     Poisson-disk seam-targeted decal stamping, Bayer-dither AO baking,
     and tile deduplication into a compact atlas + Tiled/Godot layout.
"""
from __future__ import annotations

import hashlib
import json
import math
import random as _random
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from config.pipeline_config import (
    BG_KEY_HEX,
    OUTPUT_DIR,
    TILE_SIZE,
    UPSCALE_FACTOR,
)
from config.namespaces import environment_dir, mega_dir
from core.api_client import GeminiImageClient
from core.grid_resampler import resample_to_true_pixel, upscale_nearest
from core.palette_quantizer import (
    PALETTE_RGB,
    RAMP_SIZE,
    bayer_threshold,
    hex_to_rgb,
    lock_palette,
    nearest_palette_indices,
    palette_violations,
    shade_rgb,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
BIG_TILE = 64              # true-pixel size of a 9-slice piece
MEGA_SCALE = UPSCALE_FACTOR  # 16  (64*16 = 1024 API px per piece)
API_1536 = 1536              # mother-image API side for 3x3 at 512 px/ piece
# For 16x upscale: 192 * 16 = 3072.  But PLAN says 1536 (8x).  We use 8x for
# mega to keep the API bill reasonable while matching PLAN dimensions.
MEGA_SCALE8 = 8
MOTHER_TRUE = BIG_TILE * 3           # 192
MOTHER_API = MOTHER_TRUE * MEGA_SCALE8  # 1536

SEAMLESS_BORDER = 8   # px locked during seamless repaint


# ---------------------------------------------------------------------------
# 4.1  Nine-slice kit generation
# ---------------------------------------------------------------------------

NINE_SLICE_PROMPT = (
    "A pixel-art 3x3 grid of a massive ancient obsidian stone fortress wall facade. "
    "Top row: crenellated battlements (merlons and crenels) with a dark sky behind. "
    "Middle row: large weathered stone blocks, mortar lines, iron torch sconces. "
    "Bottom row: a heavy sloped stone base plinth with rubble at the foot. "
    "Left and right edges have thick corner columns with vertical grooves. "
    "The centre shows continuous brick masonry. "
    "The entire facade must be contiguous – top merges seamlessly into middle, "
    "middle into bottom, left columns merge into centre, right into centre. "
    "Solid #FF00FF magenta anywhere outside the wall silhouette. "
    "Strictly flat orthographic front view, crisp pixel clusters, 64-color "
    "palette, 1px dark outlines, zero anti-aliasing, zero gradients, zero blur."
)


def _nine_slice_names() -> list[tuple[str, int, int]]:
    """Return (name, col, row) for the 9 cells of the mother image."""
    return [
        ("K_TL", 0, 0), ("E_T", 1, 0), ("K_TR", 2, 0),
        ("E_L",  0, 1), ("C1",  1, 1), ("E_R",  2, 1),
        ("K_BL", 0, 2), ("E_B", 1, 2), ("K_BR", 2, 2),
    ]


def generate_mother(api: GeminiImageClient, prompt: str | None = None) -> Image.Image:
    """Generate the 9-slice mother image (192x192 true px, 1536 API)."""
    prompt = prompt or NINE_SLICE_PROMPT
    print(f"  4.1: generating mother image ({MOTHER_TRUE}x{MOTHER_TRUE} true px) ...")
    raw = api.generate_one(
        prompt,
        role="sunburst",
        aspect="1:1",
        size="2K",
        tag="mega-mother",
    )
    # Resize to target API size
    if raw.size != (MOTHER_API, MOTHER_API):
        raw = raw.resize((MOTHER_API, MOTHER_API), Image.LANCZOS)
    mother = resample_to_true_pixel(raw, (MOTHER_TRUE, MOTHER_TRUE))
    mother = lock_palette(mother)
    return key_mother_background(mother)


def key_mother_background(mother: Image.Image, tol: float = 22.0) -> Image.Image:
    """Remove the AI's flat backdrop (white or magenta) from the mother facade.

    Without this, the pale backdrop of the 3x3 mother image is quantised to a
    light palette grey and every crenel gap becomes an opaque white square in
    the assembled wall.
    """
    from core.grid_resampler import background_mask, estimate_background
    arr = np.array(mother.convert("RGBA"))
    bg = estimate_background(mother)
    transparent_border = float((arr[0, :, 3] == 0).mean()) > 0.25
    if not (bg.mean() > 150 or (bg[0] > 180 and bg[2] > 180 and bg[1] < 90) or transparent_border):
        return mother
    if bg.mean() > 150 or (bg[0] > 180 and bg[2] > 180 and bg[1] < 90):
        mask = background_mask(arr[..., :3], bg, tol=tol)
    else:
        mask = np.zeros(arr.shape[:2], dtype=bool)

    # The API paints solid near-black sky bars behind the battlements / below
    # the base.  They are large rectangles adjacent to the transparent backdrop
    # (not the wall's 1px dark outline), so key those components specifically.
    from scipy import ndimage as _ndi
    h, w = arr.shape[:2]
    lum = arr[..., :3].astype(np.float32).mean(-1)
    dark = (lum < 22) & (arr[..., 3] > 0)
    transparent = arr[..., 3] == 0
    near_trans = _ndi.binary_dilation(transparent, iterations=2)
    labels, n_dark = _ndi.label(dark)
    for lbl in range(1, n_dark + 1):
        comp = labels == lbl
        area = int(comp.sum())
        if area < 120:
            continue
        ys, xs = np.nonzero(comp)
        y0, y1 = ys.min(), ys.max()
        x0, x1 = xs.min(), xs.max()
        bw, bh = x1 - x0 + 1, y1 - y0 + 1
        fill = area / max(1, bw * bh)
        band = (y1 < h * 0.35) or (y0 > h * 0.85)
        if band and fill > 0.45 and near_trans[comp].mean() > 0.2:
            mask |= comp

    arr[mask, 3] = 0
    arr[mask, :3] = 0
    return Image.fromarray(arr, "RGBA")


def cut_nine_slice(mother: Image.Image) -> dict[str, Image.Image]:
    """Cut a 192x192 mother image into the 9 named 64x64 pieces."""
    assert mother.size == (MOTHER_TRUE, MOTHER_TRUE), f"expected {MOTHER_TRUE}x{MOTHER_TRUE}"
    pieces: dict[str, Image.Image] = {}
    for name, col, row in _nine_slice_names():
        x0 = col * BIG_TILE
        y0 = row * BIG_TILE
        piece = mother.crop((x0, y0, x0 + BIG_TILE, y0 + BIG_TILE))
        pieces[name] = lock_palette(piece)
    return pieces


# --- Seamless enforcement ---

def _seam_median_edges(tile: Image.Image, axes: str = "xy", width: int = 2) -> Image.Image:
    """Palette-neighbourhood median on the wrap edges (visual seam smoothing).

    The statistical KS test rejects both a visible seam and a perfectly smooth
    seam (its gradient distribution differs from the textured interior), so
    the actual product uses this deterministic 2 px palette median to remove
    the visible boundary while keeping the AI motif.
    """
    a = np.array(tile.convert("RGBA"))
    h, w = a.shape[:2]
    for _ in range(2):
        if "x" in axes:
            for y in range(h):
                for x in list(range(width)) + list(range(w - width, w)):
                    nbrs = [a[(y + dy) % h, (x + dx) % w, :3]
                            for dy in (-1, 0, 1) for dx in (-1, 0, 1) if (dy, dx) != (0, 0)]
                    u, c = np.unique(np.array(nbrs), axis=0, return_counts=True)
                    a[y, x, :3] = u[int(np.argmax(c))]
        if "y" in axes:
            for x in range(w):
                for y in list(range(width)) + list(range(h - width, h)):
                    nbrs = [a[(y + dy) % h, (x + dx) % w, :3]
                            for dy in (-1, 0, 1) for dx in (-1, 0, 1) if (dy, dx) != (0, 0)]
                    u, c = np.unique(np.array(nbrs), axis=0, return_counts=True)
                    a[y, x, :3] = u[int(np.argmax(c))]
    return Image.fromarray(a, "RGBA")


def make_seamless_2d(
    api: GeminiImageClient,
    tile: Image.Image,
    border: int = SEAMLESS_BORDER,
    tag: str = "seamless2d",
) -> Image.Image:
    """Make a tile toroidally seamless (both axes).

    Rolls half the tile width/height so original edges become a centre cross,
    inpainting only the cross while locking the border.
    """
    tile = lock_palette(tile.convert("RGBA"))
    w, h = tile.size
    bw, bh = w // 2, h // 2

    # Roll so old edges meet at centre
    arr = np.array(tile.convert("RGB"))
    rolled = np.roll(np.roll(arr, bw, axis=1), bh, axis=0)
    rolled_img = Image.fromarray(rolled)

    # Cross mask: central band of width ~16 px
    mask = Image.new("L", (w, h), 0)
    draw = ImageDraw.Draw(mask)
    half_band = max(6, w // 8)
    # Vertical cross arm
    draw.rectangle([w // 2 - half_band, 0, w // 2 + half_band - 1, h - 1], fill=255)
    # Horizontal cross arm
    draw.rectangle([0, h // 2 - half_band, w - 1, h // 2 + half_band - 1], fill=255)
    # Lock border: ensure outermost `border` px are black (protected)
    draw.rectangle([0, 0, w - 1, border - 1], fill=0)
    draw.rectangle([0, h - border, w - 1, h - 1], fill=0)
    draw.rectangle([0, 0, border - 1, h - 1], fill=0)
    draw.rectangle([w - border, 0, w - 1, h - 1], fill=0)

    prompt = (
        "Seamlessly continue the stone brick wall pattern across the red-tinted "
        "masked area. Preserve the exact pixel style, mortar line spacing, and "
        "colour palette of the surrounding wall. Zero visible seams."
    )
    result = api.inpaint(
        rolled_img, mask, prompt,
        role="flare", aspect="1:1", size="1K", tag=tag,
    )
    result = result.resize((w, h), Image.LANCZOS)

    # Roll back
    out_arr = np.array(result)
    unrolled = np.roll(np.roll(out_arr, -bw, axis=1), -bh, axis=0)
    out = lock_palette(Image.fromarray(unrolled).convert("RGBA"))
    return _seam_median_edges(out, axes="xy")


def make_seamless_1d_x(
    api: GeminiImageClient,
    tile: Image.Image,
    border: int = SEAMLESS_BORDER,
    tag: str = "seamless1dx",
) -> Image.Image:
    """Make a tile seamless along the X axis only (horizontal tiling).

    Rolls half width so old edges meet at vertical centre line.
    """
    tile = lock_palette(tile.convert("RGBA"))
    w, h = tile.size
    bw = w // 2

    rgba = np.array(tile.convert("RGBA"))
    alpha_orig = rgba[..., 3]
    arr = rgba[..., :3]
    rolled = np.roll(arr, bw, axis=1)
    rolled_img = Image.fromarray(rolled)

    mask = Image.new("L", (w, h), 0)
    draw = ImageDraw.Draw(mask)
    half_band = max(6, w // 8)
    draw.rectangle([w // 2 - half_band, border, w // 2 + half_band - 1, h - border - 1], fill=255)

    prompt = (
        "Seamlessly continue the pixel-art stone wall pattern horizontally across "
        "the vertical seam in the masked area. Preserve the block alignment and "
        "mortar lines. Zero visible vertical seam."
    )
    result = api.inpaint(
        rolled_img, mask, prompt,
        role="flare", aspect="1:1", size="1K", tag=tag,
    )
    result = result.resize((w, h), Image.LANCZOS)

    out_arr = np.array(result)
    unrolled = np.roll(out_arr, -bw, axis=1)
    out = lock_palette(Image.fromarray(np.dstack([unrolled, alpha_orig]), "RGBA"))
    return _seam_median_edges(out, axes="x")


def make_seamless_1d_y(
    api: GeminiImageClient,
    tile: Image.Image,
    border: int = SEAMLESS_BORDER,
    tag: str = "seamless1dy",
) -> Image.Image:
    """Make a tile seamless along the Y axis only (vertical tiling)."""
    tile = lock_palette(tile.convert("RGBA"))
    w, h = tile.size
    bh = h // 2

    rgba = np.array(tile.convert("RGBA"))
    alpha_orig = rgba[..., 3]
    arr = rgba[..., :3]
    rolled = np.roll(arr, bh, axis=0)
    rolled_img = Image.fromarray(rolled)

    mask = Image.new("L", (w, h), 0)
    draw = ImageDraw.Draw(mask)
    half_band = max(6, h // 8)
    draw.rectangle([border, h // 2 - half_band, w - border - 1, h // 2 + half_band - 1], fill=255)

    prompt = (
        "Seamlessly continue the pixel-art stone wall pattern vertically across "
        "the horizontal seam in the masked area. Preserve the block alignment. "
        "Zero visible horizontal seam."
    )
    result = api.inpaint(
        rolled_img, mask, prompt,
        role="flare", aspect="1:1", size="1K", tag=tag,
    )
    result = result.resize((w, h), Image.LANCZOS)

    out_arr = np.array(result)
    unrolled = np.roll(out_arr, -bh, axis=0)
    out = lock_palette(Image.fromarray(np.dstack([unrolled, alpha_orig]), "RGBA"))
    return _seam_median_edges(out, axes="y")


def generate_center_variants(
    api: GeminiImageClient,
    base: Image.Image,
    n: int = 3,
    border: int = SEAMLESS_BORDER,
) -> list[Image.Image]:
    """Generate N seamless centre variants from a base C1 tile.

    Locks the outer `border` px and inpaints the interior with different seeds.
    """
    base = lock_palette(base.convert("RGBA"))
    w, h = base.size
    variants = [base]  # C1 = first variant

    mask = Image.new("L", (w, h), 0)
    draw = ImageDraw.Draw(mask)
    draw.rectangle([border, border, w - border - 1, h - border - 1], fill=255)

    for i in range(n - 1):
        prompt = (
            "Repaint the interior stone brick wall area with a slightly different "
            "block arrangement and mortar crack pattern, while keeping the outer "
            "border frame completely unchanged. Same palette, same architectural "
            "style, different brick pattern."
        )
        result = api.inpaint(
            base.convert("RGB"), mask, prompt,
            role="flare", aspect="1:1", size="1K",
            tag=f"center-var-{i}",
        )
        result = result.resize((w, h), Image.LANCZOS)
        variant = lock_palette(result.convert("RGBA"))
        variants.append(variant)

    # --- Sanitize: replace light-gray pixels with C1 reference ---
    # The API occasionally produces a variant where large areas are washed-out
    # light gray (lum > 150, low saturation).  These wreck the atlas.
    variants = _sanitize_center_variants(variants, base)
    return variants


def _sanitize_center_variants(
    variants: list[Image.Image],
    c1_ref: Image.Image,
    lum_threshold: int = 150,
    sat_threshold: int = 30,
) -> list[Image.Image]:
    """Replace light-gray pixels in centre variants with C1 reference pixels.

    For each variant, any pixel where (R+G+B)/3 > lum_threshold AND
    max(RGB)-min(RGB) < sat_threshold is considered a washed-out background
    artifact and replaced with the C1 pixel at the same coordinate.
    """
    c1_arr = np.array(c1_ref.convert("RGBA"))
    sanitized: list[Image.Image] = []
    for vi, var in enumerate(variants):
        arr = np.array(var.convert("RGBA"))
        bright = arr[..., :3].astype(np.float32).mean(axis=-1)
        max_c = arr[..., :3].max(axis=-1).astype(np.float32)
        min_c = arr[..., :3].min(axis=-1).astype(np.float32)
        spread = max_c - min_c
        bad = (bright > lum_threshold) & (spread < sat_threshold) & (arr[..., 3] > 0)
        if bad.any():
            n_bad = int(bad.sum())
            n_total = int((arr[..., 3] > 0).sum())
            pct = 100.0 * n_bad / max(1, n_total)
            print(f"     sanitize C{vi + 1}: {n_bad}/{n_total} ({pct:.1f}%) "
                  f"light-gray px -> replaced with C1")
            for c in range(3):
                arr[bad, c] = c1_arr[bad, c]
        else:
            print(f"     sanitize C{vi + 1}: clean")
        sanitized.append(lock_palette(Image.fromarray(arr, "RGBA")))
    return sanitized


# ---------------------------------------------------------------------------
# 4.2  Cross-grid decal generation
# ---------------------------------------------------------------------------

DECAL_PROMPTS = {
    "crack": (
        "A massive jagged structural crack and collapsed stone cavity spanning "
        "the entire wall from the top edge to the bottom edge, at least three "
        "tiles wide and four tiles tall. Deep fissures, chipped edges, fallen "
        "rubble. Pixel art, same stone palette as the surrounding wall."
    ),
    "vine": (
        "Thick hanging pixel art ivy vines and overgrown moss patches clinging "
        "to the stone brick wall. Dark green leaves, twisting brown stems, "
        "clusters of leaves draping downward. Same wall palette behind."
    ),
    "gargoyle": (
        "A weathered gothic stone gargoyle relief mounted on the brick wall, "
        "with heavy rusted iron chains bolted across the stones. Pixel art, "
        "same stone palette, 1px outlines."
    ),
}


def tile_wall_background(
    c1: Image.Image,
    grid: int = 3,
) -> Image.Image:
    """Tile C1 into a grid x grid background."""
    c1 = lock_palette(c1.convert("RGBA"))
    tile_sz = c1.width  # 64
    canvas_sz = tile_sz * grid
    canvas = Image.new("RGBA", (canvas_sz, canvas_sz), (0, 0, 0, 0))
    for row in range(grid):
        for col in range(grid):
            canvas.paste(c1, (col * tile_sz, row * tile_sz))
    return canvas


def tile_wall_background_rect(
    c1: Image.Image,
    cols: int,
    rows: int,
) -> Image.Image:
    """Tile C1 into a cols x rows rectangular background (64px tiles)."""
    c1 = lock_palette(c1.convert("RGBA"))
    tile_sz = c1.width  # 64
    canvas = Image.new("RGBA", (tile_sz * cols, tile_sz * rows), (0, 0, 0, 0))
    for r in range(rows):
        for c in range(cols):
            canvas.paste(c1, (c * tile_sz, r * tile_sz))
    return canvas


def generate_decal(
    api: GeminiImageClient,
    background: Image.Image,
    decal_type: str,
    c1: Image.Image,
    grid_cols: int = 3,
    grid_rows: int = 3,
) -> Image.Image:
    """Generate one decal on a tiled background and extract as alpha layer.

    grid_cols × grid_rows = tile count (each tile is 64×64 true px).
    Returns an RGBA image where only the decal pixels are non-zero alpha.
    """
    true_w = BIG_TILE * grid_cols
    true_h = BIG_TILE * grid_rows
    scale = 4                    # keep API call affordable
    api_w = true_w * scale
    api_h = true_h * scale

    prompt = DECAL_PROMPTS.get(decal_type, DECAL_PROMPTS["crack"])

    # Upscale background and mask to API scale
    bg_api = background.convert("RGB").resize((api_w, api_h), Image.NEAREST)

    mask = Image.new("L", (api_w, api_h), 0)
    draw = ImageDraw.Draw(mask)
    cx, cy = api_w // 2, api_h // 2
    rx, ry = int(api_w * 0.44), int(api_h * 0.44)
    draw.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=255)
    # PLAN 4.2: keep at least 32 true px of untouched wall around the decal
    # (0.5 tile), so a 3x4-cell crack can actually fit instead of only 2x1.
    margin_api = (BIG_TILE * scale) // 2
    draw.rectangle([0, 0, api_w - 1, margin_api - 1], fill=0)
    draw.rectangle([0, api_h - margin_api, api_w - 1, api_h - 1], fill=0)
    draw.rectangle([0, 0, margin_api - 1, api_h - 1], fill=0)
    draw.rectangle([api_w - margin_api, 0, api_w - 1, api_h - 1], fill=0)

    result = api.inpaint(
        bg_api, mask, prompt,
        role="sunburst", aspect="1:1", size="1K",
        tag=f"decal-{decal_type}-{grid_cols}x{grid_rows}",
    )
    result = result.resize((api_w, api_h), Image.LANCZOS)

    # Resample to true pixels
    true_result = resample_to_true_pixel(result, (true_w, true_h))
    true_result = lock_palette(true_result)

    # Build reference tiled background at true-pixel size
    c1_tiled = tile_wall_background_rect(c1, grid_cols, grid_rows)
    decal_arr = np.array(true_result.convert("RGBA"))
    bg_arr = np.array(c1_tiled.convert("RGBA"))

    # --- LAB-distance-based background detection ---
    # Instead of exact palette-index match (which fails when the API produces
    # a slightly different wall shade), use LAB colour distance against the
    # reference background.
    from core.palette_quantizer import rgb_to_lab
    decal_lab = rgb_to_lab(decal_arr[..., :3]).reshape(true_h, true_w, 3)
    bg_lab = rgb_to_lab(bg_arr[..., :3]).reshape(true_h, true_w, 3)
    lab_dist = np.linalg.norm(decal_lab - bg_lab, axis=-1)
    BG_DIST_THRESHOLD = 12.0  # pixels within 12 LAB distance = background
    is_bg = np.all(decal_arr[..., :3] == 0, axis=-1)
    same_bg = (lab_dist < BG_DIST_THRESHOLD) | is_bg

    from scipy import ndimage
    from core.palette_quantizer import rgb_to_lab as _lab

    decal_rgb = decal_arr[..., :3].astype(np.float32)
    bg_lum = (bg_arr[..., :3].astype(np.float32) @ np.array([0.299, 0.587, 0.114]))
    lum = decal_rgb @ np.array([0.299, 0.587, 0.114])
    sat = (decal_rgb.max(axis=-1) - decal_rgb.min(axis=-1)) / np.maximum(decal_rgb.max(axis=-1), 1.0)

    # Type-specific content mask: only the decal motif, never the wall.
    if decal_type == "vine":
        content = (decal_rgb[..., 1] > decal_rgb[..., 0] + 4) & \
                  (decal_rgb[..., 1] > decal_rgb[..., 2] + 4) & (decal_rgb[..., 1] > 28)
    elif decal_type == "crack":
        content = (lum < bg_lum - 25)
    else:  # gargoyle / chains: neutral stone relief, the wall is purple
        content = ((sat < 0.24) & (lum > 25) & (lum < 175)) | (lab_dist > 16)
    keep = content & ~is_bg & ~same_bg

    # Keep only sizeable components whose bbox intersects the central region.
    labels, n_labels = ndimage.label(keep)
    if n_labels > 0:
        cy0, cy1 = int(true_h * 0.15), int(true_h * 0.85)
        cx0, cx1 = int(true_w * 0.15), int(true_w * 0.85)
        keep2 = np.zeros_like(keep)
        for lbl in range(1, n_labels + 1):
            comp = labels == lbl
            if comp.sum() < 15:
                continue
            ys, xs = np.nonzero(comp)
            if ys.max() < cy0 or ys.min() > cy1 or xs.max() < cx0 or xs.min() > cx1:
                continue
            keep2 |= comp
        keep = keep2 if keep2.any() else keep

    bright = decal_arr[..., :3].astype(np.float32).mean(axis=-1)
    max_c = decal_arr[..., :3].max(axis=-1).astype(np.float32)
    min_c = decal_arr[..., :3].min(axis=-1).astype(np.float32)
    saturation = (max_c - min_c) / np.maximum(max_c, 1.0)
    light_gray = (bright > 110) & (saturation < 0.15) & keep
    keep = keep & ~light_gray

    # Moss / chipped-stone underlay: a 3px growth ring makes the decal a
    # solid patch instead of a thin stem, so it actually hides a seam.
    under = np.zeros_like(keep)
    if keep.any() and decal_type == "vine":
        under = ndimage.binary_dilation(keep, iterations=3) & ~keep & ~is_bg & ~same_bg
        # avoid swallowing the whole wall: only keep underlay near the content
        under &= ndimage.binary_dilation(keep, iterations=5)

    out = np.zeros((true_h, true_w, 4), dtype=np.uint8)
    for c in range(3):
        out[keep, c] = decal_arr[keep, c]
    out[keep, 3] = 255
    if under.any():
        from core.palette_quantizer import PALETTE_RGB as _PR
        under_col = _PR[3 * 8 + 2]  # #224a26 dark foliage
        out[under, :3] = under_col
        out[under, 3] = 255

    # Include 1px border around decal areas for contact shadow
    dilated = ndimage.binary_dilation(keep, iterations=1)
    new_keep = dilated & ~keep & ~is_bg
    if new_keep.any():
        edge_rgb = decal_arr[new_keep, :3]
        darkened = shade_rgb(edge_rgb, -2)
        for c in range(3):
            out[new_keep, c] = darkened[:, c]
        out[new_keep, 3] = 255

    return lock_palette(Image.fromarray(out, "RGBA"))


def build_decal_set(
    api: GeminiImageClient,
    c1: Image.Image,
    out_dir: Path | None = None,
    decal_grid_cols: int = 4,
    decal_grid_rows: int = 3,
) -> dict[str, Image.Image]:
    """Generate decal types at decal_grid_cols × decal_grid_rows tile size.

    Each decal is (64*cols) × (64*rows) true pixels.
    """
    out_dir = Path(out_dir) if out_dir else environment_dir("field") / "mega" / "decals"
    out_dir.mkdir(parents=True, exist_ok=True)

    bg = tile_wall_background_rect(c1, decal_grid_cols, decal_grid_rows)
    bg.save(out_dir / "decal_background.png")

    decals: dict[str, Image.Image] = {}
    for dtype in ["crack", "vine", "gargoyle"]:
        print(f"  4.2: generating decal '{dtype}' ({decal_grid_cols}x{decal_grid_rows}) ...")
        decal = generate_decal(api, bg, dtype, c1,
                               grid_cols=decal_grid_cols, grid_rows=decal_grid_rows)
        decal.save(out_dir / f"decal_{dtype}.png")
        decals[dtype] = decal
    return decals


# ---------------------------------------------------------------------------
# 4.3  Deterministic macro-assembly
# ---------------------------------------------------------------------------

def _neighbor_bits(blueprint: np.ndarray, r: int, c: int) -> int:
    """Return a 4-neighbour bitmask: N=1, S=2, W=4, E=8."""
    bits = 0
    H, W_arr = blueprint.shape
    if r > 0 and blueprint[r - 1, c]:
        bits |= 1  # North
    if r < H - 1 and blueprint[r + 1, c]:
        bits |= 2  # South
    if c > 0 and blueprint[r, c - 1]:
        bits |= 4  # West
    if c < W_arr - 1 and blueprint[r, c + 1]:
        bits |= 8  # East
    return bits


def _diag_bits(blueprint: np.ndarray, r: int, c: int) -> int:
    """Return a 4-diagonal bitmask: NW=1, NE=2, SW=4, SE=8."""
    bits = 0
    H, W_arr = blueprint.shape
    if r > 0 and c > 0 and blueprint[r - 1, c - 1]:
        bits |= 1
    if r > 0 and c < W_arr - 1 and blueprint[r - 1, c + 1]:
        bits |= 2
    if r < H - 1 and c > 0 and blueprint[r + 1, c - 1]:
        bits |= 4
    if r < H - 1 and c < W_arr - 1 and blueprint[r + 1, c + 1]:
        bits |= 8
    return bits


def bitmask_placement(
    blueprint: np.ndarray,
    kit: dict[str, Image.Image],
    center_variants: list[Image.Image],
    rng: np.random.RandomState,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Place 9-slice pieces according to the blueprint topology.

    Returns (layout_ids, variant_indices, total_mask).
    layout_ids: HxW array of piece name indices (or -1 for empty).
    variant_indices: HxW array of which centre variant was used.
    total_mask: HxW boolean mask of occupied cells.
    """
    H, W_arr = blueprint.shape
    name_to_idx = {
        "K_TL": 0, "E_T": 1, "K_TR": 2,
        "E_L": 3,  "C": 4,  "E_R": 5,
        "K_BL": 6, "E_B": 7, "K_BR": 8,
    }
    layout_ids = np.full((H, W_arr), -1, dtype=np.int32)
    variant_indices = np.full((H, W_arr), -1, dtype=np.int32)
    total_mask = blueprint.astype(bool)

    for r in range(H):
        for c in range(W_arr):
            if not blueprint[r, c]:
                continue
            nb = _neighbor_bits(blueprint, r, c)
            db = _diag_bits(blueprint, r, c)

            n = bool(nb & 1)
            s = bool(nb & 2)
            w = bool(nb & 4)
            e = bool(nb & 8)
            nw = bool(db & 1)
            ne = bool(db & 2)
            sw = bool(db & 4)
            se = bool(db & 8)

            # Determine piece type
            if n and s and w and e:
                # Interior cell - use centre variant
                piece_name = "C"
            elif n and s and w and not e:
                piece_name = "E_R"
            elif n and s and not w and e:
                piece_name = "E_L"
            elif n and not s and w and e:
                piece_name = "E_B"
            elif not n and s and w and e:
                piece_name = "E_T"
            elif n and s and not w and not e:
                piece_name = "E_R" if c < W_arr // 2 else "E_L"
            elif not n and not s and w and e:
                piece_name = "E_B" if r < H // 2 else "E_T"
            # Corners
            elif n and e and not s and not w:
                piece_name = "K_BL"
            elif n and w and not s and not e:
                piece_name = "K_BR"
            elif s and e and not n and not w:
                piece_name = "K_TL"
            elif s and w and not n and not e:
                piece_name = "K_TR"
            # Edge pieces (only two neighbours)
            elif n and not s and not w and not e:
                piece_name = "E_B"
            elif s and not n and not w and not e:
                piece_name = "E_T"
            elif w and not e and not n and not s:
                piece_name = "E_R"
            elif e and not w and not n and not s:
                piece_name = "E_L"
            # Isolated / with one diagonal
            else:
                # Just use centre as fallback
                piece_name = "C"

            layout_ids[r, c] = name_to_idx.get(piece_name, 4)

            if piece_name == "C":
                # Assign a variant index (graph coloring later)
                variant_indices[r, c] = 0  # will be filled by graph coloring
            else:
                variant_indices[r, c] = 0

    return layout_ids, variant_indices, total_mask


def graph_color_centers(
    blueprint: np.ndarray,
    variant_indices: np.ndarray,
    num_variants: int,
    rng: np.random.RandomState,
) -> np.ndarray:
    """Assign centre variant indices so no two adjacent interior cells share
    the same variant (graph-colouring constraint)."""
    H, W_arr = blueprint.shape
    colored = variant_indices.copy()

    for r in range(H):
        for c in range(W_arr):
            if not blueprint[r, c]:
                continue
            if colored[r, c] != 0:
                continue  # not a centre cell or already coloured

            # Interior cell: check 4-neighbours
            forbidden: set[int] = set()
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < H and 0 <= nc < W_arr and blueprint[nr, nc]:
                    # Check if neighbour is interior
                    nb = _neighbor_bits(blueprint, nr, nc)
                    if nb == 15:  # all 4 directions occupied = interior
                        if colored[nr, nc] > 0:
                            forbidden.add(colored[nr, nc])

            available = [v for v in range(1, num_variants + 1) if v not in forbidden]
            if not available:
                available = list(range(1, num_variants + 1))
            colored[r, c] = int(rng.choice(available))

    return colored


def poisson_disk_seam_anchors(
    blueprint: np.ndarray,
    min_radius: float = 2.5,
    rng: np.random.RandomState | None = None,
) -> list[tuple[int, int]]:
    """Poisson-disk sample seam intersection points on interior cells."""
    if rng is None:
        rng = np.random.RandomState(42)
    H, W_arr = blueprint.shape

    # Find interior cells (all 4 neighbours filled)
    interior: list[tuple[int, int]] = []
    for r in range(H):
        for c in range(W_arr):
            if blueprint[r, c] and _neighbor_bits(blueprint, r, c) == 15:
                interior.append((r, c))

    if not interior:
        return []

    # Poisson disk sampling
    k = 30  # max attempts per point
    radius = max(1.0, min_radius)
    cell_size = radius / math.sqrt(2)
    grid_w = max(1, int(math.ceil(W_arr / cell_size)))
    grid_h = max(1, int(math.ceil(H / cell_size)))
    grid = np.full((grid_h, grid_w), -1, dtype=np.int32)

    def grid_pos(px: float, py: float) -> tuple[int, int]:
        return (int(py / cell_size), int(px / cell_size))

    # Start with a random interior cell
    active: list[tuple[float, float]] = []
    idx0 = rng.randint(0, len(interior))
    r0, c0 = interior[idx0]
    samples: list[tuple[float, float]] = [(float(c0), float(r0))]
    gx, gy = grid_pos(c0, r0)
    if 0 <= gy < grid_h and 0 <= gx < grid_w:
        grid[gy, gx] = 0
    active.append((float(c0), float(r0)))

    while active:
        ai = rng.randint(0, len(active))
        ax, ay = active[ai]
        found = False
        for _ in range(k):
            angle = rng.uniform(0, 2 * math.pi)
            dist = rng.uniform(radius, 2 * radius)
            nx = ax + dist * math.cos(angle)
            ny = ay + dist * math.sin(angle)
            nc = int(round(nx))
            nr = int(round(ny))
            if 0 <= nr < H and 0 <= nc < W_arr and blueprint[nr, nc]:
                # Check this is an interior cell
                if _neighbor_bits(blueprint, nr, nc) == 15:
                    gx, gy = grid_pos(nx, ny)
                    if 0 <= gx < grid_w and 0 <= gy < grid_h:
                        # Check neighbours in grid
                        ok = True
                        for dgx in range(max(0, gx - 1), min(grid_w, gx + 2)):
                            for dgy in range(max(0, gy - 1), min(grid_h, gy + 2)):
                                if grid[dgy, dgx] >= 0:
                                    sx, sy = samples[grid[dgy, dgx]]
                                    if (nx - sx) ** 2 + (ny - sy) ** 2 < radius ** 2:
                                        ok = False
                                        break
                            if not ok:
                                break
                        if ok:
                            samples.append((nx, ny))
                            grid[gy, gx] = len(samples) - 1
                            active.append((nx, ny))
                            found = True
                            break
        if not found:
            active.pop(ai)

    # Convert to integer cell coordinates
    return [(int(round(y)), int(round(x))) for x, y in samples]


def apply_decals(
    base_canvas: Image.Image,
    decals: dict[str, Image.Image],
    anchors: list[tuple[int, int]],
    blueprint: np.ndarray,
    total_mask: np.ndarray,
    tile_sz: int = BIG_TILE,
    rng: _random.Random | None = None,
    target_coverage: float = 0.30,
    max_decals: int = 48,
) -> tuple[Image.Image, dict]:
    """Stamp macro decals on interior cross seams and under the eaves.

    Coverage is measured strictly: a seam counts only when an opaque decal
    pixel lies within +/-2 px of the 4-tile intersection, over *all* interior
    intersections (not just those whose four cells have full 4-neighbourhoods).
    """
    if rng is None:
        rng = _random.Random(42)

    canvas = base_canvas.copy()
    H, W_arr = blueprint.shape
    canvas_arr = np.array(canvas.convert("RGBA"))
    decal_pixels = np.zeros(canvas_arr.shape[:2], dtype=bool)

    interior_cells = int(np.sum([blueprint[r, c] and _neighbor_bits(blueprint, r, c) == 15
                                 for r in range(H) for c in range(W_arr)]))
    seam_coords: list[tuple[int, int]] = []
    for r in range(H - 1):
        for c in range(W_arr - 1):
            if blueprint[r, c] and blueprint[r, c + 1] and blueprint[r + 1, c] and blueprint[r + 1, c + 1]:
                seam_coords.append((r, c))
    cross_seams = len(seam_coords)

    def _place(decal: Image.Image, px: int, py: int, clip_to_silhouette: bool = True) -> None:
        nonlocal canvas_arr
        dw, dh = decal.size
        px = max(0, min(canvas.width - dw, px))
        py = max(0, min(canvas.height - dh, py))
        d_arr = np.array(decal.convert("RGBA"))
        dh_actual = min(dh, canvas.height - py)
        dw_actual = min(dw, canvas.width - px)
        region = canvas_arr[py:py + dh_actual, px:px + dw_actual]
        d_region = d_arr[:dh_actual, :dw_actual]
        if clip_to_silhouette and total_mask.shape[:2] == canvas_arr.shape[:2]:
            # PLAN 4.3: non-hanging decals are alpha-clipped by the real
            # building silhouette M_total (the assembled alpha, not whole cells).
            m = total_mask[py:py + dh_actual, px:px + dw_actual]
            d_region = d_region.copy()
            d_region[..., 3] = np.where(m, d_region[..., 3], 0)
        a = d_region[..., 3].astype(np.float32) / 255.0
        a3 = np.dstack([a] * 3)
        region[..., :3] = (a3 * d_region[..., :3] + (1 - a3) * region[..., :3]).astype(np.uint8)
        region[..., 3] = np.maximum(region[..., 3], d_region[..., 3])
        decal_pixels[py:py + dh_actual, px:px + dw_actual] |= (d_region[..., 3] > 0)

    def _centroid(decal: Image.Image) -> tuple[float, float]:
        """Opaque pixel with the densest neighbourhood (a moss cluster, not a stem)."""
        a = (np.array(decal.convert("RGBA"))[..., 3] > 0).astype(np.float32)
        oy, ox = np.nonzero(a > 0)
        if not len(ox):
            return decal.width / 2, decal.height / 2
        from scipy import ndimage as _nd
        dens = _nd.uniform_filter(a, size=5)
        k = int(np.argmax(dens[oy, ox]))
        return float(ox[k]), float(oy[k])

    def _dense_now() -> set[tuple[int, int]]:
        out = set()
        for (sr, sc) in seam_coords:
            sx = (sc + 1) * tile_sz
            sy = (sr + 1) * tile_sz
            w = decal_pixels[max(0, sy - 2):sy + 3, max(0, sx - 2):sx + 3]
            if int(w.sum()) >= 10:
                out.add((sr, sc))
        return out

    def _covered_now() -> set[tuple[int, int]]:
        out = set()
        for (sr, sc) in seam_coords:
            sx = (sc + 1) * tile_sz
            sy = (sr + 1) * tile_sz
            w = decal_pixels[max(0, sy - 2):sy + 3, max(0, sx - 2):sx + 3]
            if w.any():
                out.add((sr, sc))
        return out

    # --- Eave vines: hang from every exposed top edge (PLAN 4.3) ---
    eave_cells = [(r, c) for r in range(1, H) for c in range(W_arr)
                  if blueprint[r, c] and not blueprint[r - 1, c]]
    rng.shuffle(eave_cells)
    placed = 0
    for (r, c) in eave_cells[:4]:
        decal = decals.get("vine")
        if decal is None:
            break
        cx, cy = _centroid(decal)
        px = int(round((c + 0.5) * tile_sz - cx))
        py = int(round(r * tile_sz - cy * 0.15))  # top of content near the eave
        _place(decal, px, py)
        placed += 1

    # --- Wall seams: greedy placement until coverage target / cap ---
    type_cycle = ["vine", "vine", "crack", "vine", "gargoyle", "vine", "crack", "vine"]
    gargoyle_count = 0
    cracks = 0
    # PLAN 4.3 Poisson anchors seed the placement; remaining seams fill in.
    anchor_seams: list[tuple[int, int]] = []
    for (ar, ac) in anchors:
        if seam_coords:
            near = min(seam_coords, key=lambda q: (q[0] - ar) ** 2 + (q[1] - ac) ** 2)
            if near not in anchor_seams:
                anchor_seams.append(near)
    candidates = anchor_seams + [q for q in seam_coords if q not in anchor_seams]
    rng.shuffle(candidates[len(anchor_seams):])
    centers: list[tuple[int, int]] = []
    ti = 0
    for (sr, sc) in candidates:
        if placed >= max_decals:
            break
        if len(_dense_now()) / max(1, cross_seams) >= 0.34 and placed >= 10:
            break
        sx = (sc + 1) * tile_sz
        sy = (sr + 1) * tile_sz
        if any(abs(sx - x) < tile_sz * 0.9 and abs(sy - y) < tile_sz * 0.9 for x, y in centers):
            continue
        dtype = type_cycle[ti % len(type_cycle)]
        ti += 1
        if dtype == "gargoyle" and gargoyle_count >= 2:
            dtype = "vine"
        decal = decals.get(dtype)
        if decal is None:
            continue
        cx, cy = _centroid(decal)
        if dtype in ("crack", "gargoyle"):
            # macro decals must span 2-3 cells; upscale the extracted layer so
            # it actually covers the seam arms (nearest keeps pixel clusters)
            f = 2.0 if dtype == "crack" else 1.5
            decal = decal.resize((int(decal.width * f), int(decal.height * f)), Image.NEAREST)
            cx, cy = _centroid(decal)
        _place(decal, int(round(sx - cx)), int(round(sy - cy)),
               clip_to_silhouette=(dtype != "vine"))
        centers.append((sx, sy))
        placed += 1
        if dtype == "gargoyle":
            gargoyle_count += 1
        elif dtype == "crack":
            cracks += 1

    result = Image.fromarray(canvas_arr, "RGBA")
    result = lock_palette(result)

    covered_seam_set = _covered_now()
    dense_set = _dense_now()

    # Clip decals to building mask
    result_arr = np.array(result.convert("RGBA"))
    for r in range(H):
        for c in range(W_arr):
            if not blueprint[r, c]:
                x0 = c * tile_sz
                y0 = r * tile_sz
                result_arr[y0:y0 + tile_sz, x0:x0 + tile_sz, 3] = 0
    result = lock_palette(Image.fromarray(result_arr, "RGBA"))

    coverage = len(covered_seam_set) / max(1, cross_seams)
    stats = {
        "interior_cells": interior_cells,
        "cross_seams": cross_seams,
        "decal_anchors": placed,
        "covered_seams": len(covered_seam_set),
        "coverage_ratio": round(coverage, 4),
        "coverage_dense": round(len(dense_set) / max(1, cross_seams), 4),
        "covered_dense": len(dense_set),
        "gargoyle_count": gargoyle_count,
        "crack_count": cracks,
        "eave_vines": min(4, len(eave_cells)),
    }
    return result, stats


def soften_black_areas(canvas: Image.Image) -> Image.Image:
    """Lift large pure-black shadow bands to the next palette shade.

    The AI mother uses #08080c for deep shadow courses; tiled over 64 px they
    read as solid black bars.  Thin 1 px outlines are preserved (erosion),
    while large areas are lifted to #14141c.
    """
    from scipy import ndimage as _ndi
    arr = np.array(canvas.convert("RGBA"))
    black = np.all(arr[..., :3] == np.array([8, 8, 12], dtype=np.uint8), axis=-1)
    black &= arr[..., 3] > 0
    core = _ndi.binary_erosion(black, iterations=1)
    areas = _ndi.binary_dilation(core, iterations=1)
    arr[areas, :3] = np.array([20, 20, 28], dtype=np.uint8)
    return lock_palette(Image.fromarray(arr, "RGBA"))


def bake_macro_ao(
    canvas: Image.Image,
    blueprint: np.ndarray,
    tile_sz: int = BIG_TILE,
) -> Image.Image:
    """Bake ambient occlusion: bottom height attenuation + interior corner AO.

    Uses Bayer dither to darken by 1 shade step in the palette.
    """
    canvas = lock_palette(canvas.convert("RGBA"))
    arr = np.array(canvas.convert("RGBA"))
    H_grid, W_grid = blueprint.shape
    h, w = arr.shape[:2]
    bayer = bayer_threshold((h, w), strength=0.6)

    # --- Vertical height attenuation (bottom 20% of structure) ---
    for r in range(H_grid):
        if not blueprint[r, :].any():
            continue
        y0 = r * tile_sz
        y1 = y0 + tile_sz
        # Normalized height from bottom
        max_row = max(rr for rr in range(H_grid) if blueprint[rr, :].any())
        if max_row == r:
            continue  # top row, no AO needed
        # Height ratio: 0 at top occupied row, 1 at bottom
        if max_row > 0:
            h_ratio = (max_row - r) / max_row
        else:
            h_ratio = 0

        # h_ratio is 0 at the structure bottom and 1 at the top; darken the
        # bottom 20% (PLAN 4.3 vertical gradient).
        if h_ratio < 0.2:
            intensity = (0.2 - h_ratio) / 0.2  # 0 to 1
            for y in range(y0, min(y1, h)):
                for x in range(w):
                    if arr[y, x, 3] == 0:
                        continue
                    if bayer[y, x] < intensity * 0.7:
                        arr[y, x, :3] = shade_rgb(arr[y, x, :3], -1)

    # --- Interior concave corner AO ---
    for r in range(H_grid - 1):
        for c in range(W_grid - 1):
            # L-shaped interior corner: two adjacent filled, diagonal empty
            patterns = [
                (blueprint[r, c], blueprint[r, c + 1],
                 blueprint[r + 1, c], blueprint[r + 1, c + 1]),
            ]
            for tl, tr, bl, br in [(
                blueprint[r, c], blueprint[r, c + 1],
                blueprint[r + 1, c], blueprint[r + 1, c + 1],
            )]:
                if tl and tr and bl and not br:  # bottom-right empty = L corner
                    _apply_corner_ao(arr, r, c, "br", tile_sz, bayer, h)
                if tl and tr and not bl and br:  # bottom-left empty
                    _apply_corner_ao(arr, r, c, "bl", tile_sz, bayer, h)
                if tl and not tr and bl and br:  # top-right empty
                    _apply_corner_ao(arr, r, c, "tr", tile_sz, bayer, h)
                if not tl and tr and bl and br:  # top-left empty
                    _apply_corner_ao(arr, r, c, "tl", tile_sz, bayer, h)

    out = Image.fromarray(arr, "RGBA")
    return lock_palette(out)


def _apply_corner_ao(
    arr: np.ndarray,
    grid_r: int,
    grid_c: int,
    corner: str,
    tile_sz: int,
    bayer: np.ndarray,
    max_h: int,
) -> None:
    """Apply AO darkening in a 6px band along an L-corner seam."""
    cx = grid_c * tile_sz
    cy = grid_r * tile_sz
    band = 6

    if corner == "br":
        # Along the bottom of cell (r, c) and right of cell (r, c)
        x0 = cx + tile_sz - band
        y0 = cy + tile_sz - band
        x1 = cx + tile_sz
        y1 = cy + tile_sz
    elif corner == "bl":
        x0 = cx
        y0 = cy + tile_sz - band
        x1 = cx + band
        y1 = cy + tile_sz
    elif corner == "tr":
        x0 = cx + tile_sz - band
        y0 = cy
        x1 = cx + tile_sz
        y1 = cy + band
    elif corner == "tl":
        x0 = cx
        y0 = cy
        x1 = cx + band
        y1 = cy + band
    else:
        return

    x0 = max(0, x0)
    y0 = max(0, y0)
    x1 = min(arr.shape[1], x1)
    y1 = min(max_h, y1)

    for y in range(y0, y1):
        for x in range(x0, x1):
            if arr[y, x, 3] == 0:
                continue
            if bayer[y, x] > 0.5:
                arr[y, x, :3] = shade_rgb(arr[y, x, :3], -1)


def tile_deduplicate(
    canvas: Image.Image,
    tile_sz: int = TILE_SIZE,
) -> tuple[Image.Image, list[dict]]:
    """Slice a mega canvas into tile_sz x tile_sz pieces, hash-deduplicate,
    and produce a compact atlas + layout map.

    Returns (atlas_image, layout_list).
    """
    canvas = lock_palette(canvas.convert("RGBA"))
    w, h = canvas.size
    cols = w // tile_sz
    rows = h // tile_sz

    # Hash every tile
    tile_hashes: dict[str, int] = {}  # hash -> atlas_x index
    layout: list[dict] = []
    unique_tiles: list[Image.Image] = []

    for row in range(rows):
        for col in range(cols):
            x0 = col * tile_sz
            y0 = row * tile_sz
            tile = canvas.crop((x0, y0, x0 + tile_sz, y0 + tile_sz))
            tile = lock_palette(tile)

            # Check if tile is fully transparent
            tile_arr = np.array(tile.convert("RGBA"))
            if tile_arr[..., 3].sum() == 0:
                layout.append({"row": row, "col": col, "atlas_x": -1, "empty": True})
                continue

            tile_hash = hashlib.sha256(tile_arr.tobytes()).hexdigest()
            if tile_hash in tile_hashes:
                layout.append({
                    "row": row, "col": col,
                    "atlas_x": tile_hashes[tile_hash],
                    "empty": False,
                })
            else:
                atlas_idx = len(unique_tiles)
                tile_hashes[tile_hash] = atlas_idx
                unique_tiles.append(tile)
                layout.append({
                    "row": row, "col": col,
                    "atlas_x": atlas_idx,
                    "empty": False,
                })

    # Build atlas
    atlas_w = len(unique_tiles) * tile_sz
    atlas_h = tile_sz
    atlas = Image.new("RGBA", (max(1, atlas_w), atlas_h), (0, 0, 0, 0))
    for i, tile in enumerate(unique_tiles):
        atlas.paste(tile, (i * tile_sz, 0))

    return atlas, layout


# ---------------------------------------------------------------------------
# Full 4.1 pipeline
# ---------------------------------------------------------------------------

def build_nine_slice_kit(
    api: GeminiImageClient,
    out_dir: Path | None = None,
    prompt: str | None = None,
) -> dict:
    """Run the full 4.1 pipeline: mother -> 9-slice -> seamless -> variants."""
    out_dir = Path(out_dir) if out_dir else environment_dir("field") / "mega" / "kit"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Generate mother
    mother = generate_mother(api, prompt)
    mother.save(out_dir / "mother_raw.png")

    # Cut into 9 pieces
    pieces = cut_nine_slice(mother)
    for name, piece in pieces.items():
        piece.save(out_dir / f"piece_{name}_raw.png")

    # 2D seamless centre
    print("  4.1: making C1 2D seamless ...")
    c1_seamless = make_seamless_2d(api, pieces["C1"], tag="c1-2d")
    c1_seamless.save(out_dir / "piece_C1_2d.png")

    # 1D seamless edges
    print("  4.1: making edges 1D seamless ...")
    for name, make_fn, tag in [
        ("E_T", make_seamless_1d_x, "et-1dx"),
        ("E_B", make_seamless_1d_x, "eb-1dx"),
        ("E_L", make_seamless_1d_y, "el-1dy"),
        ("E_R", make_seamless_1d_y, "er-1dy"),
    ]:
        seamless = make_fn(api, pieces[name], tag=tag)
        pieces[name] = seamless
        seamless.save(out_dir / f"piece_{name}_seamless.png")

    pieces["C1"] = c1_seamless

    # Corner pieces: no seamless enforcement needed (they're unique)
    for name in ["K_TL", "K_TR", "K_BL", "K_BR"]:
        pieces[name].save(out_dir / f"piece_{name}_final.png")

    # Generate centre variants
    print("  4.1: generating centre variants ...")
    center_variants = generate_center_variants(api, c1_seamless, n=3)
    for i, cv in enumerate(center_variants):
        cv.save(out_dir / f"piece_C{i + 1}.png")

    # Save final kit
    kit = {
        "K_TL": pieces["K_TL"], "E_T": pieces["E_T"], "K_TR": pieces["K_TR"],
        "E_L": pieces["E_L"],   "C1": center_variants[0], "E_R": pieces["E_R"],
        "K_BL": pieces["K_BL"], "E_B": pieces["E_B"], "K_BR": pieces["K_BR"],
    }
    center_pool = {f"C{i + 1}": center_variants[i] for i in range(len(center_variants))}

    report = {
        "module": "mega_4.1",
        "pieces": list(kit.keys()),
        "center_variants": len(center_variants),
        "output_dir": str(out_dir),
    }
    (out_dir / "report.json").write_text(json.dumps(report, indent=2))

    return {"kit": kit, "center_pool": center_pool, "report": report}


# ---------------------------------------------------------------------------
# Full 4.3 pipeline
# ---------------------------------------------------------------------------

def assemble_megastructure(
    blueprint: np.ndarray,
    kit: dict[str, Image.Image],
    center_pool: dict[str, Image.Image],
    decals: dict[str, Image.Image],
    tile_sz: int = BIG_TILE,
    seed: int = 42,
    write_debug: bool = True,
) -> tuple[Image.Image, dict]:
    """Run the full 4.3 assembly pipeline."""
    rng = np.random.RandomState(seed)
    py_rng = _random.Random(seed)

    H, W_arr = blueprint.shape
    canvas_w = W_arr * tile_sz
    canvas_h = H * tile_sz

    (environment_dir("field") / "mega").mkdir(parents=True, exist_ok=True)

    print(f"  4.3: assembling {H}x{W_arr} blueprint -> {canvas_w}x{canvas_h} canvas")
    print(f"       kit pieces={len(kit)}, center variants={len(center_pool)}, decals={len(decals)}")

    # Step 1: Bitmask placement
    layout_ids, variant_indices, total_mask = bitmask_placement(
        blueprint, kit, list(center_pool.values()), rng,
    )

    # Step 2: Graph colour centre variants
    n_variants = len(center_pool)
    variant_indices = graph_color_centers(
        blueprint, variant_indices, n_variants, rng,
    )

    # Build base canvas
    canvas = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
    center_list = list(center_pool.values())
    name_idx_to_piece = {
        0: kit["K_TL"], 1: kit["E_T"], 2: kit["K_TR"],
        3: kit["E_L"],  4: center_list[0], 5: kit["E_R"],
        6: kit["K_BL"], 7: kit["E_B"], 8: kit["K_BR"],
    }

    for r in range(H):
        for c in range(W_arr):
            if not blueprint[r, c]:
                continue
            piece_id = layout_ids[r, c]
            if piece_id == 4:  # Centre piece
                vi = variant_indices[r, c]
                if vi <= 0:
                    vi = 1
                piece = center_list[min(vi - 1, len(center_list) - 1)]
            else:
                piece = name_idx_to_piece.get(piece_id, center_list[0])
            piece = lock_palette(piece.convert("RGBA"))
            canvas.paste(piece, (c * tile_sz, r * tile_sz))

    if write_debug:
        canvas.save(environment_dir("field") / "mega" / "assembly_base.png")

    # Step 3: Poisson-disk seam anchors
    anchors = poisson_disk_seam_anchors(blueprint, min_radius=2.5, rng=rng)
    print(f"  4.3: Poisson-disk anchors = {len(anchors)}")

    # Step 4: Apply decals
    total_mask_px = np.array(canvas.convert("RGBA"))[..., 3] > 0
    canvas, coverage = apply_decals(
        canvas, decals, anchors, blueprint, total_mask_px,
        tile_sz=tile_sz, rng=py_rng, target_coverage=0.55, max_decals=80,
    )
    if write_debug:
        canvas.save(environment_dir("field") / "mega" / "assembly_decals.png")

    # Step 5: Bake AO
    canvas = bake_macro_ao(canvas, blueprint, tile_sz=tile_sz)
    canvas = soften_black_areas(canvas)
    if write_debug:
        canvas.save(environment_dir("field") / "mega" / "assembly_final.png")

    stats = {
        "blueprint": f"{H}x{W_arr}",
        "canvas": f"{canvas_w}x{canvas_h}",
        "tile_count": int(np.sum(blueprint)),
        "center_variants_used": int(np.max(variant_indices)),
        "decal_anchors": len(anchors),
        **coverage,
    }
    return canvas, stats


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

def build_mega_all(
    api: GeminiImageClient,
    blueprint: np.ndarray | None = None,
    out_dir: Path | None = None,
    seed: int = 42,
) -> dict:
    """Run the full Module 4 pipeline end-to-end and export the atlas."""
    out_dir = Path(out_dir) if out_dir else mega_dir("field")
    out_dir.mkdir(parents=True, exist_ok=True)
    mega_env = environment_dir("field") / "mega"
    mega_env.mkdir(parents=True, exist_ok=True)

    # 4.1 Nine-slice kit
    print("=" * 60)
    print("Module 4.1: Nine-slice kit")
    print("=" * 60)
    result_41 = build_nine_slice_kit(api, mega_env)
    kit = result_41["kit"]
    center_pool = result_41["center_pool"]

    # 4.2 Decals
    print("=" * 60)
    print("Module 4.2: Cross-grid decals")
    print("=" * 60)
    c1 = center_pool.get("C1", list(center_pool.values())[0])
    decals = build_decal_set(api, c1, mega_env / "decals")

    # 4.3 Assembly
    print("=" * 60)
    print("Module 4.3: Macro assembly")
    print("=" * 60)
    if blueprint is None:
        # Castle blueprint: 15×20 with thick walls, two towers, narrow gate (3 cells).
        # Designed so walls are continuous on both sides of the gate.
        H, W = 15, 20
        castle = [
            "....................",
            "......######........",
            "....##########......",
            "...##############...",
            "..################..",
            ".######....#######..",
            ".######....#######..",
            ".######....#######..",
            ".######....#######..",
            ".######....#######..",
            ".######....#######..",
            ".######....#######..",
            ".######....#######..",
            ".######....#######..",
            "....................",
        ]
        blueprint = np.zeros((H, W), dtype=bool)
        for r, row in enumerate(castle):
            for c, ch in enumerate(row):
                if ch == "#":
                    blueprint[r, c] = True

        # Narrow gate opening (3 cells wide) at bottom centre, rows 12-13
        gate_c = W // 2 - 1  # centre-left of gate
        for r in (12, 13):
            for c in range(gate_c, gate_c + 3):
                if 0 <= c < W:
                    blueprint[r, c] = False

    bp_path = mega_env / "blueprint.npy"
    np.save(bp_path, blueprint)
    bp_txt = mega_env / "blueprint.txt"
    bp_txt.write_text("\n".join(
        "".join("#" if c else "." for c in row) for row in blueprint
    ))
    print(f"  Blueprint saved: {blueprint.shape}, "
          f"filled={np.sum(blueprint)}/{blueprint.size}")

    canvas, stats = assemble_megastructure(
        blueprint, kit, center_pool, decals,
        tile_sz=BIG_TILE, seed=seed,
    )

    # Deduplicate and export
    print("  4.3: tile deduplication ...")
    # First slice the 64x64 pieces into 32x32 tiles
    canvas_32, layout = tile_deduplicate(canvas, tile_sz=TILE_SIZE)

    atlas_path = out_dir / "mega_atlas.png"
    canvas_32.save(atlas_path)
    print(f"  Atlas -> {atlas_path} ({canvas_32.size})")

    layout_path = out_dir / "mega_layout.json"
    layout_path.write_text(json.dumps({
        "tile_size": TILE_SIZE,
        "atlas_width": canvas_32.width,
        "unique_tiles": canvas_32.width // TILE_SIZE if canvas_32.width > 0 else 0,
        "layout": layout,
    }, indent=2))
    print(f"  Layout -> {layout_path}")

    # Preview image (2x nearest-neighbour)
    preview = canvas.copy()
    preview = preview.resize((canvas.width * 2, canvas.height * 2), Image.NEAREST)
    preview_path = out_dir / "mega_preview.png"
    preview.save(preview_path)
    print(f"  Preview (2x) -> {preview_path}")

    # Save the 1x canvas too for reference
    canvas.save(out_dir / "mega_canvas_1x.png")

    # Palette check
    vp, vo = palette_violations(canvas)
    print(f"  Palette violations: partial_alpha={vp}, off_palette={vo}")

    report = {
        "module": "mega_all",
        "steps": ["4.1", "4.2", "4.3"],
        "blueprint": f"{blueprint.shape[0]}x{blueprint.shape[1]}",
        "canvas_true_px": f"{canvas.width}x{canvas.height}",
        "unique_32px_tiles": canvas_32.width // TILE_SIZE if canvas_32.width > 0 else 0,
        "palette_violations": vp + vo,
        "coverage": stats.get("coverage_ratio", 0),
        "coverage_dense": stats.get("coverage_dense", 0),
        "covered_seams": stats.get("covered_seams", 0),
        "covered_dense": stats.get("covered_dense", 0),
        "cross_seams": stats.get("cross_seams", 0),
        "decal_anchors": stats.get("decal_anchors", 0),
        "center_variants": len(center_pool),
        "output_dir": str(out_dir),
        "files": {
            "atlas": str(atlas_path),
            "layout": str(layout_path),
            "preview": str(preview_path),
        },
    }
    (out_dir / "report.json").write_text(json.dumps(report, indent=2))
    print("=" * 60)
    print("Module 4 complete.")
    return report


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    api = GeminiImageClient()
    build_mega_all(api)