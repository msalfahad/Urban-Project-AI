# S9 TEST_RUN: whole-building structural BOQ reconciliation

Baseline HEAD `b85d2af`. Date 2026-10-10. Commits of the round:

| Commit | What it holds |
|---|---|
| `37579dc` | **The blind freeze.** The engine `engine/source/structural_reconciliation.py`, the builder, outputs 00 - 15, and `16_S9_FREEZE_MANIFEST.json` (`FROZEN_BEFORE_COMPARISON`, `references_read: []`). Also the synthetic and package tests and the registry entries |
| `8b62213` | The post-freeze comparison (`post_freeze/`: old Urban V3b BOQ, PRE-S8 census, R5) and its tests, plus the workbook view `build_workbook.py` |
| this commit | This record and the gate report `TEST_GATE_8b62213.json` |

S9 reconciles every structural family from the frozen S1 - S8 stages. All 29 freezes from S4 to S8.8, and the S1 / S2 /
S3 / S3.1 indexes, verify unchanged before and after.

**Release: 158.070 m3 concrete, 18,845.961 kg reinforcement.**

- **Concrete.** 12.204 m3 is carried from S8.1 / S8.3 / S8.4 / S8.6A / S8.7, and 145.866 m3 is released here as 110
  auditable S9 deltas.
- **Reinforcement.** Each family is taken at its authoritative frozen version. S9-C01 moves 1,217.128 kg of S3.1
  column tie paths and hooks to conditional.
- **This is a partial structural BOQ, not a complete building estimate.** The production BOQ is not updated.

Passing tests prove the arithmetic and the reading of the frozen registers. They do not prove engineering approval.

## What the tests pin

- **Freeze and firewall.**
  - The S9 manifest and the 29 stage manifests verify, and so do the four stage indexes.
  - No manifest input touches V3b, R5, R9_1, the PRE-S8 data registers or `post_freeze`.
  - The workbook is not a frozen output.
  - The registry declares the engine, the builder and the comparison.
- **Concrete, recomputed from the raw registers** with code independent of the builder:
  - **Footings** use the S1 schedule, their own bounding-box overlap and S2 VERIFIED. 25 are released.
    - The F9 / FN deduction is 0.14 m2 x 0.30 m.
    - FF (4.60 x 4.50 x 0.55 = 11.385 m3) is counted once, in the footings. The lift family keeps a reference.
    - F / F10 is a conflict.
  - **Columns** use the schedule section x the printed floor-to-floor (4.5 / 4.2 / 4.2), for S2 VERIFIED occurrences
    whose drawn section matches.
    - No foundation neck is released.
    - The four lift columns at the pit are a source conflict.
  - **Ground beams** are the six spans whose width and depth are both explicit. The length-class sections come from
    D1.1's frozen source search.
  - **Slabs** use their own shoelace and holes, x the PRE-S7 thickness: 47 panels.
    - The 49 S2-VERIFIED panels are these 47 plus the two S8.4 tank panels.
    - No tank panel enters the slab release.
  - **Frozen-stage concrete** (S8.1, S8.3, S8.4, S8.6A, S8.7) is carried unchanged. The delta register and the frozen
    part add up to the total.
- **Reinforcement and precedence.**
  - Each family is re-summed and checked against its stage summaries:
    - ground beams: S5 + S5.1 + AD1 + D1.1;
    - beams: S6 + S6.1 + D1.1;
    - S4, S7, S8.6A.
  - S8.6A is never added to S8.6.
  - **S9-C01** is re-derived from S3.1's release register: 288 parts, 1,217.128 kg, all conditional.
    - The released column laps, anchorages and starters are only S3.1's printed-rule parts (P8-N09, P13, P15).
  - There is one authoritative version per family. Beam concrete is recorded as "not measured as zero".
- **Conservation.**
  - Ids are unique, each with one owner.
  - GROSS - deductions = NET.
  - Released rows equal NET, and nothing outside a released lane carries a value. No authoritative kg is negative.
  - C01 - C22 and O-01 - O-16 all pass.
  - The A1 / A2 released BOQ sums to the summary, and every released bar has a diameter.
- **Missing and blocked.**
  - Every category is present, including possible multi-stage counts and the post-freeze old-BOQ check.
  - No released concrete row is without its steel.
  - The beam conditional ranges follow B x H x L .. B x (H + 0.16) x L, or carry an explicit upper bound.
- **Stairs, lift, pool.**
  - Only S8.7's three plates are released (0.516582788 m3 / 59.020862261 kg).
  - Nothing is released for the lift or the pool. The four pit walls are indicative only.
  - The README states the 110 - 120 mm riser rule and the owner-scenario status.
- **RFIs.** 207 rows with unique ids. The S8.7C and S8.8 RFIs are all carried, plus nine consolidated S9 RFIs.
- **Hygiene and reproducibility.**
  - No owner name, no Arabic and no benchmark figure appears in the outputs.
  - A rebuild is byte-identical, for the package and the post-freeze comparison.

## Targeted

```
python3 -m pytest -o addopts="" -p no:cacheprovider tests/structural_s9 tests/structural_comparison_engine tests/stairs_s8_7c tests/stairs_s8_7b tests/stairs_s8_7a tests/stairs_s8_7 tests/lift_s8_8 tests/lintels_s8_6a tests/lintels_s8_6 tests/r8_0/test_r8_0_import_boundaries.py tests/r8_1/test_r8_1_boundaries.py tests/environment_recovery
```

- At `37579dc`: 350 passed, 1 xfailed. That is S8.7C's 325 plus this round's 20 at the freeze plus the registry
  checks. The xfail is the recorded B-7 boundary debt, older than S8.
- At `8b62213`: 356 passed, 1 xfailed (the 6 post-freeze tests added).
- `tests/structural_s9`: 26 passed.

| File | Tests | Covers |
|---|---|---|
| `test_structural_reconciliation.py` | 4 | Synthetic only: polygon area with holes, overlap and prism (a missing dimension is never zero), version chains (a delta never subtracts, a correction never adds, superseding replaces), single owner and lane-safe totals |
| `test_s9_package.py` | 16 | Everything listed above |
| `test_s9_post_freeze.py` | 6 | The freeze is intact and the comparison downstream; every V3b concrete line and rebar population is compared and classified; the footing difference is exactly the overlap prism; the PRE-S8 crosswalk accounts for every census element, and the 8 hatch bands are absent from S9; nothing is released; an identical rerun |

The builder was also run twice by hand: the output is byte-identical (17 files).

### Found while building (fixed before the freeze)

- **A planted-column extra had no diameter.** One S6.1 delta row (B26, 12.010 kg) carried its diameter only in its
  facets. It is now read from there, so the A2 released BOQ has a diameter on every row.
- **FN footing links.** Three FN footings link to several S4 occurrences ("FOCC-1100+1101+..."). The first build read
  only the first, so it reported them as "concrete without steel". A shared link resolver fixes this.
- **Beam concrete read as zero.** The precedence register showed beam concrete as a released 0. It now says
  "nothing released, not measured as zero", with the lane counts.
- **Missing-register category.** "Possible multi-stage count" existed only in the overlap audit. It is now in the
  missing register too.
- **RFI counts.** The S9 RFI counts (column mismatches, the S9-C01 kg, sunken drops) were literals. They are now
  derived from the data.

## Post-freeze findings (not fixed: S9 stays frozen)

- **F-01, missed object.** The PRE-S8 census lists 8 cantilever / bearing-wall hatch bands (HZ-*, 4.947 m2 in plan).
  - They have no S1 panel, no owner and no thickness, and S9 has no row for them.
  - No released figure changes, but the inventory and the missing register are incomplete by these rows.
  - A dated correction layer needs approval.
- **F-02.** The footing difference with V3b (-0.042 m3) is exactly the F9 / FN overlap prism.
- **F-03.** V3b's footing steel (1,132.674 kg) cannot be decomposed from its registers. S4's 3,629.6 kg stands.
- **F-04.** V3b and S9 split slabs, beams and columns on different conventions, so the totals are compared by group
  only. The slab area reconciliation leaves a residual that V3b's single plate figure cannot explain.

## Full suite

**Full suite: NOT GREEN. Gate: INCOMPLETE.**

`python3 -m pytest -o addopts="" -q -rfEs -p no:cacheprovider --junitxml=...` was run on the clean committed tree
`8b62213`. No file was edited during the run.

| Run | Commit | Passed | Failed | Errors | Skipped | xfailed | Time | Exit |
|---|---|---|---|---|---|---|---|---|
| 18 | `0c7e1b5` (S8.7C) | 7108 | 344 | 32 | 138 | 100 | 340.9 s | 1 |
| 19 | `8b62213` (S9) | **7134** | 344 | 32 | 138 | 100 | 331.8 s | 1 |

- **The 26 extra passes are this round's tests:** 4 synthetic, 16 package and 6 post-freeze. All 26 executed and
  passed; none is skipped.
- **Nothing else changed.** The blocked (376), prerequisite-skipped (136), skip-reason and code-failure (0) sets are
  identical to run 18's, test for test.
- **The failures and errors are missing private data.** The 344 failures and 32 errors are the unchanged
  missing-private-data set. They are not code failures, and none touches S9.

| Class (`classify_test_run.py`) | Tests |
|---|---|
| 1. Executed and passed | **7134** |
| 2. Legitimately skipped: prerequisite unavailable | 136 |
| Skipped for another reason | 2 |
| Expected failures (xfail) | 100 |
| 3. Mandatory regression blocked by missing data | 376 |
| 4. Actual code failures | **0** |

**Complete-project regression gate: INCOMPLETE** (not GREEN).

- 376 mandatory regression tests are blocked by missing private data.
- 136 tests are skipped for an unavailable prerequisite.
- 108 locked prerequisites are missing: 14 BENCHMARK, 87 DERIVED and 7 SOURCE.

The record is `TEST_GATE_8b62213.json`.

## Limitations

- **Beams.** Beam concrete is conditional: the schedule depth convention is not printed, and S2 holds beam lengths
  as a lower bound.
- **Column intervals.** Columns are measured on the printed floor-to-floor, because structural slab levels and
  build-ups are not printed (a project-basis value). Foundation necks need the founding level.
- **Missing quantities.**
  - Pool, parapets, blinding, the boundary wall, dome rings, lift pit walls and the tie beam are not quantified.
  - The same goes for the sunken drops, the ground-slab remainder and the 8 hatch bands (F-01).
- **No stair flight is released.** The owner scenarios are not approved, and the waist and build-ups are unknown.
- **The workbook is a view.** It is not frozen and not committed.
