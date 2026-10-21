"""E62 — accept, hash, THEN open the reference."""

from __future__ import annotations

from dataclasses import dataclass, field

import pytest

from engine.control_freeze import (ACCEPTED, BBOX_EDGE, MULTI_LABEL,
                                   NO_CANDIDATE, OVERLAPS_ANOTHER,
                                   RASTER_EDGE, REFUSED, UNSUPPORTED_BOUNDARY,
                                   WRONG_BASIS, FreezeError, accept,
                                   compare_after_freeze, geometry_hash,
                                   summary)
from engine.controls import Control


def poly(x0, y0, x1, y1):
    from shapely.geometry import Polygon
    return Polygon([(x0, y0), (x1, y0), (x1, y1), (x0, y1)])


@dataclass(frozen=True)
class Cand:
    space_geometry_id: str = "SG-1"
    geometry: object = None
    geometry_role: str = "OCCUPIABLE_SPACE_CANDIDATE"
    measurement_basis: str = "CLEAR_INTERNAL_FINISH_FACE"
    bounding_band_ids: tuple = ("WB-1", "WB-2")
    bounding_portal_ids: tuple = ()
    provenance: dict = field(default_factory=lambda: {
        "bbox_derived_edges": 0, "raster_derived_edges": 0,
        "centreline_offset_used": False})

    @property
    def area_m2(self):
        return self.geometry.area / 1e6

    @property
    def perimeter_m(self):
        return self.geometry.length / 1000

    @property
    def polygon_mm(self):
        return tuple(self.geometry.exterior.coords)[:-1]


@dataclass(frozen=True)
class Env:
    geometry: object


def ctl(sid="BED-01", rt="BEDROOM"):
    return Control(sid, rt, "by rule")


def good(**kw):
    return Cand(geometry=poly(0, 0, 4000, 3000), **kw)


ENV = Env(poly(-1000, -1000, 20000, 20000))


# --- the gate ---------------------------------------------------------------

def test_a_clean_candidate_is_accepted_and_hashed():
    f = accept(ctl(), good(), envelope=ENV, labels_inside=("BED-01",),
               run_id="R1")
    assert f.status == ACCEPTED
    assert f.accepted
    assert f.area_m2 == pytest.approx(12.0)
    assert len(f.geometry_hash) == 24
    assert f.record()["frozen_before_any_reference_was_read"] is True


def test_no_candidate_at_all_is_refused_and_says_the_raster_may_not_stand_in():
    f = accept(ctl(), None, envelope=ENV, labels_inside=())
    assert f.status == REFUSED
    assert f.refusals == (NO_CANDIDATE,)
    assert "raster outline may not stand in" in f.why


def test_more_than_one_labelled_room_inside_is_refused():
    f = accept(ctl(), good(), envelope=ENV,
               labels_inside=("BED-NW", "BTH-01"))
    assert MULTI_LABEL in f.refusals
    assert not f.accepted


def test_a_bbox_derived_edge_is_refused_however_well_it_measures():
    c = good(provenance={"bbox_derived_edges": 1, "raster_derived_edges": 0})
    f = accept(ctl(), c, envelope=ENV, labels_inside=("BED-01",))
    assert BBOX_EDGE in f.refusals
    assert "right for the wrong reason" in f.why


def test_a_raster_derived_millimetre_edge_is_refused():
    c = good(provenance={"bbox_derived_edges": 0, "raster_derived_edges": 3})
    f = accept(ctl(), c, envelope=ENV, labels_inside=("BED-01",))
    assert RASTER_EDGE in f.refusals


def test_a_boundary_with_no_wall_support_is_refused():
    f = accept(ctl(), good(bounding_band_ids=()), envelope=ENV,
               labels_inside=("BED-01",))
    assert UNSUPPORTED_BOUNDARY in f.refusals


def test_the_wrong_measurement_basis_is_refused():
    f = accept(ctl(), good(measurement_basis="WALL_CENTRELINE_FACE"),
               envelope=ENV, labels_inside=("BED-01",))
    assert WRONG_BASIS in f.refusals


def test_overlapping_an_accepted_space_is_refused():
    other = Cand(space_geometry_id="SG-2", geometry=poly(2000, 0, 6000, 3000))
    f = accept(ctl(), good(), envelope=ENV, labels_inside=("BED-01",),
               others=[other])
    assert OVERLAPS_ANOTHER in f.refusals


# --- the freeze is the guarantee -------------------------------------------

def test_the_hash_covers_the_provenance_not_only_the_coordinates():
    """The same coordinates reached a different way are a different result."""
    a = geometry_hash("X", ((0, 0), (1, 0), (1, 1)), {"method": "FREE_SPACE"})
    b = geometry_hash("X", ((0, 0), (1, 0), (1, 1)), {"method": "RASTER"})
    assert a != b


def test_a_comparison_against_unfrozen_geometry_is_refused():
    from engine.control_freeze import FrozenControl
    unfrozen = FrozenControl("BED-01", "BEDROOM", "SG-1", ACCEPTED,
                             polygon_mm=((0, 0), (1, 0), (1, 1)),
                             area_m2=12.0, geometry_hash="")
    with pytest.raises(FreezeError, match="never frozen"):
        compare_after_freeze(unfrozen, reference_area_m2=12.0)


def test_a_refused_control_has_nothing_to_compare():
    f = accept(ctl(), None, envelope=ENV, labels_inside=())
    out = compare_after_freeze(f, reference_area_m2=12.0)
    assert out["comparable"] is False


def test_comparing_across_bases_is_refused_rather_than_answered():
    f = accept(ctl(), good(), envelope=ENV, labels_inside=("BED-01",))
    out = compare_after_freeze(f, reference_area_m2=12.0,
                               reference_basis="WALL_CENTRELINE_FACE")
    assert out["comparable"] is False
    assert "NEVER COMPARE UNLIKE BASES" in out["why"]


def test_a_missing_reference_is_stated_not_scored_as_zero():
    f = accept(ctl(), good(), envelope=ENV, labels_inside=("BED-01",))
    out = compare_after_freeze(f, reference_area_m2=None,
                               reference_name="SITE_BENCHMARK")
    assert out["comparable"] is False
    assert "SITE_BENCHMARK" in out["why"]


# --- a ragged reference is not an engine error ------------------------------

def test_a_pixel_staircase_perimeter_is_not_a_comparable_perimeter():
    """92 m of boundary around a 24 m2 room is the reference's raggedness,
    not the engine's error."""
    f = accept(ctl(), good(), envelope=ENV, labels_inside=("BED-01",))
    out = compare_after_freeze(f, reference_area_m2=12.0,
                               reference_perimeter_m=60.0,
                               reference_basis="CLEAR_INTERNAL_FINISH_FACE")
    assert out["perimeter_comparable"] is False
    assert "pixel staircase" in out["perimeter_why"]
    assert "perimeter_error_pct" not in out


def test_a_plausible_reference_perimeter_is_compared():
    f = accept(ctl(), good(), envelope=ENV, labels_inside=("BED-01",))
    out = compare_after_freeze(f, reference_area_m2=12.0,
                               reference_perimeter_m=14.5,
                               reference_basis="CLEAR_INTERNAL_FINISH_FACE")
    assert out["perimeter_comparable"] is True
    assert out["perimeter_error_pct"] is not None


# --- the exit gate ----------------------------------------------------------

def test_one_accepted_control_passes_the_exit_gate():
    ok = accept(ctl(), good(), envelope=ENV, labels_inside=("BED-01",))
    bad = accept(ctl("STR-01", "STORE"), None, envelope=ENV,
                 labels_inside=())
    out = summary([ok, bad])
    assert out["exit_gate"] == "PASS"
    assert out["accepted_space_ids"] == ["BED-01"]
    assert "STR-01" in out["refusal_reasons"]


def test_no_accepted_control_fails_the_exit_gate():
    bad = accept(ctl(), None, envelope=ENV, labels_inside=())
    assert summary([bad])["exit_gate"] == "FAIL"
