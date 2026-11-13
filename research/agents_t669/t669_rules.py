"""T-669 rules (research, unwired): owner of an exterior corner square with no column, and the drawn lower end of a
roof-storey column. Any villa.

R-T669-1 CORNER SQUARE WITH NO COLUMN (completes R-T666-1 at an L / T corner of two runs). Where two beam runs meet
    and the square they share (run widths in plan) holds no column, exactly one run owns it, read from the drawn
    outlines:
    (a) COLUMN: a column outline contains the square -> the column owns it (R-T666-1 (a), UP-CONC-JOINT-001).
    (b) DRAWN OUTLINE: a run owns the square when BOTH of its edge lines are drawn across the whole square (its outer
        and inner face lines continue to the other run's outer line), while the other run's inner face line stops at
        the owner's inner face. The owner's measured length then runs to the outer face (the square is added to its
        span); the other run stops at the owner's inner face (unchanged).
    (c) Refused (HELD, owner not guessed): no run draws both edges across the square (closed separately or undrawn),
        both do (two owners), or a run covers it only in part. The square stays named beside both runs as an exposure
        A x the floor depth, never 0 and never counted twice.
    The quantity follows the owner's own depth basis (its title, floor or bound); a square never takes the larger of
    the two runs' depths because it is larger.
R-T669-2 ROOF-STOREY COLUMN LOWER END. Where the roof slab-top level is not printed (only a finished mark above an
    unprinted build-up), the column's top (it owns its section to the slab top, UP-CONC-JOINT-001) is still bounded
    BELOW by what the drawings fix under the same slab:
        top >= highest printed opening top (head / arch apex) under that slab + least printed thickness of that slab,
    because the opening and then the whole slab depth sit below the slab top. Height low = that top - the column base
    (a printed or an approved datum; the highest admissible base for a low end). Low m3 = least drawn / scheduled
    section x height low. Admissible only when (i) the opening top is printed (a level or a printed chain from a
    printed level, not scaled), (ii) the slab thickness is printed on the slab plan, (iii) the roof is one drawn slab
    plane over the opening and the column (section draws one continuous slab top, the slab plan prints no step or
    level change), (iv) the base is fixed. Otherwise refused: the lower end stays open BY NAME (which print is
    missing), never a generic storey or build-up value. A low above the ceiling (finished mark - base) is a conflict:
    refused, HELD.

Provenance: T-669 (2026-11-10, worker 1) on Checker F-T665-1 (T-665 Gate B verdict) and the 6 UPPER_ONLY roof columns
of V3.0.63 (R-T658-4); UP-CONC-JOINT-001, R-T666-1, R-CONC-OWN-1 1.0.0-proposed, D-39, Q-54 B, ERS s.2.4. Scope: every
villa (the Alsenan figures are one application).
"""
from __future__ import annotations

from decimal import Decimal

Q6 = Decimal("0.000001")


class Refused(ValueError):
    """A reading the rules refuse (the quantity stays HELD, never 0)."""


def _d(v, what, allow_zero=False, limit=Decimal(50)):
    if v is None:
        raise Refused(f"{what} not printed / not drawn: HELD, never 0")
    d = Decimal(str(v))
    if d < 0 or (d == 0 and not allow_zero):
        raise Refused(f"{what} {v}: not positive")
    if limit is not None and d > limit:
        raise Refused(f"{what} {v}: dimensions in m (a value above {limit} reads as mm)")
    return d


def _box(b, what):
    if b is None or len(b) != 4:
        raise Refused(f"{what}: outline not drawn")
    x0, y0, x1, y1 = (Decimal(str(v)) for v in b)
    if x1 <= x0 or y1 <= y0:
        raise Refused(f"{what}: empty outline")
    return x0, y0, x1, y1


def _inside(a, b, tol):
    return a[0] >= b[0] - tol and a[1] >= b[1] - tol and a[2] <= b[2] + tol and a[3] <= b[3] + tol


def _overlap(a, b):
    return min(a[2], b[2]) > max(a[0], b[0]) and min(a[3], b[3]) > max(a[1], b[1])


def both_edges_box(axis, outer, inner):
    """The plan box where BOTH edge lines of a run are drawn: axis 'x' (edges horizontal: (y, x0, x1)) or 'y' (edges
    vertical: (x, y0, y1)). Returns None when the two edges share no common extent."""
    c_o, a_o, b_o = (Decimal(str(v)) for v in outer)
    c_i, a_i, b_i = (Decimal(str(v)) for v in inner)
    a, b = max(min(a_o, b_o), min(a_i, b_i)), min(max(a_o, b_o), max(a_i, b_i))
    if b <= a or c_o == c_i:
        return None
    lo, hi = min(c_o, c_i), max(c_o, c_i)
    return (a, lo, b, hi) if axis == "x" else (lo, a, hi, b)


def corner_owner(square, *, runs, columns=(), tol="0.001"):
    """R-T669-1: (kind, owner id) of a corner square; runs = [(id, both_edges_box or None)], columns = [(id, box)]."""
    sq = _box(square, "corner square")
    t = Decimal(tol)
    for cid, cb in columns:
        bb = _box(cb, f"column {cid}")
        if _inside(sq, bb, t):
            return ("COLUMN", cid)
        if _overlap(sq, bb):
            raise Refused(f"PARTIAL: square only partly inside column {cid}: HELD")
    owners, partial = [], []
    for rid, rb in runs:
        if rb is None:
            continue
        bb = _box(rb, f"run {rid}")
        if _inside(sq, bb, t):
            owners.append(rid)
        elif _overlap(sq, bb):
            partial.append(rid)
    if partial:
        raise Refused(f"PARTIAL: square only partly inside run(s) {partial}: owner not established, HELD")
    if len(owners) > 1:
        raise Refused(f"DOUBLE: both runs {owners} draw both edges across the square: HELD")
    if not owners:
        raise Refused("NONE: no run draws both edges across the square: owner not read, HELD (exposure beside both)")
    return ("RUN", owners[0])


def span_with_square(span, square_side):
    """R-T669-1 (b): the owner's span grows by the square it owns."""
    return _d(span, "measured span") + _d(square_side, "square side")


def prism(length, width, depth):
    return (_d(length, "length") * _d(width, "width") * _d(depth, "depth")).quantize(Q6)


def column_low(*, section_min, base, opening_top, slab_t_min, finished_top, single_plane, base_fixed=True):
    """R-T669-2: (height_low, m3_low, height_ceiling) or Refused with the missing print named."""
    if not single_plane:
        raise Refused("roof slab not one drawn plane over the opening and the column: lower end open (no transfer)")
    if not base_fixed:
        raise Refused("column base not fixed (planted / unprinted base): lower end open")
    s = _d(section_min, "least section m2")
    b = _d(base, "base level", allow_zero=True, limit=Decimal(200))
    o = _d(opening_top, "printed opening top under the slab", limit=Decimal(200))
    tt = _d(slab_t_min, "printed slab thickness")
    f = _d(finished_top, "finished roof mark", limit=Decimal(200))
    if tt > 1:
        raise Refused(f"slab thickness {slab_t_min} m: not a slab")
    h_low = o + tt - b
    h_ceiling = f - b
    if h_low <= 0:
        raise Refused("opening top + slab below the base: wrong storey")
    if h_low > h_ceiling:
        raise Refused(f"CONFLICT: low {h_low} above the ceiling {h_ceiling}: HELD")
    return h_low, (s * h_low).quantize(Q6), h_ceiling
