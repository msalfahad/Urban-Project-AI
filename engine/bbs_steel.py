"""E2 — BBS Steel Engine.

Steel weight from the bar schedules on the drawing (the real quantity), with the
kg/m³ ratios currently in use kept only as a sanity check — never as the official
quantity. Deterministic; the bar data comes from the drawing's schedules (e.g.
ST7757 p9 footing reinforcement).

Standard bar mass per metre (kg/m) by diameter (mm), from nominal steel density.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# kg per metre for standard reinforcement diameters (mm).
BAR_KG_PER_M = {
    6: 0.222, 8: 0.395, 10: 0.617, 12: 0.888, 14: 1.208,
    16: 1.578, 18: 1.998, 20: 2.466, 25: 3.853, 32: 6.313,
}


@dataclass
class Bar:
    diameter_mm: int
    length_m: float
    count: float

    def weight_kg(self) -> float:
        if self.diameter_mm not in BAR_KG_PER_M:
            raise ValueError(f"no mass table for Ø{self.diameter_mm}")
        return self.count * self.length_m * BAR_KG_PER_M[self.diameter_mm]


@dataclass
class SteelResult:
    total_kg: float
    by_diameter: dict[int, float] = field(default_factory=dict)


def steel_from_bars(bars: list[Bar]) -> SteelResult:
    """Total reinforcement weight from a bar schedule."""
    by_dia: dict[int, float] = {}
    for b in bars:
        by_dia[b.diameter_mm] = by_dia.get(b.diameter_mm, 0.0) + b.weight_kg()
    return SteelResult(total_kg=sum(by_dia.values()), by_diameter=by_dia)


# kg/m3 sanity band (a check, not the quantity).
RATIO_YELLOW = (70.0, 200.0)
RATIO_RED = (40.0, 300.0)


def ratio_check(steel_kg: float, concrete_m3: float) -> dict:
    """Compare steel/concrete against the sanity band."""
    if concrete_m3 <= 0:
        return {"ratio": None, "status": "n/a"}
    ratio = steel_kg / concrete_m3
    if ratio < RATIO_RED[0] or ratio > RATIO_RED[1]:
        status = "RED"
    elif ratio < RATIO_YELLOW[0] or ratio > RATIO_YELLOW[1]:
        status = "YELLOW"
    else:
        status = "OK"
    return {"ratio": ratio, "status": status,
            "band": {"yellow": RATIO_YELLOW, "red": RATIO_RED}}
