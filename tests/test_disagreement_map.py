"""An area delta is not an error rate until it is decomposed.

BED-01's vector geometry and its raster reference differ. A single
percentage cannot say whether the engine is wrong, the reference is wrong, or
the two are measuring different things — and the raster is a segmentation
output, not ground truth. So the disagreement is cut into pieces and each
piece is given a cause and a side to blame.

Nothing here corrects the vector geometry and nothing is tuned to make the
delta smaller.
"""

import pytest
from shapely.geometry import Polygon

from engine import disagreement_map as dm


def _rect(x0, y0, x1, y1):
    return Polygon([(x0, y0), (x1, y0), (x1, y1), (x0, y1)])


class _Solid:
    def __init__(self, geom):
        self.geometry = geom


class _Barrier:
    def __init__(self, i, ring):
        from engine.free_space import BARRIER_ACCEPTED
        self.portal_id, self.ring = i, ring
        self.status = BARRIER_ACCEPTED


def _ring(x0, y0, x1, y1):
    return ((x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0))


# --- the headline numbers -------------------------------------------------

def test_identical_shapes_agree_completely():
    g = _rect(0, 0, 4000, 3000)
    rep = dm.build("BED-01", g, g)
    assert rep.iou == pytest.approx(1.0)
    assert rep.pieces == []
    assert rep.area_delta_pct == pytest.approx(0.0)


def test_iou_is_reported_because_area_alone_can_agree_while_shape_is_wrong():
    # Two rectangles of the SAME area that barely overlap. An area
    # comparison would call this a perfect match.
    a = _rect(0, 0, 4000, 3000)
    b = _rect(3000, 0, 7000, 3000)
    rep = dm.build("X", a, b)
    assert rep.area_delta_pct == pytest.approx(0.0)
    assert rep.iou < 0.2


def test_a_missing_shape_is_not_agreement():
    rep = dm.build("X", None, _rect(0, 0, 100, 100))
    assert rep.notes["status"] == "NOT_COMPARABLE"
    assert "not agreement" in rep.notes["why"]
    assert rep.iou == 0.0


# --- the causes, A to G ---------------------------------------------------

def test_a_piece_inside_the_wall_solid_is_the_reference_s_basis():
    vec = _rect(0, 0, 4000, 3000)
    ras = _rect(0, 0, 4000, 3200)          # boundary sits in the wall
    solid = _Solid(_rect(0, 3000, 4000, 3200))
    rep = dm.build("X", vec, ras, solid=solid)
    p = rep.pieces[0]
    assert p.cause == dm.CAUSE_WALL_BASIS
    assert p.blame == "THE_REFERENCE"


def test_a_thin_strip_hugging_the_wall_is_the_same_basis_difference():
    # The earlier test asked only whether the piece lay INSIDE the solid, so
    # an 83 mm strip on the room side of the wall came out unexplained. It is
    # the same disagreement measured from the other side.
    vec = _rect(0, 0, 7000, 3000)
    ras = _rect(0, 0, 7000, 2917)
    solid = _Solid(_rect(0, 3000, 7000, 3200))
    rep = dm.build("X", vec, ras, solid=solid, max_wall_thickness_mm=440.0)
    p = rep.pieces[0]
    assert p.cause == dm.CAUSE_WALL_BASIS
    assert p.max_width_mm == pytest.approx(83.0, abs=2.0)


def test_a_strip_wider_than_any_wall_is_not_a_basis_difference():
    vec = _rect(0, 0, 7000, 3000)
    ras = _rect(0, 0, 7000, 2000)
    solid = _Solid(_rect(0, 3000, 7000, 3200))
    rep = dm.build("X", vec, ras, solid=solid, max_wall_thickness_mm=440.0)
    assert rep.pieces[0].cause != dm.CAUSE_WALL_BASIS


def test_a_doorway_sized_piece_on_a_barrier_is_a_threshold():
    vec = _rect(0, 0, 4000, 3000)
    ras = vec.union(_rect(1000, 3000, 1900, 3200))
    bars = [_Barrier("PT-1", _ring(1000, 3000, 1900, 3200))]
    rep = dm.build("X", vec, ras, solid=_Solid(_rect(9e6, 9e6, 9e6 + 1, 9e6 + 1)),
                   barriers=bars)
    p = rep.pieces[0]
    assert p.cause == dm.CAUSE_DOORWAY
    assert p.barrier_ids == ("PT-1",)


def test_a_big_lobe_that_merely_touches_a_barrier_is_not_a_threshold():
    # Ordering the barrier test first put 3.8 m2 of segmentation that had
    # grown out through a doorway into "threshold closed differently", which
    # reads as harmless. It is the reference claiming a corridor.
    vec = _rect(0, 0, 4000, 3000)
    lobe = _rect(1000, 3000, 3000, 5000)
    bars = [_Barrier("PT-1", _ring(1000, 2950, 1900, 3050))]
    rep = dm.build("X", vec, vec.union(lobe),
                   solid=_Solid(_rect(9e6, 9e6, 9e6 + 1, 9e6 + 1)),
                   barriers=bars)
    p = max(rep.pieces, key=lambda p: p.area_m2)
    assert p.cause == dm.CAUSE_RASTER_OVERREACH
    assert p.blame == "THE_REFERENCE"
    assert "through the doorway, not across a threshold" in p.why


def test_a_pixel_wide_sliver_is_the_raster_s_own_resolution():
    vec = _rect(0, 0, 4000, 3000)
    ras = _rect(0, 0, 4000, 2990)
    rep = dm.build("X", vec, ras)
    assert rep.pieces[0].cause == dm.CAUSE_QUANTISATION


def test_a_hole_carved_around_a_fixture_does_not_remove_floor():
    # A segmentation carves holes around fixtures, hatching and text. The
    # earlier test for this asked whether the piece touched the
    # intersection's BOUNDARY — which includes every hole ring — so it never
    # fired and 21 pieces came out unexplained.
    vec = _rect(0, 0, 4000, 3000)
    ras = vec.difference(_rect(1000, 1000, 1600, 1600))
    rep = dm.build("X", vec, ras)
    p = rep.pieces[0]
    assert p.cause == dm.CAUSE_FIXTURE
    assert p.blame == "THE_REFERENCE"
    assert "does not remove floor area" in p.why


def test_holes_are_counted_and_both_reference_areas_reported():
    vec = _rect(0, 0, 4000, 3000)
    ras = vec.difference(_rect(1000, 1000, 1600, 1600))
    got = dm.build("X", vec, ras).record()["notes"]["raster_reference_holes"]
    assert got["holes"] == 1
    assert got["hole_area_m2"] == pytest.approx(0.36)
    assert got["raster_area_with_holes_filled_m2"] == pytest.approx(12.0)
    assert "does not remove floor area" in got["why_it_matters"]


def test_a_vector_piece_inside_another_room_s_region_is_the_engine():
    # The only cause that blames the engine: the vector space reached past a
    # separator missing from the wall solid.
    vec = _rect(0, 0, 4000, 3000)
    ras = _rect(0, 0, 2000, 3000)
    other = _rect(2000, 0, 4000, 3000)
    rep = dm.build("BED-01", vec, ras, other_regions={"BTH-01": other})
    p = max(rep.pieces, key=lambda p: p.area_m2)
    assert p.cause == dm.CAUSE_VECTOR_LEAK
    assert p.blame == "THE_ENGINE"
    assert p.other_space_ids == ("BTH-01",)


def test_nothing_available_to_explain_a_piece_is_said_plainly():
    vec = _rect(0, 0, 4000, 3000).union(_rect(9000, 9000, 10000, 10000))
    rep = dm.build("X", vec, _rect(0, 0, 4000, 3000))
    p = rep.pieces[0]
    assert p.cause == dm.CAUSE_UNEXPLAINED
    assert p.blame == "NOT_ATTRIBUTED"
    assert "a guess here would become a correction" in p.why


# --- what the report refuses to do ---------------------------------------

def test_a_piece_below_one_square_centimetre_is_not_a_finding():
    vec = _rect(0, 0, 4000, 3000)
    ras = _rect(0, 0, 4000, 2999.9)
    assert dm.build("X", vec, ras).pieces == []


def test_the_report_says_the_raster_is_not_ground_truth():
    r = dm.build("X", _rect(0, 0, 10, 10), _rect(0, 0, 10, 10)).record()
    assert "raster_is_not_ground_truth" in r
    assert "segmentation output" in r["raster_is_not_ground_truth"]
    assert "not an error rate until it is decomposed" in r[
        "raster_is_not_ground_truth"]
    assert "nothing is adjusted to make the delta smaller" in r[
        "this_control_is_not_tuned"]


def test_reference_side_and_engine_side_causes_do_not_overlap():
    assert not (set(dm.REFERENCE_SIDE_CAUSES)
                & set(dm.ENGINE_SIDE_CAUSES))
    for c in dm.REFERENCE_SIDE_CAUSES + dm.ENGINE_SIDE_CAUSES:
        assert c in dm.CAUSES


# --- turning a label mask into a polygon ---------------------------------

def test_a_mask_becomes_a_polygon_in_vector_millimetres():
    import numpy as np
    mask = np.zeros((10, 10), dtype=bool)
    mask[2:5, 3:8] = True
    got = dm.polygon_from_mask(mask, px_mm=10.0, to_vector=lambda x, y: (x, y))
    assert got.area == pytest.approx(3 * 5 * 100.0)


def test_a_mask_polygon_respects_an_axis_swapping_transform():
    import numpy as np
    mask = np.zeros((10, 10), dtype=bool)
    mask[0:2, 0:6] = True
    got = dm.polygon_from_mask(mask, px_mm=10.0, to_vector=lambda x, y: (y, x))
    x0, y0, x1, y1 = got.bounds
    assert (x1 - x0) == pytest.approx(20.0)
    assert (y1 - y0) == pytest.approx(60.0)


def test_an_empty_mask_yields_no_polygon():
    import numpy as np
    assert dm.polygon_from_mask(np.zeros((5, 5), dtype=bool), px_mm=10.0,
                                to_vector=lambda x, y: (x, y)) is None
