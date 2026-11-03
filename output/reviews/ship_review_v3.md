# Ship interior — independent art review v3

Reviewer: independent multimodal reviewer (round 3). I did not generate any of these assets.
Method: visual read of every review PNG at full size + pixel-level verification on the native files
(`environment/ship/**`, `mega/ship/**`, `showcase/ship/**`). No asset was modified, no project test was run,
no image was regenerated.

Coordinate convention: all coordinates below are **native 1x** in `mega/ship/ship_mega_1x.png` (1536 x 640,
32 px tiles, floor row = 16 → walk surface at y = 512) or in the stated sprite. Review-packet files are exact
nearest-neighbour upscales: `05/06` = 2x of the 1x scene (verified `np.array_equal`), `01` = 4x of
`tileset_sample.png`, so pixel-art integrity is intact in the packet (no bilinear blur anywhere).

---

## 1. File coverage (100% of the packet, plus native cross-checks)

| # | File | Content verified | Verdict |
|---|---|---|---|
| 1 | `work/review/ship/00_tileset_x8.png` (2048x1024) | 8x atlas of all 25 tiles, labels legible, no labels baked into `tileset.png` | **PASS** |
| 2 | `work/review/ship/01_tileset_sample_x4.png` (2304x1152) | tiled room slice; wall bands, lit panels, window, vent, frames, deck, step, grate, hazard | **FAIL** (grate patch + hazard strike-through, §3) |
| 3 | `work/review/ship/02_all_tiles_x5.png` (1320x1100) | all 25 tiles labelled 6+6+6+6+1 = 25 (counted); every tile distinct | **FAIL** (atlas is complete and legible, but two shipped tiles are defective: `grate_fill`/`grate_top` noise, `hazard` not tileable) |
| 4 | `work/review/ship/03_medium_catalog_x3.png` (1560x520) | console_bank, cargo_stack, server_rack on the catalog card | **FAIL** (cargo_stack hazard squiggle + missing inter-crate shadow) |
| 5 | `work/review/ship/04_mega_catalog_x3.png` (1560x520) | hull_frame, viewport, reactor_core | **PASS (minor)** — reactor sprite still carries 53 transparent rows above content |
| 6 | `work/review/ship/05_whole_ship_x2.png` (3072x1280) | full assembly, 5 ribs, viewport, reactor, console, cargo x2, rack | **FAIL** (§2 M5/M6/M7, §3) |
| 7 | `work/review/ship/06_showcase_x2.png` (3072x1280) | assembly + 2 agent frames | **FAIL** (inherits the above; character grounding/style) |

Native files opened and measured (not sampled):

* `environment/ship/tiles/*.png` — all 25 tiles + `deck_fill/deck_top/*_left/*_right/deck_step*` row dumps;
  `hazard.png` tiling test; color census of every tile.
* `environment/ship/props/console_bank/sprite.png` (128x64), `cargo_stack/sprite.png` (64x96),
  `server_rack/sprite.png` (64x112) — alpha bbox, connected components, per-row dumps.
* `mega/ship/elements/hull_frame/sprite.png` (128x256), `viewport/sprite.png` (128x96),
  `reactor_core/sprite.png` (128x192) — alpha bbox, component count, template placement search.
* `mega/ship/ship_mega_1x.png` (1536x640), `mega/ship/ship_mega_preview.png`, `ship_layout.json`,
  `showcase/ship/scene_1x.png` (1536x640), `scene.png`, `environment/ship/tileset.png`,
  `tileset_sample.png`, `materials.json`, `report.json`, `REPORT.md`, `config/ship_config.py` (prompt strings).

Global style audit: 24 distinct colors across all tiles, 4–10 colors/tile, **0 semi-transparent pixels**
(alpha is strictly 0/255) in every sprite and tile → no AA, no blur, no gradients; 1 px `(8,8,12)` outline on
every prop; flat ramps; no magenta; no baked text in any shippable asset (labels exist only in the review
catalogs). `grep` of `ship_config.py` confirms warm rust/orange `(125,58,42)…(236,132,85)` is an intended
"small warm hazard marking" accent, so it is not a palette violation.

---

## 2. Round-2 blockers / majors

| ID | Round-2 requirement | Status | Visible evidence (exact coordinates) |
|---|---|---|---|
| **B1** | 5 ribs, single ceiling→floor pieces, no mid-height flared shelf / double flange, no foot under the console dais, no rib cut at the right edge | **FIXED** | Ribs present at x = 0, 320, 704, 1088, 1408 (5/5); content x 5–122 each; capital y 67–77, body 78–481, plinth 482–510, so each rib meets the walk surface (512) and the ceiling line (64) as one uninterrupted column. Width is constant 5–122 between capital and plinth → no mid-height shelf. Console dais occupies x 476–647, ribs nearest at 320–448/704–832 → no rib foot buried. Rib 5 ends at x 1530, 6 px of wall before the frame edge → not cut. |
| **B2** | cargo_stack = 2–3 offset crates with lids, inter-crate shadow, straps, hazard stripe — not a 3x3 panel grid | **PARTIAL** | Offset stacking + lids + corner rivets now read correctly (3 crates, sprite rows 8–33 / 34–61 / 62–95; lids at 8–13, 34–38, 62–66). **Inter-crate shadow absent**: at the seam the lower lid is *full brightness* — sprite row 34 = `(8,8,12)` 1 px outline, rows 35–38 = `(155,155,176)/(111,111,136)/111/111`, i.e. the upper crate casts nothing. **Straps read as dividers**: 2 plain black vertical bars + 3 full-width horizontal rules per crate reproduce the same 3x3 grid the round-2 note complained about (no buckles/tensioners). **Hazard stripe is a squiggle**: 23x6 px of gold diagonal dashes at (168–190, 503–508) in the assembly (sprite 8–30, 82–89) — reads as scratches/graffiti, not a hazard band. |
| **M1** | Deck top-registered: lit walk surface at y=512, front face below, no lit band 11 px down + dark recess under props | **FIXED** | Row y=512 is `(155,155,176)` for 1352 of 1536 px; the lip is 512–515 `(111/54/54)`, moulding 516–519 `(78,78,99)`, 2 px shadow 520–521, face 522–640. `deck_top.png` row 0 = `(155,155,176)` full width (top-registered). Props: cargo content bottom 511, server_rack 511, reactor hazard platform 511, and each has a contact shadow on row 512 (cargo 172–211, rack 908–947, cargo-B 1228–1267) → nothing hovers. |
| **M3** | Reactor cropped to content, grounded, mount frame fits content (no 56 px empty black frame above) | **PARTIAL** | The 56 px *black* band is gone — that area is now transparent, and in-scene the plate reads as a ~7–8 px recess bezel (rows 373–380) with the machine starting at 381. But the shipped sprite is **still not cropped**: `reactor_core/sprite.png` alpha bbox = (5,53)-(123,190) in a 128x192 canvas → 53 transparent rows above and 2 below (content 118x137). `ship_layout.json` even states "cropped to content", which is false. Grounding is OK via the hazard platform (bottom 511). |
| **M4** | server_rack solid & readable, vents/LEDs/cables, no black holes, no glitch noise | **FIXED (minor)** | Content 901–956 x 406–511; one connected 5775 px component; 6 vent rows + 6 LED pairs; opaque pure-black is only the 1 px outline (the two apparent "holes" at the base are empty alpha/outline, not interior black). No glitch noise. Minors: 14 px blank header plate (sprite y 6–20), **no cables at all**, 4 stray cyan/violet dashes at sprite (6–30, 100–102), right-hand LEDs are grey where the left are violet, bottom is a flat 1 px black line. |
| **M5** | Hazard runs terminated/snapped to props, no raw mid-stripe cut | **NOT FIXED** | The run is snapped to the prop width (platform 1276–1405 under reactor content 1285–1403) — good. But the **tile itself is not tileable**: `hazard.png` stripes are 5 px on / 7 px off (period **12**), while the tile is 32 px, so every 32 px boundary cuts a stripe into a 1–2 px sliver. Measured on the reactor platform at y = 485/495/505: sliver-plus-wide-gap at x ≈ **1308, 1340, 1372, 1404**, producing 4 visible vertical seams through the diagonal stripes (clearly visible at 10x). Same defect in `01_tileset_sample` at x 448–511. |
| **M6** | grate_top = recessed grate at the walk line, not a patch stuck over the deck face | **PARTIAL** | Top is now registered: grate occupies (256–319, 512–543), so its top row is the walk line (previously 11 px down). But it is still a 64x32 patch **plastered over the lip and 24 px of the front face**, with a 1 px solid `(8,8,12)` column at x=256 from y 512–543 cutting the lit lip, and the tile's own light band at y 527–528 creating a *second* floor line inside the dark patch. Combined with the X-diamond lattice on pure black it reads as a hole / missing-texture patch, not a grate. |
| **M7** | Pipe runs need flanges/caps/elbows; no pure-black slot ends; no vertical pipes stopping flat against bare wall | **NOT FIXED** | (a) Vertical 3-pipe run at x 293–320 descends from the ceiling and **stops dead at y = 448** against bare wall — no flange, cap or elbow (12x zoom confirms a flat cut). (b) Horizontal runs end mid-bay with a 4 px near-black slot: run 452–665 terminates at x 666–669 = `(20,20,28)` slot plus a lone floating `(155,155,176)` pixel at (667,475); the left-bay run ends at x 281 with a plain square end. |
| **M2** | Wall accent strips not chopped into short dashes by cluster overrides | **FIXED** | Cyan strips at x = 169, 489, 873, 1257 and violet strips at x = 278, 598, 982, 1366 run continuously y 104 → ~457 (≈300 px per bay). The only breaks are the deliberate 1 px clamp collars (15 px on / 1 px off) from `wall_flat_light`/`wall_flat_violet`; at x=598 the strip is simply occluded by the viewport mount (correct layering). |
| **M8** | Wall must not be ~77 % one byte-identical tile; clusters visible & distinct | **FIXED** | Hashed every 32 px wall block outside the ribs (336 blocks): most common byte-identical block = **30.1 %** (101 blocks), **73 distinct blocks**, top-4 = 60 %. Visible clusters are real (lit panels with clamp strips, framed inset panels, vents, window, violet rib-adjacent fields). Still reads as a regular panel grid (see §3 minor) but the round-2 threshold is met. |

---

## 3. New / remaining findings

### BLOCKER

**B-1 — `hazard.png` cannot be tiled; the hero prop shows the seam.**
Severity: BLOCKER (the tile is unusable for any run > 32 px, and it is used on the reactor platform).
Evidence: stripes period 12 px in a 32 px tile (32 mod 12 = 8) — numerically, shifting the tile by one stripe
period never aligns; on `ship_mega_1x` rows 480–511, x 1276–1405 there are 4 stripe-slivers with a wide gap at
x = 1308/1340/1372/1404 and a faint 1 px tile edge line at every seam. Same artifact in `tileset_sample`
x 448–511.
Fix: regenerate the hazard tile with an integer number of stripes per tile (e.g. 8 px period: 4 stripes per
32 px tile, 45° with dx = dy = 32/4 = 8), or draw the run as one authored band; re-emit `02`/`03` and the
assembly.

### MAJOR

**MJ-1 — Pipes dead-end (M7, above).** Vertical run x 293–320 ends at y 448 flat against the wall; horizontal
runs end in a 4 px black slot at x 666–669 / plain cut at x 281.
Fix: terminate every run with a flange tile (2 px collar + 4 px plate), and route the vertical run into a
horizontal elbow or down to the deck.

**MJ-2 — Grate still reads as a hole in the deck fascia (M6, above).** 64x32 patch at (256–319, 512–543) with a
1 px black border column at x=256, a second light band at y 527–528, and high-contrast X-lattice.
Fix: replace with a floor-line grate: 2–3 px bright lip (matching `deck_top` rows 0–3), dark slots at 4–8 px
depth only, drop the duplicated light band, and draw a 1 px inset frame instead of a solid black border.

**MJ-3 — `grate_fill` / `grate_top` are noise, not grates (tile readability).** Both tiles are pure black
`(8,8,12)` fields with diagonal X-diamond lattice and 1 px light specks; at 1x they read as corrupted data or
a missing texture. 6 colors each, high local contrast on black — the only tiles in the set that break the
"flat 3-tone, readable at 1x" rule.
Fix: rebuild as horizontal bars (like `vent.png`) with a 1 px light top edge and 2–3 px slots; keep the tile
at ≤3 value steps.

**MJ-4 — cargo_stack still a panel grid in disguise (B2, above).** No inter-crate shadow; strap bars carry no
hardware; the hazard marking is a 23x6 squiggle.
Fix: add a 3 px shadow row on each lower lid (use `(20,20,28)` then `(35,35,46)`), give each strap a 3x2
buckle, and replace the squiggle with a straight 6 px hazard band across the bottom crate (using a hazard
pattern that actually tiles).

### MINOR

1. **Reactor sprite not cropped** — 53 transparent rows above content, 2 below (128x192 canvas, 118x137 content);
   `ship_layout.json` claims "cropped to content". Consequences: wrong bbox for collision/UI and an empty
   bezel ring (~7–8 px top, ~5 px sides) that reads as a picture frame around the machine. Fix: crop to
   (5,53)-(123,190) and re-pivot.
2. **Viewport double frame** — rows 128–134 are a flat `(20,20,28)` band above the bezel and there is a 1 px
   `(78,78,99)` outline only on the right (x=640), so the recess reads asymmetric / as a floating framed
   picture. Fix: either author the recess inside `viewport.png` with a symmetric 1 px outline, or drop it.
3. **Characters sink 3 px** — showcase layer bbox y 458–**514** while props stop at 511 and the walk surface is
   512; the boots overwrite the lit lip rows 512–514 (rows 512/513/514 become `(20,20,28)/(8,8,12)/(8,8,12)`
   at x 978–984). Also `shoot2` (x 961–1011) is fully airborne with no ground contact in a *showcase* shot.
   Fix: rebase the character pivot to the walk line and pick a grounded frame for the showcase.
4. **Character style gap** — the agent frames use ~1 px detail, soft hair highlights and 7 colors
   (`(247,195,154) (231,154,114) (207,117,82) (214,214,230) (82,53,116)`) that exist nowhere in the
   24-color environment palette; env uses chunky 2–3 px blocks. Reads as two different games in `06`.
5. **Wall still grid-like** — 30 % one identical block and a 32 px square-motif rhythm; four identical bay
   accent layouts (cyan at rib+41, violet at rib+150 in all 4 bays). Suggest 2–3 larger multi-tile motifs
   (a 3x2 window bank, a 2x3 service hatch) to break the lattice.
6. **Ceiling/wall junction = 3 px pure black** across the full width (rows 62–64). Reads as an open slot
   between ceiling and wall. Fix: one row `(20,20,28)` + one row `(8,8,12)` max.
7. **Wall vents are decals** — e.g. x 590–615, y 400–423 and x 1240–1265: 5 slats drawn straight onto the
   wall with no housing, no shadow, no rim. Fix: 1 px housing + 1 px top shadow.
8. **Console lower body reads empty** — the two dark side boxes and the centre "drawer" (sprite x 28–100,
   y 44–60) are large flat near-black rectangles; a few 1 px warm/cyan specks in the keyboard area
   (`(210,84,56)` x4, `(236,132,85)` x3) read as dirt rather than lit keys.
9. **Rack header/ledger** — 14 px blank top plate, no cable bundle despite the brief, stray dash row at the
   base, and cyan/cyan vs violet/grey LED pairing inconsistency.
10. **Down-scaled catalog check** — `04_mega_catalog_x3` is a 3x of `sprite_x4`-derived art; the hull_frame
    shown there (content y 50–253) does **not** match the assembled rib (best case 40 % of opaque pixels match
    at any integer offset; mismatches are single-ramp-step swaps both ways). The assembly draws ribs from
    stacked 32 px modules (period 32 confirmed at x=8/20/45), so the room is not reproducible from the element
    PNG. Not visible as a defect, but the element/assembly pair is inconsistent — worth reconciling so the
    shipped `hull_frame` is the thing that ships in the room.

---

## 4. Verdict

## **FAIL**

One blocker and four majors remain and are visible to the naked eye in `05`/`06`:

1. the hazard tile is not tileable → 4 stripe breaks across the reactor platform (x 1308/1340/1372/1404);
2. pipes dead-end (vertical run at x 293–320 stopping at y 448; horizontal run ending in a black slot at
   x 666–669);
3. the grate is a 64x32 black patch punched through the deck lip (x 256–319, y 512–543);
4. `grate_fill`/`grate_top` read as noise/corruption rather than grates;
5. cargo_stack still lacks inter-crate shadow and a real hazard stripe (B2 only partially addressed).

Round-2 items that are genuinely resolved and should not be reopened: **B1** (ribs), **M1** (deck
registration), **M2** (accent strips), **M4** (server rack), **M8** (wall variance). **M3** and **M6** are
half-fixed; **M5** and **M7** are not fixed.

---

## 5. Summary

This is a real improvement over round 2: the hull ribs are now honest single ceiling-to-floor columns with a
capital and a plinth and no buried feet or edge cuts, the deck is correctly top-registered with the lit surface
at y=512 and every prop seated on it with a contact shadow, the wall accent strips run hundreds of pixels
without being chopped, the server rack is now a solid readable cabinet, and the wall's most-repeated block has
dropped from ~77 % to 30 % of the field with 73 distinct blocks — plus the whole set is genuinely crisp (24
colors, zero semi-transparent pixels, clean nearest-neighbour previews). What still fails the bar is detail
craft at the contact points: the hazard tile has a 12 px stripe period in a 32 px tile, so the reactor's
hazard platform visibly stutters four times; three vertical pipes stop flat against bare wall at y=448 and the
horizontal runs end in a 4 px black slot; the grate is a 64x32 black patch with a 1 px black border column
plastered through the deck lip, and its lattice texture reads as corrupted data; and the cargo stack, though
now clearly three offset crates, still has no shadow between crates and a 23x6 gold squiggle instead of a
hazard stripe. None of these are hard to fix — a tileable hazard pattern, flange/elbow terminators, a
floor-line grate rebuilt from horizontal bars, and one shadow row plus a real hazard band on the crates — but
as it stands the environment is not shippable, so the verdict is **FAIL**.
