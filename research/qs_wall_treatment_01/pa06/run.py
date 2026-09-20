"""PA06 runner: supervised P7757 pipeline with freeze barriers, the required registers, queues, ledger, status
migration report, metrics; then the blind gate v2 (reference freeze -> blind run -> comparison), the entry gate
v2 (review-dependent conditions evaluated again by report.py once the cold review exists).

    python3 -m research.qs_wall_treatment_01.pa06.run
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

from engine import benchmark_protection as BP
from engine.ingest import ENGINE_VERSION, gates as G, gates_v2 as G2, harness as H, pipeline as PL, states as STS
from research.qs_wall_treatment_01.pa06 import blind_v2 as BV, config as C6

OUT6 = C6.OUT6
REQUIRED = ["PA06_SOURCE_UNIT_REGISTER", "PA06_PRIMITIVE_ROLE_REGISTER", "PA06_MATERIAL_GEOMETRY_REGISTER", "PA06_TOPOLOGICAL_SITE_REGISTER", "PA06_PHYSICAL_SPACE_REGISTER",
            "PA06_SPACE_BOUNDARY_FACE_REGISTER", "PA06_SPACE_WALL_LENGTH_REGISTER", "PA06_STOREY_REGISTER", "PA06_VIEW_COPY_FAMILY_REGISTER", "PA06_SHEET_ROLE_REGISTER",
            "PA06_SEMANTIC_ANCHOR_REGISTER", "PA06_ASSEMBLY_OBJECT_REGISTER", "PA06_STRUCTURAL_OBJECT_REGISTER", "PA06_TRADE_MEASUREMENT_REGION_REGISTER", "PA06_QUANTITY_INPUT_TRACE"]
ENGINE_FILES = sorted(str(p) for p in Path("engine/ingest").glob("*.py"))


def write(name, obj):
    OUT6.mkdir(parents=True, exist_ok=True)
    (OUT6 / f"{name}.json").write_text(json.dumps(obj, indent=1, default=H._json_default), "utf-8")


def run_tests():
    proc = subprocess.run([sys.executable, "-m", "pytest", "tests/test_pa06_topology.py", "tests/test_pa06_pipeline.py", "tests/test_pa05_ingest.py", "-q", "-rA", "-p", "no:cacheprovider"], capture_output=True, text=True, timeout=2400)
    res = {}
    for line in proc.stdout.splitlines():
        m = re.match(r"^(PASSED|FAILED|ERROR|SKIPPED) tests/\w+\.py::(\w+)", line)
        if m:
            res[m.group(2)] = m.group(1) == "PASSED"
    return res, proc.returncode


def status_migration():
    """Tokens still living in the older modules, each with its boundary adapter; no module rewritten."""
    from engine import height_parameters as HPm, self_checks as SCm, quantity_state as QSm
    from research.a21_trace_sufficiency_01 import parameters as A21
    return STS.migration_report({"engine/self_checks.py": ("self_checks", list(SCm.VALID_STATES)), "engine/height_parameters.py": ("height_parameters", list(HPm.STATUSES)),
                                 "research/a21_trace_sufficiency_01/parameters.py": ("a21_provenance", list(A21.PROVENANCE_RANK)), "engine/quantity_state.py": ("quantity_state", list(QSm.STATES))})


def queues(run):
    R = run.registers
    owner, source = [], []
    sem = R["PA06_SEMANTIC_ANCHOR_REGISTER"]
    undec = sem["COUNTS"]["BY_TEXT_ROLE"].get("UNDECODABLE_TEXT", 0)
    if undec:
        owner.append({"DECISION_ID": "PA06-OD-01", "QUESTION": f"{undec} room stamps are undecodable (SHX / Arabic rendering): confirm room names per cell or supply a sheet index", "BLOCKS": "identity-dependent heights (normal internal plaster area)", "STATUS": "OPEN", "CARRIED_AS": "UNRESOLVED identity"})
    st = R["PA06_STOREY_REGISTER"]["ROWS"]
    if any(not r["STOREY_NAME"] for r in st):
        owner.append({"DECISION_ID": "PA06-OD-02", "QUESTION": "storey names for the plan copies (no floor-label text in the model space): confirm GROUND / FIRST / ROOF per copy", "BLOCKS": "external plaster storey heights", "STATUS": "OPEN", "CARRIED_AS": "FLOOR_UNORDERED"})
    for r in R["PA06_QUANTITY_INPUT_TRACE"]["LINES"]:
        if r["QUANTITY_STATUS"] == "SOURCE_REQUIRED":
            source.append({"REQUEST_ID": f"PA06-SR-{len(source) + 1:02d}", "LINE_ID": r["LINE_ID"], "NEED": "source unit / geometry authority", "STATUS": "OPEN"})
    for k in R["SOURCE_INVENTORY"]["MISSING"]:
        source.append({"REQUEST_ID": f"PA06-SR-{len(source) + 1:02d}", "SOURCE_KIND": k, "BLOCKED_QUESTIONS": R["SOURCE_INVENTORY"]["BLOCKED_QUESTIONS"].get(k), "STATUS": "OPEN"})
    unres = R["PA06_TOPOLOGICAL_SITE_REGISTER"]["SUMMARY"].get("UNRESOLVED_SITE", 0)
    if unres:
        owner.append({"DECISION_ID": "PA06-OD-03", "QUESTION": f"{unres} unresolved opening sites (jamb pair, no leaf / frame / glazing): door, passage or window per site", "BLOCKS": "trade closures at those sites", "STATUS": "OPEN", "CARRIED_AS": "UNRESOLVED_GAP (never closed by a measurement basis)"})
    owner.append({"DECISION_ID": "PA06-OD-04", "QUESTION": "height scopes for RECEPTION / SALOON / stair well / double-height zones and TARTUSHA height", "BLOCKS": "areas for those cells", "STATUS": "OPEN (carried from PA04 queue; not re-asked)", "CARRIED_AS": "NOT_ESTABLISHED height"})
    return ({"ARTIFACT": "PA06_OWNER_DECISION_QUEUE", "QUEUE": owner, "D3_NOT_RE_ASKED": True, "PRICING": False},
            {"ARTIFACT": "PA06_SOURCE_REQUEST_QUEUE", "QUEUE": source})


def main():
    t0 = time.perf_counter()
    if OUT6.exists():
        shutil.rmtree(OUT6)
    run = PL.run(C6.supervised(), out_dir=str(OUT6 / "supervised"))
    R = run.registers
    for name in REQUIRED:
        write(name, R[name])
    write("PA06_STATUS_MIGRATION_REPORT", status_migration())
    oq, sq = queues(run); write("PA06_OWNER_DECISION_QUEUE", oq); write("PA06_SOURCE_REQUEST_QUEUE", sq)
    write("PA06_REVISION_SUPERSESSION_LEDGER", {"ARTIFACT": "PA06_REVISION_SUPERSESSION_LEDGER", "FORWARD_ONLY": True, "ENTRIES": [
        {"SUPERSEDED": "pa05/harness/OPENING_SITE_REGISTER (collinear-gap sites, all closed before flood)", "BY": "PA06_TOPOLOGICAL_SITE_REGISTER (host-wall context, physical separators only)", "REASON": "FM-P5-01"},
        {"SUPERSEDED": "pa05/harness/PHYSICAL_SPACE_REGISTER WALL_BOUNDARY_LM (raster runs)", "BY": "PA06_SPACE_WALL_LENGTH_REGISTER (vector faces)", "REASON": "FM-P5-02"},
        {"SUPERSEDED": "pa05/harness/ATOMIC_FACE_REGISTER as material", "BY": "PA06_MATERIAL_GEOMETRY_REGISTER (role-filtered)", "REASON": "FM-P5-03"},
        {"SUPERSEDED": "PA05 config VIEW_ASSIGNMENTS / LAYER_OVERRIDES", "BY": "PA06_STOREY_REGISTER + layer-table linetypes", "REASON": "FM-P5-05 / FM-P5-11"},
        {"SUPERSEDED": "PA05 blind gate (4 must-agree topics)", "BY": "PA06 blind gate v2 (A-M predeclared tolerances)", "REASON": "FM-P5-14"}], "FROZEN_ARTIFACTS_REWRITTEN": False})
    tests, rc = run_tests(); write("PA06_TEST_RESULTS", {"ARTIFACT": "PA06_TEST_RESULTS", "RESULTS": tests, "RETURN_CODE": rc, "COUNTS": dict(Counter("PASS" if v else "FAIL" for v in tests.values()))})
    scan = {"CLEAN": True, "HITS": {}}
    for name in REQUIRED:
        found = BP.scan(json.loads(json.dumps(R[name], default=H._json_default)))
        if found:
            scan["CLEAN"] = False; scan["HITS"][name] = found[:10]
    write("PA06_BENCHMARK_LEAKAGE_SCAN", {"ARTIFACT": "PA06_BENCHMARK_LEAKAGE_SCAN", **scan, "ENGINE_CONSTANT_HITS": G.scan_engine(ENGINE_FILES)})
    # blind gate v2: freeze the reference first, then the blind run, then compare
    ref_freeze = BV.freeze_reference(OUT6 / "supervised"); write("FREEZE_PA06_REFERENCE", ref_freeze)
    write("PA06_BLIND_PROTOCOL", BV.PROTOCOL)
    blind = BV.launch(extra_files=[C6.C5.ST_PDF]); write("PA06_BLIND_RESULT", blind)
    comparison = None
    if blind["STATUS"] == "COMPLETED":
        comparison = BV.compare(BV.BLIND_DIR / "pipeline", OUT6 / "supervised", ref_freeze); write("PA06_BLIND_COMPARISON", comparison)
    gate = G2.evaluate(registers=R, blind_comparison=comparison, review=None, benchmark_scan=scan, tests_pass=tests); write("PA06_PROJECT_3_ENTRY_GATE_V2", dict(gate, NOTE="review-dependent conditions are re-evaluated by report.py after the cold review"))
    # metrics (counts, not a score)
    roles = R["PA06_PRIMITIVE_ROLE_REGISTER"]["BY_ROLE"]; qa = R["PA06_QA_REPORT"]; wl = R["PA06_SPACE_WALL_LENGTH_REGISTER"]["ROWS"]; sem = R["PA06_SEMANTIC_ANCHOR_REGISTER"]
    cells = [c for c in R["PA06_PHYSICAL_SPACE_REGISTER"]["CELLS"] if c["IN_RANGE"]]
    metrics = {"ARTIFACT": "PA06_METRICS", "RAW_PRIMITIVES": R["PA06_PRIMITIVE_ROLE_REGISTER"]["COUNT"], "ROLE_FILTERED_MATERIAL_PRIMITIVES": qa["CONTAMINATION"]["MATERIAL_ENTITIES"],
               "HATCH_STROKES_REJECTED": qa["CONTAMINATION"]["HATCH_STROKES_REJECTED"], "DOOR_SWINGS_REJECTED": qa["CONTAMINATION"]["DOOR_SWINGS_REJECTED"], "ANNOTATION_GEOMETRY_REJECTED": qa["CONTAMINATION"]["ANNOTATION_REJECTED"],
               "MATERIAL_WALL_FACES": roles.get("MATERIAL_WALL_FACE", {}).get("COUNT", 0), "CURVED_MATERIAL_FACES": sum(1 for m in R["PA06_MATERIAL_GEOMETRY_REGISTER"]["ROWS"] if m["KIND"] in ("ARC", "CIRCLE")),
               "TOPOLOGICAL_SITES_BY_CLASS": R["PA06_TOPOLOGICAL_SITE_REGISTER"]["SUMMARY"], "NON_SITES_COLLINEAR_STUBS": len(R["PA06_TOPOLOGICAL_SITE_REGISTER"]["NON_SITES"]),
               "UNRESOLVED_SITES": R["PA06_TOPOLOGICAL_SITE_REGISTER"]["SUMMARY"].get("UNRESOLVED_SITE", 0), "PHYSICAL_SPACES_IN_RANGE": R["PA06_PHYSICAL_SPACE_REGISTER"]["COUNTS"]["REGIONS_IN_RANGE"],
               "TOPOLOGY_CELLS_IN_RANGE": len(cells), "OPEN_PHYSICAL_SPACES": R["PA06_PHYSICAL_SPACE_REGISTER"]["COUNTS"]["OPEN_GROUPS"], "FUNCTIONAL_ZONES": sem["COUNTS"]["ZONES"],
               "CELLS_WITH_SOURCE_IDENTITY": sum(1 for c in cells if (c.get("SEMANTIC_IDENTITY") or {}).get("STATUS") == "SINGLE"), "CELLS_WITH_OWNER_IDENTITY": 0,
               "CELLS_WITH_UNRESOLVED_IDENTITY": sum(1 for c in cells if (c.get("SEMANTIC_IDENTITY") or {}).get("STATUS") in ("NONE", "UNRESOLVED", "MULTIPLE")),
               "VECTOR_MATERIAL_WALL_M_IN_RANGE_CELLS": R["PA06_SPACE_WALL_LENGTH_REGISTER"]["TOTALS_STRUCTURE_ONLY"], "MEASUREMENT_CLOSURES": sum(len(r["SYNTHETIC_CLOSURES"]) for r in R["PA06_TRADE_MEASUREMENT_REGION_REGISTER"]["ROWS"]),
               "QUANTITY_INPUT_LINES_BY_STATE": R["PA06_QUANTITY_INPUT_TRACE"]["BY_STATUS"], "SOURCE_REQUESTS": len(sq["QUEUE"]), "OWNER_DECISIONS": len(oq["QUEUE"]),
               "BLIND_COMPARISON_FAILURES": (comparison or {}).get("FAILED"), "ARCHITECTURE_REVIEW_BLOCKERS": None, "AI_CALLS_IN_BATCH": 0, "DETERMINISTIC_RUNTIME_S": run.metrics["DETERMINISTIC_RUNTIME_S"],
               "STAGE_RUNTIMES_S": {k: v["RUNTIME_S"] for k, v in run.metrics["STAGES"].items()}, "BATCH_WALL_CLOCK_S": round(time.perf_counter() - t0, 1), "ENGINE_VERSION": ENGINE_VERSION}
    write("PA06_METRICS", metrics)
    print(json.dumps({"BLIND": blind["STATUS"], "COMPARISON_FAILED": (comparison or {}).get("FAILED"), "GATE_FAILED": gate["FAILED"], "TESTS": Counter("PASS" if v else "FAIL" for v in tests.values()), "RUNTIME": metrics["BATCH_WALL_CLOCK_S"]}, default=str))


if __name__ == "__main__":
    main()
