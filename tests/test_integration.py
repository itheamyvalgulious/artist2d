"""Cross-module acceptance checks on the shipped asset pack."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from core.palette_quantizer import palette_violations
from config.namespaces import environment_dir, mega_dir, showcase_dir

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "output"

CHAR_DIRS = ["idle", "running", "attack", "defend", "jump", "in_air"]
ENV_TILES = ["grass", "dirt", "stone", "water"]


def _shipped_files() -> list[Path]:
    files: list[Path] = []
    for a in CHAR_DIRS:
        files += sorted((OUT / "character" / "knight" / a / "frames").glob("frame_*.png"))
        files.append(OUT / "character" / "knight" / a / "sheet.png")
        files.append(OUT / "character" / "knight" / a / "sheet_1x.png")
    files.append(OUT / "character" / "knight" / "char_ref_64.png")
    for n in ENV_TILES:
        files.append(environment_dir("field") / f"{n}_seamless.png")
    files += sorted(environment_dir("field").glob("autotile_*.png"))
    files.append(environment_dir("field") / "stamp" / "stamp_matted.png")
    files.append(mega_dir("field") / "mega_atlas.png")
    files.append(showcase_dir("field") / "scene_1x.png")
    return [p for p in files if p.exists()]


def test_all_shipped_assets_are_palette_pure():
    files = _shipped_files()
    assert len(files) >= 40, f"only found {len(files)} shipped assets"
    bad = []
    for p in files:
        partial, off = palette_violations(Image.open(p).convert("RGBA"))
        if partial or off:
            bad.append((str(p.relative_to(ROOT)), partial, off))
    assert not bad, bad


def test_character_sheets_have_eight_frames():
    for a in CHAR_DIRS:
        sheet = Image.open(OUT / "character" / "knight" / a / "sheet_1x.png")
        assert sheet.size == (64 * 8, 64), (a, sheet.size)


def test_environment_tiles_are_opaque_and_square():
    for n in ENV_TILES:
        img = Image.open(environment_dir("field") / f"{n}_seamless.png").convert("RGBA")
        assert img.size == (32, 32)
        assert np.all(np.array(img)[..., 3] == 255), n


def test_mega_layout_has_no_adjacent_duplicate_interior_tiles():
    data = json.loads((mega_dir("field") / "mega_layout.json").read_text())
    grid = {}
    for cell in data["layout"]:
        grid[(cell["row"], cell["col"])] = cell
    rows = max(r for r, _ in grid) + 1
    cols = max(c for _, c in grid) + 1
    solid = {(r, c) for (r, c), cell in grid.items() if not cell.get("empty")}
    # interior = all 4 neighbours solid
    violations = 0
    for (r, c) in solid:
        if all((r + dr, c + dc) in solid for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]):
            a = grid[(r, c)].get("atlas_x", -1)
            for dr, dc in [(0, 1), (1, 0)]:
                nb = grid.get((r + dr, c + dc))
                if nb and not nb.get("empty") and nb.get("atlas_x", -1) == a and a >= 0:
                    violations += 1
    assert violations == 0, f"{violations} adjacent duplicate interior tiles"


def test_showcase_scene_exists():
    scene = Image.open(showcase_dir("field") / "scene.png")
    assert scene.size == (3584, 2432)


def test_reference_panel_is_bit_locked():
    from character.sheet_compositor import board_panel_box
    work = ROOT / "work" / "character" / "knight"
    for a in CHAR_DIRS:
        d = OUT / "character" / "knight" / a
        if not (d / "board.png").exists():
            d = work / a
        board = np.array(Image.open(d / "board.png").convert("RGB"))
        remaster = np.array(Image.open(d / "remaster.png").convert("RGB"))
        x0, y0, x1, y1 = board_panel_box(0)
        diff = np.abs(board[y0:y1, x0:x1].astype(int) - remaster[y0:y1, x0:x1].astype(int)).max()
        assert diff == 0, f"{a}: reference panel changed by {diff}"
        assert (d / "mask.png").exists()


def test_mega_strict_decal_coverage():
    report = json.loads((mega_dir("field") / "report.json").read_text())
    assert report["coverage"] >= 0.30, report
