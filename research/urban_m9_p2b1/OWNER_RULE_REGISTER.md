# Permanent owner-rule register (deliverable 3)

Generated from `knowledge/URBAN_ENGINEERING_KNOWLEDGE_1.0.0.json` (rule set `URBAN_KB_1.0.0`, digest `e97d01f4cac84d6e`; builder `tools/kb_build.py`). The JSON is the source of truth; this table is a view of it. Every rule names its authority, status, the code that applies it and the tests that prove it (`tests/m9_kb/test_kb_registry.py::test_every_code_and_test_link_exists` checks that every link exists).

25 records; statuses: OWNER_APPROVED 23, PROJECT_SPECIFIC 1, DEPRECATED 1

| Rule | Title | Status | Kind | Authority | Applied by | Proved by |
|---|---|---|---|---|---|---|
| PS-REF-001 | Reference project: a service corridor connecting separate building areas is outdoors | PROJECT_SPECIFIC | PROJECT_DECISION | owner master prompt 2026-10-14 (URBAN PROJECT AI - master engineering intelligence program) Part C section 9 | apply_decisions | test_a_project_decision_binds_one_space_only |
| UP-CEIL-001 | Ceilings: actual eligible surfaces only | OWNER_APPROVED | ENGINEERING_RULE | owner master prompt 2026-10-14 (URBAN PROJECT AI - master engineering intelligence program) Part D section 18; rules/methods URBAN-CEILING-QUANTITY-WITHOUT-MATERIAL@v1 | measure | test_double_height_ceiling_counted_once |
| UP-DOOR-AREA-001 | Door areas: as-drawn and owner-required, confirmed and assumed, never mixed | OWNER_APPROVED | OWNER_RULE | owner master prompt 2026-10-14 (URBAN PROJECT AI - master engineering intelligence program) Part C section 11, Part F section 25; owner correction 2026-10-14 (CRITICAL OWNER CORRECTION - door opening dimensions) | door_scenarios | test_scenario_areas_are_kept_apart |
| UP-DOOR-CLS-001 | Ordinary internal doors are PVC | OWNER_APPROVED | OWNER_RULE | owner door rules 2026-10-13 (engine/source/door_model.py DOOR_RULE_ID OWNER_DOOR_CLASSES_2026_10_13); owner master prompt 2026-10-14 (URBAN PROJECT AI - master engineering intelligence program) Part C section 8 | _classify; door_category | test_categories_follow_the_space_model; test_a_wall_gap_without_a_door_symbol_is_a_passage_not_a_door; test_a_door_symbol_with_no_wall_gap_is_never_measured |
| UP-DOOR-CLS-002 | Ordinary doors to genuine outdoor spaces are aluminium | OWNER_APPROVED | OWNER_RULE | owner door rules 2026-10-13 (engine/source/door_model.py DOOR_RULE_ID OWNER_DOOR_CLASSES_2026_10_13); owner master prompt 2026-10-14 (URBAN PROJECT AI - master engineering intelligence program) Part C section 9 | _classify; door_category | test_a_kitchen_door_to_outdoors_is_aluminium; test_a_pantry_door_to_an_indoor_corridor_stays_pvc; test_a_balcony_door_is_aluminium_and_the_balcony_is_waterproofed |
| UP-DOOR-CLS-003 | Bathroom doors: PVC material, bathroom opening standard | OWNER_APPROVED | OWNER_RULE | owner master prompt 2026-10-14 (URBAN PROJECT AI - master engineering intelligence program) Part C section 8; owner correction 2026-10-14 (CRITICAL OWNER CORRECTION - door opening dimensions) | door_category | test_the_owner_correction_table[bath-0.90] |
| UP-DOOR-CLS-004 | The main entrance is its own door category, measured as drawn | OWNER_APPROVED | OWNER_RULE | owner door rules 2026-10-13 (engine/source/door_model.py DOOR_RULE_ID OWNER_DOOR_CLASSES_2026_10_13); owner master prompt 2026-10-14 (URBAN PROJECT AI - master engineering intelligence program) Part C section 10; owner correction 2026-10-14 (CRITICAL OWNER CORRECTION - door opening dimensions) | main_entrance; required_opening | test_the_main_entrance_keeps_its_drawn_width; test_a_balcony_door_is_aluminium_and_the_balcony_is_waterproofed |
| UP-DOOR-CLS-005 | Elevator entrances are not ordinary doors | OWNER_APPROVED | OWNER_RULE | owner door rules 2026-10-13 (engine/source/door_model.py DOOR_RULE_ID OWNER_DOOR_CLASSES_2026_10_13); owner master prompt 2026-10-14 (URBAN PROJECT AI - master engineering intelligence program) Part C section 12 | lift_openings; lift_candidates; elevator_schedule | test_no_elevator_entrance_reaches_the_door_quantities |
| UP-DOOR-CLS-006 | One physical double-leaf door is one door set | OWNER_APPROVED | OWNER_RULE | owner door rules 2026-10-13 (engine/source/door_model.py DOOR_RULE_ID OWNER_DOOR_CLASSES_2026_10_13) | elements | test_a_double_leaf_door_is_one_door_assembly |
| UP-DOOR-DEP-001 | An enlarged opening changes other trades: listed for review, never auto-released | OWNER_APPROVED | ENGINEERING_RULE | owner master prompt 2026-10-14 (URBAN PROJECT AI - master engineering intelligence program) Part F section 26 | dependency_impacts | test_an_enlargement_lists_its_dependent_trades_and_releases_nothing |
| UP-DOOR-HGT-001 | Door heights: sources first, owner reference heights as labelled fallbacks | OWNER_APPROVED | OWNER_RULE | owner master prompt 2026-10-14 (URBAN PROJECT AI - master engineering intelligence program) Part C section 11 | door_height | test_a_schedule_height_wins_over_the_owner_fallback; test_an_owner_fallback_height_is_assumed_never_confirmed; test_an_assumption_is_never_released_as_confirmed |
| UP-DOOR-MIN-001 | Minimum door opening widths (master prompt Part C section 7) - SUPERSEDED | DEPRECATED (superseded by UP-DOOR-OPEN-002) | OWNER_RULE | owner master prompt 2026-10-14 (URBAN PROJECT AI - master engineering intelligence program) Part C section 7 | - | test_the_superseded_part_c_reading_is_not_applied |
| UP-DOOR-OPEN-002 | Required nominal door opening and architectural wall opening | OWNER_APPROVED | OWNER_RULE | owner correction 2026-10-14 (CRITICAL OWNER CORRECTION - door opening dimensions) | required_opening; door_scenarios | test_the_owner_correction_table; test_no_second_allowance_is_added; test_the_drawn_width_is_never_overwritten; test_conflicting_opening_dimensions_keep_both_values_and_hold_the_door; test_the_owner_required_view_never_reaches_the_boq_lines |
| UP-ELEV-SCHED-001 | Separate elevator quotation schedule | OWNER_APPROVED | OWNER_RULE | owner master prompt 2026-10-14 (URBAN PROJECT AI - master engineering intelligence program) Part C section 12 | elevator_schedule | test_the_elevator_schedule_uses_cad_geometry |
| UP-FIN-PAINT-001 | No paint over full-height porcelain; one finish per face | OWNER_APPROVED | OWNER_RULE | owner master prompt 2026-10-14 (URBAN PROJECT AI - master engineering intelligence program) Part D section 15 | finish_scope | test_wall_porcelain_runs_full_height_and_no_paint_band_is_asked |
| UP-FIN-PLASTER-001 | Door jamb and head plaster is measured from geometry | OWNER_APPROVED | OWNER_RULE | owner master prompt 2026-10-14 (URBAN PROJECT AI - master engineering intelligence program) Part D section 15; data/registry/URBAN_OWNER_METHOD_RULES.json URBAN-REVEAL-FINISH-METHOD (reveal default PLASTER) | jamb_plaster_lines | test_door_jamb_plaster_is_measured_and_provisional |
| UP-FIN-WALL-001 | Full-height wall porcelain in wet areas | OWNER_APPROVED | OWNER_RULE | owner master prompt 2026-10-14 (URBAN PROJECT AI - master engineering intelligence program) Part D sections 13, 15; rules/methods/URBAN_METHOD_REGISTER_V1.json URBAN-WET-WALL-TILE-FULL-HEIGHT@v1 | wall_tile_height | test_wall_porcelain_runs_full_height_and_no_paint_band_is_asked; test_an_explicit_lower_tile_height_wins_and_is_flagged |
| UP-KB-PREC-001 | Source authority hierarchy, and as-drawn kept apart from owner-required | OWNER_APPROVED | KNOWLEDGE_POLICY | owner master prompt 2026-10-14 (URBAN PROJECT AI - master engineering intelligence program) Part B section 5 | precedence_rank; door_scenarios | test_precedence_puts_drawing_evidence_above_owner_rules; test_the_drawn_width_is_never_overwritten; test_no_drawn_dimension_is_replaced; test_an_assumption_is_never_released_as_confirmed; test_v2_2_never_reads_the_registry |
| UP-KB-QUES-001 | Question policy: what may be asked of the owner | OWNER_APPROVED | KNOWLEDGE_POLICY | owner master prompt 2026-10-14 (URBAN PROJECT AI - master engineering intelligence program) Part A sections 2-3, Part E section 23 | classify_question; owner_questions | test_established_rules_are_never_asked; test_repeated_instances_are_grouped_into_one_question; test_engine_defects_are_never_owner_questions; test_every_catalogue_entry_is_reached_by_its_example; test_an_unknown_reason_is_reported_unclassified_never_dropped |
| UP-SKIRT-001 | Conventional skirting on eligible dry-room wall boundaries | OWNER_APPROVED | OWNER_RULE | owner master prompt 2026-10-14 (URBAN PROJECT AI - master engineering intelligence program) Part D section 14; rules/owner_library UP-CER-002, UP-CER-003; data/registry/URBAN_OWNER_METHOD_RULES.json URBAN-SKIRTING-OPENING-METHOD | measure; passage_jamb_skirting | test_a_dry_room_keeps_its_skirting; test_passage_jambs_are_skirted_provisionally |
| UP-SPACE-001 | Interior / exterior status from enclosure and connectivity, with evidence | OWNER_APPROVED | ENGINEERING_RULE | owner master prompt 2026-10-14 (URBAN PROJECT AI - master engineering intelligence program) Part A section 6, Part C section 8, Part E section 20 | build | test_indoor_and_outdoor_corridors_are_told_apart; test_an_unlabelled_space_is_never_assumed_interior; test_v2_3_is_invariant_under_moving_mirroring_and_turning |
| UP-SPACE-002 | Project-specific space decisions bind one space and are never generalized | OWNER_APPROVED | KNOWLEDGE_POLICY | owner master prompt 2026-10-14 (URBAN PROJECT AI - master engineering intelligence program) Part C section 9 | apply_decisions | test_a_project_decision_binds_one_space_only |
| UP-THR-001 | Wet-room doorways take a marble threshold; other doorways continue the floor porcelain | OWNER_APPROVED | OWNER_RULE | owner master prompt 2026-10-14 (URBAN PROJECT AI - master engineering intelligence program) Part D section 16; data/registry/URBAN_OWNER_METHOD_RULES.json URBAN-WET-SERVICE-MARBLE-THRESHOLD (Urban-wide); data/registry/OWNER_METHOD_FACTS.json#/facts/0 (floor continues through doorways) | threshold_lines | test_wet_doorways_take_a_marble_threshold_from_geometry; test_dry_doorways_continue_the_floor_porcelain_once; test_several_strip_faces_of_one_opening_make_one_line; test_a_door_closure_strip_asks_for_the_door_not_the_finish |
| UP-WET-001 | Owner wet areas and their finish scope | OWNER_APPROVED | OWNER_RULE | owner master prompt 2026-10-14 (URBAN PROJECT AI - master engineering intelligence program) Part D section 13; rules/methods/URBAN_METHOD_REGISTER_V1.json URBAN-WET-WALL-TILE-FULL-HEIGHT@v1; rules/methods/URBAN_METHOD_REGISTER_V3.json URBAN-NO-SKIRTING-FULL-TILE-WET@v1 | finish_scope | test_kitchen_pantry_and_ironing_rooms_take_the_wet_scope; test_wet_scope_never_spreads_to_an_open_plan_dry_space |
| UP-WP-ROOF-001 | Roofs and balconies are waterproofed under the default scope | OWNER_APPROVED | OWNER_RULE | owner master prompt 2026-10-14 (URBAN PROJECT AI - master engineering intelligence program) Part D section 17; rules/methods/URBAN_METHOD_REGISTER_V1.json URBAN-ROOF-WATERPROOF-UPTURN-200@v1 | exterior_wp_lines | test_balconies_get_provisional_waterproofing; test_a_balcony_door_is_aluminium_and_the_balcony_is_waterproofed |

## Rule logic (machine-readable records, abridged)

### PS-REF-001 - Reference project: a service corridor connecting separate building areas is outdoors

- Purpose: the owner's decision for one corridor of the reference project
- Scope: the reference project only; elements SPACE; locations OUTDOOR_SERVICE_CORRIDOR
- Logic: `{"binding": "PROJECT_SPECIFIC_UNBOUND in the public registry; the binding (floor + point) lives in the project's private decision file once the corridor is identified", "never": "applied to any other corridor or project", "statement": "the service corridor connecting separate building areas is outdoors"}`
- Limitations: the corridor is named by description, not by drawing reference: the binding needs a reviewer
- Dependent trades: OPENINGS; assumptions permitted: NONE

### UP-CEIL-001 - Ceilings: actual eligible surfaces only

- Purpose: no ceiling over voids, open-to-below, shafts or stair voids; no surface on two floors
- Scope: every room; elements CEILING; locations ALL
- Logic: `{"implemented_in": "ARCH_TAKEOFF_V2 and later (S5 double height, voids, stair wells, shafts)"}`
- Dependent trades: CEILING; assumptions permitted: NONE

### UP-DOOR-AREA-001 - Door areas: as-drawn and owner-required, confirmed and assumed, never mixed

- Purpose: door BOQ areas that show the drawing and the owner's requirement side by side
- Scope: every door with a width and a height; elements DOOR; locations ALL
- Logic: `{"as_drawn": "wall opening area = CAD wall opening x height", "formula": "DOOR_AREA_M2 = WIDTH_M x HEIGHT_M", "never": ["a fabricated confirmed area when either dimension is unresolved", "the two scenarios added together"], "owner_required": ["wall opening area = owner-required wall opening x height", "nominal door area = nominal door width x height"], "states": ["CONFIRMED (width and height from sources)", "ASSUMED (an assumed height)", "BLOCKED"]}`
- Dependent trades: OPENINGS; assumptions permitted: NONE

### UP-DOOR-CLS-001 - Ordinary internal doors are PVC

- Purpose: the owner's default door material for doors between spaces of the enclosed building
- Scope: every ordinary door that connects two spaces inside the enclosed building; elements DOOR; locations INTERIOR
- Exceptions: main entrance (UP-DOOR-CLS-004); elevator entrances (UP-DOOR-CLS-005); a project specification naming another material
- Logic: `{"boq_item": "DOOR.INTERNAL.PVC", "classification": "connectivity, never the symbol lying inside a drawing outline, a layer name or the swing direction", "material": "PVC"}`
- Dependent trades: OPENINGS; assumptions permitted: NONE

### UP-DOOR-CLS-002 - Ordinary doors to genuine outdoor spaces are aluminium

- Purpose: the owner's default material for doors that lead outdoors
- Scope: every ordinary door with an exterior space (or the facade) on one side and an interior space on the other; elements DOOR; locations FACADE; OUTDOOR_SERVICE_CORRIDOR; ROOF; COURTYARD; BALCONY
- Exceptions: the main entrance (UP-DOOR-CLS-004); a pantry or kitchen door into an enclosed interior corridor stays internal
- Logic: `{"boq_item": "DOOR.EXTERNAL.ALUMINIUM", "examples_of_outdoor_access": ["kitchen external access", "pantry external access", "outdoor service corridors", "driver-room access from outdoors", "diwaniya access from outdoors", "roof access", "courtyard access"], "material": "ALUMINIUM"}`
- Dependent trades: OPENINGS; ALUMINIUM; assumptions permitted: NONE

### UP-DOOR-CLS-003 - Bathroom doors: PVC material, bathroom opening standard

- Purpose: bathroom doors are internal doors for material, with their own (smaller) opening standard
- Scope: an internal door with a bathroom / W.C. space on one side; elements DOOR; locations BATHROOM
- Exceptions: a project specification naming another material or size; an accessible bathroom (clearance requirements are not covered by this rule: flagged)
- Logic: `{"boq_item": "DOOR.INTERNAL.PVC", "dimension_category": "BATHROOM_PVC", "material": "PVC"}`
- Dependent trades: OPENINGS; assumptions permitted: NONE

### UP-DOOR-CLS-004 - The main entrance is its own door category, measured as drawn

- Purpose: the first principal door into the main building is a separate item, larger and differently specified
- Scope: the main entrance of the main building; elements DOOR; locations ENTRANCE
- Logic: `{"boq_item": "DOOR.MAIN_ENTRANCE", "dimensions": "actual drawing dimensions and approved specifications; the ordinary PVC / aluminium opening standard is never applied", "examples_not_mandatory_widths_m": [2.0, 2.5], "never_also": ["PVC", "ALUMINIUM"]}`
- Limitations: a single-leaf main entrance is identified only through entrance evidence
- Dependent trades: OPENINGS; assumptions permitted: NONE

### UP-DOOR-CLS-005 - Elevator entrances are not ordinary doors

- Purpose: the elevator company supplies the landing doors; they are quoted on a separate elevator schedule
- Scope: every opening or door that serves an elevator landing; elements DOOR; OPENING; SHAFT; locations ELEVATOR_SHAFT
- Exceptions: a door beside a shaft is not automatically an elevator entrance
- Logic: `{"door_boq": "EXCLUDED (never PVC, aluminium or main entrance)", "lift_shaft_finishes": "excluded from room finishes", "schedule": "UP-ELEV-SCHED-001"}`
- Dependent trades: OPENINGS; ELEVATOR; assumptions permitted: NONE

### UP-DOOR-CLS-006 - One physical double-leaf door is one door set

- Purpose: never count leaves as door items
- Scope: every door element; elements DOOR; locations ALL
- Logic: `{"count": "1 per physical door element", "leaf_count": "recorded"}`
- Dependent trades: OPENINGS; assumptions permitted: NONE

### UP-DOOR-DEP-001 - An enlarged opening changes other trades: listed for review, never auto-released

- Purpose: show what an owner-required enlargement touches before anyone builds it
- Scope: every door with a required enlargement; elements DOOR; WALL; LINTEL; COLUMN; locations ALL
- Logic: `{"affected": {"blockwork deduction": "+enlargement x height", "door area": "+enlargement x height", "lintel": "span +enlargement (bearing to check)", "plaster / paint / wall tile deductions": "+enlargement x height per finished face", "reveals and jambs": "jamb surfaces move; head soffit +enlargement x wall thickness", "skirting": "-enlargement on each skirted side face", "structural interface": "a column or wall end within the enlargement blocks it: review", "threshold / doorway strip": "+enlargement x wall thickness"}, "release": "REVIEW_REQUIRED: indicative impacts only, no BOQ line changes"}`
- Dependent trades: MASONRY; PLASTER; PAINT; WALL_FINISH; FLOOR_FINISH; MARBLE; WATERPROOFING; CONCRETE; assumptions permitted: NONE

### UP-DOOR-HGT-001 - Door heights: sources first, owner reference heights as labelled fallbacks

- Purpose: door areas need a height; a verified height always wins, a fallback is never a measurement
- Scope: ordinary PVC / aluminium doors and the main entrance; elements DOOR; locations ALL
- Logic: `{"flags": ["HEIGHT_ASSUMED", "AREA_ASSUMED"], "main_entrance_note": "2.50 m is a possible fallback subject to project context: used only as ASSUMED with a review flag", "never": ["replace a verified height", "a confirmed area from an assumed height"], "order": ["door schedule", "section", "elevation", "explicit dimension", "project fallback (facts opening_heights.DOOR_ASSUMED)", "owner reference height"], "owner_reference_height_m": {"BATHROOM_PVC": 2.2, "EXTERNAL_ALUMINIUM": 2.2, "INTERNAL_PVC": 2.2, "MAIN_ENTRANCE": 2.5}}`
- Dependent trades: OPENINGS; assumptions permitted: the owner reference heights, labelled HEIGHT_ASSUMED

### UP-DOOR-MIN-001 - Minimum door opening widths (master prompt Part C section 7) - SUPERSEDED

- Purpose: historical record: the dimensional reading of Part C section 7 was replaced before implementation
- Scope: ordinary PVC / bathroom / aluminium doors; elements DOOR; locations ALL
- Logic: `{"superseded_reading": "OWNER_REQUIRED_WIDTH = max(DRAWN_OPENING_WIDTH, minimum 1.00 / 0.90 / 1.00 m) applied to the architectural wall opening", "why_superseded": "the owner distinguishes the nominal door opening from the architectural wall opening (nominal + 0.10 m); the minimums 1.00 / 0.90 / 1.00 are NOMINAL door openings"}`
- Dependent trades: OPENINGS; assumptions permitted: NONE

### UP-DOOR-OPEN-002 - Required nominal door opening and architectural wall opening

- Purpose: the owner orders doors of a required nominal size and builds the wall opening 0.10 m wider for installation / frame coordination; an undersized drawn opening is enlarged to that wall opening
- Scope: ordinary internal PVC, bathroom PVC and ordinary external aluminium doors; elements DOOR; locations INTERIOR; BATHROOM; FACADE
- Exceptions: main entrance: actual drawing dimensions and specifications (UP-DOOR-CLS-004); elevator entrances: excluded (UP-DOOR-CLS-005); an approved door schedule with another dimensional convention: recorded, conflict flagged
- Logic: `{"allowance_m": 0.1, "flag": "OPENING_BELOW_OWNER_STANDARD (enlargement > 1 mm)", "formulas": ["ARCHITECTURAL_WALL_OPENING = REQUIRED_NOMINAL_DOOR_OPENING + 0.10 m", "OWNER_REQUIRED_WALL_OPENING = max(CAD_WALL_OPENING, ARCHITECTURAL_WALL_OPENING)", "REQUIRED_ENLARGEMENT = OWNER_REQUIRED_WALL_OPENING - CAD_WALL_OPENING"], "kept_apart": ["CAD_WALL_OPENING", "REQUIRED_NOMINAL_DOOR_OPENING", "OWNER_REQUIRED_WALL_OPENING", "frame width (door block)", "nominal leaf width (swing radius, evidence only)", "finished clear passage width (not measured from a plan)"], "never": ["add another 0.10 m after applying the rule", "overwrite the CAD measurement", "treat the 0.10 m as a verified manufacturer installation requirement", "declare an enlarged opening buildable"], "nominal_door_for_a_larger_opening": "where the CAD wall opening already exceeds the architectural wall opening, the door that fits it `
- Examples: `[{"cad_m": 0.9, "category": "INTERNAL_PVC", "enlargement_m": 0.2, "required_wall_opening_m": 1.1}, {"cad_m": 0.9, "category": "BATHROOM_PVC", "enlargement_m": 0.1, "required_wall_opening_m": 1.0}, {"cad_m": 1.0, "category": "EXTERNAL_ALUMINIUM", "enlargement_m": 0.1, "required_wall_opening_m": 1.1}, {"cad_m": 1.2, "category": "INTERNAL_PVC", "enlargement_m": 0.0, "required_wall_opening_m": 1.2}, {"cad_m": 0.8, "category": "INTERNAL_PVC", "enlargement_m": 0.3, "required_wall_opening_m": 1.1}, {"cad_m": 0.75, "category": "INTERNAL_PVC", "enlargement_m": 0.35, "required_wall_opening_m": 1.1}, {"c`
- Limitations: accessibility, fire-safety and structural conditions are not checked: flagged only; the head height of the wall opening is not covered by the 0.10 m rule (width only)
- Dependent trades: OPENINGS; MASONRY; PLASTER; PAINT; WALL_FINISH; FLOOR_FINISH; MARBLE; WATERPROOFING; CONCRETE; assumptions permitted: the 0.10 m allowance is an owner planning rule; conflicts with shop drawings, structural constraints or manufacturer details are flagged
- Supersedes: UP-DOOR-MIN-001

### UP-ELEV-SCHED-001 - Separate elevator quotation schedule

- Purpose: the information the elevator company quotes from, kept out of the architectural door BOQ
- Scope: every shaft that may hold an elevator; elements SHAFT; OPENING; locations ELEVATOR_SHAFT
- Logic: `{"fields": ["shaft id", "shaft dimensions (CAD geometry)", "door-opening dimensions", "number of landings", "floors served", "number of elevators", "evidence source", "missing information"], "reference_shaft_m": [1.8, 1.8], "reference_use": "a comparison only; never an assumed shaft size", "status": ["CONFIRMED_LIFT (lift word / schedule / owner)", "CANDIDATE (stacked shaft with an opening)"]}`
- Dependent trades: ELEVATOR; assumptions permitted: NONE

### UP-FIN-PAINT-001 - No paint over full-height porcelain; one finish per face

- Purpose: never count paint and porcelain on the same wall face
- Scope: every wall face; elements WALL_FACE; locations ALL
- Logic: `{"dry": "plaster + paint", "substrate": "the cementitious substrate / plaster behind porcelain is its own line", "wet_full_height": "PAINT NOT_APPLICABLE_WITH_EVIDENCE"}`
- Dependent trades: PAINT; WALL_FINISH; PLASTER; assumptions permitted: NONE

### UP-FIN-PLASTER-001 - Door jamb and head plaster is measured from geometry

- Purpose: plaster around door frames may be needed for frame alignment; it is not omitted because a PVC frame is installed
- Scope: every door opening in a plastered wall; elements DOOR_JAMB; REVEAL; locations ALL
- Logic: `{"area": "2 jambs x wall thickness x door height + head soffit wall thickness x opening width", "never": ["porcelain because an adjacent room is wet", "one reveal in two room finishes"], "state": "PROVISIONAL (the frame detail decides how much of it is plastered)"}`
- Dependent trades: PLASTER; assumptions permitted: door height may be the owner fallback (then the line says HEIGHT_ASSUMED)

### UP-FIN-WALL-001 - Full-height wall porcelain in wet areas

- Purpose: the visible wall tile of a wet area runs to the finished ceiling
- Scope: the walls of owner wet areas; elements WALL_FACE; locations BATHROOM; KITCHEN; PANTRY; IRONING; LAUNDRY
- Logic: `{"height": "the room's established clear (ceiling) height: the same ladder as paint (engine/source/arch_measure.py heights, URBAN-PAINT-TO-FINISHED-CEILING)", "precedence": "an explicit wall-tile height from a drawing, schedule or project decision governs; a lower one is flagged WALL_TILE_BELOW_OWNER_FULL_HEIGHT and the band above stays a question", "unknown_height": "the area is BLOCKED (the height is a document request), the scope is not"}`
- Dependent trades: WALL_FINISH; assumptions permitted: NONE

### UP-KB-PREC-001 - Source authority hierarchy, and as-drawn kept apart from owner-required

- Purpose: decide which source establishes a physical fact, and never let an owner design requirement overwrite what the drawing shows
- Scope: every quantity, classification and dimension of every project; elements ALL; locations ALL
- Logic: `{"design_requirement": "an explicit owner-required minimum may set the REQUIRED value without changing the AS-DRAWN measurement; both are kept, each with its own source; the difference is a modification, never a correction of the drawing", "never": ["overwrite original evidence", "add the AS_DRAWN and OWNER_REQUIRED scenarios together", "release an owner-required quantity as measured"], "physical_fact_hierarchy": ["1 approved drawing dimensions and schedules", "2 approved project specifications and details", "3 verified geometric evidence", "4 project-specific owner decisions", "5 general owner rules", "6 labelled assumptions", "7 unresolved questions"], "scenarios": ["AS_DRAWN", "OWNER_REQUIRED", "UNRESOLVED"]}`
- Examples: `[{"as_drawn_m": 0.9, "case": "CAD opening 0.90 m, owner-required wall opening 1.10 m", "modification_m": 0.2, "owner_required_m": 1.1}]`
- Dependent trades: ALL; assumptions permitted: NONE

### UP-KB-QUES-001 - Question policy: what may be asked of the owner

- Purpose: stop asking answered questions, and stop reporting software failures as owner decisions
- Scope: every unresolved item the engine emits; elements ALL; locations ALL
- Logic: `{"before_asking": ["search the registry", "check project-specific decisions", "inspect the drawing and schedules", "check existing owner answers", "decide whether it is a software defect", "attempt safe evidence-based classification", "group repeated instances"], "categories": {"A_ESTABLISHED": "an approved rule applies: apply it, never ask", "B_MISSING_DRAWING_EVIDENCE": "a rule exists but the drawings do not show whether it applies: investigate geometry, connectivity, levels, annotations and other drawings; request the document (schedule, section, label), not a policy", "C_RULE_CONFLICT": "two approved rules, or a drawing and an owner requirement, disagree: keep both facts and explain the modification; ask only where precedence does not decide it", "D_MISSING_OWNER_POLICY": "no approved rule resolves it: the only category that is an owner question", "E_ENGINEERING_DEFECT": "the engine `
- Dependent trades: ALL; assumptions permitted: NONE

### UP-SKIRT-001 - Conventional skirting on eligible dry-room wall boundaries

- Purpose: skirting where it is built, measured along real wall faces at floor level
- Scope: dry rooms with a tiled floor; elements WALL_FACE; COLUMN_FACE; locations DRY_ROOMS
- Logic: `{"doorless_opening_jambs": "included by URBAN-SKIRTING-OPENING-METHOD; ARCH_TAKEOFF_V2.3 adds them as a PROVISIONAL line per passage", "eligible": "dry-room wall and column faces; not across door / passage openings", "never": ["a 50 / 50 allocation of uncertain edges", "omission because the drawing is complex", "an uncertain range converted to a confirmed quantity"], "separate_items": ["conventional skirting", "hidden skirting / profile system"], "uncertain": "a conservative released length plus an explicit range (F-17, ARCH_TAKEOFF_V2.2)"}`
- Dependent trades: FLOOR_FINISH; assumptions permitted: NONE

### UP-SPACE-001 - Interior / exterior status from enclosure and connectivity, with evidence

- Purpose: door materials and finish scopes depend on whether a space is inside the enclosed building
- Scope: every space of every floor; elements SPACE; ROOM; CORRIDOR; OUTDOOR_AREA; locations ALL
- Logic: `{"building_parts": "interior spaces joined by doors / passages form one building part per floor; an exterior space joining two parts is a connecting outdoor area", "evidence_order": ["project-specific decision binding the space (UP-SPACE-002)", "an exterior room word (balcony, terrace, roof, garden, court, pool)", "an interior room word (a room function implies an enclosed room)", "an unlabelled space with a doorless facade opening -> POSSIBLY_EXTERIOR", "otherwise UNKNOWN (never assumed interior)"], "never": ["a label alone defines every construction property", "an unlabelled corridor generalized as outdoors"], "statuses": ["INTERIOR", "EXTERIOR", "POSSIBLY_EXTERIOR", "UNKNOWN"]}`
- Dependent trades: OPENINGS; FLOOR_FINISH; WALL_FINISH; WATERPROOFING; assumptions permitted: NONE

### UP-SPACE-002 - Project-specific space decisions bind one space and are never generalized

- Purpose: apply an owner decision about one space exactly where it was given
- Scope: project decision files (URBAN_PROJECT_DECISIONS_V1); elements SPACE; locations ALL
- Logic: `{"binding": "floor + a point inside the space (drawing coordinates, m) or the space's room code; the decision applies to the space containing that point only", "file": "kept with the project's private inputs (never in the public repository)", "unbound": "a decision whose space is not identified is recorded PROJECT_SPECIFIC_UNBOUND and applies to nothing"}`
- Dependent trades: ALL; assumptions permitted: NONE

### UP-THR-001 - Wet-room doorways take a marble threshold; other doorways continue the floor porcelain

- Purpose: water containment at wet doorways; no unmeasured strip at any other doorway
- Scope: the doorway strip (wall thickness) of every door; elements DOOR_THRESHOLD; DOORWAY_STRIP; locations ALL
- Logic: `{"dry": {"count": "once, as its own line", "item": "FIN.FLOOR.PORCELAIN (doorway strip)"}, "never": ["an invented threshold depth", "the strip counted in two floors"], "wet": {"area": "length x depth", "depth": "the doorway strip depth (wall thickness, geometry)", "item": "FIN.MARBLE.THRESHOLD", "length": "clear door opening width (CAD)", "porcelain": "the strip is not in the adjacent room floors (deducted by construction)"}}`
- Dependent trades: MARBLE; FLOOR_FINISH; assumptions permitted: NONE

### UP-WET-001 - Owner wet areas and their finish scope

- Purpose: rooms where water is used receive floor porcelain, full-height wall porcelain and waterproofing; their tiled walls carry no conventional skirting
- Scope: enclosed rooms whose function is a wet area; elements ROOM; WALL_FACE; FLOOR; locations BATHROOM; KITCHEN; PANTRY; IRONING; LAUNDRY
- Exceptions: an American (open) pantry: a functional zone, never forced into a closed room (UP-PANTRY-001); laundry / washing rooms: wet where the project scope establishes it (kept wet, flagged); a project specification or approved detail stating another treatment
- Logic: `{"never": "wet finishes applied to adjacent dry spaces", "project_confirmation_codes": ["LAUNDRY"], "scope": {"floor": "porcelain (wet-area floor item)", "paint": "none over full-height porcelain (UP-FIN-PAINT-001)", "skirting": "none on fully porcelain-tiled faces (UP-CER-004)", "threshold": "marble at the doorway (UP-THR-001)", "walls": "full-height wall porcelain (UP-FIN-WALL-001)", "waterproofing": "floor + upturn + doorway continuation (UP-WP-001..003)"}, "wet_codes": ["BATHROOM", "KITCHEN", "PANTRY", "IRONING", "LAUNDRY"]}`
- Dependent trades: FLOOR_FINISH; WALL_FINISH; WATERPROOFING; PAINT; MARBLE; assumptions permitted: NONE

### UP-WP-ROOF-001 - Roofs and balconies are waterproofed under the default scope

- Purpose: exterior horizontal surfaces exposed to water
- Scope: balconies, terraces and roofs drawn as spaces; elements FLOOR; locations BALCONY; ROOF
- Logic: `{"area": "the drawn exterior space area", "state": "PROVISIONAL (membrane system and upturn by specification; one system never assumed for every location)"}`
- Dependent trades: WATERPROOFING; assumptions permitted: NONE

