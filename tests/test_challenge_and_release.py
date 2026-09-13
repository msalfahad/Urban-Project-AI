"""A2 challenger and E33 release control."""

from __future__ import annotations

from decimal import Decimal as D

import pytest

from agents.a1_extractor.semantic import SpaceSemantics
from agents.a2_reviewer.challenge import (BLOCK, CHALLENGE_HIGH, CHALLENGE_LOW,
                                          PASS, Challenge, ChallengeError,
                                          ChallengeOutput)
from engine.quantities import (AUTO_VALIDATED, BLOCKED, REVIEW_REQUIRED,
                               SpaceInputs, assemble, total)
from engine.release import apply, decide, route
from engine.semantic_compare import compare_space
from engine.trade_rules import TradeRuleSet

CERAMIC = TradeRuleSet.load("data/trade_rules/23010_ceramic.json")


def sem(**kw) -> SpaceSemantics:
    base = dict(space_id="BTH-03", semantic_label="BATHROOM", label_source="PDF_TEXT",
                label_confidence="HIGH", confidence_basis="text + polygon + schedule",
                scope_status="IN_SCOPE")
    base.update(kw)
    return SpaceSemantics(**base)


def space(**kw) -> SpaceInputs:
    base = dict(space_id="BTH-03", floor_id="2F", semantic_label="BATHROOM",
                semantic_source="A1+A2", semantic_status="VALIDATED",
                floor_area_m2=D("4.53"), gross_wall_perimeter_m=D("8.60"),
                geometry_source="E23", geometry_basis="CLEAR_INTERNAL_FINISH_FACE",
                drawing="AR-00", drawing_revision="MAR.2023")
    base.update(kw)
    return SpaceInputs(**base)


def chal(**kw) -> Challenge:
    base = dict(challenge_id="C1", project_id="23010", space_id="BTH-03",
                challenge_type="WRONG_SCOPE", severity=CHALLENGE_HIGH,
                evidence="AR-00 shows it outside the marked apartment",
                reason="scope brief excludes this zone",
                recommended_route="HUMAN_REVIEW")
    base.update(kw)
    return Challenge(**base)


# ------------------------------------------------------------- challenger
def test_a_challenge_cannot_propose_a_replacement_number():
    with pytest.raises(ChallengeError, match="never proposes a number"):
        ChallengeOutput.from_dict({"challenges": [
            {"challenge_id": "C1", "corrected_value": 5.1}]})


def test_a_challenge_without_evidence_is_refused():
    with pytest.raises(ChallengeError, match="is an opinion"):
        chal(evidence="  ").validate()


def test_a_verdict_cannot_understate_its_own_findings():
    with pytest.raises(ChallengeError, match="cannot understate"):
        ChallengeOutput(verdict=PASS, challenges=[chal(severity=BLOCK)]).validate()


def test_an_unknown_challenge_type_is_refused():
    with pytest.raises(ChallengeError, match="not one of"):
        chal(challenge_type="VIBES").validate()


def test_high_and_block_stop_release_and_low_does_not():
    assert chal(severity=CHALLENGE_HIGH).blocks_release
    assert chal(severity=BLOCK).blocks_release
    assert not chal(severity=CHALLENGE_LOW).blocks_release


# ---------------------------------------------------------------- release
def test_a_clean_quantity_auto_validates():
    q = assemble("23010", [space()], [CERAMIC])[0]
    d = decide(q, comparison=compare_space(sem(), sem()), approved_revision="MAR.2023")
    assert d.status == AUTO_VALIDATED and d.released


def test_weak_agreement_does_not_auto_validate():
    """AGREE_LOW_CONFIDENCE is exactly the case that must not slip through."""
    weak = dict(label_confidence="LOW", label_source="VISION_MODEL")
    q = assemble("23010", [space()], [CERAMIC])[0]
    d = decide(q, comparison=compare_space(sem(**weak), sem(**weak)),
               approved_revision="MAR.2023")
    assert d.status == REVIEW_REQUIRED
    assert "AGREE_LOW_CONFIDENCE" in d.reasons[0]


def test_a_missing_comparison_blocks():
    q = assemble("23010", [space()], [CERAMIC])[0]
    assert decide(q, comparison=None).status == BLOCKED


def test_the_wrong_revision_blocks():
    q = assemble("23010", [space(drawing_revision="JAN.2023")], [CERAMIC])[0]
    d = decide(q, comparison=compare_space(sem(), sem()), approved_revision="MAR.2023")
    assert d.status == BLOCKED and "off revision" in d.reasons[0]


def test_geometry_without_a_basis_goes_to_review():
    q = assemble("23010", [space(geometry_basis="")], [CERAMIC])[0]
    d = decide(q, comparison=compare_space(sem(), sem()), approved_revision="MAR.2023")
    assert d.status == REVIEW_REQUIRED
    assert any("measurement basis" in r for r in d.reasons)


def test_a_missing_trade_rule_goes_to_review():
    q = assemble("23010", [space()], [CERAMIC])[0]
    d = decide(q, comparison=compare_space(sem(), sem()), rule_exists=False,
               approved_revision="MAR.2023")
    assert d.status == REVIEW_REQUIRED


def test_a_blocking_challenge_stops_the_quantity():
    q = assemble("23010", [space()], [CERAMIC])[0]
    d = decide(q, comparison=compare_space(sem(), sem()),
               challenges=[chal(severity=BLOCK)], approved_revision="MAR.2023")
    assert d.status == BLOCKED


def test_unreleased_quantities_never_reach_the_boq():
    qs = assemble("23010", [space()], [CERAMIC])
    weak = dict(label_confidence="LOW", label_source="VISION_MODEL")
    q = route(qs, comparisons={"BTH-03": compare_space(sem(**weak), sem(**weak))},
              approved_revision="MAR.2023")
    assert total(apply(qs, q)) == D(0)


def test_the_queue_is_ordered_worst_first_and_reports_a_review_rate():
    qs = assemble("23010", [space(), space(space_id="BTH-04")], [CERAMIC])
    q = route(qs, comparisons={
        "BTH-03": compare_space(sem(), sem()),
        "BTH-04": compare_space(sem(space_id="BTH-04", scope_status="IN_SCOPE"),
                                sem(space_id="BTH-04", scope_status="OUT_OF_SCOPE")),
    }, approved_revision="MAR.2023")
    assert q.ordered()[0].space_id == "BTH-04"
    assert 0 < q.human_review_rate < 1


def test_routing_never_changes_a_value():
    qs = assemble("23010", [space()], [CERAMIC])
    stamped = apply(qs, route(qs, comparisons={"BTH-03": None}))
    assert [q.value for q in stamped] == [q.value for q in qs]
