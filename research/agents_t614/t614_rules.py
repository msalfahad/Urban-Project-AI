"""T-614 rules (research, unwired): the part of a drawn beam band beside a column that covers only part of the band.

R-T614-1 (PROPOSED, every villa; scope: cast-in-situ beams hanging from one slab, straight in plan, at every column
the drawn band runs into, at a run END or where the band runs THROUGH the column; refines the reading of
UP-CONC-JOINT-001 1.0.0 'beam face to face' on DRAWN outlines, never on the column alone):
  (a) the beam-column piece of a band is P = drawn band n S(column), S = the strip of the band axis between the
      column's two extreme stations (the column's along-axis span); the column owns P n column (its footprint, to the
      slab top); the remainder E = P - every column outline is the UNCOVERED part: concrete that exists because the
      band is drawn there and the column does not fill the band width (column shallower across the band than the
      band, or off the band axis);
  (b) E is owned by the BEAM whose band it lies in (the band runs on to the next drawn member face; the drawn band's
      own end edge bounds it, so E never runs past what is drawn); its volume is |E| x the beam depth, on the same
      depth convention as the candidate line it joins (full schedule depth to the slab top);
  (c) the part of E inside another beam's drawn band is a beam-beam common block: it is R-T610-1's (deeper member
      owns) and is NOT counted here; counting it again is refused (refuse_recount);
  (d) a piece whose beam depth is unknown is HELD (never 0, never valued at another member's depth);
  (f) the piece is MEASURED only where the band is drawn beside the column: the band's face on the uncovered side
      runs continuously (no break > FACE_GAP_M) along the piece, and the strip the column leaves beside it over its
      whole span (an end gap between the drawn band end and the column face included), net of columns and other
      beams' bands, lies inside the drawn band. Any part of that strip outside the drawn band and billed by no line
      is HELD (bounded by its area x the beam depth), never 0 and never assumed to be beam (Checker F-C-P02-5 adverse
      case: a broken face beside the column);
  (e) a column that fills the band width across its span gives E = 0 (the normal case: the column face closes the
      run); a census reports it as FULL, not as a finding.
  (g) (r2, Checker 2026-11-08T03:55Z, F-C-T614-2) BILLING OF A PIECE BY A LEDGER LINE is read from the line's own
      measured extent and its named add terms, never from a plan model: the line bills (i) its own route G rectangle(s)
      (= the printed length between the faces it names x the drawn width), (ii) where the printed length x width
      exceeds that rectangle (a mean-length oblique end, a run over an unlabelled span), only the drawn parts beyond the
      rectangle whose area matches that excess within EXT_TOL_M2, (iii) a named add term (T-229 END_SHORT_*, a T-229 run
      that replaces the schedule value) only through drawn parts beyond the rectangle whose area x depth matches the
      add value within ADD_TOL (best subset), (iv) a SUPPORT_CUT_BESIDE add only at its own cut column (placed by the
      census). Every other drawn part beyond the rectangle is MODEL_ONLY: not billed, however well a whole-line plan
      model matches the line value (a match within a tolerance larger than the piece proves nothing about the piece).

Accounting against an engine (account_piece): each candidate line bills a plan polygon; over E the engine bills
|E n union(billed)| at the line's depth; HELD lines (no valued depth) carry |E n held| as HELD; what lies in no
billed plan, no held plan and no other beam's band is the OMISSION, valued |E_omit| x d (verdict ENGINE_WRONG_OMISSION).
A plan billed inside E by two lines is a DOUBLE (verdict ENGINE_WRONG_DOUBLE_COUNT).
"""
from __future__ import annotations

import math

import shapely
from shapely.geometry import Polygon  # noqa: F401 (re-exported for the census)

RULE_ID = "R-T614-1"
GRID_M = 1e-7               # same snap grid as R-T610-1 (0.1 micrometre)
EPS_M2 = 1e-6               # 1 mm x 1 m: below this a piece is drafting noise (kept in totals, not a finding)
END_TOL_M = 0.02            # a column whose span reaches within 20 mm of the drawn band end closes that end
NEAR_M = 0.05               # columns within 50 mm of a drawn band are examined (an end gap of a few cm is caught)
FACE_GAP_M = 0.005          # a drawn face broken by more than 5 mm beside the column: the strip is not drawn


class Refused(ValueError):
    """An input that would make the census wrong (a piece counted twice, a piece valued at a guessed depth)."""


def polys(g):
    if g is None or g.is_empty:
        return Polygon()
    if g.geom_type in ("Polygon", "MultiPolygon"):
        return g
    parts = [p for p in getattr(g, "geoms", []) if p.geom_type in ("Polygon", "MultiPolygon") and not p.is_empty]
    return shapely.union_all(parts) if parts else Polygon()


def snap(g):
    g = polys(g)
    return polys(shapely.set_precision(g, GRID_M)) if not g.is_empty else Polygon()


def inter(a, b):
    return polys(shapely.intersection(snap(a), snap(b), grid_size=GRID_M))


def minus(a, b):
    return polys(shapely.difference(snap(a), snap(b), grid_size=GRID_M))


def union(gs):
    gs = [snap(g) for g in gs if g is not None and not g.is_empty]
    return polys(shapely.union_all(gs, grid_size=GRID_M)) if gs else Polygon()


def unit(u):
    n = math.hypot(u[0], u[1])
    if n == 0:
        raise Refused("a band axis needs a direction")
    return (u[0] / n, u[1] / n)


def span(g, u):
    """(min, max) station of a geometry's vertices on axis u."""
    pts = []
    for p in getattr(g, "geoms", [g]):
        pts += list(p.exterior.coords)
    ts = [x * u[0] + y * u[1] for x, y in pts]
    return min(ts), max(ts)


def strip(u, t0, t1, big=1e5):
    """The plan strip between stations t0 and t1 of axis u (unbounded across, in practice +-big)."""
    n = (-u[1], u[0])

    def P(t, o):
        return (u[0] * t + n[0] * o, u[1] * t + n[1] * o)
    return Polygon([P(t0, -big), P(t1, -big), P(t1, big), P(t0, big)])


def column_cover(band, u, column):
    """Across-band cover of a column: (cover_m, band_width_m, off_axis_m). cover = length of the band width the column
    spans; off_axis = distance from the band centre line to the column's centre across the band."""
    n = (-u[1], u[0])
    lo, hi = span(band, n)
    c0, c1 = span(column, n)
    cover = max(0.0, min(hi, c1) - max(lo, c0))
    return cover, hi - lo, abs((c0 + c1) / 2 - (lo + hi) / 2)


def piece(band, u, column, columns=()):
    """(a): P = band n S(column) and E = P - column outlines (the column itself and every other column given)."""
    u = unit(u)
    t0, t1 = span(column, u)
    P = inter(band, strip(u, t0, t1))
    E = minus(P, union([column] + list(columns)))
    return P, E


def band_strip(u, n_lo, n_hi, t0, t1):
    """The band's full-width strip (offsets n_lo .. n_hi across axis u) between stations t0 and t1."""
    u = unit(u)
    n = (-u[1], u[0])

    def P(t, o):
        return (u[0] * t + n[0] * o, u[1] * t + n[1] * o)
    if t1 <= t0:
        return Polygon()
    return Polygon([P(t0, n_lo), P(t1, n_lo), P(t1, n_hi), P(t0, n_hi)])


def beside_strip(u, n_lo, n_hi, column, band_span, pos, tol=1e-3, clip=False, bridge=False):
    """(f): the strip a column leaves beside it inside the band width, over the column's span, on each side the column
    does not reach (plus, at a run end, the full-width gap between the drawn band end and the column face).
    clip: limit the strip to the drawn band's own station range (a run END: past its end it is not this band);
    bridge: the band's collinear continuation (same axis, same face offsets) resumes on the column's far side, so the
    strip beside the whole column span belongs to the run even though its face is not drawn there (HELD, (f)).
    Not net of columns (the caller subtracts every column outline)."""
    u = unit(u)
    n = (-u[1], u[0])
    c0, c1 = span(column, u)
    cn0, cn1 = span(column, n)
    b0, b1 = band_span
    parts = []
    if pos == "BESIDE_BAND":
        return Polygon()
    s0, s1 = c0, c1
    if clip and not bridge:
        # at a run end the band is drawn only up to its end: beside the column beyond it is not this band
        s0, s1 = max(c0, b0), min(c1, b1)
    if cn1 < n_hi - tol:
        parts.append(band_strip(u, max(cn1, n_lo), n_hi, s0, s1))
    if cn0 > n_lo + tol:
        parts.append(band_strip(u, n_lo, min(cn0, n_hi), s0, s1))
    if pos == "END_HI" and c0 > b1 + tol:
        parts.append(band_strip(u, n_lo, n_hi, b1, c0))
    if pos == "END_LO" and c1 < b0 - tol:
        parts.append(band_strip(u, n_lo, n_hi, c1, b0))
    return union(parts)


def covered(intervals, t0, t1):
    """Length of [t0, t1] covered by the union of the intervals."""
    tot, cur = 0.0, t0
    for a, b in sorted(intervals):
        a, b = max(a, cur), min(b, t1)
        if b > a:
            tot += b - a
            cur = b
    return tot


def face_gaps(E, u, n_lo, n_hi, faces, column, tol=1e-3):
    """(f): the longest undrawn length of the band face on the column's uncovered side(s) along the piece E.
    faces: [{'off_m': offset across u, 'intervals': [(t0, t1), ...]}] for the band's two drawn faces."""
    E = polys(E)
    if E.is_empty:
        return 0.0
    u = unit(u)
    n = (-u[1], u[0])
    cn0, cn1 = span(column, n)
    t0, t1 = span(E, u)
    worst = 0.0
    for side_off, uncovered in ((n_hi, cn1 < n_hi - tol), (n_lo, cn0 > n_lo + tol)):
        if not uncovered:
            continue
        fs = [f for f in faces if abs(f["off_m"] - side_off) <= 0.01]
        cov = covered([iv for f in fs for iv in f["intervals"]], t0, t1) if fs else 0.0
        worst = max(worst, (t1 - t0) - cov)
    return worst


def position(band, u, column, tol=END_TOL_M):
    """END_LO / END_HI where the column span reaches the drawn band end (within tol), else THROUGH."""
    u = unit(u)
    b0, b1 = span(band, u)
    c0, c1 = span(column, u)
    if c0 <= b0 + tol:
        return "END_LO"
    if c1 >= b1 - tol:
        return "END_HI"
    return "THROUGH"


def account_piece(E, depth_m, billed, held=(), other_bands=()):
    """E: the uncovered piece; depth_m: the owning beam's depth (None = unknown); billed: {line_id: plan polygon} of
    valued candidate lines; held: plans of lines without a valued depth; other_bands: drawn bands of OTHER beams (a
    part of E inside one is R-T610-1's crossing zone, excluded here)."""
    E = snap(E)
    a = E.area
    cross = inter(E, union(list(other_bands)))
    own = minus(E, cross)
    per_line = {k: inter(own, v).area for k, v in billed.items() if v is not None and not v.is_empty}
    per_line = {k: v for k, v in per_line.items() if v > 0.0}
    b_union = inter(own, union([v for v in billed.values() if v is not None]))
    double = sum(per_line.values()) - b_union.area
    h = minus(inter(own, union(list(held))), b_union)
    omit = minus(minus(own, b_union), h)
    rec = {"piece_m2": a, "in_other_band_m2": cross.area, "owned_m2": own.area, "billed_m2": b_union.area,
           "billed_by": per_line, "billed_twice_m2": max(double, 0.0), "held_m2": h.area, "unowned_m2": omit.area}
    if abs(rec["billed_m2"] + rec["held_m2"] + rec["unowned_m2"] - rec["owned_m2"]) > 1e-7:   # snap-grid noise (perimeter x 1e-7 m)
        raise AssertionError(rec)
    if a <= EPS_M2:
        rec.update(state="MEASURED", verdict="FULL", omission_m3=0.0, double_m3=0.0)
        return rec
    if depth_m is None:
        rec.update(state="HELD", verdict="HELD", omission_m3=None, double_m3=None,
                   reason="beam depth unknown: the piece is HELD, never 0 and never valued at another depth")
        return rec
    rec.update(state="MEASURED", depth_m=depth_m, omission_m3=rec["unowned_m2"] * depth_m,
               double_m3=rec["billed_twice_m2"] * depth_m)
    if rec["billed_twice_m2"] > EPS_M2:
        rec["verdict"] = "ENGINE_WRONG_DOUBLE_COUNT"
    elif rec["unowned_m2"] > EPS_M2:
        rec["verdict"] = "ENGINE_WRONG_OMISSION"
    elif rec["held_m2"] > EPS_M2:
        rec["verdict"] = "HELD_LINE"
    else:
        rec["verdict"] = "ENGINE_RIGHT"
    return rec


EXT_TOL_M2 = 1e-4           # (g)(ii): printed length x width minus the rectangle, matched by drawn parts within 1 cm2 ...
EXT_TOL_REL = 0.001         # ... or 0.1 % of the excess (a 4-decimal printed length on a 0.65 m band: GF B26 0.18 mm)
ADD_TOL_ABS_M3 = 0.001      # (g)(iii): a named add placed by drawn parts whose volume matches within 1 dm3 ...
ADD_TOL_REL = 0.01          # ... or 1 % of the add (T-229 printed its adds to 4 decimals from hand-rounded areas)
MAX_PARTS = 12              # subset search bound (a run end has a handful of parts)


def parts_of(g, min_m2=1e-9):
    g = polys(g)
    return [p for p in getattr(g, "geoms", [g]) if not p.is_empty and p.area > min_m2]


def _best_subset(areas, target, weight=1.0):
    """Indices of the subset whose sum x weight is nearest the target; (best, diff, runner_up_diff, runner_up)."""
    n = len(areas)
    if n > MAX_PARTS:
        raise Refused(f"{n} parts beyond one ledger rectangle: too many to place a named add (inspect by hand)")
    scored = []
    for mask in range(1 << n):
        s = sum(areas[i] for i in range(n) if mask >> i & 1) * weight
        scored.append((abs(s - target), bin(mask).count("1"), mask))
    scored.sort()
    best = scored[0]
    second = scored[1] if len(scored) > 1 else (math.inf, 0, 0)
    idx = [i for i in range(n) if best[2] >> i & 1]
    idx2 = [i for i in range(n) if second[2] >> i & 1]
    return idx, best[0], second[0], idx2


def ledger_billing(rect_billed, beyond, ext_m2, add_m3, depth_m):
    """(g): the plan a LEDGER line bills. rect_billed: its own route G rectangle(s) (junction deductions applied);
    beyond: the drawn parts of its own pieces outside every rectangle (the T-610 model's extra plan); ext_m2: printed
    length x drawn width minus the rectangle area (<= EPS: none); add_m3: named END / run add values (not
    SUPPORT_CUT_BESIDE, placed at its cut by the census); depth_m: the line's depth.
    Returns {'billed': plan, 'extent_m2', 'add_m2', 'model_only_m2', 'model_only': plan, 'ext_state', 'add_state',
    'add_diff_m3', 'add_runner_up_diff_m3'}."""
    ps = parts_of(beyond)
    areas = [p.area for p in ps]
    used = set()
    rec = {"ext_state": "NONE", "add_target_m3": sum(add_m3),
           "add_state": "NONE", "add_diff_m3": None, "add_runner_up_diff_m3": None}
    ext_parts, add_parts = [], []
    ext_tol = max(EXT_TOL_M2, EXT_TOL_REL * ext_m2)
    rec["ext_target_m2"] = ext_m2 if ext_m2 > ext_tol else 0.0
    if ext_m2 > ext_tol:
        idx, diff, _, _ = _best_subset(areas, ext_m2)
        if diff <= ext_tol:
            ext_parts = idx
            used |= set(idx)
            rec["ext_state"] = "PLACED"
        else:
            rec["ext_state"] = "UNPLACED"      # the printed extent is longer than any drawn part set: not proof
        rec["ext_diff_m2"] = diff
    if add_m3:
        if depth_m is None:
            raise Refused("a named add cannot be placed without the line's depth")
        rest = [i for i in range(len(ps)) if i not in used]
        idx, diff, diff2, idx2 = _best_subset([areas[i] for i in rest], sum(add_m3), depth_m)
        tol = max(ADD_TOL_ABS_M3, ADD_TOL_REL * sum(add_m3))
        rec["add_diff_m3"], rec["add_runner_up_diff_m3"] = diff, diff2
        if diff <= tol:
            add_parts = [rest[i] for i in idx]
            used |= set(add_parts)
            # a second, different subset inside the tolerance: the placement is not unique; flagged, never silent
            rec["add_state"] = "PLACED_AMBIGUOUS" if diff2 <= tol and set(idx) != set(idx2) else "PLACED"
        else:
            rec["add_state"] = "UNPLACED"
    mo = [ps[i] for i in range(len(ps)) if i not in used]
    rec["billed"] = union([rect_billed] + [ps[i] for i in ext_parts + add_parts])
    rec["model_only"] = union(mo)
    rec["extent_m2"] = sum(areas[i] for i in ext_parts)
    rec["add_m2"] = sum(areas[i] for i in add_parts)
    rec["model_only_m2"] = sum(p.area for p in mo)
    return rec


def refuse_model_proof(piece, line_extent_plan, model_plan, model_state):
    """Adverse guard (g): a piece outside the ledger line's own extent / named adds offered as billed because the
    whole-line model matches (MODEL_MATCHES within LEDGER_TOL) is refused."""
    out = minus(inter(piece, model_plan), line_extent_plan)
    if out.area > EPS_M2 and model_state == "MODEL_MATCHES":
        raise Refused(f"{out.area:.6f} m2 of the piece lies outside the line's measured extent and named adds: a "
                      f"plan model matching the line value within a tolerance never proves billing of a piece")
    return out.area


def refuse_recount(claims, crossing_zones):
    """Adverse guard (c): a claimed piece that overlaps a beam-beam crossing zone (R-T610-1) is refused; claims and
    zones are plan polygons."""
    zs = union(list(crossing_zones))
    for k, g in claims.items():
        ov = inter(g, zs).area
        if ov > EPS_M2:
            raise Refused(f"piece {k} overlaps a R-T610-1 crossing zone by {ov:.6f} m2: one block, one owner")


def refuse_guessed_depth(rec):
    """Adverse guard (d): a HELD piece offered with a volume (0 or a borrowed depth) is refused."""
    if rec.get("state") == "HELD" and rec.get("omission_m3") is not None:
        raise Refused("a HELD piece carries no volume (never 0, never a borrowed depth)")
    return rec
