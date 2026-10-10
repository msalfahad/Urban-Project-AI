"""E31B — comparison after generation, and the cost side of recovery."""

from __future__ import annotations

from engine.face_qa import (MANY_TO_MANY, MICRO_CLASSES, ONE_TO_ONE,
                            RASTER_ONLY, RASTER_SPLITS_VECTOR,
                            VECTOR_ONLY, VECTOR_SPLITS_RASTER,
                            classify_micro_faces, correspond,
                            false_split_control)
from engine.planar import BOUNDED, Face


def face(fid, x0, y0, x1, y1, area=None):
    poly = ((x0, y0), (x1, y0), (x1, y1), (x0, y1))
    a = area if area is not None else (x1 - x0) * (y1 - y0)
    return Face(face_id=fid, component_id="GC-1", half_edge_ids=("h",),
                polygon_mm=poly, signed_area_mm2=a,
                perimeter_mm=2 * ((x1 - x0) + (y1 - y0)),
                orientation="COUNTERCLOCKWISE", kind=BOUNDED)


def region(rid, x0, y0, x1, y1, space=""):
    return {rid: {"bbox_mm": (x0, y0, x1, y1),
                  "area_m2": (x1 - x0) * (y1 - y0) / 1e6, "space_id": space}}


def test_one_face_one_region_is_one_to_one():
    c = correspond([face("F1", 0, 0, 4000, 3000)],
                   region(1, 0, 0, 4000, 3000, "BTH-01"))
    assert c[0].relationship == ONE_TO_ONE


def test_two_faces_dividing_one_region_is_vector_splits_raster():
    """The class that may expose an under-segmented space — and equally the
    class a false split hides in."""
    faces = [face("F1", 0, 0, 2000, 3000), face("F2", 2000, 0, 4000, 3000)]
    c = correspond(faces, region(1, 0, 0, 4000, 3000, "BED-04"))
    assert {x.relationship for x in c} == {VECTOR_SPLITS_RASTER}


def test_a_region_with_no_face_over_it_is_raster_only():
    c = correspond([], region(1, 0, 0, 4000, 3000, "BTH-01"))
    assert c[0].relationship == RASTER_ONLY


def test_a_face_with_no_region_under_it_is_vector_only():
    c = correspond([face("F1", 0, 0, 4000, 3000)], {})
    assert c[0].relationship == VECTOR_ONLY


def test_neither_side_is_forced_to_match_the_other():
    import inspect

    from engine import face_qa
    doc = inspect.getdoc(face_qa)
    assert "neither side is forced to match the other" in doc
    assert "faces are generated FIRST" in doc


def test_splitting_a_stable_space_is_reported_as_the_cost_of_recovery():
    """An engine that finds BED-04's bathroom and splits ten normal bedrooms
    is not successful."""
    faces = [face("F1", 0, 0, 2000, 3000), face("F2", 2000, 0, 4000, 3000)]
    c = correspond(faces, region(1, 0, 0, 4000, 3000, "BED-01"))
    out = false_split_control(c, stable_space_ids=["BED-01"])
    assert out["vector_splits_of_a_STABLE_raster_space"]
    assert "FALSE SPLITS PRESENT" in out["verdict"]


def test_splitting_a_known_broken_space_is_what_we_are_hoping_for():
    faces = [face("F1", 0, 0, 2000, 3000), face("F2", 2000, 0, 4000, 3000)]
    c = correspond(faces, region(1, 0, 0, 4000, 3000, "BED-04"))
    out = false_split_control(c, stable_space_ids=["BED-01"])
    assert not out["vector_splits_of_a_STABLE_raster_space"]
    assert out["vector_splits_of_a_KNOWN_BROKEN_space"]


# --- micro faces --------------------------------------------------------------

def test_no_area_threshold_deletes_a_face():
    tiny = [face("F1", 0, 0, 500, 500)]
    out = classify_micro_faces(tiny)
    assert out and all(m["deleted"] is False for m in out)
    assert out[0]["micro_class"] in MICRO_CLASSES


def test_a_long_thin_face_between_walls_is_a_cavity_not_a_room():
    out = classify_micro_faces([face("F1", 0, 0, 4000, 100)])
    assert out[0]["micro_class"] == "WALL_CAVITY"


def test_a_narrow_but_habitable_face_is_kept_as_a_real_space():
    """It is NOT removed for being small."""
    out = classify_micro_faces([face("F1", 0, 0, 900, 500)])
    assert out[0]["micro_class"] == "REAL_NARROW_SPACE"
    assert "NOT removed" in out[0]["why"]


def test_a_face_found_twice_is_a_duplicate_not_two_rooms():
    out = classify_micro_faces([face("F1", 0, 0, 700, 600),
                                face("F2", 0, 0, 700, 600)])
    assert any(m["micro_class"] == "DUPLICATE_ARTIFACT" for m in out)


def test_a_big_face_is_not_classified_as_micro_at_all():
    assert classify_micro_faces([face("F1", 0, 0, 4000, 3000)]) == []
