"""CURVED OPENING MEASUREMENT (V1.1) - every geometric basis of a curved (arc) glazing run is published under an
unambiguous geometric name; the commercial basis is chosen by a versioned method or a project override, never by a
benchmark.

bases()        concentric source arcs (radius, swept angle each; the sweeps may differ when the run is cut by straight
               jambs) ->
                 MIN_RADIUS_ARC  developed length of the smallest-radius arc
                 MID_BAND_ARC    mid-band length (MIN_RADIUS_ARC + MAX_RADIUS_ARC) / 2
                 MAX_RADIUS_ARC  developed length of the largest-radius arc
                 CHORD           chord of the smallest-radius arc
               aliases kept for compatibility only: INNER = MIN_RADIUS_ARC, CENTRE = MID_BAND_ARC,
               OUTER = MAX_RADIUS_ARC. Arcs that do not share one centre -> NOT_CONCENTRIC (blocked).
orient()       semantic sides, only where established: room_side in {"MIN_RADIUS", "MAX_RADIUS"} (from source
               evidence) -> ROOM_SIDE_ARC / EXTERIOR_SIDE_ARC; otherwise NOT_ESTABLISHED. MIN_RADIUS_ARC is never
               assumed to be the room side.
commercial()   METHOD URBAN_CURVED_ALUMINIUM_INNER_FACE_METHOD@v1 selects MIN_RADIUS_ARC (the geometric inner arc);
               a project override may select MIN_RADIUS / MID_BAND / MAX_RADIUS / CHORD, or ROOM_SIDE / EXTERIOR_SIDE
               when that side is established.

Project-agnostic; stdlib only.
"""

from __future__ import annotations

import math

POLICY_ID = "CURVED_OPENING_V1_1"
METHOD_ID = "URBAN_CURVED_ALUMINIUM_INNER_FACE_METHOD@v1"
GEOMETRIC = ("MIN_RADIUS_ARC", "MID_BAND_ARC", "MAX_RADIUS_ARC", "CHORD")
ALIASES = {"INNER": "MIN_RADIUS_ARC", "CENTRE": "MID_BAND_ARC", "OUTER": "MAX_RADIUS_ARC"}
BASES = GEOMETRIC                                           # the explicit names; aliases are not bases
OVERRIDES = {"MIN_RADIUS": "MIN_RADIUS_ARC", "MID_BAND": "MID_BAND_ARC", "MAX_RADIUS": "MAX_RADIUS_ARC",
             "CHORD": "CHORD", "ROOM_SIDE": "ROOM_SIDE_ARC", "EXTERIOR_SIDE": "EXTERIOR_SIDE_ARC"}
DEFAULT = "MIN_RADIUS_ARC"


def bases(arcs, *, centre_tol=1.0) -> dict:
    """arcs [{"cx", "cy", "r", "sweep_rad"}] in one unit (mm)."""
    if not arcs:
        return {"state": "NO_ARCS"}
    c0 = arcs[0]
    if any(math.hypot(a["cx"] - c0["cx"], a["cy"] - c0["cy"]) > centre_tol for a in arcs):
        return {"state": "NOT_CONCENTRIC", "arcs": len(arcs)}
    srt = sorted(arcs, key=lambda a: a["r"])
    lo, hi = srt[0], srt[-1]
    Lmin, Lmax = lo["r"] * lo["sweep_rad"], hi["r"] * hi["sweep_rad"]
    out = {"state": "COMPUTED", "radii_mm": [a["r"] for a in srt], "sweeps_rad": [a["sweep_rad"] for a in srt],
           "MIN_RADIUS_ARC": round(Lmin, 3), "MID_BAND_ARC": round((Lmin + Lmax) / 2.0, 3), "MAX_RADIUS_ARC": round(Lmax, 3),
           "CHORD": round(2 * lo["r"] * math.sin(lo["sweep_rad"] / 2.0), 3), "unit": "mm"}
    for alias, name in ALIASES.items():
        out[alias] = out[name]
    out["aliases"] = dict(ALIASES)
    return out


def orient(b: dict, room_side=None) -> dict:
    """room_side: "MIN_RADIUS" / "MAX_RADIUS" when the source establishes which face meets the room, else None."""
    if b.get("state") != "COMPUTED" or room_side not in ("MIN_RADIUS", "MAX_RADIUS"):
        return {"state": "NOT_ESTABLISHED", "ROOM_SIDE_ARC": None, "EXTERIOR_SIDE_ARC": None, "room_side": None}
    other = "MAX_RADIUS" if room_side == "MIN_RADIUS" else "MIN_RADIUS"
    return {"state": "ESTABLISHED", "room_side": room_side, "ROOM_SIDE_ARC": b[room_side + "_ARC"],
            "EXTERIOR_SIDE_ARC": b[other + "_ARC"]}


def commercial(b: dict, *, override=None, room_side=None) -> dict:
    if b.get("state") != "COMPUTED":
        return {"state": "BLOCKED", "why": b.get("state")}
    o = orient(b, room_side)
    sel, auth = DEFAULT, METHOD_ID
    if override:
        key = override.get("basis")
        if key not in OVERRIDES:
            raise ValueError("override basis must be one of " + ", ".join(OVERRIDES))
        sel, auth = OVERRIDES[key], "PROJECT_OVERRIDE " + str(override.get("id"))
        if sel in ("ROOM_SIDE_ARC", "EXTERIOR_SIDE_ARC") and o["state"] != "ESTABLISHED":
            return {"state": "BLOCKED", "why": f"override {key} needs an established room side", "orientation": o}
    length = o[sel] if sel in ("ROOM_SIDE_ARC", "EXTERIOR_SIDE_ARC") else b[sel]
    return {"state": "COMPUTED", "basis": sel, "authority": auth, "length_mm": length, "orientation": o,
            "all_bases_mm": {k: b[k] for k in GEOMETRIC}}
