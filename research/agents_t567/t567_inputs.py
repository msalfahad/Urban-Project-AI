"""T-567 development-villa inputs: the freelancer's external plaster / Sigma rows mapped to the drawn faces of the merged
ledgers, with every term's arithmetic written out. Repository files only; no coordinate, client name or workbook text.

Drawn faces: T-337 BINDING_T337.csv (109 keys, V3.0.22 binding of the T-305 faces), with the T-348 r2 re-measures and
new faces (FILL_T314_T348.csv), the T-324 parapet inner face + top ranges (FREELANCER_T324.csv), the T-346 band terms
of his rows 65 / 69 (BANDS_T346.csv) and the T-348 r2 terms of his rows 70 / 71 / 74 (RECON_T348.csv).
His cells: tests/alsenan/registers_b1/FREELANCER_RAW_ROWS.json (file PLS, statement sheet rows 51-97, as numbers).
Formula structure read this run from the workbook itself (Drive "Alsenan chalet project", the internal plaster + Sigma
.xls, decoded into the private folder, converted there with LibreOffice so the formulas survive): every I cell of rows
51-90 is PRODUCT(E:H) of the typed count / height / width / length; the elevation subtotals are J55 = SUM(I51:I55),
J61 = SUM(I58:I61), J65 = SUM(I63:I65), J75 = SUM(I68:I75), J79 = SUM(I77:I79), J84 = SUM(I83:I84), J90 = SUM(I87:I90),
J92 = H92 x F92; J93 = SUM(J53:J92) holds each I row exactly once. J97 = SUM(I96:I97) with I96 = J41 (his external
opening list, rows 29-41, the same list his internal plaster deducts) and I97 = 11 x 0.70 x 0.50 (bathroom windows).
Invoice row 25: net = J93 - J97 / 2. Columns A ('ends', m.l) and B ('corners', m.l) are summed in A93 / B93 and paid as
m.l at half (invoice row 26 = (A93 + B93) / 2): no reveal or arris is in his m2.
Candidate: ARCH_TAKEOFF_V3.0.57 line index (research/agents_t507/out/LINE_INDEX_V3_0_57.json); V3.0.58 (arch_v3058.py
docstring (e)) keeps every V3.0.57 line byte-identical, so the facade lines below are the candidate of record's.
"""

FILES = {
    "binding": "research/agents_t337/BINDING_T337.csv",
    "openings": "research/agents_t337/OPENINGS_T337.csv",
    "items": "research/agents_t337/ITEMS_T337.csv",
    "t348_fill": "research/agents_t348/FILL_T314_T348.csv",
    "t348_recon": "research/agents_t348/RECON_T348.csv",
    "t346_bands": "research/agents_t346/BANDS_T346.csv",
    "t324_his": "research/agents_t324/FREELANCER_T324.csv",
    "his_cells": "tests/alsenan/registers_b1/FREELANCER_RAW_ROWS.json",
    "line_index": "research/agents_t507/out/LINE_INDEX_V3_0_57.json",
}

# his elevation groups as his own subtotal formulas group them (statement sheet)
GROUPS = [("SW", "J55", range(51, 56)), ("SE", "J61", range(58, 62)), ("NE", "J65", range(63, 66)),
          ("NW", "J75", range(68, 76)), ("ROOF", "J79", range(77, 80)), ("PARAPETS", "J84", range(83, 85)),
          ("BOUNDARY", "J90", range(87, 91)), ("DRIP", "J92", range(92, 93))]
HIS_GROSS_CELL = "J93"
HIS_OPENINGS_CELL = "J97"
HIS_NET = "1469.9675"        # invoice row 25 (J93 - J97 / 2)

# candidate lines checked on the line index (id prefix -> expected item / class / value)
CANDIDATE = {
    "FIN.EXT.FINISH": {"L-b05f70c92405dbcfbe62": "GF", "L-8bb83e16cc7b104ab88b": "1F", "L-d52c4f763b19aedf8b8b": "2F"},
    "pool_soffit": ("L-23072352a28aeca7b051", "FIN.CEILING", "12.834"),
}

# T-348 r2 changes to the T-337 face set (key -> (class, elevation)); values come from FILL_T314_T348.csv
T348_CLASS = {"storey": "STOREY", "parapet": "PARAPET_OUTER", "slab_edge": "SLAB_EDGE", "reveal": "REVEAL",
              "soffit": "SOFFIT"}
T348_ELEVATION = "NW"   # every T-348 face is on the sea end (the pool block and the void AT225 in front of it)

# Row map. portions: (key, part as "a/b" of the face length, or "1"); terms / his_only: (name, cause, formula or
# (lo, hi) or ("CSV", file, selector), source). Formulas are evaluated exactly (no float).
S162 = "T-162 r2 TERMS_T162.csv / T-337 FREELANCER_T337.csv"
ROWS = [
    {"row": "51", "group": "SW", "portions": [("GF/SW-9/EDGE/plinth", "1"), ("GF/SW-9/EDGE/storey", "1"),
                                              ("GF/SW-9/EDGE/parapet", "1")],
     "terms": [("his height from +-0.00, the drawn face from the floor +0.15 (1.50 x 0.15)", "ENGINE_RIGHT",
                "1.5*0.15", S162)]},
    {"row": "52", "group": "SW",
     "portions": [("GF/SW-7/FLUSH/plinth", "6.77/14.87"), ("GF/SW-7/FLUSH/storey", "6.77/14.87"),
                  ("1F/SW-3/STOREY/storey", "6.77/14.87"), ("1F/SW-3/PARAPET/parapet", "1")],
     "terms": [("plinth below his +1.00 plane (owner Q-07 B bands from the F.F.L.; 6.77 x 0.85)", "RULE_DIFFERENCE",
                "-6.77*0.85", S162),
               ("his width 6.90 vs the drawn 6.77 m over his 10.00 m height", "ENGINE_RIGHT", "(6.90-6.77)*10.0",
                S162)]},
    {"row": "53", "group": "SW",
     "portions": [("GF/SW-7/FLUSH/plinth", "8.10/14.87"), ("GF/SW-7/FLUSH/storey", "8.10/14.87"),
                  ("1F/SW-3/STOREY/storey", "8.10/14.87"), ("2F/SW-1/STOREY+PARAPET/storey", "1"),
                  ("2F/SW-1/STOREY+PARAPET/parapet", "1")],
     "terms": [("his height from +-0.00, the drawn face from +0.15 (8.10 x 0.15)", "ENGINE_RIGHT", "8.10*0.15",
                S162),
               ("his width 7.90 vs the drawn 8.10 m over his 14.40 m", "ENGINE_RIGHT", "(7.90-8.10)*14.4", S162)]},
    {"row": "54", "group": "SW",
     "portions": [(k, "1") for k in ("GF/SW-1/EDGE/plinth", "GF/SW-1/EDGE/storey", "GF/SW-1/EDGE/parapet",
                                     "GF/SW-2/EDGE/plinth", "GF/SW-2/EDGE/storey", "GF/SW-2/EDGE/parapet",
                                     "GF/NW-1/EDGE/plinth", "GF/NW-1/EDGE/storey", "GF/NW-1/EDGE/parapet")],
     "terms": [("annex run allocation: his 4.00 m vs the drawn 5.642 m (SW-1 3.10 + SW-2 arc 2.042 + NW-1 0.50) at "
                "the annex height 4.80 (group 54 + 55 + 60: 18.50 vs 18.742 m)", "ENGINE_RIGHT", "(4.0-5.642)*4.8",
                S162),
               ("his height 5.25 vs the printed annex top +4.80 on his 4.00 m (no 5.25 level printed)",
                "ENGINE_RIGHT", "(5.25-4.8)*4.0", S162),
               ("his height from +-0.00, the drawn faces from +0.15 (5.642 x 0.15)", "ENGINE_RIGHT", "5.642*0.15",
                S162),
               ("SW-2 arc face areas at 4 decimals (T-305) vs 2.042 x 4.65", "ROUNDING", "2.042*4.65-9.4955",
                "T-305 FACE_LINE_LEDGER 4-dp areas")]},
    {"row": "55", "group": "SW",
     "portions": [(k, "1") for k in ("GF/SW-3/EDGE/plinth", "GF/SW-3/EDGE/storey", "GF/SW-3/EDGE/parapet",
                                     "GF/SW-3/COVERED/plinth", "GF/SW-3/COVERED/storey")],
     "terms": [("annex run allocation: his 13.00 m vs the drawn SW-3 6.40 m at 4.80", "ENGINE_RIGHT",
                "(13.0-6.4)*4.8", S162),
               ("his height from +-0.00, the drawn faces from +0.15 (6.40 x 0.15)", "ENGINE_RIGHT", "6.4*0.15", S162),
               ("SW-3 covered 0.20 m strip runs to the house roof +5.50, not +4.80 (0.20 x 0.70)", "ENGINE_RIGHT",
                "-0.2*0.7", S162)]},
    {"row": "58", "group": "SE",
     "portions": [(k, "1") for k in ("2F/SE-1/STOREY+PARAPET/storey", "2F/SE-1/STOREY+PARAPET/parapet",
                                     "1F/SE-2/STOREY/storey", "GF/SE-4/FLUSH/plinth", "GF/SE-4/FLUSH/storey")],
     "terms": [("his one plane 6.75 m wide from +-0.00: below +9.70 only the 4.50 m tower strip stands in that plane; "
                "the 2.25 m over the porch is open / the 1F roof (2.25 x 9.70); the recessed entrance faces behind it "
                "are our GF SE-2 / SE-3 (OURS_ONLY)", "ENGINE_RIGHT", "2.25*9.70", S162),
               ("his height from +-0.00, the tower strip from +0.15 (4.50 x 0.15)", "ENGINE_RIGHT", "4.5*0.15", S162),
               ("his width 6.75 vs the 2F face 6.80 m above +9.70 (4.70 m)", "ENGINE_RIGHT", "(6.75-6.80)*4.7",
                S162)]},
    {"row": "59", "group": "SE",
     "portions": [(k, "1") for k in ("1F/SE-1/STOREY/storey", "1F/SE-1/PARAPET/parapet",
                                     "1F/SE-1/OVER_LOWER_ROOF/over_lower_roof")],
     "terms": [("his length 5.25 vs the drawn 1F street face 7.50 m, at his 11.85 m", "ENGINE_RIGHT",
                "(5.25-7.50)*11.85", S162),
               ("his height 11.85 (not printed) vs the drawn bands on 7.50 m: 3.40 m from the annex roof +4.30, 4.10 m "
                "from +5.50 over the porch court, wave top mean +10.741 (his height may take in the recessed porch "
                "faces SE-2 / SE-3 and the 4.10 m slab edge, which we hold apart)", "ENGINE_RIGHT",
                "7.50*11.85-43.387", S162)]},
    {"row": "60", "group": "SE", "portions": [(k, "1") for k in ("GF/SE-1/EDGE/plinth", "GF/SE-1/EDGE/storey",
                                                                 "GF/SE-1/EDGE/parapet")],
     "terms": [("annex run allocation: his 1.50 m vs the drawn SE-1 6.70 m at 4.80 (+-0.00 -> +4.80 both)",
                "ENGINE_RIGHT", "(1.5-6.7)*4.8", S162)]},
    {"row": "61", "group": "SE", "portions": [],
     "his_only": [("frame bands 2 x 0.45 x 27.70: FIN.EXT.FRAME, profile not detailed (no face measured)", "HELD",
                   "2*0.45*27.7", S162)]},
    {"row": "63", "group": "NE", "portions": [(k, "1") for k in ("GF/NE-6/EDGE/plinth", "GF/NE-6/EDGE/storey",
                                                                 "GF/NE-6/EDGE/parapet")],
     "terms": [("his length 10.00 vs the drawn annex NE face 10.80 m at 4.80", "ENGINE_RIGHT", "(10.0-10.8)*4.8",
                S162)]},
    {"row": "64", "group": "NE",
     "portions": [(k, "1") for k in ("GF/NE-4/EDGE/plinth", "GF/NE-4/EDGE/storey", "GF/NE-4/EDGE/parapet",
                                     "1F/NE-2/STOREY/storey", "1F/NE-2/PARAPET/parapet")],
     "terms": [("plinth below his +1.00 plane (Q-07 B; GF NE-4 19.37 x 1.00)", "RULE_DIFFERENCE", "-19.37*1.0", S162),
               ("his one plane hides the 0.50 m band where the GF parapet stands 1.50 m in front of the 1F face "
                "(both faces are built: 19.27 x 0.50)", "ENGINE_RIGHT", "-19.27*0.5", S162),
               ("his width 19.20 vs GF 19.37 (+1.00 -> +6.00) and 1F 19.27 (+6.00 -> +11.00)", "ENGINE_RIGHT",
                "(19.2-19.37)*5.0+(19.2-19.27)*5.0", S162)]},
    {"row": "65", "group": "NE", "portions": [("GF/P-2/COVERED/plinth", "1.3/4.7"), ("GF/P-2/COVERED/storey", "1.3/4.7")],
     "terms": [("T-346 band: his +-0.00 vs the passage floor +0.15", "ENGINE_RIGHT", ("CSV", "65", "0.000000"),
                "T-346 BANDS_T346.csv"),
               ("T-346 band: 0.20 m of his 1.50 is the boundary wall closing the passage (Q-65 C, other trade)",
                "ENGINE_RIGHT", ("CSV", "65", "0.150000|1.000000"), "T-346 BANDS_T346.csv"),
               ("T-346 band: the GF roof runs on over the passage, no face above +5.50", "ENGINE_RIGHT",
                ("CSV", "65", "5.500000"), "T-346 BANDS_T346.csv")],
     "his_only": [("NW end return of the 1.50 m NE band = the same GF NW-7 1.50 m portion as his row 68: double count "
                   "in his sheet (1.50 x 6.00)", "ENGINE_RIGHT", "1.5*6.0", "T-346 ROWS_T346.csv")]},
    {"row": "68", "group": "NW", "portions": [("GF/NW-7/EDGE/plinth", "1.5/7.9"), ("GF/NW-7/EDGE/storey", "1.5/7.9"),
                                              ("GF/NW-7/EDGE/parapet", "1.5/7.9")], "terms": []},
    {"row": "69", "group": "NW",
     "portions": [("GF/NW-7/EDGE/plinth", "6.4/7.9"), ("GF/NW-7/EDGE/storey", "6.4/7.9"),
                  ("GF/NW-7/EDGE/parapet", "6.4/7.9"), ("1F/NW-5/STOREY/storey", "1"), ("1F/NW-5/PARAPET/parapet", "1")],
     "terms": [("plinth below his +1.00 plane (Q-07 B; GF NW-7 6.40 x 1.00)", "RULE_DIFFERENCE", "-6.4*1.0",
                "T-346 ROWS_T346.csv (drawn outside his band 6.400)"),
               ("T-346 bands: his width 6.75 vs GF NW-7 6.40 / 1F NW-5 6.725", "ENGINE_RIGHT",
                ("CSV", "69", "1.000000|6.000000|9.700000"), "T-346 BANDS_T346.csv"),
               ("T-346 band: his one plane hides the 0.50 m where the GF parapet stands 1.50 m in front of the 1F face",
                "ENGINE_RIGHT", ("CSV", "69", "5.500000"), "T-346 BANDS_T346.csv"),
               ("T-346 band: his rectangle to the wave's printed peak +10.80 vs the drawn wave (mean top +10.148)",
                "ENGINE_RIGHT", ("CSV", "69", "10.148089"), "T-346 BANDS_T346.csv")]},
    {"row": "70", "group": "NW",
     "portions": [(k, "1") for k in ("1F/NW-1/STOREY/storey", "1F/NW-1/PARAPET/parapet", "1F/NW-3/STOREY/storey",
                                     "1F/NW-3/PARAPET/parapet", "1F/NW-2/PARAPET/parapet",
                                     "1F/NW-2/SCREEN-FRONT/storey", "GF/POOL-COURT-FRONT/slab_edge")],
     "terms": [("the screen's open arch (inner arch 8.133820 m2, T-348 r2): no face, not in his opening list",
                "ENGINE_RIGHT", "8.133820", "T-348 summary screen_hole_m2"),
               ("T-348: his width 4.95 vs the drawn 4.8077 x 5.70", "ENGINE_RIGHT", "0.811110", "T-348 RECON_T348.csv"),
               ("T-348: CAD parapet tops +10.999 and the DXF chord", "ROUNDING", "0.001084", "T-348 RECON_T348.csv")]},
    {"row": "71", "group": "NW",
     "portions": [("1F/NW-2/SCREEN-BACK/storey", "1"), ("1F/NW-2/STOREY/storey", "1")],
     "terms": [("the screen's open arch seen from the recess (8.133820 m2): no face", "ENGINE_RIGHT", "8.133820",
                "T-348 summary screen_hole_m2"),
               ("T-348: his band above +9.70, where the recess is roofed (no face)", "ENGINE_RIGHT", "6.435000",
                "T-348 RECON_T348.csv"),
               ("T-348: two faces stacked in depth (screen back on the chord + the curved wall on the arc) vs his one "
                "4.95 m width", "ENGINE_RIGHT", "-6.878330", "T-348 RECON_T348.csv")]},
    {"row": "74", "group": "NW",
     "portions": [("1F/NW-3/SW-RETURN/storey", "1"), ("1F/NW-3/SW-RETURN/parapet", "1")],
     "terms": [("T-348 face values at 6 decimals (1.252688 + 0.427737 vs the 1.680424 of the statement)", "ROUNDING",
                "1.680424-1.680425", "T-348 RECON_T348.csv")],
     "his_only": [("the rest of two 4.95 x 5.50 side faces of the pool block: no exterior face exists (NE side runs on "
                   "as NE-2 in his row 64; SW side is the 1F-11 / bath partition behind the W18 strip)", "ENGINE_RIGHT",
                   "52.769576", "T-348 RECON_T348.csv")]},
    {"row": "72", "group": "NW", "portions": [],
     "his_only": [("domes inside and outside 6 x 3.14 x 9.65: owner item 3 (no domes)", "RULE_DIFFERENCE",
                   "6*3.14*9.65", S162)]},
    {"row": "73", "group": "NW", "portions": [],
     "his_only": [("pool-court soffit = the candidate's FIN.CEILING line L-23072352a28aeca7b051 (RELEASED 12.834, owner "
                   "item 4): another line family, not a wall face", "RULE_DIFFERENCE", "12.834",
                   "LINE_INDEX_V3_0_57 / T-127"),
                  ("his soffit 2 x 3.14 x 3.05 vs the measured 12.834", "ENGINE_RIGHT", "2*3.14*3.05-12.834",
                   "owner item 4 / T-127")]},
    {"row": "75", "group": "NW", "portions": [],
     "his_only": [("frame band 0.45 x 8.75: FIN.EXT.FRAME, profile not detailed", "HELD", "0.45*8.75", S162)]},
    {"row": "77", "group": "ROOF",
     "portions": [(k, "1") for k in ("2F/NE-1/STOREY+PARAPET/storey", "2F/NE-1/STOREY+PARAPET/parapet",
                                     "2F/NW-1/STOREY+PARAPET/storey", "2F/NW-1/STOREY+PARAPET/parapet")],
     "terms": [("his run 17.75 vs the 2F NE 8.10 + NW 6.80 = 14.90 m at 4.70 (the 2F SE / SW faces are in his rows "
                "58 / 53): 2.85 m of run no plan draws", "UNRESOLVED", "(17.75-14.90)*4.7", S162)]},
    {"row": "78", "group": "ROOF", "portions": [], "other": ("78", "1F parapet inner face + top (T-324)"),
     "terms": [("his girth 1.70 printed nowhere (drawn 1.30 face + 0.20 top at most)", "UNRESOLVED", ("T324", "78"),
                "T-324 FREELANCER_T324.csv")]},
    {"row": "79", "group": "ROOF", "portions": [], "other": ("79", "annex parapet inner face + top (T-324)"),
     "terms": [("his run 28.40 = the inner run without the B34 extension, top on his run", "ENGINE_RIGHT",
                ("T324", "79"), "T-324 FREELANCER_T324.csv")]},
    {"row": "83+84", "group": "PARAPETS", "portions": [], "other": ("83+84", "GF + 2F parapet inner face + top (T-324)"),
     "terms": [("7.5 m of run in his cells that no plan draws (his 0.70 = 0.50 face + 0.20 top agrees)", "UNRESOLVED",
                ("T324", "83+84"), "T-324 FREELANCER_T324.csv")]},
    {"row": "87-90", "group": "BOUNDARY", "portions": [],
     "his_only": [("boundary wall faces: the candidate's EXT.FENCE.PLASTER family (8 lines, all HELD blank on V3.0.58); "
                   "not a house face (Q-65 C)", "HELD", "2.4*37.65+2.4*5.8+2.4*0.5+4*2.2*0.2", S162)]},
    {"row": "92", "group": "DRIP", "portions": [],
     "his_only": [("drip edge 0.28 x 181.70: nothing drawn, owner not answered (UNKNOWN, no number of ours)",
                   "HELD", "0.28*181.7", S162)]},
]

# his-row ids -> sheet rows (for the cell check)
ROW_CELLS = {"51": [51], "52": [52], "53": [53], "54": [54], "55": [55], "58": [58], "59": [59], "60": [60],
             "61": [61], "63": [63], "64": [64], "65": [65], "68": [68], "69": [69], "70": [70], "71": [71],
             "74": [74], "72": [72], "73": [73], "75": [75], "77": [77], "78": [78], "79": [79], "83+84": [83, 84],
             "87-90": [87, 88, 89, 90], "92": [92]}
