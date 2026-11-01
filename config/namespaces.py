"""Asset-set namespaces.

Every deliverable belongs to a *set* so different worlds never share a folder.
Characters are already namespaced by name (``character/knight``,
``character/agent``); environment, mega and showcase use an explicit set name:

    environment/field    -> the original top-down terrain / shrine scene
    environment/ship     -> the new side-view sci-fi spaceship interior
    mega/field           -> the original castle megastructure
    mega/ship            -> the spaceship structural kit / assembly
    showcase/field       -> the original terrain showcase
    showcase/ship        -> the new spaceship interior showcase

The helpers below are the single source of truth for those paths.  Modules must
not concatenate ``"environment"`` / ``"mega"`` / ``"showcase"`` by hand.
"""
from __future__ import annotations

from pathlib import Path

from config.pipeline_config import OUTPUT_DIR, ROOT

SETS = ("field", "ship")


def _checked(set_name: str) -> str:
    if set_name not in SETS:
        raise ValueError(f"unknown asset set {set_name!r}; expected one of {SETS}")
    return set_name


def character_dir(name: str) -> Path:
    return OUTPUT_DIR / "character" / name


def environment_dir(set_name: str = "field") -> Path:
    return OUTPUT_DIR / "environment" / _checked(set_name)


def mega_dir(set_name: str = "field") -> Path:
    return OUTPUT_DIR / "mega" / _checked(set_name)


def showcase_dir(set_name: str = "field") -> Path:
    return OUTPUT_DIR / "showcase" / _checked(set_name)


def work_character_dir(name: str) -> Path:
    return ROOT / "work" / "character" / name


def work_environment_dir(set_name: str = "field") -> Path:
    return ROOT / "work" / "environment" / _checked(set_name)


def work_mega_dir(set_name: str = "field") -> Path:
    return ROOT / "work" / "mega" / _checked(set_name)


def work_showcase_dir(set_name: str = "field") -> Path:
    return ROOT / "work" / "showcase" / _checked(set_name)
