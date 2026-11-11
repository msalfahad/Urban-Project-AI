"""T-715 rules (project-agnostic; scope: every villa). Research only, unwired: no engine module, method, rule-version
or knowledge file reads this. Built on UP-STAIR-003 / -005 / -006 / -008 / -010 / -011 (URBAN_RULES 1.6.0 / 1.7.0),
Q-46 A (section counts govern), Q-50 A cond (plan count when no section; curved parts HELD), owner S-9 (winders never
generated), R-T412-1 (one riser, one nosing), R-T410 (skirting per side: zigzag / sloped figures), R-T493-1 (landings
per stair), R-T508-1 (one blank line per alternative form, never additive), R-T696-1 (directed rounding); none edited.

R-T715-1 1.0.0  RISER, PITCH AND STEP OF A STRAIGHT FLIGHT FROM ITS SECTION COUNT.
    Physical element: the visible riser faces, the pitch line and the steps of ONE drawn flight.
    riser r = storey rise / risers of the storey (section count, Q-46 A; plan count only under Q-50 A cond and then
    ASSUMED - OWNER-APPROVED); visible riser = r - t (t tread marble, UP-STAIR-006); riser marble m2 = risers x width x
    (r - t) (every riser of the flight, the one onto the landing / floor included: R-T412-1); pitch lm = goings x
    hypot(going, r) (the engine's FIN.STAIR.FLIGHT definition, nosing to nosing); step lm = treads x width
    (UP-STAIR-008, a landing edge is not a step). Refused: a missing count / rise / width / going (never 0), mm,
    a visible riser <= 0, a going count that is not risers - 1 or risers (the flight ends on a landing or a winder).

R-T715-2 1.0.0  A TURN (WINDER) REGION WHOSE SUBDIVISION IS NOT DRAWN.
    The treads of a turn tile its plan region whatever the subdivision, so the TREAD MARBLE of the turn = the region's
    plan area (a DRAWN quantity, not held by the subdivision). Every winder nosing runs from the inner corner / newel
    to the outer wall, so it is never shorter than the lane width: step lm >= winder treads x lane width; riser marble
    >= turn risers x lane width x (r - t). The pitch line (walking line) and the exact step / riser figures stay HELD
    by the subdivision item. Requires the riser count from a section; a count conflict without a governing source,
    or a missing region area, refuses the rule (the line stays blank).

R-T715-3 1.0.0  ONE PHYSICAL FLIGHT, ONE CARRIER READING.
    A flight read on two plans (seen through a void, stacked, exposure) carries each item on ONE reading (the carrier,
    the reading whose tread / step line stands valued or is the bound element of the drawn flight). Every other reading
    of the same item is NOT_APPLICABLE with the carrier named, only if a carrier line of the SAME item code exists in
    the candidate (any class); with no carrier line the duplicate is refused NOT_APPLICABLE (it becomes the carrier).

R-T715-4 1.0.0  STAIR SKIRTING: PHYSICAL STRIP vs PAYABLE FORM.
    The skirting strip along a walled flight side is physical and measurable: zigzag (UP-STAIR-010) = plan + risers
    inside x r + returns; sloped (UP-STAIR-011) = plan x hypot(run, rise) / run + returns. Which form is PAYABLE is the
    project's choice (ORR-007): each form line carries its own figure CONDITIONAL on the form (never additive with its
    sibling); for the pair family the payable total is bounded [sum sloped, sum zigzag] (sloped <= zigzag always:
    hypot(a, b) <= a + b). A side whose wall face is not established (opening sill / head not printed, band role
    unknown, plan conflict) is AT_MOST its full-wall figure per form (0 when no wall). In a corner turn bounded by two
    walls, the risers of the turn land on one wall or the other: zigzag W + N = plan W + plan N + turn rise (exact for
    the pair); each wall alone in [plan, plan + rise]; sloped pair in [hypot(aW + aN, R), max over splits].
"""
from __future__ import annotations

import sys
from decimal import Context, Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "agents_t696"))
import bound_rounding_v1 as BR  # noqa: E402

X = Decimal
_C = Context(prec=50)
RULES = {"R-T715-1": "1.0.0", "R-T715-2": "1.0.0", "R-T715-3": "1.0.0", "R-T715-4": "1.0.0"}
UNITS_M = ("m",)


class Refused(ValueError):
    pass


def _m(v, what, unit="m"):
    if unit not in UNITS_M:
        raise Refused(f"{what}: unit {unit!r} refused (metres only)")
    if v is None:
        raise Refused(f"{what}: missing (never 0)")
    try:
        d = BR.D(v)
    except BR.BoundRoundingError as e:
        raise Refused(f"{what}: {e}") from None
    if d <= 0:
        raise Refused(f"{what}: must be positive, got {d}")
    return d


def _n(v, what):
    if v is None or isinstance(v, bool) or not isinstance(v, int) or v <= 0:
        raise Refused(f"{what}: a positive whole count is required, got {v!r}")
    return v


def sqrt(x):
    return _C.sqrt(BR.D(x))


def hyp(a, b):
    return sqrt(_C.add(_C.multiply(BR.D(a), BR.D(a)), _C.multiply(BR.D(b), BR.D(b))))


def riser(storey_rise, storey_risers):
    return _C.divide(_m(storey_rise, "storey rise"), X(_n(storey_risers, "storey risers")))


# ------------------------------------------------------------------ R-T715-1
def straight_flight(*, rise_m, risers, goings, width_m, going_m, tread_t_m, unit="m"):
    """rise_m: the storey (or flight) riser height source: pass the riser height itself (Decimal) or a (rise, count)
    tuple. Returns exact Decimals; rounding at the statement."""
    if unit != "m":
        raise Refused(f"unit {unit!r} refused (metres only)")
    r = riser(*rise_m) if isinstance(rise_m, tuple) else _m(rise_m, "riser")
    n = _n(risers, "risers")
    g = _n(goings, "goings")
    if g not in (n - 1, n):
        raise Refused(f"goings {g} must be risers - 1 (ends on a floor / landing edge) or risers (ends on a winder)")
    w, go, t = _m(width_m, "width"), _m(going_m, "going"), _m(tread_t_m, "tread marble t")
    vis = _C.subtract(r, t)
    if vis <= 0:
        raise Refused(f"visible riser {vis} <= 0")
    return {"rule": "R-T715-1", "riser_m": r, "visible_m": vis,
            "riser_m2": BR.mul(n, w, vis), "pitch_lm": BR.mul(g, hyp(go, r)), "step_lm": BR.mul(g, w)}


# ------------------------------------------------------------------ R-T715-2
def turn_region(*, region_m2, risers_section, risers_plan=None, governing="SECTION", treads, lane_width_m, riser_m,
                tread_t_m):
    if governing != "SECTION":
        raise Refused("R-T715-2: the turn's riser count must come from a governing section (Q-46 A)")
    n = _n(risers_section, "turn risers (section)")
    k = _n(treads, "turn treads")
    if k not in (n - 1, n):
        raise Refused(f"turn treads {k} must be risers {n} - 1 or risers")
    a = _m(region_m2, "turn region area")
    w, r, t = _m(lane_width_m, "lane width"), _m(riser_m, "riser"), _m(tread_t_m, "tread marble t")
    vis = _C.subtract(r, t)
    if vis <= 0:
        raise Refused(f"visible riser {vis} <= 0")
    return {"rule": "R-T715-2", "tread_m2": a, "tread_basis": "region area (subdivision-independent tiling)",
            "step_lm_at_least": BR.mul(k, w), "riser_m2_at_least": BR.mul(n, w, vis),
            "plan_count_beside": risers_plan, "pitch": "HELD (walking line not drawn)"}


# ------------------------------------------------------------------ R-T715-3
def carrier_check(dup_element, carrier_element, item_code, candidate_lines):
    """candidate_lines: {(element_id, item_code): class}. NOT_APPLICABLE only with a carrier line of the same code."""
    if dup_element == carrier_element:
        raise Refused("R-T715-3: a reading cannot be its own carrier")
    cls = candidate_lines.get((carrier_element, item_code))
    if cls is None:
        raise Refused(f"R-T715-3: no carrier line {item_code} on {carrier_element}: the duplicate is the carrier")
    if cls == "EXCLUDED":
        raise Refused(f"R-T715-3: carrier {carrier_element} {item_code} is itself EXCLUDED")
    return {"rule": "R-T715-3", "class_after": "NOT_APPLICABLE", "carrier": carrier_element, "carrier_class": cls}


# ------------------------------------------------------------------ R-T715-4
def skirt_forms(*, plan_m, risers_in, riser_m, run_m, rise_m, returns_m="0"):
    p = _m(plan_m, "plan") if BR.D(plan_m) != 0 else X(0)
    if p < 0:
        raise Refused("plan < 0")
    n = risers_in
    if not isinstance(n, int) or isinstance(n, bool) or n < 0:
        raise Refused(f"risers inside {n!r}")
    r = _m(riser_m, "riser")
    ret = BR.D(returns_m)
    if ret < 0:
        raise Refused("returns < 0")
    zig = BR.add(p, BR.mul(n, r), ret)
    if p == 0:
        if n == 0:
            raise Refused("a stretch with no plan length and no riser is not a skirting piece")
        slo = None                       # UP-STAIR-011 has no rake over a zero run (lone step): not defined
    else:
        run, rise = _m(run_m, "flight run"), _m(rise_m, "flight rise")
        slo = BR.add(_C.divide(_C.multiply(p, hyp(run, rise)), run), ret)
    if slo is not None and slo > zig:
        raise Refused("sloped > zigzag: inputs inconsistent")
    return {"rule": "R-T715-4", "zigzag_lm": zig, "sloped_lm": slo}


def corner_turn(*, plan_a_m, plan_b_m, turn_rise_m):
    a, b, R = _m(plan_a_m, "wall a"), _m(plan_b_m, "wall b"), _m(turn_rise_m, "turn rise")
    s_lo = hyp(BR.add(a, b), R)
    s_hi = max(BR.add(hyp(a, R), b), BR.add(a, hyp(b, R)))
    return {"rule": "R-T715-4", "zig_pair": BR.add(a, b, R), "zig_a": (a, BR.add(a, R)), "zig_b": (b, BR.add(b, R)),
            "slo_pair": (s_lo, s_hi), "slo_a": (a, hyp(a, R)), "slo_b": (b, hyp(b, R))}


# ------------------------------------------------------------------ statement guard
CLASSES = ("MEASURED", "CONDITIONAL_ON_FORM", "AT_LEAST", "AT_MOST", "RANGE", "NOT_APPLICABLE", "BLANK_NAMED",
           "WIRING_GAP")


def statement(line, cls, *, value=None, low=None, high=None, status, cause, carrier=None, item=None):
    if cls not in CLASSES:
        raise Refused(f"{line}: class {cls}")
    st = {"line_id": line, "class": cls, "status": status, "cause": cause, "value": None, "low": None, "high": None,
          "carrier": carrier, "item": item}
    if cls in ("MEASURED", "CONDITIONAL_ON_FORM"):
        if value is None or BR.D(value) <= 0:
            raise Refused(f"{line}: {cls} needs a positive value")
        st["value"] = str(BR.round_point(value))
    elif cls == "AT_LEAST":
        if low is None or BR.D(low) <= 0 or high is not None:
            raise Refused(f"{line}: AT_LEAST is a positive floor alone")
        st["low"] = str(BR.round_low(low))
    elif cls == "AT_MOST":
        if high is None or BR.D(high) <= 0 or low is not None:
            raise Refused(f"{line}: AT_MOST is a positive ceiling alone (low 0 is implied by 'no wall')")
        st["high"] = str(BR.round_high(high))
    elif cls == "RANGE":
        lo, hi = BR.D(low), BR.D(high)
        if lo <= 0 or hi < lo:
            raise Refused(f"{line}: RANGE needs 0 < low <= high")
        st["low"], st["high"] = str(BR.round_low(lo)), str(BR.round_high(hi))
    elif cls == "NOT_APPLICABLE":
        if not cause:
            raise Refused(f"{line}: NOT_APPLICABLE names its evidence")
    elif cls == "BLANK_NAMED":
        if not item:
            raise Refused(f"{line}: a blank line names its item")
    if value is not None and cls not in ("MEASURED", "CONDITIONAL_ON_FORM"):
        raise Refused(f"{line}: {cls} carries no point value")
    return st
