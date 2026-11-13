"""T-769 (F-10, lane S): fix-row set for the FENCE, GATES and SITE families without a figure on the candidate index.

DELIVERY MODE (owner 2026-11-13): every line gets a figure by the fallback order with its label
MEASURED / DRAWING-READ / DEFAULT / ESTIMATE / SAFETY and a one-line basis. Nothing is wired here (Worker 3, T-770).

Inputs: merged repository records only (values, no drawing, no client data):
  line index   research/agents_t314/out/LINE_INDEX_V3_0_79.json (newest merged index; the fence / site lines are
               identical to V3.0.78)
  fence runs   T-396 (run table, printed 2.65), T-404 (faces, corner convention, court +0.15), T-361 (gates),
               T-403 (below-N.G. section), T-761 (10 boundary pads = 10 columns, SAFETY count), T-764 (boundary
               formation 1.67 below N.G., S01), T-343 (pool water-face bound), T-357 / T-491 (plot 15.00 x 31.37,
               printed GF area), T-358 (groundwater -4.50)
  scaled read  this run: Drive "Alsenan chalet project" / Alsenan_Architectural_P7757_Pages_11-12 p.12 FENCE ELEVATION
               1:100, 400 dpi raster, read only in .work/private: street solid run drawn 5.79 m (= printed 5.80 outer,
               scale check 0.2 %); area between the wall top (corner end) and the drawn top profile (railing dip +
               the lower rounded gate end) = 4.119 m2 (dip 3.800 + gate end 0.319); developed top over the drawn width
               5.747 m = 6.874 m (+1.127 m); gate end top drawn 0.603 m below the corner end. Only these four numbers
               are carried; no image or coordinate is committed.

    python3 -I research/agents_t769/fill_t769.py [--check]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
OUT = HERE / "out"
IDX = ROOT / "research/agents_t314/out/LINE_INDEX_V3_0_79.json"

# printed / merged values (sources in the docstring)
H_FENCE = 2.65            # p.12 SECTION '265' (T-396 R-T396-2)
H_UPPER_SECTION = 2.15    # p.12 SECTION '215': exposed above the higher (outside) ground band '50'
COURT = 0.15              # plot-side court +0.15 (p.11 B-B, T-404)
COL_W = 0.30              # boundary column 20 x 30 (ST p.14), 0.30 along the run
PER_COL = COL_W * H_FENCE  # 0.795 m2 of block per column above N.G. (T-396 R-T396-3)
RUN = {"F-NORTH": 31.37, "F-NORTH-PLOT": 30.97, "F-STREET-OUT": 5.80, "F-STREET-PLOT": 5.60,
       "F-SEA": 2.40, "F-LOWER": 1.20}
COLS = {"F-NORTH": 2, "F-STREET": 2, "F-SEA": 4, "F-LOWER": 2}   # T-761: one column at each end of the 5 band runs
DIP = 4.119               # scaled, p.12 elevation (dip 3.800 + lower rounded gate end 0.319)
TOP_EXTRA = 1.127         # scaled developed top - drawn width
GATE_END_DROP = 0.603     # scaled
BAND = 44.07              # boundary band (T-253 / T-403)
FORMATION = 1.67          # T-764 boundary trench (S01), below N.G.
BLINDING = 0.10
LOWER_GB = 0.60           # owner Q-28 A method (p.10 B.W 20 x 60)
UPPER_GB = 0.40           # ST p.14 '(20x40)'
BLOCKS_PER_M2 = 12.5      # owner Q-75 / Q-80
PLOT_A = 470.55           # T-357 / T-491: 15.00 x 31.37
GF_AREA = 319.99          # ARCH p.1 printed GF area (68.00 %), T-357 s.7
WATER = -4.50             # ST p.9 note 4 (T-358)


def r(x, n=3):
    return round(x + 0.0, n)


def load():
    d = json.loads(IDX.read_text(encoding="utf-8"))
    return {l["line_id"]: l for l in d["lines"]}


def needs(l):
    return l["class"] == "HELD" and l["measured_net"] is None


def before(l):
    return {"class": l["class"], "net": l["measured_net"], "low": l["held_low"], "high": l["held_high"]}


def build():
    L = load()
    by_el = {l["element_id"]: l for l in L.values()}
    rows = []

    def put(el, net, label, basis):
        l = by_el[el]
        assert needs(l), el
        rows.append({"line_id": l["line_id"], "item_code": l["item_code"], "unit": l["unit"], "element_id": el,
                     "before": before(l), "after": {"class": "RELEASED", "net": r(net, 4)}, "label": label,
                     "basis": basis})
        return net

    # ---- physical faces (EXT.FENCE.FACE) ----
    st_out = RUN["F-STREET-OUT"] * H_FENCE - DIP
    st_plot = RUN["F-STREET-PLOT"] * H_FENCE - DIP
    put("FENCE:F-STREET:FACE:OUTSIDE", st_out, "ESTIMATE",
        f"5.80 x 2.65 printed = 15.370 - dip / rounded gate end 4.119 m2 scaled from the p.12 elevation 1:100 = {st_out:.3f}")
    put("FENCE:F-STREET:FACE:PLOT", st_plot, "ESTIMATE",
        f"5.60 x 2.65 printed = 14.840 - the same scaled dip 4.119 m2 = {st_plot:.3f}")
    end = 0.20 * (H_FENCE - GATE_END_DROP)
    put("FENCE:F-STREET:FACE:END-G-01", end, "ESTIMATE",
        f"stop-end at G-01 0.20 x (2.65 - 0.603 scaled drop of the gate end) = {end:.3f} (T-404 at most 0.530)")
    sea = RUN["F-SEA"] * H_FENCE
    low = RUN["F-LOWER"] * H_FENCE
    for side in ("OUTSIDE", "PLOT"):
        put(f"FENCE:F-SEA:FACE:{side}", sea, "ESTIMATE",
            "sea solid 2.40 (T-396 runs, gate G-02 and pool back excluded) x 2.65 drawn in both elevations "
            "(not printed for this run; Q-63 C element, designer RFI-B-A11 replaces it) = 6.360")
        put(f"FENCE:F-LOWER:FACE:{side}", low, "ESTIMATE",
            "passage closure 1.20 (T-396) x 2.65 fence height (no height printed for the closure; same fence) = 3.180")

    # ---- wall planes ----
    put("FENCE:F-SEA:WALL_PLANE", sea, "ESTIMATE", "2.40 x 2.65 (as the sea faces) = 6.360")
    put("FENCE:F-LOWER:WALL_PLANE", low, "ESTIMATE", "1.20 x 2.65 (as the closure faces) = 3.180")

    # ---- block net above N.G. ----
    blk = {}
    blk["F-NORTH"] = RUN["F-NORTH"] * H_FENCE - COLS["F-NORTH"] * PER_COL
    put("FENCE:F-NORTH:BLOCK_NET", blk["F-NORTH"], "ESTIMATE",
        f"plane 31.37 x 2.65 = 83.1305 - 2 columns x 0.30 x 2.65 (T-761 count: one per run end) = {blk['F-NORTH']:.3f}; "
        "block to the full 2.65 (lower 0.50 band material not printed)")
    blk["F-STREET"] = 14.84 - DIP - COLS["F-STREET"] * PER_COL
    put("FENCE:F-STREET:BLOCK_NET", blk["F-STREET"], "ESTIMATE",
        f"plane 14.840 (released) - scaled dip 4.119 - 2 columns 1.590 = {blk['F-STREET']:.3f}")
    blk["F-SEA"] = sea - COLS["F-SEA"] * PER_COL
    put("FENCE:F-SEA:BLOCK_NET", blk["F-SEA"], "ESTIMATE",
        f"plane 6.360 - 4 columns (two sea runs, G-02 jambs) 3.180 = {blk['F-SEA']:.3f}")
    blk["F-LOWER"] = low - COLS["F-LOWER"] * PER_COL
    put("FENCE:F-LOWER:BLOCK_NET", blk["F-LOWER"], "ESTIMATE",
        f"plane 3.180 - 2 columns 1.590 = {blk['F-LOWER']:.3f}")

    # ---- masonry below N.G. ----
    h_below = FORMATION - BLINDING - LOWER_GB - UPPER_GB
    below = BAND * h_below - 10 * COL_W * h_below
    put("FENCE:BAND:MASONRY_BELOW_NG", below, "ESTIMATE",
        f"band 44.07 x h {h_below:.2f} (formation 1.67 S01 as T-764 - blinding 0.10 - lower G.B 0.60 Q-28 A - upper G.B 0.40) "
        f"= {BAND * h_below:.3f} - 10 columns x 0.30 x {h_below:.2f} = {below:.3f} (T-403 at least 17.628 at 1.50)")

    block_total = sum(blk.values()) + below
    put("FENCE:ALL:BLOCKS", round(block_total * BLOCKS_PER_M2), "ESTIMATE",
        f"fence block net above N.G. {sum(blk.values()):.3f} + below N.G. {below:.3f} = {block_total:.3f} m2 x 12.5 "
        "per m2 (owner Q-75 / Q-80), waste separate; type HELD (Q-65 C)")

    # ---- finishable faces: plaster = paint (no tile, no ceiling band on a fence) ----
    fin = {
        ("F-NORTH", "OUTSIDE"): (RUN["F-NORTH"] * H_UPPER_SECTION, "DRAWING-READ",
                                 "31.37 x 2.15 (p.12 SECTION '215' above the outside ground band '50')"),
        ("F-NORTH", "PLOT"): (RUN["F-NORTH-PLOT"] * (H_FENCE - COURT), "DRAWING-READ",
                              "30.97 x 2.50 (2.65 - court +0.15; T-404 finishable lower bound)"),
        ("F-STREET", "OUTSIDE"): (st_out - RUN["F-STREET-OUT"] * (H_FENCE - H_UPPER_SECTION), "ESTIMATE",
                                  "face 11.251 - 5.80 x 0.50 outside ground band (SECTION '50'; elevation draws about 2.0 exposed)"),
        ("F-STREET", "PLOT"): (st_plot - RUN["F-STREET-PLOT"] * COURT, "ESTIMATE",
                               "face 10.721 - 5.60 x 0.15 court"),
        ("F-SEA", "OUTSIDE"): (RUN["F-SEA"] * H_UPPER_SECTION, "ESTIMATE", "2.40 x 2.15 (section as the other runs)"),
        ("F-SEA", "PLOT"): (RUN["F-SEA"] * (H_FENCE - COURT), "ESTIMATE", "2.40 x 2.50 (court +0.15)"),
        ("F-LOWER", "OUTSIDE"): (RUN["F-LOWER"] * H_UPPER_SECTION, "ESTIMATE", "1.20 x 2.15 (section as the other runs)"),
        ("F-LOWER", "PLOT"): (RUN["F-LOWER"] * (H_FENCE - COURT), "ESTIMATE", "1.20 x 2.50 (court +0.15)"),
    }
    sysnote = ("; system as the house exterior (render 1:4 + paint, Q-79; fence finish not printed, owner item open "
               "under Q-65 C)")
    for (run, side), (a, lab, b) in fin.items():
        put(f"FENCE:{run}:FACE:{side}:PLASTER", a, lab, f"exposed face {b} = {a:.3f}{sysnote}")
        put(f"FENCE:{run}:FACE:{side}:PAINT", a, lab, f"= the plaster face {a:.3f} (owner 2026-11-12: paint = plaster face)")

    # ---- top, gates ----
    top = RUN["F-STREET-PLOT"] + TOP_EXTRA
    put("FENCE:F-STREET:TOP", top, "ESTIMATE",
        f"plan 5.60 (corner square in the north top) + 1.127 developed along the scaled dip / rounded end = {top:.3f}")
    put("FENCE:G-01:LEAF", 1, "ESTIMATE",
        "one gate set in the printed 2.50 opening (leaf not drawn: type / leaves by the designer, T-361)")
    put("FENCE:G-02:LEAF", 1, "DRAWING-READ", "1 leaf drawn (D120 single swing; elevation leaf 0.90 x 2.10), T-361")

    # ---- pool water face, outdoor floor points ----
    put("GF-POOL-WATER#FINISH", 8.578838 + 11.069469 * 1.15, "DRAWING-READ",
        "pool floor 8.5788 + inner perimeter 11.0695 x 1.15 (DXF dim 2E5E finished floor -0.85 to rim +0.30) = 21.309 (T-343)")
    for el in ("GF-COURT#POOL-DECK", "GF-COURT#PORCH"):
        l = by_el[el]
        assert l["held_low"] == l["held_high"]
        put(el, l["held_low"], "MEASURED", "range low = high: the drawn polygon (T-157 / T-343)")

    # ---- missing families: new lines (no line id yet; Worker 3 assigns) ----
    clear_dw = WATER + FORMATION
    new = [
        {"family": "B1-01", "item_code": "SITE.CLEARANCE", "unit": "m2", "net": PLOT_A, "label": "DRAWING-READ",
         "basis": "plot 15.00 x 31.37 printed (ARCH p.1 / p.2) = 470.550; owner 2026-11-02 17:20 (6) scope = the plot (T-491)"},
        {"family": "B1-05", "item_code": "SITE.ANTI_TERMITE", "unit": "m2", "net": GF_AREA, "label": "DEFAULT",
         "basis": "building footprint = printed GF area 319.99 m2 (ARCH p.1, 68.00 % of 470.55); no sheet prints a soil "
                  "treatment (T-471): Lead row default, the designer can strike it"},
        {"family": "B1-06", "item_code": "SITE.DEWATERING", "unit": "item", "net": None, "label": "NOT_APPLICABLE",
         "basis": f"groundwater -4.50 printed (ST p.9 note 4) vs deepest formation -1.67: {abs(clear_dw):.2f} m clear; "
                  "conditional only (note 14, T-358 B1-06a). Excavation support B1-06b is TRIGGERED (T-358): left to T-771"},
        {"family": "B1-07", "item_code": "SITE.PRELIMINARIES", "unit": "item", "net": 1, "label": "DEFAULT",
         "basis": "one lump-sum item (owner 17:20 (6): site handover item; hoarding gross 92.74 lm = 2 x (15.00 + 31.37) "
                  "beside, T-491); durations / counts by the contractor's programme"},
    ]
    return L, rows, new, {"block_net_above": sum(blk.values()), "below": below, "fin": fin}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    L, rows, new, x = build()
    fams = ("EXT.FENCE.", "EXT.POOL.", "EXT.FLOOR.OUTDOOR")
    fam_lines = [l for l in L.values() if l["item_code"].startswith(fams)]
    blank_before = sum(1 for l in fam_lines if needs(l))
    filled = {r["line_id"] for r in rows}
    blank_after = sum(1 for l in fam_lines if needs(l) and l["line_id"] not in filled)
    per = {}
    for r_ in rows:
        k = f"{r_['item_code']} [{r_['unit']}]"
        p = per.setdefault(k, {"lines": 0, "after": 0.0})
        p["lines"] += 1
        p["after"] = round(p["after"] + r_["after"]["net"], 4)
    plaster = sum(v[0] for v in x["fin"].values())
    face_released = 83.1305 + 82.0705
    faces_total = face_released + sum(r_["after"]["net"] for r_ in rows if r_["item_code"] == "EXT.FENCE.FACE")
    fl = {
        "fence block above N.G. vs freelancer 'السور' 74.40 m2": [round(x["block_net_above"], 3), 74.40],
        "fence plaster / paint vs freelancer exterior rows 87-90 107.24 m2": [round(plaster, 3), 107.24],
        "pool water face vs freelancer 40.80 m2": [21.309, 40.80],
    }
    out = {"schema": "URBAN_FIX_ROWS_V1", "task": "T-769", "candidate_version": "ARCH_TAKEOFF_V3.0.79",
           "inputs": [str(IDX.relative_to(ROOT))],
           "summary": {"family_lines": len(fam_lines), "lines_without_point_before": blank_before, "rows": len(rows),
                       "lines_without_point_after": blank_after, "new_lines_missing_families": len(new),
                       "per_item": per, "fence_faces_total_m2": round(faces_total, 3),
                       "vs_freelancer": fl},
           "rows": rows, "new_lines": new}
    OUT.mkdir(exist_ok=True)
    js = json.dumps(out, indent=1, ensure_ascii=False) + "\n"
    md = [f"# T-769 fix rows: fence, gates, pool face, outdoor floor and site families (V3.0.79 index)", "",
          f"Lines without a point figure in these families: {blank_before} -> {blank_after}; rows {len(rows)}; "
          f"new lines for missing families {len(new)} (B1-01, B1-05, B1-06 NOT_APPLICABLE, B1-07).", "",
          "| vs freelancer | candidate | freelancer | diff | % |", "|---|---|---|---|---|"]
    for k, (c, f) in fl.items():
        md.append(f"| {k} | {c:.2f} | {f:.2f} | {c - f:+.2f} | {100 * (c - f) / f:+.1f} % |")
    md += ["", "| item | lines | after |", "|---|---|---|"]
    md += [f"| {k} | {v['lines']} | {v['after']} |" for k, v in sorted(per.items())]
    md += ["", "| line | item | unit | element | before | after | label | basis |", "|---|---|---|---|---|---|---|---|"]
    for r_ in rows:
        b = r_["before"]
        bs = "BLANK" if b["low"] is None else f"HELD {b['low']} .. {b['high']}"
        md.append(f"| {r_['line_id']} | {r_['item_code']} | {r_['unit']} | {r_['element_id']} | {bs} | "
                  f"{r_['after']['net']} | {r_['label']} | {r_['basis']} |")
    md += ["", "## New lines (missing families; Worker 3 assigns line ids)", "", "| family | item | unit | figure | label | basis |",
           "|---|---|---|---|---|---|"]
    md += [f"| {n['family']} | {n['item_code']} | {n['unit']} | {n['net']} | {n['label']} | {n['basis']} |" for n in new]
    mds = "\n".join(md) + "\n"
    if a.check:
        ok = (OUT / "FIX_ROWS.json").read_text(encoding="utf-8") == js and (OUT / "FIX_ROWS.md").read_text(encoding="utf-8") == mds
        print("T769 CHECK", "PASS" if ok else "FAIL")
        return 0 if ok else 1
    (OUT / "FIX_ROWS.json").write_text(js, encoding="utf-8")
    (OUT / "FIX_ROWS.md").write_text(mds, encoding="utf-8")
    print(json.dumps(out["summary"], indent=1, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
