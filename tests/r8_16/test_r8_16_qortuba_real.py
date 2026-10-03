"""R8.16 on the committed registers: closure V2 at I1471, window floor contact, door / doorless jambs, skirting V3,
hidden profile, Q-13 / Q-14 rebuild, marble regression, owner facts, digests and gates."""

from __future__ import annotations

import json
import math
from pathlib import Path

from engine.source import owner_method_facts as MF, topology as T, wall_contact_path as WC

ROOT = Path(__file__).resolve().parents[2]
REG = Path(__file__).parent / "registers"
ROWS = ("Q-03", "Q-03P", "Q-11", "Q-12", "Q-13", "Q-14")


def _r(n):
    return json.loads((REG / f"{n}.json").read_text())


# ------------------------------------------------------------------------------- closure V2
def test_every_new_revision_door_has_closure_b_and_i1471_uses_the_offset_rule():
    c = _r("CLOSURE_BLIND_RESULT")["NEW_K2"]
    assert c["closure_b_missing"] == [] and c["openings"]["I1471"]["rule"] == T.B_OFFSET_JAMB
    assert c["closure_b_rules"][T.B_OFFSET_JAMB] == 1
    assert _r("QORTUBA_R8_16_STATUS")["doors_without_threshold_site"] == []
    p = _r("OFFSET_CLOSURE_POLICY")
    assert p["policy"]["policy_id"] == "DOOR_OPENING_CLOSURE_POLICY_V2"
    assert p["in_run_manifest"] == [p["policy"]["policy_id"], p["policy"]["digest"]]
    assert all(p["reproduced_by_the_lab"].values())


def test_the_i1471_audit_explains_the_offset_from_two_established_bands():
    a = _r("I1471_SOURCE_AUDIT")
    assert sorted(b["thickness_mm"] for b in a["hosting_bands"]) == [150.0, 200.0]
    assert {b["state"] for b in a["hosting_bands"]} == {"WALL_BAND_ESTABLISHED"}
    assert a["v2_result"]["rule"] == T.B_OFFSET_JAMB
    ev = a["v2_result"]["evidence"]
    assert ev["stagger"] <= ev["depth"]
    assert a["strip_site"]["area_m2"] > 0


def test_h2430_h2431_closures_and_the_old_revision_do_not_regress():
    st = _r("QORTUBA_R8_16_STATUS")
    assert all(st["old_revision_unchanged_vs_r8_15"].values())
    assert all(st["determinism"].values())
    tcs = _r("CLOSURE_BLIND_RESULT")["NEW_K2"]["topology_closures"]
    assert sorted(x for c in tcs for x in c["separated_m2"]) == [0.3813, 0.6494]


# ------------------------------------------------------------------------------- windows
def test_proven_windows_keep_the_skirting_continuous_and_the_glazed_screen_is_withheld():
    w = _r("WINDOW_FLOOR_CONTACT_REGISTER")
    above = [x for x in w["windows"] if x["floor_contact"]["state"] == WC.ABOVE_FLOOR]
    assert above and all(x["hosted_on_wall_face_line"] and x["span"] == "SKIRTING_CONTINUITY_UNDER_WINDOW"
                         for x in above)
    assert abs(math.fsum(x["length_mm"] for x in above) / 1000 - w["continuity_lm"]) < 1e-3
    other = [x for x in w["windows"] if x not in above]
    assert all(x["floor_contact"]["state"] == WC.FLOOR_CONTACT_UNPROVEN and not x["hosted_on_wall_face_line"]
               for x in other)
    assert all(x["topology_effect"].startswith("NONE") for x in w["windows"])


def test_the_owner_window_facts_are_scoped_and_qp09_stays_on_file():
    facts = [MF.from_record(f) for f in json.loads((ROOT / "data/registry/OWNER_METHOD_FACTS.json").read_text())
             ["facts"]]
    by = {f.fact_id: f for f in facts}
    win = by["QORTUBA-NEW-NORMAL-WINDOWS-ABOVE-FLOOR-OWNER-001"]
    assert win.statement["sill_height_m"] == 1.0 and win.scope["source_revision_id"] == "QORTUBA_REV_NEW"
    sup = by["QORTUBA-NEW-SKIRTING-WINDOW-FLOOR-CONTACT-OWNER-001"]
    (rel,) = sup.relations
    assert rel["relation"] == MF.SUPERSEDED_IN_SCOPE and rel["scope"] and rel["rule"].startswith("QP-09")
    assert "ON FILE, UNCHANGED" in _r("OWNER_METHOD_RULE_REGISTER")["qp09"]["state"]


# ------------------------------------------------------------------------------- doors / doorless
def test_installed_doors_stop_the_path_with_zero_jamb_skirting():
    d = _r("DOOR_SKIRTING_POLICY")
    assert d["rule"] == {"path": "STOP_AT_OPENING", "across_opening": "NONE", "jamb_skirting": "NONE"}
    assert len(d["door_jambs"]) == 16 and all(j["skirting_lm"] == 0.0 for j in d["door_jambs"])
    sk = _r("SKIRTING_REGISTER")
    assert sk["excluded_lm"]["DOOR_JAMB"] == 0.0 and sk["excluded_lm"][WC.DOOR_PRESENT] > 0


def test_doorless_openings_count_real_jambs_once_and_nothing_across():
    d = _r("DOORLESS_JAMB_REGISTER")
    assert d["across_opening_lm"] == 0.0 and d["topology_closure_lm"] == 0.0
    hall = [j for j in d["jambs"] if j["opening"] == d["hall_far_jamb"]["opening"]]
    assert sorted(j["side"] for j in hall) == ["LEFT", "RIGHT"] and all(j["physical"] for j in hall)
    assert d["hall_far_jamb"]["source"].startswith("BANDEND|")
    cont = [j for j in d["jambs"] if j["end_kind"] == "CONTINUOUS_WALL_FACE"]
    assert cont and all(not j["physical"] and j["counted_lm"] == 0.0 for j in cont)
    assert abs(d["counted_lm"] - _r("SKIRTING_REGISTER")["breakdown_lm"]["doorless_jamb"]) < 1e-9


# ------------------------------------------------------------------------------- skirting / hidden profile
def test_the_skirting_row_is_the_blind_record_and_its_breakdown_reconciles():
    sk, b = _r("SKIRTING_REGISTER"), _r("SKIRTING_BLIND_RESULT")
    assert sk["SKIRTING_LM"] == b["PAYABLE_LM"] and sk["reproduces_blind"]
    assert abs(math.fsum(sk["breakdown_lm"].values()) - sk["SKIRTING_LM"]) < 1e-5
    assert abs(math.fsum(v["payable_lm"] for v in sk["per_room"].values()) - sk["SKIRTING_LM"]) < 1e-5
    assert sk["reconciliation_vs_r8_15"]["reconciles"] and sk["reconciliation_vs_r8_15"]["is_target"] is False
    assert {v["state"] for v in sk["per_room"].values() if "BATH" in v["zones"] or "PAINTRY" in v["zones"]} == \
        {WC.NO_SKIRTING}
    assert sk["state"] == "COMPUTED_SHADOW_WITH_WITHHELD_SPANS" and sk["withheld_lm"] > 0
    assert any(x.startswith("WITHHELD_SPAN") for x in sk["release_blockers"])
    assert any(x.startswith("V3_O1") for x in sk["release_blockers"])


def test_the_hidden_profile_is_its_own_row_on_the_identical_path():
    hp, sk = _r("HIDDEN_PROFILE_REGISTER"), _r("SKIRTING_REGISTER")
    assert hp["HIDDEN_PROFILE_LM"] == sk["SKIRTING_LM"] and hp["merged_with_skirting"] is False
    assert hp["release_blockers"] == sk["release_blockers"] and hp["state"] == sk["state"]
    assert hp["per_room_lm"] == {k: v["payable_lm"] for k, v in sk["per_room"].items()}


# ------------------------------------------------------------------------------- rows / marble
def test_q14_lost_exactly_the_i1471_reveal_and_the_floor_rows_are_unchanged():
    st, q14 = _r("QORTUBA_R8_16_STATUS"), _r("Q14_STATUS")
    reg = q14["regression_vs_r8_15"]
    assert reg["R8.16"] == reg["R8.15_counterfactual"] and reg["delta_m2"] == -_r("I1471_SOURCE_AUDIT")[
        "strip_site"]["area_m2"]
    assert q14["door_strip_is_ceiling"] == []
    assert all(st["vs_r8_15"][rid]["delta"] == 0.0 for rid in ("Q-03", "Q-03P", "Q-11", "Q-12", "Q-13"))
    assert {v["STATE"] for v in st["six_rows"].values()} == {"COMPUTED_SHADOW"}


def test_marble_is_unchanged_and_i1471_creates_no_marble():
    m = _r("MARBLE_THRESHOLD_REGISTER")["regression_vs_r8_15"]
    assert m["unchanged"] and m["R8.16"]["count"] == 4
    assert m["i1471"]["classification"] == "DRY_DRY_CONTINUOUS_PORCELAIN"


def test_digests_changed_for_the_recorded_closure_policy_and_gates_hold():
    dh = _r("DIGEST_HIERARCHY")
    assert all(v["TOPOLOGY_RUN_INPUT_DIGEST"] == "CHANGED" for v in dh["vs_r8_15"].values())
    d = _r("R8_16_DECISION_REGISTER")
    assert d["gates"] == {"MIGRATION_PLANNING_READY": "YES", "MIGRATION_EXECUTION_READY": "NO",
                          "PRODUCTION_MIGRATION": "NO"}
    assert len(d["answers"]) == 36 and _r("SOURCE_ANCHOR_STATUS")["state"] == "NOT_ESTABLISHED"
    assert _r("WALL_FACE_ENGINE_READINESS")["ready_to_publish"] is False
    assert _r("OWNER_ACTION_REGISTER")["required_now"] == []
