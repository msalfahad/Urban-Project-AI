# S8.5 TEST_RUN: special columns (turned, dead and planted)

Baseline HEAD `9a82950`. Commits of the round:

| Commit | What it holds |
|---|---|
| `4531f05` | **The blind freeze**: the engine `engine/source/special_column_components.py`, the builder, 17 outputs + `17_S8_5_FREEZE_MANIFEST.json` (`FROZEN_BEFORE_COMPARISON`, `references_read: []`), the synthetic and package tests, the registry entries |
| `8b53c69` | The post-freeze comparison (`post_freeze/`) and its tests (COMPARISON_MODULES) |
| this commit | This record and the gate report `TEST_GATE_8b53c69.json` |

S8.5 releases **0 kg** of reinforcement and **0 m3** of concrete.

- The six labels bind to six real S1 / S3.1 column occurrences:
  - two turned columns: C8 and C9, GF -> 1F at the GF roof;
  - one dead column: C11, which stops at the GF roof;
  - three planted columns, each in the storey above its slab: 544 and 548 at 1F, 77C at 2F.
- The special extras already counted stay with their owners:
  - S3.1's 4Ø16 at the two turns (12.642 kg each);
  - S6.1's beam extra for 548 (12.009877 kg).
- 24 roles stay blocked with their questions and 18 sensitivity cases:
  - the spiral (undimensioned);
  - the cranks;
  - the planted starters;
  - 544's and 77C's beam extras (each column sits on a beam-on-beam node);
  - the dead-column termination.
- No frozen quantity moves. All 21 earlier freeze manifests, the three S8.3 errata files and the S1 / S2 / S3 / S3.1
  register indexes still verify.

## Targeted

```
python3 -m pytest -o addopts="" -p no:cacheprovider tests/special_columns_s8_5 tests/water_tank_s8_4 tests/dome_mesh_s8_3a tests/dome_ring_s8_3 tests/structural_comparison_engine tests/r8_0/test_r8_0_import_boundaries.py tests/r8_1/test_r8_1_boundaries.py tests/environment_recovery
```

At `4531f05` this gave 253 passed and 1 xfailed. The xfail is the recorded B-7 boundary debt: two engine modules import
a research parameter file. It predates S8.5. With the post-freeze tests (`8b53c69`), `tests/special_columns_s8_5` plus
the registry firewall gave 110 passed.

| File | Tests | Covers |
|---|---|---|
| `test_special_column_components.py` | 29 | Synthetic known answers only. See the list below |
| `test_s8_5_package.py` | 22 | See the list below |
| `test_s8_5_post_freeze.py` | 5 | Freeze intact, every row classified, V3b reproduced by its own formula with no special component, registered, identical rerun |

`test_special_column_components.py` covers:

- **Labels name events, never bars:** T.C / D.C / P.C (with and without a printed section, compact 'P.C20X50'
  included). C.S, F.C, C.A, B.W and noise are refused. Bar-count texts are read; rates, bare numbers and zero
  counts are refused.
- **Storey of a planted column:** the storey above its slab (GFRS -> 1F, FFRS -> 2F). There is nothing above the
  top slab.
- **Plan geometry:**
  - axis rectangles (rotated ones are refused);
  - the turn overlap (200 x 250);
  - a footprint's length along an oblique beam;
  - span relations (INSIDE / AT_END / OUTSIDE).
- **Host resolution:** only one INSIDE span names a host. Beam ends meeting under a column are a NODE, never a host.
- **Quantities:**
  - the pitch and turn count come from the stated rate (12 turns over 2 m at 6/m);
  - the ellipse perimeter is checked against a numerical arc length;
  - the helix length is longer than both the pitch and the plan perimeter;
  - the inscribed centreline (142 x 192) is an upper bound only;
  - the beam-extra projection and the unit mass are checked.
- **Ownership:**
  - a role another stage holds is never added again, even when part of it is blocked;
  - a role held blocked stays blocked;
  - a role is added only when the source requires it and fixes its quantity.

`test_s8_5_package.py` covers:

- **The freeze and every earlier stage:** all 21 manifests, the S8.3 errata, and the S1 / S2 / S3 / S3.1 register
  indexes.
- **Blindness:** PRE-S8 is read through a column whitelist that never binds its quantity column. The registry is
  checked.
- **The six records:**
  - they equal PRE-S8's candidate ids (id column only) and S1's special register;
  - they bind to six real column occurrences, with no second column;
  - storeys and extents are 1F +5.50 -> +9.70 and 2F +9.70 -> +13.90;
  - 548 is on B26; 544 and 77C stay unresolved on their four-span nodes.
- **No double count:**
  - every one of the 56 S3.1 rows of the eight special segments is cited exactly once;
  - nothing already owned is added again;
  - S3.1's and S6.1's totals are unchanged.
- **By hand:**
  - the 4Ø16 extras (4 x 2 m);
  - S6.1's 548 extra (4 x (2 x 850 + 200));
  - every host reading of 544 and 77C;
  - both spiral bounds (circular 142 mm, elliptical 142 x 192, 12 turns);
  - the 1 m continuity range;
  - the starters.
- **Registers:** concrete never re-added; footing starters NOT_APPLICABLE in S4; ground beams under S5; blocked roles,
  questions, conflicts and dated ownership deltas (0 kg moved).
- **Conservation and hygiene:** 16 checks, no drawing, no Arabic run, no title-block text.

With the private drawing present it also covers:

- through ezdxf: the labels, bar texts, circles, leaders and outlines, with outlines compared in their sheet frames;
- through shapely: the turn overlaps and the circles' relation to the outlines;
- a byte-identical rebuild.

The builder was run twice with byte-identical output (18 files).

### Defects found and fixed before the freeze

- **A held role could have been released as new.** The first ownership rule recognised only a single released state.
  Ties held partly LOWER_BOUND and partly BLOCKED (C9 GF, C11 GF), and candidate beams in mixed S6 states (77C), would
  have been treated as unowned. A role is now owned when any part of it is released by its stage, and a test covers it.
- **The turn binding was too strict.** Circle 31C encloses the GF outline but only meets the turned 1F outline. The
  binding now asks that the circle meet an outline, and it records which outlines are enclosed.
- **548's beam extra was checked against the wrong length.** S6.1 used the 200 mm column width, its stated lower
  bound. The drawn footprint spans 212.9 mm along B26, which runs at 88.51 deg. The check now verifies S6.1's own
  formula. The exact projection (+0.082 kg) is a sensitivity, and the role stays S6.1's.
- **Smaller defects:**
  - untagged S6 continuation spans at both planted nodes were missed and are now listed as candidates;
  - span limits printed as '825' for 8250;
  - the compact label 'P.C20X50' was refused;
  - two Arabic rule texts were copied into the register;
  - a rounded beam angle broke a by-hand recomputation.

## Full suite

**Full suite: NOT GREEN. Gate: INCOMPLETE.**

`python3 -m pytest -o addopts="" -q -rfEs -p no:cacheprovider --junitxml=...` was run on the clean committed tree
`8b53c69`. No file was edited during the run.

| Run | Commit | Passed | Failed | Errors | Skipped | xfailed | Time | Exit |
|---|---|---|---|---|---|---|---|---|
| 10 | `b2afdb5` (S8.4) | 6808 | 344 | 32 | 138 | 100 | 348.2 s | 1 |
| 11 | `8b53c69` (S8.5) | **6864** | 344 | 32 | 138 | 100 | 319.4 s | 1 |

- The 56 extra passes are this round's 56 tests (29 + 22 + 5). All of them executed and passed; none is skipped.
- The blocked, code-failure and prerequisite-skipped test sets are identical to run 10's.

### Every test, classified (`classify_test_run.py`, run 11)

| Class | Tests | Meaning |
|---|---|---|
| 1. Executed and passed | **6864** | The only class that proves anything |
| 2. Legitimately skipped: prerequisite unavailable | **136** | A private input, fixture, client data or generated artefact is absent. Never counted as a pass |
| Skipped for another reason | 2 | `QS_MEASUREMENT_REGION_BUILDER does not exist yet` |
| Expected failures (xfail) | 100 | Recorded by the tests themselves |
| 3. Mandatory regression blocked by missing data | **376** | Failed or errored on a missing required file |
| 4. Actual code failures | **0** | |

The 376 blocked tests, by missing path:

| Missing | Tests |
|---|---|
| `data/experiments/P7757_WALL_TREATMENT_ESTIMATE_01/...` | 373 |
| `data/runs/7757/...` | 1 |
| A generated prerequisite (`run workbook_boq first`) | 1 |
| A session upload under `/root/.claude` | 1 |

**Complete-project regression gate: INCOMPLETE.**

- 376 mandatory regression tests are blocked by missing data.
- 136 tests are skipped for an unavailable prerequisite.
- 108 locked prerequisites are missing: 14 BENCHMARK, 87 DERIVED and 7 SOURCE.

The gate stays INCOMPLETE until the private fixtures and the sealed benchmark evidence are restored.

- The blind builder never read benchmark truth.
- Test IDs and missing paths are in `TEST_GATE_8b53c69.json`.
- That file holds no content and no benchmark value.

## Limitations

- The full suite is red because private data is missing. No missing-data skip is presented as a pass.
- The p.15 details exist only as a plot. Their reading, measured on 600 dpi renders, enters as visual records; the
  renders stay outside git.
- Column concrete is counted per occurrence by S2 and is not measured in m3 by any stage. S8.5 adds none and measures
  none.
- The drawing-dependent tests skip when the private drawing is absent. The synthetic engine tests always run.
