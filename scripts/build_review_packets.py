"""Build review-only contact sheets for the independent multimodal reviewer.

The reviewer must see every shipped frame, not a handful of samples.  These
packets are *not* deliverables: they only arrange the already-shipped files so
100% coverage is practical to inspect.

    .venv/bin/python scripts/build_review_packets.py
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from config.namespaces import character_dir, environment_dir, mega_dir, showcase_dir  # noqa: E402

REVIEW = ROOT / "work" / "review"
BG = (18, 18, 26, 255)
MAGENTA = (255, 0, 255, 255)
ACTIONS = ("idle", "run", "jump", "in_air", "shoot1", "shoot2", "shoot3",
           "slash1", "slash2", "slash3", "block", "roll")


def _canvas(w: int, h: int, bg=BG) -> Image.Image:
    return Image.new("RGBA", (w, h), bg)


def _paste_center(canvas: Image.Image, im: Image.Image, box: tuple[int, int, int, int],
                  margin: int = 10) -> None:
    x0, y0, x1, y1 = box
    im = im.convert("RGBA")
    avail_w, avail_h = x1 - x0 - 2 * margin, y1 - y0 - 2 * margin
    scale = min(avail_w / im.width, avail_h / im.height)
    nw, nh = max(1, int(im.width * scale)), max(1, int(im.height * scale))
    im = im.resize((nw, nh), Image.NEAREST)
    canvas.alpha_composite(im, (x0 + (x1 - x0 - nw) // 2, y0 + (y1 - y0 - nh) // 2))


def _grid_exact(items: list[Image.Image], cols: int, cell_w: int, cell_h: int,
                labels: list[str] | None = None, bg=BG) -> Image.Image:
    """Paste sprites at their exact pixel scale (no fit-to-cell rescaling)."""
    rows = (len(items) + cols - 1) // cols
    out = _canvas(cols * cell_w, rows * cell_h, bg)
    for i, im in enumerate(items):
        r, c = divmod(i, cols)
        x = c * cell_w + (cell_w - im.width) // 2
        y = r * cell_h + (cell_h - im.height) // 2
        out.alpha_composite(im.convert("RGBA"), (x, y))
        if labels:
            _label(out, labels[i], (c * cell_w + 8, r * cell_h + 6))
    return out


def _label(canvas: Image.Image, text: str, xy: tuple[int, int]) -> None:
    d = ImageDraw.Draw(canvas)
    d.text(xy, text, fill=(220, 230, 240, 255))


def _grid(items: list[Image.Image], cols: int, cell_w: int, cell_h: int,
          labels: list[str] | None = None, bg=BG, margin: int = 8) -> Image.Image:
    rows = (len(items) + cols - 1) // cols
    out = _canvas(cols * cell_w, rows * cell_h, bg)
    for i, im in enumerate(items):
        r, c = divmod(i, cols)
        box = (c * cell_w, r * cell_h, (c + 1) * cell_w, (r + 1) * cell_h)
        _paste_center(out, im, box, margin=margin)
        if labels:
            _label(out, labels[i], (c * cell_w + 8, r * cell_h + 6))
    return out


def build_character() -> Path:
    src = character_dir("agent")
    out = REVIEW / "character"
    out.mkdir(parents=True, exist_ok=True)
    for p in out.glob("*.png"):
        p.unlink()
    manifest: list[str] = []

    # Design sheet: full body + the separate katana / scabbard / pistol parts.
    shutil.copy2(src / "design_sheet.png", out / "00_design_sheet.png")
    manifest += ["00_design_sheet.png"]
    for name in ("parts/katana.png", "parts/scabbard.png", "parts/pistol.png"):
        shutil.copy2(src / name, out / f"02_part_{Path(name).stem}.png")
        manifest.append(f"02_part_{Path(name).stem}.png")

    for action in ACTIONS:
        d = src / action
        report = json.loads((d / "report.json").read_text())
        n = int(report["frames"])
        hi = [Image.open(d / "frames_hi" / f"frame_{i:02d}.png").convert("RGBA") for i in range(n)]
        lo = [Image.open(d / "frames" / f"frame_{i:02d}.png").convert("RGBA") for i in range(n)]
        cols = 4 if n > 4 else n
        hcell = hi[0].width
        _grid(hi, cols, hcell, hcell, [f"frame {i}" for i in range(n)], margin=0).save(out / f"10_{action}_hi_all.png")
        _grid([im.resize((512, 512), Image.NEAREST) for im in lo], cols, 512, 512,
              [f"frame {i}" for i in range(n)], margin=0).save(out / f"11_{action}_64px_all.png")
        manifest += [f"10_{action}_hi_all.png", f"11_{action}_64px_all.png"]

        truth = src / "mannequin" / action / "sheet_shaded.png"
        if not truth.exists():
            truth = ROOT / "work" / "character" / "agent" / "mannequin" / action / "sheet_shaded.png"
        if truth.exists():
            sheet = Image.open(truth).convert("RGB")
            have = sheet.width // 512
            frames = [sheet.crop((i * 512, 0, (i + 1) * 512, 512)) for i in range(min(n, have))]
            _grid(frames, cols, 512, 512, [f"frame {i}" for i in range(len(frames))], margin=0).save(
                out / f"12_{action}_3d_truth_all.png")
            manifest.append(f"12_{action}_3d_truth_all.png")

    # Cross-action consistency: one representative of each action, same scale.
    import json as _json
    reps = []
    for a in ACTIONS:
        n = int(_json.loads((src / a / "report.json").read_text())["frames"])
        k = min(3, n - 1)
        reps.append(Image.open(src / a / "frames" / f"frame_{k:02d}.png").convert("RGBA")
                    .resize((512, 512), Image.NEAREST))
    _grid(reps, 4, 512, 512, list(ACTIONS), margin=0).save(out / "20_cross_action.png")
    manifest.append("20_cross_action.png")

    # Transition anchors: build every pair from the shipped transitions.json.
    import json as _json
    trans = _json.loads((src / "transitions.json").read_text()) if (src / "transitions.json").exists() else {}
    pairs: list[tuple[str, Path]] = []
    for action, anchors in trans.items():
        for which, info in anchors.items():
            if not info:
                continue
            anchor = info.get("anchor", "")
            dep, idx = anchor.split(":", 1)
            frame = "frame_00.png" if which == "start" else "frame_07.png"
            pairs.append((f"{action} {which}", src / action / "frames" / frame))
            pairs.append((anchor, src / dep / "frames" / f"frame_{int(idx):02d}.png"))
    imgs = [Image.open(p).convert("RGBA").resize((512, 512), Image.NEAREST)
            for _, p in pairs]
    _grid(imgs, 4, 512, 512, [n for n, _ in pairs], margin=0).save(out / "21_transition_pairs.png")
    manifest.append("21_transition_pairs.png")

    # Difference proof: an identical anchor pair produces a pure black tile.
    diffs = []
    labels = []
    for i in range(0, len(imgs), 2):
        a, b = imgs[i].convert("RGB"), imgs[i + 1].convert("RGB")
        from PIL import ImageChops
        diffs.append(ImageChops.difference(a, b))
        labels.append(f"{pairs[i][0]} vs {pairs[i+1][0]}")
    _grid(diffs, 2, 512, 512, labels, margin=0, bg=(0, 0, 0, 255)).save(out / "23_transition_diff.png")
    manifest.append("23_transition_diff.png")

    # Run loop: the honest 4-pose cycle, shown across the wrap 2,3,0,1.
    loop = [Image.open(src / "run" / "frames_hi" / f"frame_{i:02d}.png").convert("RGBA")
            for i in (6, 7, 0, 1)]
    _grid(loop, 4, 512, 512, ["f6", "f7", "f0", "f1"], margin=0).save(out / "22_run_loop.png")
    manifest.append("22_run_loop.png")

    trans = {}
    tp = src / "transitions.json"
    if tp.exists():
        trans = json.loads(tp.read_text())
    trans_lines = []
    for action, anchors in trans.items():
        for which, info in anchors.items():
            if info:
                trans_lines.append(f"- {action} {which}: `{info.get('anchor')}` "
                                   f"sha256 `{info.get('sha256','')}`")
    (out / "MANIFEST.md").write_text(
        "# Character review packet (agent)\n\n"
        "All paths are review copies of shipped assets. `10_*` = every 512px frame shipped for "
        "that action (eight frames per action; slash2 hi-res frames are 640 px so the raised "
        "blade fits, others 512), `11_*` = the matching 64px game frames upscaled 8x, "
        "`12_*` = the 3D mannequin truth for the same frames. `20` is "
        "cross-action consistency; `21` are transition anchors (pairs must be pixel-identical); "
        "`22` is the run cycle wrap (f6,f7,f0,f1); `23` is the pixel-difference proof for each "
        "anchor pair (black = identical).\n\n"
        + "\n".join(f"- `{n}`" for n in manifest) + "\n\n## Transition SHA-256\n\n"
        + "\n".join(trans_lines) + "\n",
        encoding="utf-8")
    return out


def _catalog(items: list[tuple[str, Path]], cols: int, cell_w: int, cell_h: int,
             scale: int, out: Path) -> None:
    imgs = []
    labels = []
    for name, p in items:
        im = Image.open(p).convert("RGBA")
        im = im.resize((im.width * scale, im.height * scale), Image.NEAREST)
        imgs.append(im)
        labels.append(name)
    # Grow the cell if the requested exact scale does not fit: the 118x203 hull
    # at 3x is 609 px tall and used to be clipped top and bottom in a 520 cell.
    cell_w = max(cell_w, max(im.width for im in imgs) + 24)
    cell_h = max(cell_h, max(im.height for im in imgs) + 24)
    _grid_exact(imgs, cols, cell_w, cell_h, labels).save(out)


def build_ship() -> Path:
    env = environment_dir("ship")
    mg = mega_dir("ship")
    show = showcase_dir("ship")
    out = REVIEW / "ship"
    out.mkdir(parents=True, exist_ok=True)
    for p in out.glob("*.png"):
        p.unlink()
    manifest = []
    for src, dst in [
        (env / "tileset_preview_x8.png", "00_tileset_x8.png"),
        (env / "tileset_sample_x4.png", "01_tileset_sample_x4.png"),
        (mg / "ship_mega_preview.png", "05_whole_ship_x2.png"),
        (show / "scene.png", "06_showcase_x2.png"),
    ]:
        shutil.copy2(src, out / dst)
        manifest.append(dst)

    meta = json.loads((env / "tileset.json").read_text())
    tile_items = [(n, env / "tiles" / f"{n}.png") for n in meta["tiles"]]
    _catalog(tile_items, 6, 220, 220, 5, out / "02_all_tiles_x5.png")
    manifest.append("02_all_tiles_x5.png")

    med = [
        ("console_bank", env / "props" / "console_bank" / "sprite.png"),
        ("cargo_stack", env / "props" / "cargo_stack" / "sprite.png"),
        ("server_rack", env / "props" / "server_rack" / "sprite.png"),
    ]
    _catalog(med, 3, 520, 520, 3, out / "03_medium_catalog_x3.png")
    manifest.append("03_medium_catalog_x3.png")

    meg = [
        ("hull_frame", mg / "elements" / "hull_frame" / "sprite.png"),
        ("viewport", mg / "elements" / "viewport" / "sprite.png"),
        ("reactor_core", mg / "elements" / "reactor_core" / "sprite.png"),
    ]
    _catalog(meg, 3, 520, 520, 3, out / "04_mega_catalog_x3.png")
    manifest.append("04_mega_catalog_x3.png")

    (out / "MANIFEST.md").write_text(
        "# Ship environment review packet\n\n"
        "`02` is the complete tile atlas (every tile, 25: 22 originals + 3 real platform-step "
        "variants); `03` the three medium structures; `04` the three modular mega elements; "
        "`05` the whole-ship mega assembly; `06` the showcase with the agent character. "
        "`00` and `01` are the tile atlas and a tiled room slice.\n\n"
        + "\n".join(f"- `{n}`" for n in manifest) + "\n",
        encoding="utf-8")
    return out


def main() -> None:
    c = build_character()
    s = build_ship()
    print("character:", c)
    print("ship:", s)


if __name__ == "__main__":
    main()
