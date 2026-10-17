# 12 Regression results (M7)

## M7 tests (`tests/m7_reliability/`, 42)

| File | Tests | What they prove |
|---|---:|---|
| `test_m7_geometry.py` | 11 | geometry fixtures with the expected value from the fixture itself (`08_INDEPENDENT_VALIDATION.md` §3) |
| `test_m7_legend.py` | 5 | adversarial legends: nearest caption on the row, ambiguity recorded, no caption |
| `test_m7_release.py` | 6 | release ladder, decisions bound to revision and item, OCR ledger, reconciliation states |
| `test_m7_project_run.py` | 3 | blind protocol: freeze before the reference, byte-identical rebuild, refusals |
| `test_m7_properties.py` | 9 | every metamorphic operation on cluttered villas, no SILENT row, set-aside evidence still reported |
| `test_m7_package.py` | 8 | package files, hygiene, freeze against git, held-out summary, CSV / workbook / PDF rebuilt from the records, **live** ST7757 records rebuilt byte for byte |

**Result:** 42 passed (targeted run and inside the full suite; the live ST7757 test ran, it was not skipped).

## Frozen packages inside the full run

| Suite | Passed | |
|---|---:|---|
| `tests/m1_usable_boq` | 30 | |
| `tests/m2_generic_engine` | 58 | |
| `tests/m3_recovery` | 70 | |
| `tests/m4_correctness` | 47 | **live**: the M4 registers and independent checks rebuild byte for byte on the M7 working tree |
| `tests/m5_reconciliation` | 26 | **live**: every committed M5 text file rebuilds byte for byte on the M7 working tree |
| `tests/m6_completeness` | 40 | both M6 ST7757 runs rebuild byte for byte from the M6 engines read from git |
| `tests/structural_comparison_engine/test_rebar_product_firewall.py` | 30 | no comparison module reachable from the accurate path |

Every M7 change is gated by a V5 convention; the live M4 and M5 rebuilds on the M7 working tree are the evidence
that the V3 / V4 paths they freeze are unchanged. The two ungated changes tried during M7 were caught by exactly these
tests and withdrawn (`04_GEOMETRY_AUDIT.md`).

## Full suite

**Command:** `python3 -m pytest -o addopts="" -p no:cacheprovider --junitxml=junit_m7.xml` on the package tree of
`8694286` (engine = freeze `af2822a` + the post-freeze fixes P1–P3 of `a99974d`).
**Classification:** `research/environment_recovery/classify_test_run.py`; reduced summary in `TEST_GATE_M7.json`.

| Class | M7 | M6 |
|---|---:|---:|
| EXECUTED_PASSED | 7476 | 7434 |
| CODE_FAILURE | **0** | 0 |
| MANDATORY_BLOCKED_BY_MISSING_DATA | 376 | 376 |
| SKIPPED_PREREQUISITE_UNAVAILABLE | 136 | 136 |
| SKIPPED_OTHER | 2 | 2 |
| EXPECTED_FAILURE | 100 | 100 |

- **Raw pytest:** 344 failed, 7476 passed, 138 skipped, 100 xfailed, 32 errors in 8 min 29 s.
- **The 344 failures and 32 errors are not code failures**: the same 376 tests blocked by missing data as at
  M1–M6 (373 under `data/experiments/P7757_WALL_TREATMENT_ESTIMATE_01`, 1 needing the private reconciliation
  document under `data/runs/7757`, 1 generated prerequisite, 1 private path outside the repository).
- **Passes: +42**, exactly the 42 M7 tests. No earlier test changed.
- Two deprecation warnings, both from earlier tests importing moved QA helpers (not M7).
- **Gate: INCOMPLETE** (376 blocked by missing data, 136 prerequisite skips, 108 locked prerequisites missing). Only
  EXECUTED_PASSED proves anything; a skip is not a pass.

## Defects found by M7's own checks and fixed

| Found by | Defect | Fix |
|---|---|---|
| Metamorphic harness | 13 placement / representation causes (MTEXT rotation, far-from-origin coordinates, flush faces, arc clip, furniture square as column, fixed rectangle minimum, line rings, reversed continuous beam, class limits at float precision, duplicated text, frames as lines, treads across layers, metre / millimetre) | one V5 convention per cause (`03_ENGINE_WEAKNESS_REGISTER.csv`) |
| Frozen M4 / M5 packages | two ungated changes (polygon area, slab local origin) changed a frozen label and SVGs | withdrawn; re-introduced only behind a convention |
| ST7757 after the held-out run | P1 lintel band at float precision; P2 set-aside column outlines no longer reported; P3 checker wrong for a two-label footing | fixed, reported apart; held-out completeness re-run identical (`heldout/POSTFIX_COMPLETENESS.json`) |
| Package test | the PDF and workbook were about to be committed against the repository convention | kept out of git; the test rebuilds both from the records |
