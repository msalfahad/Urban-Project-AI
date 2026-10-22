"""T-162 corners / arrises on a facade (research only, not a method, not wired): pure functions, metres in, metres out.

Owner item 2 (notes 2026-10-21, FLAGGED, not a rule): corners are measured in metres run (m.l) and shown both ways,
the m.l figure and the freelancer's practice "2 m.l = 1 m2" as a comparison only. Nothing here converts corners into
area for a quantity: the owner decides.

What is measured:
  1. VERTICAL corners where two faces of one floor's outline meet. Walking the closed outline, the turn at each
     junction of two sides is CONVEX (an external arris: plaster bead / corner work) or CONCAVE (an internal angle).
     A junction whose two tangents agree within TANGENT_TOL_DEG (a straight run, or an arc that leaves a straight
     side tangentially) is NOT a corner. A dropped edge (a passage mouth, owner Q-67 A) is not a face: each of its
     two ends is a free wall end turning into the passage, recorded as a CONVEX corner of kind MOUTH_END.
     The height of a corner is where BOTH faces exist: min(top_i, top_j) - max(bottom_i, bottom_j), from the levels
     the caller gives for each side at that junction; an unknown level -> the corner is HELD (None), never 0.
  2. HORIZONTAL arrises the caller lists: the top edge of a parapet (outer face), opening reveals (head, jambs,
     sill), slab edges over open air. These carry their own length and status.

The caller supplies levels; nothing here knows a villa. Tested by check_t162.py on a hand-calculated non-Alsenan box."""
import math

TANGENT_TOL_DEG = 1.0


def _unit(v):
    L = math.hypot(v[0], v[1])
    return (v[0] / L, v[1] / L) if L > 0 else (0.0, 0.0)


def arc_sign(e):
    """+1 when the arc edge e runs counter-clockwise about its centre from a to b, -1 clockwise (the sweep is its true
    length / radius; the sense is the one whose angular travel matches that sweep)."""
    c, r = e["c"], e["r"]
    a0 = math.atan2(e["a"][1] - c[1], e["a"][0] - c[0])
    a1 = math.atan2(e["b"][1] - c[1], e["b"][0] - c[0])
    sweep = e["len_m"] / r
    d = (a1 - a0) % (2 * math.pi)
    return 1.0 if abs(d - sweep) <= abs((2 * math.pi - d) - sweep) else -1.0


def tangent(e, at_end):
    """unit direction of travel of edge e at its start (at_end False) or its end (True)."""
    if e["straight"]:
        return _unit((e["b"][0] - e["a"][0], e["b"][1] - e["a"][1]))
    p = e["b"] if at_end else e["a"]
    rx, ry = p[0] - e["c"][0], p[1] - e["c"][1]
    s = arc_sign(e)
    return _unit((-ry * s, rx * s))


def signed_area(edges):
    s = 0.0
    for e in edges:
        s += e["a"][0] * e["b"][1] - e["b"][0] * e["a"][1]
    return s / 2.0


def turn(edges, i, j):
    """signed turn (degrees, left positive) from the end of edge i to the start of edge j."""
    t1, t2 = tangent(edges[i], True), tangent(edges[j], False)
    cr = t1[0] * t2[1] - t1[1] * t2[0]
    dt = t1[0] * t2[0] + t1[1] * t2[1]
    return math.degrees(math.atan2(cr, dt))


def ring_corners(edges, drop=()):
    """every corner of one closed outline (edges in walking order, each ending where the next starts).
    -> [{"at": point, "prev": edge index, "next": edge index, "kind": CONVEX | CONCAVE | MOUTH_END, "turn_deg"}]
    Junctions inside a straight run or at a tangent arc are not corners. A dropped edge gives two MOUTH_END corners
    (its ends) and no corner across it."""
    n = len(edges)
    if n < 3:
        return []
    ccw = signed_area(edges) > 0
    drop = set(drop)
    out = []
    for i in range(n):
        j = (i + 1) % n
        if i in drop and j in drop:
            continue
        if i in drop or j in drop:
            out.append({"at": edges[i]["b"], "prev": i, "next": j, "kind": "MOUTH_END", "turn_deg": None})
            continue
        t = turn(edges, i, j)
        if abs(t) <= TANGENT_TOL_DEG:
            continue
        convex = (t > 0) == ccw
        out.append({"at": edges[i]["b"], "prev": i, "next": j, "kind": "CONVEX" if convex else "CONCAVE",
                    "turn_deg": round(t, 4)})
    return out


def corner_height(band_i, band_j):
    """height over which both faces exist: band = (bottom, top) of each side at the junction, a level None if unknown.
    -> metres, or None (HELD) when any level is unknown; a negative overlap raises (inconsistent input)."""
    if band_i is None or band_j is None or None in band_i or None in band_j:
        return None
    lo, hi = max(band_i[0], band_j[0]), min(band_i[1], band_j[1])
    if hi < lo - 1e-9:
        raise ValueError("faces at a corner do not overlap in height")
    return max(0.0, hi - lo)


def opening_reveal_ml(width_m, height_m, has_sill):
    """arrises round one opening on a face: head + two jambs (+ sill for a window). Height unknown -> (known part,
    None): the head (and sill) are known from the width, the jambs are HELD."""
    known = width_m * (2 if has_sill else 1)
    if height_m is None:
        return known, None
    return known + 2 * height_m, 0.0


def both_ways(ml):
    """the m.l figure and the freelancer's practice 2 m.l = 1 m2 (comparison only, not a rule)."""
    return {"ml": ml, "freelancer_m2_equiv": None if ml is None else ml / 2.0}
