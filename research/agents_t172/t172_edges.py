"""T-172 (research only, not a method, not wired): parapets and wall edges as PHYSICAL components, and the four separate
figures of a corner / edge line (physical length, contract measurement quantity, payable quantity, rate basis).

ENGINEERING_REASONING_STANDARD.md sections 2.1 and 3: a parapet is not one number. It is
    two vertical faces (outer, inner)                       m2
    a top surface (plan centreline x thickness)             m2
    an outer top arris and an inner top arris               m.l   (external edges)
    stop-ends at free ends: 2 vertical arrises + top edge   m.l
    the inner base junction with the roof                   m.l   (internal angle / plaster termination, NOT an arris)
    drip, coping, upturn                                    only where the drawings or specification show them
and a corner paid at half rate is still its full physical length (section 3, first bullet).

Geometry is metres in plan. A parapet CHAIN is the ordered run of outline sides (straight or arc) that carry a parapet,
with outward normals; the inner face is the wall's roof-side face (outline offset inward by the wall thickness t),
mitred at corners, cut at each chain end by what the end does:
    ABUT  : the parapet ends against higher construction; the inner face stops at that construction's roof-side face
            (a line given as point + direction).
    FREE  : the parapet stops in the open: square end, the inner face ends opposite the outer end; the end face
            t x h has two vertical arrises (h each) and a top edge (t).
    UNKNOWN: the end condition is not established from the drawings: the inner length uses the square end and the
            stop-end arrises are HELD (a range 0 .. 2h + t), never 0 and never guessed.
    CLOSED: at both ends, for a parapet ring with no end (the last side returns to the first).
A NICHE (a recess of the outer face shallower than t between two collinear sides: return, recessed side, return) does
not move the wall's inner face; the inner face runs straight across it (the wall is one straight wall with a niche).

Stdlib only, project-agnostic, no Alsenan value in this file."""
import math

TOL = 1e-6


# ------------------------------------------------------------------------------------------------ small geometry
def _sub(a, b):
    return (a[0] - b[0], a[1] - b[1])


def _add(a, b):
    return (a[0] + b[0], a[1] + b[1])


def _mul(a, k):
    return (a[0] * k, a[1] * k)


def _dot(a, b):
    return a[0] * b[0] + a[1] * b[1]


def _cross(a, b):
    return a[0] * b[1] - a[1] * b[0]


def _len(a, b):
    return math.hypot(b[0] - a[0], b[1] - a[1])


def _unit(v):
    L = math.hypot(v[0], v[1])
    if L <= TOL:
        raise ValueError("zero-length direction")
    return (v[0] / L, v[1] / L)


def side_length(s):
    """True length of an outline side: chord for a straight side, r x sweep for an arc (never the chord)."""
    if s["kind"] == "ARC":
        return s["r"] * _sweep(s["c"], s["a"], s["b"], s["r"])
    return _len(s["a"], s["b"])


def _sweep(c, a, b, r):
    """Minor sweep between the radius vectors to a and b (outline arcs of a building are under 180 degrees here;
    a caller with a larger arc splits it)."""
    va, vb = _sub(a, c), _sub(b, c)
    ang = math.atan2(_cross(va, vb), _dot(va, vb))
    return abs(ang)


def _inner_line(s):
    """Inner offset of a straight side: (point, direction)."""
    d = _unit(_sub(s["b"], s["a"]))
    n = _unit(s["normal"])
    return (_add(s["a"], _mul(n, -s["t"])), d)


def _inner_radius(s):
    """An arc whose centre lies on the OUTSIDE (concave in plan) grows inward; a convex arc shrinks."""
    n = _unit(s["normal"])
    mid_dir = _unit(_add(_unit(_sub(s["a"], s["c"])), _unit(_sub(s["b"], s["c"]))))
    convex = _dot(mid_dir, n) > 0          # radius vector points outward -> centre inside -> convex
    r = s["r"] - s["t"] if convex else s["r"] + s["t"]
    if r <= TOL:
        raise ValueError("wall thickness not smaller than the arc radius")
    return r


def _line_line(p, d, q, e):
    den = _cross(d, e)
    if abs(den) <= 1e-9:
        return None
    k = _cross(_sub(q, p), e) / den
    return _add(p, _mul(d, k))


def _line_circle(p, d, c, r, near):
    f = _sub(p, c)
    b = _dot(f, d)
    cc = _dot(f, f) - r * r
    disc = b * b - cc
    if disc < -1e-9:
        return None
    disc = max(disc, 0.0)
    pts = [_add(p, _mul(d, -b + s * math.sqrt(disc))) for s in (1, -1)]
    return min(pts, key=lambda x: _len(x, near))


def _joint(s1, s2, outer_pt):
    """Inner point of the junction between consecutive sides s1 -> s2 (shared outer point outer_pt)."""
    k1, k2 = s1["kind"], s2["kind"]
    if k1 != "ARC" and k2 != "ARC":
        p, d = _inner_line(s1)
        q, e = _inner_line(s2)
        x = _line_line(p, d, q, e)
        if x is None:                       # collinear continuation (equal thickness): the offset point itself
            return _add(outer_pt, _mul(_unit(s1["normal"]), -s1["t"]))
        return x
    if k1 == "ARC" and k2 == "ARC":
        raise ValueError("arc-to-arc junctions are not handled here (split with a straight side)")
    arc, st = (s1, s2) if k1 == "ARC" else (s2, s1)
    r_in = _inner_radius(arc)
    p, d = _inner_line(st)
    # tangent junction: the line's offset touches the offset circle at the shared point's offset
    rad = _unit(_sub(outer_pt, arc["c"]))
    if abs(_dot(rad, _unit(_sub(st["b"], st["a"])))) <= 1e-6:
        return _add(arc["c"], _mul(rad, r_in))
    x = _line_circle(p, d, arc["c"], r_in, outer_pt)
    if x is None:
        raise ValueError("inner offset line misses the inner arc")
    return x


def _end_point(s, end, which):
    """Inner end point of the chain's first ('start') or last ('end') side."""
    outer = s["a"] if which == "start" else s["b"]
    kind = end.get("type", "UNKNOWN")
    if s["kind"] == "ARC":
        if kind == "ABUT":
            raise ValueError("an abutment on an arc end is not handled here")
        rad = _unit(_sub(outer, s["c"]))
        return _add(s["c"], _mul(rad, _inner_radius(s)))
    p, d = _inner_line(s)
    if kind == "ABUT":
        q, e = end["line"]
        x = _line_line(p, d, q, _unit(e))
        if x is None:
            raise ValueError("abutment line parallel to the parapet")
        return x
    # FREE or UNKNOWN: square end, opposite the outer end point
    return _add(outer, _mul(_unit(s["normal"]), -s["t"]))


def _merge_niches(sides):
    """Replace (side, return, recessed side, return, side) groups whose recess is shallower than t by one virtual
    straight side for the INNER computation only. Returns (virtual sides, list of merged index groups)."""
    out, groups, i = [], [], 0
    while i < len(sides):
        if i + 4 < len(sides):
            s1, r1, m, r2, s2 = sides[i:i + 5]
            if all(x["kind"] == "STRAIGHT" for x in (s1, r1, m, r2, s2)):
                d1 = _unit(_sub(s1["b"], s1["a"]))
                d2 = _unit(_sub(s2["b"], s2["a"]))
                dm = _unit(_sub(m["b"], m["a"]))
                depth = side_length(r1)
                collinear = abs(_cross(d1, d2)) <= 1e-6 and abs(_cross(_sub(s2["a"], s1["a"]), d1)) <= 1e-4
                if (collinear and abs(_cross(d1, dm)) <= 1e-6 and depth < s1["t"] - TOL
                        and abs(side_length(r2) - depth) <= 1e-4 and s1["t"] == s2["t"]):
                    v = dict(s1)
                    v["b"] = s2["b"]
                    out.append(v)
                    groups.append(list(range(i, i + 5)))
                    i += 5
                    continue
        out.append(sides[i])
        i += 1
    return out, groups


def inner_runs(sides, start, end):
    """Inner face length of each (virtual) side of a parapet chain. sides: ordered outline sides with keys kind,
    a, b, normal (outward), t, and for arcs c, r. start / end: {"type": "ABUT", "line": (point, direction)} |
    {"type": "FREE"} | {"type": "UNKNOWN"}. Returns {"inner_m": total, "parts": [(names, inner length)],
    "niches": merged groups}."""
    if not sides:
        raise ValueError("empty chain")
    for s in sides:
        if s.get("t") is None or s["t"] <= 0:
            raise ValueError("wall thickness missing on side %s: HELD, never assumed" % s.get("name"))
    vs, groups = _merge_niches(sides)
    closed = start.get("type") == "CLOSED"
    if closed != (end.get("type") == "CLOSED"):
        raise ValueError("a closed ring has CLOSED at both ends")
    if closed:
        if _len(vs[-1]["b"], vs[0]["a"]) > 1e-4:
            raise ValueError("CLOSED chain does not return to its start")
        j0 = _joint(vs[-1], vs[0], vs[0]["a"])
        pts = [j0]
    else:
        pts = [_end_point(vs[0], start, "start")]
    for k in range(len(vs) - 1):
        pts.append(_joint(vs[k], vs[k + 1], vs[k]["b"]))
    pts.append(j0 if closed else _end_point(vs[-1], end, "end"))
    parts = []
    for k, s in enumerate(vs):
        p, q = pts[k], pts[k + 1]
        if s["kind"] == "ARC":
            L = _inner_radius(s) * _sweep(s["c"], p, q, None)
        else:
            d = _unit(_sub(s["b"], s["a"]))
            L = _dot(_sub(q, p), d)
            if L < -1e-6:
                raise ValueError("inner face of side %s has negative length" % s.get("name"))
        parts.append((s.get("name"), round(L, 6)))
    # inner length per ORIGINAL side: a niche group's straight inner face is split at the positions of its sides
    # along the wall (the returns get 0: the inner face does not follow them)
    by_side = []
    gi = {g[0]: g for g in groups}
    k = i = 0
    while i < len(sides):
        if i in gi:
            g = gi[i]
            s1, r1, m, r2, s2 = (sides[j] for j in g)
            d = _unit(_sub(s1["b"], s1["a"]))
            p, q = pts[k], pts[k + 1]
            l1 = _dot(_sub(s1["b"], p), d)
            lm = _dot(_sub(m["b"], m["a"]), d)
            l2 = _dot(_sub(q, s2["a"]), d)
            by_side += [(s1.get("name"), round(l1, 6)), (r1.get("name"), 0.0), (m.get("name"), round(lm, 6)),
                        (r2.get("name"), 0.0), (s2.get("name"), round(l2, 6))]
            i += 5
        else:
            by_side.append((sides[i].get("name"), parts[k][1]))
            i += 1
        k += 1
    return {"inner_m": round(sum(L for _, L in parts), 6), "parts": parts, "by_side": by_side, "niches": groups}


# ------------------------------------------------------------------------------------------------ components
def parapet_components(sides, start, end, height_of):
    """Physical components of one parapet chain.
    height_of(side) -> float | ("HELD", lo, hi)  : parapet height above the roof slab top on that side.
    Areas use the outer length for the outer face and the inner length for the inner face; the top surface uses the
    mean of both (plan centreline) x t. A HELD height makes the dependent areas HELD (a range), never 0."""
    outer = [(s.get("name"), side_length(s)) for s in sides]
    L_out = sum(L for _, L in outer)
    inn = inner_runs(sides, start, end)
    L_in = inn["inner_m"]
    inner_by_side = inn["by_side"]
    of_lo = of_hi = 0.0
    if_lo = if_hi = 0.0
    held = []
    for s in sides:
        h = height_of(s)
        Ls = side_length(s)
        if isinstance(h, tuple):
            held.append(s.get("name"))
            lo, hi = h[1], h[2]
        else:
            lo = hi = h
        of_lo += Ls * lo
        of_hi += Ls * hi
    # inner faces: each original side's share of the inner face at that side's own parapet height
    for s, (_nm, Li) in zip(sides, inner_by_side):
        if Li <= 0:
            continue
        h = height_of(s)
        lo, hi = (h[1], h[2]) if isinstance(h, tuple) else (h, h)
        if_lo += Li * lo
        if_hi += Li * hi
    t_mean = sum(side_length(s) * s["t"] for s in sides) / L_out
    stop = []
    for tag, e, s in (("start", start, sides[0]), ("end", end, sides[-1])):
        h = height_of(s)
        lo, hi = (h[1], h[2]) if isinstance(h, tuple) else (h, h)
        if e.get("type") == "FREE":
            stop.append({"end": tag, "status": "DRAWING-CONFIRMED" if not isinstance(h, tuple) else "HELD",
                         "vertical_ml": (2 * lo, 2 * hi), "top_ml": s["t"]})
        elif e.get("type") == "UNKNOWN":
            stop.append({"end": tag, "status": "HELD", "vertical_ml": (0.0, 2 * hi), "top_ml": (0.0, s["t"])})
    r6 = lambda x: round(x, 6)                                              # noqa: E731
    return {
        "outer_top_arris_ml": r6(L_out),
        "inner_top_arris_ml": r6(L_in),
        "inner_base_junction_ml": r6(L_in),      # internal angle at the roof: a termination, not an external arris
        "top_surface_m2": r6((L_out + L_in) / 2.0 * t_mean),
        "outer_face_m2": (r6(of_lo), r6(of_hi)),
        "inner_face_m2": (r6(if_lo), r6(if_hi)),
        "held_height_sides": held,
        "stop_ends": stop,
        "inner_parts": inn["parts"],
        "inner_by_side": inner_by_side,
        "niches": inn["niches"],
        "t_mean_m": r6(t_mean),
    }


def edges_per_metre(components):
    """External arrises a plain rectangular parapet physically has per metre of its outer run (outer + inner top
    arris), the comparison a '2 or 3 lines per metre' convention has to be held against."""
    return round((components["outer_top_arris_ml"] + components["inner_top_arris_ml"])
                 / components["outer_top_arris_ml"], 6)


# ------------------------------------------------------------------------------------------------ vertical corners
def vertical_corner_ml(band_a, band_b):
    """Length of an external vertical arris where two faces meet: the overlap of their vertical bands
    (bottom, top in metres). A band edge None -> HELD (returns None), never 0."""
    if None in band_a or None in band_b:
        return None
    return round(max(0.0, min(band_a[1], band_b[1]) - max(band_a[0], band_b[0])), 6)


def turn_is_convex(s1, s2):
    """True when the outline turns so that the junction s1 -> s2 is an external arris (convex corner). The outline
    orientation is read from s1's outward normal (right-hand of travel = clockwise outline), so the same call works
    for a mirrored drawing."""
    d1 = _unit(_sub(s1["b"], s1["a"]))
    d2 = _unit(_sub(s2["b"], s2["a"]))
    n1 = _unit(s1["normal"])
    turn = _cross(d1, d2)
    if abs(turn) <= 1e-9:
        return False
    # orientation: outward normal on the LEFT of travel -> the interior is on the right -> clockwise outline
    left = (-d1[1], d1[0])
    cw = _dot(left, n1) > 0
    # clockwise outline: a right turn (turn < 0) is convex; anticlockwise: a left turn
    return turn < 0 if cw else turn > 0


# ------------------------------------------------------------------------------------------------ four figures
def four_figures(physical_ml, contract_ml, payable_factor, rate_qty_ml=None, rate_per_ml=None,
                 equiv_rate_per_payable=None):
    """Keep physical length, contract measurement quantity, payable quantity and the rate basis apart
    (ENGINEERING_REASONING_STANDARD section 3). payable_factor applies to the CONTRACT quantity only; the physical
    length is never derived from, nor changed by, a payment convention."""
    if physical_ml is not None and physical_ml < 0:
        raise ValueError("negative physical length")
    payable = None if contract_ml is None else round(contract_ml * payable_factor, 6)
    out = {"physical_ml": physical_ml, "contract_ml": contract_ml, "payable_factor": payable_factor,
           "payable_ml": payable}
    if rate_qty_ml is not None and rate_per_ml is not None:
        out["rate_basis_amount"] = round(rate_qty_ml * rate_per_ml, 6)
    if payable is not None and equiv_rate_per_payable is not None:
        out["payable_amount_at_equiv_rate"] = round(payable * equiv_rate_per_payable, 6)
    return out


# ------------------------------------------------------------------------------------------------ workbook cells
def decode_cell(value, length, height, max_n=4, tol=0.0051):
    """Small non-negative integer combinations a x length + b x height that reproduce a workbook cell. Evidence of a
    counting convention, never proof of a physical item: the caller labels a match 'consistent with', not 'is'."""
    sols = []
    if value is None:
        return sols
    for a in range(max_n + 1):
        for b in range(max_n * 4 + 1):
            if a == 0 and b == 0:
                continue
            v = a * (length or 0.0) + b * (height or 0.0)
            if abs(v - value) <= tol:
                sols.append((a, b))
    return sols
