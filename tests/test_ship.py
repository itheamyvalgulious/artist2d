"""Acceptance tests for the side-view spaceship environment set."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from config.namespaces import environment_dir, mega_dir, showcase_dir
from core.palette_quantizer import palette_violations

ROOT = Path(__file__).resolve().parent.parent
ENV = environment_dir("ship")
MG = mega_dir("ship")
SHOW = showcase_dir("ship")

MEDIUM = {"console_bank": (128, 64), "cargo_stack": (64, 96), "server_rack": (64, 112)}
MEGA = {"hull_frame": (128, 256), "viewport": (128, 96), "reactor_core": (128, 192)}


def test_materials_are_seamless():
    rep = json.loads((ENV / "materials.json").read_text())
    assert set(rep) == {"deck", "wall", "grate", "conduit"}
    for name, r in rep.items():
        assert r["ks"]["pass"], (name, r)
        img = Image.open(ENV / "tiles" / f"{name}_seamless.png").convert("RGBA")
        assert img.size == (32, 32)
        assert palette_violations(img) == (0, 0)


def test_tileset_is_complete():
    meta = json.loads((ENV / "tileset.json").read_text())
    names = meta["tiles"]
    required = {"deck_top", "deck_top_left", "deck_top_right", "deck_fill",
                "wall_flat", "wall_flat_light", "ceiling", "grate_top",
                "hazard", "vent", "window", "pipe_h", "pipe_v"}
    assert required.issubset(names)
    assert len(names) >= 20
    for name in names:
        img = Image.open(ENV / "tiles" / f"{name}.png").convert("RGBA")
        assert img.size == (32, 32), name
        assert palette_violations(img) == (0, 0), name


@pytest.mark.parametrize("name,size", list(MEDIUM.items()))
def test_medium_structures(name, size):
    p = ENV / "props" / name / "sprite.png"
    img = Image.open(p).convert("RGBA")
    assert img.size == size
    assert palette_violations(img) == (0, 0)
    meta = json.loads((ENV / "props" / name / "metadata.json").read_text())
    assert meta["kind"] == "medium structure"
    assert meta["pivot"] == [size[0] // 2, size[1]]


@pytest.mark.parametrize("name,size", list(MEGA.items()))
def test_mega_elements(name, size):
    p = MG / "elements" / name / "sprite.png"
    img = Image.open(p).convert("RGBA")
    assert img.size == size
    assert palette_violations(img) == (0, 0)
    meta = json.loads((MG / "elements" / name / "metadata.json").read_text())
    assert meta["kind"] == "mega element"


def test_mega_assembly():
    img = Image.open(MG / "ship_mega_1x.png").convert("RGBA")
    assert img.size == (48 * 32, 20 * 32)
    assert palette_violations(img) == (0, 0)
    preview = Image.open(MG / "ship_mega_preview.png")
    assert preview.size == (img.width * 2, img.height * 2)
    layout = json.loads((MG / "ship_layout.json").read_text())
    assert layout["scene"]["width_tiles"] == 48
    assert {e["id"] for e in layout["mega_elements"]} == set(MEGA)


def test_showcase_scene():
    img = Image.open(SHOW / "scene_1x.png").convert("RGBA")
    assert img.size == (48 * 32, 20 * 32)
    assert palette_violations(img) == (0, 0)
    assert Image.open(SHOW / "scene.png").size == (img.width * 2, img.height * 2)


def test_reports_exist():
    assert (ENV / "REPORT.md").exists()
    assert (ENV / "report.json").exists()
    assert (MG / "report.json").exists()
    assert (SHOW / "report.json").exists()
    rep = json.loads((MG / "report.json").read_text())
    assert rep["set"] == "ship"
    assert rep["assembly"]["palette_violations"] == [0, 0]
