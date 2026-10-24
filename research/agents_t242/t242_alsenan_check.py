"""T-242 on the development villa: the CONC.GROUND reference line closed component by component.

Inputs (committed, values / ids / handles only): ALSENAN_GROUND_INPUT.json (t242_extract.py on the Drive drawings,
this run), research/agents_t230/ALSENAN_END_INPUT.json (T-230 MERGED 17ed6f92: neck DOUBLE / GAP per end, lift-ring
ends), research/agents_t141/T141_SPANS.csv (span -> T-138 occurrence), research/agents_t138/T138_MEMBERS.csv (the
pre-S5 exterior / interior reading carried by T-138), tests/alsenan/registers_b1/FREELANCER_RAW_ROWS.json (his
'الشناجات' sheet rows 11-16). Outputs: LEDGER_T242.csv, summary.json.

    python3 -I research/agents_t242/t242_alsenan_check.py [--write]
"""
from __future__ import annotations

import csv
import io
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import ground_line as GL  # noqa: E402

# printed datums (merged level chain, values only)
GF_TOP = {"MAIN": 0.95, "ANNEX": 0.25}    # GF structural slab tops: FFL +1.00 / +0.30 less the 0.05 build-up (T-214)
OUTER_GROUND = (0.00, 0.15)               # 'Outer Normal ground level': existing +-0.00 or the court +0.15 (T-206 / T-214)
BOUNDARY_GB_DEPTH = 0.40                  # p.14 TYPICAL BOUNDARY WALL: plan 'GROUND BEAM (20x40)', section A-A '40'
# lift-pit ring ends (T-230 MERGED, Checker 18:01 own 2.900 / 3.228 / 5.020 m)
LIFT_END = {"15D+7C8#1": 2.900, "17C+7E3#1": 3.228, "177+7CD#1": 5.020}

# freelancer RC workbook, sheet 'الشناجات' (committed cells)
FL_ROWS = {"slab": ("A11", "E11"), "longitudinal": ("A13", "E13"), "transverse": ("A14", "E14"),
           "boundary": ("A15", "E15"), "total": ("A16", "I16")}


def literal_titles(L):
    """p.13 titles that hold literally for a face-to-face length L (m): 'more than 5', 'less than 5', 'less than 2.5'."""
    out = []
    if L >= 5.0 - 1e-9:
        out.append("P13-GB-GT5M")
    if L <= 5.0 + 1e-9:
        out.append("P13-GB-LT5M")
    if L < 2.5:
        out.append("P13-GB-LT2_5M")
    return out


def s2_of(walls):
    if any(w["exterior_side"] for w in walls):
        return GL.EXTERIOR
    if walls:
        return GL.INTERIOR
    return "NOWALL"


def s3_of(detail):
    if detail is None:
        return "UNKNOWN"
    parts = set(detail.replace("CONC/", "").split("/"))
    if parts == {"EXT"}:
        return "EXT"
    if "EXT" in parts:
        return "EXT_OR_INT"
    return "INT"


def load():
    inp = json.loads((HERE / "ALSENAN_GROUND_INPUT.json").read_text(encoding="utf-8"))
    ends = json.loads((ROOT / "research/agents_t230/ALSENAN_END_INPUT.json").read_text(encoding="utf-8"))
    t141 = {r["span_id"]: r for r in csv.DictReader(open(ROOT / "research/agents_t141/T141_SPANS.csv",
                                                          encoding="utf-8"))}
    t138 = {}
    for r in csv.DictReader(open(ROOT / "research/agents_t138/T138_MEMBERS.csv", encoding="utf-8")):
        if r["family"] == "GROUND_BEAM" and r["component"] == "TOP":
            t138.setdefault(r["member"], r["detail"])
    fl = {}
    raw = json.loads((ROOT / "tests/alsenan/registers_b1/FREELANCER_RAW_ROWS.json").read_text(encoding="utf-8"))
    for r in raw["rows"]:
        if r["file"] == "RC" and r["sheet"] == "الشناجات":
            fl.update({k: v["v"] for k, v in r["cells"].items()})
        if r["file"] == "RC" and r["sheet"] == "ورقة1" and r["row"] == 18:
            fl["SUMMARY_E18"] = r["cells"]["E18"]["v"]
    return inp, ends, t141, t138, fl


def adjustments(ends):
    """Per span: plan m2 (lo, hi) added at its ends from the T-230 neck readings (DOUBLE removed, GAP added once)."""
    adj = {}
    notes = {}
    for c in ends["column_ends"]:
        d = c["double_plan_m2_per_reading"]
        if max(d) > 0:
            lo, hi = adj.get(c["span_id"], (0.0, 0.0))
            adj[c["span_id"]] = (lo - max(d), hi - min(d))
            notes.setdefault(c["span_id"], []).append(f"neck {c['column']} DOUBLE {min(d):.4f}..{max(d):.4f} m2 "
                                                      f"({c['neck_status']})")
    for j in ends["junctions"]:
        g = j["gap_plan_m2_per_reading"]
        if max(g) > 0:
            sid = j["ends"][0].split(":")[0]          # one owner: the first beam end listed at the neck
            lo, hi = adj.get(sid, (0.0, 0.0))
            adj[sid] = (lo + min(g), hi + max(g))
            notes.setdefault(sid, []).append(f"beam strip beside neck {j['column']} GAP {min(g):.4f}..{max(g):.4f} "
                                             f"m2 ({j['neck_status']})")
    return adj, notes


def main(write=False):
    inp, ends, t141, t138, fl = load()
    adj, adj_notes = adjustments(ends)
    part_pieces = inp["partition"]["unbilled_pieces"]
    # the L-corner square at 10B+7D1 / 7D4+F8 (both bands stop at the junction: billed by neither span); owner = the
    # plot-line band 7D4+F8, which runs through the corner
    corner = [p for p in part_pieces if p["in_bands"] == ["10B+7D1"] and "7D4+F8#2" in p["touches_spans"]]
    if len(corner) != 1:
        raise SystemExit("corner piece 10B+7D1 / 7D4+F8 not found once")
    lo, hi = adj.get("7D4+F8#2", (0.0, 0.0))
    adj["7D4+F8#2"] = (lo + corner[0]["plan_m2"], hi + corner[0]["plan_m2"])
    adj_notes.setdefault("7D4+F8#2", []).append(f"corner square with 10B+7D1 {corner[0]['plan_m2']:.4f} m2 "
                                                "(billed by no span; this run owns it)")

    rows, runs = [], {"interior": [], "exterior": [], "other": []}
    for s in inp["spans"]:
        sid = s["span_id"]
        A = [p["level"] for p in s["S1_probes"] if p["side"] == "A"]
        Bv = [p["level"] for p in s["S1_probes"] if p["side"] == "B"]
        s1, s1s = GL.s1_reading(A, Bv)
        s2 = s2_of(s["S2_walls"])
        det = t138.get(t141[sid]["hand_occurrence"]) if sid in t141 else None
        s3 = s3_of(det)
        kind, why = GL.classify(s1, s1s, s2, s3)
        L = LIFT_END.get(sid, s["face_to_face_m"])
        if sid in LIFT_END:
            classes = literal_titles(L)
            basis = "face to face to the lift pit ring (T-230)"
        else:
            cl = set(s["class_face_to_face"]) | set(s["class_centreline"])
            for v in s["end_candidates"].values():
                cl |= set(v["class"])
            classes = sorted(cl)
            basis = "face to face (V2), title on the face and centreline bases"
        d33 = bool(s["tees_mid_span"])
        held_v2 = [h for h in s["v2_held"] if not (sid == "177+7CD#1")]   # T-230 resolved its GAP_TO_COLUMN end
        ea = adj.get(sid, (0.0, 0.0))
        depths = GL.title_depths(classes)
        if kind == GL.INTERIOR:
            r = GL.run_volume(sid, kind, s["width_m"], L, depths=depths, d33=d33, end_adjust_m2=ea)
        elif kind == GL.EXTERIOR:
            ext = GL.exterior_depth([GF_TOP[s["part"]]], OUTER_GROUND)
            r = GL.run_volume(sid, kind, s["width_m"], L, ext=ext, end_adjust_m2=ea)
        else:
            cand = sorted(set(depths) | ({GF_TOP[s["part"]] - g for g in OUTER_GROUND}
                                         if s3 in ("EXT", "EXT_OR_INT") or s2 == GL.EXTERIOR or s1 == GL.EXTERIOR
                                         else set()))
            r = GL.run_volume(sid, kind, s["width_m"], L, depths=cand, end_adjust_m2=ea)
        if held_v2 and r["status"] == GL.CALCULATED:
            r = dict(r, status=GL.HELD, value_m3=None)
        if held_v2:
            r["reasons"] = r["reasons"] + held_v2
        r["kind"] = kind
        (runs["interior"] if kind == GL.INTERIOR else runs["exterior"] if kind == GL.EXTERIOR
         else runs["other"]).append(r)
        rows.append({"run": sid, "component": "GB-" + kind, "part": s["part"], "direction": s["direction"],
                     "b_m": s["width_m"], "L_m": round(L, 4), "length_basis": basis,
                     "titles": "+".join(c[4:] for c in classes), "S1": f"{s1} ({s1s})", "S2": s2,
                     "S3": f"{s3} ({det})", "class_why": why, "d33_tees": "; ".join(t["band_id"] for t in
                                                                                   s["tees_mid_span"]),
                     "end_adjust_m2": f"{ea[0]:+.4f}..{ea[1]:+.4f}" if ea != (0.0, 0.0) else "",
                     "end_notes": "; ".join(adj_notes.get(sid, [])), "status": r["status"],
                     "value_m3": "" if r["value_m3"] is None else f"{r['value_m3']:.4f}",
                     "low_m3": "" if r["low_m3"] is None else f"{r['low_m3']:.4f}",
                     "high_m3": "" if r["high_m3"] is None else f"{r['high_m3']:.4f}",
                     "reasons": " | ".join(r["reasons"])})

    # curved runs (plan area between the drawn arcs, net of supports and straight bands)
    for a in inp["arc_bands"]:
        ins = [p["level"] for p in a["S1_probes"] if p["side"] == "inside"]
        outs = [p["level"] for p in a["S1_probes"] if p["side"] == "outside"]
        s1, s1s = GL.s1_reading(ins, outs)
        # S3: the pre-S5 register types both curved bands 'P13-GB-EXTERIOR' (both outline tests; T-138 / S5)
        kind, why = GL.classify(s1, s1s, "NOWALL", "EXT")
        if kind == GL.CANDIDATES and s1 == "UNKNOWN":
            # the ring 157 / 158 encloses the pool court (+0.15 printed inside it) on the house side of the north
            # band: no probe face carried a mark, so it stays as the register reads it, HELD with the exterior range
            kind, why = GL.EXTERIOR, "S3 exterior (both pre-S5 outline tests); S1 no mark on either side: HELD"
        ext = GL.exterior_depth([GF_TOP[a["part"]]], OUTER_GROUND)
        r = GL.run_volume(a["arc_band"], GL.EXTERIOR, a["width_m"], None, ext=ext, plan_m2=a["net_plan_m2"])
        r["kind"] = kind
        runs["exterior"].append(r)
        rows.append({"run": a["arc_band"], "component": "GB-" + kind + " (curved)", "part": a["part"],
                     "direction": "ARC", "b_m": a["width_m"], "L_m": round(a["net_plan_m2"] / a["width_m"], 4),
                     "length_basis": f"plan {a['net_plan_m2']:.4f} m2 net of supports / b", "titles": "EXT",
                     "S1": f"{s1} ({s1s})", "S2": "-", "S3": "EXT (pre-S5)", "class_why": why, "d33_tees": "",
                     "end_adjust_m2": "", "end_notes": f"deducted {a['deducted_straight_and_columns_m2']:.4f} m2 "
                                                       f"(columns {', '.join(x for x in a['touches'] if x.startswith('COL'))})",
                     "status": r["status"], "value_m3": "", "low_m3": f"{r['low_m3']:.4f}",
                     "high_m3": f"{r['high_m3']:.4f}", "reasons": " | ".join(r["reasons"])})

    # boundary-wall ground beam at natural ground (p.14)
    bw_area = sum(b["plan_m2"] for b in inp["boundary_bands"])
    bw_len = sum(b["plan_m2"] / b["width_m"] for b in inp["boundary_bands"])
    if any(b["overlap_spans_m2"] or b["overlap_columns_m2"] for b in inp["boundary_bands"]):
        raise SystemExit("boundary band overlaps a building beam / column: own it once first")
    bw_solid = round(bw_area * BOUNDARY_GB_DEPTH, 6)
    bw = {"run_id": "BOUNDARY-GB (S-BOUN " + " + ".join(b["handle"] for b in inp["boundary_bands"]) + ")",
          "status": GL.HELD, "value_m3": None, "low_m3": None, "high_m3": bw_solid, "kind": "BOUNDARY",
          "reasons": ["solid 0.20 x 0.40 x band DRAWING-CONFIRMED (p.14 plan label + section A-A); the 20 x 30 "
                      "boundary columns inside it are drawn on no plan (count not printed, T-065 M4): the column "
                      "share moves to the column line, so the beam's own volume has no established low end"]}
    rows.append({"run": bw["run_id"], "component": "BOUNDARY-GB at N.G.", "part": "PLOT", "direction": "-",
                 "b_m": 0.20, "L_m": round(bw_len, 4), "length_basis": "band plan area / drawn width",
                 "titles": "p.14 20x40", "S1": "-", "S2": "-", "S3": "-", "class_why": "-", "d33_tees": "",
                 "end_adjust_m2": "", "end_notes": "no overlap with any building beam or column (0.0000 m2)",
                 "status": bw["status"], "value_m3": "", "low_m3": "", "high_m3": f"{bw_solid:.4f}",
                 "reasons": bw["reasons"][0]})

    comp = {"interior": GL.component_total(runs["interior"]), "exterior": GL.component_total(runs["exterior"]),
            "court_or_candidates": GL.component_total(runs["other"]),
            "boundary_gb": {"runs": 1, "calculated_m3": 0.0, "held_runs": 1, "held_low_m3": None,
                            "held_high_m3": bw_solid, "held_no_value": [], "band_m2": round(bw_area, 4),
                            "band_length_m": round(bw_len, 4)},
            "ground_slab": {"status": "NOT_MEASURED", "why": "keyed STR.CONC.GROUND_SLAB; not re-measured in T-242"}}
    closable, why_not = GL.line_closable(comp)

    # the interior component split by what holds it
    int_split = {}
    for r in runs["interior"]:
        key = ("CALCULATED" if r["status"] == GL.CALCULATED else
               "+".join(sorted({x.split(" ")[0] for x in r["reasons"] if x.startswith("D-")})) or
               ("NECK-SECTION CONFLICT (T-217)" if r["status"] == GL.CONFLICT else "HELD"))
        e = int_split.setdefault(key, {"runs": 0, "low": 0.0, "high": 0.0})
        e["runs"] += 1
        e["low"] += r["low_m3"]
        e["high"] += r["high_m3"]
    int_split = {k: {"runs": v["runs"], "low_m3": round(v["low"], 4), "high_m3": round(v["high"], 4)}
                 for k, v in sorted(int_split.items())}
    ext_split = {}
    for r in runs["exterior"]:
        key = r["status"] + (" (annex: literal depth below every printed section)" if r["status"] == GL.CONFLICT
                             else " (main house: D-35)")
        e = ext_split.setdefault(key, {"runs": 0, "low": 0.0, "high": 0.0})
        e["runs"] += 1
        e["low"] += r["low_m3"]
        e["high"] += r["high_m3"]
    ext_split = {k: {"runs": v["runs"], "low_m3": round(v["low"], 4), "high_m3": round(v["high"], 4)}
                 for k, v in sorted(ext_split.items())}

    # lengths for the freelancer reconciliation (building beams only)
    def lsum(pred):
        return round(sum(float(x["L_m"]) for x in rows if x["component"].startswith("GB-") and pred(x)), 4)
    drawn = {}
    for s in inp["spans"]:
        drawn.setdefault(s["band_id"], (s["direction"], s["band_drawn_m"]))
    fl_len = {"longitudinal": fl["C13"], "transverse": fl["C14"], "boundary": fl["C15"]}
    lengths = {"face_to_face_X_m": lsum(lambda x: x["direction"] == "X"),
               "face_to_face_Y_m": lsum(lambda x: x["direction"] == "Y"),
               "face_to_face_oblique_m": lsum(lambda x: x["direction"] == "OBLIQUE"),
               "curved_m": lsum(lambda x: x["direction"] == "ARC"),
               "drawn_bands_X_m": round(sum(v[1] for v in drawn.values() if v[0] == "X"), 4),
               "drawn_bands_Y_m": round(sum(v[1] for v in drawn.values() if v[0] == "Y"), 4),
               "drawn_bands_oblique_m": round(sum(v[1] for v in drawn.values() if v[0] == "OBLIQUE"), 4),
               "freelancer": fl_len}
    freel = {"slab_m3": fl["E11"], "slab_m2": fl["B11"], "slab_t_m": fl["D11"],
             "longitudinal_m3": fl["E13"], "transverse_m3": fl["E14"], "boundary_m3": fl["E15"],
             "section_m": [fl["B13"], fl["D13"]], "total_m3": fl["I16"], "summary_row_18": fl["SUMMARY_E18"]}

    # building beams against the freelancer's 211 m x 0.30 x 0.60 (his 'longitudinal' + 'transverse' rows)
    bld = [r for r in runs["interior"] + runs["exterior"] + runs["other"]]
    b_lo = sum(r["low_m3"] for r in bld)
    b_hi = sum(r["high_m3"] for r in bld)
    L_ours = (lengths["face_to_face_X_m"] + lengths["face_to_face_Y_m"] + lengths["face_to_face_oblique_m"]
              + lengths["curved_m"])
    L_his = fl["C13"] + fl["C14"]
    sec_his = fl["B13"] * fl["D13"]
    recon = {"his_m3": round(fl["E13"] + fl["E14"], 4), "ours_low_m3": round(b_lo, 4), "ours_high_m3": round(b_hi, 4),
             "his_length_m": L_his, "our_face_to_face_length_m": round(L_ours, 4),
             "length_effect_m3": round((L_his - L_ours) * sec_his, 4),
             "section_effect_low_m3": round(L_ours * sec_his - b_hi, 4),
             "section_effect_high_m3": round(L_ours * sec_his - b_lo, 4),
             "note": "his - ours = length (his lengths run through the supports: the drawn bands sum "
                     f"{lengths['drawn_bands_X_m'] + lengths['drawn_bands_Y_m'] + lengths['drawn_bands_oblique_m']:.2f}"
                     " m + curved) + section (his 0.30 x 0.60 on every beam vs the printed 0.30 / 0.40 / 0.60 "
                     "interior and FOLLOW ARCH. exterior depths); the end pieces are inside 'ours'"}
    recon["residual_low_m3"] = round(recon["his_m3"] - b_hi - recon["length_effect_m3"] - recon["section_effect_low_m3"], 6)
    recon["residual_high_m3"] = round(recon["his_m3"] - b_lo - recon["length_effect_m3"] - recon["section_effect_high_m3"], 6)
    bw_recon = {"his_m3": fl["E15"], "his_length_m": fl["C15"], "his_section_m2": fl["B15"] * fl["D15"],
                "drawn_m3": bw_solid, "drawn_length_m": round(bw_len, 4), "drawn_section_m2": 0.08,
                "section_effect_m3": round(bw_len * (fl["B15"] * fl["D15"] - 0.08), 4),
                "length_effect_m3": round((fl["C15"] - bw_len) * fl["B15"] * fl["D15"], 4)}
    # D-34 information only: the most specific p.13 title on the face-to-face basis (NOT applied, NOT released)
    d34_reading = 0.0
    for r_, x in zip(runs["interior"], [x for x in rows if x["component"] == "GB-INTERIOR"]):
        L_ = float(x["L_m"])
        d = None if abs(L_ - 5.0) < 1e-6 else (0.60 if L_ > 5.0 else 0.40 if L_ >= 2.5 else 0.30)
        if d is None:
            d34_reading = None
            break
        d34_reading += float(x["b_m"]) * L_ * d
    summary = {"policy": GL.policy_record(), "components": comp, "interior_split": int_split,
               "freelancer_reconciliation_building_beams": recon, "freelancer_reconciliation_boundary": bw_recon,
               "d34_information_most_specific_title": d34_reading,
               "exterior_split": ext_split, "line_closable": closable, "line_not_closable_because": why_not,
               "lengths": lengths, "freelancer": freel,
               "partition": {k: v for k, v in inp["partition"].items() if not isinstance(v, list)},
               "partition_named_pieces": [p for p in part_pieces if p["plan_m2"] > 0],
               "alignment": inp["alignment"],
               "classification": {k: sum(1 for x in rows if x["component"].startswith("GB-" + k))
                                  for k in (GL.INTERIOR, GL.EXTERIOR, GL.COURT, GL.CANDIDATES)}}
    if write:
        with open(HERE / "LEDGER_T242.csv", "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)
        (HERE / "summary.json").write_text(json.dumps(summary, indent=1, sort_keys=True, ensure_ascii=False) + "\n",
                                           encoding="utf-8")
    return rows, summary


if __name__ == "__main__":
    rows, s = main(write="--write" in sys.argv)
    buf = io.StringIO()
    for r in rows:
        print(r["run"], r["component"], r["part"], r["L_m"], r["titles"], r["status"], r["value_m3"] or
              f"{r['low_m3']}..{r['high_m3']}", "|", r["class_why"], "|", r["end_notes"])
    print(json.dumps({k: s[k] for k in ("components", "interior_split", "exterior_split", "line_closable",
                                         "line_not_closable_because", "lengths", "freelancer", "classification")},
                     indent=1, ensure_ascii=False))
