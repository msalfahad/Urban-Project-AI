"""E-QTY — Deterministic quantity assembly.

Code calculates. Nothing else does.

A quantity here is never just a number: it is a number plus every input that
produced it, so the question "where did this come from?" has an answer that can
be read back from the record itself rather than reconstructed by someone's
memory. Geometry source and basis, semantic source and status, trade rule id and
version, the formula, the engine version, the drawing and its revision.

Two rules that the shape of this module enforces:

- No agent value can enter. The inputs are validated geometry, validated
  semantics and a trade rule. There is no parameter through which a model's
  opinion of an area could arrive.
- No generic wall quantity is reused across trades. Ceramic runs to 3.00 m on
  this project and plaster to 3.20 m, so asking for "the wall quantity" without
  naming a trade is a question with no answer.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal

CALC_ENGINE_VERSION = "1.0"

# Release lifecycle (E33 decides which one a quantity ends in).
DRAFT = "DRAFT"
AUTO_VALIDATED = "AUTO_VALIDATED"
REVIEW_REQUIRED = "REVIEW_REQUIRED"
BLOCKED = "BLOCKED"
APPROVED_BY_ENGINEER = "APPROVED_BY_ENGINEER"
REJECTED = "REJECTED"
SUPERSEDED = "SUPERSEDED"

RELEASABLE = {AUTO_VALIDATED, APPROVED_BY_ENGINEER}


class QuantityError(ValueError):
    """A quantity could not be assembled from proven inputs."""


@dataclass(frozen=True)
class Quantity:
    """One trade quantity for one space, with its whole provenance."""

    quantity_id: str
    project_id: str
    floor_id: str
    space_id: str
    trade: str
    element: str                 # FLOOR / WALL / SKIRTING / CEILING ...
    value: Decimal
    unit: str

    geometry_source: str
    geometry_basis: str
    semantic_source: str
    semantic_status: str
    trade_rule_id: str
    trade_rule_version: str
    calculation_formula: str
    drawing: str
    drawing_revision: str

    calculation_engine_version: str = CALC_ENGINE_VERSION
    status: str = DRAFT
    notes: str = ""

    @property
    def releasable(self) -> bool:
        return self.status in RELEASABLE

    def provenance(self) -> dict:
        """Everything needed to answer 'where did this number come from?'."""
        return {
            "quantity_id": self.quantity_id, "value": str(self.value),
            "unit": self.unit, "formula": self.calculation_formula,
            "geometry": f"{self.geometry_source} ({self.geometry_basis})",
            "semantics": f"{self.semantic_source} [{self.semantic_status}]",
            "trade_rule": f"{self.trade_rule_id} v{self.trade_rule_version}",
            "drawing": f"{self.drawing} rev {self.drawing_revision}",
            "engine": self.calculation_engine_version,
            "status": self.status,
        }


@dataclass
class SpaceInputs:
    """The proven facts about one space. No agent numbers appear here."""

    space_id: str
    floor_id: str
    semantic_label: str
    semantic_source: str
    semantic_status: str
    floor_area_m2: Decimal | None = None
    gross_wall_perimeter_m: Decimal | None = None
    geometry_source: str = ""
    geometry_basis: str = ""
    drawing: str = ""
    drawing_revision: str = ""
    opening_deduction_m: Decimal = Decimal(0)


def _qid(project: str, space: str, trade: str, element: str) -> str:
    return f"{project}:{space}:{trade}:{element}"


def floor_quantity(project_id: str, sp: SpaceInputs, rules) -> Quantity | None:
    """Floor finish area, when this trade's rules give this space one."""
    rule = rules.rule_for(sp.semantic_label)
    if rule.floor_finish is None:
        return None
    if sp.floor_area_m2 is None:
        raise QuantityError(
            f"{sp.space_id}: {rules.trade} floor finish applies but no validated "
            "floor area exists. Route to review rather than assume one.")
    return Quantity(
        quantity_id=_qid(project_id, sp.space_id, rules.trade, "FLOOR"),
        project_id=project_id, floor_id=sp.floor_id, space_id=sp.space_id,
        trade=rules.trade, element="FLOOR", value=sp.floor_area_m2, unit="m2",
        geometry_source=sp.geometry_source, geometry_basis=sp.geometry_basis,
        semantic_source=sp.semantic_source, semantic_status=sp.semantic_status,
        trade_rule_id=rule.rule_id or f"{rules.trade}:{rule.room_type}",
        trade_rule_version=rules.version,
        calculation_formula="validated floor area",
        drawing=sp.drawing, drawing_revision=sp.drawing_revision,
        notes=rule.notes,
    )


def wall_quantity(project_id: str, sp: SpaceInputs, rules,
                  *, deduct_openings: bool = False) -> Quantity | None:
    """Wall finish area at THIS trade's height. Never a shared wall number."""
    rule = rules.rule_for(sp.semantic_label)
    if rule.wall_finish is None:
        return None
    if sp.gross_wall_perimeter_m is None:
        raise QuantityError(
            f"{sp.space_id}: {rules.trade} wall finish applies but no validated "
            "wall perimeter exists. Route to review rather than assume one.")
    length = sp.gross_wall_perimeter_m
    formula = f"gross wall perimeter {length} m x {rules.trade} height {rules.height_m} m"
    if deduct_openings and sp.opening_deduction_m:
        length = length - sp.opening_deduction_m
        formula += f" (less {sp.opening_deduction_m} m of openings, per trade rule)"
    if length < 0:
        raise QuantityError(f"{sp.space_id}: deductions exceed the wall length")
    return Quantity(
        quantity_id=_qid(project_id, sp.space_id, rules.trade, "WALL"),
        project_id=project_id, floor_id=sp.floor_id, space_id=sp.space_id,
        trade=rules.trade, element="WALL", value=length * rules.height_m, unit="m2",
        geometry_source=sp.geometry_source, geometry_basis=sp.geometry_basis,
        semantic_source=sp.semantic_source, semantic_status=sp.semantic_status,
        trade_rule_id=rule.rule_id or f"{rules.trade}:{rule.room_type}",
        trade_rule_version=rules.version, calculation_formula=formula,
        drawing=sp.drawing, drawing_revision=sp.drawing_revision, notes=rule.notes,
    )


def assemble(project_id: str, spaces: list[SpaceInputs], rule_sets: list,
             *, deduct_openings: bool = False) -> list[Quantity]:
    """Every quantity every trade rule produces for every space."""
    out: list[Quantity] = []
    for sp in spaces:
        for rules in rule_sets:
            for fn in (floor_quantity, wall_quantity):
                kw = {"deduct_openings": deduct_openings} if fn is wall_quantity else {}
                q = fn(project_id, sp, rules, **kw)
                if q is not None:
                    out.append(q)
    return out


def total(quantities: list[Quantity], *, trade: str | None = None,
          element: str | None = None, released_only: bool = True) -> Decimal:
    """Sum quantities. By default only released ones — a BOQ is downstream."""
    return sum((q.value for q in quantities
                if (trade is None or q.trade == trade)
                and (element is None or q.element == element)
                and (not released_only or q.releasable)), Decimal(0))
