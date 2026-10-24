"""BEAM_LEDGER_R2 (T-252, unwired, stdlib only; rollback: delete the folder).

Revision 2 of the T-241 CONC.BEAM ledger (BEAM_LINE_V1 stays untouched). Two plan-geometry rules the Checker found
missing (Verifier 2026-10-24 02:02 / 02:08, T-180 slot), each a NEW rule version beside the merged ones:

R-BEAM-END-OBLIQUE-2 (supersedes the T-229 end check for members ending on an oblique carrier; T-229 files untouched)
    Physical element: a beam run ends where its solid meets the face of the member that carries it. When that face is
    oblique to the run, each of the run's two side faces meets the carrier face at its OWN point, so the run's plan is a
    trapezoid: length along each drawn edge = start face -> carrier face on that edge; area = b x (La + Lb) / 2. This
    holds on EITHER face of the carrier (lower / upper, west / east). Billing the short edge only (a one-face end) leaves
    the triangle b x |La - Lb| / 2 in no line. T-229 classify_end measured the drawn-edge cover beyond the billed end
    per side; on a triangle the side at the apex has zero length beyond the face, its cover read 0 and the end passed as
    'ends at the billed face'. R2 measures each edge to the face instead, so an apex edge is simply already at the face.

R-BEAM-CURVED-AREA-2 (any curved / ring beam)
    The plan area of a curved member is the area between its OWN drawn edges (arcs as arcs), closed only by the faces of
    the members that own the crossings, less any void it surrounds. Never the sum of straight / chord bands a
    band-fitter returns (they under-cover the arcs and leave the junction pieces in no band). The ring is reconciled
    once: marks around it vs pieces vs area. Under convention C1 (T-234) the beam owns the whole ring area; an area of
    the ring that the slab ledger also holds is a double count and is refused (R-CONC-OWN-1).

ERS s.2 (define, reconstruct from first principles, reconcile), s.3 (geometric scope before numbers), s.4 (quantity +
rule + regression test). No value is defaulted: a missing edge, face or depth is refused or HELD, never 0.
"""
from __future__ import annotations

import math

SCHEMA = "BEAM_LEDGER_R2"
RULES = ("R-BEAM-END-OBLIQUE-2", "R-BEAM-CURVED-AREA-2")
UNIT_TO_M = {"m": 1.0, "cm": 0.01, "mm": 0.001}
ON_FACE_TOL_M = 0.003    # a drawn edge end within 3 mm of the carrier face line is ON that face (drafting precision)
LEN_TOL_M = 0.002        # billed vs drawn length: agreement within 2 mm
GAP_TOL_M = 0.002        # loop closure: consecutive boundary pieces must meet within 2 mm
AREA_TOL_M2 = 1e-3       # area agreement for the counted-once checks (0.001 m2 = 0.6 mm fit x 1.7 m of edge)
PARALLEL_TOL_DEG = 0.5
MEASURED = ("CALCULATED", "DRAWING-CONFIRMED", "VERIFIED")


class Refused(ValueError):
    """A request the rules refuse (the message names the rule)."""


def to_m(v, unit="m"):
    if unit not in UNIT_TO_M:
        raise Refused("UNIT_UNKNOWN: %r" % unit)
    if v is None:
        return None
    return float(v) * UNIT_TO_M[unit]


def _pt(p, unit):
    return (to_m(p[0], unit), to_m(p[1], unit))


# ----------------------------------------------------------------------------------------------------------- lines
def _line(p, q):
    dx, dy = q[0] - p[0], q[1] - p[1]
    n = math.hypot(dx, dy)
    if n < 1e-9:
        raise Refused("DEGENERATE_LINE: two equal points")
    return p, (dx / n, dy / n)


def _intersect(l1, l2):
    (p, u), (q, v) = l1, l2
    den = u[0] * v[1] - u[1] * v[0]
    if abs(den) < math.sin(math.radians(PARALLEL_TOL_DEG)):
        return None
    t = ((q[0] - p[0]) * v[1] - (q[1] - p[1]) * v[0]) / den
    return (p[0] + t * u[0], p[1] + t * u[1])


def dist_to_line(pt, line):
    (p, u) = line
    return abs((pt[0] - p[0]) * u[1] - (pt[1] - p[1]) * u[0])


def _shoelace(pts):
    s = 0.0
    for i in range(len(pts)):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % len(pts)]
        s += x1 * y2 - x2 * y1
    return s / 2.0


# ------------------------------------------------------------------------------------- R-BEAM-END-OBLIQUE-2 (a)
def run_between_faces(edge_a, edge_b, start_face, end_face, unit="m", b_schedule=None, depth=None):
    """A straight beam run from its drawn edges.

    edge_a / edge_b: the two drawn side edges, each as two points (p, q) on the edge line, q being the drawn end
    at the carrier; start_face / end_face: two points on each face line. Every length / area is measured on each edge
    from the start face to the end face (the trapezoid), whatever the faces' angles.

    Refused: edges not parallel (not one straight member), an edge parallel to a face (it never meets it), a drawn
    edge end that is not ON the end face (EDGE_STOPS_SHORT_OF_FACE: the drawn member does not reach that carrier;
    the end is not this rule's), b_schedule given and different from the drawn width by more than 5 mm (a width
    CONFLICT belongs to the T-241 conflict rule, never collapsed here)."""
    ea = _line(_pt(edge_a[0], unit), _pt(edge_a[1], unit))
    eb = _line(_pt(edge_b[0], unit), _pt(edge_b[1], unit))
    sf = _line(_pt(start_face[0], unit), _pt(start_face[1], unit))
    ef = _line(_pt(end_face[0], unit), _pt(end_face[1], unit))
    cross = abs(ea[1][0] * eb[1][1] - ea[1][1] * eb[1][0])
    if cross > math.sin(math.radians(PARALLEL_TOL_DEG)):
        raise Refused("EDGES_NOT_PARALLEL: the two edges are not one straight member")
    b = dist_to_line(eb[0], ea)
    if b < 1e-6:
        raise Refused("EDGES_COINCIDENT: no width between the two edges")
    pts = {}
    for name, e, raw in (("a", ea, edge_a), ("b", eb, edge_b)):
        s = _intersect(e, sf)
        t = _intersect(e, ef)
        if s is None or t is None:
            raise Refused("EDGE_PARALLEL_TO_FACE: edge %s never meets a face" % name)
        drawn_end = _pt(raw[1], unit)
        if dist_to_line(drawn_end, ef) > ON_FACE_TOL_M:
            raise Refused("EDGE_STOPS_SHORT_OF_FACE: drawn edge %s ends %.4f m off the carrier face (both edges must "
                          "reach the face; otherwise the end is not measured by this rule)"
                          % (name, dist_to_line(drawn_end, ef)))
        pts[name] = (s, t)
    La = math.hypot(pts["a"][1][0] - pts["a"][0][0], pts["a"][1][1] - pts["a"][0][1])
    Lb = math.hypot(pts["b"][1][0] - pts["b"][0][0], pts["b"][1][1] - pts["b"][0][1])
    area = abs(_shoelace([pts["a"][0], pts["a"][1], pts["b"][1], pts["b"][0]]))
    if b_schedule is not None and abs(to_m(b_schedule, unit) - b) > 0.005:
        raise Refused("WIDTH_CONFLICT: schedule %.3f vs drawn %.3f m (T-241 conflict rule, range kept apart)"
                      % (to_m(b_schedule, unit), b))
    out = dict(rule="R-BEAM-END-OBLIQUE-2", b_drawn_m=b, La_m=La, Lb_m=Lb, mean_length_m=(La + Lb) / 2.0,
               plan_m2=area, end_triangle_m2=b * abs(La - Lb) / 2.0)
    if depth is not None:
        out["m3"] = area * to_m(depth, unit)
    return out


def check_billed_end(billed_length_m, run, tol=LEN_TOL_M):
    """Compare a ledger's billed length with the drawn trapezoid (run from run_between_faces).

    PASS                 billed = mean edge length (both faces met)
    ONE_FACE_END         billed = the shorter (or longer) edge only while the edges differ: the triangle b|La-Lb|/2
                         is in no line (short) or billed twice (long); the correction is (mean - billed) x b x D
    MISMATCH             anything else: not explained by the end rule, reported, never silently corrected."""
    La, Lb, m = run["La_m"], run["Lb_m"], run["mean_length_m"]
    if billed_length_m is None:
        raise Refused("BILLED_LENGTH_MISSING")
    if abs(billed_length_m - m) <= tol:
        return dict(result="PASS", delta_length_m=0.0)
    if abs(La - Lb) > tol and min(abs(billed_length_m - La), abs(billed_length_m - Lb)) <= tol:
        return dict(result="ONE_FACE_END", delta_length_m=m - billed_length_m,
                    reason="billed to one edge's meeting point only; the run ends on the carrier face on BOTH edges "
                           "(R-BEAM-END-OBLIQUE-2)")
    return dict(result="MISMATCH", delta_length_m=m - billed_length_m,
                reason="billed length is neither the trapezoid mean nor one edge: investigate, not corrected here")


def accept_billed_end(billed_length_m, run, tol=LEN_TOL_M):
    """Refuses a one-face end (the adverse case); returns the PASS record otherwise."""
    c = check_billed_end(billed_length_m, run, tol)
    if c["result"] == "ONE_FACE_END":
        raise Refused("ONE_FACE_END: the run is billed to %.4f m (one edge) but its edges meet the carrier face at "
                      "%.4f / %.4f m (R-BEAM-END-OBLIQUE-2)" % (billed_length_m, run["La_m"], run["Lb_m"]))
    if c["result"] == "MISMATCH":
        raise Refused("LENGTH_MISMATCH: billed %.4f vs drawn mean %.4f m" % (billed_length_m, run["mean_length_m"]))
    return c


# ------------------------------------------------------------------------------------ R-BEAM-CURVED-AREA-2 (b)
def _norm_sweep(a0, a1):
    s = (a1 - a0) % 360.0
    return s if s > 1e-12 else 360.0


def _seg_ends(seg, unit):
    k = seg[0]
    if k == "line":
        return _pt(seg[1], unit), _pt(seg[2], unit)
    if k == "arc":
        _, c, R, a0, a1 = seg[:5]
        c, R = _pt(c, unit), to_m(R, unit)
        return ((c[0] + R * math.cos(math.radians(a0)), c[1] + R * math.sin(math.radians(a0))),
                (c[0] + R * math.cos(math.radians(a1)), c[1] + R * math.sin(math.radians(a1))))
    if k in ("chord", "band"):
        raise Refused("CURVED_MEMBER_AS_CHORDS: a curved edge given as %r pieces; the plan area is taken between "
                      "the member's own drawn arcs (R-BEAM-CURVED-AREA-2)" % k)
    raise Refused("SEGMENT_KIND_UNKNOWN: %r" % (k,))


def loop_area(segments, unit="m", gap_tol=GAP_TOL_M):
    """Exact area of one closed boundary made of ('line', p, q) and ('arc', centre, R, a_start_deg, a_end_deg[, 'cw'])
    pieces in boundary order (arcs counter-clockwise unless 'cw'). Area = shoelace over the piece end points + the
    circular segment of every arc (R^2 / 2 (theta - sin theta)), signed by the arc's sense against the loop's sense.
    No densification: an arc is an arc.

    Refused: a piece given as chords / bands (CURVED_MEMBER_AS_CHORDS), consecutive pieces that do not meet within
    gap_tol (LOOP_NOT_CLOSED). Returns (area_m2 > 0, max_gap_m)."""
    if not segments:
        raise Refused("LOOP_EMPTY")
    ends = [_seg_ends(s, unit) for s in segments]
    gap = 0.0
    for i in range(len(ends)):
        e0 = ends[i][1]
        s1 = ends[(i + 1) % len(ends)][0]
        g = math.hypot(s1[0] - e0[0], s1[1] - e0[1])
        if g > gap_tol:
            raise Refused("LOOP_NOT_CLOSED: piece %d ends %.4f m from piece %d" % (i, g, (i + 1) % len(ends)))
        gap = max(gap, g)
    verts = []
    for s, e in ends:
        verts.extend([s, e])
    # signed area of the region = signed shoelace of the chord polygon + the signed circular segment of every arc
    # (+ for an arc traversed counter-clockwise, - clockwise), whatever the loop's own sense
    poly = _shoelace(verts)
    seg_sum = 0.0
    for s in segments:
        if s[0] != "arc":
            continue
        R = to_m(s[2], unit)
        cw = len(s) > 5 and s[5] == "cw"
        th = math.radians(_norm_sweep(s[4], s[3]) if cw else _norm_sweep(s[3], s[4]))
        seg_sum += (-1.0 if cw else 1.0) * R * R / 2.0 * (th - math.sin(th))
    return abs(poly + seg_sum), gap


def curved_member_area(outer, voids=(), unit="m", annuli=(), b_schedule=None, width_tol=0.005):
    """Plan area of a curved / ring member between its own drawn edges.

    outer: the closed outer boundary (arcs + the faces of the members owning the crossings); voids: closed boundaries
    of the voids it surrounds (inside the outer boundary). annuli: (R_outer, R_inner) pairs of concentric drawn edges;
    each R_outer - R_inner is the drawn width, checked against b_schedule (two-source width; a difference above
    width_tol is a CONFLICT, refused here).

    Returns dict(area_m2, outer_m2, voids_m2, widths)."""
    A_out, g1 = loop_area(outer, unit)
    A_v = 0.0
    g = g1
    for v in voids:
        a, gv = loop_area(v, unit)
        A_v += a
        g = max(g, gv)
    if A_v >= A_out:
        raise Refused("VOID_NOT_INSIDE: the voids are not inside the outer boundary")
    widths = []
    for Ro, Ri in annuli:
        w = to_m(Ro, unit) - to_m(Ri, unit)
        if w <= 0:
            raise Refused("ANNULUS_INVERTED: outer radius not larger than inner")
        if b_schedule is not None and abs(w - to_m(b_schedule, unit)) > width_tol:
            raise Refused("WIDTH_CONFLICT: drawn ring width %.3f vs schedule %.3f m" % (w, to_m(b_schedule, unit)))
        widths.append(w)
    return dict(rule="R-BEAM-CURVED-AREA-2", area_m2=A_out - A_v, outer_m2=A_out, voids_m2=A_v, widths_m=widths,
                max_gap_m=g)


SLIVER_SHARE = 0.01      # other beams' band slivers inside a ring up to 1 % of its area (band fit at the shared
                         # faces) are a named residual; above it the area is a double count and refused


def ring_counted_once(ring_area_m2, replaced_band_m2, slab_ledger_in_ring_m2, other_beam_bands_in_ring_m2=0.0,
                      tol=AREA_TOL_M2):
    """Reconcile a ring once against the ledgers.

    replaced_band_m2: the ledger pieces (chord / arc bands) the ring row replaces (their area inside the ring);
    slab_ledger_in_ring_m2: area of the drawn ring that the slab ledger bills (C1: must be 0, else DOUBLE, refused);
    other_beam_bands_in_ring_m2: area of OTHER beams' bands inside the ring: fit slivers at the shared faces up to
    SLIVER_SHARE of the ring are returned as a named residual (never added, never silently dropped); above, refused.
    Returns the area the band set missed (ring - replaced), which the ring row adds."""
    if slab_ledger_in_ring_m2 > tol:
        raise Refused("RING_ALSO_IN_SLAB: %.4f m2 of the drawn ring is billed by the slab ledger; under C1 the beam "
                      "owns the ring (R-CONC-OWN-1); count it once" % slab_ledger_in_ring_m2)
    if other_beam_bands_in_ring_m2 > SLIVER_SHARE * ring_area_m2:
        raise Refused("RING_ALSO_IN_ANOTHER_BEAM: %.4f m2 of the ring lies in another beam's band"
                      % other_beam_bands_in_ring_m2)
    if replaced_band_m2 - ring_area_m2 > tol:
        raise Refused("BANDS_EXCEED_RING: the replaced bands (%.4f) are larger than the drawn ring (%.4f)"
                      % (replaced_band_m2, ring_area_m2))
    return dict(missed_m2=ring_area_m2 - replaced_band_m2, ring_m2=ring_area_m2, replaced_m2=replaced_band_m2,
                sliver_residual_m2=other_beam_bands_in_ring_m2)


# --------------------------------------------------------------------------------------------- ledger revision
def revise(rows, corrections):
    """Ledger r2 from r1 rows (dicts with run, storey, status, m3, m3_low, m3_high) and corrections:
    {'kind': 'replace_length', 'run': id, 'length_m', 'b', 'depth', 'basis'} or
    {'kind': 'supersede', 'runs': [ids], 'new': row-dict, 'basis'}.
    r1 rows are never edited in place: a superseded / corrected r1 row is carried with status SUPERSEDED_R2 and
    the replacement row is added (r2 id = r1 id + '.r2'), so both stay traceable. Every id must exist once."""
    by = {}
    for r in rows:
        if r["run"] in by:
            raise Refused("RUN_TWICE: %s" % r["run"])
        by[r["run"]] = r
    out = [dict(r) for r in rows]
    idx = {r["run"]: i for i, r in enumerate(out)}
    used = set()
    added = []
    for c in corrections:
        if c["kind"] == "replace_length":
            rid = c["run"]
            if rid not in idx or rid in used:
                raise Refused("CORRECTION_TARGET: %s missing or corrected twice" % rid)
            used.add(rid)
            old = out[idx[rid]]
            if old["status"] not in MEASURED:
                raise Refused("CORRECTION_ON_UNMEASURED: %s is %s" % (rid, old["status"]))
            new = dict(old)
            new.update(run=rid + ".r2", length_m=round(c["length_m"], 4), status="CALCULATED",
                       m3=round(c["length_m"] * c["b"] * c["depth"], 6), basis=c["basis"], supersedes=rid)
            new["m3_low"] = new["m3_high"] = new["m3"]
            old.update(status="SUPERSEDED_R2", superseded_by=new["run"])
            added.append(new)
        elif c["kind"] == "supersede":
            for rid in c["runs"]:
                if rid not in idx or rid in used:
                    raise Refused("CORRECTION_TARGET: %s missing or corrected twice" % rid)
                used.add(rid)
            new = dict(c["new"])
            new.setdefault("supersedes", "; ".join(c["runs"]))
            new["basis"] = c["basis"]
            for rid in c["runs"]:
                out[idx[rid]].update(status="SUPERSEDED_R2", superseded_by=new["run"])
            added.append(new)
        else:
            raise Refused("CORRECTION_KIND: %r" % c["kind"])
    out.extend(added)
    ids = [r["run"] for r in out]
    if len(ids) != len(set(ids)):
        raise Refused("RUN_TWICE after revision")
    return out


def totals(rows):
    """Per storey: measured m3, CONFLICT low .. high, HELD low .. high (+ ids with no value). SUPERSEDED_R2 rows are
    carried for traceability and counted nowhere; HELD is never 0."""
    t = {}
    for r in rows:
        s = t.setdefault(r["storey"], dict(n=0, measured_m3=0.0, conflict_n=0, conflict_low=0.0, conflict_high=0.0,
                                           held_n=0, held_low=0.0, held_high=0.0, held_no_value=[], superseded=0))
        st = r["status"]
        if st == "SUPERSEDED_R2":
            s["superseded"] += 1
            continue
        s["n"] += 1
        if st in MEASURED:
            if r.get("m3") is None:
                raise Refused("MEASURED_WITHOUT_VALUE: %s" % r["run"])
            s["measured_m3"] += r["m3"]
        elif st == "CONFLICT":
            s["conflict_n"] += 1
            s["conflict_low"] += r["m3_low"]
            s["conflict_high"] += r["m3_high"]
        elif st == "HELD":
            if r.get("m3") not in (None, ""):
                raise Refused("HELD_WITH_VALUE: %s" % r["run"])
            s["held_n"] += 1
            if r.get("m3_low") in (None, ""):
                s["held_no_value"].append(r["run"])
            else:
                s["held_low"] += r["m3_low"]
                s["held_high"] += r["m3_high"]
        else:
            raise Refused("STATUS_UNKNOWN: %s %r" % (r["run"], st))
    for s in t.values():
        for k in ("measured_m3", "conflict_low", "conflict_high", "held_low", "held_high"):
            s[k] = round(s[k], 6)
    return t
