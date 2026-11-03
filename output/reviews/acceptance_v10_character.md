# Character acceptance review v10 — agent sprite pack

**VERDICT: FAIL** (1 blocker, 3 majors, 6 minors)

- Reviewer: independent; did not build these assets; no asset was modified. This report is the only file written.
- Packet reviewed: `/dat/projects/artist2d/work/review/character/` — all 24 PNGs (the 23 listed in `MANIFEST.md` plus the unlisted `01_char_ref_64_x16.png`) and `MANIFEST.md`.
- Shipped frames cross-checked pixel-for-pixel: `/dat/projects/artist2d/output/character/agent/<action>/frames/frame_00..07.png` (64) and `<action>/frames_hi/frame_00..07.png` (512; slash2 640) for idle, run, slash2, shoot2, roll, plus `parts/{katana,scabbard,pistol}.png`. The packet is current: packet 18:17, frames 17:52–17:56, `build_report.json` / `transitions.json` 17:56:34, no build process running at 18:41.
- Method: every packet PNG opened as an image; all 80 shipped frames loaded and measured (alpha, bbox, border contact, connected components, filled holes, hashes, pixel equality); targeted 4–28x nearest-neighbour crops of every face, hip, hilt, gun and frame edge that is cited below.

Severity used here: blocker = asset is broken as delivered; major = clearly visible shipped defect against an explicit requirement; minor = local/small defect or readability note.

---

## BLOCKERS

### B1 — Idle frames 2, 3 and 4 are rendered at ~0.71 scale and contain a second detached head

- Files: `output/character/agent/idle/frames_hi/frame_02.png`, `frame_03.png`, `frame_04.png` (512) **and** `output/character/agent/idle/frames/frame_02.png`, `frame_03.png`, `frame_04.png` (64). Evidence: `10_idle_hi_all.png` (frames 2–4 and the head fragment under each), `11_idle_64px_all.png` (same).
- Defect (512, f2 measured; f3/f4 identical): the character is one component 299 px tall, bbox `(169,84)–(342,382)`, vs 420 px tall `(…,84)–(…,503)` in f0/f1/f5/f6/f7 — a 0.712x scale. Her feet end at y=382, i.e. **121 px above the ground line** used by every other idle frame (y=503). Below her feet, a **second, detached copy of the head** (hair + face + violet eye) floats at `(208,404)–(301,503)`, 6 260 opaque px, 22 px below her body, with its own bottom sitting exactly on the ground line the body should stand on.
- Defect (64, f2): body component `(21,10)–(42,47)`, 38 px tall vs 53 px in the other idle frames (0.717x), feet at y=47 instead of y=62; detached head `(26,50)–(37,62)`, 107 px, with silver hair, skin, and a violet eye pixel — i.e. at game resolution the idle frame contains **two figures**: a shrunken girl and a floating head at her feet.
- f3 and f4 are the same defect: 512 main 18 837 / 18 636 px + fragments 6 289 / 6 250 px at `(208,404)–(301,503)`; 64 main 340 / 337 px + fragments 109 / 111 px at `(26,50)–(37,62)`.
- Requirement: every frame complete, no neighbour/duplicate body parts; cross-frame body size consistent (no shrunken/oversized frame); coherent motion; commercial quality. An idle cycle cannot contain a 29% size pop and a duplicate head.
- Note: this is the same failure class v9 saw in slash2 f3/f4 in an earlier build; in this 17:52–17:56 build it is idle f2–f4. The build keeps relocating this bug; it must be made deterministic.

---

## MAJORS

### M1 — `slash2/frames/frame_04.png` (64): the drawn blade is cut flat at the right frame edge

- File: `output/character/agent/slash2/frames/frame_04.png`. Evidence: `11_slash2_64px_all.png` f4; 16x crop.
- Defect: alpha touches the right border `x=63` at rows `y=52,53,54` (3 px). The 640 hi-res f4 is complete (bbox `(126,156)–(583,567)`, tip inside the canvas), but the 64 game frame is an 8x crop of the 512 body window `x=64..575`, and **110 opaque hi-res px** of the blade tip at `(576,486)–(583,500)` fall outside that window. The blade therefore ends in a flat vertical cut at the frame border instead of a tip.
- Requirement: every frame complete — no cropped blade at the edge; readable silhouette at 64.
- Note: only f4 loses content; f0–f3, f5–f7 have no content outside the crop window.

### M2 — `slash2` f2 (512): a second katana hilt is visible on her back while the drawn katana is in her hand

- File: `output/character/agent/slash2/frames_hi/frame_02.png` (visible at `(372,262)–(430,305)`); at 64 it is `slash2/frames/frame_02.png` around `(38,25)–(46,30)` but merges into the body/hair silhouette and is not separately readable at game resolution — the defect is confirmed on the 512 art.
- Defect: the drawn katana is gripped in her right hand at `(355,345)–(400,395)` with the blade up-right; at the same time a **wrapped tsuka with a rounded silver kashira** (identical construction to the stowed hilt in `idle/frames_hi/frame_00.png` at `(296,206)–(352,250)`) protrudes from her upper back at `(372,262)–(430,305)`, above the scabbard that runs down-left. The sheathed katana was not hidden/emptied when the sword was drawn, so the frame shows **one drawn katana + one sheathed katana = two hilts**.
- Requirement: exactly ONE katana/scabbard/pistol; no second hilt/blade. When drawn, only the empty scabbard should remain on the back (as the `01_char_ref_64_x16.png` reference and the scabbard part show — the scabbard part has silver end caps, not a wrapped hilt).
- Note: in f1/f3–f6 the stowed hilt is occluded by the arm/hair, so f2 is the frame that reveals it; the fix is to suppress the stowed hilt in all slash2 frames.

### M3 — `shoot2` f1–f6 (512 and 64): the empty holster is missing

- Files: `output/character/agent/shoot2/frames_hi/frame_01..06.png` and `frames/frame_01..06.png`. Evidence: `10_shoot2_hi_all.png`, `11_shoot2_64px_all.png`.
- Defect: f0/f7 (run anchors) show the pistol in a drop-leg holster on the right/near thigh (holster box + checkered grip + strap, e.g. idle f0 `(300,330)–(365,430)`, slash2 f2 `(262,380)–(350,470)`). In shoot2 f1–f6 the pistol is in the extended hand and **the holster is gone with it**: the near thigh is bare skin from the shorts hem to the knee, no holster body, no strap, no buckle. There is no empty holster anywhere in the action, at either resolution. The pistol and holster appear to move as one prop.
- Requirement: empty holster visible and consistent in shoot2; weapons stowed/unstowed without teleporting props.

---

## MINORS

### m1 — `shoot2` f6: one violet pixel inside the gun/trigger-guard edge

- Files: `shoot2/frames_hi/frame_06.png` at `(x=451,y=236)` and `shoot2/frames/frame_06.png` at `(x=56,y=29)`; colour `#DBBCFF` (219,188,255), between gun grey `#23232E/#363646` and skin `#F7C39A`.
- Defect: a single lavender fleck in the pistol silhouette at the trigger-guard/hand contact. At 64 it is the only saturated violet pixel in the gun and reads as a colour bleed; the rest of the gun is clean (0 violet pixels in `frame_01..05`, 512 and 64). Fails the explicit "no violet fleck inside the gun" check, though it is 1 px.

### m2 — `roll` 64 f1 and f5: hair touches the right frame border

- Files: `roll/frames/frame_01.png` (`x=63,y=26`, 1 px) and `roll/frames/frame_05.png` (`x=63,y=26–27`, 2 px).
- Defect: the hair silhouette is flush with the right edge of the 64 frame and looks cut. The 512 source is not clipped (hair tip at `x=505`, 6 px margin; f1 bbox `(86,129)–(505,503)`, f5 `(100,136)–(505,503)`), so this is a downscale-border artifact, not lost art.

### m3 — the shared anchor frame has a 15 px detached fleck

- Files: `run/frames_hi/frame_00.png` (second alpha component, 15 px at `(114,160)–(117,165)`), the same art in `slash2/frames_hi/frame_00.png` at `(178,224)–(181,229)` (640 canvas, +64 px offset) and in `shoot2/frames_hi/frame_00.png` at `(114,160)–(117,165)`; floating to the left of the hair tips.
- Defect: a small disconnected dark fragment in the transition start anchor. It merges into one component at 64, so it is a 512-only blemish, but it is in the anchor frame shared by three actions.

### m4 — 64 px eye has no resolvable pupil

- Files: all 40 64 px frames. Example `idle/frames/frame_00.png`: eye is 2 px, `(35,15)=#DBBCFF` and `(36,15)=#B78CE0`; no dark pupil pixel. The 512 idle f0 eye has a full violet iris plus an opaque dark pupil.
- Defect: if "violet eye … with an opaque pupil" is read literally at 64, this fails (the eye is present, opaque and violet, but the pupil is below the resolution). Also note the 64 eye is a *pale* lavender, close to the hair highlight.

### m5 — 64 px weapon readability

- Files: all 64 frames; examples `idle/frames/frame_00.png` hip `(30,30)–(40,42)`, `shoot2/frames/frame_06.png` gun `(44,25)–(62,34)`, `roll/frames/frame_02.png` hip `(22,26)–(32,38)`.
- Defect: at 64 the holstered pistol is a grey blob with a cyan strap (no readable pistol silhouette), and the pistol in hand is a horizontal bar with a cyan dash. The 512 art reads correctly (grip, slide, guard, muzzle). Not a crop or a missing part — a readability/commercial-quality note at the game resolution.

### m6 — review-packet truth sheets are mirrored and do not match the shipped pose language

- Files: all `12_*_3d_truth_all.png`.
- Defect: the mannequin faces **left** (nose/eyes and boot toes to the left) while every shipped frame faces **right**; the shoot2 truth is a standing lunge while the shipped shoot2 is a deep kneel. The sheets also use a solid magenta background instead of transparency. They are therefore unusable for validating pose/direction and cannot serve as the "truth" the manifest claims. Packet/tooling issue, not shipped art.

---

## CHECKS THAT PASS (measured)

### Frame counts and uniqueness

- 8/8 unique frames per action at 512 and 64 (`sha256`): idle, run, slash2, shoot2, roll — 40 unique 64 frames, 40 unique hi frames. No duplicated frame in any cycle.

### Transitions (64 px anchors)

Verified byte-for-byte equal, and equal to the `MANIFEST.md` hashes:

| pair | result |
|---|---|
| `run/f0` vs `slash2/f0` | identical (sha `d38482cc40126e3c…`) |
| `run/f7` vs `slash2/f7` | identical (sha `9dc9fd7afbbedd3e…`) |
| `run/f0` vs `shoot2/f0` | identical |
| `run/f7` vs `shoot2/f7` | identical |
| `idle/f0` vs `roll/f0` | identical (`e7a0e0a8459a08a5…`) |
| `idle/f7` vs `roll/f7` | identical (`fe47d7f507749aea…`) |

At hi-res, shoot2 and roll anchors are pixel-identical to their run/idle counterparts; slash2 hi-res is 640x640 by design and is **not** pixel-identical to the 512 run anchor (canvas re-render), which matches the spec (only the 64 anchors must match).

### Run cycle

- 8 unique poses; pairwise silhouette IoU 0.44–0.82, no duplicate pose, legs alternate across the cycle.
- Vertical bounce present: head/hair top 84→79→90→98→103→98→94→103 px (512), i.e. 24 px = 3 px at 64; feet stay on the ground line (61–62 at 64), so the bounce reads as a body bob/crouch, not a flight phase (acceptable, but the run is more of a power-run than an airborne sprint).
- Loop wrap f7→f0 is a normal stride transition (no reversal/duplicate).

### Roll

- f0 = idle f0, f7 = idle f7 (pixel-identical); f1–f6 are a coherent forward somersault, sky/ground orientation flips correctly (f2/f3 inverted, f4 curled, f5/f6 recovery).
- No pistol or katana in hand in any roll frame; the sheathed katana (hilt + scabbard) and the holstered pistol stay on the body. In f1/f3 the hilt and the far end of the scabbard are the two visible ends of that one stowed weapon, the middle being hidden by the body; no separate loose weapon is present. (Note: in f3 the hilt axis and the visible scabbard axis are visibly kinked rather than one straight line — a geometry blemish on a hi-res inverted frame, below the 64 read limit, not a second weapon.)
- No detached weapon component or neighbour fragment: exactly one alpha component in all eight 512 roll frames (f0 is the idle anchor and is also one component); the 15 px hair fleck (m3) does not occur in roll.

### Weapons

- Katana drawn only in slash2 f1–f6; stowed (hilt + scabbard across the lower back) in idle, run, shoot2 and roll.
- Pistol in hand only in shoot2 f1–f6; holstered at the hip in idle, run, slash2 and roll.
- Exactly one pistol visible in shoot2 (no second gun); exactly one katana scabbard visible in shoot2/roll/idle/run.
- Hand–hilt attachment in slash2 f1/f2/f3/f5/f6 and the hand–gun attachment in shoot2 are correct (guard below the fist, fingers over the grip, no blade/gun floating away from the hand).

### Completeness / alpha

- Alpha is binary in all 80 frames (0/255 only; 0 semi-transparent px) — no halos or anti-aliased fringe.
- No border contact in any 512/640 frame (all four edges, all 40 hi frames): 0 px.
- 64 border contact only at M1 (slash2 f4) and m2 (roll f1/f5); no head, hand or boot touches a border anywhere else.
- No isolated transparent pinholes: the enclosed transparent regions are legitimate negative space between limb and torso (e.g. idle f0 305 px between forearm and hip; slash2 f5 2 375 px between the sword arm and torso; the 64 armpit gaps of 5–27 px are continuous gaps, not punched holes).

### Character identity

- Long silver hair in all frames; short-sleeve crop top, detached forearm sleeves with cyan trim on both arms, shorts, boots — consistent in 512 and 64.
- Violet eye present at 512 with an opaque dark pupil (idle f0 iris `#DBBCFF/#B78CE0`, pupil `#08080C`); violet eye pixel present at 64 in every action including the inverted roll f2/f3 (`roll/f2` 64 violet at `(49,27)`, `(53,22)`), though with no resolvable pupil (m4).
- The 512 face/eye is not punched through (no transparent pupil).

### Slash2 body size

- All six slash frames f1–f6 are one component, 512 bbox height 412–417 px and 64 body height 51–52 px (head/hair top 151–156 in 512, boots 567; the 5 px spread is hair tilt, not scale); no frame is scaled. f0 (420/53) and f7 (401/50) inherit the run anchor crouch by design — a 1–3 px bob at 64, not a scale change. No shrunken/oversized slash frame in this build.

### Motion / completeness notes

- No missing limb: both arms and both legs are present in every 512 frame; where one arm/leg is hidden in shoot2 and roll it is occluded by the torso/other leg (consistent silhouette at 64). No frame is missing a hand, foot, or the head.
- Weapon change f0→f1 and f6→f7 (`slash2`, `shoot2`) is the spec-mandated anchor: the weapon goes from stowed to hand in one frame. This is accepted as a spec constraint, but it pops when the action is played standalone (same note as v9); the *unintended* pops are M2 (second hilt on the back) and M3 (holster vanishes with the pistol).

---

## Requirement checklist

| Requirement | Result |
|---|---|
| Cyberpunk woman: long silver hair, violet eyes (opaque pupil), short-sleeve top, detached sleeves, shorts, boots | PASS at 512; 64 eye is iris-only (m4) |
| Katana across the lower back when unused | PASS (idle/run/shoot2/roll) |
| Pistol at the right hip with a readable pistol shape | PASS at 512; at 64 not readable (m5) |
| Katana drawn ONLY in slash2 | PASS (f1–f6) |
| Pistol in hand ONLY in shoot2 | PASS (f1–f6); no gun in hand in roll/slash2/idle/run |
| Exactly ONE katana/scabbard/pistol; no second hilt/blade/gun | **FAIL (M2)** |
| Empty holster visible and consistent in shoot2 | **FAIL (M3)** |
| No violet fleck inside the gun | **FAIL (m1, 1 px)** |
| idle 8 unique | Count PASS; content **FAIL (B1)** |
| run 8-frame self-loop, alternating legs, vertical bounce | PASS (8 unique, bounce 3 px at 64) |
| slash2 8 frames; body same height, no shrunken/oversized | Count/scale PASS (51–52 px f1–f6); blade **FAIL (M1)** |
| shoot2 8 frames | Count PASS; holster **FAIL (M3)** |
| roll 8 frames | PASS; 64 border touch (m2) |
| Transitions: slash2/shoot2 start = run f0, end = run f7 (64 identical) | PASS (six pairs byte-identical) |
| roll = idle f0/f7 | PASS (byte-identical) |
| Every frame complete: no cropped head/hair/hand/boot/blade at the edge | **FAIL (M1, m2)** |
| No missing limb | PASS |
| No transparent pinholes | PASS (no isolated holes; enclosed regions are limb negative space) |
| No neighbour fragments / duplicate parts | **FAIL (B1; m3)** |
| Violet eye at 512 and 64 (incl. inverted roll), opaque pupil | PASS at 512; 64 eye PASS, pupil **FAIL-if-literal (m4)** |
| Slash2 64 body height equal in all frames | PASS for f1–f6 (51–52); f0/f7 inherit the run bob (53/50), not scaling |
| Readable silhouettes at 64 | Body PASS; hip pistol / in-hand gun **m5** |
| Coherent motion | **FAIL (B1)**; run/slash/shoot/roll coherent |
| No weapon teleport/popping | **FAIL (M2, M3)**; anchor draw/sheath accepted by spec |
| Roll: no slabs/floating weapons, no pistol/katana in hand | PASS (one stowed weapon + holstered pistol; f3 hilt-axis kink noted, hi-res only) |

---

## Frames opened

Packet (all 24 PNGs): `00_design_sheet`, `01_char_ref_64_x16`, `02_part_katana`, `02_part_scabbard`, `02_part_pistol`, `10_idle_hi_all`, `11_idle_64px_all`, `12_idle_3d_truth_all`, `10_run_hi_all`, `11_run_64px_all`, `12_run_3d_truth_all`, `10_slash2_hi_all`, `11_slash2_64px_all`, `12_slash2_3d_truth_all`, `10_shoot2_hi_all`, `11_shoot2_64px_all`, `12_shoot2_3d_truth_all`, `10_roll_hi_all`, `11_roll_64px_all`, `12_roll_3d_truth_all`, `20_cross_action`, `21_transition_pairs`, `23_transition_diff`, `22_run_loop`.

Shipped frames (80): `idle`, `run`, `slash2`, `shoot2`, `roll` × `frames/frame_00..07.png` and `frames_hi/frame_00..07.png`; plus `parts/katana.png`, `parts/scabbard.png`, `parts/pistol.png`, `design_sheet.png`, `char_ref_64_x16.png`.

Targeted crops opened at 4–28x: idle f0/f1/f2/f3/f5 head and hip; run f0 hair fleck and f4/f5 hip; slash2 f1/f2/f3/f4/f5/f6 hand, waist, back and 64 f4 edge; shoot2 f2/f4/f6/f7 pelvis and gun, 64 f2/f6 gun; roll f1/f2/f3/f4/f5 hip, weapons and 64 f1/f2/f5 head/edge; 64 eyes in all actions.

---

## Fix list (in order)

1. `idle` f2/f3/f4: render the missing 3 idle frames at the same character scale as f0/f1/f5–f7 (512 body 420 px, 64 53 px, feet on y=503/62) and remove the detached duplicate head. Re-run the connected-component check on every frame (must be exactly 1 component, and for slash2 the component must not touch the crop window edge).
2. `slash2` 64 f4: widen/shift the 64 crop window (or re-pose) so the blade tip keeps ≥2 px margin; the 640 source is complete, only the crop is wrong.
3. `slash2` 512/64 f2: hide the stowed hilt in all slash2 frames (keep the empty scabbard only) so exactly one katana is visible.
4. `shoot2` f1–f6: keep the empty drop-leg holster (body + strap + buckle) at the hip while the pistol is in the hand; do not move the holster with the pistol.
5. `shoot2` f6: replace the `#DBBCFF` pixel at (451,236)/(56,29) with gun grey or skin; run a palette check on the gun mask.
6. `roll` 64 f1/f5: add ≥1 px of right margin for the hair (re-crop or shorten the hair tip by 1 px).
7. `run/slash2/shoot2` f0: weld or delete the 15 px hair fleck at `(114,160)–(117,165)` in the shared anchor.
8. 64 px eye: if a pupil is required, paint one dark pixel into the eye (the current 2 px eye is iris-only).
9. Packet: rebuild the `12_*` truth sheets unmirrored, transparent, and from the same pose as the art; otherwise remove the "truth" claim from `MANIFEST.md`.
