"""T-598 R-T598-1..3 on a non-Alsenan hand fixture (Villa K598) with normal and adverse cases.

Villa K598 (invented, hand-calculated): straight lane 1.000 wide, goings 0.280; a 3-winder quarter turn in a 1.000 x
1.100 turn region whose plan subdivision is NOT drawn; a closing riser drawn on two drawings; a floor edge not drawn
whose 12th riser the section gives, lane bounds drawn over s 0 .. 4.0 and 0 .. 4.2, open position range 3.5 .. 3.7;
a curtail first step: front arc r 0.300, sweep 180 deg.
"""
from __future__ import annotations

import importlib
import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t598"))
E = importlib.import_module("edge_classes")


def floor_edge(**kw):
    e = {"id": "K598-FLOOR", "count_source": "SECTION_OWNER_RULE", "length_basis": "LANE_INVARIANT",
         "lane_bounds": [(0.0, 4.0), (0.0, 4.2)], "position_range": (3.5, 3.7), "length_m": 1.000}
    e.update(kw)
    return e


# ------------------------------------------------------------------ normal
def test_floor_edge_value_when_lane_covers_the_open_position():
    c = E.classify(floor_edge(position_conflict="beam clash: position only"))
    assert c["cls"] == "VALUE" and c["lm"] == 1.000 and c["status"] == "DRAWING-CONFIRMED"
    assert c["bound"] is None and "position only" in c["why"]


def test_closing_riser_drawn_on_two_drawings_is_value():
    c = E.classify({"id": "K598-TR", "count_source": "SECTION_OWNER_RULE", "length_basis": "DRAWN_EDGE",
                    "length_m": 1.000})
    assert c["cls"] == "VALUE" and c["lm"] == 1.000


def test_winder_subdivision_not_drawn_is_designer_item_with_first_principles_bound():
    # hand: each front crosses the 1.000 lane (>= 1.000) and fits in 1.000 x 1.100 (<= hypot = 1.486607)
    longest = math.hypot(1.000, 1.100)
    c = E.classify({"id": "K598-W", "count_source": "SECTION_OWNER_RULE", "length_basis": "NOT_DRAWN",
                    "region": {"n_fronts": 3, "lane_m": 1.000, "longest_m": longest}})
    assert c["cls"] == "DESIGNER_ITEM" and c["lm"] is None and c["status"] == "HELD"
    assert c["bound"] == (3.000, pytest.approx(4.459821, abs=1e-6))


def test_reconstructed_count_is_owner_approved_not_drawing_confirmed():
    c = E.classify({"id": "K598-RC", "count_source": "PLAN_RECONSTRUCTION_OWNER_APPROVED",
                    "length_basis": "DRAWN_EDGE", "length_m": 1.000})
    assert c["status"] == "ASSUMED - OWNER-APPROVED"


def test_curtail_on_the_developed_arc_not_the_chord():
    # hand: pi x 0.300 = 0.942478; chord 0.600
    assert E.arc_length(0.300, 270.0, 90.0) == pytest.approx(0.942478, abs=1e-6)
    assert E.chord(0.300, 270.0, 90.0) == pytest.approx(0.600, abs=1e-9)
    assert E.arc_length(0.300, 270.0, 90.0) != pytest.approx(E.chord(0.300, 270.0, 90.0))


def test_arc_rotation_and_mirror_invariance():
    a = E.arc_length(0.300, 270.0, 90.0)
    assert E.arc_length(0.300, 270.0 + 37.0, 90.0 + 37.0) == pytest.approx(a)       # rotation
    assert E.arc_length(0.300, 360.0 - 90.0, 360.0 - 270.0 + 360.0) == pytest.approx(a)   # mirror (sweep kept)


def test_units_mm_and_m():
    assert E.to_m(1000.0, "mm") == 1.0 and E.to_m(1.0, "m") == 1.0


def test_reconciliation_closes_exactly():
    # his 10 x 1.050 = 10.500; ours 9 valued at 1.000 + 1 held: causes HELD 1.050 + WIDTH 9 x 0.050 = 0.450
    assert E.residual({"rows": [(10, 1.050)]}, [("HELD", 1.050), ("WIDTH", 0.450)], 9.000) == pytest.approx(0.0, abs=1e-9)


# ------------------------------------------------------------------ adverse
def test_winder_count_conflict_stays_conflict_with_bound():
    c = E.classify({"id": "K598-WC", "count_source": "SECTION_OWNER_RULE", "length_basis": "TWO_READINGS",
                    "readings_m": [1.414214, 1.200]})
    assert c["cls"] == "DRAWING_CONFLICT" and c["lm"] is None and c["status"] == "HELD"
    assert c["bound"] == (1.200, 1.414214)


def test_held_edge_as_zero_or_none_refused():
    with pytest.raises(E.RuleError):
        E.classify(floor_edge(length_m=None))
    with pytest.raises(E.RuleError):
        E.classify(floor_edge(length_m=0.0))
    with pytest.raises(E.RuleError):
        E.arc_length(None, 0.0, 90.0)


def test_generated_winder_refused():
    with pytest.raises(E.RuleError):
        E.classify({"id": "K598-G", "count_source": "SECTION_OWNER_RULE", "length_basis": "DRAWN_EDGE",
                    "length_m": 1.2, "generated": True})


def test_lane_bound_not_covering_the_position_refused():
    with pytest.raises(E.RuleError):
        E.classify(floor_edge(lane_bounds=[(0.0, 3.6), (0.0, 4.2)]))


def test_no_governing_count_is_designer_item_never_a_value():
    c = E.classify({"id": "K598-N", "count_source": "NONE", "length_basis": "DRAWN_EDGE", "length_m": 1.0})
    assert c["cls"] == "DESIGNER_ITEM" and c["lm"] is None


def test_equal_readings_are_not_a_conflict_and_missing_reading_refused():
    with pytest.raises(E.RuleError):
        E.classify({"id": "x", "count_source": "SECTION_OWNER_RULE", "length_basis": "TWO_READINGS",
                    "readings_m": [1.2, 1.2]})
    with pytest.raises(E.RuleError):
        E.classify({"id": "x", "count_source": "SECTION_OWNER_RULE", "length_basis": "TWO_READINGS",
                    "readings_m": [1.2, None]})


def test_designer_item_without_region_refused_and_bad_region_refused():
    with pytest.raises(E.RuleError):
        E.classify({"id": "x", "count_source": "SECTION_OWNER_RULE", "length_basis": "NOT_DRAWN"})
    with pytest.raises(E.RuleError):
        E.classify({"id": "x", "count_source": "SECTION_OWNER_RULE", "length_basis": "NOT_DRAWN",
                    "region": {"n_fronts": 3, "lane_m": 1.0, "longest_m": 0.9}})


def test_cm_unit_and_unknown_sources_refused():
    with pytest.raises(E.RuleError):
        E.to_m(115.0, "cm")
    with pytest.raises(E.RuleError):
        E.classify(floor_edge(count_source="BEST_FIT"))
    with pytest.raises(E.RuleError):
        E.classify(floor_edge(length_basis="CHORD"))


def test_zero_sweep_and_bad_radius_refused():
    with pytest.raises(E.RuleError):
        E.arc_length(0.3, 90.0, 90.0)
    with pytest.raises(E.RuleError):
        E.arc_length(-0.3, 0.0, 90.0)
