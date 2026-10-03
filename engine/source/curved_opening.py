"""CURVED OPENING MEASUREMENT (V1) - every geometric basis of a curved (arc) glazing run is published; the
commercial basis is chosen by a versioned method or a project override, never by a benchmark.

bases()        concentric source arcs (radius, swept angle each; the sweeps may differ when the run is cut by straight
               jambs) -> INNER = developed length of the smallest-radius arc, OUTER = of the largest-radius arc, CENTRE
               = mid-band length (INNER + OUTER) / 2, CHORD = chord of the inner arc; arcs that do not share one centre
               -> NOT_CONCENTRIC (blocked).
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


def bases(arcs, *, centre_tol=1.0) -> dict:
    """arcs [{"cx", "cy", "r", "sweep_rad"}] in one unit (mm)."""
    if not arcs:
        return {"state": "NO_ARCS"}
    c0 = arcs[0]
    if any(math.hypot(a["cx"] - c0["cx"], a["cy"] - c0["cy"]) > centre_tol for a in arcs):
        return {"state": "NOT_CONCENTRIC", "arcs": len(arcs)}
    srt = sorted(arcs, key=lambda a: a["r"])
    inner, outer = srt[0], srt[-1]
    Li, Lo = inner["r"] * inner["sweep_rad"], outer["r"] * outer["sweep_rad"]
    return {"state": "COMPUTED", "radii_mm": [a["r"] for a in srt], "sweeps_rad": [a["sweep_rad"] for a in srt],
            "INNER": round(Li, 3), "CENTRE": round((Li + Lo) / 2.0, 3), "OUTER": round(Lo, 3),
            "CHORD": round(2 * inner["r"] * math.sin(inner["sweep_rad"] / 2.0), 3), "unit": "mm"}


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
