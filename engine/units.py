"""Unit algebra for construction quantities.

The whole system rests on one rule: *code calculates, agents never do*. Before
any arithmetic can be trusted, the quantities going into it have to carry their
units, and the units have to combine lawfully. This module is the vocabulary
every other engine module speaks.

A `Quantity` is a number plus a `Unit`. Units only combine in the ways that make
physical sense: a length times a length is an area, a count times a length is a
length, and adding an area to a length is refused outright. That refusal is the
point — it is what stops a takeoff from silently summing square metres, linear
metres and a stray count into a single meaningless total (the real "295.44"
defect the audit found).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Unit(str, Enum):
    """The measurement dimensions a construction quantity can have.

    Stored as strings so a `Quantity` serialises cleanly into Firestore and
    reads plainly in an audit log.
    """

    COUNT = "count"      # dimensionless: pieces, doors, windows, fixtures
    LENGTH = "m"         # linear metres
    AREA = "m2"          # square metres
    VOLUME = "m3"        # cubic metres
    WEIGHT = "kg"        # kilograms (steel, mostly)
    MONEY = "KWD"        # Kuwaiti dinar

    def __str__(self) -> str:  # nicer messages and logs
        return self.value


class UnitError(ValueError):
    """Raised when an operation would combine units unlawfully.

    This is never swallowed. A UnitError means a takeoff tried to do something
    physically meaningless, and the calculation must stop and go to a human
    rather than produce a confident wrong number.
    """


# Which unit results from multiplying two units together. Only the physically
# meaningful products are listed; anything absent is illegal and raises.
# The table is symmetric — it is consulted with the pair pre-sorted.
_MULTIPLICATION: dict[frozenset[Unit], Unit] = {
    frozenset({Unit.COUNT, Unit.COUNT}): Unit.COUNT,
    frozenset({Unit.COUNT, Unit.LENGTH}): Unit.LENGTH,
    frozenset({Unit.COUNT, Unit.AREA}): Unit.AREA,
    frozenset({Unit.COUNT, Unit.VOLUME}): Unit.VOLUME,
    frozenset({Unit.COUNT, Unit.WEIGHT}): Unit.WEIGHT,
    frozenset({Unit.LENGTH, Unit.LENGTH}): Unit.AREA,
    frozenset({Unit.LENGTH, Unit.AREA}): Unit.VOLUME,
    frozenset({Unit.COUNT, Unit.MONEY}): Unit.MONEY,   # qty of items at a price
}


@dataclass(frozen=True)
class Quantity:
    """A number that knows what it measures.

    Immutable on purpose: a quantity that came off a drawing is a fact, and
    facts are not edited in place. Arithmetic returns new quantities, leaving a
    trail the audit log can follow.
    """

    value: float
    unit: Unit

    def __post_init__(self) -> None:
        if not isinstance(self.unit, Unit):
            raise UnitError(f"unit must be a Unit, got {self.unit!r}")

    # -- addition: only like units add ------------------------------------
    def __add__(self, other: "Quantity") -> "Quantity":
        self._require_quantity(other)
        if self.unit != other.unit:
            raise UnitError(
                f"cannot add {self.unit} to {other.unit} — "
                "these are different measurements and their sum is meaningless"
            )
        return Quantity(self.value + other.value, self.unit)

    def __sub__(self, other: "Quantity") -> "Quantity":
        self._require_quantity(other)
        if self.unit != other.unit:
            raise UnitError(
                f"cannot subtract {other.unit} from {self.unit} — "
                "these are different measurements"
            )
        return Quantity(self.value - other.value, self.unit)

    # -- multiplication: units combine per the table ----------------------
    def __mul__(self, other: "Quantity | float | int") -> "Quantity":
        if isinstance(other, (int, float)):
            # A bare number is treated as a dimensionless scalar.
            return Quantity(self.value * other, self.unit)
        self._require_quantity(other)
        key = frozenset({self.unit, other.unit})
        result = _MULTIPLICATION.get(key)
        if result is None:
            raise UnitError(
                f"cannot multiply {self.unit} by {other.unit} — "
                "no physical quantity has those dimensions"
            )
        return Quantity(self.value * other.value, result)

    __rmul__ = __mul__

    @staticmethod
    def _require_quantity(other: object) -> None:
        if not isinstance(other, Quantity):
            raise UnitError(f"expected a Quantity, got {type(other).__name__}")

    def __str__(self) -> str:
        return f"{self.value:g} {self.unit}"
