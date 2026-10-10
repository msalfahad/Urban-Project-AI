"""WATERPROOFING POLICY (V1) - physical QTO is the net surface; laps are a separate procurement factor that exists
only when the membrane system is known.

roof()   URBAN-ROOF-WATERPROOF-UPTURN-200@v1: net exposed roof area + region perimeter x 0.20 m upturn.
wet()    wet-room floor area + wet-room perimeter x 0.15 m upturn (door openings deducted from the upturn length when
         their widths are known; otherwise the gross perimeter is used and stated).
procurement() lap / overlap factor applied to the physical QTO only when a system with a stated lap is named.

Project-agnostic; stdlib only.
"""

from __future__ import annotations

POLICY_ID = "WATERPROOFING_POLICY_V1"
ROOF_UPTURN_M = 0.20
WET_UPTURN_M = 0.15


def roof(*, area_m2, perimeter_m, region) -> dict:
    if area_m2 is None or perimeter_m is None:
        return {"region": region, "state": "BLOCKED_REGION", "physical_m2": None}
    up = perimeter_m * ROOF_UPTURN_M
    return {"region": region, "state": "COMPUTED", "flat_m2": round(area_m2, 6), "upturn_m2": round(up, 6),
            "physical_m2": round(area_m2 + up, 6), "upturn_m": ROOF_UPTURN_M,
            "method": "URBAN-ROOF-WATERPROOF-UPTURN-200@v1", "laps": "NOT_INCLUDED (procurement factor)"}


def wet(*, floor_m2, perimeter_m, door_widths_m=None, room) -> dict:
    if floor_m2 is None or perimeter_m is None:
        return {"room": room, "state": "BLOCKED_ROOM", "physical_m2": None}
    L = perimeter_m - (sum(door_widths_m) if door_widths_m else 0.0)
    up = L * WET_UPTURN_M
    return {"room": room, "state": "COMPUTED", "floor_m2": round(floor_m2, 6), "upturn_length_m": round(L, 6),
            "upturn_basis": "perimeter - door widths" if door_widths_m else "gross perimeter (door widths unknown)",
            "upturn_m2": round(up, 6), "physical_m2": round(floor_m2 + up, 6), "upturn_m": WET_UPTURN_M,
            "laps": "NOT_INCLUDED (procurement factor)"}


def procurement(physical_m2, *, system=None, lap_factor=None) -> dict:
    if not system or lap_factor is None:
        return {"state": "NOT_APPLIED", "why": "membrane system / lap not known", "procurement_m2": None}
    return {"state": "COMPUTED", "system": system, "lap_factor": lap_factor,
            "procurement_m2": round(physical_m2 * lap_factor, 6)}
