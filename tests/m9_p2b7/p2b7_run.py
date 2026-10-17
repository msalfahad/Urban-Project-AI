"""Phase 2B-7 test helpers: the architectural CLI under ARCH_TAKEOFF_V2.7 (and V2.6 for before / after), and readers
of its outputs. The heights are the synthetic S2 facts of tests/m9_p2b6/p2b6_run (stated test inputs)."""

from __future__ import annotations

import json
import math
import re
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "m9_p2b6"))

import p2b6_run as R6                                         # noqa: E402

V26, V27 = "ARCH_TAKEOFF_V2.6", "ARCH_TAKEOFF_V2.7"
FACTS = R6.FACTS
load, lines, rooms, roles_of = R6.load, R6.lines, R6.rooms, R6.roles_of


def run(dxf, out, *, roles=None, facts=False, method=V27):
    return R6.run(dxf, out, roles=roles, facts=facts, method=method)


def totals(out):
    return R6.totals(out)


def openings(out, kind=None):
    return [o for o in load(out, "ARCH_OPENINGS.json")["openings"] if kind is None or o["kind"] == kind]


def net(out, code, room=None):
    """the summed measured net of an item, optionally in rooms whose English name starts with `room`."""
    return round(sum(ln["measured_net"] or 0.0 for ln in lines(out) if ln["item_code"] == code and
                     (room is None or ((ln.get("location") or {}).get("room_name_en") or "").startswith(room))), 6)


def room(out, name):
    return [r for r in rooms(out) if r["name_en"].startswith(name)]


def corrections(out):
    return load(out, "CORRECTIONS_V2_7.json")["corrections"]


def plan_evidence(out, region=0):
    return load(out, "ARCH_PLAN.json")["regions"][region]["layer_evidence"]


def unresolved(out):
    return load(out, "UNRESOLVED.json")["unresolved"]


def shoelace(poly):
    return abs(sum(poly[i - 1][0] * poly[i][1] - poly[i][0] * poly[i - 1][1] for i in range(len(poly)))) / 2


def diff(a_out, b_out, tol=1e-6):
    """{(item_code, room): (V_a, V_b)} for every total that differs."""
    a, b = totals(a_out), totals(b_out)
    return {k: (a.get(k), b.get(k)) for k in set(a) | set(b)
            if a.get(k, (0, 0))[1] != b.get(k, (0, 0))[1] or abs(a.get(k, (0, 0))[0] - b.get(k, (0, 0))[0]) > tol}


def invariant(a_out, b_out, tol=1e-5):
    return not diff(a_out, b_out, tol)
