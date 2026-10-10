"""E23F — the transform between vector and raster frames, measured not assumed."""

from __future__ import annotations

import numpy as np
import pytest

from engine.frames import (IDENTITY, MIN_ACCEPTABLE_FIT, SWAP_FLIP_Y, Frame,
                           FrameError, fit)
from engine.vector_source import STROKE, VectorSegment


def seg(sid, x0, y0, x1, y1):
    return VectorSegment(sid, "VP-1", 0, "H", y0, x0, x1, STROKE, 1.14, False,
                         0.0, x0, y0, x1, y1)


def test_a_flip_is_not_the_same_as_a_swap():
    """The inline comment said the axes swap. They swap AND flip, and half
    right in a transform means mirrored."""
    f = Frame(SWAP_FLIP_Y, 1000.0, 800.0)
    assert f.to_raster(100.0, 200.0) == (200.0, 700.0)
    assert Frame("SWAP", 1000.0, 800.0).to_raster(100.0, 200.0) == (200.0, 100.0)


def test_the_transform_round_trips():
    for name in (IDENTITY, SWAP_FLIP_Y, "SWAP", "ROT90", "ROT180", "ROT270",
                 "SWAP_FLIP_X", "SWAP_FLIP_BOTH"):
        f = Frame(name, 1000.0, 800.0)
        x, y = 123.0, 456.0
        rx, ry = f.to_raster(x, y)
        bx, by = f.to_vector(rx, ry)
        assert (round(bx, 6), round(by, 6)) == (x, y), name


def test_a_bbox_is_reordered_after_a_flip():
    """Mapping corners without re-ordering produces an inverted box that
    silently overlaps nothing."""
    f = Frame(SWAP_FLIP_Y, 1000.0, 800.0)
    x0, y0, x1, y1 = f.bbox_to_vector((100.0, 200.0, 300.0, 400.0))
    assert x0 < x1 and y0 < y1


def test_a_frame_is_measured_against_the_wall_mask():
    # ASYMMETRIC on purpose: a wall across the middle fits a swap and a
    # swap+flip equally, and the fitter would rightly refuse to choose.
    # ASYMMETRIC IN BOTH AXES on purpose. A wall across the middle fits a swap
    # and a swap+flip equally, and the fitter would rightly refuse to choose —
    # so the fixture has to break the symmetry the way a real plan does.
    mask = np.zeros((80, 100), bool)
    mask[20, 10:40] = True            # raster row 20 of 80, columns 10..40
    px = 10.0
    # SWAP_FLIP_Y maps (x, y) -> (y, h - x) with h = 800. Raster row 20 is
    # ry = 200, so x = 600; raster columns 100..400 are y = 100..400.
    segs = [VectorSegment("A", "VP", 0, "V", 600.0, 120.0, 380.0, STROKE,
                          1.14, False, 0.0, 600.0, 120.0, 600.0, 380.0)]
    f = fit(segs, mask, px)
    assert f.name == SWAP_FLIP_Y
    assert f.fit >= MIN_ACCEPTABLE_FIT


def test_a_frame_that_does_not_fit_is_refused_rather_than_picked():
    """Below the threshold this is a coincidence, not a transform, and using
    it would mirror every comparison."""
    mask = np.zeros((80, 100), bool)
    segs = [seg("A", 0.0, 0.0, 100.0, 0.0)]
    with pytest.raises(FrameError):
        fit(segs, mask, 10.0)


def test_fitting_with_nothing_to_fit_is_refused():
    with pytest.raises(FrameError, match="no segments"):
        fit([], np.zeros((10, 10), bool), 10.0)
