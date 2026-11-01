"""Side-view spaceship tile set: coherent materials + deterministic structural tiles.

One Gemini call generates a 2x2 material board (deck / wall / grate / conduit)
whose four quadrants share the same palette and lighting.  Each quadrant is
resampled to a 32x32 true-pixel tile and made seamless with the project's
palette-aware toroidal seam median (no extra API call).  Structural edges,
hazard trim, light strips, vents and a starfield window are then derived
deterministically from those materials, so the tile atlas is a complete
side-view platformer kit rather than four loose textures.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from PIL import Image

from config.ship_config import MATERIALS, MATERIAL_PROMPT, TILE
from core.api_client import GeminiImageClient
from core.grid_resampler import resample_to_true_pixel, upscale_nearest
from core.palette_quantizer import (
    PALETTE_RGB,
    lock_palette,
    nearest_palette_indices,
    palette_violations,
    shade_rgb,
)
from environment.material_genesis import _fill_terrain, perlin_noise
from environment.seamless_toroidal import _seam_median, select_best_phase

def _quadrant_ramp(name: str) -> int:
    for m in MATERIALS:
        if m["id"] == name:
            return int(m["ramp"])
    return 0


def make_constraint_board(res: int = 1024, seed: int = 7) -> Image.Image:
    """2x2 palette-locked noise board used as the colour-temperature guide."""
    half = res // 2
    noise = perlin_noise(res, octaves=4, seed=seed)
    rgb = np.zeros((res, res, 3), dtype=np.uint8)
    for qi, m in enumerate(MATERIALS):
        row, col = divmod(qi, 2)
        y0, y1 = row * half, (row + 1) * half
        x0, x1 = col * half, (col + 1) * half
        n = noise[y0:y1, x0:x1]
        base = int(m["ramp"])
        shade = 1 + (n * 6).astype(np.int32).clip(1, 6)
        for s in range(7):
            mask = shade == (1 + s)
            rgb[y0:y1, x0:x1][mask] = PALETTE_RGB[base + s]
    return Image.fromarray(rgb, "RGB")


def _slice_quadrants(raw: Image.Image, inset: float = 0.02) -> list[Image.Image]:
    w, h = raw.size
    ix, iy = int(w * inset), int(h * inset)
    out = []
    for i in range(4):
        r, c = divmod(i, 2)
        out.append(raw.crop((c * w // 2 + ix, r * h // 2 + iy,
                             (c + 1) * w // 2 - ix, (r + 1) * h // 2 - iy)))
    return out


def _material_from_raw(raw: Image.Image) -> tuple[Image.Image, dict]:
    base = lock_palette(resample_to_true_pixel(raw.convert("RGB"), (TILE, TILE)))
    base = Image.fromarray(np.asarray(_fill_terrain(base)).astype(np.uint8), "RGBA")
    smoothed = _seam_median(base, width=2, passes=2)
    arr, py, px, ks = select_best_phase(np.asarray(smoothed.convert("RGBA")))
    tile = lock_palette(Image.fromarray(arr, "RGBA"))
    return tile, {"phase": [py, px], "ks": ks,
                  "violations": palette_violations(tile)}


def generate_materials(client: GeminiImageClient | None = None,
                       outdir: Path | str = "output/environment/ship",
                       force: bool = False) -> tuple[dict[str, Image.Image], dict]:
    """Generate the 2x2 ship material board and return four seamless tiles."""
    client = client or GeminiImageClient()
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    from config.namespaces import work_environment_dir
    board_path = outdir / "material_board.png"
    work_board = work_environment_dir("ship") / "material_board.png"
    if not board_path.exists() and work_board.exists():
        board_path = work_board
    if board_path.exists() and not force:
        raw = Image.open(board_path).convert("RGB")
    else:
        board = make_constraint_board(1024, seed=7)
        work = work_environment_dir("ship")
        work.mkdir(parents=True, exist_ok=True)
        board.save(work / "material_constraint.png")
        prompt = MATERIAL_PROMPT.format(
            deck=MATERIALS[0]["desc"], wall=MATERIALS[1]["desc"],
            grate=MATERIALS[2]["desc"], conduit=MATERIALS[3]["desc"])
        raw = client.edit(prompt, [board], role="sunburst", aspect="1:1", size="1K",
                          tag="ship-material-2x2-v1")
        raw.save(board_path)

    materials: dict[str, Image.Image] = {}
    reports: dict[str, dict] = {}
    for m, q in zip(MATERIALS, _slice_quadrants(raw)):
        name = m["id"]
        tile, rep = _material_from_raw(q)
        materials[name] = tile
        reports[name] = rep
        tdir = outdir / "tiles"
        tdir.mkdir(parents=True, exist_ok=True)
        tile.save(tdir / f"{name}_seamless.png")
        upscale_nearest(tile, 8).save(tdir / f"{name}_x8.png")
        # 3x3 checkerboard for visual seam inspection.
        cb = Image.new("RGBA", (TILE * 3, TILE * 3), (0, 0, 0, 0))
        for y in range(3):
            for x in range(3):
                cb.paste(tile, (x * TILE, y * TILE))
        cb.save(tdir / f"{name}_checkerboard.png")
        work = work_environment_dir("ship")
        (work / "tiles").mkdir(parents=True, exist_ok=True)
        q.save(work / "tiles" / f"{name}_raw.png")
        print(f"  {name:8s} ks={rep['ks']['ks_statistic']:.3f} "
              f"p={rep['ks']['p_value']:.3f}/{rep['ks']['p_value_3x3']:.3f} "
              f"pass={rep['ks']['pass']} phase={rep['phase']}")
    (outdir / "materials.json").write_text(json.dumps(reports, indent=2))
    return materials, reports


# ---------------------------------------------------------------------------
# Deterministic structural tiles
# ---------------------------------------------------------------------------

def _edge_lip(tile: Image.Image, rows: int = 4) -> Image.Image:
    """Bright top lip + shadow under it, for a walkable platform surface."""
    arr = np.array(tile.convert("RGBA"))
    rgb = arr[..., :3]
    top = shade_rgb(rgb[0:1], 2)
    rgb[0:rows] = np.where(np.arange(rows)[:, None, None] == 0, top, rgb[0:rows])
    arr[..., :3] = rgb
    return lock_palette(Image.fromarray(arr, "RGBA"))


def deck_top(tile: Image.Image) -> Image.Image:
    arr = np.array(tile.convert("RGBA"))
    rgb = arr[..., :3]
    rgb[0] = shade_rgb(rgb[0:1], 2)[0]
    rgb[1] = shade_rgb(rgb[1:2], 1)[0]
    rgb[2:4] = shade_rgb(rgb[2:4], -1)
    arr[..., :3] = rgb
    return lock_palette(Image.fromarray(arr, "RGBA"))


def deck_side(tile: Image.Image, side: str) -> Image.Image:
    arr = np.array(tile.convert("RGBA"))
    rgb = arr[..., :3]
    if side == "left":
        rgb[:, 0] = shade_rgb(rgb[:, 0:1], 2)[:, 0]
        rgb[:, 1] = shade_rgb(rgb[:, 1:2], -1)[:, 0]
        rgb[:, 2] = shade_rgb(rgb[:, 2:3], -2)[:, 0]
    else:
        rgb[:, -1] = shade_rgb(rgb[:, -1:], 2)[:, 0]
        rgb[:, -2] = shade_rgb(rgb[:, -2:-1], -1)[:, 0]
        rgb[:, -3] = shade_rgb(rgb[:, -3:-2], -2)[:, 0]
    arr[..., :3] = rgb
    return lock_palette(Image.fromarray(arr, "RGBA"))


def deck_corner(tile: Image.Image, side: str) -> Image.Image:
    out = deck_side(deck_top(tile), side)
    return out


def hazard_tile() -> Image.Image:
    arr = np.zeros((TILE, TILE, 4), dtype=np.uint8)
    arr[..., 3] = 255
    dark = PALETTE_RGB[1]
    gold = PALETTE_RGB[50]
    for y in range(TILE):
        for x in range(TILE):
            if (x + y) % 12 < 5:
                arr[y, x, :3] = gold
            else:
                arr[y, x, :3] = dark
    arr[:2, :, :3] = shade_rgb(PALETTE_RGB[4:5], 0)[0]
    arr[-2:, :, :3] = PALETTE_RGB[0]
    return lock_palette(Image.fromarray(arr, "RGBA"))


def window_tile(wall: Image.Image) -> Image.Image:
    rng = np.random.default_rng(11)
    arr = np.array(wall.convert("RGBA"))
    rgb = arr[..., :3]
    rgb[:] = PALETTE_RGB[0]
    # starfield
    stars = rng.random((TILE, TILE)) < 0.10
    stars[3:-3, 3:-3] &= rng.random((TILE - 6, TILE - 6)) < 0.75
    rgb[3:-3, 3:-3][stars[3:-3, 3:-3]] = PALETTE_RGB[39]
    # frame + cyan glow
    rgb[:3, :] = PALETTE_RGB[4]
    rgb[-3:, :] = PALETTE_RGB[3]
    rgb[:, :3] = PALETTE_RGB[4]
    rgb[:, -3:] = PALETTE_RGB[3]
    rgb[3, 3:-3] = PALETTE_RGB[35]
    arr[..., :3] = rgb
    return lock_palette(Image.fromarray(arr, "RGBA"))


def vent_tile(wall: Image.Image) -> Image.Image:
    arr = np.array(wall.convert("RGBA"))
    rgb = arr[..., :3]
    for y in range(7, 25, 4):
        rgb[y:y + 3, 6:26] = PALETTE_RGB[1]
        rgb[y, 6:26] = PALETTE_RGB[5]
        rgb[y + 2, 6:26] = PALETTE_RGB[0]
    arr[..., :3] = rgb
    return lock_palette(Image.fromarray(arr, "RGBA"))


def flat_wall() -> Image.Image:
    """Low-contrast large-area wall: no cyan strip, no strong repeating motif.

    The AI wall quadrant is intentionally detail-rich, so using it as a
    wallpaper makes a 48-tile room read as a barcode of vertical bars.  This
    deterministic panel keeps the same palette and rivets but removes the
    high-frequency motif; the detailed wall tile becomes an accent instead.
    """
    arr = np.zeros((TILE, TILE, 4), dtype=np.uint8)
    arr[..., 3] = 255
    arr[..., :3] = PALETTE_RGB[2]
    # subtle panel edges
    arr[:, 0, :3] = PALETTE_RGB[1]
    arr[:, 1, :3] = PALETTE_RGB[3]
    arr[0, :, :3] = PALETTE_RGB[1]
    arr[1, :, :3] = PALETTE_RGB[3]
    # rivets and scuffs
    for x, y in ((5, 6), (26, 6), (5, 25), (26, 25)):
        arr[y, x, :3] = PALETTE_RGB[4]
        arr[y + 1, x, :3] = PALETTE_RGB[0]
    rng = np.random.default_rng(23)
    scuff = rng.random((TILE, TILE)) < 0.035
    arr[scuff, :3] = PALETTE_RGB[3]
    # a single tiny status pixel so the wall is not completely dead
    arr[3, 29, :3] = PALETTE_RGB[35]
    return lock_palette(Image.fromarray(arr, "RGBA"))


def neutralize_violet(tile: Image.Image) -> Image.Image:
    """Turn the busy violet accent panel into a plain metal panel.

    Used as the large-area backdrop so the detailed panel tile becomes an
    occasional accent instead of a wallpaper that repeats every 32 px.
    """
    arr = np.array(tile.convert("RGBA"))
    rgb = arr[..., :3]
    idx = nearest_palette_indices(rgb.reshape(-1, 3)).reshape(rgb.shape[:2])
    violet = idx >= 56
    rgb[violet] = PALETTE_RGB[3]
    # keep a 1px vertical seam so the plain wall still reads as panelling
    rgb[:, 15] = PALETTE_RGB[1]
    rgb[:, 16] = PALETTE_RGB[4]
    arr[..., :3] = rgb
    return lock_palette(Image.fromarray(arr, "RGBA"))


def strip_tile(tile: Image.Image, color_index: int = 35, y: int = 5) -> Image.Image:
    arr = np.array(tile.convert("RGBA"))
    rgb = arr[..., :3]
    rgb[y, :] = PALETTE_RGB[color_index]
    rgb[y + 1, :] = PALETTE_RGB[color_index]
    rgb[y - 1, :] = PALETTE_RGB[2]
    rgb[y + 2, :] = PALETTE_RGB[1]
    arr[..., :3] = rgb
    return lock_palette(Image.fromarray(arr, "RGBA"))


def build_tileset(materials: dict[str, Image.Image],
                  outdir: Path | str = "output/environment/ship") -> dict:
    outdir = Path(outdir)
    tdir = outdir / "tiles"
    tdir.mkdir(parents=True, exist_ok=True)
    deck, wall, grate, conduit = (materials[k] for k in ("deck", "wall", "grate", "conduit"))

    tiles: dict[str, Image.Image] = {
        "deck_fill": deck,
        "deck_top": deck_top(deck),
        "deck_top_left": deck_corner(deck, "left"),
        "deck_top_right": deck_corner(deck, "right"),
        "deck_left": deck_side(deck, "left"),
        "deck_right": deck_side(deck, "right"),
        "grate_fill": grate,
        "grate_top": deck_top(grate),
        "wall": wall,
        "wall_plain": neutralize_violet(wall),
        "wall_flat": flat_wall(),
        "wall_flat_light": strip_tile(flat_wall(), 35, 5),
        "wall_flat_violet": strip_tile(flat_wall(), 59, 11),
        "wall_light": strip_tile(wall, 35, 5),
        "wall_violet": strip_tile(wall, 59, 11),
        "ceiling": deck_top(Image.fromarray(np.flipud(np.array(deck)), "RGBA")),
        "pipe_h": conduit,
        "pipe_v": Image.fromarray(np.rot90(np.array(conduit), 1).copy(), "RGBA"),
        "hazard": hazard_tile(),
        "vent": vent_tile(flat_wall()),
        "window": window_tile(wall),
        "light_strip": strip_tile(Image.new("RGBA", (TILE, TILE), (*PALETTE_RGB[2], 255)), 35, 15),
    }
    tiles = {k: lock_palette(v) for k, v in tiles.items()}
    for name, tile in tiles.items():
        tile.save(tdir / f"{name}.png")
        upscale_nearest(tile, 8).save(tdir / f"{name}_x8.png")

    names = sorted(tiles)
    cols = 8
    rows = (len(names) + cols - 1) // cols
    atlas = Image.new("RGBA", (cols * TILE, rows * TILE), (0, 0, 0, 0))
    for i, name in enumerate(names):
        r, c = divmod(i, cols)
        atlas.paste(tiles[name], (c * TILE, r * TILE))
    atlas = lock_palette(atlas)
    atlas.save(outdir / "tileset.png")
    preview = Image.new("RGB", atlas.size, (8, 8, 12))
    preview.paste(atlas, (0, 0), atlas)
    upscale_nearest(preview, 8).save(outdir / "tileset_preview_x8.png")
    meta = {
        "tile_size": TILE,
        "columns": cols,
        "rows": rows,
        "tiles": {name: {"index": i, "col": i % cols, "row": i // cols}
                  for i, name in enumerate(names)},
    }
    (outdir / "tileset.json").write_text(json.dumps(meta, indent=2))

    # A small assembled platform sample (wall backdrop + deck platform + props
    # that exist in this set) so the shapes can be checked without the full scene.
    sample = Image.new("RGBA", (TILE * 14, TILE * 8), (0, 0, 0, 255))
    for y in range(8):
        for x in range(14):
            sample.paste(tiles["wall_flat"] if y < 5 else tiles["deck_fill"], (x * TILE, y * TILE))
    for x in range(14):
        sample.paste(tiles["deck_top"], (x * TILE, 5 * TILE))
    for x, name in [(4, "vent"), (8, "wall_light"), (10, "window")]:
        sample.paste(tiles[name], (x * TILE, 2 * TILE))
    for x in range(14):
        sample.paste(tiles["hazard"], (x * TILE, 6 * TILE))
    sample = lock_palette(sample)
    sample.save(outdir / "tileset_sample.png")
    upscale_nearest(sample, 4).save(outdir / "tileset_sample_x4.png")
    return {"tiles": names, "atlas": "tileset.png", "sample": "tileset_sample.png",
            "meta": meta}
