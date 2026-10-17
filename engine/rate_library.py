"""E4 — Rate Library.

Holds material, installed and selling rates, each with its unit, contractor and
the category it belongs to. Seeded from real pricing (a Urban Projects Manager
"Cost By Category" export), it is the single place the pricing step looks up a
rate — code applies it, no AI ever invents a number.

Deliberately dependency-free and serialisable (to/from plain dicts) so a library
can live in Firestore, a JSON file, or memory.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any


@dataclass
class RateItem:
    """One priced line from an estimate."""

    description: str
    category: str           # بند / category, e.g. "بند السيراميك"
    type: str = ""          # General | Labor | Material | Logistics | lump
    contractor: str = ""
    qty: float | None = None
    unit: str = ""          # qty | item | m3 | ton | m2 | ...
    unit_cost: float | None = None
    total: float | None = None

    def implied_unit_cost(self) -> float | None:
        if self.qty and self.total is not None and self.qty != 0:
            return self.total / self.qty
        return self.unit_cost


@dataclass
class RateCategory:
    name: str
    items: list[RateItem] = field(default_factory=list)
    stated_total: float | None = None

    def computed_total(self) -> float:
        return sum(i.total for i in self.items if i.total is not None)

    def reconciles(self, tol: float = 1.0) -> bool:
        """True if the items sum to the stated category total (within tol KWD)."""
        if self.stated_total is None:
            return True
        return abs(self.computed_total() - self.stated_total) <= tol


@dataclass
class RateLibrary:
    project: str = ""
    currency: str = "KWD"
    categories: list[RateCategory] = field(default_factory=list)
    grand_total: float | None = None

    # -- lookups ----------------------------------------------------------
    def all_items(self) -> list[RateItem]:
        return [i for c in self.categories for i in c.items]

    def find(self, keyword: str) -> list[RateItem]:
        """Items whose description or category contains the keyword."""
        k = keyword.strip()
        return [i for i in self.all_items() if k in i.description or k in i.category]

    def rate_for(self, keyword: str, unit: str | None = None) -> float | None:
        """The unit cost of the first matching item (optionally unit-filtered)."""
        for i in self.find(keyword):
            if unit is None or i.unit == unit:
                return i.implied_unit_cost()
        return None

    def computed_grand_total(self) -> float:
        return sum(c.computed_total() for c in self.categories)

    # -- serialisation ----------------------------------------------------
    def to_dict(self) -> dict[str, Any]:
        return {
            "project": self.project,
            "currency": self.currency,
            "grand_total": self.grand_total,
            "categories": [
                {
                    "name": c.name,
                    "stated_total": c.stated_total,
                    "items": [asdict(i) for i in c.items],
                }
                for c in self.categories
            ],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RateLibrary":
        cats = []
        for c in data.get("categories", []):
            items = [RateItem(**it) for it in c.get("items", [])]
            cats.append(RateCategory(name=c.get("name", ""), items=items,
                                     stated_total=c.get("stated_total")))
        return cls(
            project=data.get("project", ""),
            currency=data.get("currency", "KWD"),
            categories=cats,
            grand_total=data.get("grand_total"),
        )

    def reconciliation_report(self, tol: float = 1.0) -> list[str]:
        """Human-readable notes on any category that doesn't sum to its total."""
        out = []
        for c in self.categories:
            if not c.reconciles(tol):
                out.append(f"{c.name}: items sum to {c.computed_total():g} but "
                           f"stated total is {c.stated_total:g}")
        if self.grand_total is not None:
            g = self.computed_grand_total()
            if abs(g - self.grand_total) > tol:
                out.append(f"grand total: items sum to {g:g} but stated {self.grand_total:g}")
        return out
