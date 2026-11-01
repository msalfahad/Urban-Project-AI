"""T-413 on the development villa: the lift-entrance marble (B6-06 surround, B6-07 threshold) at the three landing doors
of LIFT-01, by LIFT_ENTRANCE_MARBLE_V1, bound to the candidate of record ARCH_TAKEOFF_V3.0.35. Research only.

    python3 -I research/agents_t413/t413_alsenan.py <dir holding V3_0_35_BOQ_LINES.json> --write   # own run, writes
    python3 -I research/agents_t413/t413_alsenan.py --check                                       # committed closes

Geometry: station-LOCAL dimensions only (origin = the middle of the lift opening at mid wall, landing side = -y), read
this run on the architectural DXF (Drive "Alsenan chalet project", P7757_DXF_COMPRESSED.zip -> P7757.dxf, sha256
ab54dd55; layers 1 / 5 / S-COL.BON / LEVEL / 4) and on the section sheets (p7757_arch_sheet10.pdf SECTION A-A,
Alsenan_Architectural_P7757_Pages_11-12.pdf SECTION B-B). Entities are named by DXF handle; no coordinate, image, name
or drawing content is committed.

Per plan (GF / 1F / 2F the same set-out, offset 44.853 m in x): shaft inner 1.800 x 1.800 (layer 1, = T-401), south
wall 0.200 (dimension '200'), opening between the jamb lines at -0.500 / +0.500 = 1.000 m clear, four layer-5 lines
across the gap at +0.100 / +0.050 / 0.000 / -0.100 (the landing-door / sill lines: no threshold dimension), car outline
and diagonal + rear bar (layer 5) inside the shaft; the shaft's N / E / W inner faces are unbroken: ONE door per floor.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lift_entrance_marble_v1 as LM  # noqa: E402

CANDIDATE = "ARCH_TAKEOFF_V3.0.35"
CANDIDATE_JSON_SHA256 = "b011bace2958f3da42afa00587eb2511afed754a46aba78e8d08346aa2903e10"  # T-400 summary_t400.json
TABLE = HERE / "STATION_TABLE_T413.csv"
SUMMARY = HERE / "summary.json"
DXF_SHA8 = "ab54dd55"

# storey heights F.F.L. to F.F.L., printed on SECTION A-A (sheet 10: '450', '420', '420'; +1.00 / +5.50 / +9.70 / +13.90)
STOREY = {"GF": 4.50, "1F": 4.20, "2F": 4.20}

# Own reading this run (handles of P7757.dxf). available = landing wall face beside the jamb, to the next corner or
# opening on the plan (the band may not run past it).
DRAWN = {
    "GF": {"engine_opening": "OP-011", "landing_face": "GF-RC99C2A", "shaft_face": "GF-R89E756",
           "jambs": "226 / 227 (layer 1, x -0.500 / +0.500)", "sill_lines": "228 / 229 / 22A / 22B (layer 5)",
           "left_available_m": 0.700, "left_stop": "jamb of the 1.00 door D120 (insert 2C7, wall lines 20E / 20F)",
           "right_available_m": 0.650, "right_stop": "external corner of column 2F8A (0.25 x 1.00, proud 0.05 of "
                                                     "wall line 222)"},
    "1F": {"engine_opening": "OP-007", "landing_face": "1F-R78C367", "shaft_face": "1F-RCCB686",
           "jambs": "B96 / B97", "sill_lines": "B98 / B99 / B9A / B9B",
           "left_available_m": 0.600, "left_stop": "external corner of the shaft block at wall line B16 (stair "
                                                   "beyond)",
           "right_available_m": 0.935, "right_stop": "wall end (lines AFD / B18 stop at +1.435)"},
    "2F": {"engine_opening": "OP-002", "landing_face": "2F-R4D1B62", "shaft_face": "2F-R2BDCEE",
           "jambs": "12AE / 12AF", "sill_lines": "12B0 / 12B1 / 12B2 / 12B3",
           "left_available_m": 0.600, "left_stop": "external corner at wall line 129A",
           "right_available_m": 0.400, "right_stop": "INTERNAL corner: wall 1294 / 128D (0.20) runs south from the "
                                                     "column 2F6C face at +0.900 (door d220 in it)"},
}
CLEAR_W = 1.000
WALL_BAND = 0.200
# threshold placed flush with the shaft face (A) or starting at the landing face (B): own shapely check on the engine
# room polygons of this run (the opening band itself lies in no face: 0.000 in landing and shaft)
OVERLAP_A, OVERLAP_B = 0.300, 0.500

FREELANCER = {
    "marble_sheet_rows": 31, "lift_marble_rows": 0, "rows_total": 885, "lift_term_rows": 1,
    "lift_term_row": "RC 'walls + columns' row 11: lift walls 20 cm (concrete, T-401)",
    "plaster_lift_doors": "PLS row 10 column 'corners m.l' 17.4 'for lift doors' (corner beads, T-405 B4-09)",
}


def build():
    st = LM.stations([{"floor": f, "doors": [{}]} for f in ("GF", "1F", "2F")])
    rows, surs, thrs = [], [], []
    for sid, f in zip(st, ("GF", "1F", "2F")):
        d = DRAWN[f]
        left = LM.band_width("LEFT", available_m=d["left_available_m"], default_m=LM.SURROUND_DEFAULT_M,
                             default_source=LM.SURROUND_SOURCE)
        top = LM.band_width("TOP", default_m=LM.SURROUND_DEFAULT_M, default_source=LM.SURROUND_SOURCE)
        right = LM.band_width("RIGHT", available_m=d["right_available_m"], default_m=LM.SURROUND_DEFAULT_M,
                              default_source=LM.SURROUND_SOURCE)
        s = LM.surround(sid, clear_width_m=CLEAR_W, clear_height_m=None, storey_height_m=STOREY[f],
                        left=left, top=top, right=right)
        t = LM.threshold(sid, clear_width_m=CLEAR_W, default_depth_m=LM.THRESHOLD_DEFAULT_DEPTH_M,
                         depth_source=LM.THRESHOLD_SOURCE, wall_band_m=WALL_BAND)
        assert t["floor_overlap_bound_m2"] == [OVERLAP_A, OVERLAP_B]
        surs.append(s)
        thrs.append(t)
        rows.append({
            "STATION": sid, "FLOOR": f, "ENGINE_OPENING": d["engine_opening"], "LANDING_FACE": d["landing_face"],
            "SHAFT_FACE": d["shaft_face"], "CLEAR_WIDTH_M": f"{CLEAR_W:.3f}", "WIDTH_STATUS": LM.DRAWING,
            "WIDTH_SOURCE": f"jamb lines {d['jambs']}", "CLEAR_HEIGHT": "HELD: not printed (plans, A-A, B-B)",
            "LEFT_M": _w(left), "LEFT_STATUS": left["status"], "LEFT_AVAILABLE_M": f"{d['left_available_m']:.3f}",
            "TOP_M": _w(top), "TOP_STATUS": top["status"],
            "RIGHT_M": _w(right), "RIGHT_STATUS": right["status"],
            "RIGHT_AVAILABLE_M": f"{d['right_available_m']:.3f}",
            "SURROUND_M2": "", "SURROUND_STATUS": s["status"],
            "SURROUND_BOUND_M2": f"{s['bound_m2'][0]:.4f} .. {s['bound_m2'][1]:.4f}", "SURROUND_FORMULA": s["formula"],
            "THRESHOLD_M2": f"{t['area_m2']:.4f}", "THRESHOLD_STATUS": f"width {LM.DRAWING}; depth {t['status']}",
            "FRONT_EDGE_LM": f"{t['front_edge_lm']:.3f}",
            "FLOOR_OVERLAP_M2": f"{t['floor_overlap_bound_m2'][0]:.4f} .. {t['floor_overlap_bound_m2'][1]:.4f}",
            "FLOOR_OVERLAP_STATUS": t["floor_overlap_status"],
            "CANDIDATE_LINE": "NO LINE (B6-06 / B6-07)",
        })
    return st, rows, surs, thrs


def _w(b):
    return f"{b['width_m']:.3f}" if b["width_m"] is not None else f"HELD 0 .. {b['bound'][1]:.3f}"


# the three ARCH.THRESHOLD LIFT_LANDING band lines (wall band 1.000 x 0.200 of each lift opening, BOUNDED_EXPOSURE,
# 'the sill finish is not specified', T-240 / T-325 MERGED) and the three NOT_APPLICABLE porcelain doorway strips
LIFT_BAND_LINES = ["L-6f5806adbacba9118497", "L-084df97d3d41525a65c2", "L-3c5a3be22e861d9d4cfb"]
LIFT_STRIP_LINES = ["L-2621372661b2eb15b748", "L-bb09715ec8ccdd5d11a8", "L-17a56dfafc5504f41a28"]


def _code(ln):
    return str(ln.get("item_code") or ln.get("item") or "")


def binding(lines_path):
    """The candidate lines a lift-entrance marble station touches (ids, codes, states, m2 only)."""
    import re
    lines = json.loads(Path(lines_path).read_text(encoding="utf-8"))
    lines = lines["lines"] if isinstance(lines, dict) else lines
    lift_marble = sorted(ln["line_id"] for ln in lines
                         if re.search(r"ELEV|LIFT", _code(ln).upper()) and _code(ln).startswith(("FIN", "ARCH")))
    faces = {DRAWN[f]["landing_face"]: f for f in DRAWN}
    floor_lines = {k: [] for k in faces}
    landing, opening = [], {}
    for ln in lines:
        code, loc = _code(ln), ln.get("location") or {}
        eid, fl = str(loc.get("element_id") or ""), str(loc.get("floor") or "")
        if code.startswith("FIN.FLOOR"):
            for face in faces:
                if eid == f"{face}:floor":
                    floor_lines[face].append({"line_id": ln["line_id"], "item_code": code,
                                              "evidence_state": ln.get("evidence_state"),
                                              "measured_net": ln.get("measured_net")})
        if code == "ARCH.PASSAGE" and fl in DRAWN and eid == f"{DRAWN[fl]['landing_face']}:{DRAWN[fl]['engine_opening']}":
            opening[fl] = ln["line_id"]
        if code.startswith(("FIN.FLOOR", "ARCH.THRESHOLD", "FIN.MARBLE")) and fl in DRAWN:
            op = DRAWN[fl]["engine_opening"]
            if re.search(rf"(STRIP-|THRESHOLD:{fl}:){op}\b", eid):
                br = ln.get("bounded_range") or {}
                landing.append({"line_id": ln["line_id"], "item_code": code, "floor": fl, "element_id": eid,
                                "evidence_state": ln.get("evidence_state"),
                                "measured_net": ln.get("measured_net"),
                                "bound_m2": [br.get("low"), br.get("high")] if br else None})
    return {"lift_marble_lines": lift_marble,
            "floor_finish_lines_on_landing_faces": floor_lines,
            "lift_opening_lines": sorted(landing, key=lambda r: (r["floor"], r["item_code"])),
            "lift_landing_threshold_lines": sorted(r["line_id"] for r in landing
                                                   if r["item_code"] == "ARCH.THRESHOLD"),
            "opening_lines": opening,
            "lines_total": len(lines)}


def outputs(lines_path=None, prior=None):
    st, rows, surs, thrs = build()
    if lines_path is not None:
        raw = Path(lines_path).read_bytes()
        sha = hashlib.sha256(raw).hexdigest()
        if sha != CANDIDATE_JSON_SHA256:
            raise SystemExit(f"candidate json {sha[:8]} != pinned {CANDIDATE_JSON_SHA256[:8]}")
        bnd = binding(lines_path)
    else:
        bnd = prior["candidate_binding"]
    for r in rows:
        f = r["FLOOR"]
        r["OPENING_LINE"] = bnd["opening_lines"].get(f, "")
        r["BAND_LINE"] = " | ".join(x["line_id"] for x in bnd["lift_opening_lines"]
                                    if x["floor"] == f and x["item_code"] == "ARCH.THRESHOLD")
        r["FLOOR_LINE"] = " | ".join(x["line_id"] for x in
                                     bnd["floor_finish_lines_on_landing_faces"][r["LANDING_FACE"]]) or "NO LINE"
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=list(rows[0].keys()), lineterminator="\n")
    w.writeheader()
    w.writerows(rows)
    table = buf.getvalue()
    summary = {
        "task": "T-413", "model": LM.MODEL, "candidate": CANDIDATE, "candidate_json_sha256": CANDIDATE_JSON_SHA256,
        "dxf_sha8": DXF_SHA8, "stations": st, "station_count": len(st),
        "surround_B6_06": {"value_m2": None, "status": LM.HELD,
                           "bound_m2": LM.totals(surs, "area_m2")["bound"],
                           "per_station_bound_m2": {s["station_id"]: s["bound_m2"] for s in surs},
                           "missing": sorted({m for s in surs for m in s["missing"]})},
        "threshold_B6_07": {"value_m2": LM.totals(thrs, "area_m2")["value"],
                            "front_edge_lm": round(sum(t["front_edge_lm"] for t in thrs), 3),
                            "status": "width DRAWING-CONFIRMED x depth ASSUMED — OWNER-APPROVED (UP-ELEV-005)",
                            "floor_overlap_bound_m2": [round(sum(t["floor_overlap_bound_m2"][0] for t in thrs), 4),
                                                       round(sum(t["floor_overlap_bound_m2"][1] for t in thrs), 4)]},
        "candidate_binding": bnd,
        "freelancer": FREELANCER,
    }
    return table, json.dumps(summary, indent=1, ensure_ascii=False, sort_keys=True) + "\n"


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--check" in argv:
        prior = json.loads(SUMMARY.read_text(encoding="utf-8"))
        table, summ = outputs(prior=prior)
        ok = table == TABLE.read_text(encoding="utf-8") and summ == SUMMARY.read_text(encoding="utf-8")
        print("T-413 check", "OK" if ok else "DIFFERS")
        return 0 if ok else 1
    if "--write" in argv:
        src = [a for a in argv if not a.startswith("--")][0]
        table, summ = outputs(lines_path=Path(src) / "V3_0_35_BOQ_LINES.json")
        TABLE.write_text(table, encoding="utf-8")
        SUMMARY.write_text(summ, encoding="utf-8")
        print(summ)
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
