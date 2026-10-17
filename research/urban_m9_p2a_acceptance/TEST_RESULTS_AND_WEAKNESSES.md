# Test results and known weaknesses: Phase 2A acceptance review

**Date and environment:**
- 2026-10-14.
- CPython 3.11.17, as in `research/freeze_integrity/ENVIRONMENT_LOCK.json`.

**Code under test:** `e78f6bd` (Phase 2A, as delivered), plus this review's additions:
- documents;
- the blind-test scorer and its dry run;
- one test file;
- seven findings appended to the register.

**Production code:** not changed by the review.

## 1. Independent verification (this review, not the sprint's own verifier)

| Check | Method | Result |
|---|---|---|
| V1 and V2 unchanged by Phase 2A | CLI `arch` run from a worktree at the pre-sprint commit `a1493b1` and from `e78f6bd`. Methods V1 and V2, on 3 drawings: the synthetic villa; the synthetic villa mirrored, turned and moved; the reference plan (private). Every published file compared byte for byte. | **98 / 98 files byte-identical**, workbooks included (V1: 15 + 15 + 16; V2: 17 + 17 + 18) |
| V2.1 deterministic | two V2.1 runs of the synthetic villa and the reference plan | **identical** (23 and 24 files) |
| Frozen artefacts | `tools/freeze_verify.py check` against `FREEZE_BASELINE_INDEX.jsonl` | **0 artefacts differ** |
| Attribution of the reference-plan changes | private ablation: V2.1 with the robust predicate and the mean axis switched separately | every material change comes from the **robust predicate alone**; the mean axis changes no line at 6 dp; with both switches at their frozen values, V2.1 equals V2 |
| Threshold decisions | the 23 AT_THRESHOLD records | 6 lie below their threshold by floating-point noise and are kept; only 2 (the GF 100 mm wall-face pieces) change a BOQ line; 0 UNDECIDABLE |
| Door conservation | every floor | every swing is in exactly one element; 28 door sets, 29 leaves |

## 2. Test runs

### 2.1 Full suite at `e78f6bd`

- **Where:** a private clone (`data/inputs` symlinked; no real-plan drawing variable).
- **Time:** 12 min 01 s.

| Collected | Passed | Failed | Errors | Skipped | xfailed |
|---|---|---|---|---|---|
| 8,557 | 7,921 | 345 | 32 | 157 | 102 |

**Classification of the 377 failures and errors:**
- **373** are `FileNotFoundError` on the gitignored `data/experiments/...` datasets (the PA-08 / PA-09 studies), which are absent here.
- **1** is a missing `data/runs/...` reconciliation output.
- **1** is "run workbook_boq first" (missing data).
- **1** is a client upload from an earlier session.
  - These 376 equal the pre-sprint baseline: the sprint re-ran them at `a1493b1` with the same result.
- **1** (`tests/m5_reconciliation/test_m5_package.py::test_live_reproduction_of_every_committed_text_file`) is an artefact of the clone layout.
  - The source inventory writes paths relative to the repository root, and the clone's `data/inputs` is a symlink into another tree.
  - **The same test passes in the main repository** (re-run: 1 passed).
- **Code failures:** 0.

### 2.2 The rest

| Run | Result |
|---|---|
| Real-plan tests with `URBAN_REAL_PLAN_DXF` (`tests/m9_s4`, `m9_s5`, `m9_s6` real-plan files) | 8 passed, 10 skipped (they need the Round-5 registers, absent) |
| Affected suites after the review's additions: `tests/m9_p2a` (including the new `test_p2a_blind_scoring.py`), `tests/zz_freeze_integrity` (the findings register with F-17 to F-24 appended), `tests/m9_s2_arch`, `tests/m9_s6` | **253 passed, 2 xfailed** (F-9 strict xfail and one earlier xfail) |
| Blind-test scorer dry run (`blind_test/dry_run.py`) | **6 / 6 injected faults detected**, each in its own category |

## 3. Known weaknesses

Numbered by finding (`research/freeze_integrity/ENGINEERING_FINDINGS.jsonl`).

| Finding | Weakness | Affects released quantities? | Methods |
|---|---|---|---|
| **F-24** | With wall heights supplied, a passage is deducted at full width from every room that touches it. One reference-plan room goes negative and **the run stops** (LineError). | **Yes** (stop, or under-measured walls) | V1, V2, V2.1 |
| **F-17** | A boundary edge with two roles is split 50 / 50. A window frame drawn on the room face is half skirted. This explains BA-12; about 8.4 m of released skirting on the reference plan rests on the split. | **Yes** (skirting) | V1, V2, V2.1 |
| **F-18** | A door with an open width REVIEW (0.9 m opening against a 1.0 m frame) is released. | **Yes** (aluminium width) | V2.1 |
| **F-20** | A door into an unlabelled space with a doorless facade opening is released as internal PVC. | **Yes** (class) | V2.1 |
| **F-19** | A confirmed door with an unresolved class is withheld without a finding. | no (withheld) | V2.1 |
| **F-21** | 102 of 427 lines are not in the surface ledger, and ENGINE_LIMIT records are labelled NO_EMITTER. | no (diagnostic) | V2.1 |
| **F-22** | Lift entrances are found only from a lift word. Three probable lift openings are passages. | no door total; passage count and ledger, yes | V2.1 |
| F-9 | Column outlines are axis-aligned only. A rotated plan loses its columns. | yes, on rotated plans | all |
| F-13 | The DWG adapter reads DIMLFAC from the header only. | no (read-only cross-check) | V2.1 |
| F-15 | Docstring drift in a fixture. | no | — |
| — | Every wall finish (plaster, paint, wall tile) and every door / window area is BLOCKED by missing heights, unless a facts file is given; F-24 must be fixed before that is safe. | — | all |
| — | ARCH_OPENINGS carries no window position, so the scorer matches windows by width only. | — | all |
| — | The engine takes one plan file per run. A drawing set split across files is run file by file. | — | all |
| — | The synthetic villa is a regression fixture of the engine. Its perfect dry-run score is **not** accuracy evidence. | — | — |

## 4. What was not verified

- **Any accuracy figure.** No blind drawing and no independent benchmark were used. The private benchmark was not opened.
- **Route G** was not re-run in this review. The evidence for it is the sprint's own final verifier at `2a34281` (sprint report, section 7), which this review did not repeat. The V1 / V2 byte-identity above covers the architectural route only.
- **The Round-5 real-plan regression tests** were skipped (their registers are absent).
