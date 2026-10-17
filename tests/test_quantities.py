"""Deterministic quantity assembly: code calculates, and every number explains itself."""

from __future__ import annotations

from decimal import Decimal as D

import pytest

from engine.quantities import (AUTO_VALIDATED, BLOCKED, DRAFT, Quantity,
                               QuantityError, SpaceInputs, assemble,
                               floor_quantity, total, wall_quantity)
from engine.trade_rules import TradeRuleSet

CERAMIC = TradeRuleSet.load("data/trade_rules/23010_ceramic.json")
PLASTER = TradeRuleSet.load("data/trade_rules/23010_plaster.json")


def space(**kw) -> SpaceInputs:
    base = dict(space_id="BTH-03", floor_id="2F", semantic_label="BATHROOM",
                semantic_source="A1+A2 AGREE_HIGH_CONFIDENCE",
                semantic_status="VALIDATED", floor_area_m2=D("4.53"),
                gross_wall_perimeter_m=D("8.60"),
                geometry_source="E23 vector-snapped",
                geometry_basis="CLEAR_INTERNAL_FINISH_FACE",
                drawing="AR-00", drawing_revision="MAR.2023")
    base.update(kw)
    return SpaceInputs(**base)


def test_a_bathroom_gets_ceramic_floor_and_wall():
    qs = assemble("23010", [space()], [CERAMIC])
    assert {q.element for q in qs} == {"FLOOR", "WALL"}
    assert next(q for q in qs if q.element == "FLOOR").value == D("4.53")


def test_wall_quantity_uses_this_trades_height_not_a_shared_one():
    """Ceramic is 3.00 m on this project and plaster is 3.20 m."""
    assert CERAMIC.height_m != PLASTER.height_m
    w = wall_quantity("23010", space(semantic_label="SALON"), PLASTER)
    assert w.value == D("8.60") * D("3.20")
    assert "plaster height 3.20" in w.calculation_formula


def test_a_bedroom_gets_no_ceramic_wall():
    assert wall_quantity("23010", space(semantic_label="BEDROOM"), CERAMIC) is None


def test_a_terrace_gets_no_internal_ceramic_at_all():
    qs = assemble("23010", [space(semantic_label="TERRACE")], [CERAMIC])
    assert qs == []


def test_missing_geometry_refuses_rather_than_assuming():
    with pytest.raises(QuantityError, match="Route to review"):
        floor_quantity("23010", space(floor_area_m2=None), CERAMIC)
    with pytest.raises(QuantityError, match="Route to review"):
        wall_quantity("23010", space(gross_wall_perimeter_m=None), CERAMIC)


def test_openings_are_deducted_only_when_asked_and_the_formula_says_so():
    sp = space(opening_deduction_m=D("0.90"))
    gross = wall_quantity("23010", sp, CERAMIC)
    net = wall_quantity("23010", sp, CERAMIC, deduct_openings=True)
    assert gross.value == D("8.60") * D("3.00")
    assert net.value == D("7.70") * D("3.00")
    assert "less 0.90 m of openings" in net.calculation_formula


def test_deductions_cannot_exceed_the_wall():
    with pytest.raises(QuantityError, match="exceed the wall length"):
        wall_quantity("23010", space(opening_deduction_m=D("99")), CERAMIC,
                      deduct_openings=True)


def test_every_quantity_answers_where_did_this_number_come_from():
    q = wall_quantity("23010", space(), CERAMIC)
    p = q.provenance()
    for key in ("quantity_id", "value", "formula", "geometry", "semantics",
                "trade_rule", "drawing", "engine", "status"):
        assert p[key], f"{key} is empty — the number cannot be traced"
    assert "CLEAR_INTERNAL_FINISH_FACE" in p["geometry"]
    assert "MAR.2023" in p["drawing"]


def test_a_new_quantity_is_draft_and_not_releasable():
    q = floor_quantity("23010", space(), CERAMIC)
    assert q.status == DRAFT and not q.releasable


def test_totals_exclude_unreleased_quantities_by_default():
    """A BOQ is downstream of validation, not a sum of drafts."""
    qs = assemble("23010", [space()], [CERAMIC])
    assert total(qs) == D(0)
    released = [Quantity(**{**q.__dict__, "status": AUTO_VALIDATED}) for q in qs]
    assert total(released, element="FLOOR") == D("4.53")
    assert total(released, released_only=False) > 0


def test_a_blocked_quantity_never_reaches_a_total():
    qs = [Quantity(**{**floor_quantity("23010", space(), CERAMIC).__dict__,
                      "status": BLOCKED})]
    assert total(qs) == D(0)


def test_two_trades_over_one_space_do_not_share_a_wall_number():
    sp = space(semantic_label="SALON")
    qs = assemble("23010", [sp], [CERAMIC, PLASTER])
    walls = [q for q in qs if q.element == "WALL"]
    assert len(walls) == 1 and walls[0].trade == "plaster"   # salon has no ceramic wall
