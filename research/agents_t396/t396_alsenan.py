"""T-396: the development villa's boundary / fence masonry above N.G. from the committed values-only input (research).

    python3 -I research/agents_t396/t396_alsenan.py           # print the ledger
    python3 -I research/agents_t396/t396_alsenan.py --write   # (re)write LEDGER / CROSS_TRADE / FREELANCER / summary
    python3 -I research/agents_t396/t396_alsenan.py --check   # committed outputs reproduce

The freelancer comparison is kept to his row's QUANTITIES in summary.json (no rate, no table of his sheet committed).

Inputs: ALSENAN_FENCE_INPUT.json (t396_extract.py on P7757.dxf: plan runs, elevation fence-end tops, layer-1 guard)
and the PRINTED facts below, each with its sheet (Drive "Alsenan chalet project", read this run; values only):

  P12_SECTION   Alsenan_Architectural_P7757_Pages_11-12.pdf p.12 'SECTION 1:100' of the fence: overall '265' from the
                lower ground line to the wall top = '50' (lower band, drawn in the same cross-hatch as the ground bands)
                + '215' (upper part, outline only); no level printed; no cut mark on the fence plan.
  P12_ELEVATION the same sheet, FENCE ELEVATION 1:100: the street solid wall has a curved dip filled with an X railing
                (dip profile NOT dimensioned); the 2.50 gate opening shows only a ground strip.
  ST14          ST7757.pdf p.14 TYPICAL BOUNDARY WALL: plan 'GROUND BEAM (20x40)', '(20x30) R.C COLUMNS 4d14' at 'SEE
                ARCH PLAN' (count / positions printed nowhere: M4), pads 130x80x30; section A-A: G.B top at 'N.G. LEVEL',
                column above with a break line (no height), 'Brick Wall' below 'AS PER EXCAVATION DEPTH BELOW N.G. LEVEL'
                down to the lower G.B.
  ST01_NOTE2    ST7757.pdf p.1 note 2: the exterior ground beams on the NEIGHBOUR side are cast above and below black
                block built from the foundation level (material of the BELOW-N.G. masonry on neighbour sides only).
  T253_RUNS     merged T-253 (Checker 07:20, own 0.0 %): upper G.B band runs 31.37 / 8.10 / 2.25 / 1.15 / 1.20 = 44.07 m.
  T392_POOL     T-392 (READY, Lead ruling 2026-10-31 12:30): sea line 8D 5.1684 = 0.9184 S + pool back 3.50 + 0.75 N.
"""

from __future__ import annotations

import csv
import io
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import boundary_fence as BF  # noqa: E402

INP = HERE / "ALSENAN_FENCE_INPUT.json"
LEDGER = HERE / "LEDGER_T396.csv"
CROSS = HERE / "CROSS_TRADE_T396.csv"
SUMMARY = HERE / "summary.json"

P12 = "Pages_11-12 p.12 SECTION '265' = '50' + '215'"
T253_BAND = {"north 7FE#1": 31.37, "street 7FE#2": 8.10, "sea 7FE#3": 2.25, "sea 7FC#1": 1.15, "lower 810#1": 1.20}
POOL_BACK = 3.50          # T-392 READY / Lead ruling: owned by the POOL wall line
SEA_S, SEA_N = 0.9184, 0.75
FREELANCER = {"row": "blockwork workbook sheet 'الكميات' row 150 (his 15 cm section)", "n": 1, "len": 37.20, "h": 2.00}


def build():
    d = json.loads(INP.read_text(encoding="utf-8"))
    nw, se = d["elevation_fence_end_nw"], d["elevation_fence_end_se"]
    corr = [f"NW elevation fence end {'/'.join(nw['handles'][:3])} top {nw['top_above_pm000_m']} above +-0.00 "
            f"(level {nw['handles'][3]})",
            f"SE elevation fence end {'/'.join(se['handles'][:3])} top {se['top_above_pm000_m']} above +-0.00 "
            f"(level {se['handles'][3]})"]
    h_printed = BF.height(2.65, "PRINTED", P12, corroborated_by=corr)
    h_sea = BF.height(se["top_above_pm000_m"], "DRAWN", "SE / NW elevations, gate-zone lines 2.50 above the court "
                      "+0.15 (not printed; owner Q-63 C holds the sea element)")
    h_none = BF.height(None, "NONE", "no printed top: passage closure partly under the GF roof +5.50 (T-361 E-02 "
                       "stop-end HELD)")
    st, no, sea, lo = d["street"], d["north"], d["sea"], d["lower_passage_closure"]
    sea_outer = round(sea["col_face_2F96_to_8D"] + sea["solid_8D"] + sea["zone_8E"], 6)
    rows = [
        BF.ledger_row("F-NORTH (upper neighbour)", no["outer_99_98"], [], [], h_printed, None,
                      lower_band=(0.50, "UNRESOLVED"), profile_cut="NONE"),
        BF.ledger_row("F-STREET", st["outer_10F"], [st["gate_gap_110"]], [], h_printed, None,
                      lower_band=(0.50, "UNRESOLVED"), profile_cut="UNDIMENSIONED", corner_owned_elsewhere_m=0.20),
        BF.ledger_row("F-SEA (Q-63 C element)", sea_outer, [1.00], [POOL_BACK], h_sea, None,
                      element_held=True, corner_owned_elsewhere_m=0.20),
        BF.ledger_row("F-LOWER passage closure", lo["outer_86"], [], [], h_none, None),
    ]
    # conservation against the Checker-verified G.B band (same runs, corner squares once)
    band_runs = {"F-NORTH (upper neighbour)": no["outer_99_98"], "F-STREET": round(st["outer_10F"] - 0.20, 6),
                 "F-SEA (Q-63 C element)": round(sea_outer - 0.20 - POOL_BACK, 6), "F-LOWER passage closure": lo["outer_86"]}
    band_total = round(sum(band_runs.values()), 6)
    assert abs(band_total - sum(T253_BAND.values())) < 1e-6, band_total
    assert abs(band_runs["F-SEA (Q-63 C element)"] - (T253_BAND["sea 7FE#3"] + T253_BAND["sea 7FC#1"])) < 1e-6
    assert abs(sea["col_face_2F96_to_8D"] + SEA_S - T253_BAND["sea 7FC#1"]) < 1e-6
    assert abs(SEA_N + sea["zone_8E"] - 0.20 - T253_BAND["sea 7FE#3"]) < 1e-6
    assert abs(SEA_S + POOL_BACK + SEA_N - sea["solid_8D"]) < 1e-6
    assert abs(rows[1]["solid_m"] - st["inner_13A_leg"]) < 1e-6          # street solid = inner face leg 5.60
    tot = BF.totals(rows)

    own_len = round(rows[0]["solid_m"] + rows[1]["solid_m"], 6)
    fr = BF.map_freelancer(FREELANCER["len"], FREELANCER["h"], [no["outer_99_98"], st["outer_10F"] - st["gate_gap_110"]],
                           0.20, own_len, 2.65)
    cross = [
        ("layer-1 wall lines on the fence bands (DXF guard)", sum(len(v) for v in d["layer1_wall_lines_on_fence_bands"].values()),
         "0 = no house wall band lies on any fence face (8 faces checked, 0.25 m, parallel)"),
        ("pool wall (POOL line, R-POOL)", 0, "pool back 3.50 m excluded from F-SEA by name (T-392 / Lead ruling); "
         "above the rim nothing is drawn in front of the pool drum (T-361): no fence counted there"),
        ("house facade faces (T-159 / T-337)", 0, "boundary / fence faces are NOT facade (register 2026-10-30, Q-65 C); "
         "fence runs are layer-5 plot-line bands"),
        ("T-279 / register v4 house blockwork (28 masonry lines, 76 walls)", 0,
         "register v4 holds storey walls GF/1F/2F only; GF-W15 7.100 is the entrance front (T-175), not the sea line"),
        ("boundary G.B concrete L-fb7a6431 (upper) / L-6290a9f3 (lower)", 0,
         "the wall stands ON the upper G.B (top at N.G.); runs conserve the band: 44.07 m = T-253"),
        ("fence railing RL-10 (MET guard, V3.0.30, HELD)", 0, "the X railing fills the street dip: it is the profile "
         "cut of F-STREET, carried by the railing line, never block"),
        ("gates G-01 2.50 / G-02 1.00 (T-361)", 0, "inside their runs, never wall"),
    ]
    cd = d["columns_drawn_in_fence_bands"]
    n_struct = sum(len(v["S-COL.BON"]) for v in cd.values())
    d_rects = [x[0] for v in cd.values() for x in v["D_rectangles"]]
    cross.append(("boundary columns 20 x 30 (ST p.14 'SEE ARCH PLAN', M4)", n_struct,
                  f"no S-COL.BON column inside any fence band on the arch GF plan; layer-D rectangles only at the sea "
                  f"wall ends ({', '.join(d_rects)}: nature not printed, part of the HELD sea element): the column count "
                  f"stays NOT PRINTED, block net HELD"))
    below = {"component": "boundary masonry BELOW N.G. (between the upper G.B soffit at N.G. - 0.40 and the lower G.B)",
             "length_m": band_total, "thickness_m": 0.20, "height": None, "status": BF.HELD,
             "missing_fact": "lower G.B top / excavation depth not printed (ST p.14 'AS PER EXCAVATION DEPTH'; T-356 / "
                             "T-357: existing ground printed at the plot corners only)",
             "material": "black block on the neighbour sides (ST p.1 note 2: north 31.37 + lower 1.20 = 32.57 m); street "
                         "8.10 and sea 3.40 m not printed",
             "in_any_line": "NO (no masonry line; the concrete lines carry only the two beams): MISSING category"}
    return d, rows, tot, band_runs, band_total, fr, cross, below


def _csv(rows, fields):
    b = io.StringIO()
    w = csv.DictWriter(b, fieldnames=fields, lineterminator="\n")
    w.writeheader()
    for r in rows:
        w.writerow({k: (json.dumps(r[k]) if isinstance(r.get(k), list) else r.get(k)) for k in fields})
    return b.getvalue()


def outputs():
    d, rows, tot, band_runs, band_total, fr, cross, below = build()
    fields = list(rows[0].keys())
    ledger = _csv(rows, fields)
    cross_csv = _csv([{"other_line": a, "overlaps": b, "evidence": c} for a, b, c in cross], ["other_line", "overlaps", "evidence"])
    summary = {"task": "T-396", "method": "BOUNDARY_FENCE_V1 (research, not wired)", "unit": "m / m2",
               "runs": {r["run"]: {"solid_m": r["solid_m"], "plane_m2": r["plane_m2"], "plane_status": r["plane_status"],
                                   "block_status": r["block_status"], "block_at_most_m2": r["block_at_most_m2"]} for r in rows},
               "band_conservation_m": {"runs": band_runs, "total": band_total, "t253_total": round(sum(T253_BAND.values()), 6)},
               "totals": tot, "freelancer": {"row": FREELANCER["row"], "his": [FREELANCER["n"], FREELANCER["len"], FREELANCER["h"]], **fr}, "below_ng": below,
               "column_face_per_unit_m2": round(BF.COLUMN_ALONG_WALL_M * 2.65, 6),
               "lower_band_m2_north_street": round(0.50 * (rows[0]["solid_m"] + rows[1]["solid_m"]), 6),
               "candidate_lines_changed": 0}
    return {LEDGER: ledger, CROSS: cross_csv,
            SUMMARY: json.dumps(summary, indent=1, sort_keys=True, ensure_ascii=False) + "\n"}


def main(argv):
    outs = outputs()
    if "--write" in argv:
        for p, s in outs.items():
            p.write_text(s, encoding="utf-8")
        print("written:", ", ".join(p.name for p in outs))
        return 0
    if "--check" in argv:
        bad = [p.name for p, s in outs.items() if not p.exists() or p.read_text(encoding="utf-8") != s]
        print("committed outputs reproduce" if not bad else f"DIFFER: {bad}")
        return 1 if bad else 0
    print(outs[LEDGER])
    print(outs[SUMMARY])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
