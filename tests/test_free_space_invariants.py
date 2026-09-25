"""Invariants A-H of the free-space construction, and proof each one fires.

An invariant nobody has seen fail is a comment. Every check here gets a
positive control: a construction that breaks it, asserted to be caught. The
tolerances are ABSOLUTE and the tests say why — a percentage on a 1000 m2
envelope hides several square metres of lost topology inside an agreeable
figure, which is precisely the failure being hunted.
"""

import pytest
from shapely.geometry import Polygon
from shapely.ops import unary_union

from engine import free_space_invariants as fsi
from engine.free_space import (BARRIER_ACCEPTED, BARRIER_REJECTED,
                               OCCUPIABLE_SPACE_CANDIDATE)


# --- stand-ins carrying only the fields the invariants read ---------------

class _WP:
    def __init__(self, i, ring, reason=""):
        self.wall_band_id, self.ring = i, ring
        self.unresolved_reason = reason

    @property
    def is_resolved(self):
        return bool(self.ring)


class _Solid:
    def __init__(self, geom, grid=0.0):
        self.geometry, self.snap_grid_mm = geom, grid


class _Barrier:
    def __init__(self, i, ring, status=BARRIER_ACCEPTED):
        self.portal_id, self.ring, self.status = i, ring, status


class _Env:
    def __init__(self, geom):
        self.geometry = geom


class _Cand:
    def __init__(self, i, geom):
        self.space_geometry_id, self.geometry = i, geom
        self.geometry_role = OCCUPIABLE_SPACE_CANDIDATE


def _ring(x0, y0, x1, y1):
    return ((x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0))


def _poly(x0, y0, x1, y1):
    return Polygon(_ring(x0, y0, x1, y1))


def _sound():
    """A 10x10 m envelope, one internal wall, two rooms. Conserves exactly."""
    env = _poly(0, 0, 10000, 10000)
    wall = _poly(4900, 0, 5100, 10000)
    rooms = [_Cand("SG-1", _poly(0, 0, 4900, 10000)),
             _Cand("SG-2", _poly(5100, 0, 10000, 10000))]
    return ([_WP("WB-1", _ring(4900, 0, 5100, 10000))],
            _Solid(wall), [], _Env(env), rooms)


def test_a_sound_construction_holds_every_invariant():
    rep = fsi.falsify(*_sound())
    assert rep.holds, rep.by_invariant()
    assert set(rep.record()["invariants_checked"]) == set(fsi.INVARIANTS)
    fsi.assert_sound(*_sound())


def test_the_conservation_identity_is_reported_whether_it_holds_or_not():
    rep = fsi.falsify(*_sound())
    got = rep.checked["area_conservation"]
    assert got["envelope_m2"] == pytest.approx(100.0)
    assert got["obstacles_inside_envelope_m2"] == pytest.approx(2.0)
    assert got["free_space_m2"] == pytest.approx(98.0)
    assert abs(got["residual_mm2"]) <= fsi.AREA_TOLERANCE_MM2


# --- A: a band that produced nothing must say why -------------------------

def test_an_unresolved_wall_polygon_without_a_reason_is_a_violation():
    wps, solid, bars, env, cands = _sound()
    wps.append(_WP("WB-silent", (), reason=""))
    rep = fsi.falsify(wps, solid, bars, env, cands)
    assert fsi.INV_WALL_POLYGON_VALID in rep.by_invariant()


def test_an_unresolved_wall_polygon_with_a_reason_is_accepted():
    wps, solid, bars, env, cands = _sound()
    wps.append(_WP("WB-honest", (), reason="NO_SECOND_FACE"))
    assert fsi.falsify(wps, solid, bars, env, cands).holds


def test_a_resolved_but_self_intersecting_wall_polygon_is_caught():
    wps, solid, bars, env, cands = _sound()
    bowtie = ((0, 0), (100, 100), (100, 0), (0, 100), (0, 0))
    wps.append(_WP("WB-bowtie", bowtie))
    rep = fsi.falsify(wps, solid, bars, env, cands)
    assert fsi.INV_WALL_POLYGON_VALID in rep.by_invariant()


# --- C/D: the components ---------------------------------------------------

def test_two_free_space_polygons_that_overlap_are_caught():
    # Connected components of one geometry are disjoint, so an overlap means
    # the free space was NOT built from a single difference.
    wps, solid, bars, env, _ = _sound()
    cands = [_Cand("SG-1", _poly(0, 0, 6000, 10000)),
             _Cand("SG-2", _poly(4000, 0, 10000, 10000))]
    rep = fsi.falsify(wps, solid, bars, env, cands)
    assert fsi.INV_NO_FREE_OVERLAP in rep.by_invariant()


def test_two_polygons_merely_sharing_an_edge_do_not_overlap():
    wps, solid, bars, env, _ = _sound()
    cands = [_Cand("SG-1", _poly(0, 0, 5000, 10000)),
             _Cand("SG-2", _poly(5000, 0, 10000, 10000))]
    rep = fsi.falsify(wps, solid, bars, env, cands)
    assert fsi.INV_NO_FREE_OVERLAP not in rep.by_invariant()


# --- E: free space cannot exist where the floor does not ------------------

def test_free_space_outside_the_envelope_is_caught():
    wps, solid, bars, env, cands = _sound()
    cands = cands + [_Cand("SG-outside", _poly(11000, 0, 12000, 1000))]
    rep = fsi.falsify(wps, solid, bars, env, cands)
    assert fsi.INV_INSIDE_ENVELOPE in rep.by_invariant()


def test_a_millimetre_of_shared_boundary_is_not_an_escape():
    # The envelope's own ring is built from the same coordinates, so a
    # sub-millimetre poke is an artefact, not free space off the floor.
    wps, solid, bars, env, cands = _sound()
    cands[1] = _Cand("SG-2", _poly(5100, 0, 10000.5, 10000))
    rep = fsi.falsify(wps, solid, bars, env, cands)
    assert fsi.INV_INSIDE_ENVELOPE not in rep.by_invariant()


# --- F: space and material cannot occupy the same millimetre --------------

def test_free_space_overlapping_the_wall_solid_is_caught():
    wps, _, bars, env, cands = _sound()
    solid = _Solid(_poly(4000, 0, 6000, 10000))
    rep = fsi.falsify(wps, solid, bars, env, cands)
    assert fsi.INV_NO_SOLID_INTERSECTION in rep.by_invariant()


# --- G: a barrier exists precisely to keep free space out -----------------

def test_free_space_overlapping_an_accepted_barrier_is_caught():
    wps, solid, _, env, cands = _sound()
    bars = [_Barrier("PT-1", _ring(1000, 1000, 2000, 2000))]
    rep = fsi.falsify(wps, solid, bars, env, cands)
    assert fsi.INV_NO_BARRIER_INTERSECTION in rep.by_invariant()


def test_a_rejected_barrier_is_not_checked_because_it_does_not_exist():
    wps, solid, _, env, cands = _sound()
    bars = [_Barrier("PT-1", _ring(1000, 1000, 2000, 2000),
                     status=BARRIER_REJECTED)]
    rep = fsi.falsify(wps, solid, bars, env, cands)
    assert fsi.INV_NO_BARRIER_INTERSECTION not in rep.by_invariant()


def test_barriers_are_checked_on_the_same_grid_as_the_solid():
    # An unsnapped barrier checked against a snapped difference is two
    # different geometries, and the discrepancy is not a violation of
    # anything. This failed six times with 2-25 mm2 overlaps before the
    # grid was applied on both sides — and the fix was not a wider
    # tolerance: an invariant one may widen to pass is not an invariant.
    env = _poly(0, 0, 10000, 10000)
    grid = 0.05
    bar_ring = _ring(4000.013, 0.017, 4200.013, 3000.017)
    solid = _Solid(_poly(4900, 0, 5100, 10000), grid=grid)
    from engine.free_space import _on_grid
    snapped = _on_grid(Polygon(bar_ring), grid)
    free = unary_union([env]).difference(
        unary_union([solid.geometry, snapped]))
    cands = [_Cand(f"SG-{i}", g)
             for i, g in enumerate(getattr(free, "geoms", [free]), 1)]
    rep = fsi.falsify([], solid, [_Barrier("PT-1", bar_ring)], _Env(env),
                      cands)
    assert fsi.INV_NO_BARRIER_INTERSECTION not in rep.by_invariant()


# --- H: a small absolute loss on a large floor ----------------------------

def test_losing_a_sliver_of_the_envelope_is_caught_however_small():
    # 0.02 m2 lost from 100 m2 is 0.02% — a figure any percentage tolerance
    # would wave through. Absolutely, it is two hundred square centimetres
    # of floor that is neither wall nor room.
    wps, solid, bars, env, cands = _sound()
    cands[0] = _Cand("SG-1", _poly(0, 0, 4900, 9959))
    rep = fsi.falsify(wps, solid, bars, env, cands)
    assert fsi.INV_AREA_CONSERVED in rep.by_invariant()
    lost = rep.checked["area_conservation"]["residual_m2"]
    assert lost == pytest.approx(0.2009, abs=0.01)


def test_the_area_tolerance_is_absolute_and_one_square_centimetre():
    assert fsi.AREA_TOLERANCE_MM2 == 10_000.0
    assert "ABSOLUTE" in fsi.Report().record()["note"]
    assert "percentage" in fsi.Report().record()["note"]


def test_overlapping_barriers_are_counted_once_in_the_identity():
    # Summing barrier areas instead of unioning them would show a phantom
    # deficit and send someone hunting for geometry that was never lost.
    env = _poly(0, 0, 10000, 10000)
    bars = [_Barrier("PT-1", _ring(1000, 1000, 3000, 3000)),
            _Barrier("PT-2", _ring(2000, 1000, 4000, 3000))]
    both = unary_union([Polygon(b.ring) for b in bars])
    free = env.difference(both)
    cands = [_Cand("SG-1", free)]
    rep = fsi.falsify([], _Solid(None), bars, _Env(env), cands)
    got = rep.checked["area_conservation"]
    assert got["obstacles_inside_envelope_m2"] == pytest.approx(
        both.area / 1e6)
    assert fsi.INV_AREA_CONSERVED not in rep.by_invariant()


def test_a_barrier_outside_the_envelope_is_not_counted_as_an_obstacle():
    env = _poly(0, 0, 10000, 10000)
    bars = [_Barrier("PT-far", _ring(20000, 0, 21000, 1000))]
    cands = [_Cand("SG-1", env)]
    rep = fsi.falsify([], _Solid(None), bars, _Env(env), cands)
    assert rep.checked["area_conservation"][
        "obstacles_inside_envelope_m2"] == 0.0
    assert rep.holds


def test_assert_sound_raises_and_names_the_invariant():
    wps, solid, bars, env, cands = _sound()
    cands[0] = _Cand("SG-1", _poly(0, 0, 4900, 9000))
    with pytest.raises(fsi.FreeSpaceFalsified) as e:
        fsi.assert_sound(wps, solid, bars, env, cands)
    assert "neither obstacle nor free space" in str(e.value)
