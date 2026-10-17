"""URBAN METHOD REGISTER (V1) - reusable measurement methods: versioned, scope-limited, overrideable. A method is
not a project fact: it says HOW to measure when the source is silent, never WHAT the project contains.

Each method: id@version, statement, applies_to, never_applies_to, parameters, precedence (what outranks it).
applies(method_id, element_kind) -> bool; a kind listed in never_applies_to is refused even if a caller asks.
resolve(method_id, project_override) -> the parameters in force with their authority.

Project-agnostic; stdlib only.
"""

from __future__ import annotations

import hashlib
import json

METHODS = {
    "URBAN-FLOOR-FINISH-BEFORE-CABINETRY-METHOD@v1": {
        "statement": "the floor finish is laid before fixed cabinetry / wardrobes / joinery and continues under them",
        "applies_to": ["WARDROBE", "FIXED_JOINERY", "KITCHEN_CABINET", "VANITY_CABINET"],
        "never_applies_to": ["WALL", "COLUMN", "PLINTH", "SHAFT", "DUCT", "CURB"],
        "parameters": {}, "precedence": ["PROJECT_SPECIFICATION"]},
    "URBAN_CURVED_ALUMINIUM_INNER_FACE_METHOD@v1": {
        "statement": "curved aluminium / glazing is measured commercially on the inner (smallest-radius) arc; inner, "
                     "centre, outer and chord are always published",
        "applies_to": ["CURVED_GLAZING"], "never_applies_to": ["STRAIGHT_GLAZING"],
        "parameters": {"basis": "INNER"}, "precedence": ["PROJECT_OVERRIDE"]},
    "URBAN-WET-WALL-TILE-FULL-HEIGHT@v1": {
        "statement": "wet / service rooms: visible wall tile to the finished ceiling",
        "applies_to": ["WET_ROOM", "SERVICE_ROOM"], "never_applies_to": ["DRY_ROOM"],
        "parameters": {"to": "FINISHED_CEILING"}, "precedence": ["PROJECT_SPECIFICATION"]},
    "URBAN-PLASTER-TO-MASONRY-TERMINATION@v1": {
        "statement": "internal plaster covers the full masonry face to the structural termination, above a false "
                     "ceiling included", "applies_to": ["MASONRY_WALL_FACE"], "never_applies_to": ["DRY_LINING"],
        "parameters": {}, "precedence": ["PROJECT_SPECIFICATION"]},
    "URBAN-PAINT-TO-FINISHED-CEILING@v1": {
        "statement": "paint runs to the finished ceiling, taken as the controlling soffit minus a ceiling allowance "
                     "unless a ceiling level is in the source; concealed plaster in dry rooms is not painted",
        "applies_to": ["DRY_ROOM_WALL_FACE"], "never_applies_to": ["WET_ROOM_TILED_FACE"],
        "parameters": {"ceiling_allowance_m": 0.150}, "precedence": ["SOURCE_CEILING_LEVEL", "PROJECT_SPECIFICATION"]},
    "URBAN-ROOF-WATERPROOF-UPTURN-200@v1": {
        "statement": "roof membrane upturn 0.20 m at every roof-region edge; wet-room upturn stays 0.15 m; laps are a "
                     "separate procurement factor", "applies_to": ["ROOF_REGION"], "never_applies_to": ["WET_ROOM"],
        "parameters": {"roof_upturn_m": 0.20, "wet_upturn_m": 0.15}, "precedence": ["PROJECT_SPECIFICATION"]},
    "URBAN-COLUMN-HEIGHT-TO-CONTROLLING-MEMBER@v1": {
        "statement": "column concrete height = structural storey interval - depth of the deepest member framing into "
                     "THAT column (slab thickness when none); never a global depth",
        "applies_to": ["COLUMN"], "never_applies_to": ["NECK", "WALL"],
        "parameters": {}, "precedence": ["SOURCE_COLUMN_HEIGHT", "STRUCTURAL_LEVELS"]},
    "URBAN-BEAM-TYPE-FROM-SCHEDULE-LENGTH-FROM-PLAN@v1": {
        "statement": "beam type from the bound plan tag, section from its own schedule namespace, length from the bound "
                     "plan band (four bases stored apart)", "applies_to": ["BEAM", "CONTINUOUS_BEAM"],
        "never_applies_to": ["STRAP"], "parameters": {}, "precedence": ["EXPLICIT_LOCAL_DIMENSION"]},
    "URBAN-NON-OVERLAPPING-SLAB-BEAM-MODEL@v1": {
        "statement": "slab = net plate x t; downstand = clear length x B x (D - t); joint = column area x (D_ctrl - t); "
                     "gross beam view reported separately", "applies_to": ["SLAB", "BEAM", "JOINT"],
        "never_applies_to": [], "parameters": {}, "precedence": ["PROJECT_SPECIFICATION"]},
}


def applies(method_id, element_kind) -> bool:
    m = METHODS[method_id]
    if element_kind in m["never_applies_to"]:
        return False
    return element_kind in m["applies_to"]


def resolve(method_id, project_override=None) -> dict:
    m = METHODS[method_id]
    params = dict(m["parameters"])
    auth = method_id
    if project_override:
        params.update(project_override.get("parameters", {}))
        auth = f"PROJECT_OVERRIDE {project_override.get('id')} over {method_id}"
    return {"method": method_id, "parameters": params, "authority": auth}


def register() -> dict:
    rows = [dict({"id": k}, **v) for k, v in sorted(METHODS.items())]
    rec = {"SCHEMA": "URBAN_METHOD_REGISTER_V1", "methods": rows,
           "rule": "a method is versioned, scope-limited and overrideable; it is never a project fact"}
    rec["digest"] = hashlib.sha256(json.dumps(rows, sort_keys=True).encode()).hexdigest()
    return rec
