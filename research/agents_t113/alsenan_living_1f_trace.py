"""T-113 read-only Alsenan trace: where the first-floor living face (ARCH_TAKEOFF_V2.9, room 1F-R78C367) gets the
5.95 m2 that the printed split (owner Q-56 A: living + corridor + landing + connector) does not have.

Method (independent of the engine's own area bookkeeping):
    1. the face polygon, the outlined void (run.double_height, shifted from the plan below) and every tread quad of the
       face are read from one V2.9 run;
    2. the face is cut into the six regions the printed dimension chains of the 1F plan define (local metres, origin at
       the face's south-west bounding-box corner): living 4.80 x 5.20, corridor 5.87 x 1.20, main-stair landing
       2.50 x 1.95, connector (1.30 x 1.25 + 2.37 x 1.20), the stair opening 5.87 x 4.00 (printed 587 / 400) and the
       dog-leg stair well 2.50 x 4.50 (printed 120 + 330 of the 645 chain);
    3. in each region: face, void, treads (shapely polygons, union, so a tread drawn twice is deducted once) and the
       residual the engine leaves as porcelain; each residual is split into named pieces;
    4. the engine's own tread deduction (arch_floor._treads: region_area_in_convex per quad) is recomputed quad by
       quad and compared with the exact polygon intersection.
Usage (Python 3.11; the drawing stays outside the clone):
    python3 -I research/agents_t113/alsenan_living_1f_trace.py --v29 <scratch>/v29.pkl --out <scratch>/t113
    (the pickle is (boq, arch, extra) of tools.urban_boq_m9.arch_compute(<P7757.dxf>, method="ARCH_TAKEOFF_V2.9"); or
    give the drawing with --drawing and the run is made here, about 55 s)
Writes only to --out. Areas and local coordinates (metres from the face corner) only; no CAD world coordinates."""

from __future__ import annotations

import argparse
import csv
import json
import pickle
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from shapely.geometry import Polygon, box  # noqa: E402
from shapely.ops import unary_union  # noqa: E402

ROOM = "1F-R78C367"

# regions in local metres (x east, y north from the face's south-west bounding-box corner); printed sources in brackets
REGIONS = {
    "LIVING": [(9.670, 0.000, 14.470, 5.200)],                        # 480 x 520
    "CORRIDOR": [(3.800, 4.000, 9.670, 5.200)],                       # 587 x 120
    "LANDING": [(0.000, 5.150, 2.500, 7.100)],                        # (120 + 10 + 120) x 195
    "CONNECTOR": [(2.500, 5.150, 3.800, 6.400), (3.800, 5.200, 6.170, 6.400)],   # 125 / 240 - 120; 20 + 347 chain
    "OPENING": [(3.800, 0.000, 9.670, 4.000)],                        # 587 x 400 (void + round stair)
    "STAIRWELL": [(0.000, 7.100, 2.500, 11.600)],                     # 120 + 330 of the 645 chain, 250 wide
}
SUBPIECES = {
    "LIVING": [
        ("quarter landing of the round stair inside the living rectangle", (9.670, 0.000, 10.820, 1.150)),
        ("arrival edge strip of the round stair (stair box 240 minus treads and landing)", (9.670, 2.350, 10.820, 2.400)),
    ],
    "OPENING": [
        ("void edge strip between the printed corridor edge (120) and the X-marked void", (3.800, 3.9505, 9.670, 4.000)),
        ("sliver between the X-marked void and the living line (east)", (9.6205, 1.2005, 9.670, 3.9505)),
        ("sliver between the wall and the X-marked void (west)", (3.800, 1.2005, 3.8005, 3.9505)),
        ("band between the X-marked void and the south wall, outside the treads (round-stair zone)", (3.800, 0.000, 9.670, 1.2005)),
    ],
    "STAIRWELL": [
        ("square at the top of the dog-leg, east of the winder (1.15 x 1.15)", (1.350, 10.450, 2.500, 11.600)),
        ("gap between the two flights (printed 10, drawn 0.20)", (1.150, 7.100, 1.350, 10.450)),
        ("foot of the east flight: last drawn tread line to the printed landing edge", (1.350, 7.100, 2.500, 7.450)),
    ],
}
# hand values from the printed dimensions (T-091 LIVING_1F_SPLIT.csv; the connector from the chains, see the note)
HAND = {"LIVING": 22.200, "CORRIDOR": 7.044, "LANDING": 4.875, "CONNECTOR": 4.469, "OPENING": 0.0, "STAIRWELL": 0.0}
FREELANCER_ONE_ROW_M2 = 38.96


def _u(rects, ox, oy):
    return unary_union([box(ox + a, oy + b, ox + c, oy + d) for a, b, c, d in rects])


def trace(boq, arch):
    from engine.source import arch_floor as AF
    room = next(r for r in arch["rooms"] if r["room_id"] == ROOM)
    F = Polygon(room["polygon_m"]).buffer(0)
    ox, oy = F.bounds[0], F.bounds[1]
    dh = next(v for v in arch["run"]["double_height"] if v["floor"] == room["floor"])
    xs = [p[0] - dh["offset"]["dx"] for p in dh["window"]]
    ys = [p[1] - dh["offset"]["dy"] for p in dh["window"]]
    V = box(min(xs) / 1000.0, min(ys) / 1000.0, max(xs) / 1000.0, max(ys) / 1000.0)
    flights, quad_rows, eng_own, eng_below = {}, [], 0.0, 0.0
    for fl in room["symbols_inside"]["stair_flights"]:
        fid = fl["flight_id"].split(":")[-1]
        polys = []
        for i, q in enumerate(fl["tread_quads"]):
            qm = [(x / 1000.0, y / 1000.0) for x, y in q]
            P = Polygon(qm).buffer(0)
            polys.append(P)
            e = AF.PP.region_area_in_convex(room["polygon_m"], room["hole_polygons_m"], qm)
            t = P.intersection(F).area
            if abs(e - t) > 1e-3:
                quad_rows.append({"flight": fid, "quad": i + 1, "engine_clip_m2": round(e, 4), "exact_m2": round(t, 4),
                                  "non_convex_m2": round(P.convex_hull.area - P.area, 5)})
        flights[fid] = {"poly": unary_union(polys), "below": bool(fl.get("drawn_on_plan_below")), "kind": fl["kind"]}
    TU = unary_union([f["poly"] for f in flights.values()])
    line = next(l for l in boq["lines"] if l["item_code"] == "FIN.FLOOR.PORCELAIN" and
                l["location"].get("room_id") == ROOM)
    rows, regions_union = [], []
    for name, rects in REGIONS.items():
        R = _u(rects, ox, oy)
        regions_union.append(R)
        fa = F.intersection(R)
        res = fa.difference(V).difference(TU)
        fl = {k: round(v["poly"].intersection(fa).difference(V).area, 4) for k, v in flights.items()
              if v["poly"].intersection(fa).difference(V).area > 1e-4}
        rows.append({"region": name, "piece": "region total", "face_m2": round(fa.area, 4),
                     "void_m2": round(fa.intersection(V).area, 4), "treads_m2": round(sum(fl.values()), 4),
                     "engine_floor_m2": round(res.area, 4), "hand_m2": HAND[name],
                     "engine_minus_hand_m2": round(res.area - HAND[name], 4), "flights": json.dumps(fl),
                     "local_box_m": json.dumps(rects)})
        acc = 0.0
        for label, rect in SUBPIECES.get(name, ()):
            a = res.intersection(_u([rect], ox, oy)).area
            acc += a
            rows.append({"region": name, "piece": label, "engine_floor_m2": round(a, 4), "local_box_m": json.dumps(rect)})
        if name in SUBPIECES:
            rows.append({"region": name, "piece": "rest of the region's residual", "engine_floor_m2": round(res.area - acc, 4)})
    cov = unary_union(regions_union)
    outside = F.difference(cov).difference(V).difference(TU).area
    exact_floor = F.difference(V).difference(TU).area
    summary = {
        "room": ROOM, "engine_line_m2": line["measured_net"], "engine_gross_m2": line["gross"],
        "engine_deductions": line["deductions"], "exact_floor_after_void_and_treads_m2": round(exact_floor, 4),
        "engine_minus_exact_m2": round(line["measured_net"] - exact_floor, 4),
        "tread_clip_differences": quad_rows, "face_outside_the_regions_m2": round(outside, 4),
        "hand_total_m2": round(sum(HAND.values()), 3), "freelancer_one_row_m2": FREELANCER_ONE_ROW_M2,
    }
    summary["engine_minus_hand_m2"] = round(line["measured_net"] - summary["hand_total_m2"], 4)
    return rows, summary


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--v29")
    ap.add_argument("--drawing")
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    if a.v29:
        boq, arch, _ = pickle.load(open(a.v29, "rb"))
    else:
        from tools import urban_boq_m9 as M
        boq, arch, _ = M.arch_compute(a.drawing, method="ARCH_TAKEOFF_V2.9")
    rows, summary = trace(boq, arch)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    keys = ["region", "piece", "face_m2", "void_m2", "treads_m2", "engine_floor_m2", "hand_m2", "engine_minus_hand_m2",
            "flights", "local_box_m"]
    with open(out / "LIVING_1F_TRACE.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)
    (out / "living_1f_trace_summary.json").write_text(json.dumps(summary, indent=1, default=str), encoding="utf-8")
    print(json.dumps(summary, indent=1, default=str))


if __name__ == "__main__":
    main()
