"""CURVED MEMBER GEOMETRY - circular arcs, rings and spherical shells measured exactly (generic, stdlib).

Arcs
  A world arc is {"c": (x, y), "r": r, "start": deg, "sweep": deg}: counter-clockwise, 0 < sweep <= 360.
  world_arc() converts a DXF ARC / CIRCLE given in its object coordinate system. An extrusion of (0, 0, -1) maps an
  OCS point (x, y) to the world point (-x, y): the angle a becomes 180 - a and the turning direction reverses.
  transform_arc() applies a 2D similarity (rotation, uniform scale, translation, optional mirror) as a block insert
  does; a mirror reverses the direction. An end angle below the start angle is a sweep across 0 degrees, never a
  negative sweep and never a near-full circle. Arc length = r x sweep; chord = 2 r sin(sweep / 2).
Angular coverage
  merge_intervals(): repeated or overlapping arcs on one circle are covered once and never summed twice. A ring is
  closed only when its merged coverage is 360 degrees.
Bands (curved members drawn as two concentric edges)
  band_segments(): a segment exists where both the inner and the outer edge are drawn. Its area is the annular
  sector sweep / 2 x (R2^2 - R1^2); its centreline length is (R1 + R2) / 2 x sweep.
Overlaps with straight members
  disk_rect_area(): the exact area of a disk inside a rectangle of any orientation (closed form, no sampling).
  annulus_rect_area() = disk(R2) - disk(R1) inside the rectangle: the junction of a ring with a straight member.
Spherical caps and shells
  cap_radius(chord, rise); cap_volume(R, h); cap_area(R, h) = 2 pi R h. shell_between_caps(): the solid between a
  sphere and a concentric sphere t smaller, above one springing plane (thickness normal to the surface).
  circle_fit() is an algebraic least-squares fit. profile_check() calls a drawn profile circular only within a stated
  residual, and a surface of revolution spherical only when the fitted centre lies on the axis of revolution.
Lines at a spacing over a surface: total length = area / spacing (a continuous density, never rounded).
Concentric circles offset about a centre radius: total length = 2 pi x sum(rc + offset); for offsets that sum to zero
it is n x 2 pi rc, whatever the offsets are.

Nothing here names a project, a sheet or a handle.
"""

from __future__ import annotations

import math

TOL = 1e-9


class CurvedGeometryError(ValueError):
    pass


# ------------------------------------------------------------------ arcs
def norm_deg(a):
    a = math.fmod(a, 360.0)
    a = a + 360.0 if a < 0 else a
    return 0.0 if abs(a - 360.0) < TOL else a


def sweep_deg(a0, a1):
    """CCW sweep from a0 to a1 in degrees, in (0, 360). Equal angles are an error, not a full circle."""
    s = norm_deg(a1 - a0)
    if s < TOL:
        raise CurvedGeometryError("zero sweep: equal start and end angles are not an arc")
    return s


def world_arc(centre, r, start_deg=0.0, end_deg=360.0, extrusion=(0.0, 0.0, 1.0), full=False):
    """A DXF ARC (or CIRCLE with full=True) in its OCS -> a CCW world arc. Only +Z / -Z extrusions are planar here."""
    ex, ey, ez = (float(v) for v in extrusion)
    if abs(ex) > 1e-9 or abs(ey) > 1e-9 or abs(abs(ez) - 1.0) > 1e-9:
        raise CurvedGeometryError(f"extrusion {extrusion} is not +Z or -Z")
    if r <= 0:
        raise CurvedGeometryError("radius must be positive")
    sw = 360.0 if full else sweep_deg(start_deg, end_deg)
    cx, cy = float(centre[0]), float(centre[1])
    if ez > 0:
        return {"c": (cx, cy), "r": float(r), "start": 0.0 if full else norm_deg(start_deg), "sweep": sw}
    # arbitrary-axis algorithm for Az = (0, 0, -1): Ax = (-1, 0, 0), Ay = (0, 1, 0)
    return {"c": (-cx, cy), "r": float(r), "start": 0.0 if full else norm_deg(180.0 - end_deg), "sweep": sw}


def transform_arc(arc, m):
    """m = (a, b, c, d, tx, ty): world = [[a, b], [c, d]] . p + (tx, ty). Must be a similarity (rotation x uniform
    scale, with or without a mirror)."""
    a, b, c, d, tx, ty = (float(v) for v in m)
    s1, s2 = math.hypot(a, c), math.hypot(b, d)
    if abs(s1 - s2) > 1e-9 * max(1.0, s1) or abs(a * b + c * d) > 1e-9 * max(1.0, s1 * s2):
        raise CurvedGeometryError("not a similarity: a circle would not stay a circle")
    det = a * d - b * c
    x, y = arc["c"]
    cen = (a * x + b * y + tx, c * x + d * y + ty)

    def ang(deg):
        u = (math.cos(math.radians(deg)), math.sin(math.radians(deg)))
        return norm_deg(math.degrees(math.atan2(c * u[0] + d * u[1], a * u[0] + b * u[1])))
    start = ang(arc["start"]) if det > 0 else ang(arc["start"] + arc["sweep"])
    return {"c": cen, "r": arc["r"] * s1, "start": 0.0 if arc["sweep"] >= 360.0 else start, "sweep": arc["sweep"]}


def arc_length(arc):
    return arc["r"] * math.radians(arc["sweep"])


def chord_length(arc):
    return 2.0 * arc["r"] * math.sin(math.radians(min(arc["sweep"], 360.0)) / 2.0)


def arc_end_points(arc):
    c, r = arc["c"], arc["r"]
    p = lambda deg: (c[0] + r * math.cos(math.radians(deg)), c[1] + r * math.sin(math.radians(deg)))  # noqa: E731
    return p(arc["start"]), p(arc["start"] + arc["sweep"])


def concentric(a, b, ctol=1.0):
    return math.dist(a["c"], b["c"]) <= ctol


# ------------------------------------------------------------------ angular coverage
def _unroll(intervals):
    out = []
    for s, w in intervals:
        if w <= 0 or w > 360.0 + TOL:
            raise CurvedGeometryError(f"sweep {w} outside (0, 360]")
        if w >= 360.0 - TOL:
            return [(0.0, 360.0)]
        s = norm_deg(s)
        e = s + w
        out.extend([(s, 360.0), (0.0, e - 360.0)] if e > 360.0 else [(s, e)])
    return sorted(out)


def _roll(pieces):
    merged = []
    for a, b in sorted(pieces):
        if merged and a <= merged[-1][1] + TOL:
            merged[-1][1] = max(merged[-1][1], b)
        else:
            merged.append([a, b])
    if not merged:
        return []
    if len(merged) == 1 and merged[0][0] <= TOL and merged[0][1] >= 360.0 - TOL:
        return [(0.0, 360.0)]
    if len(merged) > 1 and merged[0][0] <= TOL and merged[-1][1] >= 360.0 - TOL:      # joined across 0 degrees
        first = merged.pop(0)
        merged[-1][1] = 360.0 + first[1]
    return [(norm_deg(a), b - a) for a, b in merged]


def merge_intervals(intervals):
    """[(start_deg, sweep_deg)] on one circle -> disjoint merged intervals; each angle is covered once."""
    return _roll(_unroll(intervals))


def coverage_deg(intervals):
    return sum(w for _, w in merge_intervals(intervals))


def intersect_intervals(a, b):
    pa, pb = _unroll(merge_intervals(a)), _unroll(merge_intervals(b))
    out = []
    for a0, a1 in pa:
        for b0, b1 in pb:
            lo, hi = max(a0, b0), min(a1, b1)
            if hi - lo > TOL:
                out.append((lo, hi))
    return _roll(out)


def is_closed(intervals):
    return coverage_deg(intervals) >= 360.0 - 1e-7


# ------------------------------------------------------------------ bands
def annular_sector_area(r1, r2, sweep):
    if not 0 <= r1 < r2:
        raise CurvedGeometryError("need 0 <= r1 < r2")
    return 0.5 * math.radians(sweep) * (r2 * r2 - r1 * r1)


def band_segments(inner_arcs, outer_arcs, ctol=1.0, rtol=1e-6):
    """Concentric inner and outer edges of one curved member -> its band segments (both edges drawn)."""
    arcs = list(inner_arcs) + list(outer_arcs)
    if not inner_arcs or not outer_arcs:
        raise CurvedGeometryError("a band needs an inner and an outer edge")
    if any(not concentric(arcs[0], x, ctol) for x in arcs):
        raise CurvedGeometryError("band edges are not concentric")
    r1s, r2s = {round(x["r"], 6) for x in inner_arcs}, {round(x["r"], 6) for x in outer_arcs}
    if len(r1s) != 1 or len(r2s) != 1:
        raise CurvedGeometryError("each band edge must be one radius")
    r1, r2 = inner_arcs[0]["r"], outer_arcs[0]["r"]
    if r2 - r1 <= rtol:
        raise CurvedGeometryError("outer edge must be outside the inner edge")
    segs = intersect_intervals([(x["start"], x["sweep"]) for x in inner_arcs],
                               [(x["start"], x["sweep"]) for x in outer_arcs])
    rc = (r1 + r2) / 2.0
    return [{"start": s, "sweep": w, "r1": r1, "r2": r2, "width": r2 - r1, "centreline_length": rc * math.radians(w),
             "chord_centreline": 2 * rc * math.sin(math.radians(min(w, 360.0)) / 2), "area": annular_sector_area(r1, r2, w)}
            for s, w in segs]


# ------------------------------------------------------------------ overlaps (closed form)
def _H(t, R):
    """Antiderivative of sqrt(R^2 - t^2) on [-R, R]."""
    t = max(-R, min(R, t))
    return 0.5 * (t * math.sqrt(max(0.0, R * R - t * t)) + R * R * math.asin(t / R))


def _quadrant(x, y, R):
    """Area of the disk |p| <= R with X <= x and Y <= y."""
    if x <= -R or y <= -R:
        return 0.0
    x = min(x, R)
    if y >= R:
        return 2.0 * (_H(x, R) - _H(-R, R))
    w = math.sqrt(R * R - y * y)
    total = 0.0
    # pieces of [-R, x]: (-R, -w) and (w, R) carry 2h if y > 0 else 0; (-w, w) carries y + h
    for lo, hi, kind in ((-R, -w, "out"), (-w, w, "in"), (w, R, "out")):
        b = min(hi, x)
        if b <= lo:
            continue
        if kind == "in":
            total += y * (b - lo) + _H(b, R) - _H(lo, R)
        elif y > 0:
            total += 2.0 * (_H(b, R) - _H(lo, R))
    return total


def disk_rect_area(centre, R, rect):
    """rect = {"o": (x, y), "u": (ux, uy) unit direction, "u0", "u1", "v0", "v1"}: the points o + s u + t v with
    v = u turned +90 degrees, s in [u0, u1], t in [v0, v1]. Returns the exact area of the disk inside it."""
    if R <= 0:
        return 0.0
    ux, uy = rect["u"]
    n = math.hypot(ux, uy)
    if abs(n - 1.0) > 1e-9:
        raise CurvedGeometryError("rect direction must be a unit vector")
    vx, vy = -uy, ux
    dx, dy = centre[0] - rect["o"][0], centre[1] - rect["o"][1]
    cu, cv = dx * ux + dy * uy, dx * vx + dy * vy
    u0, u1, v0, v1 = rect["u0"] - cu, rect["u1"] - cu, rect["v0"] - cv, rect["v1"] - cv
    if u1 <= u0 or v1 <= v0:
        raise CurvedGeometryError("empty rectangle")
    return _quadrant(u1, v1, R) - _quadrant(u0, v1, R) - _quadrant(u1, v0, R) + _quadrant(u0, v0, R)


def annulus_rect_area(centre, r1, r2, rect):
    if not 0 <= r1 < r2:
        raise CurvedGeometryError("need 0 <= r1 < r2")
    return disk_rect_area(centre, r2, rect) - disk_rect_area(centre, r1, rect)


def axis_rect(x0, y0, x1, y1):
    """An axis-aligned rectangle in disk_rect_area form."""
    return {"o": (0.0, 0.0), "u": (1.0, 0.0), "u0": min(x0, x1), "u1": max(x0, x1), "v0": min(y0, y1), "v1": max(y0, y1)}


def circle_segment_area(R, d):
    """Area of a disk of radius R beyond a line at signed distance d from its centre (d >= R -> 0)."""
    if d >= R:
        return 0.0
    if d <= -R:
        return math.pi * R * R
    return R * R * math.acos(d / R) - d * math.sqrt(R * R - d * d)


# ------------------------------------------------------------------ spherical caps and shells
def cap_radius(chord, rise):
    if chord <= 0 or rise <= 0:
        raise CurvedGeometryError("chord and rise must be positive")
    return (chord * chord / 4.0 + rise * rise) / (2.0 * rise)


def cap_volume(R, h):
    if not 0 <= h <= 2 * R + TOL:
        raise CurvedGeometryError("cap height outside [0, 2R]")
    return math.pi * h * h * (3.0 * R - h) / 3.0


def cap_area(R, h):
    if not 0 <= h <= 2 * R + TOL:
        raise CurvedGeometryError("cap height outside [0, 2R]")
    return 2.0 * math.pi * R * h


def shell_between_caps(r_out, h_out, t):
    """The solid between a sphere of radius r_out and a concentric sphere of radius r_out - t, above the springing
    plane that cuts the outer cap at height h_out. Thickness t is normal to both surfaces."""
    if t <= 0 or t >= r_out:
        raise CurvedGeometryError("thickness must be in (0, R)")
    d = r_out - h_out                                   # signed distance from the centre up to the springing plane
    r_in = r_out - t
    h_in = r_in - d
    if h_in <= 0:
        raise CurvedGeometryError("the inner surface does not reach above the springing plane")
    r_mid = r_out - t / 2.0
    h_mid = r_mid - d
    a_out2, a_in2 = r_out * r_out - d * d, r_in * r_in - d * d
    return {"r_out": r_out, "h_out": h_out, "r_in": r_in, "h_in": h_in, "t": t, "centre_below_springing": d,
            "volume": cap_volume(r_out, h_out) - cap_volume(r_in, h_in),
            "area_out": cap_area(r_out, h_out), "area_in": cap_area(r_in, h_in),
            "r_mid": r_mid, "h_mid": h_mid, "area_mid": cap_area(r_mid, h_mid),
            "springing_radius_out": math.sqrt(max(0.0, a_out2)), "springing_radius_in": math.sqrt(max(0.0, a_in2)),
            "springing_width": math.sqrt(max(0.0, a_out2)) - math.sqrt(max(0.0, a_in2))}


def circle_fit(points):
    """Algebraic (Kasa) least-squares circle -> (centre, R, max |radial residual|)."""
    n = len(points)
    if n < 3:
        raise CurvedGeometryError("a circle fit needs three points")
    mx, my = sum(p[0] for p in points) / n, sum(p[1] for p in points) / n
    u = [p[0] - mx for p in points]
    v = [p[1] - my for p in points]
    suu, svv, suv = sum(a * a for a in u), sum(b * b for b in v), sum(a * b for a, b in zip(u, v))
    suuu, svvv = sum(a ** 3 for a in u), sum(b ** 3 for b in v)
    suvv, svuu = sum(a * b * b for a, b in zip(u, v)), sum(b * a * a for a, b in zip(u, v))
    det = suu * svv - suv * suv
    if abs(det) < TOL:
        raise CurvedGeometryError("collinear points")
    uc = (0.5 * (suuu + suvv) * svv - 0.5 * (svvv + svuu) * suv) / det
    vc = (0.5 * (svvv + svuu) * suu - 0.5 * (suuu + suvv) * suv) / det
    c = (uc + mx, vc + my)
    R = math.sqrt(uc * uc + vc * vc + (suu + svv) / n)
    return c, R, max(abs(math.dist(p, c) - R) for p in points)


def profile_check(points, residual_tol, axis_x=None, axis_tol=None):
    """CIRCULAR if every vertex is within residual_tol of the fitted circle; SPHERICAL_ABOUT_AXIS when, in addition,
    the fitted centre lies on the vertical axis x = axis_x within axis_tol (a surface of revolution of a circular arc
    about an axis through its centre is a sphere)."""
    c, R, res = circle_fit(points)
    state = "CIRCULAR" if res <= residual_tol else "NOT_CIRCULAR"
    on_axis = None
    if axis_x is not None:
        on_axis = abs(c[0] - axis_x) <= axis_tol
        if state == "CIRCULAR" and on_axis:
            state = "SPHERICAL_ABOUT_AXIS"
    return {"state": state, "centre": c, "R": R, "max_residual": res, "centre_on_axis": on_axis}


# ------------------------------------------------------------------ lengths
def length_at_spacing(area, spacing):
    if spacing <= 0 or area < 0:
        raise CurvedGeometryError("spacing must be positive and area non-negative")
    return area / spacing


def concentric_circle_total(rc, offsets):
    """Total length of full circles of radius rc + o for each offset o, and whether the offsets are symmetric."""
    if any(rc + o <= 0 for o in offsets):
        raise CurvedGeometryError("radius must stay positive")
    total = sum(2.0 * math.pi * (rc + o) for o in offsets)
    return {"total": total, "symmetric": abs(sum(offsets)) <= 1e-9 * max(1.0, rc), "n": len(offsets),
            "n_times_centreline": len(offsets) * 2.0 * math.pi * rc}
