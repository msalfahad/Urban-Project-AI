"""§11 — the template layer must not erase, or over-extend, an E27 project rule.

Two mirror-image failures, both real, both now guarded:

  UNDER  The first export hard-coded trade_rule = False for every space. 23010
         has two APPROVED owner rule sets covering fifteen room types each. A
         signed rule the workbook ignores is a real rule thrown away.
  OVER   The fix asked "does ANY rule cover this room type", which made
         waterproofing releasable on the strength of the ceramic rule. Thirteen
         spaces read READY because of it.

AUTHORITY ORDER:

    1  APPROVED PROJECT TRADE RULE   (E27, data/trade_rules/*.json)
    2  approved room/trade template  (E45, reusable structure)
    3  nothing — and nothing means nothing

A template is reusable structure a project rule may reference. It never
replaces a project-specific approved rule, and an EMPTY template library does
not erase one.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from engine.templates import TemplateLibrary
from tools.export_qa_workbook import (USE_TRADE, _rule_sets,
                                      _trade_rule_covers)

RULES = Path("data/trade_rules")


@pytest.mark.skipif(not RULES.exists(), reason="rule library not present")
def test_the_existing_e27_project_rules_are_still_loadable():
    """The template layer did not displace them."""
    sets = _rule_sets()
    assert sets, "no E27 rule set loaded — the project rules have gone missing"
    trades = {rs.trade.lower() for rs in sets.values()}
    assert "ceramic" in trades and "plaster" in trades


@pytest.mark.skipif(not RULES.exists(), reason="rule library not present")
def test_an_approved_project_rule_is_recognised_for_its_own_trade():
    space = {"room_type": "BATHROOM"}
    assert _trade_rule_covers(space, "GROSS_CERAMIC_WALL")
    assert _trade_rule_covers(space, "GROSS_PLASTER")


@pytest.mark.skipif(not RULES.exists(), reason="rule library not present")
def test_a_rule_for_one_trade_never_establishes_another():
    """A ceramic rule saying a bedroom has a ceramic floor says nothing
    whatever about waterproofing."""
    space = {"room_type": "BEDROOM"}
    assert _trade_rule_covers(space, "GROSS_CERAMIC_WALL")
    assert not _trade_rule_covers(space, "WATERPROOFING_HORIZONTAL")
    assert not _trade_rule_covers(space, "PAINT")
    assert not _trade_rule_covers(space, "CEILING")


def test_a_room_type_with_no_rule_is_not_covered():
    assert not _trade_rule_covers({"room_type": "OPEN_PLAN_LIVING"},
                                  "GROSS_CERAMIC_WALL")
    assert not _trade_rule_covers({"room_type": ""}, "GROSS_CERAMIC_WALL")


def test_a_use_with_no_trade_never_claims_a_rule():
    """GROSS_PERIMETER needs no trade rule and must not claim one."""
    assert "GROSS_PERIMETER" not in USE_TRADE
    assert not _trade_rule_covers({"room_type": "BATHROOM"}, "GROSS_PERIMETER")


def test_an_empty_template_library_does_not_erase_a_project_rule():
    """NULL TEMPLATE must never mean NULL PROJECT RULE."""
    assert TemplateLibrary().room_template("BATHROOM") is None
    assert _trade_rule_covers({"room_type": "BATHROOM"},
                              "GROSS_CERAMIC_WALL") is True


def test_the_authority_order_is_written_down_where_it_is_used():
    import inspect

    from tools import export_qa_workbook
    doc = inspect.getdoc(export_qa_workbook._rule_sets)
    assert "APPROVED PROJECT TRADE RULE" in doc
    assert "NULL TEMPLATE must never mean NULL PROJECT RULE" in doc
