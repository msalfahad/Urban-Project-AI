"""T-721 rules (project-agnostic; scope: every villa). Research only, unwired. Built on R-T660-3 (a strip outside a
scheduled beam's face with no mark, bars or printed depth is no beam by its layer), R-T711-3 (a line that may physically
be 0 or needs an unprinted dimension stays blank with its item and a per-unit quantity), R-T712-1 (floor = exact drawn
plan area x the least guaranteed depth, least plan reading), R-CONC-OWN-1 (one owner per square: beam below the slab,
intersection once) and R-T696-1 (bound_rounding_v1, directed rounding); none of them edited.

R-T721-1 1.0.0  BAR-STACK FLOOR OF A HELD BEAM WHOSE SECTION PRINTS ITS BARS BUT NOT ITS DEPTH.
    Physical element: a beam (e.g. an opening ring) whose referenced section ('SEE DETAIL') draws the longitudinal bars on
    shared verticals inside the link - top bars, at least one side-bar level, bottom bars - while its depth is written as
    a reference ('AS PER ARCH') or drawn not to scale. Bars on one vertical cannot overlap and the link wraps them, so
        depth >= 2 x link dia + top dia + (side dia x printed side levels counted at the least, 1) + bottom dia.
    Cover is NOT added unless the sheet prints it (no default value); any real cover only raises the true depth, so the
    floor stays valid. AT_LEAST = round_low(least plan area x that depth). The scaled measurement of a not-to-scale detail
    and a spacing label ('/20cm' = maximum spacing) are no depth guarantees. Applies only when the section is referenced
    from the member on the plan (a 'SEE DETAIL' on the member) and the plan area is net of the slab (the slab stops at
    the member's outer face) and of the framing members (owned once). Refused: bars not on shared verticals, a missing
    bar diameter, a cover not printed but supplied, a plan area not netted, a zero / mm-sized input.

R-T721-2 1.0.0  AN EDGE PROJECTION / STRIP WITH NO SECTION, NO MARK, NO BARS AND NO PRINTED MATERIAL STAYS BLANK.
    A band outside a scheduled beam's outer face (roof-edge projection, box, cornice strip) whose depth no section prints
    and whose material is referred to the architect may be cast with the slab, be a parapet base, or be non-concrete: it
    may physically carry 0 m3 of beam concrete, so no AT_LEAST (it would be a chosen depth) and no AT_MOST. HELD BLANK
    with its designer item, its drawn plan area (= m3 per m of depth) and the one-family guard (beam OR parapet /
    projection item, never both). A cut section that crosses the strip and draws no concrete in it neither proves nor
    excludes it. A beam-schedule envelope applied to it is 'not drawn' and is set aside.

R-T721-3 1.0.0  SCHEDULE AND DRAWING DISAGREE ON A SIZE: AT_LEAST ON THE SMALLER READING, NEVER THE AVERAGE.
    Where the printed schedule width / depth and the drawn edge pair of the same member disagree and no section settles
    it, the floor uses the smaller reading x the drawn length (stopper to stopper, R-T704-2); the larger reading is an
    AT_MOST only where ONE drawn geometry bounds it (both readings printed for that member). A third reading or a mean is
    refused. The released line is never moved by this rule.

Rounding: R-T696-1 (AT_LEAST floors at 6 dp from the exact decimal product; AT_MOST rounds up).
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "agents_t696"))
import bound_rounding_v1 as BR  # noqa: E402

RULES = {"R-T721-1": "1.0.0", "R-T721-2": "1.0.0", "R-T721-3": "1.0.0"}
CLASSES = ("AT_LEAST", "BOUNDED", "BLANK_NAMED")


class Refused(ValueError):
    pass


def _m(v, what, *, small=False):
    if v is None:
        raise Refused(f"{what}: missing (HELD by name, never a default)")
    d = BR.D(v)
    if d <= 0:
        raise Refused(f"{what}: {d} not positive")
    if abs(d) >= (1 if small else 100):
        raise Refused(f"{what}: {d} looks like mm (inputs are metres)")
    return d


# ------------------------------------------------------------------ R-T721-1
def bar_stack_depth(*, link_dia, top_dia, bottom_dia, side_dia=None, side_levels=1, shared_verticals=True,
                    cover=None, cover_printed=False):
    """Least physical depth of a section that prints its bars (metres)."""
    if not shared_verticals:
        raise Refused("R-T721-1: bars not drawn on shared verticals: no stack, no floor")
    if cover is not None and not cover_printed:
        raise Refused("R-T721-1: a cover not printed on the sheet is a default value")
    d = 2 * _m(link_dia, "link dia", small=True) + _m(top_dia, "top bar dia", small=True) + \
        _m(bottom_dia, "bottom bar dia", small=True)
    if side_dia is not None:
        n = int(side_levels)
        if n < 1:
            raise Refused("R-T721-1: a printed side-bar level counts at least once")
        d += n * _m(side_dia, "side bar dia", small=True)
    if cover is not None:
        d += 2 * _m(cover, "printed cover", small=True)
    return d


def bar_stack_floor(*, areas_m2, depth, referenced=True, net_of_slab=True, net_of_framing=True):
    if not referenced:
        raise Refused("R-T721-1: the section is not referenced from this member")
    if not (net_of_slab and net_of_framing):
        raise Refused("R-T721-1: the plan area must be net of the slab and the framing members (owned once)")
    if not areas_m2:
        raise Refused("R-T721-1: no plan-area reading")
    a = min(_m(x, "plan area") for x in areas_m2)
    d = _m(depth, "depth")
    return {"rule": "R-T721-1", "area_min_m2": a, "depth_m": d, "at_least": BR.round_low(BR.mul(a, d)),
            "at_most": None}


# ------------------------------------------------------------------ R-T721-2
def projection_blank(*, item, area_m2, section_prints_depth=False, mark=None, bars=None, material_printed=False):
    if section_prints_depth or mark or bars or material_printed:
        raise Refused("R-T721-2: the strip has a printed depth / mark / bars / material: measure it, do not blank it")
    if not item:
        raise Refused("R-T721-2: a blank line names its designer item")
    a = _m(area_m2, "plan area")
    return {"rule": "R-T721-2", "class": "BLANK_NAMED", "at_least": None, "at_most": None, "item": item,
            "m3_per_m_depth": str(BR.round_low(a)), "guard": "valued in ONE family only (beam OR parapet / projection)"}


# ------------------------------------------------------------------ R-T721-3
def disagreeing_sizes(*, length_m, readings, other_m, one_geometry_bounds=False):
    """readings: the two printed / drawn values of the disputed dimension; other_m: the agreed other dimension."""
    if len(readings) != 2:
        raise Refused("R-T721-3: exactly the two printed readings (schedule, drawing); no third value, no mean")
    lo, hi = sorted(_m(r, "reading") for r in readings)
    L, o = _m(length_m, "length"), _m(other_m, "other dimension")
    out = {"rule": "R-T721-3", "at_least": BR.round_low(BR.mul(L, lo, o)), "at_most": None}
    if one_geometry_bounds:
        out["at_most"] = BR.round_high(BR.mul(L, hi, o))
    return out


# ------------------------------------------------------------------ statement guard
def statement(line_id, element_id, cls, *, at_least=None, at_most=None, item=None):
    if cls not in CLASSES:
        raise Refused(f"{line_id}: class {cls}")
    if cls in ("AT_LEAST", "BOUNDED"):
        if at_least is None or BR.D(at_least) <= 0:
            raise Refused(f"{line_id}: a floor must be positive (never 0)")
        if at_most is not None and BR.D(at_most) < BR.D(at_least):
            raise Refused(f"{line_id}: AT_MOST below AT_LEAST")
        if cls == "AT_LEAST" and at_most is not None:
            raise Refused(f"{line_id}: AT_LEAST carries no high")
    else:
        if at_least is not None or at_most is not None:
            raise Refused(f"{line_id}: a blank line carries no figure")
    if not item:
        raise Refused(f"{line_id}: every held line names its item")
    return {"line_id": line_id, "element_id": element_id, "class_after": "HELD", "bound": cls,
            "at_least_m3": None if at_least is None else str(BR.D(at_least)),
            "at_most_m3": None if at_most is None else str(BR.D(at_most)), "measured_net": None, "item": item}
