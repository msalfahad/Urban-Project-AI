"""T-526 (R-T526-1, COLUMN_END_CENSUS_V2) on a hand-calculated villa that is not the development villa (villa P526).

Villa P526, one storey, black blocks 0.20 m, course 0.19 + 10 mm joint (module 0.20), owner joint 10 mm:
  run R1: axis (0, 0) -> (3.00, 0), t 0.20. Column K1 0.30 (along) x 0.40 (across), centred on the axis, drawn ONLY on the
          structural sheet, standing beyond the end at x 3.00 .. 3.30 (the run ends ON its face, so no run piece is a
          column). V1 (consecutive pieces) lists 0 junctions; V2 lists 1 END junction, gap 0, cover 1.
  hand effects of that junction (block 3.00 m under a beam, block top 2.80 m; a column piece C0 at the start in the run):
    sharmat ties (R-T355-1, levels z = 3 k x 0.20 while z + 0.01 < 2.80): k = 1 .. 4 (0.60, 1.20, 1.80, 2.40) = 4 nr;
    V-joint mesh (T-317 drawing band, finished floor 0.10): 2.80 - 0.10 = 2.70 m per finished side, 2 sides = 5.40 m;
    perimeter mortar (R-T520-1): end F -> C makes the course segment c = 2: + 2.80 m of vertical joint, less one more
    uncredited top corner: 0.92625 x 0.20 x 0.010 x (2.80 - 0.010) = 0.0051684750 m3;
    blockwork length / m2 / blocks along the run: 0 (the end face is the column face).
Adverse: a corner-only touch (no joint face), a half-thickness offset column (HELD, contact named), a 5 mm drawn gap
(inside the 10 mm joint: junction, length unchanged), a 15 mm gap (HELD), units in mm, missing outlines, mirror and
rotation invariance, no double count with V1's own column piece.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest
from shapely import affinity
from shapely.geometry import Polygon, box

ROOT = Path(__file__).resolve().parents[2]
for p in ("agents_t526", "agents_t520", "agents_t355", "agents_t317"):
    sys.path.insert(0, str(ROOT / "research" / p))
import end_census_v2 as E  # noqa: E402
import perimeter_joint_v1 as PJ  # noqa: E402
import t317_spatter_mesh as M  # noqa: E402
import t355_masonry_accessories as X  # noqa: E402

A, B, T, J = (0.0, 0.0), (3.00, 0.0), 0.20, 0.010
K1 = box(3.00, -0.20, 3.30, 0.20)          # structural-only column beyond end 1


def test_run_ending_on_a_structural_only_column_is_a_junction():
    r = E.classify_end(A, B, T, 1, [K1], J)
    assert (r.cls, r.gap_m, r.cover, r.junction) == ("COLUMN", 0.0, 1.0, True)
    assert E.classify_end(A, B, T, 0, [K1], J).cls == "NO_COLUMN"
    # V1 sees no column piece in the run: no junction; V2 adds exactly one END junction
    ends = [E.classify_end(A, B, T, e, [K1], J) for e in (0, 1)]
    js = E.end_junctions("P526-R1", ["BLOCK"], ends)
    assert [j["source"] for j in js] == ["V2_END"] and js[0]["at"] == "end 1"
    # the architectural-only list (column not drawn there) misses it: the census must read both drawings
    assert E.classify_end(A, B, T, 1, [], J).cls == "NO_COLUMN"


def test_hand_effects_of_the_added_junction():
    # sharmat ties (T-355 code), 4 by hand
    course = X.course_spec(0.190, 0.010, "P526 fixture", "FIXTURE")
    blk = X.make_piece("BLOCK", 3.00, 2.80, "R1@b0")
    old = X.Panel("P526-R1", "GF", (blk,), (), course)
    new = X.Panel("P526-R1", "GF", (blk, X.make_piece("COLUMN", 0.30, None, "R1@3.000")), (), course)
    assert X.ties(old) == []
    t = X.ties(new)
    assert len(t) == 1 and t[0]["ties"] == 4 and [z for _k, z, _h in X.levels(course, 2.80)] == [0.6, 1.2, 1.8, 2.4]
    # V-joint mesh, drawing band (T-317 code): 2.70 m per finished side
    sides = (M.Side("INT-A", "PLASTER", 0.10, 2.90), M.Side("INT-B", "PLASTER", 0.10, 2.90))
    w0 = M.make_wall("P526-R1", 3.00, [M.Piece("BLOCK", 3.00, 2.80, "BM1", (), "BEAM")], sides)
    w1 = M.make_wall("P526-R1", 3.00, [M.Piece("BLOCK", 3.00, 2.80, "BM1", (), "BEAM"),
                                         M.Piece("COLUMN", 0.30, None, "K1")], sides)
    v = lambda w: [j for j in M.joints_to_soffit(w, 0.10) if j["dir"] == "V"]
    assert v(w0) == [] and [j["length_m"] for j in v(w1)] == [2.70, 2.70]
    # perimeter mortar (R-T520-1): F -> C at end 1, the start column C0 in the run
    mod = (0.39, 0.19, 0.40, 0.20)
    ps = [PJ.Piece("COLUMN", 0.30, None, "C0"), PJ.Piece("BLOCK", 3.00, 2.80, "BM1")]
    before = PJ.measure(PJ.Wall("P526-R1", T, J, mod, ps, "C", "F"))["m3"]
    after = PJ.measure(PJ.Wall("P526-R1", T, J, mod, ps, "C", "C"))["m3"]
    assert after - before == pytest.approx(0.92625 * 0.20 * 0.010 * (2.80 - 0.010), abs=1e-12)
    assert after - before == pytest.approx(0.0051684750, abs=1e-10)


def test_corner_only_touch_is_not_a_junction():
    edge = box(3.00, 0.10, 3.30, 0.40)         # meets the end only on the wall face line: no joint face (zero area)
    assert E.classify_end(A, B, T, 1, [edge], J).cls == "NO_COLUMN"
    tip = Polygon([(3.00, 0.10), (3.20, 0.30), (3.40, 0.10), (3.20, 0.25)])   # a vertex on the wall face corner
    assert E.classify_end(A, B, T, 1, [tip], J).cls == "NO_COLUMN"
    # a column turned 45 deg with its corner at the end face: part of the thickness only -> HELD, never a full joint
    diamond = Polygon([(3.00, 0.0), (3.15, 0.15), (3.30, 0.0), (3.15, -0.15)])
    r = E.classify_end(A, B, T, 1, [diamond], J)
    assert r.cls == "PARTIAL_COLUMN" and r.junction is None


def test_offset_column_is_partial_and_held_by_name():
    half = box(3.00, 0.0, 3.30, 0.40)          # meets 0.0995 m of the 0.20 m thickness (0.5 mm inset)
    r = E.classify_end(A, B, T, 1, [half], J)
    assert r.cls == "PARTIAL_COLUMN" and r.junction is None and r.contact_m == pytest.approx(0.0995, abs=1e-6)
    assert "0.0995" in r.held
    js = E.end_junctions("P526-R1", ["BLOCK"], [E.classify_end(A, B, T, 0, [half], J), r])
    assert js == [{"run": "P526-R1", "at": "end 1", "source": "V2_END", "state": "HELD", "held": r.held}]


def test_tolerance_5_mm_short_is_a_junction_15_mm_is_held():
    r5 = E.classify_end(A, B, T, 1, [box(3.005, -0.20, 3.305, 0.20)], J)
    assert (r5.cls, r5.junction) == ("COLUMN_WITHIN_JOINT", True) and r5.gap_m == pytest.approx(0.005, abs=1e-9)
    r15 = E.classify_end(A, B, T, 1, [box(3.015, -0.20, 3.315, 0.20)], J)
    assert (r15.cls, r15.junction) == ("GAP_HELD", None) and "15.0 mm" in r15.held
    far = E.classify_end(A, B, T, 1, [box(3.06, -0.20, 3.36, 0.20)], J)
    assert far.cls == "NO_COLUMN"              # beyond the 0.05 m search: not this end's column
    # a run end 5 mm INSIDE the outline still reads the column at the face (gap 0)
    assert E.classify_end(A, B, T, 1, [box(2.995, -0.20, 3.295, 0.20)], J).cls == "COLUMN"


@pytest.mark.parametrize("deg", [0.0, 37.0, 90.0, 213.5])
@pytest.mark.parametrize("mirror", [False, True])
def test_rotation_and_mirror_invariant(deg, mirror):
    def tf(g):
        g = affinity.scale(g, -1.0 if mirror else 1.0, 1.0, origin=(0, 0)) if mirror else g
        return affinity.rotate(g, deg, origin=(0, 0))

    def pt(p):
        return tuple(tf(Polygon([p, (p[0] + 1e-9, p[1]), (p[0], p[1] + 1e-9)])).exterior.coords[0])
    a, b = pt(A), pt(B)
    for col, cls in ((K1, "COLUMN"), (box(3.005, -0.2, 3.305, 0.2), "COLUMN_WITHIN_JOINT"),
                     (box(3.0, 0.0, 3.3, 0.4), "PARTIAL_COLUMN"), (box(3.0, 0.1, 3.3, 0.4), "NO_COLUMN")):
        assert E.classify_end(a, b, T, 1, [tf(col)], J).cls == cls
    # reversing the run swaps the end index, not the result
    assert E.classify_end(b, a, T, 0, [tf(K1)], J).cls == "COLUMN"


def test_units_and_missing_inputs_refused():
    with pytest.raises(E.EndCensusError):
        E.classify_end(A, B, 200, 1, [K1], J)          # thickness in mm
    with pytest.raises(E.EndCensusError):
        E.classify_end(A, B, T, 1, [K1], 10)           # joint in mm
    with pytest.raises(E.EndCensusError):
        E.classify_end(A, B, T, 1, None, J)            # outlines not read: never 'no column'
    with pytest.raises(E.EndCensusError):
        E.classify_end(A, B, None, 1, [K1], J)
    with pytest.raises(E.EndCensusError):
        E.classify_end(A, A, T, 1, [K1], J)


def test_no_double_count_with_v1_column_piece():
    r = E.classify_end(A, B, T, 1, [K1], J, own_piece_is_column=True)
    assert r.cls == "COLUMN_PIECE_IN_RUN"
    js = E.end_junctions("P526-R1", ["BLOCK", "COLUMN"], [E.classify_end(A, B, T, 0, [K1], J), r])
    assert [j["source"] for j in js] == ["V1"]        # once, by V1
    with pytest.raises(E.EndCensusError):              # a column beyond the end of a column piece is inconsistent
        E.end_junctions("P526-R1", ["BLOCK", "COLUMN"], [E.classify_end(A, B, T, 0, [K1], J),
                                                         E.classify_end(A, B, T, 1, [K1], J)])
    with pytest.raises(E.EndCensusError):              # a HELD end must carry its reason
        E.end_junctions("P526-R1", ["BLOCK"], [E.EndResult("GAP_HELD", 0.02, 1.0, T, 0, None, "")])


def test_math_isclose_guard():
    assert math.isclose(E.PROBE, 0.02) and E.SEARCH == 0.05 and E.COVER_FULL == 0.999
