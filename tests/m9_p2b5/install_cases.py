"""INSTALLATION CASES - Phase 2B-5: the ten ARCH_TAKEOFF_V2.6 worked examples. Each example follows the verification
chain of the program:

    OWNER / PROJECT RULE -> SOURCE DRAWING -> GEOMETRIC INTERPRETATION -> MEASUREMENT FORMULA
    -> INDEPENDENT EXPECTED RESULT (the hand derivation below, typed as literals) -> ENGINE RESULT -> DIFFERENCE
    -> PASS / FAIL -> BOQ IMPACT

Rules for this file (as Phases 2B-3 and 2B-4): it imports nothing and computes nothing; every expected value is a
literal typed from the hand derivation next to it (test_p2b5_independence checks both). Geometry in millimetres
(integers, counter-clockwise rings); expected values in metres and square metres.

The source drawing of every example is synthetic: its room ring, doors, open edges, obstructions, drains and pipes
are the "room" record (the engine reads it through the same feature builder as the Phase 2B-3 proof cases). Values
used, all approved Urban rules or stated parameters:
    roll 1.00 x 10.00 m (UP-WP-001); side lap and end lap 0.10 m (UP-WP-002); upturn 0.20 m (UP-WP-003); the band
    flange onto the floor 0.10 m (V2.5's assumption, carried as alternative A of the open FLOOR_WALL_JUNCTION);
    doorway continuation = door width x (wall depth 0.20 + 0.10 lap) (UP-WP-DOOR-001); wet areas = bathrooms,
    kitchens, pantries, ironing rooms (owner scope); a drain that is not drawn is NOT_SHOWN, never zero.
The V2.5 cutting plan rules applied by hand: strips n = 1 + ceil((D - W) / (W - s)), the last cut down lengthwise;
a trim at least one band (0.30 m) wide gives band lanes; a doorway piece comes from the shortest lane that fits
(else a new segment); the band takes the shortest lane that finishes the need, else the longest, then the shortest
new full-width segment (1 cm steps, 3 lanes) that finishes every run, weighed against filling the largest roll tail
first; rolls packed exactly; directions compared by rolls, seams, membrane, ALONG_X first.
"""

RULES = ["UP-WP-001 roll 1.00 x 10.00 m", "UP-WP-002 lap 0.10 m", "UP-WP-003 upturn 0.20 m",
         "UP-WP-DOOR-001 doorway continuation width x (depth + 0.10)", "UP-WP-LAY-001 rolls -> seams -> membrane",
         "UP-WP-MAT-001 net / installed / procurement apart", "UP-WP-004 corners and penetrations by detail",
         "N-11 floor-to-wall junction OPEN (alternatives shown)"]

COMMON_OPEN = ["FLOOR_WALL_JUNCTION_UNRESOLVED", "JOINT_OFFSET_UNVERIFIED"]

# ------------------------------------------------------------------------------------------------------- IX-01
IX01 = {
    "id": "IX-01", "case": "WP_A", "title": "2.00 x 2.00 m bathroom, closed (no doorway)",
    "rules": RULES,
    "room": {"poly": [(0, 0), (2000, 0), (2000, 2000), (0, 2000)], "doors": [], "breaks": [], "holes": [],
             "pipes": [], "drains": [], "codes": ["BATHROOM"], "scope": "WET"},
    "interpretation": ["one closed band loop of 8.00 m from the ring start (0, 0); 4 internal corners at run "
                       "positions 0 / 2.00 / 4.00 / 6.00", "no drain drawn: NOT_SHOWN"],
    "formula": ["floor = 2.00 x 2.00; upturn = 8.00 x 0.20; every band piece laps 0.10 over the one before, the "
                "first over the last (5 joints)"],
    "hand": [
        "floor 4.00 + upturn 1.60 = proven subtotal 5.60 m2",
        "strips along X (square: tie, X first): S1 y 0-1.00, S2 0.90-1.90, S3 1.80-2.00 (0.20 wide)",
        "cuts S1 2.00, S2 2.00, and 2.00 ripped into S3 0.20 + lanes 0.30 + 0.30 + residue 0.20 (0.40 m2)",
        "band 8.00 closed: lanes 2.00 + 2.00 cover 1.90 + 1.90; segment 3 x (L - 0.10) >= 4.20 -> 1.50 m, ripped "
        "into 3 lanes + 0.10 residue (0.15 m2)",
        "pieces B1 2.00, B2 2.00, B3 1.50, B4 1.50, B5 1.50: B1 -0.10..1.90, B2 1.80..3.80, B3 3.70..5.20, "
        "B4 5.10..6.60, B5 6.50..8.00",
        "joints 7.90-8.00 (the closure), 1.80-1.90, 3.70-3.80, 5.10-5.20, 6.50-6.60 -> to the corners 0.00, 0.10, "
        "0.20, 0.80, 0.50 -> min 0.00 (the closure joint ends on the corner at the ring start)",
        "floor seams S1/S2 y 0.90-1.00 and S2/S3 y 1.80-1.90 meet the east wall at r 2.90-3.00 / 3.80-3.90 and the "
        "west wall at r 7.00-7.10 / 6.10-6.20: 4 seam ends under the flange",
        "joint 3.70-3.80 touches the seam end 3.80-3.90 (no overlap): min joint-to-seam 0.00, 0 stacked",
        "laps: side 2 x 2.00 x 0.10 = 0.40; flange 8.00 x 0.10 = 0.80; band ends 5 x 0.03 = 0.15 -> 1.35",
        "installed 5.60 + 1.35 = 6.95; consumed 3 x 2.00 + 1.50 = 7.50 = 6.95 + 0.55 true waste; 1 roll, 2.50 m2 "
        "stock; seams 2 + 5 = 7",
        "continuous fold: developed 2.40 x 2.40, 3 strips 2.40 long (the last 0.60 wide) = 7.20 m2, 1 roll, 2 "
        "seams; installed (2 x 1.00 + 0.60) x 2.40 = 6.24 = 5.60 + laps 0.48 + corner squares 4 x 0.04 = 0.16",
    ],
    "expected": {"direction": "X", "proven_subtotal_m2": 5.6, "consumed_m2": 7.5, "installed_m2": 6.95,
                 "laps_total_m2": 1.35, "laps_side_m2": 0.4, "laps_floor_end_m2": 0.0, "laps_junction_m2": 0.8,
                 "laps_band_end_m2": 0.15, "laps_doorway_m2": 0.0, "true_waste_m2": 0.55, "reusable_m2": 0.0,
                 "stock_m2": 2.5, "rolls": 1, "floor_seams": 2, "floor_end_laps": 0, "band_joints": 5, "seams": 7,
                 "band_pieces_m": [1.5, 1.5, 1.5, 2.0, 2.0], "min_joint_corner_m": 0.0, "min_joint_seam_end_m": 0.0,
                 "joints_stacked_on_seam_ends": 0, "jamb_butt_joints": 0, "terminations": 0, "corners_internal": 4,
                 "corners_external": 0, "flange_pleats_m2": 0.04, "flange_gaps_m2": 0.0, "t_flange_over_seam_end": 4,
                 "t_doorway_lap_over_seam_end": 0, "t_seam_end_at_break": 0,
                 "fold": {"rolls": 1, "consumed_m2": 7.2, "installed_m2": 6.24, "laps_m2": 0.48,
                          "corner_excess_m2": 0.16, "seams": 2}},
    "flags": COMMON_OPEN + ["DRAIN_NOT_SHOWN", "JOINT_AT_CORNER", "JOINT_TOUCHES_SEAM_END", "LAY_ORDER_NOT_VALIDATED"],
    "boq_impact": "material only (B, rolls): 6.95 m2 installed, 1 roll; the closure joint at a corner is an "
                  "installation instruction (start the loop off the corner), no quantity change",
}

# ------------------------------------------------------------------------------------------------------- IX-02
IX02 = {
    "id": "IX-02", "case": "WP_B", "title": "3.00 x 4.00 m bathroom, one 1.00 m door (the audited WP-B)",
    "rules": RULES,
    "room": {"poly": [(0, 0), (4000, 0), (4000, 3000), (0, 3000)],
             "doors": [{"id": "D1", "edge": 0, "t0": 1500, "t1": 2500, "depth": 200, "other_side": "DRY"}],
             "breaks": [], "holes": [], "pipes": [], "drains": [], "codes": ["BATHROOM"], "scope": "WET"},
    "interpretation": ["one open run of 13.00 m from the east jamb (x 2.50) round to the west jamb (x 1.50); corners "
                       "SE 1.50, NE 4.50, NW 8.50, SW 11.50"],
    "formula": ["as Phase 2B-4 WPB-A1 (the hand derivation there); the installation layer adds the joint, seam-end "
                "and jamb inventory"],
    "hand": [
        "proven subtotal 12.00 + 2.60 + 0.20 = 14.80 m2; strips ALONG_Y S1..S5 (S5 0.40 wide)",
        "cuts S1-S4 3.00 whole; 3.00 ripped S5 0.40 + L1 + L2; 2.80 ripped L3 L4 L5 + 0.10 residue",
        "DW 1.00 from L1 (2.00 left = B2); B1 = L2 3.00; B3 B4 B5 2.80",
        "joints 2.90-3.00, 4.80-4.90, 7.50-7.60, 10.20-10.30: corners 1.40, 0.30, 0.90, 1.20 -> 0.30; the joints at "
        "4.80 and 7.50 lie on the S4/S5 and S1/S2 seam ends -> 2 stacked, min 0.00",
        "7 seam ends under the flange + 1 under the doorway lap; 2 butt joints at the jambs; best order 2.00, 3.00, "
        "2.80 x 3 from the west jamb: corners >= 0.30, seam ends >= 0.20",
        "consumed 17.80 = installed 17.52 + 0.28 true waste; 2 rolls, stock 2.20; seams 4 + 4 = 8",
        "continuous fold: developed 4.40 x 3.40, 4 strips 4.40 long ALONG_X (the last 0.70) = 17.60 m2, 2 rolls, "
        "3 seams; installed 16.28 = 14.80 + laps 1.32 + corner squares 0.16",
        "junction flange: 2 rolls up to 0.15 m, 3 rolls from 0.16 m (Phase 2B-4 SWEEP_HAND)",
    ],
    "expected": {"direction": "Y", "proven_subtotal_m2": 14.8, "consumed_m2": 17.8, "installed_m2": 17.52,
                 "laps_total_m2": 2.72, "laps_side_m2": 1.2, "laps_floor_end_m2": 0.0, "laps_junction_m2": 1.3,
                 "laps_band_end_m2": 0.12, "laps_doorway_m2": 0.1, "true_waste_m2": 0.28, "reusable_m2": 0.0,
                 "stock_m2": 2.2, "rolls": 2, "floor_seams": 4, "floor_end_laps": 0, "band_joints": 4, "seams": 8,
                 "band_pieces_m": [2.0, 2.8, 2.8, 2.8, 3.0], "min_joint_corner_m": 0.3, "min_joint_seam_end_m": 0.0,
                 "joints_stacked_on_seam_ends": 2, "jamb_butt_joints": 2, "terminations": 0, "corners_internal": 4,
                 "corners_external": 0, "flange_pleats_m2": 0.04, "flange_gaps_m2": 0.0, "t_flange_over_seam_end": 7,
                 "t_doorway_lap_over_seam_end": 1, "t_seam_end_at_break": 0, "best_corner_m": 0.3,
                 "best_seam_end_m": 0.2, "junction_rolls": [2, 3], "junction_roll_change_flange_m": 0.16,
                 "fold": {"rolls": 2, "consumed_m2": 17.6, "installed_m2": 16.28, "laps_m2": 1.32,
                          "corner_excess_m2": 0.16, "seams": 3}},
    "flags": COMMON_OPEN + ["DRAIN_NOT_SHOWN", "JOINT_ON_SEAM_END", "JUNCTION_CHANGES_ROLL_COUNT",
                            "LAY_ORDER_NOT_VALIDATED"],
    "boq_impact": "B 17.52 m2 / 2 rolls as V2.5; the material state becomes PROVISIONAL_DETAILS_OPEN while the "
                  "junction is open (2 rolls with a flange up to 0.15 m, 3 from 0.16 m); 17.60 m2 with a fold",
}

# ------------------------------------------------------------------------------------------------------- IX-03
IX03 = {
    "id": "IX-03", "case": "WP_E", "title": "3.60 x 3.00 m wet area, two doors and a pipe sleeve (the audited WP-E)",
    "rules": RULES,
    "room": {"poly": [(0, 0), (3600, 0), (3600, 3000), (0, 3000)],
             "doors": [{"id": "D1", "edge": 3, "t0": 1500, "t1": 2400, "depth": 200, "other_side": "DRY"},
                       {"id": "D2", "edge": 2, "t0": 400, "t1": 1200, "depth": 200, "other_side": "DRY"}],
             "breaks": [], "holes": [], "pipes": [{"id": "T1", "x": 3200, "y": 400}], "drains": [],
             "codes": ["KITCHEN"], "scope": "WET"},
    "interpretation": ["two open runs: 3.90 m from D2 to D1 and 7.60 m from D1 to D2; a pipe sleeve drawn at "
                       "(3.20, 0.40); no drain drawn"],
    "formula": ["as Phase 2B-4 WPE-A1"],
    "hand": [
        "proven subtotal 10.80 + 11.50 x 0.20 + 0.34 = 13.44 m2; strips ALONG_Y S1..S4 (S4 0.90)",
        "a 3.64 m band segment (3 lanes) and a 0.90 m doorway segment (DW-D1, DW-D2, B1)",
        "run 1: B1 0.90 + B2 3.10, joint 0.80-0.90 (1.50 from the corner, 0.20 from a seam end); run 2: B3 3.64, "
        "B4 3.64, B5 0.52, joints 3.54-3.64 and 7.08-7.18 -> the last ends 0.02 from the corner at 7.20",
        "best order of run 2: 3.64, 0.52, 3.64 -> 0.14 from corners and seam ends",
        "pipe: 0.30 clear of the band flanges, 0.40 of the nearest floor seam -> a centred collar up to 0.60 m",
        "consumed 16.54 = installed 15.75 + 0.79 true waste; 2 rolls, stock 3.46; seams 3 + 3 = 6; 4 butt joints",
        "continuous fold: developed 4.00 x 3.40, 4 strips 4.00 ALONG_X = 16.00 m2, 2 rolls, 3 seams, installed 14.80",
    ],
    "expected": {"direction": "Y", "proven_subtotal_m2": 13.44, "consumed_m2": 16.54, "installed_m2": 15.75,
                 "laps_total_m2": 2.31, "laps_side_m2": 0.9, "laps_floor_end_m2": 0.0, "laps_junction_m2": 1.15,
                 "laps_band_end_m2": 0.09, "laps_doorway_m2": 0.17, "true_waste_m2": 0.79, "reusable_m2": 0.0,
                 "stock_m2": 3.46, "rolls": 2, "floor_seams": 3, "floor_end_laps": 0, "band_joints": 3, "seams": 6,
                 "band_pieces_m": [0.52, 0.9, 3.1, 3.64, 3.64], "min_joint_corner_m": 0.02,
                 "min_joint_seam_end_m": 0.14, "joints_stacked_on_seam_ends": 0, "jamb_butt_joints": 4,
                 "terminations": 0, "corners_internal": 4, "corners_external": 0, "flange_pleats_m2": 0.04,
                 "flange_gaps_m2": 0.0, "t_flange_over_seam_end": 5, "t_doorway_lap_over_seam_end": 1,
                 "t_seam_end_at_break": 0, "best_corner_m": 0.14, "best_seam_end_m": 0.14, "pipe_T1_clear_m": 0.3,
                 "fold": {"rolls": 2, "consumed_m2": 16.0, "installed_m2": 14.8, "laps_m2": 1.2,
                          "corner_excess_m2": 0.16, "seams": 3}},
    "flags": COMMON_OPEN + ["LAY_ORDER_NOT_VALIDATED", "NO_DRAIN_DRAWN"],
    "boq_impact": "B 15.75 m2 / 2 rolls as V2.5; the pipe collar (P-8) stays withheld with its 0.60 m limit",
}

# ------------------------------------------------------------------------------------------------------- IX-04
IX04 = {
    "id": "IX-04", "case": "WP_D", "title": "L-shaped bathroom 3.00 x 3.00 m less 1.00 x 1.00 m (the audited WP-D)",
    "rules": RULES,
    "room": {"poly": [(0, 0), (3000, 0), (3000, 2000), (2000, 2000), (2000, 3000), (0, 3000)],
             "doors": [{"id": "D1", "edge": 0, "t0": 500, "t1": 1400, "depth": 200, "other_side": "DRY"}],
             "breaks": [], "holes": [], "pipes": [], "drains": [], "codes": ["BATHROOM"], "scope": "WET"},
    "interpretation": ["one open run of 11.10 m with 5 internal corners and 1 external (the re-entrant corner); the "
                       "strip crossing the step leaves a 1.00 x 0.80 m rectangle outside the room"],
    "formula": ["as Phase 2B-4 WPD-A1"],
    "hand": [
        "proven subtotal 8.00 + 11.10 x 0.20 + 0.18 = 10.40 m2; strips ALONG_X S1-S3 3.00 long, S4 0.30 x 2.00",
        "S3 crosses the step: its part x 2.00-3.00, y 2.00-2.80 lies outside the room -> a 1.00 x 0.80 m offcut "
        "(REUSABLE_SUBJECT_TO_N7), not a 0.27 x 3.00 trim",
        "band B1 2.00, B2 1.10, B3 2.80, B4 2.80, B5 2.80: B4 starts on the corner (2, 3) at 5.60 -> a joint at a "
        "corner; best order: 0.10 from the corners, 0.20 from the seam ends",
        "consumed 13.80 = installed 12.52 + 0.48 true waste + 0.80 reusable; 2 rolls, stock 6.20; seams 3 + 4 = 7",
        "continuous fold: not computed (not a rectangle; the external corner needs a gusset detail)",
    ],
    "expected": {"direction": "X", "proven_subtotal_m2": 10.4, "consumed_m2": 13.8, "installed_m2": 12.52,
                 "laps_total_m2": 2.12, "laps_side_m2": 0.8, "laps_floor_end_m2": 0.0, "laps_junction_m2": 1.11,
                 "laps_band_end_m2": 0.12, "laps_doorway_m2": 0.09, "true_waste_m2": 0.48, "reusable_m2": 0.8,
                 "stock_m2": 6.2, "rolls": 2, "floor_seams": 3, "floor_end_laps": 0, "band_joints": 4, "seams": 7,
                 "band_pieces_m": [1.1, 2.0, 2.8, 2.8, 2.8], "min_joint_corner_m": 0.0, "min_joint_seam_end_m": 0.2,
                 "joints_stacked_on_seam_ends": 0, "jamb_butt_joints": 2, "terminations": 0, "corners_internal": 5,
                 "corners_external": 1, "flange_pleats_m2": 0.05, "flange_gaps_m2": 0.01, "t_flange_over_seam_end": 6,
                 "t_doorway_lap_over_seam_end": 0, "t_seam_end_at_break": 0, "best_corner_m": 0.1,
                 "best_seam_end_m": 0.2, "fold": "BLOCKED"},
    "flags": COMMON_OPEN + ["DRAIN_NOT_SHOWN", "JOINT_AT_CORNER", "LAY_ORDER_NOT_VALIDATED"],
    "boq_impact": "B 12.52 m2 / 2 rolls as V2.5; 0.80 m2 of the 1.28 m2 offcuts is a reusable rectangle (its reuse "
                  "is N-7): reused for the doorway piece the room needs 13.50 m2 instead of 13.80 m2",
}

# ------------------------------------------------------------------------------------------------------- IX-05
IX05 = {
    "id": "IX-05", "case": None, "title": "3.00 x 2.50 m bathroom with a free-standing 0.40 x 0.40 m column, one "
                                          "0.90 m door",
    "rules": RULES,
    "room": {"poly": [(0, 0), (3000, 0), (3000, 2500), (0, 2500)],
             "holes": [[(1300, 1000), (1700, 1000), (1700, 1400), (1300, 1400)]],
             "doors": [{"id": "D1", "edge": 0, "t0": 300, "t1": 1200, "depth": 200, "other_side": "DRY"}],
             "breaks": [], "pipes": [], "drains": [], "codes": ["BATHROOM"], "scope": "WET"},
    "interpretation": ["the column is an obstruction: the floor excludes it, its four faces are upturned (a closed "
                       "1.60 m loop with 4 EXTERNAL corners seen from the room)",
                       "the outer run: 10.10 m open from the east jamb of D1 (x 1.20); corners SE 1.80, NE 4.30, "
                       "NW 7.30, SW 9.80"],
    "formula": ["floor = 3.00 x 2.50 - 0.40 x 0.40; upturn = (11.00 - 0.90 + 1.60) x 0.20; continuation 0.90 x 0.20"],
    "hand": [
        "floor 7.50 - 0.16 = 7.34; upturn 11.70 x 0.20 = 2.34; continuation 0.18 -> proven subtotal 9.86 m2",
        "ALONG_X: strips 3.00 long across 2.50: n = 3 (1.00 + 2 x 0.90 = 2.80), S3 0.70 wide; S1 y 0-1.00, S2 "
        "0.90-1.90, S3 1.80-2.50; the column (y 1.00-1.40) lies in S2 only: S2 is one 3.00 m piece with the "
        "column footprint cut out (a 0.40 x 0.40 offcut)",
        "S3 is cut from a full 3.00 piece: trim 0.30 -> one lane 3.00 (no residue); DW 0.90 from it -> 2.10 left",
        "outer run: 2.10 (no lap) covers 2.10, 8.00 left; then the column loop 1.60 (every piece lapped): the "
        "shortest segment of 3 lanes that finishes both: two lanes cover 2 (L - 0.10), the third finishes the run "
        "and keeps 1.70 for the column: 3L - 8.30 >= 1.70 -> L = 3.34 (3.33 leaves 1.69)",
        "3.34 does not fit roll 1's 1.00 m tail; filling the tail first (1.00 + a 2.44 segment) gives 2 rolls but 7 "
        "joints against 4 -> 3.34 is kept",
        "band: B1 2.10, B2 3.34, B3 3.34, B4 1.62 (outer run); B5 1.70 (column loop, from the third lane's rest); "
        "0.02 m of that lane is left (0.006 m2)",
        "ALONG_Y for comparison: 4 strips 2.50 (10.00 m) + a 2.70 segment = 12.70 m2, 2 rolls, 3 + 5 = 8 seams -> "
        "ALONG_X (2 rolls, 2 + 4 = 6 seams) is selected",
        "laps: side 2 x 3.00 x 0.10 = 0.60; flange 11.70 x 0.10 = 1.17; band ends 4 x 0.03 = 0.12; doorway 0.09 -> "
        "1.98; installed 9.86 + 1.98 = 11.84",
        "consumed 3 x 3.00 + 3.34 = 12.34; offcuts 0.50 = column footprint 0.16 (0.40 x 0.40, REUSABLE_SUBJECT_TO_N7) "
        "+ segment residue 0.10 x 3.34 = 0.334 + lane rest 0.006 (TRUE_WASTE 0.34); 2 rolls (3.34 + 3.00 + 3.00 | "
        "3.00), stock 0.66 + 7.00 = 7.66 m2",
        "outer joints 2.00-2.10, 5.24-5.34, 8.48-8.58: corners 0.20, 0.94, 1.18 -> 0.20; floor seams (y 0.90-1.00, "
        "1.80-1.90) meet the east wall at r 2.70-2.80 / 3.60-3.70 and the west wall at 8.80-8.90 / 7.90-8.00 -> "
        "seam distances 0.60, 1.54, 0.22 -> 0.22",
        "column loop from (1.30, 1.00): one piece 1.70, its closing joint 1.50-1.60 ends on the corner at the loop "
        "start (0.00); the S1/S2 lap (y 0.90-1.00) runs along the column's south face under its flange (a seam "
        "along a wall, r 0-0.40): the closing joint touches it -> min joint-to-seam 0.00",
        "corners 4 internal + 4 external: flange pleats 0.04, flange gaps at the column 4 x 0.01 = 0.04 m2",
        "continuous fold: not computed (an obstruction inside the room)",
    ],
    "expected": {"direction": "X", "proven_subtotal_m2": 9.86, "consumed_m2": 12.34, "installed_m2": 11.84,
                 "laps_total_m2": 1.98, "laps_side_m2": 0.6, "laps_floor_end_m2": 0.0, "laps_junction_m2": 1.17,
                 "laps_band_end_m2": 0.12, "laps_doorway_m2": 0.09, "true_waste_m2": 0.34, "reusable_m2": 0.16,
                 "stock_m2": 7.66, "rolls": 2, "floor_seams": 2, "floor_end_laps": 0, "band_joints": 4, "seams": 6,
                 "band_pieces_m": [1.62, 1.7, 2.1, 3.34, 3.34], "min_joint_corner_m": 0.0,
                 "min_joint_seam_end_m": 0.0, "joints_stacked_on_seam_ends": 0, "jamb_butt_joints": 2,
                 "terminations": 0, "corners_internal": 4, "corners_external": 4, "flange_pleats_m2": 0.04,
                 "flange_gaps_m2": 0.04, "t_flange_over_seam_end": 4, "t_doorway_lap_over_seam_end": 0,
                 "t_seam_end_at_break": 0, "seams_along_walls": 1, "run_min_joint_corner_m": [0.2, 0.0],
                 "run_min_joint_seam_end_m": [0.22, 0.0], "fold": "BLOCKED"},
    "flags": COMMON_OPEN + ["DRAIN_NOT_SHOWN", "FLOOR_SEAM_ALONG_A_WALL", "JOINT_AT_CORNER",
                            "JOINT_TOUCHES_SEAM_END", "LAY_ORDER_NOT_VALIDATED"],
    "boq_impact": "B 11.84 m2 / 2 rolls; the column adds 1.60 m of upturn (0.32 m2) and 4 external corners whose "
                  "flange gaps (0.04 m2) need the corner detail; the column footprint is a reusable 0.40 x 0.40 offcut",
}

# ------------------------------------------------------------------------------------------------------- IX-06
IX06 = {
    "id": "IX-06", "case": None, "title": "4.00 x 3.00 m kitchen: a 0.90 m door to the dry dining, a 0.80 m service "
                                          "doorway to a waterproofed laundry, a floor drain",
    "rules": RULES,
    "room": {"poly": [(0, 0), (4000, 0), (4000, 3000), (0, 3000)],
             "doors": [{"id": "D1", "edge": 3, "t0": 1000, "t1": 1900, "depth": 200, "other_side": "DRY"},
                       {"id": "D2", "edge": 1, "t0": 500, "t1": 1300, "depth": 200, "other_side": "WATERPROOFED"}],
             "breaks": [], "holes": [], "pipes": [], "drains": [{"id": "FD1", "x": 1400, "y": 2200}],
             "codes": ["KITCHEN"], "scope": "WET"},
    "interpretation": ["D2 leads to a waterproofed laundry: the membrane runs through (DOORWAY_CONTINUATION, resolved "
                       "by geometry); D1 to a dry room: its threshold transition is UNRESOLVED",
                       "two open runs: 6.70 m from D2 (east jamb, y 1.30) over the north wall to D1 (y 2.00), corners "
                       "NE 1.70 and NW 5.70; 5.60 m from D1 (y 1.10) over the south wall to D2 (y 0.50), corners SW "
                       "1.10 and SE 5.10", "the drain FD1 is drawn at (1.40, 2.20)"],
    "formula": ["floor 4.00 x 3.00; upturn (14.00 - 0.90 - 0.80) x 0.20; continuation (0.90 + 0.80) x 0.20"],
    "hand": [
        "floor 12.00 + upturn 12.30 x 0.20 = 2.46 + continuation 0.34 -> proven subtotal 14.80 m2",
        "ALONG_Y: strips 3.00 long across 4.00: n = 5 (1.00 + 4 x 0.90 = 4.60), S5 0.40 wide; trim 0.60 -> lanes "
        "L1 L2 3.00 (no residue)",
        "DW-D1 0.90 from L1 (2.10 left); DW-D2 0.80 from the shortest lane that fits (L1's 2.10) -> 1.30 left",
        "run 1 (6.70): L2 3.00 covers 3.00; L1's 1.30 covers 1.20; 2.50 left; a new segment for 2.50 (lapped) + "
        "run 2 5.60: the first lane gives 2.60 to run 1, then 3L - 2.80 >= 5.60 -> L = 2.80 (2.79 gives 5.57)",
        "2.80 fits roll 2's 4.00 m tail; band: run 1 B1 3.00, B2 1.30, B3 2.60; run 2 B4 2.80, B5 2.80, B6 0.20",
        "ALONG_X for comparison: 4 strips 4.00 + a 2.00 roll tail + a 0.50 segment = 18.50 m2, 2 rolls, 3 + 5 = 8 "
        "seams; ALONG_Y 17.80 m2, 2 rolls, 4 + 4 = 8 seams -> ALONG_Y (less membrane at equal rolls and seams)",
        "laps: side 4 x 3.00 x 0.10 = 1.20; flange 12.30 x 0.10 = 1.23; band ends 4 x 0.03 = 0.12; doorways "
        "(0.90 + 0.80) x 0.10 = 0.17 -> 2.72; installed 17.52",
        "consumed 5 x 3.00 + 2.80 = 17.80 = 17.52 + 0.28 true waste (0.10 x 2.80); 2 rolls (3 x 3.00 | 2 x 3.00 + "
        "2.80), stock 1.00 + 1.20 = 2.20 m2; seams 8",
        "run 1 joints 2.90-3.00, 4.10-4.20: corners 1.20, 1.50; the floor seams (x 0.90-1.00 ... 3.60-3.70) meet the "
        "north wall at r 4.70-4.80, 3.80-3.90, 2.90-3.00, 2.00-2.10: the joint 2.90-3.00 lies on the S3/S4 seam "
        "end (stacked)",
        "run 2 joints 2.70-2.80, 5.40-5.50: corners 1.60, 0.30 -> min 0.30; seam ends on the south wall r 2.00-2.10, "
        "2.90-3.00, 3.80-3.90, 4.70-4.80 -> 0.10, 0.60",
        "8 seam ends under the flange, none in a doorway; 4 butt joints at the jambs (D1, D2); B6 is a 0.20 m "
        "piece (0.10 past its lap): its acceptability is P-9",
        "drain FD1 at x 1.40: 0.40 from the S1/S2 and S2/S3 laps, 0.70 from the north flange -> a centred collar up "
        "to 0.80 m; lay order from the drain strip S2: S2, S1, S3, S4, S5",
        "continuous fold: developed 4.40 x 3.40 = WP-B's: 17.60 m2, 2 rolls, 3 seams, installed 16.28",
        "junction flange: ALONG_X keeps 2 rolls while the 0.70 m trim of S4 holds two band lanes (b = 0.20 + j <= "
        "0.35, j <= 0.15: lanes 4.00 + 4.00 less the doorway pieces leave a band need that fits the two 2.00 m roll "
        "tails); from j = 0.16 the trim holds one lane and either direction needs at least 15.00 (or 16.00) m of "
        "floor + 5.50 m of segments > 20.00 m -> 3 rolls",
    ],
    "expected": {"direction": "Y", "proven_subtotal_m2": 14.8, "consumed_m2": 17.8, "installed_m2": 17.52,
                 "laps_total_m2": 2.72, "laps_side_m2": 1.2, "laps_floor_end_m2": 0.0, "laps_junction_m2": 1.23,
                 "laps_band_end_m2": 0.12, "laps_doorway_m2": 0.17, "true_waste_m2": 0.28, "reusable_m2": 0.0,
                 "stock_m2": 2.2, "rolls": 2, "floor_seams": 4, "floor_end_laps": 0, "band_joints": 4, "seams": 8,
                 "band_pieces_m": [0.2, 1.3, 2.6, 2.8, 2.8, 3.0], "min_joint_corner_m": 0.3,
                 "min_joint_seam_end_m": 0.0, "joints_stacked_on_seam_ends": 1, "jamb_butt_joints": 4,
                 "terminations": 0, "corners_internal": 4, "corners_external": 0, "flange_pleats_m2": 0.04,
                 "flange_gaps_m2": 0.0, "t_flange_over_seam_end": 8, "t_doorway_lap_over_seam_end": 0,
                 "t_seam_end_at_break": 0, "drain_FD1_clear_m": 0.4, "drain_FD1_on_seam": False,
                 "lay_order": [2, 1, 3, 4, 5], "shortest_band_piece_m": 0.2, "junction_rolls": [2, 3],
                 "junction_roll_change_flange_m": 0.16,
                 "fold": {"rolls": 2, "consumed_m2": 17.6, "installed_m2": 16.28, "laps_m2": 1.32,
                          "corner_excess_m2": 0.16, "seams": 3}},
    "flags": COMMON_OPEN + ["JOINT_ON_SEAM_END", "JUNCTION_CHANGES_ROLL_COUNT"],
    "boq_impact": "B 17.52 m2 / 2 rolls; the service doorway carries no threshold transition (continuation), the "
                  "dining door does (withheld); the drawn drain fixes the lay order",
}

# ------------------------------------------------------------------------------------------------------- IX-07
IX07 = {
    "id": "IX-07", "case": None, "title": "4.00 x 1.50 m balcony: a 1.80 m door, the front edge open (railing)",
    "rules": RULES,
    "room": {"poly": [(0, 0), (4000, 0), (4000, 1500), (0, 1500)],
             "doors": [{"id": "D1", "edge": 2, "t0": 1100, "t1": 2900, "depth": 200, "other_side": "DRY"}],
             "breaks": [{"id": "E1", "edge": 0, "t0": 0, "t1": 4000, "kind": "OPEN_EDGE"}], "holes": [],
             "pipes": [], "drains": [], "codes": ["BALCONY"], "scope": "EXTERIOR"},
    "interpretation": ["the front edge (y = 0) has no wall: no upturn, the membrane edge needs a termination detail "
                       "(4.00 m)", "two open runs of 2.60 m: from the open edge up the east wall (corner NE 1.50) to "
                       "the door; from the door over the north wall (corner NW 1.10) down the west wall to the open "
                       "edge", "the corners at the open edge are upturn ends, not corners", "no drain drawn"],
    "formula": ["floor 4.00 x 1.50; upturn (11.00 - 4.00 - 1.80) x 0.20; continuation 1.80 x 0.20"],
    "hand": [
        "floor 6.00 + upturn 5.20 x 0.20 = 1.04 + continuation 0.36 -> proven subtotal 7.40 m2",
        "ALONG_X: strips 4.00 across 1.50: n = 2, S2 0.60 wide; trim 0.40 -> 1 lane 4.00 + 0.10 x 4.00 residue",
        "DW 1.80 from the lane -> 2.20 left; run 1 (2.60): 2.20 covers 2.20, 0.40 left; then run 2 (2.60): a "
        "segment whose first lane finishes run 1 (0.50 used) and whose lanes cover run 2: 3L - 0.70 >= 2.60 -> "
        "L = 1.10 (1.09 gives 2.57); it fits the 2.00 m roll tail",
        "band: run 1 B1 2.20, B2 0.50; run 2 B3 1.10, B4 1.10, B5 0.60",
        "ALONG_Y for comparison: 5 strips 1.50 + a 1.80 doorway segment = 9.30 m2, 1 roll, 4 + 2 = 6 seams -> "
        "ALONG_X (1 roll, 1 + 3 = 4 seams)",
        "laps: side 4.00 x 0.10 = 0.40; flange 5.20 x 0.10 = 0.52; band ends 3 x 0.03 = 0.09; doorway 1.80 x 0.10 "
        "= 0.18 -> 1.19; installed 8.59",
        "consumed 2 x 4.00 + 1.10 = 9.10 = 8.59 + 0.51 true waste (0.40 + 0.11); 1 roll, stock 0.90 m2; seams 4",
        "run 1 joint 2.10-2.20: 0.60 from the corner NE (1.50), 1.10 from the seam end (east wall, r 0.90-1.00)",
        "run 2 joints 1.00-1.10 and 2.00-2.10: the first ends on the corner NW (1.10) -> 0.00; seam end on the west "
        "wall at r 1.60-1.70 -> 0.50 and 0.30",
        "2 corners (both internal); 2 seam ends under the flange; 2 butt joints (D1) and 2 terminations at the open "
        "edge (the band ends there); the open edge itself: 4.00 m of termination",
        "continuous fold: not computed (the open edge has no wall to fold onto)",
    ],
    "expected": {"direction": "X", "proven_subtotal_m2": 7.4, "consumed_m2": 9.1, "installed_m2": 8.59,
                 "laps_total_m2": 1.19, "laps_side_m2": 0.4, "laps_floor_end_m2": 0.0, "laps_junction_m2": 0.52,
                 "laps_band_end_m2": 0.09, "laps_doorway_m2": 0.18, "true_waste_m2": 0.51, "reusable_m2": 0.0,
                 "stock_m2": 0.9, "rolls": 1, "floor_seams": 1, "floor_end_laps": 0, "band_joints": 3, "seams": 4,
                 "band_pieces_m": [0.5, 0.6, 1.1, 1.1, 2.2], "min_joint_corner_m": 0.0, "min_joint_seam_end_m": 0.3,
                 "joints_stacked_on_seam_ends": 0, "jamb_butt_joints": 2, "terminations": 2, "corners_internal": 2,
                 "corners_external": 0, "flange_pleats_m2": 0.02, "flange_gaps_m2": 0.0, "t_flange_over_seam_end": 2,
                 "t_doorway_lap_over_seam_end": 0, "t_seam_end_at_break": 0, "fold": "BLOCKED"},
    "flags": COMMON_OPEN + ["DRAIN_NOT_SHOWN", "JOINT_AT_CORNER", "LAY_ORDER_NOT_VALIDATED"],
    "boq_impact": "B 8.59 m2 / 1 roll (exterior system); the 4.00 m open-edge termination and the door threshold "
                  "stay withheld; a balcony without a drawn drain is NOT_SHOWN, never zero",
}

# ------------------------------------------------------------------------------------------------------- IX-08
IX08 = {
    "id": "IX-08", "case": "WP_F", "title": "12.00 x 6.00 m roof: parapets, an access door, a 2.00 m open edge, "
                                            "two roof drains",
    "rules": RULES,
    "room": {"poly": [(0, 0), (12000, 0), (12000, 6000), (0, 6000)],
             "doors": [{"id": "D1", "edge": 2, "t0": 6000, "t1": 7000, "depth": 200, "other_side": "DRY"}],
             "breaks": [{"id": "E1", "edge": 1, "t0": 2000, "t1": 4000, "kind": "OPEN_EDGE"}], "holes": [],
             "pipes": [], "drains": [{"id": "RD1", "x": 2000, "y": 1000}, {"id": "RD2", "x": 10000, "y": 1000}],
             "codes": ["ROOF"], "scope": "EXTERIOR"},
    "interpretation": ["parapet walls carry the upturn; the open edge E1 (east, y 2.00-4.00) and the door D1 (north, "
                       "x 5.00-6.00) break it into runs of 8.00 m and 25.00 m",
                       "the strips are 12.00 m long - longer than a roll - so each is spliced 10.00 + 2.10"],
    "formula": ["as the Phase 2B-3 proof case WP-F; spliced strips laid with end laps"],
    "hand": [
        "proven subtotal 72.00 + 6.60 + 0.20 = 78.80 m2; 7 strips ALONG_X, each spliced at x 9.90-10.00",
        "consumed 92.14 = installed 90.18 + 1.96 true waste; 10 rolls, stock 7.86 m2; seams 6 + 7 + 4 = 17",
        "laps: side 7.20; end 0.66; flange 3.30; band ends 0.12; doorway 0.10 -> 11.38",
        "run 1 (8.00): one piece; run 2 (25.00): B 2.00, 1.10, 7.44, 7.44, 7.42: joints 1.90-2.00, 2.90-3.00, "
        "10.24-10.34, 17.58-17.68: corners 3.00, 2.00, 0.66, 5.32 -> 0.66; the west-wall seam end at 10.00-10.10 is "
        "0.14 from the third joint",
        "12 seam ends under the flange (10 side laps on the east and west parapets, 2 end laps on the south and "
        "north); 2 side laps end at the open edge",
        "every strip is spliced at the same place: the end laps of neighbouring strips are not staggered (0.00) - "
        "12 four-layer crossings",
        "both drains (y 1.00) sit on the S1/S2 lap (y 0.90-1.00); RD2 also on the splice line: 0.00 clear",
        "two drains: the catchments are not drawn, no lay order is derived; continuous fold: not computed (open edge)",
    ],
    "expected": {"direction": "X", "proven_subtotal_m2": 78.8, "consumed_m2": 92.14, "installed_m2": 90.18,
                 "laps_total_m2": 11.38, "laps_side_m2": 7.2, "laps_floor_end_m2": 0.66, "laps_junction_m2": 3.3,
                 "laps_band_end_m2": 0.12, "laps_doorway_m2": 0.1, "true_waste_m2": 1.96, "reusable_m2": 0.0,
                 "stock_m2": 7.86, "rolls": 10, "floor_seams": 6, "floor_end_laps": 7, "band_joints": 4, "seams": 17,
                 "band_pieces_m": [1.1, 2.0, 7.42, 7.44, 7.44, 8.0], "min_joint_corner_m": 0.66,
                 "min_joint_seam_end_m": 0.14, "joints_stacked_on_seam_ends": 0, "jamb_butt_joints": 2,
                 "terminations": 2, "corners_internal": 4, "corners_external": 0, "flange_pleats_m2": 0.04,
                 "flange_gaps_m2": 0.0, "t_flange_over_seam_end": 12, "t_doorway_lap_over_seam_end": 0,
                 "t_seam_end_at_break": 2, "min_end_lap_stagger_m": 0.0, "drain_RD1_clear_m": 0.0,
                 "drain_RD1_on_seam": True, "drain_RD2_clear_m": 0.0, "drain_RD2_on_seam": True, "fold": "BLOCKED"},
    "flags": COMMON_OPEN + ["DRAIN_ON_A_FLOOR_SEAM", "END_LAPS_NOT_STAGGERED", "LAY_ORDER_NOT_VALIDATED"],
    "boq_impact": "B 90.18 m2 / 10 rolls as V2.5; two installation defects of the plan are now visible (drains on a "
                  "lap, end laps in one line) - correcting them is a lay-out change with a possible material effect "
                  "(staggering the splices of a 12 m strip needs another cut pattern)",
}

# ------------------------------------------------------------------------------------------------------- IX-09
WP_W_ROOM = {"poly": [(0, 0), (1500, 0), (1500, 1200), (0, 1200)],
             "doors": [{"id": "D1", "edge": 0, "t0": 350, "t1": 1150, "depth": 200, "other_side": "DRY"}],
             "breaks": [], "holes": [], "pipes": [], "drains": [], "codes": ["BATHROOM"], "scope": "WET"}
IX09 = {
    "id": "IX-09", "case": None, "title": "Shared roll inventory: the 4 x 3 m bathroom, a 1.50 x 1.20 m WC and the "
                                          "2 x 2 m bathroom on one floor, one membrane system",
    "rules": RULES + ["UP-WP-MAT-001 C: whole rolls of the cutting plan per membrane system"],
    "areas": {"IX-02": "IX-02", "WC": WP_W_ROOM, "IX-01": "IX-01"},
    "interpretation": ["only full-width cuts are shared between areas (a roll remainder cut to a piece's length); "
                       "band lanes, trims and offcuts stay with their area"],
    "formula": ["fewest whole rolls for the multiset of cut lengths (exact packing)"],
    "hand": [
        "cuts: bathroom 3.00 x 5 + 2.80; WC 1.20 + 1.20 + 1.50 (Phase 2B-3 WP-W); 2 x 2 bathroom 2.00 x 3 + 1.50",
        "each alone: 2 + 1 + 1 = 4 rolls",
        "together 15.00 + 2.80 + 3.90 + 7.50 = 29.20 m -> at least 3 rolls; 3 is reached: 3.00 + 3.00 + 2.00 + 2.00 = "
        "10.00; 3.00 + 3.00 + 2.80 + 1.20 = 10.00; 3.00 + 2.00 + 1.50 + 1.50 + 1.20 = 9.20",
        "gross 30.00 m2 = consumed 29.20 + untouched 0.80; one roll saved by sharing, none carried between floors",
    ],
    "expected": {"rolls_alone": 4, "rolls_shared": 3, "consumed_m2": 29.2, "gross_m2": 30.0, "untouched_m2": 0.8,
                 "pieces": 13},
    "flags": [],
    "boq_impact": "procurement C: 3 rolls instead of 4 (the BOQ quantities A and B are unchanged)",
}

# ------------------------------------------------------------------------------------------------------- IX-10
WP_G_ROOM = {"poly": [(0, 0), (4000, 0), (4000, 1500), (0, 1500)],
             "doors": [{"id": "D1", "edge": 2, "t0": 1100, "t1": 2900, "depth": 200, "other_side": "DRY"}],
             "breaks": [], "holes": [], "pipes": [], "drains": [], "codes": ["BALCONY"], "scope": "EXTERIOR"}
IX10 = {
    "id": "IX-10", "case": None, "title": "Two separate membrane systems: the 4 x 3 m bathroom (wet-area system) and "
                                          "a 4.00 x 1.50 m balcony (exterior system)",
    "rules": RULES + ["UP-WP-MAT-001: never a roll or a total across membrane systems"],
    "areas": {"IX-02": "IX-02", "BALCONY": WP_G_ROOM},
    "interpretation": ["different systems never share a roll, even where a remainder would fit"],
    "formula": ["fewest whole rolls per system"],
    "hand": [
        "bathroom cuts 3.00 x 5 + 2.80 = 17.80 -> 2 rolls; balcony (Phase 2B-3 WP-G) 4.00 + 4.00 + 2.44 = 10.44 -> "
        "2 rolls; 4 rolls in all",
        "if the systems were mixed, 28.24 m would fit 3 rolls (4.00 + 3.00 + 3.00; 4.00 + 3.00 + 2.80; 3.00 + 3.00 + "
        "2.44) - the system boundary costs one roll and is kept",
    ],
    "expected": {"systems": 2, "rolls_by_scope": {"WET": 2, "EXTERIOR": 2}, "rolls_total": 4,
                 "rolls_if_mixed": 3},
    "flags": [],
    "boq_impact": "procurement C per system: 2 + 2 rolls, never 3 combined; no total across systems",
}

EXAMPLES = [IX01, IX02, IX03, IX04, IX05, IX06, IX07, IX08, IX09, IX10]
SINGLE = [IX01, IX02, IX03, IX04, IX05, IX06, IX07, IX08]
BY_ID = {x["id"]: x for x in EXAMPLES}
