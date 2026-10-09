# S8.2 TEST_RUN: swimming pool, source-controlled concrete and reinforcement QTO

Baseline HEAD `763a00e`. The round has four commits:

| Commit | What it holds |
|---|---|
| `b83dc9d` | Work in progress after the container loss: the recovered builder, the reconstructed engine and the rewritten synthetic tests. It has no outputs and no freeze. |
| `ae6393b` | **The blind freeze.** 18 outputs plus `18_S8_2_FREEZE_MANIFEST.json` in state `FROZEN_BEFORE_COMPARISON`, with `references_read: []`; package and real-geometry tests. |
| `52fa35f` | The post-freeze comparison, its tests, and its registration in COMPARISON_MODULES. |
| this commit | This record. |

S8.2 releases **0 m3** of concrete and **0 kg** of steel. Every total stays unknown, not 0. All 16 earlier frozen
manifests still verify, S7 (3,802.015 kg), S8.1 (3.785852 m3 / 233.694587 kg) and S8.1A included.

## Inputs and recovery

- The three client drawings were restored from `Urban_Alsenan_S8_2_Source_Restore.zip`. All three full SHA-256 hashes
  match `SHA256SUMS.txt` and the hashes the builder pins.
- They sit in `data/inputs/by_sha256/`, which `/data/*` keeps out of git, and are not committed.
- The rebuild reproduces the pre-loss fingerprint row by row (`RECOVERY_NOTE.md`).
- Independent checks of the reconstructed helpers against ezdxf and shapely on the real geometry
  (`test_s8_2_real_geometry.py`) found two latent defects, shared with the pre-loss code, and both were corrected
  before the freeze:
  - **The CCW arc 1849, drawn across 0 degrees.** Effect: BF-R4 SHALLOW_BASE drops from 5718.781 to 5614.513 drawing
    units.
  - **Arc distance measured to the full circle.** Effect: two false incidental contacts are removed.
- Neither correction changes a lane, a state, an owner or a quantity.

## Environment (rebuilt in the new container)

Python 3.11.17. ezdxf 1.4.4, shapely 2.2.0, pypdf 6.19.0, scipy 1.17.1, numpy 2.4.6, cryptography 50.0.2, cffi 2.1.1,
PyMuPDF 1.28.2, anthropic 1.12.1, openpyxl 3.1.5, Jinja2 3.1.6, python-barcode 0.16.1, Pillow 12.3.0, matplotlib
3.11.2, pytest 9.1.1.

The fresh container lacked several of these, and they were added as each failure showed up:

| Package | Why it was needed |
|---|---|
| cryptography + cffi | The system binding panicked under pypdf |
| scipy | The S1 column census needs it |
| PyMuPDF | 9 existing test modules import it; S8.2 code never uses it |
| anthropic | `test_base_models.py` needs it |

S8.1A's rebuild is byte-identical in this environment, so the rebuilt toolchain reproduces an earlier frozen stage.

## Targeted

```
python3 -m pytest -o addopts="" -p no:cacheprovider tests/swimming_pool_s8_2 tests/ground_slab_s8_1a tests/ground_slab_s8_1 tests/structural_comparison_engine tests/r8_1/test_r8_1_boundaries.py tests/r8_8/test_r8_8_architecture.py
```

| Run | Result |
|---|---|
| At `ae6393b` | **229 passed** |
| S8.2 + firewall + K1 boundary, after the post-freeze tests | **141 passed** |

The 71 S8.2 tests break down as follows:

| File | Tests | Covers |
|---|---|---|
| `test_pool_qto.py` | 30 | Synthetic known answers |
| `test_s8_2_package.py` | 24 | The package |
| `test_s8_2_real_geometry.py` | 8 | Independent checks of the helpers on the drawing |
| `test_s8_2_post_freeze.py` | 9 | The post-freeze comparison |

- The builder was run twice and gave byte-identical output (19 files). `test_rebuild_is_byte_identical` repeats this
  under `python -I`.
- The post-freeze comparison was run twice and also gave identical output.

## Full suite

`python3 -m pytest -o addopts="" -q -p no:cacheprovider` on the clean committed tree `52fa35f`. No file was edited
during any run.

| Run | Passed | Failed | Errors | Skipped | xfailed | Time | Exit |
|---|---|---|---|---|---|---|---|
| 1, before PyMuPDF | 0 | 0 | 9 (collection) | 0 | 0 | 28 s | 2 |
| 2, before anthropic | 6655 | 345 | 35 | 138 | 100 | 300.7 s | 1 |
| 3, final environment | 6659 | 344 | 32 | 138 | 100 | 294.7 s | 1 |
| 4, final environment, with JUnit XML | **6659** | **344** | **32** | **138** | **100** | 285.1 s | 1 |

Notes on the runs:

- **Run 1** stopped at collection. All 9 errors were `No module named 'pymupdf'`.
- **Run 2:** 4 of its failures were the missing `anthropic` package; installing it made all 12 `test_base_models.py`
  tests pass.
- **Run 4** is the definitive record. Its JUnit XML attributes every non-passing test.

### Every non-passing test is missing private client data

All 376 tests that failed or errored in run 4 have the same kind of cause. None is unexplained.

| Missing file | Tests |
|---|---|
| `data/experiments/P7757_WALL_TREATMENT_ESTIMATE_01/...`: the private Qortuba, Al Rashed and villa working data | 373 |
| A workbook in the same `data/experiments` tree ("run workbook_boq first") | 1 |
| `data/runs/7757/reconciliation/P7757_GROUND_OPEN_ZONE_RECONCILIATION.json` | 1 |
| An xlsx uploaded in an earlier session, under `/root/.claude/uploads/...` | 1 |

The failing files are:

- the `test_pa08_qortuba_*` family;
- the `test_pa09_alrashed_*` family;
- the `test_pa09_villa_*` family;
- `test_benchmark_protection.py`.

These files are git-ignored client data and project working outputs. They existed only in the old container and were
not in the restore archive. The 21 freeze-named failures are all Qortuba, Al Rashed or villa freezes whose frozen
artifacts live in that absent tree. None of them changed.

The 134 extra skips (138 against 4) are tests that declare a data absence and skip by design: "golden data for 23010
is not mounted", "client data not present", "declared fixture not present", "run ... regression_r7 first", and so on.

### Alsenan and S8.2 status in run 4

| Suite | Result |
|---|---|
| S8.2 | 71 / 71 |
| S8.1A | 34 / 34 |
| S8.1 | 45 / 45 |
| S7 | 73 / 73 |
| Firewall / registry | 54 / 54 |
| R8.1 | 880 passed, 10 skipped |
| R8.8 | 71 passed, 7 skipped |

### Reconciliation with the baseline

At `763a00e` the suite gave 7098 passed, 4 skipped and 100 xfailed. That is 7202 cases; run 4 has 7273 = 7202 + 71
new S8.2 tests. The pass count closes exactly:

7098 + 71 = 7169 = 6659 passed + 376 data-absent failures and errors + 134 data-absent skips.

The suite returns to the baseline once the private `data/experiments/P7757_WALL_TREATMENT_ESTIMATE_01` and
`data/runs/7757` trees are restored.
