"""CONSTRUCTABILITY CASES - Phase 2B-4: the audited rooms, every cutting plan written out piece by piece, the hand
derivation of each plan and its expected quantities as LITERALS typed from that derivation.

Rules for this file (as Phase 2B-3): no expected value is computed here - test_p2b4_independence checks that every
expected value is a literal; nothing here imports the engine or any calculator. Units: plan geometry in millimetres
(the calculator's unit); expected values in metres and square metres.

Values used, all from the approved Urban rules or stated as audit parameters:
    roll 1.00 x 10.00 m (UP-WP-001); side lap and band end lap 0.10 m (UP-WP-002); upturn 0.20 m (UP-WP-003);
    doorway continuation = door width x wall depth, lapped 0.10 m onto the floor (UP-WP-DOOR-001); wall depth at
    every door 0.20 m (the synthetic assumption of the Phase 2B-3 cases).
    j - the flange of a separate upstand on the floor - is NOT an Urban rule: V2.5 sets it to the 0.10 m lap of
    UP-WP-002. The audit treats it as a product value and shows other widths as sensitivities, never as standards.
"""

ROOM_B = {"id": "WP-B", "title": "Bathroom 4.00 x 3.00 m, one 1.00 m door (the 3 x 4 m bathroom)",
          "poly": [(0, 0), (4000, 0), (4000, 3000), (0, 3000)],
          "doors": [{"id": "D1", "edge": 0, "t0": 1500, "t1": 2500, "depth": 200}], "pipes": []}
ROOM_E = {"id": "WP-E", "title": "Wet area 3.60 x 3.00 m, two doors and a pipe sleeve",
          "poly": [(0, 0), (3600, 0), (3600, 3000), (0, 3000)],
          "doors": [{"id": "D1", "edge": 3, "t0": 1500, "t1": 2400, "depth": 200},
                    {"id": "D2", "edge": 2, "t0": 400, "t1": 1200, "depth": 200}],
          "pipes": [{"id": "T1", "x": 3200, "y": 400}]}
ROOM_D = {"id": "WP-D", "title": "L-shaped bathroom 3.00 x 3.00 m less 1.00 x 1.00 m, one 0.90 m door",
          "poly": [(0, 0), (3000, 0), (3000, 2000), (2000, 2000), (2000, 3000), (0, 3000)],
          "doors": [{"id": "D1", "edge": 0, "t0": 500, "t1": 1400, "depth": 200}], "pipes": []}
ROOMS = {"WP-B": ROOM_B, "WP-E": ROOM_E, "WP-D": ROOM_D}

COMMON_B = [
    "floor 4.00 x 3.00 = 12.00 m2; perimeter 14.00 m; door 1.00 m -> wall upturn run 13.00 m (one open run, jamb "
    "to jamb), upturn 13.00 x 0.20 = 2.60 m2; doorway continuation 1.00 x 0.20 = 0.20 m2",
    "proven subtotal (the surfaces to waterproof) = 12.00 + 2.60 + 0.20 = 14.80 m2 - no lap, no junction, no detail",
    "run positions from the east jamb (x 2.50) going east: corners SE 1.50, NE 4.50, NW 8.50, SW 11.50; the run "
    "ends at the west jamb (x 1.50) at 13.00",
]

# ------------------------------------------------------------------------------------------------- WP-B plans
WPB_A1 = {
    "id": "WPB-A1", "room": "WP-B", "junction": "SEPARATE_UPSTAND, flange 0.10 m", "reading": "V2.5 (as planned)",
    "title": "The V2.5 cutting plan, rebuilt piece by piece",
    "plan": {"method": "A", "along": "Y", "j": 100,
             "rolls": [[("S1", 3000), ("S2", 3000), ("S3", 3000)], [("S4", 3000), ("C5", 3000), ("G", 2800)]],
             "rip": {"C5": [("S5", 400), ("L1", 300), ("L2", 300)], "G": [("L3", 300), ("L4", 300), ("L5", 300)]},
             "cross": {"L1": [("DW", 1000), ("B2", 2000)], "L2": [("B1", 3000)], "L3": [("B3", 2800)],
                       "L4": [("B4", 2800)], "L5": [("B5", 2800)]},
             "floor": ["S1", "S2", "S3", "S4", "S5"], "runs": [["B1", "B2", "B3", "B4", "B5"]],
             "doorways": {"D1": "DW"}},
    "hand": COMMON_B + [
        "floor strips 3.00 m long laid across x: S1 0.00-1.00, S2 0.90-1.90, S3 1.80-2.80, S4 2.70-3.70, S5 3.60-4.00",
        "roll 1: S1 0-3.00, S2 3.00-6.00, S3 6.00-9.00, 1.00 m untouched; roll 2: S4 0-3.00, C5 3.00-6.00, "
        "G 6.00-8.80, 1.20 m untouched",
        "C5 (1.00 x 3.00) ripped lengthwise: S5 0.40 + L1 0.30 + L2 0.30 (no residue); G (1.00 x 2.80) ripped: L3, L4, "
        "L5 0.30 + a 0.10 x 2.80 residue",
        "L1 cross-cut: DW 1.00 (the doorway piece, 0.30 = 0.20 in the opening + 0.10 onto the floor) + B2 2.00; "
        "L2 = B1 3.00; L3, L4, L5 = B3, B4, B5 2.80",
        "band laid from the east jamb: B1 0-3.00, B2 2.90-4.90, B3 4.80-7.60, B4 7.50-10.30, B5 10.20-13.00 "
        "(each piece laps 0.10 over the one before)",
        "laps: side 4 x 3.00 x 0.10 = 1.20; floor-to-wall flange 13.00 x 0.10 = 1.30; band end laps 4 x 0.30 x 0.10 "
        "= 0.12; doorway piece onto the floor 1.00 x 0.10 = 0.10 -> 2.72 m2",
        "installed = floor 13.20 + doorway 0.30 + band 0.30 x 13.40 = 4.02 -> 17.52 m2 (= 14.80 + 2.72)",
        "consumed = (5 x 3.00 + 2.80) x 1.00 = 17.80 m2 = 17.52 installed + 0.28 true waste (0.10 x 2.80, narrower "
        "than any piece); 0 reusable; roll stock 1.00 + 1.20 = 2.20 m2; 2 rolls",
        "corners: SE in B1, NE in B2, NW in B4, SW in B5 - every corner inside one piece; the flange folds into a "
        "0.10 x 0.10 pleat at each of the 4 internal corners (0.04 m2, inside the band material)",
        "joints vs corners: 2.90-3.00 -> 1.40; 4.80-4.90 -> 0.30 (NE); 7.50-7.60 -> 0.90; 10.20-10.30 -> 1.20; "
        "min 0.30 m",
        "floor-seam ends on the walls (run positions): S1/S2 7.50-7.60 & 12.40-12.50, S2/S3 6.60-6.70 (its south end "
        "is in the doorway), S3/S4 5.70-5.80 & 0.20-0.30, S4/S5 4.80-4.90 & 1.10-1.20",
        "joint 4.80-4.90 lies exactly on the S4/S5 seam end and joint 7.50-7.60 on the S1/S2 seam end: two "
        "four-layer points (floor lap under band lap)",
        "seam ends under the flange 7, under the doorway lap 1 (S2/S3); the doorway piece meets B1 at the east "
        "jamb and B5 at the west jamb edge to edge: 2 butt joints",
        "the same five pieces laid from the west jamb in the order 2.00, 3.00, 2.80, 2.80, 2.80 put the joints at "
        "11.00-11.10, 8.10-8.20, 5.40-5.50, 2.70-2.80: >= 0.30 m from every corner and >= 0.20 m from every seam end",
    ],
    "expected": {"consumed_m2": 17.8, "installed_m2": 17.52, "laps_side_m2": 1.2, "laps_junction_m2": 1.3,
                 "laps_band_end_m2": 0.12, "laps_doorway_m2": 0.1, "laps_total_m2": 2.72, "true_waste_m2": 0.28,
                 "reusable_m2": 0.0, "stock_m2": 2.2, "rolls": 2, "floor_seams": 4, "band_joints": 4, "seams": 8,
                 "min_joint_corner_m": 0.3, "min_joint_seam_end_m": 0.0, "joints_stacked_on_seam_ends": 2,
                 "jamb_butt_joints": 2, "corners_internal": 4, "corners_external": 0, "flange_pleats_m2": 0.04,
                 "flange_gaps_m2": 0.0, "t_flange_over_seam_end": 7, "t_doorway_lap_over_seam_end": 1,
                 "best_corner_m": 0.3, "best_seam_end_m": 0.2},
}

WPB_A1_ARR = {
    "id": "WPB-A1-ARR", "room": "WP-B", "junction": "SEPARATE_UPSTAND, flange 0.10 m",
    "reading": "V2.5 pieces, joints rearranged",
    "title": "The same V2.5 pieces laid in a buildable order (no material change)",
    "plan": dict(WPB_A1["plan"], runs=[["B2", "B1", "B3", "B4", "B5"]], reversed=[0]),
    "hand": ["the V2.5 cut list unchanged; the band laid from the west jamb: B2 2.00 at 11.00-13.00, B1 3.00 at "
             "8.10-11.10, B3 at 5.40-8.20, B4 at 2.70-5.50, B5 at 0.00-2.80",
             "joints 2.70-2.80, 5.40-5.50, 8.10-8.20, 11.00-11.10: corners 1.20, 0.90, 0.30, 0.40 -> min 0.30; seam ends "
             "1.50, 0.20 (S3/S4 at 5.70), 0.50, 1.30 -> min 0.20; no joint on a seam end"],
    "expected": {"consumed_m2": 17.8, "installed_m2": 17.52, "laps_total_m2": 2.72, "rolls": 2, "seams": 8,
                 "min_joint_corner_m": 0.3, "min_joint_seam_end_m": 0.2, "joints_stacked_on_seam_ends": 0},
}

WPB_A1_FJ = {
    "id": "WPB-A1-FJ", "room": "WP-B", "junction": "SEPARATE_UPSTAND, flange 0.10 m",
    "reading": "UP-WP-LAY-001 applied to the band plan (fewest joints first)",
    "title": "Fewest band joints: one full trim lane + three 3.44 m segment lanes",
    "plan": {"method": "A", "along": "Y", "j": 100,
             "rolls": [[("S1", 3000), ("S2", 3000), ("S3", 3000)], [("S4", 3000), ("C5", 3000), ("G", 3440)]],
             "rip": {"C5": [("S5", 400), ("L1", 300), ("L2", 300)], "G": [("La", 300), ("Lb", 300), ("Lc", 300)]},
             "cross": {"L1": [("DW", 1000)], "L2": [("B1", 3000)], "La": [("B2", 3440)], "Lb": [("B3", 3440)],
                       "Lc": [("B4", 3420)]},
             "floor": ["S1", "S2", "S3", "S4", "S5"], "runs": [["B1", "B2", "B3", "B4"]], "doorways": {"D1": "DW"}},
    "hand": ["three pieces cannot do it: 3.00 + 2 x (g - 0.10) >= 13.00 needs g >= 5.10 > the 4.00 m tail of roll 2",
             "four pieces: the doorway piece from L1 (2.00 m of L1 left unused), the band from L2 (3.00) and three "
             "lanes of one segment g: 3.00 + 3 x (g - 0.10) >= 13.00 -> g >= 3.434 -> 3.44 m (fits roll 2: 3.00 + "
             "3.00 + 3.44 = 9.44); the last piece is cut 3.42",
             "(the alternative - both trim lanes in the band, the doorway piece from the third segment lane - needs "
             "3.00 + 2.90 + 2 x (g - 0.10) >= 13.00 -> g = 3.65, i.e. more membrane)",
             "consumed 15.00 + 3.44 = 18.44 m2; installed 13.20 + 0.30 + 0.30 x 13.30 = 17.49; laps 1.20 + 1.30 + "
             "3 x 0.03 + 0.10 = 2.69; reusable L1's 0.30 x 2.00 = 0.60; true waste 0.10 x 3.44 + 0.30 x 0.02 = 0.35",
             "joints 2.90-3.00, 6.24-6.34, 9.58-9.68: corners >= 1.08 m, seam ends >= 0.26 m (S2/S3 at 6.60)",
             "rolls 2; seams 4 floor + 3 joints = 7 (one fewer than V2.5's 8) for 0.64 m2 more membrane"],
    "expected": {"consumed_m2": 18.44, "installed_m2": 17.49, "laps_total_m2": 2.69, "laps_band_end_m2": 0.09,
                 "true_waste_m2": 0.35, "reusable_m2": 0.6, "stock_m2": 1.56, "rolls": 2, "band_joints": 3,
                 "seams": 7, "min_joint_corner_m": 1.08, "min_joint_seam_end_m": 0.26},
}

WPB_A2_LM = {
    "id": "WPB-A2-LM", "room": "WP-B", "junction": "SEPARATE_UPSTAND, flange 0.15 m (sensitivity value)",
    "reading": "V2.5 reading (least membrane within the direction)",
    "title": "A 0.15 m junction flange: strips along X, two short segments",
    "plan": {"method": "A", "along": "X", "j": 150,
             "rolls": [[("S1", 4000), ("S2", 4000), ("G1", 2000)], [("S3", 4000), ("C4", 4000), ("G2", 750)]],
             "rip": {"C4": [("S4", 300), ("L1", 350), ("L2", 350)], "G1": [("L3", 350), ("L4", 350)],
                     "G2": [("L5", 350), ("L6", 350)]},
             "cross": {"G1~w": [("DW", 1000)], "L1": [("B1", 4000)], "L2": [("B2", 4000)], "L3": [("B3", 2000)],
                       "L4": [("B4", 2000)], "L5": [("B5", 750)], "L6": [("B6", 750)]},
             "floor": ["S1", "S2", "S3", "S4"], "runs": [["B1", "B2", "B3", "B4", "B5", "B6"]],
             "doorways": {"D1": "DW"}},
    "hand": ["band 0.20 + 0.15 = 0.35 m wide: a full-width segment gives 2 lanes + 0.30 residue; the 0.60 trim of a "
             "3.00 m strip (ALONG_Y) gives 1 lane",
             "ALONG_Y in 2 rolls is impossible: all the lane material the two roll tails (1.00 + 4.00) and the trim "
             "can give covers 3.00 + 1.00 + 1.00 + 4.00 + 4.00 - 4 x 0.10 = 12.60 < 13.00 -> 3 rolls",
             "ALONG_X: 4 strips 4.00 m (the last 0.30 wide); C4 ripped 0.30 + 0.35 + 0.35 (no residue); tails 2.00 "
             "in each roll",
             "band: L1 4.00 + L2 4.00 cover 7.90; 5.10 left. G1 2.00 in roll 1 (2 lanes cover 3.80), G2 in roll 2: "
             "2 x (g - 0.10) >= 1.30 -> 0.75 m; the doorway piece from the 0.30 residue of G1",
             "consumed 16.00 + 2.00 + 0.75 = 18.75 m2; installed 13.20 + 0.30 + 0.35 x 13.50 = 18.225; laps 1.20 + "
             "1.95 + 5 x 0.035 + 0.10 = 3.425; reusable 0.30 x 1.00 + 0.30 x 0.75 = 0.525; true waste 0",
             "rolls 2; seams 3 + 5 = 8; joints vs corners min 0.10 (11.60-11.70, SW corner 11.50); joint 9.70-9.80 "
             "meets the S2/S3 seam end 9.60-9.70 edge to edge (0.00)"],
    "expected": {"consumed_m2": 18.75, "installed_m2": 18.225, "laps_junction_m2": 1.95, "laps_band_end_m2": 0.175,
                 "laps_total_m2": 3.425, "true_waste_m2": 0.0, "reusable_m2": 0.525, "stock_m2": 1.25, "rolls": 2,
                 "band_joints": 5, "seams": 8, "min_joint_corner_m": 0.1, "min_joint_seam_end_m": 0.0},
}

WPB_A2_FJ = {
    "id": "WPB-A2-FJ", "room": "WP-B", "junction": "SEPARATE_UPSTAND, flange 0.15 m (sensitivity value)",
    "reading": "UP-WP-LAY-001 applied to the band plan (fewest joints first)",
    "title": "A 0.15 m junction flange, fewest band joints",
    "plan": {"method": "A", "along": "X", "j": 150,
             "rolls": [[("S1", 4000), ("S2", 4000), ("G1", 2000)], [("S3", 4000), ("C4", 4000), ("G2", 1400)]],
             "rip": {"C4": [("S4", 300), ("L1", 350), ("L2", 350)], "G1": [("L3", 350), ("L4", 350)],
                     "G2": [("L5", 350), ("L6", 350)]},
             "cross": {"G1~w": [("DW", 1000)], "L1": [("B1", 4000)], "L2": [("B2", 4000)], "L3": [("B3", 2000)],
                       "L4": [("B4", 2000)], "L5": [("B5", 1400)]},
             "floor": ["S1", "S2", "S3", "S4"], "runs": [["B1", "B2", "B3", "B4", "B5"]], "doorways": {"D1": "DW"}},
    "hand": ["four pieces cannot do it: 4.00 + 3.90 + 2 lanes of at most 2.00 (the tails) cover 11.70 < 13.00",
             "five pieces: L1, L2 and both lanes of G1 (2.00) cover 11.70; one lane of G2 covers the last 1.30 -> G2 "
             "= 1.40 m; its second lane (0.35 x 1.40) is not needed",
             "consumed 16.00 + 2.00 + 1.40 = 19.40 m2; installed 13.20 + 0.30 + 0.35 x 13.40 = 18.19; laps 1.20 + "
             "1.95 + 4 x 0.035 + 0.10 = 3.39; reusable 0.30 x 1.00 + 0.35 x 1.40 + 0.30 x 1.40 = 1.21",
             "rolls 2; seams 3 + 4 = 7"],
    "expected": {"consumed_m2": 19.4, "installed_m2": 18.19, "laps_total_m2": 3.39, "true_waste_m2": 0.0,
                 "reusable_m2": 1.21, "stock_m2": 0.6, "rolls": 2, "band_joints": 4, "seams": 7},
}

WPB_B = {
    "id": "WPB-B", "room": "WP-B", "junction": "CONTINUOUS_FOLD (floor sheet folded 0.20 m up every wall)",
    "reading": "both readings (no band, no joint choice)",
    "title": "Continuous fold-up: strips over the developed surface",
    "plan": {"method": "B", "along": "X",
             "rolls": [[("S1", 4400), ("S2", 4400)], [("S3", 4400), ("C4", 4400)]],
             "rip": {"C4": [("S4", 700)]}, "cross": {}, "floor": ["S1", "S2", "S3", "S4"]},
    "hand": ["developed surface: x -0.20..4.20, y -0.20..3.20 (4.40 x 3.40 = 14.96 m2) = the 14.80 m2 to waterproof "
             "+ four 0.20 x 0.20 corner squares (0.16 m2) that are no surface: folded into the corner or cut out",
             "the doorway: the south flap of S1 lies flat into the 1.00 x 0.20 opening; slit 0.20 m at each jamb so the "
             "wall flap can rise - 2 slits",
             "strips along X 4.40 m: 1.00 + 3 x 0.90 = 3.70 >= 3.40 -> 4 strips at y -0.20..0.80, 0.70..1.70, "
             "1.60..2.60, 2.50..3.20 (the last 0.70 wide; trim 0.30 x 4.40)",
             "2 strips per roll (8.80 m, 1.20 m left) -> 2 rolls; consumed 4 x 4.40 = 17.60 m2",
             "installed 3 x 4.40 + 0.70 x 4.40 = 16.28 = 14.80 + side laps 3 x 4.40 x 0.10 = 1.32 + corners 0.16",
             "no floor-to-wall lap, no band joint, no doorway lap; the trim 0.30 x 4.40 = 1.32 m2 is a reusable offcut "
             "(nothing in this room needs it); stock 2.40 m2",
             "seams 3, each crossing the west and east fold lines (6 seam-fold crossings, none in the doorway)",
             "strips along Y (3.40 m) would need 5 strips = 17.00 m but only 2 fit a roll -> 3 rolls; 2 rolls only "
             "with one strip spliced by an end lap (17.10 m2, 5 seams) - fewer seams selects ALONG_X"],
    "expected": {"consumed_m2": 17.6, "installed_m2": 16.28, "laps_total_m2": 1.32, "corner_excess_m2": 0.16,
                 "true_waste_m2": 0.0, "reusable_m2": 1.32, "stock_m2": 2.4, "rolls": 2, "seams": 3,
                 "floor_end_laps": 0, "jamb_slits": 2, "seam_crossings_doorway": 0, "seam_crossings_wall": 6,
                 "proven_subtotal_m2": 14.8},
}

# ------------------------------------------------------------------------------------------------- WP-E plans
COMMON_E = [
    "floor 3.60 x 3.00 = 10.80 m2; perimeter 13.20; doors D1 0.90 (west wall, y 0.60-1.50) and D2 0.80 (north wall, "
    "x 2.40-3.20); upturn run 13.20 - 1.70 = 11.50 m in two runs; upturn 2.30 m2; continuation 0.18 + 0.16 = 0.34",
    "run 1 (3.90 m) from the D2 west jamb westwards and down to the D1 north jamb, corner NW at 2.40; run 2 (7.60 m) "
    "from the D1 south jamb: corners SW 0.60, SE 4.20, NE 7.20, ending at the D2 east jamb",
]
WPE_A1 = {
    "id": "WPE-A1", "room": "WP-E", "junction": "SEPARATE_UPSTAND, flange 0.10 m", "reading": "V2.5 (as planned)",
    "title": "The V2.5 cutting plan, rebuilt piece by piece",
    "plan": {"method": "A", "along": "Y", "j": 100,
             "rolls": [[("G", 3640), ("S1", 3000), ("S2", 3000)], [("S3", 3000), ("C4", 3000), ("H", 900)]],
             "rip": {"C4": [("S4", 900)], "H": [("L1", 300), ("L2", 300), ("L3", 300)],
                     "G": [("La", 300), ("Lb", 300), ("Lc", 300)]},
             "cross": {"L1": [("DW1", 900)], "L2": [("DW2", 800)], "L3": [("P1", 900)],
                       "La": [("P2", 3100), ("P5", 520)], "Lb": [("P3", 3640)], "Lc": [("P4", 3640)]},
             "floor": ["S1", "S2", "S3", "S4"], "runs": [["P1", "P2"], ["P3", "P4", "P5"]],
             "doorways": {"D1": "DW1", "D2": "DW2"}},
    "hand": COMMON_E + [
        "strips along Y 3.00 m: S1 0-1.00, S2 0.90-1.90, S3 1.80-2.80, S4 2.70-3.60 (0.90; trim 0.10 x 3.00 is waste)",
        "H 0.90 m full width -> 3 lanes 0.30 x 0.90: DW1, DW2 (0.80; 0.10 left), P1; G 3.64 -> 3 lanes: P2 3.10 + "
        "P5 0.52 from lane a (0.02 left), P3 and P4 3.64",
        "run 1: P1 0-0.90, P2 0.80-3.90; run 2: P3 0-3.64, P4 3.54-7.18, P5 7.08-7.60",
        "laps: side 3 x 3.00 x 0.10 = 0.90; flange 11.50 x 0.10 = 1.15; band ends 3 x 0.03 = 0.09; doorway pieces "
        "(0.90 + 0.80) x 0.10 = 0.17 -> 2.31; installed 11.70 + 0.51 + 0.30 x 11.80 = 15.75",
        "consumed 16.54 = 15.75 + true waste 0.79 (0.30 + 0.09 + 0.364 + 0.03 + 0.006: all narrower than 0.30 m or "
        "no longer than a lap); stock 0.36 + 3.10 = 3.46; 2 rolls; seams 3 + 3 = 6",
        "joint 7.08-7.18 ends 0.02 m before the NE corner (7.20): a lap edge at an internal corner; 3.54-3.64 is "
        "0.56 m from the SE corner; run 1's joint 0.80-0.90 is 1.50 m from the NW corner",
        "seam ends: run 2 south wall 1.50-1.60, 2.40-2.50, 3.30-3.40; run 1 north wall 0.50-0.60, 1.40-1.50; S3/S4 "
        "ends in doorway D2 under DW2's lap; nearest joint to a seam end 0.14 m (3.54 vs 3.40)",
        "doorways: DW1 laps onto S1 only; DW2's lap crosses the S3/S4 seam end; 4 jamb butt joints (two per door)",
        "pipe sleeve (text anchor 3.20, 0.40): on S4, 0.40 m from the S3/S4 seam, 0.30 m from the south and east "
        "flanges -> a centred square collar up to 0.60 m stays clear; its size and detail are not known (withheld)",
        "rearranged (same pieces): run 1 from the D1 jamb (joint 3.00-3.10, 0.60 m from NW); run 2 order 3.64, "
        "0.52, 3.64 (joints 3.54-3.64 and 3.96-4.06): 0.14 m from every corner and seam end",
    ],
    "expected": {"consumed_m2": 16.54, "installed_m2": 15.75, "laps_side_m2": 0.9, "laps_junction_m2": 1.15,
                 "laps_band_end_m2": 0.09, "laps_doorway_m2": 0.17, "laps_total_m2": 2.31, "true_waste_m2": 0.79,
                 "reusable_m2": 0.0, "stock_m2": 3.46, "rolls": 2, "floor_seams": 3, "band_joints": 3, "seams": 6,
                 "min_joint_corner_m": 0.02, "min_joint_seam_end_m": 0.14, "joints_stacked_on_seam_ends": 0,
                 "jamb_butt_joints": 4, "corners_internal": 4, "corners_external": 0, "flange_pleats_m2": 0.04,
                 "t_flange_over_seam_end": 5, "t_doorway_lap_over_seam_end": 1, "best_corner_m": 0.14,
                 "best_seam_end_m": 0.14, "pipe_clear_m": 0.3, "pipe_patch_max_m": 0.6,
                 "pipe_seam_clear_m": 0.4},
}
WPE_A1_ARR = {
    "id": "WPE-A1-ARR", "room": "WP-E", "junction": "SEPARATE_UPSTAND, flange 0.10 m",
    "reading": "V2.5 pieces, joints rearranged", "title": "The same V2.5 pieces laid in a buildable order",
    "plan": dict(WPE_A1["plan"], runs=[["P1", "P2"], ["P3", "P5", "P4"]], reversed=[0]),
    "hand": ["run 1 laid from the D1 jamb: P1 at 3.00-3.90, P2 at 0.00-3.10 (joint 3.00-3.10)",
             "run 2: P3 0-3.64, P5 3.54-4.06, P4 3.96-7.60: joints 0.56 / 0.14 from SE, 0.14 / 0.56 from the seam end "
             "3.30-3.40"],
    "expected": {"consumed_m2": 16.54, "rolls": 2, "seams": 6, "min_joint_corner_m": 0.14,
                 "min_joint_seam_end_m": 0.14},
}
WPE_A1_FJ = {
    "id": "WPE-A1-FJ", "room": "WP-E", "junction": "SEPARATE_UPSTAND, flange 0.10 m",
    "reading": "UP-WP-LAY-001 applied to the band plan (fewest joints first)",
    "title": "Fewest band joints: run 1 in one piece, run 2 in two",
    "plan": {"method": "A", "along": "Y", "j": 100,
             "rolls": [[("S1", 3000), ("S2", 3000), ("S3", 3000), ("H", 900)], [("C4", 3000), ("G", 3900)]],
             "rip": {"C4": [("S4", 900)], "H": [("L1", 300), ("L2", 300), ("L3", 300)],
                     "G": [("La", 300), ("Lb", 300), ("Lc", 300)]},
             "cross": {"L1": [("DW1", 900)], "L2": [("DW2", 800)], "La": [("P1", 3900)], "Lb": [("P2", 3900)],
                       "Lc": [("P3", 3800)]},
             "floor": ["S1", "S2", "S3", "S4"], "runs": [["P1"], ["P2", "P3"]], "doorways": {"D1": "DW1", "D2": "DW2"}},
    "hand": ["a lane longer than 7.00 m needs a roll with at most one 3.00 m strip -> 3 rolls; so run 2 (7.60) needs "
             "two pieces: at least 1 joint",
             "one segment G 3.90 (lanes: run 1 in one piece 3.90; run 2 3.90 + 3.80) and H 0.90 for the doorway "
             "pieces in the 1.00 m tail of roll 1 (3 strips + H = 9.90); roll 2: C4 + G = 6.90",
             "consumed 12.00 + 0.90 + 3.90 = 16.80 m2; installed 11.70 + 0.51 + 0.30 x 11.60 = 15.69; laps 0.90 + 1.15 "
             "+ 0.03 + 0.17 = 2.25; reusable lane L3 0.30 x 0.90 = 0.27; true waste 0.84",
             "rolls 2; seams 3 + 1 = 4 (V2.5: 6) for 0.26 m2 more; joint 3.80-3.90, 0.30 m from the SE corner"],
    "expected": {"consumed_m2": 16.8, "installed_m2": 15.69, "laps_total_m2": 2.25, "reusable_m2": 0.27,
                 "true_waste_m2": 0.84, "rolls": 2, "band_joints": 1, "seams": 4, "min_joint_corner_m": 0.3,
                 "min_joint_seam_end_m": 0.4},
}
WPE_B = {
    "id": "WPE-B", "room": "WP-E", "junction": "CONTINUOUS_FOLD", "reading": "both readings",
    "title": "Continuous fold-up for the two-door room",
    "plan": {"method": "B", "along": "X", "rolls": [[("S1", 4000), ("S2", 4000)], [("S3", 4000), ("C4", 4000)]],
             "rip": {"C4": [("S4", 700)]}, "cross": {}, "floor": ["S1", "S2", "S3", "S4"]},
    "hand": ["developed 4.00 x 3.40 = 13.60 m2 = 13.44 to waterproof + 0.16 corner squares",
             "strips along X 4.00 m: 4 strips (the last 0.70), 2 per roll -> 2 rolls, 16.00 m2; installed 14.80 = "
             "13.44 + laps 1.20 + corners 0.16; trim 0.30 x 4.00 = 1.20 reusable",
             "D1 flap is made of the ends of S1 and S2: the S1/S2 seam (y 0.70-0.80) runs out through the doorway "
             "into the opening; D2 is S4's north flap; 4 jamb slits",
             "pipe: on S1, 0.30 m from the S1/S2 seam and 0.40 m from the fold lines -> a centred square up to 0.60 m"],
    "expected": {"consumed_m2": 16.0, "installed_m2": 14.8, "laps_total_m2": 1.2, "corner_excess_m2": 0.16,
                 "reusable_m2": 1.2, "true_waste_m2": 0.0, "rolls": 2, "seams": 3, "jamb_slits": 4,
                 "seam_crossings_doorway": 1, "pipe_clear_m": 0.3, "proven_subtotal_m2": 13.44},
}

# ------------------------------------------------------------------------------------------------- WP-D plans
COMMON_D = [
    "floor 9.00 - 1.00 = 8.00 m2; perimeter 12.00; door 0.90 m in the south wall x 0.50-1.40 -> one open run "
    "11.10 m; upturn 2.22; continuation 0.18; proven subtotal 10.40 m2",
    "run positions from the east jamb (x 1.40) going east: SE 1.60, (3,2) 3.60, (2,2) 4.60 EXTERNAL, (2,3) 5.60, "
    "NW 7.60, SW 10.60 (5 internal, 1 external); the run ends at the west jamb at 11.10",
]
WPD_A1 = {
    "id": "WPD-A1", "room": "WP-D", "junction": "SEPARATE_UPSTAND, flange 0.10 m", "reading": "V2.5 (as planned)",
    "title": "The V2.5 cutting plan, rebuilt piece by piece",
    "plan": {"method": "A", "along": "X", "j": 100,
             "rolls": [[("S1", 3000), ("S2", 3000), ("S3", 3000)], [("G", 2800), ("C4", 2000)]],
             "rip": {"C4": [("S4", 300), ("L1", 300), ("L2", 300)], "G": [("L3", 300), ("L4", 300), ("L5", 300)]},
             "cross": {"L1": [("DW", 900), ("B2", 1100)], "L2": [("B1", 2000)], "L3": [("B3", 2800)],
                       "L4": [("B4", 2800)], "L5": [("B5", 2800)]},
             "floor": ["S1", "S2", "S3", "S4"], "runs": [["B1", "B2", "B3", "B4", "B5"]], "doorways": {"D1": "DW"}},
    "hand": COMMON_D + [
        "strips along X: S1 y 0-1.00, S2 0.90-1.90 (3.00 m), S3 1.80-2.80 cut 3.00 m - its 1.00 x 0.80 m corner "
        "(x 2-3, y 2.0-2.8) lies beyond the step and is cut off; S4 2.70-3.00 (2.00 m, from C4)",
        "C4 ripped 0.30 + 0.30 + 0.30 + residue 0.10 x 2.00; G 2.80 ripped into 3 lanes + 0.10 x 2.80",
        "L1: DW 0.90 + B2 1.10; band B1 2.00 0-2.00, B2 1.90-3.00, B3 2.90-5.70, B4 5.60-8.40, B5 8.30-11.10",
        "laps: side 0.30 + 0.30 + 0.20 = 0.80; flange 11.10 x 0.10 = 1.11; band ends 0.12; doorway 0.09 -> 2.12; "
        "installed 8.80 + 0.27 + 3.45 = 12.52",
        "consumed 13.80 = 12.52 + true waste 0.48 (0.20 + 0.28) + the cut-off corner 0.80 (a full 1.00 x 0.80 piece: "
        "reusable, not waste); stock 1.00 + 5.20 = 6.20; 2 rolls; seams 3 + 4 = 7",
        "corners: B1 through SE, B3 through (3,2), (2,2) and (2,3), B4 through NW, B5 through SW; B4 starts exactly at "
        "the internal corner (2,3): its end lap begins on the corner line (joint distance 0.00)",
        "at the external corner (2,2) the flange must be slit: a 0.10 x 0.10 gap in the flange (0.01 m2); the 5 "
        "internal corners fold 0.10 x 0.10 pleats (0.05 m2) - both need the corner treatment (withheld)",
        "seam ends on the walls 2.50-2.60, 3.40-3.50, 5.30-5.40, 7.80-7.90, 8.70-8.80, 9.60-9.70; joints >= 0.20 m "
        "from them; 6 seam ends under the flange",
        "best order of the same pieces (1.10, 2.80, 2.80, 2.00, 2.80): joints 1.00-1.10, 3.70-3.80, 6.40-6.50, "
        "8.30-8.40 -> 0.10 m from the nearest corner (3,2), 0.20 m from the nearest seam end",
    ],
    "expected": {"consumed_m2": 13.8, "installed_m2": 12.52, "laps_side_m2": 0.8, "laps_junction_m2": 1.11,
                 "laps_band_end_m2": 0.12, "laps_doorway_m2": 0.09, "laps_total_m2": 2.12, "true_waste_m2": 0.48,
                 "reusable_m2": 0.8, "stock_m2": 6.2, "rolls": 2, "floor_seams": 3, "band_joints": 4, "seams": 7,
                 "min_joint_corner_m": 0.0, "min_joint_seam_end_m": 0.2, "joints_stacked_on_seam_ends": 0,
                 "jamb_butt_joints": 2, "corners_internal": 5, "corners_external": 1, "flange_pleats_m2": 0.05,
                 "flange_gaps_m2": 0.01, "t_flange_over_seam_end": 6, "t_doorway_lap_over_seam_end": 0,
                 "piece_edges_at_corners": 1, "best_corner_m": 0.1, "best_seam_end_m": 0.2},
}
WPD_A1_ARR = {
    "id": "WPD-A1-ARR", "room": "WP-D", "junction": "SEPARATE_UPSTAND, flange 0.10 m",
    "reading": "V2.5 pieces, joints rearranged", "title": "The same V2.5 pieces laid in the best order",
    "plan": dict(WPD_A1["plan"], runs=[["B2", "B3", "B4", "B1", "B5"]]),
    "hand": ["B2 1.10 at 0-1.10, B3 1.00-3.80, B4 3.70-6.50, B1 6.40-8.40, B5 8.30-11.10: no piece edge at a corner; "
             "nearest joint to a corner 0.10 m (3.70 vs (3,2) at 3.60)"],
    "expected": {"consumed_m2": 13.8, "rolls": 2, "seams": 7, "min_joint_corner_m": 0.1,
                 "min_joint_seam_end_m": 0.2, "piece_edges_at_corners": 0},
}
WPD_REUSE = {
    "id": "WPD-REUSE", "room": "WP-D", "junction": "SEPARATE_UPSTAND, flange 0.10 m",
    "reading": "V2.5 reading, the cut-off corner reused",
    "title": "The doorway piece cut from the 1.00 x 0.80 m corner cut off S3",
    "plan": {"method": "A", "along": "X", "j": 100,
             "rolls": [[("S1", 3000), ("S2", 3000), ("S3", 3000)], [("G", 2500), ("C4", 2000)]],
             "rip": {"C4": [("S4", 300), ("L1", 300), ("L2", 300)], "G": [("L3", 300), ("L4", 300), ("L5", 300)],
                     "S3.o1": [("O1d", 300)]},
             "cross": {"O1d": [("DW", 900)], "L1": [("B2", 2000)], "L2": [("B1", 2000)], "L3": [("B3", 2500)],
                       "L4": [("B4", 2500)], "L5": [("B5", 2500)]},
             "floor": ["S1", "S2", "S3", "S4"], "runs": [["B1", "B2", "B3", "B4", "B5"]], "doorways": {"D1": "DW"}},
    "hand": ["the doorway piece 0.90 x 0.30 from the cut-off corner (0.80 wide x 1.00 long: rip 0.30, cross-cut 0.90)",
             "band: L2 2.00 + L1 2.00 cover 3.90, 7.20 left -> 3 x (g - 0.10) >= 7.20 -> g = 2.50 (2.49: 7.17)",
             "consumed 9.00 + 2.00 + 2.50 = 13.50 m2 (V2.5 13.80); same 2 rolls, same 4 joints, same 12.52 installed",
             "true waste 0.20 + 0.25 + 0.03 = 0.48; reusable 0.50 x 1.00 = 0.50",
             "joints 1.90-2.00, 3.80-3.90, 6.20-6.30, 8.60-8.70: >= 0.20 m from every corner"],
    "expected": {"consumed_m2": 13.5, "installed_m2": 12.52, "laps_total_m2": 2.12, "true_waste_m2": 0.48,
                 "reusable_m2": 0.5, "stock_m2": 6.5, "rolls": 2, "band_joints": 4, "seams": 7,
                 "min_joint_corner_m": 0.2},
}
WPD_FJ = {
    "id": "WPD-FJ", "room": "WP-D", "junction": "SEPARATE_UPSTAND, flange 0.10 m",
    "reading": "UP-WP-LAY-001 applied to the band plan (fewest joints first)",
    "title": "Fewest band joints: two 5.60 m band pieces",
    "plan": {"method": "A", "along": "X", "j": 100,
             "rolls": [[("S1", 3000), ("S2", 3000), ("S3", 3000)], [("G", 5600), ("C4", 2000)]],
             "rip": {"C4": [("S4", 300), ("L1", 300), ("L2", 300)], "G": [("L3", 300), ("L4", 300), ("L5", 300)]},
             "cross": {"L1": [("DW", 900)], "L3": [("B1", 5600)], "L4": [("B2", 5600)]},
             "floor": ["S1", "S2", "S3", "S4"], "runs": [["B1", "B2"]], "doorways": {"D1": "DW"}},
    "hand": ["one piece cannot cover 11.10 m (a roll is 10.00 m); two pieces from one segment: 2g - 0.10 >= 11.10 -> "
             "g = 5.60, in roll 2 with C4 (7.60)",
             "consumed 9.00 + 2.00 + 5.60 = 16.60 m2 (V2.5 13.80); installed 8.80 + 0.27 + 0.30 x 11.20 = 12.43; laps "
             "0.80 + 1.11 + 0.03 + 0.09 = 2.03; true waste 0.20 + 0.56 = 0.76; reusable 3.41",
             "rolls 2; seams 3 + 1 = 4; the single joint 5.50-5.60 ends exactly on the internal corner (2,3) whichever "
             "jamb the band starts from: moving it off the corner needs a longer segment"],
    "expected": {"consumed_m2": 16.6, "installed_m2": 12.43, "laps_total_m2": 2.03, "true_waste_m2": 0.76,
                 "reusable_m2": 3.41, "rolls": 2, "band_joints": 1, "seams": 4, "min_joint_corner_m": 0.0,
                 "best_corner_m": 0.0},
}

PLANS = [WPB_A1, WPB_A1_ARR, WPB_A1_FJ, WPB_A2_LM, WPB_A2_FJ, WPB_B,
         WPE_A1, WPE_A1_ARR, WPE_A1_FJ, WPE_B,
         WPD_A1, WPD_A1_ARR, WPD_REUSE, WPD_FJ]

# The 3 x 4 m bathroom, separate upstand: the selected plan for a junction flange j, hand-verified at the points
# where the answer changes. "V25" = least membrane inside each direction, directions by rolls -> seams -> membrane
# (what V2.5 does); "RULE" = rolls -> seams -> membrane over every plan (UP-WP-LAY-001 applied throughout).
SWEEP_HAND = {
    "j_0.10": {"V25": ("Y", 2, 17.8, 8), "RULE": ("Y", 2, 18.44, 7)},
    "j_0.11": {"V25": ("Y", 2, 18.77, 7), "RULE": ("Y", 2, 18.77, 7)},
    "j_0.15": {"V25": ("X", 2, 18.75, 8), "RULE": ("X", 2, 19.4, 7)},
    "j_0.16": {"V25": ("X", 3, 20.6, 5), "RULE": ("X", 3, 22.55, 4)},
}
SWEEP_HAND_TEXT = [
    "j = 0.10: V25 is the V2.5 plan (17.80, 8 seams); RULE: WPB-A1-FJ (18.44, 7 seams; ALONG_X's best has 7 seams too "
    "but 18.80 m2)",
    "j = 0.11 (band 0.31): the 0.60 trim gives one lane and a 0.29 residue too narrow for the doorway piece; ALONG_Y: "
    "doorway piece from the trim lane (2.00 left), 2.00 + 3 x (g - 0.10) >= 13.00 -> g = 3.77 m in roll 2 (9.77) -> "
    "18.77 m2 with 4 band pieces = 7 seams; ALONG_X's least membrane plan (18.20) has 9 seams -> both readings "
    "select ALONG_Y 18.77",
    "j = 0.15: WPB-A2-LM (18.75, 8 seams) and WPB-A2-FJ (19.40, 7 seams); ALONG_Y needs 3 rolls",
    "j = 0.16 (band 0.36): ALONG_X trim gives one lane 4.00 (+ a 0.34 residue that takes the doorway piece); the two "
    "roll tails (2.00 each, 2 lanes per segment) give at most 4 x 1.90 = 7.60 < 9.00 still needed -> a third roll. "
    "V25: one segment 2 x (g - 0.10) >= 9.00 -> 4.60 m, 16.00 + 4.60 = 20.60 m2, 3 pieces (5 seams; ALONG_Y 20.60 "
    "with 6). RULE: 2 pieces from one segment, 2g - 0.10 >= 13.00 -> 6.55 m, 22.55 m2, 4 seams",
    "so: 2 rolls for every flange up to 0.15 m, 3 rolls from 0.16 m",
]
