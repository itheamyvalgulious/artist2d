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
        client = client or GeminiImageClient()
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
        work = work_environment_dir("ship")
        # Material inspection sheets are working files: only the 25 derived
        # structural tiles are shipped in `output/environment/ship/tiles/`.
        wdir = work / "tiles"
        wdir.mkdir(parents=True, exist_ok=True)
        tile.save(wdir / f"{name}_seamless.png")
        upscale_nearest(tile, 8).save(wdir / f"{name}_x8.png")
        # 3x3 checkerboard for visual seam inspection.
        cb = Image.new("RGBA", (TILE * 3, TILE * 3), (0, 0, 0, 0))
        for y in range(3):
            for x in range(3):
                cb.paste(tile, (x * TILE, y * TILE))
        cb.save(wdir / f"{name}_checkerboard.png")
        q.save(wdir / f"{name}_raw.png")
        print(f"  {name:8s} ks={rep['ks']['ks_statistic']:.3f} "
              f"p={rep['ks']['p_value']:.3f}/{rep['ks']['p_value_3x3']:.3f} "
              f"pass={rep['ks']['pass']} phase={rep['phase']}")
    (outdir / "materials.json").write_text(json.dumps(reports, indent=2))
    return materials, reports


# ---------------------------------------------------------------------------
# Deterministic structural tiles
# ---------------------------------------------------------------------------

def _hash01(x: int, y: int, seed: int = 0) -> float:
    """Deterministic 0..1 hash for 1 px wear/dither (no RNG state)."""
    n = (int(x) * 374761393 + int(y) * 668265263 + int(seed) * 362437) & 0xFFFFFFFF
    n = ((n ^ (n >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((n ^ (n >> 16)) & 0xFFFF) / 65535.0


def _plate_face() -> np.ndarray:
    """32x32 deck plate front face: joint bevel, recessed panels, rivets, wear.

    Deterministic replacement for the AI deck quadrant, which was a near-empty
    dark field once its bright band had been flattened (mean L 29.8, 5 colours).
    Density is deliberately brought up to the wall tiles: base + bevel + two
    recessed sub-panels + hash-based 1 px wear.

    The plate joint sits at x=16 / y=16 (not on the tile border) so the tile
    boundary falls inside a uniform field: the 2x2 repeat is continuous *and*
    the edge columns/rows are identical (seam difference 0), without mirroring.
    """
    arr = np.zeros((TILE, TILE, 4), dtype=np.uint8)
    arr[..., 3] = 255
    rgb = arr[..., :3]
    rgb[:] = PALETTE_RGB[2]
    # deliberate scuffs: a few 2-3 px scratches + 3 worn dents (no 1 px noise)
    for y, x, n in ((4, 6, 2), (10, 20, 3), (22, 25, 2), (26, 8, 3),
                    (30, 14, 2), (6, 28, 2)):
        rgb[y, x:x + n] = PALETTE_RGB[3]
    for y, x in ((12, 9), (19, 23), (27, 17)):
        rgb[y, x] = PALETTE_RGB[1]
    # horizontal plate joint at y=16 so the tile border lands inside the plate
    # body (row 31 == row 0 == body): the vertical repeat is continuous and the
    # edge rows are identical, with the joint still every 32 px.
    rgb[16, 2:] = PALETTE_RGB[1]
    rgb[17, 2:] = PALETTE_RGB[3]
    # vertical plate joint at the tile edge (mirrored to a 2 px groove by
    # seamless()); the bevel reads as the plate's top-left lit edge.
    rgb[:, 0] = PALETTE_RGB[1]
    rgb[:, 1] = PALETTE_RGB[3]
    # anti-slip tread: short vertical stamps between the joints (reads as a
    # textured deck band, not as a dashed seam line across the floor)
    for x in range(3, 32, 8):
        rgb[9, x:x + 2] = PALETTE_RGB[3]
        rgb[10, x:x + 2] = PALETTE_RGB[1]
    # rivets either side of the horizontal joint
    for x, y in ((5, 13), (26, 13), (5, 21), (26, 21)):
        rgb[y, x] = PALETTE_RGB[4]
        rgb[y + 1, x] = PALETTE_RGB[0]
    return arr


def deck_top(_tile: Image.Image | None = None) -> Image.Image:
    """Walk surface: 1 px bright lip on row 0, shadow under it, plate face below.

    y=512 is the actual lit deck surface.  Rows 1-2 are the lip's underside
    and shadow so the lip never reads as a floating white line.
    """
    arr = _plate_face()
    rgb = arr[..., :3]
    rgb[0, :] = PALETTE_RGB[6]
    rgb[1, :] = PALETTE_RGB[4]
    return lock_palette(Image.fromarray(arr, "RGBA"))


def deck_fill(_tile: Image.Image | None = None) -> Image.Image:
    """Deck front face: panelled plating with no repeated lit band."""
    return lock_palette(Image.fromarray(_plate_face(), "RGBA"))


def _cap_face(face: Image.Image) -> Image.Image:
    """Left platform end cap: lit edge, stepped bevel, then the plate face."""
    arr = np.array(face.convert("RGBA"))
    rgb = arr[..., :3]
    rgb[:, 0] = PALETTE_RGB[0]
    rgb[:, 1] = PALETTE_RGB[6]
    rgb[:, 2] = PALETTE_RGB[4]
    rgb[:, 3] = PALETTE_RGB[3]
    # chamfer the two outer corners so the cap reads as a cut block end
    rgb[0, 1:3] = PALETTE_RGB[4]
    rgb[-1, 1:3] = PALETTE_RGB[1]
    arr[..., :3] = rgb
    return lock_palette(Image.fromarray(arr, "RGBA"))


def deck_side(side: str) -> Image.Image:
    """Platform end cap. `right` is the exact mirror of `left`."""
    left = _cap_face(deck_fill())
    return left if side == "left" else left.transpose(Image.FLIP_LEFT_RIGHT)


def deck_corner(side: str) -> Image.Image:
    """Platform top corner: walk lip + end cap, `right` mirrors `left`."""
    left = _cap_face(deck_top())
    return left if side == "left" else left.transpose(Image.FLIP_LEFT_RIGHT)


def deck_step(side: str | None = None) -> Image.Image:
    """Raised platform step: tread, shadowed overhang, riser, kick plate.

    Reads as a step block, not a framed wall bay: a 4 px tread catching the
    top-left light, a 1 px overhang shadow, a mostly horizontal riser face
    (two tone bands, rivets, one equipment label) and a dark base.  The old
    face was a per-tile framed panel with a checkerboard vent band, which
    stacked into a row of "lockers" under the console.
    """
    arr = np.zeros((TILE, TILE, 4), dtype=np.uint8)
    arr[..., 3] = 255
    rgb = arr[..., :3]
    rgb[:] = PALETTE_RGB[2]
    # tread (top surface, catching the top-left light)
    rgb[0, :] = PALETTE_RGB[6]
    rgb[1, :] = PALETTE_RGB[5]
    rgb[2, :] = PALETTE_RGB[5]
    rgb[3, :] = PALETTE_RGB[4]
    rgb[4, :] = PALETTE_RGB[2]          # riser body directly under the tread
    # riser face: horizontal tone bands, no vertical frame
    rgb[5:27, :] = PALETTE_RGB[2]
    rgb[5, :] = PALETTE_RGB[1]
    rgb[12, :] = PALETTE_RGB[1]
    rgb[13, :] = PALETTE_RGB[3]
    rgb[22, :] = PALETTE_RGB[1]
    rgb[23, :] = PALETTE_RGB[4]
    # rivet pairs + one cyan equipment label per bay
    for x in (7, 24):
        for y in (8, 18):
            rgb[y, x] = PALETTE_RGB[4]
            rgb[y + 1, x] = PALETTE_RGB[0]
    # one recessed vent slot per bay instead of a loud repeating label
    rgb[17, 12:19] = PALETTE_RGB[1]
    rgb[18, 12:19] = PALETTE_RGB[3]
    # grip strip + base
    for x in range(5, 28, 3):
        rgb[26, x] = PALETTE_RGB[5]
        rgb[26, x + 1] = PALETTE_RGB[1]
    rgb[27, :] = PALETTE_RGB[1]
    rgb[28, :] = PALETTE_RGB[2]
    rgb[29, :] = PALETTE_RGB[3]
    rgb[30, :] = PALETTE_RGB[1]
    rgb[31, :] = PALETTE_RGB[0]
    face = lock_palette(Image.fromarray(arr, "RGBA"))
    if side == "left":
        return _cap_face(face)
    if side == "right":
        return _cap_face(face).transpose(Image.FLIP_LEFT_RIGHT)
    return face


def hazard_tile() -> Image.Image:
    """True 45-degree hazard stripes; exact wrap on both axes, no border.

    The pattern is ``(x + y) % 8``; 32 is a multiple of 8 so column 31 and row
    31 continue the diagonal into the next copy.  No edge band, and the tile is
    never passed through :func:`seamless` (that would mirror the stripes).
    """
    arr = np.zeros((TILE, TILE, 4), dtype=np.uint8)
    arr[..., 3] = 255
    yy, xx = np.mgrid[0:TILE, 0:TILE]
    gold = ((xx + yy) % 8) < 4
    arr[..., :3] = np.where(gold[..., None], PALETTE_RGB[50], PALETTE_RGB[1])
    # 1 px lit edge along the top of every gold stripe (reads as a bevel at 1x)
    edge = ((xx + yy) % 8) == 0
    arr[edge, :3] = PALETTE_RGB[51]
    return lock_palette(Image.fromarray(arr, "RGBA"))


def window_tile(_wall: Image.Image | None = None) -> Image.Image:
    """Recessed porthole: lit steel frame, sill, graded glass, single mullion.

    No crossing mullion and no purple bar: the glass carries a vertical value
    gradient, stars and one ringed planet, and the sill/bezel give the recess.
    """
    arr = np.zeros((TILE, TILE, 4), dtype=np.uint8)
    arr[..., 3] = 255
    rgb = arr[..., :3]
    rgb[:] = PALETTE_RGB[2]
    # outer joint
    rgb[0, :] = PALETTE_RGB[1]
    rgb[-1, :] = PALETTE_RGB[0]
    rgb[:, 0] = PALETTE_RGB[1]
    rgb[:, -1] = PALETTE_RGB[0]
    # steel frame, top-left lit / bottom-right shaded
    rgb[1:3, 1:31] = PALETTE_RGB[6]
    rgb[3, 1:31] = PALETTE_RGB[4]
    rgb[1:31, 1:3] = PALETTE_RGB[6]
    rgb[1:31, 3] = PALETTE_RGB[4]
    rgb[28:31, 1:31] = PALETTE_RGB[3]
    rgb[1:31, 28:31] = PALETTE_RGB[3]
    # inner bezel: 1 px dark recess top/left, lit lip bottom/right
    rgb[4, 4:28] = PALETTE_RGB[0]
    rgb[5:28, 4] = PALETTE_RGB[0]
    rgb[27, 4:28] = PALETTE_RGB[5]
    rgb[5:28, 27] = PALETTE_RGB[4]
    # glass 6..26 x 6..26: vertical gradient, dark at the top, teal near the sill
    rgb[5:27, 5:27] = PALETTE_RGB[33]
    rgb[5:11, 5:27] = PALETTE_RGB[32]
    rgb[5:7, 5:27] = PALETTE_RGB[33]
    rgb[20:27, 5:27] = PALETTE_RGB[34]
    rgb[25:27, 5:27] = PALETTE_RGB[35]
    # interior glow spilled on the glass from the sill
    rgb[26, 6:26] = PALETTE_RGB[36]
    # stars
    for x, y in ((8, 8), (14, 11), (23, 8), (11, 17), (24, 15), (9, 23),
                 (19, 22), (25, 23), (16, 7)):
        rgb[y, x] = PALETTE_RGB[6]
    for x, y in ((12, 9), (21, 18), (7, 13), (17, 19)):
        rgb[y, x] = PALETTE_RGB[5]
    # planet, upper right: 9 px disc, lit from the top-left, 1 px dark limb
    for y in range(5, 17):
        for x in range(16, 28):
            d = (x - 21) ** 2 + (y - 10) ** 2
            if d <= 16:
                lit = (x - 21) + (y - 10) <= -2
                rgb[y, x] = PALETTE_RGB[37] if lit else (
                    PALETTE_RGB[35] if d <= 9 else PALETTE_RGB[34])
            elif d <= 24:
                rgb[y, x] = PALETTE_RGB[0]
    rgb[7, 19:21] = PALETTE_RGB[38]
    rgb[8, 18] = PALETTE_RGB[38]
    # single vertical mullion (no horizontal bar -> no crosshair)
    rgb[5:27, 15] = PALETTE_RGB[1]
    rgb[5:27, 16] = PALETTE_RGB[3]
    # corner bolts in the frame
    for x, y in ((2, 2), (29, 2), (2, 29), (29, 29)):
        rgb[y, x] = PALETTE_RGB[7]
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


def pipe_tile(horizontal: bool = True) -> Image.Image:
    """Readable 3-cylinder pipe bundle (replace the AI cable mush)."""
    arr = np.array(flat_wall())
    rgb = arr[..., :3]
    tubes = (5, 14, 23)
    for ti, y0 in enumerate(tubes):
        body = PALETTE_RGB[3] if ti != 1 else PALETTE_RGB[4]
        rgb[y0, :] = PALETTE_RGB[6]
        rgb[y0 + 1:y0 + 3, :] = body
        rgb[y0 + 3, :] = PALETTE_RGB[1]
        # a cyan/violet status band every 16 px
        band = PALETTE_RGB[37] if ti == 0 else (PALETTE_RGB[59] if ti == 2 else PALETTE_RGB[5])
        rgb[y0 + 1:y0 + 3, 8:10] = band
        rgb[y0 + 1:y0 + 3, 24:26] = band
        # bolted joint at x=0 and x=16
        for x in (0, 16):
            rgb[y0:y0 + 4, x] = PALETTE_RGB[1]
            rgb[y0, x] = PALETTE_RGB[5]
    if not horizontal:
        rgb = np.rot90(rgb, 1).copy()
    arr[..., :3] = rgb
    return lock_palette(Image.fromarray(arr, "RGBA"))


def wall_panel() -> Image.Image:
    """Clean inset wall panel; replaces the 'broken doorway' AI motif."""
    arr = np.array(flat_wall())
    rgb = arr[..., :3]
    # inset frame: dark top/left, light bottom/right
    rgb[5, 4:28] = PALETTE_RGB[1]
    rgb[6:26, 4] = PALETTE_RGB[1]
    rgb[26, 4:28] = PALETTE_RGB[4]
    rgb[5:27, 27] = PALETTE_RGB[4]
    rgb[6, 5:27] = PALETTE_RGB[3]
    rgb[7:25, 5] = PALETTE_RGB[3]
    # corner rivets
    for x, y in ((6, 7), (25, 7), (6, 24), (25, 24)):
        rgb[y, x] = PALETTE_RGB[5]
        rgb[y + 1, x] = PALETTE_RGB[0]
    return lock_palette(Image.fromarray(arr, "RGBA"))


def wall_strip(color_index: int, x: int = 9) -> Image.Image:
    """Bare full-height light strip on the flat wall."""
    arr = np.array(flat_wall())
    rgb = arr[..., :3]
    rgb[:, x] = PALETTE_RGB[color_index]
    rgb[:, x - 1] = PALETTE_RGB[0]
    rgb[:, x + 1] = PALETTE_RGB[0]
    return lock_palette(Image.fromarray(arr, "RGBA"))


def wall_strip_panel(color_index: int, x: int = 9) -> Image.Image:
    """Inset-panel wall with a short vertical strip inside the recess."""
    arr = np.array(wall_panel())
    rgb = arr[..., :3]
    rgb[5:27, x] = PALETTE_RGB[color_index]
    rgb[5:27, x - 1] = PALETTE_RGB[0]
    rgb[5:27, x + 1] = PALETTE_RGB[0]
    return lock_palette(Image.fromarray(arr, "RGBA"))


def wall_plain_variant() -> Image.Image:
    """A second flat fill with a different seam position (not an alias)."""
    arr = np.array(flat_wall())
    rgb = arr[..., :3]
    rgb[:, 20] = PALETTE_RGB[1]
    rgb[:, 21] = PALETTE_RGB[4]
    rgb[15, 4:18] = PALETTE_RGB[1]
    rgb[16, 4:18] = PALETTE_RGB[4]
    return lock_palette(Image.fromarray(arr, "RGBA"))


def grate_fill(grate: Image.Image) -> Image.Image:
    """Readable horizontal-bar grate (replaces the AI X-lattice noise)."""
    arr = np.zeros((TILE, TILE, 4), dtype=np.uint8)
    arr[..., 3] = 255
    rgb = arr[..., :3]
    rgb[:] = PALETTE_RGB[2]
    for y in range(0, TILE, 4):
        rgb[y, :] = PALETTE_RGB[6]
        rgb[y + 1, :] = PALETTE_RGB[4]
        rgb[y + 2:y + 4, :] = PALETTE_RGB[0]
    # two vertical support ribs
    for x in (7, 24):
        rgb[:, x] = PALETTE_RGB[1]
        rgb[:, x + 1] = PALETTE_RGB[3]
    return lock_palette(Image.fromarray(arr, "RGBA"))


def grate_top(grate: Image.Image) -> Image.Image:
    """Floor-line grate: bright lip, recessed slots, 1 px inset frame."""
    arr = np.array(grate_fill(grate))
    rgb = arr[..., :3]
    rgb[0, :] = PALETTE_RGB[6]
    rgb[1, :] = PALETTE_RGB[4]
    rgb[2, :] = PALETTE_RGB[0]
    rgb[:, 0] = PALETTE_RGB[0]
    rgb[:, -1] = PALETTE_RGB[0]
    rgb[3, 1:-1] = PALETTE_RGB[1]
    # keep the deck's 1 px walk lip continuous through the grate insert
    rgb[0, 0] = PALETTE_RGB[6]
    rgb[0, -1] = PALETTE_RGB[6]
    arr[..., :3] = rgb
    return lock_palette(Image.fromarray(arr, "RGBA"))


def ceiling_tile() -> Image.Image:
    """Coffered ceiling band: beams, recessed coffers, lit top joint.

    Deliberately not a flipped deck copy: no walk lip, no deck plate motif.
    """
    arr = np.zeros((TILE, TILE, 4), dtype=np.uint8)
    arr[..., 3] = 255
    rgb = arr[..., :3]
    rgb[:] = PALETTE_RGB[1]
    # recessed coffers (dark top/left, lit bottom/right)
    for x0 in (3, 19):
        rgb[6, x0:x0 + 10] = PALETTE_RGB[0]
        rgb[7:26, x0] = PALETTE_RGB[0]
        rgb[7:26, x0 + 1:x0 + 10] = PALETTE_RGB[2]
        rgb[26, x0:x0 + 10] = PALETTE_RGB[4]
        rgb[7:26, x0 + 9] = PALETTE_RGB[3]
    # structural beams at the tile edge and the tile centre
    rgb[2:32, 0] = PALETTE_RGB[3]
    rgb[2:32, 1] = PALETTE_RGB[2]
    rgb[2:32, 16] = PALETTE_RGB[3]
    rgb[2:32, 17] = PALETTE_RGB[2]
    # lit joint along the top of the band (reads as a beam across the room)
    rgb[0, :] = PALETTE_RGB[6]
    rgb[1, :] = PALETTE_RGB[4]
    rgb[2, 2:16] = PALETTE_RGB[3]
    rgb[2, 18:32] = PALETTE_RGB[3]
    rgb[31, :] = PALETTE_RGB[2]
    return lock_palette(Image.fromarray(arr, "RGBA"))


def light_fixture(ceiling_base: Image.Image | None = None) -> Image.Image:
    """A hanging ceiling light whose top rows continue the ceiling tile."""
    base = ceiling_base if ceiling_base is not None else flat_wall()
    arr = np.array(base.convert("RGBA"))
    rgb = arr[..., :3]
    # The fixture sits in the second ceiling row: its top must continue the
    # ceiling's dark underside, not repeat the bright top lip.
    rgb[0:7, :] = rgb[-1:, :]
    # housing
    rgb[6:9, 2:30] = PALETTE_RGB[1]
    rgb[8:23, 3:29] = PALETTE_RGB[2]
    rgb[9:22, 4:28] = PALETTE_RGB[1]
    # bright tube + dithered glow below it
    rgb[17:20, 6:26] = PALETTE_RGB[38]
    rgb[18:19, 6:26] = PALETTE_RGB[6]
    for x in range(6, 26):
        if x % 2 == 0:
            rgb[20, x] = PALETTE_RGB[37]
        rgb[23, x] = PALETTE_RGB[1]
    arr[..., :3] = rgb
    return lock_palette(Image.fromarray(arr, "RGBA"))


def seamless(tile: Image.Image, wrap_x: bool = True, wrap_y: bool = True,
             band: int = 2) -> Image.Image:
    """Make opposite edges identical so the tile can repeat without a seam."""
    arr = np.array(tile.convert("RGBA"))
    rgb = arr[..., :3]
    if wrap_x:
        for k in range(band):
            rgb[:, -1 - k] = rgb[:, k]
    if wrap_y:
        for k in range(band):
            rgb[-1 - k, :] = rgb[k, :]
    arr[..., :3] = rgb
    return lock_palette(Image.fromarray(arr, "RGBA"))


def despeckle(tile: Image.Image) -> Image.Image:
    """Remove isolated 1 px noise specks without touching structural lines."""
    arr = np.array(tile.convert("RGBA"))
    rgb = arr[..., :3].copy()
    c = rgb[1:-1, 1:-1]
    u = rgb[:-2, 1:-1]
    d = rgb[2:, 1:-1]
    l = rgb[1:-1, :-2]
    r = rgb[1:-1, 2:]
    m = ((u == d).all(axis=2) & (l == r).all(axis=2) & (u == l).all(axis=2)
         & (u != c).any(axis=2))
    c[m] = u[m]
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


def door_tile(top: bool = False) -> Image.Image:
    """One half of a 32x64 bulkhead door pair.

    `door_top` = lintel + transom slit, no threshold; `door` = leaves +
    kick plate + hazard threshold, no window.  Both jambs are lighter than the
    wall base so the opening reads at 1x (the old right jamb was (20,20,28),
    darker than the wall).
    """
    arr = np.zeros((TILE, TILE, 4), dtype=np.uint8)
    arr[..., 3] = 255
    rgb = arr[..., :3]
    rgb[:] = PALETTE_RGB[2]
    # --- jambs: 3 px, lit on the left, mid steel on the right -------------
    rgb[:, 0] = PALETTE_RGB[0]
    rgb[:, 1] = PALETTE_RGB[5]
    rgb[:, 2] = PALETTE_RGB[4]
    rgb[:, 29] = PALETTE_RGB[4]
    rgb[:, 30] = PALETTE_RGB[3]
    rgb[:, 31] = PALETTE_RGB[0]
    # --- two leaves (3..28), centre seam at 15/16 -------------------------
    rgb[:, 3:29] = PALETTE_RGB[3]
    rgb[:, 3] = PALETTE_RGB[2]
    rgb[:, 28] = PALETTE_RGB[2]
    rgb[:, 15] = PALETTE_RGB[1]
    rgb[:, 16] = PALETTE_RGB[4]
    # leaf bevel + inset panel (dark top/left, lit bottom/right)
    for x0 in (4, 17):
        x1 = x0 + 10
        rgb[7, x0:x1] = PALETTE_RGB[1]
        rgb[7:27, x0] = PALETTE_RGB[1]
        rgb[26, x0:x1] = PALETTE_RGB[4]
        rgb[7:27, x1 - 1] = PALETTE_RGB[4]
        rgb[8:26, x0 + 1:x1 - 1] = PALETTE_RGB[2]
    if top:
        # lintel: 3 px bright header, no threshold
        rgb[0, :] = PALETTE_RGB[1]
        rgb[1, 1:31] = PALETTE_RGB[6]
        rgb[2, 1:31] = PALETTE_RGB[4]
        rgb[3, 1:31] = PALETTE_RGB[1]
        # transom: small dark-framed window, not a full-width light bar
        rgb[4, 8:24] = PALETTE_RGB[0]
        rgb[5:11, 8:24] = PALETTE_RGB[33]
        rgb[5:11, 8] = PALETTE_RGB[0]
        rgb[5:11, 23] = PALETTE_RGB[0]
        rgb[5, 9:23] = PALETTE_RGB[0]
        rgb[6, 9:23] = PALETTE_RGB[34]
        rgb[7:9, 9:23] = PALETTE_RGB[35]
        rgb[7:9, 15] = PALETTE_RGB[0]
        rgb[8, 12] = PALETTE_RGB[38]
        rgb[8, 19] = PALETTE_RGB[38]
        rgb[10, 9:23] = PALETTE_RGB[32]
        # leaf panel detail: two small stencils
        rgb[15, 7:12] = PALETTE_RGB[4]
        rgb[15, 20:25] = PALETTE_RGB[4]
        rgb[18, 7:12] = PALETTE_RGB[1]
        rgb[18, 20:25] = PALETTE_RGB[1]
    else:
        # kick plate on each leaf
        for x0 in (5, 18):
            rgb[19:22, x0:x0 + 9] = PALETTE_RGB[4]
            rgb[22, x0:x0 + 9] = PALETTE_RGB[1]
        # hazard threshold: only this tile carries it
        rgb[27, :] = PALETTE_RGB[0]
        for x in range(3, 29):
            rgb[28, x] = PALETTE_RGB[50] if (x // 3) % 2 == 0 else PALETTE_RGB[1]
            rgb[29, x] = PALETTE_RGB[50] if (x // 3) % 2 == 1 else PALETTE_RGB[1]
        rgb[30, :] = PALETTE_RGB[1]
        rgb[31, :] = PALETTE_RGB[0]
    arr[..., :3] = rgb
    return lock_palette(Image.fromarray(arr, "RGBA"))


def build_tileset(materials: dict[str, Image.Image],
                  outdir: Path | str = "output/environment/ship") -> dict:
    from config.namespaces import work_environment_dir
    outdir = Path(outdir)
    tdir = outdir / "tiles"
    tdir.mkdir(parents=True, exist_ok=True)
    deck, wall, grate, conduit = (materials[k] for k in ("deck", "wall", "grate", "conduit"))

    # Drop stale tile files from earlier rounds so the shipped folder is
    # exactly the atlas (deck_top_left.png was an orphan not in tileset.json).
    stale = ("deck_top_left", "deck_top_left_x8", "wall_plain", "wall_plain_x8")
    for stem in stale:
        for suffix in (".png",):
            p = tdir / f"{stem}{suffix}"
            if p.exists():
                p.unlink()

    wall_base = wall_panel()
    ceiling = ceiling_tile()
    tiles: dict[str, Image.Image] = {
        "deck_fill": deck_fill(deck),
        "deck_top": deck_top(deck),
        "deck_top_right": deck_corner("right"),
        "deck_left": deck_side("left"),
        "deck_right": deck_side("right"),
        "deck_step": deck_step(),
        "deck_step_left": deck_step("left"),
        "deck_step_right": deck_step("right"),
        "grate_fill": grate_fill(grate),
        "grate_top": grate_top(grate),
        # The AI 'wall' quadrant reads as a broken door jamb; use clean
        # deterministic panel/fill families with genuinely different designs.
        "wall": wall_base,
        "door": door_tile(),
        "door_top": door_tile(top=True),
        "wall_flat": flat_wall(),
        "wall_flat_light": wall_strip(37, 9),
        "wall_flat_violet": wall_strip(59, 22),
        "wall_light": wall_strip_panel(37, 9),
        "wall_violet": wall_strip_panel(59, 22),
        "ceiling": ceiling,
        "pipe_h": pipe_tile(True),
        "pipe_v": pipe_tile(False),
        "hazard": hazard_tile(),
        "vent": vent_tile(flat_wall()),
        "window": window_tile(wall_base),
        "light_strip": light_fixture(ceiling),
    }
    # AI-derived surfaces carry 1 px salt-and-pepper noise; remove it so the
    # wall reads as metal instead of a starfield.
    for k in ("wall", "wall_flat", "wall_flat_light", "wall_flat_violet",
              "wall_light", "wall_violet", "grate_fill", "grate_top"):
        tiles[k] = despeckle(tiles[k])
    # Structural tiles must repeat in the directions they are used:
    # deck faces horizontally, ceiling both ways, pipes/grate both ways.
    # `hazard` is generated exact by construction: passing it through
    # seamless() would mirror column 0 onto column 31 and break the diagonal.
    seam_x = ("deck_fill", "deck_top", "ceiling", "pipe_h", "pipe_v",
              "grate_fill", "grate_top", "wall", "wall_flat", "wall_flat_light",
              "wall_flat_violet", "wall_light", "wall_violet")
    seam_y = ("ceiling", "pipe_h", "pipe_v", "grate_fill", "grate_top",
              "wall", "wall_flat", "wall_flat_light", "wall_flat_violet",
              "wall_light", "wall_violet")
    for k in seam_x:
        tiles[k] = seamless(tiles[k], wrap_x=True, wrap_y=False)
    for k in seam_y:
        tiles[k] = seamless(tiles[k], wrap_x=False, wrap_y=True)
    tiles = {k: lock_palette(v) for k, v in tiles.items()}
    work_tiles = work_environment_dir("ship") / "tiles"
    work_tiles.mkdir(parents=True, exist_ok=True)
    for name, tile in tiles.items():
        tile.save(tdir / f"{name}.png")
        upscale_nearest(tile, 8).save(work_tiles / f"{name}_x8.png")
    # The shipped tiles folder is exactly the atlas: drop every stale working
    # preview / dropped-material artifact from earlier rounds.
    for p in sorted(tdir.glob("*.png")):
        if p.stem not in tiles:
            p.unlink()

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

    # A small room slice: wall + vertical strip + window + vent + a raised
    # dais with real side faces + a grate section + hazard.  This proves the
    # platform-edge tiles in context instead of showing isolated squares.
    SW, SH = 18, 9
    FLOOR = 6
    sample = Image.new("RGBA", (TILE * SW, TILE * SH), (0, 0, 0, 255))
    for y in range(FLOOR):
        for x in range(SW):
            sample.paste(tiles["wall_flat"], (x * TILE, y * TILE))
    # continuous vertical light strip at x=3
    for y in range(1, 5):
        sample.paste(tiles["wall_light"], (3 * TILE, y * TILE))
    for x, y, name in [(6, 2, "window"), (8, 2, "vent"),
                       (11, 2, "wall_violet"), (13, 3, "wall_light")]:
        sample.paste(tiles[name], (x * TILE, y * TILE))
    # ceiling light fixtures
    for x in (4, 9, 14):
        sample.paste(tiles["light_strip"], (x * TILE, 0))
    # floor with a grate section and a one-tile raised dais
    for x in range(SW):
        sample.paste(tiles["grate_top"] if x in (7, 8) else tiles["deck_top"],
                     (x * TILE, FLOOR * TILE))
        for y in range(FLOOR + 1, SH):
            sample.paste(tiles["deck_fill"], (x * TILE, y * TILE))
    for x, name in [(11, "deck_step_left"), (12, "deck_step"), (13, "deck_step_right")]:
        sample.paste(tiles[name], (x * TILE, (FLOOR - 1) * TILE))
    for x in (14, 15):
        sample.paste(tiles["hazard"], (x * TILE, (FLOOR + 1) * TILE))
    sample = lock_palette(sample)
    sample.save(outdir / "tileset_sample.png")
    upscale_nearest(sample, 4).save(outdir / "tileset_sample_x4.png")
    return {"tiles": names, "atlas": "tileset.png", "sample": "tileset_sample.png",
            "meta": meta}
