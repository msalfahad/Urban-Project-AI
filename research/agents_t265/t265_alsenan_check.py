"""T-265 Alsenan: ground-beam bars by population on the merged T-253 / T-242 run geometry (committed ledgers only;
no private file is read here). Sections as printed on Drive "Alsenan chalet project" / "ST7757.pdf":
  p.14 TYPICAL BOUNDARY WALL section A-A (upper G.B at N.G.): 20 x 40, '2ø14 (T&B)' (leader to the top layer, 2 dots),
       '3ø16 (T&B)' (leader to the bottom layer, 3 dots), 'ø8/20 STIRRUPS'; plain concrete 15 above N.G.
  p.13 'Ground Beams. for exterior walls': 30 wide, depth 'FOLLOW ARCH.' (from 'Ground Floor slab level' to 'Outer
       Normal ground level'), 3ø16 top, '2ø12/30cm' side (2 levels x 2 dots drawn), 6ø16 bottom (two rows of 3 dots),
       'ø8/15cm'.
  p.8 note 21 (side bars 2 / 3 / 4 ø12 in beams deeper than 60 cm 'unless stated otherwise': p.13 states them);
       note 22 (cover >= 2.5 cm beams, >= 7 cm against soil).
Writes LEDGER_T265.csv and summary.json next to this file when run as a script.
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import t265_gb_bars as G  # noqa: E402

T253 = HERE.parent / "agents_t253" / "LEDGER_T253.csv"
STOCK_M = 12.0          # stock length used by the merged T-149 (procurement splices only, HELD, never net)
OWN_MEASURED = {"7D0+FC#1", "7D0+FC#2", "7D0+FC#3", "7D0+FC#4", "7E0+FD#1", "7E0+FD#2"}   # Checker T-253 verdict

TB = G.tb_reading([(2, 14, "TOP"), (3, 16, "BOTTOM")], {"TOP": 2, "BOTTOM": 3}, 0.20, 0.025, 8)

SECTIONS = {
    "P14_BOUNDARY_GB": {
        "section_id": "P14_BOUNDARY_GB", "source": "ST7757.pdf p.14 TYPICAL BOUNDARY WALL section A-A",
        "applies_to": ["BOUNDARY_GB"], "b_m": 0.20, "depth_m": 0.40,
        "top": TB["top"], "bottom_rows": [TB["bottom"]], "stirrup": (8, 0.20), "side": None},
    "P13_GB_EXTERIOR": {
        "section_id": "P13_GB_EXTERIOR", "source": "ST7757.pdf p.13 Ground Beams for exterior walls",
        "applies_to": ["GB_EXTERIOR"], "b_m": 0.30, "depth_m": None,
        "top": [(3, 16)], "bottom_rows": [[(3, 16)], [(3, 16)]], "stirrup": (8, 0.15),
        "side": {"bars_per_level": 2, "dia_mm": 12, "pitch_m": 0.30}},
}


def members():
    out = []
    for r in csv.DictReader(T253.open(encoding="utf-8")):
        comp, item = r["component"], r["item"]
        L = float(r["L_m"]) if r["L_m"] else None
        if comp.startswith("BOUNDARY-GB at"):
            out.append({"member_id": item, "family": "BOUNDARY_GB", "L_m": L, "depth_m": 0.40, "state": G.APPLIES,
                        "column_zones": "UNKNOWN_COUNT", "section": "P14_BOUNDARY_GB",
                        "provenance": "T-253 band run, Checker-measured face to face (dff9cb79)"})
        elif comp.startswith("GB-EXTERIOR MAIN"):
            out.append({"member_id": item, "family": "GB_EXTERIOR", "L_m": L, "depth_m": float(r["d_m"]),
                        "state": G.APPLIES, "column_zones": "NONE", "section": "P13_GB_EXTERIOR",
                        "provenance": ("Checker own-measured (T-253 verdict)" if item in OWN_MEASURED
                                       else "T-242 geometry, Checker-verified 01:21 (cited)")})
        elif comp.startswith("GB-EXTERIOR ANNEX"):
            out.append({"member_id": item, "family": "GB_EXTERIOR", "L_m": L, "depth_m": None,
                        "state": G.CONFLICT, "section": "P13_GB_EXTERIOR",
                        "provenance": "annex depth CONFLICT (T-253 s.3): literal 0.25 m cannot hold the p.13 section"})
        elif comp.startswith("GB-COURT"):
            out.append({"member_id": item, "family": "GB_COURT", "L_m": L, "depth_m": None,
                        "state": G.NONE_PRINTED, "section": None,
                        "provenance": "court run: no printed section (T-253 s.4)"})
    out.append({"member_id": "P14 plain concrete 15 above N.G.", "family": "PAVING", "L_m": None, "depth_m": None,
                "state": G.PLAIN, "section": None,
                "provenance": "ST7757.pdf p.14 A-A 'PLAIN CONC.' 15: court paving on N.G. (T-253 s.2 reading 5)"})
    return out


def main(write=True):
    rows = []
    for m in members():
        rows += G.population(m, SECTIONS.get(m["section"]), stock_m=STOCK_M)
    by_fam = {}
    for r in rows:
        f = by_fam.setdefault(r["family"], {"released_lower_bound_kg": None, "by_component_kg": {}, "held": 0})
        if r["kg"] is not None:                  # None = nothing released (never 0 by default)
            f["released_lower_bound_kg"] = round((f["released_lower_bound_kg"] or 0.0) + r["kg"], 3)
            f["by_component_kg"][r["component"]] = round(f["by_component_kg"].get(r["component"], 0) + r["kg"], 3)
        if r["status"] == G.HELD:
            f["held"] += 1
    ms = members()
    annex_len = round(sum(m["L_m"] for m in ms if m["state"] == G.CONFLICT), 4)
    main_len = round(sum(m["L_m"] for m in ms if m["family"] == "GB_EXTERIOR" and m["state"] == G.APPLIES), 4)
    band_len = round(sum(m["L_m"] for m in ms if m["family"] == "BOUNDARY_GB"), 4)
    summ = {
        "policy": G.POLICY_ID, "inputs": ["research/agents_t253/LEDGER_T253.csv"],
        "tb_reading": {"reading": TB["reading"], "top": TB["top"], "bottom": TB["bottom"],
                       "rejected": TB["rejected"]},
        "lengths_m": {"boundary_band": band_len, "main_exterior": main_len, "annex_conflict": annex_len},
        "families": by_fam,
        "annex_reading_if_p13_applied_kg": {
            "top_bottom_depth_invariant": round(annex_len * 9 * G.kg_per_m(16), 3),
            "status": "HELD (CONFLICT: not a quantity)"},
        "boundary_bottom_fits": {"cover_0.025": G.layer_fits(TB["bottom"], 0.20, 0.025, 8),
                                 "cover_0.07_soil": G.layer_fits(TB["bottom"], 0.20, 0.07, 8),
                                 "note": "3 d16 cannot stand in 0.20 m at the note-22 soil cover 7 cm: designer item; "
                                         "the printed count is kept (counts and lengths do not depend on cover)"},
        "literal_tb_both_layers_kg_rejected": round(band_len * 2 * (2 * G.kg_per_m(14) + 3 * G.kg_per_m(16)), 3),
    }
    if write:
        with (HERE / "LEDGER_T265.csv").open("w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
        (HERE / "summary.json").write_text(json.dumps(summ, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    return rows, summ


if __name__ == "__main__":
    R, S = main()
    print(json.dumps(S, indent=1))
