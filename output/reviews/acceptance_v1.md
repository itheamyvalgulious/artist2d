# Acceptance review v1 — artist2d preview batch (agent + ship)

Inspector: `acceptance-v1` (independent, did not generate these assets).
Method: direct multimodal inspection of the shipped PNGs. The review packets' MANIFESTs and the earlier `output/reviews/*_review_v*.md` verdicts were **not** treated as authority. No asset was modified, no project test was run, nothing was regenerated.
Scope: the preview batch as shipped (`output/character/agent`, `output/environment/ship`, `output/mega/ship`, `output/showcase/ship`).

---

## 1. Coverage table

Legend for the packet tables: **PASS** = the file was opened, every cell/frame was inspected, and what it certifies is acceptable. **FAIL** = inspected, but the asset(s) it documents do not meet the requirement quoted in §2. Counts below are the actual files in `work/review/`.

### 1.1 Character packet — 24 / 24 files

| # | File | Inspected | Verdict | Evidence / why |
|---|---|---|---|---|
| 1 | `00_design_sheet.png` | full + 3x/4x crops | PASS | One full-body side/¾ pose **plus** separate katana, scabbard and pistol part drawings; silver hair, violet iris, short-sleeve top, detached forearm sleeves, shorts, black boots all readable. Minor: the in-hand katana has no visible tsuba and a needle-thin grip; the hip piece reads as a large black box. |
| 2 | `01_char_ref_64_x16.png` | full | FAIL | At 64 px the drawn katana is a 1 px dotted diagonal line with no guard; the two rear scabbards read as a tail/prongs; the two legs merge into one column. |
| 3 | `02_part_katana.png` | full | PASS | Complete, palette-limited part drawing (blade, edge highlight, tsuba, wrapped grip). Minor: dead-straight blade, plain bar tsuba, a notch in the kissaki. |
| 4 | `02_part_scabbard.png` | full | PASS | Complete scabbard with metal throat/foot. Minor: no sageo/kurikata, reads as a black stick. |
| 5 | `02_part_pistol.png` | full | PASS | Best part drawing: readable cyberpunk pistol with slide, trigger guard, cyan accents. |
| 6 | `10_idle_hi_all.png` | all 8 frames + 3x/4x crops | FAIL | Two scabbards at the hip; katana drawn in hand during idle while the scabbard is also worn; no neck (jaw sits on the collar); ear patch painted on hair; legs merge; heavy skin dither. |
| 7 | `11_idle_64px_all.png` | all 8 frames | FAIL | Weapons unreadable; twin scabbards read as prongs; the figure reads one-legged; violet speckles on hair. |
| 8 | `12_idle_3d_truth_all.png` | all 8 frames | PASS | Usable standing-pose truth (magenta is the truth sheet's key background, not a shipped asset). The pixel idle broadly matches the truth's stance. |
| 9 | `10_run_hi_all.png` | all 8 frames | FAIL | **Eye is a blank white rectangle in all 8 frames**; twin scabbards; constant head-top y=84 and foot y=503 in every frame (no bob, no flight phase). |
| 10 | `11_run_64px_all.png` | all 8 frames | FAIL | The sheathed hilt reads as a black antenna/wing; the white eye is a 2×2 white block; the rear bars read as a tail. |
| 11 | `12_run_3d_truth_all.png` | all 8 frames | PASS | Truth is legible; it exposes the pixel run's missing forward lean and missing body rise/fall, but the leg phasing is broadly followed. |
| 12 | `10_slash2_hi_all.png` | all 8 frames + zooms f1,f2,f3,f5,f6 | FAIL | **f1: hand holds a hilt with no blade at all** (the 3D truth f1 has a raised vertical blade). **f6: two blades at once** (thin blade upper-left + broad cyan-edged blade lower-right), plus a second katana hilt at the waist. Blade width/scale flips 5 px → 10 px between f2/f3 and f5/f6. |
| 13 | `11_slash2_64px_all.png` | all 8 frames | FAIL | No blade in f1; two blades in f6; the f5/f6 blade is a thick bright bar; the katana is not identifiable as one weapon across the action. |
| 14 | `12_slash2_3d_truth_all.png` | all 8 frames | PASS | Truth shows a blade in every frame, which proves the f1 omission is a defect and not an artistic choice. |
| 15 | `10_shoot2_hi_all.png` | all 8 frames + zooms f1,f4,f5 | FAIL | Pistol alternates between a proper handgun (f2,f5,f6) and a black box with cyan slats (f1,f4); f3 has a doubled slide/barrel. A second katana hilt at the waist appears in f4/f5 in addition to the back-mounted katana. Body drops 43 px (f5) and 66 px (f6) mid-action while the run anchors sit at y=84. |
| 16 | `11_shoot2_64px_all.png` | all 8 frames | FAIL | Same weapon flip; the f5/f6 crouch is a visible dip; the extended arm is ~1.4× too long; eye blank. |
| 17 | `12_shoot2_3d_truth_all.png` | all 8 frames | PASS | Truth is a compact standing aim with a small pistol; exposes the f5/f6 crouch and the box-gun frames as deviations. |
| 18 | `10_roll_hi_all.png` | all 8 frames | FAIL | f2–f5 are anatomically unreadable tangles; one scabbard is visibly 1.5–2× its idle length and cuts through the torso/legs; the in-hand katana of idle f0 disappears in f1–f6 and reappears at f7. |
| 19 | `11_roll_64px_all.png` | all 8 frames | FAIL | f2–f5 cannot be read as a person rolling at game resolution. |
| 20 | `12_roll_3d_truth_all.png` | all 8 frames | PASS | The gross stand→tuck→inverted→tuck→stand order matches the truth; the oversized weapon in the pixel version does not. |
| 21 | `20_cross_action.png` | full | FAIL | The five actions show the same outfit/hair silhouette but **not the same face/eye** (violet iris in idle, blank white eye in run/slash/shoot) and three different katana states. |
| 22 | `21_transition_pairs.png` | all 6 pairs | PASS | Direct byte comparison of the six source pairs: run:0/slash2:0, run:7/slash2:7, run:0/shoot2:0, run:7/shoot2:7, idle:0/roll:0, idle:7/roll:7 are all identical (both 512 and 64 px). Anchor requirement met. |
| 23 | `22_run_loop.png` | f6,f7,f0,f1 | PASS | The wrap f7→f0 is continuous; the cycle is a genuine loop. Defect noted elsewhere: no vertical travel. |
| 24 | `23_transition_diff.png` | all 6 cells | PASS | All six cells are fully black (zero difference), consistent with the direct byte check. |

### 1.2 Ship packet — 7 / 7 files

| # | File | Inspected | Verdict | Evidence |
|---|---|---|---|---|
| 1 | `00_tileset_x8.png` | full | PASS | All 25 tiles present, 32×32, one palette, no anti-aliasing; the `window` tile is a defect listed in §2/§4. |
| 2 | `01_tileset_sample_x4.png` | full | FAIL | Tiling is seamless, but the slice reads as paste: two `window` tiles show as random static squares, the wall repeats identically, the special tiles are scattered, and the floor is a 25 %-of-frame empty band. |
| 3 | `02_all_tiles_x5.png` | all 25 tiles | PASS | 22 originals + 3 step variants present and readable; 7 wall variants are near-duplicates (redundancy, not missing coverage). |
| 4 | `03_medium_catalog_x3.png` | 3 / 3 | PASS | console_bank, cargo_stack, server_rack all present and readable. Defects: server_rack is a flat slab and its sprite has no alpha channel; console screen content is pseudo-glyph noise. |
| 5 | `04_mega_catalog_x3.png` | 3 / 3 | PASS | hull_frame, viewport, reactor_core present, readable, one palette. Defects: reactor base is clipped at the sprite's bottom edge; viewport's planet is a flat blob. |
| 6 | `05_whole_ship_x2.png` | full + native 1× halves | FAIL | Coherent corridor, but 5 identical ribs/4 identical bays, two static-noise squares pasted on the wall, flat value hierarchy, empty floor. |
| 7 | `06_showcase_x2.png` | full + native 3×/4× crops + preview diff | FAIL | Two clones of the same character in different frames; hard black rectangular "shadows" (80×6 at 2×) cutting the floor's light trim; the characters sit 2–6 px (2×) above the floor surface; no lighting integration, no contact shading. |

### 1.3 Native cross-checks

| Target | Files | Inspected | Verdict |
|---|---|---|---|
| `output/character/agent/{idle,run,slash2,shoot2,roll}/frames_hi/` | 40 PNG @512 | all 8 per action via sheets + native zooms of ambiguous frames (idle f0; run f0; slash2 f1/f2/f3/f5/f6; shoot2 f1/f4/f5) | PASS (coverage) / FAIL (quality per §2–3) |
| `output/character/agent/{...}/frames/` | 40 PNG @64 | all 8 per action; native x16 inspection of idle f0 and run f0 | PASS (coverage) / FAIL (64 px weapon + roll readability) |
| `output/environment/ship/tiles/` | 29 base + 4 checkerboards | atlas + `deck/wall/grate/conduit_checkerboard.png` | PASS (seamless 3×3, no seam leak) |
| `output/environment/ship/props/{console_bank,cargo_stack,server_rack}/sprite.png` | 3 | 102×59, 59×87, 55×105 | PASS (console/cargo) / FAIL (server alpha=255 everywhere, i.e. an opaque rectangle) |
| `output/mega/ship/elements/{hull_frame,viewport,reactor_core}/sprite.png` | 3 | 118×203, 112×88, 118×137 | PASS (readable) / FAIL (reactor base clipped at y=136) |
| `output/mega/ship/ship_mega_1x.png` | 1536×640 | full, both halves at 1.5× | FAIL (same defects as §4: static squares, repetition) |
| `output/showcase/ship/scene.png` | 3072×1280 | full + native 3–4× crops; diffed against `ship_mega_preview.png` | FAIL (grounding/shadow/lighting) |

Numeric technical checks (my own): 512 px frames use 56 opaque colours, 64 px frames 44; **alpha is strictly {0,255}** (no anti-aliasing/blur); **0 near-magenta pixels** in all 40 shipped frames; every frame is a single connected silhouette (so “detached head” is *not* a literal disconnected component — it is an anatomical silhouette problem).

---

## 2. Requirement checklist

### A. Character `agent`

| Requirement | Verdict | Evidence |
|---|---|---|
| Beautiful female special agent, long silver hair | PASS (design) / PARTIAL (execution) | Hair clearly silver/long in every action. The face has no neck, the jaw sits on the collar (`idle/frames_hi/frame_00.png`, `shoot2/frames_hi/frame_01.png`), the ear is painted as a flesh patch on top of the hair, and the mouth is a dot on the chin. “Beautiful” is not met at 512. |
| Violet eyes | **FAIL** | Violet iris only in idle (`idle/frames_hi/frame_00.png`, iris `#6F4A9C` + white sparkle). Run is a **blank white rectangle** (`run/frames_hi/frame_00..07.png`); slash2 f3 and shoot2 f5 are a **pure white hexagon** with no iris; slash2 f2/f4 read as a black visor. Four of five actions are off-model. |
| Short-sleeve top + detached forearm sleeves + short shorts | PASS | Present and repeated consistently in all actions. |
| Coherent colours | PASS | One palette across 40 frames (56 colours at 512); navy/black, cyan seams, violet accents, peach skin. |
| Black combat boots | PASS | Both boots black with treads; visible in every action. |
| Katana + pistol exist, complete part drawings | PASS | `02_part_katana.png`, `02_part_pistol.png`, plus `02_part_scabbard.png`; the design sheet is not one pose. |
| Katana sheathed diagonally on back when not in use | **FAIL** | Run/shoot have the hilt over the left shoulder (correct), but **idle has the katana drawn in hand while the scabbard is still worn on the back** (`idle/frames_hi/frame_00.png`), and slash/shoot add a *second* hilt at the waist (`slash2/frames_hi/frame_01/03/04/05/06.png`, `shoot2/frames_hi/frame_04/05.png`). The state contradicts both the spec and itself. |
| Pistol holstered at waist/hip | PARTIAL | A holster mass exists at the front hip, but it is a large featureless black box with cyan slats and does not match `02_part_pistol.png`. |
| Katana drawn in hand for slash/block | **FAIL** | Drawn, but slash2 f1 has **no blade** (hilt only) and slash2 f6 has **two blades at once**; the blade's width doubles between f2 and f5. |
| Pistol drawn for shoot | PARTIAL | Drawn, but the weapon swaps between a real handgun and a black box with cyan slats frame-to-frame. |
| Idle / run / slash2 / shoot2 / roll delivered | PASS | All five actions × 8 frames exist at 512 and 64. |
| Run is a self-looping cycle | PASS | Direct byte check: `run/frames_hi/frame_07` → `frame_00` wraps; `22_run_loop.png` confirms. |
| shoot2 anchored run→shoot2→run | PASS (anchors) / FAIL (motion) | f0/f7 are byte-identical to run f0/f7; but f5/f6 drop the whole body 43/66 px and crouch, so the run cycle is broken inside the clip. |
| slash2 anchored run→slash2→run | PASS (anchors) | f0/f7 byte-identical to run f0/f7. |
| roll anchored idle→roll→idle | PASS (anchors) | f0/f7 byte-identical to idle f0/f7; the in-hand katana still vanishes in f1–f6. |
| 2D side-view pixel art | PASS | Strict side view, hard pixels, no AA (alpha {0,255}). |
| Design sheet not one pose; separate complete weapons | PASS | `00_design_sheet.png` has the body + katana + scabbard + pistol at full size. |
| Coherent identity every frame/action | **FAIL** | Eye/face changes (violet → white → black), weapon state changes, blade construction changes. Not one character across the five actions. |
| Correct weapon presence/absence | **FAIL** | Missing blade (slash2 f1), duplicate blades (slash2 f6), extra waist katana (slash/shoot). |
| No duplicate weapons | **FAIL** | **Two scabbards** are drawn behind the hip in every idle/run/slash/shoot frame (two identical black bars with the same rounded metal end caps). Idle = 2 scabbards + 1 drawn katana; shoot f4/f5 = 2 scabbards + 1 back katana + 1 waist katana + 1 pistol. |
| Complete limbs/weapons | **FAIL** | Roll2–f5 has merged/unreadable limbs; slash2 f1 is blade-less. |
| Clean pixel art, no magenta | PASS | 0 near-magenta pixels; palette-limited. Cosmetic stain: isolated lavender pixels on hair/outline (`#DBBCFF`, 199 px across 40 frames) read as fringing. |
| No anti-aliasing / blur | PASS | No partial alpha; 56/44 colours. |
| Proper grounding (character) | PASS (sheets) | All standing frames bottom at y=503/512 and y=62/64; heads at y=84. Consistent baseline. |
| Readable at 64×64 | **FAIL** | Body silhouette is readable; weapons are not (katana = 1 px dotted line, hilt = antenna, twin scabbards = prongs), the eye is a 2×2 white block, and roll f2–f5 is illegible. |
| Readable at 512×512 | PARTIAL | Clean at the pixel level, but the anatomy (no neck, merged legs, oversized arm, skin dither) is clearly visible and not commercial-grade. |

### B. Ship environment `ship`

| Requirement | Verdict | Evidence |
|---|---|---|
| Complete side-view spaceship interior, sci-fi + cyberpunk | PASS | Corridor/hangar with ribs, panels, pipes, screens, viewport, reactor; side view throughout. |
| Tiles + medium structures + mega elements, unified style | PASS | 25 tiles (`02_all_tiles_x5.png`), 3 medium (`03_medium_catalog_x3.png`), 3 mega (`04_mega_catalog_x3.png`); one palette and one outline language. |
| Whole interior can read as one mega structure | PARTIAL | It reads as one long corridor, but the 5 hull ribs and 4 bays are exact clones; the whole ship is a horizontally repeated module. |
| Final scene natural and beautiful, not pasted assets | **FAIL** | Two random-static squares pasted on the wall; console perched on a grille "dais" 57 px (2×) above the floor; characters floating with black rectangle shadows; flat values, no light pooling. |
| Diversity 3 mega + 3 medium (preview scope) | PASS | Exactly 3 + 3 delivered; full 20/10 correctly out of scope. |
| Side-view pixel art, coherent palette, crisp pixels | PASS | 32×32 tiles, hard edges, no AA. |
| No anti-aliasing/blur/gradients | PASS | Tile/prop/mega alpha checks: {0,255} only; no gradients sampled. |
| No magenta | PASS | None in the shipped ship files. |
| No text/watermarks | PASS | Console screens are abstract pseudo-glyphs, not legible text; no watermarks. |
| No floating/missing fragments | **FAIL** | server_rack sprite is an opaque rectangle (alpha=255 everywhere) and its base sits above the floor; console base is a notch that shows the wall through it; reactor_core's X-brace base is cut off at the sprite's last row (y=136); the two `window` tiles read as texture corruption. |
| Correct grounding | **FAIL** | Showcase: characters 1–3 px (1×) above the walk surface, with hard black 40×3 px rectangle “shadows” cutting the floor light trim; server rack 1–2 px high; console on a 28 px (1×) grille. |
| Readable tiles and structures | PASS | At 1× the ribs, deck, console, cargo, rack, viewport and reactor are identifiable. Exception: the 32 px `window` tile (static). |
| Seamless tiling | PASS | `deck/wall/grate/conduit_checkerboard.png` 3×3 show no seam leaks. |

### C. Isolation — see §5 (PASS).

### D. No code unit tests
No unit-test suite is expected; acceptance here is visual. This review did not use or require one, and did not run project tests.

---

## 3. Character animation review (all 8 frames per action)

Global numbers used below: standing frames are 420 px tall at 512; head top y=84 and content bottom y=503 in every standing frame; 64 px content bottom y=62/64.

### 3.1 Idle — `10_idle_hi_all.png`, `11_idle_64px_all.png`, `12_idle_3d_truth_all.png`

| Frame | Observed | Defect severity |
|---|---|---|
| 0 | Standing, katana drawn at the hip pointing up-right, scabbard(s) behind, violet eye | **BLOCKER** duplicate scabbard (two bars, identical metal caps); **MAJOR** katana drawn in idle |
| 1 | Same pose, 1 px sway | same |
| 2 | Same pose, 1 px sway | same |
| 3 | Same pose | same |
| 4 | Same pose | same |
| 5 | Same pose, minor hair shift | same |
| 6 | Same pose | same |
| 7 | Byte-identical to f0 | same |

Additional: no neck — the jaw terminates on the black collar; the ear is a flesh rectangle floating on the hair; the near/far legs merge into one peach column with the far leg a thin dark-orange strip; thigh skin is covered in single-pixel orange dither that reads as dirt. Truth match: acceptable stance; the 3D truth has no weapon, so the drawn katana is entirely invented.

### 3.2 Run — `10_run_hi_all.png` / `11_run_64px_all.png` / `12_run_3d_truth_all.png`

| Frame | Observed | Defect severity |
|---|---|---|
| 0 | Stride, hilt above the left shoulder, scabbards at hip, white eye | **MAJOR** blank eye; **BLOCKER** twin scabbards; **MAJOR** no bob |
| 1 | Pass, one leg forward/bent, rear leg extended | same; 64 px: legs merge |
| 2 | Legs together/crossed, heel up | same; 64 px: single leg mass |
| 3 | Wide stride | same |
| 4 | Widest stride | same; **MAJOR** the far leg is only a dark sliver |
| 5 | Pass | same |
| 6 | Crossed legs | same; 64 px: unreadable limb count |
| 7 | Stride (anchor) | same |

Cycle: exact head-top y=84 and foot y=503 in all eight frames → **no vertical bob and no airborne phase**; the run reads as a scissoring glide. The 3D truth has a pronounced forward lean/head-down that the pixel run drops. The sheathed hilt at 64 px is an isolated black wing with a light tip — not a katana. All eight frames carry the blank white eye.

### 3.3 Slash2 — `10_slash2_hi_all.png` / `11_slash2_64px_all.png` / `12_slash2_3d_truth_all.png`

| Frame | Observed | Defect severity |
|---|---|---|
| 0 | = run 0 (anchor, byte-identical) | inherited |
| 1 | Arm overhead, hand grips a hilt, **no blade rendered**; face covered by hair; a second hilt at the waist | **BLOCKER** incomplete weapon (truth f1 has a vertical blade) |
| 2 | Katana up in hand (thin 5 px blade, tsuba visible); blank white eye; second hilt at waist present/absent flicker | **MAJOR** weapon construction differs; **MAJOR** duplicate waist hilt |
| 3 | Blade horizontal, doubled/ghosted light edge, extends ~200 px right; waist hilt present; white eye | **MAJOR** doubled blade edge; **MAJOR** duplicate hilt |
| 4 | Blade low across the body; waist hilt present | **MAJOR** duplicate hilt |
| 5 | Broad ~10 px blade angled down-right, no tsuba, **no eye at all** | **MAJOR** scale/width change; **MAJOR** missing eye |
| 6 | **Two blades simultaneously** (thin blade upper-left + broad cyan-edged blade lower-right), plus waist hilt and twin scabbards; blade passes through the thigh | **BLOCKER** duplicate blades |
| 7 | = run 7 (anchor, byte-identical) | inherited |

Truth match: 3D f1 shows the blade raised (so f1 is wrong); f3/f5 roughly match direction but not blade width. Overall slash2 does not read as one sword over eight frames.

### 3.4 Shoot2 — `10_shoot2_hi_all.png` / `11_shoot2_64px_all.png` / `12_shoot2_3d_truth_all.png`

| Frame | Observed | Defect severity |
|---|---|---|
| 0 | = run 0 (anchor) | inherited |
| 1 | Arm extended; "pistol" is a black box with cyan slats and a brass pip; no eye; back katana + twin scabbards | **MAJOR** wrong pistol; **MAJOR** blank eye |
| 2 | Proper handgun silhouette; white eye; waist-adjacent hilt absent | **MAJOR** blank eye |
| 3 | Handgun with doubled slide/barrel and a long thin extension | **MAJOR** doubled weapon |
| 4 | Back katana hilt over shoulder **and** a second katana hilt at the waist; box pistol; white eye | **BLOCKER** two katanas |
| 5 | Crouched; proper handgun; white eye; back + waist hilts; body top y=127 (43 px drop) | **MAJOR** crouch breaks run continuity |
| 6 | Deep crouch; handgun; body top y=150 (66 px drop) | **MAJOR** 66 px dip |
| 7 | = run 7 (anchor) | inherited |

Weapon identity, body height and face all change inside one clip; the arm is ~1.4× body-proportion long and the forearm has no taper.

### 3.5 Roll — `10_roll_hi_all.png` / `11_roll_64px_all.png` / `12_roll_3d_truth_all.png`

| Frame | Observed | Defect severity |
|---|---|---|
| 0 | = idle 0 (anchor) | inherited |
| 1 | Deep crouch; the in-hand katana is gone; one scabbard is ~1.5–2× its idle length and spans the back | **MAJOR** weapon pop; **MAJOR** scale explosion |
| 2 | Tuck; limbs merge; the scabbard cuts the body; hair a separate mass | **BLOCKER** unreadable |
| 3 | Inverted; boots top-left, head bottom-right; scabbard crosses the torso | **BLOCKER** unreadable |
| 4 | Inverted horizontal ball; head/hair detached-looking at left; scabbard crosses the body | **BLOCKER** unreadable |
| 5 | Kneeling crouch facing left; head down; impossible limb read | **BLOCKER** unreadable at 64 |
| 6 | Rising crouch; hair covers the head | **MAJOR** |
| 7 | = idle 7 (anchor) | inherited |

The 3D truth also tumbles as a ball, but its weapon is a compact plank; the pixel version's scabbard is oversized and slices through the silhouette, which is what destroys legibility. At 64 px, f2–f5 cannot be parsed as a human.

### 3.6 Cross-action consistency

Same hairstyle/silhouette, same outfit, same palette, same 420 px height and same baseline — but:
- the **eye** is violet in idle, blank white in run/slash/shoot f3/f5, black visor in slash2 f2/f4;
- the **katana state** is drawn in idle, back-sheathed in run, drawn + waist-sheathed in slash/shoot, absent in roll;
- the **blade** is 5 px in slash2 f2, ~10 px and cyan-edged in f5/f6, and missing in f1;
- the **pistol** is a handgun in some shoot frames and a black box in others.

They do not convincingly read as one character animated five ways; they read as one sprite with inconsistent weapon/eye overlays.

### 3.7 Transition verification (independent)

Six pair byte comparisons of the shipped frames: all identical at both 512 and 64 (run0↔slash2-0, run7↔slash2-7, run0↔shoot2-0, run7↔shoot2-7, idle0↔roll-0, idle7↔roll-7). `23_transition_diff.png` is fully black. **PASS.** This certifies continuity of the endpoint *pixels*, not the continuity of weapon state inside the clips.

---

## 4. Ship environment review

### 4.1 Tiles (25)
All 25 present: ceiling, deck family (fill/left/right/top/top-left/top-right/step/step-left/step-right), grate fill/top, hazard, light_strip, pipe_h, pipe_v, vent, 7 wall variants, window. Palette is uniform (dark blue-grey + cyan + violet + ochre hazard). Pixels are crisp, no AA, seamless (3×3 checkerboards clean).

Problems:
- **BLOCKER (composition)** `window.png` is 32 px of random cyan/white specks with one purple blob; at 1× it is indistinguishable from texture corruption/static, and the whole-ship scene pastes it twice as a wall decal (`ship_mega_1x.png` x≈380 and x≈1287, 2× scene x≈760/2574). This is the most visible defect in the environment.
- **MAJOR** every tile is covered in uniform single-pixel light speckle; because the same tile repeats, the speckle repeats on a 32 px lattice and reads as noise, not detail (visible in `01_tileset_sample_x4.png` across the whole wall).
- **MAJOR** 7 of 25 tiles are near-identical wall variants (wall / wall_flat / wall_flat_light / wall_flat_violet / wall_light / wall_plain / wall_violet); variety is low for 25 tiles.
- MINOR the `hazard` tile is the only warm colour and is very saturated; it dominates when used as a pad.

### 4.2 Medium structures (3)
- `console_bank` (102×59): strongest silhouette; angled screens, purple rails, cyan UI. MINOR its screen “data” is illegible noise and the left contour has a large notch that shows the wall through it.
- `cargo_stack` (59×87): three stacked containers with straps and labels; reads immediately. MINOR: labels are arbitrary cyan/violet rectangles; no perspective.
- `server_rack` (55×105): weakest. Reads as a flat slab; horizontal bars repeat; the top is a plain block. **MAJOR**: its sprite has **no transparency at all** (alpha=255 on every pixel), so it is an opaque 55×105 rectangle pasted over the wall rather than a cut-out prop.

### 4.3 Mega elements (3)
- `hull_frame` (118×203): good truss/pipes/ribs; cut pipe ends are intentional for tiling. MINOR the top/bottom cap is plain and the jagged outer pillar edge is noisy.
- `viewport` (112×88): best mega element; beveled recess, cyan accents, starfield, planet. MINOR planet is a flat ball with a few specks; the frame's lower band is an unfinished dark strip.
- `reactor_core` (118×137): strong focal element (purple coil banks, cyan core capsules). **MAJOR** the base X-brace mesh is clipped by the sprite's bottom edge (bbox reaches y=136 exactly), so the machine has no finished footing; in the scene it is hidden by the hazard pad.

### 4.4 Whole-ship assembly (`05_whole_ship_x2.png`, `ship_mega_1x.png`)
Positives: it does read as a real spaceship corridor/hangar; ribs + deck + viewport + console + reactor form a coherent architecture; the cyan accents give a consistent cyberpunk identity; the hull ribs have genuine 3D form.

Negatives:
- **MAJOR** module repetition: 5 identical hull ribs at equal spacing, 4 identical bays, identical wall-panel pattern; the corridor is one repeated slice.
- **BLOCKER** the two static-noise squares.
- **MAJOR** value hierarchy is flat: everything sits in a narrow dark range; only the console and reactor are bright, so the eye goes to the bottom-right corner and the center of the wall is dead.
- **MAJOR** the console_bank is perched on a grille “dais” (grate tiles) 57 px (2×) above the floor, reading as a console standing on a fence/vent, not on a platform.
- MINOR the floor is ~25 % of the frame height and is an empty striped band; no clutter, lights or markings to sell scale.
- MINOR 1 px cyan/violet “pipe_v” lines run down the wall and end abruptly.

### 4.5 Showcase (`06_showcase_x2.png`, `scene.png`) — the finished commercial scene
- **MAJOR** two copies of the same character appear in one frame (idle at x≈472–551, shoot2 at x≈1924–2023), reading as clones rather than a scene.
- **BLOCKER grounding** each character has a hard-edged solid black rectangle under it instead of a contact shadow: 80×4 + 40×2 px at 2× (left) and 80×6 px (right), colour `#08080C`, y=1024–1029. It cuts the floor's bright trim (`#9B9BB0`) and reads as a hole, not a shadow.
- **BLOCKER grounding** the characters do not touch the floor: content bottoms y=1021 (left) and y=1017 (right) vs. walk surface y=1024 (2×), i.e. 1.5 px and 3.5 px at 1×, with the two characters 1 px apart in baseline as well.
- **MAJOR** no lighting integration: no rim light from the cyan strips, no ambient tint, no local value change; the dark outfit and black boots vanish against the wall. At 1× the character is only findable by her silver hair.
- **MAJOR** the console railing/trim passes in front of the console's lower housing and the console is on the grille dais; the props have no contact shadows either.
- MINOR the hazard pad under the reactor is a flat rectangle with a hard vertical cut; the reactor is half-hidden by the right rib.
- Composition: the two figures are at 15 % and 63 % width and neither interacts with any prop or light source; the middle third is empty wall.

### 4.6 Style unity / naturalness / beauty
Style unity: **PASS** (one palette, one outline language, one noise treatment). Naturalness: **FAIL** (floating props and characters, fake rectangular shadows, static-square wall decals, console on a vent). Beauty: **PARTIAL** (the rib/viewport/reactor language is genuinely good; the composition and lighting are not finished).

---

## 5. Isolation check

Verified on disk:

```
output/character/   agent/  knight/                 (isolated by character name)
output/environment/ field/  ship/                  (isolated by set)
output/mega/        field/  ship/                  (isolated by set)
output/showcase/    field/  ship/                  (isolated by set)
```

- No files directly at `output/environment/`, `output/mega/`, `output/showcase/` (`find -maxdepth 1 -type f` returns nothing). **PASS**
- `output/character/` contains only the two character directories. **PASS**
- The original `field` top-down map is still under `environment/field` and `field` mega/showcase, untouched and not mixed with `ship`. **PASS**
- Packet directories: `work/review/character/` = 24 PNG + MANIFEST; `work/review/ship/` = 7 PNG + MANIFEST. Counts match the MANIFESTs. **PASS**

Isolation verdict: **PASS**.

---

## 6. Overall verdict

**FAIL.** There are multiple BLOCKER and MAJOR defects; the acceptance rule (PASS only with zero BLOCKER and zero MAJOR) is not met.

### BLOCKERs
1. **Duplicate weapon geometry** — two scabbards drawn behind the hip in every idle/run/slash2/shoot2 frame (two identical bars with the same rounded metal caps), plus a second waist-mounted katana in slash/shoot frames. Up to four long weapon constructs are visible in one frame (`slash2/frames_hi/frame_06.png`, `shoot2/frames_hi/frame_04.png`).
2. **slash2 f1 has no blade** — the raised hand holds a bare hilt; the 3D truth f1 has the blade raised, so this is a defect. (`slash2/frames_hi/frame_01.png`)
3. **slash2 f6 has two blades at once**, one thin upper-left and one broad cyan-edged lower-right, plus the waist hilt and twin scabbards. (`slash2/frames_hi/frame_06.png`)
4. **The eye/face is off-model in 4 of 5 actions** — blank white rectangle/hexagon in run, slash2 f3/f5, shoot2 f5; black visor in slash2 f2/f4; the violet iris exists only in idle.
5. **Roll f2–f5 are unreadable** at both 512 and 64: limbs merge, the overscaled scabbard cuts through the body, the in-hand katana vanishes. (`roll/frames_hi/frame_02..05.png`)
6. **Showcase grounding** — hard black rectangular “shadows” cutting the floor trim, and characters floating 1.5–3.5 px (1×) above the walk surface.

### MAJORs
1. Weapon construction changes frame-to-frame: blade 5 px → 10 px → doubled edge → absent; pistol handgun ↔ black box with cyan slats; doubled slide in shoot2 f3.
2. Idle violates the “not in use ⇒ sheathed on the back” rule (katana drawn at the hip with the scabbard still worn).
3. Weapons unreadable at 64×64: katana is a 1 px dotted line, the hilt is an isolated “antenna”, twin scabbards read as a tail; the eye is a white 2×2 block.
4. shoot2 breaks the run cycle: body top y=127/150 in f5/f6 vs 84 in the anchors (43/66 px drop).
5. Run has no vertical bob and no flight phase (head y=84 and foot y=503 in all 8 frames).
6. `window` tile is random static and is pasted twice on the wall as a decal.
7. `server_rack` sprite is an opaque rectangle (no alpha) and sits 1–2 px above the floor.
8. `reactor_core` base is clipped by the sprite edge.
9. Ship scene is extremely repetitive (5 identical ribs, 4 identical bays, 7 near-identical wall tiles) with a flat value hierarchy.
10. No lighting integration — the dark character disappears against the dark wall; no contact/rim/ambient treatment on props or characters.
11. The showcase contains two clones of the same character in one frame.

### MINORs
Katana is dead straight with a plain bar tsuba and a notched kissaki; scabbard is a black stick with no sageo/kurikata; skin has dirty single-pixel dither; the ear is a flesh patch on the hair; no visible neck; the mouth is a chin dot; lavender stray pixels (`#DBBCFF`) on hair/outline; the console has a notch through which the wall shows; hazard pad is a flat rectangle; 1 px pipe lines end abruptly; the floor is 25 % empty band; console screen data is illegible noise.

---

## 7. Final summary

**Genuinely commercial-grade:**
- The *pipeline discipline*: byte-identical transition anchors at both resolutions, strict palette (44/56 colours), alpha strictly {0,255}, no anti-aliasing, no magenta, no text/watermarks, correct folder isolation and set separation, and a real 3+3 preview scope.
- `02_part_pistol.png`: a clean, readable cyberpunk pistol.
- The ship's structural language: the hull rib (truss, pipe bundle, caps), the viewport, and the reactor are coherent, detailed modular elements with a unified palette.
- The whole-ship assembly reads as a believable spaceship corridor at 1×.
- The design sheet does satisfy the “full body + separate complete weapon parts” requirement.

**Must be fixed before any acceptance:**
1. Remove the duplicate scabbard/waist-katana objects; enforce a single weapon-state machine: idle = katana sheathed on the back, pistol holstered; slash = one drawn katana, empty scabbard on the back; shoot = one pistol, katana sheathed.
2. Restore the blade in slash2 f1 and remove the second blade in f6; lock one katana construction (width, tsuba, length) across all slash frames.
3. Rebuild the eye so the violet iris is present in every frame and every action (run, slash, shoot included), and fix the face profile (neck/jaw, ear, mouth).
4. Re-author roll f2–f5 so the body reads as a rolling figure at 64 px; constrain the scabbard's scale to the idle length.
5. Re-time shoot2 so the body height stays on the run cycle (no 43/66 px crouch), and use a single pistol construction.
6. Replace the black rectangle “shadows” with a proper contact shadow and ground both showcase characters on the y=1024 walk surface.
7. Remove or redesign the `window` tile; stop using it as a wall decal.
8. Give `server_rack` a transparent cut-out; finish the reactor base; add contact shadows and light integration for all props.
9. Break the repetition: vary the bays/ribs, add light pools, floor markings and a focal composition; use the viewport/reactor as intentional focal points instead of edge decoration.

The preview demonstrates a working, technically disciplined pipeline and three strong environment elements, but the character (the primary hero asset) is not yet a single coherent, weapon-correct character at commercial quality, and the environment's completed scene is not yet naturally assembled. **Verdict: FAIL.**
