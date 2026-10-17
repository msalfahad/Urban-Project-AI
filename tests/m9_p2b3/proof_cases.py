"""PROOF CASES - Phase 2B-3 (ARCH_TAKEOFF_V2.5) engineering calculation proof library: the waterproofing cases.

Each case is a simple dimensioned scenario with (1) its geometry, (2) the Urban rules it applies, (3) the project
overrides, (4) an independent hand calculation written out step by step, (5) the expected quantities as LITERALS
typed from that hand calculation, (9) the coordinate explanation and (10) the exclusions and why. (6) - (8), the engine
quantities, the difference and PASS / FAIL, are produced by proof_engine.compare() at test / report time.

Rules for this file: no expected value is computed here (test_p2b3_independence checks that every expected value is a
literal number, string, boolean or None); nothing here imports the engine. Coordinates in metres, x east, y north, the
room's south-west inner corner at the origin; the wall is 0.20 m thick wherever a doorway piece needs its depth (a
synthetic assumption stated in each case). Urban values used (registry 1.1.0, owner approved): roll 1.00 x 10.00 m
(UP-WP-001), lap 0.10 m at every joint (UP-WP-002), upturn 0.20 m on eligible boundaries (UP-WP-003), doorway
continuation = door width x wall depth (UP-WP-DOOR-001), the three quantities A / B / C kept apart (UP-WP-MAT-001), the
layout selection fewest rolls -> fewest seams -> least membrane -> direction order (UP-WP-LAY-001).

Terms used in the sheets:
    strip       a floor piece cut across the full roll width (1.00 m); strips lap 0.10 m side by side
    band        the upturn: 0.20 m up the wall + 0.10 m lapped onto the floor membrane = 0.30 m wide
    lane        a 0.30 m band strip cut along a roll; a full-width segment gives 3 lanes (0.90 m) + 0.10 m residue
    joint       a band piece lapping 0.10 m onto the piece before it (every piece after the first of an open run;
                every piece of a closed loop)
    consumed    roll length cut x 1.00 m;  cutting waste = consumed - installed (laid) membrane
"""

URBAN = {"roll_w_m": 1.0, "roll_l_m": 10.0, "lap_m": 0.1, "upturn_h_m": 0.2, "band_w_m": 0.3, "lanes_per_width": 3}
URBAN_RULES = ["UP-WP-001 roll 1.00 x 10.00 m", "UP-WP-002 lap 0.10 m (side, end, band, doorway)",
               "UP-WP-003 upturn 0.20 m on WALL / COLUMN / WINDOW_THRESHOLD boundaries",
               "UP-WP-DOOR-001 doorway continuation = door width x wall depth; threshold transition by detail",
               "UP-WP-004 penetrations and corners counted, treatment by detail",
               "UP-WP-MAT-001 A net / B installed / C rolls", "UP-WP-LAY-001 layout selection and cutting plan"]
STRIP_RULE = ("strips across a cross width D: the smallest n with 1.00 + (n - 1) x 0.90 >= D (each further strip adds "
              "0.90 m because it laps 0.10 m onto the last); the last strip is cut down lengthwise to "
              "D - (n - 1) x 0.90")

# ---------------------------------------------------------------------------------------------------------- WP-B
# WP-2 of the program: the 3.00 x 4.00 m bathroom, demonstrated first.
WP_B = {
    "id": "WP-B", "sequence": 2, "kind": "POSITIVE", "title": "Bathroom 4.00 x 3.00 m with one 1.00 m door",
    "proves": ["UP-WP-001", "UP-WP-002", "UP-WP-003", "UP-WP-DOOR-001", "UP-WP-MAT-001", "UP-WP-LAY-001"],
    "scenario": {
        "ring": [(0.0, 0.0), (4.0, 0.0), (4.0, 3.0), (0.0, 3.0)], "codes": ["BATHROOM"], "scope": "WET",
        "doors": [{"id": "D1", "edge": 0, "t0": 1.5, "t1": 2.5, "width_m": 1.0, "depth_m": 0.2, "other_side": "DRY"}],
        "inserts": [], "texts": [], "rules": []},
    "coordinates": "inner faces x 0..4.00, y 0..3.00 (12.00 m2); the door D1 in the south wall (y = 0) from x 1.50 to "
                   "2.50, leading to a dry corridor; no column, drain or pipe",
    "overrides": [],
    "assumptions": ["wall thickness at the door 0.20 m (not stated by the scenario; needed for the doorway "
                    "continuation piece only)", "no membrane system named: the Urban standard roll"],
    "hand": [
        "A  net floor = 4.00 x 3.00 = 12.00 m2",
        "perimeter = 2 x (4.00 + 3.00) = 14.00 m; the door 1.00 m is a doorway, not a wall (UP-WP-003)",
        "eligible upturn length = 14.00 - 1.00 = 13.00 m (one open run, jamb to jamb)",
        "wall upturn = 13.00 x 0.20 = 2.60 m2",
        "proven geometric subtotal A + upturn = 12.00 + 2.60 = 14.60 m2 (not a material requirement)",
        "doorway continuation (UP-WP-DOOR-001) = 1.00 x 0.20 = 0.20 m2 -> proven subtotal incl. continuation 14.80 m2",
        "-- layout 1: strips 3.00 m long (ALONG_Y), laid across the 4.00 m width --",
        "strips: 1.00 + 3 x 0.90 = 3.70 < 4.00, 1.00 + 4 x 0.90 = 4.60 >= 4.00 -> n = 5; the last strip is "
        "4.00 - 4 x 0.90 = 0.40 m wide",
        "strip x-ranges: S1 0.00-1.00, S2 0.90-1.90, S3 1.80-2.80, S4 2.70-3.70, S5 3.60-4.00 (each 3.00 m long)",
        "floor cuts 5 x 3.00 m = 15.00 m of roll; floor laid = (4 x 1.00 + 0.40) x 3.00 = 13.20 m2",
        "side laps = 4 seams x 3.00 m x 0.10 m = 1.20 m2 (13.20 - 12.00)",
        "offcut: S5 is cut from a full-width 3.00 m piece -> trim 0.60 x 3.00 m -> 2 lanes 0.30 x 3.00 m "
        "(0.60 / 0.30 = 2, no residue)",
        "doorway piece 1.00 x (0.20 + 0.10 lap onto the floor) = 1.00 x 0.30 m, cut from a 3.00 m lane -> 2.00 m left",
        "lane pool for the band: 3.00 m and 2.00 m",
        "band run 13.00 m (open): piece 1 = 3.00 lane, no lap, covers 3.00; piece 2 = 2.00 lane, laps 0.10, covers "
        "1.90; covered 4.90, left 8.10 m",
        "new band segment: 3 lanes, each piece laps 0.10: 3 x (L - 0.10) >= 8.10 -> L >= 2.80 m; cut 2.80 m "
        "(2.79 m would cover 3 x 2.69 = 8.07 < 8.10)",
        "band pieces 3.00 + 2.00 + 2.80 + 2.80 + 2.80 = 13.40 m = 13.00 + 4 joints x 0.10",
        "band laid 0.30 x 13.40 = 4.02 m2 = upturn 2.60 + band-to-floor lap 13.00 x 0.10 = 1.30 + end laps "
        "4 x 0.30 x 0.10 = 0.12",
        "laps total = 1.20 (side) + 1.30 (band to floor) + 0.12 (band joints) + 0.10 (doorway piece to floor, "
        "1.00 x 0.10) = 2.72 m2",
        "B installed = 12.00 + 2.60 + 0.20 + 2.72 = 17.52 m2 (= laid 13.20 + 0.30 + 4.02)",
        "cut inventory: 3.00, 3.00, 3.00, 3.00, 3.00 (floor), 2.80 (band segment) = 17.80 m -> consumed 17.80 m2",
        "rolls: 17.80 m > 10.00 m -> at least 2; roll 1: S1 S2 S3 = 9.00 m (1.00 m untouched); roll 2: S4 S5 + "
        "band 2.80 = 8.80 m (1.20 m untouched) -> 2 rolls",
        "cutting waste = 17.80 - 17.52 = 0.28 m2 (the 0.10 x 2.80 m residue of the band segment); untouched roll "
        "remainders 2.20 m2 are stock, not waste",
        "-- layout 2: strips 4.00 m long (ALONG_X), across the 3.00 m width --",
        "three strips cover only 1.00 + 0.90 + 0.90 = 2.80 < 3.00 -> n = 4, the last 3.00 - 3 x 0.90 = 0.30 m wide",
        "floor cuts 4 x 4.00 = 16.00 m; trim 0.70 x 4.00 -> 2 lanes 4.00 m + 0.10 x 4.00 residue (0.40 m2 scrap)",
        "doorway piece from a 4.00 lane (3.00 left); band: 4.00 (covers 4.00) + 3.00 (covers 2.90), left 6.10 m",
        "a single new segment 3 x (L - 0.10) >= 6.10 -> 2.14 m does not fit the 2.00 m remainders of rolls 1 and 2 "
        "(4.00 + 4.00 each) -> 3 rolls; filling the 2.00 m remainder of roll 1 first (3 lanes x 1.90 = 5.70) leaves "
        "0.40 m, finished by a 0.40 m segment in roll 2 (lane 1 covers 0.30, lane 2 is cut 0.20 = 0.10 + lap) -> "
        "2 rolls, 18.40 m, 6 band joints",
        "selection (UP-WP-LAY-001): both 2 rolls; seams layout 1 = 4 strip seams + 4 band joints = 8, layout 2 = 3 + 6 "
        "= 9 -> layout 1 (ALONG_Y)",
        "-- what the material requirement does NOT include --",
        "doorway threshold transition: no detail -> UNRESOLVED; alternatives UPTURN_ACROSS_THRESHOLD 1.00 x 0.20 = "
        "0.20 m2, CONTINUATION_TERMINATED 0 m2 + 1.00 m termination, JAMB_RETURNS 2 x 0.20 x 0.20 = 0.08 m2 + "
        "1.00 m termination -> range 0.00 - 0.20 m2",
        "if the threshold were upturned the band would be a closed 14.00 m loop: pieces 3.00 + 2.00 lapped (4.80), "
        "segment 3 x (L - 0.10) >= 9.20 -> 3.17 m; roll 2 = 6.00 + 3.17 = 9.17 m -> still 2 rolls",
        "4 internal corners: treatment withheld (no corner detail); penetrations: none drawn -> NOT_SHOWN (never 0)",
        "final material requirement: PROVISIONAL (doorway detail, corner treatment, membrane system open); the "
        "2-roll count holds for every doorway alternative",
    ],
    "expected": {
        "A_net_m2": 12.0, "perimeter_m": 14.0, "eligible_m": 13.0, "upturn_m2": 2.6, "doorway_continuation_m2": 0.2,
        "proven_subtotal_m2": 14.8, "direction": "ALONG_Y", "floor_strips": 5, "last_strip_w_m": 0.4,
        "band_pieces_m": [2.0, 2.8, 2.8, 2.8, 3.0], "band_joints": 4, "laps_m2": 2.72, "B_m2": 17.52,
        "consumed_m2": 17.8, "waste_m2": 0.28, "rolls": 2,
        "cuts_m": [3.0, 3.0, 3.0, 3.0, 3.0, 2.8], "untouched_m2": 2.2,
        "alt_rolls": 2, "alt_seams": 9, "alt_consumed_m2": 18.4,
        "doorway_transition": "UNRESOLVED", "transition_range_m2": [0.0, 0.2],
        "rolls_if_threshold_upturned": 2, "corners_internal": 4, "corners_external": 0, "corner_state": "WITHHELD",
        "penetrations": "NOT_SHOWN", "final_material_state": "PROVISIONAL_DETAILS_OPEN"},
    "reference": {"poly_mm": [(0, 0), (4000, 0), (4000, 3000), (0, 3000)], "runs_mm": [(13000, False)],
                  "doorways_mm": [(1000, 200)], "along": "Y", "alt_along": "X", "alt_split_mm": [2000, 400]},
    "exclusions": ["the doorway threshold transition (no detail: UNRESOLVED, range 0.00 - 0.20 m2)",
                   "corner treatment (4 internal corners; no detail, no size)",
                   "penetration treatment (none drawn: the count is not established)",
                   "falls, screed and lap shingling towards a drain (no drain or fall plan)"],
}

# ---------------------------------------------------------------------------------------------------------- WP-A
WP_A = {
    "id": "WP-A", "sequence": 1, "kind": "POSITIVE", "title": "Bathroom 2.00 x 2.00 m, closed (no doorway)",
    "proves": ["UP-WP-001", "UP-WP-002", "UP-WP-003", "UP-WP-MAT-001", "UP-WP-LAY-001"],
    "scenario": {"ring": [(0.0, 0.0), (2.0, 0.0), (2.0, 2.0), (0.0, 2.0)], "codes": ["BATHROOM"], "scope": "WET",
                 "doors": [], "inserts": [], "texts": [], "rules": []},
    "coordinates": "inner faces x 0..2.00, y 0..2.00; walls on all four sides (the simplest closed band loop)",
    "overrides": [], "assumptions": ["no membrane system named: the Urban standard roll"],
    "hand": [
        "A = 2.00 x 2.00 = 4.00 m2; perimeter 8.00 m, all wall -> eligible 8.00 m, one closed loop",
        "upturn = 8.00 x 0.20 = 1.60 m2; proven subtotal 5.60 m2",
        "strips: 1.00 + 0.90 = 1.90 < 2.00 -> n = 3, the last 2.00 - 2 x 0.90 = 0.20 m wide (either direction: "
        "square)",
        "floor cuts 3 x 2.00 = 6.00 m; laid (2 x 1.00 + 0.20) x 2.00 = 4.40 m2; side laps 2 x 2.00 x 0.10 = 0.40 m2",
        "trim 0.80 x 2.00 -> 2 lanes 2.00 m + 0.20 x 2.00 residue (0.40 m2 scrap)",
        "closed loop: every piece laps 0.10 (also the closure); lanes 2.00 + 2.00 cover 1.90 + 1.90 = 3.80, left "
        "4.20 m",
        "segment 3 x (L - 0.10) >= 4.20 -> L = 1.50 m exactly; pieces 2.00 + 2.00 + 1.50 x 3 = 8.50 m = 8.00 + 5 x 0.10",
        "band laid 0.30 x 8.50 = 2.55 m2; laps 0.40 + 0.80 (8.00 x 0.10) + 0.15 (5 x 0.03) = 1.35 m2",
        "B = 4.00 + 1.60 + 1.35 = 6.95 m2; cuts 2.00 x 3 + 1.50 = 7.50 m -> consumed 7.50 m2, 1 roll (2.50 m left)",
        "waste = 7.50 - 6.95 = 0.55 m2 (0.40 floor trim residue + 0.10 x 1.50 segment residue)",
        "both directions give the same plan: tie -> ALONG_X (direction order)",
        "not included: 4 internal corners (no detail); penetrations not drawn",
    ],
    "expected": {"A_net_m2": 4.0, "perimeter_m": 8.0, "eligible_m": 8.0, "upturn_m2": 1.6,
                 "doorway_continuation_m2": 0.0, "proven_subtotal_m2": 5.6, "direction": "ALONG_X", "floor_strips": 3,
                 "last_strip_w_m": 0.2, "band_pieces_m": [1.5, 1.5, 1.5, 2.0, 2.0], "band_joints": 5,
                 "laps_m2": 1.35, "B_m2": 6.95, "consumed_m2": 7.5, "waste_m2": 0.55, "rolls": 1,
                 "cuts_m": [2.0, 2.0, 2.0, 1.5], "untouched_m2": 2.5, "doorway_transition": None,
                 "corners_internal": 4, "corners_external": 0, "corner_state": "WITHHELD", "penetrations": "NOT_SHOWN",
                 "final_material_state": "PROVISIONAL_DETAILS_OPEN"},
    "reference": {"poly_mm": [(0, 0), (2000, 0), (2000, 2000), (0, 2000)], "runs_mm": [(8000, True)],
                  "doorways_mm": [], "along": "X"},
    "exclusions": ["corner treatment (4 internal corners)", "penetrations (none drawn)"],
}

# ---------------------------------------------------------------------------------------------------------- WP-S
WP_S = {
    "id": "WP-S", "sequence": 3, "kind": "BOUNDARY", "title": "Strip count boundary: 4.00 x 2.80 m, closed",
    "proves": ["UP-WP-002", "UP-WP-003", "UP-WP-LAY-001"],
    "scenario": {"ring": [(0.0, 0.0), (4.0, 0.0), (4.0, 2.8), (0.0, 2.8)], "codes": ["BATHROOM"], "scope": "WET",
                 "doors": [], "inserts": [], "texts": [], "rules": []},
    "coordinates": "inner faces x 0..4.00, y 0..2.80: three strips reach exactly 1.00 + 2 x 0.90 = 2.80 m",
    "overrides": [], "assumptions": [],
    "hand": [
        "A = 4.00 x 2.80 = 11.20 m2; perimeter 13.60 m, closed loop; upturn 13.60 x 0.20 = 2.72 m2",
        "strips 4.00 m long across 2.80: 1.00 + 2 x 0.90 = 2.80 exactly -> n = 3, the last strip full width (no trim, "
        "no lane offcut)",
        "floor cuts 3 x 4.00 = 12.00 m; laid 2.80 x 4.00 + 2 x 4.00 x 0.10 = 11.20 + 0.80 = 12.00 m2",
        "no offcut lane: the band comes from a new segment; closed loop 13.60 m, every piece laps -> 3 x (L - 0.10) "
        ">= 13.60 -> L = 4.64 m (4.63 gives 3 x 4.53 = 13.59 < 13.60)",
        "lanes 1 and 2 cover 4.54 each (9.08); lane 3 is cut to the last 4.52 + 0.10 lap = 4.62 m (0.02 m left) -> "
        "pieces 4.64 + 4.64 + 4.62 = 13.90 m = 13.60 + 3 joints x 0.10",
        "band laid 0.30 x 13.90 = 4.17 m2; laps 0.80 + 1.36 + 0.09 = 2.25 m2; B = 11.20 + 2.72 + 2.25 = 16.17 m2",
        "cuts 4.00 x 3 + 4.64 = 16.64 m -> 2 rolls (roll 1: 4.00 + 4.00; roll 2: 4.00 + 4.64)",
        "waste = 16.64 - 16.17 = 0.47 m2 (0.10 x 4.64 segment residue 0.464 + 0.02 x 0.30 unused lane 0.006)",
        "strips 2.80 m long across 4.00 (ALONG_Y): n = 5 (1.00 + 4 x 0.90 = 4.60), last 0.40 m: trim 0.60 -> 2 lanes "
        "2.80 m; band 2.70 + 2.70 (both lapped) = 5.40, left 8.20 -> 3 x (L - 0.10) >= 8.20 -> segment 2.84 m; cuts "
        "5 x 2.80 + 2.84 = 16.84 m, 2 rolls; seams 4 + 5 = 9 vs ALONG_X 2 + 3 = 5 -> ALONG_X",
    ],
    "expected": {"A_net_m2": 11.2, "perimeter_m": 13.6, "eligible_m": 13.6, "upturn_m2": 2.72,
                 "doorway_continuation_m2": 0.0, "proven_subtotal_m2": 13.92, "direction": "ALONG_X",
                 "floor_strips": 3, "last_strip_w_m": 1.0, "band_pieces_m": [4.62, 4.64, 4.64], "band_joints": 3,
                 "laps_m2": 2.25, "B_m2": 16.17, "consumed_m2": 16.64, "waste_m2": 0.47, "rolls": 2,
                 "cuts_m": [4.64, 4.0, 4.0, 4.0], "untouched_m2": 3.36, "doorway_transition": None,
                 "corners_internal": 4, "corners_external": 0, "corner_state": "WITHHELD", "penetrations": "NOT_SHOWN",
                 "final_material_state": "PROVISIONAL_DETAILS_OPEN"},
    "reference": {"poly_mm": [(0, 0), (4000, 0), (4000, 2800), (0, 2800)], "runs_mm": [(13600, True)],
                  "doorways_mm": [], "along": "X"},
    "exclusions": ["corner treatment", "penetrations"],
}

# ---------------------------------------------------------------------------------------------------------- WP-C
WP_C = {
    "id": "WP-C", "sequence": 4, "kind": "POSITIVE", "title": "Bathroom 4.00 x 3.00 m, one door and a floor drain",
    "proves": ["UP-WP-004", "UP-WP-MAT-001"],
    "scenario": dict(WP_B["scenario"], inserts=[{"id": "FD1", "name": "FLOOR DRAIN", "x": 2.0, "y": 1.5}]),
    "coordinates": "WP-B with a FLOOR DRAIN block at (2.00, 1.50)",
    "overrides": [], "assumptions": WP_B["assumptions"],
    "hand": [
        "geometry, layout and rolls exactly as WP-B (a drain changes no strip, band or lap)",
        "penetrations: 1 drawn (FLOOR_DRAIN) -> counted 1; its collar / patch has no detail -> withheld, named",
        "B, consumed and rolls stay 17.52 / 17.80 m2 / 2: the drain treatment is NOT in them and is listed as open",
    ],
    "expected": {
        "A_net_m2": 12.0, "perimeter_m": 14.0, "eligible_m": 13.0, "upturn_m2": 2.6, "doorway_continuation_m2": 0.2,
        "proven_subtotal_m2": 14.8, "direction": "ALONG_Y", "floor_strips": 5, "last_strip_w_m": 0.4,
        "band_pieces_m": [2.0, 2.8, 2.8, 2.8, 3.0], "band_joints": 4, "laps_m2": 2.72, "B_m2": 17.52,
        "consumed_m2": 17.8, "waste_m2": 0.28, "rolls": 2, "cuts_m": [3.0, 3.0, 3.0, 3.0, 3.0, 2.8],
        "doorway_transition": "UNRESOLVED", "transition_range_m2": [0.0, 0.2], "corners_internal": 4,
        "corners_external": 0, "corner_state": "WITHHELD", "penetrations": "COUNTED", "penetration_count": 1,
        "penetration_treatment": "WITHHELD", "final_material_state": "PROVISIONAL_DETAILS_OPEN"},
    "reference": WP_B["reference"],
    "exclusions": WP_B["exclusions"][:2] + ["the drain collar / patch (1 drain, no detail)"],
}

WP_CX = {
    "id": "WP-CX", "sequence": 5, "kind": "EXCEPTION",
    "title": "WP-C with a project drain detail: one 0.50 x 0.50 m membrane patch",
    "proves": ["UP-WP-004", "UP-WP-MAT-001", "UP-WP-LAY-001", "UP-RULES-001"],
    "scenario": dict(WP_C["scenario"], rules=[{"id": "PR-1", "rule_id": "UP-WP-004",
                                               "parameter": "penetration_treatment",
                                               "value": {"kind": "PATCH", "size_m": [0.5, 0.5]},
                                               "scope": {"kind": "PROJECT"},
                                               "source": {"kind": "DETAIL", "ref": "synthetic detail WP-01"}}]),
    "coordinates": "WP-C; project rule PR-1 (detail WP-01): each penetration takes a 0.50 x 0.50 m patch of the "
                   "membrane",
    "overrides": ["PR-1 UP-WP-004 penetration_treatment = PATCH 0.50 x 0.50 m (PROJECT scope, DETAIL)"],
    "assumptions": WP_B["assumptions"] + ["the patch is cut from the area's own membrane (a PATCH treatment is "
                                          "membrane area)"],
    "hand": [
        "the patch 0.50 x 0.50 is wider than a lane (0.30): a 0.50 m full-width segment holds two patches side by "
        "side (1.00 / 0.50); one is used, the other 0.50 x 0.50 place gives 1 lane 0.30 x 0.50 + 0.20 x 0.50 residue "
        "(0.10 m2 scrap)",
        "-- layout 1: strips 3.00 m long (ALONG_Y), as WP-B --",
        "pool after the doorway piece and the patch: 3.00, 2.00, 0.50; band 3.00 (covers 3.00) + 2.00 (1.90) + 0.50 "
        "(0.40) = 5.30, left 7.70 m -> segment 3 x (L - 0.10) >= 7.70 -> 2.67 m (2.66 gives 7.68)",
        "cuts 5 x 3.00 + 0.50 + 2.67 = 18.17 m, 2 rolls; band joints 5; seams 4 + 5 = 9",
        "-- layout 2: strips 4.00 m long (ALONG_X) --",
        "4 strips (last 0.30 m): floor cuts 16.00 m; trim 0.70 x 4.00 -> 2 lanes 4.00 + 0.40 m2 residue; doorway "
        "piece from a 4.00 lane (3.00 left); with the patch lane the pool is 4.00, 3.00, 0.50",
        "band 4.00 (covers 4.00) + 3.00 (2.90) + 0.50 (0.40) = 7.30, left 5.70 m -> 3 x (L - 0.10) >= 5.70 -> "
        "L = 2.00 m exactly (1.99 gives 5.67)",
        "band pieces 4.00 + 3.00 + 0.50 + 2.00 x 3 = 13.50 m = 13.00 + 5 joints x 0.10",
        "cuts 4.00 x 4 + 2.00 + 0.50 = 18.50 m -> roll 1 4.00 + 4.00 + 2.00 = 10.00, roll 2 4.00 + 4.00 + 0.50 = "
        "8.50 -> 2 rolls; seams 3 + 5 = 8",
        "selection (UP-WP-LAY-001): both 2 rolls; 8 seams < 9 -> ALONG_X, although it uses 0.33 m2 more membrane "
        "(fewest seams ranks before least membrane)",
        "laps 1.20 + 1.30 + 5 x 0.03 + 0.10 = 2.75 m2; detailing (the patch) 0.25 m2",
        "B = 12.00 + 2.60 + 0.20 + 2.75 + 0.25 = 17.80 m2 (the same in both layouts)",
        "waste = 18.50 - 17.80 = 0.70 m2 (0.40 floor trim residue + 0.10 patch residue + 0.10 x 2.00 segment residue)",
        "V2.4 counted the patch (1 pc, 0.25 m2) but left it out of B and of the rolls",
        "hand-calculation correction: the first draft of this sheet evaluated only layout 1 (18.17 m2); the engine "
        "comparison failed, layout 2 was then derived by hand as above - the expected values follow the hand "
        "calculation, not the engine",
    ],
    "expected": {"A_net_m2": 12.0, "eligible_m": 13.0, "upturn_m2": 2.6, "doorway_continuation_m2": 0.2,
                 "proven_subtotal_m2": 14.8, "direction": "ALONG_X", "floor_strips": 4, "last_strip_w_m": 0.3,
                 "band_pieces_m": [0.5, 2.0, 2.0, 2.0, 3.0, 4.0], "band_joints": 5, "laps_m2": 2.75,
                 "detailing_m2": 0.25, "B_m2": 17.8, "consumed_m2": 18.5, "waste_m2": 0.7, "rolls": 2,
                 "cuts_m": [4.0, 4.0, 4.0, 4.0, 2.0, 0.5], "alt_rolls": 2, "alt_seams": 9, "alt_consumed_m2": 18.17,
                 "penetrations": "COUNTED", "penetration_count": 1, "penetration_treatment": "BY_DETAIL",
                 "doorway_transition": "UNRESOLVED", "final_material_state": "PROVISIONAL_DETAILS_OPEN"},
    "reference": {"poly_mm": [(0, 0), (4000, 0), (4000, 3000), (0, 3000)], "runs_mm": [(13000, False)],
                  "doorways_mm": [(1000, 200)], "patches_mm": [(500, 500, 1)], "along": "X", "alt_along": "Y"},
    "exclusions": ["the doorway threshold transition", "corner treatment"],
}

# ---------------------------------------------------------------------------------------------------------- WP-BX
WP_BX = {
    "id": "WP-BX", "sequence": 6, "kind": "EXCEPTION",
    "title": "WP-B with a project doorway detail: upturn across the threshold",
    "proves": ["UP-WP-DOOR-001", "UP-RULES-001"],
    "scenario": dict(WP_B["scenario"], rules=[{"id": "PR-1", "rule_id": "UP-WP-DOOR-001", "parameter": "doorway_detail",
                                               "value": "UPTURN_ACROSS_THRESHOLD", "scope": {"kind": "PROJECT"},
                                               "source": {"kind": "DETAIL", "ref": "synthetic detail WP-02"}}]),
    "coordinates": "WP-B; project rule PR-1 (detail WP-02): the upturn continues across the door threshold",
    "overrides": ["PR-1 UP-WP-DOOR-001 doorway_detail = UPTURN_ACROSS_THRESHOLD (PROJECT scope, DETAIL)"],
    "assumptions": WP_B["assumptions"],
    "hand": [
        "transition released: 1.00 x 0.20 = 0.20 m2 (the threshold upturn)",
        "the band now follows the whole room line: one closed loop 13.00 + 1.00 = 14.00 m, every piece lapped",
        "pool 3.00, 2.00 (after the doorway piece): cover 2.90 + 1.90 = 4.80, left 9.20 m",
        "segment 3 x (L - 0.10) >= 9.20 -> L = 3.17 m (3.16 gives 9.18); pieces 3.17 + 3.17 + 3.16",
        "band pieces 3.00 + 2.00 + 3.17 + 3.17 + 3.16 = 14.50 m = 14.00 + 5 x 0.10",
        "laps 1.20 + 1.40 (14.00 x 0.10) + 0.15 + 0.10 = 2.85 m2; B = 12.00 + 2.60 + 0.20 + 0.20 + 2.85 = 17.85 m2",
        "cuts 5 x 3.00 + 3.17 = 18.17 m -> 2 rolls; waste 18.17 - 17.85 = 0.32 m2",
        "V2.4 modelled the threshold as a separate open 1.00 m run without laps at its two joints",
    ],
    "expected": {"A_net_m2": 12.0, "eligible_m": 13.0, "upturn_m2": 2.6, "transition_m2": 0.2,
                 "doorway_transition": "RESOLVED_BY_DETAIL", "direction": "ALONG_Y",
                 "band_pieces_m": [2.0, 3.0, 3.16, 3.17, 3.17], "band_joints": 5, "laps_m2": 2.85, "B_m2": 17.85,
                 "consumed_m2": 18.17, "waste_m2": 0.32, "rolls": 2},
    "reference": {"poly_mm": [(0, 0), (4000, 0), (4000, 3000), (0, 3000)], "runs_mm": [(14000, True)],
                  "doorways_mm": [(1000, 200)], "along": "Y", "extra_net_m2": 0.2},
    "exclusions": ["corner treatment", "penetrations (none drawn)"],
}

# ---------------------------------------------------------------------------------------------------------- WP-LX
WP_LX = {
    "id": "WP-LX", "sequence": 7, "kind": "EXCEPTION", "title": "WP-B with a project lap of 0.15 m (manufacturer)",
    "proves": ["UP-WP-002", "UP-RULES-001"],
    "scenario": dict(WP_B["scenario"], rules=[{"id": "PR-1", "rule_id": "UP-WP-002", "parameter": "lap_m",
                                               "value": 0.15, "scope": {"kind": "PROJECT"},
                                               "source": {"kind": "SPECIFICATION",
                                                          "ref": "synthetic membrane data sheet MS-01"}}]),
    "coordinates": "WP-B; project rule PR-1: the membrane data sheet asks 0.15 m at every joint (stricter wins, "
                   "UP-WP-002)",
    "overrides": ["PR-1 UP-WP-002 lap_m = 0.15 m (PROJECT scope, SPECIFICATION) - side and end laps alike"],
    "assumptions": WP_B["assumptions"],
    "hand": [
        "strips now add 1.00 - 0.15 = 0.85 m each; band = 0.20 + 0.15 = 0.35 m wide -> 2 lanes per 1.00 m width "
        "(0.70) + 0.30 m residue (too narrow for a 0.35 m lane)",
        "-- layout 1: strips 4.00 m long (ALONG_X) --",
        "across 3.00: 1.00 + 2 x 0.85 = 2.70 < 3.00 -> n = 4, the last 3.00 - 3 x 0.85 = 0.45 m; trim 0.55 -> 1 lane "
        "0.35 x 4.00 + 0.20 x 4.00 residue (0.80 m2)",
        "floor cuts 4 x 4.00 = 16.00 m; laid 3.45 x 4.00 = 13.80 m2 (side laps 3 x 4.00 x 0.15 = 1.80)",
        "doorway piece 1.00 x (0.20 + 0.15) from the 4.00 lane -> 3.00 left",
        "band 13.00 open: 3.00 (no lap), left 10.00 -> 2 x (L - 0.15) >= 10.00 -> L = 5.15 m; pieces 3.00 + 5.15 + "
        "5.15, 2 joints",
        "cuts 16.00 + 5.15 = 21.15 m -> 3 rolls (5.15 + 4.00 | 4.00 + 4.00 | 4.00)",
        "laps 1.80 + 1.95 (13.00 x 0.15) + 0.105 (2 x 0.35 x 0.15) + 0.15 (1.00 x 0.15) = 4.005 m2",
        "B = 12.00 + 2.60 + 0.20 + 4.005 = 18.805 m2; waste 21.15 - 18.805 = 2.345 m2 (0.80 + 0.30 x 5.15)",
        "-- layout 2: strips 3.00 m (ALONG_Y): n = 5 (1.00 + 4 x 0.85 = 4.40), last 0.60, 1 lane 3.00; segment "
        "2 x (L - 0.15) >= 11.00 -> 5.65 m; cuts 20.65 m, 3 rolls; seams 4 + 2 = 6 vs 3 + 2 = 5 -> ALONG_X",
        "the 0.15 m lap costs one roll against the 0.10 m standard (WP-B: 2 rolls) and 2.07 m2 more cutting waste",
    ],
    "expected": {"A_net_m2": 12.0, "eligible_m": 13.0, "upturn_m2": 2.6, "doorway_continuation_m2": 0.2,
                 "direction": "ALONG_X", "floor_strips": 4, "last_strip_w_m": 0.45,
                 "band_pieces_m": [3.0, 5.15, 5.15], "band_joints": 2, "laps_m2": 4.005, "B_m2": 18.805,
                 "consumed_m2": 21.15, "waste_m2": 2.345, "rolls": 3, "cuts_m": [5.15, 4.0, 4.0, 4.0, 4.0],
                 "alt_rolls": 3, "alt_seams": 6, "alt_consumed_m2": 20.65},
    "reference": {"poly_mm": [(0, 0), (4000, 0), (4000, 3000), (0, 3000)], "runs_mm": [(13000, False)],
                  "doorways_mm": [(1000, 200)], "along": "X", "alt_along": "Y", "lap_mm": 150},
    "exclusions": WP_B["exclusions"],
}

# ---------------------------------------------------------------------------------------------------------- WP-D
WP_D = {
    "id": "WP-D", "sequence": 8, "kind": "POSITIVE", "title": "L-shaped bathroom with a re-entrant corner",
    "proves": ["UP-WP-002", "UP-WP-003", "UP-WP-004", "UP-WP-LAY-001"],
    "scenario": {"ring": [(0.0, 0.0), (3.0, 0.0), (3.0, 2.0), (2.0, 2.0), (2.0, 3.0), (0.0, 3.0)],
                 "codes": ["BATHROOM"], "scope": "WET",
                 "doors": [{"id": "D1", "edge": 0, "t0": 0.5, "t1": 1.4, "width_m": 0.9, "depth_m": 0.2,
                            "other_side": "DRY"}], "inserts": [], "texts": [], "rules": []},
    "coordinates": "3.00 x 3.00 m with the 1.00 x 1.00 m north-east corner cut away: vertices (0,0) (3,0) (3,2) (2,2) "
                   "(2,3) (0,3); a 0.90 m door in the south wall x 0.50 - 1.40",
    "overrides": [], "assumptions": ["wall thickness at the door 0.20 m"],
    "hand": [
        "A = 9.00 - 1.00 = 8.00 m2; perimeter 3 + 2 + 1 + 1 + 2 + 3 = 12.00 m; eligible 12.00 - 0.90 = 11.10 m",
        "upturn 11.10 x 0.20 = 2.22 m2; continuation 0.90 x 0.20 = 0.18 m2; proven subtotal 10.40 m2",
        "corners: 5 internal (the room-side angle 90 degrees) + 1 external at (2,2) (the wall turns into the room: the "
        "re-entrant corner of the L); 2 upturn ends at the door jambs",
        "strips 3.00 m long across y 0..3: n = 4 (1.00 + 3 x 0.90 = 3.70), widths 1.00, 1.00, 1.00, 0.30 at y 0-1, "
        "0.9-1.9, 1.8-2.8, 2.7-3.0",
        "S1, S2 lie below y = 2: 3.00 m; S3 straddles y = 2: cut 3.00 m, room under it 0.20 x 3.00 + 0.80 x 2.00 = "
        "2.20 m2, the 0.80 x 1.00 m beyond the step is cut off at the wall (0.80 m2 waste); S4 above y = 2: 2.00 m",
        "floor cuts 3.00 x 3 + 2.00 = 11.00 m; laid 3.00 + 3.00 + 2.20 + 0.60 = 8.80 m2 (side laps 0.30 + 0.30 + 0.20 "
        "= 0.80)",
        "S4 trim 0.70 x 2.00 -> 2 lanes 2.00 + 0.10 x 2.00 residue (0.20 m2); doorway piece 0.90 x 0.30 from a lane "
        "-> 1.10 left",
        "band 11.10 m open: 2.00 (covers 2.00) + 1.10 (1.00), left 8.10 -> segment 2.80 (3 x 2.70 = 8.10 exactly)",
        "band pieces 2.00 + 1.10 + 2.80 x 3 = 11.50 m = 11.10 + 4 x 0.10; laid 3.45 m2",
        "laps 0.80 + 1.11 + 0.12 + 0.09 = 2.12 m2; B = 8.00 + 2.22 + 0.18 + 2.12 = 12.52 m2",
        "cuts 3.00, 3.00, 3.00, 2.80, 2.00 = 13.80 m -> 2 rolls; waste 13.80 - 12.52 = 1.28 m2 (0.80 step + 0.20 trim "
        "residue + 0.28 segment residue)",
        "the L is symmetric about its diagonal: the other direction gives the same plan -> ALONG_X",
        "not included: 6 corners (no detail - an external corner usually needs its own piece), the doorway transition "
        "(0.90 m, range 0.00 - 0.18 m2)",
    ],
    "expected": {"A_net_m2": 8.0, "perimeter_m": 12.0, "eligible_m": 11.1, "upturn_m2": 2.22,
                 "doorway_continuation_m2": 0.18, "proven_subtotal_m2": 10.4, "direction": "ALONG_X",
                 "floor_strips": 4, "last_strip_w_m": 0.3, "band_pieces_m": [1.1, 2.0, 2.8, 2.8, 2.8], "band_joints": 4,
                 "laps_m2": 2.12, "B_m2": 12.52, "consumed_m2": 13.8, "waste_m2": 1.28, "rolls": 2,
                 "cuts_m": [3.0, 3.0, 3.0, 2.8, 2.0], "doorway_transition": "UNRESOLVED",
                 "transition_range_m2": [0.0, 0.18], "corners_internal": 5, "corners_external": 1,
                 "corner_state": "WITHHELD", "penetrations": "NOT_SHOWN",
                 "final_material_state": "PROVISIONAL_DETAILS_OPEN"},
    "reference": {"poly_mm": [(0, 0), (3000, 0), (3000, 2000), (2000, 2000), (2000, 3000), (0, 3000)],
                  "runs_mm": [(11100, False)], "doorways_mm": [(900, 200)], "along": "X"},
    "exclusions": ["corner treatment (5 internal, 1 external)", "doorway threshold transition", "penetrations"],
}

# ---------------------------------------------------------------------------------------------------------- WP-E
WP_E = {
    "id": "WP-E", "sequence": 9, "kind": "POSITIVE", "title": "Kitchen 3.60 x 3.00 m with two doors and a pipe",
    "proves": ["UP-WP-003", "UP-WP-004", "UP-WP-DOOR-001", "UP-WP-LAY-001"],
    "scenario": {"ring": [(0.0, 0.0), (3.6, 0.0), (3.6, 3.0), (0.0, 3.0)], "codes": ["KITCHEN"], "scope": "WET",
                 "doors": [{"id": "D1", "edge": 3, "t0": 1.5, "t1": 2.4, "width_m": 0.9, "depth_m": 0.2,
                            "other_side": "DRY"},
                           {"id": "D2", "edge": 2, "t0": 0.4, "t1": 1.2, "width_m": 0.8, "depth_m": 0.2,
                            "other_side": "DRY"}],
                 "inserts": [], "texts": [{"id": "T1", "value": "PIPE SLEEVE", "x": 3.2, "y": 0.4}], "rules": []},
    "coordinates": "inner faces x 0..3.60, y 0..3.00; D1 0.90 m in the west wall y 0.60 - 1.50 (ring edge 3 runs "
                   "north to south from (0,3)); D2 0.80 m in the north wall x 2.40 - 3.20 (edge 2 runs west from "
                   "(3.6,3)); a PIPE SLEEVE text at (3.20, 0.40)",
    "overrides": [], "assumptions": ["wall thickness at both doors 0.20 m"],
    "hand": [
        "A = 3.60 x 3.00 = 10.80 m2; perimeter 13.20 m; eligible 13.20 - 0.90 - 0.80 = 11.50 m; upturn 2.30 m2",
        "continuation 0.90 x 0.20 + 0.80 x 0.20 = 0.34 m2; proven subtotal 13.44 m2",
        "two open runs, in ring order from after D2: 2.40 (north wall west of D2) + 1.50 (west wall north of D1) = "
        "3.90 m; then 0.60 + 3.60 + 3.00 + 0.40 = 7.60 m",
        "-- strips 3.00 m long (ALONG_Y) across the 3.60 m width --",
        "n = 4 (1.00 + 3 x 0.90 = 3.70 >= 3.60), the last 0.90 m wide: trim 0.10 x 3.00 is narrower than a lane "
        "(0.30 m2 scrap); floor cuts 4 x 3.00 = 12.00 m, laid 3.90 x 3.00 = 11.70 m2 (side laps 0.90)",
        "D1 piece 0.90 x 0.30: no lane -> a new 0.90 m full-width segment, 3 lanes: one used, two kept (0.90, "
        "0.90); residue 0.10 x 0.90 (0.09 m2); D2 piece 0.80 x 0.30 from a 0.90 lane -> 0.10 left",
        "run 1 (3.90): 0.90 lane covers 0.90 (no lap), left 3.00; the 0.10 lane covers nothing past its lap",
        "new segment for 3.00 (run 1, lapped) + 7.60 (run 2): 3.64 m - lane a: 3.10 finishes run 1 (0.54 left); "
        "run 2: lane b 3.64 (no lap), lane c 3.64 covers 3.54, lane a's 0.54 is cut 0.52 for the last 0.42 + lap",
        "3.63 fails: run 2 would be left 0.01 m with only 0.10 m lanes (0.10 - 0.10 lap covers nothing)",
        "band pieces 0.90 + 3.10 + 3.64 + 3.64 + 0.52 = 11.80 m = 11.50 + 3 joints x 0.10; laid 3.54 m2",
        "laps 0.90 + 1.15 + 0.09 + 0.17 (doorways 1.70 x 0.10) = 2.31 m2; B = 10.80 + 2.30 + 0.34 + 2.31 = 15.75 m2",
        "cuts 3.64, 3.00 x 4, 0.90 = 16.54 m -> 2 rolls (3.64 + 3.00 + 3.00; 3.00 + 3.00 + 0.90)",
        "waste 16.54 - 15.75 = 0.79 m2 (0.30 trim + 0.09 + 0.364 + 0.03 + 0.006)",
        "-- strips 3.60 m long (ALONG_X) --",
        "n = 4, last 0.30 m: trim 0.70 -> 2 lanes 3.60; D1 from a 3.60 (2.70 left), D2 from 2.70 (1.90 left); run 1: "
        "3.60 + 0.40; run 2: 1.50 + new segment 2.14 (3 x 2.04 = 6.12 >= 6.10); cuts 4 x 3.60 + 2.14 = 16.54 m, 2 "
        "rolls, 4 band joints, B 15.96 m2",
        "selection: both 2 rolls; seams ALONG_Y 3 + 3 = 6 < ALONG_X 3 + 4 = 7 -> ALONG_Y (the same 16.54 m consumed)",
        "pipe: 1 PIPE_PENETRATION counted from the text; collar withheld",
        "not included: two doorway transitions (0.90 m and 0.80 m: range 0.00 - 0.34 m2), 4 corners, the pipe collar",
    ],
    "expected": {"A_net_m2": 10.8, "perimeter_m": 13.2, "eligible_m": 11.5, "upturn_m2": 2.3,
                 "doorway_continuation_m2": 0.34, "proven_subtotal_m2": 13.44, "direction": "ALONG_Y",
                 "floor_strips": 4, "last_strip_w_m": 0.9, "band_pieces_m": [0.52, 0.9, 3.1, 3.64, 3.64],
                 "band_joints": 3, "laps_m2": 2.31, "B_m2": 15.75, "consumed_m2": 16.54, "waste_m2": 0.79, "rolls": 2,
                 "cuts_m": [3.64, 3.0, 3.0, 3.0, 3.0, 0.9], "alt_rolls": 2, "alt_seams": 7, "alt_consumed_m2": 16.54,
                 "doorway_transition": "UNRESOLVED", "transition_range_m2": [0.0, 0.34], "corners_internal": 4,
                 "corners_external": 0, "corner_state": "WITHHELD", "penetrations": "COUNTED",
                 "penetration_count": 1, "penetration_treatment": "WITHHELD",
                 "final_material_state": "PROVISIONAL_DETAILS_OPEN"},
    "reference": {"poly_mm": [(0, 0), (3600, 0), (3600, 3000), (0, 3000)], "runs_mm": [(3900, False), (7600, False)],
                  "doorways_mm": [(900, 200), (800, 200)], "along": "Y", "alt_along": "X"},
    "exclusions": ["two doorway transitions", "corner treatment", "the pipe collar (1 pipe, no detail)"],
}

# ---------------------------------------------------------------------------------------------------------- WP-F
WP_F = {
    "id": "WP-F", "sequence": 10, "kind": "POSITIVE",
    "title": "Roof 12.00 x 6.00 m: parapets, an access door, an open edge, two drains",
    "proves": ["UP-WP-ROOF-001", "UP-WP-002", "UP-WP-003", "UP-WP-004", "UP-WP-LAY-001"],
    "scenario": {"ring": [(0.0, 0.0), (12.0, 0.0), (12.0, 6.0), (0.0, 6.0)], "codes": ["ROOF"], "scope": "EXTERIOR",
                 "doors": [{"id": "D1", "edge": 2, "t0": 6.0, "t1": 7.0, "width_m": 1.0, "depth_m": 0.2,
                            "other_side": "DRY"}],
                 "open_edges": [{"id": "E1", "edge": 1, "t0": 2.0, "t1": 4.0}],
                 "inserts": [{"id": "RD1", "name": "ROOF DRAIN", "x": 2.0, "y": 1.0},
                             {"id": "RD2", "name": "ROOF DRAIN", "x": 10.0, "y": 1.0}], "texts": [], "rules": []},
    "coordinates": "parapet inner faces x 0..12.00, y 0..6.00; the stair-room door D1 1.00 m in the north side x 5.00 "
                   "- 6.00 (edge 2 runs west from (12,6)); an open edge E1 2.00 m in the east side y 2.00 - 4.00 (no "
                   "parapet: a step down to a lower roof); roof drains at (2,1) and (10,1)",
    "overrides": [], "assumptions": ["wall thickness at the door 0.20 m", "exterior membrane by specification: the "
                                     "Urban roll used, PROVISIONAL (UP-WP-ROOF-001)"],
    "hand": [
        "A = 12.00 x 6.00 = 72.00 m2; perimeter 36.00 m; eligible 36.00 - 1.00 - 2.00 = 33.00 m; upturn 6.60 m2",
        "continuation 1.00 x 0.20 = 0.20 m2; proven subtotal 78.80 m2",
        "runs in ring order from after the open edge: 2.00 + 6.00 = 8.00 m; then 5.00 + 6.00 + 12.00 + 2.00 = 25.00 m",
        "strips along the 12.00 m side across 6.00: n = 7 (1.00 + 6 x 0.90 = 6.40), the last 0.60 m",
        "12.00 m is longer than a roll: each strip is spliced 10.00 + 2.10 (2.00 + 0.10 end lap) -> 7 end laps",
        "floor cuts 7 x 10.00 + 7 x 2.10 = 84.70 m; laid 6.60 x 12.00 + end laps (6 x 1.00 + 0.60) x 0.10 = 79.20 + "
        "0.66 = 79.86 m2 (side laps 6 x 12.00 x 0.10 = 7.20)",
        "S7 trim 0.40 wide -> 1 lane per piece (10.00 and 2.10) + 0.10 residue x 12.10 m = 1.21 m2",
        "doorway piece 1.00 x 0.30 from the 2.10 lane -> 1.10 left; pool 10.00, 1.10",
        "run 1 (8.00): the 10.00 lane covers it (2.00 left); run 2 (25.00): 2.00 (no lap) + 1.10 (1.00) = 3.00, left "
        "22.00",
        "segment 3 x (L - 0.10) >= 22.00 -> 7.44 m (7.43 gives 21.99); pieces 7.44 + 7.44 + 7.42",
        "band pieces 8.00 + 2.00 + 1.10 + 7.44 + 7.44 + 7.42 = 33.40 = 33.00 + 4 x 0.10; laid 10.02 m2",
        "laps 7.20 + 0.66 + 3.30 + 0.12 + 0.10 = 11.38 m2; B = 72.00 + 6.60 + 0.20 + 11.38 = 90.18 m2",
        "cuts 92.14 m -> at least 10 rolls; 7 rolls hold one 10.00 m piece each; 7.44 + 2.10, 4 x 2.10, 2 x 2.10 -> 10",
        "waste 92.14 - 90.18 = 1.96 m2 (1.21 + 0.744 + 0.006)",
        "the other direction (6.00 m strips across 12.00): 14 strips, no two share a roll (12.00 > 10.00) -> at least 14 "
        "rolls -> the 12.00 m direction",
        "2 roof drains counted, treatment withheld; the open edge E1 2.00 m needs a termination detail; the door a "
        "transition detail (range 0.00 - 0.20 m2); 4 corners withheld",
    ],
    "expected": {"A_net_m2": 72.0, "perimeter_m": 36.0, "eligible_m": 33.0, "upturn_m2": 6.6,
                 "doorway_continuation_m2": 0.2, "proven_subtotal_m2": 78.8, "direction": "ALONG_X",
                 "floor_strips": 7, "last_strip_w_m": 0.6, "band_pieces_m": [1.1, 2.0, 7.42, 7.44, 7.44, 8.0],
                 "band_joints": 4, "laps_m2": 11.38, "B_m2": 90.18, "consumed_m2": 92.14, "waste_m2": 1.96,
                 "rolls": 10, "doorway_transition": "UNRESOLVED", "transition_range_m2": [0.0, 0.2],
                 "termination_unresolved_m": 3.0, "corners_internal": 4, "corners_external": 0,
                 "corner_state": "WITHHELD", "penetrations": "COUNTED", "penetration_count": 2,
                 "penetration_treatment": "WITHHELD", "final_material_state": "PROVISIONAL_DETAILS_OPEN"},
    "reference": {"poly_mm": [(0, 0), (12000, 0), (12000, 6000), (0, 6000)], "runs_mm": [(8000, False),
                                                                                          (25000, False)],
                  "doorways_mm": [(1000, 200)], "along": "X"},
    "exclusions": ["the open-edge termination (2.00 m)", "the door transition", "2 drain collars", "4 corners",
                   "falls and the lap direction towards the drains"],
}

# ---------------------------------------------------------------------------------------------------------- WP-G
WP_G = {
    "id": "WP-G", "sequence": 11, "kind": "POSITIVE", "title": "Balcony 4.00 x 1.50 m with its 1.80 m doorway",
    "proves": ["UP-WP-ROOF-001", "UP-WP-DOOR-001", "UP-WP-MAT-001"],
    "scenario": {"ring": [(0.0, 0.0), (4.0, 0.0), (4.0, 1.5), (0.0, 1.5)], "codes": ["BALCONY"], "scope": "EXTERIOR",
                 "doors": [{"id": "D1", "edge": 2, "t0": 1.1, "t1": 2.9, "width_m": 1.8, "depth_m": 0.2,
                            "other_side": "DRY"}], "inserts": [], "texts": [], "rules": []},
    "coordinates": "balcony inner faces x 0..4.00, y 0..1.50; the building wall on the north (y = 1.50) with the "
                   "1.80 m door to the living room x 1.10 - 2.90; parapet walls on the other three sides",
    "overrides": [], "assumptions": ["wall thickness at the door 0.20 m", "exterior membrane by specification "
                                     "(PROVISIONAL)"],
    "hand": [
        "A = 4.00 x 1.50 = 6.00 m2; perimeter 11.00 m; eligible 11.00 - 1.80 = 9.20 m; upturn 1.84 m2",
        "continuation 1.80 x 0.20 = 0.36 m2; proven subtotal 8.20 m2",
        "strips 4.00 m across 1.50: n = 2 (1.00 + 0.90 = 1.90), the last 0.60 m; trim 0.40 -> 1 lane 4.00 + 0.10 x "
        "4.00 residue (0.40 m2)",
        "floor cuts 2 x 4.00 = 8.00 m, laid 1.60 x 4.00 = 6.40 m2 (side lap 0.40)",
        "doorway piece 1.80 x 0.30 from the 4.00 lane -> 2.20 left",
        "band 9.20 open: 2.20 (covers 2.20), left 7.00 -> segment 2.44 m (3 x 2.34 = 7.02; 2.43 gives 6.99)",
        "pieces 2.20 + 2.44 + 2.44 + 2.42 = 9.50 m = 9.20 + 3 x 0.10; laid 2.85 m2",
        "laps 0.40 + 0.92 + 0.09 + 0.18 = 1.59 m2; B = 6.00 + 1.84 + 0.36 + 1.59 = 9.79 m2",
        "cuts 4.00 + 4.00 + 2.44 = 10.44 m -> 2 rolls (the second roll is used for 2.44 m only); waste 0.65 m2",
        "1.50 m strips (ALONG_Y): 5 strips, 2 rolls, seams 4 + 6 = 10 vs 1 + 3 = 4 -> ALONG_X",
        "not included: the door threshold - the critical exterior detail, 1.80 m (range 0.00 - 0.36 m2); 4 corners; "
        "drains not drawn (NOT_SHOWN)",
        "procurement: an exterior system is never combined with the wet-area rolls (UP-WP-MAT-001)",
    ],
    "expected": {"A_net_m2": 6.0, "perimeter_m": 11.0, "eligible_m": 9.2, "upturn_m2": 1.84,
                 "doorway_continuation_m2": 0.36, "proven_subtotal_m2": 8.2, "direction": "ALONG_X",
                 "floor_strips": 2, "last_strip_w_m": 0.6, "band_pieces_m": [2.2, 2.42, 2.44, 2.44], "band_joints": 3,
                 "laps_m2": 1.59, "B_m2": 9.79, "consumed_m2": 10.44, "waste_m2": 0.65, "rolls": 2,
                 "doorway_transition": "UNRESOLVED", "transition_range_m2": [0.0, 0.36], "corners_internal": 4,
                 "corners_external": 0, "corner_state": "WITHHELD", "penetrations": "NOT_SHOWN",
                 "final_material_state": "PROVISIONAL_DETAILS_OPEN"},
    "reference": {"poly_mm": [(0, 0), (4000, 0), (4000, 1500), (0, 1500)], "runs_mm": [(9200, False)],
                  "doorways_mm": [(1800, 200)], "along": "X"},
    "exclusions": ["the balcony door threshold (critical: water towards the interior)", "corners", "drains (none "
                   "drawn)", "the balustrade / parapet top"],
}

# ---------------------------------------------------------------------------------------------------------- WP-W
WP_W = {
    "id": "WP-W", "sequence": 12, "kind": "POSITIVE", "title": "WC 1.50 x 1.20 m with a 0.80 m door (for WP-H)",
    "proves": ["UP-WP-LAY-001"],
    "scenario": {"ring": [(0.0, 0.0), (1.5, 0.0), (1.5, 1.2), (0.0, 1.2)], "codes": ["BATHROOM"], "scope": "WET",
                 "doors": [{"id": "D1", "edge": 0, "t0": 0.35, "t1": 1.15, "width_m": 0.8, "depth_m": 0.2,
                            "other_side": "DRY"}], "inserts": [], "texts": [], "rules": []},
    "coordinates": "inner faces x 0..1.50, y 0..1.20; a 0.80 m door in the south wall x 0.35 - 1.15",
    "overrides": [], "assumptions": ["wall thickness at the door 0.20 m"],
    "hand": [
        "A = 1.80 m2; eligible 5.40 - 0.80 = 4.60 m; upturn 0.92 m2; continuation 0.16 m2",
        "strips 1.20 m long across 1.50 (ALONG_Y): n = 2, the last 0.60 m; trim 0.40 -> 1 lane 1.20; doorway piece "
        "0.80 from it (0.40 left)",
        "band 4.60 open: 0.40 (covers 0.40), left 4.20 -> segment 1.50 m (3 x 1.40 = 4.20 exactly); pieces 0.40 + "
        "1.50 x 3 = 4.90 m, 3 joints",
        "cuts 1.20 + 1.20 + 1.50 = 3.90 m, 1 roll; B = 1.80 + 0.92 + 0.16 + 0.75 = 3.63 m2 (laps 0.12 + 0.46 + 0.09 + "
        "0.08)",
        "ALONG_X (1.50 m strips): 2 strips, segment 0.94 m, 4 joints, 3.94 m -> seams 1 + 4 = 5 vs 1 + 3 = 4 -> ALONG_Y",
    ],
    "expected": {"A_net_m2": 1.8, "eligible_m": 4.6, "upturn_m2": 0.92, "doorway_continuation_m2": 0.16,
                 "direction": "ALONG_Y", "floor_strips": 2, "band_pieces_m": [0.4, 1.5, 1.5, 1.5], "band_joints": 3,
                 "laps_m2": 0.75, "B_m2": 3.63, "consumed_m2": 3.9, "waste_m2": 0.27, "rolls": 1,
                 "cuts_m": [1.5, 1.2, 1.2]},
    "reference": {"poly_mm": [(0, 0), (1500, 0), (1500, 1200), (0, 1200)], "runs_mm": [(4600, False)],
                  "doorways_mm": [(800, 200)], "along": "Y"},
    "exclusions": ["doorway transition", "corners", "penetrations"],
}

# ---------------------------------------------------------------------------------------------------------- WP-H
WP_H = {
    "id": "WP-H", "sequence": 13, "kind": "POSITIVE",
    "title": "Several rooms sharing one roll inventory: WP-B + WP-A + WP-W (wet) and WP-G (exterior)",
    "proves": ["UP-WP-LAY-001", "UP-WP-MAT-001"],
    "members": ["WP-B", "WP-A", "WP-W", "WP-G"],
    "hand": [
        "compatibility: WP-B, WP-A and WP-W are one wet-area system (same roll 1.00 x 10.00, same 0.10 lap); WP-G is "
        "the exterior system - never in the same rolls",
        "cut sizes - only full-width pieces move between rooms; band lanes, trims and residues stay in their room:",
        "  WP-B 3.00 x 5, 2.80; WP-A 2.00 x 3, 1.50; WP-W 1.50, 1.20, 1.20 -> 13 pieces, 29.20 m",
        "rolls if each room is bought alone: 2 + 1 + 1 = 4",
        "shared: 29.20 m -> at least 3 rolls; a 3-roll cutting plan exists: roll 1 3.00 + 3.00 + 2.80 + 1.20 = "
        "10.00; roll 2 3.00 + 3.00 + 2.00 + 2.00 = 10.00; roll 3 3.00 + 2.00 + 1.50 + 1.50 + 1.20 = 9.20 m (0.80 m "
        "left) -> 3 rolls",
        "first fit decreasing (V2.4): 3+3+3 | 3+3+2.80+1.20 | 2+2+2+1.50+1.50 | 1.20 -> 4 rolls: it places the long "
        "pieces first and strands the last 1.20 m",
        "installation practicality: every piece is a straight full-width cut from a roll remainder at least as long "
        "as the piece; all rooms on one floor (no part roll carried between floors)",
        "exterior system WP-G alone: 4.00 + 4.00 + 2.44 = 10.44 m > 10.00 m -> 2 rolls (nothing to share with)",
        "C procurement: wet-area system 3 rolls, exterior system 2 rolls - two lines, never one total",
    ],
    "expected": {"wet_rolls": 3, "wet_rolls_alone": 4, "wet_cut_m": 29.2, "exterior_rolls": 2, "systems": 2,
                 "v24_first_fit_rolls": 4},
    "reference": None,
    "exclusions": ["sharing narrow offcuts between rooms (not done: a band lane from one room is not carried to "
                   "another)", "carrying part rolls between floors (owner / contractor decision)"],
}

WP_CASES = [WP_A, WP_B, WP_S, WP_C, WP_CX, WP_BX, WP_LX, WP_D, WP_E, WP_F, WP_G, WP_W, WP_H]
SEQUENCE = [c["id"] for c in sorted(WP_CASES, key=lambda c: c["sequence"])]
