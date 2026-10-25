"""T-287 G1 rule: the GF column base (= neck top = ground-beam top) of a column on a ground-beam line is the slab top of
the one building floor printed beside it (FFL - build-up); exterior ground beside it is not a building slab; two
different building floors beside it are the designer's (UNRESOLVED); nothing printed is MISSING. Never the higher,
lower or nearer level by preference.

Villa G hand cases (m): annex FFL +0.40, house FFL +1.10, court ground +0.20, build-up 0.05.
  normal: column between the annex (+0.40) and a court passage (+0.20)  -> base +0.35 (SETTLED)
  adverse: column between the annex (+0.40) and the house (+1.10)       -> UNRESOLVED, readings +0.35 / +1.05
  adverse: only the court passage printed beside it                    -> MISSING (no default to either slab)
  adverse: build-up not drawing-confirmed                             -> MISSING
"""

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
_s = importlib.util.spec_from_file_location("t287_search", ROOT / "research" / "agents_t287" / "t287_search.py")
S = importlib.util.module_from_spec(_s)
sys.modules.setdefault("t287_search", S)
_s.loader.exec_module(S)

COURT = (0.20,)


def test_one_building_floor_beside_the_column_settles_the_base():
    r = S.settle_column_base([("m1", 0.40, -0.4, -0.9), ("m2", 0.20, 0.8, -0.4)], COURT, 0.05)
    assert r["status"] == "SETTLED" and r["base"] == pytest.approx(0.35) and r["exterior"] == [0.2]


def test_two_building_floors_are_the_designers():
    r = S.settle_column_base([("m1", 0.40, -0.4, 0.0), ("m3", 1.10, 0.8, 0.0)], COURT, 0.05)
    assert r["status"] == "UNRESOLVED" and r["base"] is None and r["readings"] == [0.35, 1.05]


def test_exterior_only_or_no_build_up_is_missing():
    assert S.settle_column_base([("m2", 0.20, 0.8, 0.0)], COURT, 0.05)["status"] == "MISSING"
    assert S.settle_column_base([], COURT, 0.05)["base"] is None
    assert S.settle_column_base([("m1", 0.40, 0, 0)], COURT, None)["status"] == "MISSING"


def test_bay_reading_stops_at_the_next_beam_band():
    # column centre (0, 0) inside a band x -0.15 .. 0.15; a passage to x 1.35; the next band 1.35 .. 1.65; house beyond
    edges = [((-0.15, -5), (-0.15, 5)), ((0.15, -5), (0.15, 5)), ((1.35, -5), (1.35, 5)), ((1.65, -5), (1.65, 5))]
    marks = [("annex", 0.40, (-1.0, 0.5)), ("passage", 0.20, (0.8, 0.3)), ("house", 1.10, (2.6, 0.4)),
             ("far", 0.40, (-6.0, 0.0))]
    adj = S.adjoining_levels((0.0, 0.0), marks, edges, radius=3.5)
    assert [a[0] for a in adj] == ["annex", "passage"]
    assert S.settle_column_base(adj, COURT, 0.05)["base"] == pytest.approx(0.35)


def test_space_reading_takes_the_mark_of_the_open_room_only():
    # a kitchen bay with no mark is open to a lobby printing +0.40; a wall separates the house (+1.10)
    walls = [((1.35, -5.0), (1.35, 5.0)), ((-3.0, 0.0), (-1.2, 0.0))]          # house wall; a partial wall (W.C)
    marks = [("lobby", 0.40, (-0.4, -0.9)), ("house", 1.10, (2.5, 1.0))]
    got = S.same_space_levels([("SW", (-0.6, 1.0))], marks, walls, radius=5.0)
    assert got == [("lobby", 0.40, "SW")]
    shut = walls + [((-1.2, 0.0), (0.0, 0.0))]                                   # the opening closed: no reading
    assert S.same_space_levels([("SW", (-0.6, 1.0))], marks, shut, radius=5.0) == []


def test_crossings_counts_proper_intersections_only():
    assert S.crossings((0, 0), (2, 0), [((1, -1), (1, 1))]) == 1
    assert S.crossings((0, 0), (2, 0), [((3, -1), (3, 1))]) == 0
    assert S.crossings((0, 0), (2, 0), [((1, 0.5), (1, 1))]) == 0
