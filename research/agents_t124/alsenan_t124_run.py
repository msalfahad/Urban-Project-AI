"""T-124 read-only audit run: every area ARCH_TAKEOFF_V2.13 hands to MEMBRANE_FOLD_V3 (wet areas, roofs) on an
architectural DXF (the development villa's Drive copy, P7757_DXF_COMPRESSED.zip), every owner Q-58 A count checked:
    V3   the four longest-wall layouts (V2.12 / V2.13 count from these): MEMBRANE_FOLD_V5.audit_v3 per layout
    V4   every wall frame (T-104): the same audit per layout
    V5   the count on one set of rolls per layout, the Q-49 A choice and its ledger (installed, upturn, gross cut, laps,
         trims, offcut left, rolls) and the full cutting plan of the chosen layout (roll, piece, position)
Engine room ids, lengths, areas and counts only; nothing is written into the repository.

    python3 -I research/agents_t124/alsenan_t124_run.py <P7757.dxf> --out <scratch>/t124.json \
        [--zone-floor GF --zone-code PANTRY --zone-length 4.50 --zone-width 3.00 --zone-sheet "ground floor plan"]

Project inputs as T-096 / T-120: research/agents_t010/sanitary_reading.json and research/agents_t071/alsenan_facts.json.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

PID = "development-villa-t124"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("drawing")
    ap.add_argument("--out", required=True)
    ap.add_argument("--zone-floor", default="GF")
    ap.add_argument("--zone-code", default="PANTRY")
    ap.add_argument("--zone-length", type=float)
    ap.add_argument("--zone-width", type=float)
    ap.add_argument("--zone-sheet", default="ground floor plan")
    a = ap.parse_args(argv)
    from engine.source import arch_measure as AM
    from engine.source import membrane_fold_v3 as F3
    from engine.source import membrane_fold_v5 as F5
    from tools import urban_boq_m9 as M
    facts = {"schema": AM.FACTS_SCHEMA,
             "sanitary_by_room": json.loads((ROOT / "research/agents_t010/sanitary_reading.json").read_text(
                 encoding="utf-8"))["items"],
             "exterior_spaces": json.loads((ROOT / "research/agents_t071/alsenan_facts.json").read_text(
                 encoding="utf-8"))}
    if a.zone_length is not None:
        facts["project_data"] = {"schema": "URBAN_PROJECT_DATA_FILE_V1", "project": PID, "records": [{
            "key": f"WET_ZONE_SIZE_{a.zone_floor}_{a.zone_code}", "project": PID, "kind": "table", "unit": "none",
            "value": {"length_m": a.zone_length, "width_m": a.zone_width}, "status": "DRAWING-VERIFIED",
            "drawing_file": Path(a.drawing).name, "drawing_number": "architectural set",
            "revision": "no revision printed", "sheet": a.zone_sheet,
            "reference": f"printed {a.zone_length:.2f} x {a.zone_width:.2f} m at the {a.zone_code} label",
            "applies_to": {"floors": [a.zone_floor], "members": [a.zone_code]},
            "reviewer_or_source": "hand reading (T-114 read the same printed size)", "entered_by": "TYPED"}]}
    seen, real_area, real_fold = [], F3.area, F3.fold

    def spy_area(**kw):
        r = real_area(**kw)
        seen.append(("area", kw))
        return r

    def spy_fold(polygon, *, holes=(), unit_m=1.0, spec=None):
        r = real_fold(polygon, holes=holes, unit_m=unit_m, spec=spec)
        seen.append(("fold", {"polygon": polygon, "holes": holes, "unit_m": unit_m, "spec": spec}))
        return r
    F3.area, F3.fold = spy_area, spy_fold
    try:
        M.arch_compute(a.drawing, method="ARCH_TAKEOFF_V2.13", facts=facts, project_id=PID)
    finally:
        F3.area, F3.fold = real_area, real_fold
    # one entry per outline folded (area() folds through fold(); keep the area() call, then any fold() of its own)
    def _k(kw):
        return (repr(kw["polygon"]), repr(tuple(kw.get("holes") or ())), kw.get("unit_m", 1.0))
    named = {_k(kw) for kind, kw in seen if kind == "area"}
    areas, keys = [], set()
    for kind, kw in seen:
        key = _k(kw)
        if key in keys or (kind == "fold" and key in named):
            continue
        keys.add(key)
        areas.append((kind, kw))
    rows = []
    for kind, kw in areas:
        spec = kw.get("spec")
        try:
            f = F5.fold(kw["polygon"], holes=kw.get("holes") or (), unit_m=kw.get("unit_m", 1.0), spec=spec)
        except F5.FoldError as ex:
            rows.append({"floor": kw.get("floor"), "room_id": kw.get("room_id"), "state": "HELD", "reason": str(ex)})
            continue
        sp = f["spec"]
        v3 = [dict(layout=f"{x['direction']} / {x['start']}", claimed=x["rolls_by_basis"],
                   **{k: v for k, v in F5.audit_v3(x, sp).items() if k in ("verdict", "why", "corrected", "v5_rolls",
                                                                          "own_offcut_pieces")})
              for x in f["layouts_v3"]]
        v4 = [{"layout": y["name"], "v4": y["rolls_v4"], "v5": y["rolls_v5"], "verdict": y["audit_v3_a"]["verdict"],
               "why": y["audit_v3_a"]["why"], "own_offcut_pieces": y["audit_v3_a"]["own_offcut_pieces"],
               "ledger": y["ledger"]} for y in f["layouts_v5"]]
        ch = f["choice_v5"]
        sel = f["layouts_v5"][ch["q58_a"]["layout"]]
        rows.append({"via": kind, "floor": kw.get("floor"), "room_id": kw.get("room_id"), "name": kw.get("name"),
                     "floor_m2": f["floor_m2"], "v3_layouts": v3, "v4_v5_layouts": v4,
                     "v3_min_a": min(x["claimed"]["Q58_A"] for x in v3),
                     "v4_choice": {b: x["rolls"] for b, x in f["choice_v4"]["by_reading"].items()},
                     "v5_choice": {"state": ch["state"], "by_reading": {b: x["rolls"] for b, x in
                                                                         ch["by_reading"].items()},
                                   "layout": ch["q58_a"]["name"], "ledger": ch["q58_a"]["ledger"],
                                   "lower_bound": sel["plan_q58_a"]["lower_bound"],
                                   "pieces_from_rolls": len(sel["plan_q58_a"]["pieces_from_rolls"]),
                                   "pieces_from_own_offcuts": sel["plan_q58_a"]["pieces_from_own_offcuts"],
                                   "offcuts_left": sel["plan_q58_a"]["offcuts_left"],
                                   "plan": sel["plan_q58_a"]["plan"]},
                     "flags_v5": f["flags_v5"]})
    Path(a.out).write_text(json.dumps(rows, indent=1, ensure_ascii=False, default=str), encoding="utf-8")
    for r in rows:
        if "v3_layouts" not in r:
            print(r)
            continue
        bad3 = [(x["layout"], x["verdict"], x["claimed"]["Q58_A"], x["corrected"]) for x in r["v3_layouts"]
                if x["verdict"] != "VALID"]
        bad4 = [(x["layout"], x["verdict"], x["v4"]["Q58_A"], x["v5"]["Q58_A"]) for x in r["v4_v5_layouts"]
                if x["verdict"] != "VALID"]
        own = len(r["v5_choice"]["pieces_from_own_offcuts"])
        print(f"{r['floor']} {r['room_id']} {r['floor_m2']} m2 | V3 min A {r['v3_min_a']} | V4 {r['v4_choice']} | "
              f"V5 {r['v5_choice']['state']} {r['v5_choice']['by_reading']} own-offcut pieces {own} | "
              f"V3 not valid {bad3} | V4 not valid {bad4}\n    ledger {r['v5_choice']['ledger']}")


if __name__ == "__main__":
    main()
