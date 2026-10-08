# D1.1 TEST_RUN: stirrup / link core-path authority audit

Baseline HEAD `59f2083`. D1.1 is an errata layer: S4, S5, S6, S4.1, S6.1 and S5.1 are unchanged, and all six freeze
manifests still match.

## Targeted

```
python3 -m pytest -q -p no:cacheprovider -o addopts="" tests/d1_1_stirrup_authority_audit tests/delta_release \
    tests/footing_rebar_s4_1 tests/superstructure_beam_rebar_s6_1 tests/ground_system_rebar_s5_1 \
    tests/structural_comparison_engine/test_rebar_product_firewall.py \
    tests/footing_rebar_s4/test_alsenan_s4_package.py::test_freeze_manifest_still_matches \
    tests/ground_system_rebar_s5/test_alsenan_s5_package.py::test_freeze_manifest_still_matches \
    tests/superstructure_beam_rebar_s6/test_alsenan_s6_package.py::test_freeze_manifest_still_matches \
    tests/source_recovery_delta
```

Result: **168 passed**. That is the 130 D1 tests plus 38 new D1.1 tests:
- 15 generic tests in `test_delta_correction.py`;
- 23 package tests in `test_d1_1_package.py`.

One D1 test was replaced. `tests/delta_release/test_link_geometry.py::test_core_path_stays_below_a_rounded_link_with_its_closing_hooks`
assumed a hook extension, which is the withdrawn premise. It is now
`::test_rounded_link_is_shorter_than_the_core_path_and_hooks_are_no_proof`.

The frozen S6.1 / S5.1 package tests still pass unchanged. They test what those frozen packages recorded. The
authority of the link rows recorded there is superseded by the D1.1 errata, not rewritten.

## Brief §11: where each required test lives

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
| S5.1 through-support unaffected | `::test_s5_1_through_support_release_unaffected` |
| frozen S5 / S6 / S5.1 / S6.1 immutability | `::test_frozen_s4_s5_s6_s4_1_s6_1_s5_1_are_immutable`, `::test_d1_1_freeze_manifest_still_matches`, plus the three frozen `test_freeze_manifest_still_matches` and the S4.1 / S6.1 / S5.1 freeze tests |
| correction conservation | `test_delta_correction.py::test_correction_conservation`, `test_d1_1_package.py::test_correction_conservation` |

Also tested:
- an erratum never adds steel, and the modelled / QA / reject states keep 0 kg;
- retained steel stays a LOWER_BOUND, and a full retraction is BLOCKED_UNQUANTIFIED;
- every correction states its reason and evidence;
- the normal delta rule is unchanged: `DR.record` still refuses a negative delta, and CORRECTION_ERRATA is not a delta change kind;
- every released S6.1 / S5.1 row is audited exactly once;
- the source search finds no bend radius, hook length or closure, and the links are drawn rounded;
- the rebuild is byte-identical, and the builder is blind and registered.

## Full suite

(recorded below after the run on the committed tree)
