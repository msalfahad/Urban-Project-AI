"""E17 — Preliminaries.

The costs that never appear on a drawing and quietly eat the profit: site
engineer, scaffolding, temporary power and water, crane, cleaning, waste removal.
This makes them explicit line items instead of a forgotten margin leak.

Time-driven items scale with the programme duration (E12); the rest are lump or
per-project. Rates are provisional (KWD) until measured (E19/E20).
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class PrelimRate:
    name: str
    basis: str          # "per_week" | "lump" | "per_m2"
    rate: float         # KWD per unit of basis


# Provisional preliminaries rate card (KWD).
DEFAULT_RATES = [
    PrelimRate("Site engineer / supervision", "per_week", 120.0),
    PrelimRate("Scaffolding", "lump", 800.0),
    PrelimRate("Temporary power & water", "per_week", 25.0),
    PrelimRate("Crane / hoisting", "lump", 1500.0),
    PrelimRate("Cleaning", "per_week", 20.0),
    PrelimRate("Waste removal / skips", "per_week", 35.0),
    PrelimRate("Site setup & hoarding", "lump", 600.0),
]


@dataclass
class PrelimItem:
    name: str
    basis: str
    quantity: float
    rate: float
    amount: float


@dataclass
class Preliminaries:
    items: list[PrelimItem] = field(default_factory=list)

    @property
    def total(self) -> float:
        return sum(i.amount for i in self.items)


def preliminaries(
    *,
    duration_weeks: float,
    built_area_m2: float | None = None,
    rates: list[PrelimRate] | None = None,
) -> Preliminaries:
    """Compute preliminaries for a project of a given duration.

    Time-based items multiply by weeks; lump items are once; per_m2 by area.
    """
    rates = rates or DEFAULT_RATES
    items: list[PrelimItem] = []
    for r in rates:
        if r.basis == "per_week":
            qty = duration_weeks
        elif r.basis == "per_m2":
            qty = built_area_m2 or 0.0
        else:  # lump
            qty = 1.0
        items.append(PrelimItem(r.name, r.basis, qty, r.rate, qty * r.rate))
    return Preliminaries(items=items)
