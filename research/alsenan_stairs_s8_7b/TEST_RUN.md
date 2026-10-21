# S8.7B TEST_RUN: staircase owner scenario and engineering reconciliation

Baseline HEAD `303df68`. Date 2026-10-10. Commits of the round:

| Commit | What it holds |
|---|---|
| `36b36b9` | **The blind freeze**: the engine `engine/source/stair_scenario_checks.py`, the builder, outputs 00-15 + `16_S8_7B_FREEZE_MANIFEST.json` (`FROZEN_BEFORE_COMPARISON`, `references_read: []`, release delta 0 / 0), the synthetic and package tests, the registry entries |
| `f1e04c1` | The post-freeze comparison (`post_freeze/`) and its tests (COMPARISON_MODULES) |
| this commit | This record and the gate report `TEST_GATE_f1e04c1.json` |

S8.7B is a research scenario layer over S8.7 and S8.7A. Both, and all 27 freezes from S4 to S8.8, verify unchanged.
**Release delta: 0 m3 concrete, 0 kg reinforcement.** S8.7's frozen 0.516582788 m3 / 59.020862261 kg is untouched.
Passing tests prove the arithmetic and the reading of the drawings. They do not prove engineering approval.

## What the tests pin

- **Owner scenario.** GF -> 1F 28 risers, 1F -> 2F 27 risers, waist UNKNOWN and a 30 mm stair finish (bedding not
  stated) are all provisional. The round stair is evaluated as drawn and is not owner-approved.
- **GF -> 1F at 28 risers.** 160.714285714 mm, 0.714 mm over the preferred maximum (a tolerance decision). The
  arrangement conflicts with the drawings:
  - The printed +3.50 half-landing cannot be reached with equal risers: it falls between +3.411 and +3.571.
  - The drawn allocation lands at +3.571.
  - The last riser on the structural sheet is 200 mm inside B20.
- **Section A-A (measured).** GF -> 1F draws 15 + 12 = 27 risers of 166.667 mm, reaching +3.50 exactly. 1F -> 2F
  draws 13 + 12 = 25 risers of 168 mm, with the landing scaling to about +7.69.
- **1F -> 2F at 27 risers.** 155.556 mm. The arrangement clears B23 by 100 mm, but it needs the architectural
  plan's winders, which the structural sheet draws as a flat quarter. The landing level is not printed.
- **Setting out.** Cumulative levels rounded to 1 mm stay within 0.5 mm. The rounded risers come out as 8 x 160 +
  20 x 161 and 12 x 155 + 15 x 156, and they never accumulate an error.
- **Finishes.** First concrete riser = h + f_b - s and last = h - f_t + s. The datum model is written separately
  from the closed form and agrees with it. A 200 / 100 pair needs floor build-ups no drawing gives.
- **Concrete.** The waist sensitivity at 150 / 160 / 175 / 200 mm is never released:
  - flights use an exact section integral equal to the plumb-cut outline;
  - beam overlap zones and column cut-outs are kept apart from NET;
  - the S8.7 plates are excluded from every new total.
- **Reinforcement.** The nine 8Ø16/m plan callouts are read again and equal S8.7's bindings. Every typical family
  and all anchorage and laps are blocked. The S7 top extensions (71.895327413 kg) and S6 beams are preserved.

## Targeted

```
python3 -m pytest -o addopts="" -p no:cacheprovider tests/stairs_s8_7b tests/stairs_s8_7a tests/stairs_s8_7 tests/lift_s8_8 tests/structural_comparison_engine tests/lintels_s8_6a tests/lintels_s8_6 tests/r8_0/test_r8_0_import_boundaries.py tests/r8_1/test_r8_1_boundaries.py tests/environment_recovery
```

Results:

- At `36b36b9`: 299 passed, 1 xfailed. The xfail is the recorded B-7 boundary debt, older than S8.
- At `f1e04c1`: 303 passed, 1 xfailed (the four post-freeze tests added).
- `tests/stairs_s8_7b`: 31 passed.

| File | Tests | Covers |
|---|---|---|
| `test_stair_scenario_checks.py` | 11 | Synthetic only; see below |
| `test_s8_7b_package.py` | 16 | See below |
| `test_s8_7b_post_freeze.py` | 4 | Freeze intact and comparison downstream; V3b reproduced and classified; nothing released; identical rerun |

`test_stair_scenario_checks.py` covers:

- landing reach;
- the counts that reach a 5 / 9 landing;
- unequal split risers;
- rounding of levels versus repeated risers;
- unknown build-up layers;
- the datum model against the riser schedule and the closed form over 300 random stairs;
- signs of the first and last risers;
- the section integral against the plumb-cut outline, a brute-force integral and interval additivity;
- solid steps and winder bounds.

`test_s8_7b_package.py` covers:

- **Freezes:** the freeze and the 27 earlier freezes, and the PRE-S8 / V3b / R5 firewall on inputs and code.
- **Owner register.**
- **By hand:** the riser table, the setting-out schedule (exact levels and 1 mm levels), the landing reconciliation,
  head-beam clearances with the overlap zone checked by a brute-force integral, first / last risers, flight and
  step concrete by closed form, and winder treads and bounds.
- **Section A-A:** counts, levels and the 1:100 scale.
- **Registers:** reinforcement and ownership; conflicts, RFIs and conservation.
- **Hygiene.**

With the private drawings it also covers:

- a byte-identical rebuild;
- a raw-ezdxf recount of the structural sheets: west and east columns, radial lines, and the B20 / B23 edges.

The builder was also run twice by hand with byte-identical output (17 files).

### Found while building

- **Section A-A render.** A full-page 600 dpi render took 216 s. A crop window is pixel-identical and takes 30 s.
- **Winder split.** Rays starting inside the quarter did not split it. Angular wedges about the fan centre now do,
  with the back sector closed.
- **BL001.** It is a beam inclined about 9° off the axis, so its bounding box over-stated overlaps. True band
  polygons are now used.
- **Callout 537.** It sits inside a block INSERT; texts are now read from inserts too.
- **Number formatter.** It stripped trailing zeros from integers (200 -> "2"). It is fixed before the freeze.
- **Steps on grade.** The entrance steps sit over ground beam BL021, and beam CA plus the stub BL041 cross the
  light-well flight. Those zones are now deducted from NET.

## Full suite

**Full suite: NOT GREEN. Gate: INCOMPLETE.**

`python3 -m pytest -o addopts="" -q -rfEs -p no:cacheprovider --junitxml=...` was run on the clean committed tree
`f1e04c1`. No file was edited during the run.

| Run | Commit | Passed | Failed | Errors | Skipped | xfailed | Time | Exit |
|---|---|---|---|---|---|---|---|---|
| 16 | `8a30192` (S8.7A) | 7050 | 344 | 32 | 138 | 100 | 302.6 s | 1 |
| 17 | `f1e04c1` (S8.7B) | **7081** | 344 | 32 | 138 | 100 | 319.1 s | 1 |

- The 31 extra passes are this round's tests: 11 synthetic, 16 package and 4 post-freeze. All of them executed and
  passed; none is skipped.
- The blocked (376), prerequisite-skipped (136), skip-reason (24) and code-failure (0) sets are identical to run 16's,
  test for test.
- The 344 failures and 32 errors are the unchanged missing-private-data set. They are not code failures, and none
  touches S8.7B.

| Class (`classify_test_run.py`) | Tests |
|---|---|
| 1. Executed and passed | **7081** |
| 2. Legitimately skipped: prerequisite unavailable | 136 |
| Skipped for another reason | 2 |
| Expected failures (xfail) | 100 |
| 3. Mandatory regression blocked by missing data | 376 |
| 4. Actual code failures | **0** |

**Complete-project regression gate: INCOMPLETE** (not GREEN).

- 376 mandatory regression tests are blocked by missing private data.
- 136 tests are skipped for an unavailable prerequisite.
- 108 locked prerequisites are missing: 14 BENCHMARK, 87 DERIVED and 7 SOURCE.

## Limitations

- Section A-A is measured from a render. The calibration residual is under 0.2 px, but the 1F -> 2F landing has no
  printed level, so its +7.69 is indicative only.
- p.16 and the owner images are visual records. The renders stay outside git.
- Winder and curved-flight volumes are plane-equivalent approximations; the winders also have a flat-soffit upper
  bound. The steps on grade are conditional, because the construction is not drawn.
- No floor or stair build-up is printed. The first and last risers are evaluated on an illustrative grid.
