# Regression and frozen-integrity report (deliverable 10)

"Preserve all historical V1 - V2.4 outputs and their byte-identity guarantees. Do not edit frozen baselines, source
drawings or opening_census.py." Every check below was run on the engine commit of this phase (`765318d`). The
reporting commit adds the reports and the generated views, corrects one V2.4 test docstring and makes the proof
drawing writer deterministic (a test helper, see section 3). It changes no engine or CLI code.

## 1. Frozen methods

| Check | How | Result |
|---|---|---|
| V1 .. V2.4 CLI outputs | the six methods on the synthetic villa, its mirror and the reference plan; V2.2 .. V2.4 also with the synthetic heights facts. The baseline was taken from a clean worktree of `2097f2c` (the Phase 2B-2 head) before any edit and compared file by file (SHA-256) with the same runs of the V2.5 code | **747 of 747 files byte-identical** (720 outputs + 27 run logs), every run exit 0 |
| The baseline itself | the same runs from the Phase 2B-2 final evidence (V1 .. V2.3 at `b4d0b6b`, V2.4) | identical to the `2097f2c` baseline |
| `rules/`, `engine/source/opening_census.py` | `git diff 2097f2c` | empty |
| Registry 1.0.0 / 1.1.0 | `tools/kb_build.py --check`, `tools/kb_build_1_1.py --check` | up to date (V2.5 reads 1.1.0, unchanged) |
| Frozen artefacts | `python3 -I tools/freeze_verify.py check --index research/freeze_integrity/FREEZE_BASELINE_INDEX.jsonl` | 0 artefacts differ |
| Freeze import closures | `python3 -I tools/freeze_verify.py closure` | none of the five changed or new code files is in the functional closure of any of the 33 freeze manifests |
| Environment lock | `python3 -I tools/freeze_verify.py env --lock research/freeze_integrity/ENVIRONMENT_LOCK.json` | `in_lock: true` |
| S1 hygiene (`test_m9_s1_package.py`) | the external-figure scan of the S1 files (`membrane_layout.py`, `urban_boq_m9.py` are S1 files) | passes; comments that wrote a bare method version were reworded, the test unchanged |

## 2. How shared code changed without changing V1 .. V2.4

| Shared file | Change | Why V1 .. V2.4 are unaffected |
|---|---|---|
| `engine/source/membrane_layout.py` | the band planner MIN_SEGMENT_V2_5, `pack_rolls`, detail patches | each behind a constraints key (`band_planner`, `detail_pieces`) that no earlier caller passes; without it `_one` runs the original loop and records no new key |
| `engine/source/waterproofing_system.py` | `build_area(..., v25=False)`, `cutting_plan(..., exact=False)`, the V2.5 helpers, `METHOD_V25` | both defaults reproduce V2.4; the new keys are added to a schedule row only when `area["v25"]` exists |
| `engine/source/door_feasibility.py` | `feasibility(..., v25=False)`, `clearances(..., inclusive_reach=False)`, `_placements(..., pier_open_run=False)` | defaults reproduce V2.4 |
| `engine/source/traceability.py` | new | imported only on the V2.5 path |
| `tools/urban_boq_m9.py` | method ARCH_TAKEOFF_V2.5, `--independent-checks`, the drawing binding, BOQ_TRACEABILITY | every addition is behind `method == ARCH_TAKEOFF_V2.5`; `_v24_stage` takes `v25` / `independent` only from it |
| `tests/m9_p2b2/test_p2b2_waterproofing.py` | docstring only (D-V25-06) | asserted values unchanged |

## 3. V2.5 itself

| Check | Result |
|---|---|
| Determinism | the V2.5 runs (villa, mirror, reference plan; U and A modes) twice: **254 of 254 files identical** |
| Through the drawing route | PD-1 reproduces the WP-B hand calculation for both bathrooms (`test_the_drawing_route_reproduces_the_3x4_hand_calculation`); two runs byte-identical (`test_v2_5_is_deterministic`) |
| Opt-in | a V2.4 run carries no V2.5 file, key or method (`test_v2_5_is_opt_in`); V2.5-only inputs are refused by the other methods |
| Reproducible reports | `make_p2b3_docs.py` run twice gives identical files. The first attempt did not: the proof drawing's SHA-256 changed per build (DXF writer timestamps, GUIDs, hash-seed CLASS order), and the rules sheets bind to it. `proof_drawings.py` now writes fixed metadata and sorted classes (byte-identical over five hash seeds) |
| Effect on the project drawings (aggregates) | villa: 6 -> 5 rolls (lower bound 5, proven), consumed 48.25 -> 47.65 m2, installed 46.22 -> 45.91 m2 (the kitchen's 3-roll ALONG_Y layout with 9 seams now wins over ALONG_X with 10). Mirror: identical to the villa. Reference plan: 14 rolls either way (lower bound 14, proven), consumed 138.13 -> 136.36 m2, cutting waste 18.11 -> 16.34 m2, installed unchanged 120.02 m2. No area of either drawing changes its roll count when every open doorway is upturned |

## 4. Tests

| Suite | Result |
|---|---|
| `tests/m9_p2b3` (new) | **59 passed** |
| affected suites with the reference plan (`URBAN_REAL_PLAN_DXF`): m9_p2b3, m9_p2b2, m9_kb, m9_p2b0, m9_p2a, m9_s6, m9_s5, m9_s4, m9_s3, m9_s2_arch, m9_foundation, each with its own `--basetemp` | **659 tests: 647 passed, 0 failed**, 2 xfailed (expected, unchanged), 10 skipped (m9_s4 real-plan regression: it also needs the Round-5 registers, which this environment does not have). The first m9_s6 run stopped on the repository's determinism guard because `proof_drawings.py` was edited while it ran; re-run after the edit: 74 passed, 1 xfailed. m9_p2b3 re-run on the final test code: 59 passed |
| full suite (private clone, `765318d`, no reference plan) | 8165 passed, 345 failed, 32 errors, 160 skipped, 102 xfailed. Test by test against the Phase 2B-2 baseline (`b4d0b6b`: 8106 passed, 345 failed, 32 errors, 160 skipped, 102 xfailed): **0 new failures**, 0 baseline failures changed state, 59 tests added (all passed). The 345 + 32 are the known baseline set (tests that need git-ignored private datasets and workbooks), reported separately and not caused by this phase |
