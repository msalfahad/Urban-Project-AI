"""E32 — comparison is arithmetic on fields, and agreement is not proof."""

from __future__ import annotations

import pytest

from agents.a1_extractor.semantic import SemanticOutput, SpaceSemantics
from engine.semantic_compare import (AGREE_HIGH_CONFIDENCE, AGREE_LOW_CONFIDENCE,
                                     CRITICAL, DISAGREE, HIGH, LOW, MEDIUM,
                                     MISSING_A1, MISSING_A2, SOURCE_CONFLICT,
                                     compare, compare_space, label_materiality)
from agents.a1_extractor.tests.registry_fixture import REG
from engine.trade_rules import TradeRuleSet

RULES = TradeRuleSet.load("data/trade_rules/23010_ceramic.json")


def s(**kw) -> SpaceSemantics:
    base = dict(space_id="X", semantic_label="BEDROOM", label_source="PDF_TEXT",
                semantic_label_confidence="HIGH",
                confidence_basis="drawing text entity inside the polygon",
                scope_status="IN_SCOPE", scope_confidence="HIGH",
                scope_basis="named in the owner brief",
                apartment_id="APT-001", apartment_membership_confidence="HIGH",
                apartment_basis="access from the main landing")
    base.update(kw)
    return SpaceSemantics(**base)


# Every comparison in this file runs against the canonical registry, because a
# comparison without one is the Run 0 defect: free-text identifiers checked by
# string equality. The wrappers keep that from being something a test can forget.
_compare_space, _compare = compare_space, compare


def compare_space(a1, a2, **kw):          # noqa: F811 — deliberate shadow
    kw.setdefault("registry", REG)
    return _compare_space(a1, a2, **kw)


def compare(a1, a2, **kw):                # noqa: F811 — deliberate shadow
    kw.setdefault("registry", REG)
    return _compare(a1, a2, **kw)


def test_identical_strong_records_agree():
    assert compare_space(s(), s()).verdict == AGREE_HIGH_CONFIDENCE


def test_agreement_on_weak_evidence_is_not_a_pass():
    """Two LOW-confidence agents saying the same thing prove nothing."""
    weak = dict(semantic_label_confidence="LOW", label_source="VISION_MODEL")
    c = compare_space(s(**weak), s(**weak))
    assert c.verdict == AGREE_LOW_CONFIDENCE
    assert not c.is_pass_candidate
    assert "weak evidence" in c.source_conflict


def test_agreement_carrying_an_unresolved_conflict_is_not_a_pass():
    c = compare_space(s(semantic_conflicts=["old takeoff calls this مطبخ"]), s())
    assert c.verdict == AGREE_LOW_CONFIDENCE and not c.is_pass_candidate


def test_two_agents_agreeing_against_a_schedule_are_outvoted():
    """A1=BATHROOM, A2=BATHROOM, schedule=STORE is a conflict, not agreement."""
    c = compare_space(s(semantic_label="BATHROOM"), s(semantic_label="BATHROOM"),
                      schedule_label="STORE")
    assert c.verdict == SOURCE_CONFLICT
    assert "not proof" in c.source_conflict
    assert not c.is_pass_candidate


def test_a_missing_space_on_either_side_is_critical():
    assert compare_space(None, s()).verdict == MISSING_A1
    assert compare_space(s(), None).verdict == MISSING_A2
    assert compare_space(None, s()).materiality == CRITICAL


def test_scope_disagreement_is_critical():
    c = compare_space(s(scope_status="IN_SCOPE"), s(scope_status="OUT_OF_SCOPE"))
    assert c.verdict == DISAGREE and c.materiality == CRITICAL


def test_wrong_apartment_is_critical():
    c = compare_space(s(apartment_id="APT-001"), s(apartment_id="APT-002"))
    assert c.materiality == CRITICAL


def test_shaft_versus_a_room_is_critical():
    c = compare_space(s(semantic_label="SHAFT"), s(semantic_label="WASHROOM"))
    assert c.materiality == CRITICAL
    assert "not usable floor" in c.diffs[0].note


def test_labels_with_identical_trade_consequences_are_low_materiality():
    """BEDROOM and SALON both take ceramic floor and no ceramic wall."""
    mat, note = label_materiality("BEDROOM", "SALON", RULES)
    assert mat == LOW and "identical trade consequences" in note


def test_a_label_with_no_trade_rule_is_high_not_low():
    """Unknown consequence is not the same as no consequence."""
    mat, note = label_materiality("BEDROOM", "ROOF_ROOM", RULES)
    assert mat == HIGH and "consequence unknown" in note


def test_labels_with_different_trade_consequences_are_high():
    mat, _ = label_materiality("BEDROOM", "BATHROOM", RULES)
    assert mat == HIGH


def test_materiality_never_resolves_the_disagreement():
    """A cheap disagreement is still a disagreement."""
    c = compare_space(s(semantic_label="BEDROOM"), s(semantic_label="SALON"),
                      rules=RULES)
    assert c.verdict == DISAGREE
    assert not c.is_pass_candidate


def test_confidence_does_not_pick_a_winner():
    """The more certain model does not win. Both readings stay visible."""
    c = compare_space(s(semantic_label="BEDROOM", semantic_label_confidence="HIGH"),
                      s(semantic_label="BATHROOM", semantic_label_confidence="LOW"),
                      rules=RULES)
    assert c.verdict == DISAGREE
    assert c.diffs[0].a1 == "BEDROOM" and c.diffs[0].a2 == "BATHROOM"


def out(*spaces) -> SemanticOutput:
    return SemanticOutput(spaces=list(spaces))


def test_report_queues_worst_first_and_never_hides_a_row():
    rep = compare(
        out(s(space_id="A"), s(space_id="B", scope_status="IN_SCOPE"),
            s(space_id="C", semantic_label="BEDROOM")),
        out(s(space_id="A"), s(space_id="B", scope_status="OUT_OF_SCOPE"),
            s(space_id="C", semantic_label="SALON")),
        rules=RULES)
    assert len(rep.rows) == 3
    assert rep.queue()[0].space_id == "B"          # CRITICAL first
    assert len(rep.pass_candidates) == 1
    assert 0 < rep.disagreement_rate < 1


def test_a_space_only_one_agent_saw_still_appears():
    rep = compare(out(s(space_id="A")), out(s(space_id="A"), s(space_id="GHOST")))
    assert {r.space_id for r in rep.rows} == {"A", "GHOST"}
    assert rep.by_verdict(MISSING_A1)[0].space_id == "GHOST"


def test_comparing_nothing_raises():
    with pytest.raises(ValueError, match="nothing to compare"):
        compare_space(None, None)


# ------------------------------------------------- a label never moves geometry
def test_a_semantic_disagreement_does_not_recalculate_the_polygon():
    """SPACE-021 is 3.59 m2. A1 says WASHROOM, A2 says SERVICE_ROOM.

    That is a SEMANTIC_CONFLICT and nothing else. The area is established by
    E23 from the drawing's vector geometry and no label can move it.
    """
    from decimal import Decimal as D

    from engine.quantities import SpaceInputs, assemble
    from engine.release import apply, route

    geometry = D("3.59")
    sp = SpaceInputs("SPACE-021", "2F", "WASHROOM", "A1", "DISPUTED",
                     floor_area_m2=geometry, gross_wall_perimeter_m=D("10.53"),
                     geometry_source="E23", geometry_basis="CLEAR_INTERNAL_FINISH_FACE",
                     drawing="AR-00", drawing_revision="MAR.2023")
    before = assemble("23010", [sp], [RULES])
    floor_before = next(q.value for q in before if q.element == "FLOOR")

    conflict = compare_space(s(space_id="SPACE-021", semantic_label="WASHROOM"),
                             s(space_id="SPACE-021", semantic_label="SERVICE_ROOM"),
                             rules=RULES)
    assert conflict.verdict == DISAGREE
    assert not conflict.is_pass_candidate

    after = apply(before, route(before, comparisons={"SPACE-021": conflict}))
    floor_after = next(q.value for q in after if q.element == "FLOOR")
    assert floor_before == floor_after == geometry, "a label moved the geometry"
    # the conflict stops the quantity being released, it does not change it
    assert all(not q.releasable for q in after)


def test_label_does_not_imply_scope_or_finish():
    """TERRACE is a space type. Whether it is excluded is scope_status' job."""
    included = s(semantic_label="TERRACE", scope_status="IN_SCOPE")
    excluded = s(space_id="X", semantic_label="TERRACE", scope_status="OUT_OF_SCOPE")
    c = compare_space(included, excluded, rules=RULES)
    assert c.verdict == DISAGREE and c.materiality == CRITICAL
    # the label agreed; only the scope differed
    assert [d.field_name for d in c.diffs] == ["scope_status"]


# --- what a project cannot define, it does not get scored on -----------------

def test_a_zone_difference_is_not_scored_when_no_ontology_exists():
    """Run 0 called this 100% disagreement. It was a missing definition."""
    from engine.semantic_compare import comparable_fields
    fields, excluded = comparable_fields(REG)
    assert "zone_id" in excluded and "zone_id" not in fields
    assert "no zone ontology" in excluded["zone_id"]
    c = compare_space(s(zone_id="UNKNOWN"), s(zone_id="UNKNOWN"))
    assert c.verdict == AGREE_HIGH_CONFIDENCE
    assert "zone_id" in c.excluded


def test_a_zone_difference_is_scored_where_an_ontology_does_exist():
    from agents.a1_extractor.tests.registry_fixture import ZONED
    c = compare_space(s(zone_id="ZONE-001"), s(zone_id="ZONE-002"), registry=ZONED)
    assert c.verdict == DISAGREE
    assert [d.field_name for d in c.diffs] == ["zone_id"]


def test_without_a_registry_no_identifier_is_scored_at_all():
    """Fail closed: an unvalidated identifier is worse than an absent one."""
    from engine.semantic_compare import comparable_fields
    fields, excluded = comparable_fields(None)
    assert set(excluded) == {"apartment_id", "zone_id"}
    assert "string equality" in excluded["apartment_id"]


def test_trade_relevance_left_this_comparison():
    """E27 owns trade relevance; scoring A1 against A2 on it measured nothing."""
    from engine.semantic_compare import FIELD_MATERIALITY
    assert "trade_relevance" not in FIELD_MATERIALITY


def test_membership_sets_see_through_a_renamed_group():
    """The migration diagnostic: same rooms, different names for the group."""
    from engine.semantic_compare import membership_diff
    a1 = SemanticOutput(spaces=[s(space_id="A", apartment_id="APT-001"),
                                s(space_id="B", apartment_id="APT-002")])
    a2 = SemanticOutput(spaces=[s(space_id="A", apartment_id="APT-002"),
                                s(space_id="B", apartment_id="APT-001")])
    d = membership_diff(a1, a2, "APARTMENT")
    assert d.same_partition                      # identical carve-up
    assert sorted(d.identical_sets) == [("APT-001", "APT-002"), ("APT-002", "APT-001")]


def test_membership_sets_still_catch_a_real_regrouping():
    from engine.semantic_compare import membership_diff
    a1 = SemanticOutput(spaces=[s(space_id="A", apartment_id="APT-001"),
                                s(space_id="B", apartment_id="APT-001")])
    a2 = SemanticOutput(spaces=[s(space_id="A", apartment_id="APT-001"),
                                s(space_id="B", apartment_id="APT-002")])
    d = membership_diff(a1, a2, "APARTMENT")
    assert not d.same_partition
