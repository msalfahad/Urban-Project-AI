"""Phase N10 test helpers: the architectural CLI under ARCH_TAKEOFF_V2.9 (V2.8 for the as-found readings) on the
n10_fixtures drawings, and readers of its outputs (the Phase 2B-9 helpers, tests/m9_p2b9/p2b9_run.py)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "m9_p2b9"))

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
