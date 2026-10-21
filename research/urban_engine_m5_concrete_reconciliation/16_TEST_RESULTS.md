# 16 Test results (M5)

## M5 tests (`tests/m5_reconciliation/`)

| File | Tests | What they prove |
|---|---:|---|
| `test_m5_units.py` | 5 | Difference classes (zero against zero is never "matched"); how an item enters the reference (measured / conditional / unmeasurable / excluded, and a decomposed cell priced on its slab area, not the overstated exposure); family totals never add an excluded item; crosswalk keys and mark normalisation; strip centreline by hand (L-shape, 14.8 m) |
| `test_m5_engine_fix.py` | 5 | V4 = V3 + `PLANTED_COLUMN_LABELS` and the CLI default stays V3; a "P.C WxD" label is section × the storey above (hand-derived), a plain "C" label is ignored, bars stay MISSING_DATA; no storey above is UNRESOLVED, never zero; a label on a counted column is not counted twice; live ST7757: V4 adds exactly the three planted columns (1.428 m3) and leaves every V3 item unchanged |
| `test_m5_package.py` | 16 | Deliverables; hygiene, path and benchmark firewall over every text file; external figures read from records, never constants (AST scan); M5 code declared as comparison code; no drawing, workbook, PDF or image in git; the RECONCILIATION phase declared after a freeze; RC and plain concrete never added; the bridge closes and every step is classified and priced; every record in exactly one group; element rows classified and located; nothing VERIFIED and NOT QUOTATION-READY; no ratio fills a missing quantity; independent checks pass; missing sources recorded, not recreated; RFIs ranked with quantity and cost; live reproduction of every committed text file, byte for byte, from the private drawings |

**Result:** 26 passed (38 s).

## Targeted run before the full suite

`tests/m4_correctness tests/m2_generic_engine tests/m3_recovery tests/r8_1 tests/r8_0 tests/test_benchmark_protection.py tests/structural_comparison_engine/test_rebar_product_firewall.py tests/m1_usable_boq`

- 856 passed, 87 xfailed.
- 1 failure in `tests/test_benchmark_protection.py`: it needs the private reconciliation document under `data/runs/7757`. It is the same test the full suite classifies as blocked by missing data.
- Every M1 / M2 / M3 / M4 package test still passes, including the M4 live reproduction. The M5 engine change is gated on the V4 conventions.

## Full suite

**Command:** `python3 -m pytest -o addopts="" -p no:cacheprovider --junitxml=junit_m5.xml`, on `883c488` plus the M5 working tree of this commit.

**Classification:** by `research/environment_recovery/classify_test_run.py`; reduced summary in `TEST_GATE_M5.json`.

| Class | M5 | `1213430` (M4) |
|---|---:|---:|
| EXECUTED_PASSED | 7394 | 7368 |
| CODE_FAILURE | **0** | 0 |
| MANDATORY_BLOCKED_BY_MISSING_DATA | 376 | 376 |
| SKIPPED_PREREQUISITE_UNAVAILABLE | 136 | 136 |
| SKIPPED_OTHER | 2 | 2 |
| EXPECTED_FAILURE | 100 | 100 |

- **Raw pytest:** 344 failed, 7394 passed, 138 skipped, 100 xfailed, 32 errors, in 7 min 28 s.
- **The 344 failures and 32 errors are not code failures.** They are the same 376 tests blocked by missing data as at M1–M4:
  - 373 under `data/experiments/P7757_WALL_TREATMENT_ESTIMATE_01`;
  - 1 that needs the private reconciliation document under `data/runs/7757`;
  - 1 generated prerequisite and 1 private path outside the repository.
- **Passes:** +26, exactly the 26 M5 tests.
- **Gate: INCOMPLETE.** 376 mandatory tests are blocked by missing data, 136 are skipped for an unavailable prerequisite, and 108 locked prerequisites are missing (benchmark 14, derived 87, source 7).

## Defects found during M5 and fixed before the commit

| Found by | Defect | Fix |
|---|---|---|
| Bridge closure check | The bridge missed closing by about 1e-5 m3: steps were rounded before summing, and the ground-slab area was rounded | Closure computed from raw values; step B07a carries the ground-slab residual |
| IV-11 (beam sections against the drawing) | Failed on B21 and CB2, where M4 uses the schedule width rather than the drawn width | The check accepts a schedule-width substitution and reports it |
| `test_element_rows_classified_and_located` | CB10 and other rows had an empty explanation | Explanations for the beam / column / footing base cases, dome tower and drums, pool base, plus a generic fallback |
| Hygiene test | A placeholder path to the missing freelancer workbook was written as an absolute local path | Written as `uploads/<session>/...` |
| Rebar product firewall test | The M5 modules and directory were not declared | Declared in the registry as comparison code |
| `test_label_section_times_the_storey_above` | The test assumed the order of the produced items (a test defect, not an engine one) | Compares sorted values |

## Double build and the change after the full suite

- **Double build.** The package was built twice with different hash seeds (`PYTHONHASHSEED` 1 and 7). All 50 committed text files were byte-identical, with the same content digest `d6eacdd3…` and 20 / 20 independent checks.
- **Change after the full suite: figures only.** In `m5_visual.py`:
  - the unresolved maps (09a–d) now carry a numbered key under each map;
  - the bar charts keep a right margin for their labels ("cond. to x", "in neither base: not drawn / unresolved");
  - each SVG's background is sized to its content.

  No engine code, quantity or register changed. The measured RC base is still 316.065 m3, with 20 / 20 checks.
- **Re-run.** `tests/m5_reconciliation` passed again (26 tests) on the rebuilt package, including the byte-for-byte live reproduction of every committed text file.
