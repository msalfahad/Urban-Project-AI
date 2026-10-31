"""T-380: drainage / water-supply SOURCE CENSUS rules (B12-02), any villa.

What a drainage sheet can give the BOQ is decided per printed item, before any number:

- COUNTABLE: a discrete physical item (manhole / inspection chamber, clean-out, rodding eye, stack, rain-water pipe,
  gully, valve, pump) whose symbol or legend tag is PRINTED. One pcs per printed position; a stack that passes several
  floors is ONE stack, matched floor to floor by position and by its F/A (from above) / T/B (to below) tags.
- MEASURABLE: a pipe run whose length the drawings STATE: a printed dimension, or printed levels / invert levels at
  both ends of a vertical or a dimensioned layout. Only then is a length computed.
- SCHEMATIC_ONLY: a run that is drawn (route, size, slope may be printed) but whose length is not stated. Its length is
  never scaled, and never scaled at all where the sheet says the builder works with stated dimensions and not to scale.
- NOT_PRINTED: an item the sheets do not show (for example a water-supply layout on a drainage-only set). It stays
  HELD; it is never 0 and never inferred from practice, the freelancer or a legend entry that is not used on the plan.

A legend entry is a vocabulary, not an item: a symbol listed in the legend and drawn nowhere on the plan is
NOT_PRINTED (LEGEND_ONLY). Research module, no engine import, no rule version: it reports, it releases nothing.
"""

from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass

COUNTABLE = "COUNTABLE"
MEASURABLE = "MEASURABLE"
SCHEMATIC_ONLY = "SCHEMATIC_ONLY"
NOT_PRINTED = "NOT_PRINTED"
STATUSES = (COUNTABLE, MEASURABLE, SCHEMATIC_ONLY, NOT_PRINTED)

# Evidence that may carry an item. Anything else is refused.
SYMBOL = "SYMBOL_DRAWN"            # the item's symbol is drawn at a position
LEGEND_TAG = "LEGEND_TAG"          # a printed tag the legend defines, at a position (MH, GCO, CO, SS, RWP, FD, RWD)
PRINTED_LABEL = "PRINTED_LABEL"    # a printed note naming the item (e.g. 'MH 100X100X100 DEEP INSPECTION CHAMBER')
ROUTE_DRAWN = "ROUTE_DRAWN"        # a pipe route drawn as a line (schematic)
DIMENSION = "PRINTED_DIMENSION"    # a printed length / dimension string on the run
LEVELS = "PRINTED_LEVELS"          # printed (invert) levels at BOTH ends of the run
LEGEND_ONLY = "LEGEND_ONLY"        # listed in the legend, drawn nowhere
ABSENT = "ABSENT"                  # searched, not on any sheet
BASES = (SYMBOL, LEGEND_TAG, PRINTED_LABEL, ROUTE_DRAWN, DIMENSION, LEVELS, LEGEND_ONLY, ABSENT)
REFUSED_BASES = ("SCALED", "PRACTICE", "FREELANCER", "GUESS", "ROOM_NAME")

COUNT_KINDS = ("MANHOLE", "GROUND_CLEAN_OUT", "CLEAN_OUT", "RODDING_EYE", "NON_RETURN_VALVE", "AREA_DRAIN",
               "SUMP_PUMP", "SOIL_STACK", "RAIN_WATER_PIPE", "FLOOR_DRAIN", "ROOF_DRAIN", "WATER_TANK",
               "WATER_HEATER", "SUPPLY_POINT", "VENT_PIPE")
RUN_KINDS = ("DRAIN_MAIN", "SOIL_BRANCH", "WASTE_BRANCH", "SUSPENDED_DRAIN", "STACK_VERTICAL", "RWP_VERTICAL",
             "WATER_SUPPLY")


UNLABELLED = "UNLABELLED"           # a drop symbol drawn with no printed tag (identity only from the floor above)


class CensusRefused(ValueError):
    """A length from a schematic, a NOT_PRINTED item written as 0, or an item typed without printed evidence."""


@dataclass(frozen=True)
class Item:
    item_id: str
    kind: str
    floor: str
    ref: str                    # sheet / page / point, or DXF handle, or 'searched: ...'
    basis: str
    diameter: str = ""          # as PRINTED (e.g. '6in'); '' = not printed (never defaulted)
    slope: str = ""             # as printed
    tags: tuple = ()            # printed F/A, T/B, H/L, B.T.T.S. ...
    note: str = ""

    def __post_init__(self):
        if self.basis in REFUSED_BASES or self.basis not in BASES:
            raise CensusRefused(f"{self.item_id}: basis {self.basis!r} is not printed evidence")
        if self.kind not in COUNT_KINDS + RUN_KINDS:
            raise CensusRefused(f"{self.item_id}: kind {self.kind!r} unknown")

    @property
    def is_run(self):
        return self.kind in RUN_KINDS


def status(item: Item, sheet_not_to_scale: bool) -> str:
    """The census status of one item, from its printed basis only."""
    if item.basis in (LEGEND_ONLY, ABSENT):
        return NOT_PRINTED
    if not item.is_run:
        if item.basis in (SYMBOL, LEGEND_TAG, PRINTED_LABEL):
            return COUNTABLE
        raise CensusRefused(f"{item.item_id}: a {item.kind} needs a printed symbol / tag / label to be counted")
    if item.basis in (DIMENSION, LEVELS):
        return MEASURABLE
    if item.basis == ROUTE_DRAWN:
        return SCHEMATIC_ONLY
    raise CensusRefused(f"{item.item_id}: run basis {item.basis!r}")


def length_m(item: Item, sheet_not_to_scale: bool, stated_length_m=None, end_levels=None):
    """A run length in metres, or a refusal. Never a scaled length; never 0 for a run that is not stated.

    stated_length_m: the printed dimension (MEASURABLE by DIMENSION); end_levels: (top, bottom) printed levels in m
    for a vertical run (MEASURABLE by LEVELS)."""
    st = status(item, sheet_not_to_scale)
    if st != MEASURABLE:
        raise CensusRefused(f"{item.item_id}: {st}: no length (a drawn route is not a measured length"
                            + ("; the sheet says work with stated dimensions, not to scale" if sheet_not_to_scale
                               else "") + ")")
    if item.basis == DIMENSION:
        if stated_length_m is None or stated_length_m <= 0:
            raise CensusRefused(f"{item.item_id}: printed dimension missing or not positive")
        return float(stated_length_m)
    if end_levels is None or len(end_levels) != 2 or None in end_levels:
        raise CensusRefused(f"{item.item_id}: both end levels must be printed")
    top, bottom = end_levels
    if top <= bottom:
        raise CensusRefused(f"{item.item_id}: top level {top} not above bottom {bottom}")
    if abs(top) > 200 or abs(bottom) > 200:
        raise CensusRefused(f"{item.item_id}: levels look like mm, not m ({top}, {bottom})")
    return round(top - bottom, 6)


def quantity(item: Item, sheet_not_to_scale: bool):
    """The census value of an item: 1 pcs for a COUNTABLE item, 'HELD' for anything not stated (never 0)."""
    st = status(item, sheet_not_to_scale)
    if st == COUNTABLE:
        return 1
    return "HELD"


def check_items(items):
    ids = [i.item_id for i in items]
    dup = sorted({x for x in ids if ids.count(x) > 1})
    if dup:
        raise CensusRefused(f"item listed twice: {dup}")
    return True


def counts(items, sheet_not_to_scale: bool):
    """pcs per kind of the COUNTABLE items; NOT_PRINTED kinds listed apart as HELD (never a 0 count)."""
    check_items(items)
    c = OrderedDict()
    held = OrderedDict()
    for it in items:
        st = status(it, sheet_not_to_scale)
        if st == COUNTABLE:
            c[it.kind] = c.get(it.kind, 0) + 1
        elif st == NOT_PRINTED:
            held[it.kind] = "HELD"
    for k in held:
        if k in c:
            raise CensusRefused(f"{k} both counted and NOT_PRINTED")
    return c, held


def chain_stacks(drops, tol_pt=12.0):
    """Match vertical pipes floor to floor into physical stacks.

    drops: list of (item_id, floor_index, x_pt, y_pt, tags), floor_index 0 = lowest, positions in one page frame.
    A stack starts at a drop without 'F/A' (its top) and continues to the drop at the same position (within tol_pt)
    on the floor below when the upper one prints 'T/B' or the lower one prints 'F/A'. A link carried by only one of
    the two tags (the other not printed, or an UNLABELLED drop symbol) is kept and returned as a finding: its identity
    rests on the one printed tag. A T/B with no unique match below, or an F/A drop that no stack reaches, is refused.
    Returns (stacks as lists of item ids, top first; findings)."""
    ids = [d[0] for d in drops]
    if len(set(ids)) != len(ids):
        raise CensusRefused("a drop listed twice")
    by_floor = {}
    for d in drops:
        by_floor.setdefault(d[1], []).append(d)
    used = set()
    stacks, findings = [], []
    for d in sorted(drops, key=lambda e: (-e[1], e[0])):
        if "F/A" in d[4] or UNLABELLED in d[4] or d[0] in used:
            continue
        chain = [d]
        used.add(d[0])
        cur = d
        while True:
            below = [e for e in by_floor.get(cur[1] - 1, []) if e[0] not in used
                     and abs(e[2] - cur[2]) <= tol_pt and abs(e[3] - cur[3]) <= tol_pt]
            tb = "T/B" in cur[4]
            if tb and len(below) != 1:
                raise CensusRefused(f"{cur[0]}: T/B with {len(below)} matching drops on the floor below")
            if not tb:
                below = [e for e in below if "F/A" in e[4]]
                if len(below) != 1:
                    break
            nxt = below[0]
            fa = "F/A" in nxt[4]
            if not fa and UNLABELLED not in nxt[4]:
                raise CensusRefused(f"{nxt[0]}: receives a T/B from above but carries no F/A tag")
            if not (tb and fa):
                findings.append(f"{cur[0]} -> {nxt[0]}: link printed on one side only "
                                f"({'T/B above' if tb else 'F/A below'}); the other tag is not printed")
            chain.append(nxt)
            used.add(nxt[0])
            cur = nxt
        stacks.append([e[0] for e in chain])
    dangling = sorted(set(ids) - used)
    if dangling:
        raise CensusRefused(f"F/A with no matching drop above: {dangling}")
    return stacks, findings
