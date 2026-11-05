"""LINTEL_BEARING_V2 (T-519, Checker finding F-C-T516-1): the jamb masonry reach with a LINEAR tolerance and a column
corner met inside the band classified COLUMN. Research only; successor of the reach / stopper step of
research/agents_t516/t516_extract.py (V1, left unchanged).

V1 accepted a strip [jamb, jamb +- e] x (full thickness - inset) as masonry when the area of the strip outside the
masonry was below EPS_AREA = 2e-5 m2. Against a POINTED column corner (a column drawn at 45 degrees) the intrusion is a
triangle whose area grows with the square of its depth d (d^2 for a right-angled corner), so V1 ran up to
sqrt(2e-5) = 4.5 mm into the column before stopping, and the point probe on the band axis just beyond the stop missed a
corner standing off the axis, calling the stopper END_OF_MASONRY instead of COLUMN (Checker: D-GF-11 START 0.831 vs own
0.827 m, stopper COL).

V2:
  ok(e)    every connected piece of (strip - masonry) has min(extent along the wall, extent across the wall) <= TOL_M
           (0.5 mm): a drafting hairline (nearly zero across, or nearly zero along) still closes, but any intrusion that
           is more than 0.5 mm both ways stops the strip. The tolerance is linear, so it does not depend on the wall
           thickness or on the shape of the intrusion.
  stopper  the slice [e, e + PROBE_M] across the full band (same inset) is tested against every column outline FIRST
           (any overlap with min extent > 0, i.e. a real area), then the opening gaps, so a column corner anywhere
           inside the band is COLUMN; an opening gap is OPENING; nothing -> END_OF_MASONRY (or SEARCH_LIMIT).
Expected effect on the training villa (from the Checker's own re-measure, not re-run here): one end moves in value,
none in state: D-GF-11 START 0.831 -> 0.827 m, stopper END_OF_MASONRY -> COLUMN, state BOUNDED unchanged; the lintel's
hard length ceiling 1.869 -> 1.865 m. No other end lies within 5 mm of the 0.40 m minimum, so no state can move.
"""
from __future__ import annotations

from shapely.geometry import Polygon
from shapely.ops import unary_union

VERSION = "LINTEL_BEARING_V2"
TOL_M = 0.0005
INSET = 0.0005
PROBE_M = 0.003
SEARCH_M = 3.0


def strip(a, ux, uy, s0, s1, half):
    nx, ny = -uy, ux
    p = lambda s, o: (a[0] + ux * s + nx * o, a[1] + uy * s + ny * o)
    return Polygon([p(s0, -half), p(s1, -half), p(s1, half), p(s0, half)])


def _pieces(g):
    if g.is_empty:
        return []
    return list(getattr(g, "geoms", [g]))


def extents(piece, a, ux, uy):
    """(extent along the wall axis, extent across it) of one polygon piece, in metres."""
    pts = list(piece.exterior.coords) if hasattr(piece, "exterior") else list(piece.coords)
    s = [(x - a[0]) * ux + (y - a[1]) * uy for x, y in pts]
    n = [-(x - a[0]) * uy + (y - a[1]) * ux for x, y in pts]
    return max(s) - min(s), max(n) - min(n)


def missing_ok(missing, a, ux, uy, tol=TOL_M):
    """True when every connected piece of the non-masonry part is a hairline (<= tol in one direction)."""
    return all(min(extents(p, a, ux, uy)) <= tol for p in _pieces(missing) if p.area > 0)


def reach(M, a, ux, uy, jamb, sign, half, search=SEARCH_M, tol=TOL_M):
    """largest e (to 0.01 mm) with the strip [jamb, jamb + sign e] x (half - INSET) inside M up to the linear tolerance;
    -> (e, capped)."""
    def missing(e):
        s0, s1 = min(jamb, jamb + sign * e), max(jamb, jamb + sign * e)
        return strip(a, ux, uy, s0, s1, half - INSET).difference(M)

    def ok(e):
        return missing_ok(missing(e), a, ux, uy, tol)
    if ok(search):
        return search, True
    lo, hi = 0.0, search
    if ok(1e-4):
        while hi - lo > 1e-5:
            mid = (lo + hi) / 2
            lo, hi = (mid, hi) if ok(mid) else (lo, mid)
    # the tolerance must not lengthen the reach: a non-masonry piece touching the leading edge is the START of the
    # obstruction (column face / corner, wall end, gap), so the reach ends where that piece begins
    lead = []
    for p in _pieces(missing(max(lo, 1e-4))):
        if p.area <= 0:
            continue
        s = [((x - a[0]) * ux + (y - a[1]) * uy - jamb) * sign for x, y in p.exterior.coords]
        if max(s) >= max(lo, 1e-4) - 1e-7 and extents(p, a, ux, uy)[1] > tol:   # lengthwise hairlines excluded
            lead.append(min(s))
    return (max(0.0, min(lead)) if lead else lo), False


def stopper(e, capped, a, ux, uy, jamb, sign, half, columns, gaps):
    """what lies just beyond the reach: COLUMN (any column outline inside the band slice), OPENING <id>, END_OF_MASONRY
    or SEARCH_LIMIT. gaps: [(id, polygon)]."""
    if capped:
        return "SEARCH_LIMIT", ""
    s0, s1 = sorted((jamb + sign * e, jamb + sign * (e + PROBE_M)))
    probe = strip(a, ux, uy, s0, s1, half - INSET)
    if columns and probe.intersection(unary_union(columns)).area > 1e-12:
        return "COLUMN", ""
    for gid, g in gaps:
        if probe.intersection(g).area > 1e-12:
            return "OPENING", gid
    return "END_OF_MASONRY", ""


EXPECTED_TRAINING_VILLA_MOVES = [
    {"opening_id": "D-GF-11", "side": "START", "v1_available_m": 0.831, "v2_available_m": 0.827,
     "v1_stopper": "END_OF_MASONRY", "v2_stopper": "COLUMN", "state_v1": "BOUNDED", "state_v2": "BOUNDED",
     "length_hi_v1_m": 1.869, "length_hi_v2_m": 1.865,
     "source": "Checker own re-measure, T-516 verdict (F-C-T516-1): column corner vertex s = 1746.5 mm, n = +35 mm, "
               "S-COL.BON 2F8D drawn at 45 degrees",
     "status": "EXPECTED, NOT RE-RUN (the DXF chain needs research scripts the run wrapper refuses)"},
]
