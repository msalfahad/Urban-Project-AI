"""Generic region recovery (engine/source/region_recovery.py): synthetic known answers only, no project data.

A partition closes only what the drawing closes and covers its domain once. Every part takes one lane from drawn
evidence, and a part with no identity is never a slab by default. The cover fit stacks E.W. as one mesh and T&B as
two."""

from __future__ import annotations

import pytest
from shapely.geometry import LineString, Polygon, box

from engine.source import region_recovery as RR


def band(a, b, w):
    return LineString([a, b]).buffer(w / 2.0, cap_style=2)


# ------------------------------------------------------------------ partition
def test_partition_covers_the_domain_exactly_once():
    dom = box(0, 0, 6000, 4000)
    bars = [LineString([(3000, -500), (3000, 4500)]), LineString([(0, 2000), (3000, 2000)])]
    faces = RR.partition(dom, bars)
    assert sorted(round(f.area / 1e6, 6) for f in faces) == [6.0, 6.0, 12.0]
    pr = RR.tiling_proof(dom, faces)
    assert pr["exact"] and pr["overlap_mm2"] == 0 and pr["gap_mm2"] == 0


def test_an_open_line_closes_nothing():
    dom = box(0, 0, 4000, 4000)
    faces = RR.partition(dom, [LineString([(2000, 0), (2000, 3950)])])   # stops 50 mm short of the far edge
    assert len(faces) == 1 and faces[0].area == pytest.approx(16e6)


def test_a_closed_outline_inside_the_domain_becomes_its_own_face_and_holes_are_kept():
    dom = Polygon([(0, 0), (8000, 0), (8000, 6000), (0, 6000)], [[(500, 500), (1000, 500), (1000, 1000), (500, 1000)]])
    pit = box(3000, 2000, 5000, 4000).exterior
    faces = RR.partition(dom, [pit])
    assert sorted(round(f.area / 1e6, 4) for f in faces) == [4.0, round(48 - 0.25 - 4, 4)]
    assert RR.tiling_proof(dom, faces)["exact"]


def test_a_gap_and_an_overlap_are_reported():
    dom = box(0, 0, 2000, 1000)
    assert not RR.tiling_proof(dom, [box(0, 0, 1000, 1000)])["exact"]                          # gap
    pr = RR.tiling_proof(dom, [box(0, 0, 1200, 1000), box(1000, 0, 2000, 1000)])
    assert pr["overlap_mm2"] == pytest.approx(0.2e6) and not pr["exact"]


def test_partition_is_independent_of_barrier_order():
    dom = box(0, 0, 6000, 4000)
    bars = [LineString([(3000, 0), (3000, 4000)]), LineString([(0, 2000), (6000, 2000)])]
    a = [round(f.area, 3) for f in RR.partition(dom, bars)]
    b = [round(f.area, 3) for f in RR.partition(dom, list(reversed(bars)))]
    assert a == b == [6e6] * 4


# ------------------------------------------------------------------ classification
def test_pit_ring_opening_wall_beam_stair_and_cell():
    ring = box(2000, 2000, 4200, 4200).difference(box(2200, 2200, 4000, 4000))
    island = box(2200, 2200, 4000, 4000)
    beam = band((0, 1150), (8000, 1150), 300)
    treads = [(f"T{i}", LineString([(5100, 2000 + 300 * i), (5900, 2000 + 300 * i)])) for i in range(5)]
    ev = {"openings": [("PIT", island)], "walls": [("RING", ring)], "beam_bands": [("GB1", beam)], "treads": treads}
    assert RR.classify(island, **ev)[0] == RR.LIFT_PIT_OPENING
    assert RR.classify(box(2000, 2000, 4200, 2200), **ev)[:2] == (RR.STRUCTURAL_BEAM_OR_WALL, "WALL")
    assert RR.classify(box(1000, 1000, 7000, 1300), **ev)[:2] == (RR.STRUCTURAL_BEAM_OR_WALL, "BEAM")
    lane, kind, e = RR.classify(box(5000, 1900, 6000, 3500), **ev)
    assert lane == RR.STAIR_OR_SPECIAL_STRUCTURE and len(e["treads"]) == 5
    assert RR.classify(box(4300, 1400, 4900, 4000), **ev)[0] == RR.GROUND_SLAB_CANDIDATE


def test_three_treads_do_not_make_a_stair():
    treads = [(f"T{i}", LineString([(100, 200 + 300 * i), (900, 200 + 300 * i)])) for i in range(3)]
    assert RR.classify(box(0, 0, 1000, 1000), treads=treads)[0] == RR.GROUND_SLAB_CANDIDATE


def test_partly_inside_a_wall_is_blocked_not_a_slab():
    wall = box(0, 0, 200, 2000)
    lane, kind, e = RR.classify(box(100, 0, 1100, 2000), walls=[("W", wall)])
    assert (lane, kind) == (RR.CLASSIFICATION_BLOCKED, "EVIDENCE_DISAGREES")


def test_a_shared_edge_is_not_partial_evidence():
    wall = box(0, 0, 200, 2000)
    assert RR.classify(box(200, 0, 1200, 2000), walls=[("W", wall)])[0] == RR.GROUND_SLAB_CANDIDATE


def test_sliver_and_outside():
    assert RR.classify(box(0, 0, 10, 50))[:2] == (RR.CLASSIFICATION_BLOCKED, "SLIVER")
    env = box(0, 0, 1000, 1000)
    assert RR.classify(box(900, 0, 1900, 1000), envelope=env)[0] == RR.OUTSIDE_BUILDING


def test_column_outline():
    col = box(0, 0, 300, 500)
    assert RR.classify(box(0, 0, 300, 500), columns=[("C", col)])[:2] == (RR.STRUCTURAL_BEAM_OR_WALL, "COLUMN")


# ------------------------------------------------------------------ cover fit
def test_each_way_is_one_mesh_of_two_crossing_directions():
    f = RR.mesh_cover_fit(100, (10, 10), 25, 25)
    assert f["required_mm"] == 70 and f["margin_mm"] == 30 and f["fits"] is True
    f = RR.mesh_cover_fit(100, (10, 10), 70, 25)
    assert f["required_mm"] == 115 and f["margin_mm"] == -15 and f["fits"] is False


def test_top_and_bottom_mats_stack_twice():
    assert RR.mesh_cover_fit(100, (10, 10, 10, 10), 25, 25)["required_mm"] == 90


def test_unknown_cover_gives_no_verdict_and_bad_inputs_are_refused():
    assert RR.mesh_cover_fit(100, (10, 10), None, 25)["fits"] is None
    with pytest.raises(RR.RegionRecoveryError):
        RR.mesh_cover_fit(None, (10, 10), 25, 25)
    with pytest.raises(RR.RegionRecoveryError):
        RR.mesh_cover_fit(100, (), 25, 25)
    with pytest.raises(RR.RegionRecoveryError):
        RR.partition(Polygon(), [])
