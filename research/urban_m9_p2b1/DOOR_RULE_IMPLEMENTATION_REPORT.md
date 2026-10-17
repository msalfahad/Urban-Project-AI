# Door classification and opening-standard implementation (WP-3; deliverable 6)

ARCH_TAKEOFF_V2.3, `engine/source/door_standards.py`, rules UP-DOOR-CLS-001 .. -006, UP-DOOR-OPEN-002,
UP-DOOR-HGT-001, UP-DOOR-AREA-001, UP-DOOR-DEP-001, UP-ELEV-SCHED-001 (knowledge registry 1.0.0).

## 1. The owner correction, as implemented (UP-DOOR-OPEN-002; supersedes UP-DOOR-MIN-001)

| Door category | Required nominal door opening | Required architectural wall opening |
|---|---|---|
| Internal PVC | 1.00 m | 1.10 m |
| Bathroom PVC | 0.90 m | 1.00 m |
| Ordinary external aluminium | 1.00 m | 1.10 m |

```
ARCHITECTURAL_WALL_OPENING  = REQUIRED_NOMINAL_DOOR_OPENING + 0.10 m       (the table above, held in the registry)
OWNER_REQUIRED_WALL_OPENING = max(CAD_WALL_OPENING, ARCHITECTURAL_WALL_OPENING)
REQUIRED_ENLARGEMENT        = OWNER_REQUIRED_WALL_OPENING - CAD_WALL_OPENING      (flag OPENING_BELOW_OWNER_STANDARD > 1 mm)
nominal door for a wider CAD opening = CAD - 0.10 m  (RULE_DERIVED; a schedule overrides it)
```

- The values live in the registry (`UP-DOOR-OPEN-002.logic.table`), not in code
  (`test_the_owner_correction_values_live_in_data_not_code`).
- No second 0.10 m is ever added: re-applying the rule to a required wall opening changes nothing
  (`test_no_second_allowance_is_added`).
- The CAD measurement is kept separately on every row; the frame span (door block), the nominal leaf (swing radius)
  and the finished clear passage ("NOT_MEASURED") are kept apart and never substituted
  (`test_the_drawn_width_is_never_overwritten`).
- The 0.10 m allowance is recorded as an owner planning rule, not a verified manufacturer installation requirement
  (`logic.never`); a conflicting manufacturer or schedule value would be a drawing / specification fact (precedence 1-2)
  and governs.
- **WP-3 task 1 ("implement UP-DOOR-MIN-001")**: implemented as superseded. The owner correction redefined the minimums
  as nominal doors; UP-DOOR-MIN-001 is DEPRECATED with `superseded_by` UP-DOOR-OPEN-002 and its old reading is tested
  as never applied (`test_the_superseded_part_c_reading_is_not_applied`).

### The owner's examples (all pass; `test_the_owner_correction_table`, 12 cases)

| Case | CAD | Owner-required wall opening | Enlargement |
|---|---|---|---|
| internal PVC | 0.90 | 1.10 | +0.20 |
| bathroom PVC | 0.90 | 1.00 | +0.10 |
| external aluminium | 1.00 | 1.10 | +0.10 |
| internal PVC | 1.20 | 1.20 (no enlargement; nominal door 1.10 RULE_DERIVED) | 0 |
| internal PVC at nominal / at wall standard | 1.00 / 1.10 | 1.10 / 1.10 | +0.10 / 0 |
| bathroom below / at / above | 0.80 / 1.00 / 1.05 | 1.00 / 1.00 / 1.05 | +0.20 / 0 / 0 |
| external below / at / above | 0.90 / 1.10 / 1.20 | 1.10 / 1.10 / 1.20 | +0.20 / 0 / 0 |

## 2. Door categories (UP-DOOR-CLS-001 .. -006)

| Category | Evidence | Opening standard | Quantities |
|---|---|---|---|
| INTERNAL_PVC | interior spaces on both sides | 1.00 / 1.10 | released when the element is CONFIRMED |
| BATHROOM_PVC | a bathroom on one side (PVC material, bathroom standard) | 0.90 / 1.00 | released when CONFIRMED |
| EXTERNAL_ALUMINIUM | the facade or an exterior space on one side | 1.00 / 1.10 | released when CONFIRMED and not held |
| MAIN_ENTRANCE | the external door of the entrance floor with entrance evidence | **as drawn** (no ordinary standard) | measured from its drawing |
| MAIN_ENTRANCE_CANDIDATE | an external door into a hall / living space without entrance evidence | as drawn | withheld until named (B request) |
| ELEVATOR | a lift space or a lift door block | excluded | elevator schedule only |
| CLASS_REVIEW | a side may be exterior (unlabelled space with a facade opening) or a shaft | the standard every candidate class shares (1.10 for internal / external), else a range | withheld |
| CLASS_UNRESOLVED | the sides do not settle the class | as CLASS_REVIEW | withheld |

A kitchen door to a genuine outdoor space is aluminium; a pantry door to an indoor corridor stays PVC (internal
standard, not the bathroom one) - `test_a_kitchen_door_to_outdoors_is_aluminium`,
`test_a_pantry_door_to_an_indoor_corridor_stays_pvc`. A door to a balcony or roof is never a main-entrance candidate
(V2.3 refinement; V2.2 withheld such a door) - `test_a_balcony_door_is_aluminium_and_the_balcony_is_waterproofed`.

## 3. Heights and areas (UP-DOOR-HGT-001, UP-DOOR-AREA-001)

Order: door schedule / section / elevation / explicit dimension (facts `opening_heights` with a SOURCE authority) >
project fallback (`DOOR_ASSUMED`) > owner reference height: 2.20 m internal / bathroom / external, 2.50 m main
entrance (the latter flagged MAIN_ENTRANCE_FALLBACK_SUBJECT_TO_PROJECT_CONTEXT). A fallback is labelled
HEIGHT_ASSUMED and its area AREA_ASSUMED; an assumed area is never in a confirmed total
(`test_an_owner_fallback_height_is_assumed_never_confirmed`, `test_a_schedule_height_wins_over_the_owner_fallback`,
`test_an_assumption_is_never_released_as_confirmed`). The door model receives `<class>_ASSUMED` heights, read after
any source height, so the V2.2 "DOOR HEIGHTS MISSING_SOURCE" question is no longer raised.

## 4. Scenarios, never added together (UP-KB-PREC-001, UP-DOOR-AREA-001)

`DOOR_SCENARIOS.json` / `.csv` hold, per door element: AS_DRAWN (CAD opening, width source and state, frame, leaf,
height, wall-opening area and its state) beside OWNER_REQUIRED (state, required nominal, owner-required wall opening,
enlargement, nominal door for the opening, areas, head basis), the review status
(MODIFICATION_PROPOSED_NOT_APPROVED / NO_MODIFICATION) and the flags. Views: AS_DRAWN (released doors), OWNER_REQUIRED
(the same doors under the owner standard), UNRESOLVED (withheld doors by category and state), EXCLUDED (elevator).
Conservation: every door element in exactly one row (`conservation.ok`). The BOQ lines keep the drawn doors; the
owner-required view never reaches them (`test_the_owner_required_view_never_reaches_the_boq_lines`).

## 5. Dependency map of an enlargement (UP-DOOR-DEP-001)

For every door below the standard: openings (wall-opening area), masonry (blockwork deduction), wall finish per side
(plaster + tile on a wet side, plaster + paint on a dry side), skirting stopping at the wider opening (dry side),
head / reveal plaster, threshold (marble at a wet doorway, floor strip otherwise), doorway waterproofing (wet), lintel
span. A column jamb is a STRUCTURAL_INTERFACE (one column: REVIEW, enlarge to the masonry side only; two columns:
BLOCKS_ENLARGEMENT). Release: REVIEW_REQUIRED - never an automatic quantity, never a buildability approval.

## 6. Results

Synthetic villa (6 door elements): 5 released (3 internal PVC 0.90 -> 1.10, 2 bathroom PVC 0.80 -> 1.00, each +0.20 m)
and 1 main-entrance candidate (1.00 m, as drawn, withheld - no entrance word on the plan). With a schedule height of
2.10 m every released area is CONFIRMED; without, every area is ASSUMED on 2.20 m.

Reference plan (aggregate): 28 door elements, 16 released (14 PVC, 2 aluminium) and 12 withheld (6 provisional widths,
2 main-entrance candidates, 1 class review, 2 class unresolved, 1 aluminium door held for a width review). Under
the owner standard 16 of the 16 released doors are below it: 7 internal PVC (total enlargement 1.10 m), 7 bathroom PVC
(1.40 m) and 2 external aluminium (0.30 m). No elevator entrance is in a door view (the shaft's three landings are on
the elevator schedule). Element conservation: 28 elements, 28 rows.

## 7. Acceptance (WP-3)

| Criterion | Evidence |
|---|---|
| All example cases in Part C (as corrected) pass | `test_the_owner_correction_table` (12 parametrised cases), `test_no_second_allowance_is_added` |
| No elevator entrance in ordinary door quantities | `test_no_elevator_entrance_reaches_the_door_quantities`; reference plan EXCLUDED / door views |
| No drawn width silently overwritten | `test_the_drawn_width_is_never_overwritten`, `test_no_drawn_dimension_is_replaced` |
| Door-element conservation | `conservation.ok` on every run; `test_scenario_areas_are_kept_apart` |

## 8. Limitations (carried to the audit)

- The head height of an enlarged wall opening is not an owner rule (CF-11): taken at the door height, ASSUMED; one
  owner question per run (OQ-02).
- The door jamb / head plaster line uses the internal reference height (2.20 m) for every door when no source height
  is given, including a main entrance (2.50 m reference); the line is PROVISIONAL.
- Accessibility (an accessible bathroom needing a wider clear opening) is not modelled: the bathroom standard applies
  to every bathroom door; a schedule value governs when given.
- Double-leaf and sliding doors: one door set per physical door (UP-DOOR-CLS-006); the opening standard is applied to
  the whole opening, which is correct for a single opening but not a verified rule for double leaves.
