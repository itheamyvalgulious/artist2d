"""Height-modulated 47-tile autotile synthesiser (PLAN 2.3).

Given two seamless base tiles (e.g. grass over dirt), generates the full
47-tile set of organic transition tiles using a height-field-modulated
distance-field cutout.  A 1px junction shadow is baked along every boundary.
"""
from __future__ import annotations

import json
import numpy as np
from PIL import Image
from scipy import ndimage

from config.pipeline_config import TILE_SIZE
from core.palette_quantizer import (
    PALETTE_RGB,
    nearest_palette_indices,
    shade_rgb,
    lock_palette,
    palette_violations,
)

# ---------------------------------------------------------------------------
# 47-state enumeration
# ---------------------------------------------------------------------------
# cardinal mask: bit 0=N, 1=E, 2=S, 3=W  (1 = upper material)
# A diagonal is "active" only when both adjacent cardinal bits are 1.
# The total valid (cardinal, diag_subset) pairs is exactly 47.


def _active_diagonals(cardinal: int) -> list[int]:
    """Return which diagonal bits (0=NE 1=SE 2=SW 3=NW) are active for a cardinal mask."""
    n = (cardinal >> 0) & 1
    e = (cardinal >> 1) & 1
    s = (cardinal >> 2) & 1
    w = (cardinal >> 3) & 1
    active = []
    if n and e:
        active.append(0)  # NE
    if s and e:
        active.append(1)  # SE
    if s and w:
        active.append(2)  # SW
    if n and w:
        active.append(3)  # NW
    return active


def enumerate_47() -> list[tuple[int, int]]:
    """Return the 47 (cardinal_mask, diag_mask) pairs."""
    states: list[tuple[int, int]] = []
    for cm in range(16):
        active = _active_diagonals(cm)
        k = len(active)
        for bits in range(1 << k):
            dm = 0
            for i, diag_bit in enumerate(active):
                if (bits >> i) & 1:
                    dm |= 1 << diag_bit
            states.append((cm, dm))
    assert len(states) == 47, f"expected 47 states, got {len(states)}"
    return states


ALL_STATES = enumerate_47()
STATE_TO_INDEX: dict[tuple[int, int], int] = {s: i for i, s in enumerate(ALL_STATES)}


# ---------------------------------------------------------------------------
# Height field extraction (PLAN 2.3 step 1)
# ---------------------------------------------------------------------------

def extract_height_field(tile: Image.Image) -> np.ndarray:
    """Height field H ∈ [0,1]: luminance + distance to bright-cluster centres.

    Terrain tiles are fully opaque, so connected components are built from the
    *highlight* mask (luminance above the tile median), not from alpha.  That is
    what makes the boundary follow grass tufts and stone slabs instead of a
    radial gradient.
    """
    arr = np.array(tile.convert("RGBA")).astype(np.float64)
    rgb = arr[..., :3]
    lum = 0.299 * rgb[..., 0] + 0.587 * rgb[..., 1] + 0.114 * rgb[..., 2]
    lo, hi = float(lum.min()), float(lum.max())
    lum_n = (lum - lo) / max(hi - lo, 1.0)

    opaque = arr[..., 3] > 128
    thr = np.percentile(lum[opaque], 58) if opaque.any() else lum.mean()
    fg = opaque & (lum > thr)
    labels, n = ndimage.label(fg)
    dist = np.zeros_like(lum_n)
    for lbl in range(1, n + 1):
        mask = labels == lbl
        if mask.sum() < 2:
            dist[mask] = 0.5
            continue
        ys, xs = np.nonzero(mask)
        cy, cx = ys.mean(), xs.mean()
        d = np.sqrt((ys - cy) ** 2 + (xs - cx) ** 2)
        dmax = float(d.max()) or 1.0
        dist[ys, xs] = 1.0 - d / dmax
    h = 0.55 * lum_n + 0.45 * dist
    h[~opaque] = 0.0
    return h


# ---------------------------------------------------------------------------
# Distance field per state (PLAN 2.3 step 2)
# ---------------------------------------------------------------------------

def _build_distance_field(size: int, cardinal: int, diag: int) -> np.ndarray:
    """Dual-grid bilinear blob field for one of the 47 neighbour states.

    The upper/lower state of the 3x3 neighbourhood is sampled at the tile
    centres (32 px apart) and bilinearly interpolated over the tile.  Shared
    edges sample exactly the same two cells on both sides, so neighbouring
    tiles are continuous by construction, and connected edges are full-width
    bands rather than 1 px lines.
    """
    s = float(size)
    yy, xx = np.mgrid[0:size, 0:size].astype(np.float64)

    n = (cardinal >> 0) & 1
    e = (cardinal >> 1) & 1
    s_ = (cardinal >> 2) & 1
    w = (cardinal >> 3) & 1
    ne = (diag >> 0) & 1
    se = (diag >> 1) & 1
    sw = (diag >> 2) & 1
    nw = (diag >> 3) & 1

    # rows: y (top = north), cols: x (left = west)
    st = np.array([
        [nw, n, ne],
        [w, 1, e],
        [sw, s_, se],
    ], dtype=np.float64)

    u = (xx + s / 2.0) / s          # 0.5 at the west edge, 1.5 at the east edge
    v = (yy + s / 2.0) / s
    i0 = np.floor(u).astype(np.int32)
    j0 = np.floor(v).astype(np.int32)
    fx = u - i0
    fy = v - j0
    i0 = np.clip(i0, 0, 1)
    j0 = np.clip(j0, 0, 1)
    i1 = i0 + 1
    j1 = j0 + 1

    val = (st[j0, i0] * (1 - fx) * (1 - fy) + st[j0, i1] * fx * (1 - fy) +
           st[j1, i0] * (1 - fx) * fy + st[j1, i1] * fx * fy)

    # Map a soft field to the [0,1] decision surface.
    return np.clip(val, 0.0, 1.0)


# ---------------------------------------------------------------------------
# Single tile synthesis (PLAN 2.3 step 3-4)
# ---------------------------------------------------------------------------

def _synthesize_one(
    top: np.ndarray, bottom: np.ndarray,
    height: np.ndarray, cardinal: int, diag: int,
    size: int = TILE_SIZE, bake_shadow: bool = True, pin_inset: int = 1,
    smooth_mask: bool = False, notch_r: float | None = None,
    concave_notch: bool = True, diag_marker: bool = False,
) -> np.ndarray:
    """Produce one 32×32 RGBA transition tile."""
    wf = _build_distance_field(size, cardinal, diag)
    # Low-frequency, wrap-around height modulation turns the straight band
    # boundary into an organic edge (single-pixel height noise only jitters).
    smooth_h = ndimage.gaussian_filter(height, sigma=2.2, mode="wrap")
    # PLAN 2.3: S = W_mask + 0.35 * (H_A - 0.5)
    S = wf + 0.35 * (smooth_h - 0.5)

    out = np.zeros((size, size, 4), dtype=np.uint8)
    upper = S > 0.5
    # Diagonal corners: a missing diagonal cuts a concave notch at the tile
    # corner even when the bilinear field is above the threshold there, so all
    # 47 states are distinct.
    n = (cardinal >> 0) & 1
    e = (cardinal >> 1) & 1
    s_ = (cardinal >> 2) & 1
    w = (cardinal >> 3) & 1
    ne = (diag >> 0) & 1
    se = (diag >> 1) & 1
    sw = (diag >> 2) & 1
    nw = (diag >> 3) & 1
    # Pin the connected edges BEFORE the diagonal notches: the pin keeps the
    # edge band full-width, and the notch is then allowed to cut the concave
    # corner.  Doing it the other way round leaves an extra upper-material
    # triangle at every tile corner.
    # Keep the connected edge full-width in its middle, but do not paint the
    # 1 px corner where the perpendicular neighbour is lower: that single
    # pixel was the extra dirt triangle at every grass corner.
    inset = pin_inset
    if n:
        upper[0, (0 if w else inset):(size if e else size - inset)] = True
    if e:
        upper[(0 if n else inset):(size if s_ else size - inset), -1] = True
    if s_:
        upper[-1, (0 if w else inset):(size if e else size - inset)] = True
    if w:
        upper[(0 if n else inset):(size if s_ else size - inset), 0] = True
    yy, xx = np.mgrid[0:size, 0:size].astype(np.float64)
    r = (size / 3.0 * 0.72) if notch_r is None else float(notch_r)
    def _notch(cx: float, cy: float) -> None:
        nonlocal upper
        d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
        upper &= d >= r
    # A concave corner is the 3-top / 1-bottom 2x2 case.  Notching the top
    # there leaves a land triangle inside the water (apex on land, base in
    # water).  Water sets concave_notch=False; convex corners still use the
    # normal diagonal field.
    if concave_notch:
        if n and e and not ne:
            _notch(size - 1, 0)
        if s_ and e and not se:
            _notch(size - 1, size - 1)
        if s_ and w and not sw:
            _notch(0, size - 1)
        if n and w and not nw:
            _notch(0, 0)
    if smooth_mask:
        # Fill 1 px dirt spikes / pinholes at the water boundary so the bank
        # corners do not leave small triangles inside the water.
        upper = ndimage.binary_closing(upper, structure=np.ones((3, 3), bool),
                                       border_value=1)
    lower = ~upper

    out[upper, :3] = top[upper, :3]
    out[upper, 3] = top[upper, 3]
    out[lower, :3] = bottom[lower, :3]
    out[lower, 3] = bottom[lower, 3]

    if diag_marker:
        # Keep the 47 diagonal states distinguishable without putting a land
        # triangle back into the water: a 1 px WATER highlight in the concave
        # corner.  The geometry stays square; only one water pixel differs.
        top_rgb = top[..., :3].reshape(-1, 3)
        top_rgb = top_rgb[top[..., 3].reshape(-1) > 0]
        if top_rgb.size:
            lum = top_rgb @ np.array([0.2126, 0.7152, 0.0722])
            hi = top_rgb[int(np.argmax(lum))]
        else:
            hi = np.array([53, 162, 196], dtype=top.dtype)
        concave = [
            (size - 1, 0, bool(n and e and not ne)),
            (size - 1, size - 1, bool(s_ and e and not se)),
            (0, size - 1, bool(s_ and w and not sw)),
            (0, 0, bool(n and w and not nw)),
        ]
        for cy, cx, flag in concave:
            if flag:
                upper[cy, cx] = True
                out[cy, cx, :3] = hi
                out[cy, cx, 3] = 255

    # 1px junction shadow (PLAN 2.3 step 4):
    # pixels that are lower but have an upper pixel directly above them
    shadow_mask = lower.copy()
    shadow_mask[0, :] = False  # top row can't have above
    # shift upper mask down by 1
    above_is_upper = np.zeros_like(upper)
    above_is_upper[1:, :] = upper[:-1, :]
    shadow = shadow_mask & above_is_upper

    if bake_shadow and shadow.any():
        shadow_rgb = out[shadow, :3].astype(np.float64).reshape(-1, 3)
        dark = shade_rgb(shadow_rgb, -1)
        out[shadow, :3] = dark.reshape(-1, 3)

    return out


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def synthesize_47(
    top_material: Image.Image,
    bottom_material: Image.Image,
    size: int = TILE_SIZE,
    bake_shadow: bool = True,
    pin_inset: int = 1,
    smooth_mask: bool = False,
    notch_r: float | None = None,
    concave_notch: bool = True,
    diag_marker: bool = False,
) -> tuple[Image.Image, dict]:
    """Generate the full 47-tile autotile atlas.

    Parameters
    ----------
    top_material:
        32×32 RGBA palette-locked upper-layer tile (e.g. grass).
    bottom_material:
        32×32 RGBA palette-locked lower-layer tile (e.g. dirt).
    size:
        Tile size (default 32).

    Returns
    -------
    (atlas, metadata)
        ``atlas`` is an 8×6 grid image (256×192); ``metadata`` is a dict
        with key ``"map"`` mapping state string ``"cardinal:diag"`` → sheet
        column-major index and ``"violations"`` palette purity check.
    """
    top_arr = np.array(top_material.convert("RGBA"))
    bot_arr = np.array(bottom_material.convert("RGBA"))
    height = extract_height_field(top_material)

    tiles_rgba = []
    cols = 8
    for cm, dm in ALL_STATES:
        tile = _synthesize_one(
            top_arr, bot_arr, height, cm, dm, size,
            bake_shadow=bake_shadow, pin_inset=pin_inset,
            smooth_mask=smooth_mask, notch_r=notch_r,
            concave_notch=concave_notch, diag_marker=diag_marker)
        tiles_rgba.append(tile)

    # Build atlas: 8 columns × 6 rows (47 tiles fit in 48 cells, last empty)
    rows = 6
    atlas = np.zeros((size * rows, size * cols, 4), dtype=np.uint8)
    for i, tile in enumerate(tiles_rgba):
        r, c = divmod(i, cols)
        y0, y1 = r * size, (r + 1) * size
        x0, x1 = c * size, (c + 1) * size
        atlas[y0:y1, x0:x1] = tile
    # Fill the last (48th) empty cell with the bottom material so the atlas
    # has no transparent gaps / magenta bleed-through in previews.
    last_r, last_c = divmod(len(tiles_rgba), cols)
    if last_r < rows:
        atlas[last_r * size:(last_r + 1) * size,
              last_c * size:(last_c + 1) * size] = bot_arr

    atlas_img = Image.fromarray(atlas, "RGBA")
    atlas_img = lock_palette(atlas_img)

    # Metadata
    state_map = {f"{cm}:{dm}": i for i, (cm, dm) in enumerate(ALL_STATES)}
    metadata = {
        "tile_count": len(tiles_rgba),
        "atlas_layout": {"cols": cols, "rows": rows, "tile_size": size},
        "map": state_map,
        "violations": palette_violations(atlas_img),
    }
    return atlas_img, metadata


def autotile_index_for_neighbors(north: bool, east: bool, south: bool, west: bool,
                                 ne: bool = False, se: bool = False,
                                 sw: bool = False, nw: bool = False) -> int:
    """Convenience: map 8-neighbour booleans (True = upper) to autotile atlas index."""
    cm = (int(north) << 0) | (int(east) << 1) | (int(south) << 2) | (int(west) << 3)
    dm = (int(ne) << 0) | (int(se) << 1) | (int(sw) << 2) | (int(nw) << 3)
    # Mask diagonal to only active bits
    active = _active_diagonals(cm)
    dm = dm & sum(1 << a for a in active)
    return STATE_TO_INDEX.get((cm, dm), 0)