# TEST_RUN: pre-S5 ground-system readiness

| Item | Value |
|---|---|
| Baseline | `6b2b41b` |
| Readiness commit | `a68a1ab` |

## Targeted runs

| Command | Result |
|---|---|
| `pytest tests/pre_s5_ground_system`: GB-MP-01..05 and GB-ARC-01..05, plus shared-face and node-at-split fixtures; package tests (INDEX, byte-identical rebuild from ST7757.dxf, V3 / R4 reproduction, change attribution, arc overlap, conservation, literal 5 m threshold L < 5 / = 5 / > 5, nested < 2.5 m, rows distinct, exterior depth, no kg, conflict release gate, strap lengths, F3 authority, S5 provenance contract, donor firewall) | 27 passed |
| `pytest tests/structural_comparison_engine` (RF.1 firewall: `ground_beam_network`, `ground_system_provenance` and `build_pre_s5` declared ACCURATE) | 54 passed |
| `pytest tests/footing_rebar_s4` (S4 freeze manifest still matches; S4 untouched) | 32 passed |
| `pytest tests/pre_s5_ground_system tests/footing_rebar_s4 tests/pre_s4_footing_readiness tests/structural_comparison_engine tests/alsenan_structural_census tests/column_rebar_engine tests/structural_review_engine tests/alsenan_rebar_truth tests/alsenan_rebar_source_exhaustion` | 423 passed, 4 xfailed |

The builder ran twice with byte-identical outputs (INDEX.json compared).

## Full suite

`python3 -m pytest -rs` on `a68a1ab`:

**6412 passed, 4 skipped, 100 xfailed, 0 failed, 0 errors (321.04 s).**

That is 6385 (S4) + 27 new tests.

The 4 skips are unchanged:
- `r8_4` real-source row (URBAN_R8_REAL_SOURCE unset);
- the R9.1 rebuild (needs the donor dataset);
- 2 × QS_MEASUREMENT_REGION_BUILDER placeholders.
