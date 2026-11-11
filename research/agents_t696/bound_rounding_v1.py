"""BOUND_ROUNDING_V1 (rule R-T696-1, research version; every villa): directed rounding of a bounded quantity.

Physical meaning first. A bounded line says "the installed quantity lies in [low, high]". The printed figures must keep
that statement true after rounding to the reporting precision: the printed HIGH may never sit below the exact high
and the printed LOW may never sit above the exact low. Half-way rounding (the rule the V3.0.68 producers apply to both
ends) breaks this whenever the exact high has a digit below the reporting step that rounds down (Checker F-V672-1:
D-1F-09 bed high 2 x 0.40 x 0.001389375 = 0.0011115 m3 printed 0.001111; D-1F-03 0.638520 x 0.001389375 =
0.00088715... printed 0.000887).

Rule:
  (1) low  -> rounded toward minus infinity (floor) at the reporting precision;
  (2) high -> rounded toward plus infinity (ceiling) at the reporting precision;
  (3) a point value (low = high: an EXACT / VALUE line, not a bound) keeps half-up rounding (unchanged, not a bound);
  (4) the exact end is the product / sum of the line's own stated inputs (lengths, areas, factors, rates at the
      precision their ledger records them) computed in decimal arithmetic, NOT an already-rounded figure: a rounded
      intermediate is refused when it is offered as an end (`exact=False`), because ceiling a half-way-rounded
      number can still sit below the exact value;
  (5) a bound is never widened by more than one reporting step per end, and low <= high after rounding (asserted);
  (6) nothing becomes 0: a missing input is an error, never a zero.

Decimal arithmetic uses a LOCAL context only (never the process-global precision: F-T648-2).
"""
from __future__ import annotations

from decimal import ROUND_CEILING, ROUND_FLOOR, ROUND_HALF_UP, Context, Decimal

RULE_ID = "R-T696-1"
RULE_VERSION = "1.0.0"
METHOD = "BOUND_ROUNDING_V1"
REPORT_DP = 6                      # the candidate prints m3 / pcs / kg at 6 decimals
_CTX = Context(prec=50)            # local context: exact for every product / sum this rule meets


class BoundRoundingError(ValueError):
    pass


def D(x) -> Decimal:
    """an input as an exact decimal: int, str or Decimal; a float is converted through its shortest repr (the figure
    as the ledger prints it), never through its binary expansion."""
    if x is None:
        raise BoundRoundingError("a missing input is never 0 (R-T696-1 (6))")
    if isinstance(x, bool):
        raise BoundRoundingError("a boolean is not a quantity")
    if isinstance(x, Decimal):
        return x
    if isinstance(x, (int, str)):
        return Decimal(x)
    if isinstance(x, float):
        if x != x or x in (float("inf"), float("-inf")):
            raise BoundRoundingError("not a finite number")
        return Decimal(repr(x))
    raise BoundRoundingError(f"not a number: {type(x).__name__}")


def mul(*xs) -> Decimal:
    out = Decimal(1)
    for x in xs:
        out = _CTX.multiply(out, D(x))
    return out


def add(*xs) -> Decimal:
    out = Decimal(0)
    for x in xs:
        out = _CTX.add(out, D(x))
    return out


def _q(dp):
    if not isinstance(dp, int) or dp < 0 or dp > 12:
        raise BoundRoundingError(f"reporting precision {dp!r} is not 0..12 decimals")
    return Decimal(1).scaleb(-dp)


def round_low(x, dp=REPORT_DP) -> Decimal:
    return D(x).quantize(_q(dp), rounding=ROUND_FLOOR)


def round_high(x, dp=REPORT_DP) -> Decimal:
    return D(x).quantize(_q(dp), rounding=ROUND_CEILING)


def round_point(x, dp=REPORT_DP) -> Decimal:
    return D(x).quantize(_q(dp), rounding=ROUND_HALF_UP)


def bound(low, high, dp=REPORT_DP, *, exact=True):
    """exact [low, high] -> printed [floor(low), ceil(high)] at dp. `exact` must be True: the ends are the exact
    products / sums of the stated inputs (R-T696-1 (4))."""
    if not exact:
        raise BoundRoundingError("an already-rounded end cannot be directed-rounded (R-T696-1 (4)): recompute it "
                                 "from its inputs")
    lo, hi = D(low), D(high)
    if lo > hi:
        raise BoundRoundingError(f"low {lo} > high {hi}")
    if lo == hi:
        p = round_point(lo, dp)
        return p, p
    rl, rh = round_low(lo, dp), round_high(hi, dp)
    step = _q(dp)
    if not (rl <= lo and hi <= rh and lo - rl < step and rh - hi < step and rl <= rh):
        raise BoundRoundingError("directed rounding invariant broken")   # cannot happen; asserted
    return rl, rh


def as_float(x: Decimal) -> float:
    return float(x)


def half_way(x, dp=REPORT_DP) -> float:
    """the producers' present half-way rounding (round(x, dp) on the binary float), for the before / after delta."""
    return round(float(D(x)), dp)
