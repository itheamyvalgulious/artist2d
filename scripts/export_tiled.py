"""Export the mega layout as a native Tiled `.tmj` map (and Godot-friendly JSON).

    .venv/bin/python scripts/export_tiled.py
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
import sys
sys.path.insert(0, str(ROOT))
from config.namespaces import mega_dir  # noqa: E402
MEGA = mega_dir("field")


def main() -> None:
    layout = json.loads((MEGA / "mega_layout.json").read_text())
    tile = layout["tile_size"]
    cols = max(c["col"] for c in layout["layout"]) + 1
    rows = max(c["row"] for c in layout["layout"]) + 1
    atlas_w = layout["atlas_width"]
    tile_count = atlas_w // tile

    data = [0] * (cols * rows)
    for cell in layout["layout"]:
        if cell.get("empty") or cell.get("atlas_x", -1) < 0:
            continue
        gid = int(cell["atlas_x"]) + 1
        data[cell["row"] * cols + cell["col"]] = gid

    tiled = {
        "type": "map",
        "version": "1.10",
        "tiledversion": "1.10.2",
        "orientation": "orthogonal",
        "renderorder": "right-down",
        "infinite": False,
        "width": cols,
        "height": rows,
        "tilewidth": tile,
        "tileheight": tile,
        "nextlayerid": 2,
        "nextobjectid": 1,
        "layers": [{
            "id": 1,
            "name": "mega",
            "type": "tilelayer",
            "x": 0, "y": 0,
            "width": cols, "height": rows,
            "opacity": 1,
            "visible": True,
            "data": data,
        }],
        "tilesets": [{
            "firstgid": 1,
            "name": "mega_atlas",
            "image": "mega_atlas.png",
            "imagewidth": atlas_w,
            "imageheight": tile,
            "tilewidth": tile,
            "tileheight": tile,
            "columns": tile_count,
            "tilecount": tile_count,
            "margin": 0,
            "spacing": 0,
        }],
    }
    out = MEGA / "mega_map.tmj"
    out.write_text(json.dumps(tiled, indent=2))
    print("wrote", out, f"{cols}x{rows} tiles, {tile_count} atlas tiles")


if __name__ == "__main__":
    main()
