# S8.7C TEST_RUN: stair design resolution study

Baseline HEAD `0cda418`. Date 2026-10-10. Commits of the round:

| Commit | What it holds |
|---|---|
| `584384f` | **The blind freeze**: the engine `engine/source/stair_fit_checks.py`, the builder, outputs 00-15 + `13_S8_7C_FREEZE_MANIFEST.json` (`FROZEN_BEFORE_COMPARISON`, `references_read: []`, release delta 0 / 0), the synthetic and package tests, the registry entries |
| `0c7e1b5` | The post-freeze comparison (`post_freeze/`) and its tests (registered with the comparison modules) |
| this commit | This record and the gate report `TEST_GATE_0c7e1b5.json` |

S8.7C is a research and design-comparison study over S8.7, S8.7A and S8.7B. **It is not approval to change the
drawings.** Those three, and all 28 freezes from S4 to S8.7B, verify unchanged.

**Release delta: 0 m3 concrete, 0 kg reinforcement.** S8.7's frozen 0.516582788 m3 / 59.020862261 kg is untouched,
and the production BOQ is not updated.

Passing tests prove the arithmetic and the reading of the drawings. They do not prove engineering approval.

## What the tests pin

- **GF -> 1F arrangements.** Seven arrangements are checked by hand: the riser, the landing level, the foot, the last
  riser and the B20 clearance.
  - With equal risers, only 27 and 36 of the counts 20 - 40 reach +3.50.
  - **A-28** (structural sheet) conflicts three ways: the landing is +3.571 (+71.4 mm), the last riser is 200 mm
    inside B20, and the foot is 600 mm south of the other drawings.
  - **B-27-S** (section A-A) lands on +3.50 and matches the section's turn treads. Its last riser is still 200 mm
    inside B20.
  - **B-27-SM** clears B20 only with proposed 272.7 mm goings.
- **Transition levels** close on +1.00 / +5.50, and the riser numbering is contiguous.
- **The cause of the B20 clash** is the upper flight, not the total.
  - The landing edge is 3100 mm from B20, so at most 11 risers fit at 300 mm.
  - Every 12-riser flight at 300 mm is 200 mm inside B20.
  - 12 risers fit only with goings of 272.7 mm (with a 100 mm strip) or 281.8 mm (with none).
- **Section A-A.**
  - The turn has five dashed treads at the levels after risers 10 - 14 of 27 equal risers, each within 6 mm. Only
    B-27-S and B-27-SM match them.
  - The landing is 1.2 m deep and the upper run 3.3 m.
  - The arrival scales at y 16112, and the foot within 50 mm of the architectural foot.
- **Fan centre.** The three winder radials are read by handle. Their pairwise intersections agree with the builder's
  least-squares centre within 3 mm.
- **1F -> 2F.**
  - The owner's 27: 155.556 mm risers, landing +7.989, B23 clear by 100 mm.
  - The structural sheet: 24 risers of 175 mm.
  - Section A-A: 25 risers of 168 mm, 200 mm inside B23.
  - Plan capacity: 24 risers with a flat quarter, 27 with the four-riser turn.
- **Round stair.** The statuses are pinned. Beam CA leaves 1.589 m headroom if it sits at the 1F floor. The corner
  landing is +4.696 if the risers are equal.
- **Concrete.**
  - Every flight matches the closed form, and waist plus step wedges equals the section integral.
  - GROSS = NET + deductions on every row.
  - The B20 zone is checked by a brute-force midpoint integral.
  - The S8.7 landing and the strips of unsettled ownership never enter a total.
  - **A-28 reproduces S8.7B's frozen owner-28 figures.** The flights and the B20 zone match exactly, the column
    cut-out within 1e-7 m3 and the turn within 1e-6 m3, because S8.7B publishes its tread areas to 1e-6 m2.
- **Reinforcement.** The 8Ø16/m lengths are checked by hand. S8.7, S7 and S6 ownership is preserved, and the ten
  typical-only families are blocked.
- **Records.** The RFI, conservation checks C01 - C15, the README statements, the SVG validity (no embedded images)
  and the hygiene.
- **With the private drawings:** a byte-identical rebuild, and a raw-ezdxf re-read of the radials and the B20 edges.

## Targeted

```
python3 -m pytest -o addopts="" -p no:cacheprovider tests/stairs_s8_7c tests/stairs_s8_7b tests/stairs_s8_7a tests/stairs_s8_7 tests/lift_s8_8 tests/structural_comparison_engine tests/lintels_s8_6a tests/lintels_s8_6 tests/r8_0/test_r8_0_import_boundaries.py tests/r8_1/test_r8_1_boundaries.py tests/environment_recovery
```

Results:

- At `584384f`: 325 passed, 1 xfailed. That is S8.7B's 303 plus this round's 22. The xfail is the recorded B-7
  boundary debt, older than S8.
- At `0c7e1b5`: 330 passed, 1 xfailed (the five post-freeze tests added).
- `tests/stairs_s8_7c`: 27 passed.

| File | Tests | Covers |
|---|---|---|
| `test_stair_fit_checks.py` | 5 | Synthetic only: run ends in both directions, band-clearance sign, riser capacity and the going to fit, transition levels over 100 random stairs, headroom |
| `test_s8_7c_package.py` | 17 | Everything listed above |
| `test_s8_7c_post_freeze.py` | 5 | The freeze is intact and the comparison downstream; V3b reproduced and every difference classified; candidates against earlier figures; nothing released; an identical rerun |

The builder was also run twice by hand, with byte-identical output (16 files).

### Found while building

- **Wall lines.** In section A-A the wall lines are about 50 mm wide at 1:100. Measured from a line's edge, the
  landing came out 1172.5 mm deep. Measured between line centres, as the risers are, it is 1195.8 mm.
- **The fifth winder tread.** The fifth dashed tread (+3.336) touches a solid line. It is found by its dashed columns,
  not by the width of the group.
- **The S1 beam register** has unsized rows (no B_cm). They are skipped.
- **Fan centre.** The diagram's fan centre was first a constant. It is now the least-squares intersection of the three
  radials read by handle (rms miss 1.64 mm).
- **Column 36B.** The cut-out now uses the rectangle read by handle instead of constants. The values are the same.
- **Diagram checks.** The diagrams were checked visually from headless-Chromium renders. A first render clipped the
  bottom of the page; the renders stay in the scratchpad and are never committed.

## Full suite

**Full suite: NOT GREEN. Gate: INCOMPLETE.**

`python3 -m pytest -o addopts="" -q -rfEs -p no:cacheprovider --junitxml=...` was run on the clean committed tree
`0c7e1b5`. No file was edited during the run.

| Run | Commit | Passed | Failed | Errors | Skipped | xfailed | Time | Exit |
|---|---|---|---|---|---|---|---|---|
| 17 | `f1e04c1` (S8.7B) | 7081 | 344 | 32 | 138 | 100 | 319.1 s | 1 |
| 18 | `0c7e1b5` (S8.7C) | **7108** | 344 | 32 | 138 | 100 | 340.9 s | 1 |

- The 27 extra passes are this round's tests: 5 synthetic, 17 package and 5 post-freeze. All of them executed and
  passed; none is skipped.
- The blocked (376), prerequisite-skipped (136), skip-reason and code-failure (0) sets are identical to run 17's,
  test for test.
- The 344 failures and 32 errors are the unchanged missing-private-data set. They are not code failures, and none
  touches S8.7C.

| Class (`classify_test_run.py`) | Tests |
|---|---|
| 1. Executed and passed | **7108** |
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

- **Section A-A is measured from a 600 dpi render.** Its positions and levels are indicative (`SCALED_FROM_SECTION`).
- **Some geometry is proposed, not drawn.** The five-riser turn and the 272.7 mm goings are proposals. The five-riser
  turn's tread areas are equal shares of the drawn quarter.
- **Winder volumes are approximations.** They are plane-equivalent, with a flat-soffit upper bound.
- **No floor or stair build-up is printed, and the waist is unknown.**
- **The diagrams are schematic** and drawn from coordinates. They are not drawings.
