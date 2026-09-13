"""Trades are a registry, not prose; labels normalise without losing the original."""

from __future__ import annotations

import pytest

from agents.a1_extractor.semantic import (SEMANTIC_SCHEMA_VERSION, SemanticError,
                                          SemanticOutput)
from engine.trades import (RULE_REQUIRED, TradeError, alias_version,
                           normalize_label, registry, registry_version, resolve)


def rec(**kw):
    base = dict(space_id="S1", semantic_label="BEDROOM", label_source="PDF_TEXT",
                label_confidence="HIGH", confidence_basis="text + polygon + schedule",
                scope_status="IN_SCOPE")
    base.update(kw)
    return base


def test_a_canonical_trade_is_accepted():
    out = SemanticOutput.from_dict({"spaces": [rec(
        trade_relevance=["ARCHITECTURAL_FLOOR_FINISH", "PAINT"])]})
    assert out.spaces[0].trade_relevance == ["ARCHITECTURAL_FLOOR_FINISH", "PAINT"]


def test_an_invented_trade_string_is_refused():
    """"ceramic" is not a trade id; the rules speak ARCHITECTURAL_FLOOR_FINISH."""
    with pytest.raises(SemanticError, match="not a canonical trade"):
        SemanticOutput.from_dict({"spaces": [rec(trade_relevance=["ceramic"])]})


def test_rule_required_must_say_which_rule_is_missing():
    with pytest.raises(SemanticError, match="which rule or schedule"):
        SemanticOutput.from_dict({"spaces": [rec(trade_relevance=[RULE_REQUIRED])]})


def test_rule_required_with_a_note_is_a_routed_question_not_an_error():
    out = SemanticOutput.from_dict({"spaces": [rec(
        semantic_label="TERRACE", trade_relevance=[RULE_REQUIRED],
        trade_notes="external tile and waterproofing depend on project scope; "
                    "no finish schedule supplied")]})
    assert RULE_REQUIRED in out.spaces[0].trade_relevance


def test_the_registry_carries_names_units_and_a_version():
    assert registry_version() == "1.0"
    hvac = resolve("HVAC")
    assert hvac.display_name_ar and hvac.quantity_unit == "count" and hvac.active
    assert len(registry()) >= 38


def test_unknown_trade_falls_back_to_other_rather_than_a_new_string():
    out = SemanticOutput.from_dict({"spaces": [rec(
        trade_relevance=["OTHER"], trade_notes="shading pergola, no trade yet")]})
    assert out.spaces[0].trade_relevance == ["OTHER"]


@pytest.mark.parametrize("raw,expected", [
    ("كوي", "IRON_ROOM"), ("IRONING", "IRON_ROOM"), ("UTILITY", "IRON_ROOM"),
    ("مغاسل", "WASHROOM"), ("WASH AREA", "WASHROOM"),
    ("غرفة نوم BED ROOM", "BEDROOM"), ("تراس TERRACE", "TERRACE"),
])
def test_aliases_normalise_to_one_label(raw, expected):
    assert normalize_label(raw) == expected


def test_an_unrecognised_label_returns_nothing_rather_than_guessing():
    assert normalize_label("SNUG") is None
    assert normalize_label("") is None


def test_normalising_never_replaces_the_original_drawing_label():
    out = SemanticOutput.from_dict({"spaces": [rec(
        space_id="IRN-01", semantic_label="IRON_ROOM", original_drawing_label="كوي")]})
    assert out.spaces[0].original_drawing_label == "كوي"
    assert out.spaces[0].semantic_label == "IRON_ROOM"


def test_records_carry_the_schema_version_they_were_written_under():
    out = SemanticOutput.from_dict({"spaces": [rec()]})
    assert out.spaces[0].semantic_schema_version == SEMANTIC_SCHEMA_VERSION
    assert alias_version() == "1.0"


def test_space_function_must_not_just_repeat_the_label():
    with pytest.raises(SemanticError, match="repeats semantic_label"):
        SemanticOutput.from_dict({"spaces": [rec(space_function="BEDROOM")]})


def test_space_function_carries_a_real_subtype():
    out = SemanticOutput.from_dict({"spaces": [rec(
        semantic_label="SERVICE_ROOM", space_function="Water pump room")]})
    assert out.spaces[0].space_function == "Water pump room"
