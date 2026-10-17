"""OPENING AUTHORITY (V1) - existence, geometry, function, material and vertical extent of an opening are separate
facts with separate authority; function is never promoted silently.

classify()        evidence -> FUNCTION:
                    DOOR                      door evidence in the opening: a swing / leaf / sliding-leaf motif or a
                                              door block bound to it
                    WINDOW_CANDIDATE          linear glazing in a wall gap and no door geometry
                    GLAZED_OPENING (UNKNOWN)  glazing without door geometry but with an ambiguity flag (e.g. the
                                              opening joins two interior spaces, or door and window evidence conflict)
                  swing_closes_on_opening() is the generic door test: a door-layer arc hinged at one jamb whose
                  radius is the opening width and whose free end lands on the other jamb.
                  A previously published WINDOW whose function is now UNKNOWN is a FUNCTION_DEMOTION (reported);
                  UNKNOWN is never published as WINDOW.
resolve_height()  hierarchy: SOURCE_DIMENSION > SECTION_ELEVATION > PROJECT_OWNER_FACT > URBAN_FALLBACK_BY_TYPE >
                  BLOCKED. A fallback needs a known function (no fallback for UNKNOWN) and a versioned method id;
                  never one global number.

Project-agnostic; stdlib only.
"""

from __future__ import annotations

import hashlib
import json

POLICY_ID = "OPENING_AUTHORITY_V1"
DOOR, WINDOW, UNKNOWN = "DOOR", "WINDOW_CANDIDATE", "GLAZED_OPENING_FUNCTION_UNKNOWN"
HEIGHT_ORDER = ("SOURCE_DIMENSION", "SECTION_ELEVATION", "PROJECT_OWNER_FACT", "URBAN_FALLBACK_BY_TYPE")


def classify(opening: dict) -> dict:
    """opening {"id", "existence", "width_mm", "glazing": bool, "door_evidence": [..], "ambiguity": [..],
    "previous_function"?}."""
    door = list(opening.get("door_evidence") or [])
    amb = list(opening.get("ambiguity") or [])
    if door:
        fn, why = DOOR, "door evidence: " + "; ".join(door)
    elif opening.get("glazing") and amb:
        fn, why = UNKNOWN, "glazing without door geometry; ambiguous: " + "; ".join(amb)
    elif opening.get("glazing"):
        fn, why = WINDOW, "linear glazing in a wall gap without door geometry"
    else:
        fn, why = UNKNOWN, "no glazing and no door evidence"
    prev = opening.get("previous_function")
    change = None
    if prev and prev != fn:
        change = "FUNCTION_DEMOTION" if fn == UNKNOWN else "FUNCTION_CHANGE"
    return {"id": opening["id"], "existence": opening.get("existence"), "geometry": {"width_mm": opening.get("width_mm")},
            "function": fn, "function_basis": why, "material": opening.get("material", "BLOCKED_MATERIAL"),
            "vertical_extent": None, "previous_function": prev, "function_change": change}


def swing_closes_on_opening(arc, jamb_a, jamb_b, *, width_tol=0.10, end_tol) -> bool:
    """arc {"cx", "cy", "r", "a0", "a1"} (radians); jamb_a / jamb_b the two jamb points of the opening line. True when
    the arc is hinged at one jamb (centre within end_tol), its radius is the opening width (+- width_tol) and one of
    its end points lands on the other jamb (within end_tol)."""
    import math
    w = math.hypot(jamb_b[0] - jamb_a[0], jamb_b[1] - jamb_a[1])
    if w <= 0 or abs(arc["r"] - w) > width_tol * w:
        return False
    ends = [(arc["cx"] + arc["r"] * math.cos(a), arc["cy"] + arc["r"] * math.sin(a)) for a in (arc["a0"], arc["a1"])]
    for hinge, other in ((jamb_a, jamb_b), (jamb_b, jamb_a)):
        if math.hypot(arc["cx"] - hinge[0], arc["cy"] - hinge[1]) <= end_tol and \
                any(math.hypot(e[0] - other[0], e[1] - other[1]) <= end_tol for e in ends):
            return True
    return False


def resolve_height(candidates, *, function) -> dict:
    """candidates [{"authority", "value_m", "ref"}] -> the highest authority present."""
    by = {}
    for c in candidates:
        if c.get("value_m") is None or c.get("authority") not in HEIGHT_ORDER:
            continue
        if c["authority"] == "URBAN_FALLBACK_BY_TYPE" and (function == UNKNOWN or not c.get("method_id")):
            continue
        by.setdefault(c["authority"], []).append(c)
    for a in HEIGHT_ORDER:
        if a in by:
            vals = sorted({round(c["value_m"], 6) for c in by[a]})
            if len(vals) > 1:
                return {"state": "SOURCE_CONFLICT", "authority": a, "values_m": vals, "height_m": None}
            alt = [{"authority": b, "values_m": sorted({c["value_m"] for c in by[b]})} for b in HEIGHT_ORDER if b in by and b != a]
            return {"state": "RESOLVED", "authority": a, "height_m": vals[0], "refs": [c.get("ref") for c in by[a]],
                    "outranked": alt}
    return {"state": "BLOCKED_HEIGHT", "authority": None, "height_m": None,
            "why": "no source / section / owner value; no fallback for function " + str(function)}


def policy_record() -> dict:
    rec = {"policy_id": POLICY_ID, "functions": [DOOR, WINDOW, UNKNOWN], "height_order": list(HEIGHT_ORDER),
           "never": ["UNKNOWN published as WINDOW", "one global opening height", "a fallback height for UNKNOWN"]}
    rec["digest"] = hashlib.sha256(json.dumps(rec, sort_keys=True).encode()).hexdigest()
    return rec
