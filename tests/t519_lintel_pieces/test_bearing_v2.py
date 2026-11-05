"""LINTEL_BEARING_V2 (F-C-T516-1) on synthetic geometry, against the merged V1 reach of research/agents_t516.

Wall 0.15 m thick along the axis, jamb at s = 0, masonry to s = 2.0. A column drawn at 45 degrees (a square of
half-diagonal 0.20 m) points its corner at s = 1.000 m, 35 mm off the axis (inside the band).
  V1: the intrusion beyond the corner is a right-angled triangle of area d^2; d^2 < 2e-5 m2 -> V1 runs to
      d = sqrt(2e-5) = 4.47 mm past the corner, and its point probe on the axis (the column reaches the axis only at
      s = 1.035) calls the stopper END_OF_MASONRY.
  V2: the triangle is d along and 2d across; min = d <= 0.5 mm -> V2 stops within 0.5 mm of the corner; the band probe
      meets the column -> COLUMN.
Normal: no column -> both reach the masonry end (2.000 m), END_OF_MASONRY. Hairlines: a 0.1 mm crosswise seam closes in
both; a 0.2 mm lengthwise seam (two half-thickness drafts) closes in V2 and stops V1 near the jamb; a real 1 mm gap
stops both. Rotation: the same geometry rotated 30 degrees gives the same V2 reach.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest
from shapely import affinity
from shapely.geometry import Point, Polygon, box

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research" / "agents_t519"))
sys.path.insert(0, str(ROOT / "research" / "agents_t516"))

import lintel_bearing_v2 as V2  # noqa: E402
import t516_extract as V1  # noqa: E402

H = 0.075
COL = Polygon([(1.0, 0.035), (1.2, 0.235), (1.4, 0.035), (1.2, -0.165)])
WALL = box(0.0, -H, 2.0, H)


def test_v1_runs_into_a_pointed_corner_v2_stops():
    M = WALL.difference(COL)
    e1, _ = V1.reach(M, (0, 0), 1, 0, 0.0, +1, H)
    e2, cap = V2.reach(M, (0, 0), 1, 0, 0.0, +1, H)
    assert e1 == pytest.approx(1.0 + math.sqrt(V1.EPS_AREA), abs=3e-4)       # ~4.5 mm into the column
    assert e2 == pytest.approx(1.0, abs=5e-5) and not cap                   # stops at the corner itself
    assert V2.stopper(e2, cap, (0, 0), 1, 0, 0.0, +1, H, [COL], []) == ("COLUMN", "")
    # V1's axis probe misses the off-axis corner
    assert not COL.contains(Point(e1 + 0.003, 0.0))


def test_normal_no_column():
    e2, cap = V2.reach(WALL, (0, 0), 1, 0, 0.0, +1, H)
    assert e2 == pytest.approx(2.0, abs=2e-5)
    assert V2.stopper(e2, cap, (0, 0), 1, 0, 0.0, +1, H, [], []) == ("END_OF_MASONRY", "")


def test_hairlines_and_real_gap():
    cross = box(0, -H, 1.0, H).union(box(1.0001, -H, 2.0, H))
    assert V2.reach(cross, (0, 0), 1, 0, 0.0, +1, H)[0] == pytest.approx(2.0, abs=2e-5)
    assert V1.reach(cross, (0, 0), 1, 0, 0.0, +1, H)[0] == pytest.approx(2.0, abs=2e-4)   # V1 overruns by area left
    seam = box(0, -H, 2.0, -0.0001).union(box(0, 0.0001, 2.0, H))
    assert V2.reach(seam, (0, 0), 1, 0, 0.0, +1, H)[0] == pytest.approx(2.0, abs=2e-5)
    assert V1.reach(seam, (0, 0), 1, 0, 0.0, +1, H)[0] < 0.2                  # area tolerance trips on a long seam
    gap = box(0, -H, 1.0, H).union(box(1.001, -H, 2.0, H))
    e2, cap = V2.reach(gap, (0, 0), 1, 0, 0.0, +1, H)
    assert e2 == pytest.approx(1.0, abs=5e-5)
    gid = box(1.0, -H - 0.01, 1.001, H + 0.01)
    assert V2.stopper(e2, cap, (0, 0), 1, 0, 0.0, +1, H, [], [("OP-X", gid)]) == ("OPENING", "OP-X")


def test_rotation_and_mirror_invariant():
    M = WALL.difference(COL)
    ang = math.radians(30)
    Mr = affinity.rotate(M, 30, origin=(0, 0))
    e0, _ = V2.reach(M, (0, 0), 1, 0, 0.0, +1, H)
    er, _ = V2.reach(Mr, (0, 0), math.cos(ang), math.sin(ang), 0.0, +1, H)
    assert er == pytest.approx(e0, abs=2e-5)
    Mm = affinity.scale(M, xfact=-1, origin=(0, 0))                          # mirrored: search in -s
    em, _ = V2.reach(Mm, (0, 0), 1, 0, 0.0, -1, H)
    assert em == pytest.approx(e0, abs=2e-5)


def test_search_limit_and_jamb_on_column():
    long = box(0, -H, 5.0, H)
    assert V2.reach(long, (0, 0), 1, 0, 0.0, +1, H) == (3.0, True)
    assert V2.stopper(3.0, True, (0, 0), 1, 0, 0.0, +1, H, [], []) == ("SEARCH_LIMIT", "")
    col_at_jamb = box(0.0, -0.2, 0.3, 0.2)
    assert V2.reach(WALL.difference(col_at_jamb), (0, 0), 1, 0, 0.0, +1, H) == (0.0, False)


def test_expected_training_villa_move_recorded_not_applied():
    (m,) = V2.EXPECTED_TRAINING_VILLA_MOVES
    assert m["state_v1"] == m["state_v2"] == "BOUNDED" and m["v2_stopper"] == "COLUMN"
    assert m["length_hi_v2_m"] == pytest.approx(0.80 + 0.827 + 0.238) and "NOT RE-RUN" in m["status"]
