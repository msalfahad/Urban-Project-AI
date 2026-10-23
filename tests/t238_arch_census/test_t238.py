"""T-238: arched / banded openings read on their opening line (UP-OPEN-ARCH-001 v1.1 proposal) and the development
villa's census + delta of the merged opening ledgers.

Fixture villa T238-M (NOT Alsenan), hand truth:
  M1 arched window: width 1.20, springing 2.00, semicircular arch r 0.60 (crown 2.60); a 0.10 surround band outside it
     (band crown 2.70).
     masonry / plaster / paint deduction = 1.20 x 2.00 + pi x 0.60^2 / 2 = 2.400 + 0.5655 = 2.9655 m2
     window line (owner Q-32 A, enclosing rectangle on the opening line) = 1.20 x 2.60 = 3.120 m2
     reveal = 2 x 2.00 + pi x 0.60 + 1.20 = 4.000 + 1.8850 + 1.200 = 7.085 m (rectangle perimeter 7.600 refused)
     plastered height H = 2.30 (inside the arch): 2.400 + [y sqrt(r^2 - y^2) + r^2 asin(y / r)] at y = 0.30
       = 2.400 + 0.3 x 0.519615 + 0.36 x 0.523599 = 2.400 + 0.344381 = 2.744381 m2
  M2 plain window 1.00 x 1.50: rectangle (no arc) -> 1.500 m2 both trades
  M3 segmental arch drawn as one arc: chord 1.00, rise 0.30 -> r = (0.25 + 0.09) / 0.60 = 0.566667,
     theta = 2 asin(0.5 / r) = 2.161678 rad, sin theta = 0.830450, segment = r^2 / 2 (theta - sin theta) = 0.213736 m2
     (a numeric strip integration of the same circle gives 0.213736), arc = r theta = 1.224951 m
  M4 window curved on plan, developed width 3.00, opening crown 2.40 .. 2.45, archivolt crown 2.90: finish deduction HELD,
     upper bound 3.00 x 2.45 = 7.350; the archivolt 3.00 x 2.90 = 8.700 is never the window
Adverse: band crown as head, width x crown for masonry, chord only, jamb rectangle only, a profile point outside the jambs
(band line), a rectangle perimeter as reveal, a held outline deducted, a cap inside the arch without its profile.
"""
from __future__ import annotations

import csv
import json
import math
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research" / "agents_t238"
sys.path.insert(0, str(HERE))

import arch_rules as R  # noqa: E402

R06 = 0.60


def semicircle_profile(width=1.20, spring=2.00, n=720):
    r = width / 2
    return [(r - r * math.cos(math.pi * i / n), spring + r * math.sin(math.pi * i / n)) for i in range(n + 1)]


def m1(band=0.10):
    seg, length, crown = R.profile_segment(1.20, 2.00, semicircle_profile())
    return R.arched_outline("M1", 1.20, 2.00, crown, seg, length, band_m=band)


# ------------------------------------------------------------------------------------------------ normal cases
def test_m1_outline_window_and_reveal_by_hand():
    o = m1()
    assert o["crown_m"] == pytest.approx(2.60, abs=1e-6)
    assert o["arch_segment_m2"] == pytest.approx(math.pi * R06 ** 2 / 2, abs=2e-4)          # 0.5655
    assert o["masonry_deduction_m2"] == pytest.approx(2.9655, abs=2e-4)
    assert o["finish_deduction_m2"] == o["masonry_deduction_m2"]
    assert o["window_area_q32a_m2"] == pytest.approx(3.120, abs=1e-6)
    assert o["reveal_lm"] == pytest.approx(7.085, abs=1e-3)
    assert o["band_crown_m"] == pytest.approx(2.70, abs=1e-9)
    assert R.check_masonry_deduction(2.9655, o)
    assert R.check_window_area(3.120, o)
    assert R.check_reveal(7.085, o)


def test_m2_plain_window_is_a_rectangle_in_both_trades():
    assert R.census_code("rectangular", arc_drawn=False) == "RECT_ON_OPENING_LINE"
    assert 1.00 * 1.50 == pytest.approx(1.500)


def test_m3_segmental_arc_by_hand():
    seg, arc, r = R.circular_segment(1.00, 0.30)
    assert r == pytest.approx(0.566667, abs=1e-6)
    assert seg == pytest.approx(0.213736, abs=1e-6)
    assert arc == pytest.approx(1.224951, abs=1e-6)
    o = R.arched_outline("M3", 1.00, 2.20, 2.50, seg, arc, status=R.SS, sill_edge=False)
    assert o["masonry_deduction_m2"] == pytest.approx(2.2 + 0.2137, abs=1e-4)
    assert o["window_area_q32a_m2"] == pytest.approx(2.50)
    assert R.check_masonry_deduction(2.4137, o)           # a source-supported outline may be carried as a candidate


def test_height_cap_clipping_by_hand():
    prof = semicircle_profile()
    o = m1()
    assert R.clipped_finish_deduction(o, 3.00)["m2"] == o["finish_deduction_m2"]     # cap above the crown
    assert R.clipped_finish_deduction(o, 1.80)["m2"] == pytest.approx(1.20 * 1.80)   # cap below the springing
    c = R.clipped_finish_deduction(o, 2.30, prof)
    assert c["m2"] == pytest.approx(2.744381, abs=2e-4)


def test_m4_curved_on_plan_is_held_with_its_bound():
    b = R.curved_plan_bound("M4", 3.00, 2.40, 2.45)
    assert b["status"] == R.HELD
    assert b["finish_deduction_upper_m2"] == pytest.approx(7.350)
    assert b["window_q32a_range_m2"] == (pytest.approx(7.20), pytest.approx(7.35))
    assert 3.00 * 2.90 not in b["window_q32a_range_m2"]
    assert R.census_code("arched", True, curved_on_plan=True) == "CURVED_ON_PLAN"


def test_dimension_target_tells_opening_from_band():
    assert R.dimension_target(2.60, 2.60, (2.70,)) == "OPENING"
    assert R.dimension_target(2.70, 2.60, (2.70,)) == "BAND"
    assert R.dimension_target(2.85, 2.60, (2.70,)) == "UNBOUND"


# ------------------------------------------------------------------------------------------------ adverse cases
def test_band_crown_taken_as_head_is_refused_in_both_trades():
    o = m1()
    with pytest.raises(ValueError, match="BAND_CROWN_AS_HEAD"):
        R.check_masonry_deduction(1.20 * 2.70, o)
    with pytest.raises(ValueError, match="BAND_CROWN_AS_HEAD"):
        R.check_window_area(1.20 * 2.70, o)


def test_width_times_crown_for_masonry_is_refused():
    with pytest.raises(ValueError, match="RECTANGLE_FOR_MASONRY"):
        R.check_masonry_deduction(1.20 * 2.60, m1())


def test_chord_only_and_jamb_rectangle_only_are_refused():
    with pytest.raises(ValueError, match="ARCH_AS_CHORD"):
        R.profile_segment(1.20, 2.00, [(0.0, 2.0), (1.2, 2.0)])
    with pytest.raises(ValueError, match="ARCH_DROPPED"):
        R.check_masonry_deduction(2.400, m1())


def test_a_band_line_is_not_the_opening_line():
    band = [(x * 1.4 / 1.2 - 0.1, y) for x, y in semicircle_profile()]           # the outer chain, 1.40 wide
    with pytest.raises(ValueError, match="ARCH_NOT_ON_OPENING_LINE"):
        R.profile_segment(1.20, 2.00, band)
    stray = semicircle_profile()
    stray[100] = (-0.05, stray[100][1])
    with pytest.raises(ValueError, match="ARCH_OUTSIDE_JAMBS"):
        R.profile_segment(1.20, 2.00, stray)


def test_rectangle_perimeter_as_reveal_is_refused():
    with pytest.raises(ValueError, match="RECTANGLE_PERIMETER"):
        R.check_reveal(2 * 2.60 + 2 * 1.20, m1())


def test_held_outline_is_never_a_deduction_and_never_zero():
    h = R.arched_outline("H", 1.20, None, None, None, None)
    assert h["status"] == R.HELD and "masonry_deduction_m2" not in h
    with pytest.raises(ValueError, match="OPENING_HELD"):
        R.check_masonry_deduction(0.0, h)
    assert R.clipped_finish_deduction(h, 3.0)["m2"] is None
    row = R.delta_row("L", "H", "x", "y", "m2", 2.0, None, R.HELD, "c")
    assert row["new"] == "HELD" and row["change"] == "to HELD"


def test_cap_inside_the_arch_without_profile_is_held():
    c = R.clipped_finish_deduction(m1(), 2.30)
    assert c["status"] == R.HELD and c["m2"] is None


def test_impossible_segments_are_refused():
    with pytest.raises(ValueError, match="ARCH_SEGMENT_IMPOSSIBLE"):
        R.arched_outline("X", 1.0, 2.0, 2.3, 0.40, 1.3)                                 # > width x rise
    with pytest.raises(ValueError, match="SEGMENT_IMPOSSIBLE"):
        R.circular_segment(1.0, 0.6)


# ------------------------------------------------------------------------------------------------ development villa
def _rows(name):
    with open(HERE / name, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def test_alsenan_outputs_reproduce():
    p = subprocess.run([sys.executable, "-I", str(HERE / "alsenan_t238.py"), "--check"], capture_output=True,
                       text=True, cwd=ROOT)
    assert p.returncode == 0, p.stdout + p.stderr
    assert "CHECK PASS" in p.stdout


def test_alsenan_census_covers_every_opening_and_names_the_defects():
    census = {r["ID"]: r for r in _rows("CENSUS_T238.csv")}
    t198 = [r["ID"] for r in _rows("../agents_t198/OPENINGS_T198.csv")]
    assert set(t198) <= set(census) and len(t198) == 68
    assert census["W15"]["CODE"] == census["W16"]["CODE"] == "BAND_CROWN_READ_AS_HEAD"
    assert census["W26"]["CODE"] == "ARCH_READ_AS_RECTANGLE"
    assert census["W17"]["CODE"] == "CURVED_ON_PLAN" and census["W17"]["STATUS"] == R.HELD
    assert census["A-GF-01"]["CODE"] == "ARCH_DRAWN_NOT_DIMENSIONED"
    assert census["A-1F-01"]["CODE"] == "NOT_DRAWN"
    assert census["F-BB-GF-ARCH"]["STATUS"] == R.UNKNOWN


def test_alsenan_outlines_and_window_effect():
    s = json.loads((HERE / "summary.json").read_text(encoding="utf-8"))
    o = s["outlines"]
    assert o["W15"]["masonry_deduction_m2"] == pytest.approx(4.3629, abs=5e-4)       # T-227 / Checker 4.3629
    assert o["W15"]["window_area_q32a_m2"] == pytest.approx(4.650)
    assert o["W26"]["masonry_deduction_m2"] == pytest.approx(1.875, abs=5e-4)
    assert o["W26"]["window_area_q32a_m2"] == pytest.approx(2.040)
    assert o["A-GF-01"]["status"] == R.SS
    w = s["windows"]
    assert w["windows_T150_established_8_before_m2"] == pytest.approx(56.771)
    assert w["windows_same_7_after_m2 (W17 to HELD)"] == pytest.approx(45.101)
    assert w["engine_vs_freelancer_7"][0] == pytest.approx(-0.380)
    assert s["W17"]["window_HELD_m2"] == [9.87, 11.515]


def test_alsenan_delta_never_zero_for_held_and_merged_ledgers_untouched():
    d = _rows("DELTA_T238.csv")
    for r in d:
        if r["new_status"] == R.HELD:
            assert r["new"].startswith("HELD") or r["item"].startswith("head edge"), r
        assert r["new"] not in ("0", "0.000") or r["item"].startswith("head edge"), r
    w17 = [r for r in d if r["opening"] == "W17" and r["line"] == "WINDOW.ALUMINIUM"][0]
    assert w17["old"] == "11.515" and w17["new"] == "HELD"
    t150 = {r["ID"]: r for r in _rows("../agents_t150/OPENINGS_T150.csv")}
    assert t150["W15"]["HEIGHT_M"] == "3.10" and t150["W17"]["HEIGHT_M"] == "3.50"          # merged file unchanged
