"""T-660 rules (research, unwired): a HELD beam piece restated member by member from what the structural drawings print,
for any villa. Builds on R-T402-1 .. 6 (T-402, merged) and owner Q-61 answer C (member by member).

R-T660-1 VALUE ONLY FROM A PRINTED SECTION ON THE PIECE. A held piece takes ONE value only when a section cut crosses
    it and the section prints its depth by dimensions that close the outline (R-T402-6); a rounded corner is deducted
    only when both extents are dimensioned. The width is the plan's drawn edge distance where the section leaves the
    width undimensioned (a scaled section width is an indication, never a quantity); the length is face to face of the
    drawn supports. V = (b x D - r^2 (1 - pi/4)) x L.
R-T660-2 UNLABELLED PIECE: SCHEDULE ENVELOPE OF ITS DRAWN WIDTH. A piece drawn between beam edge lines with no mark is
    bounded by the smallest and largest scheduled depth among the schedule rows whose breadth equals its drawn width
    (never another width's rows, never the neighbour's section, Q-61 C(4)); no row of that width -> no bound (HELD
    blank). A bound, never its midpoint, never the freelancer's borrowed section.
R-T660-3 EDGE STRIP / PROJECTION IS NOT BOUNDED FROM THE BEAM SCHEDULE. A strip outside the outer face of a scheduled
    beam, with no mark, no bar and no printed depth, which a section cut crosses without drawing it (the section's
    outline ends at the beam face), is HELD with its plan area and NO m3 bound (the beam schedule envelope is not a
    property of a projection: R-T402-4). Where the slab plans refer parapets / projections to the architectural
    detail, the strip is listed beside the parapet family with a guard: it may be valued in ONE family only.
R-T660-4 TWO MARKS ON ONE SPAN. Bounded by the two scheduled sections, never their sum (Q-61 C(2)); the schedule's
    printed span list is compared with the drawn spans centre to centre and reported as evidence for the Checker; the
    comparison never selects a reading by itself.
R-T660-5 WIDTH CONFLICT WITH ITS SLAB PAIRING. A schedule-vs-drawn width conflict is carried as the pair of readings
    (Q-61 C(1)), with the net concrete shift (beam change less the slab strip the other reading gives up or must take,
    R-T402-5 r2) beside it; the beam bound alone is never added to a slab measured net of the drawn faces.
R-T660-6 ONCE. Every held line id appears once; a valued piece's plan rectangle intersects no column outline and no
    other valued piece; HELD is never 0; low <= high; lengths and levels in m (a value above 50 reads as mm: refused).

Provenance: T-660 (2026-11-09, worker 1), on R-T402-1 .. 6, R-T642, owner Q-61 C, Q-44 A, ERS s.2 - 5.
Scope: every villa (the Alsenan figures are one application).
"""
from __future__ import annotations

import math
from decimal import Decimal

Q6 = Decimal("0.000001")


class Refused(ValueError):
    """A reading the rules refuse."""


def _m(v, what):
    if v is None:
        raise Refused(f"{what} not printed / not drawn: HELD, never 0")
    d = Decimal(str(v))
    if d <= 0:
        raise Refused(f"{what} {v}: not positive")
    if d > 50:
        raise Refused(f"{what} {v}: dimensions in m (a value above 50 reads as mm)")
    return d


def value_from_section(*, width_plan, depth_chain, length_f2f, round_extents=None, section_crosses_piece=True,
                       chain_closes_outline=True):
    """R-T660-1: one value from a printed section on the piece."""
    if not section_crosses_piece:
        raise Refused("no section cut crosses the piece: no value (bound or hold)")
    if not depth_chain:
        raise Refused("section prints no depth dimension: no value")
    if not chain_closes_outline:
        raise Refused("printed depth chain does not close the section outline: no value")
    b = _m(width_plan, "plan width")
    D = sum((_m(x, "depth term") for x in depth_chain), Decimal(0))
    L = _m(length_f2f, "face-to-face length")
    a = b * D
    if round_extents is not None:
        h, v = (_m(x, "round extent") for x in round_extents)
        if h != v:
            raise Refused("round extents differ: not a quarter circle, no deduction rule")
        a -= h * h * (Decimal(1) - Decimal(str(math.pi)) / 4)
    return (a * L).quantize(Q6)


def schedule_envelope(drawn_width, length_f2f, schedule_rows):
    """R-T660-2: (low, high) over the rows of the drawn width, or None when no row has that width."""
    b = _m(drawn_width, "drawn width")
    L = _m(length_f2f, "face-to-face length")
    depths = sorted({_m(d, "row depth") for (w, d) in schedule_rows if _m(w, "row width") == b})
    if not depths:
        return None
    return ((b * depths[0] * L).quantize(Q6), (b * depths[-1] * L).quantize(Q6))


def projection_strip(plan_area, *, has_mark=False, has_bars=False, printed_depth=None, section_draws_it=False):
    """R-T660-3: a projection strip is HELD with plan area; a printed depth (or a section that draws it) is required."""
    if has_mark or has_bars or printed_depth is not None or section_draws_it:
        raise Refused("not a bare projection: measure it as the member it is printed as")
    return {"status": "HELD_NO_DRAWN_DEPTH", "plan_area_m2": str(_m(plan_area, "plan area").quantize(Q6)),
            "m3_low": None, "m3_high": None, "guard": "valued in ONE family only (beam or parapet)"}


def two_marks(m3_a, m3_b):
    """R-T660-4: bound of the two readings; their sum is refused."""
    a, b = Decimal(str(m3_a)), Decimal(str(m3_b))
    if a <= 0 or b <= 0:
        raise Refused("a reading is not positive")
    return (min(a, b).quantize(Q6), max(a, b).quantize(Q6))


def span_crosscheck(printed_spans, drawn_cc_spans, tol=Decimal("0.10")):
    """R-T660-4 evidence: per span |printed - drawn c/c|, and whether the counts agree; never a selection."""
    p = [Decimal(str(x)) for x in printed_spans]
    d = [Decimal(str(x)) for x in drawn_cc_spans]
    if len(p) != len(d):
        return {"count_agrees": False, "diffs": None, "within_tol": None}
    diffs = [(y - x).quantize(Decimal("0.001")) for x, y in zip(p, d)]
    return {"count_agrees": True, "diffs": [str(x) for x in diffs], "within_tol": [abs(x) <= tol for x in diffs]}


def net_shift(beam_low, beam_high, slab_strip_low, slab_strip_high, wider_reading_is_schedule):
    """R-T660-5: concrete total shift schedule - drawn = beam change -/+ slab strip (overlap / gap), as a bound."""
    db = Decimal(str(beam_high)) - Decimal(str(beam_low))
    s_lo, s_hi = Decimal(str(slab_strip_low)), Decimal(str(slab_strip_high))
    if s_lo > s_hi:
        raise Refused("slab strip low > high")
    if wider_reading_is_schedule:      # schedule wider: the slab gives up the overlap
        lo, hi = db - s_hi, db - s_lo
    else:                              # schedule narrower: the slab must take the gap
        lo, hi = -db + s_lo, -db + s_hi
    return (lo.quantize(Q6), hi.quantize(Q6))


def rect_overlap(a, b):
    """Plan rectangles (x0, x1, y0, y1) in m: True when their interiors intersect."""
    return min(a[1], b[1]) > max(a[0], b[0]) and min(a[3], b[3]) > max(a[2], b[2])


def check_once(rows):
    """R-T660-6: ids once; HELD never 0; low <= high."""
    ids = [r["line_id"] for r in rows]
    if len(ids) != len(set(ids)):
        raise Refused("a line id appears twice")
    for r in rows:
        if r["status"].startswith("HELD"):
            if r.get("m3_value") not in (None,):
                raise Refused(f"{r['line_id']}: a HELD line carries a value")
            lo, hi = r.get("m3_low"), r.get("m3_high")
            if lo is not None and Decimal(lo) == 0 and (hi is None or Decimal(hi) == 0):
                raise Refused(f"{r['line_id']}: HELD closed as 0")
            if lo is not None and hi is not None and Decimal(lo) > Decimal(hi):
                raise Refused(f"{r['line_id']}: low > high")
    return True
