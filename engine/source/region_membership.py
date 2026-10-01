"""Exact region membership of a curve (R8.8): SEGMENT, ARC, CIRCLE, ELLIPTICAL_ARC against an axis-aligned region.

R8.7 judged a curve by a handful of SAMPLED points (an arc at five angles, an ellipse at five parameters). A curve whose
samples are all inside can still leave the region between them - the extremum of a 60-degree arc, the bulge of an
ellipse between two parameters - and was then kept as inside. Sampling cannot prove membership; this module does not
sample.

Method (analytic, no flattening)
    The region is a CLOSED box R = [x0, x1] x [y0, y1]. A curve C is
        FULLY_INSIDE       C is a subset of R (its exact bounding box lies in R);
        FULLY_OUTSIDE      C and R are disjoint (no point of C in R);
        CROSSES_BOUNDARY   otherwise (C has points both in and out of R, including a curve that only TOUCHES R
                           from outside: its intersection with R is not empty and not all of C);
        UNRESOLVED         the geometry is not finite or the kind is not supported.
    The exact bounding box of a circular or elliptical arc is its end points plus every axis extremum whose
    parameter lies inside the sweep: x(t) = cx + ux cos t + vx sin t has extrema where tan t = vx / ux (and the
    circle case is the special ux = r, vx = 0). Disjointness is decided by the same extrema plus the exact
    intersections of the curve with the four box edges (a cos t + b sin t = c solved in closed form).

Tangency (frozen, R8.8 policy RM-TANGENT-1)
    R is closed. A curve that touches the boundary from INSIDE is FULLY_INSIDE (no point of it leaves R). A curve
    that touches R only from OUTSIDE is CROSSES_BOUNDARY: it is not disjoint from R and not contained in it, so it
    is neither kept nor discarded silently - the occurrence goes to REVIEW_REQUIRED.

Numeric noise
    A curve that leaves R by no more than `eps` (the frozen numeric-representation tolerance of the topology
    tolerance policy, never a calibrated value) is treated as touching: noise of the representation cannot move a
    record across a region boundary, and nothing larger is swallowed.

Rotation / reflection
    Every test is on the realised WORLD geometry (after the insert transforms), so a rotated or mirrored occurrence
    gets the answer of its physical geometry.

Project-agnostic; stdlib only.
"""

from __future__ import annotations

import math

FULLY_INSIDE = "FULLY_INSIDE"
FULLY_OUTSIDE = "FULLY_OUTSIDE"
CROSSES_BOUNDARY = "CROSSES_BOUNDARY"
UNRESOLVED = "UNRESOLVED"
STATES = (FULLY_INSIDE, FULLY_OUTSIDE, CROSSES_BOUNDARY, UNRESOLVED)
TWO_PI = 2.0 * math.pi
POLICY = {
    "id": "RM-EXACT-1",
    "region": "closed axis-aligned box in world coordinates",
    "method": "exact bounding box (end points + in-sweep axis extrema) and exact edge intersections; no sampling, "
              "no flattening",
    "tangent_rule": "RM-TANGENT-1: touching from inside = FULLY_INSIDE; touching only from outside = "
                    "CROSSES_BOUNDARY (REVIEW_REQUIRED)",
    "noise": "a curve leaving the region by <= eps (numeric-representation tolerance) counts as touching",
    "states": list(STATES),
}


def _finite(*v) -> bool:
    return all(isinstance(x, (int, float)) and math.isfinite(x) for x in v)


def _in_sweep(t, t0, sweep) -> bool:
    """t lies on the CCW sweep from t0 of length sweep (radians)."""
    return ((t - t0) % TWO_PI) <= sweep + 1e-15


def _param_interval(t0, t1):
    """An elliptical arc's parameters form an INTERVAL (the realisers emit t1 = t0 +/- sweep): (start, sweep)."""
    lo, hi = min(t0, t1), max(t0, t1)
    sweep = hi - lo
    return lo, (TWO_PI if sweep <= 0.0 or sweep >= TWO_PI else sweep)


def _conic_point(c, u, v, t):
    return (c[0] + u[0] * math.cos(t) + v[0] * math.sin(t), c[1] + u[1] * math.cos(t) + v[1] * math.sin(t))


def _conic_bbox(c, u, v, t0, sweep):
    """Exact bounding box of point(t) = c + u cos t + v sin t, t in [t0, t0 + sweep]."""
    ts = [t0, t0 + sweep]
    for a, b in ((u[0], v[0]), (u[1], v[1])):
        if a == 0.0 and b == 0.0:
            continue
        t = math.atan2(b, a)                         # d/dt (a cos t + b sin t) = 0  <=>  tan t = b / a
        for cand in (t, t + math.pi):
            if _in_sweep(cand, t0, sweep):
                ts.append(cand)
    pts = [_conic_point(c, u, v, t) for t in ts]
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return min(xs), min(ys), max(xs), max(ys)


def _conic_hits_line(c, u, v, t0, sweep, axis, value, lo, hi, eps):
    """Does the conic arc meet the line {axis = value} with the other coordinate in [lo - eps, hi + eps]?"""
    a, b = (u[0], v[0]) if axis == 0 else (u[1], v[1])
    k = value - c[axis]
    rad = math.hypot(a, b)
    if rad == 0.0:
        return False
    q = k / rad
    if abs(q) > 1.0:
        return False
    phi = math.atan2(b, a)
    d = math.acos(max(-1.0, min(1.0, q)))
    other = 1 - axis
    for t in (phi + d, phi - d):
        if _in_sweep(t, t0, sweep):
            p = _conic_point(c, u, v, t)
            if lo - eps <= p[other] <= hi + eps:
                return True
    return False


def _segment_classify(a, b, box, eps):
    x0, y0, x1, y1 = box
    inside = [x0 - eps <= p[0] <= x1 + eps and y0 - eps <= p[1] <= y1 + eps for p in (a, b)]
    if all(inside):
        return FULLY_INSIDE
    if any(inside):
        return CROSSES_BOUNDARY
    # both ends outside: disjoint unless the segment passes through the box (Liang-Barsky)
    dx, dy = b[0] - a[0], b[1] - a[1]
    t0, t1 = 0.0, 1.0
    for p, q in ((-dx, a[0] - (x0 - eps)), (dx, (x1 + eps) - a[0]), (-dy, a[1] - (y0 - eps)), (dy, (y1 + eps) - a[1])):
        if p == 0.0:
            if q < 0.0:
                return FULLY_OUTSIDE
            continue
        r = q / p
        if p < 0.0:
            t0 = max(t0, r)
        else:
            t1 = min(t1, r)
        if t0 > t1:
            return FULLY_OUTSIDE
    return CROSSES_BOUNDARY


def _conic_classify(c, u, v, t0, sweep, box, eps):
    x0, y0, x1, y1 = box
    bx0, by0, bx1, by1 = _conic_bbox(c, u, v, t0, sweep)
    if bx0 >= x0 - eps and by0 >= y0 - eps and bx1 <= x1 + eps and by1 <= y1 + eps:
        return FULLY_INSIDE
    p_start = _conic_point(c, u, v, t0)
    if x0 - eps <= p_start[0] <= x1 + eps and y0 - eps <= p_start[1] <= y1 + eps:
        return CROSSES_BOUNDARY                       # one point in, the bbox says some point out
    for axis, value, lo, hi in ((0, x0, y0, y1), (0, x1, y0, y1), (1, y0, x0, x1), (1, y1, x0, x1)):
        for vv in (value - eps, value + eps) if eps else (value,):
            if _conic_hits_line(c, u, v, t0, sweep, axis, vv, lo, hi, eps):
                return CROSSES_BOUNDARY
    # no point on the box boundary and the start outside: the connected arc never enters the box
    return FULLY_OUTSIDE


def classify(kind: str, geometry: tuple, box, eps: float = 0.0) -> str:
    """Membership of one realised curve. geometry as CanonicalPart.geometry:
    SEGMENT (x1, y1, x2, y2); ARC (cx, cy, r, a0, a1) CCW radians; CIRCLE (cx, cy, r);
    ELLIPTICAL_ARC (cx, cy, ux, uy, vx, vy, t0, t1) with t increasing from t0 to t1."""
    if geometry is None or not _finite(*geometry) or not _finite(*box):
        return UNRESOLVED
    if kind == "SEGMENT":
        x1, y1, x2, y2 = geometry
        return _segment_classify((x1, y1), (x2, y2), box, eps)
    if kind == "ARC":
        cx, cy, r, a0, a1 = geometry
        sweep = (a1 - a0) % TWO_PI or TWO_PI
        return _conic_classify((cx, cy), (r, 0.0), (0.0, r), a0, sweep, box, eps)
    if kind == "CIRCLE":
        cx, cy, r = geometry
        return _conic_classify((cx, cy), (r, 0.0), (0.0, r), 0.0, TWO_PI, box, eps)
    if kind == "ELLIPTICAL_ARC":
        cx, cy, ux, uy, vx, vy, t0, t1 = geometry
        lo, sweep = _param_interval(t0, t1)
        return _conic_classify((cx, cy), (ux, uy), (vx, vy), lo, sweep, box, eps)
    return UNRESOLVED


def classify_point(p, box, eps: float = 0.0) -> str:
    if p is None or not _finite(*p):
        return UNRESOLVED
    x0, y0, x1, y1 = box
    return FULLY_INSIDE if (x0 - eps <= p[0] <= x1 + eps and y0 - eps <= p[1] <= y1 + eps) else FULLY_OUTSIDE


def classify_points(points, box, eps: float = 0.0) -> str:
    """A record represented by a finite point set (text placement, dimension points)."""
    if not points:
        return UNRESOLVED
    states = {classify_point(p, box, eps) for p in points}
    if UNRESOLVED in states:
        return UNRESOLVED
    if states == {FULLY_INSIDE}:
        return FULLY_INSIDE
    if states == {FULLY_OUTSIDE}:
        return FULLY_OUTSIDE
    return CROSSES_BOUNDARY


def exact_bbox(kind: str, geometry: tuple):
    """Exact axis-aligned bounds of a realised curve (None when not finite / unsupported)."""
    if geometry is None or not _finite(*geometry):
        return None
    if kind == "SEGMENT":
        x1, y1, x2, y2 = geometry
        return min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2)
    if kind == "ARC":
        cx, cy, r, a0, a1 = geometry
        return _conic_bbox((cx, cy), (r, 0.0), (0.0, r), a0, (a1 - a0) % TWO_PI or TWO_PI)
    if kind == "CIRCLE":
        cx, cy, r = geometry
        return cx - r, cy - r, cx + r, cy + r
    if kind == "ELLIPTICAL_ARC":
        cx, cy, ux, uy, vx, vy, t0, t1 = geometry
        lo, sweep = _param_interval(t0, t1)
        return _conic_bbox((cx, cy), (ux, uy), (vx, vy), lo, sweep)
    return None
