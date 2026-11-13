"""T-751 exterior paint edge and corner bounds closure on the development villa (research; nothing wired).

Inputs (all committed, sha-pinned): the own DXF census in/T751_CENSUS.json (t751_census.py, private DXF read by hand),
the merged T-747 output (paint faces, window edges, corners by host), the T-172 vertical-corner ledger (per-corner caps),
the T-737 rows (the held corner rows), the T-159 face sides (NW-6 plinth). Rules R-T751-1 .. -4 (t751_rules.py).

    python -I research/agents_t751/t751_alsenan.py [--write | --check]
"""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import t751_rules as R  # noqa: E402

CENSUS = "research/agents_t751/in/T751_CENSUS.json"
T747 = "research/agents_t747/out/T747_EXT_PAINT.json"
T172 = "research/agents_t172/VERTICAL_CORNERS_T172.csv"
T737 = "research/agents_t737/out/T737_ROWS.csv"
T159 = "research/agents_t159/FACADE_SIDES_T159.csv"
PINS = [CENSUS, T747, T172, T737, T159]
OUT_JSON = HERE / "out" / "T751_EDGE_BOUNDS.json"
OUT_MD = HERE / "out" / "T751_EDGE_BOUNDS.md"
SCHEMA = "URBAN_T751_EDGE_BOUNDS_V1"
DATUM_1F_ROOF = Decimal("9.70")  # 2F F.F.L. / 1F roof +9.70 (T-159 'F2', printed 100 + 870 on all four elevations)
D = R.D
s6 = R.s6


def _p(rel):
    return ROOT / rel


def sha(rel):
    return hashlib.sha256(_p(rel).read_bytes()).hexdigest()


def jload(rel):
    return json.loads(_p(rel).read_text(encoding="utf-8"))


def rows(rel):
    with _p(rel).open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


# ---------------------------------------------------------------- corners (R-T751-1, R-T751-4)

def t172_caps():
    caps = {}
    for r in rows(T172):
        if r["floor"] == "1F" and r["type"].startswith("CONVEX"):
            caps[r["corner"]] = (D(r["held_top"]) - D(r["top"]), r["note"])
    return caps


def parapet_end_corners(cen):
    caps = t172_caps()
    c = cen["corners_1f"]
    out = []
    for cid, v in sorted(c.items()):
        if "vertical" in v:
            top = D(str(v["vertical"]["lv_hi"]))
            src = f"{v['frame']} frame, corner outline {v['vertical']['handle']} (layer 1) to {s6(top)}"
        else:
            top = D(str(v["top_line"]["lv_hi"]))
            src = f"{v['frame']} frame, the continuous top line {v['top_line']['handle']} at {s6(top)} over the corner"
        rr = None
        if "round" in v:
            rd = v["round"]
            if abs(D(str(rd["rise"])) - D(str(rd["run"]))) > D("0.00001"):
                raise R.RuleError(f"{cid}: end round not circular")
            rr = D(str(rd["rise"]))
            top = top + rr  # the vertical outline stops at the tangent point; the drawn top is one radius higher
            src += f", end round r {s6(rr)} ({rd['handles'][0]} .. {rd['handles'][-1]}) to the top {s6(top)}"
        it = R.corner_extra(cid, DATUM_1F_ROOF, top=top, round_r=rr, source=src)
        cap, why = caps[cid]
        it["t172_cap"] = s6(cap)
        it["t172_note"] = why
        if D(it["lm"][0]) > cap:
            it["cap_check"] = ("ABOVE THE T-172 CAP: the cap used the 1F printed parapet maximum +11.00; this corner is "
                               "the SE face's NE end, printed +11.30 ('6800' above +4.30 + '200', T-159 SE-1): the "
                               "printed level governs, the per-corner cap was wrong (the row bound 0 .. 11.90 holds)")
        else:
            it["cap_check"] = "inside the T-172 cap"
        if "beyond" in v:
            it["beyond"] = ("a higher element drawn on the beyond layer 5 (" +
                            " / ".join(b["handle"] for b in v["beyond"]) +
                            f", top {s6(D(str(max(b['lv_hi'] for b in v['beyond']))))}) stands behind the corner: not "
                            "the corner's own outline, not added here (R-T751-1 rule 3); named in the findings")
        out.append(it)
    return out


def plinth_corners(cen):
    pc = cen["plinth_corners"]
    out = []
    for cid in ("NW-3/NW-4", "NW-4/NW-5"):
        ln = pc[cid]
        it = R.corner_extra(cid, D(str(ln["lv_lo"])), top=D(str(ln["lv_hi"])),
                            source=f"NW frame plinth line {ln['handle']} (layer 1) {ln['lv_lo']} .. {ln['lv_hi']}: the "
                                   "arc end stands on the pool court +0.15, not on the pool rim +0.30 (rim lines "
                                   + " / ".join(x["handle"] for x in pc["arc_inner_rim"]) + " start at +0.30 inside "
                                   "the arc)")
        out.append(it)
    nw6 = [r for r in rows(T159) if r["FLOOR"] == "GF" and r["SIDE"] == "NW-6" and r["BOTTOM_M"] == "0.150"]
    if len(nw6) != 1 or nw6[0]["STATUS"] != "DRAWING-CONFIRMED" or nw6[0]["TOP_M"] != "1.000":
        raise R.RuleError("NW-6 plinth face not DRAWING-CONFIRMED +0.15 .. +1.00")
    out.append(R.corner_extra("SW-8/NW-6", D("0.15"), top=D("1.00"),
                              source="T-159 GF NW-6 plinth +0.15 .. +1.00 DRAWING-CONFIRMED over its whole 0.45 m: the "
                                     "convex corner at its NE end shares it"))
    return out


def held_rows():
    held = {}
    for r in rows(T737):
        if r["kind"] == "BEAD" and r["bead_class"] in ("EXTERNAL_CORNER", "MOUTH_WALL_END") and \
                r["bead_state_after"] in ("HELD_BOUND", "HELD_BLANK") and (r["low"] != r["high"] or not r["low"]):
            held[r["id"] + " -> " + r["host_after"]] = r
    return held


def corners(cen, t747):
    before = t747["edges"]["corners"]
    hr = held_rows()
    ends = parapet_end_corners(cen)
    pl = plinth_corners(cen)
    ends_sum = R.sum_lm(ends)["lm"]
    pl_sum = R.sum_lm(pl)["lm"]
    r_ends = hr["EXT#1F-CONVEX-PARAPET-ENDS -> NEW FIN.EXT.FINISH PARAPET-OUTER 1F +9.70"]
    r_pl = hr["EXT#GF-CONVEX-PLINTH -> NEW FIN.EXT.FINISH PLINTH GF"]
    r_stop = hr["EXT#GF-MOUTHS-STOP -> NEW FIN.EXT.FINISH PARAPET-OUTER GF +5.50"]
    r_nohost = hr["EXT#GF-MOUTHS -> NO_HOST"]
    closures = [
        R.close_bound("EXT#1F-CONVEX-PARAPET-ENDS (8 corners above +9.70)", r_ends["low"], r_ends["high"],
                      ends_sum[0], sorted({(v.get("vertical") or v["top_line"])["handle"]
                                           for v in cen["corners_1f"].values()})),
        R.close_bound("EXT#GF-CONVEX-PLINTH (3 pool-court corners below the F.F.L.)", r_pl["low"], r_pl["high"],
                      pl_sum[0], ["285E", "283E", "T-159 NW-6"]),
    ]
    lo_b, hi_b = D(before["total_lm"][0]), D(before["total_lm"][1])
    fixed_lo = lo_b - D(r_ends["low"]) - D(r_pl["low"]) - D(r_stop["low"])
    fixed_hi = hi_b - D(r_ends["high"]) - D(r_pl["high"]) - D(r_stop["high"])
    if fixed_lo != fixed_hi:
        raise R.RuleError("the non-held corner parts are not a point")
    after_lo = fixed_lo + D(ends_sum[0]) + D(pl_sum[0]) + D(r_stop["low"])
    after_hi = fixed_hi + D(ends_sum[1]) + D(pl_sum[1]) + D(r_stop["high"])
    nohost = D(r_nohost["part_m"])
    return {
        "before_lm": before["total_lm"], "fixed_part_lm": s6(fixed_lo),
        "parapet_ends": ends, "parapet_ends_lm": ends_sum, "plinth": pl, "plinth_lm": pl_sum,
        "closures": closures,
        "stop_end": {"row": "EXT#GF-MOUTHS-STOP", "lm": [s6(r_stop["low"]), s6(r_stop["high"])], "state": "HELD",
                     "cause": "GF house parapet (+5.50 -> +6.00) end at the passage mouth: free (stop-end 2 x 0.50 + "
                              "0.20) or abutting is shown on no vector view read (the NE elevation, sheet 09, is a "
                              "raster scan; the SE frame draws the GF parapet only beyond the annex, layer 5)"},
        "no_host": {"row": "EXT#GF-MOUTHS -> NO_HOST", "lm": s6(nohost), "state": "DRAWING-CONFIRMED, host blank",
                    "cause": "1.4 m of passage-mouth wall-end arris above the annex parapet top +4.80 to +5.50 "
                             "(T-737): the arris is measured; only its host face line is missing (wiring, T-749); "
                             "shown beside the hosted total, never 0"},
        "after_lm": [s6(after_lo), s6(after_hi)],
        "after_physical_lm": [s6(after_lo + nohost), s6(after_hi + nohost)],
        "narrowed_lm": s6((hi_b - lo_b) - (after_hi - after_lo)),
    }


# ---------------------------------------------------------------- windows (R-T751-2)

def windows(cen, t747):
    ops = {o["opening"]: o for o in t747["edges"]["openings"]}
    out = []
    for wid, w in sorted(cen["windows"].items()):
        o = ops[wid]
        if o["basis"] != "ARC_DEVELOPED":
            raise R.RuleError(f"{wid} is not carried as arched by T-747")
        rect_t746 = [x for x in o["others"] if x["source"] == "T-746 window OUT"][0]["lm"][0]
        it = R.arched_edge(wid, sill=str(w["sill"]), springing=str(w["springing"]),
                           head_developed=str(w["head_developed"]), width=str(w["width"]), crown=str(w["crown"]),
                           ledger=o["lm"][0])
        it["t746_rectangle"] = rect_t746
        it["t746_minus_developed"] = s6(D(rect_t746) - D(it["lm"]))
        it["evidence"] = (f"{w['frame']} frame: jambs {w['jambs'][0]} / {w['jambs'][1]} (layer 1) sill "
                          f"{w['sill']}" + (f" (line {w['sill_line']})" if w["sill_line"] else "") +
                          f" -> springing {w['springing']}; head chain {w['head_handles'][0]} .. {w['head_handles'][1]}"
                          f" ({w['head_segments']} segments) developed {w['head_developed']} over {w['width']}, "
                          f"crown {w['crown']}")
        out.append(it)
    before = D(t747["edges"]["summary"]["windows"]["lm"][0])
    ledger_sum = sum(D(it["ledger"]) for it in out)
    dev_sum = sum(D(it["lm"]) for it in out)
    rect_sum = sum(D(it["t746_rectangle"]) for it in out)
    after = before - ledger_sum + dev_sum
    t746_total = D(t747["edges"]["summary"]["reconciliation"]["t746_outside_edge_lm_all"])
    recon = t746_total - (rect_sum - dev_sum) - after
    if recon != 0:
        raise R.RuleError(f"window lm reconciliation residual {recon}")
    return {"arched": out, "before_lm": s6(before), "after_lm": s6(after), "ledger_to_dxf_lm": s6(dev_sum - ledger_sum),
            "t746_lm": s6(t746_total), "t746_minus_after": s6(t746_total - after),
            "held": t747["edges"]["summary"]["windows"]["held"], "residual": s6(recon)}


# ---------------------------------------------------------------- the SE entrance surround (R-T751-3)

def surround(cen, t747):
    s = cen["surround"]
    face = {f["face_id"]: f for f in t747["faces"]}
    st, pl = face["GF/SE-2/COVERED/storey"], face["GF/SE-2/COVERED/plinth"]
    zone747 = sum(D(d["m2"]) for f in (st, pl) for d in f["deductions"])
    att = R.plane_attribution(s["piece_layer"], s["door_line"]["layer"])
    total = D(str(s["t360_visible_m2"]))
    inside = D(str(s["inside_t747_span_m2"]))
    right = total - inside
    rings = inside - zone747
    crown = D(str(s["blocks_right_of_span"][0]["face_m2"]))
    return {
        "t747_zone_m2": s6(zone747), "t360_visible_m2": s6(total), "difference_m2": s6(total - zone747),
        "explained": {"right_of_t747_span_m2": s6(right), "of_which_crown_block_m2": s6(crown),
                      "of_which_band_and_cut_strip_m2": s6(right - crown),
                      "pen_rings_and_joints_inside_span_m2": s6(rings),
                      "residual_m2": s6(total - zone747 - right - rings)},
        "split_at_ffl_m2": {"below_+1.00": s6(str(s["below_ffl_m2"])), "above_+1.00": s6(str(s["above_ffl_m2"]))},
        "keystone": {"inner_outline": s["crown_inner_handles"], "outer_ring": s["crown_outer_handles"],
                     "face_m2": s6(crown), "levels": [s["blocks_right_of_span"][0]["lv_lo"],
                                                      s["blocks_right_of_span"][0]["lv_hi"]],
                     "cut_by": s["cut_line"]["handle"]},
        "plane": {"piece_layer": s["piece_layer"], "door_line": s["door_line"]["handle"],
                  "door_layer": s["door_line"]["layer"], "landing_line": s["landing_line"]["handle"],
                  "landing_layer": s["landing_line"]["layer"], "attribution": att},
        "verdict": ("OFF_FACE: the stones are drawn on the front layer 1 in the porch-mouth plane; the face that holds "
                    "D-GF-07 (door line 1C00, landing 1BFE) is drawn beyond on layer 5. The surround is the porch-mouth "
                    "arch piece (T-360 C-1, an open side with no face key), not a zone of GF/SE-2: the SE-2 paint "
                    "deduction is 0 and the surround's own render / paint is a missing item HELD blank (material "
                    "unprinted, the half behind the annex section line 2416 UNKNOWN)"),
    }


# ---------------------------------------------------------------- paint lines after the closures

def paint_after(t747, sur, cen):
    lines = {ln["line_key"]: ln for ln in t747["lines"]}
    face = {f["face_id"]: f for f in t747["faces"]}
    changes = []
    if sur["plane"]["attribution"] == "OFF_FACE":
        for fid in ("GF/SE-2/COVERED/storey", "GF/SE-2/COVERED/plinth"):
            f = face[fid]
            changes.append({"face_id": fid, "line_key": f["line_key"], "what": "surround deduction removed (R-T751-3)",
                            "paint_before": f["paint"], "paint_after": f["render"],
                            "render": f["render"], "render_after": f["render"]})
    pf = face["1F/NW-5/SW-PIER-RETURNS/parapet"]
    width = D("0.536522")  # T-567 R-T567-6 pier return lengths 0.305222 + 0.157080 + ... (its md, section 5)
    top = D(str(cen["pier"]["top_line"]["lv_hi"]))
    span = D(str(cen["pier"]["top_line"]["dx"]))
    if span != D("1.005222"):
        raise R.RuleError("pier top line span is not the T-567 pier span 1.005222")
    val = width * (top - DATUM_1F_ROOF)
    cl = R.close_bound("1F/NW-5/SW-PIER-RETURNS/parapet m2", pf["render"][0], pf["render"][1], val,
                       [cen["pier"]["top_line"]["handle"]] + [e["handle"] for e in cen["pier"]["edges"]])
    changes.append({"face_id": pf["face_id"], "line_key": pf["line_key"],
                    "what": f"pier top drawn at {s6(top)} (27CA over the pier span 1.005222; edges 25B3 / 270A / 2728 / "
                            "2783 to the same top): 0.536522 x 1.30 (render and paint move together)",
                    "paint_before": pf["paint"], "paint_after": [s6(val), s6(val)],
                    "render": pf["render"], "render_after": [s6(val), s6(val)], "closure": cl})
    out_lines = []
    tot_p = [Decimal(0), Decimal(0)]
    tot_r = [Decimal(0), Decimal(0)]
    for key, ln in sorted(lines.items()):
        p = [D(ln["paint_m2"][0]), D(ln["paint_m2"][1])]
        r = [D(ln["render_m2"][0]), D(ln["render_m2"][1])]
        for c in changes:
            if c["line_key"] == key:
                for i in (0, 1):
                    p[i] += D(c["paint_after"][i]) - D(c["paint_before"][i])
                    r[i] += D(c["render_after"][i]) - D(c["render"][i])
        moved = p != [D(ln["paint_m2"][0]), D(ln["paint_m2"][1])] or r != [D(ln["render_m2"][0]),
                                                                           D(ln["render_m2"][1])]
        if moved:
            out_lines.append({"line_key": key, "element": ln["element"], "floor": ln["floor"],
                              "paint_before": ln["paint_m2"], "paint_after": [s6(p[0]), s6(p[1])],
                              "render_before": ln["render_m2"], "render_after": [s6(r[0]), s6(r[1])]})
        for i in (0, 1):
            tot_p[i] += p[i]
            tot_r[i] += r[i]
    t = t747["total"]
    if [s6(x) for x in tot_r] != [s6(D(t["render"][0]) + D(changes[-1]["render_after"][0]) - D(pf["render"][0])),
                                  s6(D(t["render"][1]) + D(changes[-1]["render_after"][1]) - D(pf["render"][1]))]:
        raise R.RuleError("render total does not re-add")
    return {"face_changes": changes, "lines_moved": out_lines,
            "total_before": {"paint": t["paint"], "render": t["render"]},
            "total_after": {"paint": [s6(x) for x in tot_p], "render": [s6(x) for x in tot_r],
                            "render_minus_paint": [s6(tot_r[0] - tot_p[0]), s6(tot_r[1] - tot_p[1])]},
            "blank_faces": t["blank_faces"]}


FINDINGS = [
    ("F-T751-1", "PRINTED_ABOVE_CAP", "T-172 capped the 1F NE-2 / SE-1 corner at +11.00 (1.30 above +9.70); the SE "
     "frame draws the corner line 1BFD to +11.30 and T-159 reads the SE face's NE end as printed +11.30 ('6800' above "
     "+4.30 + '200'): 1.60 lm above +9.70; the row bound 0 .. 11.90 still holds (closure inside it)."),
    ("F-T751-2", "DRAWING_FINDING", "1F NE-2 parapet top is not one level: the NW frame draws its NW end at +10.80 with "
     "an r 0.20 end round (27B6, 2584 .. 2579) and the SE frame its SE end at +11.30 (1BFD, 2220); the T-159 / T-747 "
     "NE-2 parapet outer face 19.27 x 1.30 = 25.051 m2 (sheet 09 '130') is therefore not a single-level face: the "
     "'130' witness line should be re-read by the Checker on sheet 09 (raster; nothing is scaled here). No m2 moved "
     "by this task; the step arris on the NE face (0.50 m where +11.30 drops to +10.80) is HELD blank by name "
     "(position not on a vector view)."),
    ("F-T751-3", "ENGINE_WRONG (T-747 attribution)", "the SE entrance stone surround is drawn on the front layer 1 in "
     "the porch-mouth plane, D-GF-07 and its landing on the beyond layer 5: the surround is not on GF/SE-2. T-747's "
     "0 .. 1.298383 m2 paint deduction on SE-2 (storey 1.075883 + plinth 0.222500) is removed; the surround is the "
     "T-360 C-1 porch-mouth arch piece (1.514884 m2 visible, crown block 0.134936 cut by 2416), an open side with no "
     "face key: its render / paint is a missing item HELD blank."),
    ("F-T751-4", "ENGINE_RIGHT on the arched heads", "W15 / W16 / W26 developed outlines re-measured from the DXF head "
     "chains agree with the merged T-405 ledger within 0.0004 m each; T-746's rectangles (to the crown) are refused: "
     "-2.338 lm."),
    ("F-T751-5", "HELD by name", "the NW-5 bay pier rises from +5.50 to +11.00 (NW frame) in front of a wave wall "
     "whose top is +9.80: its back above +9.80 (roof side) is drawn in no view read (the 2F plan draws only its front), "
     "so any arris there is HELD blank, not counted. The T-159 key corner SW-1 / NW-5 coincides with the pier's SW "
     "return (2783, the 0.08 recess return and the 0.305 pier return in one line): the arris there is the pier's "
     "rounded corner r 0.10 (2728 .. 2783), same height (+11.00); one arris, count unchanged."),
]


def build():
    cen = jload(CENSUS)
    t747 = jload(T747)
    cor = corners(cen, t747)
    win = windows(cen, t747)
    sur = surround(cen, t747)
    pa = paint_after(t747, sur, cen)
    doors = t747["edges"]["summary"]["doors"]
    return {
        "schema": SCHEMA, "rules": list(R.RULE_IDS), "version": R.VERSION,
        "pins": {p: sha(p)[:16] for p in PINS}, "census_dxf_sha16": cen["dxf_sha16"],
        "corners": cor, "windows": win,
        "doors": {"lm": doors["lm"], "state": "HELD (bound kept)",
                  "cause": "jambs 0 by the drawn frame posts (T-746); the head member's depth is drawn on no plan and "
                           "on no vector elevation (D-GF-07 is drawn beyond, layer 5, as a leaf + frame face only): head "
                           "0 .. w stays"},
        "surround": sur, "paint": pa,
        "slab_edge_1f": {"state": "HELD blank (6 faces), unchanged",
                         "cause": "slab / edge-beam depth below +5.50 at those faces is not printed on the architectural "
                                  "sheets; the structural sheets were not read this run (Q-68 finish HELD)"},
        "findings": [{"id": a, "verdict": b, "text": c} for a, b, c in FINDINGS],
    }


def md(d):
    c, w, s, p = d["corners"], d["windows"], d["surround"], d["paint"]
    L = ["# T751 exterior paint edge / corner bounds (generated by t751_alsenan.py; do not edit)", "",
         f"Pins: {', '.join(f'{k} {v}' for k, v in d['pins'].items())}; DXF {d['census_dxf_sha16']}.", "",
         "## Corners (lm)", "",
         f"Before {c['before_lm'][0]} .. {c['before_lm'][1]}; fixed part {c['fixed_part_lm']}; "
         f"after {c['after_lm'][0]} .. {c['after_lm'][1]} (narrowed {c['narrowed_lm']}); with the NO_HOST "
         f"{c['no_host']['lm']} DRAWING-CONFIRMED arris: {c['after_physical_lm'][0]} .. {c['after_physical_lm'][1]}.",
         "", "| corner | above datum lm | T-172 cap | check | source |", "|---|---|---|---|---|"]
    for it in c["parapet_ends"] + c["plinth"]:
        L.append(f"| {it['corner']} | {it['lm'][0]} | {it.get('t172_cap', '-')} | {it.get('cap_check', '-')[:40]} | "
                 f"{it['source']} |")
    for cl in c["closures"]:
        L.append(f"\n- closure {cl['item']}: {cl['before'][0]} .. {cl['before'][1]} -> {cl['after']}")
    L.append(f"- {c['stop_end']['row']} {c['stop_end']['lm'][0]} .. {c['stop_end']['lm'][1]} HELD: "
             f"{c['stop_end']['cause']}")
    L += ["", "## Arched windows (lm, outside jambs + head)", "",
          "| opening | developed (DXF) | ledger | diff | T-746 rectangle | rect - dev |", "|---|---|---|---|---|---|"]
    for it in w["arched"]:
        L.append(f"| {it['opening']} | {it['lm']} | {it['ledger']} | {it['ledger_diff']} | {it['t746_rectangle']} | "
                 f"{it['t746_minus_developed']} |")
    L.append(f"\nWindow outside edges {w['before_lm']} -> {w['after_lm']} lm (T-746 {w['t746_lm']}, "
             f"-{w['t746_minus_after']}); residual {w['residual']}; HELD {', '.join(w['held'])}.")
    L += ["", "## SE entrance surround (m2)", "",
          f"T-747 zone {s['t747_zone_m2']} vs T-360 visible {s['t360_visible_m2']}: +{s['difference_m2']} = right of "
          f"the T-747 span {s['explained']['right_of_t747_span_m2']} (crown block {s['explained']['of_which_crown_block_m2']}"
          f" + band / cut strip {s['explained']['of_which_band_and_cut_strip_m2']}) + pen rings / joints inside the "
          f"span {s['explained']['pen_rings_and_joints_inside_span_m2']}; residual {s['explained']['residual_m2']}.",
          f"Plane: {s['verdict']}", "", "## Paint lines moved (m2)", "", "| line | paint before | paint after | "
          "render before | render after |", "|---|---|---|---|---|"]
    for ln in p["lines_moved"]:
        L.append(f"| {ln['line_key']} | {ln['paint_before'][0]} .. {ln['paint_before'][1]} | {ln['paint_after'][0]} .. "
                 f"{ln['paint_after'][1]} | {ln['render_before'][0]} .. {ln['render_before'][1]} | "
                 f"{ln['render_after'][0]} .. {ln['render_after'][1]} |")
    ta, tb = p["total_after"], p["total_before"]
    L.append(f"\nTotal (valued faces) paint {tb['paint'][0]} .. {tb['paint'][1]} -> {ta['paint'][0]} .. "
             f"{ta['paint'][1]}; render {tb['render'][0]} .. {tb['render'][1]} -> {ta['render'][0]} .. "
             f"{ta['render'][1]}; render - paint {ta['render_minus_paint'][0]} / {ta['render_minus_paint'][1]}; "
             f"blank faces {len(p['blank_faces'])} (never 0).")
    L += ["", f"Doors {d['doors']['lm'][0]} .. {d['doors']['lm'][1]} lm HELD: {d['doors']['cause']}",
          f"1F slab edge: {d['slab_edge_1f']['state']}: {d['slab_edge_1f']['cause']}", "", "## Findings", ""]
    for f in d["findings"]:
        L.append(f"- {f['id']} {f['verdict']}: {f['text']}")
    return "\n".join(L) + "\n"


def main(argv):
    d = build()
    js = json.dumps(d, ensure_ascii=False, indent=1, sort_keys=True) + "\n"
    mt = md(d)
    if "--write" in argv:
        OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
        OUT_JSON.write_text(js, encoding="utf-8")
        OUT_MD.write_text(mt, encoding="utf-8")
        print("T751 outputs written")
    elif "--check" in argv:
        ok = OUT_JSON.read_text(encoding="utf-8") == js and OUT_MD.read_text(encoding="utf-8") == mt
        print("T751 outputs AGREE" if ok else "T751 outputs DIFFER")
        return 0 if ok else 1
    else:
        print(mt)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
