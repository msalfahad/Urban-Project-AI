"""E1.3 — the eighteen general regressions the correction asks for.

Every fixture is invented: a 150 mm break in a straight wall, a cross wall
landing in a gap, a column behind a straight finish face and the same
column pushed out past it, three walls and an opening. None is P7757 and
none carries a P7757 dimension.

What they guard, in the order the correction lists them:

     1 a 150 mm collinear gap with no door evidence is not a door
     2 a wall-thickness-scale T-junction is not a portal
     3 a confirmed door entity does establish a portal
     4 a probable doorway needs more than one independent evidence
     5 a column behind a straight finish face does not deform the room
     6 a column protruding into the room does deform it
     7 existence and clear-face ownership are separate statuses
     8 an open room keeps an ordered partial boundary chain
     9 an open edge contributes no material
    10 a counter beside an open side does not force the room closed
    11 internal continuity is not openness
    12 a possible functional subzone cannot veto physical enclosure
    13 physical over-capture requires crossing a physical boundary
    14 physical and functional arbitration disagree independently
    15 the ledger refuses a contradictory decision record
    16 an arc keeps its own parameters
    17 site-context labels stay out of the denominator
    18 interval role evidence stays local to its interval
"""

from __future__ import annotations

import math

import pytest

from engine import arbitration_dimensions as ad
from engine import atomic_interval as ai
from engine import boundary_chain as bc
from engine import cad_geometry as cg
from engine import column_ownership as co
from engine import decision_ledger as dl
from engine import edge_relation as er
from engine import gap_ontology as go
from engine import interval_role as ir
from engine import label_ontology as lo
from engine import space_status as ss
from engine import visual_challenger_v2 as vc

JUNCTION = 20.0
DOUBLE_LEAF = cg.MAX_DOUBLE_LEAF_MM


# ------------------------------------------------------------------ gaps
def test_01_a_collinear_gap_without_door_evidence_is_not_a_door():
    """The Driver defect, stated generally.

    Two ends of one straight wall, 150 mm apart, continuing each other's
    line, with no leaf, no swing, no block and nothing else. E1.2 made
    this a portal on the strength of the two ends facing each other, and
    built a released room through it.
    """
    g = go.classify(gap_mm=150.0, junction_gap_mm=JUNCTION,
                    max_barrier_mm=DOUBLE_LEAF)
    assert g["GAP_CLASS"] != go.CONFIRMED_DOOR_PORTAL
    assert g["GAP_CLASS"] != go.PROBABLE_DOOR_PORTAL
    assert g["IS_A_PORTAL"] is False
    assert g["NOTHING_MAY_BE_CLOSED_ACROSS"] is True


def test_02_a_wall_thickness_scale_t_junction_is_not_a_portal():
    """A cross wall lands in the gap. That is a junction, not a doorway."""
    families = go.thickness_families([150.0, 150.0, 152.0, 148.0])
    fam = go.matches_a_thickness_family(150.0, families)
    assert fam is not None and fam["members"] == 4

    g = go.classify(gap_mm=150.0, junction_gap_mm=JUNCTION,
                    max_barrier_mm=DOUBLE_LEAF,
                    occupancy=[go.OCC_PERPENDICULAR_WALL],
                    thickness_family=fam)
    assert g["GAP_CLASS"] == go.MATERIAL_CONTINUITY_GAP
    assert g["IS_A_PORTAL"] is False
    assert g["MATERIAL_CONTINUES_ACROSS"] is True

    # and with nothing standing in it, the same width is a question, not a door
    q = go.classify(gap_mm=150.0, junction_gap_mm=JUNCTION,
                    max_barrier_mm=DOUBLE_LEAF, thickness_family=fam)
    assert q["GAP_CLASS"] == go.UNRESOLVED_GAP


def test_03_a_confirmed_door_entity_establishes_a_portal():
    for ev in go.CONFIRMING_EVIDENCE:
        g = go.classify(gap_mm=900.0, junction_gap_mm=JUNCTION,
                        max_barrier_mm=DOUBLE_LEAF, confirming_evidence=[ev])
        assert g["GAP_CLASS"] == go.CONFIRMED_DOOR_PORTAL, ev
        assert g["IS_A_PORTAL"] is True


def test_04_a_probable_doorway_requires_independent_evidences():
    one = go.classify(gap_mm=900.0, junction_gap_mm=JUNCTION,
                      max_barrier_mm=DOUBLE_LEAF,
                      probable_evidence=[go.EV_JAMB_GEOMETRY])
    assert one["GAP_CLASS"] == go.UNRESOLVED_GAP
    assert one["IS_A_PORTAL"] is False

    two = go.classify(gap_mm=900.0, junction_gap_mm=JUNCTION,
                      max_barrier_mm=DOUBLE_LEAF,
                      probable_evidence=[go.EV_JAMB_GEOMETRY,
                                         go.EV_VISUAL_DOORWAY])
    assert two["GAP_CLASS"] == go.PROBABLE_DOOR_PORTAL
    assert two["IS_A_PORTAL"] is True
    assert len(two["probable_evidence"]) >= go.PROBABLE_EVIDENCE_REQUIRED
    # and it says why, rather than asserting a doorway
    assert any("circumstantial" in n for n in two["notes"])


# --------------------------------------------------------------- columns
def _column(**kw):
    base = dict(column_evidence=["A_SMALL_CLOSED_LOOP",
                                 "ITS_LAYER_HOLDS_ALMOST_NOTHING_BUT_SUCH_LOOPS"],
                structural_in_kind=["ITS_LAYER_HOLDS_ALMOST_NOTHING_BUT_SUCH_LOOPS"])
    base.update(kw)
    return co.assess(**base)


def test_05_a_column_behind_a_straight_finish_face_does_not_deform_the_room():
    """The Driver corner, stated generally."""
    box = (0.0, 0.0, 400.0, 400.0)
    # the finish face is cut into intervals at the column, exactly as CAD
    # fragments it: one piece stops before the pier, the next resumes after
    face_runs_past = [((-3000.0, 200.0), (-1.0, 200.0)),
                      ((401.0, 200.0), (3000.0, 200.0))]
    cont = co.architectural_face_continues_across(box, face_runs_past)
    assert cont["continues_across"] is True, (
        "no single interval spans a column: the test is on collinear runs")
    assert cont["architectural_faces_before_the_footprint"]
    assert cont["architectural_faces_after_the_footprint"]

    # and a face that merely stops at the pier does NOT continue across
    stops = [((-3000.0, 200.0), (-1.0, 200.0))]
    assert co.architectural_face_continues_across(
        box, stops)["continues_across"] is False

    r = _column(architectural_face_continues=cont["continues_across"])
    assert r["EXISTENCE"]["COLUMN_EXISTENCE_STATUS"] == \
        co.STRUCTURAL_COLUMN_CONFIRMED
    assert r["EXPOSURE"]["EXPOSED_TO_ROOM_STATUS"] == co.NOT_EXPOSED_TO_ROOM
    own = r["CLEAR_FACE_OWNERSHIP"]
    assert own["CLEAR_FACE_OWNERSHIP_STATUS"] == co.ARCHITECTURAL_FACE_OWNS
    assert own["may_deform_the_clear_internal_boundary"] is False
    # and the column is NOT deleted - it is described
    assert own["structural_object_relation"] == \
        co.STRUCTURAL_OBJECT_BEHIND_FINISH_FACE


def test_06_a_column_protruding_into_the_room_does_deform_it():
    r = _column(exposure_evidence=[co.EV_PROTRUDES_BEYOND_THE_FINISH_FACE,
                                   co.EV_ARCH_FINISH_WRAPS_THE_COLUMN],
                architectural_face_continues=False,
                architectural_face_present=True)
    assert r["EXPOSURE"]["EXPOSED_TO_ROOM_STATUS"] == co.EXPOSED_TO_ROOM
    own = r["CLEAR_FACE_OWNERSHIP"]
    assert own["CLEAR_FACE_OWNERSHIP_STATUS"] == co.COLUMN_FACE_OWNS
    assert own["may_deform_the_clear_internal_boundary"] is True


def test_07_existence_and_clear_face_ownership_are_separate_statuses():
    """The eleven weak cases: three answers, not one.

    A loop whose only structural-in-kind evidence is contact with a wall
    may be a boxed riser. Whatever it is, it does not touch the room
    boundary until exposure is established.
    """
    weak = _column(column_evidence=["A_SMALL_CLOSED_LOOP",
                                    "THE_LOOP_MEETS_ESTABLISHED_WALL_FACES"],
                   structural_in_kind=["THE_LOOP_MEETS_ESTABLISHED_WALL_FACES"],
                   architectural_face_present=True)
    # existence may well be satisfied under the owner's bar ...
    assert weak["EXISTENCE"]["COLUMN_EXISTENCE_STATUS"] == \
        co.STRUCTURAL_COLUMN_CONFIRMED
    # ... and it still changes nothing about the room
    assert weak["EXPOSURE"]["EXPOSED_TO_ROOM_STATUS"] == co.EXPOSURE_UNRESOLVED
    assert weak["CLEAR_FACE_OWNERSHIP"][
        "may_deform_the_clear_internal_boundary"] is False

    unresolved = _column(column_evidence=["A_SMALL_CLOSED_LOOP"],
                         structural_in_kind=[],
                         architectural_face_present=True)
    assert unresolved["EXISTENCE"]["COLUMN_EXISTENCE_STATUS"] == \
        co.COLUMN_CANDIDATE_UNRESOLVED
    assert unresolved["CLEAR_FACE_OWNERSHIP"][
        "may_deform_the_clear_internal_boundary"] is False

    # the three statuses are genuinely independent fields
    assert (weak["EXISTENCE"]["COLUMN_EXISTENCE_STATUS"]
            != weak["EXPOSURE"]["EXPOSED_TO_ROOM_STATUS"]
            != weak["CLEAR_FACE_OWNERSHIP"]["CLEAR_FACE_OWNERSHIP_STATUS"])


# ---------------------------------------------------------------- chains
def _three_walls_and_an_opening():
    els = [
        {"kind": bc.MATERIAL_WALL_FACE, "start_mm": (0.0, 0.0),
         "end_mm": (3000.0, 0.0), "object_id": "SOUTH"},
        {"kind": bc.MATERIAL_WALL_FACE, "start_mm": (0.0, 0.0),
         "end_mm": (0.0, 2000.0), "object_id": "WEST"},
        {"kind": bc.MATERIAL_WALL_FACE, "start_mm": (0.0, 2000.0),
         "end_mm": (3000.0, 2000.0), "object_id": "NORTH"},
    ]
    conn = [{"kind": bc.OPEN_EDGE, "start_mm": (3000.0, 2000.0),
             "end_mm": (3000.0, 0.0),
             "why": "no wall band is drawn on this side"}]
    return bc.build(els, connectors=conn)


def test_08_an_open_room_keeps_an_ordered_partial_boundary_chain():
    ch = _three_walls_and_an_opening()
    assert ch["runs"] == 1, "the three walls run into each other"
    assert [e["CHAIN_ELEMENT"] for e in ch["CHAIN"]] == [
        bc.MATERIAL_WALL_FACE, bc.MATERIAL_WALL_FACE, bc.MATERIAL_WALL_FACE,
        bc.OPEN_EDGE]
    assert [e["SEQ"] for e in ch["CHAIN"]] == [1, 2, 3, 4]
    # consecutive material elements actually join
    for a, b in zip(ch["CHAIN"], ch["CHAIN"][1:]):
        if a["CHAIN_ELEMENT"] in bc.MATERIAL_ELEMENTS and \
                b["CHAIN_ELEMENT"] in bc.MATERIAL_ELEMENTS:
            assert a["end_mm"] == b["start_mm"]
    assert ch["CLOSED_BY_DRAWN_MATERIAL"] is False

    st = ss.physical_status(chain=ch)
    assert st["PHYSICAL_GEOMETRY_STATUS"] == ss.ESTABLISHED_OPEN
    assert st["geometry_is_established"] is True, (
        "an established open region is a result, not a failure to close")


def test_09_an_open_edge_contributes_no_material():
    ch = _three_walls_and_an_opening()
    gap = [e for e in ch["CHAIN"] if e["CHAIN_ELEMENT"] == bc.OPEN_EDGE][0]
    assert gap["material_present"] is False
    assert gap["wall_length_contribution_mm"] == 0.0
    assert gap["length_mm"] == 2000.0, "it keeps its extent in the topology"
    assert ch["material_length_mm"] == 8000.0
    bc.assert_no_material_on_a_gap(ch)

    # and a gap that claims material is refused outright
    forged = {"CHAIN": [dict(gap, material_present=True,
                             wall_length_contribution_mm=2000.0)]}
    with pytest.raises(AssertionError):
        bc.assert_no_material_on_a_gap(forged)


def test_10_a_counter_beside_an_open_side_does_not_force_the_room_closed():
    """The Pantry shape: a worktop stands off the open side.

    A counter run is not a wall, and a chain must not quietly use one to
    close the region it happens to stand beside.
    """
    els = [
        {"kind": bc.MATERIAL_WALL_FACE, "start_mm": (0.0, 0.0),
         "end_mm": (3000.0, 0.0)},
        {"kind": bc.MATERIAL_WALL_FACE, "start_mm": (0.0, 0.0),
         "end_mm": (0.0, 2000.0)},
        {"kind": bc.MATERIAL_WALL_FACE, "start_mm": (0.0, 2000.0),
         "end_mm": (3000.0, 2000.0)},
    ]
    conn = [{"kind": bc.OPEN_EDGE, "start_mm": (3000.0, 2000.0),
             "end_mm": (3000.0, 0.0),
             "why": "a counter run stands off this side; nothing is built "
                    "across it"}]
    ch = bc.build(els, connectors=conn)
    assert ch["CLOSED_BY_DRAWN_MATERIAL"] is False
    assert ss.physical_status(chain=ch)["PHYSICAL_GEOMETRY_STATUS"] == \
        ss.ESTABLISHED_OPEN
    # a counter is not a chain element at all: it cannot be smuggled in
    with pytest.raises(ValueError):
        bc.build(els + [{"kind": "COUNTER_EDGE", "start_mm": (3000.0, 0.0),
                         "end_mm": (3000.0, 2000.0)}])


# ------------------------------------------------- relations and identity
def test_11_internal_continuity_is_not_openness():
    """The Kitchen defect, stated generally.

    A region whose own body continues into its own leg has said nothing
    about what lies beyond it. E1.2 turned a non-empty list into
    visual_says_open = True.
    """
    rels = [er.PHYSICAL_BOUNDARY_WALL, er.PHYSICAL_BOUNDARY_WALL,
            er.PHYSICAL_BOUNDARY_DOOR_PORTAL,
            er.INTERNAL_CONTINUITY_WITHIN_CANDIDATE]
    assert er.physically_open(rels) is False
    assert bool(rels) is True, (
        "the list is non-empty: only its CONTENT says the region is closed")

    opened = rels + [er.PHYSICAL_BOUNDARY_OPEN_TO_OTHER_SPACE]
    assert er.physically_open(opened) is True

    subzone = [er.PHYSICAL_BOUNDARY_WALL,
               er.FUNCTIONAL_SUBZONE_BOUNDARY_WITHOUT_WALL]
    assert er.physically_open(subzone) is False

    assert er.physically_open([er.PHYSICAL_BOUNDARY_WALL,
                               er.UNRESOLVED_EDGE_RELATION]) is None


def test_12_a_possible_functional_subzone_cannot_veto_physical_enclosure():
    s = vc.split_statuses([vc.VISUALLY_CONSISTENT,
                           vc.POSSIBLE_FUNCTIONAL_SUBZONE])
    assert s["FUNCTIONAL_STATUSES"] == [vc.POSSIBLE_FUNCTIONAL_SUBZONE]
    assert s["PHYSICAL_STATUSES"] == []
    assert s["vetoes_physical_release"] is False
    assert s["permits_physical_release"] is True

    with pytest.raises(vc.VisualChallengerError):
        vc.assert_no_naming_status_vetoes(
            ["COLD_VISUAL_V2_DOES_NOT_CHALLENGE_THE_BOUNDARY:"
             + vc.POSSIBLE_FUNCTIONAL_SUBZONE])

    f = ss.functional_status(labels_inside=["KITCHEN"], subzone_suggested=True)
    assert f["FUNCTIONAL_IDENTITY_STATUS"] == ss.FUNCTIONAL_SUBZONE_UNRESOLVED
    assert f["blocks_physical_geometry"] is False


def test_13_physical_over_capture_requires_crossing_a_physical_boundary():
    assert vc.POSSIBLE_OVER_CAPTURE in vc.PHYSICAL_STATUSES
    assert vc.POSSIBLE_FUNCTIONAL_SUBZONE not in vc.PHYSICAL_STATUSES
    assert vc.WRONG_FUNCTIONAL_REGION not in vc.PHYSICAL_STATUSES
    # the brief has to say so, or the pass cannot comply
    assert "CROSSES A PHYSICAL BOUNDARY" in vc.V2_BRIEF
    assert "not over-capture" in vc.V2_BRIEF

    over = vc.split_statuses([vc.POSSIBLE_OVER_CAPTURE])
    assert over["vetoes_physical_release"] is True
    assert over["permits_physical_release"] is False


def test_14_physical_and_functional_arbitration_disagree_independently():
    r = ad.arbitrate(
        topology_args=dict(
            a18_says_open=False, cad_open=False,
            edge_relations=[er.PHYSICAL_BOUNDARY_WALL,
                            er.INTERNAL_CONTINUITY_WITHIN_CANDIDATE]),
        role_args=dict(),
        identity_args=dict(labels_inside=["KITCHEN"],
                           v2_subzone_suggested=True))
    assert r[ad.PHYSICAL_TOPOLOGY_ARBITRATION]["STATE"] == \
        ad.TOPOLOGY_AGREED_CLOSED
    assert r[ad.FUNCTIONAL_IDENTITY_ARBITRATION]["STATE"] == \
        ad.IDENTITY_MULTIPLE_ZONES_POSSIBLE
    assert r[ad.FUNCTIONAL_IDENTITY_ARBITRATION][
        "blocks_physical_release"] is False
    assert r["blocks_physical_release"] is False, (
        "confirmed enclosure with unresolved naming is a valid outcome")

    # and the reverse: unresolved topology blocks, whatever the name says
    blocked = ad.arbitrate(
        topology_args=dict(a18_says_open=True, cad_open=False,
                           edge_relations=[]),
        role_args=dict(),
        identity_args=dict(labels_inside=["W.C"]))
    assert blocked[ad.PHYSICAL_TOPOLOGY_ARBITRATION]["STATE"] == \
        ad.TOPOLOGY_UNRESOLVED
    assert blocked["blocks_physical_release"] is True
    assert blocked[ad.FUNCTIONAL_IDENTITY_ARBITRATION]["STATE"] == \
        ad.IDENTITY_AGREED


# ---------------------------------------------------------------- ledger
def test_15_the_ledger_refuses_a_contradictory_decision_record():
    """Frozen E1.2 Kitchen gave three different reasons for one decision."""
    L = dl.Ledger("A_REGION")
    L.gate("PHYSICAL_ENCLOSURE_IS_ESTABLISHED", True, "closed by material")
    L.diagnostic("NO_SITE_FACE_LEAKAGE", dl.FAIL, "the ring is the site face")

    assert L.decision() == dl.RELEASED
    assert L.failed_gates() == []
    assert "NO_SITE_FACE_LEAKAGE" in L.failed_diagnostics()

    # a diagnostic may not be quoted as the reason for a decision
    with pytest.raises(dl.LedgerContradiction) as e:
        L.assert_consistent(failed=["NO_SITE_FACE_LEAKAGE"])
    assert "DIAGNOSTIC_ONLY" in str(e.value)

    # nor may the decision disagree with the gates
    with pytest.raises(dl.LedgerContradiction):
        L.assert_consistent(decision=dl.WITHHELD)

    # nor may the prose be written independently of them
    with pytest.raises(dl.LedgerContradiction):
        L.assert_consistent(why="withheld: NO_SITE_FACE_LEAKAGE")

    # one check, one result
    with pytest.raises(dl.LedgerContradiction):
        L.gate("PHYSICAL_ENCLOSURE_IS_ESTABLISHED", False, "and also not")

    # a real failure produces all three accounts from the same row
    M = dl.Ledger("ANOTHER_REGION")
    M.gate("EVERY_GAP_ON_THE_BOUNDARY_IS_CLASSIFIED", False,
           "1 gap is UNRESOLVED_GAP")
    out = M.record_out()
    assert out["DECISION"] == dl.WITHHELD
    assert out["FAILED_RELEASE_GATES"] == [
        "EVERY_GAP_ON_THE_BOUNDARY_IS_CLASSIFIED"]
    assert "EVERY_GAP_ON_THE_BOUNDARY_IS_CLASSIFIED" in out["WHY"]
    assert "1 gap is UNRESOLVED_GAP" in out["WHY"]


# ------------------------------------------------------- carried forward
def test_16_exact_arcs_remain_unchanged():
    """E1.1 and E1.2 established this. E1.3 must not quietly lose it."""
    class _Arc:
        kind, object_id = "ARC", "CAD-1"
        cx, cy, radius = 1234.5, -6789.25, 2500.0
        start_angle, end_angle = 0.3, 1.9
        length_mm = 2500.0 * (1.9 - 0.3)
        provenance = type("P", (), {"layer": "1", "entity_type": "ARC",
                                    "handle": 1, "block_path": (),
                                    "instance_path": ()})()

    a = _Arc()
    rows = ai.cut(a, [(0.5, ai.CUT_INTERSECTION)])
    assert len(rows) == 2
    assert abs(sum(r.length_mm for r in rows) - a.length_mm) < 1e-6
    for r in rows:
        p = ai.point_at(a, r.t_start)
        assert abs(math.hypot(p[0] - a.cx, p[1] - a.cy) - a.radius) < 1e-6
    seg = cg._as_segment(a, role=cg.CURVED_MATERIAL_FACE)
    rec = seg.record()
    assert rec["centre_mm"] == [1234.5, -6789.25]
    assert rec["radius_mm"] == 2500.0
    assert rec["analytical_geometry"] == "THE_ORIGINAL_CURVE"
    # and a curve is a material chain element in its own right
    assert bc.CURVED_MATERIAL_FACE in bc.MATERIAL_ELEMENTS


def test_17_site_context_labels_remain_outside_the_denominator():
    assert lo.SITE_CONTEXT_ANNOTATION not in lo.IN_THE_COMPLETENESS_DENOMINATOR
    assert lo.PHYSICAL_SPACE_LABEL in lo.IN_THE_COMPLETENESS_DENOMINATOR
    assert lo.FUNCTIONAL_ZONE_LABEL in lo.IN_THE_COMPLETENESS_DENOMINATOR
    # and nothing in E1.3 quietly re-admits them
    assert len(lo.IN_THE_COMPLETENESS_DENOMINATOR) == 2


def test_18_interval_role_evidence_remains_local():
    """A partner on 600 mm of a 4 m line says nothing about the other 3.4 m."""
    assert ai.EVIDENCE_LICENSES_ONLY_ITS_OWN_INTERVAL
    assert ai.WHOLE_ENTITY_PROMOTION_IS_BANNED
    # collinearity is still a diagnostic tag, not an establishing one
    assert ir.EV_COLLINEAR_GEOMETRIC not in ir.ESTABLISHING_EVIDENCE
    only = ai.Interval(interval_id="IV", parent_object_id="O",
                       length_mm=1000.0, role=ir.UNKNOWN,
                       evidence=(ir.EV_COLLINEAR_GEOMETRIC,))
    assert ir.established_by_collinearity_alone(only) is True
    backed = ai.Interval(interval_id="IV2", parent_object_id="O2",
                         length_mm=250.0, role=ir.COLUMN,
                         evidence=(ir.EV_COLLINEAR_GEOMETRIC,
                                   ir.EV_COL_LAYER_IS_STRUCTURAL,
                                   ir.EV_COL_LOOP))
    assert ir.established_by_collinearity_alone(backed) is False


def test_19_the_vocabulary_is_complete():
    assert len(er.EDGE_RELATIONS) == 8
    assert len(go.GAP_CLASSES) == 6
    assert len(co.EXISTENCE_STATUSES) == 3
    assert len(co.EXPOSURE_STATUSES) == 3
    assert len(co.OWNERSHIP_STATUSES) == 3
    assert len(bc.CHAIN_ELEMENTS) == 8
    assert len(ss.PHYSICAL_GEOMETRY_STATUSES) == 5
    assert len(ss.FUNCTIONAL_IDENTITY_STATUSES) == 5
    assert len(ad.DIMENSIONS) == 3
    assert len(dl.KINDS) == 2
