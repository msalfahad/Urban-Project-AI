"""T-116 Alsenan run of STAIR_FLOOR_RESIDUE_V1 on every ARCH_TAKEOFF_V2.9 room face with a floor-finish line.

Usage (Python 3.11; the drawing stays outside the clone):
    python3 -I research/agents_t116/alsenan_stair_floor_residue.py --v29 <scratch>/v29.pkl --out <scratch>/t116
    (the pickle is (boq, arch, extra) of tools.urban_boq_m9.arch_compute(<P7757.dxf>, method="ARCH_TAKEOFF_V2.9"))
The outlined void windows of a plan are those the engine carried down to the plan below (run.double_height, state
APPLIED), moved back by the recorded column-grid offset, the same reading as T-113. Writes only to --out; areas and
counts only, no CAD coordinates."""

from __future__ import annotations

import argparse
import json
import pickle
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import stair_floor_residue as SFR  # noqa: E402

FLOOR_ITEMS = ("FIN.FLOOR.PORCELAIN", "FIN.FLOOR.WET_TILE")


def run(boq, arch, extra):
    u = arch["run"]["unit_m"]
    voids_by_floor = {}
    for v in arch["run"].get("double_height") or ():
        if v.get("state") != "APPLIED":
            continue
        dx, dy = v["offset"]["dx"], v["offset"]["dy"]
        voids_by_floor.setdefault(v["floor"], []).append(
            {"void_id": v["void_id"], "corners": [(x - dx, y - dy) for x, y in v["window"]]})
    lines = {}
    for ln in boq["lines"]:
        if ln["item_code"] in FLOOR_ITEMS:
            lines[ln["location"].get("room_id")] = ln
    doors = {}
    for o in arch["openings"]:
        c = (o.get("position") or {}).get("centre_m")
        if c:
            for r in o.get("rooms") or ():
                doors.setdefault(r, []).append((c[0] / u, c[1] / u))
    rows = []
    for room in arch["rooms"]:
        ln = lines.get(room["room_id"])
        if ln is None:
            continue
        rec = SFR.face_residue(room, voids=voids_by_floor.get(room["floor"], ()), segments=extra["segments"],
                               arcs=extra["arcs"], unit_m=u, floor_points=doors.get(room["room_id"], ()))
        eng = ln.get("measured_net")
        rows.append({"room_id": room["room_id"], "floor": room["floor"], "item": ln["item_code"],
                     "engine_net_m2": eng, "scope": rec["scope"], "status": rec["status"],
                     "residue_low_m2": rec.get("floor_net_low_m2"), "residue_high_m2": rec.get("floor_net_high_m2"),
                     "change_low_m2": None if eng is None or rec.get("floor_net_low_m2") is None else
                     round(rec["floor_net_low_m2"] - eng, 4), "record": rec})
    return rows


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--v29", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    boq, arch, extra = pickle.load(open(a.v29, "rb"))
    rows = run(boq, arch, extra)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "stair_floor_residue_alsenan.json").write_text(json.dumps(rows, indent=1, default=str), encoding="utf-8")
    for r in rows:
        print(r["room_id"], r["item"], r["engine_net_m2"], r["scope"], r["status"], r["residue_low_m2"],
              r["residue_high_m2"], r["change_low_m2"])


if __name__ == "__main__":
    main()
