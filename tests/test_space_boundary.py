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
    from engine.lengths import LengthSet
    with pytest.raises(SpaceBoundaryError, match="ZERO actual wall material"):
        BoundaryInterval("BI-1", "BTH-05", "south", "H", 0.0, 0.0, 1054.0,
                         VIRTUAL_PORTAL,
                         lengths=LengthSet(material_present_mm=1054.0),
                         closure_basis="CLEAR_INTERNAL_FINISH_FACE")


def test_a_physical_wall_with_no_material_is_refused_too():
    """A wall that is not there is not a wall."""
    from engine.lengths import LengthSet
    with pytest.raises(SpaceBoundaryError, match="not a wall"):
        BoundaryInterval("BI-1", "X", "north", "H", 0.0, 0.0, 1000.0,
                         PHYSICAL_WALL,
                         lengths=LengthSet(material_present_mm=0.0))


def test_material_length_ignores_every_virtual_interval():
    from engine.lengths import LengthSet
    ivs = [BoundaryInterval("BI-1", "X", "north", "H", 0.0, 0.0, 3000.0,
                            PHYSICAL_WALL,
                            lengths=LengthSet(material_present_mm=3000.0)),
           BoundaryInterval("BI-2", "X", "south", "H", 2000.0, 0.0, 1054.0,
                            VIRTUAL_PORTAL,
                            lengths=LengthSet(material_present_mm=0.0,
                                              host_wall_gross_mm=1054.0),
                            closure_basis="CLEAR_INTERNAL_FINISH_FACE")]
    assert material_length_m(ivs) == 3.0


def test_the_virtual_span_is_reported_but_is_never_a_quantity():
    from engine.lengths import LengthSet
    ivs = [BoundaryInterval("BI-2", "X", "south", "H", 0.0, 0.0, 1054.0,
                            VIRTUAL_PORTAL,
                            lengths=LengthSet(space_boundary_mm=1054.0,
                                              host_wall_gross_mm=1054.0,
                                              material_present_mm=0.0,
                                              opening_mm=1054.0),
                            closure_basis="CLEAR_INTERNAL_FINISH_FACE")]
    out = summary(ivs, [])
    assert out["virtual_span_m"] == pytest.approx(1.054, abs=0.01)
    assert out["virtual_material_length_m"] == 0.0
    assert out["material_present_length_m"] == 0.0
    # and the gross host line still carries it
    assert out["host_wall_gross_length_m"] == pytest.approx(1.054, abs=0.01)


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


def test_a_gap_far_wider_than_a_door_gets_no_support_from_its_span():
    """WIDTH IS EVIDENCE, NOT A PHYSICAL RULE — large openings exist. A 6 m gap
    simply gets no help from the span family; the other families decide."""
    p = classify_gap("OPEN-01", "north", "H", 0.0, 0.0, 6053.0,
                     bands_face_each_other=True, other_sides_complete=True)
    assert "SPAN_IN_THE_DOOR_RANGE" not in p.evidence
    assert "width is evidence only" in p.why


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


# --- the length ontology (E51) ------------------------------------------------

def test_a_host_wall_opening_carries_gross_length_but_no_material():
    """The correction: a doorway belongs to the gross host-wall line even
    though no wall material stands in it."""
    from engine.lengths import LengthSet
    from engine.space_boundary import (CLEAR_INTERNAL_FINISH_FACE,
                                       HOST_WALL_OPENING, BoundaryInterval)
    i = BoundaryInterval(
        "BI-1", "BTH-05", "south", "H", 0.0, 0.0, 1054.0, HOST_WALL_OPENING,
        lengths=LengthSet(space_boundary_mm=1054.0, host_wall_gross_mm=1054.0,
                          material_present_mm=0.0, opening_mm=1054.0),
        closure_basis=CLEAR_INTERNAL_FINISH_FACE)
    assert i.lengths.material_present_mm == 0.0
    assert i.lengths.host_wall_gross_mm == 1054.0


def test_an_open_plan_boundary_has_no_host_wall_either():
    """There is no wall here to be gross about, and a semantic transition must
    never become one."""
    from engine.lengths import LengthSet
    from engine.space_boundary import (OPEN_PLAN_VIRTUAL, BoundaryInterval,
                                       SpaceBoundaryError)
    with pytest.raises(SpaceBoundaryError, match="no wall here to be gross"):
        BoundaryInterval("BI-1", "OPEN-01", "north", "H", 0.0, 0.0, 6000.0,
                         OPEN_PLAN_VIRTUAL,
                         lengths=LengthSet(host_wall_gross_mm=6000.0,
                                           material_present_mm=0.0))


def test_a_closure_without_a_stated_basis_is_refused():
    """Room area depends on where the closure line runs, so it is required."""
    from engine.lengths import LengthSet
    from engine.space_boundary import (HOST_WALL_OPENING, BoundaryInterval,
                                       SpaceBoundaryError)
    with pytest.raises(SpaceBoundaryError, match="where the closure line runs"):
        BoundaryInterval("BI-1", "X", "south", "H", 0.0, 0.0, 900.0,
                         HOST_WALL_OPENING,
                         lengths=LengthSet(space_boundary_mm=900.0,
                                           host_wall_gross_mm=900.0,
                                           material_present_mm=0.0,
                                           opening_mm=900.0))


def test_the_three_virtual_classes_are_not_interchangeable():
    from engine.space_boundary import (HOST_WALL_OPENING, OPEN_PLAN_VIRTUAL,
                                       OTHER_VIRTUAL, VIRTUAL_TYPES)
    assert len(set(VIRTUAL_TYPES)) == 3
    assert HOST_WALL_OPENING != OPEN_PLAN_VIRTUAL != OTHER_VIRTUAL


def test_gross_reconciles_as_material_plus_openings():
    """HOST_WALL_GROSS = MATERIAL_PRESENT + supported HOST-WALL OPENINGS.
    BTH-05: 6.538 + 1.054 = 7.592."""
    from engine.space_boundary import reconcile
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
    p = classify_gap("BTH-05", "south", "H", 1460.0, 1282.0, 2336.0,
                     bands_face_each_other=True, other_sides_complete=True)
    r = reconcile(build_space_boundary("BTH-05", sides, [p]))
    assert r["identity_holds"]
    assert r["host_wall_gross_length_m"] == pytest.approx(7.592, abs=0.001)
    assert r["material_present_length_m"] == pytest.approx(6.538, abs=0.001)
    assert r["opening_length_m"] == pytest.approx(1.054, abs=0.001)


# --- the evidence combination matrix (§6) -------------------------------------

def test_geometry_and_topology_are_correlated_and_cap_at_probable():
    """The same gap geometry produces both "there is a gap" and "closing it
    closes the room". One observation seen twice is one observation."""
    from engine.space_boundary import (FAMILY_GEOMETRY, FAMILY_SYMBOL,
                                       FAMILY_TOPOLOGY, PORTAL_PROBABLE,
                                       PORTAL_VALIDATED, status_for)
    assert status_for({FAMILY_GEOMETRY, FAMILY_TOPOLOGY})[0] == PORTAL_PROBABLE
    assert status_for({FAMILY_GEOMETRY, FAMILY_SYMBOL})[0] == PORTAL_VALIDATED


def test_no_single_family_ever_carries_a_portal():
    from engine.space_boundary import (FAMILY_GEOMETRY, FAMILY_SEMANTIC,
                                       FAMILY_TOPOLOGY, PORTAL_CANDIDATE,
                                       status_for)
    for fam in (FAMILY_GEOMETRY, FAMILY_TOPOLOGY, FAMILY_SEMANTIC):
        assert status_for({fam})[0] == PORTAL_CANDIDATE


def test_width_is_evidence_and_not_a_physical_rule():
    """Large openings exist. A wide gap does not become an open-plan
    transition by arithmetic."""
    import inspect

    from engine import space_boundary
    src = inspect.getsource(space_boundary.classify_gap)
    assert "WIDTH IS EVIDENCE, NOT A PHYSICAL RULE" in src
    assert "Large openings exist" in src
