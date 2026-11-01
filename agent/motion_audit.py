"""Deterministic motion audit for the character pipeline.

The agent must not judge a 3D action from a single 2D still.  This module asks
Godot for the real 3D trajectory of the sword tip, both hands, the shield and
the hips, then:

* classifies every candidate clip as forward-chop / lateral-slash / thrust /
  static from the measured tip ranges;
* checks that the camera is on the sword side (the sword hand is nearer to the
  camera than the shield centre in most frames);
* picks the best attack clip by score instead of a hard-coded guess;
* renders a four-view contact sheet at the impact frame so the visual reviewer
  can confirm the facing and swing direction.

Run:
    .venv/bin/python -m agent.motion_audit [--out work/character/knight]
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
GODOT = os.environ.get("GODOT_BIN", "godot")
DISPLAY = os.environ.get("GODOT_DISPLAY", ":0")
PROJECT = ROOT / "character" / "godot_mannequin"
RENDER_SCRIPT = "res://scripts/render_actor.gd"

# Candidate clips that could serve as a right-hand attack.  The audit decides,
# the shortlist is intentionally broad (1H/2H, chop/slice/stab).
CANDIDATES = [
    "1H_Melee_Attack_Chop",
    "1H_Melee_Attack_Slice_Diagonal",
    "1H_Melee_Attack_Slice_Horizontal",
    "1H_Melee_Attack_Stab",
    "2H_Melee_Attack_Chop",
]

VIEW_ANGLES = [("front (+Z)", 0), ("right side (-X)", 90),
               ("back (-Z)", 180), ("left side (+X)", 270)]


def read_camera() -> tuple[float, float, float]:
    """Read the one source of truth for the camera (the Godot script)."""
    text = (PROJECT / "scripts" / "render_actor.gd").read_text()
    m = re.search(r"var requested_cam := Vector3\(([-\d.]+),\s*([-\d.]+),\s*([-\d.]+)\)", text)
    if not m:
        raise RuntimeError("cannot find requested_cam in render_actor.gd")
    return tuple(float(v) for v in m.groups())


def run_trace(clip: str, frames: int, outdir: Path,
              camera: tuple[float, float, float]) -> dict:
    outdir.mkdir(parents=True, exist_ok=True)
    cmd = [
        GODOT, "--path", str(PROJECT), "--rendering-driver", "opengl3",
        "--script", RENDER_SCRIPT, "--",
        "--action", "attack", "--clip", clip, "--source", "kaykit",
        "--frames", str(frames), "--trace", "1", "--out", str(outdir),
        "--cam", ",".join(f"{v:g}" for v in camera),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=240,
                          env=dict(os.environ, DISPLAY=DISPLAY))
    if "MOTION_TRACE" not in proc.stdout:
        raise RuntimeError(f"trace failed for {clip}:\n{proc.stdout[-1200:]}\n{proc.stderr[-1200:]}")
    return json.loads((outdir / "motion_trace.json").read_text())


def run_views(clip: str, frame: int, outdir: Path,
              camera: tuple[float, float, float]) -> list[Path]:
    outdir.mkdir(parents=True, exist_ok=True)
    cmd = [
        GODOT, "--path", str(PROJECT), "--rendering-driver", "opengl3",
        "--script", RENDER_SCRIPT, "--",
        "--action", "attack", "--clip", clip, "--source", "kaykit",
        "--frames", "8", "--views", "1", "--view_frame", str(frame),
        "--out", str(outdir), "--cam", ",".join(f"{v:g}" for v in camera),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=240,
                          env=dict(os.environ, DISPLAY=DISPLAY))
    if "VIEWS_DONE" not in proc.stdout:
        raise RuntimeError(f"views failed:\n{proc.stdout[-1200:]}\n{proc.stderr[-1200:]}")
    return [outdir / f"view_{a:03d}.png" for _, a in VIEW_ANGLES]


def analyze(trace: dict) -> dict:
    s = trace["samples_data"]
    tip = np.array([x["tip"] for x in s], dtype=float)
    hand_r = np.array([x["hand_r"] for x in s], dtype=float)
    shield = np.array([x["shield"] for x in s], dtype=float)
    hips = np.array([x["hips"] for x in s], dtype=float)
    rng = tip.max(0) - tip.min(0)
    impact = int(tip[:, 1].argmin())
    cam = np.array(trace["camera"], dtype=float)
    target = np.array([0.0, hips[:, 1].mean(), 0.0])
    # Direction from the character to the camera: larger dot = nearer camera.
    cam_dir = (cam - target)
    cam_dir = cam_dir / max(float(np.linalg.norm(cam_dir)), 1e-6)
    sword_depth = hand_r @ cam_dir
    shield_depth = shield @ cam_dir
    sword_near = sword_depth > shield_depth
    tip_ends = tip[[0, impact, -1]]

    x, y, z = rng
    if max(x, y, z) < 3.0:
        kind = "static"
    elif z > 1.3 * x and y > 0.6 * z:
        kind = "forward_chop"
    elif x > 1.2 * z:
        kind = "lateral_slash"
    elif z > 1.3 * x and y < 0.5 * z:
        kind = "thrust"
    else:
        kind = "mixed"

    # Forward+vertical motion is a chop; lateral motion is penalised; the
    # sword must be on the camera side, otherwise the shield reads as the
    # attacking prop.
    score = z + 0.8 * y - 1.5 * x + 6.0 * float(sword_near.mean())
    return {
        "clip": trace["clip"],
        "kind": kind,
        "range": {"x": round(float(x), 2), "y": round(float(y), 2), "z": round(float(z), 2)},
        "impact_frame": impact,
        "impact_delta": {
            "dx": round(float(tip[impact, 0] - tip[0, 0]), 2),
            "dy": round(float(tip[impact, 1] - tip[0, 1]), 2),
            "dz": round(float(tip[impact, 2] - tip[0, 2]), 2),
        },
        "sword_near_fraction": round(float(sword_near.mean()), 3),
        "score": round(float(score), 2),
        "tip_start": [round(float(v), 2) for v in tip_ends[0]],
        "tip_impact": [round(float(v), 2) for v in tip_ends[1]],
        "tip_end": [round(float(v), 2) for v in tip_ends[2]],
    }


def compose_views(paths: list[Path], out: Path, title: str) -> None:
    cell = 320
    sheet = Image.new("RGB", (cell * len(paths), cell + 30), (20, 20, 24))
    draw = ImageDraw.Draw(sheet)
    draw.text((8, 8), title, fill=(255, 255, 255))
    for i, (path, (label, _)) in enumerate(zip(paths, VIEW_ANGLES)):
        im = Image.open(path).convert("RGB").resize((cell, cell), Image.LANCZOS)
        sheet.paste(im, (i * cell, 30))
        draw.text((i * cell + 8, 12), label, fill=(255, 255, 255))
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out)


def audit(outdir: Path, frames: int = 32) -> dict:
    camera = read_camera()
    results = []
    for clip in CANDIDATES:
        trace = run_trace(clip, frames, outdir / "traces" / clip, camera)
        results.append(analyze(trace))
    ranked = sorted(results, key=lambda r: r["score"], reverse=True)
    chops = [r for r in ranked if r["kind"] == "forward_chop"]
    chosen = (chops[0] if chops else ranked[0])
    if chosen["kind"] != "forward_chop":
        raise RuntimeError(f"no forward-chop candidate; ranked={ranked}")

    # The impact view is the frame where the tip is lowest; render a wide
    # four-view contact sheet at that moment for the visual reviewer.
    frame = chosen["impact_frame"]
    view_paths = run_views(chosen["clip"], frame, outdir / "orientation", camera)
    sheet = outdir / "attack_orientation.png"
    compose_views(view_paths, sheet, f"{chosen['clip']} @ impact frame {frame}")

    report = {
        "camera": list(camera),
        "candidates": results,
        "ranked": [r["clip"] for r in ranked],
        "chosen_clip": chosen["clip"],
        "chosen_kind": chosen["kind"],
        "chosen_impact_frame": frame,
        "orientation_sheet": str(sheet.relative_to(ROOT)),
        "sword_near_ok": chosen["sword_near_fraction"] >= 0.75,
        "requirements": {
            "forward_component": chosen["range"]["z"] > 1.3 * chosen["range"]["x"],
            "vertical_component": chosen["range"]["y"] > 0.6 * chosen["range"]["z"],
            "sword_near_camera": chosen["sword_near_fraction"] >= 0.75,
        },
    }
    (outdir / "motion_audit.json").write_text(json.dumps(report, indent=2))
    print(json.dumps({k: report[k] for k in
                      ("camera", "chosen_clip", "chosen_kind",
                       "chosen_impact_frame", "sword_near_ok", "requirements")},
                     indent=2))
    for r in ranked:
        print(f"  {r['clip']:34s} {r['kind']:13s} "
              f"x={r['range']['x']:5.1f} y={r['range']['y']:5.1f} z={r['range']['z']:5.1f} "
              f"near={r['sword_near_fraction']:.2f} score={r['score']:.1f}")
    return report


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "work" / "character" / "knight"))
    ap.add_argument("--frames", type=int, default=32)
    args = ap.parse_args()
    audit(Path(args.out), args.frames)


if __name__ == "__main__":
    main()
