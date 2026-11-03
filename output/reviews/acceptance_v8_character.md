# Acceptance review v8 — character pack `agent`

**Verdict: FAIL**

5 blockers, 5 majors, 5 minors. A commercial pass is impossible with any blocker or major.

Reviewer: independent acceptance pass; I did not build these assets. No asset was modified; only this report was written. The review packet's MANIFEST was read first, every PNG in `work/review/character/` was opened, and the shipped per-frame PNGs in `output/character/agent/` were cross-checked for hashes, alpha, bboxes, border contact, connected components, enclosed transparent regions, and consecutive-frame change counts. The 3D truth sheets were used only as pose reference.

---

## 1. Blockers

### B1 — `slash2` body scale is not constant; the 64px frames crop the head/hair/blade

**Files / frames**
- `output/character/agent/slash2/frames_hi/frame_01.png` … `frame_06.png`
- `output/character/agent/slash2/frames/frame_01.png` … `frame_06.png`
- `work/review/character/11_slash2_64px_all.png` (all 8 cells)
- `work/review/character/10_slash2_hi_all.png` (all 8 cells)

**Measured**
- 512 hi-res: `frame_00` and `frame_07` have a 420px body (head top y=148, boots y=567). `frame_01`–`frame_06` have a ~512px body (head top y≈55, boots y=567). Eye-to-boot: 365px at f00/f07 vs 451px at f02, a **1.24× jump**.
- 64 game frames: f00/f07 body height **53px**; f01–f06 body height **63px** = **1.19×** the f00 body after the 8× crop. The 64 silhouette is 63px inside a 64px frame.
- 64 border contact: f01/f02/f03/f04/f05/f06 have **11, 16, 12, 12, 11, 12** opaque pixels on row 0 — the crown of the head/hair (and in f01/f02 the blade) is cut flat by the top edge. `frame_03` also has **3 opaque pixels on the right edge** — the blade tip is truncated there. The 512 frames are not cropped (50–55px margins); the 64 crop window is the immediate cause of the cut. The 512 scale mismatch is the separate failure in the first bullet.
- Consecutive 64 change: f00→f01 **1375/4096 px (33.6%)**, f06→f07 **1465/4096 px (35.8%)**, versus ≈700–900px for ordinary run steps. This is the scale pop and the weapon snap in one transition.

**Broken requirement**
“Cross-frame/action body size: every shipped slash2 frame must have the same body height … no single shrunken frame”; “no cropped head/hair/hand/boot/blade at the edge”; “slash2 64 body window”; “readable silhouettes at 64”; “no scale popping”.

The 640 canvas is allowed, but the character inside it must stay at the same 512 pixel scale (≈420px body) as the f00/f07 anchors, using the extra 128px only for the raised blade. Instead the action frames are rendered ≈1.22× larger, and the 64 window (512px of a 640 frame) cannot contain the head and blade.

---

### B2 — `slash2` contains a second, sheathed katana; the scabbard is not empty

**Files / frames**
- `slash2/frames_hi/frame_03.png`, `frame_04.png`, `frame_05.png`, `frame_06.png`
- Corresponding 64 frames and `11_slash2_64px_all.png` (f03–f06)

**Evidence**
- In f03–f06 there is a **wrapped tsuka with tsuba and pommel at the lower back**, still joined to the purple scabbard (f04: native x≈365–430, y≈225–295; f05/f06 equivalent). At the same time the **drawn katana** is in the right hand, with its own tsuba and grip at native x≈325–360, y≈290–315; the two objects are not collinear.
- `frame_02` shows the scabbard mouth empty (only a small throat stub at the back); **the second hilt appears at f03** and stays through f06. This is both a duplicate weapon and a frame-to-frame weapon pop.
- f00/f01/f02 and f07 show only one katana (sheathed or drawn), so the second hilt is not an intentional carried spare; it appears mid-action.

**Broken requirement**
“Exactly ONE katana/scabbard/pistol; no second hilt/blade/gun”; “scabbard empty” in slash2; “Katana drawn ONLY in slash2” implies the stowed katana must be gone; “no weapon popping”; check 8.

---

### B3 — `roll` has giant detached fabric slabs fused into the silhouette

**Files / frames**
- `roll/frames_hi/frame_01.png` … `frame_06.png`
- `roll/frames/frame_01.png` … `frame_06.png`
- `work/review/character/11_roll_64px_all.png` (f1–f6)

**Evidence**
- f01: a dark rectangular slab at native x≈110–250, y≈215–300, plus a second below it; the slab has the speckled cloth texture of the outfit and a beveled rectangular outline, not a limb.
- f02: multiple slabs of ≈140–180px wide and 70–150px tall around the body (upper centre, left, lower left, right); the actual character is a small torso/hair mass in the middle.
- f03/f04/f05: equivalent slabs at native x≈150–450, y≈160–480; f06: a slab spans the back/shoulder from the neck to the hip.
- In the 64 frames these slabs become the dominant dark silhouette; f01–f06 no longer read as a woman rolling, only as a dark blob plus hair. `12_roll_3d_truth_all.png` shows the same exploded boxes in the source mannequin, so this is not a 2D edge artifact.

**Broken requirement**
“Roll: … no floating slab”; “Every frame complete … no neighbour fragments”; “Commercial quality: readable silhouettes at 64, coherent motion”; check 7.

---

### B4 — `roll` draws both the pistol and the katana; neither is stowed

**Files / frames**
- `roll/frames_hi/frame_02.png` and `roll/frames/frame_02.png`
- `roll/frames_hi/frame_01.png`, `frame_03.png`–`frame_06.png`

**Evidence**
- f02: a complete pistol (slide, grip, trigger guard, cyan muzzle/slide) is gripped **two-handed** at native x≈100–195, y≈300–360. This is the shoot2 pistol, not a boot or prop; it is roughly 1.4× the shoot2 512 pistol and oversized against the hands.
- f02 also has a **drawn katana** behind the body: a vertical silver blade with tsuba and wrapped hilt at native x≈330–350, y≈380–470, not held by a hand.
- f01: a gray blade with a white tip lies across the upper back (native x≈175–345, y≈250–270), while the purple scabbard with white cap is separately visible at x≈135–290, y≈190–250. f03/f04/f05: a bare katana blade floats diagonally across the hair; f06: a bare blade lies across the back.
- Thus the roll contains **pistol in hand + drawn katana + scabbard**, with the pistol in hand in a non-shoot action.

**Broken requirement**
“Pistol in hand ONLY in shoot2”; “Katana drawn ONLY in slash2”; “Exactly ONE katana/scabbard/pistol”; “katana attached/behind the body”; “no floating slab/weapon”; check 7 and 10.

---

### B5 — `run` legs do not alternate; the 8-frame loop is a one-sided hop

**Files / frames**
- `run/frames_hi/frame_00.png` … `frame_07.png`
- `run/frames/frame_00.png` … `frame_07.png`
- `work/review/character/22_run_loop.png` (f6, f7, f0, f1)

**Evidence**
- The near/light thigh is forward in **every** contact: f00 front thigh (247,195,154) at x≈300–380, rear thigh (207,117,82) at x≈180–270; identical arrangement at f02, f04, f06 (and f07). The far/dark leg never comes forward. This is a same-leg-leading hop, not alternating legs.
- The bounce is 84→80→75→79→84→79→75→84 (bbox top). f07 and f00 are **both low (84)** and are the same near-leg contact; the loop therefore has a double-low/stutter at the wrap, with three low frames (f00, f04, f07) and two high frames (f02, f06).
- `12_run_3d_truth_all.png` shows the same lead-leg phasing in the 3D source, so the 2D is faithfully reproducing a broken run clip; it is still a defect in the shipped frames.
- The 64 run frames inherit both problems.

**Broken requirement**
“run 8-frame self-loop with alternating legs and a vertical bounce”; “coherent motion, no popping”; check 4.

---

## 2. Majors

### M1 — `shoot2` empty holster is missing in three aiming frames and changes appearance

**Files / frames**
- `shoot2/frames_hi/frame_02.png`, `frame_03.png`, `frame_06.png`
- `shoot2/frames/frame_02.png`, `frame_03.png`, `frame_06.png`
- `11_shoot2_64px_all.png` f2/f3/f6

**Evidence**
- In f02/f03/f06 the right thigh is bare from the shorts hem to the knee — no drop-leg holster, no strap, no pouch. In f01/f04/f05 the holster is visible; in f00/f07 the pistol is holstered.
- The visible empty holster is not consistent: f01 shows a gray holster panel/liner with a black strap; f04/f05 show a black pouch with a cyan retention line. The hip prop changes construction between aiming frames.
- `11_shoot2_64px_all.png` shows the same: f01/f04/f05 have a small dark hip patch; f02/f03/f06 have none.

**Broken requirement**
“empty holster stays visible in shoot2”; “holster consistent”; check 9. The pistol is correctly in hand in f01–f06, but the holster continuity fails.

---

### M2 — `shoot2` violet/magenta flecks inside/on the pistol

**Files / frames**
- `shoot2/frames/frame_01.png` (64) — violet (113,74,156) at (56,21); (82,53,116) at (57,21) and (59,21); bright (219,188,255) at (55,23), on the slide/trigger-guard area.
- `shoot2/frames/frame_04.png` (64) — (113,74,156) at (54,20), on the rear sight/slide.
- `shoot2/frames_hi/frame_04.png` — (113,74,156) at (437,165), inside the rear sight; `frame_01.png` — (113,74,156) at (448,173) on the hand/gun edge.

**Evidence**
- `parts/pistol.png` uses the dark outline (56,36,86) and cyan (53,162,196)/(99,203,216); it does **not** contain (113,74,156), (82,53,116), or (219,188,255). Those are character/eye-palette violets bleeding onto the gun.
- At 64 the bright (219,188,255) is a single light-violet pixel, but it is visible at 1× as a fleck on the weapon; at 512 the (113,74,156) reads as a violet dot in the rear sight.

**Broken requirement**
“no magenta/violet fleck inside the gun”; check 9; weapon cleanliness/identity.

---

### M3 — `roll` loses the violet eye

**Files / frames**
- `roll/frames_hi/frame_02.png` (512) and `roll/frames/frame_02.png` (64)
- `roll/frames/frame_03.png` (64)

**Evidence**
- In the 64 roll f02 there are **zero violet pixels in the entire frame**; the visible eye is a white sclera with a black pupil. In the 512 roll f02 the eye is mostly a white sclera with a black pupil and only a 1-px violet sliver at the top — it no longer reads as the violet eye of the design.
- The 64 roll f03 has only one violet pixel in the frame; the eye is effectively lost in the tumble.
- The idle/run/shoot/slash 64 eye is a 2×2 violet block; the roll is the odd action.

**Broken requirement**
“Violet eye intact at 512 and 64”; “violet eyes (opaque pupil)” identity; check 1/2.

---

### M4 — Weapon teleports at the `slash2`/`shoot2` action boundaries

**Files / frames**
- `slash2/frames/frame_00.png` → `frame_01.png`; `frame_06.png` → `frame_07.png`
- `shoot2/frames/frame_00.png` → `frame_01.png`; `frame_06.png` → `frame_07.png`
- `21_transition_pairs.png` / `23_transition_diff.png` only prove f00/f07 equality; they do not cover the adjacent frames.

**Evidence**
- slash f00 (run f0 pose; katana sheathed) → f01: katana is already fully drawn, blade raised in front of the face. f06 (blade extended) → f07 (run f7 pose; katana completely sheathed, pistol holstered). No draw or sheathe pose exists.
- shoot f00 (run pose; pistol holstered) → f01: pistol fully extended in the aim. f06 (aimed) → f07 (run f7 pose; pistol holstered). No raise or lower pose exists.
- 64 consecutive-frame diffs: slash f00→f01 1375, f06→f07 1465; shoot f00→f01 939, f06→f07 1037, versus run’s ordinary ~700–900. The anchors are required to be identical, but f01/f06 themselves are free to be a draw/raise or stow/lower pose; they are instead the fully deployed pose.

**Broken requirement**
“coherent motion, no popping”; “Any … weapon popping”; check 10. (The f00/f07 anchor identity itself passes.)

---

### M5 — `slash2` drawn blade collapses to a needle in f01

**Files / frames**
- `slash2/frames_hi/frame_01.png`; `slash2/frames/frame_01.png`; `11_slash2_64px_all.png` f1

**Evidence**
- f01 blade is 1–2px wide (a near-vertical hairline in front of the face); f02–f06 blades are 5–7px wide with a cyan edge. At 64 f01 the blade is a 1-px line. The hilt is in the hand and the blade is present and full length, but the drawn katana reads as a wire in the frame that establishes the draw, then instantly becomes a broad blade at f02.
- f01 does contain a blade; the defect is its width, not a missing blade.

**Broken requirement**
“katana … full length”; “readable silhouettes at 64”; “coherent motion, no popping”; check 8.

---

## 3. Minors

**m1 — Idle eye/pupil drift.**
`idle/frames_hi/frame_02/03/04.png` show a broad, filled violet iris (41–52 violet px; no black pupil comparable to f00, only a 1-px dark edge) versus the narrower pupil eye of f00/f01/f05–f07 (17–30 violet px, with the 5×8 black pupil in f00). The eye visibly opens/blankens in the middle of the idle loop. At 64 every idle frame is a 2×2 violet block with no discernible pupil. Broken: “violet eyes (opaque pupil)”; “no popping”. Not a transparent hole (alpha is 255 throughout the iris).

**m2 — 64 shoot2 muzzle is 1–2px from the frame edge.**
`shoot2/frames/frame_01.png` … `frame_06.png`: x max 61–62 of 64; f02–f06 also end at y=62. Not cropped (no border pixels), but the aiming silhouette is tighter than every other action; the muzzle/hand nearly touches the right edge. Minor framing risk at 64.

**m3 — 64 shoot2 f03/f06 pistol readability.**
At 64 the gun in f03/f06 is a ~10×3 px bar with a 2×2 grip; the trigger guard is a single cyan pixel. It is still identifiable as a pistol but marginal; f02/f04/f05 are clearly more readable. Check 9 asks for “readable every aiming frame” — these two are borderline.

**m4 — `01_char_ref_64_x16.png` is stale.**
It shows the older concept (different top/hair silhouette and a drawn katana in hand) and does not match the shipped design sheet/parts or the shipped 64 frames. It is a reference file, not a shipped frame, but it is inconsistent documentation in the same packet.

**m5 — 512 `shoot2` f02/f06 body height dips without a pose reason.**
`shoot2/frames_hi/frame_02.png` and `frame_06.png` have body height 409/415px versus 420px in the other aiming frames (head top y=95/89 vs 84; feet fixed at 503). The head itself is not scaled; this is a 1.2–2.6% aim duck. If the aim is meant to be locked, the dip reads as a small body-height pop; verify it is intentional.

---

## 4. Frames actually opened

Every PNG in `/dat/projects/artist2d/work/review/character/` was opened. The `10_*`/`11_*`/`12_*` sheets were inspected cell by cell (all 8 cells per action; slash2 `10_*` cells are 640px). Shipped frames were opened directly for the evidence below; the remaining frames were inspected through the full 8-cell sheets and the 64px sheet.

| Action | 10_* hi (all 8) | 11_* 64 (all 8) | 12_* truth | Shipped evidence opened |
|---|---|---|---|---|
| idle | yes; direct f00/f01/f04/f07 + eye/face crops | yes; 64 eye crops f00/f02/f05/f07 | yes | all 8 via 10_/11_; direct `idle/frames_hi/frame_00/01/04/07` |
| run | yes; 22_run_loop f6/f7/f0/f1 | yes | yes | all 8 via 10_/11_/12_; direct 22 loop images |
| slash2 | yes; direct 640 f00–f07 + waist/hilt/face/scabbard crops | yes; 64 f00/f02 full + edge checks | yes | direct `slash2/frames_hi/frame_00..07`; all 8 64 via 11_ |
| shoot2 | yes; hip crops f00–f07 + gun crops f01–f06 | yes; gun64 f01–f06 | yes | all 8 via 10_/11_; direct hip/gun crops from `frames_hi` f00–f07 |
| roll | yes; direct f01/f02/f03/f06 + face/hand/waist crops | yes | yes | direct `roll/frames_hi/frame_01/02/03/06`; all 8 via 10_/11_ |

Also opened: `MANIFEST.md`, `00_design_sheet.png`, `01_char_ref_64_x16.png`, `02_part_katana.png`, `02_part_scabbard.png`, `02_part_pistol.png`, `20_cross_action.png`, `21_transition_pairs.png`, `22_run_loop.png`, `23_transition_diff.png`.

---

## 5. Checks that produced no defect (for completeness, not praise)

- 64px anchors are pixel-identical: `run:0` = `slash2:0` = `shoot2:0`; `run:7` = `slash2:7` = `shoot2:7`; `idle:0` = `roll:0`; `idle:7` = `roll:7`. `23_transition_diff.png` is black for all six pairs.
- Each action has 8 frames; no exact duplicate frames at 512 or 64 (`idle`, `run`, `slash2`, `shoot2`, `roll`).
- All 512/64 frames are a single opaque component (no detached foreign fragments). The roll slabs are fused to the body — that is the defect in B3, not a separate component.
- Alpha is binary 0/255 in all frames. No transparent eye-pupil hole was found. The enclosed transparent regions flagged by a strict hole test are background gaps, not pinholes: `idle f05` (between the calves, closed by the boot top), `idle f02` (between hair strand and back), `slash2 f01` (between the raised blade and face/hair), `run f02/f06` and `shoot2 f02` (between the legs/scabbard).
- Idle: 8 unique frames, body 420px in all, katana sheathed across the lower back, pistol holstered at the right thigh, one of each.
- Shoot2 512: body 420px, pistol readable in f01–f06, one gun in hand, katana sheathed, one pistol. The failures are the holster continuity and the violet flecks.
- Slash2 512: drawn blade full length and tip inside the 640 frame (`f03` tip x=590, 50px margin); gripped in f02–f06; one pistol holstered; the scabbard prop is present.
- Roll: starts/ends on idle f00/f07, the f01–f05 rotation is forward (head moves right→down→left) and there is no re-inversion after standing at f06/f07. The failures are the slabs and weapons.
- Design sheet and 02 parts: silver hair, violet iris, short-sleeve top + detached sleeves + shorts + boots; katana, scabbard and pistol parts are complete and the pistol part is readable. The in-game stowed katana/pistol states in idle/run match the brief.
- The 3D truth was used only as a pose reference; it confirms the roll source boxes (B3) and the run lead-leg phasing (B5), but no shipped frame was accepted on truth alone.

---

## 6. Packet notes (not extra asset defects)

- `20_cross_action.png` uses only f00 of each action. The five first frames are identity/scale consistent (all 53px at 64) and the weapon states are the stowed ones, so the sheet passes as an anchor comparison. It cannot expose the `slash2` f01–f06 scale pop (B1), the roll interior slabs (B3/B4), or the run leg phasing (B5).
- `21_transition_pairs.png` and `23_transition_diff.png` correctly prove the six 64px anchor pairs (all black). They do not cover the f00→f01 / f06→f07 adjacency, which is where the weapon/scale popping occurs (B1, M4).
- `22_run_loop.png` correctly shows the wrap f6→f7→f0→f1; it is the evidence for the f07/f00 double-low and same-leg contact in B5.
- `12_*` is a 3D mannequin truth sheet, not a shipped asset. The roll truth shows the same exploded boxes as the shipped 2D, which locates the source of B3; the other truth sheets are consistent with the shipped stances and were not used to excuse any 2D defect.
- `01_char_ref_64_x16.png` is a stale reference (m4); `00_design_sheet.png` and the three `02_part_*` images match the shipped design's silver hair, violet eyes, short-sleeve top + detached sleeves + shorts + boots, and the katana/scabbard/pistol parts.
