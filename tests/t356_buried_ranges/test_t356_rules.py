"""T-356 rules on a hand-calculated villa that is NOT the development villa (villa T356-X).

Villa T356-X (all by hand, metres):
  pads P1 1.60 x 1.60 at x 0.00 .. 1.60 and P2 1.60 x 1.60 at x 5.00 .. 6.60; strap S 0.50 wide on y -0.25 .. 0.25
  between them: clear 3.40 m. Blinding projection 0.10, thickness 0.10.
    own strip   (0.50 + 0.20) x 3.40 = 2.380 m2 -> 0.2380 m3
    merged      2.380 - 2 ends x 0.10 x 0.70 (the pads' blinding band) = 2.240 m2 -> 0.2240 m3
  boundary band 0.20 wide, drawn centreline 40.00 m, 6.00 m through footings, printed sections 20 x 40 and 20 x 60:
    low (40 - 6) x 0.20 x 0.40 = 2.720 m3; high 40 x 0.20 x 0.60 = 4.800 m3; pad 1.30 x 0.20 x 0.30 = 0.078 each
  ground-beam titles > 5 m: 0.60, < 5 m: 0.40, < 2.5 m: 0.30 (b 0.30)
"""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t356"))
import t356_rules as R  # noqa: E402

A = pytest.approx
TITLES = [("GT5M", ">", 5.0, 0.60), ("LT5M", "<", 5.0, 0.40), ("LT2_5M", "<", 2.5, 0.30)]


# ---- strap blinding (R-T356-2) ------------------------------------------------------------------------------------
def test_strap_without_printed_blinding_low_is_reading_none():
    r = R.strap_blinding_range(2.38, 0.10, False, merged_strip_m2=2.24)
    assert (r["low"], r["high"], r["merged"], r["status"]) == (A(0.0), A(0.238), A(0.224), "HELD")


def test_strap_with_printed_blinding_level_open():
    r = R.strap_blinding_range(2.38, 0.10, True, merged_strip_m2=2.24)
    assert (r["low"], r["high"]) == (A(0.224), A(0.238))


def test_adverse_ground_beam_above_never_deducted():
    with pytest.raises(R.Refused):
        R.strap_blinding_range(2.38, 0.10, False, gb_plan_overlap_m2=0.30, gb_vertical_gap_m=0.28)
    with pytest.raises(R.Refused):                       # a level not established is not a shared level either
        R.strap_blinding_range(2.38, 0.10, False, gb_plan_overlap_m2=0.30)


def test_adverse_merged_larger_than_own_refused():
    with pytest.raises(R.Refused):
        R.strap_blinding_range(2.24, 0.10, False, merged_strip_m2=2.38)


# ---- boundary band (R-T356-3 / -4) ----------------------------------------------------------------------------------
def test_band_range_by_hand():
    r = R.band_range(40.0, 6.0, 0.20, (0.40, 0.60))
    assert (r["low"], r["high"]) == (A(2.72), A(4.80))


def test_adverse_single_reading_carried_as_line_value():
    # a line showing one section x one length (34 m x 0.20 x 0.60 = 4.08) inside the range is still CORRECT_RANGE
    assert R.verdict(4.08, 4.08, 2.72, 4.80) == "CORRECT_RANGE"
    assert R.verdict(2.72, 4.80, 2.72, 4.80) == "LINE_RIGHT"


def test_adverse_lost_side_length_inside_range_is_not_a_reading():
    # 3 of 4 sides of a 12 x 8 band (centreline 40): 32 m x 0.20 x 0.60 = 3.84 lies inside [2.72, 4.80] by chance
    assert R.verdict(3.84, 3.84, 2.72, 4.80) == "CORRECT_RANGE"


def test_band_line_low_not_established_without_pad_count():
    assert R.band_line_low(2.72, 0.078, None) is None
    assert R.band_line_low(2.72, 0.078, 4) == A(2.72 - 0.312)
    with pytest.raises(R.Refused):
        R.band_line_low(2.72, 0.078, 2.5)


def test_adverse_crossing_longer_than_band_and_mm_input():
    with pytest.raises(R.Refused):
        R.band_range(40.0, 41.0, 0.20, (0.40,))
    with pytest.raises(R.Refused):
        R.band_range(40000.0, 6000.0, 0.20, (0.40, 0.60))


# ---- length-class titles (R-T356-5) ----------------------------------------------------------------------------------
def test_short_span_both_titles_hold():
    held = R.class_titles([1.80, 2.10], TITLES)
    assert [t[0] for t in held] == ["LT2_5M", "LT5M"]
    r = R.depth_range(0.54, held)                       # 1.80 x 0.30 plan
    assert (r["low"], r["high"], r["single"]) == (A(0.162), A(0.216), False)


def test_boundary_length_keeps_both_neighbours():
    held = R.class_titles([5.00, 5.30], TITLES)
    assert [t[0] for t in held] == ["LT5M", "GT5M"]
    held = R.class_titles([5.00], TITLES)               # exactly 5.00: no title literally, both neighbours
    assert [t[0] for t in held] == ["LT5M", "GT5M"]


def test_long_span_single_title():
    held = R.class_titles([6.0, 6.3], TITLES)
    assert [t[0] for t in held] == ["GT5M"]
    assert R.depth_range(1.80, held)["single"] is True


def test_adverse_most_specific_pick_is_not_the_rule():
    held = R.class_titles([1.80, 2.10], TITLES)
    picked = min(held, key=lambda t: t[2])              # 'most specific' = a precedence the drawing does not print
    assert R.depth_range(0.54, held)["high"] > 0.54 * picked[3]
    assert R.verdict(0.162, 0.162, 0.162, 0.216) == "CORRECT_RANGE"


# ---- blank never 0 --------------------------------------------------------------------------------------------------
def test_held_written_as_zero_refused():
    assert R.fill_value("HELD", None) == ""
    with pytest.raises(R.Refused):
        R.fill_value("HELD", 0.0)
    with pytest.raises(R.Refused):
        R.fill_value("NOT_ESTABLISHED", 0)
    assert R.fill_value("BOUND", 0.0) == "0.000000"
