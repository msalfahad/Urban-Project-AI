# S8.6A TEST_RUN: lintel bearing, release authority and quantity reconciliation

Baseline HEAD `974bff2`. Date 2026-10-10. Commits of the round:

| Commit | What it holds |
|---|---|
| `9dd7804` | The dated correction layer: the engine `engine/source/lintel_release_audit.py`, the builder, 12 outputs and `12_S8_6A_CORRECTION_MANIFEST.json` (`DATED_CORRECTION_LAYER`, `references_read: []`), the synthetic and project tests, and the registry entries |
| this commit | This record and the gate report `TEST_GATE_9dd7804.json` |

The frozen S8.6 package is verified before and after the build and is never written. All 23 freezes verify: the 22
that S8.6 verified, plus S8.6 itself. So do the three S8.3 errata files and the S1 / S2 / S3 / S3.1 register indexes.

| | Lintels | m3 | kg |
|---|---|---|---|
| Frozen S8.6 release (history) | 14 | 0.745261681 | 96.427279858 |
| Newly blocked: bearing requirement (GF-005, GF-021, GF-029, 1F-017) | -4 | -0.171721681 | -22.371921833 |
| Newly blocked: column connection (GF-013, GF-018) | -2 | -0.12004 | -12.329135804 |
| Withheld: head / function unresolved (GF-014) | -1 | -0.092 | -12.137185185 |
| Corner prism 1F-017 / 1F-018 re-assigned to 1F-018 | 0 | +0.0045 | 0 |
| **Corrected eligible release** | **7** | **0.366** | **49.589037037** |

The figures by floor are in `09_QUANTITY_RECONCILIATION.csv`, and each column closes.

## Targeted

```
python3 -m pytest -o addopts="" -p no:cacheprovider tests/lintels_s8_6a tests/lintels_s8_6 tests/structural_comparison_engine
```

At `9dd7804`: 136 passed. That is S8.6A 28, S8.6 54 (unchanged and still green) and the registry firewall 54.

| File | Tests | Covers |
|---|---|---|
| `test_lintel_release_audit.py` | 15 | Synthetic only, see the list below |
| `test_s8_6a_package.py` | 13 | See the list below |

`test_lintel_release_audit.py` covers:

- **Bearing reach:** straight wall, T-junction (far face), L-corner, a cap line is not a cross wall, a wall crossing is
  masonry while an 800 mm gap is not, a column ends the run, an oblique junction is not verified.
- **Classification:** end and lintel states, and their precedence.
- **Stirrup readings:** the four ways of counting an '/M' rate.
- **Overlaps:** one owner per shared volume.

`test_s8_6a_package.py` covers:

- **Freezes:** the correction manifest; every S8.6 output unchanged; all 23 freezes.
- **States:** all 14 lintel states; the six cases as the drawing gives them.
- **Agreement:** the independent bearing equals the frozen geometry wherever both read the same axis.
- **Quantities:** corrected m3 and kg recomputed by hand; the reconciliation closes for every column; one owner for
  the shared corner.
- **Labels:** cover and stirrup authority labels; ordered sensitivities; rebar lanes follow the lintel state.
- **Census:** 74 ids unchanged; the 9 vs 10 missed populations.
- **Hygiene and registry.**

With the private drawings it also covers:

- a byte-identical rebuild;
- **a second, different method (shapely rays across the wall)**: just past every short end the centreline is open
  space or inside a column; every retained end has no open stretch longer than a wall crossing and no column within
  its 400 mm.

### Found while building

- **The first trace read an oblique junction as a wall end.** At GF-029's start, 45-degree walls meet the faces. That
  end is now `OBLIQUE_JUNCTION` / `BEARING_NOT_VERIFIED`: neither assumed nor called short. GF-029 is blocked by its
  other end (189 mm, L-corner) in any case.
- **The first independent check failed at T-junctions.** Rays across the wall find no face where a cross wall joins.
  It now allows only crossing-length open stretches, mirroring the bearing rule with a different primitive.

## Full suite

**Full suite: NOT GREEN. Gate: INCOMPLETE.**

`python3 -m pytest -o addopts="" -q -rfEs -p no:cacheprovider --junitxml=...` was run on the clean committed tree
`9dd7804`. No file was edited during the run.

| Run | Commit | Passed | Failed | Errors | Skipped | xfailed | Time | Exit |
|---|---|---|---|---|---|---|---|---|
| 12 | `45db97b` (S8.6) | 6918 | 344 | 32 | 138 | 100 | 239.1 s | 1 |
| 13 | `9dd7804` (S8.6A) | **6946** | 344 | 32 | 138 | 100 | 227.6 s | 1 |

- The 28 extra passes are this round's tests. All of them executed and passed; none is skipped.
- The blocked, code-failure and prerequisite-skipped test sets are unchanged.

| Class (`classify_test_run.py`) | Tests |
|---|---|
| 1. Executed and passed | **6946** |
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

- The bearing trace reads axis-parallel and perpendicular wall lines. Oblique junctions are reported as not verified.
- No head is printed for any opening. The seven retained lintels keep the S8.6 project-basis position: a door, arch or
  headed passage leaves wall above its head in a 4.20 to 4.50 m storey. Q-HEAD-GENERAL still stands.
- Cover, straight lengths, stirrup count and shape are measurement conventions. They are labelled as such in
  `04_COVER_AND_STIRRUP_AUTHORITY.csv` and `07_REINFORCEMENT_RECLASSIFICATION.csv`.
