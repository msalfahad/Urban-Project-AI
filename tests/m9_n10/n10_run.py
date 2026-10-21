"""Phase N10 test helpers: the architectural CLI under ARCH_TAKEOFF_V2.9 (V2.8 for the as-found readings) on the
n10_fixtures drawings, and readers of its outputs (the Phase 2B-9 helpers, tests/m9_p2b9/p2b9_run.py)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "m9_p2b9"))
sys.path.insert(0, str(HERE.parent / "m9_p2b6"))

import p2b9_run as R9                                         # noqa: E402

V28, V29 = R9.V28, "ARCH_TAKEOFF_V2.9"
lines, rooms, unresolved, net, the, all_of, load = R9.lines, R9.rooms, R9.unresolved, R9.net, R9.the, R9.all_of, R9.load
reveals = R9.reveals if hasattr(R9, "reveals") else (lambda out: load(out, "WINDOW_REVEALS.json")["reveals"])


def run(dxf, out, *, roles=None, method=V29, units=None, facts=False):
    return R9.run(dxf, out, roles=roles, method=method, units=units, facts=facts)


def curved(out):
    return load(out, "CURVED_OPENINGS.json")


def floor_area(out):
    return sum(r["area_m2"] for r in rooms(out))


def range_of(out, item_code, element):
    ln = the(out, item_code, element)
    return ln.get("bounded_range") or {}


def run_facts(dxf, out, facts, *, method=V29, roles=None):
    """the CLI with a stated facts file (URBAN_ARCH_FACTS_V1) written next to the output."""
    import subprocess
    import p2b6_run as R6
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    fp = out.parent / (out.name + "_facts.json")
    fp.write_text(json.dumps(dict({"schema": "URBAN_ARCH_FACTS_V1"}, **facts)), encoding="utf-8")
    argv = [sys.executable, "-I", str(R6.CLI), "arch", "--drawings", str(dxf), "--out", str(out), "--method", method,
            "--facts", str(fp)]
    if roles:
        argv += ["--layer-roles", *roles]
    r = subprocess.run(argv, capture_output=True, text=True, cwd=str(out.parent))
    assert r.returncode == 0, r.stdout[-1500:] + r.stderr[-1500:]
    return out


def masonry(out):
    return load(out, "MASONRY.json")["floors"]
