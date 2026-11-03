# Acceptance v3 — Ship environment pack

**Verdict: FAIL**

- Reviewer: independent multimodal review (`ship-accept-v3`)
- Scope: every PNG in `/dat/projects/artist2d/work/review/ship/` (`00`–`06`, starting from `MANIFEST.md`), plus the underlying delivered PNGs in `output/environment/ship/`, `output/mega/ship/`, `output/showcase/ship/` to verify transparency, silhouette edges and seams that the opaque catalogs cannot show.
- No asset was modified. Only this report was written.

**Totals: 2 blockers, 10 majors, 12 minors.** A pass is impossible with any blocker or major. The deterministic palette and hard-alpha checks return zero violations, but the hard requirements on door coverage, seamless floor/ceiling/pipe tiling, readable windows, contact shadows and one coherent assembly are not met.

---

## 1. Blockers

### B1 — No door tile exists anywhere in the 25-tile set

**Files / elements**
- `work/review/ship/02_all_tiles_x5.png` — all 25 labels read: `ceiling`, `deck_fill`, `deck_left`, `deck_right`, `deck_step`, `deck_step_left`, `deck_step_right`, `deck_top`, `deck_top_left`, `deck_top_right`, `grate_fill`, `grate_top`, `hazard`, `light_strip`, `pipe_h`, `pipe_v`, `vent`, `wall`, `wall_flat`, `wall_flat_light`, `wall_flat_violet`, `wall_light`, `wall_plain`, `wall_violet`, `window`. **No door.**
- `work/review/ship/00_tileset_x8.png`, `01_tileset_sample_x4.png`, `05_whole_ship_x2.png`, `06_showcase_x2.png` — no door in any of them; the whole ship is one continuous wall with no doorway.
- `output/environment/ship/tileset.json` — 25 names, no door.
- `output/environment/ship/REPORT.md` — the only door entries are `security_door` (medium, catalog 10) and `bulkhead_door` (mega, catalog 20), explicitly listed among the **ungenerated** remainder (“Only the three pilot structures/elements were generated”). The tile atlas description also omits doors.

**What is wrong:** the explicitly required tile type “doors” was never delivered. The nearest asset (`wall`, a framed 27×26 inset panel with four rivets and no handle/hinge/frame) is a wall panel, not a door. A customer cannot build a compartment, airlock, or doorway with this pack.

**Requirement broken:** “25 tiles … that tile seamlessly: floors, walls, ceiling, pipes, grates, hazard stripes, windows, doors.”

### B2 — The main floor and ceiling tiles are not seamless, and the failure is visible in the shipped uses

**Files / elements**
- `output/environment/ship/tiles/deck_fill.png` (#01) and `deck_top.png` (#07); used for the entire 4-row deck face in `05_whole_ship_x2.png` / `06_showcase_x2.png`.
- `output/environment/ship/tiles/ceiling.png` (#00); used as **two stacked rows** at the top of both scenes.
- `work/review/ship/01_tileset_sample_x4.png` — the tiled slice exposes the floor seam.
- `work/review/ship/05_whole_ship_x2.png`, `06_showcase_x2.png` — the floor dot grid and the ceiling band are visible at normal viewing.

**What is wrong (measured):**
- **Deck fill seam.** In every `deck_fill` / `deck_top` tile the horizontal highlight stops roughly 2 px before the right tile boundary and restarts after the next boundary; the 2×2 repeat shows a dark notch every 32 px. The edge mismatch is `mean |left−right| = 6.6` versus an internal neighbour difference of `0.9` (7.3×), with an edge max difference of 184. The tiled slice `01` shows the floor highlight segmented into 32 px dashes.
- **Right-edge cyan artifact.** A single cyan pixel at `(x=31, y=3)` of `deck_fill` and `(x=31, y=23)` of `deck_top` is the brightest pixel on the tile edge. Tiled, it becomes a regular dot grid: the 1× scene contains **190 exact `(53,162,196)` pixels on the deck face (y≥512), all at x ≡ 31 (mod 32), in four rows y = 535, 547, 579, 611**. That is a seam artifact repeated 48 times across the floor, not an authored deck light (no housing, no symmetric placement).
- **Ceiling vertical seam.** `ceiling` has a strong top cap (top row far brighter than the bottom): `mean |top−bottom| = 152.7` versus internal `13.2` (11.6×). Stacking two rows — exactly what `05`/`06` do — repeats the bright cap at y = 32 as a hard horizontal band. It may read as a second ceiling beam, but the tile itself is not vertically seamless and the scene does not use a single-row cap.
- **Consequence in `05`/`06`:** the floor face is a 128 px dark slab with a regular cyan-dot grid and interrupted plate highlights; the ceiling has a hard band at y = 32. At 2× these are unmistakable.

**Requirement broken:** “25 tiles … that tile seamlessly: floors … ceiling …” and “no visible seams.”

---

## 2. Majors

### M1 — The remaining “seamless” structural tiles also fail their seam tests

**Files:** `tiles/pipe_h.png` (#14), `tiles/pipe_v.png` (#15), `tiles/hazard.png` (#12), `tiles/grate_fill.png` (#10), `tiles/grate_top.png` (#11); shown in `01_tileset_sample_x4.png`, `05_whole_ship_x2.png`, `06_showcase_x2.png`.

- **`pipe_h`:** horizontal seam `21.6` vs internal `4.1` (5.3×). The bright pipe highlight is cut at every tile boundary; a 2×2 repeat shows a notch/joint every 32 px. `05` runs the pipe in 5–8-tile runs, so the seam repeats across each run.
- **`pipe_v`:** the same failure vertically (`21.6` vs `4.1`); the vertical pipe runs in `05` show a horizontal band every 32 px.
- **`hazard`:** horizontal tiling passes (`11.9` = `11.9`), but vertical tiling is not (`75.7` vs `14.6`); the top/bottom 2–4 px are a dark border. It works only as a one-row decal. `01` tests only one row; a two-row hazard wall would show a hard band.
- **`grate_fill` / `grate_top`:** horizontal mesh is seamless (`seamX = 0.0`), vertical seam is `133.6` / `139.2` vs internal `64.6` / `60.8`; the vertical posts are cut at each horizontal tile join. The scene only uses one row, so this is hidden in `05`/`06`, but the tile does not satisfy “tile seamlessly.”

**Requirement broken:** “25 tiles … that tile seamlessly: pipes, grates, hazard stripes.”

### M2 — The ceiling light fixtures are wall tiles pasted into the ceiling, producing dark square holes

**Files:** `tiles/light_strip.png` (#13), `05_whole_ship_x2.png`, `06_showcase_x2.png`; assembly at `x = 5,13,25,37,43` tiles, `y = 32`.

**What is wrong:** `light_strip` is a wall-panel tile (wall-flat background, panel border, horizontal cyan line). In `05`/`06` it replaces the entire second ceiling row at five columns. At `x=160`, rows 32–63 the patch is `[20,20,28]` while the adjacent ceiling at `x=192` begins `[155,155,176]`, `[111,111,136]`, `[54,54,70]` — a 32×32 **dark notch** cut out of the ceiling's bright beam. All five dark squares sit fully in the ceiling's second row (the ribs start at y=64, below the strip at y=32), so each is a full 32×32 hole in the bright beam. They read as missing ceiling tiles, not light fixtures: no housing, wrong material, and a hard rectangular boundary.

**Requirement broken:** one coherent interior; no visible seams; readable, integrated emissives.

### M3 — `window` is not a readable window

**Files:** `02_all_tiles_x5.png` #24; `tiles/window.png`; `01_tileset_sample_x4.png` at tile `(6,2)` (1× at `192,64`); `05_whole_ship_x2.png` at tiles `(8,6)` and `(30,9)`.

**What is wrong:** at 32×32 the tile is a near-black square with a 1 px gray border, a **4×4 violet blob** (planet), **four single-pixel stars**, and a **10 px cyan horizontal line** at `x=4..13` that looks like a HUD fragment or a scratch. There is no mullion, no glass plane, no frame depth, no star density. At 1× it reads as a black hole or a small poster with a purple dot, and it cuts through the wall-panel frames where it is pasted. Both copies in `05` are visually identical black holes at two different heights. The large `viewport` mega is readable; this required window tile is not.

**Requirement broken:** “readable windows/emissives.”

### M4 — `server_rack` is flat and under-detailed compared with the other two medium structures

**Files:** `output/environment/ship/props/server_rack/sprite.png` (55×105, 10 colors), `03_medium_catalog_x3.png`, `05_whole_ship_x2.png` at `x≈895–950`.

**What is wrong:** the silhouette is a narrow black box under a **large featureless light-gray header** (a flat slab with a corner notch), with five long 1 px horizontal rails and a small cyan LED strip at the bottom. It has no side panel, no rack ears, no module depth, no top/side shading; compared with `console_bank` (102×59, 27 colors, slanted screens, buttons, cables, base) and `cargo_stack` (59×87, three crates, straps, hazard plate), it reads as a flat cabinet/shelf. At 1× in `05` it is a gray rectangle with lines, and its light-gray header is the brightest large flat area in the medium set. The three mediums do not share pixel density or 3D treatment.

**Requirement broken:** exactly 3 medium structures that share palette, light direction, outline weight and pixel density; one unified interior.

### M5 — `hull_frame` is non-integer resampled to 128×448 and has hard internal seams

**Files:** `output/mega/ship/elements/hull_frame/sprite.png` (118×203); `05_whole_ship_x2.png` / `06_showcase_x2.png` at `x = 0,320,704,1088,1408`, `y = 64..512`; assembly in `environment/ship_assembly.py` `_rib_module`.

**What is wrong:** the 118×203 sprite is resized to 128 wide (1.085×) and assembled from a 50 px top cap, a 103→116 px mid module repeated three times, and a 50 px bottom cap, for 448 px of height. Neither axis is an integer multiple. The visible result at 1×/2× is uneven 1–2 px linework on the X-braces and side pipes, and a 1 px black seam drawn across the full rib width at `y=166` and `y=282`; the seams cut the X-brace, the cyan pipe and the purple pipe with no joint flange. Five of these ribs dominate `05`/`06`, so the mismatch is systematic, not incidental. The `04` review sheet compounds this by showing the hull at ~2.48× (fit-to-cell), not 3×, so its pixel density cannot be judged from the catalog.

**Requirement broken:** no mismatched pixel density; consistent 1 px outline weight; one unified interior.

### M6 — Contact shadows are 2 px bbox-wide lines, not contact footprints

**Files:** `05_whole_ship_x2.png`, `06_showcase_x2.png`; implementation `_paste_grounded` / `_shadow` in `environment/ship_assembly.py`.

**What is wrong:** every prop and the character gets a **2-row** shadow spanning the **full sprite bbox width**, drawn at the deck's top edge. Examples measured from the sprites and scene:
- `cargo_stack`: shadow 59 px, bottom crate base 47 px — 6 px of shadow under each overhang.
- `server_rack`: shadow 55 px (header width), body/feet ~45 px.
- `console_bank`: shadow 102 px (including the top/side cable bbox), base ~90 px.
- character: shadow 31 px, feet ~12 px — it extends under the katana and hair.

The dither is a single alternating row on the 2 px line (`y=512–513` for floor props; `y=480–481` for the console on the dais). At 1× it is not legible as a dither; it reads as a dark dotted seam that replaces the deck's bright lip. The objects are geometrically on the deck/base (no floating), but the shadow does not describe the contact area, and the console's shadow visibly breaks the dais's bright top edge.

**Requirement broken:** “dithered contact shadows, grounded objects.”

### M7 — The right bay fuses the cargo stack and reactor; the hazard band is mostly hidden

**Files:** `05_whole_ship_x2.png`, `06_showcase_x2.png`; `mega/ship/ship_layout.json` (cargo x=38, reactor x=40); `mega/ship/ship_assembly.py` (reactor mount rectangle, hazard band x=39..44).

**What is wrong:** the flipped cargo occupies x≈1218–1276; the reactor's 3 px black mount begins at x≈1282 and the reactor body at x≈1285, leaving only a 5 px wall gap. Both silhouettes have near-black outlines, so the cargo, mount and reactor read as one clump. The 5-tile hazard band (x=1248–1408, y=480–512) is behind them: the cargo covers its left ~29 px and the reactor covers the rest, leaving a thin yellow border around the reactor. The cargo's own 3 px hazard stripes at its base sit directly above the floor band's 5 px stripes, so the two hazard motifs merge into a single yellow patch. The bay is visually packed while the first and third bays are sparse; the scene does not distribute its stations coherently.

**Requirement broken:** whole ship assembles into one coherent scene.

### M8 — Two of the 25 tiles are byte-identical duplicates

**Files:** `tiles/deck_top_left.png` == `tiles/deck_left.png`; `tiles/deck_top_right.png` == `tiles/deck_right.png`; the same duplicate cells are present in `tileset.png` and labelled separately in `02_all_tiles_x5.png` (#02/#08 and #03/#09).

**What is wrong:** 25 files, but only **23 distinct tiles**. The “deck top corner” variants are not real corners; they are the edge caps copied under new names. The “22 originals” count is inflated by two redundant files, while the required door is absent. A customer using the atlas by name gets duplicated artwork and no corner variant.

**Requirement broken:** 25 functioning tiles (22 originals + 3 real step variants); atlas completeness.

### M9 — Character metadata still says two characters; the image has one

**Files:** `mega/ship/ship_layout.json` (character array: `idle frame 00 at x=7` **and** `shoot2 frame 02 at x=30, flipped`); `showcase/ship/report.json` (`"character": "agent idle/shoot2"`); `06_showcase_x2.png`.

**What is wrong:** the delivered layout/report describe **two** character placements, including a `shoot2` frame at x=30. The actual 06 image has exactly **one** idle frame at x≈240 (content), and the 1× diff against `ship_mega_1x.png` is **one connected component, 30×55 px at x=241–270, y=459–513** (including its 2-row shadow). The build code currently writes only the idle entry, so the shipped JSON/report are stale from before the single-character fix. The image meets “exactly once”; the data does not, and a user following the layout would add a second character.

**Requirement broken:** showcase “character integrated exactly once”; coherent delivered metadata.

### M10 — The wall system is a patchwork, and 01 and 05 show two different walls

**Files:** `tiles/wall.png`, `wall_flat.png`, `wall_plain.png`, `wall_light.png`, `wall_violet.png`, `wall_flat_light.png`, `wall_flat_violet.png`; `01_tileset_sample_x4.png`; `05_whole_ship_x2.png`, `06_showcase_x2.png`.

**What is wrong:** `01` is a fully framed-panel wall (`wall` with `wall_light`/`wall_violet` accents); `05`/`06` are mostly flat `wall_flat` with four rectangular “detail clusters” using a 4-state checkerboard (`(x+y)%4` → `wall`, `wall_plain`, `wall_light`, `wall_violet`), plus eight full-height bare `wall_flat_light/violet` strips. The result mixes framed short strips, bare full-height strips, plain panels and a short 1 px dash (`wall_plain`, near mid-height) in hard-edged rectangular patches that are not tied to the ribs, viewport or stations. The two small windows (tiles (8,6) and (30,9)) and four vents (tiles (6,10),(18,12),(28,8),(40,10)) sit at unrelated heights; the windows are inside a framed band in one bay and on flat wall in another. In addition, all wall/deck tiles are covered in random 1 px multicolor specks (cyan/white/violet); at 2× the wall reads as a starfield/salt-and-pepper noise rather than metal. This is not one unified interior.

**Requirement broken:** one unified side-view interior; coherent wall/light/detail system.

---

## 3. Minors

Each item lists the exact file and the requirement it weakens. These are not blockers by themselves, but they compound the failed sections above.

1. **m1 — 02/03/04 review sheets are not at the labelled scales.** `02_all_tiles_x5.png`: tiles are 204×204 in 220 px cells (effective **6.375×**, not 5×); the label at `(8,6)` overlaps the tile's top-left corner at `(8,8)`, exactly where corners must be checked. `03_medium_catalog_x3.png`: the fit-to-cell code scales console/cargo/server to **4.94× / 5.79× / 4.80×**, not 3×. `04_mega_catalog_x3.png`: hull/viewport/reactor are **2.48× / 4.50× / 3.60×**, so the viewport is over-scaled and the hull under-scaled; relative scale is distorted. The 03/04 labels are in the cell margins; the 02 labels are the ones that overlap. **Breaks:** the review packet's ability to prove the labelled 5×/3× pixel density and the tile corners. (Review-packet evidence defect; the raw sprites were inspected separately.)
2. **m2 — Shipped catalogs hide the outlines.** `props/catalog_preview.png` and `mega/ship/elements/catalog_preview.png` use background `[8,8,12]`, exactly the sprites' 1 px outline colour, so the outer silhouettes disappear and the props lose 1–2 px of their bbox. The 04 viewport (a wall element) is bottom-aligned with floor-standing hull/reactor, making it look floor-mounted. **Breaks:** catalog readability of the transparent silhouettes (presentation, not asset alpha).
3. **m3 — `wall` frame is off-centre and not square.** The bright frame occupies x=1..27, y=1..26 in the 32×32 tile (margins 1/4 and 1/5); tiled, the panel grid is 1 px tighter at the top/left and the panel interior is 25×24, not square. **Breaks:** the 1 px panel-grid consistency in the wall tile.
4. **m4 — `wall_plain` is a near-duplicate of `wall_flat`.** Mean absolute difference 2.82/255; it adds a short 1 px horizontal dash near mid-height (the rest of the difference is noise). The name is misleading and the tile adds little variety. **Breaks:** the claimed variety of the 22 originals.
5. **m5 — `vent` and `window` are pasted decals, not integrated tiles.** Their full 32×32 opaque backgrounds cut the wall-panel frames; the vent at (6,10) and the window at (8,6) sit at arbitrary offsets; no alignment to the panel grid. **Breaks:** one unified wall / decal integration.
6. **m6 — `01` does not test the vertical seams.** It shows only the wall/floor slice plus one window, vent, hazard row and grate row; there is no ceiling, pipe run or two-row hazard/grate. The floor seam and window failure show, but M1's vertical failures are hidden. **Breaks:** 01 as a seam test for the ceiling, pipes, hazard and grate.
7. **m7 — Pipe indicator blocks have no housing.** `pipe_h`/`pipe_v` carry symmetric 2×2 cyan/violet blocks at x/y 8–9 and 24–25 around a 1 px central joint; at 1× they read as saturated stickers on the pipe rather than indicator lamps. **Breaks:** coherent, readable pipe detail.
8. **m8 — Three different hazard motifs.** Floor hazard = 5 px diagonal stripes; cargo base = 3 px stripes; reactor plinth = orange dashes. In the right bay the cargo and floor motifs are adjacent and read as one inconsistent yellow patch. **Breaks:** a single coherent hazard language.
9. **m9 — Large dead floor band.** The deck face is 4 tiles (128 px) of dark `deck_fill` below the walkable lip, ~20% of the 640 px scene height, with only the repeated dot/line pattern. The composition is top-heavy and the bottom of `05`/`06` is visually empty. **Breaks:** showcase composition/readability.
10. **m10 — Cutout edge gaps (no magenta/partial alpha, but not every silhouette is closed).** `viewport` top row is 82/90 opaque pixels of light gray `[155,155,176]` with no dark outline; `console_bank` bottom row has 16 violet cable pixels on the boundary; `reactor_core` base left edge has one ochre pixel on the boundary. These are minor clipped-edge/outline gaps, not halos. **Breaks:** the “no clipped edges” requirement at the sprite boundary.
11. **m11 — The showcase character is peripheral.** The agent is 30 px wide (30×55 including its 2-row shadow) at x=241–270 in a 1536×640 scene, at the far left next to the cargo; most of the frame is wall/ribs and open floor. The integration rules are met, but the “showcase” does not stage the character or the ship's stations. **Breaks:** showcase staging (the integration rules themselves pass).
12. **m12 — Manifest contradiction.** `output/MANIFEST.md` §6 still states “ship v5 = PASS (no BLOCKER/MAJOR)”; the independent v3 inspection finds two blockers and ten majors. The stale PASS should be withdrawn or the fixes re-reviewed. **Breaks:** acceptance/documentation integrity.

---

## 4. Per-item checklist

Method for every tile: opened the raw 32×32 RGBA PNG, checked alpha (all 255), palette, all four edges and corners, built a 2×2 nearest-neighbour repeat with tile-boundary lines, inspected the `02` contact sheet (nominal x5, effective 6.375×), and checked the tile's actual use in `01`/`05`/`06`. “PASS” below means the tile itself is solid/legible/consistent; scene-level failures are listed in the rows.

### 4.1 All 25 tiles

| # | Tile | What I inspected | Result |
|---:|---|---|---|
| 00 | `ceiling` | 32×32; 2×2 repeat; top vs bottom edge; 2-row use in 05/06 | **FAIL seam (B2).** Top band repeats at y=32; seamY 152.7 vs internal 13.2; cyan p1 at the right edge; five dark light-strip patches break the band (M2). |
| 01 | `deck_fill` | 32×32; 2×2; edge columns; 01 floor; 05 deck face | **FAIL seam (B2).** Highlight stops ~2 px before each boundary; seamX 6.6 vs 0.9; cyan p1 at (31,3); 190 cyan dots at x≡31 across the deck face. |
| 02 | `deck_left` | 32×32; left cap; 2×2; dais cap | **PASS tile** (left edge lit [111,111,136], consistent top-left light); **M8 duplicate** of `deck_top_left`. |
| 03 | `deck_right` | 32×32; right cap; 2×2 | **PASS tile** (outer edge dark [8,8,12], shadow side); **M8 duplicate** of `deck_top_right`. |
| 04 | `deck_step` | 32×32; solid alpha; distinct; 4-instance dais run | **PASS.** seamX 0.5 (edges match); distinct from both step caps; solid. |
| 05 | `deck_step_left` | 32×32; solid; left cap; dais left edge | **PASS.** Distinct; left outer column lit; right column dark. |
| 06 | `deck_step_right` | 32×32; solid; right cap; dais right edge | **PASS.** Distinct; right outer column dark; left lit. |
| 07 | `deck_top` | 32×32; 2×2; floor lip in 05/06 | **FAIL seam (B2).** Same 2 px highlight notch; seamX 6.6 vs 1.1; cyan p1 at (31,23); the floor lip is interrupted at every tile. |
| 08 | `deck_top_left` | 32×32; byte compare with #02; 2×2 | **FAIL (M8).** Byte-identical to `deck_left`; not a real top-left corner variant. |
| 09 | `deck_top_right` | 32×32; byte compare with #03; 2×2 | **FAIL (M8).** Byte-identical to `deck_right`; not a real top-right corner variant. |
| 10 | `grate_fill` | 32×32; 2×2; 01 grate; vertical posts | **PASS horizontally, FAIL vertically (M1).** seamX 0.0; seamY 133.6 vs 64.6; posts cut at horizontal joins. Not used in 05 (only `grate_top`). |
| 11 | `grate_top` | 32×32; 2×2; 01 grate; 05 floor row | **PASS as a one-row cap, FAIL as a 2D tile (M1).** seamY 139.2; in 05 it reads as a bright ladder/vent on the deck face rather than a walkable floor grate. |
| 12 | `hazard` | 32×32; 2×2; 01 one-row patch; 05 floor band | **PASS horizontally (11.9 = 11.9), FAIL vertically (75.7 vs 14.6) (M1).** Single-row decal only; top/bottom dark border. |
| 13 | `light_strip` | 32×32; 2×2; ceiling placement | **FAIL in use (M2).** Cyan line is continuous horizontally (good), but the wall-panel background is pasted into the ceiling as a dark 32×32 notch at five columns. |
| 14 | `pipe_h` | 32×32; 2×2; 05 pipe runs | **FAIL seam (M1).** Highlight cut at every 32 px; seamX 21.6 vs 4.1; symmetric 2×2 cyan/violet blocks at x=8–9/24–25. |
| 15 | `pipe_v` | 32×32; 2×2; 05 vertical runs | **FAIL seam (M1).** seamY 21.6 vs 4.1; horizontal bands every 32 px; cyan at x=6–7, violet at x=24–25. |
| 16 | `vent` | 32×32; slats; wall placement | **PASS as a vent sprite, minor (m5).** Slats readable; opaque background cuts the wall-panel frame and is placed at arbitrary offsets. |
| 17 | `wall` | 32×32; 2×2; frame bbox; cluster use | **PASS as a framed panel; m3 frame, M10 system.** Frame 27×26 at x=1..27, y=1..26, off-centre; used in checkerboard clusters, not a coherent wall system. |
| 18 | `wall_flat` | 32×32; 2×2; random specks | **PASS seam (no structural line), major (M10).** No seam line, but covered in random 1 px cyan/white/violet noise. |
| 19 | `wall_flat_light` | 32×32; cyan line x=9; full-height strip use | **PASS tile; M10 system:** bare 2 px strip on a flat wall; mixed with framed strips in 05. |
| 20 | `wall_flat_violet` | 32×32; violet x=22; strip use | **PASS tile; M10 system:** same, violet on the shadow side. |
| 21 | `wall_light` | 32×32; framed panel; cyan x=9 (22 px) | **PASS tile; M10 system:** framed short strip; mixed with bare strips. |
| 22 | `wall_plain` | 32×32; compare with `wall_flat`; dash | **PASS seam**, minor (m4): mean diff 2.82; 1 px dash plus noise; near-duplicate. |
| 23 | `wall_violet` | 32×32; framed panel; violet x=22 (22 px) | **PASS tile; M10 system:** framed short strip on the shadow side. |
| 24 | `window` | 32×32; 2×2; 01 at (192,64); 05 at (256,192)/(960,288) | **FAIL (M3).** Black square, 4×4 violet blob, four 1 px stars, 10 px cyan line; reads as a hole/poster, not a window. |

**Coverage: 25 files, 23 distinct; no door (B1); the three step variants are real and solid (PASS).**

### 4.2 Three medium structures

| Element | What I inspected | Result |
|---|---|---|
| `console_bank` (102×59) | `sprite.png` at 1×/4×, checkerboard cutout, `03`, `05` placement, alpha bbox, perimeter | **PASS asset.** 27 colors; hard alpha; 1 px outline; three readable cyan screens; slanted top, buttons, cables, base. Minor: bottom row has 16 violet cable pixels on the bbox edge; its `05` shadow spans 102 px vs ~90 px base (M6). |
| `cargo_stack` (59×87) | `sprite.png` 1×/4×, checkerboard, `03`, `05` at x=162 and flipped x=1218, perimeter | **PASS asset.** 10 colors; hard alpha; three distinct crates; straps/rivets; hazard plate; bottom/top outlines black. Fails at scene level: 59 px shadow vs 47 px bottom crate (M6); merges with the reactor (M7). |
| `server_rack` (55×105) | `sprite.png` 1×/4×, checkerboard, `03`, `05` at x≈895–950, perimeter | **FAIL (M4).** 10 colors; large featureless gray header; five 1 px rails; no side depth; reads as a flat cabinet/shelf. Shadow 55 px vs ~45 px feet (M6). |

**Type count: exactly 3 (console/cargo/server) — PASS. Delivered quality: 2 pass, 1 fail.**

### 4.3 Three mega elements

| Element | What I inspected | Result |
|---|---|---|
| `hull_frame` (118×203) | `sprite.png` 1×/2×, checkerboard, `04`, `05/06` all five ribs, resize path, seams | **FAIL (M5).** Hard-alpha cutout is clean, but the scene resamples 118→128 × 203→448 (non-integer) and repeats a 116 px mid module with 1 px black seams at y=166/282 that cut the braces and pipes. Five instances amplify the mismatch. |
| `viewport` (112×88) | `sprite.png` 1×/4×, checkerboard, `04`, `05` at (520,128), top edge, starfield | **PASS with minor (m10).** Readable starfield/planet; 25 colors; 1 px frame bevel; recessed 3 px black mount in the scene. Top row is 82/90 light-gray pixels with no dark outline; minor edge gap. |
| `reactor_core` (118×140) | `sprite.png` 1×/4×, checkerboard, `04`, `05` at x≈1285–1397, base, hazard band | **PASS with minor (m8/m10).** 28 colors; detailed cyan cells, violet coils, pipes, plinth; hard alpha; bottom black. Base left edge has one ochre pixel at the bbox boundary; its orange base dashes clash with the 5 px floor hazard (M7/m8). |

**Type count: exactly 3 (hull/viewport/reactor) — PASS. Delivered quality: 1 fail, 2 pass with minors.**

### 4.4 `01_tileset_sample_x4.png`

- 576×288 at 1× (18×9), 2304×1152 at 4×; opened both the 4× and the 1× source.
- Wall: framed `wall` panels with `wall_light`/`wall_violet` accents; floor: deck fill (dimmer `[78,78,99]` lip than the 05 `deck_top` `[155,155,176]`); window at (192,64); hazard one row; grate at the floor; no ceiling, pipes, doors.
- **Findings:** floor highlight segmented at 32 px; regular cyan edge dots; window is an unreadable black square; the sample's all-framed wall does not match 05's flat+patch wall (M10); no vertical seam tests for ceiling/pipes/hazard/grate (m6); no door (B1). **FAIL as a seam/representative slice.**

### 4.5 `05_whole_ship_x2.png`

- 3072×1280 (exact 2× of 1536×640, 48×20 tiles at 32 px); floor row 16, deck lip y=512; five 448 px hull ribs at x=0,320,704,1088,1408; one viewport at (520,128); one reactor at x≈1285; two cargo (x=162 and flipped x=1218); one console at (525,421) on the 192 px dais (x=480–672, y=480–512); one server at x≈895; **zero characters** (by design); **zero doors**.
- Inspected at 1× and 2×, plus 2× crops of the left bay, center station, right bay and ceiling; measured the 5 rib positions, deck lip, cyan dot rows, ceiling patch colors, prop bboxes and shadows.
- **Passes:** palette (0 off-palette), integer 2× upscale, hard alpha/opaque scene, viewport/console station centered, props geometrically on the deck/dais, zero characters (the 05 assembly is the no-character version).
- **Fails:** B1 no door; B2 floor/ceiling seams; M1 pipe/hazard/grate seams; M2 ceiling light patches; M3 small windows; M4 server; M5 hull; M6 shadows; M7 right-bay fusion; M10 wall patchwork/noise; the 128 px dead floor band (m9); hard scene-edge cuts (minor). **FAIL.**

### 4.6 `06_showcase_x2.png`

- 3072×1280 (exact 2× of 1536×640); same scene as 05 with the agent.
- **Character check:** one connected 1× diff component, 30×55 px, x=241–270, y=459–513; idle frame 00 only; 53 px tall = 1.66 tiles (32 px tile), correct relative to the 59 px console and 87 px cargo; feet end at y=511, deck lip starts y=512, shadow rows y=512–513; no second character, no floating, hard-alpha character, no magenta.
- **Passes:** exactly one character **in the image**; idle pose; standing on the deck; correct scale; contact shadow present (dithered); not floating.
- **Fails:** shadow spans the full 31 px bbox vs ~12 px feet (M6); the character is peripheral (30 px wide at the far left of 1536, m11); the scene behind inherits B1/B2/M1–M10; the delivered `ship_layout.json` still says two characters (M9). **FAIL overall; the character integration itself passes the count/scale/grounding checks.**

### 4.7 `00`, `02`, `03`, `04`

- `00_tileset_x8.png`: 2048×1024, exact 8× of `tileset.png` 256×128; 8×4 grid, 25 tiles + 7 empty cells; window at the bottom-left; no door; **FAIL coverage (B1)**, no duplicates visible at a glance but `02`/atlas cells duplicate.
- `02_all_tiles_x5.png`: 1320×1100, 6×5 cells of 220; labels for all 25; **effective 6.375×, not 5×**; labels overlap the top-left corner; **2 duplicate cells**; **no door**; **FAIL coverage**, minor evidence issue (m1).
- `03_medium_catalog_x3.png`: 1560×520; exactly three mediums; labels; fit-to-cell 4.94×/5.79×/4.80×; no shadows; server flat (M4); **FAIL quality**.
- `04_mega_catalog_x3.png`: 1560×520; exactly three megas; labels; fit-to-cell 2.48×/4.50×/3.60×; viewport over-scaled vs hull; hull seams not visible at this reduced scale; **FAIL quality/pixel-density evidence** (M5/m1).

---

## 5. Requirement matrix

| Requirement | Result | Evidence |
|---|---|---|
| 25 tiles (22 originals + 3 real platform-step variants) | **FAIL** | 25 files / 23 distinct; 2 duplicates (M8); no door (B1); the 3 step variants are real and solid (PASS). |
| Floors, walls, ceiling, pipes, grates, hazard, windows, doors | **FAIL** | All present except **doors** (B1); window unreadable (M3). |
| Tile seamlessly (no visible seams) | **FAIL** | Deck/ceiling (B2), pipes/hazard/grate (M1); 01/05 show the floor; 05 shows the ceiling/pipes. |
| Exactly 3 medium structures | **PASS count** | console/cargo/server in 03 and 05; 2 cargo instances in 05 is placement, not a fourth type. |
| Exactly 3 modular mega elements | **PASS count** | hull/viewport/reactor in 04 and 05; 5 hull instances is modular use, not a fourth type. |
| Tiles/mediums/megas share palette | **PASS** | 0 off-palette pixels in every delivered sprite/tile; 64-colour palette; 0 partial alpha. |
| Consistent top-left light | **PASS with minor** | Tiles' top bands, prop top-left bevels, console/cargo/reactor highlights agree; hull is symmetric (appropriate for a rib); server header is flat. |
| Consistent 1 px outline weight | **FAIL** | Hull non-integer resample makes 1–2 px linework (M5); server is mostly flat (M4). |
| No mismatched pixel density | **FAIL** | Hull resample (M5); server flat header (M4); random 1 px wall noise (M10). |
| Transparent cutouts, no magenta/purple fringe | **PASS** | All `sprite.png` cutouts are hard alpha (0 partial), 0 magenta pixels, 0 halo; 03/04 are opaque catalogs by design. |
| No opaque background rectangle (in the cutout assets) | **PASS** | `sprite.png` backgrounds are fully transparent; only the review sheets/catalogs are opaque. |
| Dithered contact shadows | **FAIL** | 2 px bbox-wide lines; dither is one row and not legible at 1×; footprint too wide (M6). |
| Grounded objects (no floating) | **PASS geometrically** | Feet/base rows end at deck−1; deck lip at 512; props grounded; shadow quality fails (M6). |
| Readable windows/emissives | **FAIL** | `window` unreadable (M3); viewport/console/light strips readable. |
| Showcase 06: agent exactly once, standing, correct scale, shadow, not floating | **PASS image / FAIL data** | One idle component, 53 px, feet on deck, shadow present; layout says two (M9); shadow footprint (M6). |
| Whole ship assembles into one coherent scene | **FAIL** | Ceiling patches (M2), right-bay fusion (M7), wall patchwork (M10), no door (B1). |
| No clipped edges | **PASS with minor** | Viewport top 82/90 light-gray with no outline; console bottom 16 violet cable pixels; reactor base 1 ochre pixel (m10). |
| Tile atlas 02 / tiled slice 01 / medium catalog 03 / mega catalog 04 / whole ship 05 / showcase 06 | **FAIL** | 02: no door + duplicates + label overlap; 01: floor seam + window; 03: server; 04: hull/pixel density; 05: B1/B2/M2/M7/M10; 06: M6/M9 + inherited scene fails. |

---

## 6. What was actually inspected

- **All 7 review PNGs**: `00_tileset_x8.png`, `01_tileset_sample_x4.png`, `02_all_tiles_x5.png`, `03_medium_catalog_x3.png`, `04_mega_catalog_x3.png`, `05_whole_ship_x2.png`, `06_showcase_x2.png`, starting from `MANIFEST.md`.
- **Every one of the 25 tile PNGs** at 32×32: alpha, palette, four edges/corners, 2×2 repeat, atlas cell, and use in the scenes.
- **All 6 sprite PNGs** at 1×/4× and on a checkerboard: alpha bbox, perimeter colours, silhouette closure, 1 px outline, palette, and scene placement.
- **Both 1× scenes** (`mega/ship/ship_mega_1x.png`, `showcase/ship/scene_1x.png`) and the 2× review copies; 2× crops of the left bay, center station, right bay, ceiling, floor line, character and windows.
- **Quantitative checks**: seam edge-difference ratios, exact cyan-pixel positions, ceiling patch colours, diff component of 05 vs 06, bbox/scale measurements, alpha histograms, palette membership.
- **No assets were modified.** Only this report was created.

---

## 7. Conclusion

**FAIL.** The palette/hard-alpha checks pass and the large viewport/console are readable, but the pack cannot ship as a commercial 25-tile seamless ship interior while:

1. **no door tile exists** (B1);
2. the **main floor and ceiling** are not seamless and the defects are visible in `01`/`05`/`06` (B2);
3. the **pipes, hazard and grate** fail their seam tests (M1);
4. the **ceiling light fixtures** are wall tiles creating dark holes (M2);
5. the **window tile** is an unreadable black square (M3);
6. the **server rack** is a flat placeholder next to the other two mediums (M4);
7. the **hull frame** is non-integer resampled with hard internal seams (M5);
8. the **contact shadows** are bbox-wide 2 px lines (M6);
9. the **right bay** fuses the cargo and reactor (M7);
10. two of the 25 tiles are **duplicates** (M8);
11. the **layout metadata** still says two characters (M9);
12. the **wall system** is a patchwork and 01/05 show different walls (M10).

**PASS would require zero blockers and zero majors.** This review found **2 blockers and 10 majors**; the correct verdict is **FAIL**.
