"""E3 — Calculator.

All quantity arithmetic, per trade, from the records A1/A2 produced. It sums
measurements into trade totals — and refuses to add across different units (it
leans on the Unit Guard's dimensions), so a mixed-unit total can never form here.
Deterministic; this is the arithmetic the agents must never do.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass


@dataclass
class QtyRecord:
    trade: str
    description: str
    quantity: float
    unit: str          # canonical: count | m | m2 | m3 | kg


class MixedUnitError(ValueError):
    """Raised if a single trade+description would sum across different units."""


def calculate(records: list[QtyRecord]) -> dict[str, dict[str, float]]:
    """Return {trade: {unit: total}} — quantities summed within a unit only."""
    out: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    for r in records:
        if r.quantity is None:
            continue
        out[r.trade][r.unit] += r.quantity
    return {t: dict(u) for t, u in out.items()}


def total_for(records: list[QtyRecord], trade: str, unit: str) -> float:
    return sum(r.quantity for r in records
               if r.trade == trade and r.unit == unit and r.quantity is not None)


def priced_total(records: list[QtyRecord], rates: dict[tuple[str, str], float]) -> float:
    """Apply a {(trade,unit): rate} map to the calculated totals."""
    totals = calculate(records)
    grand = 0.0
    for trade, byunit in totals.items():
        for unit, qty in byunit.items():
            rate = rates.get((trade, unit))
            if rate is not None:
                grand += qty * rate
    return grand
