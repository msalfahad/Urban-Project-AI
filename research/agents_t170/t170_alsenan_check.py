"""T-170 on the development villa: the excavation / backfill ledger from ALSENAN_EXCAVATION_INPUT.json (values,
Drive titles, DXF handles and coordinates only; read from 'ST7757 dxf.dxf' and 'ST7757.pdf' this run).
Run: python3 -I research/agents_t170/t170_alsenan_check.py [--write]  -> summary.json, LEDGER_T170.csv"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import excavation_ledger_v1 as X  # noqa: E402

INPUT = HERE / "ALSENAN_EXCAVATION_INPUT.json"


def load():
    doc = json.loads(INPUT.read_text(encoding="utf-8"))
    u = doc["units"]
    fts = []
    for f in doc["footings"]:
        s = f.get("schedule_L_W_H_m")
        fts.append({"id": f["id"], "type": f["type"], "outline": f["outline"], "detail": f["detail"],
                    "conflict": f.get("conflict"),
                    "L_m": s[0] if s else None, "W_m": s[1] if s else None, "H_m": s[2] if s else None,
                    "x0_m": X.to_m(f["x0_mm"], u["x0_mm"]), "y0_m": X.to_m(f["y0_mm"], u["y0_mm"]),
                    "dx_m": X.to_m(f["dx_mm"], u["dx_mm"]), "dy_m": X.to_m(f["dy_mm"], u["dy_mm"])})
    beams = []
    for b in doc["beams"]:
        why = None
        if b["depth_m"] is None:
            why = ("exterior-wall beam: depth 'FOLLOW ARCH.' (p.13), underside 'Outer Normal ground level' (a name)"
                   if b.get("arch_class") == "EXTERIOR_WALL" else
                   "interior beam: p.13 class by span (0.60 over 5 m, 0.40 under 5 m, 0.30 under 2.5 m); the span of "
                   "the whole beam this piece belongs to is not in the input")
        beams.append({"id": b["id"], "kind": "STRAP" if b["detail"] == "STRAP" else "TRENCH", "mark": b.get("mark"),
                      "detail": b["detail"], "width_m": b["width_m"], "length_m": b["length_m"],
                      "depth_m": b["depth_m"], "depth_why": why, "top": None})
    lv = doc["levels"]
    levels = {"details": doc["details"], "existing_ground": lv["existing_ground"], "formation": lv["formation"],
              "working_space_m": lv["working_space_m"]}
    return doc, fts, beams, levels


def run():
    doc, fts, beams, levels = load()
    led = X.ledger(fts, beams, levels)
    pits = led["pits"]
    ok = [p for p in pits if p["neat_status"] == X.DRAWING_CONFIRMED]
    res = {
        "method": X.METHOD_ID,
        "footings": len(fts), "beams": len(beams),
        "neat_pits_confirmed": len(ok),
        "neat_pit_plan_m2": round(sum(p["neat_plan_m2"] for p in ok), 6),
        "footprint_m2_confirmed_pits": round(sum(p["footprint_m2"] for p in ok), 6),
        "held_pits": {p["id"]: p["held"] for p in pits if p["neat_status"] != X.DRAWING_CONFIRMED},
        "buried_confirmed_m3": {k: round(sum(p["buried"][k] for p in ok if p["buried"][k] is not None), 6)
                                for k in ("blinding_m3", "underlay_m3", "footing_m3")},
        "trench_neat_plan_m2": round(sum(t["neat_plan_m2"] for t in led["trenches"]
                                         if t["neat_status"] == X.DRAWING_CONFIRMED), 6),
        "trenches_confirmed": sum(1 for t in led["trenches"] if t["neat_status"] == X.DRAWING_CONFIRMED),
        "straps_footprint_m2": round(sum(b["width_m"] * b["length_m"] for b in beams if b["kind"] == "STRAP"), 6),
        "overlaps": led["overlaps"],
        "excavation_m3": led["totals"]["excavation_m3"], "backfill_m3": led["totals"]["backfill_m3"],
        "per_type_chain": {},
        "pits": pits, "trenches": led["trenches"],
    }
    for p in pits:
        res["per_type_chain"].setdefault(p["type"], p["above_formation_m"])
    return res


def write(res):
    (HERE / "summary.json").write_text(json.dumps({k: v for k, v in res.items()}, indent=1) + "\n", encoding="utf-8")
    with open(HERE / "LEDGER_T170.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["id", "kind", "type_or_mark", "footprint_m2", "neat_plan_m2", "neat_status",
                    "blinding_top_above_F", "footing_bottom_above_F", "footing_top_above_F",
                    "depth_m", "excavation_m3", "excavation_status", "why", "blinding_m3", "underlay_m3",
                    "footing_m3", "backfill_status"])
        for p in res["pits"]:
            a = p["above_formation_m"]
            w.writerow([p["id"], "PIT", p["type"], p["footprint_m2"], p["neat_plan_m2"], p["neat_status"],
                        a["blinding_top"], a["footing_bottom"], a["footing_top"], p["depth_m"] or "",
                        p["excavation_m3"] or "", p["excavation_status"], p["excavation_why"],
                        p["buried"]["blinding_m3"], p["buried"]["underlay_m3"], p["buried"]["footing_m3"],
                        p["backfill_status"]])
        for t in res["trenches"]:
            w.writerow([t["id"], t["kind"], t["mark"] or "", round(t["width_m"] * t["length_m"], 6),
                        t["neat_plan_m2"], t["neat_status"], "", "", "", t["depth_m"] or "", t["excavation_m3"] or "",
                        t["excavation_status"], t["excavation_why"], "", "", "", "HELD"])


if __name__ == "__main__":
    r = run()
    if "--write" in sys.argv:
        write(r)
    print(json.dumps({k: r[k] for k in ("footings", "beams", "neat_pits_confirmed", "neat_pit_plan_m2",
                                         "footprint_m2_confirmed_pits", "held_pits", "buried_confirmed_m3",
                                         "trench_neat_plan_m2", "trenches_confirmed", "straps_footprint_m2",
                                         "excavation_m3", "backfill_m3", "per_type_chain")}, indent=1))
    print("overlaps", json.dumps(r["overlaps"], indent=0))
