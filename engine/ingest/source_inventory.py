"""Source inventory / sufficiency (PA05 §15) and the ingestion manifest (§16)."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from engine.ingest import ENGINE_VERSION

SOURCE_KINDS = ("ARCHITECTURAL_PLAN", "SECTION", "ELEVATION", "ROOF_PLAN", "STRUCTURAL_PLAN", "BEAM_SCHEDULE", "COLUMN_SCHEDULE", "SANITARY", "ELECTRICAL",
                "DOOR_WINDOW_SCHEDULE", "FINISH_SCHEDULE", "DETAIL", "CAD_MODEL", "OWNER_INPUTS")
ROLE_TO_KIND = {"FLOOR_PLAN": "ARCHITECTURAL_PLAN", "ROOF_PLAN": "ROOF_PLAN", "SECTION": "SECTION", "ELEVATION": "ELEVATION", "SECTION_ELEVATION": "ELEVATION",
                "STRUCTURAL_PLAN": "STRUCTURAL_PLAN", "BEAM_SCHEDULE": "BEAM_SCHEDULE", "COLUMN_SCHEDULE": "COLUMN_SCHEDULE", "DOOR_WINDOW_SCHEDULE": "DOOR_WINDOW_SCHEDULE",
                "FINISH_SCHEDULE": "FINISH_SCHEDULE", "DETAIL": "DETAIL", "REFLECTED_CEILING_PLAN": "ARCHITECTURAL_PLAN"}
# what a missing source prevents (trade question -> best attainable status)
BLOCKS = {
    "FINISH_SCHEDULE": [("WALL_TILE_HEIGHT", "cannot be source-established; wet-room areas stay lm only"), ("EXTERNAL_FINISH_SYSTEM", "external faces stay geometric reference only"),
                        ("CEILING_TREATMENT", "ceiling regions stay geometry only"), ("PLASTER_HEIGHT_BY_ROOM", "heights need an owner parameter")],
    "DOOR_WINDOW_SCHEDULE": [("OPENING_SIZES", "actual sizes stay provisional where only a leaf width is drawn"), ("REVEAL_DEPTHS", "reveals stay temporary defaults")],
    "SECTION": [("STOREY_HEIGHTS", "levels cannot be source-established"), ("DOUBLE_HEIGHT_FACES", "vertical ranges cannot be proved"), ("PARAPET_HEIGHTS", "parapet faces stay provisional")],
    "ELEVATION": [("FACADE_OPENINGS", "external openings stay unknown"), ("PARAPET_TOPS", "roof-edge tops stay unknown")],
    "STRUCTURAL_PLAN": [("BEAM_SOFFITS", "column exposed heights stay not established"), ("SLAB_OPENINGS", "void extents rely on architectural X marks only")],
    "BEAM_SCHEDULE": [("BEAM_DEPTHS", "downstand faces stay not established")],
    "COLUMN_SCHEDULE": [("COLUMN_SECTIONS", "girths rely on architectural loops only")],
    "ROOF_PLAN": [("ROOF_EDGE_RUNS", "parapet lengths stay unknown")],
    "SANITARY": [("WET_ROOM_FIXTURES", "wet-room identity relies on labels only")],
    "DETAIL": [("KERB_AND_COPING_PROFILES", "profiles stay lower bounds")],
    "CAD_MODEL": [("AUTHORED_GEOMETRY", "every length becomes a raster interpretation")],
    "OWNER_INPUTS": [("PARAMETRIC_HEIGHTS", "no parametric areas at all")],
}


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def inventory(sheet_roles, extra_kinds=()):
    """sheet_roles: [{"SHEET_ID", "FINAL_ROLE", ...}] -> available kinds, missing kinds and the trade questions each missing kind blocks."""
    present = {ROLE_TO_KIND[r["FINAL_ROLE"]] for r in sheet_roles if r["FINAL_ROLE"] in ROLE_TO_KIND} | set(extra_kinds)
    missing = [k for k in SOURCE_KINDS if k not in present]
    return {"AVAILABLE": sorted(present), "MISSING": missing, "BLOCKED_QUESTIONS": {k: [{"QUESTION": q, "CONSEQUENCE": c} for q, c in BLOCKS.get(k, [])] for k in missing},
            "MUST_RUN_BEFORE_QUANTITIES": True}


def manifest(*, project_id, source_files, drawing_family, revision, sheet_index, view_roles, cad_units, transforms, available_schedules, missing_sources,
             owner_inputs, rule_version, extra=None):
    files = [{"PATH": str(p), "SHA256": sha(p) if Path(p).exists() else None, "PRESENT": Path(p).exists()} for p in source_files]
    body = {"ARTIFACT": "PROJECT_INGESTION_MANIFEST", "PROJECT_ID": project_id, "SOURCE_FILES": files, "FILE_HASHES": {f["PATH"]: f["SHA256"] for f in files},
            "DRAWING_FAMILY": drawing_family, "REVISION": revision, "SHEET_INDEX": sheet_index, "VIEW_ROLES": view_roles, "CAD_UNITS": cad_units, "TRANSFORMS": transforms,
            "AVAILABLE_SCHEDULES": available_schedules, "MISSING_SOURCES": missing_sources, "KNOWN_OWNER_INPUTS": owner_inputs, "RULE_VERSION": rule_version, "ENGINE_VERSION": ENGINE_VERSION}
    if extra:
        body.update(extra)
    body["MANIFEST_DIGEST"] = hashlib.sha256(json.dumps(body, sort_keys=True, default=str).encode()).hexdigest()
    return body
