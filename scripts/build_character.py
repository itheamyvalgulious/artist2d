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
    stabilize_action,
    verify_action,
)
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
        "jump": {"clip": "Jump_Start"},
        "in_air": {"clip": "Jump_Full_Short", "start": 0.35, "end": 0.68},
    },
    "agent": {
        "idle": {"clip": "Idle"},
        "run": {"clip": "Running_A", "context_action": "idle"},
        "jump": {"clip": "Jump_Start"},
        "in_air": {"clip": "Jump_Idle"},
        "shoot1": {"clip": "1H_Ranged_Shoot", "base_clip": "Idle", "upper_clip": "1H_Ranged_Shoot", "upper_start": 0.08, "upper_end": 0.40},
        "shoot2": {"clip": "1H_Ranged_Shoot", "base_clip": "Running_A", "upper_clip": "1H_Ranged_Shoot", "upper_start": 0.08, "upper_end": 0.40, "context_action": "run", "board_fill": 0.86},
        "shoot3": {"clip": "1H_Ranged_Shoot", "base_clip": "Jump_Idle", "upper_clip": "1H_Ranged_Shoot", "upper_start": 0.08, "upper_end": 0.40},
        "slash1": {"clip": "1H_Melee_Attack_Slice_Diagonal", "start": 0.32, "end": 0.52},
        "slash2": {"clip": "1H_Melee_Attack_Slice_Diagonal", "base_clip": "Running_A", "upper_clip": "1H_Melee_Attack_Slice_Diagonal", "upper_start": 0.32, "upper_end": 0.52, "context_action": "run", "board_fill": 0.86},
        "slash3": {"clip": "1H_Melee_Attack_Slice_Diagonal", "base_clip": "Jump_Idle", "upper_clip": "1H_Melee_Attack_Slice_Diagonal", "upper_start": 0.32, "upper_end": 0.52},
        "block": {"clip": "Blocking"},
        "roll": {"clip": "Dodge_Forward", "start": 0.10, "end": 0.62, "context_action": "idle", "board_fill": 0.82},
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


def build_hires_action(out_dir: Path, frames: int = 8, action: str = "",
                       fill: float = 0.82) -> dict:
    """Build the 512-px-per-frame companion animation from the AI panels."""
    panels = [Image.open(out_dir / f"panel_{i:02d}.png").convert("RGB") for i in range(frames)]
    hi = panels_to_hires(panels, fill=fill)
    if action in ("slash2", "shoot2", "roll"):
        hi = [keep_main_component(f) for f in hi]
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
                     cfg: dict, frames: int = 8) -> None:
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
        "--gear", json.dumps((spec.gear or {}).get(action, {})),
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
                 ref64, frames: int, force: bool, cfg: dict) -> dict:
    name = spec.name
    man_dir = OUTPUT_DIR / "character" / name / "mannequin" / action
    out_dir = character_dir(name) / action
    sheet_file = out_dir / "sheet.png"
    if sheet_file.exists() and not force:
        return json.loads((out_dir / "report.json").read_text())

    render_mannequin(action, man_dir, spec, cfg, frames)
    export_motion_npy(man_dir)
    sheet = Image.open(man_dir / "sheet_shaded.png").convert("RGB")
    src = [sheet.crop((i * 512, 0, (i + 1) * 512, 512)) for i in range(frames)]
    # The board must use the FULL-RESOLUTION fitted reference, not the 64px
    # pixelated master (re-pixelating loses face/weapon detail).
    candidates = [character_dir(name) / "char_ref_canvas.png",
                  ROOT / "work" / "character" / name / "char_ref_canvas.png"]
    full_ref = next((p for p in candidates if p.exists()), None)
    if full_ref is not None:
        ref_canvas = Image.open(full_ref).convert("RGB").resize((512, 512), Image.LANCZOS)
    else:
        ref_canvas = ref_canvas_from64(ref64)
    out_dir.mkdir(parents=True, exist_ok=True)

    board = build_board(ref_canvas, src, fill=cfg.get("board_fill", 0.9),
                        safety_frame=False)
    board.save(out_dir / "board.png")
    mask = make_board_mask(board.size)
    mask.save(out_dir / "mask.png")
    extra_imgs: list[Image.Image] = []
    prompt_extra = KNIGHT_ACTION_EXTRA.get(action, "") if name == "knight" else ""
    context = None
    context_action = cfg.get("context_action")
    if context_action:
        context = build_context_frame(name, context_action, action)
        if context is not None:
            extra_imgs.append(context)
            prompt_extra += (
                f" Image 3 is ONE approved frame of the previous {context_action} action. Use it only "
                f"as a consistency reference for the body proportions, outfit, hair and weapon "
                f"placement; do not copy it into the sheet as an extra panel."
            )
    prompt = (
        board_prompt(spec, action)
        + prompt_extra
        + " Image 2 is a mask: pure black means keep that panel exactly as in Image 1, "
          "pure white means repaint that panel."
    )
    result = pipe.client.edit(
        prompt, [board, mask.convert("RGB")] + extra_imgs,
        role=cfg.get("role", "sunburst"), aspect="1:1", size="2K",
        tag=f"{name}-{action}-board-v6",
    )
    result = lock_reference_panel(result, board)
    result.save(out_dir / "remaster.png")
    panels = [extract_panel(result, i + 1) for i in range(frames)]
    for i, p in enumerate(panels):
        p.save(out_dir / f"panel_{i:02d}.png")
    margin_ok = True
    margin_attempts = 1
    sprites, warps = panels_to_sprites(panels, mannequin_panels=src,
                                       fill=cfg.get("sprite_fill", 0.9))
    for i, f in enumerate(sprites):
        f.save(out_dir / f"raw_{i:02d}.png")

    report = stabilize_action(man_dir, [out_dir / f"raw_{i:02d}.png" for i in range(frames)],
                              out_dir / "frames", action, warps=warps)
    final = [Image.open(out_dir / "frames" / f"frame_{i:02d}.png") for f in range(frames)]
    final = [remove_small_components(f) for f in final]
    if name == "knight" and action == "idle":
        final = [split_merged_boots(f) for f in final]
    for i, f in enumerate(final):
        f.save(out_dir / "frames" / f"frame_{i:02d}.png")
    sheet_from_frames(final, scale=8).save(out_dir / "sheet.png")
    sheet_from_frames(final, scale=1).save(out_dir / "sheet_1x.png")
    np.save(out_dir / "warps.npy", np.array(warps))
    report["verification"] = verify_action(
        man_dir, [out_dir / f"raw_{i:02d}.png" for i in range(frames)],
        [out_dir / "frames" / f"frame_{i:02d}.png" for i in range(frames)], warps, action,
        static_only=report.get("static_features", False))
    hires = build_hires_action(out_dir, frames, action,
                               fill=cfg.get("sprite_fill", 0.82))
    report.update({"sheets": "sheet.png", "mannequin": str(man_dir), "source": cfg,
                   "hires": hires, "margin_ok": margin_ok,
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
            dst_img = src_img.copy()
            dst_img.save(dst)
            anchors[which] = {"anchor": anchor, "ok": True, "sha256": _sha(dst)}
            hi_src = base / dep / "frames_hi" / f"frame_{int(idx):02d}.png"
            hi_dst_dir = out_dir / "frames_hi"
            if hi_src.exists() and hi_dst_dir.exists():
                hi_dst = hi_dst_dir / dst.name
                Image.open(hi_src).convert("RGBA").save(hi_dst)
                anchors[which]["hires_sha256"] = _sha(hi_dst)
            changed = True
        if changed:
            final = [Image.open(frame_dir / f"frame_{i:02d}.png").convert("RGBA")
                     for i in range(frames)]
            sheet_from_frames(final, scale=8).save(out_dir / "sheet.png")
            sheet_from_frames(final, scale=1).save(out_dir / "sheet_1x.png")
            hi_dir = out_dir / "frames_hi"
            if hi_dir.exists():
                hi_frames = [Image.open(hi_dir / f"frame_{i:02d}.png").convert("RGBA")
                             for i in range(frames)]
                hi_sheet = Image.new("RGBA", (512 * frames, 512), (0, 0, 0, 0))
                for i, f in enumerate(hi_frames):
                    hi_sheet.alpha_composite(f, (i * 512, 0))
                from core.palette_quantizer import lock_palette as _lock
                _lock(hi_sheet).save(out_dir / "sheet_hi.png")
                _save_apng(hi_frames, out_dir / "preview_hi.png")
                _save_gif(hi_frames, out_dir / "preview_hi.gif")
            report = json.loads((out_dir / "report.json").read_text())
            report["transitions"] = anchors
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
    if args.character == "agent":
        weapon_ref = generate_weapon_reference(pipe.client, spec, character_dir(spec.name),
                                               force=False)
        print("weapon reference ready", weapon_ref.size)

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
        reports[action] = build_action(pipe, spec, action, ref64, args.frames, args.force, cfg)
        print(action, {k: reports[action].get(k) for k in
                       ("frames", "static_features", "features_repaired", "locked_pixels")})
        print("  hires:", reports[action].get("hires", {}).get("size"))
    transitions = enforce_transitions(args.character, order, args.frames)
    (character_dir(args.character) / "build_report.json").write_text(
        json.dumps({"character": args.character, "actions": reports,
                    "transitions": transitions}, indent=2))


if __name__ == "__main__":
    main()
