"""EXCAVATION_ZONE_OWNERSHIP_V1 (T-497, research; rule R-T497-1, every villa): one owner zone per excavated m3.

Physical element (ENGINEERING_REASONING_STANDARD s.2.1): an excavation zone (B1-02) is the ground a dig removes; where two
zone plans overlap, the ground there is removed ONCE, by the zone that digs it first in the dig sequence of the drawings
(the deeper / earlier dig: pool envelope, footing pits, other footing zones, then the shallow strips such as the
blinding-only ground-beam trench). Every later zone subtracts the plans of ALL earlier zones, in the plot AND beyond the
plot line, by geometry, never from a list of known interfaces (Checker F-C-T350R4-1: a strip zone that excluded only
the pits zone counted 0.134 m3 already dug by the F10F footing zone and 0.089 m3 over the pits' own beyond-plot strips).

    own_plans(zones, plot) -> {name: {"own": geometry, "in_plot_m2", "beyond_plot_m2", "given_up_m2": {earlier: m2}}}

`zones` is an ordered list of (name, plan) in dig order; plans are shapely geometries in metres. The function refuses a
repeated name, an empty / invalid plan, and a result whose owned plans are not pairwise disjoint or do not add up to the
union of all plans (every m2 once, asserted to TOL). A zone wholly inside earlier zones owns an EMPTY plan (a
calculated zero: the ground is dug, by another zone), which the caller states as such, never as a missing value.
Nothing here names a project, a sheet, a layer or a coordinate.
"""
from __future__ import annotations

from shapely.geometry.base import BaseGeometry
from shapely.ops import unary_union

METHOD_ID = "EXCAVATION_ZONE_OWNERSHIP_V1"
RULE_ID, RULE_VERSION = "R-T497-1", "1.0.0"
TOL = 1e-6


class Refused(ValueError):
    pass


def own_plans(zones, plot: BaseGeometry | None = None):
    names = [n for n, _ in zones]
    if len(set(names)) != len(names):
        raise Refused("ZONE_TWICE: a zone is named twice (one zone, one owner)")
    if not zones:
        raise Refused("NO_ZONE")
    for n, g in zones:
        if g is None or not isinstance(g, BaseGeometry) or g.is_empty or not g.is_valid or g.area <= 0:
            raise Refused(f"BAD_PLAN: zone {n!r} has no valid plan")
    out, earlier = {}, []
    for n, g in zones:
        prior = unary_union([p for _, p in earlier]) if earlier else None
        own = g.difference(prior) if prior is not None else g
        given = {m: g.intersection(out[m]["own"]).area for m, _ in earlier}   # earlier owns are disjoint
        rec = {"own": own, "plan_m2": g.area, "own_m2": own.area,
               "given_up_m2": {m: a for m, a in given.items() if a > TOL}}
        if abs(rec["own_m2"] + sum(given.values()) - rec["plan_m2"]) > TOL * max(1.0, rec["plan_m2"]):
            raise Refused(f"NOT_ONCE: zone {n!r} own + given up is not its plan")
        if plot is not None:
            rec["in_plot_m2"] = own.intersection(plot).area
            rec["beyond_plot_m2"] = own.difference(plot).area
        out[n] = rec
        earlier.append((n, g))
    total = unary_union([g for _, g in zones]).area
    if abs(sum(r["own_m2"] for r in out.values()) - total) > TOL * max(1.0, total):
        raise Refused("NOT_ONCE: the owned plans do not add up to the union of the zone plans")
    owns = [r["own"] for r in out.values()]
    for i in range(len(owns)):
        for j in range(i + 1, len(owns)):
            if owns[i].intersection(owns[j]).area > TOL:
                raise Refused(f"OVERLAP: {names[i]} and {names[j]} both own ground")
    return out


def strip_volume(rec, depth_m):
    """(in-plot m3, beyond-plot m3) of an owned plan dug to a uniform depth (m). depth must be positive."""
    if not isinstance(depth_m, (int, float)) or isinstance(depth_m, bool) or depth_m <= 0:
        raise Refused(f"BAD_DEPTH: {depth_m!r}")
    if "in_plot_m2" not in rec:
        raise Refused("NO_PLOT: the plot line is needed to split in-plot and beyond-plot ground")
    return rec["in_plot_m2"] * depth_m, rec["beyond_plot_m2"] * depth_m


__all__ = ["METHOD_ID", "RULE_ID", "RULE_VERSION", "Refused", "own_plans", "strip_volume"]
