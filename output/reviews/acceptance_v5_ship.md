# Ship Environment — Independent Acceptance (v5)

**Verdict: FAIL**

PASS is not issued. There are **2 blockers and 9 majors**; any one of the blockers is sufficient to fail the pack. No asset was modified; this report is the only write.

Scope: every PNG in `work/review/ship/` (`00`–`06`), plus the raw tiles, props, mega sprites, the 1x mega assembly and the 1x showcase under
`output/environment/ship/`, `output/mega/ship/`, `output/showcase/ship/`, and the generator `environment/ship_assembly.py`
(`_shadow`, `_paste_grounded`, `_rib_module`, `compose`). `tileset.json`, `ship_layout.json` and the two catalog sheets were used for cross-checks.
Method: every image was opened; problem areas were examined at 7–14× nearest-neighbour crops; alpha, edge, luminance and repeat measurements were made
directly from the PNGs. The pack's own `report.json` pass flags are not used as evidence.

---

## Blockers

### B1 — Contact shadows are an opaque black sawtooth, not a contact footprint
**Files/elements:** `output/showcase/ship/scene_1x.png` and `06_showcase_x2.png`, agent at x≈242–270, feet rows 505–511, deck surface y=512;
also every grounded prop; code: `environment/ship_assembly.py`, `_shadow()` / `_paste_grounded()`.

`_shadow()` stamps 4 rows of **opaque palette-0 (8,8,12)** at `base_y` directly over the deck/dais 1-px rim light (**155,155,176**). The dark
dither is a weak stipple on the deck body (`deck_fill` mean 29.8 vs the 8,8,12 stamp), but its high-contrast result is that it punches a 1-px-comb
pattern through the floor's bright lip. Measured in `scene_1x.png`:

| object | x | rows | black px on the rim row (of width) |
|---|---|---|---|
| cargo | 162–221 | 512–515 | 44 / 29 / 19 / 11 of 60 |
| console (on dais) | 525–627 | 480–483 | 71 / 47 / 31 / 18 of 102 |
| server | 900–955 | 512–515 | 41 / 27 / 18 / 10 of 55 |
| agent | 242–270 | 512–515 | 11 / 6 / 14 / 2 of 28 |

The agent's boots are themselves near-black (`8,8,12`) and the shadow starts immediately under them, so the boots and the shadow merge into one black
mass; at 1× and at the shipped 2× the feet are no longer readable as feet. The effect is a sawtooth/comb, not a shadow. **Broken:** “Dithered contact
shadows with a real contact footprint (including reactor/console), grounded objects” and “Showcase … contact shadow, not floating”.

### B2 — Reactor has no contact shadow, and its base/plinth is cut off by the hazard band
**Files/elements:** `output/mega/ship/ship_mega_1x.png`, reactor x=1285–1403; `05_whole_ship_x2.png` far right; `ship_layout.json`.

The reactor's `_shadow(scene, rx-4, FLOOR_ROW*TILE_SIZE, …)` is called **before** the deck is pasted, and the deck loop (`for row in range(FLOOR_ROW+1, H)`
plus `deck_top` at row 16) overwrites rows 512–515. Measured under the reactor in rows 512–515: **0 / 0 / 0 / 0** black pixels; the 4-row mean is 100.0,
identical to bare floor. There is no contact shadow at all.

The hazard band (x=1248–1408, y=480–511) is pasted **after** the reactor, so it covers the reactor's bottom 32 px — about 23 % of its 140-px
height — including the X-braced base and its orange dashes. Only the top ~8 px of the 40-px plinth remain visible; the visible reactor ends in a flat
horizontal cut at y=480 and appears to stand behind the hazard rather than on the deck. **Broken:** “dithered contact shadows with a real contact footprint (including reactor/console), grounded objects”; the “including reactor”
case is explicit.

---

## Majors

### M1 — Right bay: cargo overlaps the reactor's hazard pad; the bay is overfull
**Files/elements:** `05_whole_ship_x2.png`, right bay; `ship_layout.json` “cargo_stack … x=38 (flipped)”; `compose()`.

Right cargo occupies x=1218–1277; the hazard band occupies x=1248–1408. Overlap = **29 px**. The hazard's left trim at x=1248 (the dark/gold end cap
from `_hazard_trim`) is hidden behind the crate, so the band starts at the crate with no termination; the crate's own gold diagonal hazard band at its
base sits adjacent to the floor band's gold chevrons. The 192-px slot bay (x=1216–1408; 202 px between the rib art) must hold the cargo (59 px) plus
the hazard pad (160 px) = 219 px of occupied width, with the 118-px reactor standing inside the hazard; 219 > 192, so the cargo necessarily overlaps the
pad. The reactor is pushed to 1285–1403 (5 px from the rib at 1408, with 37 px of hazard on its left and 5 px on its right). **Broken:** “whole ship
assembles into one coherent scene”, grounded/coherent composition.

### M2 — `hazard.png` does not tile as a diagonal; a multi-tile run becomes chevrons
**Files/elements:** `output/environment/ship/tiles/hazard.png`; `02_all_tiles_x5.png`; 2×2 repeat; `01_tileset_sample_x4.png` 2×1 patch; `05` 5×1 band.

The tile's left column equals its right column and its top row equals its bottom row (**seam ratio 0.00 on both axes**). An independent 2×2 repeat
therefore mirrors the 45° stripes at every 32 px, and the 2×1 / 5×1 runs in the sample and the ship read as a row of chevrons, not as a continuous
diagonal hazard stripe. If chevrons are the intent, the tile must be authored as a chevron pair and documented; as delivered, the “25 tiles that tile
seamlessly … hazard” claim is false for this tile. (The same edge-mirror also creates a visible pattern break at every tile boundary.) **Broken:**
“25 tiles that tile seamlessly: … hazard”.

### M3 — Hull rib base is a flat 39-px black plinth that slices the rib's detailed foot
**Files/elements:** `output/mega/ship/ship_mega_1x.png` at x=0/320/704/1088/1408; `environment/ship_assembly.py`, `_rib_module()`.

The 118×203 source rib's foot is pasted at module y=359–408; the module then draws
`rectangle([px, 409, px+w-1, 447], fill=palette 1)` plus 1-px vertical stripes — a **39-px, 118-px-wide solid near-black block** — to reach the
448-px floor. It cuts the X-braced foot at y=408/409, covers the wall's base trim, and has no shading, bevel, or contact shadow. The block repeats
five times across the room. **Broken:** “hull rib scaling”, “grounded objects”, “no mismatched density”.

### M4 — Server rack is under-detailed and flat relative to the console
**Files/elements:** `output/environment/ship/props/server_rack/sprite.png` (55×105); `03_medium_catalog_x3.png`; `05`.

The rack is a flat dark rectangle: a plain gray header, 1-px horizontal slot lines, two thin LED columns, no side panels, no depth, no proper feet
(two 10-px side tabs and a 1-px rear rail), no bevels. Its base has a **35×4 transparent slot** (rows 100–103, x=10–44) above a 1-px bottom rail, so
on a bright floor the chassis is hollow. Its light is top-only (T−B luminance +52.4, L−R +5.5) rather than the tiles'/cargo's top-left. Compared with
the console (102×59 with three detailed screens, key rows, cables, canopy) the density is clearly mismatched. **Broken:** “no mismatched density”, “consistent top-left light”,
“grounded objects”.

### M5 — Window tile: purple blob in the pane, near-black glass, no recess/glow
**Files/elements:** `output/environment/ship/tiles/window.png` (and `window_x8.png`); `02`; `01` at (192,64); `05` at (256,192) and (960,288).

A **9×1 pure-violet bar with a 3×3 darker violet block and a 1-px gray thruster** sits in the lower-left pane (row 19, x=5–13). It is probably
intended as a distant ship, but at 1× it reads as a plus/compression artifact; it is not an alpha fringe (all cutout pixels are 0/255), yet it is an
unexplained purple detail at the only window's focal point. The panes are below 25 luminance except a thin top gradient, with a handful of gray
specks; at 1× the tile reads as a framed vent/picture rather than a window. The tile is dropped straight onto wall panels with no recess, sill, or
cyan glass glow, and is the only 32-px window in the pack. **Broken:** “readable windows/emissives”; the purple artifact also conflicts with
the spirit of the no-magenta/purple-artifact rule.

### M6 — Floor is a near-featureless void; density mismatch with the wall
**Files/elements:** `output/environment/ship/tiles/deck_fill.png`, `deck_top.png`; `05`/`06` bottom 20 %.

`deck_fill` uses **5 colours**, has a mean absolute adjacent-column difference of **0.90**, and a mean luminance of **29.8**. The wall tiles use 5–7
colours, 4–15 adjacent-column difference, 39–42 mean; the ceiling is 52.9. The floor in `05`/`06` is a large dark band with three faint lines; the
only bright floor element is the 1-px deck lip, which is exactly what B1 destroys. The bottom fifth of the scene reads as empty rather than as a
deck. **Broken:** “no mismatched density”, “grounded objects”.

### M7 — Door is hard to see, is in the wrong bay, and is too small for the bay's equipment
**Files/elements:** `05`/`06` door at x=1024, y=448–512; `door.png` / `door_top.png`; `ship_layout.json`.

The 32×64 door has a left frame at (78,78,99) but a right frame at (20,20,28)/(35,35,46), i.e. the right edge is darker than the wall's interior
(35,35,46); the right jamb visually disappears. At 1× the only reliable cues are the 4×4 cyan indicator in `door_top` and the 3-px gold threshold;
the door reads as a dark recess. Placement: `ship_layout.json`/`compose()` say the door is “in the clear bay between the cockpit console and the rib”,
but the console bay is x=448–704 and the door is at 1024, in the next bay (832–1088) beside the server (900–955), 69 px from the server and 32 px
from the rib. Clear opening is 24 px; the agent's body is ≈16 px (it fits), and 64 px door vs 53 px agent is fine — but the cargo (87) and server
(105) are taller than the 64-px door, and the console reaches 91 px with its 1-tile dais (the bare console is 59); the only opening cannot pass two
of the three props and only fits the console with the dais removed. **Broken:** “the door must be visible in the scene”; “a usable door at the
agent's scale” is only marginally met (agent passes, equipment does not); coherent bay access.

### M8 — Lighting is not consistently top-left across the three mediums and three megas
**Files/elements:** sprite luminance, left 8 columns vs right 8 columns; `03`/`04` and `05`.

Measured left-minus-right mean luminance: cargo **+3.0** (left lit), console **−3.1** (right rail is the lit side; its left is the dark cut-out),
reactor **−1.1** (right-biased and mirror-symmetric), hull **+0.2** (sides equal), server **+5.5** (top-only, T−B +52.4). The tiles, door, window and
cargo are top-left; the console's gray side rail is on its right, the reactor's left and right rails are lit identically, and the hull's sides have
equal luminance (+0.2) despite their different content. **Broken:** “consistent top-left light”.

### M9 — 03/04 review catalogs are per-sprite fit, not the labelled x3 (packet, not shipped asset)
**Files/elements:** `work/review/ship/03_medium_catalog_x3.png`, `04_mega_catalog_x3.png`; `scripts/build_review_packets.py`, `_catalog` →
`_paste_center`.

Each sprite is first scaled by the nominal factor and then `_paste_center` re-fits it to the 520-px cell, so every sprite gets a different final
scale: console ≈4.89×, cargo ≈5.75×, server ≈4.76×; hull ≈2.46× (fit by height) vs viewport/reactor 3×. The hull (118 px wide) therefore appears
**narrower** (290 px) than the viewport (336 px) even though it is wider; the server and cargo both appear 500 px tall although the server is 105 vs
87. The “x3” filename/manifest claim is wrong, and the hull rib scale cannot be judged from `04`; the scale check had to use the 1× `05` and the
`metadata.json` sizes. **Broken:** the review packet's own scale claim; “check the hull rib scaling”.

---

## Minors

1. **`deck_top_left.png` is orphaned.** It exists on disk (12:03) but is not in `tileset.json` or `02_all_tiles_x5.png`; the atlas registers 25 tiles
   while 26 base tile PNGs exist. The platform-corner set is asymmetric and the left-top corner cannot be found from the atlas.
2. **The “left/right” cap tiles are noise variants, not mirrored caps.** `deck_left` vs `deck_right` mean diff 3.5, `deck_step_left` vs
   `deck_step_right` 4.2; neither pair is a flip of the other (`flip_equal = False`). The deck/step “L/R” variants keep the accent on the same side;
   the manifest's “3 real platform-step variants” are near-duplicate noise variants.
3. **Dais face reads as a low wall, not a step.** Six identical `deck_step` bays, each a 32-px framed panel with a checkerboard vent band; the
   “tread” is a 2-px line; the console sits on it, but the riser/tread geometry is not a step and the dais has no base shadow.
4. **Wall “clusters” are ad-hoc.** The `compose()` cluster code writes `wall` only on the top row and `wall_light`/`wall_violet` on the sides; there
   is no bottom frame, and the accent on those tiles is 8 px inside the tile edge, so the “frames” are off-centre and the wall reads as random panel
   variation rather than designed bays.
5. **Console centre screen is blown out** (near-white) versus the detailed left/right screens; with the 1-tile dais the console top (421) is 27 px
   above the door top (448) and 38 px above the agent's head (459); its control ledge sits at ankle height relative to an operator on the dais.
6. **Server base slot** (see M4): 35×4 transparent, shows the background on bright floors; the base is a 1-px rear rail on two 10-px side legs.
7. **Showcase framing/contact seam.** The agent (53 px, 8.3 % of the 640-px image height) stands at x=242 with its feet (256–263) on the grate at
   x=256; the 11-px shadow (254–265) straddles the deck/grate seam under the foot's left edge. It is easy to miss in the 1536-px room and the
   contact is at the busiest part of the floor. It is exactly once; its scale against the 64-px door is acceptable (53 vs 64) and its base row is 511
   against deck 512, so it is not floating — the contact shadow is the defect (B1).
8. **Sheet packing.** `00` uses 8×4 cells for 25 tiles, leaving 7 empty cells (~22 %); `02` uses 6×5 cells with one tile in a 220-px last row
   (5 empty cells); labels are small. Cosmetic, but the atlases are not efficient review documents.
9. **`01` hazard placement is inconsistent with `05`.** In `01` the hazard patch is at row 7 (the deck's front face, one tile below the lip); in `05`
   it is at row 15 (the wall base, one tile above the floor). Both are plausible uses, but the pack never demonstrates the hazard as a floor marking.
10. **Cutouts have zero bleed.** Every sprite's opaque bbox starts at the canvas border (a full 1-px `8,8,12` border is at 0 and w/h−1); any 1-px
    placement error clips the outline. No partial alpha, fringe or halo was found (all alpha 0/255) — this is a packaging caution, not a visible defect.
11. **Hull mid-section repetition.** The 103-px mid is repeated exactly three times (joins at y=50/153/256/359); the pipe clamps, cyan ticks and
    orange dots repeat at the same 103-px rhythm, and the 118-px top flange sits 5 px inside the 128-px module, so the rib never spans its slot.
12. **Viewport glass is very dark.** The 112×88 frame has a clean chamfer, a top-left bevel and a recessed sill, but the glass is a near-black field
    with sparse 1-px stars and one purple asteroid; at 1× it reads as a black panel more than a window.
13. **`05`/`06` are a flat backdrop, not a room with depth.** One 14-tile wall, one floor line, all props on the same plane; the ribs provide the only
    vertical rhythm. Coherent as a side-view hangar, but there is no foreground/parallax/depth cue.

---

## Per-item checklist

### 25 tiles (+ the orphan)

| # | tile | Verdict | Note |
|---|---|---|---|
| 1 | `ceiling` | PASS | Seamless 2×2; bright lip at the top and bottom reads as a beam; only used two rows. |
| 2 | `deck_fill` | PASS* | Seamless, but M6: 5 colours, 0.90 adjacent diff, 29.8 mean. |
| 3 | `deck_left` | PASS* | Near-duplicate, not mirrored (minor 2); unused in the scene. |
| 4 | `deck_right` | PASS* | Same as `deck_left`; the “right” cap is not a mirror. |
| 5 | `deck_step` | PASS* | Face bay tiles; reads as a panel/vent row, not a step (minor 3). |
| 6 | `deck_step_left` | PASS* | Noise variant of `deck_step`, not a mirrored end (minor 2). |
| 7 | `deck_step_right` | PASS* | Noise variant; the dais's ends are not a true L/R pair. |
| 8 | `deck_top` | PASS | Lip/face tile; horizontal repeat clean; the B1 rim is the casualty, not the tile. |
| 9 | `deck_top_right` | PASS* | Corner variant; near-duplicate of `deck_top`; not mirrored against the orphan left. |
| 10 | `door` | PASS* | Clean 32×64 double leaf, left-lit jamb; scene legibility/placement fails (M7). |
| 11 | `door_top` | PASS* | Cyan indicator and lintel; scene legibility (M7). |
| 12 | `grate_fill` | PASS | Seamless; bars continue across the 2×2. |
| 13 | `grate_top` | PASS | Seamless; used at the floor's top row, 2 tiles wide. |
| 14 | `hazard` | **FAIL** | Edge-mirrored; 2×2 and 5×1 runs form chevrons (M2). |
| 15 | `light_strip` | PASS | Housing/emitter reads; used as ceiling fixtures. |
| 16 | `pipe_h` | PASS | Seamless; flanges added by `_flange` in the scene. |
| 17 | `pipe_v` | PASS | Seamless; meets the horizontal run at row 14. |
| 18 | `vent` | PASS | Slotted wall vent; isolated use; frame reads. |
| 19 | `wall` | PASS | Framed panel; 2×2 clean. |
| 20 | `wall_flat` | PASS | Background filler; 2×2 clean; speck bolts. |
| 21 | `wall_flat_light` | PASS | 1-px cyan accent at x=8; stacks into a continuous strip. |
| 22 | `wall_flat_violet` | PASS | 1-px violet accent; much dimmer than cyan (accent strength uneven). |
| 23 | `wall_light` | PASS | Panel + left accent; used for cluster sides. |
| 24 | `wall_violet` | PASS | Panel + left accent; same. |
| 25 | `window` | **FAIL** | Purple 9×1 bar + 3×3 block in pane; near-black glass; no recess/sill (M5). |
| — | `deck_top_left` | **NOT IN ATLAS** | File exists, not in `tileset.json`/`02`; minor 1. |

### 3 medium structures

| item | Verdict | Note |
|---|---|---|
| `console_bank` (102×59) | PASS* | Dense, clean silhouette, three screens; right rail is the lit side (M8), centre screen blown, scene shadow is the B1 comb. |
| `cargo_stack` (59×87) | PASS* | Clean top-left crate stack, straps/labels read; the right instance overlaps the hazard (M1); scene shadow is the B1 comb. |
| `server_rack` (55×105) | **FAIL** | Flat/slot-line rack, no depth/feet, top-only light, 35×4 base hole; density mismatch with the console (M4). |

### 3 mega elements

| item | Verdict | Note |
|---|---|---|
| `hull_frame` (118×203 source) | **FAIL** | The 448-px module's 39-px flat plinth slices the foot (M3); symmetric sides (M8); mid repeated 3× (minor 11). |
| `viewport` (112×88) | PASS* | Clean chamfer, top-left bevel, recessed sill; glass too dark / planet blob (minor 12). |
| `reactor_core` (118×140) | **FAIL** | No shadow and 32 px of plinth hidden by the hazard (B2); mirror-symmetric lighting (M8); the sprite itself is dense. |

### Whole ship / showcase

| item | Verdict | Note |
|---|---|---|
| `05_whole_ship_x2.png` / `ship_mega_1x.png` | **FAIL** | B1/B2; M1 right bay; M3 hull plinths; M6 floor; M7 door; M8 light. 3 medium types / 3 mega types present; scene uses 4 medium instances (cargo ×2) and 7 mega instances (hull ×5, viewport, reactor). |
| `06_showcase_x2.png` / `scene_1x.png` | **FAIL** | Agent exactly once, on the deck, 53 px vs 64 px door, base row 511 vs deck 512 — but the contact shadow is the B1 comb and the black boots merge into it; the foot sits on the grate and the shadow (254–265) straddles the deck/grate seam (minor 7). |

### Review packet `00`–`06`

| file | Verdict | Note |
|---|---|---|
| `00_tileset_x8.png` | PASS* | 25 tiles at 8×; 7 empty cells / ~22 % (minor 8). |
| `01_tileset_sample_x4.png` | PASS* | Valid tile slice; hazard at row 7 (minor 9); no ceiling/door demonstration. |
| `02_all_tiles_x5.png` | PASS* | 25 registered at uniform 5×; missing `deck_top_left`, last row mostly empty (minor 1/8). |
| `03_medium_catalog_x3.png` | **FAIL (packet)** | Per-sprite fit: console ≈4.9×, cargo ≈5.75×, server ≈4.76× (M9). |
| `04_mega_catalog_x3.png` | **FAIL (packet)** | Hull ≈2.46× vs viewport/reactor 3×; hull appears narrower than viewport (M9). |
| `05_whole_ship_x2.png` | **FAIL** | Same as whole ship (B1/B2/M1/M3/M6/M7/M8). |
| `06_showcase_x2.png` | **FAIL** | Same as showcase (B1); agent once/scale/ground position pass. |

---

## Bottom line

The materials pass the basic pixel checks — the palette is locked (0 violations), all sprite alpha is hard 0/255 with no magenta fringe, halo or
partial-alpha edge, the wall/deck/grate/pipe/ceiling repeats are stable, and the console, cargo and viewport sprites are dense. The pack fails at
integration, not at the basic pixel level:

1. the contact-shadow implementation is visibly broken under every grounded object and erases the agent's feet (B1);
2. the reactor has no shadow and its plinth is cut off by the hazard band (B2);
3. the hazard tile is edge-mirrored and reads as chevrons (M2);
4. the right bay's cargo/hazard/reactor overlap (M1);
5. the hull plinths, the flat server, the dark window, the empty floor, the weak door and the inconsistent light direction are visible at normal
   viewing size (M3–M8).

**Verdict: FAIL. PASS not issued.**
