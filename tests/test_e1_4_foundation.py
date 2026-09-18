"""E1.4 §20 - the twenty-three regressions the foundation repair must pass.

Each case is built here. None is P7757, none carries a benchmark
quantity, and none was drawn to make a particular number come out. Where
a case comes from a real failure, the failure is described in the test's
own words and the geometry is synthetic.

The nine Ground Floor candidates the external review vetoed are
regression cases for the GENERAL mechanism. There is no rule here that
names one of them, and no test asserts that a particular room closes.
"""

import importlib
import math
from pathlib import Path

import pytest

from engine import boundary_capability as bcap
from engine import boundary_chain as bc
from engine import boundary_fragment as bf
from engine import boundary_walk as bw
from engine import cad_geometry as cg
from engine import column_ownership as co
from engine import column_validation as cv
from engine import execution_provenance as ep
from engine import interval_role as ir
from engine import label_anchor as la
from engine import line_semantics as ls
from engine import opening_discovery as od
from engine import ring_qa as rq
from engine import traversal_geometry as tg
from engine import visual_finding as vf

REPO = Path(__file__).resolve().parents[1]


# 1 --------------------------------------------------------------------
def test_1_an_executed_module_missing_from_the_manifest_fails_the_freeze():
    """boundary_walk.py was the whole E1.3 mechanism and the freeze did not
    bind it. A manifest maintained by hand omits what nobody remembered."""
    man = ep.manifest(REPO)
    names = {r["MODULE_NAME"] for r in man["modules"]}
    assert "engine.boundary_walk" in names, (
        "the mechanism that walks every boundary must be bound")
    assert ep.assert_every_executed_local_module_is_hashed(
        man, REPO)["EVERY_EXECUTED_LOCAL_ANALYTICAL_MODULE_IS_HASHED"]

    # a module imported after the manifest was taken is not bound by it
    probe = REPO / "engine" / "_e1_4_manifest_probe.py"
    probe.write_text("VALUE = 1\n")
    try:
        importlib.invalidate_caches()
        importlib.import_module("engine._e1_4_manifest_probe")
        assert "engine._e1_4_manifest_probe" in ep.unhashed_executed_modules(
            man, REPO)
        with pytest.raises(ValueError) as e:
            ep.assert_every_executed_local_module_is_hashed(man, REPO)
        assert "EVERY_EXECUTED_LOCAL_ANALYTICAL_MODULE_IS_HASHED = false" \
            in str(e.value)
        # and generating it again binds the new file, because it is
        # generated from what ran
        again = ep.manifest(REPO)
        assert ep.assert_every_executed_local_module_is_hashed(again, REPO)
    finally:
        probe.unlink()
        import sys
        sys.modules.pop("engine._e1_4_manifest_probe", None)


def test_1b_a_compiled_file_is_never_provenance():
    man = ep.manifest(REPO)
    assert not [r for r in man["modules"]
                if "__pycache__" in r["RELATIVE_FILE_PATH"]
                or r["RELATIVE_FILE_PATH"].endswith(".pyc")]


# 2 --------------------------------------------------------------------
def test_2_a_pool_contour_never_silently_becomes_a_material_wall_face():
    """E1.2 asked `iv.kind in ("ARC","CIRCLE")` before it asked what the
    interval was, so the edge of the water came back as wall face."""
    for kind in (cg.ARC, cg.CIRCLE, cg.LINE, cg.POLYLINE, cg.COMPOSITE_CURVE):
        row = bcap.boundary_role_for(ir.POOL_CONTOUR, kind=kind)
        assert row["BOUNDARY_ROLE"] == bcap.POOL_WATER_EDGE
        assert row["BOUNDARY_ROLE"] != cg.MATERIAL_WALL_FACE
        assert row["MAY_BOUND_A_CLEAR_FLOOR_REGION"] is False
    assert bcap.has(ir.POOL_CONTOUR, bcap.CAN_BOUND_POOL_WATER_REGION)
    assert not bcap.has(ir.POOL_CONTOUR, bcap.CAN_CONTRIBUTE_MATERIAL_WALL_LENGTH)
    assert not bcap.has(ir.POOL_CONTOUR, bcap.CAN_HOST_OPENING)
    # E1.2's frozen admission list is the defect, and it is not consulted
    assert ir.POOL_CONTOUR in ir.MAY_BOUND_MATERIAL
    assert bcap.roles_admitted_by_e1_2_but_not_by_e1_4() == (ir.POOL_CONTOUR,)


# 3 --------------------------------------------------------------------
def test_3_a_curved_wall_keeps_both_its_curve_and_its_wall_role():
    row = bcap.boundary_role_for(ir.MATERIAL_WALL_FACE, kind=cg.ARC)
    assert row["BOUNDARY_ROLE"] == cg.MATERIAL_WALL_FACE
    assert row["SHAPE"] == bcap.CURVE
    assert row["MAY_BOUND_A_CLEAR_FLOOR_REGION"] is True
    assert bcap.has(ir.MATERIAL_WALL_FACE,
                    bcap.CAN_CONTRIBUTE_MATERIAL_WALL_LENGTH)


def test_3b_curved_glazing_bounds_the_space_and_is_not_masonry():
    row = bcap.boundary_role_for(ir.GLAZING, kind=cg.ARC)
    assert row["BOUNDARY_ROLE"] == cg.GLAZING_BOUNDARY
    assert row["SHAPE"] == bcap.CURVE
    assert row["MAY_BOUND_A_CLEAR_FLOOR_REGION"] is True
    assert not bcap.has(ir.GLAZING, bcap.CAN_CONTRIBUTE_MATERIAL_WALL_LENGTH)


def test_3c_an_annotation_arc_bounds_nothing():
    row = bcap.boundary_role_for(ir.ANNOTATION, kind=cg.ARC)
    assert row["BOUNDARY_ROLE"] == bcap.NOT_A_PHYSICAL_BOUNDARY
    assert bcap.capabilities_of(ir.ANNOTATION) == ()


def test_3d_every_role_is_answered_explicitly():
    bcap.assert_every_role_is_answered()
    assert bcap.roles_missing_a_capability_row() == ()


# 4 --------------------------------------------------------------------
def test_4_a_door_swing_arc_is_opening_evidence_and_never_a_wall():
    row = bcap.boundary_role_for(ir.DOOR, kind=cg.ARC)
    assert row["BOUNDARY_ROLE"] == bcap.OPENING_EVIDENCE_NOT_A_BOUNDARY
    assert row["MAY_BOUND_A_CLEAR_FLOOR_REGION"] is False
    assert bcap.capabilities_of(ir.DOOR) == ()
    assert od.SWING_ARC in od.ESTABLISHES_THAT_AN_OPENING_EXISTS


# 5 --------------------------------------------------------------------
def test_5_a_footprint_that_contradicts_its_reported_size_is_unresolved():
    """The frozen case: a loop spanning about 600 x 2600 mm reporting a
    size of 600 x 250 mm. Nothing downstream can tell which is wrong."""
    got = cv.assess({
        "loop": [(0, 0), (600, 0), (600, 2600), (0, 2600)],
        "reported_size_mm": (600, 250),
        "on_structural_layer": True,
        "repeats_as_a_family": True,
    })
    assert got["DERIVED_GEOMETRY_SELF_CONSISTENT"] is False
    assert got["COLUMN_EXISTENCE_STATUS"] == cv.STRUCTURAL_COLUMN_UNRESOLVED
    assert got["derived_bbox_height_mm"] == 2600.0
    assert got["reported_size_mm"] == [600.0, 250.0]
    # and a consistent, compact, raised loop is confirmed
    ok = cv.assess({
        "loop": [(0, 0), (600, 0), (600, 600), (0, 600)],
        "reported_size_mm": (600, 600),
        "on_structural_layer": True, "repeats_as_a_family": True,
    })
    assert ok["COLUMN_EXISTENCE_STATUS"] == cv.STRUCTURAL_COLUMN_CONFIRMED


def test_5b_the_footprint_is_the_loops_own_ring_not_its_members_extents():
    """Reproducing the frozen 600 x 2600 against 600 x 250 shows where the
    two numbers came from: one is the loop, the other is the bounding box
    of the whole entities that contribute sides to it. A wall line several
    metres long can give a loop 250 mm of itself."""
    members = [{"object_id": "W-1", "a": (0, 0), "b": (0, 2600)},
               {"object_id": "W-2", "a": (600, 0), "b": (600, 2600)},
               {"object_id": "S-1", "a": (0, 0), "b": (600, 0)},
               {"object_id": "S-2", "a": (0, 250), "b": (600, 250)}]
    d = cv.derive_from_members(members, expect_centre_mm=(300, 125),
                               max_side_mm=1200.0)
    assert d["LOOP_RING_ESTABLISHED"] is True
    assert d["FOOTPRINT_BOX_FROM_THE_LOOPS_OWN_RING_MM"] == [0.0, 0.0,
                                                             600.0, 250.0]
    assert d["MEMBER_ENTITY_EXTENTS_BOX_MM"] == [0, 0, 600, 2600]
    assert d["SIDES_OF_THIS_LOOP_ARE_PARTS_OF_LONGER_LINES"] is True
    assert {r["object_id"] for r in d["MEMBERS_REACHING_BEYOND_THE_FOOTPRINT"]} \
        == {"W-1", "W-2"}
    # the loop and the size agree; what is not established is that a
    # rectangle formed where two long walls cross is a discrete column
    got = cv.assess({"loop": d["LOOP_RING"], "reported_size_mm": (600, 250),
                     "on_structural_layer": True, "repeats_as_a_family": True,
                     "sides_are_parts_of_longer_lines":
                         d["SIDES_OF_THIS_LOOP_ARE_PARTS_OF_LONGER_LINES"]})
    assert got["DERIVED_GEOMETRY_SELF_CONSISTENT"] is True
    assert got["COLUMN_EXISTENCE_STATUS"] == cv.STRUCTURAL_COLUMN_UNRESOLVED
    assert got["SIDES_OF_THIS_LOOP_ARE_PARTS_OF_LONGER_LINES"] is True
    assert got["nothing_is_deleted"]


def test_5c_members_that_do_not_close_establish_no_footprint():
    d = cv.derive_from_members([{"object_id": "A", "a": (0, 0), "b": (600, 0)},
                                {"object_id": "B", "a": (600, 0),
                                 "b": (600, 600)}])
    assert d["LOOP_RING_ESTABLISHED"] is False
    assert d["LOOP_RING"] is None
    assert d["MEMBER_ENTITY_EXTENTS_BOX_MM"] == [0.0, 0.0, 600.0, 600.0]


# 6 --------------------------------------------------------------------
def test_6_a_repeated_long_thin_loop_is_not_automatically_a_column():
    got = cv.assess({
        "loop": [(0, 0), (3000, 0), (3000, 200), (0, 200)],
        "reported_size_mm": (3000, 200),
        "on_structural_layer": True,
        "repeats_as_a_family": True,
        "touches_a_wall": True,
        "resembles_another_loop": True,
    })
    assert got["DERIVED_GEOMETRY_SELF_CONSISTENT"] is True
    assert got["footprint_is_compact"] is False
    assert got["COLUMN_EXISTENCE_STATUS"] == cv.STRUCTURAL_COLUMN_UNRESOLVED
    assert "pier" in got["why"]


def test_6b_a_compact_loop_nothing_raises_as_structure_is_not_a_column():
    got = cv.assess({"loop": [(0, 0), (500, 0), (500, 500), (0, 500)],
                     "reported_size_mm": (500, 500)})
    assert got["COLUMN_EXISTENCE_STATUS"] == cv.STRUCTURAL_COLUMN_UNRESOLVED
    assert got["evidence_raising_it_as_structure"] == []


def test_6c_nothing_is_deleted_for_an_unresolved_column():
    got = cv.assess({"loop": [(0, 0), (600, 0), (600, 2600), (0, 2600)],
                     "reported_size_mm": (600, 250)})
    assert got["nothing_is_deleted"]
    assert got["derived_perimeter_mm"] > 0


# 7, 8 -----------------------------------------------------------------
def test_7_a_hidden_structural_column_does_not_own_the_clear_finish_face():
    got = co.clear_face_ownership(
        existence_status=co.STRUCTURAL_COLUMN_CONFIRMED,
        exposure_status=co.NOT_EXPOSED_TO_ROOM,
        architectural_face_present=True)
    assert got["CLEAR_FACE_OWNERSHIP_STATUS"] == co.ARCHITECTURAL_FACE_OWNS
    assert got["may_deform_the_clear_internal_boundary"] is False
    assert got["structural_object_relation"] == \
        co.STRUCTURAL_OBJECT_BEHIND_FINISH_FACE


def test_8_an_exposed_column_may_own_the_clear_finish_face():
    got = co.clear_face_ownership(
        existence_status=co.STRUCTURAL_COLUMN_CONFIRMED,
        exposure_status=co.EXPOSED_TO_ROOM,
        architectural_face_present=False)
    assert got["CLEAR_FACE_OWNERSHIP_STATUS"] == co.COLUMN_FACE_OWNS
    assert got["may_deform_the_clear_internal_boundary"] is True
    assert bcap.has(ir.COLUMN, bcap.CAN_BE_CLEAR_FINISH_FACE)


def test_8b_existence_exposure_and_ownership_stay_three_questions():
    unresolved = co.clear_face_ownership(
        existence_status=co.COLUMN_CANDIDATE_UNRESOLVED,
        exposure_status=co.EXPOSURE_UNRESOLVED,
        architectural_face_present=False)
    assert unresolved["CLEAR_FACE_OWNERSHIP_STATUS"] == \
        co.CLEAR_FACE_OWNERSHIP_UNRESOLVED
    assert unresolved["may_deform_the_clear_internal_boundary"] is False


# 9 --------------------------------------------------------------------
def test_9_a_dashed_overhead_outline_cannot_become_a_wall():
    """Cold V2 saw dashed stair outlines appearing as wall and column."""
    stair = ls.classify([ls.LINETYPE_IS_DASHED, ls.RUNS_WITH_A_STAIR])
    assert stair["LINE_SEMANTICS_STATUS"] == ls.STAIR_PROJECTION
    assert stair["MAY_BE_ASKED_TO_BOUND"] is False

    overhead = ls.classify([ls.LINETYPE_IS_DASHED, ls.LAYER_SAYS_OVERHEAD])
    assert overhead["LINE_SEMANTICS_STATUS"] == ls.OVERHEAD_GEOMETRY
    assert overhead["MAY_BE_ASKED_TO_BOUND"] is False

    # a line that would have closed a chain is still not a wall: the
    # evidence that it is outside the cut plane wins and says so
    tempting = ls.classify([ls.LINETYPE_IS_DASHED, ls.LAYER_SAYS_OVERHEAD,
                            ls.IS_INSIDE_A_WALL_BAND])
    assert tempting["MAY_BE_ASKED_TO_BOUND"] is False
    assert ls.IS_INSIDE_A_WALL_BAND in tempting["blocked_by"]

    unknown = ls.classify([])
    assert unknown["LINE_SEMANTICS_STATUS"] == ls.UNRESOLVED
    assert unknown["MAY_BE_ASKED_TO_BOUND"] is False

    nothing_exposed = ls.classify([ls.LINETYPE_NOT_EXPOSED])
    assert nothing_exposed["LINE_SEMANTICS_STATUS"] == ls.UNRESOLVED

    # this drawing draws what the cut plane misses with a broken linetype,
    # so a continuous line is in the cut plane. What it is MADE of is the
    # semantic role's question and this status does not answer it
    plain = ls.classify([ls.LINETYPE_IS_CONTINUOUS])
    assert plain["LINE_SEMANTICS_STATUS"] == ls.VISIBLE_MATERIAL_FACE
    assert plain["MAY_BE_ASKED_TO_BOUND"] is True
    assert not bcap.may_bound_a_clear_floor_region(ir.FURNITURE)

    solid = ls.classify([ls.LINETYPE_IS_CONTINUOUS,
                         ls.PAIRED_AT_A_WALL_THICKNESS])
    assert solid["LINE_SEMANTICS_STATUS"] == ls.VISIBLE_MATERIAL_FACE
    assert solid["MAY_BE_ASKED_TO_BOUND"] is True


# 10, 11 ---------------------------------------------------------------
def _wall_at_x(x0):
    """material_between for a single wall standing on the line x = x0."""
    def between(a, b):
        if (a[0] - x0) * (b[0] - x0) < 0:
            return True, f"a wall stands on x = {x0}"
        return False, None
    return between


def test_10_a_bilingual_centroid_across_a_wall_does_not_seed_the_neighbour():
    """LG-012 WASH: the English token, the Arabic token and their group
    centroid did not all stand in the same compartment, and the centroid
    was on the far side of the separating wall."""
    anchors = [
        la.anchor(la.ENGLISH_TOKEN_ANCHOR, (1000.0, 500.0), source="TEXT-1",
                  text="WASH"),
        la.anchor(la.ARABIC_TOKEN_ANCHOR, (3000.0, 500.0), source="TEXT-2"),
        la.anchor(la.GROUP_CENTROID, (2000.0, 500.0), source="GROUP-1"),
    ]
    got = la.assess("LG-XXX", anchors, material_between=_wall_at_x(2500.0))
    assert got["LABEL_SEED_STATUS"] == la.AMBIGUOUS_ACROSS_PHYSICAL_BOUNDARY
    assert got["SEED_MM"] is None
    assert got["compartment_count"] == 2


def test_11_anchors_in_one_compartment_agree_and_seed_from_a_stamp():
    anchors = [
        la.anchor(la.GROUP_CENTROID, (1200.0, 500.0), source="GROUP-1"),
        la.anchor(la.ENGLISH_TOKEN_ANCHOR, (1000.0, 500.0), source="TEXT-1"),
    ]
    got = la.assess("LG-YYY", anchors, material_between=_wall_at_x(2500.0))
    assert got["LABEL_SEED_STATUS"] == la.SEED_ESTABLISHED
    assert got["SEED_ANCHOR_KIND"] == la.ENGLISH_TOKEN_ANCHOR
    assert got["SEED_MM"] == [1000.0, 500.0]


def test_11b_an_ambiguous_seed_is_not_quietly_the_old_centroid():
    anchors = [
        la.anchor(la.ENGLISH_TOKEN_ANCHOR, (1000.0, 500.0), source="T1"),
        la.anchor(la.GROUP_CENTROID, (3000.0, 500.0), source="G1"),
    ]
    got = la.assess("LG-ZZZ", anchors, material_between=_wall_at_x(2000.0))
    assert got["SEED_MM"] is None
    assert got["SEED_ANCHOR_KIND"] is None
    assert "no_area_and_no_expectation" in got


# 12, 13, 14 -----------------------------------------------------------
_WALL = {"wall_id": "W-1", "a": (0.0, 0.0), "b": (6000.0, 0.0),
         "interrupted_spans": [{"from_mm": (2500.0, 0.0),
                                "to_mm": (3400.0, 0.0)}]}


def test_12_door_first_finds_an_opening_the_gap_search_missed():
    """E1.3 looked for gaps between wall ends and only then asked whether
    a door stood there, so a real doorway could never reach the ontology
    if the gap search did not raise it."""
    doors = [{"door_id": "D-1", "at_mm": (2950.0, 120.0),
              "evidence": [od.SWING_ARC, od.DOOR_LEAF],
              "direction": (1.0, 0.0)}]
    found = od.door_first(doors, [_WALL], reach_mm=600.0)
    assert found["matched"] == 1
    cand = found["OPENING_CANDIDATES"][0]
    assert cand["width_mm"] == 900.0
    assert cand["geometry_came_from"] == "THE_HOST_WALLS_OWN_INTERRUPTION"

    # the gap search found nothing at all, and the opening still exists
    rec = od.reconcile([], found)
    row = rec["RECONCILED_OPENINGS"][0]
    assert row["RECONCILIATION_STATUS"] == od.CONFIRMED_DOOR_FIRST


def test_13_the_two_searches_reconcile_deterministically():
    doors = [{"door_id": "D-1", "at_mm": (2950.0, 120.0),
              "evidence": [od.SWING_ARC], "direction": (1.0, 0.0)}]
    found = od.door_first(doors, [_WALL], reach_mm=600.0)
    gap = [{"GAP_ID": "G-1", "start_mm": (2500.0, 0.0),
            "end_mm": (3400.0, 0.0)}]
    rec = od.reconcile(gap, found)
    assert len(rec["RECONCILED_OPENINGS"]) == 1
    assert rec["RECONCILED_OPENINGS"][0]["RECONCILIATION_STATUS"] == \
        od.CONFIRMED_BY_BOTH
    # same inputs, same answer, and every status is accounted for
    assert rec == od.reconcile(gap, od.door_first(doors, [_WALL],
                                                  reach_mm=600.0))
    assert set(rec["counts_by_status"]) == set(od.RECONCILIATION_STATUSES)

    # the same opening, found in the same place, at two different widths
    wide = [{"GAP_ID": "G-2", "start_mm": (2400.0, 0.0),
             "end_mm": (3500.0, 0.0)}]
    conflict = od.reconcile(wide, found)["RECONCILED_OPENINGS"][0]
    assert conflict["RECONCILIATION_STATUS"] == od.CONFLICT
    assert "1100.0 mm against 900.0 mm" in conflict["why"]
    # a wall interruption somewhere else entirely is not the same opening
    elsewhere = [{"GAP_ID": "G-3", "start_mm": (100.0, 0.0),
                  "end_mm": (900.0, 0.0)}]
    rows = od.reconcile(elsewhere, found)["RECONCILED_OPENINGS"]
    assert {r["RECONCILIATION_STATUS"] for r in rows} == {
        od.CONFIRMED_GAP_FIRST, od.CONFIRMED_DOOR_FIRST}


def test_14_unmatched_door_evidence_stays_auditable():
    unbroken = {"wall_id": "W-2", "a": (0.0, 0.0), "b": (6000.0, 0.0),
                "interrupted_spans": []}
    doors = [{"door_id": "D-9", "at_mm": (2950.0, 120.0),
              "evidence": [od.SWING_ARC]},
             {"door_id": "D-10", "at_mm": (30000.0, 0.0),
              "evidence": [od.DOOR_LEAF]},
             {"door_id": "D-11", "at_mm": (100.0, 100.0),
              "evidence": [od.THRESHOLD]}]
    found = od.door_first(doors, [unbroken], reach_mm=600.0)
    assert found["matched"] == 0
    reasons = {a["door_id"]: a["REJECTED_BECAUSE"]
               for a in found["HOST_WALL_MATCH_ATTEMPTS"]}
    assert reasons["D-9"] == od.HOST_WALL_NOT_INTERRUPTED
    assert reasons["D-10"] == od.NO_HOST_WALL_WITHIN_REACH
    assert reasons["D-11"] == "NO_EVIDENCE_THAT_AN_OPENING_EXISTS"
    assert len(found["HOST_WALL_MATCH_ATTEMPTS"]) == 3


def test_14b_appearance_alone_is_not_a_portal():
    doors = [{"door_id": "D-12", "at_mm": (2950.0, 120.0),
              "evidence": [od.OPENING_SYMBOL], "direction": (0.0, 1.0)}]
    found = od.door_first(doors, [_WALL], reach_mm=600.0)
    assert found["matched"] == 0
    assert found["HOST_WALL_MATCH_ATTEMPTS"][0]["REJECTED_BECAUSE"] == \
        od.DOOR_NOT_ALIGNED_WITH_THE_WALL


# 15, 16, 17 -----------------------------------------------------------
def _hypo(side, expecting="a wall face"):
    return bf.hypothesis("LG-PANTRY-LIKE", side, expecting,
                         source="FROZEN_SOURCE_ONLY_V1_OBSERVATION")


def _frag(fid, geom, hypo, start, end):
    return bf.fragment(fid, "LG-PANTRY-LIKE", source_hypothesis=hypo,
                       cad_entity_ids=["E-" + fid], interval_ids=["I-" + fid],
                       ordered_geometry=geom,
                       semantic_role=ir.MATERIAL_WALL_FACE,
                       boundary_capabilities=bcap.capabilities_of(
                           ir.MATERIAL_WALL_FACE),
                       start_termination=start, end_termination=end,
                       confidence="ESTABLISHED_FROM_CAD",
                       provenance="CAD_ENTITY")


def test_15_an_open_room_keeps_every_disconnected_established_fragment():
    """Success for a region the drawing does not enclose is not a closed
    polygon. It is every side that IS drawn, kept, with both ends named."""
    a = _frag("A", [(0, 0), (3000, 0)], _hypo("SOUTH"),
              bf.TERMINATES_AT_A_WALL_END, bf.TERMINATES_AT_AN_UNCLASSIFIED_GAP)
    b = _frag("B", [(3000, 2000), (0, 2000)], _hypo("NORTH"),
              bf.TERMINATES_AT_A_CLASSIFIED_PORTAL, bf.TERMINATES_AT_A_WALL_END)
    got = bf.summarise("LG-PANTRY-LIKE", [a, b],
                       complete_region_status="COMPLETE_REGION_NOT_ESTABLISHED")
    assert got["established_fragment_count"] == 2
    assert got["BOUNDARY_FRAGMENT_STATUS"] == \
        "EVERY_ESTABLISHED_FRAGMENT_RECOVERED"
    assert got["COMPLETE_PHYSICAL_REGION_STATUS"] == \
        "COMPLETE_REGION_NOT_ESTABLISHED"
    assert got["completeness_is_not_closure"]
    # the two fragments are not joined to each other by anything
    assert a["ORDERED_GEOMETRY"][-1] != b["ORDERED_GEOMETRY"][0]


def test_16_a_missing_fragment_is_recorded_and_never_bridged():
    hypo = _hypo("WEST", "a wall face closing the west side")
    miss = bf.unmet(hypo, searched="every interval within the drawing extent "
                                   "on the west of this candidate",
                    why="CAD establishes no face there")
    assert miss["FRAGMENT_STATUS"] == bf.FRAGMENT_HYPOTHESISED_NOT_FOUND
    assert miss["FRAGMENT_ID"] is None
    assert "no_geometry_was_produced" in miss
    assert "ORDERED_GEOMETRY" not in miss
    got = bf.summarise("LG-PANTRY-LIKE", [miss],
                       complete_region_status="COMPLETE_REGION_NOT_ESTABLISHED")
    assert got["established_fragment_count"] == 0
    assert got["hypotheses_not_met"] == 1


def test_17_v1_may_say_where_to_search_and_owns_no_coordinate():
    hypo = _hypo("EAST", "a partition between this space and the next")
    assert "point_mm" not in hypo and "start_mm" not in hypo
    assert not any(isinstance(v, (int, float)) for v in hypo.values())
    assert hypo["SOURCE"] == "FROZEN_SOURCE_ONLY_V1_OBSERVATION"
    frag = _frag("E", [(4000, 0), (4000, 2000)], hypo,
                 bf.TERMINATES_AT_A_WALL_END, bf.TERMINATES_AT_A_WALL_END)
    # the coordinates came from CAD; the hypothesis only said where to look
    assert frag["PROVENANCE"] == "CAD_ENTITY"
    assert frag["CAD_ENTITY_IDS"] == ["E-E"]
    assert frag["SOURCE_HYPOTHESIS"]["SOURCE"] == \
        "FROZEN_SOURCE_ONLY_V1_OBSERVATION"


# 18, 19 ---------------------------------------------------------------
def test_18_visual_uncertainty_with_no_geometry_effect_is_not_blocking():
    """Kitchen was withheld because a finding NAMED unresolved gated the
    release, though neither reading of it moved the proposed boundary."""
    f = vf.finding("COLUMN_EXPOSURE_UNRESOLVED",
                   evidence=["the crop does not settle whether the column "
                             "face is exposed"],
                   confidence="LOW",
                   affects_proposed_boundary=vf.AFFECTS_NO,
                   why="the architectural face runs across the column on "
                       "both readings, so the chain is the same either way")
    assert f["EFFECT"] == vf.DIAGNOSTIC
    assert f["RECOMMENDED_ACTION"] == vf.RECORD_AND_CARRY_FORWARD
    assert vf.gate([f])["COLD_VISUAL_FINDINGS_BLOCK_THE_GEOMETRY"] is False
    # and being unresolved is not a challenge to the stronger source
    x = vf.cross_representation("the face is at x = 2400",
                                vf.VISUAL_UNRESOLVED,
                                what="the position of the clear face")
    assert x["IS_A_CROSS_REPRESENTATION_CHALLENGE"] is False


def test_19_a_positive_contradiction_on_the_clear_face_is_blocking():
    f = vf.finding("COLUMN_EXPOSURE_CONTRADICTED",
                   evidence=["the crop shows the column standing proud of "
                             "the wall line"],
                   confidence="HIGH",
                   affects_proposed_boundary=vf.AFFECTS_YES,
                   affected_chain_elements=["CH-4"],
                   visual_position=vf.VISUAL_CONTRADICTION,
                   why="if the column is exposed the clear face steps "
                       "around it and the chain moves")
    assert f["EFFECT"] == vf.BLOCKING
    assert f["RECOMMENDED_ACTION"] == vf.WITHHOLD_UNTIL_RESOLVED
    g = vf.gate([f])
    assert g["COLD_VISUAL_FINDINGS_BLOCK_THE_GEOMETRY"] is True
    assert "CH-4" in g["why"]
    x = vf.cross_representation("the face is at x = 2400",
                                vf.VISUAL_CONTRADICTION,
                                what="the position of the clear face")
    assert x["IS_A_CROSS_REPRESENTATION_CHALLENGE"] is True


def test_19b_not_knowing_whether_it_moves_the_boundary_withholds():
    f = vf.finding("SOMETHING_IS_DRAWN_HERE", evidence=["a mark"],
                   confidence="LOW",
                   affects_proposed_boundary=vf.AFFECTS_UNRESOLVED)
    assert f["EFFECT"] == vf.BLOCKING
    assert f["RECOMMENDED_ACTION"] == vf.HUMAN_REVIEW


# 20 --------------------------------------------------------------------
def _single_line_walk():
    pieces = [{"coords": [(0.0, 0.0), (4000.0, 0.0)], "object_id": "L1",
               "layer": "W", "boundary_role": cg.MATERIAL_WALL_FACE}]
    steps = [{"STEP": "MATERIAL_WALL_FACE", "piece": 0, "entered_at_end": 0},
             {"STEP": "SINGLE_LINE_WALL_END_TURN", "at_mm": [4000.0, 0.0],
              "length_mm": 0.0},
             {"STEP": "MATERIAL_WALL_FACE", "piece": 0, "entered_at_end": 1}]
    return tg.traverse(steps, pieces, mates={})


def test_20_a_single_line_u_turn_doubles_nothing():
    out = _single_line_walk()
    assert out[tg.TRAVERSAL_PATH]["TRAVERSAL_LENGTH_MM"] == 8000.0
    assert out[tg.TRAVERSAL_PATH]["STEPS_THAT_REPEAT_A_STRETCH"] == 1
    u = out[tg.UNIQUE_PHYSICAL_BOUNDARY_GEOMETRY]
    assert u["PHYSICAL_BOUNDARY_LENGTH_MM"] == 4000.0
    assert u["DUPLICATION_THE_TRAVERSAL_WOULD_HAVE_ADDED_MM"] == 4000.0
    assert len(u["stretches"]) == 1
    assert u["stretches"][0]["TIMES_WALKED"] == 2
    m = out[tg.MATERIAL_CONTRIBUTION_GEOMETRY]
    assert m["BODIES"] == 1
    assert m["BODY_RUN_LENGTH_MM"] == 4000.0
    body = m["bodies"][0]
    # a finish reads faces against the run, and there is one face here
    assert body["FACES_WALKED_ON_THIS_REGIONS_SIDE"] == 1
    assert body["FACE_LENGTH_ON_THIS_REGIONS_SIDE_MM"] == 4000.0
    assert body["THICKNESS_ESTABLISHED"] is False
    assert body["THICKNESS_MM"] is None
    tg.assert_no_stretch_is_counted_twice(out)


def test_20b_the_turn_across_nothing_carries_no_length():
    out = _single_line_walk()
    turn = [s for s in out[tg.TRAVERSAL_PATH]["steps"]
            if s["BOUNDARY_KIND"] == tg.TURN_WITHOUT_GEOMETRY]
    assert len(turn) == 1 and turn[0]["length_mm"] == 0.0


def test_20c_a_wall_with_both_faces_in_the_room_is_one_wall():
    pieces = [{"coords": [(0.0, 0.0), (3000.0, 0.0)], "object_id": "F1",
               "boundary_role": cg.MATERIAL_WALL_FACE},
              {"coords": [(0.0, 200.0), (3000.0, 200.0)], "object_id": "F2",
               "boundary_role": cg.MATERIAL_WALL_FACE}]
    mates = {0: [{"mate": 1, "thickness_mm": 200.0,
                  "matched_family_mm": 200.0}],
             1: [{"mate": 0, "thickness_mm": 200.0,
                  "matched_family_mm": 200.0}]}
    steps = [{"STEP": "MATERIAL_WALL_FACE", "piece": 0, "entered_at_end": 0},
             {"STEP": "WALL_END_RETURN", "at_mm": [3000.0, 0.0],
              "to_mm": [3000.0, 200.0], "thickness_mm": 200.0,
              "matched_family_mm": 200.0, "mate_piece": 1, "mate_end": 1,
              "why": "the end of the wall"},
             {"STEP": "MATERIAL_WALL_FACE", "piece": 1, "entered_at_end": 1}]
    m = tg.traverse(steps, pieces,
                    mates=mates)[tg.MATERIAL_CONTRIBUTION_GEOMETRY]
    assert m["BODIES"] == 1
    body = m["bodies"][0]
    assert body["FACES_WALKED_ON_THIS_REGIONS_SIDE"] == 2
    assert body["BOTH_SIDES_FACE_THIS_REGION"] is True
    assert body["BODY_RUN_LENGTH_MM"] == 3000.0
    assert body["FACE_LENGTH_ON_THIS_REGIONS_SIDE_MM"] == 6000.0
    assert body["WALL_END_FACE_LENGTH_MM"] == 200.0


def test_20d_a_portal_span_bounds_the_region_and_contributes_no_material():
    pieces = [{"coords": [(0.0, 0.0), (3000.0, 0.0)], "object_id": "F1",
               "boundary_role": cg.MATERIAL_WALL_FACE}]
    steps = [{"STEP": "MATERIAL_WALL_FACE", "piece": 0, "entered_at_end": 0},
             {"STEP": "ACROSS_A_CLASSIFIED_GAP", "gap": "G-1",
              "GAP_CLASS": "DOORWAY", "start_mm": [3000.0, 0.0],
              "end_mm": [3900.0, 0.0]}]
    out = tg.traverse(steps, pieces, mates={})
    u = out[tg.UNIQUE_PHYSICAL_BOUNDARY_GEOMETRY]
    assert u["LENGTH_BY_KIND_MM"][tg.PORTAL_SPAN] == 900.0
    m = out[tg.MATERIAL_CONTRIBUTION_GEOMETRY]
    assert m["BODY_RUN_LENGTH_MM"] == 3000.0


def test_20e_which_register_answers_which_question_is_written_down():
    out = _single_line_walk()
    q = out["WHICH_REGISTER_ANSWERS_WHICH_QUESTION"]
    assert q["physical boundary length"] == tg.UNIQUE_PHYSICAL_BOUNDARY_GEOMETRY
    assert q["wall material length"] == tg.MATERIAL_CONTRIBUTION_GEOMETRY
    assert q["future plaster length"] == tg.MATERIAL_CONTRIBUTION_GEOMETRY
    assert q["future skirting length"] == tg.MATERIAL_CONTRIBUTION_GEOMETRY


# 21 --------------------------------------------------------------------
def test_21_a_raw_ring_may_not_contain_an_undrawn_closure():
    """3.738 m of chain became a 1.619 m^2 polygon because Polygon() joined
    two loose ends with 1.95 m nobody drew."""
    steps = [[(0.0, 0.0), (2000.0, 0.0)], [(2000.0, 0.0), (2000.0, 1738.0)]]
    ring = [(0.0, 0.0), (2000.0, 0.0), (2000.0, 1738.0)]
    got = rq.assess(ring=ring, chain_length_mm=3738.0, step_points=steps,
                    seed=(500.0, 200.0))
    rq.assert_every_required_field_is_written(got)
    assert got["MAX_UNDRAWN_CLOSURE_MM"] > 1.0
    assert got["RING_CONSISTS_ONLY_OF_CHAIN"] is False
    assert got["CHAIN_CONTINUITY_STATUS"] == rq.OPEN_ENDED
    verdict = rq.establishes_geometry(got)
    assert verdict["RING_ESTABLISHES_GEOMETRY"] is False
    assert "THE_RING_DID_NOT_CLOSE_ON_THE_CHAIN" in verdict["WHY_NOT"]


def test_21b_a_ring_that_is_its_own_chain_passes_every_field():
    steps = [[(0.0, 0.0), (4000.0, 0.0)], [(4000.0, 0.0), (4000.0, 3000.0)],
             [(4000.0, 3000.0), (0.0, 3000.0)], [(0.0, 3000.0), (0.0, 0.0)]]
    ring = [steps[0][0]] + [p for s in steps for p in s[1:]]
    chain = 4000.0 + 3000.0 + 4000.0 + 3000.0
    got = rq.assess(ring=ring, chain_length_mm=chain, step_points=steps,
                    seed=(2000.0, 1500.0),
                    portal_spans=[{"GAP_ID": "G-1",
                                   "start_mm": (4000.0, 3000.0),
                                   "end_mm": (0.0, 3000.0)}])
    rq.assert_every_required_field_is_written(got)
    assert got["CHAIN_CONTINUITY_STATUS"] == rq.CLOSED_ON_ITSELF
    assert got["RING_CONSISTS_ONLY_OF_CHAIN"] is True
    assert got["RING_ENCLOSES_SEED"] is True
    assert got["POLYGON_REPAIR_APPLIED"] is False
    assert got["ISOPERIMETRIC_CHECK"]["PASSED"] is True
    assert got["PORTAL_ORIENTATION_CHECK"][
        "EVERY_SPAN_IS_ONE_STEP_OF_THE_RING"] is True
    assert rq.establishes_geometry(got)["RING_ESTABLISHES_GEOMETRY"] is True


def test_21c_a_ring_that_does_not_contain_its_seed_establishes_nothing():
    steps = [[(0.0, 0.0), (1000.0, 0.0)], [(1000.0, 0.0), (1000.0, 1000.0)],
             [(1000.0, 1000.0), (0.0, 1000.0)], [(0.0, 1000.0), (0.0, 0.0)]]
    ring = [steps[0][0]] + [p for s in steps for p in s[1:]]
    got = rq.assess(ring=ring, chain_length_mm=4000.0, step_points=steps,
                    seed=(5000.0, 5000.0))
    assert got["RING_ENCLOSES_SEED"] is False
    assert "THE_RING_DOES_NOT_CONTAIN_ITS_SEED" in \
        rq.establishes_geometry(got)["WHY_NOT"]


def test_21d_a_span_the_ring_carries_backwards_is_reported():
    steps = [[(0.0, 0.0), (4000.0, 0.0)], [(4000.0, 0.0), (4000.0, 3000.0)],
             [(4000.0, 3000.0), (0.0, 3000.0)], [(0.0, 3000.0), (0.0, 0.0)]]
    ring = [steps[0][0]] + [p for s in steps for p in s[1:]]
    got = rq.assess(ring=ring, chain_length_mm=14000.0, step_points=steps,
                    seed=(2000.0, 1500.0),
                    portal_spans=[{"GAP_ID": "G-1",
                                   "start_mm": (1000.0, 3000.0),
                                   "end_mm": (2000.0, 3000.0)}])
    row = got["PORTAL_ORIENTATION_CHECK"]["spans"][0]
    assert row["THE_SPAN_IS_A_SINGLE_STEP_OF_THE_RING"] is False
    assert got["PORTAL_ORIENTATION_CHECK"][
        "SPANS_THE_RING_DOES_NOT_CARRY"] == 1


# 22 --------------------------------------------------------------------
def _quarter_arc(cx, cy, r, a0, a1, n=24):
    return [(cx + r * math.cos(a0 + (a1 - a0) * k / n),
             cy + r * math.sin(a0 + (a1 - a0) * k / n))
            for k in range(n + 1)]


def test_22_an_exact_curve_survives_the_whole_chain():
    """bc.build once measured every element as the straight line between
    its ends, so an arc was measured and drawn as its chord."""
    arc = _quarter_arc(0.0, 0.0, 2000.0, 0.0, math.pi / 2, n=64)
    element = {"kind": bc.MATERIAL_WALL_FACE, "start_mm": arc[0],
               "end_mm": arc[-1], "points_mm": arc, "object_id": "ARC-1",
               "boundary_role": cg.MATERIAL_WALL_FACE}
    chain = bc.build([element])
    el = chain["CHAIN"][0]
    true_arc = math.pi / 2 * 2000.0
    chord = math.hypot(arc[-1][0] - arc[0][0], arc[-1][1] - arc[0][1])
    assert el["length_mm"] == pytest.approx(true_arc, rel=1e-3)
    assert el["chord_length_mm"] == pytest.approx(chord, rel=1e-6)
    assert el["length_mm"] > el["chord_length_mm"]

    # and through the traversal the same curve is measured along itself
    pieces = [{"coords": arc, "object_id": "ARC-1",
               "boundary_role": cg.MATERIAL_WALL_FACE}]
    out = tg.traverse([{"STEP": "MATERIAL_WALL_FACE", "piece": 0,
                        "entered_at_end": 0}], pieces, mates={})
    u = out[tg.UNIQUE_PHYSICAL_BOUNDARY_GEOMETRY]
    assert u["PHYSICAL_BOUNDARY_LENGTH_MM"] == pytest.approx(true_arc,
                                                             rel=1e-3)
    assert len(u["stretches"][0]["points_mm"]) == len(arc)


# 23 --------------------------------------------------------------------
def test_23_order_is_never_identity_in_the_traversal():
    """The same drawing, its faces handed over in a different order, is the
    same boundary and the same material."""
    a = {"coords": [(0.0, 0.0), (3000.0, 0.0)], "object_id": "F1",
         "boundary_role": cg.MATERIAL_WALL_FACE}
    b = {"coords": [(3000.0, 0.0), (3000.0, 2000.0)], "object_id": "F2",
         "boundary_role": cg.MATERIAL_WALL_FACE}
    one = tg.traverse(
        [{"STEP": "MATERIAL_WALL_FACE", "piece": 0, "entered_at_end": 0},
         {"STEP": "MATERIAL_WALL_FACE", "piece": 1, "entered_at_end": 0}],
        [a, b], mates={})
    two = tg.traverse(
        [{"STEP": "MATERIAL_WALL_FACE", "piece": 1, "entered_at_end": 0},
         {"STEP": "MATERIAL_WALL_FACE", "piece": 0, "entered_at_end": 0}],
        [b, a], mates={})
    keys_one = {s["GEOMETRY_KEY_HASH"]
                for s in one[tg.UNIQUE_PHYSICAL_BOUNDARY_GEOMETRY]["stretches"]}
    keys_two = {s["GEOMETRY_KEY_HASH"]
                for s in two[tg.UNIQUE_PHYSICAL_BOUNDARY_GEOMETRY]["stretches"]}
    assert keys_one == keys_two
    assert (one[tg.UNIQUE_PHYSICAL_BOUNDARY_GEOMETRY][
        "PHYSICAL_BOUNDARY_LENGTH_MM"]
        == two[tg.UNIQUE_PHYSICAL_BOUNDARY_GEOMETRY][
            "PHYSICAL_BOUNDARY_LENGTH_MM"])
    assert ([r["BODY_ID"] for r in
             one[tg.MATERIAL_CONTRIBUTION_GEOMETRY]["bodies"]]
            == [r["BODY_ID"] for r in
                two[tg.MATERIAL_CONTRIBUTION_GEOMETRY]["bodies"]])


def test_23b_a_stretch_is_the_same_stretch_walked_either_way():
    fwd = tg.geometry_key([(0.0, 0.0), (1000.0, 0.0)])
    rev = tg.geometry_key([(1000.0, 0.0), (0.0, 0.0)])
    assert fwd == rev


def test_23c_a_label_seed_does_not_depend_on_the_order_of_its_anchors():
    pts = [la.anchor(la.ENGLISH_TOKEN_ANCHOR, (1000.0, 500.0), source="T1"),
           la.anchor(la.ARABIC_TOKEN_ANCHOR, (3000.0, 500.0), source="T2"),
           la.anchor(la.GROUP_CENTROID, (2000.0, 500.0), source="G1")]
    between = _wall_at_x(2500.0)
    first = la.assess("LG-A", pts, material_between=between)
    second = la.assess("LG-A", list(reversed(pts)),
                       material_between=between)
    assert first["LABEL_SEED_STATUS"] == second["LABEL_SEED_STATUS"]
    assert first["SEED_MM"] == second["SEED_MM"]
    assert first["compartment_count"] == second["compartment_count"]


# the Pantry regression (§13) -------------------------------------------
def test_pantry_class_success_is_preserved_evidence_not_a_closed_polygon():
    """A region the drawing does not enclose. What must come out is every
    fragment that IS established, each end named, the missing side stated,
    and no polygon."""
    south = _frag("S", [(0, 0), (2400, 0)], _hypo("SOUTH"),
                  bf.TERMINATES_AT_A_WALL_END,
                  bf.TERMINATES_AT_AN_UNCLASSIFIED_GAP)
    east = _frag("E", [(2400, 0), (2400, 1800)], _hypo("EAST"),
                 bf.TERMINATES_AT_A_WALL_END, bf.TERMINATES_AT_A_WALL_END)
    missing = bf.unmet(_hypo("WEST"), searched="the west of this candidate",
                       why="CAD establishes no face there")
    got = bf.summarise("LG-PANTRY-LIKE", [south, east, missing],
                       complete_region_status="COMPLETE_REGION_NOT_ESTABLISHED")
    assert got["established_fragment_count"] == 2
    assert got["hypotheses_not_met"] == 1
    assert got["COMPLETE_PHYSICAL_REGION_STATUS"] == \
        "COMPLETE_REGION_NOT_ESTABLISHED"
    # nothing anywhere in this answer is a closed region or an area
    assert not any("AREA" in k.upper() for k in got)
    for f in (south, east):
        assert f["START_TERMINATION"] in bf.TERMINATIONS
        assert f["END_TERMINATION"] in bf.TERMINATIONS


def test_no_prior_guard_is_weakened():
    """The E1.3 mechanism's own parameters are unchanged by E1.4."""
    p = bw.frozen_parameters()
    assert p["MODEL"] == "A_BOUNDARY_IS_WALKED_FROM_FACE_TO_FACE_V1"
    assert bw.RING_PERIMETER_TOLERANCE_MM == 1.0
    assert bw.THICKNESS_TOLERANCE_MM == 15.0
    assert bw.MIN_PAIR_OVERLAP_MM == 150.0


# §7 - what the drawing itself says about its linetypes ------------------
def test_9b_a_dashed_layer_is_read_from_the_drawings_own_tables():
    """No layer is named in code. A layer is drawn broken when the LTYPE
    its own record points at has a dash pattern."""
    objects = [
        {"object": "LTYPE", "name": "CONTINUOUS", "handle": [0, 1, 16],
         "description": "Solid line", "pattern_len": 0.0},
        {"object": "LTYPE", "name": "HIDDEN", "handle": [0, 1, 147],
         "description": "__ __ __ __ __ __", "pattern_len": 0.375},
        {"object": "LAYER", "name": "WALLS", "ltype": [5, 1, 16, 16]},
        {"object": "LAYER", "name": "ABOVE", "ltype": [5, 1, 147, 147]},
        {"object": "LAYER", "name": "NOTHING_SAID", "ltype": []},
    ]
    table = ls.linetype_table(objects)
    assert table["WALLS"]["IS_DASHED"] is False
    assert table["ABOVE"]["IS_DASHED"] is True
    assert table["ABOVE"]["LINETYPE"] == "HIDDEN"
    assert table["NOTHING_SAID"]["LINETYPE_WAS_EXPOSED"] is False
    assert ls.layer_linetype_evidence("ABOVE", table) == ls.LINETYPE_IS_DASHED
    assert ls.layer_linetype_evidence("WALLS", table) == \
        ls.LINETYPE_IS_CONTINUOUS
    assert ls.layer_linetype_evidence("NOTHING_SAID", table) == \
        ls.LINETYPE_NOT_EXPOSED
    assert ls.layer_linetype_evidence("NEVER_HEARD_OF_IT", table) == \
        ls.LINETYPE_NOT_EXPOSED


def test_9c_the_sheet_is_read_for_what_it_prints():
    solid = ls.raster_stroke_evidence([True] * 20)
    assert solid["EVIDENCE"] == ls.RASTER_SHOWS_A_SOLID_STROKE
    broken = ls.raster_stroke_evidence(
        [True, True, False, False] * 6)
    assert broken["EVIDENCE"] == ls.RASTER_SHOWS_A_BROKEN_STROKE
    assert broken["blank_runs"] >= ls.BROKEN_MIN_BLANK_RUNS
    assert ls.raster_stroke_evidence([True] * 5)["EVIDENCE"] is None
    assert ls.raster_stroke_evidence([False] * 30)["EVIDENCE"] is None
    # one interruption in an otherwise inked stretch is not a dash pattern
    nearly = ls.raster_stroke_evidence([True] * 10 + [False] + [True] * 10)
    assert nearly["EVIDENCE"] == ls.RASTER_SHOWS_A_SOLID_STROKE


def test_9d_a_dashed_layer_and_a_solid_sheet_settle_nothing():
    got = ls.classify([ls.LINETYPE_IS_DASHED, ls.RASTER_SHOWS_A_SOLID_STROKE,
                       ls.PAIRED_AT_A_WALL_THICKNESS])
    assert got["LINE_SEMANTICS_STATUS"] == ls.UNRESOLVED
    assert got["MAY_BE_ASKED_TO_BOUND"] is False
    assert ls.LINETYPE_IS_DASHED in got["CONFLICTING_EVIDENCE"]
    assert ls.RASTER_SHOWS_A_SOLID_STROKE in got["CONFLICTING_EVIDENCE"]
    # the sheet showing a broken stroke settles it, and it is not material
    settled = ls.classify([ls.LINETYPE_IS_DASHED,
                           ls.RASTER_SHOWS_A_BROKEN_STROKE,
                           ls.PAIRED_AT_A_WALL_THICKNESS])
    assert settled["LINE_SEMANTICS_STATUS"] == ls.BELOW_CUT_PLANE_GEOMETRY
    assert settled["MAY_BE_ASKED_TO_BOUND"] is False


# §14 - the effect is computed from the drawing, not read off the name --
def _owner(*, continues_across):
    return {"rows": [{"COLUMN_ID": "LOOP-001",
                      "member_object_ids": ["COL-1"],
                      "CLEAR_FACE_OWNERSHIP_STATUS": co.ARCHITECTURAL_FACE_OWNS,
                      "architectural_face_continues_across": continues_across}],
            "object_ids_that_do_not_own_the_room_face": ["COL-1"],
            "object_ids_that_own_the_room_face": []}


def _row_with_column_on_its_chain():
    return {"chain": {"CHAIN": [{"object_id": "COL-1"},
                                {"object_id": "W-1"}]}}


def test_14_a_column_that_cannot_move_the_chain_is_diagnostic():
    """Kitchen's bug was that a status NAMED unresolved gated the release.
    Here the architectural face runs unbroken across the footprint, so the
    clear face is that face on either reading and the chain cannot move."""
    from tools import run_e1_4 as r14
    got = r14.affects_proposed_boundary(
        "COLUMN_EXPOSURE_UNRESOLVED", _row_with_column_on_its_chain(),
        _owner(continues_across=True))
    assert got["AFFECTS_PROPOSED_BOUNDARY"] is vf.AFFECTS_NO
    f = vf.finding("COLUMN_EXPOSURE_UNRESOLVED", evidence=["the crop"],
                   confidence="COLD_VISUAL_READING",
                   affects_proposed_boundary=got["AFFECTS_PROPOSED_BOUNDARY"],
                   affected_chain_elements=got["AFFECTED_CHAIN_ELEMENTS"])
    assert vf.gate([f])["COLD_VISUAL_FINDINGS_BLOCK_THE_GEOMETRY"] is False


def test_14b_a_column_that_would_move_the_clear_face_is_blocking():
    from tools import run_e1_4 as r14
    got = r14.affects_proposed_boundary(
        "COLUMN_EXPOSURE_UNRESOLVED", _row_with_column_on_its_chain(),
        _owner(continues_across=False))
    assert got["AFFECTS_PROPOSED_BOUNDARY"] is vf.AFFECTS_YES
    assert got["AFFECTED_CHAIN_ELEMENTS"] == ["LOOP-001"]
    f = vf.finding("COLUMN_EXPOSURE_UNRESOLVED", evidence=["the crop"],
                   confidence="COLD_VISUAL_READING",
                   affects_proposed_boundary=got["AFFECTS_PROPOSED_BOUNDARY"],
                   affected_chain_elements=got["AFFECTED_CHAIN_ELEMENTS"])
    assert vf.gate([f])["COLD_VISUAL_FINDINGS_BLOCK_THE_GEOMETRY"] is True


def test_14c_a_finding_about_the_chain_itself_always_challenges_it():
    from tools import run_e1_4 as r14
    for status in ("WALL_FALSELY_REMOVED", "OPEN_SIDE_FALSELY_CLOSED",
                   "POSSIBLE_UNDER_CAPTURE", "POSSIBLE_OVER_CAPTURE"):
        got = r14.affects_proposed_boundary(
            status, _row_with_column_on_its_chain(),
            _owner(continues_across=True))
        assert got["AFFECTS_PROPOSED_BOUNDARY"] is vf.AFFECTS_YES, status


def test_14d_no_rule_in_the_effect_mechanism_names_a_region():
    """Do not special-case Kitchen. AST-stripped, the mechanism names no
    room, no candidate id and no token from this drawing."""
    import ast
    import inspect
    from tools import run_e1_4 as r14
    src = inspect.getsource(r14.affects_proposed_boundary)
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant):
            node.value.value = ""
        if isinstance(node, (ast.FunctionDef, ast.Module)):
            if (node.body and isinstance(node.body[0], ast.Expr)
                    and isinstance(node.body[0].value, ast.Constant)):
                node.body = node.body[1:] or [ast.Pass()]
    code = ast.unparse(ast.fix_missing_locations(tree)).upper()
    for token in ("KITCHEN", "PANTRY", "WASH", "DEWANEYA", "SALOON",
                  "LG-0", "E1_3-", "E1_4-LG"):
        assert token not in code, token


def test_14e_a_column_at_the_other_end_of_the_floor_cannot_move_this_chain():
    """Asking for every column on the floor whose ownership reads
    ARCHITECTURAL_FACE_OWNS named nineteen loops against one small room.
    A finding about a column that does not meet this chain cannot move
    this boundary, and a rule that says it can is name-based gating in
    different clothes."""
    from tools import run_e1_4 as r14
    row = {"chain": {"CHAIN": [{"start_mm": (0, 0), "end_mm": (2000, 0)},
                               {"start_mm": (2000, 0), "end_mm": (2000, 2000)}]}}
    far = {"rows": [{"COLUMN_ID": "LOOP-FAR",
                     "member_object_ids": ["COL-FAR"],
                     "FOOTPRINT_BOX_FROM_THE_LOOPS_OWN_RING_MM":
                         [50000, 50000, 50600, 50600],
                     "CLEAR_FACE_OWNERSHIP_STATUS": co.ARCHITECTURAL_FACE_OWNS,
                     "architectural_face_continues_across": False}],
           "object_ids_that_do_not_own_the_room_face": ["COL-FAR"],
           "object_ids_that_own_the_room_face": []}
    got = r14.affects_proposed_boundary("COLUMN_EXPOSURE_UNRESOLVED", row, far)
    assert got["AFFECTS_PROPOSED_BOUNDARY"] is vf.AFFECTS_NO
    assert got["AFFECTED_CHAIN_ELEMENTS"] == []

    # the same column standing on this chain does reach it
    near = {"rows": [dict(far["rows"][0],
                          COLUMN_ID="LOOP-NEAR",
                          FOOTPRINT_BOX_FROM_THE_LOOPS_OWN_RING_MM=[
                              1900, -100, 2100, 300])],
            "object_ids_that_do_not_own_the_room_face": ["COL-FAR"],
            "object_ids_that_own_the_room_face": []}
    got = r14.affects_proposed_boundary("COLUMN_EXPOSURE_UNRESOLVED", row, near)
    assert got["AFFECTS_PROPOSED_BOUNDARY"] is vf.AFFECTS_YES
    assert got["AFFECTED_CHAIN_ELEMENTS"] == ["LOOP-NEAR"]
