"""Physical-geometry readers and comparators for R8.0.

The acceptance target is WHERE THE CURVE IS in WCS, not how it is written.
Start/end angles, determinant, rotation field and bulge sign are
representations; they are never compared here. Every engine's output is first
turned into physical points:

    ARC   : CENTER, START_POINT, MID_SWEEP_POINT, END_POINT, SWEEP_DIRECTION
    BULGE : VERTEX_A, ARC_MIDPOINT, VERTEX_B, SIDE_OF_CHORD, SWEEP_DIRECTION

GEOMETRY_TRUTH_TOL_MM is the comparison tolerance for SYNTHETIC fixtures with
exact inputs: one nanometre, far above float64 noise at these magnitudes
(~1e-12 mm) and far below any drafting precision. It is not an R8
reconciliation tolerance and no real project informed it.
"""

from __future__ import annotations

import math

GEOMETRY_TRUTH_TOL_MM = 1e-6


def close(p, q, tol=GEOMETRY_TRUTH_TOL_MM):
    return p is not None and q is not None and math.hypot(p[0] - q[0], p[1] - q[1]) <= tol


def cross(o, a, b):
    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])


def side_of_chord(a, b, m):
    c = cross(a, b, m)
    return "LEFT" if c > 0 else "RIGHT" if c < 0 else "ON_CHORD"


def ccw_arc_points(c, r, sa, ea):
    """Physical points of an arc written CCW from sa to ea (radians)."""
    sweep = (ea - sa) % (2 * math.pi)
    if sweep == 0:
        sweep = 2 * math.pi
    pt = lambda a: (c[0] + r * math.cos(a), c[1] + r * math.sin(a))
    return pt(sa), pt(sa + sweep / 2.0), pt(ea)


def orientation_of(p0, pm, p1, centre):
    """CCW if travelling p0 -> pm -> p1 turns counter-clockwise about centre."""
    a0 = math.atan2(p0[1] - centre[1], p0[0] - centre[0])
    am = math.atan2(pm[1] - centre[1], pm[0] - centre[0])
    a1 = math.atan2(p1[1] - centre[1], p1[0] - centre[0])
    d_m = (am - a0) % (2 * math.pi)
    d_1 = (a1 - a0) % (2 * math.pi)
    return "CCW" if d_m < d_1 else "CW"


# ----------------------------------------------------------- comparators

def compare_arc(truth, got):
    """Field-by-field physical comparison. `got` is an oriented traversal
    {CENTER, P0, PM, P1, DIR} as the engine represents it."""
    out = {}
    ends = (got["P0"], got["P1"])
    out["CENTER"] = close(truth["CENTER"], got["CENTER"])
    out["START_POINT"] = any(close(truth["START_POINT"], e) for e in ends)
    out["END_POINT"] = any(close(truth["END_POINT"], e) for e in ends)
    out["MID_SWEEP_POINT"] = close(truth["MID_SWEEP_POINT"], got["PM"])
    if close(truth["START_POINT"], got["P0"]):
        implied = got["DIR"]
    elif close(truth["START_POINT"], got["P1"]):
        implied = {"CCW": "CW", "CW": "CCW"}[got["DIR"]]
    else:
        implied = "INCONSISTENT"
    out["SWEEP_DIRECTION"] = implied == truth["SWEEP_DIRECTION"]
    if "RADIUS" in truth and got.get("RADIUS") is not None:
        out["RADIUS"] = abs(truth["RADIUS"] - got["RADIUS"]) <= GEOMETRY_TRUTH_TOL_MM
    return out


def compare_bulge(truth, got):
    """`got` = {VERTEX_A, VERTEX_B, ARC_MIDPOINT, CENTER, DIR_A_TO_B}."""
    out = {"VERTEX_A": close(truth["VERTEX_A"], got["VERTEX_A"]),
           "VERTEX_B": close(truth["VERTEX_B"], got["VERTEX_B"]),
           "ARC_MIDPOINT": close(truth["ARC_MIDPOINT"], got["ARC_MIDPOINT"]),
           "CENTER": close(truth["CENTER"], got["CENTER"])}
    out["SIDE_OF_CHORD"] = side_of_chord(got["VERTEX_A"], got["VERTEX_B"], got["ARC_MIDPOINT"]) == truth["SIDE_OF_CHORD"]
    out["SWEEP_DIRECTION"] = got["DIR_A_TO_B"] == truth["SWEEP_DIRECTION"]
    return out


def compare_segment(truth, got):
    a, b = truth["A"], truth["B"]
    ok = (close(a, got[0]) and close(b, got[1])) or (close(a, got[1]) and close(b, got[0]))
    return {"SEGMENT": ok}


def failed_fields(result):
    return sorted(k for k, v in result.items() if not v)


# ------------------------------------------- reader: current cad_adapter

def current_normalize(decode):
    from engine.cad_adapter import normalize
    return normalize(decode, source_file="r8_0_synthetic", source_hash="r8_0")


def current_realised(decode):
    """Current Urban output turned into physical points (no fixes applied)."""
    nd = current_normalize(decode)
    arcs, bulges, segs = [], [], []
    for p in nd.primitives:
        if p.kind == "ARC":
            c = (p.cx, p.cy)
            s, m, e = ccw_arc_points(c, p.radius, p.start_angle, p.end_angle)
            if p.provenance.entity_type == "77":
                a, b = (p.x1, p.y1), (p.x2, p.y2)
                if close(a, s):
                    d = "CCW"
                elif close(a, e):
                    d = "CW"
                else:
                    d = "INCONSISTENT"
                bulges.append({"VERTEX_A": a, "VERTEX_B": b, "ARC_MIDPOINT": m,
                               "CENTER": c, "DIR_A_TO_B": d})
            else:
                arcs.append({"CENTER": c, "P0": s, "PM": m, "P1": e, "DIR": "CCW", "RADIUS": p.radius})
        elif p.kind == "SEGMENT":
            segs.append(((p.x1, p.y1), (p.x2, p.y2)))
    return {"arcs": arcs, "bulges": bulges, "segments": segs, "normalized": nd}


def match_segment_sets(truth_segs, got_segs, tol=GEOMETRY_TRUTH_TOL_MM):
    """One-to-one tolerant matching of two segment multisets (end order free).

    Returns (matched, missing_from_got, unexpected_in_got)."""
    left = list(got_segs)
    missing = []
    for t in truth_segs:
        hit = None
        for i, g in enumerate(left):
            if (close(t[0], g[0], tol) and close(t[1], g[1], tol)) or \
               (close(t[0], g[1], tol) and close(t[1], g[0], tol)):
                hit = i
                break
        if hit is None:
            missing.append(t)
        else:
            left.pop(hit)
    return (not missing and not left), missing, left
