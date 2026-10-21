"""STAIR GEOMETRY - stair flights, landings and winders from drawn treads and stated levels (generic).

Nothing here chooses a dimension. Every function takes the riser count, riser height, going, width, waist and
landing thicknesses it is given and says what follows from them; whether each input has authority is the caller's
record.

Plan evidence
    detect_tread_runs(segments, pitch, len_tol, min_lines, angle_tol)
        parallel lines of one length at a regular pitch: one run per set of drawn treads. segments are
        (id, (x0, y0), (x1, y1)). Returns runs sorted by angle and offset: {ids, angle, count, pitches, length,
        offsets, along}. A run is a drawing fact, not a riser count: whether each line is a riser, a nosing or a
        landing edge is decided by the caller.
    fan_centre(segments)
        least-squares meeting point of the extended lines of a fan of radial treads (curved flights, winders) with
        its largest miss distance.

Section geometry of a straight flight (profile in the vertical plane along the walking line; s along the run, z up)
    straight_flight(n_risers, riser, going, width, waist, bottom=None, top=None)
        n risers, n - 1 goings between the first and the last riser line; the last riser arrives on the top landing.
        bottom / top: (length, thickness) of the landing plate the flight joins, or None for a plumb cut at the
        first / last riser line (with no top landing the last riser is the face of the member it arrives on). The solid is ONE outline: the steps (monolithic), the waist (normal thickness
        `waist` below the line through the step roots, the usual throat measure) and the landing plates down to
        their own soffits. The soffit is
        continuous: it turns where the waist soffit plane meets each landing soffit plane (before or after the
        riser line, wherever the planes meet), so the waist and a landing are never two prisms over one volume. Returns the outline and
          PLAN_PROJECTED_AREA          flight only: (n - 1) x going x width (landings separately)
          LANDING_PLAN_AREAS           each landing plate: length x width
          INCLINED_WAIST_SURFACE_AREA  soffit of the waist between its two turning points x width
          STAIR_CONCRETE_VOLUME        outline area x width
          FINISHING_TREAD_AREA         (n - 1) x going x width (flight goings; landing finishes are the plan areas)
          FINISHING_RISER_AREA         n x riser x width
          HANDRAIL_PATH_LENGTH         pitch line from the first to the last nosing
    profile_area_outside(outline, rects)
        outline area less its overlap with axis-parallel rectangles (s0, z0, s1, z1): a member another stage owns
        (a landing beam, a floor beam) is taken out once.

Curved and winding flights (plan and soffit only; a helical volume is an approximation and is labelled so)
    annular_flight(r_in, r_out, sweep, n_risers, riser, walk_radius)
        a flight on an annular sector: plan area, going on the walking line, walking-line length, its inclined
        length, and the exact helicoid soffit area between r_in and r_out for the stated rise.
    polygon_area(points)
        shoelace area (winder kites, landings of any outline).

Bars
    rate_density_length(rate_per_m, distribution_width, run)  equivalent length (m) of an n/m bar rate spread over
        a width, each bar `run` long (unrounded; the slab family's rate-density reading).
    rate_count(rate_per_m, distribution_width)  ceil(n x width): a count reading of the same rate.

Stdlib only. No project data.
"""

from __future__ import annotations

import math

TOL = 1e-9


class StairGeometryError(ValueError):
    pass


# ------------------------------------------------------------------ plan evidence
def _ang(a, b):
    return math.degrees(math.atan2(b[1] - a[1], b[0] - a[0])) % 180.0


def detect_tread_runs(segments, pitch=(230.0, 360.0), len_tol=120.0, min_lines=3, angle_tol=0.5):
    if pitch[0] <= 0 or pitch[1] < pitch[0]:
        raise StairGeometryError("pitch range must be positive and ordered")
    groups = {}
    for sid, a, b in segments:
        ln = math.dist(a, b)
        if ln <= TOL:
            continue
        ang = round(_ang(a, b) / angle_tol) * angle_tol % 180.0
        groups.setdefault(ang, []).append((sid, a, b))
    runs = []
    for ang, segs in sorted(groups.items()):
        th = math.radians(ang)
        u, n = (math.cos(th), math.sin(th)), (-math.sin(th), math.cos(th))
        items = []
        for sid, a, b in segs:
            pa, pb = a[0] * u[0] + a[1] * u[1], b[0] * u[0] + b[1] * u[1]
            items.append((a[0] * n[0] + a[1] * n[1], min(pa, pb), max(pa, pb), str(sid)))
        items.sort()
        used = set()
        for i, (o, s0, s1, sid) in enumerate(items):
            if sid in used:
                continue
            run = [(o, s0, s1, sid)]
            for o2, t0, t1, sid2 in items[i + 1:]:
                if sid2 in used:
                    continue
                gap = o2 - run[-1][0]
                if gap > pitch[1]:
                    break
                if gap >= pitch[0] and abs(t0 - s0) <= len_tol and abs(t1 - s1) <= len_tol:
                    run.append((o2, t0, t1, sid2))
            if len(run) >= min_lines:
                used |= {r[3] for r in run}
                runs.append({"ids": [r[3] for r in run], "angle": ang, "count": len(run),
                             "pitches": [run[k + 1][0] - run[k][0] for k in range(len(run) - 1)],
                             "length": s1 - s0, "offsets": [r[0] for r in run], "along": (s0, s1)})
    return runs


def fan_centre(segments):
    """least-squares point closest to every extended line; returns (centre, max distance from a line)."""
    rows = []
    for _, a, b in segments:
        ln = math.dist(a, b)
        if ln <= TOL:
            raise StairGeometryError("zero-length segment")
        nx, ny = -(b[1] - a[1]) / ln, (b[0] - a[0]) / ln
        rows.append((nx, ny, nx * a[0] + ny * a[1]))
    if len(rows) < 2:
        raise StairGeometryError("a fan needs at least two lines")
    sxx = sum(r[0] * r[0] for r in rows)
    sxy = sum(r[0] * r[1] for r in rows)
    syy = sum(r[1] * r[1] for r in rows)
    sxc = sum(r[0] * r[2] for r in rows)
    syc = sum(r[1] * r[2] for r in rows)
    det = sxx * syy - sxy * sxy
    if abs(det) <= TOL:
        raise StairGeometryError("parallel lines have no fan centre")
    cx, cy = (sxc * syy - syc * sxy) / det, (syc * sxx - sxc * sxy) / det
    return (cx, cy), max(abs(r[0] * cx + r[1] * cy - r[2]) for r in rows)


# ------------------------------------------------------------------ polygons
def polygon_area(points):
    pts = list(points)
    if len(pts) < 3:
        raise StairGeometryError("a polygon needs three points")
    s = 0.0
    for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]):
        s += x0 * y1 - x1 * y0
    return abs(s) / 2.0


def _seg_cross(p, q, r, s):
    def o(a, b, c):
        v = (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
        return 0 if abs(v) <= 1e-7 else (1 if v > 0 else -1)
    return o(p, q, r) * o(p, q, s) < 0 and o(r, s, p) * o(r, s, q) < 0


def is_simple(points):
    pts = list(points)
    e = list(zip(pts, pts[1:] + pts[:1]))
    for i in range(len(e)):
        for j in range(i + 2, len(e)):
            if i == 0 and j == len(e) - 1:
                continue
            if _seg_cross(*e[i], *e[j]):
                return False
    return True


def _clip(poly, edge_in, inter):
    out = []
    for a, b in zip(poly, poly[1:] + poly[:1]):
        ia, ib = edge_in(a), edge_in(b)
        if ia and ib:
            out.append(b)
        elif ia and not ib:
            out.append(inter(a, b))
        elif not ia and ib:
            out.append(inter(a, b))
            out.append(b)
    return out


def _clip_rect(poly, s0, z0, s1, z1):
    """Sutherland-Hodgman clip of a simple polygon by an axis-parallel rectangle (convex window)."""
    def xi(x):
        return lambda a, b: (x, a[1] + (b[1] - a[1]) * (x - a[0]) / (b[0] - a[0]))

    def yi(y):
        return lambda a, b: (a[0] + (b[0] - a[0]) * (y - a[1]) / (b[1] - a[1]), y)
    p = list(poly)
    for edge_in, inter in ((lambda q: q[0] >= s0, xi(s0)), (lambda q: q[0] <= s1, xi(s1)),
                           (lambda q: q[1] >= z0, yi(z0)), (lambda q: q[1] <= z1, yi(z1))):
        if not p:
            break
        p = _clip(p, edge_in, inter)
    return p


def profile_area_outside(outline, rects):
    """outline area less its overlap with each rectangle; rectangles must not overlap one another."""
    for i, a in enumerate(rects):
        for b in rects[i + 1:]:
            if min(a[2], b[2]) - max(a[0], b[0]) > TOL and min(a[3], b[3]) - max(a[1], b[1]) > TOL:
                raise StairGeometryError("owned members overlap one another")
    total = polygon_area(outline)
    cut = 0.0
    for s0, z0, s1, z1 in rects:
        if s1 <= s0 or z1 <= z0:
            raise StairGeometryError("empty rectangle")
        c = _clip_rect(outline, s0, z0, s1, z1)
        cut += polygon_area(c) if len(c) >= 3 else 0.0
    return total - cut, cut


# ------------------------------------------------------------------ straight flights
def straight_flight(n_risers, riser, going, width, waist, bottom=None, top=None):
    if n_risers < 2 or int(n_risers) != n_risers:
        raise StairGeometryError("a flight needs a whole number of at least two risers")
    for v, nm in ((riser, "riser"), (going, "going"), (width, "width"), (waist, "waist")):
        if v <= 0:
            raise StairGeometryError(f"{nm} must be positive")
    n = int(n_risers)
    run = (n - 1) * going
    rise = n * riser
    slope = riser / going
    cos = going / math.hypot(going, riser)
    drop = waist / cos                                   # vertical depth of the waist below the root line

    def soffit(s):                                      # line through the step roots, lowered by the waist
        return slope * s - drop

    pts = []
    s0 = soffit(0.0)
    if bottom:
        lb, tb = bottom
        if lb <= 0 or tb <= 0:
            raise StairGeometryError("landing length and thickness must be positive")
        pts.append((-lb, 0.0))
    pts.append((0.0, 0.0))
    for i in range(n - 1):                              # riser i+1 at s = i x going, then its tread
        pts.append((i * going, (i + 1) * riser))
        pts.append(((i + 1) * going, (i + 1) * riser))
    if top:
        lt, tt = top
        if lt <= 0 or tt <= 0:
            raise StairGeometryError("landing length and thickness must be positive")
        pts.append((run, rise))                         # the last riser rises onto the top landing
        pts.append((run + lt, rise))
        pts.append((run + lt, rise - tt))
        s_top = (rise - tt + drop) / slope               # waist soffit meets the top landing soffit
        if s_top > run + lt + TOL:
            raise StairGeometryError("the waist soffit passes below the end of the top landing")
        s_top = min(s_top, run + lt)
        pts.append((s_top, rise - tt))
    else:
        s_top = run                                     # plumb cut at the last riser line: the last riser is
        pts.append((run, soffit(run)))                 # the face of the support the flight arrives on
    if bottom:
        s_bot = (drop - tb) / slope                     # waist soffit meets the bottom landing soffit
        if s_bot < -lb - TOL:
            raise StairGeometryError("the waist soffit passes below the end of the bottom landing")
        if s_bot > s_top + TOL:
            raise StairGeometryError("landing soffits cross the waist: thicken the waist or shorten the flight")
        s_bot = max(s_bot, -lb)
        pts.append((s_bot, -tb))
        pts.append((-lb, -tb))
    else:
        s_bot = 0.0
        pts.append((0.0, s0))                          # plumb cut at the first riser line
    if not is_simple(pts):
        raise StairGeometryError("the flight outline is not simple (waist too thin for the steps?)")
    area = polygon_area(pts)
    soffit_len = math.hypot(s_top - s_bot, slope * (s_top - s_bot))
    out = {"outline": pts, "run": run, "rise": rise, "pitch_deg": math.degrees(math.atan2(riser, going)),
           "PLAN_PROJECTED_AREA": run * width,
           "LANDING_PLAN_AREAS": {"bottom": (bottom[0] * width) if bottom else 0.0,
                                  "top": (top[0] * width) if top else 0.0},
           "INCLINED_WAIST_SURFACE_AREA": soffit_len * width, "inclined_waist_length": soffit_len,
           "STAIR_CONCRETE_VOLUME": area * width, "profile_area": area,
           "FINISHING_TREAD_AREA": (n - 1) * going * width, "FINISHING_RISER_AREA": n * riser * width,
           "HANDRAIL_PATH_LENGTH": math.hypot(run, (n - 1) * riser),
           "soffit_turning_points": (s_bot, s_top)}
    return out


def blondel(riser, going):
    """2R + G (mm): a comfort reading only, never used to choose a riser."""
    return 2.0 * riser + going


def riser_height(total_rise, n_risers):
    if n_risers < 1 or int(n_risers) != n_risers:
        raise StairGeometryError("risers must be a whole number")
    if total_rise <= 0:
        raise StairGeometryError("rise must be positive")
    return total_rise / n_risers


def inclined_length(run, rise):
    if run < 0 or rise < 0:
        raise StairGeometryError("run and rise must not be negative")
    return math.hypot(run, rise)


# ------------------------------------------------------------------ curved flights
def _helicoid_strip(rho, c):
    q = math.sqrt(rho * rho + c * c)
    return 0.5 * (rho * q + c * c * math.log(rho + q))


def annular_flight(r_in, r_out, sweep, n_risers, riser, walk_radius=None):
    if not 0 <= r_in < r_out:
        raise StairGeometryError("radii must satisfy 0 <= r_in < r_out")
    if sweep <= 0 or sweep > 2 * math.pi:
        raise StairGeometryError("sweep must be in (0, 2 pi]")
    if n_risers < 2 or int(n_risers) != n_risers or riser <= 0:
        raise StairGeometryError("a flight needs at least two risers of positive height")
    n = int(n_risers)
    rw = walk_radius if walk_radius is not None else 0.5 * (r_in + r_out)
    if not r_in <= rw <= r_out:
        raise StairGeometryError("walking line outside the flight")
    rise = n * riser
    c = rise / sweep                                    # rise per radian
    walk = sweep * rw
    return {"PLAN_PROJECTED_AREA": 0.5 * sweep * (r_out ** 2 - r_in ** 2), "rise": rise,
            "walking_line_length": walk, "walking_line_going": walk / (n - 1),
            "walking_line_inclined_length": math.hypot(walk, (n - 1) * riser),
            "HELICOID_SOFFIT_AREA": sweep * (_helicoid_strip(r_out, c) - _helicoid_strip(r_in, c)),
            "FINISHING_RISER_AREA": n * riser * (r_out - r_in),
            "FINISHING_TREAD_AREA_FRACTION": (n - 1) / n}


# ------------------------------------------------------------------ bars
def rate_density_length(rate_per_m, distribution_width, run):
    if rate_per_m <= 0 or distribution_width < 0 or run < 0:
        raise StairGeometryError("rate positive, width and run not negative")
    return rate_per_m * distribution_width / 1000.0 * run / 1000.0


def rate_count(rate_per_m, distribution_width):
    if rate_per_m <= 0 or distribution_width < 0:
        raise StairGeometryError("rate positive, width not negative")
    return int(math.ceil(rate_per_m * distribution_width / 1000.0 - 1e-9))
