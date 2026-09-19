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
            "se_audit": ARTIFACTS_SE_AUDIT}[stage]
    body = {
        "PHASE_ID": P.PHASE_ID, "ARTIFACT": f"FREEZE_{stage.upper()}",
        "STAGE": stage, "GIT_HEAD_AT_FREEZE": _git_head(),
        "VERIFIED_INPUTS": P.VERIFIED_INPUTS,
        "UPSTREAM_SHA256": {u: (_sha(Path(u)) if Path(u).exists() else None) for u in UPSTREAM},
        "CODE_SHA256": {c: (_sha(Path(c)) if Path(c).exists() else None) for c in CODE},
        "ARTIFACT_SHA256": {a: (_sha(OUT / a) if (OUT / a).exists() else None) for a in arts},
        "BENCHMARK_OPENED_BEFORE_THIS_FREEZE": stage in ("final", "dual", "owner_evidence", "se_audit"),
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
