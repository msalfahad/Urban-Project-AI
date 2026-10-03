"""PA04 §8 wall-treatment sequences and §9 height parameter table.

    python3 -m research.qs_wall_treatment_01.pa04.heights_treatments
"""

from __future__ import annotations

from engine import height_parameters as HP
from engine import wall_treatment_matrix as WTM
from research.qs_wall_treatment_01.pa04 import common as C

TREATMENTS_V2 = ("CEMENT_SPLATTER", "COLUMN_BONDING_MATERIAL", "INTERNAL_PLASTER", "EXTERNAL_PLASTER", "TILE_WALL_PREPARATION", "CLADDING_BASE", "PAINT_BASE", "OTHER")
SEQUENCES_V2 = {
    "NORMAL_WALL_FACE": ("CEMENT_SPLATTER", "INTERNAL_PLASTER", "PAINT_BASE"),
    "EXPOSED_COLUMN_FACE": ("COLUMN_BONDING_MATERIAL", "CEMENT_SPLATTER", "INTERNAL_PLASTER", "PAINT_BASE"),
    "WET_ROOM_WALL_FACE": ("CEMENT_SPLATTER", "TILE_WALL_PREPARATION"),
    "EXTERNAL_PLASTER_FACE": ("CEMENT_SPLATTER", "EXTERNAL_PLASTER"),
    "EXTERNAL_CLADDING_FACE": ("CLADDING_BASE",),
    "EXTERNAL_UNKNOWN_FACE": ("OTHER",),
    "STAIR_WALL_FACE": ("CEMENT_SPLATTER", "INTERNAL_PLASTER", "PAINT_BASE"),
    "PARAPET_FACE": ("CEMENT_SPLATTER", "EXTERNAL_PLASTER"),
}


@C.timed("heights_treatments")
def run():
    owner = C.read("P7757_OWNER_PARAMETERS.json", C.OUT)
    params = [
        HP.parameter(scope="GROUND_NORMAL_INTERNAL", value=3.20, source="owner parameter NORMAL_INTERNAL_PLASTER_HEIGHT (OWNER_PROJECT_INPUT)", status="OWNER_AUTHORISED",
                     effective_scope="GF normal-height internal faces already measured under that rule (SALOON etc.)", owner_override="P7757_OWNER_PARAMETERS.json NORMAL_INTERNAL_PLASTER_HEIGHT", revision=1),
        HP.parameter(scope="FIRST_NORMAL_INTERNAL", value=None, source="no owner authorisation for the FF; sections give a 4.20 storey (+5.50 -> +9.70) and no ceiling level", status="NOT_ESTABLISHED",
                     effective_scope="FF room faces (FF_PHYSICAL_FACE_REGISTER): lm only", note="3.20 is NOT extended to the FF by analogy"),
        HP.parameter(scope="SECOND_ROOF_NORMAL_INTERNAL", value=None, source="tower / roof rooms not measured", status="NOT_ESTABLISHED", effective_scope="ROOF copy rooms"),
        HP.parameter(scope="RECEPTION_DOUBLE_HEIGHT", value=None, source="RECEPTION_VERTICAL_FACE_REGISTER: candidate 8.54 (+1.00 -> +9.54) unproved by section", status="NOT_ESTABLISHED",
                     effective_scope="RVF-S-B and the overhanging faces", note="owner item RECEPTION-SECTION-SOURCE"),
        HP.parameter(scope="STAIR_WELL_BY_SEGMENT", value=None, source="per-storey segments from the level chains", status="PROVISIONAL", effective_scope="block stair faces per storey",
                     segments={"GF": 5.20, "FF": 4.20, "ROOF": 4.20}, note="segment heights established from levels; the faces stay GEOMETRIC_REFERENCE_ONLY until deductions exist"),
        HP.parameter(scope="EXTERNAL_FACE_BY_STOREY", value=None, source="DWG NW elevation chain 100 / 870 / 420 / 50", status="PROVISIONAL", effective_scope="facade faces",
                     segments={"GF": 4.50, "FF": 4.20, "TOWER": 4.20, "TOP": 0.50}, note="geometric only; finish system unknown"),
        HP.parameter(scope="PARAPET_FACE", value=None, source="per edge (ROOF_EDGE_REGISTER_V2)", status="PROVISIONAL", effective_scope="parapet faces", segments={"SE_SOLID": "1.22 / 1.40 dual", "NE": 1.40, "SW": "~1.53", "TOWER": 0.50}),
        HP.parameter(scope="WET_ROOM_TILE_PREP", value=None, source="no finishes schedule", status="NOT_ESTABLISHED", effective_scope="wet-room faces: lm only", note="no universal tiled height invented"),
    ]
    table = HP.table(params)
    seqs = {k: {"SEQUENCE": v, "PHYSICAL_AREA_COUNTED_ONCE": True, "SEPARATE_CONTRACTUAL_OPERATIONS": True} for k, v in SEQUENCES_V2.items()}
    example = WTM.treatment_lines(face_id="example", physical_area_m2=10.0, area_state="PROVISIONAL_QUANTITY", face_kind="EXPOSED_COLUMN_FACE")
    C.METRICS.setdefault("heights_treatments", {}).update({"AI_CALLS": 0, "DETERMINISTIC_OPS": len(params) + len(seqs)})
    C.write("HEIGHT_PARAMETER_TABLE.json", {"ARTIFACT": "HEIGHT_PARAMETER_TABLE", **table, "RULE": "no global plaster height; 3.20 only where already authorised; unknown height still allows lm outputs"})
    C.write("WALL_TREATMENT_SEQUENCES_V2.json", {"ARTIFACT": "WALL_TREATMENT_SEQUENCES_V2", "TREATMENTS": TREATMENTS_V2, "SEQUENCES": seqs,
                                                 "RULE": "one physical wall area receives sequential treatments; geometry reports the area once; trade lines repeat it only as separate contractual operations",
                                                 "ENGINE_EXAMPLE": example})
    return {"MISSING_SCOPES": table["MISSING_SCOPES"], "PARAMS": [(p["SCOPE"], p["VALUE"], p["STATUS"]) for p in params]}


if __name__ == "__main__":
    import json
    print(json.dumps(run(), indent=1, default=str))
