"""T-017: PAIR_MIDLINE_CENSUS_V1 (independent masonry census) on a hand-calculated synthetic villa (not Alsenan).

Fixture K17 (metres): an exterior 0.20 ring on the centreline rectangle 10.0 x 6.0 (four L corners), a 0.40 x 0.40 column
standing in the bottom wall at x 7.0 .. 7.4, a window 1.20 in the right wall, a passage 1.00 with head lines on both
faces in the left wall, and an internal 0.15 wall at x 4.0 from the bottom wall to the top wall (a T at each end) with a
0.90 door. The linework is the outline of the union of the wall strips (as a CAD plan draws it: an L's outer face to
the outer corner, a T's through face continuous), openings and the column cut out.

Hand calculation (architectural run, openings IN the run, Q-73; column cut, Q-69 B; L at the midlines; T stem to the face):
  bottom: 0 .. 7.0 = 7.000 and 7.4 .. 10.0 = 2.600 (column 0.400 cut)          -> 9.600
  top 10.000, left 6.000 (passage 1.000 in the run), right 6.000 (window 1.200 in the run)
  0.20 total = 9.600 + 10.000 + 6.000 + 6.000 = 31.600 m
  stem: 6.000 - 0.100 - 0.100 = 5.800 m (door 0.900 in the run)                  -> 0.15 total 5.800 m
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest
from shapely.geometry import LineString, Polygon, box
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t017"))
import masonry_pair_census as PC  # noqa: E402


def strip(x0, y0, x1, y1, t):
    return LineString([(x0, y0), (x1, y1)]).buffer(t / 2, cap_style=2)


def outline_segments(geom):
    segs = []
    polys = getattr(geom, "geoms", [geom])
    for p in polys:
        for ring in [p.exterior, *p.interiors]:
            c = list(ring.coords)
            segs += [(c[i], c[i + 1]) for i in range(len(c) - 1)]
    return segs


def fixture_k17(with_column_outline=True, crossing=False):
    t, ti = 0.20, 0.15
    walls = [strip(-0.1, 0, 10.1, 0, t), strip(-0.1, 6, 10.1, 6, t), strip(0, -0.1, 0, 6.1, t),
             strip(10, -0.1, 10, 6.1, t), strip(4.0, 0.1, 4.0, 5.9, ti)]
    if crossing:
        walls += [strip(6.0, 2.0, 9.0, 2.0, ti), strip(7.5, 1.0, 7.5, 3.0, ti)]
    u = unary_union(walls)
    col = box(7.0, -0.2, 7.4, 0.2)
    door = box(4.0 - 0.2, 1.0, 4.0 + 0.2, 1.9)
    window = box(9.8, 2.0, 10.2, 3.2)
    passage = box(-0.2, 2.0, 0.2, 3.0)
    u = u.difference(col).difference(door).difference(window).difference(passage)
    wall = outline_segments(u)
    columns = [list(col.exterior.coords)] if with_column_outline else []
    opening_pts = [(4.0 - 0.075, 1.0), (4.0 - 0.075 - 0.9, 1.0), (10.0, 2.0), (10.0, 3.2), (10.0, 2.6)]
    others = [((-0.1, 2.0), (-0.1, 3.0)), ((0.1, 2.0), (0.1, 3.0))]       # passage head lines on both faces
    return wall, columns, opening_pts, others


def transform(data, f):
    wall, columns, pts, others = data
    return ([(f(a), f(b)) for a, b in wall], [[f(p) for p in c] for c in columns], [f(p) for p in pts],
            [(f(a), f(b)) for a, b in others])


def run(data, floor="K17"):
    wall, columns, pts, others = data
    return PC.census(wall, columns, pts, floor=floor, other_segments=others)


def by_t(res):
    return {k: v["arch_run_m"] for k, v in PC.totals(res).items()}


def test_hand_calculation_normal():
    res = run(fixture_k17())
    tot = PC.totals(res)
    assert tot["0.20"]["arch_run_m"] == pytest.approx(31.600, abs=1e-3)
    assert tot["0.15"]["arch_run_m"] == pytest.approx(5.800, abs=1e-3)
    assert tot["0.20"]["openings_m"] == pytest.approx(2.200, abs=1e-3)       # window 1.20 + passage 1.00
    assert tot["0.15"]["openings_m"] == pytest.approx(0.900, abs=1e-3)
    stem = [r for r in res["runs"] if r.t == 0.15]
    assert len(stem) == 1 and stem[0].ends == ["T_STEM", "T_STEM"]
    bottom = sorted((r for r in res["runs"] if r.t == 0.20 and abs(r.ang) < 1e-6 and abs(r.off) < 0.01),
                    key=lambda r: r.s0)
    assert [round(r.arch_run_m, 3) for r in bottom] == [7.0, 2.6]
    assert bottom[0].ends == ["L", "COLUMN"] and bottom[1].ends == ["COLUMN", "L"]


@pytest.mark.parametrize("name,f", [
    ("mirror", lambda p: (-p[0], p[1])),
    ("rotate30", lambda p: (p[0] * math.cos(0.5236) - p[1] * math.sin(0.5236), p[0] * math.sin(0.5236) + p[1] * math.cos(0.5236))),
    ("shift", lambda p: (p[0] + 1234.5, p[1] - 77.25)),
])
def test_adverse_mirror_rotation_shift(name, f):
    assert by_t(run(transform(fixture_k17(), f))) == pytest.approx(by_t(run(fixture_k17())), abs=2e-3)


def test_adverse_millimetre_input_refused():
    wall, columns, pts, others = transform(fixture_k17(), lambda p: (p[0] * 1000, p[1] * 1000))
    with pytest.raises(ValueError):
        PC.census(wall, columns, pts, other_segments=others)


def test_adverse_missing_column_outline_never_becomes_masonry():
    """Without the column outline the 0.40 gap has no evidence: the run splits there (listed), never bridged."""
    res = run(fixture_k17(with_column_outline=False))
    assert PC.totals(res)["0.20"]["arch_run_m"] == pytest.approx(31.600, abs=1e-3)
    assert any(g["kind"] == "SPLIT" and abs(g["width"] - 0.4) < 1e-6 for g in res["gaps"])


def test_crossing_counted_once():
    """Two 0.15 walls drawn through each other: 3.00 + 2.00 - 0.15 = 4.85 m (the crossing square once)."""
    res = run(fixture_k17(crossing=True))
    assert PC.totals(res)["0.15"]["arch_run_m"] == pytest.approx(5.800 + 4.850, abs=1e-3)
    assert sum(len(r.crossings) for r in res["runs"]) == 1


def ledger_k17():
    return [
        {"id": "K-W01", "t": 0.20, "a": (0, 0), "b": (7.0, 0), "length": 7.000},
        {"id": "K-W02", "t": 0.20, "a": (7.4, 0), "b": (10.0, 0), "length": 2.600},
        {"id": "K-W03", "t": 0.20, "a": (0, 6), "b": (10, 6), "length": 10.000},
        {"id": "K-W04", "t": 0.20, "a": (0, 0), "b": (0, 6), "length": 6.000},
        {"id": "K-W05", "t": 0.20, "a": (10, 0), "b": (10, 6), "length": 6.000},
        {"id": "K-W06", "t": 0.15, "a": (4.0, 0.1), "b": (4.0, 5.9), "length": 5.800},
    ]


def test_agreement_normal_all_agree():
    rows = PC.agreement(ledger_k17(), run(fixture_k17()))
    assert {r["id"]: r["status"] for r in rows} == {f"K-W0{i}": "AGREE" for i in range(1, 7)}


def test_adverse_missing_wall_reported_both_ways():
    led = [r for r in ledger_k17() if r["id"] != "K-W06"] + [
        {"id": "K-W99", "t": 0.15, "a": (2.0, 3.0), "b": (3.5, 3.0), "length": 1.500}]   # not drawn on the plan
    st = {r["id"]: r["status"] for r in PC.agreement(led, run(fixture_k17()))}
    assert st["K-W99"] == "MISSING_IN_CENSUS"
    assert list(st.values()).count("MISSING_IN_LEDGER") == 1               # the undeclared stem


def test_adverse_stem_to_centreline_and_duplicated_stem_reported():
    led = ledger_k17()
    led[5] = dict(led[5], a=(4.0, 0.0), b=(4.0, 6.0), length=6.000)       # stem run to both midlines
    rows = {r["id"]: r for r in PC.agreement(led, run(fixture_k17()))}
    assert rows["K-W06"]["status"] == "DIFFERS" and rows["K-W06"]["d_m"] == pytest.approx(0.200, abs=1e-3)
    led = ledger_k17() + [{"id": "K-W06b", "t": 0.15, "a": (4.0, 2.0), "b": (4.0, 5.9), "length": 3.900}]
    rows = {r["id"]: r for r in PC.agreement(led, run(fixture_k17()))}
    assert rows["K-W06"]["status"] == rows["K-W06b"]["status"] == "DUPLICATE"


def test_stem_to_centreline_cause_named():
    led = ledger_k17()
    led[5] = dict(led[5], a=(4.0, 0.1), b=(4.0, 6.0), length=5.900)       # one end to the top wall's midline
    rows = {r["id"]: r for r in PC.agreement(led, run(fixture_k17()))}
    assert rows["K-W06"]["cause"] == "STEM_TO_CENTRELINE"


def test_independence_no_engine_import():
    src = (ROOT / "research" / "agents_t017" / "masonry_pair_census.py").read_text()
    for banned in ("engine", "masonry_centreline", "arch_walls", "masonry_area", "shapely", "ezdxf"):
        assert f"import {banned}" not in src and f"from {banned}" not in src
