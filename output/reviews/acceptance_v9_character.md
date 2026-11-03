# Character acceptance review v9 — agent sprite pack

**VERDICT: FAIL**

- Reviewer: independent; did not build these assets. No asset was modified. This report is the only file written under `output/`.
- Target per the task: the 16:31 review packet `/dat/projects/artist2d/work/review/character/` (all 23 manifest PNGs + the unlisted `01_char_ref_64_x16.png`, plus `MANIFEST.md`).
- Shipped frames cross-checked: `/dat/projects/artist2d/output/character/agent/<action>/frames_hi/frame_00..07.png` (512, slash2 640) and `<action>/frames/frame_00..07.png` (64).
- Method: every packet image and every current frame opened as an image; pixel/alpha/connected-component/hole/eye/border measurements on all 40 512 frames and all 40 64 frames; per-frame crops for face, hip, hilt, blade and gun.

## Snapshot warning — the pack is not frozen

The 16:31 packet is not the current state. The pack was rebuilt under the reviewer twice:

| time | event |
|---|---|
| 16:24–16:31 | review packet generated (the packet this report was asked to review) |
| 16:45–16:54 | rebuild #1 (`build_character.py --character agent --actions idle,run,slash2,shoot2,roll --keep-reference --force`, PID 25014); 176 PNGs rewritten, `build_report.json` 16:54:28 |
| 16:58–17:02+ | rebuild #2 (PID 30905) started; idle/run re-written at 16:59–17:01, slash2 raws 17:02; **still running at report time** |

Consequences:

- The 16:31 packet no longer describes the shipped frames. The packet's `MANIFEST.md` transition hashes (`7caa…`, `5f2d…`, `c8a0…`, `86d9…`) are for the pre-rebuild art; the 16:54 build's anchors are `3156…`, `a839…`, `5a23…`, `9406…`; by 17:01 the run/idle anchors had changed again (`c25b…`, `e9cd…`, `06a0…`, `56a1…`) while slash2/shoot2/roll were still on the 16:54 values — i.e. at 17:01 the 64 transition anchors were **not** pixel-identical.
- The packet's design sheet, parts, `12_*` 3D truth sheets, `20/21/22/23` proofs and `build_report.json` are all from the old art.
- **This alone is a delivery blocker** (same failure class as v5): a commercial pack cannot be accepted while it is regenerated under the reviewer.

**Live delta at 17:04 (snapshot C, build still running).** The 16:58 build has already rewritten `slash2/frames_hi/frame_03.png`/`frame_04.png` and `slash2/frames/frame_03.png`/`frame_04.png` (17:03). The detached head and the 0.8× body scale seen in snapshot B are gone at f3/f4: both are now one alpha component (f3 640 bbox `143,92–513,567`; f4 `133,148–634,567`; 64 f3 `10,3–55,62`, f4 `8,10–63,62`; body ~52 px). However, the 64 `slash2/frames/frame_04.png` bbox is `8,10–63,62` — it **touches the right edge at x=63** while the 640 blade tip is at `x=634` (5 px margin), so the 64 crop cuts the blade again, now in f4 instead of f3. The blade-edge blocker (A1) is therefore not resolved by the 16:58 build; it moved frames. Snapshot C remains unaccepted until the build freezes.

The report therefore records:

- **Snapshot A** — the 16:31 packet (what the task named as current). Defects below marked A are real in that packet but were partly fixed in the 16:54 build; do not blindly re-fix them without checking the final build.
- **Snapshot B** — the 16:45–16:54 build (the first frozen rebuild after the packet). Defects marked B were reproduced on the actual shipped frames.
- **Snapshot C** — the 16:58+ rebuild. Not assessed: it was mid-build at report time (`slash2/raw_*` still being written at 17:02). Any acceptance must be re-run on the frozen output of the final build.

The FAIL verdict holds for the packet (A) and for the 16:54 build (B). No PASS is possible for a moving target.

---

## BLOCKERS

### PB1 — Pack is being rebuilt during acceptance; packet and shipped output disagree (process, all actions)

- Files: `work/review/character/*` (16:31); `output/character/agent/**` (rewritten 16:45–16:54, again 16:58+); `output/character/agent/build_report.json` (16:54:28, stale already); `output/character/agent/transitions.json`.
- Defect: two `--force` rebuilds ran while this review was open. The 16:31 packet's frames are not the 16:54 frames, and the 16:58 rebuild is overwriting idle/run/slash2 again. At 17:01 the 64 anchors were split across builds: `run/frames/frame_00.png` = `c25b58…`, `slash2/frames/frame_00.png` = `315607…`, `shoot2/frames/frame_00.png` = `315607…`; `run/frames/frame_07.png` = `e9cd35…`, slash2/shoot2 f7 = `a83957…`. This is not a valid transition state.
- Requirement: the packet's own promise that its images are review copies of shipped assets; "transitions start = run f0 / end = run f7 (the 64 anchors are pixel-identical)"; a commercial pack cannot be reviewed while regenerating.
- Fix: freeze the build; regenerate the packet, `MANIFEST.md`, `build_report.json`, `transitions.json` and all proof sheets from that one build; then re-run acceptance.

### A1 — Slash2 64 f3 blade is cut flat at the right frame edge (packet A)

- Files: `output/character/agent/slash2/frames/frame_03.png` (64); evidence `work/review/character/11_slash2_64px_all.png` f3.
- Defect: alpha at `x=63`, rows 24–26; the blade ends in a flat vertical cut at the border. The 640 hi-res (`slash2/frames_hi/frame_03.png`) has its tip at `x=633` (6 px from the 640 edge), but the 64 game frame is a crop of the 512 body window, so roughly the last 7 game px (≈57 hi-res px, nearly half the blade beyond the fist) are lost. The blade reads as a short stub ending at the frame edge.
- Requirement: every frame complete — no cropped blade at the edge; readable at 64.
- Status: fixed in snapshot B (B's slash2 f3 64 bbox `13,11–55,62`, 8 px margin; 640 bbox `165,156–507,489`, no edge contact). **Regressed in snapshot C:** `slash2/frames/frame_04.png` is `8,10–63,62` (right edge x=63; 640 tip x=634), so the 64 crop cuts the blade at the edge again in f4. Re-verify after the build freezes; the frame that clips has changed.

### A2 — Shoot2 f1–f6: the empty holster is completely absent (packet A)

- Files: `output/character/agent/shoot2/frames/frame_01..06.png` and `frames_hi/frame_01..06.png`; evidence `10_shoot2_hi_all.png`, `11_shoot2_64px_all.png`.
- Defect: f0/f7 (run anchors) show the pistol in a drop-leg holster on the right thigh with two horizontal straps. In f1–f6 the pistol is in the extended right hand and both the holster body and both thigh straps are gone — the right hip/thigh is bare shorts/skin. No empty holster anywhere in the action.
- Requirement: empty holster stays visible and consistent in shoot2; exactly one pistol; stowed weapons consistent.
- Status: fixed in snapshot B (the new shoot2 f1–f6 show an empty drop-leg holster at the right thigh while the pistol is in the hand). Must be re-verified in snapshot C.

### B1 — Slash2 512/640 f3 and f4 contain a detached duplicate head at the bottom of the frame (snapshot B)

- Files: `output/character/agent/slash2/frames_hi/frame_03.png`, `frame_04.png` (640); `slash2/frames/frame_03.png`, `frame_04.png` (64).
- Defect: each of these frames has **two alpha components**: the character, and a second copy of the head (hair + face + violet eye) floating below the feet at `(248,508)–(417,567)` (f3, 4 542 px) and `(239,508)–(407,567)` (f4, 4 481 px) in the 640 canvas. In the 64 frames the fragment is `(23,55)–(44,62)` (83 px) and `(22,55)–(42,62)` (77 px), i.e. a recognizable miniature head sitting at the bottom of the game frame (1 px above the bottom edge). The body itself ends at `y=489` (640) / `y=53` (64).
- This is not the character's head: the body already has its own head at the top. The frame shows a second head, reads as a neighbour fragment, and is a compositing/head-decal bug.
- Requirement: every frame complete; no neighbour fragments; no duplicate head/hilt/blade; no cropped/extra body parts.
- Fix: remove the second head component; find the head-decal/composite offset that places the head at the bottom of the 640/64 canvas in f3/f4 only, and pin it to the body head. Re-check every slash2 frame for a second component.

### B2 — Slash2 512/640 f3 and f4 collapse the character scale by ~20% (snapshot B)

- Files: `slash2/frames_hi/frame_03.png`, `frame_04.png`; `slash2/frames/frame_03.png`, `frame_04.png`.
- Defect (body component only, excluding the detached head):
  - 640 body bbox f0 `157,148–477,567` (420 px tall), f1 body top 113 is the overhead blade, f2 `145,156–471,567` (412), f5 `150,156–436,567` (412), f6 `156,156–476,567` (412), f7 `157,148–475,567` (420).
  - f3 body `165,156–507,489` = **334 px**; f4 body `169,156–445,489` = **334 px**. That is 0.80× the 420 px body.
  - 64 body: f0/f7 53 px, f2/f5/f6 52 px; f3/f4 **43 px** (the 64 bbox reports 52 px only because the detached head at `y=55–62` inflates it).
  - The shrunken body is visible in the packet-style sheet: f3/f4 characters sit higher and smaller than the neighbouring frames, with the floating head below.
- Requirement: every slash2 64 frame body has the same height; no single shrunken/oversized frame; cross-frame/action body size.
- Fix: re-render/re-pose f3/f4 at the same character scale as f0/f2/f5/f6 (body head-to-boot 52–53 px at 64; ~412–420 px at 640) and remove the detached head (B1). The 64 bbox check must exclude the head fragment, or the fragment will keep hiding the shrink.

---

## MAJORS

### M1 — 512 run f7 / slash2 f7 / shoot2 f7: 14 px detached fragment at the waist (snapshot B)

- Files: `output/character/agent/run/frames_hi/frame_07.png`; `slash2/frames_hi/frame_07.png`; `shoot2/frames_hi/frame_07.png` (the two attacks copy the run f7 anchor).
- Defect: a second alpha component, 14 px at `(393,246)–(397,248)` (5 × 3), floating near the right hip/hilt, disconnected from the body. The 64 f7 frames merge it into the hilt (one component), so it is a 512/underlying-anchor defect, but the f7 is the transition end anchor and the 512 art is shipped.
- Requirement: every frame complete; no neighbour fragments; no second hilt/blade; anchors clean.
- Fix: weld the fragment back to the hilt/hand or remove it; re-check the anchors after the rebuild.

### M2 — Drawn katana blade is a solid cyan energy blade, not the gray katana of the part/design sheet (snapshot B)

- Files: `slash2/frames_hi/frame_01..06.png` and `slash2/frames/frame_01..06.png`; compare `02_part_katana.png`, `00_design_sheet.png`, `char_ref_stowed_512.png`.
- Defect: the drawn blade is a saturated cyan ramp (`#63cbd8` / `#35a2c4` with a white core) in every drawn frame; the part katana and the design sheet blade are gray metal (`#9b9bb0`/`#d6d6e6` with a thin cyan edge). The stowed scabbard is dark; the drawn weapon no longer matches the weapon it is supposed to be. At 64 it reads as an energy sword; at 512 it is a different material from the part sheet.
- Requirement: katana consistent with the design/part; stowed and drawn states are the same weapon; coherent identity; commercial consistency.
- Fix: either restore the gray blade with its cyan edge, or, if the cyan blade is an intentional VFX, update `02_part_katana.png` and the design sheet to match and document the energy edge. Do not ship a part sheet that contradicts every drawn frame.
- Note: the cyan blade *is* highly readable at 64; the old v5 "1 px dotted blade" problem is fixed. The remaining issue is material/design consistency, not readability.

### M3 — Roll (snapshot A only): stowed katana composited over the body/hair; 64 f5 loses the violet eye

- Files (A): `roll/frames_hi/frame_02.png`, `frame_04.png`, `frame_05.png`; `roll/frames/frame_05.png`; evidence `10_roll_hi_all.png`, `11_roll_64px_all.png`.
- Defect A: in the 16:31 packet the scabbard/hilt is drawn in front of the torso/hair: f2 the hilt/guard sits at the head and the scabbard crosses the torso; f4 the scabbard crosses the shorts/thigh with the hilt at the neck; f5 the hilt crosses the hair/cheek. At 64 it becomes a black bar across the figure. In `roll/frames/frame_05.png` (64) the face has **no violet pixel at all** (face x≈32–42, y≈39–47; the only violet pixels in the frame are hair/boot highlights at (26–27,36–37), (17,41), (20,62)); the 512 f5 has the full iris+pupil at (293–295,322–325). 64 f1–f4 reduce the eye to a single 1 px lavender pixel (f1 (50,41) `#dbbcff`; f2 (34,56) `#dbbcff`; f3 (20,50) `#b78ce0`; f4 (26,39) `#b78ce0`).
- Requirement A: roll has no slabs/floating weapons; violet eye intact at 64 including the inverted roll frames; coherent layering.
- Status: **fixed in snapshot B**. The 16:54 roll draws the scabbard behind the body/hair in f2–f6; `roll/frames/frame_05.png` (64) has violet at (23,47)–(24,49) and the 512 f5 eye is intact; the sword is not in hand. Re-verify in snapshot C.

---

## MINORS

1. **64 px eye loses the opaque pupil in all actions (A and B).** Example `idle/frames/frame_00.png`: eye at (34–35,15–16) is `#dbbcff`/`#9169c4` (2 px violet + highlight), with no `#241838` pupil; the 512 idle f0 eye has a painted dark pupil. The v5 transparent-eye hole is fixed; the remaining issue is pupil resolution at 64. The old roll f5 eye loss is fixed in B.
2. **1–3 px enclosed transparent pinholes at 64 (A and B).** Per-frame counts at 64 are 0–5 (run/idle 0–2; slash2/shoot2 1–5; roll 0–5). Examples: `run/frames/frame_00.png` at (25,29); `slash2/frames/frame_01.png` at (20,24)/(27,27); `shoot2/frames/frame_04.png` at (28,26); `roll/frames/frame_01.png` at (35,28). The larger enclosed regions are legitimate negative space (hand/guard, knee/calf, blade/hair); the single-pixel ones are downscale pinholes. Fill the 1 px holes.
3. **Roll 64 f2/f3/f4 readability (A and B).** The tumbling head/hair/torso/limbs compress into a dark mass at 64; the 512 roll is readable, the 64 is marginal. The eye is present in B. Clean the silhouette/contrast in the inverted frames.
4. **Packet/manifest/design/parts are stale (A and B).** `MANIFEST.md` lists the 16:31 SHAs and 24 files; `01_char_ref_64_x16.png` is present but unlisted and shows a different concept (front 3/4, drawn katana, bright cyan/purple). `00_design_sheet.png`/`02_part_*` show the pre-rebuild art (solid top, gray blade), while the 16:54 frames have a keyhole-cutout top and a cyan blade. `12_*` are the old crude box mannequins (the user is replacing them). `20_cross_action.png` shows the five f0 anchors only — three identical run panels + two identical idle panels — so it cannot demonstrate cross-action body size; use a mid-action frame per action.
5. **64 shoot2 far boot is 1 px from the right edge in f2–f6.** `shoot2/frames/frame_02..06.png` bbox `x1=62`; the boot is complete (1 px margin) but there is no room for any aim/recoil drift. 512 has 10 px. This is a tight-margin note, not a crop.
6. **Anchor-mandated weapon snap (A and B, spec tension).** `slash2` f0→f1 and f6→f7, `shoot2` f0→f1 and f6→f7 change the weapon from stowed to hand in one frame with no draw/holster motion; the 64 anchors are required and pass, but the action played standalone pops. If this is shipped, mask with a draw/stow transition or accept the spec's constraint explicitly.
7. **512 hi-res anchors are separate renders.** Only the 64 anchors are pixel-identical; the 512/640 f0/f7 of slash2/shoot2/roll are not byte-identical to the run/idle hi-res. If the engine transitions on the 512 art, the seams are not guaranteed. The packet's `21/23` proofs are 64 only.

---

## Measurements

### Snapshot A (16:31 packet) — 64 px

| action | bbox height f0..f7 | top min | bottom min | left min | right min | border contact |
|---|---|---|---|---|---|---|
| idle | 53,53,53,53,53,53,53,53 | 10 | 1 | 18 | 18 | none |
| run | 53,57,54,52,53,58,54,51 | 5 | 1 | 11 | 9 | none |
| slash2 | 53,55,52,52,53,52,52,51 | 8 | 1 | 8 | **0 (f3)** | **f3 right x=63, rows 24–26** |
| shoot2 | 53,53,53,51,52,53,53,51 | 10 | 1 | 10 | 1 | none (f2/f3 gun 1 px) |
| roll | 53,42,47,45,30,31,43,53 | 10 | 1 | 17 | 8 | none |

- Slash2 body scale: head-hair top 8–12, boot bottom 62, face-to-boot 42–45, head mass 22–25 px wide in all eight frames → no shrunken/oversized body in A. The 51–55 bbox range is the run bounce and f1's overhead blade, not a scale change.
- 512/640 margins: min right 6 px (`slash2/frames_hi/frame_03.png` tip x=633 of 640); every other frame ≥8 px. No 512 crop contact.
- Transitions at 16:33: all six 64 anchors SHA-identical (`7caa…`/`5f2d…`/`c8a0…`/`86d9…`); `23_transition_diff.png` all black.
- 8/8 unique frames per action at 64 and 512; single alpha component in all 40 frames (A).

### Snapshot B (16:45–16:54 build) — body components

| slash2 640 frame | body component bbox | body height | second component |
|---|---|---|---|
| f0 | (157,148)–(477,567) | 420 | — |
| f1 | (167,113)–(480,567) | 455 incl. overhead blade | — |
| f2 | (145,156)–(471,567) | 412 | — |
| f3 | (165,156)–(507,489) | **334** | **4 542 px head (248,508)–(417,567)** |
| f4 | (169,156)–(445,489) | **334** | **4 481 px head (239,508)–(407,567)** |
| f5 | (150,156)–(436,567) | 412 | — |
| f6 | (156,156)–(476,567) | 412 | — |
| f7 | (157,148)–(475,567) | 420 | 14 px fragment (393,246)–(397,248) |

| slash2 64 frame | body bbox | body height | second component |
|---|---|---|---|
| f0 | (11,10)–(51,62) | 53 | — |
| f1 | (13,6)–(51,62) | 57 incl. overhead blade | — |
| f2 | (10,11)–(50,62) | 52 | — |
| f3 | (13,11)–(55,53) | **43** | **head 83 px (23,55)–(44,62)** |
| f4 | (13,11)–(47,53) | **43** | **head 77 px (22,55)–(42,62)** |
| f5 | (10,11)–(46,62) | 52 | — |
| f6 | (11,11)–(51,62) | 52 | — |
| f7 | (11,10)–(51,62) | 53 | — (512 f7 fragment merges at 64) |

- 16:54 64 anchors: all six pixel-identical at 16:54 (`slash2/shoot2` start `315607…`, end `a83957…`; `roll` start `5a2383…`, end `9406d1…`). They are broken again by the 16:58 rebuild (PB1).
- 16:54 border contact: none at 64 or 512/640. Closest: `shoot2/frames/frame_02..06.png` right `x1=62` (1 px, complete); `slash2/frames/frame_03.png` right `x1=55` (8 px); `slash2/frames_hi/frame_03.png` right `x=507` of 640.
- 16:54 slash2 blade: complete, no edge contact; the 64 blade is a readable cyan line with a hilt/guard.
- 16:54 empty holster: present in `shoot2/frames/frame_01..06.png` and `frames_hi/frame_01..06.png` at the right thigh, gun absent (in hand).
- 16:54 roll: sword behind the body/hair in f2–f6; 64 f5 eye violet at (23,47)–(24,49); no weapon in hand.
- 16:54 8/8 unique per action at 64 and 512.

---

## Requirement checklist

| requirement | A (16:31 packet) | B (16:54 build) |
|---|---|---|
| cyberpunk woman: long silver hair, violet eyes (opaque pupil), short-sleeve top, detached sleeves, shorts, boots | PASS at 512; 64 pupil minor | PASS at 512; 64 pupil minor |
| katana stowed across lower back when unused | PASS | PASS |
| pistol at right hip, readable shape | PASS at 512; 64 small | PASS at 512; 64 small |
| katana drawn ONLY in slash2 | PASS | PASS |
| pistol in hand ONLY in shoot2 | PASS | PASS |
| exactly one katana/scabbard/pistol; no second hilt/blade/gun | PASS | PASS (the f7 14 px fragment is not a second weapon but is a fragment) |
| empty holster visible and consistent in shoot2 | **FAIL (A2)** | PASS |
| idle 8 unique frames | PASS | PASS |
| run 8-frame self-loop, alternating legs, vertical bounce | PASS (512 bounce 9 px, 64 1 px) | PASS (512 9 px, 64 1 px) |
| slash2 8 frames | PASS count; **FAIL A1 (f3 crop)** | PASS count; **FAIL B1/B2 (f3/f4 head + scale)** |
| shoot2 8 frames | PASS count; **FAIL A2 (holster)** | PASS count; PASS holster |
| roll 8 frames | PASS count; **FAIL M3 (eye/layer)** | PASS count; PASS eye/layer |
| slash2/shoot2 start = run f0, end = run f7, 64 anchors identical | PASS at 16:33 | PASS at 16:54; broken at 17:01 by rebuild |
| roll start/end = idle f0/f7 | PASS at 16:33 | PASS at 16:54; broken at 17:01 by rebuild |
| every frame complete: no cropped head/hair/hand/boot/blade | **FAIL A1** (slash2 f3) | **FAIL B1** (slash2 f3/f4 duplicate head); no edge crop |
| no missing limb | PASS | PASS |
| no transparent pinholes | PASS 512; minor 64 | PASS 512; minor 64 |
| no neighbour fragments | PASS | **FAIL B1 (head), M1 (f7 512 14 px)** |
| violet eye intact at 512 | PASS (painted pupil; v5 hole fixed) | PASS (painted pupil) |
| violet eye intact at 64, incl. inverted roll frames | **FAIL M3 (roll f5 no eye; f1–f4 1 px)** | PASS on presence (roll f5 violet present); pupil still absent |
| every slash2 64 body same height; no shrunken frame | PASS (51–55 bbox, scale constant) | **FAIL B2 (f3/f4 body 43 vs 52)** |
| readable silhouettes at 64, coherent motion | PASS except roll 64; M3 layering | PASS except slash2 f3/f4 (broken) and roll 64 readability (minor) |
| no weapon teleport/popping | FAIL M3 (roll layer); anchor snaps note | PASS within actions; anchor snaps note |
| roll no slabs/floating weapons, no pistol/katana in hand | **FAIL M3** | PASS (sword behind body, no weapon in hand) |
| commercial quality | FAIL (A1/A2/M3) | FAIL (B1/B2/M2) |

---

## Frames actually opened

Packet (`work/review/character/`): `00_design_sheet.png`, `01_char_ref_64_x16.png` (unlisted), `02_part_katana.png`, `02_part_scabbard.png`, `02_part_pistol.png`, `10_idle_hi_all.png`, `11_idle_64px_all.png`, `12_idle_3d_truth_all.png`, `10_run_hi_all.png`, `11_run_64px_all.png`, `12_run_3d_truth_all.png`, `10_slash2_hi_all.png`, `11_slash2_64px_all.png`, `12_slash2_3d_truth_all.png`, `10_shoot2_hi_all.png`, `11_shoot2_64px_all.png`, `12_shoot2_3d_truth_all.png`, `10_roll_hi_all.png`, `11_roll_64px_all.png`, `12_roll_3d_truth_all.png`, `20_cross_action.png`, `21_transition_pairs.png`, `22_run_loop.png`, `23_transition_diff.png`, `MANIFEST.md`.

Shipped frames opened individually (snapshot A and B): `idle/frames_hi/frame_00.png`; `run/frames_hi/frame_00.png`; `slash2/frames_hi/frame_03.png`, `frame_04.png`, `frame_05.png`, `frame_02.png`; `slash2/frames/frame_03.png`, `frame_04.png`; `shoot2/frames_hi/frame_01.png`, `frame_03.png`; `shoot2/frames/frame_01.png`, `frame_03.png`; `roll/frames_hi/frame_00..06.png` (0,1,2,3,4,5,6); `roll/frames/frame_05.png`; plus full-frame crops at 12–30× of the face/eye, hip/holster, hilt, gun and blade for every cited frame, and 8× contact sheets of all 8 frames of all five actions at both resolutions (snapshot B).

Not assessed: snapshot C (the 16:58+ rebuild) — it was still writing frames at report time.

---

## Conditions for a PASS

1. Freeze the pack. Regenerate `work/review/character/`, `MANIFEST.md`, `transitions.json`, `build_report.json`, `00_design_sheet.png`, `02_part_*` and `12_*` from one frozen build; re-run acceptance on that build. No PASS while the pack is regenerating.
2. Fix snapshot B B1/B2: slash2 f3/f4 must have one body at the same scale as f0/f2/f5/f6 (64 body 52–53 px; 640 body ~412–420 px) and no detached head. Re-check every 512/64 frame for a second alpha component.
3. Fix M1: weld/remove the 14 px fragment at (393,246)–(397,248) in run/slash2/shoot2 f7 (512); re-verify the anchors.
4. Resolve M2: restore the gray katana blade (with cyan edge) or update the part/design sheet to the cyan energy blade; the drawn and stowed weapon must be the same object visually.
5. Re-verify the snapshot A fixes on the frozen build: slash2 64 f3 **and f4** blade ≥1 px margin (snapshot C's f4 touches at x=63); shoot2 f1–f6 empty holster visible; roll 64 f5 eye present with a 2+ px violet iris and a dark pupil; roll sword behind the body/hair.
6. Fix/minor: 64 px pupil (at least 1 dark pixel), 64 px 1–3 px pinholes, roll 64 f2–f4 readability, 64 shoot2 far-boot 1 px margin, design/part/truth sheets aligned with the final art, `01_char_ref_64_x16.png` manifest/cleanup.
7. Re-run the 64 anchor SHA checks after the freeze; the packet's `7caa…`/`5f2d…` hashes are stale.

Only when blockers and majors are zero can this pack be accepted.
