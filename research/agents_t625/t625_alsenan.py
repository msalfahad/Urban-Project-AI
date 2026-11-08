"""T-625 builder (research, unwired): the T-621 floor-tile carry-forward rows restated from T625_DRAWN.json under
R-T625-1: row 0 (GF round-stair footprint below the cut) own area from its entities, and the open sides of GF-OPEN.full
(rows 2-5, 9) and 1F-LIV (rows 11-13) named with the printed line, door or dimension that bounds each, deltas classed.
No line, class or quantity of the candidate moves: proposals for the Checker / lane I only.

    python3 -I research/agents_t625/t625_alsenan.py           (write out/)
    python3 -I research/agents_t625/t625_alsenan.py --check   (rebuild and compare)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import t625_rules as R  # noqa: E402

D = Decimal
DRAWN = HERE / "T625_DRAWN.json"
T621 = ROOT / "research" / "agents_t621" / "out" / "T621_ROW_EVIDENCE.json"
T621_SHA = "6bb6a8af06130559809cc700dcd15c6c03019927cc452dc9a1db88054eb3c36d"
OUT_JSON = HERE / "out" / "T625_EVIDENCE.json"
OUT_MD = HERE / "out" / "T625_EVIDENCE.md"
T621_MEASURES = {"GF-OPEN.full": D("147.657717"), "1F-LIV.floor_printed": D("38.5855"), "1F-LIV.floor_drawn": D("38.988")}
ENGINE_1F = D("38.633536")      # porcelain 33.711036 + arrival marble 4.9225 (T-240 / T-621 beside)
ARRIVAL_RULE_PIECE = D("0.0475")  # T-240 / T-269: well end -0.010 + nosing band 0.0575 (by reference)
ROWS_GF, ROWS_1F = (2, 3, 4, 5, 9), (11, 12, 13)


def _sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def build():
    if _sha(T621) != T621_SHA:
        raise R.RuleError("T-621 row evidence changed: re-pin its sha256 after reading the change")
    d = json.loads(DRAWN.read_text(encoding="utf-8"))
    rows = json.loads(T621.read_text(encoding="utf-8"))["rows"]
    st = d["stair_row0"]
    b = st["beside"]
    # ---- row 0: own tread band below the cut (R-T625-1 (4))
    parts = {
        "F1 curved tread band (arcs 239 / 23D, nosing 256 to the arc ends)":
            {"area": st["F1_band_exact"], "role": "BAND", "handles": ["239", "23D", "256"]},
        "F2 straight run (22E / A7, arc end to the cut 13C, less column 2FD2)":
            {"area": st["F2_run_net"], "role": "BAND", "handles": ["22E", "A7", "13C", "2FD2"]},
        "curtail of the first step (arc 258 to the inner tread arc 239; printed 963 ends on it)":
            {"area": b["curtail_first_step"], "role": "BESIDE", "handles": ["258", "239", "963"]},
        "inner string band, curve (23F / 239), net of the curtail":
            {"area": str(D(b["inner_string_curve"]) - D(b["inner_string_curve_in_curtail"])), "role": "BESIDE",
             "handles": ["23F", "239", "258"]},
        "inner string band, run (22C / 22E to the cut)":
            {"area": b["inner_string_run"], "role": "BESIDE", "handles": ["22C", "22E", "13C"]},
        "outer string band, curve (23D / 23E), inside the face (north of A8)":
            {"area": b["outer_string_curve_in_face"], "role": "BESIDE", "handles": ["23D", "23E", "A8"]},
    }
    fp = R.footprint(parts)
    row0 = rows[0]
    own0 = D(fp["band"])
    chord_route = D(st["F1_chord"]) + D(st["strip_arc_end_to_first_run_nosing"]) + D(st["F2_from_first_run_nosing_net"])
    status0, diff0, cause0 = R.classify_delta(
        own0, D(row0["delta"]),
        "the engine's tread union flattens the curved band into chords through the nosing points "
        f"(chord loss {st['F1_chord_loss']}) and its quads leave {chord_route - D(row0['delta'])}; CAD "
        f"{own0 - chord_route - D(st['F1_chord_loss'])} (run outer edge A7 vs the outer arc end, 0.05 mm)")
    split0 = {"chord_loss": st["F1_chord_loss"], "engine_quads_vs_chord_route": str(chord_route - D(row0["delta"])),
              "cad_arc_end_vs_A7": str(own0 - chord_route - D(st["F1_chord_loss"]))}
    if sum(D(v) for v in split0.values()) != diff0:
        raise R.RuleError("row 0 difference does not split exactly")
    beside_total = sum((D(v) for v in fp["beside"].values()), D(0))
    r0 = {"row": 0, "t621_class": row0["class"], "t621_delta": row0["delta"], "kind": "PIECE",
          "own": str(own0), "status": status0, "difference": str(diff0), "cause": cause0, "difference_split": split0,
          "F1": st["F1_band_exact"], "F2": st["F2_run_net"], "sweep_deg": st["sweep_deg"],
          "radii": [st["inner_r"], st["outer_r"]], "nosing_steps_deg": sorted(set(st["nosing_steps_deg"])),
          "engine_split_reproduced": {"F1_chord_plus_strip": str(D(st["F1_chord"]) +
                                                                 D(st["strip_arc_end_to_first_run_nosing"])),
                                      "F2_from_22F_net": st["F2_from_first_run_nosing_net"],
                                      "engine_F1_F2": ["4.094412", "2.03"]},
          "printed": st["printed"], "parts": parts, "beside": fp["beside"], "beside_total": str(beside_total),
          "class_proposal": {
              "row": "RULE_DIFFERENCE kept (UP-CER-001: the footprint is out of the tile; UP-STAIR-005 treads marble)",
              "quantity": f"ENGINE_WRONG {diff0} m2 (chord flattening of a drawn arc band): own {own0} governs",
              "curtail": f"ENGINE_WRONG {b['curtail_first_step']} m2: the first step's curtail is drawn (L5 arc 258) "
                         "and printed (963 ends on it, 0.0 mm): a tread, not porcelain; also absent from the F1 tread "
                         "marble line (4.094413): marble trade to check",
              "strings": f"UNRESOLVED 0 .. {D(parts['inner string band, curve (23F / 239), net of the curtail']['area']) + D(b['inner_string_run']) + D(b['outer_string_curve_in_face'])} m2: "
                         "0.05 bands drawn beside the tread edges (L5) are stair structure or cladding; ST-02 "
                         "structure undrawn (Q-50 / T-269 designer item); not floor finish by drawing, not added"},
          "effect_if_adopted": f"GF porcelain L-7625f35c -{diff0} (band) -{b['curtail_first_step']} (curtail) m2; "
                               f"row 0 amount {row0['delta']} -> {own0 + D(b['curtail_first_step'])} m2"}
    # ---- open-plan outlines (R-T625-1 (1)-(3))
    outs = {}
    for name, o in d["outlines"].items():
        acc = R.account(o["edges"])   # re-validated here: any undrawn side without evidence raises
        own = D(o["area_exact_net"])
        st_, diff, cause = R.classify_delta(own, T621_MEASURES[name], "")
        r2 = D(o["area_route2"]["area"])
        if abs(own - r2) > R.AREA_TOL:
            raise R.RuleError(f"{name}: the two area routes disagree")
        lv = [R.one_level([x["level"] for x in o["levels"]])]
        dims_ok = all(abs(D(v["diff"])) <= R.LENGTH_TOL for v in o["dim_checks"].values())
        outs[name] = {"own_exact_net": str(own), "t621_measure": str(T621_MEASURES[name]), "status": st_,
                      "difference": str(diff), "route2": o["area_route2"], "route2_minus_own": str(r2 - own),
                      "column_notch_at_boundary": o["column_notch_at_boundary"],
                      "columns_notched": o["columns_notched"], "columns_inside": o["columns_inside"],
                      "perimeter": acc["perimeter"], "metres_by_class": acc["metres"],
                      "open_sides": acc["open_sides"], "levels": lv, "level_marks": [x["mark"] for x in o["levels"]],
                      "printed_edge_checks": o["dim_checks"], "printed_checks_all_agree": dims_ok}
    gf = outs["GF-OPEN.full"]
    f1p, f1d = outs["1F-LIV.floor_printed"], outs["1F-LIV.floor_drawn"]
    ff = d["first_floor"]
    band = D(ff["arrival_band"]["area"])
    restated_1f = D(f1p["own_exact_net"]) + band
    readings_1f = {
        "east_lane_boundary": {"printed_edge": f1p["own_exact_net"], "last_drawn_nosing": f1d["own_exact_net"],
                               "difference": str(D(f1d["own_exact_net"]) - D(f1p["own_exact_net"])),
                               "governs": "PRINTED edge (10DF end, ST7757 459 on it at "
                                          f"{ff['st_lines']['459']['offset_to_arch_line_mm']} mm): the 0.4025 beyond "
                                          "it is the 12th tread 0.345 (stair, marble) + the landing nosing band "
                                          "0.0575 (arrival marble piece, T-240), never porcelain"},
        "rs_a_arrival_band": {"area": str(band), "handles": ff["arrival_band"]["handles"],
                              "st_riser_315_offset_mm": ff["st_lines"]["315"]["offset_to_arch_line_mm"],
                              "class_proposal": f"ENGINE_WRONG -{band} m2 (engine short): the landing nosing band in "
                                                "front of the top riser D24 (L2, ST 315 on it) up to nosing D22 (L5) "
                                                "is floor of the +5.50 living (R-T269 riser convention, as the "
                                                "east lane's 0.0575); in neither the printed reading nor the engine "
                                                "porcelain 33.711036; condition: no ST-02 stair line carries it"},
        "restated_floor_at_550": str(restated_1f),
        "engine_minus_restated": str(ENGINE_1F - restated_1f),
        "engine_minus_restated_split": {"arrival_rule_piece": str(ARRIVAL_RULE_PIECE), "rs_a_band": str(-band),
                                        "residual": str(ENGINE_1F - restated_1f - ARRIVAL_RULE_PIECE + band)},
        "slab_edge_margin": dict(ff["slab_edge_margin"], class_proposal=(
            f"UNRESOLVED 0 .. {ff['slab_edge_margin']['bound_m2']} m2, not added: the structural slab edge (ST 2D2 / "
            "2CF) lies 0.05 beyond the architectural void lines B74 / B75; the architectural line bounds the finish; "
            "the printed 1265 (1.25 = 0.05 + 1.15 + 0.05) makes the 0.05 west of B75 the round-stair flight's string; "
            "a void-edge / balustrade detail closes it")),
    }
    # T-621 rows carried forward
    row13 = rows[13]
    carry = []
    for i in ROWS_GF + ROWS_1F:
        r = rows[i]
        carry.append({"row": i, "class": r["class"], "delta": r["delta"], "t621_evidence": r["evidence_status"],
                      "boundary": "GF-OPEN.full" if i in ROWS_GF else "1F-LIV.floor_printed",
                      "boundary_status": "DRAWING_CONFIRMED (every open side named, R-T625-1)"})
    out = {"schema": "T625_EVIDENCE_V1", "rule": R.RULE_ID, "governing": R.GOVERNING,
           "drawn": str(DRAWN.relative_to(ROOT)), "t621": {"path": str(T621.relative_to(ROOT)), "sha256": T621_SHA},
           "row0": r0, "outlines": outs, "first_floor_readings": readings_1f, "carried_rows": carry,
           "row13_with_rs_a_band": {"his_minus_engine": row13["delta"],
                                    "if_band_adopted": str(D(row13["delta"]) - band), "class": "UNRESOLVED kept"},
           "rows_measured": "41 / 41 (row 0 own area this run; T-621 40 / 41)",
           "st_frame_residual_mm": d["st_frame"]["residual_mm"]}
    return out


def md(o):
    r0 = o["row0"]
    L = ["# T-625 floor tile carry-forward: round-stair footprint and open-plan boundaries (R-T625-1)", "",
         "Research only; no line, class or quantity of the candidate moves. Sources: Drive 'Alsenan chalet project' "
         "P7757.dxf and 'ST7757 dxf.dxf' (second drawing, frame residual "
         f"{o['st_frame_residual_mm']} mm), decoded into .work/private only.", "",
         "## Row 0: GF round-stair footprint below the cut", "",
         f"Own band {r0['own']} m2 = F1 {r0['F1']} (annular sector r {r0['radii'][0]} .. {r0['radii'][1]} m, sweep "
         f"{r0['sweep_deg']} deg, 12 treads at {', '.join(r0['nosing_steps_deg'])} deg) + F2 {r0['F2']} (run 1.15 wide "
         f"to the cut 13C, less column 2FD2). Row {r0['t621_delta']}: {r0['status']} {r0['difference']} m2 = "
         f"{r0['difference_split']}. Engine split reproduced: {r0['engine_split_reproduced']}.", "",
         "| Beside piece (not in the band) | m2 |", "|---|---|"]
    L += [f"| {k} | {v} |" for k, v in r0["beside"].items()]
    L += ["", "Proposals: " + "; ".join(f"{k}: {v}" for k, v in r0["class_proposal"].items()) + ".",
          f"Effect if adopted: {r0['effect_if_adopted']}.", "", "## Open-plan outlines", ""]
    for name, v in o["outlines"].items():
        L += [f"### {name}: own {v['own_exact_net']} m2 ({v['status']} {v['difference']} vs T-621 "
              f"{v['t621_measure']}; route 2 {v['route2']['area']}), level(s) {', '.join(v['levels'])}", "",
              f"Perimeter {v['perimeter']} m by class {v['metres_by_class']}; columns notched {v['columns_notched']}, "
              f"inside {v['columns_inside']}; printed edge checks all agree: {v['printed_checks_all_agree']}.", "",
              "| Edge | Open side | m | Bounded by | Status |", "|---|---|---|---|---|"]
        L += [f"| {s['edge']} | {s['class']} | {s['length']} | {' '.join(s['by'])} | {s['status']} |"
              for s in v["open_sides"]]
        L.append("")
    f = o["first_floor_readings"]
    L += ["## 1F living readings", "",
          f"- East lane: printed {f['east_lane_boundary']['printed_edge']} vs last drawn nosing "
          f"{f['east_lane_boundary']['last_drawn_nosing']} (+{f['east_lane_boundary']['difference']}): "
          f"{f['east_lane_boundary']['governs']}.",
          f"- RS-A arrival band {f['rs_a_arrival_band']['area']} m2: {f['rs_a_arrival_band']['class_proposal']}.",
          f"- Restated floor at +5.50: {f['restated_floor_at_550']} m2; engine - restated = "
          f"{f['engine_minus_restated']} = {f['engine_minus_restated_split']}.",
          f"- Slab edge margin: {f['slab_edge_margin']['class_proposal']}.",
          f"- Row 13 with the band: {o['row13_with_rs_a_band']}.", "", f"Rows measured: {o['rows_measured']}.", ""]
    return "\n".join(L)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    o = build()
    js, mdt = json.dumps(o, indent=1, sort_keys=True) + "\n", md(o)
    if a.check:
        same = OUT_JSON.read_text(encoding="utf-8") == js and OUT_MD.read_text(encoding="utf-8") == mdt
        print("rebuild", "identical" if same else "DIFFERS")
        return 0 if same else 1
    OUT_JSON.parent.mkdir(exist_ok=True)
    OUT_JSON.write_text(js, encoding="utf-8")
    OUT_MD.write_text(mdt, encoding="utf-8")
    print(mdt)
    return 0


if __name__ == "__main__":
    sys.exit(main())
