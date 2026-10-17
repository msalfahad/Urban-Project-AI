"""Synthetic tests of engine/source/structural_completeness.py (no project data)."""

from __future__ import annotations

import math

import pytest

from engine.source import structural_completeness as SCQ


def test_point_in_polygon_and_overlap_with_holes_and_concave_faces():
    sq = [(0, 0), (1000, 0), (1000, 1000), (0, 1000)]
    assert SCQ.point_in_polygon(500, 500, sq) and not SCQ.point_in_polygon(1500, 500, sq)
    assert SCQ.rect_polygon_overlap((0, 0, 1000, 1000), sq) == pytest.approx(1e6)
    assert SCQ.rect_polygon_overlap((500, 500, 1500, 1500), sq) == pytest.approx(2.5e5)
    hole = [(200, 200), (400, 200), (400, 400), (200, 400)]
    assert SCQ.rect_polygon_overlap((0, 0, 1000, 1000), sq, [hole]) == pytest.approx(1e6 - 4e4)
    ell = [(0, 0), (1000, 0), (1000, 200), (200, 200), (200, 1000), (0, 1000)]       # concave L
    assert SCQ.rect_polygon_overlap((400, 400, 900, 900), ell) == 0.0                 # in the notch
    assert SCQ.rect_polygon_overlap((0, 0, 200, 1000), ell) == pytest.approx(2e5)
    assert SCQ.rect_polygon_overlap((2000, 0, 3000, 100), sq) == 0.0
    with pytest.raises(SCQ.CompletenessError):
        SCQ.rect_polygon_overlap((0, 0, 1, 1), sq, step=0)


def test_edge_on_lines_unions_collinear_pieces_within_tolerance():
    p, q = (0, 0), (1000, 0)
    ok, cov = SCQ.edge_on_lines(p, q, [((0, 1), (600, 1)), ((500, -1), (1000, -1))])
    assert ok and cov == pytest.approx(1.0)
    ok, cov = SCQ.edge_on_lines(p, q, [((0, 0), (500, 0))])
    assert not ok and cov == pytest.approx(0.5)
    ok, _ = SCQ.edge_on_lines(p, q, [((0, 5), (1000, 5))], tol=2.0)                     # parallel, 5 mm off
    assert not ok
    with pytest.raises(SCQ.CompletenessError):
        SCQ.edge_on_lines(p, p, [])


def test_hatch_spacing_folds_a_doubled_gap_and_nearest_reference_refuses_ties():
    r = SCQ.hatch_spacing([0, 100, 200, 400, 500])                                      # one line lost at 300
    assert r["spacing"] == pytest.approx(100) and r["lines"] == 5 and r["max"] == pytest.approx(100)
    assert SCQ.hatch_spacing([5.0]) is None
    refs = {"A": 100.0, "B": 250.0}
    assert SCQ.nearest_reference(103.0, refs)[0] == "A"
    assert SCQ.nearest_reference(180.0, refs)[0] is None                                 # beyond 6 % of both
    assert SCQ.nearest_reference(150.0, {"A": 100.0, "B": 200.0}, max_rel=1.0)[0] == "B"     # relative distance
    assert SCQ.nearest_reference(150.0, {"A": 100.0, "B": 300.0}, max_rel=1.0)[0] is None    # 50 % from both: a tie
    assert SCQ.nearest_reference(None, refs) == (None, {})


def test_beam_readings_differ_by_the_strip_and_a_missing_dimension_is_never_zero():
    v = SCQ.beam_convention_volumes(0.2, 0.4, 1.62, 0.16)
    assert v["TOTAL_DEPTH"] == pytest.approx(0.2 * 0.4 * 1.62)
    assert v["BELOW_SLAB"] == pytest.approx(0.2 * 0.56 * 1.62)
    assert v["BELOW_SLAB"] - v["TOTAL_DEPTH"] == pytest.approx(v["STRIP"]) == pytest.approx(0.2 * 0.16 * 1.62)
    assert v["TOTAL_DEPTH"] == pytest.approx(v["DOWNSTAND_TOTAL_DEPTH"] + v["STRIP"])
    for bad in ((None, 0.4, 1, 0.16), (0.2, None, 1, 0.16), (0.2, 0.4, None, 0.16), (0.2, 0.4, 1, None)):
        with pytest.raises(SCQ.CompletenessError, match="missing"):
            SCQ.beam_convention_volumes(*bad)
    with pytest.raises(SCQ.CompletenessError):
        SCQ.beam_convention_volumes(0.2, 0.16, 1, 0.16)                                # slab not below H
    with pytest.raises(SCQ.CompletenessError):
        SCQ.beam_convention_volumes(-0.2, 0.4, 1, 0.16)


def test_length_class_bounds_are_exclusive_bands():
    b = (2.5, 5.0)
    assert [SCQ.length_class(x, b) for x in (0.4, 2.49, 2.5, 4.99, 5.0, 9.9)] == [0, 0, 1, 1, 2, 2]
    with pytest.raises(SCQ.CompletenessError):
        SCQ.length_class(None, b)
    with pytest.raises(SCQ.CompletenessError):
        SCQ.length_class(1.0, (5.0, 2.5))
    assert math.isclose(SCQ.TOL, 1e-9)
