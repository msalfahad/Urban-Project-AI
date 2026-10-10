"""ALSENAN CONTROL-PLANE ROUND 2 - registers that depend on the repository, not on the drawing:

    LEGACY_CAD_MIGRATION_REGISTER   every user-facing tool whose import graph reaches engine/cad_adapter.py, with its
                                    guard; library / reference paths listed with the reason they are not guarded
    GATE_TRANSITION_REGISTER        G01-G23: old failure, production change, new behaviour, real Alsenan evidence,
                                    proving test, final state (PASS / XFAIL) - and the round-1 tests it supersedes
"""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "research" / "alsenan_control_plane_01"))
import build_registers as R1  # noqa: E402  (static AST import graph of round 1)

GUARD = "require_legacy_opt_in("


def legacy_cad() -> dict:
    rows = []
    for p in sorted((ROOT / "tools").resolve().glob("*.py")):
        top = R1._reach(p, False)
        lazy = top or R1._reach(p, True)
        if not lazy:
            continue
        src = p.read_text()
        main_at = src.find("def main(")
        guarded = main_at >= 0 and GUARD in src[main_at:main_at + 1500]
        rows.append({"entry_point": f"tools/{p.name}", "kind": "USER_CLI", "reaches": "MODULE_LEVEL" if top else "LAZY",
                     "chain": lazy, "guarded": guarded,
                     "behaviour": "refuses (exit 2) without --allow-legacy-cad-adapter / URBAN_ALLOW_LEGACY_CAD_ADAPTER=1"
                     if guarded else "UNGUARDED"})
    for ep, path, kind, why in (
            ("engine.ingest.harness", "engine/ingest/harness.py", "LIBRARY",
             "imported by research PA05/PA07/PA08 runners and their tests; not a user command - left unguarded so "
             "historical reproductions keep working; any new CLI over it must call the guard"),
            ("engine.freeze_manifest", "engine/freeze_manifest.py", "LIBRARY_LAZY",
             "function-level import used to hash historical freezes; no measurement"),
            ("RC1 Qortuba (rc1_qortuba)", "research/external_engine_lab/rc1_qortuba.py", "REFERENCE_UNCHANGED",
             "RC1_REFERENCE is never patched: it imports cad_adapter dataclasses via r8_7_canonical but measures "
             "through K1 / K2; Qortuba outputs are regression-tested unchanged")):
        p = ROOT / path
        top = R1._reach(p, False)
        rows.append({"entry_point": ep, "kind": kind, "reaches": "MODULE_LEVEL" if top else
                     ("LAZY" if R1._reach(p, True) else "NOT_REACHABLE"), "chain": top or R1._reach(p, True),
                     "guarded": False, "behaviour": why})
    cli = [r for r in rows if r["kind"] == "USER_CLI"]
    return {"SCHEMA": "URBAN_LEGACY_CAD_MIGRATION_V1", "guard_module": "engine/legacy_cad_guard.py", "rows": rows,
            "user_cli_total": len(cli), "user_cli_guarded": sum(r["guarded"] for r in cli),
            "rule": "a user-facing command that can reach the legacy adapter refuses without an explicit opt-in; "
                    "historical code is not deleted"}


T1 = "tests/alsenan_control_plane/test_control_plane_r1.py"
T2 = "tests/alsenan_control_plane/test_control_plane_r2_gates.py"
GATES = [
    ("G01", "C-1", "PASS", "R1: 325.251 m2 of COMPUTED_REVIEW room floor released as COMPUTED (registers.py "
     "'COMPUTED' if .. else 'COMPUTED')", "alsenan_v3_registers.propagate(): every room-derived line is capped by "
     "its room status; alsenan_v3b_lines.cap_by_room_status() caps V3b re-derivations",
     "a COMPUTED_REVIEW room yields REVIEW lines (V1) and at most PROVISIONAL (V2)",
     "RELEASE_V2_MIGRATION_REGISTER: no F-FL line of a non-COMPUTED room is VERIFIED_COMPLETE",
     "test_G01_review_room_floor_never_verified"),
    ("G02", "B-1", "PASS", "R1: TS01 MULTI_UNRESOLVED zones released as one clean zone",
     "rooms carry TS01 semantic_state; ALSENAN_CONTROL_V2 evaluates every room trade through TRADE_DEPENDENCY_MATRIX",
     "split-dependent trades of GF-Z04 / GF-Z06 are BLOCKED_SEMANTIC_TRADE_BOUNDARY; no line of an unresolved "
     "space is VERIFIED_COMPLETE", "GF-Z04 floor 155.655 BLOCKED (audit), GF-Z06 floor 24.94 BLOCKED",
     "test_G02_unresolved_semantic_space_never_released_as_one_clean_zone"),
    ("G03", "B-2", "PASS", "R1: _room_class('DEWANEYA / Wash') == 'DRY' (DRY wins)",
     "alsenan_v3_layers._room_class returns MIXED_SEMANTIC_ZONE for names of different classes",
     "mixed spaces get no default dry material and no dry-only quantity", "GF-Z04, GF-Z06, 1F-Z06 = MIXED",
     "test_G03_dry_wins_removed"),
    ("G04", "J-1", "PASS (semantics corrected)", "R1 gate asked wet_rooms_lost == [] (forces labels into rooms)",
     "WET_LABEL_ACCOUNTING_REGISTER: every wet label ends in a terminal state; mixed-zone wet trades emit BLOCKED "
     "lines (registers.tile_wp)", "unaccounted_wet_labels == []; blocked labels keep the wet population incomplete",
     "35 labels: 25 bound, 5 blocked semantic boundary, 4 blocked no physical site, 1 not in scope (pool)",
     "test_G04_every_wet_label_accounted"),
    ("G05", "C-2", "PASS", "R1: skirting hard-coded COMPUTED", "propagate() on F-SK", "skirting follows room status",
     "F-SK lines of review rooms REVIEW", "test_G05_skirting_status_propagates"),
    ("G06", "C-3", "PASS", "R1: ceiling hard-coded COMPUTED", "propagate() on CE", "ceiling follows room status",
     "CE lines of review rooms REVIEW", "test_G06_ceiling_status_propagates"),
    ("G07", "D", "PASS (V2 field)", "R1: release('PARTIAL') procurement_eligible (V1)",
     "engine/source/release_model_v2: PARTIAL -> VERIFIED_PARTIAL_LOWER_BOUND, never procurement eligible without "
     "owner approval; V1 kept as procurement_eligible_v1", "lower bounds shown '>= q', not procurable by default",
     "every VERIFIED_PARTIAL_LOWER_BOUND line has procurement_eligible_v2 = False",
     "test_G07_partial_never_procurement_eligible_v2"),
    ("G08", "E-1", "PASS (semantics corrected)", "R1 gate asked every source object CONSUMED_COMPLETE (parse success)",
     "alsenan_structural_source_v2 + STRUCTURAL_SOURCE_COVERAGE_V2: every admitted source object has a terminal "
     "coverage state; interpretation reported separately", "accounting 100 %, interpretation < 100 % stated",
     "332 source objects accounted", "test_G08_every_structural_source_object_has_a_terminal_state"),
    ("G09", "F-1", "PASS (semantics corrected)", "R1 gate asked zero silent occurrences only via a register count",
     "production terminal records (alsenan_v3_structure.terminal) + STRUCTURAL_POPULATION_COVERAGE_V2 + ledger",
     "every concrete / rebar occurrence ends in a terminal state; BLOCKED allowed", "ledger conserved",
     "test_G09_every_structural_population_has_a_terminal_state"),
    ("G10", "D1", "PASS (definitions only)", "R1: no CB definition in any register",
     "STRUCTURAL_DEFINITION_REGISTER_V2 reads C-BEAM2 / C-BEAM3 ATTRIBs", "13 typed CB definitions; CB rebar "
     "populations stay BLOCKED (REBAR_BLOCKED_PENDING_REBAR_CONSUMER_V2)", "CB1-CB13",
     "test_G10_cb_definitions_captured_from_source"),
    ("G11", "D2", "XFAIL (by design this round)", "per-metre footing counts used as bar counts",
     "per-metre sets now BLOCKED terminal records (no wrong kg released)", "quantity consumer is Round 3",
     "F8 / F12 / F13 / F14 BLOCKED", "test_G11_two_layer_footing_quantity_consumer"),
    ("G12", "D3", "PASS", "R1: FF emitted nothing", "footing_rebar emits REBAR_BLOCKED_SCHEDULE_CELL_UNREAD",
     "FF has a blocked population row", "FF #? BLOCKED", "test_G12_ff_emits_a_blocked_population"),
    ("G13", "D4", "XFAIL (by design this round)", "straps filtered out", "strap_rebar emits "
     "REBAR_BLOCKED_NO_CONSUMER terminals (accounted)", "strap quantity consumer is Round 3", "SB1-SB3 BLOCKED",
     "test_G13_strap_rebar_quantity_consumer"),
    ("G14", "D5", "PASS", "R1: 1,739.7 kg on 26 occurrences with no concrete",
     "column_rebar emits REBAR_BLOCKED_OCCURRENCE_NOT_ESTABLISHED with the kg in audit only",
     "no verified rebar without an established occurrence", "26 occurrences BLOCKED",
     "test_G14_no_verified_rebar_without_an_established_occurrence"),
    ("G15", "D6", "XFAIL (owner / engineer question Q-S4)", "min-area ground binding", "none this round",
     "unchanged", "-", "test_G15_ground_zone_not_bound_by_minimum_area"),
    ("G16", "I-1", "PASS (semantics corrected)", "R1 gate asked ambiguous_m == 0",
     "blockwork() writes BLOCKWORK_BLOCKED_AMBIGUOUS_BAND rows; WALL_LENGTH_CONSERVATION_V2",
     "raw 46.63 m kept; accounted 46.63; unaccounted 0; blockwork LOWER_BOUND", "13 ambiguous bands",
     "test_G16_ambiguous_wall_length_accounted_not_erased"),
    ("G17", "I-2", "PASS (semantics corrected)", "R1 gate asked unpaired boundary == 0",
     "every boundary item outside a band is classified in the ledger", "raw 187.82 m kept as AMBIGUOUS_BLOCKED; "
     "glazing / obstacle edges classified; unaccounted 0", "772 unpaired items",
     "test_G17_unpaired_boundary_accounted"),
    ("G18", "K-1", "PASS", "R1: 59 V3a openings COMPUTED with a BLOCKED height",
     "openings() rows PARTIAL with per-attribute states; OPENING_EVIDENCE_V2", "area never more certain than height",
     "0 COMPUTED-with-blocked-height", "test_G18_opening_area_never_computed_with_blocked_height"),
    ("G19", "SD-12", "PASS", "R1: SB2 duplicate kept silently", "schedule_grammar.key_conflicts in the V2 reader",
     "SOURCE_CONFLICT_DUPLICATE_SCHEDULE_KEY with both rows; SB2 population BLOCKED", "SB2 80x50 / 100x50",
     "test_G19_duplicate_sb2_is_an_explicit_conflict"),
    ("G20", "SD-08", "PASS (semantics corrected)", "R1 gate asked BOXED interpreted",
     "FT definitions keep raw_boxed_value + BLOCKED_SEMANTICS; affected footings LOWER_BOUND", "captured, not guessed",
     "11 FT types", "test_G20_boxed_captured_and_accounted"),
    ("G21", "SD-11", "PASS (semantics corrected)", "R1 gate asked side bars in bar definitions",
     "REMARKS bound to rows as typed tokens (TOKENS_PARSED_SEMANTICS_CANDIDATE)", "accounted; no kg added",
     "23 beams B7-B29", "test_G21_side_bar_remarks_accounted"),
    ("G22", "O-1", "PASS", "R1: tools/run_cad_pipeline.py reaches cad_adapter unguarded",
     "engine/legacy_cad_guard.py called first in main() of 17 tools", "refusal (exit 2) without explicit opt-in",
     "17 / 17 user CLIs guarded", "test_G22_user_cli_legacy_adapter_guarded"),
    ("G23", "SD-17", "XFAIL (applicability unproved)", "stair rebar BLOCKED", "none (page-16 layout captured as "
     "BLOCKED_UNREAD source object, not applied)", "unchanged", "-", "test_G23_stair_rebar_bound_to_typical_layout"),
]
SUPERSEDED_R1 = [
    ("test_c_flooring_status_is_computed_whatever_the_room_status", "pinned the defect; replaced by G01 / G05"),
    ("test_c_skirting_and_ceiling_status_hardcoded_computed", "replaced by G05 / G06"),
    ("test_b_room_class_multi_name_dry_wins", "replaced by G03"),
    ("test_j_tile_wp_skips_a_dry_zone_with_a_wet_label", "mixed zones now emit BLOCKED wet lines (G04)"),
    ("test_d2_footing_per_metre_count_used_as_absolute_count", "per-metre sets now BLOCKED (G11 stays XFAIL)"),
    ("test_d3_ff_empty_bar_definition_emits_nothing", "replaced by G12"),
    ("test_sd01_footing_skip_is_silent", "replaced by test_terminal_records_footing_blocked_concrete"),
    ("test_d1_cb_measured_occurrence_emits_nothing", "replaced by test_terminal_records_beams"),
    ("test_d4_strap_definition_filtered_out", "replaced by test_terminal_records_straps / G13"),
    ("test_sd04_beam_without_length_is_silent", "replaced by test_terminal_records_beams"),
    ("test_d5_column_rebar_ignores_occurrence_state", "replaced by G14"),
    ("test_mutation_room_status_does_not_reach_floor_status", "replaced by test_mutation_room_status_reaches_lines"),
    ("test_d6_ground_zone_binds_the_smallest_containing_cell", "line anchor moved; replaced by G15 (XFAIL)"),
    ("test_sd_code_anchors_hold", "R1 anchors describe the 47dac56 code; R2 terminal records replace the drops"),
    ("G01-G23 (round 1)", "evaluated the frozen R1 diagnostic registers (which can never change); re-homed in "
                          "test_control_plane_r2_gates.py against production behaviour and the R2 registers"),
]


def gates() -> dict:
    return {"SCHEMA": "URBAN_ALSENAN_GATE_TRANSITION_V1", "rows": [
        {"gate": g, "defect": d, "final_state": st, "old_failure": old, "production_change": ch, "new_behaviour": nb,
         "real_alsenan_evidence": ev, "proving_test": f"{T2}::{t}"} for g, d, st, old, ch, nb, ev, t in GATES],
        "superseded_round1_tests": [{"test": f"{T1}::{t}" if t.startswith("test") else t, "why": w}
                                    for t, w in SUPERSEDED_R1],
        "rule": "a gate passes only because production behaviour changed; never because a diagnostic register was "
                "redefined, a count was set to zero, an object was removed from admission or a benchmark was used"}
