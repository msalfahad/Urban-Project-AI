"""Axis-aligned geometry primitives, and the few relations the engine reasons about.

Everything is exact arithmetic on floats that came from a drawing, so comparisons take an explicit tolerance and
never a hidden one.  A tolerance is a property of the source (how finely the drawing was authored), which is why
it is always passed in rather than chosen here.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

AXIS_X = "X"        # a run parallel to the x axis
AXIS_Y = "Y"


@dataclass(frozen=True)
class Rect:
    x0: float
    y0: float
    x1: float
    y1: float

    def __post_init__(self):
        if self.x1 < self.x0 or self.y1 < self.y0:
            raise ValueError(f"degenerate rectangle {self}")

    @property
    def width(self):
        return self.x1 - self.x0

    @property
    def height(self):
        return self.y1 - self.y0

    @property
    def area(self):
        return self.width * self.height

    @property
    def centroid(self):
        return ((self.x0 + self.x1) / 2.0, (self.y0 + self.y1) / 2.0)

    def contains_point(self, x, y, tol=0.0):
        return (self.x0 - tol <= x <= self.x1 + tol) and (self.y0 - tol <= y <= self.y1 + tol)

    def intersection(self, other):
        x0, y0 = max(self.x0, other.x0), max(self.y0, other.y0)
        x1, y1 = min(self.x1, other.x1), min(self.y1, other.y1)
        return Rect(x0, y0, x1, y1) if x1 > x0 and y1 > y0 else None

    def overlaps(self, other, tol=0.0):
        return (min(self.x1, other.x1) - max(self.x0, other.x0) > -tol
                and min(self.y1, other.y1) - max(self.y0, other.y0) > -tol)

    def expanded(self, tol):
        return Rect(self.x0 - tol, self.y0 - tol, self.x1 + tol, self.y1 + tol)

    def as_tuple(self, places=6):
        return (round(self.x0, places), round(self.y0, places), round(self.x1, places), round(self.y1, places))


def bbox(rects):
    return Rect(min(r.x0 for r in rects), min(r.y0 for r in rects),
                max(r.x1 for r in rects), max(r.y1 for r in rects))


def total_area(rects):
    """Exact area of a set of rectangles that do not overlap; the caller owns that guarantee."""
    return sum(r.area for r in rects)


def centroid(rects):
    a = total_area(rects)
    if a <= 0:
        b = bbox(rects)
        return b.centroid
    cx = sum(r.centroid[0] * r.area for r in rects) / a
    cy = sum(r.centroid[1] * r.area for r in rects) / a
    return (cx, cy)


def intersection_area(a_rects, b_rects):
    total = 0.0
    for a in a_rects:
        for b in b_rects:
            i = a.intersection(b)
            if i:
                total += i.area
    return total


def iou(a_rects, b_rects):
    """Intersection over union, the usual measure of "is this the same object, moved a little"."""
    inter = intersection_area(a_rects, b_rects)
    union = total_area(a_rects) + total_area(b_rects) - inter
    return inter / union if union > 0 else 0.0


def shared_edge(a_rects, b_rects, tol):
    """Where two rectangle sets touch without overlapping: the axis, the coordinate, and the shared interval.

    Returns a list of (axis, position, lo, hi) - the seam an engine has to ask a question about, because a seam
    is where two components either continue into one another or are separated by something physical.
    """
    seams = []
    for a in a_rects:
        for b in b_rects:
            # vertical seam: a's right face touches b's left face (or the reverse)
            for pa, pb in ((a.x1, b.x0), (b.x1, a.x0)):
                if abs(pa - pb) <= tol:
                    lo, hi = max(a.y0, b.y0), min(a.y1, b.y1)
                    if hi - lo > tol:
                        seams.append((AXIS_Y, (pa + pb) / 2.0, lo, hi))
            for pa, pb in ((a.y1, b.y0), (b.y1, a.y0)):
                if abs(pa - pb) <= tol:
                    lo, hi = max(a.x0, b.x0), min(a.x1, b.x1)
                    if hi - lo > tol:
                        seams.append((AXIS_X, (pa + pb) / 2.0, lo, hi))
    return _merge_seams(seams, tol)


def _merge_seams(seams, tol):
    by_line = {}
    for axis, pos, lo, hi in seams:
        by_line.setdefault((axis, round(pos / max(tol, 1e-9))), []).append((pos, lo, hi))
    out = []
    for (axis, _k), spans in sorted(by_line.items(), key=lambda kv: (kv[0][0], kv[0][1])):
        pos = sum(s[0] for s in spans) / len(spans)
        merged = []
        for lo, hi in sorted((s[1], s[2]) for s in spans):
            if merged and lo <= merged[-1][1] + tol:
                merged[-1][1] = max(merged[-1][1], hi)
            else:
                merged.append([lo, hi])
        out.extend((axis, pos, lo, hi) for lo, hi in merged)
    return out


def seam_length(seams):
    return sum(hi - lo for _axis, _pos, lo, hi in seams)


def distance_point_to_rect(x, y, r):
    dx = max(r.x0 - x, 0.0, x - r.x1)
    dy = max(r.y0 - y, 0.0, y - r.y1)
    return math.hypot(dx, dy)
