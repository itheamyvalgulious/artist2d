# Ship Environment — Fix Pass v6

Scope: the ship pack only — `environment/ship_tiles.py`, `environment/ship_props_det.py`,
`environment/ship_objects.py`, `environment/ship_assembly.py`, `scripts/build_ship.py`
and the ship outputs (`output/environment/ship/`, `output/mega/ship/`,
`output/showcase/ship/`). No character file, no review packet, no `work/review/`
content was touched. `tileset.json` still holds **25 tiles**, the pack still ships
**3 medium + 3 mega** types, and the three isolation directories are unchanged.

This report does **not** claim PASS. An independent re-review should re-measure.

## Rebuild / verify

```bash
.venv/bin/python scripts/build_ship.py      # deterministic, no API key, no AI call
.venv/bin/python scripts/verify_ship_v6.py  # prints every number quoted below
```

`build_ship.py` now constructs the image client only for `--force`; a plain run
rebuilds *every* tile and deterministic prop from code, re-derives the four
AI-authored sprites from their cached base art (`sprite_src.png`), and re-composes
both the mega and the showcase. Two consecutive runs produce byte-identical
`tileset.json`, `tileset.png`, `tileset_sample.png` and `ship_mega_1x.png`
(verified by SHA-256 in `verify_ship_v6.py`).

Note: `scene_1x.png` / `scene_focus_x4.png` additionally depend on
`output/character/agent/idle/frames/frame_00.png`, which another worker was
regenerating during this pass, so their hash moves with that file — not with the
ship code. With a fixed character frame they are byte-stable too.

---

## Blockers

### B1 — Contact shadows: below the rim, dithered, boot silhouette readable — FIXED

`_shadow()` was rewritten:

* it starts at **`base_y + 1`**, so the 1-px bright walk lip at `base_y` is never written;
* it is a **4-row ordered-dither falloff** — 75 % / 50 % / 25 % / 12.5 % of the pixels,
  each row with a different phase — instead of 4 opaque rows with a 1-px comb;
* it tapers 1 px per row at both ends and is biased 1 px to the right for the top-left key light;
* it only writes over opaque scene pixels and is applied **at the end of `compose()`**, after
  the deck, the dais and the hazard pad exist;
* narrow footprints are widened to at least 60 % of the silhouette width (the agent’s two boots
  are 9 px inside a 28 px body), so the agent gets a contact pool instead of a speck.

Dark pixels per row under each object, measured in `ship_mega_1x.png` (`scene_1x.png` for the agent):

| object | before (v5, on the rim row `base_y`) | after (rows `base_y+1 … base_y+4`) |
|---|---|---|
| cargo | 44 / 29 / 19 / 11 of 60 | 45 / 29 / 14 / 6 of 61 |
| console | 71 / 47 / 31 / 18 of 102 | 72 / 47 / 23 / 11 of 97 |
| server | 41 / 27 / 18 / 10 of 55 | 41 / 27 / 13 / 6 of 56 |
| reactor | 0 / 0 / 0 / 0 (see B2) | 94 / 62 / 30 / 15 of 126 |
| agent | 11 / 6 / 14 / 2 of 28 | 15 / 10 / 5 / 2 of 40 |

Row 512 in `scene_1x.png` is now **1536 / 1536 pixels of the pure lip colour (155,155,176)**;
no shadow pixel touches it. The agent’s boots still read as two boots, separated from the
shadow by that lip line.

### B2 — Reactor shadow drawn under the deck; plinth cut by the hazard band — FIXED

* The reactor is now composed **after** the deck, and its 32-px plinth stands **on top of a
  raised hazard pad** (tiles 38–43, `y=480`), not behind it. Rows 461–479 under the reactor
  are 2242 opaque pixels in 18 colours — the full X-braced foot and its orange dashes are visible.
* Its shadow is applied in the same end-of-compose pass as every other object: 94 / 62 / 30 / 15
  dark pixels in rows 481–484 across its 126-px footprint (v5: 0 / 0 / 0 / 0).
* The dark mount frame around the reactor is now three-sided (left/top/right); the old opaque
  bottom bar that sat on the pad’s top row is gone, so the contact reads through the dither.

---

## Majors

### M1 — Right bay no longer overfull — FIXED

The two cargo stacks moved to the **left bay** (x=154..213 and x=234..293, both unflipped);
the reactor’s pad owns the whole right bay (x=1216..1407). Overlap is now **0 px**
(v5: cargo 1218–1277 against hazard 1248–1408, 29 px). The reactor is centred on its pad
(sprite 1253..1370, 37 px of pad on each side), so the pad reads as a
deliberate hazard zone rather than a band glued to a crate.

### M2 — `hazard` is a real 45° pattern that tiles both axes — FIXED

The 2-px top/bottom border was removed and the tile is **no longer passed through `seamless()`**
(that call is what mirrored the stripes). The pattern is `(x + y) % 8`, and 32 is a multiple of 8,
so column 31 continues into column 0. Proof in `verify_ship_v6.py`:

* a 2×2 repeat is **pixel-identical** to an analytic 64×64 `(x+y)%8` pattern;
* a 4×4 repeat is **pixel-identical** to the analytic 128×128 pattern;
* row *n* shifted left by one column equals row *n+1* (a continuous 1:1 diagonal).

Its edge columns are *not* identical (19.17 mean difference) — that is inherent to a diagonal
and is why the raw seam metric is the wrong test for this tile; the analytic-repeat test above
is the correct one.

### M3 — Hull rib rebuilt at 1:1 with the real base flare — FIXED

`_rib_module()` is now `cap 50 + mid 103 × 3 + a designed 39-px sleeve + the raw 50-px base
flare = 448`, all integer copies, no resampling. The flat 118×39 near-black plinth (module
y=409–447) is gone; the raw base flare, its X-bracing and its own base plate end exactly on
the floor line. The new sleeve is a vented structural section with the rib’s two outer
columns, louvers, a cyan status tick and matching 1-px joins at every module boundary
(y=50/153/256/359/398). All five ribs are now identical (the alternating mirror flip was
removed) so the light direction is consistent.

### M4 — Server rack rebuilt — FIXED

`draw_server_rack()` was rewritten from 55×105/10-colour flat bands to a **52×104, 13-colour**
cabinet with:

* a lit left side housing and a shaded right housing (depth + bevels),
* a beveled top cap (lit top edge, dark under-line), two front bays with seams,
* three banks of recessed louvers, a framed status screen, four connector blocks,
* a **solid** recessed kick plate (the old 35×4 transparent slot above a 1-px rail is gone;
  there is no transparent hole inside the chassis any more, only the gap *between* the two feet),
* 1-px and 2-px wear that survives the despeckle floor.

Light before/after is in M8.

### M5 — Window rebuilt — FIXED

The 9×1 violet bar, the 3×3 violet block and the **mullion cross** were removed. The tile is
now: dark joint outline → 3-px steel frame (lit top-left, shaded bottom-right) → 1-px recessed
bezel → glass with a vertical value gradient (palette 32 at the top to 35 near the sill),
stars, one shaded 9-px planet with a dark limb at the upper right, a **single vertical
mullion** (no horizontal bar, so no crosshair) and a lit sill + cyan spill. Glass mean
luminance is **47.4** with a 181.8 peak (v5: below 25 except a thin gradient); no violet
pixel remains (0 palette violations).

### M6 — Deck face has plate/panel/rivet density — FIXED

`deck_fill` is no longer the flattened AI quadrant; it is a deterministic plate face:
a plate joint every 32 px (dark groove + top-left bevel), a second joint row at y=16 so the
tile border lands inside the plate body, anti-slip stamps, four rivets per plate and
deliberate 2–3-px scuffs.

| metric | v5 `deck_fill` | v6 `deck_fill` | wall (`wall_flat`) |
|---|---|---|---|
| colours | 5 | 5 | 5 |
| mean adjacent-column difference | 0.90 | **4.90** | 4.12 |
| mean luminance | 29.8 | **36.4** | 36.7 |

The seamless X wrap is exact (seamX 0.00) and the Y repeat is exact too (seamY 0.00). The
1-px walk lip is owned by `deck_top` (palette 6, row 0) and is intact in the scene (row 512 =
1536/1536 lip pixels).

### M7 — Door is visible, lit on both jambs and usable — FIXED

* The door tile pair is redrawn: lit left jamb (palette 5/4), **right jamb palette 4/3
  = (78,78,99)/(54,54,70)**, both lighter than the wall base (35,35,46) — the old right jamb
  was (20,20,28). Leaves are palette 3 with inset panels, kick plates, a lintel + transom
  window in `door_top` and the hazard threshold only in `door`.
* The lower conduit run moved from row 14 to row 13, so **nothing crosses the 32×64 opening**
  (the old door sat under `pipe_h` for its whole top tile).
* It now stands at tile 31 (x=992..1023, y=448..511) in the server bay (tiles 26–33), with the
  agent in front of it, 64 px opening vs 53 px agent, clear width 26 px.
* 25-tile count unchanged.

### M8 — One light direction across all six props — FIXED

New deterministic `unify_light()` pass: the outer 7-px bands of every sprite are stepped one
shade along the pixel’s own palette ramp, +1 on the left/top and −1 on the right/bottom, with
a 4×4 ordered dither at the band edge; palette-0 outline pixels are excluded so every cutout
keeps its closed 1-px outline. The pass is applied on every build to all six sprites
(including the four cached AI ones, which are re-derived from `sprite_src.png`), so it can
never be double-applied.

Left-8 minus right-8 mean luminance (positive = lit from the left):

| sprite | v5 | v6 |
|---|---|---|
| cargo_stack | +3.0 | **+17.9** |
| console_bank | −3.1 | **+6.0** |
| reactor_core | −1.1 | **+9.2** |
| hull_frame | +0.2 | **+15.0** |
| server_rack | +5.5 (top-only) | **+34.6** |
| viewport | n/a | **+16.7** |

---

## Minors

* **Orphan `deck_top_left.png` removed** (`deck_top_left*.png` and the stale
  `wall_plain*.png` are now deleted by `build_tileset()`, so the folder is exactly the
  25-tile atlas: 25 base PNGs on disk == 25 keys in `tileset.json`).
* **L/R caps are real mirrors**: `deck_right` is the exact pixel mirror of `deck_left`
  (`flip_equal True`) and `deck_step_right` of `deck_step_left`; previously they were
  independent noise variants.
* **Dais step geometry**: the step tile is no longer a framed panel with a checkerboard vent
  band. It now has a 4-px tread, a 1-px overhang shadow, a horizontal riser (two tone bands,
  rivets, one cyan equipment label) and a grip strip + base; stacked as
  `left + step ×4 + right` it reads as a raised platform, not as a row of lockers.
* **Wall cluster / bottom frame**: the ad-hoc clusters were replaced by real bays — the clear
  spans between the ribs are framed by a `wall` cornice row (y=3), a `wall` skirting row
  (y=12) and accent columns at both bay edges (`wall_flat_light` left, `wall_flat_violet`
  right, whose strips already sit 9–10 px inside the tile edge), so every bay has a top and
  a bottom frame and the accents line up.
* **Server base slot**: see M4 — the base is an opaque kick plate; only the gap between the
  feet is transparent.
* **Showcase framing**: new `output/showcase/ship/scene_focus_x4.png` (4× crop of the
  server / agent / door / grate) so the agent’s 53 px scale against the 64 px door can be
  read without hunting the 1536-px room. The 2× `scene.png` is unchanged in kind.
* **Metadata**: `medium_generated_count` / `mega_generated_count` + `*_catalog_total` replace
  the misleading `medium_catalog_size: 10`; `ship_layout.json` now records the real door,
  hazard pad, cargo, server and agent coordinates.

---

## Verification summary

* 25 tiles in `tileset.json`, 25 base PNGs on disk, no orphan; 3 medium + 3 mega sprites.
* The agent appears exactly once: `scene_1x.png` vs `ship_mega_1x.png` differ in a single
  cluster, bbox (952, 459)–(979, 516), 499 px (body + its contact shadow).
* `palette_violations == (0, 0)` for the atlas, the sample, the mega, the scene and the focus
  crop; every sprite alpha is exactly {0, 255}; no magenta anywhere.
* Seam difference 0.00/0.00 for every repeating fill: `ceiling`, `deck_fill`, `grate_fill`,
  `grate_top`, `pipe_h`, `pipe_v`, `wall`, `wall_flat`, `wall_flat_light`, `wall_flat_violet`,
  `wall_light`, `wall_violet`; `deck_top` / `deck_step` are 0.00 on X (they are used as a
  single row) and intentionally differ on Y (lip / tread against base).
  The remaining non-zero tiles are one-off features or caps: `deck_left/right`,
  `deck_top_right`, `deck_step_left/right` (the lit cap edge), `door`/`door_top` (a 2-tile
  stack: transom vs threshold), `vent`, `window`, `light_strip`, and `hazard` (proved by the
  analytic repeat above).

## Remaining issues / risks

1. **`hazard` fails the literal “seam difference 0” test** (19.17 on both axes). A 45°
   diagonal cannot have identical edge columns; the correct test (2×2 and 4×4 repeats equal to
   the analytic pattern) passes. If the next review insists on the numeric test, the tile
   should be re-specified as a chevron pair instead.
2. **`deck_top_left` is gone, so the top-corner set is still right-only** (`deck_top_right`
   exists, no left twin). Adding it would require dropping another tile to stay at 25; the
   v5 report offered removal as an acceptable resolution and the three cap tiles
   (`deck_left/right`, `deck_top_right`) are kit-only — they are not placed in the scene.
3. **The five ribs are now identical** (the alternate flip was removed to keep the light
   consistent). Repetition is more visible than before; the new 39-px service sleeve breaks
   the vertical rhythm but does not remove it.
4. **The console’s AI art is untouched** beyond the light pass. Its centre screen is a
   bright cyan schematic — re-inspected at 12× it is a readable display, not a flat blown-out
   field; a CRT-scanline pass was tried and reverted because it banded the screens. If the
   next review still reads it as blown out, the fix belongs in a re-generation, not a filter.
5. **The viewport glass is still dark** (v5 minor 12). It was outside this fix list and the
   cached AI art was left alone.
6. **`sprite_src.png` is a new shipped file** in the four AI-authored sprite folders. It is
   the cached base art the build re-derives `sprite.png` from, which is what keeps
   `build_ship.py` AI-free and byte-reproducible; it is palette-locked and 0/255 alpha like
   every other asset.
7. **Composition is still a flat side view** — no foreground/parallax layer (v5 minor 13).
8. **The review packet `00`–`06` was not rebuilt** (out of scope, as agreed), so the packet
   still shows the v5 framing until it is regenerated.
