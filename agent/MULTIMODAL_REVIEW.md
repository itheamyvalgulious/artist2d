# Multimodal acceptance review

This project deliberately has **no code unit tests**. A green script is not
evidence that the art looks right. Every shipped asset is inspected visually by
an independent subagent.

## Reviewer

- Model: `dawnfm/deepseek-v4.1-flash-1017`
- Reasoning effort: `high`
- Must be a fresh subagent, not the generation session.
- Tools: `read` on the PNGs; may use `glob`/`shell` to list files, but must not
  modify assets or regenerate images.
- Report: write `output/reviews/<area>_review_vN.md`.

## 100% coverage rule

1. Build the review packets:

   ```bash
   .venv/bin/python scripts/build_review_packets.py
   ```

2. The character packet (`work/review/character/`) expands **all eight frames**
   of every action at 512px, all eight 64px game frames (8x nearest), and the
   3D mannequin truth for the same eight frames. It also contains cross-action
   consistency, every transition-anchor pair, a pixel-difference proof, and the
   run-cycle wrap.
3. The ship packet (`work/review/ship/`) contains the complete 22-tile atlas,
   all three medium structures, all three mega elements, the whole-ship
   assembly and the showcase.
4. The reviewer must open **every file** in the packet. Sampling a few frames is
   not acceptable. If a contact sheet is ambiguous, open the original frames.
5. The review must also cover the **3D truth → final** chain: compare each
   action's final frames with its mannequin sheet. A final frame that diverges
   from the 3D pose is a finding.

## Character checklist

- Identity: female cyberpunk agent, long silver hair, violet eyes, beautiful,
  short-sleeve top + detached sleeves + shorts, black boots, dark navy /
  gunmetal / silver / cyan / violet palette. Not the knight, not a man.
- Weapons: full-length katana + dark scabbard + compact pistol. Stowed when not
  in use: katana on the back, pistol on the hip. Katana drawn only in slash;
  pistol in hand only in shoot. No duplicates, no shield, no dagger, no
  shortened blade.
- Weapon parts sheet: separate full katana, empty scabbard, pistol; readable
  blade, guard, grip, barrel, trigger guard.
- Actions: idle breathing; run self-loop; slash2 running slash; shoot2 running
  shot with a horizontal pistol; roll forward somersault that starts/ends in
  idle and stays in frame.
- Consistency: same face, hair length, outfit, body proportions and scale in
  every action and frame; no missing/extra limbs; no floating pieces; no
  magenta blocks; no anti-aliasing/blur.
- Transitions: `run:0` / `run:7` anchors for slash2 and shoot2; `idle:0` /
  `idle:7` anchors for roll; the run cycle must wrap without a pop.
- Report every issue as BLOCKER / MAJOR / MINOR with the exact file and frame.

## Ship checklist

- Style: side-view pixel-art sci-fi + cyberpunk spaceship interior; coherent
  gunmetal / navy / cyan / violet / hazard palette, crisp pixels, no blur.
- Tiles: all 22 complete, side-view, usable at 32px, no magenta, no seams in
  the sample.
- Medium structures: console bank, cargo stack, server rack; complete,
  grounded, readable, style-consistent.
- Mega elements: hull frame, viewport, reactor core; complete modular
  side-view, style-consistent.
- Whole-ship assembly + showcase: everything grounded, no clipping, no missing
  tiles, consistent floor line, character correctly scaled and grounded, enough
  variety; flag copy-paste repetition where it hurts readability.
- Report every issue as BLOCKER / MAJOR / MINOR with the exact file/tile.

## Fix loop

If any BLOCKER or MAJOR is found:

1. Fix the source (prompt, 3D pose, extraction, composition), not the review
   packet.
2. Rebuild the affected assets and the review packet.
3. Re-run the **full chain** review, including the 3D mannequin truth and the
   cross-action consistency sheet, not only the changed frame.
4. Write a new report (`v2`, `v3`, ...). Do not overwrite the old report; the
   history is part of the evidence.
