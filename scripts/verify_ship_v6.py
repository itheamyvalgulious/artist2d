"""Deterministic verification for the v6 ship pack (no AI, no network).

Prints the measurements quoted in output/reviews/ship_fix_v6.md.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from core.palette_quantizer import (  # noqa: E402
    PALETTE_RGB, nearest_palette_indices, palette_violations,
)

ENV = ROOT / "output/environment/ship"
MEGA = ROOT / "output/mega/ship"
SHOW = ROOT / "output/showcase/ship"


def lum(rgb: np.ndarray) -> np.ndarray:
    return rgb.astype(np.float64) @ np.array([0.2126, 0.7152, 0.0722])


def lr_balance(img: Image.Image, band: int = 8) -> float:
    a = np.array(img.convert("RGBA"))
    al = a[..., 3]
    L = lum(a[..., :3])
    left, right = [], []
    for x in range(band):
        m = al[:, x] == 255
        if m.any():
            left.append(L[m, x].mean())
        m = al[:, img.width - 1 - x] == 255
        if m.any():
            right.append(L[m, img.width - 1 - x].mean())
    return float(np.mean(left) - np.mean(right))


def main() -> None:
    print("== determinism ==")
    files = [ENV / "tileset.json", ENV / "tileset.png", ENV / "tileset_sample.png",
             MEGA / "ship_mega_1x.png", SHOW / "scene_1x.png", SHOW / "scene_focus_x4.png"]
    h1 = {f.name: hashlib.sha256(f.read_bytes()).hexdigest()[:16] for f in files}
    import subprocess
    r = subprocess.run([sys.executable, str(ROOT / "scripts/build_ship.py")],
                       cwd=ROOT, capture_output=True, text=True)
    h2 = {f.name: hashlib.sha256(f.read_bytes()).hexdigest()[:16] for f in files}
    print("rebuild rc:", r.returncode, "identical:", h1 == h2)
    for k in h1:
        print(f"  {k:24s} {h1[k]} {'same' if h1[k]==h2[k] else 'CHANGED'}")

    print("\n== inventory ==")
    meta = json.loads((ENV / "tileset.json").read_text())
    names = sorted(meta["tiles"])
    print("tiles in tileset.json:", len(names))
    on_disk = sorted(p.stem for p in (ENV / "tiles").glob("*.png")
                     if not p.stem.endswith("_x8") and not p.stem.endswith("_seamless")
                     and not p.stem.endswith("_checkerboard")
                     and p.stem not in ("deck_x8", "grate_x8", "wall_x8", "conduit_x8"))
    print("base tile pngs on disk:", len(on_disk), "== atlas:", on_disk == names)
    props = sorted(p.name for p in (ENV / "props").glob("*/sprite.png"))
    megas = sorted(p.name for p in (MEGA / "elements").glob("*/sprite.png"))
    print("medium sprites:", len(props), "mega sprites:", len(megas))
    print("isolation dirs:", ENV.exists(), MEGA.exists(), SHOW.exists())

    print("\n== palette / alpha ==")
    for p in [ENV / "tileset.png", ENV / "tileset_sample.png", MEGA / "ship_mega_1x.png",
              SHOW / "scene_1x.png", SHOW / "scene_focus_x4.png"]:
        print(f"  {p.relative_to(ROOT)} violations {palette_violations(Image.open(p))}")
    for p in sorted((ENV / "props").glob("*/sprite.png")) + sorted((MEGA / "elements").glob("*/sprite.png")):
        im = Image.open(p).convert("RGBA")
        a = np.array(im)[..., 3]
        print(f"  {p.parent.name:14s} {im.size} violations {palette_violations(im)} alpha {sorted(set(np.unique(a).tolist()))}")

    print("\n== seams (mean |col0-col31| / |row0-row31|) ==")
    groups = {"repeat fill": ["ceiling", "deck_fill", "grate_fill", "grate_top", "pipe_h",
                              "pipe_v", "wall", "wall_flat", "wall_flat_light",
                              "wall_flat_violet", "wall_light", "wall_violet"],
              "repeat X only": ["deck_top", "deck_step"],
              "one-off caps/features": ["deck_left", "deck_right", "deck_top_right",
                                        "deck_step_left", "deck_step_right", "door",
                                        "door_top", "hazard", "vent", "window", "light_strip"]}
    for g, ns in groups.items():
        print(f"  [{g}]")
        for n in ns:
            a = np.array(Image.open(ENV / "tiles" / f"{n}.png").convert("RGBA"))[..., :3].astype(int)
            print(f"    {n:20s} seamX {np.abs(a[:,0]-a[:,-1]).mean():6.2f} "
                  f"seamY {np.abs(a[0,:]-a[-1,:]).mean():6.2f}")

    print("\n== hazard analytic tiling ==")
    h = np.array(Image.open(ENV / "tiles/hazard.png").convert("RGBA"))
    for reps in (2, 4):
        big = np.zeros((32 * reps, 32 * reps, 4), np.uint8)
        for y in range(reps):
            for x in range(reps):
                big[y*32:(y+1)*32, x*32:(x+1)*32] = h
        yy, xx = np.mgrid[0:32*reps, 0:32*reps]
        ref = np.zeros_like(big)
        ref[..., 3] = 255
        ref[..., :3] = np.where((((xx+yy) % 8) < 4)[..., None],
                                PALETTE_RGB[50], PALETTE_RGB[1])
        ref[((xx+yy) % 8) == 0, :3] = PALETTE_RGB[51]
        print(f"  {reps}x{reps} repeat == analytic 45deg: {np.array_equal(big, ref)}")
    row = h[20, :, :3]
    print("  row20 shifted == row21 (1:1 diagonal):",
          np.array_equal(row[1:], h[21, :-1, :3]))

    print("\n== decks / shadows ==")
    mega = Image.open(MEGA / "ship_mega_1x.png").convert("RGBA")
    scene = Image.open(SHOW / "scene_1x.png").convert("RGBA")
    for img, tag, objs in (
        (mega, "mega", [("cargo#1", 154, 215, 512), ("cargo#2", 234, 295, 512),
                        ("console", 532, 629, 480), ("server", 870, 926, 512),
                        ("reactor", 1249, 1375, 480)]),
        (scene, "scene", [("agent", 950, 990, 512), ("reactor", 1249, 1375, 480)]),
    ):
        a = np.array(img)
        L = lum(a[..., :3])
        print(f"  [{tag}]")
        for name, x0, x1, base in objs:
            rows = [int((L[base + 1 + i, x0:x1] < 18).sum()) for i in range(4)]
            print(f"    {name:9s} rows {base+1}-{base+4}: {rows} of {x1-x0}")
        i512 = nearest_palette_indices(a[512, :, :3])
        print(f"    row 512 lip (palette 6): {int((i512==6).sum())}/{len(i512)}")

    print("\n== sprite lighting (left 8 - right 8 mean luminance) ==")
    for p in sorted((ENV / "props").glob("*/sprite.png")) + sorted((MEGA / "elements").glob("*/sprite.png")):
        print(f"  {p.parent.name:14s} {lr_balance(Image.open(p)):+.2f}")

    print("\n== tile / sprite metrics quoted in the report ==")
    for n in ("deck_fill", "wall_flat", "deck_top", "hazard", "window"):
        a = np.array(Image.open(ENV / "tiles" / f"{n}.png").convert("RGBA"))[..., :3].astype(int)
        print(f"  {n:12s} colours {len(np.unique(a.reshape(-1,3),axis=0)):2d} "
              f"adjcol {np.abs(np.diff(a,axis=1)).mean():5.2f} "
              f"L {lum(a).mean():5.1f}")
    w = np.array(Image.open(ENV / "tiles/window.png").convert("RGBA"))[..., :3].astype(float)
    glass = lum(w[5:27, 5:27])
    print(f"  window glass L mean {glass.mean():.1f} max {glass.max():.1f}")
    door = np.array(Image.open(ENV / "tiles/door.png").convert("RGBA"))[..., :3]
    print("  door jambs  col0/1/2:", door[10, 0].tolist(), door[10, 1].tolist(), door[10, 2].tolist(),
          " col29/30/31:", door[10, 29].tolist(), door[10, 30].tolist(), door[10, 31].tolist())
    print("  wall base colour:", np.array(Image.open(ENV / "tiles/wall_flat.png").convert("RGBA"))[10, 10, :3].tolist())
    for p in sorted((ENV / "props").glob("*/sprite.png")) + sorted((MEGA / "elements").glob("*/sprite.png")):
        im = Image.open(p).convert("RGBA")
        a = np.array(im)
        op = a[..., 3] == 255
        print(f"  {p.parent.name:14s} {im.size} colours {len(np.unique(a[...,:3][op].reshape(-1,3),axis=0))}")

    print("\n== reactor plinth ==")
    a = np.array(mega)
    reg = a[461:480, 1237:1355]
    print("  reactor rows 461-479 opaque:", int((reg[..., 3] == 255).sum()),
          "colours:", len(np.unique(reg[..., :3].reshape(-1, 3), axis=0)))
    pad = a[480, 1218:1406, :3]
    print("  hazard pad row 480 colours:", len(np.unique(pad.reshape(-1, 3), axis=0)))


if __name__ == "__main__":
    main()
