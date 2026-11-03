# Ship Environment — Independent Acceptance (v6)

**Verdict: FAIL**

PASS is not issued. There is **1 blocker and 2 majors**; any one of them is sufficient to fail the pack. No asset was modified; this report is the only write.

Scope: every PNG in `work/review/ship/` (`00`–`06`), the raw 25 tiles, the three medium and three mega sprites, the 1x mega and the 1x/2x showcase, `tileset.json`, `ship_layout.json`, the three `report.json` files, `environment/ship_assembly.py` (`_shadow`, `_paste_grounded`, `_rib_module`, `compose`), the door/window/deck/hazard builders in `environment/ship_tiles.py`, and `scripts/build_review_packets.py` (`_catalog` → `_grid_exact`).

Method: every image was opened; problem areas were examined at 2–16× nearest-neighbour crops. Alpha, palette, seams, repeat behaviour, density and luminance were measured directly from the PNGs. To isolate the contact shadows from the underlying art I re-ran `compose()` in `/tmp/opencode/ship/` twice (shadow patched to a no-op, and unpatched) and diffed; the pack's own pass flags are not used as evidence. The shipped previews and packet were also hash-compared (see the packet note).

---

## Blockers

### B1 — Contact shadows are still a 1-px dash/checker strip, not a contact footprint (v5 B1 not resolved)

**Files/elements:** every grounded object in `output/showcase/ship/scene_1x.png` and `06_showcase_x2.png`; code: `environment/ship_assembly.py`, `_shadow()` (rows `base_y+1 … base_y+4`). Cargo at x=154–212 and 234–292, console 525–626, server 872–923, agent 952–979, reactor 1253–1370.

v5's two worst symptoms *are* fixed and I verified them:

* row 512 of `scene_1x.png` is **1536/1536 pixels of the pure lip colour (155,155,176)** — no shadow pixel touches it;
* the agent's boots are separated from the shadow by that row; they read as boots, not as one black mass.

What remains is the shape and the pattern of the new shadow. It is a 4-row ordered dither whose first row is 75 % `palette 0`, i.e. **a 1-px-tall bar that is dark for 3 of every 4 columns** — a dashed line, not a falloff. Measured from the shadow-only diff (shipped scene vs a no-shadow compose):

| object | sprite | base | shadow rows | dark px / footprint width |
|---|---|---|---|---|
| cargo ×2 | 59×87 | 512 | 513–516 | 46 / 29 / 14 / 6 of 61 each |
| console | 102×59 | 480 (dais) | 481–484 | 73 / 47 / 23 / 11 of 97 |
| server | 52×104 | 512 | 513–516 | 42 / 27 / 13 / 6 of 56 |
| agent | 28×53 | 512 | 513–516 | 16 / 10 / 5 / 2 of **20** |
| reactor | 118×140 | 480 (pad) | 481–484 | 95 / 62 / 30 / 15 of 126 |

The first row is `(x)%4 != 0` (3 dark, 1 light), row 2 is a 50 % checker, row 3 is 25 %, row 4 is 12.5 %. At 1× it is a 1-px dashed run: on the 36-lum deck body it vanishes, and on the 80/113-lum bevel/tread it reads as dashes. At the shipped 2× (`05`/`06`) it reads as a **dashed line** under every object (verified at 2× and 6× on the cargo, server, agent, console and reactor bases).

It also lands on, and destroys, bright surfaces that the v5 shadow did not touch:

* `deck_top` row 1 (y=513, lum 80) — the lower half of the 2-px deck lip. Row 512 (lum 155) survives, but the lip now reads as 1 px light + 1 px dashed.
* `deck_step` rows 1–3 (y=481–483, lum 113/113/80) — the dais's 4-px tread. Row 480 (157) survives, so the console's step reads as 1 px light + 3 px dotted. The 2× crop shows the console standing on a **dotted tread**, and the no-shadow render shows the clean tread it replaced.
* `hazard` rows 1–4 (y=481–484) — the reactor pad's top gold stripe is chopped into black dashes.

The footprint is also a fixed rectangle taken from the bottom 4 sprite rows (+2 px each side), not the base silhouette, and the same 4-row strip is reused under objects of very different size (agent 53 tall vs reactor 140 tall) with no scaling of the falloff.

**Broken:** "Dithered contact shadows with a real contact footprint, below the deck's bright lip, reactor/console included; grounded objects" and "Showcase … contact shadow, not floating". v5 B1 is improved but not resolved.

---

## Majors

### M1 — Two pixel-identical cargo stacks, 21 px apart, in the first bay

**Files/elements:** `scene_1x.png` / `05_whole_ship_x2.png` / `06_showcase_x2.png`, left bay x=128–319; `cargo_stack/sprite.png` pasted at x=154 and x=234, same y (425–511); code `compose()` "Left bay: two cargo stacks side by side (no mirror flip)"; `ship_layout.json` "both unflipped".

Both instances are the same file, the same orientation, the same three crates, the same cyan and violet labels, the same internal hazard band, and the same shadow (46/29/14/6 each). The pasted rectangles differ only in 109 px where the sprite's transparent margins let a different wall column show through — the crates themselves are identical. The left bay therefore presents **six identical crates** as the first subject the eye reads.

The v5 defect (cargo ×2 overlapping the reactor hazard pad by 29 px) is gone — measured overlap is now 0 px — but the fix moved both stacks, unflipped, into one bay and created a copy-paste pair.

**Broken:** "whole ship assembles into one coherent scene" (same sprite, same decals, same light, 21 px gap).

### M2 — The reactor's "raised hazard pad" is a 32-px hazard-painted wall band, not a pad

**Files/elements:** `05`/`06`, x=1216–1407, y=480–511 (tiles 38–43); `reactor_core/sprite.png` at x=1253–1370, y=340–479; code `compose()` `HAZARD_BAY` + `_hazard_trim`.

The reactor's plinth occlusion is fixed: the X-braced base and its orange dashes are visible above y=480, and the old opaque bottom bar is gone. But what the reactor stands on has no pad geometry:

* the band's top row (y=480) is a raw hazard stripe — there is no tread, lip or bevel, so the reactor's base (y=479) meets a stripe, not an edge;
* the band has no cast shadow of its own on the deck, no side thickness and no termination other than the deck lip at y=512; remove the reactor and it is indistinguishable from a hazard-painted wall base;
* the reactor's contact is a stack of dark/dashed rows with no solid edge: the sprite's gold dashes (row 138) + 1-px black outline (row 139), the pad's stripe row 480, then the shadow's 75 % black row 481;
* the band is 192 px wide against the reactor's 118 px (37 px of hazard each side) and its mean luminance is 51.2 vs the deck's 36.7 and the wall's 41.0 — the brightest large surface in the right bay.

**Broken:** "dithered contact shadows with a real contact footprint … reactor/console included; grounded objects" (the reactor is grounded on a hazard band, not a readable platform) and "coherent composition". This is the residual of v5 B2: the plinth is visible, the "pad" is not modelled.

---

## Minors

1. **`04_mega_catalog_x3.png` crops the hull.** `hull_frame` is 118×203 → 354×609 at 3×; the cell is 520×520, `_grid_exact` pastes it at y=(520−609)//2 = −44, so 89 px (44 top + 45 bottom) are cut, including the top flange and the base plate. The visible width is 336 px (the shaft at 3×), not the 354 flange width, so the hull's full silhouette and its foot cannot be reviewed on `04`; viewport and reactor are exactly 3.00×. The shipped `mega/ship/elements/catalog_preview_x2.png` does show the full hull at 2×.
2. **`output/environment/ship/tiles/` ships 29 32×32 PNGs against 25 atlas keys.** `conduit_seamless.png`, `deck_seamless.png`, `grate_seamless.png` and `wall_seamless.png` are not in `tileset.json`; `conduit_*` is a dropped material that `REPORT.md` still lists. The fix report's "25 base PNGs on disk == 25 keys" is false.
3. **`ship_layout.json` (and the fix report) place the agent "in front of the door".** "idle frame 00 at x=934 (in front of the door, facing it)": the opaque body is x=952–979, the door x=992–1023. She stands 13 px left of the door, in front of the wall, facing right toward it. "Facing it" is true; "in front of it" is false.
4. **The showcase is not reproducible from the delivered character frame.** Rebuilding `compose(include_character=True)` differs from `scene_1x.png` in 435 px, bbox (951,459)–(980,513), all inside the agent body; `ship_mega_1x.png` is byte-identical. The shipped scene embeds an older `output/character/agent/idle/frames/frame_00.png` than the one on disk.
5. **The bays' right-hand violet accent is hidden in three of four bays.** The vertical pipes at tile x=9/21/33 sit on the bays' right-edge `wall_flat_violet` tile (288–319 / 672–703 / 1056–1087), so the opaque pipe covers the accent strip. The violet pixels measured at x=310/694/1078 (64 px each) are the pipe's own dots, not the accent; only bay 4 at x=1398 shows the accent (288 px). The cyan left accents at 137/457/841/1225 are visible. "Accents line up at both bay edges" is false for 3 of 4 bays.
6. **Five identical hull ribs** at x=0/320/704/1088/1408 (the alternate flip was removed); the X-braces and the new 39-px sleeve repeat at a 320-px pitch.
7. **The 6-tile dais repeats one `deck_step` tile**: six identical cyan labels and rivet patterns on the riser at a 32-px pitch.
8. **Viewport glass is still very dark** — mean 40.0, p10 8.3, 749 px of palette-56 dark violet in the sprite (asteroid/nebula and frame shading); at 1× it reads as a black panel (v5 minor 12, unchanged).
9. **The server (104) and cargo (87) are taller than the door frame (64; 60 px leaf opening).** The only door could not pass two of the three medium props. The agent (53) passes with 7 px headroom; the fix report's "64 px opening vs 53 px agent" quotes the frame, not the clear leaf opening (rows 452–511).
10. **`unify_light` is a 7-px rim only; the bodies are unchanged.** L−R over the outer 7 px is positive on all six (cargo +18.1, console +10.1, reactor +6.6, hull +15.3, server +38.6, viewport +19.0), but over the left/right thirds it is +5.4, +3.2, +0.4, +0.3, +17.3, +1.2 — the reactor, hull and viewport bodies are still mirror-symmetric, and the server's rim is 5.8× the reactor's. Direction is now consistent; "top-left light" is not readable on the megas beyond the rim. (The report's reactor "+9.2" is +6.6 over the same band.)
11. **Packet framing:** `00` uses 8×4 cells for 25 tiles (7 empty, ~22 %); `02` uses 6×5 (5 empty); `02` uses small default-font labels.
12. **`01` places the hazard at row 7 (floor front face)** and demonstrates no ceiling and no door; valid as a slice, not a full usage demo (v5 minor 9).
13. **`deck_top_right` has no left twin**; the top-corner cap set is right-only. The three cap tiles are kit-only (not placed in the scene).
14. **`REPORT.md` lists `conduit` as a tile material**; the 25-tile atlas has no conduit tile (see item 2).
15. **Fix-report inaccuracies (not asset defects):** "the review packet was not rebuilt" is false — `00`/`01`/`05`/`06` are byte-identical to the shipped previews (SHA-256 matches) and `02`–`04` were regenerated; "64 px opening" is the frame (60 px clear); the agent's shadow is 20 px wide, not "of 40"; "25 base PNGs" is 29; the agent is beside the door, not in front of it.

---

## Claimed fixes — verified

| claim | result | evidence |
|---|---|---|
| B1 lip untouched | **true, but residual** | row 512 = 1536/1536 lip; rows 481–483/513 chop the dais tread / deck bevel / pad stripe (B1) |
| B2 plinth visible | **true** | X-braced base + orange dashes visible above y=480; the "pad" itself is M2 |
| M1 no overlap | **true, new defect** | cargo/hazard overlap 0 px (was 29); duplicate pair instead (M1) |
| M2 hazard diagonal | **true** | tile invariant under (x+1,y−1); 2×2/4×4 continuous; seam 19.17 = interior 19.17 |
| M3 rib 1:1 base | **true** | 448 = 50 + 3×103 + 39 + 50; base flare ends at 512; flat 39-px plinth gone |
| M4 server rebuilt | **true** | 52×104, 13 colours, lit left, solid kick plate (transparency only in the foot gap, rows 101–103) |
| M5 window fixed | **true** | 14 colours, 0 violet, glass mean 41.9 (max 181.8), planet + single mullion + lit sill |
| M6 deck density | **true** | 5 colours, adj 4.90, mean 36.4 vs wall 4.12/36.7; seam 0.00 both axes |
| M7 door visible/usable | **true** | jambs 103/73 and 73/51 vs wall 36; lower pipe moved to row 13; leaf opening 60, agent 53; visible at 1× |
| M8 left-lit | **partial** | all six L−R > 0 in the outer 7 px; bodies still symmetric (minor 10) |
| M9 catalogs 3× | **partial** | `03` = 3.00× for all three; `04` hull clipped (minor 1) |

---

## Per-item checklist

### 25 tiles (atlas = 25 keys; 29 32×32 PNGs on disk)

| # | tile | verdict | note |
|---|---|---|---|
| 1 | `ceiling` | PASS | 2×2 exact (seam 0/0); bright lips at rows 0/31 |
| 2 | `deck_fill` | PASS | 5 colours, adj 4.90, mean 36.4; X/Y seam 0.00; plate joints/rivets read at 1× |
| 3 | `deck_left` | PASS | true pixel mirror of `deck_right` (`flip_equal`), kit-only |
| 4 | `deck_right` | PASS | mirror of `deck_left`; kit-only |
| 5 | `deck_step` | PASS* | tile is a readable 4-px tread + riser + grip strip; its tread is chopped by the console's shadow (B1) |
| 6 | `deck_step_left` | PASS | exact mirror of `deck_step_right`; darker outer edge |
| 7 | `deck_step_right` | PASS | mirror; dais ends close cleanly |
| 8 | `deck_top` | PASS* | lip/face tile; X seam 0.00; its row-1 bevel is chopped by the shadows (B1) |
| 9 | `deck_top_right` | PASS* | corner cap; no left twin (minor 13) |
| 10 | `door` | PASS | 32×32 double leaf; left jamb 103/73, right 73/51 (both > wall 36); gold threshold |
| 11 | `door_top` | PASS | lit lintel + transom (cyan) + leaf tops; X seam 0.00 |
| 12 | `grate_fill` | PASS | 2×2 exact; bars continue |
| 13 | `grate_top` | PASS | 2×2 exact; bright top rail meets the deck lip |
| 14 | `hazard` | PASS | 3 colours; (x+1,y−1) invariant; 2×2 and 4×4 continuous; seam = interior 19.17 |
| 15 | `light_strip` | PASS | housing + cyan emitter reads as a fixture (slightly monitor-like) |
| 16 | `pipe_h` | PASS | 2×2 exact; clamps/cyan/violet ticks |
| 17 | `pipe_v` | PASS | 2×2 exact; vertical run meets the lower pipe row |
| 18 | `vent` | PASS | centred louvre (x=5–26, y=6–25), wall panel frame |
| 19 | `wall` | PASS | 2×2 exact; framed panel band |
| 20 | `wall_flat` | PASS | 2×2 exact; 5 colours, adj 4.12 |
| 21 | `wall_flat_light` | PASS | 1-px cyan accent at x=9; stacks continuously |
| 22 | `wall_flat_violet` | PASS* | 1-px violet accent at x=22; hidden under the vertical pipe in bays 1–3 (minor 5) |
| 23 | `wall_light` | PASS | panel + left accent; kit-only |
| 24 | `wall_violet` | PASS | panel + left accent; kit-only |
| 25 | `window` | PASS | 14 colours; no violet; glass mean 41.9; cyan planet, vertical mullion, lit sill |

### 3 medium structures

| item | verdict | note |
|---|---|---|
| `console_bank` (102×59) | PASS* | dense (28 colours, adj 20.95); three screens; left-lit; the dais tread under it is dotted by B1 |
| `cargo_stack` (59×87) | PASS* | clean top-left stack, labels/straps/hazard; the scene places two identical copies (M1) |
| `server_rack` (52×104) | PASS | rebuilt: 13 colours, lit left housing, louvers, screen, connectors, solid kick plate, no interior hole |

### 3 mega elements

| item | verdict | note |
|---|---|---|
| `hull_frame` (118×203) | PASS* | 1:1 448-px module, real base flare, designed 39-px sleeve; the five ribs are identical (minor 6) |
| `viewport` (112×88) | PASS* | chamfer, recessed bezel, sill, top-left bevel; glass very dark (minor 8) |
| `reactor_core` (118×140) | PASS* | dense, symmetric machine; plinth visible; the hazard band/pad and contact are M2/B1 |

### Whole ship / showcase / packet

| item | verdict | note |
|---|---|---|
| `05_whole_ship_x2.png` / `ship_mega_1x.png` | **FAIL** | B1, M1, M2; 25 tiles, 3 medium + 3 mega types present; ribs ×5, viewport ×1, reactor ×1 |
| `06_showcase_x2.png` / `scene_1x.png` | **FAIL** | B1 (agent's shadow is a 20-px dashed strip); agent exactly once (diff vs mega = one 499-px cluster), standing, 53 px vs 60-px leaf opening, base row 511 vs deck 512 — not floating |
| `00_tileset_x8.png` | PASS* | 25 tiles at 8×, 7 empty cells |
| `01_tileset_sample_x4.png` | PASS* | valid tile slice; hazard at row 7; no ceiling/door demo |
| `02_all_tiles_x5.png` | PASS* | 25 labelled at exactly 5× (160×160); 5 empty cells |
| `03_medium_catalog_x3.png` | PASS | all three at 3.00× |
| `04_mega_catalog_x3.png` | **FAIL (packet)** | viewport/reactor 3.00×; hull 354×609 in a 520 cell → 89 px cut (top flange/base plate), visible width 336 (shaft) |
| `05_whole_ship_x2.png` | **FAIL** | as whole ship |
| `06_showcase_x2.png` | **FAIL** | as showcase |

Note on the packet: the fix report says `00`–`06` were not rebuilt. That is wrong. `00`/`01`/`05`/`06` are byte-identical (SHA-256) to `tileset_preview_x8.png`, `tileset_sample_x4.png`, `ship_mega_preview.png` and `scene.png`, and `02`–`04` are regenerated at 17:19, so the packet is current v6 and usable as evidence.

---

## Bottom line

The basic pixel work is substantially improved and passes: 25 tiles, 3 + 3 types, palette locked (0 violations in every shipped asset; the review sheets `02`–`04` use a non-palette background and label colour), alpha hard 0/255 with no magenta/purple fringe or halo (the reactor's dark-violet silhouette pixels are a deliberate dark outline, not a bleed), every repeating fill tile is exactly seamless (12 fills at 0.00 on both axes; `deck_top`/`deck_step` are 0.00 on X and intentionally differ on Y), the hazard is now a real continuous 45° diagonal, the dais reads as a step, the door has two lit jambs and a clear 60-px leaf opening, the server is rebuilt, the window's purple bar is gone, the deck now matches the wall's density, and the hull rib stands on its real base flare at the floor line.

The pack still fails on the one thing v5 blocked it for. The contact-shadow pass is a 4-row screen-space dither rectangle whose first row is a 3:1 comb of the darkest palette entry: at 1× it is invisible on the dark deck, and at 2× it reads as a dashed line under every object; on the bright surfaces it is actively destructive — it chops the dais's 4-px tread into a dotted line, the deck lip's bevel into dashes, and the reactor pad's top gold stripe into a dashed border. Together with the 32-px "hazard pad" that has no top face and the twice-pasted cargo stack, the integration does not yet meet "dithered contact shadows with a real contact footprint … reactor/console included; grounded objects" or "one coherent scene".

**Verdict: FAIL. PASS not issued.**
