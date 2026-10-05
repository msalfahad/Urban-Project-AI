"""CALIBRATION_V2 - raster sheet calibration as a named, testable object: UNIFORM, XY or AFFINE.

    uniform(obs)              obs = [{"ref", "px", "real_mm"}]           one scale from distances
    xy(x_obs, y_obs)          per-axis scales; an axis with no observation is X_NOT_OBSERVED / Y_NOT_OBSERVED
                              (never copied from the other axis)
    affine(anchors)           anchors = [{"ref", "px": (u, v), "real": (X, Y)}]; least squares, >= 4 anchors so
                              that a residual exists; decomposed into sx, sy, rotation, shear (+ reflection)

Every result carries calibration_id, mode, the anchors / observations, sx, sy, rotation_deg, shear, rms_residual_mm,
max_residual_mm, status and flags (ANISOTROPIC, ROTATED, SHEARED, REFLECTED, RESIDUAL_EXCEEDED, X_NOT_OBSERVED ...).
status: CALIBRATED | CALIBRATED_WITH_FLAGS | INSUFFICIENT_ANCHORS | DEGENERATE | AXIS_NOT_OBSERVED.
A raster-derived measurement must cite the calibration_id it used and the axis it was measured along.
Stdlib only, project-agnostic.
"""

from __future__ import annotations

import hashlib
import json
import math
import statistics

POLICY_ID = "CALIBRATION_V2"
TOL = {"anisotropy": 0.01, "rotation_deg": 0.25, "shear": 0.005, "residual_mm": 20.0}
MIN_AFFINE_ANCHORS = 4


def _cid(mode, payload):
    return mode + ":" + hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()[:16]


def _scale(obs):
    ratios = [o["real_mm"] / o["px"] for o in obs if o.get("px") and o.get("real_mm")]
    if not ratios:
        return None, []
    s = statistics.median(ratios)
    res = [{"ref": o.get("ref"), "px": o["px"], "real_mm": o["real_mm"], "residual_mm": o["real_mm"] - s * o["px"]}
           for o in obs if o.get("px") and o.get("real_mm")]
    return s, res


def uniform(obs, tol=None) -> dict:
    t = dict(TOL, **(tol or {}))
    s, res = _scale(obs)
    if s is None:
        return {"policy": POLICY_ID, "mode": "UNIFORM", "status": "INSUFFICIENT_ANCHORS", "flags": [], "sx": None,
                "sy": None, "calibration_id": None, "observations": obs}
    mx = max(abs(r["residual_mm"]) for r in res)
    flags = ["RESIDUAL_EXCEEDED"] if mx > t["residual_mm"] else []
    return {"policy": POLICY_ID, "mode": "UNIFORM", "sx": s, "sy": s, "rotation_deg": 0.0, "shear": 0.0,
            "rms_residual_mm": math.sqrt(sum(r["residual_mm"] ** 2 for r in res) / len(res)),
            "max_residual_mm": mx, "observations": res, "flags": flags,
            "status": "CALIBRATED_WITH_FLAGS" if flags else "CALIBRATED",
            "assumption": "isotropic: the same scale is used on both axes", "calibration_id": _cid("UNIFORM", res)}


def xy(x_obs, y_obs, tol=None) -> dict:
    t = dict(TOL, **(tol or {}))
    sx, rx = _scale(x_obs or [])
    sy, ry = _scale(y_obs or [])
    flags = []
    if sx is None:
        flags.append("X_NOT_OBSERVED")
    if sy is None:
        flags.append("Y_NOT_OBSERVED")
    out = {"policy": POLICY_ID, "mode": "XY", "sx": sx, "sy": sy, "rotation_deg": None, "shear": None,
           "x_observations": rx, "y_observations": ry, "flags": flags}
    res = [r["residual_mm"] for r in rx + ry]
    out["rms_residual_mm"] = math.sqrt(sum(r * r for r in res) / len(res)) if res else None
    out["max_residual_mm"] = max((abs(r) for r in res), default=None)
    if sx is None or sy is None:
        out["status"] = "AXIS_NOT_OBSERVED"
    else:
        if abs(sx - sy) / ((sx + sy) / 2) > t["anisotropy"]:
            flags.append("ANISOTROPIC")
        if out["max_residual_mm"] > t["residual_mm"]:
            flags.append("RESIDUAL_EXCEEDED")
        out["status"] = "CALIBRATED_WITH_FLAGS" if flags else "CALIBRATED"
    out["calibration_id"] = _cid("XY", [rx, ry])
    return out


def _solve3(M, b):
    A = [row[:] + [bb] for row, bb in zip(M, b)]
    for c in range(3):
        p = max(range(c, 3), key=lambda r: abs(A[r][c]))
        if abs(A[p][c]) < 1e-12:
            return None
        A[c], A[p] = A[p], A[c]
        for r in range(3):
            if r != c:
                f = A[r][c] / A[c][c]
                A[r] = [x - f * y for x, y in zip(A[r], A[c])]
    return [A[i][3] / A[i][i] for i in range(3)]


def affine(anchors, tol=None) -> dict:
    t = dict(TOL, **(tol or {}))
    base = {"policy": POLICY_ID, "mode": "AFFINE", "anchors": anchors, "flags": []}
    if len(anchors) < MIN_AFFINE_ANCHORS:
        return dict(base, status="INSUFFICIENT_ANCHORS", sx=None, sy=None, calibration_id=None,
                    why=f"{len(anchors)} anchor(s); {MIN_AFFINE_ANCHORS} needed so that a residual exists")
    U = [(a["px"][0], a["px"][1], 1.0) for a in anchors]
    M = [[sum(u[i] * u[j] for u in U) for j in range(3)] for i in range(3)]
    px = _solve3(M, [sum(u[i] * a["real"][0] for u, a in zip(U, anchors)) for i in range(3)])
    py = _solve3(M, [sum(u[i] * a["real"][1] for u, a in zip(U, anchors)) for i in range(3)])
    if px is None or py is None:
        return dict(base, status="DEGENERATE", sx=None, sy=None, calibration_id=None,
                    why="anchors collinear / coincident")
    a, b, c = px
    d, e, f = py
    sx = math.hypot(a, d)
    rot = math.degrees(math.atan2(d, a))
    det = a * e - b * d
    k = (a * b + d * e) / sx
    sy = det / sx
    shear = k / sy if sy else None
    res = []
    for an in anchors:
        u, v = an["px"]
        X, Y = a * u + b * v + c, d * u + e * v + f
        res.append({"ref": an.get("ref"), "residual_mm": math.hypot(X - an["real"][0], Y - an["real"][1])})
    flags = []
    if det < 0:
        flags.append("REFLECTED")
    if abs(abs(sx) - abs(sy)) / ((abs(sx) + abs(sy)) / 2) > t["anisotropy"]:
        flags.append("ANISOTROPIC")
    r = ((rot + 180.0) % 360.0) - 180.0
    if min(abs(r), abs(abs(r) - 180.0)) > t["rotation_deg"]:
        flags.append("ROTATED")
    if shear is not None and abs(shear) > t["shear"]:
        flags.append("SHEARED")
    mx = max(x["residual_mm"] for x in res)
    if mx > t["residual_mm"]:
        flags.append("RESIDUAL_EXCEEDED")
    return dict(base, A=[[a, b], [d, e]], t=[c, f], sx=sx, sy=abs(sy), rotation_deg=rot, shear=shear,
                rms_residual_mm=math.sqrt(sum(x["residual_mm"] ** 2 for x in res) / len(res)), max_residual_mm=mx,
                residuals=res, flags=flags, status="CALIBRATED_WITH_FLAGS" if flags else "CALIBRATED",
                calibration_id=_cid("AFFINE", anchors))


def measure(px, cal, axis) -> dict:
    """A raster measurement along one axis; refuses an axis the calibration did not observe."""
    s = {"x": cal.get("sx"), "y": cal.get("sy")}[axis]
    if cal.get("mode") == "XY" and f"{axis.upper()}_NOT_OBSERVED" in cal.get("flags", []):
        return {"state": "AXIS_NOT_OBSERVED", "value_mm": None, "calibration_id": cal.get("calibration_id"),
                "axis": axis}
    single_axis = cal.get("mode") == "XY" and cal.get("status") == "AXIS_NOT_OBSERVED" and s is not None
    if s is None or (cal.get("status") not in ("CALIBRATED", "CALIBRATED_WITH_FLAGS") and not single_axis):
        return {"state": "NOT_SCALABLE", "value_mm": None, "calibration_id": cal.get("calibration_id"), "axis": axis}
    state = "MEASURED" if cal["status"] == "CALIBRATED" else (
        "MEASURED_OBSERVED_AXIS_ONLY" if single_axis else "MEASURED_WITH_FLAGS")
    return {"state": state, "value_mm": px * s,
            "calibration_id": cal["calibration_id"], "axis": axis, "flags": list(cal.get("flags", []))}
