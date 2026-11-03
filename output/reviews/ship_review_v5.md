# Ship interior — independent art review v5

Reviewer: independent multimodal reviewer (round 5). I did not generate, modify or regenerate any asset, ran no
project test, and changed nothing except writing this file. Everything below is read + pixel measurement of the
shipped files.

Coordinate convention: native **1x** in `mega/ship/ship_mega_1x.png` (1536 x 640, 32 px tiles, floor row 16 →
walk line **y = 512**). `05`/`06` are byte-exact 2x nearest-neighbour upscales of the 1x scene
(`np.array_equal` == True), `00` is a byte-exact 8x of `tileset.png` (all 25 filled cells diff 0), `01` is a
byte-exact 4x of `tileset_sample.png`. `02`/`03`/`04` are **not** integer upscales, so every pixel claim below
was measured on the native files.

What changed since round 4 (mtimes): only `props/cargo_stack/sprite.png` (23:08), `ship_mega_1x.png` (23:08),
`showcase/scene_1x.png` (23:08) and the re-emitted sheets `02`–`06` (23:08). Tiles (22:32), the other five
sprites (22:30) and the composites' geometry are untouched — the round-4 pass items are therefore re-tested
here rather than assumed.

---

## 1. File coverage (100 % of the packet)

Every PNG in `work/review/ship/` was opened with the image reader at full frame, then cross-checked against the
natives listed at the end of this section. Nothing was sampled.

| # | File | What was verified | Verdict |
|---|---|---|---|
| 1 | `00_tileset_x8.png` (2048x1024) | 8x atlas over `tileset.png` (256x128 = 8x4 cells): **all 25 filled cells byte-identical (diff 0)**, remaining 7 cells flat-filled; all 25 tiles 32x32, fully opaque (alpha 255 everywhere), 4–10 colours each; labels/order match `tileset.json` | **PASS** |
| 2 | `01_tileset_sample_x4.png` (2304x1152) | exact 4x of `tileset_sample.png` (576x288 = 18x9); every cell resolves to a shipped tile: 2 ceiling rows, wall band, 4 cyan/violet light-strip columns, window, vent, grate (cols 7–8), deck_step dais (cols 11–13), deck_top row 6, deck_fill rows 7–8, hazard at row 7 cols 14–15 | **PASS** (minor 7) |
| 3 | `02_all_tiles_x5.png` (1320x1100) | complete 6x5 atlas, 25 labels legible and in `tileset.json` order, hazard slot shows the 8 px tape (gold row counts 63/63/63/63/… at sheet scale, 2 colours only), no clipping | **PASS** (minor 8, 9) |
| 4 | `03_medium_catalog_x3.png` (1560x520) | `console_bank`, `cargo_stack`, `server_rack` complete and labelled; **cargo hazard band now reads as 45° gold/black tape** (gold bbox x 655–914, y 454–488; per-row gold counts 134/123/105/92/91/102 = 5.8x the sprite's 23/21/18/16/16/18 → the sheet carries the new band, not the old squiggle) | **PASS** |
| 5 | `04_mega_catalog_x3.png` (1560x520) | `hull_frame`, `viewport`, `reactor_core` complete, labelled, bboxes tight (pad 0), no floating fragments | **PASS** (minor 5, 6) |
| 6 | `05_whole_ship_x2.png` (3072x1280) | whole assembly: 5 ribs, 4 bays, viewport, console on dais, rack, both cargo stacks, reactor on the 4-tile hazard platform, ceiling lights, deck at 512 | **PASS** (minor 1, 2, 3, 4) |
| 7 | `06_showcase_x2.png` (3072x1280) | assembly + 2 agent frames (idle f00 left, shoot2 f02 mirrored right), no prop/character overlap, 36-colour palette, no text | **PASS** (minor 10) |

Native files opened and measured (no sampling): all 25 `environment/ship/tiles/*.png` (size, alpha min/max,
colour census, per-row dumps for `hazard`, `grate_top`, `grate_fill`, `pipe_h`, `pipe_v`, `deck_top`,
`ceiling`, `wall_flat_light`); `tileset.png`, `tileset_sample.png`, `tileset.json`; all three prop sprites;
all three `mega/ship/elements/*/sprite.png`; `mega/ship/ship_mega_1x.png`, `showcase/ship/scene_1x.png`
(colour census, 32-px grid classification of all 48x20 cells, run-length dumps of the cargo bays, the hazard
platform edges, the deck lip, the rib columns and the contact shadows).

---

## 2. Round-4 major

| ID | Round-4 requirement | Status | Exact evidence |
|---|---|---|---|
| **MJ-1** | `cargo_stack` must carry a real hazard band: **45°, 8 px period, gold/black, clipped to the crate face, drawn under the straps, 1 px dark inset**, matching `hazard.png` | **FIXED** | `props/cargo_stack/sprite.png` (59x87): gold `(112,75,12)` = 112 px, **all** of them inside rows **77–82** and **all** satisfying `(x+y) mod 8 ∈ {0,5,6,7}` (histogram 30/27/27/28) → exact 45°, period exactly **8**, 4 px gold / 4 px black `(20,20,28)`. Band rect **x 8–52 (45 px), y 77–82 (6 px)**. Dark inset `(8,8,12)`: column x 7, column x 53, row 76, row 83. Crate face is x 6–53, so the band is inset 2 px and the corner rim highlights (x 3–5 / 54–56 `(78,78,99)`) are **untouched** — the old "gold over the rim" is gone. Straps are redrawn on top: at y 80 the stripe model puts gold at x 13,14 and at x 46,47,48, but those pixels are `(20,20,28)` = strap columns 12–14 / 46–48 → **the straps cross the tape**. No leftover squiggle: zero gold pixels outside the band rect. Language matches `hazard.png` exactly — same gold `(112,75,12)`, same black `(20,20,28)`, same 45° orientation, same 8 px pitch, same 4 px stripe width (phase 3 px apart, which no requirement asks to match). In-scene: gold appears **only** at x 170–214 / y 502–507 (left crate), x 1224–1268 / y 502–507 (right, mirrored) and x 1275–1405 / y 480–511 (reactor platform); crate bottom row 511 on walk line 512. Visible in `03` (above), `05` (bottom-left bay) and `06` (left bay) |

---

## 3. Round-4 pass items re-verified this round

| Item | Result |
|---|---|
| `hazard.png` period 8, seamless platform | 32x32, rows 0–1 `(78,78,99)` lip, rows 2–29 stripes, rows 30–31 `(8,8,12)` base; gold = `(x+y) mod 8 ∈ {0,1,2,3}`, 448 px, 4 stripes/row. Platform = cells x 1280/1312/1344 byte-identical to the tile (**diff 0**), x 1376 diff 8670 = rib-foot overlap only; lip continuous 1275–1404. **No seam** |
| Pipes terminate in flanges/junctions | `pipe_h`: end collar `(20,20,28)`+`(54,54,70)` at x 1–2 with light rail x 0, inline junction stubs at x 15–16 / 31; `pipe_v`: junction bands rows 6–7 and 22–23 with cyan/violet lamps. In scene the vertical run x 288–320 lands on a horizontal junction at y 448 (no open-wall dead end) |
| Grate is a horizontal-bar floor grate | `grate_top` rows 4/8/12/16/20/24/28 = 1 px `(155,155,176)` + 1 px `(78,78,99)`, 2 px black between, two 2-px posts at x 7–8 / 24–25, 2-px light lip rows 0–1; `grate_fill` same field, period 4 → wraps vertically exactly (32/4). In scene x 256–320, y 512–543, flush with the deck lip |
| Deck top-registered at y = 512 | `deck_top` row 0 is the bright `(155,155,176)` line; scene row 512 is `(155,155,176)` across the full 1536 px with only 190 non-light px = the two crate contact shadows. Registration exact |
| Ribs single ceiling-to-floor | 5 ribs; each is one continuous column from the ceiling (y 64) to the deck (511): 32-px X-brace modules, twin conduits, side plates, feet flaring on the last 12 rows. No break, no doubled rib |
| Wall strips continuous | `wall_flat_light` cyan at tile x 9 (30 of 32 rows, break rows 7/23); in scene at x 169/489/873/1257 with 311–364 cyan px over the strip run → **segmented** by the tile's own panel seam, see minor 4 (pre-existing, unchanged) |
| Server solid | `server_rack` 55x105, alpha 255 on every pixel (no holes), placed at (900,407) with **diff 0** against the scene, bottom 511 |
| Wall variance | 624 blocks in the wall band → **126 distinct**, most common 107 blocks = **17.1 %** (threshold ≤ 30 %) |
| Sprites trimmed to alpha bbox | 6/6: `cargo_stack` 59x87, `console_bank` 102x59, `server_rack` 55x105, `hull_frame` 118x203, `reactor_core` 118x137, `viewport` 112x88 — all bbox == full canvas (pad 0 on all four sides) |
| All sprites single connected component | 6/6 = 1 component, 0 semi-transparent pixels in every asset |
| Palette purity / no AA / no magenta | `05` = 33 colours, `06` = 36, `tileset` = 16, individual tiles 4–10; alpha strictly 0/255 everywhere; zero magenta-family pixels; the viewport's near-white stars `(214,214,230)` are 3 px inside the window, not noise |
| No baked text/watermarks | Console screens are abstract bar/block glyphs; rack display is 6 flat bars; `03`/`04` labels are sheet chrome, not in any shippable asset |

---

## 4. New / remaining findings

### BLOCKER
None.

### MAJOR
None.

### MINOR

1. **Hazard platform right edge has a 1 px gold column that breaks the lip** — at x = 1405 the tape pattern
   runs the full 32 rows, so `(1405, 480)` and `(1405, 481)` are `(112,75,12)` instead of the `(78,78,99)` lip,
   and `(1405, 510)` / `(1405, 511)` are gold instead of the `(8,8,12)` base. Reads as a small notch in the
   top-right and bottom-right corner of the plinth at 1x. Fix: clamp the stripe field to x ≤ 1404 (or draw the
   lip/base after the field).
2. **Hazard platform left edge is off-grid and overlaps the right crate** — the band starts at x 1275 (5 px off
   the 32-px grid, i.e. 2 px into the crate footprint 1218–1276), overwriting the crate's x 1275–1276 border
   rows 480–511, and it is a mid-stripe cut with no end treatment (the crate band, by contrast, has a dark
   inset at both ends). Invisible at 1x because the crate hides it; fix by starting the band at 1280 and letting
   the crate overlap it, or by adding the same 1 px dark inset the cargo band got.
3. **Cargo tape's black == strap colour** — both are `(20,20,28)`, so where a strap crosses the band there is no
   1 px separation: the strap reads as a vertical black gap in the tape rather than as an object lying over it.
   Still legible (the strap continues above and below), but a 1 px darker strap shadow over the tape would
   sharpen it.
4. **Vertical light strips are segmented** (pre-existing) — 1 px break every ~16 px from the tile's own panel
   seam, so "strips continuous" holds visually, not literally. Accept or make the strip pass under the seam.
5. **Reactor's own plinth is never seen in the assembly** (pre-existing) — the 4-tile hazard platform occupies
   y 480–511 and hides the `reactor_core` sprite's bottom 32 rows, so its bespoke X-braced base only exists in
   `04`. Not a defect, but half of the sprite is dead weight in every composite.
6. **Reactor platform orange dashes** (pre-existing, catalog-only) — `reactor_core` rows 120–122 / total 37 px of
   `(207,117,82)` in an irregular 1-px pattern over `(36,24,56)`; reads as chipped paint rather than hazard
   language, and it is the only place the set uses orange on purple. Invisible in `05`/`06`.
7. **`01` puts the hazard tile on the deck fascia** (pre-existing) — row 7, cols 14–15 (y 224–256), two rows
   below the walk surface, so the sample's only in-situ hazard is painted on the platform face rather than a
   wall lip. Defensible, but it is the odd placement out (in `05` it is correct, row 15).
8. **Two tileset slots are byte-identical duplicates** (pre-existing) —
   `deck_top_left.png` == `deck_left.png` and `deck_top_right.png` == `deck_right.png` (diff 0), so the atlas
   advertises 25 tiles with 23 unique.
9. **`02`/`03`/`04` are still non-integer upscales** (pre-existing) — pixel-block parity cannot be judged from
   them; use `00` (exact 8x) and the natives. The cargo band is measurable on `03` only because its 5.8x scale
   is uniform.
10. **Characters hover 1–2 px** (pre-existing) — `agent idle f00` bbox `(17,10,47,63)` placed at (224,448) →
    lowest opaque row 510, walk line 512. Same for the mirrored `shoot2 f02`. Fix: place at y 449–450.
11. **Crate contact shadow is inset 11 px** (pre-existing) — 3 px shadow on rows 512–514 spans x 173–209 under
    a 58 px footprint (162–220), so the outer 11 px of each crate base has no contact shadow. Also the crate
    side borders are 5–6 px of pure black (x 0–5 / 54–58), the heaviest outline in the set.

---

## 5. Verdict

## **PASS**

No blocker and no major remain.

The round-4 major is genuinely fixed and provably so, not merely recoloured: the cargo hazard band is a 6 px
tape of 45° gold `(112,75,12)` / black `(20,20,28)` stripes on an exact 8 px pitch (112 gold pixels, every one
of them on `(x+y) mod 8 ∈ {0,5,6,7}`), clipped to the crate face x 8–52 with a 1 px `(8,8,12)` inset on all four
sides, with both straps genuinely re-drawn on top (the stripe model predicts gold at x 13–14 and x 46–48 of row
80; the strap wins), zero gold left anywhere else in the sprite, and the same stripe language as `hazard.png`
and the reactor platform. It reads as applied door-tape at 1x in `03`, `05` and `06`, which was the only thing
holding the set back. Everything round 3 and round 4 signed off is intact: the hazard platform is seamless
(cells byte-identical, diff 0), pipes land in flanges/junctions, the grate is a horizontal-bar floor grate, the
deck lip is exactly at y 512 with no gaps, the ribs are single ceiling-to-floor columns, the rack is solid and
placed at diff 0, wall variance is 17.1 % most-common block, all six sprites are trimmed to their alpha bbox as
single components, and the palette is 33/36 colours with no AA, no gradients and no magenta.

---

## 6. Summary

This round the pipeline did exactly the one thing that was asked and did it correctly: the `cargo_stack` gold
zig-zag is gone, replaced by a true hazard band that is geometrically indistinguishable from `hazard.png`
(45°, period 8, 4 px gold on 4 px black, same two colours), properly inset so it reads as tape rather than a
decal, and drawn beneath the straps so they visibly cross it. The proof is arithmetic rather than impression —
every one of the 112 gold pixels falls on the 8 px diagonal lattice, the band occupies exactly rows 77–82 / x
8–52 inside a crate face of x 6–53, and the strap columns 12–14 and 46–48 override the stripes where the
pattern says gold. The rest of the set is unchanged from the round-4 pass and re-verified item by item, and the
remaining list is polish only: a 1 px gold notch at the platform tape's right edge (x 1405), the platform band
starting 5 px off-grid under the crate, the tape's black coinciding with the strap colour, segmented light
strips, the reactor's hidden plinth, catalog-only orange dashes, the two duplicate deck-cap tiles, non-integer
review-sheet scales, a 1–2 px character hover, and the inset crate contact shadow. None of them is visible
enough to hide the fix or to fail the set, so the ship interior ships.
