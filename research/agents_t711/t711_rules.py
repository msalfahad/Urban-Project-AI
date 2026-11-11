"""T-711 rules (project-agnostic; scope: every villa). Research only, unwired. Built on R-T657-1 .. 4 (neck ends),
R-T401-2 (pit-wall height on the governing detail's datum), R-T319 parapet floor (T-311 / F-T311-C1), R-T699-1 (one-sided
statement form) and R-T696-1 (bound_rounding_v1, directed rounding); none of them edited.

R-T711-1 1.0.0  ONE-SIDED LOWER BOUND BELOW A SUPPLIER-DEPTH RAFT (lift necks, lift-pit walls).
    Physical element: a vertical RC member from the TOP of a raft whose depth is left to a supplier ('as per lift
    manufacturer') up to a printed datum (the GF column base / the slab-on-grade top at the landing).
    h >= top_level - raft_top_highest, raft_top_highest = -(min founding depth) + stack + H, where the min founding
    depth is the printed minimum excavation below EG, the stack is the printed under-raft layers (largest reading),
    H the raft thickness (largest reading). A deeper pit only lengthens the member, so the upper end stays OPEN by its
    supplier item. m3 >= h x the SMALLEST plan area among the printed readings. Refused: a top level, a depth, a stack,
    an H or an area that is missing, not positive or given in mm; an upper end stated while the depth is a supplier item.

R-T711-2 1.0.0  LOWER BOUND OF A LINE WITH CONFLICTING READINGS.
    Where the drawings print two (or more) complete readings of one member (e.g. riser count 27 vs 28), the AT_LEAST of
    the line is the MINIMUM over the readings of each reading's own sum of its components (each component at its
    smallest drawn extent within that reading). Components may not be mixed across readings for the floor's argument,
    but the component-wise minimum is reported beside as a check (it can only be lower). An open-ended component
    (no upper end) forbids any AT_MOST / range for the line. A reading with a missing component is refused.

R-T711-3 1.0.0  A LINE THAT IS PHYSICALLY ABLE TO BE 0 OR WHOSE ONLY DIMENSION IS UNPRINTED STAYS BLANK.
    A waist / support that may not exist (steps on grade), a junction whose section is not drawn, a member whose
    section is printed nowhere, or a part whose geometry needs an unprinted riser: no AT_LEAST (it would be 0 or a
    chosen number), no AT_MOST (unbounded). The line stays HELD BLANK with its designer item named and its quantity per
    unit of the missing dimension stated beside (m3 per m of thickness / per m2 of section / per m of riser), never 0.

Rounding: R-T696-1 (AT_LEAST floors at 6 dp from the exact decimal product).
"""
from __future__ import annotations

import sys
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "agents_t696"))
import bound_rounding_v1 as BR  # noqa: E402

X = Decimal
RULES = {"R-T711-1": "1.0.0", "R-T711-2": "1.0.0", "R-T711-3": "1.0.0"}
CLASSES = ("AT_LEAST", "BLANK_NAMED")


class Refused(ValueError):
    pass


def _m(v, what, *, allow_zero=False, allow_negative=False):
    """an input in metres (m / m2): str / int / Decimal; refuses None, mm-sized values and non-positive values."""
    if v is None:
        raise Refused(f"{what}: missing (HELD by name, never a default)")
    d = BR.D(v)
    if not allow_negative and (d < 0 or (d == 0 and not allow_zero)):
        raise Refused(f"{what}: {d} not positive")
    if abs(d) >= 100:
        raise Refused(f"{what}: {d} looks like mm (inputs are metres)")
    return d


# ------------------------------------------------------------------ R-T711-1
def raft_top_highest(*, min_depth, stack, H):
    """highest admissible raft top relative to EG +-0.00 (negative = below EG)."""
    return -_m(min_depth, "min founding depth") + _m(stack, "under-raft stack") + _m(H, "raft H")


def below_supplier_raft(*, top_level, areas_m2, min_depth, stack, H, supplier_item, upper=None):
    """R-T711-1: {h_low, area_min, at_least, at_most(None), open_by}. `areas_m2` = every printed reading of the plan area."""
    if upper is not None:
        raise Refused("R-T711-1: an upper end while the raft depth is a supplier item")
    if not supplier_item:
        raise Refused("R-T711-1: the open upper end must name its supplier / designer item")
    if not areas_m2:
        raise Refused("R-T711-1: no plan-area reading")
    top = _m(top_level, "top level", allow_zero=True, allow_negative=True)
    rt = raft_top_highest(min_depth=min_depth, stack=stack, H=H)
    h = top - rt
    if h <= 0:
        raise Refused(f"R-T711-1: member top {top} not above the highest raft top {rt}")
    a = min(_m(a, "plan area") for a in areas_m2)
    return {"rule": "R-T711-1", "h_low_m": h, "raft_top_highest_m": rt, "area_min_m2": a,
            "at_least": BR.round_low(BR.mul(a, h)), "at_most": None, "open_by": supplier_item}


# ------------------------------------------------------------------ R-T711-2
def min_over_readings(readings):
    """readings: {name: {component: low_m3 (str/Decimal) or None}}. Returns the R-T711-2 floor and its reading."""
    if not readings or len(readings) < 1:
        raise Refused("R-T711-2: no reading")
    comps = None
    sums = {}
    for name, parts in readings.items():
        if comps is None:
            comps = set(parts)
        elif set(parts) != comps:
            raise Refused(f"R-T711-2: reading {name} does not name the same components")
        for c, v in parts.items():
            if v is None:
                raise Refused(f"R-T711-2: reading {name} component {c} missing (no floor from a partial reading)")
        sums[name] = BR.add(*(_m(v, f"{name}:{c}") for c, v in parts.items()))
    gov = min(sums, key=lambda k: (sums[k], k))
    cw = BR.add(*(min(_m(readings[r][c], c) for r in readings) for c in sorted(comps)))
    return {"rule": "R-T711-2", "at_least": BR.round_low(sums[gov]), "governing_reading": gov,
            "reading_sums": {k: BR.round_low(v) for k, v in sums.items()}, "componentwise_min": BR.round_low(cw),
            "at_most": None}


# ------------------------------------------------------------------ parapet floor (R-T319 / F-T311-C1, restated)
def parapet_floor(runs, upstand_floor_m):
    """sum of each run's smallest drawn top (centreline x thickness) x the printed minimum RC upstand above the slab top.
    A run without a top is refused (never 0)."""
    f = _m(upstand_floor_m, "upstand floor")
    tot = X(0)
    for r in runs:
        tot += _m(r.get("top_lo_m2"), f"run {r.get('run')} top")
    return {"top_lo_m2": tot, "at_least": BR.round_low(BR.mul(tot, f)), "at_most": None}


# ------------------------------------------------------------------ R-T711-3
def blank_named(*, item, why, per_unit=None):
    if not item:
        raise Refused("R-T711-3: a blank line must name its designer item")
    if not why:
        raise Refused("R-T711-3: a blank line must say why no bound exists")
    return {"rule": "R-T711-3", "class": "BLANK_NAMED", "at_least": None, "at_most": None, "item": item, "why": why,
            "per_unit": per_unit}


# ------------------------------------------------------------------ statement guard
def statement(line_id, element_id, cls, *, at_least=None, at_most=None, item=None):
    """one line's wiring form: HELD with AT_LEAST (never a range, never 0) or HELD BLANK with its item."""
    if cls not in CLASSES:
        raise Refused(f"{line_id}: class {cls}")
    if at_most is not None:
        raise Refused(f"{line_id}: T-711 states no AT_MOST (every upper end here is open by its item)")
    if cls == "AT_LEAST":
        if at_least is None or BR.D(at_least) <= 0:
            raise Refused(f"{line_id}: AT_LEAST must be a positive floor (never 0)")
    else:
        if at_least is not None:
            raise Refused(f"{line_id}: a blank line carries no figure")
        if not item:
            raise Refused(f"{line_id}: a blank line names its item")
    return {"line_id": line_id, "element_id": element_id, "class_after": "HELD", "bound": cls,
            "at_least_m3": None if at_least is None else str(BR.D(at_least)), "at_most_m3": None,
            "measured_net": None, "item": item}
