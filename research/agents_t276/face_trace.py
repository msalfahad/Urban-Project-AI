"""T-276 face trace: every boundary piece of a plan solid to exactly ONE drawn member (shapely; any villa, any units).

`trace(owners, boundaries, step)` walks each boundary ring in equal steps (<= step) and gives each step to the member
nearest to its midpoint (ties: SPAN, COLUMN, ARC, PIECE, LIFT_RING in that order), so the pieces of one boundary sum
to its length exactly and no piece is counted for two members. A SPAN owner carries its band frame (unit vector u,
normal n, face offsets lo / hi, face stations ta / tb) so the step is named side A (offset lo), side B (offset hi) or
END; an ARC owner carries its centre and two radii so the step is named CONVEX / CONCAVE. Which SIDE of the building a
face looks into is decided by the boundary it lies on (a panel hole or the outer boundary), never by the face's name.
"""
from __future__ import annotations

import math

KIND_ORDER = ("SPAN", "COLUMN", "ARC", "PIECE", "LIFT_RING")
FACE_TOL = 12.0      # same tolerance (drawing units, mm) as the band pairing of T-141 / T-242
SNAP_TOL = 1.0       # r2 (T-276 rejection 20:59): a drawn member thinner than 1 mm is a drafting offset, not concrete;
#                      an edge end within 1 mm of another member is ON that member's face


def _side(owner, pt):
    kind, _, _, meta = owner
    if kind == "SPAN":
        (ux, uy), (nx, ny) = meta["u"], meta["n"]
        off = pt.x * nx + pt.y * ny
        t = pt.x * ux + pt.y * uy
        st = meta.get("side_t") or {"A": (meta["ta"], meta["tb"]), "B": (meta["ta"], meta["tb"])}
        # r2: the face whose drawn line is NEAREST (r1 gave any step within FACE_TOL of a side line to that side, so a
        # free end face lost 12 mm at each corner to the sides: 0.276 of a 0.300 m end)
        d_end = min(abs(t - meta["ta"]), abs(t - meta["tb"]))
        best = None
        for side, o in (("A", meta["lo"]), ("B", meta["hi"])):
            t0, t1 = st[side]
            d = abs(off - o)
            if t0 - FACE_TOL <= t <= t1 + FACE_TOL and d <= FACE_TOL and d <= d_end and (best is None or d < best[0]):
                best = (d, side)
        return best[1] if best else "END"
    if kind == "ARC":
        cx, cy = meta["centre"]
        rr = math.hypot(pt.x - cx, pt.y - cy)
        return "CONVEX" if abs(rr - meta["r_out"]) < abs(rr - meta["r_in"]) else "CONCAVE"
    return None


def trace(owners, boundaries, step=5.0):
    """owners: [(kind, id, polygon, meta)]; boundaries: [(boundary_id, ring coordinate list)].

    Returns {boundary_id: {"length": L, "max_dist": d, "pieces": {(kind, id, face): length}}}."""
    from shapely.geometry import LineString
    from shapely.strtree import STRtree

    check_owners(owners)
    tree = STRtree([o[2] for o in owners])
    out = {}
    for bid, coords in boundaries:
        ls = LineString(coords)
        L = ls.length
        nstep = max(1, int(math.ceil(L / step)))
        acc, maxd = {}, 0.0
        for k in range(nstep):
            s0, s1 = L * k / nstep, L * (k + 1) / nstep
            pt = ls.interpolate((s0 + s1) / 2.0)
            idx, dist = tree.query_nearest(pt, return_distance=True)
            cand = sorted((owners[i] for i in idx), key=lambda o: (KIND_ORDER.index(o[0]), o[1]))
            o = cand[0]
            maxd = max(maxd, float(dist[0]))
            key = (o[0], o[1], _side(o, pt))
            acc[key] = acc.get(key, 0.0) + (s1 - s0)
        out[bid] = {"length": L, "max_dist": maxd, "pieces": acc}
    return out


def check_owners(owners):
    """Every owner is a declared kind and a real member: a polygon thinner than SNAP_TOL (a drafting offset between
    two outlines, e.g. a column drawn 0.05 mm inside a band edge) is refused as an owner (r2, T-276): its boundary
    steps must fall to the member it lies against."""
    for o in owners:
        if o[0] not in KIND_ORDER:
            raise ValueError(f"owner kind {o[0]!r} not declared")
        if is_sliver(o[2]):
            raise ValueError(f"owner {o[0]} {o[1]} is thinner than {SNAP_TOL} mm: a drafting offset, not a member")


def panels_and_outers(solid, min_hole_area):
    """Holes of the solid at or above min_hole_area are panels (ids by area, largest first); smaller holes are named
    slivers (returned, not traced); every part's exterior is an outer boundary (largest first)."""
    from shapely.geometry import Polygon
    holes, small = [], []
    parts = sorted(getattr(solid, "geoms", [solid]), key=lambda g: -g.area)
    for g in parts:
        for rr in g.interiors:
            P = Polygon(rr)
            (holes if P.area >= min_hole_area else small).append(P)
    return holes, small, [list(g.exterior.coords) for g in parts]


def is_sliver(poly, tol=SNAP_TOL):
    """A drawn piece whose inscribed width is below `tol` (a drafting offset between two outlines) is not a member."""
    return poly.is_empty or poly.buffer(-tol / 2.0).is_empty


def side_interval(intervals, t0, t1, join=1.0):
    """The drawn extent of one band edge: the chain of collinear edge-line intervals (gaps <= join) that covers the
    band's paired overlap t0 .. t1. Raises when no chain covers it (the band would not be drawn on that side)."""
    iv = sorted((min(a, b), max(a, b)) for a, b in intervals)
    chains = []
    for a, b in iv:
        if chains and a <= chains[-1][1] + join:
            chains[-1][1] = max(chains[-1][1], b)
        else:
            chains.append([a, b])
    for a, b in chains:
        if a <= t0 + join and b >= t1 - join:
            return (a, b)
    raise ValueError("no drawn edge chain covers the band overlap")


def close_band_ends(u, lo, hi, t0, t1, ext_a, ext_b, others, reach, tol=SNAP_TOL):
    """r2 (T-276, Checker 2026-10-24 20:59): a member ends on its carrier's drawn face on EACH of its own edges.

    The paired band strip t0 .. t1 is the OVERLAP of its two edge lines (pair_straight): at an end where the edges
    stop at different stations (an oblique or curved carrier, staggered columns) the strip is cut square at the
    shorter edge and the drawn concrete between that cut, the longer edge and the carrier is lost (an invented earth
    pocket plus an invented end face). For each end with stations differing by more than `tol`:
      1. close each edge on its carrier: an edge end within `tol` of other drawn concrete is closed there; an edge
         end in the open is run along its own line to the first other concrete within `reach` (at most one band
         width), else it stays OPEN;
      2. extension = the band rectangle from the overlap end to the farther closed edge end, MINUS all other drawn
         concrete, the part touching the strip; when that is not enclosed, the same with `reach` beyond the farther
         end (room for a re-entrant corner between two carriers);
      3. it is admitted only when ENCLOSED: every part of its boundary lies on the strip, on other concrete or on the
         band's own (closed) edge lines; otherwise the end is reported OPEN with the free length, nothing added.
    Returns [{end, stations: {A, B}, closed: {A, B}, status: CLOSED | OPEN | NONE, poly, area, free_len}]."""
    from shapely.geometry import LineString, Point, Polygon
    from shapely.ops import unary_union

    nx, ny = -u[1], u[0]
    P = lambda t, o: (t * u[0] + o * nx, t * u[1] + o * ny)  # noqa: E731
    strip = Polygon([P(t0, lo), P(t1, lo), P(t1, hi), P(t0, hi)])
    out = []
    for end, sgn, t_ov, ea, eb in (("start", -1.0, t0, ext_a[0], ext_b[0]), ("end", 1.0, t1, ext_a[1], ext_b[1])):
        rec = {"end": end, "stations": {"A": ea, "B": eb}, "closed": {}, "status": "NONE", "poly": None,
               "area": 0.0, "free_len": 0.0}
        if abs(ea - eb) <= tol:
            out.append(rec)
            continue
        for side, o, te in (("A", lo, ea), ("B", hi, eb)):
            if others.distance(Point(P(te, o))) <= tol:
                rec["closed"][side] = te
                continue
            ray = LineString([P(te, o), P(te + sgn * reach, o)])
            hit = ray.intersection(others)
            if hit.is_empty:
                rec["closed"][side] = None
                continue
            ts = [c[0] * u[0] + c[1] * u[1] for g in getattr(hit, "geoms", [hit]) for c in g.coords]
            rec["closed"][side] = min(ts) if sgn > 0 else max(ts)
            rec.setdefault("ray_gap", {})[side] = abs(rec["closed"][side] - te)
        if None in rec["closed"].values():
            rec["status"] = "OPEN"
            rec["free_len"] = None
            out.append(rec)
            continue
        for pad in (0.0, reach):      # first to the farther closed edge end; then room for a re-entrant corner
            far = (max if sgn > 0 else min)(rec["closed"].values()) + sgn * pad
            box = Polygon([P(min(t_ov, far), lo), P(max(t_ov, far), lo), P(max(t_ov, far), hi),
                           P(min(t_ov, far), hi)])
            rest = box.difference(others)
            parts = [g for g in getattr(rest, "geoms", [rest]) if not g.is_empty and g.distance(strip) <= tol
                     and not is_sliver(g, tol)]
            if not parts:
                rec.update(status="NONE", poly=None, area=0.0, free_len=0.0)
                break
            ext = unary_union(parts)
            edges = unary_union([LineString([P(min(t_ov, rec["closed"][k]), o), P(max(t_ov, rec["closed"][k]), o)])
                                 for k, o in (("A", lo), ("B", hi))])
            cover = unary_union([strip.boundary.buffer(tol), others.buffer(tol), edges.buffer(tol)])
            free = ext.boundary.difference(cover).length
            rec.update(area=ext.area, free_len=free, pad=pad)
            if free <= tol:
                rec.update(poly=ext, status="CLOSED")
                break
            rec.update(poly=None, status="OPEN")
        out.append(rec)
    return out
