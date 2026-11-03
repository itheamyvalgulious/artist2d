"""Compose the spaceship interior from the ship tiles and generated modules.

The whole side-view ship hall is the "mega": structural hull ribs, a viewport,
a reactor core, wall/floor tiles, pipes and the three pilot medium props are
assembled into one large room.  The same assembly is exported twice:

* ``mega/ship/ship_mega_1x.png``   – structure + props (no character)
* ``showcase/ship/scene_1x.png``   – the same room with agent poses

Composition order matters for contact shadows: the deck (and the reactor's
hazard pad) are written first, then every grounded object, and only then are
the dithered contact footprints stamped *below* the deck rim (``base_y + 1``)
so the 1 px bright lip survives and the boots stay readable.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from config.namespaces import environment_dir, mega_dir, showcase_dir
from config.pipeline_config import TILE_SIZE
from core.palette_quantizer import PALETTE_RGB, lock_palette, palette_violations

W, H = 48, 20              # tiles
FLOOR_ROW = 16             # deck surface
BIG = 2

# Clear wall bays between the five 4-tile hull ribs.
BAYS = [(4, 9), (14, 21), (26, 33), (38, 43)]
# x tile of the bulkhead door (32x64 pair on the deck line) and the agent.
DOOR_TILE = 31
AGENT_TILE = 29.2
HAZARD_BAY = (38, 43)      # 6-tile bay that holds the reactor pad
PAD_TILES = 5              # the pad itself: 5 tiles (160 px), centred in the bay
DECK_LIP = 2               # deck_top rows 0-1 are the lit walk lip
DAIS_LIP = 4               # deck_step rows 0-3 are the tread
PAD_TREAD = 4              # pad tread rows on top of the hazard side face


def _load_tiles(env: Path) -> tuple[dict[str, Image.Image], dict]:
    meta = json.loads((env / "tileset.json").read_text())
    tiles = {}
    for name in meta["tiles"]:
        p = env / "tiles" / f"{name}.png"
        tiles[name] = Image.open(p).convert("RGBA")
    return tiles, meta


def _rgb(i: int) -> tuple[int, int, int]:
    return tuple(int(v) for v in PALETTE_RGB[i])


def _contact_depths(sprite: Image.Image, height: int) -> np.ndarray:
    """Per-column shadow depth derived from the sprite's base silhouette.

    Every column that reaches the sprite's bottom 4 rows is a contact column;
    the mask is dilated by 1 px and 1-px gaps are closed so the footprint is
    continuous.  Columns whose lowest opaque pixel sits 1-3 px above the base
    (chamfers, a raised heel) get a proportionally shallower shadow, so the
    footprint follows the object instead of being a fixed rectangle.
    """
    a = np.array(sprite.convert("RGBA"))[..., 3]
    h, w = a.shape
    ymax = np.full(w, -1, dtype=int)
    for x in range(w):
        ys = np.nonzero(a[:, x])[0]
        if len(ys):
            ymax[x] = int(ys.max())
    if (ymax < 0).all():
        return np.zeros(w, dtype=int)
    base = int(ymax.max())
    touch = ymax >= base - 3
    fp = touch.copy()
    fp[1:] |= touch[:-1]
    fp[:-1] |= touch[1:]
    for x in range(1, w - 1):
        if not fp[x] and fp[x - 1] and fp[x + 1]:
            fp[x] = True
    depths = np.where(fp, np.clip(height - (base - ymax), 1, height), 0)
    return depths.astype(int)


def _shadow(scene: Image.Image, x_off: int, depths: np.ndarray,
            first_row: int) -> None:
    """Stamp a solid contact core + ordered-dither falloff.

    Row 0 is a **solid** palette-0 core across the whole footprint (not a dash),
    row 1 is solid as well when the falloff is 5 rows tall (the reactor), then
    rows fall off at 5/8, 3/8 and 1/8 with a different 8-px phase per row.
    ``first_row`` is already past the landing surface's lip/tread, so the bright
    deck lip, dais tread and pad tread are never written.
    """
    if depths is None or len(depths) == 0 or depths.max() <= 0:
        return
    arr = np.array(scene)
    H = int(depths.max())
    core = 2 if H >= 5 else 1
    fall = (0.625, 0.375, 0.125, 0.0625)
    for i in range(H):
        y = first_row + i
        if y < 0 or y >= scene.height:
            continue
        dens = 1.0 if i < core else fall[min(i - core, len(fall) - 1)]
        for x in np.nonzero(depths > i)[0]:
            sx = x_off + int(x)
            if not (0 <= sx < scene.width):
                continue
            if arr[y, sx, 3] == 0:
                continue
            if dens < 1.0 and ((sx * 3 + i * 5) % 8) >= dens * 8:
                continue
            arr[y, sx, :3] = PALETTE_RGB[0]
    scene.paste(Image.fromarray(arr, "RGBA"))


def _shadow_height(sprite: Image.Image) -> int:
    """Falloff height scales with the sprite: 3 rows, 5 rows for the reactor."""
    return 5 if sprite.height >= 130 else 3


def _paste_grounded(scene: Image.Image, sprite: Image.Image, x: int, base_y: int,
                    lip: int, shadows: list) -> None:
    """Composite a sprite with its bbox bottom on ``base_y``; queue its shadow.

    ``lip`` is the height of the landing surface's lit edge (deck 2 px, dais and
    reactor pad 4 px) that the shadow must start below.
    """
    bbox = sprite.getbbox()
    if bbox is None:
        return
    y = base_y - bbox[3]
    scene.alpha_composite(sprite, (x, y))
    heights = _shadow_height(sprite)
    shadows.append((x, _contact_depths(sprite, heights), base_y + lip))


def _cargo_low(cargo: Image.Image) -> Image.Image:
    """Two-crate variant of the cargo sprite (same generator, shorter stack).

    Row 26 of `cargo_stack/sprite.png` is the shared outline between the top and
    middle crates, so cutting there keeps a closed 1-px outline and the middle
    crate's lid.  Used for the second bay instance so the left bay is not two
    identical stacks (v6 M1).
    """
    return cargo.crop((0, 26, cargo.width, cargo.height))


def _service_band(w: int, h: int = 39, variant: int = 0) -> Image.Image:
    """Designed 118x39 sleeve that lengthens the rib shaft at 1:1.

    The raw rib is 203 px tall (50 cap + 103 mid + 50 base); three 103 px mids
    plus cap and base reach 409 px, so a 39 px band is needed to reach the
    448 px floor.  Instead of a flat near-black plinth this band continues the
    rib's two outer columns and centre conduit bay with louvers, rivets and a
    lit left edge, and it ends exactly on the real base flare.

    Three variants (louver pitch, status marking, bracket) are used across the
    five ribs so they are no longer pixel-identical; every variant keeps the
    same lit-left / shaded-right columns, so the light direction is unchanged.
    """
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(out)
    x0, x1 = 10, w - 11          # same silhouette as the shaft segment
    d.rectangle([x0, 0, x1, h - 1], fill=_rgb(2))
    d.line([x0, 0, x0, h - 1], fill=_rgb(0))
    d.line([x1, 0, x1, h - 1], fill=_rgb(0))
    # outer structural columns (lit on the left, shaded on the right)
    for a, b, lit in ((x0 + 1, 31, 4), (86, x1 - 1, 2)):
        d.rectangle([a, 0, b, h - 1], fill=_rgb(2))
        d.line([a, 0, a, h - 1], fill=_rgb(lit))
        d.line([a + 1, 0, a + 1, h - 1], fill=_rgb(lit - 1 if lit > 2 else 1))
        d.line([b, 0, b, h - 1], fill=_rgb(1))
        # column rivets + a panel break
        for yy in (8, 20, 32):
            d.point((a + 4, yy), fill=_rgb(4))
            d.point((a + 4, yy + 1), fill=_rgb(0))
        d.line([a, 16, b, 16], fill=_rgb(1))
        d.line([a, 17, b, 17], fill=_rgb(3))
    # centre bay: recessed louver sleeve with a cyan status tick
    d.rectangle([32, 0, 85, h - 1], fill=_rgb(1))
    d.line([32, 0, 32, h - 1], fill=_rgb(0))
    d.line([85, 0, 85, h - 1], fill=_rgb(0))
    d.line([33, 1, 84, 1], fill=_rgb(3))
    if variant == 1:
        rows = (5, 10, 15, 20, 25, 30, 35)
    elif variant == 2:
        rows = (9, 17, 25, 33)
    else:
        rows = (7, 12, 17, 22, 27, 32)
    for yy in rows:
        d.line([36, yy, 81, yy], fill=_rgb(0))
        d.line([36, yy + 1, 81, yy + 1], fill=_rgb(3))
    if variant == 1:
        # warm status dashes on the right of the bay + a bracket strip
        d.rectangle([60, 4, 70, 5], fill=_rgb(50))
        d.point((62, 4), fill=_rgb(53))
        d.rectangle([60, 32, 70, 33], fill=_rgb(50))
        d.line([56, 2, 57, h - 3], fill=_rgb(4))
        d.line([58, 2, 58, h - 3], fill=_rgb(1))
    elif variant == 2:
        # cyan status bar low in the bay + a bolt row
        d.rectangle([40, 26, 60, 28], fill=_rgb(37))
        d.point((42, 27), fill=_rgb(38))
        for xx in (38, 50, 62, 74):
            d.point((xx, 35), fill=_rgb(4))
            d.point((xx, 36), fill=_rgb(0))
    else:
        d.rectangle([38, 3, 48, 5], fill=_rgb(37))
        d.point((40, 4), fill=_rgb(38))
    # consistent 1 px join line at both ends of the band
    d.line([x0 + 1, 0, x1 - 1, 0], fill=_rgb(0))
    d.line([x0 + 1, h - 1, x1 - 1, h - 1], fill=_rgb(0))
    return out


def _rib_module(mg: Path, variant: int = 0) -> Image.Image:
    """One 448 px rib at 1:1 pixel scale (no non-integer stretching).

    cap 50 + mid 103x3 + designed 39 px sleeve + the raw 50 px base flare,
    ending exactly on the floor line.  The old build closed the last 39 px with
    a flat near-black plinth that sliced the X-braced foot.
    """
    im = Image.open(mg / "elements" / "hull_frame" / "sprite.png").convert("RGBA")
    bbox = im.getchannel("A").getbbox()
    if bbox:
        im = im.crop(bbox)
    w, h = im.size
    top = im.crop((0, 0, w, 50))
    mid = im.crop((0, 50, w, 153))
    bottom = im.crop((0, 153, w, 203))
    out = Image.new("RGBA", (128, 448), (0, 0, 0, 0))
    px = (128 - w) // 2
    out.alpha_composite(top, (px, 0))
    for y in (50, 153, 256):
        out.alpha_composite(mid, (px, y))
    out.alpha_composite(_service_band(w, variant=variant), (px, 359))
    out.alpha_composite(bottom, (px, 398))
    # consistent beveled join at every module boundary (no partial joins)
    d = ImageDraw.Draw(out)
    for y in (50, 153, 256, 359, 398):
        d.line([px + 1, y, px + w - 2, y], fill=_rgb(0))
        d.line([px + 1, y + 1, px + w - 2, y + 1], fill=_rgb(3))
    return lock_palette(out)


def _collar(scene: Image.Image, x: int, y: int) -> None:
    d = ImageDraw.Draw(scene)
    d.rectangle([x + 2, y - 1, x + 125, y + 2], fill=_rgb(0))
    d.rectangle([x + 3, y, x + 124, y + 1], fill=_rgb(3))
    for bx in (x + 16, x + 48, x + 80, x + 112):
        d.point((bx, y), fill=_rgb(6))
        d.point((bx, y + 1), fill=_rgb(1))


def _flange(scene: Image.Image, x: int, y: int, h: int = 32) -> None:
    """A 4px pipe flange with a light rim and two bolts (not a black slot)."""
    d = ImageDraw.Draw(scene)
    d.rectangle([x, y, x + 3, y + h - 1], fill=_rgb(1))
    d.line([x, y, x + 3, y], fill=_rgb(5))
    d.line([x + 4, y + 2, x + 4, y + h - 3], fill=_rgb(3))
    d.point((x + 1, y + 4), fill=_rgb(6))
    d.point((x + 1, y + h - 5), fill=_rgb(6))


def _pad_tread(scene: Image.Image, x0: int, x1: int, y: int) -> None:
    """Turn the hazard band into a real 1-tile platform.

    The hazard stripes stay on the *side face* only; the top is the same 4-px
    tread the dais uses (156 / 113 / 113 / 80) so both platforms read alike, the
    ends get a 3-px chamfered side thickness, and the face starts on the next
    row.  The pad's own contact shadow on the deck is queued by compose().
    """
    d = ImageDraw.Draw(scene)
    h = TILE_SIZE
    # tread: lit lip, two bevel rows, mid row (identical to deck_step's tread)
    d.rectangle([x0, y, x1 - 1, y], fill=_rgb(6))
    d.rectangle([x0, y + 1, x1 - 1, y + 2], fill=_rgb(5))
    d.rectangle([x0, y + 3, x1 - 1, y + 3], fill=_rgb(4))
    # side thickness: chamfered end faces, lit on the left / shaded on the right
    for ex, lit, face in ((x0, 5, 3), (x1 - 3, 3, 2)):
        d.rectangle([ex, y, ex + 2, y + h - 1], fill=_rgb(face))
        d.line([ex, y, ex, y + h - 1], fill=_rgb(0))
        d.line([ex + 1, y + 1, ex + 1, y + h - 1], fill=_rgb(lit))
        d.line([ex + 2, y + 1, ex + 2, y + h - 1], fill=_rgb(1))



def compose(include_character: bool = True,
            env: Path | None = None, mg: Path | None = None) -> Image.Image:
    env = Path(env) if env else environment_dir("ship")
    mg = Path(mg) if mg else mega_dir("ship")
    tiles, _ = _load_tiles(env)
    scene = Image.new("RGBA", (W * TILE_SIZE, H * TILE_SIZE), (0, 0, 0, 255))
    shadows: list[tuple[int, int, int]] = []

    # --- background wall: flat base, framed bay edges, cornice/skirting ----
    # (8,6) sat exactly under the vertical conduit at tile 8; moved to tile 7
    windows = {(7, 6), (30, 7)}
    vents = {(6, 9), (18, 8), (28, 9), (40, 8)}
    for y in range(2, FLOOR_ROW):
        for x in range(W):
            name = "wall_flat"
            for bx0, bx1 in BAYS:
                if bx0 <= x <= bx1:
                    if y == 3 or y == 12:
                        name = "wall"
                    elif x == bx0:
                        name = "wall_flat_light"
                    elif x == bx1:
                        name = "wall_flat_violet"
            if (x, y) in vents:
                name = "vent"
            if (x, y) in windows:
                name = "window"
            scene.paste(tiles[name], (x * TILE_SIZE, y * TILE_SIZE))

    # --- ceiling, conduits, ceiling lights ---------------------------------
    # 1 tile left of the bay-edge accent columns (x=9/21/33), which the opaque
    # pipe used to hide in three of the four bays
    for x in (8, 20, 32):
        for y in range(1, 14):
            scene.paste(tiles["pipe_v"], (x * TILE_SIZE, y * TILE_SIZE))
    for y in range(2):
        for x in range(W):
            scene.paste(tiles["ceiling"], (x * TILE_SIZE, y * TILE_SIZE))
    for x in (5, 13, 25, 37, 43):
        scene.paste(tiles["light_strip"], (x * TILE_SIZE, TILE_SIZE))
    for x0, x1 in ((5, 10), (14, 22), (26, 34), (38, 44)):
        for x in range(x0, x1):
            scene.paste(tiles["pipe_h"], (x * TILE_SIZE, 2 * TILE_SIZE))
        _flange(scene, x0 * TILE_SIZE, 2 * TILE_SIZE)
        _flange(scene, x1 * TILE_SIZE - 4, 2 * TILE_SIZE)
    # lower conduit run sits one tile higher than before so the 32x64 door
    # opening is not crossed by a pipe at door height
    for x0, x1 in ((4, 10), (14, 22), (26, 34), (38, 44)):
        for x in range(x0, x1):
            scene.paste(tiles["pipe_h"], (x * TILE_SIZE, 13 * TILE_SIZE))
        _flange(scene, x0 * TILE_SIZE, 13 * TILE_SIZE)
        _flange(scene, x1 * TILE_SIZE - 4, 13 * TILE_SIZE)
    for x in (8, 20, 32):
        _flange(scene, x * TILE_SIZE, 13 * TILE_SIZE)

    # --- structural ribs: one 448 px ceiling-to-floor piece ----------------
    # No mirroring (that would flip the light): three service-sleeve variants
    # are distributed palindromically so the five ribs are not identical while
    # every one stays lit from the left.
    hulls = [_rib_module(mg, v) for v in range(3)]
    for x, vi in zip((0, 10, 22, 34, 44), (0, 1, 2, 1, 0)):
        scene.alpha_composite(hulls[vi], (x * TILE_SIZE, 2 * TILE_SIZE))

    # --- viewport with a recessed mount ------------------------------------
    viewport = Image.open(mg / "elements" / "viewport" / "sprite.png").convert("RGBA")
    vx = 16 * TILE_SIZE + (128 - viewport.width) // 2
    vy = 4 * TILE_SIZE
    d = ImageDraw.Draw(scene)
    d.rectangle([vx - 3, vy - 3, vx + viewport.width + 2, vy + viewport.height + 2],
                outline=_rgb(0), width=3)
    d.rectangle([vx - 1, vy - 1, vx + viewport.width, vy + viewport.height],
                outline=_rgb(4), width=1)
    scene.alpha_composite(viewport, (vx, vy))

    # --- bulkhead door: drawn in front of the wall/conduit, in a clear bay --
    door_x = DOOR_TILE * TILE_SIZE
    scene.paste(tiles["door_top"], (door_x, (FLOOR_ROW - 2) * TILE_SIZE))
    scene.paste(tiles["door"], (door_x, (FLOOR_ROW - 1) * TILE_SIZE))
    d.rectangle([door_x - 1, (FLOOR_ROW - 2) * TILE_SIZE, door_x - 1,
                 FLOOR_ROW * TILE_SIZE - 1], fill=_rgb(0))
    d.rectangle([door_x + TILE_SIZE, (FLOOR_ROW - 2) * TILE_SIZE, door_x + TILE_SIZE,
                 FLOOR_ROW * TILE_SIZE - 1], fill=_rgb(0))

    # --- deck / floor, dais and the reactor's hazard pad -------------------
    # grate strip beside the airlock: the only clean 2-tile floor span that no
    # prop or contact shadow lands on (the old pair sat under the agent)
    grate_cols = {32, 33}
    for x in range(W):
        top = tiles["grate_top"] if x in grate_cols else tiles["deck_top"]
        scene.paste(top, (x * TILE_SIZE, FLOOR_ROW * TILE_SIZE))
        for row in range(FLOOR_ROW + 1, H):
            scene.paste(tiles["deck_fill"], (x * TILE_SIZE, row * TILE_SIZE))
    dais_x0, dais_x1 = 15 * TILE_SIZE, 21 * TILE_SIZE
    for x, name in ((15, "deck_step_left"), (16, "deck_step"), (17, "deck_step"),
                    (18, "deck_step"), (19, "deck_step"), (20, "deck_step_right")):
        scene.paste(tiles[name], (x * TILE_SIZE, (FLOOR_ROW - 1) * TILE_SIZE))
    # the dais is a 192-px block standing on the deck: it gets the same solid
    # core + falloff footprint under its own base as the reactor pad
    shadows.append((dais_x0, np.full(dais_x1 - dais_x0, 3, dtype=int),
                    FLOOR_ROW * TILE_SIZE + DECK_LIP))
    hz0, hz1 = HAZARD_BAY
    bay_x0, bay_x1 = hz0 * TILE_SIZE, (hz1 + 1) * TILE_SIZE
    pad_w = PAD_TILES * TILE_SIZE
    pad_x0 = bay_x0 + (bay_x1 - bay_x0 - pad_w) // 2
    pad_x1 = pad_x0 + pad_w
    pad_y = (FLOOR_ROW - 1) * TILE_SIZE
    # hazard is the pad's *side face* only; the top is a real tread.  The pad is
    # narrower than its bay, so only the in-span part of each 32-px cell is used
    # (the 45-degree phase is unaffected: 32 is a multiple of the 8-px period).
    for cell in range(hz0, hz1 + 1):
        cx = cell * TILE_SIZE
        ox, ex = max(pad_x0, cx), min(pad_x1, cx + TILE_SIZE)
        if ex <= ox:
            continue
        scene.paste(tiles["hazard"].crop((ox - cx, 0, ex - cx, TILE_SIZE)), (ox, pad_y))
    _pad_tread(scene, pad_x0, pad_x1, pad_y)
    # the pad is a block on the deck: its own contact shadow, below the deck lip
    shadows.append((pad_x0, np.full(pad_w, 3, dtype=int),
                    FLOOR_ROW * TILE_SIZE + DECK_LIP))

    # --- reactor: stands on the hazard pad, full plinth visible ------------
    reactor_full = Image.open(mg / "elements" / "reactor_core" / "sprite.png").convert("RGBA")
    rb = reactor_full.getchannel("A").getbbox()
    reactor = reactor_full.crop(rb) if rb else reactor_full
    rx = pad_x0 + (pad_x1 - pad_x0 - reactor.width) // 2
    ry = pad_y - reactor.height
    # recessed mount frame: left/top/right only, so the reactor's base meets
    # the hazard pad through its dithered contact shadow instead of a black bar
    top = ry - 3
    bot = ry + reactor.height - 1
    d.rectangle([rx - 3, top, rx + reactor.width + 2, top + 1], fill=_rgb(0))
    d.rectangle([rx - 3, top, rx - 2, bot], fill=_rgb(0))
    d.rectangle([rx + reactor.width + 1, top, rx + reactor.width + 2, bot], fill=_rgb(0))
    d.line([rx - 1, top + 2, rx + reactor.width, top + 2], fill=_rgb(4))
    d.line([rx - 1, top + 2, rx - 1, bot - 1], fill=_rgb(4))
    d.line([rx + reactor.width, top + 2, rx + reactor.width, bot - 1], fill=_rgb(4))
    scene.alpha_composite(reactor, (rx, ry))
    shadows.append((rx, _contact_depths(reactor, _shadow_height(reactor)),
                    pad_y + PAD_TREAD))

    # --- medium props ------------------------------------------------------
    props = env / "props"
    cargo = Image.open(props / "cargo_stack" / "sprite.png").convert("RGBA")
    console = Image.open(props / "console_bank" / "sprite.png").convert("RGBA")
    server = Image.open(props / "server_rack" / "sprite.png").convert("RGBA")
    # Left bay: a full three-crate stack and, 102 px to its right, a shorter
    # two-crate stack mirrored, so the bay no longer reads as a copy-paste pair
    # (v6 M1).  Both variants come from the same deterministic cargo generator.
    _paste_grounded(scene, cargo, 143, FLOOR_ROW * TILE_SIZE, DECK_LIP, shadows)
    _paste_grounded(scene, _cargo_low(cargo).transpose(Image.FLIP_LEFT_RIGHT), 245,
                    FLOOR_ROW * TILE_SIZE, DECK_LIP, shadows)
    # Console on the 192 px dais (shadow starts below the 4-px tread).
    _paste_grounded(scene, console, 16 * TILE_SIZE + (128 - console.width) // 2,
                    (FLOOR_ROW - 1) * TILE_SIZE, DAIS_LIP, shadows)
    # Server rack in the door bay, left of the opening.
    _paste_grounded(scene, server, 27 * TILE_SIZE + 8, FLOOR_ROW * TILE_SIZE,
                    DECK_LIP, shadows)

    # --- character ---------------------------------------------------------
    if include_character:
        ch = Path(__file__).resolve().parent.parent / "output" / "character" / "agent"
        idle_p = ch / "idle" / "frames" / "frame_00.png"
        if idle_p.exists():
            idle = Image.open(idle_p).convert("RGBA")
            # Beside the door (body 952-979, door 992-1023), facing right
            # toward it: the 60-px clear opening and the 53-px agent share one
            # shot, which is the scale proof.
            _paste_grounded(scene, idle, int(AGENT_TILE * TILE_SIZE),
                            FLOOR_ROW * TILE_SIZE, DECK_LIP, shadows)

    # --- contact shadows last: every grounded object, below the deck rim ---
    for x_off, depths, first_row in shadows:
        _shadow(scene, x_off, depths, first_row)

    return lock_palette(scene)


def main() -> None:
    env = environment_dir("ship")
    mg = mega_dir("ship")
    mg.mkdir(parents=True, exist_ok=True)
    mega = compose(include_character=False, env=env, mg=mg)
    mega.save(mg / "ship_mega_1x.png")
    mega.resize((mega.width * BIG, mega.height * BIG), Image.NEAREST).save(mg / "ship_mega_preview.png")
    scene = compose(include_character=True, env=env, mg=mg)
    out = showcase_dir("ship")
    out.mkdir(parents=True, exist_ok=True)
    scene.save(out / "scene_1x.png")
    scene.resize((scene.width * BIG, scene.height * BIG), Image.NEAREST).save(out / "scene.png")
    focus = scene.crop((27 * TILE_SIZE, 11 * TILE_SIZE, 37 * TILE_SIZE, 17 * TILE_SIZE))
    focus.resize((focus.width * 4, focus.height * 4), Image.NEAREST).save(
        out / "scene_focus_x4.png")
    # 6x shadow plate: the two 1-tile platforms (dais under the console, reactor
    # pad) side by side, so the contact footprints can be checked at 6x without
    # cropping scene_1x.png by hand.  Palette-safe (scene pixels + palette-0 bg).
    left = scene.crop((470, 455, 700, 530))
    right = scene.crop((1216, 455, 1446, 530))
    plate = Image.new("RGBA", (left.width + right.width + 15, left.height + 10),
                      tuple(int(v) for v in PALETTE_RGB[0]) + (255,))
    plate.alpha_composite(left, (5, 5))
    plate.alpha_composite(right, (left.width + 10, 5))
    plate.resize((plate.width * 6, plate.height * 6), Image.NEAREST).save(
        out / "scene_shadows_x6.png")
    # Character placement metadata is measured from the current frame so the
    # layout never claims a stale body rectangle.
    idle_p = (Path(__file__).resolve().parent.parent / "output" / "character"
              / "agent" / "idle" / "frames" / "frame_00.png")
    agent_text = f"idle frame 00 pasted at x={int(AGENT_TILE * TILE_SIZE)}"
    if idle_p.exists():
        ib = Image.open(idle_p).getchannel("A").getbbox()
        if ib:
            bx0 = int(AGENT_TILE * TILE_SIZE) + ib[0]
            bx1 = int(AGENT_TILE * TILE_SIZE) + ib[2] - 1
            agent_text += (f", opaque body x={bx0}-{bx1}, i.e. {DOOR_TILE * TILE_SIZE - bx1 - 1} px "
                           f"left of the door (x={DOOR_TILE * TILE_SIZE}-{DOOR_TILE * TILE_SIZE + 31}), "
                           "facing right toward it")
    layout = {
        "scene": {"width_tiles": W, "height_tiles": H, "tile_size": TILE_SIZE,
                  "floor_row": FLOOR_ROW},
        "mega_elements": [
            {"id": "hull_frame", "count": 5,
             "placement": "single 448px ribs at x=0,10,22,34,44 (ceiling y=64 to floor y=512), identical top-left light"},
            {"id": "viewport", "count": 1, "placement": "x=16,y=4 with recessed mount"},
            {"id": "reactor_core", "count": 1,
             "placement": "centred on the 6-tile hazard platform in the right bay, standing on its 4-px tread (base y=480)"},
        ],
        "medium_structures": [
            {"id": "cargo_stack", "count": 2,
             "placement": ("left bay: 3-crate stack at x=143 (y=425-511) and a shorter "
                           "2-crate stack mirrored at x=245 (y=451-511), 102 px apart")},
            {"id": "console_bank", "count": 1,
             "placement": "x=16 on the raised dais under the viewport"},
            {"id": "server_rack", "count": 1, "placement": "door bay, x=872 px"},
        ],
        "platforms": {
            "dais": "tiles 15-20 (x=480-671), base row 511, own contact shadow rows 514-516",
            "reactor_pad": ("5 tiles (x=1232-1391), centred in the 6-tile bay; 4-px tread "
                            "480-483, hazard side face 484-511, own contact shadow rows 514-516"),
        },
        "tiles_in_scene": {
            "door": f"tile {DOOR_TILE} (x={DOOR_TILE * TILE_SIZE}..{DOOR_TILE * TILE_SIZE + 31}), rows 14-15 (y=448..511)",
            "hazard": ("raised 1-tile platform: 4-px tread on top, hazard on the side "
                       "face only, chamfered ends, own contact shadow on the deck"),
        },
        "character": [agent_text],
        "palette_violations": list(palette_violations(scene)),
    }
    (mg / "ship_layout.json").write_text(json.dumps(layout, indent=2))
    print("mega", mega.size, "scene", scene.size, "purity", palette_violations(scene))
    print("->", mg / "ship_mega_preview.png")
    print("->", out / "scene.png")


if __name__ == "__main__":
    main()
