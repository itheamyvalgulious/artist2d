"""Module 3: Medium megastructure stamp generation (PLAN 模块三).

Produces a grounded building/tree/altar stamp (4x5 grid, 128x160 true pixels),
difference-mattes it against the ground, slices into 32x32 tiles with Y-sort
layer metadata, and renders a Y-sort demo placing a character in front of and
behind the structure.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from config.pipeline_config import BG_KEY_HEX, OUTPUT_DIR, TILE_SIZE, UPSCALE_FACTOR
from config.namespaces import environment_dir
from core.api_client import GeminiImageClient
from core.grid_resampler import (
    background_mask,
    estimate_background,
    resample_to_true_pixel,
    upscale_nearest,
)
from core.palette_quantizer import (
    PALETTE_RGB,
    bayer_threshold,
    hex_to_rgb,
    lock_palette,
    nearest_palette_indices,
    palette_violations,
    shade_rgb,
)

# ---------------------------------------------------------------------------
# Ground tile generation / loading
# ---------------------------------------------------------------------------

GROUND_PROMPT = (
    "A single 32x32 top-down pixel art cobblestone floor tile. Flat top-down view, "
    "crisp pixel clusters, no perspective, neutral grey-brown stone, 1px dark gaps "
    "between stones, seamless tiling, solid #FF00FF magenta background, 64-color "
    "palette, zero anti-aliasing, zero gradients."
)


def generate_ground_tile(api: GeminiImageClient) -> Image.Image:
    """Generate a 32x32 true-pixel ground tile via Gemini."""
    api_size = TILE_SIZE * UPSCALE_FACTOR  # 512
    raw = api.generate_one(
        GROUND_PROMPT,
        role="sunburst",
        aspect="1:1",
        size="1K",
        tag="ground-tile",
    )
    # Resize to api_size if needed
    if raw.size != (api_size, api_size):
        raw = raw.resize((api_size, api_size), Image.LANCZOS)
    tile = resample_to_true_pixel(raw, (TILE_SIZE, TILE_SIZE))
    tile = lock_palette(tile)
    return tile


def load_or_generate_ground_tile(api: GeminiImageClient) -> Image.Image:
    """Use PLAN module 2's seamless stone as the stamp ground tile."""
    module2 = environment_dir("field") / "stone_seamless.png"
    if module2.exists():
        return lock_palette(Image.open(module2).convert("RGBA"))
    tiles_dir = environment_dir("field") / "tiles"
    existing = sorted(tiles_dir.glob("*.png")) if tiles_dir.exists() else []
    if existing:
        tile = Image.open(existing[0]).convert("RGBA")
        tile = tile.resize((TILE_SIZE, TILE_SIZE), Image.NEAREST)
        tile = lock_palette(tile)
        tile.save(existing[0])  # keep the on-disk tile palette-pure too
        return tile

    print("  No ground tiles found – generating one via Gemini ...")
    tiles_dir.mkdir(parents=True, exist_ok=True)
    tile = generate_ground_tile(api)
    tile.save(tiles_dir / "ground_cobble.png")
    v, _ = palette_violations(tile)
    print(f"  Ground tile saved ({tile.size}), violations={v}")
    return tile


# ---------------------------------------------------------------------------
# Canvas construction
# ---------------------------------------------------------------------------

def tile_ground_on_canvas(
    canvas_w: int,
    canvas_h: int,
    tile: Image.Image,
    ground_true_rows: int,
    scale: int,
) -> Image.Image:
    """Tile the ground texture across the bottom rows of an API-scale canvas.

    The rest of the canvas is filled with magenta.
    """
    tile_api = upscale_nearest(tile, scale)  # 32*scale x 32*scale
    tw, th = tile_api.size
    ground_px = ground_true_rows * TILE_SIZE * scale
    canvas = Image.new("RGB", (canvas_w, canvas_h), BG_KEY_HEX)

    # Tile ground across the bottom ground_px rows
    for y in range(canvas_h - ground_px, canvas_h, th):
        for x in range(0, canvas_w, tw):
            # Crop if the tile extends beyond canvas
            box = (0, 0, min(tw, canvas_w - x), min(th, canvas_h - y))
            canvas.paste(tile_api.crop(box), (x, y))
    return canvas


def create_envelope_mask(
    canvas_w: int,
    canvas_h: int,
    ground_true_rows: int,
    scale: int,
    margin_ground_cols: int = 1,
    footprint_cols: float = 2.2,
) -> Image.Image:
    """Create a mask: white in the center envelope, black in ground corners.

    The top (magenta) region is fully white. The bottom ground region has a
    white center band (building footprint) and black corner columns where the
    original ground is preserved.
    """
    mask = Image.new("L", (canvas_w, canvas_h), 255)  # all white by default
    draw = ImageDraw.Draw(mask)

    ground_y_start = canvas_h - ground_true_rows * TILE_SIZE * scale
    # The building may only grow inside a narrow central footprint on the
    # ground rows; the rest of the ground is locked and later keyed out.
    fp = int(footprint_cols * TILE_SIZE * scale)
    if ground_y_start < canvas_h:
        draw.rectangle([0, ground_y_start, canvas_w - 1, canvas_h - 1], fill=0)
        draw.rectangle([(canvas_w - fp) // 2, ground_y_start,
                        (canvas_w + fp) // 2, canvas_h - 1], fill=255)

    return mask


# ---------------------------------------------------------------------------
# Difference matting
# ---------------------------------------------------------------------------

def difference_matte(
    stamp_rgba: Image.Image,
    ground_tiled_rgba: Image.Image,
    bg_rgb: np.ndarray,
    footprint_mask: Image.Image | None = None,
    ground_rows: int = 2,
) -> Image.Image:
    """Extract the building from the generated stamp via difference matting.

    - Pixels matching the background (magenta)      -> alpha = 0
    - Pixels identical to the original ground tile  -> alpha = 0
    - Pixels that are a darker shade of the ground
      ramp (AI-drawn contact shadow)                -> darkest palette colour
                                                        + Bayer dither,
                                                        alpha = 255
    - Everything else (building / tree / altar)     -> alpha = 255, as-is
    """
    stamp = lock_palette(stamp_rgba)
    ground = lock_palette(ground_tiled_rgba)

    s_arr = np.array(stamp.convert("RGBA"))
    g_arr = np.array(ground.convert("RGBA"))
    h, w = s_arr.shape[:2]

    # Palette indices for every pixel
    s_idx = nearest_palette_indices(s_arr[..., :3]).reshape(h, w)
    g_idx = nearest_palette_indices(g_arr[..., :3]).reshape(h, w)

    # Background: original alpha plus connected magenta.  lock_palette() sets
    # transparent pixels' RGB to (0,0,0), so a pure magenta key would miss the
    # already-transparent backdrop and keep it as an opaque black rectangle.
    bg_mask = background_mask(s_arr[..., :3], bg_rgb) | (s_arr[..., 3] == 0)

    # Same as ground (palette-index exact, plus a LAB tolerance for the AI's
    # slightly shifted ground redraw)
    from core.palette_quantizer import rgb_to_lab
    s_lab = rgb_to_lab(s_arr[..., :3])
    g_lab = rgb_to_lab(g_arr[..., :3])
    lab_dist = np.linalg.norm(s_lab - g_lab, axis=-1)
    same_ground = ((s_idx == g_idx) | (lab_dist < 9.0)) & ~bg_mask

    # Ramp analysis: the AI often repaints the ground one or two shades
    # lighter/darker; within +/-2 shades of the same ramp it is still ground.
    s_ramp = s_idx // 8
    g_ramp = g_idx // 8
    same_ramp = (s_ramp == g_ramp) & ~bg_mask
    ramp_close = same_ramp & (np.abs(s_idx - g_idx) <= 2)
    same_ground = same_ground | ramp_close
    darker = same_ramp & (s_idx < g_idx - 2)
    is_shadow = darker & ~same_ground

    # Ground flood: in the ground rows, the ground is connected to the left /
    # right canvas edges.  Flood through ground-like pixels from those edges;
    # everything reached is ground (transparent), while the building base
    # blocks the flood and stays opaque.
    from scipy import ndimage as _ndi
    ground_like = same_ground | ramp_close
    ground_start = h - ground_rows * TILE_SIZE
    seed = np.zeros((h, w), dtype=bool)
    if ground_start < h:
        seed[ground_start:, 0] = True
        seed[ground_start:, w - 1] = True
    labels_g, _n_g = _ndi.label(ground_like)
    edge_labels = np.unique(labels_g[seed & ground_like])
    edge_labels = edge_labels[edge_labels != 0]
    flood_ground = np.isin(labels_g, edge_labels)

    # Building: everything else that isn't background or ground
    is_building = ~bg_mask & ~same_ground & ~is_shadow
    is_building &= ~flood_ground

    # Build output RGBA
    out = np.zeros((h, w, 4), dtype=np.uint8)

    # Building pixels: keep as-is
    out[is_building, :3] = s_arr[is_building, :3]
    out[is_building, 3] = 255

    # Shadow pixels: darkest shade of the ramp + Bayer dither, fully opaque
    if is_shadow.any():
        # Darken shadow pixels toward the darkest shade in their ramp
        shadow_rgb = shade_rgb(s_arr[is_shadow, :3], -3)
        # Bayer dither between the ground colour and the darkest shade
        bayer_map = bayer_threshold((h, w), strength=0.6)

        # Build flat index mapping for shadow pixels
        shadow_ys, shadow_xs = np.nonzero(is_shadow)
        shadow_flat_idx = {f"{sy}:{sx}": i for i, (sy, sx) in enumerate(zip(shadow_ys, shadow_xs))}

        for sy, sx in zip(shadow_ys, shadow_xs):
            key = f"{sy}:{sx}"
            idx = shadow_flat_idx[key]
            if bayer_map[sy, sx] > 0.5:
                out[sy, sx, :3] = shadow_rgb[idx]
            else:
                out[sy, sx, :3] = g_arr[sy, sx, :3]  # keep ground colour
        out[is_shadow, 3] = 255

    # Same-as-ground and background pixels: alpha=0 (already zeroed)

    out[flood_ground, 3] = 0
    out[flood_ground, :3] = 0

    # Restrict the grounded base to the building's own width: take the
    # silhouette immediately above the ground rows and keep a narrow band.
    if ground_start > 2:
        above = ~bg_mask[ground_start - 2]
        xs = np.nonzero(above)[0]
        if len(xs):
            bx0 = max(0, int(xs.min()) - 6)
            bx1 = min(w, int(xs.max()) + 7)
            band = np.zeros((h, w), dtype=bool)
            band[ground_start:, bx0:bx1] = True
            out[ground_start:, :][~band[ground_start:, :]] = 0

    # Clean the grounded band: keep only sizeable connected components and
    # close 1px holes, so the base is a coherent plinth rather than a
    # checkerboard of ground fragments.
    bs = h - ground_rows * TILE_SIZE
    if bs < h:
        bottom_alpha = out[bs:, :, 3] > 0
        from scipy import ndimage as _ndi2
        lab_b, n_b = _ndi2.label(bottom_alpha)
        keep_b = np.zeros_like(bottom_alpha)
        for lbl in range(1, n_b + 1):
            comp = lab_b == lbl
            if comp.sum() >= 40:
                keep_b |= comp
        keep_b = _ndi2.binary_closing(keep_b, iterations=1) | keep_b
        out[bs:, :, 3] = np.where(keep_b, 255, 0).astype(np.uint8)
        out[bs:, :, :3][~keep_b] = 0

    if footprint_mask is not None:
        fm = np.array(footprint_mask.convert("L").resize((w, h), Image.NEAREST)) > 127
        ground_start = h - ground_rows * TILE_SIZE
        outside = np.zeros((h, w), dtype=bool)
        outside[ground_start:, :] = True
        outside &= ~fm
        out[outside, 3] = 0
        out[outside, :3] = 0

    result = Image.fromarray(out, "RGBA")
    return lock_palette(result)


def refine_grounding(stamp: Image.Image, ground_rows: int = 2,
                     ground_tile: Image.Image | None = None,
                     source: Image.Image | None = None) -> Image.Image:
    """Complete the AI-grounded base into a clean plinth, keeping its centre.

    The matte keeps the AI's central steps and contact shadow, but the
    generative repaint also leaves mis-classified cobble fragments beside
    them.  The sides are rebuilt as a clean two-step stone base textured with
    the AI's own grounded band, then the AI's central base pixels are pasted
    back on top, so the AI's grounding survives while the band still tiles
    and reaches the Y-sort pivot.  The plan's (0,0,0,128) shadow is baked as
    opaque dithered palette pixels (hard metric 1 forbids partial alpha).
    """
    arr = np.array(stamp.convert("RGBA"))
    h, w = arr.shape[:2]
    bs = h - ground_rows * TILE_SIZE
    if bs <= 0:
        return stamp
    ai_band = arr[bs:, :].copy()
    above = arr[max(0, bs - 2):bs]
    opaque = above[..., 3] > 0
    xs = np.nonzero(opaque.any(axis=0))[0] if opaque.any() else np.array([w // 3, 2 * w // 3])
    bx0, bx1 = int(xs.min()), int(xs.max()) + 1
    if bx1 - bx0 < 48:
        cx = (bx0 + bx1) // 2
        bx0, bx1 = max(0, cx - 32), min(w, cx + 32)
    tex_src = source if source is not None else ground_tile
    gt = None
    if tex_src is not None:
        gt_full = np.array(tex_src.convert("RGB"))
        gt = gt_full[bs:, :]
        from scipy import ndimage as _ndi
        gt = _ndi.median_filter(gt, size=(3, 3, 1))
        gh, gw = gt.shape[:2]

    arr[bs:, :, 3] = 0
    arr[bs:, :, :3] = 0
    outline = np.array([35, 35, 46], np.uint8)
    top0, top1 = bs, bs + 14
    base0, base1 = top1, h
    for y in range(top0, top1):
        for x in range(max(0, bx0 - 4), min(w, bx1 + 4)):
            arr[y, x, :3] = gt[(y - top0) % gh, x % gw] if gt is not None else (155, 155, 176)
            arr[y, x, 3] = 255
    for y in range(base0, base1):
        for x in range(max(0, bx0 - 7), min(w, bx1 + 7)):
            col = gt[(y - base0) % gh, x % gw] if gt is not None else np.array([111, 111, 136], np.uint8)
            if y >= base1 - 5:
                from core.palette_quantizer import shade_rgb as _shade
                col = _shade(np.array(col, np.uint8), -2)
            arr[y, x, :3] = col
            arr[y, x, 3] = 255
    for y in range(top0, base1):
        for x in range(max(0, bx0 - 7), min(w, bx1 + 7)):
            if arr[y, x, 3] == 0:
                continue
            if y == top0 or y == base0 or y == base1 - 1:
                arr[y, x, :3] = outline
            elif x <= max(0, bx0 - 6) or x >= min(w - 1, bx1 + 5):
                from core.palette_quantizer import shade_rgb as _sh
                arr[y, x, :3] = _sh(arr[y, x, :3], -2)

    # Paste the AI's own central base (steps / roots / contact shadow) back.
    cx = (bx0 + bx1) // 2
    half = min(30, max(18, (bx1 - bx0) // 4))
    for y in range(bs, h):
        for x in range(max(0, cx - half), min(w, cx + half)):
            if ai_band[y - bs, x, 3] > 0:
                arr[y, x] = ai_band[y - bs, x]
    return lock_palette(Image.fromarray(arr, "RGBA"))


# ---------------------------------------------------------------------------
# Slicing & metadata export
# ---------------------------------------------------------------------------

def slice_stamp(
    stamp: Image.Image,
    grid_w: int,
    grid_h: int,
    out_dir: Path,
) -> list[Image.Image]:
    """Slice a stamp into TILE_SIZE x TILE_SIZE pieces, return ordered list."""
    out_dir.mkdir(parents=True, exist_ok=True)
    pieces = []
    for row in range(grid_h):
        for col in range(grid_w):
            x0 = col * TILE_SIZE
            y0 = row * TILE_SIZE
            piece = stamp.crop((x0, y0, x0 + TILE_SIZE, y0 + TILE_SIZE))
            piece = lock_palette(piece)
            piece.save(out_dir / f"tile_r{row}_c{col}.png")
            pieces.append(piece)
    return pieces


def export_metadata(
    out_dir: Path,
    grid_w: int,
    grid_h: int,
    ground_rows: int,
) -> None:
    """Write stamp_metadata.json with Y-sort layers and collision flags."""
    tiles = []
    for row in range(grid_h):
        for col in range(grid_w):
            tile_id = f"tile_r{row}_c{col}"
            if row >= grid_h - ground_rows:
                # Bottom rows: sorted body layer, collision enabled
                pivot_y = TILE_SIZE  # tile bottom edge
                entry = {
                    "id": tile_id,
                    "row": row,
                    "col": col,
                    "layer": "sorted_body",
                    "collision": True,
                    "pivot_y": pivot_y,
                }
            else:
                # Upper rows: overhead canopy, no collision
                entry = {
                    "id": tile_id,
                    "row": row,
                    "col": col,
                    "layer": "overhead_canopy",
                    "collision": False,
                }
            tiles.append(entry)

    meta = {
        "grid": {"width": grid_w, "height": grid_h},
        "pivot": {"x": grid_w * TILE_SIZE // 2, "y": grid_h * TILE_SIZE},
        "tile_size": TILE_SIZE,
        "ground_rows": ground_rows,
        "tiles": tiles,
    }
    (out_dir / "stamp_metadata.json").write_text(json.dumps(meta, indent=2))
    print(f"  Metadata -> {out_dir / 'stamp_metadata.json'}")


# ---------------------------------------------------------------------------
# Y-Sort demo
# ---------------------------------------------------------------------------

def render_ysort_demo(
    pieces: list[Image.Image],
    grid_w: int,
    grid_h: int,
    out_dir: Path,
    ground_rows: int = 2,
) -> None:
    """Render the Y-sort layering demo with the real knight sprite.

    Left: the player stands in front of the shrine and is drawn on top of the
    sorted body.  Right: the player stands behind it; the overhead canopy is
    composited after the player, so the roof cuts the head off while the rest
    of the sprite still reads, exactly as the exported layer metadata intends.
    """
    T = TILE_SIZE
    map_w, map_h = grid_w * T, grid_h * T
    margin = 32
    panel_w = map_w + 64

    stamp_full = Image.new("RGBA", (map_w, map_h), (0, 0, 0, 0))
    for row in range(grid_h):
        for col in range(grid_w):
            piece = pieces[row * grid_w + col]
            stamp_full.paste(piece, (col * T, row * T), piece)

    ground_path = out_dir / "ground_tile.png"
    if ground_path.exists():
        ground_tile = Image.open(ground_path).convert("RGBA")
    else:
        ground_tile = Image.new("RGBA", (T, T), (64, 96, 48, 255))
    ground = Image.new("RGBA", (panel_w, map_h), (0, 0, 0, 0))
    for y in range(0, map_h, T):
        for x in range(0, panel_w, T):
            ground.paste(ground_tile, (x, y), ground_tile)

    knight_path = Path(__file__).resolve().parent.parent / "output" / "character" / "knight" / "idle" / "frames" / "frame_00.png"
    if knight_path.exists():
        char = Image.open(knight_path).convert("RGBA")
    else:
        char = Image.new("RGBA", (32, 48), (0, 0, 0, 0))
        d = ImageDraw.Draw(char)
        d.rectangle([10, 16, 22, 40], fill=(120, 32, 32, 255))
        d.rectangle([11, 4, 21, 17], fill=(176, 176, 200, 255))
    # Overlap the shrine's right edge so one half is occluded when behind.
    char_x = 120
    char_y = map_h - char.height - 2

    def compose(front: bool) -> Image.Image:
        scene = ground.copy()
        if front:
            scene.alpha_composite(stamp_full, (margin, 0))
            scene.alpha_composite(char, (char_x, char_y))
        else:
            scene.alpha_composite(char, (char_x, char_y))
            scene.alpha_composite(stamp_full, (margin, 0))
        return scene

    demo_w = panel_w * 2 + 16
    demo = Image.new("RGBA", (demo_w, map_h), (0, 0, 0, 0))
    demo.alpha_composite(compose(False), (0, 0))
    demo.alpha_composite(compose(True), (panel_w + 16, 0))

    from PIL import ImageFont
    d = ImageDraw.Draw(demo)
    try:
        font = ImageFont.load_default()
        for ox, label in ((8, "BEHIND"), (panel_w + 24, "IN FRONT")):
            d.rectangle([ox - 3, 3, ox + 6 * len(label) + 3, 16], fill=(8, 8, 12, 255))
            d.text((ox, 6), label, fill=(255, 255, 255, 255), font=font)
    except Exception:
        pass

    demo = lock_palette(demo)
    demo_path = out_dir / "ysort_demo.png"
    demo.save(demo_path)
    print(f"  Y-Sort demo -> {demo_path}")


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def build_stamp_medium(
    api: GeminiImageClient,
    out_dir: Path | None = None,
    prompt_override: str | None = None,
    ground_tile: Image.Image | None = None,
) -> dict:
    """Full Module 3 pipeline.

    Returns a dict with paths and metrics.
    """
    out_dir = Path(out_dir) if out_dir else environment_dir("field") / "stamp"
    out_dir.mkdir(parents=True, exist_ok=True)

    # --- Grid parameters ---
    grid_w, grid_h = 4, 5          # 4 columns x 5 rows
    ground_rows = 2                # bottom 2 rows are ground
    true_w = grid_w * TILE_SIZE    # 128
    true_h = grid_h * TILE_SIZE    # 160
    scale = UPSCALE_FACTOR          # 16
    api_w = true_w * scale          # 2048
    api_h = true_h * scale          # 2560

    print(f"Module 3: stamp {grid_w}x{grid_h} ({true_w}x{true_h} true px, {api_w}x{api_h} API)")

    # --- Ground tile ---
    if ground_tile is None:
        ground_tile = load_or_generate_ground_tile(api)
    else:
        ground_tile = lock_palette(ground_tile.convert("RGBA"))
    ground_tile.save(out_dir / "ground_tile.png")

    # --- Canvas ---
    canvas = tile_ground_on_canvas(api_w, api_h, ground_tile, ground_rows, scale)
    canvas.save(out_dir / "canvas_base.png")

    # Ground-tiled reference (used for difference matting later)
    ground_tiled = tile_ground_on_canvas(true_w, true_h, ground_tile, ground_rows, 1)
    ground_tiled.save(out_dir / "ground_tiled_ref.png")

    # --- Mask ---
    mask = create_envelope_mask(api_w, api_h, ground_rows, scale, margin_ground_cols=1)
    mask.save(out_dir / "mask.png")

    # --- Prompt ---
    if prompt_override:
        prompt = prompt_override
    else:
        prompt = (
            "A complete pixel-art ancient stone shrine standing on the cobblestone ground. "
            "The shrine has a peaked roof with dark tiles, two wooden pillars, a small altar "
            "inside, and stone steps at the base. The roof top must clearly separate from the "
            "solid #FF00FF magenta background above. The base must cast a dark contact shadow "
            "onto the cobblestone ground, with roots or stone base blending naturally into "
            "the stones. Flat top-down-oblique perspective, crisp pixel clusters, 64-color "
            "palette, 1px dark outlines, zero anti-aliasing, zero gradients, no blur."
        )

    # --- API call (edit/inpaint) ---
    print(f"  Calling Gemini edit (sunburst) ...")
    bg_rgb = np.array(hex_to_rgb(BG_KEY_HEX), dtype=np.float64)
    result = api.inpaint(
        canvas,
        mask,
        prompt,
        role="sunburst",
        aspect="4:5",
        size="2K",
        tag="stamp-shrine-4x5",
    )
    result = result.resize((api_w, api_h), Image.LANCZOS)
    result.save(out_dir / "api_result.png")

    # --- Resample to true pixels ---
    stamp_true = resample_to_true_pixel(result, (true_w, true_h), bg_rgb=bg_rgb)
    stamp_true.save(out_dir / "stamp_raw.png")

    # --- Difference matting ---
    footprint_true = mask.resize((true_w, true_h), Image.NEAREST)
    stamp_matted = difference_matte(stamp_true, ground_tiled, bg_rgb,
                                    footprint_mask=footprint_true,
                                    ground_rows=ground_rows)
    stamp_matted = refine_grounding(stamp_matted, ground_rows, ground_tile,
                                    source=stamp_true)
    stamp_matted.save(out_dir / "stamp_matted.png")

    # --- Slice ---
    pieces = slice_stamp(stamp_matted, grid_w, grid_h, out_dir / "tiles")

    # --- Metadata ---
    export_metadata(out_dir, grid_w, grid_h, ground_rows)

    # --- Y-Sort demo ---
    render_ysort_demo(pieces, grid_w, grid_h, out_dir, ground_rows)

    # --- Metrics ---
    vp, vo = palette_violations(stamp_matted)
    violations = vp + vo
    print(f"  Palette violations: partial_alpha={vp}, off_palette={vo}")

    report = {
        "module": "stamp_medium",
        "grid": f"{grid_w}x{grid_h}",
        "true_pixels": f"{true_w}x{true_h}",
        "ground_rows": ground_rows,
        "tile_count": len(pieces),
        "palette_violations": violations,
        "output_dir": str(out_dir),
        "files": {
            "stamp_matted": str(out_dir / "stamp_matted.png"),
            "metadata": str(out_dir / "stamp_metadata.json"),
            "ysort_demo": str(out_dir / "ysort_demo.png"),
        },
    }

    (out_dir / "report.json").write_text(json.dumps(report, indent=2))
    print(f"  Stamp complete, violations={violations}")
    return report


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    api = GeminiImageClient()
    build_stamp_medium(api)