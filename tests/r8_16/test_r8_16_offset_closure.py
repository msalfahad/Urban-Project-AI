"""R8.16 §15-§17: DOOR_OPENING_CLOSURE_POLICY_V2 - closure B for a door whose jamb caps are offset (two walls of
different thickness flush on one side). Frozen before any Qortuba run."""

from __future__ import annotations

import math
import random

from engine.source import room_topology as RT, topology as T, topology_closures as TC
from tests.r8_8 import helpers as H


def door_parts(hinge=(495.0, 150.0), leaf_x=None):
    hx, hy = hinge
    lx = hx if leaf_x is None else leaf_x
    return [H.part(20, "ARC", (hx, hy, 100, 0.0, math.pi / 2), layer="DOOR", path=("70",)),
            H.seg(21, lx, hy, lx, hy + 100, layer="DOOR", path=("70",))]


def walls(upper_left=495.0, lower_left=495.0, extra=()):
    return [H.seg(1, 0, 0, 1000, 0), H.seg(2, 1000, 0, 1000, 400), H.seg(3, 1000, 400, 0, 400), H.seg(4, 0, 400, 0, 0),
            H.seg(5, lower_left, 0, lower_left, 150), H.seg(6, 505, 0, 505, 150), H.seg(7, lower_left, 150, 505, 150),
            H.seg(8, upper_left, 250, upper_left, 400), H.seg(9, 505, 250, 505, 400),
            H.seg(10, upper_left, 250, 505, 250)] + list(extra)


def run(parts, texts=(("A", 250, 200), ("B", 750, 200)), shuffle=None):
    if shuffle is not None:
        parts = list(parts)
        random.Random(shuffle).shuffle(parts)
    tx = [H.text(50 + i, v, x, y) for i, (v, x, y) in enumerate(texts)]
    return RT.run(H.inp(parts, texts=tx), frame_insert=None, closure_policy=TC.POLICY_ID)


def opening(r):
    (occ, st), = [(k, v) for k, v in r["openings"].items()]
    return occ, st


def strip(r):
    return [t for t in r["semantic"]["thresholds"]]


def test_a_normal_aligned_door_keeps_the_v1_end_point_closure():
    r = run(walls() + door_parts())
    _, st = opening(r)
    assert st["closure_b"] and st["closure_b_rule"] == T.B_END_POINT
    assert len(strip(r)) == 1 and abs(strip(r)[0]["area"] - 100 * 10) < 1e-6


def test_an_offset_jamb_door_gets_its_closure_b_and_its_own_strip_site():
    r = run(walls(upper_left=490.0) + door_parts())
    _, st = opening(r)
    assert st["closure_b"] and st["closure_b_rule"] == T.B_OFFSET_JAMB
    ev = st["closure_b_evidence"]
    assert abs(ev["depth"] - 10) < 1e-9 and abs(ev["stagger"] - 5) < 1e-9
    (t,) = strip(r)
    assert abs(t["area"] - 100 * 10) < 1e-6 and len(t["sides"]) == 2


def test_the_same_offset_geometry_without_a_door_forms_no_closure():
    r = run(walls(upper_left=490.0))
    assert r["openings"] == {} and strip(r) == []
    assert not [c for c in r["closures"] if c.source_id.startswith("CLOSURE|")]


def test_a_leaf_inside_the_reveal_gets_no_closure_b():
    r = run(walls() + door_parts(hinge=(500.0, 150.0)))                 # leaf in the middle of the reveal
    _, st = opening(r)
    assert st["closure_b"] is None and st["closure_b_blocked"] == T.B_LEAF_INSIDE


def test_two_competing_far_faces_block_closure_b():
    p = [H.seg(1, 0, 0, 1000, 0), H.seg(2, 1000, 0, 1000, 400), H.seg(3, 1000, 400, 0, 400), H.seg(4, 0, 400, 0, 0),
         H.seg(5, 495, 0, 495, 150), H.seg(6, 505, 0, 505, 150), H.seg(7, 495, 150, 505, 150),
         H.seg(8, 490, 250, 490, 400), H.seg(9, 515, 250, 515, 400), H.seg(10, 490, 250, 515, 250)]
    r = run(p + door_parts())                                             # caps reach 505 and 515: no single B
    _, st = opening(r)
    assert st["closure_b"] is None and st["closure_b_blocked"] in (T.B_NOT_PARALLEL, T.B_AMBIGUOUS)


def test_a_stagger_deeper_than_the_strip_blocks_closure_b():
    r = run(walls(upper_left=480.0) + door_parts())
    _, st = opening(r)
    assert st["closure_b"] is None and st["closure_b_blocked"] == T.B_STAGGER_TOO_DEEP


def test_an_intervening_boundary_inside_the_strip_blocks_closure_b():
    r = run(walls(upper_left=490.0, extra=[H.seg(30, 500, 150, 500, 250)]) + door_parts())
    _, st = opening(r)
    assert st["closure_b"] is None and st["closure_b_blocked"] == T.B_INTERVENING


def test_a_door_next_to_a_t_junction_still_closes():
    tj = [H.seg(31, 505, 300, 1000, 300), H.seg(32, 505, 310, 1000, 310)]
    r = run(walls(extra=tj) + door_parts(), texts=(("A", 250, 200), ("B", 750, 200), ("C", 750, 360)))
    _, st = opening(r)
    assert st["closure_b"] and len(strip(r)) == 1


def test_a_door_next_to_a_column_still_closes():
    col = [H.part(40 + i, "SEGMENT", g, layer="COL", idx=i) for i, g in enumerate(
        [(505, 260, 525, 260), (525, 260, 525, 280), (525, 280, 505, 280), (505, 280, 505, 260)])]
    r = run(walls(upper_left=490.0) + door_parts() + col)
    _, st = opening(r)
    assert st["closure_b"] and st["closure_b_rule"] == T.B_OFFSET_JAMB


def test_a_door_next_to_an_open_passage_still_closes():
    part = [H.seg(1, 0, 0, 1000, 0), H.seg(2, 1000, 0, 1000, 400), H.seg(3, 1000, 400, 0, 400),
            H.seg(4, 0, 400, 0, 0), H.seg(5, 495, 0, 495, 150), H.seg(6, 505, 0, 505, 150), H.seg(7, 495, 150, 505, 150),
            H.seg(8, 490, 250, 490, 300), H.seg(9, 505, 250, 505, 300), H.seg(10, 490, 250, 505, 250),
            H.seg(11, 490, 300, 505, 300)]                               # a 100-unit gap up to the outer wall
    r = run(part + door_parts())
    _, st = opening(r)
    assert st["closure_b"] and st["closure_b_rule"] == T.B_OFFSET_JAMB


def test_wet_and_dry_door_fixtures_both_get_a_strip_with_two_sides():
    for labels in ((("BATH", 250, 200), ("BED", 750, 200)), (("BED", 250, 200), ("HALL", 750, 200))):
        r = run(walls(upper_left=490.0) + door_parts(), texts=labels)
        (t,) = strip(r)
        assert len(t["sides"]) == 2


def test_shuffled_input_gives_the_same_closures_and_sites():
    base = run(walls(upper_left=490.0) + door_parts())
    for seed in (3, 11):
        r = run(walls(upper_left=490.0) + door_parts(), shuffle=seed)
        assert sorted((c.source_id, tuple(round(v, 9) for v in c.geometry)) for c in r["closures"]) == \
            sorted((c.source_id, tuple(round(v, 9) for v in c.geometry)) for c in base["closures"])
        assert sorted(round(s["area"], 6) for s in r["sites"]) == sorted(round(s["area"], 6) for s in base["sites"])


def test_the_policy_is_versioned_and_in_the_run_manifest():
    rec = T.door_closure_policy_record()
    assert rec["policy_id"] == "DOOR_OPENING_CLOSURE_POLICY_V2" and len(rec["digest"]) == 64
    r = run(walls() + door_parts())
    assert r["run_manifest"]["policies"]["door_opening_closure"] == [T.DOOR_CLOSURE_POLICY_ID, rec["digest"]]
    v1 = T.opening_closures({}, [], 0.1, policy="DOOR_OPENING_CLOSURE_POLICY_V1")
    assert v1 == ([], {})
