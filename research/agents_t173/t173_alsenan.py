"""T-173 development-villa run: stair shaft ST-01 wall faces, drawing-derived vs owner manual vs storey interval.

Rerun (from the task tree root): python3 -I research/agents_t173/t173_alsenan.py [--write]
Reads only ALSENAN_SHAFT_INPUT.json (shaft-local dimensions and levels, no coordinates or client data).
Two scenarios bound every PROVISIONAL / HELD input:
  HI: build-up b = 0, NW floor under the winders +0.30, held contacts and held openings not deducted;
  LO: build-up b = 0.10, NW floor +1.00, held contacts and held openings deducted over their whole bounded zone.
"""

from __future__ import annotations

import csv
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _load(name):
    spec = importlib.util.spec_from_file_location(name, HERE / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules.setdefault(name, mod)
    spec.loader.exec_module(mod)
    return sys.modules[name]


S = _load("t173_shaft")
INP = json.loads((HERE / "ALSENAN_SHAFT_INPUT.json").read_text())
T = 0.16
DECOR = 0.15
STOREYS = [5.50, 9.70]


def faces(b: float, nw_floor: float, top: float) -> list[dict]:
    L = INP["levels"]
    F = INP["flights"]
    s1 = L["f1"] - b - T          # 1F slab soffit
    s2 = L["f2"] - b - T          # 2F slab soffit
    winder_bottom = S.flight_soffit_at_last_riser(1.00, 10, 1 / 6, 0.30, 0.16)   # 2.317: lowest possible
    def fl(key, extend_end=True, t_start=None, t_end=None):
        f = F[key]
        return dict(u_first=f["first_riser_Y"], direction=1 if f["dir"] == "+Y" else -1, z0=f["z0"],
                    risers=f["risers"], riser=f["riser"], going=f["going"], waist=f["waist"],
                    t_start=t_start, t_end=t_end, extend_end=extend_end)

    head_beams = lambda u_end_b20, u_end_b23: [
        {"id": "B20 end (HELD Q-46 / OQ-11)", "status": "HELD", "rect": [4.50, u_end_b20, s1 - 0.75, s1]},
        {"id": "B23 end (HELD Q-46 / OQ-11)", "status": "HELD", "rect": [4.50, u_end_b23, s2 - 0.75, s2]},
    ]
    slabs = [
        {"id": "1F slab band (arrival landing)", "band": {"u": [4.50, 5.20], "level": L["f1"], "t": T, "buildup": b}},
        {"id": "2F slab band (arrival landing)", "band": {"u": [4.50, 5.20], "level": L["f2"], "t": T, "buildup": b}},
    ]
    O = INP["openings"]
    def op(key, status=None, z=None):
        o = O[key]
        u = o.get("Y") or o.get("X")
        zz = z or o["z"]
        return {"id": key, "status": status or o["status"], "rect": [u[0], u[1], zz[0], zz[1]]}

    west = {
        "id": "W (west, outer wall: W01 / W13 / W26)",
        "region": [[0.0, 1.15, nw_floor, top], [1.15, 5.00, L["gf"], top], [5.00, 5.20, L["f1"], top]],
        "contacts": [
            {"id": "MS1-L flight", "flight": fl("MS1-L", extend_end=False, t_start=0.0, t_end=T + b)},
            {"id": "MS1-T winders (HELD: soffit not drawn)", "status": "HELD", "rect": [0.0, 1.15, winder_bottom, L["landing1"]]},
            {"id": "MS2-L flight", "flight": fl("MS2-L", t_start=T + b, t_end=T + b)},
            {"id": "MS2-LD landing (west half)", "band": {"u": [0.0, 1.20], "level": L["landing2_w"], "t": T, "buildup": b}},
        ] + slabs + head_beams(5.00, 4.95),
        "openings": [op("W01"), op("W13"), op("W26"), op("D115")],
        "returns": [{"u": u, "depth": INP["dimensions_m"]["pier_returns"]["depth"]} for u in INP["dimensions_m"]["pier_returns"]["v"]],
    }
    east = {
        "id": "E (east, lift-shaft wall)",
        "region": [[0.0, 1.15, L["gf_lobby"], top], [1.15, 1.45, 0.475, top], [1.45, 1.75, 0.65, top],
                   [1.75, 2.05, 0.825, top], [2.05, 5.00, L["gf"], top], [5.00, 5.20, L["f1"], top]],
        "contacts": [
            {"id": "MS1-LD landing", "band": {"u": [0.0, 1.20], "level": L["landing1"], "t": T, "buildup": b}},
            {"id": "MS1-U flight", "flight": fl("MS1-U", t_start=T + b, t_end=T + b)},
            {"id": "MS2-LD landing (east half)", "band": {"u": [0.0, 1.20], "level": L["landing2_e"], "t": T, "buildup": b}},
            {"id": "MS2-U flight", "flight": fl("MS2-U", t_start=T + b, t_end=T + b)},
        ] + slabs + head_beams(5.00, 4.95),
        "openings": [op("GF-passage-E", z=O["GF-passage-E"]["held_band"])],
    }
    north = {
        "id": "N (north, outer wall)",
        "region": [[0.0, 1.30, nw_floor, top], [1.30, 2.50, L["gf_lobby"], top]],
        "contacts": [
            {"id": "MS1-T winders (HELD: soffit not drawn)", "status": "HELD", "rect": [0.0, 1.30, winder_bottom, L["landing1"]]},
            {"id": "MS1-LD landing", "band": {"u": [1.30, 2.50], "level": L["landing1"], "t": T, "buildup": b}},
            {"id": "MS2-LD landing (west half)", "band": {"u": [0.0, 1.25], "level": L["landing2_w"], "t": T, "buildup": b}},
            {"id": "MS2-LD landing (east half)", "band": {"u": [1.25, 2.50], "level": L["landing2_e"], "t": T, "buildup": b}},
        ],
        "openings": [
            op("GF-court-door"),
            op("1F-north-window", z=[L["landing1"], L["landing2_e"] - b - T]),
            op("W27", z=[L["landing2_e"], top]),
        ],
    }
    south = {
        "id": "S (GF south wall only; above it the 1F arrival landing)",
        "region": [[0.0, 2.50, L["gf"], s1]],
        "contacts": [{"id": "B20 over the wall (HELD Q-46 / OQ-11)", "status": "HELD", "rect": [0.0, 2.50, s1 - 0.75, s1]}],
        "openings": [op("GF-south-door")],
    }
    return [west, east, north, south]


def run():
    roof = INP["levels"]["roof_mark"]
    out = {}
    for case, b, nw in (("HI", 0.0, INP["levels"]["gf_lobby"]), ("LO", 0.10, INP["levels"]["gf"])):
        top_plaster = roof - b - T
        out[case] = {
            "plaster": S.measure_shaft(faces(b, nw, top_plaster), STOREYS),
            "paint": S.measure_shaft(faces(b, nw, top_plaster - DECOR), STOREYS),
            "b": b, "nw_floor": nw, "top_plaster": top_plaster,
        }
    lengths = {"GF": 5.00 + 5.00 + 2.50 + 2.50 + 0.10, "1F": 5.20 + 5.20 + 2.50 + 0.10, "2F": 5.20 + 5.20 + 2.50 + 0.10}
    owner = S.owner_manual_gross(lengths, INP["owner_manual"]["heights"])
    interval = S.storey_interval_gross({"GF": lengths["GF"], "1F": lengths["1F"]}, {"GF": 4.50, "1F": 4.20})
    void_only = {"GF": 11.60, "1F": 11.60, "2F": 11.60}
    return {"cases": out, "lengths_by_storey": lengths, "owner_manual": owner, "storey_interval_gf_1f": interval,
            "void_lengths": void_only}


def _r(x):
    return round(x, 2)


def summary(res):
    rows = []
    for case in ("HI", "LO"):
        for kind in ("plaster", "paint"):
            t = res["cases"][case][kind]["total"]
            rows.append({"case": case, "finish": kind, **{k: _r(v) for k, v in t.items() if k != "storeys"},
                         "storeys": [{k: (_r(v) if isinstance(v, float) else v) for k, v in s.items()} for s in t["storeys"]]})
    return rows


if __name__ == "__main__":
    res = run()
    rows = summary(res)
    for r in rows:
        print(r["case"], r["finish"], "gross", r["gross"], "known contacts", r["contacts_known"], "openings", r["openings_known"],
              "held c", r["contacts_held_max"], "held o", r["openings_held_max"], "returns", r["returns_hi"], r["returns_lo"],
              "net_hi", r["net_hi"], "net_lo", r["net_lo"])
        print("   storeys", [(s["z_from"], s["z_to"], s["gross"], s["net_hi"], s["net_lo"]) for s in r["storeys"]])
    for case in ("HI", "LO"):
        for f in res["cases"][case]["plaster"]["faces"]:
            print(case, f["id"], {k: _r(f[k]) for k in ("gross", "contacts_known", "openings_known", "contacts_held_max", "openings_held_max", "net_hi", "net_lo")})
            print("     ", {k: _r(v) for k, v in f["pieces"]["contacts"].items()}, {k: _r(v) for k, v in f["pieces"]["openings"].items()})
    print("owner manual", {k: _r(v) for k, v in res["owner_manual"]["per_storey"].items()}, _r(res["owner_manual"]["total"]))
    print("storey interval GF/1F", {k: _r(v) for k, v in res["storey_interval_gf_1f"]["per_storey"].items()})
    if "--write" in sys.argv:
        (HERE / "SHAFT_T173.json").write_text(json.dumps({
            "summary": rows,
            "faces": {case: {kind: [{k: (_r(v) if isinstance(v, float) else v) for k, v in f.items() if k not in ("pieces", "storeys")}
                                    | {"pieces": {g: {n: _r(a) for n, a in d.items()} for g, d in f["pieces"].items()},
                                       "storeys": [{k: (_r(v) if isinstance(v, float) else v) for k, v in s.items()} for s in f["storeys"]]}
                                    for f in res["cases"][case][kind]["faces"]] for kind in ("plaster", "paint")} for case in ("HI", "LO")},
            "owner_manual": {"per_storey": {k: _r(v) for k, v in res["owner_manual"]["per_storey"].items()}, "total": _r(res["owner_manual"]["total"])},
            "lengths_by_storey": res["lengths_by_storey"],
        }, indent=1) + "\n")
