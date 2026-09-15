"""§1-§7: one doorway, three models, and no trading one for another.

Round 3's "reopening every portal dropped recall from 75% to 58.3%" was the
symptom of a conflation. These tests assert MATERIAL connectivity, ROOM
PARTITION and NAVIGABILITY separately for every case, so a change that buys
one with another fails instead of looking like progress.
"""

import pytest

from engine import portal_topology_fixtures as fx
from engine import space_topologies as st
from engine.evidence_tiers import (PORTAL_DOCUMENT_VALIDATED,
                                   PORTAL_DRAWING_VALIDATED,
                                   PORTAL_UNVALIDATED)


def _answers(case):
    return st.answer_pair(case.space_a, case.space_b,
                          portal=fx.boundary_of(case),
                          material_between=case.material_between)


# --- the eleven cases, three assertions each -----------------------------

@pytest.mark.parametrize("case", fx.cases(), ids=lambda c: c.name)
def test_all_three_answers_independently(case):
    got = _answers(case)
    assert got[st.MATERIAL_GEOMETRY]["connected"] == (
        case.expect_material_connected), case.note
    assert got[st.ROOM_PARTITION_TOPOLOGY]["connected"] == (
        not case.expect_rooms_distinct), case.note
    assert got[st.NAVIGABLE_FREE_SPACE]["connected"] == (
        case.expect_navigable), case.note
    assert got[st.ROOM_PARTITION_TOPOLOGY]["status"] == (
        case.expect_partition_status), case.note


def test_a_bedroom_and_its_ensuite_hold_all_three_at_once():
    """§7's worked example: three different answers, none contradicting."""
    got = _answers(fx.bedroom_to_ensuite())
    assert got[st.MATERIAL_GEOMETRY]["connected"] is True
    assert got[st.ROOM_PARTITION_TOPOLOGY]["connected"] is False
    assert got[st.NAVIGABLE_FREE_SPACE]["connected"] is True


# --- §3 the generalisation rule ------------------------------------------

def test_door_ink_that_closes_pixels_gives_the_same_partition_as_ink_that_does_not():
    """The rule that makes room topology travel between architects."""
    closes = fx.leaf_ink_touching_both_jambs()
    floats = fx.graphics_that_do_not_touch()
    assert closes.door_ink_closes_pixels is True
    assert floats.door_ink_closes_pixels is False

    a = _answers(closes)[st.ROOM_PARTITION_TOPOLOGY]
    b = _answers(floats)[st.ROOM_PARTITION_TOPOLOGY]
    assert a["connected"] == b["connected"]
    assert a["status"] == b["status"]


def test_the_record_says_why_door_ink_is_not_a_boundary():
    rec = st.build([]).record()
    why = rec["why_door_ink_is_not_a_boundary"]
    assert "EVIDENCE that a portal exists" in why
    assert "does not travel between architects" in why


def test_no_model_uses_door_ink_at_all():
    """Ink cannot reach the partition: there is nowhere for it to enter."""
    import inspect
    src = inspect.getsource(st)
    for forbidden in ("mask", "pixel", "ink", "raster"):
        assert f"{forbidden} =" not in src
    params = set(inspect.signature(st.answer_pair).parameters)
    assert params == {"space_a", "space_b", "portal", "material_between"}


# --- §4 zero material ----------------------------------------------------

def test_a_partition_boundary_carries_zero_material():
    b = fx.boundary_of(fx.bedroom_to_corridor())
    assert b.material_present_length_mm == 0.0
    assert b.opening_length_mm == 900.0
    assert b.space_boundary_length_mm == 900.0
    assert b.host_wall_gross_length_mm == 900.0


def test_the_four_length_measures_follow_the_ontology():
    rec = fx.boundary_of(fx.double_doors()).record()
    got = rec["lengths_mm"]
    assert got["MATERIAL_PRESENT_LENGTH"] == 0.0
    assert got["OPENING_LENGTH"] == 1800.0
    assert got["SPACE_BOUNDARY_LENGTH"] == 1800.0
    assert got["HOST_WALL_GROSS_LENGTH"] == 1800.0


def test_a_partition_boundary_may_not_enter_the_material_model():
    rec = fx.boundary_of(fx.bedroom_to_corridor()).record()
    assert rec["participates_in"] == st.ROOM_PARTITION_TOPOLOGY
    assert st.MATERIAL_GEOMETRY in rec["never_participates_in"]
    assert "zero material" in rec["never_participates_in"]


# --- §5 evidence controls authority, not existence -----------------------

def test_an_unvalidated_portal_still_separates_the_rooms():
    """§5: do not solve uncertainty by merging the two rooms."""
    got = _answers(fx.door_without_swing_arc())
    assert got[st.ROOM_PARTITION_TOPOLOGY]["connected"] is False
    assert got[st.ROOM_PARTITION_TOPOLOGY]["status"] == (
        st.PARTITION_DIAGNOSTIC)


def test_a_validated_portal_makes_the_partition_releasable():
    got = _answers(fx.bedroom_to_corridor())
    assert got[st.ROOM_PARTITION_TOPOLOGY]["status"] == (
        st.PARTITION_RELEASABLE)


def test_no_portal_and_no_material_is_unresolved_not_two_rooms():
    got = _answers(fx.unresolved_gap_with_no_portal_evidence())
    assert got[st.ROOM_PARTITION_TOPOLOGY]["status"] == (
        st.PARTITION_UNRESOLVED)
    assert got[st.ROOM_PARTITION_TOPOLOGY]["connected"] is True
    assert "may not be released as either" in got[
        st.ROOM_PARTITION_TOPOLOGY]["basis"]


def test_open_plan_with_no_portal_is_one_space():
    """Two labels do not create a boundary."""
    got = _answers(fx.open_plan_with_no_portal_boundary())
    assert got[st.ROOM_PARTITION_TOPOLOGY]["connected"] is True


def test_the_weakest_portal_sets_the_partition_status():
    strong = fx.boundary_of(fx.bedroom_to_corridor())
    weak = fx.boundary_of(fx.door_without_swing_arc())
    assert st.partition_status([strong])["status"] == (
        st.PARTITION_RELEASABLE)
    got = st.partition_status([strong, weak])
    assert got["status"] == st.PARTITION_DIAGNOSTIC
    assert got["weakest_grade"] == PORTAL_UNVALIDATED
    assert "merge the two rooms" in got["what_uncertainty_does_not_do"]


def test_material_between_needs_no_portal_to_keep_rooms_distinct():
    got = st.answer_pair("A", "B", portal=None, material_between=True)
    assert got[st.MATERIAL_GEOMETRY]["connected"] is False
    assert got[st.ROOM_PARTITION_TOPOLOGY]["connected"] is False
    assert got[st.NAVIGABLE_FREE_SPACE]["connected"] is False


# --- the report ----------------------------------------------------------

def test_the_report_counts_the_three_models_separately():
    rows = [(c.space_a, c.space_b, fx.boundary_of(c), c.material_between)
            for c in fx.cases()]
    bounds = [fx.boundary_of(c) for c in fx.cases()
              if fx.boundary_of(c) is not None]
    rec = st.build(rows, boundaries=bounds).record()
    assert rec["pairs"] == 11
    assert rec["rooms_kept_distinct"] == 9
    assert rec["navigable_connections"] == 11
    assert rec["total_partition_material_length_m"] == 0.0
    assert rec["total_partition_boundary_length_m"] > 0
    assert "one binary portal operation cannot serve three" in rec[
        "the_conflation_this_prevents"]


def test_navigability_is_barred_from_defining_room_identity():
    rec = st.build([]).record()
    assert "may NEVER define room identity" in rec[
        "what_each_model_is_for"][st.NAVIGABLE_FREE_SPACE]


def test_the_hash_changes_when_a_grade_changes():
    a = st.build([], boundaries=[fx.boundary_of(fx.bedroom_to_corridor())])
    weak = fx.boundary_of(fx.door_without_swing_arc())
    b = st.build([], boundaries=[weak])
    assert a.output_hash != b.output_hash
