"""PA07 report.  Before the cold review it writes PA07_REPORT.md and PA07_PROJECT_3_ENTRY_GATE_V3.json (frozen by
FREEZE_PA07).  After the cold review (which runs after the freeze) it writes the POST_REVIEW variants beside the
frozen artifacts and never rewrites them.

    python3 -m research.qs_wall_treatment_01.pa07.report
"""

from __future__ import annotations

import json
from pathlib import Path

from engine.ingest import gates_v3 as G3, harness as H
from research.qs_wall_treatment_01.pa07 import config as C7

OUT7 = C7.OUT7


def load(name):
    p = OUT7 / f"{name}.json"
    return json.loads(p.read_text("utf-8")) if p.exists() else None


def main():
    review = load("PA07_ARCHITECTURE_REVIEW")
    names = ("PA07_QA_REPORT", "PA07_QUANTITY_SAFETY_REGISTER", "PA07_QUANTITY_INPUT_TRACE", "PA07_OPENING_SITE_REGISTER", "PA07_MATERIAL_BAND_REGISTER", "PA07_TRADE_MEASUREMENT_REGION_REGISTER", "PA07_SOURCE_AUDIT")
    R = {n: load(n) for n in names}
    tests = load("PA07_TEST_RESULTS")["RESULTS"]; scan = load("PA07_BENCHMARK_LEAKAGE_SCAN")
    suffix = "_POST_REVIEW" if review else ""
    gate = G3.evaluate(registers=R, validation_result=load("PA07_INDEPENDENT_VALIDATION_RESULT"), review=review, benchmark_scan=scan, tests_pass=tests)
    (OUT7 / f"PA07_PROJECT_3_ENTRY_GATE_V3{suffix}.json").write_text(json.dumps(gate, indent=1, default=H._json_default), "utf-8")
    m = load("PA07_METRICS"); m["ARCHITECTURE_REVIEW_BLOCKERS"] = [f["ID"] for f in (review or {}).get("FAILURE_MODES", []) if f.get("BLOCKS_PROJECT_3")]; m["GATE_V3_FAILED"] = gate["FAILED"]
    (OUT7 / f"PA07_METRICS{suffix}.json").write_text(json.dumps(m, indent=1, default=H._json_default), "utf-8")
    reg = load("PA07_P7757_REGRESSION"); req = load("SECOND_REGRESSION_SOURCE_REQUIRED"); oq = load("PA07_OWNER_DECISION_QUEUE"); sq = load("PA07_SOURCE_REQUEST_QUEUE")
    qa = R["PA07_QA_REPORT"]; bands = R["PA07_MATERIAL_BAND_REGISTER"]["SUMMARY"]; sites = R["PA07_OPENING_SITE_REGISTER"]
    L = ["# PA07 — GEOMETRY + TOPOLOGY SAFETY CHECKPOINT REPORT", "", f"**Gate v3:** {gate['VERDICT']}; failed conditions: {gate['FAILED']}", "",
         "Every number below is a structure count with its state. No number is a quantity, no total is a BOQ figure. P7757 is the regression project, not the design target.", "",
         "## Material bands", "", f"- accepted {bands['ACCEPTED']} (straight {bands['BY_TYPE'].get('STRAIGHT_BAND', 0)}, angled {bands['BY_TYPE'].get('ANGLED_BAND', 0)}, curved {bands['BY_TYPE'].get('CURVED_BAND', 0)}, column {bands['BY_TYPE'].get('COLUMN_BAND', 0)}); of these {bands['ACCEPTED_WITH_FACE_DOUBLING']} carry an AMBIGUOUS face position (doubled line)",
         f"- rejected {bands['REJECTED']} by reason: {bands['REJECTED_BY_REASON']}", f"- unresolved {bands['UNRESOLVED']} by reason: {bands['UNRESOLVED_BY_REASON']}",
         f"- accepted developed length (all views, structure only): {bands['ACCEPTED_DEVELOPED_M']}", "",
         "## Topology", "", f"- intervals: {R['PA07_QUANTITY_SAFETY_REGISTER'] and load('PA07_BAND_INTERVAL_REGISTER')['SUMMARY']['INTERVALS']}", f"- sites by class: {sites['BY_CLASS']}", f"- sites by status: {sites['BY_STATUS']}", "",
         "## Spaces", "", f"- planar faces by eligibility: {qa['PLANAR_FACES']}", f"- spaces on plan views: {qa['SPACES_ON_PLAN_VIEWS']} ({qa['SPACES_BY_GEOMETRY_STATUS']}); identity {qa['SPACES_BY_IDENTITY']}",
         f"- MISSING_SPACE_QA: {qa['MISSING_SPACE_QA']}", f"- material boundary on plan interior spaces (structure only): {qa['MATERIAL_BOUNDARY_M_PLAN_INTERIOR_STRUCTURE_ONLY']} m; established boundaries only: {qa['MATERIAL_BOUNDARY_M_PLAN_INTERIOR_ESTABLISHED_ONLY']} m", "",
         "## Columns / beams", "", f"- {qa['COLUMNS']}", "",
         "## P7757 regression against PA06R2", "", f"- PA06R2 interior vector wall: {reg['PA06R2']['VECTOR_MATERIAL_WALL_M_INTERIOR_CELLS']} m over {reg['PA06R2']['SPACES']['CELLS_IN_RANGE']} in-range cells",
         f"- PA07: {reg['PA07']['MATERIAL_BOUNDARY_M_PLAN_INTERIOR_STRUCTURE_ONLY']} m over {reg['PA07']['INTERIOR_SPACES_ON_PLAN_VIEWS']} interior spaces on plan views", f"- {reg['INTERPRETATION']['INTERIOR_VECTOR_WALL_LENGTH']}",
         f"- {reg['INTERPRETATION']['WHY_THE_LENGTH_FELL']}", f"- {reg['INTERPRETATION']['PA05_FACE_COUNTS']}", "",
         "## Quantity safety", "", f"- bridge allowed lines: {qa['QUANTITY_SAFETY']['BRIDGE_ALLOWED']}; blocked by gate: {qa['QUANTITY_SAFETY']['BLOCKED_BY_GATE']}; lines by status: {qa['QUANTITY_SAFETY']['LINES_BY_STATUS']}", "",
         "## Independent validation", "", f"- {req['STATUS']}: {req['GATE_V3_EFFECT']}", f"- upload request: {req['UPLOAD_REQUEST']}", "",
         "## Gate v3", ""] + [f"- {c['CONDITION']}: {'PASS' if c['PASS'] else 'FAIL'}" for c in gate["CONDITIONS"]] + ["",
         "## Queues", "", f"- owner decisions: {len(oq['QUEUE'])}; source requests: {len(sq['QUEUE'])}", ""]
    if review:
        L += ["## Cold architecture review", "", f"- failure modes: {len(review.get('FAILURE_MODES', []))}; blocking: {[f['ID'] for f in review.get('FAILURE_MODES', []) if f.get('BLOCKS_PROJECT_3')]}",
              f"- PA06 modes: {review.get('PA06_FAILURE_MODES_STATUS')}", ""]
    L += ["## Answer", "", "May the architecture produce a DRAFT BOQ for an unseen villa: **NO** (no independent validation executed; the P7757 regression shows the honest failure surface: most walls unresolved without fill or end-face evidence).", ""]
    (OUT7 / f"PA07_REPORT{suffix}.md").write_text("\n".join(L), "utf-8")
    if suffix and not (OUT7 / "PA07_REPORT.md").exists():
        (OUT7 / "PA07_REPORT.md").write_text("\n".join(L), "utf-8")      # a revision run started after the review still carries the plain report the freeze lists
    print(json.dumps({"VERDICT": gate["VERDICT"], "FAILED": gate["FAILED"], "REPORT": str(OUT7 / f"PA07_REPORT{suffix}.md")}))


if __name__ == "__main__":
    main()
