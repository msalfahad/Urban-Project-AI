"""The rasteriser must stay exact AND affordable.

Both properties were broken in this round and both are worth a test: a
per-pixel predicate over a union component's bounding box cost minutes, and
a per-row scanline that replaced it was both slow (97 s for one component)
and WRONG (68 108 pixels where 75 512 was correct).
"""

import time

import numpy as np
from shapely.geometry import box
from shapely.ops import unary_union

from engine import raster_topology as rt
from engine.frames import SWAP_FLIP_Y, Frame

PX = 10.813
SHAPE = (3509, 4963)


def _frame():
    return Frame(SWAP_FLIP_Y, raster_w_mm=SHAPE[1] * PX,
                 raster_h_mm=SHAPE[0] * PX, fit=1.0)


def test_a_rectangle_rasterises_exactly():
    m = rt._rasterise(box(5000, 5000, 5200, 25000), _frame(), PX, SHAPE)
    assert m.sum() > 0
    # 200 mm x 20 000 mm at 10.813 mm/px is ~18.5 x 1850 px.
    assert 30000 < int(m.sum()) < 45000


def test_a_union_component_equals_the_union_of_its_parts():
    """The correctness bug the scanline had."""
    a, b = box(5000, 5000, 25000, 5200), box(24800, 5000, 25000, 25000)
    f = _frame()
    joined = rt._rasterise(unary_union([a, b]), f, PX, SHAPE)
    apart = (rt._rasterise(a, f, PX, SHAPE) | rt._rasterise(b, f, PX, SHAPE))
    assert (joined == apart).all()


def test_a_comb_shaped_component_is_affordable():
    """A wall solid's components are combs. This must not take minutes."""
    comb = unary_union(
        [box(5000 + i * 400, 5000, 5000 + i * 400 + 200, 15000)
         for i in range(30)]
        + [box(5000, 4800, 17000, 5000)])
    t = time.time()
    m = rt._rasterise(comb, _frame(), PX, SHAPE)
    elapsed = time.time() - t
    assert m.sum() > 0
    assert elapsed < 2.0, f"took {elapsed:.1f}s — the per-pixel path is back"


def test_a_rectilinear_decomposition_covers_the_part():
    L = unary_union([box(0, 0, 100, 10), box(90, 0, 100, 100)])
    rects = rt._rect_decompose(L)
    assert rects
    covered = unary_union(rects)
    assert covered.area >= L.area - 1e-6
    assert all(r.equals(r.envelope) for r in rects)


def test_a_non_rectilinear_part_falls_back_to_its_envelope():
    """Too generous is safe for a barrier; too small is not."""
    from shapely.geometry import Polygon
    circle = Polygon([(0, 0), (100, 5), (200, 0), (150, 100), (50, 100)])
    rects = rt._rect_decompose(circle, max_slabs=2)
    assert len(rects) == 1
    assert rects[0].equals(circle.envelope)
