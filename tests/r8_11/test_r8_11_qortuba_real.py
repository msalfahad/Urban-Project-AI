"""R8.11 on the declared Qortuba fixtures (old revision, with the closure policy) and the consistency of the
committed R8.11 registers (the new revision is rebuilt in the lab: research/external_engine_lab/r8_11_qortuba.py)."""

from __future__ import annotations

import hashlib
import json
import random
import sys
from dataclasses import replace
from pathlib import Path

import pytest

from engine.source import topology_closures as TC, wall_bands as WB

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = json.loads((ROOT / "tests/r8_8/FIXTURE_MANIFEST.json").read_text())
REG = Path(__file__).parent / "registers"


def _r(name):
    return json.loads((REG / f"{name}.json").read_text())


@pytest.fixture(scope="module")
def lab():
    for path, want in MANIFEST["fixtures"].items():
        if not (ROOT / path).exists():
            pytest.skip(f"declared fixture not present in this checkout: {path}")
        assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == want, f"FIXTURE DRIFT: {path}"
    sys.path.insert(0, str(ROOT / "research/external_engine_lab"))
    import r8_10_claims as CL
    import r8_8_topology as m
    return m, CL


@pytest.fixture(scope="module")
def old(lab):
    m, CL = lab
    pc, xc, _ = CL.load()
    k1 = m.C.old_input()
    plain = m.run(k1, m.k1_unrealised(), part_claims=pc, xref_claims=xc)
    closed = m.run(k1, m.k1_unrealised(), part_claims=pc, xref_claims=xc, closure_policy=TC.POLICY_ID)
    return k1, plain, closed, (pc, xc)


# ------------------------------------------------------------------------------- old revision, real fixture
def test_old_revision_rows_are_unchanged_by_the_closure_policy(lab, old):
    m, _ = lab
    a, b = m.six_rows(old[1], "QORTUBA_REV_OLD"), m.six_rows(old[2], "QORTUBA_REV_OLD")
    assert {r: (v["state"], v["value"]) for r, v in a.items()} == {r: (v["state"], v["value"]) for r, v in b.items()}
    assert b["Q-03"]["value"] == 17.7425 and b["Q-03P"]["value"] == 11.685


def test_old_revision_has_no_authorised_closure_and_no_area_moves(old):
    closed = old[2]
    assert [c for c in closed["topology_closures"]["closures"] if c["release"] == TC.AUTHORISED_FOR_SHADOW] == []
    assert [(s["site_id"], round(s["area"], 9)) for s in closed["sites"]] == \
        [(s["site_id"], round(s["area"], 9)) for s in old[1]["sites"]]


def test_old_revision_manifest_offers_the_new_claims_and_applies_none(old):
    man = old[2]["run_manifest"]
    assert man["claims_applied"] == [] and man["claims_offered"]
    assert {c["outcome"] for c in man["claims_rejected"] if "per_part" in c} == {"SOURCE_SCOPE_MISMATCH"}


def test_same_fixtures_deterministic_first_run_and_order_independent_bands(lab, old):
    m, _ = lab
    pc, xc = old[3]
    k1 = old[0]
    parts = list(k1.parts)
    random.Random(11).shuffle(parts)
    again = m.run(replace(k1, parts=tuple(parts)), m.k1_unrealised(), part_claims=pc, xref_claims=xc,
                  closure_policy=TC.POLICY_ID)
    assert again["run_manifest"]["RUN_INPUT_DIGEST"] == old[2]["run_manifest"]["RUN_INPUT_DIGEST"]
    assert sorted(b["band_id"] for b in again["wall_bands"]["bands"]) == \
        sorted(b["band_id"] for b in old[2]["wall_bands"]["bands"])
    assert sorted(c["closure_id"] for c in again["topology_closures"]["closures"]) == \
        sorted(c["closure_id"] for c in old[2]["topology_closures"]["closures"])


def test_the_closure_policy_is_recorded_in_the_run_digest(old):
    assert old[1]["run_manifest"]["RUN_INPUT_DIGEST"] != old[2]["run_manifest"]["RUN_INPUT_DIGEST"]
    assert old[2]["run_manifest"]["method"]["closure_policy"] == TC.POLICY_ID


# ------------------------------------------------------------------------------- committed registers
def test_new_revision_rows_preserve_r8_10_and_q14_q13_stay_blocked():
    rows = _r("QORTUBA_R8_11_STATUS")["rows"]["NEW_K2_R8_11"]
    assert {r: rows[r]["value"] for r in ("Q-03", "Q-03P", "Q-11", "Q-12")} == {
        "Q-03": 17.7425, "Q-03P": 11.685, "Q-11": 17.7425, "Q-12": 11.685}
    # owner clarification: H2430's physical role is resolved; what blocks is the engine representation
    assert rows["Q-14"]["state"] == "BLOCKED_ENGINE_LIMITATION" and rows["Q-14"]["value"] is None
    assert rows["Q-13"]["state"] == "BLOCKED_MULTIPLE: BLOCKED_ENGINE_LIMITATION, BLOCKED_ROLE, BLOCKED_TRADE_RULE"
    assert all(v["final"] is False for v in (_r("Q13_STATUS"), _r("Q14_STATUS")))
    assert all(v["release_blockers"] and v["run_input_digest"] and v["row_input_digest"] for v in rows.values())


def test_q14_is_blocked_by_the_h2430_wall_core_only():
    (site,) = _r("Q14_STATUS")["blockers"]
    assert site["zones"] == ["HALL", "whgm"]
    (b,) = site["blockers"]
    assert (b["class"], b["issue"]) == ("ENGINE_LIMITATION", "WALL_END_REPRESENTATION_PENDING")
    assert b["detail"]["source"] == "2430" and b["detail"]["owner_action"] == "NONE"
    assert b["detail"]["pockets_m2"] == [0.3813]


def test_the_h2431_closure_is_zero_material_from_the_face_end_points():
    reg = _r("TOPOLOGY_CLOSURE_REGISTER")
    (cid,) = reg["applied"]["NEW_K2"]
    c = next(x for x in reg["NEW_K2"] if x["closure_id"] == cid)
    assert c["release"] == TC.AUTHORISED_FOR_SHADOW and c["source_evidence"][:2] == ["2296", "2297"]
    assert c["physical_material"] == "NONE" and not c["affects_wall_quantity"] and not c["affects_finish_quantity"]
    assert c["geometry"] == [109893.4, 15029.72, 109893.4, 15049.72]              # faces' start points, not H2431
    assert c["safety"]["label_partition_unchanged"] and c["safety"]["area_balance_ok"]
    (p,) = c["safety"]["separated_pieces"]
    assert p["pure_band_interior"] and p["area_m2"] == 0.6494
    leak = reg["leak"]
    assert leak["hall_area_r8_10_m2"] == 43.83 and leak["hall_area_r8_11_m2"] == 43.1806
    assert "NEAR_MISS_BOUNDARY_GAP" in leak["hall_issues_r8_10"] and \
        "NEAR_MISS_BOUNDARY_GAP" not in leak["hall_issues_r8_11"]


def test_blind_cap_classification():
    caps = _r("WALL_BAND_REGISTER")["cap_analysis"]
    assert caps["2431"]["classification"] == WB.CAP_CANDIDATE and caps["2431"]["gap_to_face_ends_mm"] == [9.2, 0.49]
    assert caps["2430"]["classification"] == WB.CAP_UNRESOLVED
    assert {f["face"]: f["collinear_fragments"] for f in caps["2430"]["faces_at_its_ends"]} == {"471": ["470"],
                                                                                                "477": []}
    assert caps["1316"]["classification"] == WB.NOT_WALL_CAP and caps["1316"]["glazing_ending_on_it"]


def test_amendment_a1_removed_candidates_only():
    reg = _r("WALL_BAND_REGISTER")
    frozen = reg["frozen_v1_first_run"]["NEW_K2"]
    applied = _r("TOPOLOGY_CLOSURE_REGISTER")["applied"]["NEW_K2"]
    assert applied == frozen["closures"]["AUTHORISED_FOR_SHADOW"]
    assert reg["policy"]["policy_id"] == "WALL_BAND_POLICY_V2" and reg["amendment_A1"]
    assert len(_r("OPEN_PASSAGE_SITE_REGISTER")["NEW_K2"]) < frozen["passages"]


def test_open_passages_are_explicit_and_the_mb_dress_passage_is_corroborated():
    reg = _r("OPEN_PASSAGE_SITE_REGISTER")
    for p in reg["NEW_K2"]:
        assert p["kind"] == WB.OPEN_PASSAGE and p["physically_connected"] and p["trade_allocation"] == "NOT_ALLOCATED"
        assert p["width_mm"] > 0 and p["wall_thickness_mm"] > 0 and p["jamb_faces"]
        assert p["head_condition"] == "NOT_ESTABLISHED_IN_SOURCE"
    a = reg["qp_audit"]
    assert a["QP-17_M.B.ROOM/DRESS_1.200"]["status"] == "CORROBORATED_BY_OWNER_RULE"
    assert a["QP-17_HALL/LOBBY_1.200"]["status"] == "NOT_DETECTED_AS_PASSAGE_SITE"


def test_semantic_classes_reproduce_r8_10_treatments():
    eq = _r("SEMANTIC_CLASS_REGISTER")["equivalence_with_r8_10"]
    assert all(v["r8_10"] == v["r8_11"] for v in eq.values())


def test_floor_footprint_is_unresolved_and_the_ceiling_policy_comes_from_the_q14_claim():
    fp = _r("OBJECT_FOOTPRINT_POLICY")
    assert fp["FLOOR_FINISH"]["policy"] is None and fp["FLOOR_FINISH"]["state"] == "UNRESOLVED"
    assert fp["CEILING"]["authority"] == "QORTUBA-Q14-CEILING-FOOTPRINT-OWNER-001"
    assert fp["implicit_path"]["rows_affected"]


def test_manifest_digest_is_reproducible_and_excludes_the_commit():
    m = _r("QTO_RUN_MANIFEST")
    d = m["determinism_shuffled_source_order"]
    assert d["same_digest"] and d["same_closures"] and d["same_bands"] and d["same_hall_area"]
    assert "code_commit" in m["NEW_K2"]["not_in_digest"]
    assert m["NEW_K2"]["policies"]["wall_band"][0] == "WALL_BAND_POLICY_V2"
    assert m["NEW_K2"]["RUN_INPUT_DIGEST"] != m["NEW_K2_WITHOUT_CLOSURES"]["RUN_INPUT_DIGEST"]


def test_no_owner_question_because_the_wardrobe_fact_is_not_the_sole_q13_blocker():
    q13 = _r("Q13_STATUS")
    assert q13["sole_blocker_test"]["answer"] == "NO"
    oa = _r("OWNER_ACTION_REGISTER")
    assert oa["required_now"] == [] and oa["headline"] == "NO OWNER ACTION REQUIRED."


def test_gates():
    g = _r("R8_11_DECISION_REGISTER")["gates"]
    assert (g["MIGRATION_PLANNING_READY"], g["MIGRATION_EXECUTION_READY"], g["PRODUCTION_MIGRATION"]) == \
        ("YES", "NO", "NO")
