"""T-361 development villa: fencing / gates (B13-04), posts / glass panels (B7-11) and the open-edge guard census.

    python3 -I research/agents_t361/t361_alsenan.py [--write | --check]

Reads only committed, values-only inputs: ALSENAN_FENCE_GATE_INPUT.json (this task, from the private DXF by
t361_extract.py), research/agents_t164/RAILINGS_T164.csv (merged T-164, Checker re-measure 2026-10-22 20:21) and
research/agents_t162/PARAPETS_T162.csv (merged T-162 r2). Printed values read by eye on the PDF sheets this run are
constants below with their sheet (never scaled). Writes GATES_T361.csv, BOUNDARY_T361.csv, OPEN_EDGES_T361.csv,
POSTS_GLASS_T361.csv, CENSUS_T361.csv and summary.json next to this file (--write), or compares them (--check).
"""

from __future__ import annotations

import csv
import io
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import t361_rules as R  # noqa: E402

INP = json.loads((HERE / "ALSENAN_FENCE_GATE_INPUT.json").read_text())
RES = HERE.parent

PRINTED = {
    "P12_FENCE_PLAN": "Pages_11-12 p.12 FENCE PLAN 1:100: chain 580 / 250 / 81 / 195 / 115 / 195 / 83 (fence, gate, "
                      "annex face); the 250 gap is crossed by a dashed line only, no leaf or swing",
    "P12_FENCE_ELEV": "Pages_11-12 p.12 FENCE ELEVATION 1:100: low wavy wall with an X railing in its dip and a rounded "
                      "end pier; the 250 gap shows a ground strip only (no leaf, no post, no frame)",
    "P12_SECTION": "Pages_11-12 p.12 SECTION: 265 = 50 + 215",
    "S03_PLOT": "sheet03 GF plan: STREET 15.00, SEA VIEW 15.00, NEIGHBOUR 31.37 (both sides)",
}


def _rows(path):
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def railings():
    return _rows(RES / "agents_t164" / "RAILINGS_T164.csv")


def parapets():
    out = {}
    for r in _rows(RES / "agents_t162" / "PARAPETS_T162.csv"):
        if r.get("CHAIN") in ("ANNEX", "GF", "1F", "2F") and r.get("INNER_TOP_ARRIS_ML"):
            out[r["CHAIN"]] = (float(r["OUTER_TOP_ARRIS_ML"]), float(r["INNER_TOP_ARRIS_ML"]), r["LEVELS"])
    return out


def build():
    s, sea, se, nw = INP["street"], INP["sea"], INP["se_elevation_sea_gate"], INP["nw_elevation_sea_gate_zone"]

    # ---------------- boundary lines (R-T361-2) ----------------
    street = R.boundary_line("F-STREET", s["fence_line_outer_10F"], [s["solid"]], [s["gap_110_hidden"]])
    north = R.boundary_line("F-NORTH", INP["upper_neighbour"]["outer_99_98"], [INP["upper_neighbour"]["outer_99_98"]],
                            [])
    lower = R.boundary_line("F-LOWER-1.20", INP["lower_neighbour_short"]["outer_86"],
                            [INP["lower_neighbour_short"]["outer_86"]], [])
    # sea element: column face -> plot corner = 0.232 (column face to the wall end at 39F) + 8D + 8E zone
    sea_lead = round(sea["element_column_face_to_corner"] - sea["solid_8D"] - sea["zone_8E"], 4)
    sea_line = R.boundary_line("F-SEA", sea["element_column_face_to_corner"],
                               [sea_lead, sea["solid_8D"], sea["zone_8E"] - sea["gate_block_width"]],
                               [sea["gate_block_width"]])
    boundary = [
        dict(street, infill="X railing in the dip of the solid wall (p.12 FENCE ELEVATION); length NOT PRINTED -> HELD "
                            "(= T-164 RL-10)", status="DRAWING-CONFIRMED (lengths); infill HELD",
             source="DXF 10F (layer 5) 8.300 = HIDDEN gap 110 2.500 + solid to cap 10B; " + PRINTED["P12_FENCE_PLAN"],
             note="Q-65 C recorded 5.70 + 2.50 'subject to verification': the drawing gives 5.80 solid (+0.10 m)"),
        dict(north, infill="none drawn", status="DRAWING-CONFIRMED (blockwork lane, Q-65 C material HELD)",
             source=f"DXF 99 + 98 (layer 5) outer {INP['upper_neighbour']['outer_99_98']}; inner 13A leg "
                    f"{INP['upper_neighbour']['inner_13A_leg']}; sheet03 'NEIGHBOUR 31.37'",
             note="no gate, no opening, no infill on the whole side; a solid wall item, not a B13-04 infill item"),
        dict(lower, infill="none drawn", status="DRAWING-CONFIRMED (blockwork lane, T-253 band 810#1)",
             source="DXF 86 / 106 (layer 5) 1.200 between the annex and the main house", note=""),
        dict(sea_line, infill="NOT DRAWN (material, height, structure, finishes, railing / glazing: owner Q-63 C HELD)",
             status="HELD (Q-63 C visible element); geometry DRAWING-CONFIRMED",
             source=f"DXF column face 2F96 -> plot corner {sea['element_column_face_to_corner']} = {sea_lead} + wall 8D "
                    f"{sea['solid_8D']} + zone 8E {sea['zone_8E']} (gate D120 {sea['gate_block_width']} + "
                    f"{round(sea['zone_8E'] - sea['gate_block_width'], 4)} jamb / pier)",
             note="7.10 outer-line from the column face to the plot corner = Q-63's 7.00 on the centreline to the north "
                  "fence centreline (+0.10 = half its 0.20 width): reconciled, 0.000 residual"),
    ]

    # ---------------- gates (R-T361-1 / -2) ----------------
    if s["leaf_symbols_in_gap"]:
        raise SystemExit("a leaf symbol appeared in the street gap: re-read the drawing")
    g1 = R.gate_record("G-01", s["gap_110_hidden"], {"PLAN_GAP", "ELEVATION_GAP"})
    g2 = R.gate_record("G-02", sea["gate_block_width"], {"PLAN_LEAF", "ELEVATION_LEAF"}, leaf_count=1,
                       leaf_size_m=(se["leaf_w_23F1_23F2"], se["leaf_h"]))
    pcs, held_ids = R.gate_count([g1, g2])
    gates = [
        dict(g1, where="street fence, between the annex corner and the solid fence end", sheets=(
            "DXF GF plan: gap = HIDDEN polyline 110 (layer 2) 2.500 from the annex corner to cap 10B; no door block or "
            "layer-D symbol overlaps the gap (the D120 door 15E at its end is the annex door in the annex wall); "
            + PRINTED["P12_FENCE_PLAN"] + "; " + PRINTED["P12_FENCE_ELEV"]),
             held_text="leaf count / type (sliding or swing), height, material, frame, hardware, track; never 0, "
                       "never an assumed leaf", census="not in the opening census (T-150 / T-249 list no street gate)"),
        dict(g2, where="sea-side boundary, 0.30 m from the upper-neighbour corner (end of the side passage)", sheets=(
            f"DXF GF plan: D120 block 2D8 ({sea['gate_block_width']} jamb to jamb, leaf swing r "
            f"{sea['gate_leaf_swing_radius']}, single leaf, mirrored, opening into the court strip); SE elevation (DXF, "
            f"seen through the side passage): leaf 23F1 / 23F2 {se['leaf_w_23F1_23F2']} x {se['leaf_h']} with knob 23F6, "
            f"frame 23F4 / 23F3 {se['frame_w_23F4_23F3']}, head line 23F8 {se['head_23F8_above_court_23E5']} above the "
            f"court line 23E5, wall line {se['frame_line_h_23F4']}; NW elevation (DXF): panel 27FA {nw['panel_27FA']} x "
            f"{nw['panel_h_above_27F1']} between pier 2880 / 2881 ({nw['pier_2880_2881']}) and the north fence end "
            f"27EA / 27EB ({nw['end_27EA_27EB']}); no dimension printed on any of them"),
             held_text="material, structure, hardware (owner Q-63 C: the sea-side element's gate is an unknown); the "
                       "drawn leaf 0.90 x 2.10 / opening 1.00 x 2.20 are DXF geometry, NOT printed",
             census="= D-GF-15 (T-150 / T-249, class GATE, SITE.GATE_HELD, 'no sheet prints it'): the SAME gate, "
                    "counted once; this run adds the two elevations that DRAW it"),
    ]

    # ---------------- open edges (R-T361-3) ----------------
    rl = {}
    for r in railings():
        rl.setdefault(r["RUN"], []).append(r)

    def rl_len(run):
        v = [float(x["LENGTH_LM"]) for x in rl.get(run, []) if x["LENGTH_LM"]]
        return round(sum(v), 3) if v else None

    pp = parapets()
    st = INP["st03"]
    edges = [
        R.open_edge("E-01 annex roof +4.30", pp["ANNEX"][1], "DRAWN",
                    f"parapet ANNEX {pp['ANNEX'][2]} inner run {pp['ANNEX'][1]} (T-162) + railing RL-03 "
                    f"{rl_len('RL-03')} lm on its low parts (T-164)"),
        R.open_edge("E-02 GF roof +5.50", pp["GF"][1], "DRAWN",
                    f"parapet GF {pp['GF'][2]} inner run {pp['GF'][1]} (T-162); the sea strip before W15 / W16 carries "
                    f"RL-04 {rl_len('RL-04')} HELD (plan band vs NW elevation piers, T-164) and the passage-mouth "
                    f"stop-end HELD 0 .. 1.20 (T-162)"),
        R.open_edge("E-03 1F roof +9.70", pp["1F"][1], "DRAWN",
                    f"parapet 1F inner run {pp['1F'][1]} (T-162) + RL-01 {rl_len('RL-01')} + RL-02 {rl_len('RL-02')} lm"),
        R.open_edge("E-04 2F roof +13.90", pp["2F"][1], "DRAWN", f"parapet 2F closed ring inner run {pp['2F'][1]}"),
        R.open_edge("E-05 ST-02 inner side + 1F void gallery", rl_len("RL-05"), "DRAWN",
                    f"RL-05 {rl_len('RL-05')} lm installed (T-164)"),
        R.open_edge("E-06 1F living floor edge beside RS-A", rl_len("RL-06"), "DRAWN", "RL-06 (T-164, D-23)"),
        R.open_edge("E-07 ST-02 outer side", None, "UNKNOWN",
                    None) | {"note": "RL-09 outer 50 mm band: guard or string not established; plan 4.035 .. 4.455 m"},
        R.open_edge("E-08 ST-01 inner (well) side, 4 flights + turns + 2F edge", rl_len("RL-07"), "DRAWN",
                    f"RL-07 {rl_len('RL-07')} measured, MS1-T / MS1-LD turns HELD (T-164)"),
        R.open_edge("E-09 ST-01b lobby flight D1, drawn side", rl_len("RL-08"), "DRAWN", "RL-08 section A-A (T-164)"),
        R.open_edge("E-10 ST-01b lobby flight D1, second side", None, "UNKNOWN", None)
        | {"note": "section A-A draws one rail; whether the second side is open or walled is not established here"},
        R.open_edge("E-11 ST-03 entrance stair, north (court) side", st["open_side_368"], "NONE_DRAWN",
                    drop_m=(0.0, 0.85)) | {"note": "layer-5 edge 368 (flight side, +0.15 -> +1.00) with nothing drawn "
                                                   "beside it; render T-161 F04 shows a balustrade: a render never "
                                                   "makes it (R-T361-4)"},
        R.open_edge("E-12 ST-03 top strip at +1.00 (north end)", st["top_strip_367"], "NONE_DRAWN",
                    drop_m=(0.85, 0.85)) | {"note": "layer-5 edge 367 between the flight and the porch wall"},
        R.open_edge("E-13 ST-03 south side", st["open_side_368"], "WALL",
                    f"wall 15A / 158 ({st['wall_side_15A_158_thickness']} m, layer 1) runs the full flight + column "
                    f"2FAE"),
    ]
    for e in edges:
        e.setdefault("note", "")

    # ---------------- posts / glass (R-T361-5) ----------------
    P = INP["posts"]
    nw_posts = R.posts_from_lines([x * 1000 for x, _ in P["nw_vertical_lines"]])
    se_posts = R.posts_from_lines([x * 1000 for x, _ in P["se_vertical_lines"]])
    glass = R.glass_panels([])
    hatch = INP["hatch_patterns"]
    posts = [
        {"id": "PG-01", "item": "posts, RL-02 1F roof sea (NW) railing", "pcs": len(nw_posts),
         "positions_m": [round(p / 1000, 3) for p in nw_posts], "rail_m": P["nw_top_rail_279F"],
         "status": "DRAWN (component count; no separate line without a specification)",
         "source": "NW elevation DXF: vertical line pairs under top rail 279F (single 251F excluded)"},
        {"id": "PG-02", "item": "posts, RL-01 1F roof street (SE) face", "pcs": len(se_posts),
         "positions_m": [round(p / 1000, 3) for p in se_posts], "rail_m": P["se_top_rail_223C"],
         "status": "DRAWN (component count; the 2.470 SW return is not in this elevation: its posts NOT COUNTED here)",
         "source": "SE elevation DXF: vertical line pairs under top rail 223C"},
        {"id": "PG-03", "item": "posts, RL-03 annex roof railing / street fence X railing", "pcs": None,
         "positions_m": [], "rail_m": None, "status": "NOT COUNTED (raster sheet p.12 / p.7 / p.9 only; a count from a "
         "raster is left to the Checker's own reading)", "source": "Pages_11-12 p.12 FENCE ELEVATION"},
        {"id": "PG-04", "item": "stair balusters / posts (ST-01, ST-01b, ST-02)", "pcs": None, "positions_m": [],
         "rail_m": None, "status": "NOT DRAWN on the plans (continuous 50 mm band only); section A-A rails per T-164",
         "source": "GF / 1F / 2F plan bands (T-164)"},
        {"id": "PG-05", "item": "glass panels (balustrade / guard / fence)", "pcs": None, "positions_m": [],
         "rail_m": None, "status": glass["status"] + " (m2 None, never 0 by default)",
         "source": f"DXF hatch patterns {hatch} (no glass pattern); the DXF holds 24 distinct texts, none names glass; "
                   f"no schedule / specification issued (RFI-B-A12)"},
    ]

    # ---------------- per-sheet census (a) ----------------
    census = [
        ("DXF GF plan (P7757.dxf)", "read this run", "street gap 110 (HIDDEN) 2.500 + cap 10B; sea gate D120 2D8; "
         "north fence 99 / 98 / 13A; lower 1.20 86 / 106; ST-03 edges 368 / 367, wall 15A / 158; no fence infill "
         "symbol on any side"),
        ("DXF SE elevation", "read this run", "sea gate leaf 23F1 / 23F2 + knob 23F6, frame 23F4 / 23F3, head 23F8; "
         "RL-01 street-face posts under 223C"),
        ("DXF NW elevation", "read this run", "sea gate zone 27FA + pier 2880 / 2881 + north fence end 27EA / 27EB; "
         "RL-02 posts under 279F; the 5.17 m solid sea wall 8D is not drawn in front of the pool drum"),
        ("Pages_11-12 p.12 FENCE PLAN / ELEVATION / SECTION", "read this run (200 dpi, by eye)",
         PRINTED["P12_FENCE_PLAN"] + "; " + PRINTED["P12_FENCE_ELEV"] + "; " + PRINTED["P12_SECTION"]),
        ("p7757_arch_sheet03 (GF plan)", "read this run (50 dpi overview)", PRINTED["S03_PLOT"]),
        ("1F / 2F plans, SW p.7, NE p.9, section A-A", "cited, not re-read (merged T-164 / T-162)",
         "railing bands RL-01 .. RL-09, parapet chains"),
        ("ST7757 p.14 TYPICAL BOUNDARY WALL", "cited (merged T-253 / Q-65 text)", "brick wall on 20 x 40 ground beams, "
         "20 x 30 columns; no gate, no infill, no railing detail"),
        ("Renders (T-161)", "never a source of quantity", "porch balustrade, pool-court railing, street fence "
         "railing: R-T361-4"),
    ]

    # ---------------- freelancer (d) ----------------
    freelancer = [
        {"his_row": "blockwork workbook, 'fence' 1 x 37.20 x 2.00 = 74.40 m2", "ours": "north 31.37 + street solid "
         "5.80 = 37.17 (+ lower 1.20 + sea 7.10 HELD)", "verdict": "AGREE on the scope he counts (37.20 vs 37.17, "
         "+0.03 m); he has no gate, no infill and no sea element: RULE_DIFFERENCE (scope)"},
        {"his_row": "aluminium workbook GF 'external door' 4 x 1.00 x 2.40 = 9.60 m2", "ours": "sea gate G-02 1.00 "
         "(drawn leaf 0.90 x 2.10, head 2.20)", "verdict": "UNRESOLVED: whether one of his four 1.00 doors is the sea "
         "gate is not shown by his sheet (no location column); his 2.40 is not the drawn 2.20 head"},
        {"his_row": "none", "ours": "street gate opening G-01 2.50, leaf HELD", "verdict": "HAND_FOUND (no row); "
         "neither side has a leaf quantity"},
        {"his_row": "none", "ours": "glass panels NOT DRAWN", "verdict": "AGREE (nothing to count)"},
    ]
    return {"boundary": boundary, "gates": gates, "gate_pcs": pcs, "gate_openings_held": held_ids, "edges": edges,
            "posts": posts, "census": census, "freelancer": freelancer}


def _csv(rows, cols):
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(cols)
    for r in rows:
        w.writerow([json.dumps(r.get(c)) if isinstance(r.get(c), (list, tuple, dict)) else r.get(c) for c in cols])
    return buf.getvalue()


def outputs(b):
    none_drawn = [e for e in b["edges"] if e["guard"] == "NONE_DRAWN"]
    summary = {
        "task": "T-361", "project": "development villa (Alsenan); not an accuracy claim",
        "gates_pcs_drawing_confirmed": b["gate_pcs"], "gate_openings_leaf_held": b["gate_openings_held"],
        "gate_opening_widths_m": {g["id"]: g["opening_width_m"] for g in b["gates"]},
        "boundary_lines_m": {r["id"]: {"drawn": r["drawn_m"], "solid": r["solid_m"], "gates": r["gates_m"]}
                             for r in b["boundary"]},
        "open_edges": len(b["edges"]), "open_edges_none_drawn": [e["id"] for e in none_drawn],
        "open_edges_none_drawn_plan_m": round(sum(e["plan_length_m"] for e in none_drawn), 3),
        "open_edges_unknown": [e["id"] for e in b["edges"] if e["guard"] == "UNKNOWN"],
        "posts_drawn": {p["id"]: p["pcs"] for p in b["posts"] if p["id"] in ("PG-01", "PG-02")},
        "glass_panels": "NOT_DRAWN", "fence_infill_lm": None, "fence_infill_status": "HELD (length not printed)",
        "cross_check_shared_ids": R.cross_check_zero(
            [g["id"] for g in b["gates"]] + ["F-STREET-INFILL"],
            ["RL-01", "RL-02", "RL-03", "RL-04", "RL-05", "RL-06", "RL-07", "RL-08", "RL-09", "RL-10", "FIN.HANDRAIL",
             "F-STREET-SOLID", "F-NORTH-SOLID"])["count"],
        "freelancer": b["freelancer"],
    }
    return {
        "GATES_T361.csv": _csv(b["gates"], ["id", "kind", "gates_pcs", "leaves_pcs", "opening_width_m", "leaf_size_m",
                                            "status", "where", "sheets", "held_text", "census"]),
        "BOUNDARY_T361.csv": _csv(b["boundary"], ["id", "drawn_m", "solid_m", "gates_m", "infill", "status", "source",
                                                  "note"]),
        "OPEN_EDGES_T361.csv": _csv(b["edges"], ["id", "plan_length_m", "guard", "guard_ref", "drop_m", "note"]),
        "POSTS_GLASS_T361.csv": _csv(b["posts"], ["id", "item", "pcs", "positions_m", "rail_m", "status", "source"]),
        "CENSUS_T361.csv": _csv([dict(zip(("sheet", "read", "found"), c)) for c in b["census"]],
                                ["sheet", "read", "found"]),
        "summary.json": json.dumps(summary, indent=1, ensure_ascii=True) + "\n",
    }


def main(argv):
    out = outputs(build())
    if "--write" in argv:
        for name, text in out.items():
            (HERE / name).write_text(text)
        print("wrote", ", ".join(out))
        return 0
    bad = [n for n, t in out.items() if not (HERE / n).exists() or (HERE / n).read_text() != t]
    print("committed outputs reproduce" if not bad else f"DIFFER: {bad}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
