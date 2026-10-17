# TEST_RUN: S4 accurate footing rebar

| Item | Value |
|---|---|
| Baseline | `e3633af` |
| S4 freeze commit | `50c546b` |
| Post-freeze comparison commit | `e2f2fe8` |

## Targeted runs

| Command | Result |
|---|---|
| `pytest tests/footing_rebar_s4`: 20 generic engine tests (covering the 24 required behaviours) + 12 package tests (freeze manifest, builder blindness, byte-identical rebuild, F3, four golden examples, blind invariants, summary / conservation, provenance, post-freeze record) | 32 passed |
| `pytest tests/pre_s4_footing_readiness` | 125 passed |
| `pytest tests/structural_comparison_engine` (RF.1 rebar product firewall: `footing_rebar.py`, `footing_rebar_guard.py` and the S4 builder declared ACCURATE; the post-freeze script declared COMPARISON) | 54 passed |
| `pytest tests/footing_rebar_s4 tests/pre_s4_footing_readiness tests/structural_comparison_engine tests/alsenan_structural_census tests/column_rebar_engine tests/structural_review_engine tests/alsenan_rebar_truth tests/alsenan_rebar_source_exhaustion` | 396 passed, 4 xfailed |

**Post-freeze comparison:**
- The script re-ran twice, giving byte-identical outputs.
- It refuses to run unless `S4_FREEZE_MANIFEST.json` re-verifies.
- `test_freeze_manifest_still_matches` passes on the committed tree.

## Full suite

`python3 -m pytest -rs` on the tree at `e2f2fe8`:

**6385 passed, 4 skipped, 100 xfailed, 0 failed, 0 errors (307.65 s).**

That is 6353 (pre-S4) + 32 new S4 tests.

The 4 skips are the same as before this round:
- `r8_4` real-source row (URBAN_R8_REAL_SOURCE unset);
- the R9.1 rebuild (needs the Chris dataset);
- 2 × QS_MEASUREMENT_REGION_BUILDER placeholders.

The frozen S4 outputs are unchanged after the full run: `test_freeze_manifest_still_matches` passed, and `git status` shows no frozen output modified.
