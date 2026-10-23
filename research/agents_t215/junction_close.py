"""T-215: close a HELD wall-end bound from the drawn faces (any villa; pure, unwired research module).

Problem (T-108 r2, MASONRY_CENTRELINE_V2): where a wall end meets another wall at an oblique angle (45 deg bends, a
diagonal stem against a vertical wall and a through wall, a wall running into a column) the physical module cannot
close the end as a clean T or L, so it records 'up to max_lm more is not measured' and the ledger carries a HELD bound
(0 .. max, never added). The masonry itself is not unknown: the plan draws both faces of every wall up to the junction.

Engineering basis (ERS s.2 steps 1-3; s.3 'one element, counted once'):
  1. WHAT IS BUILT: the masonry in plan near a junction is the region the drawn face lines enclose, less any column
     (concrete, UP-COL-ORIENT-001). Built from the drawing (`masonry_from_faces`), never from a run length.
  2. MEASURE: block area per wall = plan area of its share / thickness = the physical length (for a straight piece
     between two cuts, area / t is exactly its centreline length whatever the angle of the cuts).
  3. ASSIGN ONCE (rule proposal UP-MAS-JUNCTION-001 v1.0.0, any villa): every point of the junction masonry belongs to
     exactly one wall: (a) a point inside one wall band only -> that wall; (b) a point inside several bands -> the
     THROUGH wall if one is drawn continuous across the junction (a stem stops on its face, the V2 T rule); (c) else
     (bends, oblique L, Y nodes) the wall in whose band the point lies most centrally, |d| / (t / 2) smallest (at an L
     corner each wall gets half the corner parallelogram, the same areas as the mitre through the inner and outer
     corners, because a parallelogram's diagonals cut it into four equal triangles; any thicknesses; mirror / rotation
     invariant);
     (d) masonry inside no band is UNASSIGNED and stays HELD (never dropped, never 0); two crossing through walls are
     refused (a crossing is a different rule).
  4. CLOSE: per wall, delta = share / t - the length the run already counts inside the same window. The cluster
     residual (masonry area - sum t x counted length) is the unmeasured piece; a set of extra lengths claimed by another
     method (a hand run, another wall's bound) whose area exceeds it counts a piece twice and is refused (`check_claims`).
  5. HEIGHT (owner Q-60 A): the gross m2 change = (integral of the block height over the wall's share - over the strip
     its run already counts) / t, the height being storey - depth of the member drawn above each point (the deepest
     where two overlap), the slab height elsewhere; with no member and no slab given the piece is HELD
     (`gross_change`, `height_integral`).

Units: metres only; a thickness outside 0.05 .. 0.60 m (for example millimetres) raises ValueError.
No drawing data in this file; callers pass geometry read at run time.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from shapely.geometry import LineString, Polygon, box
from shapely.ops import polygonize, unary_union

AREA_TOL = 1e-6          # m2: 1 mm x 1 m; below it a piece is rounding
T_MIN, T_MAX = 0.05, 0.60


@dataclass(frozen=True)
class Wall:
    """One wall arm at a junction. `node`: a point on the wall centreline at the junction; `u`: the direction pointing
    AWAY from the junction (normalised here); `window_s`: distance from `node` along u to the window cut (a full-width
    masonry section inside the run); `counted_s`: distance from `node` along u to the end the run ALREADY counts
    (negative when the run overshoots the node point); `through`: drawn continuous across the junction."""
    wall_id: str
    t_m: float
    node: tuple
    u: tuple
    window_s: float
    counted_s: float
    through: bool = False
    reach_m: float | None = None

    def check(self):
        if not (T_MIN <= float(self.t_m) <= T_MAX):
            raise ValueError(f"{self.wall_id}: thickness {self.t_m} outside {T_MIN} .. {T_MAX} m (units must be metres)")
        n = math.hypot(*self.u)
        if n < 1e-12:
            raise ValueError(f"{self.wall_id}: zero direction")
        if not self.window_s > 0:
            raise ValueError(f"{self.wall_id}: the window cut must lie beyond the node (window_s > 0)")
        return self


def _unit(v):
    n = math.hypot(*v)
    return (v[0] / n, v[1] / n)


def _frame(w: Wall):
    u = _unit(w.u)
    n = (-u[1], u[0])
    return u, n


def strip(w: Wall) -> Polygon:
    """The wall band from beyond the node (reach) to the window cut."""
    w.check()
    u, n = _frame(w)
    h = float(w.t_m) / 2
    r = w.reach_m if w.reach_m is not None else 4 * float(w.t_m)
    pts = []
    for s, o in ((-r, -h), (w.window_s, -h), (w.window_s, h), (-r, h)):
        pts.append((w.node[0] + u[0] * s + n[0] * o, w.node[1] + u[1] * s + n[1] * o))
    return Polygon(pts)


def _d(w: Wall, x, y):
    """Signed distance to the centreline / half thickness, as linear coefficients (a, b, c): a x + b y + c."""
    u, n = _frame(w)
    h = float(w.t_m) / 2
    return (n[0] / h, n[1] / h, -(n[0] * w.node[0] + n[1] * w.node[1]) / h)


def _halfplane(a, b, c, lt: bool, bbox):
    """{a x + b y + c < 0} (lt) or {> 0}, clipped to bbox (x0, y0, x1, y1)."""
    B = box(*bbox)
    if abs(a) < 1e-15 and abs(b) < 1e-15:
        return B if ((c < 0) == lt) else Polygon()
    big = 4 * max(bbox[2] - bbox[0], bbox[3] - bbox[1]) + 10
    nn = math.hypot(a, b)
    nx, ny = a / nn, b / nn
    cx, cy = (bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2
    # foot of the line nearest the bbox centre
    k = (a * cx + b * cy + c) / (nn * nn)
    p0 = (cx - a * k, cy - b * k)
    sgn = -1.0 if lt else 1.0           # side where f < 0 is along -normal
    v = (-ny, nx)
    q = [(p0[0] + v[0] * big, p0[1] + v[1] * big), (p0[0] - v[0] * big, p0[1] - v[1] * big)]
    q += [(q[1][0] + sgn * nx * big, q[1][1] + sgn * ny * big), (q[0][0] + sgn * nx * big, q[0][1] + sgn * ny * big)]
    return Polygon(q).intersection(B)


def beats(j: Wall, i: Wall, bbox):
    """Region where wall j takes a point that lies in both bands (rule 3 b / c)."""
    if j.through and i.through:
        raise ValueError(f"{j.wall_id} and {i.wall_id} are both THROUGH: a crossing is not closed by this rule")
    if j.through:
        return box(*bbox)
    if i.through:
        return Polygon()
    aj, bj, cj = _d(j, 0, 0)
    ai, bi, ci = _d(i, 0, 0)
    # |dj| < |di|  <=>  (dj - di)(dj + di) < 0
    m1 = (aj - ai, bj - bi, cj - ci)
    p1 = (aj + ai, bj + bi, cj + ci)
    r1 = _halfplane(*m1, True, bbox).intersection(_halfplane(*p1, False, bbox))
    r2 = _halfplane(*m1, False, bbox).intersection(_halfplane(*p1, True, bbox))
    return unary_union([r1, r2])


def masonry_from_faces(face_segments, walls, closing_segments=(), columns=(), pad=0.002):
    """The drawn masonry of a junction window: the closed cells formed by the drawn face segments, the window cuts of
    each wall (its band width, padded) and any closing segment (a through wall's near face drawn with a gap), whose
    representative point lies inside a window-clipped band; columns cut out. Returns a (Multi)Polygon."""
    lines = [LineString(s) for s in face_segments] + [LineString(s) for s in closing_segments]
    for w in walls:
        u, n = _frame(w.check())
        h = float(w.t_m) / 2 + pad
        c = (w.node[0] + u[0] * w.window_s, w.node[1] + u[1] * w.window_s)
        lines.append(LineString([(c[0] - n[0] * h, c[1] - n[1] * h), (c[0] + n[0] * h, c[1] + n[1] * h)]))
    bands = unary_union([strip(w) for w in walls])
    cells = [p for p in polygonize(unary_union(lines)) if bands.contains(p.representative_point())]
    m = unary_union(cells) if cells else Polygon()
    if columns:
        m = m.difference(unary_union([Polygon(c) for c in columns]))
    return m


def close_junction(masonry, walls):
    """Partition the junction masonry among the walls (rule 3) and close each wall's end. Returns a dict with per-wall
    share_m2, share_len_m, counted_len_m, delta_m, the unassigned area (HELD), the residual and the checks."""
    walls = [w.check() for w in walls]
    ids = [w.wall_id for w in walls]
    if len(set(ids)) != len(ids):
        raise ValueError("a wall appears twice at one junction")
    if masonry is None or masonry.is_empty:
        raise ValueError("no drawn masonry: the junction is HELD, never 0")
    x0, y0, x1, y1 = masonry.bounds
    bb = (x0 - 1, y0 - 1, x1 + 1, y1 + 1)
    S = {w.wall_id: strip(w) for w in walls}
    regions = {}
    for i in walls:
        r = masonry.intersection(S[i.wall_id])
        for j in walls:
            if j is i:
                continue
            lost = S[j.wall_id].intersection(beats(j, i, bb))
            r = r.difference(lost)
        regions[i.wall_id] = r
    union = unary_union(list(regions.values()))
    unassigned = masonry.difference(union).area
    overl = 0.0
    for a in range(len(walls)):
        for b in range(a + 1, len(walls)):
            overl += regions[ids[a]].intersection(regions[ids[b]]).area
    if overl > AREA_TOL:
        raise ValueError(f"assignment overlaps by {overl:.6f} m2: a piece would be counted twice")
    out = {"walls": {}, "masonry_m2": masonry.area, "unassigned_m2": unassigned, "overlap_m2": overl}
    counted = 0.0
    for w in walls:
        t = float(w.t_m)
        share = regions[w.wall_id].area
        cl = w.window_s - w.counted_s
        counted += cl * t
        out["walls"][w.wall_id] = {"t_m": t, "share_m2": share, "share_len_m": share / t, "counted_len_m": cl,
                                   "delta_m": share / t - cl}
    out["residual_m2"] = masonry.area - counted
    out["_regions"] = regions
    out["status"] = "CLOSED" if unassigned <= AREA_TOL else "PARTLY_HELD"
    s = sum(v["share_m2"] for v in out["walls"].values())
    if abs(s + unassigned - masonry.area) > AREA_TOL:
        raise ValueError("partition does not add up to the drawn masonry")
    return out


def counted_strip(w: Wall) -> Polygon:
    """The full-width piece the run already counts inside the window (from its counted end to the window cut)."""
    u, n = _frame(w.check())
    h = float(w.t_m) / 2
    return Polygon([(w.node[0] + u[0] * s + n[0] * o, w.node[1] + u[1] * s + n[1] * o)
                    for s, o in ((w.counted_s, -h), (w.window_s, -h), (w.window_s, h), (w.counted_s, h))])


def height_integral(region, members, default_h):
    """Integral of the block height over a plan region (m3 of wall volume per metre of thickness): height = storey
    height - depth of the member above (owner Q-60 A). `members`: [(polygon, height_m)] (a point under several takes the
    LOWEST height: the deepest member sits on the wall); outside every member the slab height `default_h`; None ->
    ValueError (a piece with no member drawn above is HELD, never defaulted)."""
    if region.is_empty:
        return 0.0
    tot, left = 0.0, region
    for poly, h in sorted(members, key=lambda m: m[1]):
        part = left.intersection(poly)
        if part.area > 0:
            tot += part.area * float(h)
            left = left.difference(poly)
    if left.area > AREA_TOL:
        if default_h is None:
            raise ValueError("part of the piece has no member drawn above it: HELD")
        tot += left.area * float(default_h)
    return tot


def gross_change(walls, result, members, default_h):
    """Per wall: gross block m2 change = (integral of h over its share - over its counted strip) / t, so the area and
    the height of the closed piece both come from the drawings."""
    out = {}
    for w in walls:
        t = float(w.t_m)
        a = height_integral(result["_regions"][w.wall_id], members, default_h)
        b = height_integral(counted_strip(w), members, default_h)
        out[w.wall_id] = (a - b) / t
    return out


def check_claims(result, claims):
    """Refuse extra lengths (wall_id -> m) whose area exceeds the unmeasured masonry: the same piece counted twice."""
    have = max(result["residual_m2"], 0.0)
    want = 0.0
    for wid, L in claims.items():
        if wid not in result["walls"]:
            raise ValueError(f"{wid} is not at this junction")
        if L < 0:
            raise ValueError("a claim is a positive extra length")
        want += L * result["walls"][wid]["t_m"]
    if want > have + AREA_TOL:
        raise ValueError(f"claimed {want:.6f} m2 > unmeasured {have:.6f} m2: a junction piece counted twice")
    return True
