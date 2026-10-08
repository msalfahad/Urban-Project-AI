"""GROUND SLAB QTO - restricted, source-zoned slab-on-grade concrete and mesh quantities (generic).

Only the zones a source assigns a thickness and a mesh may carry a quantity. Every other cell stays listed with no
m3 and no kg (not even 0). No thickness ladder, no fallback, no rule carried over from another slab family.

Geometry
  * A region is a list of closed rings (the first is the outer boundary, the others are holes). A ring is a list of
    edges, each a straight LINE or a circular ARC, so a drawn curve is integrated as a curve and not as its chords.
  * ring_from_polygon(points, arcs) builds a ring from a polygon whose vertices on a drawn arc are chords of it: a run
    of consecutive vertices on the arc (one turning direction, short chords) is replaced by the arc itself, so a cell
    bounded by part of a drawn arc gets that sub-arc. Vertices off the circle are kept as drawn; inconsistent runs
    are refused.
  * area(): exact signed area by Green's theorem (lines and arcs in closed form).

Mesh (rate density)
  * A mesh 'N bars/m each way' is two independent bar families. Bars of direction X run along x and are distributed
    across y; bars of direction Y run along y and are distributed across x.
  * band_strips(region, direction) cuts the region into bands across the distribution coordinate t at every vertex
    and at every arc extreme, so the chord length inside a band is a sum of straight and circular branches. Each
    band's integral of chord length is exact (trapezoid for a line, the closed-form circle integral for an arc).
  * mesh_direction() feeds the strips to slab_rebar_qto.rate_strip_length: L = N x f x sum(w x l). The equivalent
    count N x f x W is never rounded and never +1; the physical bar count stays UNRESOLVED.
  * For any region the strip integral of each direction equals the region area; strip_coverage() proves it.

Concrete
  * slab_concrete(): net area x the source thickness. A missing thickness returns no volume.

Stdlib + engine.source.slab_rebar_qto only. No project data.
"""

from __future__ import annotations

import math

from engine.source import slab_rebar_qto as SR

LINE = "LINE"
ARC = "ARC"
X = "X"          # bars run along x, distributed across y
Y = "Y"          # bars run along y, distributed across x
DIRECTIONS = (X, Y)
TOL = 1e-9


class GroundSlabQtoError(ValueError):
    pass


# ------------------------------------------------------------------ rings
def line(p0, p1):
    return (LINE, (float(p0[0]), float(p0[1])), (float(p1[0]), float(p1[1])))


def arc(centre, radius, theta0, theta1):
    """Arc of a circle traversed from angle theta0 to theta1 (radians; theta1 < theta0 means clockwise)."""
    if radius <= 0:
        raise GroundSlabQtoError(f"arc radius must be positive: {radius!r}")
    if abs(theta1 - theta0) <= TOL or abs(theta1 - theta0) > 2 * math.pi + TOL:
        raise GroundSlabQtoError("arc sweep must be in (0, 2 pi]")
    return (ARC, (float(centre[0]), float(centre[1])), float(radius), float(theta0), float(theta1))


def _point(edge, end):
    if edge[0] == LINE:
        return edge[1] if end == 0 else edge[2]
    _, (cx, cy), r, t0, t1 = edge
    t = t0 if end == 0 else t1
    return (cx + r * math.cos(t), cy + r * math.sin(t))


def check_ring(ring, *, tol=1e-6):
    """A ring is closed and every edge starts where the previous one ends."""
    if len(ring) < 2:
        raise GroundSlabQtoError("a ring needs at least two edges")
    for i, e in enumerate(ring):
        a = _point(e, 1)
        b = _point(ring[(i + 1) % len(ring)], 0)
        if math.hypot(a[0] - b[0], a[1] - b[1]) > tol:
            raise GroundSlabQtoError(f"ring is not closed at edge {i}: {a} -> {b}")
    return ring


MAX_CHORD_DEG = 30.0   # a polyline that stands for a drawn arc uses short chords; a longer step is a real line


def ring_from_polygon(points, arcs=(), *, tol_mm=0.5, max_chord_deg=MAX_CHORD_DEG):
    """Closed ring from polygon vertices. arcs: (centre, radius, start_deg, end_deg) drawn counter-clockwise from
    start to end (the DXF convention). A run of consecutive vertices on one arc (on the circle within tol_mm, inside
    the sweep, turning one way, every chord shorter than max_chord_deg) is a chord approximation of that arc: the
    run is replaced by the arc itself, from its first to its last vertex. A vertex off the circle is kept as drawn
    (a notch where another member meets the curve splits the arc into stretches). A two-vertex chord longer than
    max_chord_deg is a real straight edge; a longer run that turns both ways or has a long chord is refused.
    Returns (ring, replaced_vertex_count)."""
    pts = [(float(x), float(y)) for x, y in points]
    if len(pts) > 1 and math.hypot(pts[0][0] - pts[-1][0], pts[0][1] - pts[-1][1]) <= tol_mm:
        pts = pts[:-1]
    n = len(pts)
    if n < 3:
        raise GroundSlabQtoError("a polygon needs three vertices")
    arc_of = {}                       # first vertex index of a run -> (last index, arc edge, interior indices)
    claimed = set()
    for (c, r, a0d, a1d) in arcs:
        a0, a1 = math.radians(a0d), math.radians(a1d)
        if a1 <= a0:
            a1 += 2 * math.pi
        on = [k for k in range(n) if _on_arc(pts[k], c, r, a0, a1, tol_mm)]
        if not on:
            continue
        onset = set(on)
        starts = [k for k in on if (k - 1) % n not in onset] or [on[0]]
        for s0 in starts:
            run = [s0]
            while (run[-1] + 1) % n in onset and (run[-1] + 1) % n != s0:
                run.append((run[-1] + 1) % n)
            if len(run) < 2:
                continue
            th = [math.atan2(pts[k][1] - c[1], pts[k][0] - c[0]) for k in run]
            for i in range(1, len(th)):               # unwrap
                while th[i] - th[i - 1] > math.pi:
                    th[i] -= 2 * math.pi
                while th[i] - th[i - 1] < -math.pi:
                    th[i] += 2 * math.pi
            steps = [b - a for a, b in zip(th, th[1:])]
            longest = max(abs(x) for x in steps)
            if len(run) == 2 and longest > math.radians(max_chord_deg):
                continue                              # a real straight edge between two points of the circle
            if not (all(x > 0 for x in steps) or all(x < 0 for x in steps)):
                raise GroundSlabQtoError(f"vertices on the arc centred {c} do not turn one way")
            if longest > math.radians(max_chord_deg):
                raise GroundSlabQtoError(f"a chord on the arc centred {c} is longer than {max_chord_deg} deg")
            if claimed & set(run) - {run[0], run[-1]} or run[0] in arc_of:
                raise GroundSlabQtoError("two arcs claim the same polygon vertices")
            claimed |= set(run[1:-1])
            pts[run[0]] = (c[0] + r * math.cos(th[0]), c[1] + r * math.sin(th[0]))
            pts[run[-1]] = (c[0] + r * math.cos(th[-1]), c[1] + r * math.sin(th[-1]))
            arc_of[run[0]] = (run[-1], arc(c, r, th[0], th[-1]), run[1:-1])
    inner = {k for _, _, ch in arc_of.values() for k in ch}
    start = min(k for k in range(n) if k not in inner)
    ring, k = [], start
    for _ in range(n + 1):
        if k in arc_of:
            v, e, _ch = arc_of[k]
            ring.append(e)
            nxt = v
        else:
            nxt = (k + 1) % n
            if pts[k] != pts[nxt]:
                ring.append(line(pts[k], pts[nxt]))
        k = nxt
        if k == start:
            break
    else:
        raise GroundSlabQtoError("ring walk did not close")
    return check_ring(ring), len(inner)


def _on_arc(p, c, r, a0, a1, tol):
    d = math.hypot(p[0] - c[0], p[1] - c[1])
    if abs(d - r) > tol:
        return False
    t = math.atan2(p[1] - c[1], p[0] - c[0])
    while t < a0 - 1e-12:
        t += 2 * math.pi
    while t > a0 + 2 * math.pi:
        t -= 2 * math.pi
    return t <= a1 + 1e-9


def ring_area(ring):
    """Exact signed area (Green's theorem; counter-clockwise positive)."""
    s = 0.0
    for e in ring:
        if e[0] == LINE:
            (x0, y0), (x1, y1) = e[1], e[2]
            s += x0 * y1 - x1 * y0
        else:
            _, (cx, cy), r, t0, t1 = e
            s += r * r * (t1 - t0) + r * (cx * (math.sin(t1) - math.sin(t0)) - cy * (math.cos(t1) - math.cos(t0)))
    return s / 2.0


def area(region):
    """Net area of a region: |outer| - sum |holes| (mm2 for mm coordinates)."""
    if not region:
        raise GroundSlabQtoError("empty region")
    for ring in region:
        check_ring(ring)
    outer = abs(ring_area(region[0]))
    holes = math.fsum(abs(ring_area(h)) for h in region[1:])
    if holes >= outer:
        raise GroundSlabQtoError("holes cover the whole region")
    return outer - holes


# ------------------------------------------------------------------ strips
def _swap(region):
    """Mirror across y = x: the Y direction is the X direction of the mirrored region (chords are unchanged)."""
    out = []
    for ring in region:
        r2 = []
        for e in ring:
            if e[0] == LINE:
                r2.append(line((e[1][1], e[1][0]), (e[2][1], e[2][0])))
            else:
                _, (cx, cy), r, t0, t1 = e
                r2.append(arc((cy, cx), r, math.pi / 2 - t0, math.pi / 2 - t1))
        out.append(r2)
    return out


def _in_sweep(t, t0, t1):
    lo, hi = (t0, t1) if t1 >= t0 else (t1, t0)
    while t < lo - 1e-12:
        t += 2 * math.pi
    while t > hi + 1e-12:
        t -= 2 * math.pi
    return lo - 1e-12 <= t <= hi + 1e-12


def _breaks(region):
    """Distribution coordinate (y) values where the chord's branch structure can change."""
    ts = set()
    for ring in region:
        for e in ring:
            ts.add(round(_point(e, 0)[1], 9))
            ts.add(round(_point(e, 1)[1], 9))
            if e[0] == ARC:
                _, (cx, cy), r, t0, t1 = e
                for th in (math.pi / 2, -math.pi / 2):
                    if _in_sweep(th, t0, t1):
                        ts.add(round(cy + r * math.sin(th), 9))
    return sorted(ts)


def _crossings(region, ym):
    """Branches crossing the line y = ym: (x at ym, integral of x over [y0, y1]) callables."""
    out = []
    for ring in region:
        for e in ring:
            if e[0] == LINE:
                (x0, y0), (x1, y1) = e[1], e[2]
                if (y0 < ym < y1) or (y1 < ym < y0):
                    out.append((x0 + (ym - y0) * (x1 - x0) / (y1 - y0), ("L", x0, y0, x1, y1)))
            else:
                _, (cx, cy), r, t0, t1 = e
                v = (ym - cy) / r
                if abs(v) >= 1.0:
                    continue
                for th in (math.asin(v), math.pi - math.asin(v)):
                    if _in_sweep(th, t0, t1):
                        sigma = 1.0 if math.cos(th) > 0 else -1.0
                        out.append((cx + r * math.cos(th), ("A", cx, cy, r, sigma)))
    return sorted(out, key=lambda c: c[0])


def _branch_integral(b, y0, y1):
    if b[0] == "L":
        _, xa, ya, xb, yb = b
        def x(y):
            return xa + (y - ya) * (xb - xa) / (yb - ya)
        return (x(y0) + x(y1)) / 2.0 * (y1 - y0)
    _, cx, cy, r, sigma = b

    def F(u):
        u = max(-r, min(r, u))
        return (u * math.sqrt(max(r * r - u * u, 0.0)) + r * r * math.asin(u / r)) / 2.0
    return cx * (y1 - y0) + sigma * (F(y1 - cy) - F(y0 - cy))


def band_strips(region, direction):
    """Exact bands of one bar direction: [{t0, t1, width_mm, integral_mm2, run_mm, branches}] where t is the
    distribution coordinate (y for X bars, x for Y bars) and run_mm is the mean bar run inside the band."""
    if direction not in DIRECTIONS:
        raise GroundSlabQtoError(f"direction must be one of {DIRECTIONS}: {direction!r}")
    reg = region if direction == X else _swap(region)
    for ring in reg:
        check_ring(ring)
    ts = _breaks(reg)
    out = []
    for y0, y1 in zip(ts, ts[1:]):
        if y1 - y0 <= TOL:
            continue
        cr = _crossings(reg, (y0 + y1) / 2.0)
        if len(cr) % 2:
            raise GroundSlabQtoError(f"odd crossing count at {direction} t = {(y0 + y1) / 2.0}")
        integ = math.fsum(_branch_integral(cr[k + 1][1], y0, y1) - _branch_integral(cr[k][1], y0, y1)
                          for k in range(0, len(cr), 2))
        if integ <= TOL:
            continue
        w = y1 - y0
        out.append({"t0": y0, "t1": y1, "width_mm": w, "integral_mm2": integ, "run_mm": integ / w,
                    "intervals": len(cr) // 2, "branches": sorted({c[1][0] for c in cr})})
    return out


def mesh_direction(region, direction, *, rate_per_m, dia_mm, fraction=1.0):
    """One bar family of a mesh over a region: strips, equivalent count (unrounded), equivalent length, kg."""
    strips = band_strips(region, direction)
    q = SR.rate_strip_length(rate_per_m, [(s["width_mm"], s["run_mm"]) for s in strips], fraction=fraction)
    m = SR.mass(dia_mm, q["length_m"])
    a = area(region)
    cov = SR.strip_coverage([(s["width_mm"], s["run_mm"]) for s in strips], a)
    return {"direction": direction, "strips": strips, "rate_per_m": float(rate_per_m), "fraction": float(fraction),
            "dia_mm": float(dia_mm), "distribution_width_m": q["width_m"], "equivalent_count": q["equivalent_count"],
            "mean_run_m": q["mean_run_m"], "integral_m2": q["integral_m2"], "length_m": q["length_m"],
            "unit_mass_kg_m": m["unit_mass_kg_m"], "kg": m["kg"], "unit_mass_method": m["method"],
            "physical_bbs_count": q["physical_bbs_count"], "coverage": cov}


# ------------------------------------------------------------------ concrete
def slab_concrete(area_m2, thickness_mm):
    """Net area x source thickness (m3). No thickness, no volume (None, never 0)."""
    if thickness_mm is None:
        return None
    if area_m2 < 0 or thickness_mm <= 0:
        raise GroundSlabQtoError(f"area and thickness must be positive: {area_m2!r}, {thickness_mm!r}")
    return float(area_m2) * float(thickness_mm) / 1000.0
