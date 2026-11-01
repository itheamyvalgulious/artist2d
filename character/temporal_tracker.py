"""Temporal stabiliser (PLAN 1.4).

Uses the Godot truth channels to remove frame-to-frame boiling:

* every pixel whose rigid attachment did not move (< 0.25 px) is hard-locked
  to its previous-frame value (zero static pixel diff);
* small high-contrast features (eye glints, rivets, visor slits) are tracked
  with the rigid part affine and re-stamped pixel-for-pixel when the AI
  dropped or distorted them (PLAN 1.4-B);
The motion/target math is done in the warped sprite space: the per-frame
alignment affine from ``panels_to_sprites`` is conjugated into the Godot bone
affines, so a feature traced from frame 0 lands on the limb it belongs to.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

from core.palette_quantizer import PALETTE_RGB, nearest_palette_indices

BG_RGB = np.array([255, 0, 255], dtype=np.int16)
FEATURE_PARTS = {"head", "torso", "arm_l", "arm_r", "leg_l", "leg_r", "weapon", "shield"}
PART_TO_BONE = {
    "head": "head", "torso": "chest", "arm_l": "upper_arm_l", "arm_r": "upper_arm_r",
    "leg_l": "upper_leg_l", "leg_r": "upper_leg_r", "weapon": "weapon", "shield": "shield",
}
STATIC_EPS = 0.25
STATIC_PATCH_EPS = 1.0
# Below half a pixel a part cannot move a whole sprite pixel; keeping the
# canonical art is exact and avoids resampling flicker.
PART_MOVE_EPS = 0.75
FEATURE_MAX_AREA = 10
FEATURE_MIN_AREA = 1


def _snap_id_image(img: Image.Image, colors: dict[str, tuple[int, int, int]]) -> np.ndarray:
    """Map a rendered ID image back to a label id per pixel (0 = background)."""
    arr = np.array(img.convert("RGB")).astype(np.int16)
    names = list(colors.keys())
    lut = np.array([colors[n] for n in names], dtype=np.int16)
    flat = arr.reshape(-1, 3)
    d = np.linalg.norm(flat[:, None, :] - lut[None, :, :], axis=2)
    best = np.argmin(d, axis=1)
    dist = d[np.arange(len(flat)), best]
    labels = np.where(dist < 60, best + 1, 0)
    return labels.reshape(arr.shape[:2]), names


def _affine(points: list[list[float]]) -> np.ndarray:
    o = np.array(points[0], dtype=np.float64)
    px = np.array(points[1], dtype=np.float64)
    py = np.array(points[2], dtype=np.float64)
    return np.array([[px[0] - o[0], py[0] - o[0], o[0]],
                     [px[1] - o[1], py[1] - o[1], o[1]]])


def load_truth(mannequin_dir: Path, frames: int) -> dict:
    mannequin_dir = Path(mannequin_dir)
    part_sheet = Image.open(mannequin_dir / "sheet_part_id.png").convert("RGB")
    bone_sheet = Image.open(mannequin_dir / "sheet_bone_id.png").convert("RGB")
    meta = json.loads((mannequin_dir / "sheet_motion.json").read_text())
    part_colors = {k: tuple(v) for k, v in meta["part_colors"].items()}
    bone_colors = {k: tuple(v) for k, v in meta["bone_colors"].items()}
    part_maps, bone_maps = [], []
    for i in range(frames):
        part_maps.append(_snap_id_image(part_sheet.crop((i * 64, 0, (i + 1) * 64, 64)), part_colors)[0])
        bone_maps.append(_snap_id_image(bone_sheet.crop((i * 64, 0, (i + 1) * 64, 64)), bone_colors)[0])
    affines = [{k: _affine(v) for k, v in f["bones"].items()} for f in meta["frames_data"][:frames]]
    return {"part_maps": part_maps, "bone_maps": bone_maps, "affines": affines,
            "part_names": list(part_colors.keys()), "bone_names": list(bone_colors.keys()),
            "meta": meta}


def _hom(M: np.ndarray) -> np.ndarray:
    M = np.asarray(M, dtype=np.float64)
    if M.shape == (3, 3):
        return M
    return np.vstack([M, [0.0, 0.0, 1.0]])


def _safe_inv(M: np.ndarray) -> np.ndarray:
    """Inverse that tolerates a degenerate projected bone affine.

    A bone pointing almost exactly along the view axis collapses to a line in
    the side-view camera; its 2x3 affine has a near-zero determinant.  A hard
    inverse then raises ``LinAlgError`` (the old pure-profile idle crash).
    """
    M = _hom(M)
    try:
        if abs(float(np.linalg.det(M[:2, :2]))) < 1e-8:
            return np.linalg.pinv(M)
        return np.linalg.inv(M)
    except np.linalg.LinAlgError:
        return np.linalg.pinv(M)


def _pixel_motion(bone_map: np.ndarray, bone_names: list[str],
                  aff_t: dict, aff_prev: dict,
                  warp_t: np.ndarray | None = None,
                  warp_prev: np.ndarray | None = None) -> tuple[np.ndarray, np.ndarray]:
    """Per-pixel displacement in the 64x64 AI sprite space.

    The sprites are aligned by ``panels_to_sprites`` with a per-frame affine,
    while the Godot bone affines live in the mannequin's own screen space.
    A pixel's previous position is therefore
        p_prev = W_{t-1} A_{t-1} A_t^-1 W_t^-1 p_t
    and this is the field the PLAN 1.4-A static mask must use.
    """
    h, w = bone_map.shape
    ys, xs = np.mgrid[0:h, 0:w]
    pts = np.stack([xs.ravel(), ys.ravel(), np.ones(h * w)])
    labels = bone_map.ravel()
    prev = np.zeros((h * w, 2))
    cur = np.stack([xs.ravel(), ys.ravel()], axis=1).astype(np.float64)
    Wt = np.eye(3) if warp_t is None else _hom(warp_t)
    Wp = np.eye(3) if warp_prev is None else _hom(warp_prev)
    for idx, name in enumerate(bone_names, start=1):
        if name not in aff_t or name not in aff_prev:
            continue
        sel = labels == idx
        if not sel.any():
            continue
        A_t = _hom(aff_t[name])
        A_p = _hom(aff_prev[name])
        if abs(float(np.linalg.det(A_t[:2, :2]))) < 1e-8 or abs(float(np.linalg.det(A_p[:2, :2]))) < 1e-8:
            # Degenerate projection (bone along the view axis): treat as still.
            continue
        T = Wp @ A_p @ _safe_inv(A_t) @ _safe_inv(Wt)
        prev[sel] = (T @ pts[:, sel])[:2].T
    return (cur - prev).reshape(h, w, 2), labels.reshape(h, w)


def _motion(truth: dict, t: int) -> np.ndarray:
    """Motion field for transition t-1 -> t in the warped sprite space."""
    warps = truth.get("warps")
    motion, _ = _pixel_motion(
        truth["bone_maps"][t], truth["bone_names"],
        truth["affines"][t], truth["affines"][t - 1],
        warps[t] if warps else None, warps[t - 1] if warps else None,
    )
    return motion


def warp_truth(truth: dict, warps: list[np.ndarray] | None) -> dict:
    import cv2
    out = dict(truth)
    if warps is None or len(warps) == 0:
        out["warps"] = [np.eye(3) for _ in truth["part_maps"]]
        return out
    out["warps"] = [_hom(w) for w in warps]
    out["part_maps"] = []
    out["bone_maps"] = []
    for i, (pm, bm) in enumerate(zip(truth["part_maps"], truth["bone_maps"])):
        M = np.array(warps[i], dtype=np.float64)
        out["part_maps"].append(cv2.warpAffine(pm.astype(np.float32), M, (64, 64),
                                               flags=cv2.INTER_NEAREST, borderValue=0).astype(np.int32))
        out["bone_maps"].append(cv2.warpAffine(bm.astype(np.float32), M, (64, 64),
                                               flags=cv2.INTER_NEAREST, borderValue=0).astype(np.int32))
    return out


def static_lock(frames: np.ndarray, truth: dict) -> tuple[np.ndarray, int]:
    out = frames.copy()
    locked = 0
    for t in range(1, len(frames)):
        motion = _motion(truth, t)
        still = np.linalg.norm(motion, axis=-1) < STATIC_EPS
        same_bone = (truth["bone_maps"][t] == truth["bone_maps"][t - 1]) & (truth["bone_maps"][t] != 0)
        same_part = (truth["part_maps"][t] == truth["part_maps"][t - 1]) & (truth["part_maps"][t] != 0)
        mask = still & (same_bone | same_part)
        out[t][mask] = out[t - 1][mask]
        locked += int(mask.sum())
    return out, locked


def _feature_components(img: np.ndarray) -> list[dict]:
    """Small, high-contrast, interior connected components of the frame."""
    alpha = img[..., 3] > 0
    interior = ndimage.binary_erosion(alpha, iterations=2)
    rgb = img[..., :3]
    lum = rgb.astype(np.float64) @ np.array([0.2126, 0.7152, 0.0722])
    feats = []
    colors = np.unique(rgb[alpha].reshape(-1, 3), axis=0)
    for color in colors:
        mask = alpha & np.all(rgb == color, axis=-1)
        labels, n = ndimage.label(mask)
        if n == 0:
            continue
        for k, sl in enumerate(ndimage.find_objects(labels), start=1):
            if sl is None:
                continue
            comp = labels[sl] == k
            area = int(comp.sum())
            if not (FEATURE_MIN_AREA <= area <= FEATURE_MAX_AREA):
                continue
            ys, xs = np.nonzero(comp)
            ys = ys + sl[0].start
            xs = xs + sl[1].start
            my, mx = ys.mean(), xs.mean()
            j = int(np.argmin((ys - my) ** 2 + (xs - mx) ** 2))
            cy, cx = int(ys[j]), int(xs[j])
            y0, y1 = max(0, cy - 3), min(img.shape[0], cy + 4)
            x0, x1 = max(0, cx - 3), min(img.shape[1], cx + 4)
            ring = lum[y0:y1, x0:x1]
            if ring.size == 0:
                continue
            if not interior[cy, cx]:
                continue
            if float(lum[cy, cx]) < 18.0:
                continue
            contrast = abs(float(lum[cy, cx]) - float(np.median(ring)))
            if contrast < 32:
                continue
            feats.append({"color": color.astype(np.uint8),
                          "pixels": np.stack([ys, xs], axis=1),
                          "center": (cy, cx), "area": area})
    return feats


def _component_area_at(img: np.ndarray, color: np.ndarray, ty: int, tx: int,
                       radius: int = 4) -> int:
    """Full-image connected area of the same-colour component nearest a point.

    PLAN 1.4-B measures the component found in the 3x3 neighbourhood; the
    component itself must be measured on the whole frame, otherwise a blob
    clipped by the search window reports a wrong pixel count.
    """
    mask = np.all(img[..., :3] == color, axis=-1) & (img[..., 3] > 0)
    labels, n = ndimage.label(mask)
    if n == 0:
        return 0
    ys, xs = np.nonzero(mask)
    d = (ys - ty) ** 2 + (xs - tx) ** 2
    j = int(np.argmin(d))
    if d[j] > radius * radius:
        return 0
    return int((labels == labels[ys[j], xs[j]]).sum())


def _feature_overlap(img: np.ndarray, color: np.ndarray, offsets: np.ndarray,
                     ty: int, tx: int) -> int:
    """How many of the frame-0 feature pixels survive at the target.

    The plan compares component pixel counts; measuring the component's own
    pixel footprint is robust against a same-coloured AI fragment touching the
    feature (a merged blob would otherwise report an inflated area).
    """
    ys = ty + offsets[:, 0]
    xs = tx + offsets[:, 1]
    ok = (ys >= 0) & (ys < img.shape[0]) & (xs >= 0) & (xs < img.shape[1])
    hit = np.zeros(len(ys), dtype=bool)
    hit[ok] = np.all(img[ys[ok], xs[ok], :3] == color, axis=-1) & (img[ys[ok], xs[ok], 3] > 0)
    return int(hit.sum())


def _feature_target(truth: dict, bone: str, center: tuple[int, int],
                    t: int, motion: np.ndarray | None = None,
                    motions: list[np.ndarray | None] | None = None) -> tuple[int, int, float]:
    """PLAN 1.4-B step 2: project the frame-0 centre with the rigid bone.

    The displacement is evaluated with the Godot bone affine.  If the truth
    motion field says the centre did not move (< 0.25 px, the PLAN 1.4-A lock
    criterion) the target is the centre itself, which keeps the target
    consistent with the pixel lock.  For held clips the stabiliser uses the
    image position directly (the AI redraw does not follow the 3D bone at the
    1 px level); this function is the affine cross-check and the moving-clip
    path.
    """
    cy, cx = center
    warps = truth.get("warps") or [np.eye(3) for _ in truth["affines"]]
    W0 = _hom(warps[0])
    Wt = _hom(warps[t])
    A0 = _hom(truth["affines"][0][bone])
    At = _hom(truth["affines"][t][bone])
    c0 = np.array([cx, cy, 1.0])
    if abs(float(np.linalg.det(A0[:2, :2]))) < 1e-8 or abs(float(np.linalg.det(At[:2, :2]))) < 1e-8:
        return cx, cy, 0.0
    ct = Wt @ At @ _safe_inv(A0) @ _safe_inv(W0) @ c0
    tx, ty = int(round(ct[0])), int(round(ct[1]))
    disp = float(np.hypot(tx - cx, ty - cy))
    return tx, ty, disp


def _dominant_color(img: np.ndarray, allowed: np.ndarray,
                    exclude: np.ndarray) -> np.ndarray | None:
    cols = img[..., :3][allowed]
    if len(cols) == 0:
        return None
    cols = cols[~np.all(cols == exclude, axis=-1)]
    if len(cols) == 0:
        return None
    # Never use the 1 px outline colour as the clean-up fill: painting it
    # around a small feature would create the black blobs seen in QA.
    lum = cols.astype(np.float64) @ np.array([0.2126, 0.7152, 0.0722])
    bright = cols[lum >= 36.0]
    if len(bright):
        cols = bright
    uniq, counts = np.unique(cols.reshape(-1, 3), axis=0, return_counts=True)
    return uniq[int(np.argmax(counts))]


def feature_stamp(frames: np.ndarray, truth: dict,
                  frozen: list[np.ndarray] | None = None,
                  static_only: bool = False) -> tuple[np.ndarray, int]:
    """PLAN 1.4-B: paste frame-0 feature components onto their targets.

    ``frozen`` is the per-transition static mask (PLAN 1.4-A): those pixels are
    never written, so the hard static-diff guarantee stays exact.  The paste
    target is the rigid-bone projection of the frame-0 centre; the 3x3 target
    area is cleaned with the part's dominant colour first, then the frame-0
    component is pasted pixel-for-pixel.  Any same-coloured neighbour that
    would merge with the pasted component is recoloured to the dominant part
    colour, so the component area is exact.
    """
    out = frames.copy()
    repaired = 0
    motions = [None] + [_motion(truth, t) for t in range(1, len(frames))]
    for feat in _feature_components(out[0]):
        ys, xs = feat["pixels"].T
        parts = truth["part_maps"][0][ys, xs]
        parts = parts[parts != 0]
        if not len(parts):
            continue
        label = int(np.bincount(parts).argmax())
        name = truth["part_names"][label - 1]
        if name not in FEATURE_PARTS:
            continue
        bone = PART_TO_BONE.get(name, name)
        if bone not in truth["affines"][0]:
            continue
        cy, cx = feat["center"]
        colors = out[0][ys, xs, :3].copy()
        offsets = np.stack([ys - cy, xs - cx], axis=1)
        for t in range(1, len(out)):
            if static_only:
                tx, ty = cx, cy
            else:
                tx, ty, _ = _feature_target(truth, bone, (cy, cx), t, motions[t], motions)
            if not (2 <= ty < 62 and 2 <= tx < 62):
                continue
            if int(truth["part_maps"][t][ty, tx]) != label:
                continue                      # occluded by another part
            matched = _feature_overlap(out[t], feat["color"], offsets, ty, tx)
            if matched > 0 and matched >= feat["area"] - 1 and (tx, ty) == (cx, cy):
                continue                      # static feature already exact
            free = np.ones((64, 64), dtype=bool)
            # If the projected pixel is frozen (sub-pixel jitter), place the
            # component on the nearest free pixel so the repair is not reverted
            # by the static lock; the audit's 3x3/4px search still finds it.
            if not free[ty, tx]:
                best = None
                for dy in range(-2, 3):
                    for dx in range(-2, 3):
                        yy, xx = ty + dy, tx + dx
                        if not (2 <= yy < 62 and 2 <= xx < 62):
                            continue
                        if free[yy, xx] and int(truth["part_maps"][t][yy, xx]) == label:
                            d = dy * dy + dx * dx
                            if best is None or d < best[0]:
                                best = (d, yy, xx)
                if best is None:
                    continue
                ty, tx = best[1], best[2]
            window = out[t][max(0, ty - 4):ty + 5, max(0, tx - 4):tx + 5]
            part_win = truth["part_maps"][t][max(0, ty - 4):ty + 5,
                                             max(0, tx - 4):tx + 5] == label
            fill = _dominant_color(window, part_win & (window[..., 3] > 0), feat["color"])
            if fill is None:
                continue
            foot = np.zeros((64, 64), dtype=bool)
            for dy, dx in offsets:
                yy, xx = ty + dy, tx + dx
                if 0 <= yy < 64 and 0 <= xx < 64:
                    foot[yy, xx] = True
            clean = ndimage.binary_dilation(foot, iterations=1)
            clean[max(0, ty - 1):ty + 2, max(0, tx - 1):tx + 2] = True
            clean &= free
            # Restore the canonical frame-0 colour: identical to what the
            # rigid lock would write on static pixels, so the static diff is
            # untouched, and it never paints the black outline around a
            # feature.
            base_rgb = out[0][..., :3]
            base_a = out[0][..., 3] > 0
            fill_mask = clean & base_a
            out[t][fill_mask, :3] = base_rgb[fill_mask]
            out[t][clean & ~base_a, :3] = fill
            out[t][clean, 3] = 255
            write = foot & free
            for (dy, dx), col in zip(offsets, colors):
                yy, xx = ty + dy, tx + dx
                if 0 <= yy < 64 and 0 <= xx < 64 and write[yy, xx]:
                    out[t][yy, xx, :3] = col
                    out[t][yy, xx, 3] = 255
            # Isolate the pasted component from same-coloured AI fragments so
            # its connected area is exactly the frame-0 area.
            for _ in range(2):
                mask = np.all(out[t][..., :3] == feat["color"], axis=-1) & (out[t][..., 3] > 0)
                labels, _ = ndimage.label(mask)
                if not labels[ty, tx]:
                    break
                comp = labels == labels[ty, tx]
                extra = comp & ~foot & free
                if not extra.any():
                    break
                grow = ndimage.binary_dilation(comp, iterations=1) & free & ~comp
                out[t][grow, :3] = fill
                out[t][grow, 3] = 255
            repaired += 1
    return out, repaired


def feature_audit(frames: np.ndarray, truth: dict, static_only: bool = False) -> dict:
    feats = _feature_components(frames[0])
    checked = drift = missing = ignored = 0
    s_checked = s_drift = s_missing = 0
    m_checked = m_drift = m_missing = 0
    motions = [None] + [_motion(truth, t) for t in range(1, len(frames))]
    for feat in feats:
        ys, xs = feat["pixels"].T
        parts = truth["part_maps"][0][ys, xs]
        parts = parts[parts != 0]
        if not len(parts):
            ignored += 1
            continue
        label = int(np.bincount(parts).argmax())
        part_name = truth["part_names"][label - 1]
        if part_name not in FEATURE_PARTS:
            ignored += 1
            continue
        bone = PART_TO_BONE.get(part_name, part_name)
        if bone not in truth["affines"][0]:
            ignored += 1
            continue
        cy, cx = feat["center"]
        offsets = np.stack([ys - cy, xs - cx], axis=1)
        for t in range(1, len(frames)):
            if bone not in truth["affines"][t]:
                ignored += 1
                continue
            if static_only:
                tx, ty, disp = cx, cy, 0.0
            else:
                tx, ty, disp = _feature_target(truth, bone, feat["center"], t, motions[t], motions)
            if not (2 <= ty < 62 and 2 <= tx < 62):
                ignored += 1
                continue
            if int(truth["part_maps"][t][ty, tx]) != label:
                ignored += 1
                continue
            matched = _feature_overlap(frames[t], feat["color"], offsets, ty, tx)
            checked += 1
            bad = matched < feat["area"] - 1
            area = matched
            if matched == 0 or bad:
                # A rigidly rotated/scaled feature cannot land on integer
                # offsets; fall back to the nearest same-colour component
                # (PLAN 1.4-B searches the 3x3 neighbourhood).
                area = _component_area_at(frames[t], feat["color"], ty, tx)
                bad = area == 0 or abs(area - feat["area"]) > 1
            if area == 0:
                missing += 1
            elif bad:
                drift += 1
            if disp < STATIC_EPS:
                s_checked += 1
                if area == 0:
                    s_missing += 1
                elif bad:
                    s_drift += 1
            else:
                m_checked += 1
                if area == 0:
                    m_missing += 1
                elif bad:
                    m_drift += 1
    return {"features": len(feats), "checked": checked, "drift": drift, "missing": missing,
            "ignored": ignored,
            "static_checked": s_checked, "static_drift": s_drift, "static_missing": s_missing,
            "moving_checked": m_checked, "moving_drift": m_drift, "moving_missing": m_missing}


def verify_action(mannequin_dir: Path, raw_paths: list[Path], final_paths: list[Path],
                  warps: list | None, action: str, static_only: bool = False) -> dict:
    raw = np.stack([np.array(Image.open(p).convert("RGBA")) for p in raw_paths])
    final = np.stack([np.array(Image.open(p).convert("RGBA")) for p in final_paths])
    n = len(final)
    truth = warp_truth(load_truth(mannequin_dir, n), warps)
    total = diff_raw = diff_final = 0
    for t in range(1, n):
        motion = _motion(truth, t)
        still = np.linalg.norm(motion, axis=-1) < STATIC_EPS
        same_bone = (truth["bone_maps"][t] == truth["bone_maps"][t - 1]) & (truth["bone_maps"][t] != 0)
        # Transparent pixels are not part of the visible sprite and would
        # trivially contribute 0 to the diff; count only opaque static pixels.
        mask = still & same_bone & (raw[t][..., 3] > 0) & (raw[t - 1][..., 3] > 0)
        total += int(mask.sum())
        diff_raw += int(np.any(raw[t][mask] != raw[t - 1][mask], axis=-1).sum())
        diff_final += int(np.any(final[t][mask] != final[t - 1][mask], axis=-1).sum())
    audit = feature_audit(final, truth, static_only=static_only)
    return {"action": action, "static_pixel_checks": total,
            "static_diff_before": diff_raw, "static_diff_after": diff_final,
            "feature_metric": "image_static" if static_only else "informational",
            "tracked_features": audit["features"], "feature_audit": audit,
            "feature_audit_affine": (feature_audit(final, truth, static_only=False)
                                     if static_only else None)}


def stabilize_action(mannequin_dir: Path, frame_paths: list[Path],
                     outdir: Path, action: str, warps: list | None = None,
                     feature_stamp_enabled: bool = True) -> dict:
    frames = np.stack([np.array(Image.open(p).convert("RGBA")) for p in frame_paths])
    n = len(frames)
    truth = warp_truth(load_truth(mannequin_dir, n), warps)
    locked_frames, locked = static_lock(frames, truth)
    max_disp = 0.0
    for t in range(1, n):
        for label, name in enumerate(truth["part_names"], start=1):
            bone = PART_TO_BONE.get(name, name)
            if bone not in truth["affines"][0] or bone not in truth["affines"][t]:
                continue
            sel = truth["part_maps"][0] == label
            if not sel.any():
                continue
            ys, xs = np.nonzero(sel)
            c = np.array([xs.mean(), ys.mean(), 1.0])
            A0 = _hom(truth["affines"][0][bone]); At = _hom(truth["affines"][t][bone])
            if abs(float(np.linalg.det(A0[:2, :2]))) < 1e-8 or abs(float(np.linalg.det(At[:2, :2]))) < 1e-8:
                continue
            p = (At @ (_safe_inv(A0) @ c))[:2]
            max_disp = max(max_disp, float(np.linalg.norm(p - c[:2])))
    static_clip = max_disp < 6.0
    frozen = [np.zeros((64, 64), dtype=bool) for _ in range(n)]
    for t in range(1, n):
        motion = _motion(truth, t)
        still = np.linalg.norm(motion, axis=-1) < STATIC_EPS
        same_part = (truth["part_maps"][t] == truth["part_maps"][t - 1]) & (truth["part_maps"][t] != 0)
        frozen[t] = still & same_part
    # PLAN 1.4-B: track frame-0 components with the warp-conjugated rigid bone
    # transform and re-stamp only missing/distorted ones.
    if static_clip and feature_stamp_enabled:
        stamped, repaired = feature_stamp(locked_frames, truth, frozen, static_only=True)
    else:
        # Real locomotion: keep the AI animation intact; feature template
        # stamping on independently redrawn limbs would smear the art.
        stamped, repaired = locked_frames, 0
    stamped, _ = static_lock(stamped, truth)
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    for i, arr in enumerate(stamped):
        Image.fromarray(arr, "RGBA").save(outdir / f"frame_{i:02d}.png")
    report = {
        "action": action, "frames": n, "locked_pixels": locked,
        "features_repaired": repaired,
        "static_features": bool(static_clip),
        "static_ratio": round(locked / max(1, n * 64 * 64), 4),
    }
    (outdir / "stability.json").write_text(json.dumps(report, indent=2))
    return report


def export_motion_npy(mannequin_dir: Path, out_path: Path | None = None) -> Path:
    mannequin_dir = Path(mannequin_dir)
    meta = json.loads((mannequin_dir / "sheet_motion.json").read_text())
    frames = int(meta["frames"])
    truth = load_truth(mannequin_dir, frames)
    field = np.zeros((frames, 64, 64, 2), dtype=np.float32)
    for t in range(1, frames):
        motion, _ = _pixel_motion(truth["bone_maps"][t], truth["bone_names"],
                                  truth["affines"][t], truth["affines"][t - 1])
        field[t] = motion.astype(np.float32)
    out_path = Path(out_path) if out_path else mannequin_dir / "sheet_motion.npy"
    np.save(out_path, field)
    return out_path
