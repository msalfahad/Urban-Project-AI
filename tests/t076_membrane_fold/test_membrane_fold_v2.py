"""T-076 membrane fold V2: every expected value below is written by hand from the room sizes and the owner's method
(Q-30 kitchen worked example: roll 1.00 x 10.00 m UP-WP-001, lap 0.10 m UP-WP-002, upturn 0.20 m UP-WP-003 folded
from the same strip; Q-35 C: strips 0.20 m longer at both ends whatever sits in the wall, the BOQ upturn line on the
walls only plus one doorway transition line per door; Q-37 A: an open side is a threshold line). Synthetic rooms only:
no client project. The hand arithmetic is in each docstring."""

from __future__ import annotations

import math

import pytest

from engine.source import membrane_fold_v2 as F

A = pytest.approx


def rect(x, y, x0=0.0, y0=0.0):
    return [(x0, y0), (x0 + x, y0), (x0 + x, y0 + y), (x0, y0 + y)]


def turn(ring, deg, about=(0.0, 0.0)):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return [(about[0] + (p[0] - about[0]) * c - (p[1] - about[1]) * s,
             about[1] + (p[0] - about[0]) * s + (p[1] - about[1]) * c) for p in ring]


def d(f, which):
    return {o["direction"]: o for o in f["directions"]}[which]


def widths_lengths(o):
    return [(s["width_m"], s["length_m"]) for s in o["strip_list"]]


# ------------------------------------------------------------------------------------------------ owner's kitchen
def test_owner_kitchen_q30_every_number():
    """3.00 x 4.00 m. Along the 4 m wall: span 3.00, strips cover 0.80 + 0.90 + 0.90 + 0.40 = 3.00 m of floor, the
    4th strip 0.40 + 0.10 + 0.20 = 0.70 m wide; each 4.00 + 0.20 + 0.20 = 4.40 m; cut 3 x 4.40 + 0.70 x 4.40 = 16.28;
    4 cuts of 4.40 m: two per 10 m roll = 2 rolls; by cut area ceil(1.628) = 2; offcut 20 - 16.28 = 3.72. Floor 12.00,
    perimeter 14.00, floor + upturn 12.00 + 2.80 = 14.80. Across: span 4.00 + 0.40 = 4.40 developed, n = ceil(3.40 /
    0.90) + 1 = 5, last 4.40 - 4 x 0.90 = 0.80; 5 x 3.40 m = 17.00 m of roll: 3 rolls by length (3.40 x 2 per roll),
    2 by cut area (16.32 m2): the bases differ and the direction changes the rolls - both flagged, neither picked."""
    f = F.fold(rect(4.0, 3.0))
    assert f["shape"] == "RECTANGLE" and f["selected"] is None
    assert f["floor_m2"] == A(12.0) and f["boundary_lm"] == A(14.0) and f["surface_full_boundary_m2"] == A(14.8)
    a = d(f, F.ALONG_LONG)
    assert widths_lengths(a) == [(1.0, 4.4), (1.0, 4.4), (1.0, 4.4), (0.7, 4.4)]
    assert [s["floor_to_m"] - s["floor_from_m"] for s in a["strip_list"]] == A([0.8, 0.9, 0.9, 0.4])
    assert a["cut_m2"] == A(16.28) and a["rolls_if_alone"] == 2 and a["rolls_by_cut_area"] == 2
    assert a["gross_offcut_if_alone_m2"] == A(3.72) and a["upturn_shortfall_m2"] == 0.0
    b = d(f, F.ACROSS)
    assert widths_lengths(b) == [(1.0, 3.4)] * 4 + [(0.8, 3.4)]
    assert b["cut_m2"] == A(16.32) and b["roll_length_used_m"] == A(17.0)
    assert b["rolls_if_alone"] == 3 and b["rolls_by_cut_area"] == 2 and b["roll_count_bases_differ"]
    assert {"DIRECTION_CHANGES_ROLLS", "ROLL_COUNT_BASES_DIFFER"} <= set(f["flags"])


def test_kitchen_boq_lines_q35_c():
    """one 0.90 m door: walls-only upturn 14.00 - 0.90 = 13.10 lm = 2.62 m2; one doorway transition (pcs); no
    threshold. The membrane to buy (16.28 m2) does not change with the door (Q-35 C)."""
    r = F.area(floor="GF", room_id="K1", polygon=rect(4.0, 3.0),
               roles_lm={"wall": 13.10, "door": 0.90}, doors=[{"opening_id": "D1", "width_m": 0.90}])
    up = r["lines"]["upturn"]
    assert up["lm"] == A(13.10) and up["m2"] == A(2.62)
    assert [(t["opening_id"], t["qty"]) for t in r["lines"]["door_transitions"]] == [("D1", 1)]
    assert r["lines"]["thresholds"] == []
    assert d(r["fold"], F.ALONG_LONG)["cut_m2"] == A(16.28)


def test_owner_bathroom_3x3_picture():
    """3 x 3 with his Q-30 method: 4 strips (1.0, 1.0, 1.0, 0.7) x 3.40 m = 12.58 m2; 13.60 m of roll: 2 rolls
    (the picture's 3 strips x 3.20 m / 1 roll leaves out the upturn and the laps)."""
    f = F.fold(rect(3.0, 3.0))
    for o in f["directions"]:
        assert widths_lengths(o) == [(1.0, 3.4), (1.0, 3.4), (1.0, 3.4), (0.7, 3.4)]
        assert o["cut_m2"] == A(12.58) and o["rolls_if_alone"] == 2 and o["rolls_by_cut_area"] == 2


# ------------------------------------------------------------------------------------------------ adversarial input
@pytest.mark.parametrize("ring,unit", [
    (turn(rect(4.0, 3.0), 37.0, (5.0, 2.0)), 1.0),                       # rotated 37 deg
    (turn(rect(4.0, 3.0), 45.0), 1.0),                                   # rotated 45 deg (two Alsenan rooms)
    (turn(rect(4.0, 3.0), 90.0), 1.0),                                   # longest wall drawn vertical
    ([(-p[0], p[1]) for p in rect(4.0, 3.0)], 1.0),                      # mirrored
    (rect(4000.0, 3000.0), 0.001),                                       # millimetres
    ([(0, 0), (1.3, 0), (2.5, 0), (4, 0), (4, 1.2), (4, 3), (4, 3), (2, 3), (0, 3), (0, 1.0), (0, 0)], 1.0),
])                                                                       # collinear, repeated and closing points
def test_same_room_any_frame_any_units(ring, unit):
    f = F.fold(ring, unit_m=unit)
    assert f["shape"] == "RECTANGLE" and f["points_used"] == 4
    assert f["floor_m2"] == A(12.0) and f["boundary_lm"] == A(14.0)
    assert d(f, F.ALONG_LONG)["cut_m2"] == A(16.28) and d(f, F.ALONG_LONG)["rolls_if_alone"] == 2
    assert d(f, F.ACROSS)["cut_m2"] == A(16.32) and d(f, F.ACROSS)["rolls_if_alone"] == 3


def test_collinear_points_reported():
    f = F.fold([(0, 0), (2, 0), (4, 0), (4, 3), (0, 3)])
    assert f["collinear_or_repeated_removed"] == 1 and "COLLINEAR_POINTS_REMOVED" in f["flags"]


def test_l_shaped_bathroom():
    """3 x 3 less a 1.5 x 1.5 corner: floor 6.75, boundary 12.00. Strips along x (span 3.00): floor bands 0-0.8,
    0.8-1.7, 1.7-2.6, 2.6-3.0; the floor in the first two reaches x = 3.00 (strips 3.40 m), in the last two x = 1.50
    (strips 1.90 m); cut 3.4 + 3.4 + 1.9 + 0.7 x 1.9 = 10.03 m2 (the full 3 x 3 square: 12.58). The inner wall at
    y = 1.50 lies inside band 2, whose sheet reaches y = 1.70: its 0.20 m upturn is covered; no shortfall. One
    internal corner: its corner piece is by detail. Roll length 3.4 + 3.4 + 1.9 + 1.9 = 10.6 m: 2 rolls."""
    f = F.fold([(0, 0), (3, 0), (3, 1.5), (1.5, 1.5), (1.5, 3), (0, 3)])
    assert f["shape"] == "ORTHOGONAL" and f["floor_m2"] == A(6.75) and f["boundary_lm"] == A(12.0)
    for o in f["directions"]:                       # the L is symmetric about its diagonal
        assert widths_lengths(o) == [(1.0, 3.4), (1.0, 3.4), (1.0, 1.9), (0.7, 1.9)]
        assert o["cut_m2"] == A(10.03) and o["upturn_shortfall_m2"] == 0.0 and o["rolls_if_alone"] == 2
    assert f["internal_corners"] == 1 and "INTERNAL_CORNER_PIECES_BY_DETAIL" in f["flags"]


def test_u_shape_splits_a_band_into_two_strips():
    """4 x 3 with a 2.0 wide, 2.0 deep notch from the top middle (prongs 1.0 wide). Along x (span 3): bands 0-0.8
    and 0.8-1.7 hold floor over x 0-4 (one strip of 4.40 each); bands 1.7-2.6 and 2.6-3.0 hold two prongs 2.00 m apart
    (more than the 0.40 m of two strip ends): two strips of 1.0 + 0.40 = 1.40 m each. Cut 4.4 + 4.4 + 2 x 1.4 +
    0.7 x 2 x 1.4 = 13.56 m2 (one strip over the whole band, as T-074 laid it: 16.28). Roll length 14.40 m: 2 rolls.
    From the other wall (notch side first): bands 0-0.8 and 0.8-1.7 are prongs only (2 x 1.40 each), 1.7-2.6 and
    2.6-3.0 full (4.40): 4 x 1.40 + 4.40 + 0.70 x 4.40 = 13.08 m2 - shown beside it, not selected.
    Across (span 4, 5 strips, last 0.80): x bands 0-0.8 and 0.8-1.7 reach y = 3 (3.40), 1.7-2.6 only the notch floor
    y 0-1 (1.40), 2.6-3.5 and 3.5-4.0 y = 3 (3.40): 3.4 + 3.4 + 1.4 + 3.4 + 0.8 x 3.4 = 14.32 m2."""
    U = [(0, 0), (4, 0), (4, 3), (3, 3), (3, 1), (1, 1), (1, 3), (0, 3)]
    f = F.fold(U)
    assert f["floor_m2"] == A(8.0)
    a = d(f, F.ALONG_LONG)
    assert widths_lengths(a) == [(1.0, 4.4), (1.0, 4.4), (1.0, 1.4), (1.0, 1.4), (0.7, 1.4), (0.7, 1.4)]
    assert a["cut_m2"] == A(13.56) and a["rolls_if_alone"] == 2 and a["upturn_shortfall_m2"] == 0.0
    assert a["other_start"]["cut_m2"] == A(13.08) and a["start_changes_cut_m2"] == A(-0.48)
    b = d(f, F.ACROSS)
    assert sorted(widths_lengths(b)) == sorted([(1.0, 3.4), (1.0, 3.4), (1.0, 1.4), (1.0, 3.4), (0.8, 3.4)])
    assert b["cut_m2"] == A(14.32) and b["upturn_shortfall_m2"] == 0.0
    assert f["internal_corners"] == 2


def test_slanted_wall_shortfall_is_reported_not_zeroed():
    """trapezoid 3.00 at the base, 2.00 at the top, 2.00 high (one slanted wall): floor (3 + 2) / 2 x 2 = 5.00. A
    straight strip end 0.20 m past the slanted wall reaches it only 0.20 x cos(angle) deep: the uncovered part of
    its upturn is reported in m2 (> 0), and the room's second wall frame is shown."""
    f = F.fold([(0, 0), (3, 0), (3, 2), (1, 2)])
    assert f["shape"] == "NON_ORTHOGONAL" and f["floor_m2"] == A(5.0)
    assert "UPTURN_SHORTFALL" in f["flags"] and "SEVERAL_WALL_FRAMES" in f["flags"]
    assert any(o["upturn_shortfall_m2"] > 0 for o in f["directions"])
    assert f["other_frames"] and all(len(x["directions"]) == 2 for x in f["other_frames"])


def test_strip_longer_than_a_roll_is_spliced():
    """12.00 x 1.50 shower corridor along x: span 1.50 + 0.40 = 1.90, 2 strips (1.00, 1.00), each 12.40 m: 10.00 +
    (12.40 - 9.90) = 2.50 m with a 0.10 m end lap. Cut 2 x 12.40 = 24.80 m2; roll used 2 x 12.50 = 25.00 m; pieces
    10, 10, 2.5, 2.5: 3 rolls (lower bound 3)."""
    o = d(F.fold(rect(12.0, 1.5)), F.ALONG_LONG)
    assert [s["pieces"] for s in o["strip_list"]] == [2, 2]
    assert sorted(o["piece_lengths_m"]) == A([2.5, 2.5, 10.0, 10.0])
    assert o["cut_m2"] == A(24.8) and o["roll_length_used_m"] == A(25.0) and o["rolls_if_alone"] == 3


def test_narrow_room_one_strip():
    """2.00 x 0.50: 0.50 + 0.40 = 0.90 <= 1.00: one strip 0.90 wide x 2.40 m = 2.16 m2, 1 roll."""
    o = d(F.fold(rect(2.0, 0.5)), F.ALONG_LONG)
    assert widths_lengths(o) == [(0.9, 2.4)] and o["cut_m2"] == A(2.16) and o["rolls_if_alone"] == 1


def test_column_inside_area_upturn_is_its_own_piece():
    """3 x 3 with a 0.30 x 0.30 column: floor 9.00 - 0.09 = 8.91; the column lies inside one band, so the strips run
    over it (cut as the 3 x 3: 12.58). The column faces need 1.20 lm x 0.20 = 0.24 m2; the sheet over the column is
    0.30 x 0.30 = 0.09 m2 and can rise on the faces once: 0.15 m2 needs its own pieces (never claimed as covered)."""
    f = F.fold(rect(3.0, 3.0), holes=[rect(0.3, 0.3, 1.35, 1.35)])
    assert f["floor_m2"] == A(8.91) and "OBSTRUCTION_INSIDE" in f["flags"]
    assert f["obstruction_upturn"]["lm"] == A(1.2) and f["obstruction_upturn"]["m2"] == A(0.24)
    o = d(f, F.ALONG_LONG)
    assert o["cut_m2"] == A(12.58)
    assert o["hole_upturn"]["required_m2"] == A(0.24) and o["hole_upturn"]["covered_by_strips_m2"] == A(0.09)
    assert o["hole_upturn"]["own_pieces_m2"] == A(0.15)


def test_roof_skylight_opening_splits_the_strips():
    """roof 6.00 x 5.00 with a 2.00 x 2.00 skylight opening at x 2-4, y 1.5-3.5 (Q-29: open, 0.20 m upturn round it).
    Along the 6 m wall (span 5.00 + 0.40 = 5.40: 6 strips, last 5.40 - 5 x 0.90 = 0.90): floor bands 0-0.8, 0.8-1.7
    (y < 1.5 full width), 1.7-2.6, 2.6-3.5 (split by the opening into x 0-2 and 4-6: two strips of 2.40 each),
    3.5-4.4, 4.4-5.0 full. Lengths: 6.4, 6.4, 2.4 + 2.4, 2.4 + 2.4, 6.4, 6.4 (last 0.90 wide); cut 6.4 + 6.4 + 4 x 2.4 +
    6.4 + 0.9 x 6.4 = 34.56 m2. The opening's 8.00 lm x 0.20 = 1.60 m2 upturn: the split strips end 0.20 m inside it
    (side flaps covered); the full-width strip of band 0.8-1.7 has sheet to y 1.7, so the bottom flap (y 1.5-1.7) is
    covered; the full-width strip of band 3.5-4.4 laps back only to y 3.4, so of the top flap (y 3.3-3.5) the 0.10 m
    between the split strips' ends (x 2.2-3.8, 1.60 m) is bare: 0.16 m2; with the 4 corner squares where two flaps
    meet (4 x 0.04 = 0.16) the own pieces are 0.32 m2 and the strips cover 1.28 m2."""
    f = F.fold(rect(6.0, 5.0), holes=[rect(2.0, 2.0, 2.0, 1.5)])
    assert f["floor_m2"] == A(26.0)
    o = d(f, F.ALONG_LONG)
    assert sorted(widths_lengths(o)) == sorted([(1.0, 6.4), (1.0, 6.4), (1.0, 2.4), (1.0, 2.4), (1.0, 2.4),
                                                (1.0, 2.4), (1.0, 6.4), (0.9, 6.4)])
    assert o["cut_m2"] == A(34.56) and o["upturn_shortfall_m2"] == 0.0
    assert o["hole_upturn"]["required_m2"] == A(1.6) and o["hole_upturn"]["own_pieces_m2"] == A(0.32)
    assert o["hole_upturn"]["covered_by_strips_m2"] == A(1.28)


# ------------------------------------------------------------------------------------------------ BOQ lines, missing data
def test_open_side_is_a_threshold_line_q37():
    """pantry 4.50 x 3.00 open on one 4.50 m side: walls 3.00 + 3.00 + 4.50 = 10.50 lm (2.10 m2), threshold 4.50 lm,
    no door. Strips along the 4.50 wall: 4 x 4.90 m (1, 1, 1, 0.7) = 18.13 m2, 2 rolls; across: 6 x 3.40 m (last
    4.90 - 5 x 0.90 = 0.40) = 18.36 m2, 20.40 m of roll = 3 rolls."""
    r = F.area(floor="GF", room_id="P", polygon=rect(4.5, 3.0), roles_lm={"wall": 10.5, "other": 4.5})
    assert r["lines"]["upturn"]["lm"] == A(10.5) and r["lines"]["upturn"]["m2"] == A(2.1)
    assert [(t["role"], t["lm"]) for t in r["lines"]["thresholds"]] == [("other", 4.5)]
    assert d(r["fold"], F.ALONG_LONG)["cut_m2"] == A(18.13) and d(r["fold"], F.ALONG_LONG)["rolls_if_alone"] == 2
    assert d(r["fold"], F.ACROSS)["cut_m2"] == A(18.36) and d(r["fold"], F.ACROSS)["rolls_if_alone"] == 3


def test_typed_ring_roles_and_slivers():
    """upper-case wp_geometry roles are read; GLAZING is a threshold (UP-WP-003 by detail), not an upturn; a 4 mm
    open edge is a sliver, listed, not a line; a door edge with no opening id is listed with its count held."""
    r = F.area(floor="GF", room_id="B", polygon=rect(2.0, 1.5),
               roles_lm={"WALL": 5.0, "COLUMN": 0.2, "WINDOW_THRESHOLD": 0.6, "GLAZING": 0.5, "DOOR": 0.8,
                         "OTHER": 0.004})
    ln = r["lines"]
    assert ln["upturn"]["lm"] == A(5.8)
    assert [(t["role"], t["lm"]) for t in ln["thresholds"]] == [("glazing_edge", 0.5)]
    assert ln["sliver_lm"] == {"other": A(0.004)}
    assert ln["door_transitions"][0]["opening_id"] is None and ln["door_transitions"][0]["qty"] is None


def test_untyped_edges_hold_the_upturn_never_zero():
    r = F.area(floor="1F", room_id="X", polygon=rect(2.0, 2.0), roles_lm=None)
    assert r["lines"]["upturn"]["state"] == "HELD" and r["lines"]["upturn"]["lm"] is None
    assert r["state"] == "COMPUTED" and d(r["fold"], F.ALONG_LONG)["cut_m2"] is not None
    p = F.project([r])
    assert p["upturn_walls_lm"] is None and p["upturn_held_areas"] == 1


def test_bad_outline_is_held():
    r = F.area(floor="GF", room_id="Z", polygon=[(0, 0), (1, 0)])
    assert r["state"] == "HELD" and r["fold"] is None and r["reason"]
    bow = F.area(floor="GF", room_id="Y", polygon=[(0, 0), (2, 2), (2, 0), (0, 2)])
    assert bow["state"] == "HELD"


# ------------------------------------------------------------------------------------------------ project
def test_project_shared_door_once_and_rolls_per_direction_set():
    """kitchen 4 x 3 (along its 4 m wall: 4 strips x 4.40 m) and a 2.00 x 0.50 room (along: 1 strip x 2.40 m).
    All along: 4 x 4.40 + 2.40 = 20.00 m of roll; two 4.40 m fill a roll to 8.80, a third piece never fits with two
    (4.40 + 4.40 + 2.40 = 11.20 > 10): the pieces need 3 rolls (2 + 1 alone = 3 as well). The door D1 between the two
    rooms is one transition line, not two; a held room is counted beside, never 0. Walls 13.10 + 4.20 = 17.30 lm."""
    k = F.area(floor="GF", room_id="K", polygon=rect(4.0, 3.0), roles_lm={"wall": 13.1, "door": 0.9},
               doors=[{"opening_id": "D1", "width_m": 0.9}])
    n = F.area(floor="GF", room_id="N", polygon=rect(2.0, 0.5, 10.0, 0.0), roles_lm={"wall": 4.2, "door": 0.8},
               doors=[{"opening_id": "D1", "width_m": 0.8}])
    h = F.area(floor="GF", room_id="H", polygon=[(0, 0), (1, 0)])
    p = F.project([k, n, h])
    assert p["areas"] == 2 and p["held"] == 1 and p["selected"] is None
    assert len(p["door_transitions"]) == 1 and p["door_transitions_shared"] == 1
    assert p["floor_m2"] == A(13.0) and p["upturn_walls_lm"] == A(17.3)
    s = p["direction_sets"]["ALL_ALONG_LONGEST_WALL"]
    assert s["roll_length_used_m"] == A(20.0) and s["rolls_to_buy"] == 3 and s["rolls_if_each_area_alone"] == 3
    with pytest.raises(F.FoldError):
        F.project([k, k])


def test_u_shape_rotated_mirrored_in_mm():
    """the U of test_u_shape... turned 30 deg, in mm: the same strips (13.56 / 14.32 m2). Mirrored across its long
    wall (notch at the bottom), the layout from the lower wall is the original's other-start layout (13.08 m2) and
    vice versa: the start wall is a property of the room, not of how it was drawn, and both are always shown."""
    U = [(0, 0), (4, 0), (4, 3), (3, 3), (3, 1), (1, 1), (1, 3), (0, 3)]
    t = F.fold([(x * 1000.0, y * 1000.0) for x, y in turn(U, 30.0, (7.0, -2.0))], unit_m=0.001)
    assert d(t, F.ALONG_LONG)["cut_m2"] == A(13.56) and d(t, F.ACROSS)["cut_m2"] == A(14.32)
    m = F.fold([(x, -y) for x, y in U])
    a = d(m, F.ALONG_LONG)
    assert sorted([a["cut_m2"], a["other_start"]["cut_m2"]]) == A([13.08, 13.56])


def test_wedge_room_both_wall_frames_shown():
    """a wedge W.C. like the Alsenan core W.C.s: 2.00 x 1.50 with one corner cut by a 45 deg wall 0.50 m on each leg:
    floor 3.00 - 0.125 = 2.875, boundary 2.0 + 1.0 + 0.5 x sqrt(2) + 1.5 + 1.5 = 6.707. The 45 deg wall is 0.707 m,
    under the 1 m frame minimum: no second frame. Along x: the top strip's length is set by the 2.0 m wall below the
    diagonal (sheet to x 2.20 over y up to 1.70), so the diagonal's flap lies on sheet: no bare part. Across (strips
    along y, last band x 1.7 - 2.0, 0.60 wide, its floor reaching y 1.0 + 0.3 = 1.30, strip 1.70 m to y 1.50): the
    flap of the diagonal (x + y from 3.00 to 3.00 + 0.20 x sqrt(2) = 3.283) beyond x 1.70 (band 2's sheet edge) and
    y 1.50 (band 3's strip end) is bare: a right triangle with legs 3.283 - 3.20 = 0.083: 0.083^2 / 2 = 0.0034 m2."""
    f = F.fold([(0, 0), (2.0, 0), (2.0, 1.0), (1.5, 1.5), (0, 1.5)])
    assert f["floor_m2"] == A(2.875) and f["boundary_lm"] == A(2.0 + 1.0 + 0.5 * math.sqrt(2) + 3.0, abs=1e-4)
    assert f["shape"] == "NON_ORTHOGONAL" and f["other_frames"] == []
    assert d(f, F.ALONG_LONG)["upturn_shortfall_m2"] == 0.0
    b = d(f, F.ACROSS)
    assert widths_lengths(b) == [(1.0, 1.9), (1.0, 1.9), (0.6, 1.7)]
    assert b["upturn_shortfall_m2"] == A((0.2 * math.sqrt(2) - 0.2) ** 2 / 2, abs=1e-4)
