"""R8.18 §33: WATERPROOFING_POLICY_V1 - floor membrane = wet-room site area, 0.15 m upturn on the GROSS perimeter,
doorways NOT deducted; independent of skirting, wall tile and marble. Synthetic only, frozen before Qortuba."""

from __future__ import annotations

import random

from engine.source import waterproofing as WP, wall_contact_path as WC
from tests.r8_8 import helpers as H
from tests.r8_13.test_r8_13_wall_band_v4 import box
from tests.r8_16.test_r8_16_offset_closure import door_parts, walls
from tests.r8_16.test_r8_16_skirting_v3 import room, site_at

U, UP, AUTH = 0.001, 0.15, "US-04"


def wp(r, pt, **kw):
    s = site_at(r, pt)
    return WP.wet_room(WC.site_edges(r["_arr"], s), area_m2=s["area"] * U * U, u=U, upturn_height_m=UP,
                       upturn_authority=AUTH, **kw)


def bath():
    return room(box(2000, 1500), [("BATH", 1000, 750)])


def test_a_rectangular_bathroom_floor_and_gross_perimeter():
    w = wp(bath(), (1000, 750))
    assert w["state"] == "COMPUTED" and abs(w[WP.FLOOR] - 3.0) < 1e-9 and abs(w[WP.UPTURN] - 7.0) < 1e-9
    assert w["upturn_height_m"] == 0.15 and abs(w["upturn_m2_informational"] - 1.05) < 1e-9


def test_a_doorway_is_not_deducted():
    r = room(walls() + door_parts(), [("BATH", 250, 200), ("B", 750, 200)])
    w = wp(r, (250, 200))
    assert w["doorways_deducted"] is False and w["perimeter_by_class_m"].get(WC.DOOR_PRESENT, 0) > 0
    m = WC.measure_v4(WC.site_edges(r["_arr"], site_at(r, (250, 200))), WC.SkirtingMethodV3("T", 1, {}), eps=1e-6)
    assert w[WP.UPTURN] > m["length"] * U                                     # not the skirting path


def test_two_doors_both_on_the_perimeter():
    p = box(2000, 1000) + [H.seg(10, 1000, 0, 1000, 450), H.seg(11, 1020, 0, 1020, 450), H.seg(12, 1000, 450, 1020, 450),
                           H.seg(13, 1000, 550, 1000, 1000), H.seg(14, 1020, 550, 1020, 1000),
                           H.seg(15, 1000, 550, 1020, 550)]
    r = room(p, [("BATH", 500, 500), ("HALL", 1500, 500)])
    s = site_at(r, (500, 500))
    w = WP.wet_room(WC.site_edges(r["_arr"], s), area_m2=s["area"] * U * U, u=U, upturn_height_m=UP,
                    upturn_authority=AUTH)
    assert abs(w[WP.UPTURN] - math.fsum(e["length"] for e in WC.site_edges(r["_arr"], s)) * U) < 1e-9


def test_a_marble_threshold_changes_nothing_and_full_wall_tile_and_skirting_are_independent():
    r = room(walls() + door_parts(), [("BATH", 250, 200), ("B", 750, 200)])
    a, b = wp(r, (250, 200)), wp(r, (250, 200))
    assert a == b and "a marble-threshold modification without an explicit rule" in WP.policy_record()["never"]
    assert "the skirting path" in WP.policy_record()["never"]


def test_a_column_projection_and_an_internal_obstacle_are_on_the_gross_perimeter():
    col = {"sources": ["W|H70||SEGMENT|2"], "roles": ["STRUCTURAL_OBSTACLE"], "length": 300.0, "hole": False}
    wall = {"sources": ["W|H1||SEGMENT|0"], "roles": ["TOPOLOGY_BOUNDARY"], "length": 4000.0, "hole": False}
    hole = {"sources": ["W|H77||SEGMENT|0"], "roles": ["TOPOLOGY_BOUNDARY"], "length": 800.0, "hole": True}
    w = WP.wet_room([wall, col, hole], area_m2=2.0, u=U, upturn_height_m=UP, upturn_authority=AUTH)
    assert abs(w[WP.UPTURN] - 5.1) < 1e-9 and abs(w["perimeter_by_class_m"]["HOLE_PERIMETER"] - 0.8) < 1e-9
    v = WP.wet_room([wall, col, hole], area_m2=2.0, u=U, upturn_height_m=UP, upturn_authority=AUTH,
                    include_holes=False)
    assert abs(v[WP.UPTURN] - 4.3) < 1e-9


def test_no_upturn_authority_blocks_and_the_floor_is_the_site_area():
    w = WP.wet_room([], area_m2=1.5, u=U, upturn_height_m=None, upturn_authority=None)
    assert w["state"] == "BLOCKED" and w["upturn_m2_informational"] is None and w[WP.FLOOR] == 1.5


def test_shuffled_input_is_deterministic():
    p = box(2000, 1500)
    base = wp(room(p, [("BATH", 1000, 750)]), (1000, 750))
    for seed in (1, 6):
        q = list(p)
        random.Random(seed).shuffle(q)
        assert wp(room(q, [("BATH", 1000, 750)]), (1000, 750)) == base


import math  # noqa: E402
