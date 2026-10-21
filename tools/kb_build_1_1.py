"""KNOWLEDGE REGISTRY 1.1.0 BUILDER (M9 Phase 2B-2) - knowledge/URBAN_ENGINEERING_KNOWLEDGE_1.1.0.json is the frozen
1.0.0 registry (read byte for byte, never rebuilt) plus the delta of the owner program of 2026-10-16 (master
engineering rules, waterproofing optimization and door feasibility):

    new rules        UP-WP-001 roll, UP-WP-002 lap, UP-WP-003 upturn, UP-WP-004 penetrations / corners,
                     UP-WP-MAT-001 three quantities, UP-WP-LAY-001 layout and cutting plan, UP-WP-DOOR-001 doorway
                     transitions, UP-RULES-001 Level A / Level B rules and the Project Engineering Rules Sheet,
                     UP-DOOR-FEAS-001 door feasibility
    superseded       UP-WP-UPTURN-015 (the earlier general 0.15 m upturn, DEPRECATED, superseded_by UP-WP-003)
    updated (1.1.0)  UP-WET-001, UP-WP-ROOF-001, UP-DOOR-OPEN-002, UP-DOOR-HGT-001, UP-DOOR-AREA-001, UP-DOOR-DEP-001
    reference only   four Urban owner methods found in data/registry (never applied by the engine; kept findable)
    conflicts        CF-12 doorway segment in the upturn, CF-13 identifier namespace, CF-14 balcony upturn
    questions        the new flag families of ARCH_TAKEOFF_V2.4 (each with an example reason)

    python3 -I tools/kb_build_1_1.py            write the 1.1.0 registry
    python3 -I tools/kb_build_1_1.py --check    exit 1 when the committed 1.1.0 registry differs from a fresh build

Stdlib only."""
import copy
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "knowledge" / "URBAN_ENGINEERING_KNOWLEDGE_1.0.0.json"
OUT = ROOT / "knowledge" / "URBAN_ENGINEERING_KNOWLEDGE_1.1.0.json"
D16 = "2026-10-16"
P = "owner program 2026-10-16 (URBAN PROJECT AI - master engineering rules, waterproofing optimization and door " \
    "feasibility)"
T = "tests/m9_p2b2/"
WT, DT, RT, IT = (T + "test_p2b2_waterproofing.py::", T + "test_p2b2_door_feasibility.py::",
                  T + "test_p2b2_project_rules.py::", T + "test_p2b2_integration.py::")
REGT = T + "test_p2b2_registry.py::"
WS, DF, PR = ("engine/source/waterproofing_system.py::", "engine/source/door_feasibility.py::",
              "engine/source/project_rules.py::")
H1 = [{"version": "1.1.0", "date": D16, "change": "first registry record (Phase 2B-2)"}]


def rec(rule_id, title, *, purpose, scope, elements, locations=("ALL",), preconditions=(), exceptions=(),
        authority, status, logic, evidence=(), assumptions="NONE", conflicts=(), trades=(), tests=(), code=(),
        examples=(), limitations=(), history=None, supersedes=(), superseded_by=None, kind="OWNER_RULE",
        version="1.1.0"):
    return {"rule_id": rule_id, "title": title, "kind": kind, "purpose": purpose, "scope": scope,
            "elements": list(elements), "locations": list(locations), "preconditions": list(preconditions),
            "exceptions": list(exceptions), "authority": authority, "status": status, "effective_version": version,
            "logic": logic, "required_evidence": list(evidence), "assumptions_permitted": assumptions,
            "conflicts": list(conflicts), "dependent_trades": list(trades), "tests": list(tests), "code": list(code),
            "examples": list(examples), "limitations": list(limitations), "history": history or H1,
            "supersedes": list(supersedes), "superseded_by": superseded_by}


def owner(part):
    return {"kind": "OWNER", "source": f"{P} {part}", "received": D16}


NEW = []
# ------------------------------------------------------------------------------------------------ Level A / Level B
NEW.append(rec(
    "UP-RULES-001", "Two rule levels: Urban master standards (A) and project-specific rules (B), one rules sheet per "
    "project", kind="KNOWLEDGE_POLICY",
    purpose="apply the company standards to every project, let a project's approved requirements govern within their "
            "scope, keep both, and show which rule governs every quantity",
    scope="every project and every quantity", elements=["ALL"], authority=owner("Part 2, Part 5"),
    status="OWNER_APPROVED",
    logic={"level_A": "Urban Project master standards: this registry (door heights and widths, opening allowance, "
                      "membrane roll, overlap, upturn, wet-area classes, skirting, thresholds)",
           "level_B": "project-specific approved requirements: drawings, schedules, details, specifications and "
                      "owner project approvals (input URBAN_PROJECT_RULES_V1)",
           "precedence": "Level B overrides Level A for that project, only within the scope it names",
           "scopes": ["PROJECT", "LOCATION_TYPE", "DOOR_CATEGORY", "FLOOR", "ROOM", "WALL", "OPENING"],
           "most_specific_scope_wins": "OPENING > WALL > ROOM > FLOOR > LOCATION_TYPE / DOOR_CATEGORY > PROJECT > the "
                                       "Urban standard; a type filter added to a floor or room scope ranks it higher",
           "both_kept": "the Urban standard and the project requirement are both recorded, each with its source",
           "conflict": "two project rules of the same rank that disagree for one element: CONFLICT_REVIEW, the "
                       "affected quantity unresolved - never silently discarded",
           "rules_sheet": "the Project Engineering Rules Sheet is generated before the BOQ calculation; its version "
                          "and sha256 travel with every output",
           "change": "a rules sheet with another hash supersedes the earlier outputs (moved aside, never reused) and "
                     "names the changed rules and the trades they affect",
           "states": ["DRAWING_CONFIRMED", "PROJECT_SPECIFIED", "OWNER_STANDARD_ASSUMED", "OWNER_PROJECT_APPROVED",
                      "CONFLICT_REVIEW", "ENGINE_LIMITATION", "MISSING_DOCUMENT"],
           "never": ["a project rule applied outside its scope", "a conflict discarded", "a stale result kept after "
                     "the rules changed"]},
    evidence=["the project rule's source (drawing, page, detail, schedule, specification, owner approval)"],
    trades=["ALL"],
    tests=[RT + "test_a_project_upturn_overrides_the_urban_standard_only_in_its_scope",
           RT + "test_the_most_specific_scope_wins",
           RT + "test_two_project_rules_that_disagree_are_a_conflict_never_discarded",
           RT + "test_a_conflicting_project_rule_is_never_shown_as_applied",
           RT + "test_the_rules_sheet_has_every_section_and_state",
           RT + "test_a_changed_rules_sheet_invalidates_earlier_outputs",
           IT + "test_the_rules_sheet_hash_is_in_every_v2_4_output"],
    code=[PR + "bind", PR + "_rank", PR + "rules_sheet", PR + "invalidation"],
    examples=[{"case": "Urban upturn 0.20 m; an approved project detail specifies 0.30 m for the first-floor "
                       "bathrooms", "urban_m": 0.20, "project_m": 0.30, "applied_m": 0.30,
               "scope": "FLOOR 1F + LOCATION_TYPE BATHROOM", "state": "PROJECT_SPECIFIED"}]))
# ------------------------------------------------------------------------------------------------ waterproofing
NEW.append(rec(
    "UP-WP-001", "Waterproofing membrane roll: 1.00 m x 10.00 m (10.00 m2 gross)", kind="OWNER_STANDARD",
    purpose="the roll the procurement quantity is counted in", scope="every sheet-membrane waterproofing quantity",
    elements=["WATERPROOFING"], authority=owner("Part 3.1 (UP-WP-001)"), status="OWNER_APPROVED",
    logic={"roll_width_m": 1.0, "roll_length_m": 10.0, "gross_roll_area_m2": 10.0, "level": "A",
           "override": "the roll of a project-specified membrane system replaces it within that system's scope "
                       "(UP-RULES-001)",
           "same_values_as": "rules/materials MEM-URBAN-DEFAULT-1x10 (the rule store's default membrane)",
           "never": ["the net area / roll area rounded up as the roll count", "a waste percentage in place of a "
                     "cutting plan"]},
    trades=["WATERPROOFING"],
    tests=[REGT + "test_the_approved_waterproofing_values_cannot_silently_change",
           WT + "test_rectangular_bathroom_hand_calculation"],
    code=[WS + "system_spec"],
    examples=[{"case": "a 12.4 m2 cutting plan", "rolls": "from the cutting plan, never ceil(12.4 / 10) by rule"}]))
NEW.append(rec(
    "UP-WP-002", "Membrane overlap 0.10 m at the joints between adjacent strips", kind="OWNER_STANDARD",
    purpose="the lap material between adjoining membrane pieces", scope="every sheet-membrane layout",
    elements=["WATERPROOFING"], authority=owner("Part 3.1 (UP-WP-002)"), status="OWNER_APPROVED",
    logic={"lap_m": 0.1, "level": "A",
           "applies_to": ["side laps between adjacent floor strips", "end laps where a strip is spliced along its "
                          "length", "upturn band joints and the band's lap onto the floor membrane",
                          "a doorway piece's lap onto the floor membrane"],
           "stricter_wins": "a project or manufacturer lap larger than 0.10 m governs within its scope (Level B)",
           "never": ["a flat 10 % waste allowance in place of the laps", "a lap smaller than the applied value"]},
    trades=["WATERPROOFING"],
    tests=[REGT + "test_the_approved_waterproofing_values_cannot_silently_change",
           WT + "test_project_overlap_overrides_the_standard"],
    code=[WS + "system_spec"],
    examples=[{"case": "cross width 1.90 m, roll 1.00 m", "strips": 2, "basis": "1.00 + (1.00 - 0.10) >= 1.90"}]))
NEW.append(rec(
    "UP-WP-003", "Waterproofing upturn 0.20 m along eligible wall boundaries", kind="OWNER_STANDARD",
    purpose="the vertical membrane turned up the walls of a waterproofed area",
    scope="wet areas, balconies, terraces and roofs", elements=["WATERPROOFING"],
    authority=owner("Part 3.1 (UP-WP-003), Part 3.4"), status="OWNER_APPROVED",
    logic={"upturn_h_m": 0.2, "level": "A",
           "eligible": ["WALL", "COLUMN", "WINDOW_THRESHOLD (the wall below a sill)", "obstruction (column / shaft) "
                        "rings inside the area"],
           "not_a_wall_upturn": {"DOOR": "doorway transition (UP-WP-DOOR-001)",
                                 "GLAZING_EDGE": "threshold transition at a floor-level frame (by detail)",
                                 "PASSAGE": "continuation into an adjacent waterproofed area, else a termination "
                                            "(by detail)",
                                 "ZONE_LINE": "continuation into a waterproofed zone, else a termination (by detail)",
                                 "OPEN_EDGE": "termination (by detail)"},
           "override": "an approved project detail (Level B) governs within its scope; both values are kept",
           "never": ["every doorway width x 0.20 m as a wall upturn", "the 0.15 m value of the superseded rule"]},
    trades=["WATERPROOFING"], supersedes=["UP-WP-UPTURN-015"],
    history=[{"version": "1.1.0", "date": D16, "change": "first registry record (Phase 2B-2); replaces the earlier "
                                                          "general 0.15 m upturn (UP-WP-UPTURN-015)"}],
    tests=[REGT + "test_the_superseded_upturn_keeps_its_history",
           WT + "test_doorways_are_transitions_not_wall_upturns", WT + "test_project_upturn_overrides_the_standard",
           WT + "test_balcony_upturn_on_walls_and_open_edge_termination",
           WT + "test_a_window_frame_line_on_the_wall_face_is_a_sill_upturn_not_glazing",
           WT + "test_the_segmentation_check_accepts_window_frames_and_flags_anything_else"],
    code=["engine/source/wp_geometry.py::boundary", "engine/source/wp_geometry.py::segments", WS + "area_schedule"],
    examples=[{"case": "bathroom 2.00 x 1.50 m, one 0.80 m door", "eligible_lm": 6.2, "upturn_m2": 1.24,
               "doorway": "a transition item, not 0.80 x 0.20 in the upturn"}]))
NEW.append(rec(
    "UP-WP-004", "Penetrations, corners and other interruptions: counted from the drawings, treated by the detail",
    kind="OWNER_STANDARD", purpose="the extra waterproofing work around drains, pipes, outlets, corners, junctions and "
                                   "doorways, never invented",
    scope="every waterproofed area", elements=["WATERPROOFING"], authority=owner("Part 3.1 (UP-WP-004)"),
    status="OWNER_APPROVED",
    logic={"kinds": ["FLOOR_DRAIN", "PIPE_PENETRATION", "PLUMBING_OUTLET", "ROOF_DRAIN", "OTHER_INTERRUPTION",
                     "DOORWAY_TRANSITION", "CORNER_INTERNAL", "CORNER_EXTERNAL", "JUNCTION"],
           "count_from": ["drain / gully / trap / outlet / sleeve symbols and texts drawn inside the area",
                          "the area polygon's corners where two upturned boundaries meet; obstruction corners",
                          "sanitary fixtures are indicative only: a fixture symbol does not establish an outlet "
                          "through the membrane"],
           "quantity_from": "the project waterproofing detail or the system data sheet (patch size, collar, "
                            "reinforcement strip) - UP-RULES-001 Level B",
           "missing": "the missing detail is named and the extra quantity withheld (in no total)",
           "never": ["an invented dimension or count", "'not shown' reported as zero"]},
    trades=["WATERPROOFING"],
    tests=[WT + "test_multiple_floor_drains_are_counted_and_their_treatment_withheld",
           WT + "test_l_shaped_bathroom_corners_and_upturn", WT + "test_missing_detail_blocks_the_quantity"],
    code=[WS + "penetrations", WS + "area_schedule"]))
NEW.append(rec(
    "UP-WP-MAT-001", "Three waterproofing quantities kept apart: net area, installed membrane, procurement rolls",
    kind="OWNER_STANDARD", purpose="a membrane quantity that can be checked and bought",
    scope="every waterproofed area and the project total", elements=["WATERPROOFING"],
    authority=owner("Part 3.2, Part 3.5"), status="OWNER_APPROVED",
    logic={"A_net": "the floor / roof area requiring waterproofing (horizontal)",
           "B_installed": ["horizontal coverage", "wall upturns", "required doorway waterproofing", "joint overlaps",
                           "penetration detailing (only from a detail)", "specified reinforcement (only from a "
                           "detail)", "the cutting and layout losses of the supported cutting plan"],
           "C_procurement": "whole rolls of the feasible cutting plan of each membrane system",
           "systems": "one procurement group per membrane system; until the project names its systems the wet-area "
                      "and exterior (balcony / roof) groups are kept apart",
           "never": ["net / roll area rounded up", "an arbitrary waste percentage unless a source or an owner "
                     "decision authorizes it", "incompatible membrane systems in one procurement total"]},
    trades=["WATERPROOFING"],
    tests=[WT + "test_separate_systems_are_never_combined", WT + "test_rectangular_bathroom_hand_calculation",
           WT + "test_same_area_different_shape_changes_material_and_rolls"],
    code=[WS + "schedule", WS + "cutting_plan"]))
NEW.append(rec(
    "UP-WP-LAY-001", "Deterministic membrane layout and cutting plan from the area polygon", kind="ENGINEERING_RULE",
    purpose="the installed and procurement quantities from a buildable layout, not from a ratio",
    scope="every sheet-membrane waterproofed area", elements=["WATERPROOFING"], authority=owner("Part 3.3"),
    status="OWNER_APPROVED",
    logic={"steps": ["the waterproofing boundary", "openings, doorways, columns and interruptions", "eligible upturn "
                     "paths", "drains and known penetrations", "candidate strip layouts", "0.10 m laps (UP-WP-002)",
                     "cut lengths and strip counts", "upturns and eligible transitions", "offcut reuse only where the "
                     "cutting plan demonstrates it", "roll count", "unused material and cutting waste",
                     "a reviewable layout and material schedule"],
           "orientations": "at least two (along and across the area frame) where the geometry permits",
           "selection": ["valid laps, details and installation constraints", "fewest rolls for the area installed "
                         "on its own", "fewest seams (fewer potential leak paths)", "least consumed membrane",
                         "direction order (frame x before frame y)"],
           "reuse": "the project plan cuts the areas' full-width pieces from shared rolls of the same system (a roll "
                    "remainder reused only where a piece is cut from it); a narrow offcut is retained only under a "
                    "project minimum reusable size",
           "roll_count_state": "CONFIRMED only with a project-specified system, measured geometry and resolved "
                               "doorway, penetration and corner details; otherwise PROVISIONAL with what is withheld",
           "not_validated": "lap shingling against the falls (no drain or fall plan is read)",
           "never": ["a strip joined to another without its lap", "a reuse the plan does not show", "the lowest "
                     "waste taken as the buildable sequence regardless of the constraints"]},
    trades=["WATERPROOFING"],
    tests=[WT + "test_both_strip_orientations_are_evaluated_and_the_choice_is_deterministic",
           WT + "test_partial_roll_reuse_only_with_a_cutting_plan",
           WT + "test_roll_count_never_confirmed_without_a_valid_basis"],
    code=[WS + "room_layout", WS + "cutting_plan"]))
NEW.append(rec(
    "UP-WP-DOOR-001", "Doorway waterproofing transitions are modelled on their own", kind="ENGINEERING_RULE",
    purpose="a doorway neither stops the waterproofing nor becomes a 0.20 m wall upturn by default",
    scope="every doorway of a waterproofed area", elements=["WATERPROOFING", "DOOR"], authority=owner("Part 3.4"),
    status="OWNER_APPROVED",
    logic={"types": ["WALL_UPTURN", "DOOR_THRESHOLD_TRANSITION", "DOORWAY_CONTINUATION", "TERMINATION",
                     "PENETRATION_COLLAR", "CORNER_REINFORCEMENT"],
           "continuation": "the floor membrane continues through the doorway (door width x wall depth): the approved "
                           "owner method (rules/ UP-WP-003 1.1.0), released",
           "transition_alternatives": {"UPTURN_ACROSS_THRESHOLD": "door width x upturn height",
                                       "CONTINUATION_TERMINATED": "no extra membrane; a door-width termination at "
                                                                  "the outer face (by system)",
                                       "JAMB_RETURNS": "2 x wall depth x upturn height"},
           "detail": "a project waterproofing detail (UP-RULES-001) selects the alternative",
           "no_detail": "UNRESOLVED: the alternatives are listed with their quantities; the item is withheld",
           "never": "every doorway width x 0.20 m added to the wall upturn"},
    trades=["WATERPROOFING"], conflicts=["CF-12"],
    tests=[WT + "test_doorways_are_transitions_not_wall_upturns", WT + "test_missing_detail_blocks_the_quantity"],
    code=[WS + "transitions"]))
NEW.append(rec(
    "UP-WP-UPTURN-015", "The earlier general waterproofing upturn of 0.15 m - SUPERSEDED", kind="OWNER_STANDARD",
    purpose="history: the value the Urban rule library 1.4.0 and the lab waterproofing policy carried",
    scope="none (superseded)", elements=["WATERPROOFING"],
    authority={"kind": "OWNER", "source": "rules/owner_library URBAN_PROJECTS_RULE_LIBRARY 1.4.0 UP-WP-002 1.0.0; "
                                          "engine/source/waterproofing_policy.py WET_UPTURN_M", "received": "2026-10-12"},
    status="DEPRECATED", logic={"upturn_h_m": 0.15, "superseded_on": ["2026-10-12 (rule store UP-WP-002 2.0.0 = 0.20 "
                                                                      "m)", D16 + " (UP-WP-003)"]},
    superseded_by="UP-WP-003", trades=["WATERPROOFING"],
    history=[{"version": "1.0.0", "date": "2026-10-12", "change": "rule library 1.4.0 value (0.15 m)"},
             {"version": "1.1.0", "date": D16, "change": "registered as DEPRECATED, superseded by UP-WP-003 (0.20 m)"}],
    tests=[REGT + "test_the_superseded_upturn_keeps_its_history"], code=[], version="1.1.0"))
# ------------------------------------------------------------------------------------------------ doors
NEW.append(rec(
    "UP-DOOR-FEAS-001", "Door opening feasibility: does the owner-standard door fit, and can the opening be enlarged",
    kind="ENGINEERING_RULE",
    purpose="tell what the drawing shows, what Urban requires, where they differ and whether the required "
            "modification can physically fit - without approving it",
    scope="every ordinary door (internal PVC, bathroom PVC, external aluminium); the main entrance as drawn; "
          "elevators excluded", elements=["DOOR"], authority=owner("Part 4.3 - 4.7"), status="OWNER_APPROVED",
    logic={"per_door": ["actual CAD wall opening", "owner-preferred nominal door", "required wall opening",
                        "available nominal under the allowance (CAD - 0.10 m)", "difference to the required opening",
                        "whether enlargement is needed", "whether it appears geometrically feasible",
                        "what constrains it"],
           "classes": ["STANDARD_FITS_AS_DRAWN", "ENLARGEMENT_GEOMETRICALLY_POSSIBLE", "ENLARGEMENT_CONSTRAINED",
                       "ENLARGEMENT_REQUIRES_ENGINEERING_REVIEW", "INSUFFICIENT_DRAWING_EVIDENCE"],
           "constraints_read": ["the wall run on both faces beyond each jamb", "columns", "wall junctions and returns",
                                "corners and wall ends", "the swing of the larger leaf", "nearby openings (doors, "
                                "windows, passages)", "stair / shaft / lift spaces at the enlarged jamb", "fixtures "
                                "drawn in the swing", "the structural status of the host wall"],
           "pier": "the wall left beside a junction, corner or opening after the enlargement: a project value "
                   "(UP-RULES-001), engine default 0.10 m labelled ENGINE_REVIEW_THRESHOLD - not an owner standard",
           "structure_states": ["STRUCTURAL (project rule)", "NON_STRUCTURAL_SPECIFIED (project rule)",
                                "MASONRY_INDICATED (a masonry wall layer in a plan that draws a column frame; not "
                                "verified)", "UNKNOWN (no frame drawn, or the project says so)"],
           "views": ["AS_DRAWN", "OWNER_STANDARD", "PROPOSED_MODIFICATION", "UNRESOLVED"],
           "alternative": "if the enlargement is not approved, the door that fits = CAD wall opening - allowance",
           "never": ["geometric clearance taken as structural approval", "a column, beam or structural wall cut or "
                     "altered by recommendation without qualified engineering review", "a proposed modification "
                     "released as an as-drawn quantity", "the preferred door treated as already fitting"]},
    trades=["OPENINGS", "MASONRY", "PLASTER", "PAINT", "WALL_FINISH", "FLOOR_FINISH", "CONCRETE"],
    tests=[DT + "test_bathroom_0_80_needs_0_20_and_is_not_treated_as_fitting", DT + "test_opening_beside_a_column",
           DT + "test_unknown_structural_classification_requires_engineering_review",
           DT + "test_no_proposed_modification_is_released_as_drawn",
           DT + "test_door_opening_into_a_corridor_swing_clearance",
           DT + "test_mirrored_and_rotated_geometry_give_the_same_result",
           DT + "test_a_swing_symbol_closing_outside_its_gap_is_reported_not_evaluated",
           DT + "test_a_stair_at_the_enlarged_jamb_constrains_and_says_why_first"],
    code=[DF + "feasibility", DF + "clearances", DF + "classify", DF + "swing"],
    examples=[{"case": "bathroom CAD wall opening 0.80 m", "required_wall_opening_m": 1.0,
               "available_nominal_m": 0.7, "enlargement_m": 0.2, "compliance": "ENLARGEMENT_REQUIRED"}]))
# ------------------------------------------------------------------------------------------------ reference only
REF_SRC = "data/registry/URBAN_OWNER_METHOD_RULES.json"
for rid, title, src, logic in (
        ("UP-REF-REVEAL-001", "Reveal finishes: plaster by default (owner method, reference only)",
         "URBAN-REVEAL-FINISH-METHOD", {"default": "PLASTER", "porcelain": "only when requested, shown or "
                                        "project-authorised", "paint": "on a reveal owned by a painted dry surface"}),
        ("UP-REF-COLUMN-001", "Exposed column faces follow the room treatment (owner method, reference only)",
         "URBAN-EXPOSED-COLUMN-FINISH-METHOD", {"principle": "an exposed column face inside a room follows the "
                                                "surrounding room treatment at the room's own finish height"}),
        ("UP-REF-DUCT-001", "Exposed duct / boxed-out faces take the dry-room treatment (owner method, reference only)",
         "URBAN-EXPOSED-INTERIOR-DUCT-FINISH-METHOD", {"principle": "an exposed interior duct face takes the "
                                                       "surrounding dry-room treatment"}),
        ("UP-REF-CABINET-001", "Floor finish continues under cabinetry (owner method, reference only)",
         "URBAN-FLOOR-FINISH-BEFORE-CABINETRY-METHOD", {"principle": "cabinetry installed after the floor finish "
                                                        "does not reduce the floor-finish area"})):
    NEW.append(rec(rid, title, kind="OWNER_METHOD_REFERENCE",
                   purpose="knowledge retention: an approved Urban owner method the architectural route does not "
                           "apply, kept findable (Part 6)", scope="every Urban project (as the source states)",
                   elements=["FINISH"], authority={"kind": "OWNER_METHOD", "source": f"{REF_SRC} {src}",
                                                   "received": "before 2026-10-14"},
                   status="REFERENCE_ONLY", logic=dict(logic, applied_by="no emitter in ARCH_TAKEOFF_V2.4"),
                   limitations=["not applied: no ARCH_TAKEOFF route emits these surfaces"], trades=["PLASTER"]))

# ------------------------------------------------------------------------------------------------ updated records
UPDATES = {
    "UP-WET-001": {
        "logic.scope.waterproofing": "floor (rules/ UP-WP-001) + wall upturn on eligible boundaries (registry UP-WP-003) "
                                     "+ doorway continuation (rules/ UP-WP-003 1.1.0) and transition (registry "
                                     "UP-WP-DOOR-001)",
        "change": "waterproofing scope text names its rule sets (the rule store and the registry both use UP-WP-00x)",
        "code": [WS + "area_schedule"], "tests": [WT + "test_kitchen_and_pantry_get_membrane_material"]},
    "UP-WP-ROOF-001": {
        "logic.upturn": "UP-WP-003: 0.20 m on wall / parapet boundaries (owner standard, project detail overrides); "
                        "doorways are transitions (UP-WP-DOOR-001); open edges are terminations (by detail)",
        "logic.system": "by specification; a separate procurement group from the wet-area membrane (UP-WP-MAT-001)",
        "change": "the balcony upturn follows UP-WP-003 (was: by specification); the roof upturn follows the eligible "
                  "boundaries (was: the whole region perimeter)",
        "conflicts": ["CF-14"], "code": [WS + "area_schedule"],
        "tests": [WT + "test_balcony_upturn_on_walls_and_open_edge_termination"]},
    "UP-DOOR-OPEN-002": {
        "logic.available_nominal": "every door: the CAD wall opening - 0.10 m is the largest nominal door it takes "
                                   "under the allowance (owner example: a 0.80 m bathroom opening takes a 0.70 m door)",
        "logic.available_nominal_example": {"category": "BATHROOM_PVC", "cad_wall_opening_m": 0.8,
                                            "available_nominal_m": 0.7, "required_nominal_door_m": 0.9,
                                            "required_wall_opening_m": 1.0, "required_enlargement_m": 0.2,
                                            "status": "ENLARGEMENT_REQUIRED"},
        "logic.compliance": ["MEETS_STANDARD", "ENLARGEMENT_REQUIRED", "NOT_APPLICABLE", "NOT_ESTABLISHED"],
        "logic.project_override": "a project width standard (UP-RULES-001, scope DOOR_CATEGORY / OPENING) replaces the "
                                  "required nominal door; the Urban value is kept beside it",
        "change": "available nominal for every door, compliance status, project override (Part 4.3, Part 5)",
        "code": [DF + "feasibility"], "tests": [DT + "test_bathroom_0_80_needs_0_20_and_is_not_treated_as_fitting",
                                                DT + "test_a_project_specific_width_standard"]},
    "UP-DOOR-HGT-001": {
        "logic.state_label": "OWNER_STANDARD_ASSUMED",
        "logic.applies_to": "door areas and the related finish calculations (door jamb / head plaster) by door "
                            "category; the main entrance 2.50 m; a main-entrance candidate between 2.20 and 2.50 m",
        "change": "the owner's state label (never DRAWING_MEASURED); jamb plaster by category (Part 4.2)",
        "code": [DF + "jamb_plaster_lines"], "tests": [IT + "test_v2_4_jamb_plaster_uses_the_category_height"]},
    "UP-DOOR-AREA-001": {
        "logic.views_v2_4": ["AS_DRAWN", "OWNER_STANDARD", "PROPOSED_MODIFICATION", "UNRESOLVED", "EXCLUDED "
                             "(elevators)"],
        "change": "the PROPOSED_MODIFICATION view of the door feasibility engine (Part 4.6); never combined",
        "code": [DF + "views"], "tests": [DT + "test_no_proposed_modification_is_released_as_drawn"]},
    "UP-DOOR-DEP-001": {
        "logic.feasibility": "the dependency map is read with the feasibility of the enlargement (UP-DOOR-FEAS-001): "
                             "the column / junction / corner / opening / swing constraints and the structural status",
        "change": "dependency impacts carried into the door feasibility schedule", "code": [DF + "feasibility"],
        "tests": [DT + "test_opening_beside_a_column"]},
}


def _set(d, dotted, value):
    keys = dotted.split(".")
    for k in keys[:-1]:
        d = d[k]
    d[keys[-1]] = value


CONFLICTS = [
    {"id": "CF-12", "between": ["rules/ UP-WP-002 2.0.0 (upturn around the full boundary including every doorway "
                                "segment, no door deduction)", "UP-WP-DOOR-001 / owner program 2026-10-16 Part 3.4 "
                                "(never every doorway width x 0.20 m; a transition by detail)"], "state": "RESOLVED",
     "resolution": "the newer owner instruction governs ARCH_TAKEOFF_V2.4: the wall upturn leaves the doorway segments "
                   "out and each doorway is a transition item (alternatives listed, withheld until a detail); V1 .. "
                   "V2.3 keep the rule store reading (frozen)"},
    {"id": "CF-13", "between": ["rules/ UP-WP-001 floor, 002 upturn, 003 doorway, 004 shower, 005 lap",
                                "registry UP-WP-001 roll, 002 lap, 003 upturn, 004 penetrations"], "state": "RESOLVED",
     "resolution": "the same identifiers name different rules in the two rule sets: every reference carries its rule "
                   "set (rules/ 1.5.0 or URBAN_KB_1.1.0); ARCH_TAKEOFF_V2.4 cites the waterproofing standards "
                   "from the registry; the crosswalk below relates them"},
    {"id": "CF-14", "between": ["UP-WP-ROOF-001 1.0.0 (balcony upturn by specification)", "UP-WP-003 (0.20 m along "
                                "eligible wall boundaries)"], "state": "RESOLVED",
     "resolution": "ARCH_TAKEOFF_V2.4 applies 0.20 m on the balcony's wall boundaries (OWNER_STANDARD_ASSUMED); an "
                   "approved project detail overrides it; the open edge is a termination by detail"},
]
CROSSWALK = [
    {"registry": "UP-WP-001", "rule_store": "MEM-URBAN-DEFAULT-1x10 (rules/materials): the same roll"},
    {"registry": "UP-WP-002", "rule_store": "UP-WP-005 1.0.0 (minimum 0.10 m lap, never a flat waste rate)"},
    {"registry": "UP-WP-003", "rule_store": "UP-WP-002 2.0.0 (0.20 m; its doorway segment reading superseded: CF-12)"},
    {"registry": "UP-WP-004", "rule_store": "none (the default membrane's corner / penetration treatment is null)"},
    {"registry": "UP-WP-DOOR-001", "rule_store": "UP-WP-003 1.1.0 (continuation through the doorway: kept)"},
    {"registry": "UP-WP-UPTURN-015", "rule_store": "UP-WP-002 1.0.0 (0.15 m, superseded)"},
    {"registry": "(none)", "rule_store": "UP-WP-001 1.0.0 floor in m2 (unchanged); UP-WP-004 1.1.0 shower (PROPOSED, "
                                         "not promoted)"},
]

QUESTIONS = [
    {"pattern": r"^DOORWAY_WP_TRANSITION_DETAIL_REQUIRED", "category": "B_MISSING_DRAWING_EVIDENCE",
     "group": "WATERPROOFING_DOORWAY_DETAIL", "rule": "UP-WP-DOOR-001",
     "request": "the project waterproofing detail at the doorway (upturn across the threshold, continuation with a "
                "termination, or jamb returns)",
     "example": ("DOORWAY_WP_TRANSITION_DETAIL_REQUIRED (UP-WP-DOOR-001): door OP-005", "FIN.WP.DOORWAY_TRANSITION")},
    {"pattern": r"^WP_TERMINATION_DETAIL_REQUIRED", "category": "B_MISSING_DRAWING_EVIDENCE",
     "group": "WATERPROOFING_EDGE_DETAIL", "rule": "UP-WP-003",
     "request": "the termination detail at an open edge, a floor-level frame or a doorless opening to a dry space",
     "example": ("WP_TERMINATION_DETAIL_REQUIRED (UP-WP-003): an open edge", "FIN.WP.TERMINATION")},
    {"pattern": r"^WP_PENETRATIONS_NOT_SHOWN", "category": "B_MISSING_DRAWING_EVIDENCE",
     "group": "WATERPROOFING_PENETRATIONS", "rule": "UP-WP-004",
     "request": "the drainage / plumbing layout (floor drains, outlets, sleeves) of the waterproofed areas",
     "example": ("WP_PENETRATIONS_NOT_SHOWN (UP-WP-004): no drain drawn", "FIN.WP.PENETRATION")},
    {"pattern": r"^WP_PENETRATION_DETAIL_REQUIRED", "category": "B_MISSING_DRAWING_EVIDENCE",
     "group": "WATERPROOFING_PENETRATIONS", "rule": "UP-WP-004",
     "request": "the penetration / collar detail of the membrane system",
     "example": ("WP_PENETRATION_DETAIL_REQUIRED (UP-WP-004): 2 floor drains", "FIN.WP.PENETRATION")},
    {"pattern": r"^WP_CORNER_DETAIL_REQUIRED", "category": "B_MISSING_DRAWING_EVIDENCE",
     "group": "WATERPROOFING_SYSTEM_DETAILS", "rule": "UP-WP-004",
     "request": "the corner / junction reinforcement of the membrane system",
     "example": ("WP_CORNER_DETAIL_REQUIRED (UP-WP-004): 6 corners", "FIN.WP (material)")},
    {"pattern": r"^WP_SYSTEM_NOT_SPECIFIED", "category": "B_MISSING_DRAWING_EVIDENCE",
     "group": "WATERPROOFING_SPECIFICATION", "rule": "UP-WP-MAT-001",
     "request": "the membrane system of each waterproofed location (specification / data sheet)",
     "example": ("WP_SYSTEM_NOT_SPECIFIED (UP-WP-MAT-001): the wet-area membrane", "FIN.WP (procurement)")},
    {"pattern": r"^WP_BOUNDARY_SEGMENTATION_REVIEW", "category": "E_ENGINEERING_DEFECT",
     "group": "WATERPROOFING_BOUNDARY", "rule": "UP-WP-003",
     "example": ("WP_BOUNDARY_SEGMENTATION_REVIEW: the ring roles disagree", "FIN.WP (material)")},
    {"pattern": r"^WP_LAYOUT_BLOCKED", "category": "E_ENGINEERING_DEFECT", "group": "WATERPROOFING_LAYOUT",
     "rule": "UP-WP-LAY-001", "example": ("WP_LAYOUT_BLOCKED: a doorway piece wider than the roll", "FIN.WP (material)")},
    {"pattern": r"^PROJECT_RULE_CONFLICT", "category": "C_RULE_CONFLICT", "group": "PROJECT_RULE_CONFLICT",
     "rule": "UP-RULES-001", "handled_by": "both project values kept; the affected quantity is unresolved until the "
                                           "project documents are reconciled (not an owner question)",
     "example": ("PROJECT_RULE_CONFLICT (UP-RULES-001): PR-1 and PR-2 disagree", "FIN.WP.WALL_UPTURN")},
    {"pattern": r"^PROJECT_RULE_UNBOUND", "category": "B_MISSING_DRAWING_EVIDENCE", "group": "PROJECT_RULE_BINDING",
     "rule": "UP-RULES-001", "request": "the element the project rule names (its point lies in no room / opening)",
     "example": ("PROJECT_RULE_UNBOUND (UP-RULES-001): PR-3", "PROJECT_RULES")},
    {"pattern": r"^PROJECT_RULE_NOT_SUPPORTED", "category": "E_ENGINEERING_DEFECT", "group": "PROJECT_RULE_SUPPORT",
     "rule": "UP-RULES-001", "handled_by": "the rule is listed in the rules sheet (ENGINE_LIMITATION) and never "
                                           "applied; the engine needs the parameter before the rule can govern",
     "example": ("PROJECT_RULE_NOT_SUPPORTED: the engine has no parameter 'x' for UP-WP-003", "PROJECT_RULES")},
    {"pattern": r"^JAMB_HEIGHT_CLASS_PENDING", "category": "B_MISSING_DRAWING_EVIDENCE", "group": "MAIN_ENTRANCE",
     "rule": "UP-DOOR-HGT-001", "request": "entrance label, elevation or door schedule",
     "example": ("JAMB_HEIGHT_CLASS_PENDING (UP-DOOR-HGT-001): a main-entrance candidate", "FIN.PLASTER")},
    {"pattern": r"^JAMB_HEIGHT_NOT_ESTABLISHED", "category": "B_MISSING_DRAWING_EVIDENCE", "group": "LIFT_IDENTITY",
     "rule": "UP-DOOR-HGT-001", "request": "the elevator landing door data (height)",
     "example": ("JAMB_HEIGHT_NOT_ESTABLISHED (UP-DOOR-HGT-001): a lift landing", "FIN.PLASTER")},
]


def build():
    base_bytes = BASE.read_bytes()
    reg = json.loads(base_bytes.decode("utf-8"))
    reg = copy.deepcopy(reg)
    rules = {r["rule_id"]: r for r in reg["rules"]}
    for rid, up in UPDATES.items():
        r = rules[rid]
        for k, v in up.items():
            if k.startswith("logic."):
                _set(r, k, v)
        r["effective_version"] = "1.1.0"
        r["history"] = r["history"] + [{"version": "1.1.0", "date": D16, "change": up["change"]}]
        r["code"] = r["code"] + [c for c in up.get("code", ()) if c not in r["code"]]
        r["tests"] = r["tests"] + [t for t in up.get("tests", ()) if t not in r["tests"]]
        r["conflicts"] = r["conflicts"] + [c for c in up.get("conflicts", ()) if c not in r["conflicts"]]
    for r in NEW:
        assert r["rule_id"] not in rules, r["rule_id"]
        rules[r["rule_id"]] = r
    qs = []
    for q in QUESTIONS:
        q = dict(q)
        reason, item = q.pop("example")
        q["example"] = {"reason": reason, "item": item}
        qs.append(q)
    reg.update(version="1.1.0", effective=D16,
               base={"version": "1.0.0", "sha256": hashlib.sha256(base_bytes).hexdigest()},
               consumed_by=["ARCH_TAKEOFF_V2.4 (engine/source/knowledge.py, using('1.1.0'))"],
               not_consumed_by="ARCH_TAKEOFF_V1 / V2 / V2.1 / V2.2 (frozen; rules/ 1.5.0); ARCH_TAKEOFF_V2.3 reads "
                               "registry 1.0.0 (frozen)",
               rules=sorted(rules.values(), key=lambda r: r["rule_id"]),
               conflicts=reg["conflicts"] + CONFLICTS,
               question_catalogue=reg["question_catalogue"] + qs,
               rule_store_crosswalk=CROSSWALK,
               levels={"A": "Urban Project master standards (this registry)",
                       "B": "project-specific approved rules (URBAN_PROJECT_RULES_V1, engine/source/project_rules.py)"},
               delta={"builder": "tools/kb_build_1_1.py", "new": sorted(r["rule_id"] for r in NEW),
                      "updated": sorted(UPDATES), "conflicts": [c["id"] for c in CONFLICTS],
                      "questions": [q["pattern"] for q in qs]})
    ids = [r["rule_id"] for r in reg["rules"]]
    assert len(ids) == len(set(ids)), "duplicate rule id"
    return reg


TEXT = json.dumps(build(), indent=1, sort_keys=True, ensure_ascii=False) + "\n"
if __name__ == "__main__":
    if "--check" in sys.argv[1:]:
        same = OUT.is_file() and OUT.read_text(encoding="utf-8") == TEXT
        print("registry 1.1.0 up to date" if same else "registry 1.1.0 differs from a fresh build: run "
                                                        "tools/kb_build_1_1.py")
        sys.exit(0 if same else 1)
    OUT.write_text(TEXT, encoding="utf-8")
    reg = json.loads(TEXT)
    print(len(reg["rules"]), "rules", len(reg["conflicts"]), "conflicts", len(reg["question_catalogue"]),
          "question patterns", OUT.stat().st_size, "bytes")
