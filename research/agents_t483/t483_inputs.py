"""T-483: URBAN_V3048_INPUTS_V1 for the development villa: the Checker-verified T-481 census (merged a8609a7a;
Verifier 2026-11-03T05:44Z own re-measure AGREE on W17 / W11 / W02 / the 1F dressing) re-booked as the skirting
remainder of ARCH_TAKEOFF_V3.0.48. Nothing here is measured anew: every sill, edge, stretch, handle and opening id is
the merged T-481 table (research/agents_t481/t481_alsenan.py SILLS / LINES / DRESSING / SHAFT / L_LIVING). Line ids
and expected states are the candidate of record's (V3.0.47 e86a53a8; bound and checked at load: a stale id stops the
run).

    from t483_inputs import build; build(project_id)
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "agents_t481"))
import t481_alsenan as T481  # noqa: E402

SCHEMA = "URBAN_V3048_INPUTS_V1"
SOURCES = [
    {"task": "T-481", "file": "research/agents_t481/LINES_T481.csv",
     "sha256": "9be4c4070bec20643186fe2af0912611bbfc7983f687c3ee8c8c54005497833d", "merge_commit": "a8609a7a",
     "checker_run": "Verifier 2026-11-03T05:44Z Gate A PASS (own re-measure W17 NW elevation chain, W11 section B-B "
                    "scan 0.72 over +0.30, W02 floor glazing, 1F dressing 5.100 lm by handle: AGREE)"},
]
DRESSING_LINE = "L-4a85470b3a822d6fb7bb"   # FIN.SKIRTING 1F-RFFE7AF (SKIRT-T422), BLOCKED_RFI blank since V3.0.44
DRESSING_ROOM, DRESSING_FLOOR = "1F-RFFE7AF", "1F"


def _w(cid, edge, mode):
    views = T481.SILLS.get(cid)
    # the governing reading is the first view of the merged table (a section cut or a printed chain on printed level
    # markers); the other views agree on the decision (T-481 WINDOWS spread named there), never a pick by size
    sill = round(views[0][1], 3) if views else None
    return {"census_id": cid, "edge_lm": edge, "sill_m": sill, "status": "DRAWING-CONFIRMED",
            "why": f"T-481 READINGS / WINDOWS ({'; '.join(v[0] for v in views or ())})"[:300]}


def _walk_sides():
    sides = []
    for sd in T481.DRESSING:
        pos, sts = 0.0, []
        for st in sd["stretches"]:
            a, b = round(pos, 4), round(pos + st["length"], 4)
            x = {"s0": a, "s1": b, "kind": st["kind"]}
            if st["kind"] == "WALL":
                x["handles"] = st["ref"]
            else:
                x["opening_id"] = st["ref"]
            sts.append(x)
            pos = b
        sides.append({"id": sd["id"], "length": sd["length"], "stretches": sts})
    return sides


def build(project_id):
    L = T481.LINES
    w11 = L["W11+W12"]
    rel = [{"line_id": w11["line"], "expect": {"gross": w11["gross"], "measured_net": w11["net"]},
            "windows": [_w(c, e, "RELEASE") for c, e in sorted(w11["edges"].items())],
            "range_line": {"line_id": w11["range"], "expect": {"low": 0.0, "high": w11["range_hi"]}},
            "source_tasks": ["T-481"]}]
    clo = []
    for key in ("W02", "W17"):
        r = L[key]
        ws = []
        for c, e in sorted(r["edges"].items()):
            w = _w(c, e, "CLOSE")
            w["reason"] = "FLOOR_GLAZING"
            ws.append(w)
        clo.append({"line_id": r["range"], "expect": {"low": 0.0, "high": r["range_hi"]}, "windows": ws,
                    "source_tasks": ["T-481"]})
    # W13 / W25 (living range L-079bc766, 0 .. 2.200): R-T481-3 puts both inside stair side stretches, but B7-07 /
    # B7-08 have no candidate line (NOT_IN_CANDIDATE in BOQ_FAMILY_MASTER 1.44.0): closing the range now would drop
    # 2.200 lm from the BOQ. Kept HELD (WAITING T483_1F_SHAFT), with the 9.050 lm shaft faces.
    walk = [{"line_id": DRESSING_LINE, "room": DRESSING_ROOM, "floor": DRESSING_FLOOR,
             "expect": {"evidence_state": "BLOCKED_RFI"}, "gross_lm": 6.9, "evidence_status": "VERIFIED",
             "evidence_state": "SOURCE_DERIVED",
             "joinery_backed_lm": round(sum(j["length"] for j in T481.DRESSING_JOINERY), 4),
             "sides": _walk_sides(), "source_tasks": ["T-481"]}]
    return {"schema": SCHEMA, "project_id": project_id, "sources": SOURCES, "releases": rel, "closes": clo,
            "walks": walk}
