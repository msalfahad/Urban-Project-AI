"""T-404: the development villa's boundary fence finishes, face by face, from committed values-only inputs (research).

    python3 -I research/agents_t404/t404_alsenan.py           # print the face ledger
    python3 -I research/agents_t404/t404_alsenan.py --write   # (re)write FACES / ITEMS / FREELANCER / summary
    python3 -I research/agents_t404/t404_alsenan.py --check   # committed outputs reproduce

Inputs (read only): research/agents_t396/ALSENAN_FENCE_INPUT.json (merged T-396: band lines by DXF handle, elevation
fence-end tops and court lines), research/agents_t337/BINDING_T337.csv (merged house facade face ledger), and the
facts below, each read this run from Drive "Alsenan chalet project" (values only, nothing scaled):

  P12_SECTION   Alsenan_Architectural_P7757_Pages_11-12.pdf p.12 'SECTION 1:100': wall '265' above the lower ground line
                = '50' + '215'; the ground band on the OTHER side is drawn higher than the dimension base (level not
                printed); the '50' band is hatched like the ground bands and continuous with the higher side's band; the
                top is a plain 0.20 end: no coping, no drip, no finish line, no note.
  P12_ELEVATION same sheet, FENCE ELEVATION 1:100 (street side): solid wall with a curved dip carrying an X railing and a
                rounded top at the gate end with the house number; the gate-end top drawn lower than the corner end;
                none of it dimensioned; the 2.50 gate opening runs from the fence end to the house wall (ground strip
                only); no hatch, texture or note on the fence faces.
  P12_PLAN      same sheet, FENCE PLAN: '580' solid + '250' gate on the street line; no finish note.
  ST14          ST7757.pdf p.14 TYPICAL BOUNDARY WALL plan + A-A: no coating, render or finish drawn or noted (T-263 s.1,
                T-396 s.0 read it; no new reading needed for a layer that is absent).
  SET           T-091 (0 finish notes on any plan), T-360 (0 of 675 DXF texts name a material; p.12: house number only),
                RFI-B-A12 (no finishes schedule or specification issued).
"""

from __future__ import annotations

import csv
import io
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import fence_finish as FF  # noqa: E402

ROOT = HERE.parents[1]
T396_INPUT = ROOT / "research" / "agents_t396" / "ALSENAN_FENCE_INPUT.json"
T337_BINDING = ROOT / "research" / "agents_t337" / "BINDING_T337.csv"
FACES = HERE / "FACES_T404.csv"
ITEMS = HERE / "ITEMS_T404.csv"
FREEL = HERE / "FREELANCER_T404.csv"
SUMMARY = HERE / "summary.json"

H_TOP = 2.65                     # printed '265' (p.12), T-396 R-T396-2 DRAWING-CONFIRMED on north + street
H_SRC = "Pages_11-12 p.12 SECTION '265'; NW / SE elevation fence ends 2.65 above +-0.00 (T-396)"
LOWER_BAND = 0.50                # printed '50' of the same section; material UNRESOLVED (T-396 designer fact 1)
NO_LAYER_AUTHORITY = None        # R-T404-5: no printed note, no owner rule (OWNER_NOTES_SIGMA item 3 unanswered)
FREELANCER = [                   # exterior plaster + Sigma workbook, sheet 'البيان' rows 87-90 (quantities only)
    ("r87 'سور'", 1, 37.65, 2.40),
    ("r88 'تابع'", 1, 5.80, 2.40),
    ("r89 'تابع'", 1, 0.50, 2.40),
    ("r90 'كتف'", 4, 0.20, 2.20),
]
FREELANCER_CORNERS_ML = {"A87": 73.65, "B87": 75.34, "B88": 16.10}   # his corner / arris columns (T-172), m.l


def _h():
    return {"value": H_TOP, "status": FF.DC, "source": H_SRC}


def build():
    d = json.loads(T396_INPUT.read_text(encoding="utf-8"))
    t = d["lower_passage_closure"]["thickness"]
    court = d["elevation_fence_end_nw"]["court_above_pm000_m"]
    assert court == d["elevation_fence_end_se"]["court_above_pm000_m"]
    assert d["elevation_fence_end_nw"]["top_above_pm000_m"] == H_TOP == d["elevation_fence_end_se"]["top_above_pm000_m"]
    st = d["street"]
    gate = st["gate_gap_110"]

    # R-T404-1: north owns both corner squares (outer 99 + 98 = 31.37; inner 13A leg 30.97 = 31.37 - 2 x 0.20)
    n_out, n_in = FF.face_lengths(d["north"]["outer_99_98"], t, 2)
    assert abs(n_in - d["north"]["inner_13A_leg"]) < 1e-9
    # street: outer 10F 8.30 = solid 5.80 to the corner point + gate 2.50; inner 13A leg 5.60 + gate 2.50
    s_out, s_in = FF.face_lengths(st["outer_10F"], t, 1)
    assert abs((s_in - gate) - st["inner_13A_leg"]) < 1e-9
    gates = [("G-01", gate)]
    faces = [
        FF.physical_face("F-NORTH", "OUTSIDE", n_out, _h()),
        FF.physical_face("F-NORTH", "PLOT", n_in, _h()),
        FF.physical_face("F-STREET", "OUTSIDE", s_out, _h(), gates, profile="UNDIMENSIONED"),
        FF.physical_face("F-STREET", "PLOT", s_in, _h(), gates, profile="UNDIMENSIONED"),
        # sea element (owner Q-63 C) and passage closure (no height printed): HELD by name (T-396)
        FF.physical_face("F-SEA", "OUTSIDE", 2.40, {"value": 2.65, "status": FF.HELD}),
        FF.physical_face("F-SEA", "PLOT", 2.40, {"value": 2.65, "status": FF.HELD}),
        FF.physical_face("F-LOWER", "OUTSIDE", 1.20, None),
        FF.physical_face("F-LOWER", "PLOT", 1.20, None),
    ]
    FF.once(faces)
    end = FF.stop_end("F-STREET", "G-01", t, _h(), own_end=True, profile="UNDIMENSIONED")
    # the other jamb of G-01 is the house wall (p.12 elevation): owned by the house facade ledger, not counted here
    tops = [FF.top("F-NORTH", d["north"]["outer_99_98"], t), FF.top("F-STREET", st["inner_13A_leg"], t, "UNDIMENSIONED")]

    rows = []
    for f in faces:
        plot = f["side"] == "PLOT"
        level = court if plot and f["status"] == FF.DC else None
        fin = FF.finishable(f, H_TOP, level, along_whole_run=False)
        geom = f["net_m2"] if f["net_m2"] is not None else f["at_most_m2"]
        lyr = [FF.layer(f["key"], n, geom, NO_LAYER_AUTHORITY) for n in FF.LAYERS]
        solid = None if f["gross_m2"] is None else \
            f["length_m"] - sum(w for _, w in (gates if f["run"] == "F-STREET" else []))
        lower = None if solid is None else round(solid * LOWER_BAND, 6)
        rows.append({"key": f["key"], "run": f["run"], "side": f["side"], "length_m": f["length_m"],
                     "height_m": f["height_m"], "gross_m2": f["gross_m2"],
                     "deductions": ";".join(f"{g}:{m}" for g, m in f["deductions"]),
                     "net_m2": f["net_m2"], "at_most_m2": f["at_most_m2"],
                     "comparison_only_m2": f["comparison_only_m2"], "face_status": f["status"],
                     "face_held": "; ".join(f["held"]),
                     "of_which_lower_050_band_m2": lower,
                     "finishable_m2": fin["m2"], "finishable_lo_m2": fin["lo_m2"], "finishable_hi_m2": fin["hi_m2"],
                     "finishable_status": fin["status"], "finishable_basis": fin["basis"],
                     "plaster_status": lyr[0]["status"], "plaster_at_most_m2": lyr[0]["at_most_m2"],
                     "sigma_paint_status": lyr[1]["status"], "sigma_paint_at_most_m2": lyr[1]["at_most_m2"]})

    # acceptance (c): faces shared with the house facade ledger, by key and by level band on the boundary line
    house = list(csv.DictReader(T337_BINDING.open(encoding="utf-8")))
    shared = FF.no_shared_faces([r["key"] for r in rows], [r["key"] for r in house])
    on_line = [r for r in house if "boundary line" in r["why"]]
    band_overlap = round(sum(max(0.0, min(float(r["top"]), H_TOP) - max(float(r["bottom"]), 0.0)) * float(r["length_m"])
                             for r in on_line), 6)

    items = []
    for tp in tops:
        items.append({"item": f"{tp['key']} wall top (m.l / m2)", "unit": "m.l | m2", "value": tp["ml"],
                      "value2": tp["m2"], "at_least": tp["at_least_ml"], "at_least2": tp["at_least_m2"], "at_most": None,
                      "geometry_status": tp["status"], "layer_status": FF.HELD,
                      "evidence": "p.12 section: plain 0.20 top, no coping / no note; layer R-T404-5"})
    items.append({"item": end["key"] + " stop-end face at the gate jamb", "unit": "m2", "value": end["m2"], "value2": None,
                  "at_least": None, "at_least2": None, "at_most": end["at_most_m2"], "geometry_status": end["status"], "layer_status": FF.HELD,
                  "evidence": f"t 0.20 x 2.65 = {end['at_most_m2']} at most; end top drawn rounded and lower (p.12 elevation)"})
    items.append({"item": "G-01 far jamb (house wall)", "unit": "m2", "value": None, "value2": None, "at_least": None,
                  "at_least2": None, "at_most": None, "geometry_status": "OTHER_OWNER", "layer_status": "OTHER_OWNER",
                  "evidence": "p.12 elevation: the gate runs to the house wall; house facade ledger (T-305 / T-337)"})
    items.append({"item": "coping on the fence top", "unit": "m.l", "value": None, "value2": None, "at_least": None,
                  "at_least2": None, "at_most": None, "geometry_status": FF.NOT_DRAWN, "layer_status": FF.NOT_DRAWN,
                  "evidence": "no coping drawn in the p.12 section / elevation or ST p.14; named, no quantity"})
    items.append({"item": "coating below N.G.: boundary G.B faces", "unit": "m2", "value": None, "value2": None,
                  "at_least": None, "at_least2": None, "at_most": None, "geometry_status": "OTHER_OWNER", "layer_status": FF.HELD,
                  "evidence": "owned by T-263 (HELD, gross 35.256 m2: ST p.14 A-A prints no coating); not counted here"})
    items.append({"item": "coating below N.G.: boundary masonry faces (44.07 m band, both faces)", "unit": "m2",
                  "value": None, "value2": None, "at_least": None, "at_least2": None, "at_most": None, "geometry_status": FF.HELD,
                  "layer_status": FF.HELD,
                  "evidence": "masonry height below N.G. not printed (T-396 s.4, 'AS PER EXCAVATION DEPTH'); no coating "
                              "note on ST p.14; HELD blank, never 0"})
    items.append({"item": "faces shared with the house facade ledger", "unit": "m2", "value": float(shared),
                  "value2": band_overlap, "at_least": None, "at_least2": None, "at_most": None, "geometry_status": "CHECK",
                  "layer_status": "CHECK",
                  "evidence": f"0 keys shared; {len(on_line)} house face(s) on the boundary line "
                              f"({', '.join(r['key'] for r in on_line)}): level-band overlap with the fence 0..{H_TOP} "
                              f"= {band_overlap} m2"})

    # R-T404-6: freelancer, best-fit mapping A (r88 5.80 = the street OUTSIDE face exactly)
    by = {r["key"]: r for r in rows}
    n_plot = by["F-NORTH/PLOT"]["length_m"]
    s_plot_solid = st["inner_13A_leg"]
    s_out_solid = round(s_out - gate, 6)
    his_a = [(FREELANCER[0][0], 1, 37.65, 2.40, round(n_plot + s_plot_solid, 6)),
             (FREELANCER[1][0], 1, 5.80, 2.40, s_out_solid),
             (FREELANCER[2][0], 1, 0.50, 2.40, None),
             (FREELANCER[3][0], 4, 0.20, 2.20, None)]
    rec_a = FF.reconcile(his_a, [(end["key"], end["at_most_m2"])], H_TOP)
    his_b = [(FREELANCER[0][0], 1, 37.65, 2.40, round(n_out + s_out_solid, 6)),
             (FREELANCER[1][0], 1, 5.80, 2.40, s_plot_solid),
             (FREELANCER[2][0], 1, 0.50, 2.40, None),
             (FREELANCER[3][0], 4, 0.20, 2.20, None)]
    rec_b = FF.reconcile(his_b, [(end["key"], end["at_most_m2"])], H_TOP)

    dc_faces = FF.totals([{"key": r["key"], "status": r["face_status"], "m2": r["net_m2"], "at_most_m2": r["at_most_m2"]}
                          for r in rows])
    summary = {
        "method": "FENCE_FINISH_V1 (research, not wired)", "candidate_lines_changed": 0,
        "height_m": H_TOP, "court_level_m": court, "thickness_m": t,
        "faces": {r["key"]: {"net_m2": r["net_m2"], "at_most_m2": r["at_most_m2"], "status": r["face_status"]}
                  for r in rows},
        "physical_faces_dc_m2": dc_faces["dc"], "physical_faces_held": dc_faces["held"],
        "physical_faces_held_at_most_m2_known_part": dc_faces["held_at_most"],
        "stop_end_at_most_m2": end["at_most_m2"],
        "tops": {tp["key"]: {"ml": tp["ml"], "m2": tp["m2"], "at_least_ml": tp["at_least_ml"],
                             "at_least_m2": tp["at_least_m2"], "status": tp["status"]} for tp in tops},
        "layers": "PLASTER and SIGMA_PAINT HELD on every face (R-T404-5; OWNER_NOTES_SIGMA item 3 unanswered; Q-65 C)",
        "coping": FF.NOT_DRAWN, "shared_faces_with_house": shared, "house_band_overlap_m2": band_overlap,
        "freelancer": {"rows_m2": {r[0]: round(r[1] * r[2] * r[3], 6) for r in FREELANCER},
                       "his_total_m2": rec_a["his_m2"], "corners_ml": FREELANCER_CORNERS_ML,
                       "mapping_A": rec_a, "mapping_B": rec_b,
                       "mapping_note": "A: r87 = the PLOT faces (north + street), r88 = the street OUTSIDE face (5.80 exact); "
                                       "B: r87 = the OUTSIDE faces (31.37 + 5.80, his blockwork basis), r88 = the street "
                                       "PLOT face at 5.80; neither is proven (UNRESOLVED); in both, ONE north face is "
                                       "outside his take",
                       "not_in_his_scope": {"A": "F-NORTH/OUTSIDE (neighbour face) 83.1305", "B": "F-NORTH/PLOT 82.0705"}},
    }
    return rows, items, summary


def _csv(rows):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=list(rows[0].keys()), lineterminator="\n")
    w.writeheader()
    for r in rows:
        w.writerow({k: ("" if v is None else v) for k, v in r.items()})
    return buf.getvalue()


def _freel_rows(summary):
    out = []
    for name in ("mapping_A", "mapping_B"):
        rec = summary["freelancer"][name]
        for rid, why, m2 in rec["causes"]:
            out.append({"mapping": name, "row_or_face": rid, "cause": why, "m2": m2})
        out.append({"mapping": name, "row_or_face": "TOTAL", "cause": f"his {rec['his_m2']} - ours {rec['own_m2']}",
                    "m2": rec["diff_m2"]})
        out.append({"mapping": name, "row_or_face": "RESIDUAL", "cause": "unexplained", "m2": rec["residual_m2"]})
    return out


def outputs():
    rows, items, summary = build()
    return {FACES: _csv(rows), ITEMS: _csv(items), FREEL: _csv(_freel_rows(summary)),
            SUMMARY: json.dumps(summary, ensure_ascii=False, indent=1, sort_keys=True) + "\n"}


def main(argv):
    outs = outputs()
    if "--write" in argv:
        for p, s in outs.items():
            p.write_text(s, encoding="utf-8")
        print("written", ", ".join(p.name for p in outs))
        return 0
    if "--check" in argv:
        bad = [p.name for p, s in outs.items() if not p.exists() or p.read_text(encoding="utf-8") != s]
        print("CHECK", "FAIL " + ", ".join(bad) if bad else "OK")
        return 1 if bad else 0
    print(outs[FACES])
    print(outs[ITEMS])
    print(outs[FREEL])
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
