"""T-618 rules (any villa; research, unwired): closing small named-but-unexplained residuals between an engine BOQ and a
reference takeoff without matching figures.

R-T618-1 (proposed, every villa; provenance T-618; builds on R-T574-1 (classes and units apart), R-T578-1 (HELD blank
with bound, never 0), R-T602-1 (d) (pieces without ids are compared in aggregate; figure matching is not evidence),
R-T606-1 (a reading is ESTABLISHED only when it reproduces BOTH the reference perimeter and area inside its rounding),
ORR-007 (one flight-skirting element, its form range never summed as a point), ERS s.2-4):

  (a) RESIDUAL AGAINST A HELD RANGE IS A RANGE. When the compared scope holds a HELD quantity with bound [lo, hi] (hi may
      be unbounded), the residual his - ours is the interval [his - valued - hi, his - valued - lo]. Subtracting only
      the lower bound gives the interval's UPPER END, not a residual quantity: it is reported as a range and never as a
      point UNRESOLVED amount. A HELD piece inside the compared scope that a decomposition leaves out (hi = None) makes
      the lower end unbounded. Ranges of separate groups add end by end; an unbounded end stays unbounded.
  (b) PIECE MULTISET. A reference that books count x length pieces without ids is compared as a MULTISET of piece
      lengths against our census pieces (R-T602-1 (d) stays: no piece is assigned to an opening). A drawn READING is a
      uniform basis applied to every census opening of a class (e.g. door-leaf block width for every house door); it
      is a CANDIDATE when its multiset equals the reference multiset piece by piece inside the reference rounding, and
      only then may it be named as the cause of the aggregate residual (verdict RULE_DIFFERENCE proposal when our basis
      is set by an owner / measurement rule). A reading that matches the SUM but not the multiset is refused. It is
      never ESTABLISHED without ids on the reference rows.
  (c) UNIFORM OFFSET TEST. For a simple outline with offset coefficient k (P(t) = P + 2 k t, A(t) = A + P t + k t^2;
      k = 4 for any orthogonal outline, k > 0 measured for one with arcs), a reference gross figure that differs from
      the drawn outline by dP, dA can be a uniform face offset (centreline, plaster face, outer face) only if dP and
      dA have the same sign AND the t solved from dP reproduces dA inside the reference rounding (and vice versa).
      Opposite signs refute every uniform offset at once.
  (d) WALLED SIDES OF A LANDING. Level skirting on a stair landing is bounded by its walled length (wall lines and
      column faces lying on the landing's sides, R-T606-1 roles). A reference figure above that bound has its excess on
      faces with no wall base (risers, open stair edges): ENGINE_RIGHT on that excess if the reading is established,
      otherwise a CANDIDATE with that consequence.
  (e) NOTATION FIRST (ERS s.2.2). Where a reference books stair skirting in two rows, a length row and a per-step piece
      row whose count equals its step count, the per-step row is the flight-side skirting and the length row is the
      level (landing) skirting until the reference says otherwise; the comparison of the length row with a flight
      bound is then a cross-element comparison and is labelled so (never a residual of the flight).
  (f) Units never meet; HELD is never 0; an UNRESOLVED residual is computed, never typed; VERIFIED is the Checker's word.
"""
from __future__ import annotations

from collections import Counter
from decimal import Decimal, getcontext

getcontext().prec = 40
RULE_ID = "R-T618-1"
VERDICTS = ("ENGINE_RIGHT", "ENGINE_WRONG", "FREELANCER_RIGHT", "RULE_DIFFERENCE", "TOLERANCE", "UNRESOLVED", "HELD",
            "CANDIDATE", "NOT_DRAWN", "REFUTED")


class RuleError(ValueError):
    pass


def D(x) -> Decimal:
    if x is None:
        raise RuleError("quantity unknown (None) used as a number: HELD / UNKNOWN is never 0")
    if isinstance(x, float):
        return Decimal(repr(x))
    return Decimal(str(x))


def half_unit(places=2) -> Decimal:
    return Decimal(1).scaleb(-places) / 2


def within(value, his, places=2) -> bool:
    """strictly inside the reference's rounding of `places` decimals."""
    return abs(D(value) - D(his)) < half_unit(places)


# ---- (a) residual against HELD ranges --------------------------------------------------------------------------------
def range_residual(his, valued, held):
    """his - ours with HELD bounds [(lo, hi|None)]: returns (low end | None for unbounded, high end)."""
    lo_sum = sum((D(lo) for lo, _ in held), Decimal(0))
    if any(hi is None for _, hi in held):
        low = None
    else:
        low = D(his) - D(valued) - sum((D(hi) for _, hi in held), Decimal(0))
    high = D(his) - D(valued) - lo_sum
    if low is not None and low > high:
        raise RuleError("a HELD bound with hi < lo")
    return low, high


def add_ranges(ranges):
    low = Decimal(0)
    high = Decimal(0)
    for lo, hi in ranges:
        high += D(hi)
        low = None if (low is None or lo is None) else low + D(lo)
    return low, high


def refuse_point_residual(reported, low, high):
    """(a): a point residual equal to the range's upper end, while the range is not a point, is refused."""
    if low is not None and low == high:
        return False
    if D(reported) == D(high):
        raise RuleError(f"residual {reported} is the upper end of a HELD range [{low}, {high}], not a quantity")
    return False


# ---- (b) piece multiset ----------------------------------------------------------------------------------------------
def _key(x, places=2):
    return D(x).quantize(Decimal(1).scaleb(-places))


def multiset_compare(his, ours, places=2):
    h = Counter(_key(x, places) for x in his)
    o = Counter(_key(x, places) for x in ours)
    common = h & o
    return {"common": sorted(common.elements()), "his_only": sorted((h - o).elements()),
            "ours_only": sorted((o - h).elements()), "pieces_differing": sum((h - o).values())}


def reading_test(his, reading, places=2):
    """(b): CANDIDATE only if the reading's pieces equal his piece by piece (multiset) inside his rounding."""
    if len(his) != len(reading):
        return "REFUTED"
    hs = sorted(D(x) for x in his)
    rs = sorted(D(x) for x in reading)
    if all(within(r, h, places) for r, h in zip(rs, hs)):
        return "CANDIDATE"
    return "REFUTED"


def sum_only_match_refused(his, reading, places=2):
    if within(sum(D(x) for x in reading), sum(D(x) for x in his), places) and reading_test(his, reading) != "CANDIDATE":
        raise RuleError("the reading matches his total but not his pieces: figure matching by sum is not evidence")
    return False


# ---- (c) uniform offset ----------------------------------------------------------------------------------------------
def offset_test(P, dP, dA, k, places=2):
    P, dP, dA, k = D(P), D(dP), D(dA), D(k)
    if k <= 0:
        raise RuleError("offset coefficient k must be positive for a simple outline")
    if dP == 0 and dA == 0:
        return {"status": "NO_DIFFERENCE"}
    if (dP > 0 > dA) or (dP < 0 < dA):
        return {"status": "REFUTED", "why": "opposite signs: every uniform offset moves P and A the same way"}
    t_p = dP / (2 * k)
    dA_from_p = P * t_p + k * t_p * t_p
    # t from dA: k t^2 + P t - dA = 0, root nearest 0
    disc = (P * P + 4 * k * dA).sqrt()
    t_a = (-P + disc) / (2 * k)
    dP_from_a = 2 * k * t_a
    ok = within(dA_from_p, dA, places) and within(dP_from_a, dP, places)
    return {"status": "CANDIDATE" if ok else "REFUTED", "t_from_dP": t_p, "dA_from_dP": dA_from_p,
            "t_from_dA": t_a, "dP_from_dA": dP_from_a}


def notch_reading(dP, dA):
    """one rectangular notch (adds 2 d, removes w d) or pocket (adds 2 d, adds w d) walked round: its size, or None
    when the perimeter does not grow (neither shape can then explain it)."""
    dP, dA = D(dP), D(dA)
    if dP <= 0 or dA == 0:
        return None
    d = dP / 2
    if dA < 0:
        return {"kind": "NOTCH", "sign": "-", "depth": d, "width": -dA / d}
    return {"kind": "POCKET", "sign": "+", "depth": d, "width": dA / d}


# ---- (d) landing walled sides ----------------------------------------------------------------------------------------
def landing_bound(sides):
    """sides: {name: {"length", "walled"}} -> walled total, open total; walled never exceeds the side length."""
    w = Decimal(0)
    o = Decimal(0)
    for name, s in sides.items():
        L, wl = D(s["length"]), D(s["walled"])
        if wl > L + Decimal("0.05"):
            raise RuleError(f"side {name}: walled {wl} longer than the side {L}")
        w += wl
        o += max(L - wl, Decimal(0))
    return w, o


def excess_on_open_faces(his, walled):
    return max(D(his) - D(walled), Decimal(0))


# ---- (e) notation ----------------------------------------------------------------------------------------------------
def per_step_row_is_flight(piece_count, step_count):
    return int(piece_count) == int(step_count)


def check_verdict(v):
    if v not in VERDICTS:
        raise RuleError(f"verdict {v} unknown")
    if v == "VERIFIED":
        raise RuleError("VERIFIED is the Checker's word")
    return v
