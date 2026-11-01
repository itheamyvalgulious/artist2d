"""End-to-end mega-structure build (PLAN modules 3 & 4).

    .venv/bin/python scripts/build_mega.py

Runs stamp_medium (Module 3) and mega_macro (Module 4), writing all outputs
to output/mega/.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from config.pipeline_config import OUTPUT_DIR  # noqa: E402
from config.namespaces import environment_dir, mega_dir  # noqa: E402
from core.api_client import GeminiImageClient  # noqa: E402
from environment.stamp_medium import build_stamp_medium  # noqa: E402
from environment.mega_macro import build_mega_all  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser(description="Build mega-structure assets (modules 3 & 4)")
    ap.add_argument("--skip-stamp", action="store_true", help="Skip Module 3 (stamp_medium)")
    ap.add_argument("--skip-mega", action="store_true", help="Skip Module 4 (mega_macro)")
    ap.add_argument("--seed", type=int, default=42, help="Random seed for decals and assembly")
    ap.add_argument("--blueprint-rows", type=int, default=15, help="Blueprint height")
    ap.add_argument("--blueprint-cols", type=int, default=20, help="Blueprint width")
    args = ap.parse_args()

    api = GeminiImageClient()
    mega_out = mega_dir("field")
    mega_out.mkdir(parents=True, exist_ok=True)

    reports = {}

    # --- Module 3: Stamp (medium mega-structure) ---
    if not args.skip_stamp:
        print("\n" + "=" * 70)
        print("  MODULE 3: Medium Stamp")
        print("=" * 70)
        stamp_report = build_stamp_medium(api, out_dir=environment_dir("field") / "stamp")
        reports["stamp"] = stamp_report
        print(f"  Stamp done: {stamp_report['palette_violations']} palette violations")
    else:
        print("  Skipping Module 3 (stamp_medium)")

    # --- Module 4: Mega (large-scale assembly) ---
    if not args.skip_mega:
        print("\n" + "=" * 70)
        print("  MODULE 4: Mega Macro")
        print("=" * 70)

        # Build blueprint – castle: continuous walls, narrow 3-cell gate
        H, W = args.blueprint_rows, args.blueprint_cols
        castle = [
            "....................",
            "......######........",
            "....##########......",
            "...##############...",
            "..################..",
            ".######....#######..",
            ".######....#######..",
            ".######....#######..",
            ".######....#######..",
            ".######....#######..",
            ".######....#######..",
            ".######....#######..",
            ".######....#######..",
            ".######....#######..",
            "....................",
        ]
        blueprint = np.zeros((H, W), dtype=bool)
        for r, row in enumerate(castle):
            for c, ch in enumerate(row):
                if ch == "#":
                    blueprint[r, c] = True
        # Narrow gate (3 cells wide) at bottom centre, rows 12-13
        gate_c = W // 2 - 1
        for r in (12, 13):
            for c in range(gate_c, gate_c + 3):
                if 0 <= c < W:
                    blueprint[r, c] = False

        mega_report = build_mega_all(api, blueprint=blueprint, out_dir=mega_out, seed=args.seed)
        reports["mega"] = mega_report
        print(f"  Mega done: {mega_report['palette_violations']} palette violations, "
              f"coverage={mega_report.get('coverage', 'N/A')}")
    else:
        print("  Skipping Module 4 (mega_macro)")

    # Keep the Tiled map in sync with the freshly built atlas/layout.
    if not args.skip_mega:
        import subprocess as _sp
        _sp.run([sys.executable, str(ROOT / "scripts" / "export_tiled.py")], check=True, cwd=ROOT)

    # --- Summary ---
    print("\n" + "=" * 70)
    print("  BUILD COMPLETE")
    print("=" * 70)
    for name, r in reports.items():
        v = r.get("palette_violations", "?")
        print(f"  {name}: violations={v}, output={r.get('output_dir', 'N/A')}")
    print(f"\n  All outputs under: {mega_out}")


if __name__ == "__main__":
    main()