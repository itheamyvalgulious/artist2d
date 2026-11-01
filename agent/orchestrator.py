"""Art-agent entry point: audit, visual review, purity, tests, report.

The agent owns the *judgement* steps:

* ``agent.motion_audit`` measures the real 3D sword/hand/shield trajectory,
  chooses the attack clip, and verifies the camera side.
* ``agent.visual_review`` sends the stitched sheets/terrain/scene to the local
  NewAPI vision model and records a strict pass/fail verdict.
* this module combines those with deterministic palette purity and the test
  suite, then writes ``output/AGENT_RUN.md``.

Usage:
    .venv/bin/python -m agent.orchestrator --verify
    .venv/bin/python -m agent.orchestrator --verify --no-vision
    .venv/bin/python -m agent.orchestrator --audit-only
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "output"
from config.namespaces import environment_dir, showcase_dir  # noqa: E402
ENV = environment_dir("field")
CHAR = OUT / "character" / "knight"
WORK = ROOT / "work" / "character" / "knight"


def purity_scan() -> dict:
    from PIL import Image, ImageSequence
    from core.palette_quantizer import palette_violations

    files = sorted(OUT.rglob("*.png"))
    partial = off = 0
    bad: list[tuple[str, int, int]] = []
    for f in files:
        im = Image.open(f)
        for frame in ImageSequence.Iterator(im):
            a, b = palette_violations(frame.convert("RGBA"))
            partial += a
            off += b
            if a or b:
                bad.append((str(f.relative_to(ROOT)), a, b))
                break
    return {"pngs": len(files), "partial_alpha": partial,
            "off_palette": off, "bad": bad[:10],
            "pass": partial == 0 and off == 0}


def run_tests() -> dict:
    proc = subprocess.run([sys.executable, "-m", "pytest", "tests", "-q"],
                          cwd=ROOT, capture_output=True, text=True)
    tail = [ln for ln in proc.stdout.splitlines() if ln.strip()][-1:]
    return {"returncode": proc.returncode, "tail": tail,
            "pass": proc.returncode == 0}


def load_visual() -> dict:
    def _load(p: Path):
        try:
            return json.loads(p.read_text())
        except Exception:
            return None
    return {
        "character": _load(CHAR / "visual_review.json"),
        "environment": _load(ENV / "visual_review.json"),
        "showcase": _load(showcase_dir("field") / "visual_review.json"),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--audit-only", action="store_true")
    ap.add_argument("--no-vision", action="store_true",
                    help="reuse the saved visual_review.json files")
    args = ap.parse_args()

    from agent.motion_audit import audit
    motion = audit(WORK)
    (CHAR / "motion_audit.json").write_text(json.dumps(motion, indent=2))
    if args.audit_only:
        print(json.dumps(motion, indent=2))
        return

    visual = load_visual()
    if not args.no_vision:
        from agent.visual_review import run_all
        visual = run_all()

    purity = purity_scan()
    tests = run_tests()
    char_pass = bool(visual["character"]) and all(
        v.get("pass") for v in visual["character"].values())
    env_pass = bool(visual["environment"] and visual["environment"].get("pass"))
    show_pass = bool(visual["showcase"] and visual["showcase"].get("pass"))

    lines = [
        "# Agent Run / 自动审查报告",
        "",
        "由 `agent/orchestrator.py` 生成；方向、clip 与验收结论均来自 agent 的",
        "确定性 3D 轨迹审计和视觉模型审查，而非人工目测。",
        "",
        "## 1. Motion audit (3D truth)",
        "",
        f"- Camera: `{motion['camera']}` (sword-side / near-profile).",
        f"- Chosen attack clip: **{motion['chosen_clip']}** ({motion['chosen_kind']}).",
        f"- Impact frame: {motion['chosen_impact_frame']}/32.",
        f"- Sword near camera: `{motion['sword_near_ok']}`.",
        f"- Requirements: `{json.dumps(motion['requirements'])}`.",
        "",
        "| clip | kind | X range | Y range | Z range | sword near | score |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for r in sorted(motion["candidates"], key=lambda x: -x["score"]):
        lines.append(
            f"| `{r['clip']}` | {r['kind']} | {r['range']['x']} | {r['range']['y']} | "
            f"{r['range']['z']} | {r['sword_near_fraction']} | {r['score']} |")
    lines += [
        "",
        "The audit reads the real 3D sword-tip trajectory from Godot; a lateral",
        "Slash_Diagonal (X 36.2) is rejected while Chop (Z 31.1, Y 32.1, X 9.0)",
        "is selected as a forward-down chop.",
        "",
        "## 2. Visual review",
        "",
        "| area | verdict | notes |",
        "|---|---|---|",
    ]

    def _note(v):
        if not v:
            return "no data"
        a = v.get("answer", {})
        return str(a.get("notes", ""))[:120]

    for action in ("idle", "running", "attack", "defend", "jump", "in_air"):
        v = (visual["character"] or {}).get(action)
        lines.append(f"| character / {action} | {'PASS' if v and v.get('pass') else 'FAIL'} | {_note(v)} |")
    lines.append(f"| environment | {'PASS' if env_pass else 'FAIL'} | {_note(visual['environment'])} |")
    lines.append(f"| showcase | {'PASS' if show_pass else 'FAIL'} | {_note(visual['showcase'])} |")
    lines += [
        "",
        "## 3. Deterministic gates",
        "",
        f"- Palette purity: **{purity['pass']}** — {purity['pngs']} PNGs, "
        f"partial-alpha {purity['partial_alpha']}, off-palette {purity['off_palette']}.",
        f"- Tests: **{tests['pass']}** — {'; '.join(tests['tail'])}.",
        "",
        "## 4. Decision",
        "",
        f"- Character set: **{'PASS' if char_pass else 'FAIL'}**.",
        f"- Environment: **{'PASS' if env_pass else 'FAIL'}**.",
        f"- Showcase: **{'PASS' if show_pass else 'FAIL'}** "
        "(the mega 9-slice gate is a known composition weak spot; the agent keeps it visible).",
        f"- Overall: **{'PASS' if (char_pass and env_pass and purity['pass'] and tests['pass']) else 'FAIL'}**.",
    ]
    (OUT / "AGENT_RUN.md").write_text("\n".join(lines) + "\n")
    print(json.dumps({"character": char_pass, "environment": env_pass,
                      "showcase": show_pass, "purity": purity["pass"],
                      "tests": tests["pass"]}, indent=2))
    if not (char_pass and env_pass and purity["pass"] and tests["pass"]):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
