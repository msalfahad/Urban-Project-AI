"""engine/source/opening_census.py - synthetic known answers only (no project data)."""

from __future__ import annotations

import math

import pytest

from engine.source import opening_census as OC


def wall(x0, x1, y=0.0, t=200.0, tag="w"):
    return [(f"{tag}a", (x0, y), (x1, y)), (f"{tag}b", (x0, y + t), (x1, y + t))]


def band_of(segs, t=(80, 400)):
    lines = OC.face_lines(segs)
    bands = OC.wall_bands(lines, *t)
    assert len(bands) == 1
    return bands[0]


def test_face_lines_merge_collinear_and_keep_gaps():
    segs = wall(0, 1000) + wall(1900, 3000, tag="v")
    lines = OC.face_lines(segs)
    assert len(lines) == 2
    assert [[round(a), round(b)] for a, b, _ in lines[0]["cover"]] == [[0, 1000], [1900, 3000]]


def test_wall_band_needs_two_faces_in_range_and_no_line_between():
    assert len(OC.wall_bands(OC.face_lines(wall(0, 1000, t=500)), 80, 400)) == 0
    segs = wall(0, 1000) + [("mid", (0, 100), (1000, 100))]
    bands = OC.wall_bands(OC.face_lines(segs), 80, 400)
    assert all(round(b["t"]) == 100 for b in bands)          # only the nearest facing pairs
    with pytest.raises(OC.OpeningCensusError):
        OC.wall_bands([], 0, 100)


def test_masonry_jamb_opening():
    b = band_of(wall(0, 1000) + wall(1900, 3000, tag="v"))
    (g,) = OC.band_gaps(b)
    assert (round(g["s0"]), round(g["s1"]), round(g["width"])) == (1000, 1900, 900)
    assert g["start_jamb"] == g["end_jamb"] == OC.MASONRY_JAMB and g["state"] == OC.OPENING


def test_faces_ending_apart_are_unbounded_and_rejected():
    segs = [("a", (0, 0), (1000, 0)), ("b", (0, 200), (1100, 200)), ("c", (1900, 0), (3000, 0)),
            ("d", (1900, 200), (3000, 200))]
    (g,) = OC.band_gaps(band_of(segs))
    assert g["start_jamb"] == OC.UNBOUNDED and g["state"] == OC.REJECTED
    assert OC.decide_gap(g, ["DOOR"]) == (OC.REJECTED, OC.WALL_DEFLECTION)


def test_column_jamb_and_closure_jamb():
    # the wall faces run along the column (built to its thickness, P8-N20); the gap ends at its face
    col = ("C1", [(1900, -10), (2200, -10), (2200, 210), (1900, 210)])
    segs = wall(0, 1000) + wall(1900, 3000, tag="v")
    (g,) = OC.band_gaps(band_of(segs), obstacles=[col])
    assert g["end_jamb"] == OC.COLUMN_JAMB and g["end_column"] == "C1" and round(g["width"]) == 900
    far = ("C2", [(2500, -10), (2800, -10), (2800, 210), (2500, 210)])
    (g,) = OC.band_gaps(band_of(segs), obstacles=[far])
    assert g["end_jamb"] == OC.MASONRY_JAMB                  # a column further along is not a jamb
    segs = [("a", (0, 0), (1000, 0)), ("b", (0, 200), (1200, 200)), ("x", (1200, -150), (1200, 200)),
            ("c", (1900, 0), (3000, 0)), ("d", (1900, 200), (3000, 200))]
    (g,) = OC.band_gaps(band_of(segs), closures=segs)
    assert g["start_jamb"] == OC.CLOSURE_JAMB and g["start_column"] == "x"


def test_closure_needs_evidence():
    g = {"start_jamb": OC.CLOSURE_JAMB, "end_jamb": OC.MASONRY_JAMB}
    assert OC.decide_gap(g, []) == (OC.REJECTED, OC.CLOSURE_WITHOUT_EVIDENCE)
    assert OC.decide_gap(g, ["GLAZING"]) == (OC.OPENING, None)
    assert OC.decide_gap({"start_jamb": OC.MASONRY_JAMB, "end_jamb": OC.COLUMN_JAMB}, []) == (OC.OPENING, None)
    with pytest.raises(OC.OpeningCensusError):
        OC.decide_gap(g, ["WINDOW"])


def test_overhead_cover_needs_both_faces():
    b = band_of(wall(0, 1000) + wall(1900, 3000, tag="v"))
    both = [("o1", (1000, 0), (1900, 0)), ("o2", (1000, 200), (1900, 200))]
    assert OC.overhead_cover(b, 1000, 1900, both)
    assert not OC.overhead_cover(b, 1000, 1900, both[:1])
    assert not OC.overhead_cover(b, 1000, 1900, [("o1", (1000, 0), (1300, 0)), ("o2", (1000, 200), (1900, 200))])


def test_side_points_are_beyond_each_face():
    b = band_of(wall(0, 1000) + wall(1900, 3000, tag="v"))
    (g,) = OC.band_gaps(b)
    pa, pb = OC.side_points(g, b, 300)
    assert sorted([round(pa[1]), round(pb[1])]) == [-300, 500]
    assert round(pa[0]) == round(pb[0]) == 1450


def test_parallel_runs_and_run_ends():
    segs = [(f"g{i}", (40 * i, 1000), (40 * i, 5950)) for i in range(4)]
    (run,) = OC.parallel_runs(segs, max_width=300, min_len=300)
    assert round(run["width"]) == 4950 and round(run["hi"] - run["lo"]) == 120
    closures = [("top", (-50, 5950), (200, 5950)), ("bot", (-50, 1000), (200, 1000))]
    e = OC.run_ends(run, closures=closures)
    assert e["start_jamb"] == e["end_jamb"] == OC.CLOSURE_JAMB
    assert OC.run_ends(run)["start_jamb"] == OC.UNBOUNDED


def test_arc_band_gap_mid_radius_length():
    arcs = [("i1", (0, 0), 1000, 0, 40), ("i2", (0, 0), 1000, 80, 180),
            ("o1", (0, 0), 1200, 0, 40), ("o2", (0, 0), 1200, 80, 180)]
    (b,) = OC.arc_bands(arcs, 80, 400)
    (g,) = OC.arc_gaps(b)
    assert g["state"] == OC.OPENING
    assert g["width_mid_arc"] == pytest.approx(math.radians(40) * 1100)
    assert g["chord_mid"] == pytest.approx(2 * 1100 * math.sin(math.radians(20)))


def test_chain_levels_sum_printed_values_and_flag_conflicts():
    dims = [(0, 1000, 1000), (1000, 5500, 4500), (5500, 5700, 200), (1000, 4300, 3300)]
    lv, cf = OC.chain_levels(dims, [(0, 0)])
    assert lv == {0: 0, 1000: 1000, 5500: 5500, 5700: 5700, 4300: 4300} and not cf
    lv, cf = OC.chain_levels(dims + [(0, 4300, 4000)], [(0, 0)])
    assert cf                                               # 4300 reached as 4300 and as 4000
    lv, _ = OC.chain_levels([(10, 20, 10), (100, 200, 100)], [(10, 0)])
    assert 100 not in lv                                    # an unconnected chain gets no level
    with pytest.raises(OC.OpeningCensusError):
        OC.chain_levels([(0, 10, 0)], [(0, 0)])


def test_vote_offset_and_mirror():
    p = [0, 1552, 2045, 3597, 7745, 8245]
    e = [x + 7146.3 for x in p]
    c, n, second, _ = OC.vote_offset(e, p, 1, 2.0)
    assert c == pytest.approx(7146.3) and n == 6 and second < n
    c, n, _, _ = OC.vote_offset([100 - x for x in p], p, -1, 2.0)
    assert c == pytest.approx(100) and n == 6
    with pytest.raises(OC.OpeningCensusError):
        OC.vote_offset(e, p, 0)
