# M3 TEST_RUN: real-drawing recovery and BOQ completeness

**Baseline and gate**
- Baseline: M2 at `fe41de1` (full suite in `research/urban_engine_m2_generalization/TEST_RUN.md`).
- Full suite at `bfa208e` on 2026-10-11.
- M3 releases nothing. A generic run never produces VERIFIED.
- The frozen stages, the frozen M1 files and the pinned M2 evidence are unchanged.
- The project gate stays **INCOMPLETE**.
- Passing tests prove bookkeeping, geometry, parsing and arithmetic, not engineering approval.

## What the M3 tests pin (`tests/m3_recovery`, 70 tests)

| File | Tests | What it pins |
|---|---:|---|
| `test_m3_footings.py` | 3 | Every footing label quantified once (polygon, layer template, label beside outline, label-only, type mark without a number, two-label conflict); quantities by hand; bindings and risk records |
| `test_m3_columns.py` | 6 | Twin outlines; a column-plan size is no false conflict; storey presence from the roof plan; necks over their own footing; necks without printed levels stay unresolved; a column mark in a beam table is a beam |
| `test_m3_ground_beams.py` | 6 | Dotted marks and duplicate-row widths; straps between two footings only; source-supported ground-beam widths; the exterior detail on perimeter bands; typical bars from the detail evidence; without evidence the bars stay MISSING_DATA |
| `test_m3_detail_evidence.py` | 26 | Bar notation (parametrised parses and rejects); the 3 / 5 glyph vote; captions and role assembly; validation and redaction (the generic rule, plus the project's patterns supplied by the caller); native text needs no OCR; a raster page without OCR goes to manual; raster OCR needs unanimous reads; **the ST7757 p.13 real regression** (all four ground-beam details, the committed evidence reproduced record for record) |
| `test_m3_slabs_beams.py` | 9 | Stair zone not slab; a free column on a suspended slab is counted and flagged; the 10 mm intervening stub; the unambiguous part of a shared face; inheritance across a column-filled gap; a named beam layer joins on one mark; the single-face edge beam; ground-slab cells closed by a column outline; open-boundary panel = face minus bands |
| `test_m3_completeness_families.py` | 4 | Blinding under every footing; no printed thickness → unresolved; every concrete component has a rebar state and missing steel is counted; family coverage states |
| `test_m3_heldout_generator.py` | 2 | The M3 defect mode changes the drawing, never the truth, and leaves the M2 noise variant's entities unchanged; the M3 engine recovers footings exactly and beams within 2 % from the defective drawing |
| `test_m3_reports.py` | 14 | Deliverables present; hygiene, path and benchmark firewall over every package text file; no drawing in the package; the 89 components each with a state or a named match failure; positions-only benchmarks; reconciliation classes and tags; summary deltas add up; missing steel counted, never 0 kg; no VERIFIED; coverage names the missing input; held-out M3 no worse than M2; RFIs and profile provenance; evidence never promoted; **live reproduction** of files 06, 07, 08 and 11 byte for byte, and of the M3 family totals, from the private drawing |

## Targeted checks

| Check | Result |
|---|---|
| `tests/m3_recovery` | 70 passed |
| `tests/m2_generic_engine` | passed (states assertion updated to the M3 coverage states in WP8) |
| `tests/m1_usable_boq` | passed (the frozen M1 package verifies) |
| `tests/structural_comparison_engine` + `tests/r8_0` (rebar product firewall, import boundaries) | 333 passed, 87 xfailed (as before) |
| `tests/r8_1` boundaries | 16 passed after the fix below |
| ST7757 evidence re-extraction with the project redaction patterns | records, details and notes identical to the committed file |
| Route-G CLI and `build_m3_reports.py` rerun | every committed output identical except machine timings |

## Full suite

**Command:** `python3 -m pytest -o addopts="" -p no:cacheprovider --junitxml=junit_bfa208e.xml` at `bfa208e`.

**Classification:** by `research/environment_recovery/classify_test_run.py`; reduced summary in `TEST_GATE_bfa208e.json`.

| Class | `bfa208e` (M3) | `fe41de1` (M2) |
|---|---:|---:|
| EXECUTED_PASSED | 7321 | 7251 |
| CODE_FAILURE | **0** | 0 |
| MANDATORY_BLOCKED_BY_MISSING_DATA | 376 | 376 |
| SKIPPED_PREREQUISITE_UNAVAILABLE | 136 | 136 |
| SKIPPED_OTHER | 2 | 2 |
| EXPECTED_FAILURE | 100 | 100 |

- **Raw pytest:** 344 failed, 7321 passed, 138 skipped, 100 xfailed, 32 errors, in 5 min 59 s.
- **The 344 failures and 32 errors** are the same 376 tests blocked by missing data as at M1 and M2:
  - 373 are under `data/experiments/P7757_WALL_TREATMENT_ESTIMATE_01`;
  - the other 3 are a generated prerequisite and two private paths.
  - None of them is a code failure.
- **Passes:** +70, exactly the M3 tests.
- **Gate: INCOMPLETE.** 376 mandatory tests are blocked by missing data, 136 are skipped for an unavailable prerequisite, and 108 locked prerequisites are missing (benchmark 14, derived 87, source 7).

## A code failure found and fixed in this round

**What failed.** The first full suite, at `0aba317`, classified **1 CODE_FAILURE**:
- the test was `tests/r8_1/test_r8_1_boundaries.py::test_project_names_appear_only_as_field_audit_evidence_never_in_logic`;
- the gate read FAILED;
- the cause was the WP4 redaction rule in `engine/source/detail_evidence.py`, which carried the project's title-block tokens. `engine/source` must stay project-agnostic.

**Fix (`bfa208e`)**
- The engine keeps the generic rule (file paths, Arabic-script source text).
- The project's owner and title-block words are passed by the caller (`--redact`) and recorded in the evidence file.
- The p.13 evidence was re-extracted with them and is identical record for record.

**Record.** Regression record R33 in `16_REGRESSION_RECORD.md`. The targeted M3 and firewall suites had passed before that full run; only the full suite caught it.

## Limitations

- The synthetic truth shares the generator's drafting assumptions (`13_HELDOUT_EVALUATION.md`).
- On ST7757 the comparisons are against the M2 run and our own frozen replay, not ground truth.
- No second real villa was available.
