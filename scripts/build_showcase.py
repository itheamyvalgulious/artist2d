"""Compose a playable-looking showcase scene from the generated asset packs.

The scene exercises every module at once:
  * grass/dirt/water seamless tiles with 47-tile autotile transitions,
  * the medium grounded stamp (shrine) with its Y-sort base,
  * the 20x15 mega-structure assembly,
  * idle / attack character frames.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from config.pipeline_config import OUTPUT_DIR, TILE_SIZE  # noqa: E402
from config.namespaces import environment_dir, mega_dir, showcase_dir  # noqa: E402
from core.palette_quantizer import lock_palette  # noqa: E402
from environment.autotile_47 import autotile_index_for_neighbors  # noqa: E402
from scipy import ndimage  # noqa: E402

ENV = environment_dir("field")
W, H = 56, 38
BIG = 2  # preview scale


def load_tile(name: str) -> Image.Image:
    img = Image.open(ENV / f"{name}_seamless.png").convert("RGBA")
    assert img.size == (TILE_SIZE, TILE_SIZE)
    return img


def autotile_tile(atlas: Image.Image, state_map: dict, cm: int, dm: int) -> Image.Image:
    idx = state_map.get(f"{cm}:{dm}", 0)
    cols = 8
    x = (idx % cols) * TILE_SIZE
    y = (idx // cols) * TILE_SIZE
    return atlas.crop((x, y, x + TILE_SIZE, y + TILE_SIZE))


def grass_mask() -> np.ndarray:
    m = np.ones((H, W), dtype=bool)
    # dirt clearing (bottom-left)
    m[15:23, 3:17] = False
    # water pond (top-left)
    m[3:10, 4:12] = False
    # service road in front of the castle
    m[20:23, 17:38] = False
    return m


def key_border_dark(img: Image.Image, tol: int = 40) -> Image.Image:
    """Make the border-connected near-black canvas transparent (keeps inner outlines)."""
    import cv2
    a = np.array(img.convert("RGBA"))
    h, w = a.shape[:2]
    dark = (a[..., :3].astype(int).max(-1) < tol) & (a[..., 3] > 0)
    mask = np.zeros((h + 2, w + 2), np.uint8)
    ff = dark.astype(np.uint8).copy()
    for seed in [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)]:
        if ff[seed[1], seed[0]]:
            cv2.floodFill(ff, mask, seed, 2)
    a[(ff == 2)] = 0
    return Image.fromarray(a, "RGBA")


def _paint(scene: Image.Image, atlas: Image.Image, state_map: dict,
           mask: np.ndarray, interior: Image.Image) -> None:
    h, w = mask.shape
    for y in range(h):
        for x in range(w):
            if not mask[y, x]:
                continue
            n = int(mask[y - 1, x]) if y > 0 else 0
            e = int(mask[y, x + 1]) if x < w - 1 else 0
            s_ = int(mask[y + 1, x]) if y < h - 1 else 0
            ww = int(mask[y, x - 1]) if x > 0 else 0
            ne = int(mask[y - 1, x + 1]) if y > 0 and x < w - 1 else n and e
            se = int(mask[y + 1, x + 1]) if y < h - 1 and x < w - 1 else s_ and e
            sw = int(mask[y + 1, x - 1]) if y < h - 1 and x > 0 else s_ and ww
            nw = int(mask[y - 1, x - 1]) if y > 0 and x > 0 else n and ww
            cm = n | (e << 1) | (s_ << 2) | (ww << 3)
            dm = ne | (se << 1) | (sw << 2) | (nw << 3)
            if cm == 15 and dm == 15:
                tile = interior
            else:
                idx = autotile_index_for_neighbors(bool(n), bool(e), bool(s_), bool(ww),
                                                   bool(ne), bool(se), bool(sw), bool(nw))
                x0 = (idx % 8) * TILE_SIZE
                y0 = (idx // 8) * TILE_SIZE
                tile = atlas.crop((x0, y0, x0 + TILE_SIZE, y0 + TILE_SIZE))
            scene.paste(tile, (x * TILE_SIZE, y * TILE_SIZE))


def _shadow(scene: Image.Image, box: tuple[int, int, int, int], height: int = 7,
            alpha: int = 90) -> None:
    """Soft contact shadow under a building footprint (1px rows, fading out)."""
    x0, y0, x1, y1 = box
    layer = Image.new("RGBA", scene.size, (0, 0, 0, 0))
    arr = np.array(layer)
    for i in range(height):
        a = int(alpha * (1.0 - i / max(1, height - 1)))
        y = min(scene.height - 1, y1 + i)
        arr[y, x0:x1, 3] = a
    scene.alpha_composite(Image.fromarray(arr, "RGBA"))


def gate_interior(w: int, h: int) -> Image.Image:
    """A wooden double gate with iron bands (deterministic, palette-only)."""
    im = Image.new("RGBA", (w, h), (8, 8, 12, 255))
    arr = np.array(im)
    plank_cols = [(46, 26, 16), (71, 40, 24), (56, 32, 20), (82, 48, 28)]
    for x in range(w):
        arr[:, x, :3] = plank_cols[(x // 16) % len(plank_cols)]
        if x % 16 == 0:
            arr[:, x, :3] = (26, 15, 10)
    # central door gap
    c = w // 2
    arr[:, c - 3:c + 3, :3] = (20, 12, 8)
    arr[:, c - 1:c + 1, :3] = (8, 8, 12)
    # iron bands + rivets
    for y in range(24, h - 10, 96):
        arr[y:y + 6, :, :3] = (54, 54, 70)
        arr[y, :, :3] = (78, 78, 99)
        arr[y + 5, :, :3] = (35, 35, 46)
        for x in range(10, w - 8, 32):
            arr[y + 2, x:x + 2, :3] = (214, 214, 230)
    # side frame + lintel shadow
    arr[:, :6, :3] = (35, 35, 46)
    arr[:, -6:, :3] = (35, 35, 46)
    arr[:8, :, :3] = (8, 8, 12)
    return Image.fromarray(arr, "RGBA")


def compose() -> Image.Image:
    grass = load_tile("grass")
    dirt = load_tile("dirt")
    water = load_tile("water")

    def load_atlas(name):
        atlas = Image.open(ENV / f"autotile_{name}.png").convert("RGBA")
        meta = json.loads((ENV / f"autotile_{name}.json").read_text())
        return atlas, meta["map"]

    dirt_atlas, dirt_map = load_atlas("dirt_over_grass")
    water_atlas, water_map = load_atlas("water_over_dirt")

    yy, xx = np.mgrid[0:H, 0:W]
    road = np.abs(yy - (34.0 + 0.8 * np.sin(xx / 5.0))) < 1.5
    clearing = (((xx - 5.0) / 4.5) ** 2 + ((yy - 31.0) / 4.0) ** 2) < 1.0
    path = (np.abs(xx - 5.0) < 1.2) & (yy >= 33.0) & (yy <= 35.0)
    dirt_mask = road | clearing | path
    pond = (((xx - 4.0) / 3.5) ** 2 + ((yy - 6.0) / 2.5) ** 2) < 1.0
    bank = ndimage.binary_dilation(pond, iterations=2) & ~pond

    scene = Image.new("RGBA", (W * TILE_SIZE, H * TILE_SIZE), (0, 0, 0, 255))
    for y in range(H):
        for x in range(W):
            scene.paste(grass, (x * TILE_SIZE, y * TILE_SIZE))
    # dirt road and clearing (47-tile over grass)
    _paint(scene, dirt_atlas, dirt_map, dirt_mask, dirt)
    # pond bank is dirt, then water over the dirt (water-over-dirt 47-tile)
    _paint(scene, dirt_atlas, dirt_map, bank, dirt)
    pond_paint = ndimage.binary_dilation(pond, iterations=1) & (pond | bank)
    _paint(scene, water_atlas, water_map, pond_paint, water)

    # mega structure: 20x15 big tiles -> 640x480 at scene scale (32 px/tile)
    mega = Image.open(mega_dir("field") / "mega_canvas_1x.png").convert("RGBA")
    ma = np.array(mega)
    yellow = (ma[..., 0] > 200) & (ma[..., 1] > 200) & (ma[..., 2] < 80)
    ma[yellow] = 0
    # The generated gate opening has a 65 px stone sill; cut it so the wooden
    # gate reaches the ground instead of reading as a floating window.
    ma[895:960, 448:768, 3] = 0
    mega = Image.fromarray(ma, "RGBA")
    mx, my = 8 * TILE_SIZE, 4 * TILE_SIZE
    # Fill the mega's internal openings with one deterministic wooden gate,
    # using the generated alpha holes themselves (the gate is wider at the
    # bottom and has a narrow top gap).  This guarantees no grass shows
    # through and no fixed rectangle / placeholder jamb is needed.
    gate = gate_interior(mega.width, mega.height)
    gm = np.zeros((mega.height, mega.width), np.uint8)
    opaque = np.array(mega)[..., 3] > 0
    for y in range(300, mega.height):
        x = 0
        while x < mega.width:
            if not opaque[y, x]:
                s0 = x
                while x < mega.width and not opaque[y, x]:
                    x += 1
                if s0 > 0 and x < mega.width and (x - s0) > 32:
                    gm[y, s0:x] = 255
            else:
                x += 1
    gate.putalpha(Image.fromarray(gm))
    scene.alpha_composite(gate, (mx, my))
    scene.alpha_composite(mega, (mx, my))

    # medium stamp (4x5 tiles) in the dirt clearing, seated on the dirt
    stamp = Image.open(ENV / "stamp" / "stamp_matted.png").convert("RGBA")
    stamp = key_border_dark(stamp)
    sx, sy = 3 * TILE_SIZE, 28 * TILE_SIZE
    _shadow(scene, (sx + 10, sy + stamp.height - 6, sx + stamp.width - 10,
                    sy + stamp.height), height=5, alpha=90)
    scene.alpha_composite(stamp, (sx, sy))

    # characters on the road in front of the gate (feet at the road bottom)
    idle = Image.open(OUTPUT_DIR / "character" / "knight" / "idle" / "frames" / "frame_00.png").convert("RGBA")
    attack = Image.open(OUTPUT_DIR / "character" / "knight" / "attack" / "frames" / "frame_06.png").convert("RGBA")
    scene.alpha_composite(idle, (25 * TILE_SIZE, 32 * TILE_SIZE))
    scene.alpha_composite(attack, (27 * TILE_SIZE, 32 * TILE_SIZE))

    # The contact shadows are alpha-composited; snap the finished opaque scene
    # back onto the master palette so every shipped pixel stays palette-pure.
    return lock_palette(scene)


def main() -> None:
    out = showcase_dir("field")
    out.mkdir(parents=True, exist_ok=True)
    scene = compose()
    scene.save(out / "scene_1x.png")
    scene.resize((scene.width * BIG, scene.height * BIG), Image.NEAREST).save(out / "scene.png")
    print("showcase", scene.size, "->", out / "scene.png")


if __name__ == "__main__":
    main()
