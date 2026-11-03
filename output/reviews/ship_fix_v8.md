# Ship Environment — Fix Pass v8

Scope: the ship pack only — `environment/ship_assembly.py`, `scripts/build_ship.py`,
and the ship outputs (`output/environment/ship/`, `output/mega/ship/`,
`output/showcase/ship/`). No character file was modified; `work/review/` was not
written (the packet rebuild is yours). 25 tiles, 3 medium + 3 mega types, the three
isolation directories unchanged.

This report does **not** claim PASS.

## Rebuild / verify

```bash
.venv/bin/python scripts/build_ship.py      # deterministic, no API key, no AI call
.venv/bin/python scripts/verify_ship_v8.py  # prints every number quoted below
```

Ship layer byte-identical across consecutive builds; `scene_1x.png` is 0 px
different from a fresh `compose(include_character=True)` on the frame in the tree.

---

## Major — the dais now has a contact footprint (M1) — FIXED

`compose()` appends the dais to the shadow list exactly like the pad:

```python
shadows.append((dais_x0, np.full(dais_x1 - dais_x0, 3, dtype=int),
                FLOOR_ROW * TILE_SIZE + DECK_LIP))
```

Measured with the same no-shadow diff (shipped scene vs `compose()` with
`_shadow` patched to a no-op), rows 514–516:

| platform | base | v7 | v8 |
|---|---|---|---|
| dais (x=480–671) | row 511 | **0 / 0 / 0** | **192 / 120 / 72** |
| reactor pad (x=1232–1391) | row 511 | 192 / 120 / 72 (6 tiles wide) | **160 / 100 / 60** (5 tiles) |

Row 514 of the scene now carries six runs: 58 (3-crate), 58 (2-crate), **192
(dais)**, 52 (server), 18 (agent), 160 (pad) = **538 px** (v7: 378). Total shadow
pixels: mega **1587** (v7: 1267), scene **1618** (v7: 1298) — the dais adds 384,
the narrower pad removes 64.

The dais’s own tread stays untouched: rows 480–483 have **0** changed px, and the
console’s shadow still starts at 484 on the riser.

---

## Minors

1. **The hidden window is back.** The window moved from (8,6) — which the conduit
   at tile 8 covered 100 % — to **(7,6)** (x=224–255), immediately left of the
   conduit. The cell now shows the full 14-colour window (frame, graded glass,
   planet, mullion, sill glow); the conduit and the bay accents are unchanged.
2. **The reactor pad is tightened to 5 tiles**: 160 px at **x=1232–1391**,
   centred in the 6-tile bay (16 px of wall left and right), reactor at
   x=1253–1370 with 21 px of pad on each side (v7: 192 px pad, 37 px margins).
   The hazard face is drawn per cell with a cropped 32-px slice, so the 45°
   diagonal still runs continuously across the pad.
3. **The five ribs are no longer identical**: `_service_band()` now has three
   variants (louver pitch 6 / 7 / 4 rows, cyan tick vs warm status dashes +
   bracket vs low cyan bar + bolt row), distributed palindromically
   **(0, 1, 2, 1, 0)** across x=0/10/22/34/44. Sleeve hashes:
   `3ded74bc / 34af551b / 3a8d4478 / 34af551b / 3ded74bc` (3 unique). Every
   variant keeps the lit-left / shaded-right columns, so the light direction and
   the 1:1 448-px module are unchanged.
4. **The pad’s top edge now matches the dais**: the v7 pad had a pure-black
   overhang row; rows 480–483 now read **156.5 / 112.8 / 112.8 / 79.5**, the
   same as the dais tread, so the two platforms have identical top edges.
5. **6× shadow plate added**: `output/showcase/ship/scene_shadows_x6.png`
   (2850×510) shows the dais + console and the reactor pad side by side at 6×,
   palette-safe (0 violations). It complements the 4× `scene_focus_x4.png`.
6. **Report corrections** (this report): shadow totals are given per render
   (mega 1587 / scene 1618); the bay accents are quoted as **256 cyan / 256
   violet pixels per bay** over y=96–415 in a 2-px column (the v7 “180” was a
   single-column count over a shorter range and is withdrawn); the packet is
   current and `04` is the 633-px-cell sheet; `scene_focus_x4.png` is 4× and the
   new shadow plate is 6×.

---

## Verification summary

* 25 atlas keys == 25 PNGs in `tiles/`; 3 medium + 3 mega sprites.
* `palette_violations == (0, 0)` for atlas, sample, mega, scene, focus and the
  new 6× plate; every sprite alpha is exactly {0, 255}.
* Shadow rows never touch a lip or tread (0 px changed on rows 480–483 and
  512–513); the deck lip reads 156.5 / 79.3.
* Dais and pad treads are identical (156.5 / 112.8 / 112.8 / 79.5).
* The agent appears once (scene − mega = 631 px, body + blade tip + shadow).
* Repeating fills still 0.00/0.00 on both axes (12 tiles); `deck_top` /
  `deck_step` are 0.00 on X and one-shot on Y; hazard wrap 19.17 = interior.

## Remaining issues / risks (not addressed in this pass)

1. **Viewport glass is dark** (mean ≈ 38): at 1× it still reads as a black panel.
2. **Door vs props**: the clear opening is 60 px; the 104-px server and 87-px
   cargo are taller than the only door.
3. **`unify_light` is a rim pass** — outer-7-px L−R is positive on all six, but
   the reactor/hull/viewport bodies stay near-symmetric (by design for the
   reactor, but the hull and viewport are only rim-lit).
4. **The 6-tile dais still repeats one `deck_step` tile** (the vent slot at a
   32-px pitch).
5. **Packet framing** (`00` 7 empty cells, `02` 5 empty cells, small labels) and
   the `01` slice (hazard at row 7, no ceiling/door demo) — packet-side, rebuilt
   by you.
6. **`deck_top_right` has no left twin** (kit-only cap set).
7. **The 2-crate cargo variant is a crop** of the shipped sprite (row 26), not a
   separate file; documented in `ship_layout.json` and `_cargo_low()`.
