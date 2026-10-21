"""V1 vs V2 on the same drawing: V1 lines must appear unchanged in V2; geometry (rooms, openings, columns, plates,
floor categories) must be equal; list what V2 adds. usage: python3 -I v1_v2_compare.py V1_OUT V2_OUT [JSON_OUT]"""
import json, sys
from collections import Counter
a, b = sys.argv[1], sys.argv[2]
def J(d, f):
    x = json.load(open(f"{d}/{f}"))
    return x
L1 = J(a, "BOQ_LINES.json"); L1 = L1["lines"] if isinstance(L1, dict) else L1
L2 = J(b, "BOQ_LINES.json"); L2 = L2["lines"] if isinstance(L2, dict) else L2
by2 = {l["line_id"]: l for l in L2}
missing = [l["line_id"] for l in L1 if l["line_id"] not in by2]
changed = [l["line_id"] for l in L1 if l["line_id"] in by2 and json.dumps(l, sort_keys=True) != json.dumps(by2[l["line_id"]], sort_keys=True)]
ids1 = {l["line_id"] for l in L1}
added = [l for l in L2 if l["line_id"] not in ids1]
def rooms(d):
    return sorted((r["floor"], r["room_id"], r["class"], "+".join(r.get("codes") or []), round(r["area_m2"], 6), round(r["gross_m2"] or 0, 6))
                  for r in J(d, "ARCH_ROOMS.json")["rooms"])
def ops(d):
    O = J(d, "ARCH_OPENINGS.json"); O = O["openings"] if isinstance(O, dict) else O
    return sorted((o["floor"], o["opening_id"], o["kind"], round(o["width_m"], 6)) for o in O)
def plan(d):
    return sorted((r["floor"], r.get("columns"), json.dumps(r.get("plate"), sort_keys=True), r.get("stage_state")) for r in J(d, "ARCH_PLAN.json")["regions"])
def cats(d):
    return sorted((f["floor"], json.dumps(f["categories_m2"], sort_keys=True), f["gross_floor_plate_m2"]) for f in J(d, "ARCH_FLOOR_AREAS.json")["floors"])
res = {"v1_lines": len(L1), "v2_lines": len(L2), "v1_lines_missing_in_v2": missing, "v1_lines_changed_in_v2": changed,
       "added_by_item": dict(Counter(l["item_code"] + ":" + l["evidence_state"] for l in added)),
       "added_with_quantity": [l["line_id"] for l in added if l.get("measured_net") is not None],
       "rooms_equal": rooms(a) == rooms(b), "openings_equal": ops(a) == ops(b), "plan_equal": plan(a) == plan(b),
       "floor_categories_equal": cats(a) == cats(b)}
print(json.dumps(res, indent=1))
if len(sys.argv) > 3:
    json.dump(res, open(sys.argv[3], "w"), indent=1)
