# M2 TEST_RUN: the generic engine (route G)

Baseline: M1 `8e2198b`. Full suite at `fe41de1` on 2026-10-10. The commits of the round are in `16_COMMITS_AND_BRANCH.md`.

M2 releases nothing. A generic run never produces VERIFIED: source-complete items are PROVISIONAL with support SOURCE_COMPLETE_UNREVIEWED. The frozen stages and the frozen M1 files are unchanged, and the project gate stays **INCOMPLETE**. Passing tests prove bookkeeping, geometry and arithmetic, not engineering approval.

## What the M2 tests pin (`tests/m2_generic_engine`, 58 tests)

- **CAD geometry fixtures (7), hand-derived truth:**
  - a bulge semicircle;
  - a mirrored INSERT arc (centre, sweep and layer inheritance);
  - an OCS-extruded arc;
  - nested rotated blocks;
  - MINSERT copies with distinct ids;
  - an ellipse (which crashed the intake before);
  - layer-0 inheritance keyed by the kernel's decimal ids (the hex-key bug found by the defect set).
- **Components (26):**
  - attribute-row schedules under both tag sets match the design;
  - drawn text tables, including a combined B3/B4 row and unit inference;
  - a duplicate mark with different sizes is a conflict, never a choice;
  - bar notation (5 grammars); an unreadable callout is blocked, not guessed;
  - closed links and hooks against an independent derivation, to 1 µm (the engine's rounding);
  - mass d²/162;
  - CAD heal: merge without bridging a column, plus a snap / wide-snap / no-snap trio;
  - EN and AR titles (an opening "schedule" word wins);
  - normalisation.
- **Synthetic end-to-end (13):**
  - two seeds, clean and with defects: every family within 1e-5 of the design truth, detection 1.0, no polluted range;
  - hard defects are closed and every widened snap reported;
  - with snapping disabled, the slab loss is reported, never silent;
  - no concrete is owned twice (bands against columns and panels);
  - per-owner area conservation (BEAM / COLUMN / PANEL faces equal the design areas);
  - the generator imports no engine module;
  - route G through the one-command CLI (no VERIFIED; NOT DETECTED lists every out-of-scope family; outputs carry no Arabic source text);
  - the frozen M1 CLI is byte-identical to its freeze (sha256);
  - the intake cache hits on the second run, with byte-identical outputs.
- **Room slice (3):**
  - four rooms (one Arabic label) with area, perimeter, door widths and skirting exactly as drawn;
  - wet-room rules: unresolved skirting, zero under full-height tile (UP-CER-004), doorway piece in the waterproofing (UP-WP-003), 0.15 m upturn (UP-WP-002);
  - an unlabelled space is a coverage risk.
- **Stair (4):** the owner's worked example (UP-STAIR-003), hand geometry, scenarios side by side, and the sanity range as a diagnostic only.
- **Package (5):**
  - the deliverables are present;
  - hygiene and the benchmark firewall hold over every text file of the package;
  - the 89 components are listed one by one;
  - the benchmark file holds positions only;
  - the Alsenan generic run reproduces the committed comparison (19 matched slab faces, no silent face loss, no VERIFIED).

## Targeted checks

| check | result |
|---|---|
| `tests/m2_generic_engine` | 58 passed |
| `tests/m1_usable_boq` | 30 passed (the frozen M1 package verifies; the CLI restore was caught here) |
| rebar product firewall + import boundaries | pass, 1 xfail (the recorded B-7 boundary debt) |
| route G workbook (Alsenan) recalculated in LibreOffice | 78 formulas, 0 errors; the totals equal the registers (263.435 m³, 19,740.94 kg) |
| determinism | two runs of route G give byte-identical registers and an identical SUMMARY (except the cache state) |

## Full suite

`python3 -m pytest -o addopts="" -p no:cacheprovider --junitxml=junit_fe41de1.xml` at `fe41de1`, classified by `research/environment_recovery/classify_test_run.py` (`TEST_GATE_fe41de1.json`):

| class | count | at M1 (`eab0fc1`) |
|---|---:|---:|
| EXECUTED_PASSED | 7251 | 7193 |
| CODE_FAILURE | 0 | 0 |
| MANDATORY_BLOCKED_BY_MISSING_DATA | 376 | 376 |
| SKIPPED_PREREQUISITE_UNAVAILABLE | 136 | 136 |
| SKIPPED_OTHER | 2 | 2 |
| EXPECTED_FAILURE | 100 | 100 |

- **Raw pytest:** 344 failed, 7251 passed, 138 skipped, 100 xfailed, 32 errors, in 5 min 46 s.
- **The 344 failures and 32 errors** are the same 376 tests blocked by missing data as at M1 (private benchmark and derived files that are not in git). None is a code failure.
- **Passes:** +58, exactly the M2 tests.
- **Gate: INCOMPLETE.** 376 mandatory tests are blocked by missing data, 136 are skipped for an unavailable prerequisite, and 108 locked prerequisites are missing.

## Limitations

- The synthetic truth shares the generator's drafting assumptions. See `11_GENERIC_TEST_RESULTS.md`.
- The Alsenan comparison is against our own frozen replay, not ground truth.
- No second real villa was available.
