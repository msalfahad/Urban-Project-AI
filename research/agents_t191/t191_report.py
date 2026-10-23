"""T-191 report: rev2 pool steel per bar mark (both printed populations) and the step-by-step delta from rev1 (T-166).

Reads research/agents_t191/ALSENAN_POOL_STEEL_INPUT.json and research/agents_t166/T166_STEEL.csv (rev1, merged);
writes research/agents_t191/T191_STEEL.csv and T191_SUMMARY.json.  Research only, unwired.

Delta steps per mark (kg; low / high ends of rev2):
    S0  rev1 (T-166, reading A): verticals 1.55 m on the FACE perimeters, hoops 8 over 0.40 + 1.15 = 1.55 m
    S1  the verified height only: verticals base underside -> rim 1.60 m, hoops over the wall above the base top
        1.20 m (6 .. 7), still face to face and rev1's counts
    S2  bar lines and the counting meaning: centrelines at the printed soil cover / bounded non-soil cover, hoops
        inside the verticals, mesh with an edge bar each side (N = ceil(L_eff / s) + 1), loops N = ceil(P / s)
    S3  = rev2: the drawn shapes (water-face verticals: top hook + closed box in the base)
"""

from __future__ import annotations

import csv
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
_spec = importlib.util.spec_from_file_location("t191_pool_steel", HERE / "t191_pool_steel.py")
S = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(S)

REV1_MAP = {"wall vertical, outer face": "WV_OUT", "wall vertical, inner face": "WV_IN",
            "wall horizontal hoops, outer face": "WH_OUT", "wall horizontal hoops, inner face": "WH_IN",
            "floor bottom, section-line bars": "FB_MAIN", "floor bottom, dot-row bars": "FB_DIST",
            "floor top, section-line bars": "FT_MAIN", "floor top, dot-row bars": "FT_DIST",
            "rim bars at the wall top": "RIM", "corner bars floor / wall": "CORNER"}
POP_OF_REV1 = {"POOL R1 deep-end population": "R1_deep_end_detail",
               "POOL R2 shallow-end population": "R2_shallow_end_detail"}


def rev1_rows():
    out = {}
    with open(ROOT / "research" / "agents_t166" / "T166_STEEL.csv", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["element"] in POP_OF_REV1 and r["part"] in REV1_MAP and r["kg_A"]:
                out.setdefault(POP_OF_REV1[r["element"]], {})[REV1_MAP[r["part"]]] = r
    return out


def _mark_base(mark):
    """FB_MAIN_X -> FB_MAIN"""
    return "_".join(mark.split("_")[:2]) if mark.startswith(("FB_", "FT_")) else mark


def _by_base(rows):
    d = {}
    for r in rows:
        d[_mark_base(r["mark"])] = d.get(_mark_base(r["mark"]), 0.0) + r["kg"]
    return d


def run():
    inp = json.load(open(HERE / "ALSENAN_POOL_STEEL_INPUT.json", encoding="utf-8"))
    g = S.load(inp)
    outer, wt, bt, wh, cs = g["outer"], g["wall_t"], g["base_t"], g["wall_h"], g["c_s"]
    rev1 = rev1_rows()
    led = S.ledger(inp)
    summary = {"wall_h_m": wh, "unit_mass": led["unit_mass"], "populations": {}}
    csv_rows = []
    for name, pop in inp["populations"].items():
        rg = S.population_range(pop, outer, wt, bt, wh, cs, g["c_n"], main_dirs=g["main_dirs"])
        ends = {"low": rg["low"], "high": rg["high"]}
        straight = {k: dict(v, shape="STRAIGHT") if k == "WV_IN" else v for k, v in pop.items()}
        s2 = {}
        for e, rd in ends.items():
            rows, _ = S.population_rows(straight, outer, wt, bt, wh, cs, rd["c_n"], hoops=rd["hoops"],
                                        main_dir=rd["main_dir"])
            s2[e] = _by_base(rows)
        s3 = {e: _by_base(rd["rows"]) for e, rd in ends.items()}
        steps = {}
        P_face = {"WV_OUT": outer.perimeter(), "WH_OUT": outer.perimeter(),
                  "WV_IN": outer.offset(wt).perimeter(), "WH_IN": outer.offset(wt).perimeter()}
        for mk, r1 in rev1[name].items():
            d = int(r1["d"])
            s0 = float(r1["kg_A"])
            if mk in ("WV_OUT", "WV_IN"):
                s1 = (int(r1["n_A"]) * (bt + wh) * S.kg_per_m(d),) * 2
            elif mk in ("WH_OUT", "WH_IN"):
                lo, hi = S.count_hoops(wh, 0.20)
                s1 = (lo * P_face[mk] * S.kg_per_m(d), hi * P_face[mk] * S.kg_per_m(d))
            else:
                s1 = (s0, s0)
            steps[mk] = {"d": d, "S0_rev1_A": round(s0, 3), "S1_height": [round(x, 3) for x in s1],
                         "S2_barlines_counts": [round(s2["low"][mk], 3), round(s2["high"][mk], 3)],
                         "S3_rev2_shapes": [round(s3["low"][mk], 3), round(s3["high"][mk], 3)]}
            csv_rows.append({"population": name, "mark": mk, "d": d, **{k: (v if not isinstance(v, list)
                             else f"{v[0]}..{v[1]}") for k, v in steps[mk].items() if k != "d"}})
        tot = {k: [round(sum((v[k] if isinstance(v[k], list) else [v[k], v[k]])[i] for v in steps.values()), 2)
                   for i in (0, 1)] for k in ("S0_rev1_A", "S1_height", "S2_barlines_counts", "S3_rev2_shapes")}
        p = led["populations"][name]
        summary["populations"][name] = {"kg_net_range": [p["kg_low"], p["kg_high"]],
                                        "kg_exact_density_range": [p["kg_exact_density_low"],
                                                                   p["kg_exact_density_high"]],
                                        "low_reading": p["low_reading"], "high_reading": p["high_reading"],
                                        "held_legs": p["held_legs"],
                                        "laps_kg_range_procurement": p["laps_kg_range_procurement"],
                                        "delta_steps_per_mark": steps, "delta_totals": tot,
                                        "readings": [{"c_n": round(r["c_n"], 3), "hoops": r["hoops"],
                                                      "main_dir": r["main_dir"], "kg": round(r["kg"], 2)}
                                                     for r in rg["readings"]],
                                        "marks": p["marks"], "status": p["status"]}
    with open(HERE / "T191_STEEL.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(csv_rows[0]))
        w.writeheader()
        w.writerows(csv_rows)
    with open(HERE / "T191_SUMMARY.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=1, ensure_ascii=False)
    return summary


if __name__ == "__main__":
    s = run()
    for n, p in s["populations"].items():
        print(n, p["kg_net_range"], "laps", p["laps_kg_range_procurement"], "legs", p["held_legs"])
        print("  totals", p["delta_totals"])
        for mk, v in p["delta_steps_per_mark"].items():
            print("  ", mk, v)
        for r in p["readings"]:
            print("    reading", r)
    sys.exit(0)
