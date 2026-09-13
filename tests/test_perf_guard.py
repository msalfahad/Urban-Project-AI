"""A guard against reintroducing whole-sheet work inside a per-pixel loop.

E25's internal/external march reads one pixel at a time, up to ~55 times per
segment. It used to read that pixel by np.roll-ing the entire label map twice.
On the 13x9 arrays the unit tests use that is free; on a 3509x4963 architectural
sheet it turned a two-minute run into hours, and no test noticed.

The exact runtime is not pinned — machines differ and that would be a flaky
test. What is pinned is the shape of the code and the scaling behaviour: a
lookup must not copy the sheet, and doubling the array must not multiply the
work by the number of pixels.
"""

from __future__ import annotations

import inspect
import time
from decimal import Decimal as D

import numpy as np
import pytest

from engine import walls
from engine.walls import space_walls


def sheet(h: int, w: int):
    """A room in the middle of an otherwise solid sheet."""
    lab = np.zeros((h, w), np.int32)
    lab[h // 3: 2 * h // 3, w // 3: 2 * w // 3] = 2
    lab[0, :] = 1; lab[-1, :] = 1; lab[:, 0] = 1; lab[:, -1] = 1
    wall = ~(lab > 0)
    return lab, wall


def trace(h: int, w: int) -> float:
    lab, wall = sheet(h, w)
    t0 = time.perf_counter()
    space_walls("RM", lab, 2, wall, np.zeros_like(wall), D("10"),
                outside_id={1}, id_to_space={2: "RM"}, max_opening_mm=0)
    return time.perf_counter() - t0


def test_the_march_does_not_copy_the_sheet_to_read_one_pixel():
    """The structural guard: peek() indexes, look() rolls."""
    src = inspect.getsource(space_walls)
    march = src[src.index("march past the wall body"):]
    assert "peek(labels" in march
    assert "look(labels" not in march and "look(wall" not in march


def test_peek_reads_a_single_cell_rather_than_building_an_array():
    src = inspect.getsource(space_walls)
    body = src[src.index("def peek("):src.index("edge = R & ~look(R)")]
    # the call, not the word: peek's docstring explains why it does not roll
    assert "np.roll(" not in body
    assert "return arr[y, x]" in body


@pytest.mark.slow
def test_quadrupling_the_pixels_does_not_multiply_the_work_by_the_pixels():
    """A 2x larger sheet in each dimension is 4x the pixels. With a whole-array
    copy per lookup the cost went up far faster than that; indexed lookups keep
    it roughly proportional. The bound is loose on purpose — this catches a
    return to O(pixels) per lookup, not a 30% regression."""
    small = trace(400, 560)
    large = trace(800, 1120)
    assert large < small * 12, (
        f"{small:.3f}s -> {large:.3f}s for 4x the pixels: the march looks like it "
        "is doing whole-sheet work per lookup again")


def test_the_march_never_wraps_around_the_sheet():
    """np.roll wrapped, so a march off the edge reappeared on the far side and
    reported whatever room happened to sit there."""
    src = inspect.getsource(space_walls)
    body = src[src.index("def peek("):src.index("edge = R & ~look(R)")]
    assert "% h]" not in body and "% w]" not in body
    assert "return None" in body
