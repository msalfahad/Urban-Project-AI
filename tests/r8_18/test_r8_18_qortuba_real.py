"""R8.18 on the committed registers: scoped wall heights, WF-O1 fixed (both area paths reconcile everywhere), the dry
plaster / paint and wet tile rows (authorised subtotals, COMPLETE null while columns / duct are unresolved), reveals,
waterproofing, the existing-row regression, the disclosed WF2-L1 correction, gates."""

from __future__ import annotations

import json
import math
from pathlib import Path

from engine.source import reveal_finish as RF, waterproofing as WP

REG = Path(__file__).parent / "registers"
REG17 = Path(__file__).resolve().parents[1] / "r8_17" / "registers"
ROWS = ("Q-03", "Q-03P", "Q-11", "Q-12", "Q-13", "Q-14")
ENGINE = Path(__file__).resolve().parents[2] / "engine"


def _r(n, reg=REG):
    return json.loads((reg / f"{n}.json").read_text())


# ------------------------------------------------------------------------------- heights
def test_heights_are_scoped_evidence_objects_and_no_company_constant_exists():
    h = _r("QORTUBA_WALL_HEIGHT_REGISTER")
    g = h["governing"]
    for k in ("DRY_INTERNAL_ROOM|PLASTER", "DRY_INTERNAL_ROOM|PAINT"):
        assert g[k]["value_m"] == 3.15 and g[k]["governing"] == "OWNER_PROJECT_FACT"
        assert g[k]["authority"].startswith("QORTUBA-NEW-DRY-WALL-FINISH-HEIGHT-OWNER-001")
        assert h["derivation"][k]["state"] == "BLOCKED" and h["derivation"][k]["value_m"] is None
    for k in ("WET_SERVICE_ROOM|WALL_TILE", "SERVICE_ROOM|WALL_TILE"):
        assert g[k]["value_m"] == 3.2 and "WET-SERVICE-FINISH" in g[k]["authority"]
    assert h["rationale_is_formula"] is False and h["blind_equal"]
    assert [c["state"] for c in h["conflicts"]] == ["POTENTIAL_PHYSICAL_CONFLICT_NOT_PROVEN"]
    src = "\n".join(p.read_text() for p in ENGINE.rglob("*.py"))
    assert "URBAN_DEFAULT_WALL_HEIGHT" not in src


# ------------------------------------------------------------------------------- WF-O1 / V2
def test_every_site_reconciles_by_both_methods_and_no_surface_is_counted_twice():
    ws, wo = _r("WALL_SURFACE_REGISTER"), _r("WF_O1_ROOT_CAUSE")
    assert ws["all_sites_reconcile"] and wo["all_sites_reconcile"] and ws["blind_equal_per_site"]
    for v in ws["per_site"].values():
        for f in v["faces"].values():
            r = f["reconciliation"]
            assert f["state"] == "COMPUTED" and r["state"] == "PASS" and r["difference_m2"] <= r["tolerance_m2"]
            a = f["areas_m2"]
            assert abs(a["WALL_PLANE_NET"] - a["WALL_PLANE_NET_METHOD_B"]) <= r["tolerance_m2"]
    assert ws["double_count_guard"]["state"] == "PASS" and not ws["double_count_guard"]["duplicates"]
    assert ws["topology_closures"]["area_m2"] == 0.0
    for x in wo["v1_failure_on_qortuba"]:                     # V1's correct primary form = V2's net, same site
        assert x["agree_when_the_window_plane_is_included"]
        assert ws["per_site"][x["site"]]["faces"][x["trade"]]["areas_m2"]["WALL_PLANE_NET"] == x["net_primary_m2"]


def test_windows_keep_their_below_sill_and_above_head_surfaces():
    ws = _r("WALL_SURFACE_REGISTER")
    wins = [o for v in ws["per_site"].values() for f in v["faces"].values() for o in f["openings"]
            if o["kind"] == "WINDOW"]
    assert wins and all(o["state"] == "COMPUTED" and o["contained"] for o in wins)
    assert all(o["below_sill_m2"] > 0 and o["above_opening_m2"] >= 0 for o in wins)
    assert all(abs(o["rectangle_m2"] - o["width_m"] * o["height_m"]) < 1e-5 for o in wins)


# ------------------------------------------------------------------------------- trades
def test_dry_plaster_and_paint_are_authorised_per_room_with_complete_null():
    pl, pa = _r("PLASTER_REGISTER"), _r("PAINT_REGISTER")
    for t in (pl, pa):
        assert t["state"] == "COMPUTED_SHADOW_WITH_UNRESOLVED" and t["COMPLETE_M2"] is None
        assert t["reconciliation"]["reconciles"] and all(v["components_reconcile"] for v in t["per_room"].values())
        assert all(v["height_m"] == 3.15 and v["class"] == "DRY_INTERNAL_ROOM" for v in t["per_room"].values())
        assert t["unresolved_contributors"] and t["unresolved_area_m2"] > 0
    assert pa["vs_dry_plaster"]["equal"] and pl["row_id"] == "DRY_WALL_PLASTER"
    w = pl["WET_SERVICE_REVEAL_PLASTER"]
    assert w["AUTHORISED_M2"] > 0 and len(w["unresolved_reveals"]) == 1


def test_wall_tile_stays_at_3_20_and_prep_is_a_separate_equal_row():
    wt = _r("WALL_TILE_REGISTER")
    assert wt["COMPLETE_M2"] is None and wt["reconciliation"]["reconciles"]
    assert all(v["height_m"] == 3.2 for v in wt["per_room"].values())
    assert {tuple(v["zones"]) for v in wt["per_room"].values()} == {("BATH",), ("PAINTRY",)}
    assert wt["prep_equals_tile"] and wt["WET_WALL_TILE_PREP"]["row"] == "WET_WALL_TILE_PREP"
    assert all(v["jamb_reveals_m2"] == 0.0 and v["head_reveals_m2"] == 0.0 for v in wt["per_room"].values())


def test_column_and_duct_faces_are_unresolved_never_silently_excluded():
    cd, oa = _r("COLUMN_DUCT_FINISH_REGISTER"), _r("OWNER_ACTION_REGISTER")
    assert set(cd["method"]["column_faces"].values()) == {"UNRESOLVED"}
    assert set(cd["method"]["obstacle_faces"].values()) == {"UNRESOLVED"}
    assert cd["columns"] and cd["duct_faces"] and cd["r8_17_misreading"]["disclosed"]
    assert [q["id"] for q in oa["needed_to_complete_rows"]] == ["QORTUBA_NEW_COLUMN_FACE_FINISH"]
    assert oa["required_now"] == [] and "duct" in oa["do_not_ask"]
    tot = math.fsum(x["area_m2"] for x in cd["columns"] + cd["duct_faces"])
    pl, wt = _r("PLASTER_REGISTER"), _r("WALL_TILE_REGISTER")
    assert abs(tot - pl["unresolved_area_m2"] - wt["unresolved_area_m2"]) < 1e-6


# ------------------------------------------------------------------------------- reveals
def test_reveals_default_to_plaster_porcelain_never_and_paint_only_in_dry_rooms():
    rv = _r("REVEAL_FINISH_REGISTER")
    assert rv["porcelain"] == "NONE (no explicit authority)"
    for x in rv["reveals"]:
        if x["finish"] == RF.PLASTER_AND_PAINT:
            assert x["owner_class"] == "DRY_INTERNAL_ROOM"
        if x.get("owner_class") in ("WET_SERVICE_ROOM", "SERVICE_ROOM"):
            assert "PAINT" not in x["trades"] and x["finish"] in (RF.PLASTER_DEFAULT, RF.UNRESOLVED)
    assert [x["surface"] for x in rv["unresolved"]] == ["RIGHT_JAMB"]
    assert rv["sliding_door_split"]["state"] == "ESTABLISHED"
    assert rv["hall_lobby_soffit_vs_q14"]["equal"]
    full = [x for x in rv["reveals"] if x["kind"] == "OPEN_PASSAGE_FULL_HEIGHT"]
    assert [x["surface"] for x in full] == ["LEFT_JAMB"]


def test_wf2_l1_is_the_only_blind_vs_rebuild_difference():
    d = _r("REVEAL_FINISH_REGISTER")["blind_vs_rebuild"]
    assert len(d["reveal_differences"]) == 1
    x = d["reveal_differences"][0]
    assert x["blind"]["finish"] == RF.PLASTER_DEFAULT and x["rebuild"]["finish"] == RF.UNRESOLVED
    for t, v in d["trade_row_differences"].items():
        assert v["blind"]["AUTHORISED_SUBTOTAL_M2"] == v["rebuild"]["AUTHORISED_SUBTOTAL_M2"]


# ------------------------------------------------------------------------------- waterproofing
def test_waterproofing_floor_and_gross_upturn_with_doorways_kept():
    w = _r("WATERPROOFING_REGISTER")
    assert w["state"] == "COMPUTED_SHADOW" and w["blind_equal"] and not w["doorways_deducted"]
    assert w["rows"][WP.UPTURN]["upturn_height_m"] == 0.15 and w["skirting_path_used"] is False
    assert all(v["perimeter_reconciles"] and v["upturn_height_m"] == 0.15 for v in w["per_room"].values())
    assert abs(math.fsum(v[WP.FLOOR] for v in w["per_room"].values()) - w["rows"][WP.FLOOR]["value"]) < 1e-6
    assert abs(math.fsum(v[WP.UPTURN] for v in w["per_room"].values()) - w["rows"][WP.UPTURN]["value"]) < 1e-6
    assert all(v > 0 for v in w["opening_lengths_in_upturn_m"].values())
    assert w["anti_calibration"]["is_target"] is False


# ------------------------------------------------------------------------------- regression / gates
def test_existing_rows_skirting_hidden_profile_and_marble_are_unchanged():
    s, s17 = _r("QORTUBA_R8_18_STATUS"), _r("QORTUBA_R8_17_STATUS", REG17)
    for rid in ROWS:
        assert s["six_rows"][rid]["VALUE"] == s17["six_rows"][rid]["VALUE"]
        assert s["six_rows"][rid]["STATE"] == s17["six_rows"][rid]["STATE"]
        assert set(s["digest_vs_r8_17"][rid].values()) == {"SAME"}
    assert all(s["old_revision_unchanged_vs_r8_17"].values())
    assert all(s["reproduces"]["r8_18_blind"].values()) and all(s["reproduces"]["v4_blind"].values())
    assert _r("SKIRTING_REGISTER")["regression_vs_r8_17"]["unchanged"]
    assert _r("HIDDEN_PROFILE_REGISTER")["regression_vs_r8_17"]["unchanged"]
    assert _r("MARBLE_THRESHOLD_REGISTER")["regression_vs_r8_17"]["unchanged"]


def test_gates_anchor_second_project_and_decisions():
    d = _r("R8_18_DECISION_REGISTER")
    assert d["gates"] == {"MIGRATION_PLANNING_READY": "YES", "MIGRATION_EXECUTION_READY": "NO",
                          "PRODUCTION_MIGRATION": "NO"}
    assert len(d["answers"]) == 43
    assert _r("SOURCE_ANCHOR_STATUS")["state"] == "NOT_ESTABLISHED"
    assert _r("SECOND_PROJECT_REGRESSION")["state"] == "NOT_RUN"
    assert _r("CLOSURE_RELEASE_STATUS")["production"] == "NO"
    assert _r("QORTUBA_R8_18_STATUS")["production_migration"] == "NO"
