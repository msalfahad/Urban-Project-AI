"""CORNER BEAD GEOMETRY (V3b) - steel plaster angle beads as segments at exposed plaster edges.

    segments(openings, corners, method) -> [segment]

An opening has two faces (the two sides of its host wall); each face has a plaster interval [z0, z1] (m above the
finished floor of the face) or None when that face is not plastered (tiled full height, stone-clad, fair-faced...).
Edges of an opening on a face:
    JAMB x 2 (vertical, sill -> head), HEAD (horizontal, width), SILL (horizontal, width; windows only, when the
    method includes window sills); a door has no floor edge.
A vertical edge receives a bead over its overlap with the face's plaster interval; a horizontal edge receives a bead
when its level lies inside the plaster interval. External / exposed corners: [{"id", "z0", "z1", "faces": [plaster
interval of face 1, of face 2]}] - a corner receives a bead over the overlap of the corner with BOTH faces' plaster
(a corner with one tiled face is a tile trim, never a plaster bead).
Every segment: HOST, EDGE_TYPE, FACE, LENGTH_M, SOURCE, FINISH_POPULATION, STATUS. Height or plaster interval unknown
-> the segment is emitted with LENGTH_M None and STATUS BLOCKED (never zero, never guessed here).
Stdlib only, project-agnostic.
"""

from __future__ import annotations

import hashlib
import json

POLICY_ID = "CORNER_BEAD_GEOMETRY_V1"
DEFAULT_METHOD = {"window_sill": True, "door_head": True, "window_head": True}


def _overlap(a0, a1, b0, b1):
    return max(0.0, min(a1, b1) - max(a0, b0))


def segments(openings, corners=(), method=None) -> list:
    m = dict(DEFAULT_METHOD, **(method or {}))
    out = []
    for o in sorted(openings, key=lambda x: str(x["id"])):
        kind = o["kind"]
        w, h, sill = o.get("width_m"), o.get("height_m"), o.get("sill_m", 0.0)
        for fi, face in enumerate(o.get("faces") or []):
            fid = face.get("face") or f"F{fi + 1}"
            pz = face.get("plaster")
            pop = face.get("finish_population")
            base = {"host": o["id"], "face": fid, "source": o.get("source"), "finish_population": pop}
            if pz is None:
                continue                                   # face not plastered: no bead
            if h is None or w is None:
                for et in ("JAMB", "JAMB", "HEAD") + (("SILL",) if kind == "WINDOW" and m["window_sill"] else ()):
                    out.append({**base, "edge_type": f"{kind}_{et}", "length_m": None, "status": "BLOCKED",
                                "why": "opening height / width unknown"})
                continue
            z0, z1 = pz
            head = sill + h
            jl = _overlap(sill, head, z0, z1)
            for side in ("L", "R"):
                if jl > 0:
                    out.append({**base, "edge_type": f"{kind}_JAMB", "side": side, "length_m": jl, "status": "MEASURED"})
            if (kind != "WINDOW" and m["door_head"] or kind == "WINDOW" and m["window_head"]) and z0 <= head <= z1:
                out.append({**base, "edge_type": f"{kind}_HEAD", "length_m": w, "status": "MEASURED"})
            if kind == "WINDOW" and m["window_sill"] and sill > 0 and z0 <= sill <= z1:
                out.append({**base, "edge_type": "WINDOW_SILL", "length_m": w, "status": "MEASURED"})
    for c in sorted(corners, key=lambda x: str(x["id"])):
        f1, f2 = (c.get("faces") or [None, None])[:2]
        base = {"host": c["id"], "face": "CORNER", "source": c.get("source"),
                "finish_population": c.get("finish_population"), "edge_type": "EXTERNAL_CORNER"}
        if c.get("z0") is None or c.get("z1") is None:
            out.append({**base, "length_m": None, "status": "BLOCKED", "why": "corner height unknown"})
            continue
        if f1 is None or f2 is None:
            continue
        lo = max(c["z0"], f1[0], f2[0])
        hi = min(c["z1"], f1[1], f2[1])
        if hi > lo:
            out.append({**base, "length_m": hi - lo, "status": "MEASURED"})
    return out


def total(segs) -> dict:
    meas = [s for s in segs if s["status"] == "MEASURED"]
    by = {}
    for s in meas:
        by[s["edge_type"]] = by.get(s["edge_type"], 0.0) + s["length_m"]
    return {"measured_lm": sum(s["length_m"] for s in meas), "blocked_segments": sum(1 for s in segs
                                                                                    if s["status"] == "BLOCKED"),
            "by_edge_type": dict(sorted(by.items())), "segments": len(segs)}


def policy_record() -> dict:
    rec = {"policy_id": POLICY_ID, "default_method": DEFAULT_METHOD,
           "rule": "bead on every opening edge of a plastered face (jambs over the plaster interval, head / sill inside "
                   "it) and on external corners plastered on both faces",
           "never": ["a bead on a tiled / clad / unplastered face", "a door floor edge", "a guessed opening height"]}
    rec["digest"] = hashlib.sha256(json.dumps(rec, sort_keys=True).encode()).hexdigest()
    return rec
