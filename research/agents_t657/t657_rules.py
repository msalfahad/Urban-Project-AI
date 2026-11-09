"""T-657 rules (research, unwired): the column NECK between the footing top and the ground-beam / GF column base, both
ends of its height read from the project's printed drawings, for any villa.

R-T657-1 UPPER END FROM THE PRINTED SINGLE-BEAM CONDITION. Where the project's structural sheets print an isolated
    footing detail for a level difference 'upper ground beam top .. footing underside LESS THAN D_max' and a second
    detail (an extra, lower ground-beam row) for a difference MORE than D_max, and the foundation / ground-beam plans
    draw ONE ground-beam row only, the drawn design fixes GB top - footing underside <= D_max. The neck then satisfies
    h = (GB top - footing underside) - H <= D_max - H_min. The bound holds whichever line the D_max dimension reaches
    at its top (the ground-beam top or a level above it): it is the largest such height. A formation deeper than that
    is a DESIGN CHANGE (the other detail, a lower beam row that no plan draws, engineering approval: owner Q-21 'no
    change of founding level ... without engineering approval'); it is named beside as a scenario, never measured into
    the drawn neck.
R-T657-2 NOT ON A PIT RAFT OF UNPRINTED DEPTH. R-T657-1 is not applied to a neck standing on a raft whose depth the
    sheets leave to a supplier (e.g. a lift pit 'as per lift manufacturer'): that upper end stays open by its item.
R-T657-3 EACH END ITS OWN READINGS. Low end: lowest drawn top, printed minimum depth, largest candidate H, smallest
    candidate section (R-T572-2). High end: R-T657-1 with the smallest candidate H and the largest candidate section.
    low <= high is checked; a contradiction is refused (it would mean the printed minimum depth already exceeds the
    single-beam condition, so the second detail governs and the drawn set is incomplete).
R-T657-4 VALUED ONLY ON TWO PRINTED LEVELS. A neck is a single value only when the footing (or formation) level and the
    neck top are both printed; a printed minimum plus a printed maximum condition gives a BOUNDED range, never its
    midpoint, never the freelancer's flat height, never 0.

Provenance: T-657 (2026-11-09, worker 1), on R-T572-1 .. 4, R-NECK-ENDS-1 (T-205), owner Q-21 answer C. Scope: every
villa whose structural set prints the single / two ground-beam condition; elsewhere the upper end stays open.
"""
from __future__ import annotations

from decimal import Decimal

Q6 = Decimal("0.000001")


class Refused(ValueError):
    """A reading the rules refuse."""


def _m(v, what):
    if v is None:
        raise Refused(f"{what} not printed: HELD with its item, never 0")
    d = Decimal(str(v))
    if d > 50:
        raise Refused(f"{what} {v}: levels / depths in m (a value above 50 reads as mm)")
    return d


def neck_high_height(d_max, H_candidates, *, one_gb_row_drawn, pit_raft_unprinted=False, detail_printed=True):
    """R-T657-1 / -2: h <= D_max - H_min, or None with the reason when the condition does not apply."""
    if pit_raft_unprinted:
        return None, "R-T657-2: raft depth left to the supplier; upper end open by its item"
    if not detail_printed:
        raise Refused("no printed single / two ground-beam condition: the upper end stays open (no typical value)")
    if not one_gb_row_drawn:
        return None, "R-T657-1 not applicable: the plans draw a lower ground-beam row (second detail governs)"
    if not H_candidates or any(h is None for h in H_candidates):
        raise Refused("footing depth not printed: HELD with the footing item")
    h = _m(d_max, "D_max") - min(_m(x, "H") for x in H_candidates)
    if h <= 0:
        raise Refused("non-positive neck height: the printed condition and the footing depth contradict")
    return h.quantize(Q6), None


def neck_low_height(top_low, min_depth, stack, H_candidates):
    """R-T572-2 restated: h >= top_low + printed minimum depth - stack below the footing - H_max."""
    if not H_candidates or any(h is None for h in H_candidates):
        raise Refused("footing depth not printed: HELD with the footing item")
    h = (_m(top_low, "neck top") + _m(min_depth, "minimum depth") - _m(stack, "stack")
         - max(_m(x, "H") for x in H_candidates))
    if h <= 0:
        raise Refused("non-positive neck height: the datums contradict")
    return h.quantize(Q6)


def neck_range(top_low, min_depth, stack, H_candidates, sections_m2, d_max, *, one_gb_row_drawn,
               pit_raft_unprinted=False):
    """R-T657-3: (h_low, h_high or None, m3_low, m3_high or None, high_reason)."""
    if not sections_m2:
        raise Refused("no section: HELD with the section item")
    secs = [Decimal(str(a)) for a in sections_m2]
    hl = neck_low_height(top_low, min_depth, stack, H_candidates)
    hh, why = neck_high_height(d_max, H_candidates, one_gb_row_drawn=one_gb_row_drawn,
                               pit_raft_unprinted=pit_raft_unprinted)
    if hh is not None and hl > hh:
        raise Refused(f"low {hl} > high {hh}: the printed minimum depth exceeds the single-beam condition")
    lo = (min(secs) * hl).quantize(Q6)
    hi = None if hh is None else (max(secs) * hh).quantize(Q6)
    return hl, hh, lo, hi, why


def neck_value(top, footing_top, sections_m2):
    """R-T657-4: one value only from two printed levels and one section."""
    if top is None or footing_top is None:
        raise Refused("an end level is not printed: carry the range, never a midpoint")
    secs = {Decimal(str(a)) for a in sections_m2}
    if len(secs) != 1:
        raise Refused("section candidates conflict: carry the range")
    h = _m(top, "top") - Decimal(str(footing_top))
    if h <= 0:
        raise Refused("top not above the footing top")
    return (secs.pop() * h).quantize(Q6)
