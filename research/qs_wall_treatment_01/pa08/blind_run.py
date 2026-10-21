"""PA08 blind production run.

The production system receives only: the new project's permitted source drawings, the generic engine, the generic
approved rules (owner parameter registry declared as test-mode input).  It must not receive the truth pack, any
P7757 or 23010 artifact, benchmarks, workbooks or expected values.  Every file open is audited in a subprocess; any
forbidden read raises inside the run, the result is VALIDATION_INVALID and nothing downstream proceeds.  The output
is frozen by hash before the truth pack is opened.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

from research.qs_wall_treatment_01.pa08 import config as C8

POLICY = {"ARTIFACT": "PA08_BLIND_RUN_POLICY", "VERSION": "PA08-BR-1",
          "MAY_READ": ["the accepted source files of the new project (by exact path)", "engine/ and engine/ingest/ (generic engine)", "the generic Urban rule set / owner parameter registry declared as test-mode input",
                       "the blind output directory (its own writes)"],
          "MUST_NOT_READ": ["the sealed truth pack", "any P7757 artifact (data/experiments/P7757_*, data/golden/7757)", "data/golden/23010 and its benchmark files", "contractor workbooks / any .xlsx", "manual expected values",
                            "any *REVIEW*, *GUARDS*, *REGRESSION* artifact"],
          "ENFORCEMENT": "sys.addaudithook on open in a subprocess; a read outside the allowlist raises PermissionError inside the engine; the access log is written beside the output",
          "ON_VIOLATION": "STATUS = VALIDATION_INVALID; stop; nothing is compared", "FREEZE": "output register hashes recorded in FREEZE_PA08_BLIND.json before the truth pack is opened"}
ALLOW_PREFIXES = ("engine/",)

SCRIPT = r'''
import json, os, sys
from pathlib import Path
ALLOW = tuple(json.loads(os.environ["BLIND_ALLOW"])); FILES = tuple(json.loads(os.environ["BLIND_FILES"])); OUT = os.environ["BLIND_OUT"]; CFG = json.loads(os.environ["BLIND_CFG"])
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
    ok = rel.startswith(ALLOW) or rel in FILES or rel.startswith(OUT) or os.path.abspath(rel) in FILES
    LOG.append({"PATH": rel, "MODE": args[1], "ALLOWED": ok})
    if not ok and ("r" in (args[1] or "r")): raise PermissionError("BLIND VIOLATION: " + rel)
sys.addaudithook(hook)
from engine.ingest import pipeline7 as P7
try:
    P7.run(CFG, out_dir=OUT); status, err = "COMPLETED", None
except PermissionError as e: status, err = "VALIDATION_INVALID", str(e)
except Exception as e: status, err = "FAILED_ERROR", repr(e)
Path(OUT).mkdir(parents=True, exist_ok=True)
Path(OUT, "BLIND_ACCESS_LOG.json").write_text(json.dumps({"ARTIFACT": "PA08_BLIND_ACCESS_LOG", "STATUS": status, "ERROR": err, "OPENS": LOG, "VIOLATIONS": [l for l in LOG if not l["ALLOWED"]]}, indent=1), "utf-8")
print(status)
'''


def _sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def config_for(acceptance, registry, trades=("NORMAL_INTERNAL_PLASTER", "WET_ROOM_SPLATTER", "COLUMN_BONDING"), rule_version="URBAN_RULES_PA08_DRAFT", dry_run=False, owner_storey_names=None):
    """Sources only: no reads, no assignments, no overrides, no labels; the registry is a declared generic test-mode input.
    A PRIMITIVE_JSON (synthetic) source is admitted only in a dry run of the harness, never in validation."""
    sources = []
    for f in acceptance["FILES"]:
        if not f["EXISTS"] or f["KIND"] == "FORBIDDEN_SPREADSHEET":
            continue
        kind = "CAD_DECODE_JSON" if f["KIND"] == "CAD_DECODE_JSON" else ("PDF" if f["KIND"] == "PDF" else ("PRIMITIVE_JSON" if (dry_run and f["KIND"] == "PRIMITIVE_JSON_SYNTHETIC") else None))
        if kind is None:
            continue         # a raw DWG / DXF needs its decode; the acceptance record says so
        sources.append({"PATH": f["PATH"], "KIND": kind, "FAMILY": f.get("FAMILY") if f.get("FAMILY") != "UNDECLARED" else "ARCHITECTURAL"})
    return {"PROJECT_ID": acceptance["PROJECT_ALIAS"], "DRAWING_FAMILY": "VILLA_INDEPENDENT_VALIDATION", "REVISION": "R0", "CAD_UNITS": "mm", "RULE_VERSION": rule_version, "MAX_RUNTIME_S": 1800,
            "SOURCES": sources, "SHEET_METADATA": {}, "VIEW_ASSIGNMENTS": [], "LAYER_OVERRIDES": None, "OWNER_INPUTS": [], "PRINTED_LABELS": [], "OWNER_ANCHORS": [], "AI_LABELS": [],
            "DECLARED_UNITS": {}, "OWNER_PARAMETER_REGISTRY": registry, "OWNER_STOREY_NAMES": owner_storey_names or {}, "SHEET_INDEX_OWNER": {}, "TRADES": list(trades)}


def launch(cfg, allowed_files, out_dir=None):
    out = Path(out_dir or C8.BLIND_DIR)
    out.mkdir(parents=True, exist_ok=True)
    files = [str(Path(f)) for f in allowed_files] + [str(Path(f).resolve()) for f in allowed_files]
    env = dict(os.environ, BLIND_ALLOW=json.dumps(list(ALLOW_PREFIXES)), BLIND_FILES=json.dumps(files), BLIND_OUT=str(out), BLIND_CFG=json.dumps(cfg), PYTHONPATH=os.getcwd())
    proc = subprocess.run([sys.executable, "-c", SCRIPT], env=env, capture_output=True, text=True, timeout=3600)
    (out / "STDERR.txt").write_text(proc.stderr, "utf-8")
    logp = out / "BLIND_ACCESS_LOG.json"
    log = json.loads(logp.read_text("utf-8")) if logp.exists() else None
    status = (log or {}).get("STATUS", "FAILED_NO_LOG")
    rec = {"ARTIFACT": "PA08_BLIND_RESULT", "STATUS": status, "RETURN_CODE": proc.returncode, "STDERR_TAIL": proc.stderr[-1200:], "VIOLATIONS": (log or {}).get("VIOLATIONS"),
           "FILES_OPENED": sorted({l["PATH"] for l in (log or {}).get("OPENS", [])}), "OUTPUT_DIR": str(out), "TRUTH_OPENED_BEFORE_FREEZE": False}
    if status == "COMPLETED":
        rec["FREEZE"] = freeze_output(out)
    return rec


def freeze_output(out_dir):
    out = Path(out_dir)
    files = {p.name: _sha(p) for p in sorted(out.glob("*.json")) if p.name != "BLIND_ACCESS_LOG.json"}
    rec = {"ARTIFACT": "FREEZE_PA08_BLIND", "FILES": files, "DIGEST": hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest(), "TRUTH_STILL_SEALED": True}
    (out.parent / "FREEZE_PA08_BLIND.json").write_text(json.dumps(rec, indent=1), "utf-8")
    return rec
