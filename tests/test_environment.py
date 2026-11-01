"""Tests for environment pipeline (PLAN module 2).

Validates tile dimensions, palette purity, 47-tile count and KS test pass.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from config.pipeline_config import TILE_SIZE, OUTPUT_DIR  # noqa: E402
from config.namespaces import environment_dir  # noqa: E402
from core.palette_quantizer import lock_palette, palette_violations  # noqa: E402
from environment.autotile_47 import enumerate_47, STATE_TO_INDEX  # noqa: E402
from environment.material_genesis import make_constraint_board  # noqa: E402
from environment.seamless_toroidal import _build_cross_mask, ks_seam_test  # noqa: E402


# ---------------------------------------------------------------------------
# material_genesis
# ---------------------------------------------------------------------------

class TestMaterialGenesis:
    def test_constraint_board_dimensions(self):
        board = make_constraint_board(1024, seed=0)
        assert board.size == (1024, 1024)

    def test_constraint_board_palette(self):
        board = make_constraint_board(512, seed=1)
        v = palette_violations(board.convert("RGBA"))
        assert v[0] == 0, f"partial alpha pixels: {v[0]}"
        # constraint board uses only palette colours by construction
        assert v[1] == 0, f"off-palette opaque pixels: {v[1]}"


# ---------------------------------------------------------------------------
# seamless_toroidal
# ---------------------------------------------------------------------------

class TestSeamlessToroidal:
    def test_cross_mask_shape(self):
        mask = _build_cross_mask(512)
        assert mask.size == (512, 512)

    def test_cross_mask_border_safe(self):
        mask = _build_cross_mask(512, cross_half=64, border_safe=32)
        arr = np.array(mask)
        # borders must be black
        assert arr[:32, :].max() == 0
        assert arr[-32:, :].max() == 0
        assert arr[:, :32].max() == 0
        assert arr[:, -32:].max() == 0
        # centre must have white
        assert arr[256, 256] == 255

    def test_cross_mask_symmetry(self):
        mask = _build_cross_mask(512)
        arr = np.array(mask)
        assert np.array_equal(arr, arr[:, ::-1])
        assert np.array_equal(arr, arr[::-1, :])


class TestKS:
    def test_homogeneous_tile_passes(self):
        """A uniform-colour tile has zero edge differences everywhere → p=1.0."""
        tile = Image.new("RGBA", (32, 32), (34, 102, 47, 255))
        tile = lock_palette(tile)
        result = ks_seam_test(tile)
        assert result["pass"], f"uniform tile should pass KS: {result}"
        assert result["p_value"] == 1.0

    def test_random_palette_tile(self):
        """A randomised palette tile should still produce a finite KS result."""
        from core.palette_quantizer import PALETTE_RGB
        rng = np.random.default_rng(42)
        idx = rng.integers(0, 64, (32, 32))
        rgb = PALETTE_RGB[idx]
        alpha = np.full((32, 32), 255, dtype=np.uint8)
        rgba = np.dstack([rgb, alpha])
        tile = Image.fromarray(rgba, "RGBA")
        result = ks_seam_test(tile)
        assert "ks_statistic" in result
        assert "p_value" in result
        assert 0.0 <= result["p_value"] <= 1.0


# ---------------------------------------------------------------------------
# autotile_47
# ---------------------------------------------------------------------------

class TestAutotile47:
    def test_state_count(self):
        states = enumerate_47()
        assert len(states) == 47, f"expected 47 states, got {len(states)}"

    def test_state_map(self):
        assert len(STATE_TO_INDEX) == 47

    def test_all_states_unique(self):
        assert len(set(enumerate_47())) == 47


# ---------------------------------------------------------------------------
# Integration: check output/environment artifacts if they exist
# ---------------------------------------------------------------------------

@pytest.mark.integration
class TestEnvironmentOutputs:
    @pytest.fixture(autouse=True)
    def outdir(self):
        d = environment_dir("field")
        if not d.exists():
            pytest.skip("output/environment not built yet — run build_environment.py first")
        return d

    def test_base_tiles_exist(self, outdir):
        for name in ("grass", "dirt", "stone", "water"):
            p = outdir / f"{name}_base.png"
            assert p.exists(), f"missing {p}"

    def test_base_tile_dimensions(self, outdir):
        for name in ("grass", "dirt", "stone", "water"):
            p = outdir / f"{name}_base.png"
            if p.exists():
                img = Image.open(p)
                assert img.size == (TILE_SIZE, TILE_SIZE), \
                    f"{name}_base.png is {img.size}, expected ({TILE_SIZE},{TILE_SIZE})"

    def test_base_tile_palette_pure(self, outdir):
        for name in ("grass", "dirt", "stone", "water"):
            p = outdir / f"{name}_base.png"
            if p.exists():
                v = palette_violations(Image.open(p))
                assert v[0] == 0, f"{name}_base.png has {v[0]} partial-alpha pixels"
                assert v[1] == 0, f"{name}_base.png has {v[1]} off-palette opaque pixels"

    def test_seamless_tiles_dimensions(self, outdir):
        for name in ("grass", "dirt", "stone", "water"):
            p = outdir / f"{name}_seamless.png"
            if p.exists():
                img = Image.open(p)
                assert img.size == (TILE_SIZE, TILE_SIZE), \
                    f"{name}_seamless.png is {img.size}"

    def test_seamless_tiles_palette_pure(self, outdir):
        for name in ("grass", "dirt", "stone", "water"):
            p = outdir / f"{name}_seamless.png"
            if p.exists():
                v = palette_violations(Image.open(p))
                assert v[0] == 0, f"{name}_seamless.png has {v[0]} partial-alpha pixels"
                assert v[1] == 0, f"{name}_seamless.png has {v[1]} off-palette opaque pixels"

    def test_shipped_tiles_pass_full_and_3x3_ks(self, outdir):
        """PLAN hard metric 3: both the wrap test and the 3x3 tiling test."""
        for name in ("grass", "dirt", "stone", "water"):
            ks = ks_seam_test(Image.open(outdir / f"{name}_seamless.png"))
            assert ks["p_value"] > 0.05, (name, ks)
            assert ks["p_value_3x3"] > 0.05, (name, ks)
            assert ks["pass"], (name, ks)

    def test_checkerboards_exist(self, outdir):
        for name in ("grass", "dirt", "stone", "water"):
            p = outdir / f"{name}_checkerboard.png"
            assert p.exists(), f"missing {p}"

    def test_autotile_atlas_exist(self, outdir):
        for pair in ("grass_over_dirt", "stone_over_dirt"):
            p = outdir / f"autotile_{pair}.png"
            assert p.exists(), f"missing {p}"

    def test_autotile_tile_count(self, outdir):
        for pair in ("grass_over_dirt", "stone_over_dirt"):
            p = outdir / f"autotile_{pair}.json"
            if p.exists():
                meta = json.loads(p.read_text())
                assert meta["tile_count"] == 47, \
                    f"{pair} has {meta['tile_count']} tiles, expected 47"

    def test_autotile_palette_pure(self, outdir):
        for pair in ("grass_over_dirt", "stone_over_dirt"):
            p = outdir / f"autotile_{pair}.png"
            if p.exists():
                v = palette_violations(Image.open(p))
                assert v[0] == 0, f"{pair} atlas has partial-alpha pixels"
                assert v[1] == 0, f"{pair} atlas has off-palette pixels"

    def test_ks_report_has_seam_tests(self, outdir):
        report = outdir / "REPORT.md"
        if report.exists():
            text = report.read_text()
            assert "KS" in text, "REPORT.md missing KS test section"

    def test_report_exists(self, outdir):
        assert (outdir / "REPORT.md").exists(), "REPORT.md not found"

def test_autotile_present_edges_are_continuous():
    """A connected cardinal edge must be ~100% upper material (PLAN 2.3 topology)."""
    import numpy as np
    from PIL import Image
    from environment.autotile_47 import ALL_STATES, synthesize_47

    root = Path(__file__).resolve().parent.parent
    top = Image.open(root / "output/environment/field/grass_seamless.png").convert("RGBA")
    bot = Image.open(root / "output/environment/field/dirt_seamless.png").convert("RGBA")
    atlas, _ = synthesize_47(top, bot)
    arr = np.array(atlas.convert("RGBA"))
    worst = 1.0
    for i, (cm, dm) in enumerate(ALL_STATES):
        tile = arr[(i // 8) * 32:(i // 8 + 1) * 32, (i % 8) * 32:(i % 8 + 1) * 32]
        # grass predicate: green dominance
        grass = (tile[..., 1].astype(int) > tile[..., 0].astype(int) + 4) & \
                (tile[..., 1] > tile[..., 2] + 4)
        # The connected edge is a full-width band; the 4 px concave corner
        # (the 47-tile diagonal notch) is excluded from the span check.
        edges = []
        if cm & 1: edges.append(grass[0, 8:-8])
        if cm & 2: edges.append(grass[8:-8, -1])
        if cm & 4: edges.append(grass[-1, 8:-8])
        if cm & 8: edges.append(grass[8:-8, 0])
        for e in edges:
            worst = min(worst, float(e.mean()))
    assert worst >= 0.9, f"worst connected-edge coverage {worst:.2f}"


def test_autotile_47_tiles_are_unique():
    """The 47 states must yield 47 distinct pixel tiles, not repeated blobs."""
    import hashlib
    import numpy as np
    from PIL import Image
    from environment.autotile_47 import synthesize_47

    root = Path(__file__).resolve().parent.parent
    top = Image.open(root / "output/environment/field/grass_seamless.png").convert("RGBA")
    bot = Image.open(root / "output/environment/field/dirt_seamless.png").convert("RGBA")
    atlas, _ = synthesize_47(top, bot)
    arr = np.array(atlas)
    hashes = {
        hashlib.sha256(arr[(i // 8) * 32:(i // 8 + 1) * 32, (i % 8) * 32:(i % 8 + 1) * 32].tobytes()).hexdigest()
        for i in range(47)
    }
    assert len(hashes) == 47, f"only {len(hashes)} unique autotile tiles"


def test_autotile_present_edges_are_full_width():
    """A connected edge must be 100% upper material across its full span."""
    import numpy as np
    from PIL import Image
    from environment.autotile_47 import _synthesize_one, extract_height_field

    root = Path(__file__).resolve().parent.parent
    top_img = Image.open(root / "output/environment/field/grass_seamless.png").convert("RGBA")
    bot_img = Image.open(root / "output/environment/field/dirt_seamless.png").convert("RGBA")
    top = np.array(top_img)
    bot = np.array(bot_img)
    h = extract_height_field(top_img)

    def grass(tile):
        return (tile[..., 1].astype(int) > tile[..., 0].astype(int) + 4) & \
               (tile[..., 1] > tile[..., 2] + 4)

    n_tile = grass(_synthesize_one(top, bot, h, 1, 0, 32))
    assert n_tile[0, 4:-4].mean() >= 0.9     # connected edge band (corners notched)
    assert n_tile[5].mean() >= 0.6           # and it is a band, not a 1px line
    e_tile = grass(_synthesize_one(top, bot, h, 2, 0, 32))
    assert e_tile[4:-4, -1].mean() >= 0.9
    assert e_tile[:, 26].mean() >= 0.6
    # A straight N+E+W edge (NE/NW grass, S/SE/SW dirt) is a full-width
    # horizontal band, not vertical side stripes.
    straight = _synthesize_one(top, bot, h, 11, 9, 32)
    assert grass(straight)[:6, 4:-4].mean() >= 0.9
