"""Phase 2B-8 test helpers: the architectural CLI under ARCH_TAKEOFF_V2.7.1 (and V2.7 / V2.6 for before / after), and
readers of its outputs. The heights are the synthetic S2 facts of tests/m9_p2b6/p2b6_run (stated test inputs)."""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "m9_p2b7"))

import p2b7_run as R7                                         # noqa: E402

V26, V27, V271 = R7.V26, R7.V27, "ARCH_TAKEOFF_V2.7.1"
FACTS = R7.FACTS
load, lines, rooms, totals, openings, unresolved, diff = R7.load, R7.lines, R7.rooms, R7.totals, R7.openings, \
    R7.unresolved, R7.diff


def run(dxf, out, *, roles=None, facts=False, method=V271):
    return R7.run(dxf, out, roles=roles, facts=facts, method=method)


def room_lines(out, room_id, prefix="FIN."):
    return [ln for ln in lines(out) if (ln.get("location") or {}).get("room_id") == room_id and
            (ln["item_code"].startswith(prefix) or ln["item_code"] == "ARCH.SPACE")]


def review_spaces(out):
    return load(out, "REVIEW_SPACES.json")["spaces"]


def release_report(out):
    return load(out, "BOQ_RELEASE_REPORT.json")


def door_reconciliation(out):
    return load(out, "DOOR_STANDARD_RECONCILIATION.json")["doors"]


def corrections(out):
    return load(out, "CORRECTIONS_V2_7.json")["corrections"]


def lobby(out, area=10.2):
    lob = [r for r in rooms(out) if abs(r["area_m2"] - area) < 1e-6]
    assert len(lob) == 1
    return lob[0]


def scenario_items(space, scenario, room_id=None):
    """{(item_code, element): quantity or (low, high) or None} of one scenario's conditional entries (optionally of
    one location)."""
    out = {}
    for c in space["conditional"][scenario]:
        if room_id is not None and c["room_id"] != room_id:
            continue
        q = c["quantity"] if c["quantity"] is not None else (
            (c["low"], c["high"]) if c.get("low") is not None else None)
        out[(c["item_code"], c["element"])] = q
    return out
