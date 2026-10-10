"""The two Urban reinforcement products and the dependency firewall between them (declaration only).

    STRUCTURAL SOURCE REGISTERS  ->  ACCURATE_BOQ_REBAR      (official takeoff, bar-by-bar)
    CONCRETE REGISTER            ->  ROUGH_REBAR_SUMMARY     (estimating / sanity only)

There is no arrow between the two engines. They meet only in the REPORT layer, which reads both and writes neither.
Kept beside the test (not in engine/) because it names project builders. The lists below are what
test_rebar_product_firewall.py checks: the transitive
import closure of every ACCURATE module and builder must not reach a ROUGH, REPORT or COMPARISON module and must not
carry reference-QS or external-oracle quantities; the ROUGH closure must not reach an ACCURATE module. A new rebar / BBS module in engine/ must be declared here
or the firewall test fails. No imports.
"""

ACCURATE_BOQ_REBAR = "ACCURATE_BOQ_REBAR"
ROUGH_REBAR_SUMMARY = "ROUGH_REBAR_SUMMARY"

ACCURATE_MODULES = (
    "engine/source/accurate_boq_rebar.py",
    "engine/source/rebar_model.py",
    "engine/source/column_rebar.py",
    "engine/source/slab_rebar_binding.py",
    "engine/source/bbs_optimiser.py",
    "engine/source/rebar_unit_mass.py",
    "engine/source/waste_procurement.py",
    "engine/source/urban_methods_v3.py",
    "engine/source/footing_rebar_guard.py",     # pre-S4 input guard (token parity, census, BOXED); no kg
    "engine/source/footing_rebar.py",           # S4 accurate footing rebar engine
    "engine/source/ground_beam_network.py",     # pre-S5 ground-beam physical network (geometry only, no kg)
    "engine/source/ground_system_provenance.py",  # S5 provenance = generic contract + member fields
    "engine/source/rebar_provenance.py",        # generic accurate-rebar provenance (ELEMENT_* identity)
    "engine/source/ground_system_resolution.py",  # pre-S5.1 source-resolution decisions (no geometry, no kg)
    "engine/source/ground_system_rebar.py",     # S5 accurate ground-beam + strap-beam rebar engine
    "engine/source/beam_rebar_readiness.py",    # pre-S6 superstructure beam readiness (occurrence / detail state, no kg)
    "engine/source/superstructure_beam_rebar.py",  # S6 accurate simple-beam + continuous-beam rebar engine
    "engine/source/graphic_evidence.py",        # D1 graphic evidence policy (which drawn portion may carry length)
    "engine/source/delta_release.py",           # D1 frozen baseline + delta records, conservation (no kg rewrite)
    "engine/source/link_geometry.py",           # D1 link topology + envelope core path / end leg / count bounds
    "engine/source/delta_correction.py",        # D1.1 errata records over a frozen delta (never adds steel)
    "engine/source/authority_decisions.py",     # AD1 owner authority decisions, provenance classes, facet errata
    "engine/source/cover_authority.py",         # D1.2 cover basis, straight-run / count directions, cover errata
    "engine/source/slab_rebar_readiness.py",    # PRE-S7 slab readiness (no kg)
    "engine/source/slab_qto_authority.py",      # AD2 / PRE-S7.1 slab QTO authority lanes (no kg)
    "engine/source/slab_rebar_qto.py",          # S7 restricted project-basis slab rebar QTO (rate density, D^2/162)
    "engine/source/ground_slab_qto.py",         # S8.1 source-zoned ground-slab concrete + mesh (exact line / arc strips)
    "engine/source/region_recovery.py",         # S8.1A unfaced-region partition, evidence lanes, mesh cover fit (no kg)
    "engine/source/pool_qto.py",                # S8.2 pool shell concrete + rate / finite bars, bar runs, interfaces
    "engine/source/shell_line_distribution.py",  # S8.3A line layouts on a spherical cap (density / meridians)
    "engine/source/slab_layered_mesh.py",       # S8.4 callouts, thickness tags, (T&B) layers, stop zones per edge
    "engine/source/special_column_components.py",  # S8.5 turned / dead / planted column components, ownership
    "engine/source/lintel_qto.py",              # S8.6 lintel schedule binding, extent, straight bars, stirrup count
    "engine/source/opening_census.py",          # S8.6 wall openings from plan faces (geometry only, no kg)
    "engine/source/lintel_release_audit.py",    # S8.6A bearing reach, end classification, stirrup readings
    "engine/source/stair_geometry.py",          # S8.7 tread runs, flight / landing outlines, rate density (no project data)
    "engine/bbs_steel.py",
)
# project builders that produce accurate reinforcement registers
ACCURATE_BUILDERS = (
    "research/alsenan_rebar_truth_03/build_rebar_v3.py",
    "research/alsenan_rebar_source_exhaustion_04/build_rebar_v4.py",
    "research/external_engine_lab/alsenan_rebar_v3.py",
    "research/external_engine_lab/alsenan_rebar_v4.py",
    "research/external_engine_lab/alsenan_v3b_rebar.py",
    "research/external_engine_lab/alsenan_v3b_struct.py",
    "research/alsenan_column_rebar_s3/build_column_rebar_s3.py",
    "research/alsenan_column_rebar_s3_1/build_column_rebar_s3_1.py",
    "research/alsenan_footing_rebar_s4/build_footing_rebar_s4.py",
    "research/pre_s5_ground_system_readiness/build_pre_s5.py",
    "research/pre_s5_1_source_resolution/build_pre_s5_1.py",
    "research/alsenan_ground_system_rebar_s5/build_ground_system_rebar_s5.py",
    "research/pre_s6_superstructure_beam_readiness/build_pre_s6.py",
    "research/alsenan_superstructure_beam_rebar_s6/build_superstructure_beam_rebar_s6.py",
    "research/source_recovery_delta/build_source_recovery_delta.py",   # source-recovery register (no kg)
    "research/alsenan_footing_rebar_s4_1/build_footing_rebar_s4_1.py",  # S4.1 delta over frozen S4
    "research/alsenan_superstructure_beam_rebar_s6_1/build_superstructure_beam_rebar_s6_1.py",  # S6.1 delta over S6
    "research/alsenan_ground_system_rebar_s5_1/build_ground_system_rebar_s5_1.py",  # S5.1 delta over S5
    "research/d1_1_stirrup_authority_audit/build_d1_1_stirrup_audit.py",  # D1.1 link-authority errata over S6.1 / S5.1
    "research/ad1_authority_decisions/build_ad1_authority_decisions.py",  # AD1 authority decisions + errata
    "research/d1_2_footing_cover_audit/build_d1_2_footing_cover_audit.py",  # D1.2 footing cover-authority errata
    "research/alsenan_slab_rebar_pre_s7/build_pre_s7.py",  # PRE-S7 slab readiness (no kg)
    "research/alsenan_slab_rebar_pre_s7_1/build_pre_s7_1.py",  # AD2 / PRE-S7.1 slab QTO authority delta (no kg)
    "research/alsenan_slab_rebar_s7/build_s7.py",  # S7 restricted elevated slab rebar QTO (476 candidates only)
    "research/alsenan_slab_rebar_s7a_qa/build_s7a_qa.py",  # S7A dated QA: top-extent readings (sensitivity), errata
    "research/pre_s8_structural_completeness/build_pre_s8.py",  # PRE-S8 census, coverage, readiness (no kg)
    "research/alsenan_ground_slab_s8_1/build_s8_1.py",  # S8.1 ground slab, two source-zoned cells (project basis)
    "research/alsenan_ground_slab_s8_1a/build_s8_1a.py",  # S8.1A population recovery + cover audit (no kg, no m3)
    "research/alsenan_swimming_pool_s8_2/build_s8_2.py",  # S8.2 swimming pool source-controlled QTO
    "research/alsenan_swimming_pool_s8_2a/build_s8_2a.py",  # S8.2A elevation depth authority (correction layer)
    "research/alsenan_dome_ring_s8_3/build_s8_3.py",      # S8.3 dome shells + ring beams (blind, frozen)
    "research/alsenan_dome_ring_s8_3/errata/build_errata.py",  # S8.3 errata (dated, moves no quantity)
    "research/alsenan_dome_mesh_s8_3a/build_s8_3a.py",  # S8.3A mesh distribution audit (no quantity moved)
    "research/alsenan_water_tank_s8_4/build_s8_4.py",   # S8.4 water-tank roof region (blind, frozen)
    "research/alsenan_special_columns_s8_5/build_s8_5.py",  # S8.5 special columns (blind, frozen)
    "research/alsenan_lintels_s8_6/build_s8_6.py",  # S8.6 lintels (blind, frozen)
    "research/alsenan_lintels_s8_6a/build_s8_6a.py",  # S8.6A dated correction layer over S8.6 (lanes only)
    "research/alsenan_stairs_s8_7/build_s8_7.py",  # S8.7 staircases and landings (blind, frozen)
)
ROUGH_MODULES = (
    "engine/source/rough_rebar_sanity.py",
)
ROUGH_PROFILES = (
    "engine/profiles/URBAN_ROUGH_REBAR_PROFILE_V1.json",
)
SANITY_QA_MODULES = (                    # kg/m3 QA helpers moved out of the accurate code (deprecated wrappers remain)
    "engine/source/rebar_sanity_qa.py",
    "engine/rebar_sanity_qa.py",            # production-layer mirror (production may not import engine.source)
)
REPORT_MODULES = (                       # may read both products, writes neither
    "engine/source/rebar_sanity_variance.py",
    "engine/source/rebar_boq_sections.py",
)
COMPARISON_MODULES = (                   # reference-QS / oracle comparison: never upstream of an accurate quantity
    "engine/source/comparison_scope.py",
    "engine/source/source_oracle_comparison.py",
    "engine/source/cad_oracle.py",
    "research/external_engine_lab/alsenan_b1_benchmark.py",
    "research/alsenan_rebar_truth_03/post_freeze_rebar_compare.py",
    "research/alsenan_rebar_source_exhaustion_04/post_freeze_rebar_comparison.py",
    "research/alsenan_footing_rebar_s4/post_freeze_comparison.py",
    "research/alsenan_ground_system_rebar_s5/post_freeze_comparison.py",
    "research/alsenan_superstructure_beam_rebar_s6/post_freeze_comparison.py",
    "research/alsenan_slab_rebar_s7/post_freeze/post_freeze_comparison.py",
    "research/alsenan_ground_slab_s8_1/post_freeze/post_freeze_comparison.py",
    "research/alsenan_swimming_pool_s8_2/post_freeze/post_freeze_comparison.py",
    "research/alsenan_dome_ring_s8_3/post_freeze/post_freeze_comparison.py",
    "research/alsenan_water_tank_s8_4/post_freeze/post_freeze_comparison.py",
    "research/alsenan_special_columns_s8_5/post_freeze/post_freeze_comparison.py",
    "research/alsenan_lintels_s8_6/post_freeze/post_freeze_comparison.py",
    "research/alsenan_stairs_s8_7/post_freeze/post_freeze_comparison.py",
)
COMPARISON_DIRS = (
    "research/alsenan_multi_engine_comparison",
)
# engine modules that mention reinforcement but are neither product (QS audit of external BOQs, reporting, census)
OTHER_REBAR_AWARE = (
    "engine/audit/refdata.py", "engine/audit/rules.py", "engine/audit/takeoff.py",
    "engine/reporting_v2/terms.py", "engine/reporting_v3/units.py", "engine/reporting_v3/workbooks.py",
    "engine/reporting_v3/workbooks_v3b.py", "engine/schedule_template.py", "engine/raster_topology.py",
    "engine/__init__.py", "engine/source/cad_guards.py", "engine/source/engineering_flags.py",
    "engine/source/flag_detectors.py", "engine/source/schedule_grammar.py", "engine/source/structural_authority.py",
    "engine/source/structural_census.py", "engine/source/structural_qto.py", "engine/source/structural_schedule.py",
    "engine/source/structural_population_discovery.py",
    # coverage-recovery round: concrete / geometry modules that mention reinforcement only to exclude it
    "engine/source/column_concrete_geometry.py", "engine/source/physical_measurement_state.py",
    "engine/source/coverage_metrics.py",
)
