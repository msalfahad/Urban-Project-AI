"""E8 — Waste Logic.

Waste is per material, not one blind percentage — marble waste and porcelain
waste are not the same problem. Given a net (measured) quantity, this returns the
gross (order) quantity a trade must actually buy. Deterministic; the factors are
tunable to Urban Projects' real experience over time (E20 feeds this).
"""

from __future__ import annotations

import math

# Fractional waste allowance by material family (0.10 = 10% extra to order).
WASTE_FACTORS = {
    "marble": 0.15,
    "granite": 0.12,
    "porcelain": 0.10,
    "ceramic": 0.10,
    "tile": 0.10,
    "block": 0.05,
    "blockwork": 0.05,
    "concrete": 0.03,
    "screed": 0.03,
    "plaster": 0.05,
    "paint": 0.08,
    "steel": 0.03,
    "cladding": 0.12,
    "gypsum": 0.08,
}
DEFAULT_WASTE = 0.05

# Arabic → family, so a takeoff description maps to the right factor.
_AR = {
    "رخام": "marble", "جرانيت": "granite", "بورسلان": "porcelain", "بورسيلين": "porcelain",
    "سيراميك": "ceramic", "طابوق": "block", "بلوك": "block", "خرسانه": "concrete",
    "خرسانة": "concrete", "لياسة": "plaster", "مساح": "plaster", "صبغ": "paint",
    "حديد": "steel", "كلادينج": "cladding", "جبس": "gypsum", "كسوة": "cladding",
}


def family_of(description: str) -> str | None:
    """Best-effort material family from an English or Arabic description."""
    d = (description or "").lower()
    for key in WASTE_FACTORS:
        if key in d:
            return key
    for ar, fam in _AR.items():
        if ar in description:
            return fam
    return None


def waste_factor(material: str) -> float:
    """The waste fraction for a material family (default if unknown)."""
    fam = family_of(material) or material.strip().lower()
    return WASTE_FACTORS.get(fam, DEFAULT_WASTE)


def gross_quantity(net: float, material: str, *, round_up_to: float | None = None) -> float:
    """Order quantity = net × (1 + waste). Optionally round up to a pack size."""
    gross = net * (1 + waste_factor(material))
    if round_up_to:
        gross = math.ceil(gross / round_up_to) * round_up_to
    return gross
