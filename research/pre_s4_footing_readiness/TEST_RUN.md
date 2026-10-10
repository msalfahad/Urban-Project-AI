# TEST_RUN: pre-S4 hardening

Baseline `445dd1d`.

## Targeted runs

| Command | Result |
|---|---|
| `pytest tests/pre_s4_footing_readiness` (fixtures FT-01…06, RB-01…03, provenance contract, stamps, package incl. byte-for-byte rebuild from ST7757.dxf) | 125 passed |
| `pytest tests/structural_comparison_engine/test_rebar_product_firewall.py` (guard declared ACCURATE; closure checks) | passed |
| `pytest tests/alsenan_rebar_source_exhaustion tests/alsenan_rebar_truth tests/alsenan_structural_census tests/column_rebar_engine tests/coverage_recovery_engine tests/r9_1_chris_post_freeze tests/structural_comparison_engine tests/structural_review_engine tests/pre_s4_footing_readiness` | 416 passed, 1 skipped (R9.1 rebuild needs the Chris dataset), 4 xfailed |

## Full suite

`python3 -m pytest -rs` from the tree built on `445dd1d`, with every change of this round present:

**6353 passed, 4 skipped, 100 xfailed, 0 failed, 0 errors (308 s).**

The 4 skips were already skipped before this round:
- `r8_4` real-source row (URBAN_R8_REAL_SOURCE unset);
- the R9.1 rebuild (needs the Chris dataset);
- 2 × QS_MEASUREMENT_REGION_BUILDER placeholders.
