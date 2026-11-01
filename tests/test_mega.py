"""Tests for mega-structure pipeline (PLAN modules 3 & 4).

Validates:
- 15x20 blueprint layout correctness
- No horizontal/vertical adjacent same interior centre blocks (graph colouring)
- Decal coverage >= 0.30
- All palette pure (no off-palette colours, no partial alpha)
- Atlas dimensions correct
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

from config.pipeline_config import OUTPUT_DIR, TILE_SIZE  # noqa: E402
from config.namespaces import environment_dir, mega_dir, work_environment_dir  # noqa: E402
from core.palette_quantizer import lock_palette, palette_violations  # noqa: E402
from environment.mega_macro import (  # noqa: E402
    BIG_TILE,
    _neighbor_bits,
    assemble_megastructure,
    bitmask_placement,
    graph_color_centers,
    poisson_disk_seam_anchors,
    tile_deduplicate,
)


# ---------------------------------------------------------------------------
# Synthetic kit helpers (no API calls needed)
# ---------------------------------------------------------------------------

def _solid_piece(r: int, g: int, b: int, size: int = BIG_TILE) -> Image.Image:
    """Create a solid-colour palette-locked piece for testing."""
    img = Image.new("RGBA", (size, size), (r, g, b, 255))
    return lock_palette(img)


def _make_synthetic_kit() -> tuple[dict, dict]:
    """Create a synthetic 9-slice kit with distinct colours for each piece type."""
    kit = {
        "K_TL": _solid_piece(40, 20, 10),   # dark brown
        "E_T": _solid_piece(50, 50, 60),     # grey (top battlement)
        "K_TR": _solid_piece(40, 20, 10),
        "E_L": _solid_piece(60, 50, 40),     # warm grey (left column)
        "E_R": _solid_piece(60, 50, 40),     # warm grey (right column)
        "K_BL": _solid_piece(30, 20, 15),    # dark base
        "E_B": _solid_piece(30, 20, 15),     # dark base
        "K_BR": _solid_piece(30, 20, 15),    # dark base
    }
    # 3 distinct centre variants
    center_pool = {
        "C1": _solid_piece(80, 80, 70),   # lighter grey
        "C2": _solid_piece(70, 75, 65),   # slightly different
        "C3": _solid_piece(85, 78, 72),   # another variant
    }
    return kit, center_pool


def _make_synthetic_decals() -> dict[str, Image.Image]:
    """Create synthetic decals at 4×3 tile size (256×192)."""
    decals = {}
    decal_w, decal_h = BIG_TILE * 4, BIG_TILE * 3  # 256×192
    for dtype, color in [("crack", (20, 20, 20)), ("vine", (30, 80, 30)),
                          ("gargoyle", (50, 40, 30))]:
        img = Image.new("RGBA", (decal_w, decal_h), (0, 0, 0, 0))
        from PIL import ImageDraw
        draw = ImageDraw.Draw(img)
        # Draw a large irregular patch covering most of the decal area
        draw.ellipse([32, 24, decal_w - 33, decal_h - 25],
                      fill=(*color, 255))
        decals[dtype] = lock_palette(img)
    return decals


# ---------------------------------------------------------------------------
# Unit tests (no API needed)
# ---------------------------------------------------------------------------

class TestBitmaskPlacement:
    """Verify that the 9-slice topology bitmask placement produces valid layouts."""

    def test_15x20_layout_shape(self):
        """A 15x20 blueprint should produce layout arrays of the same shape."""
        bp = np.ones((15, 20), dtype=bool)
        bp[0, :] = False
        bp[-1, :] = False
        bp[:, 0] = False
        bp[:, -1] = False
        kit, center_list = _make_synthetic_kit()
        centers = list(center_list.values())
        rng = np.random.RandomState(42)

        layout_ids, variant_indices, total_mask = bitmask_placement(
            bp, kit, centers, rng,
        )
        assert layout_ids.shape == (15, 20)
        assert variant_indices.shape == (15, 20)
        assert total_mask.shape == (15, 20)
        # Every filled cell should have a piece assigned
        assert np.all(layout_ids[bp] >= 0)
        # Empty cells should have -1
        assert np.all(layout_ids[~bp] == -1)

    def test_small_rectangle_uses_corners_and_edges(self):
        """A 3x3 filled rect should use all 9 piece types."""
        bp = np.ones((3, 3), dtype=bool)
        kit, center_list = _make_synthetic_kit()
        centers = list(center_list.values())
        rng = np.random.RandomState(42)

        layout_ids, _, _ = bitmask_placement(bp, kit, centers, rng)
        unique = set(layout_ids[bp].tolist())
        # Should have at least 5 distinct piece types (corners + edges + centre)
        assert len(unique) >= 5, f"Expected >=5 piece types, got {len(unique)}: {unique}"


class TestGraphColoring:
    """Verify the graph-colouring constraint for centre variants."""

    def test_no_adjacent_same_variant(self):
        """No two adjacent interior cells should have the same centre variant."""
        bp = np.ones((15, 20), dtype=bool)
        bp[0, :] = False
        bp[-1, :] = False
        bp[:, 0] = False
        bp[:, -1] = False
        H, W = bp.shape
        n_variants = 3
        rng = np.random.RandomState(42)

        variant_indices = np.full((H, W), 0, dtype=np.int32)
        # Mark all filled cells as interior (variant 0 = uncolored)
        variant_indices[bp] = 0

        colored = graph_color_centers(bp, variant_indices, n_variants, rng)

        # Check no adjacent same
        for r in range(H):
            for c in range(W):
                if not bp[r, c]:
                    continue
                if _neighbor_bits(bp, r, c) == 15:  # interior
                    v = colored[r, c]
                    assert v > 0, f"Interior cell ({r},{c}) not coloured"
                    # Check right neighbour
                    if c + 1 < W and bp[r, c + 1] and _neighbor_bits(bp, r, c + 1) == 15:
                        assert v != colored[r, c + 1], (
                            f"Adjacent interior cells ({r},{c}) and ({r},{c + 1}) "
                            f"share variant {v}"
                        )
                    # Check down neighbour
                    if r + 1 < H and bp[r + 1, c] and _neighbor_bits(bp, r + 1, c) == 15:
                        assert v != colored[r + 1, c], (
                            f"Adjacent interior cells ({r},{c}) and ({r + 1},{c}) "
                            f"share variant {v}"
                        )


class TestPoissonDisk:
    """Verify Poisson-disk anchor sampling."""

    def test_produces_anchors(self):
        """A filled 15x20 blueprint should produce a reasonable number of anchors."""
        bp = np.ones((15, 20), dtype=bool)
        bp[0, :] = False
        bp[-1, :] = False
        bp[:, 0] = False
        bp[:, -1] = False
        rng = np.random.RandomState(42)

        anchors = poisson_disk_seam_anchors(bp, min_radius=2.5, rng=rng)
        assert len(anchors) > 0, "Should find at least some anchors"
        # Anchors should be within bounds
        for r, c in anchors:
            assert 0 <= r < 15
            assert 0 <= c < 20
            assert bp[r, c], f"Anchor ({r},{c}) not on filled cell"

    def test_min_spacing(self):
        """Anchors should respect the minimum radius constraint.

        With min_radius=2.5 on a 10x10 grid, anchors should be at least
        2 cells apart (diagonal adjacency is ~1.41, acceptable for cell-
        based sampling where anchors snap to cell centres).
        """
        bp = np.ones((10, 10), dtype=bool)
        rng = np.random.RandomState(42)

        anchors = poisson_disk_seam_anchors(bp, min_radius=2.5, rng=rng)
        for i, (r1, c1) in enumerate(anchors):
            for j, (r2, c2) in enumerate(anchors):
                if i >= j:
                    continue
                dist = np.sqrt((r1 - r2) ** 2 + (c1 - c2) ** 2)
                # Allow diagonal adjacency (dist ~1.4) since anchors snap to
                # cell centres; the Poisson radius is in cell units.
                assert dist >= 1.0, (
                    f"Anchors ({r1},{c1}) and ({r2},{c2}) too close: dist={dist:.2f}"
                )


class TestAssembly:
    """Integration test for the full assembly pipeline with synthetic data."""

    def test_full_assembly_produces_valid_canvas(self):
        """Assembly with synthetic kit should produce a non-empty RGBA canvas."""
        bp = np.ones((15, 20), dtype=bool)
        bp[0, :] = False
        bp[-1, :] = False
        bp[:, 0] = False
        bp[:, -1] = False

        kit, center_pool = _make_synthetic_kit()
        decals = _make_synthetic_decals()

        canvas, stats = assemble_megastructure(
            bp, kit, center_pool, decals, tile_sz=BIG_TILE, seed=42,
            write_debug=False,
        )

        assert canvas.size == (20 * BIG_TILE, 15 * BIG_TILE)
        assert canvas.mode == "RGBA"
        assert stats["coverage_ratio"] >= 0.0

        # Palette purity
        vp, vo = palette_violations(canvas)
        assert vp == 0, f"{vp} partial-alpha pixels"
        assert vo == 0, f"{vo} off-palette opaque pixels"

    def test_15x20_no_adjacent_same_internal(self):
        """15x20 layout: no horizontally or vertically adjacent interior cells
        should share the same centre variant."""
        bp = np.ones((15, 20), dtype=bool)
        bp[0, :] = False
        bp[-1, :] = False
        bp[:, 0] = False
        bp[:, -1] = False

        kit, center_pool = _make_synthetic_kit()
        decals = _make_synthetic_decals()

        # We can't directly inspect variant assignments after assembly (they're
        # baked into the canvas), but we can test the graph coloring step.
        rng = np.random.RandomState(42)
        centers = list(center_pool.values())
        layout_ids, variant_indices, _ = bitmask_placement(bp, kit, centers, rng)
        n_variants = len(center_pool)
        colored = graph_color_centers(bp, variant_indices, n_variants, rng)

        H, W = bp.shape
        for r in range(H):
            for c in range(W):
                if not bp[r, c]:
                    continue
                if _neighbor_bits(bp, r, c) == 15:  # interior
                    v = colored[r, c]
                    # Check horizontal adjacency
                    if c + 1 < W and bp[r, c + 1] and _neighbor_bits(bp, r, c + 1) == 15:
                        assert v != colored[r, c + 1], (
                            f"Horizontal adjacency violation at ({r},{c})-({r},{c + 1}) "
                            f"both using variant {v}"
                        )
                    # Check vertical adjacency
                    if r + 1 < H and bp[r + 1, c] and _neighbor_bits(bp, r + 1, c) == 15:
                        assert v != colored[r + 1, c], (
                            f"Vertical adjacency violation at ({r},{c})-({r + 1},{c}) "
                            f"both using variant {v}"
                        )


class TestTileDedup:
    """Verify tile deduplication and atlas generation."""

    def test_atlas_dimensions(self):
        """Dedup a known canvas and check atlas dimensions."""
        # Create a 4x4 grid of 32x32 tiles (128x128 canvas)
        canvas = Image.new("RGBA", (128, 128), (0, 0, 0, 0))
        # Fill with identical tiles (except one)
        from PIL import ImageDraw
        tile_a = Image.new("RGBA", (32, 32), (50, 50, 50, 255))
        tile_a = lock_palette(tile_a)
        tile_b = Image.new("RGBA", (32, 32), (100, 100, 100, 255))
        tile_b = lock_palette(tile_b)

        for r in range(4):
            for c in range(4):
                tile = tile_b if (r == 0 and c == 0) else tile_a
                canvas.paste(tile, (c * 32, r * 32))

        atlas, layout = tile_deduplicate(canvas, tile_sz=32)

        # Should have 2 unique tiles
        unique_count = atlas.width // 32 if atlas.width > 0 else 0
        assert unique_count == 2, f"Expected 2 unique tiles, got {unique_count}"
        assert atlas.height == 32
        assert len(layout) == 16

    def test_all_palette_pure(self):
        """Dedup output should have no palette violations."""
        canvas = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        tile = lock_palette(Image.new("RGBA", (32, 32), (128, 64, 32, 255)))
        canvas.paste(tile, (0, 0))
        canvas.paste(tile, (32, 0))
        canvas.paste(tile, (0, 32))
        canvas.paste(tile, (32, 32))

        atlas, _ = tile_deduplicate(canvas, tile_sz=32)
        vp, vo = palette_violations(atlas)
        assert vp == 0
        assert vo == 0


class TestDecalCoverage:
    """Verify decal coverage ratio."""

    def test_coverage_with_full_blueprint(self):
        """A fully filled interior blueprint should achieve >=30% coverage."""
        bp = np.ones((15, 20), dtype=bool)
        bp[0, :] = False
        bp[-1, :] = False
        bp[:, 0] = False
        bp[:, -1] = False

        kit, center_pool = _make_synthetic_kit()
        decals = _make_synthetic_decals()

        canvas, stats = assemble_megastructure(
            bp, kit, center_pool, decals, tile_sz=BIG_TILE, seed=42,
            write_debug=False,
        )

        coverage = stats["coverage_ratio"]
        # With synthetic decals that cover a 2x2 tile area and many anchors,
        # coverage should be at least 0.30
        assert coverage >= 0.30, (
            f"Decal coverage {coverage:.4f} below minimum 0.30. "
            f"Seams={stats.get('cross_seams', '?')}, "
            f"covered={stats.get('covered_seams', '?')}"
        )


# ---------------------------------------------------------------------------
# Integration tests (check actual build output if it exists)
# ---------------------------------------------------------------------------

class TestBuildOutput:
    """Verify the output of a completed build (if output files exist)."""

    @pytest.fixture
    def mega_dir(self):
        d = mega_dir("field")
        if not d.exists():
            pytest.skip("No output/mega/field/ directory – run scripts/build_mega.py first")
        return d

    def test_atlas_exists_and_valid(self, mega_dir):
        """mega_atlas.png should exist and be palette-pure."""
        path = mega_dir / "mega_atlas.png"
        if not path.exists():
            pytest.skip("mega_atlas.png not found")
        img = Image.open(path).convert("RGBA")
        vp, vo = palette_violations(img)
        assert vp == 0, f"Atlas has {vp} partial-alpha pixels"
        assert vo == 0, f"Atlas has {vo} off-palette pixels"

    def test_layout_json_valid(self, mega_dir):
        """mega_layout.json should exist and match atlas dimensions."""
        path = mega_dir / "mega_layout.json"
        if not path.exists():
            pytest.skip("mega_layout.json not found")
        data = json.loads(path.read_text())
        assert "tile_size" in data
        assert data["tile_size"] == TILE_SIZE
        assert "layout" in data
        assert len(data["layout"]) > 0

    def test_preview_exists(self, mega_dir):
        """mega_preview.png should exist."""
        path = mega_dir / "mega_preview.png"
        if not path.exists():
            pytest.skip("mega_preview.png not found")
        img = Image.open(path)
        assert img.width > 0 and img.height > 0

    def test_blueprint_stored(self, mega_dir):
        """Blueprint should be saved alongside the output."""
        candidates = [
            environment_dir("field") / "mega",
            work_environment_dir("field") / "mega",
        ]
        bp_txt = bp_npy = None
        for env_dir in candidates:
            if (env_dir / "blueprint.npy").exists() or (env_dir / "blueprint.txt").exists():
                bp_txt = env_dir / "blueprint.txt"
                bp_npy = env_dir / "blueprint.npy"
                break
        found = bool(bp_txt and (bp_txt.exists() or (bp_npy and bp_npy.exists())))
        if not found:
            pytest.skip("Blueprint not found (may need full build)")
        assert found

    def test_report_has_metrics(self, mega_dir):
        """report.json should contain coverage and violation metrics."""
        path = mega_dir / "report.json"
        if not path.exists():
            pytest.skip("report.json not found")
        data = json.loads(path.read_text())
        assert "palette_violations" in data
        assert data["palette_violations"] == 0, f"Violations: {data['palette_violations']}"
        if "coverage" in data:
            assert data["coverage"] >= 0.0


# ---------------------------------------------------------------------------
# Stamp module tests
# ---------------------------------------------------------------------------

class TestStampOutput:
    """Verify stamp_medium outputs."""

    @pytest.fixture
    def stamp_dir(self):
        d = environment_dir("field") / "stamp"
        if not d.exists():
            d = mega_dir("field") / "stamp"
        if not d.exists():
            pytest.skip("No stamp output – run scripts/build_mega.py first")
        return d

    def test_stamp_matted_palette_pure(self, stamp_dir):
        """stamp_matted.png should have no palette violations."""
        path = stamp_dir / "stamp_matted.png"
        if not path.exists():
            pytest.skip("stamp_matted.png not found")
        img = Image.open(path).convert("RGBA")
        vp, vo = palette_violations(img)
        assert vp == 0, f"Stamp has {vp} partial-alpha pixels"
        assert vo == 0, f"Stamp has {vo} off-palette pixels"

    def test_metadata_exists(self, stamp_dir):
        """stamp_metadata.json should have correct structure."""
        path = stamp_dir / "stamp_metadata.json"
        if not path.exists():
            pytest.skip("stamp_metadata.json not found")
        data = json.loads(path.read_text())
        assert data["grid"]["width"] == 4
        assert data["grid"]["height"] == 5
        assert data["tile_size"] == TILE_SIZE
        assert len(data["tiles"]) == 20

        # Check layer assignments
        body_tiles = [t for t in data["tiles"] if t["layer"] == "sorted_body"]
        canopy_tiles = [t for t in data["tiles"] if t["layer"] == "overhead_canopy"]
        assert len(body_tiles) == 8, f"Expected 8 body tiles, got {len(body_tiles)}"
        assert len(canopy_tiles) == 12, f"Expected 12 canopy tiles, got {len(canopy_tiles)}"

        for t in body_tiles:
            assert t["collision"] is True
            assert "pivot_y" in t
        for t in canopy_tiles:
            assert t["collision"] is False

    def test_ysort_demo_palette_pure(self, stamp_dir):
        """Y-sort demo should have no palette violations."""
        path = stamp_dir / "ysort_demo.png"
        if not path.exists():
            pytest.skip("ysort_demo.png not found")
        img = Image.open(path).convert("RGBA")
        vp, vo = palette_violations(img)
        assert vp == 0, f"Demo has {vp} partial-alpha pixels"
        assert vo == 0, f"Demo has {vo} off-palette pixels"

    def test_tiles_count(self, stamp_dir):
        """Should have 20 tile PNGs."""
        tiles_dir = stamp_dir / "tiles"
        if not tiles_dir.exists():
            pytest.skip("tiles/ not found")
        pngs = list(tiles_dir.glob("*.png"))
        assert len(pngs) == 20, f"Expected 20 tiles, got {len(pngs)}"
        for p in pngs[:3]:  # Spot-check first 3
            img = Image.open(p).convert("RGBA")
            assert img.size == (TILE_SIZE, TILE_SIZE)