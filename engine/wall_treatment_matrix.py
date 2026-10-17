"""WALL-TREATMENT TRADE MATRIX (directive PA02 §17): every physical face is
classified into treatments; sequential treatments on one face (column
bonding, then plaster) are two treatment quantities on ONE physical area,
never two wall areas."""

from __future__ import annotations

TREATMENTS = ("NORMAL_INTERNAL_PLASTER", "TILE_WALL_PREPARATION", "COLUMN_BONDING", "EXTERNAL_PLASTER",
              "CLADDING_BASE", "PARAPET_PLASTER", "STAIR_WALL_PLASTER", "OTHER", "UNKNOWN")
SEQUENCES = {
    "EXPOSED_COLUMN_FACE": ("COLUMN_BONDING", "NORMAL_INTERNAL_PLASTER"),
    "WET_ROOM_WALL_FACE": ("TILE_WALL_PREPARATION",),
    "NORMAL_WALL_FACE": ("NORMAL_INTERNAL_PLASTER",),
    "STAIR_WALL_FACE": ("STAIR_WALL_PLASTER",),
    "PARAPET_FACE": ("PARAPET_PLASTER",),
    "EXTERNAL_PLASTER_FACE": ("EXTERNAL_PLASTER",),
    "EXTERNAL_CLADDING_FACE": ("CLADDING_BASE",),
    "EXTERNAL_UNKNOWN_FACE": ("UNKNOWN",),
}


def classify(face_kind: str, *, finish_status=None) -> tuple:
    if face_kind == "EXTERNAL_FACE":
        return {"EXTERNAL_PLASTER_CONFIRMED": ("EXTERNAL_PLASTER",), "EXTERNAL_CLADDING_CONFIRMED": ("CLADDING_BASE",),
                "PLASTER_BASE_BEHIND_CLADDING": ("CLADDING_BASE",)}.get(finish_status, ("UNKNOWN",))
    return SEQUENCES.get(face_kind, ("UNKNOWN",))


def treatment_lines(*, face_id, physical_area_m2, area_state, face_kind, finish_status=None, unit="m2") -> dict:
    """One physical area; one line per treatment in sequence; the physical
    area is reported once and never summed across the treatment lines."""
    seq = classify(face_kind, finish_status=finish_status)
    lines = [{"FACE_ID": face_id, "TREATMENT": t, "SEQUENCE": i + 1, "UNIT": unit,
              "VALUE": physical_area_m2 if t != "UNKNOWN" else None,
              "QUANTITY_STATE": ("NOT_ESTABLISHED" if t == "UNKNOWN" else area_state)} for i, t in enumerate(seq)]
    return {"FACE_ID": face_id, "PHYSICAL_AREA_M2": physical_area_m2, "PHYSICAL_AREA_STATE": area_state,
            "TREATMENTS": lines, "PHYSICAL_AREA_COUNTED_ONCE": True}
