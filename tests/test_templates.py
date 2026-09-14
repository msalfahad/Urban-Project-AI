"""E45 — templates and assemblies: requirements, never defaults."""

from __future__ import annotations

import pytest

from engine.templates import (APPROVED, DRAFT, PLANNED_ASSEMBLIES, ROOM_TYPES,
                              RoomTemplate, TemplateError, TemplateLibrary,
                              TradeAssembly, Versioned)

OK = Versioned("V1", APPROVED, "Owner", "2026-09-14", "signed rule sheet")


def test_a_version_must_be_a_version():
    """"bathroom rule" cannot be reproduced. "BATHROOM template V3" can."""
    with pytest.raises(TemplateError, match="V1, V2, V3"):
        Versioned("bathroom rule")


def test_an_approval_with_nobody_s_name_is_not_an_approval():
    with pytest.raises(TemplateError, match="approved_by and approved_on"):
        Versioned("V1", APPROVED)


def test_a_draft_may_not_be_applied():
    """An LLM may propose a rule. It may not approve one."""
    draft = RoomTemplate("RT-1", "BATHROOM", Versioned("V1", DRAFT))
    assert not draft.applies_to("BATHROOM")


def test_no_approved_template_never_means_use_a_default():
    """NULL RULE SET MUST NEVER MEAN DEFAULT RULE."""
    lib = TemplateLibrary()
    assert lib.room_template("BATHROOM") is None
    assert lib.coverage(["BATHROOM"])["without_approved_template"] == ["BATHROOM"]


def test_an_assembly_declares_what_it_needs_not_what_it_produces():
    a = TradeAssembly("CERAMIC_WALL_STANDARD_V1", "CERAMIC", OK,
                      required_geometry=("wall_perimeter",),
                      required_heights=("ceramic_height",),
                      required_openings=True, unit="m2")
    assert a.missing({}) == ["wall_perimeter", "ceramic_height", "openings"]
    assert a.missing({"wall_perimeter": True, "ceramic_height": True,
                      "openings": True}) == []


def test_an_assembly_may_not_carry_arithmetic():
    """An assembly that can compute is a second source of truth for a
    quantity, and then two places have to agree about the answer."""
    with pytest.raises(TemplateError, match="NAME an engine function"):
        TradeAssembly("A", "CERAMIC", OK, formula_reference="length * height")


def test_an_assembly_naming_an_engine_function_is_fine():
    a = TradeAssembly("A", "CERAMIC", OK,
                      formula_reference="engine.wall_model.run_wall_model")
    assert a.formula_reference.startswith("engine.")


def test_a_room_template_says_possible_not_actual():
    """A bathroom template naming CERAMIC_WALL means "ask the ceramic rule
    about this room", never "this room has ceramic"."""
    t = RoomTemplate("RT-1", "BATHROOM", OK, possible_trades=("CERAMIC_WALL",))
    assert "possible_trades" in t.record()
    assert "quantities" not in t.record()


def test_the_room_vocabulary_is_not_a_set_of_templates():
    """Naming a room type is not approving a rule for it."""
    assert "MASTER_BEDROOM" in ROOM_TYPES
    assert "OPEN_PLAN_LIVING" in ROOM_TYPES
    assert TemplateLibrary().room_template("MASTER_BEDROOM") is None


def test_the_planned_assemblies_are_slots_not_definitions():
    assert "CERAMIC_WALL_STANDARD" in PLANNED_ASSEMBLIES
    assert TemplateLibrary().assembly("CERAMIC_WALL_STANDARD") is None


def test_no_pricing_or_material_recipe_anywhere():
    from pathlib import Path

    from engine import templates
    src = Path(templates.__file__).read_text().lower()
    for forbidden in ("price", "rate_kd", "kwd", "cost_per"):
        assert forbidden not in src, forbidden
