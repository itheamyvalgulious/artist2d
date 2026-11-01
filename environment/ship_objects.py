"""Medium-structure and mega-element generation for the ship set.

Every object is generated as a single side-view sprite on a flat magenta key,
using the ship material board as a style reference.  The result is cropped,
fitted to the catalog's true-pixel footprint, palette-locked and saved with
Y-sort/collision metadata.  The same code path is used for the 10 medium
structures (``environment/ship``) and the 20 mega elements (``mega/ship``).
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from PIL import Image

from config.namespaces import environment_dir, mega_dir, work_environment_dir
from config.pipeline_config import TILE_SIZE
from config.ship_config import OBJECT_PROMPT
from core.api_client import GeminiImageClient
from core.grid_resampler import (
    background_mask,
    estimate_background,
    resample_to_true_pixel,
    upscale_nearest,
)
from core.palette_quantizer import lock_palette, palette_violations
from scipy import ndimage


def load_style_reference(env_dir: Path | None = None) -> Image.Image:
    env_dir = Path(env_dir) if env_dir else environment_dir("ship")
    work_env = work_environment_dir("ship")
    candidates = [
        env_dir / "material_board.png",
        work_env / "material_board.png",
        env_dir / "tileset_preview_x8.png",
        env_dir / "tiles" / "deck_x8.png",
    ]
    for p in candidates:
        if p.exists():
            img = Image.open(p).convert("RGB")
            # The style reference is only a visual anchor; 768 px is enough.
            if max(img.size) > 768:
                s = 768 / max(img.size)
                img = img.resize((int(img.width * s), int(img.height * s)), Image.LANCZOS)
            return img
    raise FileNotFoundError("ship material board / tileset preview not found")


def fit_object_to_true(raw: Image.Image, size: tuple[int, int],
                       api_scale: int = 8, fill: float = 0.92) -> Image.Image:
    """Crop the magenta-backed object and fit it to a true-pixel footprint."""
    tw, th = int(size[0]), int(size[1])
    rgb = np.array(raw.convert("RGB"))
    bg = estimate_background(raw)
    mask = background_mask(rgb, bg)
    ys, xs = np.nonzero(~mask)
    if len(xs) == 0:
        return Image.new("RGBA", (tw, th), (0, 0, 0, 0))
    x0, x1 = int(xs.min()), int(xs.max()) + 1
    y0, y1 = int(ys.min()), int(ys.max()) + 1
    crop = raw.convert("RGBA").crop((x0, y0, x1, y1))
    cw, ch = tw * api_scale, th * api_scale
    scale = min(cw * fill / max(1, crop.width), ch * fill / max(1, crop.height))
    nw = max(1, int(round(crop.width * scale)))
    nh = max(1, int(round(crop.height * scale)))
    resized = crop.resize((nw, nh), Image.LANCZOS)
    canvas = Image.new("RGB", (cw, ch), (255, 0, 255))
    x = (cw - nw) // 2
    y = ch - nh - max(1, int(ch * 0.012))
    canvas.paste(resized, (x, y), resized)
    px = lock_palette(resample_to_true_pixel(canvas, (tw, th)))
    arr = np.array(px.convert("RGBA"))
    lab, n = ndimage.label(arr[..., 3] > 0)
    if n > 1:
        sizes = np.bincount(lab.ravel())
        sizes[0] = 0
        for k in range(1, n + 1):
            if sizes[k] < 16:
                arr[lab == k, 3] = 0
    return lock_palette(Image.fromarray(arr, "RGBA"))


def preview_on_dark(img: Image.Image, scale: int = 4, pad: int = 8) -> Image.Image:
    bg = Image.new("RGBA", (img.width + pad * 2, img.height + pad * 2), (8, 8, 12, 255))
    bg.alpha_composite(img, (pad, pad))
    return bg.resize((bg.width * scale, bg.height * scale), Image.NEAREST)


def generate_object(client: GeminiImageClient, entry: dict, kind: str,
                    style_ref: Image.Image, outdir: Path, force: bool = False) -> dict:
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    sprite_path = outdir / "sprite.png"
    meta_path = outdir / "metadata.json"
    if sprite_path.exists() and meta_path.exists() and not force:
        return json.loads(meta_path.read_text())

    prompt = OBJECT_PROMPT.format(kind=kind, desc=entry["desc"])
    raw = client.generate_one(prompt, images=[style_ref], role="sunburst",
                              aspect="1:1", size="2K",
                              tag=f"ship-{kind}-{entry['id']}-v1")
    raw.save(outdir / "ai_raw.png")
    sprite = fit_object_to_true(raw, tuple(entry["size"]))
    sprite.save(sprite_path)
    preview_on_dark(sprite, 4).save(outdir / "sprite_x4.png")
    meta = {
        "id": entry["id"],
        "name": entry.get("name", entry["id"]),
        "kind": kind,
        "size": list(sprite.size),
        "pivot": [sprite.width // 2, sprite.height],
        "layer": "sorted_body",
        "collision": True,
        "catalog_size": list(entry["size"]),
        "palette_violations": list(palette_violations(sprite)),
        "source": {"model": "gemini-nano-banana-2.1", "prompt": prompt},
    }
    meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False))
    return meta


def generate_catalog(client: GeminiImageClient, entries: list[dict], kind: str,
                     outdir: Path, force: bool = False) -> list[dict]:
    style_ref = load_style_reference()
    reports = []
    for entry in entries:
        print(f"  generating {kind}: {entry['id']} {tuple(entry['size'])}")
        rep = generate_object(client, entry, kind, style_ref, outdir / entry["id"], force)
        print(f"    -> {rep['size']} violations={rep['palette_violations']}")
        reports.append(rep)
    return reports


def contact_sheet(entries: list[dict], outdir: Path, filename: str = "catalog_preview.png",
                  scale: int = 2) -> Path:
    """A simple side-by-side preview on a ship-dark backdrop with a deck line."""
    sprites = []
    for entry in entries:
        p = outdir / entry["id"] / "sprite.png"
        if p.exists():
            sprites.append(Image.open(p).convert("RGBA"))
    if not sprites:
        raise FileNotFoundError("no sprites for contact sheet")
    gap = 24
    w = sum(s.width for s in sprites) + gap * (len(sprites) + 1)
    h = max(s.height for s in sprites) + 64
    sheet = Image.new("RGBA", (w, h), (8, 8, 12, 255))
    x = gap
    for s in sprites:
        sheet.alpha_composite(s, (x, h - 40 - s.height))
        x += s.width + gap
    sheet.save(outdir / filename)
    upscale_nearest(sheet, scale).save(outdir / filename.replace(".png", f"_x{scale}.png"))
    return outdir / filename
