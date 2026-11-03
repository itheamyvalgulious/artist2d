# Character animation review — round 2 (independent)

Reviewer: `char-review-v2` (did not generate these assets).
Packet: `/dat/projects/artist2d/work/review/character/` (MANIFEST.md read first).
Ship source: `/dat/projects/artist2d/output/character/agent/<action>/{frames_hi,frames}/`.
Method: every listed PNG was opened and inspected at full resolution; ambiguous sheets were resolved by
nearest-neighbour zoom crops of the source frames (no resampling, no regeneration, no asset modification).
Numeric checks below are measurements taken from the shipped PNGs (bounding boxes, identical-frame diffs,
colour counts, downsample comparison); no pipeline test was executed.

---

## 1. Coverage — every file inspected

24 / 24 listed files inspected (5 actions × 3 sheets + 5 design/part files + 4 cross-cutting sheets).
Result of the numeric checks used to confirm what the eye sees is in the right column.

| # | File | Result | Note / evidence |
|---|------|--------|-----------------|
| 1 | `00_design_sheet.png` | PASS | Female cyberpunk, silver hair, violet-tinted eye, crop top + shorts + detached sleeves + boots, full katana (thick blade, tsuba, cyan edge), dark scabbard, compact pistol, palette on spec. |
| 2 | `01_char_ref_64_x16.png` | FAIL | The canonical 64px reference itself draws the katana as a thin hatched needle and the face with no readable violet eye — this reference is the origin of both B3 and M9. |
| 3 | `02_part_katana.png` | PASS | Full-length thick blade, cyan edge on the cutting side, wide tsuba, wrapped tsuka. |
| 4 | `02_part_scabbard.png` | PASS | Thick dark scabbard with metal mouth and chape. |
| 5 | `02_part_pistol.png` | PASS | Compact pistol, cyan accents, readable guard/slide/sights. |
| 6 | `10_idle_hi_all.png` | PASS (head) / MINOR loop pop | All 8 heads identical; legs/hair drift, wrap pops (§3, M7). |
| 7 | `11_idle_64px_all.png` | FAIL | Face is blank skin at 64px; no eye pixel anywhere (§2 M9). |
| 8 | `12_idle_3d_truth_all.png` | PASS | 8 subtle variants of the same standing pose; matches the art. |
| 9 | `10_run_hi_all.png` | FAIL | Cycle is a 4-frame pattern repeated twice; leading leg never swaps; hilt/scabbard split (§3 B2, M1). |
| 10 | `11_run_64px_all.png` | FAIL | Eye gone, hilt/scabbard fused into one dark blob, speckled hair. |
| 11 | `12_run_3d_truth_all.png` | PASS | Contact/pass/rise poses match the drawn frames. |
| 12 | `10_slash2_hi_all.png` | FAIL | Blade is a variable-length needle with no cyan edge in f2–f5; f6 carries an extra detached blade shard on the thigh (§2 B3, §3 B3). |
| 13 | `11_slash2_64px_all.png` | FAIL | Blade degrades to a 1px staircase; tsuba and cyan edge disappear. |
| 14 | `12_slash2_3d_truth_all.png` | PASS | Sword direction/arc per frame agrees with the art. |
| 15 | `10_shoot2_hi_all.png` | FAIL | Two drawn pistols in f1, ghost pistol + edge clipping in f4, holstered thigh pistol never removed in f1–f6 (§2 B1, §3 B1/B4). |
| 16 | `11_shoot2_64px_all.png` | FAIL | Gun becomes an unreadable club; face blank. |
| 17 | `12_shoot2_3d_truth_all.png` | PASS | Extended-arm aiming pose matches. |
| 18 | `10_roll_hi_all.png` | FAIL | f2/f3/f4 are an inverted sprawl, not a tucked roll; scabbard flies off the body (§2 Roll, §3 M3). |
| 19 | `11_roll_64px_all.png` | FAIL | Frames 2–4 are an unreadable jumble of hair/limbs at game scale. |
| 20 | `12_roll_3d_truth_all.png` | PASS | Truth is a proper compact tucked ball — the art deviates from it. |
| 21 | `20_cross_action.png` | FAIL (inherits) | Proportions/scale are consistent, but it exposes the split stowed katana and the oversized duplicated pistols. |
| 22 | `21_transition_pairs.png` | PASS | run:0 = slash2:0 = shoot2:0, run:7 = slash2:7 = shoot2:7, idle:0 = roll:0, idle:7 = roll:7. |
| 23 | `22_run_loop.png` | FAIL | f7→f0 wrap is continuous in direction, but the cycle content repeats f0–f3 in f4–f7 (§3 M1). |
| 24 | `23_transition_diff.png` | PASS | All six panels pure black (0 differing pixels) → anchors are byte-identical. |

Manifest SHAs verified against `frames/frame_*.png`:
`idle:0 79015248…`, `idle:7 420b3d47…`, `run:0 4b41f2d1…`, `run:7 b7066c8c…` — all match.

---

## 2. Round-1 blockers — re-verification

| Item | Verdict | Visible evidence | Fix |
|------|---------|------------------|-----|
| **B1** shoot2 f1/f4 had no pistol | **NOT FIXED (worse)** | A pistol now exists, but **f1 draws two complete pistols**: the held one (grip in the fist) plus a second full silhouette with its own round trigger guard, offset ≈55px up/right — `shoot2/frames_hi/frame_01.png` (region x380–512, y70–300). **f4** has the held pistol *plus* a third gun fragment at the top-right — `frame_04.png` (same region) — and the held pistol is **cut by the canvas edge** (content reaches x=511; other frames stop at x=501–504). On top of that the **thigh-holstered pistol is still drawn in every frame f0–f7**, so f1–f6 carry 2–3 pistols. | Composite the canonical pistol exactly once per frame; delete the thigh copy in all frames where the hand pistol is visible; re-frame f4 so the muzzle keeps ≥8px margin. |
| **B2** slash2 f6 had no katana | **PARTIAL** | A full katana does continue the arc in f6 with a tsuba and cyan edge (`slash2/frames_hi/frame_06.png`), and the back scabbard is empty (no hilt protruding in f2–f6) ✔. **But f6 also contains a second, detached blade shard lying across the bare right thigh** (~x295–320, y400–445 in `frame_06.png`, clearly visible at 4×): a duplicate blade fragment left by the inpaint. | Remove the shard; inpaint only the blade corridor. |
| **B3** drawn katana was a variable-length needle | **NOT FIXED** | Blade tip→tsuba length in the 512px frames: f2 ≈200px, f3 ≈153px, f4 ≈130px, f5 ≈113px, f6 ≈227px (**2× spread**); blade thickness f5 ≈3px vs f6 ≈12px (**4× spread**). The cyan cutting edge of `02_part_katana.png` is present only in f6; f3/f4/f5 have a plain grey needle with a 1–3px tsuba bar, f5 has no readable tsuba. The back scabbard is empty in all drawn-katana frames ✔ (but see §3 B2 — the sheathed hilt is misaligned). | Draw the blade from one parametric katana (fixed blade length ≈0.40 × body height, fixed 10–12px width, tsuba + cyan edge) and only rotate it. |
| **B4/B5** idle had two faces and a 17px head pop | **FIXED** | All 8 `idle/frames_hi` frames: topmost face-skin row = **y112** and face skin x-range = **(238,301) exactly, in all 8 frames**; the 8 head crops are pixel-identical. No head jump anywhere in the loop. | — |
| **Roll** round 1 sprawl | **NOT FIXED / PARTIAL** | f0 and f7 are correct and the 360° pitch exists, but f2 (`frame_02.png`) and **f3 (`frame_03.png`) are an inverted sprawl**: legs splayed to the upper-left, torso horizontal, head bottom-right, nothing tucked; f4 (`frame_04.png`) reads as lying on the back with the knees in the air. The figure also floats free of the ground plane (no contact shadow or floor contact in f1–f6) and the scabbard leaves the body as a loose rod in f1–f4. Both feet are distinguishable ✔; framing stays inside the panel ✔ (roll bbox max x=484). | Re-key the roll from the 3D tuck truth (`12_roll_3d_truth_all.png`, which is compact) — keep hands to shins, knees to chest, and keep the scabbard attached. |
| **M9** 64px diverged and lost the violet eye | **PARTIAL** | The 64px poses now match the 512 art: nearest 8× downsample of `frames_hi` matches the shipped 64px frame on **90–94 % of pixels** (box filter only 68–86 %), so the derivation is real ✔. **But the violet eye does not survive**: in `idle/frames/frame_00.png` the face rows 14–19 contain *no* eye pixel at all (the only dark pixel in the face is the outline at (16,37)); violet-hue pixel count across all 8 idle frames = **1**, run = 2, slash2 = 0, shoot2 = 0 (canonical `char_ref_64.png` has 8). Blades collapse to 1px staircases and the tsuba/cyan edge vanish. | Sample the eye (and blade edge) as a preserved 1–2px detail cluster during downsample, or paint the eye into the 64px head patch after resampling. |

---

## 3. New / remaining findings

### BLOCKER

**B1 — shoot2 carries two or three pistols per frame.**
`shoot2/frames_hi/frame_01.png`: a second complete pistol overlaps the held one (own slide, cyan bar, round trigger guard, grip) offset up/right. `frame_04.png`: a third pistol fragment at the top-right, plus the held pistol clipped by the canvas edge (x reaches 511 of 512). In **every** frame f0–f7 the thigh pistol from the idle/run sheet is still present (`shoot2/frames_hi/frame_0*.png`, hip region x180–340, y240–430), so f1–f6 show the hero holding a gun *and* wearing the same gun. Requirement violated: "no duplicate weapons".
*Fix:* single-source the pistol; mask out the holstered pistol during shoot; clamp the f4 muzzle inside the panel.

**B2 — stowed katana is split into two misaligned pieces.**
In `idle/frames_hi/frame_00.png`…`frame_07.png` and `run/frames_hi/frame_00.png`…`frame_07.png` the back weapon is drawn as (a) a wrapped **hilt + filigree tsuba** floating at the left of the head at ≈47° (pommel up-left, guard at the neck, nothing attached to the guard) and (b) a **scabbard rod** at her hip at ≈27° the *opposite* way, with a metal chape. The two never meet (≈105px gap, ≈75° kink) — it reads as a hilt glued to her back plus a loose scabbard. Compare `10_roll_hi_all.png` f5/f6, where the hilt and scabbard *are* collinear, proving the assembly exists and that idle/run are wrong. Also the idle tsuba is a lattice ornament, while `02_part_katana.png` has a plain wide bar — a different sword.
*Fix:* composite the sheathed katana as one rigid (hilt+tsuba+scabbard) sprite, one rotation, attached at the left shoulder strap.

**B3 — the drawn slash2 katana is still a needle with wrong length/thickness.**
See §2 B3. The f6 blade is a believable katana; f3/f4/f5 are 3px-thick lines 27–36 % of the body height (wakizashi/dagger proportions), f2 is 48 %. No cyan edge outside f6. The action therefore swings three different swords.
*Fix:* as in §2 B3; also add the cyan edge as a mandatory 1px line.

### MAJOR

**M1 — the run cycle is a 4-frame cycle repeated, and the leading leg never alternates.**
Legs-only (y300–512) silhouette match after best translation: f0↔f4 **25 %** mismatch, f1↔f5 **24 %**, f2↔f6 30 %, f3↔f7 32 %, whereas genuinely different poses score 73–107 % (f0↔f1 81 %, f0↔f2 73 %, f1↔f2 107 %). So f4–f7 are re-drawn copies of f0–f3: the near (right) leg leads in both halves and the far leg never comes forward. The residual 24–32 % is not pose change but jitter: the best-fit translation between the halves is **dx = +3/−12/+6/−5, dy = +5/+8/+2/−2**, i.e. the legs slide up to 12px horizontally and 8px vertically relative to the torso between the two halves of the loop. There is a vertical bob (dy 2–8px) but it is inconsistent, so it reads as wobble, not a bounce.
*Fix:* build a real 8-frame cycle (contact → down → pass → up ×2 with the legs swapped) and lock the pelvis height curve.

**M2 — 64px game frames are faceless.**
`11_idle_64px_all.png`, `11_run_64px_all.png`, `11_shoot2_64px_all.png`, `11_slash2_64px_all.png`, `11_roll_64px_all.png`: the head is a peach blob with a hair cap; there is no eye, no brow, no violet. Measured: `idle/frames/frame_00.png` rows 14–19 contain only skin/hair values — the eye does not exist at 64px. The character therefore loses "violet eyes / beautiful" in the only resolution the game uses. Additionally the 64px hair carries salt-and-pepper isolated pixels (e.g. `(111,111,136)` specks inside the light hair mass) that read as dirt, and the blades become 1px staircases.
*Fix:* hand-touch the 64px head patch (2px violet iris + 1px dark lash), and quantise/despeckle the hair after downsampling.

**M3 — the roll does not read as a roll; it is an aerial sprawl in f2–f4.**
`roll/frames_hi/frame_02.png`: torso horizontal, head bottom-right, legs bent behind at upper-left, arms crossing, everything floating. `frame_03.png`: fully inverted, legs splayed up-left, head at the bottom, unreadable silhouette. `frame_04.png`: on the back, knees in the air. The 3D truth for the same frames (`12_roll_3d_truth_all.png` f2–f4) is a tight ball — the art diverges from its own truth by the whole tuck. No ground contact in any frame.
*Fix:* re-composite roll f2–f4 from the tuck truth pose (same as the truth sheet), and add a ground-contact shadow line.

**M4 — shoot2 f4 is clipped by the canvas.**
`shoot2/frames_hi/frame_04.png` bbox right = **512** (content in the last column); all other shoot frames stop at x=501–504. The muzzle and one gun fragment are cut off.
*Fix:* shift the f4 key pose ~20px left or shrink the arm reach.

**M5 — no sheathing beat at the end of slash2.**
f6 ends mid-swing with the blade low-right; f7 is the mandated `run:7` anchor with the blade gone. The katana disappears in one frame. (Anchors themselves are correct and required, so this is a staging defect, not an anchor defect.)
*Fix:* end the swing with the blade returning toward the scabbard by f6, or add a 2-frame recovery inside the action budget.

### MINOR

- **m1 — inconsistent transparent pixel data in shoot2.** f2, f3, f5, f6 have RGB (0,0,0) under alpha 0; f0, f1, f4, f7 have the canvas colour (8,8,12). Invisible under alpha-test, but it will fringe under bilinear scaling/mipmaps, and it proves those frames went through a different stage.
- **m2 — scabbard depth/overlap.** In slash2 f2–f5 the scabbard rod is drawn *over* the shorts and the thigh (e.g. `frame_04.png`), not behind the body.
- **m3 — tsuba mismatch.** Frame tsuba is a thin bar (f2–f4) or missing (f5) and a lattice ornament in idle; `02_part_katana.png` has a wide plain bar.
- **m4 — stipple noise.** Skin, shorts and hair carry salt-and-pepper dither (`(231,154,114)` specks on skin, `(111,111,136)` specks on hair, a violet speck on the pistol slide in shoot2 f3). No AA and no magenta anywhere (verified: alpha is strictly 0/255, 46–52 colours per action, 0 magenta pixels), but the surfaces are dirty rather than crisp.
- **m5 — idle loop pop.** `idle` wrap f7→f0 differs by **16,341 px**, more than any internal step (max 13,668). The silhouette widens from x=179 (f0) to x=166 (f7) and the soles move 3–4px vertically, so the idle cuts back to a narrower, higher stance. Head is unaffected (B4/B5 fixed).
- **m6 — 12_*_3d_truth_all.png sheets are rendered on (255,0,255) magenta.** They are review artefacts, not shipped frames (shipped frames contain zero magenta), but they make "no magenta" impossible to judge from the composite alone; use a neutral background in the packet.
- **m7 — the far arm is never visible** in idle/run/shoot (hidden with no shoulder hint). Acceptable for a strict side view, worth a shoulder sliver for readability.

### Requirements walked through
Female cyberpunk agent ✔ · long silver hair ✔ · violet eye ✔ at 512 (5–15 violet px/frame), ✘ at 64 · short-sleeve top / detached sleeves / shorts / black boots ✔ · navy-gunmetal-silver-cyan-violet palette ✔ (no magenta) · katana + scabbard + pistol exist ✔ but are duplicated/mis-assembled ✘ · stowed when not in use ✔ · no duplicate weapons ✘ · no shield/dagger ✔ · consistent proportions/scale across actions ✔ (idle 84–504, run 79–504, slash 84–504, shoot 84–504) · no missing limbs ✔ · floating pieces ✘ (f6 shard, detached hilt) · crisp pixels ✔ / AA and blur absent ✔.

---

## 4. Verdict

**FAIL.**

Two blockers and one major are visible without magnification at game scale:
1. `shoot2` f1/f4 show two or three pistols at once (duplicate weapon, one clipped by the frame).
2. `slash2` f6 carries a detached blade shard lying on the thigh, and the drawn katana is still a 3px needle of inconsistent length across f3–f5.
3. The stowed katana in idle/run is a hilt and a scabbard at a 75° kink — a broken weapon.
Plus the unalternating 4-frame run, the faceless 64px frames and the sprawled roll. Round 1's head/face fix, the transition anchors, and the 512→64 derivation are genuinely fixed and pass.

---

## 5. Summary

The rebuild fixed the cheap, verifiable things and left the expensive ones. Idle is now clean: all eight frames share one canonical head/face at exactly y112 with a zero-pixel head jump, the six transition anchors are byte-identical (black diff sheet) and match their manifest SHAs, the 64px frames really are resampled from the 512 art (90–94 % nearest-match) with a binary alpha, ~50 colours, no AA, no blur and no magenta; the character, outfit, palette and the three canonical weapon parts are on spec and the katana now exists in slash2 f6. What has not been fixed is composition: the pistol is composited twice in shoot2 f1/f4 (and the thigh pistol is never removed), a second blade shard was in-painted onto the thigh in slash2 f6, the drawn katana still changes length by 2× and thickness by 4× between frames and only gains its cyan edge in f6, the sheathed katana in idle/run is assembled from a hilt and a scabbard bent 75° apart, the run is a 4-frame pattern played twice with the same leading leg and a 12px wobble, the 64px frames have no eye at all so the violet eye is lost at game resolution, and the tumble in roll f2–f4 is still an inverted sprawl that even contradicts its own compact 3D truth. These are content-level defects, not polish, so the packet cannot pass.
