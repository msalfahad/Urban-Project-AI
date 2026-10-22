"""T-162 corners / arrises on a facade (research only, not a method, not wired): pure functions, metres in, metres out.

Corners are their own m.l line (owner notes Sigma, correction of 2026-10-22 07:10; ENGINEERING_REASONING_STANDARD
section 3): the PHYSICAL length is measured in full; the freelancer's "2 m = 1 m" is a PAYMENT convention (half the
length paid, or the full length at half the m2 rate: Urban cost PDF 1.25 KWD/m.l = half of 2.50 KWD/m2). Physical,
contract, payable, rate and amount are kept as separate figures (four_figures); nothing here ever converts m.l to m2,
and add_area_m2 refuses any item that is not in m2 (r2, after the Checker's rejection of r1 on 2026-10-22 10:20).

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


def opening_arrises(openings):
    """arrises round a list of openings, composed ONCE from opening_reveal_ml (r2: r1's caller added the two jambs a
    second time, 2 x height per opening). openings: iterable of (id, width m, height m or None, status, has_sill).
    -> {"measured": m.l with printed / inferred heights (+ head / sill of the HELD ones), "assumed": m.l on an approved
    fallback height, "held_ids": openings whose jambs are HELD, "per": {id: m.l or None}}"""
    measured = assumed = 0.0
    held, per = [], {}
    for oid, w, h, status, sill in openings:
        known, rest = opening_reveal_ml(w, h, sill)
        if rest is None:
            measured += known
            held.append(oid)
            per[oid] = None
        elif status == "ASSUMED":
            assumed += known
            per[oid] = known
        else:
            measured += known
            per[oid] = known
    return {"measured": measured, "assumed": assumed, "held_ids": held, "per": per}


URBAN_PDF_CORNER_RATE_KWD_PER_ML = 1.25      # Urban cost PDF: exterior corners 1,300 m.l x 1.25 KWD (owner notes)
URBAN_PDF_EXT_PLASTER_RATE_KWD_PER_M2 = 2.50  # Urban cost PDF: exterior plaster labour 1,500 m2 x 2.50 KWD


def four_figures(physical_ml, contract_ml=None):
    """one corner line as four separate figures, all in m.l or KWD, never m2 (standard section 3):
    physical length (full), contract measurement quantity (default: the physical length; a contract basis such as
    the freelancer's 1,297.35 is passed explicitly), payable length under the freelancer's half convention
    (comparison only, never a physical length), and the amount at the Urban PDF rate (full length x 1.25 KWD/m.l,
    which equals the half length x 2.50). A HELD physical length (None) stays None in every figure."""
    c = physical_ml if contract_ml is None else contract_ml
    return {"unit": "m.l",
            "physical_ml": physical_ml,
            "contract_ml": c,
            "payable_ml_half_convention": None if c is None else c / 2.0,
            "rate_basis": "1.25 KWD/m.l on the full length (= half of 2.50 KWD/m2)",
            "amount_kwd": None if c is None else c * URBAN_PDF_CORNER_RATE_KWD_PER_ML}


def add_area_m2(*items):
    """sum plaster surfaces: each item (quantity, unit). Refuses anything that is not m2 (a corner m.l line can never be
    added to a plaster area) and returns None (HELD) when any quantity is None, never 0."""
    tot = 0.0
    for q, unit in items:
        if unit != "m2":
            raise ValueError(f"not an area: {q} {unit} (corners stay their own m.l line)")
        if q is None:
            return None
        tot += q
    return tot


def parapet_components(outer_ml, inner_ml, t_m, h_inner_m):
    """one parapet run as its physical items (plain parapet, section with a flat top): outer top arris m.l, inner top
    arris m.l (each on its own run), top surface m2 on the centreline ((outer + inner) / 2 x t), inner face m2 (inner
    run x height above the roof slab top). The outer face is part of the facade and is not returned. A height given as
    (lo, hi) returns a range; None -> HELD (None), never 0."""
    if t_m is None or outer_ml is None or inner_ml is None:
        raise ValueError("parapet run needs outer, inner run and thickness")
    top = (outer_ml + inner_ml) / 2.0 * t_m
    if h_inner_m is None:
        face = None
    elif isinstance(h_inner_m, tuple):
        face = (inner_ml * h_inner_m[0], inner_ml * h_inner_m[1])
    else:
        face = inner_ml * h_inner_m
    return {"outer_top_arris_ml": outer_ml, "inner_top_arris_ml": inner_ml, "top_m2": top, "inner_face_m2": face}
