"""M9 S1 tile layout (rectangle exact): hand-checked cutting plans of the owner's 3.00 x 2.00 m bathroom, the takeoff
skill's grid example, the material balance on many rectangles, the owner waste definition, packaging that is never
guessed, and the interfaces that are BLOCKED in S1 (polygon rooms, patterns)."""

from __future__ import annotations

import itertools

import pytest

from engine.source import material_spec as MS
from engine.source import tile_layout as TL
from engine.source import material_result as WP

C = {"joint_m": 0.002, "min_cut_m": 0.10, "min_reusable_m": 0.10, "kerf_m": 0.0, "rotation_allowed": False}
BATH = {"room_id": "B", "length_m": 3.0, "width_m": 2.0}


def test_axis_pieces_for_each_alignment():
    assert TL.axis_pieces(3.0, 1.2, 0.002, "CORNER") == pytest.approx([1.2, 1.2, 0.596])
    assert TL.axis_pieces(2.0, 0.6, 0.002, "CORNER") == pytest.approx([0.6, 0.6, 0.6, 0.194])
    assert TL.axis_pieces(3.0, 0.8, 0.002, "CENTRED_TILE") == pytest.approx([0.296, 0.8, 0.8, 0.8, 0.296])
    cj = TL.axis_pieces(2.0, 0.6, 0.002, "CENTRED_JOINT")
    assert cj == pytest.approx([0.397, 0.6, 0.6, 0.397]) and abs(sum(cj) + 3 * 0.002 - 2.0) < 1e-9
    for D, t, g, a in itertools.product((0.45, 1.0, 2.0, 3.37, 5.4), (0.6, 1.2, 1.6), (0.0, 0.002, 0.003), TL.ALIGNMENTS):
        ps = TL.axis_pieces(D, t, g, a)
        assert all(0 < p <= t + 1e-9 for p in ps)
        assert sum(ps) + g * (len(ps) - 1) <= D + 1e-9 and sum(ps) + g * (len(ps) - 1) >= D - g - 1e-9


def test_owner_bathroom_120x60_cutting_plan_by_hand():
    r = TL.layout(BATH, MS.tile("TILE-120x60"), orientation=0, align_x="CORNER", align_y="CORNER", constraints=C)
    L = r["layout"]
    assert (L["full_tiles"], L["cut_pieces"], L["tiles_opened_for_cuts"], r["units"]["consumed_units"]) == (6, 6, 3, 9)
    assert r["consumed_m2"] == pytest.approx(6.48) and r["placed_m2"] == pytest.approx(2.996 * 1.994)
    assert r["reusable_offcuts_m2"] == pytest.approx(0.604 * 0.6 + 0.604 * 0.212)
    assert r["cutting_waste_m2"] == pytest.approx(6.48 - 5.974024 - 0.490448)
    assert r["cutting_waste_pct"] == pytest.approx(100 * 0.015528 / 6.0, abs=1e-4)
    assert r["joint_m2"] == pytest.approx(6.0 - 5.974024)


def test_owner_bathroom_160x80_cutting_plan_by_hand():
    r = TL.layout(BATH, MS.tile("TILE-160x80"), orientation=90, align_x="CENTRED_TILE", align_y="CORNER", constraints=C)
    assert (r["units"]["full"], r["units"]["cut"], r["units"]["consumed_units"]) == (3, 7, 5)
    assert r["reusable_offcuts_m2"] == pytest.approx(0.208 * 1.6 + 0.208 * 0.406)
    assert r["cutting_waste_m2"] == pytest.approx(6.4 - 2.992 * 1.998 - 0.417248)


def test_comparison_keeps_the_selected_size_primary():
    rows = TL.compare(BATH, [MS.tile(s) for s in MS.OWNER_TILE_SIZES], "TILE-120x60", C)
    by = {r["spec_id"]: r for r in rows}
    assert by["TILE-120x60"]["role"].startswith("SELECTED") and by["TILE-120x60"]["recommendation"] == ""
    assert {r["spec_id"]: r["consumed"] for r in rows} == {"TILE-120x60": 9, "TILE-60x60": 17, "TILE-160x80": 5}
    for sid in ("TILE-60x60", "TILE-160x80"):
        assert by[sid]["role"].startswith("ALTERNATIVE") and by[sid]["recommendation"].startswith("RECOMMENDATION ONLY")
    for r in rows:
        assert r["packaging_state"] == "UNRESOLVED" and r["boxes"] is None          # the registry has no box data
        assert r["feasible"] and r["net_m2"] == pytest.approx(6.0)
    with pytest.raises(TL.LayoutError):
        TL.compare(BATH, [MS.tile("TILE-60x60")], "TILE-120x60", C)


def test_min_waste_search_is_over_the_same_constraints_for_every_candidate():
    b = TL.best(BATH, MS.tile("TILE-120x60"), C)
    assert len(b["tried"]) == 18 and b["objective"] == "CONSUMED_MATERIAL"
    assert min(t["consumed"] for t in b["tried"]) == b["selected"]["units"]["consumed_units"]
    assert len(TL.best(BATH, MS.tile("TILE-60x60"), C)["tried"]) == 9                 # square: one orientation
    w = TL.best(BATH, MS.tile("TILE-120x60"), dict(C, objective="CUTTING_WASTE"))
    assert w["selected"]["cutting_waste_m2"] == min(t["cutting_waste_m2"] for t in w["tried"])
    assert any(c.startswith("LOWER_CONSUMPTION_LAYOUT_EXISTS") for c in w["selected"]["concerns"])


def test_a_layout_with_a_cut_below_the_minimum_is_infeasible():
    room = {"length_m": 1.21, "width_m": 0.6}
    r = TL.layout(room, MS.tile("TILE-60x60"), constraints=dict(C, min_cut_m=0.05))
    assert not r["layout"]["feasible"] and r["state"] == "COMPUTED_REVIEW"
    b = TL.best(room, MS.tile("TILE-60x60"), dict(C, min_cut_m=0.05))
    assert b["feasible"] and not b["selected"]["layout"]["small_cuts_m"]


def test_the_takeoff_skill_grid_example_is_a_cross_check():
    for sid, n in (("TILE-60x60", 42), ("TILE-120x60", 24), ("TILE-160x80", 15)):
        r = TL.layout({"length_m": 4.2, "width_m": 3.6}, MS.tile(sid), constraints={"joint_m": 0.002})
        assert r["layout"]["grid_check"]["tiles"] == n == r["layout"]["tiles_without_reuse"] == r["units"]["consumed_units"]


@pytest.mark.parametrize("X,Y", [(3.0, 2.0), (2.3, 3.2), (5.4, 4.2), (1.0, 0.9), (7.13, 2.41), (0.55, 0.55)])
def test_material_balance_on_every_layout(X, Y):
    for sid in MS.OWNER_TILE_SIZES + ("CUSTOM",):
        spec = MS.custom_tile(0.9, 0.3) if sid == "CUSTOM" else MS.tile(sid)
        for o, ax, ay in itertools.product(TL.ORIENTATIONS, TL.ALIGNMENTS, TL.ALIGNMENTS):
            for c in (C, dict(C, min_reusable_m=None), dict(C, kerf_m=0.003, rotation_allowed=True)):
                r = TL.layout({"length_m": X, "width_m": Y}, spec, orientation=o, align_x=ax, align_y=ay, constraints=c)
                WP.check(r)
                parts = r["placed_m2"] + r["cutting_waste_m2"] + r["reusable_offcuts_m2"]
                assert parts == pytest.approx(r["consumed_m2"], abs=1e-5)
                assert r["placed_m2"] + r["joint_m2"] == pytest.approx(X * Y, abs=1e-6)
                assert r["units"]["consumed_units"] <= r["layout"]["tiles_without_reuse"]
                if c.get("min_reusable_m") is None:
                    assert r["units"]["consumed_units"] == r["layout"]["positions"] and r["reusable_offcuts_m2"] == 0


def test_packaging_is_resolved_only_with_box_data():
    t = MS.with_packaging(MS.tile("TILE-120x60"), pieces_per_box=2, source="test parameter")
    r = TL.layout(BATH, t, constraints=C)
    p = r["packaging"]
    assert p["state"] == "RESOLVED" and p["packs"] == 5 and p["packaging_surplus_m2"] == pytest.approx(10 * 0.72 - 6.48)
    assert r["spare_allowance"]["state"] == "NOT_SET" and p["procurement_packs"] == 5
    s = TL.layout(BATH, t, constraints=dict(C, spare_allowance=WP.spare(10, "owner test decision")))
    assert s["packaging"]["spare_units"] == 1 and s["packaging"]["procurement_packs"] == 5
    with pytest.raises(WP.ResultError):
        WP.spare(5)                                                                  # no source


def test_polygon_rooms_and_patterns_are_blocked_never_approximated():
    L = {"polygon": [[0, 0], [4, 0], [4, 2.5], [2, 2.5], [2, 3.5], [0, 3.5]]}
    r = TL.layout(L, MS.tile("TILE-60x60"), constraints=C)
    assert r["state"] == "BLOCKED" and r["blocked_by"].startswith("POLYGON_OPTIMIZER_NOT_IMPLEMENTED")
    assert r["consumed_m2"] is None and r["packaging"] is None
    rot = {"polygon": [[0, 0], [2.0, 1.5], [1.1, 2.7], [-0.9, 1.2]]}                 # a rotated 2.5 x 1.5 rectangle
    r2 = TL.layout(rot, MS.tile("TILE-60x60"), constraints=C)
    assert r2["state"] != "BLOCKED" and r2["net_installed_m2"] == pytest.approx(2.5 * 1.5)
    hb = dict(MS.tile("TILE-60x60"), pattern="HERRINGBONE")
    assert TL.layout(BATH, hb, constraints=C)["blocked_by"].startswith("PATTERN_NOT_IMPLEMENTED")
    with pytest.raises(TL.LayoutError):
        TL.layout(BATH, MS.tile("TILE-60x60"), constraints={"min_cut_m": 0.1})       # no joint width


def test_wet_rooms_flag_falls_and_offcut_reuse_is_never_credited_across_rooms():
    r = TL.layout(BATH, MS.tile("TILE-60x60"), constraints=dict(C, wet_room=True))
    assert any(c.startswith("FALLS_TO_DRAIN_NOT_MODELLED") for c in r["concerns"])
    assert any("never credited to another room" in a for a in r["assumptions"])
    assert r["waste_if_offcuts_discarded_m2"] == pytest.approx(r["cutting_waste_m2"] + r["reusable_offcuts_m2"])
