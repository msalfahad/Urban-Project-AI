# Frozen-version integrity evidence (deliverable 12)

"Do not modify V1, V2, V2.1, V2.2 or V2.3 historical outputs. Do not modify opening_census.py. Use a new explicitly
opt-in method version for changed quantity behavior." Every check below was run on the engine code of the reporting
commit (`b4d0b6b`; the reporting commit adds reports and one test assertion only) and, before the wording fix of
`b4d0b6b`, on `3b0f12f` with the same results.

| Check | How | Result |
|---|---|---|
| V1 .. V2.3 CLI outputs | the five methods on the synthetic villa, its mirror and the reference plan (V2.2 / V2.3 also with the synthetic heights facts): baseline from a clean worktree of `7b83c20` before any edit, compared file by file (SHA-256) with the same runs of the final code | **505 of 505 files byte-identical** (484 outputs + 21 run logs), every run exit 0 |
| Registry 1.0.0 (V2.3 reads it) | SHA-256 against `7b83c20` | identical (`e97d01f4cac84d6e...`); `knowledge.version()` outside `using()` is still 1.0.0 |
| V2.3 does not follow 1.1.0 | `test_v2_3_is_unchanged_by_v2_4_and_does_not_follow_the_new_registry`: the registry 1.1.0 replaced by a copy with a 0.25 m upturn | V2.3 lines and run record byte-identical; the V2.4 upturn scales 0.25 / 0.20 and its rules hash changes |
| `rules/`, `opening_census.py` | `git diff 7b83c20` | empty |
| engines reused, not edited | `git diff 7b83c20 -- membrane_layout.py door_model.py door_standards.py arch_measure.py owner_finish_scope.py` | empty |
| Frozen artefacts | `python3 -I tools/freeze_verify.py check --index research/freeze_integrity/FREEZE_BASELINE_INDEX.jsonl` | 0 artefacts differ |
| Freeze import closures | `python3 -I tools/freeze_verify.py closure` | none of the 11 changed or new code files is in the import closure of any of the 33 freeze manifests |
| Environment lock | `python3 -I tools/freeze_verify.py env --lock research/freeze_integrity/ENVIRONMENT_LOCK.json` | `in_lock: true` (Python 3.11.17, 0 package differences) |
| Registry builders | `tools/kb_build.py --check`, `tools/kb_index.py --check`, `tools/kb_build_1_1.py --check` | all up to date (1.1.0 = 1.0.0 + the delta, reproducible) |
| V2.4 determinism | the V2.4 runs (villa, mirror, reference plan; with and without facts) twice | 242 of 242 files identical |
| Rules-hash binding | `test_the_rules_sheet_hash_is_in_every_v2_4_output` | every output file listed with its SHA-256 under the rules hash |

## How the V2.3 outputs stay unchanged although shared files changed

| Shared file | Change | Why V1 .. V2.3 are unaffected |
|---|---|---|
| `tools/urban_boq_m9.py` | V2.4 method, stage, outputs, `--project-rules`, `OUTPUT_MANIFEST.json` | every addition is behind `method == ARCH_TAKEOFF_V2.4` or a key only V2.4 writes (`rules_sheet`); the original body runs as `_arch_compute` for every other method |
| `engine/source/knowledge.py` | versioned registry (`using`, `version`, `rule_set`), `wp_standard()` | the default version is 1.0.0; only V2.4 enters `using("1.1.0")`; `policy_record` prints the same relative path for 1.0.0 |
| `engine/source/surface_ledger.py` | table ELIGIBILITY_V0_3_WP_SYSTEM behind `wp_system=True`; the owner-scope label names the active registry | V2.3 calls without the flag; the label reads 1.0.0 for V2.3 as before |
| `engine/source/boq_line.py` | four new item codes (FIN.WP.WALL_UPTURN, FIN.WP.DOORWAY_TRANSITION, FIN.WP.TERMINATION, FIN.WP.PENETRATION) | no earlier method emits them |
| `engine/boq_room_workbook.py` | three SUMMARY rows when the run has a rules sheet | only V2.4 runs carry `rules_sheet` |

## Two changes outside the engine, stated plainly

1. **`tools/arch_synth.py` (the synthetic test-drawing generator).** Its mirror variant turned every mirrored door leaf
   half a turn about the hinge (`rotation 180 - r` instead of `-r`): mirrored doors closed outside their gap and
   swung into the other room. The V2.4 door-swing check exposed it
   (`test_mirrored_and_rotated_geometry_give_the_same_result`). The generator now produces a true mirror. The frozen
   snapshots are unaffected (they read the mirror drawing generated in Phase 2B-0); the earlier metamorphic suites that
   generate mirrors (`tests/m9_s2_arch`, ...) still pass.
2. **`tests/m9_foundation/test_m9_s1_package.py`.** Its hygiene test rejects any decimal in the S1 files that equals an
   external benchmark figure. The owner-mandated method name `ARCH_TAKEOFF_V2.4` contains `2.4`, which collides with
   one such figure. The test now removes `ARCH_TAKEOFF_V<n>.<n>` method identifiers before scanning; the
   forbidden-number and identifier checks of the same test are unchanged, and two comments that wrote a bare "V2.4"
   were reworded instead of exempted.
