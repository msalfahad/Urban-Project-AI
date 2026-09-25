"""PROJECT_3_ENTRY_GATE_V3 (PA07): thirteen conditions evaluated from the PA07 registers, the independent validation
result, the benchmark scan and the cold review.  READY_FOR_CONTROLLED_DRAFT_ONLY when every condition holds;
NOT_READY otherwise.  A missing independent source is a correct NOT_READY, not a failure of the phase."""

from __future__ import annotations

CONDITIONS = ("FM_P6_01_CLOSED_WRONG_FAMILIES_NEVER_WALLS", "FM_P6_02_CLOSED_WALL_INTERIORS_SEALED", "FM_P6_03_CLOSED_CURVED_BANDS_HOST_SITES", "FM_P6_10_CLOSED_NO_SEED_DEPENDENCE",
              "INDEPENDENT_VALIDATION_EXECUTED_ON_INDEPENDENT_SOURCE", "NO_CRITICAL_MISMATCH_IN_VALIDATION", "WRONG_TOPOLOGY_IS_CORRECT_OR_LOUD", "BRIDGE_EMITS_NOTHING_FROM_UNRESOLVED_TOPOLOGY",
              "UNIT_GATE_PASSES", "SOURCE_AUDIT_PASSES", "FREEZE_REVERSIBILITY_PASSES", "BENCHMARK_LEAKAGE_SCAN_CLEAN", "COLD_REVIEW_FINDS_NO_SILENT_PATH")


def evaluate(*, registers, validation_result, review, benchmark_scan, tests_pass):
    qa = registers["PA07_QA_REPORT"]
    safety = registers["PA07_QUANTITY_SAFETY_REGISTER"]
    trace = registers["PA07_QUANTITY_INPUT_TRACE"]["LINES"]
    sites = registers["PA07_OPENING_SITE_REGISTER"]
    bands = registers["PA07_MATERIAL_BAND_REGISTER"]
    tmr = registers["PA07_TRADE_MEASUREMENT_REGION_REGISTER"]
    t = tests_pass

    def passed(*names):
        return all(t.get(n, False) for n in names)
    band_tests = ("test_01_two_parallel_window_frame_lines_are_not_a_wall", "test_02_stair_treads_beside_a_wall_are_a_repetition_family", "test_03_hatch_strokes_with_wall_like_spacing_are_not_walls",
                  "test_04_furniture_rectangle_is_not_a_wall_or_a_column", "test_05_glazing_frame_lines_are_not_a_wall", "test_11_tapering_decorative_element_is_not_a_wall", "test_15_tiny_drafting_offsets_and_line_doubling",
                  "test_hidden_linetype_and_invisible_entities_are_never_faces")
    seal_tests = ("test_single_face_gap_is_never_a_doorway", "test_both_faces_interrupted_without_any_evidence_is_unresolved_not_merged", "test_seals_close_every_interval_and_carry_no_material", "test_open_plan_doorway_and_missing_leaf_relations")
    curved_tests = ("test_c1_semicircular_wall_no_opening", "test_c2_curved_wall_with_door", "test_c3_curved_wall_with_window", "test_c7_small_unresolved_arc_gap", "test_c8_tangent_transition_curved_to_straight")
    seed_tests = ("test_narrow_rooms_0_60_and_0_40_m_exist", "test_triangular_rotated_l_shaped_concave_rooms", "test_corner_gaps_2_5_10_25_mm_keep_one_room", "test_region_touching_border_and_courtyard_and_shaft")
    # bridge emits nothing from unresolved topology: every line whose space has unresolved relations or a non-established site is blocked
    leaks = [l for l in trace if l.get("QUANTITY_STATUS") not in ("NOT_ESTABLISHED", "HUMAN_REVIEW", "SOURCE_REQUIRED", "NOT_APPLICABLE") and l.get("BLOCKED_BY") == [] and
             (l.get("REGION_STATUS") not in ("MEASUREMENT_REGION_CLOSED", "MEASUREMENT_RUN_ESTABLISHED"))]
    # PA07R1 (FM-P7-15): recompute from the space register: an allowed line's space must have no unresolved relation and an established boundary
    spaces = {s["SPACE_ID"]: s for s in registers.get("PA07_PHYSICAL_SPACE_REGISTER", {}).get("ROWS", [])}
    for r in safety["ROWS"]:
        if not r["BLOCKED_BY"]:
            sp = spaces.get(r["SPACE_ID"], {})
            if sp.get("UNRESOLVED_RELATIONS") or sp.get("GEOMETRY_STATUS") != "ESTABLISHED" or sp.get("UNRESOLVED_MM", 0) > 0:
                leaks.append({"LINE_ID": r["SAFETY_ID"], "WHY": "allowed line on a space with unresolved topology"})
    exercised = t.get("test_pipeline7_end_to_end_formed_region_and_blocked_unresolved", False)
    unresolved_sites = sites["BY_STATUS"].get("INSUFFICIENT_EVIDENCE", 0) + sites["BY_STATUS"].get("SINGLE_FACE_GAP", 0) + sites["BY_STATUS"].get("OPEN_PASSAGE_CANDIDATE", 0)
    loud = all(r["REJECTION_REASON"] for r in bands["ROWS"] if r["MATERIAL_STATUS"] != "ACCEPTED") and all(s.get("STATUS") and s.get("REASON") for s in sites["ROWS"])   # every non-accepted band and every site carries its reason
    critical = [f for f in (review or {}).get("FAILURE_MODES", []) if f.get("SEVERITY") == "CRITICAL" and f.get("BLOCKS_PROJECT_3")]
    silent = [f for f in (review or {}).get("FAILURE_MODES", []) if f.get("DETECTION") == "SILENT" and f.get("SEVERITY") in ("CRITICAL", "HIGH") and f.get("PRODUCES_WRONG_QUANTITY", True)]
    vr = validation_result or {}
    rows = [
        ("FM_P6_01_CLOSED_WRONG_FAMILIES_NEVER_WALLS", passed(*band_tests), {"TESTS": band_tests}),
        ("FM_P6_02_CLOSED_WALL_INTERIORS_SEALED", passed(*seal_tests), {"TESTS": seal_tests}),
        ("FM_P6_03_CLOSED_CURVED_BANDS_HOST_SITES", passed(*curved_tests), {"TESTS": curved_tests}),
        ("FM_P6_10_CLOSED_NO_SEED_DEPENDENCE", passed(*seed_tests), {"TESTS": seed_tests}),
        ("INDEPENDENT_VALIDATION_EXECUTED_ON_INDEPENDENT_SOURCE", vr.get("STATUS") == "EXECUTED" and vr.get("SOURCE_INDEPENDENT") is True, {"STATUS": vr.get("STATUS"), "SOURCE": vr.get("SOURCE_SET")}),
        ("NO_CRITICAL_MISMATCH_IN_VALIDATION", vr.get("STATUS") == "EXECUTED" and not vr.get("CRITICAL_MISMATCHES"), {"CRITICAL_MISMATCHES": vr.get("CRITICAL_MISMATCHES")}),
        ("WRONG_TOPOLOGY_IS_CORRECT_OR_LOUD", loud and passed("test_both_faces_interrupted_without_any_evidence_is_unresolved_not_merged", "test_three_parallel_lines_without_fill_or_caps_stay_unresolved"),
         {"BANDS_UNRESOLVED": bands["SUMMARY"]["UNRESOLVED"], "BANDS_REJECTED": bands["SUMMARY"]["REJECTED"], "SITES_NOT_ESTABLISHED": unresolved_sites}),
        ("BRIDGE_EMITS_NOTHING_FROM_UNRESOLVED_TOPOLOGY", not leaks and all(l["BARE_NUMBER"] is False for l in trace) and safety["BRIDGE_ALLOWED"] == sum(1 for r in safety["ROWS"] if not r["BLOCKED_BY"]) and exercised,
         {"LEAKS": [l["LINE_ID"] for l in leaks], "BRIDGE_ALLOWED": safety["BRIDGE_ALLOWED"], "BLOCKED_BY_GATE": safety["BLOCKED_BY_GATE"], "EXERCISED_BY_END_TO_END_TEST": exercised, "NOTE": "vacuous on a project with zero allowed lines; the end-to-end synthetic test must show a formed region and a blocked unresolved room"}),
        ("UNIT_GATE_PASSES", all(qa["UNITS_ACCEPTABLE"].values()) if qa["UNITS_ACCEPTABLE"] else False, qa["UNITS_ACCEPTABLE"]),
        ("SOURCE_AUDIT_PASSES", registers.get("PA07_SOURCE_AUDIT", {}).get("PASS") is True and bool(registers.get("PA07_SOURCE_AUDIT", {}).get("SOURCES")), registers.get("PA07_SOURCE_AUDIT", {})),
        ("FREEZE_REVERSIBILITY_PASSES", (tmr["REVERSIBILITY"]["ALL_REVERSIBLE"] is True or (tmr["COUNT"] == 0 and exercised)) and (tmr["REVERSIBILITY"]["ALL_ZERO_MATERIAL"] is True or (tmr["COUNT"] == 0 and exercised)) and passed("test_seals_close_every_interval_and_carry_no_material"),
         {"REGIONS": tmr["COUNT"], "REVERSIBILITY": tmr["REVERSIBILITY"], "EXERCISED_BY_END_TO_END_TEST": exercised, "NOTE": "with zero regions on the project the property is shown by the end-to-end synthetic test, never assumed"}),
        ("BENCHMARK_LEAKAGE_SCAN_CLEAN", benchmark_scan.get("CLEAN") is True, {"HITS": benchmark_scan.get("HITS")}),
        ("COLD_REVIEW_FINDS_NO_SILENT_PATH", review is not None and not silent and not critical, {"REVIEW_PRESENT": review is not None, "SILENT": [f.get("ID") for f in silent], "CRITICAL": [f.get("ID") for f in critical]}),
    ]
    out = [{"CONDITION": c, "PASS": bool(p), "EVIDENCE": e} for c, p, e in rows]
    failed = [r["CONDITION"] for r in out if not r["PASS"]]
    return {"ARTIFACT": "PA07_PROJECT_3_ENTRY_GATE_V3", "CONDITIONS": out, "FAILED": failed,
            "VERDICT": "READY_FOR_CONTROLLED_DRAFT_ONLY" if not failed else "NOT_READY",
            "NOTE": "NOT_READY because no independent second source exists is the correct result of the phase, not a failure of it" if "INDEPENDENT_VALIDATION_EXECUTED_ON_INDEPENDENT_SOURCE" in failed else None}
