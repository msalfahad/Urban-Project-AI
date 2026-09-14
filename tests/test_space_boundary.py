"""E31D — a virtual boundary closes a room and is never wall material."""

from __future__ import annotations

import pytest

from engine.connectivity import EndCap
from engine.space_boundary import (GAP_DOOR, GAP_MISSING_EXTRACTION,
                                   GAP_OPEN_PLAN, MIN_FAMILIES_FOR_VALIDATED,
                                   OPEN_TRANSITION, PHYSICAL_WALL,
                                   PORTAL_CANDIDATE, PORTAL_PROBABLE,
                                   PORTAL_UNRESOLVED, VIRTUAL_PORTAL,
                                   BoundaryInterval, SpaceBoundaryError,
                                   build_space_boundary, classify_gap,
                                   material_length_m, space_closes, summary)


def cap(cid, at):
    return EndCap(cid, "VS-1", "V", 200.0, (0.0, 200.0), at, ("F1", "F2"),
                  200.0, 1.14, "test")


# --- the hard invariant -------------------------------------------------------

def test_a_virtual_boundary_carrying_material_is_refused_by_the_type():
    """It contributes zero blockwork, zero plaster and zero physical wall
    length, and a quantity engine reading material_length_mm must never be
    handed anything else."""
    with pytest.raises(SpaceBoundaryError, match="ZERO wall material"):
        BoundaryInterval("BI-1", "BTH-05", "south", "H", 0.0, 0.0, 1054.0,
                         VIRTUAL_PORTAL, 1054.0)


def test_a_physical_wall_with_no_material_is_refused_too():
    """A wall that is not there is not a wall."""
    with pytest.raises(SpaceBoundaryError, match="not a wall"):
        BoundaryInterval("BI-1", "X", "north", "H", 0.0, 0.0, 1000.0,
                         PHYSICAL_WALL, 0.0)


def test_material_length_ignores_every_virtual_interval():
    ivs = [BoundaryInterval("BI-1", "X", "north", "H", 0.0, 0.0, 3000.0,
                            PHYSICAL_WALL, 3000.0),
           BoundaryInterval("BI-2", "X", "south", "H", 2000.0, 0.0, 1054.0,
                            VIRTUAL_PORTAL, 0.0)]
    assert material_length_m(ivs) == 3.0


def test_the_virtual_span_is_reported_but_is_never_a_quantity():
    ivs = [BoundaryInterval("BI-2", "X", "south", "H", 0.0, 0.0, 1054.0,
                            VIRTUAL_PORTAL, 0.0)]
    out = summary(ivs, [])
    assert out["virtual_length_m"] == pytest.approx(1.054, abs=0.01)
    assert out["virtual_material_length_m"] == 0.0
    assert "never a quantity" in out["note"]


# --- portals ------------------------------------------------------------------

def test_gap_size_alone_is_never_enough_to_call_a_door():
    """It would classify a missing wall as a doorway and a doorway as a
    missing wall with equal confidence."""
    p = classify_gap("X", "south", "H", 0.0, 0.0, 1000.0,
                     bands_face_each_other=False, other_sides_complete=False)
    assert p.status == PORTAL_CANDIDATE
    assert not p.may_close_a_space


def test_two_independent_families_make_a_portal_probable():
    p = classify_gap("BTH-05", "south", "H", 0.0, 0.0, 1054.0,
                     bands_face_each_other=True, other_sides_complete=True)
    assert p.status == PORTAL_PROBABLE
    assert p.gap_class == GAP_DOOR
    assert len(p.families) >= MIN_FAMILIES_FOR_VALIDATED
    assert p.may_close_a_space


def test_a_gap_far_wider_than_a_door_is_an_open_plan_transition():
    p = classify_gap("OPEN-01", "north", "H", 0.0, 0.0, 6053.0,
                     bands_face_each_other=True, other_sides_complete=True)
    assert p.gap_class == GAP_OPEN_PLAN
    assert p.status == PORTAL_UNRESOLVED
    assert not p.may_close_a_space


def test_a_gap_with_no_portal_evidence_reads_as_missing_extraction():
    p = classify_gap("STR-01", "east", "V", 0.0, 0.0, 2606.0,
                     bands_face_each_other=False, other_sides_complete=False)
    assert p.gap_class in (GAP_MISSING_EXTRACTION, GAP_OPEN_PLAN)
    assert not p.may_close_a_space


def test_jamb_end_caps_are_a_geometry_family_not_a_verdict():
    p = classify_gap("X", "south", "H", 0.0, 0.0, 900.0,
                     caps=[cap("EC-1", 0.0), cap("EC-2", 900.0)],
                     bands_face_each_other=False, other_sides_complete=False)
    assert "END_CAPS_AT_BOTH_JAMBS" in p.evidence


# --- the two graphs -----------------------------------------------------------

def test_a_room_closes_across_a_probable_doorway_without_inventing_wall():
    """Three sides of wall and one 1054 mm door. Closing it with a virtual
    boundary is MORE correct than inventing wall material across the door."""
    sides = {
        "north": {"axis": "H", "fixed": 0.0, "lo": 0.0, "hi": 2336.0,
                  "covered": [(0.0, 2336.0)], "gaps": [], "band_ids": ()},
        "south": {"axis": "H", "fixed": 1460.0, "lo": 0.0, "hi": 2336.0,
                  "covered": [(0.0, 1282.0)], "gaps": [(1282.0, 2336.0)],
                  "band_ids": ()},
        "west": {"axis": "V", "fixed": 0.0, "lo": 0.0, "hi": 1460.0,
                 "covered": [(0.0, 1460.0)], "gaps": [], "band_ids": ()},
        "east": {"axis": "V", "fixed": 2336.0, "lo": 0.0, "hi": 1460.0,
                 "covered": [(0.0, 1460.0)], "gaps": [], "band_ids": ()},
    }
    portal = classify_gap("BTH-05", "south", "H", 1460.0, 1282.0, 2336.0,
                          bands_face_each_other=True,
                          other_sides_complete=True)
    ivs = build_space_boundary("BTH-05", sides, [portal])
    assert space_closes(ivs)
    virtual = [i for i in ivs if i.is_virtual]
    assert len(virtual) == 1
    assert virtual[0].material_length_mm == 0.0
    # the material wall graph stays open there: three sides of material only
    assert material_length_m(ivs) == pytest.approx(
        (2336 + 1282 + 1460 + 1460) / 1000)


def test_an_unexplained_gap_leaves_the_boundary_open_rather_than_closing_it():
    """Closing it would be inventing either a wall or a door."""
    sides = {"east": {"axis": "V", "fixed": 0.0, "lo": 0.0, "hi": 2606.0,
                      "covered": [], "gaps": [(0.0, 2606.0)],
                      "band_ids": ()}}
    ivs = build_space_boundary("STR-01", sides, [])
    assert not space_closes(ivs)
    assert ivs[0].boundary_type == OPEN_TRANSITION
    assert ivs[0].material_length_mm == 0.0


def test_an_open_plan_space_is_not_forced_closed():
    """OPEN-01 may remain one physical open space. Inventing walls between
    saloon, dining and circulation to produce more faces would be fiction."""
    sides = {"north": {"axis": "H", "fixed": 0.0, "lo": 0.0, "hi": 9180.0,
                       "covered": [(0.0, 1527.0)],
                       "gaps": [(1527.0, 9180.0)], "band_ids": ()}}
    portal = classify_gap("OPEN-01", "north", "H", 0.0, 1527.0, 9180.0,
                          bands_face_each_other=True,
                          other_sides_complete=False)
    ivs = build_space_boundary("OPEN-01", sides, [portal])
    assert not space_closes(ivs)
    assert all(i.material_length_mm == 0.0 for i in ivs if i.is_virtual)
