"""T-561 development-villa inputs: candidate paint line ids, the freelancer's PAINT workbook cells as numbers by sheet
row, and drawing-derived values of merged tasks (cited). No coordinate, client name or workbook text is stored.

Candidate: ARCH_TAKEOFF_V3.0.57 line index (research/agents_t507/out/LINE_INDEX_V3_0_57.json); V3.0.58 (T-507) moves only
roof WP lines, so every FIN.PAINT line here is the candidate of record's (as in T-552).
Freelancer: his paint workbook (Drive "Alsenan chalet project", the paint workbook), parsed in
tests/alsenan/registers_b1/FREELANCER_RAW_ROWS.json (file PNT): statement sheet 'wall paint m2' rows 4-28 (length H x
height F per row; rows 18-19 width G x length H; J28 = 1249.375), rows 29-45 his opening list (identical to his plaster
list, J45 116.495), rows 46-51 'decor paint m2' (J51 452.325: ceilings, a CEILING item, listed beside), invoice sheet
rows 16 (walls net 1191.1275 = 1249.375 - 58.2475, his half column) and 18 (decor 452.325), 22 (total 1643.4525). His
paint workbook has NO external row: his exterior coating (Sigma) is his exterior plaster area in the plaster workbook
(OWNER_NOTES_SIGMA_2026-10-21; T-552 s.4, T-567).
"""

LINE_INDEX = "research/agents_t507/out/LINE_INDEX_V3_0_57.json"
FREELANCER_GROSS = "1249.375"         # J28
FREELANCER_NET = "1191.1275"          # invoice row 16
FREELANCER_OPENING_LIST = "116.495"   # J45 (J41 61.895 + J44 54.6)
FREELANCER_DECOR = "452.325"          # J51 (ceilings: rooms 337.57 + baths 72.01 + cove 28.285 + 14.46)
FREELANCER_INVOICE_TOTAL = "1643.4525"  # invoice row 22 = net walls + decor

# his paint rows that are his plaster rows 1:1 (T-552 used plaster sheet rows): plaster row -> paint row.
ROW_MAP = {4: 4, 5: 5, 6: 6, 7: 7, 8: 8, 9: 9, 11: 11, 12: 12, 13: 13, 14: 14, 15: 15, 16: 16, 19: 21, 20: 22,
           23: 24, 24: 25, 26: 27}
# rows in his paint that are NOT in his plaster: the stair flight soffits (his label: for the stair soffits).
# (paint row, width G, length H, stair read from his label, T-281 stair id, T-281 measured true area method D)
SOFFIT_ROWS = [(18, "1.2", "20.2", "service stair (enclosed shaft stair)", "ST-01", "17.243246", "L-1fcec332"),
               (19, "2.1", "7.5", "hall stair", "ST-02", "4.905788", "L-c77e3887")]
T281 = ("T-281 STAIR_SOFFIT_V1 summary.json totals true_D_measured (ST-01 2 rows HELD, 1.50 m2 plan; ST-02 RS-C curved "
        "flight HELD, 4.443156 m2 plan, helicoid soffit not drawn)")

T128 = "T-128 r3 ROOMS_T128_R3.csv (walked drawn faces; OWNER_H = owner G1, DWG_PAINT_TILE_H = drawing-derived)"
# paint line element key per T-552 DRY room key
PAINT_ELEMENT = {"GF-01": "GF_01", "GF-04": "GF_04", "GF-15": "GF_15", "GF-08": "GF_08", "1F-01": "1F_01",
                 "1F-04": "1F_04", "1F-10": "1F_10", "1F-11": "1F_11", "1F-13": "1F_13", "2F-03": "2F_03",
                 "2F-01": "2F_01"}
SHAFT_PAINT_LINES = ["ST_GF", "ST_1F", "ST_2F"]

# SHAFT (T-173, actual exposed geometry, Q-72 B): paint gross 171.88 .. 175.14 (b 0.10 .. 0); plaster 173.82 .. 177.07.
SHAFT_PAINT_GROSS_HI = "175.14"
SHAFT_PAINT_GROSS_LO = "171.88"
SHAFT_PAINT_NET = ("154.87", "159.03")
SHAFT_PAINT_NET_LO_ALL_HELD = "135.26"
T173 = "T-173 STAIR_SHAFT_WALLS s.1 / s.3 (his box closed to the drawing, test tests/t173_shaft)"
SHAFT_COMPONENTS = [  # name, qty, sign (+: in his gross, not in the drawing), cause, source
    ("south side: his box counts a 2.40 m south wall over 12.90 m; above +5.50 the void is open to the arrival "
     "landings (GF south wall only, under the 1F slab)", "20.11", 1, "ENGINE_RIGHT", T173),
    ("north side: his width 2.40 vs printed 2.50 and his +1.00 start vs the +0.30 lobby", "2.64", -1, "ENGINE_RIGHT",
     T173),
    ("west / east: his 5.00 x 12.90 x 2 vs the faces to 5.20 under the slabs, the lobby / steps and the roof soffit "
     "0.16 below +13.90", "3.62", -1, "ENGINE_RIGHT", T173),
    ("paint top: under the roof the paint stops at the 0.15 decor line (Q-48 A, ASSUMED - OWNER-APPROVED in T-173), "
     "his 12.90 runs to the plaster top (T-173 plaster gross 177.07 - paint gross 175.14)", "1.93", 1,
     "RULE_DIFFERENCE", T173 + "; owner 2026-11-02 paint to the finished ceiling"),
]
SHAFT_RESIDUAL = ("his row 25 (2.50 x 5.40 = 13.50, matches no drawn face, T-173) + his row 8 'stair wall' (11.25 x "
                  "3.60 = 40.50: no stair face outside the shaft box his row 24 already covers from +1.00)")

RETURN_HIS = (27, "14", "0.2", "5.7")   # E27 doors x F27 0.20 x H27 5.70 = J27 15.96

# Drawing-derived paint height terms (T-128 r3 s.2): interval - slab 0.16 - build-up b (0 .. 0.10, not printed) - decor
# 0.15 (Q-48 A). Owner G1: interval - 0.60 beam - 0.15 decor - 0.10 floor (Q-48 A; Q-52 C: an approximation).
DRY_DWG_COLS = ("DWG_PAINT_TILE_H_M", "DWG_GROSS_M2", "DWG_NET_M2", "DWG_STATUS")
