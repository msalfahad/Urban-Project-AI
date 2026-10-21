"""Trades are a registry, not prose; labels normalise without losing the original."""

from __future__ import annotations

import pytest

from agents.a1_extractor.semantic import (SEMANTIC_SCHEMA_VERSION, SemanticError,
                                          SemanticOutput)
from agents.a1_extractor.tests.registry_fixture import parse
from engine.trades import (RULE_REQUIRED, TradeError, alias_version,
                           normalize_label, registry, registry_version, resolve)


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


def test_a_challenge_may_name_a_canonical_trade():
    out = parse({"spaces": [rec(trade_challenges=[
        {"kind": "TRADE_RULE_CHALLENGE", "trade": "ARCHITECTURAL_FLOOR_FINISH",
         "note": "no rule covers this space type"}])]})
    assert out.spaces[0].trade_challenges[0].trade == "ARCHITECTURAL_FLOOR_FINISH"


def test_an_invented_trade_string_is_refused_even_in_a_challenge():
    """"ceramic" is not a trade id; the rules speak ARCHITECTURAL_FLOOR_FINISH."""
    with pytest.raises(SemanticError, match="not a canonical trade"):
        parse({"spaces": [rec(trade_challenges=[
            {"kind": "TRADE_RULE_CHALLENGE", "trade": "ceramic", "note": "x"}])]})


def test_a_missing_rule_is_now_e27s_to_name():
    """A1 raises the question; E27 issues the routable id."""
    from engine.trade_rules import RULE_REQUIRED as E27_RULE_REQUIRED
    from engine.trade_rules import TradeRuleSet, decide_trade
    rules = TradeRuleSet.load("data/trade_rules/23010_ceramic.json")
    d = decide_trade(rules, "PARKING", "WALL", scope_status="IN_SCOPE")
    assert d.status == E27_RULE_REQUIRED
    assert d.missing_rule_id == "CERAMIC_WALL_PARKING"
    assert not d.applies


def test_the_registry_carries_names_units_and_a_version():
    assert registry_version() == "1.0"
    hvac = resolve("HVAC")
    assert hvac.display_name_ar and hvac.quantity_unit == "count" and hvac.active
    assert len(registry()) >= 38


def test_unknown_trade_falls_back_to_other_rather_than_a_new_string():
    out = parse({"spaces": [rec(trade_challenges=[
        {"kind": "TRADE_RULE_CHALLENGE", "trade": "OTHER",
         "note": "shading pergola, no trade yet"}])]})
    assert out.spaces[0].trade_challenges[0].trade == "OTHER"


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
    out = parse({"spaces": [rec(
        space_id="IRN-01", semantic_label="IRON_ROOM", original_drawing_label="كوي")]})
    assert out.spaces[0].original_drawing_label == "كوي"
    assert out.spaces[0].semantic_label == "IRON_ROOM"


def test_records_carry_the_schema_version_they_were_written_under():
    out = parse({"spaces": [rec()]})
    assert out.spaces[0].semantic_schema_version == SEMANTIC_SCHEMA_VERSION == "3.0"
    assert alias_version() == "2.0"


def test_space_function_must_not_just_repeat_the_label():
    with pytest.raises(SemanticError, match="repeats semantic_label"):
        parse({"spaces": [rec(space_function="BEDROOM")]})


def test_space_function_carries_a_real_subtype():
    out = parse({"spaces": [rec(
        semantic_label="SERVICE_ROOM", space_function="Water pump room")]})
    assert out.spaces[0].space_function == "Water pump room"


# ------------------------------------------ matcher safety (no substring mode)
@pytest.mark.parametrize("generic", ["room", "hall", "area", "service", "غرفة"])
def test_a_dangerous_generic_word_matches_nothing_on_its_own(generic):
    """"room" sits inside BEDROOM, MAID_ROOM, IRON_ROOM and SERVICE_ROOM.

    صالة is NOT in this list: it is a real room label, handled by an anchored
    pattern rather than thrown away.
    """
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


def test_the_taxonomy_is_frozen_with_the_approved_labels():
    """The LABEL vocabulary did not move in schema 3.0 — only what surrounds it."""
    from agents.a1_extractor.semantic import SEMANTIC_LABELS, SEMANTIC_SCHEMA_VERSION
    assert SEMANTIC_SCHEMA_VERSION == "3.0"
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
        parse({"spaces": [rec(semantic_label="NOT_A_SPACE")]})


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


# ------------------------ صالة: a real label, matched only on the whole phrase
@pytest.mark.parametrize("raw", ["صالة", "صاله", "صالة شقة 1", "صالة شقة 2",
                                 "صالة شقة 12"])
def test_sala_alone_or_with_a_unit_number_is_a_salon(raw):
    from engine.trades import match_label
    m = match_label(raw)
    assert m.canonical_label == "SALON"
    assert m.match_method in ("EXACT_ALIAS", "ANCHORED_PATTERN")


def test_a_qualified_sala_is_not_a_salon():
    """صالة رياضية is a gym. A qualifier can change the room entirely."""
    from engine.trades import match_label
    assert match_label("صالة رياضية").canonical_label != "SALON"
    assert match_label("صالة رياضية").canonical_label == "UNKNOWN"


def test_sala_taam_is_dining_not_salon():
    from engine.trades import match_label
    m = match_label("صالة طعام")
    assert m.canonical_label == "DINING" and m.canonical_label != "SALON"


def test_sala_istiqbal_is_not_forced_into_an_existing_label():
    """No RECEPTION label exists, so this routes to review rather than guessing."""
    from engine.trades import match_label
    assert match_label("صالة استقبال").canonical_label == "UNKNOWN"


def test_an_anchored_pattern_names_the_rule_that_matched():
    from engine.trades import match_label
    m = match_label("صالة شقة 1", source="PDF_TEXT")
    assert m.matched_alias == "AR_SALA_APARTMENT_HALL"
    assert m.input_text == "صالة شقة 1"        # raw label preserved exactly


@pytest.mark.parametrize("raw,expected", [
    ("IRON", "IRON_ROOM"), ("ROOF", "ROOF_AREA"), ("BATH", "BATHROOM"),
])
def test_a_bare_element_word_resolves_only_as_the_whole_label(raw, expected):
    from engine.trades import match_label
    assert match_label(raw).canonical_label == expected


@pytest.mark.parametrize("raw", ["IRON RAILING", "ROOF DRAIN", "BATH TUB SCHEDULE",
                                 "IRON MONGERY", "ROOF PARAPET"])
def test_the_same_word_inside_a_phrase_is_never_a_room(raw):
    from engine.trades import match_label
    assert match_label(raw).canonical_label == "UNKNOWN"
