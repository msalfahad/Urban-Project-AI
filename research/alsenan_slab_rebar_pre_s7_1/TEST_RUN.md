# PRE-S7.1 / AD2 TEST_RUN: slab QTO authority / readiness resolution

Baseline HEAD `9f89ab6`. PRE-S7.1 is a delta over frozen PRE-S7:
- no slab kg and no bar-length total are calculated;
- S7 is not started;
- PRE-S7 is not edited;
- S4, S4.1, S5, S6, S5.1, S6.1, AD1, D1.1, D1.2 and PRE-S7 are unchanged, and all ten freeze manifests still match.

The builder was run twice and the second run was byte-identical (`test_rebuild_is_byte_identical` repeats this).
`PRE_S7_1_FREEZE_MANIFEST.json` hashes the 14 builder outputs, the inputs and the code. This file (TEST_RUN.md) is
not a builder output and is not in the manifest.

## Targeted

```
python3 -m pytest -q -p no:cacheprovider -o addopts="" tests/slab_rebar_pre_s7_1 tests/slab_rebar_pre_s7 \
    tests/d1_2_footing_cover_audit tests/ad1_authority_decisions tests/d1_1_stirrup_authority_audit \
    tests/delta_release tests/footing_rebar_s4_1 tests/superstructure_beam_rebar_s6_1 \
    tests/ground_system_rebar_s5_1 tests/structural_comparison_engine/test_rebar_product_firewall.py \
    tests/footing_rebar_s4/test_alsenan_s4_package.py::test_freeze_manifest_still_matches \
    tests/ground_system_rebar_s5/test_alsenan_s5_package.py::test_freeze_manifest_still_matches \
    tests/superstructure_beam_rebar_s6/test_alsenan_s6_package.py::test_freeze_manifest_still_matches \
    tests/source_recovery_delta
```

Result: **337 passed**. That is the 281 from PRE-S7, plus 56 PRE-S7.1 tests:
- 29 generic tests in `tests/slab_rebar_pre_s7_1/test_slab_qto_authority.py`, using synthetic inputs only;
- 27 package tests in `tests/slab_rebar_pre_s7_1/test_pre_s7_1_package.py`.

The firewall registry gains two entries:
- `engine/source/slab_qto_authority.py`, in ACCURATE_MODULES;
- `research/alsenan_slab_rebar_pre_s7_1/build_pre_s7_1.py`, in ACCURATE_BUILDERS.

No earlier test was changed.

## Brief §20: where each required test lives

Generic tests are in `test_slab_qto_authority.py`; package tests are in `test_pre_s7_1_package.py` (both under
`tests/slab_rebar_pre_s7_1/`).

| §20 item | Generic test | Package test |
|---|---|---|
| 5 bars/m × 3.6 m = 18 equivalent bars | `test_five_bars_per_metre_over_3_6_m_is_18_equivalent_bars` | `test_rate_density_is_unrounded_and_never_plus_one` |
| no +1 | `test_rate_qto_adds_no_plus_one` | `test_rate_density_is_unrounded_and_never_plus_one` |
| no rounding of rate QTO | `test_rate_qto_is_never_rounded` | `test_rate_density_is_unrounded_and_never_plus_one` |
| physical BBS count remains unresolved | `test_physical_bbs_count_stays_unresolved` | `test_rate_density_is_unrounded_and_never_plus_one` |
| explicit NØD count | `test_explicit_count_needs_a_finite_bar_object`, `test_a_released_count_with_an_unknown_length_stays_blocked` | `test_explicit_counts_release_with_blocked_lengths` |
| 50/50 QTO split | `test_fifty_fifty_qto_split` | `test_fifty_plus_fifty_is_one_hundred`, `test_curtailed_half_is_shortened_by_0125_L_on_rectangles` |
| odd physical count remains BBS-ambiguous | `test_odd_physical_count_is_bbs_ambiguous` | `test_fifty_plus_fifty_is_one_hundred` (PHYSICAL_SEQUENCING unresolved) |
| same-role local rule overrides generic | `test_same_role_local_rule_overrides_generic` | `test_top_rule_identity_same_family_note_governs`, `test_local_top_override_supersedes_the_general_rule` |
| different-role rules coexist | `test_different_role_rules_coexist` | `test_top_rule_identity_same_family_note_governs` (the '/Top' bars beside beams stay unresolved, nothing else blocked) |
| mismatch split left/right | `test_mismatch_splits_left_and_right` | `test_mismatch_splits_do_not_overlap` |
| no invented lap | `test_no_invented_lap` | `test_mismatch_splits_do_not_overlap` (transitions blocked, no crossing item) |
| water-tank ownership transfer | `test_water_tank_ownership_transfer` | `test_ownership_transfer_loses_nothing` |
| GF-21 ownership transfer | `test_stair_lightwell_transfer_preserves_the_conflict` | `test_ownership_transfer_loses_nothing` |
| sunken slab mesh retained | `test_sunken_slab_mesh_retained` | `test_sunken_mesh_retained_and_extras_blocked` |
| sunken edge extra blocked | `test_sunken_edge_extras_blocked` | `test_sunken_mesh_retained_and_extras_blocked` |
| cantilever vs bearing-wall geometry | `test_cantilever_versus_bearing_wall_geometry` | `test_dense_hatch_classified_by_geometry` |
| trapezoid panel local bar runs | `test_trapezoid_panel_local_bar_runs` | `test_local_strips_reconcile_to_panel_geometry`, `test_irregular_panels_use_local_bar_lines` |
| L-shaped panel local bar runs | `test_l_shaped_panel_local_bar_runs` | `test_local_strips_reconcile_to_panel_geometry` |
| opening clipped local bar run | `test_opening_clipped_local_bar_run` | (no in-scope panel has a hole: the engine test covers it) |
| outside edge = non-continuous | `test_outside_edge_is_non_continuous` | `test_physical_continuity_not_analysis_ownership` |
| excluded-but-physical slab != outside edge | `test_excluded_but_physical_slab_is_not_an_outside_edge` | `test_physical_continuity_not_analysis_ownership` |
| minimum 25 mm cover authority | `test_minimum_25_mm_cover_is_project_basis_only` | `test_lanes_and_labels` (no released item uses the minimum cover or '40 CL.') |
| 160 mm temperature remains blocked | `test_160_mm_temperature_stays_blocked` | `test_temperature_stays_blocked_and_separate` |
| component-level blocking does not block unrelated steel | `test_component_blocking_does_not_block_unrelated_steel` | `test_temperature_stays_blocked_and_separate` |

The package tests also cover:
- deliverables, the PRE-S7.1 freeze manifest, the ten frozen stages including PRE-S7, and the byte-identical rebuild;
- builder blindness (no donor, code, benchmark or kg reference) and its registry entry;
- every PRE-S7 component terminating once, item parents and component states;
- the density budget and full width coverage per bottom family;
- crossings counted once, from the lower-id face only;
- conflicts, gates and provenance.

The package tests re-derive the package's own claims rather than checking them against a reference total:
- each strip integral against the S1 polygon area (shoelace formula);
- each equivalent count as rate × fraction × width;
- each rectangular-panel run as the census clear span;
- each curtailed run as L × (1 − 0.125 n);
- each top extension as L / 3.

## Full suite

`python3 -m pytest -o addopts="" -q -p no:cacheprovider` at `787890c` gave
**6905 passed, 4 skipped, 100 xfailed, 2 warnings in 440.09 s, exit 0**.
- That is the 6849 from PRE-S7 plus the 56 PRE-S7.1 tests.
- The run used the clean committed tree. No file was edited during it, and the tree was still clean afterwards.
- The 2 warnings are the existing deprecation shims (`ratio_check`, `ratio_qa`), the same ones as in PRE-S7.
- Every frozen-manifest test still matches: S4, S5, S6, S4.1, S6.1, S5.1, AD1, D1.1, D1.2 and PRE-S7, plus the new PRE-S7.1
  manifest.
