"""STRUCTURAL COMPLETENESS - plan overlap, hatch reading and beam depth-convention arithmetic (generic).

Nothing here reads a drawing. Callers pass coordinates they took from a source and get back what follows from them:
how much of a rectangle lies inside a polygon, whether a boundary edge lies on a drawn line, which legend symbol a
measured hatch spacing belongs to, what a beam's concrete is under each reading of its schedule depth, and which
length class a span falls in.

Plan geometry (mm, any frame)
    point_in_polygon(x, y, poly)              even-odd rule (a point on an edge counts as outside)
    rect_polygon_overlap(rect, poly, holes, step)
                                              area of rect inside poly minus holes, by cell-centre sampling at `step`
                                              (exact for rectilinear shapes on the step grid; robust for slit / concave
                                              faces where polygon clipping is not)
    edge_on_lines(p, q, lines, tol, min_cover) does the edge p-q lie on drawn segments for at least `min_cover` of its
                                              length (union of collinear segments within `tol`)

Hatch reading
    hatch_spacing(offsets, min_gap)           median perpendicular spacing of parallel hatch lines; a doubled gap (a
                                              line lost to clipping) is folded back to one spacing
    nearest_reference(value, references, max_rel)
                                              the reference label whose value is nearest; None when the nearest is more
                                              than `max_rel` away (relative) or two references are equally near

Beam depth conventions (m)
    beam_convention_volumes(B, H, L, t)       TOTAL_DEPTH: H is the overall depth, the slab zone above the beam is part
                                              of H, volume B x H x L; BELOW_SLAB: H is measured under the slab, the
                                              beam is B x (H + t) x L; the difference is the B x t x L strip over the
                                              beam. Panels measured between beam faces never hold that strip, so
                                              neither reading counts it twice.

Length classes
    length_class(L, bounds)                   index of the first bound L is below (bounds ascending); len(bounds) above
                                              the last

Stdlib only. No project data.
"""

from __future__ import annotations

import math
import statistics

TOL = 1e-9


class CompletenessError(ValueError):
    pass


# ------------------------------------------------------------------ plan geometry
def point_in_polygon(x, y, poly):
    inside = False
    n = len(poly)
    for i in range(n):
        x0, y0 = poly[i][0], poly[i][1]
        x1, y1 = poly[(i + 1) % n][0], poly[(i + 1) % n][1]
        if (y0 > y) != (y1 > y) and x < x0 + (y - y0) * (x1 - x0) / (y1 - y0):
            inside = not inside
    return inside


def _bbox(poly):
    xs = [p[0] for p in poly]
    ys = [p[1] for p in poly]
    return min(xs), min(ys), max(xs), max(ys)


def rect_polygon_overlap(rect, poly, holes=(), step=10.0):
    x0, y0, x1, y1 = (min(rect[0], rect[2]), min(rect[1], rect[3]), max(rect[0], rect[2]), max(rect[1], rect[3]))
    if step <= 0:
        raise CompletenessError("step must be positive")
    if len(poly) < 3:
        raise CompletenessError("a polygon needs at least three vertices")
    px0, py0, px1, py1 = _bbox(poly)
    if px1 <= x0 or px0 >= x1 or py1 <= y0 or py0 >= y1:
        return 0.0
    nx = max(1, int(round((x1 - x0) / step)))
    ny = max(1, int(round((y1 - y0) / step)))
    dx, dy = (x1 - x0) / nx, (y1 - y0) / ny
    hit = 0
    for i in range(nx):
        cx = x0 + dx * (i + 0.5)
        if not (px0 <= cx <= px1):
            continue
        for j in range(ny):
            cy = y0 + dy * (j + 0.5)
            if py0 <= cy <= py1 and point_in_polygon(cx, cy, poly) and not any(point_in_polygon(cx, cy, h)
                                                                              for h in holes):
                hit += 1
    return hit * dx * dy


def edge_on_lines(p, q, lines, tol=2.0, min_cover=0.9):
    """lines: [((x0, y0), (x1, y1)), ...]. True when collinear drawn segments cover min_cover of p-q."""
    L = math.hypot(q[0] - p[0], q[1] - p[1])
    if L <= TOL:
        raise CompletenessError("a zero-length edge")
    ux, uy = (q[0] - p[0]) / L, (q[1] - p[1]) / L
    spans = []
    for a, b in lines:
        da = (a[0] - p[0]) * uy - (a[1] - p[1]) * ux
        db = (b[0] - p[0]) * uy - (b[1] - p[1]) * ux
        if abs(da) > tol or abs(db) > tol:
            continue
        sa = (a[0] - p[0]) * ux + (a[1] - p[1]) * uy
        sb = (b[0] - p[0]) * ux + (b[1] - p[1]) * uy
        lo, hi = max(0.0, min(sa, sb)), min(L, max(sa, sb))
        if hi > lo:
            spans.append((lo, hi))
    covered, end = 0.0, 0.0
    for lo, hi in sorted(spans):
        if hi <= end:
            continue
        covered += hi - max(lo, end)
        end = hi
    return covered / L >= min_cover - TOL, covered / L


# ------------------------------------------------------------------ hatch reading
def hatch_spacing(offsets, min_gap=0.0):
    pts = sorted(offsets)
    gaps = [b - a for a, b in zip(pts, pts[1:]) if b - a > min_gap]
    if not gaps:
        return None
    base = min(gaps)
    singles = [g / max(1, round(g / base)) for g in gaps]
    return {"spacing": statistics.median(singles), "min": min(singles), "max": max(singles), "lines": len(pts),
            "gaps": len(gaps)}


def nearest_reference(value, references, max_rel=0.06):
    if value is None or not references:
        return None, {}
    dist = {k: abs(value - v) / v for k, v in references.items()}
    order = sorted(dist.items(), key=lambda kv: kv[1])
    best = order[0]
    if best[1] > max_rel or (len(order) > 1 and abs(order[1][1] - best[1]) <= TOL):
        return None, dist
    return best[0], dist


# ------------------------------------------------------------------ beams
def beam_convention_volumes(B, H, L, t):
    for name, v in (("B", B), ("H", H), ("L", L), ("t", t)):
        if v is None:
            raise CompletenessError(f"{name} is missing: a missing dimension is not zero")
        if float(v) < 0:
            raise CompletenessError(f"{name} is negative")
    B, H, L, t = map(float, (B, H, L, t))
    if t >= H:
        raise CompletenessError("slab thickness not below the schedule depth")
    total = B * H * L
    below = B * (H + t) * L
    return {"TOTAL_DEPTH": total, "BELOW_SLAB": below, "STRIP": below - total,
            "DOWNSTAND_TOTAL_DEPTH": B * (H - t) * L, "DOWNSTAND_BELOW_SLAB": B * H * L}


def length_class(L, bounds):
    if L is None:
        raise CompletenessError("a missing length has no class")
    b = list(bounds)
    if b != sorted(b):
        raise CompletenessError("bounds must ascend")
    for i, x in enumerate(b):
        if L < x:
            return i
    return len(b)
