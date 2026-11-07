"""T-578 rules (any villa; research, unwired): HANDRAILS / BALUSTRADES / GUARDS and STAIR NOSING reconciled against a
reference takeoff in lm (and nr where the reference counts pieces), every piece and every reference cell used once.

R-T578-1 (proposed, every villa; provenance T-578; builds on UP-STAIR-012 v2.0.0 (installed 3D path), UP-STAIR-013 (a
wall handrail only where shown), OWNER_RULE_STAIRS_2026-10-24 S-9 (winders never generated, no walking-line offset),
R-T412-* (one riser one nosing; drawn front edge), R-T476-1..3 / R-T480-1 (rail on the slope, one home per flight side),
R-T547-1 (bound every HELD element before any %), R-T577-1 (a number's unit is its own label; causes close exactly)
and ENGINEERING_REASONING_STANDARD s.2-4):
  (a) RAIL PIECE. Three kinds, each with its own installed length:
        INCLINED    along a flight's pitch line, first to last nosing: sqrt(plan^2 + rise^2). A plan length billed for
                    an inclined piece is refused; an inclined piece without a rise is refused.
        HORIZONTAL  a level run (landing, well end, void / floor edge): its drawn plan length; a rise on it is refused.
        TURN        a rail over winders / a closing riser whose profile is not drawn: HELD (never valued, never 0).
  (b) FAMILIES are kept apart: WALL_HANDRAIL (B7-10, only where drawn), BALUSTRADE (B7-09, the open side of a flight and
      the level band continuous with it), GUARD (B13-08, a separately drawn floor / roof / terrace edge). A reference
      figure that mixes them is compared only through named SCOPE causes, never by adding families silently.
  (c) NOSING. One nosing per riser, the arrival edge of a landing or floor included; lm = the drawn front-edge length
      less a drawn notch (a column proud of the edge). The reference's lm for a step row is its own count cell x its
      own width cell (never a conversion of an area); a width basis different from the drawn edge is its own cause.
  (d) CAUSES (signed his - ours, as the task states) close EXACTLY: his - ours = sum of causes. A HELD cause carries
      his share opposite the held pieces; our side stays blank with a bound (lo, hi; hi None = unbounded) of what the
      held pieces would add; a held piece never enters our sum and is never 0.
  (e) %. Only for a group with no HELD, SCOPE or UNIT cause and his total > 0; never an accuracy figure.
  (f) STATUS. DRAWING-CONFIRMED, ASSUMED - OWNER-APPROVED, ESTIMATED, PROVISIONAL, HELD, UNKNOWN or NOT_APPLICABLE;
      VERIFIED is the Checker's word and is refused here.
"""
from __future__ import annotations

from decimal import Decimal, getcontext

getcontext().prec = 40
KINDS = ("INCLINED", "HORIZONTAL", "TURN")
FAMILIES = ("WALL_HANDRAIL", "BALUSTRADE", "GUARD")
CAUSE_KINDS = ("MEASURE", "HELD", "SCOPE", "UNIT", "RESIDUAL")
VERDICTS = ("AGREE", "TOLERANCE", "ENGINE_RIGHT", "ENGINE_WRONG", "ENGINE_OMISSION", "RULE_DIFFERENCE", "HELD",
            "NOT_IN_HIS_ROWS", "UNRESOLVED")
STATUSES = ("DRAWING-CONFIRMED", "ASSUMED - OWNER-APPROVED", "ESTIMATED", "PROVISIONAL", "HELD", "UNKNOWN",
            "NOT_APPLICABLE")
NOSING_KINDS = ("TREAD", "WINDER", "LANDING_EDGE", "FLOOR_EDGE")
LEN_UNITS = {"m": Decimal(1), "mm": Decimal("0.001")}
TOL = Decimal("0.000001")


class RuleError(ValueError):
    pass


def D(x) -> Decimal:
    if x is None:
        raise RuleError("quantity unknown (None) used as a number: HELD / UNKNOWN is never 0")
    if isinstance(x, float):
        return Decimal(repr(x))
    return Decimal(str(x))


def _len(x, unit="m"):
    if unit not in LEN_UNITS:
        raise RuleError(f"length unit {unit!r} unknown (m or mm only)")
    v = D(x) * LEN_UNITS[unit]
    if v < 0:
        raise RuleError("a length is never negative")
    return v


def _status(s):
    if s == "VERIFIED":
        raise RuleError("VERIFIED is the Checker's word, never set by a worker build")
    if s not in STATUSES:
        raise RuleError(f"status {s!r} unknown")
    return s


# ---- (a) rail pieces -------------------------------------------------------------------------------------------------
def rail_length(kind, plan, rise=None, unit="m", places=6):
    """Installed length of one rail piece (R-T578-1 (a)); 6 dp."""
    if kind not in KINDS:
        raise RuleError(f"rail piece kind {kind!r} unknown")
    if kind == "TURN":
        raise RuleError("a TURN piece (profile not drawn) is HELD: it has no length, and never 0")
    p = _len(plan, unit)
    q = Decimal(1).scaleb(-places)
    if kind == "INCLINED":
        if rise is None or _len(rise, unit) == 0:
            raise RuleError("an inclined rail without a rise: the pitch length cannot be formed (HELD, never the plan)")
        r = _len(rise, unit)
        return (p * p + r * r).sqrt().quantize(q)
    if rise is not None and _len(rise, unit) != 0:
        raise RuleError("a horizontal rail piece with a rise: it is INCLINED")
    return p.quantize(q)


def check_billed(kind, plan, rise, billed, unit="m", curved=False):
    """A billed figure must be the installed length; the plan length of an inclined piece is refused by name. A curved
    flight billed per going (one sloped piece per going, T-476) cannot be recomputed from its totals: it is accepted
    only between the straight pitch line and plan + rise (R-T480-1)."""
    want = rail_length(kind, plan, rise, unit)
    b = _len(billed, unit)
    if kind == "INCLINED" and abs(b - _len(plan, unit)) <= TOL and want - _len(plan, unit) > TOL:
        raise RuleError("plan length billed for an inclined rail: the installed length is along the pitch")
    if curved:
        if kind != "INCLINED":
            raise RuleError("only an inclined piece can be a curved flight")
        if not (want - TOL <= b <= _len(plan, unit) + _len(rise, unit) + TOL):
            raise RuleError(f"curved flight billed {b} outside [pitch {want}, plan + rise]")
        return b
    if abs(b - want) > TOL:
        raise RuleError(f"billed {b} is not the installed length {want}")
    return want


def turn_bound(plan, rise, unit="m"):
    """A drawn rail whose turn profile is not drawn: it at least spans its two drawn ends (the chord); no upper bound."""
    p, r = _len(plan, unit), _len(rise, unit)
    return ((p * p + r * r).sqrt().quantize(Decimal("0.000001")), None)


def existence_bound(extent=None):
    """A band whose element is UNKNOWN (rail or edge): 0 .. its drawn extent (None when no extent is printed)."""
    return (Decimal(0), None if extent is None else D(extent))


def rail_piece(pid, family, kind, status, plan=None, rise=None, billed=None, bound=None, run=None, curved=False):
    if family not in FAMILIES:
        raise RuleError(f"family {family!r} unknown")
    _status(status)
    if status in ("HELD", "UNKNOWN"):
        if billed is not None:
            raise RuleError(f"{pid}: a HELD / UNKNOWN piece carries no figure (never 0)")
        if bound is None:
            raise RuleError(f"{pid}: a HELD / UNKNOWN piece needs a bound (lo, hi)")
        return {"id": pid, "family": family, "kind": kind, "status": status, "value": None, "bound": bound, "run": run}
    if status == "NOT_APPLICABLE":
        return {"id": pid, "family": family, "kind": kind, "status": status, "value": None, "bound": None, "run": run}
    v = check_billed(kind, plan, rise, billed, curved=curved)
    return {"id": pid, "family": family, "kind": kind, "status": status, "value": v, "bound": None, "run": run,
            "curved": curved}


def plan_from_points(p, q, unit="m", places=6):
    """Plan length between two drawn points (x, y), any rotation or mirror."""
    import math
    if unit not in LEN_UNITS:
        raise RuleError(f"length unit {unit!r} unknown (m or mm only)")
    d = math.hypot(float(q[0]) - float(p[0]), float(q[1]) - float(p[1]))
    return (D(d) * LEN_UNITS[unit]).quantize(Decimal(1).scaleb(-places))


# ---- (c) nosing ------------------------------------------------------------------------------------------------------
def nosing_lm(edge, notch=0, unit="m"):
    e, n = _len(edge, unit), _len(notch, unit)
    if n > e:
        raise RuleError("a notch longer than its edge")
    return e - n


def nosing_piece(eid, stair, kind, status, edge=None, notch=0, beside=None):
    """One nosing per riser. A HELD edge carries no figure (a 0 is refused) and its drawn-beside length, or None when
    nothing is drawn for it."""
    if kind not in NOSING_KINDS:
        raise RuleError(f"nosing kind {kind!r} unknown")
    _status(status)
    if status in ("HELD", "UNKNOWN"):
        if edge is not None:
            raise RuleError(f"{eid}: a HELD nosing carries no figure (never 0)")
        # bound: 0 .. the length drawn beside the blank (the reading is not established); None when nothing is drawn
        return {"id": eid, "stair": stair, "kind": kind, "status": status, "value": None,
                "bound": (Decimal(0), None if beside is None else D(beside))}
    return {"id": eid, "stair": stair, "kind": kind, "status": status, "value": nosing_lm(edge, notch),
            "notch": _len(notch), "edge": _len(edge), "bound": None}


def his_row_lm(count, width):
    """His lm for a step row = his count cell x his width cell (R-T578-1 (c)); a missing cell is refused."""
    c = D(count)
    if c != c.to_integral_value() or c < 0:
        raise RuleError("a piece count is a non-negative whole number")
    return c * _len(width)


# ---- (d) causes ------------------------------------------------------------------------------------------------------
def cause(label, amount, verdict, kind, source, bound=None):
    if verdict not in VERDICTS:
        raise RuleError(f"verdict {verdict!r} unknown")
    if kind not in CAUSE_KINDS:
        raise RuleError(f"cause kind {kind!r} unknown")
    a = D(amount)
    if kind == "HELD":
        if bound is None:
            raise RuleError("a HELD cause needs the bound of what the held pieces would add")
    c = {"label": label, "amount": a, "verdict": verdict, "kind": kind, "source": source}
    if bound is not None:
        c["bound"] = bound
    return c


def close(his, ours, causes):
    """his - ours = sum of causes, exactly; an unnamed residual is refused."""
    gap = D(his) - D(ours)
    s = sum((c["amount"] for c in causes), Decimal(0))
    if s != gap:
        raise RuleError(f"causes {s} do not close the gap {gap}: residual {gap - s} unnamed")
    return gap


def ours_total(pieces):
    """Sum of valued pieces; HELD / UNKNOWN never enter; NOT_APPLICABLE carry nothing."""
    tot = Decimal(0)
    for p in pieces:
        if p["status"] in ("HELD", "UNKNOWN"):
            if p.get("value") is not None:
                raise RuleError(f"{p['id']}: a HELD piece with a value")
            continue
        if p["status"] == "NOT_APPLICABLE":
            continue
        tot += D(p["value"])
    return tot


def held_bound(pieces):
    hs = [p["bound"] for p in pieces if p["status"] in ("HELD", "UNKNOWN")]
    lo = sum((D(b[0]) for b in hs), Decimal(0))
    hi = None if any(b[1] is None for b in hs) else sum((D(b[1]) for b in hs), Decimal(0))
    return lo, hi


def pct(his, ours, causes):
    if any(c["kind"] in ("HELD", "SCOPE", "UNIT") for c in causes) or D(his) <= 0:
        return None
    return ((D(his) - D(ours)) / D(his) * 100).quantize(Decimal("0.01"))
