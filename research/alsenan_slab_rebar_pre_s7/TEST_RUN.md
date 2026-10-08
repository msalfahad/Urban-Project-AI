# PRE-S7 TEST_RUN: elevated slab rebar readiness / source exhaustion

Baseline HEAD `44f693e`. PRE-S7 is a readiness package only:
- no slab reinforcement kg is calculated or published;
- S7 is not started;
- S4, S4.1, S5, S6, S5.1, S6.1, AD1, D1.1 and D1.2 are unchanged, and all nine freeze manifests still match.

The builder was run twice and the second run was byte-identical (`test_rebuild_is_byte_identical` repeats this).
`PRE_S7_FREEZE_MANIFEST.json` hashes the 17 builder outputs, the inputs and the code. This file (TEST_RUN.md) is not
a builder output and is not in the manifest.

## Targeted

```
python3 -m pytest -q -p no:cacheprovider -o addopts="" tests/slab_rebar_pre_s7 tests/d1_2_footing_cover_audit \
    tests/ad1_authority_decisions tests/d1_1_stirrup_authority_audit tests/delta_release \
    tests/footing_rebar_s4_1 tests/superstructure_beam_rebar_s6_1 tests/ground_system_rebar_s5_1 \
    tests/structural_comparison_engine/test_rebar_product_firewall.py \
    tests/footing_rebar_s4/test_alsenan_s4_package.py::test_freeze_manifest_still_matches \
    tests/ground_system_rebar_s5/test_alsenan_s5_package.py::test_freeze_manifest_still_matches \
    tests/superstructure_beam_rebar_s6/test_alsenan_s6_package.py::test_freeze_manifest_still_matches \
    tests/source_recovery_delta
```

Result: **281 passed**. That is the 233 from D1.2, plus 48 PRE-S7 tests:
- 24 generic tests in `tests/slab_rebar_pre_s7/test_slab_rebar_readiness.py`. They use synthetic inputs only, with no
  project data.
- 24 package tests in `tests/slab_rebar_pre_s7/test_pre_s7_package.py`.

The firewall registry (`tests/structural_comparison_engine/rebar_product_registry.py`) gains two entries:
- `engine/source/slab_rebar_readiness.py`, in ACCURATE_MODULES;
- `research/alsenan_slab_rebar_pre_s7/build_pre_s7.py`, in ACCURATE_BUILDERS.

No earlier test was changed.

## PRE-S7 brief §23: where each required test lives

Generic tests are in `test_slab_rebar_readiness.py`; package tests are in `test_pre_s7_package.py` (both under
`tests/slab_rebar_pre_s7/`).

| §23 item | Generic test | Package test |
|---|---|---|
| local thickness override | `test_local_thickness_overrides_floor_and_default` | `test_thickness_precedence` |
| 160 mm missing row | `test_160_mm_has_no_temperature_row` | `test_temperature_table_has_no_160_or_180_row` |
| 180 mm missing row | `test_180_mm_has_no_temperature_row` | `test_temperature_table_has_no_160_or_180_row` |
| no interpolation | `test_no_interpolation_and_exact_rows_only` | `test_temperature_table_has_no_160_or_180_row` |
| 25 mm cover is not exact | `test_minimum_25_mm_cover_is_not_exact` | `test_cover_is_a_minimum_and_no_length_is_exact` |
| clear vs centreline span | `test_clear_span_versus_centreline_span` | `test_support_extents_rederived` |
| 0.25L | `test_025L_at_a_non_continuous_support` | `test_support_rules_gates`, `test_support_extents_rederived` |
| 0.30L | `test_030L_at_a_continuous_support_uses_the_larger_span` | `test_support_rules_gates`, `test_support_extents_rederived` |
| 0.125L | `test_0125L_bottom_cutoff` | `test_support_rules_gates` |
| unknown L blocks release | `test_unknown_L_basis_blocks_release` | `test_support_rules_gates` (plan note 2 "1/3 span": `L_UNDEFINED`, gate blocked) |
| 50% split | `test_50_percent_bottom_bar_split` | `test_support_rules_gates` (WHICH_50_PERCENT = NOT_STATED), `test_readiness_states` |
| continuous bar counted once | `test_a_continuous_bar_across_two_panels_is_counted_once` | `test_bar_runs_count_each_bar_once` |
| support top bar counted once | `test_a_support_top_bar_is_counted_once` | `test_supports_terminate_and_are_counted_once` |
| opening intersects X only | `test_opening_intersects_x_bars_only` | `test_openings` |
| opening intersects X and Y | `test_opening_intersects_x_and_y_bars` | `test_openings` |
| opening extras kept separate | `test_opening_extra_bars_stay_separate_from_deductions` | `test_openings`, `test_only_project_supported_component_types` |
| VOID + tag conflict | `test_void_with_a_reinforcement_tag_is_a_source_conflict` | `test_gf_void_with_t16_tag_is_a_source_conflict` |
| spacing ambiguity | `test_spacing_count_is_ambiguous_without_a_project_rule` | `test_count_rules_keep_rate_width_and_rule_apart` |
| edge-bar ambiguity | `test_edge_bar_is_ambiguous` | `test_count_rules_keep_rate_width_and_rule_apart` |
| NTS cannot create length | `test_nts_graphic_cannot_create_length` | `test_support_rules_gates` (rule rows carry NTS_STATUS; values only from printed text) |
| specials excluded | `test_special_structures_are_excluded` | `test_special_structures_never_reach_s7`, `test_scope_population` |
| population conservation | `test_population_conservation` | `test_every_slab_geometry_terminates_once`, `test_conservation_gates_and_provenance` |
| token conservation | `test_token_conservation` | `test_token_conservation` |

The package tests also cover:
- deliverables;
- the PRE-S7 freeze manifest;
- immutability of the nine frozen stages and the S1 INDEX;
- the byte-identical rebuild;
- builder blindness (no donor, code or benchmark reference) and its registry entry;
- no kg anywhere;
- the readiness states;
- conflicts, SENL and questions.

The package tests re-derive the package's own claims rather than checking them against a reference total:
- each support extent is recomputed from the census clear spans: 0.30 × max(L1, L2) at a continuous support, and
  0.25 × L1 at a non-continuous one;
- each bar run's known straight extent is recomputed from the panel extents;
- each count candidate is recomputed from width / (1000 / rate).

## Known gap (recorded, not fixed)

The frozen `cover_authority.wording_kind` (D1.2) does not recognise the wording "shall not be less than" as a
minimum-cover phrase.
- `slab_rebar_readiness.cover_wording_kind` adds that phrase for slabs only.
- The frozen module is unchanged.

## Full suite

Pending: it will be run on the clean committed tree.
