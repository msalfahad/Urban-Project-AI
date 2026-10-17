"""S6 floor-finish coverage census (read-only prototype of the proposed CATEGORY_TRUTH gate).

usage: python3 -I floor_finish_census.py OUT_DIR [JSON_OUT]
For every floor, every physical area category of ARCH_FLOOR_AREAS.json gets ONE disposition:
    FINISH_LINE        floor finish lines carry it (by evidence state)
    BOUNDED_OR_BLOCKED a line exists with no quantity (BOUNDED_EXPOSURE / BLOCKED_RFI) or a space line + RFI
    NOT_APPLICABLE     no floor finish by definition (wall mass, shaft, void, the stair below seen)
    UNACCOUNTED        no line and no RFI: a silent gap (the gate fails when this is > 0)
"""
import json, sys
from collections import defaultdict

out = sys.argv[1]
FA = json.load(open(out + "/ARCH_FLOOR_AREAS.json"))["floors"]
L = json.load(open(out + "/BOQ_LINES.json"))
L = L["lines"] if isinstance(L, dict) else L
U = json.load(open(out + "/UNRESOLVED.json"))
U = U.get("unresolved", U) if isinstance(U, dict) else U

NA = {"WALL_AND_COLUMN_MASS": "walls and columns carry no floor finish",
      "SHAFT": "a shaft has no floor finish (ARCH.SPACE line records it)",
      "VOID": "open to below: no floor",
      "STAIR_BELOW_SEEN": "the flight of the plan below, counted there",
      "SLIVERS": "a sliver below the face threshold"}


def lines_of(floor, *prefixes):
    return [ln for ln in L if (ln.get("location") or {}).get("floor") == floor and ln["item_code"].startswith(prefixes)]


def m2(ls):
    return round(sum(ln["measured_net"] or 0 for ln in ls), 4)


res = {}
for f in FA:
    fl, cat = f["floor"], f["categories_m2"]
    rows = []
    fin = lines_of(fl, "FIN.FLOOR.")
    by_ev = defaultdict(float)
    for ln in fin:
        by_ev[ln["evidence_state"]] += ln["measured_net"] or 0
    room_open = cat.get("ROOM_FLOOR", 0) + cat.get("OPEN_PLAN_FLOOR", 0)
    rows.append({"category": "ROOM_FLOOR + OPEN_PLAN_FLOOR", "m2": round(room_open, 4), "disposition": "FINISH_LINE",
                 "lines_m2": m2(fin), "by_evidence_m2": {k: round(v, 4) for k, v in sorted(by_ev.items())},
                 "check": "BALANCED" if abs(m2(fin) - room_open) < 1e-3 else "MISMATCH"})
    un = sum(v for k, v in cat.items() if k.startswith("UNALLOCATED"))
    sp = [ln for ln in lines_of(fl, "ARCH.SPACE") if ln["evidence_state"] == "PROVISIONAL"]
    rfi = [u for u in U if u.get("floor") == fl and u.get("item") == "ARCH.SPACE"]
    rows.append({"category": "UNALLOCATED (merged + mixed + unlabelled)", "m2": round(un, 4),
                 "split_m2": {k: v for k, v in cat.items() if k.startswith("UNALLOCATED") and v},
                 "disposition": "BOUNDED_OR_BLOCKED" if un < 1e-6 or (sp and rfi) else "UNACCOUNTED",
                 "space_lines_m2": m2(sp), "rfis": len(rfi)})
    thr = lines_of(fl, "FIN.THRESHOLD", "FIN.MARBLE.THRESHOLD")
    ds = cat.get("DOORWAY_STRIPS", 0)
    rows.append({"category": "DOORWAY_STRIPS", "m2": round(ds, 4),
                 "disposition": "FINISH_LINE" if thr else ("NOT_APPLICABLE" if ds < 1e-6 else "UNACCOUNTED"),
                 "lines": len(thr), "note": "no threshold item exists in the architectural route; UP-CER-001 keeps a "
                                            "marble threshold out of the room floor, but no rule measures door thresholds"})
    tr = lines_of(fl, "FIN.MARBLE.TREAD")
    rows.append({"category": "STAIR_FLIGHTS", "m2": round(cat.get("STAIR_FLIGHTS", 0), 4),
                 "disposition": "FINISH_LINE" if tr or cat.get("STAIR_FLIGHTS", 0) < 1e-6 else "UNACCOUNTED",
                 "tread_lines_m2": m2(tr), "tread_states": sorted({ln["evidence_state"] for ln in tr})})
    la = lines_of(fl, "FIN.MARBLE.LANDING")
    lb = cat.get("STAIR_LANDINGS_BOUND", 0)
    rows.append({"category": "STAIR_LANDINGS_BOUND", "m2": round(lb, 4),
                 "disposition": ("BOUNDED_OR_BLOCKED" if la else "UNACCOUNTED") if lb > 1e-6 else "NOT_APPLICABLE",
                 "landing_lines": len(la), "landing_states": sorted({ln["evidence_state"] for ln in la})})
    ex = lines_of(fl, "ARCH.EXTERIOR")
    e = cat.get("EXTERNAL", 0)
    rows.append({"category": "EXTERNAL", "m2": round(e, 4),
                 "disposition": ("BOUNDED_OR_BLOCKED" if ex else "UNACCOUNTED") if e > 1e-6 else "NOT_APPLICABLE",
                 "note": "space recorded (ARCH.EXTERIOR); the exterior finish scope is an owner decision"})
    for k, why in NA.items():
        if cat.get(k):
            rows.append({"category": k, "m2": round(cat[k], 4), "disposition": "NOT_APPLICABLE", "why": why})
    total = round(sum(cat.values()), 4)
    disp = defaultdict(float)
    for r in rows:
        disp[r["disposition"]] += r["m2"]
    res[fl] = {"faces_m2": total, "rows": rows, "by_disposition_m2": {k: round(v, 4) for k, v in sorted(disp.items())},
               "covered_m2": round(sum(disp.values()), 4),
               "gate": "PASS" if disp.get("UNACCOUNTED", 0) < 1e-6 and abs(sum(disp.values()) - total) < 1e-3
               else "FAIL"}
print(json.dumps({k: {"faces_m2": v["faces_m2"], "by_disposition_m2": v["by_disposition_m2"], "gate": v["gate"]}
                  for k, v in res.items()}, indent=1))
if len(sys.argv) > 2:
    json.dump(res, open(sys.argv[2], "w"), indent=1)
