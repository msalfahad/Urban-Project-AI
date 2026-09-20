"""PA07 runner: supervised P7757 pipeline with the seven serial freeze barriers, the required registers, the P7757
regression against PA06R2, queues, ledger, metrics, the independent-validation protocol (and the SOURCE_REQUIRED
record when no independent villa exists), the entry gate v3 (review-dependent conditions re-evaluated by report.py
after the cold review), visual QA overlays (never truth).

    python3 -m research.qs_wall_treatment_01.pa07.run
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import shutil
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

from engine import benchmark_protection as BP
from engine.ingest import ENGINE_VERSION, gates as G, gates_v3 as G3, harness as H, pipeline7 as P7, material_bands as MB, band_topology as BT
from research.qs_wall_treatment_01.pa07 import config as C7, validation as VAL

OUT7 = C7.OUT7
REQUIRED = ["PA07_MATERIAL_BAND_REGISTER", "PA07_BAND_INTERVAL_REGISTER", "PA07_OPENING_SITE_REGISTER", "PA07_PLANAR_FACE_REGISTER", "PA07_PHYSICAL_SPACE_REGISTER",
            "PA07_SPACE_BOUNDARY_FACE_REGISTER", "PA07_COLUMN_JUNCTION_REGISTER", "PA07_DISPLAY_SEMANTICS_REGISTER", "PA07_QUANTITY_SAFETY_REGISTER", "PA07_TRADE_MEASUREMENT_REGION_REGISTER",
            "PA07_QUANTITY_INPUT_TRACE", "PA07_SEMANTIC_ANCHOR_REGISTER", "PA07_MISSING_SPACE_QA", "PA07_STOREY_REGISTER", "PA07_QA_REPORT"]
ENGINE_FILES = sorted(str(p) for p in Path("engine/ingest").glob("*.py"))
TEST_FILES = ["tests/test_pa07_bands.py", "tests/test_pa07_topology.py", "tests/test_pa07_spaces.py", "tests/test_pa06_topology.py", "tests/test_pa06_pipeline.py", "tests/test_pa05_ingest.py"]


def write(name, obj):
    OUT7.mkdir(parents=True, exist_ok=True)
    (OUT7 / f"{name}.json").write_text(json.dumps(obj, indent=1, default=H._json_default), "utf-8")


def load6(name):
    p = C7.PA06R2 / f"{name}.json"
    if not p.exists():
        p = C7.PA06R2 / "supervised" / f"{name}.json"
    return json.loads(p.read_text("utf-8")) if p.exists() else None


def run_tests():
    proc = subprocess.run([sys.executable, "-m", "pytest", *TEST_FILES, "-q", "-rA", "-p", "no:cacheprovider"], capture_output=True, text=True, timeout=3600)
    res = {}
    for line in proc.stdout.splitlines():
        m = re.match(r"^(PASSED|FAILED|ERROR|SKIPPED) tests/\w+\.py::(\w+)", line)
        if m:
            res[m.group(2)] = m.group(1) == "PASSED"
    return res, proc.returncode


def source_audit(run):
    rows = []
    for s in run.cfg["SOURCES"]:
        p = Path(s["PATH"])
        rows.append({"PATH": s["PATH"], "KIND": s["KIND"], "EXISTS": p.exists(), "SHA256": hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None, "BYTES": p.stat().st_size if p.exists() else None})
    units = run.registers["PA06_SOURCE_UNIT_REGISTER"]["ROWS"]
    return {"ARTIFACT": "PA07_SOURCE_AUDIT", "SOURCES": rows, "UNITS": [{"SOURCE_ID": u["SOURCE_ID"], "STATUS": u["STATUS"], "UNIT": u["UNIT_CANDIDATE"]} for u in units],
            "PASS": all(r["EXISTS"] for r in rows) and all(u["ACCEPTABLE_FOR_QUANTITIES"] for u in units), "BENCHMARK_OPENED_IN_THIS_PHASE": False, "PRICING": False, "FIREBASE": False}


def regression(run):
    R = run.registers
    roles = R["PA06_PRIMITIVE_ROLE_REGISTER"]
    bands = R["PA07_MATERIAL_BAND_REGISTER"]
    sites = R["PA07_OPENING_SITE_REGISTER"]
    faces = R["PA07_PLANAR_FACE_REGISTER"]
    spaces = R["PA07_PHYSICAL_SPACE_REGISTER"]["ROWS"]
    qa = R["PA07_QA_REPORT"]
    cols = R["PA07_COLUMN_JUNCTION_REGISTER"]["SUMMARY"]
    plan = [s for s in spaces if s.get("VIEW_ROLE") in ("FLOOR_PLAN", "ROOF_PLAN")]
    old_qa = load6("PA06_QA_REPORT") or {}
    old_sites = (load6("PA06_TOPOLOGICAL_SITE_REGISTER") or {}).get("SUMMARY")
    old_spaces = (load6("PA06_PHYSICAL_SPACE_REGISTER") or {}).get("COUNTS")
    old_metrics = load6("PA06_METRICS") or {}
    old_sem = (load6("PA06_SEMANTIC_ANCHOR_REGISTER") or {}).get("COUNTS")
    pa05 = None
    p5 = C7.OUT / "pa05" / "harness" / "ATOMIC_FACE_REGISTER.json"
    if p5.exists():
        pa05 = json.loads(p5.read_text("utf-8")).get("SUMMARY")
    by_view = {}
    for v in run.views:
        vid = v["VIEW_ID"]
        b = bands["BY_VIEW"].get(vid, {})
        vs = [s for s in spaces if s["VIEW_ID"] == vid]
        by_view[vid] = {"ROLE": v["ROLE"]["FINAL_ROLE"], "ROLE_STATUS": v["ROLE"]["ROLE_STATUS"], "PRIMITIVES": len(v["PRIMITIVES"]), "BANDS": {k: b.get(k) for k in ("ACCEPTED", "REJECTED", "UNRESOLVED")},
                        "ACCEPTED_DEVELOPED_M": b.get("ACCEPTED_DEVELOPED_M"), "SITES_BY_CLASS": dict(Counter(s["CLASS"] for s in sites["ROWS"] if s["VIEW_ID"] == vid)),
                        "PLANAR_FACES_BY_ELIGIBILITY": dict(Counter(f["SPACE_ELIGIBILITY"] for f in faces["ROWS"] if f["VIEW_ID"] == vid)), "SPACES": len(vs),
                        "MATERIAL_BOUNDARY_M_STRUCTURE_ONLY": round(sum(s["MATERIAL_BOUNDARY_MM"] for s in vs) / 1000, 3),
                        "ROOM_LABELS_IN_VIEW": sum(1 for t in run._texts(v) if t["ROLE"] == "ROOM_NAME")}
    interior_m = qa["MATERIAL_BOUNDARY_M_PLAN_INTERIOR_STRUCTURE_ONLY"]
    return {"ARTIFACT": "PA07_P7757_REGRESSION", "RULE": "structure counts only; no total is a quantity; PA07 does not preserve any PA06 number",
            "PA07": {"RAW_PRIMITIVES": roles["COUNT"], "ROLE_FILTERED_CANDIDATES": sum(b.get("ACCEPTED", 0) + b.get("REJECTED", 0) + b.get("UNRESOLVED", 0) for b in bands["BY_VIEW"].values()),
                     "ACCEPTED_BANDS": bands["SUMMARY"]["ACCEPTED"], "ACCEPTED_BANDS_WITH_FACE_DOUBLING": bands["SUMMARY"]["ACCEPTED_WITH_FACE_DOUBLING"], "REJECTED_BY_REASON": bands["SUMMARY"]["REJECTED_BY_REASON"],
                     "UNRESOLVED_BY_REASON": bands["SUMMARY"]["UNRESOLVED_BY_REASON"], "ACCEPTED_DEVELOPED_M_ALL_VIEWS": bands["SUMMARY"]["ACCEPTED_DEVELOPED_M"],
                     "SITES_BY_CLASS": sites["BY_CLASS"], "SITES_BY_STATUS": sites["BY_STATUS"], "PLANAR_FACES": faces["BY_ELIGIBILITY"], "INTERIOR_SPACES_ON_PLAN_VIEWS": len(plan),
                     "SPACES_BY_GEOMETRY_STATUS": dict(Counter(s["GEOMETRY_STATUS"] for s in plan)), "OPEN_REGIONS": qa["MISSING_SPACE_QA"].get("OPEN_REGION", 0),
                     "ANCHORS_WITHOUT_SPACE": qa["MISSING_SPACE_QA"].get("ANCHOR_WITHOUT_SPACE", 0), "SPACES_WITHOUT_ANCHORS": qa["MISSING_SPACE_QA"].get("SPACE_WITHOUT_IDENTITY", 0),
                     "MERGED_MULTI_ANCHOR_SPACES": qa["MISSING_SPACE_QA"].get("MULTIPLE_ANCHORS_ONE_SPACE", 0), "POSSIBLE_MISSED_SPACES": qa["MISSING_SPACE_QA"].get("POSSIBLE_MISSED_SPACE", 0),
                     "COLUMN_JUNCTIONS": cols, "QUANTITY_ELIGIBLE_BOUNDARY_M_PLAN_INTERIOR_ESTABLISHED_ONLY": qa["MATERIAL_BOUNDARY_M_PLAN_INTERIOR_ESTABLISHED_ONLY"],
                     "MATERIAL_BOUNDARY_M_PLAN_INTERIOR_STRUCTURE_ONLY": interior_m, "BRIDGE_ALLOWED_LINES": R["PA07_QUANTITY_SAFETY_REGISTER"]["BRIDGE_ALLOWED"],
                     "BLOCKED_BY_GATE": R["PA07_QUANTITY_SAFETY_REGISTER"]["BLOCKED_BY_GATE"], "BY_VIEW": by_view},
            "PA06R2": {"VECTOR_MATERIAL_WALL_M_INTERIOR_CELLS": old_qa.get("VECTOR_MATERIAL_WALL_M_INTERIOR_CELLS"), "SITES": old_sites, "SPACES": old_spaces, "SEMANTIC": old_sem,
                       "MATERIAL_ENTITIES": old_metrics.get("ROLE_FILTERED_MATERIAL_PRIMITIVES"), "MATERIAL_WALL_FACES": old_metrics.get("MATERIAL_WALL_FACES")},
            "PA05": {"ATOMIC_FACE_SUMMARY": pa05},
            "INTERPRETATION": {
                "INTERIOR_VECTOR_WALL_LENGTH": f"PA06R2 counted {old_qa.get('VECTOR_MATERIAL_WALL_M_INTERIOR_CELLS')} m of material wall face around 22 interior cells; PA07 attributes {interior_m} m of established material boundary to {len(plan)} interior spaces on plan views. The number was not preserved and could not be: PA06 accepted any role-classified face beside a flooded cell, PA07 accepts a face only through a band that survived the pairing, enclosure, face-side, structure and evidence rules, and a space only when its boundary closes without leaking to the view border.",
                "WHY_THE_LENGTH_FELL": "most P7757 walls are drawn with a third parallel line (column-bonding strip, door-layer line, finish line) and no hatch and no end returns; the band engine cannot tell which of three parallel lines is the material face without fill or end-face evidence and leaves the strip UNRESOLVED (FACE_SIDE_CONFLICT / VOID_BESIDE_EVIDENCED_ELEMENT / ISOLATED_PAIR). A room bounded by one unresolved wall leaks to the exterior face and is not a space. This is the FAIL VISIBLY outcome, not a measurement.",
                "PA05_FACE_COUNTS": "the PA05 raw face counts (8,976 established / 11,846 total atomic faces) are meaningless under PA07: a face is not a unit of material; the unit is a band (two paired faces with evidence), and a band's developed length is the only length that exists. Counting faces double-counts every wall and counts every frame, hatch stroke and doubling line.",
                "FACE_DOUBLING": f"{bands['SUMMARY']['ACCEPTED_WITH_FACE_DOUBLING']} accepted bands carry a doubled face (a parallel line < 75 mm from a face); their face position is AMBIGUOUS and the quantity gate blocks them (MATERIAL_BANDS gate)."}}


def queues(run, val_required):
    R = run.registers
    owner, source = [], []
    bands = R["PA07_MATERIAL_BAND_REGISTER"]["SUMMARY"]
    n_conf = bands["UNRESOLVED_BY_REASON"].get("FACE_SIDE_CONFLICT", 0) + bands["UNRESOLVED_BY_REASON"].get("VOID_BESIDE_EVIDENCED_ELEMENT", 0)
    if n_conf:
        owner.append({"DECISION_ID": "PA07-OD-01", "QUESTION": f"{n_conf} wall strips have three or more parallel lines with no hatch and no end returns: which line is the wall face (column-bonding strip / door-layer line / finish line)?  A wall thickness table or a drafting convention statement resolves them all at once",
                      "BLOCKS": "band acceptance -> space closure -> every quantity on those rooms", "STATUS": "OPEN", "CARRIED_AS": "UNRESOLVED band, leaked space, no number", "CHANGES_PHYSICAL_GEOMETRY": True})
    dbl = bands["ACCEPTED_WITH_FACE_DOUBLING"]
    if dbl:
        owner.append({"DECISION_ID": "PA07-OD-02", "QUESTION": f"{dbl} accepted bands carry a doubled face line 50 mm inside the wall (S-COL.BON / D layers): is the wall face the outer or the inner line?", "BLOCKS": "face position (±50 mm on the room dimension); MATERIAL_BANDS gate", "STATUS": "OPEN", "CARRIED_AS": "FACE_POSITION_STATUS AMBIGUOUS_FACE_DOUBLING"})
    sites = R["PA07_OPENING_SITE_REGISTER"]["BY_STATUS"]
    if sites.get("INSUFFICIENT_EVIDENCE") or sites.get("PROVISIONAL") or sites.get("OPEN_PASSAGE_CANDIDATE"):
        owner.append({"DECISION_ID": "PA07-OD-03", "QUESTION": f"{sites.get('INSUFFICIENT_EVIDENCE', 0)} both-face gaps without jamb / leaf / swing / frame, {sites.get('PROVISIONAL', 0)} probable doors without leaf, {sites.get('OPEN_PASSAGE_CANDIDATE', 0)} open-passage candidates: door, window, passage or drafting break per site",
                      "BLOCKS": "OPENING_SITE_STATUS gate on the rooms beside them", "STATUS": "OPEN", "CARRIED_AS": "UNRESOLVED / PROVISIONAL site, never closed by a basis"})
    if sites.get("SINGLE_FACE_GAP"):
        source.append({"REQUEST_ID": f"PA07-SR-{len(source) + 1:02d}", "NEED": f"{sites['SINGLE_FACE_GAP']} single-face gaps: the face line stops with no crossing band (niche, recess or an omitted line); confirm against the original DWG at those bands", "STATUS": "OPEN"})
    owner.append({"DECISION_ID": "PA07-OD-04", "QUESTION": "storey names for the plan copies; height scopes for double-height / stair / exterior rooms; TARTUSHA height", "BLOCKS": "STOREY_STATUS and HEIGHT_STATUS gates", "STATUS": "OPEN (carried from PA04 / PA06 queues; not re-asked)", "CARRIED_AS": "SOURCE_REQUIRED height"})
    for k in R["SOURCE_INVENTORY"]["MISSING"]:
        source.append({"REQUEST_ID": f"PA07-SR-{len(source) + 1:02d}", "SOURCE_KIND": k, "BLOCKED_QUESTIONS": R["SOURCE_INVENTORY"]["BLOCKED_QUESTIONS"].get(k), "STATUS": "OPEN"})
    if val_required:
        source.append({"REQUEST_ID": f"PA07-SR-{len(source) + 1:02d}", "SOURCE_KIND": "SECOND_REGRESSION_VILLA", "NEED": val_required["UPLOAD_REQUEST"], "BLOCKS": "PROJECT_3_ENTRY_GATE_V3 conditions 5 and 6", "STATUS": "OPEN"})
    return ({"ARTIFACT": "PA07_OWNER_DECISION_QUEUE", "QUEUE": owner, "D3_NOT_RE_ASKED": True, "PRICING": False, "NOTE": "PA07-OD-01 would change physical geometry if answered by convention; the phase did not stop because the engine records the strips as UNRESOLVED instead of guessing"},
            {"ARTIFACT": "PA07_SOURCE_REQUEST_QUEUE", "QUEUE": source})


def overlays(run):
    """Visual QA: accepted band strips, rejected / unresolved candidates, eligible spaces.  Encouraged by the directive; never truth."""
    try:
        from PIL import Image, ImageDraw
    except Exception:
        return []
    out = []
    (OUT7 / "overlays").mkdir(parents=True, exist_ok=True)
    COL = {"ACCEPTED": (0, 170, 0), "REJECTED": (220, 0, 0), "UNRESOLVED": (255, 150, 0)}
    for v in run.views:
        bands = run.bands7.get(v["VIEW_ID"], [])
        if not bands:
            continue
        x0, y0, x1, y1 = v["BBOX_MM"]
        S = 2400 / max(x1 - x0, y1 - y0)
        img = Image.new("RGB", (int((x1 - x0) * S) + 2, int((y1 - y0) * S) + 2), "white"); d = ImageDraw.Draw(img)
        px = lambda x, y: ((x - x0) * S, (y1 - y) * S)
        grids = run.grids7.get(v["VIEW_ID"])
        if grids is not None:
            lab = grids["label"]; meta = grids["meta"]; cell = grids["cell"]
            elig = {f["RUN_LABEL_NOT_A_KEY"] for f in run.faces[v["VIEW_ID"]] if f["SPACE_ELIGIBILITY"] == "ELIGIBLE"}
            for f in run.faces[v["VIEW_ID"]]:
                if f["RUN_LABEL_NOT_A_KEY"] in elig:
                    bx0, by0, bx1, by1 = f["BBOX_MM"]
                    d.rectangle([px(bx0, by1), px(bx1, by0)], outline=(0, 120, 255), width=2)
        for p in v["PRIMITIVES"]:
            if p.kind == "SEGMENT":
                d.line([px(p.x1, p.y1), px(p.x2, p.y2)], fill=(200, 200, 200), width=1)
        for b in bands:
            c = COL[b["STATUS"]]
            for lo, hi in b["COVER"]:
                n = 30; pts = [px(*MB.band_point(b, lo + i * (hi - lo) / n)) for i in range(n + 1)]
                d.line(pts, fill=c, width=max(2, int(b["THK"] * S * 0.5)))
        path = OUT7 / "overlays" / f"{v['VIEW_ID']}_bands_faces.png"
        img.save(path); out.append({"VIEW_ID": v["VIEW_ID"], "PATH": str(path), "LEGEND": "green accepted band, red rejected, orange unresolved, blue box = eligible space bbox; NOT TRUTH"})
    return out


def main():
    t0 = time.perf_counter()
    if OUT7.exists():
        shutil.rmtree(OUT7)
    run = P7.run(C7.supervised(), out_dir=str(OUT7 / "supervised"))
    R = run.registers
    R["PA07_SOURCE_AUDIT"] = source_audit(run); write("PA07_SOURCE_AUDIT", R["PA07_SOURCE_AUDIT"])
    for name in REQUIRED:
        write(name, R[name])
    write("PA07_P7757_REGRESSION", regression(run))
    protocol, required = VAL.protocol(), VAL.second_source_required()
    write("PA07_INDEPENDENT_VALIDATION_PROTOCOL", protocol)
    write("SECOND_REGRESSION_SOURCE_REQUIRED", required)
    oq, sq = queues(run, required); write("PA07_OWNER_DECISION_QUEUE", oq); write("PA07_SOURCE_REQUEST_QUEUE", sq)
    write("PA07_REVISION_SUPERSESSION_LEDGER", {"ARTIFACT": "PA07_REVISION_SUPERSESSION_LEDGER", "FORWARD_ONLY": True, "ENTRIES": [
        {"SUPERSEDED": "PA06_MATERIAL_GEOMETRY_REGISTER (role-classified faces are material)", "BY": "PA07_MATERIAL_BAND_REGISTER (paired bands with evidence; a face is material only through an accepted band)", "REASON": "FM-P6-01"},
        {"SUPERSEDED": "PA06_TOPOLOGICAL_SITE_REGISTER (gaps between collinear faces)", "BY": "PA07_BAND_INTERVAL_REGISTER + PA07_OPENING_SITE_REGISTER (longitudinal intervals of a host band; single-face gap never a doorway; chords seal band interiors)", "REASON": "FM-P6-02"},
        {"SUPERSEDED": "PA06 chord closure of curved walls", "BY": "PA07 curved bands with developed-distance axis; openings as developed intervals", "REASON": "FM-P6-03"},
        {"SUPERSEDED": "PA06_PHYSICAL_SPACE_REGISTER (1 m seed-grid flood)", "BY": "PA07_PLANAR_FACE_REGISTER + PA07_PHYSICAL_SPACE_REGISTER (connected components of the whole free mask)", "REASON": "FM-P6-10"},
        {"SUPERSEDED": "PA06_SPACE_WALL_LENGTH_REGISTER (boundary tracing of cells)", "BY": "PA07_SPACE_BOUNDARY_FACE_REGISTER (band developed geometry cut at junctions and column footprints)", "REASON": "FM-P6-05 / FM-P6-07"},
        {"SUPERSEDED": "PA06 blind gate v2 (engine compared with itself)", "BY": "PA07_INDEPENDENT_VALIDATION_PROTOCOL (second villa or sealed hand-verification pack); not executed: SECOND_REGRESSION_SOURCE_REQUIRED", "REASON": "FM-P6-14"},
        {"SUPERSEDED": "PA06 bridge on every in-range cell", "BY": "PA07_QUANTITY_SAFETY_REGISTER: nine gates per space x trade before the existing engines run", "REASON": "FM-P6-08 / FM-P6-15"},
        {"SUPERSEDED": "PA06 HATCH_STROKE role as an exclusion", "BY": "PA07 re-examines PA06 hatch strokes longer than 300 mm (the PA06 family rule swallowed 1-3 m wall faces beside door frames); PA06 code untouched", "REASON": "new finding FM-P7-A"}],
        "FROZEN_ARTIFACTS_REWRITTEN": False})
    tests, rc = run_tests(); write("PA07_TEST_RESULTS", {"ARTIFACT": "PA07_TEST_RESULTS", "RESULTS": tests, "RETURN_CODE": rc, "COUNTS": dict(Counter("PASS" if v else "FAIL" for v in tests.values()))})
    scan = {"CLEAN": True, "HITS": {}}
    for name in REQUIRED:
        found = BP.scan(json.loads(json.dumps(R[name], default=H._json_default)))
        if found:
            scan["CLEAN"] = False; scan["HITS"][name] = found[:10]
    write("PA07_BENCHMARK_LEAKAGE_SCAN", {"ARTIFACT": "PA07_BENCHMARK_LEAKAGE_SCAN", **scan, "ENGINE_CONSTANT_HITS": G.scan_engine(ENGINE_FILES), "BENCHMARK_FILES_OPENED": []})
    gate = G3.evaluate(registers=R, validation_result=None, review=None, benchmark_scan=scan, tests_pass=tests)
    write("PA07_PROJECT_3_ENTRY_GATE_V3", dict(gate, NOTE_REVIEW="review-dependent condition 13 is re-evaluated by report.py after the cold review; conditions 5 and 6 stay failed until an independent source exists"))
    ov = overlays(run); write("PA07_OVERLAYS", {"ARTIFACT": "PA07_OVERLAYS", "FILES": ov, "TRUTH": False})
    qa = R["PA07_QA_REPORT"]; bands = R["PA07_MATERIAL_BAND_REGISTER"]["SUMMARY"]
    metrics = {"ARTIFACT": "PA07_METRICS", "OUTPUT_TAG": C7.TAG, "COUNTS_NOT_SCORES": True,
               "RAW_PRIMITIVES": R["PA06_PRIMITIVE_ROLE_REGISTER"]["COUNT"], "BAND_CANDIDATES": bands["ACCEPTED"] + bands["REJECTED"] + bands["UNRESOLVED"], "ACCEPTED_BANDS": bands["ACCEPTED"], "REJECTED_BANDS": bands["REJECTED"],
               "UNRESOLVED_BANDS": bands["UNRESOLVED"], "REJECTED_BY_REASON": bands["REJECTED_BY_REASON"], "UNRESOLVED_BY_REASON": bands["UNRESOLVED_BY_REASON"], "ACCEPTED_DEVELOPED_M_ALL_VIEWS": bands["ACCEPTED_DEVELOPED_M"],
               "ACCEPTED_WITH_FACE_DOUBLING": bands["ACCEPTED_WITH_FACE_DOUBLING"], "INTERVALS": R["PA07_BAND_INTERVAL_REGISTER"]["SUMMARY"], "SITES_BY_CLASS": R["PA07_OPENING_SITE_REGISTER"]["BY_CLASS"],
               "SITES_BY_STATUS": R["PA07_OPENING_SITE_REGISTER"]["BY_STATUS"], "PLANAR_FACES": R["PA07_PLANAR_FACE_REGISTER"]["BY_ELIGIBILITY"], "SPACES_ON_PLAN_VIEWS": qa["SPACES_ON_PLAN_VIEWS"],
               "SPACES_BY_GEOMETRY_STATUS": qa["SPACES_BY_GEOMETRY_STATUS"], "SPACES_BY_IDENTITY": qa["SPACES_BY_IDENTITY"], "MISSING_SPACE_QA": qa["MISSING_SPACE_QA"], "COLUMNS": qa["COLUMNS"],
               "MATERIAL_BOUNDARY_M_PLAN_INTERIOR_STRUCTURE_ONLY": qa["MATERIAL_BOUNDARY_M_PLAN_INTERIOR_STRUCTURE_ONLY"], "MATERIAL_BOUNDARY_M_PLAN_INTERIOR_ESTABLISHED_ONLY": qa["MATERIAL_BOUNDARY_M_PLAN_INTERIOR_ESTABLISHED_ONLY"],
               "QUANTITY_SAFETY": qa["QUANTITY_SAFETY"], "OWNER_DECISIONS": len(oq["QUEUE"]), "SOURCE_REQUESTS": len(sq["QUEUE"]), "TESTS": dict(Counter("PASS" if v else "FAIL" for v in tests.values())),
               "INDEPENDENT_VALIDATION": required["STATUS"], "GATE_V3_FAILED": gate["FAILED"], "ARCHITECTURE_REVIEW_BLOCKERS": None, "AI_CALLS_IN_BATCH": 0,
               "DETERMINISTIC_RUNTIME_S": run.metrics["DETERMINISTIC_RUNTIME_S"], "STAGE_RUNTIMES_S": {k: v["RUNTIME_S"] for k, v in run.metrics["STAGES"].items()}, "BATCH_WALL_CLOCK_S": round(time.perf_counter() - t0, 1), "ENGINE_VERSION": ENGINE_VERSION}
    write("PA07_METRICS", metrics)
    print(json.dumps({"GATE_V3": gate["VERDICT"], "FAILED": gate["FAILED"], "TESTS": metrics["TESTS"], "RUNTIME": metrics["BATCH_WALL_CLOCK_S"], "SPACES": qa["SPACES_ON_PLAN_VIEWS"]}, default=str))


if __name__ == "__main__":
    main()
