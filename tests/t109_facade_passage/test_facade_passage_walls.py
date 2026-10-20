"""T-109 FACADE_PASSAGE_WALLS_V1: hand fixtures, NOT the development villa.

Plan (metres; north up): two blocks with 0.20 m walls whose north and south faces are collinear, a 1.50 m strip of
ground between them.
  Block A: outer 0.00 .. 6.00 x 0.00 .. 5.00, one room (label at 3.00, 2.50); a 1.00 m door in its east wall at
           y 1.00 .. 2.00 (opening onto the strip).
  Block B: outer 7.50 .. 15.00 x 0.00 .. 5.00, one room (label at 11.00, 2.50); a 1.50 m window in its west wall at
           y 2.00 .. 3.50.
  The census reads the strip's two ends as doorless wall openings (PASSAGE): OP-N at the north face line (thresholds
  at y 5.00 and 4.80), OP-S at the south face line (thresholds at y 0.00 and 0.20).
  Variant "boundary": a boundary wall drawn on a layer of its own closes the south end (lines y 0.00 and y 0.20 across
  the strip): an open-air dead-end passage, open to the court at the north.
  Variant "through": nothing is drawn across either end: a passage open at both ends.

Hand calculation:
  engine outline (crosses the strip at both ends) = 2 x (15.00 + 5.00) = 40.00 m (OP-N 1.50 + OP-S 1.50 included).
  boundary: exterior faces = A 6.00 + 5.00 + 6.00 + its east face from the boundary wall's inner face (y 0.20) to the
            north face line 4.80 (door included) + B 7.50 + 5.00 + 7.50 + its west face 4.80 (window included)
            = 46.60 m = 40.00 - 1.50 - 1.50 + 4.80 + 4.80; the 1.50 m inner face of the boundary wall is not counted.
  through:  the walls run the full 5.00 m: 40.00 - 3.00 + 10.00 = 47.00 m.
  strip area: boundary 1.50 x 4.80 = 7.20 m2 (plus the OP-N band 0.30 m2 inside it: 1.50 x 5.00 - the boundary wall
            band 0.30 = 7.20 m2 in all), through 7.50 m2.
Variants: rotated 30 / -121 deg, mirrored, in m and in mm (unit 0.001) through the engine's own topology
(engine.source.topology.build) and arch_v29.facade_outlines (the walked run is the engine's run)."""
from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.source import arch_v29 as V29                         # noqa: E402
from engine.source import facade_passage_walls as P               # noqa: E402
from engine.source import topology as TP                          # noqa: E402


def rect(x0, y0, x1, y1, role, tag):
    pts = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    return [(pts[i], pts[(i + 1) % 4], role, "%s%d" % (tag, i)) for i in range(4)]


def plan(passage_threshold_extra=False):
    """segments (a, b, role, source) of the two blocks, their openings and the census thresholds of the strip."""
    s = []
    # block A outer faces; east face split by the door (x 6.00, y 1.00 .. 2.00)
    s += [((0, 0), (6, 0), "WALL", "A_S"), ((0, 0), (0, 5), "WALL", "A_W"), ((0, 5), (6, 5), "WALL", "A_N"),
          ((6, 0), (6, 1), "WALL", "A_E1"), ((6, 2), (6, 5), "WALL", "A_E2"),
          ((6, 1), (6, 2), "DOOR_THRESHOLD", "THR|D-1|0")]
    # block A inner faces; the door's inner threshold and its jambs
    s += [((0.2, 0.2), (5.8, 0.2), "WALL", "a_s"), ((0.2, 0.2), (0.2, 4.8), "WALL", "a_w"),
          ((0.2, 4.8), (5.8, 4.8), "WALL", "a_n"), ((5.8, 0.2), (5.8, 1), "WALL", "a_e1"),
          ((5.8, 2), (5.8, 4.8), "WALL", "a_e2"), ((5.8, 1), (5.8, 2), "DOOR_THRESHOLD", "THR|D-1|1"),
          ((5.8, 1), (6, 1), "WALL", "jd1"), ((5.8, 2), (6, 2), "WALL", "jd2")]
    # block B outer faces; west face split by the window (x 7.50, y 2.00 .. 3.50)
    s += [((7.5, 0), (15, 0), "WALL", "B_S"), ((15, 0), (15, 5), "WALL", "B_E"), ((7.5, 5), (15, 5), "WALL", "B_N"),
          ((7.5, 0), (7.5, 2), "WALL", "B_W1"), ((7.5, 3.5), (7.5, 5), "WALL", "B_W2"),
          ((7.5, 2), (7.5, 3.5), "WINDOW_THRESHOLD", "THR|W-1|0")]
    s += [((7.7, 0.2), (14.8, 0.2), "WALL", "b_s"), ((14.8, 0.2), (14.8, 4.8), "WALL", "b_e"),
          ((7.7, 4.8), (14.8, 4.8), "WALL", "b_n"), ((7.7, 0.2), (7.7, 2), "WALL", "b_w1"),
          ((7.7, 3.5), (7.7, 4.8), "WALL", "b_w2"), ((7.7, 2), (7.7, 3.5), "WINDOW_THRESHOLD", "THR|W-1|1"),
          ((7.5, 2), (7.7, 2), "WALL", "jw1"), ((7.5, 3.5), (7.7, 3.5), "WALL", "jw2")]
    # the census thresholds across the strip (PASSAGE: no door, no glazing)
    s += [((6, 5), (7.5, 5), "PASSAGE_THRESHOLD", "THR|OP-N|1"), ((6, 4.8), (7.5, 4.8), "PASSAGE_THRESHOLD",
                                                                    "THR|OP-N|0"),
          ((6, 0), (7.5, 0), "PASSAGE_THRESHOLD", "THR|OP-S|0"), ((6, 0.2), (7.5, 0.2), "PASSAGE_THRESHOLD",
                                                                  "THR|OP-S|1")]
    return s


BOUNDARY = [((6, 0), (7.5, 0), "BND"), ((6, 0.2), (7.5, 0.2), "BND")]
LABELS = [(3, 2.5), (11, 2.5)]
ROOF_ALL = [[(0, 0), (15, 0), (15, 5), (0, 5)]]
ROOF_BLOCKS = [[(0, 0), (6, 0), (6, 5), (0, 5)], [(7.5, 0), (15, 0), (15, 5), (7.5, 5)]]
ROOF_HALF = [[(0, 2.5), (15, 2.5), (15, 5), (0, 5)]]


def xf(p, rot=0.0, mirror=False, scale=1.0):
    x, y = p
    if mirror:
        x = -x
    c, s = math.cos(math.radians(rot)), math.sin(math.radians(rot))
    return ((c * x - s * y) * scale, (s * x + c * y) * scale)


def setup(rot=0.0, mirror=False, scale=1.0, unit_m=1.0, segs=None):
    segs = plan() if segs is None else segs
    items = [TP.BoundaryItem(src, "SEGMENT", xf(a, rot, mirror, scale) + xf(b, rot, mirror, scale), role)
             for a, b, role, src in segs]
    arr = TP.build(items, 1e-6 * scale)
    fac = V29.facade_outlines(arr, unit_m, 1.0)
    k = min((k for k, f in enumerate(arr.faces) if f["area"] <= 0 and f["cycle"]), key=lambda k: arr.faces[k]["area"])
    ring = P.ring_with_inner(arr, k, unit_m)
    faces = P.faces_from_arrangement(arr, unit_m)
    tr = lambda p: list(xf(p, rot, mirror, 1.0))                                  # noqa: E731  (metres)
    return fac, ring, faces, tr


def lines(spec, tr):
    return [{"a": tr(a), "b": tr(b), "layer": lay} for a, b, lay in spec]


def polys(spec, tr):
    return [[tr(p) for p in poly] for poly in spec]


VARIANTS = [(0, False, 1.0, 1.0), (30, False, 1.0, 1.0), (-121, True, 1.0, 1.0), (0, False, 1000.0, 0.001),
            (30, True, 1000.0, 0.001)]


# ---------------------------------------------------------------------------------------- the engine bridges it
@pytest.mark.parametrize("rot,mirror,scale,unit_m", VARIANTS)
def test_engine_walks_across_the_strip(rot, mirror, scale, unit_m):
    fac, ring, faces, tr = setup(rot, mirror, scale, unit_m)
    assert fac["state"] == "ONE_OUTLINE"
    assert fac["outlines"][0]["perimeter_m"] == pytest.approx(40.00, abs=1e-5)
    ops = {o["opening_id"]: o["width_m"] for o in fac["outlines"][0]["openings"]}
    assert ops["OP-N"] == pytest.approx(1.50, abs=1e-6) and ops["OP-S"] == pytest.approx(1.50, abs=1e-6)


# ---------------------------------------------------------------------------------------- open-air dead end
@pytest.mark.parametrize("rot,mirror,scale,unit_m", VARIANTS)
def test_boundary_closed_passage_open_to_the_sky(rot, mirror, scale, unit_m):
    fac, ring, faces, tr = setup(rot, mirror, scale, unit_m)
    r = P.passage_walls(ring, faces, labels=[tr(p) for p in LABELS], above=polys(ROOF_BLOCKS, tr),
                        other_lines=lines(BOUNDARY, tr))
    assert r["state"] == "RESOLVED"
    assert r["walked_m"] == pytest.approx(40.00, abs=1e-5)
    assert r["run_m"] == pytest.approx(46.60, abs=1e-5)
    assert r["not_building_openings"] == ["OP-N", "OP-S"]
    (p,) = r["passages"]
    assert p["state"] == "OPEN_AIR" and "OPEN_TO_THE_SKY" in p["why"]
    cls = {m["opening_id"]: m["cls"] for m in p["mouths"]}
    assert cls == {"OP-N": "OPEN_MOUTH", "OP-S": "CLOSED_BY_ELEMENT"}
    elem = next(m for m in p["mouths"] if m["opening_id"] == "OP-S")
    assert elem["element_t_m"] == pytest.approx(0.20, abs=1e-6) and elem["element_layer"] == "BND"
    assert p["walls_m"] == pytest.approx(9.60, abs=1e-5)
    assert p["mouths_m"] == pytest.approx(3.00, abs=1e-6)
    assert p["delta_m"] == pytest.approx(6.60, abs=1e-5)
    assert p["element_inner_face_m"] == pytest.approx(1.50, abs=1e-6)
    assert p["space_area_m2"] == pytest.approx(7.20, abs=1e-5)
    assert p["covered_m2"] == pytest.approx(0.0, abs=1e-6) and p["open_sky_m2"] == pytest.approx(7.20, abs=1e-5)
    assert p["openings_onto"] == ["D-1", "W-1"]


def test_partly_roofed_passage_is_still_open_air_and_lists_the_cover():
    fac, ring, faces, tr = setup()
    r = P.passage_walls(ring, faces, labels=LABELS, above=ROOF_HALF, other_lines=lines(BOUNDARY, tr))
    (p,) = r["passages"]
    assert p["state"] == "OPEN_AIR" and r["run_m"] == pytest.approx(46.60, abs=1e-5)
    assert p["covered_m2"] == pytest.approx(1.50 * 2.50, abs=1e-5)           # y 2.50 .. 5.00 under the plate
    assert p["open_sky_m2"] == pytest.approx(1.50 * 2.30, abs=1e-5)          # y 0.20 .. 2.50
    assert p["covered_walls_m"] == pytest.approx(2 * 2.50, abs=1e-5)


# ---------------------------------------------------------------------------------------- roofed, one open mouth
def test_fully_roofed_dead_end_is_held_with_both_runs():
    fac, ring, faces, tr = setup()
    r = P.passage_walls(ring, faces, labels=LABELS, above=ROOF_ALL, other_lines=lines(BOUNDARY, tr))
    assert r["state"] == "HELD_RANGE"
    assert r["range_m"] == [pytest.approx(40.00, abs=1e-5), pytest.approx(46.60, abs=1e-5)]
    assert r["run_m"] == pytest.approx(40.00, abs=1e-5)                  # nothing applied while held
    assert r["not_building_openings"] == []
    assert "COVERED_ONE_MOUTH" in r["passages"][0]["why"]


def test_roof_not_read_holds_a_dead_end():
    fac, ring, faces, tr = setup()
    r = P.passage_walls(ring, faces, labels=LABELS, above=None, other_lines=lines(BOUNDARY, tr))
    assert r["state"] == "HELD_RANGE" and "ROOF_NOT_READ" in r["passages"][0]["why"]
    assert r["range_m"] == [pytest.approx(40.00, abs=1e-5), pytest.approx(46.60, abs=1e-5)]


# ---------------------------------------------------------------------------------------- open at both ends
@pytest.mark.parametrize("above", [None, ROOF_ALL])
@pytest.mark.parametrize("rot,mirror,scale,unit_m", [(0, False, 1.0, 1.0), (30, True, 1000.0, 0.001)])
def test_through_passage_is_outside_air_roofed_or_not(above, rot, mirror, scale, unit_m):
    fac, ring, faces, tr = setup(rot, mirror, scale, unit_m)
    r = P.passage_walls(ring, faces, labels=[tr(p) for p in LABELS], above=polys(above, tr) if above else None,
                        other_lines=[])
    assert r["state"] == "RESOLVED"
    assert r["run_m"] == pytest.approx(47.00, abs=1e-5)
    (p,) = r["passages"]
    assert p["state"] == "OPEN_AIR" and "OPEN_AT_TWO_ENDS" in p["why"]
    assert p["walls_m"] == pytest.approx(10.00, abs=1e-5) and p["space_area_m2"] == pytest.approx(7.50, abs=1e-5)


# ---------------------------------------------------------------------------------------- what stays as it is
def test_labelled_space_behind_a_doorless_opening_is_kept():
    fac, ring, faces, tr = setup()
    r = P.passage_walls(ring, faces, labels=LABELS + [(6.75, 2.5)], above=ROOF_BLOCKS,
                        other_lines=lines(BOUNDARY, tr))
    assert r["state"] == "RESOLVED" and r["run_m"] == pytest.approx(40.00, abs=1e-5)
    assert r["passages"][0]["state"] == "KEPT" and r["not_building_openings"] == []


def test_single_line_across_a_mouth_is_held():
    fac, ring, faces, tr = setup()
    r = P.passage_walls(ring, faces, labels=LABELS, above=ROOF_BLOCKS, other_lines=lines(BOUNDARY[:1], tr))
    assert r["state"] == "HELD_RANGE"
    assert {m["opening_id"]: m["cls"] for m in r["passages"][0]["mouths"]}["OP-S"] == "HELD_LINE_ONLY"


def test_lines_not_read_hold_without_a_number():
    fac, ring, faces, tr = setup()
    r = P.passage_walls(ring, faces, labels=LABELS, above=ROOF_BLOCKS, other_lines=None)
    assert r["state"] == "HELD_RANGE" and r["range_m"] == "NOT_ESTABLISHED"
    assert r["passages"][0]["delta_m"] is None and r["run_m"] == pytest.approx(40.00, abs=1e-5)


def test_no_passage_on_the_outline():
    segs = [s for s in plan() if not s[3].startswith("THR|OP-")]
    segs += [((6, 5), (7.5, 5), "WALL", "fill_n"), ((6, 0), (7.5, 0), "WALL", "fill_s")]
    fac, ring, faces, tr = setup(segs=segs)
    r = P.passage_walls(ring, faces, labels=LABELS, above=ROOF_BLOCKS, other_lines=[])
    assert r["state"] == "NO_PASSAGE" and r["run_m"] == r["walked_m"] == pytest.approx(40.00, abs=1e-5)


def test_empty_outline_is_no_outline_not_zero():
    r = P.passage_walls([], {})
    assert r["state"] == "NO_OUTLINE" and r["walked_m"] is None and r["run_m"] is None


# ---------------------------------------------------------------------------------------- a wall-end drafting gap
def test_threshold_over_a_wall_end_is_kept_as_wall_face():
    """Block A's south face line stops 0.20 m short of its corner (x 5.80) and a cap closes the wall end there; the
    census threshold of the south mouth then runs 5.80 .. 7.50 (1.70 m). The 0.20 m over the wall end is the wall's
    outer face, kept in the run; only the 1.50 m across the strip is the mouth. Hand: 46.60 m as before."""
    segs = [s for s in plan() if s[3] not in ("A_S", "THR|OP-S|0", "a_s")]
    segs += [((0, 0), (5.8, 0), "WALL", "A_S'"), ((5.8, 0), (7.5, 0), "PASSAGE_THRESHOLD", "THR|OP-S|0"),
             ((5.8, 0), (5.8, 0.2), "WALL_CAP", "CAP|A"), ((0.2, 0.2), (5.8, 0.2), "WALL", "a_s'")]
    fac, ring, faces, tr = setup(segs=segs)
    assert fac["outlines"][0]["perimeter_m"] == pytest.approx(40.00, abs=1e-5)
    r = P.passage_walls(ring, faces, labels=LABELS, above=ROOF_BLOCKS, other_lines=lines(BOUNDARY, tr))
    assert r["run_m"] == pytest.approx(46.60, abs=1e-5)
    (g,) = r["wall_end_gaps"]
    assert g["opening_id"] == "OP-S" and g["len_m"] == pytest.approx(0.20, abs=1e-6)
