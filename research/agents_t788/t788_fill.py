"""T-788 F-22 cornice fix row on ARCH_TAKEOFF_V3.0.85 (worker 2, 2026-11-14).

The candidate line FIN.CEILING.CORNICE (B5-03, L-33d272f5b4d7b33767b6) carries 302.88 lm = the T-147 closed-room
perimeters only; the open zones (GF open room, pantry, wash lobby, 1F living zone, 2F stair lobby) were left out as
"run not closed". R-T788-1 / -2 (t788_rules.py) give each of them the run on its wall faces.

Inputs: the architectural DXF of the Drive folder "Alsenan chalet project" (P7757_DXF_COMPRESSED.zip), decoded with the
wrapper into .work/private, polygonised per floor with the T-147 tool (boxes of T-128 walk_r2.py):
  python -I research/agents_t147/scripts/rooms.py <P7757.dxf> -163 -124 -811 -784 <priv>/gf_rooms.json
  python -I research/agents_t147/scripts/rooms.py <P7757.dxf> -208 -169 -811 -784 <priv>/f1_rooms.json
  python -I research/agents_t147/scripts/rooms.py <P7757.dxf> -253 -214 -811 -784 <priv>/f2_rooms.json
  python -I research/agents_t788/t788_fill.py <priv>          (writes out/FIX_ROWS.json; no coordinates are written)
Zone cuts are the T-147 ceil_ledger.py clips (gclip, lobby box, pantry box, shaft boxes), copied below.
"""
from __future__ import annotations

import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
RES = HERE.parent
sys.path.insert(0, str(HERE))
import t788_rules as R  # noqa: E402

LINE = "L-33d272f5b4d7b33767b6"
IDX = RES / "agents_t770/out/LINE_INDEX_V3_0_85.json"
T147 = RES / "agents_t147/rooms_geom.json"
FREELANCER = {  # Drive freelancer finishing workbook, sheet 'decor', cornice column G (lm) by room row
    "dry": {"GF reception+dining": 58.16, "GF master bed": 21.71, "GF entrance": 14.76, "GF diwaniya": 20.0,
            "GF driver": 12.5, "1F living": 43.78, "1F bed 1": 22.89, "1F bed 2": 21.4, "1F bed 3": 17.3,
            "1F bed 4": 17.45, "2F maid": 19.3, "2F corridor": 13.6},
    "wet": {"GF diwaniya wash": 14.8, "GF baths (4)": 27.9, "GF kitchen": 14.35, "GF bath (2)": 13.08,
            "GF washroom": 7.2, "1F baths (5)": 40.68, "1F laundry": 16.85, "2F bath": 9.75},
}
FL_DRY, FL_WET = 282.85, 144.61


def open_zones(priv):
    from shapely import wkt
    from shapely.geometry import Polygon, box

    def faces(name):
        return {o["i"]: wkt.loads(o["wkt"]) for o in json.load(open(priv / name))["faces"]}

    gf, f1, f2 = faces("gf_rooms.json"), faces("f1_rooms.json"), faces("f2_rooms.json")
    # parent faces, identified by area (the polygoniser numbers faces differently from run to run)
    def pick(F, area, tol=0.02):
        m = [g for g in F.values() if abs(g.area - area) < tol]
        if len(m) != 1:
            raise SystemExit(f"face of {area} m2 not unique ({len(m)})")
        return m[0]
    G0 = max(gf.values(), key=lambda g: g.area)          # the GF open face (leaks to the yard through unclosed gaps)
    P1 = pick(f1, 75.983)                                 # 1F living zone + stair shaft box
    P2 = pick(f2, 18.600)                                 # 2F stair lobby + shaft box
    niche = pick(gf, 0.637, 0.005)                        # wash-lobby niche face (T-147 lobby union)
    gclip = Polygon([(-148.2, -805.094), (-129.07, -805.094), (-129.07, -797.594), (-131.0, -797.594),
                     (-131.0, -795.9), (-145.05, -795.9), (-145.05, -800.45), (-148.2, -800.45)])
    LB, PB = box(-140.6, -796.0, -137.85, -793.0), box(-148.2, -805.2, -145.05, -800.45)
    g = R.partition_perimeter(G0, {"GF-14": LB,
                                   "GF-07": PB.intersection(gclip), "GF-08": gclip}, "OUTSIDE")
    p1 = R.partition_perimeter(P1, {"ST-1F": box(-189.893, -797.194, -187.393, -791.994)}, "1F-13")
    p2 = R.partition_perimeter(P2, {"ST-2F": box(-234.745, -797.194, -232.245, -791.994)}, "2F-01")
    # cut lines (T-147 clips) classified on the drawing: OPENING = a gap inside a wall line, OPEN_SIDE = no wall
    cuts = {
        "GF-07": [(2.79, "OPENING")],                     # south window gap, inner wall face (wall body leaks)
        "GF-08": [(0.285, "OPENING"), (1.475, "OPENING"), (0.891, "OPENING"), (1.271, "OPENING"), (4.5, "OPEN_SIDE")],
        "GF-14": [(1.271, "OPENING"), (niche.length, "WALL")],
        "1F-13": [(2.5, "OPEN_SIDE")],
        "2F-01": [],
    }
    runs = {
        "GF-07": R.cornice_run([(g["GF-07"], "WALL")] + cuts["GF-07"] + [(4.5, "OPEN_SIDE")], True),
        "GF-08": R.cornice_run([(g["GF-08"], "WALL")] + cuts["GF-08"], True),
        "GF-14": R.cornice_run([(g["GF-14"], "WALL")] + cuts["GF-14"], True),
        "1F-13": R.cornice_run([(p1["1F-13"], "WALL")] + cuts["1F-13"], True),
        # 2F lobby and the shaft-box top are ONE decor ceiling (T-147 ceils the box under the 2F roof slab)
        "2F-01+ST-2F": R.cornice_run([(p2["2F-01"], "WALL"), (p2["ST-2F"], "WALL")], True),
        "ST-1F": R.cornice_run([], False),
    }
    return runs, {"GF": g, "1F": p1, "2F": p2}


def main(priv):
    rooms = json.load(open(T147))
    open_ids = {"GF-07", "GF-08", "GF-14", "1F-13", "2F-01"}
    closed = {r["id"]: (r["kind"], r["perimeter"]) for r in rooms
              if r["id"] not in open_ids and r["kind"] in ("DRY", "WET")}
    runs, parts = open_zones(priv)
    before = 302.88
    st2_t147 = 15.5                                       # ST-2F perimeter T-147 carried in its 2F dry sum
    dry = sum(p for k, p in closed.values() if k == "DRY") + runs["GF-08"] + runs["1F-13"] + runs["2F-01+ST-2F"]
    wet = sum(p for k, p in closed.values() if k == "WET") + runs["GF-07"] + runs["GF-14"]
    after = round(dry + wet, 2)
    causes = {
        "GF open room (dining / entrance / reception / hall)": runs["GF-08"],
        "1F living zone (living + corridor + landing + light-well)": runs["1F-13"],
        "GF wash lobby (2 basins, incl. niche)": runs["GF-14"],
        "GF pantry (wet by owner Q-37 A)": runs["GF-07"],
        "2F stair lobby + shaft-box ceiling, net of the ST-2F 15.5 already in": round(runs["2F-01+ST-2F"] - st2_t147, 3),
    }
    out = {
        "schema": "URBAN_FIX_ROWS_V1", "task": "T-788", "rule": "R-T788-1 .. 2 (t788_rules.py, every villa)",
        "base": "ARCH_TAKEOFF_V3.0.85 (LINE_INDEX_V3_0_85.json)",
        "summary": {"before_lm": before, "after_lm": after, "dry_lm": round(dry, 3), "wet_lm": round(wet, 3),
                    "freelancer_lm": round(FL_DRY + FL_WET, 2), "freelancer_dry": FL_DRY, "freelancer_wet": FL_WET,
                    "added_by_cause_lm": {k: round(v, 3) for k, v in causes.items()},
                    "partition_lm": parts},
        "rows": [{
            "line_id": LINE, "item_code": "FIN.CEILING.CORNICE", "unit": "lm", "element_id": "T-771:NEW:CEILING:CORNICE",
            "before": {"class": "RELEASED", "net": before, "label": "ESTIMATE"},
            "after": {"class": "RELEASED", "net": after},
            "label": "ESTIMATE",
            "basis": (f"R-T788-1: decor-ceiling wall run per room / zone from the arch DXF faces (lengths MEASURED; the run "
                      f"itself ESTIMATE: no cornice detail printed, Q-57 A mod): closed rooms (T-147) 302.88 + open zones "
                      f"{round(after - before, 2)} (GF open room {runs['GF-08']}, 1F living zone {runs['1F-13']}, wash "
                      f"lobby {runs['GF-14']}, pantry {runs['GF-07']}, 2F lobby + shaft-box top {runs['2F-01+ST-2F']} "
                      f"replacing ST-2F 15.5); dry {round(dry, 2)} + wet {round(wet, 2)}; no run on open sides, void "
                      f"edges (ceiling drops, own line) or the stair wells"),
        }],
    }
    idx = json.load(open(IDX))
    line = next(l for l in idx["lines"] if l["line_id"] == LINE)
    assert abs(line["measured_net"] - before) < 1e-6, "candidate line moved: re-base the fix row"
    (HERE / "out").mkdir(exist_ok=True)
    (HERE / "out/FIX_ROWS.json").write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps(out["summary"], indent=1))


if __name__ == "__main__":
    main(pathlib.Path(sys.argv[1]))
