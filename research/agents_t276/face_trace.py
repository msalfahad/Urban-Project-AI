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


def _side(owner, pt):
    kind, _, _, meta = owner
    if kind == "SPAN":
        (ux, uy), (nx, ny) = meta["u"], meta["n"]
        off = pt.x * nx + pt.y * ny
        t = pt.x * ux + pt.y * uy
        inside = meta["ta"] - FACE_TOL <= t <= meta["tb"] + FACE_TOL
        if inside and abs(off - meta["lo"]) <= FACE_TOL:
            return "A"
        if inside and abs(off - meta["hi"]) <= FACE_TOL:
            return "B"
        return "END"
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

    for o in owners:
        if o[0] not in KIND_ORDER:
            raise ValueError(f"owner kind {o[0]!r} not declared")
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
