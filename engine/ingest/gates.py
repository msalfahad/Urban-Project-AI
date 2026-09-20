"""Executable Project-3 entry gates (PA05 §21).

Each gate is a function of a context dictionary and returns
{GATE, PASS, EVIDENCE}.  Gates read test outcomes, the engine source scan,
harness metrics and the blind-rebuild result; they never read a project's
quantities.  The constant scan patterns are generic shapes of project
leakage (entity handles, model-space coordinates, project numbers, room
vocabulary, data paths), not one project's values.
"""

from __future__ import annotations

import re
from pathlib import Path

GATES = ("NO_PROJECT_SPECIFIC_COORDINATES_IN_ENGINE", "STABLE_IDS_PASS", "SHEET_ROLE_TEST_PASS", "DIMENSION_OWNER_TEST_PASS", "CURVE_TEST_PASS",
         "OPENING_SITE_TEST_PASS", "DOORLESS_OPENING_TEST_PASS", "MEASUREMENT_CLOSURE_REVERSIBILITY_PASS", "OWNER_INPUT_RECALC_PASS", "BENCHMARK_LEAKAGE_PASS",
         "P7757_BLIND_REBUILD_PASS", "PERFORMANCE_WITHIN_LIMIT")
TEST_FOR_GATE = {"STABLE_IDS_PASS": "stable_ids", "SHEET_ROLE_TEST_PASS": "sheet_role", "DIMENSION_OWNER_TEST_PASS": "dimension_owner", "CURVE_TEST_PASS": "curve",
                 "OPENING_SITE_TEST_PASS": "opening_site", "DOORLESS_OPENING_TEST_PASS": "doorless", "MEASUREMENT_CLOSURE_REVERSIBILITY_PASS": "reversib",
                 "OWNER_INPUT_RECALC_PASS": "owner_input"}
# generic leakage shapes: a CAD entity handle token, a model-space coordinate with 5+ digits and a decimal, a project number token,
# a room-vocabulary string literal, a data / upload path literal
LEAK_PATTERNS = {
    "CAD_ENTITY_ID": re.compile(r"\bCAD-\d{2,}\b|\bLOOP-\d{2,}\b"),
    "MODEL_SPACE_COORDINATE": re.compile(r"(?<![\w.])-?\d{5,7}\.\d+(?![\w.])"),
    "PROJECT_NUMBER": re.compile(r"\b[Pp]?\d{4}_(?:ARCHITECTURAL|STRUCTURAL|DRAWINGS|SCAN)\b|\bP\d{4}\b"),
    "ROOM_NAME_LITERAL": re.compile(r"[\"'](?:RECEPTION|MAJLIS|SALOON|DINING|KITCHEN|MASTER BED\w*|BED ?ROOM|LAUNDRY|PANTRY|DIWANIYA|MAID)[\"']", re.I),
    "DATA_PATH_LITERAL": re.compile(r"[\"'](?:data/|/root/\.claude/uploads|/tmp/)[^\"']*[\"']"),
    "STOREY_OFFSET_CONSTANT": re.compile(r"\b(?:GF|FF|ROOF)2(?:GF|FF|ROOF)\b"),
}


def scan_engine(paths):
    """Scan engine source files for the generic leakage shapes; returns hits per file."""
    hits = []
    for p in paths:
        text = Path(p).read_text("utf-8")
        for i, line in enumerate(text.splitlines(), 1):
            for name, rx in LEAK_PATTERNS.items():
                m = rx.search(line)
                if m:
                    hits.append({"FILE": str(p), "LINE": i, "PATTERN": name, "MATCH": m.group(0)})
    return hits


def _test_gate(gate, ctx):
    key = TEST_FOR_GATE[gate]
    results = ctx.get("TEST_RESULTS") or {}
    rel = {n: ok for n, ok in results.items() if key in n}
    return {"GATE": gate, "PASS": bool(rel) and all(rel.values()), "EVIDENCE": {"TESTS": rel} if rel else {"TESTS": {}, "NOTE": "no test matched"}}


def evaluate(ctx):
    """ctx: ENGINE_PATHS, TEST_RESULTS {test name: bool}, HARNESS {QA_REPORT, METRICS}, BENCHMARK_SCAN {CLEAN: bool, ...}, BLIND {STATUS, ...}, RUNTIME_LIMIT_S."""
    out = []
    hits = scan_engine(ctx.get("ENGINE_PATHS") or [])
    out.append({"GATE": "NO_PROJECT_SPECIFIC_COORDINATES_IN_ENGINE", "PASS": not hits, "EVIDENCE": {"HITS": hits, "FILES_SCANNED": len(ctx.get("ENGINE_PATHS") or [])}})
    for g in TEST_FOR_GATE:
        r = _test_gate(g, ctx)
        if g == "MEASUREMENT_CLOSURE_REVERSIBILITY_PASS":
            hq = (ctx.get("HARNESS") or {}).get("QA_REPORT") or {}
            r["PASS"] = r["PASS"] and hq.get("CLOSURE_REVERSIBILITY") is True
            r["EVIDENCE"]["HARNESS_CLOSURE_REVERSIBILITY"] = hq.get("CLOSURE_REVERSIBILITY")
        out.append(r)
    bs = ctx.get("BENCHMARK_SCAN") or {}
    out.append({"GATE": "BENCHMARK_LEAKAGE_PASS", "PASS": bs.get("CLEAN") is True, "EVIDENCE": bs})
    bl = ctx.get("BLIND") or {}
    out.append({"GATE": "P7757_BLIND_REBUILD_PASS", "PASS": bl.get("STATUS") == "PASS", "EVIDENCE": bl or {"NOTE": "blind rebuild not run"}})
    m = ((ctx.get("HARNESS") or {}).get("METRICS") or {})
    limit = ctx.get("RUNTIME_LIMIT_S")
    rt = m.get("DETERMINISTIC_RUNTIME_S")
    out.append({"GATE": "PERFORMANCE_WITHIN_LIMIT", "PASS": (rt is not None and limit is not None and rt <= limit), "EVIDENCE": {"RUNTIME_S": rt, "LIMIT_S": limit}})
    assert [g["GATE"] for g in out] == list(GATES)
    return {"ARTIFACT": "PROJECT_3_EXECUTABLE_GATES", "GATES": out, "ALL_PASS": all(g["PASS"] for g in out), "FAILED": [g["GATE"] for g in out if not g["PASS"]]}
