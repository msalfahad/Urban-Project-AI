"""T-214 (development villa): the floor build-up FFL -> structural top per floor and zone, drawing-derived beside the
owner manual method, and its consequence for the merged level chain (LEVEL_CHAIN_V1, evidence set R2 of T-206).

Inputs (committed, read only): ALSENAN_BUILDUP_INPUT.json (this run's readings: metres measured on the architect's
sections, Drive file titles and views only; produced with section_bands.py on the private DWF and the 400 dpi band
profiles of the two current-issue scans), research/agents_t206/ALSENAN_LEVEL_INPUT_R2.json (T-206, untouched).
Evidence set R3 = R2 + one DRAWING layer FLOOR_BUILD_UP per chain whose zone this run established (dry floors only).
No BOQ quantity, released method, candidate or rule version changes.

Run from the repository root:
    python3 -I research/agents_t214/t214_alsenan_check.py            # prints the summary
    python3 -I research/agents_t214/t214_alsenan_check.py --write    # writes summary.json
    python3 -I research/agents_t214/t214_alsenan_check.py --check    # rebuilds and compares with summary.json
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE))

from engine.source import level_chain_v1 as LC  # noqa: E402
import floor_buildup_v1 as FB  # noqa: E402

R2 = ROOT / "research" / "agents_t206" / "ALSENAN_LEVEL_INPUT_R2.json"
INPUT = HERE / "ALSENAN_BUILDUP_INPUT.json"
OUT = HERE / "summary.json"
# level-chain chain id -> (floor id, zone id) of this run's result; only DRY zones are carried (ERS s.3)
CHAIN_ZONE = {"GF-FLOOR": ("GF", "GF-DRY"), "GF-EXT-F8": ("GF", "GF-DRY"), "ANNEX-FLOOR": ("ANNEX", "ANNEX-DRY"),
              "1F-FLOOR": ("1F", "1F-DRY"), "2F-FLOOR": ("2F", "2F-DRY")}
PLOT_RESOLUTION_M = 0.002   # DWF logical unit about 2.1 mm of drawing (T-201): readings 0.049 / 0.050 are one value


def _pick(res, keys):
    return {k: res[k] for k in keys if k in res}


def build():
    inp = json.loads(INPUT.read_text(encoding="utf-8"))
    fb = FB.evaluate(inp)
    r2 = json.loads(R2.read_text(encoding="utf-8"))
    r3 = copy.deepcopy(r2)
    added = []
    for cid, (fid, zid) in CHAIN_ZONE.items():
        z = fb["floors"][fid]["zones"][zid]["drawing"]
        if z["b"] is None:
            continue
        r3["layers"].append({"chain_id": cid, "layer": "FLOOR_BUILD_UP", "thickness": z["b"],
                             "status": z["status"], "method": "DRAWING",
                             "ref": f"T-214 {zid}: {z['basis']}"})
        added.append({"chain_id": cid, "b": z["b"], "status": z["status"]})
    lc2, lc3 = LC.check(r2), LC.check(r3)

    def datums(res, kinds):
        return {f"{d['chain_id']}/{d['kind']}": [d["value"], d["status"]] for d in res["datums"]
                if d["kind"] in kinds}
    kinds = ("SLAB_TOP", "SLAB_SOFFIT", "BEAM_BOTTOM", "GB_TOP", "GB_BOTTOM")
    d2, d3 = datums(lc2, kinds), datums(lc3, kinds)
    changed = {k: {"R2": d2.get(k), "R3": v} for k, v in sorted(d3.items()) if d2.get(k) != v}
    uses = {}
    for u2, u3 in zip(lc2["uses"], lc3["uses"]):
        if (u2["code"], u2["detail"], u2["sensitivity"]) != (u3["code"], u3["detail"], u3["sensitivity"]):
            uses[u3["use_id"]] = {"R2": _pick(u2, ("code", "detail", "sensitivity")),
                                  "R3": _pick(u3, ("code", "detail", "sensitivity"))}
    zones = []
    for fid, f in fb["floors"].items():
        for zid, z in f["zones"].items():
            om = [{"rule": o["rule"], "scope": o["scope"], "range_m": [o["lo"], o["hi"]], "partial": o["partial"],
                   "usable_as_datum": o["usable_as_datum"],
                   "residual_drawn_minus_owner_m": o.get("residual_drawn_minus_owner"),
                   "residual_named": o.get("residual_named")} for o in z["owner_manual"]]
            zones.append({"floor": fid, "zone": zid, "type": z["type"], "ffl": f["ffl"],
                          "drawing_b_m": z["drawing"]["b"], "drawing_status": z["drawing"]["status"],
                          "drawing_basis": z["drawing"]["basis"], "slab_top_drawing": z.get("slab_top_drawing"),
                          "drawing_notes": [n.split(" (Drive")[0] for n in z["drawing"].get("notes", [])],
                          "owner_manual": om})
    return {"task": "T-214", "method": FB.METHOD, "plot_resolution_m": PLOT_RESOLUTION_M, "zones": zones,
            "conditions": fb["conditions"], "level_chain": {
                "evidence_set": "R3 = T-206 R2 + FLOOR_BUILD_UP drawing layers below", "layers_added": added,
                "R2_summary": lc2["summary"], "R3_summary": lc3["summary"],
                "datums_changed": changed, "uses_changed": uses}}


def main(argv):
    res = build()
    text = json.dumps(res, indent=1, ensure_ascii=False, sort_keys=True) + "\n"
    if "--check" in argv:
        same = OUT.read_text(encoding="utf-8") == text
        print("summary.json reproduces: " + ("YES" if same else "NO"))
        return 0 if same else 1
    if "--write" in argv:
        OUT.write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
