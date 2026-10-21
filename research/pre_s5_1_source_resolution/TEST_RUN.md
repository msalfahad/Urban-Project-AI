# TEST_RUN: PRE-S5.1 ground-system source resolution

| Item | Value |
|---|---|
| Baseline | `0a23c06` |
| Round commit | `24d66f4` |

## Targeted runs

| Command | Result |
|---|---|
| `pytest tests/pre_s5_1_source_resolution` (generic provenance identity, fake footing identity rejected, S4 equivalence 84 x 10, support face-to-face run, oblique bar line, length conflict, unresolved run, arch exterior overlay, partial wall overlap, exterior vs interior wall, authority without proxy vote, FOLLOW ARCH derivation, dual length basis, concentrated-load unknown, overlapping-detail precedence, free-end order; package: INDEX, byte-identical rebuild from ST7757 + P7757, overlay coverage, 19 disagreements, depth bounded only, no old minimum, SB2 candidate-invariant, free-end conservation, release gates, generic templates, donor firewall) | 35 passed |
| `pytest tests/pre_s5_ground_system` (package rebuilt with the generic identity; no status change) | 27 passed |
| `pytest tests/structural_comparison_engine` (RF.1 firewall: `rebar_provenance`, `ground_system_resolution`, `build_pre_s5_1` declared ACCURATE) | 54 passed |
| `pytest tests/footing_rebar_s4` (S4 freeze manifest still matches) | 32 passed |
| `pytest tests/pre_s4_footing_readiness` (S4 provenance contract unchanged) | 125 passed |

The PRE-S5.1 builder ran twice with byte-identical outputs (INDEX.json compared).

## Full suite

`python3 -m pytest -o addopts="" -q -rs` on `24d66f4`:

**6447 passed, 4 skipped, 100 xfailed, 0 failed, 0 errors (309.64 s).**

That is 6412 (pre-S5) + 35 new.

The 4 skips are unchanged:
- `r8_4` real-source row (URBAN_R8_REAL_SOURCE unset);
- R9.1 rebuild (needs the donor dataset);
- 2 x QS_MEASUREMENT_REGION_BUILDER placeholders.
