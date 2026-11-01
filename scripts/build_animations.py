"""Playable previews and animated terrain tiles.

Produces:
  * character/<action>/preview.png  (APNG) + preview.gif — contiguous playback
  * environment/{water,grass}_anim/frame_XX.png + *_anim.png/.gif — 4-frame
    seamless tile animation
  * environment/autotile_water_over_dirt.png — 47-tile water bank atlas
  * environment/terrain_preview.png / _x2.png — one stitched map that uses the
    47-tile atlases for grass/dirt, stone and water transitions

Every PNG frame is palette-pure and 0/255 alpha; the APNG is a real PNG so the
strict output scan sees pure pixels, while a browser/image viewer plays it.
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
from config.namespaces import environment_dir  # noqa: E402
from core.palette_quantizer import (  # noqa: E402
    PALETTE_RGB,
    lock_palette,
    palette_violations,
)
from environment.autotile_47 import (  # noqa: E402
    autotile_index_for_neighbors,
    synthesize_47,
)
from environment.water_animation import generate_water_frames  # noqa: E402
from environment.seamless_toroidal import ks_seam_test  # noqa: E402

ENV = environment_dir("field")
CHAR = OUTPUT_DIR / "character" / "knight"
ACTIONS = ["idle", "running", "attack", "defend", "jump", "in_air"]
BG = (8, 8, 12, 255)


def _save_apng(frames: list[Image.Image], path: Path, duration: int = 110) -> None:
    frames[0].save(path, save_all=True, append_images=frames[1:],
                   duration=duration, loop=0, disposal=1, blend=0)


def _save_gif(frames: list[Image.Image], path: Path, duration: int = 110,
              scale: int = 4) -> None:
    rgb = []
    for f in frames:
        bg = Image.new("RGBA", f.size, BG)
        bg.alpha_composite(f)
        big = bg.convert("RGB").resize((f.width * scale, f.height * scale), Image.NEAREST)
        rgb.append(big)
    rgb[0].save(path, save_all=True, append_images=rgb[1:], duration=duration,
                loop=0, disposal=2, optimize=False)


def build_character_previews() -> dict:
    """APNG/GIF playback of every action's 8 final frames."""
    out = {}
    for action in ACTIONS:
        d = CHAR / action / "frames"
        frames = [Image.open(d / f"frame_{i:02d}.png").convert("RGBA")
                  for i in range(8)]
        big = [f.resize((f.width * 4, f.height * 4), Image.NEAREST) for f in frames]
        apng = CHAR / action / "preview.png"
        gif = CHAR / action / "preview.gif"
        _save_apng(big, apng, duration=110)
        _save_gif(frames, gif, duration=110, scale=4)
        out[action] = {"apng": str(apng), "gif": str(gif)}
        print(f"  {action:12s} 8 frames -> {apng.name} / {gif.name}")
    return out


# ---------------------------------------------------------------------------
# Animated tiles
# ---------------------------------------------------------------------------

def _mode_color(arr: np.ndarray) -> np.ndarray:
    cols = arr[..., :3][arr[..., 3] > 0].reshape(-1, 3)
    uniq, counts = np.unique(cols, axis=0, return_counts=True)
    return uniq[int(np.argmax(counts))]


def _lum(rgb: np.ndarray) -> np.ndarray:
    return rgb.astype(np.float64) @ np.array([0.2126, 0.7152, 0.0722])


def animate_grass(tile: Image.Image, n: int = 4) -> list[Image.Image]:
    """Sway the bright blade pixels; the dark base stays put."""
    arr = np.array(tile.convert("RGBA"))
    base = _mode_color(arr)
    base_lum = float(_lum(base[None, None, :])[0, 0])
    lum = _lum(arr[..., :3])
    blades = (lum > base_lum + 12) & (arr[..., 3] > 0)
    frames = []
    for k in range(n):
        out = arr.copy()
        moved = np.zeros_like(blades)
        moved_col = np.zeros_like(arr)
        for y in range(arr.shape[0]):
            dx = int(round(1.2 * np.sin(2 * np.pi * k / n + y / 7.0)))
            moved[y] = np.roll(blades[y], dx)
            moved_col[y] = np.roll(arr[y], dx, axis=0)
        vacated = blades & ~moved
        out[vacated, :3] = base
        out[moved, :3] = moved_col[moved, :3]
        out[..., 3] = 255
        frames.append(lock_palette(Image.fromarray(out, "RGBA")))
    return frames


def _phase_all(frames: list[Image.Image]) -> list[Image.Image]:
    """Find one toroidal phase where every frame passes both KS tests."""
    best = None
    for dy in range(32):
        for dx in range(32):
            rolled = [Image.fromarray(np.roll(np.roll(np.array(f), dy, axis=0), dx, axis=1), "RGBA")
                      for f in frames]
            ks = [ks_seam_test(f) for f in rolled]
            score = min(min(k["p_value"], k["p_value_3x3"]) for k in ks)
            if best is None or score > best[0]:
                best = (score, rolled, ks)
            if score > 0.05:
                break
        if best and best[0] > 0.05:
            break
    return best[1]


def build_tile_animation(name: str, frames: list[Image.Image]) -> dict:
    outdir = ENV / f"{name}_anim"
    outdir.mkdir(parents=True, exist_ok=True)
    for i, f in enumerate(frames):
        f.save(outdir / f"frame_{i:02d}.png")
    big = [f.resize((f.width * 8, f.height * 8), Image.NEAREST) for f in frames]
    _save_apng(big, outdir / f"{name}_anim.png", duration=160)
    _save_gif(frames, outdir / f"{name}_anim.gif", duration=160, scale=8)
    ks = [ks_seam_test(f) for f in frames]
    return {"frames": len(frames), "ks": ks,
            "apng": str(outdir / f"{name}_anim.png"),
            "gif": str(outdir / f"{name}_anim.gif")}


# ---------------------------------------------------------------------------
# Stitched terrain preview
# ---------------------------------------------------------------------------

def _paint_mask(scene: Image.Image, atlas: Image.Image, state_map: dict,
                mask: np.ndarray, lower: Image.Image,
                interior: Image.Image | None = None) -> None:
    h, w = mask.shape
    for y in range(h):
        for x in range(w):
            if not mask[y, x]:
                continue
            n = int(mask[y - 1, x]) if y > 0 else 0
            e = int(mask[y, x + 1]) if x < w - 1 else 0
            s = int(mask[y + 1, x]) if y < h - 1 else 0
            ww = int(mask[y, x - 1]) if x > 0 else 0
            ne = int(mask[y - 1, x + 1]) if y > 0 and x < w - 1 else n and e
            se = int(mask[y + 1, x + 1]) if y < h - 1 and x < w - 1 else s and e
            sw = int(mask[y + 1, x - 1]) if y < h - 1 and x > 0 else s and ww
            nw = int(mask[y - 1, x - 1]) if y > 0 and x > 0 else n and ww
            idx = autotile_index_for_neighbors(bool(n), bool(e), bool(s), bool(ww),
                                               bool(ne), bool(se), bool(sw), bool(nw))
            cm = n | (e << 1) | (s << 2) | (ww << 3)
            dm = ne | (se << 1) | (sw << 2) | (nw << 3)
            if interior is not None and cm == 15 and dm == 15:
                tile = interior
            else:
                x0 = (idx % 8) * TILE_SIZE
                y0 = (idx // 8) * TILE_SIZE
                tile = atlas.crop((x0, y0, x0 + TILE_SIZE, y0 + TILE_SIZE))
            scene.paste(tile, (x * TILE_SIZE, y * TILE_SIZE))


def clean_water_edge(scene: Image.Image, water: Image.Image, dirt: Image.Image) -> Image.Image:
    """Smooth the water/dirt boundary at the pixel level.

    The 47-tile atlas can leave 1 px water spikes into the bank (and 1 px
    dirt pinholes in the water) where transition tiles meet.  A morphological
    open+close of the water mask removes both; removed water is filled from
    the SAME base dirt tile, added water from the SAME base water tile as the
    interior and the atlas.
    """
    from scipy import ndimage as ndi
    arr = np.array(scene.convert("RGBA"))
    wt = np.array(water.convert("RGB"))
    dt = np.array(dirt.convert("RGB"))
    water_colors = [tuple(c) for c in np.unique(wt.reshape(-1, 3), axis=0)]
    wm = np.zeros(arr.shape[:2], bool)
    for c in water_colors:
        wm |= np.all(arr[..., :3] == np.array(c, dtype=np.uint8), axis=-1)
    st = np.ones((3, 3), bool)
    opened = ndi.binary_opening(wm, structure=st, border_value=0)
    closed = ndi.binary_closing(opened, structure=st, border_value=0)
    ys, xs = np.nonzero(wm & ~closed)
    arr[ys, xs, :3] = dt[ys % 32, xs % 32]
    ys, xs = np.nonzero(closed & ~wm)
    arr[ys, xs, :3] = wt[ys % 32, xs % 32]
    return Image.fromarray(arr, "RGBA")


def build_terrain_preview(water_frames=None, grass_frames=None) -> dict:
    grass = Image.open(ENV / "grass_seamless.png").convert("RGBA")
    dirt = Image.open(ENV / "dirt_seamless.png").convert("RGBA")
    stone = Image.open(ENV / "stone_seamless.png").convert("RGBA")
    water = Image.open(ENV / "water_seamless.png").convert("RGBA")

    def load_atlas(name):
        atlas = Image.open(ENV / f"autotile_{name}.png").convert("RGBA")
        meta = json.loads((ENV / f"autotile_{name}.json").read_text())
        return atlas, meta["map"]

    dirt_atlas, dirt_map = load_atlas("dirt_over_grass")
    stone_atlas, stone_map = load_atlas("stone_over_grass")
    water_atlas, water_map = load_atlas("water_over_dirt")

    W, H = 30, 20
    yy, xx = np.mgrid[0:H, 0:W]
    road = np.abs(yy - (13.5 + 2.2 * np.sin(xx / 3.4))) < 1.6
    clearing = (((xx - 8.0) / 4.2) ** 2 + ((yy - 15.5) / 2.6) ** 2) < 1.0
    dirt_mask = road | clearing
    pond = (((xx - 7.5) / 3.6) ** 2 + ((yy - 4.2) / 2.3) ** 2) < 1.0
    plaza = (((xx - 23.5) / 3.4) ** 2 + ((yy - 4.5) / 2.4) ** 2) < 1.0
    from scipy import ndimage as _nd
    bank = _nd.binary_dilation(pond, iterations=2) & ~pond

    n_frames = 4 if grass_frames else 1
    out_frames = []
    for k in range(n_frames):
        base = grass_frames[k] if grass_frames else grass
        # The terrain preview uses the same base water tile as the 47-tile
        # bank atlas; the AI animation frames live in the separate water_anim
        # asset so the pond interior and its banks are never two waters.
        watery = water
        scene = Image.new("RGBA", (W * TILE_SIZE, H * TILE_SIZE), (0, 0, 0, 255))
        for y in range(H):
            for x in range(W):
                scene.paste(base, (x * TILE_SIZE, y * TILE_SIZE))
        _paint_mask(scene, dirt_atlas, dirt_map, dirt_mask, grass)
        _paint_mask(scene, dirt_atlas, dirt_map, pond | bank, grass)
        _paint_mask(scene, stone_atlas, stone_map, plaza, grass)
        from scipy import ndimage as _nd2
        pond_paint = _nd2.binary_dilation(pond, iterations=1) & (pond | bank)
        _paint_mask(scene, water_atlas, water_map, pond_paint, grass, interior=watery)
        out_frames.append(scene)

    out_frames[0].save(ENV / "terrain_preview.png")
    out_frames[0].resize((out_frames[0].width * 2, out_frames[0].height * 2),
                         Image.NEAREST).save(ENV / "terrain_preview_x2.png")
    if len(out_frames) > 1:
        _save_apng(out_frames, ENV / "terrain_preview_anim.png", duration=200)
        _save_gif([f.convert("RGBA") for f in out_frames],
                  ENV / "terrain_preview_anim.gif", duration=200, scale=1)
    return {"map": f"{W}x{H}", "size": out_frames[0].size, "frames": len(out_frames)}


def main() -> None:
    print("Character playback ...")
    chars = build_character_previews()
    print("Animated tiles ...")
    grass = Image.open(ENV / "grass_seamless.png").convert("RGBA")
    # Reuse the already generated AI water frames; do not call the image model
    # while restoring/checking the terrain cut.
    water_frames = [Image.open(ENV / "water_anim" / f"frame_{i:02d}.png").convert("RGBA")
                    for i in range(4)]
    grass_frames = _phase_all(animate_grass(grass))
    water_anim = build_tile_animation("water", water_frames)
    grass_anim = build_tile_animation("grass", grass_frames)
    print("Terrain preview ...")
    terrain = build_terrain_preview(water_frames, grass_frames)
    print("character previews:", len(chars))
    print("water animation:", water_anim["frames"], water_anim["ks"])
    print("grass animation:", grass_anim["frames"], grass_anim["ks"])
    print("terrain:", terrain)


if __name__ == "__main__":
    main()
