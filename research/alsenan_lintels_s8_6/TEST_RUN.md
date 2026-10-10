# S8.6 TEST_RUN: lintels (opening census, schedule binding, lintel QTO)

Baseline HEAD `818321e`. Commits of the round:

| Commit | What it holds |
|---|---|
| `308dbc4` | **The blind freeze**: engines `engine/source/opening_census.py` and `engine/source/lintel_qto.py`, the builder, 15 outputs + `15_S8_6_FREEZE_MANIFEST.json` (`FROZEN_BEFORE_COMPARISON`, `references_read: []`), the synthetic and package tests, the registry entries |
| `45db97b` | The post-freeze comparison (`post_freeze/`) and its tests (COMPARISON_MODULES) |
| this commit | This record and the gate report `TEST_GATE_45db97b.json` |

S8.6 releases **14 lintels, 0.745262 m3, 96.427 kg** (project basis):

- 65 wall openings, 1 boundary-wall gate and 8 slab openings are counted once each.
- 52 openings stay blocked, with their sensitivity (4.232 m3, 522.091 kg, not released).
- No frozen quantity moves. All 22 earlier freeze manifests, the S8.3 errata and the S1 / S2 / S3 / S3.1 register
  indexes still verify.

## Targeted

```
python3 -m pytest -o addopts="" -p no:cacheprovider tests/lintels_s8_6 tests/special_columns_s8_5 tests/water_tank_s8_4 tests/structural_comparison_engine tests/r8_0/test_r8_0_import_boundaries.py tests/r8_1/test_r8_1_boundaries.py tests/environment_recovery
```

At `308dbc4`: 236 passed, 1 xfailed (the recorded B-7 boundary debt, older than S8.6). `tests/lintels_s8_6` with the
post-freeze tests: 54 passed.

| File | Tests | Covers |
|---|---|---|
| `test_opening_census.py` | 12 | Synthetic only: face lines, wall bands, masonry / column / closure / unbounded jambs, the evidence gate for corner closures, overhead lines, side points, glazing runs and their ends, curved bands, printed level chains (with conflicts), elevation offset voting |
| `test_lintel_qto.py` | 19 | Synthetic only: printed cells, schedule gaps and overlap refusal, 11 exact boundary widths, no width in two rows, bearing / frame / deficit, overlap cut at the pier middle, strip relation, bar lengths, RATE_COUNT, one lintel by hand |
| `test_s8_6_package.py` | 19 | See the list below |
| `test_s8_6_post_freeze.py` | 4 | Freeze intact, every V3b row classified, V3b reproduced by its own formula, the double counts are the R5 pairs, identical rerun |

`test_s8_6_package.py` covers:

- the freeze and all 22 earlier manifests;
- the PRE-S8 / R5 whitelists and the registry;
- one census row and one decision per opening;
- the lift landings stacked and blocked;
- the R5 pairs collapsing to one opening;
- the exact schedule transcription and boundary cases;
- rows recomputed from widths;
- nothing unsupported released;
- no released lintel under a beam;
- concrete and bars by hand, with totals by floor and diameter;
- every bend, hook, anchorage and lap registered;
- the BOQ link ids, ownership and the 18 conservation checks;
- hygiene.

With the private drawings present it also covers:

- a byte-identical rebuild;
- an independent ezdxf + shapely re-measurement of every released opening: the strip is free of wall faces, the faces
  stop at the jambs, and the width equals the drawn one.

The builder was run twice with byte-identical output.

### Defects found and fixed before the freeze

- A 13.27 m "opening" between two unrelated wall ends was accepted once corner closures counted as jambs. A gap closed
  only by a crossing wall face now needs a door, glazing, arch or overhead-line symbol.
- **Rooms leaked into the exterior.** Wall bodies without end caps, drafting slots under 50 mm and open passages
  merged spaces. Fixed in three ways:
  - the spaces are now built with caps on every band;
  - barriers are thickened and spaces opened, so slots far narrower than any opening never join two spaces;
  - exterior reachability is decided with only door and glazing openings closed.
- The masonry beyond a jamb missed corner blocks and crossing walls, giving bearings of 40 mm or 74 mm. Fixed: one wall
  thickness past the two-face stretch is now counted, and junction holes are filled.
- Beam bands that only touched a jamb were read as a beam over the opening. Contacts under 20 mm are now ignored.
- Two released lintels shared a corner block (1F-017 / 1F-018): the shared 0.0045 m3 is counted once.
- **Wrong source-survey claim.** P7757 does contain 388 dimension entities; the earlier survey said none. They are now
  read:
  - 11 plan widths are printed and equal the drawn widths;
  - the east elevation registers uniquely to the 1F east wall and prints the sills of two full-height glazed
    openings;
  - no head is printed exactly at an opening outline.

## Full suite

**Full suite: NOT GREEN. Gate: INCOMPLETE.**

`python3 -m pytest -o addopts="" -q -rfEs -p no:cacheprovider --junitxml=...` was run on the clean committed tree
`45db97b`. No file was edited during the run.

| Run | Commit | Passed | Failed | Errors | Skipped | xfailed | Time | Exit |
|---|---|---|---|---|---|---|---|---|
| 11 | `8b53c69` (S8.5) | 6864 | 344 | 32 | 138 | 100 | 319.4 s | 1 |
| 12 | `45db97b` (S8.6) | **6918** | 344 | 32 | 138 | 100 | 239.1 s | 1 |

- The 54 extra passes are this round's tests. All of them executed and passed; none is skipped.
- The blocked, code-failure and prerequisite-skipped test sets are identical to run 11's.

| Class (`classify_test_run.py`) | Tests |
|---|---|
| 1. Executed and passed | **6918** |
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

- p.13 has no vector text. The schedule, detail and section enter as visual records read from 400 dpi renders; the
  renders stay outside git.
- No opening height and no door / window schedule is printed. That is why the 46 openings with a beam band over them
  stay blocked: whether the head reaches the soffit is not established.
- The drawing-dependent tests skip when the private drawings are absent. The synthetic engine tests always run.
