# Character animation review — round 4 (independent reviewer)

- Packet: `/dat/projects/artist2d/work/review/character/` (24 files, all inspected)
- Shipped frames cross-checked: `output/character/agent/<action>/frames_hi/frame_00..07.png` (512) and `output/character/agent/<action>/frames/frame_00..07.png` (64)
- Reviewer: independent, adversarial, no assets modified, no pipeline code executed (only read-only pixel measurement of the PNGs).

## 1. Coverage — every file inspected

| # | File | What I looked for | Result |
|---|------|-------------------|--------|
| 1 | `00_design_sheet.png` | identity, palette, weapon set, proportions | PASS — silver hair, violet eye, short-sleeve top + detached sleeves, shorts, boots, full-length katana, scabbard, compact pistol |
| 2 | `01_char_ref_64_x16.png` | 16× upsample of the 64 hero | PASS (with note) — clean upscale, but hero pose shows the drawn blade *and* the sheathed set (weapon-count reference) |
| 3 | `02_part_katana.png` | tsuba, tsuka wrap, kissaki, blade:handle ratio | PASS — one piece, 485 px tall, blade≈4:1 hilt |
| 4 | `02_part_scabbard.png` | one straight rigid rod, mouth, chape | PASS — single rod, single chape, no split |
| 5 | `02_part_pistol.png` | compact pistol silhouette | PASS |
| 6 | `10_idle_hi_all.png` | eye, stow, loop | FAIL — two chape-tipped rods behind the hip in all 8 frames |
| 7 | `11_idle_64px_all.png` | same at game res | FAIL — same duplicate rods |
| 8 | `12_idle_3d_truth_all.png` | pose truth | PASS — 3D truth holds a near-static standing pose matching the sprite |
| 9 | `10_run_hi_all.png` | eye, stow, leg cycle | FAIL — 2 rods + extra back-mounted hilt; leading leg never alternates; eye is a white sclera with a 1 px violet rim |
| 10 | `11_run_64px_all.png` | same | FAIL — duplicate rods and hilt visible; 4-frame repeat |
| 11 | `12_run_3d_truth_all.png` | pose truth | PASS — leg phases in truth do alternate; sprite does not follow it |
| 12 | `10_slash2_hi_all.png` | blade count, tip, length | FAIL — f1 bare hilt, f6 two blades, blunt tips, 1.9× length / 3× thickness spread |
| 13 | `11_slash2_64px_all.png` | same | FAIL — same defects, f6 wide blade reads as a machete |
| 14 | `12_slash2_3d_truth_all.png` | pose truth | FAIL (consistency) — truth blade is a thin short spike; sprite blade is 2–3× longer and far wider |
| 15 | `10_shoot2_hi_all.png` | stow, gun, eye | FAIL — 2 rods + back hilt; gun absent in f1; eye white-with-violet-rim |
| 16 | `11_shoot2_64px_all.png` | same | FAIL — same; f1 gun not readable at 64 |
| 17 | `12_shoot2_3d_truth_all.png` | pose truth | PASS — arm extension phases match |
| 18 | `10_roll_hi_all.png` | tuck, stow attachment/layer, feet | FAIL — stowed hilt+tsuba drawn over hair/next to face in f1–f5; eye blank white |
| 19 | `11_roll_64px_all.png` | tuck readability | FAIL — tuck reads as an amorphous blob at 64; rod crosses the head band |
| 20 | `12_roll_3d_truth_all.png` | pose truth | PASS — tumble phases match the sprite; truth *does* keep the back item rigidly attached, sprite does not |
| 21 | `20_cross_action.png` | weapon set consistency across actions | FAIL — idle shows no back-mounted hilt; run/shoot2 do |
| 22 | `21_transition_pairs.png` | anchor equality | PASS — run:0≡slash2:0, run:7≡slash2:7, run:0≡shoot2:0, run:7≡shoot2:7, idle:0≡roll:0, idle:7≡roll:7 |
| 23 | `22_run_loop.png` | f6→f7→f0→f1 wrap | FAIL — wrap is continuous, but f7→f0 advances and f0→f1 repeats the same near/far leg assignment |
| 24 | `23_transition_diff.png` | black = identical | PASS — all six panels are fully black (0 differing px) |

Anchors were verified independently, not just from the diff sheet: all six pairs are **byte-identical** at 512 and at 64, and `23_transition_diff.png` is genuinely black. Manifest hashes also verify (`run:0 00ed62e5…`, `run:7 460a6f64…`, `idle:0 bbf9f24f…`, `idle:7 cdd9fdb1…`) — but only against the **64 px** frames, not the 512 frames (`run:0` hi = `eb7ec42b…`).

## 2. Round-3 blockers — status

| Round-3 blocker | Status | Evidence |
|---|---|---|
| Sheathed katana split / duplicated | **NOT FIXED** | Two chape-tipped rods behind the hip in **every** idle, run and shoot2 frame. Idle f0 light chape blobs `(143–152,343–352)` n=45 **and** `(184–195,391–400)` n=54; run f0 `(106–114,323–335)` n=49 **and** `(138–148,369–379)` n=48; shoot2 f3 `(102–108,326–338)` n=48 **and** `(135–144,373–382)` n=45. Additionally run/shoot2 carry a **second** katana hilt above the left shoulder (tsuka + tsuba, e.g. run f0 near `(200,140)`) that does not exist in idle → 2 hilts + 2 scabbards instead of 1 katana + 1 scabbard. |
| slash2 f6 duplicate blade + clipped tip | **NOT FIXED** | f6 has **two** blades: a thin blade from the hand pointing up-left ending in a blunt cut near `(190,90)`, plus a separate broad blade across the hips from `(206,320)` to `(474,494)` with no hilt attached. f1 is worse than before: the raised hand holds a **bare hilt with no blade at all** (spare hilt). Tips are blunt in f2 (stepped cut at y≈88), f3 (stepped cut ending x=500, only 9 px from the canvas edge), f5 (flat 2–3 px end), f6 (rounded flat end, no kissaki). |
| Violet eye missing in 4/5 actions | **PARTIAL — 1/5 fixed** | Idle is correct: filled violet iris, 52 iris-violet px in the head zone at 512, 2×2 violet block at 64, identical across all 8 frames. Run/slash2/shoot2 show a blown-out **white sclera with a 1 px violet rim and no iris** (5–25 stray violet px in the head zone are hair accents; e.g. shoot2 f3 = 1 px). Roll is worst: **pure white eye, zero violet** (roll f2/f3/f4 = 0 iris-violet px in the head zone). Eye design is therefore *not* consistent across actions. |
| Drawn blade length 3× | **PARTIAL** | Not 3× any more, but still inconsistent: major-axis length/width along the blade component at 512 = f2 **198×15**, f3 **198×16**, f4 **161×13** (partly occluded by the forearm), f5 **241×18**, f6 **308×40**. Against a ≈345 px body: 0.57 / 0.57 / 0.47 / 0.70 / **0.89** body heights, i.e. a 1.9× length swing and a **3× thickness swing** (f6 is a greatsword, f4 a dagger). |
| Run leading leg / 4-frame repeat | **NOT FIXED** | Front-foot x per frame: f0 396, f1 309, f2 290, f3 400, f4 418, f5 327, f6 292, f7 389 → period 4. Frames f0/f4, f1/f5, f2/f6, f3/f7 are the same pose with jitter (foot pairs repeat, near leg stays leading); the far leg never becomes the leading leg. The 3D truth alternates correctly, so this is a sprite problem only. |
| Roll: stow must stay attached/behind body, not cross face | **NOT FIXED** | The stowed katana's **hilt and tsuba are drawn over the hair and beside the face**: f1 hilt at the shoulder/head top, f2 hilt over the hair at the head, f3 hilt over the hair at the bottom of the head, f4 hilt+tsuba in front of the hair immediately left of the face, f5 hilt touching the top-left of the head. In f2 the scabbard body also crosses the head/hair band. The weapon is drawn on top of hair it should be behind, and its pivot is not the hip. |

## 3. Findings by severity

### BLOCKER

1. **Duplicate stowed weapons in idle / run / shoot2 (all 8 frames each).** Two identical chape-tipped scabbard rods sit behind the hip; run and shoot2 add a second katana hilt above the left shoulder. Requirement "no duplicate weapons" is violated in 24 of 24 frames of these actions and the weapon set is not the same in idle as in run/shoot2 (`20_cross_action.png` shows the mismatch).
   *Fix:* build **one** stowed katana (hilt + one scabbard, collinear, one chape) and instance it per action; delete the second rod, delete the back-mounted hilt, and draw the stow from the same anchored rig as the 3D truth so the set is identical in idle/run/shoot2/roll.
2. **slash2 is not one continuous single blade.** f1 = bare hilt (no blade); f6 = two blades (hand blade + detached hip blade). Requirement "exactly one drawn katana, no spare hilt, no detached shard".
   *Fix:* one blade geometry driven by the hilt position for all of f1–f6; f1 must show the blade already out of the scabbard (or the draw must start at f2 and f1 stay fully sheathed with the hilt at the hip).
3. **Violet iris only in idle.** 4 of 5 actions fail: run/slash2/shoot2 are white sclera + 1 px violet rim, roll is white with no violet at all.
   *Fix:* apply the idle eye raster (dark lash + filled violet iris + single highlight px) verbatim to run/slash2/shoot2/roll, and keep it identical at 64 and 512.
4. **Blade length/thickness is not consistent across slash2 f1–f6 (198/198/161/241/308 px long, 13–40 px thick).** f6 reads as a different weapon.
   *Fix:* lock blade length ≈ the part asset (0.55–0.65 body height, i.e. ≈200 px at 512) and blade width to 15–18 px for every drawn frame; re-derive f6 and f5 from the same geometry.
5. **Roll: stowed katana crosses the head / is drawn in front of hair** (f1–f5).
   *Fix:* parent the stow to the hip socket with the same transform as the 3D truth, force the stow layer behind the body and hair, and keep the hilt ≥8 px clear of the head silhouette through the tumble.
6. **Run does not alternate the leading leg — 4-frame cycle played twice.** This breaks the "running" read at game speed.
   *Fix:* rebuild f4–f7 as the mirrored second step (far leg leading), keeping the existing f0–f3 as the first step; the 3D truth already has the right phases.

### MAJOR

7. **512 "hi" art and 64 game art are two different drawings.** A nearest-neighbour downscale of `frames_hi` differs from `frames` in 264–382 px per frame (e.g. idle f0 = 264 px, run f0 = 374 px). Consequence: the eye reads violet at 64 in run/slash2 and white-with-violet-rim at 512 in the same frame — the review sheet does not represent the shipped sprite. Idle f0 and f7 are byte-identical at 512 but *different* hashes at 64, which is only possible if the two resolutions are painted independently.
   *Fix:* pick one source of truth (draw at 64, upscale ×8 for the review packet, or downscale the 512 art with a palette-locked quantiser) and regenerate the sheet from it.
8. **Blade tips are blunt/stepped, and f3 ends 9 px from the canvas edge** (x=500 of 512; content max x=503). It reads as a blade cut off by the frame. Requirement "no blade clipped by the canvas".
   *Fix:* give the drawn blade a real kissaki (3–4 px taper) and keep ≥16 px margin to the canvas edge in every slash frame.
9. **shoot2 f1: the pistol is not readable** (hand holds a small box with a cyan strip; no pistol silhouette at 512 or 64) while f0/f2–f7 show it clearly, and f0/f7 are the shared run anchor with no gun in hand. Reads as a weapon pop.
   *Fix:* keep the pistol silhouette in f1 (recoil/hold frame) or show it clearly holstered in the same place as idle.
10. **Idle loop has a duplicated frame**: `idle f7` is byte-identical to `idle f0` at 512 (both `4b5ff3e0…`) — the loop holds one frame and stalls at the seam.
    *Fix:* make f7 a distinct end pose (or drop to 7 frames) so f7→f0 continues the breathing phase.

### MINOR

11. **Roll tuck readability at 64.** f2 is a horizontal blob: at game resolution the head, the two boots and the rod merge; both feet are distinguishable at 512 but not at 64.
12. **Roll f2/f3 boots overlap the body silhouette** at 64, which is what kills the tuck read; nudge the tuck to keep a 1 px background gap between the two boots.
13. **Manifest hash scope is ambiguous** — the six SHA-256 values match the 64 px `frames/` files, not the 512 `frames_hi/` files. State the resolution in `MANIFEST.md`.
14. **`12_*_3d_truth_all.png` uses a magenta matte** (`#FF00FF`-family background). Harmless for a truth sheet, but it trips any automated "no magenta" palette check; use a neutral grey matte.

### Verified good (do not regress)

- Transitions: all six anchor pairs byte-identical; `23` diff genuinely all-black. Anchors/loop wraps are clean.
- No anti-aliasing: 64 px frames use exactly 20 flat colours, 512 frames 46–51 flat colours, no intermediate gradient pixels; hard 1 px edges.
- No magenta and no stray opacity in any sprite; backgrounds are fully transparent (`8,8,12,0`).
- Nothing touches a canvas border at 64 px (max content x = 62, min = 9) — no hard clipping at game resolution.
- Pistol, katana and scabbard **parts** are each clean single objects; boots, silhouette, proportions, hair length and the short-sleeve/detached-sleeve/shorts/boots costume are consistent with the design sheet.
- Transition pose reuse (run:0/run:7 as slash/shoot boundaries) is exact; the 3D truth poses for idle/run/shoot2 match the sprite phases.

## 4. Overall verdict

**FAIL.**

Three round-3 blockers are unchanged (duplicated stowed katana, slash2 duplicate blade/empty hilt, roll stow crossing the head), one is only one-fifth fixed (violet eye survives only in idle), the drawn blade is still self-inconsistent across f2–f6, and run is still a 4-frame repeat with a non-alternating leading leg. Six blockers and four majors remain, so the set is not shippable.

## 5. Summary

The packet is well-built and honest — every anchor pair is byte-identical, the diff sheet is genuinely black, the palette is flat and anti-alias-free at both resolutions, and the parts (katana, scabbard, pistol) are each correct single objects. But the fix pass only landed on idle: the eye raster is right there and nowhere else (roll has literally zero violet pixels in the head zone), the stowed katana still exists twice at the hip in all 24 idle/run/shoot2 frames while run and shoot2 additionally grow a second hilt above the shoulder, slash2 f1 holds a bare hilt and f6 carries two blades, and the drawn blade swings from a 161×13 dagger to a 308×40 greatsword inside one six-frame swing with blunt, edge-hugging tips. On top of that the tumble clips the stowed katana in front of the hair and beside the face, the run cycle never lets the far leg lead, and the 512 review art is silently a different drawing from the 64 game art. Fix the weapon instancing (one katana, one scabbard, one hilt), stamp the idle eye onto all five actions in both resolutions, lock the blade geometry to the part asset, re-parent the stow to the hip/back socket behind the body, and mirror f4–f7 for the run; then this set should pass.
