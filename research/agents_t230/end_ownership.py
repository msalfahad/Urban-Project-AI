"""T-230 END_OWNERSHIP_V1 (research, unwired, stdlib only): strap and ground-beam (tie-beam) ends into footings, necks
and walls, every intersection volume owned once.

Physical elements (ST7757 p.13 typical isolated-footing detail; T-206 / T-214 level chain; T-174 straps; T-205 necks):

- FOOTING: a slab of thickness H on the printed underlay; its soffit = formation + 0.17 (T-206, every type).
- NECK: the column between the footing top and the ground-beam top, billed through at its full printed section
  (T-205: ground beams are billed net of the column footprint, the neck owns that junction).
- STRAP: a beam B x D cast between two footings along its axis (Q-74: concrete at the axis length between the faces).
  Its level against the footings is printed nowhere (T-174): the strap soffit is a single unknown `e` per strap
  (height of the strap soffit above the footing soffit; one straight member of one printed section, so one value
  for both ends when the two footings share one soffit level).
- GROUND BEAM (tie beam): B x D at slab level (top = GF structural slab top), framing into necks or walls.

Ownership (R-CONC-OWN-1, T-189): the element billed THROUGH the junction at full section owns the intersection; the
other is measured net. A plan overlap is never an intersection unless the solids overlap in 3-D (Q-62).

Functions return plain dicts. Missing input never becomes 0: it returns status HELD with the missing item named.
"""
from __future__ import annotations

import math

POLICY_ID = "END_OWNERSHIP_V1"
DEFAULT_GUARD_CLASS = "UNWIRED_PRODUCER"   # research module: no released or candidate method imports it
TOL = 1e-9

DRAWING_CONFIRMED = "DRAWING-CONFIRMED"
HELD = "HELD"
CONFLICT = "CONFLICT"


class EndError(ValueError):
    pass


# ------------------------------------------------------------------------------------------------ plan geometry
def area(poly):
    s = 0.0
    for i in range(len(poly)):
        x0, y0 = poly[i]
        x1, y1 = poly[(i + 1) % len(poly)]
        s += x0 * y1 - x1 * y0
    return abs(s) / 2.0


def _ccw(poly):
    s = 0.0
    for i in range(len(poly)):
        x0, y0 = poly[i]
        x1, y1 = poly[(i + 1) % len(poly)]
        s += x0 * y1 - x1 * y0
    return poly if s > 0 else list(reversed(poly))


def clip_convex(subject, clip):
    """Sutherland-Hodgman: subject polygon clipped by a CONVEX clip polygon (both lists of (x, y))."""
    clip = _ccw([tuple(map(float, p)) for p in clip])
    out = [tuple(map(float, p)) for p in subject]
    for i in range(len(clip)):
        a, b = clip[i], clip[(i + 1) % len(clip)]
        inp, out = out, []
        if not inp:
            break

        def side(p):
            return (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0])

        for j in range(len(inp)):
            p, q = inp[j], inp[(j + 1) % len(inp)]
            sp, sq = side(p), side(q)
            if sp >= -TOL:
                out.append(p)
            if (sp >= -TOL) != (sq >= -TOL):
                t = sp / (sp - sq)
                out.append((p[0] + t * (q[0] - p[0]), p[1] + t * (q[1] - p[1])))
    return out


def overlap_area(a, b):
    """Plan area of the intersection of two convex polygons."""
    c = clip_convex(a, b)
    return area(c) if len(c) >= 3 else 0.0


def strip(p0, p1, width):
    """Rectangle of `width` centred on the segment p0 -> p1 (a beam strip in plan)."""
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    L = math.hypot(dx, dy)
    if L <= 0 or width <= 0:
        raise EndError("strip needs a length and a width")
    nx, ny = -dy / L * width / 2.0, dx / L * width / 2.0
    return [(p0[0] + nx, p0[1] + ny), (p1[0] + nx, p1[1] + ny), (p1[0] - nx, p1[1] - ny), (p0[0] - nx, p0[1] - ny)]


# ------------------------------------------------------------------------------------------------ vertical
def vertical_overlap(a0, a1, b0, b1):
    """Length of the overlap of two vertical intervals [a0, a1] and [b0, b1]."""
    return max(0.0, min(a1, b1) - max(a0, b0))


def strap_end(D, H, A_net, A_col, e):
    """One strap end inside one footing outline, the strap soffit `e` above the footing soffit.

    A_net = strap plan area inside the footing outline with the column (neck) footprint removed; A_col = that
    column footprint inside the strap strip. Strap solid [e, e + D]; footing [0, H]; neck [H, top].
    Returns the footing-owned part (counted once, in the footing line), the strap excess (strap concrete in no
    footing: the strap's own), the neck-owned part (the strap above the footing top inside the column footprint:
    the neck is billed through from the footing top) and whether the strap is cast monolithic with the footing.
    """
    for k, v in (("D", D), ("H", H), ("A_net", A_net), ("A_col", A_col), ("e", e)):
        if v is None:
            return {"status": HELD, "missing": k}
    if D <= 0 or H <= 0 or A_net < 0 or A_col < 0:
        raise EndError("D, H must be > 0; areas >= 0")
    ov = vertical_overlap(e, e + D, 0.0, H)
    above_top = vertical_overlap(e, e + D, H, math.inf)
    return {"status": DRAWING_CONFIRMED, "footing_m3": A_net * ov, "strap_excess_m3": A_net * (D - ov),
            "neck_m3": A_col * above_top, "monolithic": ov > TOL, "vertical_overlap_m": ov}


def strap_level_range(D, ends, e_min=None, e_max=None, step_breaks=True):
    """Strap excess over every level `e` at which the strap is monolithic with EVERY footing it joins.

    ends: [{"end": id, "H": m, "A_net": m2, "A_col": m2}] sharing one footing-soffit datum. Returns the minimum
    (with the e that gives it), the supremum (an open bound: monolithic at both ends is strict) and the excess at
    e = 0. Any H missing -> HELD (never 0)."""
    for x in ends:
        if x.get("H") is None or x.get("A_net") is None:
            return {"status": HELD, "missing": f"{x.get('end')}: footing thickness or plan area"}
    lo = -D if e_min is None else e_min
    hi = min(x["H"] for x in ends) if e_max is None else e_max
    if hi - lo <= TOL:
        return {"status": HELD, "missing": "no level is monolithic with every footing"}
    breaks = {lo, hi, 0.0}
    for x in ends:
        breaks |= {x["H"] - D, x["H"], 0.0 - D}
    pts = sorted(b for b in breaks if lo - TOL <= b <= hi + TOL)

    def total(e):
        ex = sum(strap_end(D, x["H"], x["A_net"], x.get("A_col", 0.0), e)["strap_excess_m3"] for x in ends)
        nk = sum(strap_end(D, x["H"], x["A_net"], x.get("A_col", 0.0), e)["neck_m3"] for x in ends)
        return ex, nk

    vals = [(total(e)[0], e) for e in pts]          # piecewise linear: extremes sit on breakpoints
    vmin, emin = min(vals)
    vsup, esup = max(vals)
    at0 = total(0.0) if lo - TOL <= 0.0 <= hi + TOL else (None, None)
    return {"status": HELD, "e_range_m": (lo, hi), "excess_min_m3": vmin, "e_at_min_m": emin,
            "excess_sup_m3": vsup, "e_at_sup_m": esup, "excess_at_e0_m3": at0[0], "neck_at_e0_m3": at0[1],
            "note": "open bound at the range ends: monolithic with every footing is strict"}


def check_strap_billing(axis_face_to_face_m, billed_length_m, D, H_ends, tol=0.002):
    """Refuse a strap concrete length that runs past the footing faces while the strap is no deeper than the
    footings (that part is footing concrete, owned once by the footing) or a centre-to-centre length."""
    if billed_length_m is None or axis_face_to_face_m is None:
        return {"status": HELD, "missing": "length"}
    if billed_length_m > axis_face_to_face_m + tol and all(H is not None and D <= H + TOL for H in H_ends):
        return {"status": "REFUSED", "reason": "DOUBLE: strap billed inside a footing at D <= H (footing owns it)",
                "excess_m": billed_length_m - axis_face_to_face_m}
    if billed_length_m < axis_face_to_face_m - tol:
        return {"status": "REFUSED", "reason": "GAP: strap shorter than the axis between the faces (projection?)",
                "short_m": axis_face_to_face_m - billed_length_m}
    return {"status": "OK"}


# ------------------------------------------------------------------------------------------------ ground beams
def band_frame(u):
    L = math.hypot(*u)
    if abs(L - 1.0) > 1e-6:
        raise EndError("u must be a unit vector")
    return u, (-u[1], u[0])


def band_slab(u, lo, hi, t0, t1):
    """Plan rectangle of a band between stations t0 .. t1 (band offsets lo .. hi along n)."""
    u, n = band_frame(u)
    t0, t1 = sorted((t0, t1))
    P = lambda t, o: (t * u[0] + o * n[0], t * u[1] + o * n[1])  # noqa: E731
    return [P(t0, lo), P(t1, lo), P(t1, hi), P(t0, hi)]


def gb_end(u, lo, hi, t_face, side, neck_polys, drawn_column, depths, t_drawn_end=None):
    """One ground-beam span end at a column (neck).

    The span is billed face to face from `t_face` (the face of the DRAWN column on the ground-beam plan) into the
    span (`side` = +1: span at t > t_face, -1: t < t_face). Neck candidates: one polygon per printed reading.
    DOUBLE = neck plan inside the billed span strip (the beam billed over the neck); GAP = beam strip between the
    face line and the drawn column outline (oblique faces) not inside the neck. Volumes = plan x every candidate
    depth. Owner of the intersection: NECK (billed through to the beam top). One candidate -> DRAWING-CONFIRMED;
    several -> CONFLICT range (never its larger end); none -> HELD."""
    if not neck_polys:
        return {"status": HELD, "missing": "neck section"}
    if not depths:
        return {"status": HELD, "missing": "ground-beam depth"}
    far = t_face + side * 1e6
    span = band_slab(u, lo, hi, t_face, far)
    # station where the drawn column first enters the band strip on the span side
    uu, nn = band_frame(u)
    inside = clip_convex(drawn_column, band_slab(u, lo, hi, t_face - 1e6, t_face + 1e6))
    ts = [p[0] * uu[0] + p[1] * uu[1] for p in inside] or [t_face]
    t_enter = min(ts) if side > 0 else max(ts)
    if t_drawn_end is not None:
        t_enter = max(t_enter, t_drawn_end) if side > 0 else min(t_enter, t_drawn_end)
    rows, slabs = [], []
    for np_ in neck_polys:
        dbl = overlap_area(np_, span)
        # the neck's own face on the span side (inside the band strip); a neck smaller than the drawn outline leaves
        # beam concrete between its face and the drawn face
        nin = clip_convex(np_, band_slab(u, lo, hi, t_face - 1e6, t_face + 1e6))
        nts = [p[0] * uu[0] + p[1] * uu[1] for p in nin] or [t_enter]
        t_neck = max(nts) if side > 0 else min(nts)
        t_back = min(t_enter, t_neck) if side > 0 else max(t_enter, t_neck)
        if t_drawn_end is not None:            # beam concrete exists only where the band is drawn
            t_back = max(t_back, t_drawn_end) if side > 0 else min(t_back, t_drawn_end)
        gap, slab = 0.0, None
        if abs(t_face - t_back) > TOL:
            slab = band_slab(u, lo, hi, t_back, t_face)
            gap = max(0.0, area(slab) - overlap_area(slab, np_))
        rows.append((dbl, gap))
        slabs.append(slab)
    dmin, dmax = min(d for d, _ in rows), max(d for d, _ in rows)
    gmin, gmax = min(g for _, g in rows), max(g for _, g in rows)
    Dl, Dh = min(depths), max(depths)
    status = DRAWING_CONFIRMED if len(neck_polys) == 1 and len(set(depths)) == 1 else \
        (CONFLICT if len(neck_polys) > 1 else HELD)
    return {"status": status, "owner": "NECK", "double_plan": (dmin, dmax), "gap_plan": (gmin, gmax),
            "double_m3": (dmin * Dl, dmax * Dh), "gap_m3": (gmin * Dl, gmax * Dh),
            "gb_correction_m3": (gmin * Dl - dmax * Dh, gmax * Dh - dmin * Dl),
            "per_reading": rows, "gap_regions": slabs}


def widened(rect, axis, delta):
    """Candidates for a printed section larger than the drawn axis-aligned rectangle by `delta` along x (axis 0) or
    y (axis 1), the drawn position of the extra not printed: grown at the low side, centred, at the high side."""
    xs = [p[0] for p in rect]
    ys = [p[1] for p in rect]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    out = []
    for f in (1.0, 0.5, 0.0):                      # share of delta added at the low side
        if axis == 0:
            a, b, c, d = x0 - f * delta, x1 + (1 - f) * delta, y0, y1
        else:
            a, b, c, d = x0, x1, y0 - f * delta, y1 + (1 - f) * delta
        out.append([(a, c), (b, c), (b, d), (a, d)])
    return out


def vertical_separation(gb_top, gb_depth, footing_top):
    """Gap between a ground-beam soffit and a footing top (m). None in -> None (HELD)."""
    if gb_top is None or gb_depth is None or footing_top is None:
        return None
    return (gb_top - gb_depth) - footing_top


def free_end_support(t_drawn_end, candidates, tol):
    """The support of a ground-beam end that has no column: the drawn element whose face the band END lies on.

    candidates: [{"id", "kind" (WALL / COLUMN / BEAM / FOOTING), "t_face", "separation_m" (vertical gap to the
    beam; None = unknown)}]. A footing (or any element) vertically separated from the beam is never a support (its
    plan outline is not a 3-D contact); the face must coincide with the drawn band end within tol; none -> HELD."""
    hits, refused = [], []
    for c in candidates:
        sep = c.get("separation_m")
        if c["kind"] == "FOOTING" and (sep is None or sep > 0):
            refused.append((c["id"], "FOOTING outline: no 3-D contact with the beam" if sep else
                            "FOOTING outline: vertical relation unknown"))
            continue
        if abs(c["t_face"] - t_drawn_end) <= tol:
            hits.append(c)
    if len(hits) == 1:
        return {"status": DRAWING_CONFIRMED, "support": hits[0]["id"], "kind": hits[0]["kind"],
                "t_face": hits[0]["t_face"], "refused": refused}
    return {"status": HELD, "missing": "no drawn support at the band end" if not hits else "two supports",
            "refused": refused}


def ledger_check(pieces):
    """Sum of billed = union: every intersection id is owned by exactly one element (pieces: [{"element",
    "owns": [ids], "nets": [ids]}]). Returns DOUBLE / GAP lists."""
    owned, netted = {}, {}
    for p in pieces:
        for i in p.get("owns", []):
            owned.setdefault(i, []).append(p["element"])
        for i in p.get("nets", []):
            netted.setdefault(i, []).append(p["element"])
    double = sorted(i for i, v in owned.items() if len(v) > 1)
    gap = sorted(i for i in netted if i not in owned)
    return {"double": double, "gap": gap, "ok": not double and not gap}


def policy_record():
    return {"policy_id": POLICY_ID, "guard_class": DEFAULT_GUARD_CLASS,
            "rule": "R-CONC-OWN-1 (T-189) applied to strap / ground-beam ends; proposed R-END-OWN-1 (T-230)",
            "statement": "A strap end inside a footing is footing concrete up to the footing's own depth; the part of "
                         "the strap outside the footing's depth is the strap's, except inside the neck footprint "
                         "above the footing top (neck). One strap soffit level per strap: every end is evaluated "
                         "at the same level. A ground beam is billed net of the PRINTED neck section (not a drafting "
                         "outline); a plan overlap with a footing is no intersection when the solids are separated "
                         "vertically, and a footing outline never terminates a ground beam."}
