# D1.2 TEST_RUN: S4 footing cover / bar-length authority audit

Baseline HEAD `1384bf3`. D1.2 is a state-correction layer (S4_1A) over frozen S4.1. S4, S4.1, S5, S6, S5.1, S6.1,
AD1 and D1.1 are unchanged, and all eight freeze manifests still match.

The builder was run twice and the second run was byte-identical (`test_rebuild_is_byte_identical` repeats this).

## Targeted

```
python3 -m pytest -q -p no:cacheprovider -o addopts="" tests/d1_2_footing_cover_audit tests/ad1_authority_decisions \
    tests/d1_1_stirrup_authority_audit tests/delta_release \
    tests/footing_rebar_s4_1 tests/superstructure_beam_rebar_s6_1 tests/ground_system_rebar_s5_1 \
    tests/structural_comparison_engine/test_rebar_product_firewall.py \
    tests/footing_rebar_s4/test_alsenan_s4_package.py::test_freeze_manifest_still_matches \
    tests/ground_system_rebar_s5/test_alsenan_s5_package.py::test_freeze_manifest_still_matches \
    tests/superstructure_beam_rebar_s6/test_alsenan_s6_package.py::test_freeze_manifest_still_matches \
    tests/source_recovery_delta
```

Result: **233 passed**. That is the 199 from AD1 / D1.1 revision 2, plus 34 D1.2 tests:
- 16 generic tests in `tests/d1_2_footing_cover_audit/test_cover_authority.py`;
- 18 package tests in `tests/d1_2_footing_cover_audit/test_d1_2_package.py`.

No earlier test was changed.

## D1.2 brief §8: where each required test lives

All paths are under `tests/d1_2_footing_cover_audit/`.

| §8 item | Test |
|---|---|
| exact cover | `test_cover_authority.py::test_exact_cover`, `::test_a_detail_dimension_or_derived_cover_outranks_the_minimum_rule` |
| minimum cover | `::test_minimum_cover`, `test_d1_2_package.py::test_the_70_mm_rule_is_a_minimum`, `::test_cover_basis_is_minimum_project_cover_70` |
| greater-than-minimum cover | `test_cover_authority.py::test_greater_than_minimum_cover_shortens_the_straight_run`, `test_d1_2_package.py::test_straight_run_is_span_minus_140_and_a_maximum` |
| unknown actual cover | `test_cover_authority.py::test_unknown_actual_cover_gives_no_length`, `::test_bounded_cover` |
| bar-length monotonicity versus cover | `::test_bar_length_is_strictly_decreasing_in_cover`, `::test_rate_count_is_non_increasing_in_cover_and_the_edge_bar_pulls_the_other_way` |
| minimum cover produces the maximum straight length | `::test_minimum_cover_produces_the_maximum_straight_length`, `test_d1_2_package.py::test_straight_run_is_span_minus_140_and_a_maximum` |
| no silent lower-bound classification | `test_cover_authority.py::test_no_silent_lower_bound_classification`, `::test_a_minimum_cover_straight_bar_with_unquantified_ends_is_no_bound`, `test_d1_2_package.py::test_every_part_moves_to_project_basis_numeric_and_none_stays_a_lower_bound` |
| S4 / S4.1 frozen-manifest integrity | `test_d1_2_package.py::test_frozen_s4_s4_1_and_other_stages_are_immutable`, `::test_d1_2_freeze_manifest_still_matches`, plus the S4 / S5 / S6 `test_freeze_manifest_still_matches` and the S4.1 package tests |
| correction conservation | `test_cover_authority.py::test_correction_conservation`, `::test_a_correction_never_adds_steel_and_always_changes_something`, `test_d1_2_package.py::test_correction_conservation`, `::test_kg_is_rederived_and_unchanged` |

The package tests re-derive each part from the frozen S4 provenance and the S4.1 delta rows:
- the straight run is span - 140;
- the rate count is ceil(rate x (W - 140));
- the kg is n x (span - 140) x d² / 162.

None of them is checked against a reference total.

## Full suite

`python3 -m pytest -o addopts="" -q -p no:cacheprovider` at `d0d2ad9` gave
**6801 passed, 4 skipped, 100 xfailed, 2 warnings in 432.95 s, exit 0**.
- That is the 6767 from AD1 / D1.1 revision 2 plus the 34 D1.2 tests.
- The run used the clean committed tree. No file was edited during it, and the tree was still clean afterwards.
- Every frozen-manifest test still matches: S4, S5, S6, S4.1, S6.1, S5.1, AD1, D1.1 and D1.2.
