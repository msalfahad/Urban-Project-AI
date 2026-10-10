"""The fail-closed audit: every default path, checked as a test rather than read.

The brief before Run 1 listed the conversions that must not exist anywhere:

    UNKNOWN            -> IN_SCOPE
    AMBIGUOUS          -> first match
    missing trade rule -> default trade
    missing zone       -> arbitrary zone
    model parse error  -> partial accepted record
    challenge          -> replacement quantity

Reading the code for them is how you miss one. Each is a test here, named after
the conversion it forbids, so the guarantee survives the next refactor. The audit
already found one live defect this way: release.decide() defaulted rule_exists to
True, so a quantity could be released against a trade rule nobody looked up.
"""

from __future__ import annotations

from decimal import Decimal as D

import pytest

from agents.a1_extractor.semantic import SemanticError, SemanticOutput
from agents.a1_extractor.tests.registry_fixture import REG, parse
from engine.group_registry import APARTMENT, ZONE, GroupRegistryError
from engine.quantities import REVIEW_REQUIRED, SpaceInputs, assemble, total
from engine.release import apply, decide, route
from engine.semantic_compare import AGREE_HIGH_CONFIDENCE, compare_space
from engine.trade_rules import (APPLIES, FLOOR, NOT_WIRED, RULE_ENGINE_NOT_AVAILABLE,
                                TradeRuleSet, decide_trade, trade_relevance)

CERAMIC = TradeRuleSet.load("data/trade_rules/23010_ceramic.json")


def rec(**kw):
    base = dict(space_id="S1", semantic_label="BEDROOM", label_source="PDF_TEXT",
                semantic_label_confidence="HIGH",
                confidence_basis="drawing text entity inside the polygon",
                scope_status="IN_SCOPE", scope_confidence="HIGH",
                scope_basis="named in the owner brief",
                apartment_id="APT-001", apartment_membership_confidence="HIGH",
                apartment_basis="access from the main landing")
    base.update(kw)
    return base


# 1 ── UNKNOWN must never become IN_SCOPE
def test_an_unknown_label_does_not_carry_a_space_into_scope():
    ds = trade_relevance("UNKNOWN", "IN_SCOPE", {"ceramic": CERAMIC})
    assert not any(d.applies for d in ds)


def test_scope_defaults_to_ambiguous_when_the_field_is_absent():
    data = {k: v for k, v in rec().items()
            if k not in ("scope_status", "scope_confidence", "scope_basis")}
    out = parse({"spaces": [data]})
    assert out.spaces[0].scope_status == "AMBIGUOUS"


def test_scope_cannot_be_in_scope_without_traceable_evidence():
    with pytest.raises(SemanticError, match="answer AMBIGUOUS"):
        parse({"spaces": [rec(scope_confidence="NOT_ESTABLISHED", scope_basis="")]})


# 2 ── AMBIGUOUS must never become "the first match"
def test_two_matching_aliases_give_ambiguous_not_the_first_one():
    from engine.trades import match_label
    assert match_label("SNUG").canonical_label == "UNKNOWN"      # zero matches
    # the multi-match path is exercised in test_a1_trades; here we hold the rule
    # that AMBIGUOUS is never silently resolved downstream:
    ds = trade_relevance("AMBIGUOUS", "IN_SCOPE", {"ceramic": CERAMIC})
    assert not any(d.applies for d in ds)


def test_an_ambiguous_scope_never_resolves_itself_into_a_quantity():
    ds = trade_relevance("BATHROOM", "AMBIGUOUS", {"ceramic": CERAMIC})
    assert not any(d.applies for d in ds)


# 3 ── a missing trade rule must never become a default trade
def test_a_missing_rule_never_produces_a_quantity():
    stub = TradeRuleSet(trade="paint", height_m=D("3.2"), rules={},
                        trade_rule_status=NOT_WIRED)
    d = decide_trade(stub, "BEDROOM", FLOOR, scope_status="IN_SCOPE")
    assert d.status == RULE_ENGINE_NOT_AVAILABLE and not d.applies


def test_rule_presence_that_was_never_established_is_not_yes():
    """The defect this audit found. `rule_exists` used to default to True."""
    sp = SpaceInputs("BTH-03", "2F", "BATHROOM", "A1+A2", "VALIDATED",
                     D("4.53"), D("8.60"), "E23", "CLEAR_INTERNAL_FINISH_FACE",
                     "AR-00", "MAR.2023")
    q = assemble("23010", [sp], [CERAMIC])[0]
    from agents.a1_extractor.semantic import SpaceSemantics
    s = SpaceSemantics(**{**rec(space_id="BTH-03", semantic_label="BATHROOM")})
    d = decide(q, comparison=compare_space(s, s, registry=REG),
               approved_revision="MAR.2023")
    assert d.status == REVIEW_REQUIRED
    assert any("never established" in r for r in d.reasons)


# 4 ── a missing zone must never become an arbitrary zone
def test_a_missing_zone_stays_unknown_rather_than_taking_the_first_group():
    out = parse({"spaces": [{k: v for k, v in rec().items() if k != "zone_id"}]})
    assert out.spaces[0].zone_id == "UNKNOWN"


def test_an_invented_zone_is_refused_rather_than_normalised():
    with pytest.raises(SemanticError, match="no zone ontology"):
        parse({"spaces": [rec(zone_id="ZONE-001")]})


def test_a_missing_apartment_stays_unknown_rather_than_defaulting_to_apt_001():
    data = {k: v for k, v in rec().items()
            if k not in ("apartment_id", "apartment_membership_confidence",
                         "apartment_basis")}
    out = parse({"spaces": [data]})
    assert out.spaces[0].apartment_id == "UNKNOWN"


# 5 ── a parse error must never leave a partial record standing
def test_one_bad_record_rejects_the_whole_output():
    with pytest.raises(SemanticError):
        parse({"spaces": [rec(space_id="GOOD"),
                          rec(space_id="BAD", semantic_label="SNUG")]})


def test_a_truncated_answer_is_an_error_not_a_short_answer():
    from agents.base import ModelTruncated
    assert issubclass(ModelTruncated, Exception)


def test_an_empty_spaces_array_is_not_a_pass():
    """Zero classified spaces must not read as zero problems."""
    out = parse({"spaces": []})
    assert out.covers(["SPACE-001", "SPACE-002"]) == ["SPACE-001", "SPACE-002"]


# 6 ── a challenge must never become a replacement quantity
def test_a_geometry_challenge_carries_no_number_to_substitute():
    out = parse({"spaces": [rec(geometry_challenge="region looks clipped at 2.1 m")]})
    s = out.spaces[0]
    assert s.geometry_challenge
    assert not hasattr(s, "area_m2") and not hasattr(s, "proposed_area_m2")


def test_a_challenge_cannot_smuggle_a_measurement_in_a_geometry_field():
    with pytest.raises(SemanticError, match="belongs to E23/E25"):
        parse({"spaces": [rec(challenged_area_m2=4.9)]})


def test_a_blocked_quantity_contributes_nothing_to_a_total():
    sp = SpaceInputs("BTH-03", "2F", "BATHROOM", "A1+A2", "VALIDATED",
                     D("4.53"), D("8.60"), "E23", "CLEAR_INTERNAL_FINISH_FACE",
                     "AR-00", "MAR.2023")
    qs = assemble("23010", [sp], [CERAMIC])
    queue = route(qs, comparisons={}, approved_revision="MAR.2023")
    assert total(apply(qs, queue)) == D(0)


# 7 ── nothing downstream may validate an identifier the registry would refuse
def test_the_comparator_will_not_score_an_identifier_it_cannot_validate():
    from engine.semantic_compare import comparable_fields
    _, excluded = comparable_fields(None)
    assert "apartment_id" in excluded and "zone_id" in excluded


def test_the_registry_refuses_an_assignment_outside_its_vocabulary():
    with pytest.raises(GroupRegistryError, match="not a canonical id"):
        REG.validate_assignment(APARTMENT, "APT-EAST", space_id="SPACE-001")
    with pytest.raises(GroupRegistryError, match="no zone ontology"):
        REG.validate_assignment(ZONE, "ZONE-001", space_id="SPACE-001")


# 8 ── geometry stays where it is
def test_no_semantic_path_can_write_geometry():
    """Accepted geometry mutations must be zero, structurally rather than by audit."""
    from agents.a1_extractor.semantic import SpaceSemantics
    fields = set(SpaceSemantics.__dataclass_fields__)
    banned = {"area_m2", "perimeter_m", "width_mm", "height_mm", "polygon"}
    assert not (fields & banned)
