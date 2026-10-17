"""Phase 2B-6 test helpers: the architectural CLI on a synthetic drawing, and its totals."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CLI = ROOT / "tools" / "urban_boq_m9.py"
AUDIT = ROOT / "tools" / "arch_run_audit.py"
# synthetic heights, stated as test inputs (the S2 facts template's values)
FACTS = {"schema": "URBAN_ARCH_FACTS_V1",
         "wall_heights": {"*": {k: {"value_m": v, "authority": "OWNER_PROJECT_FACT: synthetic test parameter"}
                                for k, v in (("PLASTER", 3.0), ("PAINT", 3.0), ("WALL_TILE", 2.4))}},
         "opening_heights": {k: {"value_m": v, "authority": "OWNER_PROJECT_FACT: synthetic test parameter"}
                             for k, v in (("DOOR", 2.1), ("WINDOW", 1.5))}}


def run(dxf, out, *, roles=None, facts=False, method="ARCH_TAKEOFF_V2.6"):
    argv = [sys.executable, "-I", str(CLI), "arch", "--drawings", str(dxf), "--out", str(out), "--method", method]
    if facts:
        fp = Path(out).parent / "facts.json"
        fp.write_text(json.dumps(FACTS), encoding="utf-8")
        argv += ["--facts", str(fp)]
    if roles:
        argv += ["--layer-roles", *roles]
    r = subprocess.run(argv, capture_output=True, text=True, cwd=str(Path(out).parent))
    assert r.returncode == 0, r.stdout[-1500:] + r.stderr[-1500:]
    return Path(out)


def load(out, name):
    return json.loads((Path(out) / name).read_text(encoding="utf-8"))


def lines(out):
    return load(out, "BOQ_LINES.json")


def totals(out):
    """{(item_code, room name with opening ids masked): (net total, line count)} - element ids renumber under
    transformations, quantities must not."""
    t, n = defaultdict(float), defaultdict(int)
    for ln in lines(out):
        name = re.sub(r"OP-\d+", "OP-*", (ln.get("location") or {}).get("room_name_en") or "-")
        k = (ln["item_code"], name)
        t[k] += ln.get("measured_net") or 0.0
        n[k] += 1
    return {k: (round(t[k], 6), n[k]) for k in t}


def rooms(out):
    return load(out, "ARCH_ROOMS.json")["rooms"]


def roles_of(out):
    return load(out, "ARCH_PLAN.json")["regions"][0]["layer_roles"]


def audit(run_dir, dxf=None, *extra):
    argv = [sys.executable, "-I", str(AUDIT), "--run", str(run_dir), *(["--dxf", str(dxf)] if dxf else []), *extra]
    r = subprocess.run(argv, capture_output=True, text=True)
    return r.returncode, (json.loads(r.stdout) if r.stdout.strip().startswith("{") else None), r.stderr
