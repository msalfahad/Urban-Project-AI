"""The snap grid must be measured, bounded, and refusable.

Round 1 used 0.05 mm justified as "one two-thousandth of the thinnest wall".
That is a ratio to a wall, not a measurement of the coordinates being
snapped, so it could be neither confirmed nor refuted — and the next drawing
has different coordinates. These tests lock down the three things that make
the replacement auditable: it measures, it caps, and it refuses.
"""

import pytest

from engine import snap_tolerance as st
from engine.wall_solid import MAX_DEFENSIBLE_SNAP_MM, NODE_SNAP_GRID_MM


def test_the_ceiling_is_the_same_one_the_solid_enforces():
    # Two ceilings that can drift apart are one ceiling nobody enforces.
    assert st.MAX_DEFENSIBLE_SNAP_MM == MAX_DEFENSIBLE_SNAP_MM


def _ring(x, y, d=1000.0):
    return ((x, y), (x + d, y), (x + d, y + d), (x, y + d), (x, y))


def test_vertices_that_coincide_exactly_are_measured_as_noise_free():
    rings = [_ring(0.0, 0.0), _ring(1000.0, 0.0)]
    ev = st.measure(rings)
    assert ev.status == st.MEASURED
    assert ev.largest_coincidence_mm == pytest.approx(0.0)


def test_the_recommendation_sits_at_the_top_of_the_noise_population():
    # Exactly-coincident nodes sit many decades below representation noise,
    # so the histogram is bimodal. Stopping at the first empty decade would
    # recommend a grid too small to merge the nodes it exists to merge.
    rings = [_ring(0.0, 0.0),
             _ring(1000.0, 0.0),               # exact coincidence
             _ring(2000.0 + 0.004, 0.004)]     # noise-scale offset
    ev = st.measure(rings)
    assert ev.status == st.MEASURED
    assert ev.recommended_grid_mm == 0.01
    assert ev.noise_floor_mm == 0.01
    assert ev.first_empty_decade_mm == 0.1


def test_separation_must_be_proven_by_an_empty_band():
    # Offsets spread right up to the ceiling: noise and drawn gaps are
    # indistinguishable, so no tolerance is defensible.
    rings = [_ring(0.0, 0.0)]
    x = 1000.0
    for off in (0.004, 0.04, 0.4, 0.9):
        rings.append(_ring(x + off, off))
        x += 1000.0
    ev = st.measure(rings)
    assert ev.status == st.NOT_SEPARABLE
    assert ev.recommended_grid_mm is None
    assert not ev.is_usable
    assert "Snap nothing and report the gaps instead" in ev.why


def test_nothing_to_measure_is_not_a_licence_to_snap():
    rings = [_ring(0.0, 0.0), _ring(50000.0, 50000.0)]
    ev = st.measure(rings)
    assert ev.status == st.NO_COINCIDENCES
    assert ev.recommended_grid_mm is None
    assert "no tolerance is warranted" in ev.why


def test_vertices_of_one_ring_are_never_compared_with_each_other():
    # A ring's own corners are meant to be distinct. Including them would
    # put real wall lengths into a histogram of numerical noise.
    ev = st.measure([_ring(0.0, 0.0, d=0.5)])
    assert ev.pairs_examined == 0
    assert ev.status == st.NO_COINCIDENCES


def test_the_recommendation_can_never_exceed_the_absolute_ceiling():
    ev = st.measure([_ring(0.0, 0.0), _ring(1000.0, 0.0)],
                    reach_mm=st.MAX_DEFENSIBLE_SNAP_MM)
    assert ev.recommended_grid_mm <= st.MAX_DEFENSIBLE_SNAP_MM


def test_the_record_refuses_to_be_a_drawing_constant():
    ev = st.measure([_ring(0.0, 0.0), _ring(1000.0, 0.0)])
    r = ev.record()
    assert "must not be promoted to a project or engine default" in r[
        "not_a_drawing_constant"]
    assert "SNAPPING" in r["snapping_is_not_gap_closing"].upper() or \
        "invent material" in r["snapping_is_not_gap_closing"]


# --- what this says about a gap someone wants to close --------------------

def test_a_gap_orders_of_magnitude_above_the_floor_is_not_an_artefact():
    ev = st.measure([_ring(0.0, 0.0), _ring(1000.0, 0.0),
                     _ring(2000.0 + 0.004, 0.004)])
    got = st.gaps_this_cannot_close(ev, [50.0, 300.0])
    assert got["none_are_snap_artefacts"]
    assert got["gaps"][0]["multiples_of_the_grid"] == pytest.approx(5000.0)
    assert "would close every genuine gap of that size too" in got[
        "why_this_matters"]


def test_a_gap_inside_the_grid_is_reported_as_closable():
    ev = st.measure([_ring(0.0, 0.0), _ring(1000.0, 0.0),
                     _ring(2000.0 + 0.004, 0.004)])
    got = st.gaps_this_cannot_close(ev, [0.002])
    assert got["gaps"][0]["closable_by_snapping"]
    assert not got["none_are_snap_artefacts"]


# --- auditing the constant the run actually used --------------------------

def test_the_grid_in_use_becomes_auditable_once_something_measures_it():
    ev = st.measure([_ring(0.0, 0.0), _ring(1000.0, 0.0),
                     _ring(2000.0 + 0.004, 0.004)])
    got = st.compare_to_the_grid_in_use(ev, NODE_SNAP_GRID_MM)
    assert got["measured_recommendation_mm"] == 0.01
    assert got["ratio_to_the_measurement"] == pytest.approx(5.0)
    assert got["verdict"] == "SAFE_AND_WITHIN_AN_ORDER_OF_THE_MEASUREMENT"
    assert got["still_below_anything_drawn"]


def test_a_grid_smaller_than_the_noise_floor_is_named_as_such():
    ev = st.measure([_ring(0.0, 0.0), _ring(1000.0, 0.0),
                     _ring(2000.0 + 0.004, 0.004)])
    got = st.compare_to_the_grid_in_use(ev, 1e-6)
    assert got["verdict"] == "SMALLER_THAN_THE_MEASURED_NOISE_FLOOR"


def test_a_grid_above_the_ceiling_is_named_before_anything_else():
    ev = st.measure([_ring(0.0, 0.0), _ring(1000.0, 0.0),
                     _ring(2000.0 + 0.004, 0.004)])
    got = st.compare_to_the_grid_in_use(ev, 5.0)
    assert got["verdict"] == "ABOVE_THE_ABSOLUTE_CEILING"


def test_an_unmeasurable_drawing_yields_no_verdict_on_the_grid():
    ev = st.measure([_ring(0.0, 0.0), _ring(50000.0, 50000.0)])
    got = st.compare_to_the_grid_in_use(ev, NODE_SNAP_GRID_MM)
    assert got["verdict"] == "NOT_MEASURABLE_ON_THIS_DRAWING"
