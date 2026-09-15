"""A leak map must answer WHERE free space crossed and WHAT is drawn there.

The failures these tests lock down are the ones that made an earlier leak map
report 27 of 30 separations as NO_VECTOR_SEPARATOR on a drawing whose walls
are largely present: probing a metres-long frontier at one point, reading the
frontier's axis in raster space when the frame transform swaps the axes, and
classifying a separation from a bounding box instead of from the stretch that
is actually open.
"""

import pytest

from engine import leak_map as lm


# --- intervals: coverage is a union, and a gap is a gap -------------------

def test_coverage_is_a_union_not_a_sum():
    # Two bands that overlap cover their union once, not twice.
    assert lm._measure(lm._union([(0.0, 100.0), (50.0, 150.0)])) == 150.0


def test_a_span_outside_the_frontier_earns_no_coverage():
    assert lm._clip([(500.0, 900.0)], 0.0, 100.0) == []


def test_gaps_are_what_the_spans_leave_open():
    got = lm._gaps(lm._union([(10.0, 20.0), (30.0, 40.0)]), 0.0, 50.0)
    assert got == [(0.0, 10.0), (20.0, 30.0), (40.0, 50.0)]


def test_subtract_works_run_by_run():
    # A frontier in two runs, with material covering part of the first.
    got = lm._subtract([(0.0, 100.0), (200.0, 300.0)], [(0.0, 60.0)])
    assert got == [(60.0, 100.0), (200.0, 300.0)]


# --- the frame may swap the axes -----------------------------------------

def test_the_along_axis_is_measured_from_the_transform_not_assumed():
    # AR-00's frame is SWAP_FLIP_Y: vector x follows PIXEL Y. Reading the
    # frontier's axis off the raster spread transposes every frontier, and a
    # transposed frontier looks for walls along the line it divides.
    assert lm._axis_map(lambda x, y: (y, x)) == "y"
    assert lm._axis_map(lambda x, y: (x, y)) == "x"


# --- classification happens at the aperture, not at the midpoint ----------

class _Band:
    def __init__(self, i, axis, centre, a, b):
        self.wall_band_id, self.axis = i, axis
        self.centreline_mm, self.start_mm, self.end_mm = centre, a, b


class _Stroke:
    def __init__(self, i, axis, fixed, a, b, cls):
        self.stroke_id, self.axis, self.fixed_mm = i, axis, fixed
        self.start_mm, self.end_mm, self.stroke_class = a, b, cls


class _Portal:
    def __init__(self, i, axis, fixed, a, b):
        self.portal_id, self.axis, self.fixed_mm = i, axis, fixed
        self.start_mm, self.end_mm = a, b


def _frontier(**kw):
    base = {"space_a": "A", "space_b": "B", "axis": "H",
            "centre_mm": (0.0, 0.0), "fixed_mm": 1000.0,
            "window_mm": (900.0, 1100.0), "window_is_measured": True,
            "support_mm": [(0.0, 6000.0)], "along_mm": (0.0, 6000.0),
            "length_mm": 6000.0}
    base.update(kw)
    return base


def _leak(fr, bands=(), strokes=(), portals=(),
          localiser=lm.LOCALISER_FRONTIER):
    return lm._leak_at(fr, localiser, "LK-0001", "SG-0001", 2, set(),
                       list(bands), list(strokes), list(portals))


def test_a_wall_on_part_of_a_long_frontier_is_not_a_missing_separator():
    # The defect this replaces: a 6 m frontier was probed at its midpoint, so
    # a wall running along its first four metres was invisible and the
    # frontier was reported as having no separator at all.
    lk = _leak(_frontier(),
               bands=[_Band("WB-1", "H", 1000.0, 0.0, 4000.0)])
    assert lk.cause == lm.UNRESOLVED_PORTAL or lk.cause != lm.VALID_WALL_BAND_PRESENT
    assert lk.bands_at_frontier == ("WB-1",)
    assert lk.band_coverage_mm == pytest.approx(4000.0)
    # And the aperture is the stretch the wall does NOT cover.
    assert lk.aperture_mm == pytest.approx((4000.0, 6000.0))


def test_the_cause_is_read_at_the_aperture_not_anywhere_on_the_frontier():
    # A single-line wall lying under the part that is ALREADY walled cannot
    # explain a leak: free space did not cross there.
    lk = _leak(_frontier(),
               bands=[_Band("WB-1", "H", 1000.0, 0.0, 4000.0)],
               strokes=[_Stroke("VS-1", "H", 1000.0, 100.0, 900.0,
                                "CONFIRMED_SINGLE_LINE_WALL")])
    assert lk.cause == lm.NO_VECTOR_SEPARATOR
    assert lk.strokes_at_aperture == ()
    # The stroke is still reported as being on the frontier: it is real.
    assert lk.unpaired_strokes_at_frontier == ("VS-1",)


def test_a_stroke_in_the_aperture_does_explain_the_leak():
    lk = _leak(_frontier(),
               bands=[_Band("WB-1", "H", 1000.0, 0.0, 4000.0)],
               strokes=[_Stroke("VS-1", "H", 1000.0, 4200.0, 5800.0,
                                "CONFIRMED_SINGLE_LINE_WALL")])
    assert lk.cause == lm.SINGLE_LINE_WALL_CANDIDATE
    assert lk.strokes_at_aperture == ("VS-1",)


def test_a_fully_walled_frontier_is_not_a_repair():
    lk = _leak(_frontier(),
               bands=[_Band("WB-1", "H", 1000.0, 0.0, 6000.0)])
    assert lk.cause == lm.VALID_WALL_BAND_PRESENT
    assert not lk.is_an_open_aperture
    assert lk.aperture_mm is None


def test_a_frontier_with_nothing_anywhere_says_so_differently():
    lk = _leak(_frontier())
    assert lk.cause == lm.NO_VECTOR_SEPARATOR
    assert "anywhere along it" in lk.why


def test_a_mark_outside_the_measured_window_is_not_at_this_frontier():
    # The window is measured from the gap between the two spaces. A band a
    # metre away belongs to another room.
    lk = _leak(_frontier(),
               bands=[_Band("WB-far", "H", 3000.0, 0.0, 6000.0)])
    assert lk.bands_at_frontier == ()


def test_coverage_is_measured_over_the_facing_support_only():
    # Two spaces facing each other in two stretches with a gap between: a
    # band running through the gap earns coverage only where they face.
    fr = _frontier(support_mm=[(0.0, 1000.0), (5000.0, 6000.0)],
                   length_mm=2000.0)
    lk = _leak(fr, bands=[_Band("WB-1", "H", 1000.0, 0.0, 6000.0)])
    assert lk.band_coverage_mm == pytest.approx(2000.0)
    assert lk.frontier_runs == 2


# --- necks: the passage the merged polygon itself reveals -----------------

def _rect(x0, y0, x1, y1):
    from shapely.geometry import Polygon
    return Polygon([(x0, y0), (x1, y0), (x1, y1), (x0, y1)])


def _two_rooms_joined_by(gap_mm):
    """Two 4x4 m rooms side by side, joined by one gap in the wall."""
    from shapely.ops import unary_union
    a = _rect(0, 0, 4000, 4000)
    b = _rect(4200, 0, 8200, 4000)
    mid = 2000.0
    link = _rect(4000, mid - gap_mm / 2.0, 4200, mid + gap_mm / 2.0)
    return unary_union([a, b, link])


def test_a_neck_measures_the_passage_that_merged_two_spaces():
    geom = _two_rooms_joined_by(800.0)
    found, diag = lm.necks(geom, {"A": (2000, 2000), "B": (6200, 2000)})
    assert len(found) == 1
    # The passage is 800 mm wide, so the two halves part at half that.
    assert found[0]["passage_width_mm"] == pytest.approx(800.0, abs=60.0)
    assert found[0]["channel_located"]
    assert not diag["frozen_at_mm"]


def test_a_hairline_gap_is_found_at_its_own_width():
    found, _ = lm.necks(_two_rooms_joined_by(50.0),
                        {"A": (2000, 2000), "B": (6200, 2000)})
    assert found and found[0]["passage_width_mm"] == pytest.approx(50.0,
                                                                   abs=60.0)


def test_necks_report_one_record_per_split_not_per_label_pair():
    # Three rooms in a row joined by two openings: two passages, not three
    # pair facts.
    from shapely.ops import unary_union
    geom = unary_union([
        _two_rooms_joined_by(800.0),
        _rect(8400, 0, 12400, 4000),
        _rect(8200, 1800, 8400, 2200)])
    found, _ = lm.necks(geom, {"A": (2000, 2000), "B": (6200, 2000),
                               "C": (10400, 2000)})
    assert len(found) == 2


def test_a_seed_in_a_wall_is_moved_into_the_free_space():
    # An L-shaped space has its centroid outside itself. Snapping such a seed
    # to the boundary puts it where the first erosion step removes it, the
    # label drops out of the partition, and its passage is never reported.
    from shapely.geometry import Polygon
    ell = Polygon([(0, 0), (6000, 0), (6000, 2000), (2000, 2000),
                   (2000, 6000), (0, 6000)])
    seeds, depth = lm._interior_seeds(ell, {"L": (4000, 4000)},
                                      step_mm=25.0)
    assert ell.covers(seeds["L"])
    assert depth["L"] >= lm.SEED_MIN_DEPTH_MM


def test_a_passage_with_no_bounded_extent_is_refused_not_classified():
    # Reading the drawing over an unbounded extent returns every band on the
    # sheet, which would look like a confident answer and be worthless. The
    # measured WIDTH survives; the classification does not.
    fr = _frontier(channel_located=True, extent_established=False,
                   passage_width_mm=1250.0,
                   labels_a=("A",), labels_b=("B", "C"))
    lk = _leak(fr, bands=[_Band("WB-1", "H", 1000.0, 0.0, 6000.0)],
               localiser=lm.LOCALISER_NECK)
    assert lk.cause == lm.LEAK_UNRESOLVED
    assert lk.bands_at_frontier == ()
    assert lk.passage_width_mm == 1250.0
    assert lk.channel_located and not lk.extent_established


def test_a_located_passage_with_walls_along_all_of_it_is_a_junction_gap():
    # The walls ARE drawn and ARE in the solid, and free space crossed
    # anyway. Nothing is missing from the source; the repair is in the
    # extractor, and calling it a missing separator would send the work to
    # the wrong place.
    fr = _frontier(channel_located=True, extent_established=True,
                   passage_width_mm=50.0,
                   support_mm=[(0.0, 200.0)], along_mm=(0.0, 200.0),
                   length_mm=200.0)
    lk = _leak(fr, bands=[_Band("WB-1", "H", 1000.0, 0.0, 200.0)],
               localiser=lm.LOCALISER_NECK)
    assert lk.hairline_junction_gap
    assert lk.repair_is_in_the_extractor
    assert "fail to meet" in lk.why


# --- the map must know when it is incomplete ------------------------------

def test_a_partition_that_does_not_account_for_every_label_says_so():
    # A component holding N labels was merged through at least N-1 passages.
    # Reporting fewer and presenting them as the explanation is the failure
    # this check exists to catch.
    found = [{"labels_a": ("A",), "labels_b": ("B", "C", "D")}]
    got = lm._partition_check(("A", "B", "C", "D"), found)
    assert got["passages_needed_at_least"] == 3
    assert got["passages_reported"] == 1
    assert not got["complete"]


def test_a_label_no_passage_ever_separated_is_named():
    got = lm._partition_check(("A", "B", "C"),
                              [{"labels_a": ("A",), "labels_b": ("B",)}])
    assert got["labels_never_separated"] == ["C"]
    assert not got["complete"]


def test_a_complete_partition_is_reported_as_complete():
    found = [{"labels_a": ("A",), "labels_b": ("B", "C")},
             {"labels_a": ("B",), "labels_b": ("C",)}]
    assert lm._partition_check(("A", "B", "C"), found)["complete"]


# --- ranking --------------------------------------------------------------

def test_an_already_walled_separation_never_outranks_an_open_one():
    walled = _leak(_frontier(),
                   bands=[_Band("WB-1", "H", 1000.0, 0.0, 6000.0)])
    opened = _leak(_frontier())
    s = lm.summary([walled, opened])
    assert s["top_ranked"][0]["is_an_open_aperture"]
    assert s["open_apertures"] == 1
    assert s["separations_already_walled"] == 1
