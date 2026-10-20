"""T-089 read-only Alsenan run: MEMBRANE_CUTTING_PLAN_V1 on every wet area (the 17 spaces WET_ROOM_EVIDENCE_V1 classes
WET on ARCH_TAKEOFF_V2.9, as the T-076 run), the pantry from its printed size (owner Q-37 A, 4.50 x 3.00) and the
roofs that EXTERIOR_SPACES_V1 releases (outlines dumped by research/agents_t076/alsenan_roof_fold.py), each alone
(owner Q-49 A). Nothing is written into the repository: the JSON, the text tables and the SVGs go to --out-dir (a
scratch folder). Output: areas, lengths, counts and engine room ids only.
    python3 -I research/agents_t089/alsenan_cutting_run.py --v29 <pickle> --t010 <t010 json>
        --roofs <roof outlines json> --out-dir <scratch>/t089
the pickle: tools/urban_boq_m9.arch_compute(<P7757.dxf>, method="ARCH_TAKEOFF_V2.9"); the T-010 json:
research/agents_t010/alsenan_wet_run.py; the roof outlines: alsenan_roof_fold.py --dump-outlines."""

from __future__ import annotations

import argparse
import json
import pickle
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

PANTRY = {"floor": "GF", "room_id": "GF-PANTRY-PRINTED", "name": "PANTRY (printed 4.50 x 3.00, Q-37 A)",
          "x_m": 4.50, "y_m": 3.00}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--v29", required=True)
    ap.add_argument("--t010", required=True)
    ap.add_argument("--roofs", required=True)
    ap.add_argument("--out-dir", required=True)
    a = ap.parse_args(argv)
    from engine.source import membrane_cutting_plan as C
    _, arch, _ = pickle.load(open(a.v29, "rb"))
    t010 = json.loads(Path(a.t010).read_text(encoding="utf-8"))["rows"]
    wet = {(r["floor"], r["room_id"]) for r in t010 if r["t010_class"] == "WET"}
    areas = []
    for r in arch["rooms"]:
        if (r["floor"], r["room_id"]) not in wet:
            continue
        areas.append(C.plan(r["polygon_m"], holes=r.get("hole_polygons_m") or (), floor=r["floor"],
                            room_id=r["room_id"], name="/".join(r["codes"]) or "(no label)", group="WET_AREA"))
    p = PANTRY
    areas.append(C.plan([(0, 0), (p["x_m"], 0), (p["x_m"], p["y_m"]), (0, p["y_m"])], floor=p["floor"],
                        room_id=p["room_id"], name=p["name"], group="PANTRY"))
    for i, o in enumerate(json.loads(Path(a.roofs).read_text(encoding="utf-8"))):
        areas.append(C.plan(o["outer"], holes=o["holes"], floor=o["region"], room_id=f"ROOF-{i + 1}",
                            name=f"ROOF {o['region']}", group="ROOF"))
    # the top roof of the second-floor block is drawn on no plan sheet (owner Q-34 parked): held, never 0
    areas.append(C.held(floor="2F top roof", room_id="ROOF-TOP", name="ROOF above the 2F block (no plan drawn)",
                        group="ROOF", reason="OUTLINE_NOT_DRAWN_ON_ANY_PLAN (owner Q-34 held)"))
    proj = C.project(areas)
    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "cutting_plans.json").write_text(json.dumps({"areas": [C.public(x) for x in areas], "project": proj},
                                                       indent=1, ensure_ascii=False, default=str), encoding="utf-8")
    (out / "cutting_plans.txt").write_text("\n".join(C.text_table(x) for x in areas), encoding="utf-8")
    for x in areas:
        (out / f"{x['floor'].replace(':', '_')}_{x['room_id']}.svg").write_text(C.svg(x), encoding="utf-8")
    for x in areas:
        print(x["group"], x["floor"], x["room_id"], x["name"], x.get("floor_m2"), x["rolls_to_buy"], x.get("reason"),
              x["strip_metres"], x["leftover_m"], x["cut_m2"], x["side_trim_m2"],
              (x.get("selected") or {}).get("direction"), (x.get("selected") or {}).get("start"),
              (x.get("selected") or {}).get("proof_state"), x.get("flags"))
    print(json.dumps({g: {k: v for k, v in t.items() if k != "held_rows"} for g, t in proj["groups"].items()},
                     indent=1))


if __name__ == "__main__":
    main()
