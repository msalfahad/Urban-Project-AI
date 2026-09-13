"""E32 — comparison is arithmetic on fields, and agreement is not proof."""

from __future__ import annotations

import pytest

from agents.a1_extractor.semantic import SemanticOutput, SpaceSemantics
from engine.semantic_compare import (AGREE_HIGH_CONFIDENCE, AGREE_LOW_CONFIDENCE,
                                     CRITICAL, DISAGREE, HIGH, LOW, MEDIUM,
                                     MISSING_A1, MISSING_A2, SOURCE_CONFLICT,
                                     compare, compare_space, label_materiality)
from engine.trade_rules import TradeRuleSet

RULES = TradeRuleSet.load("data/trade_rules/23010_ceramic.json")


def s(**kw) -> SpaceSemantics:
    base = dict(space_id="X", semantic_label="BEDROOM", label_source="PDF_TEXT",
                label_confidence="HIGH", confidence_basis="text + polygon + schedule",
                scope_status="IN_SCOPE")
    base.update(kw)
    return SpaceSemantics(**base)


def test_identical_strong_records_agree():
    assert compare_space(s(), s()).verdict == AGREE_HIGH_CONFIDENCE


def test_agreement_on_weak_evidence_is_not_a_pass():
    """Two LOW-confidence agents saying the same thing prove nothing."""
    weak = dict(label_confidence="LOW", label_source="VISION_MODEL")
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
    c = compare_space(s(apartment_id="RIGHT"), s(apartment_id="LEFT"))
    assert c.materiality == CRITICAL


def test_shaft_versus_a_room_is_critical():
    c = compare_space(s(semantic_label="SHAFT"), s(semantic_label="WASHROOM"))
    assert c.materiality == CRITICAL
    assert "not usable floor" in c.diffs[0].note


def test_labels_with_identical_trade_consequences_are_low_materiality():
    mat, note = label_materiality("BEDROOM", "SALOON", RULES)
    assert mat == LOW and "identical trade consequences" in note


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
    c = compare_space(s(semantic_label="BEDROOM", label_confidence="HIGH"),
                      s(semantic_label="BATHROOM", label_confidence="LOW"),
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
