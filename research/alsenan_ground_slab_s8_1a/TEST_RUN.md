# S8.1A TEST_RUN: ground-slab population recovery and cover-authority audit

Baseline HEAD `12cabc3`. The round has three commits.

**`042e427`** is the package. It holds:

- the generic engine module `engine/source/region_recovery.py`, declared in the firewall registry;
- the builder `build_s8_1a.py`;
- the 14 outputs plus `14_S8_1A_FREEZE_MANIFEST.json`, in state `FROZEN_NO_QUANTITY_RELEASED` with
  `references_read: []`;
- `tests/ground_slab_s8_1a`: 14 synthetic known-answer tests and 20 package tests.

**`584180d`** declares the module's shapely import at the R8.1 K1 stdlib boundary (see "Full suite" below).

**The third commit** is this TEST_RUN record.

This round releases no steel or concrete, so it has no post-freeze comparison and opened no reference.

S8.1 is unchanged:

| Item | Value |
|---|---|
| Concrete | 3.785852 m3 |
| Total steel | 233.694587 kg |
| S8.1 files changed | none (the S8.1 manifest still verifies) |

All 15 frozen manifests read as inputs still match, S7 (3,802.015 kg) and S8.1 included.

## Targeted

```
python3 -m pytest -o addopts="" -p no:cacheprovider tests/ground_slab_s8_1a tests/ground_slab_s8_1 tests/structural_comparison_engine
python3 -m pytest -o addopts="" -p no:cacheprovider tests/r8_1/test_r8_1_boundaries.py tests/r8_8/test_r8_8_architecture.py tests/ground_slab_s8_1a tests/structural_comparison_engine
```

| Commit | Result | Breakdown |
|---|---|---|
| `042e427` | **133 passed** | 34 S8.1A + 45 S8.1 + 54 comparison-engine / firewall |
| `584180d` | **122 passed** | R8.1 boundaries + R8.8 architecture + 34 S8.1A + 54 comparison-engine / firewall |

Two earlier tests were edited:

- The firewall registry gained two lines.
- The K1 boundary test gained one declared module.

No assertion was weakened for any other module.

The builder was run twice and gave byte-identical output. `test_rebuild_is_byte_identical` repeats this under
`python -I`.

## Full suite

Both runs used `python3 -m pytest -o addopts="" -q -p no:cacheprovider` on a clean committed tree. No file was edited
during either run.

| Commit | Passed | Failed | Skipped | xfailed | Warnings | Time | Exit |
|---|---|---|---|---|---|---|---|
| `042e427` | 7097 | **1** | 4 | 100 | 2 | 385.25 s | 1 |
| `584180d` | **7098** | 0 | 4 | 100 | 2 | 373.81 s | 0 |

**The failure at `042e427`.** The failing test was `tests/r8_1/test_r8_1_boundaries.py::test_k1_is_stdlib_only_in_r8_1`, with:

```
AssertionError: ('engine/source/region_recovery.py', 'shapely.geometry')
```

`engine/source` modules must use only the standard library unless declared by design. The new module imports shapely
lazily through `_geom()`. `584180d` declares it the same way `ground_slab_recovery.py` and `topology_crosscheck.py`
are declared. `mesh_cover_fit()` stays stdlib, and the module computes no quantity.

**The run at `584180d`.**

- 7098 is the 7064 from S8.1 (`90986fa`) plus the 34 new S8.1A tests (14 synthetic, 20 package).
- The 2 warnings are the existing deprecation shims (`ratio_check`, `ratio_qa`).
- Every frozen-manifest test still matches: S4, S5, S6, S4.1, S6.1, S5.1, AD1, D1.1, D1.2, PRE-S7, PRE-S7.1, S7, S7A,
  PRE-S8 and S8.1.
