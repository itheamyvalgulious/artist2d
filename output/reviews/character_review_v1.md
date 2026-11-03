# Independent character review v1 — cyberpunk agent, 5 actions

Reviewer: `char-review-v1` (independent multimodal reviewer; did not generate these assets).
Date: 2026-11-01.
Scope: every PNG in `work/review/character/` (23 files) plus, where a label was ambiguous, the full-resolution
originals in `output/character/agent/<action>/frames_hi/frame_0*.png` and `frames/frame_0*.png`.

Method / integrity
- 100 % coverage: all 23 packet files opened and judged (table below).
- No asset was modified, no pipeline code was run, nothing was regenerated.
- For evidence I magnified regions with nearest-neighbour crops written **outside the project**
  (`/tmp/opencode/zoom/`) and did read-only pixel statistics on the originals
  (alpha bbox, byte-exact pair comparison, colour histograms, isolated-pixel counts).
- Anything I claim below is visible in the shipped pixels or is a byte-exact measurement quoted in the text.

---

## 1. File-by-file coverage (23/23)

| # | File | Verdict | One-line reason |
|---|------|---------|-----------------|
| 1 | `00_design_sheet.png` | **PASS** | Female, silver hair, violet iris, short-sleeve top + detached sleeves + shorts + boots; katana / empty scabbard / pistol shown as three separate complete parts with readable blade, tsuba, wrapped grip, barrel, trigger guard. (Minor m1: the character in the sheet holds a drawn katana.) |
| 2 | `01_char_ref_64_x16.png` | **PASS** | 64 px master ref is a woman in the right outfit with a single bright-violet iris pixel; weapons stowed/holstered. Minor m1 (katana drawn in hand in a reference sheet). |
| 3 | `02_part_katana.png` | **PASS** | Full length, bevel tip, cyan edge, dark spine, wide tsuba, diamond-wrapped grip. Reads as a katana at part scale. |
| 4 | `02_part_scabbard.png` | **PASS** | Separate, empty, closed mouth + silver chape, correct length (461 px vs 485 px katana). Minor m5 (grey notch at the mouth). |
| 5 | `02_part_pistol.png` | **PASS** | Compact pistol: slide, barrel/muzzle, trigger guard, grip, cyan slide accents. Complete and readable. Minor m6 (crop is very tight). |
| 6 | `10_idle_hi_all.png` | **FAIL** | Face is a different drawing in f0/f1 vs f2–f7; head-top jumps 17 px; heavy 1 px speckle. |
| 7 | `11_idle_64px_all.png` | **FAIL** | Same defects at game res: head/face pop of ~2 px between f1→f2, 6–14 % of the sprite re-renders every frame. |
| 8 | `12_idle_3d_truth_all.png` | **PASS** | Truth sheet is internally consistent (arms folded in front, one weapon prop at the hip, gentle breathing). |
| 9 | `10_run_hi_all.png` | **FAIL** | Thighs ~2–3× idle thickness, legs merge into one mass in f2/f6, no vertical bob, non-collinear back-weapon. |
| 10 | `11_run_64px_all.png` | **FAIL** | At 64 px the legs are flat orange slabs; f2/f6 lose the far leg entirely; boot/ground contact unreadable. |
| 11 | `12_run_3d_truth_all.png` | **PASS** | Truth bobs correctly and alternates halves; single weapon prop. |
| 12 | `10_slash2_hi_all.png` | **FAIL** | Katana becomes a 2–4 px needle (f3), blade length varies 90–250 px, sword disappears entirely in f6. |
| 13 | `11_slash2_64px_all.png` | **FAIL** | At 64 px the katana never reads as a katana (1–2 px line, no tsuba); f6 empty-handed. |
| 14 | `12_slash2_3d_truth_all.png` | **PASS** | Truth pose sequence is a forward/down sweep; note it renders the sword as a thin stick (see M11). |
| 15 | `10_shoot2_hi_all.png` | **FAIL** | Pistol missing entirely in f1 and f4; hip holster also absent → weapon nowhere. |
| 16 | `11_shoot2_64px_all.png` | **FAIL** | Same: f1/f4 hand ends in a fist blob; at 64 px the pistol in f2/f3/f5/f6 is oversized/illegible. |
| 17 | `12_shoot2_3d_truth_all.png` | **PASS** | Truth holds the arm horizontally for all 8 frames (art diverges at the anchors, see M11). |
| 18 | `10_roll_hi_all.png` | **FAIL** | Sprawl, not a tuck: legs extended in f2–f5; f4 shows three boot-shaped masses for two legs; framing jumps. |
| 19 | `11_roll_64px_all.png` | **FAIL** | f2/f3/f4/f5 are unreadable jumbles at game resolution (hair, torso and limbs fuse). |
| 20 | `12_roll_3d_truth_all.png` | **PASS** | Truth rotates a full 360° forward and starts/ends standing. |
| 21 | `20_cross_action.png` | **FAIL** | Cross-action sheet itself exposes the needle katana (slash2 panel) and the illegible roll panel. |
| 22 | `21_transition_pairs.png` | **PASS** | All six pairs are byte-identical (verified, see §7). |
| 23 | `22_run_loop.png` | **FAIL** | f7→f0 is the single largest discontinuity in the cycle (1437/4096 px at 64 px) — visible pop. |

---

## 2. Identity

**What passes.** Female silhouette in every frame and every action; never the knight, never male. Long flowing silver
hair in all five actions, hip length, streaming to the rear in the run. Outfit is correct: short-sleeve top, bare
midriff, detached forearm sleeve with a cyan cuff, violet/purple shorts, black chunky combat boots with laces.
Palette is a locked set (44–46 colours at 512, 22 at 64) of `#08080c` outline, gunmetal ramp
`#23232e / #36364 6 / #4e4e63 / #6f6f88 / #9b9bb0 / #d6d6e6`, violet `#241838 / #382456`, warm skin
`#f7c39a / #f7b184 / #cf7552 / #a95539`, cyan `#63cbda / #35a2c4`. That is exactly the requested
navy / gunmetal / silver / cyan / violet / warm-skin palette.

**BLOCKER B4 — the face is not the same face across frames of the same action.**
`10_idle_hi_all.png` f0 and f1 vs f2–f7 (identical at 64 px, `11_idle_64px_all.png` f0/f1 vs f2–f7):
- eye in f0/f1 = white sclera with a thin violet rim, ~7 px wide, with a 1 px dark pupil;
- eye in f2–f7 = a large solid violet lens ~14 px wide with a white rim (a completely different eye design);
- the fringe/bang shape differs (f0/f1 has a smooth crown, f2–f7 has a spiked fringe over the forehead);
- the chin/mouth line present in f0/f1 is gone in f2–f7.
Evidence: `frames_hi/idle/frame_00..03.png` magnified 12×; the idle head montage shows four different faces.
Fix: generate the head **once** and composite the same head/face layer into all 8 idle frames (and all actions),
offsetting only the body. No frame may call the image model for the head again.

**BLOCKER B5 — idle loop pops by 17 px (2.1 px at 64).**
Measured alpha bounding boxes of `idle/frames_hi`: f0 and f1 `y 67..503`; f2–f7 `y 84..503` (x 145..336 for all).
The crown of the head is 17 px lower from f2 onward and jumps back at f0. This is a hard visible pop twice per loop
(f1→f2 and f7→f0; the f7→f0 pair changes 650/4096 px at 64 px, more than any internal idle step).
Fix: re-export idle with one head geometry; force the bbox to `y 84..503` for all 8 frames.

**MAJOR M10 (identity/scale) — the head grows by ~20 % outside idle.**
Idle f2 head (hair crown → chin) is visibly smaller than run f2 / slash2 f2 / shoot2 f5 at the same magnification
(head-compare montage). The run is also shorter overall (420 px vs 437 px tall) **while** having a bigger head, i.e.
shorter legs + bigger head = chibi drift. Requirement says no chibi change. Fix: normalise the head to one pixel size
and keep the leg length constant across actions.

**MINOR m7 — face reads crude at 512.** Large wedge nose, long jaw, no lips, and 1 px speckle across the cheek
(salt-and-pepper skin shading) in `run/frames_hi/frame_02.png` and `shoot2/frames_hi/frame_04.png`. At 64 px it is
acceptable; at the review resolution it reads masculine. Fix: clean the cheek speckle and simplify the nose to 2 tones.

**MINOR m9 — outfit drift vs the design sheet.** The sheet's top reaches the hip; the frames show a crop top with a
bare midriff. Same palette, but the silhouette changed between the sheet and the animation.

**MINOR m8 — hair edges are ragged.** Strands terminate in 1 px stair-steps and the mass has no strand separation;
at 64 px it is one flat grey cape. Fix: quantise the hair silhouette to 2 px steps and split it into 2–3 clusters.

---

## 3. Weapons

**What passes.** No shield, no greatsword, no dagger, no extra pistol. The katana is drawn **only** in slash2 and the
pistol **only** in shoot2 (subject to the missing-prop bugs). Stowage logic is correct where it works: the hip holster
is present in every stowed frame (idle f0–f7, run f0–f7, slash f0/f7, shoot f0/f7) and is **absent** exactly in the
frames where the pistol is in hand — so there is no duplicate pistol.

**BLOCKER B1 — the pistol vanishes in `shoot2` f1 and f4.**
`shoot2/frames_hi/frame_01.png` and `frame_04.png`: the extended arm ends in a dark glove with a thumb spike; there is
no slide, no barrel, no trigger guard, and the hip holster is also gone (hip crop shows only belt + shorts). Alpha
proof: the rightmost extent is x=425 (f1) / x=464 (f4) versus x=498 for f2; the silhouette in that region is a fist
(`#` map printed from the alpha channel: a rounded blob with one spike, no gun outline). The pistol exists in f2, f3,
f5, f6 only.
Fix: composite the `02_part_pistol` silhouette into f1/f4 at the same scale/orientation as f2/f5, then re-attach the
glove over the grip; re-render the arm with a locked "aim" pose instead of a free regeneration.

**BLOCKER B2 — the katana vanishes in `slash2` f6.**
`slash2/frames_hi/frame_06.png`: no blade anywhere in the frame (alpha x-max 380, i.e. nothing protrudes past the
body); the hand is a closed fist at the hip. The scabbard is still mounted on the back. f5 has the blade, f6 has none,
f7 is a byte copy of run f7 with the sword sheathed again — so the weapon teleports away and back within two frames.
Fix: draw f6 with the blade continuing the arc (down/back), and add a real sheathing motion in f6/f7 if the sword must
be stowed at f7.

**BLOCKER B3 — the drawn katana is a needle and its length changes per frame.**
Blade length in `slash2/frames_hi` (grip → tip, read off the 512 px frames): f1 ≈ 160 px, f2 ≈ 250 px, f3 ≈ 90 px, f4 ≈ 190 px,
f5 ≈ 215 px at 512. Blade thickness in f3 is 2–4 px, in f2 6–8 px; the parts sheet blade is ~14 px wide with a cyan
edge and a dark spine, and the tsuba is not visible on the drawn sword at all. In f3 the katana reads as a light beam,
not as the parts-sheet katana (this is also what `20_cross_action.png` shows). A full katana on a 420 px figure
should be ≈ 200–240 px of blade (the part is 485 px long for a ~1.7 m character).
Fix: stop drawing the sword from the pose prompt. Composite `02_part_katana` rigidly: constant scale (blade
≈ 210 px at 512), rotate about the tsuba, keep the cyan edge + black spine + visible tsuba in every frame, and clip
nothing.

**MAJOR M5 — the holstered pistol is not readable as a pistol.**
`idle/frames_hi/frame_00.png`, `run/frames_hi/frame_07.png`, `shoot2/frames_hi/frame_00.png`: the hip prop is a
≈ 30 × 95 px black slab with one long vertical cyan strip — no grip, no trigger guard, no muzzle. The parts sheet is
117 × 88 with a clear guard. At 64 px it is a black blob. Requirement "pistol holstered at hip" is therefore not
visually satisfied in any stowed frame.
Fix: composite the pistol (rotated muzzle-down, scaled to ~45 × 34 at 64 px) inside a simple holster shell so the
grip and trigger guard silhouette remain visible.

**MAJOR M4 — the back-mounted sheathed katana is geometrically impossible.**
`idle/frame_00.png`, `run/frame_02.png`, `run/frame_07.png`, `shoot2/frame_05.png`: the hilt above the shoulder points
**down-right** (its axis runs from upper-left into the torso), while the scabbard end below the hip points
**up-right** from a silver chape at the lower-left. Two visible segments of one rigid scabbard must be collinear; these
are at roughly +45° and −40°, i.e. they cannot belong to the same straight object. In addition a third dark rounded
stub protrudes behind the right hip (`shoot2/frame_05.png`, 7× crop) that exists in no 3D truth frame (the truth has
exactly one weapon prop). At 64 px the result is three loose sticks.
Fix: rig the scabbard as a single line from the right shoulder to the left hip, hide the occluded middle behind the
torso, delete the third stub, and derive both visible ends from that one line.

**MINOR m2 — the pistol in hand is oversized.** `shoot2/frame_02/frame_05`: ≈ 100 px long at 512 (23 % of the 420 px
body ≈ 40 cm) for a "compact pistol". Scale to ≈ 55–60 px.

**MINOR m3 — loose grip.** `shoot2/frame_05`: a 2–4 px gap between the glove and the pistol's grip; the gun looks
pinned to the air in front of the fist.

**MINOR m1 — drawn katana outside slash2.** `00_design_sheet.png` and `01_char_ref_64_x16.png` show the katana drawn
in hand. The action frames are correct, but the reference implies a weapon-in-hand default. Change the refs to the
stowed pose.

---

## 4. Actions

### idle — FAIL (B4, B5, M10, m4, m8)
Relaxed stance, both hands empty, all weapons stowed: correct. But the "breathing" is not breathing: the frames are
re-generated, not offset (15 000–32 000 changed pixels per consecutive pair at 512, 228–583 per pair at 64 px ≈ 6–14 %
of the sprite). The loop therefore boils (hair, chest, thigh shading all shift) instead of breathing.
Minor m4: the hands merge into the holster mass and do not read as two empty hands.
Fix: one body layer, ±1–2 px chest/shoulder offset, hair offset ±1 px, no re-render.

### run — FAIL (M1, M2, M3, M4, M5, M10)
Self-looping, side view facing screen-right, hair streaming, face visible, weapons stowed: correct in principle.
- **M1 thickening:** the near thigh is 10–14 px wide at 64 px (80–112 px at 512) in f2/f5 vs 4–5 px in idle; the legs
  are 2–3× thicker than the idle legs and the far leg is drawn with the same tone as the near leg, so in f2 and f6 the
  two legs fuse into one orange mass (no knee, no ankle, no ground contact). Fix: keep the idle limb width, give the
  far limb a one-step darker tone, and separate the silhouettes with a 1 px outline gap.
- **M2 the cycle is a 4-frame cycle played twice:** leg phase f0≈f4, f1≈f5, f2≈f6, f3≈f7, and the near (screen-right)
  leg leads in **both** halves → no alternating strides, it reads as a one-legged scamper. Fix: mirror the second half
  (or re-generate f4–f7 with the far leg leading).
- **M3 no bob:** alpha bbox is exactly `y 84..503` in all 8 frames while the 3D truth bobs; the run will glide.
  Fix: drop the per-frame bbox normalisation and allow ±3–4 px vertical travel at 512.

### slash2 — FAIL (B2, B3, M4, M10)
Anchors correct (f0/f7 = run f0/f7 byte-identical), arc sweeps up-back → up-forward → horizontal-forward → down-forward
→ down: correct direction, face visible in every frame. But the blade is a needle (B3) and disappears in f6 (B2), and
the guard/grip do not read at 64 px. In `11_slash2_64px_all.png` f1–f5 the sword is a 1–2 px light line: at game
resolution this is not a katana.

### shoot2 — FAIL (B1, M5, m2)
Anchors correct, arm horizontal, pistol aimed horizontally screen-right and clearly readable in f2/f3/f5/f6 with the
cyan slide — those four frames are the best art in the packet. But f1 and f4 have **no pistol at all** (B1) and the
holstered pistol is unreadable (M5).

### roll — FAIL (M6, M7, M8)
Starts and ends in idle (f0 = idle f0, f7 = idle f7, byte-identical) and the body does rotate a full 360° forward
(head right → head down → head left → head up), matching the truth's rotation order. But:
- **M6 not tucked:** f2–f5 are an extended sprawl (legs straight out, arms away from the torso). At 64 px
  `11_roll_64px_all.png` f2/f3/f4/f5 are unreadable — the hair, the torso and the limbs fuse into one shape, and f4
  shows **three** boot-shaped masses for two legs (7× crop of `frame_04.png`, legs region). Fix: re-pose with knees
  to chest, elbows in, chin tucked; make the two feet clearly distinguishable.
- **M7 framing:** f2's body occupies only `y 252..503` (the whole upper half of the frame is empty) while f3 occupies
  `y 78..503`; f4 and f5 reach x=509 / x=506 — 3 px from the right edge. Fix: keep the tumbling body centred with a
  ≥ 10 px margin and a consistent pivot (hip centre, not bbox centre).
- **M8 f1 is a mid-air upright run pose** while the truth's f1 is already tilted ~45° forward; the launch reads as a
  run frame pasted in.

---

## 5. Cross-action consistency

Same character, same outfit, same palette, same hair length, no missing arms, no extra arms, no shield/dagger. But:
face/head differ in size (M10) and design (B4); the limb thickness changes by 2–3× between idle and run (M1); the
weapon mount geometry changes between idle/run/shoot (M4); the hip holster silhouette changes shape between the
stowed frames (a big cyan slab) and the drawn frames (a small black pouch). `20_cross_action.png` documents the
defects rather than disproving them: its slash2 panel is the needle-blade frame and its roll panel is unreadable.

---

## 6. Transitions and the run loop

`21_transition_pairs.png` — **PASS**, and verified as more than "looks the same": all six pairs are **byte-identical**,
both at 512 and at 64 px:

| pair | 512 px | 64 px |
|---|---|---|
| run:0 / slash2:0 | identical | identical |
| run:7 / slash2:7 | identical | identical |
| run:0 / shoot2:0 | identical | identical |
| run:7 / shoot2:7 | identical | identical |
| idle:0 / roll:0 | identical | identical |
| idle:7 / roll:7 | identical | identical |

The mechanism, however, is "copy the anchor frame", which creates the teleports in §3: slash2 f6 → f7 re-mounts a
fresh sheathed katana; shoot2 f1 has neither hand nor holster pistol. Passing the anchor test is not enough — the
frames adjacent to the anchors must be re-authored to connect.

`22_run_loop.png` — **FAIL**. The wrap f7→f0 is the largest single discontinuity in the cycle: 1437 of 4096 px change
at 64 px, versus 684–1173 for every internal adjacent pair, and 72 267 px at 512. The legs go from the f7 stance to
the f0 wide split while the hair and arms flip phase in the same step: a visible pop on every loop. Fix: author f0/f7
as a proper contact pair (equal stride length, same hair phase) instead of reusing the same generated frames.

---

## 7. Artifacts / pixel quality

- **Magenta / pink blocks: none.** 0 hits of `r>150, b>150, g<90` across all 40 final frames. (The magenta in
  `12_*` is the truth render's chroma-key background, only in the reference sheets.)
- **Anti-aliasing: none.** 0 pixels with partial alpha in all 40 frames; 0 blended colours.
- **Palette:** locked, 44–46 colours (512) / 22 (64). Consistent ramp between frames.
- **MAJOR M10 speckle noise:** 3.5–5.4 % of visible pixels are *isolated* (all 8 neighbours different) —
  1 440–2 900 pixels per 512 frame. On skin this reads as dirt/bruises (clearly visible on the thighs and cheeks),
  on hair as ragged edges. Clean pixel art should be < 1 %.
- **MAJOR M10 sub-pixel detail:** only 65–73 % of 8×8 blocks are colour-uniform, i.e. the 512 files are not a clean
  8× doubling of the 64 px sprite; they contain 2–4 px features. Consequence: at 64 px the detail collapses into
  noise (see the boot/thigh mush in `11_run_64px_all.png`).
- **MAJOR M9 512 vs 64 divergence:** nearest-downsampling `frames_hi` and comparing to the shipped `frames` differs in
  691–956 of 4096 px (17–23 %) — the review sheets are **not** the shipped game art. Concretely, the violet iris
  `#9169c4` present in the 512 art (≈ 2 px per frame) does not exist at all in the 64 px frames, while the 64 px
  char ref does have it: **the violet eyes do not survive into the game sprite.**
- **MINOR m5:** `02_part_scabbard.png` has a grey notch at the mouth that reads as a chipped/broken edge.

---

## 8. 3D truth consistency

| action | follow? | divergences |
|---|---|---|
| idle | **no** | The truth's arms are folded in front of the belly; the art's arms hang at the sides. The truth's single weapon prop is at the hip; the art mounts a scabbard on the back. |
| run | **yes** | Pose order, stride halves and crouch frames match; the art removes the truth's vertical bob (M3) and re-draws the far limb so it merges. |
| slash2 | partly | Arc direction matches; the art raises the arm far above the truth in f1–f2 (the truth keeps the hand at chest height). The truth's katana is itself a thin white stick, and that is exactly the defect the art inherited (B3). |
| shoot2 | partly | The truth's arm is horizontal in **all 8** frames including f0/f7; the art's f0/f7 are run anchors with the arm down — so the two anchor frames diverge from the truth even though they satisfy the transition requirement. This is a spec conflict the pipeline did not resolve. |
| roll | **yes** | Rotation order matches (≈ 0/45/90/150/210/260/315/360°). But the truth itself is a sprawl rather than a tuck, so the art inherits a non-tucked roll (M6). |

---

## 9. Verdict

**FAIL.** No blockers/majors may remain for a PASS; this packet has 5 blockers and 11 majors.

Blockers: (B1) the pistol is missing in shoot2 f1/f4; (B2) the katana is missing in slash2 f6; (B3) the drawn katana
is a 2–4 px needle of varying length; (B4) two different faces in one idle loop; (B5) a 17 px head jump that makes the
idle loop pop.

Top majors: 2–3× thigh thickening and fused legs in the run; a 4-frame cycle repeated with the same leading leg; no
vertical bob; an impossible non-collinear back-scabbard plus a third stray stub; an unreadable holstered pistol; a
sprawling, illegible roll with bad framing; 3.5–5.4 % isolated-pixel noise; and the 512 review art not matching the
shipped 64 px art (the violet eyes are lost).

What is genuinely good and must be preserved: the parts sheets (three separate, complete, readable weapons), the
palette discipline (no AA, no magenta, locked ramp), the byte-identical transition anchors, the shoot2 aim frames
(f2/f3/f5/f6) which are the visual benchmark for the whole set, and the run's overall stride readability at 512.

---

## 10. Re-verification checklist for the pipeline

1. Re-render idle/run/slash2/shoot2/roll with a **locked head/face layer**; assert `ymin == ymax` consistency:
   idle `y 84..503` in all 8, run `y 78..509` band (allow a 6 px bob).
2. Assert **exactly one** weapon prop in the stowed frames: one collinear scabbard line, one pistol in the holster
   with a visible trigger guard.
3. Assert the pistol is present **and** ≥ 45 px long in every shoot2 frame f1–f6; assert the blade is present and
   200–240 px long in every slash2 frame f1–f6.
4. Composite parts instead of re-generating them; assert the blade width ≥ 8 px at 512 (≥ 1 px at 64 px with a
   tsuba pixel).
5. Re-export 64 px from the 512 atlas with a nearest 8× block pass; assert `downsample(hi) == shipped_64`.
6. Assert isolated-pixel ratio < 1 % per frame.
7. Retake `22_run_loop` after making f7/f0 a true contact pair; assert `diff(f7,f0) ≤ max(diff(fi,fi+1))`.

---

### Summary

The pipeline produced a strong design sheet and three genuinely good weapon parts, a disciplined palette with zero
anti-aliasing and zero magenta, and mechanically perfect transition anchors, and its shoot2 aim frames are the best
art in the set. It did not, however, produce a coherent animation set: the idle contains two different faces and a
17 px head jump, the run has thighs 2–3× too thick that fuse into a single mass in the passing frames and repeats the
same leading leg, the slash's katana degenerates into a 2–4 px needle that changes length every frame and then
disappears in f6, the shoot's pistol is simply absent in f1 and f4, the roll sprawls instead of tucking and is
unreadable at 64 px, the sheathed katana is mounted on a geometrically impossible broken line, the holstered pistol is
an unreadable slab, ~4 % of all pixels are isolated noise, and the 512 px sheets reviewers are shown are not the art
that ships (the violet eyes never reach the 64 px sprite). Verdict: **FAIL** — regenerate with locked head/weapon
layers and composited parts, then re-review every frame.
