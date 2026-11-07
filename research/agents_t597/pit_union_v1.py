"""T-597 PIT_UNION_V1: the plan side of B1 excavation zones (every villa; research only, unwired).

Physical element: the excavated footprint at formation of each zone. For an isolated footing the pit plan is the
footing outline grown by the printed blinding projection p on every side (a rectangle grown with square corners: the
blinding is a slab with straight edges). Neighbouring pits that overlap are ONE dig: their overlap is taken once
(defect L-N10-03). A zone list is owned in dig order (R-T497-1): each later zone gives up every m2 an earlier zone owns.
The depth is NOT part of this module: every result is a plan (m2) only; a depth stays with its own source / hold.

Rules (R-T597-1 .. 4, PROPOSED; provenance T-597, Q-21 C, R-EXC-LEDGER-1, R-T497-1, L-N10-03):
  R-T597-1  pit plan = outline grown by the PRINTED projection p; p missing -> the pit is HELD (never p = 0, never a
            default). An outline missing or open -> HELD by name, never 0 and never left out silently.
  R-T597-2  union, not sum: a zone plan is the exact union of its pits; sum - union = overlap, stated beside in m2 and
            by pair; summing pits is refused as the zone plan.
  R-T597-3  plot clip: the in-plot part is the plan inside the plot polygon; the beyond-plot part is stated apart (held
            with its own item), never dropped and never added into the in-plot figure.
  R-T597-4  ownership: earlier zones (dig order) own their plan first; the given-up m2 per earlier zone is stated;
            own + given-up = plan (asserted).

Units: input in metres (callers convert mm once, `unit` is required: 'm' or 'mm'). Output m2 at 6 dp.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

from shapely import affinity
from shapely.geometry import Polygon, box
from shapely.ops import unary_union

SCALE = {"m": 1.0, "mm": 0.001}


class PitUnionError(ValueError):
    pass


@dataclass
class Pit:
    """A footing outline: centre (cx, cy), size (L along its own x, W), rotation deg about the centre.
    `outline` None (or L / W None) = the outline is not drawn -> HELD."""
    pid: str
    cx: float | None
    cy: float | None
    L: float | None
    W: float | None
    rot_deg: float = 0.0
    projection: float | None = None     # printed blinding projection each side; None -> HELD
    unit: str = "m"
    ref: str = ""


@dataclass
class ZoneResult:
    zone: str
    pits_valued: list = field(default_factory=list)
    pits_held: list = field(default_factory=list)       # (pid, reason)
    per_pit_m2: dict = field(default_factory=dict)
    sum_m2: float | None = None
    union_m2: float | None = None
    overlap_m2: float | None = None
    overlap_pairs: list = field(default_factory=list)    # (a, b, m2)
    in_plot_m2: float | None = None
    beyond_plot_m2: float | None = None
    given_up_m2: dict = field(default_factory=dict)      # earlier zone -> m2 (in plot)
    own_in_plot_m2: float | None = None
    geometry: object = None                              # shapely, in plot, before ownership


def _f(v, unit):
    if unit not in SCALE:
        raise PitUnionError(f"undeclared unit {unit!r}")
    return None if v is None else float(v) * SCALE[unit]


def pit_polygon(p: Pit):
    """Grown outline (m) or None when HELD; raises on a non-physical size."""
    s = SCALE.get(p.unit)
    if s is None:
        raise PitUnionError(f"{p.pid}: undeclared unit {p.unit!r}")
    if None in (p.cx, p.cy, p.L, p.W) or p.projection is None:
        return None
    L, W, pr = p.L * s, p.W * s, p.projection * s
    if L <= 0 or W <= 0 or pr < 0:
        raise PitUnionError(f"{p.pid}: non-physical size L {L} W {W} projection {pr}")
    cx, cy = p.cx * s, p.cy * s
    g = box(cx - L / 2 - pr, cy - W / 2 - pr, cx + L / 2 + pr, cy + W / 2 + pr)
    if p.rot_deg:
        g = affinity.rotate(g, p.rot_deg, origin=(cx, cy))
    return g


def zone_plan(zone: str, pits: list[Pit], plot=None, earlier: list | None = None) -> ZoneResult:
    """earlier: [(zone name, shapely polygon in m, already the owned plan of that zone)] in dig order."""
    r = ZoneResult(zone=zone)
    polys = {}
    for p in pits:
        try:
            g = pit_polygon(p)
        except PitUnionError:
            raise
        if g is None:
            why = "projection not printed" if p.projection is None else "outline not drawn"
            r.pits_held.append((p.pid, why))
            continue
        if p.pid in polys:
            raise PitUnionError(f"pit {p.pid} listed twice")
        polys[p.pid] = g
        r.per_pit_m2[p.pid] = round(g.area, 6)
    r.pits_valued = sorted(polys)
    if not polys:
        return r                                   # nothing valued: every figure stays None (HELD), never 0
    ids = sorted(polys)
    for i, a in enumerate(ids):
        for b in ids[i + 1:]:
            ov = polys[a].intersection(polys[b]).area
            if ov > 1e-9:
                r.overlap_pairs.append((a, b, round(ov, 6)))
    u = unary_union(list(polys.values()))
    r.sum_m2 = round(sum(g.area for g in polys.values()), 6)
    r.union_m2 = round(u.area, 6)
    r.overlap_m2 = round(r.sum_m2 - r.union_m2, 6)
    inside = u if plot is None else u.intersection(plot)
    r.in_plot_m2 = round(inside.area, 6)
    r.beyond_plot_m2 = round(u.area - inside.area, 6) if plot is not None else 0.0
    own = inside
    for name, g in (earlier or []):
        gi = own.intersection(g).area
        r.given_up_m2[name] = round(gi, 6)
        own = own.difference(g)
    r.own_in_plot_m2 = round(own.area, 6)
    tot = r.own_in_plot_m2 + sum(r.given_up_m2.values())
    if abs(tot - r.in_plot_m2) > 2e-6:
        raise PitUnionError(f"{zone}: own + given-up {tot} != in-plot {r.in_plot_m2} (an earlier zone overlaps another)")
    r.geometry = own
    return r


def convex_offset_area(area: float, perimeter: float, d: float, turning_rad: float = 2 * math.pi) -> float:
    """Exact area of a convex outline grown by d (Steiner): A + P d + (turning / 2) d^2; for a closed convex outline
    the total turning is 2 pi. Used to cross-check a polygonised envelope."""
    return area + perimeter * d + turning_rad / 2 * d * d


def refuse_sum_as_zone(sum_m2: float, union_m2: float) -> None:
    """R-T597-2: a zone plan given as the sum of overlapping pits is refused."""
    if sum_m2 - union_m2 > 1e-6:
        raise PitUnionError(f"sum {sum_m2} exceeds the union {union_m2}: overlaps counted twice")
