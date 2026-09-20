"""Freeze the phase artifacts and the code that produced them (§33, §37).

Two stages, two files, so the order of events is provable from hashes:

    FREEZE_ESTIMATE.json   before A22 runs - the estimate, the audits, the
                           registers, the UI, the parameters, the code
    FREEZE_A22.json        after A22 - adds the comparison, before any
                           benchmark is opened

    python3 -m research.qs_wall_treatment_01.freeze estimate|a22
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

from research.qs_wall_treatment_01 import protocol as P

OUT = Path(P.OUT_DIR)

CODE = [
    "engine/material_role_audit.py", "engine/dimension_owner.py",
    "engine/wall_face_set.py", "engine/wall_treatment_engine.py",
    "engine/cad_curve_register.py", "engine/qs_measurement_region.py",
    "engine/plaster_trade_engine.py", "engine/trace_to_region.py",
    "research/a21_trace_sufficiency_01/parameters.py",
    "research/qs_wall_treatment_01/protocol.py",
    "research/qs_wall_treatment_01/declarations.py",
    "research/qs_wall_treatment_01/owner_parameters.py",
    "research/qs_wall_treatment_01/faces_from_traces.py",
    "research/qs_wall_treatment_01/build_estimate.py",
    "research/qs_wall_treatment_01/run_overlap_audit.py",
    "research/qs_wall_treatment_01/run_dimension_owner.py",
    "research/qs_wall_treatment_01/run_cad_curves.py",
    "research/qs_wall_treatment_01/source_inventory.py",
    "research/qs_wall_treatment_01/review_ui.py",
    "research/qs_wall_treatment_01/a22_structural_comparison.py",
    "research/qs_wall_treatment_01/freeze.py",
    "research/qs_wall_treatment_01/benchmark_survey.py",
    "research/qs_wall_treatment_01/benchmark_reconciliation.py",
    "research/qs_wall_treatment_01/review_package.py",
    "engine/quantity_layers.py", "engine/contractor_measurement.py",
    "engine/cad_trace_registration.py",
    "research/qs_wall_treatment_01/cad_links.py",
    "research/qs_wall_treatment_01/dual_basis.py",
    "research/qs_wall_treatment_01/decision_cards.py",
    "research/qs_wall_treatment_01/a22_dual_basis.py",
    "research/qs_wall_treatment_01/owner_review_v2.py",
    "engine/dimension_roles.py",
    "research/qs_wall_treatment_01/owner_plan_verification.py",
    "research/qs_wall_treatment_01/owner_review_v3.py",
    "research/qs_wall_treatment_01/se_elevation_source_audit.py",
    "research/qs_wall_treatment_01/owner_review_v4.py",
    "engine/quantity_state.py", "engine/parapet_assembly.py", "engine/measurement_region_builder.py",
    "engine/opening_register.py", "engine/supersession_ledger.py", "engine/owner_decision_queue.py",
    "engine/structural_registration.py", "engine/qs_measurement_region.py",
    "research/qs_wall_treatment_01/roof_edge_cad.py", "research/qs_wall_treatment_01/structural_check.py",
    "research/qs_wall_treatment_01/parapet_assembly_p7757.py", "research/qs_wall_treatment_01/plaster_pass_v4.py",
    "research/qs_wall_treatment_01/measurement_regions_v4.py", "research/qs_wall_treatment_01/a22_v4.py",
    "research/qs_wall_treatment_01/decision_queue_v4.py", "research/qs_wall_treatment_01/visual_qa_v4.py",
    "research/qs_wall_treatment_01/owner_report_v5.py",
    "engine/level_identity.py", "engine/column_faces.py", "engine/wall_treatment_matrix.py",
    "research/qs_wall_treatment_01/pa02_levels_columns.py", "research/qs_wall_treatment_01/pa02_double_height_stair.py",
    "research/qs_wall_treatment_01/pa02_roof_edges_facade.py", "research/qs_wall_treatment_01/pa02_trades_wet_openings.py",
    "research/qs_wall_treatment_01/pa02_visual_qa.py", "research/qs_wall_treatment_01/pa02_gate.py",
    "research/qs_wall_treatment_01/owner_report_v6.py",
    "engine/source_review.py",
    "research/qs_wall_treatment_01/pa03_source_review.py", "research/qs_wall_treatment_01/pa03_visual_qa.py",
    "research/qs_wall_treatment_01/pa03_gate.py", "research/qs_wall_treatment_01/owner_report_v7.py",
    "engine/plan_regions.py", "engine/height_parameters.py", "engine/self_checks.py", "engine/cold_challenge.py",
    "research/qs_wall_treatment_01/pa04/common.py", "research/qs_wall_treatment_01/pa04/rooms.py", "research/qs_wall_treatment_01/pa04/facades.py",
    "research/qs_wall_treatment_01/pa04/roof_edges.py", "research/qs_wall_treatment_01/pa04/stairs_v3.py", "research/qs_wall_treatment_01/pa04/structural.py",
    "research/qs_wall_treatment_01/pa04/openings_v2.py", "research/qs_wall_treatment_01/pa04/heights_treatments.py", "research/qs_wall_treatment_01/pa04/challenges.py",
    "research/qs_wall_treatment_01/pa04/gate.py", "research/qs_wall_treatment_01/pa04/report_v8.py",
    "engine/ingest/__init__.py", "engine/ingest/ids.py", "engine/ingest/status.py", "engine/ingest/units.py", "engine/ingest/rules.py", "engine/ingest/owner_inputs.py",
    "engine/ingest/curves.py", "engine/ingest/sheet_roles.py", "engine/ingest/source_inventory.py", "engine/ingest/views.py", "engine/ingest/dimensions.py",
    "engine/ingest/faces.py", "engine/ingest/opening_sites.py", "engine/ingest/spaces.py", "engine/ingest/measurement_regions.py", "engine/ingest/harness.py",
    "engine/ingest/gates.py", "research/qs_wall_treatment_01/pa05/config_p7757.py", "research/qs_wall_treatment_01/pa05/migration.py",
    "research/qs_wall_treatment_01/pa05/blind_rebuild.py", "research/qs_wall_treatment_01/pa05/run.py", "tests/test_pa05_ingest.py", "tests/data/p7757_pa05_expectations.json",
    "engine/ingest/source_units.py", "engine/ingest/primitive_roles.py", "engine/ingest/assemblies.py", "engine/ingest/wall_continuity.py", "engine/ingest/spaces_v2.py",
    "engine/ingest/space_boundary.py", "engine/ingest/storeys.py", "engine/ingest/semantics.py", "engine/ingest/states.py", "engine/ingest/bridge.py", "engine/ingest/pipeline.py",
    "engine/ingest/gates_v2.py", "research/qs_wall_treatment_01/pa06/config.py", "research/qs_wall_treatment_01/pa06/blind_v2.py", "research/qs_wall_treatment_01/pa06/run.py",
    "research/qs_wall_treatment_01/pa06/report.py", "tests/test_pa06_topology.py", "tests/test_pa06_pipeline.py",
    "engine/cad_adapter.py", "engine/ingest/material_bands.py", "engine/ingest/band_topology.py", "engine/ingest/planar_faces.py", "engine/ingest/junctions.py", "engine/ingest/pipeline7.py",
    "engine/ingest/gates_v3.py", "research/qs_wall_treatment_01/pa07/config.py", "research/qs_wall_treatment_01/pa07/validation.py", "research/qs_wall_treatment_01/pa07/run.py",
    "research/qs_wall_treatment_01/pa07/report.py", "tests/pa07_fixtures.py", "tests/test_pa07_bands.py", "tests/test_pa07_topology.py", "tests/test_pa07_spaces.py", "tests/test_pa07r1_guards.py",
]
ARTIFACTS_ESTIMATE = [
    "P7757_OWNER_PARAMETERS.json", "OVERLAP_AUDIT.json",
    "DIMENSION_OWNER_REGISTER.json", "CAD_CURVE_REGISTER.json",
    "SOURCE_INVENTORY.json", "TRACE_REVIEW_UI.html",
    "P7757_WALL_TREATMENT_ESTIMATE.json", "QS_TRACE.md", "SENSITIVITY.json",
]
ARTIFACTS_A22 = ARTIFACTS_ESTIMATE + ["FREEZE_ESTIMATE.json", "A22_STRUCTURAL_COMPARISON.json"]
ARTIFACTS_FINAL = ARTIFACTS_A22 + ["FREEZE_A22.json", "BENCHMARK_ACCESS_LOG.json",
                                   "BENCHMARK_RECONCILIATION.json", "OWNER_REVIEW_PACKAGE.md"]
ARTIFACTS_DUAL = ARTIFACTS_FINAL + [
    "FREEZE_FINAL.json", "CAD_TRACE_LINKS.json", "P7757_WALL_TREATMENT_ESTIMATE_v2.json",
    "QS_TRACE_v2.md", "SENSITIVITY_v2.json", "DUAL_BASIS.json", "DECISION_CARDS.json",
    "A22_DUAL_BASIS.json", "OWNER_REVIEW_V2.md"]
ARTIFACTS_OWNER_EVIDENCE = ARTIFACTS_DUAL + [
    "FREEZE_DUAL.json", "OWNER_EVIDENCE_RECONCILIATION.json",
    "P7757_WALL_TREATMENT_ESTIMATE_v3.json", "QS_TRACE_v3.md", "SENSITIVITY_v3.json",
    "DUAL_BASIS_v3.json", "A22_DUAL_BASIS_v3.json", "OWNER_REVIEW_V3.md",
    "decision_cards/S1_SALOON_DIMENSIONS.png"]
ARTIFACTS_SE_AUDIT = ARTIFACTS_OWNER_EVIDENCE + [
    "FREEZE_OWNER_EVIDENCE.json", "SE_ELEVATION_SOURCE_AUDIT.json",
    "decision_cards/D1_SE_PARAPET_SOURCE_CARD.png", "OWNER_REVIEW_V4.md"] + [
    f"decision_cards/se_native/{n}" for n in (
        "DIM-07_130.png", "DIM-08_50.png", "DIM-10_50.png", "DIM-11_50.png", "DIM-13_1440.png",
        "DIM-14_50.png", "DIM-15_420.png", "DIM-16_155.png", "DIM-17_193.png", "DIM-18_104.png",
        "DIM-19_139.png", "DIM-20_20.png", "DIM-21_680.png", "below_parapet_139_windows.png",
        "chain_104_139.png", "left_of_tower_97.png")]
ARTIFACTS_ASSEMBLY = ARTIFACTS_SE_AUDIT + [
    "FREEZE_SE_AUDIT.json", "ROOF_EDGE_PLAN_TO_ELEVATION_LINK_REGISTER.json", "STRUCTURAL_SOURCE_CHECK.json",
    "PARAPET_ASSEMBLY_REGISTER.json", "FACE_MEASUREMENT_REGISTER.json", "QS_MEASUREMENT_REGION_REGISTER.json",
    "OPENING_REGISTER_v4.json", "PLASTER_QUANTITY_TRACE.json", "P7757_WALL_TREATMENT_ESTIMATE_v4.json",
    "A22_RECONCILIATION_REGISTER.json", "OWNER_DECISION_QUEUE.json", "REVISION_SUPERSESSION_LEDGER.json",
    "SOURCE_COVERAGE.json", "BENCHMARK_LEAKAGE_GUARD.json", "VISUAL_QA.json",
    "visual_qa/SE_ELEVATION_FACES.png", "visual_qa/ROOF_PLAN_EDGES.png", "visual_qa/GF_PLAN_D2_COLUMN.png",
    "OWNER_REPORT_V5.md"]
ARTIFACTS_PA02 = ARTIFACTS_ASSEMBLY + [
    "FREEZE_ASSEMBLY.json", "D1_LEVEL_IDENTITY.json", "COLUMN_FACE_REGISTER.json", "DOUBLE_HEIGHT_AND_STAIR_REGISTERS.json",
    "ROOF_EDGES_FACADE_FINISH_KERB.json", "TRADES_WET_OPENINGS_FLOORS_COVERAGE.json", "PA02_GATE.json",
    "A22_RECONCILIATION_REGISTER_v5.json", "VISUAL_QA_PA02.json", "visual_qa/FF_VOID_STAIR.png", "visual_qa/SE_FACADE_OPENINGS.png",
    "visual_qa/NE_PARAPET_TOP.png", "visual_qa/NW_ROOF_EDGE.png", "OWNER_REPORT_V6.md"]
ARTIFACTS_PA03 = ARTIFACTS_PA02 + [
    "FREEZE_PA02.json", "VOID_GEOMETRY_RECONCILIATION.json", "RECEPTION_VERTICAL_FACE_REGISTER.json", "STAIR_COMPONENT_REGISTER_V2.json",
    "COLUMN_VERTICAL_EXPOSURE_REGISTER.json", "NE_ELEVATION_FINISH_ELIGIBILITY_REGISTER.json", "SE_OPENING_DIMENSION_OWNERSHIP_AUDIT.json",
    "PA02_SOURCE_REVIEW_SUPERSESSION_LEDGER.json", "QA_RENDER_VALIDITY_REGISTER.json", "PA03_DEPENDENT_QUANTITIES.json",
    "A22_RECONCILIATION_REGISTER_v6.json", "PA03_GATE.json", "visual_qa/FF_VOID_TWO_OBJECTS.png",
    "visual_qa/source_crops/se_tower_chain.png", "visual_qa/source_crops/se_mb_window.png", "visual_qa/source_crops/se_base_chain.png",
    "visual_qa/source_crops/ne_top_full.png", "visual_qa/source_crops/ne_top_zoomL.png", "visual_qa/source_crops/ne_top_zoomR.png",
    "OWNER_REPORT_V7.md"]
ARTIFACTS_PA04 = ARTIFACTS_PA03 + ["FREEZE_PA03.json"] + [f"pa04/{a}" for a in (
    "FF_PHYSICAL_FACE_REGISTER.json", "GF_ROOF_PHYSICAL_FACE_REGISTER.json", "WET_ROOM_REGISTER_V2.json", "CEILING_MEASUREMENT_REGION_REGISTER.json",
    "FLOOR_MEASUREMENT_REGION_REGISTER.json", "FACADE_OPENINGS_NE_NW_PRIMARY.json", "ROOF_EDGE_REGISTER_V2.json", "STAIR_GEOMETRY_V3.json",
    "STRUCTURAL_EXPOSURE_REGISTER.json", "OPENING_REGISTER_V2.json", "PROFILE_STEEL_REGISTER_V2.json", "HEIGHT_PARAMETER_TABLE.json",
    "WALL_TREATMENT_SEQUENCES_V2.json", "COLD_CHALLENGE_RECONCILIATION.json", "CHALLENGER_READINGS.json", "PA04_SELF_CHECKS.json",
    "A22_RECONCILIATION_REGISTER_v7.json", "COVERAGE_PA04.json", "OWNER_DECISION_QUEUE_V4.json", "PA04_METRICS.json", "PA04_GATE.json",
    "FABLE_RECOMMENDATIONS.json", "PROJECT_3_ENTRY_CRITERIA.json", "OWNER_REPORT_V8.md")]
ARTIFACTS_PA05 = ARTIFACTS_PA04 + ["FREEZE_PA04.json"] + [f"pa05/harness/{a}" for a in (
    "SHEET_REGISTER.json", "SHEET_ROLE_REGISTER.json", "SOURCE_INVENTORY.json", "LAYER_PROFILE.json", "VIEW_TRANSFORMS.json", "ATOMIC_FACE_REGISTER.json", "CURVE_REGISTER.json",
    "DIMENSION_CHAIN_REGISTER.json", "OPENING_SITE_REGISTER.json", "PHYSICAL_SPACE_REGISTER.json", "SEMANTIC_ANCHOR_REGISTER.json", "MEASUREMENT_REGION_REGISTER.json",
    "QA_REPORT.json", "PROJECT_INGESTION_MANIFEST.json")] + [f"pa05/{a}" for a in (
    "P7757_MIGRATION_REPORT.json", "PA05_TEST_RESULTS.json", "BENCHMARK_LEAKAGE_SCAN.json", "PA05_SUCCESS_GATE.json", "P7757_BLIND_REBUILD_RESULT.json",
    "P7757_BLIND_REBUILD_COMPARISON.json", "BLIND_REBUILD_FREEZE_COPY.json", "PROJECT_3_EXECUTABLE_GATES.json", "PA05_METRICS.json")]
ARTIFACTS_PA06 = ARTIFACTS_PA05 + ["FREEZE_PA05.json"] + [f"pa06/{a}" for a in (
    "PA06_SOURCE_UNIT_REGISTER.json", "PA06_PRIMITIVE_ROLE_REGISTER.json", "PA06_MATERIAL_GEOMETRY_REGISTER.json", "PA06_TOPOLOGICAL_SITE_REGISTER.json", "PA06_PHYSICAL_SPACE_REGISTER.json",
    "PA06_SPACE_BOUNDARY_FACE_REGISTER.json", "PA06_SPACE_WALL_LENGTH_REGISTER.json", "PA06_STOREY_REGISTER.json", "PA06_VIEW_COPY_FAMILY_REGISTER.json", "PA06_SHEET_ROLE_REGISTER.json",
    "PA06_SEMANTIC_ANCHOR_REGISTER.json", "PA06_ASSEMBLY_OBJECT_REGISTER.json", "PA06_STRUCTURAL_OBJECT_REGISTER.json", "PA06_TRADE_MEASUREMENT_REGION_REGISTER.json", "PA06_QUANTITY_INPUT_TRACE.json",
    "PA06_STATUS_MIGRATION_REPORT.json", "PA06_BLIND_PROTOCOL.json", "PA06_BLIND_RESULT.json", "PA06_BLIND_COMPARISON.json", "PA06_PROJECT_3_ENTRY_GATE_V2.json", "PA06_OWNER_DECISION_QUEUE.json",
    "PA06_SOURCE_REQUEST_QUEUE.json", "PA06_REVISION_SUPERSESSION_LEDGER.json", "PA06_METRICS.json", "PA06_TEST_RESULTS.json", "PA06_BENCHMARK_LEAKAGE_SCAN.json", "FREEZE_PA06_REFERENCE.json",
    "supervised/FREEZE_PA06_GEOMETRY.json", "supervised/FREEZE_PA06_TOPOLOGY.json", "PA06_REPORT.md")]
ARTIFACTS_PA06R1 = ARTIFACTS_PA06 + ["FREEZE_PA06.json"] + [a.replace("pa06/", "pa06r1/", 1) for a in ARTIFACTS_PA06 if a.startswith("pa06/")]
ARTIFACTS_PA06R2 = ARTIFACTS_PA06R1 + ["FREEZE_PA06R1.json"] + [a.replace("pa06/", "pa06r2/", 1) for a in ARTIFACTS_PA06 if a.startswith("pa06/")]
ARTIFACTS_PA07 = ARTIFACTS_PA06R2 + ["FREEZE_PA06R2.json"] + [f"pa07/{a}" for a in (
    "PA07_MATERIAL_BAND_REGISTER.json", "PA07_BAND_INTERVAL_REGISTER.json", "PA07_OPENING_SITE_REGISTER.json", "PA07_PLANAR_FACE_REGISTER.json", "PA07_PHYSICAL_SPACE_REGISTER.json",
    "PA07_SPACE_BOUNDARY_FACE_REGISTER.json", "PA07_COLUMN_JUNCTION_REGISTER.json", "PA07_DISPLAY_SEMANTICS_REGISTER.json", "PA07_QUANTITY_SAFETY_REGISTER.json", "PA07_TRADE_MEASUREMENT_REGION_REGISTER.json",
    "PA07_QUANTITY_INPUT_TRACE.json", "PA07_SEMANTIC_ANCHOR_REGISTER.json", "PA07_MISSING_SPACE_QA.json", "PA07_STOREY_REGISTER.json", "PA07_QA_REPORT.json", "PA07_SOURCE_AUDIT.json",
    "PA07_P7757_REGRESSION.json", "PA07_INDEPENDENT_VALIDATION_PROTOCOL.json", "SECOND_REGRESSION_SOURCE_REQUIRED.json", "PA07_OWNER_DECISION_QUEUE.json", "PA07_SOURCE_REQUEST_QUEUE.json",
    "PA07_REVISION_SUPERSESSION_LEDGER.json", "PA07_TEST_RESULTS.json", "PA07_BENCHMARK_LEAKAGE_SCAN.json", "PA07_PROJECT_3_ENTRY_GATE_V3.json", "PA07_OVERLAYS.json", "PA07_METRICS.json",
    "supervised/FREEZE7_1_SOURCE_UNITS.json", "supervised/FREEZE7_2_PRIMITIVE_ROLES.json", "supervised/FREEZE7_3_MATERIAL_BANDS.json", "supervised/FREEZE7_4_TOPOLOGICAL_SITES.json",
    "supervised/FREEZE7_5_PLANAR_FACES.json", "supervised/FREEZE7_6_SEMANTIC_ATTACHMENT.json", "supervised/FREEZE7_7_QUANTITY_BRIDGE.json", "PA07_REPORT.md")]
ARTIFACTS_PA07R1 = ARTIFACTS_PA07 + ["FREEZE_PA07.json", "pa07/PA07_ARCHITECTURE_REVIEW.json", "pa07/PA07_PROJECT_3_ENTRY_GATE_V3_POST_REVIEW.json", "pa07/PA07_REPORT_POST_REVIEW.md"] + [a.replace("pa07/", "pa07r1/", 1) for a in ARTIFACTS_PA07 if a.startswith("pa07/")] + ["pa07r1/PA07R1_GUARDS.json"]
UPSTREAM = [
    P.TRACE_REGISTER,
    "data/experiments/A21_TRACE_SUFFICIENCY_01/TRACE_PILOT_REPORT.json",
    "data/experiments/A21_TRACE_SUFFICIENCY_01/RAW_OUTPUT_FREEZE.json",
    "data/experiments/DETERMINISTIC_QS_PATH_01/P7757_DETERMINISTIC_PATH_FREEZE.json",
    "research/a21_trace_sufficiency_01/visual_trace.py",
]


def _sha(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _git_head() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"],
                                       text=True).strip()
    except Exception:
        return "UNKNOWN"


def freeze(stage: str) -> dict:
    arts = {"estimate": ARTIFACTS_ESTIMATE, "a22": ARTIFACTS_A22, "final": ARTIFACTS_FINAL,
            "dual": ARTIFACTS_DUAL, "owner_evidence": ARTIFACTS_OWNER_EVIDENCE,
            "se_audit": ARTIFACTS_SE_AUDIT, "assembly": ARTIFACTS_ASSEMBLY, "pa02": ARTIFACTS_PA02, "pa03": ARTIFACTS_PA03, "pa04": ARTIFACTS_PA04, "pa05": ARTIFACTS_PA05, "pa06": ARTIFACTS_PA06, "pa06r1": ARTIFACTS_PA06R1, "pa06r2": ARTIFACTS_PA06R2, "pa07": ARTIFACTS_PA07, "pa07r1": ARTIFACTS_PA07R1}[stage]
    body = {
        "PHASE_ID": P.PHASE_ID, "ARTIFACT": f"FREEZE_{stage.upper()}",
        "STAGE": stage, "GIT_HEAD_AT_FREEZE": _git_head(),
        "VERIFIED_INPUTS": P.VERIFIED_INPUTS,
        "UPSTREAM_SHA256": {u: (_sha(Path(u)) if Path(u).exists() else None) for u in UPSTREAM},
        "CODE_SHA256": {c: (_sha(Path(c)) if Path(c).exists() else None) for c in CODE},
        "ARTIFACT_SHA256": {a: (_sha(OUT / a) if (OUT / a).exists() else None) for a in arts},
        "BENCHMARK_OPENED_BEFORE_THIS_FREEZE": stage in ("final", "dual", "owner_evidence", "se_audit", "assembly", "pa02", "pa03", "pa04", "pa05", "pa06", "pa06r1", "pa06r2", "pa07", "pa07r1"),
        "STANDING_PROHIBITIONS": P.STANDING_PROHIBITIONS,
    }
    missing = [k for k, v in body["ARTIFACT_SHA256"].items() if v is None]
    if missing:
        raise SystemExit(f"cannot freeze {stage}: missing {missing}")
    body["FREEZE_DIGEST_SHA256"] = hashlib.sha256(json.dumps(
        {k: body[k] for k in ("UPSTREAM_SHA256", "CODE_SHA256", "ARTIFACT_SHA256")},
        sort_keys=True).encode()).hexdigest()
    p = OUT / f"FREEZE_{stage.upper()}.json"
    p.write_text(json.dumps(body, indent=2) + "\n", encoding="utf-8")
    return {"FREEZE_FILE": str(p), "FREEZE_FILE_SHA256": _sha(p),
            "FREEZE_DIGEST_SHA256": body["FREEZE_DIGEST_SHA256"]}


if __name__ == "__main__":
    print(json.dumps(freeze(sys.argv[1] if len(sys.argv) > 1 else "estimate"), indent=2))
