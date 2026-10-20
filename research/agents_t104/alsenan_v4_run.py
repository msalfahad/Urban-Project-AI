"""T-104 read-only Alsenan run: every wet area and roof that ARCH_TAKEOFF_V2.12 hands to MEMBRANE_FOLD_V3 is laid again
with MEMBRANE_FOLD_V4 (every wall frame of the area). Prints per area: the V3 choice (MEMBRANE_CUTTING_PLAN_V2, the
released V2.12 figures) and the V4 choice (rolls per owner Q-58 reading, strip metres, layout), and the sums. Engine room
ids, lengths and counts only; nothing is written into the repository.
    python3 -I research/agents_t104/alsenan_v4_run.py <P7757.dxf> --out <scratch>/t104_alsenan.json
Project inputs as T-096: research/agents_t010/sanitary_reading.json and research/agents_t071/alsenan_facts.json."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("drawing")
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    from engine.source import arch_measure as AM
    from engine.source import arch_v212 as AV
    from engine.source import membrane_cutting_plan_v2 as CP
    from engine.source import membrane_fold_v4 as F4
    from tools import urban_boq_m9 as M
    seen = []
    real = AV.F3.area

    def spy(**kw):                                        # record the outline each area is folded on
        r = real(**kw)
        seen.append((kw, r))
        return r
    AV.F3.area = spy
    facts = {"schema": AM.FACTS_SCHEMA,
             "sanitary_by_room": json.loads((ROOT / "research/agents_t010/sanitary_reading.json").read_text(
                 encoding="utf-8"))["items"],
             "exterior_spaces": json.loads((ROOT / "research/agents_t071/alsenan_facts.json").read_text(
                 encoding="utf-8"))}
    try:
        M.arch_compute(a.drawing, method="ARCH_TAKEOFF_V2.12", facts=facts)
    finally:
        AV.F3.area = real
    rows = []
    for kw, r in seen:
        if r["state"] != "COMPUTED":
            rows.append({"floor": kw["floor"], "room_id": kw["room_id"], "name": kw.get("name"), "state": r["state"]})
            continue
        p3 = CP.purchase(r["fold"])
        f4 = F4.fold(kw["polygon"], holes=kw.get("holes") or (), unit_m=kw.get("unit_m", 1.0))
        p4 = F4.purchase(f4)
        rows.append({"floor": kw["floor"], "room_id": kw["room_id"], "name": kw.get("name"),
                     "floor_m2": f4["floor_m2"], "frames": [x["frame_deg"] for x in f4["frames_v4"]],
                     "v3": {"state": p3["state"], "rolls": p3["rolls"], "bounded": p3["rolls_bounded"],
                            "by_reading": {b: x["rolls"] for b, x in p3["rolls_by_reading"].items()},
                            "strip_m": p3["strip_length_m"], "layout": f"{p3['direction']} / {p3['start']}",
                            "patch_m2": p3["patch_m2"]},
                     "v4": {"state": p4["state"], "rolls": p4["rolls"], "bounded": p4["rolls_bounded"],
                            "by_reading": {b: x["rolls"] for b, x in p4["rolls_by_reading"].items()},
                            "strip_m": p4["strip_length_m"], "layout": p4["layout"], "leftover_m": p4["leftover_m"],
                            "strips": [(s["width_m"], s["length_m"]) for s in
                                       f4["layouts_v4"][f4["choice_v4"]["layout"]]["strips"]],
                            "patches": [(q["shape"], q["m2"], q.get("sides_m")) for q in p4["patches"]],
                            "patch_m2": p4["patch_m2"], "flags": p4["flags"]}})
    Path(a.out).write_text(json.dumps(rows, indent=1, ensure_ascii=False, default=str), encoding="utf-8")
    for r in rows:
        if "v3" not in r:
            print(r)
            continue
        print(f"{r['floor']} {r['room_id']} {r['name']} {r['floor_m2']} m2 frames {r['frames']}\n"
              f"   V3 {r['v3']['by_reading']} {r['v3']['strip_m']} m {r['v3']['layout']}\n"
              f"   V4 {r['v4']['by_reading']} {r['v4']['strip_m']} m {r['v4']['layout']} {r['v4']['strips']}"
              f" patches {r['v4']['patches']}")


if __name__ == "__main__":
    main()
