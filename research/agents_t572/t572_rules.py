"""T-572 rules (research, unwired): every HELD structural component given the bound the drawings alone support, or the
named item that prevents one; like-for-like comparison against a freelancer only on the measured set, for any villa.

R-T572-1 BOUND OR BLOCKER, PER COMPONENT. A held component (element id, family, unit) carries a LOW and a HIGH end, each
    either a number with its drawn basis or None with the named item (designer / owner / RFI id) that prevents it. Kinds:
    BOUNDED (both ends), LOWER_ONLY, UPPER_ONLY, UNBOUNDED (neither; the item is required) and NOT_PRESENT_PROPOSED
    (the drawings say the element does not exist; carried apart, never as 0 m3 of a held line). A basis that is a
    generic / default / typical convention, a borrowed value or a freelancer figure is refused: such a range is
    reported beside as CANDIDATE_RANGE_NOT_DRAWN, never as the bound. A low end of 0 is allowed only when the open
    question is whether the element exists at all (existence_open=True).
R-T572-2 HEIGHT BETWEEN TWO STRUCTURAL DATUMS. A vertical element's height is top - bottom of two structural datums
    (R-NECK-ENDS-1, R-T394-1). With both printed (or drawing-confirmed) the element is BOUNDED at one value. With a
    printed MINIMUM depth only (e.g. 'excavation not less than 1.50 m below the plot level') the bound is one-sided:
    neck h >= top_low + min_depth - printed stack below the footing - H_max; the deeper end stays open on the formation
    item. Each end takes the reading that keeps the bound valid under every open reading: the lowest drawn top, the
    largest candidate footing depth, the smallest candidate section. A depth that is not printed (a default or typical
    depth) is refused.
R-T572-3 HELD NEVER SUMS AS 0. A family total is stated as valued + [sum of lows, sum of highs] ONLY when every held
    component is bounded on that side; otherwise that side is None ('not stateable') and the bounded part is reported
    with the count of components that block it. Bounds and valued figures are added in one unit only (m3 with m3).
R-T572-4 LIKE-FOR-LIKE ON THE MEASURED SET. A percentage engine vs freelancer is computed only over components valued on
    the engine side AND present in his rows, same unit; NO_ROW is never 0 and gives no percentage; m3 is never compared
    with m2 (or kg). For a held family with a drawn one-sided bound his figure is classed against that end
    (BELOW_DRAWN_LOWER / WITHIN / ABOVE_DRAWN_UPPER), information for the Checker, never a reason to release.

Provenance: T-572 (2026-11-06), on R-T547-1 (bound every HELD element before any %), R-T551-1 .. 4, R-T565-1 .. 4,
R-T566-1 .. 5, R-NECK-ENDS-1 (T-205), T-214 (GF structural top +0.95), T-287 (annex base +0.25). Scope: every villa.
"""
from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

Q6 = Decimal("0.000001")
KINDS = ("BOUNDED", "LOWER_ONLY", "UPPER_ONLY", "UNBOUNDED", "NOT_PRESENT_PROPOSED")
REFUSED_BASIS = ("GENERIC", "DEFAULT", "ASSUMED", "BORROWED", "FREELANCER")
UNITS = ("m3", "m2", "m", "nr", "kg")


class Refused(ValueError):
    """A reading the rules refuse."""


def d6(x) -> Decimal:
    if x is None:
        raise Refused("missing value: carry it HELD with its item, never 0")
    if isinstance(x, bool):
        raise Refused("not a quantity")
    if isinstance(x, str):
        s = x.strip().lower()
        if s.endswith("%"):
            raise Refused("a percentage is not a quantity")
        if s.endswith("mm"):
            raise Refused("lengths in m only (mm refused)")
    v = Decimal(str(x))
    if v < 0:
        raise Refused("negative quantity")
    return v.quantize(Q6, rounding=ROUND_HALF_UP)


def _check_basis(basis):
    if not basis or not str(basis).strip():
        raise Refused("a bound end needs its drawn basis")
    up = str(basis).upper()
    for w in REFUSED_BASIS:
        if w in up:
            raise Refused(f"basis '{basis}' is not drawing evidence ({w}): report it beside, never as the bound")


def component(element_id, family, unit, low=None, high=None, low_basis=None, high_basis=None, low_item=None,
              high_item=None, existence_open=False, not_present_basis=None, candidate_range=None, flags=()):
    """R-T572-1: one held component with its bound or blocker."""
    if unit not in UNITS:
        raise Refused(f"unit {unit!r}")
    if not element_id:
        raise Refused("a component is named by its element id")
    rec = {"element_id": element_id, "family": family, "unit": unit, "flags": list(flags)}
    if candidate_range is not None:
        rec["candidate_range_not_drawn"] = [str(d6(candidate_range[0])), str(d6(candidate_range[1]))]
    if not_present_basis:
        if low is not None or high is not None:
            raise Refused("a NOT_PRESENT element carries no bound")
        rec.update(kind="NOT_PRESENT_PROPOSED", low=None, high=None, basis=not_present_basis)
        return rec
    lo = hi = None
    if low is not None:
        _check_basis(low_basis)
        lo = d6(low)
        if lo == 0 and not existence_open:
            raise Refused("a low end of 0 only when the element's existence is the open question")
    elif not low_item:
        raise Refused(f"{element_id}: no low end and no named item")
    if high is not None:
        _check_basis(high_basis)
        hi = d6(high)
    elif not high_item:
        raise Refused(f"{element_id}: no high end and no named item")
    if lo is not None and hi is not None and lo > hi:
        raise Refused(f"{element_id}: low {lo} > high {hi}")
    kind = ("BOUNDED" if lo is not None and hi is not None else "LOWER_ONLY" if lo is not None
            else "UPPER_ONLY" if hi is not None else "UNBOUNDED")
    rec.update(kind=kind, low=None if lo is None else str(lo), high=None if hi is None else str(hi),
               low_basis=low_basis if lo is not None else None, high_basis=high_basis if hi is not None else None,
               low_item=None if lo is not None else low_item, high_item=None if hi is not None else high_item)
    return rec


def height_between(top, bottom, top_basis, bottom_basis):
    """R-T572-2, both ends printed: one value."""
    if top is None or bottom is None:
        raise Refused("an end datum is not printed: HELD with its item")
    _check_basis(top_basis)
    _check_basis(bottom_basis)
    t, b = Decimal(str(top)), Decimal(str(bottom))
    if t <= b:
        raise Refused("top datum not above the bottom datum")
    return (t - b).quantize(Q6)


def neck_low_height(top_low, min_depth, stack, H_candidates, depth_printed=True):
    """R-T572-2, printed minimum only: h >= top_low + min_depth - stack - max(H)."""
    if min_depth is None:
        raise Refused("no printed founding / excavation depth: HELD with the formation item")
    if not depth_printed:
        raise Refused("a default or typical founding depth is not a drawn bound")
    if not H_candidates or any(h is None for h in H_candidates):
        raise Refused("footing depth not printed: HELD with the footing item")
    for v in (top_low, min_depth, stack, *H_candidates):
        if Decimal(str(v)) > 50:
            raise Refused("levels / depths in m (a value above 50 reads as mm)")
    h = Decimal(str(top_low)) + Decimal(str(min_depth)) - Decimal(str(stack)) - max(Decimal(str(x)) for x in H_candidates)
    if h <= 0:
        raise Refused("non-positive neck height: the datums contradict")
    return h.quantize(Q6)


def volume(section_candidates_m2, h):
    if not section_candidates_m2:
        raise Refused("no section: HELD with the section item")
    return d6(min(Decimal(str(a)) for a in section_candidates_m2) * Decimal(str(h)))


def family_total(valued_m3, comps, unit="m3"):
    """R-T572-3: valued + bounds, a side None when any component blocks it; NOT_PRESENT components apart."""
    for c in comps:
        if c["unit"] != unit:
            raise Refused(f"{c['element_id']}: {c['unit']} added to {unit}")
    held = [c for c in comps if c["kind"] != "NOT_PRESENT_PROPOSED"]
    v = d6(valued_m3)
    lo_ok = [c for c in held if c["low"] is not None]
    hi_ok = [c for c in held if c["high"] is not None]
    lo_part = sum((Decimal(c["low"]) for c in lo_ok), Decimal(0))
    hi_part = sum((Decimal(c["high"]) for c in hi_ok), Decimal(0))
    return {"valued": str(v), "held_components": len(held),
            "not_present_proposed": len(comps) - len(held),
            "bounded_both": sum(1 for c in held if c["kind"] == "BOUNDED"),
            "low_stated": len(lo_ok), "high_stated": len(hi_ok),
            "family_low": str((v + lo_part).quantize(Q6)) if len(lo_ok) == len(held) else None,
            "family_high": str((v + hi_part).quantize(Q6)) if len(hi_ok) == len(held) else None,
            "bounded_part_low": str(lo_part.quantize(Q6)) if lo_ok else None,
            "bounded_part_high": str(hi_part.quantize(Q6)) if hi_ok else None,
            "low_blocked_by": sorted({c["low_item"] for c in held if c["low"] is None}),
            "high_blocked_by": sorted({c["high_item"] for c in held if c["high"] is None})}


def like_for_like(engine, his, unit_engine="m3", unit_his="m3"):
    """R-T572-4: % only on the measured set, same unit; NO_ROW gives none."""
    if unit_engine != unit_his:
        raise Refused(f"{unit_engine} compared with {unit_his}")
    if his is None or his == "NO_ROW":
        return {"engine": str(d6(engine)), "his": "NO_ROW", "diff": None, "pct": None}
    e, h = d6(engine), d6(his)
    if h == 0:
        raise Refused("his figure 0 on a measured set: not a comparison base")
    return {"engine": str(e), "his": str(h), "diff": str(e - h),
            "pct": str(((e - h) / h * 100).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))}


def against_bound(his, low, high):
    """R-T572-4: his figure against the drawn ends (information only)."""
    if his is None:
        return "NO_ROW"
    h = Decimal(str(his))
    if low is not None and h < Decimal(str(low)):
        return "BELOW_DRAWN_LOWER"
    if high is not None and h > Decimal(str(high)):
        return "ABOVE_DRAWN_UPPER"
    if low is None and high is None:
        return "UNBOUNDED"
    return "WITHIN" if low is not None and high is not None else "NOT_CONTRADICTED_ONE_SIDED"
