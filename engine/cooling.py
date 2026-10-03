"""E9 — Cooling Load.

AC sizing per floor for package units, with a stated rule behind it — replacing
the current blind 9,750 KWD lump allowance. Kuwait's climate drives a high load;
this uses a per-m² cooling intensity (BTU/h) and standard package-unit sizes.

Deterministic and transparent: every number traces to the floor area and the
stated intensity. A proper thermal load calc (glazing, orientation, occupancy)
is a later refinement; this is an honest sizing rule, not a guess.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

# Cooling intensity (BTU/h per m²) by space type — Kuwait residential, provisional.
INTENSITY_BTU_M2 = {
    "living": 600,      # majlis / reception, high glazing
    "bedroom": 500,
    "kitchen": 700,
    "service": 400,
    "default": 550,
}
BTU_PER_TON = 12000
# Common package-unit sizes in tons of refrigeration.
PACKAGE_UNITS_TON = [1.5, 2.0, 2.5, 3.0, 4.0, 5.0]


@dataclass
class FloorLoad:
    floor: str
    area_m2: float
    space_type: str
    tons: float
    units: list[float] = field(default_factory=list)


def tons_for_area(area_m2: float, space_type: str = "default") -> float:
    intensity = INTENSITY_BTU_M2.get(space_type, INTENSITY_BTU_M2["default"])
    return area_m2 * intensity / BTU_PER_TON


def select_units(tons: float) -> list[float]:
    """Pick package units summing to at least the required tonnage.

    Greedy from the largest standard size; simple and predictable.
    """
    remaining = tons
    units: list[float] = []
    for size in sorted(PACKAGE_UNITS_TON, reverse=True):
        while remaining >= size - 1e-9:
            units.append(size)
            remaining -= size
    if remaining > 1e-6:
        units.append(min(s for s in PACKAGE_UNITS_TON if s >= remaining))
    return units


def floor_load(floor: str, area_m2: float, space_type: str = "default") -> FloorLoad:
    tons = tons_for_area(area_m2, space_type)
    return FloorLoad(floor=floor, area_m2=area_m2, space_type=space_type,
                     tons=tons, units=select_units(tons))


def total_tons(loads: list[FloorLoad]) -> float:
    return sum(l.tons for l in loads)
