# TEST_RUN: Phase 2B-5 overnight engineering program

**Baseline.** Stage A, `64827c6` (Phase 2B-4).

**Final full suite.** `b9baa7b`, run in a separate clone with no private drawing present. This report itself is in a
later commit that adds documents only.

Passing tests prove the stated geometry, arithmetic and bookkeeping against independent or hand-derived truth. They
are not an accuracy measurement: the formal blind evaluation was not started.

## 1. Targeted suites

| suite | tests | result | what it pins |
|---|---|---|---|
| `tests/m9_p2b5` installation layer (`_examples` 39, `_mutations` 23, `_trace` 17, `_cli` 7, `_independence` 4) | 90 | pass | ten worked examples against an independent constructability reference (297 checks), mutation and edge cases, the cut trace, the command line with byte identity of V1 - V2.5 and determinism, the reference's independence from the engine |
| `tests/m9_p2b5/test_p2b5_door_reconcile.py` | 20 | pass | D-V26-06: the hinge, leaf-share and closure limits at their boundaries; one swing per opening; a strict door untouched; held doors through the command line, with a PROVISIONAL doorway waterproofing piece |
| `tests/m9_p2b5/test_p2b5_strip_split.py` | 24 | pass | D-V26-07: two doors and the wall between them at three angles; a door and a passage; five refusals; the leaf-closed box at three angles and its six refusals; through the command line, V2.5 against V2.6 on the real plan's pattern, with hand-derived values (0.2054 → 0.16 m2) |
| `tests/m9_p2b5/test_p2b5_curved_wall.py` | 9 | pass | D-D2 asserted as found, next to the truth |
| `tests/m9_p2b5_bench` (`test_bench` 33, `test_skills` 6) | 39 | pass | the room-reader benchmark (16 synthetic plans, hand truth), the CAD encodings, the vision prototypes and hybrid rules with provenance, the six Urban skills |
| all of the above | **182** | **182 passed** | - |

## 2. Full suite against the baseline, test by test

| | tests | passed | failed | errors | skipped | xfailed |
|---|---|---|---|---|---|---|
| baseline `64827c6` | 8835 | 8196 | 345 | 32 | 160 | 102 |
| final `b9baa7b` | 9017 | 8378 | 345 | 32 | 160 | 102 |

Matched by test identity (class and name) through the JUnit records:

- 182 new tests, all passed (143 in `tests/m9_p2b5`, 39 in `tests/m9_p2b5_bench`);
- 0 removed;
- 0 changed state (no pass → fail, no fail → pass, no other change).

The 345 failures and 32 errors are the known baseline set, in 26 test modules that need git-ignored private datasets
and workbooks. They are reported separately in every phase and are not caused by this one.

An intermediate full suite at `48fb049` (after Stages C - F) gave the same picture: 157 new tests, all passed, 0
changed state.

## 3. Frozen integrity

| check | result |
|---|---|
| V1 - V2.5 outputs on three drawings (the synthetic villa, its mirror, the private reference plan), Mode U and Mode A, against the Stage A snapshot | **968 files, 0 differ**; 39 runs, exit 0. Repeated after every engine change of the program: Stage B, D-V26-06, the held-door doorway state, D-V26-07 |
| `tools/freeze_verify.py check` (FREEZE_BASELINE_INDEX) | 0 frozen artefacts differing |
| `tools/freeze_verify.py env` (ENVIRONMENT_LOCK) | in lock, no package differences |
| `tools/freeze_verify.py closure` | exit 0; identical to the run before D-V26-07 |
| V2.6 on the synthetic villa | only RUN_RULES (the corrections, empty records) and the output manifest differ from the run before each correction; every quantity file is byte-identical |
| benchmark regenerated (`bench_run.py`) | every measured value identical; only runtimes and the new provenance fields changed |

## 4. Real-plan evidence (private run, aggregates)

| step | real-room checks failing (of 66) | other effect |
|---|---|---|
| V2.5 | 11 | - |
| V2.6 with D-V26-06 | 10 | one opening reconciled |
| V2.6 with D-V26-06 and D-V26-07 | **8** | 5 doorways get their threshold, 2 doorway waterproofing pieces lose their wall; every box confirmed by an independent raw-line jamb reading |

Room areas, floor areas and coverage are identical between V2.5 and V2.6 on the reference plan.

## 5. Privacy

The project's privacy scan was run on every new and changed file before each commit, with no findings. It covers
client names, project codes, Arabic text in shareable documents, private room ids and the forbidden figures.
Reference-plan data appears only as aggregates.
