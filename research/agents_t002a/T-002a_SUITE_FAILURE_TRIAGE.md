# T-002a: triage of the 377 known full-suite failures

Board task T-002a (gate 0). Docs only: no test, engine, rule or data file was edited, skipped or deleted.
Per-test list (all 377 ids, outcome, class, missing input, first failure): `T-002a_FAILING_TESTS.csv` (this folder).

## Result

| Class | Tests | Modules |
|---|---|---|
| PRIVATE_INPUT_ABSENT | **377** (344 failed + 32 errors re-run here; 1 failure from the baseline clone, below) | 26 |
| STALE_EXPECTATION | 0 | 0 |
| REAL_DEFECT | 0 | 0 |

- **376 of the 377** were reproduced here and match the baseline set id for id (the 345 failed + 32 errors of
  `research/urban_m9_n10/FULL_SUITE_COMPARISON.md` §3, HEAD 892a318). Each fails at the **first file read**:
  - 373 at a git-ignored file under `data/experiments/P7757_WALL_TREATMENT_ESTIMATE_01/` (the PA-08 Qortuba and
    PA-09 Al Rashed / villa-blind studies). That includes the `pa09_alrashed_detailed` errors, which fail in fixture
    setup (32);
  - 1 `test_pa08_qortuba_boq_rules.py::test_the_workbook_carries_the_fifteen_house_columns_in_order`: "run workbook_boq
    first" (a workbook generated from the same absent dataset);
  - 1 `test_pa08_qortuba_boq_schema.py::test_the_originals_were_not_modified`: a client upload outside the repository;
  - 1 `test_benchmark_protection.py`: `data/runs/7757/reconciliation/` absent.
- **The 377th**, `tests/m5_reconciliation/test_m5_package.py::test_live_reproduction_of_every_committed_text_file`,
  fails only in a clone whose `data/inputs` is a symlink (source inventory paths are written relative to the clone);
  it passes in the main repository (`research/urban_m9_p2a_acceptance/TEST_RESULTS_AND_WEAKNESSES.md` §2.1). Here,
  with no `data/inputs`, it skips ("prerequisite: the private ST7757 drawings"), so it could not be re-checked.
  Classed PRIVATE_INPUT_ABSENT (clone-layout of the private inputs), not a code defect.
- **What this does not show.** These tests never reach an assertion on content, so whether they would pass with the
  dataset restored is unknown. `data/experiments/P7757_WALL_TREATMENT_ESTIMATE_01` is listed as DERIVED_EXPERIMENT in
  `research/environment_recovery/RECOVERY_MANIFEST.json` (85 entries); restoring it is the only way to move them to
  passed or to STALE_EXPECTATION / REAL_DEFECT.

### Per module (first failing test and its first failure)

| Module | Failed | Errors | First failing test: first failure (missing file) |
|---|---|---|---|
| tests/test_benchmark_protection.py | 1 | 0 | test_the_p7757_reconciliation_document_obeys_the_protocol: `data/runs/7757/reconciliation/P7757_GROUND_OPEN_ZONE_RECONCILIATION.json` |
| tests/test_pa08_qortuba_boq_rules.py | 23 | 0 | test_no_rule_stands_at_urban_standard: `…/pa08_qortuba_boq/URBAN_BOQ_RULE_REGISTRY.json` |
| tests/test_pa08_qortuba_boq_schema.py | 14 | 0 | test_every_item_was_verified_in_the_sheet_it_names: `…/pa08_qortuba_boq/URBAN_PROJECTS_BOQ_SCHEMA_…` |
| tests/test_pa08_qortuba_ext01.py | 13 | 0 | test_no_engine_quantity_is_written_into_the_contractor_registers: `…/pa08_qortuba_ext01/…` |
| tests/test_pa08_qortuba_final_takeoff.py | 10 | 0 | test_the_window_height_is_a_project_input_and_not_an_urban_default: `…/pa08_qortuba_boq/URBAN_OWNER_RULES_V1.json` |
| tests/test_pa08_qortuba_open_passage.py | 9 | 0 | test_open_passage_is_a_permanent_opening_type: `…/pa08_qortuba_boq/URBAN_OWNER_RULES_V1.json` |
| tests/test_pa08_qortuba_opening_completion.py | 19 | 0 | test_the_search_names_what_it_looked_for_and_what_was_there: `…/pa08_qortuba_boq/QORTUBA_OPENING_REGISTER_…` |
| tests/test_pa08_qortuba_owner_inputs_v2.py | 20 | 0 | test_a_window_height_comes_from_the_owner_and_never_from_a_default: `…/pa08_qortuba_boq/URBAN_OWNER_RULES_V1.json` |
| tests/test_pa08_qortuba_owner_rule_audit.py | 26 | 0 | test_every_room_path_adds_back_up_to_its_gross_perimeter: `…/pa08_qortuba_boq/QORTUBA_OWNER_RULE_APPLICA…` |
| tests/test_pa08_qortuba_owner_rules.py | 33 | 0 | test_the_priority_ladder_is_stored_in_order_and_precedent_sits_outside_it: `…/pa08_qortuba_boq/URBAN_OWNER_RULES_V1.json` |
| tests/test_pa08_qortuba_pricing.py | 15 | 0 | test_no_row_carries_a_rate_or_an_amount: `…/pa08_qortuba_pricing/…` |
| tests/test_pa08_qortuba_pricing_audit.py | 15 | 0 | test_every_row_has_exactly_one_class_from_the_list: `…/pa08_qortuba_pricing/…` |
| tests/test_pa08_qortuba_qs01.py | 21 | 0 | test_the_freeze_declares_the_source_only_calculation_complete: `…/pa08_qortuba_qs01/FREEZE_…` |
| tests/test_pa08_qortuba_question_crops.py | 11 | 0 | test_every_open_gap_question_has_its_own_image: `…/pa08_qortuba_boq/QORTUBA_OWNER_QUESTIONS.json` |
| tests/test_pa08_qortuba_workflow_v1.py | 20 | 0 | test_the_case_vocabulary_is_eight_cases_and_no_more: `…/pa08_qortuba_boq/QORTUBA_OPENING_REGISTER_…` |
| tests/test_pa09_alrashed.py | 20 | 0 | test_the_engine_ran_on_the_villa_without_touching_anything_it_should_not: `…/pa09_alrashed/ALRASHED_BLIND_RESULT.json` |
| tests/test_pa09_alrashed_amendment.py | 3 | 0 | test_the_amendment_touches_nothing_that_was_measured: `…/pa09_alrashed/ALRASHED_VALIDATION_AMENDMENT…` |
| tests/test_pa09_alrashed_detailed.py | 0 | 32 | test_ar_fl_01_agrees_across_json_workbook_and_boq: fixture setup, `…/pa09_alrashed/…` |
| tests/test_pa09_alrashed_final.py | 14 | 0 | test_no_window_takes_its_width_from_the_guide: `…/pa09_alrashed/FULL_VILLA_BLIND_PRE_PRICING_…` |
| tests/test_pa09_alrashed_historical.py | 14 | 0 | test_the_workbook_matches_the_hash_the_owner_declared: `…/pa09_alrashed/ALRASHED_HISTORICAL_VALIDATIO…` |
| tests/test_pa09_alrashed_quantities.py | 12 | 0 | test_the_slab_thickness_is_still_not_assumed: `…/pa09_alrashed/ALRASHED_FINISHING_TAKEOFF.json` |
| tests/test_pa09_alrashed_unseal.py | 6 | 0 | test_the_frozen_blind_takeoff_is_untouched: `…/pa09_alrashed/FULL_VILLA_BLIND_PRE_PRICING_…` |
| tests/test_pa09_villa_attribution.py | 8 | 0 | test_a_source_identical_to_the_sealed_input_is_recognised_however_it_is_labelled: `…/pa09_villa_blind/…` |
| tests/test_pa09_villa_blind_inventory.py | 6 | 0 | test_no_commercial_file_was_opened_to_find_out_what_it_was: `…/pa09_villa_blind/…` |
| tests/test_pa09_villa_blind_protocol.py | 11 | 0 | test_the_benchmark_seal_covers_everything_the_owner_asked_to_preserve: `…/pa08_qortuba_boq/QORTUBA_BENCHMARK_SEAL.json` |
| tests/m5_reconciliation/test_m5_package.py | 1 | 0 | test_live_reproduction_of_every_committed_text_file: clone-layout artefact (above) |
| **Total** | **345** | **32** | **377** |

`…` = `data/experiments/P7757_WALL_TREATMENT_ESTIMATE_01`.

## Runs (HEAD 39c9dea = 892a318 + T-001a; no private inputs attached)

| Run | Python | Tests | Passed | Failed | Errors | Skipped | xfailed |
|---|---|---|---|---|---|---|---|
| A | 3.13.16 (agent default `python3`), `requirements.txt` + ezdxf 1.4.4 + pymupdf 1.28.2, no anthropic, shallow clone | 9,432 | 8,664 | 412 | 35 | 216 | 105 |
| **B** | **3.11.17 venv, the lock's pins** | 9,432 | 8,715 | 359 | 39 | 214 | 105 |

Run A's 447 = run B's 398 minus 8 (pip present) + 57: 4 `anthropic` absent, 11 git objects absent in the shallow clone,
42 from Python 3.13 (one-ulp rebuild differences and the frozen-file cascade in finding 1). Run B is the one used for the table above. Its 398 failures and errors = the 376 above + 22 that the baseline clone did
not have, all environmental here:
- 14 need `data/inputs/by_sha256/9f9d1179….dxf` (the Alsenan structural drawing, not linked in this environment): 12
  `test_rebuild_is_byte_identical` builders (d1_1, d1_2, s6_1, pre_s7, pre_s7_1, s7, s7a_qa, s8_1, s8_1a, pre_s8,
  source_recovery_delta, s9a) exit 1 on that path, plus `test_control_plane_r2_gates.py::test_G08…` and
  `test_s9a_package.py::test_bands_redetected_from_the_drawing`;
- 8 in `tests/zz_freeze_integrity/test_fi_verifier_synthetic.py`: `pip freeze` fails because the uv venv has no pip.

## Findings outside the 377 (for the lead; one-line task proposals)

1. **Rebuild tests write into frozen, tracked research packages** (REAL_DEFECT in test hygiene). Under Python 3.13
   (run A) `tests/footing_rebar_s4/test_alsenan_s4_package.py::test_rebuild_is_byte_identical` re-ran the S4 builder,
   which wrote `research/alsenan_footing_rebar_s4/*` in place with one-ulp float differences (`project_known_kg`
   3629.59950617284 -> 3629.5995061728395: `sum()` is compensated from Python 3.12). Nothing restores the files, so
   most of the 42 Python-3.13 failures later in the same session (S4.1 ... S9a package tests and the `zz_freeze_integrity` session guard)
   failed on "frozen baseline altered". The tree was restored with `git checkout -- research`; nothing was committed.
   Proposed task: rebuild tests build into a temporary copy and compare, so a mismatch can never overwrite a frozen
   artefact (test strengthened, not weakened).
2. **The interpreter is not pinned.** The agent environment's `python3` is 3.13; CLAUDE.md and the lock say 3.11, and
   the frozen builders are only byte-reproducible on 3.11. Proposed task: CLAUDE.md / TEST_COMMANDS.md tell agents to
   run the suite with `python3.11` and the lock's pins (`uv venv -p python3.11` works here), and a guard test fails
   fast on another minor version.
3. **`requirements.txt` misses test dependencies** (`ezdxf`, `pymupdf`, `anthropic`): with it alone, 20 modules fail
   collection. Proposed task: point the test instructions to `requirements-lock.proposed.txt` (or add the three).
4. **The 26 modules stay red until `data/experiments/P7757_WALL_TREATMENT_ESTIMATE_01` is restored** (from the private
   store, or regenerated by its tracked scripts once their sources are back). No code task follows from them now.
