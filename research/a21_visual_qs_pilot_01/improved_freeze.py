"""Freeze one improved pass, by bytes, without reading a single quantity.

Each pass is frozen ALONE, before the other pass is looked at, so neither
can be adjusted in the light of the other. This module hashes files and
counts them. It never opens a result to decide anything.

    python3 -m research.a21_visual_qs_pilot_01.improved_freeze 1
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

from research.a21_visual_qs_pilot_01 import improved_preregistration as PRE
from research.a21_visual_qs_pilot_01 import improved_protocol as IP

RUN_DIR = Path("data/experiments/A21_VISUAL_QS_PILOT_01")
RAW = RUN_DIR / "improved_raw"

GROUPS = {
    "A": (["CASE-1-NORMAL-PLASTER", "CASE-2-TILE-PREP",
           "CASE-3-DOOR-AND-WINDOW"], "GROUP_A_CASES_1_3"),
    "B": (["CASE-4-STAIR", "CASE-5-EXTERNAL-FACADE",
           "CASE-6-ROOF-PARAPET"], "GROUP_B_CASES_4_6"),
}


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def freeze(pass_no: int) -> dict:
    IP.assert_baseline_intact()
    pre = PRE.verify()
    moved = [k for k, v in pre.items() if v["PRESENT"] and not v["UNCHANGED"]]
    if moved:
        raise SystemExit(f"a pre-registered input moved: {moved}")

    outs = []
    for g, (cases, promptname) in GROUPS.items():
        f = RAW / f"IMP_PASS{pass_no}_cases_{'1_3' if g == 'A' else '4_6'}.json"
        pf = RUN_DIR / "prompts_improved" / f"PASS{pass_no}_{promptname}.txt"
        outs.append({
            "OUTPUT_FILE": f.name,
            "PRESENT": f.exists(),
            "SHA256": sha(f) if f.exists() else None,
            "bytes": f.stat().st_size if f.exists() else 0,
            "CASES_COVERED": cases,
            "PROMPT_FILE": pf.name,
            "PROMPT_SHA256": sha(pf),
        })
    if not all(o["PRESENT"] for o in outs):
        raise SystemExit("a reader output is missing; nothing is frozen")

    body = {
        "EXPERIMENT_ID": IP.EXPERIMENT_ID,
        "RUN_ID": IP.RUN_ID,
        "PASS": f"PASS_{pass_no}_OF_2",
        "WHAT_THIS_FREEZE_IS": (
            "one improved pass, frozen on its own. Bytes were hashed; no "
            "quantity was read to produce this record"),
        "IMPROVED_PROTOCOL_HASH": PRE.IMPROVED_PROTOCOL_HASH,
        "IMPROVED_INPUT_MANIFEST_SHA256":
            PRE.INPUT_SHA256["IMPROVED_INPUT_MANIFEST.json"],
        "IMPROVED_PROMPT_RECORD_SHA256":
            PRE.INPUT_SHA256["IMPROVED_PROMPT_RECORD.json"],
        "THE_PACKET_AND_PROMPTS_WERE_COMMITTED_BEFORE_ANY_READER_RAN": True,
        "BASELINE_IS_UNTOUCHED": True,
        "BASELINE_A21_FREEZE_SHA256":
            "5335486d28ab3eb8869545a3f169af90769ef8d46156f48e7fe59536dbdc9434",
        "READER_OUTPUTS": outs,
        "RUNTIME_PROVENANCE": {
            "ORCHESTRATOR_MODEL_CONFIGURED": "claude-opus-5",
            "SESSION_RECORD_ALSO_CARRIES": "configured_model claude-opus-4-8",
            "THE_DISCREPANCY_IS_REPORTED_NOT_RESOLVED": True,
            "READERS": "sealed subagents, same model family",
            "HOW_MANY_AGENTS": 2,
            "WHAT_IS_NOT_KNOWN": (
                "the exact serving model for each subagent turn is not "
                "exposed to this session, so it is not claimed"),
        },
        "SOURCE_PRESENTATION_AS_RUN": {
            "rotation": "+90 CCW, verified per page before the run",
            "trim": "mechanical, by ink profile, to the drawn area",
            "reduction": "one LANCZOS pass to the runtime ceiling",
            "detail_crop": "native-pixel lossless PNG, 12 m across, "
                           "cases 1-3 only",
            "EFFECTIVE_SCALE_VS_BASELINE": PRE.EFFECTIVE_SCALE_VS_BASELINE,
            "CROSS_SHEET_NEVER_CROPPED_SELECTIVELY": True,
        },
        "CASE_6_COMPARABILITY": IP.CASE_6_CLASSIFICATION,
        "CASE_6_IS_NOT_A_ONE_VARIABLE_COMPARISON":
            IP.CASE_6_IS_NOT_A_ONE_VARIABLE_COMPARISON,
        "INDEPENDENCE": {
            "STATUS": IP.EVIDENCE_INDEPENDENCE_STATUS,
            "COMPONENTS": list(IP.INDEPENDENCE_COMPONENTS),
            "WHAT_AGREEMENT_SHOWS": IP.WHAT_AGREEMENT_SHOWS,
        },
        "NOTHING_HAS_BEEN_AVERAGED_OR_SELECTED": True,
        "NO_COMPARISON_ARTIFACT_WAS_CONSULTED_TO_WRITE_THIS": True,
    }
    out = RUN_DIR / f"IMPROVED_PASS{pass_no}_FREEZE.json"
    out.write_text(json.dumps(body, indent=2, ensure_ascii=False) + "\n",
                   encoding="utf-8")
    return {"FREEZE_FILE": out.name, "SHA256": sha(out),
            "READER_OUTPUT_SHA256": {o["OUTPUT_FILE"]: o["SHA256"]
                                     for o in outs}}


if __name__ == "__main__":
    print(json.dumps(freeze(int(sys.argv[1])), indent=2))
