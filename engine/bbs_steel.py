"""E2 — BBS Steel Engine.

Steel weight from the bar schedules on the drawing (the real quantity). The kg/m³
sanity check now lives in engine/rebar_sanity_qa.py — never as the official
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


# The kg/m3 sanity band moved to engine/rebar_sanity_qa.py (QA layer). The old names stay as deprecated
# wrappers resolved lazily, so the bar-schedule code above never depends on them.
_MOVED = {"ratio_check": "ratio_band_check", "RATIO_YELLOW": "RATIO_YELLOW", "RATIO_RED": "RATIO_RED"}


def __getattr__(name):
    if name in _MOVED:
        import warnings
        from engine import rebar_sanity_qa as _qa
        warnings.warn(f"engine.bbs_steel.{name} moved to engine.rebar_sanity_qa.{_MOVED[name]} (QA only)",
                      DeprecationWarning, stacklevel=2)
        return getattr(_qa, _MOVED[name])
    raise AttributeError(name)
