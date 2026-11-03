# Ship Environment — Independent Acceptance (v8)

**Verdict: PASS**

**Blockers: 0. Majors: 0. Minors: 16.** PASS is issued because both counts are zero. No asset was modified; this report is the only write.

**Scope:** every PNG in `work/review/ship/` (`00`–`06`), the 25 `tiles/` PNGs, `tileset.png`, `tileset_sample.png`, `tileset.json`; the three medium sprites and the three mega sprites; `ship_mega_1x.png`, `scene_1x.png`, `scene.png`, `scene_focus_x4.png`, `scene_shadows_x6.png`; the 1× catalogs/previews; the three `report.json` files, `ship_layout.json`, `REPORT.md`; `environment/ship_assembly.py`; `scripts/build_review_packets.py`; `output/reviews/acceptance_v7_ship.md` and `output/reviews/ship_fix_v8.md`.

**Method:** every packet image was opened, and defect areas were re-examined at 2–16× nearest-neighbour crops. Alpha, palette, nonzero colours, tile seams, 2×2 repeats, shadow row runs, and catalog scale were measured from the PNGs. I re-ran `compose(include_character=True/False)` and diffed it against the shipped scene/mega; I re-ran `compose()` with `_shadow` patched to a no-op to isolate the contact layer. The 02/03/04 sheets were matched against exact 5×/3× scaled sprites; the 00/01/05/06 SHA-256s were compared with the shipped previews; the 6× plate was rebuilt from the scene crop and compared pixel-for-pixel. The pack's own pass flags are not used as evidence.

---

## Blockers

None.

---

## Majors

None.

---

## Minors

1. **Server base has a 20×2 transparent slot** — `output/environment/ship/props/server_rack/sprite.png`, sprite x=16–35, y=101–102 (the only enclosed alpha-0 hole in the sprite; the louvres themselves are opaque). In `scene_1x.png` it lands at x=888–907, y=509–510 and shows the wall behind (`#23232e`/`#363646`), so the base reads as a light kick-plate bar that changes with the background. On the dark 03 catalog it reads as a dark vent. This is cutout hygiene rather than the listed fringe/partial-alpha/clipped-edge failures, hence Minor. Requirement: "Cutouts: no magenta/purple fringe, opaque rectangle, halo/partial alpha/clipped edges"; "one unified … interior." Fix: make the vent slot opaque (palette 0/1) and rebuild the 03/06 previews.
2. **The showcase's agent is one character rebuild stale** — `output/showcase/ship/scene_1x.png` and packet `06_showcase_x2.png`. The shipped scene is 18:48; `idle/frames/frame_00.png` was regenerated at 18:55. A fresh `compose(include_character=True)` differs by **303 px, all inside (950,459)–(981,511)**, i.e. the agent body only. The fix report's "0 px" and "rows 480–483 have 0 changed px" do not reproduce in the current tree (those row diffs are the stale agent, not shadows). The agent still passes every visual showcase requirement (see checklist), so this is a reproducibility/report defect, not a visual failure. Requirement: "Showcase: agent exactly once, standing, correct scale, contact shadow, not floating"; "verify, do not trust." Fix: rebuild the scene and `06` after the character build.
3. **The five hull footings have no contact footprint** — `scene_1x.png` x=0–127, 320–447, 704–831, 1088–1215, 1408–1535, rows 514–516 contain no shadow run. Every free-standing platform/prop/agent is covered; the 118-px rib base plates meet the deck lip at row 511 with only their 1-px bottom outline. I treat the ribs as wall architecture (the requirement's explicit object list is reactor/console/dais/agent), so this is a Minor/risk. Under a literal "every lip/tread" reading it is the same class as v7 M1 at five junctions and would be a Major. Requirement: "Contact shadows: a real dithered footprint below every lip/tread, solid core + falloff … grounded." Fix if the client counts footings: append `(x, np.full(118, 3), 514)` for the five rib positions.
4. **The pad's end treatment is not the dais's** — `scene_1x.png` pad x=1232–1391 versus dais x=480–671. The **155/111/111/78 tread rows are identical** (measured at x=500/1250), and the fix report's "identical top edges" is true for those rows; but the pad's ends are 3-px chamfered faces, while the dais's ends are 32-px `deck_step_left/right` caps with a bright vertical bar. The two platforms therefore read slightly differently at the ends. Requirement: "one unified side-view … interior"; report accuracy. Minor.
5. **Viewport glass is dark** — `output/mega/ship/elements/viewport/sprite.png`, placed at scene x=520–631, y=128–215. Inner-glass mean **37.56**, p10 **11.0**, versus the window tile's scene mean **49.96**. At 1× it reads as a black panel with a faint planet. Requirement: "shared palette/light"; "windows." Minor (acknowledged as risk 1 in the fix report).
6. **Door clear height 60 px versus server 104 / cargo 87** — `scene_1x.png`, door x=992–1023, rows 448–511. The agent (53 px) fits with 7 px headroom, so "usable at the agent's scale" is satisfied; the two tallest medium props could not pass the only door. Requirement: "Door visible and usable at the agent's scale" (met); "one unified … interior" (logistics inconsistency). Minor (risk 2).
7. **The five ribs still read as a repeated module at 1×** — `scene_1x.png` x=0/320/704/1088/1408. The service bands are genuinely different (three unique hashes; variants 0,1,2,1,0; 0 and 4 differ only by a 1-px surrounding wall column), but the difference is confined to the bottom 39 px and the X-brace top caps remain identical. Requirement: "one unified … interior"; the v7 "five identical ribs" finding is reduced, not visually eliminated. Minor.
8. **Ceiling light strips are irregularly spaced and monitor-like** — `scene_1x.png` at x=5/13/25/37/43 (tile units), spacing 8/12/12/6 tiles; three sit above ribs (13/25/37) and two in bays (5/43). The `light_strip` housing has a monitor/stand silhouette. Requirement: "shared palette/light"; "one unified … interior." Minor.
9. **Packet framing** — `00_tileset_x8.png` is 8×4 cells with **7 empty** (~22 %); `02_all_tiles_x5.png` is 6×5 with **5 empty**; the labels are small default font. Requirement: "25 tiles" presentation. Minor.
10. **The `01` slice is not a room demo** — `01_tileset_sample_x4.png`, 18×9 tiles: no ceiling tile and no door; the `hazard` pair is at row 7 (the deck front face), not on a raised platform. It is a valid tile slice, not a full usage demo. Requirement: "Tiles seamless (… windows, door)." Minor.
11. **The 6-tile dais repeats `deck_step` four times** — `scene_1x.png` x=512–639, rows 480–511; the recessed vent slot repeats at a 32-px pitch. Requirement: "one unified … interior." Minor.
12. **The 2-crate cargo is a crop of the 3-crate sprite** — `environment/ship_assembly.py` `_cargo_low()` crops `cargo_stack/sprite.png` at row 26; there is no separate shipped 2-crate file. The variant is documented in `ship_layout.json` and the fix report (risk 9). Requirement: "exactly 3 medium" (the type count is correct; the variant is a crop). Minor.
13. **The lower vertical-pipe flanges are offset vertical bars** — `scene_1x.png` x=256/640/1024, y=416–447: `_flange()` draws a 4×32 bar at the left edge of the 32-px pipe bundle, parallel to the pipes, so the termination reads as a bracket rather than a horizontal collar. Requirement: "pipes … no visible seams." Minor.
14. **The bay accent lines break at both panel bands** — `wall_flat_light`/`wall_flat_violet` give 256 cyan/256 violet pixels per bay over y=96–415 (verified; the fix report's 256 is correct, the v7 180 was not), but the lines stop for the 32-px `wall` panel rows at y=3 and y=12. It reads as the neon passing behind the panel band; nevertheless the accent is not continuous. Requirement: "no visible seams." Minor.
15. **Report/measurement corrections** — `output/reviews/ship_fix_v8.md`: "scene_1x.png is 0 px different from a fresh compose" is false (303 px, agent only); "rows 480–483 have 0 changed px" is false in the current tree (those are the stale agent's pixels, not the shadow); "the two platforms have identical top edges" is true only for the 155/111/111/78 tread rows, not the end caps. The shadow totals (scene 1618 including the 31-px agent footprint; mega 1587), the 256 accents, the 6× plate, and the 633-px 04 cell do reproduce. Requirement: "verify, do not trust." Minor (report, not asset).
16. **The whole-ship edges are cut; the end-cap kit is unused** — `scene_1x.png` / `05_whole_ship_x2.png` x=0 and x=1535: the floor is `deck_top` to the image border, the wall is cut, and `deck_left`, `deck_right`, `deck_top_right` are not placed. The 05 is a hall slice, so this is a framing choice; the `deck_top_right` still has no left twin. Requirement: "one unified … interior"; "25 tiles" (the caps are kit). Minor.

---

## Claims verified (not taken on trust)

| v8 claim | result | evidence |
|---|---|---|
| Dais contact footprint fixed | **true** | scene minus no-shadow compose, rows 514–516: dais x=480–671 = **192 / 120 / 72**; row 514 is 100 % solid; rows 512–513 (deck lip) and 480–483 (dais tread) contain no shadow pixels |
| Pad is 5 tiles, x=1232–1391 | **true** | 160 px wide, 16 px margins in the 6-tile bay; reactor x=1253–1370 with 21 px either side; pad shadow **160 / 100 / 60** |
| Row 514 has six runs totalling 538 px | **true** | 58 (3-crate), 58 (2-crate), 192 (dais), 52 (server), 18 (agent), 160 (pad) = 538 |
| Shadow totals | **true** | no-shadow diff is 1921 px: 303 stale-agent + 1618 shadow; mega 1587 = 1618 − 31-px agent footprint |
| Console / reactor shadows | **true** | console 94/58/35 at rows 484–486; reactor 118/118/73/44/14 at rows 484–488; cargo 58/36/21, server 52/28/17, agent 18/10/3 at 514–516 |
| Hidden window moved to (7,6) | **true** | window x=224–255 fully visible; conduit at x=256–287 does not overlap; the (30,7) window x=960–991 is also visible |
| Pad top edge matches the dais | **true for the tread** | both rows 480–483 = 155/111/111/78 at x=500/1250; end caps differ (Minor 4) |
| Five ribs no longer identical | **true at pixel level** | scene module hashes 0=589b8cc8, 1=6bed5fae, 2=1ba3a21d, 3=6bed5fae, 4=5b502692 (3 unique); 0 vs 4 differs only at one surrounding wall column |
| 6× shadow plate exists and is current | **true** | `scene_shadows_x6.png` 2850×510; rebuilt from scene crops (470,455,700,530)/(1216,455,1446,530) = **0 px difference**; palette-safe |
| 25 atlas keys = 25 PNGs = 25 cells | **true** | 25 keys, 25 files, all atlas cells pixel-identical; no stale `_seamless`/`conduit` files |
| 3 medium + 3 mega types | **true** | console_bank 102×59, cargo_stack 59×87, server_rack 52×104; hull_frame 118×203, viewport 112×88, reactor_core 118×140 |
| 04 hull is 1:1 and unclipped | **true** | 04 sheet 1560×633; hull 354×609 at (83,12); exact 3.00×; top flange and base inside the cell; scene ribs are 1:1 448-px modules |
| 02/03/04 exact scale, no clipping | **true** | every tile 5.00×, every medium/mega 3.00×; 0 opaque-pixel mismatch against the shipped sprites |
| Packet current | **true for the ship** | 00/01/05/06 SHA-256 equal `tileset_preview_x8`/`tileset_sample_x4`/`ship_mega_preview`/`scene.png`; 02–04 rebuilt at 19:20; 06 is a copy of the shipped (stale-agent) scene |
| Palette / alpha | **true** | 0 palette violations for every tile, sprite, scene, focus and 6× plate; alpha exactly 0/255; scene 44 colours, mega 37; no pink/magenta pixels |
| Tile seams | **true for the repeats** | 12 repeating fills 0.00/0.00 on both axes; hazard 19.17/19.17 = interior 19.17; deck_step/deck_top/door/door_top are X-0.00 and one-shot on Y by design; door_top→door 0.00; deck_top→deck_fill 0.00; deck_step caps 0.00; deck_top→grate_top 14.10 and grate_top→grate_fill 11.34 are designed insets |
| Agent exactly once | **true** | scene − mega = **631 px**, one bbox (950,459)–(981,516): body 53 rows, 32 px wide, blade tip and 18-px shadow; no other pixel differs |
| Showcase reproducible | **false** | 303 px agent-only difference because the current idle frame post-dates the scene (Minor 2) |
| Rows 480–483 / 512–513 untouched | **shadow layer true; scene diff false** | the shadow layer starts at 484/514; the 26 px on 480–483 are the stale agent, not the shadow (Minor 2) |

---

## Per-item checklist

### 25 tiles (atlas 25 keys; 25 `tiles/` PNGs; 25 in 00 and 02)

| # | tile | verdict | note |
|---|---|---|---|
| 1 | `ceiling` | PASS | 6 colours; 2×2 0.00/0.00; two-panel coffer; continuous in the scene |
| 2 | `deck_fill` | PASS | 5 colours; 0.00/0.00; floor face rows 17–19 |
| 3 | `deck_left` | PASS (kit) | true mirror of `deck_right` (0.00 max 0); X 29.48 is the designed cap edge; not placed |
| 4 | `deck_right` | PASS (kit) | mirror; not placed |
| 5 | `deck_step` | PASS* | 7 colours; X 0.00, Y 152.67 one-shot; tread 155/111/111/78; 4× on the dais (vent repeats, Minor 11) |
| 6 | `deck_step_left` | PASS | cap; joint to `deck_step` 0.00; dais left end |
| 7 | `deck_step_right` | PASS | cap; joint 0.00; dais right end |
| 8 | `deck_top` | PASS* | 6 colours; X 0.00, Y 123.04 one-shot; lip 512–513; deck_top→deck_fill 0.00 |
| 9 | `deck_top_right` | PASS (kit) | corner cap; no left twin; not placed (Minor 16) |
| 10 | `door` | PASS | 7 colours; two leaves; gold threshold; 60-px clear; visible at 1× |
| 11 | `door_top` | PASS | 12 colours; lintel/transom/cyan display; joint to door 0.00 |
| 12 | `grate_fill` | PASS (kit) | 0.00/0.00; not placed; scene uses `grate_top` + `deck_fill` |
| 13 | `grate_top` | PASS | 0.00/0.00; top rail meets the lip; 2-tile inset at x=1024–1087; 1-px black frame is the designed inset |
| 14 | `hazard` | PASS | 3 colours; 19.17/19.17 = interior; 45° stripe continuous across the 5-tile pad (the pad starts 16 px into cell 38 and ends 15 px into cell 43; the 8-px period keeps the phase) |
| 15 | `light_strip` | PASS* | 8 colours; housing + cyan; five at x=5/13/25/37/43 (irregular spacing, Minor 8) |
| 16 | `pipe_h` | PASS | 0.00/0.00; rows 2/13; flanges; crosses the verticals |
| 17 | `pipe_v` | PASS* | 0.00/0.00; x=8/20/32; bottom flange offset (Minor 13) |
| 18 | `vent` | PASS | 6 colours; louvre; four at (6,9),(18,8),(28,9),(40,8); visible |
| 19 | `wall` | PASS | 0.00/0.00; framed panel band rows 3/12; across the bays |
| 20 | `wall_flat` | PASS | 5 colours; 0.00/0.00; wall field |
| 21 | `wall_flat_light` | PASS | 1-px cyan at x=9; 0.00; 256 px per bay; breaks at the panel bands (Minor 14) |
| 22 | `wall_flat_violet` | PASS | 1-px violet at x=22; 0.00; 256 px per bay; visible; pad no longer covers it |
| 23 | `wall_light` | PASS (kit) | 0.00; not in the scene; 5 uses in 01 |
| 24 | `wall_violet` | PASS (kit) | 0.00; not in the scene; 1 use in 01 |
| 25 | `window` | PASS* | 14 colours; planet/mullion/sill; (7,6) visible; (30,7) visible; one in 01; single-use by design |

### 3 medium

| item | verdict | note |
|---|---|---|
| `console_bank` 102×59 | PASS* | 28 colours; three screens; on the 6-tile dais; shadow 94/58/35 at 484–486; no fringe (violet is interior trim) |
| `cargo_stack` 59×87 | PASS* | 11 colours; 3 crates; scene has 3-crate + mirrored 2-crate; shadows 58/36/21; 0 overlap; 2-crate is a crop (Minor 12) |
| `server_rack` 52×104 | PASS* | 13 colours; louvers/screen/kick plate; shadow 52/28/17; 20×2 base hole (Minor 1); taller than the 60-px door (Minor 6) |

### 3 mega

| item | verdict | note |
|---|---|---|
| `hull_frame` 118×203 | PASS* | 1:1; 448-px rib; base flare; 39-px sleeve; 3 variants across five ribs; no footing shadow (Minor 3); 04 full |
| `viewport` 112×88 | PASS* | chamfer/recessed bezel/sill; glass mean 37.56 (Minor 5); one in the scene |
| `reactor_core` 118×140 | PASS* | 30 colours; X-braced base; shadow 118/118/73/44/14; 5-tile pad (160 px) with 21-px margins; 6× plate |

### Whole ship

| item | verdict | note |
|---|---|---|
| `05_whole_ship_x2.png` / `ship_mega_1x.png` | PASS* | 25 tiles, 3 medium + 3 mega types present; five ribs, one viewport, one reactor; palette/alpha/seams pass; no agent; shadows pass; minors 1, 3–8, 11–16 |
| `00_tileset_x8.png` | PASS* | 8× exact atlas; 25 tiles; 7 empty (Minor 9) |
| `01_tileset_sample_x4.png` | PASS* | 162-tile slice at 4×; no ceiling/door; hazard at row 7 (Minor 10) |
| `02_all_tiles_x5.png` | PASS* | 25 at 5.00×; labels; 5 empty (Minor 9) |
| `03_medium_catalog_x3.png` | PASS | three at 3.00×; no clipping; exact |
| `04_mega_catalog_x3.png` | PASS | three at 3.00×; hull 354×609 in a 633 cell, full; exact |
| `scene_focus_x4.png` | PASS* | 4× crop of agent/server/door/grate; current with the scene |
| `scene_shadows_x6.png` | PASS | 6× dais/pad plate; 0-px difference from the scene crop; palette-safe |

### Showcase

| item | verdict | note |
|---|---|---|
| `06_showcase_x2.png` / `scene_1x.png` | PASS* | agent exactly once (631-px diff, bbox 950,459–981,516); standing; 53 px vs 60-px opening; feet at 511 on lip 512; shadow 18/10/3 at 514–516; not floating; **stale frame** (Minor 2) |
| `scene_1x.png` agent scale | PASS | body 32×53; door 32×60 clear; 10 px left of the door; facing right |
| `scene_1x.png` agent shadow | PASS | 18 px solid at 514, 10 at 515, 3 at 516; aligned to both feet (feet 961–976) |
| `scene_focus_x4.png` / `scene_shadows_x6.png` | PASS* | 4× focus is 1280×768; 6× plate 2850×510; both current |

### 2×2 / seam checks

| group | result |
|---|---|
| 12 repeating fills: ceiling, deck_fill, wall, wall_flat, wall_flat_light, wall_flat_violet, wall_light, wall_violet, grate_fill, grate_top, pipe_h, pipe_v | X 0.00 / Y 0.00 on every tile; no visible seam in the 2×2 sheet |
| hazard | X 19.17 / Y 19.17 = interior 19.17; 2×2 and 4×4 continuous |
| deck_step, deck_top, door, door_top | X 0.00; one-shot on Y by design (152.67 / 123.04 / 48.72 / 37.05); used with caps/lintel |
| deck_left/right, deck_step_left/right, deck_top_right | designed caps; X 29.48–39.00; not fills |
| light_strip, vent, window | one-shot fixtures; X/Y edges are frames, not fills |
| cross-tile joints | door_top→door 0.00; deck_top→deck_fill 0.00; deck_step caps 0.00; wall variants 0.00; deck_top→grate_top 14.10 and grate_top→grate_fill 11.34 are 1-px designed insets |

---

## Bottom line

The v7 Major is fixed: the 192-px dais now carries a **192/120/72** dithered footprint at rows 514–516, matching the pad's **160/100/60**, with a solid first row, 5/8 and 3/8 falloff, no writes to the deck lip (512–513) or the dais/pad treads (480–483). The console (94/58/35), reactor (118/118/73/44/14), cargo (58/36/21), server (52/28/17) and agent (18/10/3) footprints are present and silhouette-derived. The hidden window is fixed, the pad is tightened to 5 tiles, the five ribs are no longer pixel-identical, the pad tread matches the dais, and the 6× plate is real and current. The 25 tiles, the 3 medium and 3 mega types, the palette/alpha, the 25-PNG tiles folder, the catalogs and the 1:1 hull all verify.

The remaining 16 items are polish/report issues: the server's 20×2 see-through base slot, the stale showcase agent (303 px, agent only), the five hull footings with no footprint under a literal reading, the pad's end caps, the dark viewport, the door-vs-props scale, the still-repeated ribs at 1×, the irregular ceiling lights, the packet framing, the 01 slice, the repeated dais tile, the cropped 2-crate, the offset pipe flanges, the accent breaks, the report's "0 px"/"rows 480–483"/"identical top edges" claims, and the cut scene edges. None of these is a blocker or a Major under the stated object list.

**Verdict: PASS. Blockers 0, Majors 0, Minors 16.**
