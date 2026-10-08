# D1.1 TEST_RUN: AD1 authority decisions, then the stirrup / link core-path audit (revision 2)

Baseline HEAD `59f2083`. D1.1 is an errata layer: S4, S5, S6, S4.1, S6.1 and S5.1 are unchanged, and all six freeze
manifests still match.

Order of the rounds:
1. **D1.1 revision 1** at `35567e2`. Its test record is at `cbcbb36`.
2. **AD1**: the owner authority decisions are recorded and frozen in `research/ad1_authority_decisions/`.
3. **D1.1 revision 2** is rebuilt on top of AD1. AD1's manifest is verified first, together with the six stage
   manifests.

## Targeted

```
python3 -m pytest -q -p no:cacheprovider -o addopts="" tests/ad1_authority_decisions \
    tests/d1_1_stirrup_authority_audit tests/delta_release \
    tests/footing_rebar_s4_1 tests/superstructure_beam_rebar_s6_1 tests/ground_system_rebar_s5_1 \
    tests/structural_comparison_engine/test_rebar_product_firewall.py \
    tests/footing_rebar_s4/test_alsenan_s4_package.py::test_freeze_manifest_still_matches \
    tests/ground_system_rebar_s5/test_alsenan_s5_package.py::test_freeze_manifest_still_matches \
    tests/superstructure_beam_rebar_s6/test_alsenan_s6_package.py::test_freeze_manifest_still_matches \
    tests/source_recovery_delta
```

Result: **199 passed**. That is the 130 D1 tests plus:
- 38 D1.1 tests:
  - 15 generic tests in `test_delta_correction.py`;
  - 23 package tests in `test_d1_1_package.py`, updated for revision 2;
- 31 AD1 tests:
  - 14 generic tests in `tests/ad1_authority_decisions/test_authority_decisions.py`;
  - 17 package tests in `test_ad1_package.py`.

One D1 test was replaced. `tests/delta_release/test_link_geometry.py::test_core_path_stays_below_a_rounded_link_with_its_closing_hooks`
assumed a hook extension, which is the withdrawn premise. It is now
`::test_rounded_link_is_shorter_than_the_core_path_and_hooks_are_no_proof`.

The frozen S6.1 / S5.1 package tests still pass unchanged. They test what those frozen packages recorded. Their
authority is superseded by the D1.1 and AD1 errata, not rewritten.

## D1.1 brief §11: where each required test lives

All paths are under `tests/d1_1_stirrup_authority_audit/`.

| §11 item | Test |
|---|---|
| sharp rectangular perimeter | `test_delta_correction.py::test_sharp_rectangular_perimeter` |
| rounded 90° corner | `::test_rounded_90_degree_corner` (a square bent at R = W/2 is a circle, 100 pi) |
| rounded loop < sharp loop for R > 0 | `::test_rounded_loop_is_shorter_than_the_sharp_loop_for_every_positive_radius`, `tests/delta_release/test_link_geometry.py::test_rounded_link_is_shorter_than_the_core_path_and_hooks_are_no_proof` |
| unknown R | `::test_unknown_bend_radius_gives_no_loop_and_no_lower_bound` |
| unknown hook length | `::test_unknown_hook_length_never_promotes_the_sharp_path`, `::test_lower_bound_needs_an_exact_envelope_and_a_source_derived_length_needs_everything` |
| known topology / unknown cut length | `::test_known_topology_with_unknown_cut_length`, `test_d1_1_package.py::test_register_keeps_four_facts_separate` |
| known count / unknown mass | `::test_known_count_with_unknown_mass`, `test_d1_1_package.py::test_known_count_and_diameter_with_unknown_mass` |
| STR2 topology survives the mass block | `test_d1_1_package.py::test_str2_topology_survives_the_mass_block` |
| STR3 topology survives the mass block | `::test_str3_topology_survives_the_mass_block` |
| S6.1 longitudinal releases unaffected | `::test_s6_1_longitudinal_and_planted_releases_unaffected`, `::test_cb7_and_other_stirrup_counts_retained` |
| S5.1 through-support unaffected | `::test_s5_1_through_support_release_unaffected`, `tests/ad1_authority_decisions/test_ad1_package.py::test_s5_1_through_support_and_link_releases_untouched` |
| frozen S5 / S6 / S5.1 / S6.1 immutability | `::test_frozen_s4_s5_s6_s4_1_s6_1_s5_1_and_ad1_are_immutable`, `::test_d1_1_freeze_manifest_still_matches`, `test_ad1_package.py::test_frozen_stages_are_immutable`, plus the three frozen `test_freeze_manifest_still_matches` and the S4.1 / S6.1 / S5.1 freeze tests |
| correction conservation | `test_delta_correction.py::test_correction_conservation`, `test_d1_1_package.py::test_correction_conservation` (link and AD-6 errata), `test_ad1_package.py::test_conservation_and_flags` |

## Authority decisions: where each one is tested

All paths are under `tests/ad1_authority_decisions/`.

| Decision | Test |
|---|---|
| Q2 analysis not promoted, no confidence carried | `test_ad1_package.py::test_q2_analysis_is_not_promoted_and_carries_no_confidence`, `::test_only_the_workflow_engineer_claim_is_on_record`, `test_authority_decisions.py::test_analysis_and_code_values_are_never_promoted`, `::test_no_confidence_value_travels_with_a_ruling` |
| AD-1 BOXED | `test_ad1_package.py::test_boxed_state_errata` |
| AD-2 70Ø / 40Ø | compliance rows AD1-K05 / K06, checked in the builder (rule scope, no anchorage kg) |
| AD-3 end bends | `::test_cb_end_legs_lose_their_depth_derived_length` |
| AD-4 stirrup hooks | `test_d1_1_package.py::test_register_keeps_four_facts_separate` (hook extension blocked on all 180 sets) |
| AD-5 GB < 2.5 m | builder checks in AD1 and D1.1 (no inherited diameter); compliance row AD1-K13 |
| AD-6 concentrated reaction | `test_authority_decisions.py::test_a_beam_framing_in_between_supports_is_an_engineering_derived_reaction`, `::test_support_junctions_symbols_and_drawn_loads_are_not_reclassified`, `::test_loaded_candidates_are_taken_per_length_basis`, `test_ad1_package.py::test_ground_beam_reactions_are_engineering_derived`, `::test_loaded_candidates_rederived_from_the_length_basis`, `::test_kg_retracted_exactly_on_the_two_loaded_spans` |
| AD-7 FOLLOW ARCH | compliance row AD1-K18 (builder checks: no depth published, no lower bound) |
| AD-8 continuous beams | compliance rows AD1-K19 to K21; `test_d1_1_package.py::test_topology_register_summary` (counts are rate x run only) |
| AD-9 side bars | `test_ad1_package.py::test_side_bars_classified_only_from_the_middle_reinf_field` |
| all decisions recorded and checked | `::test_nine_owner_decisions_with_their_rulings`, `::test_compliance_register_covers_every_decision` |

## Full suite

(recorded below after the run on the committed tree)
