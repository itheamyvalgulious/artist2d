# Acceptance review — character pack “agent” (v3)

**Verdict: FAIL**

4 blockers, 3 majors, 6 minors.

Reviewed independently. I did not build these assets. Every PNG in
`/dat/projects/artist2d/work/review/character/` was opened, and because the packet
turned out not to be pixel-faithful (major M3), I also opened and measured the
shipped frames under `/dat/projects/artist2d/output/character/agent/` directly.

---

## What I checked, and how

- Opened all 24 PNGs in `work/review/character/` (design sheet, 01 ref, 3 weapon
  parts, five `10_*` 512 sheets, five `11_*` 64px sheets, five `12_*` 3D truth
  sheets, `20`, `21`, `22`, `23`).
- Opened the shipped per-frame PNGs for every action
  (`idle/frames[_hi]/frame_00..07`, `run/…/frame_00..03`,
  `slash2/…/frame_00..07`, `shoot2/…/frame_00..07`, `roll/…/frame_00..07`).
- Re-computed: SHA-256 per frame, alpha values, opaque bounding boxes, border
  contact, connected components, enclosed transparent regions, consecutive-frame
  change counts, and the 512→64 nearest-downsample relation.
- Cross-checked the 3D truth only as a pose reference, as instructed.

Baseline facts (all confirmed):

- Frame counts are 8 / 4 / 8 / 8 / 8, at 512×512 and 64×64.
- Every 64px frame is an exact nearest 8× downsample of its 512px frame
  (0 differing pixels), but with a **(4,4) registration offset** (minor m2).
- Alpha is binary (0/255) everywhere; no semi-transparent edge halo.
- Each frame has exactly one opaque connected component; no stray fragments from
  neighbouring panels.
- Transition anchors are pixel-identical (SHA-256):
  - run f0 `d1cd5e55…` = slash2 f0 = shoot2 f0
  - run f3 `2d748418…` = slash2 f7 = shoot2 f7
  - idle f0 `6a5dc8df…` = roll f0; idle f7 `2bffd7cf…` = roll f7
  - `23_transition_diff.png` is genuinely all black.
- `02_part_katana.png` (58×485) is a complete katana (angled tip, guard, wrapped
  grip, pommel). `02_part_scabbard.png` (52×461) has caps at both ends.
  `02_part_pistol.png` (117×88) has slide, barrel, trigger guard and grip.
- The run is a real 4-frame alternating cycle (four distinct leg configurations).

---

## Blockers

### B1 — `slash2` frame 3 is cut off by the frame edge

**Files**
`output/character/agent/slash2/frames_hi/frame_03.png` (512px)
`output/character/agent/slash2/frames/frame_03.png` (shipped 64px)

**What is wrong**
- The opaque bbox is `x = 0 … 505`, `y = 84 … 503`. Column `x=0` is opaque for
  82 pixels: a contiguous run `y = 352–367` (scabbard fill `#382456`) and a
  contiguous run `y = 419–484` (rear boot), with 452 opaque pixels inside
  `x ≤ 5`.
- The scabbard’s silver end cap, visible in every other slash2 frame (f4 near
  `x=75`, f5 near `x=175`), is **absent**; the dark scabbard runs straight off
  the left edge.
- The rear boot is similarly sliced by the left edge.
- The defect survives downsampling: the shipped 64px frame has 9 opaque pixels
  in column 0 (frames 2 and 4 have 0).
- The same frame also ends its blade at `x = 505` (11 opaque pixels at
  `x ≥ 505`), only 6 px from the right edge; see M1.

**Requirement broken**
“Every frame complete: no cropped head/hair/hand/boot/blade at the frame edge”,
and the source spec’s “must never touch or cross the panel edge”.

**Review-packet caveat:** the packet’s `10_slash2_hi_all.png` cell 3 shows an
8px margin at the left because the packet is inset/scaled (M3). The clip is
visible only in the shipped frame. Do not accept the packet’s margin as proof.

---

### B2 — `slash2` contains two katana hilts: the sheathed katana is never removed

**Files**
`slash2/frames_hi/frame_01.png`, `frame_02.png`, `frame_03.png`,
`frame_05.png`, `frame_06.png` (and the matching 64px frames)

**What is wrong**
In every one of these frames the character holds a drawn katana **and** a
complete sheathed katana hilt (pommel + wrapped grip + tsuba) is still sitting
at her right waist:

- f1: drawn sword overhead (grip in the raised hand, ≈`x330,y85`); second hilt
  at the waist ≈`x300–395, y205–290`.
- f2: drawn sword above the head; second hilt ≈`x310–390, y285–350`.
- f3: drawn blade at full forward extension; second hilt ≈`x185–250, y235–295`.
- f5: drawn sword in the hand at ≈`x300,y300`; second hilt ≈`x295–360, y240–295`.
- f6: drawn sword low in the hand; second hilt ≈`x325–380, y245–305`.
- f4: no stowed hilt is visible — so the extra weapon **pops in and out** between
  adjacent frames.

The 00 design sheet correctly shows an empty scabbard when the katana is drawn;
the animation does not.

**Requirement broken**
“Exactly ONE katana, ONE scabbard, ONE pistol; no shield, no second
blade/hilt/gun/dagger”; the source spec’s “never duplicate a weapon”.

---

### B3 — `roll`: the stowed katana leaves its mount and crosses the body

**Files**
`roll/frames_hi/frame_04.png`, `frame_05.png`, `frame_06.png`
(and the matching 64px frames)

**What is wrong**
- f5: the sheathed katana’s hilt (pommel, wrapped grip, tsuba) is at the **left
  shoulder/neck** (≈`x150–185, y225–300`), ≈100–130 px above the waist position
  it occupies in idle. The scabbard then runs diagonally across the front of the
  torso and shorts to ≈`x300,y435`.
- f6: the hilt is beside her **ear/cheek** (≈`x325–360, y235–305`), with the
  scabbard crossing her hair/upper back down-left. Relative to the chin, the
  hilt has moved from ≈50 px below the chin in idle to ≈25–60 px above it in
  f5/f6 — a 75–110 px slide (≈18–26 % of body height).
- f4: the whole sheathed katana is laid out horizontally across the near side of
  the hips (hilt ≈`x140,y370`, silver cap ≈`x442,y395`), overlapping the
  shorts/thigh and reading as a detached plank rather than a back-mounted
  scabbard; the hilt is ≈110 px behind the hip.
- The 3D truth keeps the scabbard at a fixed offset on the torso through the
  same frames; the art does not.

**Requirement broken**
Requirement 7: “stowed katana/hair attached and correctly scaled (flag any
detached/floating or slab-like scabbard)”, plus “same … weapon” consistency.

---

### B4 — `roll` does not read as a forward roll, and is unreadable at 64px

**Files**
`roll/frames_hi/frame_02.png`, `frame_03.png`, `frame_04.png`,
`frame_05.png`, `frame_06.png` (512px)
`roll/frames/frame_02.png`, `frame_03.png`, `frame_04.png`,
`frame_05.png`, `frame_06.png` (shipped 64px)

**What is wrong**
- f5 and f6 are **seated** poses: hips down, torso upright, both boots raised
  and extended to screen-right. They are not the landing-crouch/roll-exit pose.
  The pose reference for f5/f6 shows the body still horizontal/curled with the
  head at the opposite end; the art has already sat up, so the 360° rotation
  is not completed.
- f6 (hair top `y≈178`) → f7 (standing, hair top `y≈85`) is a seated-to-standing
  jump in one frame.
- At 64px, `frame_02` and `frame_03` are indecipherable tangles of hair, skin,
  boot and scabbard; `frame_04` is a mass of skin and black; `frame_05/06` read
  as a seated blob. The only legible element is the long dark scabbard crossing
  the body. This fails at actual game resolution even though the 512px versions
  are (barely) parseable.
- Consecutive-frame change counts confirm the churn: the mid-roll 64px steps
  change 1027–1290 pixels of an ~800–990-pixel silhouette, i.e. essentially the
  whole sprite is redrawn per frame with no stable read.

**Requirement broken**
“Roll: reads as a forward roll with a complete body”; “readable silhouettes at
64px”; “coherent motion, … no frame-to-frame popping”.

---

## Majors

### M1 — `slash2` f3 blade tip is blunt / truncated

**File** `output/character/agent/slash2/frames_hi/frame_03.png` (512px) and
`output/character/agent/slash2/frames/frame_03.png` (shipped 64px)

The blade ends in a flat vertical edge at `x = 505` (rows `y = 199–213`), only
6 px from the frame edge. Every other drawn frame has a tapered kissaki
(compare f4, whose tip is correctly angled). `02_part_katana.png` also has a
tapered tip. The blunt end reads as a clipped/truncated blade.

**Requirement broken** “full length, correct blade” (item 8), “no cropped …
blade at the frame edge” (item 1).

---

### M2 — `slash2` blade reverses direction between f3 and f4

**Files** `output/character/agent/slash2/frames_hi/frame_03.png` →
`output/character/agent/slash2/frames_hi/frame_04.png`

- f3 tip: ≈`(505, 205)` — full forward extension at chest height.
- f4 tip: ≈`(418, 110)` — blade vertical, 87 px back and 95 px up in one frame
  (≈90° reversal).
- f5 then goes down-forward again (≈`(410, 390)`).

The source arc requires the blade to continue forward and down from the
extension; here it snaps back up for one frame and then cuts down a second time.
At 64px the f3→f4 change is 1384 px (the largest transition in the set), so it
reads as a pop rather than a follow-through.

**Requirement broken** “coherent motion … no frame-to-frame popping”; the source
arc spec (“continue forward and down”, “never swing backwards”).

---

### M3 — the review packet is not a 1:1 / 8× copy of the shipped frames

**Files** every `10_*_hi_all.png` and `11_*_64px_all.png`

The packet cells are inset and scaled to approximately **496/512 = 0.96875**
and offset by about `(8,7)` — not 1:1 (10_*) or 8× (11_*). The measured
ratios (0.968–0.969) are consistent with a 496 px inset in a 512 px cell:

- `10_slash2_hi_all.png` cell 3 content bbox `(8,89)–(497,495)` vs the shipped
  `(0,84)–(505,503)`; width 490 vs 506, height 407 vs 420 (ratio 0.968–0.969).
- `11_idle_64px_all.png` cell 0 content bbox `(132,86)–(371,495)` vs the 64px
  frame upscaled 8× `(128,80)–(375,503)`.
- The 8× upscale is therefore not block-pure: 7–15 px runs instead of 8/16, and
  451 of 4096 8×8 blocks are non-uniform.
- Palette values differ between packet and shipped frame at the same sprite
  coordinate (e.g. packet `(214,214,230)` where the shipped frame has
  `(155,155,176)`) because the resample samples a different source pixel.

Consequence: the packet **cannot** be used for edge/margin, pixel-identity or
64/512 equality verdicts. In particular it hides B1’s `x=0` clip behind 8 px of
inset margin. The manifest’s “11_* = the matching 64px game frames upscaled 8x”
is inaccurate.

**Requirement broken** the packet’s own claim (“review copies of shipped
assets”) and item 3’s pixel-identity evidence standard. This is a
delivery/QA defect, not a pixel defect of the game frames themselves.

---

## Minors

### m1 — idle has duplicate frames (6 unique poses, not 8)

`output/character/agent/idle/frames_hi/frame_04.png` is byte-identical to
`frame_00.png`, and `frame_06.png` is byte-identical to `frame_02.png` (same
SHA-256; the 64px copies likewise). The
8-frame idle therefore repeats two poses mid-loop (sequence A B C D A E C F),
which reads as a hold/stutter. Item 10 (“no frame-to-frame popping”) is not
outright broken, but a commercial 8-frame idle should not contain exact
duplicates.

### m2 — 64px and 512px frames are not registered to the same origin

The 64px frame is an exact nearest downsample of the 512px frame only at
`dx=4, dy=4` (0 differing pixels at that offset; 394–671 differing pixels at
0,0). Content is identical, but the two resolutions are shifted a half
low-res pixel. Mixing the two in one game (e.g. 512 store art vs 64 gameplay)
will not anchor identically.

### m3 — violet eye is not readable at 64px

The 512px eye is a dark plum/violet almond (palette `(82,53,116)` /
`(113,74,156)` / `(145,105,196)`). At 64px it collapses to 1–2 pixels of
near-black plum — e.g. idle `(56,36,86)`/`(36,24,56)`, run f0 `(36,24,56)` /
`(21,15,34)`; a medium violet `(82,53,116)` survives in a few frames but the
bright iris highlight does not. At game resolution the eye reads as a dark dot,
so the “violet eyes” identity cue is not visible. (Item 1 / identity.)

### m4 — run arm swing is nearly static

In all four run frames the far arm stays bent with the hand at the chest and
the near arm stays down over the holster; only the legs alternate. The legs
are a real cycle (item 22 passes), but the upper body reads stiff against the
spec’s “arms pumping”.

### m5 — `slash2` wind-up is behind the head

f1 and f2 hold the katana above/behind the head with the blade pointing
screen-left (behind her); the tip only reaches the forward extension at f3.
The concept’s arc requires the first drawn frames to be “raised high in front of
the chest” and “never swing backwards behind her body”. Combined with M2, the
8-frame arc is effectively two half-cuts rather than one clean slash.

### m6 — `01_char_ref_64_x16.png` does not depict the shipped character

The packet’s 01 image is a 16× blow-up of `char_ref_64.png`, a rough concept
figure with a white cap of hair, a different outfit (magenta/purple shorts,
cyan accents), different proportions and a sword held in front. It is clearly an
input reference, not the game sprite, but it is shipped in
`output/character/agent/` and listed in the packet without a “concept input”
label. If a customer receives it as a character reference it is a direct
identity contradiction. (Not used by any game frame.)

---

## Items that pass (for the record)

- **Item 1 (per-frame completeness, except B1):** every other frame is fully
  inside its 512/64 cell — minimum margins are 8 px at the bottom, ≥6 px at the
  right, ≥69 px at the left, and no other frame touches a border. No missing
  limbs, no enclosed transparent holes inside a limb (the detected enclosed
  regions are the normal gaps between legs/arm and torso), no neighbour-panel
  fragments.
- **Item 2 (cross-action identity/scale):** idle / run / slash2 / shoot2 / roll
  anchors share the same head size, body height, hair length, outfit colours and
  silhouette scale; `20_cross_action.png` is consistent.
- **Item 3 (transition anchors):** six of six pairs are pixel-identical
  (SHA-256 above); `23_transition_diff.png` is all black and consistent with the
  real hashes. Roll starts/ends exactly on idle f0/f7.
- **Item 4 (run cycle):** four distinct, alternating strides; no two of the four
  frames are duplicates.
- **Item 5 (design sheet / parts):** the 00 sheet shows the full-length katana,
  the scabbarded back carry, the pistol and the outfit; the three 02 parts are
  complete and correctly proportioned (tip, guard, grip, pommel; scabbard caps;
  pistol slide/barrel/trigger guard/grip).
- **Item 6:** the 3D truth was used only as a pose reference; the verdict is
  based on the drawn pixels.
- **Item 8 (partially):** in slash2 f1–f6 the katana is gripped in the hand (the
  fist is on the handle, the guard is outside the fist), and the scabbard
  remains on the back. The blade reaches full length in every drawn frame, but
  f3’s tip is blunt (M1). Failures are B1/B2/M1/M2.
- **Item 9:** in shoot2 f1–f6 the pistol is complete and readable — slide, cyan
  sight, barrel, trigger guard and grip all present, hand on the grip; the
  katana stays sheathed. I found no second pistol: the hip holster reads empty
  when the pistol is drawn. f0/f7 are the run anchors with the pistol holstered,
  as specified.
- **Weapon state:** katana sheathed in idle/run/shoot2/roll, drawn only in
  slash2; pistol holstered in idle/run/slash2/roll, in hand only in shoot2 f1–f6.
  No shield, no second blade, no dagger.
- **Alpha quality:** binary alpha, no anti-aliasing halo, no colour bleed at the
  silhouette.

---

## Frames actually opened

Individual 512px frames were opened at full size (and, for the flagged frames,
at 2×–10× nearest zoom); the 64px counterparts were opened both in the `11_*`
sheets and, for the flagged frames, as individual 16×/1:1 inspections.

| Action | 512px frames opened | 64px frames opened | Extra zoom inspections |
|---|---|---|---|
| idle | 0–7 via `10_idle_hi_all.png`; 0 and 1 also full-size | 0–7 via `11_idle_64px_all.png`; 0 at 16× | face 0 at 6×/24×; hip 0 at 6×; diff f0↔f2 |
| run | 0–3 via sheet; all four at 2× | 0–3 via sheet | f0–f3 full-body 2× |
| slash2 | 0–7 via sheet; 1,3,4,5 also full 512 | 0–7 via sheet; 3 at 16× | waist/hilt f1–f6 at 4–8×; hand f1/f2/f4/f6 at 5–8×; f3 left/right edges at 6–10×; tips f4/f5 at 8× |
| shoot2 | 0–7 via sheet; 1,2,3,5,6,7 crops | 0–7 via sheet; 3 at 16× | gun/hip f1–f6 at 4–10× |
| roll | 0–7 via sheet; 1–6 at 2× | 0–7 via sheet; 2,3,4,5,6 at 16× | f2/f4/f5/f6 at 3–4×; f5 grid; f6 head/hilt at 4×; 64px strip |
| other | 00, 01, 02×3, 12×5, 20, 21, 22, 23 (all opened) | — | — |

Frames 0 and 7 of every 8-frame action are the hash-verified transition
anchors, and were additionally seen in the idle/run sheets at both resolutions.

---

## Bottom line

**FAIL.** The pack cannot ship as-is.

The blocking issues are: a genuinely clipped frame (`slash2` f3), a duplicated
stowed katana in the slash (`slash2` f1/f2/f3/f5/f6), and a roll whose stowed
katana slides to the shoulder/ear and whose f2–f6 beats do not read as a
forward roll at 64px. The transition anchors, frame counts, run cycle, weapon
parts and shoot2 pistol all pass; fixing the four blockers (plus M1/M2, and
regenerating a faithful 1:1/8× packet) would make the pack a credible candidate
for a re-review.
