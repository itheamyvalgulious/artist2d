"""Character sheet compositor (PLAN 1.2).

Generates the master character reference, builds the composite pose board
(reference panel + mannequin panels), calls the Gemini image model to restyle
every panel, then resamples each panel back to a clean 64x64 true-pixel sprite.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

from config.pipeline_config import BG_KEY_HEX, CHAR_CANVAS, CHAR_UPSCALE, ROOT
from core.api_client import GeminiImageClient
from core.grid_resampler import (
    background_mask,
    background_mask_all,
    estimate_background,
    matte_keyed,
    remove_detached_specks,
    remove_detached_specks_image,
    resample_from_hi,
    resample_sprite_coverage,
    resample_to_true_pixel,
    upscale_nearest,
)
from core.palette_quantizer import lock_palette, palette_violations

BOARD = 2048
CELL = 512
MARGIN = 256


@dataclass
class CharacterSpec:
    name: str
    description: str
    style: str = (
        "TRUE low-resolution pixel art: large crisp square pixel clusters, 1px near-black outline, "
        "32 colour limited palette, flat three-tone shading, zero anti-aliasing, zero blur, no gradients"
    )
    ref_extra: str = ""
    ref_pose: str = (
        "Orthographic near-profile view from the character's right side, about 75 degrees off "
        "the front. Neutral standing A-pose, both feet visible, entire body centred in frame."
    )
    board_extra: str = ""
    action_extra: dict = field(default_factory=dict)
    gear: dict = field(default_factory=dict)
    params: dict = field(default_factory=dict)
    camera: tuple[float, float, float] | None = None
    camera_text: str = (
        "near-profile view from the character's RIGHT side, about 75 degrees off the front, "
        "facing screen-left"
    )


DEFAULT_SPEC = CharacterSpec(
    name="knight",
    description=(
        "a wandering knight in weathered steel plate armour with a deep crimson tabard, "
        "a round wooden shield with an iron boss strapped to the left arm, and a long greatsword "
        "gripped in the right hand"
    ),
    ref_extra="helmet with a closed visor and a small crest, battle-worn plate, crimson cloth at the waist",
    ref_pose=(
        "Orthographic near-profile view from the character's RIGHT side (the sword side), about "
        "75 degrees off the front: the right arm and the greatsword are nearest the camera, the "
        "round wooden shield on the left arm is on the FAR side, mostly behind the body and seen "
        "at a steep foreshortened angle so it never covers the chest or the sword. Neutral standing "
        "A-pose, both feet visible, entire body from head to boots centred in frame with a margin "
        "on every side."
    ),
)


# ----------------------------------------------------------------------------
# Reference generation
# ----------------------------------------------------------------------------
def generate_reference(client: GeminiImageClient, spec: CharacterSpec, outdir: Path) -> Image.Image:
    prompt = (
        f"Full-body 2D pixel art character sprite of {spec.description}. "
        f"{spec.ref_pose} "
        f"{spec.ref_extra}. "
        f"{spec.style}. Background: solid pure magenta #FF00FF, completely flat and empty. "
        "No grid lines, no checkerboard, no ground, no cast shadow, no text, no border, no UI."
    )
    raw = client.generate_one(prompt, role="sunburst", aspect="1:1", size="2K", tag=f"ref-{spec.name}-right75")
    outdir.mkdir(parents=True, exist_ok=True)
    raw.save(outdir / "char_ref_raw.png")
    canvas = fit_to_canvas(raw, 512, fill=0.94)
    canvas.save(outdir / "char_ref_canvas.png")
    # Clean 512-px reference: same composition as the canvas, magenta keyed
    # out and palette locked so it can ship next to the 64-px master.
    from core.grid_resampler import background_mask, estimate_background
    rgb = np.array(canvas)
    bg = estimate_background(canvas)
    mask = background_mask_all(rgb, bg)
    ref512 = np.dstack([rgb, np.where(mask, 0, 255).astype(np.uint8)])
    ref512[..., 3] = np.where(
        remove_detached_specks(ref512[..., 3] > 0, min_area=8, near=2), 255, 0)
    lock_palette(Image.fromarray(ref512, "RGBA")).save(outdir / "char_ref_512.png")
    px = lock_palette(resample_to_true_pixel(canvas, CHAR_CANVAS))
    px.save(outdir / "char_ref_64.png")
    upscale_nearest(px, CHAR_UPSCALE).save(outdir / "char_ref_64_x16.png")
    (outdir / "char_ref_meta.json").write_text(json.dumps({
        "spec": spec.__dict__,
        "prompt": prompt,
        "violations": palette_violations(px),
    }, indent=2, ensure_ascii=False))
    return px


def generate_weapon_reference(client: GeminiImageClient, spec: CharacterSpec,
                               outdir: Path, force: bool = False) -> Image.Image:
    """Create a clean reference of every moving part (katana, scabbard, pistol).

    The character reference alone hides the blade inside its scabbard; the
    image model then invents a short blade and a mismatched hilt in the action
    panels.  This sheet shows the drawn katana, the empty scabbard and the
    pistol side by side, and is passed as a reference image to every action
    board.
    """
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    candidates = [outdir / "weapon_ref_canvas.png",
                  ROOT / "work" / "character" / spec.name / "weapon_ref_canvas.png"]
    if not force:
        for p in candidates:
            if p.exists():
                return Image.open(p).convert("RGB")
    ref = outdir / "char_ref_canvas.png"
    if not ref.exists():
        ref = ROOT / "work" / "character" / spec.name / "char_ref_canvas.png"
    input_img = Image.open(ref).convert("RGB") if ref.exists() else ref_canvas_from64(
        Image.open(outdir / "char_ref_64.png").convert("RGBA"))
    prompt = (
        "A clean 2D pixel-art WEAPON reference sheet for the character in Image 1, on a solid "
        "magenta #FF00FF background. NO character, NO hands, NO text, NO labels. Three separate "
        "items laid out left to right with wide magenta gaps: "
        "1) the full-length straight katana drawn: a long silver blade about 2.5 times the length "
        "of the dark wrapped handle, a small square guard, a cyan edge highlight; "
        "2) the empty dark katana scabbard, exactly the same length as the blade, with a silver "
        "throat and end cap; "
        "3) the compact dark pistol: a clear barrel, grip, trigger guard and a small cyan sight. "
        "Flat side-view orthographic, same pixel style and palette as Image 1: large crisp pixel "
        "clusters, 1px dark outline, 64-colour palette, zero anti-aliasing, zero gradients, no "
        "extra weapons, no shield. Every item fully inside the canvas with a margin."
    )
    raw = client.edit(prompt, [input_img], role="sunburst", aspect="1:1", size="2K",
                      tag=f"{spec.name}-weapon-ref-v1")
    raw.save(outdir / "weapon_ref_raw.png")
    canvas = fit_to_canvas(raw, 512, fill=0.94)
    canvas.save(outdir / "weapon_ref_canvas.png")
    rgb = np.array(canvas)
    bg = estimate_background(canvas)
    mask = background_mask_all(rgb, bg)
    rgba = np.dstack([rgb, np.where(mask, 0, 255).astype(np.uint8)])
    rgba[..., 3] = np.where(
        remove_detached_specks(rgba[..., 3] > 0, min_area=8, near=2), 255, 0)
    lock_palette(Image.fromarray(rgba, "RGBA")).save(outdir / "char_ref_weapons_512.png")
    return canvas


# ----------------------------------------------------------------------------
# Canvas helpers
# ----------------------------------------------------------------------------
def fit_to_canvas(raw: Image.Image, canvas: int = 512, fill: float = 0.92,
                  bottom: float = 0.985, margin: int = 6) -> Image.Image:
    """Crop the sprite to its content box and centre it on a magenta canvas.

    Fitting before pooling is what keeps a 64px sprite crisp: the character
    occupies almost the whole output canvas instead of a small island of pixels.
    """
    rgb = np.array(raw.convert("RGB"))
    bg = estimate_background(raw)
    mask = background_mask(rgb, bg)
    ys, xs = np.nonzero(~mask)
    if len(xs) == 0:
        return Image.new("RGB", (canvas, canvas), (255, 0, 255))
    x0, x1 = int(xs.min()), int(xs.max()) + 1
    y0, y1 = int(ys.min()), int(ys.max()) + 1
    crop = raw.convert("RGBA").crop((x0, y0, x1, y1))
    avail = int(canvas * fill)
    scale = min(avail / crop.width, avail / crop.height)
    nw, nh = max(1, int(round(crop.width * scale))), max(1, int(round(crop.height * scale)))
    crop = crop.resize((nw, nh), Image.LANCZOS)
    out = Image.new("RGB", (canvas, canvas), (255, 0, 255))
    x = (canvas - nw) // 2
    y = min(canvas - margin - nh, int(canvas * bottom) - nh)
    out.paste(crop, (x, max(margin, y)), crop)
    return out


def ref_canvas_from64(ref64: Image.Image) -> Image.Image:
    big = upscale_nearest(ref64, 8)
    canvas = Image.new("RGB", big.size, (255, 0, 255))
    canvas.paste(big, (0, 0), big)
    return canvas


def make_board_mask(size: tuple[int, int]) -> Image.Image:
    """White = repaint, black = locked.  Panel 0 (the reference) is locked."""
    from PIL import ImageDraw
    mask = Image.new("L", size, 255)
    draw = ImageDraw.Draw(mask)
    x0, y0, x1, y1 = board_panel_box(0)
    draw.rectangle([x0, y0, x1 - 1, y1 - 1], fill=0)
    return mask


def lock_reference_panel(result: Image.Image, board: Image.Image) -> Image.Image:
    """Force panel 0 back to the exact source reference pixels."""
    out = np.array(result.convert("RGB")).copy()
    src = np.array(board.convert("RGB"))
    x0, y0, x1, y1 = board_panel_box(0)
    out[y0:y1, x0:x1] = src[y0:y1, x0:x1]
    return Image.fromarray(out, "RGB")


def build_board(ref_canvas: Image.Image, frames: list[Image.Image],
                fill: float = 0.9, ref_fill: float = 0.94,
                safety_frame: bool = False,
                safety_inset: int = 16, safety_width: int = 3) -> Image.Image:
    """3x3 board: top-left = master reference, the other 8 = mannequin poses.

    Gemini prefers square canvases, so the single-sheet composite from PLAN 1.2
    is laid out as a 3x3 grid (ref + 8 frames) inside a 2K magenta canvas.
    """
    board = Image.new("RGB", (BOARD, BOARD), (255, 0, 255))
    panels = [fit_to_canvas(ref_canvas, CELL, fill=ref_fill)] + [
        fit_to_canvas(f, CELL, fill=fill) for f in frames]
    for i, panel in enumerate(panels[:9]):
        row, col = divmod(i, 3)
        x = MARGIN + col * CELL
        y = MARGIN + row * CELL
        board.paste(panel.resize((CELL, CELL), Image.NEAREST), (x, y))
        if safety_frame and i > 0:
            d = ImageDraw.Draw(board)
            d.rectangle([x + safety_inset, y + safety_inset,
                         x + CELL - safety_inset - 1, y + CELL - safety_inset - 1],
                        outline=(0, 255, 255), width=safety_width)
    return board


def build_silhouette_mask(board: Image.Image, dilate: int = 16) -> Image.Image:
    """Mask of the eight mannequin silhouettes (dilated) on the 3x3 board.

    The generative model may not respect a painted margin or a cyan frame, but
    it cannot paint outside an inpainting mask.  Dilating each mannequin
    silhouette by a few pixels gives the character room for hair and weapons
    while keeping every limb/weapon away from the panel edge.
    """
    from scipy import ndimage
    size = board.size
    mask = np.zeros((size[1], size[0]), dtype=np.uint8)
    for i in range(1, 9):
        x0, y0, x1, y1 = board_panel_box(i)
        panel = board.crop((x0, y0, x1, y1)).convert("RGB")
        rgb = np.array(panel)
        bg = estimate_background(panel)
        fg = ~background_mask_all(rgb, bg)
        fg = ndimage.binary_dilation(fg, iterations=dilate)
        mask[y0:y1, x0:x1] = np.where(fg, 255, 0).astype(np.uint8)
    return Image.fromarray(mask, "L")


def board_panel_box(index: int) -> tuple[int, int, int, int]:
    row, col = divmod(index, 3)
    x = MARGIN + col * CELL
    y = MARGIN + row * CELL
    return x, y, x + CELL, y + CELL


BOARD_PROMPT = (
    "A 3x3 pixel-art character sprite sheet laid out on a huge flat pure magenta #{bg} canvas. "
    "The nine 512-pixel panels form a centred grid with a wide magenta border all around. "
    "The TOP-LEFT panel is the MASTER CHARACTER REFERENCE: {desc}. "
    "The other EIGHT panels each show a crude 3D blocky mannequin in a different pose of the "
    "action '{action}'. "
    "TASK: redraw those EIGHT mannequin panels as the exact same character as the top-left "
    "reference (identical face, hair, outfit, colours, weapons and proportions), while strictly "
    "preserving each mannequin's pose, silhouette, limb angles, weapon placement and weapon "
    "direction. Keep the top-left reference panel unchanged: it supplies the character identity "
    "only. The EIGHT action panels use the MANNEQUIN'S VIEW: {camera_text}. Follow each "
    "mannequin's camera, not the reference panel's camera. {board_extra} "
    "PANEL MARGINS: leave a clear magenta margin of at least 6% of the panel width/height around "
    "the character in every panel; never crop hair, hands, feet, the katana or the pistol at a "
    "panel edge. For a roll, keep the entire tumbling body inside the panel with a wide margin. "
    "WEAPON / GEAR RULES: {gear_rules} Every weapon must remain complete and at full length in "
    "every panel; never shorten, crop, hide or duplicate a weapon. Every figure must be fully "
    "opaque and complete: no translucent shapes, no magenta or purple overlays inside the body, "
    "no black holes, no missing limbs, no extra limbs. "
    "{action_extra} "
    "Render each character fully inside its own panel, standing on solid magenta. "
    "Style: {style}. No grid lines, no panel borders, no text, no watermark, no ground shadow."
)


def gear_rules(spec: CharacterSpec, action: str) -> str:
    gear = (spec.gear or {}).get(action, {})
    if not gear:
        return (
            "Keep every stowed weapon attached to the body; draw a drawn weapon in the hand the "
            "mannequin uses, and keep the other weapon stowed."
        )
    katana = gear.get("katana", "back")
    pistol = gear.get("pistol", "hip")
    kat = {
        "hand": "the katana is drawn and held in the right hand",
        "back": "the katana is sheathed diagonally on her back with the hilt above the right shoulder",
        "none": "no katana",
    }[katana]
    pis = {
        "hand": "the pistol is drawn in the right hand and aimed forward",
        "hip": "the pistol is holstered at the right hip",
        "none": "no pistol",
    }[pistol]
    return f"{kat}; {pis}. The free weapon must stay clearly visible and must not be duplicated."


def board_prompt(spec: CharacterSpec, action: str) -> str:
    action_extra = (spec.action_extra or {}).get(action, "")
    return BOARD_PROMPT.format(
        bg=BG_KEY_HEX.lstrip("#"),
        desc=spec.description,
        action=action,
        camera_text=spec.camera_text,
        board_extra=spec.board_extra,
        gear_rules=gear_rules(spec, action),
        action_extra=action_extra,
        style=spec.style,
    )


def remaster_board(client: GeminiImageClient, board: Image.Image, spec: CharacterSpec,
                   tag: str, role: str = "sunburst", action: str = "") -> Image.Image:
    prompt = board_prompt(spec, action) if action else BOARD_PROMPT.format(
        bg=BG_KEY_HEX.lstrip("#"), desc=spec.description, action="idle",
        camera_text=spec.camera_text, board_extra=spec.board_extra,
        gear_rules=gear_rules(spec, "idle"), action_extra="", style=spec.style)
    return client.edit(prompt, [board], role=role, aspect="1:1", size="2K", tag=tag)


def remaster_board(client: GeminiImageClient, board: Image.Image, spec: CharacterSpec,
                   tag: str, role: str = "sunburst") -> Image.Image:
    prompt = BOARD_PROMPT.format(bg=BG_KEY_HEX.lstrip("#"), desc=spec.description, style=spec.style)
    return client.edit(prompt, [board], role=role, aspect="1:1", size="2K", tag=tag)


def extract_panel(board: Image.Image, index: int) -> Image.Image:
    return board.crop(board_panel_box(index))


def extract_action_panel(board: Image.Image, index: int, inset: int = 19) -> Image.Image:
    """Crop an action panel inside its cyan safety frame and restore 512 px."""
    x0, y0, x1, y1 = board_panel_box(index)
    crop = board.crop((x0 + inset, y0 + inset, x1 - inset, y1 - inset))
    return crop.resize((CELL, CELL), Image.LANCZOS)


def panel_has_margin(panel: Image.Image, margin: int = 4,
                     max_fg: int = 6) -> bool:
    """True when the outer ring of the action panel is clean magenta."""
    rgb = np.array(panel.convert("RGB")).astype(np.int16)
    fg = ~((np.minimum(rgb[..., 0], rgb[..., 2]) - rgb[..., 1]) > 60)
    ring = np.zeros(fg.shape[:2], dtype=bool)
    ring[:margin, :] = True
    ring[-margin:, :] = True
    ring[:, :margin] = True
    ring[:, -margin:] = True
    return int((fg & ring).sum()) <= max_fg


def panel_metrics(panel: Image.Image) -> dict:
    """Bounding box, content crop and lower-body centre of a panel."""
    rgb = np.array(panel.convert("RGB"))
    bg = estimate_background(panel)
    mask = background_mask(rgb, bg)
    ys, xs = np.nonzero(~mask)
    if len(xs) == 0:
        return {"crop": Image.new("RGBA", (1, 1)), "box": (0, 0, 1, 1),
                "lower_cx": 0.0, "lower_w": 1.0, "h": 0}
    x0, x1 = int(xs.min()), int(xs.max()) + 1
    y0, y1 = int(ys.min()), int(ys.max()) + 1
    crop = panel.convert("RGBA").crop((x0, y0, x1, y1))
    band = (~mask)[y0 + int((y1 - y0) * 0.55):y1, x0:x1]
    if band.any():
        bx = np.nonzero(band)[1]
        lower_cx = float(bx.mean())
        lower_w = float(bx.max() - bx.min() + 1)
    else:
        lower_cx = (x1 - x0) / 2.0
        lower_w = float(x1 - x0)
    return {"crop": crop, "box": (x0, y0, x1, y1),
            "lower_cx": lower_cx, "lower_w": lower_w, "h": y1 - y0}


def split_merged_boots(im: Image.Image, x0: int = 23, x1: int = 30,
                       y0: int = 52) -> Image.Image:
    """Carve a consistent gap between the two idle boots.

    The AI sometimes merges the two boots into one wide mass, which reads as a
    third foot.  A fixed transparent strip in the gap is applied to every idle
    frame, so the static lock sees the same gap in all frames.
    """
    arr = np.array(im.convert("RGBA"))
    arr[y0:64, x0:x1, 3] = 0
    return lock_palette(Image.fromarray(arr, "RGBA"))


def remove_small_components(im: Image.Image, min_size: int = 24) -> Image.Image:
    """Drop detached specks after stabilisation/warping (final-frame guard)."""
    arr = np.array(im.convert("RGBA"))
    lab, n = ndimage.label(arr[..., 3] > 0)
    if n > 1:
        sizes = np.bincount(lab.ravel())
        sizes[0] = 0
        for k in range(1, n + 1):
            if sizes[k] < min_size:
                arr[lab == k, 3] = 0
    return lock_palette(Image.fromarray(arr, "RGBA"))


def panels_to_sprites(panels: list[Image.Image], canvas: int = 512,
                      fill: float = 0.9, baseline: float = 0.985,
                      mannequin_panels: list[Image.Image] | None = None):
    """Convert panels to true-pixel sprites with a shared body scale.

    Returns ``(sprites, warps)`` where each warp is a 2x3 affine mapping the
    mannequin's 64x64 truth frame into the sprite's 64x64 frame (when
    ``mannequin_panels`` is supplied), so the temporal truth channels stay
    aligned with the restyled art.
    """
    metrics = [panel_metrics(p) for p in panels]
    heights = [m["h"] for m in metrics if m["h"] > 0]
    widths = [m["box"][2] - m["box"][0] for m in metrics if m["h"] > 0]
    h_med = float(np.median(heights)) if heights else 1.0
    w_max = float(max(widths)) if widths else 1.0
    scale = min(canvas * fill / max(1.0, h_med), canvas * fill / max(1.0, w_max))
    cx_med = float(np.median([m["lower_cx"] for m in metrics])) if metrics else 0.0
    # One clip-level mannequin→sprite scale.  A per-frame scale (the AI's
    # lower-body width changes with the redraw) made the truth warp breathe by
    # 10-15%, which pushed feature targets several pixels away from the art.
    clip_sa = None
    if mannequin_panels is not None:
        ratios = []
        for m, mp in zip(metrics, mannequin_panels):
            if m["h"] == 0:
                continue
            mm = panel_metrics(mp)
            ratios.append(float(np.clip(m["lower_w"] / max(1.0, mm["lower_w"]), 0.5, 2.0)))
        if ratios:
            clip_sa = float(np.median(ratios))
    sprites: list[Image.Image] = []
    warps: list[np.ndarray] = []
    for i, (crop, m) in enumerate(zip([m["crop"] for m in metrics], metrics)):
        if m["h"] == 0:
            sprites.append(Image.new("RGBA", CHAR_CANVAS, (0, 0, 0, 0)))
            warps.append(np.array([[1, 0, 0], [0, 1, 0]], dtype=np.float64))
            continue
        nw = max(1, int(round(crop.width * scale)))
        nh = max(1, int(round(crop.height * scale)))
        resized = crop.resize((nw, nh), Image.LANCZOS)
        big = Image.new("RGB", (canvas, canvas), (255, 0, 255))
        px = int(round(canvas / 2 - cx_med * scale))
        px = int(np.clip(px, 2, canvas - nw - 2)) if nw < canvas - 4 else 2
        py = int(round(canvas * baseline)) - nh
        big.paste(resized, (px, py), resized)
        # Matte once at 512 (all key-colour pockets removed) and downsample
        # that exact alpha; the 64px and 512px assets cannot disagree.
        sprite_px = resample_from_hi(matte_keyed(big), CHAR_CANVAS, alpha_threshold=0.18)
        sprites.append(sprite_px)

        if mannequin_panels is not None:
            mm = panel_metrics(mannequin_panels[i])
            sa = clip_sa if clip_sa is not None else float(np.clip(m["lower_w"] / max(1.0, mm["lower_w"]), 0.5, 2.0))
            dx0, dy0, dx1, dy1 = m["box"]
            sx0, sy0, sx1, sy1 = mm["box"]
            src_cx = (sx0 + sx1) / 2.0
            src_bottom = sy1
            dst_cx = (dx0 + dx1) / 2.0
            dst_bottom = dy1
            offx = ((sa * (-src_cx) + dst_cx - dx0) * scale + px) / 8.0
            offy = ((sa * (-src_bottom) + dst_bottom - dy0) * scale + py) / 8.0
            warps.append(np.array([[scale * sa, 0.0, offx],
                                   [0.0, scale * sa, offy]], dtype=np.float64))
        else:
            warps.append(np.array([[1, 0, 0], [0, 1, 0]], dtype=np.float64))
    return sprites, warps


def panel_to_sprite(panel: Image.Image) -> Image.Image:
    return panels_to_sprites([panel])[0][0]
def panels_to_hires(panels: list[Image.Image], mannequin_panels: list[Image.Image] | None = None,
                    canvas: int = 512, fill: float = 0.9, baseline: float = 0.985) -> list[Image.Image]:
    """Align the 512-px AI panels into the same 512-px frame as the 64-px sheet.

    ``panels_to_sprites`` first pastes the crop onto a 512 canvas and then
    core-window-pools it to 64.  This function returns that 512 canvas with the
    magenta key removed and the palette locked, so the high-resolution animation
    shares the exact scale, baseline and centre of the 64-px sprite.
    """
    metrics = [panel_metrics(p) for p in panels]
    heights = [m["h"] for m in metrics if m["h"] > 0]
    widths = [m["box"][2] - m["box"][0] for m in metrics if m["h"] > 0]
    h_med = float(np.median(heights)) if heights else 1.0
    w_max = float(max(widths)) if widths else 1.0
    scale = min(canvas * fill / max(1.0, h_med), canvas * fill / max(1.0, w_max))
    cx_med = float(np.median([m["lower_cx"] for m in metrics])) if metrics else 0.0
    out: list[Image.Image] = []
    for crop, m in zip([m["crop"] for m in metrics], metrics):
        if m["h"] == 0:
            out.append(Image.new("RGBA", (canvas, canvas), (0, 0, 0, 0)))
            continue
        nw = max(1, int(round(crop.width * scale)))
        nh = max(1, int(round(crop.height * scale)))
        resized = crop.resize((nw, nh), Image.LANCZOS)
        big = Image.new("RGB", (canvas, canvas), (255, 0, 255))
        px = int(round(canvas / 2 - cx_med * scale))
        px = int(np.clip(px, 2, canvas - nw - 2)) if nw < canvas - 4 else 2
        py = int(round(canvas * baseline)) - nh
        big.paste(resized, (px, py), resized)
        out.append(matte_keyed(big))
    return out




def sheet_from_frames(frames: list[Image.Image], scale: int = 8) -> Image.Image:
    """Compose a horizontal preview sheet with a *transparent* background.

    A magenta preview background used to leak opaque #FF00FF pixels into the
    shipped sheet, violating the "every opaque pixel is in the master palette"
    acceptance rule.  Transparency is the correct sprite-sheet background.
    """
    w = frames[0].width * scale
    h = frames[0].height * scale
    out = Image.new("RGBA", (w * len(frames), h), (0, 0, 0, 0))
    for i, f in enumerate(frames):
        big = upscale_nearest(f, scale)
        out.alpha_composite(big, (i * w, 0))
    # Strict palette rule: transparent pixels must also carry a palette RGB.
    return lock_palette(out)


# ----------------------------------------------------------------------------
# Orchestration
# ----------------------------------------------------------------------------
class CharacterPipeline:
    def __init__(self, client: GeminiImageClient | None = None,
                 outdir: Path | str = "output/character") -> None:
        self.client = client or GeminiImageClient()
        self.outdir = Path(outdir)
        self.outdir.mkdir(parents=True, exist_ok=True)

    def reference(self, spec: CharacterSpec = DEFAULT_SPEC) -> Image.Image:
        return generate_reference(self.client, spec, self.outdir / spec.name)

    def generate_action(
        self,
        spec: CharacterSpec,
        action: str,
        mannequin_dir: Path,
        ref64: Image.Image,
        frames: int = 8,
        batch_size: int = 3,
    ) -> dict:
        man_dir = self.outdir / spec.name / action
        man_dir.mkdir(parents=True, exist_ok=True)
        sheet = Image.open(mannequin_dir / "sheet_shaded.png").convert("RGB")
        src = [sheet.crop((i * 512, 0, (i + 1) * 512, 512)) for i in range(frames)]
        ref_canvas = upscale_nearest(ref64, 8).convert("RGB")

        out_frames: list[Image.Image] = []
        batches = []
        for start in range(0, frames, batch_size):
            idxs = [(start + k) % frames for k in range(batch_size)]
            batches.append(idxs)
        for bi, idxs in enumerate(batches):
            board = build_board(ref_canvas, [src[i] for i in idxs])
            board.save(man_dir / f"board_{bi}.png")
            result = remaster_board(self.client, board, spec, tag=f"{spec.name}-{action}-{bi}")
            result.save(man_dir / f"remaster_{bi}.png")
            for k, i in enumerate(idxs):
                panel = extract_panel(result, k + 1)
                panel.save(man_dir / f"panel_{bi}_{k}.png")
                out_frames.append(panel_to_sprite(panel))
        # keep first N unique frames (batches may wrap around for non-multiples)
        out_frames = out_frames[:frames]
        for i, f in enumerate(out_frames):
            f.save(man_dir / f"frame_{i:02d}.png")
        sheet_from_frames(out_frames).save(man_dir / f"{action}_preview.png")
        meta = {
            "spec": spec.__dict__,
            "action": action,
            "frames": len(out_frames),
            "batches": batches,
            "violations": [palette_violations(f) for f in out_frames],
        }
        (man_dir / "meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False))
        return meta
