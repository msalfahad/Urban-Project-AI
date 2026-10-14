# Tests and regression results (WP-5; deliverable 12)

## 1. New tests (`tests/m9_kb`, 78 tests, all passing)

| File | Tests | What it proves |
|---|---|---|
| `test_kb_registry.py` | 13 | every record complete and valid; every code / test link exists; required families approved; the superseded reading points to the correction; values in data; precedence order; project decisions never general; open conflicts name a question; the wet list; the index is current and carries no identity; `rules/` gains no file; line references name the registry digest; the registry is the builder's output |
| `test_kb_door_standards.py` | 25 | the owner table (16 cases: below / at / above for each category); no second allowance; CAD never overwritten; main entrance as drawn; elevator excluded; scenario areas apart; fallback heights ASSUMED; schedule height wins; dependency map, nothing released; categories from the space model; kitchen-to-outdoor door aluminium; pantry-to-corridor door PVC; elevator schedule from CAD; the Part C reading superseded |
| `test_kb_space_model.py` | 3 | indoor vs outdoor corridor (connecting space reported, not applied); an unlabelled space never assumed interior; a project decision binds one space only |
| `test_kb_finish_scope.py` | 10 | kitchen / pantry / ironing wet; no wet spread to an open plan; full-height porcelain, no band question; an explicit lower tile wins, flagged; marble thresholds from geometry; dry doorways porcelain once; door jamb plaster PROVISIONAL; passage jambs skirted; balcony waterproofing; dry-room skirting kept |
| `test_kb_questions.py` | 7 | every catalogue entry reached by its example; established rules never asked (V2.2 A > 0 -> V2.3 A = 0); repeated instances grouped; engine defects never owner questions; unknown reasons reported; catalogue prefixes exist in the engine; the register is a pure function |
| `test_kb_integration.py` | 13 | V2.3 changes only the lines a registry rule names (both modes); no drawn dimension replaced; deterministic; invariant under translate / mirror / turn / nested blocks / attribute labels / mirror + turn; no assumption released as confirmed; the owner-required view never reaches the BOQ lines; V2.2 never reads the registry |
| `test_kb_wp5.py` | 7 | conflicting opening dimensions (frame vs opening) keep both values; a door symbol with no wall gap is never measured; a wall gap with no symbol is a passage; millimetre and metre drawings agree; a balcony door is aluminium and the balcony waterproofed; several strip faces make one line; a door-closure strip asks for the door |

## 2. The owner's WP-5 list -> tests

| WP-5 case | Test |
|---|---|
| internal PVC below / at / above 1.00 m | `test_the_owner_correction_table[internal-0.90 / internal-1.00 / internal-1.10 / internal-1.20]` |
| bathroom below / at / above 0.90 m | `[bath-0.80 / bath-0.90 / bath-1.00 / bath-1.05]` |
| external aluminium below / above 1.00 m | `[external-0.90 / external-1.00 / external-1.10 / external-1.20]` |
| main entrance larger than the minimum | `test_the_main_entrance_keeps_its_drawn_width` (1.60 m) |
| elevator entrance exclusion | `test_no_elevator_entrance_reaches_the_door_quantities`, `test_the_elevator_schedule_uses_cad_geometry` |
| indoor vs outdoor corridor | `test_indoor_and_outdoor_corridors_are_told_apart` |
| kitchen-to-outdoor door | `test_a_kitchen_door_to_outdoors_is_aluminium` |
| pantry-to-indoor door | `test_a_pantry_door_to_an_indoor_corridor_stays_pvc` |
| wet-room porcelain, no conventional skirting | `test_wall_porcelain_runs_full_height_and_no_paint_band_is_asked`, `test_kitchen_pantry_and_ironing_rooms_take_the_wet_scope` |
| dry-room skirting eligibility | `test_a_dry_room_keeps_its_skirting`, `test_passage_jambs_are_skirted_provisionally` |
| door height from schedule | `test_a_schedule_height_wins_over_the_owner_fallback` |
| door height from owner fallback | `test_an_owner_fallback_height_is_assumed_never_confirmed` |
| conflicting opening dimensions | `test_conflicting_opening_dimensions_keep_both_values_and_hold_the_door` |
| door symbol with no matched wall gap | `test_a_door_symbol_with_no_wall_gap_is_never_measured` (+ V2.1 / V2.2 door-model tests) |
| missing opening symbol with a geometric gap | `test_a_wall_gap_without_a_door_symbol_is_a_passage_not_a_door` |
| mirrored / rotated / translated drawings | `test_v2_3_is_invariant_under_moving_mirroring_and_turning[mirror / turn / translate / mirror-turn]` |
| millimetre vs metre | `test_millimetre_and_metre_drawings_give_the_same_v2_3_result` |
| nested CAD blocks | `test_v2_3_is_invariant_under_moving_mirroring_and_turning[nested-blocks / attribute-labels]` |
| missing room labels | `test_an_unlabelled_space_is_never_assumed_interior` |
| conflicting owner and drawing evidence | `test_an_explicit_lower_tile_height_wins_and_is_flagged`, `test_the_drawn_width_is_never_overwritten` |
| repeated owner questions resolved automatically | `test_established_rules_are_never_asked`, `test_repeated_instances_are_grouped_into_one_question` |

Failing-before / passing-after for the material corrections of this phase: see `INDEPENDENT_AUDIT.md` section 2 (D1 ..
D9). Before each fix the named test failed on the defect (reproduced on the reference plan or the fixture); no
existing test was weakened.

## 3. Full suite (private clone, commit `811c10e` - same tree as `e73d9da`)

Command: `python3 -m pytest -p no:cacheprovider --basetemp=<tmp> --junitxml=<tmp>/junit.xml` (11 min 56 s).

| Run | Passed | Failed | Errors | Skipped | xfailed |
|---|---|---|---|---|---|
| Baseline `9875f40` (Phase 2B-0), same clone | 7,958 | 345 | 32 | 160 | 102 |
| **`811c10e`** | **8,029** | **345** | **32** | **160** | **102** |

- **The full suite is not passing**: 377 failures and errors remain - the same test ids as the baseline (classified in
  `research/urban_m9_p2b0/TEST_RESULTS_AND_INTEGRITY.md`: missing git-ignored datasets and one clone-layout artefact;
  code failures 0).
- **New failures: 0. Baseline failures that disappeared: 0.**
- **Tests not in the baseline: 71, all passing** (64 in `tests/m9_kb` at that commit, 7 Phase 2B-0 tests added
  after the baseline run).
- The 14 tests added afterwards (WP-5 file, metamorphic variants, boundary cases, builder check) are in the affected
  run below.

## 4. Affected suites with the reference plan (`URBAN_REAL_PLAN_DXF` set; working tree of the reporting commit)

| Suite | Passed | xfailed | Skipped | Failed |
|---|---|---|---|---|
| m9_kb | 78 | 0 | 0 | 0 |
| m9_p2b0 | 42 | 0 | 0 | 0 |
| m9_p2a | 99 | 1 | 0 | 0 |
| m9_s6 | 74 | 1 | 0 | 0 |
| m9_s5 | 29 | 0 | 0 | 0 |
| m9_s4 | 20 | 0 | 10 | 0 |
| m9_s3 | 24 | 0 | 0 | 0 |
| m9_s2_arch | 61 | 0 | 0 | 0 |
| m9_foundation | 98 | 0 | 0 | 0 |
| **Total** | **525** | **2** | **10** | **0** |

- **Missing prerequisite (not a pass)**: the 10 `m9_s4` skips need the private Round-5 registers
  (`URBAN_R5_REGISTERS`), which are not available in this environment.
- **Expected failures**: the 2 xfails are recorded open findings (F-9 rotated column outlines; S6P1-NEW-05 a length
  threshold equal to a drafted dimension), unchanged.

## 5. Reference-plan checks (private run, aggregate results only)

V2.3 in both modes: no crash; no negative quantity; ledger conservation ok; CONFIRMED_MISSING 0; 0 unclassified
items; 0 already-answered questions raised; 28 door elements in 28 scenario rows; one elevator shaft candidate with
three landings; one connecting-space candidate. Two defects found by this run were fixed before the reporting commit
(D1 duplicate strip lines, D8 / D9 question wording and patterns).

## 6. Determinism

Two complete V2.3 CLI runs on the three regression drawings in both modes (176 output files): 0 files differ.
