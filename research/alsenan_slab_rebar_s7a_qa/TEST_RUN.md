# S7A TEST_RUN: S7 engineering QA (dated sensitivity layer, no release)

Baseline HEAD `aeb8798`. The package was committed at `7e1ebe8`, together with the PRE-S8 census. That commit holds:

- the builder `build_s7a_qa.py`;
- the 11 outputs plus `11_S7A_FREEZE_MANIFEST.json` (state `FROZEN_QA_LAYER_NO_RELEASE`);
- `tests/s7a_qa` (18 tests);
- the firewall-registry entry.

`76f97da` corrects PRE-S8 only. S7A is not changed by it.

S7 is unchanged: its builder, outputs, engine and manifest are untouched, and its total is still **3,802.015 kg**. Every
scenario (A, B, C, D1, D2, E) is a sensitivity reading. None is released and none replaces reading A. All frozen
manifests still match: S4, S5, S6, S4.1, S5.1, S6.1, AD1, D1.1, D1.2, PRE-S7, PRE-S7.1 and S7.

## Targeted

```
python3 -m pytest -q -p no:cacheprovider -o addopts="" tests/s7a_qa tests/pre_s8_census \
    tests/structural_comparison_engine/test_rebar_product_firewall.py tests/slab_rebar_s7
```

| Commit | Result | Breakdown |
|---|---|---|
| `7e1ebe8` | **140 passed** | 18 S7A + 19 PRE-S8 + 30 firewall + 73 S7 |
| `76f97da` | **144 passed** | 4 more PRE-S8 regression tests |

No earlier test was changed. The builder was run twice and gave byte-identical output (`test_rebuild_is_byte_identical`).

## Full suite

Every full-suite run used `python3 -m pytest -o addopts="" -q -p no:cacheprovider` on a clean committed tree. No file was edited during either run.

| Commit | Passed | Skipped | xfailed | Warnings | Time | Exit |
|---|---|---|---|---|---|---|
| `7e1ebe8` | 7015 | 4 | 100 | 2 | 405.19 s | 0 |
| `76f97da` | **7019** | 4 | 100 | 2 | 380.41 s | 0 |

- `7e1ebe8` gave 7015: the 6978 from S7 plus the 37 new tests.
- `76f97da` gave 7019: 7015 plus the 4 regression tests.
- The 2 warnings are the existing deprecation shims (`ratio_check`, `ratio_qa`).
- Every frozen-manifest test still matches: S4, S5, S6, S4.1, S6.1, S5.1, AD1, D1.1, D1.2, PRE-S7, PRE-S7.1, S7, S7A and PRE-S8.
