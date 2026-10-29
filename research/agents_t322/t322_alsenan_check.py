"""T-322 on the development villa: the FF raft and lift-pit component ledger (LIFT_BASE_LEDGER_V1) from the own-read
input ALSENAN_LIFT_BASE_INPUT.json (values, handles, page references only), and the reconciliation of the merged
ledgers that disagree on the FF blinding (F-T320-03: T-233 2.256 m3 vs T-170 HELD), with the closures against
T-233 (CONC.FOOTING / CONC.BLINDING components), T-170 (pits), T-219 (lift underlay), T-204 (ring) and T-320 (Z1).

Run: python3 -I research/agents_t322/t322_alsenan_check.py  ->  LEDGER_T322.csv, summary.json beside this file.
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RES = HERE.parent
sys.path.insert(0, str(HERE))
import lift_base_ledger_v1 as X  # noqa: E402


def _load(p):
    return json.loads((RES / p).read_text())


def _csv(p):
    with open(RES / p, newline="") as f:
        return list(csv.DictReader(f))


def p14_scaled_projection(inp):
    v = inp["p14_vector_read"]
    pairs = [(v["screed"]["printed_m"], v["screed"]["drawn_pt"]), (v["blinding"]["printed_m"], v["blinding"]["drawn_pt"])]
    beyond_face = [X.scaled_reading(pairs, d) for d in v["projection_beyond_footing_face_pt"]]
    beyond_board = [X.scaled_reading(pairs, d) for d in v["projection_beyond_board_pt"]]
    board = [X.scaled_reading(pairs, d) for d in v["board_drawn_pt"]]
    k = beyond_face[0]["scale_paper_per_m"]
    return {"scale_pt_per_m": k, "scale_ratio_1_to": 1000.0 / (k * 25.4 / 72.0),
            "beyond_footing_face_m": [r["value_m"] for r in beyond_face],
            "beyond_board_m": [r["value_m"] for r in beyond_board],
            "board_m": [r["value_m"] for r in board],
            "membrane_under_screed_m": X.scaled_reading(pairs, v["membrane_under_screed_drawn_pt"])["value_m"]}


def spec_from(inp, sc):
    gov = inp["governing_detail"]
    p13 = inp["p13_projection"]
    pr = round(sc["beyond_footing_face_m"][0], 3)
    return {
        "unit": inp["unit"], "governing_detail": gov,
        "raft": {"rect": inp["raft"]["rect"], "schedule": inp["raft"]["schedule"], "H": inp["raft"]["H"],
                 "source": inp["raft"]["handle"] + "; " + inp["raft"]["schedule_source"]},
        "blinding": inp["blinding"],
        "readings_p": [
            {"value": p13["value"], "kind": p13["kind"], "basis": p13["source"] + " (a typical detail of another "
             "element type; FF has its own governing detail)"},
            {"value": pr * 1000.0, "kind": X.SCALED, "basis": "ST p.14 drawn edge, scale 1:%.1f proven by the printed "
             "'5cm Screed' and '10cm Plain con.' (not dimensioned)" % sc["scale_ratio_1_to"]}],
        "underlay": [dict(u, t=(None if u["t"] is None else dict(u["t"]))) for u in inp["underlay"]],
        "ring": dict(inp["ring"], source=inp["ring"]["handles"] + "; " + inp["ring"]["column_handles"]),
        "pit_height": inp["pit_height"],
        "side_buildup": inp["side_buildup"],
    }


def run():
    inp = json.loads((HERE / "ALSENAN_LIFT_BASE_INPUT.json").read_text())
    sc = p14_scaled_projection(inp)
    led = X.build(spec_from(inp, sc))
    comp = {c["id"]: c for c in led["components"]}

    # merged ledgers (read only; by column name)
    rows233 = [r for r in _csv("agents_t233/LEDGER_T233.csv") if r["outline"] == "1B2B"]
    ff_foot_233 = next(float(r["m3"]) for r in rows233 if r["line"] == "CONC.FOOTING")
    ff_blind_233 = next(float(r["m3"]) for r in rows233 if r["line"] == "CONC.BLINDING")
    s320 = _load("agents_t320/summary.json")
    rows320 = [r for r in _csv("agents_t320/LEDGER_T320.csv") if r["group"].startswith("PIT:FTG:SH10:FF@")]
    rows219 = [r for r in _csv("agents_t219/LEDGER_T219.csv") if r["outline"] == "1B2B"]
    rows204 = {r["component"]: r for r in _csv("agents_t204/LEDGER_T204.csv")}
    rows170 = [r for r in _csv("agents_t170/LEDGER_T170.csv") if r["id"].startswith("FTG:SH10:FF@")]

    raft = comp["RAFT"]["value"]
    bl = comp["BLINDING"]
    t233_blind_line = s320["t233_closure"]["blinding_line_m3"]            # 14.990438 (T-233 measured)
    t233_foot_line = s320["t233_closure"]["footing_line_m3"]               # 64.304
    pits24_inside = s320["pits24_blinding_inside_plot_m3"]
    corrected_blind_measured = round(t233_blind_line - ff_blind_233, 6)
    screed = comp["UNDERLAY:screed:VOL"]["value"]
    s219_screed = next(float(r["qty"]) for r in rows219 if r["item"] == "SCREED.LIFT_PIT_BASE" and r["unit"] == "m3")
    s219_area = next(float(r["qty"]) for r in rows219 if r["item"] == "SCREED.LIFT_PIT_BASE" and r["unit"] == "m2")
    ring204 = float(rows204["PIT_RING_PLAN_NET"]["value"])
    readings = {r["kind"]: r["volume_m3"] for r in bl["readings"]}
    res = {
        "method": X.METHOD_ID,
        "p14_scale": sc,
        "components": led["components"],
        "totals": led["totals"],
        "F_T320_03": {
            "t233_ff_blinding_m3": ff_blind_233,
            "t170_ff_neat_status": [r["neat_status"] + " / " + r["why"] for r in rows170],
            "t320_ff_blinding_row": [r["range_m3"] + " " + r["status"] for r in rows320 if r["kind"] == "BLINDING"],
            "cause": ("INHERITED OFFSET: T-233 applied the p.13 TYPICAL isolated-footing projection 0.10 (projection_m "
                      "0.1 for all 26 outlines) to FF, whose governing detail is p.14 (lift with isolated footing): p.14 "
                      "prints the blinding thickness ('10cm Plain con.') and draws the blinding beyond the side "
                      "membrane + protection board, with NO projection dimension. T-170's HELD is the correct reading."),
            "corrected_status": bl["status"], "corrected_value": bl["value"],
            "at_least_m3": bl["low"], "readings_m3": readings,
            "impact_between_readings_m3": round(readings[X.SCALED] - readings[X.INHERITED], 6),
            "per_cm_projection_m3_first_order": round(0.10 * 2 * (4.6 + 4.5) * 0.01, 6),
        },
        "closure": {
            "t233_footing_FF_m3": ff_foot_233, "ledger_raft_m3": raft,
            "raft_residual_m3": round(raft - ff_foot_233, 6),
            "t233_blinding_measured_m3": t233_blind_line,
            "blinding_measured_after_T322_m3": corrected_blind_measured,
            "t320_24_pits_inside_plot_m3": pits24_inside,
            "blinding_residual_vs_t320_m3": round(corrected_blind_measured - pits24_inside, 6),
            "t219_screed_m3": s219_screed, "ledger_screed_m3": screed, "screed_residual_m3": round(screed - s219_screed, 6),
            "t219_screed_area_m2": s219_area, "ledger_raft_plan_m2": led["totals"]["raft_plan_m2"],
            "t204_ring_net_m2": ring204, "ledger_ring_net_m2": led["totals"]["ring_net_m2"],
            "ring_residual_m2": round(led["totals"]["ring_net_m2"] - ring204, 6),
            "t320_z1_established_m3": s320["z1_established_m3"],
            "z1_change_m3": 0.0,
            "z1_note": ("T-320 Z1 holds every FF component (below-EG share depends on the unprinted pit depth); this "
                        "ledger moves no value into Z1: residual 0.000. Its FF blinding hold changes basis: 0 .. 2.256 "
                        "(T-233 offset) -> HELD, AT_LEAST 2.070 if wholly below EG, upper end not printed."),
        },
    }
    return res, led


def write():
    res, led = run()
    with open(HERE / "LEDGER_T322.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["element", "id", "component", "unit", "value", "low", "high", "status", "owner_line", "held",
                    "source", "note"])
        for c in led["components"]:
            w.writerow(["FF 1B2B / LIFT-01", c["id"], c["component"], c["unit"], c["value"], c["low"], c["high"],
                        c["status"], c["owner_line"], "; ".join(c["held"]), c["source"], c["note"]])
    (HERE / "summary.json").write_text(json.dumps(res, indent=1, sort_keys=True) + "\n")
    return res


if __name__ == "__main__":
    r = write()
    print(json.dumps({"F_T320_03": r["F_T320_03"], "closure": r["closure"], "p14_scale": r["p14_scale"]}, indent=1))
