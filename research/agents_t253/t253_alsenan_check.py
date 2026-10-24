"""T-253 Alsenan check (committed inputs only): boundary G.B at N.G. run by run, the outer-ground datum, the main-house
exterior runs at that datum, the annex depth conflict, the 3 court runs, the consultant rows narrowed to exact runs and
the deltas for lane I (T-254). Nothing applied to any engine, candidate or released line.

    python3 -I research/agents_t253/t253_alsenan_check.py          # writes LEDGER_T253.csv and summary.json

Inputs: research/agents_t253/ALSENAN_BOUNDARY_INPUT.json (t253_extract.py on Drive "Alsenan chalet project" /
"ST7757 dxf.dxf", sha 9f9d1179), research/agents_t242/LEDGER_T242.csv and ALSENAN_GROUND_INPUT.json (merged 9455a63d,
read-only), and the printed values below, each with its drawing reference (PDF pages read visually this run).
"""
from __future__ import annotations

import csv
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import boundary_court as BC  # noqa: E402

T242 = os.path.join(ROOT, "research", "agents_t242")

# ---- printed values (drawing references; nothing typed from the freelancer or the engine)
P14_GB_B, P14_GB_D = 0.20, 0.40          # ST7757.pdf p.14 TYPICAL BOUNDARY WALL plan "GROUND BEAM (20x40)"; A-A "40"
P14_COL_A, P14_COL_B = 0.20, 0.30        # p.14 "(20x30) R.C COLUMNS 4 d14", spacing "SEE ARCH PLAN"
P13_MIN_DEPTH = 0.30                     # p.13: the shallowest printed ground-beam section (less than 2.5 m, 30 x 30)
TOP_MAIN, TOP_ANNEX = 0.95, 0.25         # T-214 (merged): FFL +1.00 / +0.30 less the 0.05 build-up, DRAWING-CONFIRMED
GROUND_READINGS = [
    {"level": 0.00, "kind": "NATURAL", "source": "ST7757 p.3 (DXF layer 3, 6 level blocks '+-0.00' outside the plot "
                                                  "line on all four sides)"},
    {"level": 0.00, "kind": "NATURAL", "source": "architectural GF plan p7757_arch_sheet03.pdf: '+-0.00' marks outside "
                                                  "the plot on the street, both neighbour and sea sides"},
    {"level": 0.00, "kind": "NATURAL", "source": "architectural section B-B (Pages_11-12, p.11): ground line '+-0.00' at "
                                                  "the street end beside the annex and at the far plot end"},
    {"level": 0.15, "kind": "FINISHED_PAVING", "on": 0.00,
     "source": "section B-B: the court '+0.15' is a hatched paving band drawn on the earth line, whose underside is "
               "level with the '+-0.00' ground line (pixel profile at 300 dpi: band 0.15 .. 0.19 m over that line)"},
    {"level": 0.15, "kind": "FINISHED_PAVING", "on": 0.00,
     "source": "ST7757 p.14 section A-A: 'PLAIN CONC.' 15 drawn above the G.B top at 'N.G. LEVEL'"},
]
COURT_CANDIDATES = {          # T-242 candidate sets, with the exterior end at the established datum only (0.80 retired)
    "178+7DB#1": [0.40, 0.95],
    "185+7C7#1": [0.30, 0.40, 0.95],
    "1811+1812#1": [0.30, 0.40],
}
FREELANCER_BOUNDARY = {"L_m": 42.0, "b_m": 0.30, "d_m": 0.60, "m3": 7.56,
                       "cells": "RC workbook sheet 'الشناجات' boundary-beam row (T-242 committed cells)"}


def r4(v):
    return None if v is None else round(float(v) + 0.0, 4)


def load():
    inp = json.load(open(os.path.join(HERE, "ALSENAN_BOUNDARY_INPUT.json"), encoding="utf-8"))
    led = list(csv.DictReader(open(os.path.join(T242, "LEDGER_T242.csv"), encoding="utf-8")))
    gin = json.load(open(os.path.join(T242, "ALSENAN_GROUND_INPUT.json"), encoding="utf-8"))
    return inp, led, gin


def _adj(s):
    if not s:
        return 0.0
    lo, hi = s.split("..")
    if float(lo) != float(hi):
        raise BC.BoundaryCourtError("end adjustment is a range: not a single reading")
    return float(lo)


def main(write=True):
    inp, led, gin = load()
    rows = []

    # ---- (a) boundary G.B at N.G., run by run
    END_KIND = {"COLUMN": "COLUMN", "POOL_WALL": "POOL_WALL", "COLUMN+GROUND_BEAM_FACE": "COLUMN"}
    b_runs = []
    for b in inp["boundary_bands"]:
        for r in b["runs"]:
            ends = []
            for e in r["ends"]:
                if e["kind"] == "CORNER":
                    ends.append({"face": "corner (continues into the next run)", "status": BC.CALCULATED})
                    continue
                if e["kind"] in END_KIND:
                    t = BC.end_in_3d(END_KIND[e["kind"]], beam_top=0.00, beam_bottom=-0.40)
                    ends.append({"face": f"{e['kind']} {'/'.join(e['refs'])}", **t})
                elif e["kind"] == "GROUND_BEAM_FACE":
                    # the annex exterior beam 10B+7D1 (top +0.25): its soffit is the annex CONFLICT; below it the
                    # neighbour-side black brick (ST p.1 note 2). The plan face is drawn; the 3-D member is not shown.
                    ends.append({"face": f"ground-beam face {'/'.join(e['refs'])} (annex exterior 10B+7D1)",
                                 "status": BC.HELD, "ends": False,
                                 "why": "3-D member at this face: the annex beam if deeper than 0.25 m (annex CONFLICT), "
                                        "else the neighbour-side brick below it; the plan length is unaffected"})
                else:
                    ends.append({"face": "nothing drawn", **BC.end_in_3d("NONE")})
            v = BC.boundary_run(r["run_id"], r["length_m"], P14_GB_B, P14_GB_D, d_source="ST7757 p.14 A-A '40'")
            v["ends"] = ends
            b_runs.append(v)
            rows.append({"item": r["run_id"], "component": "BOUNDARY-GB at N.G.", "L_m": r["length_m"],
                         "b_m": P14_GB_B, "d_m": P14_GB_D, "status": "DRAWING-CONFIRMED (" + v["status"] + ")",
                         "value_m3": r4(v["value_m3"]), "low_m3": "", "high_m3": "",
                         "basis": f"{r['axis']} run, {r['corners_owned']} corner square(s) owned; ends: "
                                  + "; ".join(f"{x['face']} -> {x['status']}" for x in ends)})
    # openings drawn across the band (gate, doors) are listed in the input; the band hatch is continuous under them
    share = BC.column_share(None, P14_COL_A, P14_COL_B, P14_GB_D)
    bline = BC.boundary_line(b_runs, share)
    rows.append({"item": "BOUNDARY columns 20x30 inside the beam", "component": "BOUNDARY-GB column share",
                 "L_m": "", "b_m": "", "d_m": P14_GB_D, "status": share["status"], "value_m3": "",
                 "low_m3": "", "high_m3": "", "basis": f"{share['each_m3']} m3 per column; " + share["why"]})
    band_len = sum(r["length_m"] for b in inp["boundary_bands"] for r in b["runs"])
    band_area = sum(b["plan_m2"] for b in inp["boundary_bands"])

    # ---- outer ground datum and the exterior depths
    datum = BC.outer_ground_datum(GROUND_READINGS)
    d_main = BC.exterior_depth(TOP_MAIN, datum, P13_MIN_DEPTH)
    d_annex = BC.exterior_depth(TOP_ANNEX, datum, P13_MIN_DEPTH)
    main_rows = [r for r in led if r["component"].startswith("GB-EXTERIOR") and r["part"] == "MAIN"]
    annex_rows = [r for r in led if r["component"].startswith("GB-EXTERIOR") and r["part"] == "ANNEX"]
    arcs = {a["arc_band"]: a for a in gin["arc_bands"]}

    def plan_m2(r):
        if r["run"].startswith("ARC:"):
            return arcs[r["run"]]["net_plan_m2"]
        return float(r["L_m"]) * float(r["b_m"]) + _adj(r["end_adjust_m2"])
    main_tot = 0.0
    for r in main_rows:
        v = round(plan_m2(r) * d_main["value_m"], 6)
        main_tot += v
        rows.append({"item": r["run"], "component": "GB-EXTERIOR MAIN at the N.G. datum", "L_m": r["L_m"],
                     "b_m": r["b_m"], "d_m": d_main["value_m"], "status": "DRAWING-CONFIRMED (proposal; T-242 HELD "
                     "D-35)", "value_m3": r4(v), "low_m3": r["low_m3"], "high_m3": r["high_m3"],
                     "basis": f"plan {plan_m2(r):.4f} m2 x (top +0.95 - N.G. +-0.00); T-242 range {r['low_m3']} .. "
                              f"{r['high_m3']}"})
    annex_lit = 0.0
    for r in annex_rows:
        v = round(plan_m2(r) * d_annex["literal_m"], 6)
        annex_lit += v
        rows.append({"item": r["run"], "component": "GB-EXTERIOR ANNEX (CONFLICT)", "L_m": r["L_m"], "b_m": r["b_m"],
                     "d_m": "", "status": "CONFLICT", "value_m3": "", "low_m3": r4(v), "high_m3": "",
                     "basis": f"literal reading {d_annex['literal_m']:.2f} m = {v:.4f} m3; section reading: no printed "
                              f"depth (no value); T-242 literal 0.10 .. 0.25 narrowed to 0.25 by the datum"})

    # ---- (b) court runs
    spans = {s["span_id"]: s for s in gin["spans"]}
    court_on_boundary = {t["line"] for t in inp["ground_beam_lines_ending_on_boundary"] if t["kind"] == "END_ON_FACE"}
    court = []
    for rid, cands in COURT_CANDIDATES.items():
        s = spans[rid]
        lines = set(s["handles"])
        end_kind = s["end"]["kind"]
        ends_ok = end_kind != "FREE_END" or bool(lines & court_on_boundary)
        c = BC.court_run(rid, s["face_to_face_m"], s["width_m"], ends_ok, cands)
        c["end_reading"] = ("ends on the boundary band face (7FE, band continuous across the run's 0.30 width): "
                            "plan length closed; 3-D support with the section (HELD)"
                            if end_kind == "FREE_END" and lines & court_on_boundary else
                            f"{s['start']['kind']} {'/'.join(s['start']['refs'])} -> {end_kind} "
                            f"{'/'.join(s['end']['refs'])}")
        court.append(c)
        rows.append({"item": rid, "component": "GB-COURT", "L_m": c["L_m"], "b_m": s["width_m"], "d_m": "",
                     "status": "HELD", "value_m3": "", "low_m3": c["low_m3"], "high_m3": c["high_m3"],
                     "basis": f"candidates {c['candidates_m']}; {c['end_reading']}"})

    # ---- (d) consultant rows narrowed to exact runs (from the merged T-242 ledger)
    d33 = sorted(r["run"] for r in led if "D-33" in r["reasons"])
    d34 = sorted(r["run"] for r in led if "D-34" in r["reasons"])
    d35_annex = sorted(r["run"] for r in annex_rows)
    t217 = sorted(r["run"] for r in led if r["status"] == "CONFLICT" and r["component"] == "GB-INTERIOR")

    def rng(names):
        lo = sum(float(r["low_m3"] or 0) for r in led if r["run"] in names)
        hi = sum(float(r["high_m3"] or 0) for r in led if r["run"] in names)
        return r4(lo), r4(hi)
    consultant = {
        "D-33": {"runs": d33, "range_m3": rng(d33),
                 "question": "Do the p.13 ground-beam sections (printed 'without concentrated load') apply to a ground "
                             "beam that receives another ground beam between its supports? If not, give the section of "
                             "these runs."},
        "D-34": {"runs": d34, "range_m3": rng(d34),
                 "question": "For a ground beam shorter than 2.5 m (both 'less than 2.5 m' 30x30 and 'less than 5 m' "
                             "30x40 hold), which section applies, and is the length class read face to face?"},
        "D-35 (annex only)": {"runs": d35_annex, "literal_m3": r4(annex_lit),
                              "question": "The annex exterior ground beams (top +0.25, natural ground +-0.00) give 0.25 m "
                                          "by 'FOLLOW ARCH.', shallower than every printed ground-beam section and "
                                          "unable to hold the drawn exterior section: what is their depth?"},
        "D-35 (main house)": {"runs": sorted(r["run"] for r in main_rows), "value_m3": r4(main_tot),
                              "proposal": "WITHDRAW as a depth question: the drawings settle 'Outer Normal ground level' "
                                          "= natural ground +-0.00 (5 readings agree; the court +0.15 is 0.15 paving on "
                                          "N.G.); D = 0.95 m; DRAWING-CONFIRMED pending the Checker's re-read"},
        "M4": {"runs": [r["run_id"] for b in inp["boundary_bands"] for r in b["runs"]],
               "each_m3": share["each_m3"],
               "question": "Boundary-wall columns 20x30 ('SEE ARCH PLAN', none drawn on any plan): give their positions "
                           "and count along the boundary wall."},
        "T-217 (neck section, not a consultant row here)": {"runs": t217},
    }

    fl = FREELANCER_BOUNDARY
    summary = {
        "policy": BC.policy_record(),
        "boundary_gb": {
            "runs": [{k: v for k, v in x.items() if k in ("run", "status", "value_m3", "L_m")} for x in b_runs],
            "run_length_m": r4(band_len), "band_plan_m2": r4(band_area),
            "band_m3_physical": r4(bline["band_m3"]), "beam_line_m3": bline["beam_line_m3"],
            "beam_line_status": bline["status"], "column_each_m3": share["each_m3"],
            "freelancer": {**fl, "difference_m3": r4(fl["m3"] - bline["band_m3"]),
                           "section_part_m3": r4((fl["b_m"] * fl["d_m"] - P14_GB_B * P14_GB_D) * fl["L_m"]),
                           "length_part_m3": r4((fl["L_m"] - band_len) * P14_GB_B * P14_GB_D)},
            "released_A": None, "candidate": None,
        },
        "datum": datum, "depth_main": d_main, "depth_annex": d_annex,
        "exterior_main_m3": r4(main_tot), "exterior_main_runs": len(main_rows),
        "annex_literal_m3": r4(annex_lit), "annex_runs": len(annex_rows),
        "court": [{k: v for k, v in c.items() if k in ("run", "L_m", "low_m3", "high_m3", "candidates_m",
                                                         "length_closed", "end_reading")} for c in court],
        "court_range_m3": [r4(sum(c["low_m3"] for c in court)), r4(sum(c["high_m3"] for c in court))],
        "consultant_rows": consultant,
    }
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=["item", "component", "L_m", "b_m", "d_m", "status", "value_m3", "low_m3",
                                        "high_m3", "basis"], lineterminator="\n")
    w.writeheader()
    for r in rows:
        w.writerow(r)
    if write:
        with open(os.path.join(HERE, "LEDGER_T253.csv"), "w", encoding="utf-8", newline="") as f:
            f.write(buf.getvalue())
        with open(os.path.join(HERE, "summary.json"), "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=1, sort_keys=True, ensure_ascii=False)
            f.write("\n")
    return rows, summary


if __name__ == "__main__":
    rows, s = main(write=True)
    print(json.dumps({k: s[k] for k in ("boundary_gb", "datum", "depth_main", "depth_annex", "exterior_main_m3",
                                        "annex_literal_m3", "court_range_m3")}, indent=1, ensure_ascii=False))
    for k, v in s["consultant_rows"].items():
        print(k, len(v["runs"]), {kk: vv for kk, vv in v.items() if kk not in ("runs",)})
