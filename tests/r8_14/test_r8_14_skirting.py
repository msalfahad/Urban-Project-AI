"""R8.14 §39: the skirting wall-contact path (classification only; no quantity is published)."""

from __future__ import annotations

import json
import math
from pathlib import Path

from engine.source import owner_facts as OF, owner_method_facts as MF, room_topology as RT, topology_closures as TC
from engine.source import topology as T, wall_contact_path as WC
from tests.r8_8 import helpers as H
from tests.r8_13.test_r8_13_wall_band_v4 import box, rect, wall

ROOT = Path(__file__).resolve().parents[2]
FACTS = {f["fact_id"]: f for f in json.loads((ROOT / "data/registry/OWNER_METHOD_FACTS.json").read_text())["facts"]}


def room(parts, texts):
    return RT.run(H.inp(parts, texts=texts), frame_insert=None, closure_policy=TC.POLICY_ID)


def site_path(r, pt, **kw):
    sid, _ = T.locate(r["_arr"], r["sites"], pt, 0.0)
    s = next(z for z in r["sites"] if z["site_id"] == sid)
    return WC.path(WC.site_edges(r["_arr"], s), **kw)


def single_room(extra=()):
    return room(box(500, 400) + list(extra), [H.text(5, "BED", 250, 200)])


def test_a_dry_room_with_real_walls_has_its_whole_wall_path():
    p = site_path(single_room(), (250, 200))
    assert abs(p["on_path_length"] - 1800.0) < 1e-6 and set(p["by_class"]) == {WC.REAL_WALL_FACE}


def test_a_built_in_wardrobe_or_loose_furniture_against_the_wall_keeps_the_path():
    wardrobe = rect(30, 0, 300, 200, 400, layer="FURNITURE")                      # against two walls
    sofa = rect(31, 200, 100, 350, 160, layer="FURNITURE")
    assert abs(site_path(single_room(wardrobe + sofa), (250, 250))["on_path_length"] - 1800.0) < 1e-6


def door_rooms():
    walls = [H.seg(1, 0, 0, 1000, 0), H.seg(2, 1000, 0, 1000, 400), H.seg(3, 1000, 400, 0, 400), H.seg(4, 0, 400, 0, 0),
             H.seg(5, 495, 0, 495, 150), H.seg(6, 505, 0, 505, 150), H.seg(7, 495, 150, 505, 150),
             H.seg(8, 495, 250, 495, 400), H.seg(9, 505, 250, 505, 400), H.seg(10, 495, 250, 505, 250)]
    door = [H.part(20, "ARC", (495, 150, 100, 0.0, math.pi / 2), layer="DOOR", path=("70",)),
            H.seg(21, 495, 150, 495, 250, layer="DOOR", path=("70",))]
    return room(walls + door, [H.text(5, "A", 250, 200), H.text(6, "B", 750, 200)])


def test_a_door_opening_stops_the_path():
    p = site_path(door_rooms(), (250, 200))
    assert p["by_class"][WC.DOOR_OPENING]["edges"] >= 1
    assert abs(p["on_path_length"] - (495 + 400 + 495 + 150 + 150)) < 1e-6        # the 100 doorway is not on it


def test_an_open_passage_stops_the_path_and_a_topology_closure_gives_zero():
    p = box() + wall(lower=((0, 300), (300, 600))) + \
        [H.seg(20, 720, 400, 1000, 400), H.seg(21, 720, 420, 1000, 420), H.seg(91, 720, 400, 720, 420, layer="DIM")]
    r = room(p, [H.text(5, "HALL", 500, 100), H.text(6, "LOBBY", 500, 700)])
    s = next(z for z in r["sites"] if z["labels"])
    edges = WC.site_edges(r["_arr"], s)
    res = WC.path(edges)
    assert res["by_class"].get(WC.TOPOLOGY_CLOSURE, {"length": 0.0})["length"] > 0       # the closure edge exists
    on = [e for e in edges if WC.classify(e) == WC.REAL_WALL_FACE]
    assert not any(any(x.startswith("TCLOSURE|") for x in e["sources"]) for e in on)
    span = [e for e in on if abs(e["length"] - 120.0) < 1e-6]
    assert span == []                                                         # nothing spans the 120 passage


def test_wet_and_service_rooms_with_full_wall_tile_have_no_skirting():
    f = MF.from_record(FACTS["QORTUBA-NEW-NO-SKIRTING-FULL-WALL-TILE-ROOMS-OWNER-001"])
    assert set(f.statement["rooms"]) == {"BATHROOM", "KITCHEN", "IRONING_ROOM", "WASHING_LAUNDRY_ROOM"}
    assert set(f.scope["space_classes"]) == {"WET_SERVICE_ROOM", "SERVICE_ROOM"}
    p = site_path(single_room(), (250, 200), full_wall_tile=True)
    assert p["state"] == WC.NO_SKIRTING and p["on_path_length"] == 0.0
    assert any(r["rule"].startswith("US-02") and r["relation"] == "CORROBORATING" for r in f.relations)


def test_an_isolated_unproven_loop_contributes_no_skirting():
    r = single_room(rect(50, 200, 150, 300, 190))
    s = next(z for z in r["sites"] if z["labels"])
    iso = {x["entity"] for x in r["wall_bands"]["isolated_loops"]}
    p = WC.path(WC.site_edges(r["_arr"], s), isolated_entities=iso)
    assert p["by_class"][WC.UNPROVEN_OBSTACLE]["edges"] == 4 and abs(p["on_path_length"] - 1800.0) < 1e-6


def test_the_skirting_facts_are_explicit_lm_and_do_not_transfer():
    f = MF.from_record(FACTS["QORTUBA-NEW-DRY-ROOM-SKIRTING-ALL-REAL-WALLS-OWNER-001"])
    assert f.unit == "lm" and set(f.statement["not_deducted_for"]) == {"built-in wardrobes", "fixed joinery",
                                                                       "loose furniture"}
    assert {"door openings", "open passages"} <= set(f.statement["stops_at"])
    assert any(r["rule"].startswith("QP-08") and r["relation"] == "MORE_SPECIFIC" for r in f.relations)
    assert MF.bind(f, H.inp([H.seg(1, 0, 0, 10, 0)]))["binding"] == OF.REJECTED_SCOPE
    assert "a published quantity without a frozen, blind-tested policy" in WC.policy_record()["never"]
