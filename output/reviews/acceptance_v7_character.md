# Acceptance review v7 — character pack (`agent`)

**Reviewer:** independent multimodal acceptance (did not build these assets)
**Packet under review:** `/dat/projects/artist2d/work/review/character/` (generated 2026-11-02 14:59)
**Shipped set:** `/dat/projects/artist2d/output/character/agent/`
**Review window:** 2026-11-02 14:59 – 15:25 CST (see §0 — the shipped tree was being rebuilt throughout)

---

## Verdict

# FAIL

Blockers found: **5** — all of them break explicit requirements. Two are visible on the
run→slash2 transition, one makes the `roll` action unusable at both 512 and 64, one shrinks the
character by ~19 % for the whole slash at 64 px, and one invalidates the review evidence itself.
The pack cannot ship in this state.

Additionally the evidence packet is **not a faithful record of the delivered build** (§0), so
acceptance cannot be granted even for the parts that currently look correct.

---

## 0. Delivery-integrity warning (read first)

The shipped tree was being rewritten while this review ran. A rebuild process
(`scripts/build_character.py --character agent ...`) was live from 15:00 onward; individual
actions were re-written at 15:01 (idle), 15:02 (run), 15:04 (slash2), 15:06 (shoot2), 15:07–15:08
(roll), then again at 15:15–15:19, and slash2 again at **15:22**.

Consequences, all verified:

* `10_*` sheets were produced at **14:59**, before any of the current frames existed.
* `slash2/frames_hi/frame_00.png` toggles between two builds:
  * *stowed* variant — byte-identical to `run/frames_hi/frame_00.png` (seen at 15:20);
  * *drawn-sword* variant — `sha256 0d201987af84…` (seen at 15:04 **and again at 15:22:33**).
    The last writer wins, so the delivered state is non-deterministic.
* The 64 px anchor files are **overwritten from `run` by a post-pass** at the end of each build
  (`run`, `slash2`, `shoot2` all carry `sha256 0cedf320…` for `frame_00.png` after the post-pass,
  and `slash2` carries `dd06a6bb…` before it). The equality asserted in `MANIFEST.md` /
  `transitions.json` is therefore *produced by copying*, not by the art actually matching.

Everything below is stated with the exact frame and, where relevant, the file hash/mtime so it can
be re-checked against a frozen build.

---

## 1. Blockers

### B1 — `slash2` start frame has the katana drawn; run→slash2 transition is broken
**Files:** `output/character/agent/slash2/frames_hi/frame_00.png` (sha256 `0d201987af84…`,
mtime 15:22:33), `output/character/agent/slash2/frames/frame_00.png` (sha256 `dd06a6bb…`)
**Against:** `run/frames_hi/frame_00.png` (sha256 `bd55374776af…`), `run/frames/frame_00.png`
(`0cedf320…`)

* Measured difference (composited, alpha-correct): **54 471 visibly different pixels** inside the
  512 body window; the 64 px pair differs across essentially the whole sprite.
* Visual: `slash2 f0` holds the katana in the right hand with the blade running up across her
  chest and past her face. `run f0` has the same body pose with the sword **stowed** at the hip.
* Effect: on the run→slash2 cut the sword teleports out of the scabbard into her hand, and her
  sleeve/hair silhouette changes on the same frame.
* Reproduced three times (15:04, 15:22, and again at 15:28 with the same hi-res hash
  `0d201987af84…`, 64 px `3fc7b2b3…`), so it is the pipeline's steady state, not a one-off. The
  "stowed" variant exists only right after the anchor-copy post-pass (15:20).

**Broken requirements:** "slash2 start = run f0 … (the 64 anchors are pixel-identical)";
"katana drawn ONLY in slash2"; "transitions … no popping".

### B2 — `roll` frames 1–6 are destroyed by rectangular "slab" artefacts; unusable at 64
**Files:** `10_roll_hi_all.png` cells f1–f6; `11_roll_64px_all.png` cells f1–f6; reproduced in the
current build at `roll/frames_hi/frame_01.png` (sha256 `39688d390114…`, 15:18:56) and
`frame_02.png` (sha256 `d89b17425c2c…`)

* `roll f1`: a hard-edged ~180×105 px dark-violet rectangle sits across her back; a second grey
  rectangle hangs below it. The torso is not a torso, it is a quad.
* `roll f2`: three or four stacked black rectangles with the head hanging at the bottom; the
  scabbard is a straight bar. Not readable as a person at any resolution.
* `roll f3`–`f6`: same class of defect (rectangles for the hair mass, sleeve and scabbard). Compare
  `12_roll_3d_truth_all.png`: the 3D proxy renders the hair/scabbard as boxes, and the 2D frames
  reproduce those boxes as filled rectangles instead of silhouettes.
* At 64 px (`11_roll_64px_all.png` f1–f6) the frames are unrecognisable blobs; f2 is a vertical
  bar with a blob of hair.
* Consequence: the action reads as an explosion of dark blocks, not a forward roll.

**Broken requirements:** "Roll: forward roll … katana attached/behind the body, **no floating
slab**"; "Every frame complete: no … neighbour fragments"; "readable silhouettes at 64";
"coherent motion".

### B3 — `slash2` f3/f4: truncated blade at the canvas edge, plus a second complete katana (packet)
**Files:** `10_slash2_hi_all.png` cell f3 and cell f4 (packet, 14:59)

* Measured content bbox in the 640 px cell:
  * f3 → `x 108…639` (**touches the right edge**), blade runs off-canvas, tip missing.
  * f4 → `x 0…639` (**touches both edges**).
* `f4` additionally contains a **second, complete katana** entering from the left edge: hilt cut by
  the canvas border at x=0, tsuba, and a full blade whose tip ends in mid-air at x≈215 — while her
  own katana is in her hand and exits the right edge, and the scabbard is on her back. Three blade
  objects in one frame.
* At 64 px the same truncation survives into the game frames: `11_slash2_64px_all.png` f3 and f4
  both occupy the **last pixel column** (cell content reaches x = 63.9 of 64), so the blade tip is
  cut by the game frame as well. The duplicate sword of f4 is not separately visible at 64 (it is
  scaled into the body silhouette), but it is present in the shipped 640 art.

**Broken requirements:** "no cropped … blade at the edge"; "tip not truncated"; "Exactly ONE
katana/scabbard/pistol; no second hilt/blade/gun"; "no neighbour fragments"; "no foreign
fragments".

*Note:* B3 does **not** reproduce in the 15:17/15:19 build (f3 bbox `94…590`, f4 `98…557`). It is a
blocker for the packet as submitted; the packet must be regenerated and re-reviewed.

### B4 — `slash2` 64 px frames f1–f6 are rendered ~19 % smaller than f0/f7 (body scale changes)
**Files:** `11_slash2_64px_all.png` cells f1–f6 (packet); mechanism visible in the current build too
(`output/character/agent/slash2/frames/frame_01..06.png`, written 15:22:47)

* Packet measurement (cell content ÷ 8): f0 `y 10.0…62.9` → **53 px** tall; f7 `y 10.0…61.9` →
  52 px; but f1–f6 `y 14.0…56.9` → **43 px**. Every other action's 64 px frames are 53 px tall.
* Visually: `11_slash2` f1 is a clearly smaller character than f0 in the same cell — the head, body
  and boots are all ~20 % smaller and the sprite sits higher in the frame.
* Cause (arithmetic fits exactly): the 64 px conversion fits the whole *content* bbox instead of the
  512 body window. At 640, f0/f7 are 420 px tall, f1–f6 are **516 px** tall (raised blade), and
  420/516 = 0.814 — i.e. the 0.81× shrink.
* The current build (15:22) has a different variant of the same bug: f1–f6 are 52–53 px tall but
  sit **5–6 px higher** in the 64 frame than f0/f7 (`y 5…56` vs `y 10…62`), while at 640 all frames
  share the same body position (`y 148…567`). In game the sprite would jump up ~48 px (at 512 scale)
  on frame 1 and drop back on frame 7.

**Broken requirements:** "slash2 64 body window"; "Check that all slash2 action frames have the
same body scale (no one frame smaller)"; "no scale/head/outfit popping".

### B5 — Review evidence does not match the product
**Files:** whole packet vs `output/character/agent/`

* Packet built 14:59; every shipped action was rebuilt afterwards (see §0).
* The packet's `10_slash2` f0 shows the stowed-sword composition while the build at 15:22 ships the
  drawn-sword composition for the same frame (B1).
* Packet sheets are composited over an opaque background (`#12121A`), so the alpha channel is
  destroyed. The requirement "no transparent pinholes" **cannot be verified from the packet at
  all**. (I verified it on the RGBA frames instead: no hole larger than 4 px, but 7 tiny notches do
  remain — see m5.)
* `MANIFEST.md` states the transition proof hashes as `run:0 = 9298e8…` / `run:7 = da60cb0b…`.
  Because the build copies `run`'s 64 px anchor over the action's own file, that comparison can
  never fail — it is tautological and cannot detect the art drift that B1 describes.

**Broken requirement:** none of the art requirements directly — but the submission is not
reviewable/certifiable as delivered.

---

## 2. Majors

### M1 — Stowed pistol does not read as a pistol (all actions, 512 and 64)
**Frames:** `10_idle` f0–f7, `10_run` f0–f7, `10_shoot2` f0/f7, `10_slash2` f0/f7 — the hip object
is ~13×63 px (idle f0: x 296…312, y 292…355), a long dark slab with one cyan vertical stripe and a
grey plate.
**Reference:** `02_part_pistol.png` is a clear 117×88 landscape pistol (slide, muzzle, grip,
trigger guard); `00_design_sheet.png` shows the same readable pistol at the hip.
**Defect:** no grip/muzzle/trigger-guard silhouette is legible; it reads as a drop-leg holster or
leg sheath. At 64 it is a 3×9 dark blob (`11_idle_64px_all.png`). In `shoot2` the *in-hand* pistol
does read correctly, so the readable asset exists — it is simply not used at the hip.
**Broken requirement:** "pistol at the right hip **with a readable pistol shape**".

### M2 — `idle` f5: one-frame stance pop
**Files:** `10_idle_hi_all.png` f5; `11_idle_64px_all.png` f5
**Measurement (current build, rows 470–503):** boot span width f0 67, f1 67, f2 72, f3 67, f4 67,
**f5 94**, f6 67, f7 65. The far boot appears ~13–14 px further out on both sides for exactly one
frame and returns, and the ankle encloses two new transparent gaps (111 px + 69 px enclosed
regions, absent in f6/f7).
**Broken requirement:** "commercial quality … no popping"; `idle` should be a smooth 8-frame
breathing loop.

### M3 — `slash2` f2/f3: head unreadable at 64
**Files:** `11_slash2_64px_all.png` f2, f3
The raised blade, hair mass and face merge into one bright/dark blob; no face, no clear head
silhouette (contrast `11_run_64px_all.png`, where the head reads clearly).
**Broken requirement:** "readable silhouettes at 64"; "Violet eye intact at … 64".

---

## 3. Minors

* **m1** — `01_char_ref_64_x16.png` is present in the packet directory but **not listed in
  `MANIFEST.md`**, and it is a stale white-background reference whose blade is a black/white
  checkerboard, unlike anything shipped. Confusing evidence; drop it or document it.
* **m2** — `shoot2` f1: the top of the head/hair sits 16 px above the f0/f7 anchors and f2–f6 sit
  15–23 px below them, with the feet pinned at y=503. If this is intended crouch/aim posture it is
  fine, but it is a visible vertical jump on the anchor→aim cut; please confirm it is authored, not
  a scale change.
* **m3** — Circular grey dithered blotches appear on the top/shorts in `slash2` f1/f2/f4 (and a
  fainter one on the `run` torso) and are absent from `00_design_sheet.png`; they read as dirt or a
  print that pops in and out between frames. Confirm whether they are intended (they look like a
  dithering artefact of the warp/remaster pass).
* **m4** — Packet headers are burned into the sheets at 1:1 (`frame N` at 8,7 of every cell) and
  overlap the artwork area; harmless, but it makes automated pixel-diff of packet cells impossible
  without masking.
* **m5** — Seven 2–3 px enclosed transparent notches (literal "pinholes", cosmetically invisible at
  64): `idle` f3 (313,244); `run` f1 (202,213) and (249,232); `run` f7 (276,356); `slash2` f7
  (340,420); `shoot2` f7 (276,356); `roll` f4 (191,237) [x,y]. All sit at the katana guard/grip
  junction. Clean these if the "no transparent pinholes" clause is to be read literally.

---

## 4. Checks that passed

* **Frame completeness / uniqueness:** all 8 frames per action are byte-distinct
  (idle, run, slash2, shoot2, roll).
* **Canvas edge contact (512/640):** no action except `slash2` f3/f4 touches a hi-res canvas border
  (idle/run/shoot2/roll all have ≥8 px margin). At 64, `slash2` f3/f4 reach the right column and
  `shoot2` f1–f6 reach x=62 (1 px margin) — see B3.
* **Alpha integrity (checked on the RGBA shipped frames, not the packet):** alpha is strictly
  binary (0/255) in every frame — no semi-transparent halos. No pinhole larger than 4 px; a
  handful of 2–3 px enclosed notches remain (see m5), none of them visible at 64.
* **Scale identity at 512:** every `idle`, `run` and `slash2` frame is exactly 420 px tall; `shoot2`
  f0/f7 are 420 and f1–f6 are 397–436 (aim/crouch posture — see m2, no head-scale change).
  Head width 75–79 px in every idle frame — no single shrunken frame at 512.
  (`slash2` f1–f6 are taller only because the raised blade extends 96 px above the head, which is
  why the 640 canvas exists — see B4 for the 64 px consequence.)
* **Violet eye:** present and intact at 512 wherever the face is unobstructed — verified frame by
  frame in `idle` (all), `run` (all), `shoot2` (all) and in `slash2` f0/f1/f5/f6/f7, and as a
  violet pixel in the matching 64 px frames. Legitimately hidden in `roll` f2/f3 (head tucked) and
  partly crossed by the blade in `slash2` f2/f3 (see M3).
* **Run loop (`22_run_loop.png`, f6→f7→f0→f1):** legs alternate with contact at the same forward
  x, vertical bounce is 9 px with two hops per cycle (head 84/80/75/79/84/79/75/84,
  feet 503/499/494/498/503/498/494/503). Softness: the upper arm barely swings; acceptable.
* **64 px anchors in the packet:** run f0/f7 ≡ slash2 f0/f7 ≡ shoot2 f0/f7, and
  idle f0/f7 ≡ roll f0/f7 — **0 differing pixels** (verified numerically and in
  `23_transition_diff.png`, all black). This is currently only true because of the anchor-copy
  post-pass (see B1/B5).
* **Weapon state outside `slash2`:** katana sheathed and unique in idle, run, shoot2 and roll;
  scabbard stays empty and visible while the blade is out in `slash2` f1–f6; holster stays at the
  hip in `shoot2`; `shoot2` shows exactly one in-hand pistol.
* **Design sheet / parts:** `00` reads correctly (long silver hair, violet eye, short-sleeve top,
  detached sleeve with cyan trim, shorts, boots, katana + scabbard across the back, pistol at hip);
  `02_part_katana/scabbard/pistol` are clean single objects with consistent palette
  (0 palette violations per `build_report.json`).
* **`12_*` truth sheets:** pose reference only, consistent with the intended motion (no score
  taken) — but this is where the `roll` slabs come from (B2).

---

## 5. Frames actually opened

Every PNG in the packet directory was opened, plus the shipped cells they cross-reference:

| packet file | frames inspected |
|---|---|
| `00_design_sheet.png` | full sheet + 3× crops of head/torso/hip |
| `01_char_ref_64_x16.png` | full |
| `02_part_katana.png`, `02_part_pistol.png`, `02_part_scabbard.png` | full |
| `10_idle_hi_all.png` | f0–f7 (all 8), plus f0/f5/f6 6–8× crops (head, waist, hip, feet) |
| `10_run_hi_all.png` | f0–f7 (all 8), plus f0/f4 6× arm/leg crops |
| `10_slash2_hi_all.png` | f0–f7 (all 8), plus f1/f3/f4 2–8× crops (head, arm, left edge, hip) |
| `10_shoot2_hi_all.png` | f0–f7 (all 8), plus f1 2× and 8× crops (gun, hip, arm) |
| `10_roll_hi_all.png` | f0–f7 (all 8), plus f1/f2/f4 2× crops |
| `11_idle_64px_all.png`, `11_run_64px_all.png`, `11_slash2_64px_all.png`, `11_shoot2_64px_all.png`, `11_roll_64px_all.png` | all 8 cells each (40 cells) |
| `12_idle_3d_truth_all.png`, `12_run_3d_truth_all.png`, `12_slash2_3d_truth_all.png`, `12_shoot2_3d_truth_all.png`, `12_roll_3d_truth_all.png` | all 8 cells each (40 cells) |
| `20_cross_action.png` | all 5 panels |
| `21_transition_pairs.png` | all 6 pairs (12 panels) |
| `22_run_loop.png` | f6, f7, f0, f1 |
| `23_transition_diff.png` | all 6 diff panels |

Shipped frames cross-checked directly (RGBA, 1:1) at
`output/character/agent/{idle,run,slash2,shoot2,roll}/frames_hi/*.png` and `frames/*.png`
(40 + 40 files): bboxes, alpha holes, per-frame hashes, transition equality, boot/stance metrics,
cyan-marker tracking, and 1:1/2×/8× crops of the head, arm, hip, feet and blade tips.

---

## 6. Conditions for a PASS

1. Fix B1: `slash2` f0/f7 must be the run frames (stowed katana) in both 512/640 and 64, produced
   by the art pipeline, not by overwriting the anchor file afterwards. Ship a diff proof computed
   against a freshly read `run/frames/*` at package time.
2. Fix B2: rebuild `roll` so no quad/rectangle survives — the scabbard, hair and sleeve must follow
   the body silhouette; verify each of f1–f6 at 64 px before shipping.
3. Fix B4: derive `slash2`'s 64 px frames from the **512 body window** (never from the 640 content
   bbox), so every slash frame has the same 53 px body height and the same ground line as f0/f7.
4. Regenerate the packet **from one frozen build** and re-run acceptance. The packet must contain
   RGBA frames (or an alpha-channel proof) so pinholes can be verified.
5. Fix M1 (readable holstered pistol), M2 (idle f5 stance), M3 (slash2 f2/f3 head at 64).
6. Remove `01_char_ref_64_x16.png` from the packet or document it in `MANIFEST.md`.

Once those are done, re-review must repeat at minimum: `10_slash2` f0–f7, `10_roll` f1–f6,
`11_slash2`/`11_roll` all cells, `21`/`23` anchors, and the `10_*`/`11_*` edge-touch scan
(no frame may touch a canvas border).
