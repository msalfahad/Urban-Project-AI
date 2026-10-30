"""T-380 Alsenan census: what the drawings print for drainage / water supply (B12-02), read in this run (worker 2,
2026-10-30). Runs without any private file.

SAN = Drive 'Alsenan chalet project' / sanitary-7757.pdf: p1 GROUND, p2 FIRST, p3 2nd FLOOR DRAINAGE PLAN, 'SCALE 1/100',
  title-block NOTE 'THE BUILDER TO WORK WITH STATED DIMENSIONS NOT TO SCALE DRAWING' (all three pages). Vector only, no
  text layer. Refs 'p<page>@x,y' are PDF points of the page as displayed (rotation 270 applied); the drop / clean-out
  positions are the centres of the drawn circles extracted from the vector paths (identical frame on all three pages),
  labels were read visually at 200 / 300 dpi. Colours: magenta = soil runs and drop symbols, red = waste branches and
  GCO, blue = fixtures and CO, yellow = FD / RWD / RWP, green = text.
ARCH = Drive 'Alsenan chalet project' / P7757_DXF_COMPRESSED.zip (P7757.dxf, sha256 ab54dd55..): layers 0-6, ARNOTE, CC, D,
  DEFPOINTS, LEVEL, S-COL.BON, ST, TE, TEXT, TOI (empty), W, stamp; no pipe, tank, pump, heater or drainage text or
  block in modelspace or any of the 442 block definitions (only 'mecvent' = mechanical ventilation, T-370).
FREELANCER = Drive 'Alsenan chalet project' / 'Alsenan Chalet_by_category.xlsx' (a cost record) and
  'الارضيات+العازل+الديكور+الرخام (1).xlsx' (the measured finishes workbook), read through the Drive connector.
"""

from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import t380_drainage_rules as R  # noqa: E402

I = R.Item
NOT_TO_SCALE = True   # the printed title-block note, p1 / p2 / p3

# ---- COUNTABLE items (printed symbol / tag / label) ------------------------------------------------------------
COUNT_ITEMS = [
    I("MH-1", "MANHOLE", "GF", "p1@141.6,243.6", R.PRINTED_LABEL, note=(
        "label 'MH 100X100X100 DEEP INSPECTION CHAMBER WITH HATCH BOX AND VENT PIPE' (unit of 100 not printed; "
        "hatched square in the NW court corner, outfall arrow to the street); hatch box and vent pipe are parts of "
        "this item as printed, not separate symbols")),
    I("GCO-1", "GROUND_CLEAN_OUT", "GF", "p1@317.5,455.4", R.LEGEND_TAG, note="'GCO', head of the south branch"),
    I("GCO-2", "GROUND_CLEAN_OUT", "GF", "p1@825.4,244.6", R.LEGEND_TAG, note="'GCO', east head of the court main"),
    I("CO-1", "CLEAN_OUT", "GF", "p1@415.7,578.1", R.LEGEND_TAG, diameter="4in", note="'CO ø4\"' by the pantry"),
    # soil stacks: one physical stack per position (chained below); diameter as printed on the stack tags
    I("SS-A", "SOIL_STACK", "2F-1F-GF", "p3/p2/p1@591.3,263.8", R.LEGEND_TAG, diameter="4in",
      tags=("T/B", "F/A-T/B", "F/A"), note="2F 'SSø4\"T/B' (2F W.C 12B6) / 1F 'SSø4\"F\\A-T/B' (laundry) / GF 'SSø4\"F\\A'"),
    I("SS-B", "SOIL_STACK", "1F-GF", "p2/p1@644.7,263.9", R.LEGEND_TAG, diameter="4in",
      tags=("T/B", "UNLABELLED"), note="1F 'SSø4\"T/B' (W.C C19); GF drop circle drawn with NO tag"),
    I("SS-C", "SOIL_STACK", "1F-GF", "p2/p1@812.5,263.9", R.LEGEND_TAG, diameter="4in",
      tags=("T/B", "F/A"), note="1F 'SSø4\"T/B' (NE, end of the B.T.T.S. run); GF 'SSø4\"F\\A' by the master bedroom"),
    I("SS-D", "SOIL_STACK", "1F-GF", "p2/p1@455.7,572.7", R.LEGEND_TAG, diameter="4in",
      tags=("T/B", "F/A H/L"), note="1F 'SSø4\"T/B' (west twin baths); GF 'SSø4\"F\\A H/L' by the pantry, to CO-1"),
    # rain-water pipes: one per roof outlet (RWD); free discharge = 'FREE DISCHARGE 15CM ABOVE FFL'
    I("RWP-NE", "RAIN_WATER_PIPE", "2F-1F-GF", "p3/p2/p1@867.9,263.9", R.LEGEND_TAG, diameter="4in",
      tags=("T/B", "F/A-T/B", "F/A"), note="2F roof RWD 'RWPø4T/B' -> 1F 'RWPø4F/A-T/B' -> GF free discharge"),
    I("RWP-SE2", "RAIN_WATER_PIPE", "2F-1F", "p3/p2@897.5,564.6", R.LEGEND_TAG, diameter="4in",
      tags=("T/B", "F/A"), note="2F roof RWD 'RWPø4T/B' -> free discharge onto the 1F sea-side terrace +5.50"),
    I("RWP-SW2", "RAIN_WATER_PIPE", "2F-1F", "p3/p2@409.7,572.8", R.LEGEND_TAG, diameter="4in",
      tags=("T/B", "F/A"), note="2F roof RWD 'RWPø4T/B' -> free discharge onto the 1F strip +5.50"),
    I("RWP-TER", "RAIN_WATER_PIPE", "1F-GF", "p2/p1@937.4,597.5", R.LEGEND_TAG, diameter="4in",
      tags=("UNTAGGED TOP", "F/A"), note="1F terrace RWD with a drop circle and NO tag; GF 'RWPø4F/A FREE DISCHARGE'"),
    I("RWP-ANX", "RAIN_WATER_PIPE", "1F-GF", "p2/p1@120.5,606.1", R.LEGEND_TAG, diameter="4in",
      tags=("T/B", "F/A"), note="1F annex roof +4.30 RWD 'RWPø4T/B' -> GF west 'RWPø4F/A FREE DISCHARGE'"),
]

# ---- legend entries drawn nowhere, and items searched for and not printed ------------------------------------
NOT_PRINTED_ITEMS = [
    I("RE", "RODDING_EYE", "all", "p1-p3 legend 'R.E RODDING EYE'", R.LEGEND_ONLY, note="symbol on no plan"),
    I("NRV", "NON_RETURN_VALVE", "all", "p1-p3 legend 'NRV'", R.LEGEND_ONLY, note="symbol on no plan"),
    I("AD", "AREA_DRAIN", "all", "p1-p3 legend 'AD AREA DRAIN'", R.LEGEND_ONLY,
      note="no area drain in the courts, the garden or the pool deck"),
    I("SUMP", "SUMP_PUMP", "all", "p1-p3 legend 'SUMP PUMP'", R.LEGEND_ONLY, note="symbol on no plan"),
    I("TANK", "WATER_TANK", "roof", "searched: p1-p3; P7757.dxf texts and blocks; ST p.6 / arch sections per merged "
      "T-221 s.5", R.ABSENT, note="the structural plan prints a 'WATER TANK PLACE' slab panel (T-221 s.5): a place, "
      "not a tank; no tank, count or capacity is printed and the architect draws none"),
    I("HEATER", "WATER_HEATER", "all", "searched: p1-p3; P7757.dxf texts and blocks", R.ABSENT),
    I("SUPPLY-PT", "SUPPLY_POINT", "all", "searched: p1-p3 (drainage plans only); P7757.dxf", R.ABSENT,
      note="no cold / hot water point, no kitchen sink or washer point (T-370 UNKNOWN)"),
]

# ---- runs: drawn routes, sizes and slopes as printed; lengths never stated --------------------------------------
RUNS = [
    I("RUN-MAIN", "DRAIN_MAIN", "GF", "p1 court, along the north boundary to MH-1, branches to GCO-1 / GCO-2",
      R.ROUTE_DRAWN, diameter="6in", slope="1%", note="'Pø6\"' + 'SLOPE 1%' (3 labels); no dimension, no invert level"),
    I("RUN-GF-SOIL", "SOIL_BRANCH", "GF", "p1 magenta runs, main -> each WC / FD / stack foot", R.ROUTE_DRAWN,
      note="diameter not printed on any branch"),
    I("RUN-WASTE", "WASTE_BRANCH", "GF-1F-2F", "p1-p3 red runs, basin / tray / walk-in -> FD", R.ROUTE_DRAWN,
      note="diameter not printed"),
    I("RUN-1F-BTTS", "SUSPENDED_DRAIN", "1F", "p2, SE bath -> SS-C", R.ROUTE_DRAWN, diameter="4in", slope="1%",
      tags=("B.T.T.S.",), note="'Pø4\" SLOPE 1% B.T.T.S.' (below the slab)"),
    I("RUN-1F-SOIL", "SOIL_BRANCH", "1F-2F", "p2 / p3 magenta runs, WC / FD -> stack", R.ROUTE_DRAWN,
      note="diameter not printed"),
    I("RUN-STACKS", "STACK_VERTICAL", "all", "SS-A..SS-D", R.ROUTE_DRAWN, diameter="4in",
      note="storey levels printed (GF +0.15 / +0.30 / +1.00, 1F +5.50, 2F +9.70) but not the stack ends "
           "(foot connection under the GF slab, H/L at SS-D, top / vent): no length"),
    I("RUN-RWP", "RWP_VERTICAL", "all", "RWP-NE..RWP-ANX", R.ROUTE_DRAWN, diameter="4in",
      note="bottom end printed ('15CM ABOVE FFL'); top end = the RWD on a roof laid to falls 'SLOPE 1%' whose outlet "
           "level is not printed: no length (level differences below are indicators only)"),
    I("RUN-SUPPLY", "WATER_SUPPLY", "all", "searched: p1-p3; P7757.dxf", R.ABSENT,
      note="no water-supply layout on any sheet of the set read"),
]

# Drop symbols for the stack chain (floor index: GF 0, 1F 1, 2F 2), one page frame.
DROPS = [
    ("SS-A/2F", 2, 591.3, 263.8, ("T/B",)), ("SS-A/1F", 1, 591.3, 263.8, ("F/A", "T/B")),
    ("SS-A/GF", 0, 591.3, 263.8, ("F/A",)),
    ("SS-B/1F", 1, 644.7, 263.9, ("T/B",)), ("SS-B/GF", 0, 644.7, 263.9, (R.UNLABELLED,)),
    ("SS-C/1F", 1, 812.5, 263.9, ("T/B",)), ("SS-C/GF", 0, 812.5, 263.9, ("F/A",)),
    ("SS-D/1F", 1, 455.7, 572.7, ("T/B",)), ("SS-D/GF", 0, 455.7, 572.7, ("F/A", "H/L")),
    ("RWP-NE/2F", 2, 867.9, 263.9, ("T/B",)), ("RWP-NE/1F", 1, 867.9, 263.9, ("F/A", "T/B")),
    ("RWP-NE/GF", 0, 867.9, 263.9, ("F/A", "FREE")),
    ("RWP-SE2/2F", 2, 897.5, 564.6, ("T/B",)), ("RWP-SE2/1F", 1, 897.5, 564.6, ("F/A", "FREE")),
    ("RWP-SW2/2F", 2, 409.7, 572.8, ("T/B",)), ("RWP-SW2/1F", 1, 409.7, 572.8, ("F/A", "FREE")),
    ("RWP-TER/1F", 1, 937.4, 597.5, ()), ("RWP-TER/GF", 0, 937.4, 597.5, ("F/A", "FREE")),
    ("RWP-ANX/1F", 1, 120.5, 606.1, ("T/B",)), ("RWP-ANX/GF", 0, 120.5, 606.1, ("F/A", "FREE")),
]

# Indicators only (never a quantity): printed level at the roof the outlet sits on minus the printed free-discharge
# height above the printed level of the surface it discharges onto. The outlet lies below the printed roof level by
# the unstated fall; a GF discharge surface level is not printed at the pipe (court +0.15 / ground +-0.00 nearby).
RWP_LEVEL_INDICATORS = {
    "RWP-SE2": {"top_printed": 9.70, "bottom_printed": 5.50 + 0.15, "nominal_m": round(9.70 - 5.65, 2),
                "status": "HELD (outlet level under the 1 % falls not printed)"},
    "RWP-SW2": {"top_printed": 9.70, "bottom_printed": 5.50 + 0.15, "nominal_m": round(9.70 - 5.65, 2),
                "status": "HELD (outlet level under the 1 % falls not printed)"},
    "RWP-NE": {"top_printed": 9.70, "bottom_printed": None, "nominal_m": None,
               "status": "HELD (GF discharge surface level not printed at the pipe)"},
    "RWP-TER": {"top_printed": 5.50, "bottom_printed": None, "nominal_m": None, "status": "HELD (as RWP-NE)"},
    "RWP-ANX": {"top_printed": 4.30, "bottom_printed": None, "nominal_m": None, "status": "HELD (as RWP-NE)"},
}

# Cross-reference, not recounted here: merged T-370 register (Checker-verified 2026-10-30): FD 19 (3in x 5, 4in x 14),
# RWD 5 (separate population). Listed so B12-02 shows every connection end it would need.
T370_ENDS = {"FLOOR_DRAIN": 19, "ROOF_DRAIN": 5, "WC": 12, "BASIN": 17, "SHOWER": 6, "UNKNOWN_VALVE": 1}

# ---- freelancer side --------------------------------------------------------------------------------------------
# 'Alsenan Chalet_by_category.xlsx', category 'بند صحي' (sanitary), in workbook order; and the tiling labour rows.
FREELANCER_SANITARY = [
    ("sanitary materials", "1 item (lump sum)", "NOT COMPARABLE: no quantity basis"),
    ("'system' item (unit not defined)", "1 item", "NOT IN THE DRAWING: no water heater / booster printed"),
    ("water tanks", "2 qty", "NOT IN THE DRAWING as a count: one 'WATER TANK PLACE' panel is printed (ST p.6, T-221), the number of tanks is not: UNRESOLVED, HELD"),
    ("pit pump", "1 qty", "NOT IN THE DRAWING: sump pump = legend only"),
    ("pit covers", "2 qty", "MH-1 printed = 1 inspection chamber; a 'pit' (soak-away / septic) is printed nowhere: "
                            "UNRESOLVED, +1 not explained by the drawings"),
    ("plumber labour", "1 item (lump sum)", "NOT COMPARABLE"),
]
FREELANCER_SHOWER = 11      # tiling labour 'شاور', qty, 15 KD each
# His own measured wet-room table (finishes workbook, waterproofing sheet, wet floors 72.01 m2): rows by label
FREELANCER_WET_ROWS = {"GF": {"bath (حمامات / حمام)": 6, "wash (مغسله)": 3, "kitchen": 1},
                       "1F": {"bath (حمام)": 5, "laundry": 1}, "2F": {"bath (حمام)": 1}}

SHOWER_POPULATIONS = {
    "drawn shower positions (T-369 / T-370: 3 tray + 3 walk-in)": 6,
    "drawn showers + the UNKNOWN valve in GF W.C 1C8": 7,
    "WC rooms on the drawings (GF 6, 1F 5, 2F 1)": 12,
    "bath rows in his own wet-room table (GF 6, 1F 5, 2F 1)": 12,
    "4in floor drains (T-370)": 14,
    "all floor drains (T-370)": 19,
    "GF + 1F WC rooms (coincidence named by T-370)": 11,
}


def run():
    R.check_items(COUNT_ITEMS + NOT_PRINTED_ITEMS + RUNS)
    counted, held = R.counts(COUNT_ITEMS + NOT_PRINTED_ITEMS, NOT_TO_SCALE)
    stacks, findings = R.chain_stacks(DROPS, tol_pt=12.0)
    runs = [(r.item_id, r.kind, R.status(r, NOT_TO_SCALE), r.diameter or "not printed", r.slope or "-")
            for r in RUNS]
    return counted, held, stacks, findings, runs


if __name__ == "__main__":
    import json
    counted, held, stacks, findings, runs = run()
    print(json.dumps({"counted": counted, "held": held, "stacks": stacks, "findings": findings, "runs": runs},
                     indent=1, ensure_ascii=False))
