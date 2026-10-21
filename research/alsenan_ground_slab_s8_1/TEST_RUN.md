# S8.1 TEST_RUN: ground slab, two source-zoned cells

Baseline HEAD `73f62c3`. The round has three commits.

**`201f441`** is the freeze. It holds:

- the generic engine module `engine/source/ground_slab_qto.py`;
- the builder `build_s8_1.py`;
- the 12 outputs plus `11_S8_1_FREEZE_MANIFEST.json`, in state `FROZEN_BEFORE_COMPARISON` with `references_read: []`;
- `tests/ground_slab_s8_1`: 16 synthetic known-answer tests and 18 package tests;
- the firewall-registry entries (one accurate module, one accurate builder).

No earlier figure had been opened when this commit was made.

**`90986fa`** holds the post-freeze comparison:

- `post_freeze/post_freeze_comparison.py`, registered as a comparison module;
- its 7 outputs;
- 11 post-freeze tests.

The script checks three things before it opens any reference:

- the frozen hashes still match;
- the manifest is the one committed at `201f441`;
- that commit holds no post-freeze file.

It writes nothing in the S8.1 package. Two runs gave byte-identical outputs.

**The third commit** is this TEST_RUN record.

The frozen S8.1 result is unchanged by the comparison:

| Item | Value |
|---|---|
| Zones quantified | 2 (SP-GBP-08 / marker 1690, SP-GBP-14 / marker 169D) |
| Net zone area | 37.858523 m2 |
| Concrete | 3.785852 m3 |
| X mesh | 189.292616 m, 116.847294 kg |
| Y mesh | 189.292616 m, 116.847294 kg |
| Total steel | 233.694587 kg |
| Blocked faces | 19 (129.770584 m2) |
| Blocked records | 56 (54 BLOCKED_UNQUANTIFIED + 2 SOURCE_CONFLICT) |

All 14 frozen manifests read as inputs still match, S7 (3,802.015 kg) included.

## Targeted

```
python3 -m pytest -p no:cacheprovider tests/ground_slab_s8_1 tests/structural_comparison_engine
python3 -m pytest -p no:cacheprovider tests/structural_comparison_engine tests/pre_s8_census tests/slab_rebar_s7
```

| Commit | Result | Breakdown |
|---|---|---|
| `201f441` | **88 passed** | 34 S8.1 + 54 comparison-engine / firewall |
| `90986fa` | **45 passed** | 34 S8.1 + 11 post-freeze |
| `90986fa` | **150 passed** | comparison-engine / firewall + PRE-S8 + S7 |

No test from before this round was changed.

The builder was run twice at `201f441` and gave byte-identical output (`test_rebuild_is_byte_identical`).

## Full suite

The run used `python3 -m pytest -o addopts="" -q -p no:cacheprovider` on a clean committed tree. No file was edited
during the run.

| Commit | Passed | Skipped | xfailed | Warnings | Time | Exit |
|---|---|---|---|---|---|---|
| `90986fa` | **7064** | 4 | 100 | 2 | 385.12 s | 0 |

- 7064 is the 7019 from PRE-S8 (`76f97da`) plus the 45 new S8.1 tests (16 synthetic, 18 package, 11 post-freeze).
- The 2 warnings are the existing deprecation shims (`ratio_check`, `ratio_qa`).
- Every frozen-manifest test still matches: S4, S5, S6, S4.1, S6.1, S5.1, AD1, D1.1, D1.2, PRE-S7, PRE-S7.1, S7, S7A,
  PRE-S8 and S8.1.
