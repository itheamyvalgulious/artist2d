"""Enforce the asset-set isolation requested by the user.

``character`` was already namespaced by character name.  Environment, mega
and showcase must follow the same rule: their immediate children are set
directories, never loose files that could mix the top-down ``field`` world
with the side-view ``ship`` world.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from config.namespaces import SETS, environment_dir, mega_dir, showcase_dir

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "output"


@pytest.mark.parametrize("kind,fn", [("environment", environment_dir),
                                     ("mega", mega_dir),
                                     ("showcase", showcase_dir)])
def test_asset_sets_are_isolated(kind, fn):
    root = OUT / kind
    assert root.exists()
    loose = [p.name for p in root.iterdir() if p.is_file()]
    assert not loose, f"{kind}/ has loose files: {loose}"
    dirs = {p.name for p in root.iterdir() if p.is_dir()}
    assert {"field", "ship"}.issubset(dirs)
    for s in SETS:
        assert fn(s).is_dir(), f"{kind}/{s} missing"


def test_character_namespaces():
    chars = {p.name for p in (OUT / "character").iterdir() if p.is_dir()}
    assert "knight" in chars


def test_worlds_do_not_share_tiles():
    field = OUT / "environment" / "field"
    ship = OUT / "environment" / "ship"
    assert (field / "grass_seamless.png").exists()
    assert (ship / "tileset.png").exists()
    assert not (ship / "grass_seamless.png").exists()
    assert not (field / "tileset.png").exists()
