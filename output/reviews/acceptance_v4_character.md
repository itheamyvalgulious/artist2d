# Character acceptance review v4 — agent sprite set

- Packet: `/dat/projects/artist2d/work/review/character/` (all 24 files opened)
- Shipped frames cross-checked: `/dat/projects/artist2d/output/character/agent/<action>/frames_hi/frame_00..07.png` (512) and `<action>/frames/frame_00..07.png` (64)
- Method: every PNG opened and read; content measured on the packet cells (1:1 for 512, exact 8× for 64) and confirmed on the shipped frames with pixel/alpha/colour-component analysis. No asset was modified.

## VERDICT: **FAIL**

4 blockers, 4 majors, 8 minors. The v3/v4 weapon-instancing blockers (duplicate scabbard, duplicate hilt, bare hilt, two blades, eye missing at 512) are genuinely fixed — this is one katana, one scabbard, one pistol, one hilt in every frame. The set still fails on the run cycle, the roll, and the 64 px art.

---

## BLOCKERS

### B1 — Run does not alternate legs; it is a one-legged skip with no bob and no arm swing
Files: `10_run_hi_all.png` f0–f3, `11_run_64px_all.png` f0–f3, `22_run_loop.png` (f2,f3,f0,f1), shipped `run/frames_hi/frame_00..03.png` and `run/frames/frame_00..03.png`.

- The lit (near) leg is the leading leg in **all four** frames: its skin-component centroid x = 341 (f0), 294 (f1), 331 (f2), 342 (f3), while the shadowed (far) leg centroid stays at x = 231 / 231 / 235 / 231. The far leg never crosses in front of the near leg in any frame; only the amount of knee bend changes.
- No vertical motion at all: content top = y 84 and bottom = y 503 in f0, f1, f2 and f3, so the body does not rise or fall during the stride (a run needs a 5–15 px bounce at this 420 px body height).
- Only one arm is visible in all four frames; the near hand stays parked at the hip (x 240–286, y 334–362 across the four frames) and the far arm never enters the silhouette, so there is no arm cycle.
- The wrap f3→f0 lands the near foot on the ground again (both frames bottom = 503 with the near foot planted), so the loop stutters rather than continuing the stride.

Broken requirement: shipped `run 4-frame cycle`, check #4 “22 run cycle alternating”, and “coherent motion / no popping”. The 3D truth for the same action (`12_run_3d_truth_all.png`) does alternate the legs, so the sprite contradicts its own pose reference.

### B2 — Roll: the stowed katana is drawn in front of the body and detaches from the back
Files: `10_roll_hi_all.png` f2–f6, shipped `roll/frames_hi/frame_02..06.png` (and 64 equivalents).

- f4: the hilt + tsuba sit at her chin/neck (x ≈ 180–212, y ≈ 360–382) and the scabbard runs across her abdomen and shorts, drawn **on top of** the torso (chape at x ≈ 380, y ≈ 420).
- f5: the hilt + tsuba are on her chest (x ≈ 250–305, y ≈ 390–460) and the scabbard is drawn over her hair and thigh (`frame_05.png`).
- f2/f3/f6: the scabbard body is painted over the hair fan (`frame_03.png`, rod runs from ≈(200,407) to ≈(382,342) across the hair).
- A sheathed katana worn across the lower back must be behind the body and behind the hair. Here it reads as a floating rod lying on her chest, i.e. the exact “slab / floating scabbard” the check forbids.

Broken requirement: “Weapons stowed when unused”, check #7 “stowed katana attached and correctly scaled, no slab/floating scabbard”.

### B3 — Roll is not a forward roll: it re-inverts after standing up (seated → inverted → standing)
Files: `10_roll_hi_all.png` f3/f5/f6, shipped `roll/frames_hi/frame_03.png`, `frame_05.png`, `frame_06.png`.

- Sequence read from the frames: f0 stand → f1 crouch → f2 inverted (head bottom-right) → f3 inverted (head bottom-left) → f4 on her back (head left, legs up right) → **f5 seated upright** (head right, knees up) → **f6 fully inverted again** (head at the bottom, y ≈ 455) → f7 stand.
- f5→f6 is a ~180° flip in one frame, and f6→f7 is another ~180° flip back to standing.
- f6 is a near-copy of f3: 13,187 differing px (5.0 % of the canvas), while every other non-adjacent pair in the roll is 40,000–60,000 px (f2↔f5 = 43,493; f4↔f6 = 42,124). The back half repeats the mid-roll inversion instead of coming up out of it.

Broken requirement: check #7 “reads as a forward roll … no seated/inverted pop at the end”, “no popping”.

### B4 — 64 px violet eye is not intact; it alternates violet / pale / absent
Files: `11_idle_64px_all.png` f2, f3, f6, f7; shipped `idle/frames/frame_02.png`, `frame_03.png`, `frame_06.png`, `frame_07.png`.

At 64 px the iris colour `#714a9c` survives in only 4 of the 8 idle frames:
- f0 (35,16), f1 (35,16), f4 (35,16), f5 (35,16) = 1 violet px (acceptable);
- f2 = one `#dbbcff` pixel at (35,17) only (pale lavender, no iris) — reads as a punched-out/white eye;
- f3, f6, f7 = **zero** violet pixels anywhere in the face (the eye is a light/pale block).

Cause (verified): `frames/` is a bit-exact 1/8 nearest-neighbour downsample of `frames_hi/` (0 differing px per frame), so the 512 art’s ~4×6 px iris collapses to 0–1 px and lands differently every frame. The 512 eye is correct in all 40 frames; the game-resolution eye is not.

Broken requirement: “The violet eye must be intact (not punched out)”, “consistent identity … 64px”.

---

## MAJORS

### M1 — Idle ships 8 frames but only 4 unique poses; the “bob” is a 1-px whole-sprite translation
Files: `10_idle_hi_all.png` f0–f7, shipped `idle/frames_hi/frame_00..07.png`.

Verified exact: f4 = f0 shifted **+1 px** down, f5 = f1 shifted **−1 px** up, f6 = f2 **+1 px**, f7 = f3 **−1 px** (0 differing px after the shift). Consequence: f0–f3 replay in the second half with the whole character (feet included) moved up/down, so the ground contact oscillates between y = 502 and y = 504 (2 px at 512) and the loop visibly repeats the same four poses twice.

Broken requirement: shipped `idle 8` (frames), “no popping”.

### M2 — Slash2 f4 and f5 end in a blunt/truncated blade
Files: `10_slash2_hi_all.png` f4, f5; shipped `slash2/frames_hi/frame_04.png`, `frame_05.png`.

- f4: the blade terminates in a **flat vertical cap** at x = 503 (8 px inside the 512 canvas), 6 rows tall with square corners — no kissaki. The blade length (≈225 px) matches f2/f5, so this is a drawn flat cut, not perspective.
- f5: the blade terminates in a **straight diagonal chisel cut** (~19 px long), again no kissaki.
- f1 and f6 have a correct pointed kissaki, so the tip shape is inconsistent within one 8-frame action.

Broken requirement: check #8 “blade tip not truncated”, “full length”.

### M3 — The pistol is never readable when stowed
Files: all 40 frames (`10_idle_hi_all.png`, `10_run_hi_all.png`, `10_slash2_hi_all.png`, `10_roll_hi_all.png`); same object unchanged in `10_shoot2_hi_all.png` f1–f6.

The right-hip item in every non-shoot frame is a featureless rounded grey block (~23×21 px at 512 in idle f0 at x 291–314, y 336–357) with no grip, slide, barrel or trigger guard. The same unchanged block is present in shoot2 f1–f6 while the pistol is in her hand, so the holster neither shows a stowed pistol nor visibly empties. `01_char_ref_64_x16.png` does contain a distinct far-hip item that never appears in any shipped frame. A player sees a katana and a pouch, not “pistol holstered at the right hip”.

Broken requirement: “pistol holstered at the right hip”, “exactly ONE pistol”, “holster stays visible but EMPTY”.

### M4 — 64 px art is a raw 1/8 downsample: mottled interiors, pinholes, unreadable roll
Files: `11_idle_64px_all.png`, `11_run_64px_all.png`, `11_roll_64px_all.png` (and 512 counterparts for the cause).

- The 64 frames are an exact nearest-neighbour downsample of the 512 art (verified 0-px diff), so fine shading becomes single-pixel speckle across the torso, hair and sleeves at game resolution.
- The downsampling leaves 1-px transparent pinholes enclosed by the silhouette, e.g. idle f0 at (31,30)-(31,31) and f4, shoot2 f1 at (39,21), run f3 at (30,30)-(30,32) — visible as dark dots inside the chest/arm.
- Roll f2–f6 at 64 collapse into amorphous blobs (hair + limbs + scabbard merge); the tuck cannot be read without the 512 art.

Broken requirement: “readable silhouettes at 64px”, “commercial quality”.

---

## MINORS

1. **Slash2 f1 blade is 28 % shorter than the rest.** Blade component extent: f1 163 px, f2 226, f3 193, f4 225, f5 226, f6 195. f1 is 0.39 body height vs 0.54 for f2/f4/f5 — inconsistent for a straight in-plane swing. (`10_slash2_hi_all.png` f1.)
2. **Slash2 f3 grip/orientation.** The sword arm is extended forward while the blade points back-down across her own thigh (wrist ≈135° from the forearm); it reads as a backwards hold and the blade overlaps the near thigh. (`10_slash2_hi_all.png` f3.)
3. **Scabbard mouth reads as a stray metal hook.** A ~20 px silver L-shape sits at the belt in every frame (idle f0 around (300,255), slash2 f2 around (330,285)); at 512 it looks like a loose piece of hardware rather than a koiguchi/habaki. (`10_idle_hi_all.png` f0, `10_slash2_hi_all.png` f2.)
4. **Violet rim on the inner leg.** The inner leg/armpit contour is outlined with `#9169c4` instead of the standard dark outline (idle f0–f7, run f0–f3), leaving a bright 1-px violet line down the leg gap that draws the eye to a negative space.
5. **Blade/gun sit 1–2 px from the canvas edge at 64.** Slash2 f1/f4 last opaque column = 62, shoot2 f1–f6 = 61 (canvas indices 0–63). Technically not clipped, but there is no safe margin and it reads as running off the frame in `10_slash2_hi_all.png` / `10_shoot2_hi_all.png` at 512 (last opaque column 503 / 499).
6. **Design/cross-action sheets do not show the shipped weapon states.** `00_design_sheet.png` is a display pose (drawn katana in hand **and** scabbard **and** pistol), and `20_cross_action.png` only uses anchor frames, so run/slash2/shoot2 f0 are the same image and roll f0 = idle f0 — the sheet proves nothing about weapon-state consistency.
7. **MANIFEST hash scope is wrong.** The six SHA-256 values are the file hashes of the **64 px** `frames/frame_0N.png`, not the 512 `frames_hi/` frames shown in the `10_*` sheets; the resolution is not stated.
8. **Truth sheets use a magenta matte** (`#FF00FF` family) in all five `12_*_3d_truth_all.png`; harmless as a pose reference, but it trips any “no magenta” palette check. The truth’s slash blade is also a thin short stick, far from the sprite blade.

---

## Frames actually opened (per action)

- **idle** — 512: f0–f7 in `10_idle_hi_all.png`, with f0–f5 additionally at 2× as pairs and f0/f1, f2/f3, f4/f5, f6/f7 compared for duplicates; 64: f0–f7 (all, individually at 24× face crops and in `11_idle_64px_all.png`). Extra zooms: head 4×, hip 8–14×, legs 6×, scabbard mouth 12×.
- **run** — 512: f0, f1, f2, f3; 64: f0–f3 (`11_run_64px_all.png`); `22_run_loop.png`.
- **slash2** — 512: f0, f1, f2, f3, f4, f5, f6, f7; 64: f0–f7 (`11_slash2_64px_all.png`); tips zoomed 14–16× for f1, f3, f4, f5, f6; waist zoomed for f1, f2, f3, f5.
- **shoot2** — 512: f0, f1, f2, f3, f4, f5, f6, f7; 64: f0–f7 (`11_shoot2_64px_all.png`); gun hand zoomed 7–16× for f1 and f3; hip/holster zoomed 8–14× for f0, f1.
- **roll** — 512: f0, f1, f2, f3, f4, f5, f6, f7; 64: f0–f7 (`11_roll_64px_all.png`); full-body zooms 3–5× for f3, f4, f5.
- **other packet files** — `MANIFEST.md`, `00_design_sheet.png`, `01_char_ref_64_x16.png`, `02_part_katana.png`, `02_part_scabbard.png`, `02_part_pistol.png`, `12_idle/run/slash2/shoot2/roll_3d_truth_all.png`, `20_cross_action.png`, `21_transition_pairs.png`, `22_run_loop.png`, `23_transition_diff.png`.
- **shipped frames opened directly** — `idle/frames_hi/frame_00`, `idle/frames/frame_00,02`; `run/frames_hi/frame_00,01,03`; `slash2/frames_hi/frame_01,03,04`, `slash2/frames/frame_03`; `shoot2/frames_hi/frame_01,03`, `shoot2/frames/frame_02`; `roll/frames_hi/frame_02,03,04,05`, `roll/frames/frame_02`.

---

## Verified good (measured, so it does not need re-review)

- **One katana, one scabbard, one pistol, one hilt** in every frame of all five actions; no second blade, hilt, gun, dagger or shield anywhere. Slash2’s scabbard is empty (no second hilt); shoot2’s katana stays sheathed.
- **Transitions are byte-identical** at 512 and 64: run:0 ≡ slash2:0 ≡ shoot2:0; run:3 ≡ slash2:7 ≡ shoot2:7; idle:0 ≡ roll:0; idle:7 ≡ roll:7; `23_transition_diff.png` is genuinely all-black.
- **No clipping, no fragments, no neighbour-panel bleed:** every frame is a single connected alpha component; content stays inside x 83–503, y 84–503 at 512 and x 10–62, y 10–62 at 64 in every frame. No stray pixels.
- **Flat palette, no anti-aliasing:** 24–37 flat colours per 64 frame, 45–52 per 512 frame, hard 1-px edges, fully transparent background.
- **512 identity is consistent:** silver hair, violet iris, short-sleeve top, detached forearm sleeves, shorts, boots and head size match across actions and frames; the violet eye is intact at 512 in all 40 frames.
- **Parts are correct single objects:** `02_part_katana.png` is one full-length katana (kissaki, tsuba, wrapped tsuka), `02_part_scabbard.png` one straight sheath with chape, `02_part_pistol.png` one complete pistol.
- **Cross-action scale is constant** (`20_cross_action.png`), and all six anchors land on the same body height.
- **Roll starts on idle f0 and ends on idle f7** (pixel-identical), and the katana is never drawn (blade never leaves the scabbard) during the roll.

---

## Bottom line

The weapon-instancing and eye-at-512 work from the previous round holds: there is exactly one katana, one scabbard and one pistol, the anchors are exact, and the silhouette is complete and unclipped everywhere. It still cannot ship: the run never alternates its legs and has no bounce or arm swing (B1), the roll carries the sheathed katana across her chest and re-inverts after standing up (B2/B3), and the 64 px art loses the violet eye in half the idle frames (B4). Fix B1 by mirroring the second step, re-parent the roll stow behind the body/hair and rebuild f5–f7 as a continuous rise, and repaint (not downsample) the 64 px head so the iris is a stable 1–2 px violet block — then re-run this packet.
