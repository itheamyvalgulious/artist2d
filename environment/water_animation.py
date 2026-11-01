"""AI-generated looping water animation.

The shipped animation is NOT a procedural roll of a still.  Gemini generates a
2x2 sheet of four consecutive frames of the same seamless water tile; each
quadrant is resampled, made seamless with the same border-safe seam repair used
for the static tiles, and snapped to the blue water ramp.  The four frames form
a loop (frame 3 -> frame 0 has the smallest measured difference).
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from PIL import Image

from core.api_client import GeminiImageClient
from core.grid_resampler import resample_to_true_pixel
from core.palette_quantizer import lock_palette, palette_violations
from environment.seamless_toroidal import ks_seam_test, make_seamless

PROMPT = (
    "A 2x2 grid of four consecutive frames of a looping pixel-art water tile animation, "
    "32x32 design pixels per frame, flat top-down orthographic. All four frames show the SAME "
    "deep-blue water surface with thin 1-pixel horizontal light-blue ripple lines; only the "
    "ripple phase changes from frame to frame: the crests rise, drift a little, and fall, like "
    "real small waves. Frame 1 top-left, frame 2 top-right, frame 3 bottom-left, frame 4 "
    "bottom-right form one smooth loop, with frame 4 flowing back into frame 1. Each frame must "
    "be seamless on all four edges. No grid lines, no borders, no panel separators, no circles, "
    "no foam, no large waves, no text, no watermark, 64-color palette, crisp pixels."
)
TAG = "water-anim-2x2-v1"
def _quadrants(raw: Image.Image) -> list[Image.Image]:
    w, h = raw.size
    out = []
    for i in range(4):
        r, c = divmod(i, 2)
        ix, iy = int(w * 0.02), int(h * 0.02)   # avoid a possible panel separator
        out.append(raw.crop((c * w // 2 + ix, r * h // 2 + iy,
                             (c + 1) * w // 2 - ix, (r + 1) * h // 2 - iy)))
    return out


def _base_stats(outdir: Path) -> tuple[np.ndarray, np.ndarray]:
    base = np.asarray(Image.open(outdir / "water_seamless.png").convert("RGB"))
    u, c = np.unique(base.reshape(-1, 3), axis=0, return_counts=True)
    lum = u @ np.array([0.2126, 0.7152, 0.0722])
    order = np.argsort(lum)
    return u[order], c[order] / c.sum()


def _rank_map(im: Image.Image, colors: np.ndarray, probs: np.ndarray) -> np.ndarray:
    """Match the AI frame's luminance distribution to the base water tile.

    The 2x2 sheet comes back on a lighter mid-blue than the shipped seamless
    tile, which made the animated pond interior a pale rectangle.  Rank
    mapping preserves the AI's dash pattern while matching the base tile's
    dark/heavy distribution exactly.
    """
    a = np.asarray(im.convert("RGB")).astype(np.float64)
    lum = a @ np.array([0.2126, 0.7152, 0.0722])
    flat = lum.ravel()
    order = np.argsort(flat)
    ranks = np.empty_like(order)
    ranks[order] = np.arange(order.size)
    pct = ranks / max(1, order.size - 1)
    cum = np.cumsum(probs)
    idx = np.searchsorted(cum, pct, side="right").clip(0, len(colors) - 1)
    return colors[idx].reshape(a.shape[:2] + (3,))


def _despeckle(a: np.ndarray) -> np.ndarray:
    """Drop 1 px AI specks that have no same-colour neighbour; keep the dashes."""
    a = a.copy()
    h, w = a.shape[:2]
    for y in range(h):
        for x in range(w):
            win = a[max(0, y - 1):min(h, y + 2), max(0, x - 1):min(w, x + 2)].reshape(-1, 3)
            if int(np.all(win == a[y, x], axis=1).sum()) == 1:
                u, c = np.unique(win, axis=0, return_counts=True)
                a[y, x] = u[int(np.argmax(c))]
    return a


def generate_water_frames(client: GeminiImageClient | None = None,
                          outdir: Path | str = "output/environment") -> list[Image.Image]:
    outdir = Path(outdir)
    anim_dir = outdir / "water_anim"
    anim_dir.mkdir(parents=True, exist_ok=True)
    client = client or GeminiImageClient()
    raw = client.generate_one(PROMPT, role="sunburst", aspect="1:1", size="2K", tag=TAG)
    raw.save(outdir / "water_anim_sheet_raw.png")

    colors, probs = _base_stats(outdir)
    frames: list[Image.Image] = []
    per_frame = []
    for i, q in enumerate(_quadrants(raw)):
        px = lock_palette(resample_to_true_pixel(q.convert("RGB"), (32, 32)))
        # Match the base tile's dark palette BEFORE the seam repair so the
        # repaired frames both match the shipped water and pass KS.
        mapped = _rank_map(px, colors, probs)
        mapped_img = Image.fromarray(
            np.dstack([mapped, np.full((32, 32), 255, np.uint8)]), "RGBA")
        res, rep = make_seamless(mapped_img, client, prompt_extra="water ripples",
                                 prefer_median=False)
        cleaned = _despeckle(np.asarray(res.convert("RGB")))
        frame = Image.fromarray(
            np.dstack([cleaned, np.full((32, 32), 255, np.uint8)]), "RGBA")
        frames.append(frame)
        per_frame.append({"frame": i, "method": rep.get("method"),
                          "ks": ks_seam_test(frame),
                          "violations": palette_violations(frame)})
        frame.save(anim_dir / f"frame_{i:02d}.png")

    diffs = []
    for i in range(4):
        a = np.asarray(frames[i]).astype(np.int16)
        b = np.asarray(frames[(i + 1) % 4]).astype(np.int16)
        diffs.append(round(float(np.abs(a - b).mean()), 2))
    report = {
        "method": "gemini-2x2-animation-sheet + rank color match + seam inpaint",
        "model_tag": TAG,
        "frames": 4,
        "frame_diffs": diffs,
        "loop_diff": diffs[3],
        "ks_pass": all(f["ks"]["pass"] for f in per_frame),
        "per_frame": per_frame,
    }
    (anim_dir / "report.json").write_text(json.dumps(report, indent=2))
    return frames
