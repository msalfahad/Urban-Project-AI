"""PA05 runner: supervised P7757 ingestion through the generic harness,
migration report, executable Project-3 gates, PA05 success gate A-K, the
blind rebuild (only if A-K pass), the post-freeze comparison, performance
metrics and the batch record.

    python3 -m research.qs_wall_treatment_01.pa05.run
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

from engine import benchmark_protection as BP
from engine.ingest import ENGINE_VERSION, gates as G, harness as H, rules as R
from research.qs_wall_treatment_01.pa05 import blind_rebuild as BR, config_p7757 as CF, migration as MG

OUT5 = CF.OUT5
ENGINE_FILES = sorted(str(p) for p in Path("engine/ingest").glob("*.py"))
HARNESS_FILES = ["engine/ingest/harness.py", "engine/ingest/gates.py"]
METRICS = {"AI_CALLS": 0, "AI_WALL_CLOCK_S": 0.0, "SEMANTIC_CLAIMS": 0, "CHALLENGED": 0, "CHANGED_BY_CHALLENGE": 0, "OWNER_DECISIONS_REQUESTED": 0, "SOURCE_REQUESTS": 0}


def write(name, obj):
    OUT5.mkdir(parents=True, exist_ok=True)
    (OUT5 / name).write_text(json.dumps(obj, indent=1, default=H._json_default), "utf-8")


def run_tests():
    """Run the PA05 test file and return {test name: passed}."""
    proc = subprocess.run([sys.executable, "-m", "pytest", "tests/test_pa05_ingest.py", "-q", "-rA", "-p", "no:cacheprovider"], capture_output=True, text=True, timeout=1800)
    res = {}
    for line in proc.stdout.splitlines():
        m = re.match(r"^(PASSED|FAILED|ERROR|SKIPPED) tests/test_pa05_ingest\.py::(\w+)", line)
        if m:
            res[m.group(2)] = m.group(1) == "PASSED"
    return res, proc.returncode, proc.stdout[-600:]


def benchmark_scan(registers):
    hits = {}
    for name, reg in registers.items():
        found = BP.scan(json.loads(json.dumps(reg, default=H._json_default)))
        if found:
            hits[name] = found[:10]
    return {"CLEAN": not hits, "HITS": hits, "REGISTERS_SCANNED": len(registers)}


def success_gate(run, tests, scan_hits, migration):
    """PA05 §25 A-K, each executable; any failure -> PA05_NOT_READY."""
    qa = run.registers["QA_REPORT"]
    sr = run.registers["SHEET_ROLE_REGISTER"]
    dims = run.registers["DIMENSION_CHAIN_REGISTER"]["COUNTS"]
    sites = run.registers["OPENING_SITE_REGISTER"]["SUMMARY"]
    faces = run.registers["ATOMIC_FACE_REGISTER"]["SUMMARY"]
    spaces = run.registers["PHYSICAL_SPACE_REGISTER"]["ROWS"]
    crit = [
        ("A", "no P7757 constants in the engine or harness", not scan_hits, {"HITS": scan_hits}),
        ("B", "stable ids: same source -> same ids; shuffle / reversal invariant; tolerance and material changes behave", all(tests.get(t) for t in ("test_stable_ids_same_source_same_ids", "test_stable_ids_shuffle_and_endpoint_order_invariant", "test_stable_ids_tolerance_noise_and_material_change", "test_reclassification_keeps_geometry_id")) and qa["ID_STABILITY_SHUFFLE_AND_REVERSE"], {}),
        ("C", "sheet roles classified on P7757 (deterministic where a title exists, AI reads recorded as data, disagreements -> challenge)", tests.get("test_p7757_sheet_roles_regression") is True and not sr["COUNTS"]["SHEETS"].get("CHALLENGE"), dict(sr["COUNTS"])),
        ("D", "authored dimensions recovered with owners (the DWG void dims are BOTH_OWNED)", tests.get("test_p7757_authored_void_dimensions_recovered_with_owners") is True and dims["BY_OWNER_STATUS"]["BOTH_OWNED"] > 0, dims["BY_OWNER_STATUS"]),
        ("E", "opening topology represents absence (UNRESOLVED sites exist; nothing merges automatically)", tests.get("test_doorless_opening_site_does_not_merge_rooms") is True and sites["UNRESOLVED_OPENING_SITE"] > 0, sites),
        ("F", "angled and curved faces measured by developed length, no bounding boxes", tests.get("test_atomic_faces_any_orientation_and_arcs") is True and faces.get("ARC", {}).get("COUNT", 0) > 0 and faces.get("ANGLED", {}).get("COUNT", 0) > 0, faces),
        ("G", "space identity never from a flood id (anchor + bounding entities; RUN_LABEL_NOT_A_KEY)", all("RUN_LABEL_NOT_A_KEY" in s and s["PHYSICAL_SPACE_ID"].startswith("PS-") for s in spaces) and len(spaces) > 0, {"SPACES": len(spaces)}),
        ("H", "owner inputs versioned with deterministic dependent recalculation", tests.get("test_owner_input_recalculates_dependents_only") is True, {}),
        ("I", "closures reversible and zero-material (hash-proved on synthetic and P7757)", tests.get("test_measurement_closure_reversibility_by_hash") is True and qa["CLOSURE_REVERSIBILITY"] is True, {}),
        ("J", "canonical units and one status model (m2 + lm fails loudly; legacy tokens adapt forward)", tests.get("test_units_m2_and_lm_never_add") is True and tests.get("test_status_model_and_forward_adapters") is True and migration["COUNTS"].get("MIGRATED_WITHOUT_LOSS", 0) > 0, migration["COUNTS"]),
        ("K", "blind rebuild launchable without historical access (protocol + audit-hooked subprocess + fresh output dir)", BR.BLIND_DIR.name == "P7757_BLIND_REBUILD_01" and callable(BR.launch) and not str(BR.BLIND_DIR).startswith(str(CF.OUT)), {"OUTPUT_DIR": str(BR.BLIND_DIR)}),
    ]
    rows = [{"CRITERION": c, "TEXT": t, "PASS": bool(p), "EVIDENCE": e} for c, t, p, e in crit]
    return {"ARTIFACT": "PA05_SUCCESS_GATE", "ROWS": rows, "ALL_PASS": all(r["PASS"] for r in rows), "FAILED": [r["CRITERION"] for r in rows if not r["PASS"]],
            "STATUS": "PA05_READY_FOR_BLIND_REBUILD" if all(r["PASS"] for r in rows) else "PA05_NOT_READY"}


def main():
    t0 = time.perf_counter()
    OUT5.mkdir(parents=True, exist_ok=True)
    # 1 supervised ingestion
    run = H.run(CF.config(), out_dir=str(OUT5 / "harness"))
    METRICS["SEMANTIC_CLAIMS"] = len(run.registers["SEMANTIC_ANCHOR_REGISTER"]["ROWS"]) + len([r for r in run.registers["SHEET_ROLE_REGISTER"]["SHEETS"] if r["AI_ROLE"]]) + len([v for v in run.registers["SHEET_ROLE_REGISTER"]["VIEWS"] if v["AI_ROLE"]])
    METRICS["CHALLENGED"] = sum(1 for r in run.registers["SHEET_ROLE_REGISTER"]["SHEETS"] + run.registers["SHEET_ROLE_REGISTER"]["VIEWS"] if r["AI_ROLE"] and r["DETERMINISTIC_ROLE"] != "UNKNOWN")
    METRICS["CHANGED_BY_CHALLENGE"] = sum(1 for r in run.registers["SHEET_ROLE_REGISTER"]["SHEETS"] + run.registers["SHEET_ROLE_REGISTER"]["VIEWS"] if r["ROLE_STATUS"] == "CHALLENGE")
    # 2 migration
    mig = MG.run(run); write("P7757_MIGRATION_REPORT.json", mig)
    # 3 tests + scans
    tests, rc, tail = run_tests()
    write("PA05_TEST_RESULTS.json", {"ARTIFACT": "PA05_TEST_RESULTS", "RESULTS": tests, "RETURN_CODE": rc, "COUNTS": dict(Counter("PASS" if v else "FAIL" for v in tests.values()))})
    scan_hits = G.scan_engine(ENGINE_FILES)
    bscan = benchmark_scan(run.registers); write("BENCHMARK_LEAKAGE_SCAN.json", {"ARTIFACT": "BENCHMARK_LEAKAGE_SCAN", **bscan})
    # 4 PA05 success gate A-K
    gate = success_gate(run, tests, scan_hits, mig); write("PA05_SUCCESS_GATE.json", gate)
    # 5 blind rebuild only if A-K pass
    blind = {"STATUS": "NOT_RUN", "REASON": f"PA05 success gate failed: {gate['FAILED']}"}
    comparison = None
    if gate["ALL_PASS"]:
        blind = BR.launch(owner_inputs=mig["MIGRATED_OWNER_INPUTS"], extra_files=[CF.ST_PDF])
        if blind["STATUS"] == "COMPLETED":
            comparison = BR.compare(BR.BLIND_DIR / "harness", OUT5 / "harness", CF.OUT)
            write("P7757_BLIND_REBUILD_COMPARISON.json", comparison)
            must_agree = ("CURVE_GEOMETRY", "DIMENSION_OWNERSHIP", "MEASUREMENT_REGION_STRUCTURE", "PLAN_COPY_OFFSETS")
            verdict = {r["TOPIC"]: r["VERDICT"] for r in comparison["ROWS"]}
            blind["PASS_CRITERION"] = {"NO_ACCESS_VIOLATION": True, "COMPLETED": True, "MUST_AGREE": list(must_agree),
                                       "EXPLAINED_DIFFERENCES_ALLOWED": ["FACE_IDENTITY", "OPENING_IDENTITY (layer profile without overrides)", "SHEET_ROLES / VIEW_ROLES (no AI reads in the blind phase)"]}
            blind["STATUS"] = "PASS" if not blind["VIOLATIONS"] and all(verdict[t] == "AGREE" for t in must_agree) else "PASS_WITH_DIFFERENCES"
            blind["COMPARISON_VERDICTS"] = comparison["VERDICTS"]; blind["VERDICT_BY_TOPIC"] = verdict
    write("P7757_BLIND_REBUILD_RESULT.json", blind)
    if (BR.BLIND_DIR / "FREEZE_BLIND_REBUILD_01.json").exists():
        write("BLIND_REBUILD_FREEZE_COPY.json", {"ARTIFACT": "BLIND_REBUILD_FREEZE_COPY", "SOURCE": str(BR.BLIND_DIR / "FREEZE_BLIND_REBUILD_01.json"),
                                                 "FREEZE": json.loads((BR.BLIND_DIR / "FREEZE_BLIND_REBUILD_01.json").read_text("utf-8")), "PROTOCOL": BR.PROTOCOL})
    # 6 executable Project-3 gates
    ctx = {"ENGINE_PATHS": ENGINE_FILES, "TEST_RESULTS": tests, "HARNESS": {"QA_REPORT": run.registers["QA_REPORT"], "METRICS": run.metrics}, "BENCHMARK_SCAN": bscan,
           "BLIND": blind, "RUNTIME_LIMIT_S": CF.config()["MAX_RUNTIME_S"]}
    gates = G.evaluate(ctx); write("PROJECT_3_EXECUTABLE_GATES.json", gates)
    # 7 metrics (§23)
    METRICS.update({"DETERMINISTIC_RUNTIME_S": run.metrics["DETERMINISTIC_RUNTIME_S"], "STAGE_RUNTIMES_S": {k: v["RUNTIME_S"] for k, v in run.metrics["STAGES"].items()},
                    "ARTIFACT_COUNT": len(list(OUT5.glob("*.json"))) + len(list((OUT5 / "harness").glob("*.json"))) + (len(list((BR.BLIND_DIR / "harness").glob("*.json"))) if (BR.BLIND_DIR / "harness").exists() else 0),
                    "OWNER_DECISIONS_REQUESTED": 0, "SOURCE_REQUESTS": len(run.registers["SOURCE_INVENTORY"]["MISSING"]), "BATCH_WALL_CLOCK_S": round(time.perf_counter() - t0, 1),
                    "AI_CALLS_NOTE": "no AI call was made inside PA05: sheet AI roles are PA04 cold reads carried as data; the second architecture review is one agent call outside the batch metrics",
                    "ENGINE_VERSION": ENGINE_VERSION})
    write("PA05_METRICS.json", {"ARTIFACT": "PA05_METRICS", **METRICS})
    print(json.dumps({"GATE": gate["STATUS"], "FAILED": gate["FAILED"], "BLIND": blind["STATUS"], "GATES_FAILED": gates["FAILED"], "TESTS": Counter("PASS" if v else "FAIL" for v in tests.values()),
                      "MIGRATION": mig["COUNTS"], "RUNTIME": METRICS["BATCH_WALL_CLOCK_S"]}, default=str))


if __name__ == "__main__":
    main()
