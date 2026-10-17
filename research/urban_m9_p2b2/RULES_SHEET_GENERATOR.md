# Project Engineering Rules Sheet generator (deliverable 4)

Program Part 2 (Level A / Level B) and Part 5 (the comparison sheet). Code: `engine/source/project_rules.py`; registry
rule UP-RULES-001; tests `tests/m9_p2b2/test_p2b2_project_rules.py` (9) and the CLI tests in
`tests/m9_p2b2/test_p2b2_integration.py`. A worked example on the synthetic villa: `RULES_SHEET_EXAMPLE.md` (generated).

## 1. Two rule levels

| Level | What | Where it lives |
|---|---|---|
| A - Urban master standards | the owner-approved standards (roll, lap, upturn, door widths and heights, wet scope ...) | `knowledge/URBAN_ENGINEERING_KNOWLEDGE_1.1.0.json` |
| B - project rules | values a project's drawings, schedules, details, specifications or an owner approval set for that project | one `URBAN_PROJECT_RULES_V1` JSON per project, passed with `--project-rules` (ARCH_TAKEOFF_V2.4 only) |

A Level B rule overrides Level A **only inside its scope**. Both values stay on the sheet: the Urban value is never
deleted, the project value never silently wins outside its scope.

## 2. Input format (`URBAN_PROJECT_RULES_V1`)

```json
{"schema": "URBAN_PROJECT_RULES_V1", "project_id": "...", "drawing_revision": "...",
 "rules": [{"id": "PR-01", "rule_id": "UP-WP-003", "parameter": "upturn_h_m", "value": 0.30,
            "scope": {"kind": "LOCATION_TYPE", "types": ["BATHROOM"]},
            "source": {"kind": "DETAIL", "ref": "detail 4 / A-502"}}]}
```

| Field | Allowed |
|---|---|
| `rule_id` / `parameter` | the parameters the engine can apply (table below); anything else is listed as ENGINE_LIMITATION (PROJECT_RULE_NOT_SUPPORTED) and never applied |
| `scope.kind` | PROJECT, LOCATION_TYPE (`types`), DOOR_CATEGORY (`categories`), FLOOR (`floor`, optional `types` / `categories`), ROOM (`floor` + `point_m`: the one room containing the point), OPENING (`floor` + `opening_id`, or `point_m`: the nearest opening centre within 0.60 m), WALL (`floor` + `point_m`: the nearest wall centreline within half its thickness + 0.05 m) |
| `source.kind` | DRAWING -> DRAWING_CONFIRMED; SCHEDULE / DETAIL / SPECIFICATION -> PROJECT_SPECIFIED; OWNER_PROJECT_APPROVAL -> OWNER_PROJECT_APPROVED |

A value outside its range, an unknown scope or a missing source is refused at load (`ProjectRulesError`), never
coerced.

| Rule | Parameter | Range / values | Affects |
|---|---|---|---|
| UP-WP-001 | roll_width_m, roll_length_m | 0.3 - 5.0 m, 1 - 100 m | membrane layout, procurement |
| UP-WP-002 | lap_m | 0.02 - 0.50 m | layout, installed membrane, procurement |
| UP-WP-003 | upturn_h_m | 0.05 - 1.50 m | FIN.WP.WALL_UPTURN, doorway transition alternatives, layout |
| UP-WP-003 | termination_detail | TERMINATION_BAR / TURN_DOWN / WATER_STOP | FIN.WP.TERMINATION |
| UP-WP-DOOR-001 | doorway_detail | UPTURN_ACROSS_THRESHOLD / CONTINUATION_TERMINATED / JAMB_RETURNS | FIN.WP.DOORWAY_TRANSITION |
| UP-WP-004 | penetration_treatment, corner_treatment | {kind: PATCH, size_m} or {kind: PROPRIETARY} | penetrations / corners (material) |
| UP-WP-MAT-001 | system | {system_id, name, ...} | the procurement group (with the roll and lap the area resolves); a specified system is required for a CONFIRMED roll count |
| UP-WP-LAY-001 | min_reusable_m | 0.05 - 5.0 m | offcut reuse in the cutting plan |
| UP-DOOR-OPEN-002 | required_nominal_door_m, allowance_m | 0.5 - 3.0 m, 0 - 0.5 m | door standard, enlargement, feasibility |
| UP-DOOR-HGT-001 | door_height_m | 1.8 - 4.5 m | door heights, jamb plaster |
| UP-DOOR-FEAS-001 | min_pier_m | 0 - 1.0 m | feasibility placements (replaces the 0.10 m engine threshold) |
| UP-DOOR-FEAS-001 | wall_structure | STRUCTURAL / NON_STRUCTURAL | feasibility class |

## 3. Resolution (`Resolver.get(rule_id, parameter, target)`)

1. Candidates: the supported project rules of that rule and parameter whose scope matches the element (a point scope
   is matched through its binding).
2. The most specific scope wins: PROJECT 0 < LOCATION_TYPE / DOOR_CATEGORY 1 < FLOOR 2 < ROOM 3 < WALL 4 < OPENING 5
   (+0.5 for a FLOOR or ROOM scope narrowed by types / categories). The overridden rules are listed with the result.
3. Two rules of the same rank with different values: **CONFLICT_REVIEW, value None** - the quantity that needs it is
   withheld (BLOCKED_RFI / BOUNDED_EXPOSURE), both values are kept, the conflict goes to the approvals list. The same
   value from two sources is not a conflict.
4. No project rule: the Urban value with OWNER_STANDARD_ASSUMED (or MISSING_DOCUMENT where the Urban registry has no
   value, e.g. the doorway detail; ENGINE_LIMITATION for the 0.10 m pier threshold).
5. Every resolution is counted (`usage`: rule, parameter, state, value, project rule ids, number of elements).

## 4. The sheet

Built before any quantity: its rule rows depend only on the inputs (registry, project rules, bindings, facts,
decisions). Fields of every row: Rule / Urban standard / Drawing-specification / Applied rule / Source / Status /
Impact (trades and BOQ items), plus scope and notes. Fifteen sections (Part 5): project identification, architectural
rules, door standards, windows, floor finishes, wall finishes, skirting, waterproofing, ceilings, MEP interfaces,
structural measurement, waste and procurement, assumptions, unresolved conflicts, owner-approved project exceptions.
Seven states: DRAWING_CONFIRMED, PROJECT_SPECIFIED, OWNER_STANDARD_ASSUMED, OWNER_PROJECT_APPROVED, CONFLICT_REVIEW,
ENGINE_LIMITATION, MISSING_DOCUMENT.

A project rule in a conflict is CONFLICT_REVIEW on its own row as well as on the section-14 row: a conflicting value is
never shown as applied (`test_a_conflicting_project_rule_is_never_shown_as_applied`).

## 5. Hash, binding to outputs, invalidation

- `rules_sha256` = SHA-256 of the canonical rule part (registry rule set and digest, every rule row except the project
  identification, the project rules, the bindings). `sheet_sha256` adds the project identification (drawing file and
  sha256, revision).
- Every V2.4 JSON output with a run record carries `rules_sha256`; `OUTPUT_MANIFEST.json` lists every file of the run
  (BOQ lines, CSVs, workbook, overlays included) with its SHA-256 under the same rules hash; the workbook SUMMARY sheet
  states both hashes (`test_the_rules_sheet_hash_is_in_every_v2_4_output`).
- On a run into an OUT folder that holds an earlier sheet: same `rules_sha256` -> UNCHANGED; different ->
  RULES_CHANGED: the changed rows, affected trades and items are listed and the earlier outputs are moved to
  `SUPERSEDED_<n>` before the new ones are written - never reused, never deleted
  (`test_a_changed_project_rule_moves_the_earlier_outputs_aside`). A registry change changes the hash too.

## 6. Questions it raises

| Pattern | Category | When |
|---|---|---|
| PROJECT_RULE_CONFLICT | C_RULE_CONFLICT | two same-rank project rules disagree (one question per conflict) |
| PROJECT_RULE_UNBOUND | B_MISSING_DRAWING_EVIDENCE | a point scope lies in no element of its kind |
| PROJECT_RULE_NOT_SUPPORTED | E_ENGINEERING_DEFECT | the engine has no such parameter (the rule is listed, not applied) |

## 7. Limits

- Scope binding of ROOM / WALL / OPENING rules is by a point; a project that names elements by drawing tag needs a
  tag binding (not built).
- Facts (`URBAN_ARCH_FACTS_V1`) and project decisions keep their own files; the sheet lists them (section 1 / 2 / 4)
  but they are not Level B rules.
- The sheet states what is applied; it does not check a project value for engineering sense beyond the range check.
