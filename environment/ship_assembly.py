"""Compose the spaceship interior from the ship tiles and generated modules.

The whole side-view ship hall is the "mega": structural hull ribs, a viewport,
a reactor core, wall/floor tiles, pipes and the three pilot medium props are
assembled into one large room.  The same assembly is exported twice:

* ``mega/ship/ship_mega_1x.png``   – structure + props (no character)
* ``showcase/ship/scene_1x.png``   – the same room with agent poses
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from PIL import Image

from config.namespaces import environment_dir, mega_dir, showcase_dir
from config.pipeline_config import TILE_SIZE
from core.palette_quantizer import PALETTE_RGB, lock_palette, palette_violations

W, H = 48, 20              # tiles
FLOOR_ROW = 16             # deck surface
BIG = 2


def _load_tiles(env: Path) -> tuple[dict[str, Image.Image], dict]:
    meta = json.loads((env / "tileset.json").read_text())
    tiles = {}
    for name in meta["tiles"]:
        p = env / "tiles" / f"{name}.png"
        tiles[name] = Image.open(p).convert("RGBA")
    return tiles, meta


def _shadow(layer: Image.Image, x0: int, y0: int, x1: int, y1: int,
            height: int = 5) -> None:
    """Opaque dithered contact shadow on the deck (no partial alpha)."""
    arr = np.array(layer)
    for i in range(height):
        y = y1 + i
        if y < 0 or y >= layer.height:
            continue
        for x in range(max(0, x0), min(layer.width, x1)):
            if (x + y) % 3 == 0:
                arr[y, x, :3] = PALETTE_RGB[1]
                arr[y, x, 3] = 255
            elif (x + y) % 5 == 0:
                arr[y, x, :3] = PALETTE_RGB[0]
                arr[y, x, 3] = 255
    layer.paste(Image.fromarray(arr, "RGBA"))


def _paste_grounded(scene: Image.Image, sprite: Image.Image, x: int, y: int,
                    shadow: bool = True) -> None:
    scene.alpha_composite(sprite, (x, y))
    if shadow:
        _shadow(scene, x + max(2, sprite.width // 6), y + sprite.height,
                x + sprite.width - max(2, sprite.width // 6), y + sprite.height, 4)


def compose(include_character: bool = True,
            env: Path | None = None, mg: Path | None = None) -> Image.Image:
    env = Path(env) if env else environment_dir("ship")
    mg = Path(mg) if mg else mega_dir("ship")
    tiles, _ = _load_tiles(env)
    scene = Image.new("RGBA", (W * TILE_SIZE, H * TILE_SIZE), (0, 0, 0, 255))

    # --- background wall ---------------------------------------------------
    vent_spots = {(7, 6), (30, 9), (41, 5), (18, 12)}
    for y in range(2, FLOOR_ROW):
        for x in range(W):
            tile = tiles["wall_flat"]
            if x % 5 == 2:
                tile = tiles["wall_flat_light"]
            elif x % 9 == 7:
                tile = tiles["wall_flat_violet"]
            if (x, y) in vent_spots:
                tile = tiles["vent"]
            if x in (12, 28) and y == 6:
                tile = tiles["window"]
            # occasional detailed panel clusters behind the hero props
            if 22 <= x <= 26 and 8 <= y <= 10:
                tile = tiles["wall"]
            if 31 <= x <= 34 and 7 <= y <= 9:
                tile = tiles["wall"]
            scene.paste(tile, (x * TILE_SIZE, y * TILE_SIZE))

    # --- ceiling and cable runs -------------------------------------------
    for y in range(2):
        for x in range(W):
            scene.paste(tiles["ceiling"], (x * TILE_SIZE, y * TILE_SIZE))
    for x in range(W):
        scene.paste(tiles["pipe_h"], (x * TILE_SIZE, 2 * TILE_SIZE))
    for x in range(0, W, 16):
        for y in range(4, FLOOR_ROW - 2):
            scene.paste(tiles["pipe_v"], (x * TILE_SIZE, y * TILE_SIZE))
    # lower-wall pipe runs break up the long horizontal band
    for x0, x1 in ((0, 10), (14, 20), (29, 38), (44, 48)):
        for x in range(x0, x1):
            scene.paste(tiles["pipe_h"], (x * TILE_SIZE, (FLOOR_ROW - 2) * TILE_SIZE))

    # --- structural hull ribs (two stacked modules per rib) ----------------
    hull = Image.open(mg / "elements" / "hull_frame" / "sprite.png").convert("RGBA")
    for rib_i, x in enumerate((0, 10, 22, 34, 46)):
        top = hull
        bottom = hull.transpose(Image.FLIP_LEFT_RIGHT) if rib_i % 2 else hull
        scene.alpha_composite(top, (x * TILE_SIZE, 3 * TILE_SIZE))
        scene.alpha_composite(bottom, (x * TILE_SIZE, 11 * TILE_SIZE))
        # cover the module seam with a horizontal pipe / hazard band
        for xx in range(x, min(W, x + 4)):
            scene.paste(tiles["pipe_h"], (xx * TILE_SIZE, 11 * TILE_SIZE))

    # --- viewport and reactor (large mega elements) ------------------------
    viewport = Image.open(mg / "elements" / "viewport" / "sprite.png").convert("RGBA")
    reactor = Image.open(mg / "elements" / "reactor_core" / "sprite.png").convert("RGBA")
    scene.alpha_composite(viewport, (16 * TILE_SIZE, 4 * TILE_SIZE))
    scene.alpha_composite(reactor, (40 * TILE_SIZE, FLOOR_ROW * TILE_SIZE - reactor.height))

    # --- deck / floor ------------------------------------------------------
    grate_cols = set(range(8, 10)) | set(range(38, 40))
    for x in range(W):
        top = tiles["grate_top"] if x in grate_cols else tiles["deck_top"]
        scene.paste(top, (x * TILE_SIZE, FLOOR_ROW * TILE_SIZE))
        for row in range(FLOOR_ROW + 1, H):
            scene.paste(tiles["deck_fill"], (x * TILE_SIZE, row * TILE_SIZE))
    # hazard bands at the two service bays
    for x in list(range(3, 8)) + list(range(23, 28)) + list(range(42, 47)):
        scene.paste(tiles["hazard"], (x * TILE_SIZE, (FLOOR_ROW + 1) * TILE_SIZE))
    for x in list(range(23, 28)) + list(range(40, 44)):
        scene.paste(tiles["hazard"], (x * TILE_SIZE, (FLOOR_ROW - 1) * TILE_SIZE))

    # --- medium props ------------------------------------------------------
    props = env / "props"
    cargo = Image.open(props / "cargo_stack" / "sprite.png").convert("RGBA")
    console = Image.open(props / "console_bank" / "sprite.png").convert("RGBA")
    server = Image.open(props / "server_rack" / "sprite.png").convert("RGBA")
    _paste_grounded(scene, cargo, 4 * TILE_SIZE, FLOOR_ROW * TILE_SIZE - cargo.height)
    _paste_grounded(scene, console, 23 * TILE_SIZE, FLOOR_ROW * TILE_SIZE - console.height)
    _paste_grounded(scene, server, 32 * TILE_SIZE, FLOOR_ROW * TILE_SIZE - server.height)
    # one varied repeat (flipped) far right, so the 3 pilot props do not read
    # as three lonely islands in a 48-tile room
    cargo_flip = cargo.transpose(Image.FLIP_LEFT_RIGHT)
    _paste_grounded(scene, cargo_flip, 45 * TILE_SIZE, FLOOR_ROW * TILE_SIZE - cargo.height)

    # --- character poses ---------------------------------------------------
    if include_character:
        ch = Path(__file__).resolve().parent.parent / "output" / "character" / "agent"
        idle_p, shoot_p = ch / "idle" / "frames" / "frame_00.png", ch / "shoot2" / "frames" / "frame_02.png"
        if idle_p.exists() and shoot_p.exists():
            idle = Image.open(idle_p).convert("RGBA")
            shoot = Image.open(shoot_p).convert("RGBA")
            _paste_grounded(scene, idle, 29 * TILE_SIZE, FLOOR_ROW * TILE_SIZE - idle.height)
            shoot_l = shoot.transpose(Image.FLIP_LEFT_RIGHT)
            _paste_grounded(scene, shoot_l, 24 * TILE_SIZE, FLOOR_ROW * TILE_SIZE - shoot_l.height)

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
    layout = {
        "scene": {"width_tiles": W, "height_tiles": H, "tile_size": TILE_SIZE,
                  "floor_row": FLOOR_ROW},
        "mega_elements": [
            {"id": "hull_frame", "count": 10, "placement": "stacked ribs at x=0,10,22,34,46"},
            {"id": "viewport", "count": 1, "placement": "x=16,y=4"},
            {"id": "reactor_core", "count": 1, "placement": "x=40,floor"},
        ],
        "medium_structures": [
            {"id": "cargo_stack", "count": 2, "placement": "x=4 and x=45 (flipped)"},
            {"id": "console_bank", "count": 1, "placement": "x=23"},
            {"id": "server_rack", "count": 1, "placement": "x=32"},
        ],
        "character": ["idle frame 00 (right)", "shoot2 frame 02 (left, flipped)"],
        "palette_violations": list(palette_violations(scene)),
    }
    (mg / "ship_layout.json").write_text(json.dumps(layout, indent=2))
    print("mega", mega.size, "scene", scene.size, "purity", palette_violations(scene))
    print("->", mg / "ship_mega_preview.png")
    print("->", out / "scene.png")


if __name__ == "__main__":
    main()
