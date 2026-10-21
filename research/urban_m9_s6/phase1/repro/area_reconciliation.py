"""S6 Phase 1 area reconciliation of one drawing: V1 vs V2 per floor - the face partition (every face part -> LINE /
RFI / EXCLUDED), the floor categories (equal in V1 and V2), the doorway strips by class and by verification, and the
V1 lines kept. usage: python3 -I area_reconciliation.py V1_OUT V2_OUT OUT_JSON"""
import json, sys
from collections import defaultdict
from pathlib import Path

a, b, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
J = lambda d, n: json.loads((d / n).read_text())                                   # noqa: E731
FA1 = {f["floor"]: f for f in J(a, "ARCH_FLOOR_AREAS.json")["floors"]}
FA2 = {f["floor"]: f for f in J(b, "ARCH_FLOOR_AREAS.json")["floors"]}
COV = {f["floor"]: f for f in J(b, "FINISH_COVERAGE.json")["floors"]}
res = {"floors": {}}
for fl, f2 in FA2.items():
    f1 = FA1[fl]
    c = COV[fl]
    pr = c["physical_regions"]
    st = defaultdict(lambda: {"count": 0, "m2": 0.0})
    for s in f2.get("strips") or ():
        k = s["class"] + (":VERIFIED" if s["geometry_verified"] else ":UNVERIFIED")
        st[k]["count"] += 1
        st[k]["m2"] = round(st[k]["m2"] + s["area_m2"], 6)
    by_state = defaultdict(float)
    for r in pr["faces"]:
        by_state[r["state"]] += r["m2"]
    res["floors"][fl] = {
        "categories_equal_v1_v2": f1["categories_m2"] == f2["categories_m2"],
        "gross_floor_plate_m2": f2["gross_floor_plate_m2"], "internal_physical_floor_m2": f2["internal_physical_floor_m2"],
        "external_m2": f2["external_m2"], "categories_m2": f2["categories_m2"],
        "faces_m2": pr["faces_m2"], "covered_m2": pr["covered_m2"], "faces_by_state_m2": {k: round(v, 4) for k, v in sorted(by_state.items())},
        "by_category_and_state_m2": pr["by_category"], "coverage_gate": c["gate"], "unaccounted": len(c["unaccounted"]),
        "doorway_strips_m2": f2["categories_m2"].get("DOORWAY_STRIPS"), "doorway_strips_by_class_m2": f2.get("doorway_strips_by_class_m2"),
        "strips_by_class_and_verification": dict(sorted(st.items())),
        "functional_spaces": len(c["functional_spaces"]),
        "functional_surfaces_by_state": dict(sorted(((s, n) for s, n in __import__("collections").Counter(
            x["state"] for sp in c["functional_spaces"] for x in sp["surfaces"].values()).items()))),
    }
L1 = J(a, "BOQ_LINES.json"); L1 = L1["lines"] if isinstance(L1, dict) else L1
L2 = J(b, "BOQ_LINES.json"); L2 = L2["lines"] if isinstance(L2, dict) else L2
by2 = {x["line_id"]: x for x in L2}
res["lines"] = {"v1": len(L1), "v2": len(L2),
                "v1_kept_unchanged": sum(1 for x in L1 if json.dumps(by2.get(x["line_id"]), sort_keys=True) == json.dumps(x, sort_keys=True)),
                "v2_added": len(L2) - len(L1),
                "v2_added_with_a_quantity": sum(1 for x in L2 if x["line_id"] not in {y["line_id"] for y in L1} and x.get("measured_net") is not None)}
out.write_text(json.dumps(res, indent=1, ensure_ascii=True))
for fl, x in res["floors"].items():
    print(fl, x["coverage_gate"], "faces", x["faces_m2"], "covered", x["covered_m2"], "strips", x["doorway_strips_m2"], x["strips_by_class_and_verification"])
print(res["lines"])
