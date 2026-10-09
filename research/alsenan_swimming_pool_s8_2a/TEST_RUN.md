# S8.2A TEST_RUN: architectural elevation source recovery and pool depth authority

Baseline HEAD `3286056`. The round has four commits:

| Commit | What it holds |
|---|---|
| `1900650` | The first freeze of the S8.2A correction layer: 12 outputs plus `12_S8_2A_FREEZE_MANIFEST.json` (`FROZEN_CORRECTION_LAYER`, `references_read: []`); generic engine tests and package tests. |
| `74d033d` | `research/environment_recovery/`: the missing-prerequisite manifest, the proposed inputs lock, the prerequisite checker, the pinned requirements and their tests. |
| `0aa0642` | **The re-freeze.** The two uploaded PDF parts are treated as one 12-sheet drawing set, as the user clarified. It is registered as additional evidence, not as a replacement. |
| this commit | This record. |

S8.2A releases **0 m3** of concrete and **0 kg** of reinforcement. S8.2 is not written, and every one of its 18
outputs still verifies against its manifest.

## What the re-freeze changed

Six outputs are unchanged, byte for byte, from the first freeze:

- 02 binding;
- 04 levels and zones;
- 05 readiness;
- 06 blocked;
- 07 conflicts and questions;
- 08 sensitivity.

`test_the_re_freeze_names_the_first_freeze_and_changes_no_finding` checks this against `git show 1900650`.

The changes are in 00, 01, 03, 09, 10 and 11:

- **Set identity row.** One row for `P7757_ARCH_PDF_SET_01-12`: part 1 holds sheets 01-06, part 2 holds sheets
  07-12.
- **Set sheets.** Every page, visual record and dimension-register row names its set sheet. The NW elevation is
  sheet 08 and the GF plan is sheet 03.
- **Registration.** The set and both parts are registered as additional architectural evidence, not as a replacement
  for the earlier registered PDFs.
- **Byte finding, worded as evidence.** Each part is byte-identical to the earlier registered part after removing 134
  bytes of added /Title and /Subject.
- **No dependency on the reconstructed copies.** The output column that depended on them being on disk is gone. The
  rebuild was run with the two copies moved aside and was byte-identical.
- **New check A-13.** It checks the one-set sheet numbering.
- **Provenance.** VR-09 (all title blocks) now names both parts.

## Targeted

```
python3 -m pytest -o addopts="" -p no:cacheprovider tests/swimming_pool_s8_2a tests/swimming_pool_s8_2 tests/environment_recovery tests/structural_comparison_engine tests/r8_1/test_r8_1_boundaries.py
```

| Run | Result |
|---|---|
| At `0aa0642` | **171 passed** |

The 30 tests of this round:

| File | Tests | Covers |
|---|---|---|
| `tests/swimming_pool_s8_2a/test_elevation_binding.py` | 10 | Synthetic known answers: levels, cylinder generators, arc projection and view direction, binding rules, floor profile, PDF wrapper-metadata identity on pypdf-made files |
| `tests/swimming_pool_s8_2a/test_s8_2a_package.py` | 17 | Freeze, S8.2 untouched, the one-set identity, sheet numbers, the re-freeze against the first freeze, binding, the homonym, depth scope, no release, conflicts carried, sensitivity, A-01..A-13, hygiene, blindness, registry, byte-identical rebuild |
| `tests/environment_recovery/test_recovery_manifest.py` | 3 | Every missing prerequisite routed; the lock holds hashes only; the checker flags drift |

- The builder was run twice and gave byte-identical output (13 files). `test_rebuild_is_byte_identical` repeats this
  under `python -I`.

## Full suite: NOT GREEN

`python3 -m pytest -o addopts="" -q -rfEs -p no:cacheprovider --junitxml=...` was run on clean committed trees. No
file was edited during any run.

| Run | Commit | Passed | Failed | Errors | Skipped | xfailed | Time | Exit |
|---|---|---|---|---|---|---|---|---|
| 5 | `74d033d` | 6687 | 344 | 32 | 138 | 100 | 313.8 s | 1 |
| 6 | `0aa0642` | **6689** | **344** | **32** | **138** | **100** | 297.8 s | 1 |

Run 4 was at `52fa35f` (the S8.2 TEST_RUN): 6659 passed, with the same 376 non-passing tests.

The JUnit XML of each run attributes every one of the 376 failures and errors. The set of failing test IDs is
identical in runs 4, 5 and 6, and every one is a missing private file:

| Cause | Tests |
|---|---|
| `data/experiments/P7757_WALL_TREATMENT_ESTIMATE_01/...` (derived experiment data, not in this container) | 373 |
| `data/runs/7757/...` (derived run) | 1 |
| A workbook test that stops with "run workbook_boq first": its derived workbook is not in this container | 1 |
| A test that reads an old session upload under `/root/.claude/uploads` | 1 |

No failure comes from S8.2A or S8.2 code. The extra passes since run 4 are this round's 30 tests.

The 107 missing paths, their expected SHA-256 where git pins one, and their restore routes are in
`research/environment_recovery/RECOVERY_MANIFEST.json`.

## Limitations

- **The full suite is red.** Until the private derived data is restored or the proposed lock-based skip lands, a
  green full run is not available in this container.
- **The visual records are a human-style reading of the raster sheets in this session.** The crops are client
  drawing and are kept out of git; each record keeps its set sheet and pixel box, so it can be re-checked on the
  restored set.
- **The binding is tested on the real DXF only when the private drawings are present.** Without them, the
  drawing-dependent tests skip (`needs_inputs`). The synthetic tests always run.
- **The re-freeze test needs the first-freeze commit in the clone's history.** It skips in a shallow clone that lacks
  `1900650`.
