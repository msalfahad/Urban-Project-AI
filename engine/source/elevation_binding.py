"""ELEVATION BINDING - which physical object a dimension printed on an elevation or section measures (generic).

A dimension on an elevation names a vertical distance between two witness points. It belongs to an object only when
independent evidence ties the drawn feature to that object's plan geometry. Resemblance is not evidence: a sunken box
on an elevation could be a pool, a lift pit or a planter.

    level_at(y, datum_y, datum_level_m, units_per_m)    level of a drawing ordinate from a datum
    dimension_span(y_from, y_to, datum)                    the two witness levels and the span of a vertical dimension
    cylinder_from_generators(half_width, offsets)          a cylinder seen side-on: silhouette half-width = radius,
                                                           generators at R cos(theta), symmetric about the axis
    arc_projected_half_width(R, a0, a1, axis)              half extent of a plan arc projected onto an elevation axis
    arc_projected_interval(R, a0, a1, axis)                its (low, high): a symmetric drawn feature needs low = -high
    binding_verdict(criteria)                              BOUND only with a plan identity label, a dimension match and
                                                           a feature match, and no failed or contradicting criterion;
                                                           otherwise SOURCE_NOT_BOUND
    floor_profile(profiles)                                UNIFORM only when every source shows one and the same level;
                                                           one source with a level change and another without is a
                                                           PROFILE_CONFLICT, so no single dimension applies throughout

Stdlib only. No project data.
"""

from __future__ import annotations

import math

BOUND = "BOUND"
NOT_BOUND = "SOURCE_NOT_BOUND"
IDENTITY_LABEL = "IDENTITY_LABEL"
DIMENSION_MATCH = "DIMENSION_MATCH"
FEATURE_MATCH = "FEATURE_MATCH"
LEVEL_MATCH = "LEVEL_MATCH"
CONTRADICTION = "CONTRADICTION"
KINDS = (IDENTITY_LABEL, DIMENSION_MATCH, FEATURE_MATCH, LEVEL_MATCH, CONTRADICTION)
UNIFORM = "UNIFORM"
PROFILE_CONFLICT = "PROFILE_CONFLICT"
VARYING = "VARYING"
NOT_SHOWN = "NOT_SHOWN"


class ElevationBindingError(ValueError):
    pass


def level_at(y, datum_y, datum_level_m, units_per_m=1000.0):
    """Level (m) of a drawing ordinate y, from a datum ordinate whose level is known."""
    if units_per_m <= 0:
        raise ElevationBindingError("units_per_m must be positive")
    return datum_level_m + (float(y) - float(datum_y)) / units_per_m


def dimension_span(y_from, y_to, datum_y, datum_level_m, units_per_m=1000.0):
    """The two witness levels of a vertical dimension and its span (m)."""
    a = level_at(y_from, datum_y, datum_level_m, units_per_m)
    b = level_at(y_to, datum_y, datum_level_m, units_per_m)
    return {"low_m": min(a, b), "high_m": max(a, b), "span_m": abs(b - a)}


def cylinder_from_generators(half_width, offsets, *, tol=1.0):
    """A cylinder of radius R seen side-on: its silhouettes sit at +-R and every generator line at R cos(theta), with
    the same set on both sides of the axis. offsets: generator positions relative to the axis (drawing units)."""
    R = float(half_width)
    if R <= 0:
        raise ElevationBindingError("half width must be positive")
    inside = all(abs(o) <= R + tol for o in offsets)
    pos = sorted(o for o in offsets if o > 0)
    neg = sorted(-o for o in offsets if o < 0)
    symmetric = len(pos) == len(neg) and all(abs(a - b) <= tol for a, b in zip(pos, neg))
    angles = [math.degrees(math.acos(min(1.0, o / R))) for o in pos]
    return {"radius": R, "angles_deg": angles, "inside": inside, "symmetric": symmetric,
            "consistent": inside and symmetric and bool(pos)}


def arc_projected_half_width(R, a0_deg, a1_deg, axis="y"):
    """Half extent of a CCW arc (a0 -> a1, degrees) projected onto the plan x or y axis, about the arc centre: the
    largest |R sin t| (axis y) or |R cos t| (axis x) over the sweep, end points and interior extrema included."""
    if R <= 0:
        raise ElevationBindingError("radius must be positive")
    a0 = a0_deg % 360.0
    sweep = (a1_deg - a0_deg) % 360.0 or 360.0
    f = (lambda t: abs(math.sin(math.radians(t)))) if axis == "y" else (lambda t: abs(math.cos(math.radians(t))))
    cand = [a0, a0 + sweep] + [k * 90.0 for k in range(-4, 9) if a0 <= k * 90.0 <= a0 + sweep]
    return R * max(f(t) for t in cand)


def arc_projected_interval(R, a0_deg, a1_deg, axis="y"):
    """(low, high) of a CCW arc projected onto the plan x or y axis, about the arc centre. A drawn feature that is
    symmetric about the axis of view needs a symmetric interval (low = -high) on the axis it is projected onto."""
    if R <= 0:
        raise ElevationBindingError("radius must be positive")
    a0 = a0_deg % 360.0
    sweep = (a1_deg - a0_deg) % 360.0 or 360.0
    f = (lambda t: math.sin(math.radians(t))) if axis == "y" else (lambda t: math.cos(math.radians(t)))
    cand = [a0, a0 + sweep] + [k * 90.0 for k in range(-4, 9) if a0 <= k * 90.0 <= a0 + sweep]
    vals = [R * f(t) for t in cand]
    return min(vals), max(vals)


def binding_verdict(criteria):
    """criteria: [{"kind", "ok", "detail"}]. BOUND needs at least one satisfied IDENTITY_LABEL (the object is named in
    plan where the feature lies), DIMENSION_MATCH and FEATURE_MATCH, no failed DIMENSION / FEATURE / LEVEL criterion
    and no satisfied CONTRADICTION."""
    for c in criteria:
        if c["kind"] not in KINDS:
            raise ElevationBindingError(f"unknown criterion kind {c['kind']!r}")
    have = {k: any(c["ok"] for c in criteria if c["kind"] == k) for k in KINDS}
    failed = [c for c in criteria if c["kind"] in (DIMENSION_MATCH, FEATURE_MATCH, LEVEL_MATCH) and not c["ok"]]
    contra = [c for c in criteria if c["kind"] == CONTRADICTION and c["ok"]]
    missing = [k for k in (IDENTITY_LABEL, DIMENSION_MATCH, FEATURE_MATCH) if not have[k]]
    state = BOUND if not missing and not failed and not contra else NOT_BOUND
    return {"state": state, "missing": missing, "failed": [c["detail"] for c in failed],
            "contradictions": [c["detail"] for c in contra],
            "satisfied": sum(1 for c in criteria if c["ok"] and c["kind"] != CONTRADICTION)}


def floor_profile(profiles):
    """profiles: [{"source", "levels": [distinct floor levels the source shows, or [] when it shows none]}]. UNIFORM
    only if every source that shows the floor shows one and the same level; VARYING if every source shows the same
    several levels; PROFILE_CONFLICT if the sources disagree (one level against several, or different levels)."""
    shown = [p for p in profiles if p["levels"]]
    if not shown:
        return {"state": NOT_SHOWN, "uniform_dimension_allowed": False}
    sets = {tuple(sorted(round(v, 6) for v in p["levels"])) if all(isinstance(v, (int, float)) for v in p["levels"])
            else tuple(sorted(map(str, p["levels"]))) for p in shown}
    counts = {len(p["levels"]) for p in shown}
    if counts == {1} and len(sets) == 1:
        state = UNIFORM
    elif min(counts) > 1 and len(sets) == 1:
        state = VARYING
    else:
        state = PROFILE_CONFLICT
    return {"state": state, "uniform_dimension_allowed": state == UNIFORM,
            "sources": {p["source"]: p["levels"] for p in profiles}}
