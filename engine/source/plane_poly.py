"""PLANE POLYGONS (M9 S2) - the small set of exact planar operations the polygon layouts need (generic; stdlib only).

    area(poly)                       signed shoelace area (counter-clockwise > 0)
    perimeter(poly)                  closed length
    clip_rect(poly, x0, y0, x1, y1)  Sutherland-Hodgman clip of any simple polygon by an axis-aligned rectangle; the
                                     result's area is the exact area of the intersection (a concave subject may give
                                     zero-width bridges along the window edge, which carry no area)
    region_area_in_rect(outer, holes, rect)   area of (outer - holes) inside the rectangle
    clip_convex(poly, window)        the same clip by any convex window (either orientation)
    region_area_in_convex(outer, holes, window)   area of (outer - holes) inside a convex window
    frame_angle(poly)                the direction (mod 90 degrees) of the longest edge: layouts run along the walls
    rotate(poly, theta)              rotation about the origin by -theta (the frame becomes the x / y axes)
    intervals(outer, holes, y)       the x-intervals of (outer - holes) on the horizontal line y (even-odd rule)
    band_intervals(outer, holes, y0, y1, step)   the x-extent of (outer - holes) over the band y0..y1, as merged
                                     intervals (scan lines at every vertex level inside the band, the band edges and
                                     at most `step` apart)
"""

from __future__ import annotations

import math

EPS = 1e-9


def area(poly):
    n = len(poly)
    return sum(poly[i - 1][0] * poly[i][1] - poly[i][0] * poly[i - 1][1] for i in range(n)) / 2.0 if n >= 3 else 0.0


def perimeter(poly):
    return sum(math.dist(poly[i - 1], poly[i]) for i in range(len(poly))) if len(poly) >= 2 else 0.0


def _clip(poly, inside, cross):
    out = []
    n = len(poly)
    for i in range(n):
        cur, prev = poly[i], poly[i - 1]
        ci, pi = inside(cur), inside(prev)
        if ci:
            if not pi:
                out.append(cross(prev, cur))
            out.append(cur)
        elif pi:
            out.append(cross(prev, cur))
    return out


def clip_rect(poly, x0, y0, x1, y1):
    p = [tuple(map(float, q)) for q in poly]

    def xcut(xc):
        return lambda a, b: (xc, a[1] + (b[1] - a[1]) * (xc - a[0]) / (b[0] - a[0]))

    def ycut(yc):
        return lambda a, b: (a[0] + (b[0] - a[0]) * (yc - a[1]) / (b[1] - a[1]), yc)
    for inside, cross in ((lambda q: q[0] >= x0, xcut(x0)), (lambda q: q[0] <= x1, xcut(x1)),
                          (lambda q: q[1] >= y0, ycut(y0)), (lambda q: q[1] <= y1, ycut(y1))):
        if not p:
            return []
        p = _clip(p, inside, cross)
    return p


def region_area_in_rect(outer, holes, rect):
    x0, y0, x1, y1 = rect
    a = abs(area(clip_rect(outer, x0, y0, x1, y1)))
    for h in holes or ():
        a -= abs(area(clip_rect(h, x0, y0, x1, y1)))
    return max(a, 0.0)


def clip_convex(poly, window):
    w = [tuple(map(float, q)) for q in window]
    if len(w) < 3 or abs(area(w)) <= EPS:
        return []
    sgn = 1.0 if area(w) > 0 else -1.0
    p = [tuple(map(float, q)) for q in poly]
    for i in range(len(w)):
        a, b = w[i - 1], w[i]
        ex, ey = b[0] - a[0], b[1] - a[1]
        if ex == 0 and ey == 0:
            continue

        def side(q, a=a, ex=ex, ey=ey):
            return sgn * (ex * (q[1] - a[1]) - ey * (q[0] - a[0]))

        def cross(u, v, side=side):
            su, sv = side(u), side(v)
            t = su / (su - sv)
            return (u[0] + (v[0] - u[0]) * t, u[1] + (v[1] - u[1]) * t)
        if not p:
            return []
        p = _clip(p, lambda q, side=side: side(q) >= 0, cross)
    return p


def region_area_in_convex(outer, holes, window):
    a = abs(area(clip_convex(outer, window)))
    for h in holes or ():
        a -= abs(area(clip_convex(h, window)))
    return max(a, 0.0)


def bbox(poly):
    xs, ys = [p[0] for p in poly], [p[1] for p in poly]
    return min(xs), min(ys), max(xs), max(ys)


def frame_angle(poly):
    best, theta = -1.0, 0.0
    for i in range(len(poly)):
        (ax, ay), (bx, by) = poly[i - 1], poly[i]
        ln = math.hypot(bx - ax, by - ay)
        if ln > best + 1e-9:
            best, theta = ln, math.atan2(by - ay, bx - ax) % (math.pi / 2)
    if abs(theta - math.pi / 2) < 1e-9 or abs(theta) < 1e-9:
        theta = 0.0
    return theta


def rotate(poly, theta):
    if theta == 0.0:
        return [(float(x), float(y)) for x, y in poly]
    c, s = math.cos(-theta), math.sin(-theta)
    return [(x * c - y * s, x * s + y * c) for x, y in poly]


def intervals(outer, holes, y):
    xs = []
    for ring in [outer] + list(holes or ()):
        n = len(ring)
        for i in range(n):
            (x1, y1), (x2, y2) = ring[i - 1], ring[i]
            if (y1 > y) != (y2 > y):
                xs.append(x1 + (y - y1) * (x2 - x1) / (y2 - y1))
    xs.sort()
    return [(xs[i], xs[i + 1]) for i in range(0, len(xs) - 1, 2) if xs[i + 1] - xs[i] > EPS]


def merge(iv, tol=1e-6):
    out = []
    for a, b in sorted(iv):
        if out and a <= out[-1][1] + tol:
            out[-1] = (out[-1][0], max(out[-1][1], b))
        else:
            out.append((a, b))
    return out


def band_intervals(outer, holes, y0, y1, step=0.02):
    if y1 - y0 <= EPS:
        return []
    levels = {y0 + 1e-7, y1 - 1e-7}
    for ring in [outer] + list(holes or ()):
        for _, y in ring:
            if y0 < y < y1:
                levels.update((y - 1e-7, y + 1e-7))
    n = max(1, int(math.ceil((y1 - y0) / step)))
    levels.update(y0 + (y1 - y0) * (i + 0.5) / n for i in range(n))
    iv = []
    for y in sorted(levels):
        if y0 < y < y1:
            iv += intervals(outer, holes, y)
    return merge(iv)
