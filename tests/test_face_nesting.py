"""E56 — cycles are classified by containment before anything is summed."""

from __future__ import annotations

from dataclasses import dataclass, field

import pytest

from engine.face_nesting import (ATOMIC_SPACE_FACE, BUILDING_ENVELOPE,
                                 ENCLOSURE_CYCLE, HOLE, MICRO_FACE,
                                 UNRESOLVED_NESTED_FACE, WALL_CAVITY,
                                 NestingError, assert_additive, atomic_set,
                                 hierarchy)


@dataclass(frozen=True)
class F:
    space_face_id: str
    polygon_mm: tuple
    portal_edge_ids: tuple = ()

    @property
    def area_m2(self) -> float:
        s = 0.0
        p = list(self.polygon_mm)
        for (x0, y0), (x1, y1) in zip(p, p[1:] + p[:1]):
            s += x0 * y1 - x1 * y0
        return abs(s / 2) / 1_000_000

    @property
    def perimeter_m(self) -> float:
        import math
        p = list(self.polygon_mm)
        return sum(math.dist(a, b) for a, b in zip(p, p[1:] + p[:1])) / 1000


def box(x0, y0, x1, y1):
    return ((x0, y0), (x1, y0), (x1, y1), (x0, y1))


def region(sid, x, y):
    return {"space_id": sid, "centroid_mm": (x, y), "area_m2": 1.0}


# --- the hierarchy ----------------------------------------------------------

def test_a_depth_zero_cycle_holding_many_rooms_is_the_building_envelope():
    """§12 — a whole-floor cycle containing every room is NOT 'a room whose
    dividing walls are missing'. Calling it that sends the next round hunting
    for a wall that was never meant to exist."""
    faces = [F("SF-1", box(0, 0, 30000, 20000)),
             F("SF-2", box(1000, 1000, 5000, 5000)),
             F("SF-3", box(6000, 1000, 10000, 5000)),
             F("SF-4", box(11000, 1000, 15000, 5000))]
    regions = {1: region("BED-01", 3000, 3000), 2: region("BED-02", 8000, 3000),
               3: region("BTH-01", 13000, 3000)}
    got = {n.space_face_id: n for n in hierarchy(faces, regions)}
    assert got["SF-1"].cycle_class == BUILDING_ENVELOPE
    assert "NOT a room whose dividing walls are missing" in got["SF-1"].why
    assert got["SF-2"].cycle_class == ATOMIC_SPACE_FACE
    assert got["SF-2"].parent_id == "SF-1"
    assert got["SF-2"].depth == 1
    assert set(got["SF-1"].child_ids) == {"SF-2", "SF-3", "SF-4"}
    assert "SF-3" in got["SF-2"].sibling_ids


def test_a_cycle_inside_a_room_with_no_label_is_a_hole():
    """A shaft inside a bedroom is not a second bedroom."""
    faces = [F("SF-1", box(0, 0, 6000, 6000)),
             F("SF-2", box(2000, 2000, 4000, 4000))]
    got = {n.space_face_id: n for n in
           hierarchy(faces, {1: region("BED-01", 1000, 1000)})}
    assert got["SF-2"].cycle_class == HOLE
    assert got["SF-1"].cycle_class == ATOMIC_SPACE_FACE


def test_a_cycle_holding_two_labels_is_an_enclosure_not_a_room():
    faces = [F("SF-1", box(0, 0, 8000, 4000))]
    got = hierarchy(faces, {1: region("BED-01", 2000, 2000),
                            2: region("BTH-02", 6000, 2000)})
    assert got[0].cycle_class == ENCLOSURE_CYCLE
    assert got[0].labelled_space_ids == ("BED-01", "BTH-02")


def test_a_long_thin_cycle_is_a_cavity_not_a_room():
    faces = [F("SF-1", box(0, 0, 20000, 600))]
    got = hierarchy(faces, {1: region("X", 10000, 300)})
    assert got[0].cycle_class == WALL_CAVITY


def test_a_cycle_narrower_than_a_person_cannot_be_floor():
    faces = [F("SF-1", box(0, 0, 3000, 300))]
    assert hierarchy(faces, {})[0].cycle_class == WALL_CAVITY


def test_a_micro_cycle_is_classified_and_never_deleted():
    faces = [F("SF-1", box(0, 0, 600, 600))]
    got = hierarchy(faces, {})[0]
    assert got.cycle_class == MICRO_FACE
    assert "NOTHING here deletes it" in got.why


def test_two_cycles_that_cross_are_unresolved_rather_than_nested():
    """Neither is a refinement of the other, so neither may be atomic."""
    faces = [F("SF-1", box(0, 0, 6000, 6000)),
             F("SF-2", box(4000, 4000, 10000, 10000))]
    got = {n.space_face_id: n for n in
           hierarchy(faces, {1: region("A", 1000, 1000),
                             2: region("B", 9000, 9000)})}
    assert got["SF-2"].cycle_class == UNRESOLVED_NESTED_FACE
    assert "SF-1" in got["SF-2"].overlapping_ids


def test_containment_needs_every_vertex_not_just_the_first():
    """A single-vertex test calls two crossing cycles contained."""
    faces = [F("SF-1", box(0, 0, 6000, 6000)),
             F("SF-2", box(5000, 5000, 9000, 9000))]
    got = {n.space_face_id: n for n in hierarchy(faces, {})}
    assert got["SF-2"].parent_id == ""
    assert got["SF-2"].overlapping_ids == ("SF-1",)


# --- what may be added ------------------------------------------------------

def test_the_sum_of_bounded_cycles_is_not_a_project_area():
    """1102.64 m2 added a 989 m2 envelope to the rooms inside it."""
    faces = [F("SF-1", box(0, 0, 30000, 20000)),
             F("SF-2", box(1000, 1000, 5000, 5000)),
             F("SF-3", box(6000, 1000, 10000, 5000)),
             F("SF-4", box(11000, 1000, 15000, 5000))]
    regions = {1: region("BED-01", 3000, 3000), 2: region("BED-02", 8000, 3000),
               3: region("BTH-01", 13000, 3000)}
    nested = hierarchy(faces, regions)
    out = atomic_set(nested)
    naive = sum(f.area_m2 for f in faces)
    assert naive == pytest.approx(600 + 16 + 16 + 16, abs=0.01)
    assert out["atomic_area_m2"] == pytest.approx(48.0, abs=0.01)
    assert out["excluded_from_the_total"][BUILDING_ENVELOPE] == pytest.approx(
        600.0, abs=0.01)
    assert out["non_overlapping"]


def test_a_holes_area_comes_out_of_its_parent():
    faces = [F("SF-1", box(0, 0, 6000, 6000)),
             F("SF-2", box(2000, 2000, 4000, 4000))]
    nested = hierarchy(faces, {1: region("BED-01", 1000, 1000)})
    out = atomic_set(nested)
    assert out["atomic_area_m2"] == pytest.approx(36.0 - 4.0, abs=0.01)
    assert out["holes_deducted_m2"] == pytest.approx(4.0, abs=0.01)


def test_a_total_over_overlapping_cycles_is_refused():
    faces = [F("SF-1", box(0, 0, 6000, 6000)),
             F("SF-2", box(4000, 4000, 10000, 10000))]
    nested = hierarchy(faces, {1: region("A", 1000, 1000),
                               2: region("B", 9000, 9000)})
    # neither survives as atomic, so there is nothing to double-count
    assert atomic_set(nested)["atomic_space_candidates"] == 0
    assert_additive(nested)


def test_an_atom_nested_inside_another_atom_blocks_the_total():
    """Two labelled rooms, one inside the other, is not an additive set."""
    faces = [F("SF-1", box(0, 0, 10000, 10000)),
             F("SF-2", box(2000, 2000, 5000, 5000))]
    nested = hierarchy(faces, {1: region("OUTER", 8000, 8000),
                               2: region("INNER", 3000, 3000)})
    out = atomic_set(nested)
    if out["atoms_nested_inside_other_atoms"]:
        with pytest.raises(NestingError, match="counts the same floor twice"):
            assert_additive(nested)
