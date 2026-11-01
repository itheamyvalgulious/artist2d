"""Ship asset-set configuration (side-view sci-fi / cyberpunk spaceship).

The ship set is deliberately separate from the original ``field`` set.  It owns
its own tile materials, medium-structure catalog and mega-element catalog so the
two worlds can never overwrite each other.
"""
from __future__ import annotations

SET_NAME = "ship"
TILE = 32

STYLE = (
    "side-view 2D pixel art for a sci-fi cyberpunk spaceship interior: dark gunmetal "
    "and navy plating, rivets and panel seams, cyan holographic light strips, violet "
    "accent panels, small warm hazard markings, 1px near-black outline, crisp large "
    "pixel clusters, flat three-tone shading, 64-colour limited palette, zero "
    "anti-aliasing, zero blur, no gradients"
)

# Four materials generated together on one 2x2 constraint board, then made
# seamless deterministically.  Ramps index the master palette.
MATERIALS: list[dict] = [
    {
        "id": "deck",
        "ramp": 0,
        "desc": ("heavy spaceship deck plating seen from the side: long rectangular "
                 "gunmetal plates, rivet rows, a bright 1px top lip, occasional cyan "
                 "seam light, dark shadow gap between plates"),
        "seam_color": "neutral",
    },
    {
        "id": "wall",
        "ramp": 0,
        "desc": ("spaceship interior wall panel seen from the side: dark navy metal "
                 "panels with vertical seams, small vents, rivets, a thin cyan light "
                 "strip near the top and a violet accent panel"),
        "seam_color": "neutral",
    },
    {
        "id": "grate",
        "ramp": 0,
        "desc": ("industrial ventilation grate / catwalk floor seen from the side: "
                 "dark steel cross-hatch bars, deep black gaps, tiny cyan status LED"),
        "seam_color": "neutral",
    },
    {
        "id": "conduit",
        "ramp": 32,
        "desc": ("bundle of horizontal spaceship pipes and cables: dark metal tubes, "
                 "braided cables, cable ties, cyan and violet glowing lines, small "
                 "warning bands"),
        "seam_color": "cyan",
    },
]

MATERIAL_PROMPT = (
    "A 2x2 grid of four separate side-view 2D pixel-art spaceship interior materials "
    "on a solid magenta #FF00FF background. Keep the exact 2x2 grid and the hue/value "
    "locks of the input colour-constraint board, and restyle each quadrant as one "
    "material. [TOP-LEFT] {deck}. [TOP-RIGHT] {wall}. [BOTTOM-LEFT] {grate}. "
    "[BOTTOM-RIGHT] {conduit}. Each quadrant is one seamless 32x32 pixel-art tile "
    "upscaled 16x. Strictly flat side-view orthographic, no perspective, no horizon, "
    "uniform cool lighting. Large crisp square pixel clusters, 1px dark outlines, "
    "64-colour limited palette, zero anti-aliasing, zero gradients, no text, no grid "
    "lines, no borders between quadrants, no magenta inside the materials. "
    + STYLE
)

# 20 modular mega elements.  The pilot round generates the first three only.
MEGA_ELEMENTS: list[dict] = [
    {
        "id": "hull_frame",
        "name": "Hull Frame",
        "size": (128, 256),
        "desc": ("a tall heavy structural hull rib / bulkhead frame for a spaceship "
                 "interior, symmetric, riveted dark gunmetal beams, cyan strip light, "
                 "small hazard markings, exposed pipes, designed as a modular wall rib "
                 "that spans from ceiling to floor"),
    },
    {
        "id": "viewport",
        "name": "Armoured Viewport",
        "size": (128, 96),
        "desc": ("a wide armoured spaceship viewport module, thick riveted metal frame, "
                 "large window showing a deep-space starfield and a distant violet "
                 "planet, thin cyan interior glow, small warning labels, side view"),
    },
    {
        "id": "reactor_core",
        "name": "Reactor Core",
        "size": (128, 192),
        "desc": ("a spaceship reactor core module, vertical cylindrical reactor with "
                 "glowing cyan energy rings, violet magnetic coils, thick pipes and "
                 "cable bundles, hazard stripes at the base, side view"),
    },
    {
        "id": "bulkhead_door",
        "name": "Bulkhead Door",
        "size": (128, 192),
        "desc": "a heavy sci-fi bulkhead door module with a split hydraulic door, red status lamp and hazard stripes",
    },
    {
        "id": "floor_truss",
        "name": "Floor Truss",
        "size": (128, 64),
        "desc": "a modular load-bearing floor truss module with exposed girders and cable runs",
    },
    {
        "id": "ceiling_truss",
        "name": "Ceiling Truss",
        "size": (128, 64),
        "desc": "a modular ceiling truss with hanging conduits, vents and cyan strip lights",
    },
    {
        "id": "vent_stack",
        "name": "Vent Stack",
        "size": (64, 128),
        "desc": "a tall industrial vent stack with louvered grilles and a cyan status lamp",
    },
    {
        "id": "cable_run",
        "name": "Cable Run",
        "size": (128, 64),
        "desc": "a horizontal cable and pipe run with clamps, junction boxes and colored cables",
    },
    {
        "id": "pipe_junction",
        "name": "Pipe Junction",
        "size": (96, 96),
        "desc": "a chunky pipe junction with valves, gauges and a violet pressure light",
    },
    {
        "id": "ladder_well",
        "name": "Ladder Well",
        "size": (64, 192),
        "desc": "a vertical service ladder in a recessed well with safety cage and cyan lamps",
    },
    {
        "id": "railing",
        "name": "Railing",
        "size": (128, 64),
        "desc": "a modular safety railing with warning stripes and a glowing top edge",
    },
    {
        "id": "light_strip",
        "name": "Light Strip",
        "size": (64, 32),
        "desc": "a modular cyan light strip housing with a dark metal bracket",
    },
    {
        "id": "hazard_trim",
        "name": "Hazard Trim",
        "size": (64, 32),
        "desc": "a modular hazard-striped edge trim with a worn metal look",
    },
    {
        "id": "cryo_pod",
        "name": "Cryo Pod",
        "size": (64, 128),
        "desc": "a vertical cryogenic pod with frosted glass, cyan fluid lines and a status panel",
    },
    {
        "id": "antenna_array",
        "name": "Antenna Array",
        "size": (96, 128),
        "desc": "a compact antenna and sensor array on a metal base with cyan signal lights",
    },
    {
        "id": "thruster",
        "name": "Manoeuvring Thruster",
        "size": (96, 96),
        "desc": "a small manoeuvring thruster module with a bell nozzle and violet glow",
    },
    {
        "id": "airlock",
        "name": "Airlock",
        "size": (128, 192),
        "desc": "a circular airlock hatch module with a heavy locking wheel and hazard ring",
    },
    {
        "id": "escape_hatch",
        "name": "Escape Hatch",
        "size": (96, 96),
        "desc": "a floor escape hatch with a bright red handle and hazard outline",
    },
    {
        "id": "engine_nacelle",
        "name": "Engine Nacelle",
        "size": (128, 96),
        "desc": "a side-view engine nacelle with glowing cyan exhaust and exposed turbine fins",
    },
    {
        "id": "gravity_ring",
        "name": "Gravity Ring",
        "size": (128, 128),
        "desc": "a rotating gravity-ring machine with violet energy arcs and heavy bearings",
    },
]

# 10 medium structures / props.  The pilot round generates the first three only.
MEDIUM_STRUCTURES: list[dict] = [
    {
        "id": "console_bank",
        "name": "Console Bank",
        "size": (128, 64),
        "desc": ("a wide spaceship control console bank, twice as wide as tall, angled "
                 "screen panels with cyan holographic displays, rows of buttons, cables "
                 "and a dark metal housing, side view"),
    },
    {
        "id": "cargo_stack",
        "name": "Cargo Stack",
        "size": (64, 96),
        "desc": ("a tall stack of three industrial cargo containers, dark metal with "
                 "hazard stripes, straps and small cyan inventory labels, side view"),
    },
    {
        "id": "server_rack",
        "name": "Server Rack",
        "size": (64, 112),
        "desc": ("a tall spaceship server rack with rows of blinking cyan and violet "
                 "status lights, vents, cable bundles and a dark metal frame, side view"),
    },
    {
        "id": "med_pod",
        "name": "Medical Pod",
        "size": (96, 96),
        "desc": "a medical pod with a curved glass canopy, cyan readouts and a white-and-navy hull",
    },
    {
        "id": "holo_table",
        "name": "Holo Table",
        "size": (96, 64),
        "desc": "a low holo table projecting a cyan wireframe ship model",
    },
    {
        "id": "locker_bench",
        "name": "Locker Bench",
        "size": (96, 96),
        "desc": "a row of metal crew lockers with a bench, vents and small violet nameplates",
    },
    {
        "id": "security_door",
        "name": "Security Door",
        "size": (96, 128),
        "desc": "a reinforced security door with a red scanner, warning stripes and a cyan keypad",
    },
    {
        "id": "turret",
        "name": "Interior Turret",
        "size": (64, 64),
        "desc": "a compact ceiling-mounted security turret with a cyan sensor eye and twin barrels",
    },
    {
        "id": "vending_unit",
        "name": "Vending Unit",
        "size": (64, 96),
        "desc": "a cyberpunk vending machine with a glowing violet display and cans behind glass",
    },
    {
        "id": "escape_pod",
        "name": "Escape Pod",
        "size": (96, 96),
        "desc": "a round escape pod with a small window, hazard stripes and a cyan launch rail",
    },
]

PILOT_MEGA = ["hull_frame", "viewport", "reactor_core"]
PILOT_MEDIUM = ["console_bank", "cargo_stack", "server_rack"]

OBJECT_PROMPT = (
    "A single {kind} side-view 2D pixel-art asset for a sci-fi cyberpunk spaceship "
    "interior: {desc}. The object is fully visible and centred, flat side-view "
    "orthographic, no perspective, no ground plane, no cast shadow, no character, no "
    "text, no UI labels. Solid magenta #FF00FF background, completely flat and empty. "
    "Match the palette, pixel size, 1px outline weight, rivets, panel seams and "
    "cyan/violet lighting of the reference image. " + STYLE
)
