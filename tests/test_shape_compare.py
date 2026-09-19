"""E57 — two shapes can share an area without being the same shape."""

from __future__ import annotations

import pytest

from engine.shape_compare import (ShapeCompareError, boundary_deviation_mm,
                                  compare, intersection_area, summary)

CLEAR = "CLEAR_INTERNAL_FINISH_FACE"
CENTRE = "WALL_CENTRELINE_FACE"


def box(x0, y0, x1, y1):
    return ((x0, y0), (x1, y0), (x1, y1), (x0, y1))


def test_the_same_shape_scores_one():
    c = compare("BED-03", box(0, 0, 4000, 3000), box(0, 0, 4000, 3000),
                basis=CLEAR, reference_basis=CLEAR)
    assert c.iou == pytest.approx(1.0)
    assert c.area_variance_pct == pytest.approx(0.0)
    assert c.deviation["hausdorff_mm"] == pytest.approx(0.0)


def test_equal_area_in_the_wrong_place_is_caught_by_shape_and_not_by_area():
    """THE failure an area-only comparison cannot see. Both are 12 m2."""
    c = compare("X", box(0, 0, 4000, 3000), box(2000, 0, 6000, 3000),
                basis=CLEAR, reference_basis=CLEAR)
    assert c.area_variance_pct == pytest.approx(0.0)
    assert c.iou == pytest.approx(6.0 / 18.0, abs=1e-6)
    assert c.area_agrees_but_shape_does_not
    assert c.deviation["hausdorff_mm"] == pytest.approx(2000.0)


def test_equal_area_with_the_wrong_proportions_is_caught_too():
    """3 x 4 and 2 x 6 are both 12 m2 and are not the same room."""
    c = compare("Y", box(0, 0, 4000, 3000), box(0, 0, 6000, 2000),
                basis=CLEAR, reference_basis=CLEAR)
    assert c.area_variance_pct == pytest.approx(0.0)
    assert c.iou < 0.7
    assert c.area_agrees_but_shape_does_not


def test_perimeter_variance_catches_a_shape_that_area_does_not():
    c = compare("Y", box(0, 0, 4000, 3000), box(0, 0, 6000, 2000),
                basis=CLEAR, reference_basis=CLEAR,
                vector_perimeter_m=14.0, reference_perimeter_m=16.0)
    assert c.perimeter_variance_pct == pytest.approx(12.5, abs=0.01)


def test_comparing_across_bases_is_refused_rather_than_answered():
    """NEVER COMPARE UNLIKE BASES."""
    with pytest.raises(ShapeCompareError, match="NEVER COMPARE UNLIKE BASES"):
        compare("Z", box(0, 0, 4000, 3000), box(0, 0, 3800, 2800),
                basis=CENTRE, reference_basis=CLEAR)


def test_intersection_is_exact_on_rectilinear_shapes():
    got = intersection_area(box(0, 0, 4000, 4000), box(2000, 2000, 6000, 6000))
    assert got == pytest.approx(2000 * 2000)


def test_an_l_shape_intersects_exactly_too():
    ell = ((0, 0), (6000, 0), (6000, 2000), (3000, 2000), (3000, 5000),
           (0, 5000))
    assert intersection_area(ell, box(0, 0, 6000, 5000)) == pytest.approx(
        6000 * 2000 + 3000 * 3000)


def test_boundary_deviation_reports_both_directions():
    """One direction alone misses it. Every vertex of the shorter box lies ON
    the taller box's outline, so A->B is 0.0 while B->A is the real 200 mm."""
    d = boundary_deviation_mm(box(0, 0, 4000, 3000), box(0, 0, 4000, 3200))
    assert d["max_a_to_b_mm"] == pytest.approx(0.0)
    assert d["max_b_to_a_mm"] == pytest.approx(200.0)
    assert d["hausdorff_mm"] == pytest.approx(200.0)


def test_the_summary_names_the_worst_room_and_sets_no_threshold():
    cs = [compare("A", box(0, 0, 4000, 3000), box(0, 0, 4000, 3000),
                  basis=CLEAR, reference_basis=CLEAR),
          compare("B", box(0, 0, 4000, 3000), box(2000, 0, 6000, 3000),
                  basis=CLEAR, reference_basis=CLEAR)]
    out = summary(cs)
    assert out["worst_room"] == "B"
    assert out["acceptance_threshold"] is None
    assert out["rooms_where_area_agrees_but_shape_does_not"] == ["B"]


def test_no_rooms_compared_says_so_rather_than_returning_zeros():
    assert summary([])["rooms_compared"] == 0
