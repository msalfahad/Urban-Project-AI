"""R8.11 §5-§16, §22-§23, §30-§34, §39: wall bands from structure, zero-material wall-end closures, open passages."""

from __future__ import annotations

import math
import random

from engine.source import role_authority as RA, room_topology as RT, topology as T
from engine.source import topology_closures as TC, wall_bands as WB
from tests.r8_8 import helpers as H

POL = TC.POLICY_ID


def run(parts, texts=(), **kw):
    return RT.run(H.inp(parts, texts=texts), frame_insert=None, **kw)


def box(w=1000, h=800, h0=1):
    return [H.seg(h0, 0, 0, w, 0), H.seg(h0 + 1, w, 0, w, h), H.seg(h0 + 2, w, h, 0, h), H.seg(h0 + 3, 0, h, 0, 0)]


def stub(cap=None, cap_x=600.0, faces=((0, 600), (0, 600)), layer="DIM", t=(400, 420)):
    """A room with a double-line wall stub from the left wall; its right end is capped on `layer` (cap = shortfall
    at the bottom face), or open (cap = None)."""
    p = box() + [H.seg(10, faces[0][0], t[0], faces[0][1], t[0]), H.seg(11, faces[1][0], t[1], faces[1][1], t[1])]
    if cap is not None:
        p.append(H.seg(12, cap_x, t[0] + cap, cap_x, t[1], layer=layer))
    return p


L2 = [H.text(5, "HALL", 500, 100), H.text(6, "LOBBY", 500, 700)]


def bands(r):
    return [b for b in r["wall_bands"]["bands"] if b["state"] == WB.ESTABLISHED]


def closures(r, release=None):
    return [c for c in r["topology_closures"]["closures"] if release is None or c["release"] == release]


# ------------------------------------------------------------------------------- the band model
def test_a_wall_band_is_established_from_real_paired_faces():
    r = run(stub(), L2, closure_policy=POL)
    (b,) = bands(r)
    assert {b["face_a"], b["face_b"]} == {p.identity.key for p in stub() if p.identity.source_handle in ("10", "11")}
    assert abs(b["width"] - 20) < 1e-9 and [e["kind"] for e in b["ends"]] == [WB.CAPPED, WB.ALIGNED_FREE_END]


def test_parallel_dimension_lines_never_make_a_wall_band():
    p = box() + [H.seg(10, 0, 400, 600, 400, layer="DIM"), H.seg(11, 0, 420, 600, 420, layer="DIM")]
    assert bands(run(p, L2, closure_policy=POL)) == []


def test_a_furniture_rectangle_never_makes_a_wall_band():
    p = box() + H.box(30, 300, 300, 500, 360, layer="FURNITURE")
    assert bands(run(p, L2, closure_policy=POL)) == []


def test_two_glazing_lines_never_make_a_wall_band():
    p = box() + [H.seg(10, 0, 400, 600, 400, layer="GLAZING"), H.seg(11, 0, 420, 600, 420, layer="GLAZING")]
    assert bands(run(p, L2, closure_policy=POL)) == []


def test_corridor_opposite_walls_pair_with_their_own_faces_not_with_each_other():
    walls = [H.seg(10, 0, 300, 1000, 300), H.seg(11, 0, 320, 1000, 320),      # wall 1
             H.seg(12, 0, 440, 1000, 440), H.seg(13, 0, 460, 1000, 460)]      # wall 2 (corridor 320..440)
    r = run(box() + walls, [H.text(5, "A", 500, 100), H.text(6, "B", 500, 700)], closure_policy=POL)
    pairs = {tuple(sorted((b["face_a"].split("|")[1], b["face_b"].split("|")[1]))) for b in bands(r)}
    assert pairs == {("H10", "H11"), ("H12", "H13")}


def test_different_thicknesses_and_nearby_walls_pair_correctly():
    walls = [H.seg(10, 0, 300, 1000, 300), H.seg(11, 0, 315, 1000, 315),      # 15 thick
             H.seg(12, 0, 400, 1000, 400), H.seg(13, 0, 425, 1000, 425)]      # 25 thick, 85 apart
    r = run(box() + walls, [H.text(5, "A", 500, 100), H.text(6, "B", 500, 700)], closure_policy=POL)
    got = sorted((round(b["width"]), tuple(sorted((b["face_a"][-12:], b["face_b"][-12:])))) for b in bands(r))
    assert [w for w, _ in got] == [15, 25]


def test_duplicate_linework_is_not_a_band():
    p = box() + [H.seg(10, 0, 400, 600, 400), H.seg(11, 0, 400, 600, 400)]
    assert bands(run(p, L2, closure_policy=POL)) == []


def test_a_centreline_inside_a_band_makes_it_ambiguous_and_closes_nothing():
    p = stub(0.0) + [H.seg(13, 0, 410, 600, 410)]
    r = run(p, L2, closure_policy=POL)
    assert not closures(r, TC.AUTHORISED_FOR_SHADOW)


def test_a_real_single_line_wall_is_no_band_and_still_a_boundary():
    r0 = run(H.two_rooms(), [H.text(5, "A", 250, 200), H.text(6, "B", 750, 200)])
    r1 = run(H.two_rooms(), [H.text(5, "A", 250, 200), H.text(6, "B", 750, 200)], closure_policy=POL)
    assert bands(r1) == [] and [s["area"] for s in r0["sites"]] == [s["area"] for s in r1["sites"]]
    assert all(s["status"] == T.CERTIFIED for s in r1["sites"])


def test_band_identity_is_source_derived_and_order_independent():
    p = stub(0.0)
    a = run(p, L2, closure_policy=POL)
    q = list(p)
    random.Random(7).shuffle(q)
    b = run(q, L2, closure_policy=POL)
    assert [x["band_id"] for x in bands(a)] == [x["band_id"] for x in bands(b)]
    moved = [x if x.identity.source_handle != "11" else H.seg(11, 0, 421, 600, 421) for x in p]
    assert [x["band_id"] for x in bands(run(moved, L2, closure_policy=POL))] == [x["band_id"] for x in bands(a)]
    renamed = [x if x.identity.source_handle != "11" else H.seg(99, 0, 420, 600, 420) for x in p]
    assert [x["band_id"] for x in bands(run(renamed, L2, closure_policy=POL))] != [x["band_id"] for x in bands(a)]


# ------------------------------------------------------------------------------- caps and closures
def test_an_exact_cap_on_a_dimension_layer_is_proven_and_its_closure_authorised():
    r = run(stub(0.0), L2, closure_policy=POL)
    (c,) = closures(r)
    assert c["corroboration"][0]["grade"] == WB.CAP_PROVEN and c["release"] == TC.AUTHORISED_FOR_SHADOW
    assert RA.ROLE_CONFLICT_SEPARATOR not in [i for s in r["sites"] for i in s["issues"]]


def test_the_9_mm_cap_pattern_is_detected_generically():
    # the cap stands 0.5 mm inside the band end and stops 9.2 mm short (unit 10 mm): a candidate cap
    r = run(stub(0.92, cap_x=600.05), L2, closure_policy=POL)
    (c,) = closures(r)
    assert c["corroboration"][0]["grade"] == WB.CAP_CANDIDATE and c["release"] == TC.AUTHORISED_FOR_SHADOW
    assert tuple(c["geometry"]) == (600, 400, 600, 420)               # the FACE end points, not the cap's
    assert RA.NEAR_MISS_BOUNDARY_GAP not in [i for s in r["sites"] for i in s["issues"]]


def test_an_uncapped_band_end_closure_passes_diagnostics_but_is_never_applied():
    r = run(stub(None), L2, closure_policy=POL)
    (c,) = closures(r)
    assert c["release"] == TC.DIAGNOSTIC_PASS
    assert [round(s["area"]) for s in r["sites"]] == [800000]          # the core still leaks: no authority


def test_closure_preserves_source_coordinates_and_carries_no_material():
    p = stub(0.92, cap_x=600.05)
    i = H.inp(p, texts=L2)
    before = [(x.identity, x.geometry, x.layer) for x in i.parts]
    r = RT.run(i, frame_insert=None, closure_policy=POL)
    assert [(x.identity, x.geometry, x.layer) for x in i.parts] == before
    (c,) = closures(r)
    assert (c["physical_material"], c["affects_wall_quantity"], c["affects_finish_quantity"], c["reversible"]) == \
        ("NONE", False, False, True)


def test_a_closure_cannot_increase_wall_quantity():
    r0 = run(stub(0.0), L2)
    r1 = run(stub(0.0), L2, closure_policy=POL)
    wall = lambda r: sum(s["boundary_role_lengths"].get("TOPOLOGY_BOUNDARY", 0.0) for s in r["sites"] if s["labels"])
    assert wall(r1) <= wall(r0)
    assert all(set(s["boundary_role_lengths"]) <= {"TOPOLOGY_BOUNDARY", TC.ROLE} for s in r1["sites"])


def test_the_safe_closure_removes_only_the_obstacle_interior_leak():
    r0, r1 = run(stub(0.0), L2), run(stub(0.0), L2, closure_policy=POL)
    (room0,) = [s for s in r0["sites"] if s["labels"]]
    (room1,) = [s for s in r1["sites"] if s["labels"]]
    assert sorted(room1["labels"]) == sorted(room0["labels"])
    assert abs(room0["area"] - room1["area"] - 600 * 20) < 1e-6
    (c,) = closures(r1)
    assert [round(p["area"]) for p in c["safety"]["separated_pieces"]] == [12000]


def test_a_closure_that_would_split_two_labelled_rooms_is_never_authorised():
    items = [T.BoundaryItem(p.identity.key, "SEGMENT", p.geometry, "TOPOLOGY_BOUNDARY")
             for p in H.two_rooms(gap=(100, 300))]
    lab = [T.LabelText("A", "EA", "A", 250, 200), T.LabelText("B", "EB", "B", 750, 200)]
    bad = TC.TopologyClosure("TC-X", "REV_A", "R1", "WALL_END_CLOSURE", (500, 100, 500, 300), (), "WB-X",
                             corroboration=[{"grade": WB.CAP_PROVEN, "source": "X"}])
    TC.diagnose(items, [], [bad], lab, [], eps_n=1e-9, eps_r=0.1)
    assert bad.release == TC.UNRESOLVED and not bad.safety["label_partition_unchanged"]


def test_a_49_mm_furniture_to_wall_gap_never_closes():
    p = box() + [H.seg(40, 200, 4.9, 200, 300, layer="FURNITURE"), H.seg(41, 200, 300, 400, 300, layer="FURNITURE")]
    r0, r1 = run(p, L2), run(p, L2, closure_policy=POL)
    assert closures(r1) == [] and [s["area"] for s in r0["sites"]] == [s["area"] for s in r1["sites"]]


def test_the_near_miss_band_is_review_only_it_never_joins():
    p = stub(None) + [H.seg(13, 600, 400, 600, 419.1, layer="DIM")]       # a 0.9 shortfall with NO band end
    r = run([x for x in p if x.identity.source_handle != "11"] + [H.seg(11, 0, 420, 700, 420)], L2,
            closure_policy=POL)                                            # faces no longer aligned
    assert closures(r) == [] and RA.NEAR_MISS_BOUNDARY_GAP in [i for s in r["sites"] for i in s["issues"]]


def test_a_window_jamb_line_beside_glazing_is_not_a_wall_end():
    # the H1316 pattern: a wall-layer jamb line 0.14 short at both ends between window frame lines
    p = box() + [H.seg(20, 300, 0.14, 300, 19.86)] + \
        [H.seg(21 + k, 300, y, 500, y, layer="GLAZING") for k, y in enumerate((0.0, 7.0, 13.0, 20.0))]
    r = run(p, [H.text(5, "A", 500, 400)], closure_policy=POL)
    assert closures(r) == []


# ------------------------------------------------------------------------------- open passages vs thresholds
def test_an_open_passage_is_its_own_site_and_stays_physically_connected():
    r = run(stub(0.0), L2, closure_policy=POL)
    (p,) = r["passages"]
    assert p["kind"] == WB.OPEN_PASSAGE and abs(p["width"] - 400) < 1e-9 and abs(p["wall_thickness"] - 20) < 1e-9
    assert p["physically_connected"] and p["band_id"] == bands(r)[0]["band_id"]
    assert len([s for s in r["sites"] if s["labels"]]) == 1                 # HALL and LOBBY still one space
    assert p["reveals"]["double_count_guard"].startswith("jamb faces and soffit are opening surfaces")


def test_a_door_opening_keeps_its_threshold_and_is_not_an_open_passage():
    walls = [H.seg(1, 0, 0, 1000, 0), H.seg(2, 1000, 0, 1000, 400), H.seg(3, 1000, 400, 0, 400), H.seg(4, 0, 400, 0, 0),
             H.seg(5, 495, 0, 495, 150), H.seg(6, 505, 0, 505, 150), H.seg(7, 495, 150, 505, 150),
             H.seg(8, 495, 250, 495, 400), H.seg(9, 505, 250, 505, 400), H.seg(10, 495, 250, 505, 250)]
    door = [H.part(20, "ARC", (495, 150, 100, 0.0, math.pi / 2), layer="DOOR", path=("70",)),
            H.seg(21, 495, 150, 495, 250, layer="DOOR", path=("70",))]
    r = run(walls + door, [H.text(5, "A", 250, 200), H.text(6, "B", 750, 200)], closure_policy=POL)
    assert r["openings"]["I70"]["state"] == "CLOSED"
    assert r["passages"] == []
    assert r["semantic"]["thresholds"]


def test_network_candidates_on_paired_faces_are_corroborated():
    r = run(stub(0.0), L2, closure_policy=POL)
    faces = {bands(r)[0]["face_a"], bands(r)[0]["face_b"]}
    assert {r["network_review"][f]["state"] for f in faces if f in r["network_review"]} <= \
        {RA.NETWORK_BOUNDARY_ESTABLISHED}


def test_without_the_policy_ts01_is_unchanged():
    r = run(stub(0.0), L2)
    assert "wall_bands" not in r and "topology_closures" not in r
