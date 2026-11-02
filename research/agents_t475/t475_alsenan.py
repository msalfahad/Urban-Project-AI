"""T-475 development villa (Alsenan): per-landing lift-marble census by LIFT_LANDING_CENSUS_V1, from an own reading of
P7757.dxf (Drive "Alsenan chalet project", P7757_DXF_COMPRESSED.zip) and SECTION B-B (Alsenan_Architectural_P7757_
Pages_11-12.pdf), decoded by the wrapper into .work/private. Only station-LOCAL dimensions (origin = mid opening at
mid wall, landing side = -y) and DXF handles are recorded here; no coordinate, image, name or drawing content.

    python3 -I research/agents_t475/t475_alsenan.py --write   # writes CENSUS_T475.csv + summary.json
    python3 -I research/agents_t475/t475_alsenan.py --check   # the committed files reproduce
"""
from __future__ import annotations

import csv
import io
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lift_landing_census_v1 as C  # noqa: E402

LM = C.LM
TABLE = HERE / "CENSUS_T475.csv"
SUMMARY = HERE / "summary.json"

# Own reading this run (P7757.dxf handles; three plans with one set-out, x offset 44.853 m; units mm in the file,
# metres here). Shaft inner 1.800 x 1.800 (dims 666 / 67D GF, D31 / D3D 1F, 139A / 13A6 2F), south shaft wall 0.200
# (672 GF, D62 / E94 1F, 13CB / 142F / 1538 2F), lift columns S-COL.BON 2F8A / 2F90 GF, 2FED / 2FF3 1F.
FLOORS = [
    {"floor": "GF", "state": C.LANDING, "evidence": "jamb lines 226 / 227 1.000 apart in the 0.200 south shaft wall; "
     "layer-5 lines 228 / 229 / 22A / 22B across the gap; N / E / W inner faces 219 / 212 / 216 unbroken",
     "openings": [{"engine_opening": "OP-011", "clear_width_m": 1.000,
                   "faces": {"left": 0.700, "right": 0.650},
                   "face_evidence": {"left": "20E to the jamb of door D120 (insert 2C7; 20F resumes 1.000 further)",
                                     "right": "20D to 1.100, column 2F8A proud to 1.150 (external corner)"},
                   "ffl": "+1.00", "ffl_handle": "40F (insert 40E, 1.3 m in front of the opening)",
                   "landing_depth_m": None,
                   "landing_depth_source": "open hall: no wall, step or level line across the front within 2.5 m",
                   "storey_height_m": 4.50}]},
    {"floor": "1F", "state": C.LANDING, "evidence": "jamb lines B96 / B97 1.000 apart; layer-5 car / sill lines as GF; "
     "N / E / W inner faces B15 / B11 / B13 unbroken",
     "openings": [{"engine_opening": "OP-007", "clear_width_m": 1.000,
                   "faces": {"left": 0.600, "right": 0.935},
                   "face_evidence": {"left": "AFE to wall end B16 (external corner, stair beyond)",
                                     "right": "AFD to the jamb of door d220 (C1A, 0.900 gap to BED / AFC)"},
                   "ffl": "+5.50", "ffl_handle": "D18 (insert D17)",
                   "landing_depth_m": 1.250, "landing_depth_source": "dimension 1042 '1250' landing face to AEB",
                   "storey_height_m": 4.20}]},
    {"floor": "2F", "state": C.LANDING, "evidence": "jamb lines 12AE / 12AF 1.000 apart; layer-5 lines 12B0 .. 12B3; "
     "N / E / W inner faces 1299 / 1293 / 1297 unbroken",
     "openings": [{"engine_opening": "OP-002", "clear_width_m": 1.000,
                   "faces": {"left": 0.600, "right": 0.400},
                   "face_evidence": {"left": "128A to wall end 129A (external corner, stair beyond)",
                                     "right": "1289 to the INTERNAL corner with wall 1294 / 128D (door d220 12C2 in it)"},
                   "ffl": "+9.70", "ffl_handle": "134E (insert 134D)",
                   "landing_depth_m": 1.250, "landing_depth_source": "dimension 145F '1250' landing face to 1283",
                   "storey_height_m": 4.20}]},
    {"floor": "ROOF", "state": C.NO_LANDING,
     "evidence": "shaft closed by the +13.90 roof slab (T-401, ST 2F roof plan); SECTION B-B shows nothing above the "
                 "roof but the domes / parapet (own look, this run); no overrun door drawn", "openings": []},
]
WALL_BAND_M = 0.200
FREELANCER_ROWS = {"B6-06": "no row", "B6-07": "no row"}  # T-413 census of his marble sheet (31 rows), not re-opened
CANDIDATE = {  # T-421 V3.0.38 lines (its section 3 table); not re-run here
    "ELV-01-GF": {"thr": "L-c32effca", "edge": "L-f2b76041", "sur": "L-b66b8e76", "thr_m2": 0.500,
                  "sur_bound": [1.0, 5.0], "skirting": "L-71e2e002 (OP-011 PASSAGE 1.000 deducted, no jamb; T-296)"},
    "ELV-01-1F": {"thr": "L-9840d1da", "edge": "L-64dd750f", "sur": "L-d788f643", "thr_m2": 0.500,
                  "sur_bound": [1.0, 4.7], "skirting": "L-ba3599ec (OP-007 PASSAGE 1.000 deducted, no jamb; T-296)"},
    "ELV-01-2F": {"thr": "L-eba7ac43", "edge": "L-e29e5748", "sur": "L-fdbd9636", "thr_m2": 0.500,
                  "sur_bound": [0.75, 4.28], "skirting": "2F lobby lines of T-443 (OP-002 as LIFT, no jamb; queued)"},
}


def build():
    cen = C.census([{**f, "openings": [dict(o) for o in f["openings"]]} for f in FLOORS])
    stations = []
    for f in FLOORS:
        for o in f["openings"]:
            sid = f"ELV-01-{f['floor']}"
            sur = C.surround_from_detail(sid, clear_width_m=o["clear_width_m"], detail=None, faces=o["faces"],
                                         storey_height_m=o["storey_height_m"])
            thr = LM.threshold(sid, clear_width_m=o["clear_width_m"], default_depth_m=LM.THRESHOLD_DEFAULT_DEPTH_M,
                               depth_source=LM.THRESHOLD_SOURCE, wall_band_m=WALL_BAND_M)
            thr = C.threshold_fit(sid, thr, o["landing_depth_m"], o["landing_depth_source"])
            lvl = C.level_relation(o["ffl"])
            ded = C.deduction_matrix(sid, clear_width_m=o["clear_width_m"], surround=sur, thr=thr)
            stations.append({"station_id": sid, "floor": f["floor"], "opening": o, "surround": sur, "threshold": thr,
                             "level": lvl, "deductions": ded})
    return cen, stations


def rows(stations):
    out = []
    for s in stations:
        o, sur, thr = s["opening"], s["surround"], s["threshold"]
        b = {x["side"]: x for x in sur["bands"]}
        out.append({
            "STATION": s["station_id"], "ENGINE_OPENING": o["engine_opening"], "CLEAR_WIDTH_M": f"{o['clear_width_m']:.3f}",
            "LEFT_FACE_M": f"{o['faces']['left']:.3f}", "RIGHT_FACE_M": f"{o['faces']['right']:.3f}",
            "LEFT_BAND": b["left"]["status"] if b["left"]["width_m"] is None else f"{b['left']['width_m']:.2f} {b['left']['status']}",
            "TOP_BAND": f"{b['top']['width_m']:.2f} {b['top']['status']}",
            "RIGHT_BAND": (f"{b['right']['width_m']:.2f} {b['right']['status']}" if b["right"]["width_m"] is not None
                           else f"HELD 0 .. {b['right']['bound'][1]:.3f}"),
            "DOOR_HEIGHT": "HELD: not printed (plans, sections A-A / B-B, ST p.14)",
            "SURROUND_M2": "HELD" if sur["area_m2"] is None else f"{sur['area_m2']:.4f}",
            "SURROUND_BOUND_M2": f"{sur['bound_m2'][0]:.4f} .. {sur['bound_m2'][1]:.4f}" if sur["bound_m2"] else "",
            "THRESHOLD_M2": "HELD" if thr["area_m2"] is None else f"{thr['area_m2']:.4f}",
            "THRESHOLD_STATUS": thr["status"], "FRONT_EDGE_LM": f"{thr['front_edge_lm']:.3f}",
            "LANDING_DEPTH": (f"{thr['landing_depth']['value']:.3f} {thr['landing_depth']['status']}"
                              if thr["landing_depth"]["value"] is not None else thr["landing_depth"]["status"]),
            "LEVEL": f"{s['level']['relation']} {o['ffl']}",
            "FLOOR_PART_M2": f"{thr['floor_overlap_bound_m2'][0]:.4f} .. {thr['floor_overlap_bound_m2'][1]:.4f}",
            "SKIRTING_DEDUCT_LM": f"{o['clear_width_m']:.3f} (0 jamb)",
            "CANDIDATE_LINES": f"{CANDIDATE[s['station_id']]['thr']} / {CANDIDATE[s['station_id']]['edge']} / "
                               f"{CANDIDATE[s['station_id']]['sur']}",
        })
    return out


def outputs():
    cen, st = build()
    rs = rows(st)
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=list(rs[0]), lineterminator="\n")
    w.writeheader()
    w.writerows(rs)
    tot = C.family_totals(st)
    agree = []
    for s in st:
        c = CANDIDATE[s["station_id"]]
        agree.append({"station": s["station_id"],
                      "threshold_m2": [s["threshold"]["area_m2"], c["thr_m2"],
                                       abs(s["threshold"]["area_m2"] - c["thr_m2"]) < 5e-4],
                      "surround_bound_m2": [s["surround"]["bound_m2"], c["sur_bound"],
                                            all(abs(a - b) < 5e-4 for a, b in zip(s["surround"]["bound_m2"],
                                                                                    c["sur_bound"]))]})
    summary = {"model": C.MODEL, "census": cen, "totals": tot, "equivalent_stations": C.equivalent(st),
               "candidate_agreement": agree, "freelancer": FREELANCER_ROWS,
               "skirting": {s: CANDIDATE[s]["skirting"] for s in CANDIDATE}}
    return buf.getvalue(), json.dumps(summary, indent=1, ensure_ascii=False, sort_keys=True) + "\n"


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    table, summ = outputs()
    if "--write" in argv:
        TABLE.write_text(table, encoding="utf-8")
        SUMMARY.write_text(summ, encoding="utf-8")
        return 0
    if "--check" in argv:
        ok = TABLE.read_text(encoding="utf-8") == table and SUMMARY.read_text(encoding="utf-8") == summ
        print("T-475 outputs reproduce" if ok else "T-475 outputs DIFFER")
        return 0 if ok else 1
    print(table)
    print(summ)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
