"""R8.12 on the declared Qortuba fixtures (old revision, frozen V3) and the consistency of the committed R8.12
registers (the blind new-revision run and its comparison with the owner fact)."""

from __future__ import annotations

import hashlib
import json
import random
import sys
from dataclasses import replace
from pathlib import Path

import pytest

from engine.source import owner_facts as OF, run_manifest as RM, topology_closures as TC, wall_bands as WB

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = json.loads((ROOT / "tests/r8_8/FIXTURE_MANIFEST.json").read_text())
REG = Path(__file__).parent / "registers"


def _r(name):
    return json.loads((REG / f"{name}.json").read_text())


# ------------------------------------------------------------------------------- the freeze
def test_the_r8_12_freeze_is_intact_and_superseded_only_by_the_recorded_r8_13_v4_freeze():
    """R8.13: the live engine is WALL_BAND_POLICY_V4 (its own freeze); V3 survives as this record. A frozen R8.12 test
    may differ from its R8.12 hash only by the supersession the V4 freeze records for it."""
    fz = _r("R8_12_FRAGMENT_BAND_FREEZE")
    v4 = json.loads((ROOT / "tests/r8_13/registers/R8_13_V4_FREEZE.json").read_text())
    assert fz["wall_band_policy"]["id"] == "WALL_BAND_POLICY_V3" and v4["supersedes"]["wall_band_policy"] == \
        fz["wall_band_policy"]
    assert v4["wall_band_policy"]["id"] == "WALL_BAND_POLICY_V4"                  # superseded by V5 (R8.14)
    assert (TC.POLICY_ID, TC.policy_record()["digest"]) == (fz["closure_policy"]["id"], fz["closure_policy"]["digest"])
    v5 = json.loads((ROOT / "tests/r8_14/registers/R8_14_V5_FREEZE.json").read_text())
    for f, h in fz["synthetic_test_sha256"].items():
        live = hashlib.sha256((ROOT / f).read_bytes()).hexdigest()
        chain = [h]                                            # R8.12 -> (R8.13 V4) -> (R8.14 V5), recorded hops only
        s4 = v4["superseded_frozen_tests"].get(f)
        if s4 and s4["r8_12_sha256"] == chain[-1]:
            chain.append(s4["r8_13_sha256"])
        s5 = v5["superseded_frozen_tests"].get(f)
        if s5 and s5["previous_sha256"] == chain[-1]:
            chain.append(s5["r8_14_sha256"])
        assert live == chain[-1], f"frozen test edited outside a recorded supersession: {f}"
    assert fz["qortuba_runs_before_freeze"] == 0


# ------------------------------------------------------------------------------- the blind record
def test_the_blind_run_used_no_owner_fact_and_no_expected_value():
    b = _r("BLIND_QORTUBA_RESULT")["blind"]
    assert not (b["owner_fact_used"] or b["expected_h2430_given"] or b["expected_q14_given"]
                or b["historical_totals_given"])


def _blind_band(token):
    return next(b for b in _r("BLIND_QORTUBA_RESULT")["NEW_K2"]["watched_bands"] if token in json.dumps(b["ends"]))


def test_blind_h2430_band_spans_the_fragmented_face_and_the_column_blocks_only_its_interval():
    b = _blind_band('"2430"')
    assert b["state"] == WB.ESTABLISHED and set(b["faces"]) == {"470", "471", "477"}
    classes = [(iv["class"], iv["by"]) for iv in b["intervals"]]
    assert classes == [(WB.SPAN, []), (WB.OBSTACLE_OVERLAP, ["718", "718"]), (WB.SPAN, [])]
    end = next(e for e in b["ends"] if e["kind"] == WB.ALIGNED_FREE_END)
    assert end["faces"] == ["471", "477"] and end["caps"][0] == {"source": "2430", "role": "DIMENSION_GRAPHICS",
                                                                 "grade": WB.CAP_PROVEN, "gap_mm": [0.0, 0.0]}
    assert [e["kind"] for e in b["ends"]][0] == WB.RECEIVING_FACE_JUNCTION
    srcs = {x["source"] for sp in b["span_records"] for x in sp["source_intervals"]}
    assert srcs == {"470", "471", "477"}


def test_blind_h2430_closure_is_authorised_zero_material_and_removes_only_the_wall_core():
    c = next(x for x in _r("BLIND_QORTUBA_RESULT")["NEW_K2"]["closures"] if "2430" in x["evidence"])
    assert c["release"] == TC.AUTHORISED_FOR_SHADOW and c["material"] == "NONE"
    assert c["geometry"] == [109773.7561, 15029.7196, 109773.7561, 15049.7196]       # H471 / H477 end points
    (p,) = c["safety"]["separated_pieces"]
    assert p["pure_band_interior"] and p["area_m2"] == 0.3813
    assert c["safety"]["label_partition_unchanged"] and c["safety"]["area_balance_ok"]


def test_h2431_regression_and_h1316_negative_control():
    t = _r("TOPOLOGY_CLOSURE_REGISTER")
    r = t["h2431_regression"]
    assert r["same_geometry"] and r["r8_12"]["release"] == TC.AUTHORISED_FOR_SHADOW
    assert r["r8_12"]["safety"]["separated_pieces"][0]["area_m2"] == 0.6494 and r["r8_12"]["material"] == "NONE"
    assert t["h1316_control"]["closures_with_1316"] == []
    assert len(_r("BLIND_QORTUBA_RESULT")["NEW_K2"]["closures"]) == 2


def test_the_hall_lobby_passage_stays_open_and_measured():
    n = _r("BLIND_QORTUBA_RESULT")["NEW_K2"]
    (p,) = [x for x in n["passages"] if x["width_mm"] == 1196.45]
    assert p["thickness_mm"] == 200.0 and p["strip_in_site"] == n["hall"]["site"]
    assert n["hall"]["area_m2"] == 42.7993
    op = _r("QORTUBA_R8_12_STATUS")["owner_passage"]
    assert op["engine_width_mm"] == op["clear_width_mm_measured"] == 1196.45
    assert op["topology"]["across_the_opening"].startswith("NOTHING")


# ------------------------------------------------------------------------------- owner fact after the blind run
def test_the_owner_fact_agrees_corroborates_and_needs_no_fallback():
    o = _r("OWNER_FACT_COMPARISON")
    assert o["binding"] == {"NEW_K2": "APPLIES", "OLD_K1": OF.REJECTED_SCOPE}
    assert o["matrix_states"] == {OF.AGREES: 7} and not o["fallback_owner_role_claim_required"]
    assert {k: v["outcome"] for k, v in o["domains"].items()} == {
        OF.TOPOLOGY_ROLE: OF.OFFERED, OF.TOPOLOGY_CLOSURE_REVIEW: OF.CORROBORATING_ONLY,
        OF.BLOCKER_CLASSIFICATION: OF.CORROBORATING_ONLY, OF.PASSAGE_ATTRIBUTES: OF.APPLIED}


# ------------------------------------------------------------------------------- rows
def test_rows_q14_computed_shadow_and_the_other_rows_preserved():
    rows = _r("QORTUBA_R8_12_STATUS")["rows"]["NEW_K2_R8_12"]
    assert {r: rows[r]["value"] for r in ("Q-03", "Q-03P", "Q-11", "Q-12")} == {
        "Q-03": 17.7425, "Q-03P": 11.685, "Q-11": 17.7425, "Q-12": 11.685}
    q = _r("Q14_STATUS")
    assert q["state"] == "COMPUTED_SHADOW" and q["value"] == 141.0263 and q["final"] is False
    assert any(b.startswith("SOURCE_ANCHOR") for b in q["release_blockers"])
    assert any(b.startswith("PASSAGE_SOFFIT_ALLOCATION") for b in q["release_blockers"])
    assert q["owner_facts"] == {"corroborating": ["QORTUBA-NEW-HALL-LOBBY-OPEN-PASSAGE-OWNER-001@v1"],
                                "applied_to_row": [], "applied_to_release": ["QORTUBA-NEW-HALL-LOBBY-OPEN-PASSAGE-OWNER-001@v1"]}
    assert all(_r("QORTUBA_R8_12_STATUS")["old_revision_unchanged"].values())


def test_q13_sole_blocker_is_the_floor_under_objects_fact():
    q = _r("Q13_STATUS")
    assert q["state"].startswith("BLOCKED") and q["value"] is None
    t = q["sole_blocker_test"]
    assert t["answer"] == "YES" and t["counterfactual"]["YES_WHOLE_ROOM"]["state"] == "COMPUTED_SHADOW"
    assert t["counterfactual"]["NO_FOOTPRINT_DEDUCTED"]["state"].startswith("BLOCKED")
    assert not any(v["value_recorded"] for v in t["counterfactual"].values())
    oa = _r("OWNER_ACTION_REGISTER")
    assert len(oa["required_now"]) == 1 and oa["required_now"][0]["action_id"] == "QORTUBA_FLOOR_UNDER_BUILT_IN_WARDROBES"


# ------------------------------------------------------------------------------- digest hierarchy
def test_digest_hierarchy_owner_fact_in_release_only():
    d = _r("DIGEST_HIERARCHY")
    assert d["layers"] == list(RM.DIGEST_LAYERS)
    tops = {v["TOPOLOGY_RUN_INPUT_DIGEST"] for v in d["rows"].values()}
    assert len(tops) == 1                                                       # one TS01 run, one topology digest
    for rid, v in d["rows"].items():
        assert v["ROW_AUTHORITY_DIGEST"]["owner_facts_applied"] == []
        assert v["RELEASE_INPUT_DIGEST"]["row"] == v["ROW_AUTHORITY_DIGEST"]["digest"]
    assert d["rows"]["Q-14"]["RELEASE_INPUT_DIGEST"]["owner_facts_applied"] == \
        ["QORTUBA-NEW-HALL-LOBBY-OPEN-PASSAGE-OWNER-001@v1"]
    rad = d["rows"]["Q-14"]["ROW_AUTHORITY_DIGEST"]
    core = {k: v for k, v in rad.items() if k != "digest"}
    assert RM._digest(core) == rad["digest"]


def test_determinism_and_policy_audit():
    s = _r("QORTUBA_R8_12_STATUS")
    assert all(s["determinism"].values()) and s["lab_reproduces_blind_record"]
    a = _r("POLICY_PROVENANCE_AUDIT")
    v3 = a["wall_bands"]["params_in_policy_record"]                 # the R8.12 (V3) record; R8.13 V4 only adds keys
    assert v3["elongation_basis"].startswith("the raw overlap") and set(v3) <= set(WB.PARAMS)
    assert set(a["wall_bands"]["integer_literals_outside_params"]) <= {0, 1, 2, -1, 3, 4, 8, 16}


def test_findings_v3_d1_d2_are_recorded_not_patched():
    assert _r("FACE_CHAIN_REGISTER")["NEW_K2"]["id_collisions"]
    assert _r("WALL_BAND_ASSEMBLY_REGISTER")["wide_bands"]
    acts = {a["id"] for a in _r("ENGINEERING_ACTION_REGISTER")["actions"]}
    assert {"E-R8.13-01", "E-R8.13-02"} <= acts


def test_gates():
    g = _r("R8_12_DECISION_REGISTER")["gates"]
    assert (g["MIGRATION_PLANNING_READY"], g["MIGRATION_EXECUTION_READY"], g["PRODUCTION_MIGRATION"]) == \
        ("YES", "NO", "NO")


# ------------------------------------------------------------------------------- old revision, real fixture
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


def test_old_revision_v3_ids_are_order_independent(lab):
    m, CL = lab
    pc, xc, _ = CL.load()
    k1 = m.C.old_input()
    a = m.run(k1, m.k1_unrealised(), part_claims=pc, xref_claims=xc, closure_policy=TC.POLICY_ID)
    parts = list(k1.parts)
    random.Random(23).shuffle(parts)
    b = m.run(replace(k1, parts=tuple(parts)), m.k1_unrealised(), part_claims=pc, xref_claims=xc,
              closure_policy=TC.POLICY_ID)
    key = lambda r: (sorted(c["chain_id"] for c in r["wall_bands"]["chains"]),
                     sorted(s["span_id"] for s in r["wall_bands"]["spans"]),
                     sorted(x["band_id"] for x in r["wall_bands"]["bands"]),
                     r["run_manifest"]["RUN_INPUT_DIGEST"])
    assert key(a) == key(b)
    assert [c for c in a["topology_closures"]["closures"] if c["release"] == TC.AUTHORISED_FOR_SHADOW] == []
