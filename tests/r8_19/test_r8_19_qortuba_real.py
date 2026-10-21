"""R8.19 on the committed registers: exposed column / duct finishes, complete wall-finish rows rebuilt from surface
records (WF3-L1 / WF3-L2 disclosed), the sliding-door south reveal physicality, the regression of every existing row,
the BOQ presentation layer, closure review packets, gates."""

from __future__ import annotations

import json
import math
from pathlib import Path

from engine.source import boq_report as BR, exposed_finish as EF, reveal_physicality as RP, waterproofing as WP

REG = Path(__file__).parent / "registers"
REG18 = Path(__file__).resolve().parents[1] / "r8_18" / "registers"
ROWS = ("Q-03", "Q-03P", "Q-11", "Q-12", "Q-13", "Q-14")
TRADE_ROWS = ("DRY_WALL_PLASTER", "DRY_WALL_PAINT", "WET_SERVICE_WALL_TILE", "WET_WALL_TILE_PREP",
              "WET_SERVICE_REVEAL_PLASTER")


def _r(n, reg=REG):
    return json.loads((reg / f"{n}.json").read_text())


def rows():
    st = _r("QORTUBA_R8_19_STATUS")
    return {k: st["extra_rows"][k] for k in TRADE_ROWS}


# ------------------------------------------------------------------------------- columns / duct
def test_exposed_columns_follow_the_room_and_hidden_faces_get_nothing():
    cd = _r("COLUMN_DUCT_FINISH_REGISTER")
    c = cd["columns"]
    assert c["exposure_state"] == "PASS" and not c["errors"]
    assert set(c["contribution_m2"]) == {"DRY_WALL_PLASTER", "DRY_WALL_PAINT", "WET_SERVICE_WALL_TILE",
                                         "WET_WALL_TILE_PREP"}
    assert c["contribution_m2"]["DRY_WALL_PLASTER"] == c["contribution_m2"]["DRY_WALL_PAINT"]
    assert c["contribution_m2"]["WET_SERVICE_WALL_TILE"] == c["contribution_m2"]["WET_WALL_TILE_PREP"]
    for k, v in c["per_segment"].items():
        assert abs(v["exposed_total_m"] + v["hidden_m"] - v["length_m"]) < 1e-6
    hid = cd["hidden_faces_excluded"]
    assert hid["column_segments_hidden"] and hid["column_segments_partial"] and hid["finish_on_hidden_m2"] == 0.0
    exposed = {(f["site"], f["segment"]) for f in c["exposed_faces"]}
    assert not [k for k in hid["column_segments_hidden"] if any(k == s for _site, s in exposed)]


def test_the_duct_is_finished_on_its_four_exposed_faces_and_its_lining_is_hidden():
    d = _r("COLUMN_DUCT_FINISH_REGISTER")["duct"]
    assert d["exposure_state"] == "PASS" and set(d["contribution_m2"]) == {"DRY_WALL_PLASTER", "DRY_WALL_PAINT"}
    assert set(d["owner_physical_authority"].values()) == {"OWNER_PHYSICAL_OBSTACLE"}
    st = {k.split("|")[1]: v["state"] for k, v in d["per_segment"].items()}
    assert {s for h, s in st.items() if h == "H2061"} == {EF.HIDDEN}
    assert len([f for f in d["exposed_faces"] if "|H2060|" in f["segment"]]) == 4


def test_skirting_is_not_duplicated_by_the_new_finish_rules():
    sk = _r("SKIRTING_REGISTER")
    assert all(v["same_faces"] for v in sk["column_duct_no_duplicate"].values())
    assert sk["regression_vs_r8_18"]["unchanged"] and sk["regression_vs_r8_18"]["v4_edited"] is False
    assert _r("HIDDEN_PROFILE_REGISTER")["regression_vs_r8_18"]["unchanged"]


# ------------------------------------------------------------------------------- trade rows
def test_every_wall_finish_row_is_complete_rebuilt_from_surfaces_and_reconciles():
    for k, v in rows().items():
        assert v["state"] == "COMPUTED_SHADOW_COMPLETE" and v["COMPLETE_M2"] == v["AUTHORISED_SUBTOTAL_M2"]
    pl, pa = _r("PLASTER_REGISTER"), _r("PAINT_REGISTER")
    for reg, key in ((pl, "DRY_WALL_PLASTER"), (pl, "WET_SERVICE_REVEAL_PLASTER"), (pa, "DRY_WALL_PAINT"),
                     (_r("WALL_TILE_REGISTER"), "WET_SERVICE_WALL_TILE"),
                     (_r("WALL_TILE_PREP_REGISTER"), "WET_WALL_TILE_PREP")):
        r = reg[key]
        assert r["reconciliation"]["reconciles"] and not r["unresolved_contributors"] and r["FINAL"] is None
        assert abs(math.fsum(r["by_kind_m2"].values()) - r["COMPLETE_M2"]) < 1e-5
    assert abs(pl["PLASTER_ALL_SURFACES_M2"] - pl["DRY_WALL_PLASTER"]["COMPLETE_M2"] -
               pl["WET_SERVICE_REVEAL_PLASTER"]["COMPLETE_M2"]) < 1e-6


def test_paint_equals_dry_plaster_by_surface_identity_and_prep_equals_tile():
    pa = _r("PAINT_REGISTER")
    assert pa["vs_dry_plaster"]["same_surface_set"] and not pa["vs_dry_plaster"]["only_paint"]
    assert _r("WALL_TILE_PREP_REGISTER")["same_physical_surfaces_as_wall_tile"]
    assert _r("WALL_TILE_REGISTER")["porcelain_reveals"] == "NONE"


def test_the_rebuilt_wall_plane_equals_the_r8_18_method_b_net_room_by_room():
    pc = _r("QORTUBA_R8_19_STATUS")["plane_check_vs_r8_18_method_b"]
    assert pc["all_agree"] and len(pc["rooms"]) == 16


def test_wf3_l1_and_wf3_l2_are_the_only_blind_vs_rebuild_differences():
    b = _r("QORTUBA_R8_19_STATUS")["blind_vs_rebuild"]
    rm = b["WF3-L1"]["removed_plane_copies"]
    for k, v in b["trade_rows"].items():
        assert abs(v["delta"] + rm[k]["area_m2"]) < 1e-6
    assert b["WF3-L2"]["rebuild_guard"]["state"] == "PASS" and b["WF3-L1"]["blind_physical_guard"]["state"] == "FAIL"
    assert sum(len(x) for x in b["WF3-L1"]["blind_physical_guard"]["duplicates_by_row"].values()) == \
        sum(v["count"] for v in rm.values())
    assert all(_r("QORTUBA_R8_19_STATUS")["reproduces"]["r8_19_blind"].values())


# ------------------------------------------------------------------------------- reveals
def test_the_south_sliding_reveal_is_physical_by_the_band_end_and_the_fixture_is_rejected():
    s = _r("SLIDING_DOOR_REVEAL_PHYSICALITY")
    assert all(j["state"] == RP.ESTABLISHED for j in s["jambs"])
    south = s["south_jamb"]
    assert [e["kind"] for e in south["evidence"]] == ["ESTABLISHED_WALL_BAND_END"]
    assert south["rejected"][0]["layer"] == "FIXTURE"
    band = s["bands_used"]["WB-fa9e752f77ae497d"]
    assert band["state"] == "WALL_BAND_ESTABLISHED" and "OPENING_JAMB" in [e["kind"] for e in band["ends"]]
    rv = _r("REVEAL_FINISH_REGISTER")
    assert rv["unresolved"] == [] and rv["by_physicality"][RP.UNRESOLVED] == 0


# ------------------------------------------------------------------------------- regression
def test_waterproofing_floor_ceiling_and_marble_rows_are_unchanged():
    assert all(_r("WATERPROOFING_REGISTER")["regression_vs_r8_18"]["unchanged"].values())
    st, s18 = _r("QORTUBA_R8_19_STATUS"), _r("QORTUBA_R8_18_STATUS", REG18)
    for rid in ROWS:
        assert st["six_rows"][rid]["VALUE"] == s18["six_rows"][rid]["VALUE"]
        assert set(st["digest_vs_r8_18"][rid].values()) == {"SAME"}
    assert _r("MARBLE_THRESHOLD_REGISTER")["regression_vs_r8_18"]["unchanged"]
    assert st["extra_rows"][WP.FLOOR]["value_m2"] == _r("WATERPROOFING_REGISTER", REG18)["rows"][WP.FLOOR]["value"]


# ------------------------------------------------------------------------------- BOQ
def test_the_boq_report_copies_traces_and_never_approves():
    sh = _r("BOQ_REPORT_SHADOW")
    rep, ev = sh["report"], sh["evidence_rows"]
    items = _r("BOQ_REPORT_SCHEMA")["items"]
    assert BR.validate(rep, ev, items)["state"] == "PASS" and sh["validation"]["state"] == "PASS"
    assert sh["approved_for_boq"] == 0 and sh["status_counts"][BR.RELEASED] == 0 and rep["pricing"] is None
    tot = {r["evidence_row"]: r["QTY"] for r in rep["rows"] if r["ROW_KIND"] == "TOTAL"}
    st = _r("QORTUBA_R8_19_STATUS")
    for k in TRADE_ROWS:
        assert tot[k] == st["extra_rows"][k]["COMPLETE_M2"]
    for rid in ROWS:
        assert tot[rid] == st["six_rows"][rid]["VALUE"]
    assert all(set(BR.TRACE) <= set(r["trace"]) for r in rep["rows"])


# ------------------------------------------------------------------------------- closures / gates
def test_closure_packets_are_prepared_never_self_approved_and_gates_hold():
    c = _r("CLOSURE_RELEASE_STATUS")
    assert set(c["review_packets"]) == {"I1471", "H2430", "H2431"} and c["self_approved"] is False
    assert all(p["conditions"]["HUMAN_REVIEW"].startswith("PENDING") and p["closure_digest"]
               for p in c["review_packets"].values())
    assert c["production"] == "NO" and not c["released"]
    d = _r("R8_19_DECISION_REGISTER")
    assert d["gates"] == {"MIGRATION_PLANNING_READY": "YES", "MIGRATION_EXECUTION_READY": "NO",
                          "PRODUCTION_MIGRATION": "NO"}
    assert len(d["answers"]) == 42
    assert _r("SOURCE_ANCHOR_STATUS")["state"] == "NOT_ESTABLISHED"
    assert _r("SECOND_PROJECT_REGRESSION")["state"] == "NOT_RUN"
    assert _r("OWNER_ACTION_REGISTER")["required_now"] == []
