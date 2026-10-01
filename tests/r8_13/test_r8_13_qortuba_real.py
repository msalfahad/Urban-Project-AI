"""R8.13 on the committed registers: the blind V4 record, its comparison with V3, the owner finish facts applied
only in the trade layer, the Q-13 rebuild, the Q-14 regression, six-row provenance, digests and gates."""

from __future__ import annotations

import json
from pathlib import Path

from engine.source import closure_release as CR, owner_facts as OF, run_manifest as RM, topology_closures as TC
from engine.source import trade_strips as TS, wall_bands as WB

REG = Path(__file__).parent / "registers"
ROWS = ("Q-03", "Q-03P", "Q-11", "Q-12", "Q-13", "Q-14")


def _r(n):
    return json.loads((REG / f"{n}.json").read_text())


# ------------------------------------------------------------------------------- the blind record
def test_the_blind_run_used_no_owner_fact_and_the_frozen_v4():
    b = _r("BLIND_QORTUBA_V4_RESULT")
    assert not any(b["blind"][k] for k in ("owner_fact_used", "floor_fact_used", "finish_fact_used",
                                            "expected_h2430_given", "expected_q14_given", "historical_totals_given"))
    assert b["wall_band_policy"] == _r("R8_13_V4_FREEZE")["wall_band_policy"]
    assert b["wall_band_policy"]["id"] == WB.POLICY_ID and b["freeze"] == _r("R8_13_V4_FREEZE")["frozen_commit"]


def test_v3_d1_no_collision_and_unique_ids_on_both_revisions():
    b = _r("BLIND_QORTUBA_V4_RESULT")
    for k in ("NEW_K2", "OLD_K1"):
        v = b[k]["v4"]
        assert v["chain_id_collisions"] == [] and v["chain_ids_unique"] and v["band_ids_unique"]
        assert ["2060|0"] in v["chains_line_disambiguated"] and ["2060|2"] in v["chains_line_disambiguated"]


def test_v3_d2_the_false_band_and_its_passage_are_gone():
    b = _r("BLIND_QORTUBA_V4_RESULT")
    for k in ("NEW_K2", "OLD_K1"):
        u = [x for x in b[k]["v4"]["unsupported_touching_r8_12_findings"] if {"574", "584"} <= set(x["chain_a"] +
                                                                                                    x["chain_b"])]
        assert len(u) == 1 and round(u[0]["local_run"], 6) == 15.0 and round(u[0]["separation"], 6) == 180.0
        assert not [p for p in b[k]["passages"] if p["width_mm"] >= 4600.0]
        assert not [x for x in b[k]["v4"]["bands_touching_r8_12_findings"] if sorted(x["faces"]) == ["574", "584"]]
    assert _r("V3_DEFECT_RESOLUTION")["V3_D2"]["blind_result"]["false_passage_OP_a38c9a827025e4a9"] == "GONE"


def test_h2430_h2431_h1316_keep_their_v3_geometry_and_areas():
    c = _r("BLIND_COMPARISON")
    h = c["h2430"]
    assert h["same_geometry_as_v3"] and h["same_area_as_v3"] and h["separated_m2"] == [0.3813]
    assert h["ends"] == [WB.RECEIVING_FACE_JUNCTION, WB.ALIGNED_FREE_END]
    assert h["intervals"] == [[WB.SPAN, []], [WB.OBSTACLE_OVERLAP, ["718", "718"]], [WB.SPAN, []]]
    assert h["closure_v4"]["release"] == TC.AUTHORISED_FOR_SHADOW and h["closure_v4"]["material"] == "NONE"
    k = c["h2431"]
    assert k["same_geometry_as_v3"] and k["same_area_as_v3"] and k["separated_m2"] == [0.6494]
    assert k["passage_open"]["width_mm"] == 1196.45 and k["passage_open"]["thickness_mm"] == 200.0
    assert c["h1316"]["closures_with_1316"] == []
    assert c["labelled_site_areas_unchanged"] and c["hall_m2"]["R8.12"] == c["hall_m2"]["R8.13"] == 42.7993
    assert all(c["lab_reproduces_blind"].values())


def test_post_blind_observations_are_recorded_not_patched():
    obs = {o["id"]: o for o in _r("V3_DEFECT_RESOLUTION")["post_blind_observations_for_r8_14"]}
    assert set(obs) == {"V4-O1", "V4-O2"} and all(o["action"].startswith("R8.14") for o in obs.values())
    assert _r("R8_13_V4_FREEZE")["wall_band_policy"]["digest"] == WB.policy_record()["digest"]


# ------------------------------------------------------------------------------- rows
def test_six_rows_compute_in_shadow_and_q14_is_unchanged():
    s = _r("QORTUBA_R8_13_STATUS")
    six = s["six_rows"]
    assert {r: (six[r]["STATE"], six[r]["VALUE"]) for r in ROWS} == {
        "Q-03": ("COMPUTED_SHADOW", 17.7425), "Q-03P": ("COMPUTED_SHADOW", 11.685),
        "Q-11": ("COMPUTED_SHADOW", 17.7425), "Q-12": ("COMPUTED_SHADOW", 11.685),
        "Q-13": ("COMPUTED_SHADOW", 111.5988), "Q-14": ("COMPUTED_SHADOW", 141.0263)}
    assert all(not v["final"] for v in six.values())
    q = _r("Q14_STATUS")["regression"]
    assert (q["R8.12"], q["R8.13"], q["result"], q["is_target"]) == (141.0263, 141.0263, "SAME", False)
    assert all(s["old_revision_unchanged"].values()) and all(s["determinism"].values())


def test_no_naked_values_every_row_carries_its_provenance():
    keys = {"STATE", "VALUE", "TOPOLOGY_POLICY", "RUN_DIGEST", "ROW_AUTHORITY_DIGEST", "PHYSICAL_SITES",
            "SEMANTIC_CLASSES", "TRADE_RULES", "OBJECT_FOOTPRINT_POLICY", "THRESHOLD_PASSAGE_TREATMENT",
            "OWNER_FACTS_CLAIMS", "SOURCE_ANCHOR", "RELEASE_BLOCKERS"}
    for rid, v in _r("QORTUBA_R8_13_STATUS")["six_rows"].items():
        assert keys <= set(v), rid
        assert v["PHYSICAL_SITES"] and v["RELEASE_BLOCKERS"][-1].startswith("SHADOW_ONLY")
        assert any(b.startswith("SOURCE_ANCHOR") for b in v["RELEASE_BLOCKERS"])


def test_q13_computes_only_with_the_scoped_floor_fact():
    q = _r("Q13_STATUS")
    assert q["STATE"] == "COMPUTED_SHADOW" and q["VALUE"] == 111.5988
    assert q["without_the_floor_fact"]["state"].startswith("BLOCKED")
    assert q["OBJECT_FOOTPRINT_POLICY"] == ["QORTUBA-NEW-FLOOR-OBJECT-FOOTPRINT-OWNER-001@v1:FLOOR_FINISH:"
                                            "FOOTPRINT_INCLUDED"]
    assert q["OWNER_FACTS_CLAIMS"]["facts_applied_to_row"] == ["QORTUBA-NEW-FLOOR-OBJECT-FOOTPRINT-OWNER-001@v1"]
    assert "ROLE_UNRESOLVED_BUT_NON_MATERIAL_TO_TRADE" in q["object_footprints"]["roles"]
    assert q["historical_matching"] == "NONE"
    fp = _r("TRADE_OBJECT_FOOTPRINT_POLICY")
    assert not any(fp["leak_check_other_rows_changed"].values())
    cleared = {c for x in fp["blockers_cleared_by_the_policy"] for c in x["cleared"]}
    assert "TRADE_RULE:OBJECT_FOOTPRINT_POLICY_UNRESOLVED" in cleared


def test_thresholds_and_passages_are_never_silent():
    q = _r("Q13_STATUS")
    assert len(q["strips"]["thresholds_excluded"]) == 6 and all(a["state"] == TS.EXCLUDED and not a["in_row_total"]
                                                                for a in q["strips"]["thresholds_excluded"])
    assert {a["kind"] for a in q["strips"]["passages_included"]} == {"OPEN_PASSAGE"}
    assert all(a["in_row_total"] for a in q["strips"]["passages_included"]) and q["strips"]["blocking"] == []
    assert any(b.startswith("STRIP_ALLOCATION") for b in q["RELEASE_BLOCKERS"])
    assert not any(b.startswith("OBJECT_FOOTPRINT_IMPLICIT") for b in q["RELEASE_BLOCKERS"])
    q14 = _r("Q14_STATUS")
    assert any(b.startswith("PASSAGE_SOFFIT_ALLOCATION") for b in q14["RELEASE_BLOCKERS"])
    assert any(b.startswith("STRIP_ALLOCATION") for b in q14["RELEASE_BLOCKERS"])


# ------------------------------------------------------------------------------- facts, classes, digests
def test_fact_outcomes_per_row():
    f = {x["ref"]: x for x in _r("OWNER_FINISH_FACT_REGISTER")["facts"]}
    floor = f["QORTUBA-NEW-FLOOR-OBJECT-FOOTPRINT-OWNER-001@v1"]
    assert floor["binding"] == {"NEW_K2": "APPLIES", "OLD_K1": OF.REJECTED_SCOPE}
    assert floor["row_outcomes"] == {"Q-03": OF.REJECTED_SCOPE, "Q-03P": OF.REJECTED_SCOPE, "Q-11": OF.REJECTED_SCOPE,
                                     "Q-12": OF.REJECTED_SCOPE, "Q-13": OF.APPLIED, "Q-14": OF.REJECTED_SCOPE}
    wet = f["QORTUBA-NEW-WET-SERVICE-FINISH-OWNER-001@v1"]
    assert {wet["row_outcomes"][r] for r in ("Q-03", "Q-03P", "Q-11", "Q-12")} == {OF.CORROBORATING_ONLY}
    assert _r("OWNER_FINISH_FACT_REGISTER")["silent_contradictions"] == []
    sup = [r for r in _r("OWNER_FINISH_FACT_REGISTER")["reconciliation"] if r["relation"] == "SUPERSEDED_IN_SCOPE"]
    assert len(sup) == 1 and sup[0]["rule"].startswith("QP-01") and "old revision" in sup[0]["scope"]


def test_semantic_classes_are_exact_text_and_scoped():
    c = _r("SEMANTIC_SPACE_CLASS_REGISTER")
    assert c["rule"]["by_label"] == {"BATH": "WET_SERVICE_ROOM", "PAINTRY": "SERVICE_ROOM"}
    assert c["rule"]["otherwise_class"] == "DRY_INTERNAL_ROOM"
    assert c["owner_room_types"]["IRONING_ROOM"]["labels"] == [] and \
        c["owner_room_types"]["WASHING_LAUNDRY_ROOM"]["labels"] == []
    assert set(c["classes"]) >= {"DRY_INTERNAL_ROOM", "WET_SERVICE_ROOM", "PASSAGE", "THRESHOLD", "OBSTACLE_INTERIOR"}


def test_digest_hierarchy_floor_fact_in_q13_row_authority_only():
    d = _r("DIGEST_HIERARCHY")
    assert d["layers"] == list(RM.DIGEST_LAYERS)
    assert len({v["TOPOLOGY_RUN_INPUT_DIGEST"] for v in d["rows"].values()}) == 1
    assert d["rows"]["Q-13"]["TOPOLOGY_RUN_INPUT_DIGEST"] == _r("BLIND_QORTUBA_V4_RESULT")["NEW_K2"]["run_input_digest"]
    for rid, v in d["rows"].items():
        fa = v["ROW_AUTHORITY_DIGEST"]["owner_facts_applied"]
        assert fa == (["QORTUBA-NEW-FLOOR-OBJECT-FOOTPRINT-OWNER-001@v1"] if rid == "Q-13" else []), rid
        assert v["RELEASE_INPUT_DIGEST"]["row"] == v["ROW_AUTHORITY_DIGEST"]["digest"]
        core = {k: x for k, x in v["ROW_AUTHORITY_DIGEST"].items() if k != "digest"}
        assert RM._digest(core) == v["ROW_AUTHORITY_DIGEST"]["digest"]
    assert d["q13_row_authority_without_the_floor_fact"] != d["rows"]["Q-13"]["ROW_AUTHORITY_DIGEST"]["digest"]
    assert not any("FLOOR" in p for p in d["rows"]["Q-14"]["ROW_AUTHORITY_DIGEST"]["footprint_policies"])


def test_source_anchor_and_closure_release_are_honest():
    a = _r("SOURCE_ANCHOR_STATUS")
    assert a["state"] == "NOT_ESTABLISHED" and not any(a["decoders_found_locally"].values())
    m = _r("CLOSURE_RELEASE_MODEL")
    assert m["released"] == [] and len(m["closures"]) == 2
    for c in m["closures"].values():
        assert c["level"] == CR.AUTHORISED_FOR_SHADOW and not c["releases_anything"]
        assert set(c["missing_for_reviewed"]) == {"CROSS_ROUTE_AGREEMENT", "SOURCE_ANCHOR", "HUMAN_REVIEW"}


def test_owner_actions_and_gates():
    o = _r("OWNER_ACTION_REGISTER")
    assert o["headline"] == "NO OWNER ACTION REQUIRED." and o["required_now"] == []
    d = _r("R8_13_DECISION_REGISTER")
    assert d["gates"] == {"MIGRATION_PLANNING_READY": "YES", "MIGRATION_EXECUTION_READY": "NO",
                          "PRODUCTION_MIGRATION": "NO"}
    assert len(d["answers"]) == 31 and d["recommendation_before_coding"]["SCHEMA"].endswith("BEFORE_CODING_V1")
