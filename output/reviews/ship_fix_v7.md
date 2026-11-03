# Ship Environment — Fix Pass v7

Scope: the ship pack only — `environment/ship_tiles.py`, `environment/ship_assembly.py`,
`scripts/build_ship.py`, and the ship outputs (`output/environment/ship/`,
`output/mega/ship/`, `output/showcase/ship/`). No character file was modified and
`work/review/` was not written. `tileset.json` still holds **25 tiles**, the pack
still ships **3 medium + 3 mega** types, and the three isolation directories are
unchanged.

This report does **not** claim PASS.

## Rebuild / verify

```bash
.venv/bin/python scripts/build_ship.py      # deterministic, no API key, no AI call
.venv/bin/python scripts/verify_ship_v7.py  # prints every number quoted below
```

Two consecutive builds are byte-identical for `tileset.json`, `tileset.png`,
`tileset_sample.png` and `ship_mega_1x.png`, and `scene_1x.png` is now **0 px
different** from a fresh `compose(include_character=True)` against the character
frame on disk (v6 minor 4).

---

## B1 (blocker) — real contact footprints, below every lip and tread — FIXED

`_shadow()` still exists (same entry point the previous reviews patched) but the
fixed-rectangle row loop is gone. The pass is three pieces:

1. **`_contact_depths(sprite, height)`** — the footprint comes from the sprite’s
   base *silhouette*, not a fixed rectangle: every column that reaches the
   bottom 4 rows is a contact column, the mask is dilated 1 px, 1-px gaps are
   closed, and a column whose lowest opaque pixel sits 1–3 px above the base
   gets a proportionally shallower shadow (rounded feet/chamfers taper).
2. **`_shadow()`** — row 0 is a **solid palette-0 core** across the whole
   footprint (the reactor gets 2 solid rows), then an ordered dither falloff at
   **5/8, 3/8, 1/8** with a different 8-px phase per row. No 1-px dash, no
   checker strip.
3. **Height scales with the sprite** — 3 rows for the small props (cargo,
   console, server, agent), 5 rows for the 140-px reactor.

The start row is the landing surface’s lip height, never above it:

| surface | lit edge | shadow starts |
|---|---|---|
| deck (`deck_top`) | rows 512–513 (L 156.5 / 79.5) | row 514 |
| dais (`deck_step`) | rows 480–483 (L 156.5 / 112.8 / 112.8 / 79.5) | row 484 |
| reactor pad | rows 480–482 tread (L 156.5 / 112.8 / 112.8), row 483 overhang | row 484 |

To make the core land on a readable surface the two surface tiles lost their
1-px near-black under-lip row (deck_top row 2 and deck_step row 4 are now plate
body, L 36.1 / 35.8 instead of 20.6); the lip and tread themselves are untouched.

Measured from the shipped scene minus a no-shadow compose (the reviewer’s own
method), dark px per row over the footprint:

| object | v6 (dashed) | v7 (core + falloff) |
|---|---|---|
| cargo ×2 | 46 / 29 / 14 / 6 | **58 / 36 / 21** (100 % / 62 % / 36 %) |
| console | 73 / 47 / 23 / 11 | **94 / 58 / 35** |
| server | 42 / 27 / 13 / 6 | **52 / 28 / 17** |
| agent | 16 / 10 / 5 / 2 of 20 | **18 / 10 / 3** |
| reactor | 95 / 62 / 30 / 15 | **117 / 117 / 73 / 44 / 14** |

Rows 512 and 513 (deck lip) and rows 480–483 (dais and pad tread) are **changed
by 0 px**. The whole shadow set is 1267 px, bounds x=144–1407, y=484–516.

## M1 — the left bay is no longer a copy-paste pair — FIXED

* full 3-crate stack at x=143 (y=425–511),
* a **shorter 2-crate stack** at x=245 (y=451–511), **mirrored**, cut from the
  same deterministic sprite at row 26 (the shared outline between the top and
  middle crate, so the silhouette stays closed),
* 43 px gap between the stacks (v6: 21 px), 102 px centre-to-centre,
* 0 px overlap with the reactor pad.

The 2-crate variant is derived in `compose()` by `_cargo_low()`; `cargo_stack`
is still one medium type with one shipped `sprite.png`.

## M2 — the reactor stands on a real platform — FIXED

The 32-px hazard band is now a 1-tile platform (`_pad_tread()`):

* **tread on top**: rows 480–482 are a lit 3-px tread (156.5 / 112.8 / 112.8),
  row 483 is the slab’s overhang shadow — the reactor’s base row (479, outline
  8,8,12) meets the tread, not a stripe;
* **hazard on the side face only**: rows 484–511 carry the 45° stripes;
* **side thickness**: 3-px chamfered end caps at both ends — left = outline
  (8,8,12) + lit edge (111,111,136) + face; right = face (54,54,70) + shaded
  edge + outline;
* **cast shadow on the deck**: the pad itself is a contact object, so its own
  footprint gets a solid core + falloff at rows 514–516 (192 / 120 / 72 px of
  its 192-px width);
* the reactor’s own shadow now starts at row 484 on the hazard face (5 rows),
  so the tread above it stays intact.

## Minors

* **(a) `04` hull clipping** — `scripts/build_review_packets.py::_catalog()` now
  grows the cell to the tallest scaled sprite: the 3× hull (354×609) gets a
  633-px cell, so the top flange and the base plate are inside the sheet
  (verified by rendering `_catalog` to a temp path: output 1560×633). This is
  the only change to a review script; `work/review/` itself was not rebuilt
  here.
* **(b) tiles folder** — the shipped `output/environment/ship/tiles/` now holds
  **exactly the 25 atlas keys** (was 29 × 32-px PNGs). The four
  `*_seamless.png` + `conduit_*` artifacts were *not deleted from history*: the
  material previews are now written to `work/environment/ship/tiles/` and every
  stale `*.png` whose stem is not an atlas key is removed at build time.
  `REPORT.md` no longer calls `conduit` a shipped tile (it is a material-board
  quadrant that informs the pipe family).
* **(c) layout wording** — `ship_layout.json` now measures the agent’s opaque
  body from the current `frame_00.png` at build time and states that she stands
  **to the left of the door, facing right toward it**; “in front of the door” is
  gone.  With the frame in the tree during this pass that is body x=950–981,
  i.e. 10 px left of the door (x=992–1023); the number follows the character
  frame, the wording stays correct.
* **(d) showcase reproducibility** — the shipped `scene_1x.png` is rebuilt from
  the current `output/character/agent/idle/frames/frame_00.png`; a fresh
  compose now differs by **0 px** (v6: 435 px).

Two extra fixes from the v6 minor list:

* the vertical conduit runs moved 1 tile left (x=8/20/32 instead of 9/21/33) so
  the bays’ right-edge violet accents are no longer buried under the pipes —
  all four bays now measure 180 cyan px (left) and 180 violet px (right);
* `deck_step`’s per-tile cyan label was replaced by a quiet recessed vent slot,
  so the 6-tile dais no longer repeats six identical labels.

---

## Verification summary

* 25 atlas keys == 25 PNGs in `tiles/`, no extras; 3 medium + 3 mega sprites.
* `palette_violations == (0, 0)` for the atlas, the sample, the mega, the scene
  and the focus crop; every sprite alpha is exactly {0, 255}.
* The agent appears exactly once: `scene_1x.png` vs `ship_mega_1x.png` differ
  only on the agent (body + blade tip + contact shadow), bbox
  (950, 459)–(981, 516), 631 px; no other pixel differs.
* Shadow rows never touch a lip or tread row (measured 0 px changed on rows
  480–483 and 512–513).
* Every repeating fill still measures seam 0.00/0.00 (unchanged from v6:
  `ceiling`, `deck_fill`, `grate_fill/top`, `pipe_h/v`, `wall*`); `deck_top` and
  `deck_step` remain 0.00 on X and one-shot on Y.

## Remaining issues / risks

1. **The pad spans the full 6-tile bay (192 px)** against a 118-px reactor; it
   now has tread, ends and a shadow, but it is still a wide platform rather
   than a tight one.
2. **`deck_top` / `deck_step` changed byte-wise** (row 2 / row 4 are plate body
   now). The lip and tread are intact, but the 1-px dark gap that used to sit
   under them is gone; the contrast is now 156→79→36 and 156→113→113→80→36.
3. **The pad’s overhang row (483) is black across the whole pad** — a slab
   detail, not a shadow, but it is a full-width dark line.
4. **The five ribs are still identical** (v6 minor 6) and the 6-tile dais still
   repeats one tile (v6 minor 7, now without the loud label).
5. **The door’s clear opening is 60 px** (rows 452–511), so the 104-px server
   and 87-px cargo still could not pass it; the 53-px agent fits (v6 minor 9).
6. **The viewport glass is still dark** (v6 minor 8) — untouched cached AI art.
7. **`unify_light` is still a rim pass**: outer-7-px L−R is positive on all six
   (cargo +21.0, console +9.4, reactor +10.5, hull +16.9, server +38.9,
   viewport +18.8) and the left/right thirds are positive but small on the
   symmetric-by-design reactor/hull/viewport (+1.9 / +3.0 / +1.5).
8. **`04_mega_catalog_x3.png` in `work/review/` is still the v6 sheet** until
   the packet is rebuilt; the builder fix only takes effect on that rebuild.
9. **The 2-crate cargo variant is a crop** (`row 26`) of the shipped sprite, not
   a separate shipped file; it is documented in `ship_layout.json` and in
   `_cargo_low()`.
