"""T-696 (b): R-T696-1 BOUND_ROUNDING_V1 on a hand fixture 'Villa M' (not the development villa).

Villa M, one 0.15 m black block wall on the 40 x 20 module (kappa = 0.39 x 0.19 / (0.40 x 0.20) = 0.92625):
  f = kappa x 0.15 x 0.010 = 0.001389375 m3 per m of joint.
  - a lintel whose bearing is HELD (lintel itself held): bed 0 .. 2 x 0.40 x f = 0 .. 0.0011115 m3 exactly;
    half-way 6 dp prints 0.001111 (BELOW the exact high): R-T696-1 prints 0.001112.
  - a lintel with one deficit end: bearing 0.40 .. 0.62 m -> 0.00055575 .. 0.0008614125 m3;
    half-way prints 0.000556 .. 0.000861 (low ABOVE the exact low, high BELOW): R-T696-1 0.000555 .. 0.000862.
  - a wall area 31.0001 .. 31.4001 m2 x 12.5 = 387.50125 .. 392.50125 pcs (exact at 5 dp: unchanged);
    x 0.0110625 m3/m2 = 0.342938606.. .. 0.347363606.. -> 0.342938 .. 0.347364.
"""
import decimal
import importlib.util
from decimal import Decimal
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location("bound_rounding_v1", ROOT / "research/agents_t696/bound_rounding_v1.py")
BR = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(BR)

F = BR.mul("0.39", "0.19", "0.15", "0.010") / BR.mul("0.40", "0.20")


def test_factor_is_exact():
    assert F == Decimal("0.001389375")


# ------------------------------------------------------------------------------------------------ normal
def test_held_lintel_bed_high_rounds_up():
    lo, hi = BR.bound(0, BR.mul(2, "0.40", F))
    assert (lo, hi) == (Decimal("0.000000"), Decimal("0.001112"))


def test_deficit_bed_both_ends_directed():
    lo, hi = BR.bound(BR.mul("0.40", F), BR.mul("0.62", F))
    assert BR.mul("0.62", F) == Decimal("0.0008614125")
    assert (lo, hi) == (Decimal("0.000555"), Decimal("0.000862"))


def test_exact_at_precision_is_not_widened():
    lo, hi = BR.bound(BR.mul("31.0001", "12.5"), BR.mul("31.4001", "12.5"))
    assert (lo, hi) == (Decimal("387.501250"), Decimal("392.501250"))


def test_mortar_range():
    r = BR.mul("0.15", BR.add(1, -(BR.mul("0.39", "0.19") / BR.mul("0.40", "0.20"))))
    assert r == Decimal("0.0110625")
    lo, hi = BR.bound(BR.mul("31.0001", r), BR.mul("31.4001", r))
    assert (lo, hi) == (Decimal("0.342938"), Decimal("0.347364"))


def test_point_value_keeps_half_up():
    assert BR.bound(BR.mul("0.80", F), BR.mul("0.80", F)) == (Decimal("0.001112"), Decimal("0.001112"))
    assert BR.round_point("0.0011114") == Decimal("0.001111")


# ------------------------------------------------------------------------------------------------ adverse
def test_task_case_high_never_prints_below():
    """ACCEPTANCE: a 0.0011115 high bound never prints 0.001111."""
    assert BR.bound("0", "0.0011115")[1] == Decimal("0.001112")
    assert BR.bound(0.0, 0.0011115)[1] == Decimal("0.001112")       # float input through its printed repr
    assert BR.round_high("0.0011115") != Decimal("0.001111")


def test_mirror_summation_order_does_not_matter():
    parts = ["0.000277875", "0.0040218", "0.000403335", "0.0000040"]
    a = BR.bound(0, BR.add(*parts))
    b = BR.bound(0, BR.add(*reversed(parts)))
    assert a == b == (Decimal("0.000000"), Decimal("0.004708"))


def test_negative_bound_directions():
    assert BR.bound("-0.0000015", "-0.0000005") == (Decimal("-0.000002"), Decimal("-0.000000"))


def test_missing_is_never_zero():
    with pytest.raises(BR.BoundRoundingError):
        BR.bound(None, "0.1")
    with pytest.raises(BR.BoundRoundingError):
        BR.D(float("nan"))
    with pytest.raises(BR.BoundRoundingError):
        BR.D(True)


def test_inverted_bound_refused():
    with pytest.raises(BR.BoundRoundingError):
        BR.bound("0.2", "0.1")


def test_already_rounded_end_refused():
    with pytest.raises(BR.BoundRoundingError):
        BR.bound("0.000556", "0.001111", exact=False)


def test_bad_precision_refused():
    with pytest.raises(BR.BoundRoundingError):
        BR.round_high("0.1", dp=-1)
    with pytest.raises(BR.BoundRoundingError):
        BR.round_high("0.1", dp=2.0)


def test_units_millimetres_stay_exact():
    """a length in mm (400) is not silently a metre figure: the rule rounds what it is given, the caller's unit
    guard decides; 400 mm x f stays 400 x f (no hidden /1000)."""
    assert BR.bound(0, BR.mul(400, F))[1] == Decimal("0.555750")


def test_global_decimal_context_untouched():
    before = decimal.getcontext().prec
    BR.bound("0", BR.mul("3.333333333333333333", "0.000000123"))
    assert decimal.getcontext().prec == before
