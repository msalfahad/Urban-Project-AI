"""T-658 rules (research, unwired): HELD column, ground-beam, strap and footing concrete lines restated member by
member from what the drawings print, for any villa.

R-T658-1 OVERLAPPING LENGTH TITLES GIVE A RANGE, NEVER A PICKED END. Where a sheet prints ground-beam sections by span
    title ('less than 2.5 m', 'less than 5 m', 'more than 5 m') with no precedence, every title whose condition holds
    literally on the member's span is a reading: the bound runs from the smallest to the largest of those sections x the
    span. A held line that shows one end as a point (low == high) while a second title also holds understates the bound.
R-T658-2 ON THE LIMIT, BOTH ADJACENT TITLES. A span exactly on a printed limit (5.00 m against 'less than 5 m' / 'more
    than 5 m') satisfies neither title literally: the bound is the two adjacent printed sections x the span, flagged
    ON_LIMIT; never one of them as a value.
R-T658-3 A LITERAL TWO-LEVEL READING THAT CANNOT HOLD THE PRINTED SECTION IS A FLOOR ONLY. When a member is printed
    between two levels (top = a printed structural level, underside 'outer natural ground') and the designer item says the
    resulting depth cannot hold the printed section, the member is at least that deep: LOWER_ONLY, the literal reading as
    the floor, the high blank with the item named. Never the value, never a borrowed depth from another zone.
R-T658-4 A FINISHED-LEVEL MARK IS A CEILING FOR A COLUMN WHOSE SLAB-TOP DATUM IS NOT PRINTED. Column top = slab top <=
    the finished level drawn above it (build-up >= 0): h_max = mark - base (both printed); with one printed section the
    line gets UPPER_ONLY section x h_max; the low stays blank (build-up not printed). A column with a section CONFLICT
    whose second reading is not in the committed record, or whose top may rise above the mark (an upstand tank beam,
    D-44 type item), keeps HELD blank with the item named.
R-T658-5 SCHEDULE VS PLAN: HOLD BOTH. A printed schedule section and a drawn plan outline that differ give a CONFLICT
    range (smaller .. larger reading x height); the schedule is not picked because it is printed (owner answer: hold as
    conflict, member by member). A single reading never closes the range.
R-T658-6 HELD NEVER 0. A blank line names its item; a low of 0 only where the open question is whether a separate solid
    exists at all (an in-footing strap piece); totals only over lines that carry the end in question.

Provenance: T-658 (2026-11-09), on D-33, D-34, D-35, D-39, D-44, D-66, Q-54 B, Q-74, R-T572-1..4, R-GB-EXT-DEPTH-1,
R-COL-SECTION-CONFLICT-1. Scope: every villa.
"""
from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

Q6 = Decimal("0.000001")
STATUSES = ("VALUED", "BOUNDED", "LOWER_ONLY", "UPPER_ONLY", "HELD_BLANK")
D = Decimal


class Refused(ValueError):
    """A reading the rules refuse."""


def d6(x) -> Decimal:
    if x is None:
        raise Refused("missing value: carry it HELD with its item, never 0")
    if isinstance(x, bool):
        raise Refused("not a quantity")
    if isinstance(x, str) and x.strip().lower().endswith("mm"):
        raise Refused("lengths in m only (mm refused)")
    v = D(str(x))
    if v < 0:
        raise Refused("negative quantity")
    return v.quantize(Q6, rounding=ROUND_HALF_UP)


def m(x, source: str) -> Decimal:
    """A dimension in metres with its printed / committed source."""
    if not source or not str(source).strip():
        raise Refused("a dimension needs its source")
    v = d6(x)
    if v == 0:
        raise Refused("a zero dimension is not a member")
    if v > 200:
        raise Refused("dimension above 200 m: unit slip (mm?)")
    return v


# ------------------------------------------------------------------------------------------- R-T658-1 / R-T658-2
def titles_holding(span: Decimal, titles):
    """titles: [(name, op, limit_m, (b, d))], op in '<', '>'. Returns (holding titles, on_limit)."""
    hold, on_limit = [], False
    for name, op, lim, sec in titles:
        lim = D(str(lim))
        if span == lim:
            on_limit = True
            continue
        if (op == "<" and span < lim) or (op == ">" and span > lim):
            hold.append((name, sec))
    return hold, on_limit


def span_range(span, titles, src: str):
    """R-T658-1 / -2: (low, high, basis, flags) for one ground-beam span over the printed length titles."""
    L = m(span, src)
    hold, on_limit = titles_holding(L, titles)
    flags = []
    if on_limit:
        lim = [D(str(t[2])) for t in titles if D(str(t[2])) == L][0]
        adj = [t for t in titles if D(str(t[2])) == lim]
        secs = [t[3] for t in adj]
        flags.append("ON_LIMIT")
    else:
        if not hold:
            raise Refused("no printed title holds on this span: HELD blank, name the item")
        secs = [s for _, s in hold]
        if len(secs) > 1:
            flags.append("TITLES_OVERLAP")
    vols = sorted(d6(D(str(b)) * D(str(d)) * L) for b, d in secs)
    return vols[0], vols[-1], flags


# ------------------------------------------------------------------------------------------------ R-T658-3
def literal_floor(runs, b, top_level, underside_level, src: str):
    """Sum over runs of L x b x (top - underside): the LOWER_ONLY floor of a member whose literal depth is too shallow
    for its printed section (R-T658-3)."""
    depth = d6(D(str(top_level)) - D(str(underside_level)))
    if depth <= 0:
        raise Refused("top at or below the underside: no literal reading")
    bb = m(b, src)
    return d6(sum((m(L, src) * bb * depth for L in runs), D(0)))


# ------------------------------------------------------------------------------------------------ R-T658-4
def column_ceiling(section_m2, base_level, mark_level, *, top_may_exceed_mark=False, second_reading_unknown=False):
    """UPPER_ONLY ceiling (section x (mark - base)) or None when R-T658-4 refuses it."""
    if top_may_exceed_mark or second_reading_unknown:
        return None
    h = d6(D(str(mark_level)) - D(str(base_level)))
    if h <= 0:
        raise Refused("mark at or below the base")
    return d6(D(str(section_m2)) * h)


# ------------------------------------------------------------------------------------------------ R-T658-5
def conflict_range(readings_m2, h):
    """R-T658-5: schedule vs plan readings x height; one reading is refused as a range."""
    rs = sorted({D(str(r)) for r in readings_m2})
    if len(rs) < 2:
        raise Refused("one reading is not a conflict range")
    hh = d6(h)
    return d6(rs[0] * hh), d6(rs[-1] * hh)


# ------------------------------------------------------------------------------------------------ rows
def row(line_id, item_code, element_id, status, *, low=None, high=None, before=(None, None), basis="", item=None,
        flags=()):
    if status not in STATUSES:
        raise Refused(f"status {status}")
    lo = None if low is None else d6(low)
    hi = None if high is None else d6(high)
    if status == "BOUNDED" and (lo is None or hi is None or lo > hi):
        raise Refused(f"{line_id}: BOUNDED needs low <= high")
    if status == "LOWER_ONLY" and (lo is None or hi is not None or not item):
        raise Refused(f"{line_id}: LOWER_ONLY needs a low, no high, a named item")
    if status == "UPPER_ONLY" and (hi is None or lo is not None or not item):
        raise Refused(f"{line_id}: UPPER_ONLY needs a high, no low, a named item")
    if status == "HELD_BLANK" and (lo is not None or hi is not None or not item):
        raise Refused(f"{line_id}: HELD_BLANK carries no figure and names its item")
    if lo == 0 and "EXISTENCE_OPEN" not in flags:
        raise Refused(f"{line_id}: a low of 0 only when the solid's existence is the open question")
    b = [None if x is None else str(d6(x)) for x in before]
    return {"line_id": line_id, "item_code": item_code, "element_id": element_id, "status": status,
            "low": None if lo is None else str(lo), "high": None if hi is None else str(hi),
            "before_low": b[0], "before_high": b[1], "basis": basis, "item": item, "flags": list(flags)}


def totals(rows):
    out = {}
    for ic in sorted({r["item_code"] for r in rows}):
        rs = [r for r in rows if r["item_code"] == ic]
        bnd = [r for r in rs if r["status"] in ("BOUNDED", "VALUED")]
        out[ic] = {
            "lines": len(rs),
            "bounded": len(bnd),
            "bounded_low": str(sum((D(r["low"]) for r in bnd), D(0)).quantize(Q6)),
            "bounded_high": str(sum((D(r["high"]) for r in bnd), D(0)).quantize(Q6)),
            "lower_only": sum(1 for r in rs if r["status"] == "LOWER_ONLY"),
            "lower_only_floor": str(sum((D(r["low"]) for r in rs if r["status"] == "LOWER_ONLY"), D(0)).quantize(Q6)),
            "upper_only": sum(1 for r in rs if r["status"] == "UPPER_ONLY"),
            "upper_only_ceiling": str(sum((D(r["high"]) for r in rs if r["status"] == "UPPER_ONLY"),
                                          D(0)).quantize(Q6)),
            "blank": sum(1 for r in rs if r["status"] == "HELD_BLANK"),
            "before_bounded": sum(1 for r in rs if r["before_low"] is not None),
            "before_low": str(sum((D(r["before_low"]) for r in rs if r["before_low"] is not None), D(0)).quantize(Q6)),
            "before_high": str(sum((D(r["before_high"]) for r in rs if r["before_high"] is not None),
                                   D(0)).quantize(Q6)),
            "total": None}
    return out
