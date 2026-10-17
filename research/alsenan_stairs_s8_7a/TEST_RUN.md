# S8.7A TEST_RUN: stair riser, finishing and structural-geometry correction audit

Baseline HEAD `15730e0`. Date 2026-10-10. Commits of the round:

| Commit | What it holds |
|---|---|
| `e1a048b` | **The freeze**: the engine `engine/source/stair_riser_schedule.py`, the builder, outputs 00-14 + `15_S8_7A_CORRECTION_MANIFEST.json` (`DATED_CORRECTION_LAYER`, `corrects` S8.7, `references_read: []`), the synthetic and package tests, the registry entries |
| `8a30192` | The post-freeze comparison (`post_freeze/`) and its tests (COMPARISON_MODULES) |
| this commit | This record and the gate report `TEST_GATE_8a30192.json` |

S8.7A is a dated correction layer over S8.7. S8.7's manifest and outputs are unchanged and verified, and so are all
26 freezes from S4 to S8.8. **S8.7A releases nothing.** It reproduces S8.7's release exactly: 0.516582788 m3 and
59.020862261 kg.

## Findings that the tests pin

- **The riser disagreement is in the drawings, not the counting.** A line pair (nosing + hidden riser face, 50 mm
  apart) is one riser. The three landing-edge lines are risers. Repeated views (ground-beam plan, 2F plan) are grouped
  and not added.

  | Run (rise) | Source | Risers |
  |---|---|---|
  | GF -> 1F (4.50 m) | structural GF roof sheet | 12 + 4 + 12 = 28 |
  | GF -> 1F (4.50 m) | architectural GF plan | 10 + 4 + 11 = 25 |
  | 1F -> 2F (4.20 m) | architectural 1F plan | 12 + 4 + 11 = 27 |
  | 1F -> 2F (4.20 m) | structural 1F roof sheet and the 2F view | 12 + 1 + 11 = 24 (radial winder lines not drawn) |
  | light-well stair GF -> 1F | both primary views | 12 curved + 11 straight + 5 = 28 |

- **Owner scenarios.** Scenario A (28 / 27) is a complete drawn arrangement for each storey: GF -> 1F from the
  structural sheet, 1F -> 2F from the architectural plan. Scenario B (29 / 26) is drawn nowhere. Neither is selected.
- **Owner preference.** Inside the 150 - 160 mm range lie 29 or 30 risers for GF -> 1F (28 gives 160.714 mm) and 27
  or 28 for 1F -> 2F.
- **Physical checks:**
  - the structural 12th riser of the GF -> 1F upper flight lies inside head beam B20;
  - a 12th riser in the 1F -> 2F upper flight, as section A-A draws, would lie inside B23.
- **First / last concrete risers.** With uniform finished risers they are h + f_b - s and h - f_t + s. A 200 / 100 pair
  on 28 risers with 30 mm marble would need 69.29 / 90.71 mm floor build-ups, which no drawing gives.
- **Waist.** Not established. The 'T 16' tags are zone tags, so 160 mm is a sensitivity only.
- **Bars.** Only 8Ø16/m is explicit on the project plans. Every other p.16 family, and the anchorage and laps, are
  typical-only and blocked.

## Targeted

```
python3 -m pytest -o addopts="" -p no:cacheprovider tests/stairs_s8_7a tests/stairs_s8_7 tests/lift_s8_8 tests/structural_comparison_engine tests/lintels_s8_6a tests/lintels_s8_6 tests/r8_0/test_r8_0_import_boundaries.py tests/r8_1/test_r8_1_boundaries.py tests/environment_recovery
```

Results:

- At `e1a048b`: 268 passed, 1 xfailed. The xfail is the recorded B-7 boundary debt, which is older than S8.
- At `8a30192`: 272 passed, 1 xfailed (the four post-freeze tests added).
- `tests/stairs_s8_7a`: 29 passed.

| File | Tests | Covers |
|---|---|---|
| `test_stair_riser_schedule.py` | 11 | Synthetic only; see below |
| `test_s8_7a_package.py` | 14 | See below |
| `test_s8_7a_post_freeze.py` | 4 | Both freezes intact and the comparison downstream; V3b's method reproduced exactly and its riser counts classified; the S7 interface agrees and nothing is released; identical rerun |

`test_stair_riser_schedule.py` covers:

- nosing / riser-face pairs counted once;
- duplicate lines and irregular goings reported, not corrected;
- uniform risers and the counts in a range;
- schedule levels and the landing;
- the first / last closed form against the schedule over 200 random stairs, with the concrete risers summing to
  SSL_top - SSL_bottom;
- equal build-ups giving uniform concrete risers;
- a different landing finish moving only the two risers either side;
- the build-ups a stated 200 / 100 pair would need;
- bad segments refused;
- the plane-equivalent volume equal to a straight flight between plumb cuts;
- the bar rate.

`test_s8_7a_package.py` covers:

- **Freezes:** a dated correction layer over an unchanged S8.7, and every earlier freeze still verifying.
- **Inputs:** registry entries, and no benchmark or post-freeze file among the inputs.
- **Counts:** the riser counts per view, and the owner scenarios against the preferred range.
- **Schedules:** they close at both FFLs with uniform risers.
- **By hand:** the first / last risers, the scenario concrete (with nothing released) and the bars (with the typical
  families blocked).
- **S8.7:** its release reproduced, and corrections CR-01..06 recorded.
- **Registers:** head beams B20 / B23, conflicts SC-01..12, questions Q-ST7A-01..11, the seven owner images, and
  conservation C01-C10.
- **Hygiene.**

With the private drawings it also covers:

- a byte-identical rebuild;
- a recount with ezdxf directly, without the S1 reader or the builder, of the architectural tread lines per plan:
  pairs within 60 mm, radial lines and the closing riser.

The builder was run twice with byte-identical output (16 files).

### Found while building

- **Light-well detection.** Radial detection first counted the first straight line (at 273°). Axis-parallel lines are
  now excluded. A 1.5° tolerance then rejected the structural riser-face lines, which are about 1.8° off the radial,
  so it is 4.0°.
- **Last riser before a landing.** It now rises onto the landing finish rather than a tread.
- **Head-beam check.** It first used the pair mean. It now uses the riser-face line: 16411.856, a 99.956 mm gap to
  B20.
- **Scenario totals.** They first included the S8.7 plates. Released and not-released totals are now separate.
- **Conservation check C02.** It was trivially true. It now names the expected single-line sets exactly.

## Full suite

**Full suite: NOT GREEN. Gate: INCOMPLETE.**

`python3 -m pytest -o addopts="" -q -rfEs -p no:cacheprovider --junitxml=...` was run on the clean committed tree
`8a30192`. No file was edited during the run.

| Run | Commit | Passed | Failed | Errors | Skipped | xfailed | Time | Exit |
|---|---|---|---|---|---|---|---|---|
| 15 | `0bad737` (S8.8) | 7021 | 344 | 32 | 138 | 100 | 297.8 s | 1 |
| 16 | `8a30192` (S8.7A) | **7050** | 344 | 32 | 138 | 100 | 302.6 s | 1 |

- The 29 extra passes are this round's tests: 11 synthetic, 14 package and 4 post-freeze. All of them executed and
  passed; none is skipped.
- The blocked (376), prerequisite-skipped (136), skip-reason (24) and code-failure (0) sets are identical to run 15's,
  test for test.
- The 344 failures and 32 errors are the unchanged missing-data set. They are blocked by private inputs absent from
  this container, and none touches S8.7A.

| Class (`classify_test_run.py`) | Tests |
|---|---|
| 1. Executed and passed | **7050** |
| 2. Legitimately skipped: prerequisite unavailable | 136 |
| Skipped for another reason | 2 |
| Expected failures (xfail) | 100 |
| 3. Mandatory regression blocked by missing data | 376 |
| 4. Actual code failures | **0** |

**Complete-project regression gate: INCOMPLETE.**

- 376 mandatory regression tests are blocked by missing data.
- 136 tests are skipped for an unavailable prerequisite.
- 108 locked prerequisites are missing: 14 BENCHMARK, 87 DERIVED and 7 SOURCE.

## Limitations

- The sanitary PDF and the seven owner images are supporting visual evidence only. They are not registered inputs,
  and the renders stay outside git.
- Section A-A is a visual record, read at 600 dpi.
- Winder and curved-flight volumes are plane-equivalent approximations, labelled as such. Every scenario quantity is
  a sensitivity at a 160 mm waist and is never released.
- Floor and stair finish build-ups are not printed. The first / last risers are evaluated on a grid, not chosen.
