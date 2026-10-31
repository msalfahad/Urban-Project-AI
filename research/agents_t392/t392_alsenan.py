"""T-392 reconciliation on the development villa (Alsenan; method every villa). Research only: no line, state, rule,
method or released cell changes; corrected quantities are PROPOSALS for the Checker / lane I.

Inputs: the private geometry summary of t392_geom.py (areas, m3 and handles only) and the committed T-387 binding of
the candidate of record V3.0.29 (research/agents_t387/BINDING_T387.csv: line ids and figures). Output:
research/agents_t392/summary_t392.json (no coordinate, polygon, name or drawing content).

    python3 -I research/agents_t392/t392_geom.py <private ST dxf> <private geometry.json> <private>/geom_out.json \\
        <private P7757.dxf>
    python3 -I research/agents_t392/t392_alsenan.py <private>/geom_out.json --out research/agents_t392
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "research" / "agents_t387"))
import t392_rules as R  # noqa: E402
import t387_rules as R7  # noqa: E402

BINDING = ROOT / "research/agents_t387/BINDING_T387.csv"
LINE = {  # member -> candidate line id (V3.0.29, T-387 binding)
    "RING-B7": "L-e72c162de78a4bf302c0", "B8 BAND0003": "L-9a55aadc9f0880ae37a7",
    "B7 BAND0006": "L-cbf53752cfd897c35c2c", "CB1 BAND0041.2": "L-9270e8b8860414386adb",
    "B4 BAND0018": "L-a38b4013f5e3a30830b4", "CB4 BAND0021.1": "L-0e110d2c29b2cd318139",
    "CB8 BAND0039": "L-7c1a1da8004c4272ccba", "B27 BAND0048": "L-3dddf99008ab922da814",
    "BOUNDARY upper G.B": "L-fb7a6431fede62e93fd5", "BOUNDARY lower band": "L-6290a9f3d93f38cd46d6",
}
# the merged ledgers that wrote each line (formula field first; R-T387-7 every ledger): name -> signed m3 vs the route
# G band figure. Sources: T-146_ARCH_V3012.md s.2 'Ring overlap removed once' + V3012_BEAM_RUNS.csv adjust column;
# T-252_BEAM_LEDGER_R2.md s.1 (R-BEAM-END-OBLIQUE-2) + LEDGER_T252.csv; T-229 CENSUS.csv rows 232 / 233; the T-252
# ledger m3 rounded to 4 dp where its run carried 0.528 / 1.3388.
LEDGERS = {
    "B8 BAND0003": [("T-146 ring-overlap deduction (0.00178 m2 x 0.75)", -0.001335),
                    ("T-252 ledger m3 to 4 dp (0.528021 -> 0.5280)", -0.000021)],
    "B7 BAND0006": [("T-146 ring-overlap deduction (0.00047 m2 x 0.75)", -0.000353)],
    "CB1 BAND0041.2": [("T-146 ring-overlap deduction (0.00117 m2 x 0.75)", -0.000878),
                       ("T-252 ledger m3 to 4 dp (1.33875 -> 1.3388)", +0.000050)],
    "B4 BAND0018": [("T-252 r2 R-BEAM-END-OBLIQUE-2 both edges 27D / 282 to S-BEAM 325", +0.007381)],
    "CB4 BAND0021.1": [("T-252 r2 R-BEAM-END-OBLIQUE-2 both edges 288 / 285 to S-BEAM 325", +0.013550)],
    "CB8 BAND0039": [("T-229 column 359 owns (0.40 x 0.20 x 0.75)", -0.060000)],
}
# T-387 MEMBERS_T387.csv residuals (census, route G band basis) of the three ring-overlap members, as merged
T387_RESIDUAL_M3 = {"B8 BAND0003": -0.001356, "B7 BAND0006": -0.000353, "CB1 BAND0041.2": -0.000828}
T387_LABEL = {"B8 BAND0003": "GAP", "B7 BAND0006": "OK_ROUNDING", "CB1 BAND0041.2": "OK_ROUNDING"}


def binding():
    with BINDING.open(encoding="utf-8") as f:
        return {r["line_id"]: r for r in csv.DictReader(f)}


def fig(b, member):
    r = b[LINE[member]]
    return float(r["valued_m3"]) if r["valued_m3"] else None, r["status"], r["status_reason"]


def build(geom):
    b = binding()
    out = {"schema": "T392_SUMMARY_V1", "candidate": "ARCH_TAKEOFF_V3.0.29 (T-387 binding, lines 6b5dc44f)",
           "dxf_sha256": geom["dxf_sha256"][:16], "lines": {k: v for k, v in LINE.items()}}
    ring = geom["ring"]
    # (A) RING-B7: R-T392-4
    pieces = [(p, u) for p, u in ring["not_covered_by_piece_m2"]]
    others = sum(v.get("drawn_cell_in_ring_m2") or 0.0 for v in geom["ring_neighbours"].values()) + \
        sum(v["band_in_ring_m2"] for v in geom["ring_neighbours"].values())
    loc = R.locate_residual(ring["area_m2"], pieces, 0.75, others)
    rv, rs, _ = fig(b, "RING-B7")
    out["A_ring_B7"] = {
        "drawn_m2_densified": ring["area_m2"], "drawn_m2_exact_T252": 0.666406, "line_m3": rv, "line_status": rs,
        "own_m3_densified": ring["m3"], "own_minus_line_m3": round(ring["m3"] - rv, 6),
        "pieces_m2": ring["pieces_m2"], "route_g_arc_bands_m2": round(sum(x["band_m2"] for x in
                                                                        ring["route_g_arc_bands"].values()), 6),
        "arc_bands_in_ring_m2": ring["covered_by_arc_bands_m2"],
        "arc_bands_outside_ring_m2": round(sum(x["outside_ring_m2"] for x in ring["route_g_arc_bands"].values()), 6),
        "not_covered_m2": ring["not_covered_m2"], "located": loc,
        "census_residual_m3": 0.218186,
        "census_residual_explained": "census = (0.666407 - 0.375492) x 0.75: its band figure includes the bands' "
                                     "0.000750 m2 outside the drawn ring; own uncovered plan x 0.75 = located m3",
        "other_lines_in_ring_m2": others,
        "status": "LOCATED: drawn ring extension billed once by RING-B7; no other line's cell or band in the ring",
    }
    # (B) T-146 ring-overlap deduction: R-T392-1 per band, R-T387-7 on the census residual
    b146 = {}
    for mem, key in (("B8 BAND0003", "BAND0003"), ("B7 BAND0006", "BAND0006"), ("CB1 BAND0041.2", "BAND0041.2")):
        n = geom["ring_neighbours"][key]
        ded = [v for nm, v in LEDGERS[mem] if nm.startswith("T-146")][0]
        drawn_ov = max(n["band_in_ring_m2"], n.get("drawn_cell_in_ring_m2") or 0.0)
        chk = R.overlap_deduction(-ded / 0.75, drawn_ov, 0.75, LEDGERS[mem][0][0])
        cls = R7.classify_residual(T387_RESIDUAL_M3[mem], LEDGERS[mem])
        lv, ls, _ = fig(b, mem)
        drawn = (n.get("drawn_cell_m2") or n["band_m2"]) * 0.75
        b146[mem] = {"line_m3": lv, "drawn_band_m3": round(drawn, 6), "band_m2": n["band_m2"],
                     "band_in_ring_m2": n["band_in_ring_m2"], "drawn_cell_in_ring_m2": n.get("drawn_cell_in_ring_m2"),
                     "t146_deduction_m3": ded, "rule_R_T392_1": chk, "census_label_was": T387_LABEL[mem],
                     "rule_R_T387_7": cls, "proposed_m3": round(drawn, 6), "proposed_minus_line_m3":
                     round(drawn - lv, 6)}
    tot = round(sum(-v["t146_deduction_m3"] for v in b146.values()), 6)
    out["B_t146_ring_overlap"] = {"members": b146, "total_deducted_m3": tot,
                                  "total_gap_m3": round(sum(v["rule_R_T392_1"]["m3"] for v in b146.values()), 6),
                                  "status": "GAP (named): the 0.00342 m2 came from the T-110 band set fitted to the "
                                            "route G overlay (fit error 0.6 mm); on the candidate's own bands and on "
                                            "the drawn cells B8 / B7 / CB1 hold 0 m2 of the drawn ring, and RING-B7 is "
                                            "closed by the B8 face 46D, so no line carries it"}
    # (C-small) the 0.0235 m3 group
    sm = {}
    for mem, key in (("B4 BAND0018", "B4_BAND0018"), ("CB4 BAND0021.1", "CB4_BAND0021.1")):
        g = geom[key]
        lv, _, _ = fig(b, mem)
        band = g["band_m2"] * 0.5
        sm[mem] = {"line_m3": lv, "own_trapezoid_m3": g["trapezoid_m3"], "route_g_band_m3": round(band, 6),
                   "residual_vs_band_m3": round(lv - band, 6),
                   "rule_R_T387_7": R7.classify_residual(round(lv - band, 6), LEDGERS[mem]),
                   "own_minus_line_m3": round(g["trapezoid_m3"] - lv, 6)}
    g = geom["CB8_BAND0039"]
    lv, _, _ = fig(b, "CB8 BAND0039")
    end = R.band_end_vs_face(g["band_m2"], g["drawn_cell_to_326_m2"], g["band_beyond_326_m2"],
                             g["cell_not_in_band_m2"], g["column_37D_in_cell_m2"], 0.75)
    sm["CB8 BAND0039"] = {"line_m3": lv, "census_residual_m3": 0.002589,
                          "census_cause": "census deducted the route G B27 band overlap 0.00345 m2 from CB8's owned plan "
                                          "(B27 group owns the junction) while the line bills its band rectangle: "
                                          "0.00345 x 0.75 = 0.002588",
                          "band_m2": g["band_m2"], "drawn_cell_to_face_326_m2": g["drawn_cell_to_326_m2"],
                          "column_359_m2": g["column_359_in_cell_m2"], "column_37D_in_cell_m2":
                          g["column_37D_in_cell_m2"], "edge_2AC_past_326_mm": g["edge_2AC_end_past_326_mm"],
                          "rule_R_T392_2": end, "own_drawn_net_m3": g["drawn_net_m3"],
                          "proposed_m3": g["drawn_net_m3"], "proposed_minus_line_m3": round(g["drawn_net_m3"] - lv, 6),
                          "b27_host_face_m2": g["overrun_host_face_m2"]}
    out["C_small_residuals"] = {"members": sm,
                                "census_group_m3": 0.0235,
                                "documented_m3": round(0.007381 + 0.013550, 6),
                                "census_artefact_m3": 0.002589}
    # (D) pool fourth side: R-T392-3
    p = geom["pool_fourth_side"]
    gb_lv = fig(b, "BOUNDARY upper G.B")
    lb_lv = fig(b, "BOUNDARY lower band")
    owner = {"element": "plot boundary wall (upper G.B 20 x 40 top at N.G. + lower boundary band below; masonry above "
                        "N.G.)",
             "lines": [{"sheet": "ST ground-beam plan S-BOUN 7FC / 7FE (upper G.B 20 x 40)",
                        "line_id": LINE["BOUNDARY upper G.B"], "status": gb_lv[1] + " (" + gb_lv[2] + ")"},
                       {"sheet": "ST foundation plan S-BOUN 1658 / 1659 (lower boundary band)",
                        "line_id": LINE["BOUNDARY lower band"], "status": lb_lv[1] + " (" + lb_lv[2] + ")"},
                       {"sheet": "architectural GF plan B7 / 8D above N.G. (boundary wall masonry, lane A)",
                        "line_id": None, "status": "MISSING (T-279: the boundary fence is in no masonry line)"}]}
    sp = R.split_side(p["pair_length_m"], p["pool_side_m"], p["out_of_pool_south_m"], p["out_of_pool_north_m"], owner)
    gb = p["ground_beam_plan_upper_GB"]
    out["D_pool_fourth_side"] = {
        "geometry": p, "split": sp,
        "upper_GB_plan_m2_over_outside_parts": round(0.20 * (gb["7FC"]["over_south_part_m"] +
                                                             gb["7FE"]["over_north_part_m"]), 6),
        "upper_GB_m3_over_outside_parts": round(0.20 * 0.40 * (gb["7FC"]["over_south_part_m"] +
                                                               gb["7FE"]["over_north_part_m"]), 6),
        "upper_GB_over_pool_back_m": gb["7FC"]["over_pool_back_m"] + gb["7FE"]["over_pool_back_m"],
        "lower_band_over_pool_back_m": p["foundation_plan_lower_band"]["1658"]["over_pool_back_m"],
        "pool_lines_carry_outside_part": False,
        "status": "OWNER NAMED (boundary wall); concrete below N.G. in two HELD boundary lines (never 0), masonry above "
                  "N.G. MISSING; not pool concrete",
    }
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("geom")
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    geom = json.loads(Path(a.geom).read_text(encoding="utf-8"))
    s = build(geom)
    Path(a.out, "summary_t392.json").write_text(json.dumps(s, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: v.get("status") if isinstance(v, dict) else v for k, v in s.items()}, indent=1))


if __name__ == "__main__":
    main()
