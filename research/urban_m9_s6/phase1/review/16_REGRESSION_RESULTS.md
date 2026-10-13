# Regression results: synthetic and real

## Full suite (S6 Phase 1 working tree = c757d8a)

Two sessions, one after the other (`tests engine`, then `agents`), classified on the merged junit with `research/environment_recovery/classify_test_run.py`.

| Class | S5 (6eba0d2) | S6 Phase 1 (c757d8a) |
|---|---|---|
| CODE_FAILURE | 0 | 0 |
| EXECUTED_PASSED | 7740 | 7810 |
| EXPECTED_FAILURE | 100 | 101 (+1: the strict xfail recording S6P1-NEW-05) |
| MANDATORY_BLOCKED_BY_MISSING_DATA | 376 | 376 |
| SKIPPED_OTHER | 6 | 10 |
| SKIPPED_PREREQUISITE_UNAVAILABLE | 146 | 146 |
| total | 8368 | 8443 |

Gate: **INCOMPLETE**. The record is in `regression/TEST_GATE_M9_S6P1.json`; the detail is in `phase1_notes/S6P1_03_TEST_RESULTS.md`.

The real-plan tests (`tests/m9_s6/test_s6_real_plan.py`, private drawing, env-gated): 18 passed.

**Review note.** These tests assert the coverage gate. Investigation C shows the gate proves plan-area accountability, not element or surface completeness, so read their PASS accordingly.

## Synthetic sweeps (production CLI, separate processes)

The raw per-case results are in `regression/sweep_*.txt`.

| Sweep | Silent (exit 0, wrong) | Blocked (exit 2 + reason) | Flagged on the BOQ | Identical |
|---|---|---|---|---|
| HEAD V1 (6b7a2e4) | 22 | 0 | 0 | 9 |
| V1 at c757d8a (no flag) | 22 (unchanged, as required) | 0 | 0 | 9 |
| V1 `--strict-admission` | **0** | 12 | 10 | 9 |
| V2 | **0** | 9 | 10 | 12 |

**DWG cases** (fake converter):

| Run | Result |
|---|---|
| HEAD V1 | D1 empty, D2 stale, D4 same name and D6 plan = structural are silent; D3 garbage crashes; D5 (no conventions) runs on the defaults |
| V2 | blocks D1, D2, D3, D5 and D6 (exit 2); keeps D4 apart |
| V1 strict | blocks D1, D2, D3 and D6; keeps D4 apart; warns on D5 |

**Finish cases:**
- V1 is silent on the band above tile, the stair hall and the strips. V2 gives a BLOCKED_RFI line for each.
- The diacritic case is unchanged in both: an `ARCH.SPACE` RFI.

## V1 byte identity

| Drawing | Files identical to the hashes taken at 6b7a2e4 |
|---|---|
| synthetic villa | 15 / 15 (`17_HASHES_V1_V2.json`) |
| reference plan | 16 / 16 (private hashes) |

## Reference plan (counts only; details in PRIVATE)

| | V1 | V2 |
|---|---|---|
| lines | 341 | 426 |
| lines with a quantity | 210 | 210 |
| BLOCKED_RFI lines | 123 | 208 |
| coverage gate | — | PASS on GF / 1F / 2F |
| discovery | — | 0 FATAL, 1 BLOCKED_ITEM (stage 7, `NO_SECTION_SOURCE`), 9 warnings |

| Metamorphic variant (lines) | HEAD V1 | V2 |
|---|---|---|
| base | 341 | 426 |
| metres | 192 | 426 (one wall run −0.20 m: Investigation A) |
| nested 2 deep | 342 | 428 (flagged `FILLS_NOT_READ_IN_PLAN`) |
| frames exploded | 0 | 426 |

## Review experiments (this package)

| Experiment | Result |
|---|---|
| Investigation A fixtures A0–A6 (`fixtures_investigation_A/A_FIXTURE_RESULTS.json`) | the frozen census loses the opening in A2, A5 and A6; the robust predicate finds it in all seven |
| Method comparison, 16 cases × 2000 placements (`A_METHOD_COMPARISON.json`) | ROBUST_EPS 1.000 everywhere; frozen 0.496 (mm, random angle) |
| Instrumented reference-plan runs (none / face / overlap / gap / all) | the instrumented run is byte-identical to the committed run; only the face-piece threshold changes outputs; with it, metres = mm |
| Route-G / M4 lintel evidence probe | GF 27 frozen → 29 with the face slack (the same door and window) |
| RFI audit (85 records) | 46 owner rule, 25 missing source info, 9 reader defect, 5 missing implementation; 4 client questions |
