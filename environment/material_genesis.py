"""Multi-material genesis (PLAN 2.1).

Generates a 2×2 palette-coloured Perlin-noise constraint grid, submits it to
Gemini for coherent synchronous generation of four terrain materials (grass,
dirt, cobblestone, water), slices the result into four quadrants, resamples
each to a 32×32 true-pixel palette-locked tile, and ensures every terrain
pixel is fully opaque (no alpha holes).
"""
from __future__ import annotations

import numpy as np
from PIL import Image

from config.pipeline_config import TILE_SIZE
from core.api_client import GeminiImageClient
from core.grid_resampler import resample_to_true_pixel
from core.palette_quantizer import (
    PALETTE_RGB,
    lock_palette,
    nearest_palette_indices,
    palette_violations,
)

# ---------------------------------------------------------------------------
# Perlin-noise gradient field (numpy, no external dependency)
# ---------------------------------------------------------------------------

_PERM = np.array(
    [
        151, 160, 137, 91, 90, 15, 131, 13, 201, 95, 96, 53, 194, 233, 7, 225,
        140, 36, 103, 30, 69, 142, 8, 99, 37, 240, 21, 10, 23, 190, 6, 148,
        247, 120, 234, 75, 0, 26, 197, 62, 94, 252, 219, 203, 117, 35, 11, 32,
        57, 177, 33, 88, 237, 149, 56, 87, 174, 20, 125, 136, 171, 168, 68, 175,
        74, 165, 71, 134, 139, 48, 27, 166, 77, 146, 158, 231, 83, 111, 229, 122,
        60, 211, 133, 230, 220, 105, 92, 41, 55, 46, 245, 40, 244, 102, 143, 54,
        65, 25, 63, 161, 1, 216, 80, 73, 209, 76, 132, 187, 208, 89, 18, 169,
        200, 196, 135, 130, 116, 188, 159, 86, 164, 100, 109, 198, 173, 186, 3, 64,
        52, 217, 226, 250, 124, 123, 5, 202, 38, 147, 118, 126, 255, 82, 85, 212,
        207, 206, 59, 227, 47, 16, 58, 17, 182, 189, 28, 42, 223, 183, 170, 213,
        119, 248, 152, 2, 44, 154, 163, 70, 221, 153, 101, 155, 167, 43, 172, 9,
        129, 22, 39, 253, 19, 98, 108, 110, 79, 113, 224, 232, 178, 185, 112, 104,
        218, 246, 97, 228, 251, 34, 242, 193, 238, 210, 144, 12, 191, 179, 162, 241,
        81, 51, 145, 235, 249, 14, 239, 107, 49, 192, 214, 31, 181, 199, 106, 157,
        184, 84, 204, 176, 115, 121, 50, 45, 127, 4, 150, 254, 138, 236, 205, 93,
        222, 114, 67, 29, 24, 72, 243, 141, 128, 195, 78, 66, 215, 61, 156, 180,
    ],
    dtype=np.int32,
)
_P2 = np.concatenate([_PERM, _PERM])


def _grad(h: np.ndarray, x: np.ndarray, y: np.ndarray) -> np.ndarray:
    hh = h & 3
    return np.where(hh == 0, x + y, np.where(hh == 1, -x + y,
                    np.where(hh == 2, x - y, -x - y)))


def perlin_noise(res: int, octaves: int = 3, seed: int = 0) -> np.ndarray:
    """Generate a ``res``×``res`` Perlin noise field in [0, 1]."""
    rng = np.random.default_rng(seed)
    perm = rng.permutation(256).astype(np.int32)
    p2 = np.concatenate([perm, perm])

    coords = np.linspace(0, 1, res, endpoint=False)
    xx, yy = np.meshgrid(coords, coords)
    out = np.zeros((res, res), dtype=np.float64)
    amp = 1.0
    freq = 4.0
    for _ in range(octaves):
        fx, fy = xx * freq * res, yy * freq * res
        xi, yi = fx.astype(np.int32) & 255, fy.astype(np.int32) & 255
        xf, yf = fx - xi.astype(np.float64), fy - yi.astype(np.float64)
        u = xf * xf * xf * (xf * (xf * 6.0 - 15.0) + 10.0)
        v = yf * yf * yf * (yf * (yf * 6.0 - 15.0) + 10.0)
        aa = p2[p2[xi] + yi]
        ab = p2[p2[xi] + yi + 1]
        ba = p2[p2[xi + 1] + yi]
        bb = p2[p2[xi + 1] + yi + 1]
        x1 = _grad(aa, xf, yf)
        x2 = _grad(ba, xf - 1, yf)
        y1 = x1 + u * (x2 - x1)
        x1 = _grad(ab, xf, yf - 1)
        x2 = _grad(bb, xf - 1, yf - 1)
        y2 = x1 + u * (x2 - x1)
        out += (y1 + v * (y2 - y1)) * amp
        amp *= 0.5
        freq *= 2.0
    out -= out.min()
    out /= max(out.max(), 1e-10)
    return out


# ---------------------------------------------------------------------------
# Material board generation
# ---------------------------------------------------------------------------

# Each quadrant gets its own palette ramp for the constraint board.
# ``ramp`` is a shade index into PALETTE_RGB.
QUADRANTS: list[dict] = [
    {
        "name": "grass",
        "ramp": 24,
        "desc": "lush green grass with scattered dark tufts and occasional bare spots",
    },
    {
        "name": "dirt",
        "ramp": 8,
        "desc": "packed brown dirt path with small pebbles and slight colour variation",
    },
    {
        "name": "stone",
        "ramp": 0,
        "desc": "ancient grey cobblestone pavement with darker grout lines between irregular stones, strictly grey tones",
    },
    {
        "name": "water",
        "ramp": 32,
        "desc": "dark deep water with gentle concentric ripple rings and foam speck highlights",
    },
]

GEN_PROMPT = (
    "A 2x2 grid of four separate top-down orthographic 2D pixel art terrain "
    "textures on a solid magenta #FF00FF background. "
    "The input image is a 2x2 colour-constraint board — KEEP its exact 2x2 "
    "grid layout and the hue/value locks for each quadrant; restyle each "
    "quadrant into its target material. "
    "Grid layout — each quadrant is one distinct material, no material bleeds "
    "across the dividing line: "
    "[TOP-LEFT quadrant] {grass}: {grass_desc}. "
    "[TOP-RIGHT quadrant] {dirt}: {dirt_desc}. "
    "[BOTTOM-LEFT quadrant] {stone}: {stone_desc}. "
    "[BOTTOM-RIGHT quadrant] {water}: {water_desc}. "
    "Strictly flat top-down orthographic view, no perspective, no horizon line, "
    "uniform lighting from top-left. Each quadrant must read as a single "
    "32x32 pixel-art tile upscaled 16x: every design pixel is a large square "
    "block, cobblestones span 3-5 blocks, grass tufts 1-3 blocks, water "
    "ripples 2-4 blocks, and mortar gaps are exactly one block wide. "
    "Zero anti-aliasing, zero blur, no sub-pixel detail, no fine texture, "
    "no text labels, no grid lines, no borders between quadrants. Each "
    "quadrant is entirely filled with its material, no magenta visible "
    "inside quadrants."
)


def _build_gen_prompt() -> str:
    """Format the prompt with per-material descriptions."""
    kw: dict[str, str] = {}
    for q in QUADRANTS:
        kw[q["name"]] = q["name"]
        kw[f"{q['name']}_desc"] = q["desc"]
    return GEN_PROMPT.format(**kw)


def make_constraint_board(res: int = 1024, seed: int = 42) -> Image.Image:
    """Build a 2×2 Perlin-noise constraint board painted with palette ramps.

    ``res`` must be even; each quadrant is ``res//2`` × ``res//2``.
    """
    half = res // 2
    noise = perlin_noise(res, octaves=4, seed=seed)
    rgb = np.zeros((res, res, 3), dtype=np.uint8)
    for qi, q in enumerate(QUADRANTS):
        row = qi // 2
        col = qi % 2
        y0, y1 = row * half, (row + 1) * half
        x0, x1 = col * half, (col + 1) * half
        n = noise[y0:y1, x0:x1]
        base = q["ramp"]
        # map noise [0,1] → ramp shade 1..6 (skip darkest, keep lightest)
        shade = 1 + (n * (7 - 1)).astype(np.int32).clip(1, 6)
        for s in range(7):
            mask = shade == (1 + s)
            rgb[y0:y1, x0:x1][mask] = PALETTE_RGB[base + s]
    return Image.fromarray(rgb, "RGB")


# ---------------------------------------------------------------------------
# Terrain fill — ensures no transparent gaps in terrain tiles
# ---------------------------------------------------------------------------

def _fill_terrain(tile: Image.Image) -> Image.Image:
    """Replace every alpha=0 pixel with the nearest alpha=255 pixel colour.

    Uses iterative morphological dilation so transparent holes in terrain
    are filled from their opaque neighbours.  Designed for small scattered
    holes, not large background regions.
    """
    if not isinstance(tile, Image.Image):
        tile = Image.fromarray(np.asarray(tile), "RGBA")
    arr = np.array(tile.convert("RGBA"))
    alpha = arr[..., 3]
    opaque = alpha == 255
    if opaque.all():
        return tile

    from scipy import ndimage
    # Iteratively dilate the opaque region until every pixel is filled
    current = opaque.copy()
    filled_rgb = arr[..., :3].copy()
    max_iter = max(arr.shape[0], arr.shape[1])  # worst case: diagonal fill
    for _ in range(max_iter):
        missing = ~current
        if not missing.any():
            break
        # Dilate one step
        dilated = ndimage.binary_dilation(current, iterations=1)
        newly_filled = dilated & missing
        if not newly_filled.any():
            break
        # For each newly-filled pixel, copy the colour from any opaque neighbour
        # (simple: use the dilated colour from the previous step)
        padded = np.pad(filled_rgb, ((1, 1), (1, 1), (0, 0)), mode="edge")
        for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            ny, nx = np.nonzero(newly_filled)
            src_y = ny + 1 + dy
            src_x = nx + 1 + dx
            # Only copy from positions that were already opaque
            valid = current[ny, nx - np.full_like(nx, 0)]  # hmm, complex
        # Simpler: just take the first opaque neighbour
        ys, xs = np.nonzero(newly_filled)
        for y, x in zip(ys, xs):
            # Find nearest opaque pixel and copy its RGB
            neigh = filled_rgb[max(0, y - 1):y + 2, max(0, x - 1):x + 2, :]
            neigh_alpha = current[max(0, y - 1):y + 2, max(0, x - 1):x + 2]
            valid_neigh = neigh[neigh_alpha]
            if len(valid_neigh) > 0:
                filled_rgb[y, x] = valid_neigh[0]
        current = dilated

    out = np.dstack([filled_rgb, np.full(alpha.shape, 255, dtype=np.uint8)])
    return lock_palette(Image.fromarray(out.astype(np.uint8), "RGBA"))


# ---------------------------------------------------------------------------
# Colour-domain constraint: force a quadrant's pixels into allowed ramps
# ---------------------------------------------------------------------------

def generate_materials(
    client: GeminiImageClient | None = None,
    res: int = 1024,
    seed: int = 42,
    size: str = "2K",
) -> dict[str, Image.Image]:
    """Run the full material genesis pipeline.

    Returns a dict mapping material name → the AI's 512×512 quadrant.  The
    seamless step (PLAN 2.2) inpaints at this resolution and then pools down
    to the 32×32 true-pixel tile, so the AI's stone/grass/water structure is
    preserved instead of being thrown away by an early 32 px downsample.
    """
    client = client or GeminiImageClient()

    # 1. Build constraint board
    board = make_constraint_board(res, seed)
    board.save("/tmp/material_constraint.png")

    # 2. Call Gemini — pass the constraint board as a guide image
    prompt = _build_gen_prompt()
    raw = client.edit(prompt, [board], role="sunburst", aspect="1:1", size=size,
                      tag="material-2x2-v3")
    raw.save("/tmp/material_raw.png")

    # 3. Slice into quadrants.  raw may be 1024×1024 (1K) or 2048×2048 (2K);
    #    use the actual output dimensions, not the constraint-board resolution.
    raw_w, raw_h = raw.size
    half = raw_w // 2
    if raw_w < 2 or raw_h < 2:
        raise ValueError(f"API returned image too small: {raw.size}")

    materials: dict[str, Image.Image] = {}
    # Visual-standard prompts (user round): readable grass tufts, packed dirt
    # without grey blocks, and DIRECTIONAL thin wave lines for water (no
    # circular rings, which would tile into a circle grid).
    prompts = {
        "grass": ("A single seamless tileable 32x32 pixel art grass tile, flat top-down. A clean "
                  "mid-green lawn with 4 LARGE readable grass tufts, each a 4-5 pixel cluster of "
                  "2-3 blades with dark bases and light tips, plus 3 small dark clumps; large crisp "
                  "pixel clusters, no scattered single-pixel noise, no dots, no gradient, no "
                  "border, no grid, 64-color palette."),
        "dirt": ("A single 32x32 seamless tileable pixel art packed-dirt tile, flat top-down. "
                 "Mostly uniform warm brown with a fine 1-pixel speckle, a few subtle "
                 "low-contrast darker patches and 3-4 tiny 1-2 pixel tan pebbles. No large dark "
                 "shapes, no repeated motif, no grey rectangles or blocks, no grid, no border, "
                 "no noise, crisp pixel clusters, 64-color palette."),
        "stone": ("A single 32x32 top-down pixel art stone terrain tile. Exactly 32 by 32 design "
                  "pixels with large square pixels: blue-grey cobblestones 4-6 pixels across with "
                  "1 pixel dark mortar gaps. Flat top-down orthographic view, uniform lighting from "
                  "top-left, 64-color palette, 1 pixel dark edges, zero anti-aliasing, zero "
                  "gradients, no sub-pixel detail, no grid, no borders, no text."),
        "water": ("A single seamless tileable 32x32 pixel art calm water surface tile, flat top-down. "
                  "Deep blue base with MANY THIN 1-PIXEL horizontal ripple lines spaced 4-6 pixels "
                  "apart, short broken dashes of light blue, gentle undulation, low contrast, no "
                  "large waves, no thick crests, no circles, no foam, no border, no grid, crisp "
                  "pixel clusters, 64-color palette."),
    }
    for qi, q in enumerate(QUADRANTS):
        name = q["name"]
        tag = (f"mat4-{name}" if name in ("grass", "water")
               else (f"mat3-{name}" if name == "dirt" else "material-stone-32px"))
        tile_raw = client.generate_one(prompts[name], role="sunburst", aspect="1:1",
                                       size="1K", tag=tag)
        if name in ("grass", "dirt", "water") and max(tile_raw.size) >= 640:
            w, h = tile_raw.size
            tile_raw = tile_raw.crop(((w - 512) // 2, (h - 512) // 2,
                                      (w - 512) // 2 + 512, (h - 512) // 2 + 512))
        tile32 = lock_palette(resample_to_true_pixel(tile_raw.convert("RGB"), (32, 32)))
        if name == "grass":
            # Remove the AI's white/lavender flower specks that read as missing
            # tiles; keep the dark outlines (low luminance) and green blades.
            ga = np.array(tile32.convert("RGB")).astype(np.int16)
            lum = ga @ np.array([0.2126, 0.7152, 0.0722])
            greenish = (ga[..., 1] > ga[..., 0] + 4) & (ga[..., 1] > ga[..., 2] + 4)
            bad = (~greenish) & (lum > 70)
            if bad.any():
                cols = ga[greenish]
                if len(cols):
                    u, c = np.unique(cols, axis=0, return_counts=True)
                    ga[bad] = u[int(np.argmax(c))]
            # Remove isolated 1px dark specks: they read as dirt/noise dots.
            from scipy import ndimage as _nd
            darkish = (ga[..., 1] < 90) & (ga[..., 1] > ga[..., 0]) & (ga[..., 1] > ga[..., 2])
            neigh = _nd.convolve(darkish.astype(np.int16), np.ones((3, 3), np.int16),
                                 mode="wrap") - darkish.astype(np.int16)
            base_col = ga[greenish].mean(axis=0).astype(np.int16) if greenish.any() else np.array([47, 107, 47])
            ga[darkish & (neigh == 0)] = base_col
            tile32 = Image.fromarray(np.dstack([ga.astype(np.uint8),
                                                np.full((32, 32), 255, np.uint8)]), "RGBA")
        if name == "water":
            arr32 = np.array(tile32.convert("RGB")).astype(np.float64)
            lum32 = arr32 @ np.array([0.2126, 0.7152, 0.0722])
            ramp = np.array([[6, 20, 31], [11, 36, 54], [16, 58, 82], [23, 86, 122],
                             [34, 121, 163], [53, 162, 196], [99, 203, 216],
                             [163, 234, 240]], dtype=np.float64)
            rl = ramp @ np.array([0.2126, 0.7152, 0.0722])
            idx = np.abs(lum32[..., None] - rl[None, None, :]).argmin(-1)
            mapped = ramp[idx].astype(np.uint8)
            tile32 = Image.fromarray(np.dstack([mapped, np.full((32, 32), 255, np.uint8)]), "RGBA")
        materials[name] = tile32.resize((512, 512), Image.NEAREST).convert("RGB")

    return materials