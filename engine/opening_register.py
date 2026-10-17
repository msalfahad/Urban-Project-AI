"""OPENING REGISTER (§11): PHYSICAL_OPENING, MEASUREMENT_CLOSURE,
OPENING_DEDUCTION and REVEAL_QUANTITY are four records, never one.

An opening never disappears because a measurement polygon was closed
across it: the closure is a QS_MEASUREMENT_GEOMETRY object with zero
material; the opening stays a PHYSICAL_GEOMETRY object with its own
deduction and reveal, computed from the applicable rulebook.
"""

from __future__ import annotations

from engine.quantity_state import weakest

FIELDS = ("OPENING_ID", "HOST_FACE", "WIDTH", "HEIGHT", "AREA", "SOURCE",
          "DEDUCTION_RULE", "DEDUCTION_AMOUNT", "REVEAL_DEPTH", "REVEAL_LENGTH",
          "REVEAL_AREA", "STATUS")
DEDUCTION_RULES = {
    "FULL_OPENING_DEDUCTION": lambda a: a,
    "HALF_OPENING_DEDUCTION": lambda a: a / 2.0,
    "NO_DEDUCTION": lambda a: 0.0,
}


def opening(*, opening_id, host_face, opening_type, width_m, width_source,
            height_m, height_source, deduction_rule, reveal_depth_m=None,
            reveal_depth_source=None, reveal_sides="JAMBS_AND_HEAD") -> dict:
    if deduction_rule not in DEDUCTION_RULES:
        raise ValueError(f"unknown deduction rule {deduction_rule}")
    area = (round(width_m * height_m, 4) if isinstance(width_m, (int, float))
            and isinstance(height_m, (int, float)) else None)
    ded = DEDUCTION_RULES[deduction_rule](area) if area is not None else None
    if reveal_sides == "JAMBS_AND_HEAD":
        rl = (round(2 * height_m + width_m, 4) if area is not None else None)
    elif reveal_sides == "JAMBS_HEAD_AND_SILL":
        rl = (round(2 * height_m + 2 * width_m, 4) if area is not None else None)
    else:
        raise ValueError(f"unknown reveal sides {reveal_sides}")
    ra = (round(rl * reveal_depth_m, 4) if rl is not None
          and isinstance(reveal_depth_m, (int, float)) else None)
    st = weakest([width_source, height_source])
    return {
        "LAYER": "PHYSICAL_GEOMETRY", "OPENING_ID": opening_id, "TYPE": opening_type,
        "HOST_FACE": host_face,
        "WIDTH": width_m, "WIDTH_SOURCE": width_source,
        "HEIGHT": height_m, "HEIGHT_SOURCE": height_source,
        "AREA": area, "SOURCE": {"WIDTH": width_source, "HEIGHT": height_source},
        "DEDUCTION_RULE": deduction_rule, "DEDUCTION_AMOUNT": (round(ded, 4) if ded is not None else None),
        "REVEAL_DEPTH": reveal_depth_m, "REVEAL_DEPTH_SOURCE": reveal_depth_source,
        "REVEAL_SIDES": reveal_sides, "REVEAL_LENGTH": rl, "REVEAL_AREA": ra,
        "REVEAL_STATE": (weakest([st, reveal_depth_source]) if ra is not None else "NOT_ESTABLISHED"),
        "STATUS": st,
        "MEASUREMENT_CLOSURE": {"SEPARATE_OBJECT": True, "MATERIAL_PRESENT": False,
                                "NOTE": "a closure across this opening lives in the "
                                        "QS_MEASUREMENT_GEOMETRY layer and never removes this record"},
    }
