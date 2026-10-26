"""T-255 rule R-ARC-BAND-END-1 on a hand-calculated NON-Alsenan villa (K255), normal and adverse.

Villa K255 (hand calculation, metres; arc centre O = (0, 0)):
  ring ground beam between the inner arc r = 2.00 and the outer arc R = 2.30 (width 0.30), running west from north to
  south, printed depth D = 0.80.
  NORTH end: the outer arc ends ON the face y = 2.20 of a straight ground beam (band y 2.20 .. 2.50, x -4.00 .. 0.00);
      that face stops at the west face x = 0 of column C1 (x 0 .. 0.30, y 2.00 .. 2.30); the inner arc starts at C1's
      south-west corner (0, 2.00). Outer arc end P = (-sqrt(2.30^2 - 2.20^2), 2.20) = (-0.670820, 2.20).
  SOUTH end: both arcs end on the west face x = 0 of column C2 (x 0 .. 0.30, y -2.30 .. -2.00).
  CROWN: column C3 0.20 x 0.20 (x -2.25 .. -2.05, y -0.10 .. 0.10) stands wholly in the band: deducted.

  beta = asin(0.670820 / 2.30) = 0.295963 rad
  gross (Green, about O): 1/2 R^2 (pi - beta) + 1/2 x 0.670820 x 2.20 - 1/2 r^2 pi
        = 7.526691 + 0.737902 - 6.283185 = 1.981408 m2
  closing triangle P (-0.670820, 2.20) / Q (0, 2.20) / R (0, 2.00) = 1/2 x 0.670820 x 0.20 = 0.067082 m2
  net by drawn faces = 1.981408 - C3 0.040000 = 1.941408 m2 -> x D 0.80 = 1.553126 m3
  chord-closed reading (P -> R straight) = 1.874326 m2 (the triangle left out): retired; drawn = chord + 0.067082
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import arch_v3019 as A  # noqa: E402

R_OUT, R_IN, Y_FACE, D = 2.30, 2.00, 2.20, 0.80
XP = math.sqrt(R_OUT ** 2 - Y_FACE ** 2)
GROSS, TRI, COL3 = 1.981408, 0.067082, 0.04
NET = GROSS - COL3                       # 1.941408
CHORD_NET = NET - TRI                    # 1.874326
N = 20000


def _arc(r, t0, t1, n=N):
    return [(r * math.cos(t0 + (t1 - t0) * i / n), r * math.sin(t0 + (t1 - t0) * i / n)) for i in range(n + 1)]


def band(closing="DRAWN"):
    """the band outline: outer arc from P anticlockwise to 270 deg, the C2 face, the inner arc back to 90 deg, then the
    north closure (drawn: up C1's west face to Q and along the beam face to P; chord: straight back to P)."""
    tp = math.pi / 2 + math.asin(XP / R_OUT)
    outer = _arc(R_OUT, tp, 1.5 * math.pi)
    inner = _arc(R_IN, 1.5 * math.pi, 0.5 * math.pi)
    ring = outer + inner
    if closing == "DRAWN":
        ring += [(0.0, Y_FACE)]
    return ring


C1 = {"id": "C1", "ring": [(0, 2.0), (0.3, 2.0), (0.3, 2.3), (0, 2.3)], "deducted": True}
C2 = {"id": "C2", "ring": [(0, -2.3), (0.3, -2.3), (0.3, -2.0), (0, -2.0)], "deducted": True}
C3 = {"id": "C3", "ring": [(-2.25, -0.1), (-2.05, -0.1), (-2.05, 0.1), (-2.25, 0.1)], "deducted": True}
BEAM = {"line_id": "L-K-STRAIGHT", "ring": [(-4.0, 2.2), (0.0, 2.2), (0.0, 2.5), (-4.0, 2.5)]}


def test_hand_figures_are_the_formula():
    beta = math.asin(XP / R_OUT)
    g = 0.5 * R_OUT ** 2 * (math.pi - beta) + 0.5 * XP * Y_FACE - 0.5 * R_IN ** 2 * math.pi
    assert g == pytest.approx(GROSS, abs=1e-6)
    assert 0.5 * XP * (Y_FACE - R_IN) == pytest.approx(TRI, abs=1e-6)


def test_normal_drawn_faces_triangle_once_column_deducted():
    got = A.arc_band_net(band(), [C1, C2, C3], [BEAM])
    assert got["gross_m2"] == pytest.approx(GROSS, abs=2e-5)
    assert set(got["columns_m2"]) == {"C3"}           # C1 / C2 close the ends: outside the band, nothing to deduct
    assert got["columns_m2"]["C3"] == pytest.approx(COL3, abs=1e-9)
    assert got["net_m2"] == pytest.approx(NET, abs=2e-5)
    assert got["net_m2"] * D == pytest.approx(1.553126, abs=2e-5)


def test_chord_reading_is_short_by_the_triangle_exactly():
    drawn = A.arc_band_net(band(), [C1, C2, C3], [BEAM])["net_m2"]
    chord = A.arc_band_net(band("CHORD"), [C1, C2, C3], [BEAM])["net_m2"]
    assert chord == pytest.approx(CHORD_NET, abs=2e-5)
    assert drawn - chord == pytest.approx(TRI, abs=2e-5)


def test_mirror_and_rotation_do_not_change_the_area():
    def rot(ring, t):
        c, s = math.cos(t), math.sin(t)
        return [(c * x - s * y, s * x + c * y) for x, y in ring]
    mir = lambda ring: [(-x, y) for x, y in ring]  # noqa: E731
    for f in (lambda g: rot(g, 0.7), mir):
        cols = [dict(c, ring=f(c["ring"])) for c in (C1, C2, C3)]
        got = A.arc_band_net(f(band()), cols, [dict(BEAM, ring=f(BEAM["ring"]))])
        assert got["net_m2"] == pytest.approx(NET, abs=2e-5)


def test_units_millimetres_scale_by_a_million():
    mm = lambda ring: [(1000 * x, 1000 * y) for x, y in ring]  # noqa: E731
    got = A.arc_band_net(mm(band()), [dict(C3, ring=mm(C3["ring"]))], tol_m2=1.0)
    assert got["net_m2"] / 1e6 == pytest.approx(NET, abs=2e-5)    # an mm drawing is never read as m2


def test_adverse_chord_or_span_end_refused_where_a_drawn_face_closes_it():
    for reading in ("CHORD", "ARC_SPAN"):
        with pytest.raises(A.InputsError, match="refused: drawn faces"):
            A.check_end_reading(reading, ["beam face", "C1 west", "C1 south"])
    A.check_end_reading("DRAWN_FACES", ["C2 west"])


def test_adverse_end_with_no_drawn_face_is_held_never_a_convention():
    for reading in ("DRAWN_FACES", "CHORD"):
        with pytest.raises(A.InputsError, match="not established"):
            A.check_end_reading(reading, [])


def test_adverse_triangle_in_ring_and_straight_beam_refused():
    greedy = dict(BEAM, ring=[(-4.0, 2.0), (0.0, 2.0), (0.0, 2.5), (-4.0, 2.5)])   # beam drawn down to the chord
    with pytest.raises(A.InputsError, match="two lines"):
        A.arc_band_net(band(), [C1, C2, C3], [greedy])


def test_adverse_column_in_the_band_left_in_refused():
    with pytest.raises(A.InputsError, match="not deducted"):
        A.arc_band_net(band(), [C1, C2, dict(C3, deducted=False)], [BEAM])


def test_adverse_missing_outline_refused():
    with pytest.raises(A.InputsError, match="valid closed outline"):
        A.arc_band_net([(0, 0), (1, 0)])


def test_stdlib_clip_agrees_with_an_independent_geometry_library():
    shapely = pytest.importorskip("shapely.geometry")
    b = shapely.Polygon(band())
    got = A.arc_band_net(band(), [C1, C2, C3], [BEAM])
    assert got["gross_m2"] == pytest.approx(b.area, abs=1e-9)
    assert got["columns_m2"]["C3"] == pytest.approx(b.intersection(shapely.Polygon(C3["ring"])).area, abs=1e-9)
    tilted = {"id": "C4", "ring": [(-2.35, 0.55), (-2.0, 0.40), (-1.9, 0.65), (-2.25, 0.80)], "deducted": True}
    part = A.arc_band_net(band(), [tilted])["columns_m2"]["C4"]          # a column across the outer arc, rotated
    assert part == pytest.approx(b.intersection(shapely.Polygon(tilted["ring"])).area, abs=1e-6)


def test_adverse_concave_neighbour_outline_refused():
    ell = dict(BEAM, ring=[(-4.0, 2.2), (0.0, 2.2), (0.0, 2.5), (-2.0, 2.5), (-2.0, 3.5), (-4.0, 3.5)])
    with pytest.raises(A.InputsError, match="not convex"):
        A.arc_band_net(band(), [C1, C2, C3], [ell])
