"""Playable previews and animated tiles (acceptance feedback round)."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pytest
from PIL import Image, ImageSequence

from core.palette_quantizer import PALETTE_RGB, palette_violations
from environment.seamless_toroidal import ks_seam_test

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "output"
CHAR = OUT / "character" / "knight"
from config.namespaces import environment_dir  # noqa: E402
ENV = environment_dir("field")
ACTIONS = ["idle", "running", "attack", "defend", "jump", "in_air"]


def _frame_hashes(frames) -> int:
    return len({hashlib.sha256(f.convert("RGBA").tobytes()).hexdigest() for f in frames})


@pytest.mark.parametrize("action", ACTIONS)
def test_character_apng_plays(action):
    path = CHAR / action / "preview.png"
    assert path.exists(), f"missing {path}"
    im = Image.open(path)
    assert im.n_frames == 8, f"{action}: {im.n_frames} preview frames"
    assert im.size == (256, 256)
    frames = [f.convert("RGBA") for f in ImageSequence.Iterator(im)]
    assert _frame_hashes(frames) >= 4, f"{action}: preview is frozen"
    for f in frames:
        p, o = palette_violations(f)
        assert p == 0 and o == 0, f"{action}: preview frame not palette-pure"
    gif = CHAR / action / "preview.gif"
    assert gif.exists() and gif.stat().st_size > 0


@pytest.mark.parametrize("name", ["water", "grass"])
def test_tile_animation(name):
    d = ENV / f"{name}_anim"
    frames = [Image.open(d / f"frame_{i:02d}.png").convert("RGBA") for i in range(4)]
    assert _frame_hashes(frames) == 4, f"{name}: animation frames are not distinct"
    for i, f in enumerate(frames):
        assert f.size == (32, 32)
        p, o = palette_violations(f)
        assert p == 0 and o == 0, f"{name} frame {i}: not palette-pure"
        ks = ks_seam_test(f)
        assert ks["p_value"] > 0.05 and ks["p_value_3x3"] > 0.05, (name, i, ks)
    im = Image.open(d / f"{name}_anim.png")
    assert im.n_frames == 4 and im.size == (256, 256)
    assert (d / f"{name}_anim.gif").exists()


def test_terrain_preview_is_animated():
    path = ENV / "terrain_preview_anim.png"
    assert path.exists()
    im = Image.open(path)
    assert im.n_frames == 4
    hashes = {hashlib.sha256(f.convert("RGBA").tobytes()).hexdigest()
              for f in ImageSequence.Iterator(im)}
    assert len(hashes) == 4


def test_terrain_preview_stitches_47_tiles():
    path = ENV / "terrain_preview.png"
    assert path.exists()
    im = Image.open(path).convert("RGBA")
    assert im.size == (960, 640)
    p, o = palette_violations(im)
    assert p == 0 and o == 0
    # the preview actually exercises the atlas: every one of the 47 states is
    # present in the grass mask (interior tiles included)
    meta = json.loads((ENV / "autotile_grass_over_dirt.json").read_text())
    assert meta["tile_count"] == 47
    # water bank atlas generated for the pond edges
    water_meta = json.loads((ENV / "autotile_water_over_dirt.json").read_text())
    assert water_meta["tile_count"] == 47
    arr = np.array(Image.open(ENV / "autotile_water_over_dirt.png").convert("RGBA"))
    hashes = {hashlib.sha256(arr[(i // 8) * 32:(i // 8 + 1) * 32,
                                 (i % 8) * 32:(i % 8 + 1) * 32].tobytes()).hexdigest()
              for i in range(47)}
    assert len(hashes) == 47


def test_shipped_animation_frames_are_in_palette():
    palette = {tuple(int(v) for v in c) for c in PALETTE_RGB}
    for f in sorted(OUT.rglob("preview.png")) + sorted(OUT.rglob("*_anim/*.png")):
        if "/mannequin/" in str(f):
            continue
        im = Image.open(f)
        for frame in ImageSequence.Iterator(im):
            rgba = frame.convert("RGBA")
            alpha = np.array(rgba)[..., 3]
            assert set(np.unique(alpha)).issubset({0, 255})
            vis = np.array(rgba)[alpha == 255][:, :3]
            for c in vis[:500]:
                assert tuple(int(v) for v in c) in palette, (f, tuple(c))
