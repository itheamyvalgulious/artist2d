# Acceptance Review — Ship Environment Pack (v4)

Reviewer: independent multimodal acceptance pass
Scope: `output/environment/ship/`, `output/mega/ship/`, `output/showcase/ship/`, `work/review/ship/`
Method: opened every review PNG (00–06), the raw 1x atlases/samples/assemblies, and the raw medium/mega sprites; checked alpha, edge rings, 2x2 repeats, 1x scene coordinates, whole-scene diffs, and the shaders/assembly code for non-1:1 scaling. No assets were modified.

## Verdict

**FAIL** — 1 blocker + 5 majors. PASS cannot be issued.

The alpha/cutout checks pass, but the three platform-step tiles are effectively black voids that turn the centrepiece dais into a hole, and the assembled room has four further coherence failures (hidden door, wall patchwork, non-integer hull stretching, missing contact shadows).

---

## Blockers

### B1 — `deck_step`, `deck_step_left`, `deck_step_right` render as near-black voids; the console dais is a 192×32 black band

- **Files:** `output/environment/ship/tiles/deck_step.png`, `deck_step_left.png`, `deck_step_right.png`; used in `output/environment/ship/tileset_sample.png`, `output/mega/ship/ship_mega_1x.png`, `output/showcase/ship/scene_1x.png`; review cells in `work/review/ship/02_all_tiles_x5.png` (row 0 col 4, row 0 col 5, row 1 col 0) and `work/review/ship/01_tileset_sample_x4.png` (tiles x=11..13, y=5).
- **Element:** the three 32×32 platform-step variants; the raised dais at scene x=480..672, y=480..512 (1x), directly under the console bank.
- **Defect:** rows 4–31 of each step tile are a flat, featureless face: 711 of 896 body pixels are exactly `(8,8,12)` (79.4%), row-mean `(13,13,19)`, only three colours in the whole face, no panel/seam/dither detail. The 4px top lip is the only readable feature. The left/right variants add only a 1px near-white side edge `(214,214,230)`. In the 2×2 repeat the tile is a black grid; in the tiled slice it is a 96×32 black band above the deck; in the whole ship/showcase the dais is 69.3% below L=20 (the deck below is 18.8%), mean L 23.9 vs the deck's 31.0. The console sits on top of this band and reads as floating over a hole. `work/review/ship/MANIFEST.md` calls these "3 real platform-step variants" — they are not real step surfaces.
- **Broken requirement:** "25 tiles that tile seamlessly: floors, walls, ceiling…"; "floors"/platform steps; "one coherent scene"; "no visible seams"; the manifest's own claim of real step variants.
- **Fix:** draw a real step face (recessed panel with 3–4 tone bands, 1px inner outline, dithered lower shadow); make the 2×2 repeat read as a solid, detailed face; keep the walk lip bright and the face dark but not empty.

---

## Majors

### M1 — The only door in the whole ship is fully occluded by a hull rib; the door tile is also too short for the agent

- **Files:** `output/environment/ship/tiles/door.png`; `output/mega/ship/ship_mega_1x.png`, `output/showcase/ship/scene_1x.png`, review 05/06; `work/review/ship/02_all_tiles_x5.png` (door cell; its 2×2 repeat was checked from the raw tile).
- **Element:** door at scene x=12 tiles (384..416), y=14..15 (448..512); hull rib at x=10 tiles (320..448), drawn after the door.
- **Defect:** the door's cyan window colour `(53,162,196)` is absent at the expected scene pixels (405..408, 455..460 and 487..492); the rib is opaque there. The door is 100% hidden in the whole ship and showcase, and the tiled sample does not include it. Separately, the door tile is 32px tall: the agent is 52px tall (bbox height 52), so a single door is 1.6× shorter than the agent. The scene compensates by stacking two door tiles to reach 64px, but each tile carries its own window and its own hazard threshold: `02` shows the single door's threshold, and a 2×2 repeat (checked from the raw tile) gives four thresholds — a 2-tile stack has a hazard threshold across the middle of the opening.
- **Broken requirement:** "DOORS"; "whole ship assembles into one coherent scene"; "showcase… correct scale"; doors must be usable at the agent's scale.
- **Fix:** provide a purpose-built 32×64 door pair (top/header and bottom/threshold, no duplicated window/threshold) or a 32px hatch explicitly scaled to the agent; place the door in a clear bay not covered by a rib; prove it in 01 and 05.

### M2 — Whole-ship wall is a diagonal patchwork of framed panels / flat panels, with abrupt density jumps

- **Files:** `output/mega/ship/ship_mega_1x.png`, `output/showcase/ship/scene_1x.png` (05/06); uses `wall`, `wall_flat`, `wall_light`, `wall_violet`; `work/review/ship/02_all_tiles_x5.png` for the tiles.
- **Element:** wall clusters at x≈5..9, y≈4..6; x≈14..20, y≈8..10; x≈26..32, y≈4..6; x≈38..43, y≈4..6 (tile coords, 1x).
- **Defect:** the assembly selects `wall`/`wall_flat`/`wall_light`/`wall_violet` with `(x+y)%4` inside rectangles. Inside those rectangles the large framed `wall` panel appears as a diagonal checker among the flat panels; the framed panels are empty recesses and read as repeated "picture frames", while outside the rectangles the wall is plain. The detail density changes abruptly at every cluster edge — a 32px grid of bright framed squares next to near-empty wall. This is the largest "mismatched density" area of the pack. The `wall_flat` tile also carries the 1px status dot at (29,3) (see m1), which produces a regular cyan speck grid.
- **Broken requirement:** "no mismatched density"; "one unified… pixel density"; coherent wall.
- **Fix:** use the framed panel as an occasional accent (single row/column or a deliberate frame around a viewport/door), not a diagonal checker; keep the flat panel dominant; blend cluster edges with trim.

### M3 — The 448px hull ribs are built by non-integer nearest-neighbour stretching and repeated with inconsistent joins

- **Files:** `output/mega/ship/ship_mega_1x.png`, `output/showcase/ship/scene_1x.png` (05/06); raw `output/mega/ship/elements/hull_frame/sprite.png` (118×203); `environment/ship_assembly.py` `_rib_module`.
- **Element:** the five ceiling-to-floor ribs at x=0, 10, 22, 34, 44 tiles, y=64..512 (128×448 each).
- **Defect:** the raw 118×203 rib is resized 118→128 horizontally for the caps, 118×103→128×116 for the mid, and the mid is composited three times. The factors are 1.085× and 1.126× — not integer — so the pixel grid is no longer 1:1: some rows/columns are duplicated unevenly, and the shaft pixels are visibly larger than the cap pixels. The code draws 1px black join lines at y=166 and y=282 only (not at 50 or 398), so two of the four joins are marked and two are not. The ribs are a dominant structural element; their pixel density no longer matches the 1:1 tiles/props.
- **Broken requirement:** "sharing… pixel density"; "one unified"; pixel-art grid integrity.
- **Fix:** author a true 128×448 rib (or integer 2× segments) and repeat it without resampling; keep the join treatment consistent at every module boundary.

### M4 — The three medium structures do not share a density: server rack is a flat deterministic cabinet against the AI/dithered console and cargo

- **Files:** `output/environment/ship/props/server_rack/sprite.png` (55×105), `console_bank/sprite.png` (102×59), `cargo_stack/sprite.png` (59×87); `work/review/ship/03_medium_catalog_x3.png`; 05/06.
- **Element:** the server rack, especially the large body between the top cap and the bottom base.
- **Defect:** the server rack is clean, deterministic, regular horizontal stripes with sparse chips; the console and cargo carry 1px generated noise, dither, scuffs and irregular highlights. At 3× the server looks like a different art pass: flat bands, no dithering on its large faces, no edge wear, while the console is a dense field of 1px screen detail and the cargo is scuffed. The three are individually readable but not one medium family.
- **Broken requirement:** "exactly 3 medium… sharing palette, light direction, outline weight, pixel density".
- **Fix:** give the server a matching 1px dither/wear pass and irregular panel breaks, or regenerate it in the same pass as the console/cargo.

### M5 — Contact shadows are missing on the reactor and invisible on the console, and the rest are only a 2px line

- **Files:** `output/mega/ship/ship_mega_1x.png`, `output/showcase/ship/scene_1x.png` (05/06); `environment/ship_assembly.py` `_shadow`; review 05/06.
- **Element:** reactor at x=1285..1403, y=372..512; console at x=525..627, base y=480; cargo x=162..221; server x=900..955; agent x=242..269, base y=512.
- **Defect:** the reactor has **zero** contact-shadow pixels in rows 512–513 across its full footprint; the deck top is still the untouched bright lip `(155,155,176)`. The console's 2px shadow is drawn at y=480 on the black dais, so it is invisible. The cargo and server get only a 2px dithered line (50/118 and 47/110 dark pixels), and the agent gets 23 pixels over 2 rows. There is no multi-row footprint with a falloff under any object; the reactor and console read as pasted.
- **Broken requirement:** "dithered contact shadows with a real contact footprint"; "grounded objects"; "showcase… contact shadow, not floating".
- **Fix:** add a 3–5px wide, dithered, left/top-light-consistent shadow under the reactor and console (on the deck, not on the black face) and widen the cargo/server/agent footprint; ensure the shadow is visible against the surface it lands on.

---

## Minors

| ID | File / element | Defect | Broken requirement |
|---|---|---|---|
| m1 | `tiles/wall_flat.png` (and every `wall_*`, `pipe_*`, `vent` derived from it), 1px pixel at (29,3) | The deliberate "status" pixel repeats at the same spot on every tile; 01/05 show a regular cyan speck grid across the wall, reading as stray pixels. | "One unified" clean tile set; no stray artifacts |
| m2 | `tiles/window.png`, lower-left pane | The 5×5 planet circle plus the 9px ring reads as a purple plus/crosshair, not a planet; 02 window, 01 sample, 05 windows. | "Readable windows/emissives" |
| m3 | `tiles/hazard.png`, 2×2 repeat | 2px light top rows are copied to the bottom by `seamless()`, so a 2×2 repeat has a light band every 32px; only the single-row use in 05 hides it. | "No visible seams" when the hazard is stacked |
| m4 | `tiles/grate_fill.png`, `grate_top.png`, vertical ribs at x=7/24 | Rib gaps alternate 17px/15px; the 2×2 repeat shows uneven spacing. | Seamless grate / consistent density |
| m5 | `tiles/light_strip.png`, top 6 rows | The fixture copies the ceiling tile's top band, giving each light a gray cap that duplicates the ceiling's bright edge; 05 fixtures read as boxes with a bright lid. | Clean ceiling/fixture integration |
| m6 | `tiles/ceiling.png`; `ceiling_tile = deck_top(flipud(deck))` | The ceiling is a vertically flipped deck; its bright walk lip is at the top/outside of the room and it shares the deck's plate motif, so the top and bottom of 05 read as the same surface. | "Light direction"; readable ceiling |
| m7 | `showcase/ship/scene_1x.png`; agent feet at y=512 | The agent's contact shadow is only 23 dark pixels over 28px width and 2 rows tall; it reads as a dotted line, not a contact footprint. | "Dithered contact shadows with a real contact footprint" |
| m8 | `showcase/ship/scene_1x.png` / 06; agent at x=242 (1x) | The 28×52px agent is at the far left beside the cargo, not the centrepiece; the showcase is 05 plus a tiny figure. | Showcase composition/scale presentation |
| m9 | `work/review/ship/02`, `03`, `04` | 02's tiles are 200×200 (6.25×, labelled x5); 03's console is 500×289 (4.90×), cargo 339×500 (5.75×), server 262×500 (4.76×); 04's hull 290×500 (2.46×), viewport 500×393 (4.46×), reactor 421×500 (3.57×). Non-integer nearest rescaling breaks the 1px grid and changes relative scale (viewport appears 1.72× the hull width; raw widths are 112 vs 118). | "Pixel density"; valid 03/04 review evidence |
| m10 | `mega/ship/ship_layout.json`; `showcase/ship/report.json`; `environment/ship/report.json`; `mega/ship/report.json` | Layout lists two characters (idle x=7, shoot2 x=30); 06 has only the idle at x=7. Showcase report says "agent idle/shoot2"; environment report says `medium_catalog_size: 10` and mega report says `mega_catalog_size: 20` while only 3+3 were generated. | Accurate delivery metadata |
| m11 | `environment/ship/tiles/wall_plain.png`, `wall_plain_x8.png` | Orphan 26th structural tile not referenced by `tileset.json`, `tileset.png` or 02; stale file in the shipped tiles folder. | "Exactly 25 tiles"; clean delivery |
| m12 | 05/06 composition | Deck front is 4 tiles (128px) of mostly empty black; right cargo is a horizontal flip (mirrored labels/hazard); reactor hazard extends ~37px left and ~5px right; viewport top has a floating cyan bar and nearly black glass; alternating hull ribs mirror cyan/violet accents. | "One coherent scene" / consistent scale and lighting |

---

## Per-item checklist

### 25 tiles (02 atlas / 2×2 repeats / 01 context)

| # | Tile | 2×2 / edges | Result | Note |
|---|---|---|---|---|
| 1 | ceiling | exact wrap both axes; 2×2 continuous | PASS | m6: flipped deck, bright lip at top/outside |
| 2 | deck_fill | exact X wrap; 2×2 plate seams | PASS | very dark fill, intentional |
| 3 | deck_left | side edge; 2×2 repeats bright side | PASS | edge tile, not a fill; 2×2 shows the cap |
| 4 | deck_right | side edge | PASS | as above |
| 5 | **deck_step** | flat black face; 2×2 black grid | **FAIL** | **B1** |
| 6 | **deck_step_left** | flat black face + 1px white side | **FAIL** | **B1** |
| 7 | **deck_step_right** | flat black face + 1px white side | **FAIL** | **B1** |
| 8 | deck_top | exact X wrap; 2×2 top lip | PASS | top-surface tile; correct use is one row |
| 9 | deck_top_left | edge + top; 2×2 | PASS | edge tile |
| 10 | deck_top_right | edge + top; 2×2 | PASS | edge tile |
| 11 | door | vertical wrap; 2×2 = four doors, four thresholds | PASS (tile) / **M1 in context** | 32px door; 2-tile stack duplicates threshold/window; hidden in 05 |
| 12 | grate_fill | exact both axes; 2×2 continuous | PASS | m4 uneven 17/15 rib spacing |
| 13 | grate_top | exact both axes | PASS | 1px inset frame reads as a rib at the seam |
| 14 | hazard | exact both axes; 2×2 light bands | PASS | m3 light band every 32px when stacked |
| 15 | light_strip | fixture; H seam 152 by design | PASS | m5 gray cap duplicate |
| 16 | pipe_h | exact both axes | PASS | joints/cyan bands read |
| 17 | pipe_v | exact both axes | PASS | — |
| 18 | vent | framed feature; 2×2 four vents | PASS | not a fill, frame is intentional |
| 19 | wall | exact both axes; framed recess | PASS | m1 dot; M2 use in 05 |
| 20 | wall_flat | exact both axes; plain panel | PASS | m1 dot |
| 21 | wall_flat_light | exact both axes; cyan strip | PASS | — |
| 22 | wall_flat_violet | exact both axes; violet strip | PASS | — |
| 23 | wall_light | exact both axes; framed + strip | PASS | — |
| 24 | wall_violet | exact both axes; framed + strip | PASS | — |
| 25 | window | framed feature; 2×2 four windows | PASS | m2 planet/cross |

Tile count: **22 PASS, 3 FAIL** (the three step tiles). The seam/wrap test is clean for every repeating fill (ceiling, deck_fill/top, wall*, pipe*, grate*, hazard); the feature tiles are intentionally framed; the 2×2 sheets in 02 confirm.

### 3 medium structures

| Item | File | Result | Note |
|---|---|---|---|
| console_bank | `output/environment/ship/props/console_bank/sprite.png` | PASS (asset) | side housings and 1px outline are complete; **M5** invisible shadow on the black dais; B1 makes its base/contact unreadable |
| cargo_stack | `output/environment/ship/props/cargo_stack/sprite.png` | PASS (asset) | 1px outline closed top/bottom; **m12** right copy is flipped |
| server_rack | `output/environment/ship/props/server_rack/sprite.png` | **FAIL (M4)** | complete cutout and outline, but flat deterministic density vs console/cargo |

### 3 mega elements

| Item | File | Result | Note |
|---|---|---|---|
| hull_frame | `output/mega/ship/elements/hull_frame/sprite.png` | PASS (raw) / **FAIL in 05 (M3)** | raw 118×203 complete with 1px outline; assembly non-integer stretch 118→128 / 103→116, 3 mid copies, joins at 166/282 only |
| viewport | `output/mega/ship/elements/viewport/sprite.png` | PASS | clean outer dark ring; **m12** top cyan bar + dark glass |
| reactor_core | `output/mega/ship/elements/reactor_core/sprite.png` | PASS (raw) / **FAIL in 05 (M5)** | complete cutout; zero contact-shadow pixels; hazard platform asymmetric |

### Whole ship — `mega/ship/ship_mega_1x.png` / review `05_whole_ship_x2.png`

**FAIL.** The room assembles and the palette/light/outline read consistently, but:

- **B1** dais is a 192×32 black band under the console.
- **M1** no visible door anywhere; the 05 door at (384..416, 448..512) is behind the rib at 320..448.
- **M2** wall is a diagonal framed/flat patchwork; density jumps.
- **M3** five 448px ribs are non-integer rescaled.
- **M4** server rack's flat density breaks the medium family.
- **M5** reactor has no contact shadow; console shadow invisible.
- **m12** floor front is 4 empty tiles, right cargo flipped, reactor hazard asymmetric, alternating accent sides.

The five ribs, ceiling, wall, pipes, grate, windows, console, cargo, server and reactor all appear in one side-view hall and share the palette; that part of the requirement is structurally met, but the defects above prevent acceptance.

### Showcase — `showcase/ship/scene_1x.png` / review `06_showcase_x2.png`

**Scene: FAIL** (inherits B1 + M1/M2/M3/M4/M5 from 05).
**Agent-specific checks:**

| Check | Result | Evidence |
|---|---|---|
| Agent exactly once | **PASS** | whole-scene diff vs 05 = 514 px, one cluster only, bbox (242,460)–(269,513) |
| Standing on deck | **PASS** | feet at y=512 = deck top; pasted from bbox bottom 62 at y=450 |
| Correct scale | **PASS** | 52px tall vs 32px panels / 59px console; the 32px door is a separate M1 issue |
| Contact shadow | **PASS (minimal) / m7** | 23 dithered pixels in rows 512–513, 2px tall, no falloff |
| Not floating | **PASS** | base aligned to the deck line; no gap |

### Review packet

| Image | Result | Note |
|---|---|---|
| 00_tileset_x8 | **FAIL** | contains B1 step tiles |
| 01_tileset_sample_x4 | **FAIL** | B1 step band at x=11..13, y=5; no door/ceiling/pipes/deck-edge in this slice |
| 02_all_tiles_x5 | **FAIL** | B1 cells; m1 dots; m2 window; m3/m4/m5 minors; m9 actual 6.25× (200px) not x5 |
| 03_medium_catalog_x3 | PASS (assets) / M4 | m9 non-integer scales and distorted relative scale; console/cargo complete |
| 04_mega_catalog_x3 | PASS (assets) | m9 non-integer scales and distorted relative scale; m12 viewport |
| 05_whole_ship_x2 | **FAIL** | B1, M1–M5 |
| 06_showcase_x2 | **FAIL** | scene inherits; agent checks pass |

---

## Evidence summary

- **Alpha/cutout:** all 6 medium/mega sprites and the agent have alpha in {0,255}; 0 magenta pixels; 0 semi-transparent pixels. Each silhouette is closed with a 1px near-black outline (hull top/bottom rows are `(8,8,12)`; the console has dark side housings; the cargo, server, reactor and viewport have closed edges; a few highlight pixels touch the outer edge but no cut span was found). **No clipped-edge defect was found** — the tight bbox is a tight crop, not a cut. This requirement passes.
- **Palette/outline/light:** report palette violations 0 for tiles, sample, catalogs, assembly, showcase; one 1px near-black outline weight throughout; top-left bevel logic on wall recesses and top-lit deck/prop caps (the only inverted element is the ceiling's top lip, m6).
- **Seams:** exact wrap (0.00 mean edge difference) on the repeating axes of ceiling, deck_fill, deck_top, wall, wall_flat, wall_flat_light, wall_flat_violet, wall_light, wall_violet, pipe_h, pipe_v, grate_fill, grate_top, hazard. Feature tiles are framed by design. The three step tiles are the only "repeat" failure (B1).
- **Step stats:** body 79.4% `(8,8,12)`, 3 colours, mean L 13.2/13.2/18.6; dais 69.3% L<20 vs deck 18.8%; 192×32 in 05.
- **Door occlusion:** door cyan `(53,162,196)` absent at (405..408,455..460)/(487..492); rib alpha is opaque there; no door pixels survive in 05/06.
- **Shadows:** reactor 0 dark pixels in rows 512–513 across 118px; cargo 50, server 47, agent 23 (2px dither); console shadow at y=480 on black dais.
- **Hull:** raw 118×203; assembled 128×448; caps 118→128; mid 103→116 ×3; non-integer nearest; join lines at y=166 and 282 only.
- **Catalog scale:** 02 tiles 200×200 = 6.25× (label x5); 03 console 500×289 / cargo 339×500 / server 262×500 (4.90/5.75/4.76×, label x3); 04 hull 290×500 / viewport 500×393 / reactor 421×500 (2.46/4.46/3.57×, label x3).

## Exit criteria

1. Replace the three step tiles with real detailed faces and rebuild 01/05/06; the dais must not read as a hole.
2. Make the door visible in 05 and usable at 52px agent scale (32×64 pair, no duplicated threshold); re-render 05/06.
3. Replace the wall's diagonal framed/flat checker with deliberate accents; keep density uniform.
4. Add a true 128×448 rib (integer scale, consistent joins).
5. Bring the server rack's density in line with the console/cargo.
6. Add visible 3–5px contact shadows under the reactor, console, props and agent.
7. Regenerate 02/03/04 at integer scale with preserved relative scale; fix the stale metadata and remove the orphan `wall_plain` files.
