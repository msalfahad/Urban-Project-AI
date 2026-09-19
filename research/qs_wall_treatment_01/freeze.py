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
    arts = {"estimate": ARTIFACTS_ESTIMATE, "a22": ARTIFACTS_A22, "final": ARTIFACTS_FINAL}[stage]
    body = {
        "PHASE_ID": P.PHASE_ID, "ARTIFACT": f"FREEZE_{stage.upper()}",
        "STAGE": stage, "GIT_HEAD_AT_FREEZE": _git_head(),
        "VERIFIED_INPUTS": P.VERIFIED_INPUTS,
        "UPSTREAM_SHA256": {u: (_sha(Path(u)) if Path(u).exists() else None) for u in UPSTREAM},
        "CODE_SHA256": {c: (_sha(Path(c)) if Path(c).exists() else None) for c in CODE},
        "ARTIFACT_SHA256": {a: (_sha(OUT / a) if (OUT / a).exists() else None) for a in arts},
        "BENCHMARK_OPENED_BEFORE_THIS_FREEZE": stage == "final",
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
