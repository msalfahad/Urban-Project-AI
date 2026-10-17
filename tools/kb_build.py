"""KNOWLEDGE REGISTRY BUILDER (M9 Phase 2B-1) - the one place the engineering knowledge registry is written from:
every rule record, conflict, question pattern and owner question of knowledge/URBAN_ENGINEERING_KNOWLEDGE_1.0.0.json.

    python3 -I tools/kb_build.py            write the registry
    python3 -I tools/kb_build.py --check    exit 1 when the committed registry differs from a fresh build

A rule change is a change here (a new record version, its history entry), then --write, then tools/kb_index.py
--write; tests/m9_kb/test_kb_registry.py checks both are current. Stdlib only."""
import json
import sys
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "knowledge" / "URBAN_ENGINEERING_KNOWLEDGE_1.0.0.json"
D14 = "2026-10-14"
MP = "owner master prompt 2026-10-14 (URBAN PROJECT AI - master engineering intelligence program)"
OC = "owner correction 2026-10-14 (CRITICAL OWNER CORRECTION - door opening dimensions)"
DR13 = "owner door rules 2026-10-13 (engine/source/door_model.py DOOR_RULE_ID OWNER_DOOR_CLASSES_2026_10_13)"
T = "tests/m9_kb/"
H0 = [{"version": "1.0.0", "date": D14, "change": "first registry record (Phase 2B-1 knowledge audit)"}]


def rec(rule_id, title, *, purpose, scope, elements, locations=("ALL",), preconditions=(), exceptions=(),
        authority, status, logic, evidence=(), assumptions="NONE", conflicts=(), trades=(), tests=(), code=(),
        examples=(), limitations=(), history=None, supersedes=(), superseded_by=None, kind="OWNER_RULE",
        version="1.0.0"):
    return {"rule_id": rule_id, "title": title, "kind": kind, "purpose": purpose, "scope": scope,
            "elements": list(elements), "locations": list(locations), "preconditions": list(preconditions),
            "exceptions": list(exceptions), "authority": authority, "status": status, "effective_version": version,
            "logic": logic, "required_evidence": list(evidence), "assumptions_permitted": assumptions,
            "conflicts": list(conflicts), "dependent_trades": list(trades), "tests": list(tests), "code": list(code),
            "examples": list(examples), "limitations": list(limitations), "history": history or H0,
            "supersedes": list(supersedes), "superseded_by": superseded_by}


R = []
# ------------------------------------------------------------------------------------------------ precedence, questions
R.append(rec(
    "UP-KB-PREC-001", "Source authority hierarchy, and as-drawn kept apart from owner-required",
    kind="KNOWLEDGE_POLICY",
    purpose="decide which source establishes a physical fact, and never let an owner design requirement overwrite "
            "what the drawing shows",
    scope="every quantity, classification and dimension of every project", elements=["ALL"],
    authority={"kind": "OWNER", "source": MP + " Part B section 5", "received": D14},
    status="OWNER_APPROVED",
    logic={"physical_fact_hierarchy": [
        "1 approved drawing dimensions and schedules", "2 approved project specifications and details",
        "3 verified geometric evidence", "4 project-specific owner decisions", "5 general owner rules",
        "6 labelled assumptions", "7 unresolved questions"],
        "design_requirement": "an explicit owner-required minimum may set the REQUIRED value without changing the "
                              "AS-DRAWN measurement; both are kept, each with its own source; the difference is a "
                              "modification, never a correction of the drawing",
        "scenarios": ["AS_DRAWN", "OWNER_REQUIRED", "UNRESOLVED"], "never": [
            "overwrite original evidence", "add the AS_DRAWN and OWNER_REQUIRED scenarios together",
            "release an owner-required quantity as measured"]},
    evidence=["the source of each value (schedule, specification, geometry, decision, rule, assumption)"],
    trades=["ALL"], tests=[T + "test_kb_registry.py::test_precedence_puts_drawing_evidence_above_owner_rules",
                           T + "test_kb_door_standards.py::test_the_drawn_width_is_never_overwritten"],
    code=["engine/source/knowledge.py::precedence_rank", "engine/source/door_standards.py::door_scenarios"],
    examples=[{"case": "CAD opening 0.90 m, owner-required wall opening 1.10 m",
               "as_drawn_m": 0.90, "owner_required_m": 1.10, "modification_m": 0.20}]))
R.append(rec(
    "UP-KB-QUES-001", "Question policy: what may be asked of the owner", kind="KNOWLEDGE_POLICY",
    purpose="stop asking answered questions, and stop reporting software failures as owner decisions",
    scope="every unresolved item the engine emits", elements=["ALL"],
    authority={"kind": "OWNER", "source": MP + " Part A sections 2-3, Part E section 23", "received": D14},
    status="OWNER_APPROVED",
    logic={"categories": {
        "A_ESTABLISHED": "an approved rule applies: apply it, never ask",
        "B_MISSING_DRAWING_EVIDENCE": "a rule exists but the drawings do not show whether it applies: investigate "
                                      "geometry, connectivity, levels, annotations and other drawings; request the "
                                      "document (schedule, section, label), not a policy",
        "C_RULE_CONFLICT": "two approved rules, or a drawing and an owner requirement, disagree: keep both facts and "
                           "explain the modification; ask only where precedence does not decide it",
        "D_MISSING_OWNER_POLICY": "no approved rule resolves it: the only category that is an owner question",
        "E_ENGINEERING_DEFECT": "the engine cannot read the geometry or has not implemented an existing rule: an "
                                "engineering backlog item, never an owner question"},
        "before_asking": ["search the registry", "check project-specific decisions", "inspect the drawing and "
                          "schedules", "check existing owner answers", "decide whether it is a software defect",
                          "attempt safe evidence-based classification", "group repeated instances"],
        "each_question_shows": ["what was found", "the rule checked", "why it did not resolve the issue",
                                "the alternatives", "the BOQ quantities affected", "the engine's recommendation",
                                "whether work can continue safely without the answer"],
        "never_ask": ["whether ordinary internal doors are PVC", "whether elevator doors belong in the architectural "
                      "door count", "whether fully tiled wet rooms receive conventional skirting"]},
    trades=["ALL"], tests=[T + "test_kb_questions.py::test_established_rules_are_never_asked",
                           T + "test_kb_questions.py::test_repeated_instances_are_grouped_into_one_question",
                           T + "test_kb_questions.py::test_engine_defects_are_never_owner_questions"],
    code=["engine/source/knowledge.py::classify_question", "engine/source/knowledge.py::owner_questions"]))
# ------------------------------------------------------------------------------------------------ doors
DOOR_TESTS = T + "test_kb_door_standards.py::"
R.append(rec(
    "UP-DOOR-CLS-001", "Ordinary internal doors are PVC",
    purpose="the owner's default door material for doors between spaces of the enclosed building",
    scope="every ordinary door that connects two spaces inside the enclosed building",
    elements=["DOOR"], locations=["INTERIOR"],
    preconditions=["both sides of the door are spaces with INTERIOR status (space connectivity model, UP-SPACE-001)"],
    exceptions=["main entrance (UP-DOOR-CLS-004)", "elevator entrances (UP-DOOR-CLS-005)",
                "a project specification naming another material"],
    authority={"kind": "OWNER", "source": DR13 + "; " + MP + " Part C section 8", "received": "2026-10-13"},
    status="OWNER_APPROVED",
    logic={"material": "PVC", "boq_item": "DOOR.INTERNAL.PVC", "classification": "connectivity, never the symbol "
           "lying inside a drawing outline, a layer name or the swing direction"},
    evidence=["the two spaces joined by the door and their enclosure status"],
    conflicts=[{"with": "UP-SPACE-001", "note": "a space of UNKNOWN or POSSIBLY_EXTERIOR status makes the door "
                "CLASS_REVIEW (never PVC by default)"}],
    trades=["OPENINGS"], tests=[DOOR_TESTS + "test_categories_follow_the_space_model"],
    code=["engine/source/door_model.py::_classify", "engine/source/door_standards.py::door_category"],
    history=[{"version": "1.0.0", "date": "2026-10-13", "change": "owner door rule (code constant only)"},
             {"version": "1.0.0", "date": D14, "change": "first registry record; connectivity precondition stated"}]))
R.append(rec(
    "UP-DOOR-CLS-002", "Ordinary doors to genuine outdoor spaces are aluminium",
    purpose="the owner's default material for doors that lead outdoors",
    scope="every ordinary door with an exterior space (or the facade) on one side and an interior space on the other",
    elements=["DOOR"], locations=["FACADE", "OUTDOOR_SERVICE_CORRIDOR", "ROOF", "COURTYARD", "BALCONY"],
    preconditions=["one side is EXTERIOR by evidence: an exterior-coded space, nothing drawn beyond the facade, or "
                   "a project-specific decision binding that space as outdoors (UP-SPACE-002)"],
    exceptions=["the main entrance (UP-DOOR-CLS-004)",
                "a pantry or kitchen door into an enclosed interior corridor stays internal"],
    authority={"kind": "OWNER", "source": DR13 + "; " + MP + " Part C section 9", "received": "2026-10-13"},
    status="OWNER_APPROVED",
    logic={"material": "ALUMINIUM", "boq_item": "DOOR.EXTERNAL.ALUMINIUM",
           "examples_of_outdoor_access": ["kitchen external access", "pantry external access", "outdoor service "
                                          "corridors", "driver-room access from outdoors", "diwaniya access from "
                                          "outdoors", "roof access", "courtyard access"]},
    evidence=["exterior adjacency evidence, never the room name alone"],
    trades=["OPENINGS", "ALUMINIUM"], tests=[DOOR_TESTS + "test_a_kitchen_door_to_outdoors_is_aluminium",
                                             DOOR_TESTS + "test_a_pantry_door_to_an_indoor_corridor_stays_pvc"],
    code=["engine/source/door_model.py::_classify", "engine/source/door_standards.py::door_category"]))
R.append(rec(
    "UP-DOOR-CLS-003", "Bathroom doors: PVC material, bathroom opening standard",
    purpose="bathroom doors are internal doors for material, with their own (smaller) opening standard",
    scope="an internal door with a bathroom / W.C. space on one side", elements=["DOOR"], locations=["BATHROOM"],
    preconditions=["the door is internal (UP-DOOR-CLS-001)", "one side space carries the BATHROOM room code"],
    exceptions=["a project specification naming another material or size", "an accessible bathroom (clearance "
                "requirements are not covered by this rule: flagged)"],
    authority={"kind": "OWNER", "source": MP + " Part C section 8; " + OC, "received": D14},
    status="OWNER_APPROVED",
    logic={"material": "PVC", "boq_item": "DOOR.INTERNAL.PVC", "dimension_category": "BATHROOM_PVC"},
    trades=["OPENINGS"], tests=[DOOR_TESTS + "test_the_owner_correction_table[bath-0.90]"],
    code=["engine/source/door_standards.py::door_category"]))
R.append(rec(
    "UP-DOOR-CLS-004", "The main entrance is its own door category, measured as drawn",
    purpose="the first principal door into the main building is a separate item, larger and differently specified",
    scope="the main entrance of the main building", elements=["DOOR"], locations=["ENTRANCE"],
    preconditions=["identified by labels, exterior access, entrance sequence, topology, geometry, elevations or "
                   "schedules; a double-leaf symbol alone is not enough"],
    exceptions=[], authority={"kind": "OWNER", "source": DR13 + "; " + MP + " Part C section 10; " + OC,
                              "received": D14},
    status="OWNER_APPROVED",
    logic={"boq_item": "DOOR.MAIN_ENTRANCE", "dimensions": "actual drawing dimensions and approved specifications; "
           "the ordinary PVC / aluminium opening standard is never applied",
           "examples_not_mandatory_widths_m": [2.0, 2.5], "never_also": ["PVC", "ALUMINIUM"]},
    evidence=["entrance evidence (word, sequence, schedule); zero or several candidates -> a REVIEW finding"],
    trades=["OPENINGS"], tests=[DOOR_TESTS + "test_the_main_entrance_keeps_its_drawn_width"],
    code=["engine/source/door_model.py::main_entrance", "engine/source/door_standards.py::required_opening"],
    limitations=["a single-leaf main entrance is identified only through entrance evidence"]))
R.append(rec(
    "UP-DOOR-CLS-005", "Elevator entrances are not ordinary doors",
    purpose="the elevator company supplies the landing doors; they are quoted on a separate elevator schedule",
    scope="every opening or door that serves an elevator landing", elements=["DOOR", "OPENING", "SHAFT"],
    locations=["ELEVATOR_SHAFT"],
    preconditions=["a lift word, a lift schedule, a lift door block, or the owner confirms the landing; an opening "
                   "into a stacked shaft is a CANDIDATE until then"],
    exceptions=["a door beside a shaft is not automatically an elevator entrance"],
    authority={"kind": "OWNER", "source": DR13 + "; " + MP + " Part C section 12", "received": "2026-10-13"},
    status="OWNER_APPROVED",
    logic={"door_boq": "EXCLUDED (never PVC, aluminium or main entrance)", "schedule": "UP-ELEV-SCHED-001",
           "lift_shaft_finishes": "excluded from room finishes"},
    trades=["OPENINGS", "ELEVATOR"], tests=[DOOR_TESTS + "test_no_elevator_entrance_reaches_the_door_quantities"],
    code=["engine/source/door_model.py::lift_openings", "engine/source/door_model.py::lift_candidates",
          "engine/source/door_standards.py::elevator_schedule"]))
R.append(rec(
    "UP-DOOR-CLS-006", "One physical double-leaf door is one door set", purpose="never count leaves as door items",
    scope="every door element", elements=["DOOR"], authority={"kind": "OWNER", "source": DR13, "received": "2026-10-13"},
    status="OWNER_APPROVED", logic={"count": "1 per physical door element", "leaf_count": "recorded"},
    trades=["OPENINGS"], tests=["tests/m9_p2a/test_p2a_doors.py::test_a_double_leaf_door_is_one_door_assembly"],
    code=["engine/source/door_model.py::elements"]))
R.append(rec(
    "UP-DOOR-MIN-001", "Minimum door opening widths (master prompt Part C section 7) - SUPERSEDED",
    purpose="historical record: the dimensional reading of Part C section 7 was replaced before implementation",
    scope="ordinary PVC / bathroom / aluminium doors", elements=["DOOR"],
    authority={"kind": "OWNER", "source": MP + " Part C section 7", "received": D14}, status="DEPRECATED",
    logic={"superseded_reading": "OWNER_REQUIRED_WIDTH = max(DRAWN_OPENING_WIDTH, minimum 1.00 / 0.90 / 1.00 m) "
                                 "applied to the architectural wall opening",
           "why_superseded": "the owner distinguishes the nominal door opening from the architectural wall opening "
                             "(nominal + 0.10 m); the minimums 1.00 / 0.90 / 1.00 are NOMINAL door openings"},
    trades=["OPENINGS"], tests=[DOOR_TESTS + "test_the_superseded_part_c_reading_is_not_applied"],
    superseded_by="UP-DOOR-OPEN-002",
    history=[{"version": "1.0.0", "date": D14, "change": "received with the master prompt"},
             {"version": "1.0.0", "date": D14, "change": "DEPRECATED by the owner correction before implementation"}]))
R.append(rec(
    "UP-DOOR-OPEN-002", "Required nominal door opening and architectural wall opening",
    purpose="the owner orders doors of a required nominal size and builds the wall opening 0.10 m wider for "
            "installation / frame coordination; an undersized drawn opening is enlarged to that wall opening",
    scope="ordinary internal PVC, bathroom PVC and ordinary external aluminium doors", elements=["DOOR"],
    locations=["INTERIOR", "BATHROOM", "FACADE"],
    preconditions=["the door category is established (UP-DOOR-CLS-001..003)",
                   "the CAD architectural wall opening is measured jamb to jamb (or wall to wall for a provisional "
                   "door, which stays provisional)"],
    exceptions=["main entrance: actual drawing dimensions and specifications (UP-DOOR-CLS-004)",
                "elevator entrances: excluded (UP-DOOR-CLS-005)",
                "an approved door schedule with another dimensional convention: recorded, conflict flagged"],
    authority={"kind": "OWNER", "source": OC, "received": D14}, status="OWNER_APPROVED",
    logic={"table": {"INTERNAL_PVC": {"required_nominal_door_m": 1.00, "required_wall_opening_m": 1.10},
                     "BATHROOM_PVC": {"required_nominal_door_m": 0.90, "required_wall_opening_m": 1.00},
                     "EXTERNAL_ALUMINIUM": {"required_nominal_door_m": 1.00, "required_wall_opening_m": 1.10}},
           "allowance_m": 0.10,
           "formulas": ["ARCHITECTURAL_WALL_OPENING = REQUIRED_NOMINAL_DOOR_OPENING + 0.10 m",
                        "OWNER_REQUIRED_WALL_OPENING = max(CAD_WALL_OPENING, ARCHITECTURAL_WALL_OPENING)",
                        "REQUIRED_ENLARGEMENT = OWNER_REQUIRED_WALL_OPENING - CAD_WALL_OPENING"],
           "never": ["add another 0.10 m after applying the rule", "overwrite the CAD measurement",
                     "treat the 0.10 m as a verified manufacturer installation requirement",
                     "declare an enlarged opening buildable"],
           "flag": "OPENING_BELOW_OWNER_STANDARD (enlargement > 1 mm)",
           "kept_apart": ["CAD_WALL_OPENING", "REQUIRED_NOMINAL_DOOR_OPENING", "OWNER_REQUIRED_WALL_OPENING",
                          "frame width (door block)", "nominal leaf width (swing radius, evidence only)",
                          "finished clear passage width (not measured from a plan)"],
           "nominal_door_for_a_larger_opening": "where the CAD wall opening already exceeds the architectural wall "
                                                "opening, the door that fits it is (CAD opening - 0.10 m), recorded "
                                                "as RULE_DERIVED (a schedule overrides it)"},
    evidence=["CAD wall opening (band gap between jambs)", "door category"],
    assumptions="the 0.10 m allowance is an owner planning rule; conflicts with shop drawings, structural "
                "constraints or manufacturer details are flagged",
    conflicts=[{"with": "UP-DOOR-MIN-001", "resolution": "supersedes it"},
               {"with": "approved door schedule", "resolution": "the schedule establishes the nominal door and its "
                "convention (precedence 1); the owner rule then sets only the required wall opening; a disagreement "
                "is flagged DOOR_SCHEDULE_CONVENTION_CONFLICT"}],
    trades=["OPENINGS", "MASONRY", "PLASTER", "PAINT", "WALL_FINISH", "FLOOR_FINISH", "MARBLE", "WATERPROOFING",
            "CONCRETE"],
    tests=[DOOR_TESTS + "test_the_owner_correction_table", DOOR_TESTS + "test_no_second_allowance_is_added",
           DOOR_TESTS + "test_the_drawn_width_is_never_overwritten"],
    code=["engine/source/door_standards.py::required_opening", "engine/source/door_standards.py::door_scenarios"],
    examples=[{"category": "INTERNAL_PVC", "cad_m": 0.90, "required_wall_opening_m": 1.10, "enlargement_m": 0.20},
              {"category": "BATHROOM_PVC", "cad_m": 0.90, "required_wall_opening_m": 1.00, "enlargement_m": 0.10},
              {"category": "EXTERNAL_ALUMINIUM", "cad_m": 1.00, "required_wall_opening_m": 1.10,
               "enlargement_m": 0.10},
              {"category": "INTERNAL_PVC", "cad_m": 1.20, "required_wall_opening_m": 1.20, "enlargement_m": 0.00},
              {"category": "INTERNAL_PVC", "cad_m": 0.80, "required_wall_opening_m": 1.10, "enlargement_m": 0.30},
              {"category": "INTERNAL_PVC", "cad_m": 0.75, "required_wall_opening_m": 1.10, "enlargement_m": 0.35},
              {"category": "BATHROOM_PVC", "cad_m": 0.80, "required_wall_opening_m": 1.00, "enlargement_m": 0.20},
              {"category": "BATHROOM_PVC", "cad_m": 1.00, "required_wall_opening_m": 1.00, "enlargement_m": 0.00},
              {"category": "EXTERNAL_ALUMINIUM", "cad_m": 0.90, "required_wall_opening_m": 1.10,
               "enlargement_m": 0.20}],
    limitations=["accessibility, fire-safety and structural conditions are not checked: flagged only",
                 "the head height of the wall opening is not covered by the 0.10 m rule (width only)"],
    supersedes=["UP-DOOR-MIN-001"]))
R.append(rec(
    "UP-DOOR-HGT-001", "Door heights: sources first, owner reference heights as labelled fallbacks",
    purpose="door areas need a height; a verified height always wins, a fallback is never a measurement",
    scope="ordinary PVC / aluminium doors and the main entrance", elements=["DOOR"],
    authority={"kind": "OWNER", "source": MP + " Part C section 11", "received": D14}, status="OWNER_APPROVED",
    logic={"order": ["door schedule", "section", "elevation", "explicit dimension",
                     "project fallback (facts opening_heights.DOOR_ASSUMED)", "owner reference height"],
           "owner_reference_height_m": {"INTERNAL_PVC": 2.20, "BATHROOM_PVC": 2.20, "EXTERNAL_ALUMINIUM": 2.20,
                                        "MAIN_ENTRANCE": 2.50},
           "main_entrance_note": "2.50 m is a possible fallback subject to project context: used only as ASSUMED "
                                 "with a review flag",
           "flags": ["HEIGHT_ASSUMED", "AREA_ASSUMED"], "never": ["replace a verified height",
                                                                   "a confirmed area from an assumed height"]},
    assumptions="the owner reference heights, labelled HEIGHT_ASSUMED",
    conflicts=[{"with": "URBAN-WALL-FINISH-HEIGHT-METHOD", "resolution": "no conflict: that rule forbids a "
                "company-wide WALL FINISH height; these are door fallbacks, always labelled ASSUMED"}],
    trades=["OPENINGS"], tests=[DOOR_TESTS + "test_a_schedule_height_wins_over_the_owner_fallback",
                                DOOR_TESTS + "test_an_owner_fallback_height_is_assumed_never_confirmed"],
    code=["engine/source/door_standards.py::door_height"]))
R.append(rec(
    "UP-DOOR-AREA-001", "Door areas: as-drawn and owner-required, confirmed and assumed, never mixed",
    purpose="door BOQ areas that show the drawing and the owner's requirement side by side",
    scope="every door with a width and a height", elements=["DOOR"],
    authority={"kind": "OWNER", "source": MP + " Part C section 11, Part F section 25; " + OC, "received": D14},
    status="OWNER_APPROVED",
    logic={"formula": "DOOR_AREA_M2 = WIDTH_M x HEIGHT_M",
           "as_drawn": "wall opening area = CAD wall opening x height",
           "owner_required": ["wall opening area = owner-required wall opening x height",
                              "nominal door area = nominal door width x height"],
           "states": ["CONFIRMED (width and height from sources)", "ASSUMED (an assumed height)", "BLOCKED"],
           "never": ["a fabricated confirmed area when either dimension is unresolved",
                     "the two scenarios added together"]},
    trades=["OPENINGS"], tests=[DOOR_TESTS + "test_scenario_areas_are_kept_apart"],
    code=["engine/source/door_standards.py::door_scenarios"]))
R.append(rec(
    "UP-DOOR-DEP-001", "An enlarged opening changes other trades: listed for review, never auto-released",
    kind="ENGINEERING_RULE",
    purpose="show what an owner-required enlargement touches before anyone builds it",
    scope="every door with a required enlargement", elements=["DOOR", "WALL", "LINTEL", "COLUMN"],
    authority={"kind": "OWNER", "source": MP + " Part F section 26", "received": D14}, status="OWNER_APPROVED",
    logic={"affected": {"door area": "+enlargement x height", "blockwork deduction": "+enlargement x height",
                        "plaster / paint / wall tile deductions": "+enlargement x height per finished face",
                        "reveals and jambs": "jamb surfaces move; head soffit +enlargement x wall thickness",
                        "skirting": "-enlargement on each skirted side face",
                        "threshold / doorway strip": "+enlargement x wall thickness",
                        "lintel": "span +enlargement (bearing to check)",
                        "structural interface": "a column or wall end within the enlargement blocks it: review"},
           "release": "REVIEW_REQUIRED: indicative impacts only, no BOQ line changes"},
    trades=["MASONRY", "PLASTER", "PAINT", "WALL_FINISH", "FLOOR_FINISH", "MARBLE", "WATERPROOFING", "CONCRETE"],
    tests=[DOOR_TESTS + "test_an_enlargement_lists_its_dependent_trades_and_releases_nothing"],
    code=["engine/source/door_standards.py::dependency_impacts"]))
R.append(rec(
    "UP-ELEV-SCHED-001", "Separate elevator quotation schedule", purpose="the information the elevator company "
    "quotes from, kept out of the architectural door BOQ", scope="every shaft that may hold an elevator",
    elements=["SHAFT", "OPENING"], locations=["ELEVATOR_SHAFT"],
    authority={"kind": "OWNER", "source": MP + " Part C section 12", "received": D14}, status="OWNER_APPROVED",
    logic={"fields": ["shaft id", "shaft dimensions (CAD geometry)", "door-opening dimensions", "number of landings",
                      "floors served", "number of elevators", "evidence source", "missing information"],
           "reference_shaft_m": [1.80, 1.80], "reference_use": "a comparison only; never an assumed shaft size",
           "status": ["CONFIRMED_LIFT (lift word / schedule / owner)", "CANDIDATE (stacked shaft with an opening)"]},
    trades=["ELEVATOR"], tests=[DOOR_TESTS + "test_the_elevator_schedule_uses_cad_geometry"],
    code=["engine/source/door_standards.py::elevator_schedule"]))
# ------------------------------------------------------------------------------------------------ spaces
R.append(rec(
    "UP-SPACE-001", "Interior / exterior status from enclosure and connectivity, with evidence",
    kind="ENGINEERING_RULE",
    purpose="door materials and finish scopes depend on whether a space is inside the enclosed building",
    scope="every space of every floor", elements=["SPACE", "ROOM", "CORRIDOR", "OUTDOOR_AREA"],
    authority={"kind": "OWNER", "source": MP + " Part A section 6, Part C section 8, Part E section 20",
               "received": D14},
    status="OWNER_APPROVED",
    logic={"statuses": ["INTERIOR", "EXTERIOR", "POSSIBLY_EXTERIOR", "UNKNOWN"],
           "evidence_order": ["project-specific decision binding the space (UP-SPACE-002)",
                              "an exterior room word (balcony, terrace, roof, garden, court, pool)",
                              "an interior room word (a room function implies an enclosed room)",
                              "an unlabelled space with a doorless facade opening -> POSSIBLY_EXTERIOR",
                              "otherwise UNKNOWN (never assumed interior)"],
           "building_parts": "interior spaces joined by doors / passages form one building part per floor; an "
                             "exterior space joining two parts is a connecting outdoor area",
           "never": ["a label alone defines every construction property", "an unlabelled corridor generalized as "
                     "outdoors"]},
    trades=["OPENINGS", "FLOOR_FINISH", "WALL_FINISH", "WATERPROOFING"],
    tests=[T + "test_kb_space_model.py::test_indoor_and_outdoor_corridors_are_told_apart",
           T + "test_kb_space_model.py::test_an_unlabelled_space_is_never_assumed_interior"],
    code=["engine/source/space_model.py::build"]))
R.append(rec(
    "UP-SPACE-002", "Project-specific space decisions bind one space and are never generalized",
    kind="KNOWLEDGE_POLICY",
    purpose="apply an owner decision about one space exactly where it was given",
    scope="project decision files (URBAN_PROJECT_DECISIONS_V1)", elements=["SPACE"],
    authority={"kind": "OWNER", "source": MP + " Part C section 9", "received": D14}, status="OWNER_APPROVED",
    logic={"binding": "floor + a point inside the space (drawing coordinates, m) or the space's room code; the "
                      "decision applies to the space containing that point only",
           "unbound": "a decision whose space is not identified is recorded PROJECT_SPECIFIC_UNBOUND and applies to "
                      "nothing", "file": "kept with the project's private inputs (never in the public repository)"},
    trades=["ALL"], tests=[T + "test_kb_space_model.py::test_a_project_decision_binds_one_space_only"],
    code=["engine/source/space_model.py::apply_decisions"]))
R.append(rec(
    "PS-REF-001", "Reference project: a service corridor connecting separate building areas is outdoors",
    kind="PROJECT_DECISION",
    purpose="the owner's decision for one corridor of the reference project",
    scope="the reference project only", elements=["SPACE"], locations=["OUTDOOR_SERVICE_CORRIDOR"],
    authority={"kind": "OWNER_PROJECT", "source": MP + " Part C section 9", "received": D14},
    status="PROJECT_SPECIFIC",
    logic={"statement": "the service corridor connecting separate building areas is outdoors",
           "binding": "PROJECT_SPECIFIC_UNBOUND in the public registry; the binding (floor + point) lives in the "
                      "project's private decision file once the corridor is identified",
           "never": "applied to any other corridor or project"},
    trades=["OPENINGS"], tests=[T + "test_kb_space_model.py::test_a_project_decision_binds_one_space_only"],
    code=["engine/source/space_model.py::apply_decisions"],
    limitations=["the corridor is named by description, not by drawing reference: the binding needs a reviewer"]))
# ------------------------------------------------------------------------------------------------ wet areas, finishes
WT = T + "test_kb_finish_scope.py::"
R.append(rec(
    "UP-WET-001", "Owner wet areas and their finish scope",
    purpose="rooms where water is used receive floor porcelain, full-height wall porcelain and waterproofing; "
            "their tiled walls carry no conventional skirting",
    scope="enclosed rooms whose function is a wet area", elements=["ROOM", "WALL_FACE", "FLOOR"],
    locations=["BATHROOM", "KITCHEN", "PANTRY", "IRONING", "LAUNDRY"],
    preconditions=["the room is a closed room (ROOM, or one function only); an open-plan face that joins a wet "
                   "function with a dry one is not given the wet scope (zone extent needed)"],
    exceptions=["an American (open) pantry: a functional zone, never forced into a closed room (UP-PANTRY-001)",
                "laundry / washing rooms: wet where the project scope establishes it (kept wet, flagged)",
                "a project specification or approved detail stating another treatment"],
    authority={"kind": "OWNER", "source": MP + " Part D section 13; rules/methods/URBAN_METHOD_REGISTER_V1.json "
               "URBAN-WET-WALL-TILE-FULL-HEIGHT@v1; rules/methods/URBAN_METHOD_REGISTER_V3.json "
               "URBAN-NO-SKIRTING-FULL-TILE-WET@v1", "received": D14},
    status="OWNER_APPROVED",
    logic={"wet_codes": ["BATHROOM", "KITCHEN", "PANTRY", "IRONING", "LAUNDRY"],
           "project_confirmation_codes": ["LAUNDRY"],
           "scope": {"floor": "porcelain (wet-area floor item)", "walls": "full-height wall porcelain (UP-FIN-WALL-001)",
                     "waterproofing": "floor + upturn + doorway continuation (UP-WP-001..003)",
                     "skirting": "none on fully porcelain-tiled faces (UP-CER-004)",
                     "paint": "none over full-height porcelain (UP-FIN-PAINT-001)",
                     "threshold": "marble at the doorway (UP-THR-001)"},
           "never": "wet finishes applied to adjacent dry spaces"},
    conflicts=[{"with": "engine/source/arch_rooms.py LEXICON (kitchen / pantry / ironing are SERVICE = dry)",
                "resolution": "ARCH_TAKEOFF_V2.3 applies the owner wet scope; V1 .. V2.2 stay frozen (category E: an "
                              "existing rule not implemented)"},
               {"with": "UP-CER-009 (wall tile height derived per face, never a universal constant)",
                "resolution": "no conflict: full height is the face's own established clear height, not a constant"}],
    trades=["FLOOR_FINISH", "WALL_FINISH", "WATERPROOFING", "PAINT", "MARBLE"],
    tests=[WT + "test_kitchen_pantry_and_ironing_rooms_take_the_wet_scope",
           WT + "test_wet_scope_never_spreads_to_an_open_plan_dry_space"],
    code=["engine/source/owner_finish_scope.py::finish_scope"]))
R.append(rec(
    "UP-FIN-WALL-001", "Full-height wall porcelain in wet areas",
    purpose="the visible wall tile of a wet area runs to the finished ceiling",
    scope="the walls of owner wet areas", elements=["WALL_FACE"], locations=["BATHROOM", "KITCHEN", "PANTRY",
                                                                           "IRONING", "LAUNDRY"],
    authority={"kind": "OWNER", "source": MP + " Part D sections 13, 15; rules/methods/URBAN_METHOD_REGISTER_V1.json "
               "URBAN-WET-WALL-TILE-FULL-HEIGHT@v1", "received": D14},
    status="OWNER_APPROVED",
    logic={"height": "the room's established clear (ceiling) height: the same ladder as paint "
                     "(engine/source/arch_measure.py heights, URBAN-PAINT-TO-FINISHED-CEILING)",
           "precedence": "an explicit wall-tile height from a drawing, schedule or project decision governs; a lower "
                         "one is flagged WALL_TILE_BELOW_OWNER_FULL_HEIGHT and the band above stays a question",
           "unknown_height": "the area is BLOCKED (the height is a document request), the scope is not"},
    trades=["WALL_FINISH"], tests=[WT + "test_wall_porcelain_runs_full_height_and_no_paint_band_is_asked",
                                   WT + "test_an_explicit_lower_tile_height_wins_and_is_flagged"],
    code=["engine/source/owner_finish_scope.py::wall_tile_height"]))
R.append(rec(
    "UP-FIN-PAINT-001", "No paint over full-height porcelain; one finish per face",
    purpose="never count paint and porcelain on the same wall face", scope="every wall face",
    elements=["WALL_FACE"], authority={"kind": "OWNER", "source": MP + " Part D section 15", "received": D14},
    status="OWNER_APPROVED",
    logic={"wet_full_height": "PAINT NOT_APPLICABLE_WITH_EVIDENCE", "dry": "plaster + paint",
           "substrate": "the cementitious substrate / plaster behind porcelain is its own line"},
    trades=["PAINT", "WALL_FINISH", "PLASTER"], tests=[WT + "test_wall_porcelain_runs_full_height_and_no_paint_band_is_asked"],
    code=["engine/source/owner_finish_scope.py::finish_scope"]))
R.append(rec(
    "UP-FIN-PLASTER-001", "Door jamb and head plaster is measured from geometry",
    purpose="plaster around door frames may be needed for frame alignment; it is not omitted because a PVC frame "
            "is installed", scope="every door opening in a plastered wall", elements=["DOOR_JAMB", "REVEAL"],
    authority={"kind": "OWNER", "source": MP + " Part D section 15; data/registry/URBAN_OWNER_METHOD_RULES.json "
               "URBAN-REVEAL-FINISH-METHOD (reveal default PLASTER)", "received": D14},
    status="OWNER_APPROVED",
    logic={"area": "2 jambs x wall thickness x door height + head soffit wall thickness x opening width",
           "state": "PROVISIONAL (the frame detail decides how much of it is plastered)",
           "never": ["porcelain because an adjacent room is wet", "one reveal in two room finishes"]},
    assumptions="door height may be the owner fallback (then the line says HEIGHT_ASSUMED)",
    trades=["PLASTER"], tests=[WT + "test_door_jamb_plaster_is_measured_and_provisional"],
    code=["engine/source/owner_finish_scope.py::jamb_plaster_lines"]))
R.append(rec(
    "UP-SKIRT-001", "Conventional skirting on eligible dry-room wall boundaries",
    purpose="skirting where it is built, measured along real wall faces at floor level",
    scope="dry rooms with a tiled floor", elements=["WALL_FACE", "COLUMN_FACE"], locations=["DRY_ROOMS"],
    authority={"kind": "OWNER", "source": MP + " Part D section 14; rules/owner_library UP-CER-002, UP-CER-003; "
               "data/registry/URBAN_OWNER_METHOD_RULES.json URBAN-SKIRTING-OPENING-METHOD", "received": D14},
    status="OWNER_APPROVED",
    logic={"eligible": "dry-room wall and column faces; not across door / passage openings",
           "uncertain": "a conservative released length plus an explicit range (F-17, ARCH_TAKEOFF_V2.2)",
           "never": ["a 50 / 50 allocation of uncertain edges", "omission because the drawing is complex",
                     "an uncertain range converted to a confirmed quantity"],
           "separate_items": ["conventional skirting", "hidden skirting / profile system"],
           "doorless_opening_jambs": "included by URBAN-SKIRTING-OPENING-METHOD; ARCH_TAKEOFF_V2.3 adds them as a "
                                     "PROVISIONAL line per passage"},
    trades=["FLOOR_FINISH"], tests=[WT + "test_a_dry_room_keeps_its_skirting", WT + "test_passage_jambs_are_skirted_provisionally"],
    code=["engine/source/arch_measure.py::measure", "engine/source/owner_finish_scope.py::passage_jamb_skirting"]))
R.append(rec(
    "UP-THR-001", "Wet-room doorways take a marble threshold; other doorways continue the floor porcelain",
    purpose="water containment at wet doorways; no unmeasured strip at any other doorway",
    scope="the doorway strip (wall thickness) of every door", elements=["DOOR_THRESHOLD", "DOORWAY_STRIP"],
    authority={"kind": "OWNER", "source": MP + " Part D section 16; data/registry/URBAN_OWNER_METHOD_RULES.json "
               "URBAN-WET-SERVICE-MARBLE-THRESHOLD (Urban-wide); data/registry/OWNER_METHOD_FACTS.json#/facts/0 "
               "(floor continues through doorways)", "received": D14},
    status="OWNER_APPROVED",
    logic={"wet": {"item": "FIN.MARBLE.THRESHOLD", "length": "clear door opening width (CAD)",
                   "depth": "the doorway strip depth (wall thickness, geometry)", "area": "length x depth",
                   "porcelain": "the strip is not in the adjacent room floors (deducted by construction)"},
           "dry": {"item": "FIN.FLOOR.PORCELAIN (doorway strip)", "count": "once, as its own line"},
           "never": ["an invented threshold depth", "the strip counted in two floors"]},
    conflicts=[{"with": "data/registry/OWNER_METHOD_FACTS.json#/facts/2 (marble only if explicit, one other "
                "project)", "resolution": "project-specific for that project's revision only; the later Urban-wide "
                "rule and the master prompt govern every other project"},
               {"with": "URBAN-WET-SERVICE-MARBLE-THRESHOLD not_applicable_to pantry",
                "resolution": "CONFLICTED (CF-03): ARCH_TAKEOFF_V2.3 measures a pantry doorway threshold as "
                              "PROVISIONAL with the conflict named; owner question OQ-01"}],
    trades=["MARBLE", "FLOOR_FINISH"], tests=[WT + "test_wet_doorways_take_a_marble_threshold_from_geometry",
                                              WT + "test_dry_doorways_continue_the_floor_porcelain_once"],
    code=["engine/source/owner_finish_scope.py::threshold_lines"]))
R.append(rec(
    "UP-WP-ROOF-001", "Roofs and balconies are waterproofed under the default scope",
    purpose="exterior horizontal surfaces exposed to water", scope="balconies, terraces and roofs drawn as spaces",
    elements=["FLOOR"], locations=["BALCONY", "ROOF"],
    authority={"kind": "OWNER", "source": MP + " Part D section 17; rules/methods/URBAN_METHOD_REGISTER_V1.json "
               "URBAN-ROOF-WATERPROOF-UPTURN-200@v1", "received": D14},
    status="OWNER_APPROVED",
    logic={"area": "the drawn exterior space area", "state": "PROVISIONAL (membrane system and upturn by "
           "specification; one system never assumed for every location)"},
    trades=["WATERPROOFING"], tests=[WT + "test_balconies_get_provisional_waterproofing"],
    code=["engine/source/owner_finish_scope.py::exterior_wp_lines"]))
R.append(rec(
    "UP-CEIL-001", "Ceilings: actual eligible surfaces only", kind="ENGINEERING_RULE",
    purpose="no ceiling over voids, open-to-below, shafts or stair voids; no surface on two floors",
    scope="every room", elements=["CEILING"],
    authority={"kind": "OWNER", "source": MP + " Part D section 18; rules/methods URBAN-CEILING-QUANTITY-WITHOUT-MATERIAL@v1",
               "received": D14}, status="OWNER_APPROVED",
    logic={"implemented_in": "ARCH_TAKEOFF_V2 and later (S5 double height, voids, stair wells, shafts)"},
    trades=["CEILING"], tests=["tests/m9_s5/test_s5_ceilings_wp.py::test_double_height_ceiling_counted_once"], code=["engine/source/arch_measure.py::measure"]))

CONFLICTS = [
    {"id": "CF-01", "between": ["UP-DOOR-MIN-001", "UP-DOOR-OPEN-002"], "state": "RESOLVED",
     "resolution": "the owner correction supersedes the Part C section 7 dimensional reading"},
    {"id": "CF-02", "between": ["data/registry/OWNER_METHOD_FACTS.json#/facts/2", "URBAN-WET-SERVICE-MARBLE-THRESHOLD",
                                "UP-THR-001"], "state": "RESOLVED",
     "resolution": "the 'marble only if explicit' fact is project-specific (one other project's revision); the "
                   "Urban-wide rule and the master prompt govern the reference project and new projects"},
    {"id": "CF-03", "between": ["URBAN-WET-SERVICE-MARBLE-THRESHOLD (pantry not applicable)", "UP-WET-001 (pantry is "
                                "wet)", "UP-THR-001"], "state": "CONFLICTED",
     "resolution": "wet scope applies to an enclosed pantry; its doorway threshold is measured PROVISIONAL with the "
                   "conflict named; owner question OQ-01"},
    {"id": "CF-04", "between": ["URBAN-WET-WALL-TILE-FULL-HEIGHT@v1", "UP-CER-009"], "state": "RESOLVED",
     "resolution": "full height is the face's own derived clear height (UP-FIN-WALL-001); no universal constant"},
    {"id": "CF-05", "between": ["data/registry/OWNER_METHOD_FACTS.json#/facts/1 (dry / wet split at the door plane)",
                                "UP-THR-001"], "state": "RESOLVED",
     "resolution": "where a marble threshold is built the wet and dry floors end at the marble; the door-plane "
                   "split is that other project's own method"},
    {"id": "CF-06", "between": ["UP-DOOR-MIN-001 main entrance 1.00 m minimum", "UP-DOOR-CLS-004"],
     "state": "RESOLVED", "resolution": "the main entrance is measured as drawn and specified (owner correction)"},
    {"id": "CF-07", "between": ["arch_rooms LEXICON LAUNDRY = WET", "UP-WET-001 laundry project-specific"],
     "state": "RESOLVED", "resolution": "laundry keeps the wet scope with the flag WET_SCOPE_PROJECT_CONFIRMATION"},
    {"id": "CF-08", "between": ["URBAN-SKIRTING-OPENING-METHOD (doorless-opening jambs skirted)",
                                "arch_measure skirting (passage jambs never skirted)"], "state": "RESOLVED",
     "resolution": "category E: the rule was not implemented; ARCH_TAKEOFF_V2.3 adds PROVISIONAL passage-jamb "
                   "skirting"},
    {"id": "CF-09", "between": ["UP-WP-002 v2.0.0 (0.20 m upturn)", "engine/source/waterproofing_policy.py wet() "
                                "(0.15 m, the 1.4.0 value)"], "state": "RESOLVED",
     "resolution": "the 1.5.0 owner decision (0.20 m) governs the M9 route; the lab policy keeps its frozen value"},
    {"id": "CF-10", "between": ["facts opening_heights.DOOR_ASSUMED (project fallback)", "UP-DOOR-HGT-001 owner "
                                "reference heights"], "state": "RESOLVED",
     "resolution": "the project fallback (precedence 4) is used before the general owner reference (5)"},
    {"id": "CF-11", "between": ["UP-DOOR-OPEN-002 (width + 0.10 m)", "wall-opening head height"], "state": "OPEN",
     "resolution": "the rule covers the width only; the head allowance of the wall opening is not an owner rule: "
                   "owner question OQ-02 (the head is taken at the door height, ASSUMED)"},
]

QUESTIONS = [
    # pattern on the start of an unresolved reason (or its item) -> category, group key, governing rule
    {"pattern": r"^THRESHOLD_FINISH_NOT_ESTABLISHED", "category": "A_ESTABLISHED", "group": "DOORWAY_STRIP_FINISH",
     "rule": "UP-THR-001", "resolved_in": "ARCH_TAKEOFF_V2.3", "history": ["Q-S6-1", "O4", "OD-8"]},
    {"pattern": r"^UP-CER-004", "category": "A_ESTABLISHED", "group": "WET_ROOM_SKIRTING", "rule": "UP-WET-001",
     "resolved_in": "ARCH_TAKEOFF_V2.3", "history": ["ORR-008", "Q7", "O5"]},
    {"pattern": r"^FINISH_ABOVE_WALL_TILE_NOT_ESTABLISHED", "category": "A_ESTABLISHED",
     "group": "WET_ROOM_WALL_TILE_HEIGHT", "rule": "UP-FIN-WALL-001", "resolved_in": "ARCH_TAKEOFF_V2.3",
     "history": ["Q7", "O5", "S6R-B4", "OD-9"]},
    {"pattern": r"^MISSING_SOURCE", "item": r"^DOOR HEIGHTS", "category": "A_ESTABLISHED", "group": "DOOR_HEIGHT",
     "rule": "UP-DOOR-HGT-001", "resolved_in": "ARCH_TAKEOFF_V2.3 (ASSUMED)", "history": ["DR-07"]},
    {"pattern": r"^WALL_FINISH_HEIGHT_NOT_ESTABLISHED", "category": "B_MISSING_DRAWING_EVIDENCE",
     "group": "WALL_FINISH_HEIGHTS", "rule": "URBAN-WALL-FINISH-HEIGHT-METHOD",
     "request": "sections / schedules or the filled heights facts template (FACTS_TEMPLATE_HEIGHTS.json)",
     "history": ["O8", "OD-6"]},
    {"pattern": r"^(PLASTER|PAINT|WALL_TILE) net is a range", "category": "B_MISSING_DRAWING_EVIDENCE",
     "group": "FACE_OPENING_DEDUCTION", "rule": "UP-GEN-003",
     "request": "door closure and glazing positions (door schedule / elevations); owner rule OD-7 if none",
     "history": ["F-26", "OD-7"]},
    {"pattern": r"^WINDOW_REVEAL_FLOOR_STATUS_NOT_ESTABLISHED", "category": "B_MISSING_DRAWING_EVIDENCE",
     "group": "WINDOW_TYPE_AND_SILL", "rule": "URBAN-REVEAL-FINISH-METHOD",
     "request": "window schedule / elevations (sill or floor-level glazing)", "history": ["SE-01", "OD-11", "O8"]},
    {"pattern": r"^F-17", "category": "B_MISSING_DRAWING_EVIDENCE", "group": "WINDOW_TYPE_AND_SILL",
     "rule": "UP-SKIRT-001", "request": "window schedule / elevations", "history": ["BA-12", "OD-1"]},
    {"pattern": r"^FLOOR_FINISH_SPEC_NOT_ESTABLISHED", "category": "B_MISSING_DRAWING_EVIDENCE",
     "group": "FLOOR_FINISH_SPECIFICATION", "rule": "UP-CER-010",
     "request": "the project finish specification (selected tile sizes)"},
    {"pattern": r"^STAIR_(?!HALL_FINISH)", "category": "B_MISSING_DRAWING_EVIDENCE", "group": "STAIR_SECTIONS",
     "rule": "UP-STAIR-002", "request": "stair sections / rise and riser count"},
    {"pattern": r"^BLOCK_WALL_NOT_ESTABLISHED", "category": "B_MISSING_DRAWING_EVIDENCE",
     "group": "BLOCKWORK_SPECIFICATION", "rule": "UP-GEN-001", "request": "block material and wall heights"},
    {"pattern": r"^(UNLABELLED_SPACE|MERGED_SPACE|MIXED_SPACE|ATTACHED_THROUGH_OPEN_PASSAGE|ZONE_FROM_DRAWN_LINES)",
     "category": "B_MISSING_DRAWING_EVIDENCE", "group": "SPACE_IDENTITY", "rule": "UP-SPACE-001",
     "request": "room labels / the architect's room schedule"},
    {"pattern": r"^ROOM_TYPE_FROM_STACKED_FOOTPRINT", "category": "B_MISSING_DRAWING_EVIDENCE",
     "group": "LIFT_IDENTITY", "rule": "UP-DOOR-CLS-005", "request": "lift label or lift schedule"},
    {"pattern": r"^STAIRWELL_CEILING_SCOPE_NOT_ESTABLISHED", "category": "B_MISSING_DRAWING_EVIDENCE",
     "group": "STAIR_SECTIONS", "rule": "UP-CEIL-001", "request": "stair section / ceiling plan"},
    {"pattern": r"^STAIR_HALL_FINISH_NOT_ESTABLISHED", "category": "D_MISSING_OWNER_POLICY",
     "group": "STAIR_HALL_FINISHES", "rule": None, "question_id": "OQ-03", "history": ["Q-S6-4", "O6", "OD-10"]},
    {"pattern": r"^EXTERIOR_FINISH_SCOPE_NOT_ESTABLISHED", "category": "D_MISSING_OWNER_POLICY",
     "group": "EXTERIOR_SCOPE", "rule": None, "question_id": "OQ-04", "history": ["Q1", "O7"]},
    {"pattern": r"^STRIP_NOT_ATTRIBUTED", "category": "E_ENGINEERING_DEFECT", "group": "STRIP_ATTRIBUTION",
     "rule": "UP-THR-001"},
    {"pattern": r"^GEOMETRY_INCONSISTENT", "category": "E_ENGINEERING_DEFECT", "group": "GEOMETRY_CHECKS",
     "rule": "UP-KB-PREC-001"},
    {"pattern": r"^(WARNING|ENGINEERING)", "category": "E_ENGINEERING_DEFECT", "group": "READER_LIMITS",
     "rule": None},
    {"pattern": r"^(DOOR_CLOSURE_UNRESOLVED|VOID_EXTENT_UNRESOLVED)", "category": "E_ENGINEERING_DEFECT",
     "group": "READER_LIMITS", "rule": None},
    {"pattern": r"^REVIEW", "item": r"^DOORS:(DOOR_PROVISIONAL|DOOR_UNRESOLVED|DOOR_CLASS_UNRESOLVED)",
     "category": "B_MISSING_DRAWING_EVIDENCE", "group": "DOOR_EVIDENCE", "rule": "UP-DOOR-CLS-001",
     "request": "door schedule, or the independent opening and two typed sides"},
    {"pattern": r"^REVIEW", "item": r"^DOORS:(DOOR_HELD_WIDTH_REVIEW|DOOR_CLOSURE_FRAME_DISAGREE)",
     "category": "B_MISSING_DRAWING_EVIDENCE", "group": "DOOR_WIDTH_CONFLICT", "rule": "UP-DOOR-OPEN-002",
     "request": "door schedule or a dimension", "history": ["DR-02", "OD-2"]},
    {"pattern": r"^REVIEW", "item": r"^DOORS:DOOR_CLASS_REVIEW", "category": "B_MISSING_DRAWING_EVIDENCE",
     "group": "SPACE_ENCLOSURE", "rule": "UP-SPACE-001",
     "request": "is the space inside the envelope (label, elevation, or a project decision)", "history": ["DR-03",
                                                                                                          "OD-3"]},
    {"pattern": r"^REVIEW", "item": r"^DOORS:LIFT_ENTRANCE_CANDIDATE", "category": "B_MISSING_DRAWING_EVIDENCE",
     "group": "LIFT_IDENTITY", "rule": "UP-DOOR-CLS-005", "request": "lift label or lift schedule",
     "history": ["DR-06", "OD-4"]},
    {"pattern": r"^REVIEW", "item": r"^DOORS:MAIN_ENTRANCE", "category": "B_MISSING_DRAWING_EVIDENCE",
     "group": "MAIN_ENTRANCE", "rule": "UP-DOOR-CLS-004", "request": "entrance label, elevation or door schedule",
     "history": ["DR-01", "OD-5"]},
    {"pattern": r"^OPENING_BELOW_OWNER_STANDARD", "category": "C_RULE_CONFLICT", "group": "DOOR_ENLARGEMENT",
     "rule": "UP-DOOR-OPEN-002", "handled_by": "scenarios (AS_DRAWN / OWNER_REQUIRED); not a question"},
    {"pattern": r"^WALL_TILE_BELOW_OWNER_FULL_HEIGHT", "category": "C_RULE_CONFLICT", "group": "WET_ROOM_WALL_TILE_HEIGHT",
     "rule": "UP-FIN-WALL-001", "handled_by": "the explicit source governs; flagged"},
    {"pattern": r"^WALL_BAND_ABOVE_EXPLICIT_TILE", "category": "C_RULE_CONFLICT", "group": "WET_ROOM_WALL_TILE_HEIGHT",
     "rule": "UP-FIN-WALL-001", "handled_by": "the explicit source governs the tile; the band above it follows the "
     "same project source (confirmed with it)", "history": ["Q7", "O5"]},
    {"pattern": r"^OPEN_PLAN_WET_SCOPE_EXTENT", "category": "B_MISSING_DRAWING_EVIDENCE", "group": "WET_ZONE_EXTENT",
     "rule": "UP-WET-001", "request": "the kitchen / pantry zone of the open plan (a finish-plan line or hatch)"},
    {"pattern": r"^WET_SCOPE_PROJECT_CONFIRMATION", "category": "B_MISSING_DRAWING_EVIDENCE",
     "group": "WET_SCOPE_CONFIRMATION", "rule": "UP-WET-001",
     "request": "the project finish schedule (whether the room is a wet area)"},
    {"pattern": r"^EXTERIOR_WP_UPTURN_BY_SPECIFICATION", "category": "B_MISSING_DRAWING_EVIDENCE",
     "group": "WATERPROOFING_SPECIFICATION", "rule": "UP-WP-ROOF-001",
     "request": "the balcony / terrace membrane system and its upturn height (specification)"},
    {"pattern": r"^THRESHOLD_OF_PROVISIONAL_DOOR", "category": "B_MISSING_DRAWING_EVIDENCE", "group": "DOOR_EVIDENCE",
     "rule": "UP-THR-001", "request": "door schedule, or the independent opening and two typed sides"},
    {"pattern": r"^THRESHOLD_STRIP_NOT_ATTRIBUTED", "category": "E_ENGINEERING_DEFECT", "group": "STRIP_ATTRIBUTION",
     "rule": "UP-THR-001"},
    {"pattern": r"^PANTRY_THRESHOLD_RULE_CONFLICT", "category": "C_RULE_CONFLICT", "group": "PANTRY_THRESHOLD",
     "rule": "UP-THR-001", "question_id": "OQ-01"},
    {"pattern": r"^DOOR_OPENING_HEAD_ALLOWANCE", "category": "D_MISSING_OWNER_POLICY", "group": "DOOR_HEAD_ALLOWANCE",
     "rule": "UP-DOOR-OPEN-002", "question_id": "OQ-02"},
]

# WP-5 / integration tests that also prove a rule (added to the rule's test links)
W5, IT, Q = T + "test_kb_wp5.py::", T + "test_kb_integration.py::", T + "test_kb_questions.py::"
EXTRA_TESTS = {
    "UP-KB-PREC-001": [IT + "test_no_drawn_dimension_is_replaced", IT + "test_an_assumption_is_never_released_as_confirmed",
                       IT + "test_v2_2_never_reads_the_registry"],
    "UP-KB-QUES-001": [Q + "test_every_catalogue_entry_is_reached_by_its_example",
                       Q + "test_an_unknown_reason_is_reported_unclassified_never_dropped"],
    "UP-DOOR-CLS-001": [W5 + "test_a_wall_gap_without_a_door_symbol_is_a_passage_not_a_door",
                        W5 + "test_a_door_symbol_with_no_wall_gap_is_never_measured"],
    "UP-DOOR-CLS-002": [W5 + "test_a_balcony_door_is_aluminium_and_the_balcony_is_waterproofed"],
    "UP-DOOR-CLS-004": [W5 + "test_a_balcony_door_is_aluminium_and_the_balcony_is_waterproofed"],
    "UP-DOOR-OPEN-002": [W5 + "test_conflicting_opening_dimensions_keep_both_values_and_hold_the_door",
                         IT + "test_the_owner_required_view_never_reaches_the_boq_lines"],
    "UP-DOOR-HGT-001": [IT + "test_an_assumption_is_never_released_as_confirmed"],
    "UP-THR-001": [W5 + "test_several_strip_faces_of_one_opening_make_one_line",
                   W5 + "test_a_door_closure_strip_asks_for_the_door_not_the_finish"],
    "UP-WP-ROOF-001": [W5 + "test_a_balcony_door_is_aluminium_and_the_balcony_is_waterproofed"],
    "UP-SPACE-001": [IT + "test_v2_3_is_invariant_under_moving_mirroring_and_turning"],
}
for r_ in R:
    r_["tests"] = r_["tests"] + [t for t in EXTRA_TESTS.get(r_["rule_id"], ()) if t not in r_["tests"]]
assert set(EXTRA_TESTS) <= {r_["rule_id"] for r_ in R}

# one example reason (and item) per catalogue entry: tests/m9_kb/test_kb_questions.py proves every entry is reached by
# its example (no entry is shadowed by an earlier, broader one)
EXAMPLES = {
    (r"^THRESHOLD_FINISH_NOT_ESTABLISHED", None): ("THRESHOLD_FINISH_NOT_ESTABLISHED (Q-S6-1): the strip ...",
                                                    "ARCH.THRESHOLD"),
    (r"^UP-CER-004", None): ("UP-CER-004: the wall tile height of the wet room is not established", "FIN.SKIRTING"),
    (r"^FINISH_ABOVE_WALL_TILE_NOT_ESTABLISHED", None): ("FINISH_ABOVE_WALL_TILE_NOT_ESTABLISHED (Q7): the band", "FIN.PAINT"),
    (r"^MISSING_SOURCE", r"^DOOR HEIGHTS"): ("MISSING_SOURCE: no door height", "DOOR HEIGHTS"),
    (r"^WALL_FINISH_HEIGHT_NOT_ESTABLISHED", None): ("WALL_FINISH_HEIGHT_NOT_ESTABLISHED (UP-CER-009, PAINT): ...",
                                                     "FIN.PAINT"),
    (r"^(PLASTER|PAINT|WALL_TILE) net is a range", None): ("PAINT net is a range: closure position unknown", "FIN.PAINT"),
    (r"^WINDOW_REVEAL_FLOOR_STATUS_NOT_ESTABLISHED", None): ("WINDOW_REVEAL_FLOOR_STATUS_NOT_ESTABLISHED: the strip",
                                                             "ARCH.WINDOW_REVEAL"),
    (r"^F-17", None): ("F-17: the sill status of the window is unknown", "FIN.SKIRTING"),
    (r"^FLOOR_FINISH_SPEC_NOT_ESTABLISHED", None): ("FLOOR_FINISH_SPEC_NOT_ESTABLISHED: no selected tile size",
                                                    "FIN.FLOOR.PORCELAIN (material)"),
    (r"^STAIR_(?!HALL_FINISH)", None): ("STAIR_RISER_NOT_ESTABLISHED: flight 1", "FIN.MARBLE.RISER"),
    (r"^BLOCK_WALL_NOT_ESTABLISHED", None): ("BLOCK_WALL_NOT_ESTABLISHED (walls t=0.20 m)", "MAS.BLOCK"),
    (r"^(UNLABELLED_SPACE|MERGED_SPACE|MIXED_SPACE|ATTACHED_THROUGH_OPEN_PASSAGE|ZONE_FROM_DRAWN_LINES)", None):
        ("UNLABELLED_SPACE: no room word", "FIN.FLOOR"),
    (r"^ROOM_TYPE_FROM_STACKED_FOOTPRINT", None): ("ROOM_TYPE_FROM_STACKED_FOOTPRINT: the same footprint", "ARCH.SPACE"),
    (r"^STAIRWELL_CEILING_SCOPE_NOT_ESTABLISHED", None): ("STAIRWELL_CEILING_SCOPE_NOT_ESTABLISHED: the enclosure",
                                                          "FIN.CEILING"),
    (r"^STAIR_HALL_FINISH_NOT_ESTABLISHED", None): ("STAIR_HALL_FINISH_NOT_ESTABLISHED (Q-S6-4): the walls", "FIN.PAINT"),
    (r"^EXTERIOR_FINISH_SCOPE_NOT_ESTABLISHED", None): ("EXTERIOR_FINISH_SCOPE_NOT_ESTABLISHED (Q1): a garden",
                                                        "ARCH.EXTERIOR"),
    (r"^STRIP_NOT_ATTRIBUTED", None): ("STRIP_NOT_ATTRIBUTED: a strip in the wall thickness", "ARCH.THRESHOLD"),
    (r"^GEOMETRY_INCONSISTENT", None): ("GEOMETRY_INCONSISTENT: the parts do not add up", "FIN.FLOOR"),
    (r"^(WARNING|ENGINEERING)", None): ("WARNING: 3 HATCH: READ_ONE_BLOCK_LEVEL", "ADMISSION:ENTITY_KIND_NOT_MEASURED"),
    (r"^(DOOR_CLOSURE_UNRESOLVED|VOID_EXTENT_UNRESOLVED)", None): ("DOOR_CLOSURE_UNRESOLVED: no leaf hypothesis",
                                                                   "door symbol D1"),
    (r"^REVIEW", r"^DOORS:(DOOR_PROVISIONAL|DOOR_UNRESOLVED|DOOR_CLASS_UNRESOLVED)"): ("REVIEW: a provisional door",
                                                                                       "DOORS:DOOR_PROVISIONAL"),
    (r"^REVIEW", r"^DOORS:(DOOR_HELD_WIDTH_REVIEW|DOOR_CLOSURE_FRAME_DISAGREE)"): ("REVIEW: frame and opening disagree",
                                                                                   "DOORS:DOOR_HELD_WIDTH_REVIEW"),
    (r"^REVIEW", r"^DOORS:DOOR_CLASS_REVIEW"): ("REVIEW: possibly external", "DOORS:DOOR_CLASS_REVIEW"),
    (r"^REVIEW", r"^DOORS:LIFT_ENTRANCE_CANDIDATE"): ("REVIEW: an opening into a shaft",
                                                      "DOORS:LIFT_ENTRANCE_CANDIDATE"),
    (r"^REVIEW", r"^DOORS:MAIN_ENTRANCE"): ("REVIEW: no external door carries entrance evidence",
                                            "DOORS:MAIN_ENTRANCE_UNRESOLVED"),
    (r"^OPENING_BELOW_OWNER_STANDARD", None): ("OPENING_BELOW_OWNER_STANDARD: 0.90 m < 1.10 m", "DOOR.INTERNAL.PVC"),
    (r"^WALL_TILE_BELOW_OWNER_FULL_HEIGHT", None): ("WALL_TILE_BELOW_OWNER_FULL_HEIGHT: the explicit wall-tile height",
                                                    "FIN.WALL.TILE"),
    (r"^WALL_BAND_ABOVE_EXPLICIT_TILE", None): ("WALL_BAND_ABOVE_EXPLICIT_TILE (Q7, UP-FIN-WALL-001): the band",
                                                "FIN.PAINT"),
    (r"^OPEN_PLAN_WET_SCOPE_EXTENT", None): ("OPEN_PLAN_WET_SCOPE_EXTENT: the wet area of this open plan",
                                             "FINISH_SCOPE"),
    (r"^WET_SCOPE_PROJECT_CONFIRMATION", None): ("WET_SCOPE_PROJECT_CONFIRMATION: LAUNDRY is a wet area",
                                                 "FINISH_SCOPE"),
    (r"^EXTERIOR_WP_UPTURN_BY_SPECIFICATION", None): ("EXTERIOR_WP_UPTURN_BY_SPECIFICATION: the balcony membrane",
                                                      "FIN.WP.UPTURN"),
    (r"^THRESHOLD_OF_PROVISIONAL_DOOR", None): ("THRESHOLD_OF_PROVISIONAL_DOOR (UP-THR-001 sets the finish)",
                                                "ARCH.THRESHOLD"),
    (r"^THRESHOLD_STRIP_NOT_ATTRIBUTED", None): ("THRESHOLD_STRIP_NOT_ATTRIBUTED (UP-THR-001 sets the finish)",
                                                 "ARCH.THRESHOLD"),
    (r"^PANTRY_THRESHOLD_RULE_CONFLICT", None): ("PANTRY_THRESHOLD_RULE_CONFLICT (OQ-01): marble threshold",
                                                 "FIN.MARBLE.THRESHOLD"),
    (r"^DOOR_OPENING_HEAD_ALLOWANCE", None): ("DOOR_OPENING_HEAD_ALLOWANCE: the head of the wall opening",
                                              "DOOR.INTERNAL.PVC"),
}
for q_ in QUESTIONS:
    reason_, item_ = EXAMPLES[(q_["pattern"], q_.get("item"))]
    q_["example"] = {"reason": reason_, "item": item_}
assert len(EXAMPLES) == len(QUESTIONS)

OWNER_QUESTIONS = [
    {"id": "OQ-01", "category": "C_RULE_CONFLICT", "group": "PANTRY_THRESHOLD",
     "found": "an enclosed pantry with a door is a wet area under the master prompt (UP-WET-001), but the Urban-wide "
              "marble-threshold rule lists the pantry as not applicable",
     "rules_checked": ["UP-WET-001", "UP-THR-001", "URBAN-WET-SERVICE-MARBLE-THRESHOLD"],
     "why_unresolved": "two approved owner statements disagree for the same doorway; precedence by date is not "
                       "explicit", "alternatives": ["marble threshold at pantry doorways", "pantry floor porcelain "
                                                    "continues through the doorway (no threshold)"],
     "affects": ["FIN.MARBLE.THRESHOLD", "FIN.FLOOR.PORCELAIN doorway strips"],
     "recommendation": "marble threshold (the newer, general statement); measured PROVISIONAL meanwhile",
     "continue_safely": True},
    {"id": "OQ-02", "category": "D_MISSING_OWNER_POLICY", "group": "DOOR_HEAD_ALLOWANCE",
     "found": "the owner rule adds 0.10 m to the width of the architectural wall opening; it says nothing about "
              "its head height", "rules_checked": ["UP-DOOR-OPEN-002", "UP-DOOR-HGT-001"],
     "why_unresolved": "no approved rule gives the wall-opening head allowance",
     "alternatives": ["the wall-opening head = the door height", "door height + an allowance (owner value)"],
     "affects": ["owner-required wall-opening areas (blockwork, plaster, paint deductions)"],
     "recommendation": "door height until the owner states an allowance (labelled ASSUMED)",
     "continue_safely": True},
    {"id": "OQ-03", "category": "D_MISSING_OWNER_POLICY", "group": "STAIR_HALL_FINISHES",
     "found": "stair enclosures have plaster, paint and skirting RFIs", "rules_checked": ["UP-STAIR-001..014",
                                                                                          "UP-VOCAB-004/005"],
     "why_unresolved": "the stair rules cover treads, risers, landings, stair skirting and railings, not the "
                       "enclosure walls", "alternatives": ["dry-room treatment (plaster + paint + stair skirting)",
                                                           "a specified wall finish"],
     "affects": ["FIN.PLASTER / FIN.PAINT / FIN.SKIRTING of stair halls"],
     "recommendation": "dry-room treatment with the stair skirting measured along the stair", "continue_safely": True},
    {"id": "OQ-04", "category": "D_MISSING_OWNER_POLICY", "group": "EXTERIOR_SCOPE",
     "found": "exterior spaces (garden, terrace, hardscape) carry an area only",
     "rules_checked": ["UP-WP-ROOF-001", "external interlock (no approved record found)"],
     "why_unresolved": "no approved exterior finish scope exists beyond waterproofing",
     "alternatives": ["interlock / external tiles by specification", "excluded from the architectural BOQ"],
     "affects": ["ARCH.EXTERIOR"], "recommendation": "keep the areas as information until a scope is given",
     "continue_safely": True},
]

reg = {"schema": "URBAN_ENGINEERING_KNOWLEDGE_V1", "version": "1.0.0", "effective": D14,
       "statuses": ["OWNER_APPROVED", "DRAWING_VERIFIED", "PROJECT_SPECIFIC", "REFERENCE_ONLY", "ASSUMPTION",
                    "CONFLICTED", "REQUIRES_CONFIRMATION", "DEPRECATED"],
       "consumed_by": ["ARCH_TAKEOFF_V2.3 (engine/source/knowledge.py)"],
       "not_consumed_by": "ARCH_TAKEOFF_V1 / V2 / V2.1 / V2.2 (frozen; their rule set stays rules/ 1.5.0)",
       "index": "knowledge/RULE_SOURCE_INDEX.json (generated by tools/kb_index.py: every rule, fact and question "
                "source in the repository)",
       "precedence_rule": "UP-KB-PREC-001", "question_rule": "UP-KB-QUES-001",
       "rules": sorted(R, key=lambda r: r["rule_id"]), "conflicts": CONFLICTS, "question_catalogue": QUESTIONS,
       "owner_questions": OWNER_QUESTIONS}
ids = [r["rule_id"] for r in R]
assert len(ids) == len(set(ids)), "duplicate rule id"
TEXT = json.dumps(reg, indent=1, sort_keys=True, ensure_ascii=False) + "\n"
if __name__ == "__main__":
    if "--check" in sys.argv[1:]:
        same = OUT.is_file() and OUT.read_text(encoding="utf-8") == TEXT
        print("registry up to date" if same else "registry differs from a fresh build: run tools/kb_build.py")
        sys.exit(0 if same else 1)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(TEXT, encoding="utf-8")
    print(len(R), "rules", len(CONFLICTS), "conflicts", len(QUESTIONS), "question patterns", OUT.stat().st_size,
          "bytes")
