"""EARTHWORKS_ROUND2_V1 (T-700, lane S, every villa; stdlib only, pure; builds on EARTHWORKS_CENSUS_V1 / R-T695-1).

Three zones the census left open, each measured as a physical element first, then one wiring row per zone.

Z2  PLACED FILL ABOVE EG UNDER THE GROUND SLAB (B1-03 Z2). The soil placed and compacted between the existing ground
    EG and the underside of a slab on grade, inside the building's ground-beam network. Per vertical column of plan:
      * under a slab panel:      depth = underside - EG, underside = FFL - b (floor build-up) - T (slab);
      * under an interior beam:  depth = (top - D - blinding) - EG, never below 0 (a beam reaching EG has no fill);
      * under an exterior beam:  the same over the beam AND its outer blinding projection (its inner projection lies
                                 under a panel);
      * the blinding projections that lie above EG under a panel are solids in that panel's fill (netted once);
      * column / neck faces and lift shafts: 0 (concrete or void from EG up), never fill.
    A panel whose floor level is not established, or a beam whose depth is a designer item, enters by its admissible
    readings; the zone is the envelope of the readings, each computed alone (R-T695-1 a). EG sensitivity is shown by
    re-running the whole zone at EG +- s, never mixed into the range.

PIT A pit whose depth waits on a supplier (lift pit 'as per lift manufacturer'): AT_LEAST only, from the founding rule
    printed on the drawings (underside not less than a stated depth below EG):
      excavation >= plan_own x (founding + every layer printed below the base);
      backfill   >= (plan_own - shell outer plan) x (founding - base thickness - every layer between)   [the base, the
                   screed / blinding and the part of the plan outside the base cancel exactly at projection 0; a
                   drawn projection >= the side build-up keeps the bound valid];
    plan_own = the pit plan minus the part a deeper / other zone already owns (overlapping pits counted once, L-N10-03).
    Never an upper bound and never a value while the depth is a supplier item.

ANNEX (and any trench whose beam depth is a designer item): LOW = free strip x minimum depth (the census AT_LEAST);
    HIGH = free strip x the deepest admissible formation, a ground beam's formation never lying below the formation of
    the foundation it frames into (DATUM, stated with its scenario); an overcounted strip only loosens a HIGH bound.

Rules R-T700-1 .. 3 (PROPOSED, every villa):
  R-T700-1  Z2 is a placed-fill element of its own: per plan column depth from EG to the underside of what sits on it;
            panel levels from the printed FFL chain only; a panel with no printed level or a split level enters by the
            admissible extremes; beam depths by their printed / designer readings; never merged with Z1 backfill.
  R-T700-2  A supplier-depth pit is AT_LEAST from the printed founding minimum; its backfill bound is the plan outside
            the shell x the depth of the base top below EG.
  R-T700-3  A designer-depth trench is bounded above by the foundation formation datum when one is printed or
            owner-accepted (S01 ESTIMATED is labelled); without such a datum it stays AT_LEAST.
Units: metres, m2, m3 only (mm refused through MAX_DEPTH_M / MAX_LEVEL_M).
"""
from __future__ import annotations

import math

VERSION = "EARTHWORKS_ROUND2_V1"
MAX_DEPTH_M = 30.0
MAX_LEVEL_M = 50.0
INF = float("inf")


class Round2Error(ValueError):
    pass


def _num(x, what):
    if isinstance(x, bool) or not isinstance(x, (int, float)) or math.isnan(x):
        raise Round2Error(f"{what}: not a number: {x!r}")
    return float(x)


def _level(x, what):
    if x is None:
        raise Round2Error(f"{what}: missing (HELD: name the level, never 0)")
    v = _num(x, what)
    if math.isinf(v) or abs(v) > MAX_LEVEL_M:
        raise Round2Error(f"{what}: {v} is not a level in metres")
    return v


def layers(depth_m, lift_m):
    d, lift = _num(depth_m, "fill depth"), _num(lift_m, "lift")
    if lift <= 0 or d < 0:
        raise Round2Error("lift must be > 0 and depth >= 0")
    if d > MAX_DEPTH_M:
        raise Round2Error(f"fill depth {d} is not in metres")
    return math.ceil(round(d / lift, 9)) if d > 0 else 0


# ------------------------------------------------------------------------------------------------------ Z2 ----

def panel_fill_depth(ffl_m, buildup_m, slab_t_m, eg_m):
    """depth of placed fill under one panel reading (>= 0). A slab whose underside lies below EG has no Z2 fill (its
    seat is an excavation, another element): returns 0 with that reason, never a negative fill."""
    ffl, b, t, eg = (_level(ffl_m, "FFL"), _num(buildup_m, "build-up"), _num(slab_t_m, "slab T"),
                     _level(eg_m, "existing ground EG"))
    if b < 0 or t <= 0:
        raise Round2Error("build-up >= 0, slab T > 0")
    under = ffl - b - t
    return round(max(0.0, under - eg), 6), round(under, 6)


def panel_term(cell, area_m2, ffl_readings, buildup_m, slab_t_m, eg_m):
    """one panel: [low, high] fill m3 over its admissible FFL readings (one reading = a value)."""
    a = _num(area_m2, f"{cell} area")
    if a < 0:
        raise Round2Error(f"{cell}: negative area")
    if not ffl_readings:
        raise Round2Error(f"{cell}: no FFL reading (HELD: the level is missing, never 0)")
    ds = [panel_fill_depth(f, buildup_m, slab_t_m, eg_m)[0] for f in ffl_readings]
    return {"cell": cell, "area_m2": round(a, 6), "depth_m": [min(ds), max(ds)],
            "fill_m3": [round(a * min(ds), 6), round(a * max(ds), 6)]}


def beam_fill(D, top_m, blinding_m, eg_m, b_m, p_m, L_m, outer_proj=False):
    """placed fill m3 of one ground-beam run at depth D, measured per plan column (see the module docstring)."""
    top, bl, eg = _level(top_m, "beam top"), _num(blinding_m, "blinding"), _level(eg_m, "existing ground EG")
    b, p, L = _num(b_m, "b"), _num(p_m, "projection"), _num(L_m, "L")
    if min(b, p, L, bl) < 0:
        raise Round2Error("negative beam size")
    if math.isinf(D):
        return 0.0
    D = _num(D, "D")
    if D <= 0 or D > MAX_DEPTH_M:
        raise Round2Error(f"beam depth {D} is not a depth in metres")
    bot = top - D - bl                     # blinding bottom
    h = max(0.0, bot - eg)                  # fill under the strip
    a = max(0.0, min(bl, top - D - eg))     # blinding thickness above EG (its projection is a solid in panel fill)
    under_w = b + (p if outer_proj else 0.0)
    proj_w = p if outer_proj else 2 * p
    return under_w * L * h - proj_w * L * a


def beam_term(run, L_m, b_m, top_m, blinding_m, eg_m, p_m, readings, open_above=False, outer_proj=False):
    """[low, high] over the admissible depth readings. open_above (a designer depth bounded only from below by the
    printed section): every D >= min(readings) is admissible; the function is piecewise linear in D, so the extremes are
    at min(readings), the two breakpoints and D -> inf."""
    if not readings:
        raise Round2Error(f"{run}: no depth reading")
    ds = sorted(_num(d, f"{run} D") for d in readings)
    pts = list(ds)
    if open_above:
        top, bl, eg = _level(top_m, "beam top"), _num(blinding_m, "blinding"), _level(eg_m, "EG")
        for k in (top - bl - eg, top - eg):
            if k > ds[0]:
                pts.append(k)
        pts.append(INF)
    vals = [beam_fill(d, top_m, blinding_m, eg_m, b_m, p_m, L_m, outer_proj) for d in pts]
    hs = [0.0 if d == INF else max(0.0, _level(top_m, "beam top") - d - _num(blinding_m, "blinding") -
                                   _level(eg_m, "EG")) for d in pts]
    return {"run": run, "L_m": round(_num(L_m, "L"), 6), "readings": ds, "open_above": open_above,
            "fill_m3": [round(min(vals), 6), round(max(vals), 6)], "under_fill_m": [round(min(hs), 6), round(max(hs), 6)],
            "footprint_m2": round((_num(b_m, "b") + (_num(p_m, "p") if outer_proj else 0.0)) * _num(L_m, "L"), 6)}


def z2_zone(panels, beams, lift_m):
    """panels / beams: the term dicts above. Returns the envelope (low = every term at its low reading, each term's
    readings independent), the compaction footprint and the layer counts per term class."""
    lo = sum(p["fill_m3"][0] for p in panels) + sum(b["fill_m3"][0] for b in beams)
    hi = sum(p["fill_m3"][1] for p in panels) + sum(b["fill_m3"][1] for b in beams)
    if lo < -1e-9:
        raise Round2Error(f"Z2 low {lo:.6f} < 0: a solid exceeds the fill (check the readings)")
    fp_lo = (sum(p["area_m2"] for p in panels if p["depth_m"][0] > 0) +
             sum(b["footprint_m2"] for b in beams if b["under_fill_m"][0] > 0))
    fp_hi = (sum(p["area_m2"] for p in panels if p["depth_m"][1] > 0) +
             sum(b["footprint_m2"] for b in beams if b["under_fill_m"][1] > 0))
    dmax = max([p["depth_m"][1] for p in panels] + [0.0])
    return {"fill_m3": [round(max(lo, 0.0), 6), round(hi, 6)],
            "compaction_footprint_m2": [round(fp_lo, 6), round(fp_hi, 6)],
            "layers_max": layers(dmax, lift_m), "deepest_m": dmax}


# ----------------------------------------------------------------------------------------------------- PIT ----

def own_plan(plan_m2, owned_by_others_m2):
    """the plan a zone owns once: its plan minus every overlap a deeper / other zone already carries (L-N10-03)."""
    a = _num(plan_m2, "plan")
    o = sum(_num(v, f"overlap {k}") for k, v in owned_by_others_m2.items())
    if a < 0 or o < -1e-12 or o - a > 1e-9:
        raise Round2Error(f"overlaps {o} exceed the plan {a}")
    return round(a - o, 6)


def supplier_pit_at_least(plan_own_m2, shell_outer_m2, founding_min_m, base_t_m, layers_below_m, eg_m=0.0,
                          founding_level_m=None):
    """AT_LEAST excavation / backfill of a pit whose depth is a supplier item. founding_min_m: the printed minimum depth
    of the base underside below EG (> 0). layers_below_m: {name: thickness} of every printed layer under the base
    (screed, blinding; an unprinted thickness is left out: it only deepens the cut). founding_level_m (optional): an
    explicit underside level; when given it must respect the printed minimum."""
    a, s = _num(plan_own_m2, "pit plan"), _num(shell_outer_m2, "shell plan")
    f, t = _num(founding_min_m, "founding minimum"), _num(base_t_m, "base T")
    eg = _level(eg_m, "existing ground EG")
    if f <= 0 or f > MAX_DEPTH_M or t <= 0 or t > MAX_DEPTH_M:
        raise Round2Error("founding minimum / base T must be positive depths in metres")
    if not 0 <= s <= a:
        raise Round2Error("shell plan must lie inside the pit plan")
    if founding_level_m is not None and _level(founding_level_m, "founding level") > eg - f + 1e-9:
        raise Round2Error("founding level shallower than the printed minimum")
    below = sum(_num(v, k) for k, v in layers_below_m.items())
    if below < 0:
        raise Round2Error("negative layer")
    exc = a * (f + below)
    base_top_depth = f - t
    bf = (a - s) * max(0.0, base_top_depth)
    return {"kind": "AT_LEAST", "excavation_m3": round(exc, 6), "backfill_m3": round(bf, 6),
            "formation_depth_min_m": round(f + below, 6), "base_top_depth_min_m": round(base_top_depth, 6),
            "upper": None}


# --------------------------------------------------------------------------------------------------- TRENCH ----

def trench_bounds(parts, datum_depth_m):
    """parts: [(piece, free_strip_m2, min_depth_m, max_depth_m or None)]; None = a designer depth: bounded above by
    datum_depth_m (the foundation formation below EG) when a datum exists, else the zone stays AT_LEAST."""
    lo = hi = 0.0
    open_pieces = []
    for nm, a, dmin, dmax in parts:
        a, dmin = _num(a, f"{nm} strip"), _num(dmin, f"{nm} min depth")
        if a < 0 or dmin < 0:
            raise Round2Error(f"{nm}: negative")
        lo += a * dmin
        if dmax is None:
            if datum_depth_m is None:
                open_pieces.append(nm)
                continue
            dmax = datum_depth_m
        dmax = _num(dmax, f"{nm} max depth")
        if dmax > MAX_DEPTH_M:
            raise Round2Error(f"{nm}: depth {dmax} is not in metres")
        if dmax < dmin:
            raise Round2Error(f"{nm}: max depth below min depth")
        hi += a * dmax
    if open_pieces:
        return {"kind": "AT_LEAST", "low_m3": round(lo, 6), "high_m3": None, "open": open_pieces}
    return {"kind": "BOUNDED", "low_m3": round(lo, 6), "high_m3": round(hi, 6), "open": []}


# --------------------------------------------------------------------------------------------------- WIRING ----

WIRING_FIELDS = ("family", "line_id", "element_id", "zone", "state", "bound", "value_m3", "low_m3", "high_m3",
                 "report_class", "basis", "missing_input")
REPORT_CLASS = {"VALUE": "CONFIRMED", "ZERO_BY_GEOMETRY": "CONFIRMED", "RANGE": "HELD", "AT_LEAST": "HELD",
                "BLANK": "HELD"}


def wiring_row(family, line_id, element_id, state, bound, value=None, low=None, high=None, basis="", missing=""):
    """one row of the wiring form (UP-QTY-STATUS-001 report class). Guards: a HELD row never carries a value; a ZERO
    row is CALCULATED with its proof named; a RANGE needs both ends; an AT_LEAST has no upper end; anything held names
    the missing input."""
    if bound not in REPORT_CLASS:
        raise Round2Error(f"{element_id}: bound {bound}")
    if bound == "VALUE":
        if value is None or low is not None or high is not None:
            raise Round2Error(f"{element_id}: VALUE needs a value only")
        _num(value, "value")
    elif bound == "ZERO_BY_GEOMETRY":
        if value != 0.0 or not basis:
            raise Round2Error(f"{element_id}: a calculated 0 needs value 0.0 and its geometric proof")
    else:
        if value is not None:
            raise Round2Error(f"{element_id}: a {bound} row carries a value")
        if bound == "RANGE" and (low is None or high is None or _num(low, "low") > _num(high, "high")):
            raise Round2Error(f"{element_id}: RANGE needs low <= high")
        if bound == "AT_LEAST" and (low is None or high is not None):
            raise Round2Error(f"{element_id}: AT_LEAST has a low end and no high end")
        if bound == "BLANK" and (low is not None or high is not None):
            raise Round2Error(f"{element_id}: BLANK carries a bound")
        if not missing:
            raise Round2Error(f"{element_id}: a held row must name the missing input")
    if f":{family}:" not in element_id:
        raise Round2Error(f"{element_id}: family {family} disagrees")
    return {"family": family, "line_id": line_id, "element_id": element_id, "zone": element_id.split(":", 2)[2],
            "state": state, "bound": bound, "value_m3": value, "low_m3": low, "high_m3": high,
            "report_class": REPORT_CLASS[bound], "basis": basis, "missing_input": missing}
