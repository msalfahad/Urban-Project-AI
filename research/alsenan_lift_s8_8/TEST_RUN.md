# S8.8 TEST_RUN: lift pit, shaft walls, foundation and intermediate tie beam

Baseline HEAD `dc2d778`. Date 2026-10-10. Commits of the round:

| Commit | What it holds |
|---|---|
| `8b856d6` | **The blind freeze**: the engine `engine/source/shaft_geometry.py`, the builder, outputs 00-17 + `18_S8_8_FREEZE_MANIFEST.json` (`FROZEN_BEFORE_COMPARISON`, `references_read: []`), the synthetic and package tests, the registry entries |
| `0bad737` | The post-freeze comparison (`post_freeze/`) and its tests (COMPARISON_MODULES) |
| this commit | This record and the gate report `TEST_GATE_0bad737.json` |

S8.8 finds **one lift shaft**, LIFT-01. Every view of it groups into one physical shaft:

- the S-BW outlines on the foundation and ground-beam plans;
- the open-to-below panels at +5.50 and +9.70, and the roof panel at +13.90;
- the inside faces on the three architectural plans.

The only other S-BW outline is the S8.2 pool.

The shaft and its plan geometry:

- **Shaft:** 1800 x 1800 inside, 200 walls, four corner columns, on the FF footing (460 x 450 x 55). Three stops,
  each with a 1000 door in the S wall.
- **Ring:** 1.60 m2. The columns take 0.50 m2 of it once. The net wall pieces (S 1.8, N 1.8, W 1.2, E 0.7 m) give
  1.10 m2. They equal S8.1A RG-12..15 exactly.
- **Opening:** the 3.24 m2 S8.1A opening is the pit's inside area.
- **Pit floor:** the FF footing top. No pit slab is drawn, so no second base is added.

It releases **0 m3 and 0 kg**:

- **Pit depth.** The depth is 'As Per Lift Manufactures recommendations' and the founding level is not printed. No
  pit-wall height exists, so the wall concrete and every p.14 wall bar are blocked. Each keeps its conditional
  coefficient and one sensitivity reading, which is never released.
- **FF footing.** It stays with its owners:
  - mats: S4, 720.239506 kg Ø14, a lower bound;
  - starters: S3.1, 85.271 kg;
  - concrete: 11.385 m3, computable but unmeasured by any frozen stage.
- **P8-N19.** It triggers a GF tie beam only under floor-to-floor height (4.50 > 4.30). Clear to the beam soffit is
  at most 3.75 m, and the note defines no measure and states no section, so the beam is blocked. 1F and 2F are never
  triggered.
- **Freezes.** No frozen quantity moves. All 25 earlier freezes (S4 ... S8.7, S8.6A), the S8.3 errata and the S1 /
  S2 / S3 / S3.1 register indexes still verify.

## Targeted

```
python3 -m pytest -o addopts="" -p no:cacheprovider tests/lift_s8_8 tests/stairs_s8_7 tests/structural_comparison_engine tests/lintels_s8_6a tests/lintels_s8_6 tests/r8_0/test_r8_0_import_boundaries.py tests/r8_1/test_r8_1_boundaries.py tests/environment_recovery
```

At `0bad737`: 243 passed, 1 xfailed (the recorded B-7 boundary debt, older than S8.8). `tests/lift_s8_8`: 37 passed.

| File | Tests | Covers |
|---|---|---|
| `test_shaft_geometry.py` | 16 | Synthetic only; see below |
| `test_s8_8_package.py` | 17 | See below |
| `test_s8_8_post_freeze.py` | 4 | Freeze intact and the comparison downstream; every earlier lift figure classified; the FF volume agrees; identical rerun |

`test_shaft_geometry.py` covers:

- **Corners:** a rectangular shaft counts every corner once (centreline x thickness = the ring).
- **Against shapely:** 150 random orthogonal shafts match a mitred shapely buffer (area and both perimeters). 200
  random corner-column layouts match shapely: ring, net, overlaps, and pieces that tile without overlap.
- **Members:** a corner column spanning two wall bands is deducted once. A column proud of the face is cut to the
  ring. Partial-thickness and overlapping members are refused.
- **Openings:** a door split keeps each corner on the outer face only. An opening over a column is reported, not
  deducted twice.
- **Footing:** plan overlap of walls with a footing. Walls start at the base top, so the interface is never counted
  twice.
- **Pit:** a missing depth stays NOT_ESTABLISHED.
- **Storeys:** multi-storey segments that skip bands owned elsewhere. Tie-beam triggers under each height measure,
  and "exceeds" is strict.
- **Representations and ownership:** repeated plan views group into one object. The six ownership states, where an
  owner is not a measurement.
- **Rates:** rate counts.

`test_s8_8_package.py` covers:

- **Freeze and blindness:** the freeze; all 25 earlier freezes; PRE-S8 column whitelists; no benchmark file in the
  inputs; registry entries.
- **Population:** one physical shaft, with the pool outline not a lift. One footing, no pit base.
- **Exact closure:** the ring, the column cut-outs and the net pieces, rebuilt in shapely from the outputs. RG-04 is
  the pit's inside area, and RG-12..15 are the pieces.
- **Owners:** the FF footing mats, starters and S4.1-T01 transfer read back from S4 / S3.1 / S4.1.
- **Quantities:** nothing released; every conditional coefficient by hand (vertical counts 11 / 11 / 8 / 5 per
  face).
- **Levels:** blocked or printed as recorded.
- **P8-N19:** per storey and per measure.
- **S6:** the 12 beams on the shaft recounted from S6.
- **Openings, callouts, ownership:** landing openings reconciled with S8.6; callout roles and owners; the six
  ownership states; conservation; questions; hygiene.

With the private drawings it also covers:

- a byte-identical rebuild;
- **ezdxf directly, without the S1 reader or the builder**:
  - the six S-BW outlines (four for the shaft, two for the pool);
  - 1800 / 2200 faces 200 apart on both plans;
  - the ring minus the four columns = 1.10 m2;
  - the 4600 x 4500 footing containing the shaft;
  - the FF schedule row (460 / 450 / 55, 6 and 9 Ø14/m);
  - the printed 1800 / 200 dimensions on all three architectural plans;
  - the 1000 door jambs, 400 from each inside corner.

The builder was run twice with byte-identical output.

### Found while building

- **PRE-S8's "shaft outline not drawn" is wrong.** The outline is on the S-BW layer of both foundation-level plans
  and is dimensioned on all three architectural plans.
- **The foundation-storey lift columns conflict.** The plans draw them 200 wide (250 for C9), flush with the 200 pit
  walls. The column schedule gives 300, and S3 used the schedule (flag STR-COL-013). This is recorded as
  SOURCE_CONFLICT (Q-LIFT-08). The wall pieces follow the drawn plans until it is resolved.
- **The P8-N19 trigger depends on a measure the note does not define.** GF is 4.50 m floor to floor, but at most
  3.75 m clear under the 750 mm beams. Clear to the slab soffit exceeds 4.30 only with less than 40 mm of finish.
- **The pit floor is the FF top, and FF is at least 1.5 m below the plot level.** The implied pit is therefore at
  least about 1.95 m deep, whatever the manufacturer needs (Q-LIFT-02).
- **The p.14 section cuts only two walls.** They are the door wall (S) and the wall opposite (N). Bars for W and E
  are recorded as NOT_SHOWN, not assumed.
- **A level-state typo was caught by the package test.** A bare "BLOCKED" was used where the lane constant belongs.
  It was fixed before the freeze.

## Full suite

**Full suite: NOT GREEN. Gate: INCOMPLETE.**

`python3 -m pytest -o addopts="" -q -rfEs -p no:cacheprovider --junitxml=...` was run on the clean committed tree
`0bad737`. No file was edited during the run.

| Run | Commit | Passed | Failed | Errors | Skipped | xfailed | Time | Exit |
|---|---|---|---|---|---|---|---|---|
| 14 | `72e503e` (S8.7) | 6984 | 344 | 32 | 138 | 100 | 232.8 s | 1 |
| 15 | `0bad737` (S8.8) | **7021** | 344 | 32 | 138 | 100 | 297.8 s | 1 |

- The 37 extra passes are this round's tests. All of them executed and passed; none is skipped.
- The blocked, code-failure and prerequisite-skipped test sets are identical to run 14's.
- Two older failures whose names contain "lift" are a Qortuba apartment rule and the villa blind inventory. Both are
  in the unchanged blocked-by-missing-data set; neither touches S8.8.

| Class (`classify_test_run.py`) | Tests |
|---|---|
| 1. Executed and passed | **7021** |
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

- p.14 of ST7757.pdf has no usable vector text. It enters as a visual record read from 120 - 400 dpi renders; the
  renders stay outside git. p.8 note 19 enters through the S1 rule register (its English interpretation).
- No section or elevation in either drawing set levels the pit, the founding, a lift overrun or a machine room.
- The wall pieces assume the drawn column outlines (see the conflict above).
- The released quantity is zero by authority, not by omission. Every blocked component carries its question (14).
