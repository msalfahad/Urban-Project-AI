"""E27 decides which trades apply. A1 and A2 do not, and no longer can.

Run 0 asked both agents for `trade_relevance` and they agreed on 12 of 36
spaces. That 33% was filed as a semantic failure. It was not: neither agent had
the project's rule library, so both were improvising over a vocabulary, and the
architecture had always said E27 owns this decision. These tests hold the
decision where it belongs, and hold every branch that cannot decide to a stop.
"""

from __future__ import annotations

from decimal import Decimal as D

import pytest

from engine.trade_rules import (APPLIES, FLOOR, HELD_PENDING_SCOPE, NOT_APPLICABLE,
                                NOT_IN_SCOPE, NOT_WIRED, RULE_ENGINE_NOT_AVAILABLE,
                                RULE_REQUIRED, WALL, TradeRuleSet, applied_trades,
                                decide_trade, open_questions, trade_relevance)

CERAMIC = TradeRuleSet.load("data/trade_rules/23010_ceramic.json")
PLASTER = TradeRuleSet.load("data/trade_rules/23010_plaster.json")
RULES = {"ceramic": CERAMIC, "plaster": PLASTER}


def test_a_rule_that_exists_decides_and_names_itself():
    d = decide_trade(CERAMIC, "BATHROOM", FLOOR, scope_status="IN_SCOPE")
    assert d.status == APPLIES and d.applies
    assert d.rule_id and d.finish
    assert d.trade_rule_confidence == "HIGH"
    assert "rule" in d.basis


def test_a_rule_that_says_no_is_a_decision_not_a_gap():
    d = decide_trade(CERAMIC, "BEDROOM", WALL, scope_status="IN_SCOPE")
    assert d.status == NOT_APPLICABLE and not d.applies
    assert d.trade_rule_confidence == "HIGH"


def test_a_label_with_no_rule_stops_and_issues_a_routable_id():
    d = decide_trade(CERAMIC, "PARKING", FLOOR, scope_status="IN_SCOPE")
    assert d.status == RULE_REQUIRED and not d.applies
    assert d.missing_rule_id == "CERAMIC_FLOOR_PARKING"
    assert d.needs_human


def test_an_unwired_trade_never_becomes_a_default():
    """NULL RULE SET MUST NEVER MEAN DEFAULT RULE."""
    stub = TradeRuleSet(trade="waterproofing", height_m=D("3.0"), rules={},
                        trade_rule_status=NOT_WIRED)
    d = decide_trade(stub, "BATHROOM", FLOOR, scope_status="IN_SCOPE")
    assert d.status == RULE_ENGINE_NOT_AVAILABLE and not d.applies
    assert d.missing_rule_id == "WATERPROOFING_FLOOR_BATHROOM"


@pytest.mark.parametrize("label", ["UNKNOWN", "AMBIGUOUS", "NOT_A_SPACE", ""])
def test_a_non_label_is_never_looked_up(label):
    d = decide_trade(CERAMIC, label, FLOOR, scope_status="IN_SCOPE")
    assert d.status == RULE_REQUIRED and not d.applies


# --- scope gates the trade question, and AMBIGUOUS is held -------------------

def test_an_out_of_scope_space_takes_no_trade():
    d = decide_trade(CERAMIC, "BATHROOM", FLOOR, scope_status="OUT_OF_SCOPE")
    assert d.status == NOT_IN_SCOPE and not d.applies and d.decided


def test_an_ambiguous_scope_holds_the_trade_rather_than_assuming_in():
    """Point 12: label and scope are separate, and neither validates the other."""
    d = decide_trade(CERAMIC, "TERRACE", FLOOR, scope_status="AMBIGUOUS")
    assert d.status == HELD_PENDING_SCOPE and not d.applies
    assert d.needs_human


def test_a_confidently_labelled_terrace_still_does_not_auto_validate_its_scope():
    ds = trade_relevance("TERRACE", "AMBIGUOUS", RULES)
    assert applied_trades(ds) == []
    assert len(open_questions(ds)) == len(ds)


# --- the whole-space view A1 used to be asked for ----------------------------

def test_trade_relevance_returns_every_trade_and_element():
    ds = trade_relevance("BATHROOM", "IN_SCOPE", RULES)
    assert len(ds) == 4                      # 2 trades x FLOOR/WALL
    assert applied_trades(ds) == ["ceramic"]


def test_the_same_label_in_two_scopes_gives_two_answers():
    inside = applied_trades(trade_relevance("BEDROOM", "IN_SCOPE", RULES))
    outside = applied_trades(trade_relevance("BEDROOM", "OUT_OF_SCOPE", RULES))
    assert inside and not outside


def test_the_iron_room_takes_the_project_rule_not_general_knowledge():
    """كوي is the space the old MEASURER calls مطبخ. Only the rule set decides."""
    ds = trade_relevance("IRON_ROOM", "IN_SCOPE", RULES)
    decided = {(d.trade, d.element): d.status for d in ds}
    assert all(s != RULE_ENGINE_NOT_AVAILABLE for s in decided.values())
    for d in ds:
        if d.applies:
            assert d.rule_id


def test_an_element_that_is_not_floor_or_wall_is_refused():
    from engine.trade_rules import TradeRuleError
    with pytest.raises(TradeRuleError, match="is not FLOOR or WALL"):
        decide_trade(CERAMIC, "BATHROOM", "CEILING", scope_status="IN_SCOPE")
