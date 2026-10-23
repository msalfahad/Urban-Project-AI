"""T-222: close the last HELD block-wall bounds of the blockwork programme (any villa; pure, unwired research module).

Two engineering problems, one module:

A. A CURVED GLAZED BAY in a straight block wall (the plan draws the wall band turning into an arc, the glazing drawn
   between two radial caps). The plan run counts the glazing over the whole arc between the centreline meeting points
   and leaves the two ends as a HELD bound. The ends are not unknown: the wall layer draws both faces of the arc band
   from each full-thickness cap back to the straight wall.
   1. WHAT IS BUILT (`bay_masonry`): masonry = (arc band less the glazing sector between the caps) + (the straight
      bands, less the inside of the arc's inner face where the bay opens) + any extra drawn junction region, inside a
      window around the bay. A cap must span the whole band thickness (r_in .. r_out); a partial cap is a frame line,
      not the end of the glazing, and is refused.
   2. ASSIGN ONCE (`allocate`, the UP-MAS-JUNCTION-001 band rule of T-215 extended to an arc band): a point already
      inside a counted run strip is skipped (counted once); a point in one band -> that wall; in several -> a THROUGH
      band (one drawn continuous across the junction: a stem stops on its face) before a stem, then the wall in whose
      band it lies most centrally (|d| / (t / 2), d to the straight centreline or |r - r_mid| for the arc); in no band
      -> UNASSIGNED, HELD (never dropped, never 0). A stem's band runs to the face it stops on.
   3. HEIGHT (owner Q-60 A, `allocate(..., zones=...)`): each point takes the height of the zone it lies in (storey
      less the depth of the member drawn above it; the deepest member where zones overlap); a point under no zone is
      HELD (ValueError), never a default height.
   Integration is on a raster of step h (default 0.5 mm): the error is about perimeter x h (< 0.0005 m2 for a bay end).

B. A LEAFLESS OPENING'S HEAD and the masonry above it, from views (sections, elevations) that may not show it.
   `view_evidence`: an element drawn in a view is evidence about the opening only when it lies on the opening's own
   wall plane (depth along the view within tol). An element on a NEARER plane whose plan range covers the opening hides
   it: the view is OCCLUDED for that opening (no evidence, no conflict). An element on the same plane that disagrees
   with the plan (a leafed door drawn where the plan draws a leafless gap) is a CONFLICT: both readings are kept and no
   value is chosen. `masonry_above`: width x (top - lintel top); no head -> HELD with its bound, never 0; a CONFLICT
   -> a range; a top set by a member on a nearer plane (an occluding soffit line in an elevation) is refused.

Units: metres only (a thickness outside 0.05 .. 0.60 m raises ValueError). No drawing data in this file.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np
from shapely import contains_xy
from shapely.geometry import Point, Polygon, box
from shapely.ops import unary_union

H_DEFAULT = 0.0005


def _t_ok(t):
    if not (0.05 <= float(t) <= 0.60):
        raise ValueError(f"wall thickness {t} m outside 0.05 .. 0.60 m: metres only")


@dataclass
class StraightBand:
    """A straight wall band: centreline a -> b (metres), thickness t; the band is the strip |d| <= t / 2 over the
    segment's extent (projection 0 .. L)."""
    name: str
    a: tuple
    b: tuple
    t: float
    through: bool = False

    def __post_init__(self):
        _t_ok(self.t)
        if math.dist(self.a, self.b) <= 0:
            raise ValueError(f"{self.name}: zero-length centreline")

    def polygon(self):
        ux, uy = (self.b[0] - self.a[0], self.b[1] - self.a[1])
        L = math.hypot(ux, uy)
        ux, uy = ux / L, uy / L
        nx, ny = -uy, ux
        h = self.t / 2
        a, b = self.a, self.b
        return Polygon([(a[0] + nx * h, a[1] + ny * h), (b[0] + nx * h, b[1] + ny * h),
                        (b[0] - nx * h, b[1] - ny * h), (a[0] - nx * h, a[1] - ny * h)])

    def rel(self, X, Y):
        ux, uy = (self.b[0] - self.a[0], self.b[1] - self.a[1])
        L = math.hypot(ux, uy)
        ux, uy = ux / L, uy / L
        s = (X - self.a[0]) * ux + (Y - self.a[1]) * uy
        d = -(X - self.a[0]) * uy + (Y - self.a[1]) * ux
        inside = (np.abs(d) <= self.t / 2 + 1e-12) & (s >= -1e-12) & (s <= L + 1e-12)
        return inside, np.abs(d) / (self.t / 2)


@dataclass
class ArcBand:
    """A curved wall band: centre, inner and outer face radii (metres)."""
    name: str
    centre: tuple
    r_in: float
    r_out: float
    through: bool = False

    def __post_init__(self):
        if not self.r_out > self.r_in > 0:
            raise ValueError(f"{self.name}: need r_out > r_in > 0")
        _t_ok(self.r_out - self.r_in)

    @property
    def t(self):
        return self.r_out - self.r_in

    @property
    def r_mid(self):
        return (self.r_in + self.r_out) / 2

    def annulus(self, res=4096):
        c = Point(self.centre)
        return c.buffer(self.r_out, resolution=res).difference(c.buffer(self.r_in, resolution=res))

    def rel(self, X, Y):
        r = np.hypot(X - self.centre[0], Y - self.centre[1])
        inside = (r >= self.r_in - 1e-12) & (r <= self.r_out + 1e-12)
        return inside, np.abs(r - self.r_mid) / (self.t / 2)


def _ang(c, p):
    return math.atan2(p[1] - c[1], p[0] - c[0])


def glazing_sector(arc: ArcBand, cap_a, cap_b, tol=0.002, through=None, radial_tol=0.01):
    """The glazing region of the arc band between two caps. Each cap is a pair of points; it must be radial and span the
    full band (one end on r_in, the other on r_out, within tol) - a frame line inside the band is not the glazing end -
    and be radial within radial_tol (tangential offset of its ends at the mid radius; drafted caps are off by a few mm).
    `through` (optional point) picks which of the two sectors between the caps is glazing (default: the one containing
    the direction opposite to the caps' mean, i.e. the bay side away from the straight wall)."""
    angs = []
    for cap in (cap_a, cap_b):
        r = sorted(math.dist(arc.centre, p) for p in cap)
        if abs(r[0] - arc.r_in) > tol or abs(r[1] - arc.r_out) > tol:
            raise ValueError(f"cap {cap} does not span the band {arc.r_in} .. {arc.r_out}: a partial cap is a frame "
                             "line, not the end of the glazing")
        a0, a1 = _ang(arc.centre, cap[0]), _ang(arc.centre, cap[1])
        if abs(math.remainder(a0 - a1, 2 * math.pi)) * arc.r_mid > radial_tol:
            raise ValueError(f"cap {cap} is not radial (tangential offset > {radial_tol} m)")
        angs.append(math.atan2(math.sin(a0) + math.sin(a1), math.cos(a0) + math.cos(a1)))
    a, b = angs
    span = (b - a) % (2 * math.pi)
    if through is not None:
        tp = (_ang(arc.centre, through) - a) % (2 * math.pi)
        if tp > span:
            a, b = b, a
            span = 2 * math.pi - span
    n = 1600
    R = arc.r_out * 3
    wedge = Polygon([arc.centre] + [(arc.centre[0] + R * math.cos(a + span * k / n),
                                     arc.centre[1] + R * math.sin(a + span * k / n)) for k in range(n + 1)])
    g = arc.annulus().intersection(wedge)
    return g, span


def bay_masonry(arc: ArcBand, straights, glazing, window, extra=(), open_side_r=None):
    """Drawn masonry in `window` (a shapely polygon): arc band less glazing, the straight bands less the disc inside
    the arc's open-side face (`open_side_r`, default r_in: the bay opens there), plus `extra` drawn regions."""
    rin = arc.r_in if open_side_r is None else open_side_r
    disc = Point(arc.centre).buffer(rin, resolution=4096)
    parts = [arc.annulus().difference(glazing)]
    for s in straights:
        parts.append(s.polygon().difference(disc).difference(glazing))
    parts += list(extra)
    m = unary_union(parts).intersection(window)
    if m.is_empty or m.area <= 0:
        raise ValueError("no masonry in the window: HELD, never 0")
    return m


@dataclass
class Zone:
    """A height zone in plan: the block height of every point inside it (owner Q-60 A: storey - depth of the member
    above). Where zones overlap the LOWEST height governs (the deepest member)."""
    label: str
    poly: object
    height_m: float


@dataclass
class Allocation:
    by_wall: dict = field(default_factory=dict)      # wall -> {'area_m2', 'length_m', 'gross_m2', 'by_zone'}
    unassigned_m2: float = 0.0
    counted_skipped_m2: float = 0.0
    status: str = "CLOSED"


def allocate(masonry, bands, counted=None, zones=None, h=H_DEFAULT):
    """Assign every point of `masonry` once (see module doc A.2) and, with `zones`, integrate the block height."""
    names = [b.name for b in bands]
    if len(set(names)) != len(names):
        raise ValueError("a wall listed twice")
    x0, y0, x1, y1 = masonry.bounds
    xs = np.arange(x0 + h / 2, x1, h)
    ys = np.arange(y0 + h / 2, y1, h)
    X, Y = np.meshgrid(xs, ys)
    X, Y = X.ravel(), Y.ravel()
    m = contains_xy(masonry, X, Y)
    X, Y = X[m], Y[m]
    cell = h * h
    out = Allocation()
    if counted is not None and not counted.is_empty:
        c = contains_xy(counted, X, Y)
        out.counted_skipped_m2 = float(c.sum() * cell)
        X, Y = X[~c], Y[~c]
    best = np.full(X.shape, -1)
    bestd = np.full(X.shape, np.inf)
    bestp = np.full(X.shape, -1)
    for i, b in enumerate(bands):
        ins, d = b.rel(X, Y)
        p = 1 if b.through else 0
        better = ins & ((p > bestp) | ((p == bestp) & (d < bestd - 1e-12)))
        best[better] = i
        bestd[better] = d[better]
        bestp[better] = p
    out.unassigned_m2 = float((best < 0).sum() * cell)
    hz = None
    if zones:
        hz = np.full(X.shape, np.inf)
        lab = np.full(X.shape, -1)
        for k, z in enumerate(zones):
            zin = contains_xy(z.poly, X, Y)
            lower = zin & (z.height_m < hz)
            hz[lower] = z.height_m
            lab[lower] = k
        if np.isinf(hz[best >= 0]).any():
            raise ValueError("masonry under no member or slab zone: its height is HELD, never a default")
    for i, b in enumerate(bands):
        sel = best == i
        a = float(sel.sum() * cell)
        rec = {"area_m2": a, "length_m": a / b.t}
        if hz is not None:
            rec["gross_m2"] = float((hz[sel] * cell).sum() / b.t)
            rec["by_zone"] = {zones[k].label: float(((lab == k) & sel).sum() * cell) for k in range(len(zones))}
        out.by_wall[b.name] = rec
    if out.unassigned_m2 > 10 * h * (x1 - x0 + y1 - y0):
        out.status = "PARTLY_HELD"
    return out


# --------------------------------------------------------------------------------------------- B. heads and views

@dataclass
class Drawn:
    """An element a view draws over (part of) the opening's plan range: kind (LEAFED_DOOR, HEAD_LINE, FACE, SOFFIT),
    its plan range along the wall (m), the depth of its plane from the view plane (m, along the view direction) and,
    for a HEAD_LINE / SOFFIT, its level (m)."""
    kind: str
    plan_from: float
    plan_to: float
    depth_m: float
    level_m: float | None = None
    ref: str = ""


def view_evidence(opening_from, opening_to, opening_depth_m, drawn, tol=0.05, plan_kind="LEAFLESS"):
    """Classify one view for one opening: ('NOT_SHOWN' | 'OCCLUDED' | 'HEAD' | 'CONFLICT', details).
    An element counts for the opening only on its own plane (|depth - opening_depth| <= tol) and over its plan range;
    a nearer element covering the whole range hides the opening (OCCLUDED); a leafed door on the opening's own plane
    where the plan draws a leafless opening is a CONFLICT (both kept)."""
    if opening_to <= opening_from:
        raise ValueError("opening range must be increasing")
    same, nearer = [], []
    for e in drawn:
        ov = min(e.plan_to, opening_to) - max(e.plan_from, opening_from)
        if ov <= 0:
            continue
        if abs(e.depth_m - opening_depth_m) <= tol:
            same.append(e)
        elif e.depth_m < opening_depth_m - tol:
            nearer.append((e, ov))
    if not same:
        cover = sum(ov for _, ov in nearer)
        if nearer and cover >= (opening_to - opening_from) - tol:
            return "OCCLUDED", [e.ref for e, _ in nearer]
        return "NOT_SHOWN", []
    if plan_kind == "LEAFLESS" and any(e.kind == "LEAFED_DOOR" for e in same):
        return "CONFLICT", [e.ref for e in same]
    heads = sorted({round(e.level_m, 3) for e in same if e.kind == "HEAD_LINE" and e.level_m is not None})
    if len(heads) == 1:
        return "HEAD", heads[0]
    if len(heads) > 1:
        return "CONFLICT", heads
    return "NOT_SHOWN", []


def masonry_above(width_m, top_level_m, head_level_m=None, lintel_depth_m=None, head_range=None,
                  top_source_depth_m=None, wall_depth_m=None, tol=0.05):
    """Masonry above an opening (m2 of wall face): width x (top - (head + lintel depth)).
    - no head (None) and no head_range -> ('HELD', (0, width x (top - lintel)))  bound only, never 0 as a value;
    - head_range (a CONFLICT kept for the designer) -> ('RANGE', (lo, hi));
    - a top level read from a member on a nearer plane than the wall (an occluding soffit in an elevation) is refused."""
    if width_m <= 0:
        raise ValueError("width must be > 0")
    if top_source_depth_m is not None and wall_depth_m is not None and top_source_depth_m < wall_depth_m - tol:
        raise ValueError("the top level comes from a member in front of the wall (occluding soffit), not from the "
                         "member above the opening: refused")
    ld = 0.0 if lintel_depth_m is None else float(lintel_depth_m)
    if head_range is not None:
        lo_h, hi_h = sorted(head_range)
        vals = [width_m * (top_level_m - (h + ld)) for h in (hi_h, lo_h)]
        if min(vals) < 0:
            raise ValueError("head above the top level")
        return "RANGE", (round(vals[0], 4), round(vals[1], 4))
    if head_level_m is None:
        return "HELD", (0.0, round(width_m * (top_level_m - ld), 4))
    v = width_m * (top_level_m - (head_level_m + ld))
    if v < -1e-9:
        raise ValueError("head above the top level")
    return "VALUE", round(max(v, 0.0), 4)
