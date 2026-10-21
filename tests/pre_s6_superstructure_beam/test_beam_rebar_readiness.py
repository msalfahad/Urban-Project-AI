"""PRE-S6 generic beam readiness (engine/source/beam_rebar_readiness.py): synthetic known-answer cases, no project.

Covers the PRE-S6 brief section 24 list: simple binding, ordered CB spans, duplicate tag, tag without band, band
without tag, width conflict, candidate-invariant / candidate-different, MID count known / length unknown, hanger
absent, continuous bar crossing a support, physical != schedule total, side-rebar ambiguity, stirrup count known /
path blocked, opening absent / present, provenance, conservation - plus the binding rules (distance never ranks, text
rotation alone never verifies) and the S5 principle (a verified straight run is not demoted).
"""

from __future__ import annotations

import pytest

from engine.source import beam_rebar_readiness as BR


def cand(member, *, d=400.0, ang=0.0, w=200.0, kind="LINE", others=(), adj=False, same=False, inside=True):
    return {"member_id": member, "kind": kind, "distance_mm": d, "within_extent": True, "member_dir_deg": ang,
            "width_mm": w, "span_other_marks": list(others), "same_mark_adjacent": adj, "same_mark_on_span": same,
            "inside_physical_extent": inside, "supported_both_ends": True}


TAG = {"handle": "A1", "mark": "B1", "rotation_deg": 0.0}


# ------------------------------------------------------------------------------------------------ binding
def test_simple_binding_single_candidate_is_verified():
    r = BR.binding_decision(TAG, [cand("L1")], schedule_width_mm=200)
    assert r["decision"] == "BOUND_VERIFIED" and r["member_id"] == "L1" and r["width_state"] == "MATCH"


def test_every_alternative_is_returned():
    r = BR.binding_decision(TAG, [cand("L1"), cand("L2", ang=90), cand("L3", d=2000)], schedule_width_mm=200)
    assert [c["member_id"] for c in r["candidates"]] == ["L1", "L2", "L3"]
    assert "DISTANCE" in next(c for c in r["candidates"] if c["member_id"] == "L3")["decisive_exclusions"]


def test_distance_never_ranks_two_survivors():
    r = BR.binding_decision(TAG, [cand("L1", d=100), cand("L2", d=900)], schedule_width_mm=200)
    assert r["decision"] == "BLOCKED_BINDING" and r["member_id"] is None


def test_text_rotation_alone_never_verifies():
    # the perpendicular member is excluded only by text rotation -> candidate, not verified
    r = BR.binding_decision(TAG, [cand("L1"), cand("L2", ang=90)], schedule_width_mm=200)
    assert r["decision"] == "BOUND_CANDIDATE" and r["rotation_only_alternatives"] == ["L2"]
    # ... unless the tag lies off that member's end, or that member already carries the same mark
    r = BR.binding_decision(TAG, [cand("L1"), cand("L2", ang=90, inside=False)], schedule_width_mm=200)
    assert r["decision"] == "BOUND_VERIFIED"
    r = BR.binding_decision(TAG, [cand("L1"), cand("L2", ang=90, same=True)], schedule_width_mm=200)
    assert r["decision"] == "BOUND_VERIFIED"


def test_schedule_width_gate_resolves_two_geometric_survivors():
    r = BR.binding_decision(TAG, [cand("L1", w=200), cand("L2", w=400)], schedule_width_mm=200)
    assert r["decision"] == "BOUND_VERIFIED" and r["member_id"] == "L1" and r["stage"] == 2


def test_same_mark_continuity_gives_a_candidate_only():
    r = BR.binding_decision(TAG, [cand("L1", adj=True), cand("L2")], schedule_width_mm=200)
    assert r["decision"] == "BOUND_CANDIDATE" and r["member_id"] == "L1"


def test_tag_without_band():
    assert BR.binding_decision(TAG, [], schedule_width_mm=200)["decision"] == "TAG_WITHOUT_GEOMETRY"


def test_span_claimed_by_another_mark_is_a_source_conflict():
    r = BR.binding_decision(TAG, [cand("L1", others=["CB3"])], schedule_width_mm=200)
    assert r["decision"] == "BOUND_SOURCE_CONFLICT" and r["member_id"] == "L1"


# ------------------------------------------------------------------------------------------------ width / terminals
@pytest.mark.parametrize("drawn,state", [(200, "MATCH"), (225, "MINOR_DRAFTING_DIFFERENCE"),
                                         (250, "SOURCE_CONFLICT"), (None, "UNRESOLVED")])
def test_width_match_states(drawn, state):
    w = BR.width_match(drawn, 200)
    assert w["WIDTH_MATCH_STATE"] == state and w["SCHEDULE_WIDTH"] == 200


def test_width_conflict_keeps_the_binding_and_conflicts_the_type_rebar():
    r = BR.binding_decision(TAG, [cand("L1", w=250)], schedule_width_mm=200)
    assert r["decision"] == "BOUND_VERIFIED" and r["width_state"] == "SOURCE_CONFLICT"
    t = BR.span_tag_terminals([{"handle": "A1", "mark": "B1", "decision": r["decision"],
                                "width_state": r["width_state"]}])
    assert t["terminals"]["A1"][0] == "BOUND_SOURCE_CONFLICT" and t["geometry"][0] == "BOUND_SOURCE_CONFLICT"
    assert BR.component_status(applicability="SOURCE_CONFLICT", count_dia_known=True, run_state="VERIFIED",
                               additions_blocked=True) == "SOURCE_CONFLICT"


def test_duplicate_tag_and_band_without_tag():
    t = BR.span_tag_terminals([{"handle": "1F", "mark": "B1", "decision": "BOUND_VERIFIED", "width_state": "MATCH"},
                               {"handle": "A0", "mark": "B1", "decision": "BOUND_VERIFIED", "width_state": "MATCH"}])
    assert t["terminals"]["1F"][0] == "BOUND_VERIFIED" and t["terminals"]["A0"][0] == "DUPLICATE_TAG"
    assert t["geometry"][0] == "BOUND_VERIFIED"
    assert BR.span_tag_terminals([])["geometry"][0] == "GEOMETRY_WITHOUT_TAG"


def test_two_marks_on_one_span_conflict_every_tag():
    t = BR.span_tag_terminals([{"handle": "1", "mark": "CB3", "decision": "BOUND_SOURCE_CONFLICT"},
                               {"handle": "2", "mark": "B3", "decision": "BOUND_SOURCE_CONFLICT"}])
    assert {v[0] for v in t["terminals"].values()} == {"BOUND_SOURCE_CONFLICT"}
    assert t["geometry"][0] == "BOUND_SOURCE_CONFLICT"


def test_conservation_every_object_exactly_once():
    ok = BR.terminate([{"object_id": "TAG:1", "kind": "TAG", "terminal": "BOUND_VERIFIED"},
                       {"object_id": "SPAN:1", "kind": "MEMBER_SPAN", "terminal": "GEOMETRY_WITHOUT_TAG"},
                       {"object_id": "FRAG:1", "kind": "BAND_FRAGMENT", "terminal": "NOT_BEAM"}])
    assert ok["all_terminate_once"]
    bad = BR.terminate([{"object_id": "TAG:1", "kind": "TAG", "terminal": "BOUND_VERIFIED"},
                        {"object_id": "TAG:1", "kind": "TAG", "terminal": "DUPLICATE_TAG"},
                        {"object_id": "SPAN:1", "kind": "MEMBER_SPAN", "terminal": "DUPLICATE_TAG"}])
    assert not bad["all_terminate_once"] and bad["duplicates"] == ["TAG:1"]
    assert bad["invalid_terminals"] == [("SPAN:1", "DUPLICATE_TAG")]


# ------------------------------------------------------------------------------------------------ CB spans
def test_cb_ordered_spans_forward_and_reversed():
    f = BR.span_sequence([{"cc_m": 7.45}, {"cc_m": 5.6}], [7.5, 5.7])
    assert f["state"] == "MATCH" and f["orientation"] == "FORWARD" and f["plan_order"] == [0, 1]
    r = BR.span_sequence([{"cc_m": 3.87}, {"cc_m": 3.9}, {"cc_m": 4.05}], [4.1, 4.0, 3.7])
    assert r["state"] == "MATCH" and r["orientation"] == "REVERSED" and r["plan_order"] == [2, 1, 0]
    assert [row["PLAN"]["cc_m"] for row in r["rows"]] == [4.05, 3.9, 3.87]


def test_cb_both_directions_match_is_ambiguous():
    a = BR.span_sequence([{"cc_m": 5.85}, {"cc_m": 6.15}], [6.0, 6.1])
    assert a["orientation"] == "AMBIGUOUS"


def test_physical_total_differs_from_schedule_total_both_kept():
    s = BR.span_sequence([{"cc_m": 2.724}, {"cc_m": 3.75}], [3.3, 3.7])
    assert s["state"] == "SPAN_LENGTH_SOURCE_CONFLICT" and s["orientation"] == "NONE"
    assert s["plan_total_cc_m"] == 6.474 and s["schedule_total_m"] == 7.0 and s["total_delta_m"] == -0.526
    assert s["rows"][0]["PLAN"]["cc_m"] == 2.724 and s["rows"][0]["SCHEDULE_SPAN_M"] == 3.3
    assert s["never_shared"] and s["never_capped"]


def test_cb_span_count_conflict():
    s = BR.span_sequence([{"cc_m": 6.5}, {"cc_m": 6.9}], [3.7, 6.4, 6.8])
    assert s["state"] == "SPAN_COUNT_CONFLICT" and len(s["rows"]) == 3


# ------------------------------------------------------------------------------------------------ CB bar runs
SPANS = [{"index": 1, "clear_m": 5.0, "cc_m": 5.5, "schedule_m": 5.5},
         {"index": 2, "clear_m": 4.0, "cc_m": 4.5, "schedule_m": 4.5},
         {"index": 3, "clear_m": 3.0, "cc_m": 3.5, "schedule_m": 3.5}]
SUPS = [{"index": k, "width_m": 0.5, "kind": "COLUMN", "ref": f"C{k}"} for k in range(4)]


def bar(handle, role, u0, u1, straddles, label=(3, 16), binding="ONE_TO_ONE_PRINTED"):
    return {"handle": handle, "role": role, "u_start": u0, "u_end": u1, "straddles": straddles,
            "start_at_support": u0 == 0.0, "end_at_support": u1 == 3.0, "legs": [],
            "label": {"count": label[0], "dia": label[1], "tag": "X", "kind": "ATTRIBUTE"} if label else None,
            "binding": binding}


def test_continuous_bar_crossing_supports_is_one_run():
    rules = {"by_bar": {"B2": {"bottom_extension": {"authority": "SOURCE_DERIVED_HIGH_CONFIDENCE", "value_m": 0.075,
                                                    "rule_id": "TYP:7.5cm"}}}}
    runs = BR.cb_bar_runs(occurrence_id="CB", frame_bars=[bar("B2", "BOTTOM", 0.933, 2.195, [1, 2])], spans=SPANS,
                          supports=SUPS, rules=rules)
    assert len(runs) == 1
    r = runs[0]
    assert r["INTERMEDIATE_SUPPORTS"] == [1, 2] and r["STRAIGHT_RUN_STATE"] == "LOWER_BOUND"
    kinds = [s["kind"] for s in r["STRAIGHT_SEGMENTS"]]
    assert kinds.count("THROUGH_SUPPORT") == 2 and kinds.count("CLEAR_SPAN") == 1
    assert r["STRAIGHT_RUN_M"] == pytest.approx(4.0 + 0.5 + 0.5 + 2 * 0.075)


def test_bottom_extension_needs_a_bound_rule():
    runs = BR.cb_bar_runs(occurrence_id="CB", frame_bars=[bar("B1", "BOTTOM", 0.0, 1.057, [1])], spans=SPANS,
                          supports=SUPS, rules={})
    r = runs[0]
    assert r["STRAIGHT_RUN_M"] == pytest.approx(5.0 + 0.5) and r["STRAIGHT_RUN_STATE"] == "LOWER_BOUND"
    assert any("no bound rule" in m for m in r["MISSING"]) and any("anchorage" in m for m in r["MISSING"])


def test_mid_bar_released_only_with_a_bound_extent_rule():
    rule = {"support_bar_each_side_factor": {"authority": "SOURCE_DERIVED_HIGH_CONFIDENCE", "value": 0.22,
                                             "span_basis": "cc_m", "rule_id": "TYP:0.22Ln"}}
    ok = BR.cb_bar_runs(occurrence_id="CB", frame_bars=[bar("M1", "SUPPORT_TOP", 0.699, 1.306, [1], (8, 18))],
                        spans=SPANS, supports=SUPS, rules={"by_bar": {"M1": rule}})[0]
    assert ok["STRAIGHT_RUN_STATE"] == "VERIFIED" and not ok["MISSING"]
    assert ok["STRAIGHT_RUN_M"] == pytest.approx(0.22 * 5.5 + 0.5 + 0.22 * 4.5)


def test_mid_count_known_length_unknown_is_blocked_unquantified():
    r = BR.cb_bar_runs(occurrence_id="CB", frame_bars=[bar("M1", "SUPPORT_TOP", 0.699, 1.755, [1], (3, 16))],
                       spans=SPANS, supports=SUPS, rules={})[0]
    assert r["COUNT"] == 3 and r["DIA_MM"] == 16
    assert r["STRAIGHT_RUN_STATE"] == "BLOCKED_UNQUANTIFIED" and r["STRAIGHT_RUN_M"] is None
    assert BR.component_status(applicability="OK", count_dia_known=True, run_state=r["STRAIGHT_RUN_STATE"],
                               additions_blocked=True) == "BLOCKED_COMPONENT"


def test_empty_schedule_cell_never_releases():
    rule = {"support_bar_each_side_factor": {"authority": "SOURCE_DERIVED_HIGH_CONFIDENCE", "value": 0.22,
                                             "span_basis": "cc_m", "rule_id": "TYP"}}
    r = BR.cb_bar_runs(occurrence_id="CB", frame_bars=[bar("M2", "SUPPORT_TOP", 1.697, 2.303, [2], None,
                                                           "EMPTY_SCHEDULE_CELL")],
                       spans=SPANS, supports=SUPS, rules={"by_bar": {"M2": rule}})[0]
    assert r["STRAIGHT_RUN_STATE"] == "BLOCKED_UNQUANTIFIED" and r["COUNT"] is None


def test_top_bar_with_no_extent_rule_stays_blocked():
    r = BR.cb_bar_runs(occurrence_id="CB", frame_bars=[bar("T1", "CONTINUOUS_TOP", 0.0, 0.943, [], (2, 12))],
                       spans=SPANS, supports=SUPS, rules={})[0]
    assert r["STRAIGHT_RUN_STATE"] == "BLOCKED_UNQUANTIFIED"


def test_unresolved_rule_is_never_applied():
    rule = {"bottom_extension": {"authority": "UNRESOLVED", "why": "'0.15L' names the wrong span"}}
    r = BR.cb_bar_runs(occurrence_id="CB", frame_bars=[bar("B2", "BOTTOM", 0.933, 2.195, [1, 2])], spans=SPANS,
                       supports=SUPS, rules={"by_bar": {"B2": rule}})[0]
    assert not any(s["kind"] == "BEYOND_FAR_FACE" for s in r["STRAIGHT_SEGMENTS"])
    assert any("0.15L" in m for m in r["MISSING"])


# ------------------------------------------------------------------------------------------------ simple runs
def test_simple_bar_run_face_to_face_and_s5_principle():
    run = BR.simple_bar_run(family_id="O:BOTTOM_MAIN", face_to_face_m=4.6, start_support="C1", end_support="C2",
                            geometry_state="CONSISTENT", extent_rule={"authority": "SOURCE_DERIVED_HIGH_CONFIDENCE",
                                                                      "rule_id": "R"})
    assert run["STRAIGHT_RUN_STATE"] == "VERIFIED" and run["STRAIGHT_RUN_M"] == 4.6
    # development blocked -> the complete bar is a LOWER_BOUND, the straight run stays VERIFIED (not demoted)
    st = BR.component_status(applicability="OK", count_dia_known=True, run_state=run["STRAIGHT_RUN_STATE"],
                             additions_blocked=True)
    assert st == "READY_LOWER_BOUND" and run["STRAIGHT_RUN_STATE"] == "VERIFIED"


def test_simple_bar_run_geometry_conflict_and_pattern_authority():
    c = BR.simple_bar_run(family_id="O", face_to_face_m=-0.1, start_support="C1", end_support="C2",
                          geometry_state="BAR_RUN_GEOMETRY_CONFLICT", extent_rule={"authority": "SOURCE_EXPLICIT"})
    assert c["STRAIGHT_RUN_STATE"] == "BAR_RUN_GEOMETRY_CONFLICT" and c["STRAIGHT_RUN_M"] is None
    p = BR.simple_bar_run(family_id="O", face_to_face_m=4.0, start_support="C1", end_support="C2",
                          geometry_state="CONSISTENT", extent_rule={"authority": "PROJECT_PATTERN_ONLY"})
    assert p["STRAIGHT_RUN_STATE"] == "BLOCKED_UNQUANTIFIED"


def test_candidate_binding_is_provisional_only():
    assert BR.component_status(applicability="OK", count_dia_known=True, run_state="VERIFIED",
                               additions_blocked=True, provisional=True) == "PROVISIONAL_ONLY"


# ------------------------------------------------------------------------------------------------ candidates
def test_candidate_invariant_and_different():
    assert BR.candidate_invariant({"A": (3, 16), "B": (3, 16)}) == {"state": "INVARIANT", "value": (3, 16)}
    assert BR.candidate_invariant({"A": (3, 16), "B": (4, 16)})["state"] == "DIFFERENT"
    assert BR.candidate_invariant({"A": (3, 16), "B": "UNDEFINED"})["state"] == "UNDEFINED"


# ------------------------------------------------------------------------------------------------ hangers / side / stirrups
def test_hanger_absent_and_unlabelled_never_invented():
    assert BR.hanger_readiness(scheduled=None, detailed=None)["state"] == "ABSENT"
    u = BR.hanger_readiness(scheduled=None, detailed={"count": None, "dia_mm": None})
    assert u["state"] == "DETAILED_UNLABELLED" and u["count"] is None
    s = BR.hanger_readiness(scheduled={"count": 2, "dia_mm": 12}, detailed=None)
    assert s["state"] == "EXPLICITLY_SCHEDULED" and s["count"] == 2


def test_side_rebar_spacing_is_not_interpreted():
    tok = {"raw": "2%%C12/30cm", "count": 2, "dia_mm": 12, "spacing_cm": 30, "text_handle": "T"}
    r = BR.side_rebar_readiness(token=tok, depth_cm=75, note_threshold_cm=60)
    assert r["state"] == "BLOCKED_COMPONENT" and r["faces"] == "NOT_STATED"
    assert "AMBIGUOUS" in r["count_semantics"]
    assert BR.side_rebar_readiness(token=None, depth_cm=40, note_threshold_cm=60)["state"] == "NOT_APPLICABLE"
    assert BR.side_rebar_readiness(token=None, depth_cm=75, note_threshold_cm=60)["state"] == "BLOCKED_COMPONENT"


def test_stirrup_count_known_path_blocked():
    r = BR.stirrup_readiness(dia_mm=8, rate_per_m=6, rate_state="SOURCE_EXPLICIT", distribution_m=4.6,
                             width_state="MATCH", depth_known=True, cover_known=True,
                             topology={"state": "UNRESOLVED"}, hooks_state="BLOCKED_UNQUANTIFIED",
                             end_zone={"state": "NOT_STATED"}, first_last={"state": "NOT_STATED"})
    assert r["COUNT"] == {"value": 28, "state": "LOWER_BOUND", "distribution_m": 4.6,
                          "formula": "ceil(6/m x 4.600 m) = 28"}
    assert r["SECTION_PATH"]["state"] == "BLOCKED_UNQUANTIFIED" and r["MASS"]["state"] == "BLOCKED_UNQUANTIFIED"


# ------------------------------------------------------------------------------------------------ openings
def test_opening_absent_and_present():
    assert BR.opening_components([]) == [{"COMPONENT_FAMILY": "OPENING_EXTRA", "STATE": "NOT_APPLICABLE"}]
    assert BR.opening_components([{"relation": "ON_FACE"}, {"relation": "LINEWORK_ENTERS_BAND"}])[0]["STATE"] == \
        "NOT_APPLICABLE"
    p = BR.opening_components([{"member": "L1", "relation": "INSIDE_BAND"}])
    assert [c["COMPONENT_FAMILY"] for c in p] == ["OPENING_EXTRA_TOP", "OPENING_EXTRA_BOTTOM",
                                                  "OPENING_EXTRA_SIDE", "STIRRUP_EXTRA"]


# ------------------------------------------------------------------------------------------------ typical dimensions
def test_dimension_binds_only_on_bar_end_and_face():
    ends = [{"bar": "M", "x": 100.0}, {"bar": "M", "x": 900.0}]
    b = BR.bind_dimension_rule({"handle": "D1", "text": "0.22 Ln", "p2": 100.0, "p3": 300.0}, bar_ends=ends,
                               faces=[300.0, 400.0], axes=[350.0])
    assert b["bound"] and b["bar"] == "M" and b["measured_from"] == "FACE"
    u = BR.bind_dimension_rule({"handle": "D2", "text": "0.15L", "p2": 150.0, "p3": 300.0}, bar_ends=ends,
                               faces=[300.0], axes=[])
    assert not u["bound"] and u["state"] == "UNRESOLVED"


# ------------------------------------------------------------------------------------------------ provenance
CTX = {"PROJECT_ID": "P", "DRAWING_ID": "D", "DRAWING_SHA": "x" * 64, "ENGINE_COMMIT": "c", "REGISTER_VERSION": "V",
       "CALCULATION_ROUND": "PRE_S6"}


def _prov(sub, run=None):
    return BR.provenance_template(context=CTX, occurrence_id="O1", mark="B1", subfamily=sub, source_handles=["1"],
                                  schedule_handles=["2"], geometry_handles=["3"], support_ids=["C1", "C2"],
                                  detail_id="SBT:2", rule_id="R", convention_id="C", authority="SOURCE_EXPLICIT",
                                  release_state="READY_LOWER_BOUND", bar_run_id=run)


def test_provenance_template_generic_identity():
    t = _prov("SIMPLE_BEAM", "O1:BOTTOM_MAIN")
    assert BR.provenance_ready(t) and t["ELEMENT_FAMILY"] == "BEAM"
    assert not any(k.startswith("FOOTING_") for k in t)
    assert not BR.provenance_ready(_prov("CONTINUOUS_BEAM"))          # a CB component needs its BAR_RUN_ID
    assert BR.provenance_ready(_prov("CONTINUOUS_BEAM", "O1:BOTTOM:H1"))
    bad = dict(t, FOOTING_ID="F1")
    assert not BR.provenance_ready(bad)


def test_policy_never_borrows_slab_rules():
    rules = " ".join(BR.policy_record()["rules"])
    assert "0.25L / 0.30L rules are never borrowed" in rules and "no kg" in rules
