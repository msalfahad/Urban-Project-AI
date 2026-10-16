"""PROOF CASES - Phase 2B-3 (ARCH_TAKEOFF_V2.5): the ten door worked examples (WP-4 of the program).

Every case is the two-room synthetic plan of tests/m9_p2b2 (p2b2_fixtures.two_rooms, millimetres): room A x 200..4000,
room B x 4200..8200 (or b_right), y 200..4200, a 0.20 m party wall x 4000..4200 with the door gap y s0..s1. The
expected values are typed from the hand calculation of each case (coordinates -> distances -> the owner rules). No
value here is computed; nothing here imports the engine.

Owner values used (registry 1.1.0, owner approved): UP-DOOR-OPEN-002 required nominal door INTERNAL_PVC 1.00 m,
BATHROOM_PVC 0.90 m, EXTERNAL_ALUMINIUM 1.00 m; wall opening = nominal + 0.10 m allowance; the largest door an opening
takes = CAD opening - 0.10 m. UP-DOOR-HGT-001 owner reference heights: ordinary doors 2.20 m, main entrance 2.50 m
(OWNER_STANDARD_ASSUMED when no schedule / section gives it). UP-DOOR-FEAS-001: a column is never cut; geometric
clearance is never a structural approval.

Engine value used and NOT an owner standard (unresolved owner decision N-2): the pier kept beside a junction, corner
or opening after an enlargement, 0.10 m (ENGINE_LIMITATION). Engine reading reach beyond a jamb: 3.00 m.

Structure (UP-DOOR-FEAS-001): the plan draws a column frame (a column in room A at x 600..1000, y 3400..3800 unless
stated) and the wall on a masonry layer -> MASONRY_INDICATED (not verified); a project rule from a structural drawing
-> NON_STRUCTURAL_SPECIFIED / STRUCTURAL; neither -> UNKNOWN. No case claims structural feasibility: every
enlargement keeps the structural engineer's approval.
"""

DOOR_RULES = ["UP-DOOR-OPEN-002 required nominal + 0.10 m = required wall opening; CAD - 0.10 m = door that fits",
              "UP-DOOR-FEAS-001 clearances, constraints, placements, classes, approvals",
              "UP-DOOR-HGT-001 heights: schedule / section first, owner reference 2.20 m / 2.50 m",
              "UP-DOOR-CLS-001..004 categories (internal PVC, bathroom PVC, main entrance as drawn)",
              "UP-FIN-PLASTER-001 / V2.4 jamb plaster: 2 x wall t x H + t x opening width"]

DR_01 = {
    "id": "DR-01", "sequence": 1, "kind": "POSITIVE", "title": "1.10 m opening takes the 1.00 m internal door",
    "proves": ["UP-DOOR-OPEN-002", "UP-DOOR-FEAS-001"],
    "plan": {"s0": 1500, "s1": 2600},
    "hand": ["CAD wall opening = 2600 - 1500 = 1.10 m; BEDROOM | LIVING -> INTERNAL_PVC",
             "required nominal 1.00 m -> required wall opening 1.00 + 0.10 = 1.10 m",
             "enlargement = max(0, 1.10 - 1.10) = 0.00 -> MEETS_STANDARD, STANDARD_FITS_AS_DRAWN",
             "door that fits = 1.10 - 0.10 = 1.00 m",
             "clearances (reported, not needed): START 1500 - 200 = 1.30 m to the exterior-wall junction; END "
             "4200 - 2600 = 1.60 m to the junction",
             "no modification -> no approval; height 2.20 m owner reference (no schedule): OWNER_STANDARD_ASSUMED"],
    "expected": {"category": "INTERNAL_PVC", "cad_wall_opening_m": 1.1, "required_nominal_door_m": 1.0,
                 "required_wall_opening_m": 1.1, "available_nominal_m": 1.0, "enlargement_m": 0.0,
                 "compliance": "MEETS_STANDARD", "feasibility": "STANDARD_FITS_AS_DRAWN",
                 "start_constraint": "JUNCTION", "start_plain_m": 1.3, "end_constraint": "JUNCTION",
                 "end_plain_m": 1.6, "approvals": [], "height_m": 2.2, "height_state": "OWNER_STANDARD_ASSUMED"},
    "exclusions": ["finished clear passage width (not measured from a plan)", "frame / leaf product sizes"],
}

DR_02 = {
    "id": "DR-02", "sequence": 2, "kind": "POSITIVE",
    "title": "1.00 m opening: a 0.90 m door fits, +0.10 m for the 1.00 m standard",
    "proves": ["UP-DOOR-OPEN-002", "UP-DOOR-FEAS-001"],
    "plan": {"s0": 1500, "s1": 2500},
    "hand": ["CAD 2500 - 1500 = 1.00 m; INTERNAL_PVC; door that fits = 1.00 - 0.10 = 0.90 m",
             "required wall opening 1.10 m -> enlargement 1.10 - 1.00 = 0.10 m (ENLARGEMENT_REQUIRED)",
             "START: plain wall 1500 - 200 = 1.30 m to a junction; less the 0.10 m pier -> 1.20 m available",
             "END: 4200 - 2500 = 1.70 m to a junction; less 0.10 -> 1.60 m available",
             "maximum geometric enlargement 1.20 + 1.60 = 2.80 m >= 0.10 -> placement SPLIT_EQUAL 0.05 + 0.05 m",
             "swing: the 1.00 m leaf turns into room B, 4.00 m deep -> CLEAR",
             "structure MASONRY_INDICATED (a column frame is drawn; not verified) -> geometrically possible only",
             "approvals: owner / architect (design change), structural engineer (non-load-bearing wall, lintel)"],
    "expected": {"category": "INTERNAL_PVC", "cad_wall_opening_m": 1.0, "required_wall_opening_m": 1.1,
                 "available_nominal_m": 0.9, "enlargement_m": 0.1, "compliance": "ENLARGEMENT_REQUIRED",
                 "start_constraint": "JUNCTION", "start_plain_m": 1.3, "end_constraint": "JUNCTION",
                 "end_plain_m": 1.7, "max_feasible_enlargement_m": 2.8, "max_is_lower_bound": False,
                 "placement": "SPLIT_EQUAL", "placement_start_m": 0.05, "placement_end_m": 0.05, "swing": "CLEAR",
                 "leaf_m": 1.0, "structure": "MASONRY_INDICATED", "feasibility": "ENLARGEMENT_GEOMETRICALLY_POSSIBLE",
                 "approvals": ["owner / architect", "structural engineer"], "height_m": 2.2},
    "exclusions": ["structural feasibility (no structural drawing)", "lintel design"],
}

DR_03 = {
    "id": "DR-03", "sequence": 3, "kind": "POSITIVE",
    "title": "0.80 m bathroom opening: a 0.70 m door fits, +0.20 m for the 0.90 m standard",
    "proves": ["UP-DOOR-OPEN-002", "UP-DOOR-CLS-003"],
    "plan": {"a_word": "BATH", "s0": 1500, "s1": 2300},
    "hand": ["CAD 2300 - 1500 = 0.80 m; room A is a BATH -> BATHROOM_PVC",
             "required nominal 0.90 m -> required wall opening 1.00 m; enlargement 1.00 - 0.80 = 0.20 m",
             "door that fits as drawn = 0.80 - 0.10 = 0.70 m (the owner's own example)",
             "START 1.30 m (available 1.20), END 4200 - 2300 = 1.90 m (available 1.80) -> maximum 3.00 m; SPLIT_EQUAL "
             "0.10 + 0.10",
             "swing of the 0.90 m leaf into room B: CLEAR; structure MASONRY_INDICATED",
             "approvals: owner / architect, structural engineer"],
    "expected": {"category": "BATHROOM_PVC", "cad_wall_opening_m": 0.8, "required_nominal_door_m": 0.9,
                 "required_wall_opening_m": 1.0, "available_nominal_m": 0.7, "enlargement_m": 0.2,
                 "compliance": "ENLARGEMENT_REQUIRED", "start_plain_m": 1.3, "end_plain_m": 1.9,
                 "max_feasible_enlargement_m": 3.0, "placement": "SPLIT_EQUAL", "placement_start_m": 0.1,
                 "placement_end_m": 0.1, "leaf_m": 0.9, "feasibility": "ENLARGEMENT_GEOMETRICALLY_POSSIBLE",
                 "approvals": ["owner / architect", "structural engineer"]},
    "exclusions": ["structural feasibility"],
}

DR_04 = {
    "id": "DR-04", "sequence": 4, "kind": "BOUNDARY", "title": "Opening beside a column",
    "proves": ["UP-DOOR-FEAS-001"],
    "plan": {"columns": [[3900, 1100], [600, 3400]], "s0": 1500, "s1": 2400},
    "hand": ["CAD 2400 - 1500 = 0.90 m; INTERNAL_PVC; enlargement 1.10 - 0.90 = 0.20 m",
             "a 0.40 m column x 3900..4300, y 1100..1500 stands in the wall line, its face at the START jamb y 1500 -> "
             "START plain 0.00 m, constraint COLUMN (never cut, no enlargement on that side)",
             "END 4200 - 2400 = 1.80 m to a junction -> 1.70 m available; maximum 0.00 + 1.70 = 1.70 m",
             "placement END_SIDE: the whole 0.20 m at the end jamb (y 2400 -> 2600)",
             "approvals: owner / architect, structural engineer (the column is the jamb: the lintel bears on it)"],
    "expected": {"cad_wall_opening_m": 0.9, "enlargement_m": 0.2, "start_constraint": "COLUMN", "start_plain_m": 0.0,
                 "end_constraint": "JUNCTION", "end_plain_m": 1.8, "max_feasible_enlargement_m": 1.7,
                 "placement": "END_SIDE", "placement_start_m": 0.0, "placement_end_m": 0.2,
                 "feasibility": "ENLARGEMENT_GEOMETRICALLY_POSSIBLE",
                 "approvals": ["owner / architect", "structural engineer"]},
    "exclusions": ["the column's own design (never altered)"],
}

DR_05 = {
    "id": "DR-05", "sequence": 5, "kind": "EXCEPTION",
    "title": "Opening beside a non-structural blockwork return (project rule from the structural plan)",
    "proves": ["UP-DOOR-FEAS-001", "UP-RULES-001"],
    "plan": {"a_partition": 2500, "s0": 2800, "s1": 3700,
             "rules": [{"id": "PR-1", "rule_id": "UP-DOOR-FEAS-001", "parameter": "wall_structure",
                        "value": "NON_STRUCTURAL", "scope": {"kind": "PROJECT"},
                        "source": {"kind": "DRAWING", "ref": "structural plan S-101"}}]},
    "hand": ["CAD 3700 - 2800 = 0.90 m; enlargement 0.20 m",
             "a 0.20 m blockwork wall crosses room A at y 2500..2700 and meets the party wall's A face: START plain "
             "2800 - 2700 = 0.10 m, a junction; less the 0.10 m pier -> 0.00 m available (the return is not cut)",
             "END 4200 - 3700 = 0.50 m to the junction -> 0.40 m available; maximum 0.40 m >= 0.20 -> END_SIDE 0.20",
             "the host wall is NON_STRUCTURAL_SPECIFIED by the project rule (structural plan S-101): structural "
             "evidence exists, the structural engineer still confirms the lintel over the wider opening",
             "removing part of the blockwork return would be a further design change: not proposed"],
    "expected": {"cad_wall_opening_m": 0.9, "enlargement_m": 0.2, "start_constraint": "JUNCTION",
                 "start_plain_m": 0.1, "end_constraint": "JUNCTION", "end_plain_m": 0.5,
                 "max_feasible_enlargement_m": 0.4, "placement": "END_SIDE", "placement_end_m": 0.2,
                 "structure": "NON_STRUCTURAL_SPECIFIED", "feasibility": "ENLARGEMENT_GEOMETRICALLY_POSSIBLE",
                 "approvals": ["owner / architect", "structural engineer"]},
    "exclusions": ["cutting the blockwork return"],
}

DR_06 = {
    "id": "DR-06", "sequence": 6, "kind": "BOUNDARY", "title": "Opening at a wall corner (junction at the reach limit)",
    "proves": ["UP-DOOR-FEAS-001"],
    "plan": {"s0": 300, "s1": 1200},
    "hand": ["CAD 1200 - 300 = 0.90 m; enlargement 0.20 m",
             "START: 300 - 200 = 0.10 m to the exterior-wall junction -> 0.00 m available after the 0.10 m pier",
             "END: 4200 - 1200 = 3.00 m to the junction at the north wall -> 3.00 - 0.10 = 2.90 m available",
             "maximum 0.00 + 2.90 = 2.90 m (exact: the junction is seen) -> END_SIDE 0.20 m",
             "V2.4 read the wall only to 3.00 m exclusive: it called the END side an OPEN_RUN and claimed 'at least "
             "3.00 m' - not conservative (the true maximum is 2.90 m)"],
    "expected": {"cad_wall_opening_m": 0.9, "enlargement_m": 0.2, "start_constraint": "JUNCTION",
                 "start_plain_m": 0.1, "end_constraint": "JUNCTION", "end_plain_m": 3.0,
                 "max_feasible_enlargement_m": 2.9, "max_is_lower_bound": False, "placement": "END_SIDE",
                 "placement_end_m": 0.2, "feasibility": "ENLARGEMENT_GEOMETRICALLY_POSSIBLE"},
    "exclusions": ["the exterior wall corner itself (not altered)"],
}

DR_07 = {
    "id": "DR-07", "sequence": 7, "kind": "CONFLICT", "title": "Insufficient swing clearance into a 0.95 m corridor",
    "proves": ["UP-DOOR-FEAS-001"],
    "plan": {"b_word": "CORRIDOR", "b_right": 5150},
    "hand": ["CAD 2400 - 1500 = 0.90 m; enlargement 0.20 m; room B is a corridor x 4200..5150 = 0.95 m deep",
             "the drawn 0.90 m leaf swings clear (0.90 < 0.95); the owner-standard 1.00 m leaf does not (1.00 > 0.95) "
             "-> swing CONFLICT",
             "the wall itself has room (START 1.30, END 1.80 m) but the larger door cannot open: "
             "ENLARGEMENT_CONSTRAINED",
             "approvals: owner / architect (design change), structural engineer, owner / architect (accept a smaller "
             "door, re-hang it into room A, or redesign)"],
    "expected": {"cad_wall_opening_m": 0.9, "enlargement_m": 0.2, "swing": "CONFLICT", "swing_as_drawn": "CLEAR",
                 "leaf_m": 1.0, "feasibility": "ENLARGEMENT_CONSTRAINED", "door_that_fits_m": 0.8,
                 "approvals": ["owner / architect", "structural engineer", "owner / architect"]},
    "exclusions": ["re-hanging the door (a design choice)"],
}

DR_08 = {
    "id": "DR-08", "sequence": 8, "kind": "EXCEPTION",
    "title": "Project-specific width: the bathroom door standard is 0.80 m on this project",
    "proves": ["UP-DOOR-OPEN-002", "UP-RULES-001"],
    "plan": {"a_word": "BATH", "s0": 1500, "s1": 2300,
             "rules": [{"id": "PR-1", "rule_id": "UP-DOOR-OPEN-002", "parameter": "required_nominal_door_m",
                        "value": 0.8, "scope": {"kind": "DOOR_CATEGORY", "categories": ["BATHROOM_PVC"]},
                        "source": {"kind": "SCHEDULE", "ref": "door schedule"}}]},
    "scope_check": {"s0": 1500, "s1": 2400},
    "hand": ["the project door schedule sets BATHROOM_PVC to 0.80 m (Level B, DOOR_CATEGORY scope); the Urban 0.90 m "
             "is kept beside it",
             "required wall opening 0.80 + 0.10 = 0.90 m; CAD 0.80 m -> enlargement 0.10 m (not 0.20)",
             "scope: an internal door on the same project keeps the Urban 1.00 m (the rule names bathrooms only)"],
    "expected": {"category": "BATHROOM_PVC", "required_nominal_door_m": 0.8, "urban_nominal_m": 0.9,
                 "standard_state": "PROJECT_SPECIFIED", "required_wall_opening_m": 0.9, "enlargement_m": 0.1,
                 "scope_check_required_nominal_door_m": 1.0},
    "exclusions": [],
}

DR_09 = {
    "id": "DR-09", "sequence": 9, "kind": "POSITIVE", "title": "Main entrance, double leaf, 2.50 m height",
    "proves": ["UP-DOOR-CLS-004", "UP-DOOR-HGT-001", "UP-FIN-PLASTER-001"],
    "plan": {"b_word": "ENTRANCE HALL", "main_entrance": {"y0": 0, "y1": 200, "s0": 5000, "s1": 6600}},
    "hand": ["the opening in the south exterior wall x 5000..6600 = 1.60 m, two 0.80 m leaves, into the ENTRANCE "
             "HALL -> MAIN_ENTRANCE: measured as drawn (the PVC / aluminium standard is never applied)",
             "height: no schedule -> owner reference 2.50 m, OWNER_STANDARD_ASSUMED (AREA_ASSUMED)",
             "door area 1.60 x 2.50 = 4.00 m2 - ASSUMED only (the door scenarios); the as-drawn BOQ door line keeps "
             "count 1 and width 1.60 m and withholds the area: no confirmed area from an assumed height "
             "(UP-DOOR-HGT-001)",
             "jamb and head plaster = 2 x 0.20 x 2.50 + 0.20 x 1.60 = 1.00 + 0.32 = 1.32 m2 (PROVISIONAL)",
             "no enlargement: STANDARD_FITS_AS_DRAWN; one door set (count 1)"],
    "expected": {"category": "MAIN_ENTRANCE", "cad_wall_opening_m": 1.6, "standard": None,
                 "feasibility": "STANDARD_FITS_AS_DRAWN", "height_m": 2.5, "height_state": "OWNER_STANDARD_ASSUMED",
                 "door_count": 1, "door_area_m2": None, "assumed_area_m2": 4.0, "assumed_area_state": "ASSUMED",
                 "jamb_plaster_m2": 1.32},
    "exclusions": ["the main entrance product (by specification)"],
}

DR_10 = {
    "id": "DR-10", "sequence": 10, "kind": "POSITIVE", "title": "Ordinary internal door, 2.20 m height",
    "proves": ["UP-DOOR-HGT-001", "UP-FIN-PLASTER-001"],
    "plan": {"s0": 1500, "s1": 2400},
    "hand": ["CAD 0.90 m, INTERNAL_PVC; height: no schedule -> owner reference 2.20 m (OWNER_STANDARD_ASSUMED)",
             "door area 0.90 x 2.20 = 1.98 m2 - ASSUMED only; the as-drawn door line withholds the area (no "
             "height source)",
             "jamb and head plaster = 2 x 0.20 x 2.20 + 0.20 x 0.90 = 0.88 + 0.18 = 1.06 m2 (PROVISIONAL)",
             "the as-drawn BOQ keeps the 0.90 m door; the 0.20 m enlargement is a proposed modification only"],
    "expected": {"category": "INTERNAL_PVC", "cad_wall_opening_m": 0.9, "height_m": 2.2,
                 "height_state": "OWNER_STANDARD_ASSUMED", "door_count": 1, "door_area_m2": None,
                 "assumed_area_m2": 1.98, "assumed_area_state": "ASSUMED",
                 "jamb_plaster_m2": 1.06, "as_drawn_width_m": 0.9},
    "exclusions": [],
}

DOOR_CASES = [DR_01, DR_02, DR_03, DR_04, DR_05, DR_06, DR_07, DR_08, DR_09, DR_10]
