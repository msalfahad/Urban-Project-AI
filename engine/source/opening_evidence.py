"""OPENING_EVIDENCE_V2 - an opening is not one status: count, width, height, area, function and material each carry
their own evidence, and a derived attribute is never more certain than the attributes it is derived from.

    evaluate(opening) -> {count, width, height, area, function, material: {state, reason}, flags}

States: VERIFIED | PROVISIONAL | BLOCKED (and NOT_APPLICABLE).  Rules (each is a test):
  1. area = width x height -> area state = the weaker of width and height; no default height is ever inserted;
  2. count is VERIFIED when the opening object exists in source, whatever its dimensions;
  3. a WINDOW whose geometry also fits a door (sill near the floor or height >= the door threshold) is a
     GLAZED_DOOR_CANDIDATE: function BLOCKED_FUNCTION_UNRESOLVED - geometry alone never decides window vs door;
  4. material is a specification attribute: VERIFIED only from a source schedule / owner fact.
Stdlib only, project-agnostic.
"""

from __future__ import annotations

POLICY_ID = "OPENING_EVIDENCE_V2"
VERIFIED, PROVISIONAL, BLOCKED, NA = "VERIFIED", "PROVISIONAL", "BLOCKED", "NOT_APPLICABLE"
_ORDER = {VERIFIED: 0, PROVISIONAL: 1, BLOCKED: 2}
DOOR_SILL_MAX_M = 0.15
DOOR_HEIGHT_MIN_M = 2.0


def weaker(a, b):
    return a if _ORDER[a] >= _ORDER[b] else b


def evaluate(o: dict) -> dict:
    """o: {kind, exists, width_m, width_source, height_m, height_class (SOURCE | RASTER_DERIVED | PROVISIONAL |
    BLOCKED), sill_m, material_source}."""
    out, flags = {}, []
    out["count"] = (VERIFIED, "opening object in source") if o.get("exists", True) else (BLOCKED, "existence unproved")
    out["width"] = (VERIFIED, o.get("width_source") or "source closure") if o.get("width_m") else \
        (BLOCKED, "no width (closure not established)")
    hc = o.get("height_class")
    if o.get("height_m") is None or hc in (None, "BLOCKED"):
        out["height"] = (BLOCKED, "no source / raster height; no default height inserted")
    elif hc in ("SOURCE", "RASTER_DERIVED", "PRINTED", "OWNER_PROJECT_FACT"):
        out["height"] = (VERIFIED, f"height {hc}")
    else:
        out["height"] = (PROVISIONAL, f"height {hc}")
    a = weaker(out["width"][0], out["height"][0])
    out["area"] = (a, "width x height: " + {VERIFIED: "both verified", PROVISIONAL: "height provisional",
                                           BLOCKED: "width or height blocked"}[a])
    kind = o.get("kind")
    sill, h = o.get("sill_m"), o.get("height_m")
    if kind == "WINDOW" and ((sill is not None and sill < DOOR_SILL_MAX_M) or (h is not None and h >= DOOR_HEIGHT_MIN_M)):
        flags.append("GLAZED_DOOR_CANDIDATE")
        out["function"] = (BLOCKED, "BLOCKED_FUNCTION_UNRESOLVED: window or glazed door - geometry alone cannot decide")
    else:
        out["function"] = (VERIFIED, f"{kind} by source symbol / glazing role")
    out["material"] = (VERIFIED, o["material_source"]) if o.get("material_source") else \
        (PROVISIONAL, "material by specification (not in source)")
    return {"policy": POLICY_ID, **{k: {"state": v[0], "reason": v[1]} for k, v in out.items()}, "flags": flags}
