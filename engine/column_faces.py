"""COLUMN FACE REGISTER (directive PA02 §5): structural size and plasterable
exposed girth are different facts. Each of the four faces carries its own
exposure; a face buried in or flush with another construction is excluded."""

from __future__ import annotations

from engine.quantity_state import weakest

EXPOSURES = ("EXPOSED", "FLUSH_WITH_WALL_FACE", "BURIED_IN_WALL", "AGAINST_OTHER_CONSTRUCTION",
             "PARTIALLY_EXPOSED", "NOT_ESTABLISHED")
FACES = ("A", "B", "C", "D")


def column(*, column_id, width_m, depth_m, exposures: dict, host_wall_relation, occlusion=None,
           bonding_required, plaster_required, source, exposure_source, partial_lengths=None) -> dict:
    for f in FACES:
        if exposures.get(f) not in EXPOSURES:
            raise ValueError(f"{column_id}: face {f} exposure {exposures.get(f)!r} not in {EXPOSURES}")
    sides = {"A": width_m, "B": depth_m, "C": width_m, "D": depth_m}
    girth = 0.0
    counted = []
    for f in FACES:
        e = exposures[f]
        if e == "EXPOSED":
            girth += sides[f]
            counted.append(f)
        elif e == "PARTIALLY_EXPOSED":
            pl = (partial_lengths or {}).get(f)
            if pl is None:
                raise ValueError(f"{column_id}: PARTIALLY_EXPOSED face {f} needs a partial length")
            girth += pl
            counted.append(f)
    state = weakest([source, exposure_source] + (["NOT_ESTABLISHED"] if any(exposures[f] == "NOT_ESTABLISHED" for f in FACES) else []))
    return {"COLUMN_ID": column_id, "SECTION_WIDTH": width_m, "SECTION_DEPTH": depth_m,
            "FACE_A_EXPOSURE": exposures["A"], "FACE_B_EXPOSURE": exposures["B"],
            "FACE_C_EXPOSURE": exposures["C"], "FACE_D_EXPOSURE": exposures["D"],
            "HOST_WALL_RELATION": host_wall_relation, "FINISH_FACE_OCCLUSION": occlusion,
            "BONDING_TREATMENT_REQUIRED": bonding_required, "PLASTER_TREATMENT_REQUIRED": plaster_required,
            "STRUCTURAL_GIRTH_LM": round(2 * (width_m + depth_m), 3),
            "EXPOSED_PLASTERABLE_GIRTH_LM": round(girth, 3), "FACES_COUNTED": counted,
            "GIRTH_STATE": state, "SOURCE": source, "EXPOSURE_SOURCE": exposure_source,
            "STRUCTURAL_SIZE_IS_NOT_THE_PLASTER_GIRTH": True}
