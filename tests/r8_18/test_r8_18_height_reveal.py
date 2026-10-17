"""R8.18 §3 / §14-§17: WALL_HEIGHT_AUTHORITY_POLICY_V1 (height as a scoped evidence object) and
REVEAL_FINISH_POLICY_V1 (physical ownership from the frame plane; finish states). Synthetic only, frozen before
Qortuba."""

from __future__ import annotations

from engine.source import reveal_finish as RF, wall_height as WH

SCOPE = {"project": "P", "revision": "R", "floor": "F2", "trade": "PLASTER"}


def test_the_best_ranked_established_candidate_governs_and_all_are_kept():
    c = [WH.candidate("OWNER_PROJECT_FACT", 3.15, "OWNER@v1"), WH.candidate("SECTION_CLEAR_HEIGHT", 3.05, "SECTION A")]
    r = WH.resolve(SCOPE, c)
    assert r["state"] == WH.ESTABLISHED and r["value_m"] == 3.05 and r["governing"] == "SECTION_CLEAR_HEIGHT"
    assert len(r["candidates"]) == 2


def test_floor_to_floor_alone_is_never_a_wall_height():
    r = WH.resolve(SCOPE, [WH.candidate("FLOOR_TO_FLOOR", 4.0, "LEVEL TEXT")])
    assert r["state"] == WH.BLOCKED and r["value_m"] is None


def test_a_derivation_with_one_unknown_component_is_blocked_and_never_defaulted():
    d = WH.derive(4.0, "LEVEL TEXT", {"beam_or_soffit_zone": {"value_m": 0.6, "authority": "SECTION"},
                                      "ceiling_service_decor_zone": {"value_m": None, "authority": None},
                                      "floor_buildup": {"value_m": 0.1, "authority": "SPEC"}})
    assert d["state"] == WH.BLOCKED and d["missing"] == ["ceiling_service_decor_zone"] and d["value_m"] is None
    ok = WH.derive(4.0, "LEVEL TEXT", {"beam_or_soffit_zone": {"value_m": 0.6, "authority": "SECTION"},
                                       "ceiling_service_decor_zone": {"value_m": 0.15, "authority": "RCP"},
                                       "floor_buildup": {"value_m": 0.1, "authority": "SPEC"}})
    assert ok["state"] == WH.ESTABLISHED and abs(ok["value_m"] - 3.15) < 1e-9


def test_a_blocked_derivation_falls_to_the_owner_fact_rank():
    d = WH.derive(4.0, "LEVEL", {"beam_or_soffit_zone": {"value_m": None, "authority": None}})
    c = [dict(WH.candidate("DERIVED_CLEAR_HEIGHT", d["value_m"], None), derivation=d),
         WH.candidate("OWNER_PROJECT_FACT", 3.15, "OWNER@v1")]
    r = WH.resolve(SCOPE, c)
    assert r["governing"] == "OWNER_PROJECT_FACT" and r["value_m"] == 3.15


def test_a_finish_height_above_an_unproven_available_height_is_only_a_potential_conflict_never_clipped():
    out = WH.conflict({"WALL_TILE": 3.2, "PLASTER": 3.15}, {"value_m": 3.15, "proven": False, "basis": "rationale"})
    assert [x["trade"] for x in out] == ["WALL_TILE"] and out[0]["state"] == "POTENTIAL_PHYSICAL_CONFLICT_NOT_PROVEN"
    assert WH.conflict({"WALL_TILE": 3.2}, {"value_m": 3.1, "proven": True})[0]["state"] == "PHYSICAL_CONFLICT"
    assert "a company-wide wall height constant" in WH.policy_record()["never"]


def test_the_frame_plane_splits_reveal_ownership_and_a_flush_frame_leaves_no_reveal():
    s = RF.frame_split(0.15, [0.05, 0.15], side_a="PAINTRY", side_b="HALL")      # tracks from 50 mm to the HALL face
    assert s["PAINTRY"] == 0.05 and s["HALL"] == 0.0 and s["state"] == "ESTABLISHED"
    leaf = RF.frame_split(0.15, [0.0], side_a="BATH", side_b="HALL")             # leaf on the BATH face
    assert leaf["BATH"] == 0.0 and abs(leaf["HALL"] - 0.15) < 1e-9
    assert RF.frame_split(0.15, [], side_a="A", side_b="B")["state"] == RF.UNRESOLVED


def test_finish_states_default_plaster_paint_only_on_painted_dry_porcelain_only_explicit():
    assert RF.finish_state(ownership_established=True, owner_painted_dry=True) == RF.PLASTER_AND_PAINT
    assert RF.finish_state(ownership_established=True, owner_painted_dry=False) == RF.PLASTER_DEFAULT
    assert RF.finish_state(ownership_established=True, owner_painted_dry=False, explicit="PORCELAIN") == \
        RF.PORCELAIN_EXPLICIT
    assert RF.finish_state(ownership_established=False, owner_painted_dry=True) == RF.UNRESOLVED
    assert "porcelain because an adjacent room is wet" in RF.policy_record()["never"]
    assert RF.TRADES[RF.PLASTER_DEFAULT] == ("PLASTER",)
