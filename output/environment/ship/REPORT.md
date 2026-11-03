# Ship Environment Report / 飞船内景

## Isolation

- Tiles + medium structures: `output/environment/ship/`
- Mega elements + whole-ship assembly: `output/mega/ship/`
- Showcase: `output/showcase/ship/`
- The original top-down terrain stays in `environment/field`, `mega/field`, `showcase/field`.

## Material board (2x2, deterministic toroidal seam median)

| material | KS statistic | p (full) | p (3x3) | pass | phase |
|---|---:|---:|---:|---|---|
| deck | 0.0494 | 0.9965 | 0.3078 | True | [0, 2] |
| wall | 0.0388 | 0.9999 | 0.6087 | True | [30, 25] |
| grate | 0.0262 | 1.0000 | 0.9524 | True | [21, 29] |
| conduit | 0.0479 | 0.9977 | 0.3437 | True | [22, 2] |

Tile atlas: **25** tiles (`tileset.png`), including deck/platform edges, wall/light/violet variants, ceiling, grate, pipes, vent, hazard and starfield window.  Only these 25 derived structural tiles are shipped in `tiles/`; the board's four materials are working files (the `conduit` quadrant informs the pipe family and is not a shipped tile).

## Medium structures (pilot 3 / 10)

| id | size | palette |
|---|---|---|
| console_bank | [102, 59] | [0, 0] |
| cargo_stack | [59, 87] | [0, 0] |
| server_rack | [52, 104] | [0, 0] |

Full catalog (10): console_bank, cargo_stack, server_rack, med_pod, holo_table, locker_bench, security_door, turret, vending_unit, escape_pod

## Mega elements (pilot 3 / 20)

| id | size | palette |
|---|---|---|
| hull_frame | [118, 203] | [0, 0] |
| viewport | [112, 88] | [0, 0] |
| reactor_core | [118, 140] | [0, 0] |

Full catalog (20): hull_frame, viewport, reactor_core, bulkhead_door, floor_truss, ceiling_truss, vent_stack, cable_run, pipe_junction, ladder_well, railing, light_strip, hazard_trim, cryo_pod, antenna_array, thruster, airlock, escape_hatch, engine_nacelle, gravity_ring

## Assembly

- Whole-ship room: (1536, 640) (`mega/ship/ship_mega_1x.png`).
- Structural hull ribs, armoured viewport, reactor core, control console,
  cargo stack and server rack are placed on the tile floor.
- Showcase with the agent: `showcase/ship/scene.png`.

## Preview files

- `environment/ship/tileset_preview_x8.png`
- `environment/ship/tileset_sample_x4.png`
- `environment/ship/props/catalog_preview.png`
- `mega/ship/elements/catalog_preview.png`
- `mega/ship/ship_mega_preview.png`
- `showcase/ship/scene.png`
- `showcase/ship/scene_focus_x4.png` (4x crop of the agent / door / server)
- `showcase/ship/scene_shadows_x6.png` (6x plate: dais + reactor pad contact shadows)

> `scripts/build_ship.py` with no flags rebuilds every tile and every
> deterministic prop from code and re-derives the four AI-authored sprites
> from their cached `sprite_src.png` base art, with zero API calls.

> Only the three pilot structures/elements were generated. The other 7
> medium types and 17 mega types are already defined in
> `config/ship_config.py`; re-run `scripts/build_ship.py --medium ... --mega ...`
> after the style is approved.
