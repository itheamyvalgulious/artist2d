# Character acceptance review v5 — agent sprite pack

**VERDICT: FAIL**

- Reviewer: independent (did not build these assets). No asset was modified; this report is the only file written.
- Packet reviewed: `/dat/projects/artist2d/work/review/character/` — all 24 PNGs + `MANIFEST.md` opened and read.
- Shipped frames cross-checked: `/dat/projects/artist2d/output/character/agent/<action>/frames_hi/frame_00..07.png` (512) and `<action>/frames/frame_00..07.png` (64).
- Method: every packet cell read visually (1:1 for 512, exact 8× for 64), then re-opened as individual PNGs for every frame cited; plus pixel/alpha/colour/component measurements on both the packet and the shipped frames.

## Snapshot warning — the pack is not frozen

The pack was rebuilt **five times during this review**:

| time | event |
|---|---|
| 11:54–11:56 | review packet generated |
| 12:11–12:16 | rebuild #1 (`build_character.py --actions idle,run,slash2,shoot2,roll --force`) |
| 12:20–12:26 | rebuild #2 (all five actions rewritten) |
| 12:28–12:36 | rebuild #3 (idle re-rendered, run 12:33, slash2/shoot2 12:36) |
| 12:36–12:45 | further rewrites while this report was being written |

Consequences:

- The 11:54 packet is **stale**. It shows art that is no longer shipped (e.g. the packet's idle head is a flat two-tone face with a slit eye; the current idle has the new face with a violet iris). Any check made only against the packet is invalid.
- Art direction changed between builds (head/face redesigned, art scale changed, weapon props redrawn), so findings drift frame by frame.
- The checks below were re-run on the **12:41 state** (file mtimes 12:28–12:36). Frame-level coordinates are from that state; the defect classes were confirmed on those files. If the pack is rebuilt again, this report is stale again.

**This alone is a delivery blocker**: a commercial pack cannot be accepted while it is being regenerated under the reviewer.

---

## BLOCKERS (4)

### B1 — The eye pupil is a transparent hole in the alpha channel

Files: every `frames_hi/frame_00..07.png` (all five actions); every 64 px frame inherits it.

- The eye is drawn as a dark ring and a violet iris around a **rectangular hole in the alpha**. Rendering `idle/frames_hi/frame_00.png` and `run/frames_hi/frame_00.png` on magenta shows a clean rectangular block of background punched through the middle of each eye (4 × 6 px in idle, 6 × 8 px in run).
- Measured enclosed transparent regions at the eye (flood-fill from outside; all 40 frames have one):

| frame | hole bbox | area |
|---|---|---|
| `run/frames_hi/frame_00.png` | (369,141)–(375,149) | 54 px |
| `idle/frames_hi/frame_00.png` | (289,124)–(293,130) | 33 px |
| `slash2/frames_hi/frame_01.png` | (308,187)–(318,194) | 65 px |
| `shoot2/frames_hi/frame_02.png` | (325,155)–(329,162) | 36 px |

- On the pack's own dark background this reads as a black pupil, which is why it survives casual review. In any game composite over a lighter tile, the pupil becomes the tile colour.
- This is the one feature the brief calls out twice (“violet eyes”, “violet eye intact at 512 AND 64”), and it is the one feature that is not actually painted.

Broken requirement: “no transparent pinholes”, “Violet eye intact at 512 AND 64”, “Every frame complete”.

### B2 — Slash2 f4 collapses the character's scale (the sword ends up longer than she is tall)

Files: `slash2/frames_hi/frame_04.png` (and `slash2/frames/frame_04.png`), compared with `frame_01`/`frame_05`.

- Character height (top of hair to sole) per frame: f1 = 420 px, f3 = 304 px, **f4 = 237 px**, f5 = 377 px, f6 = 420 px.
- In f4 the head is ~40 px against ~60 px in f1 (≈ 0.65×), while the katana in the same frame spans ≈ 400 px — **longer than the character is tall**. In f1 the same katana is ≈ 250 px.
- The result reads as a small figure holding an oversized sword: an unmistakable scale pop in the middle of the action, and a broken weapon/character proportion.

Broken requirement: “Consistent identity/scale”, “no popping”, check 2; the weapon must stay one fixed size.

### B3 — Weapons are not readable at 64 px

Files:
- `slash2/frames/frame_01,02,04,05,06.png` — the katana is a **1 px dotted pale line** (the 512 blade is 5–8 px, so most 8 × 8 blocks pick the background beside the highlight). No hilt, guard or blade width reads.
- `shoot2/frames/frame_01..06.png` — the pistol is a ~10 × 3 px dark blob with one cyan speck; grip, trigger guard and barrel direction are gone.
- `idle/frames/*`, `run/frames/*` — the sheathed katana is a 1 px line with a single white chape pixel.
- With B1 the eye is also 1 px at 64, so the head reads as a hair blob plus an orange nose.

Broken requirement: “readable silhouettes at 64”, “pistol readable every aiming frame”, “violet eye intact … at 64”.

### B4 — Packet and shipped verification no longer describe the same build

Files: `work/review/character/MANIFEST.md`, `output/character/agent/build_report.json`.

- The packet was generated 11:54–11:56; the shipped actions were re-rendered at 12:20–12:45. Opening the packet shows art that is not shipped.
- `MANIFEST.md` announces a “## Transition SHA-256” section but the section is **empty** — no hash proof for the anchor claim.
- `build_report.json` lists only `"run"` under `actions` (idle/slash2/shoot2/roll absent) and `"transitions": {}`; `transitions.json` is also `{}`. The shipped build report covers 1 of 5 actions and none of the 6 anchors.

Broken requirement: the packet's own promise that its images are “review copies of shipped assets”, and check 3's evidence.

---

## MAJORS (5)

### M1 — The pistol holster is not readable, and shoot2 never shows an empty one

Files: `idle/frames_hi/frame_00..07.png`, `run/frames_hi/frame_00..07.png`, `slash2/frames_hi/frame_00.png`, `shoot2/frames_hi/frame_01..06.png`.

- The hip item is a **grey box with two cyan stripes and three-to-four tan bars** underneath; there is no slide, grip, trigger guard or muzzle direction, and no holster body. `02_part_pistol.png` is a clean 117 × 88 semi-auto, and none of that silhouette survives on the hip.
- In `shoot2 f1–f6` the pistol is in her hand, yet the same grey block is still in the holster at her hip (the “empty” holster is the same object). A player sees a pouch that never empties, not an empty holster.

Broken requirement: “pistol holstered at the right hip with a readable pistol shape”, “Empty holster stays visible in shoot2”.

### M2 — The weapon teleports at the anchors

Files: `slash2/frames_hi/frame_00.png` → `frame_01.png` and `frame_06.png` → `frame_07.png`; `shoot2/frames_hi/frame_00.png` → `frame_01.png` and `frame_06.png` → `frame_07.png`.

- f0 is the run pose with the katana sheathed / pistol holstered; f1 already has the katana overhead in both hands / the pistol aimed; f6→f7 reverses it. There is no draw or holster motion.
- The pixel-identical anchor requirement is met (see “Passes”), but the transition the player sees is a hard pop.

Broken requirement: “coherent motion, no popping”.

### M3 — Detached fragment in the idle frames

File: `idle/frames_hi/frame_00.png` (and `roll/frames_hi/frame_00.png`, which is pixel-identical).

- A **detached 8 px island** at (211,226)–(212,230): a 2 × 5 vertical speck separated from the hair mass. `idle f0`/`roll f0` are the only frames with two connected components; `idle f1–f7` have one.

Broken requirement: “no neighbour fragments”, “Every frame complete”.

### M4 — Idle has no vertical motion

Files: `idle/frames_hi/frame_00..07.png`.

- All eight frames share the same bbox (x 144–367, y 84–503): the eight unique poses only sway/lean; there is no breathing bob, and the ground contact never moves.

Broken requirement: check 1 “idle 8 unique frames” is met, but the idle does not read as alive at a commercial standard.

### M5 — Slash2 f4 blade tip and 64 px tip are unreadable

File: `slash2/frames_hi/frame_04.png`.

- Even setting the scale collapse aside, the blade tip ends in a flat chisel cap with a 1-px step, whereas f1/f5 end in a point. At 64 the blade is a line, so no tip reads at all.

Broken requirement: “katana … full length, tip not truncated”.

---

## MINORS (5)

1. **64 px outline is diluted.** Boundary-pixel mean luminance 63 at 64 px vs 105 interior (28 vs 99 at 512 px), so the 64 sprites have a soft feathered edge instead of a crisp 1-px outline.
2. **`20_cross_action.png` cannot demonstrate cross-action consistency.** Because `slash2 f0 = shoot2 f0 = run f0` and `roll f0 = idle f0`, the sheet is three identical run panels plus two identical idle panels.
3. **Roll tuck frames are cluttered.** `roll/frames_hi/frame_02,03,04,05.png` merge limbs, shorts, scabbard and hair into one dark mass; at 64 (`roll/frames/frame_02..05.png`) the body orientation cannot be read. The sequence does read as a tumble (f1 tuck → f2–f5 rotation → f6 crouch → f7 stand).
4. **Weapon length changes between stowed and drawn states.** Stowed scabbard ≈ 165 px in `idle/frames_hi/frame_00.png`; the drawn katana in `slash2/frames_hi/frame_01.png` is ≈ 250 px (same character scale).
5. **The 3D truth sheets are too crude to arbitrate.** `12_*` are untextured box mannequins with a flat hair slab and a stick weapon; the roll truth (`12_roll_3d_truth_all.png`) is itself a tangle of boxes, so the roll's readability problems are inherited from the reference rather than introduced only by the pixel pass.

---

## Passes (verified, not defects)

- **Transition anchors: exact.** All six pairs pixel-identical (0 differing px): `slash2 f0 = run f0`, `slash2 f7 = run f7`, `shoot2 f0 = run f0`, `shoot2 f7 = run f7`, `roll f0 = idle f0`, `roll f7 = idle f7`; `23_transition_diff.png` is uniformly black.
- **8 unique frames per action** at 512 and at 64 (no duplicate MD5 in any action).
- **No canvas clipping** in the current build: the tightest margin is 8 px (boot soles at y = 503, ≈1 px at 64); no frame touches an edge. (The 11:54 packet did clip `slash2 f3` at x = 0.)
- **Single connected component** in all 512 frames except `idle f0`/`roll f0` (M3).
- **No pinholes other than the eye hole (B1).** All other enclosed transparent regions are limb/hair gaps (≥ 100 px) in the current art.
- **64 px set is a clean downsample mechanically**: 98–99 % of sampled 64-px colours exist verbatim in the 512 art, i.e. the pipeline introduces no resampling blur; detail loss is inherent to 8× reduction.
- **Run cycle**: legs alternate, a real vertical bounce (sole y varies 494–503), and only a small fraction of the silhouette is unchanged across the 8 frames (no static arm/leg). No duplicate frames.
- **Weapon instancing**: one hilt + one guard + one blade in hand during slash2, one **empty** scabbard on the back (material false-colour pass on `slash2 f1`/`f6`), one pistol, one sheathed katana in idle/run. No second hilt/blade/gun.
- **Katana gripped in every drawn frame** (`slash2 f1` two-handed on the hilt; `f2–f6` one hand at the hilt with the guard adjacent).
- **Outfit at 512**: long silver hair, dark short-sleeve crop top, detached forearm sleeves with cyan cuffs, shorts + thigh strap, black boots.
- **Roll reads as a tumble** (f1 tuck → f2–f5 rotation → f6 crouch → f7 stand), not a re-inversion after standing.

---

## Frames actually opened

| action | 512 (`10_*` / shipped `frames_hi`) | 64 (`11_*` / shipped `frames`) | 3D truth (`12_*`) |
|---|---|---|---|
| idle | f0–f7, plus head/eye/hip/hair crops of f0 | f0–f7, plus 8×/16× head crops of f0/f2 | f0–f7 |
| run | f0–f7, plus eye/hip/leg crops of f0/f2 | f0–f7, plus head crops | f0–f7 |
| slash2 | f0–f7, plus blade-tip, hip, hand and false-colour crops of f1/f3/f4/f5/f6 | f0–f7, plus head crops | f0–f7 |
| shoot2 | f0–f7, plus gun/holster crops of f1/f2/f3 | f0–f7, plus head crops | f0–f7 |
| roll | f0–f7, plus full-frame crops of f1/f2/f6 and false-colour of f2/f6 | f0–f7 | f0–f7 |

Also opened: `00_design_sheet.png`, `01_char_ref_64_x16.png`, `02_part_katana.png`, `02_part_scabbard.png`, `02_part_pistol.png`, `20_cross_action.png`, `21_transition_pairs.png`, `22_run_loop.png`, `23_transition_diff.png`, `MANIFEST.md`.

---

## Fixed during the review (do not re-report as current)

- Duplicate/extra hilts and blades in `slash2 f6` (present in the 11:54 packet) — current build has one blade + an empty scabbard.
- `slash2 f3` scabbard clipped at x = 0 (11:54 packet) — the 12:28 rebuild had a 12 px left margin and no later build re-clipped it.
- Old flat idle head that did not match the other actions (11:54–12:28 builds) — the 12:33+ idle uses the new face.
- Flat in-hand pistol with a saturated violet block in `shoot2` (11:54 packet) — the current gun has a readable slide/grip/trigger guard.
- Single-frame white crescent VFX in `slash2 f3` (11:54 packet) — absent now.

---

## Conditions for a PASS

1. Paint the pupil: replace the transparent eye hole with an opaque dark pupil in all 40 frames (B1). This is the single most important fix; without it the eye is a hole in every frame.
2. Fix the slash2 scale: f3/f4/f5 must keep the same character scale and the same weapon length as f1/f6 (B2).
3. Freeze the pack (B4), regenerate the packet and `build_report.json` from the frozen build, and fill the `MANIFEST.md` SHA-256 table.
4. Make the 64 px weapons and eye readable: blade ≥ 2 px with a guard, pistol with a visible grip/trigger, iris ≥ 2 px violet (B3).
5. Rebuild the hip rig: a readable stowed pistol and a visibly **empty** holster in shoot2 (M1).
6. Add at least a 2-frame draw/holster so the anchors do not teleport (M2), remove the idle fragment (M3), give the idle a breathing bob (M4), and fix the slash2 f4 blade tip (M5).

Only when blockers and majors are zero can this pack be accepted.
