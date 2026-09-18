"""E1.3 corrected — the boundary walk, on drawings whose answer is known.

Three earlier constructions for an unenclosed region each failed in a
different way, and each failure was found by looking at a real drawing
after the fact. These cases carry their own answers, so the mechanism is
held to them before it is offered a real floor again.

Every case is built here. None of them is P7757, none of them carries a
benchmark quantity, and none of them was drawn to make a particular
number come out.
"""

import math

import pytest

from engine import boundary_walk as bw


def _seg(a, b, oid, role="MATERIAL_WALL_FACE"):
    return {"points": [a, b], "object_id": oid, "boundary_role": role,
            "layer": "1"}


def _box(x0, y0, x1, y1, tag):
    return [_seg((x0, y0), (x1, y0), tag + "-S"),
            _seg((x1, y0), (x1, y1), tag + "-E"),
            _seg((x1, y1), (x0, y1), tag + "-N"),
            _seg((x0, y1), (x0, y0), tag + "-W")]


def _run(segments, seed, *, gaps=(), families=(), rays=360):
    pieces = bw.pieces_from(segments, tol_mm=1.0)
    fams = list(families) or bw.thickness_families(
        [200.0, 200.0, 150.0, 150.0])
    mates, _pairs = bw.mate_map(pieces, families=fams)
    gaps_at = {}
    for g in gaps:
        for p in (g["start_mm"], g["end_mm"]):
            gaps_at.setdefault(bw._nkey(tuple(p)), g)
    out = bw.boundary_at(seed, pieces, gaps_at=gaps_at, mates=mates,
                         rays=rays)
    out["_pieces"] = pieces
    return out


def _material_mm(res):
    """Drawn material on the boundary, counted once however often walked."""
    pieces = res["_pieces"]
    walked = {s["piece"] for s in res["steps"]
              if s["STEP"] == bw.STEP_MATERIAL_FACE}
    m = sum(pieces[i]["length_mm"] for i in walked)
    m += sum(s["length_mm"] for s in res["steps"]
             if s["STEP"] == bw.STEP_WALL_END_RETURN)
    return m


def _gap(gid, a, b, cls="CONFIRMED_DOOR_PORTAL"):
    return {"GAP_ID": gid, "GAP_CLASS": cls, "start_mm": list(a),
            "end_mm": list(b), "notes": []}


# A - a room the drawing closes
def test_a_a_closed_room_is_walked_and_its_perimeter_is_the_drawings():
    res = _run(_box(0, 0, 4000, 3000, "R"), (2000, 1500))
    assert res["BOUNDARY_BASIS"] == bw.ENCLOSED
    assert res["RING_ENCLOSES_THE_POINT"] is True
    assert _material_mm(res) == pytest.approx(14000.0, abs=1.0)


# B - paired faces: the walk is on the faces that bound THIS room
def test_b_the_walk_is_on_the_room_side_face_of_every_paired_wall():
    segs = _box(0, 0, 4000, 3000, "IN") + _box(-200, -200, 4200, 3200, "OUT")
    res = _run(segs, (2000, 1500))
    assert res["BOUNDARY_BASIS"] == bw.ENCLOSED
    assert _material_mm(res) == pytest.approx(14000.0, abs=1.0)
    paired = [f for f in res["FACE_SELECTION"] if f["PAIRING"] == bw.PAIRED]
    assert paired, "the two faces of each wall must be paired"
    assert all(f["THE_WALK_IS_ON_THE_ROOM_SIDE_FACE"] for f in paired)
    assert {f["thickness_mm"] for f in paired} == {200.0}


# C - the same wall bounds a different space from its other face
def test_c_a_point_on_the_other_side_selects_the_other_face():
    faces = [{"a": (0, 0), "b": (4000, 0), "object_id": "A"},
             {"a": (0, 200), "b": (4000, 200), "object_id": "B"}]
    fams = bw.thickness_families([200.0, 200.0])
    pair = bw.pair_faces(faces, families=fams)[0]
    below, _ = bw.room_side_face(pair, faces, (2000, -1000))
    above, _ = bw.room_side_face(pair, faces, (2000, 1200))
    assert below == 0 and above == 1


# D - a pier standing inside the room is a hole, not the boundary
def test_d_an_island_inside_the_room_does_not_become_the_boundary():
    segs = _box(0, 0, 4000, 3000, "R") + _box(1800, 1300, 2000, 1500, "PIER")
    res = _run(segs, (600, 600))
    assert res["BOUNDARY_BASIS"] == bw.ENCLOSED
    assert _material_mm(res) == pytest.approx(14000.0, abs=1.0)
    assert res["islands_standing_in_the_region"]


# E - an opening the drawing carries evidence for is crossed
def test_e_a_classified_portal_carries_the_boundary_across_the_opening():
    segs = [_seg((0, 0), (1500, 0), "S1"), _seg((2500, 0), (4000, 0), "S2"),
            _seg((4000, 0), (4000, 3000), "E"),
            _seg((4000, 3000), (0, 3000), "N"),
            _seg((0, 3000), (0, 0), "W")]
    res = _run(segs, (2000, 1500),
               gaps=[_gap("GAP-T", (1500, 0), (2500, 0))])
    assert res["BOUNDARY_BASIS"] == bw.ENCLOSED
    assert any(s["STEP"] == bw.STEP_ACROSS_A_GAP for s in res["steps"])
    # the opening itself contributes no wall length
    assert _material_mm(res) == pytest.approx(13000.0, abs=1.0)


# F - the same opening with no evidence is not crossed
def test_f_an_unclassified_gap_is_not_bridged_and_nothing_is_proposed():
    segs = [_seg((0, 0), (1500, 0), "S1"), _seg((2500, 0), (4000, 0), "S2"),
            _seg((4000, 0), (4000, 3000), "E"),
            _seg((4000, 3000), (0, 3000), "N"),
            _seg((0, 3000), (0, 0), "W")]
    res = _run(segs, (2000, 1500))
    assert res["BOUNDARY_BASIS"] == bw.NOT_ESTABLISHED
    assert res["RING_ENCLOSES_THE_POINT"] is False
    assert any(s["STEP"] == bw.STEP_STOPS for s in res["steps"])
    assert "THIS_IS_NOT_A_PROPOSED_BOUNDARY" in res


# G - a partition meeting a wall part way along it
def test_g_a_t_junction_is_turned_correctly():
    segs = _box(0, 0, 4000, 3000, "R") + [_seg((2000, 0), (2000, 1200), "T")]
    res = _run(segs, (800, 1500))
    assert res["BOUNDARY_BASIS"] == bw.ENCLOSED
    walked = {res["_pieces"][s["piece"]]["object_id"]
              for s in res["steps"] if s["STEP"] == bw.STEP_MATERIAL_FACE}
    assert "T" in walked, "the walk must go up and back down the partition"


# H - a pier that interrupts a wall face
def test_h_a_pier_in_the_wall_face_is_walked_through():
    segs = _box(0, 0, 4000, 3000, "R") + _box(1000, 0, 1200, 200, "COL")
    res = _run(segs, (2000, 1500))
    assert res["BOUNDARY_BASIS"] == bw.ENCLOSED
    assert _material_mm(res) > 14000.0


# I - a side with nothing built along it
def test_i_an_open_side_is_never_closed_and_the_stretch_is_kept():
    segs = [_seg((0, 0), (4000, 0), "S"),
            _seg((4000, 0), (4000, 3000), "E"),
            _seg((4000, 3000), (0, 3000), "N")]
    res = _run(segs, (2000, 1500))
    assert res["BOUNDARY_BASIS"] == bw.NOT_ESTABLISHED
    # each of the three walls is drawn as one line with no thickness
    # established, so the walk runs up one side and back down the other
    # and comes back to where it started. That ring has no area and does
    # not enclose the point, which is how the open side is refused.
    assert res["rings_that_close_but_not_around_the_point"] >= 1
    assert _material_mm(res) == pytest.approx(11000.0, abs=1.0)
    assert "THIS_IS_NOT_A_PROPOSED_BOUNDARY" in res


# J - a curved boundary keeps its length
def test_j_a_curved_boundary_is_walked_at_its_own_length():
    arc = [(2000 + 2000 * math.cos(math.radians(a)),
            3000 + 2000 * math.sin(math.radians(a)))
           for a in range(0, 181, 2)]
    segs = [_seg((0, 3000), (0, 0), "W"), _seg((0, 0), (4000, 0), "S"),
            _seg((4000, 0), (4000, 3000), "E"),
            {"points": arc, "object_id": "ARC",
             "boundary_role": "MATERIAL_WALL_FACE", "layer": "1"}]
    res = _run(segs, (2000, 1500))
    assert res["BOUNDARY_BASIS"] == bw.ENCLOSED
    # the straight sides are 10 m; a half circle of radius 2 m is 6.283 m
    assert _material_mm(res) == pytest.approx(16283.0, rel=0.01)


# K - material inside the room that nothing connects to the boundary
def test_k_a_disconnected_fragment_is_reported_and_not_joined():
    segs = _box(0, 0, 4000, 3000, "R") + [_seg((1500, 1500), (2500, 1500),
                                               "STUB")]
    res = _run(segs, (800, 600))
    assert res["BOUNDARY_BASIS"] == bw.ENCLOSED
    walked = {res["_pieces"][s["piece"]]["object_id"]
              for s in res["steps"] if s["STEP"] == bw.STEP_MATERIAL_FACE}
    assert "STUB" not in walked


# L - a ring that closes around something else is not this point's boundary
def test_l_a_ring_that_does_not_enclose_the_point_is_refused():
    segs = _box(0, 0, 200, 200, "TINY")
    res = _run(segs, (3000, 3000))
    assert res["BOUNDARY_BASIS"] == bw.NOT_ESTABLISHED
    assert res["rings_that_close_but_not_around_the_point"] >= 1


# M - the end of a wall body, crossed at the thickness the pairing gives
def test_m_a_wall_end_is_returned_across_its_own_thickness():
    segs = _box(0, 0, 4000, 3000, "R") + [
        _seg((2000, 0), (2000, 1200), "PA"),
        _seg((2200, 0), (2200, 1200), "PB")]
    res = _run(segs, (800, 1500))
    assert res["BOUNDARY_BASIS"] == bw.ENCLOSED
    rets = [s for s in res["steps"] if s["STEP"] == bw.STEP_WALL_END_RETURN]
    assert rets, "the walk must turn across the end of the partition"
    assert rets[0]["length_mm"] == pytest.approx(200.0, abs=1.0)
    assert rets[0]["matched_family_mm"] == pytest.approx(200.0, abs=1.0)


# N - nothing drawn at all
def test_n_with_no_material_nothing_at_all_is_proposed():
    res = _run([], (0, 0))
    assert res["BOUNDARY_BASIS"] == bw.NOT_ESTABLISHED
    assert res["steps"] == []
    assert res["faces_the_point_can_see"] == 0


# O - a separation that matches no thickness the drawing uses is not a wall
def test_o_two_parallel_lines_at_no_known_thickness_are_not_a_wall_body():
    faces = [{"a": (0, 0), "b": (4000, 0), "object_id": "A"},
             {"a": (0, 733), "b": (4000, 733), "object_id": "B"}]
    fams = bw.thickness_families([200.0, 150.0])
    assert bw.pair_faces(faces, families=fams) == []


# P - the mechanism knows nothing about any particular room
def test_p_the_mechanism_names_no_region_and_no_project():
    """No code in the mechanism may branch on a region or a project.

    The module's opening docstring recounts which room the superseded
    constructions were wrong about, which is history and belongs there.
    Everything below it is the mechanism, and that is what is checked.
    """
    import ast
    import pathlib
    src = pathlib.Path("engine/boundary_walk.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    code = ast.unparse(ast.Module(
        body=[n for n in tree.body
              if not (isinstance(n, ast.Expr)
                      and isinstance(n.value, ast.Constant)
                      and isinstance(n.value.value, str))],
        type_ignores=[]))
    for word in ("PANTRY", "KITCHEN", "DRIVER", "WASH", "SALOON", "DINING",
                 "DEWANEYA", "P7757", "LG-0", "E1_3-LG"):
        assert word not in code, (
            f"the mechanism must be general: its code mentions {word}")


# Q - a proposal is never offered without the point inside it
def test_q_enclosed_is_never_reported_without_the_point_inside():
    for segs, seed in (
            (_box(0, 0, 4000, 3000, "R"), (2000, 1500)),
            (_box(0, 0, 200, 200, "TINY"), (3000, 3000)),
            (_box(0, 0, 4000, 3000, "R") + _box(1800, 1300, 2000, 1500, "P"),
             (600, 600)),
            ([], (0, 0)),
    ):
        res = _run(segs, seed)
        if res["BOUNDARY_BASIS"] == bw.ENCLOSED:
            assert res["RING_ENCLOSES_THE_POINT"] is True
            assert res.get("ring_area_mm2", 0.0) > 0.0
        else:
            assert res["RING_ENCLOSES_THE_POINT"] is False
            assert "THIS_IS_NOT_A_PROPOSED_BOUNDARY" in res


# R - a withheld result carries no area and says so
def test_r_a_withheld_result_carries_no_area():
    segs = [_seg((0, 0), (4000, 0), "S"),
            _seg((4000, 0), (4000, 3000), "E")]
    res = _run(segs, (2000, 1500))
    assert res["BOUNDARY_BASIS"] == bw.NOT_ESTABLISHED
    assert "ring_area_mm2" not in res
    assert res["why"] == bw.WHY_NOTHING_IS_PROPOSED
