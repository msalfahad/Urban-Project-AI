"""R8.17 on the committed registers: the sliding glass door, V3-O1 fixed by V4, the skirting / hidden-profile rows,
the row and marble regression, the wall-face engine result and readiness, gates."""

from __future__ import annotations

import json
import math
from pathlib import Path

from engine.source import wall_contact_path as WC, wall_faces as WF

REG = Path(__file__).parent / "registers"
REG16 = Path(__file__).resolve().parents[1] / "r8_16" / "registers"
ROWS = ("Q-03", "Q-03P", "Q-11", "Q-12", "Q-13", "Q-14")


def _r(n, reg=REG):
    return json.loads((reg / f"{n}.json").read_text())


# ------------------------------------------------------------------------------- sliding door
def test_the_hall_paintry_sliding_door_is_bound_excluded_and_never_a_window():
    d = _r("HALL_PAINTRY_SLIDING_DOOR_REGISTER")
    assert d["binding"] == "APPLIES" and d["classification"]["path_class"] == WC.SLIDING_GLAZED_DOOR_TO_FLOOR
    assert d["skirting"]["HALL_excluded_lm"] > 0 and d["skirting"]["payable_lm"] == 0.0
    assert len(d["jambs"]) == 2 and all(j["skirting_lm"] == 0.0 for j in d["jambs"])
    w = [x for x in _r("SKIRTING_V4_BLIND_RESULT")["windows"] if x["class"] == WC.WINDOW_ABOVE_FLOOR]
    assert not [x for x in w if any("H533" in s or "H542" in s for s in x["sources"])]
    assert d["wall_face"]["PAINTRY"]["sill_m"] == 0.0


# ------------------------------------------------------------------------------- skirting / V3-O1 / hidden profile
def test_the_v4_skirting_row_is_the_blind_record_with_nothing_withheld_and_every_edge_conserved():
    sk, b = _r("SKIRTING_REGISTER"), _r("SKIRTING_V4_BLIND_RESULT")
    assert sk["SKIRTING_LM"] == b["PAYABLE_LM"] and all(sk["reproduces_blind"].values())
    assert sk["withheld_lm"] == 0.0 and sk["state"] == "COMPUTED_SHADOW" and sk["conservation_all_sites"]
    assert abs(math.fsum(sk["breakdown_lm"].values()) - sk["SKIRTING_LM"]) < 1e-5
    assert sk["reconciliation_vs_r8_16"]["reconciles"] and sk["reconciliation_vs_r8_16"]["is_target"] is False
    assert not [x for x in sk["release_blockers"] if x.startswith(("WITHHELD_SPAN", "V3_O1"))]
    assert {x.split(":")[0] for x in sk["release_blockers"]} == {"SOURCE_ANCHOR", "SHADOW_ONLY"}
    assert sk["known_defects_open"] == []


def test_v3_o1_is_fixed_generically_the_continuous_face_is_kept_and_only_annotated():
    v = _r("SKIRTING_V3_O1_REGISTER")
    ev = v["evidence"]
    (n,) = ev["V4_annotations"]
    assert n["end_kind"] == "CONTINUOUS_WALL_FACE" and n["consumed_lm"] == 0.0
    assert abs((ev["V4_payable_lm"] - ev["V3_payable_lm"]) - n["overlap_lm"]) < 1e-6
    assert ev["V4_conservation"]["reconciles"] and v["topology_effect"] == "NONE"


def test_the_hidden_profile_is_its_own_row_on_the_certified_path():
    hp, sk = _r("HIDDEN_PROFILE_REGISTER"), _r("SKIRTING_REGISTER")
    assert hp["HIDDEN_PROFILE_LM"] == sk["SKIRTING_LM"] and hp["merged_with_skirting"] is False
    assert hp["release_blockers"] == sk["release_blockers"]


# ------------------------------------------------------------------------------- rows / marble / digests
def test_rows_marble_and_digests_do_not_move_from_r8_16():
    st = _r("QORTUBA_R8_17_STATUS")
    assert all(v["delta"] == 0.0 for v in st["vs_r8_16"].values()) and all(st["old_revision_unchanged_vs_r8_16"].values())
    assert _r("MARBLE_THRESHOLD_REGISTER")["regression_vs_r8_16"]["unchanged"]
    assert all(set(v.values()) == {"SAME"} for v in _r("DIGEST_HIERARCHY")["vs_r8_16"].values())
    assert all(all(x.values()) for x in st["reproduces"].values()) and all(st["determinism"].values())


# ------------------------------------------------------------------------------- wall faces
def test_no_wall_finish_trade_is_published_and_each_blocker_is_explicit():
    rd = _r("WALL_FACE_ENGINE_READINESS")
    assert rd["implemented"] and rd["ready_for_publication"] is False
    assert {t: v["state"] for t, v in rd["trades"].items()} == {"WALL_TILE": "BLOCKED", "PLASTER": "BLOCKED",
                                                                "PAINT": "BLOCKED"}
    assert any(b.startswith("DRY_WALL_HEIGHT_NOT_ESTABLISHED") for b in rd["trades"]["PLASTER"]["blockers"])
    assert any(b.startswith("WF-O1") for b in rd["trades"]["WALL_TILE"]["blockers"])
    st = _r("QORTUBA_R8_17_STATUS")["extra_rows"]
    assert st["PLASTER"]["value_m2"] is None and st["PAINT"]["value_m2"] is None and st["WALL_TILE"]["value_m2"] is None
    fz = _r("R8_17_WALL_FACE_FREEZE")["qortuba_wall_face_method"]
    assert fz["trade_rules"]["DRY_INTERNAL_ROOM"]["PLASTER"]["height_m"] is None


def test_wf_o1_is_only_the_second_form_check_and_the_primary_form_agrees_once_the_window_plane_is_in():
    w = _r("WALL_SURFACE_REGISTER")
    assert w["WF_O1"] and all(x["agree_when_the_window_plane_is_included"] and x["windows"] for x in w["WF_O1"])
    wt = w["WALL_TILE"]
    assert len(wt["computed_rooms_m2"]) == 3 and all(v["zones"] == ["BATH"] for s, v in wt["per_room"].items()
                                                    if s in wt["computed_rooms_m2"])
    assert w["double_count_guard"]["state"] == "PASS"
    for v in w["per_site"].values():
        for f in v["faces"].values():
            assert f["conservation"]["reconciles"]


def test_reveals_have_one_identity_no_invented_jamb_and_the_hall_soffit_matches_the_ceiling_exclusion():
    rv = _r("OPENING_REVEAL_REGISTER")["reveals"]
    keys = [(x["opening"], x["surface"]) for x in rv]
    assert len(keys) == len(set(keys)) and not [k for k in keys if k[1] == "SILL"]
    mb = [x for x in rv if x.get("non_physical_sides") == ["RIGHT"]]
    assert mb and {x["surface"] for x in mb} == {"LEFT_JAMB"}                    # H518 is wall face, never a jamb
    hall = [x for x in rv if x["surface"] == "TOP_REVEAL" and x["kind"] == WF.WITH_HEAD]
    q14 = _r("Q14_STATUS")
    assert hall and abs(hall[0]["area_m2"] - q14["SOFFIT_EXCLUSION_M2"]) < 1e-6
    dry_doors = [x for x in rv if x["kind"] == "DOOR" and x["trade"].startswith("PLASTER")]
    assert dry_doors and all(x["threshold_class"] == "DRY_DRY_CONTINUOUS_PORCELAIN" for x in dry_doors)


def test_the_blind_vs_rebuild_differences_are_only_the_two_disclosed_wiring_causes():
    d = _r("WALL_SURFACE_REGISTER")["blind_vs_rebuild"]
    for x in d["site_differences"]:
        gone = set(x["blind"]["blockers"]) - set(x["rebuild"]["blockers"])
        assert gone and all(b.startswith("PASSAGE_HEAD_NOT_ESTABLISHED") for b in gone)          # WF-L1
    assert d["engine"].startswith("identical frozen") and len(d["causes"]) == 2


def test_second_project_not_run_gates_and_owner_actions():
    assert _r("SECOND_PROJECT_REGRESSION")["state"] == "NOT_RUN"
    d = _r("R8_17_DECISION_REGISTER")
    assert d["gates"] == {"MIGRATION_PLANNING_READY": "YES", "MIGRATION_EXECUTION_READY": "NO",
                          "PRODUCTION_MIGRATION": "NO"} and len(d["answers"]) == 42
    o = _r("OWNER_ACTION_REGISTER")
    assert o["required_now"] == [] and len(o["needed_for_wall_finish_rows"]) == 2
    assert _r("SOURCE_ANCHOR_STATUS")["state"] == "NOT_ESTABLISHED"
