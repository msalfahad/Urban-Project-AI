# Rule precedence and provenance: verification (Phase 2B-5, Parts 7 and 8.3)

Every owner standard in Part 7 of the program was traced to the record that encodes it (registry
`knowledge/URBAN_ENGINEERING_KNOWLEDGE_1.1.0.json`, with `rules/` unchanged) and to the tests that exercise it. No
standard was changed in this program, and the project rules sheet was produced per run as before. The synced
`quantity-takeoff-rules` skill is a secondary reference only; where it differs from the owner's rules, the owner's
rules govern (`MCP_SKILLS_AUDIT.md` §5).

## 1. The owner standards of Part 7

| standard (Part 7) | encoded in | status | exercised by | note |
|---|---|---|---|---|
| membrane roll 1.00 x 10.00 m | UP-WP-001 | OWNER_APPROVED | V2.5 / V2.6 worked examples (`tests/m9_p2b3`, `tests/m9_p2b5`) | a project-specified system replaces the roll (the override is in the rule) |
| overlap 0.10 m (owner planning rule) | UP-WP-002 | OWNER_APPROVED | the same examples; the flange is kept apart from the lap (D-V26-01) | a product's own lap is a product value, never assumed |
| general upturn 0.20 m | UP-WP-003 (0.15 m: UP-WP-UPTURN-015 DEPRECATED) | OWNER_APPROVED | upturn lines exact in the B10 arc room and the five real rooms | doorway widths are never upturn (rule text) |
| wet areas: bathrooms, kitchens, pantries, ironing rooms (laundry by project) | UP-WET-001 (`wet_codes`: BATHROOM, KITCHEN, PANTRY, IRONING, LAUNDRY; LAUNDRY needs project confirmation) | OWNER_APPROVED | Stage C rooms; `tests/m9_p2b2` | conflict CF-03 (pantry) recorded and resolved in the registry |
| roofs and balconies | UP-WP-ROOF-001 | OWNER_APPROVED | IX-08 (roof) in `tests/m9_p2b5` | - |
| doorway transitions, corners, penetrations, terminations need details | UP-WP-DOOR-001, UP-WP-004 | OWNER_APPROVED | V2.6: counted and withheld, junction UNRESOLVED | no detail is selected by the engine |
| product specification vs company default | UP-KB-PREC-001 (source hierarchy), UP-WP-001 override | OWNER_APPROVED | `JOINT_OFFSET_UNVERIFIED` without a product value | - |
| door nominal 1.00 m (ordinary), 0.90 m (bathroom), + 0.10 m opening allowance | UP-DOOR-OPEN-002 (UP-DOOR-MIN-001 DEPRECATED, CF-01) | OWNER_APPROVED | V2.5 door worked examples; Stage C feasibility (0.80 m CAD → 0.70 m nominal available, ENLARGEMENT_REQUIRED 0.20 m) | - |
| door height 2.20 m, main entrance 2.50 m | UP-DOOR-HGT-001 (sources first; owner heights labelled fallbacks) | OWNER_APPROVED | HEIGHT_ASSUMED flags | D-C5: the Mode A test heights use 2.10 m, a synthetic parameter, not a project value |
| project drawings override Urban standards within scope | UP-RULES-001 (levels A / B, one rules sheet per project) | OWNER_APPROVED | `tests/m9_p2b2/test_p2b2_project_rules.py` (scope, most-specific scope, conflicts never discarded, a changed sheet invalidates outputs) | - |
| widening not assumed feasible | UP-DOOR-FEAS-001, UP-DOOR-DEP-001 | OWNER_APPROVED | feasibility view: UNRESOLVED without evidence, never auto-released | - |
| elevator doors belong to the elevator scope | UP-DOOR-CLS-005, UP-ELEV-SCHED-001 | OWNER_APPROVED | lift candidates excluded from door totals | - |
| wet rooms: full-height wall porcelain (company default, subject to drawings) | UP-FIN-WALL-001 (an explicit drawn height governs) | OWNER_APPROVED | Stage C wall porcelain checks | - |
| no conventional skirting under full-height tiles | UP-WET-001 scope + UP-SKIRT-001 + UP-CER-004 (owner library) | OWNER_APPROVED | B10: skirting NOT_APPLICABLE_WITH_EVIDENCE | **D-C4 conflict**: UP-CER-004's exception keeps skirting where the tile is not full height (2.40 m tile, 3.00 m finish), while the program says "no skirting in wet rooms" - an owner decision |
| wet-room thresholds marble | UP-THR-001 | OWNER_APPROVED | thresholds PROVISIONAL; D-C2 attribution | - |
| no double counting of jambs, openings, strips, thresholds | UP-THR-001 (`never: the strip counted in two floors`), UP-DOOR-CLS-006 (one double-leaf door = one set) | OWNER_APPROVED | D-V26-06 moves a strip from porcelain to threshold; floor area conserved (`BOQ_IMPACT.md`). D-V26-07 splits a face at its openings' boxes: the pieces and the remainder add back to the face, which stays counted once in the floor areas (`test_p2b5_strip_split.py`) | - |
| ceilings exclude voids / open-to-below | UP-CEIL-001 | OWNER_APPROVED | `tests/m9_s5` (voids, double height) | - |

## 2. Precedence

UP-KB-PREC-001 is the registry's `precedence_rule`:

- the source authority hierarchy applies;
- the as-drawn value is kept apart from the owner-required value, each with its own source;
- a difference between them is a proposed modification, never a correction.

UP-RULES-001 sets the two levels:

- level A, the Urban master standards;
- level B, project rules within their scope.

Conflicting project documents are recorded as conflicts (`conflicts` in the registry; OWNER_QUESTIONS.json per run),
never resolved by an arbitrary order.

## 3. Provenance classes, and where the engine distinguishes them

| class (Part 7) | how a BOQ line or record shows it |
|---|---|
| CAD-measured | `evidence_state` SOURCE_DERIVED with the geometry formula; the drawing sha256 in RUN_RULES |
| project-specified | the rules sheet (level B, `PROJECT_RULES_SHEET.json`) or a facts value with its authority |
| owner-standard | a level-A rule id on the line (`rule_id`, registry 1.1.0) |
| assumed | PROVISIONAL with an `_ASSUMED` flag (e.g. HEIGHT_ASSUMED); kept out of confirmed areas |
| proposed design modification | door feasibility: as-drawn and owner-required kept apart (UP-DOOR-AREA-001); ENLARGEMENT_REQUIRED is never released |
| unresolved conflict | BOUNDED_EXPOSURE / BLOCKED_RFI lines, OWNER_QUESTIONS.json, the registry `conflicts` |

The urban-rule-reconciliation skill (`.claude/skills/urban-rule-reconciliation/SKILL.md`) applies this table.

## 4. Part 8.3: mutation and edge tests, and where each lives

| mutation | test |
|---|---|
| door moved near a column | `tests/m9_p2b5/test_p2b5_mutations.py::test_a_door_next_to_a_column` |
| wall opening reduced by 10 cm | `::test_a_door_ten_centimetres_narrower` |
| room mirrored / drawing rotated | `::test_translation_mirror_and_rotation_keep_every_quantity`, `::test_an_arbitrary_rotation_keeps_the_quantities`; benchmark B02, B06, B09 |
| room polygon left open | `tests/test_free_space.py::test_without_the_barrier_the_room_leaks_through_the_doorway`, `tests/m2_generic_engine/test_synthetic_villas.py::test_unclosed_cells_are_reported_never_silent` |
| incorrect scale | `::test_a_tiny_room_from_a_wrong_scale_is_computed`; the admission gate's unit checks; raster `test_a_wrong_scale_is_caught` (SCALE_SUSPECT); metres benchmark C02 |
| duplicate door blocks / a doorway twice | `tests/test_qs_core_admission.py::test_one_door_drawn_twice_is_one_opening_with_the_other_marked_a_duplicate`, `::test_a_doorway_listed_twice_is_flagged` |
| missing drainage symbols | `::test_a_wet_room_without_a_drawn_drain_is_not_shown` |
| overlapping membrane regions, narrow offcuts, internal corners | IX-01 - IX-08 (`tests/m9_p2b5/test_p2b5_examples.py`), `::test_offcut_class_boundaries`, `::test_an_internal_corner_count_follows_the_ring` |
| conflicting project rules | `::test_conflicting_project_rules_block_the_layout`; `tests/m9_p2b2/test_p2b2_project_rules.py::test_two_project_rules_that_disagree_are_a_conflict_never_discarded` |
| revised drawing hash | `tests/m9_p2b2/test_p2b2_project_rules.py::test_a_changed_rules_sheet_invalidates_earlier_outputs`; `tests/m7_reliability/test_m7_release.py::test_an_approval_holds_only_for_the_revision_and_the_item_it_was_made_on` |
| room renamed without geometry change | `::test_a_renamed_room_changes_only_its_name` |
| new in this program | door-symbol limits at their boundaries (`test_p2b5_door_reconcile.py`); CAD encodings and the XREF refusal (`test_bench.py::test_the_cad_encodings`); arc rooms (`test_p2b5_curved_wall.py`) |

Each of these asserts a value or a refusal. None merely checks that the code runs.
