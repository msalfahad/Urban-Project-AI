"""R-T601-1 DOORLESS OPENING JAMB CENSUS (every villa; research rule, unwired; T-601).

Physical element: the two return faces (jambs) of a wall opening, each as deep as the wall. Skirting runs on a jamb only
under the owner method URBAN-SKIRTING-OPENING-METHOD v1 (DOORLESS_OPENING: real_floor_side_jambs INCLUDED when the opening
genuinely has no door, the jamb is a real vertical surface, that side is skirting-eligible, the floor finish reaches the
jamb, not a full-tile room; DOOR_PRESENT: jamb_skirting NONE) and UP-SKIRT-001 1.4.0 ('doorless_opening_jambs:
included'). The paired plaster / paint return faces are the PLASTERED RETURN FACE entry (UP-OPEN-SCHED-001 1.4.0): this
rule never bills them.

Census decision, in this order (the opening's own drawn evidence decides; an engine kind label such as PASSAGE is not
evidence):
  (a) CROSSED (a wall face crosses the gap strip)            -> NOT_AN_OPENING (two collinear wall pieces / a junction)
  (b) DOOR_BLOCK or DOOR_DRAWN (a leaf or its swing)          -> DOOR: jamb skirting NONE
  (c) PANEL_LINES (landing-door / frame lines across the gap) -> FRAMED: jamb skirting NONE (lift landing door)
  (d) GLAZING                                                  -> WINDOW: outside this census
  (e) otherwise (arch head, head lines, or nothing)            -> DOORLESS, then per side:
        a side OUTDOOR                -> OUTDOOR_SCOPE: carried HELD by name in the outdoor skirting scope, never 0
        a side WET (full-height tile, marble threshold: Q-06 a, UP-THR-001)
                                      -> NOT_APPLICABLE: the jamb stands on the threshold, not the dry floor finish
        a side unknown                -> HELD (side not established)
        wall depth unknown            -> HELD (2 x depth, never 0)
        both sides DRY                -> per end: MASONRY_JAMB / COLUMN_JAMB / CAPPED_END = one jamb of the wall depth;
                                         CONTINUOUS_FACE = not a jamb (that face is part of the cross wall's run and is
                                         counted there); UNBOUNDED / unknown end -> HELD
      then the engine treatment of a DRY / DRY opening:
        DEDUCTED   (the skirting line deducts the opening and values no jamb) -> FIX_ROW: + jamb lm
        IN_CELL    (both sides are one skirting cell: the outline walks the jambs) -> INCLUDED_IN_OUTLINE, no fix
        NO_LINE / unknown                                                    -> HELD (treatment not established)
Quantities are Decimal metres; a HELD result carries its bound beside, never a 0 that could be summed.
"""
from __future__ import annotations

from decimal import Decimal

D = Decimal
RULE_ID = "R-T601-1"
GOVERNING = ["URBAN-SKIRTING-OPENING-METHOD v1", "UP-SKIRT-001 1.4.0", "UP-THR-001 1.0.0", "Q-06 A"]
JAMB_ENDS = ("MASONRY_JAMB", "COLUMN_JAMB", "CAPPED_END")
NOT_JAMB_ENDS = ("CONTINUOUS_FACE",)
SIDES = ("DRY", "WET", "OUTDOOR", "SHAFT")
TREATMENTS = ("DEDUCTED", "IN_CELL", "NO_LINE")


class CensusError(ValueError):
    pass


def kind_of(evidence):
    ev = set(evidence)
    unknown = ev - {"CROSSED", "DOOR_BLOCK", "DOOR_DRAWN", "PANEL_LINES", "GLAZING", "ARCH_BLOCK", "HEAD_LINES"}
    if unknown:
        raise CensusError(f"unknown evidence {sorted(unknown)}")
    if "CROSSED" in ev:
        return "NOT_AN_OPENING"
    if ev & {"DOOR_BLOCK", "DOOR_DRAWN"}:
        return "DOOR"
    if "PANEL_LINES" in ev:
        return "FRAMED"
    if "GLAZING" in ev:
        return "WINDOW"
    return "DOORLESS"


def classify(op):
    """op: {'evidence': [...], 'ends': [end, end], 'wall_t_m': str | None, 'sides': [side | None, side | None],
    'treatment': one of TREATMENTS | None}. Returns {'kind', 'status', 'jamb_lm' (str or None), 'bound_lm', 'fix_lm',
    'why'}."""
    kind = kind_of(op.get("evidence", ()))
    res = {"rule": RULE_ID, "kind": kind, "jamb_lm": None, "bound_lm": None, "fix_lm": None}
    if kind != "DOORLESS":
        why = {"NOT_AN_OPENING": "a wall face crosses the gap: not an opening, no jamb",
               "DOOR": "DOOR_PRESENT: jamb_skirting NONE (URBAN-SKIRTING-OPENING-METHOD)",
               "FRAMED": "a landing-door / frame is drawn across the gap: not doorless, jamb_skirting NONE",
               "WINDOW": "glazing: a window, outside the doorless census"}[kind]
        return dict(res, status="NO_JAMB_SKIRTING", jamb_lm="0", why=why)
    ends = list(op.get("ends") or ())
    if len(ends) != 2:
        raise CensusError("a doorless opening needs its two ends")
    t = op.get("wall_t_m")
    depth = D(t) if t not in (None, "") else None
    if depth is not None and depth <= 0:
        raise CensusError("wall depth must be positive")
    real = sum(1 for e in ends if e in JAMB_ENDS)
    bound = None if depth is None else str(depth * real)
    sides = list(op.get("sides") or (None, None))
    for s in sides:
        if s is not None and s not in SIDES:
            raise CensusError(f"unknown side {s}")
    if "OUTDOOR" in sides:
        return dict(res, status="OUTDOOR_SCOPE", bound_lm=bound,
                    why="a side is outdoors: the returns belong to the outdoor skirting scope (unresolved), held by name")
    if "WET" in sides or "SHAFT" in sides:
        return dict(res, status="NOT_APPLICABLE", jamb_lm="0",
                    why="a side is a full-tile wet space with a marble threshold (Q-06 A, UP-THR-001) or a shaft: the "
                        "floor finish does not reach the jamb (owner method condition 4)")
    if None in sides:
        return dict(res, status="HELD", bound_lm=bound, why="a side of the opening is not established")
    if depth is None:
        return dict(res, status="HELD", bound_lm=None, why="jamb depth not established: 2 x wall depth, never 0")
    if any(e not in JAMB_ENDS + NOT_JAMB_ENDS for e in ends):
        return dict(res, status="HELD", bound_lm=str(depth * 2), why="an end is not bounded by a real jamb")
    lm = str(depth * real)
    tr = op.get("treatment")
    if tr == "DEDUCTED":
        return dict(res, status="FIX_ROW", jamb_lm=lm, fix_lm=lm,
                    why=f"{real} real jamb(s) x {depth} m; the skirting line deducts the opening and values no jamb")
    if tr == "IN_CELL":
        return dict(res, status="INCLUDED_IN_OUTLINE", jamb_lm=lm,
                    why="both sides are one skirting cell: the room outline already walks the jamb faces")
    return dict(res, status="HELD", bound_lm=lm, why="the engine treatment of the opening is not established")


def tally(results):
    """valued fix lm (Decimal) and the names of every HELD / OUTDOOR result; refuses a HELD result carrying a value."""
    fix = D("0")
    held = []
    for name, r in results:
        if r["status"] in ("HELD", "OUTDOOR_SCOPE"):
            if r.get("jamb_lm") not in (None,):
                raise CensusError(f"{name}: a held jamb carries a value")
            held.append(name)
        elif r["status"] == "FIX_ROW":
            fix += D(r["fix_lm"])
    return fix, held
