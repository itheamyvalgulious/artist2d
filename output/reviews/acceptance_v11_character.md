# Acceptance review — character pack v11 (agent, 12 actions × 8 frames)

Reviewer: independent reviewer (char-accept-v11). I did not build these assets.
Verdict: **FAIL** — 2 blockers, 5 majors, 6 minors. The pack must not ship as-is.

Method: opened every PNG in `work/review/character/` (44 sheets) plus all 96 shipped
512/640 frames and 96 shipped 64px frames in `output/character/agent/`. Measured 64px
border contact, per-frame sprite bbox, connected components (detached fragments,
holes), transition SHA-256, per-frame unique hashes, exact palette sampling, and
8–20× nearest-neighbour crops for weapon/eye/edge inspection. Assets were not modified.

---

## Blockers

### B1 — Two katana in one hand-pair at once (duplicate weapon)
**File/frame:** `output/character/agent/slash1/frames_hi/frame_03.png` (512×512) and
`output/character/agent/slash1/frames/frame_03.png` (64×64; same defect, clearly legible).
**Defect:** frame 3 of `slash1` shows **two complete katana with two hilts**: one held in
the raised rear hand, blade running up-left from the fist at ≈(235,205); a second held in
the lower front hand at ≈(400,355), blade running down-right to the frame's lower right.
The dark scabbard is a third, separate object at the lower back. f2 and f4 have only one
blade, so the second sword also *appears and disappears inside the action*.
**Requirement violated:** "Exactly ONE katana/scabbard/pistol; no second hilt/blade…" and
"no weapon teleport/popping".

### B2 — katana blade swaps material to flat cyan + cyan wedge in the torso silhouette
**File/frame:** `output/character/agent/slash3/frames_hi/frame_03.png` (512×512) and
`output/character/agent/slash3/frames/frame_03.png` (64×64).
**Defect:** in this single frame the katana blade is a solid saturated cyan slab
(`rgb(99,203,216)`: 2 218 px, versus 85–245 px in every other `slash3` frame and 133–265 px
in idle/run). Every other drawn-katana frame renders the blade in steel
`rgb(155,155,176)` + `rgb(214,214,230)` with a pale cyan edge `rgb(163,234,240)`; slash3
f3 has 3 px of that edge colour and no steel. Additionally an **opaque flat-cyan wedge**
(~340 px, same `99,203,216`) sits between the hair and the back/shoulder at
≈x150–300, y230–320 — a stray filled shape that is not part of the body or weapon and is
plainly visible at 64 as a cyan triangle at her back.
**Requirement violated:** one weapon / consistent weapon appearance, "no neighbour
fragments", "no weapon … popping", readable silhouette.

---

## Majors

### M1 — Empty holster is missing in every pistol-drawn frame
**Files/frames:** `shoot1` f01–f06, `shoot2` f01–f06, `shoot3` f01–f06 (both `frames/` and
`frames_hi/`).
**Defect:** with the pistol in hand, the right-hip holster pouch (present in idle f0,
run f0, slash/block/roll, i.e. every stowed frame) is **entirely gone**. In
`shoot1/frames_hi/frame_01.png` the hip shows only bare thigh plus the thin grey strap
band; no pouch, no cyan strap line, no holster silhouette. Same in
`shoot2/frames_hi/frame_03.png` and `shoot3/frames_hi/frame_02.png`.
**Requirement violated:** "the empty holster stays visible and consistent in every shoot
frame".

### M2 — Violet fleck inside the gun
**File/frame:** `output/character/agent/shoot1/frames_hi/frame_01.png`, region
x406–411, y166–173 (and 1 px at 412,146).
**Defect:** 12 pixels of the **eye/iris palette** — `rgb(113,74,156)`, `rgb(82,53,116)`,
`rgb(145,105,196)` — sit inside the pistol between the trigger guard and the grip, forming
a violet blob with a white highlight at 20× zoom. These exact values are the iris palette
(and the iris highlight), not part of `parts/pistol.png` (whose only purple is
`rgb(56,36,86)` / `rgb(36,24,56)`). It reads as a pasted eye fragment.
**Requirement violated:** "no violet fleck inside the gun".

### M3 — Blade truncated by the 64px frame border
**Files/frames (64×64):**
- `block/frames/frame_02.png` — non-transparent pixel in column x = 63
- `block/frames/frame_05.png` — x = 63
- `block/frames/frame_06.png` — x = 63
- `slash2/frames/frame_03.png` — x = 63

**Defect:** the blade extends into the last pixel column, so its taper is cut flat by the
canvas edge (verified at 18× on `block/frames/frame_02.png` and `slash2/frames/frame_03.png`;
right-edge alpha = 255). All 512 versions stay inside the canvas
(`block` f02 tip x = 505/512), so the loss happens only in the shipped game frames.
**Requirement violated:** "no cropped … blade at the edge".

### M4 — `jump` does not read as a jump
**Files:** `jump/frames_hi/frame_00…07.png`, `jump/frames/frame_00…07.png`.
**Defect:** all eight frames are a crouch with the boots on the ground line
(lowest boot y = 500–503 px in every frame; sprite bbox y = 84…503 = 420 px, identical to
standing `idle`). The eye moves only y = 134→139 (5 px = 1 px at 64) across the whole
action: there is **no body drop, no leg extension, no launch**. With the knees bent ~90°
and the head still at standing height, the pose reads as a wide-legged squat, not a
jump. (The `12_jump_3d_truth_all` proxy does lower the body in f2–f7, so the shipped art
does not follow its own pose reference.)
**Requirement violated:** "jump … read as their actions", "commercial quality".

### M5 — `slash2` f3: the katana becomes a white ribbon, not held
**File/frame:** `slash2/frames_hi/frame_03.png` (640×640, by design) and the 64px frame.
**Defect:** the weapon is replaced for one frame by a wide white/lavender crescent
(~120 px of `rgb(219,188,255)` fringe on a pale filled ribbon). The fist at ≈(470,190) is
**closed on nothing**; the ribbon's surface passes *behind* the hand rather than a hilt
being gripped. Inside an 8-frame swing this reads as the katana popping into a smear and
back (f2 and f4 both show a normal steel blade with a hilt).
**Requirement violated:** "no weapon teleport/popping", "commercial quality / coherent
motion".

---

## Minors

### m1 — No violet iris in two roll frames
`roll/frames_hi/frame_01.png` and `frame_05.png`: the visible eye is drawn with
`rgb(8,8,12)` + white (`rgb(214,214,230)`) only — sampling the eye box shows no
`rgb(82,53,116)` / `rgb(113,74,156)` / `rgb(56,36,86)` at all (at 64 the f1 eye pixel is
(8,8,12) plus one `(219,188,255)` glint). Every other frame of the pack has the violet
iris. Requirement: "Violet eye at 512 and 64 (including inverted … frames)".

### m2 — Detached 11-px fragment (hair tip)
`shoot3/frames_hi/frame_06.png`: a separate connected component of 11 px at
x175–178, y299–303 (outline/outfit colours) floats below the hair tips, disconnected from
the body (it merges away at 64). Requirement: "no … neighbour fragments".

### m3 — `roll` f2–f5 unreadable at 64
At 64 the inverted frames are silhouette mush (head/hair/boots/limbs interpenetrate, e.g.
`roll/frames/frame_03.png` is a boot on top of an unreadable mass). It is possible to
*guess* a tumble, but it does not read cleanly at game size. Requirement: "readable
silhouettes at 64".

### m4 — Body/head scale varies across actions
Measured eye→chin (anatomical head scale, 512): idle 26–28 px, shoot1 26–27, in_air 27,
jump 29–30, slash1 28, run 31–32, block 32, slash3 25. That is a ±14 % head-size swing;
combined with the fact that **every** frame of 11/12 actions is pinned to exactly 420 px of
silhouette height (idle standing, jump crouch, in_air tuck all 84…503), it looks like the
frames were height-normalised per frame. Switching idle→run makes the character visibly
grow. Requirement: "the character's body scale must not pop; … proportions must match".
(Flagged as major-risk rather than blocker because the head measurement also depends on
head yaw in each frame.)

### m5 — Run bounce is ~1 px at 64
`run` bbox top varies y = 9–10 at 64 and the boot bottom y = 61–62: a 1 px vertical
bounce. Requirement asks for "vertical bounce"; it is present but almost imperceptible.
Leg alternation itself is correct (contact poses alternate; f6→f7→f0 wrap is continuous).

### m6 — Stowed pistol does not read as a pistol at 64
In idle/run/jump/in_air/slash/block the hip object is a plain dark pouch slab with a cyan
strap line (at 512 the pistol grip/barrel are not separable from the holster). At 64 it is
a 5×7 px block. Requirement: "pistol at the right hip with readable pistol shape". It does
match `00_design_sheet.png`, so this may be a design-level miss rather than production
error — but the stated acceptance criterion is not met.

---

## Checks that passed

- **Frame counts / uniqueness:** 12 actions × 8 frames, all present; 8 unique SHA-256 per
  action (no duplicated frame smuggled in).
- **Transition anchors:** all 17 pairs are **byte-identical** (pixel-identical), including
  in_air=f7 jump, shoot1/slash1/block/roll = idle f0/f7, shoot2/slash2 = run f0/f7,
  shoot3/slash3 = in_air f0/f7; SHA-256 values match `MANIFEST.md` exactly.
- **Weapon state boundaries:** katana stowed in idle/run/jump/in_air/roll/shoot* and drawn
  only in slash1/slash2/slash3/block (draw on f1, sheathe on f7 — permitted); pistol in
  hand only in shoot1/shoot2/shoot3. No pistol visible in any slash/block/idle frame.
- **Front/back weapon inventory:** exactly one scabbard + one stowed hilt in stowed frames;
  one pistol in stowed frames (except the M1 holster problem); the scabbard stays visible
  and consistent in the drawn-katana frames.
- **`block`:** reads as a two-handed katana high guard; no shield; blade, hands, scabbard and
  holstered pistol all present.
- **`in_air`:** leg tuck + hair float reads as airborne; start/end match jump/in_air anchors.
- **`roll`:** f1→f6 is a continuous forward tumble (head passes the ground plane at f2–f5),
  f0/f7 = idle.
- **`shoot1/2/3`:** pistol readable at 512 in f1–f6 (slide, trigger guard, grip, cyan slide
  accents); no second gun, no dagger.
- **`slash1/2/3` other frames:** single steel blade with the correct cyan edge; hilt gripped
  in the hand; scabbard retained.
- **Character identity:** long silver hair, violet iris with a dark opaque pupil
  (`rgb(56,36,86)`/`rgb(82,53,116)`) and light-violet highlight, short-sleeve top +
  detached forearm sleeves + shorts + black boots — consistent in 94/96 frames.
- **512/640 canvas margins:** no hi-res frame touches the canvas border (min margin 7 px,
  `block` f2); slash2 hi-res is 640×640 as documented, body window preserved.
- **Holes:** all enclosed transparent regions at 64 are genuine negative space (arm↔torso,
  blade↔body, between legs); no 1-px pinhole was found inside a solid limb or the torso.
- **All 44 review sheets opened**, including `20_cross_action.png`, `22_run_loop.png` and
  `23_transition_diff.png` (the diff sheet is black = identical, consistent with the hashes).

## Notes on the review packet (not asset defects)

- The `12_*_3d_truth_all.png` boards are a flat-shaded proxy rendered from a different
  camera/pose set than the shipped side-view sprites (e.g. `slash1` truth shows both arms
  out to the sides and a short blade, while the shipped f3 is a lunging two-bladed pose;
  `block` truth holds the sword in one hand with the other arm extended). They can validate
  limb topology but not pose fidelity, and `jump`'s truth does lower the body where the
  shipped art does not.
- `21_transition_pairs.png` is scaled too small to verify anything visually; the SHA-256
  check in `MANIFEST.md` is the usable evidence (and it passes).

---

## Frames opened

Review packet (all 44): `00_design_sheet.png`, `02_part_katana.png`, `02_part_pistol.png`,
`02_part_scabbard.png`, `10_{idle,run,jump,in_air,shoot1,shoot2,shoot3,slash1,slash2,slash3,block,roll}_hi_all.png`,
`11_{same 12}_64px_all.png`, `12_{same 12}_3d_truth_all.png`, `20_cross_action.png`,
`21_transition_pairs.png`, `22_run_loop.png`, `23_transition_diff.png`.

Shipped frames inspected individually at 1×, 8×, 10×, 12×, 18× or 20× (highlights):
`idle/frames_hi/frame_00..07`, `idle/frames/frame_00`,
`run/frames_hi/frame_00..07`, `run/frames/frame_03`,
`jump/frames_hi/frame_00,01,02,03,04,05,06,07`,
`in_air/frames_hi/frame_00,03,04`, `shoot1/frames_hi/frame_00,01,02,03,04,05,06,07`,
`shoot2/frames_hi/frame_00,03,04`, `shoot3/frames_hi/frame_02,03,04,05,06`,
`slash1/frames_hi/frame_00,01,02,03,04,05,06,07`, `slash2/frames_hi/frame_00,03,04`,
`slash3/frames_hi/frame_03,04,05,06`, `block/frames_hi/frame_00,02,05,06`,
`roll/frames_hi/frame_00,01,02,03,04,05,06,07`, plus the 64px versions of every action
(`frames/frame_00..07` for all 12 actions) and `parts/{katana,pistol,scabbard}.png`.

Files are listed in the order they were opened; no shipped asset was modified.
