"""R8.14 on the committed registers: door thresholds allocated and reconciled, the Hall / Lobby soffit out of the
ceiling, skirting readiness without a quantity, V4-O1 / V4-O2, the V5 status, six-row provenance, digests and gates."""

from __future__ import annotations

import json
from pathlib import Path

from engine.source import door_transition as DT, opening_reveals as OR, trade_strips as TS, wall_bands as WB

REG = Path(__file__).parent / "registers"
ROWS = ("Q-03", "Q-03P", "Q-11", "Q-12", "Q-13", "Q-14")


def _r(n):
    return json.loads((REG / f"{n}.json").read_text())


# ------------------------------------------------------------------------------- thresholds
def test_every_threshold_is_one_physical_site_whose_parts_sum_exactly():
    t = _r("DOOR_THRESHOLD_REGISTER")
    assert t["reconciled_exactly"] and t["count"] == len(t["thresholds"])
    for x in t["thresholds"]:
        if x["regions"]:
            assert sum(r["area_m2"] for r in x["regions"]) == x["strip_m2"] or \
                abs(sum(r["area_m2"] for r in x["regions"]) - x["strip_m2"]) < 1e-9
        assert len({r["side"] for r in x["regions"]}) == len(x["regions"])


def test_no_leaf_plane_is_invented_from_a_face_anchored_symbol():
    for x in _r("DOOR_THRESHOLD_REGISTER")["thresholds"]:
        assert x["symbol"] == DT.SYMBOL_AT_FACE and abs(x["hinge_offset_mm"]) < 0.01
        assert x["transition_plane_authority"] == DT.OWNER_CENTRED_DOOR
        assert x["plane_fact"].startswith("QORTUBA-NEW-DRY-WET-TRANSITION-AT-DOOR-PLANE-OWNER-001")


def test_dry_wet_split_at_the_plane_dry_dry_continuous_and_no_marble():
    t = _r("DOOR_THRESHOLD_REGISTER")
    for x in t["thresholds"]:
        if x["allocation_state"] == DT.SPLIT:
            assert {r["side"] for r in x["regions"]} == {"A", "B"}
            assert x["regions"][0]["treatment"] != x["regions"][1]["treatment"]
        if x["allocation_state"] == DT.CONTINUOUS:
            assert len(x["regions"]) == 1 and x["regions"][0]["side"] == "AB"
        assert x["marble_evidence"] == "NONE" and x["allocation_state"] != DT.MARBLE
    assert _r("MARBLE_THRESHOLD_EVIDENCE")["result"] == "NO EXPLICIT MARBLE THRESHOLD EVIDENCE FOUND"


def test_no_threshold_blocks_and_the_outside_one_is_in_no_row():
    t = _r("DOOR_THRESHOLD_REGISTER")
    states = {x["allocation_state"] for x in t["thresholds"]}
    assert states <= set(DT.RESOLVED) | {"OUTSIDE_MEASURED_UNIT"}
    for x in t["thresholds"]:
        if x["allocation_state"] == "OUTSIDE_MEASURED_UNIT":
            assert x["receiving_rows"] == {} and x["sides_outside_unit"] == ["A", "B"]
    for v in _r("QORTUBA_R8_14_STATUS")["six_rows"].values():
        assert not any(b.startswith("STRIP_ALLOCATION") for b in v["RELEASE_BLOCKERS"])


def test_the_unit_boundary_split_is_disclosed_with_counterfactuals():
    t = [x for x in _r("DOOR_THRESHOLD_REGISTER")["thresholds"] if x["unit_boundary"]]
    q13 = _r("Q13_STATUS")
    if t:
        assert any(b.startswith("UNIT_BOUNDARY_THRESHOLD") for b in q13["RELEASE_BLOCKERS"])
        cf = q13["COUNTERFACTUALS"]["counterfactual_unit_boundary"]
        assert cf["unit_floor_stops_at_unit_face"] < cf["split_at_door_plane (computed)"] < cf["whole_strip_to_unit"]


def test_ceiling_takes_no_door_threshold():
    q14 = _r("Q14_STATUS")
    assert q14["THRESHOLD_CONTRIBUTION_M2"] == 0
    assert all(x["state"] == TS.NOT_IN_TRADE for x in q14["THRESHOLDS"])


def test_each_receiving_row_gets_exactly_its_regions():
    t = _r("DOOR_THRESHOLD_REGISTER")
    six = _r("QORTUBA_R8_14_STATUS")["six_rows"]
    for rid in ROWS:
        got = sum(x["receiving_rows"].get(rid, 0) for x in t["thresholds"])
        assert abs(got - six[rid]["THRESHOLD_CONTRIBUTION_M2"]) < 1e-9
    total = sum(x["strip_m2"] for x in t["thresholds"] if x["allocation_state"] in DT.RESOLVED)
    inside = sum(r["area_m2"] for x in t["thresholds"] for r in x["regions"] if r["treatment"] != "OUTSIDE_MEASURED_UNIT")
    outside = sum(r["area_m2"] for x in t["thresholds"] for r in x["regions"] if r["treatment"] == "OUTSIDE_MEASURED_UNIT")
    assert abs(inside + outside - total) < 1e-9
    assert abs(sum(six[r]["THRESHOLD_CONTRIBUTION_M2"] for r in ("Q-03", "Q-13")) - inside) < 1e-9


# ------------------------------------------------------------------------------- soffit / reveals
def test_q14_is_the_ceiling_sites_minus_the_soffit_footprint():
    q14 = _r("Q14_STATUS")
    so = _r("SOFFIT_ALLOCATION_POLICY")
    assert so["hall_lobby_audit"]["state"] == TS.SOFFIT_EXCLUDED
    assert round(q14["BASE_SITE_AREA_M2"] - so["q14_exclusion_m2"], 4) == q14["VALUE"]
    assert abs(so["q14_exclusion_m2"] - so["footprint_m2_from_source"]) < 1e-6
    assert so["double_count_guard"].startswith("PASS")


def test_reveal_surfaces_are_plaster_owned_once_and_no_paint():
    rv = _r("OPEN_PASSAGE_REVEAL_REGISTER")
    assert {s["surface"] for s in rv["surfaces"]} == {OR.LEFT_JAMB, OR.RIGHT_JAMB, OR.TOP_SOFFIT}
    assert all(s["finish"] == "PLASTER" and s["trade"] == "PLASTER" for s in rv["surfaces"])
    assert rv["paint"].startswith("NOT ASSUMED") and rv["ownership_guard_double_claims"] == []
    assert rv["hall_lobby"]["ownership"]["CEILING_STATE"] == "SOFFIT_FOOTPRINT_REMOVED"


def test_the_other_passage_head_is_a_release_blocker_not_a_silent_inclusion():
    q14 = _r("Q14_STATUS")
    if q14["PASSAGE_TREATMENT"]["head_unresolved"]:
        assert any(b.startswith("PASSAGE_HEAD_CONDITION_NOT_ESTABLISHED") for b in q14["RELEASE_BLOCKERS"])


# ------------------------------------------------------------------------------- skirting
def test_skirting_is_classified_but_no_quantity_is_published():
    s = _r("SKIRTING_READINESS")
    assert s["quantity"] == "NOT PRODUCED" and s["never_used"] == "a room polygon perimeter"
    assert s["missing_components"]
    m = _r("SKIRTING_METHOD_POLICY")
    assert m["behind_wardrobes"].startswith("YES") and m["across_doors_passages"].startswith("NO")


# ------------------------------------------------------------------------------- V4-O1 / V4-O2 / V5
def test_v4_o1_is_a_geometric_candidate_and_a_disclosed_release_blocker():
    o = _r("V4_O1_REGISTER")
    assert {c["authority"]["state"] for c in o["v5_band_state"]["geometric_candidates"]} == {WB.GEOMETRIC_CANDIDATE}
    assert o["material"] and o["state"].startswith("UNRESOLVED")
    for rid in o["rows_affected"]:
        v = _r("QORTUBA_R8_14_STATUS")["six_rows"][rid]
        assert any(b.startswith("OBSTACLE_AUTHORITY_UNPROVEN") for b in v["RELEASE_BLOCKERS"])
        assert o["counterfactual_if_not_an_obstacle"][rid] > v["VALUE"]


def test_v4_o2_is_deterministic_and_v5_is_frozen_and_reproduced():
    assert _r("V4_O2_REGISTER")["state"].startswith("RESOLVED")
    w = _r("WALL_BAND_POLICY_STATUS")
    assert w["policy"]["policy_id"] == "WALL_BAND_POLICY_V5"
    assert w["policy"]["digest"] == _r("R8_14_V5_FREEZE")["wall_band_policy"]["digest"]
    assert all(w["lab_reproduces_blind"].values()) and all(w["determinism"].values())
    assert sorted(x["separated_m2"][0] for x in w["h2430_h2431"]) == [0.3813, 0.6494]
    assert w["h1316"].startswith("NOT_WALL_CAP") and w["hall_m2"] == 42.7993


# ------------------------------------------------------------------------------- rows / digests / gates
def test_six_rows_compute_in_shadow_with_value_from_their_parts():
    six = _r("QORTUBA_R8_14_STATUS")["six_rows"]
    for rid, v in six.items():
        assert v["STATE"] == "COMPUTED_SHADOW" and v["final"] is False
        assert round(v["BASE_SITE_AREA_M2"] + v["THRESHOLD_CONTRIBUTION_M2"] -
                     v["PASSAGE_TREATMENT"]["soffit_exclusion_m2"], 4) == v["VALUE"]
        assert any(b.startswith("SOURCE_ANCHOR") for b in v["RELEASE_BLOCKERS"])
    assert six["Q-03"]["VALUE"] == six["Q-11"]["VALUE"] and six["Q-03P"]["VALUE"] == six["Q-12"]["VALUE"]
    assert six["Q-03P"]["THRESHOLDS"] == [] and six["Q-12"]["THRESHOLDS"] == []


def test_old_revision_unchanged_and_facts_scoped_out():
    s = _r("QORTUBA_R8_14_STATUS")
    assert all(s["old_revision_unchanged_vs_r8_13"].values())
    f = _r("OWNER_METHOD_FACT_REGISTER")
    assert all(x["binding"]["NEW_K2"] == "APPLIES" and x["binding"]["OLD_K1"] != "APPLIES" for x in f["facts"])
    assert f["silent_contradictions"] == []


def test_digest_reasons_and_gates():
    d = _r("DIGEST_HIERARCHY")
    assert d["lab_reproduces_blind_digest"]
    assert all(v["TOPOLOGY_RUN_INPUT_DIGEST"] == "CHANGED" for v in d["vs_r8_13"].values())
    dr = _r("R8_14_DECISION_REGISTER")
    assert dr["gates"] == {"MIGRATION_PLANNING_READY": "YES", "MIGRATION_EXECUTION_READY": "NO",
                           "PRODUCTION_MIGRATION": "NO"}
    assert len(dr["answers"]) == 36
    assert _r("OWNER_ACTION_REGISTER")["headline"] == "NO OWNER ACTION REQUIRED."
    assert _r("CLOSURE_RELEASE_STATUS")["released"] == []
    assert _r("SOURCE_ANCHOR_STATUS")["state"] == "NOT_ESTABLISHED"
