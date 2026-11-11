"""T-718 stair finishes round 2 (Alsenan development villa; method every villa). Research only, unwired.

(a) Checker finding F-V715-1 (MS2-L skirting plan 2.25 m vs drawn wall 2.20 m) reconciled by handle to its cause, and the
    same datum check on every skirting piece of the T-410 table that a cut splits inside a flight (R-T718-1).
(b) The one-sided T-715 lines given an upper end where one drawn geometry bounds them (R-T718-2), the floors kept or
    raised only to a drawn sum (R-T718-3), and the missing datum named where nothing drawn bounds them.

Inputs (committed only): T718_DRAWN.json (this run's own read of P7757.dxf ab54dd55 / ST7757 dxf 9f9d1179, written by
t718_extract.py), research/agents_t715/out/T715_LEDGER.json (T-715 MERGED a4e4277a), research/agents_t410/
SIDE_TABLE_T410.csv (T-410 MERGED). Owner rules: UP-STAIR-006 t 0.030, Q-46 A (4.50 / 27), Q-50 A cond (4.50 / 28).
    python3 -I research/agents_t718/t718_alsenan.py [--write | --check]
"""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
RES = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(RES / "agents_t715"))
import t715_rules as R5  # noqa: E402
import t718_rules as R  # noqa: E402

BR = R.BR
D = Decimal
DRAWN_JSON = HERE / "T718_DRAWN.json"
T715 = RES / "agents_t715" / "out" / "T715_LEDGER.json"
T410 = RES / "agents_t410" / "SIDE_TABLE_T410.csv"
OUT_JSON = HERE / "out" / "T718_LEDGER.json"
OUT_MD = HERE / "out" / "T718_REPORT.md"
PINS = {"T718_DRAWN.json": "see --check", "arch_sha8": "ab54dd55", "st_sha8": "9f9d1179"}
T_TREAD = D("0.030")
OA = "ASSUMED - OWNER-APPROVED"
DC = "DRAWING-CONFIRMED"
DW = R.DRAWN

# T-410 pieces split by a cut inside a flight: flight -> piece ids in walking order (MS1-U.E2 / E3b and the window
# pieces MS1-L.W2 / MS2-L.W2 are the held / not-applicable stretches between the cuts)
CUT_PIECES = {
    "MS2-L": ["MS2-L.W1", "MS2-L.W1C", "MS2-L.W1B", "MS2-L.W2"],
    "MS1-L": ["MS1-L.W1", "MS1-L.W1C", "MS1-L.W1B", "MS1-L.W2"],
    "MS1-U": ["MS1-U.E1", "MS1-U.E2", "MS1-U.E3a"],
    "RS-S": ["RS-S.S0", "RS-S.S1", "RS-S.S2"],
}
# MS1-U: the arch plans draw 11 front edges (s 0 .. 3.00); E3 = E3a (to the last drawn front, 1.15) + E3b (the top
# 0.300, CONFLICT arch vs ST p.4, T-508 / C-ST-4) stays AT_MOST: this run measures E3a only.


def load():
    d = json.loads(DRAWN_JSON.read_text())
    assert d["sources"]["arch"]["sha256_8"] == PINS["arch_sha8"] and d["sources"]["st"]["sha256_8"] == PINS["st_sha8"]
    led = json.loads(T715.read_text())
    assert led["candidate"] == "ARCH_TAKEOFF_V3.0.70"
    side = {r["sid"]: r for r in csv.DictReader(T410.open())}
    return d, led, side


# ------------------------------------------------------------------ (a) datum check of the cut pieces
def datum_rows(d, led, side):
    t715 = {}
    for l in led["lines"]:
        if l.get("piece"):
            t715.setdefault(l["piece"], {})[l["item_code"].split(".")[-1]] = l
    rows = []
    for fl, ids in CUT_PIECES.items():
        g = d["straight"]["flights"][fl]
        res = R.pieces(fronts=[str(v) for v in g["front_stations_m"]],
                       faces=[None if v is None else str(v) for v in g["face_stations_m"]],
                       cuts=[str(c["station_m"]) for c in g["cuts"]])
        fe, rf = res["front_edge"]["plans_m"], res["riser_face"]["plans_m"]
        assert len(fe) == len(ids), (fl, fe, ids)
        for i, sid in enumerate(ids):
            base = sid if sid in side else sid[:-1]           # E3a is the T-715 split of T-410 E3
            t410_plan = D(side[base]["plan_lm"]) if sid in side else None
            t410_ris = int(side[base]["risers_in"]) if sid in side and side[base]["risers_in"] else None
            if sid == "MS1-U.E3a":
                t410_plan, t410_ris = D(side[base]["plan_lm"]) - D("0.300"), int(side[base]["risers_in"]) - 1
            agree = t410_plan is not None and abs(fe[i] - t410_plan) < D("0.0000005") and t410_ris == res["risers"][i]
            lines = t715.get(sid, {})
            rows.append({"flight": fl, "piece": sid, "plan_front_edge_m": str(BR.round_point(fe[i])),
                         "plan_riser_face_m": str(BR.round_point(rf[i])), "risers": res["risers"][i],
                         "risers_by_front": res["risers_by_front"][i], "t410_plan_m": str(t410_plan),
                         "t410_risers": t410_ris, "t410_agrees_front_edge": agree,
                         "t715_lines": {k: {"line_id": v["line_id"], "class": v["after"]["class"],
                                            "value": v["after"]["value"], "high": v["after"]["high"]}
                                        for k, v in sorted(lines.items())},
                         "cuts": [f"{c['label']} ({c['handle']}) s {c['station_m']}" for c in g["cuts"]]})
        assert not res["cut_inside_projection"], fl
    return rows


def fv715_1(d):
    g = d["straight"]["flights"]["MS2-L"]
    p = D(str(g["nosing_projection_m"][0]))
    jamb = D(str([c for c in g["cuts"] if c["handle"] == "C5C"][0]["station_m"]))
    walled_front = jamb - D(str(g["front_stations_m"][0]))
    walled_face = jamb - D(str(g["face_stations_m"][0]))
    win_front = D(str(g["front_stations_m"][-1])) - jamb
    win_face = D(str(g["face_stations_m"][-1])) - jamb
    assert walled_front == D("2.25") and walled_face == D("2.2") and walled_front - walled_face == p
    return {"finding": "F-V715-1", "flight": "MS2-L", "status": "CLOSED - cause found (datum), no line moves",
            "walled_plan_front_edge_m": str(BR.round_point(walled_front)), "walled_plan_riser_face_m": str(BR.round_point(walled_face)),
            "window_plan_front_edge_m": str(BR.round_point(win_front)), "window_plan_riser_face_m": str(BR.round_point(win_face)),
            "difference_m": str(BR.round_point(walled_front - walled_face)), "nosing_projection_m": str(BR.round_point(p)),
            "cause": "the 0.050 is the drawn nosing projection (front edge AC0 layer 5 / riser face AC2 layer 2, every pair "
                     "0.050 apart): T-410 cut the pieces on the FRONT-EDGE datum (first front edge -> column 3005 1.000, "
                     "column 0.500, -> window jamb C5C 0.750 = 2.250); the Checker measured the wall from the first RISER "
                     "FACE (2.200). Both runs are 3.300 (11 x 0.300) and both give 4 / 1 / 3 / 4 risers; the window "
                     "stretch is 1.050 vs 1.100 by the same 0.050",
            "physical_reading": "the skirting rides the visible tread tops, which run front edge to front edge, and the "
                                "sloped form rakes on the nosing line (UP-STAIR-011): the walled stretch of the strip is "
                                "2.250 (R-T718-1); 2.200 is the wall beyond riser face 1, a different length (the first "
                                "0.050 lies over the 1F floor under nosing 1)",
            "verdict": "T-410 pieces AGREE by handle (W1 1.000 / W1C 0.500 / W1B 0.750, risers 4 / 1 / 3); the 2F stack "
                       "(12B7 / 2F78 / 12CF-12D1) repeats the 1F stations: one face, one reading"}


# ------------------------------------------------------------------ (b) bounds
def riser(rise, n):
    return R5.riser(rise, n)


def turn_rows(d, t715):
    t = d["turn_ms1_t"]
    a, b = D(str(t["side_to_west_wall_m"])), D(str(t["side_to_north_wall_m"]))
    diam = R.turn_front_at_most(side_a=(a, DW), side_b=(b, DW))
    be6 = D(str([f for f in t["fan"] if f["handle"] == "BE6"][0]["drawn_m"]))
    assert abs(diam - be6) < D("0.000001"), (diam, be6)      # the drawn diagonal BE6 is the region's diameter
    vis = riser(D("4.50"), 27) - T_TREAD
    out = []
    for code, n, unit in (("FIN.MARBLE.RISER", 5, "m2"), ("FIN.STAIR.STEP_LM", 5, "lm")):
        old = t715[("1F-R78C367:flight 5", code)]
        lo = D(old["after"]["low"])
        hi = BR.mul(n, diam, vis) if unit == "m2" else BR.mul(n, diam)
        st = R5.statement(old["line_id"], "RANGE", low=lo, high=hi, item=old["after"]["item"],
                          status=DC + " (region 1.150 x 1.150: fan BE6 / BE8 / BEA ends on AF0 / ADE)" +
                          ("; r 4.50/27 (Q-46 A), t " + OA if unit == "m2" else ""),
                          cause=f"floor kept (R-T715-2: {n} fronts >= 1.150); ceiling R-T718-2: every straight front of "
                                f"the turn lies inside the drawn square, so each <= its diameter hypot(1.150, 1.150) = "
                                f"{BR.round_point(diam)} (= BE6 drawn); {n} x that" + (" x (4.50/27 - 0.030)"
                                                                                       if unit == "m2" else ""))
        out.append({"line_id": old["line_id"], "item_code": code, "element_id": old["element_id"], "drawn_flight": "MS1-T",
                    "unit": unit, "before": old["after"], "after": st})
    return out


def rs_c_rows(d, t715):
    g = d["round_stair_rs_c"]
    ri, ro = (D(str(g["inner_edge_r_m"])), DW), (D(str(g["outer_edge_r_m"])), DW)
    st_r = g["structural_check"]["st_opening_r_m"]
    assert [str(x) for x in st_r] == [str(g["inner_edge_r_m"]), str(g["outer_edge_r_m"])]
    assert g["structural_check"]["rigid_fit_max_residual_mm"] < 1e-3
    lane = D(str(g["outer_band_r_m"])) - D(str(g["inner_band_r_m"]))
    res = {}
    for kind, curt in (("faces", g["curtail"]["face"]), ("fronts", g["curtail"]["front"])):
        hi, per = D(0), []
        for ln in g["lines"][kind]:
            k = str(ln["riser"])
            off = (D(str(ln["offset_m"])), DW)
            if k in curt:
                v = R.curtail_front_at_most(start_r=(D(str(ln["r_in_m"])), DW), offset=off, r_out=ro,
                                            curtail_arc=(D(str(curt[k]["arc_m"])), DW))
            else:
                v = R.round_front_at_most(offset=off, r_in=ri, r_out=ro)
            per.append({"riser": ln["riser"], "handle": ln["handle"], "drawn_m": ln["drawn_m"],
                        "at_most_m": str(BR.round_high(v)), "curtail": curt.get(k, {}).get("handle")})
            hi = BR.add(hi, v)
        floor = R.drawn_floor([(ln["handle"], str(ln["drawn_m"])) for ln in g["lines"][kind]],
                              lane=(lane, DW) if kind == "fronts" else None)
        res[kind] = {"floor_lm": floor, "ceiling_lm": hi, "per_line": per}
    vis = riser(D("4.50"), 28) - T_TREAD
    out = []
    old_r = t715[("GF-RC99C2A:flight 1", "FIN.MARBLE.RISER")]
    lo_r = max(D(old_r["after"]["low"]), BR.mul(res["faces"]["floor_lm"], vis))
    st = R5.statement(old_r["line_id"], "RANGE", low=lo_r, high=BR.mul(res["faces"]["ceiling_lm"], vis),
                      item=old_r["after"]["item"],
                      status=OA + " (riser 4.50/28, Q-50 A cond) on " + DC + " riser faces (own read 257 .. 241 = ST "
                      "2EA .. 2DF, rigid fit 0.0 mm)",
                      cause=f"floor R-T718-3: the 12 drawn riser faces sum {BR.round_point(res['faces']['floor_lm'])} lm "
                            f"(257 1.149742 / 255 1.148281 start on the curtails, ten 1.150) x (4.50/28 - 0.030); ceiling "
                            f"R-T718-2: each face line between the stair's outline arcs 23F r 1.530511 / 23E r 2.780511 "
                            f"(= ST S-OPENING 2DE / 2DD) = 1.250367, risers 1 / 2 from their drawn start to 23E + the "
                            f"curtail face arcs 259 0.840283 / 25B 0.562992: {BR.round_high(res['faces']['ceiling_lm'])} lm")
    out.append({"line_id": old_r["line_id"], "item_code": "FIN.MARBLE.RISER", "element_id": old_r["element_id"],
                "drawn_flight": "RS-C", "unit": "m2", "before": old_r["after"], "after": st})
    old_s = t715[("GF-RC99C2A:flight 1", "FIN.STAIR.STEP_LM")]
    lo_s = max(D(old_s["after"]["low"]), res["fronts"]["floor_lm"])
    st = R5.statement(old_s["line_id"], "RANGE", low=lo_s, high=res["fronts"]["ceiling_lm"], item=old_s["after"]["item"],
                      status=DC + " (own read: front edges 256 .. 240 layer 5, radial; curtail fronts 258 / 25A)",
                      cause=f"floor R-T718-3: 12 drawn front edges inside the lane {lane} (11 x 1.150 + 256 1.200 of which "
                            f"0.050 over the outer band, role open RFI-S27) = {BR.round_point(res['fronts']['floor_lm'])}; "
                            f"ceiling R-T718-2: radial fronts between 23F / 23E = 1.250 each, steps 1 / 2 + curtail front "
                            f"arcs 258 0.949440 / 25A 0.672000: {BR.round_high(res['fronts']['ceiling_lm'])} lm")
    out.append({"line_id": old_s["line_id"], "item_code": "FIN.STAIR.STEP_LM", "element_id": old_s["element_id"],
                "drawn_flight": "RS-C", "unit": "lm", "before": old_s["after"], "after": st})
    return out, {k: {"floor_lm": str(BR.round_low(v["floor_lm"])), "ceiling_lm": str(BR.round_high(v["ceiling_lm"])),
                     "per_line": v["per_line"]} for k, v in res.items()}


def soffit_rows(t715):
    out = []
    for el, datum in (("STAIR:ST-01:soffit",
                       "no drawn geometry bounds it from above: the winder + junction soffit (1.500 m2 plan) follows the "
                       "undrawn winder subdivision D-67 (stepped or raked underside not printed, C-ST-3) and the O vs D "
                       "soffit method has no owner rule; a raked or stepped surface over a plan has no area ceiling "
                       "without its form"),
                      ("STAIR:ST-02:soffit",
                       "no drawn geometry bounds it from above: the RS-C underside form and waist are not printed "
                       "(D-08 / RFI-S27; ST p.16 'THICK.' without a value), so the helical soffit has no ceiling")):
        old = t715[(el, "FIN.STAIR.SOFFIT")]
        st = R5.statement(old["line_id"], "AT_LEAST", low=D(old["after"]["low"]), status=old["after"]["status"],
                          item=old["after"]["item"], cause=old["after"]["cause"] + "; T-718: " + datum)
        out.append({"line_id": old["line_id"], "item_code": "FIN.STAIR.SOFFIT", "element_id": el, "unit": "m2",
                    "before": old["after"], "after": st})
    return out


def build():
    d, led, side = load()
    t715 = {(l["element_id"], l["item_code"]): l for l in led["lines"]}
    pieces = datum_rows(d, led, side)
    fv = fv715_1(d)
    lines = turn_rows(d, t715)
    rc, rc_detail = rs_c_rows(d, t715)
    lines += rc + soffit_rows(t715)
    return {"schema": "T718_STAIR_FINISH_ROUND2_V1", "candidate": "ARCH_TAKEOFF_V3.0.70", "rules": R.RULES,
            "drawn_sha256_16": hashlib.sha256(DRAWN_JSON.read_bytes()).hexdigest()[:16],
            "f_v715_1": fv, "cut_pieces": pieces, "lines": lines, "rs_c_detail": rc_detail,
            "unchanged": "every other T-715 line (79 of 85) keeps its T-715 statement; the 26 skirting form lines of the "
                         "13 walled pieces stay CONDITIONAL_ON_FORM (ORR-007): this run confirms 10 cut pieces by handle"}


def write_md(led):
    fv = led["f_v715_1"]
    L = ["# T-718 stair finishes round 2 (research, unwired; candidate V3.0.70 line ids)", "",
         "## F-V715-1 (MS2-L skirting)", "",
         f"Walled plan: front-edge datum {fv['walled_plan_front_edge_m']} m, riser-face datum "
         f"{fv['walled_plan_riser_face_m']} m; window {fv['window_plan_front_edge_m']} / {fv['window_plan_riser_face_m']} m; "
         f"difference {fv['difference_m']} = nosing projection {fv['nosing_projection_m']}. {fv['status']}.", "",
         "Cause: " + fv["cause"] + ".", "", "Reading: " + fv["physical_reading"] + ".", "", "Verdict: " + fv["verdict"] + ".",
         "", "## Cut pieces, both data (plans m, risers by face)", "",
         "| piece | front-edge plan | riser-face plan | risers | T-410 plan / risers | agree | T-715 lines |",
         "|---|---|---|---|---|---|---|"]
    for p in led["cut_pieces"]:
        tl = ", ".join(f"{k} {v['class']} {v['value'] or ('<= ' + v['high'] if v['high'] else '')}"
                       for k, v in p["t715_lines"].items()) or "none (window / held stretch)"
        L.append(f"| {p['piece']} | {p['plan_front_edge_m']} | {p['plan_riser_face_m']} | {p['risers']} | "
                 f"{p['t410_plan_m']} / {p['t410_risers']} | {p['t410_agrees_front_edge']} | {tl} |")
    L += ["", "## Lines before / after (never summed)", "",
          "| line | item | element | unit | before | after | status | cause / item |", "|---|---|---|---|---|---|---|---|"]
    for r in led["lines"]:
        b, a = r["before"], r["after"]
        bv = f"{b['class']} >= {b['low']}"
        av = f"{a['class']} {a['low'] or ''}{' .. ' + a['high'] if a['high'] else ''}"
        L.append(f"| {r['line_id']} | {r['item_code']} | {r['element_id']} | {r['unit']} | {bv} | {av} | {a['status']} | "
                 f"{a['cause']} ; item {a['item']} |")
    L += ["", "RS-C per line: " + json.dumps(led["rs_c_detail"]), "", led["unchanged"] + "."]
    return "\n".join(L) + "\n"


def main(argv):
    led = build()
    js = json.dumps(led, indent=1, sort_keys=True) + "\n"
    md = write_md(led)
    if "--write" in argv:
        OUT_JSON.parent.mkdir(exist_ok=True)
        OUT_JSON.write_text(js)
        OUT_MD.write_text(md)
    elif "--check" in argv:
        assert OUT_JSON.read_text() == js and OUT_MD.read_text() == md, "outputs differ from the committed out/"
        print("REPRODUCED")
    for r in led["lines"]:
        a = r["after"]
        print(r["item_code"], r["element_id"], a["class"], a["low"], a["high"])
    for p in led["cut_pieces"]:
        print(p["piece"], p["plan_front_edge_m"], p["plan_riser_face_m"], p["risers"], p["t410_agrees_front_edge"])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
