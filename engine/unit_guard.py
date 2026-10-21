"""E1 — Unit Guard.

The first gate every takeoff record passes through. It does not calculate a
price or a total; it only checks that a measurement is *shaped* like a real
measurement before anything downstream is allowed to touch it.

A takeoff record says: this many of this thing, arrived at by multiplying a
count by some dimensions, and the answer is in this unit. The Unit Guard
re-derives the unit from the dimensions and refuses the record if the claimed
unit does not match — for example, a record that multiplies a count by a single
length but claims the result is an area (m2). That is the exact class of mistake
that produced the audited "295.44" total, where lengths, areas and a count were
folded together.

Deterministic, dependency-free, instant. This is the kind of work the design
insists must be code, never an agent.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .units import Quantity, Unit, UnitError


@dataclass
class TakeoffRecord:
    """One measured line item, as an agent (A1/A2) would emit it.

    `dimensions` are the linear measurements multiplied together (e.g. a wall's
    length and height). `count` is how many identical instances there are. The
    Unit Guard checks that count x dimensions genuinely yields `claimed_unit`.
    """

    description: str
    count: float
    dimensions: list[Quantity]           # each must be a LENGTH
    claimed_unit: Unit
    source_drawing: str = ""             # provenance travels with the record
    source_sheet: str = ""
    source_revision: str = ""
    id: str = ""


@dataclass
class GuardResult:
    """The verdict on a single record."""

    ok: bool
    record: TakeoffRecord
    derived_unit: Unit | None = None
    computed: Quantity | None = None
    errors: list[str] = field(default_factory=list)


def check(record: TakeoffRecord) -> GuardResult:
    """Validate one takeoff record's dimensional consistency.

    Returns a GuardResult rather than raising, so a whole workbook can be
    screened and every bad line reported at once instead of stopping at the
    first. The computed quantity it returns is safe for the Calculator (E3) to
    use; a record that fails the guard must never reach the Calculator.
    """

    errors: list[str] = []

    if record.count is None or record.count < 0:
        errors.append(f"count must be zero or positive, got {record.count!r}")

    # Every stated dimension has to be a length — you build areas and volumes
    # out of lengths, never out of another area.
    for i, dim in enumerate(record.dimensions):
        if not isinstance(dim, Quantity):
            errors.append(f"dimension {i} is not a Quantity")
        elif dim.unit is not Unit.LENGTH:
            errors.append(
                f"dimension {i} is {dim.unit}, but dimensions must be lengths (m)"
            )

    if errors:
        return GuardResult(ok=False, record=record, errors=errors)

    # Re-derive the unit from first principles: count (dimensionless) times the
    # product of the lengths. The units module refuses any illegal product.
    try:
        acc = Quantity(float(record.count), Unit.COUNT)
        for dim in record.dimensions:
            acc = acc * dim
    except UnitError as exc:
        return GuardResult(ok=False, record=record, errors=[str(exc)])

    derived = acc.unit
    if derived is not record.claimed_unit:
        errors.append(
            f"unit mismatch: record claims {record.claimed_unit} but "
            f"count x {len(record.dimensions)} dimension(s) yields {derived}"
        )
        return GuardResult(ok=False, record=record, derived_unit=derived, errors=errors)

    return GuardResult(ok=True, record=record, derived_unit=derived, computed=acc)


def check_batch(records: list[TakeoffRecord]) -> list[GuardResult]:
    """Screen a whole set of records, returning a verdict for each in order."""
    return [check(r) for r in records]
