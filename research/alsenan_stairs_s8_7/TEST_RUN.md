# S8.7 TEST_RUN: staircases and landings (population, geometry, concrete, reinforcement)

Baseline HEAD `3bdc894`. Date 2026-10-10. Commits of the round:

| Commit | What it holds |
|---|---|
| `72d95fc` | **The blind freeze**: the engine `engine/source/stair_geometry.py`, the builder, outputs 00-16 + `17_S8_7_FREEZE_MANIFEST.json` (`FROZEN_BEFORE_COMPARISON`, `references_read: []`), the synthetic and package tests, the registry entries |
| `72e503e` | The post-freeze comparison (`post_freeze/`) and its tests (COMPARISON_MODULES) |
| this commit | This record and the gate report `TEST_GATE_72e503e.json` |

S8.7 finds **two staircases and two step flights**:

- **ST-A**: the main dog-leg stair, GF -> 1F -> 2F, in two storey runs.
- **ST-C**: the light-well stair, GF -> 1F.
- **ST-B**: the lobby steps, 4 risers from +1.00 down to +0.30.
- **ST-D**: the entrance steps, 5 risers from +0.15 to +1.00. They were omitted from S1 / PRE-S8.

The five PRE-S8 zones are the two staircases plus one repeated ground view.

It releases **0.516582788 m3 and 59.020862261 kg (Ø16)** on the project basis. These are three flat plates whose
outline, level and thickness all have authority:

- the GF -> 1F half-landing at +3.50;
- the 1F -> 2F arrival strip at +9.70;
- the light-well top arrival at +5.50.

The rest is not released:

- Every flight is blocked or in source conflict. The GF -> 1F riser counts differ between the plans; the 1F -> 2F
  half-landing level and the light-well corner landing level are not printed; no waist is printed.
- Every winder turn, unlevelled landing and step flight is blocked.
- Each of these keeps its sensitivity, which is never released.
- No frozen quantity moves. All 24 earlier freezes (22, S8.6, S8.6A), the S8.3 errata and the S1 / S2 / S3 / S3.1
  register indexes still verify.

## Targeted

```
python3 -m pytest -o addopts="" -p no:cacheprovider tests/stairs_s8_7 tests/structural_comparison_engine tests/lintels_s8_6a tests/lintels_s8_6 tests/r8_0/test_r8_0_import_boundaries.py tests/r8_1/test_r8_1_boundaries.py tests/environment_recovery
```

At `72e503e`: 206 passed, 1 xfailed (the recorded B-7 boundary debt, older than S8.7). `tests/stairs_s8_7`: 38
passed.

| File | Tests | Covers |
|---|---|---|
| `test_stair_geometry.py` | 17 | Synthetic only; see below |
| `test_s8_7_package.py` | 17 | See below |
| `test_s8_7_post_freeze.py` | 4 | Freeze intact and the comparison downstream; every V3b stair line classified; sensitivity stays context; identical rerun |

`test_stair_geometry.py` covers:

- **Flights:** riser / going arithmetic; a sloping waist between plumb cuts in closed form.
- **Against shapely:** 240 random flights match an independent shapely construction (the stepped top cut by the
  soffit and landing half-planes).
- **Unions:** flight-landing union with no double prism; a dog-leg unfolded so its union counts the half-landing
  once.
- **Members, voids, winders:** landing-beam cut-out; a landing with a void; winder kites tiling the quarter.
- **Curved flights:** plan area and helicoid soffit checked against numerical integration.
- **Bars:** rate density and rate count; two directions over one plate.
- **Plan evidence:** tread-run detection with distractors (wall pairs, short lines); the fan centre of radial
  treads.
- **Tiling:** a bay tiled with no double count; invalid inputs refused.

`test_s8_7_package.py` covers:

- **Freeze and blindness:** the freeze; all 24 earlier freezes; PRE-S8 column whitelists, with no firewalled file in
  the inputs; the recorded exposure; registry entries.
- **Population:** four stair elements from five zones; every tread run assigned.
- **As drawn:** riser counts in each drawing; levels as printed.
- **Exact closure:** the stair zones tiled exactly; RG-02 and SP-GBP-12 partitioned exactly, never counted as
  ground slab.
- **S7:** the stair-adjacent top steel recomputed run by run from `04_S7_BAR_RUNS.csv`.
- **Quantities:** concrete and bars by hand; only the three plates released; p.16 roles; ownership; conservation;
  hygiene.

With the private drawings it also covers:

- a byte-identical rebuild;
- **ezdxf directly, without the S1 reader or the builder**:
  - the A1-L1 edges (1200 x 1200) from lines 279 / 25A / 25B;
  - the C-T1 outline from 2CF / 289 / 2CE / 315, equal to the released area;
  - the printed '3300' / '1200' / '2500' dimensions;
  - the architectural riser lines per column: 1F 12 / 11; GF 10 (against the structural 12) and 11.

The builder was run twice with byte-identical output.

### Found while building

- **Two GF -> 1F tread sets disagree between the plans.** The structural GF roof sheet starts the flights at 16162 /
  16112 (12 + 12 risers). The architectural GF plan starts them at 16712 / 16412 (10 + 11). The structural 1F roof
  sheet equals the architectural 1F plan exactly. Recorded as SOURCE_CONFLICT (Q-ST-01), not resolved by majority.
- **Double lines in the light well are bar symbols, not walls.** 2CC/2CD, 535/536 and the arcs 2DB/2DC carry the
  callouts 53D, 537 and 5BC, as the ST-layer pairs do in the main bay.
- **The 300 mm outline 54E under the light-well straight flight is beam CA (S1 BL015).** Its level against the
  flight is a question (Q-ST-10).
- **The waist convention.** The waist is measured below the line through the step roots, not the nosings. A
  nosing-line waist put the soffit above the step roots for thin waists, and the engine refused it as a non-simple
  outline. A plumb top cut first left a zero-width spike, which shapely flagged.
- **Zone conservation found an unassigned 1F -> 2F arrival strip** (0.12 m2). It is now element A2-T1.
- **The entrance steps' top tread sits 50 mm onto ground beam BL021** (S5). This is recorded in the supports; the
  steps are blocked.
- **Hygiene caught level ids** shaped like the drawing number; they were renamed.

## Full suite

**Full suite: NOT GREEN. Gate: INCOMPLETE.**

`python3 -m pytest -o addopts="" -q -rfEs -p no:cacheprovider --junitxml=...` was run on the clean committed tree
`72e503e`. No file was edited during the run.

| Run | Commit | Passed | Failed | Errors | Skipped | xfailed | Time | Exit |
|---|---|---|---|---|---|---|---|---|
| 13 | `9dd7804` (S8.6A) | 6946 | 344 | 32 | 138 | 100 | 227.6 s | 1 |
| 14 | `72e503e` (S8.7) | **6984** | 344 | 32 | 138 | 100 | 232.8 s | 1 |

- The 38 extra passes are this round's tests. All of them executed and passed; none is skipped.
- The blocked, code-failure and prerequisite-skipped test sets are identical to run 13's.

| Class (`classify_test_run.py`) | Tests |
|---|---|
| 1. Executed and passed | **6984** |
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

- p.16 of ST7757.pdf and SECTION A-A of the architectural PDF have no vector text. They enter as visual records read
  from 150 - 600 dpi renders; the renders stay outside git.
- The riser count of a flight is read from drawn lines, each set of paired nosing / riser lines counted once. Single
  and double steps (one or two risers) are not searched on the structural sheets. On the architectural tread layers
  there is no two-line set.
- No section cuts the light-well stair. Its corner landing level and the 1F -> 2F half-landing level are not
  printed, so those flights stay blocked.
- Bar quantities are rate density over the released plates (the slab family's AD2-D02 reading). Anchorages, bends
  and the continuation into the flights are separate blocked rows.
