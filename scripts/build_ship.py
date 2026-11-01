"""Build the side-view spaceship interior asset set (preview round).

    .venv/bin/python scripts/build_ship.py            # pilot: 3 medium + 3 mega
    .venv/bin/python scripts/build_ship.py --force    # regenerate all pilot art

Stages:
 1. 2x2 ship material board -> four seamless 32px tiles + complete tileset.
 2. Medium structures (pilot: console / cargo / server) under environment/ship.
 3. Mega elements (pilot: hull frame / viewport / reactor) under mega/ship.
 4. Whole-ship mega assembly + showcase with the agent character.
 5. REPORT.md / report.json files.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from config.namespaces import environment_dir, mega_dir, showcase_dir  # noqa: E402
from config.ship_config import (  # noqa: E402
    MEDIUM_STRUCTURES,
    MEGA_ELEMENTS,
    PILOT_MEDIUM,
    PILOT_MEGA,
)
from core.api_client import GeminiImageClient  # noqa: E402
from core.palette_quantizer import palette_violations  # noqa: E402
from environment.ship_assembly import compose  # noqa: E402
from environment.ship_objects import contact_sheet, generate_catalog  # noqa: E402
from environment.ship_tiles import build_tileset, generate_materials  # noqa: E402
from PIL import Image  # noqa: E402


def _by_id(catalog: list[dict], ids: list[str]) -> list[dict]:
    return [e for e in catalog if e["id"] in ids]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--medium", default=",".join(PILOT_MEDIUM))
    ap.add_argument("--mega", default=",".join(PILOT_MEGA))
    args = ap.parse_args()
    medium_ids = [s for s in args.medium.split(",") if s]
    mega_ids = [s for s in args.mega.split(",") if s]
    medium = _by_id(MEDIUM_STRUCTURES, medium_ids)
    mega = _by_id(MEGA_ELEMENTS, mega_ids)
    if not medium or not mega:
        raise SystemExit("unknown medium/mega id")

    env = environment_dir("ship")
    mg = mega_dir("ship")
    env.mkdir(parents=True, exist_ok=True)
    mg.mkdir(parents=True, exist_ok=True)
    client = GeminiImageClient()

    print("1/4 ship materials + tileset")
    materials, mat_report = generate_materials(client, outdir=env, force=args.force)
    tile_report = build_tileset(materials, env)

    print("2/4 medium structures:", [e["id"] for e in medium])
    med_report = generate_catalog(client, medium, "medium structure",
                                  env / "props", force=args.force)
    contact_sheet(medium, env / "props", "catalog_preview.png", 2)

    print("3/4 mega elements:", [e["id"] for e in mega])
    meg_report = generate_catalog(client, mega, "mega element",
                                  mg / "elements", force=args.force)
    contact_sheet(mega, mg / "elements", "catalog_preview.png", 2)

    print("4/4 assembly + showcase")
    mega_img = compose(include_character=False, env=env, mg=mg)
    mega_img.save(mg / "ship_mega_1x.png")
    mega_img.resize((mega_img.width * 2, mega_img.height * 2), Image.NEAREST).save(
        mg / "ship_mega_preview.png")
    scene = compose(include_character=True, env=env, mg=mg)
    show = showcase_dir("ship")
    show.mkdir(parents=True, exist_ok=True)
    scene.save(show / "scene_1x.png")
    scene.resize((scene.width * 2, scene.height * 2), Image.NEAREST).save(show / "scene.png")

    env_rep = {
        "set": "ship",
        "materials": mat_report,
        "tileset": tile_report["tiles"],
        "tileset_file": "tileset.png",
        "tileset_sample": "tileset_sample.png",
        "tileset_preview": "tileset_preview_x8.png",
        "palette_violations": {
            "tileset": list(palette_violations(Image.open(env / "tileset.png"))),
            "sample": list(palette_violations(Image.open(env / "tileset_sample.png"))),
        },
        "medium_catalog_size": len(MEDIUM_STRUCTURES),
        "medium_generated": [r["id"] for r in med_report],
    }
    (env / "report.json").write_text(json.dumps(env_rep, indent=2))

    meg_rep = {
        "set": "ship",
        "mega_catalog_size": len(MEGA_ELEMENTS),
        "mega_generated": [r["id"] for r in meg_report],
        "assembly": {
            "size": list(mega_img.size),
            "file": "ship_mega_1x.png",
            "preview": "ship_mega_preview.png",
            "palette_violations": list(palette_violations(mega_img)),
        },
        "elements": meg_report,
    }
    (mg / "report.json").write_text(json.dumps(meg_rep, indent=2))
    show_rep = {
        "set": "ship",
        "scene_1x": list(scene.size),
        "scene": "scene.png",
        "palette_violations": list(palette_violations(scene)),
        "character": "agent idle/shoot2",
    }
    (show / "report.json").write_text(json.dumps(show_rep, indent=2))

    # Human-readable report.
    lines = [
        "# Ship Environment Report / 飞船内景",
        "",
        "## Isolation",
        "",
        "- Tiles + medium structures: `output/environment/ship/`",
        "- Mega elements + whole-ship assembly: `output/mega/ship/`",
        "- Showcase: `output/showcase/ship/`",
        "- The original top-down terrain stays in `environment/field`, `mega/field`, `showcase/field`.",
        "",
        "## Tile materials (2x2 board, deterministic toroidal seam median)",
        "",
        "| material | KS statistic | p (full) | p (3x3) | pass | phase |",
        "|---|---:|---:|---:|---|---|",
    ]
    for name, r in mat_report.items():
        ks = r["ks"]
        lines.append(f"| {name} | {ks['ks_statistic']:.4f} | {ks['p_value']:.4f} | "
                     f"{ks['p_value_3x3']:.4f} | {ks['pass']} | {r['phase']} |")
    lines += [
        "",
        f"Tile atlas: **{len(tile_report['tiles'])}** tiles (`tileset.png`), "
        "including deck/platform edges, wall/light/violet variants, ceiling, grate, "
        "pipes, vent, hazard and starfield window.",
        "",
        "## Medium structures (pilot 3 / 10)",
        "",
        "| id | size | palette |",
        "|---|---|---|",
    ]
    for r in med_report:
        lines.append(f"| {r['id']} | {r['size']} | {r['palette_violations']} |")
    lines += [
        "",
        "Full catalog (10): " + ", ".join(e["id"] for e in MEDIUM_STRUCTURES),
        "",
        "## Mega elements (pilot 3 / 20)",
        "",
        "| id | size | palette |",
        "|---|---|---|",
    ]
    for r in meg_report:
        lines.append(f"| {r['id']} | {r['size']} | {r['palette_violations']} |")
    lines += [
        "",
        "Full catalog (20): " + ", ".join(e["id"] for e in MEGA_ELEMENTS),
        "",
        "## Assembly",
        "",
        f"- Whole-ship room: {mega_img.size} (`mega/ship/ship_mega_1x.png`).",
        "- Structural hull ribs, armoured viewport, reactor core, control console,",
        "  cargo stack and server rack are placed on the tile floor.",
        "- Showcase with the agent: `showcase/ship/scene.png`.",
        "",
        "## Preview files",
        "",
        "- `environment/ship/tileset_preview_x8.png`",
        "- `environment/ship/tileset_sample_x4.png`",
        "- `environment/ship/props/catalog_preview.png`",
        "- `mega/ship/elements/catalog_preview.png`",
        "- `mega/ship/ship_mega_preview.png`",
        "- `showcase/ship/scene.png`",
        "",
        "> Only the three pilot structures/elements were generated. The other 7",
        "> medium types and 17 mega types are already defined in",
        "> `config/ship_config.py`; re-run `scripts/build_ship.py --medium ... --mega ...`",
        "> after the style is approved.",
    ]
    (env / "REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print("done")
    print("  env:", env)
    print("  mega:", mg)
    print("  showcase:", show)
    print("  scene:", scene.size, "purity", palette_violations(scene))


if __name__ == "__main__":
    main()
