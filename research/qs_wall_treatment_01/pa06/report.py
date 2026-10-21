"""PA06 report.  Before the review it writes PA06_REPORT.md and PA06_PROJECT_3_ENTRY_GATE_V2.json (frozen by
FREEZE_PA06).  After the cold review (which runs after the freeze) it writes the POST_REVIEW variants beside the
frozen artifacts and never rewrites them.

    python3 -m research.qs_wall_treatment_01.pa06.report
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from engine.ingest import gates_v2 as G2, harness as H
from research.qs_wall_treatment_01.pa06 import config as C6

OUT6 = C6.OUT6


def load(name):
    p = OUT6 / f"{name}.json"
    return json.loads(p.read_text("utf-8")) if p.exists() else None


def main():
    review = load("PA06_ARCHITECTURE_REVIEW")
    R = {n: load(n) for n in ("PA06_QA_REPORT", "PA06_SPACE_WALL_LENGTH_REGISTER", "PA06_QUANTITY_INPUT_TRACE", "PA06_SEMANTIC_ANCHOR_REGISTER", "PA06_STOREY_REGISTER", "PA06_TRADE_MEASUREMENT_REGION_REGISTER")}
    R["PA06_QA_REPORT"] = R["PA06_QA_REPORT"] or json.loads((OUT6 / "supervised" / "PA06_QA_REPORT.json").read_text("utf-8"))
    tests = load("PA06_TEST_RESULTS")["RESULTS"]
    scan = load("PA06_BENCHMARK_LEAKAGE_SCAN")
    suffix = "_POST_REVIEW" if review else ""
    gate = G2.evaluate(registers=R, blind_comparison=load("PA06_BLIND_COMPARISON"), review=review, benchmark_scan=scan, tests_pass=tests)
    (OUT6 / f"PA06_PROJECT_3_ENTRY_GATE_V2{suffix}.json").write_text(json.dumps(gate, indent=1, default=H._json_default), "utf-8")
    m = load("PA06_METRICS")
    m["ARCHITECTURE_REVIEW_BLOCKERS"] = [f["ID"] for f in (review or {}).get("FAILURE_MODES", []) if f.get("BLOCKS_PROJECT_3")]
    (OUT6 / f"PA06_METRICS{suffix}.json").write_text(json.dumps(m, indent=1, default=H._json_default), "utf-8")
    comp = load("PA06_BLIND_COMPARISON"); blind = load("PA06_BLIND_RESULT"); sites = load("PA06_TOPOLOGICAL_SITE_REGISTER")
    lines = ["# PA06 — PRODUCTION BRIDGE CHECKPOINT REPORT", "", f"**Gate v2:** {'READY' if gate['READY'] else 'NOT_READY'}; failed conditions: {gate['FAILED']}", "",
             "## Metrics (counts, not a score)", ""]
    for k in ("RAW_PRIMITIVES", "ROLE_FILTERED_MATERIAL_PRIMITIVES", "HATCH_STROKES_REJECTED", "DOOR_SWINGS_REJECTED", "ANNOTATION_GEOMETRY_REJECTED", "MATERIAL_WALL_FACES", "CURVED_MATERIAL_FACES",
              "TOPOLOGICAL_SITES_BY_CLASS", "NON_SITES_COLLINEAR_STUBS", "UNRESOLVED_SITES", "PHYSICAL_SPACES_IN_RANGE", "TOPOLOGY_CELLS_IN_RANGE", "OPEN_PHYSICAL_SPACES", "FUNCTIONAL_ZONES",
              "CELLS_WITH_SOURCE_IDENTITY", "CELLS_WITH_OWNER_IDENTITY", "CELLS_WITH_UNRESOLVED_IDENTITY", "VECTOR_MATERIAL_WALL_M_IN_RANGE_CELLS", "MEASUREMENT_CLOSURES", "QUANTITY_INPUT_LINES_BY_STATE",
              "SOURCE_REQUESTS", "OWNER_DECISIONS", "BLIND_COMPARISON_FAILURES", "ARCHITECTURE_REVIEW_BLOCKERS", "AI_CALLS_IN_BATCH", "DETERMINISTIC_RUNTIME_S", "BATCH_WALL_CLOCK_S"):
        lines.append(f"- {k}: {json.dumps(m.get(k), default=str)}")
    lines += ["", "## P7757 site regression (PA05 -> PA06)", "", "PA05: 578 sites (19 doors, 136 continuity, 250 junction, 173 unresolved), every site closed before flooding.",
              f"PA06: {json.dumps(sites['SUMMARY'])}; non-sites (collinear stubs across crossing walls): {len(sites['NON_SITES'])}. Not tuned toward any count.", "",
              "## Blind rebuild v2", "", f"Status {blind['STATUS']}; violations {blind['VIOLATIONS']}; files opened: {[f for f in blind['FILES_OPENED'] if 'BLIND_REBUILD_02' not in f]}", ""]
    if comp:
        lines += [f"Comparison PASS = {comp['PASS']} (tolerances declared before the run; never edited): " + ", ".join(f"{r['CRITERION']} {'PASS' if r['PASS'] else 'FAIL'}" for r in comp["ROWS"]), ""]
    lines += ["## Entry gate v2", ""] + [f"- {c['CONDITION']}: {'PASS' if c['PASS'] else 'FAIL'} — {json.dumps(c['EVIDENCE'], default=str)[:300]}" for c in gate["CONDITIONS"]]
    if review:
        lines += ["", "## Cold architecture review", "", review.get("OVERALL", {}).get("WOULD_A_NEW_VILLA_RUN_END_TO_END", ""), ""]
        for f in review.get("FAILURE_MODES", []):
            lines.append(f"- {f['ID']} [{f['SEVERITY']}/{f['DETECTION']}/blocks={f['BLOCKS_PROJECT_3']}] {f['FAILURE_MODE'][:220]}")
        lines += ["", "### PA05 failure modes after PA06", ""] + [f"- {x['ID']} {x['STATUS']}: {x.get('EVIDENCE', '')[:200]}" for x in review.get("PA05_FAILURE_MODES_STATUS", [])]
    (OUT6 / f"PA06_REPORT{suffix}.md").write_text("\n".join(lines) + "\n", "utf-8")
    print(json.dumps({"READY": gate["READY"], "FAILED": gate["FAILED"], "BLOCKERS": m["ARCHITECTURE_REVIEW_BLOCKERS"]}))


if __name__ == "__main__":
    main()
