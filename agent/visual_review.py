"""Vision reviewer used by the art agent.

The pipeline is not allowed to call an output "done" just because a script
returned zero.  This module sends the actual stitched artefacts to a vision
model served by the local NewAPI and asks for a strict JSON verdict.  The
orchestrator combines this with the deterministic checks (palette purity, 3D
motion audit, tests); the model is the visual gate, not the only gate.

Run:
    .venv/bin/python -m agent.visual_review --all
"""
from __future__ import annotations

import argparse
import base64
import io
import json
import os
import urllib.request
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "output"
from config.namespaces import environment_dir, showcase_dir  # noqa: E402
ENV = environment_dir("field")
API = os.environ.get("NEWAPI_BASE", "http://127.0.0.1:3000").rstrip("/")
# Credentials come from the environment only; see config/pipeline_config.py.
KEY = os.environ.get("NEWAPI_KEY", "").strip()
MODEL = os.environ.get("VISION_MODEL", "gemini-3.8-flash")
MAX_SIDE = 1792


def _encode(path: Path) -> str:
    im = Image.open(path)
    if im.mode in ("RGBA", "LA", "P"):
        im = im.convert("RGBA")
        bg = Image.new("RGBA", im.size, (16, 16, 20, 255))
        bg.alpha_composite(im)
        im = bg
    im = im.convert("RGB")
    w, h = im.size
    scale = min(1.0, MAX_SIDE / max(w, h))
    if scale < 1.0:
        im = im.resize((max(1, int(w * scale)), max(1, int(h * scale))), Image.LANCZOS)
    elif max(w, h) < 384:
        im = im.resize((w * 4, h * 4), Image.NEAREST)
    buf = io.BytesIO()
    im.save(buf, "PNG")
    return base64.b64encode(buf.getvalue()).decode()


def _parse_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```", 2)[1]
        if text.startswith("json"):
            text = text[4:]
    start = text.find("{")
    if start < 0:
        raise ValueError(f"no JSON object in vision answer:\n{text[:800]}")
    obj, _ = json.JSONDecoder().raw_decode(text[start:])
    return obj


def ask(prompt: str, images: list[Path], max_tokens: int = 3000) -> dict:
    if not KEY:
        raise RuntimeError(
            "NEWAPI_KEY is not set: export NEWAPI_KEY=... before running the vision reviewer"
        )
    content: list[dict] = [{"type": "text", "text": prompt}]
    for p in images:
        content.append({"type": "image_url",
                        "image_url": {"url": "data:image/png;base64," + _encode(p)}})
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": content}],
        "max_tokens": max_tokens,
        "temperature": 0.0,
    }
    req = urllib.request.Request(
        API + "/v1/chat/completions",
        data=json.dumps(payload).encode(),
        headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=240) as resp:
        data = json.load(resp)
    raw = data["choices"][0]["message"]["content"]
    return {"answer": _parse_json(raw), "raw": raw, "model": MODEL,
            "usage": data.get("usage", {})}


CHAR_SCHEMA = (
    '{"view":"right_profile|three_quarter|front|left_profile|unclear",'
    '"sword_hand":"near|far|unclear","shield_side":"far|near|unclear",'
    '"action":"forward_chop|shield_block|lateral_slash|thrust|idle|running|jump|airborne|unclear",'
    '"pink_or_magenta_block":true/false,"detached_feet":true/false,'
    '"pass":true/false,"notes":"max 14 words"}'
)


def review_character(action: str, sheet: Path, orientation: Path | None = None) -> dict:
    expected = {
        "idle": "standing idle; sword arm near, shield far",
        "running": "running to the right; sword arm near, shield far",
        "attack": "a forward downward sword chop with the right hand; NOT a shield bash",
        "defend": "a shield block: the shield is raised in front, sword held back",
        "jump": "the take-off / crouch part of a jump",
        "in_air": "airborne, both feet off the ground",
    }[action]
    prompt = (
        f"This is an 8-frame pixel-art sprite sheet (left to right) for action '{action}'. "
        "Intended camera: near-profile from the knight's RIGHT (sword) side, so the sword arm is "
        "nearest the viewer and the left-arm shield is on the far side. "
        f"Intended semantics: {expected}. "
        "Check for a flat pink/magenta rectangular block (a background-removal failure) and for "
        "detached feet/shadow blobs. Answer JSON only, no markdown: " + CHAR_SCHEMA
    )
    images = [sheet] + ([orientation] if orientation and orientation.exists() else [])
    result = ask(prompt, images)
    a = result["answer"]
    expected_action = {"attack": "forward_chop", "defend": "shield_block",
                       "in_air": "airborne"}.get(action, action)
    a["expected_action"] = expected_action
    a["action_ok"] = a.get("action") == expected_action
    # The shield is deliberately raised in front for a block; for every other
    # action it must be on the far side so it cannot read as the attacking prop.
    a["camera_ok"] = (a.get("sword_hand") == "near"
                      and (action == "defend" or a.get("shield_side") == "far"))
    a["artifact_ok"] = not a.get("pink_or_magenta_block") and not a.get("detached_feet")
    result["pass"] = bool(a.get("pass") and a["action_ok"] and a["camera_ok"] and a["artifact_ok"])
    return result


def review_terrain(preview: Path, water: Path, grass: Path, dirt: Path) -> dict:
    prompt = (
        "This is a stitched 32x32 pixel-art terrain map using 47-tile transitions: grass, a dirt "
        "road/clearing, a stone plaza and a water pond with a dirt bank. Additional images are the "
        "individual 3x3 tile checks for water, grass and dirt. Judge only what is visible. "
        "Answer JSON only, no markdown: "
        '{"visible_tile_seams":true/false,"water_directional_waves":true/false,'
        '"circular_ripples":true/false,"extra_dirt_triangles_at_grass_corners":true/false,'
        '"multiterrain_edges_ok":true/false,'
        '"interiors_natural":{"grass":true/false,"dirt":true/false,"stone":true/false,"water":true/false},'
        '"pass":true/false,"notes":"max 20 words"}'
    )
    result = ask(prompt, [preview, water, grass, dirt])
    a = result["answer"]
    interiors = a.get("interiors_natural") or {}
    result["pass"] = bool(
        a.get("pass")
        and not a.get("visible_tile_seams")
        and a.get("water_directional_waves")
        and not a.get("circular_ripples")
        and not a.get("extra_dirt_triangles_at_grass_corners")
        and a.get("multiterrain_edges_ok")
        and all(interiors.get(k) for k in ("grass", "dirt", "stone", "water"))
    )
    return result


def review_showcase(scene: Path) -> dict:
    prompt = (
        "This is a composed 2D pixel-art game scene: terrain, a knight sprite, a medium building "
        "stamp and a large modular megastructure. Check that the 32px pixel scale is consistent, "
        "the sprite is not floating, the buildings sit on the ground, and there are no obvious "
        "magenta/pink areas or broken tiles. Answer JSON only, no markdown: "
        '{"consistent_pixel_scale":true/false,"sprite_grounded":true/false,'
        '"buildings_grounded":true/false,"pink_or_broken_tiles":true/false,'
        '"pass":true/false,"notes":"max 20 words"}'
    )
    result = ask(prompt, [scene])
    a = result["answer"]
    result["pass"] = bool(
        a.get("pass") and a.get("consistent_pixel_scale") and a.get("sprite_grounded")
        and a.get("buildings_grounded") and not a.get("pink_or_broken_tiles")
    )
    return result


def run_all() -> dict:
    char_dir = OUT / "character" / "knight"
    report: dict = {"model": MODEL, "character": {}, "environment": None, "showcase": None}
    for action in ("idle", "running", "attack", "defend", "jump", "in_air"):
        sheet = char_dir / action / "sheet.png"
        if not sheet.exists():
            report["character"][action] = {"pass": False, "error": "missing sheet"}
            continue
        orientation = (ROOT / "work" / "character" / "knight" / "attack_orientation.png"
                       if action == "attack" else None)
        report["character"][action] = review_character(action, sheet, orientation)
    terrain = ENV / "terrain_preview_x2.png"
    if terrain.exists():
        report["environment"] = review_terrain(
            terrain, ENV / "water_checkerboard.png",
            ENV / "grass_checkerboard.png", ENV / "dirt_checkerboard.png")
    scene = showcase_dir("field") / "scene.png"
    if scene.exists():
        report["showcase"] = review_showcase(scene)
    (char_dir / "visual_review.json").write_text(json.dumps(report["character"], indent=2))
    if report["environment"]:
        (ENV / "visual_review.json").write_text(json.dumps(report["environment"], indent=2))
    if report["showcase"]:
        (showcase_dir("field") / "visual_review.json").write_text(json.dumps(report["showcase"], indent=2))
    return report


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true")
    args = ap.parse_args()
    report = run_all()
    ok = all(v.get("pass") for v in report["character"].values())
    ok = ok and (report["environment"] or {}).get("pass", True)
    ok = ok and (report["showcase"] or {}).get("pass", True)
    print(json.dumps({
        "character": {k: {"pass": v.get("pass"),
                          "action": v.get("answer", {}).get("action"),
                          "view": v.get("answer", {}).get("view"),
                          "notes": v.get("answer", {}).get("notes")}
                      for k, v in report["character"].items()},
        "environment": {"pass": (report["environment"] or {}).get("pass"),
                        "notes": (report["environment"] or {}).get("answer", {}).get("notes")},
        "showcase": {"pass": (report["showcase"] or {}).get("pass")},
        "all_pass": ok,
    }, indent=2, ensure_ascii=False))
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
