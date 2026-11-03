"""DISPLACEMENT_REMEASURE_V1 (T-484, research, every villa): the solids below existing ground that displace pit
backfill, each measured ONCE at its own position (ERS s.2; element register 'FOUNDATION BACKFILL displacement').

Pure functions (shapely + stdlib), units metres. No project value lives here; every input is passed in.

  neck_below_eg       column neck from its footing TOP to existing ground EG (the part above EG is zone Z2)
  strap_end_volume    the part of a strap beam that lies inside a pit's excavation plan but outside every footing
                      (the projection margin): exact plan geometry x printed section depth
  beam_solid_bounds   ground-beam solids inside the pit zone plan, per category, with
                        - column footprints removed (the neck owns them: R-CONC-OWN-1, precedence column > beam)
                        - every plan point counted once (junction squares and crossings: the deeper category owns)
                        - the high bound stopped at the solid already counted below it (footing + underlay top over a
                          footprint, the pit blinding top over the projection margin): overlap counted once
  union_plan          excavation plan of a scenario of several footings: union, never the sum

Statuses: a missing level / section returns HELD with the reason, never 0; a calculated 0 only from geometry.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from shapely.geometry.base import BaseGeometry
from shapely.ops import unary_union

HELD = "HELD"
CALC = "CALCULATED"


@dataclass
class Result:
    value: float | None = None
    low: float | None = None
    high: float | None = None
    status: str = CALC
    reason: str = ""
    parts: dict = field(default_factory=dict)


def _num(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def neck_below_eg(section_m2, footing_top_m, eg_m, in_env_m2=0.0):
    """Neck volume between the footing top and EG; the share of the section inside another zone (in_env_m2) is that
    zone's. HELD when the section or a level is missing. A footing top at or above EG gives a calculated 0."""
    if not _num(section_m2) or section_m2 <= 0:
        return Result(status=HELD, reason="SECTION_MISSING")
    if not _num(footing_top_m) or not _num(eg_m):
        return Result(status=HELD, reason="LEVEL_MISSING")
    h = max(0.0, eg_m - footing_top_m)
    a = max(0.0, section_m2 - (in_env_m2 or 0.0))
    return Result(value=a * h, parts={"h_m": h, "plan_m2": a})


def strap_end_volume(strap_plan: BaseGeometry, pit_plans: BaseGeometry, footings: BaseGeometry, depth_m,
                     width_drawn_m=None, width_section_m=None):
    """Strap solid inside the pit excavation plan outside every footing (the strap stands on its own soffit; the
    part over a footing, if any, is the footing's junction and is not displacement of backfill here).
    Plan area x section depth; when the printed section width differs from the drawn width, the plan is scaled to
    the printed section (section governs, the drawing gives the position)."""
    if not _num(depth_m) or depth_m <= 0:
        return Result(status=HELD, reason="STRAP_SECTION_MISSING")
    a = strap_plan.intersection(pit_plans).difference(footings).area
    k = 1.0
    if _num(width_drawn_m) and _num(width_section_m) and width_drawn_m > 0:
        k = width_section_m / width_drawn_m
    return Result(value=a * k * depth_m, parts={"plan_m2": a, "width_factor": k})


# category rules for a ground-beam piece: (low rule, high rule)
#   'BLINDING_ONLY'  beam bottom on EG: blinding strip x t below EG (exact)
#   'ZERO'           the whole solid above EG by a printed bound: 0
#   'OPEN'           depth not printed (designer item): low = blinding strip x t (shallowest reading) or 0,
#                    high = the solid down to the solid already counted below it
RULES = {"BLINDING_ONLY", "ZERO", "OPEN_LOW_BLINDING", "OPEN_LOW_ZERO"}


def beam_solid_bounds(pieces, columns: BaseGeometry, zone: BaseGeometry, footprints, margin_floor_m, eg_m=0.0,
                      t_blinding=0.10, priority=None):
    """pieces: [{'id', 'cat', 'rule', 'beam': polygon, 'strip': polygon}] (strip = beam grown by the blinding
    projection at the sides). footprints: [(polygon, top_of_solid_m)] = footing + underlay plans with the level of
    their top (the solid already counted). margin_floor_m: top of the pit blinding (the floor over the margin).
    Returns per category {low, high, beam_m2, strip_m2} and the total; a plan point is owned by the first category
    in `priority` that covers it."""
    if not _num(margin_floor_m) or not _num(eg_m):
        return Result(status=HELD, reason="LEVEL_MISSING")
    for fp, top in footprints:
        if not _num(top):
            return Result(status=HELD, reason="FOOTING_LEVEL_MISSING")
    cats = []
    for p in pieces:
        if p["rule"] not in RULES:
            return Result(status=HELD, reason=f"RULE_UNKNOWN:{p['rule']}")
        if p["cat"] not in cats:
            cats.append(p["cat"])
    order = list(priority or []) + [c for c in cats if c not in (priority or [])]
    taken_b = taken_s = None
    out = {}
    fp_union = unary_union([f for f, _ in footprints]) if footprints else None
    for c in order:
        ps = [p for p in pieces if p["cat"] == c]
        if not ps:
            continue
        rule = ps[0]["rule"]
        b = unary_union([p["beam"] for p in ps]).difference(columns).intersection(zone)
        s = unary_union([p["strip"] for p in ps]).difference(columns).intersection(zone)
        if taken_b is not None:
            b = b.difference(taken_b)
            s = s.difference(taken_s)
        taken_b = b if taken_b is None else taken_b.union(b)
        taken_s = s if taken_s is None else taken_s.union(s)
        if rule == "ZERO":
            lo = hi = 0.0
        elif rule == "BLINDING_ONLY":
            lo = hi = s.area * t_blinding
        else:
            lo = 0.0 if rule == "OPEN_LOW_ZERO" else s.area * t_blinding
            hi = 0.0
            rest = b
            for fp, top in footprints:
                part = rest.intersection(fp)
                hi += part.area * max(0.0, eg_m - top)
            over_margin = b.difference(fp_union) if fp_union is not None else b
            hi += over_margin.area * max(0.0, eg_m - margin_floor_m)
            hi += s.difference(b).area * t_blinding      # the strip's side margins: blinding only
        out[c] = {"low": lo, "high": hi, "beam_m2": b.area, "strip_m2": s.area, "rule": rule}
    lo = sum(v["low"] for v in out.values())
    hi = sum(v["high"] for v in out.values())
    return Result(low=lo, high=hi, value=lo if abs(hi - lo) < 1e-12 else None, parts=out)


def union_plan(plans, clip: BaseGeometry | None = None):
    """Excavation plan of several footings together: the union (an overlap is dug once), optionally clipped."""
    u = unary_union(list(plans))
    if clip is not None:
        u = u.intersection(clip)
    return u.area
