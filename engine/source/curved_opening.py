"""CURVED OPENING MEASUREMENT (V1) - every geometric basis of a curved (arc) glazing run is published; the
commercial basis is chosen by a versioned method or a project override, never by a benchmark.

bases()        concentric source arcs (radius, swept angle) -> INNER (smallest radius), CENTRE (mean of the innermost
               and outermost radius), OUTER (largest radius) developed lengths and the CHORD of the inner arc; arcs that
               are not concentric or sweep different angles -> NOT_CONCENTRIC (blocked).
commercial()   METHOD URBAN_CURVED_ALUMINIUM_INNER_FACE_METHOD@v1: INNER unless a project override names another
               basis; the room side is a separate attribute (for a curve bulging into a room the room-side face is
               the OUTER arc) and never silently replaces the geometric INNER.

Project-agnostic; stdlib only.
"""

from __future__ import annotations

import math

POLICY_ID = "CURVED_OPENING_V1"
METHOD_ID = "URBAN_CURVED_ALUMINIUM_INNER_FACE_METHOD@v1"
BASES = ("INNER", "CENTRE", "OUTER", "CHORD")


def bases(arcs, *, centre_tol=1.0, angle_tol=1e-3) -> dict:
    """arcs [{"cx", "cy", "r", "sweep_rad"}] in one unit (mm)."""
    if not arcs:
        return {"state": "NO_ARCS"}
    c0 = arcs[0]
    if any(math.hypot(a["cx"] - c0["cx"], a["cy"] - c0["cy"]) > centre_tol or abs(a["sweep_rad"] - c0["sweep_rad"]) > angle_tol
           for a in arcs):
        return {"state": "NOT_CONCENTRIC", "arcs": len(arcs)}
    rs = sorted(a["r"] for a in arcs)
    th = c0["sweep_rad"]
    ri, ro = rs[0], rs[-1]
    return {"state": "COMPUTED", "sweep_rad": th, "radii_mm": rs,
            "INNER": round(ri * th, 3), "CENTRE": round((ri + ro) / 2.0 * th, 3), "OUTER": round(ro * th, 3),
            "CHORD": round(2 * ri * math.sin(th / 2.0), 3), "unit": "mm"}


def commercial(b: dict, *, override=None, room_side=None) -> dict:
    if b.get("state") != "COMPUTED":
        return {"state": "BLOCKED", "why": b.get("state")}
    basis = METHOD_ID
    sel = "INNER"
    if override:
        if override.get("basis") not in BASES:
            raise ValueError("override basis must be one of " + ", ".join(BASES))
        sel, basis = override["basis"], "PROJECT_OVERRIDE " + str(override.get("id"))
    return {"state": "COMPUTED", "basis": sel, "authority": basis, "length_mm": b[sel],
            "room_side": room_side, "all_bases_mm": {k: b[k] for k in BASES}}
