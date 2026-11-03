# Character animation review — round 3 (independent)

Reviewer: `char-review-v3` (did not generate these assets).
Packet: `/dat/projects/artist2d/work/review/character/` (`MANIFEST.md` read first — including the transition SHA-256 list).
Ship source: `/dat/projects/artist2d/output/character/agent/<action>/{frames_hi,frames}/` (512px = `frames_hi`, 64px = `frames`).
Method: all 24 packet PNGs opened at full resolution; every ambiguous sheet was re-opened as the original
`frames_hi/frame_0*.png` / `frames/frame_0*.png` at nearest-neighbour 4×–12× zoom (no resampling, no regeneration,
no asset modification). Numeric figures below are measurements taken *from the shipped PNGs* (SHA-256, bounding boxes,
connected components, palette censuses, cross-frame diffs). No pipeline test was executed.

---

## 1. Coverage — every file inspected (24 / 24)

| # | File | Result | Evidence |
|---|------|--------|----------|
| 1 | `00_design_sheet.png` | **PASS** | Design on spec: female cyberpunk, silver hair, violet eye band, crop top + detached sleeve + shorts, black boots, full-length katana (thick blade, tsuba, cyan edge), dark scabbard with metal mouth/chape, compact pistol, dark-navy/gunmetal/silver/cyan/violet only. |
| 2 | `01_char_ref_64_x16.png` | **FAIL** | The canonical 64px ref draws the katana as a 1px dashed needle with no tsuba/cyan edge (origin of the blade defect), and the face as a violet band, not an eye. It also no longer matches the shipped 64px frames (shipped idle has a big hip plate and a two-rod stow; the ref has a small thigh holster). |
| 3 | `02_part_katana.png` | **PASS** | 58×485, full-length blade, cyan cutting edge, solid wide tsuba, wrapped tsuka, pommel. |
| 4 | `02_part_scabbard.png` | **PASS** | 52×461, thick dark scabbard with silver mouth band and chape — exactly one cap per end. |
| 5 | `02_part_pistol.png` | **PASS** | 117×88, compact pistol with guard, slide, sights, cyan accents. |
| 6 | `10_idle_hi_all.png` | **FAIL** | All 8 frames: **two** silver-capped scabbard rods leaving the same hip in different directions (caps measured at (147,347) and (189,395) in f0) — a duplicate stow. Eye is a solid black almond (no iris) in all 8. |
| 7 | `11_idle_64px_all.png` | **FAIL** | 64px head: face is a 3×4 skin block, **no eye pixel of any colour**; the only violet pixels sit on the hair silhouette ((32,10),(37,11),(38,19),(28,20) …). Legs fuse into one orange mass. |
| 8 | `12_idle_3d_truth_all.png` | **PASS** | 8 near-static standing variants; the art's stance matches. |
| 9 | `10_run_hi_all.png` | **FAIL** | Same-lead-leg cycle (§2 M1) and the same duplicate two-rod stow (run f0 caps at (103,328),(134,381); run f2 at (101,326),(132,377)). Eye black in all 8. |
| 10 | `11_run_64px_all.png` | **FAIL** | No violet eye (1 black eye pixel); hair/head boil; legs fuse. |
| 11 | `12_run_3d_truth_all.png` | **PASS (with note)** | Contact/pass poses match the art, but the truth is itself a 4-pose cycle duplicated (truth f2 vs f6 = 4.7k px, f1 vs f5 = 13.6k px), so the art inherits the repeat. |
| 12 | `10_slash2_hi_all.png` | **FAIL** | Blade length spread 86→257px (3×), f6 carries **two** blades + a spare hilt, the scabbard is absent in f1–f6, and f6 is clipped by the canvas bottom. |
| 13 | `11_slash2_64px_all.png` | **FAIL** | Blade collapses to a 1px staircase with no cyan edge; no violet eye; one stray bright-green pixel at (38,26). |
| 14 | `12_slash2_3d_truth_all.png` | **PASS** | Sword direction/arc per frame agrees with the art (the truth's blade also foreshortens, which is *why* the art's length varies — see §3 MAJOR-2). |
| 15 | `10_shoot2_hi_all.png` | **PASS on B1 / FAIL overall** | B1 fixed: exactly one pistol per frame, in the hand, no thigh pistol, muzzle ≥16px inside the panel. But the stowed katana is split at ≈50° (hilt over the left shoulder, scabbard rod at the hip) in f1–f6. |
| 16 | `11_shoot2_64px_all.png` | **FAIL (partial)** | Only action with a readable violet eye at 64px (2–3px sclera+iris+pupil) ✔; one pistol ✔; but 2 stray bright-green pixels at (40,25),(40,27) and the stow reads as a club. |
| 17 | `12_shoot2_3d_truth_all.png` | **PASS** | Extended-arm aiming pose matches frame-for-frame. |
| 18 | `10_roll_hi_all.png` | **FAIL** | Article follows the truth's tuck orientation ✔ (so round-2's “inverted sprawl” complaint is now legitimate tumbling), but f3 has **two** white-capped rods, f5 runs the scabbard vertically through her face, and f2/f3 limb count is unreadable. |
| 19 | `11_roll_64px_all.png` | **FAIL** | f2–f4 are an unreadable jumble at game scale (no readable head/limb/weapon separation). |
| 20 | `12_roll_3d_truth_all.png` | **PASS** | Compact tuck/somersault truth; art orientation now matches it. |
| 21 | `20_cross_action.png` | **FAIL (inherits)** | Scale/proportions consistent across the five actions, but it exposes the eye inconsistency (shoot2 = violet iris, idle/run/slash2/roll = black hole) and the two different stow constructions. |
| 22 | `21_transition_pairs.png` | **PASS** | All six pairs visually identical. |
| 23 | `22_run_loop.png` | **FAIL** | f6→f7→f0→f1: the same boot stays planted forward and the same boot stays lifted behind in all four — the repeat is visible in the loop sheet itself. |
| 24 | `23_transition_diff.png` | **PASS** | All six panels pure black (0 differing pixels). |

Manifest SHA-256 verified against the shipped files (`frames/` = the 64px frames the manifest hashes):
`run:0 = 0527b9d9d4927cf0…` ✔, `run:7 = e732fb6b1587b581…` ✔, `idle:0 = idle:7 = c119a9ad495a2570…` ✔ (and `idle:7 == idle:0`
byte-identically, which is the idle-loop fix). Transition anchors re-verified in `frames_hi`: `run0 == slash20 == shoot20`,
`run7 == slash27 == shoot27`, `idle0 == roll0 == roll7`, all SHA-identical.

---

## 2. Round-2 blockers / majors — re-verification

| Item | Verdict | Visible evidence (exact file / frame) | Needed fix |
|---|---|---|---|
| **B1** shoot2 duplicate pistol + thigh pistol | **FIXED** | `shoot2/frames_hi/frame_01..06.png`: exactly **one** pistol, held in the extended hand; no pistol silhouette at the hip/thigh (the hip now carries the plate rig with a cyan-outlined empty holster wedge); no duplicate. Muzzle clear of the canvas in every frame — right-most opaque pixel f1..f6 = 481/491/493/**496**/459/480 of 512 (≥16px margin). `23_transition_diff.png` proves f0/f7 still match run. | — (keep the "one pistol" guard in the pipeline) |
| **B2** slash2 f6 detached blade shard on the thigh | **NOT FIXED — mutated into a worse duplicate** | `slash2/frames_hi/frame_06.png`: the thigh shard is gone, but the frame now contains **two complete blades** (steel components 3131px / L=257 bbox (237,373)-(463,496) and 1608px / L=145 bbox (211,392)-(304,503), each with its own outline and its own cyan edge) **plus a spare wrapped hilt** at (124,300)-(190,380) that connects to nothing, while the hand grips a separate short crosswise bar with **no tsuba**. The scabbard is not merely empty — it is **absent** from f1–f6. | Re-composite f6 from one katana sprite; delete the second blade and the spare hilt; put the empty scabbard back on her hip in f1–f6. |
| **B3** drawn katana 2× length / 4× thickness | **NOT FIXED (length spread is now 3×)** | Measured on `slash2/frames_hi`: blade length f1 122px, f2 222px, **f3 86px**, f4 178px, f5 215px, **f6 257px** (+145px duplicate) → 3.0× spread (round 2: 2.0×); as a fraction of the 420px body height: .29/.53/**.20**/.42/.51/**.61**. Thickness is now consistent (10.1–12.4px, ≈1.2×) ✔ so only length is broken. f3 reads as a dagger/wakizashi stub; f1 has **no cyan edge**; f6 has **no tsuba** at the grip. | Draw the blade from one parametric katana: fixed blade length ≈0.45× body height, fixed 10–12px width, mandatory tsuba and 1px cyan edge, rotate only. Then clamp the pose so the tip stays inside the panel. |
| **Roll** inverted sprawl vs compact tuck | **PARTIAL → accept the orientation, reject the silhouette** | The art now **does** follow the truth: f1 crouch, f2 side-tuck (head down-right), f3 fully inverted with feet up-left, f4 on the back, f5 seated tuck, f6 crouch — matching `12_roll_3d_truth_all.png` cell for cell, so the "inverted" reading is the 3D tuck, not an error. **But** the sheathed katana is inflated to a plank larger than her torso (roll f3 bbox is 90 465 opaque px vs 56 706 for run f0) and in f5 it runs **vertically through her face**; f3 carries two separate white-capped rods ((433,151) and (441,231)); f2/f3 limb count is unreadable at 512. | Keep the orientation; shrink the stow to the off-hand sprite scale, keep it behind the body, and keep one rod; re-key limbs so hands+knees stay readable in f2–f4. |
| **M1** run 4-frame cycle, same leading leg | **NOT FIXED** | In **all eight** `run/frames_hi/frame_0*.png` the trailing boot stays lifted/behind at the left of the body and the leading boot stays planted/extended to the right; the feet never cross, so the lead leg never swaps. f4–f7 are the same leg phases as f0–f3 (22_run_loop shows f7/f0/f1 with the identical lead). Root cause visible in the truth: `12_run_3d_truth_all` f2 vs f6 differ by only 4675 px (f1 vs f5 13 574) — the source cycle is 4 poses duplicated. | Re-key the run as a true 2-step cycle: the second half must be the mirror-phase pose set (right leg reaching forward while the left trails), re-solved from the truth with the legs swapped, not resampled. |
| **M2/M9** 64px had no violet eye; 64px must match 512 | **PARTIAL** | *Match:* box-downsample of `frames_hi` matches the shipped 64px silhouette on **97.7–98.7 %** of pixels in all 40 frames (round 2: 90–94 %) → derivation is faithful ✔. *Eye:* **only shoot2** has a readable violet eye at 64px (f3: light-violet + violet + pupil, 2–3px). idle/run/slash2/roll 64px faces have **no eye pixel** — idle f0's face is a 3×4 skin block with nothing in it, and the violet pixels that exist are stray hair-edge dither. | Paint the eye as a preserved tile **after** downsampling (white sclera + violet(113,74,156)/(183,140,224) iris + black pupil) in every frame of every action, then re-run the despeckle so the hair-edge violet strays vanish. |
| **Idle loop** 16k-pixel f7→f0 pop | **FIXED (with a residual cadence hitch)** | `idle/frames_hi/frame_07.png` is byte-identical to `frame_00.png` (SHA `db55f7fc52ac6ceb…`), so the seam diff is **0 px** (was 16k). Side effect: the largest step in the loop is now f6→f7 (**13 828 px** vs a 5.7–10.6k mean for the other steps) and f7 is a 1-frame hold of f0. | Optionally give f7 its own pose ≤1 mean step from f0 instead of duplicating f0. |
| **Stowed katana** hilt/scabbard ~75° kink, not one rigid object | **NOT FIXED (partially improved, now also duplicated)** | *idle/run:* the hilt now sits at the **right** waist pointing up-right (fixing round 2's "hilt floating by the head"), and one scabbard rod continues it roughly collinearly — **but a second, separate silver-capped rod** leaves the hip at ≈+20° (idle f0 caps (147,347) & (189,395); run f0 (103,328) & (134,381); run f2 (101,326) & (132,377)), i.e. a duplicate scabbard. *shoot2 f3/f4/f5:* the hilt is back at the **upper-left, over the shoulder at ≈55°**, while the scabbard lies at ≈+10° at the hip — a ~45° kink and a ~250px gap (`shoot2/frames_hi/frame_04.png`, region (100,60)-(340,380)). *roll f1/f2/f4/f5/f6:* one straight object ✔. *roll f3:* two capped rods ✗. | Bake the sheathed katana once as one rigid sprite (hilt + tsuba + habaki + scabbard, one chape, collinear) and place it with **one** transform per frame from a fixed body anchor; delete the extra rod everywhere. |

---

## 3. New / remaining findings

### BLOCKER

**B-1 — The sheathed katana is still not one rigid object, and it is duplicated.** Three different constructions ship:
(a) idle/run — hilt up-right at the right waist + **two** silver-capped scabbard rods (duplicate weapon);
(b) shoot2 f1–f6 — hilt over the left shoulder at ≈55° + scabbard rod at the hip at ≈+10° (~45° kink, ~250px gap);
(c) roll f3 — two capped rods, f2/f4/f5/f6 correct single rod.
*Evidence:* `idle/frames_hi/frame_00.png` (7× crop of (100,270)-(340,380)), `run/frames_hi/frame_00.png`, `run/frames_hi/frame_02.png`, `shoot2/frames_hi/frame_04.png` (4× crop (100,60)-(340,380)), `roll/frames_hi/frame_03.png` (3× crop (200,80)-(512,512)).
*Fix:* one baked, single-rod sheathed katana; one attachment point; one rotation; assert exactly 2 silver caps (mouth + chape) per frame.

**B-2 — slash2 f6 contains two blades and a third hilt.** See §2 B2. This is a duplicate weapon, the single most visible defect in the set.
*Fix:* re-composite f6; then add a hard pipeline check "exactly one steel-edge connected component >2000px and exactly one hilt per frame".

**B-3 — Violet eyes are missing at 512 as well as 64 (identity requirement).** In `idle/*`, `run/*`, `slash2/*`, `roll/*` the eye is a solid black almond ~12×8px with no iris (verified: no violet-family pixel exists inside any eye bbox; `idle/frames_hi/frame_00.png` face 266–312 × 115–164). Only `shoot2 f1–f6` (and `shoot2` at 64px) draws white sclera + violet iris + pupil. The character therefore changes eye design between actions — visible side-by-side in `20_cross_action.png`.
*Fix:* single eye tile at both resolutions; make "black-only eye" a failing check.

### MAJOR

1. **slash2 blade length spread 3× (86–257px).** `slash2/frames_hi/frame_03.png` is a 86×15px stub (dagger proportions, .20 of body height) versus `frame_06.png` 257px (.61). Same action, three different swords. *Fix:* parametric blade (see §2 B3).
2. **slash2 loses the scabbard entirely while the katana is drawn** (f1–f6 have no scabbard anywhere; hip carries only the plate rig). The requirement is "scabbard empty", not "scabbard gone". *Fix:* keep the empty scabbard parented to the hip in every drawn-katana frame.
3. **slash2 f6 blade is clipped by the canvas.** Alpha reaches the last row (y=511) across x 440–463 (`frames_hi/frame_06.png` bbox (96,105,476,**512**)); the blade's dark outline is cut flat by the frame edge. *Fix:* shorten/rotate f6 by ~15px or offset the body up so the tip keeps ≥8px margin.
4. **run cycle never alternates the lead leg** (M1 above). At 12fps the character visibly rows with one leg for the whole loop; in `22_run_loop.png` f7/f0/f1 are indistinguishable.
5. **roll is unreadable where it matters.** 512px: f2/f3 lose limb count (arms and shins merge into the torso/hair mass); f5 runs the sheathed katana vertically **over her face**, and the stow is drawn 1.6× larger than in run (opaque px 90 465 in roll f3 vs 56 706 in run f0). 64px: f2–f4 are a dark blob with orange patches (`11_roll_64px_all.png`). *Fix:* scale the stow to the off-hand sprite size, keep it behind the silhouette, and re-key f2–f4 so head, both boots and one shoulder stay separable at 64px.
6. **Hip gear churns frame-to-frame.** The plate/holster rig is a different drawing in each action and each frame: idle f0 = horizontal slab + silver buckle; shoot2 f2 = plate + cyan chip + buckle; roll f2 = a black slab wider than her waist; slash2 f4 = a plate with a lattice panel. Also the tsuba on the stowed katana is a **hollow silver ring** in idle/run, whereas `02_part_katana.png` has a solid wide guard. *Fix:* bake the hip rig and the guard as fixed sprites like the pistol.

### MINOR

7. **Off-palette green.** 512px: (34,74,38)/(47,107,47)/(68,148,59)/(23,48,28) — 92 such pixels in `idle/frames_hi/frame_00.png`, used as the shadow edge of cyan trim (reads as dark olive against the teal, and the sheet palette is navy/gunmetal/silver/cyan/violet only). 64px: 3 bright-green strays — `slash2/frames/frame_01.png` (38,26); `shoot2/frames/frame_03.png` (40,25) & (40,27); `roll/frames/frame_04.png` (46,32). *Fix:* quantise the cyan ramp to (16,58,82)/(53,162,196)/(163,234,240) and re-run the 64px despeckle for hue outliers.
8. **Speckle noise on skin.** 10–63 isolated, ≥25-luma-darker single pixels per 512 frame inside skin areas (worst: idle f6 40, run f0 63, slash2 f0 63, shoot2 f0 63) — visible as dirt/speckles at 512. *Fix:* 1px median/ignore-isolated pass limited to skin masks in the 512 frames too (currently only the 64px pass exists).
9. **Idle cadence hitch at the (fixed) seam** — 13 828px step f6→f7 vs a 5.7–10.6k mean, because f7 was replaced by f0.
10. **roll f5 framing:** art reaches x=509 of 512 (2px margin).
11. **64px silhouette loses the costume read.** In `11_idle_64px_all` / `11_run_64px_all` the two legs merge into a single orange mass and the detached sleeve/shoulder strap disappears, so the 64px frames are a coarse silhouette of the 512 art rather than the same character. *Fix:* separate the legs by ≥1 transparent column and preserve the cyan sleeve band as a 1px accent.
12. **`01_char_ref_64_x16.png` is stale**: it still shows a needle katana and a small thigh holster, neither of which matches the shipped 64px frames; it should be regenerated from the final `frames/`.
13. **Both-feet visibility in roll f5/f6**: only one boot is separable in f5 (the other is hidden behind the torso) — acceptable for the tumble, but worth a check against the "both feet distinguishable" rule from round 2.

### Original requirements spot-check

| Requirement | Verdict |
|---|---|
| Female cyberpunk agent | PASS |
| Silver hair | PASS (silver + gunmetal shades, consistent) |
| **Violet eyes** | **FAIL** — violet iris only in shoot2; black eye in idle/run/slash2/roll, both resolutions |
| Short-sleeve top + detached sleeves + shorts | PASS (cyan-banded detached sleeve, crop top, shorts) |
| Black boots | PASS |
| Palette dark navy / gunmetal / silver / cyan / violet | PASS except 92 green-ish shadow pixels (§3 MINOR-7); no magenta anywhere (census: 0 magenta pixels in all 40 frames) |
| Full-length katana + scabbard + compact pistol | PARTIAL — the parts are correct, the *placed* katana is 0.20–0.61 of body height and the stow is duplicated/split |
| Stowed when not in use | FAIL — stow is two rods (idle/run/roll f3) or split at ~45° (shoot2) |
| No duplicate weapons / shield / dagger | **FAIL** — slash2 f6 second blade + spare hilt; duplicate scabbard rod in idle/run/roll f3 |
| Same proportions / scale | PASS — opaque bbox height 420/420/420/422/427 px across actions; head and shoulder width constant |
| No missing / extra limbs | PARTIAL — 512 single connected silhouette in all 40 frames (no floating islands), but roll f2/f3 limb count is unreadable |
| No floating pieces | PARTIAL — no detached alpha islands ✔, but the spare hilt in slash2 f6 and the hollow floating tsuba in idle/run read as floating pieces |
| No magenta | PASS |
| No AA / blur | PASS — alpha is strictly {0,255} in all 40 frames; shared ~54-colour palette; no resampled softness |
| Crisp pixels | PARTIAL — palette-locked ✔, skin speckle noise ✗ |
| 3D truth consistency | idle PASS · run PASS (but truth itself is a duplicated 4-pose cycle) · slash2 PASS (truth blade foreshortens, art over-reacts) · shoot2 PASS · roll PASS on orientation, FAIL on silhouette inflation |

---

## 4. Overall verdict

# **FAIL**

Four independent blocker-class problems remain visibly present in the shipped assets:

1. the sheathed katana is not one rigid object (duplicate rod in idle/run/roll-f3, ~45° split in shoot2 f1–f6);
2. `slash2/frames_hi/frame_06.png` contains two blades and a spare hilt (duplicate weapon) and its blade is clipped by the canvas;
3. the violet eye is missing in 4 of 5 actions at both 512px and 64px — only shoot2 has it;
4. the drawn katana changes length by 3× across slash2, including a dagger-proportioned f3.

Plus two majors that survive round 2: the run cycle still never alternates the lead leg, and the roll loses readability (512px limb merge, 64px blob) with the stow inflated and crossing her face.
Round-2 B1 (shoot2 duplicate/thigh pistol, muzzle clipping) and the idle f7→f0 pop are genuinely fixed and the transition anchors are byte-identical, so the fixes that were made are real — but the packet is not shippable.

---

## 5. Summary

Round 3 fixes two round-2 items outright and improves two others, then breaks new ground in the wrong direction. B1 is clean: every shooting frame carries exactly one pistol, in the hand, with the muzzle ≥16px inside the panel, and the holstered thigh gun is gone. The idle seam is exact (f7 ≡ f0, 0 differing pixels), all six transition anchors are SHA-identical, the 64px silhouette now matches its 512 source on 97.7–98.7 % of pixels, the drawn blade's *thickness* is finally consistent (10–12px), and the roll now genuinely follows the 3D tuck instead of inventing a sprawl. Against that: the stowed katana still ships in three mutually inconsistent constructions — a duplicate silver-capped rod in idle/run/roll-f3, and in shoot2 a shoulder hilt ~45° off from a hip scabbard with a ~250px gap; slash2 f6 now has two full blades plus a third loose hilt where round 2 had one shard, and its blade runs off the bottom of the canvas; the violet iris only exists in shoot2, so the character's eyes change colour between actions at both resolutions (idle's 64px face has no eye pixel at all, and the violet pixels that exist are stray hair-edge dither); the drawn katana still varies from an 86px dagger stub (f3) to 257px (f6), a 3× spread that is worse than round 2; the run still never swaps the lead leg in any of the eight frames (and the truth itself is a duplicated 4-pose cycle); and the roll remains unreadable at 64px in f2–f4 while its sheathed katana is drawn 1.6× larger than in run and passes vertically across her face in f5. On top of that sit hygiene defects: 92 off-palette green shadow pixels on cyan trim at 512, 3 bright-green strays at 64, 10–63 speckle pixels on skin per frame, and a churning hip rig whose plate, buckle and hollow tsuba differ in every action. The set is not shippable; the fixes needed are concrete and local (one baked stow sprite with one transform; one parametric blade with a mandatory tsuba and cyan edge; one eye tile at both resolutions; a true leg-swapped second half of the run; a re-composite of slash2 f6 with a canvas-margin clamp), and none of them requires re-authoring the character.
