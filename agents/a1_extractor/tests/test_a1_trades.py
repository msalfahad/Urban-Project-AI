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


def test_rule_required_needs_a_machine_readable_rule_id():
    """Prose in trade_notes cannot be grouped, counted or routed."""
    with pytest.raises(SemanticError, match="machine-readable"):
        SemanticOutput.from_dict({"spaces": [rec(
            trade_relevance=[RULE_REQUIRED],
            trade_notes="someone should decide about terraces")]})


def test_a_missing_rule_id_without_rule_required_is_refused():
    with pytest.raises(SemanticError, match="claim a decision it does not have"):
        SemanticOutput.from_dict({"spaces": [rec(
            missing_rule_id="CERAMIC_WALL_FINISH_IRON_ROOM")]})


def test_rule_required_with_an_id_is_a_routed_question_not_an_error():
    out = SemanticOutput.from_dict({"spaces": [rec(
        semantic_label="TERRACE", trade_relevance=[RULE_REQUIRED],
        missing_rule_id="EXTERNAL_FINISH_TERRACE",
        missing_rule_description="No project rule defines terrace external tile "
                                 "or waterproofing applicability.",
        missing_required_fields=["external_finish_scope", "waterproofing_height"],
        trade_notes="no finish schedule supplied")]})
    s = out.spaces[0]
    assert RULE_REQUIRED in s.trade_relevance
    assert s.missing_rule_id == "EXTERNAL_FINISH_TERRACE"
    assert s.missing_required_fields == ["external_finish_scope", "waterproofing_height"]


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
    assert out.spaces[0].semantic_schema_version == SEMANTIC_SCHEMA_VERSION == "2.0"
    assert alias_version() == "2.0"


def test_space_function_must_not_just_repeat_the_label():
    with pytest.raises(SemanticError, match="repeats semantic_label"):
        SemanticOutput.from_dict({"spaces": [rec(space_function="BEDROOM")]})


def test_space_function_carries_a_real_subtype():
    out = SemanticOutput.from_dict({"spaces": [rec(
        semantic_label="SERVICE_ROOM", space_function="Water pump room")]})
    assert out.spaces[0].space_function == "Water pump room"


# ------------------------------------------ matcher safety (no substring mode)
@pytest.mark.parametrize("generic", ["room", "hall", "area", "service", "غرفة", "صالة"])
def test_a_dangerous_generic_word_matches_nothing_on_its_own(generic):
    """"room" sits inside BEDROOM, MAID_ROOM, IRON_ROOM and SERVICE_ROOM."""
    from engine.trades import match_label
    assert match_label(generic).canonical_label == "UNKNOWN"


@pytest.mark.parametrize("raw,expected", [
    ("كوي IRON", "IRON_ROOM"), ("غرفة نوم BED ROOM", "BEDROOM"),
    ("حمام BATH", "BATHROOM"), ("مغاسل WASH", "WASHROOM"),
    ("غرفة خادمة MAID ROOM", "MAID_ROOM"), ("تراس TERRACE", "TERRACE"),
])
def test_bilingual_labels_resolve_through_whole_words(raw, expected):
    from engine.trades import match_label
    m = match_label(raw)
    assert m.canonical_label == expected
    assert m.match_method in ("TOKEN_ALIAS", "PHRASE_ALIAS", "EXACT_ALIAS")


def test_arabic_diacritics_and_alef_variants_normalise():
    from engine.trades import match_label, normalize_text
    assert normalize_text("حَمَّام") == "حمام"
    assert match_label("حَمَّام").canonical_label == "BATHROOM"
    assert normalize_text("إيران") == normalize_text("ايران")


def test_a_match_carries_its_whole_provenance():
    from engine.trades import match_label
    m = match_label("كوي", source="VISUAL_LABEL_HUMAN_VERIFIED")
    assert m.input_text == "كوي" and m.normalized_text == "كوي"
    assert m.matched_alias == "كوي" and m.canonical_label == "IRON_ROOM"
    assert m.match_method == "EXACT_ALIAS" and m.confidence == "HIGH"
    assert m.source == "VISUAL_LABEL_HUMAN_VERIFIED" and m.resolved


def test_an_unresolved_label_is_not_marked_resolved():
    from engine.trades import match_label
    m = match_label("SNUG")
    assert m.canonical_label == "UNKNOWN" and not m.resolved


def test_legacy_aliases_never_match_new_input():
    """qiyal / قيال survive on old records but must not classify anything now."""
    from engine.trades import match_label
    assert match_label("qiyal").canonical_label == "UNKNOWN"
    assert match_label("قيال").canonical_label == "UNKNOWN"


def test_the_taxonomy_is_frozen_at_v2_with_the_approved_labels():
    from agents.a1_extractor.semantic import SEMANTIC_LABELS, SEMANTIC_SCHEMA_VERSION
    assert SEMANTIC_SCHEMA_VERSION == "2.0"
    assert len(SEMANTIC_LABELS) == 38
    for owner_label in ("WC", "LIVING_ROOM", "OPEN_PLAN_LIVING", "DRESSING_ROOM",
                        "LAUNDRY_ROOM", "ELEVATOR_SHAFT", "SERVICE_SHAFT",
                        "STAIR_VOID", "DOUBLE_HEIGHT_VOID", "ROOF_AREA",
                        "GARAGE", "PARKING"):
        assert owner_label in SEMANTIC_LABELS
    for gone in ("DRESS", "LAUNDRY", "LIFT_SHAFT", "OPEN_PLAN", "SALOON"):
        assert gone not in SEMANTIC_LABELS


def test_not_a_space_must_use_the_list_not_the_label():
    """Two places to record the same thing is two sources of truth."""
    with pytest.raises(SemanticError, match="use the not_a_space"):
        SemanticOutput.from_dict({"spaces": [rec(semantic_label="NOT_A_SPACE")]})


# ------------------------------------------------- unwired rules fail closed
def test_an_unwired_trade_cannot_calculate_anything():
    from decimal import Decimal as D
    from engine.trade_rules import NOT_WIRED, RuleEngineNotAvailable, TradeRuleSet
    stub = TradeRuleSet(trade="paint", height_m=D("3.2"), rules={},
                        trade_rule_status=NOT_WIRED)
    with pytest.raises(RuleEngineNotAvailable, match="RULE_ENGINE_NOT_AVAILABLE"):
        stub.rule_for("BEDROOM")


def test_an_unwired_trade_never_silently_becomes_a_default():
    from decimal import Decimal as D
    from engine.quantities import SpaceInputs, floor_quantity
    from engine.trade_rules import NOT_WIRED, RuleEngineNotAvailable, TradeRuleSet
    stub = TradeRuleSet(trade="waterproofing", height_m=D("3.0"), rules={},
                        trade_rule_status=NOT_WIRED)
    sp = SpaceInputs("BTH-01", "2F", "BATHROOM", "A1", "VALIDATED",
                     floor_area_m2=D("4.5"))
    with pytest.raises(RuleEngineNotAvailable):
        floor_quantity("23010", sp, stub)


def test_two_canonical_labels_matching_is_ambiguous_not_a_coin_flip():
    """The first match is never simply taken."""
    from engine.trades import Alias, match_label
    import engine.trades as T
    original = T._aliases.__wrapped__
    fake = ((Alias("زاوية", "STORE", "ar", "TOKEN", 10),
             Alias("زاوية", "SERVICE_ROOM", "ar", "TOKEN", 10)), "test")
    T._aliases.cache_clear()
    T._aliases = lambda path=None: fake        # type: ignore[assignment]
    try:
        m = match_label("زاوية")
        assert m.canonical_label == "AMBIGUOUS"
        assert set(m.candidates) == {"STORE", "SERVICE_ROOM"}
        assert not m.resolved
    finally:
        T._aliases = original                  # type: ignore[assignment]
        T._aliases = __import__("functools").lru_cache(maxsize=1)(original)
        T._aliases.cache_clear()


@pytest.mark.parametrize("raw", ["IRON RAILING", "ROOF DRAIN", "BATH TUB SCHEDULE"])
def test_a_short_english_word_naming_a_material_is_not_a_room(raw):
    """"iron" is a room only as the whole label, never as a loose token."""
    from engine.trades import match_label
    assert match_label(raw).canonical_label == "UNKNOWN"


@pytest.mark.parametrize("raw,expected", [
    ("iron", "IRON_ROOM"), ("bath", "BATHROOM"), ("store", "STORE"),
])
def test_those_same_words_still_resolve_as_a_whole_label(raw, expected):
    from engine.trades import match_label
    m = match_label(raw)
    assert m.canonical_label == expected and m.match_method == "EXACT_ALIAS"
