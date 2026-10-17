# S9A TEST_RUN: structural completeness, cantilever bands and visual QA

Baseline HEAD `5f317d2` (S9 complete). Date 2026-10-10. Commits of the round:

| Commit | What it holds |
|---|---|
| `e97fa4b` | **The freeze.** The engine `engine/source/structural_completeness.py`, the builder and its report / figure layer, outputs 00 - 17, the visual QA package (`visual/`: 20 SVG figures, the HTML page, the figure index) and `18_S9A_CORRECTION_MANIFEST.json` (`DATED_CORRECTION_LAYER`, `references_read: []`). Also the synthetic and package tests and the registry entries |
| `e9f001f` | The post-freeze comparison (`post_freeze/`: old Urban V3b beams, ground beams and columns; the PRE-S8 census bands) and its tests |
| this commit | This record and the gate report `TEST_GATE_e9f001f.json` |

S9A is a dated correction layer over S9. S9 and the 29 stage freezes it covers verify unchanged before and after.

**Released: unchanged at 158.070 m3 concrete and 18,845.961 kg reinforcement.** The S9A delta is 0.000 m3 and
0.000 kg. S9A changes owners and lanes only, each with a reason (`10`). The production BOQ is not touched, and the
project gate stays INCOMPLETE.

Passing tests prove arithmetic and the reading of the registers and drawings. They do not prove engineering approval.

## What the tests pin

- **Correction layer and firewall.**
  - The S9A manifest verifies, and so do S9's manifest (recorded SHA) and the 30 frozen baselines.
  - No input touches V3b, R5, R9_1, the PRE-S8 data registers or `post_freeze`.
  - The PDF is not a frozen output.
  - The registry declares the engine, the builder, the figure layer and the comparison.
- **A. S9 re-verified.**
  - 21 of 21 family and total recomputes agree to below one millionth.
  - The README table's +0.001 kg is rounding only.
  - Footing steel is re-summed in the test straight from S4's BBS.
  - 560 inventory records, one lane each.
  - 110 concrete deltas, each equal to its released row.
  - S9-C01: 288 parts, 1,217.128 kg, all unreleased.
  - The conditional point never sits on a released row.
- **B. Bands.**
  - The test re-detects the dense hatches from ST7757.dxf itself: 8 handles at 100 mm spacing, 4.947346 m2, plus 6
    sunken hatches at 250 mm. Each area matches the register.
  - Every band's plotted spacing is within 6 % of the legend's cantilever-portion symbol and outside the
    bearing-wall window.
  - No overlap with a panel or a column. Thickness UNKNOWN. 0 m3 / 0 kg.
  - One S9 row per band. That row is an unreleased beam row.
- **Unique ownership.**
  - 8 band deltas and 7 ownership transfers, all 0 m3 / 0 kg. Each transfer starts from the S9 lane of that row.
  - Nothing moves into a released lane.
  - The S9A inventory view has 561 records with no duplicate (560 - 7 superseded + 8 band rows).
- **C. Beams, slabs, columns.**
  - Every beam volume is recomputed from B, H, L and t.
  - The strip identity holds, and the 103-beam totals equal the register sums.
  - BO-01 (243 of 243 panel edges on a drawn face), BO-02 (0 m2) and BO-04 (10 corner ends) hold.
  - Gross minus deductions equals net on every S9 row, and released equals net.
- **D. Ground beams and columns.**
  - Every length class is recomputed from the c/c and clear lengths with the exclusive bounds 2.5 / 5.0 m, and so is
    the "class changes with the basis" flag.
  - Missing-information spans carry no m3.
  - Kinds: 18 interpretation, 30 missing, 6 released. Columns: 19 interpretation, 9 conflict.
  - The 4 lift columns are drawn 200 / 250 against a scheduled 300.
  - Schedule m3 = section x the printed floor-to-floor.
- **Conservation and lanes.**
  - Every released family equals S9's, and the totals add up.
  - Conditional ranges never carry a released value. C01 - C17 pass.
- **Missing is never zero.** A beam with a missing dimension has an empty volume, not 0. RFI-A09's unlock and
  RFI-A03's steel are empty, not 0.
- **RFIs.**
  - 10 RFIs, each typed INTERPRETATION or MISSING_SOURCE_INFORMATION.
  - The ranking descends by the upper m3.
  - RFI-A01 ranks first for concrete and RFI-A02 first for steel.
- **E. Visual consistency.**
  - Every band polygon in every SVG maps back through its figure's `data-view` transform to the register polygon,
    within the 0.01 px drawing precision. That covers 8 per detail sheet, 8 on the overview and 8 across the floor
    maps.
  - Every footing rectangle maps back to S1's outline.
  - Every beam marker maps back to S1's tag position.
  - Each figure carries exactly the labels the index lists, and the HTML holds every figure and section.
- **Hygiene and reproducibility.**
  - No owner name, no Arabic and no benchmark figure in any output, SVG or HTML.
  - A rebuild is byte-identical, for the package and for the post-freeze comparison.

## Targeted

```
python3 -m pytest -o addopts="" -p no:cacheprovider tests/structural_s9a tests/structural_s9 tests/structural_comparison_engine tests/stairs_s8_7c tests/stairs_s8_7b tests/stairs_s8_7a tests/stairs_s8_7 tests/lift_s8_8 tests/lintels_s8_6a tests/lintels_s8_6 tests/r8_0/test_r8_0_import_boundaries.py tests/r8_1/test_r8_1_boundaries.py tests/environment_recovery
```

- At `e9f001f`: **385 passed, 1 xfailed.** That is S9's 356 plus this round's 29. The xfail is the recorded B-7
  boundary debt, older than S8.
- `tests/structural_s9a`: 29 passed.

| File | Tests | Covers |
|---|---|---|
| `test_structural_completeness.py` | 5 | Synthetic only. Point in polygon and overlap with holes and concave faces. Collinear edge cover. Hatch spacing with a lost line. Nearest legend by relative distance, with ties refused. Both beam readings and the strip, with a missing dimension refused rather than zeroed. Exclusive length classes |
| `test_s9a_package.py` | 20 | Everything listed above |
| `test_s9a_post_freeze.py` | 4 | The freeze is intact and the comparison downstream. The census bands are the S9A bands and CA is bound. Beams and ground beams are classified without a reading being chosen. Hygiene, no benchmark figure, and an identical rerun |

The builder was also run twice by hand: every output and the manifest are byte-identical.

### Found while building (fixed before the freeze)

- **Ground-beam "both hold".** The first audit read S5's "both titles hold" as exterior against interior. It means
  the p.13 titles overlap ('< 2.5 m' and '< 5 m' both hold for a short span). It is now TITLE_OVERLAP, separate from
  the length basis and from exterior or interior.
- **Lift columns counted twice in 09.** The lift findings are now merged into the existing mismatch rows.
- **BO-01 failed on 29 edges.** Those edges lie on column outlines and on layer-1 arcs. Arcs are now tessellated and
  column outlines accepted as faces: 243 of 243.
- **Panel clipping.** Polygon clipping gave impossible areas on slit or concave S1 faces. It was replaced with
  cell-centre sampling.
- **Band spacing.** The raster measurement of 54D was polluted by thick bars. It now reads the PDF's own vector
  paths.
- **RFI-A02 links.** These had included AD1 retractions. Only the D1.1 link corrections are counted now.
- **Figures.**
  - Plan maps are now clipped to their frames.
  - Outside and courtyard faces are no longer shaded.
  - The column grid was compacted, so no figure leaves a blank print page.
  - The beam section labels no longer clip.

## Post-freeze findings (not fixed: S9A stays frozen)

- **PF-01.** The PRE-S8 census's 8 HZ-* hatch zones are S9A's 8 bands: same handle, area to 0.001 m2.
- **PF-02.** The census says the legend draws the cantilever portion and the bearing wall with the same dense
  hatch. The plotted legend boxes measure 98.78 against 86.81 mm, and every band matches the cantilever portion.
  This is resolved by measurement. The thickness (RFI-A08) is still missing.
- **PF-03.** V3b's own CA residue row uses a 1.15 m drawn band extent, which is S9A-CP-01's length. The band is
  CA's footprint.
- **PF-04.** V3b's beams use reading A's downstand on 82 beams (37.587 m3). S9A's 103 conditional beams give 42.602
  m3 downstand, 56.767 m3 under reading A and 70.932 m3 under reading B. V3b is not authority for the reading, so
  RFI-A01 stands.
- **PF-05 - PF-07.**
  - V3b reads the ground-beam titles as exclusive bands, so RFI-A05 stands.
  - Both V3b and S9A block the exterior ground-beam depth.
  - Columns differ by method and population.

## Full suite

**Full suite: NOT GREEN. Gate: INCOMPLETE.**

`python3 -m pytest -o addopts="" -q -rfEs -p no:cacheprovider --junitxml=...` was run on the clean committed tree
`e9f001f`. No file was edited during the run.

| Run | Commit | Passed | Failed | Errors | Skipped | xfailed | Time | Exit |
|---|---|---|---|---|---|---|---|---|
| 19 | `8b62213` (S9) | 7134 | 344 | 32 | 138 | 100 | 331.8 s | 1 |
| 20 | `e9f001f` (S9A) | **7163** | 344 | 32 | 138 | 100 | 335.6 s | 1 |

- **The 29 extra passes are this round's tests:** 5 synthetic, 20 package and 4 post-freeze. All 29 executed and
  passed; none is skipped.
- **Nothing else changed.** The blocked (376), prerequisite-skipped (136), skip-reason and code-failure (0) sets are
  identical to run 19's, test for test.
- **The failures and errors are missing private data.** The 344 failures and 32 errors are the unchanged
  missing-private-data set. They are not code failures, and none touches S9A.

| Class (`classify_test_run.py`) | Tests |
|---|---|
| 1. Executed and passed | **7163** |
| 2. Legitimately skipped: prerequisite unavailable | 136 |
| Skipped for another reason | 2 |
| Expected failures (xfail) | 100 |
| 3. Mandatory regression blocked by missing data | 376 |
| 4. Actual code failures | **0** |

**Complete-project regression gate: INCOMPLETE** (not GREEN).

- 376 mandatory regression tests are blocked by missing private data. 373 of them need
  `data/experiments/P7757_WALL_TREATMENT_ESTIMATE_01`.
- 136 tests are skipped for an unavailable prerequisite.
- 108 locked prerequisites are missing: 14 BENCHMARK, 87 DERIVED and 7 SOURCE.

The record is `TEST_GATE_e9f001f.json`.

## Limitations

- **Beam concrete stays conditional.** The schedule depth convention is not printed, and S9A selects no reading.
- **The bands are not measured.** No thickness, section or bar detail is printed for them.
- **Ground-beam spans have no plan positions.** The registers hold the edge lines, not the span ends, so spans are
  not placed on the plans one by one.
- **Untagged spans have no marker** on the floor maps.
- **The PDF is not frozen.** It is a rendering of the frozen HTML, is git-ignored like the other review PDFs, and is
  printed by `make_pdf_s9a.py`.
