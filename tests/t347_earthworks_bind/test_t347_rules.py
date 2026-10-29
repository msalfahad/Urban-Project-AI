"""T-347 rules on a hand-made villa T347-X (not Alsenan; every figure calculated by hand below).

Villa T347-X, existing ground EG +-0.00, formation 'not less than 1.50 m' (a minimum), lift pit floor printed -1.80.
  P1 footing 2.00 x 1.80 x 0.50, neat pit (blinding +0.10 each side) 2.20 x 2.00 = 4.400 m2
  P2 footing 1.40 x 1.40 x 0.40, neat 1.60 x 1.60 = 2.560 m2; P1 / P2 neat plans overlap 0.20 x 1.60 = 0.320 m2
  strap S1 3.00 x 0.30 x 0.50 between them (no blinding projection printed: neat plan HELD)
  lift pit LP neat 2.40 x 2.40 = 5.760 m2, floor printed -1.80 -> 10.368 m3 (a VALUE)
Hand: net pit plan 4.400 + 2.560 - 0.320 = 6.640 m2; pits AT_LEAST 6.640 x 1.50 = 9.960 m3 (+ 6.640 m3 per m below).
Displacement P1 + P2 at d = 0: blinding 0.440 + 0.256 - 0.032 = 0.664; footings 1.800 + 0.784 = 2.584; necks 0.2 x 0.2
x (1.50 - 0.10 - 0.50) = 0.036 and 0.2 x 0.2 x (1.50 - 0.10 - 0.40) = 0.040 -> 3.324 m3 (+ 0.08 m3 per m of d).
Backfill >= 9.960 - 3.324 = 6.636 m3 (monotone: 6.640 > 0.08 per m).
"""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t347"))
import t347_rules as R  # noqa: E402


def test_net_plan_two_overlapping_pits():
    assert R.net_plan({"P1": 4.40, "P2": 2.56}, {("P1", "P2"): 0.32}) == pytest.approx(6.64, abs=1e-9)


def test_mirror_and_order_invariant():
    a = R.net_plan({"P1": 4.40, "P2": 2.56}, {("P1", "P2"): 0.32})
    b = R.net_plan({"P2": 2.56, "P1": 4.40}, {("P2", "P1"): 0.32})
    assert a == b


def test_overlap_counted_twice_refused():
    with pytest.raises(R.Refused):
        R.net_plan({"P1": 4.40, "P2": 2.56}, {("P1", "P2"): 0.32, ("P2", "P1"): 0.32})


def test_triple_point_refused_unless_stated():
    with pytest.raises(R.Refused):
        R.refuse_triple({(0, 0): ["P1", "P2", "P3"]})
    with pytest.raises(R.Refused):
        R.net_plan({"A": 1, "B": 1, "C": 1}, {("A", "B"): .1, ("B", "C"): .1, ("A", "C"): .1}, {("A", "B", "C"): None})
    assert R.net_plan({"A": 1, "B": 1, "C": 1}, {("A", "B"): .1, ("B", "C"): .1, ("A", "C"): .1},
                      {("A", "B", "C"): .05}) == pytest.approx(2.75)


def test_printed_minimum_is_a_bound_not_the_founding_level():
    assert R.depth("PRINTED_MINIMUM", 1.50) == ("AT_LEAST", 1.50)
    assert R.depth("PRINTED_VALUE", 1.80) == ("VALUE", 1.80)
    assert R.depth("NOT_PRINTED", None) == ("HELD", None)
    with pytest.raises(R.Refused):
        R.depth("NOT_PRINTED", 1.50)


def test_fill_pits_and_lift_pit():
    cls, d = R.depth("PRINTED_MINIMUM", 1.50)
    pits = R.part(cls, lo=6.64 * d)
    lift = R.part("VALUE", value=5.76 * 1.80)
    agg = R.aggregate([pits, lift])
    assert agg["value"] is None                      # a bound in the row: no m3
    assert agg["lo"] == pytest.approx(9.96 + 10.368)
    assert agg["hi"] is None
    assert agg["classes"] == "VALUE 1; AT_LEAST 1"


def test_held_formation_written_as_zero_refused():
    with pytest.raises(R.Refused):
        R.part("HELD", value=0.0, held="formation")
    with pytest.raises(R.Refused):
        R.part("HELD", held="")
    row = {"row_id": "X", "status": "HELD", "value_m3": 0.0, "held_items": "formation"}
    with pytest.raises(R.Refused):
        R.check_fill_row(row)
    agg = R.aggregate([R.part("HELD", held="strap neat plan")])
    assert agg["value"] is None and agg["lo"] is None and agg["hi"] is None


def test_backfill_bound_from_proved_direction():
    disp_hi = 0.664 + 2.584 + 0.036 + 0.040
    assert R.backfill_lo(9.96, disp_hi, monotone_in_depth=6.64 > 0.08) == pytest.approx(6.636)
    with pytest.raises(R.Refused):
        R.backfill_lo(9.96, disp_hi, monotone_in_depth=False)
    assert R.backfill_lo(None, disp_hi, True) is None


def test_one_displacement_bound_to_two_lines_refused():
    lines = {"L-a": {"quantity": 2.0}, "L-b": {"quantity": 1.0}}
    rows = [{"id": "P1:FOOTING", "value_m3": 1.8}]
    with pytest.raises(R.Refused):
        R.bind(rows, lines, {"P1:FOOTING": ("L-a", "L-b")})
    with pytest.raises(R.Refused):
        R.bind(rows, lines, {"P1:FOOTING": "L-zzz"})
    with pytest.raises(R.Refused):
        R.bind(rows, lines, {})
    with pytest.raises(R.Refused):
        R.bind(rows + rows, lines, {"P1:FOOTING": "L-a"})
    out, load = R.bind(rows, lines, {"P1:FOOTING": "L-a"})
    assert out == [("P1:FOOTING", "L-a", "")]


def test_line_capacity_and_blank_line():
    lines = {"L-f": {"quantity": 2.584}, "L-h": {"quantity": None}}
    rows = [{"id": "P1", "value_m3": 1.800}, {"id": "P2", "value_m3": 0.784}]
    R.bind(rows, lines, {"P1": "L-f", "P2": "L-f"})
    with pytest.raises(R.Refused):   # P1 counted on a line already full
        R.bind(rows + [{"id": "P1b", "value_m3": 1.8}], lines, {"P1": "L-f", "P2": "L-f", "P1b": "L-f"})
    with pytest.raises(R.Refused):   # a value carried through a blank line
        R.bind([{"id": "N1", "value_m3": 0.036, "status": "DRAWING-CONFIRMED"}], lines, {"N1": "L-h"})
    R.bind([{"id": "N1", "value_m3": 0.036, "status": "HELD"}], lines, {"N1": "L-h"})
    out, _ = R.bind([{"id": "W", "value_m3": 7.29}], lines, {"W": ("NO_LINE", "pool water space: a void")})
    assert out[0][1] is None
    with pytest.raises(R.Refused):
        R.bind([{"id": "W", "value_m3": 7.29}], lines, {"W": ("NO_LINE", "")})


def test_units_declared():
    assert R.metres(1500, "mm") == 1.5
    assert R.metres(1.5, "m") == 1.5
    with pytest.raises(R.Refused):
        R.metres(1500, None)


def test_no_default_bulking():
    with pytest.raises(R.Refused):
        R.bulking(None)
