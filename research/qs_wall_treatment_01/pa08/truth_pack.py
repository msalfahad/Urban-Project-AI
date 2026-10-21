"""PA08 independent truth pack: schema, validation, sealing.

The pack is built BEFORE the production run, by hand, from the original source drawings only.  It holds physical facts
(locators, wall segments, curved segments, openings, open edges, columns, space relations, manually verified
dimensions and their basis) and never a result.  Sealing records its sha256 in the freeze; the blind run's audit
hook refuses the sealed directory; the comparison step is the first reader after the production freeze.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

from research.qs_wall_treatment_01.pa08 import config as C8

CASE_FIELDS = ["CASE_ID", "CASE_KIND", "SOURCE_SHEET", "SOURCE_LOCATOR", "WALL_SEGMENTS", "CURVED_SEGMENTS", "OPENINGS", "OPEN_EDGES", "COLUMNS", "PHYSICAL_SPACE_RELATION",
               "MANUALLY_VERIFIED_DIMENSIONS", "MEASUREMENT_BASIS", "VERIFIER", "VERIFIED_ON"]
WALL_SEGMENT_FIELDS = ["SEGMENT_ID", "A_MM", "B_MM", "THICKNESS_MM", "ROLE", "MATERIAL_PRESENT", "DEVELOPED_LENGTH_MM"]
CURVED_SEGMENT_FIELDS = ["SEGMENT_ID", "CENTRE_MM", "RADIUS_AXIS_MM", "START_ANGLE_RAD", "END_ANGLE_RAD", "THICKNESS_MM", "ROLE", "MATERIAL_PRESENT", "DEVELOPED_LENGTH_MM"]
OPENING_FIELDS = ["OPENING_ID", "HOST_SEGMENT_ID", "A_MM", "B_MM", "WIDTH_MM", "ROLE"]
COLUMN_FIELDS = ["COLUMN_ID", "CENTRE_MM", "SIDES_MM", "EXPOSED_FACES", "EMBEDDED_FACES"]
ROLES = {"WALL_SEGMENT": ["WALL", "COLUMN_FACE", "GLAZING", "NOT_MATERIAL"], "OPENING": ["DOOR", "WINDOW", "GLAZED", "OPEN_PASSAGE", "NICHE_NOT_OPENING"], "OPEN_EDGE": ["OPEN_PASSAGE", "UNRESOLVED_BY_VERIFIER"]}
FORBIDDEN_KEY_TOKENS = ("AREA", "PLASTER", "BOQ", "RESULT", "ENGINE", "BENCHMARK", "CONTRACTOR", "QUANTITY", "PRICE", "COST", "EXPECTED_OUTPUT")
SCHEMA = {"ARTIFACT": "PA08_TRUTH_PACK_SCHEMA", "VERSION": "PA08-TP-1",
          "PACK": {"PROJECT_ALIAS": "string", "BUILT_BEFORE_PRODUCTION_RUN": "true (asserted by the verifier)", "SOURCE_OF_TRUTH": "original source drawings only", "CASES": "list, at least six, one of each REQUIRED kind"},
          "CASE_FIELDS": CASE_FIELDS, "WALL_SEGMENT_FIELDS": WALL_SEGMENT_FIELDS, "CURVED_SEGMENT_FIELDS": CURVED_SEGMENT_FIELDS, "OPENING_FIELDS": OPENING_FIELDS, "COLUMN_FIELDS": COLUMN_FIELDS,
          "SOURCE_LOCATOR": {"KIND": "BBOX_MM in the drawing's model coordinates (x0, y0, x1, y1) plus SHEET / VIEW name", "RULE": "every fact of the case lies inside the locator"},
          "PHYSICAL_SPACE_RELATION": {"SPACE_COUNT": "number of physical spaces the verifier sees inside the locator", "RELATIONS": "list of (space_a, space_b, DOOR | WINDOW | OPEN | WALL)"},
          "MEASUREMENT_BASIS": ["CLEAR_FACE_TO_FACE", "AXIS", "OUTER_FACE"], "ROLES": ROLES, "REQUIRED_CASE_KINDS": C8.REQUIRED_CASE_KINDS, "OPTIONAL_CASE_KINDS": C8.OPTIONAL_CASE_KINDS,
          "FORBIDDEN": ["engine result", "final plaster area", "contractor result", "benchmark result", "any key containing " + ", ".join(FORBIDDEN_KEY_TOKENS)],
          "NEVER": ["derive truth with the production pipeline", "copy engine output into truth", "use AI consensus as truth"]}


def _walk(obj, path=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield path + "/" + str(k), k
            yield from _walk(v, path + "/" + str(k))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from _walk(v, f"{path}[{i}]")


def validate(pack):
    """Structural validation only: it never judges the facts, it judges that only facts are present."""
    errors = []
    cases = pack.get("CASES") or []
    if len(cases) < 6:
        errors.append(f"at least six cases required, {len(cases)} given")
    kinds = {c.get("CASE_KIND") for c in cases}
    for k in C8.REQUIRED_CASE_KINDS:
        if k not in kinds:
            errors.append(f"required case kind {k} ({C8.REQUIRED_CASE_KINDS[k]}) missing")
    for c in cases:
        for f in CASE_FIELDS:
            if f not in c:
                errors.append(f"{c.get('CASE_ID')}: field {f} missing")
        for w in c.get("WALL_SEGMENTS", []):
            for f in WALL_SEGMENT_FIELDS:
                if f not in w:
                    errors.append(f"{c.get('CASE_ID')}/{w.get('SEGMENT_ID')}: {f} missing")
            if w.get("ROLE") not in ROLES["WALL_SEGMENT"]:
                errors.append(f"{c.get('CASE_ID')}/{w.get('SEGMENT_ID')}: role {w.get('ROLE')} not in {ROLES['WALL_SEGMENT']}")
        for o in c.get("OPENINGS", []):
            for f in OPENING_FIELDS:
                if f not in o:
                    errors.append(f"{c.get('CASE_ID')}/{o.get('OPENING_ID')}: {f} missing")
        if c.get("MEASUREMENT_BASIS") not in SCHEMA["MEASUREMENT_BASIS"]:
            errors.append(f"{c.get('CASE_ID')}: measurement basis {c.get('MEASUREMENT_BASIS')} not declared")
    for path, key in _walk(pack):
        if any(tok in str(key).upper() for tok in FORBIDDEN_KEY_TOKENS):
            errors.append(f"forbidden key {path}: results, areas, benchmarks and prices never enter a truth pack")
    if pack.get("BUILT_BEFORE_PRODUCTION_RUN") is not True:
        errors.append("BUILT_BEFORE_PRODUCTION_RUN must be asserted true by the verifier")
    if pack.get("SOURCE_OF_TRUTH") != "original source drawings only":
        errors.append("SOURCE_OF_TRUTH must be 'original source drawings only'")
    return {"VALID": not errors, "ERRORS": errors, "CASES": len(cases), "KINDS": sorted(k for k in kinds if k)}


def seal(pack_path):
    """Copy the pack into the sealed directory and record its hash.  The blind run never reads this directory."""
    pack_path = Path(pack_path)
    pack = json.loads(pack_path.read_text("utf-8"))
    v = validate(pack)
    if not v["VALID"]:
        raise SystemExit(f"truth pack invalid: {v['ERRORS'][:5]}")
    C8.SEALED_DIR.mkdir(parents=True, exist_ok=True)
    dst = C8.SEALED_DIR / "TRUTH_PACK.json"
    shutil.copyfile(pack_path, dst)
    h = hashlib.sha256(dst.read_bytes()).hexdigest()
    rec = {"ARTIFACT": "PA08_TRUTH_SEAL", "PACK": str(dst), "SHA256": h, "CASES": v["CASES"], "KINDS": v["KINDS"], "SEALED_BEFORE_BLIND_RUN": True, "OPENED_BY": None,
           "RULE": "the comparison step is the first reader after the production freeze; any earlier open is VALIDATION_INVALID"}
    (C8.OUT8 / "PA08_TRUTH_SEAL.json").write_text(json.dumps(rec, indent=1), "utf-8")
    return rec
