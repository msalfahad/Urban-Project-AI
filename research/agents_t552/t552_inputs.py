"""T-552 development-villa inputs: candidate plaster line ids / values, the freelancer's plaster workbook cells as
numbers by sheet row, and drawing-derived face values of merged tasks (cited). No coordinate, client name or workbook
text is stored.

Candidate: ARCH_TAKEOFF_V3.0.57 line index (research/agents_t507/out/LINE_INDEX_V3_0_57.json, sha256 prefix
fed5141ea31bfdd9). V3.0.58 (T-507, arch_v3058.py docstring (e)) moves only FIN.WP.ROOF / FIN.WP.ROOF_UPTURN and keeps
every V3.0.57 line byte-identical, so every FIN.PLASTER line here is the candidate of record's.
Freelancer: his plaster workbook (Drive "Alsenan chalet project", the internal plaster + Sigma workbook), as parsed in
tests/alsenan/registers_b1/FREELANCER_RAW_ROWS.json (file PLS, sha256 prefix 752c9f4e0c4546d0): statement sheet rows
4-27 (internal: length H x height F per row, J27 = 1209.385), rows 29-45 (his opening list: J41 61.895 + J44 54.6 =
J45 116.495), rows 51-93 (external + Sigma, J93 = 1502.84), rows 96-97 (external openings J97 65.745); invoice sheet
rows 16 (internal net 1151.1375 = 1209.385 - 58.2475, his 'half' column), 18 (spatter wet rooms 433.83), 25 (external
net 1469.9675 = 1502.84 - 32.8725).
Drawing faces: T-128 r3 (research/agents_t128/ROOMS_T128_R3.csv, sha256 prefix 696333bc12f0acb9; walked faces, two
methods; owner G1 heights), T-173 (stair shaft, actual exposed geometry, his rows closed exactly), T-337
(research/agents_t337/FREELANCER_T337.csv, sha256 prefix 0f7d962798425b8a; exterior face map of his rows 51-92).
"""

LINE_INDEX = "research/agents_t507/out/LINE_INDEX_V3_0_57.json"
FREELANCER_INTERNAL_GROSS = "1209.385"   # J27
FREELANCER_INTERNAL_NET = "1151.1375"    # invoice row 16
FREELANCER_OPENING_LIST = "116.495"      # J45 (J41 + J44)
FREELANCER_EXTERNAL_GROSS = "1502.84"    # J93
FREELANCER_EXTERNAL_NET = "1469.9675"    # invoice row 25
FREELANCER_EXTERNAL_OPENINGS = "65.745"  # J97
FREELANCER_WET_SPATTER = "433.83"        # J47 / invoice row 18 (= his wall-tile total, T-317)

T128 = "T-128 r3 ROOMS_T128_R3.csv (walked drawn faces, owner G1 heights Q-43 / Q-48 A)"
# DRY rooms: T-128 row, description, candidate line (id, state, net or (lo, hi) or None), face lm, owner G1 height,
# his rows [(sheet row, length H, height F)], crossing beams (T-128 col CROSSING_BEAMS: wall-end sections under Q-72).
DRY = [
    ("GF-01", "GF annex reception room", ("L-b1529955", "HELD", None), "20.127", "3.15",
     [(4, "20.0", "3.6")], ["CB6 0.75"], (("45.75", "61.20"), "T-128 r3 owner net, G2 PROVISIONAL (annex roof datum)")),
    ("GF-04", "GF annex driver room", ("L-1ddc23d5", "HELD", None), "12.5", "3.15",
     [(5, "12.5", "3.6")], [], (("33.74", "35.63"), "T-128 r3 owner net, G2 PROVISIONAL")),
    ("GF-15", "GF master bed room", ("L-0d93f220", "RELEASED", "56.0131"), "21.537", "3.65",
     [(6, "21.05", "3.6")], [], None),
    ("GF-08", "GF open room (dining / entrance / reception)", ("L-8cecb1d0", "HELD", ("152.0505", "178.805")),
     "53.188", "3.65", [(7, "54.25", "3.6")], ["B26 0.85", "B27 0.85"], None),
    ("1F-01", "1F master bed room west", ("L-af9621f4", "RELEASED", "51.415"), "17.7", "3.35",
     [(11, "17.5", "3.4")], ["B6 0.50"], None),
    ("1F-04", "1F master bed room 500 x 365", ("L-971f0bda", "RELEASED", "52.005"), "17.4", "3.35",
     [(12, "17.3", "3.4")], [], None),
    ("1F-10", "1F master bed room 380 x 430", ("L-2ba8077b", "HELD", ("48.94", "52.29")), "16.2", "3.35",
     [(13, "22.3", "3.4")], ["B19 0.75", "B6 0.50"], None),
    ("1F-11", "1F master bed room east (curved)", ("L-31db3c83", "HELD", ("61.4626", "61.7177")), "22.149", "3.35",
     [(14, "21.9", "3.4")], [], None),
    ("1F-13", "1F living + corridor + landing", ("L-9b4a7bab", "HELD", ("111.0177", "114.3677")), "39.45", "3.35",
     [(15, "40.25", "3.5"), (16, "9.35", "3.4")], ["B25 / CB12 0.75 on edges"], None),
    ("2F-03", "2F room 300 x 645", ("L-4ce74fc3", "RELEASED", "57.775"), "18.9", "3.35",
     [(19, "18.9", "3.4")], ["B2 0.40"], None),
    ("2F-01", "2F stair lobby", ("L-ae0cdd79", "HELD", ("22.6502", "26.0002")), "9.009", "3.35",
     [(20, "9.0", "3.4")], ["B15 1.20"], None),
]
# A WET space priced in his dry rows (render by the tiler, owner 2026-11-02; Q-06 A basin space): scope row.
WET_IN_HIS_DRY = [("GF-02", "GF annex wash by the reception room", "7.2", [(9, "6.75", "3.6")],
                   "WET (T-128 KIND; owner Q-06 A wash space): spatter + levelling render, the tiler's render line is "
                   "HELD blank (annex G2); not a dry plaster face")]

# SHAFT: candidate lines (T-128 r2 storey-interval nets, superseded for the element by T-173) and T-173's gross.
SHAFT_LINES = [("L-95f2c45c", "ST_GF", ("48.52", "62.01")), ("L-0eac839f", "ST_1F", ("42.48", "47.67")),
               ("L-418121a4", "ST_2F", None)]
SHAFT_GROSS_HI = "177.07"   # T-173 drawing-derived plaster gross, build-up b = 0
SHAFT_GROSS_LO = "173.82"   # b = 0.10 (not printed)
SHAFT_NET = ("156.82", "160.98")
SHAFT_HIS_ROWS = [(23, "14.8", "12.9"), (24, "2.5", "5.4"), (8, "11.25", "3.6")]
T173 = "T-173 STAIR_SHAFT_WALLS s.1 / s.3 (his box closed to the drawing, test tests/t173_shaft)"
SHAFT_COMPONENTS = [  # name, qty, sign (+: in his gross, not in the drawing), cause
    ("south side: his box counts a 2.40 m south wall over 12.90 m; above +5.50 the void is open to the arrival "
     "landings (GF south wall only, under the 1F slab)", "20.11", 1, "ENGINE_RIGHT"),
    ("north side: his width 2.40 vs printed 2.50 and his +1.00 start vs the +0.30 lobby", "2.64", -1, "ENGINE_RIGHT"),
    ("west / east: his 5.00 x 12.90 x 2 vs the faces to 5.20 under the slabs, the lobby / steps and the roof soffit "
     "0.16 below +13.90", "3.62", -1, "ENGINE_RIGHT"),
]
SHAFT_RESIDUAL = ("his row 24 (2.50 x 5.40 = 13.50, matches no drawn face, T-173) + his row 8 'stair wall' (11.25 x "
                  "3.60 = 40.50: no stair face outside the shaft box his row 23 already covers from +1.00)")

# RETURNS (door jambs / head, UP-FIN-PLASTER-001): all FIN.PLASTER lines whose element is an OPENING or REVEAL.
RETURN_HIS = (26, "14", "0.2", "5.7")   # E26 doors x F26 0.20 x H26 5.70 = J26 15.96

# WET: render lines (the candidate's wet-room FIN.PLASTER backing lines, T-331 / T-454): owned by T-547 (tile) and
# T-317 / T-349 (spatter); listed so each wet face is owned once, never reconciled against his dry plaster.

# Q-72 soffit heights (owner 2026-11-02): interval - slab - floor build-up b; slab 0.16 (structural general note 'all
# slabs 16 cm unless stated', T-128 s.2); b not printed: 0 .. 0.10 (owner floor allowance Q-43 as the upper bound).
INTERVALS = {"GF_MAIN": ("4.50", "section A-A storey marks +1.00 / +5.50 (T-128 s.2)"),
             "GF_ANNEX": ("4.00", "marks +0.30 / +4.30, PROVISIONAL (G2, finished roof mark, DCR-6)"),
             "1F": ("4.20", "marks +5.50 / +9.70 (T-128 s.2)"),
             "2F": ("4.20", "marks +9.70 / +13.90, PROVISIONAL-DATUM (roof build-up not printed, D-39)")}
ZONE = {"GF-01": "GF_ANNEX", "GF-04": "GF_ANNEX", "GF-15": "GF_MAIN", "GF-08": "GF_MAIN", "1F-01": "1F",
        "1F-04": "1F", "1F-10": "1F", "1F-11": "1F", "1F-13": "1F", "2F-03": "2F", "2F-01": "2F"}
UNDER_ROOF = {"GF-01": "1.0", "GF-04": "1.0", "GF-15": "0.15", "GF-08": "0.61", "1F-01": "1.0", "1F-04": "1.0",
              "1F-10": "0.59", "1F-11": "1.0", "1F-13": "0.57", "2F-03": "1.0", "2F-01": "1.0"}  # T-128 share
SLAB = ("0.16", "structural general note 'all slabs 16 cm unless stated' (T-128 s.2)")
BUILDUP = (("0", "0.10"), "not printed: 0 .. 0.10 (owner floor allowance Q-43 as the bound, T-128 s.2)")

# EXTERNAL: T-337 class of each of his rows -> cause in this bridge.
EXT_CAUSE = {"MAPPED": "ENGINE_RIGHT", "MAPPED_AS_GROUP": "ENGINE_RIGHT", "PARTIAL": "ENGINE_RIGHT",
             "RULE_DIFFERENCE": "RULE_DIFFERENCE", "per T-324": "ENGINE_RIGHT"}
EXT_SCOPE = {  # his rows with no wall face in the drawing map: (cause, rule / owner source)
    "NOT_IN_T159": ("HELD", "T-337 / T-159: frame bands not measured (profile not printed)"),
    "EXCLUDED": ("RULE_DIFFERENCE", "owner note item 3 (OWNER_NOTES_SIGMA_2026-10-21: no domes; T-161)"),
    "HELD_Q-65": ("HELD", "owner Q-65 C: boundary wall is another trade (EXT.FENCE lines, HELD)"),
    "HELD_UNANSWERED": ("HELD", "owner note item 3 (drip edge FIN.EXT.DRIP not answered)"),
}
POOL_SOFFIT = ("73", "L-23072352a28aeca7b051", "12.834",
               "owner note item 4 accepts the measured pool-court soffit 12.834 (T-127, Checker 12.8343): a CEILING "
               "line (FIN.CEILING), not a wall face")
