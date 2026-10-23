"""T-215: wall-end bounds closed from the drawn faces (research/agents_t215/junction_close.py). Villa T215-F, NOT
Alsenan. Hand truth (metres):

F1  L corner, both walls 0.20: wall A along -x (y 0 .. 0.20, outer face x = 0.20), wall B along -y (x 0 .. 0.20,
    outer face y = 0.20); centreline intersection P (0.10, 0.10); windows 2.00 (A) and 1.50 (B) from P.
    Drawn masonry = 2.10 x 0.20 + 0.20 x 1.60 - 0.20 x 0.20 = 0.700 m2. Mitre: A 2.000 m, B 1.500 m (0.400 + 0.300).
    The run counted A to the outer face (2.100 m) and B to A's inner face (1.400 m): 3.500 x 0.20 = 0.700, residual 0;
    closing moves 0.100 m from A to B (A -0.100, B +0.100), total unchanged.
F2  T stem + 45 deg stem under a through wall face y = 0, both 0.15: A x 0 .. 0.15 down to y = -1.00; B between
    x + y = 0.05 and x + y = 0.262132, its node on y = 0 at x = 0.156066, window 1.00 along (1, -1) / sqrt 2.
    B's drawn piece (shoelace, vertices (0.15,-0.10) (0.15,0) (0.262132,0) (0.916206,-0.654074) (0.810140,-0.760140))
    = 0.145000 m2; A 0.150000; total 0.295000 m2. Counted: A to y = -0.10 (0.900 m), B to its oblique cut, midline
    0.070711 from the node (0.929289 m): 0.15 x 1.829289 = 0.274393 m2. Junction piece (unmeasured) =
    0.15 x 0.10 + 0.112132 x 0.10 / 2 = 0.020607 m2 = 0.137377 m of 0.15 wall.
F3  0.20 wall ending on a 0.20 x 0.50 column: the counted run stops at the column face; the band beyond is concrete:
    delta 0, CLOSED (a held end inside a column is no masonry).
"""
import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "research" / "agents_t215"))
import junction_close as J  # noqa: E402

R2 = math.sqrt(2)


def f1(tr=lambda p: p, tu=lambda v: v):
    A = J.Wall("A", 0.2, tr((0.1, 0.1)), tu((-1, 0)), 2.0, -0.1)
    B = J.Wall("B", 0.2, tr((0.1, 0.1)), tu((0, -1)), 1.5, 0.1)
    # faces run on past the window cuts (as drawn faces do): the cuts close the cells, not a face end point
    faces = [((-2.0, 0), (0, 0)), ((0, 0), (0, -1.5)), ((-2.0, 0.2), (0.2, 0.2)), ((0.2, 0.2), (0.2, -1.5))]
    faces = [(tr(a), tr(b)) for a, b in faces]
    return [A, B], faces


def f2():
    c = 0.05 + 0.15 * R2 / 2
    A = J.Wall("A", 0.15, (0.075, 0.0), (0, -1), 1.0, 0.10)
    B = J.Wall("B", 0.15, (c, 0.0), (1 / R2, -1 / R2), 1.0, 0.05 * R2)
    faces = [((0, 0), (0, -1.0)), ((0.15, -0.10), (0.15, -1.0)), ((0.15, -0.10), (0.9, -0.85)),
             ((0.05 + 0.15 * R2, 0), (1.0, 0.05 + 0.15 * R2 - 1.0))]
    closing = [((-0.3, 0), (0.6, 0))]
    return [A, B], faces, closing


def test_f1_l_corner_mitre_hand_truth():
    walls, faces = f1()
    M = J.masonry_from_faces(faces, walls)
    assert M.area == pytest.approx(0.700, abs=1e-9)
    r = J.close_junction(M, walls)
    assert r["walls"]["A"]["share_len_m"] == pytest.approx(2.000, abs=1e-9)
    assert r["walls"]["B"]["share_len_m"] == pytest.approx(1.500, abs=1e-9)
    assert r["walls"]["A"]["delta_m"] == pytest.approx(-0.100, abs=1e-9)
    assert r["walls"]["B"]["delta_m"] == pytest.approx(+0.100, abs=1e-9)
    assert r["residual_m2"] == pytest.approx(0.0, abs=1e-9)
    assert r["status"] == "CLOSED"


@pytest.mark.parametrize("name,tr,tu", [
    ("mirror x", lambda p: (-p[0], p[1]), lambda v: (-v[0], v[1])),
    ("rotate 90", lambda p: (-p[1], p[0]), lambda v: (-v[1], v[0])),
    ("rotate 30 + shift", lambda p: (p[0] * math.cos(0.5236) - p[1] * math.sin(0.5236) + 50.0,
                                     p[0] * math.sin(0.5236) + p[1] * math.cos(0.5236) - 20.0),
     lambda v: (v[0] * math.cos(0.5236) - v[1] * math.sin(0.5236), v[0] * math.sin(0.5236) + v[1] * math.cos(0.5236))),
])
def test_f1_invariant_under_mirror_rotation_shift(name, tr, tu):
    walls, faces = f1(tr, tu)
    r = J.close_junction(J.masonry_from_faces(faces, walls), walls)
    assert r["walls"]["A"]["share_len_m"] == pytest.approx(2.000, abs=1e-6), name
    assert r["walls"]["B"]["share_len_m"] == pytest.approx(1.500, abs=1e-6), name


def test_f1_unequal_thickness_split_runs_through_both_corners():
    # A 0.20, B 0.10: overlap rectangle split on the line through the inner and outer corners (mitre)
    A = J.Wall("A", 0.2, (0.05, 0.1), (-1, 0), 2.0, 0.0)
    B = J.Wall("B", 0.1, (0.05, 0.1), (0, -1), 1.5, 0.0)
    faces = [((-1.95, 0), (0, 0)), ((0, 0), (0, -1.4)), ((-1.95, 0.2), (0.1, 0.2)), ((0.1, 0.2), (0.1, -1.4))]
    M = J.masonry_from_faces(faces, [A, B])
    r = J.close_junction(M, [A, B])
    # corner rectangle 0.10 x 0.20: each wall gets half (0.01 m2), the mitre's areas (diagonals: four equal triangles)
    assert r["walls"]["A"]["share_m2"] + r["walls"]["B"]["share_m2"] == pytest.approx(M.area, abs=1e-9)
    assert r["walls"]["B"]["share_m2"] == pytest.approx(1.4 * 0.1 + 0.01, abs=1e-9)


def test_f2_junction_piece_hand_truth_counted_once():
    walls, faces, closing = f2()
    M = J.masonry_from_faces(faces, walls, closing)
    assert M.area == pytest.approx(0.295000, abs=1e-6)
    r = J.close_junction(M, walls)
    assert r["residual_m2"] == pytest.approx(0.020607, abs=1e-6)
    assert sum(v["delta_m"] * v["t_m"] for v in r["walls"].values()) == pytest.approx(r["residual_m2"], abs=1e-9)
    assert r["overlap_m2"] <= J.AREA_TOL and r["unassigned_m2"] <= J.AREA_TOL


def test_adverse_junction_piece_in_both_walls_refused():
    walls, faces, closing = f2()
    r = J.close_junction(J.masonry_from_faces(faces, walls, closing), walls)
    # the hand-run habit: give the whole piece (0.137377 m) to A AND carry B to the face as well
    with pytest.raises(ValueError, match="counted twice"):
        J.check_claims(r, {"A": 0.137377, "B": 0.137377})
    assert J.check_claims(r, {"A": 0.137377})          # once is allowed


def test_adverse_l_corner_square_in_both_walls_refused():
    walls, faces = f1()
    r = J.close_junction(J.masonry_from_faces(faces, walls), walls)
    with pytest.raises(ValueError, match="counted twice"):
        J.check_claims(r, {"A": 0.1, "B": 0.1})         # nothing is unmeasured here


def test_f3_end_inside_a_column_closes_at_zero():
    W = J.Wall("W", 0.2, (0.1, 0.0), (0, -1), 0.5, 0.0)
    col = [(0, 0), (0.2, 0), (0.2, 0.5), (0, 0.5)]
    faces = [((0, 0.5), (0, -0.6)), ((0.2, 0.5), (0.2, -0.6))] + [(col[i], col[(i + 1) % 4]) for i in range(4)]
    M = J.masonry_from_faces(faces, [W], columns=[col])
    r = J.close_junction(M, [W])
    assert r["walls"]["W"]["delta_m"] == pytest.approx(0.0, abs=1e-9)
    assert r["status"] == "CLOSED"


def test_masonry_outside_every_band_is_held_never_dropped():
    W = J.Wall("W", 0.2, (0.1, 0.0), (0, -1), 0.5, 0.0, reach_m=0.1)
    from shapely.geometry import box
    M = box(0, -0.5, 0.2, 0.0).union(box(0.2, -0.3, 0.6, -0.1))   # a drawn nib no listed wall owns
    r = J.close_junction(M, [W])
    assert r["status"] == "PARTLY_HELD"
    assert r["unassigned_m2"] == pytest.approx(0.08, abs=1e-9)


def test_units_and_missing_data_refused():
    with pytest.raises(ValueError, match="metres"):
        J.Wall("A", 150, (0, 0), (1, 0), 1.0, 0.0).check()           # millimetres
    with pytest.raises(ValueError):
        J.Wall("A", 0.15, (0, 0), (0, 0), 1.0, 0.0).check()          # no direction
    with pytest.raises(ValueError, match="never 0"):
        from shapely.geometry import Polygon
        J.close_junction(Polygon(), [J.Wall("A", 0.15, (0, 0), (1, 0), 1.0, 0.0)])
    with pytest.raises(ValueError, match="twice"):
        w = J.Wall("A", 0.15, (0, 0), (1, 0), 1.0, 0.0)
        from shapely.geometry import box
        J.close_junction(box(0, -0.075, 1, 0.075), [w, w])


def test_two_through_walls_crossing_refused():
    A = J.Wall("A", 0.2, (0, 0), (1, 0), 1.0, 0.0, through=True)
    B = J.Wall("B", 0.2, (0, 0), (0, 1), 1.0, 0.0, through=True)
    from shapely.geometry import box
    M = box(-0.1, -0.1, 1.0, 0.1).union(box(-0.1, -0.1, 0.1, 1.0))
    with pytest.raises(ValueError, match="THROUGH"):
        J.close_junction(M, [A, B])


def test_through_wall_takes_the_overlap():
    # stem S (0.15) meets through wall T (0.20) at its face y = 0; T's band owns the seat, S stops on the face
    T = J.Wall("T", 0.2, (0.0, 0.1), (1, 0), 0.5, 0.0, through=True)
    S = J.Wall("S", 0.15, (0.0, 0.1), (0, -1), 1.0, 0.1)
    from shapely.geometry import box
    M = box(-0.5, 0.0, 0.5, 0.2).union(box(-0.075, -0.9, 0.075, 0.0))
    r = J.close_junction(M, [T, S])
    assert r["walls"]["S"]["share_len_m"] == pytest.approx(0.9, abs=1e-9)


def test_height_of_the_closed_piece_from_the_member_above():
    # F2 with a 0.20 beam (0.40 deep, storey 4.50 -> h 4.10) lying over y -0.05 .. 0.15 (arbitrary placement); slab
    # elsewhere 4.34. Hand: the unmeasured piece (0.020607 m2) splits at y = -0.05: above it A's rectangle 0.15 x 0.05
    # = 0.0075 plus B's triangle 0.112132 x 0.10 / 2 - (0.112132 x 0.05 ... ) -> checked through the identity below.
    from shapely.geometry import box
    walls, faces, closing = f2()
    r = J.close_junction(J.masonry_from_faces(faces, walls, closing), walls)
    beam = [(box(-1, -0.05, 2, 0.15), 4.10)]
    g = J.gross_change(walls, r, beam, 4.34)
    # identity: total change = integral of h over the masonry less over the counted strips, / t
    tot_share = J.height_integral(r["_regions"]["A"], beam, 4.34) + J.height_integral(r["_regions"]["B"], beam, 4.34)
    tot_cnt = sum(J.height_integral(J.counted_strip(w), beam, 4.34) for w in walls)
    assert sum(g.values()) * 0.15 == pytest.approx(tot_share - tot_cnt, abs=1e-12)
    # A's counted strip ends at y = -0.10, so its whole closed piece (-0.10 .. 0) lies half under the beam
    assert 4.10 * 0.0 < sum(g.values()) < 4.34 * 0.137377 + 1e-9
    assert sum(g.values()) > 4.10 * 0.137377 - 1e-9


def test_piece_with_no_member_drawn_is_held_never_defaulted():
    from shapely.geometry import box
    walls, faces, closing = f2()
    r = J.close_junction(J.masonry_from_faces(faces, walls, closing), walls)
    with pytest.raises(ValueError, match="HELD"):
        J.gross_change(walls, r, [(box(-1, -0.05, 2, 0.15), 4.10)], None)


def test_deepest_member_governs_where_two_overlap():
    from shapely.geometry import box
    region = box(0, 0, 1, 0.15)
    h = J.height_integral(region, [(box(0, 0, 0.5, 1), 4.10), (box(0.3, 0, 0.6, 1), 3.75)], 4.34)
    assert h == pytest.approx(0.15 * (0.3 * 4.10 + 0.3 * 3.75 + 0.4 * 4.34), abs=1e-12)
