# PRE-S8 TEST_RUN: structural completeness census (analysis only, no kg)

Baseline HEAD `aeb8798`. The round has three commits.

**`7e1ebe8`** holds:

- the builder `build_pre_s8.py`;
- the 13 outputs plus `13_PRE_S8_FREEZE_MANIFEST.json` (state `FROZEN_ANALYSIS_NO_KG`);
- `tests/pre_s8_census` (19 tests);
- the firewall-registry entry.

**`76f97da`** holds the corrections from a self-review of `7e1ebe8`. It still calculates no kg and moves no frozen stage.

1. **Current component states.** Footing, ground-beam and beam component states had come from the pre-delta S4, S5 and
   S6 registers. They now come from the S4.1, S5.1 and S6.1 delta rows. The AD1, D1.1 and D1.2 errata are then
   applied by `ORIGINAL_DELTA_ID`, so the 88 D1.1 stirrup core paths now read as blocked. The 60 D1.2 footing runs now
   read as `PROJECT_BASIS`. The seven delta and errata files are inputs, and each is hash-checked against its own
   freeze manifest.
2. **Rebar matrix (04).** It had parked `STATE:n` tallies and S7 face records under `OWNED_ELSEWHERE_OR_OTHER`, 46
   rows of them. Each component is now graded by its own state, and an element is counted once per component.
3. **Missing-component register (09).** The beam, ground-beam and strap blockers were missing. The register now holds
   81 kinds, up from 35.
4. **Concrete matrix (03).** It had counted the 36 slab faces as elements, giving 436 against 400. Faces now have
   their own column.

The four regression tests are:

- `test_concrete_matrix_counts_elements_and_faces_apart`;
- `test_rebar_components_are_the_latest_dated_layer_never_the_pre_delta_state`, which recomposes the layers
  independently from the frozen files;
- `test_rebar_matrix_grades_every_component_by_its_state`;
- `test_missing_register_holds_the_beam_and_ground_beam_blockers`.

**The third commit** is this TEST_RUN record.

All 13 frozen manifests read as inputs still match, S7A included. The stage totals are unchanged:

| Stage | kg |
|---|---|
| S3.1 | 7,488.205 |
| S4.1 (+D1.2) | 3,629.600 |
| S5.1 (+AD1, D1.1) | 1,436.232 |
| S6.1 (+D1.1) | 4,014.765 |
| S7 | 3,802.015 |

## Targeted

```
python3 -m pytest -q -p no:cacheprovider -o addopts="" tests/s7a_qa tests/pre_s8_census \
    tests/structural_comparison_engine/test_rebar_product_firewall.py tests/slab_rebar_s7
```

| Commit | Result | Breakdown |
|---|---|---|
| `7e1ebe8` | **140 passed** | 18 S7A + 19 PRE-S8 + 30 firewall + 73 S7 |
| `76f97da` | **144 passed** | 18 S7A + 23 PRE-S8 + 30 firewall + 73 S7 |

No test from before this round was changed. One PRE-S8 assertion added in this round now follows the corrected owner
wording: `test_dome_ring_arcs_need_an_ownership_transfer` expects "S6.1 (S6 occurrence BLOCKED_TYPE".

The builder was run twice at `76f97da` and gave byte-identical output (`test_rebuild_is_byte_identical`).

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
