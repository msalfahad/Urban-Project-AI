"""T-184 Alsenan ledger: every staircase, re-derived from ALSENAN_STAIR_INPUT.json with t184_stair_inventory, and the
reconciliation engine (released baseline A) vs own vs freelancer, component by component.

Run: python3 -I research/agents_t184/t184_alsenan_ledger.py [--out FILE.json]   (stdlib only; reads no drawing)
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("t184_stair_inventory", HERE / "t184_stair_inventory.py")
SI = importlib.util.module_from_spec(_spec)
sys.modules.setdefault("t184_stair_inventory", SI)
_spec.loader.exec_module(SI)


def load(path=HERE / "ALSENAN_STAIR_INPUT.json"):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def stair_ledger(st, floor_levels):
    parts, rows = [], []
    for f in st["flights"]:
        c = SI.flight_concrete(f["steps_counted"], f["riser"], f["going"], f["goings"], f["width"], f["waist"])
        for k in ("steps", "waist"):
            parts.append((f"{f['id']} {k}", c[k]))
            rows.append(dict(part=f"{f['id']} {k}", m3=c[k]))
    for l in st["landings"]:
        lnd = SI.Landing(l["id"], l["level"], (0, 0, 0, 0), l["thickness"], l.get("inside_floor_slab", False))
        owner = SI.landing_owner(lnd, floor_levels)
        v = SI.landing_concrete(l["length"], l["width"], l["thickness"], l.get("deduct_m2", 0.0))
        rows.append(dict(part=f"{l['id']} landing", m3=v, owner=owner))
        if owner == "STAIR":
            parts.append((f"{l['id']} landing", v))
    tot = SI.stair_total(parts)
    ded = sum(d["m3"] for d in st["deductions_q62"])
    held = [dict(id=h["id"], candidate_m3=h["candidate_m3"], why=h["why"]) for h in st["held_parts"]]
    named = {h["id"].split("-")[0] for h in held}
    held += [dict(id=k, candidate_m3=None, why="input not printed") for k in tot["held"] if k.split()[0] not in named]
    return dict(stair_id=st["stair_id"], name=st["name"], serves=st["serves"], beside_lift=st["beside_lift"],
                rows=rows, measured_m3=tot["measured_m3"], q62_deducted_m3=ded,
                net_m3=tot["measured_m3"] - ded, held=held)


def round_stair_lengths():
    """the drawn lengths of ST-02 (for the freelancer's 16.4 m): T-111 geometry, tread ends r 1.581 / 2.731, stringers
    1.531 / 2.781, walking line 2.156, 12 x 7.79 deg, straight 3.00 + landing 1.15 + short 1.20, rise 4.50."""
    sweep = math.radians(12 * 7.79)
    straight = 3.00 + 1.15 + 1.20
    walk = 2.156 * sweep + straight
    outer = 2.781 * sweep + straight
    return dict(walking_line_plan_m=walk, walking_line_sloped_m=math.hypot(walk, 4.50),
                outer_string_plan_m=outer, outer_string_sloped_m=math.hypot(outer, 4.50),
                both_strings_plan_m=(1.531 + 2.781) * sweep + 2 * straight)


def reconcile(data, led):
    fr = data["freelancer"]
    by = {s["stair_id"]: s for s in led}
    st1 = by["ST-01"]
    fl = [r for r in st1["rows"] if r["part"].split()[0] in ("MS1-L", "MS1-U", "MS2-L", "MS2-U")]
    flights_m3 = sum(r["m3"] for r in fl)
    lands_m3 = sum(r["m3"] for r in st1["rows"] if r.get("owner") == "STAIR")
    flights = data["stairs"][0]["flights"]
    sloped = [math.hypot(f["goings"] * f["going"], f["goings"] * f["riser"]) for f in flights]
    w = 1.20
    his_len, his_t = 4 * 5.3, 0.28
    a_len = w * his_t * (his_len - sum(sloped))                       # his 5.3 m flights vs the drawn sloped lengths
    t_eq = (flights_m3 - st1["q62_deducted_m3"]) / (w * sum(sloped))  # own flight m3 per m2 of sloped flight
    b_thk = w * sum(sloped) * (his_t - t_eq)
    his_land_area, own_land_area = 3 * 1.2 * 1.4, 1.20 * 1.20 + 2.50 * 1.20
    c_area = (his_land_area - own_land_area) * 0.20
    c_thk = own_land_area * (0.20 - 0.16)
    eng = {l["stair"]: l["m3"] for l in data["engine_baseline_A"]["lines"]}
    rl = round_stair_lengths()
    return dict(
        ST01=dict(freelancer=fr["main_flights"]["m3"] + fr["main_landings"]["m3"], own_net=st1["net_m3"],
                  own_flights_net=flights_m3 - st1["q62_deducted_m3"], own_landings=lands_m3,
                  engine=eng["ST-01 GF -> 1F"], engine_scope="GF -> 1F only (1F -> 2F folded away, D-T184-1)",
                  flights_sloped_m=sloped, flight_equiv_thickness_m=t_eq,
                  his_flights_minus_own=dict(length_5_3_vs_drawn=a_len, thickness_0_28_vs_drawn=b_thk,
                                             residual=fr["main_flights"]["m3"] - (flights_m3 - st1["q62_deducted_m3"])
                                             - a_len - b_thk),
                  his_landings_minus_own=dict(area_5_04_vs_4_44=c_area, thickness_0_20_vs_0_16=c_thk,
                                              residual=fr["main_landings"]["m3"] - lands_m3 - c_area - c_thk)),
        ST01b=dict(freelancer=None, own_net=by["ST-01b"]["net_m3"], engine=None),
        ST02=dict(freelancer=fr["stair_2"]["m3"], own_net=by["ST-02"]["net_m3"], engine=eng["ST-02 (part)"],
                  held=[h["id"] for h in by["ST-02"]["held"]], lengths=rl,
                  his_length_unexplained_m=16.4 - rl["outer_string_sloped_m"]),
        ST03=dict(freelancer=fr["entrance"]["m3"], own_net=by["ST-03"]["net_m3"], engine=eng["ST-03"],
                  his_run_1_8_vs_drawn_plan_1_2=1.8 - 4 * 0.30),
        DOMES=dict(freelancer=fr["domes"]["m3"], engine=eng["DOMES (T-185)"], own="T-185"),
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out")
    a = ap.parse_args()
    data = load()
    fl = data["floor_levels"]
    floors = [fl["GF"], fl["1F"], fl["2F"]]
    led = [stair_ledger(s, floors) for s in data["stairs"]]
    rec = reconcile(data, led)
    for s in led:
        print(f"{s['stair_id']:7s} measured {s['measured_m3']:.4f} - Q-62 {s['q62_deducted_m3']:.4f} = "
              f"{s['net_m3']:.4f} m3 ; held {[h['id'] for h in s['held']]}")
    print(json.dumps(rec, indent=1, default=float))
    if a.out:
        Path(a.out).write_text(json.dumps(dict(stairs=led, reconciliation=rec), indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
