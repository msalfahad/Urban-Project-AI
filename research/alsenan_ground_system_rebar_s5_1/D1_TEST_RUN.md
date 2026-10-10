# D1_TEST_RUN: source-recovery delta releases S4.1 → S6.1 → S5.1

Freeze order:
- S4.1 at `9b45495`;
- S6.1 at `23a8dbf`, checking S4.1 first;
- S5.1 at `5f794b6`, checking S4.1 and S6.1 first.

Every builder hash-checks its frozen baseline before reading it. No S4, S5 or S6 file changed.

## Targeted

```
python3 -m pytest -q -p no:cacheprovider -o addopts="" tests/delta_release tests/footing_rebar_s4_1 \
    tests/superstructure_beam_rebar_s6_1 tests/ground_system_rebar_s5_1 \
    tests/structural_comparison_engine/test_rebar_product_firewall.py \
    tests/footing_rebar_s4/test_alsenan_s4_package.py::test_freeze_manifest_still_matches \
    tests/ground_system_rebar_s5/test_alsenan_s5_package.py::test_freeze_manifest_still_matches \
    tests/superstructure_beam_rebar_s6/test_alsenan_s6_package.py::test_freeze_manifest_still_matches \
    tests/source_recovery_delta
```

Result: **130 passed**.

## Brief §22: where each required test lives

| §22 item | Test |
|---|---|
| graphic classes | `tests/delta_release/test_graphic_evidence_and_delta_release.py::test_four_graphic_classes_and_their_quantity_rule`, `::test_rule_b_needs_every_condition` |
| NTS cannot create measured length | `::test_nts_or_plotted_scale_never_creates_a_measured_length`, `::test_only_dimensioned_or_fully_derived_portions_carry_length` |
| shape-found / length-blocked | `::test_shape_found_length_blocked` |
| footing U-bar decomposition | `tests/footing_rebar_s4_1/test_alsenan_s4_1_package.py::test_footing_u_bar_decomposition`, `::test_upturn_leg_derivation_was_attempted_and_fails_on_the_endpoint` |
| 45° hook without length | `::test_45_degree_hook_found_without_length` |
| BOXED shape found / count blocked | `::test_boxed_shape_found_count_blocked` |
| FF ownership transfer | `::test_ff_wall_base_bars_transfer_to_s8` |
| STR2 topology | `tests/superstructure_beam_rebar_s6_1/test_alsenan_s6_1_package.py::test_str2_topology_four_legs_outer_link_only`, `tests/delta_release/test_link_geometry.py::test_single_str2_str3_topologies` |
| STR3 topology | `::test_str3_topology_six_legs`, `test_link_geometry.py::test_single_str2_str3_topologies` |
| inner link unresolved | `::test_inner_link_stays_unresolved` |
| single-link core lower bound | `::test_single_link_core_path_lower_bound`, `::test_core_path_released_only_with_a_released_count`, `test_link_geometry.py::test_core_path_is_the_sharp_centreline_rectangle` |
| CB downward end leg | `::test_cb_downward_end_leg_recorded_not_released`, `test_link_geometry.py::test_cb_end_leg_reaches_the_bottom_bar_level` |
| B3 base release | `::test_b3_with_stair_base_release` |
| B26 base vs extra | `::test_b26_base_vs_planted_column_extra` |
| CB7 invariant stirrup | `::test_cb7_invariant_stirrup_count`, `test_link_geometry.py::test_invariant_requires_every_interpretation_to_agree` |
| GB two-leg link | `tests/ground_system_rebar_s5_1/test_alsenan_s5_1_package.py::test_gb_two_leg_link_core_path` |
| <2.5 m link rate blocked | `::test_lt_2_5m_link_rate_blocked_and_follow_arch_blocked` |
| through-support continuous run | `::test_through_support_continuous_run`, `::test_end_supports_stay_unresolved` |
| SB1 / SB3 STR2 | `::test_sb1_sb3_str2_outer_link_only_sb2_untouched` |
| frozen baseline immutability | `test_frozen_s4_baseline_is_immutable`, `test_frozen_s6_baseline_is_immutable_and_s4_1_preceded`, `test_frozen_s5_baseline_is_immutable_and_order_kept`, `test_delta_release...::test_verify_frozen_detects_an_edited_baseline`, plus the three frozen `test_freeze_manifest_still_matches` |
| delta conservation | `test_delta_conservation` in each package, `test_delta_release...::test_delta_conservation`, `::test_delta_never_subtracts_and_never_creates_verified` |

## Full suite

`python3 -m pytest -o addopts="" -q -p no:cacheprovider` at `5f794b6` gave
**6698 passed, 4 skipped, 100 xfailed, 2 warnings in 405.89 s, exit 0**.
- That is the 6621 from the source-recovery round plus 77 new D1 tests.
- The run used the clean committed tree. No file was edited during it.
- The S4, S5 and S6 frozen-manifest tests and the three new S4.1 / S6.1 / S5.1 freeze tests all still match.
