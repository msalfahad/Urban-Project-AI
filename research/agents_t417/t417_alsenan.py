"""T-417 development villa (Alsenan is one sample): ST-01 straight flights MS1-U / MS2-L / MS2-U and the half landings,
read BY HANDLE, and the T-406 r3 'ST-01 flight length -2.016 m3' and 'landing area +0.1624 m3' terms split.

Build (needs the PRIVATE structural DXF 'ST7757 dxf.dxf' from Drive folder 'Alsenan chalet project', decoded into
.work/private only, sha256 9f9d1179...; optionally the private concrete + rebar workbook to assert his figures):
    python3 -I research/agents_t417/t417_alsenan.py --dxf <ST7757 dxf.dxf> [--freelancer <workbook>] --write
asserts the type and layer of every handle it uses and writes summary_t417.json beside this file (lengths, counts,
areas and m3 only: no coordinates, no drawing content, no freelancer row text).
Check (no private input):
    python3 -I research/agents_t417/t417_alsenan.py --check
recomputes every figure from the committed summary and prints REPRODUCED.

Engine side: the merged T-258 r2 ledger (research/agents_t258/LEDGER_T258.csv), reproduced here by hand (R-T417-1).
Freelancer side: his two ST-01 rows as quantities only (flights 1.2 x 5.3 x 0.28 x 4; landings 1.2 x 1.4 x 0.20 x 3),
bound by his own unit as in T-398 (3 flight units to MS1-U / MS2-L / MS2-U, 2 landing units to MS1-LD / MS2-LD).
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import t417_rules as R  # noqa: E402

SUMMARY = HERE / "summary_t417.json"
LEDGER = ROOT / "research" / "agents_t258" / "LEDGER_T258.csv"
MM = 0.001
HIS = {"flights": dict(w=1.2, L=5.3, t=0.28, count=4), "landings": dict(w=1.2, L=1.4, t=0.20, count=3)}
# riser heights: MS1 4.50 / 27 (Q-46 A, section A-A count), MS2 4.20 / 25 (section A-A); levels +1.00 / +5.50 / +9.70
RISER = {"MS1": 4.50 / 27, "MS2": 4.20 / 25}
WAIST = 0.16      # 'T 16' (Q-47 A), the stair panel block 't' (580 on p.4, 74A on p.5)
GOING = 0.30
FLIGHTS = {       # riser lines in walking order (first = foot); the plan run is first -> last line
    "ST01-MS1-U": dict(sheet="p4", storey="MS1", lines=["25B", "25C", "261", "263", "262", "260", "267", "266", "265",
                                                         "264", "270", "459"], lane=("2F3", "296")),
    "ST01-MS2-L": dict(sheet="p5", storey="MS2", lines=["646", "645", "640", "641", "642", "643", "63C", "63D", "63E",
                                                         "63F", "631", "632"], lane=("5E3", "62D")),
    "ST01-MS2-U": dict(sheet="p5", storey="MS2", lines=["62F", "630", "635", "637", "636", "634", "63B", "63A", "639",
                                                         "638", "644"], arrival_from_p4="459", lane=("62E", "5D4")),
}
OWNED = {"ST01-MS1-U": (["ST01-MS1-U-HEAD"], 0.030000), "ST01-MS2-L": (["ST01-MS2-L-FOOT"], 0.030171),
         "ST01-MS2-U": (["ST01-MS2-U-HEAD"], 0.030240)}          # beam-owned pieces + the Q-62 A wedge (T-258 r2)


def build(dxf_path, wb_path=None):
    import ezdxf
    db = ezdxf.readfile(dxf_path).entitydb

    def ent(h, typ, layer):
        e = db[h]
        assert e.dxftype() == typ, (h, e.dxftype(), typ)
        assert e.dxf.layer == layer, (h, e.dxf.layer, layer)
        return e

    def hline(h, layer):                                    # a horizontal line: (y, x_min, x_max) in mm
        e = ent(h, "LINE", layer)
        assert abs(e.dxf.start.y - e.dxf.end.y) < 0.5, h
        return e.dxf.start.y, min(e.dxf.start.x, e.dxf.end.x), max(e.dxf.start.x, e.dxf.end.x)

    def vline(h, layer):
        e = ent(h, "LINE", layer)
        assert abs(e.dxf.start.x - e.dxf.end.x) < 0.5, h
        return e.dxf.start.x

    def box(h):
        e = ent(h, "LWPOLYLINE", "S-COL.BON")
        assert e.closed, h
        xs = [p[0] for p in e.get_points()]
        ys = [p[1] for p in e.get_points()]
        return min(xs), max(xs), min(ys), max(ys)

    lane_layer = {"2F3": "2", "296": "1", "5E3": "1", "62D": "S-OPENING", "62E": "S-OPENING", "5D4": "1"}
    out = {"schema": "T417_ALSENAN_ST01", "drawing": "'ST7757 dxf.dxf' sha256 9f9d1179 (Drive 'Alsenan chalet "
           "project'), ST p.4 GF roof slab plan and p.5 1F roof slab plan", "flights": {}, "landings": {},
           "columns": {}}
    for fid, f in FLIGHTS.items():
        ys = []
        for h in f["lines"]:
            y, x0, x1 = hline(h, "2")
            assert abs((x1 - x0) - 1150) < 0.5, (h, x1 - x0)
            ys.append(y)
        if "arrival_from_p4" in f:                          # identical p.4 line one going beyond the last drawn
            y, _, _ = hline(f["arrival_from_p4"], "2")
            assert abs(y - (ys[-1] - 300)) < 0.5, "arrival line not one going beyond 644"
            ys.append(y)
        steps = [abs(b - a) for a, b in zip(ys, ys[1:])]
        assert all(abs(s - 300) < 0.5 for s in steps), (fid, steps)
        xa, xb = (vline(h, lane_layer[h]) for h in f["lane"])
        out["flights"][fid] = {"risers_drawn": len(f["lines"]), "risers": len(ys), "going": GOING,
                               "run": round(abs(ys[-1] - ys[0]) * MM, 6), "lane": round(abs(xb - xa) * MM, 6),
                               "lane_edges": list(f["lane"]), "first": f["lines"][0], "last": f["lines"][-1],
                               "storey": f["storey"]}
    # landings: plate depth from the flight's first riser line to the north edge; B3 'With Stair' band beyond it
    y25B = hline("25B", "2")[0]
    y279, _, _ = hline("279", "1")
    y274, _, _ = hline("274", "1")
    ent("6B7", "TEXT", "S-TEXT")
    ent("6B6", "TEXT", "S-TEXT")
    assert db["6B7"].dxf.text == "B3" and db["6B6"].dxf.text == "(With Stair)"
    y632, y62F = hline("632", "2")[0], hline("62F", "2")[0]
    y5C0, y5BE = hline("5C0", "1")[0], hline("5BE", "1")[0]
    assert db["6B9"].dxf.text == "B3" and db["6B8"].dxf.text == "(With Stair)"
    x2F3, x296 = vline("2F3", "2"), vline("296", "1")
    x5E3, x5E2, x5D4 = vline("5E3", "1"), vline("5E2", "2"), vline("5D4", "1")
    out["landings"] = {
        "ST01-MS1-LD": {"depth": round((y279 - y25B) * MM, 6), "width": round((x296 - x2F3) * MM, 6),
                        "band": {"id": "B3 (With Stair) 279 -> 274", "width": round((y274 - y279) * MM, 6),
                                 "owner": "BEAM"}, "edges": "25B -> 279, 2F3 -> 296"},
        "ST01-MS2-LD-E": {"depth": round((y5C0 - y62F) * MM, 6), "width": round((x5D4 - x5E2) * MM, 6),
                          "band": {"id": "B3 (With Stair) 5C0 -> 5BE", "width": round((y5BE - y5C0) * MM, 6),
                                   "owner": "BEAM"}, "edges": "62F -> 5C0, 5E2 -> 5D4"},
        "ST01-MS2-LD-W": {"depth": round((y5C0 - y632) * MM, 6), "width": round((x5E2 - x5E3) * MM, 6),
                          "band": {"id": "B3 (With Stair) 5C0 -> 5BE", "width": round((y5BE - y5C0) * MM, 6),
                                   "owner": "BEAM"}, "edges": "632 -> 5C0, 5E3 -> 5E2"},
    }
    # columns on the flight sides (same plan as the lane, R-T417-5)
    cols = {"691": ("ST01-MS2-L", "west", x5E3, "646"), "682": ("ST01-MS2-U", "east", x5D4, "62F"),
            "341": ("ST01-MS1-U", "east", x296, "25B"), "36B": ("ST01-MS1-L", "west", vline("284", "1"), "45A")}
    for h, (fid, side, face, first) in cols.items():
        x0, x1, y0, y1 = box(h)
        proud = (x1 - face) if side == "west" else (face - x0)
        yf = hline(first, "2")[0]
        out["columns"][h] = {"flight": fid, "side": side, "proud": round(max(proud, 0.0) * MM, 6),
                             "s0": round(min(abs(y0 - yf), abs(y1 - yf)) * MM, 6),
                             "s1": round(max(abs(y0 - yf), abs(y1 - yf)) * MM, 6),
                             "size": [round((x1 - x0) * MM, 3), round((y1 - y0) * MM, 3)]}
    if wb_path:
        import openpyxl
        ws = openpyxl.load_workbook(wb_path, data_only=True).worksheets[6]
        for key, row in (("flights", 20), ("landings", 21)):
            b, c, d, f = (ws.cell(row, x).value for x in (2, 3, 4, 6))
            h = HIS[key]
            assert (b, c, d, f) == (h["w"], h["L"], h["t"], h["count"]), (key, b, c, d, f)
        out["freelancer_asserted"] = True
    return out


def ledger():
    return {r["id"]: r for r in csv.DictReader(LEDGER.open(encoding="utf-8"))}


def derive(g):
    led = ledger()
    F = HIS["flights"]
    fl, terms, flights_sum = {}, [], 0.0
    sib = [{"id": k, "row": "flights", "run": v["run"], "n": v["risers"], "riser": RISER[v["storey"]]}
           for k, v in g["flights"].items()]
    for fid, f in g["flights"].items():
        r = RISER[f["storey"]]
        h = R.flight(f["risers"], r, f["going"], f["lane"], f["run"], WAIST)
        owned_ids, wedge = OWNED[fid]
        owned = sum(float(led[o]["value_m3"]) for o in owned_ids) + wedge
        net = R.r6(h["gross_m3"] - owned)
        lv = float(led[fid]["value_m3"])
        assert abs(net - lv) <= 2e-6, (fid, net, lv)
        his = F["w"] * F["L"] * F["t"]
        contrib = net - his
        t_w = {"term": "WIDTH", "m3": R.r6(-(F["w"] - f["lane"]) * F["L"] * F["t"]), "traced": True}
        t_t = {"term": "THICKNESS_BASIS", "m3": R.r6(h["gross_m3"] - f["run"] * f["lane"] * F["t"]), "traced": True}
        t_o = {"term": "OWNERSHIP", "m3": R.r6(-owned), "traced": True}
        t_l = R.length_terms(fid, "flights", F["L"], F["w"], F["t"], f["run"], f["risers"], r, sib)
        ts = [t_w, t_t, t_o] + t_l
        cl = R.closure(contrib, ts)
        fl[fid] = {"steps_m3": h["steps_m3"], "waist_m3": h["waist_m3"], "inclined_m": h["inclined_m"],
                   "sec": round(h["sec"], 6), "profile_m": h["profile_m"], "rise_m": R.r6(f["risers"] * r),
                   "plate_equivalent_t": round(R.plate_equivalent(h["steps_m3"], h["waist_m3"], f["run"], f["lane"]), 6),
                   "owned_elsewhere_m3": R.r6(owned), "net_m3": net, "ledger_m3": lv, "his_unit_m3": R.r6(his),
                   "contribution_m3": cl["contribution_m3"], "terms": ts}
        terms += [dict(t, piece=fid) for t in ts]
        flights_sum += contrib
    # landings: his 2 units bound to MS1-LD and MS2-LD (T-398); MS2-LD's unit bound to the E plate (his depth = 1.20 +
    # B3 on the E lane exactly), the W plate unbound (COUNT)
    L = HIS["landings"]
    ld, lterms = {}, []
    his_area = L["w"] * L["L"]
    for pid in ("ST01-MS1-LD", "ST01-MS2-LD-E"):
        p = g["landings"][pid]
        ts = R.landing_depth_terms(pid, L["L"], L["w"], p["depth"], p["width"], WAIST, [p["band"]])
        lterms += [dict(t, piece=pid) for t in ts]
        ld[pid] = {"area_m2": R.r6(p["depth"] * p["width"]), "m3": float(led[pid]["value_m3"])}
    pW = g["landings"]["ST01-MS2-LD-W"]
    aW = R.r6(pW["depth"] * pW["width"])
    lterms.append(dict(R.unbound_plate_term("ST01-MS2-LD-W", aW, WAIST), piece="ST01-MS2-LD-W"))
    ld["ST01-MS2-LD-W"] = {"area_m2": aW, "m3": float(led["ST01-MS2-LD-W"]["value_m3"])}
    for pid, v in ld.items():
        assert abs(v["area_m2"] * WAIST - v["m3"]) <= 2e-6, (pid, v)
    eng_land_area = sum(v["area_m2"] for v in ld.values())
    area_term = R.r6((eng_land_area - 2 * his_area) * WAIST)
    thk_term = R.r6((WAIST - L["t"]) * 2 * his_area)
    land_cl = R.closure(area_term, lterms)
    # columns
    cols = {}
    for h, c in g["columns"].items():
        f = g["flights"].get(c["flight"])
        if c["proud"] <= 0:
            cols[h] = {"flight": c["flight"], "state": "FLUSH", "m3": 0.0}
            continue
        if f is None:                                        # MS1-L is HELD (C-ST-4): plan exposure only
            cols[h] = {"flight": c["flight"], "state": "HELD_WITH_FLIGHT", "plan_m2": R.r6(c["proud"] *
                       (c["s1"] - c["s0"])), "m3": None}
            continue
        e = R.projection_exposure(c["proud"], c["s0"], c["s1"], RISER[f["storey"]], f["going"], WAIST,
                                  f["risers"], f["run"])
        cols[h] = dict(R.projection_deduction(e, "CONFLICT"), flight=c["flight"], plan_m2=R.r6(c["proud"] *
                       (c["s1"] - c["s0"])))
    length_total = R.r6(sum(t["m3"] for t in terms if t["term"] in ("RISE_IN_LENGTH", "ONE_LENGTH", "LENGTH")))
    rise = R.r6(sum(t["m3"] for t in terms if t["term"] == "RISE_IN_LENGTH"))
    one = R.r6(sum(t["m3"] for t in terms if t["term"] == "ONE_LENGTH"))
    untr = R.r6(sum(t["m3"] for t in terms if not t["traced"]))
    return {"flights": fl, "flights_contribution_m3": R.r6(flights_sum),
            "length_term_m3": length_total, "rise_in_length_m3": rise, "one_length_m3": one,
            "flight_untraced_m3": untr,
            "landings": ld, "landing_area_term_m3": area_term, "landing_thickness_term_m3": thk_term,
            "landing_terms": lterms, "landing_closure": land_cl,
            "landing_contribution_m3": R.r6(sum(v["m3"] for v in ld.values()) - 2 * his_area * L["t"]),
            "columns": cols}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--dxf")
    ap.add_argument("--freelancer")
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    if a.check:
        s = json.loads(SUMMARY.read_text(encoding="utf-8"))
        d = derive(s["geometry"])
        if json.dumps(d, sort_keys=True) != json.dumps(s["derived"], sort_keys=True):
            print("DIFFERS")
            return 1
        print("REPRODUCED")
        return 0
    g = build(a.dxf, a.freelancer)
    d = derive(g)
    doc = {"geometry": g, "derived": d}
    if a.write:
        SUMMARY.write_text(json.dumps(doc, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in d.items() if not isinstance(v, (dict, list))}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
