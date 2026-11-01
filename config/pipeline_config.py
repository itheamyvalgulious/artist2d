"""Global pipeline configuration.

Single source of truth for the pixel metrics, master palette, API endpoints and
filesystem layout used by every module of the pipeline.
"""
from __future__ import annotations

import os
from pathlib import Path

# ----------------------------------------------------------------------------
# Paths
# ----------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = Path(os.environ.get("PIXEL_OUTPUT_DIR", ROOT / "output"))
CACHE_DIR = Path(os.environ.get("PIXEL_CACHE_DIR", ROOT / "work" / "api_cache"))
LOG_DIR = OUTPUT_DIR / "logs"
GODOT_PROJECT = ROOT / "character" / "godot_mannequin"

# ----------------------------------------------------------------------------
# Pixel metrics (true-pixel space)
# ----------------------------------------------------------------------------
TILE_SIZE = 32
CHAR_CANVAS = (64, 64)          # (width, height) true pixels
UPSCALE_FACTOR = 16             # 32px -> 512px API canvas, 64px -> 1024px
CHAR_UPSCALE = 16
SHEET_COLUMNS = 8
SHEET_SIZE = 4096               # 8 * 512
SHEET_FRAME = 512

BG_KEY_HEX = "#FF00FF"          # magenta chroma key for every generative call

# ----------------------------------------------------------------------------
# Master palette P  (64 colours, 8 ramps x 8 shades)
# Every shipped pixel must be snapped to one of these colours.  The ramp layout
# (8 consecutive entries = one hue ladder) is also what powers the deterministic
# shade()/dither() helpers used for outlines, baked shadows and macro AO.
# ----------------------------------------------------------------------------
PALETTE_HEX: tuple[str, ...] = (
    # 0  neutral / stone / steel
    "#08080c", "#14141c", "#23232e", "#363646", "#4e4e63", "#6f6f88", "#9b9bb0", "#d6d6e6",
    # 8  warm brown / wood / leather
    "#1a0f0a", "#2e1a10", "#472818", "#64401f", "#8a5c2e", "#b38046", "#d6a769", "#f0cf9a",
    # 16 skin
    "#2e1512", "#54241d", "#7d3a2a", "#a9553a", "#cf7552", "#e79a72", "#f7c39a", "#ffe0bd",
    # 24 foliage green
    "#0e1c12", "#17301c", "#224a26", "#2f6b2f", "#44943b", "#62bd4c", "#8fdc66", "#bdf08f",
    # 32 water / cyan
    "#06141f", "#0b2436", "#103a52", "#17567a", "#2279a3", "#35a2c4", "#63cbd8", "#a3eaf0",
    # 40 red / rust
    "#20080a", "#3a0f12", "#5c1518", "#83201f", "#ad3227", "#d25438", "#ec8455", "#f7b184",
    # 48 gold / sand / harvest
    "#2a1c06", "#4a3208", "#704b0c", "#96680f", "#bd8c1a", "#dfb232", "#f2d45c", "#ffee9c",
    # 56 violet / arcane
    "#150f22", "#241838", "#382456", "#523574", "#714a9c", "#9169c4", "#b78ce0", "#dbbcff",
)
PALETTE_SIZE = len(PALETTE_HEX)          # 64
assert PALETTE_SIZE == 64
RAMP_SIZE = 8

# Part-ID debug palette from PLAN 1.1 (never shipped, only used as render truth)
PART_IDS: dict[str, tuple[int, int, int]] = {
    "background": (255, 0, 255),
    "head": (255, 0, 0),
    "torso": (0, 255, 0),
    "arm_l": (0, 0, 255),
    "arm_r": (255, 255, 0),
    "leg_l": (255, 0, 255),      # overwritten below with distinct value
    "leg_r": (136, 0, 255),
    "weapon": (0, 255, 255),
    "shield": (255, 255, 255),
}
# PLAN lists leg_l as #FF00FF, identical to the magenta background.  That makes
# the truth mask ambiguous, so we use a distinct near-magenta and keep the
# documented value in the exported manifest for traceability.
PART_IDS["leg_l"] = (255, 0, 128)

# ----------------------------------------------------------------------------
# Image API (local NewAPI gateway -> Vertex AI Gemini image models)
# ----------------------------------------------------------------------------
NEWAPI_BASE = os.environ.get("NEWAPI_BASE", "http://127.0.0.1:3000")
# Never hard-code credentials here: the key is read from the environment only
# (`export NEWAPI_KEY=...`).  It is intentionally not defaulted so a missing key
# fails loudly instead of shipping a secret in the repository.
NEWAPI_KEY = os.environ.get("NEWAPI_KEY", "").strip()
# PLAN fixes the two generative roles to gpt-image-2.5-flare / -sunburst.  The
# project requirement replaces GPT Image with Gemini image models, so the same
# roles are bound to the two Gemini tiers exposed by NewAPI:
#   flare    -> fast, cheap, used for masked repaints / texture refinements
#   sunburst -> highest quality, used for master references / full sheet edits
ROLE_MODELS: dict[str, str] = {
    "flare": os.environ.get("PIXEL_MODEL_FLARE", "gemini-3.1-flash-lite-image"),
    "sunburst": os.environ.get("PIXEL_MODEL_SUNBURST", "gemini-nano-banana-2.1"),
    "pro": os.environ.get("PIXEL_MODEL_PRO", "gemini-3-pro-image"),
}
API_TIMEOUT = 300
API_RETRIES = 4
API_CONCURRENCY = int(os.environ.get("PIXEL_API_CONCURRENCY", "3"))
API_CACHE = True

# ----------------------------------------------------------------------------
# Resampling / quantisation defaults
# ----------------------------------------------------------------------------
BG_TOL_LAB = 15.0                # PLAN 1.3 background distance threshold
CORE_WINDOW_RATIO = 0.5          # central 50% (4x4 of 8x8) core window
BG_VOTE_RATIO = 0.5              # >50% background -> transparent
BAYER4 = (
    (0, 8, 2, 10),
    (12, 4, 14, 6),
    (3, 11, 1, 9),
    (15, 7, 13, 5),
)
