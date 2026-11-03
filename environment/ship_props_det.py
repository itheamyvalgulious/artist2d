"""Deterministic replacements for the two ship props the image model kept
flattening into wall panels (cargo_stack, server_rack).

They are drawn from the same 64-colour palette, with 1px outlines and flat
three-tone shading, so they read as solid side-view objects at 1x.
"""
from __future__ import annotations

import numpy as np
from PIL import Image, ImageDraw

from config.pipeline_config import TILE_SIZE
from core.palette_quantizer import PALETTE_RGB, lock_palette


def _rgb(i: int) -> tuple[int, int, int]:
    return tuple(int(v) for v in PALETTE_RGB[i])


def _crate(d: ImageDraw.ImageDraw, x0: int, y0: int, x1: int, y1: int,
           body: int, top: int, label: int, hazard: bool = False,
           shadow_top: bool = False) -> None:
    # 1px near-black outline
    d.rectangle([x0, y0, x1, y1], fill=_rgb(0))
    d.rectangle([x0 + 1, y0 + 1, x1 - 1, y1 - 1], fill=_rgb(body))
    # lit lid plane + 1px highlight
    d.rectangle([x0 + 1, y0 + 1, x1 - 1, y0 + 4], fill=_rgb(top))
    d.line([x0 + 1, y0 + 1, x1 - 1, y0 + 1], fill=_rgb(6))
    if shadow_top:
        # the crate above casts a 2 px shadow onto this lid
        d.rectangle([x0 + 1, y0 + 2, x1 - 1, y0 + 3], fill=_rgb(0))
    # front-face panel seams
    for yy in range(y0 + 8, y1 - 3, 7):
        d.line([x0 + 3, yy, x1 - 3, yy], fill=_rgb(1))
    # hazard tape is drawn UNDER the straps, as a 45-degree 8 px-period band
    if hazard:
        bx0, bx1 = x0 + 6, x1 - 6
        by0, by1 = y1 - 9, y1 - 4
        d.rectangle([bx0 - 1, by0 - 1, bx1 + 1, by1 + 1], fill=_rgb(0))
        d.rectangle([bx0, by0, bx1, by1], fill=_rgb(1))
        for yy in range(by0, by1 + 1):
            for xx in range(bx0, bx1 + 1):
                if ((xx - bx0) + (yy - by0)) % 8 < 4:
                    d.point((xx, yy), fill=_rgb(50))
        d.line([bx0, by1 + 1, bx1, by1 + 1], fill=_rgb(0))
    # two vertical straps with buckles (drawn after the tape)
    for xx in (x0 + 10, x1 - 12):
        d.rectangle([xx, y0 + 4, xx + 2, y1 - 2], fill=_rgb(1))
        d.rectangle([xx - 1, (y0 + y1) // 2, xx + 3, (y0 + y1) // 2 + 2], fill=_rgb(0))
        d.point((xx + 1, (y0 + y1) // 2 + 1), fill=_rgb(5))
    # corner brackets
    for bx, by in ((x0 + 1, y0 + 1), (x1 - 4, y0 + 1), (x0 + 1, y1 - 4), (x1 - 4, y1 - 4)):
        d.rectangle([bx, by, bx + 2, by + 2], fill=_rgb(4))
    # cyan inventory label block
    d.rectangle([x0 + 16, y0 + 10, x0 + 26, y0 + 14], fill=_rgb(label))
    d.rectangle([x0 + 17, y0 + 11, x0 + 25, y0 + 12], fill=_rgb(2))


def draw_cargo_stack() -> Image.Image:
    """64x96: three offset crates with lids, straps and one hazard stripe."""
    im = Image.new("RGBA", (64, 96), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    # bottom crate (widest)
    _crate(d, 4, 62, 60, 94, body=2, top=4, label=37, hazard=True, shadow_top=True)
    # middle crate, offset left, slightly narrower
    _crate(d, 2, 34, 56, 62, body=3, top=5, label=59, shadow_top=True)
    # top crate, offset right
    _crate(d, 7, 8, 57, 34, body=2, top=4, label=37)
    return lock_palette(im)


def draw_server_rack() -> Image.Image:
    """56x106 solid cabinet: capped top, lit side housings, louver banks, LEDs,
    a status screen, a recessed kick plate and two real feet.

    Rebuilt for v6 after the flat 55x105 rack failed: it had no side panels or
    depth, only slot lines, a 35x4 transparent hole above its base rail and a
    top-only light.  This version has a beveled left housing, a darker right
    housing (top-left light), an opaque base and worn 1 px detail.
    """
    im = Image.new("RGBA", (56, 106), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    # silhouette + 1 px outline
    d.rectangle([2, 1, 53, 101], fill=_rgb(0))
    d.rectangle([3, 2, 52, 100], fill=_rgb(2))
    # top cap: lit top edge, bevel, dark under-line
    d.rectangle([3, 2, 52, 9], fill=_rgb(4))
    d.line([3, 2, 52, 2], fill=_rgb(6))
    d.line([3, 3, 52, 3], fill=_rgb(5))
    d.line([3, 4, 52, 4], fill=_rgb(4))
    d.line([3, 9, 52, 9], fill=_rgb(1))
    # side housings: left lit, right shaded -> consistent top-left light
    d.rectangle([3, 10, 7, 100], fill=_rgb(3))
    d.line([3, 10, 3, 100], fill=_rgb(5))
    d.line([4, 10, 4, 100], fill=_rgb(4))
    d.line([5, 10, 5, 100], fill=_rgb(3))
    d.line([7, 10, 7, 100], fill=_rgb(1))
    d.rectangle([48, 10, 52, 100], fill=_rgb(3))
    d.line([48, 10, 48, 100], fill=_rgb(1))
    d.line([50, 10, 50, 100], fill=_rgb(2))
    d.line([52, 10, 52, 100], fill=_rgb(1))
    # front face panel seams (two vertical bays)
    for x in (27,):
        d.line([x, 10, x, 100], fill=_rgb(1))
        d.line([x + 1, 10, x + 1, 100], fill=_rgb(3))
    for y in (14, 36, 58, 88):
        d.line([8, y, 47, y], fill=_rgb(1))
        d.line([8, y + 1, 47, y + 1], fill=_rgb(3))
    # louver vents: three banks of thin recessed slots with a lit lower lip
    for bank_y in (14, 34, 54):
        for k in range(5):
            y = bank_y + k * 3
            d.line([11, y, 44, y], fill=_rgb(1))
            d.line([11, y + 1, 44, y + 1], fill=_rgb(4))
        d.rectangle([9, bank_y + 1, 10, bank_y + 2], fill=_rgb(37))
        d.rectangle([45, bank_y + 1, 46, bank_y + 2], fill=_rgb(59))
    # connector blocks in the lower bay
    for x in (12, 22, 32, 42):
        d.rectangle([x, 83, x + 5, 87], fill=_rgb(1))
        d.line([x, 83, x + 5, 83], fill=_rgb(4))
        d.line([x + 1, 85, x + 4, 85], fill=_rgb(37))
    # central status screen
    d.rectangle([19, 70, 37, 80], fill=_rgb(0))
    d.rectangle([20, 71, 36, 79], fill=_rgb(34))
    for x in range(22, 35, 3):
        d.line([x, 73, x, 77], fill=_rgb(38))
    d.line([20, 71, 36, 71], fill=_rgb(32))
    d.point((35, 78), fill=_rgb(37))
    # recessed kick plate (opaque, no transparent slot)
    d.rectangle([8, 92, 47, 98], fill=_rgb(1))
    d.line([8, 92, 47, 92], fill=_rgb(0))
    for x in range(10, 46, 4):
        d.line([x, 94, x + 2, 94], fill=_rgb(2))
        d.line([x, 95, x + 2, 95], fill=_rgb(0))
    # feet with a real gap between them, and a base rail
    d.rectangle([5, 99, 17, 103], fill=_rgb(3))
    d.line([5, 99, 17, 99], fill=_rgb(5))
    d.line([6, 100, 16, 100], fill=_rgb(4))
    d.rectangle([38, 99, 50, 103], fill=_rgb(2))
    d.line([38, 99, 50, 99], fill=_rgb(3))
    d.line([5, 104, 50, 104], fill=_rgb(0))
    # 1 px wear: 2 px scratches + a few dents (survives despeckle)
    for y, x, n in ((12, 12, 3), (33, 40, 2), (55, 14, 2), (84, 42, 3),
                    (24, 30, 2), (76, 12, 2)):
        d.line([x, y, x + n - 1, y], fill=_rgb(3))
    for x, y in ((12, 30), (41, 47), (22, 86), (33, 15)):
        d.rectangle([x, y, x + 1, y + 1], fill=_rgb(1))
    return lock_palette(im)


DETERMINISTIC = {
    "cargo_stack": draw_cargo_stack,
    "server_rack": draw_server_rack,
}


if __name__ == "__main__":
    from pathlib import Path

    out = Path("output/environment/ship/props")
    for name, fn in DETERMINISTIC.items():
        p = out / name / "sprite.png"
        p.parent.mkdir(parents=True, exist_ok=True)
        fn().save(p)
        print(p, fn().size)
