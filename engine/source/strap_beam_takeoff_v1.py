"""STRAP_BEAM_TAKEOFF_V1 - strap beams (also oblique ones) measured from the drawing, one geometry per trade.

A NEW, unwired module (T-174; candidate only: no released or candidate method imports it; lane I may wire it). It does
not edit or replace GROUND_SYSTEM_SPANS_V2 (T-141), whose measure_straps() keeps every strap HELD on the length basis;
this module applies the owner's answer to Q-74 (2026-10-22, confirmed final in the main chat the same day):

    "Use the actual angled beam-axis length between the appropriate footing faces. [...] Reinforcement, formwork and
     excavation retain their own measurement geometries."

The physical element: a strap beam is a reinforced-concrete beam cast between two footings along its own axis. Each
trade gets its own geometry (ENGINEERING_REASONING_STANDARD s.3, "one element, several geometries"):

1. CONCRETE (owned by the strap line) = plan area of the strap strip of the PRINTED width B, centred on the drawn axis,
   lying OUTSIDE both footing outlines, x the printed depth D. Computed by slicing the width (exact when both strap
   edges cross the same face of each footing; then it equals B x the axis length face to face). Concrete inside a
   footing outline belongs to the footing line (counted once) as far as the footing thickness H reaches; where the
   strap is deeper than the footing (D > H) the part of the strap above / below the footing inside its outline is
   strap concrete in no footing: HELD as a range [(D - H) x A_in, D x A_in] because the strap's vertical position
   against the footing is not printed (A_in = strap plan area inside the outline up to the drawn strap end, column
   outlines removed: column / neck concrete is the column line's).
2. BARS (straight run lower bound) = the bar's run between the two footing faces along its own line (axis offsets):
   the concrete length, not the projection. Anchorage beyond each face is a separate HELD range (n_d_min .. n_d_max
   bar diameters per end, from the notes the caller passes; zone and end shape not printed -> never released).
   Links: the "n per m" notation is NOT interpreted here (per element type, ERS s.3 / Q-71): both counts are given,
   A = n x run and B = ceil(run / (1 / n)) + 1, as a HELD range; link developed length is not computed.
3. FORMWORK = the two exposed side faces, each edge's own run between the footing faces x D (an oblique face gives the
   two sides different runs). The ends are cast against the footings (no form); the top is open; the soffit is HELD
   (cast on blinding or formed: no strap section is printed). The footing side face covered by the strap (chord on
   the face x min(D, H)) is listed for the footing formwork owner as a deduction, never applied here.
4. EXCAVATION: its own geometry, never the beam's concrete section: the trench run between the footing outlines along
   the axis is an UPPER bound of the run outside the footing pits (the pits' working space is not printed), width B
   plus working space (not printed), depth from the formation (HELD, owner Q-21 C). Volume HELD, never 0.

A PROJECTION of the footings on the axis (the frozen S5 register's "clear length") is reported only to show the cause
of its difference: axis face to face = projection gap + the corner over-reach of each footing (the part of the footing
outline that projects further along the axis than the face the strap actually crosses). It is not a built length.

Inputs (drawing units "mm" or "m"; outputs in metres): strap {strap_id, mark, edges: [((x, y), (x, y)) x 2] the two
drawn strap edge lines, B_m / D_m printed section (None -> HELD), bars: [{position, count, dia_mm}], links:
{per_m, dia_mm} or None, anchorage_d: (n_min, n_max) or None}; footings [{support_id, polygon, H_m (None -> HELD)}],
convex outlines (an open outline closed by its chord, as T-073 / T-141 read it); columns [{support_id, polygon}].
Rules: Q-74 (owner, final), UP-QTY-STATUS-001 (released / held / unsupported; missing never 0), URBAN-REBAR-NET-AND-
PROCUREMENT@v1 (net lengths only, no waste), unit mass from the project method passed in (rebar_unit_mass).
"""

from __future__ import annotations

import math

POLICY_ID = "STRAP_BEAM_TAKEOFF_V1"
DEFAULT_GUARD_CLASS = "UNWIRED_PRODUCER"
RULE_Q74 = "Q-74 (owner 2026-10-22, confirmed final): strap concrete at the beam-axis length between the footing faces"
RULE_STATUS = "UP-QTY-STATUS-001"
UNIT_TO_M = {"mm": 0.001, "m": 1.0}
DRAWING_CONFIRMED, HELD = "DRAWING-CONFIRMED", "HELD"
N_SLICES = 2000
TOL_M = 0.005


class StrapError(ValueError):
    pass


# ------------------------------------------------------------------------------------------------------ geometry
def _dot(p, u):
    return p[0] * u[0] + p[1] * u[1]


def _norm(v):
    L = math.hypot(v[0], v[1])
    if L == 0:
        raise StrapError("zero-length strap edge")
    return (v[0] / L, v[1] / L)


def _area(poly):
    n = len(poly)
    return abs(sum(poly[i][0] * poly[(i + 1) % n][1] - poly[(i + 1) % n][0] * poly[i][1] for i in range(n))) / 2.0 \
        if n >= 3 else 0.0


def _signed(poly):
    n = len(poly)
    return sum(poly[i][0] * poly[(i + 1) % n][1] - poly[(i + 1) % n][0] * poly[i][1] for i in range(n)) / 2.0


def _convex(poly):
    n, sgn = len(poly), 0
    for i in range(n):
        a, b, c = poly[i], poly[(i + 1) % n], poly[(i + 2) % n]
        cr = (b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0])
        if abs(cr) < 1e-9:
            continue
        s = 1 if cr > 0 else -1
        if sgn and s != sgn:
            return False
        sgn = s
    return True


def _clip_convex(subject, clip):
    """Sutherland-Hodgman: subject (any simple polygon) clipped by a CONVEX clip polygon."""
    ccw = _signed(clip) > 0
    out = list(subject)
    n = len(clip)
    for i in range(n):
        a, b = clip[i], clip[(i + 1) % n]
        inp, out = out, []
        if not inp:
            break

        def side(p):
            v = (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0])
            return v if ccw else -v
        for j in range(len(inp)):
            p, q = inp[j], inp[(j + 1) % len(inp)]
            fp, fq = side(p), side(q)
            if fp >= 0:
                out.append(p)
            if (fp >= 0) != (fq >= 0):
                t = fp / (fp - fq)
                out.append((p[0] + t * (q[0] - p[0]), p[1] + t * (q[1] - p[1])))
    return out


def _line_hits(poly, p, d):
    """Parameters s (any sign) where the line p + s d crosses an edge of poly, with the edge index."""
    out = []
    n = len(poly)
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        ex, ey = b[0] - a[0], b[1] - a[1]
        den = d[0] * ey - d[1] * ex
        if abs(den) < 1e-12:
            continue
        s = ((a[0] - p[0]) * ey - (a[1] - p[1]) * ex) / den
        t = ((a[0] - p[0]) * d[1] - (a[1] - p[1]) * d[0]) / den
        if -1e-9 <= t <= 1 + 1e-9:
            out.append((s, i))
    return sorted(out)


def _poly(pts, what):
    poly = [tuple(map(float, p[:2])) for p in pts]
    if len(poly) >= 2 and poly[0] == poly[-1]:
        poly = poly[:-1]
    if len(poly) < 3 or _area(poly) <= 0:
        raise StrapError(f"{what}: polygon needs three or more points and an area")
    # one straight face = one edge: drop vertices that lie on the line of their neighbours (an open outline closed
    # by its chord leaves the chord collinear with the face it interrupts)
    changed = True
    while changed and len(poly) > 3:
        changed = False
        for i in range(len(poly)):
            a, b, c = poly[i - 1], poly[i], poly[(i + 1) % len(poly)]
            cr = (b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0])
            if abs(cr) <= 1e-9 * max(1.0, math.hypot(b[0] - a[0], b[1] - a[1]) * math.hypot(c[0] - b[0], c[1] - b[1])):
                del poly[i]
                changed = True
                break
    return poly


# ------------------------------------------------------------------------------------------------------ main
def _axis(strap):
    (a0, a1), (b0, b1) = [tuple(tuple(map(float, p[:2])) for p in e) for e in strap["edges"]]
    ua, ub = _norm((a1[0] - a0[0], a1[1] - a0[1])), _norm((b1[0] - b0[0], b1[1] - b0[1]))
    if _dot(ua, ub) < 0:
        b0, b1, ub = b1, b0, (-ub[0], -ub[1])
    if abs(ua[0] * ub[1] - ua[1] * ub[0]) > 2e-3:
        raise StrapError(f"strap {strap['strap_id']}: drawn edges are not parallel")
    u = _norm((ua[0] + ub[0], ua[1] + ub[1]))
    n = (-u[1], u[0])
    oa, ob = _dot(a0, n), _dot(b0, n)
    if oa > ob:
        (a0, a1, oa), (b0, b1, ob) = (b0, b1, ob), (a0, a1, oa)
    o_mid = (oa + ob) / 2.0
    s_lo = min(_dot(p, u) for p in (a0, a1, b0, b1))
    s_hi = max(_dot(p, u) for p in (a0, a1, b0, b1))
    # drawn end station of each edge (linear across the width between the two edges)
    ends = {"a": (min(_dot(a0, u), _dot(a1, u)), max(_dot(a0, u), _dot(a1, u)), oa),
            "b": (min(_dot(b0, u), _dot(b1, u)), max(_dot(b0, u), _dot(b1, u)), ob)}
    return u, n, o_mid, ob - oa, (s_lo, s_hi), ends


def _pt(u, n, s, o):
    return (s * u[0] + o * n[0], s * u[1] + o * n[1])


def _end_station(ends, o, side):
    (lo_a, hi_a, oa), (lo_b, hi_b, ob) = ends["a"], ends["b"]
    t = 0.5 if ob == oa else (o - oa) / (ob - oa)
    return (lo_a + t * (lo_b - lo_a)) if side == 0 else (hi_a + t * (hi_b - hi_a))


def takeoff_strap(strap, footings, columns=(), *, units="mm", unit_mass=None, n_slices=N_SLICES, tol_m=TOL_M):
    """One strap -> concrete / overlap / bars / formwork / excavation records (see the module docstring).
    unit_mass: callable d_mm -> kg/m of the project method (rebar_unit_mass.kg_per_m bound to the project config);
    None -> bar mass not computed (lengths only)."""
    if units not in UNIT_TO_M:
        raise StrapError(f"units {units!r} not in {sorted(UNIT_TO_M)}")
    k = UNIT_TO_M[units]
    tol = tol_m / k
    F = []
    for f in footings:
        poly = _poly(f["polygon"], f"footing {f.get('support_id')}")
        if not _convex(poly):
            raise StrapError(f"footing {f.get('support_id')}: outline is not convex (split it into convex parts)")
        F.append({"id": str(f["support_id"]), "poly": poly, "H": f.get("H_m")})
    C = [{"id": str(c["support_id"]), "poly": _poly(c["polygon"], f"column {c.get('support_id')}")} for c in columns]
    u, n, o_mid, w_drawn, (s0, s1), ends = _axis(strap)
    B, D = strap.get("B_m"), strap.get("D_m")
    res = {"strap_id": strap["strap_id"], "mark": strap.get("mark"), "policy": POLICY_ID, "family": "STRAP_BEAM",
           "axis_unit": [round(u[0], 6), round(u[1], 6)],
           "axis_angle_deg": round(math.degrees(math.atan2(u[1], u[0])) % 180.0, 3),
           "drawn_width_m": round(w_drawn * k, 4), "B_m": B, "D_m": D, "rule_ids": [RULE_Q74, RULE_STATUS],
           "flags": [], "held": []}
    if B is None or D is None:
        res["held"].append("SECTION_NOT_PRINTED: printed B x D missing; concrete / formwork / bars HELD (the drawn "
                           "width is never used as the section)")
    elif abs(B - w_drawn * k) > tol_m:
        res["flags"].append(f"DRAWN_WIDTH_DIFFERS: drawn {w_drawn * k:.3f} m vs printed {B:.3f} m (printed governs)")
    half = (B / k / 2.0) if B is not None else (w_drawn / 2.0)

    # reference station: the middle of the longest stretch of the axis between the drawn ends outside every footing
    def outside(s):
        p = _pt(u, n, s, o_mid)
        return not any(_inside(p, f["poly"]) for f in F)
    best, cur, N = None, None, 400
    for i in range(N + 1):
        s = s0 + (s1 - s0) * i / N
        if outside(s):
            cur = (cur[0], s) if cur else (s, s)
            if best is None or cur[1] - cur[0] > best[1] - best[0]:
                best = cur
        else:
            cur = None
    if best is None:
        res["held"].append("AXIS_INSIDE_FOOTINGS: no stretch of the strap axis lies outside the footing outlines")
        res["status"] = HELD
        return res
    s_ref = (best[0] + best[1]) / 2.0

    def faces(o):
        """(s_lo, footing, edge index), (s_hi, footing, edge index) of the line at offset o, nearest to s_ref."""
        p = _pt(u, n, s_ref, o)
        lo = hi = None
        for f in F:
            for s, ei in _line_hits(f["poly"], p, u):
                if s < 0 and (lo is None or s > lo[0]):
                    lo = (s, f, ei)
                if s > 0 and (hi is None or s < hi[0]):
                    hi = (s, f, ei)
        return lo, hi
    lo0, hi0 = faces(o_mid)
    if not lo0 or not hi0:
        res["held"].append("NO_FOOTING_AT_END: the strap axis meets no footing outline at "
                           f"{'both ends' if not (lo0 or hi0) else 'one end'}; nothing measured, never 0")
        res["start_footing"] = lo0[1]["id"] if lo0 else None
        res["end_footing"] = hi0[1]["id"] if hi0 else None
        res["status"] = HELD
        return res
    f_lo, f_hi = lo0[1], hi0[1]
    res.update({"start_footing": f_lo["id"], "end_footing": f_hi["id"]})
    axis_len = (hi0[0] - lo0[0]) * k

    # slice the width: run between the faces of THE SAME two footings at each offset
    runs, same_face, miss = [], True, False
    for i in range(n_slices):
        o = o_mid - half + (i + 0.5) * (2 * half) / n_slices
        lo, hi = faces(o)
        if not lo or not hi or lo[1] is not f_lo or hi[1] is not f_hi:
            miss = True
            break
        same_face &= (lo[2] == lo0[2] and hi[2] == hi0[2])
        runs.append((hi[0] - lo[0]) * k)
    edge_runs = []
    for o in (o_mid - half, o_mid + half):
        lo, hi = faces(o)
        edge_runs.append(None if (not lo or not hi or lo[1] is not f_lo or hi[1] is not f_hi)
                         else round((hi[0] - lo[0]) * k, 4))
    if miss or None in edge_runs:
        res["held"].append("STRIP_LEAVES_FOOTING: part of the strap width does not meet the same footing faces "
                           "(the strap passes a footing corner); plan area HELD")
    area_out = None if (miss or None in edge_runs) else sum(runs) * (2 * half * k) / n_slices
    if same_face and not miss:
        res["flags"].append("SAME_FACE_BOTH_ENDS: both strap edges cross one straight face of each footing, so the "
                            "plan area outside the footings = B x the axis length exactly")

    # projection cause (S5 'clear length'): gap between the footings' projections on the axis
    p_lo = max(_dot(p, u) for p in f_lo["poly"])
    p_hi = min(_dot(p, u) for p in f_hi["poly"])
    s_face_lo, s_face_hi = s_ref + lo0[0], s_ref + hi0[0]
    over_lo, over_hi = (p_lo - s_face_lo) * k, (s_face_hi - p_hi) * k
    res["lengths"] = {"axis_face_to_face_m": round(axis_len, 4), "edge_face_to_face_m": edge_runs,
                      "projection_gap_m": round((p_hi - p_lo) * k, 4),
                      "corner_overreach_m": [round(over_lo, 4), round(over_hi, 4)],
                      "basis": "AXIS_FACE_TO_FACE (Q-74 A); projection gap = axis - the two corner over-reaches, "
                               "not a built length"}

    # 1. concrete owned by the strap line
    status_c = DRAWING_CONFIRMED if (B is not None and D is not None and area_out is not None) else HELD
    res["concrete"] = {"plan_area_outside_m2": None if area_out is None else round(area_out, 4),
                       "check_B_x_axis_m2": None if B is None else round(B * axis_len, 4),
                       "volume_m3": None if status_c == HELD else round(area_out * D, 4),
                       "formula": "plan area of the B-wide strip outside both footing outlines x D", "status": status_c}

    # 1b. strap concrete inside each footing outline (overlap treatment)
    over = []
    for side, f in ((0, f_lo), (1, f_hi)):
        e_l = _end_station(ends, o_mid - half, side)
        e_r = _end_station(ends, o_mid + half, side)
        # the strip from the drawn strap end back to the reference station (outside every footing), clipped by the
        # footing outline: exactly the strap plan inside the outline, whatever the angle of the face
        r_l, r_r = _pt(u, n, s_ref, o_mid - half), _pt(u, n, s_ref, o_mid + half)
        if side == 0:
            quad = [_pt(u, n, e_l, o_mid - half), r_l, r_r, _pt(u, n, e_r, o_mid + half)]
        else:
            quad = [r_l, _pt(u, n, e_l, o_mid - half), _pt(u, n, e_r, o_mid + half), r_r]
        rec = {"footing": f["id"], "H_m": f["H"]}
        reg = _clip_convex(quad, f["poly"])
        a_gross = _area(reg) if len(reg) >= 3 else 0.0
        rec["drawn_run_inside_mean_m"] = round(a_gross / (2 * half) * k, 4)
        if a_gross * k * k <= tol_m * 2 * half * k:
            rec.update({"A_in_m2": 0.0, "status": DRAWING_CONFIRMED,
                        "note": "strap drawn to the footing face: nothing inside the outline"})
            over.append(rec)
            continue
        a_in = a_gross
        a_col = 0.0
        for c in C:
            if _convex(c["poly"]) and len(reg) >= 3:
                cc = _clip_convex(reg, c["poly"])
                a_col += _area(cc) if len(cc) >= 3 else 0.0
        A = (a_in - a_col) * k * k
        rec.update({"A_in_m2": round(A, 4), "column_area_removed_m2": round(a_col * k * k, 4)})
        if D is None or f["H"] is None:
            rec.update({"status": HELD, "note": "strap depth or footing thickness not printed"})
        elif D <= f["H"] + tol_m:
            rec.update({"volume_m3": 0.0, "owner": "FOOTING", "status": DRAWING_CONFIRMED,
                        "note": f"D {D:.2f} <= H {f['H']:.2f}: the strap inside the outline is footing concrete "
                                "(counted once, in the footing line)"})
        else:
            rec.update({"range_m3": [round((D - f["H"]) * A, 4), round(D * A, 4)], "status": HELD,
                        "note": f"D {D:.2f} > H {f['H']:.2f}: strap concrete above / below the footing inside its "
                                "outline; low end = the strap spans the full footing thickness, high end = no "
                                "vertical overlap; the strap level against the footing is not printed"})
        over.append(rec)
    res["concrete_in_footings"] = over

    # 2. bars: straight run lower bound along each bar line = the face-to-face run (axis offsets); anchorage HELD
    bars = []
    for g in strap.get("bars") or []:
        L = axis_len
        rec = {"position": g.get("position"), "count": g.get("count"), "dia_mm": g.get("dia_mm"),
               "run_lb_m": round(L, 4), "run_basis": "between the footing faces along the strap axis"}
        if g.get("count") is None or g.get("dia_mm") is None:
            rec["status"] = HELD
        else:
            rec["total_run_lb_m"] = round(g["count"] * L, 4)
            if unit_mass is not None:
                kgm = unit_mass(g["dia_mm"])
                rec.update({"kg_per_m": round(kgm, 6), "kg_lb": round(g["count"] * L * kgm, 3)})
            rec["status"] = DRAWING_CONFIRMED
            anc = strap.get("anchorage_d")
            if anc:
                a0, a1 = (2 * anc[0] * g["dia_mm"] / 1000.0, 2 * anc[1] * g["dia_mm"] / 1000.0)
                rec["anchorage_two_ends_m_each_bar"] = {"range": [round(a0, 4), round(a1, 4)], "status": HELD}
                if unit_mass is not None:
                    rec["anchorage_kg"] = {"range": [round(g["count"] * a0 * kgm, 3),
                                                     round(g["count"] * a1 * kgm, 3)], "status": HELD}
        bars.append(rec)
    if None not in edge_runs and len(set(edge_runs)) > 1:
        res["flags"].append("RUN_VARIES_ACROSS_WIDTH: bar runs differ between the edges (oblique faces); the axis "
                            "run is used for every bar and the edge runs are stored")
    lk = strap.get("links")
    links = None
    if lk and lk.get("per_m"):
        nA = lk["per_m"] * axis_len
        nB = math.ceil(axis_len * lk["per_m"] - 1e-9) + 1
        links = {"per_m": lk["per_m"], "dia_mm": lk.get("dia_mm"), "count_range": [round(nA, 3), nB],
                 "status": HELD, "note": "'n per m' meaning not established for straps (per element type, Q-71): "
                                         "A = n x run, B = ceil(run x n) + 1; link developed length not computed"}
    res["bars"] = {"groups": bars, "links": links}

    # 3. formwork: two side faces, each its own run, x D; soffit HELD; cover of the footing face listed
    if D is not None and None not in edge_runs:
        sides = round((edge_runs[0] + edge_runs[1]) * D, 4)
        res["formwork"] = {"side_faces_m2": sides, "side_runs_m": edge_runs, "status": DRAWING_CONFIRMED,
                           "below_ground": {"FORMED_m2": sides, "EARTH_CAST_m2": 0.0,
                                            "decision": "formed or earth-cast sides below ground (owner OQ-10): "
                                                        "two alternatives, never summed, not chosen here"},
                           "ends": "none (cast against the footings)", "top": "none",
                           "soffit": {"status": HELD, "candidates_m2": [0.0, None if area_out is None
                                                                        else round(area_out, 4)],
                                      "note": "cast on blinding or formed: no strap section is printed"}}
    else:
        res["formwork"] = {"status": HELD, "note": "depth or a face run missing"}
    cover = []
    for f, lo in ((f_lo, True), (f_hi, False)):
        pa = faces(o_mid - half)[0 if lo else 1]
        pb = faces(o_mid + half)[0 if lo else 1]
        if pa and pb and pa[1] is f and pb[1] is f:
            qa = _pt(u, n, s_ref + pa[0], o_mid - half)
            qb = _pt(u, n, s_ref + pb[0], o_mid + half)
            chord = math.hypot(qb[0] - qa[0], qb[1] - qa[1]) * k
            h = None if (D is None or f["H"] is None) else min(D, f["H"])
            cover.append({"footing": f["id"], "chord_on_face_m": round(chord, 4),
                          "covered_m2": None if h is None else round(chord * h, 4),
                          "for": "footing side formwork (deduction by the footing formwork owner, not applied here)"})
    res["footing_face_covered"] = cover

    # 4. excavation: own geometry; volume HELD
    res["excavation"] = {"trench_run_upper_bound_m": round(axis_len, 4), "width_min_m": B,
                         "working_space": "not printed", "depth": "HELD (formation not printed, owner Q-21 C)",
                         "volume_m3": None, "status": HELD,
                         "note": "the trench between the footing pits is shorter than the run between the footing "
                                 "outlines by the pits' working space; never the concrete section, never 0"}
    res["status"] = DRAWING_CONFIRMED if status_c == DRAWING_CONFIRMED else HELD
    return res


def _inside(p, poly):
    x, y = p
    ins = False
    n = len(poly)
    for i in range(n):
        (x1, y1), (x2, y2) = poly[i], poly[(i + 1) % n]
        if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
            ins = not ins
    return ins


def policy_record():
    return {"policy_id": POLICY_ID, "default_guard_class": DEFAULT_GUARD_CLASS, "rules": [RULE_Q74, RULE_STATUS],
            "statement": "strap concrete = printed B x D over the strip outside both footing outlines along the "
                         "strap's own axis; inside a footing it is footing concrete up to the footing thickness, the "
                         "excess depth HELD; bars on their own runs with anchorage HELD; formwork on the two side "
                         "faces; excavation its own geometry, HELD without a formation"}
