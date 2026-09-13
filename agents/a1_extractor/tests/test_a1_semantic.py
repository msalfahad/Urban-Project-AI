"""A1 as the semantic agent: it attaches meaning and never returns a number."""

from __future__ import annotations

import pytest

from agents.a1_extractor.semantic import (SemanticError, SemanticOutput,
                                          SpaceSemantics)
from agents.a1_extractor.tests.registry_fixture import REG, parse


def rec(**kw):
    base = dict(space_id="S1", semantic_label="BEDROOM", label_source="PDF_TEXT",
                semantic_label_confidence="HIGH",
                confidence_basis="drawing text entity inside the polygon",
                scope_status="IN_SCOPE", scope_confidence="HIGH",
                scope_basis="the owner's brief names this unit",
                apartment_id="APT-001", apartment_membership_confidence="HIGH",
                apartment_basis="reached from the main stair landing only")
    base.update(kw)
    return base


def test_a_valid_record_parses():
    out = parse({"spaces": [rec()]})
    assert out.spaces[0].semantic_label == "BEDROOM"


@pytest.mark.parametrize("key", ["area_m2", "perimeter_m", "width_mm", "polygon", "dimensions"])
def test_any_geometry_field_is_refused(key):
    """A1 cannot edit E23/E25 because the schema gives it nowhere to put a number."""
    with pytest.raises(SemanticError, match="belongs to E23/E25"):
        parse({"spaces": [rec(**{key: 12.5})]})


def test_a_geometry_challenge_is_the_allowed_way_to_object():
    out = parse({"spaces": [rec(geometry_challenge="region looks clipped")]})
    assert out.spaces[0].geometry_challenge


def test_confidence_must_name_its_evidence():
    with pytest.raises(SemanticError, match="must name the evidence"):
        parse({"spaces": [rec(confidence_basis="  ")]})


def test_a_vision_only_label_cannot_be_high_confidence():
    with pytest.raises(SemanticError, match="cannot rest on VISION_MODEL alone"):
        parse({"spaces": [rec(label_source="VISION_MODEL")]})


def test_no_label_source_caps_the_confidence():
    with pytest.raises(SemanticError, match="no label source"):
        parse({"spaces": [rec(label_source="UNKNOWN",
                       semantic_label_confidence="MEDIUM")]})


def test_an_unknown_semantic_label_is_refused():
    with pytest.raises(SemanticError, match="not one of"):
        parse({"spaces": [rec(semantic_label="SNUG")]})


def test_a_space_cannot_be_classified_twice():
    with pytest.raises(SemanticError, match="classified twice"):
        parse({"spaces": [rec(), rec()]})


def test_a_space_cannot_be_both_a_room_and_not_a_room():
    with pytest.raises(SemanticError, match="both classified and marked"):
        parse({"spaces": [rec()], "not_a_space": ["S1"]})


def test_covers_reports_the_spaces_left_semantically_invisible():
    out = parse({"spaces": [rec()], "not_a_space": ["S2"]})
    assert out.covers(["S1", "S2", "S3"]) == ["S3"]


def test_the_iron_room_trap_records_the_conflict_rather_than_following_the_old_name():
    """AR-00 says كوي IRON; the old MEASURER calls the same space مطبخ."""
    out = parse({"spaces": [rec(
        space_id="IRN-01", semantic_label="IRON_ROOM",
        original_drawing_label="كوي IRON",
        semantic_conflicts=["historical takeoff labels this space مطبخ (kitchen)"],
    )]})
    s = out.spaces[0]
    assert s.semantic_label == "IRON_ROOM" and s.semantic_conflicts


def test_an_out_of_scope_space_still_gets_a_record():
    out = parse({"spaces": [rec(
        space_id="TRC-01", semantic_label="TERRACE", scope_status="OUT_OF_SCOPE")]})
    assert out.spaces[0].scope_status == "OUT_OF_SCOPE"


# --- canonical identifiers: the Run 0 defect, closed --------------------------

def test_a_free_text_apartment_id_is_refused():
    """Run 0's A1 answered APT-EAST and A2 answered APT-01. Never again."""
    with pytest.raises(SemanticError, match="not a canonical id"):
        parse({"spaces": [rec(apartment_id="APT-EAST")]})


def test_unknown_and_ambiguous_are_real_apartment_answers():
    for value in ("UNKNOWN", "AMBIGUOUS"):
        out = parse({"spaces": [rec(apartment_id=value,
                                    apartment_membership_confidence="LOW",
                                    apartment_basis="position only")]})
        assert out.spaces[0].apartment_id == value


def test_a_confident_non_answer_is_a_contradiction():
    with pytest.raises(SemanticError, match="confident non-answer"):
        parse({"spaces": [rec(apartment_id="UNKNOWN")]})


def test_a_zone_is_not_invented_when_the_project_has_no_ontology():
    """Point 2 of the brief: do not manufacture canonical ids to pass a test."""
    with pytest.raises(SemanticError, match="no zone ontology is defined"):
        parse({"spaces": [rec(zone_id="ZONE-001")]})


def test_zone_confidence_cannot_be_claimed_without_an_ontology():
    with pytest.raises(SemanticError, match="must be NOT_ESTABLISHED"):
        parse({"spaces": [rec(zone_membership_confidence="HIGH")]})


def test_a_zone_id_is_accepted_where_an_ontology_does_exist():
    from agents.a1_extractor.tests.registry_fixture import ZONED
    out = parse({"spaces": [rec(zone_id="ZONE-001",
                                zone_membership_confidence="MEDIUM")]}, ZONED)
    assert out.spaces[0].zone_id == "ZONE-001"


def test_descriptions_survive_but_are_not_identifiers():
    out = parse({"spaces": [rec(apartment_description="the north-east residential wing",
                                zone_description="bedroom wing")]})
    s = out.spaces[0]
    assert s.apartment_id == "APT-001" and s.apartment_description


def test_validation_without_a_registry_fails_closed():
    with pytest.raises(SemanticError, match="no group registry supplied"):
        SemanticOutput.from_dict({"spaces": [rec()]})


# --- per-field confidence ----------------------------------------------------

def test_a_label_can_be_high_while_the_schedule_is_unknown():
    """A drawing entity reading حمام is strong evidence about what a room IS.

    It says nothing about what finish that room takes, and in Run 0 the second
    question was allowed to hold the first one down.
    """
    out = parse({"spaces": [rec(
        space_id="BTH", semantic_label="BATHROOM", label_source="DWG_TEXT_ENTITY",
        semantic_label_confidence="HIGH",
        confidence_basis="حمام as a text entity inside this polygon",
        schedule_confidence="NOT_ESTABLISHED")]})
    s = out.spaces[0]
    assert s.semantic_label_confidence == "HIGH"
    assert s.schedule_confidence == "NOT_ESTABLISHED"


def test_scope_without_evidence_must_be_ambiguous():
    """Fail closed: an untraceable scope decision is an assumption."""
    with pytest.raises(SemanticError, match="answer AMBIGUOUS"):
        parse({"spaces": [rec(scope_status="IN_SCOPE",
                              scope_confidence="NOT_ESTABLISHED", scope_basis="")]})


def test_ambiguous_scope_with_no_evidence_is_allowed():
    out = parse({"spaces": [rec(scope_status="AMBIGUOUS",
                                scope_confidence="NOT_ESTABLISHED", scope_basis="")]})
    assert out.spaces[0].scope_status == "AMBIGUOUS"


def test_a_stated_scope_confidence_must_name_its_evidence():
    with pytest.raises(SemanticError, match="scope_basis is empty"):
        parse({"spaces": [rec(scope_confidence="MEDIUM", scope_basis="  ")]})


# --- trades left this schema -------------------------------------------------

def test_trade_relevance_is_no_longer_a1s_to_decide():
    with pytest.raises(SemanticError, match="E27 decides trade relevance"):
        parse({"spaces": [rec(trade_relevance=["CERAMIC_FLOOR"])]})


def test_the_old_confidence_field_name_is_refused_rather_than_ignored():
    with pytest.raises(SemanticError, match="renamed to semantic_label_confidence"):
        parse({"spaces": [rec(label_confidence="HIGH")]})


def test_a_trade_challenge_is_the_allowed_way_to_push_back():
    out = parse({"spaces": [rec(trade_challenges=[
        {"kind": "TRADE_RULE_CHALLENGE", "trade": "ARCHITECTURAL_WALL_FINISH",
         "note": "drawing note says full-height tiling; no rule covers IRON_ROOM"}])]})
    assert out.spaces[0].trade_challenges[0].kind == "TRADE_RULE_CHALLENGE"


def test_a_challenge_with_no_note_is_not_actionable():
    with pytest.raises(SemanticError, match="not actionable"):
        parse({"spaces": [rec(trade_challenges=[
            {"kind": "DRAWING_NOTE_CONFLICT", "note": ""}])]})


@pytest.mark.parametrize("echo", ["BEDROOM", "Bedroom", "bedroom", "bed room",
                                  "  Bedroom  "])
def test_space_function_echoing_the_label_in_any_casing_is_refused(echo):
    """Both Run 1 agents tripped on exactly this: KITCHEN / "Kitchen"."""
    with pytest.raises(SemanticError, match="repeats semantic_label"):
        parse({"spaces": [rec(space_function=echo)]})


def test_an_empty_space_function_is_the_right_answer_when_there_is_nothing_to_add():
    out = parse({"spaces": [rec(space_function="")]})
    assert out.spaces[0].space_function == ""
