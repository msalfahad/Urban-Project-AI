"""PROOF CASES - Phase 2B-3 (ARCH_TAKEOFF_V2.5): the project rules sheets (WP-5 of the program), on the proof drawing
PD-1 (proof_drawings.bathrooms: BATH1 and BATH2, both the WP-B bathroom, and a dry corridor).

Each case is a project rules file (URBAN_PROJECT_RULES_V1) and the values its hand calculation gives; the drawing's
sha256 is written into the file at run time where the case says "<THIS DRAWING>" (the generated DXF is the input).
No value here is computed; nothing here imports the engine.

Sheet columns the program asks for and where they are on every row of PROJECT_RULES_SHEET: master standard
(urban_standard), drawing requirement (drawing_specification), applied rule (applied_rule), source, conflict (status
CONFLICT_REVIEW and the C- rows), assumption (status OWNER_STANDARD_ASSUMED), affected quantities (impact), approval
status (status, and APPROVALS_REQUIRED for every conflict)."""

THIS_DRAWING = "<THIS DRAWING>"
BATH1_POINT = [2.2, 1.6]

RS_01 = {
    "id": "RS-01", "sequence": 1, "kind": "POSITIVE", "title": "No project rules: every value is the Urban standard",
    "proves": ["UP-RULES-001"], "rules": None,
    "hand": ["no rules file: every rules-sheet row of a waterproofing value is OWNER_STANDARD_ASSUMED",
             "both bathrooms: upturn 0.20 m x 13.00 m = 2.60 m2 (WP-B), B 17.52 m2, 17.80 m2, 2 rolls each",
             "the sheet names the drawing file and its sha256; binding state NO_PROJECT_RULES"],
    "expected": {"binding": "NO_PROJECT_RULES", "sheet_names_drawing": True,
                 "BATH1": {"upturn_h_m": 0.2, "height_state": "OWNER_STANDARD_ASSUMED", "upturn_m2": 2.6,
                           "B_m2": 17.52, "consumed_m2": 17.8, "rolls": 2},
                 "BATH2": {"upturn_h_m": 0.2, "height_state": "OWNER_STANDARD_ASSUMED", "upturn_m2": 2.6,
                           "B_m2": 17.52, "consumed_m2": 17.8, "rolls": 2},
                 "row_status": {"S-UP-WP-003-upturn_h_m-WET": "OWNER_STANDARD_ASSUMED"}, "shared_rolls": 4},
}

RS_02 = {
    "id": "RS-02", "sequence": 2, "kind": "EXCEPTION",
    "title": "Scope: a 0.30 m upturn for BATH1 only; BATH2 keeps the 0.20 m standard",
    "proves": ["UP-RULES-001", "UP-WP-003"],
    "rules": {"schema": "URBAN_PROJECT_RULES_V1", "project_id": "SYNTHETIC PD-1", "drawing_revision": "PD-1 rev A",
              "drawing_sha256": THIS_DRAWING,
              "rules": [{"id": "PR-1", "rule_id": "UP-WP-003", "parameter": "upturn_h_m", "value": 0.3,
                         "scope": {"kind": "ROOM", "floor": "GF", "point_m": BATH1_POINT},
                         "source": {"kind": "DETAIL", "ref": "synthetic detail WP-03 (BATH1 shower)"}}]},
    "hand": [
        "PR-1 binds by its point (2.20, 1.60) to BATH1 only (ROOM scope outranks the PROJECT default)",
        "BATH1: upturn 13.00 x 0.30 = 3.90 m2 (PROJECT_SPECIFIED); BATH2: 13.00 x 0.20 = 2.60 m2 "
        "(OWNER_STANDARD_ASSUMED) - unchanged from WP-B",
        "BATH1 band = 0.30 + 0.10 lap = 0.40 m wide: 2 lanes per 1.00 m roll width + 0.20 m residue",
        "BATH1 ALONG_X: 4 strips 4.00 m (last 0.30): trim 0.70 -> 1 lane 0.40 x 4.00 + 0.30 x 4.00 residue "
        "(1.20 m2); doorway piece 1.00 x 0.30 from the lane (0.10 x 1.00 width trim), 3.00 left",
        "band 13.00 open: 3.00 (no lap), left 10.00 -> 2 x (L - 0.10) >= 10.00 -> L = 5.10 m; pieces 3.00 + 5.10 + "
        "5.10, 2 joints",
        "cuts 4 x 4.00 + 5.10 = 21.10 m -> at least 3 rolls; 5.10 + 4.00 | 4.00 + 4.00 | 4.00 -> 3",
        "laps 1.20 + 1.30 + 2 x 0.40 x 0.10 + 0.10 = 2.68 m2; B = 12.00 + 3.90 + 0.20 + 2.68 = 18.78 m2; waste "
        "21.10 - 18.78 = 2.32 m2 (1.20 + 0.10 + 0.20 x 5.10)",
        "ALONG_Y (5 strips 3.00 m): segment 2 x (L - 0.10) >= 11.00 -> 5.60 m, cuts 20.60 m, 3 rolls, seams 4 + 2 = "
        "6 vs ALONG_X 3 + 2 = 5 -> ALONG_X (fewest seams before least membrane: 0.50 m2 more)",
        "shared rolls (one system): BATH1 5.10, 4.00 x 4 + BATH2 3.00 x 5, 2.80 = 38.90 m -> at least 4: 5.10 + "
        "4.00 | 4.00 + 3.00 + 3.00 | 4.00 + 3.00 + 2.80 | 4.00 + 3.00 + 3.00 -> 4 (5 if bought per room)",
        "the 0.30 m upturn costs BATH1 one roll and 2.04 m2 more cutting waste than the 0.20 m standard (the 0.40 m "
        "band leaves a 0.20 m residue on every segment)",
    ],
    "expected": {"binding": "BOUND",
                 "BATH1": {"upturn_h_m": 0.3, "height_state": "PROJECT_SPECIFIED", "upturn_m2": 3.9, "B_m2": 18.78,
                           "consumed_m2": 21.1, "waste_m2": 2.32, "rolls": 3, "direction": "ALONG_X",
                           "band_w_m": 0.4, "lanes_per_width": 2},
                 "BATH2": {"upturn_h_m": 0.2, "height_state": "OWNER_STANDARD_ASSUMED", "upturn_m2": 2.6,
                           "B_m2": 17.52, "consumed_m2": 17.8, "waste_m2": 0.28, "rolls": 2, "direction": "ALONG_Y"},
                 "row_status": {"P-PR-1": "PROJECT_SPECIFIED"}, "bound_room": "BATH1", "shared_rolls": 4,
                 "rolls_if_each_alone": 5},
}

RS_03 = {
    "id": "RS-03", "sequence": 3, "kind": "CONFLICT",
    "title": "Conflict: two project rules of the same rank disagree on the upturn",
    "proves": ["UP-RULES-001", "UP-WP-003"],
    "rules": {"schema": "URBAN_PROJECT_RULES_V1", "project_id": "SYNTHETIC PD-1", "drawing_sha256": THIS_DRAWING,
              "rules": [{"id": "PR-1", "rule_id": "UP-WP-003", "parameter": "upturn_h_m", "value": 0.25,
                         "scope": {"kind": "PROJECT"}, "source": {"kind": "DETAIL", "ref": "detail WP-04"}},
                        {"id": "PR-2", "rule_id": "UP-WP-003", "parameter": "upturn_h_m", "value": 0.3,
                         "scope": {"kind": "PROJECT"}, "source": {"kind": "SPECIFICATION",
                                                                  "ref": "spec 07 10 00"}}]},
    "hand": ["PR-1 0.25 m (detail) and PR-2 0.30 m (specification), both PROJECT scope: same rank, different values -> "
             "CONFLICT_REVIEW; neither is applied and the Urban 0.20 m is not silently used either",
             "both bathrooms: the upturn is withheld (no height), the membrane layout is BLOCKED; A 12.00 m2 and the "
             "eligible length 13.00 m stay proven",
             "one question per conflict (row C-PR-1-PR-2) and an approval item for the project consultant"],
    "expected": {"binding": "BOUND",
                 "BATH1": {"upturn_h_m": None, "height_state": "CONFLICT_REVIEW", "upturn_m2": None,
                           "eligible_m": 13.0, "A_m2": 12.0, "layout_state": "BLOCKED"},
                 "BATH2": {"upturn_h_m": None, "height_state": "CONFLICT_REVIEW", "upturn_m2": None,
                           "layout_state": "BLOCKED"},
                 "row_status": {"P-PR-1": "CONFLICT_REVIEW", "P-PR-2": "CONFLICT_REVIEW",
                                "C-PR-1-PR-2": "CONFLICT_REVIEW"},
                 "conflict_questions": 1, "conflict_approvals": 1},
}

RS_04 = {
    "id": "RS-04", "sequence": 4, "kind": "EXCEPTION",
    "title": "Drawing binding: a rules file for another drawing is refused; an unbound file is flagged",
    "proves": ["UP-RULES-001"],
    "rules": dict(RS_02["rules"], drawing_sha256="0" * 64),
    "rules_unbound": {k: v for k, v in RS_02["rules"].items() if k != "drawing_sha256"},
    "hand": ["the rules sheet is tied to the drawing by its sha256 (and the stated drawing revision)",
             "a rules file naming another drawing's sha256: refused before any quantity "
             "(PROJECT_RULES_DRAWING_MISMATCH)",
             "a rules file naming no drawing: applied (BATH1 0.30 m as in RS-02) but flagged PROJECT_RULES_NOT_BOUND - "
             "an open item and an approval"],
    "expected": {"refused": True, "unbound_binding": "PROJECT_RULES_NOT_BOUND", "unbound_open_items": 1,
                 "unbound_BATH1_upturn_m2": 3.9},
}

RS_05 = {
    "id": "RS-05", "sequence": 5, "kind": "BOUNDARY",
    "title": "A changed rules sheet supersedes the earlier outputs",
    "proves": ["UP-RULES-001"],
    "rules": RS_02["rules"],
    "changed_value": 0.35,
    "hand": ["run 1: RS-02 (BATH1 0.30 m) into an output folder; run 2: the same file with 0.35 m into the same folder",
             "the rules hash changes -> the run-1 outputs move to SUPERSEDED_1 (never reused); invalidation "
             "RULES_CHANGED; BATH1 upturn 13.00 x 0.35 = 4.55 m2"],
    "expected": {"invalidation": "RULES_CHANGED", "superseded_folder": True, "BATH1_upturn_m2": 4.55},
}

RULES_CASES = [RS_01, RS_02, RS_03, RS_04, RS_05]
