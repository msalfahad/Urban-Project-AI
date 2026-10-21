# S7 TEST_RUN: restricted elevated slab rebar QTO (project-basis release)

Baseline HEAD `ac7a477`. The round has three commits:

1. Freeze commit `16741ec`. It holds the generic engine `engine/source/slab_rebar_qto.py`, the builder, the 12 outputs,
   `12_S7_FREEZE_MANIFEST.json`, the generic and package tests, and the firewall-registry entries. Nothing was read
   from any reference before it.
2. Post-freeze commit `4c83383`. It adds `post_freeze/`: the comparison script (registered as a COMPARISON module), its
   six outputs and the post-freeze tests.
3. This TEST_RUN record.

Frozen stages S4 ... D1.2, PRE-S7 and PRE-S7.1 are unchanged, and all eleven freeze manifests still match. The S7
builder was run repeatedly and is byte-identical (`test_rebuild_is_byte_identical`). The post-freeze comparison was
also run twice, with identical output.

## Targeted

```
python3 -m pytest -q -p no:cacheprovider -o addopts="" tests/slab_rebar_s7 tests/slab_rebar_pre_s7_1 \
    tests/slab_rebar_pre_s7 tests/d1_2_footing_cover_audit tests/ad1_authority_decisions \
    tests/d1_1_stirrup_authority_audit tests/delta_release tests/footing_rebar_s4_1 \
    tests/superstructure_beam_rebar_s6_1 tests/ground_system_rebar_s5_1 \
    tests/structural_comparison_engine/test_rebar_product_firewall.py \
    tests/footing_rebar_s4/test_alsenan_s4_package.py::test_freeze_manifest_still_matches \
    tests/ground_system_rebar_s5/test_alsenan_s5_package.py::test_freeze_manifest_still_matches \
    tests/superstructure_beam_rebar_s6/test_alsenan_s6_package.py::test_freeze_manifest_still_matches \
    tests/source_recovery_delta
```

Result: **410 passed**. That is the 337 from PRE-S7.1 plus 73 S7 tests:

- 22 generic tests in `tests/slab_rebar_s7/test_slab_rebar_qto.py`, using synthetic inputs only;
- 44 package tests in `tests/slab_rebar_s7/test_s7_package.py`;
- 7 post-freeze tests in `tests/slab_rebar_s7/test_s7_post_freeze.py`.

No earlier test was changed.

## Brief §31: where each required test lives

| §31 item | test(s) |
|---|---|
| rate x rectangle integration | `test_rate_times_rectangle_integration`, `test_rate_times_rectangle_on_rectangular_panels` |
| rate x trapezoid strip integration | `test_rate_times_trapezoid_strip_integration`, `test_strip_integration_reconciles_to_panel_geometry` |
| rate x L-shape strip integration | `test_rate_times_l_shape_strip_integration` |
| no integer rounding | `test_no_integer_rounding_of_the_equivalent_count`, `test_no_integer_rounding_and_no_plus_one` |
| no +1 | `test_no_plus_one`, `test_no_integer_rounding_and_no_plus_one` |
| 50/50 density | `test_fifty_fifty_density`, `test_fifty_plus_fifty_is_one_hundred` |
| 0.125L candidate usage | `test_curtailed_runs_use_the_frozen_0125L`, `test_curtailment_authority_is_split` |
| 1/3 project-source ratio | `test_one_third_ratio_is_project_source`, `test_one_third_is_project_source_and_the_face_origin_is_urban` |
| support-face Urban measurement convention | `test_support_face_measurement_convention_is_urban_where_the_source_is_silent` (same package test) |
| local /Top override | `test_local_top_override_needs_count_and_length_authority`, `test_local_top_override_carries_no_kg_and_no_general_bar` |
| same-role generic rule not double counted | `test_same_role_generic_rule_not_double_counted`, `test_same_role_generic_rule_never_added`, `test_top_steel_is_owned_by_the_support` |
| mismatch left/right split | `test_mismatch_left_right_runs_do_not_overlap`, `test_mismatch_supports_split_left_right` |
| no hidden lap | `test_no_hidden_lap_is_a_quantity`, `test_no_hidden_lap` |
| minimum 25 mm cover authority | `test_minimum_25mm_cover_is_project_basis_numeric`, `test_minimum_25mm_cover_and_40cl_never_used` |
| temperature excluded | `test_temperature_and_blocked_items_carry_no_kg`, `test_temperature_excluded` |
| sunken base mesh included / sunken extras blocked | `test_sunken_base_mesh_included_and_extras_blocked` |
| water tank excluded / GF-21 excluded | `test_water_tank_and_gf21_excluded` |
| opening clipping | `test_opening_clipping_uses_the_net_geometry`, `test_opening_clipping_and_trim_blocked` |
| oblique blocker / edge blocker | `test_oblique_and_edge_blockers` |
| candidate-only release | `test_candidate_only_release`, `test_every_pre_s7_1_item_terminates_once` |
| diameter / floor / project reconciliation | `test_diameter_reconciliation`, `test_floor_reconciliation`, `test_project_reconciliation`, `test_reconciliation_by_diameter_floor_and_project`, `test_bar_runs_reconcile_to_items` |
| freeze-before-reference guarantee | `test_freeze_manifest_still_matches`, `test_builder_is_blind`, `test_freeze_before_reference_guarantee` (git: the manifest committed at `16741ec` is this one, and that commit holds no post-freeze file), `test_post_freeze_comparison_is_downstream_only` |

The package tests also re-derive the following from the frozen inputs, never from a reference total:

- every PRE-S7.1 item terminates exactly once;
- the component lanes;
- strip overlap per floor, direction and layer (NO_SUPPORT_TOP_BAR_DOUBLE_COUNT);
- each bottom family covering its S1 panel area exactly once (`in_panel + 2 x continuing = rate x area`);
- explicit counts carrying no kg;
- the authority corrections S7-AC01 and S7-AC02.

## Full suite

`python3 -m pytest -o addopts="" -q -p no:cacheprovider` at `4c83383` gave
**6978 passed, 4 skipped, 100 xfailed, 2 warnings in 420.99 s, exit 0**.

- That is the 6905 from PRE-S7.1 plus the 73 S7 tests.
- The run used the clean committed tree. No file was edited during it, and the tree was still clean afterwards.
- The 2 warnings are the existing deprecation shims (`ratio_check`, `ratio_qa`).
- Every frozen-manifest test still matches: S4, S5, S6, S4.1, S6.1, S5.1, AD1, D1.1, D1.2, PRE-S7, PRE-S7.1 and S7.
