# Ship environment — independent art review v1

Reviewer: `ship-review-v1` (independent multimodal reviewer, did not generate these assets, no code tests run, no assets modified).
Scope read-only. Evidence is taken from the shipped PNGs plus pixel probes on the same files.

Scene coordinate system used below: **1x** = `ship_mega_1x.png` / `scene_1x.png`, 1536×640 px = 48×20 tiles of 32 px, floor surface at **y = 512** (row 16). Files `05`/`06` are exact 2× nearest upscales of these; `00`/`01`/`02`/`03`/`04` are review sheets.

## 1. Coverage — every file inspected

### 1.1 Required review packet (7/7 read at full sheet resolution)

| # | File | What it shows | Verdict |
|---|---|---|---|
| 1 | `work/review/ship/00_tileset_x8.png` | complete 22-tile atlas, x8 | **FAIL** — atlas is complete and technically clean, but `pipe_h`/`pipe_v` are unreadable cable mush and the four "panelled wall" tiles are an ambiguous, muddy door-jamb fragment; no true platform edge exists |
| 2 | `work/review/ship/01_tileset_sample_x4.png` | tiles in context, x4 | **FAIL** — proves a visible 32 px lattice (identical cell repeated 70×), feature tiles only shown as isolated squares, no deck edge / light strip / grate junction tested |
| 3 | `work/review/ship/02_all_22_tiles_x5.png` | all 22 tiles labelled, x5 | **FAIL** — coverage is complete (22/22, labels match), but it confirms the same tile defects as `00`: `wall`, `wall_light`, `wall_plain`, `wall_violet` are near-duplicates (128–256 differing px) of one broken motif |
| 4 | `work/review/ship/03_medium_catalog_x3.png` | console_bank, cargo_stack, server_rack, x3 | **FAIL** — console reads well; `cargo_stack` is not a cargo stack; `server_rack` has floating side tabs and a duplicated hull-lattice column |
| 5 | `work/review/ship/04_mega_catalog_x3.png` | hull_frame, viewport, reactor_core, x3 | **FAIL** — viewport is the best asset but uses soft nebula shading; hull_frame is noisy and carries 50 px of dead top padding; reactor_core is soft-gradient/asymmetric (melted coils, ambient violet blobs) |
| 6 | `work/review/ship/05_whole_ship_x2.png` | whole-ship mega assembly, x2 | **FAIL** — hull ribs neither reach the ceiling nor the floor, mid-wall "seam bands" read as an accidental second floor, one window is 100 % hidden, pipe runs end in mid-air, right edge cut |
| 7 | `work/review/ship/06_showcase_x2.png` | assembly + agent character, x2 | **FAIL** — everything from `05`, plus the character is composited inside the console footprint and uses a firing pose at a console |

### 1.2 Native-resolution files opened to resolve details (no sampling)

| File | Why opened |
|---|---|
| `output/environment/ship/tiles/*.png` (all 22 canonical: ceiling, deck_fill/left/right/top/top_left/top_right, grate_fill/top, hazard, light_strip, pipe_h, pipe_v, vent, wall, wall_flat, wall_flat_light, wall_flat_violet, wall_light, wall_plain, wall_violet, window) | per-tile pixel inspection, alpha/colour/palette probes, pairwise diff |
| `output/environment/ship/props/console_bank/sprite.png` | silhouette, bottom-left streaks |
| `output/environment/ship/props/cargo_stack/sprite.png` | silhouette / readability |
| `output/environment/ship/props/server_rack/sprite.png` | floating tabs, lattice column |
| `output/mega/ship/elements/hull_frame/sprite.png` | dead top padding, seam caps, conduit |
| `output/mega/ship/elements/viewport/sprite.png` | frame shading, starfield |
| `output/mega/ship/elements/reactor_core/sprite.png` | gradient ramps, blobs, symmetry |
| `output/mega/ship/ship_mega_1x.png` (1536×640) | whole assembly at native size |
| `output/showcase/ship/scene_1x.png` (1536×640) | showcase at native size |
| `output/character/agent/idle/frames/frame_00.png`, `shoot2/frames/frame_02.png` | scale/grounding/padding |
| `output/environment/ship/tileset.png`, `output/mega/ship/ship_layout.json`, `output/mega/ship/report.json`, `output/showcase/ship/report.json`, `environment/ship_assembly.py` | placement cross-check only (never used as evidence of quality) |

Mechanical facts verified on the shipped files: 0 magenta / pink pixels, 0 alpha holes in any of the 22 tiles, 0 off-palette pixels (all colours inside the 64-colour palette), 36 unique colours in the whole 1x scene, x2 previews are nearest-neighbour (no blur). **Pixel hygiene itself passes; the failures below are design, placement and readability failures.**

## 2. Findings by category

### 2.1 Tiles (22/22 present, all 32×32, all side-view, all opaque)

Good: `ceiling`, `deck_*`, `grate_fill/top`, `hazard`, `vent` are clean, flat, and readable. `hazard` tiles horizontally without a seam, `vent` reads instantly, `grate_top` has a convincing lip.

Problems:
- The whole wall family is **one material plus bevels**. `deck_left`, `deck_right`, `deck_top`, `deck_top_left`, `deck_top_right` differ from `deck_fill` by only **84–172 px, confined to a 3 px border band** — they are bevel variants, not platform-edge pieces. There is no side face, no underside, no end cap anywhere in the atlas, and **the assembly never places a platform edge**, so the "deck/platform edge" requirement is untested and effectively unmet.
- `wall`, `wall_light`, `wall_plain`, `wall_violet` are the same motif: dark jamb → light slab cut off by the tile edge → violet band, plus a black notch at the right edge. They differ by 128–256 px. The slab is cut by the tile boundary, so tiling them produces a repeating "broken doorway" every 32 px. `wall_plain` is not plain. They are also the only tiles with organic purple/cyan mottling, i.e. a different rendering language from the flat plates.
- `pipe_h` / `pipe_v` (14 colours each, the same artwork rotated) do not read as pipes at 1×: they read as a jumble of 1 px cyan/violet dashes. They are the busiest, brightest tile and are repeated over ~100 cells in the assembly, so the loudest thing in the room is also the least legible.
- "Light strips" are wrong in kind: `wall_flat_light` adds one horizontal dash at the top of the tile, so stacking it vertically yields a **ladder of dashes**, not a vertical strip. The dedicated `light_strip` tile (a 1 px cyan rule in a flat plate, 3 colours) is **never used** in the assembly.
- `window` is a bare starfield square with a 3 px flat rim: no housing, no inset, no glass highlight; it reads as a hole or a sticker, and it uses a different starfield from `viewport` (pure black + 2 px stars vs. navy nebula).
- Single cyan pixel at the top-right of `deck_fill`/`grate_*`/pipe tiles repeats every 32 px, producing dotted cyan lines across the floor and along bands — a tiling tell, not a rivet.

### 2.2 Medium structures

- **console_bank (128×64, content 102×59)** — the strongest asset: three monitors, desk, cabinets, correct grounding, dark plinth. Weaknesses: 4–5-tone cyan monitor glow ramps are more "rendered" than the 4–6-colour tiles; 1 px diagonal violet/cyan streaks hang inside the lower-left body (sprite x≈18–34, y≈44–60) like drips; one stray orange pixel floats in the black body at ≈(24,52).
- **cargo_stack (64×96, content 57×70)** — **not a cargo stack**. It is a flat rectangle of panels with a muddy violet "window" and side rails; no crate lid edges, no stacking lines, no volume, no value contrast. Its palette and mottling are the same as `wall_plain`, so in the assembly it is indistinguishable from a wall panel (see R5 crop at x≈1440 and the left one at x≈128).
- **server_rack (64×112, content 58×100)** — reads as a server cabinet, but its right third is an open X-lattice with see-through holes that is a **direct copy of the hull_frame motif**, so the prop collides with the room's structural language and reads as "cabinet glued to a rib". It also has two grey tabs protruding into transparency at mid-height (sprite x≈3–7 and x≈57–60) that read as broken handles/floating fragments.

### 2.3 Mega elements

- **hull_frame (128×256, content 118×203 at y 50–252)** — good rib design (top flare, base flare, X-braces, conduit), but: 50 px of empty padding at the top and 3 px at the bottom mean the sprite is not a ceiling-to-floor module even though it is sold as one; the metal carries a lot of 1 px speckle noise (5.8 % isolated pixels) instead of crisp clusters; the conduit runs on one side only, so mirroring (used for the lower module) makes the bundle jump ~30 px sideways — visible in the assembly at y≈352.
- **viewport (128×96)** — best mega asset: complete, readable, correct frame/sill. But the starfield contains a painted navy nebula and the frame uses 5 grey tones with dithered transitions; next to the flat tiles it looks like a downscaled render pasted on the wall. Placement gives it no wall cut-out, mounting bracket, or recess, so it is flush-stuck to a flat plane (the pipe column behind it dies at its lower-left corner with no connector).
- **reactor_core (128×192)** — the biggest style break: the cyan rings are soft 4-step glow ramps and there are large organic violet blobs with no hard outline behind the coils; the left and right sides are asymmetric (big violet blob + low pipe loop vs. high pipe loop). It reads as melted/organic geometry rather than "thick pipes and cable bundles", and it is the clearest violation of "flat three-tone shading, no gradients".

### 2.4 Whole-ship assembly (`05`)

With `ship_layout.json` + `ship_assembly.py` cross-checked against pixels:

- Ribs are placed at x = 0, 320, 704, 1088, 1472, with a 128×256 module at **y = 96** and a second at **y = 352**.
  - Visible content of the top module starts at **y = 146**, i.e. **50 px below the ceiling band** (which ends at y = 96) → every rib hangs in mid-air at the top.
  - The bottom module's content ends at **y = 604**, i.e. **92 px below the floor line (512)** and is buried by the deck → the rib's base plate is destroyed and the braces are cut by the floor.
  - Net result: the "ceiling-to-floor structural rib" is neither, in 10/10 placements.
- Because the two modules are stacked butt-to-butt, the top module's base flare, the pasted `pipe_h` seam band (row 11, y 352–384) and the bottom module's top flare form **two facing brackets with a bright band between them** at mid-height, five times across the room. It reads as an accidental mezzanine/ledge, and the band is louder than the rib and ends with a hard vertical cut exactly at the rib edge.
- The rib at x = 1472 (content 1477–1594) is **cut 58 px by the canvas**; the left rib at x = 0 is complete → asymmetric framing.
- Lower `pipe_h` runs are pasted at y = 448 in the ranges [0,320), [448,640), [928,1216), [1408,1536): **six hard vertical terminations in mid-wall**, no elbows, caps or brackets.
- `window` at tile (12,6) = (384,192) is **completely hidden** behind rib@320 (content 325–442 × 146–604) — a placed tile that is never visible. The only visible window is the bare 32 px square at (896,192).
- Both "detailed panel" clusters are wasted: the 5×3 `wall` cluster at 704–864 × 256–352 is **~73 % covered** by rib@704 (content 709–826), and the 4×3 cluster at 992–1120 × 224–352 is **~71 % covered** by the server (1024–1088) plus rib@1088 (1093–1210). The wall therefore renders as **~95 % one flat tile**.
- Repetition is structural, not stylistic: 624 wall cells of the same tile (verified byte-identical: sample cell diffs = 0), the same 1 px dark/light bevel at every 32 px boundary, 5 identical ribs at a fixed 10/12/12/12 tile pitch, 2 identical ceiling tiles × 48 columns, 4 identical deck bands. No ceiling fixture, no door/hatch, no foreground layer, no depth cue: at 1st read it is a decorated flat wall, not a room.
- Grounding as such is correct: every prop bottom lands on y = 511 (1 px pad), contact shadows fall on the deck, floor line is continuous at y = 512 (interrupted only by the 2-tile grate at x 256–320 / 1216–1280).

### 2.5 Showcase (`06`)

`05` vs `06` differ by exactly two character instances (1596 px, x 780–981):
- **shoot2 (flipped) at x = 768**, pixel bbox **780–829 × 453–510**, sits **inside** the console footprint **736–864 × 448–512**: the body covers the centre monitor and desk, and the firing arm/weapon overlaps the desk edge. It reads as a figure glitched into the furniture, not an operator.
- **idle at x = 928**, bbox 938–981 × 453–515, is grounded (feet at 511, shadow on the deck) and correctly scaled (≈60 px ≈ 1.9 tiles ≈ 1.9 m at 32 px/m), but stands in front of a blank wall with nothing to interact with.
- Two agents, one firing at nothing, no props/effects → reads as an animation test planted in the room rather than a showcase.

### 2.6 Style unity

Present and on-brief: dark gunmetal/navy plates, cyan accents, violet accents, warm hazard gold, 1 px near-black outlines on all props/mega, hard pixel edges, no AA, no off-palette colour.
Broken: (a) detail density is split — tiles are 4–6 colours / flat, props are 21–29 colours with speckle and 4–5-tone glow ramps; (b) the reactor and viewport use soft ambient light and nebula, which the brief forbids; (c) two different starfields (window vs. viewport) and three different "panel" languages (flat bevel plate, muddy doorway fragment, cable mush) in one room.

### 2.7 Pixel quality

No anti-aliasing, no blur, no nearest-upscale artefacts, no text/watermarks in any asset (only the review sheets carry labels), no malformed/magenta pixels, no visible transparency holes. Remaining quality issues are the 1 px speckle "sandpaper" texture on `hull_frame`/`server_rack`/`console_bank` and the stray/dangling 1 px strands noted above.

## 3. Issue list

| ID | Sev | File / element | What is visibly wrong | Concrete fix |
|---|---|---|---|---|
| B1 | **BLOCKER** | `05`/`06`, all 5 hull ribs | Rib content starts at y=146 (50 px below the ceiling band at y=96) and ends at y=604 (92 px below the floor at y=512, buried by the deck). The room's structural rib is neither ceiling-mounted nor grounded; base plates are gone and braces are sliced by the deck. | Trim the 50 px dead top pad of `hull_frame`, then place module A at y=0 and module B at y=256 so the pair fills 0–512 exactly with the base flare sitting on y=512. Keep a ≤4 px splice collar at y=256. |
| B2 | **BLOCKER** | `06`, shoot2 character | Character bbox 780–829 × 453–510 lies inside console 736–864 × 448–512: body covers the centre screen and desk, weapon overlaps the desk edge. | Move to x≈880 (right of the console, console ends at 864) or x≈700; use `idle`/`shoot2` facing away from the desk; keep a ≥8 px gap between sprite bbox and prop bbox. |
| M1 | MAJOR | `05`/`06`, rib at x=1472 | Rib content 1477–1594 is cut 58 px by the 1536 canvas; the left rib is whole, so the framing is lopsided. | Move this rib to x=38 tiles (1216) and add a 4-tile margin, or widen the room to 52 tiles and keep all elements inside a 4-tile gutter. |
| M2 | MAJOR | `05`/`06`, all 5 ribs, y=352 | `pipe_h` seam cover (row 11) + two facing flares read as a bright horizontal shelf crossing the rib; the band ends with a hard vertical cut at the rib edge. On ribs x=320 and x=1088 the mirrored lower module makes the central conduit jump ~30 px sideways at the same height. | Delete the band; make the rib a single 16-tile-tall module (or two variants that splice at a bolted 2 px collar that terminates inside the rib silhouette). Never mirror the module that carries the conduit. |
| M3 | MAJOR | `05`/`06`, y=448 | Four horizontal pipe runs end mid-wall at x=320, 448, 640, 928, 1216, 1408 with square cuts and no cap. | Terminate every run against a rib, a vertical conduit or a wall bracket; otherwise add a 2-tile elbow/end-cap tile. |
| M4 | MAJOR | `05`/`06`, window tile (12,6) | The window is 100 % occluded by rib@320 — a placed tile that never shows. The only visible window (896,192) is an unframed 32 px starfield square with a flat 3 px rim. | Move windows to non-occluded cells (e.g. tiles 13–14 and 29–30 at row 6/9) and build them as a 2×2 framed porthole cluster with a recessed rim, bolts and a 1 px inner shadow. |
| M5 | MAJOR | `05`/`06`, wall detail clusters | Cluster at 704–864 × 256–352 is ~73 % behind rib@704; cluster at 992–1120 × 224–352 is ~71 % behind the server (1024–1088) and rib@1088. The wall therefore renders as one tile everywhere. | Move clusters into clear wall bays (e.g. 27–30 above the console, 14–18 left of the viewport) and make them 6 tiles wide so they read as a distinct bay, not a patch. |
| M6 | MAJOR | `05`/`06`, whole wall/ceiling/floor | Byte-identical `wall_flat` in all 624 cells with the same 1 px bevel and the same speckle → a visible 32 px lattice; 5 identical ribs at a fixed pitch; 2 identical ceiling tiles ×48. The brief's "enough variety" bar is not met. | Add a second flat wall variant with the bevel offset (and one seamless no-bevel fill), seed a 3–4 tile mix; add a rib variant without conduit and stagger spacing (0, 9, 21, 33, 45); add a ceiling light fixture every ~8 tiles and a door/hatch. |
| M7 | MAJOR | `cargo_stack` | Reads as a wall panel: 57×70 rectangle of panels, no crate lid edges, no stacking lines, no silhouette change against `wall_plain`/`wall_flat`. In `05`/`06` it is indistinguishable from the wall. | Rebuild as 2–3 offset crates: visible lid planes, 1 px outline, 3-step value contrast (top light, front mid, side dark), stencil marks; or drop it from the assembly. |
| M8 | MAJOR | `reactor_core` | Soft 4-step cyan glow rings, large organic violet blobs with no outline, asymmetric left/right — reads as melted/airbrushed vs. the flat tiles. | Re-cut the rings as 2 hard bands (bright core + 1 px darker rim) with no falloff; replace the violet blobs with hard-edged coil plates with 1 px outline; make the element bilaterally symmetric. |
| M9 | MAJOR | `server_rack` | Right third is a see-through X-lattice copied from `hull_frame`; grey tabs protrude into transparency at mid-height (sprite x≈3–7, x≈57–60); the silhouette reads as two objects. | Replace the lattice with louvre/vent slots inside a solid 1 px-outlined rectangle; delete the protruding tabs or make them full-width mounting brackets. |
| M10 | MAJOR | tileset, `deck_left/right/top*` | Edge variants differ from `deck_fill` by only 84–172 px in a 3 px band; there is no side face, underside or cap, and no platform edge appears anywhere in `05`/`06`. | Author real edge tiles: outer 2 px cap, 6 px side face in a darker tone, and a 1 px dark underside; demonstrate a raised platform in `01` and in the room. |
| m1 | MINOR | `01` sample | 14×5 identical wall cells; only 3 feature tiles shown as isolated squares; no grate/light-strip/deck-edge/hazard junction tested in context. | Build the sample as a small room slice: wall + wall_light column + vent + window + grate + deck_top/edge + hazard riser + light strip. |
| m2 | MINOR | `wall_flat_light` / `wall_flat_violet` | Horizontal dash per tile → vertical runs become a ladder of dashes, not a light strip. `light_strip` is never used. | Add vertical strip top/mid/bottom tiles (or a 1 px vertical core in the flat tile) and use `light_strip` for the horizontal runs. |
| m3 | MINOR | `wall`, `wall_light`, `wall_plain`, `wall_violet` | Four near-duplicate "broken jamb" tiles (diff 128–256 px); `wall_plain` is not plain; organic mottling is unique to these tiles. | Keep one bay/hatch motif and drop the other two; rename to `wall_bay_*`; flatten the mottling to 3 tones. |
| m4 | MINOR | `pipe_h` / `pipe_v` | 14-colour 1 px cable mush; unreadable as pipes at 1×; repeated over ~100 cells. | Redraw as 2–3 cylinders: 1 px highlight, 3-wide body, 1 px dark underside, explicit joints every 16–32 px; reduce to 6 colours. |
| m5 | MINOR | `deck_*`, `grate_*`, `pipe_*` | One cyan pixel at the top-right of every tile → dotted cyan lines every 32 px across floor and bands. | Remove the accent pixel or make it a 2×1 rivet that varies between variants. |
| m6 | MINOR | `console_bank` bottom-left | 1 px diagonal violet/cyan strands (sprite x≈18–34, y≈44–60) and one stray orange pixel (≈24,52) inside the body. | Erase the strands and the stray pixel; keep the body 1 px-outlined and flat. |
| m7 | MINOR | `05`/`06`, hazard bands | Row-15 hazard starts/ends mid-wall with square cuts; the y=544 floor hazard has no step to mark and is 32 px wider than the console above (736–896 vs 736–864). | Snap hazard runs to prop footprints ±1 tile and terminate them under a bracket/rib; or drop the floor-level band. |
| m8 | MINOR | `05`/`06`, ceiling | Two identical `ceiling` tiles stacked + full-width `pipe_h` band, no cornice/junction; reads as stacked plates. | Add a cornice tile row and ceiling fixtures; reduce the pipe band to 2–3 short runs. |
| m9 | MINOR | `05`/`06`, contact shadows | 4 rows of hard dither at y=512–516 on a flat pixel deck reads as grit. | Use a 2 px solid `PALETTE[1]` ellipse-less contact strip directly under the base, plus 1 px of `PALETTE[0]`. |
| m10 | MINOR | `hull_frame` | 5.8 % isolated 1 px pixels (sandpaper) instead of clusters. | Clean pass: remove isolated pixels, keep clusters ≥2×2, keep 3 tones per plate. |

## 4. Overall verdict

**FAIL.**

There are two blockers and ten majors. The room's primary structural element (the hull rib) is placed so that it neither reaches the ceiling nor sits on the floor (50 px of air above the content, 92 px of it buried under the deck) — in all ten placements — so the "whole-ship mega" does not read as a coherent room; and the showcase character is composited inside the console footprint with a firing pose. Beyond that: one of the two windows is fully occluded, both wall-detail clusters are ~73 %/~71 % occluded, six horizontal pipe runs end in mid-air with square cuts, a rib is cut 58 px by the right canvas edge, the room is ~95 % one byte-identical wall tile, `cargo_stack` cannot be told apart from the wall, `reactor_core` is a soft-gradient/asymmetric melt, and the atlas has no real platform edge. Pixel hygiene (palette purity, no AA, no magenta, no alpha holes) is genuinely clean — the failures are composition, readability and style-unity failures, not technical ones.

## 5. Summary

This is a technically clean but visually mis-assembled set. The tiles are palette-locked, AA-free and hole-free, and `console_bank`, `viewport` and `grate_*` are genuinely good hand-finished pieces; the palette (navy gunmetal, cyan accents, violet, warm hazard) is consistent and reads as the intended cyberpunk ship. What fails is the second half of the job: the hull frame's 50 px dead padding was never compensated for, so every rib floats under the ceiling and is buried 92 px into the floor, with a bright `pipe_h` splice band turning each rib into an accidental two-storey bracket; the assembly then hides its only window and both detail clusters behind ribs, terminates every horizontal conduit in mid-air, cuts the last rib with the canvas edge and repeats one 32 px wall tile 624 times, so the "room" reads as a repeated lattice with a few props pasted on. The three medium props are uneven (`console_bank` ships, `server_rack` borrows the rib motif and has floating tabs, `cargo_stack` is a wall panel), and the reactor's soft glowing coils plus nebula viewport are the only painterly elements in an otherwise flat, hard-edged world, which breaks style unity. Fix the rib anchoring first (that alone converts the room from broken to plausible), then de-occlude the window and detail clusters, rework the cargo silhouette and reactor shading, add real platform-edge tiles and a second wall/rib variant — and the packet can pass the next round. As shipped it does not.
