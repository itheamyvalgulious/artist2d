"""Run every module end-to-end, then print the deterministic asset report.

    .venv/bin/python scripts/run_all.py             # original field + knight
    .venv/bin/python scripts/run_all.py --ship      # side-view ship set
    .venv/bin/python scripts/run_all.py --ship --force

There is deliberately no pytest suite.  Visual acceptance is performed by an
independent multimodal reviewer with 100% asset coverage; see README §5.

``--skip-api`` is kept for the field pipeline: it reuses the on-disk API cache
and only re-runs deterministic post-processing.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PY = sys.executable


def run(script: str, *args: str) -> None:
    cmd = [PY, str(ROOT / "scripts" / script), *args]
    print("\n==>", " ".join(cmd))
    subprocess.run(cmd, check=True, cwd=ROOT)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--character", default="knight")
    ap.add_argument("--skip-mega", action="store_true")
    ap.add_argument("--ship", action="store_true",
                    help="build the side-view ship set instead of the field set")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    if args.ship:
        run("build_ship.py", *(["--force"] if args.force else []))
    else:
        run("build_character.py", "--character", args.character, "--force")
        run("build_environment.py")
        if not args.skip_mega:
            run("build_mega.py")
            run("export_tiled.py")
        run("build_showcase.py")
        run("build_animations.py")
    run("cleanup_work.py")
    run("verify_all.py")
    print("\nVisual acceptance is a separate independent-subagent review; see README §5.")


if __name__ == "__main__":
    main()
