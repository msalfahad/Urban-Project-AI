"""T-584 rules (any villa; research, unwired): STEPS at external doors / gates, entrance-stair steps and stair-flight
steps as count x length, reconciled against a reference takeoff one unit at a time (lm, m2, nr).

R-T584-1 (proposed, every villa; provenance T-584; builds on UP-STAIR-008 (commercial step lm = sum of the UNIQUE
physical step widths; tread + riser + nosing together), R-T412-1 / -2 (one riser, one nosing; the top nosing of a flight
is a landing / floor edge, never a tread; length = the drawn front edge), R-T577-1 (one opening one piece; a number's unit
is its own column label), OWNER_RULE_OUTDOOR_FLOORS_2026-10-21 (outside stairs are marble), ERS s.2-4):
  (a) A STEP AT AN OPENING exists only where a front edge is DRAWN at the opening AND the two printed levels differ.
      Same printed level on both sides and no edge drawn: NOT_APPLICABLE (no default step, ever). An edge drawn while the
      printed levels are equal is a CONFLICT (refused here; HELD by name). An edge drawn while one side prints no level:
      the step exists (DRAWING-CONFIRMED edge), its riser height is HELD with the bound (0, printed high - lowest printed
      level of the plan], never a guessed figure.
  (b) ONE ELEMENT OR TWO. A front edge ON the wall face with nothing drawn beyond it is the outer nosing of the external
      threshold stone: ONE element, THRESHOLD_STEP, owned by the threshold line (strip lm / m2 stay that line's
      measures), with two more measures of the same piece: nosing lm = the drawn edge, riser m2 = edge x (high - low).
      A front edge drawn BEYOND the wall face is an outside stair, EXT_STEP: its own piece (B7 family, marble by owner
      rule), never inside the threshold strip. One piece, one owner: a step owned by two lines (threshold and outdoor
      floor, or threshold and a flight) is refused.
  (c) FLIGHT STEPS (UP-STAIR-008). Commercial step lm per flight = drawn treads x drawn front-edge width; nr = treads.
      The arrival riser's edge (landing or floor) is a nosing, not a step. A reference that counts one piece per riser
      closes against treads with a RULE_DIFFERENCE equal to the number of arrival edges, never silently.
  (d) UNITS. lm, m2 and nr never meet. A reference m2 cell equal to count x length with no area cell is a length in an
      area column (UNIT cause); booking a step lm as m2 is refused.
  (e) CAUSES (signed ours - his) close EXACTLY. A HELD cause carries his share opposite the held pieces and our bound
      beside (lo, hi; hi None = unbounded); held pieces never enter a sum and are never 0. An unnamed residual is
      refused; % only for a group with no HELD / SCOPE / UNIT / UNRESOLVED / ENGINE_OMISSION cause (an omission is
      not a percentage); VERIFIED is the Checker's word.
"""
from __future__ import annotations

import math
from decimal import Decimal, getcontext

getcontext().prec = 40
UNITS = ("lm", "m2", "nr")
KINDS = ("THRESHOLD_STEP", "EXT_STEP", "NO_STEP", "FLIGHT_STEP")
VERDICTS = ("AGREE", "TOLERANCE", "ENGINE_RIGHT", "ENGINE_WRONG", "ENGINE_OMISSION", "RULE_DIFFERENCE", "HELD",
            "UNRESOLVED")
CAUSE_KINDS = ("MEASURE", "HELD", "SCOPE", "UNIT", "RESIDUAL")
STATUSES = ("DRAWING-CONFIRMED", "ASSUMED - OWNER-APPROVED", "ESTIMATED", "PROVISIONAL", "HELD", "NOT_APPLICABLE")
LEN_UNITS = {"m": Decimal(1), "mm": Decimal("0.001")}


class RuleError(ValueError):
    pass


def D(x) -> Decimal:
    if x is None:
        raise RuleError("quantity unknown (None) used as a number: HELD / UNKNOWN is never 0")
    if isinstance(x, float):
        return Decimal(repr(x))
    return Decimal(str(x))


def length(x, unit="m"):
    if unit not in LEN_UNITS:
        raise RuleError(f"length unit {unit!r} unknown (m or mm only)")
    v = D(x) * LEN_UNITS[unit]
    if v < 0:
        raise RuleError("a length is never negative")
    return v


def level(txt):
    """A printed level figure ('+0.30', '-0.15', '+-0.00') or None when not printed."""
    if txt is None:
        return None
    t = str(txt).strip().replace("+-", "").replace("%%p", "")
    return D(t)


# ---- geometry (any rotation / mirror) --------------------------------------------------------------------------------
def to_frame(p, origin, angle_deg, mirror=False):
    """A point in an opening's own frame (x along the wall, y across it): inverse of insert = mirror, rotate, move."""
    a = math.radians(angle_deg)
    dx, dy = float(p[0]) - float(origin[0]), float(p[1]) - float(origin[1])
    x = dx * math.cos(a) + dy * math.sin(a)
    y = -dx * math.sin(a) + dy * math.cos(a)
    return (-x if mirror else x), y


def edge_in_frame(p, q, origin, angle_deg, mirror=False, unit="mm"):
    """(length, offset across the wall) of a drawn edge in the opening frame; the edge must run along the wall."""
    a, b = to_frame(p, origin, angle_deg, mirror), to_frame(q, origin, angle_deg, mirror)
    if abs(a[1] - b[1]) > 2:
        raise RuleError("the edge does not run along the wall (not a step front)")
    return (length(round(abs(a[0] - b[0]), 6), unit), length(round(abs((a[1] + b[1]) / 2), 6), unit))


# ---- (a) / (b) the step at an opening ---------------------------------------------------------------------------------
def step_at_opening(oid, edge_lm, on_face, beyond, level_a, level_b, plan_low=None):
    """edge_lm: the drawn front edge (m) or None; on_face / beyond: where it is drawn; level_a / level_b: printed levels
    (None = not printed); plan_low: the lowest printed level of the plan (bound only).
    Returns {kind, lm, riser_m, m2, nr, status, bound} for ONE piece."""
    if on_face and beyond:
        raise RuleError(f"{oid}: an edge on the face and another beyond it: two elements, read them as two pieces")
    la, lb = level(level_a), level(level_b)
    drawn = edge_lm is not None and (on_face or beyond)
    if not drawn:
        if la is not None and lb is not None and la == lb:
            return {"kind": "NO_STEP", "lm": None, "riser_m": None, "m2": None, "nr": 0, "status": "NOT_APPLICABLE",
                    "bound": None}
        raise RuleError(f"{oid}: no edge drawn but the levels differ or are not printed: the step is not established "
                        "(HELD by name, never a default step)")
    e = length(edge_lm)
    if e == 0:
        raise RuleError(f"{oid}: a step edge of zero length")
    kind = "THRESHOLD_STEP" if on_face else "EXT_STEP"
    if la is not None and lb is not None:
        if la == lb:
            raise RuleError(f"{oid}: an edge drawn between two equal printed levels: CONFLICT (HELD by name)")
        h = abs(la - lb)
        return {"kind": kind, "lm": e, "riser_m": h, "m2": e * h, "nr": 1, "status": "DRAWING-CONFIRMED", "bound": None}
    hi_lv = la if la is not None else lb
    if hi_lv is None:
        raise RuleError(f"{oid}: no level printed on either side: the riser is not established")
    if plan_low is None:
        raise RuleError(f"{oid}: one level not printed and no lowest printed level given: the riser has no bound")
    hmax = hi_lv - level(plan_low)
    if hmax <= 0:
        raise RuleError(f"{oid}: the printed side is the lowest level: the unprinted side cannot be lower")
    return {"kind": kind, "lm": e, "riser_m": None, "m2": None, "nr": 1, "status": "HELD",
            "bound": {"riser_m": (Decimal(0), hmax), "m2": (Decimal(0), e * hmax)}}


def owners_once(piece_owners):
    """{piece id: [owning line or family]}: one piece, one owner."""
    for pid, owners in piece_owners.items():
        own = [o for o in owners if str(o).strip()]
        if len(own) != 1:
            raise RuleError(f"{pid}: owned by {own}: one piece, one owner (a step is never threshold and outdoor floor "
                            "at once)")
    return len(piece_owners)


# ---- (c) flight steps --------------------------------------------------------------------------------------------------
def flight_steps(treads, width, unit="m"):
    """Commercial step (lm, nr) of one flight: drawn treads x drawn width."""
    if not isinstance(treads, int) or isinstance(treads, bool) or treads < 0:
        raise RuleError("a tread count is a whole number >= 0")
    w = length(width, unit)
    if w == 0:
        raise RuleError("a flight width of zero: not established (HELD)")
    return treads * w, treads


def piece_per_riser_split(his_nr, ours_treads, held_treads, arrival_edges):
    """His piece-per-riser count vs our treads: (held, arrival RULE_DIFFERENCE, remainder) with his = ours + held +
    arrival + remainder. The remainder is returned (named UNRESOLVED by the caller), never dropped."""
    for v in (his_nr, ours_treads, held_treads, arrival_edges):
        if not isinstance(v, int) or v < 0:
            raise RuleError("counts are whole numbers >= 0")
    return held_treads, arrival_edges, his_nr - ours_treads - held_treads - arrival_edges


def book(unit, element_unit, value):
    """A quantity offered to a unit table: refused unless its own unit (a step lm booked as m2 is refused)."""
    if unit not in UNITS or element_unit not in UNITS:
        raise RuleError(f"unit {unit!r} / {element_unit!r} refused")
    if unit != element_unit:
        raise RuleError(f"a {element_unit} quantity booked in the {unit} table refused (lm, m2, nr never meet)")
    return D(value)


# ---- (e) reconciliation ---------------------------------------------------------------------------------------------
def cause(label, amount, verdict, kind, source, bound=None):
    if verdict not in VERDICTS:
        raise RuleError(f"verdict {verdict!r} unknown")
    if kind not in CAUSE_KINDS:
        raise RuleError(f"cause kind {kind!r} unknown")
    if not str(label).strip():
        raise RuleError("a cause without its name (an unnamed residual is refused)")
    if kind == "HELD":
        if bound is None or bound[0] is None:
            raise RuleError(f"HELD cause {label!r} without the bound of what the held pieces would add")
        if bound[1] is not None and D(bound[1]) < D(bound[0]):
            raise RuleError(f"HELD cause {label!r}: bound hi < lo")
    elif bound is not None:
        raise RuleError(f"a bound on a non-HELD cause {label!r}")
    return {"label": label, "amount": D(amount), "verdict": verdict, "kind": kind, "source": source,
            **({"bound": (D(bound[0]), None if bound[1] is None else D(bound[1]))} if bound is not None else {})}


def close(group_id, unit, ours, his, causes):
    """One group of one unit table: ours - his == sum of causes, exactly."""
    if unit not in UNITS:
        raise RuleError(f"unit {unit!r} refused")
    gap = D(ours) - D(his)
    s = sum((c["amount"] for c in causes), Decimal(0))
    if s != gap:
        raise RuleError(f"group {group_id} ({unit}): causes {s} != gap {gap} (must close exactly)")
    comparable = not any(c["kind"] in ("HELD", "SCOPE", "UNIT") or c["verdict"] in ("UNRESOLVED", "ENGINE_OMISSION")
                         for c in causes)
    pct = (gap / D(his) * 100).quantize(Decimal("0.01")) if comparable and D(his) > 0 else None
    return {"id": group_id, "unit": unit, "ours": D(ours), "his": D(his), "gap": gap, "pct": pct, "causes": causes}


def status_ok(s):
    if s not in STATUSES:
        raise RuleError(f"status {s!r} refused (VERIFIED is the Checker's word)")
    return s
