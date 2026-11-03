"""Deterministic verification for the v7 ship pack (no AI, no network).

Every measurement quoted in output/reviews/ship_fix_v7.md comes from here.
"""
from __future__ import annotations

import collections
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import environment.ship_assembly as A  # noqa: E402
from core.palette_quantizer import (  # noqa: E402
    PALETTE_RGB, nearest_palette_indices, palette_violations,
)

ENV = ROOT / "output/environment/ship"
MEGA = ROOT / "output/mega/ship"
SHOW = ROOT / "output/showcase/ship"


def lum(rgb: np.ndarray) -> np.ndarray:
    return rgb.astype(np.float64) @ np.array([0.2126, 0.7152, 0.0722])


def compose_without_shadows(include_character: bool) -> Image.Image:
    orig = A._shadow
    A._shadow = lambda *a, **k: None
    try:
        img = A.compose(include_character=include_character, env=ENV, mg=MEGA)
    finally:
        A._shadow = orig
    return img


def main() -> None:
    print("== determinism ==")
    files = [ENV / "tileset.json", ENV / "tileset.png", ENV / "tileset_sample.png",
             MEGA / "ship_mega_1x.png"]
    h1 = {f.name: hashlib.sha256(f.read_bytes()).hexdigest()[:16] for f in files}
    r = subprocess.run([sys.executable, str(ROOT / "scripts/build_ship.py")],
                       cwd=ROOT, capture_output=True, text=True)
    h2 = {f.name: hashlib.sha256(f.read_bytes()).hexdigest()[:16] for f in files}
    print("rebuild rc:", r.returncode, "ship layer identical:", h1 == h2)

    frame = ROOT / "output/character/agent/idle/frames/frame_00.png"
    fh = hashlib.sha256(frame.read_bytes()).hexdigest()[:16]
    shipped = np.array(Image.open(SHOW / "scene_1x.png").convert("RGBA"))[..., :3].astype(int)
    fresh = np.array(A.compose(include_character=True, env=ENV, mg=MEGA))[..., :3].astype(int)
    diff = int((shipped != fresh).any(axis=2).sum())
    print(f"scene_1x == fresh compose(current frame {fh}): {diff} px differ")

    print("\n== inventory ==")
    meta = json.loads((ENV / "tileset.json").read_text())
    names = sorted(meta["tiles"])
    on_disk = sorted(p.stem for p in (ENV / "tiles").glob("*.png"))
    print("tileset keys:", len(names), "png in tiles/:", len(on_disk),
          "identical set:", on_disk == names)
    print("tiles dir contents not in atlas:", sorted(set(on_disk) - set(names)))
    print("medium sprites:", len(list((ENV / "props").glob("*/sprite.png"))),
          "mega sprites:", len(list((MEGA / "elements").glob("*/sprite.png"))))

    print("\n== palette / alpha ==")
    for p in [ENV / "tileset.png", ENV / "tileset_sample.png", MEGA / "ship_mega_1x.png",
              SHOW / "scene_1x.png", SHOW / "scene_focus_x4.png"]:
        print(f"  {p.relative_to(ROOT)} violations {palette_violations(Image.open(p))}")
    for p in sorted((ENV / "props").glob("*/sprite.png")) + sorted((MEGA / "elements").glob("*/sprite.png")):
        im = Image.open(p).convert("RGBA")
        a = np.array(im)[..., 3]
        print(f"  {p.parent.name:14s} {im.size} violations {palette_violations(im)} alpha {sorted(set(np.unique(a).tolist()))}")

    print("\n== contact shadows (shipped minus a no-shadow compose) ==")
    mega = Image.open(MEGA / "ship_mega_1x.png").convert("RGBA")
    no_mega = compose_without_shadows(False)
    a = np.array(mega)[..., :3].astype(int)
    b = np.array(no_mega)[..., :3].astype(int)
    d = (a != b).any(axis=2)
    print("  shadow pixels:", int(d.sum()), "bounds",
          tuple(int(v) for v in (np.nonzero(d)[1].min(), np.nonzero(d)[0].min(),
                                 np.nonzero(d)[1].max(), np.nonzero(d)[0].max())))
    objs = [("cargo#1", 140, 205), ("cargo#2", 243, 307), ("console", 520, 632),
            ("server", 870, 926), ("reactor", 1253, 1370), ("pad", 1216, 1407)]
    for name, x0, x1 in objs:
        m = d[:, x0:x1]
        rows = collections.Counter(np.nonzero(m)[0].tolist())
        if not rows:
            print(f"  {name:9s} NO SHADOW")
            continue
        r0 = min(rows)
        seq = [rows.get(r, 0) for r in range(r0, r0 + 5)]
        print(f"  {name:9s} first row {r0}  dark/width {seq} of {x1 - x0}")
    sc = np.array(Image.open(SHOW / "scene_1x.png").convert("RGBA"))[..., :3].astype(int)
    no_sc = np.array(compose_without_shadows(True))[..., :3].astype(int)
    ds = (sc != no_sc).any(axis=2)
    rows = collections.Counter(np.nonzero(ds[:, 950:982])[0].tolist())
    print("  agent     first row", min(rows) if rows else "-", " dark/width",
          [rows.get(r, 0) for r in range(min(rows), min(rows) + 3)] if rows else [], "of 32")

    print("\n== lip / tread preservation (0 = untouched) ==")
    for y, what in ((512, "deck lip row 0"), (513, "deck lip row 1"),
                    (480, "tread row 0"), (481, "tread row 1"),
                    (482, "tread row 2"), (483, "tread row 3")):
        print(f"  row {y} ({what}): {int(d[y].sum())} px changed by shadows")
    Lb = lum(b)
    print("  deck lip L:", [round(float(Lb[y].mean()), 1) for y in (512, 513)])
    print("  dais tread L under console:", [round(float(Lb[y, 525:627].mean()), 1) for y in range(480, 484)])
    print("  pad tread L under reactor:", [round(float(Lb[y, 1253:1370].mean()), 1) for y in range(480, 484)])
    print("  shadow starts at deck row 514 / dais+pad row 484")

    print("\n== reactor pad geometry ==")
    m = np.array(mega)
    L = lum(m[..., :3])
    print("  pad columns 1216-1407 at row 480 (tread lip) L:",
          round(float(L[480, 1216:1408].mean()), 1),
          "row 483 (overhang):", round(float(L[483, 1216:1408].mean()), 1),
          "row 484 (hazard face):", round(float(L[484, 1216:1408].mean()), 1))
    print("  pad end caps: left col 1216-1218 rgb", m[500, 1216:1219, :3].tolist(),
          " right col 1405-1407 rgb", m[500, 1405:1408, :3].tolist())
    print("  reactor base row 479 rgb", m[479, 1300, :3].tolist(),
          " pad tread 480-482 rgb", [m[y, 1300, :3].tolist() for y in range(480, 483)])

    print("\n== cargo pair ==")
    full = Image.open(ENV / "props/cargo_stack/sprite.png").convert("RGBA")
    low = A._cargo_low(full)
    print("  left  stack: 3 crates, x=143-201, y=425-511 (sprite", full.size, ")")
    print("  right stack: 2 crates, x=245-303, y=451-511 (crop", low.size,
          ", mirrored), gap", 245 - 143 - 59, "px")
    # the two scene placements must differ (not a copy-paste pair)
    same = np.array_equal(m[451:512, 143:202, :3], m[451:512, 245:304, :3])
    print("  lower 61 rows identical:", bool(same))

    print("\n== bay accents ==")
    for name, x in (("bay1 left", 137), ("bay1 right", 310), ("bay2 left", 457),
                    ("bay2 right", 694), ("bay3 left", 841), ("bay3 right", 1078),
                    ("bay4 left", 1225), ("bay4 right", 1398)):
        col = m[200:380, x, :3]
        idx = nearest_palette_indices(col)
        print(f"  {name:11s} x={x}: cyan {int((idx == 37).sum())} violet {int((idx == 59).sum())}")

    print("\n== sprite lighting (outer 7 px and left/right thirds) ==")
    for p in sorted((ENV / "props").glob("*/sprite.png")) + sorted((MEGA / "elements").glob("*/sprite.png")):
        im = Image.open(p).convert("RGBA")
        arr = np.array(im)
        al = arr[..., 3]
        L = lum(arr[..., :3])
        def mean_band(x0, x1):
            vals = []
            for x in range(x0, x1):
                msk = al[:, x] == 255
                if msk.any():
                    vals.append(L[msk, x].mean())
            return float(np.mean(vals)) if vals else 0.0
        w = im.width
        rim = mean_band(0, min(7, w)) - mean_band(max(0, w - 7), w)
        third = mean_band(0, w // 3) - mean_band(w - w // 3, w)
        print(f"  {p.parent.name:14s} rim {rim:+.1f} thirds {third:+.1f}")


if __name__ == "__main__":
    main()
