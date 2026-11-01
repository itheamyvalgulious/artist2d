"""Move non-palette process/truth files out of ``output/`` into ``work/``.

``output/`` is reserved for palette-pure shipped art; API raws, masks, 3D truth
channels and assembly intermediates live under ``work/`` mirroring the asset-set
namespace (``work/character/<name>``, ``work/environment/<set>``, ...).
"""
from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "output"
WORK = ROOT / "work"

CHAR_PROCESS_NAMES = [
    "board.png", "remaster.png", "mask.png", "warps.npy",
    "char_ref_raw.png", "char_ref_canvas.png",
]
ENV_PROCESS_NAMES = [
    "water_anim_sheet_raw.png", "material_constraint.png", "material_raw.png",
    "stamp/api_result.png", "stamp/canvas_base.png", "stamp/mask.png",
    "stamp/ground_tiled_ref.png", "stamp/stamp_raw.png",
]
MEGA_PROCESS_DIRS = ["mega"]


def move_file(src: Path, dst: Path) -> None:
    if not src.exists():
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        dst.unlink()
    shutil.move(str(src), str(dst))


def move_tree(src: Path, dst: Path) -> None:
    if not src.exists():
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists() and src.is_dir() and dst.is_dir():
        for child in list(src.iterdir()):
            target = dst / child.name
            if target.exists():
                if target.is_dir():
                    shutil.rmtree(target)
                else:
                    target.unlink()
            shutil.move(str(child), str(target))
        try:
            src.rmdir()
        except OSError:
            pass
        return
    if dst.exists():
        shutil.rmtree(dst) if dst.is_dir() else dst.unlink()
    shutil.move(str(src), str(dst))


def main() -> None:
    WORK.mkdir(exist_ok=True)

    # Characters: mannequin truth + per-action API process files.
    char_root = OUT / "character"
    if char_root.exists():
        for char_dir in sorted(p for p in char_root.iterdir() if p.is_dir()):
            name = char_dir.name
            work_char = WORK / "character" / name
            move_tree(char_dir / "mannequin", work_char / "mannequin")
            for rel in ("char_ref_raw.png", "char_ref_canvas.png", "weapon_ref_raw.png", "weapon_ref_canvas.png"):
                move_file(char_dir / rel, work_char / rel)
            for action_dir in sorted(p for p in char_dir.iterdir() if p.is_dir()):
                if action_dir.name in ("mannequin", "frames"):
                    continue
                if not (action_dir / "report.json").exists():
                    continue
                wd = work_char / action_dir.name
                for pat in ("board.png", "remaster.png", "mask.png", "raw_*.png",
                            "panel_*.png"):
                    for f in action_dir.glob(pat):
                        move_file(f, wd / f.name)
                wf = action_dir / "warps.npy"
                if wf.exists():
                    wd.mkdir(parents=True, exist_ok=True)
                    move_file(wf, wd / wf.name)

    # Environment sets: process files and mega intermediates.
    env_root = OUT / "environment"
    if env_root.exists():
        for set_dir in sorted(p for p in env_root.iterdir() if p.is_dir()):
            set_name = set_dir.name
            work_env = WORK / "environment" / set_name
            for rel in ENV_PROCESS_NAMES:
                src = set_dir / rel
                if src.is_file():
                    move_file(src, work_env / rel)
            for rel in MEGA_PROCESS_DIRS:
                move_tree(set_dir / rel, work_env / rel)
            # Anything else explicitly marked as a process file.
            for f in list(set_dir.glob("*_raw.png")):
                move_file(f, work_env / f.name)
            for rel in ("material_board.png", "material_constraint.png"):
                move_file(set_dir / rel, work_env / rel)
            for f in list((set_dir / "tiles").glob("*_raw.png")):
                move_file(f, work_env / "tiles" / f.name)
            for f in list(set_dir.glob("props/*/ai_raw.png")):
                move_file(f, work_env / "props" / f.parent.name / f.name)
    # Mega-set process files (element AI raws).
    mega_root = OUT / "mega"
    if mega_root.exists():
        for set_dir in sorted(p for p in mega_root.iterdir() if p.is_dir()):
            work_set = WORK / "mega" / set_dir.name
            for f in list(set_dir.glob("elements/*/ai_raw.png")):
                move_file(f, work_set / "elements" / f.parent.name / f.name)

    print("work/ populated; output/ now contains palette-pure assets only")


if __name__ == "__main__":
    main()
