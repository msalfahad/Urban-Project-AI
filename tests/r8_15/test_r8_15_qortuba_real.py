"""R8.15 on the committed registers: duct authority, passage heads, marble thresholds, the skirting row, reveals,
US-07, six-row provenance, digests and gates."""

from __future__ import annotations

import json
from pathlib import Path

from engine.source import door_transition as DT, marble_thresholds as MT, obstacle_authority as OA
from engine.source import opening_reveals as OR, owner_facts as OF, trade_strips as TS, wall_contact_path as WC

REG = Path(__file__).parent / "registers"
ROWS = ("Q-03", "Q-03P", "Q-11", "Q-12", "Q-13", "Q-14")


def _r(n):
    return json.loads((REG / f"{n}.json").read_text())


# ------------------------------------------------------------------------------- duct
def test_the_duct_is_owner_obstacle_authority_and_its_footprint_comes_from_source():
    d = _r("DUCT_AUTHORITY_REGISTER")
    assert {v["state"] for v in d["entity_authority"].values()} == {OA.OWNER_PHYSICAL_OBSTACLE}
    assert d["footprint_from_source_m2"]["agree"]
    assert set(d["old_revision"].values()) == {OA.UNPROVEN_OBSTACLE}               # scope never transfers
    for rid in ("Q-13", "Q-14"):
        v = _r("QORTUBA_R8_15_STATUS")["six_rows"][rid]
        assert not any(b.startswith("OBSTACLE_AUTHORITY_UNPROVEN") for b in v["RELEASE_BLOCKERS"])
        assert v["DUCT_TREATMENT"] and all(x["authorised"] for x in v["DUCT_TREATMENT"])


# ------------------------------------------------------------------------------- passages
def test_two_passages_two_head_conditions_and_qp18_unused():
    p = {x["passage"]: x for x in _r("PASSAGE_HEAD_REGISTER")["passages"]}
    heads = sorted(x["head"] for x in p.values() if x["head"])
    assert heads == [OR.FULL_HEIGHT, OR.WITH_HEAD]
    full = next(x for x in p.values() if x["head"] == OR.FULL_HEIGHT)
    assert full["ceiling"] == "CEILING_CONTINUES" and full["authority"].startswith("QORTUBA-NEW-MB-DRESS")
    q14 = _r("Q14_STATUS")
    st = {x["strip"]: x["state"] for x in q14["PASSAGE_TREATMENT"]}
    assert st[full["passage"]] == TS.INCLUDED
    assert not any(b.startswith("PASSAGE_HEAD_CONDITION_NOT_ESTABLISHED") for b in q14["RELEASE_BLOCKERS"])
    assert round(q14["BASE_SITE_AREA_M2"] - q14["SOFFIT_EXCLUSION_M2"], 4) == q14["VALUE"]


# ------------------------------------------------------------------------------- marble
def test_marble_thresholds_full_strip_counted_once_with_the_right_authority():
    m = _r("MARBLE_THRESHOLD_REGISTER")
    for t in m["thresholds"]:
        assert t["state"] == MT.COMPUTED and t["plan_area_m2"] == t["width_x_depth_m2"]
        assert t["counted_once"] and t["trade"] == MT.TRADE
        if t["authority_kind"] == MT.RULE:
            assert t["vertical_rise_mm"] == 20 and t["water_containment"] and "BATHROOM" in t["room_types"].values()
        else:
            assert t["project_specific_entrance"] and t["vertical_rise_mm"] == MT.NOT_STATED
            assert not t["water_containment"]
        assert t["depth_mm"] != 20
    q = m["quantities"]
    assert q["count"] == len(m["thresholds"]) and q["blocked"] == []
    assert abs(q["MARBLE_THRESHOLD_PLAN_AREA_M2"] - sum(t["plan_area_m2"] for t in m["thresholds"])) < 1e-9


def test_no_half_tile_survives_inside_a_marble_strip_and_every_threshold_reconciles():
    s = _r("QORTUBA_R8_15_STATUS")
    for t in s["threshold_audit"]:
        assert t["reconciles"]
        if t["allocation_state"] == DT.MARBLE:
            assert [r["treatment"] for r in t["regions"]] == [DT.MARBLE]
    assert {t["classification"] for t in s["threshold_audit"]} <= {
        "URBAN_WET_SERVICE_MARBLE_RULE", "MAIN_ENTRANCE_MARBLE_EXPLICIT", "DRY_DRY_CONTINUOUS_PORCELAIN",
        "OUTSIDE_MEASURED_SCOPE"}
    for rid in ("Q-03", "Q-11", "Q-13"):
        v = s["six_rows"][rid]
        assert all(x["row_contribution_m2"] == 0 for x in v["MARBLE"]["thresholds"])


def test_the_entrance_is_explicit_marble_and_leaves_no_porcelain_in_q13():
    e = _r("MAIN_ENTRANCE_THRESHOLD_REGISTER")
    assert e["marble"]["authority_kind"] == MT.EXPLICIT and e["q13_porcelain_from_threshold_m2"] == 0
    assert not any(b.startswith("UNIT_BOUNDARY_THRESHOLD") for b in _r("Q13_STATUS")["RELEASE_BLOCKERS"])


def test_the_marble_rule_reads_a_trade_scoped_room_type_map():
    r = _r("OWNER_METHOD_RULE_REGISTER")
    assert r["rules"][0]["ref"] == "URBAN-WET-SERVICE-MARBLE-THRESHOLD@v1"
    assert r["room_type_map_for_marble"]["PAINTRY"][0] != "KITCHEN"


# ------------------------------------------------------------------------------- skirting
def test_the_skirting_row_is_the_frozen_blind_result_with_provenance():
    s = _r("SKIRTING_REGISTER")
    b = _r("BLIND_QORTUBA_SKIRTING_RESULT")
    assert s["state"] == "COMPUTED_SHADOW" and s["reproduces_blind"] and s["SKIRTING_LM"] == b["SKIRTING_LM"]
    assert abs(sum(s["components_lm"].values()) - s["SKIRTING_LM"]) < 1e-6
    assert s["method"] == _r("R8_15_SKIRTING_FREEZE")["qortuba_method"]["ref"]
    assert any(b.startswith("JAMB_RETURN_METHOD_INFERRED") for b in s["release_blockers"])
    for v in s["per_room"].values():
        if "BATH" in v["zones"] or "PAINTRY" in v["zones"]:
            assert v["state"] == WC.NO_SKIRTING and v["lm"] == 0.0
        else:
            assert v["state"] == WC.COMPUTED and v["withheld"] == []
    assert s["components_lm"][WC.OBSTACLE_FACE] > 0 and s["excluded_lm"][WC.WINDOW_OPENING] > 0


# ------------------------------------------------------------------------------- reveals / US-07
def test_reveals_use_source_depth_and_us07_is_fallback_only():
    u = _r("US07_REVEAL_DEPTH_REVIEW")
    assert u["recommendation"].startswith("US-07 0.25 m becomes FALLBACK-ONLY")
    assert all(x["used"] == OR.SOURCE_DEPTH for x in u["surfaces"])
    rv = _r("OPENING_REVEAL_REGISTER")["passages"]
    full = next(v for v in rv.values() if v["head"] == OR.FULL_HEIGHT)
    assert not [s for s in full["surfaces"] if s["surface"] == OR.TOP_SOFFIT]
    assert full["ownership"]["CEILING_EXCLUDES_M2"] == 0.0


# ------------------------------------------------------------------------------- rows / digests / gates
def test_six_rows_compute_in_shadow_from_their_parts():
    six = _r("QORTUBA_R8_15_STATUS")["six_rows"]
    for rid, v in six.items():
        assert v["STATE"] == "COMPUTED_SHADOW" and v["final"] is False
        assert round(v["BASE_SITE_AREA_M2"] + v["THRESHOLD_CONTRIBUTION_M2"] - v["SOFFIT_EXCLUSION_M2"], 4) == v["VALUE"]
        assert any(b.startswith("SOURCE_ANCHOR") for b in v["RELEASE_BLOCKERS"])
    assert six["Q-03"]["VALUE"] == six["Q-11"]["VALUE"] == six["Q-03"]["BASE_SITE_AREA_M2"]
    assert six["Q-03P"]["THRESHOLD_TREATMENT"] == [] and six["Q-12"]["THRESHOLD_TREATMENT"] == []


def test_the_door_without_a_threshold_site_is_disclosed_not_hidden():
    s = _r("QORTUBA_R8_15_STATUS")
    for d in s["doors_without_threshold_site"]:
        assert d["closure_b"] is None and d["reveal_area_m2"] > 0
    if s["doors_without_threshold_site"]:
        q14 = _r("Q14_STATUS")
        assert any(b.startswith("DOOR_REVEAL_INSIDE_ROOM_SITE") for b in q14["RELEASE_BLOCKERS"])
        assert q14["COUNTERFACTUALS"]["counterfactual_door_reveal_excluded"] < q14["VALUE"]


def test_topology_unchanged_old_revision_unchanged_and_gates():
    d = _r("DIGEST_HIERARCHY")
    assert all(v["TOPOLOGY_RUN_INPUT_DIGEST"] == "SAME" for v in d["vs_r8_14"].values())
    s = _r("QORTUBA_R8_15_STATUS")
    assert all(s["old_revision_unchanged_vs_r8_14"].values()) and all(s["lab_reproduces_blind_v5"].values())
    f = _r("OWNER_PHYSICAL_FACT_REGISTER")
    assert all(x["binding"]["OLD_K1"] == OF.REJECTED_SCOPE for x in f["facts"])
    dr = _r("R8_15_DECISION_REGISTER")
    assert dr["gates"] == {"MIGRATION_PLANNING_READY": "YES", "MIGRATION_EXECUTION_READY": "NO",
                           "PRODUCTION_MIGRATION": "NO"} and len(dr["answers"]) == 34
    assert _r("OWNER_ACTION_REGISTER")["headline"] == "NO OWNER ACTION REQUIRED."
    assert _r("CLOSURE_RELEASE_STATUS")["released"] == [] and _r("SOURCE_ANCHOR_STATUS")["state"] == "NOT_ESTABLISHED"
