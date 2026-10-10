"""PA06 blind rebuild gate (WS11): predeclared behavioural tolerances, a
frozen reference produced by the NEW architecture, a genuinely fresh
output directory, an audit hook on every file open, and a comparison
A-M.  Tolerances are declared here BEFORE the run and are never edited
after seeing a result: a poorly specified criterion is marked
APPARATUS_DEFECT and frozen as such.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from collections import Counter
from pathlib import Path

from research.qs_wall_treatment_01.pa06 import config as C6

BLIND_DIR = C6.BLIND_DIR
TOLERANCES = {
    "A_SOURCE_UNITS": {"RULE": "unit status and scale identical", "TOL": "exact"},
    "B_PLAN_COPY_TRANSFORMS": {"RULE": "same link set; DX / DY within 1 mm; rotation exact", "TOL_MM": 1.0},
    "C_PRIMITIVE_ROLE_COUNTS": {"RULE": "per-role count within max(5, 2 %)", "TOL_ABS": 5, "TOL_REL": 0.02},
    "D_MATERIAL_FACE_DEVELOPED_LENGTH": {"RULE": "total developed length of material entities within 1 %", "TOL_REL": 0.01},
    "E_OPENING_SITE_CLASSES": {"RULE": "exact counts for HIGH-authority classes (door, window, junction, continuity); unresolved / termination within 5 %", "HIGH": ["CONFIRMED_DOOR_OPENING", "CONFIRMED_WINDOW_OPENING", "CAD_JUNCTION_GAP", "MATERIAL_CONTINUITY_GAP"], "TOL_REL": 0.05},
    "F_PHYSICAL_SPACE_COUNT": {"RULE": "in-range cell and region counts exact, or every difference explained", "TOL": "exact"},
    "G_SPACE_BOUNDARY_WALL_LENGTH": {"RULE": "total vector material wall length of in-range cells within 1 %", "TOL_REL": 0.01},
    "H_CURVE_GEOMETRY": {"RULE": "arc radius set identical within 5 mm", "TOL_MM": 5.0},
    "I_DIMENSION_OWNERSHIP": {"RULE": "owner-status counts exact", "TOL": "exact"},
    "J_STOREY_TOPOLOGY": {"RULE": "copy-family count, member count and reference levels identical; names not required (they may rely on reads)", "TOL": "exact"},
    "K_CLOSURE_REVERSIBILITY": {"RULE": "all regions reversible with zero material in both runs", "TOL": "exact"},
    "L_SEMANTIC_ANCHORS": {"RULE": "anchor count and text-role counts exact; identity names not required", "TOL": "exact"},
    "M_QUANTITY_INPUT_TRACE": {"RULE": "line count and BY_STATUS counts exact", "TOL": "exact"},
}
PROTOCOL = {"ARTIFACT": "PA06_BLIND_PROTOCOL", "RUN_ID": "P7757_BLIND_REBUILD_02", "OUTPUT_DIR": str(BLIND_DIR), "REFERENCE": "supervised PA06 run frozen by hash before the blind run",
            "MAY_READ": ["source files", "generic engine (engine/, engine/ingest/)", "config with source locations only", "owner parameter registry (declared test-mode input)"],
            "MUST_NOT_READ": ["prior registers", "benchmark", "E1 / PA artifacts", "manually carried coordinates or room ids", "hard-coded layer roles"],
            "ENFORCEMENT": "sys.addaudithook on open; any read outside the allowlist raises; the access log is written beside the outputs",
            "TOLERANCES_DECLARED_BEFORE_RUN": TOLERANCES, "GATE_WEAKENING_AFTER_RESULT": "forbidden; a mis-specified criterion becomes APPARATUS_DEFECT"}
ALLOW_PREFIXES = ("data/golden/", "data/runs/cad_convert/", "engine/", "research/qs_wall_treatment_01/pa06/", "research/qs_wall_treatment_01/pa05/", "tests/data/", str(BLIND_DIR))

SCRIPT = r'''
import json, os, sys
from pathlib import Path
ALLOW = tuple(json.loads(os.environ["BLIND_ALLOW"])); EXTRA = tuple(json.loads(os.environ["BLIND_EXTRA_FILES"])); OUT = os.environ["BLIND_OUT"]
LOG = []; ROOT = str(Path.cwd())
SYSTEM = ("/usr/", "/opt/", "/etc/", "/proc/", "/dev/", "/sys/", sys.prefix, sys.base_prefix, sys.exec_prefix)
def hook(event, args):
    if event != "open": return
    path = args[0]
    if not isinstance(path, str): return
    if path.startswith("/"):
        if path.startswith(ROOT + "/"): rel = path[len(ROOT) + 1:]
        elif path.startswith(SYSTEM) or "site-packages" in path or "/lib/python" in path: return
        else: rel = path
    else: rel = path
    if "__pycache__" in rel or rel.endswith((".pyc", ".py", ".pth")): return
    ok = rel.startswith(ALLOW) or rel in EXTRA or rel.startswith(OUT)
    LOG.append({"PATH": rel, "MODE": args[1], "ALLOWED": ok})
    if not ok and ("r" in (args[1] or "r")): raise PermissionError("BLIND VIOLATION: " + rel)
sys.addaudithook(hook)
from engine.ingest import pipeline as PL
from research.qs_wall_treatment_01.pa06 import config as C6
cfg = C6.blind()
try:
    PL.run(cfg, out_dir=OUT); status, err = "COMPLETED", None
except PermissionError as e: status, err = "FAILED_ACCESS", str(e)
except Exception as e: status, err = "FAILED_ERROR", repr(e)
Path(OUT).mkdir(parents=True, exist_ok=True)
Path(OUT, "BLIND_ACCESS_LOG.json").write_text(json.dumps({"ARTIFACT": "BLIND_ACCESS_LOG", "STATUS": status, "ERROR": err, "OPENS": LOG, "VIOLATIONS": [l for l in LOG if not l["ALLOWED"]]}, indent=1), "utf-8")
print(status)
'''


def _sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def freeze_reference(ref_dir):
    files = sorted(p for p in Path(ref_dir).glob("*.json") if p.name != "HARNESS_METRICS.json")
    body = {"ARTIFACT": "FREEZE_PA06_REFERENCE", "DIR": str(ref_dir), "FILES": {p.name: _sha(p) for p in files}}
    body["DIGEST"] = hashlib.sha256(json.dumps(body["FILES"], sort_keys=True).encode()).hexdigest()
    return body


def launch(extra_files=()):
    BLIND_DIR.mkdir(parents=True, exist_ok=True)
    (BLIND_DIR / "PA06_BLIND_PROTOCOL.json").write_text(json.dumps(PROTOCOL, indent=1), "utf-8")
    env = dict(os.environ, BLIND_ALLOW=json.dumps(list(ALLOW_PREFIXES)), BLIND_EXTRA_FILES=json.dumps(list(extra_files)), BLIND_OUT=str(BLIND_DIR / "pipeline"), PYTHONPATH=os.getcwd())
    proc = subprocess.run([sys.executable, "-c", SCRIPT], env=env, capture_output=True, text=True, timeout=1800)
    (BLIND_DIR / "STDERR.txt").write_text(proc.stderr, "utf-8")
    logp = BLIND_DIR / "pipeline" / "BLIND_ACCESS_LOG.json"
    log = json.loads(logp.read_text("utf-8")) if logp.exists() else None
    status = (log or {}).get("STATUS", "FAILED_NO_LOG")
    rec = {"ARTIFACT": "PA06_BLIND_RESULT", "STATUS": status, "RETURN_CODE": proc.returncode, "STDERR_TAIL": proc.stderr[-1200:], "VIOLATIONS": (log or {}).get("VIOLATIONS"),
           "FILES_OPENED": sorted({l["PATH"] for l in (log or {}).get("OPENS", [])}), "OUTPUT_DIR": str(BLIND_DIR / "pipeline")}
    if status == "COMPLETED":
        rec["FREEZE"] = freeze_reference(BLIND_DIR / "pipeline"); rec["FREEZE"]["ARTIFACT"] = "FREEZE_PA06_BLIND"
        (BLIND_DIR / "FREEZE_PA06_BLIND.json").write_text(json.dumps(rec["FREEZE"], indent=1), "utf-8")
    (BLIND_DIR / "PA06_BLIND_RESULT.json").write_text(json.dumps(rec, indent=1), "utf-8")
    return rec


def _load(d, n):
    p = Path(d) / f"{n}.json"
    return json.loads(p.read_text("utf-8")) if p.exists() else None


def _rel(a, b):
    return abs(a - b) / max(abs(a), abs(b), 1e-9)


def compare(blind_dir, ref_dir, ref_freeze):
    for name, h in ref_freeze["FILES"].items():
        assert _sha(Path(ref_dir) / name) == h, f"reference {name} changed since its freeze"
    b = {n: _load(blind_dir, n) for n in ("PA06_SOURCE_UNIT_REGISTER", "PA06_VIEW_COPY_FAMILY_REGISTER", "PA06_PRIMITIVE_ROLE_REGISTER", "PA06_MATERIAL_GEOMETRY_REGISTER", "PA06_TOPOLOGICAL_SITE_REGISTER",
                                         "PA06_PHYSICAL_SPACE_REGISTER", "PA06_SPACE_WALL_LENGTH_REGISTER", "CURVE_REGISTER", "DIMENSION_CHAIN_REGISTER", "PA06_STOREY_REGISTER", "PA06_TRADE_MEASUREMENT_REGION_REGISTER",
                                         "PA06_SEMANTIC_ANCHOR_REGISTER", "PA06_QUANTITY_INPUT_TRACE")}
    s = {n: _load(ref_dir, n) for n in b}
    rows = []
    def row(key, blind, ref, ok, note=None):
        rows.append({"CRITERION": key, "RULE": TOLERANCES[key]["RULE"], "BLIND": blind, "REFERENCE": ref, "PASS": bool(ok), "NOTE": note})
    # A
    ua = [(r["SOURCE_ID"], r["STATUS"], r["UNIT_SCALE_TO_MM"]) for r in b["PA06_SOURCE_UNIT_REGISTER"]["ROWS"]]; us = [(r["SOURCE_ID"], r["STATUS"], r["UNIT_SCALE_TO_MM"]) for r in s["PA06_SOURCE_UNIT_REGISTER"]["ROWS"]]
    row("A_SOURCE_UNITS", ua, us, ua == us)
    # B
    lb = sorted((l["FROM_VIEW"], l["TO_VIEW"], l["ROTATION_DEG"], round(l["DX_MM"]), round(l["DY_MM"])) for l in b["PA06_VIEW_COPY_FAMILY_REGISTER"]["LINKS"])
    ls = sorted((l["FROM_VIEW"], l["TO_VIEW"], l["ROTATION_DEG"], round(l["DX_MM"]), round(l["DY_MM"])) for l in s["PA06_VIEW_COPY_FAMILY_REGISTER"]["LINKS"])
    okb = len(lb) == len(ls) and all(x[:3] == y[:3] and abs(x[3] - y[3]) <= 1 and abs(x[4] - y[4]) <= 1 for x, y in zip(lb, ls))
    row("B_PLAN_COPY_TRANSFORMS", lb, ls, okb)
    # C
    rb = {k: v["COUNT"] for k, v in b["PA06_PRIMITIVE_ROLE_REGISTER"]["BY_ROLE"].items()}; rs = {k: v["COUNT"] for k, v in s["PA06_PRIMITIVE_ROLE_REGISTER"]["BY_ROLE"].items()}
    bad = {k: (rb.get(k, 0), rs.get(k, 0)) for k in set(rb) | set(rs) if abs(rb.get(k, 0) - rs.get(k, 0)) > max(5, 0.02 * max(rb.get(k, 0), rs.get(k, 0)))}
    row("C_PRIMITIVE_ROLE_COUNTS", rb, rs, not bad, f"outside tolerance: {bad}" if bad else None)
    # D
    db = sum(m["LENGTH_MM"] for m in b["PA06_MATERIAL_GEOMETRY_REGISTER"]["ROWS"]) / 1000; ds = sum(m["LENGTH_MM"] for m in s["PA06_MATERIAL_GEOMETRY_REGISTER"]["ROWS"]) / 1000
    row("D_MATERIAL_FACE_DEVELOPED_LENGTH", round(db, 3), round(ds, 3), _rel(db, ds) <= 0.01)
    # E
    eb, es = b["PA06_TOPOLOGICAL_SITE_REGISTER"]["SUMMARY"], s["PA06_TOPOLOGICAL_SITE_REGISTER"]["SUMMARY"]
    high_ok = all(eb.get(k, 0) == es.get(k, 0) for k in TOLERANCES["E_OPENING_SITE_CLASSES"]["HIGH"])
    low_ok = all(_rel(eb.get(k, 0), es.get(k, 0)) <= 0.05 for k in ("UNRESOLVED_SITE", "TRUE_WALL_TERMINATION"))
    row("E_OPENING_SITE_CLASSES", eb, es, high_ok and low_ok)
    # F
    fb, fs = b["PA06_PHYSICAL_SPACE_REGISTER"]["COUNTS"], s["PA06_PHYSICAL_SPACE_REGISTER"]["COUNTS"]
    row("F_PHYSICAL_SPACE_COUNT", fb, fs, fb["CELLS_IN_RANGE"] == fs["CELLS_IN_RANGE"] and fb["REGIONS_IN_RANGE"] == fs["REGIONS_IN_RANGE"],
        None if fb == fs else "difference must be explained per cell (view roles: the blind run classifies views from geometry hints only)")
    # G
    gb, gs = b["PA06_SPACE_WALL_LENGTH_REGISTER"]["TOTALS_STRUCTURE_ONLY"]["VECTOR_MATERIAL_WALL_M_IN_RANGE_CELLS"], s["PA06_SPACE_WALL_LENGTH_REGISTER"]["TOTALS_STRUCTURE_ONLY"]["VECTOR_MATERIAL_WALL_M_IN_RANGE_CELLS"]
    row("G_SPACE_BOUNDARY_WALL_LENGTH", gb, gs, _rel(gb, gs) <= 0.01)
    # H
    hb = sorted({round(c["R_MM"], 1) for c in b["CURVE_REGISTER"]["ROWS"] if c["KIND"] == "ARC"}); hs = sorted({round(c["R_MM"], 1) for c in s["CURVE_REGISTER"]["ROWS"] if c["KIND"] == "ARC"})
    okh = len(hb) == len(hs) and all(abs(x - y) <= 5.0 for x, y in zip(hb, hs))
    row("H_CURVE_GEOMETRY", {"N": len(hb)}, {"N": len(hs)}, okh)
    # I
    ib, is_ = b["DIMENSION_CHAIN_REGISTER"]["COUNTS"]["BY_OWNER_STATUS"], s["DIMENSION_CHAIN_REGISTER"]["COUNTS"]["BY_OWNER_STATUS"]
    row("I_DIMENSION_OWNERSHIP", ib, is_, ib == is_)
    # J
    jb = {"FAMILIES": len(b["PA06_VIEW_COPY_FAMILY_REGISTER"]["FAMILIES"]), "MEMBERS": sorted(len(f["MEMBERS"]) for f in b["PA06_VIEW_COPY_FAMILY_REGISTER"]["FAMILIES"]), "LEVELS": sorted(str(r["REFERENCE_LEVEL"]) for r in b["PA06_STOREY_REGISTER"]["ROWS"])}
    js = {"FAMILIES": len(s["PA06_VIEW_COPY_FAMILY_REGISTER"]["FAMILIES"]), "MEMBERS": sorted(len(f["MEMBERS"]) for f in s["PA06_VIEW_COPY_FAMILY_REGISTER"]["FAMILIES"]), "LEVELS": sorted(str(r["REFERENCE_LEVEL"]) for r in s["PA06_STOREY_REGISTER"]["ROWS"])}
    row("J_STOREY_TOPOLOGY", jb, js, jb == js)
    # K
    kb, ks = b["PA06_TRADE_MEASUREMENT_REGION_REGISTER"]["REVERSIBILITY"], s["PA06_TRADE_MEASUREMENT_REGION_REGISTER"]["REVERSIBILITY"]
    row("K_CLOSURE_REVERSIBILITY", kb, ks, bool(kb.get("ALL_REVERSIBLE")) and bool(kb.get("ALL_ZERO_MATERIAL")) and bool(ks.get("ALL_REVERSIBLE")) and bool(ks.get("ALL_ZERO_MATERIAL")))
    # L
    lb_, ls_ = b["PA06_SEMANTIC_ANCHOR_REGISTER"]["COUNTS"], s["PA06_SEMANTIC_ANCHOR_REGISTER"]["COUNTS"]
    row("L_SEMANTIC_ANCHORS", {"ANCHORS": lb_["ANCHORS"], "BY_TEXT_ROLE": lb_["BY_TEXT_ROLE"]}, {"ANCHORS": ls_["ANCHORS"], "BY_TEXT_ROLE": ls_["BY_TEXT_ROLE"]}, lb_["ANCHORS"] == ls_["ANCHORS"] and lb_["BY_TEXT_ROLE"] == ls_["BY_TEXT_ROLE"])
    # M
    mb = {"COUNT": b["PA06_QUANTITY_INPUT_TRACE"]["COUNT"], "BY_STATUS": b["PA06_QUANTITY_INPUT_TRACE"]["BY_STATUS"]}; ms = {"COUNT": s["PA06_QUANTITY_INPUT_TRACE"]["COUNT"], "BY_STATUS": s["PA06_QUANTITY_INPUT_TRACE"]["BY_STATUS"]}
    row("M_QUANTITY_INPUT_TRACE", mb, ms, mb == ms)
    return {"ARTIFACT": "PA06_BLIND_COMPARISON", "REFERENCE_DIGEST": ref_freeze["DIGEST"], "ROWS": rows, "PASS": all(r["PASS"] for r in rows), "FAILED": [r["CRITERION"] for r in rows if not r["PASS"]],
            "QUANTITIES_COMPARED": False, "TOLERANCES_EDITED_AFTER_RESULT": False}
