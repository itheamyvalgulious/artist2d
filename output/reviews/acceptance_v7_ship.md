# Ship Environment — Independent Acceptance (v7)

**Verdict: FAIL**

**Blockers: 0. Majors: 1. Minors: 14.** PASS is not issued: the Major alone is sufficient. No asset was modified; this report is the only write.

**Scope:** every PNG in `work/review/ship/` (`00`–`06`); the 25 `tiles/` PNGs, `tileset.png`, `tileset_sample.png`, `tileset.json`; the three medium sprites (`sprite.png`, `sprite_x4.png`, catalogs) and the three mega sprites; `ship_mega_1x.png`, `scene_1x.png`, `scene.png`, `scene_focus_x4.png`; the 1× catalogs/previews; `ship_layout.json`, the three `report.json` files, `REPORT.md`; `environment/ship_assembly.py` (`compose`, `_pad_tread`, `_shadow`, `_contact_depths`, `_paste_grounded`); `scripts/build_review_packets.py` (`_catalog`).

**Method:** every packet image opened and problem areas re-examined at 2–16× nearest-neighbour crops. Alpha, palette, seams and shadow shapes were measured from the PNGs. To isolate the contact shadows I re-ran `compose()` in `/tmp/opencode/shipv7/` with `_shadow` patched to a no-op and diffed it against the shipped scene; the shipped `scene_1x.png` and `ship_mega_1x.png` were also compared with a fresh `compose()` (0 px difference). The 02/03/04 sheets were matched against exact 5×/3× scaled sprites, the 00/01/05/06 SHA-256-compared with the shipped previews, and the 25 atlas cells compared pixel-for-pixel with the individual tiles. The pack's own pass flags are not used as evidence.

---

## Blockers

None.

---

## Majors

### M1 — The 6-tile dais has no contact footprint at its deck junction; the identical pad does

**Files/elements:** `scene_1x.png`, `06_showcase_x2.png`, `05_whole_ship_x2.png` / `ship_mega_1x.png`: dais x=480–671 (tiles 15–20), base row 511; deck lip rows 512–513; the shadow should start at row 514. Code: `environment/ship_assembly.py` `compose()` appends the hazard pad to `shadows` (`shadows.append((pad_x0, np.full(pad_x1 - pad_x0, 3, dtype=int), FLOOR_ROW * TILE_SIZE + DECK_LIP))`) but never appends the dais.

**Measured (shipped scene minus a no-shadow compose):** rows 514–516 contain shadow runs only at x=144–201 (cargo 3-crate), 245–302 (cargo 2-crate), 872–923 (server), 960–977 (agent), 1216–1407 (pad). The dais's 192-px base has **0 shadow pixels**. The pad, an identical 32-px platform at x=1216–1407, gets 192/120/72 px at the same rows; the cargo/server/agent get 58/36/21, 52/28/17 and 18/10/3.

**Defect:** At 1× and 2× the dais reads as part of the floor while the pad reads as a grounded block. The console's shadow (94/58/35 at rows 484–486) is on the dais's *face*, below the dais's top tread, not under the dais's base; the dais's base at the deck lip has no core and no falloff. The pack's own v7 rule ("the pad itself is a contact object, so its own footprint gets a solid core + falloff") is not applied to the same 32-px platform type.

**Requirement broken:** "Contact shadows: a real dithered footprint below every lip/tread, solid core + falloff, not a dashed line; reactor/console/agent included; grounded." The deck lip under the dais is a lip carrying no footprint. Also "one unified side-view … interior."

**Fix:** append the dais to `shadows`, e.g. `(480, np.full(192, 3, dtype=int), 16 * 32 + DECK_LIP)`, and rebuild. That yields 192/120/72 at rows 514–516, matching the pad. The dais's own tread rows 480–483 must stay untouched (the console's shadow already starts at 484).

---

## Minors

1. **The window at tile (8,6) is 100% hidden by the vertical pipe.** `compose()` uses `windows = {(8, 6), (30, 7)}`; the v7 pipe move to x=8 puts `pipe_v` at x=256–287 over the entire window cell x=256–287, y=192–223. The only visible window is at x=960–991. New regression introduced by the "conduits moved 1 tile left" fix; the `window` tile itself, the atlas, 00/01/02 and the visible (30,7) window are fine. Requirement: "windows" / "one coherent scene." Fix: move the window to (7,6)/(6,6) or the pipe, and re-check the accent.
2. **The reactor pad is 192 px wide against a 118-px reactor** (37 px of hazard on each side). It now has tread, ends and its own shadow, but it is a wide platform, not a tight one (fix report risk 1). Requirement: "one coherent scene."
3. **Five identical ribs** at x=0/10/22/34/44, 320-px pitch; the X-braces, orange status ticks and 39-px sleeve repeat (v6 minor 6). Requirement: "one unified … interior."
4. **The 6-tile dais repeats one `deck_step` tile**: the recessed vent slot repeats at a 32-px pitch; v6 minor 7 remains (now without the cyan label).
5. **Viewport glass is dark**: mean 37.9, p10 8.3 over the inner glass; at 1× it reads as a black panel; the small window at (30,7) is 58.1 mean. v6 minor 8.
6. **Server (104) and cargo (87) are taller than the door frame (64; 60 px clear).** The only door could not pass two of the three medium props; the agent (53) fits with 7 px headroom. v6 minor 9.
7. **`unify_light` is a rim-only pass.** Outer-7-px L−R: cargo +18.1, console +10.1, server +38.6, hull +15.3, reactor +6.6, viewport +19.0; left/right thirds +5.4, +3.2, +17.3, +0.3, +0.4, +1.2. The reactor/hull/viewport bodies remain near mirror-symmetric; the server's rim is 5.8× the reactor's. The fix report's updated numbers (+21.0/+9.4/+10.5/+16.9/+38.9/+18.8; thirds +1.9/+3.0/+1.5) do not reproduce. v6 minor 10.
8. **Packet framing:** `00` puts 25 tiles in 8×4 cells (7 empty, ~22 %); `02` uses 6×5 (5 empty) and small default-font labels. v6 minor 11.
9. **`01` places the hazard at row 7 (floor front face)** and demonstrates no ceiling and no door; valid as a tile slice, not a full usage demo. v6 minor 12.
10. **`deck_top_right` has no left twin**; the top-corner cap set is right-only and kit-only (not placed). v6 minor 13.
11. **The 2-crate cargo variant is a crop** (row 26) of the shipped `cargo_stack/sprite.png`, not a separate shipped file; `03_medium_catalog_x3.png` shows only the 3-crate; documented in `ship_layout.json` / `_cargo_low()`. Fix report risk 9.
12. **The pad's overhang row 483 is pure black across all 192 px**, and the reactor's two solid shadow rows 484–485 sit immediately under it: at 2× the pad's top edge has a 3-row black band under the tread. The dais's 4th tread row is 80 (bevel), not black; the two platforms' top edges are inconsistent. Fix report risk 3.
13. **Report/measurement inaccuracies:** the fix report's "whole shadow set is 1267 px" contradicts its own table (1294) and the measured 1298; "all four bays now measure 180 cyan / 180 violet" is not reproduced (accent-colour counts in the bay-edge columns are 304–360 px; bay 4 is 304 because the pad covers its lower 32 px; the accents are visible, the 180 figure is unexplained); "`04` is still the v6 sheet until the packet is rebuilt" is stale — `04` is 1560×633 and the 354×609 hull at (83,12) is fully visible; the claim that `work/review/` was not written applies to the fix pass, but the packet has since been rebuilt (`02`–`04` at 18:17) and is current. These are report defects, not asset defects.
14. **The packet's focus is 4×, not 6×.** `scene_focus_x4.png` is a 4× crop; there is no 6× shadow plate in `work/review/ship/`. I used 6×/8×/12× crops from `scene_1x.png` for this review; if a 6× packet image is required, it is missing.

---

## Claims verified (not taken on trust)

| v7 claim | result | evidence |
|---|---|---|
| B1: solid core + falloff, silhouette footprint, height scales | **true for every object that receives a shadow** | row 514: 378 px = 58+58+52+18+192, all 100 %; rows 484–488: 212/176/109/44/14 (solid cores 94/94 and 117/117); heights 3 (small props) and 5 (reactor); footprints 58 (cargo), 94 (console), 52 (server), 18 (agent), 118 (reactor), 192 (pad) |
| B1: no lip/tread is touched | **true** | no changed pixel on rows 480–483 or 512–513; shadows start at 484 / 514 |
| B1: applies to every grounded object | **false at the dais** | rows 514–516 have no run in x=480–671 → M1 |
| M1: cargo pair no longer identical | **true** | 3-crate at x=143 (58/36/21), 2-crate mirrored at x=245 (58/36/21), 43-px gap, 0 px overlap; the crates differ |
| M2: reactor pad is a real platform | **true, wide** | tread rows 480–482 (155/111/111), overhang 483, hazard 484–511, 3-px caps; pad shadow 192/120/72 at 514–516; reactor shadow 117/117/73/44/14 at 484–488; tread intact |
| 04: hull no longer clipped | **true** | sheet 1560×633; hull 354×609 at (83,12); top flange and base plate inside; hull/viewport/reactor all exactly 3.00× |
| 25 atlas keys == 25 PNGs in `tiles/` | **true** | 25 files = `tileset.json` keys = 25 atlas cells; no `*_seamless` / `conduit` files |
| layout wording | **true** | agent body x=950–981, 10 px left of door x=992–1023, "facing right toward it" |
| showcase reproducible | **true** | shipped `scene_1x.png` vs fresh `compose()` = 0 px; `ship_mega_1x.png` = 0 px |
| packet current | **true** | 00/01/05/06 SHA-256 match `tileset_preview_x8`/`tileset_sample_x4`/`ship_mega_preview`/`scene.png`; 02–04 regenerated at 18:17; 04 is the new sheet |
| palette / alpha | **true** | scene 43 colours, 0 non-palette, alpha 255; sprites alpha 0/255, 0 magenta; 02–04 use review-sheet background/label colours, not asset violations |
| seams | **true** | 12 repeating fills 0.00/0.00; hazard 19.17 = interior 19.17; `deck_top` X 0.00 / Y 123.04 and `deck_step` X 0.00 / Y 152.67 (one-shot by design); `door_top`→`door` 0.00 |
| agent exactly once | **true** | scene−mega = 631 px, bbox (950,459)–(981,516), four clusters: body 595, blade tip 5, shadow 30 + 1; no other pixel differs |

---

## Per-item checklist

### 25 tiles (atlas 25 keys; 25 `tiles/` PNGs; 25 in 00 and 02)

| # | tile | verdict | note |
|---|---|---|---|
| 1 | `ceiling` | PASS | 6 colours; 2×2 0.00/0.00; two-panel fixture; top/bottom lips; rows 0–63 |
| 2 | `deck_fill` | PASS | 5 colours; 0.00/0.00; 34 uses in 01; floor face |
| 3 | `deck_left` | PASS (kit) | true mirror of `deck_right`; X 29.48 is the designed outer edge; not placed |
| 4 | `deck_right` | PASS (kit) | mirror; not placed |
| 5 | `deck_step` | PASS* | 7 colours; X 0.00, Y one-shot 152.67; tread 156/113/113/80; vent slot rows 28–31; dais uses it 4×; console shadow 484–486 below the tread |
| 6 | `deck_step_left` | PASS | cap; joint to `deck_step` 0.00; dais left end |
| 7 | `deck_step_right` | PASS | cap; joint 0.00; dais right end |
| 8 | `deck_top` | PASS* | 6 colours; X 0.00, Y one-shot 123.04; lip 512–513; row 2 body; shadows 514+ |
| 9 | `deck_top_right` | PASS (kit) | corner cap; no left twin (minor 10); not placed |
| 10 | `door` | PASS | 7 colours; two leaves; gold threshold; 60-px clear; agent 53; visible at 1× |
| 11 | `door_top` | PASS | 12 colours; lintel/transom; joint to door 0.00 |
| 12 | `grate_fill` | PASS (kit) | 0.00/0.00; not placed; scene uses `grate_top` + `deck_fill` |
| 13 | `grate_top` | PASS | 0.00/0.00; top rail meets the lip; grate x=1024–1087; 1-px black frame at row 513 is the inset |
| 14 | `hazard` | PASS | 3 colours; (x+1,y−1) invariant; 2×2/4×4 continuous; wrap 19.17 = interior; pad face; reactor shadow |
| 15 | `light_strip` | PASS* | 8 colours; housing + cyan; five at x=5/13/25/37/43; slightly monitor-like |
| 16 | `pipe_h` | PASS | 0.00/0.00; rows 2/13; flanges; crosses the verticals |
| 17 | `pipe_v` | PASS* | 0.00/0.00; x=8/20/32; hides the window at (8,6) (minor 1) |
| 18 | `vent` | PASS | 6 colours; louvre; four at (6,9),(18,8),(28,9),(40,8); visible |
| 19 | `wall` | PASS | 0.00/0.00; framed panel band rows 3/12; across the bays |
| 20 | `wall_flat` | PASS | 5 colours; 0.00/0.00; wall field |
| 21 | `wall_flat_light` | PASS | 1-px cyan at x=9; 0.00; bay left edges |
| 22 | `wall_flat_violet` | PASS* | 1-px violet at x=22; 0.00; visible; pad covers lower 32 px in bay 4 |
| 23 | `wall_light` | PASS (kit) | 0.00; not in the scene; 5 uses in 01 |
| 24 | `wall_violet` | PASS (kit) | 0.00; not in the scene; 1 use in 01 |
| 25 | `window` | PASS* | 14 colours; planet/mullion/sill; (8,6) hidden by the pipe (minor 1); (30,7) visible; one in 01 |

### 3 medium

| item | verdict | note |
|---|---|---|
| `console_bank` 102×59 | PASS* | 28 colours; three screens; on the 6-tile dais; shadow 94/58/35 at 484–486; the dais's own base shadow is M1 |
| `cargo_stack` 59×87 | PASS* | 11 colours; 3 crates; scene has 3-crate + mirrored 2-crate; shadows 58/36/21; 0 overlap |
| `server_rack` 52×104 | PASS | 13 colours; louvers/screen/kick plate; shadow 52/28/17; taller than the 60-px door (minor 6) |

### 3 mega

| item | verdict | note |
|---|---|---|
| `hull_frame` 118×203 | PASS* | 1:1 448-px rib; base flare; 39-px sleeve; five identical (minor 3); 04 full |
| `viewport` 112×88 | PASS* | chamfer/recessed bezel/sill; glass mean 37.9 (minor 5); one in the scene |
| `reactor_core` 118×140 | PASS* | 30 colours; X-braced base visible; shadow 117/117/73/44/14; pad 192 wide (minor 2) |

### Whole ship

| item | verdict | note |
|---|---|---|
| `05_whole_ship_x2.png` / `ship_mega_1x.png` | **FAIL** | M1; minors 1–14; 25 tiles and 3 medium + 3 mega types present; five ribs / one viewport / one reactor; palette/alpha/seams pass; no agent |
| `00_tileset_x8.png` | PASS* | atlas at 8×; 25 tiles; 7 empty (minor 8) |
| `01_tileset_sample_x4.png` | PASS* | 162-tile slice at 4×; hazard at row 7; no ceiling/door (minor 9) |
| `02_all_tiles_x5.png` | PASS* | 25 at 5.00×; labels; 5 empty (minor 8) |
| `03_medium_catalog_x3.png` | PASS | three at 3.00×; no clipping |
| `04_mega_catalog_x3.png` | PASS | three at 3.00×; hull 354×609 in a 633 cell, full; v6 minor 1 fixed |

### Showcase

| item | verdict | note |
|---|---|---|
| `06_showcase_x2.png` / `scene_1x.png` | **FAIL** | M1 (the dais is in the showcase); the agent itself is exactly once (631-px diff, bbox 950,459–981,516), standing, 53 px vs 60-px opening, feet at 511 on lip 512, shadow 18/10/3 at 514–516, not floating; scale correct |
| `scene_focus_x4.png` | PASS* | 4× crop of agent/server/door/grate; the 4× (not 6×) is minor 14 |

---

## Bottom line

The v6 shadow blocker's *shape* is fixed for the objects that receive a shadow: the footprints are now silhouette-derived, the first row is 100 % solid, the falloff is 5/8–3/8 (3 rows; 5 for the reactor), and the shadows never touch the deck lip (512–513) or the dais/pad treads (480–483). The two v6 majors are fixed (the cargo pair is now a 3-crate plus a mirrored 2-crate; the reactor pad has a tread, side face, chamfered ends and its own 192/120/72 shadow). The 04 hull is fully visible, the 25-PNG tiles folder is clean, the layout wording and the showcase reproducibility are correct, and the packet is current.

The pack still fails that requirement's coverage: the 192-px dais under the console has **zero** contact pixels at rows 514–516 while the identical 192-px pad has a full 192/120/72 footprint. That is a Major against "a real dithered footprint below every lip/tread … grounded" and it is visible at 1× and 2× in both `05` and `06`. The hidden window at (8,6), the 192-px pad, the five identical ribs, the repeated dais tile, the dark viewport, the door-vs-server/cargo scale, the rim-only light, and the packet/report minors are secondary but real.

**Verdict: FAIL. PASS not issued.**
