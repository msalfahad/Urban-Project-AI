"""Generic ground-slab QTO (engine/source/ground_slab_qto.py): synthetic known answers only, no project data.

Exact strips for straight and circular edges, both bar directions independent, the rate density never rounded or
+1, holes deducted, curves integrated as curves, and no volume without a source thickness."""

from __future__ import annotations

import math

import pytest

from engine.source import ground_slab_qto as G
from engine.source import slab_rebar_qto as SR


def poly(pts):
    return G.ring_from_polygon(pts)[0]


def integ(region, d):
    return math.fsum(s["integral_mm2"] for s in G.band_strips(region, d))


def rounded_rect(w, h, r, n=24):
    """w x h rectangle at the origin with its top-right corner rounded by radius r, the arc given as n chords."""
    c = (w - r, h - r)
    pts = [(c[0], h), (0, h), (0, 0), (w, 0), (w, c[1])]
    pts += [(c[0] + r * math.cos(math.radians(90 * k / n)), c[1] + r * math.sin(math.radians(90 * k / n)))
            for k in range(1, n)]
    return pts, (c, r, 0.0, 90.0)


# ------------------------------------------------------------------ rate density
def test_rectangle_rate_times_area_both_directions():
    reg = [poly([(0, 0), (3525, 0), (3525, 4225), (0, 4225)])]
    x = G.mesh_direction(reg, G.X, rate_per_m=5, dia_mm=10)
    y = G.mesh_direction(reg, G.Y, rate_per_m=5, dia_mm=10)
    assert [(s["width_mm"], s["run_mm"]) for s in x["strips"]] == [(4225.0, 3525.0)]
    assert [(s["width_mm"], s["run_mm"]) for s in y["strips"]] == [(3525.0, 4225.0)]
    for q in (x, y):
        assert q["length_m"] == pytest.approx(5 * 14.893125, rel=1e-12)
        assert q["kg"] == pytest.approx(5 * 14.893125 * 100 / 162, rel=1e-12)
        assert q["coverage"]["reconciled"]


def test_no_plus_one_and_no_rounding_of_the_equivalent_count():
    reg = [poly([(0, 0), (4225, 0), (4225, 3525), (0, 3525)])]
    q = G.mesh_direction(reg, G.X, rate_per_m=5, dia_mm=10)
    assert q["equivalent_count"] == pytest.approx(17.625)        # not 18 and not 19 (no ceil, no +1)
    assert q["physical_bbs_count"] == SR.UNRESOLVED


def test_unit_mass_is_d_squared_over_162():
    reg = [poly([(0, 0), (1000, 0), (1000, 1000), (0, 1000)])]
    q = G.mesh_direction(reg, G.Y, rate_per_m=1, dia_mm=10)
    assert q["unit_mass_kg_m"] == pytest.approx(100 / 162, rel=1e-15)
    assert q["kg"] == pytest.approx(100 / 162, rel=1e-12)


# ------------------------------------------------------------------ exact strips
def test_l_shape_has_its_own_bands_in_each_direction():
    reg = [poly([(0, 0), (4000, 0), (4000, 1000), (1000, 1000), (1000, 3000), (0, 3000)])]
    bx, by = G.band_strips(reg, G.X), G.band_strips(reg, G.Y)
    assert [(s["width_mm"], s["run_mm"]) for s in bx] == [(1000.0, 4000.0), (2000.0, 1000.0)]
    assert [(s["width_mm"], s["run_mm"]) for s in by] == [(1000.0, 3000.0), (3000.0, 1000.0)]
    assert integ(reg, G.X) == integ(reg, G.Y) == G.area(reg) == 6e6


def test_hole_is_deducted_in_both_directions():
    reg = [poly([(0, 0), (5000, 0), (5000, 4000), (0, 4000)]),
           poly([(1000, 1000), (2000, 1000), (2000, 2000), (1000, 2000)])]
    assert G.area(reg) == 19e6
    assert integ(reg, G.X) == pytest.approx(19e6, abs=1e-6)
    assert integ(reg, G.Y) == pytest.approx(19e6, abs=1e-6)
    assert max(s["intervals"] for s in G.band_strips(reg, G.X)) == 2


def test_sloped_edges_are_integrated_exactly():
    reg = [poly([(0, 0), (3000, 0), (0, 2000)])]
    assert integ(reg, G.X) == pytest.approx(3e6, abs=1e-6)
    assert integ(reg, G.Y) == pytest.approx(3e6, abs=1e-6)


def test_ring_orientation_does_not_matter():
    ccw = [poly([(0, 0), (3000, 0), (3000, 2000), (0, 2000)])]
    cw = [poly([(0, 0), (0, 2000), (3000, 2000), (3000, 0)])]
    for d in G.DIRECTIONS:
        assert integ(ccw, d) == integ(cw, d) == G.area(cw) == 6e6


# ------------------------------------------------------------------ curves
def test_a_drawn_arc_is_integrated_as_an_arc_not_as_its_chords():
    pts, a = rounded_rect(3800, 6100, 1000)
    exact = 3800 * 6100 - (1 - math.pi / 4) * 1e6
    chords = [poly(pts)]
    ring, replaced = G.ring_from_polygon(pts, [a])
    assert replaced == 23
    assert G.area(chords) < exact                                  # chords cut the curve
    assert G.area([ring]) == pytest.approx(exact, abs=1e-6)
    for d in G.DIRECTIONS:
        assert integ([ring], d) == pytest.approx(exact, abs=1e-6)
        assert "A" in {b for s in G.band_strips([ring], d) for b in s["branches"]}


def test_a_cell_bounded_by_part_of_an_arc_gets_the_sub_arc():
    r = 1000.0
    pts = [(0, 0), (r, 0)] + [(r * math.cos(math.radians(t)), r * math.sin(math.radians(t))) for t in range(6, 90, 6)]
    pts += [(0, r)]
    ring, replaced = G.ring_from_polygon(pts, [((0, 0), r, -30.0, 180.0)])   # the drawn arc is longer
    assert replaced == 14
    assert G.area([ring]) == pytest.approx(math.pi / 4 * r * r, abs=1e-6)


def test_full_disk_from_two_arcs():
    reg = [[G.arc((0, 0), 1000, 0, math.pi), G.arc((0, 0), 1000, math.pi, 2 * math.pi)]]
    for d in G.DIRECTIONS:
        assert integ(reg, d) == pytest.approx(math.pi * 1e6, abs=1e-6)


def test_a_vertex_off_the_circle_is_kept_as_drawn():
    pts, a = rounded_rect(3800, 6100, 1000, n=8)
    off = (pts[7][0] + 5.0, pts[7][1])                             # a notch 5 mm outside the curve
    pts[7] = off
    ring, _ = G.ring_from_polygon(pts, [a])
    assert sum(1 for e in ring if e[0] == G.ARC) == 2              # two stretches of the arc
    assert any(e[0] == G.LINE and off in (e[1], e[2]) for e in ring)
    exact = 3800 * 6100 - (1 - math.pi / 4) * 1e6
    th = math.radians(22.5)                                        # the stretch the off vertex replaces by two lines
    bulge = 0.5 * 1000.0 ** 2 * (th - math.sin(th))
    assert 0 < abs(G.area([ring]) - exact) < bulge                 # only that stretch differs from the arc


def test_a_run_that_turns_both_ways_is_refused():
    r = 1000.0
    ang = (0, 10, 20, 15, 30)
    pts = [(-2000.0, -2000.0)] + [(r * math.cos(math.radians(t)), r * math.sin(math.radians(t))) for t in ang]
    with pytest.raises(G.GroundSlabQtoError):
        G.ring_from_polygon(pts, [((0, 0), r, 0.0, 90.0)])


def test_a_long_straight_edge_between_two_circle_points_is_not_an_arc():
    r = 1000.0
    pts = [(r, 0), (0, r), (-r, 0), (0, -r)]                       # a square inscribed in the circle: 90-deg chords
    with pytest.raises(G.GroundSlabQtoError):
        G.ring_from_polygon(pts, [((0, 0), r, 0.0, 360.0)])
    assert G.area([poly(pts)]) == pytest.approx(2 * r * r)         # as a polygon it stays a square


def test_open_ring_is_refused():
    with pytest.raises(G.GroundSlabQtoError):
        G.check_ring([G.line((0, 0), (1, 0)), G.line((1, 0), (1, 1))])


# ------------------------------------------------------------------ concrete
def test_concrete_is_area_times_source_thickness_and_none_without_it():
    assert G.slab_concrete(14.893125, 100) == pytest.approx(1.4893125)
    assert G.slab_concrete(14.893125, None) is None                # unknown is not zero
    with pytest.raises(G.GroundSlabQtoError):
        G.slab_concrete(10.0, 0)


def test_lanes_are_the_slab_qto_lanes():
    assert SR.PROJECT_BASIS_QTO in SR.MASS_LANES and SR.BLOCKED_UNQUANTIFIED in SR.NO_MASS_LANES
    with pytest.raises(SR.SlabRebarQtoError):
        SR.check_label("FINAL_SLAB_REBAR")
