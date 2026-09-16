"""Round 4: drawing regions, opening evidence, and the gap that stays a gap.

Round 3 measured two spaces on P7757 and released none, and it traced the
cause to a wall that stops three and a half metres short of the corner.
The fix for that is an opening — and the wrong fix for it is bridging every
hole in every wall.

So most of what these tests hold is a REFUSAL:

    a gap with no reveal and no symbol closes nothing
    a window is never a room-to-room passage
    a doorless opening settles neither one space nor two
    an arc that pierces no wall is not a door
    a block called D120 is not a portal because of its name
    nothing relates across a drawing region

and one permission, which is what the round was for: an opening backed by
evidence may close a room boundary carrying ZERO material across it.
"""

from __future__ import annotations

import math

import pytest

from engine import cad_adapter as ad
from engine import cad_measure as cm
from engine import cad_openings as co
from engine import cad_profile as cp
from engine import drawing_region as dr
from engine import portal_match as pm
from engine import room_partition_graph as rpg
from engine import round4_fixtures as fx
from engine import round4_selftest as r4
from engine import space_topologies as topo
from engine.cad_fixtures import Builder


def _norm(b):
    return ad.normalize(b.build(), source_file="T", source_hash="T")


def _measured(b):
    nd = _norm(b)
    return nd, cm.measure(nd, cp.build(nd))


def _two_rooms(*, jambs=True, door=True, width=900.0, rotation=0.0,
               scale=1.0, nested=False):
    b = Builder()
    fx._ring(b, 0, 0, 10000, 4000)
    fx._partition_v(b, 4900, 0, 4000, gaps=[(1500, 1500 + width)],
                    jambs=jambs)
    if door:
        fx._door(b, "D90", 4900, 1500, width, rotation=rotation,
                 scale=scale, nested=nested)
    fx._stamp(b, "S1", ["SALOON"], 2400, 2000)
    fx._stamp(b, "S2", ["KITCHEN"], 7500, 2000)
    return b


# --------------------------------------------------------- drawing regions

def test_two_drawings_far_apart_are_two_regions():
    b = Builder()
    fx._ring(b, 0, 0, 8000, 5000)
    fx._ring(b, 300000, 0, 8000 + 300000, 5000)
    rep = dr.isolate(_norm(b))
    assert rep.counts()["drawing_regions"] == 2
    assert rep.chosen_distance_mm in dr.cad_regions.LADDER_MM


def test_a_plot_and_the_building_inside_it_are_one_drawing():
    """Nesting is the evidence. A site line must stay in the building's
    frame, or round 3's site test has nothing to remove."""
    b = Builder()
    fx._ring(b, 0, 0, 60000, 40000, layer="PLOT")
    fx._ring(b, 20000, 14000, 40000, 26000)
    rep = dr.isolate(_norm(b))
    assert rep.counts()["drawing_regions"] == 1
    assert "nested" in " ".join(rep.notes.values()) or rep.notes["nesting"]


def test_nothing_relates_across_a_region():
    nd, rep = _measured(_u_builder())
    assert rep.regions.counts()["drawing_regions"] >= 2
    for row in rep.rows:
        for seg in row.boundary_roles:
            pid = seg["cad_provenance"]
            if pid.startswith("PORTAL-"):
                continue
            owner = rep.regions.of_object(pid)
            assert owner is None or owner.region_id == row.region_id


def _u_builder():
    b = Builder()
    for k, dx in enumerate((0.0, 200000.0)):
        fx._ring(b, dx, 0, dx + 10000, 4000)
        fx._partition_v(b, dx + 4900, 0, 4000, gaps=[(1500, 2400)])
        fx._door(b, f"D90_{k}", dx + 4900, 1500, 900)
        fx._stamp(b, f"S{k}", ["SALOON"], dx + 2400, 2000)
    return b


def test_a_region_never_claims_to_be_a_floor():
    rep = dr.isolate(_norm(_two_rooms()))
    for r in rep.regions:
        assert r.floor_name == dr.FLOOR_UNKNOWN
        assert r.record()["what_this_is_not"].startswith("a floor")


# ------------------------------------------------------- the grade ladder

def test_a_wall_gap_alone_closes_nothing():
    """The invariant of §5, stated as a test rather than a comment."""
    nd, rep = _measured(_two_rooms(jambs=False, door=False))
    assert co.UNRESOLVED_WALL_GAP in rep.openings.by_class()
    assert rep.openings.counts()["may_close_a_boundary"] == 0
    assert rep.counts()["release_eligible"] == 0


def test_a_reveal_without_a_door_may_close_a_polygon_but_not_two_rooms():
    nd, rep = _measured(_two_rooms(door=False))
    o = rep.openings.openings[0]
    assert o.opening_class == co.DOORLESS_ARCHWAY
    assert o.grade == co.GRADE_C
    assert o.may_close_boundary
    assert not o.may_partition_rooms
    assert rep.counts()["release_eligible"] == 0


def test_a_door_assembly_closes_both_rooms():
    nd, rep = _measured(_two_rooms())
    o = rep.openings.openings[0]
    assert o.opening_class == co.DOOR_WITH_LEAF
    assert o.grade == co.GRADE_A
    assert o.may_partition_rooms
    assert rep.counts()["release_eligible"] == 2
    rel = {r["ROOM_PARTITION_RELATION"] for g in rep.graphs
           for r in g.relations}
    assert rel == {topo.REL_TWO_SPACES}


@pytest.mark.parametrize("width", [800.0, 1200.0, 2400.0])
def test_the_class_does_not_follow_the_width(width):
    """A 2.4 m door and an 800 mm door are both DOOR_WITH_LEAF, and the
    same holes without a leaf are both something else."""
    _nd, with_door = _measured(_two_rooms(width=width))
    _nd2, without = _measured(_two_rooms(width=width, door=False))
    assert with_door.openings.openings[0].opening_class == co.DOOR_WITH_LEAF
    assert without.openings.openings[0].opening_class == co.DOORLESS_ARCHWAY


def test_no_table_of_plausible_opening_widths_exists():
    params = co.frozen_parameters()
    assert not [k for k in params if "WIDTH" in k]
    assert "NO table of plausible door widths" in \
        params["why"]["no_width_band"]


def test_a_block_name_cannot_create_a_portal():
    """`if block starts with D: portal = True` is the forbidden rule."""
    b = Builder()
    fx._ring(b, 0, 0, 10000, 4000)
    fx._partition_v(b, 4900, 0, 4000, gaps=[(1500, 2400)], jambs=False)
    # A block named like a door, containing geometry that pierces nothing.
    h = b.line(1000.0, 3000.0, 1900.0, 3000.0, "D")
    b.block("D090", [h])
    b.insert("D090", 0.0, 0.0)
    fx._stamp(b, "S1", ["SALOON"], 2400, 2000)
    _nd, rep = _measured(b)
    assert rep.openings.counts()["door_candidates"] == 0
    assert rep.openings.counts()["may_close_a_boundary"] == 0


# ------------------------------------------------------------ the widths

def test_the_three_width_observations_stay_apart():
    nd, rep = _measured(_two_rooms())
    w = rep.openings.openings[0].widths.record()
    assert w["GEOMETRIC_OPENING_WIDTH_MM"] == 900.0
    assert w["BLOCK_NAME_WIDTH_OBSERVATION"]["raw"] == "90"
    assert w["BLOCK_NAME_WIDTH_OBSERVATION"][
        "which_reading_agrees_with_geometry"] == "AS_CENTIMETRES"
    assert w["BLOCK_NAME_WIDTH_OBSERVATION"]["authority"].startswith("NONE")
    assert "never averaged" in w["never"]


def test_a_scaled_insert_measures_what_it_became():
    b = Builder()
    fx._ring(b, 0, 0, 8000, 8000)
    fx._partition_h(b, 3900, 0, 8000, gaps=[(3000, 4080)])
    fx._door(b, "D90", 3000, 3900, 900, rotation=-math.pi / 2, scale=1.2)
    fx._stamp(b, "S1", ["BEDROOM"], 4000, 1800)
    fx._stamp(b, "S2", ["SALOON"], 4000, 6000)
    _nd, rep = _measured(b)
    o = next(o for o in rep.openings.openings if o.may_close_boundary)
    assert round(o.opening_length_mm, 1) == 1080.0
    assert o.widths.record()["BLOCK_NAME_WIDTH_OBSERVATION"][
        "which_reading_agrees_with_geometry"] == "NEITHER_READING_AGREES"


# ------------------------------------------------------------- the window

def test_a_window_is_not_a_passage_and_does_not_leak_the_room():
    nd, rep = _measured_case("C_ROOM_WITH_AN_EXTERNAL_WINDOW")
    win = rep.openings.windows()
    assert len(win) == 1
    assert not win[0].is_navigable
    assert not win[0].may_partition_rooms
    assert win[0].may_close_boundary
    assert rep.counts()["release_eligible"] == 1
    rel = [r for g in rep.graphs for r in g.relations]
    assert rel and rel[0][topo.NAVIGABLE_FREE_SPACE]["connected"] is False


def _measured_case(name):
    case = next(c for c in fx.cases() if c.name == name)
    nd = ad.normalize(case.decode, source_file=name, source_hash="FIXTURE")
    return nd, cm.measure(nd, cp.build(nd))


# ------------------------------------------------------------ the matching

def test_two_plausible_hosts_leave_the_portal_ambiguous():
    nd, rep = _measured_case("O_OPENING_NEAR_TWO_POSSIBLE_HOST_WALLS")
    assert rep.matches.counts()["ambiguous_portal_hosts"] >= 1
    amb = {m.opening_id for m in rep.matches.ambiguous()}
    for row in rep.rows:
        if row._release()["status"] == "RELEASE_ELIGIBLE_GEOMETRY":
            assert not ({o["opening_id"] for o in row.boundary_openings}
                        & amb)


def test_a_swing_that_pierces_nothing_is_not_a_door():
    nd, rep = _measured_case("S_DOOR_SWING_TOUCHING_NO_WALL")
    assert rep.openings.counts()["door_candidates"] == 0
    assert rep.openings.unmatched_symbols
    assert rep.openings.unmatched_symbols[0]["verdict"] == "NOT_AN_OPENING"


def test_nothing_is_matched_by_being_nearest():
    assert "no global nearest-wall search" in \
        pm.MatchReport().record()["never"]
    assert "NO_COMPETING_HOST" in pm.CHECKS


# -------------------------------------------------------------- the graph

def test_a_room_with_no_readable_name_is_still_a_physical_space():
    nd, rep = _measured_case("J_UNLABELLED_ROOM_WITH_A_VALID_DOOR")
    unnamed = [r for r in rep.rows if not r.zones]
    assert unnamed, [r.space_id for r in rep.rows]
    assert unnamed[0].is_complete
    assert unnamed[0].physical_space_status == \
        "PHYSICAL_SPACE_VALIDATED_IDENTITY_UNKNOWN"
    assert unnamed[0]._release()["status"] == "DIAGNOSTIC_ONLY"


def test_two_labels_in_one_face_are_one_space_with_zones():
    nd, rep = _measured_case("H_OPEN_PLAN_WITH_NO_SEPARATOR")
    assert len(rep.rows) == 1
    row = rep.rows[0]
    assert len(row.zones) == 2
    assert row.identity_status == "IDENTITY_IS_SEVERAL_FUNCTIONAL_ZONES"
    assert row._release()["status"] == "DIAGNOSTIC_ONLY"
    assert not rep.openings.openings, "no partition was manufactured"
    conn = [c for g in rep.graphs for c in g.open_plan_connections]
    assert conn and conn[0]["ROOM_PARTITION_RELATION"] == topo.REL_ONE_SPACE


def test_the_room_perimeter_is_not_the_material_wall_length():
    nd, rep = _measured(_two_rooms())
    q = rep.rows[0].quantities
    # The left room is 4.9 x 4.0 m: 17.8 m of boundary, of which 0.9 m is
    # the doorway and 16.9 m is material.
    assert q["SPACE_BOUNDARY_LENGTH_MM"] == 17800.0
    assert q["OPENING_LENGTH_MM"] == 900.0
    assert q["MATERIAL_PRESENT_LENGTH_MM"] == 16900.0
    assert "is NOT the material wall length" in q["never"]


def test_a_portal_boundary_carries_zero_material():
    nd, rep = _measured(_two_rooms())
    virtual = [s for r in rep.rows for s in r.boundary_roles
               if s["material"] == "VIRTUAL_NO_MATERIAL"]
    assert virtual, "the door must appear as a boundary with no material"
    pb = [b for g in rep.graphs for b in g.portal_boundaries]
    assert pb and pb[0].material_present_length_mm == 0.0
    assert pb[0].space_boundary_length_mm == 900.0


def test_the_inside_of_a_wall_is_not_a_space():
    nd, rep = _measured(_two_rooms())
    assert rep.graphs[0].material_faces >= 1
    for row in rep.rows:
        assert row.enclosure.area_m2 > 1.0


# --------------------------------------------------------------- the freeze

def test_the_twenty_two_round4_cases_hold():
    rep = r4.assert_frozen()
    assert rep["cases"] == 22
    assert rep["failed"] == 0
    assert rep["required_results_held"] is True


def test_no_grade_d_opening_anywhere_may_close_a_boundary():
    """Across all twenty-two drawings, without exception."""
    for case in fx.cases():
        nd = ad.normalize(case.decode, source_file=case.name,
                          source_hash="FIXTURE")
        rep = cm.measure(nd, cp.build(nd))
        for o in (rep.openings.openings if rep.openings else []):
            if o.grade == co.GRADE_D:
                assert not o.may_close_boundary, f"{case.name} {o.opening_id}"
            if o.opening_class == co.WINDOW_OPENING:
                assert not o.may_partition_rooms


def test_rounds_two_and_three_still_hold_under_round_four():
    from engine import round2_selftest as r2
    from engine import round3_selftest as r3

    assert r2.assert_frozen()["failed"] == 0
    assert r3.assert_frozen()["failed"] == 0


def test_the_freeze_hashes_are_stable():
    for fn in (r4.freeze_hash, dr.freeze_hash, co.classifier_hash,
               pm.matcher_hash, rpg.graph_hash):
        assert fn() == fn() and len(fn()) == 24


def test_no_tolerance_was_invented_this_round():
    """Every number the opening classifier uses is an earlier freeze."""
    from engine import space_enclosure as enc

    assert co.MIN_GAP_MM == enc.JUNCTION_REACH_MM
    assert co.COLLINEAR_TOL_MM == enc.COLLINEAR_JOIN_MM
    assert co.JAMB_REACH_MM == cp.MIN_WALL_THICKNESS_MM
    assert co.MAX_WALL_MM == cp.MAX_WALL_THICKNESS_MM
    assert rpg.MATERIAL_FACE_MAX_MM == cp.MAX_WALL_THICKNESS_MM
    assert pm.REACH_MM == co.JAMB_REACH_MM
