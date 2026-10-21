# Tests and remaining failures (deliverable 11)

## 1. New tests of this phase - `tests/m9_p2b2` (63, all passing)

| File | Tests | What they prove |
|---|---|---|
| `test_p2b2_registry.py` | 10 | registry 1.1.0 reproducible and link-valid (every code and test reference exists), 1.0.0 unchanged and still the default, the approved waterproofing and door values cannot change silently, the superseded 0.15 m upturn keeps its history, crosswalk / collision, conflicts, REFERENCE_ONLY notes, question catalogue examples classify |
| `test_p2b2_project_rules.py` | 9 | scoped override, most specific scope wins, conflicts kept and never applied (also on the sheet), unbound point scope reported, unsupported parameter listed, invalid values refused, 15 sections and 7 states, a changed sheet invalidates, the hash is input-only |
| `test_p2b2_waterproofing.py` | 20 | the program's Part 3.6 list (below), the window-frame fix, the segmentation check |
| `test_p2b2_door_feasibility.py` | 17 | the program's Part 4.7 list (below), the inconsistent swing symbol, a stair at the enlarged jamb |
| `test_p2b2_integration.py` | 7 | through the CLI: the rules hash in every output, invalidation through SUPERSEDED_1, jamb plaster by category height, V2.3 unchanged and blind to a modified 1.1.0, determinism and ledger conservation, the villa before / after, the eight-question summary |

Program Part 3.6 -> tests: rectangular room (`test_rectangular_bathroom_hand_calculation`, a full hand calculation),
L-shaped room and internal / external corners (`test_l_shaped_bathroom_corners_and_upturn`), kitchen and pantry
(`test_kitchen_and_pantry_get_membrane_material`), irregular roof (`test_irregular_roof`), balcony
(`test_balcony_upturn_on_walls_and_open_edge_termination`), multiple drains
(`test_multiple_floor_drains_are_counted_and_their_treatment_withheld`), pipes (`test_pipe_penetrations`), doors
(`test_doorways_are_transitions_not_wall_upturns`), columns (`test_internal_columns`), orientations
(`test_both_strip_orientations_are_evaluated_and_the_choice_is_deterministic`), project upturn override
(`test_project_upturn_overrides_the_standard`), project overlap override (`test_project_overlap_overrides_the_standard`),
partial roll reuse (`test_partial_roll_reuse_only_with_a_cutting_plan`), insufficient detail
(`test_missing_detail_blocks_the_quantity`), same area / different shape
(`test_same_area_different_shape_changes_material_and_rolls`), never a confirmed roll count without a basis
(`test_roll_count_never_confirmed_without_a_valid_basis`), separate systems (`test_separate_systems_are_never_combined`),
A / B / C balance (`test_the_three_quantities_balance`).

Program Part 4.7 -> tests: opening already large enough and exactly at the standard; 10 and 20 cm undersized;
bathroom 0.80 m needing 0.20 m; beside a column; beside a non-structural wall return; at a corner; beside a window;
swing into a corridor; double-leaf main entrance; conflicting dimensions; unknown structural classification; missing
height; a project-specific width standard; no proposed modification released as drawn; mirrored / rotated / moved
geometry (one test each, names in `test_p2b2_door_feasibility.py`).

Failing first: every correction of `INDEPENDENT_REVIEW.md` section 1 was reproduced by its test before the fix
(D-04 for example: 5.6 m upturn instead of 6.2 m). No existing test was weakened; one existing hygiene test was
narrowed for method identifiers, with the reason (`FROZEN_INTEGRITY.md`).

## 2. Affected suites with the reference plan (`URBAN_REAL_PLAN_DXF` set)

| Suite | Passed | xfailed | Skipped | Failed |
|---|---|---|---|---|
| m9_p2b2 | 63 | 0 | 0 | 0 |
| m9_kb | 78 | 0 | 0 | 0 |
| m9_p2b0 | 42 | 0 | 0 | 0 |
| m9_p2a | 99 | 1 | 0 | 0 |
| m9_s6 | 74 | 1 | 0 | 0 |
| m9_s5 | 29 | 0 | 0 | 0 |
| m9_s4 | 20 | 0 | 10 | 0 |
| m9_s3 | 24 | 0 | 0 | 0 |
| m9_s2_arch | 61 | 0 | 0 | 0 |
| m9_foundation | 98 | 0 | 0 | 0 |
| **Total** | **588** | **2** | **10** | **0** |

## 3. Full suite (private clone, with the git-ignored datasets it has)

Command: `python3 -m pytest -p no:cacheprovider --basetemp=<tmp> --junitxml=<tmp>/junit.xml`; compared test by test
with the Phase 2B-1 junit of `d604b55`.

| Run | Passed | Failed | Errors | Skipped | xfailed |
|---|---|---|---|---|---|
| Baseline `d604b55` (Phase 2B-1) | 8,043 | 345 | 32 | 160 | 102 |
| `3b0f12f` (engine commit of this phase; 10 min 46 s) | 8,105 | 346 | 32 | 160 | 102 |
| **`b4d0b6b` (engine code of the reporting commit; 10 min 50 s)** | **8,106** | **345** | **32** | **160** | **102** |

- `3b0f12f`: **1 new failure** -
  `tests/structural_comparison_engine/test_rebar_product_firewall.py::test_every_rebar_module_in_engine_is_declared`.
  The firewall lists every engine module that mentions "reinforc". `project_rules.py` and `waterproofing_system.py`
  said "corner reinforcement" (the membrane corner item, nothing to do with rebar). Fixed in `b4d0b6b` by naming the
  item "corner treatment" in the engine (declaring them as rebar-aware would have been false); the reports keep the
  owner's wording.
- `b4d0b6b`: **new failures 0**; baseline failures that disappeared: 0; tests not in the baseline: 63, all passing
  (`tests/m9_p2b2`). The wording fix changed no quantity: the V2.4 lines and roll counts of all five V2.4 runs are
  identical between the two commits (only the rules-sheet text and therefore its hash differ).
- **The full suite is not passing**: the remaining 377 failures and errors are the baseline set (missing git-ignored
  datasets and one clone-layout artefact, classified in `research/urban_m9_p2b0/TEST_RESULTS_AND_INTEGRITY.md`).

## 4. Other checks

`tools/kb_build.py --check`, `tools/kb_index.py --check`, `tools/kb_build_1_1.py --check`: up to date. Registry links
(`knowledge.validate(..., links=True)`) on 1.0.0 and 1.1.0: no problem. Frozen outputs, freeze verifier, closures,
environment lock, determinism: `FROZEN_INTEGRITY.md`.
