"""Freeze SEMANTIC_EDGE_SCORING_01: inputs, prompts, code, outputs.

Binds every artifact of the scoring stage to its hash, including the two
things that make the result checkable rather than believable: the
reference register, which was written before A19 was opened, and the
scoring protocol, which was written before the reference was read.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from research.semantic_edge_scoring_01 import protocol as P

OUT = Path("data/experiments/SEMANTIC_EDGE_SCORING_01")
EXP = Path("data/experiments/SEMANTIC_EDGE_EXPERIMENT_01")
CODE = Path("research/semantic_edge_scoring_01")


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _tree(root: Path, skip=("__pycache__",)) -> dict:
    out = {}
    if not root.exists():
        return out
    for p in sorted(root.rglob("*")):
        if p.is_file() and not any(s in str(p) for s in skip):
            out[str(p.relative_to(root))] = _sha(p)
    return out


def _j(name):
    p = OUT / name
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def main() -> int:
    dec = _j("DECISION_REPORT.json")
    cl = _j("01_CANONICAL_FEATURE_CLUSTER_REGISTER.json")
    body = {
        "SCORING_ID": P.SCORING_ID,
        "SCORING_CLASS": P.SCORING_CLASS,
        "SCORING_PROTOCOL_HASH": P.protocol_hash(),
        "THE_EXPERIMENT_BEING_SCORED": P.EXPERIMENT_ID,
        "EXPERIMENT_FREEZE_SHA256": P.EXPERIMENT_FREEZE_SHA256,
        "THE_FROZEN_EXPERIMENT_WAS_NOT_ALTERED": True,
        "E1_4_IS_NOT_MODIFIED": True,
        "E1_4_RUN_HASH": P.E1_4_RUN_HASH,
        "NO_GEOMETRY_WAS_MODIFIED": True,
        "nothing_is_fed_back": P.NOTHING_IS_FED_BACK,
        "no_quantity_benchmark": P.NO_QUANTITY_BENCHMARK,
        "agreement_is_not_accuracy": P.AGREEMENT_IS_NOT_ACCURACY,
        "THE_ORDER_THAT_MAKES_THIS_CHECKABLE": [
            "the scoring protocol was written and hashed first",
            "the sample was canonicalised on source geometry only",
            "the reference packages were built and searched for every "
            "forbidden token before a reader saw them",
            "the reference was read cold, and read twice for the "
            "categories that could move geometry",
            "the reference register was written and hashed",
            "only then was A19 opened",
        ],
        "CANONICAL_FEATURES": cl.get("canonical_features"),
        "DECISION": {k: dec.get(k) for k in (
            "CANONICAL_FEATURES", "REFERENCE_RESOLVED_FEATURES",
            "REFERENCE_UNRESOLVED_FEATURES", "REFERENCE_CONFLICT_FEATURES",
            "REFERENCE_UNRESOLVED_RATE", "FEATURE_ASSEMBLY_ACCURACY",
            "HIGH_CONFIDENCE_FEATURE_ACCURACY",
            "MEDIUM_CONFIDENCE_FEATURE_ACCURACY", "HIGH_CONFIDENCE_WRONG",
            "ENTITY_ROLE_ACCURACY", "RELATION_AGREEMENT", "FENESTRATION",
            "CRITICAL_ERRORS_TOTAL", "CRITICAL_ERROR_COUNTS", "CHECKER",
            "COVERAGE_ANALYSIS", "READINESS", "THE_RULE_THAT_DECIDED_IT")},
        "HASHES": {
            "SCORED_EXPERIMENT_INPUTS": {
                n: _sha(EXP / n) for n in (
                    "FREEZE.json", "02_FEATURE_GROUP_REGISTER.json",
                    "03_CROP_REGISTER.json", "05_SAMPLE_REDUNDANCY.json",
                    "a19/PASS_A_FEATURE_ASSERTIONS.json",
                    "a19/PASS_A_ENTITY_ASSERTIONS.json",
                    "a19/PASS_A_RELATIONS.json",
                    "a19/PASS_B_CHALLENGE.json",
                    "optional_checker/CHECKER_COMPARISON.json")
                if (EXP / n).exists()},
            "CODE": _tree(CODE),
            "REGISTERS": {n: _sha(OUT / n) for n in (
                "00_SCORING_PROTOCOL.json",
                "01_CANONICAL_FEATURE_CLUSTER_REGISTER.json",
                "02_REFERENCE_INPUT_MANIFEST.json",
                "03_REFERENCE_LABEL_REGISTER.json",
                "04_REFERENCE_CONFLICT_REGISTER.json",
                "DECISION_REPORT.json") if (OUT / n).exists()},
            "REFERENCE_PROMPTS_AND_INPUTS": _tree(OUT / "reference_sandbox"),
            "REFERENCE_RAW_ANSWERS": _tree(OUT / "reference_raw"),
            "SCORES": _tree(OUT / "scores"),
        },
    }
    p = OUT / "FREEZE.json"
    p.write_text(json.dumps(body, indent=2, ensure_ascii=False) + "\n",
                 encoding="utf-8")
    print(json.dumps({"READINESS": dec.get("READINESS"),
                      "artifacts_hashed": sum(
                          len(v) for v in body["HASHES"].values()),
                      "FREEZE_SHA256": _sha(p)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
