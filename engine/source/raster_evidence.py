"""RASTER EVIDENCE (V3b) - scale calibration, measurement grades and cross-sheet checks for raster drawings.

A raster sheet (scanned / plotted elevation, section, detail) is evidence only after its scale is PROVED:

    calibrate(observations, nominal)   observations = [{"printed_cm", "px", "ref"}] - printed dimensions whose pixel
                                       length was measured on the same sheet. At least two, all agreeing with their
                                       median within tol, else NOT_SCALABLE (only printed values may then be used)
    measure(px, cal)                   a scaled value (grade SCALED) with its uncertainty
    printed(value_cm, ...)             a printed value read on the sheet (grade PRINTED); when its dimension line was
                                       also measured, the pixel length must agree with the calibrated scale
    linear_map(pairs)                  plan coordinate -> sheet pixel (least squares) for plan-to-elevation projection
    width_check(plan_cm, px, cal)      the cross-sheet gate: a plan width (exact CAD) against the raster width

Grades: PRINTED (dimension text read and its dimension line located) = confidence H; SCALED (calibrated sheet) = M.
Nothing here reads pixels: the caller measures, this module decides what the measurement may claim.
Stdlib only, project-agnostic.
"""

from __future__ import annotations

import hashlib
import json
import statistics

POLICY_ID = "RASTER_EVIDENCE_V1"
CALIBRATED, NOT_SCALABLE = "CALIBRATED", "NOT_SCALABLE"
PRINTED, SCALED = "PRINTED", "SCALED"
CONFIDENCE = {PRINTED: "H", SCALED: "M"}


def calibrate(observations, nominal_px_per_cm=None, tol=0.01, min_obs=2, px_tol=0.0) -> dict:
    """Scale from >= min_obs printed dimensions; an observation agrees when its relative deviation from the median
    scale is <= tol OR its pixel residual is <= px_tol (line-thickness error on short dimensions)."""
    obs = [o for o in observations if o.get("printed_cm") and o.get("px")]
    if len(obs) < min_obs:
        return {"state": NOT_SCALABLE, "why": f"{len(obs)} printed dimension(s) measured, {min_obs} required",
                "observations": obs}
    ratios = [o["px"] / o["printed_cm"] for o in obs]
    s = statistics.median(ratios)
    resid = [{"ref": o.get("ref"), "printed_cm": o["printed_cm"], "px": o["px"], "px_per_cm": r,
              "rel_dev": (r - s) / s, "px_residual": o["px"] - s * o["printed_cm"]} for o, r in zip(obs, ratios)]
    for x in resid:
        x["agrees"] = abs(x["rel_dev"]) <= tol or abs(x["px_residual"]) <= px_tol
    worst = max(abs(x["rel_dev"]) for x in resid if x["printed_cm"] == max(o["printed_cm"] for o in obs)) \
        if all(x["agrees"] for x in resid) else max(abs(x["rel_dev"]) for x in resid)
    out = {"px_per_cm": s, "observations": resid, "worst_rel_dev": worst, "tol": tol, "px_tol": px_tol,
           "nominal_px_per_cm": nominal_px_per_cm,
           "nominal_rel_dev": None if not nominal_px_per_cm else (s - nominal_px_per_cm) / nominal_px_per_cm}
    if not all(x["agrees"] for x in resid):
        bad = [x["ref"] for x in resid if not x["agrees"]]
        out.update(state=NOT_SCALABLE, why=f"printed dimensions disagree (> {tol:.0%} and > {px_tol:g} px): {bad}")
    else:
        out.update(state=CALIBRATED, why=None)
    return out


def measure(px, cal, px_tol=3.0) -> dict:
    if cal.get("state") != CALIBRATED:
        return {"state": NOT_SCALABLE, "value_cm": None, "grade": None}
    v = px / cal["px_per_cm"]
    unc = px_tol / cal["px_per_cm"] + cal["worst_rel_dev"] * v
    return {"state": "MEASURED", "value_cm": v, "uncertainty_cm": unc, "grade": SCALED, "confidence": CONFIDENCE[SCALED]}


def printed(value_cm, *, px=None, cal=None, tol=0.02) -> dict:
    """A printed dimension. If its line was measured on a calibrated sheet the two must agree (else CONFLICT)."""
    out = {"value_cm": value_cm, "grade": PRINTED, "confidence": CONFIDENCE[PRINTED], "state": "READ"}
    if px is not None and cal and cal.get("state") == CALIBRATED:
        m = px / cal["px_per_cm"]
        dev = (m - value_cm) / value_cm if value_cm else None
        out["measured_cm"], out["rel_dev"] = m, dev
        out["state"] = "VERIFIED" if dev is not None and abs(dev) <= tol else "CONFLICT"
    return out


def linear_map(pairs) -> dict:
    """pairs [(u, x)]: least-squares x = a + b u with the worst residual (pixels)."""
    n = len(pairs)
    if n < 2:
        return {"state": "INSUFFICIENT", "n": n}
    mu = sum(u for u, _ in pairs) / n
    mx = sum(x for _, x in pairs) / n
    suu = sum((u - mu) ** 2 for u, _ in pairs)
    if suu == 0:
        return {"state": "DEGENERATE", "n": n}
    b = sum((u - mu) * (x - mx) for u, x in pairs) / suu
    a = mx - b * mu
    res = [x - (a + b * u) for u, x in pairs]
    return {"state": "FITTED", "a": a, "b": b, "n": n, "max_residual_px": max(abs(r) for r in res), "residuals": res}


def width_check(plan_cm, px, cal, tol=0.03) -> dict:
    if cal.get("state") != CALIBRATED or not plan_cm:
        return {"state": "NOT_CHECKED"}
    m = px / cal["px_per_cm"]
    dev = (m - plan_cm) / plan_cm
    return {"state": "MATCH" if abs(dev) <= tol else "MISMATCH", "plan_cm": plan_cm, "raster_cm": m, "rel_dev": dev,
            "tol": tol}


def claim(*, sheet_sha256, sheet_ref, box_px, quantity, value_cm, grade, evidence, cal_state=None, check=None) -> dict:
    rec = {"sheet_sha256": sheet_sha256, "sheet_ref": sheet_ref, "box_px": list(box_px), "quantity": quantity,
           "value_cm": value_cm, "grade": grade, "confidence": CONFIDENCE.get(grade), "authority": "RASTER_DERIVED",
           "evidence": evidence, "calibration": cal_state, "check": check}
    rec["claim_id"] = hashlib.sha256(json.dumps(rec, sort_keys=True, default=str).encode()).hexdigest()[:16]
    return rec


def policy_record() -> dict:
    rec = {"policy_id": POLICY_ID,
           "rule": "a raster sheet is evidence only after >= 2 printed dimensions measured on it agree within 1 %; "
                   "printed values are grade PRINTED (H), calibrated measurements grade SCALED (M); a raster width must "
                   "match the exact plan width within 3 % before any height from that sheet is used",
           "never": ["a scaled value from an uncalibrated sheet", "OCR text without its located dimension line",
                     "a raster height whose plan width check failed"]}
    rec["digest"] = hashlib.sha256(json.dumps(rec, sort_keys=True).encode()).hexdigest()
    return rec
