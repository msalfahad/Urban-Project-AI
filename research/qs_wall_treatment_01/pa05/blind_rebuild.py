"""P7757_BLIND_REBUILD_01 (PA05 §19, §20).

A fresh output directory, the generic engine, the original sources and the
approved owner inputs only.  A process-level audit hook records every file
the run opens and aborts on any read outside the allowlist (old
quantities, reconciliations, the Excel benchmark, owner correction
quantities, old region ids, old runner outputs).  The comparison (§20)
runs only after the blind outputs are frozen by hash, and compares
structure - face identity, opening identity, curve geometry, room / zone
relationships, dimension ownership, host-wall lengths, measurement-region
structure - never quantities.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from collections import Counter
from pathlib import Path

BLIND_DIR = Path("data/experiments/P7757_BLIND_REBUILD_01")
PROTOCOL = {
    "ARTIFACT": "P7757_BLIND_REBUILD_PROTOCOL", "RUN_ID": "P7757_BLIND_REBUILD_01", "OUTPUT_DIR": str(BLIND_DIR),
    "MAY_READ": ["the original DWG decode and the two PDF sets (as source files)", "approved Urban standards (none exist yet: the rule library holds no approved URBAN_STANDARD)",
                 "approved owner project inputs (OWNER_CONFIRMED = true, values only, no quantities)", "the generic engine (engine/, engine/ingest/)", "python / site-packages"],
    "MUST_NOT_READ": ["old P7757 quantities (estimates, plaster trace, dual basis)", "old reconciliation (A22, benchmark reconciliation)", "the Excel benchmark", "owner manual correction quantities",
                      "old region ids (PA04 face registers, challenger maps)", "old P7757 runner outputs (data/experiments/P7757_WALL_TREATMENT_ESTIMATE_01 and every earlier experiment)"],
    "ENFORCEMENT": "sys.addaudithook on 'open' inside the blind subprocess: any read outside the allowlist raises and the run is marked FAILED_ACCESS; the access log is written beside the outputs",
    "SHEET_ROLES": "no PA04 sheet reads are supplied: raster sheets stay UNKNOWN unless the deterministic path decides; model-space views are classified from geometry hints only",
    "LAYER_PROFILE": "no overrides: layer roles from evidence statistics only",
    "OWNER_INPUTS": "only OWNER_CONFIRMED parameters from the owner registry, passed as values",
    "COMPARISON": "after the blind freeze, structure-only (§20); quantities never compared",
}
ALLOW_PREFIXES = ("data/golden/", "data/runs/cad_convert/", "engine/", "research/qs_wall_treatment_01/pa05/", "tests/data/", str(BLIND_DIR))


def _sha(p):
    h = hashlib.sha256(); h.update(Path(p).read_bytes()); return h.hexdigest()


BLIND_SCRIPT = r'''
import json, os, sys
from pathlib import Path
ALLOW = tuple(json.loads(os.environ["BLIND_ALLOW"]))
EXTRA = tuple(json.loads(os.environ["BLIND_EXTRA_FILES"]))
OUT = os.environ["BLIND_OUT"]
LOG = []
ROOT = str(Path.cwd())
def hook(event, args):
    if event != "open":
        return
    path = args[0]
    if not isinstance(path, str):
        return
    SYSTEM = ("/usr/", "/opt/", "/etc/", "/proc/", "/dev/", "/sys/", sys.prefix, sys.base_prefix, sys.exec_prefix)
    if path.startswith("/"):
        if path.startswith(ROOT + "/"):
            rel = path[len(ROOT) + 1:]
        elif path.startswith(SYSTEM) or "site-packages" in path or "/lib/python" in path:
            return          # interpreter / site-packages / system files
        else:
            rel = path      # any other absolute path (uploads, home) is audited against the explicit extra-file list
    else:
        rel = path
    if "__pycache__" in rel or rel.endswith((".pyc", ".py", ".pth")):
        return
    ok = rel.startswith(ALLOW) or rel in EXTRA or rel.startswith(OUT)
    LOG.append({"PATH": rel, "MODE": args[1], "ALLOWED": ok})
    if not ok and ("r" in (args[1] or "r")):
        raise PermissionError(f"BLIND VIOLATION: read outside the allowlist: {rel}")
sys.addaudithook(hook)
from engine.ingest import harness as H
from research.qs_wall_treatment_01.pa05 import config_p7757 as CF
cfg = json.loads(os.environ["BLIND_CONFIG"])
try:
    r = H.run(cfg, out_dir=OUT)
    status = "COMPLETED"
    err = None
except PermissionError as e:
    status, err = "FAILED_ACCESS", str(e)
except Exception as e:
    status, err = "FAILED_ERROR", repr(e)
Path(OUT).mkdir(parents=True, exist_ok=True)
Path(OUT, "BLIND_ACCESS_LOG.json").write_text(json.dumps({"ARTIFACT": "BLIND_ACCESS_LOG", "STATUS": status, "ERROR": err, "OPENS": LOG,
    "VIOLATIONS": [l for l in LOG if not l["ALLOWED"]]}, indent=1), "utf-8")
print(status)
'''


def blind_config(owner_inputs):
    """Sources + confirmed owner inputs only: no sheet reads, no view assignments, no layer overrides."""
    from research.qs_wall_treatment_01.pa05 import config_p7757 as CF
    return {"PROJECT_ID": "P7757", "DRAWING_FAMILY": "VILLA_KUWAIT_2026", "REVISION": "R0", "CAD_UNITS": "mm", "RULE_VERSION": "URBAN_RULES_PA05_DRAFT", "MAX_RUNTIME_S": 600,
            "SOURCES": [{"PATH": CF.DECODE, "KIND": "CAD_DECODE_JSON", "FAMILY": "ARCHITECTURAL"}, {"PATH": CF.ARCH_PDF, "KIND": "PDF", "FAMILY": "ARCHITECTURAL"}, {"PATH": CF.ST_PDF, "KIND": "PDF", "FAMILY": "STRUCTURAL"}],
            "SHEET_METADATA": {}, "VIEW_ASSIGNMENTS": [], "LAYER_OVERRIDES": None, "OWNER_INPUTS": owner_inputs, "PRINTED_LABELS": [], "OWNER_ANCHORS": []}


def launch(owner_inputs, extra_files=()):
    """Run the blind rebuild in a subprocess under the audit hook; returns the status record."""
    BLIND_DIR.mkdir(parents=True, exist_ok=True)
    (BLIND_DIR / "PROTOCOL.json").write_text(json.dumps(PROTOCOL, indent=1), "utf-8")
    cfg = blind_config(owner_inputs)
    env = dict(os.environ, BLIND_ALLOW=json.dumps(list(ALLOW_PREFIXES)), BLIND_EXTRA_FILES=json.dumps(list(extra_files)), BLIND_OUT=str(BLIND_DIR / "harness"), BLIND_CONFIG=json.dumps(cfg, default=str),
               PYTHONPATH=os.getcwd())
    proc = subprocess.run([sys.executable, "-c", BLIND_SCRIPT], env=env, capture_output=True, text=True, timeout=1800)
    (BLIND_DIR / "STDERR.txt").write_text(proc.stderr, "utf-8")
    log = json.loads((BLIND_DIR / "harness" / "BLIND_ACCESS_LOG.json").read_text("utf-8")) if (BLIND_DIR / "harness" / "BLIND_ACCESS_LOG.json").exists() else None
    status = (log or {}).get("STATUS", "FAILED_NO_LOG")
    rec = {"ARTIFACT": "P7757_BLIND_REBUILD_RESULT", "STATUS": status, "RETURN_CODE": proc.returncode, "STDERR_TAIL": proc.stderr[-1500:], "VIOLATIONS": (log or {}).get("VIOLATIONS"),
           "FILES_OPENED": sorted({l["PATH"] for l in (log or {}).get("OPENS", [])}), "OUTPUT_DIR": str(BLIND_DIR / "harness")}
    if status == "COMPLETED":
        files = sorted(p for p in (BLIND_DIR / "harness").glob("*.json") if p.name != "BLIND_ACCESS_LOG.json")
        rec["FREEZE"] = {"ARTIFACT": "FREEZE_BLIND_REBUILD_01", "FILES": {p.name: _sha(p) for p in files}}
        rec["FREEZE"]["DIGEST"] = hashlib.sha256(json.dumps(rec["FREEZE"]["FILES"], sort_keys=True).encode()).hexdigest()
        (BLIND_DIR / "FREEZE_BLIND_REBUILD_01.json").write_text(json.dumps(rec["FREEZE"], indent=1), "utf-8")
    (BLIND_DIR / "RESULT.json").write_text(json.dumps(rec, indent=1), "utf-8")
    return rec


# ------------------------------------------------------------------ §20 comparison (after the freeze)
def _load(dirpath, name):
    p = Path(dirpath) / f"{name}.json"
    return json.loads(p.read_text("utf-8")) if p.exists() else None


def compare(blind_dir, supervised_dir, old_out):
    """Structure-only comparison of the frozen blind outputs against (a) the supervised PA05 run and (b) the frozen PA03/PA04 artifacts."""
    freeze = json.loads((Path(blind_dir).parent / "FREEZE_BLIND_REBUILD_01.json").read_text("utf-8"))
    for name, h in freeze["FILES"].items():
        assert _sha(Path(blind_dir) / name) == h, f"blind output {name} changed since the freeze"
    b, s = {}, {}
    for n in ("ATOMIC_FACE_REGISTER", "OPENING_SITE_REGISTER", "PHYSICAL_SPACE_REGISTER", "DIMENSION_CHAIN_REGISTER", "MEASUREMENT_REGION_REGISTER", "SHEET_ROLE_REGISTER", "VIEW_TRANSFORMS", "CURVE_REGISTER"):
        b[n], s[n] = _load(blind_dir, n), _load(supervised_dir, n)
    rows = []
    def row(topic, blind, supervised, old, verdict, note=None):
        rows.append({"TOPIC": topic, "BLIND": blind, "SUPERVISED_PA05": supervised, "FROZEN_PA03_PA04": old, "VERDICT": verdict, "NOTE": note})
    # face identity: entity-id sets are view-dependent (view ids include the sheet hash, identical here) -> compare id overlap
    bf = {f["FACE_ID"] for f in b["ATOMIC_FACE_REGISTER"]["ROWS"]}; sf = {f["FACE_ID"] for f in s["ATOMIC_FACE_REGISTER"]["ROWS"]}
    row("FACE_IDENTITY", len(bf), len(sf), None, "AGREE" if bf == sf else "DIFFER", f"overlap {len(bf & sf)}: the supervised run removes the hidden layer by override; ids of shared faces are identical")
    row("FACE_DEVELOPED_LENGTH_BY_TYPE", b["ATOMIC_FACE_REGISTER"]["SUMMARY"], s["ATOMIC_FACE_REGISTER"]["SUMMARY"], None, "STRUCTURE_ONLY")
    bo = {o["OPENING_SITE_ID"]: o["CLASS"] for o in b["OPENING_SITE_REGISTER"]["ROWS"]}; so = {o["OPENING_SITE_ID"]: o["CLASS"] for o in s["OPENING_SITE_REGISTER"]["ROWS"]}
    same = sum(1 for k in bo if k in so and so[k] == bo[k])
    old_open = json.loads((Path(old_out) / "pa04" / "OPENING_REGISTER_V2.json").read_text("utf-8"))
    row("OPENING_IDENTITY", b["OPENING_SITE_REGISTER"]["SUMMARY"], s["OPENING_SITE_REGISTER"]["SUMMARY"], {"OLD_OPENINGS": old_open["COUNT"] if isinstance(old_open.get("COUNT"), int) else len(old_open["OPENINGS"])},
        "AGREE" if same == len(bo) == len(so) else "DIFFER", f"{same} sites identical in id and class; old register has no plan coordinates so identity cannot be matched")
    old_curves = json.loads((Path(old_out) / "CAD_CURVE_REGISTER.json").read_text("utf-8"))
    old_radii = sorted({round(a["RADIUS_MM"]) for cs in old_curves["CURVE_SETS"] for a in cs["ARCS"]})
    b_radii = sorted({round(c["R_MM"], 1) for c in b["CURVE_REGISTER"]["ROWS"] if c["KIND"] == "ARC"})
    s_radii = sorted({round(c["R_MM"], 1) for c in s["CURVE_REGISTER"]["ROWS"] if c["KIND"] == "ARC"})
    missing = [r for r in old_radii if not any(abs(r - x) <= 1.0 for x in b_radii)]
    row("CURVE_GEOMETRY", {"ARC_RADII_MM": b_radii[:80], "N_ARCS": b["CURVE_REGISTER"]["COUNT"]}, {"N_ARCS": s["CURVE_REGISTER"]["COUNT"], "SAME_RADII_SET": b_radii == s_radii},
        {"ARC_RADII_MM": old_radii, "MISSING_IN_BLIND": missing}, "AGREE" if not missing and b_radii == s_radii else "DIFFER",
        "every frozen curve-register radius must reappear in the blind CURVE_REGISTER (1 mm tolerance) and blind / supervised radii sets must be identical")
    row("ROOM_ZONE_RELATIONSHIPS", dict(b["PHYSICAL_SPACE_REGISTER"]["COUNTS"]), dict(s["PHYSICAL_SPACE_REGISTER"]["COUNTS"]), None, "STRUCTURE_ONLY", "spaces per topology status; identities are anchors, not names")
    row("DIMENSION_OWNERSHIP", b["DIMENSION_CHAIN_REGISTER"]["COUNTS"], s["DIMENSION_CHAIN_REGISTER"]["COUNTS"], None,
        "AGREE" if b["DIMENSION_CHAIN_REGISTER"]["COUNTS"]["BY_OWNER_STATUS"] == s["DIMENSION_CHAIN_REGISTER"]["COUNTS"]["BY_OWNER_STATUS"] else "DIFFER")
    bl = round(sum(sp["WALL_BOUNDARY_LM"] for sp in b["PHYSICAL_SPACE_REGISTER"]["ROWS"]), 1); sl = round(sum(sp["WALL_BOUNDARY_LM"] for sp in s["PHYSICAL_SPACE_REGISTER"]["ROWS"]), 1)
    row("HOST_WALL_LENGTHS_LM_TOTAL", bl, sl, None, "STRUCTURE_ONLY", "sum of wall boundary lm over all spaces (a structure metric, not a quantity line)")
    row("MEASUREMENT_REGION_STRUCTURE", {"REGIONS": len(b["MEASUREMENT_REGION_REGISTER"]["ROWS"]), "REVERSIBLE": b["MEASUREMENT_REGION_REGISTER"]["ALL_REVERSIBLE"]},
        {"REGIONS": len(s["MEASUREMENT_REGION_REGISTER"]["ROWS"]), "REVERSIBLE": s["MEASUREMENT_REGION_REGISTER"]["ALL_REVERSIBLE"]}, None,
        "AGREE" if b["MEASUREMENT_REGION_REGISTER"]["ALL_REVERSIBLE"] and s["MEASUREMENT_REGION_REGISTER"]["ALL_REVERSIBLE"] else "DIFFER")
    row("SHEET_ROLES", dict(Counter(r["FINAL_ROLE"] for r in b["SHEET_ROLE_REGISTER"]["SHEETS"])), dict(Counter(r["FINAL_ROLE"] for r in s["SHEET_ROLE_REGISTER"]["SHEETS"])), None, "STRUCTURE_ONLY",
        "blind: no AI reads -> raster sheets UNKNOWN; only the two vector schedule titles classify deterministically")
    row("VIEW_ROLES", [(r["FINAL_ROLE"], r["ROLE_STATUS"]) for r in b["SHEET_ROLE_REGISTER"]["VIEWS"]], [(r["FINAL_ROLE"], r["ROLE_STATUS"]) for r in s["SHEET_ROLE_REGISTER"]["VIEWS"]], None, "STRUCTURE_ONLY")
    row("PLAN_COPY_OFFSETS", [round(o["DX_MM"], 2) for o in b["VIEW_TRANSFORMS"]["COPY_OFFSETS"]], [round(o["DX_MM"], 2) for o in s["VIEW_TRANSFORMS"]["COPY_OFFSETS"]], None,
        "AGREE" if [round(o["DX_MM"], 2) for o in b["VIEW_TRANSFORMS"]["COPY_OFFSETS"]] == [round(o["DX_MM"], 2) for o in s["VIEW_TRANSFORMS"]["COPY_OFFSETS"]] else "DIFFER")
    return {"ARTIFACT": "P7757_BLIND_REBUILD_COMPARISON", "BLIND_FREEZE_DIGEST": freeze["DIGEST"], "ROWS": rows, "QUANTITIES_COMPARED": False,
            "VERDICTS": dict(Counter(r["VERDICT"] for r in rows))}
