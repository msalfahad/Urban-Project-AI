"""R8.11 post-freeze amendment A1 (WALL_BAND_POLICY_V2): a band that runs into another wall's face line is a
RECEIVING_FACE_JUNCTION - never a free end, a closure candidate or an open-passage jamb. Found on the first real run
(false 150-200 mm "passages" through the receiving wall's core); it can only REMOVE candidates."""

from __future__ import annotations

from engine.source import room_topology as RT, topology_closures as TC, wall_bands as WB
from tests.r8_8 import helpers as H

POL = TC.POLICY_ID
LAB = [H.text(5, "A", 300, 100), H.text(6, "B", 300, 700), H.text(7, "C", 800, 400)]


def box(w=1000, h=800):
    return [H.seg(1, 0, 0, w, 0), H.seg(2, w, 0, w, h), H.seg(3, w, h, 0, h), H.seg(4, 0, h, 0, 0)]


def run(parts):
    return RT.run(H.inp(parts, texts=LAB), frame_insert=None, closure_policy=POL)


def band_ends(r, handles):
    for b in r["wall_bands"]["bands"]:
        if {b["face_a"].split("|")[1], b["face_b"].split("|")[1]} == handles:
            return [e["kind"] for e in b["ends"]]
    raise AssertionError(f"no band {handles}")


def test_a_t_junction_into_a_through_wall_face_is_not_a_wall_end():
    p = box() + [H.seg(10, 0, 400, 600, 400), H.seg(11, 0, 420, 600, 420),          # the band
                 H.seg(20, 600, 0, 600, 800), H.seg(21, 620, 0, 620, 800)]          # the receiving wall
    r = run(p)
    assert band_ends(r, {"H10", "H11"})[1] == WB.RECEIVING_FACE_JUNCTION
    assert r["passages"] == []                      # no strip through the receiving wall's core
    assert not [c for c in r["topology_closures"]["closures"] if "H10" in str(c["source_evidence_ids"])]


def test_merged_wall_cores_are_a_junction_not_a_free_end():
    p = box() + [H.seg(10, 0, 400, 600, 400), H.seg(11, 0, 420, 600, 420),
                 H.seg(20, 600, 0, 600, 400), H.seg(22, 600, 420, 600, 800),          # receiving face interrupted
                 H.seg(21, 620, 0, 620, 800)]
    r = run(p)
    assert band_ends(r, {"H10", "H11"})[1] == WB.RECEIVING_FACE_JUNCTION
    assert r["topology_closures"]["closures"] == [] and r["passages"] == []


def test_a_genuine_free_end_facing_a_room_is_still_a_free_end():
    p = box() + [H.seg(10, 0, 400, 600, 400), H.seg(11, 0, 420, 600, 420)]
    r = run(p)
    assert band_ends(r, {"H10", "H11"})[1] == WB.ALIGNED_FREE_END


def test_a_one_sided_flush_line_is_not_a_receiving_face():
    """Only a line continuing beyond BOTH end points receives the band: one flush line (an L) proves nothing."""
    p = box() + [H.seg(10, 0, 400, 600, 400), H.seg(11, 0, 420, 600, 420), H.seg(20, 600, 420, 600, 800)]
    r = run(p)
    assert band_ends(r, {"H10", "H11"})[1] != WB.RECEIVING_FACE_JUNCTION


def test_the_amendment_is_versioned():
    rec = WB.policy_record()          # R8.12: V3 supersedes V2 and keeps A1 (RECEIVING_FACE_JUNCTION)
    assert WB.POLICY_ID == "WALL_BAND_POLICY_V4" and WB.RECEIVING_FACE_JUNCTION in rec["ends"]   # R8.13: V4 keeps A1
    assert any(h.startswith("V2 (R8.11 amendment A1)") for h in rec["history"])
