"""Two solids, per-interval admission, and repairs that must prove causal.

The defect being closed: one wall solid held both the 446 m where two faces
were drawn and the 55.9 m the band engine itself records as NOT established
material, and every quantity was measured against the union. A reader could
not tell which part a number came from.
"""

import pytest
from shapely.geometry import Polygon, box

from engine import counterfactual as cf
from engine import junction_patch as jp
from engine import wall_authority as wa


class _WP:
    def __init__(self, i, lo, hi, a, b, ext=(), axis="H", fixed=1000.0,
                 t=200.0):
        self.wall_band_id, self.axis = i, axis
        self.start_mm, self.end_mm = lo, hi
        self.face_a_mm, self.face_b_mm = fixed, fixed + t
        self.face_a_intervals, self.face_b_intervals = tuple(a), tuple(b)
        self.extensions = tuple(ext)
        self.source_face_ids = (f"{i}-A", f"{i}-B")
        self.ring = ((lo, fixed), (hi, fixed), (hi, fixed + t),
                     (lo, fixed + t), (lo, fixed))

    @property
    def is_resolved(self):
        return True


# --- per-interval admission ----------------------------------------------

def test_both_faces_drawn_enters_both_solids():
    wp = _WP("WB-1", 0.0, 3000.0, [(0.0, 3000.0)], [(0.0, 3000.0)])
    a = wa.classify_intervals([wp]).admissions[0]
    assert a.grounds == wa.BOTH_FACES_DRAWN
    assert a.solids == (wa.ESTABLISHED, wa.DIAGNOSTIC)
    assert a.is_established


def test_an_unresolved_extension_is_refused_from_the_established_solid():
    wp = _WP("WB-1", 0.0, 3000.0, [(0.0, 3000.0)], [(2000.0, 3000.0)],
             ext=[{"end": "start", "length_mm": 2000.0,
                   "extension_reason": "UNRESOLVED_EXTENSION"}])
    rep = wa.classify_intervals([wp])
    bad = [a for a in rep.admissions if not a.is_established]
    assert len(bad) == 1
    assert bad[0].grounds == wa.UNRESOLVED_EXTENSION
    assert bad[0].solids == (wa.DIAGNOSTIC,)
    assert bad[0].length_mm == pytest.approx(2000.0)
    assert "refused from the established solid" in bad[0].why


def test_a_cap_supported_extension_is_established():
    wp = _WP("WB-1", 0.0, 3000.0, [(0.0, 3000.0)], [(2000.0, 3000.0)],
             ext=[{"end": "start", "length_mm": 2000.0,
                   "extension_reason": "END_CAP_SUPPORTED"}])
    rep = wa.classify_intervals([wp])
    assert all(a.is_established for a in rep.admissions)
    assert wa.ONE_FACE_CAP_CLOSED in {a.grounds for a in rep.admissions}


def test_admission_is_per_interval_so_one_band_can_be_both():
    # Deciding whole polygons would either discard 1000 mm of real wall or
    # admit 2000 mm of invention.
    wp = _WP("WB-1", 0.0, 3000.0, [(0.0, 3000.0)], [(2000.0, 3000.0)],
             ext=[{"end": "start", "length_mm": 2000.0,
                   "extension_reason": "UNRESOLVED_EXTENSION"}])
    rep = wa.classify_intervals([wp])
    assert rep._m(rep.established) == pytest.approx(1.0)
    assert rep._m(rep.diagnostic_only) == pytest.approx(2.0)
    assert "per INTERVAL, not per polygon" in rep.record()["the_rule"]


def test_no_interval_provenance_means_not_established():
    wp = _WP("WB-1", 0.0, 3000.0, [], [])
    a = wa.classify_intervals([wp]).admissions[0]
    assert a.grounds == wa.NO_FACE_INTERVALS
    assert not a.is_established
    assert "cannot be established is not established" in a.why


def test_an_interval_below_the_floor_is_not_a_decision():
    wp = _WP("WB-1", 0.0, 3000.0, [(0.0, 3000.0)], [(0.0, 2980.0)])
    grounds = {a.grounds for a in wa.classify_intervals([wp]).admissions}
    assert grounds == {wa.BOTH_FACES_DRAWN}


# --- the two solids differ by exactly the unestablished material ---------

def test_the_diagnostic_solid_adds_only_the_unestablished_material():
    wp = _WP("WB-1", 0.0, 3000.0, [(0.0, 3000.0)], [(2000.0, 3000.0)],
             ext=[{"end": "start", "length_mm": 2000.0,
                   "extension_reason": "UNRESOLVED_EXTENSION"}])
    rep = wa.classify_intervals([wp])
    est = wa.build([wp], solid=wa.ESTABLISHED, report=rep)
    dia = wa.build([wp], solid=wa.DIAGNOSTIC, report=rep)
    got = wa.compare(est, dia)
    assert got["established_area_m2"] == pytest.approx(0.2)
    assert got["diagnostic_augmented_area_m2"] == pytest.approx(0.6)
    assert got["added_by_hypothesis_m2"] == pytest.approx(0.4)


def test_component_count_is_reported_but_not_a_target():
    got = wa.compare(None, None)
    assert "not automatically defective" in got[
        "why_components_are_not_a_target"]


def test_an_unknown_solid_is_refused():
    with pytest.raises(wa.WallAuthorityError):
        wa.build([], solid="SOMETHING_ELSE")


def test_the_record_says_what_may_depend_on_each_solid():
    got = wa.classify_intervals([]).record()["what_may_depend_on_each"]
    assert "production room geometry" in got[wa.ESTABLISHED]
    assert "NO quantity" in got[wa.DIAGNOSTIC]


# --- does a space rest on material that is not established? --------------

class _Cand:
    def __init__(self, geom):
        self.geometry = geom
        self.space_geometry_id = "SG-1"


def test_a_space_whose_boundary_runs_on_an_unresolved_extension_says_so():
    wp = _WP("WB-1", 0.0, 3000.0, [(0.0, 3000.0)], [(2000.0, 3000.0)],
             ext=[{"end": "start", "length_mm": 2000.0,
                   "extension_reason": "UNRESOLVED_EXTENSION"}])
    rep = wa.classify_intervals([wp])
    room = _Cand(box(0.0, 200.0, 3000.0, 1000.0))
    got = wa.unestablished_dependency(room, rep.admissions, [wp])
    assert got["depends_on_unestablished_material"]
    assert got["unestablished_boundary_length_m"] == pytest.approx(2.0)
    assert "a hypothesis was treated as masonry" in got["why"]


def test_a_space_away_from_every_unestablished_interval_does_not():
    wp = _WP("WB-1", 0.0, 3000.0, [(0.0, 3000.0)], [(2000.0, 3000.0)],
             ext=[{"end": "start", "length_mm": 2000.0,
                   "extension_reason": "UNRESOLVED_EXTENSION"}])
    rep = wa.classify_intervals([wp])
    far = _Cand(box(50000.0, 50000.0, 53000.0, 52000.0))
    got = wa.unestablished_dependency(far, rep.admissions, [wp])
    assert not got["depends_on_unestablished_material"]


# --- junction patches -----------------------------------------------------

class _Band:
    def __init__(self, i, axis, centre, lo, hi, t=200.0, paths=("P-1",)):
        self.wall_band_id, self.axis = i, axis
        self.centreline_mm, self.start_mm, self.end_mm = centre, lo, hi
        self.wall_face_separation_mm = t
        self.source_object_ids = tuple(paths)
        self.face_a_ids, self.face_b_ids = (f"{i}-A",), (f"{i}-B",)


def _gap(w=100.0, lo=1000.0, hi=1100.0, at=2000.0, axis="H"):
    return {"axis": axis, "fixed_mm": at, "along_mm": (lo, hi),
            "passage_width_mm": w, "leak_id": "LK-1",
            "located_by": "FREE_SPACE_NECK"}


def test_a_patch_needs_two_walls_to_join():
    p = jp.propose(_gap(), [_Band("WB-1", "H", 2000.0, 0.0, 1000.0)],
                   max_wall_thickness_mm=440.0, patch_id="JP-1")
    assert p.validation_status == jp.PATCH_REFUSED
    assert "inventing the second is what this module exists to refuse" in p.why
    assert p.polygon is None


def test_two_evidence_families_validate_a_junction():
    # Distinct source paths, so the families are GEOMETRY and RASTER only.
    bands = [_Band("WB-1", "H", 2000.0, 0.0, 1000.0, paths=("P-1",)),
             _Band("WB-2", "V", 1050.0, 1500.0, 2500.0, paths=("P-2",))]
    p = jp.propose(_gap(), bands, max_wall_thickness_mm=440.0,
                   raster_support=lambda *a: 0.95, patch_id="JP-1")
    assert p.validation_status == jp.PATCH_VALIDATED
    assert p.is_material
    assert p.junction_type == jp.JUNCTION_T
    assert p.families == {"GEOMETRY", "RASTER"}
    assert p.gap_repair_class == jp.REPAIR_JUNCTION


def test_one_family_gives_a_probable_patch_that_cannot_be_material():
    # Distinct source paths and no raster: GEOMETRY alone.
    bands = [_Band("WB-1", "H", 2000.0, 0.0, 1000.0, paths=("P-1",)),
             _Band("WB-2", "V", 1050.0, 1500.0, 2500.0, paths=("P-2",))]
    p = jp.propose(_gap(), bands, max_wall_thickness_mm=440.0,
                   patch_id="JP-1")
    assert p.validation_status == jp.PATCH_PROBABLE
    assert not p.is_material
    assert "one family, not several proofs" in p.why


def test_a_patch_may_not_extend_a_wall_past_the_drawing_s_thickest():
    bands = [_Band("WB-1", "H", 2000.0, 0.0, 1000.0, paths=("P-1",)),
             _Band("WB-2", "V", 1050.0, 1500.0, 2500.0, paths=("P-2",))]
    p = jp.propose(_gap(lo=1000.0, hi=2000.0), bands,
                   max_wall_thickness_mm=440.0,
                   raster_support=lambda *a: 0.95, patch_id="JP-1")
    assert p.validation_status == jp.PATCH_REFUSED
    assert "not a junction" in p.why


def test_an_empty_raster_contradicts_a_junction_and_names_the_real_repair():
    bands = [_Band("WB-1", "H", 2000.0, 0.0, 1000.0),
             _Band("WB-2", "V", 1050.0, 1500.0, 2500.0)]
    p = jp.propose(_gap(), bands, max_wall_thickness_mm=440.0,
                   raster_support=lambda *a: 0.0, patch_id="JP-1")
    assert p.validation_status == jp.PATCH_REFUSED
    assert p.gap_repair_class == jp.REPAIR_GENUINE_OPENING
    assert "closing it would invent a wall" in p.provenance["repair_class_why"]


def test_incompatible_thickness_means_two_different_walls():
    bands = [_Band("WB-1", "H", 2000.0, 0.0, 1000.0, t=150.0),
             _Band("WB-2", "V", 1050.0, 1500.0, 2500.0, t=400.0)]
    p = jp.propose(_gap(), bands, max_wall_thickness_mm=440.0,
                   raster_support=lambda *a: 0.95, patch_id="JP-1")
    assert p.validation_status == jp.PATCH_REFUSED
    assert p.gap_repair_class == jp.REPAIR_NOT_ONE_WALL


class _Stroke:
    def __init__(self, i, axis, fixed, a, b, cls):
        self.stroke_id, self.axis, self.fixed_mm = i, axis, fixed
        self.start_mm, self.end_mm, self.stroke_class = a, b, cls


def test_a_wall_drawn_but_unpaired_sends_the_repair_to_pairing():
    # The gap is not a junction that failed to close; a wall IS drawn there
    # and never became a band. A patch would paper over an extraction bug.
    from engine.unpaired_strokes import CONFIRMED_SINGLE_LINE_WALL
    p = jp.propose(
        _gap(), [_Band("WB-1", "H", 2000.0, 0.0, 1000.0)],
        max_wall_thickness_mm=440.0, raster_support=lambda *a: 0.9,
        strokes=[_Stroke("VS-1", "H", 2010.0, 1000.0, 1200.0,
                         CONFIRMED_SINGLE_LINE_WALL)],
        patch_id="JP-1")
    assert p.gap_repair_class == jp.REPAIR_PAIRING
    assert p.strokes_at_the_gap == ("VS-1",)
    assert "FACE PAIRING" in p.why


def test_the_record_names_what_a_patch_is_never_produced_by():
    p = jp.propose(_gap(), [], max_wall_thickness_mm=440.0, patch_id="JP-1")
    got = p.record()["not_produced_by"]
    for banned in ("snap tolerance", "buffer", "morphological closing",
                   "generic gap filling"):
        assert banned in got


# --- the counterfactual ---------------------------------------------------

def test_a_repair_that_changes_nothing_is_reported_as_not_causal():
    a = cf.Arm("A", single_room=4, largest_blob_labels=32)
    b = cf.Arm("B", single_room=4, largest_blob_labels=32)
    got = cf.compare(a, b, repairs=["JP-0003"])
    assert got["verdict"] == cf.NOT_CAUSAL
    assert "it is not these gaps" in got["why"]
    assert "not evidence that it is" in got["why"]


def test_a_repair_that_splits_the_blob_is_reported_as_dominant():
    a = cf.Arm("A", single_room=4, largest_blob_labels=32)
    b = cf.Arm("B", single_room=8, largest_blob_labels=20)
    got = cf.compare(a, b, repairs=["JP-1", "JP-2"])
    assert got["verdict"] == cf.DOMINANT
    assert got["delta"]["single_room_candidates"] == 4


def test_a_small_real_effect_is_contributory_not_dominant():
    a = cf.Arm("A", single_room=4, largest_blob_labels=32)
    b = cf.Arm("B", single_room=5, largest_blob_labels=31)
    got = cf.compare(a, b, repairs=["JP-1"])
    assert got["verdict"] == cf.CONTRIBUTORY
    assert "not the dominant cause" in got["why"]


def test_the_experiment_states_what_it_holds_constant():
    got = cf.compare(cf.Arm("A"), cf.Arm("B"))
    assert "and nothing else" in got["what_changed_between_the_arms"]
    assert "SPACE PARTITIONING" in got["what_is_not_compared"]
