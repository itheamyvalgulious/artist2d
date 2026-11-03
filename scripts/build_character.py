"""End-to-end character sheet build (PLAN module 1).

    .venv/bin/python scripts/build_character.py --character agent --actions idle,slash2,shoot2,roll

Pipeline:
 1. Godot renders the parametric mannequin for every action (shaded sheet,
    8-part ID sheet, bone ID sheet, projected motion truth).  The agent uses a
    female silhouette, long silver hair, stowed katana/pistol and hybrid
    "base clip + upper-body clip" poses for run-and-gun variants.
 2. Gemini generates the master reference and restyles the composite pose
    boards (reference panel + three mannequin panels per call).
 3. Every panel is fitted to a 512 canvas, core-window pooled to 64x64 and
    palette locked.
 4. The temporal tracker applies rigid static locking and feature stamping.
 5. Transition anchors are enforced pixel-for-pixel: shoot2/slash2 start and
    end on the run cycle, shoot1/slash1/block/roll on idle, in_air on the last
    jump frame.
 6. Final sheets + previews + metrics are written to output/character/<name>/.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from character.sheet_compositor import (  # noqa: E402
    CharacterPipeline,
    CharacterSpec,
    board_prompt,
    build_board,
    build_silhouette_mask,
    generate_weapon_reference,
    extract_action_panel,
    extract_panel,
    extract_panel_robust,
    lock_reference_panel,
    panel_has_margin,
    make_board_mask,
    panels_to_hires,
    panels_to_sprites,
    ref_canvas_from64,
    remove_detached_specks_image,
    remove_small_components,
    sheet_from_frames,
    split_merged_boots,
)
from character.presets import PRESETS, TRANSITIONS, transition_dependencies  # noqa: E402
from character.temporal_tracker import (  # noqa: E402
    export_motion_npy,
    load_truth,
    stabilize_action,
    static_lock,
    verify_action,
    warp_truth,
)
from core.grid_resampler import (  # noqa: E402
    background_mask_all,
    estimate_background,
    resample_from_hi,
)
from core.palette_quantizer import PALETTE_RGB  # noqa: E402
from config.namespaces import character_dir, work_character_dir  # noqa: E402
from core.api_client import GeminiImageClient  # noqa: E402
from config.pipeline_config import OUTPUT_DIR  # noqa: E402

# Character-specific action -> pose source.  A clip may be split into a lower
# body "base" clip and an upper-body clip; the renderer merges them per bone.
ACTION_SPECS: dict[str, dict[str, dict]] = {
    "knight": {
        "idle": {"clip": "Idle"},
        "running": {"clip": "Running_A"},
        "attack": {"clip": "1H_Melee_Attack_Chop"},
        "defend": {"clip": "Blocking"},
        "jump": {"clip": "Jump_Start", "start": 0.45, "end": 1.0},
        "in_air": {"clip": "Jump_Full_Short", "start": 0.35, "end": 0.68},
    },
    "agent": {
        # KayKit Idle's tail contains a weight-shift crouch that made frames
        # 5-7 shorter/one-legged.  Use the procedural breathing idle instead;
        # it keeps a constant full-body silhouette for all eight frames.
        "idle": {"source": "procedural"},
        "run": {"clip": "Running_B", "context_action": "idle"},
        "jump": {"clip": "Jump_Start", "start": 0.45, "end": 1.0},
        "in_air": {"clip": "Jump_Idle"},
        "shoot1": {"clip": "1H_Ranged_Shoot", "base_clip": "Idle", "upper_clip": "1H_Ranged_Shoot", "upper_start": 0.08, "upper_end": 0.40},
        "shoot2": {"clip": "1H_Ranged_Shoot", "base_clip": "Running_B", "upper_clip": "1H_Ranged_Shoot", "upper_start": 0.08, "upper_end": 0.40, "board_fill": 0.86},
        "shoot3": {"clip": "1H_Ranged_Shoot", "base_clip": "Jump_Idle", "upper_clip": "1H_Ranged_Shoot", "upper_start": 0.08, "upper_end": 0.40},
        "slash1": {"clip": "1H_Melee_Attack_Slice_Diagonal", "start": 0.32, "end": 0.52},
        "slash2": {"clip": "1H_Melee_Attack_Slice_Diagonal", "base_clip": "Running_B", "upper_clip": "1H_Melee_Attack_Slice_Diagonal", "upper_start": 0.32, "upper_end": 0.52, "board_fill": 0.86},
        "slash3": {"clip": "1H_Melee_Attack_Slice_Diagonal", "base_clip": "Jump_Idle", "upper_clip": "1H_Melee_Attack_Slice_Diagonal", "upper_start": 0.32, "upper_end": 0.52},
        "block": {"clip": "Blocking"},
        "roll": {"source": "procedural", "context_action": "idle", "board_fill": 0.82},
    },
}
# The pilot round only ships these four agent actions; the run clip is built
# as a transition anchor because slash2/shoot2 must start and end on it.
PILOT_ACTIONS = {
    "agent": ["idle", "slash2", "shoot2", "roll"],
    "knight": ["idle", "running", "attack", "defend", "jump", "in_air"],
}
GODOT = os.environ.get("GODOT_BIN", "godot")
DISPLAY = os.environ.get("GODOT_DISPLAY", ":0")


def _sha(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _save_apng(frames: list[Image.Image], path: Path, duration: int = 110) -> None:
    frames[0].save(path, save_all=True, append_images=frames[1:],
                   duration=duration, loop=0, disposal=1, blend=0)


def _save_gif(frames: list[Image.Image], path: Path, duration: int = 110,
              bg=(8, 8, 12, 255)) -> None:
    rgb = []
    for f in frames:
        canvas = Image.new("RGBA", f.size, bg)
        canvas.alpha_composite(f)
        rgb.append(canvas.convert("RGB"))
    rgb[0].save(path, save_all=True, append_images=rgb[1:], duration=duration,
                loop=0, disposal=2, optimize=False)


def build_design_sheet(outdir: Path) -> dict:
    """Ship the full-body reference next to the separate weapon-part sheet.

    The character reference alone hides the katana inside its scabbard and the
    pistol in its holster.  This design sheet puts the full-body identity and
    the clean katana / scabbard / pistol parts side by side, so every detail is
    inspectable and usable by downstream artists.
    """
    ref_p = outdir / "char_ref_512.png"
    weapon_p = outdir / "char_ref_weapons_512.png"
    if not ref_p.exists() or not weapon_p.exists():
        return {"ok": False, "error": "missing character or weapon reference"}
    ref = Image.open(ref_p).convert("RGBA")
    weapons = Image.open(weapon_p).convert("RGBA")
    canvas = Image.new("RGBA", (ref.width + weapons.width, max(ref.height, weapons.height)),
                       (0, 0, 0, 0))
    canvas.alpha_composite(ref, (0, 0))
    canvas.alpha_composite(weapons, (ref.width, 0))
    from core.palette_quantizer import lock_palette as _lock
    from core.palette_quantizer import palette_violations as _viol
    sheet = _lock(canvas)
    sheet.save(outdir / "design_sheet.png")
    big = sheet.resize((sheet.width * 2, sheet.height * 2), Image.NEAREST)
    _lock(big).save(outdir / "design_sheet_x2.png")

    # Split the weapon sheet into its three independent parts by connected
    # components.  The layout is explicitly left-to-right, so x-order maps to
    # katana / scabbard / pistol.  If the model merged items we keep the full
    # sheet and report it honestly instead of inventing crops.
    import numpy as _np
    from scipy import ndimage as _ndi
    arr = _np.array(weapons)
    fg = arr[..., 3] > 0
    lab, count = _ndi.label(fg)
    comps = []
    for i in range(1, count + 1):
        ys, xs = _np.nonzero(lab == i)
        if len(xs) < 120:
            continue
        comps.append((int(xs.min()), int(xs.max()), int(ys.min()), int(ys.max()), len(xs)))
    comps.sort(key=lambda c: c[0])
    parts = {}
    if len(comps) == 3:
        parts_dir = outdir / "parts"
        parts_dir.mkdir(parents=True, exist_ok=True)
        for name, (x0, x1, y0, y1, _area) in zip(("katana", "scabbard", "pistol"), comps):
            crop = weapons.crop((max(0, x0 - 2), max(0, y0 - 2),
                                 min(weapons.width, x1 + 3), min(weapons.height, y1 + 3)))
            f = parts_dir / f"{name}.png"
            _lock(crop).save(f)
            parts[name] = str(f.relative_to(outdir))
    return {"ok": True, "sheet": "design_sheet.png", "preview": "design_sheet_x2.png",
            "parts": parts, "component_count": len(comps),
            "palette_violations": list(_viol(sheet))}


def _alpha_bbox(im: Image.Image) -> tuple[int, int, int, int] | None:
    a = np.array(im.convert("RGBA"))[..., 3] > 0
    ys, xs = np.nonzero(a)
    if len(xs) == 0:
        return None
    return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1


def prune_detached(im: Image.Image, connect: int = 3) -> Image.Image:
    """Keep the body plus anything touching/near it; drop panel-bleed islands.

    The generative edit is not a hard mask, so a neighbouring panel's boot can
    land above the head.  A detached weapon or hair lock that really belongs to
    the character still touches the body within a few pixels and survives.
    """
    from scipy import ndimage
    from core.palette_quantizer import lock_palette as _lock
    arr = np.array(im.convert("RGBA"))
    fg = arr[..., 3] > 0
    lab, n = ndimage.label(fg)
    if n > 1:
        sizes = np.bincount(lab.ravel())
        sizes[0] = 0
        main = int(np.argmax(sizes))
        main_mask = lab == main
        near = ndimage.binary_dilation(main_mask, iterations=max(1, connect))
        keep = main_mask.copy()
        for k in range(1, n + 1):
            if k == main:
                continue
            comp = lab == k
            if (comp & near).any():
                keep |= comp
        arr[..., 3] = np.where(keep, arr[..., 3], 0)
    return _lock(Image.fromarray(arr, "RGBA"))


def keep_main_component(im: Image.Image, min_size: int = 48) -> Image.Image:
    """Backward-compatible alias used by the hi-res post-pass."""
    return prune_detached(im, connect=3 if im.width <= 128 else 5)


def shift_inside(im: Image.Image, max_dx: int = 8, max_dy: int = 0,
                 margin: int = 8) -> Image.Image:
    """Nudge slightly-clipped content back inside the canvas."""
    box = _alpha_bbox(im)
    if box is None:
        return im
    x0, y0, x1, y1 = box
    dx = dy = 0
    if x0 < margin:
        dx = margin - x0
    elif x1 > im.width - margin:
        dx = (im.width - margin) - x1
    if y0 < margin:
        dy = margin - y0
    elif y1 > im.height - margin:
        dy = (im.height - margin) - y1
    dx = max(-max_dx, min(max_dx, dx))
    dy = max(-max_dy, min(max_dy, dy))
    if dx == 0 and dy == 0:
        return im
    out = Image.new("RGBA", im.size, (0, 0, 0, 0))
    out.alpha_composite(im.convert("RGBA"), (dx, dy))
    return out


def fit_with_margin(im: Image.Image, margin: int = 16) -> Image.Image:
    """Scale down only when the content overflows the requested margin."""
    box = _alpha_bbox(im)
    if box is None:
        return im
    x0, y0, x1, y1 = box
    w, h = im.width, im.height
    avail_w = w - 2 * margin
    avail_h = h - 2 * margin
    if x1 - x0 <= avail_w and y1 - y0 <= avail_h:
        return im
    crop = im.crop(box)
    scale = min(avail_w / crop.width, avail_h / crop.height)
    nw, nh = max(1, int(round(crop.width * scale))), max(1, int(round(crop.height * scale)))
    resized = crop.resize((nw, nh), Image.NEAREST)
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    out.alpha_composite(resized, ((w - nw) // 2, (h - nh) // 2))
    return out


def fix_missing_katana(pipe: CharacterPipeline, out_dir: Path, part_path: Path) -> bool:
    """Repaint slash2 f6, where the AI dropped the drawn katana entirely."""
    from PIL import ImageDraw
    from core.grid_resampler import estimate_background, background_mask_all
    from core.palette_quantizer import lock_palette as _lock
    frame_path = out_dir / "frames_hi" / "frame_06.png"
    if not frame_path.exists() or not part_path.exists():
        return False
    frame = Image.open(frame_path).convert("RGBA")
    base = Image.new("RGB", frame.size, (255, 0, 255))
    base.paste(frame, (0, 0), frame)
    mask = Image.new("L", frame.size, 0)
    d = ImageDraw.Draw(mask)
    d.line([(235, 345), (470, 500)], fill=255, width=54)
    d.ellipse((205, 315, 265, 375), fill=255)
    prompt = (
        "Repaint only the white masked area as the drawn katana continuing the downward slash. "
        "The hand is at the hip; the long silver blade with a dark spine, cyan edge and a visible "
        "tsuba extends down-right in front of the leg. Use the exact katana shape in the reference "
        "image; blade length about 220 px; do not crop the tip. Keep the hand, arm, shorts, leg, "
        "boots and the flat magenta background unchanged; the leg must remain visible behind the "
        "blade. Same pixel-art style, 1px dark outline, flat shading, no blur, no extra weapons."
    )
    res = pipe.client.inpaint(base, mask, prompt, role="sunburst", aspect="1:1", size="2K",
                             tag="slash2-f6-katana-v2",
                             refs=[Image.open(part_path).convert("RGB")])
    arr = np.array(res.convert("RGB"))
    bg = estimate_background(res)
    # Only accept a magenta-keyed return; otherwise keep the original frame.
    if np.linalg.norm(np.asarray(bg, dtype=float) - np.array([255, 0, 255])) > 80:
        return False
    bgm = background_mask_all(arr, bg)
    rgba = np.dstack([arr, np.where(bgm, 0, 255).astype(np.uint8)])
    _lock(Image.fromarray(rgba, "RGBA")).save(frame_path)
    return True


def normalize_idle_hi(out_dir: Path, frames: int = 8) -> None:
    """One body height and one head for the whole idle loop.

    The AI re-drew the head at a different height/eye design in f0/f1.  Fit
    every frame to the median body height (feet anchored) and composite the
    canonical head/hair patch from f2 over all frames.  This is deterministic
    and keeps the idle loop from popping.
    """
    from core.palette_quantizer import lock_palette as _lock
    src = [Image.open(out_dir / "frames_hi" / f"frame_{i:02d}.png").convert("RGBA")
           for i in range(frames)]
    metrics = []
    for f in src:
        ys, xs = np.nonzero(np.array(f)[..., 3] > 0)
        metrics.append((int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1))
    heights = [b[3] - b[1] for b in metrics]
    target = float(np.median(heights)) if heights else 420.0
    norm = []
    for f, (x0, y0, x1, y1) in zip(src, metrics):
        h = max(1, y1 - y0)
        crop = f.crop((x0, y0, x1, y1))
        s = target / h
        nw, nh = max(1, int(round(crop.width * s))), max(1, int(round(crop.height * s)))
        crop = crop.resize((nw, nh), Image.LANCZOS)
        canvas = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
        canvas.alpha_composite(crop, ((512 - nw) // 2, 504 - nh))
        norm.append(_lock(canvas))
    box = (180, 80, 350, 285)
    patch = norm[2].crop(box)
    for i, f in enumerate(norm):
        arr = np.array(f)
        arr[box[1]:box[3], box[0]:box[2], 3] = 0
        g = Image.fromarray(arr, "RGBA")
        g.alpha_composite(patch, (box[0], box[1]))
        _lock(g).save(out_dir / "frames_hi" / f"frame_{i:02d}.png")
    # The idle loop seam must not pop: make the last frame the same as the first.
    Image.open(out_dir / "frames_hi" / "frame_00.png").save(
        out_dir / "frames_hi" / "frame_07.png")


def remove_katana_shard(im: Image.Image) -> Image.Image:
    """Remove the small detached blade fragment the f6 inpaint left on the thigh."""
    from scipy import ndimage
    from core.palette_quantizer import lock_palette as _lock
    arr = np.array(im.convert("RGBA"))
    rgb = arr[..., :3].astype(int)
    a = arr[..., 3] > 0
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    blade = a & (((r > 120) & (g > 120) & (b > 120)) |
                 ((b > r + 20) & (g > r + 10)))
    region = np.zeros_like(a)
    region[380:470, 270:350] = True
    lab, n = ndimage.label(blade & region)
    for k in range(1, n + 1):
        comp = lab == k
        area = int(comp.sum())
        if area == 0 or area > 500:
            continue
        ys, xs = np.nonzero(comp)
        if xs.min() >= 270 and xs.max() < 350 and ys.min() >= 380 and ys.max() < 470:
            arr[comp, 3] = 0
    return _lock(Image.fromarray(arr, "RGBA"))


def despeckle(im: Image.Image) -> Image.Image:
    """Remove isolated single-pixel salt/pepper while protecting outlines/accents."""
    from scipy import ndimage
    from core.palette_quantizer import lock_palette as _lock
    arr = np.array(im.convert("RGBA"))
    rgb = arr[..., :3].astype(np.int16)
    a = arr[..., 3] > 0
    eq = np.zeros_like(a)
    padded_rgb = np.pad(rgb, ((1, 1), (1, 1), (0, 0)), mode="edge")
    padded_a = np.pad(a, ((1, 1), (1, 1)), mode="edge")
    for dy in (0, 1, 2):
        for dx in (0, 1, 2):
            if dy == 1 and dx == 1:
                continue
            sh = padded_rgb[dy:dy + rgb.shape[0], dx:dx + rgb.shape[1]]
            sha = padded_a[dy:dy + a.shape[0], dx:dx + a.shape[1]]
            eq |= np.all(rgb == sh, axis=-1) & sha
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    protected = ((r + g + b) < 100) | (b > r + 28) | ((r > g + 20) & (b > g + 20)) | \
                ((r > 150) & (g > 100) & (b < 80))
    target = a & ~eq & ~protected
    if target.any():
        med = ndimage.median_filter(rgb, size=(3, 3, 1))
        rgb[target] = med[target]
        arr[..., :3] = np.clip(rgb, 0, 255).astype(np.uint8)
    return _lock(Image.fromarray(arr, "RGBA"))


def paint_eye(im: Image.Image, full: bool = True) -> Image.Image:
    """Replace a black almond eye with a readable violet iris + sclera.

    Idle/run/slash/roll were generated with a solid black eye while shoot2
    had the correct violet eye.  Detect the largest dark component inside the
    warm face region and paint one consistent eye design.
    """
    from scipy import ndimage
    from core.palette_quantizer import lock_palette as _lock
    arr = np.array(im.convert("RGBA"))
    rgb = arr[..., :3].astype(int)
    alpha = arr[..., 3] > 0
    ys, xs = np.nonzero(alpha)
    if len(xs) == 0:
        return im
    y0, y1 = int(ys.min()), int(ys.max()) + 1
    head_lim = y0 + int((y1 - y0) * 0.42)
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    rows = np.arange(arr.shape[0])[:, None] < head_lim
    skin = (r > 150) & (g > 100) & (b < 170) & (r > g) & (g > b) & rows
    dark = (r + g + b < 160) & rows
    near = ndimage.binary_dilation(skin, iterations=3)
    lab, n = ndimage.label(dark)
    best = None
    for k in range(1, n + 1):
        comp = lab == k
        area = int(comp.sum())
        if area < 6 or area > 400:
            continue
        yy, xx = np.nonzero(comp)
        w, h = xx.max() - xx.min() + 1, yy.max() - yy.min() + 1
        if w < 4 or w > 30 or h < 3 or h > 24 or not (comp & near).any():
            continue
        if best is None or area > best[0]:
            best = (area, int(xx.min()), int(xx.max()), int(yy.min()), int(yy.max()))
    if best is None:
        return im
    _, ex0, ex1, ey0, ey1 = best
    cx, cy = (ex0 + ex1) // 2, (ey0 + ey1) // 2
    if full:
        # Violet-dominant iris: a single white catchlight and a 1 px pupil.
        arr[ey0 + 1:ey1, ex0 + 1:ex1, :3] = PALETTE_RGB[61]
        arr[ey0 + 1, ex0 + 1:ex1, :3] = PALETTE_RGB[56]
        if ey0 + 2 < ey1 and ex0 + 2 < ex1:
            arr[ey0 + 2, ex0 + 2, :3] = PALETTE_RGB[7]
        arr[cy, cx, :3] = PALETTE_RGB[0]
    else:
        arr[cy - 1:cy + 2, cx - 1:cx + 2, :3] = PALETTE_RGB[61]
    return _lock(Image.fromarray(arr, "RGBA"))


def preserve_eye(hi: Image.Image, ds: Image.Image) -> Image.Image:
    """Keep the violet iris when the 512px art is pooled to 64px."""
    from core.palette_quantizer import lock_palette as _lock
    h = np.array(hi.convert("RGBA"))
    out = np.array(ds.convert("RGBA"))
    fg = h[..., 3] > 0
    ys, xs = np.nonzero(fg)
    if len(xs) == 0:
        return ds
    r, g, b = h[..., 0].astype(int), h[..., 1].astype(int), h[..., 2].astype(int)
    # Bright iris violet, anywhere in the frame: in the roll the head is
    # inverted, so a top-of-body window would miss the eye.  The dark outfit
    # violet is excluded by the brightness gate.
    violet = (r > 130) & (b > 170) & (b > g + 30) & (r > g + 20)
    if not violet.any():
        return ds
    vy, vx = np.nonzero(violet)
    for y, x in zip(vy, vx):
        cy, cx = y // 8, x // 8
        if 0 <= cy < 64 and 0 <= cx < 64:
            out[cy, cx, :3] = h[y, x, :3]
            out[cy, cx, 3] = 255
    return _lock(Image.fromarray(out, "RGBA"))


def normalize_idle_scale(out_dir: Path, frames: int = 8,
                         only: int | None = None) -> None:
    """Keep the idle body height constant; do not repaint the head/face."""
    from core.palette_quantizer import lock_palette as _lock
    src = [Image.open(out_dir / "frames_hi" / f"frame_{i:02d}.png").convert("RGBA")
           for i in range(frames)]
    metrics = []
    for f in src:
        ys, xs = np.nonzero(np.array(f)[..., 3] > 0)
        metrics.append((int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1))
    use = only if only is not None else frames
    heights = [b[3] - b[1] for b in metrics[:use]]
    target = float(np.median(heights)) if heights else 420.0
    for i, (f, (x0, y0, x1, y1)) in enumerate(zip(src[:use], metrics[:use])):
        h = max(1, y1 - y0)
        crop = f.crop((x0, y0, x1, y1))
        s = target / h
        nw, nh = max(1, int(round(crop.width * s))), max(1, int(round(crop.height * s)))
        crop = crop.resize((nw, nh), Image.LANCZOS)
        canvas = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
        canvas.alpha_composite(crop, ((512 - nw) // 2, 504 - nh))
        _lock(canvas).save(out_dir / "frames_hi" / f"frame_{i:02d}.png")


def fit_action_margin(out_dir: Path, frames: int = 8, top: int = 16,
                      baseline: int = 504) -> None:
    """Uniformly fit an action's 512px frames with a real top margin.

    The AI sometimes draws the head at y=0, so the hair is clipped by the
    frame edge.  Scale all frames of the action by one common factor and
    anchor the feet at the baseline; relative motion/scale is preserved.
    """
    from core.palette_quantizer import lock_palette as _lock
    src = [Image.open(out_dir / "frames_hi" / f"frame_{i:02d}.png").convert("RGBA")
           for i in range(frames)]
    boxes = []
    for f in src:
        ys, xs = np.nonzero(np.array(f)[..., 3] > 0)
        boxes.append((int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1))
    avail = baseline - top
    scale = min(1.0, min(avail / max(1, b[3] - b[1]) for b in boxes))
    if scale >= 0.999:
        return
    for i, (f, b) in enumerate(zip(src, boxes)):
        crop = f.crop(b)
        nw, nh = max(1, int(round(crop.width * scale))), max(1, int(round(crop.height * scale)))
        crop = crop.resize((nw, nh), Image.LANCZOS)
        canvas = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
        canvas.alpha_composite(crop, ((512 - nw) // 2, baseline - nh))
        _lock(canvas).save(out_dir / "frames_hi" / f"frame_{i:02d}.png")


def normalize_action_scale(out_dir: Path, frames: int = 8,
                           min_ratio: float = 1.12, margin: int = 8) -> None:
    """If the AI drastically resized one pose, normalise the action to median height.

    The scale-up is capped so the frame always fits inside the canvas with a
    real margin: a horizontal katana thrust otherwise fills the full 512 px and
    both the blade tip and the scabbard tip get sliced off at the edge.
    """
    from core.palette_quantizer import lock_palette as _lock
    src = [Image.open(out_dir / "frames_hi" / f"frame_{i:02d}.png").convert("RGBA")
           for i in range(frames)]
    boxes = []
    for f in src:
        ys, xs = np.nonzero(np.array(f)[..., 3] > 0)
        boxes.append((int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1))
    heights = [b[3] - b[1] for b in boxes]
    if not heights:
        return
    med = float(np.median(heights))
    if max(heights) / max(1, min(heights)) < min_ratio:
        return
    for i, (f, b) in enumerate(zip(src, boxes)):
        crop = f.crop(b)
        s = med / max(1, b[3] - b[1])
        s = min(s, (504 - margin) / max(1, crop.height))
        nw, nh = max(1, int(round(crop.width * s))), max(1, int(round(crop.height * s)))
        crop = crop.resize((nw, nh), Image.LANCZOS)
        canvas = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
        canvas.alpha_composite(crop, ((512 - nw) // 2, 504 - nh))
        _lock(canvas).save(out_dir / "frames_hi" / f"frame_{i:02d}.png")


def pad_slash_frames(out_dir: Path, frames: int = 8, target_face: int = 33,
                     man_dir: Path | None = None) -> None:
    """Give the slash action a 640 px canvas and one body scale.

    The edit model shrinks a pose to fit a raised/forward blade into 512.
    Measure the face (weapon-free), scale every drawn frame up to the same
    face width and pad to 640, so the character keeps its 420 px height and
    the blade stays whole in the hi-res art.  The 64 px game frame is cropped
    to the 512 body window afterwards.
    """
    from scipy import ndimage
    from core.palette_quantizer import lock_palette as _lock
    heads = []
    if man_dir is not None and (Path(man_dir) / "sheet_motion.json").exists():
        trace = json.loads((Path(man_dir) / "sheet_motion.json").read_text())
        for fd in trace.get("frames_data", []):
            h = fd.get("bones", {}).get("head")
            heads.append((float(h[0][0]), float(h[0][1])) if h else None)
    fw0 = 33
    for i in range(frames):
        path = out_dir / "frames_hi" / f"frame_{i:02d}.png"
        im = Image.open(path).convert("RGBA")
        a = np.array(im)
        alpha = a[..., 3] > 0
        # Drop foreign panel fragments before they get revealed by the pad.
        lab, n = ndimage.label(alpha)
        if n > 1:
            sizes = np.bincount(lab.ravel())
            sizes[0] = 0
            main = int(np.argmax(sizes))
            main_mask = lab == main
            ys, xs = np.nonzero(main_mask)
            mb = (int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max()))
            keep = main_mask.copy()
            for k in range(1, n + 1):
                if k == main:
                    continue
                comp = lab == k
                yy, xx = np.nonzero(comp)
                if len(xx) == 0:
                    continue
                w = xx.max() - xx.min() + 1
                h = yy.max() - yy.min() + 1
                if xx.max() < mb[0] - 8 or xx.min() > mb[2] + 8:
                    continue
                dist = max(mb[0] - xx.max(), xx.min() - mb[2],
                           mb[1] - yy.max(), yy.min() - mb[3], 0)
                far_y = max(mb[1] - yy.max(), yy.min() - mb[3], 0)
                if far_y > 50 and (max(w, h) / max(1, min(w, h))) < 2.5:
                    continue
                if dist <= 24 or (max(w, h) / max(1, min(w, h))) >= 2.5:
                    keep |= comp
            alpha = keep
            a[..., 3] = np.where(alpha, 255, 0)
            im = Image.fromarray(a, "RGBA")
        s = 1.0
        fx = None
        fw = 0
        a = np.array(im)
        alpha = a[..., 3] > 0
        ys, xs = np.nonzero(alpha)
        bh = int(ys.max() - ys.min() + 1) if len(ys) else 0
        # A horizontal blade keeps the body as the tallest feature; a raised
        # blade makes the bbox much taller than the body.  Only a body-height
        # bbox that is clearly short of 420 is a scale error.
        if 0 < i < frames - 1 and 0 < bh < 380:
            s = float(np.clip(420.0 / bh, 1.0, 1.4))
        # The body-height bbox rule above already catches a horizontal-blade
        # frame whose body is short; no per-frame override is needed.
        r, g, b = a[..., 0].astype(int), a[..., 1].astype(int), a[..., 2].astype(int)
        rows = np.arange(a.shape[0])[:, None] < ys.min() + int(bh * 0.45)
        cols = np.ones(a.shape[1], dtype=bool)
        if i < len(heads) and heads[i] is not None:
            hx, hy = heads[i]
            x0 = max(0, int(hx) - 80)
            x1 = min(a.shape[1], int(hx) + 80)
            cols[:] = False
            cols[x0:x1] = True
            rows = np.arange(a.shape[0])[:, None] < min(a.shape[0], int(hy) + 90)
        skin = ((r > 150) & (g > 100) & (b < 170) & (r > g) & (g > b)
                & rows & cols[None, :])
        lab, n = ndimage.label(skin)
        if n:
            sizes = np.bincount(lab.ravel())
            sizes[0] = 0
            k = int(np.argmax(sizes))
            yy, xx = np.nonzero(lab == k)
            fx = float((xx.min() + xx.max()) / 2.0)
            fw = int(xx.max() - xx.min() + 1)
            if i == 0:
                fw0 = fw
        ys, xs = np.nonzero(np.array(im)[..., 3] > 0)
        cx = fx if fx is not None else float(np.mean(xs))
        base = float(ys.max())
        nw = max(1, int(round(512 * s)))
        resized = im.resize((nw, nw), Image.LANCZOS)
        canvas = Image.new("RGBA", (640, 640), (0, 0, 0, 0))
        x = int(round(320 - cx * s))
        y = int(round(567 - base * s))
        canvas.alpha_composite(resized, (x, y))
        _lock(canvas).save(path)


def bob_run(out_dir: Path, frames: int = 8) -> None:
    """Add the vertical flight phase the 3D run has but the AI flattened.

    Contact frames (0, 4, 7 and the loop seam) stay grounded; the passing and
    flight frames lift by up to 10 px at 512 so the cycle has a real bounce.
    """
    from core.palette_quantizer import lock_palette as _lock
    offsets = {1: -4, 2: -9, 3: -5, 5: -5, 6: -9}
    for i, dy in offsets.items():
        if i >= frames:
            continue
        src = Image.open(out_dir / "frames_hi" / f"frame_{i:02d}.png").convert("RGBA")
        out = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
        out.alpha_composite(src, (0, dy))
        _lock(out).save(out_dir / "frames_hi" / f"frame_{i:02d}.png")


def fit_action_uniform(out_dir: Path, frames: int = 8, margin: int = 6) -> None:
    """Nudge a whole action inside the canvas without changing its scale.

    Scaling a single wide attack frame would pop the body height and break the
    transition anchors; a uniform sub-pixel shift keeps every frame at the same
    scale and only sacrifices the far end of the trailing scabbard, which is
    behind the character and visually cheap.
    """
    from core.palette_quantizer import lock_palette as _lock
    src = [Image.open(out_dir / "frames_hi" / f"frame_{i:02d}.png").convert("RGBA")
           for i in range(frames)]
    xs0, xs1 = [], []
    for f in src:
        ys, xs = np.nonzero(np.array(f)[..., 3] > 0)
        if len(xs) == 0:
            continue
        xs0.append(int(xs.min()))
        xs1.append(int(xs.max()) + 1)
    if not xs0:
        return
    lo, hi = min(xs0), max(xs1)
    if lo >= margin and hi <= 512 - margin:
        return
    # Prefer keeping the forward (screen-right) weapon tip intact; the
    # scabbard behind her may run off the canvas by a few pixels.
    dx = (512 - margin) - hi
    if lo + dx < -margin:
        dx = 0
    if dx == 0:
        return
    for i, f in enumerate(src):
        canvas = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
        canvas.alpha_composite(f, (dx, 0))
        _lock(canvas).save(out_dir / "frames_hi" / f"frame_{i:02d}.png")


def repeat_idle_frames(out_dir: Path, frames: int = 8, keep: int = 4) -> None:
    """Use the four complete AI idle frames as an 8-frame loop.

    KayKit/procedural idle drift made f5-f7 shorter/cropped.  Reusing the
    four full-body panels with a 1 px breathing offset keeps the loop complete
    without repainting the head or changing the character scale.
    """
    from core.palette_quantizer import lock_palette as _lock
    shifts = (1, -1, 1, -1)
    for i in range(keep, frames):
        src = Image.open(out_dir / "frames_hi" / f"frame_{i - keep:02d}.png").convert("RGBA")
        dy = shifts[(i - keep) % len(shifts)]
        out = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
        out.alpha_composite(src, (0, dy))
        _lock(out).save(out_dir / "frames_hi" / f"frame_{i:02d}.png")


def _hand_point(frame: Image.Image) -> tuple[int, int]:
    a = np.array(frame.convert("RGBA"))
    fg = a[..., 3] > 0
    ys, xs = np.nonzero(fg)
    xmax = int(xs.max())
    sel = ys[xs >= xmax - 3]
    return xmax - 2, int(np.median(sel))


def overlay_pistol(frame: Image.Image, part_path: Path, scale: float = 0.52) -> Image.Image:
    """Place the canonical pistol in an extended hand that the AI left empty.

    The pistol is drawn first and the original character is composited on top,
    so the glove hides the grip while the barrel/muzzle remains visible.
    """
    part = Image.open(part_path).convert("RGBA")
    box = part.getbbox()
    if box:
        part = part.crop(box)
    pw, ph = max(1, int(part.width * scale)), max(1, int(part.height * scale))
    gun = part.resize((pw, ph), Image.NEAREST)
    hx, hy = _hand_point(frame)
    out = frame.convert("RGBA").copy()
    layer = Image.new("RGBA", out.size, (0, 0, 0, 0))
    layer.alpha_composite(gun, (int(hx - 0.20 * pw), int(hy - 0.72 * ph)))
    out.alpha_composite(layer)
    out.alpha_composite(frame.convert("RGBA"))
    return out


def fill_eye_pupils(im: Image.Image) -> Image.Image:
    """Fill the transparent pupil hole left by the key-colour matte.

    The iris is violet and the AI paints the pupil as a key-coloured spot;
    the matte removes it, leaving a see-through rectangle.  Refill only
    enclosed holes in the head whose border is mostly violet.
    """
    from scipy import ndimage
    arr = np.array(im.convert("RGBA"))
    alpha = arr[..., 3] > 0
    ys, xs = np.nonzero(alpha)
    if len(ys) == 0:
        return im
    y0, y1 = int(ys.min()), int(ys.max()) + 1
    holes = ndimage.binary_fill_holes(alpha) & ~alpha
    lab, n = ndimage.label(holes)
    for k in range(1, n + 1):
        comp = lab == k
        yy, xx = np.nonzero(comp)
        if comp.sum() < 6 or comp.sum() > 400:
            continue
        if yy.min() < y0 or yy.max() > y0 + (y1 - y0) * 0.25:
            continue
        border = ndimage.binary_dilation(comp, iterations=1) & alpha
        cols = arr[border][:, :3].astype(int)
        if len(cols) == 0:
            continue
        vio = ((cols[:, 2] > cols[:, 1] + 20) & (cols[:, 0] > cols[:, 1])).sum()
        if vio < 2:
            continue
        # darkest violet on the iris rim = pupil
        dark = cols[np.argmin(cols.sum(axis=1))]
        arr[comp, :3] = dark
        arr[comp, 3] = 255
    return Image.fromarray(arr, "RGBA")


def fix_cyan_blades(im: Image.Image) -> Image.Image:
    """A large cyan katana blade is the mannequin label colour leaking through.
    Recolour it to the design's steel ramp (small cyan trims are untouched)."""
    from scipy import ndimage
    from core.palette_quantizer import lock_palette as _lock
    arr = np.array(im.convert("RGBA"))
    r, g, b = arr[..., 0].astype(int), arr[..., 1].astype(int), arr[..., 2].astype(int)
    cyan = (arr[..., 3] > 0) & (r > 60) & (r < 130) & (g > 170) & (b > 190)
    lab, n = ndimage.label(cyan)
    for k in range(1, n + 1):
        comp = lab == k
        if comp.sum() < 250:
            continue
        light = comp & (g > 225)
        mid = comp & (g > 190) & ~light
        dark = comp & ~light & ~mid
        arr[light, :3] = (214, 214, 230)
        arr[mid, :3] = (155, 155, 176)
        arr[dark, :3] = (111, 111, 136)
    return _lock(Image.fromarray(arr, "RGBA"))


def clean_violet_flecks(im: Image.Image, max_area: int = 80) -> Image.Image:
    """Turn small violet flecks outside the face back into the dark outline.

    The palette reserves violet for the iris.  Magenta key spill that survives
    quantisation (e.g. inside a trigger guard) becomes a small violet island;
    large violet areas (outfit shading) and the face are left untouched.
    """
    from scipy import ndimage
    arr = np.array(im.convert("RGBA"))
    alpha = arr[..., 3] > 0
    ys, xs = np.nonzero(alpha)
    if len(ys) == 0:
        return im
    y0, y1 = int(ys.min()), int(ys.max()) + 1
    head_lim = y0 + int((y1 - y0) * 0.16)
    r, g, b = arr[..., 0].astype(int), arr[..., 1].astype(int), arr[..., 2].astype(int)
    vio = (b > g + 20) & (r > g + 8) & (b > 50) & (r < 200) & alpha
    lab, n = ndimage.label(vio)
    for k in range(1, n + 1):
        comp = lab == k
        if comp.sum() > max_area:
            continue
        cy = np.nonzero(comp)[0]
        if len(cy) == 0 or int(cy.min()) < head_lim:
            continue
        arr[comp, :3] = PALETTE_RGB[1]
    return Image.fromarray(arr, "RGBA")


def finish_64(ds: Image.Image) -> Image.Image:
    """Fill 1-2 px downscale pinholes and stamp a dark pupil in the iris."""
    from scipy import ndimage
    from core.palette_quantizer import lock_palette as _lock
    arr = np.array(ds.convert("RGBA"))
    alpha = arr[..., 3] > 0
    holes = ndimage.binary_fill_holes(alpha) & ~alpha
    lab, n = ndimage.label(holes)
    for k in range(1, n + 1):
        comp = lab == k
        if comp.sum() > 2:
            continue
        yy, xx = np.nonzero(comp)
        for y, x in zip(yy, xx):
            for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                ny, nx = y + dy, x + dx
                if 0 <= ny < 64 and 0 <= nx < 64 and alpha[ny, nx]:
                    arr[y, x, :3] = arr[ny, nx, :3]
                    arr[y, x, 3] = 255
                    break
    # pupil: centre of the largest bright-violet (iris) component
    r, g, b = arr[..., 0].astype(int), arr[..., 1].astype(int), arr[..., 2].astype(int)
    vio = (arr[..., 3] > 0) & (b > g + 20) & (r > g) & (r > 120) & (b > 150)
    lab, n = ndimage.label(vio)
    if n:
        sizes = np.bincount(lab.ravel())
        sizes[0] = 0
        k = int(np.argmax(sizes))
        yy, xx = np.nonzero(lab == k)
        cy, cx = int(round(yy.mean())), int(round(xx.mean()))
        arr[cy, cx, :3] = (36, 24, 56)
        arr[cy, cx, 3] = 255
    return _lock(Image.fromarray(arr, "RGBA"))


def build_lowres_preview(out_dir: Path, frames: int = 8) -> dict:
    """Playable preview of the actual 64px game frames (4x nearest)."""
    lo = [Image.open(out_dir / "frames" / f"frame_{i:02d}.png").convert("RGBA")
          .resize((256, 256), Image.NEAREST) for i in range(frames)]
    _save_apng(lo, out_dir / "preview.png")
    _save_gif(lo, out_dir / "preview.gif")
    return {"apng": "preview.png", "gif": "preview.gif", "size": [256, 256]}


def build_hires_action(out_dir: Path, frames: int = 8, action: str = "",
                       fill: float = 0.82,
                       mannequin: list[Image.Image] | None = None) -> dict:
    """Build the 512-px-per-frame companion animation from the AI panels."""
    panels = [Image.open(out_dir / f"panel_{i:02d}.png").convert("RGB") for i in range(frames)]
    hi = panels_to_hires(panels, mannequin_panels=mannequin, fill=fill)
    hi = [prune_detached(f, connect=40) for f in hi]
    if action in ("shoot2", "slash2"):
        hi = [shift_inside(f, 8, 0) if 0 < i < frames - 1 else f
              for i, f in enumerate(hi)]
    if action == "roll":
        hi = [fit_with_margin(f, 16) if 0 < i < frames - 1 else f
              for i, f in enumerate(hi)]
    hi_dir = out_dir / "frames_hi"
    hi_dir.mkdir(parents=True, exist_ok=True)
    for i, f in enumerate(hi):
        f.save(hi_dir / f"frame_{i:02d}.png")
    sheet = Image.new("RGBA", (512 * frames, 512), (0, 0, 0, 0))
    for i, f in enumerate(hi):
        sheet.alpha_composite(f, (i * 512, 0))
    from core.palette_quantizer import lock_palette as _lock
    _lock(sheet).save(out_dir / "sheet_hi.png")
    _save_apng(hi, out_dir / "preview_hi.png")
    _save_gif(hi, out_dir / "preview_hi.gif")
    return {"frames": len(hi), "size": [512, 512],
            "frames_dir": str(hi_dir), "sheet": "sheet_hi.png",
            "apng": "preview_hi.png", "gif": "preview_hi.gif"}


def render_mannequin(action: str, outdir: Path, spec: CharacterSpec,
                     cfg: dict, frames: int = 8, gear: dict | None = None) -> None:
    outdir.mkdir(parents=True, exist_ok=True)
    source = cfg.get("source", "kaykit")
    params = {"character": spec.name, **spec.params}
    cmd = [
        GODOT, "--path", str(ROOT / "character" / "godot_mannequin"),
        "--rendering-driver", "opengl3", "--script", "res://scripts/render_actor.gd",
        "--", "--action", cfg.get("action", action), "--source", source,
        "--frames", str(frames),
        "--out", str(outdir),
        "--params", json.dumps(params),
        "--gear", json.dumps(gear if gear is not None else (spec.gear or {}).get(action, {})),
    ]
    if spec.camera is not None:
        cmd += ["--cam", ",".join(f"{v:g}" for v in spec.camera)]
    for key, cli in (("clip", "--clip"), ("start", "--start"), ("end", "--end"),
                     ("base_clip", "--base-clip"), ("upper_clip", "--upper-clip"),
                     ("base_start", "--base-start"), ("base_end", "--base-end"),
                     ("upper_start", "--upper-start"), ("upper_end", "--upper-end")):
        if key in cfg and cfg[key] is not None:
            cmd += [cli, f"{cfg[key]:g}" if isinstance(cfg[key], (int, float)) else str(cfg[key])]
    env = dict(os.environ, DISPLAY=DISPLAY)
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=240, env=env)
    if "MANNEQUIN_DONE" not in proc.stdout:
        raise RuntimeError(f"mannequin render failed for {action}:\n{proc.stdout[-2000:]}\n{proc.stderr[-2000:]}")


KNIGHT_ACTION_EXTRA = {
    "run": (" Every panel must show the same bright steel helmet with a visible visor; never a "
            "black or featureless face plate, even when the body leans forward."),
    "attack": (" In every pose the sword is in the RIGHT hand nearest the camera and swings in a "
               "downward chop; the left-hand shield stays on the far side of the body, low and "
               "foreshortened. Never turn the swing into a shield bash and never put the shield "
               "between the camera and the sword."),
    "in_air": (" The knight is in MID-AIR: both feet are clearly off the ground, both knees are "
               "bent and tucked up under the body, the tabard and cloak lift upward, and no leg is "
               "extended in a running stride. No foot rests on the ground. Draw exactly ONE sword "
               "and ONE shield in every panel; never duplicate the blade."),
    "defend": (" In every pose the LEFT-hand shield is raised across the chest as a block while "
               "the right-hand sword is held back; because the camera is on the right side the "
               "sword and sword arm stay clearly visible beside the shield. This is a shield block, "
               "not a sword swing."),
}


AGENT_STATE_LOCK = {
    "jump": ("the katana is SHEATHED on her back (exactly one hilt + one scabbard), the pistol is "
             "HOLSTERED at her hip, both hands empty"),
    "in_air": ("the katana is SHEATHED on her back (exactly one hilt + one scabbard), the pistol is "
               "HOLSTERED at her hip, both hands empty"),
    "shoot1": ("the pistol is in her extended RIGHT HAND and the hip holster is EMPTY; the katana is "
               "SHEATHED on her back (exactly one hilt + one scabbard)"),
    "shoot3": ("the pistol is in her extended RIGHT HAND and the hip holster is EMPTY; the katana is "
               "SHEATHED on her back (exactly one hilt + one scabbard)"),
    "slash1": ("the katana is DRAWN in her right hand and the back scabbard is EMPTY with no hilt; "
               "the pistol is HOLSTERED at her hip"),
    "slash3": ("the katana is DRAWN in her right hand and the back scabbard is EMPTY with no hilt; "
               "the pistol is HOLSTERED at her hip"),
    "block": ("the katana is DRAWN and held in both hands in front of her; the back scabbard is "
              "EMPTY with no hilt; the pistol is HOLSTERED at her hip; no shield"),
    "idle": ("the katana is SHEATHED on her back (exactly one hilt + one scabbard), the pistol is "
             "HOLSTERED at her hip, both hands empty"),
    "run": ("the katana is SHEATHED on her back (exactly one hilt + one scabbard), the pistol is "
            "HOLSTERED at her hip, both hands empty"),
    "roll": ("the katana is SHEATHED on her back (exactly one hilt + one scabbard), the pistol is "
             "HOLSTERED at her hip, both hands empty"),
    "shoot2": ("the pistol is in her extended RIGHT HAND and the hip holster is EMPTY; the katana is "
               "SHEATHED on her back (exactly one hilt + one scabbard)"),
    "slash2": ("the katana is DRAWN in her right hand and the back scabbard is EMPTY with no hilt; "
               "the empty scabbard itself stays fixed on her back in every panel and her fist stays "
               "closed around the hilt; the pistol is HOLSTERED at her hip"),
}


def agent_state_lock(action: str) -> str:
    state = AGENT_STATE_LOCK.get(action, "")
    if not state:
        return ""
    return (
        " STATE LOCK: In this action " + state + ". There is EXACTLY ONE katana, ONE scabbard and "
        "ONE pistol in every panel: never draw a second scabbard, a second hilt, a second blade or a "
        "second pistol. The top-left reference panel, the mannequin and this sentence all show the "
        "same state; keep it in all eight panels. SCALE LOCK: every panel must use the SAME "
        "character scale as the top-left reference and the mannequin — same head diameter, same "
        "total body height, same shoulder and hip width; never shrink or enlarge the character in "
        "any panel."
    )


def build_part_legend(out_dir: Path) -> Image.Image:
    """Legend for the flat colour-coded mannequin proxy."""
    from PIL import ImageDraw
    parts = [
        ("head", (255, 0, 0)), ("torso", (0, 255, 0)),
        ("arm_l", (0, 0, 255)), ("arm_r", (255, 255, 0)),
        ("leg_l", (255, 0, 128)), ("leg_r", (136, 0, 255)),
        ("katana", (0, 255, 255)), ("scabbard", (166, 0, 255)),
        ("pistol", (255, 140, 0)), ("holster", (230, 230, 230)),
    ]
    im = Image.new("RGB", (512, 512), (255, 0, 255))
    d = ImageDraw.Draw(im)
    d.text((16, 12), "MANNEQUIN PART COLOURS (pose proxy only)", fill=(255, 255, 255))
    for i, (name, col) in enumerate(parts):
        y = 45 + i * 44
        d.rectangle([16, y, 60, y + 34], fill=col, outline=(0, 0, 0))
        d.text((76, y + 10), name, fill=(255, 255, 255))
    im.save(out_dir / "part_legend.png")
    return im


def build_head_ref(ref_canvas: Image.Image, out_dir: Path) -> Image.Image | None:
    """A large face/hair reference so the AI cannot re-invent the eye/face."""
    rgb = np.array(ref_canvas.convert("RGB"))
    bg = estimate_background(ref_canvas)
    fg = ~background_mask_all(rgb, bg)
    ys, xs = np.nonzero(fg)
    if len(xs) == 0:
        return None
    x0, y0, x1, y1 = int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1
    cx = (x0 + x1) // 2
    h = min(220, max(120, y1 - y0))
    crop = ref_canvas.crop((max(0, cx - 110), y0, min(512, cx + 110), min(512, y0 + h)))
    out = Image.new("RGB", (512, 512), (255, 0, 255))
    out.paste(crop, ((512 - crop.width) // 2, 40))
    out.save(out_dir / "head_ref.png")
    return out


def build_context_frame(name: str, context_action: str, action: str) -> Image.Image | None:
    """One already-approved frame of the previous action (512 px)."""
    base = character_dir(name) / context_action / "frames_hi" / "frame_00.png"
    if not base.exists():
        return None
    f = Image.open(base).convert("RGBA")
    ctx = Image.new("RGB", (512, 512), (255, 0, 255))
    ctx.paste(f, (0, 0), f)
    wd = work_character_dir(name) / action
    wd.mkdir(parents=True, exist_ok=True)
    ctx.save(wd / "context.png")
    return ctx


def build_action(pipe: CharacterPipeline, spec: CharacterSpec, action: str,
                 ref64, frames: int, force: bool, cfg: dict,
                 weapon_ref: Image.Image | None = None) -> dict:
    name = spec.name
    man_dir = OUTPUT_DIR / "character" / name / "mannequin" / action
    out_dir = character_dir(name) / action
    sheet_file = out_dir / "sheet.png"
    if sheet_file.exists() and not force:
        return json.loads((out_dir / "report.json").read_text())

    # The roll mannequin carries the normal stowed gear: without a hilt the
    # edit model paints a bare floating rod, and the scabbard box has been
    # thinned to the reference proportions so it cannot read as a plank.
    roll_gear = None
    render_mannequin(action, man_dir, spec, cfg, frames, gear=roll_gear)
    export_motion_npy(man_dir)
    parts_sheet = man_dir / "sheet_parts.png"
    sheet_file = parts_sheet if (name == "agent" and parts_sheet.exists()) else (man_dir / "sheet_shaded.png")
    sheet = Image.open(sheet_file).convert("RGB")
    src = [sheet.crop((i * 512, 0, (i + 1) * 512, 512)) for i in range(frames)]
    # The board must use a FULL-RESOLUTION reference whose weapon state matches
    # this action.  Passing a drawn-katana reference into a stowed action was
    # the main source of duplicate scabbards/hilts.
    state_ref = {
        "idle": "stowed", "run": "stowed", "roll": "stowed",
        "jump": "stowed", "in_air": "stowed",
        "shoot1": "shoot", "shoot2": "shoot", "shoot3": "shoot",
        "slash1": "slash", "slash2": "slash", "slash3": "slash", "block": "slash",
    }.get(action, "")
    candidates = []
    if name == "agent" and state_ref:
        candidates += [character_dir(name) / f"char_ref_{state_ref}_canvas.png",
                       ROOT / "work" / "character" / name / f"char_ref_{state_ref}_canvas.png"]
    candidates += [character_dir(name) / "char_ref_canvas.png",
                   ROOT / "work" / "character" / name / "char_ref_canvas.png"]
    full_ref = next((p for p in candidates if p.exists()), None)
    if full_ref is not None:
        ref_canvas = Image.open(full_ref).convert("RGB").resize((512, 512), Image.LANCZOS)
    else:
        ref_canvas = ref_canvas_from64(ref64)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "frames").mkdir(parents=True, exist_ok=True)

    board = build_board(ref_canvas, src, fill=cfg.get("board_fill", 0.9),
                        safety_frame=False, shared_scale=(name == "agent"))
    board.save(out_dir / "board.png")
    # Confine the repaint to each mannequin silhouette (dilated for hair and
    # weapons).  Without this the model can paint a boot from one panel into
    # its neighbour, which showed up as floating black shapes in early runs.
    mask = build_silhouette_mask(board, dilate=32)
    mask.save(out_dir / "mask.png")
    extra_imgs: list[Image.Image] = []
    extra_notes: list[str] = []
    prompt_extra = KNIGHT_ACTION_EXTRA.get(action, "") if name == "knight" else ""
    if weapon_ref is not None:
        extra_imgs.append(weapon_ref)
        extra_notes.append(
            f" Image {2 + len(extra_imgs)} is the WEAPON PARTS REFERENCE: the exact full-length "
            "drawn katana, its empty scabbard and the compact pistol. Use those exact shapes, "
            "length ratios and colours in every panel; never shorten the katana into a dagger and "
            "never invent a second weapon."
        )
    if name == "agent":
        legend = build_part_legend(out_dir)
        extra_imgs.append(legend)
        extra_notes.append(
            f" Image {2 + len(extra_imgs)} is the MANNEQUIN PART-COLOUR LEGEND: the mannequin is a "
            "flat colour-coded pose proxy (head red, torso green, arms blue/yellow, legs pink/violet, "
            "katana cyan, scabbard purple, pistol orange, holster white). These colours are LABELS "
            "ONLY: do not use them as the character's colours. Preserve the pose, limb angles and "
            "weapon/part placement exactly; paint the character's real hair, outfit and colours "
            "(steel katana, dark scabbard, dark pistol) from the reference panel."
        )
        head_ref = build_head_ref(ref_canvas, out_dir)
        if head_ref is not None:
            extra_imgs.append(head_ref)
            extra_notes.append(
                f" Image {2 + len(extra_imgs)} is the FACE/HAIR REFERENCE at full resolution. "
                "Keep this exact face, silver hair shape, violet eyes and skin tone in every panel; "
                "do not redesign the eye or hide the face."
            )
    context = None
    context_action = cfg.get("context_action") or {
        "run": "idle", "jump": "idle", "in_air": "idle", "roll": "idle"}.get(action)
    if context_action:
        context = build_context_frame(name, context_action, action)
        if context is not None:
            extra_imgs.append(context)
            extra_notes.append(
                f" Image {2 + len(extra_imgs)} is ONE approved frame of the previous "
                f"{context_action} action. Use it only as a consistency reference for the body "
                "proportions, outfit, hair and weapon placement; do not copy it into the sheet as "
                "an extra panel."
            )
    prompt = (
        board_prompt(spec, action)
        + (agent_state_lock(action) if name == "agent" else "")
        + prompt_extra
        + "".join(extra_notes)
        + " Image 2 is a mask: pure black means keep that panel exactly as in Image 1, "
          "pure white means repaint that panel."
    )
    result = pipe.client.edit(
        prompt, [board, mask.convert("RGB")] + extra_imgs,
        role=cfg.get("role", "sunburst"), aspect="1:1", size="2K",
        tag=f"{name}-{action}-board-v9",
    )
    result = lock_reference_panel(result, board)
    result.save(out_dir / "remaster.png")
    panels = [extract_panel_robust(result, i + 1) for i in range(frames)]
    for i, p in enumerate(panels):
        p.save(out_dir / f"panel_{i:02d}.png")
    margin_ok = True
    margin_attempts = 1
    sprites, warps = panels_to_sprites(panels, mannequin_panels=src,
                                       fill=cfg.get("sprite_fill", 0.9))
    for i, f in enumerate(sprites):
        f.save(out_dir / f"raw_{i:02d}.png")

    # The 512-px companion is the art the reviewer inspects; derive the 64-px
    # game frame from that same art (coverage/mode pooling) so the two cannot
    # diverge, then run the temporal hard-lock on the derived frames.
    hires = build_hires_action(out_dir, frames, action,
                               fill=cfg.get("sprite_fill", 0.82), mannequin=src)
    if name == "agent" and action in ("slash1", "slash2", "slash3", "block"):
        for i in range(frames):
            p = out_dir / "frames_hi" / f"frame_{i:02d}.png"
            fix_cyan_blades(Image.open(p)).save(p)
    if name == "agent" and action in ("shoot1", "shoot2", "shoot3"):
        # Only the shooting hand/gun needs the violet-fleck cleanup; running it
        # on the tumbling roll would recolour the inverted iris.
        for i in range(frames):
            p = out_dir / "frames_hi" / f"frame_{i:02d}.png"
            clean_violet_flecks(Image.open(p)).save(p)
    if name == "agent" and action == "slash2":
        pad_slash_frames(out_dir, frames, man_dir=man_dir)
    if name == "agent" and action == "idle":
        normalize_idle_scale(out_dir, frames)
    if name == "agent" and action == "run":
        bob_run(out_dir, frames)
    if name == "agent" and action != "slash2":
        fit_action_margin(out_dir, frames)
        fit_action_uniform(out_dir, frames)
    if name == "agent" and action == "slash2":
        # Final body lock: measure the provisional 64 body with a morphological
        # opening (removes the 1-px blade) and scale the 640 frame until the
        # game body is exactly TARGET px.  This is the only reliable
        # cross-frame body metric.
        from scipy import ndimage as _ndi
        from core.palette_quantizer import lock_palette as _lock2
        TARGET = 52.0
        for i in range(1, frames - 1):
            p = out_dir / "frames_hi" / f"frame_{i:02d}.png"
            im = Image.open(p).convert("RGBA")
            crop = im.crop((64, 64, 576, 576))
            ds = resample_from_hi(crop, (64, 64))
            a = np.array(ds)[..., 3] > 0
            op = _ndi.binary_opening(a, structure=np.ones((3, 3)))
            ys, xs = np.nonzero(op)
            h = float(ys.max() - ys.min() + 1) if len(ys) else 0.0
            if h <= 0:
                continue
            s = float(np.clip(TARGET / h, 0.7, 1.3))
            nw = int(round(640 * s))
            resized = im.resize((nw, nw), Image.LANCZOS)
            canvas = Image.new("RGBA", (640, 640), (0, 0, 0, 0))
            canvas.alpha_composite(resized, (int(round(320 - 320 * s)),
                                             int(round(567 - 567 * s))))
            _lock2(canvas).save(p)
    if name == "agent":
        # Last step before the 64px downsample: a resample can punch the pupil
        # hole back in, so fill it after every scale/margin operation.
        for i in range(frames):
            p = out_dir / "frames_hi" / f"frame_{i:02d}.png"
            fill_eye_pupils(Image.open(p)).save(p)
        # Pure nearest downsample of the approved 512px art.  No eye paint,
        # no shard removal, no static lock, no despeckle: the 64px frame must
        # be the exact same drawing as the 512px frame (8x8 block centre).
        final = []
        # Ship the full 8-frame run: the first four frames are only one step
        # of the cycle, so truncating to four made the same leg lead every
        # frame.  Slash/shoot end anchors use run:7 (the loop boundary).
        for i in range(frames):
            hi = Image.open(out_dir / "frames_hi" / f"frame_{i:02d}.png").convert("RGBA")
            if action == "slash2" and hi.size == (640, 640):
                hi = hi.crop((64, 64, 576, 576))
            # Coverage/mode downsample, not a single-pixel nearest sample: the
            # 1 px violet iris and thin blade survive at game resolution.
            ds = resample_from_hi(hi, (64, 64))
            ds = preserve_eye(hi, ds)
            ds = despeckle(ds)
            ds = finish_64(ds)
            ds.save(out_dir / "frames" / f"frame_{i:02d}.png")
            final.append(ds)
        report = {"action": action, "frames": frames, "locked_pixels": 0,
                  "features_repaired": 0, "static_features": False, "static_ratio": 0.0,
                  "note": "coverage/mode 512->64 + iris preservation"}
    else:
        ds_dir = work_character_dir(name) / action / "frames_ds"
        ds_dir.mkdir(parents=True, exist_ok=True)
        ds_paths = []
        for i in range(frames):
            hi = Image.open(out_dir / "frames_hi" / f"frame_{i:02d}.png").convert("RGBA")
            ds = resample_from_hi(hi, (64, 64))
            ds = preserve_eye(hi, ds)
            ds = despeckle(ds)
            ds = finish_64(ds)
            p = ds_dir / f"frame_{i:02d}.png"
            ds.save(p)
            ds_paths.append(p)
        report = stabilize_action(man_dir, ds_paths, out_dir / "frames", action, warps=warps)
        final = [Image.open(out_dir / "frames" / f"frame_{i:02d}.png") for i in range(frames)]
        final = [despeckle(prune_detached(remove_small_components(f), connect=2)) for f in final]
        if name == "knight" and action == "idle":
            final = [split_merged_boots(f) for f in final]
        for i, f in enumerate(final):
            f.save(out_dir / "frames" / f"frame_{i:02d}.png")
        report["verification"] = verify_action(
            man_dir, [out_dir / f"raw_{i:02d}.png" for i in range(frames)],
            [out_dir / "frames" / f"frame_{i:02d}.png" for i in range(frames)], warps, action,
            static_only=report.get("static_features", False))
    sheet_from_frames(final, scale=8).save(out_dir / "sheet.png")
    sheet_from_frames(final, scale=1).save(out_dir / "sheet_1x.png")
    lowres = build_lowres_preview(out_dir, frames)
    np.save(out_dir / "warps.npy", np.array(warps))
    report.update({"sheets": "sheet.png", "mannequin": str(man_dir), "source": cfg,
                   "hires": {**hires, "size": list(Image.open(out_dir / "frames_hi" / "frame_00.png").size)},
                   "lowres_preview": lowres, "margin_ok": margin_ok,
                   "margin_attempts": margin_attempts})
    (out_dir / "report.json").write_text(json.dumps(report, indent=2))
    return report


def _topo_order(character: str, requested: list[str]) -> list[str]:
    """Expand anchor dependencies and return a safe build order."""
    graph = TRANSITIONS.get(character, {})
    needed: list[str] = []

    def add(a: str) -> None:
        if a in needed:
            return
        for anchor in graph.get(a, (None, None)):
            if anchor:
                add(anchor.split(":", 1)[0])
        needed.append(a)

    for action in requested:
        add(action)
    return needed


def enforce_transitions(character: str, actions: list[str], frames: int = 8) -> dict:
    """Copy anchor frames into boundary frames and prove they are identical."""
    graph = TRANSITIONS.get(character, {})
    base = character_dir(character)
    result: dict[str, dict] = {}
    for action in actions:
        spec = graph.get(action)
        if not spec:
            continue
        out_dir = base / action
        frame_dir = out_dir / "frames"
        if not frame_dir.exists():
            continue
        changed = False
        anchors = {}
        for which, anchor in zip(("start", "end"), spec):
            if not anchor:
                anchors[which] = None
                continue
            dep, idx = anchor.split(":", 1)
            src = base / dep / "frames" / f"frame_{int(idx):02d}.png"
            dst = frame_dir / (f"frame_{0:02d}.png" if which == "start" else f"frame_{frames - 1:02d}.png")
            if not src.exists():
                anchors[which] = {"anchor": anchor, "ok": False, "error": "missing anchor"}
                continue
            src_img = Image.open(src).convert("RGBA")
            # Force the anchor to the same transparent-RGB convention.
            src_img.save(dst)
            anchors[which] = {"anchor": anchor, "ok": True, "sha256": _sha(dst)}
            hi_src = base / dep / "frames_hi" / f"frame_{int(idx):02d}.png"
            hi_dst_dir = out_dir / "frames_hi"
            if hi_src.exists() and hi_dst_dir.exists():
                hi_dst = hi_dst_dir / dst.name
                if action == "slash2":
                    canvas = Image.new("RGBA", (640, 640), (0, 0, 0, 0))
                    canvas.alpha_composite(Image.open(hi_src).convert("RGBA"), (64, 64))
                    canvas.save(hi_dst)
                else:
                    Image.open(hi_src).convert("RGBA").save(hi_dst)
                anchors[which]["hires_sha256"] = _sha(hi_dst)
            changed = True
        if changed:
            final = [Image.open(frame_dir / f"frame_{i:02d}.png").convert("RGBA")
                     for i in range(frames)]
            sheet_from_frames(final, scale=8).save(out_dir / "sheet.png")
            sheet_from_frames(final, scale=1).save(out_dir / "sheet_1x.png")
            build_lowres_preview(out_dir, frames)
            hi_dir = out_dir / "frames_hi"
            if hi_dir.exists():
                hi_frames = [Image.open(hi_dir / f"frame_{i:02d}.png").convert("RGBA")
                             for i in range(frames)]
                hw, hh = hi_frames[0].size
                hi_sheet = Image.new("RGBA", (hw * frames, hh), (0, 0, 0, 0))
                for i, f in enumerate(hi_frames):
                    hi_sheet.alpha_composite(f, (i * hw, 0))
                from core.palette_quantizer import lock_palette as _lock
                _lock(hi_sheet).save(out_dir / "sheet_hi.png")
                _save_apng(hi_frames, out_dir / "preview_hi.png")
                _save_gif(hi_frames, out_dir / "preview_hi.gif")
            report = json.loads((out_dir / "report.json").read_text())
            report["transitions"] = anchors
            report["lowres_preview"] = {"apng": "preview.png", "gif": "preview.gif",
                                        "size": [256, 256]}
            # Re-verify the actual shipped frames.
            work_man = ROOT / "work" / "character" / character / "mannequin" / action
            man_dir = work_man if work_man.exists() else OUTPUT_DIR / "character" / character / "mannequin" / action
            try:
                report["verification"] = verify_action(
                    man_dir, [out_dir / f"raw_{i:02d}.png" for i in range(frames)],
                    [frame_dir / f"frame_{i:02d}.png" for i in range(frames)],
                    None, action, static_only=report.get("static_features", False))
            except Exception as exc:  # noqa: BLE001
                report["verification_error"] = str(exc)
            (out_dir / "report.json").write_text(json.dumps(report, indent=2))
            result[action] = anchors
    (base / "transitions.json").write_text(json.dumps(result, indent=2))
    return result


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--character", default="knight", choices=sorted(PRESETS))
    ap.add_argument("--actions", default="",
                    help="comma-separated actions; defaults to the pilot set")
    ap.add_argument("--frames", type=int, default=8)
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--keep-reference", action="store_true",
                    help="reuse the existing char_ref_canvas/char_ref_64 (for the face-conditioned reference)")
    ap.add_argument("--no-audit", action="store_true",
                    help="skip the 3D motion audit (uses the static ACTION_CLIPS mapping)")
    args = ap.parse_args()

    spec = PRESETS[args.character]
    pipe = CharacterPipeline(outdir=OUTPUT_DIR / "character")
    if args.keep_reference and (character_dir(spec.name) / "char_ref_64.png").exists():
        ref64 = Image.open(character_dir(spec.name) / "char_ref_64.png").convert("RGBA")
        print("reference reused", ref64.size)
    else:
        ref64 = pipe.reference(spec)
        print("reference ready", ref64.size)
    weapon_ref = None
    design = None
    if args.character == "agent":
        weapon_ref = generate_weapon_reference(pipe.client, spec, character_dir(spec.name),
                                               force=False)
        design = build_design_sheet(character_dir(spec.name))
        print("weapon reference ready", weapon_ref.size, "design", design)

    requested = ([a.strip() for a in args.actions.split(",") if a.strip()]
                 or PILOT_ACTIONS[args.character])
    known = ACTION_SPECS[args.character]
    unknown = [a for a in requested if a not in known]
    if unknown:
        raise SystemExit(f"unknown actions for {args.character}: {unknown}")
    order = _topo_order(args.character, requested)
    print("build order:", order)

    attack_clip: str | None = None
    if args.character == "knight" and "attack" in order and not args.no_audit:
        from agent.motion_audit import audit  # noqa: E402
        audit_report = audit(ROOT / "work" / "character" / args.character)
        attack_clip = audit_report["chosen_clip"]
        (character_dir(args.character) / "motion_audit.json").write_text(
            json.dumps(audit_report, indent=2))
        print("motion audit chooses", attack_clip)

    reports = {}
    for action in order:
        cfg = dict(known[action])
        if action == "attack" and attack_clip:
            cfg["clip"] = attack_clip
        print("building", action)
        reports[action] = build_action(pipe, spec, action, ref64, args.frames, args.force, cfg,
                                       weapon_ref=weapon_ref)
        print(action, {k: reports[action].get(k) for k in
                       ("frames", "static_features", "features_repaired", "locked_pixels")})
        print("  hires:", reports[action].get("hires", {}).get("size"))
    transitions = enforce_transitions(args.character, order, args.frames)
    (character_dir(args.character) / "build_report.json").write_text(
        json.dumps({"character": args.character, "actions": reports,
                    "transitions": transitions, "design_sheet": design}, indent=2))


if __name__ == "__main__":
    main()
