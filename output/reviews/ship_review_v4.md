# Ship interior — independent art review v4

Reviewer: independent multimodal reviewer (round 4). I did not generate, modify or regenerate any of these
assets, and I ran no project test — only read + pixel measurement of the shipped files.

Coordinate convention: all coordinates are **native 1x** in `mega/ship/ship_mega_1x.png` (1536 x 640, 32 px
tiles, floor row = 16 → walk surface at **y = 512**) or in the stated sprite. `05`/`06` are verified exact
2x nearest-neighbour upscales of the 1x scene (`np.array_equal` == True), `01` is an exact 4x of
`tileset_sample`, `00` is an exact 8x of the 25 tiles (every tile matches byte-for-byte at 8x). `02`, `03`
and `04` are **not** integer upscales (see minor 10), so all pixel-exact claims below were measured on the
native files, not on the sheets.

Sprite placements recovered by exact template match (not eyeballed):

| element | sprite | placement (x, y) | bbox | grounding |
|---|---|---|---|---|
| cargo_stack (left) | 59 x 87 | (162, 425) | x 162–220, y 425–511 | bottom row 511 + 3 px contact shadow on 512–514 |
| cargo_stack (right, mirrored) | 59 x 87 | (1218, 425) | x 1218–1276, y 425–511 | same |
| console_bank | 102 x 59 | (525, 421) | x 525–626, y 421–479 | stands on dais lip 480 |
| server_rack | 55 x 105 | (900, 407) | x 900–954, y 407–511 | bottom 511 |
| viewport | 112 x 88 | (520, 128) | x 520–631, y 128–215 | wall-mounted |
| reactor_core | 118 x 137 | (1285, 375) | x 1285–1402, y 375–511 | lower 32 rows behind the hazard platform, visible plinth ends on lip 480 |
| agent idle f00 | 64 x 64 | (224, 448) | content y 458–510 | 1–2 px above walk surface |
| agent shoot2 f02 (mirrored) | 64 x 64 | (960, 448) | content y 459–510 | 1–2 px above walk surface |

---

## 1. File coverage (100 % of the packet, plus native cross-checks)

| # | File | What was verified | Verdict |
|---|---|---|---|
| 1 | `work/review/ship/00_tileset_x8.png` (2048x1024) | 8x atlas, 25 tiles = 22 originals + 3 deck-step variants, 7 empty slots flat-filled; **every** 32x32 block matches the shipped tile byte-for-byte at 8x (0.0 mean diff), 15 colours total, opaque, no labels baked in | **PASS** |
| 2 | `work/review/ship/01_tileset_sample_x4.png` (2304x1152) | exact 4x of a 18x9 tiled room slice; wall band, lit frame column, window, vent, violet panel, deck-step dais, grate, hazard; all 162 cells resolved to shipped tiles (0 error) | **PASS** (with minor 9) |
| 3 | `work/review/ship/02_all_tiles_x5.png` (1320x1100) | complete atlas, 6x5 grid (30 slots, 25 filled), all 25 labels legible and in the same order as the shipped files, every tile readable at sheet size | **PASS** (2 duplicate slots, minor 4; sheet scale nit, minor 10) |
| 4 | `work/review/ship/03_medium_catalog_x3.png` (1560x520) | `console_bank`, `cargo_stack`, `server_rack` complete, labelled, no clipping, no overlap of label and art | **FAIL** — cargo hazard marking still a squiggle (major 1) |
| 5 | `work/review/ship/04_mega_catalog_x3.png` (1560x520) | `hull_frame`, `viewport`, `reactor_core` complete, labelled; sprite bboxes tight (pad 0), reactor plinth present | **PASS** (minor 2, catalog-only noise) |
| 6 | `work/review/ship/05_whole_ship_x2.png` (3072x1280) | whole assembly: 5 ribs, 4 bays, viewport, console+daïs, rack, 2 cargo stacks, reactor + hazard platform, ceiling lights | **FAIL** — inherits major 1 |
| 7 | `work/review/ship/06_showcase_x2.png` (3072x1280) | assembly + 2 agent frames; both grounded on the walk line, no overlap with props | **FAIL** — inherits major 1 (gold squiggle at x 165–191 / 1247–1273, y 504–509) |

Native files opened and measured (no sampling):

* `environment/ship/tiles/*.png` — all 25 tiles: per-row ASCII dumps, colour census, alpha census,
  horizontal/vertical wrap tests (`hazard`, `grate_fill`, `grate_top`, `deck_top`, `deck_fill`, `ceiling`,
  `pipe_h`, `pipe_v`, `vent`, `wall_flat_light`, `deck_step`, `light_strip`).
* `environment/ship/props/{cargo_stack,console_bank,server_rack}/sprite.png` — alpha bbox, connected
  components, per-row dumps, exact placement search in the assembly.
* `mega/ship/elements/{hull_frame,viewport,reactor_core}/sprite.png` — alpha bbox (all pad 0 = trimmed),
  component count (all 1 = no floating fragments), per-row dumps.
* `mega/ship/ship_mega_1x.png`, `mega/ship/ship_layout.json`, `mega/ship/report.json`,
  `showcase/ship/scene_1x.png`, `showcase/ship/report.json`, `environment/ship/tileset*.png`.

Global style audit (re-run this round):

* 05 = **33 colours**, 06 = **37 colours** (33 + 4 character skin/white), tiles 15–18 colours, 0
  semi-transparent pixels in every asset (alpha strictly 0/255) → **no AA, no blur, no gradients**.
* No `(255,0,255)` and no magenta-family colour anywhere; the only violets are the intended
  `(36,24,56)…(183,140,224)` accent ramp.
* No baked text in any shippable asset (abstract glyph blocks on the console screens, tick-marks on the rack
  display — no letterforms).
* Every sprite is a **single** connected alpha component → no floating fragments.
* Wall variance: 392 wall blocks outside the ribs → **81 distinct**, most common block 29.6 %, top-4 57.9 %
  (round-3 threshold ≤ 30 % still met).

---

## 2. Round-3 blockers

| ID | Round-3 requirement | Status | Visible evidence (exact coordinates) |
|---|---|---|---|
| **B-1** | `hazard.png` must tile: integer stripe count per tile, no slivers/seams on the reactor platform | **FIXED** | `hazard.png` = 32x32, gold `(112,75,12)` on `(20,20,28)`, **period exactly 8 px** (column x vs x+8: mean diff 0.0 for all x), **4 stripes per row** (e.g. row 2: gold x0–1, 6–9, 14–17, 22–25, 30–31), 45° (phase −1 px per row), 100 % opaque. In the assembly the band is x 1248–1407, y 480–511 (cols 39–43, col 39 partly hidden by the crates); gold runs are 4 px wide on an 8 px pitch with **constant phase across the tile seams at x = 1280 / 1312 / 1344 / 1376** (16 full periods, 0 breaks; visible gold spans x 1278 → 1405, the last 1 px sliver merged into the rib foot). Top lip rows 480–481 `(78,78,99)` is continuous across the whole band. Cells x 1280–1376 are byte-identical to `hazard.png` (mean diff 0.0), x 1376–1408 diff 2.8 (rib-foot overlap only). |
| **MJ-1** | Pipes must not dead-end; vertical runs must meet horizontal runs/flanges, no raw black-slot ends | **FIXED** | Vertical conduit run at col 9 (x 288–320) descends y 96 → 448, ends with the tile flange rows 447–449 (`(111,111,136)` collar + 24 px plate) and **lands directly on a horizontal conduit junction tile at y 448–480** (same at cols 21 and 33), so the run no longer stops in open wall. Horizontal trunks (row 2, y 64–96; cols 6–9 / 14–21 / 26–33 / 38–43) run edge-to-edge: rails at y 69–72 / 78–81 / 87–90 continue through the 32 px seams (each boundary carries the tile's deliberate 1 px clamp: `(111,111,136)` over `(20,20,28)`), and the run now ends against the rib column (x 320 / 704 / 1088 / 1408) instead of mid-bay — the round-3 4 px black slot at x 666–669 is gone (x 669 = `(155,155,176)` rail). |
| **MJ-2 / MJ-3** | Grate must read as a floor-line grate (no black patch, no duplicated light band, no X-lattice noise) | **FIXED** | `grate_top` = 32x32: 2 px light lip (rows 0–1 `(155,155,176)/(78,78,99)`), 1 px black, 1 px shadow, then **horizontal bars** (rows 4/8/12/…: 1 px `(155,155,176)` + 1 px `(78,78,99)`), 2 px black between, two 2 px vertical posts at x 7–8 / 23–24. `grate_fill` = same bar field only, period 4 px → wraps vertically exactly (32/4). In-scene at x 256–320, y 512–544 the grate sits 8 px below the deck lip with a light top edge → reads as a recessed floor grate. The X-diamond lattice and the second floor line are gone. |
| **MJ-4 / B2** | Cargo: inter-crate shadow, strap buckles, **straight hazard band** | **PARTIAL** | Shadow **FIXED** (sprite rows 22–26 = 1 px `(20,20,28)` + 3 px `(35,35,46)` under each crate, then a 1 px black seam, then the next bright lid at row 27/55). Buckles **FIXED** (3x2 `(111,111,136)`/`(155,155,176)` buckle at the top of every strap, sprite rows 4–5 and 30–31/58–59). **Hazard band NOT FIXED**: still a gold sawtooth — sprite rows 79–84, x 3–29 (world: left crate y 504–509, x 165–191; right crate y 504–509, x 1247–1273), 6 rows tall, 1–3 px strokes on a 5–6 px zig-zag pitch, and it is painted **over the left strap** (strap at sprite x 10–12, gold at x 11–13 in rows 80–83) and over the crate's bottom rim (`(78,78,99)` at x 3–5, rows 82–84). |
| **Minor** | Reactor no longer has 53 empty rows; all sprites trimmed to alpha bbox; reactor mount tight | **FIXED** | `reactor_core/sprite.png` = 118x137 with alpha bbox x 0–117, y 0–136 → **pad 0 on all four sides**; likewise `hull_frame` 118x203 (pad 0), `viewport` 112x88 (pad 0), `cargo_stack` 59x87 (pad 0), `console_bank` 102x59 (pad 0), `server_rack` 55x105 (full 255). In the assembly the reactor's visible plinth ends on the platform lip at y 480 (its lowest 32 rows are occluded by the platform band) → mount reads tight. |

---

## 3. New / remaining findings

### MAJOR

**1 — `cargo_stack` hazard marking is still a zig-zag squiggle, not a hazard band (MJ-4/B2 not fixed).**
Severity: MAJOR (explicit round-3 acceptance item, visible at 1x in both cargo bays and in `03`).
Evidence: current sprite (22:30 build) has zero 45° stripes. Rows 79–84 (6 px) hold gold `(112,75,12)` in
1–3 px runs at a 5–6 px pitch (`GGG..GGG..GGG..GGG` style), forming three "W" shapes across x 3–29 only —
i.e. 27 px of a 47 px wide crate face. It contradicts the hazard language used two tiles to the right
(45°, 8 px period, 28 px tall at x 1248–1407) and in `hazard.png`. It also paints over the left strap
(sprite x 10–12) and the crate's bottom rim, so it reads as a decal/glitch rather than door-tape. At 1x:
left bay x 165–191 / y 504–509; right bay x 1247–1273 / y 504–509.
Fix: replace rows 79–84 with a 6 px tall band of 45° gold/black stripes at an **8 px period** (same phase
math as `hazard.png`), clipped to the crate face x 6–52, drawn *under* the straps (straps re-drawn on top,
with their buckle), and with a 1 px dark inset at both ends so it reads as applied tape. Then re-emit `03`,
`05`, `06`.

### MINOR

1. **Characters hover 1 px** — `agent idle f00` at (224, 448) and `shoot2 f02` (mirrored) at (960, 448) have
   their lowest opaque row at y 510; the walk surface is y 512 (row 511 is the dark wall row). Round 3
   reported a 3 px *sink*; it is now resolved but overshot by 1 px. Fix: place both at y 449 (content bottom
   511) or shift the sprite pivot by 1 px.
2. **Reactor base band is 1 px noise** (catalog-visible only) — sprite rows 120–122 (world y 495–497, hidden
   behind the hazard platform in `05`/`06`) are a 3-row strip of 2–3 px fragments in `(36,24,56)`/`(78,78,99)`/
   `(111,111,136)`/`(207,117,82)`/`(231,154,114)`. It has no legible logic and uses two colours that are not
   in the env accent system, so in `04` it reads as dithered dirt at the base of the machine. Fix: replace
   with a 2 px `(112,75,12)`/`(20,20,28)` band or delete those three rows.
3. **`hazard.png` is only horizontally tileable** — the stripe field is rows 2–29 (28 rows = 3.5 periods of 8)
   between a 2 px light lip (rows 0–1) and a 2 px black base (rows 30–31). Stacking two rows would produce a
   4 px stripe jog at the join plus a second lip line. No current placement stacks it (both `01` and `05`
   use one row), so nothing is visible today, but the tile is a "band" piece, not a fill piece. Fix: make the
   stripe field 24 rows (3 whole periods) and keep the lip/shadow, or document it as single-row only.
4. **Two tileset slots are byte-identical duplicates** — `deck_top_left.png` == `deck_left.png` and
   `deck_top_right.png` == `deck_right.png` (0.0 diff). The atlas advertises 25 tiles / "top-cap variants"
   but only 23 unique tiles exist, and `deck_left`/`deck_right` are never used in the room (the floor runs
   full width). Fix: either author real top-cap pieces (lip + inset corner) or drop the two labels so the
   count is honest.
5. **`deck_step` reads as a catwalk railing, not a step riser** — rows 5–28 are 4 vertical posts on a field
   painted in the *wall* colour `(35,35,46)` (opaque, so no wall detail shows through), and rows 0–4 are a
   4 px bright cap. Under the console (cols 15–19, x 480–640) this makes the daïs a see-through grille; it is
   readable as a vented plinth but has no step/tread depth. Fix: fill the gaps with a 3-tone recess
   (`(20,20,28)` back, `(8,8,12)` shadow) and give the cap 6 px of tread with a 1 px front shadow.
6. **Cargo side borders are 5–6 px pure black** — sprite x 0–5 and x 54–58 are `(8,8,12)` on every row, i.e.
   10 % of the sprite width is a hard black edge, against the set's 1 px outline language. It reads as deep
   shadow and stays legible at 1x, but it is the heaviest outline in the set. Fix: 2 px edge + 3 px ramp.
7. **Crate contact shadow is inset 11 px** — the 3 px shadow on rows 512–514 spans x 173–209 (left crate) /
   x 1229–1265 (right), i.e. it starts/ends 11 px inside the crate's footprint, so the outer 11 px of the
   crate base has no contact shadow and appears pasted. Fix: run the shadow the full width minus 1 px.
8. **Vertical light strips are segmented** — the cyan `wall_flat_light` line at x 169 / 489 / 873 / 1257 is
   15 px on / 1 px off (deliberate: the tile's own panel seam at rows 7 and 23 of each tile), so the strip has
   a 1 px break every 16 px from y 96 to 448. Consistent and intentional, but it does not literally satisfy
   "strips continuous" — worth a deliberate decision (either accept as segmented tube or make the strip
   pass under the seam).
9. **`01` demo placement** — the sample puts the hazard tile at cols 14–15, **row 7** (y 224–256), i.e. 32 px
   *below* the deck surface, inside the floor slab, instead of on a platform face. Not a tile defect, but the
   only "in-situ" hazard in the sample is physically wrong; in `05` it is correct (row 15).
10. **Packet scale labels are inaccurate** — `02_all_tiles_x5` is actually rendered at ~6.375x (hazard gold
    pitch 51 px instead of 40, tile block 204 px on a 220 px grid) with uneven 6/7 px pixel blocks;
    `03`/`04` are fit-scaled per sprite (≈2.4x–5.8x). Art in those sheets is nearest-neighbour (hazard region:
    2 colours only), so no blur, but pixel-block parity cannot be judged from them — use `00` (exact 8x) and
    the natives. Fix: emit 02/03/04 at an integer scale.
11. **Housekeeping** — `tiles/` still holds `conduit_checkerboard/seamless/x8` but no `conduit.png`, plus
    `deck.png`, `grate.png`; the tileability QA set covers wall/deck/grate/conduit but **not** `hazard`
    (whose only defect was vertical wrapping, see minor 3). Not visible, but the folder no longer describes
    the tile set.

---

## 4. Verdict

## **FAIL**

No blocker remains — the three headline defects of round 3 are genuinely gone and verified numerically
(hazard period 8 px with 0 phase error across the whole 160 px platform; vertical pipe run now lands on a
flanged junction at y 448; grate is a horizontal-bar, vertically wrapping floor grate).

One **major** remains and it is the one cargo acceptance item that was never touched: the `cargo_stack`
"hazard band" is still a 6 px gold saw-tooth squiggle (sprite rows 79–84, x 3–29; world y 504–509 at
x 165–191 and x 1247–1273) painted over the left strap and the crate rim, against a hazard system that is
otherwise a clean 45° / 8 px stripe (platform x 1248–1407, y 480–511). Per the pass rule ("PASS only if no
blockers/majors remain") the set fails on that item alone; everything else is minor polish, listed above
with coordinates and fixes.

Round-3 items that must not be reopened: **B-1** (hazard tiling), **MJ-1** (pipe termination), **MJ-2/MJ-3**
(grate), the reactor/sprite alpha-bbox trim, **M1** (deck registration), **M2** (accent strips), **M4**
(server rack), **M8** (wall variance, 29.6 % most-common block).

---

## 5. Summary

The round-3 pipeline work landed: the hazard tile is now an exact 8 px-period, 4-stripe 45° pattern that
wraps horizontally with zero phase error and produces a clean 160 px platform band under the reactor with no
slivers, the vertical conduit run no longer stops in open wall at y 448 but terminates in a flange on a
horizontal junction tile (and the old black-slot run ends are gone), and the grate was rebuilt as a readable
horizontal-bar floor grate with a light top lip and a vertically seamless fill; all sprites are now trimmed
to their alpha bbox (pad 0), single-component, on a 33-colour flat palette with no AA/blur/gradient/magenta,
and the composition is grounded (props on 511 with 1–3 px contact shadows, ribs running ceiling y 64 to floor
y 511, deck lip correctly at y 512, console centred under the viewport). What holds the set back is one
specific, still-unfixed acceptance item: the `cargo_stack` hazard marking remains a 27x6 px gold zig-zag that
overlaps the strap and the crate rim, so it reads as a decal/glitch next to the properly striped platform and
breaks the hazard language of the set; a real 6 px, 8 px-period 45° band drawn under the straps fixes it.
The remaining list (1 px character hover, hidden 3-row reactor base noise, hazard not vertically tileable,
two duplicate deck-cap tiles, railing-like `deck_step`, 5–6 px crate side borders, inset contact shadow,
segmented light strips, the `01` demo placing hazard inside the floor slab, and non-integer review-sheet
scales) is minor polish that does not hide the fix, so after the cargo band is replaced this set should pass
on a re-read of `03`/`05`/`06`.
