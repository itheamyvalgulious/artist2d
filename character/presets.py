"""Character presets and action contracts.

Each character is fully described here: identity prompt, board prompt extras,
mannequin proportions, per-action weapon state and the transition anchors that
must be pixel-identical between clips.
"""
from __future__ import annotations

from character.sheet_compositor import CharacterSpec

PIXEL_STYLE = (
    "TRUE low-resolution pixel art: large crisp square pixel clusters, 1px near-black outline, "
    "64 colour limited palette, flat three-tone shading, zero anti-aliasing, zero blur, no gradients"
)

KNIGHT = CharacterSpec(
    name="knight",
    description=(
        "a wandering knight in weathered steel plate armour with a deep crimson tabard, "
        "a round wooden shield with an iron boss strapped to the left arm, and a long greatsword "
        "gripped in the right hand"
    ),
    style=PIXEL_STYLE,
    ref_extra=(
        "helmet with a closed visor and a small crest, battle-worn plate, crimson cloth at the waist"
    ),
    ref_pose=(
        "Orthographic near-profile view from the character's RIGHT side (the sword side), about "
        "75 degrees off the front: the right arm and the greatsword are nearest the camera, the "
        "round wooden shield on the left arm is on the FAR side, mostly behind the body and seen "
        "at a steep foreshortened angle so it never covers the chest or the sword. Neutral standing "
        "A-pose, both feet visible, entire body from head to boots centred in frame with a margin "
        "on every side."
    ),
    board_extra=(
        "The knight's helmet has a bright steel visor; never turn the face into a black or "
        "featureless plate. The greatsword is in the right hand nearest the camera, the round "
        "shield is on the far left arm and must never cover the chest or the sword."
    ),
    action_extra={
        "attack": " The sword swings in a forward downward chop; the shield stays low on the far side.",
        "defend": " The shield is raised across the chest as a block; the sword stays visible beside it.",
        "in_air": " Both feet are clearly off the ground and the knees are tucked.",
    },
)

_SLASH_ARC = (
    " BLADE ARC: across the eight panels the katana must sweep progressively from high right to "
    "low left: panel 1 blade high behind the right shoulder, panel 2 blade about 45 degrees above "
    "horizontal, panel 3 blade horizontal at chest height, panel 4 blade about 45 degrees below "
    "horizontal, panel 5 blade low near the left knee, panel 6 follow-through behind the left hip, "
    "panel 7 recover toward guard, panel 8 guard/run. Every panel must show a different blade "
    "angle; never jump from a high blade to a low blade without the intermediate angles."
)
_FRAMING = (
    " FRAMING: draw the character at about 65% of the panel height, centred, with a wide magenta "
    "margin on all four sides. The full katana blade / pistol muzzle must remain inside the panel "
    "and must never touch or cross the panel edge."
)

AGENT = CharacterSpec(
    name="agent",
    description=(
        "a female cyberpunk special agent with long flowing silver hair and violet eyes, wearing "
        "a fitted dark-navy cropped top with short sleeves, separate dark detached forearm sleeves "
        "with cyan technical trim, short navy shorts, and black combat boots. She carries a katana "
        "(sheathed diagonally across her back with the hilt above her right shoulder, or drawn in her "
        "right hand) and a compact dark pistol (holstered at her right hip, or drawn in her hand)"
    ),
    style=(
        "TRUE low-resolution pixel art: large crisp square pixel clusters, 1px near-black outline, "
        "64 colour limited palette, flat three-tone shading, cool gunmetal / navy / silver / cyan / "
        "violet palette, zero anti-aliasing, zero blur, no gradients"
    ),
    ref_extra=(
        "long silver hair reaching mid-back, visible violet eyes, short-sleeve top plus detached "
        "forearm sleeves, short shorts, black boots, a katana in a dark scabbard on her back, a "
        "compact pistol in a hip holster; in the reference panel the katana is drawn and the pistol is "
        "displayed, both fully visible, so the model knows their exact length and shape; "
        "bare legs use warm skin tones with warm brown shadows, never purple legs; violet appears only "
        "in the eyes and tiny accents, cyan only on the sleeve trim and pistol sight"
    ),
    ref_pose=(
        "Orthographic PURE SIDE PROFILE from the character's RIGHT side (90 degrees, no front "
        "foreshortening), facing screen-left. She holds the full-length katana DRAWN in her right "
        "hand, blade angled up and fully visible at full length; the empty dark scabbard is on her "
        "back. The compact pistol is held in her left hand at her side (or holstered at the hip) and "
        "is fully visible. The katana blade is much longer than the hilt and has a clear guard; the "
        "pistol has a clear barrel, grip and trigger guard. Both weapons are complete, no extra "
        "weapons, no shield. Neutral standing A-pose with the weapons displayed, both feet visible, "
        "entire body and both weapons inside the frame with a wide margin."
    ),
    camera=(-70.0, 37.0, 0.0),
    camera_text=(
        "pure side profile (90 degrees) from the character's RIGHT side, facing screen-left, "
        "with no front foreshortening"
    ),
    board_extra=(
        "The character is a woman, not a man and not the knight: long flowing SILVER hair (never a "
        "helmet, never short), VIOLET eyes, bare legs between short shorts and black boots, short "
        "sleeves on the upper arms and separate detached sleeves on the forearms. Keep the exact "
        "same face, hair length, outfit colours and body proportions as the top-left reference in "
        "every panel. BODY CONSISTENCY: keep the same slim body in every action: same head size, "
        "same waist, same narrow thigh and calf thickness as the reference; never thicken or "
        "muscularize the legs in running, slashing or shooting poses. The katana scabbard is dark "
        "with a silver hilt; the pistol is compact and dark with a small cyan sight. The top-left "
        "reference panel shows the exact full-length katana blade, guard, handle and scabbard and the "
        "exact pistol; use those shapes in every panel and never shorten the katana into a dagger. "
        "Never duplicate a weapon, never replace the katana with a greatsword, and never add a shield."
    ),
    action_extra={
        "idle": (
            " Standing relaxed idle, weight on one leg, both hands empty, katana sheathed on the "
            "back and pistol holstered at the hip. All eight frames are subtle breathing motion; "
            "the silver hair and the stowed weapons stay attached to the body."
        ),
        "run": (
            " A clean side-view run cycle facing screen-left: alternating strides, knees driving, "
            "arms pumping, silver hair streaming behind. The legs must stay as slim as the idle "
            "reference; do not add thigh or calf muscle. Both weapons are stowed: katana on the "
            "back, pistol in the hip holster. Never put a weapon in her hands."
        ),
        "jump": (
            " The take-off / crouch phase of a jump: knees bend, body compresses, arms swing back, "
            "then the feet leave the ground. Katana on the back and pistol holstered."
        ),
        "in_air": (
            " Airborne: both feet clearly off the ground, knees tucked, hair and clothes lifted. "
            "Katana on the back and pistol holstered. The first frame must match the last frame of "
            "the jump clip exactly."
        ),
        "shoot1": (
            " Standing pistol shot: right arm extended forward at shoulder height, pistol aimed "
            "screen-left, left hand steadying the grip or held close, torso slightly turned into "
            "the shot. The katana stays sheathed on her back. Muzzle flash may appear as a small "
            "cyan-white star but no bullet, beam or shell casings."
        ),
        "shoot2": (
            " Run-and-gun pistol shot: legs stay in a running stride, upper body aims the pistol "
            "forward at shoulder height, hair streaming. The katana stays sheathed on her back. "
            "The first and last frames must match the run cycle poses."
        ),
        "shoot3": (
            " Airborne pistol shot: knees tucked, both feet off the ground, right arm aims the "
            "pistol forward, hair lifted. Katana stays sheathed on her back."
        ),
        "slash1": (
            " Standing katana slash: the katana is drawn in the right hand and sweeps in a fast "
            "diagonal downward cut from high right to low left, one hand on the hilt, torso twisting "
            "into the cut, silver hair following. The pistol stays holstered at the hip. The blade "
            "must be complete and at full length in every frame." + _SLASH_ARC + _FRAMING
        ),
        "slash2": (
            " Running katana slash: legs stay in a running stride while the drawn katana sweeps in "
            "a diagonal cut, hair and sleeves streaming. The pistol stays holstered. The first and "
            "last frames must match the run cycle poses; the blade must be complete."
            + _SLASH_ARC + _FRAMING
        ),
        "slash3": (
            " Airborne katana slash: knees tucked, both feet off the ground, drawn katana sweeping "
            "in a diagonal cut, hair lifted. The pistol stays holstered; the blade is complete."
            + _SLASH_ARC + _FRAMING
        ),
        "block": (
            " Katana parry / guard: the katana is drawn and held with both hands in front of the "
            "chest, blade angled up and across the body to deflect an incoming attack. Knees are "
            "slightly bent, weight low, eyes forward over the blade. This is a SWORD block, not a "
            "shield block: no shield, and the pistol stays holstered. The blade is complete."
        ),
        "roll": (
            " Compact forward roll: the body curls into a tight ball, knees to the chest, head "
            "tucked, arms wrapped around the knees, and the ball rotates forward through a full "
            "360 degrees. No extended limbs, no detached boots or hair. Draw the ball at about 60% "
            "of the panel height, centred, with a wide magenta margin on all sides; the entire "
            "rolling body must stay inside the panel and must never touch or cross an edge."
        ),
    },
    gear={
        "idle": {"katana": "back", "pistol": "hip"},
        "run": {"katana": "back", "pistol": "hip"},
        "jump": {"katana": "back", "pistol": "hip"},
        "in_air": {"katana": "back", "pistol": "hip"},
        "shoot1": {"katana": "back", "pistol": "hand"},
        "shoot2": {"katana": "back", "pistol": "hand"},
        "shoot3": {"katana": "back", "pistol": "hand"},
        "slash1": {"katana": "hand", "pistol": "hip"},
        "slash2": {"katana": "hand", "pistol": "hip"},
        "slash3": {"katana": "hand", "pistol": "hip"},
        "block": {"katana": "hand", "pistol": "hip"},
        "roll": {"katana": "back", "pistol": "hip"},
    },
    params={
        "head_scale": 0.98,
        "torso_len": 0.95,
        "limb_len": 1.0,
        "shoulder_width": 0.82,
    },
)

PRESETS: dict[str, CharacterSpec] = {"knight": KNIGHT, "agent": AGENT}

# action -> (start anchor, end anchor); an anchor is ``action:frame``.
TRANSITIONS: dict[str, dict[str, tuple[str | None, str | None]]] = {
    "agent": {
        "in_air": ("jump:7", None),
        "shoot1": ("idle:0", "idle:7"),
        "slash1": ("idle:0", "idle:7"),
        "block": ("idle:0", "idle:7"),
        "roll": ("idle:0", "idle:7"),
        "shoot2": ("run:0", "run:7"),
        "slash2": ("run:0", "run:7"),
        "shoot3": ("in_air:0", "in_air:7"),
        "slash3": ("in_air:0", "in_air:7"),
    },
    "knight": {},
}


def transition_dependencies(character: str, actions: list[str]) -> list[str]:
    deps: list[str] = []
    for action in actions:
        for anchor in TRANSITIONS.get(character, {}).get(action, (None, None)):
            if not anchor:
                continue
            dep = anchor.split(":", 1)[0]
            if dep not in actions and dep not in deps:
                deps.append(dep)
    return deps
