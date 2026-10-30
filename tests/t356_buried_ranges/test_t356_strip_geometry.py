"""T-356 strap-strip geometry on villa T356-X (hand values in test_t356_rules.py): normal, rotated, mirrored, skewed.

Pads P1 0.00 .. 1.60 and P2 5.00 .. 6.60 (y -0.80 .. 0.80); strap edges y = -0.25 / +0.25 from x 0.80 to 5.80 (drawn
into both pads, as the development villa's strap lines are). Hand: own (0.50 + 0.20) x 3.40 = 2.380 m2, pads' blinding
band 2 x 0.10 x 0.70 = 0.140, merged 2.240 m2.
"""

import math
import sys
from pathlib import Path

import pytest

shapely = pytest.importorskip("shapely")
from shapely import affinity  # noqa: E402
from shapely.geometry import LineString, box  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t356"))
import t356_extract as X  # noqa: E402

A = pytest.approx


def _villa():
    pads = [box(0.0, -0.8, 1.6, 0.8), box(5.0, -0.8, 6.6, 0.8)]
    e1 = LineString([(0.8, -0.25), (5.8, -0.25)])
    e2 = LineString([(0.8, 0.25), (5.8, 0.25)])
    plot = box(-10, -10, 20, 10)
    return e1, e2, pads, plot


def _run(tf):
    e1, e2, pads, plot = _villa()
    g = [tf(e1), tf(e2), [tf(p) for p in pads], tf(plot)]
    return X.strap_strip(g[0], g[1], g[2], g[3], 0.10)


def test_normal_by_hand():
    own, out, band, merged = _run(lambda g: g)
    assert (own, out, band, merged) == (A(2.38), A(0.0), A(0.14), A(2.24))


@pytest.mark.parametrize("deg", [37.0, 90.0, 213.5])
def test_rotation_invariant(deg):
    own, out, band, merged = _run(lambda g: affinity.rotate(g, deg, origin=(0, 0)))
    assert (own, band, merged) == (A(2.38), A(0.14), A(2.24))


def test_mirror_invariant():
    own, out, band, merged = _run(lambda g: affinity.scale(g, -1.0, 1.0, origin=(0, 0)))
    assert (own, band, merged) == (A(2.38), A(0.14), A(2.24))


def test_adverse_strip_past_the_plot_is_not_own():
    e1, e2, pads, _ = _villa()
    own, out, band, merged = X.strap_strip(e1, e2, pads, box(-10, -0.30, 20, 10), 0.10)   # plot edge 0.05 below the strap
    assert out == A(0.05 * 3.40) and own == A(2.38 - 0.17)


def test_skewed_strap_between_parallel_faces_is_width_times_axis():
    # a strap at 30 deg to two parallel pad faces: the strip is a parallelogram, (B + 0.20) x axis clear length
    pads = [box(0.0, -5.0, 1.6, 5.0), box(5.0, -5.0, 6.6, 5.0)]
    a = math.radians(30.0)
    off = 0.25 / math.cos(a)
    e1 = LineString([(0.8, -off), (5.8, -off + 5.0 * math.tan(a))])
    e2 = LineString([(0.8, off), (5.8, off + 5.0 * math.tan(a))])
    own, out, band, merged = X.strap_strip(e1, e2, pads, box(-10, -10, 20, 10), 0.10)
    assert own == A(0.70 * 3.40 / math.cos(a))
    assert band == A(2 * 0.10 * 0.70 / math.cos(a))     # the pads' 0.10 band, cut obliquely
    assert merged == A(own - band)
