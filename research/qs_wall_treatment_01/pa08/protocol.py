"""PA08 protocol writer: the six prepared-but-not-executed artifacts, the active SECOND_REGRESSION_SOURCE_REQUIRED record
and the PROJECT_RULE_CANDIDATES register (owner conventions deferred until the independent villa)."""

from __future__ import annotations

import json
from pathlib import Path

from research.qs_wall_treatment_01.pa07 import validation as V7
from research.qs_wall_treatment_01.pa08 import blind_run as BR, config as C8, gate_v4 as G4, source_acceptance as SA, truth_pack as TP

PROTOCOL = {
    "ARTIFACT": "PA08_VALIDATION_PROTOCOL", "VERSION": "PA08-VP-1", "STATUS": "PREPARED_NOT_EXECUTED",
    "PURPOSE": "blind validation of the generic PA07R1 geometry / topology engine on one villa never used to develop it",
    "NEVER_THE_VALIDATION_PROJECT": sorted(C8.DEVELOPMENT_PROJECTS), "REGRESSION_ONLY": sorted(C8.DEVELOPMENT_PROJECTS),
    "STEPS": [
        {"N": 1, "STEP": "SOURCE_ACCEPTANCE", "MODULE": "pa08.source_acceptance.accept", "OUTPUT": "PA08_SOURCE_ACCEPTANCE.json", "STOP_IF": "HAS_THIS_PROJECT_BEEN_USED_TO_DEVELOP_THE_ENGINE == YES or INCOMPLETE_PACKAGE"},
        {"N": 2, "STEP": "TRUTH_PACK_BUILT_BY_HAND_FROM_ORIGINAL_DRAWINGS", "MODULE": "pa08.truth_pack.validate", "OUTPUT": "TRUTH_PACK.json (author: the verifier, never the engine)", "STOP_IF": "validation errors or fewer than six cases"},
        {"N": 3, "STEP": "TRUTH_SEAL", "MODULE": "pa08.truth_pack.seal", "OUTPUT": "PA08_TRUTH_SEAL.json (sha256 before the run)"},
        {"N": 4, "STEP": "BLIND_PRODUCTION_RUN", "MODULE": "pa08.blind_run.launch", "OUTPUT": "blind/*.json + BLIND_ACCESS_LOG.json", "STOP_IF": "any forbidden read -> VALIDATION_INVALID"},
        {"N": 5, "STEP": "FREEZE_OUTPUT_BEFORE_TRUTH", "MODULE": "pa08.blind_run.freeze_output", "OUTPUT": "FREEZE_PA08_BLIND.json"},
        {"N": 6, "STEP": "COMPARE", "MODULE": "pa08.compare.compare", "OUTPUT": "PA08_INDEPENDENT_VALIDATION_RESULT.json", "RULE": "first reader of the sealed truth; tolerances frozen; never edited after results"},
        {"N": 7, "STEP": "GATE_V4", "MODULE": "pa08.gate_v4.evaluate", "OUTPUT": "PA08_PROJECT_3_GATE_V4.json"},
        {"N": 8, "STEP": "P7757_REGRESSION_DELTA", "RULE": "P7757 is rerun only after a generic architecture change; report the delta, never tune to it"},
    ],
    "MINIMUM_SOURCE_PACKAGE": SA.MINIMUM, "TOLERANCES": C8.TOLERANCES, "COMPARISON_CLASSES": C8.COMPARISON_CLASSES,
    "REQUIRED_CASE_KINDS": C8.REQUIRED_CASE_KINDS, "OPTIONAL_CASE_KINDS": C8.OPTIONAL_CASE_KINDS,
    "OWNER_CONVENTION_QUESTIONS": "not asked yet: the independent villa decides whether the three-parallel-wall-lines convention is P7757-specific (PROJECT_RULE) or generic (proposed Urban / CAD rule for owner approval, never auto-promoted)",
    "OUTCOME_EVEN_IF_READY": "DRAFT BOQ + HUMAN REVIEW only",
}

SOURCE_ACCEPTANCE_SCHEMA = {
    "ARTIFACT": "PA08_SOURCE_ACCEPTANCE_SCHEMA", "VERSION": "PA08-SA-1",
    "RECORD_FIELDS": ["PROJECT_ALIAS", "SOURCE_FILES", "SOURCE_HASHES", "FILES[].DWG_VERSION | DXF_VERSION", "PDF_PAGE_COUNT", "VECTOR_OR_RASTER", "TEXT_AVAILABILITY", "UNIT_STATUS", "KNOWN_PRIOR_EXPOSURE",
                      "HAS_THIS_PROJECT_BEEN_USED_TO_DEVELOP_THE_ENGINE", "INDEPENDENT_VALIDATION_STATUS", "MINIMUM_PACKAGE_MET", "DECODABLE_ARCHITECTURAL_SOURCE"],
    "MINIMUM_PACKAGE": SA.MINIMUM, "EXPOSURE_REGISTRY": {k: {"ROLE": v["ROLE"], "PATHS": v["PATHS"]} for k, v in C8.DEVELOPMENT_PROJECTS.items()}, "EXPOSURE_ALIASES": list(C8.DEVELOPMENT_ALIASES),
    "DECISION": {"YES": "REJECTED_NOT_INDEPENDENT (regression use still allowed)", "NO + minimum met + decodable": "ACCEPTED", "NO + missing PDF / DWG decode": "INCOMPLETE_PACKAGE"},
    "SPREADSHEETS": "refused: never part of a validation package", "DWG_DECODER": "none in this environment: a DXF or a LibreDWG JSON decode of the same DWG is required",
}

COMPARISON_SCHEMA = {
    "ARTIFACT": "PA08_COMPARISON_SCHEMA", "VERSION": "PA08-CS-1", "CLASSES": C8.COMPARISON_CLASSES,
    "CLASS_MEANING": {"EXACT_MATCH": "engine fact equals truth (or a non-material segment correctly not accepted)", "WITHIN_TOLERANCE": "within the frozen tolerance", "ROLE_MISMATCH": "the engine's role differs from the verified role",
                      "GEOMETRY_MISMATCH": "an accepted band exists but its developed length lies outside tolerance", "OPENING_MISMATCH": "opening position / width outside 10 mm", "SPACE_TOPOLOGY_MISMATCH": "space count differs (merged or split)",
                      "MISSING_DETECTION": "a verified material fact has no accepted and no unresolved band", "FALSE_POSITIVE": "the engine accepted material where the verifier sees none",
                      "HUMAN_REVIEW_SAFE": "the engine refused (UNRESOLVED / HUMAN_REVIEW): a safe failure, not automation", "NOT_COMPARABLE": "the truth fact cannot be located in the engine's registers"},
    "FACTS_COMPARED": ["WALL_SEGMENT", "CURVED_SEGMENT", "OPENING", "PHYSICAL_SPACE_COUNT", "COLUMN"],
    "METRICS": ["VERIFIED_PHYSICAL_WALL_LENGTH_RECOVERED_MM", "VERIFIED_PHYSICAL_WALL_LENGTH_MISSED_MM", "FALSE_WALL_LENGTH_ACCEPTED_MM", "VERIFIED_OPENING_COUNT", "MISSED_OPENING_COUNT", "FALSE_OPENING_COUNT",
                "PHYSICAL_SPACES_CORRECT", "SPACES_FALSELY_MERGED", "SPACES_FALSELY_SPLIT", "CURVED_DEVELOPED_LENGTH_ERROR_MAX_REL", "COLUMN_EXPOSED_FACES_CORRECT", "QUANTITY_LINES_SAFELY_EMITTED",
                "QUANTITY_LINES_SAFELY_WITHHELD", "SILENT_WRONG_QUANTITY_COUNT"],
    "SILENT_WRONG_QUANTITY": "a bridge-allowed quantity line whose space lies in a case with any ROLE / GEOMETRY / OPENING / SPACE_TOPOLOGY mismatch, MISSING_DETECTION or FALSE_POSITIVE; must be 0",
    "TOLERANCES": C8.TOLERANCES, "FROZEN_BEFORE_ANY_RESULT": True,
}


def project_rule_candidates():
    return {"ARTIFACT": "PROJECT_RULE_CANDIDATES", "STATUS": "DEFERRED_TO_INDEPENDENT_VILLA",
            "CANDIDATES": [{"ID": "PRC-01", "CONVENTION": "three parallel wall lines (a wall drawn with a third line: finish line, skirting line or a second leaf)",
                            "OBSERVED_IN": "P7757 only", "CLASSIFICATION": "UNDETERMINED", "ENGINE_TODAY": "PA07R1 leaves such bands UNRESOLVED (FACE_SIDE_CONFLICT / ENCLOSES_PARALLEL_FACES): no quantity, HUMAN_REVIEW",
                            "DECISION_RULE": "if the independent villa shows the same convention -> propose a generic Urban / CAD rule for owner approval (never auto-promoted); if not -> PROJECT_RULE for P7757 only",
                            "OWNER_QUESTION_ASKED": False, "WHY_NOT_YET": "the owner is not asked until the second villa shows whether the convention is general"}]}


def second_source_required():
    rec = V7.second_source_required()
    rec["PA08_STATUS"] = "STILL_ACTIVE"
    rec["PA08_PACKAGE_PREPARED"] = ["PA08_VALIDATION_PROTOCOL.json", "PA08_SOURCE_ACCEPTANCE_SCHEMA.json", "PA08_TRUTH_PACK_SCHEMA.json", "PA08_BLIND_RUN_POLICY.json", "PA08_COMPARISON_SCHEMA.json",
                                    "PA08_PROJECT_3_GATE_V4.json", "PA08_RUNNER_READY_CHECK.json"]
    rec["ENTRY_POINT_WHEN_A_SOURCE_ARRIVES"] = "python -m research.qs_wall_treatment_01.pa08.run --alias <ALIAS> --arch <decode.json|.dxf> --pdf <arch.pdf> [--struct <file>] --truth <TRUTH_PACK.json>"
    rec["MINIMUM_PACKAGE"] = SA.MINIMUM
    rec["INDEPENDENT_VALIDATION"] = "DEFERRED: no independent villa exists in the repository or the uploads; not requested again here"
    return rec


def write_all(out_dir=None, gate=None):
    out = Path(out_dir or C8.OUT8)
    out.mkdir(parents=True, exist_ok=True)
    if gate is None:
        rp = C8.OUT / "pa07r1" / "PA07R1_COLD_REVIEW.json"
        review = json.loads(rp.read_text("utf-8")) if rp.exists() else None
        gate = dict(G4.evaluate(review=review), NOTE="evaluated with the annotated PA07R1 cold review and no validation input: every validation condition NOT_TESTED")
    files = {"PA08_VALIDATION_PROTOCOL.json": PROTOCOL, "PA08_SOURCE_ACCEPTANCE_SCHEMA.json": SOURCE_ACCEPTANCE_SCHEMA, "PA08_TRUTH_PACK_SCHEMA.json": TP.SCHEMA,
             "PA08_BLIND_RUN_POLICY.json": BR.POLICY, "PA08_COMPARISON_SCHEMA.json": COMPARISON_SCHEMA,
             "PA08_PROJECT_3_GATE_V4.json": gate if gate is not None else dict(G4.evaluate(), NOTE="evaluated with no validation input: every validation condition NOT_TESTED"),
             "SECOND_REGRESSION_SOURCE_REQUIRED.json": second_source_required(), "PROJECT_RULE_CANDIDATES.json": project_rule_candidates()}
    written = {}
    for name, obj in files.items():
        p = out / name
        p.write_text(json.dumps(obj, indent=1, ensure_ascii=False, default=str), "utf-8")
        written[name] = str(p)
    return written
