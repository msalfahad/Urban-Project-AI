"""STAIR SCENARIO CHECKS - what a proposed riser count implies against a printed level, how it is set out on site,
how finished and structural levels relate through separately stated finish layers, and exact section quantities of a
straight flight (generic).

Nothing here chooses a riser count, a level, a finish or a thickness. Every function takes what it is given and says
what follows; whether each input has authority is the caller's record. Levels and thicknesses are in mm.

Landings
    landing_reach(bottom_mm, top_mm, n, landing_mm, tol_mm=0.5)
        where a printed landing level falls in a stair of n uniform risers: the exact riser index k* = (L - b) / h,
        the riser boundaries either side and their levels, whether L is reachable (the nearest boundary within tol)
        and the level error of the nearest boundary.
    uniform_counts_for_landing(bottom_mm, top_mm, landing_mm, n_values, tol_mm=0.5)
        every count n among n_values whose uniform riser lands on the printed level (within tol), with the index.
    split_risers(bottom_mm, top_mm, landing_mm, k_below, n_above)
        the two unequal risers that would keep k_below risers below and n_above risers above a fixed landing.

Setting out
    setting_out(bottom_mm, top_mm, n, step_mm=1.0)
        exact cumulative levels b + k h at full precision, the same levels rounded to `step` for setting out, the
        individual risers that follow from the rounded levels and the largest deviation. Rounding the levels (not
        the risers) keeps every level within step / 2 of exact and never accumulates.
    rounded_riser_drift(rise_mm, n, riser_mm)
        n x riser - rise: the error at the top when one rounded riser height is repeated n times.

Finishes and datums
    build_up(layers)
        the sum of named layer thicknesses; None when any layer is unknown (None).
    datum_levels(bottom_ffl_mm, top_ffl_mm, n, landing_after, floor_bottom, floor_top, tread, landing=None)
        an explicit datum model, written separately from stair_riser_schedule: finished tread k = FFL_b + k h;
        the structural slab levels SSL = FFL - floor build-up; the concrete under a tread = finished tread - tread
        build-up (landing build-up where riser k arrives on a landing; the top-floor build-up for the last riser).
        Returns every concrete level and riser, the first and the last, and the closure SSL_t - SSL_b.

Exact quantities of a straight flight between plumb cuts (s along the run from the first riser line, z up from the
finished level the first riser starts at; the soffit is the line through the step roots lowered by waist / cos)
    flight_section_volume(n, riser, going, width, waist, s0=0.0, s1=None)
        the integral of (stepped top - inclined soffit) x width over [s0, s1] (mm3), exact piece by piece: the whole
        flight for [0, (n - 1) going], or the part of a flight over a beam band.
    solid_steps_volume(n, riser, going, width)
        steps built solid on the lower level: the n - 1 treads at k x riser above it, each one going deep (mm3).
    winder_bounds(tread_areas_mm2, riser, waist, walking_going)
        two readings of a winder turn whose soffit is not drawn: the plane-equivalent A (t / cos + h / 2) for a
        soffit following the walking-line pitch, and a flat-soffit bound sum A_i (i h + t) (treads i = 0, 1, ...
        above the first winder tread). Both mm3; neither is exact.

Stdlib only. No project data.
"""

from __future__ import annotations

import math

TOL = 1e-9


class ScenarioCheckError(ValueError):
    pass


def _uniform(bottom_mm, top_mm, n):
    if n < 1 or int(n) != n:
        raise ScenarioCheckError("risers must be a whole number")
    rise = top_mm - bottom_mm
    if rise <= 0:
        raise ScenarioCheckError("the top level must be above the bottom level")
    return rise, rise / n


# ------------------------------------------------------------------ landings
def landing_reach(bottom_mm, top_mm, n, landing_mm, tol_mm=0.5):
    rise, h = _uniform(bottom_mm, top_mm, n)
    if not bottom_mm < landing_mm < top_mm:
        raise ScenarioCheckError("the landing must lie between the two floors")
    k_star = (landing_mm - bottom_mm) / h
    k_lo, k_hi = math.floor(k_star + TOL), math.ceil(k_star - TOL)
    k_near = min((k_lo, k_hi), key=lambda k: (abs(bottom_mm + k * h - landing_mm), k))
    err = bottom_mm + k_near * h - landing_mm
    return {"riser_mm": h, "k_exact": k_star, "k_below": k_lo, "k_above": k_hi,
            "level_below_mm": bottom_mm + k_lo * h, "level_above_mm": bottom_mm + k_hi * h,
            "k_nearest": k_near, "nearest_error_mm": err, "reachable": abs(err) <= tol_mm}


def uniform_counts_for_landing(bottom_mm, top_mm, landing_mm, n_values, tol_mm=0.5):
    out = []
    for n in n_values:
        r = landing_reach(bottom_mm, top_mm, n, landing_mm, tol_mm)
        if r["reachable"]:
            out.append((n, r["k_nearest"], r["riser_mm"]))
    return out


def split_risers(bottom_mm, top_mm, landing_mm, k_below, n_above):
    if k_below < 1 or n_above < 1:
        raise ScenarioCheckError("both parts need at least one riser")
    if not bottom_mm < landing_mm < top_mm:
        raise ScenarioCheckError("the landing must lie between the two floors")
    hb, ha = (landing_mm - bottom_mm) / k_below, (top_mm - landing_mm) / n_above
    return {"riser_below_mm": hb, "riser_above_mm": ha, "difference_mm": ha - hb}


# ------------------------------------------------------------------ setting out
def setting_out(bottom_mm, top_mm, n, step_mm=1.0):
    if step_mm <= 0:
        raise ScenarioCheckError("the rounding step must be positive")
    rise, h = _uniform(bottom_mm, top_mm, n)

    def rnd(v):
        return math.floor(v / step_mm + 0.5) * step_mm

    rows, prev = [], rnd(bottom_mm)
    for k in range(1, n + 1):
        exact = bottom_mm + k * h if k < n else top_mm
        lv = rnd(exact)
        rows.append({"riser": k, "exact_mm": exact, "rounded_mm": lv, "rounded_riser_mm": lv - prev,
                     "deviation_mm": lv - exact})
        prev = lv
    counts = {}
    for r in rows:
        counts[r["rounded_riser_mm"]] = counts.get(r["rounded_riser_mm"], 0) + 1
    return {"riser_mm": h, "rows": rows, "rounded_riser_counts": counts,
            "max_abs_deviation_mm": max(abs(r["deviation_mm"]) for r in rows),
            "rounded_rise_mm": rows[-1]["rounded_mm"] - rnd(bottom_mm)}


def rounded_riser_drift(rise_mm, n, riser_mm):
    if n < 1 or int(n) != n:
        raise ScenarioCheckError("risers must be a whole number")
    return n * riser_mm - rise_mm


# ------------------------------------------------------------------ finishes and datums
def build_up(layers):
    vals = list(dict(layers).values())
    if any(v is None for v in vals):
        return None
    if any(v < 0 for v in vals):
        raise ScenarioCheckError("a layer thickness cannot be negative")
    return math.fsum(vals)


def datum_levels(bottom_ffl_mm, top_ffl_mm, n, landing_after, floor_bottom, floor_top, tread, landing=None):
    rise, h = _uniform(bottom_ffl_mm, top_ffl_mm, n)
    land = set(landing_after)
    if any(not 1 <= k < n for k in land):
        raise ScenarioCheckError("a landing follows a riser between the first and the last")
    if None in (floor_bottom, floor_top, tread):
        return None
    s_l = tread if landing is None else landing
    ssl_b, ssl_t = bottom_ffl_mm - floor_bottom, top_ffl_mm - floor_top
    conc = [ssl_b]
    finished = [bottom_ffl_mm]
    for k in range(1, n + 1):
        f_k = bottom_ffl_mm + k * h if k < n else top_ffl_mm
        finished.append(f_k)
        if k == n:
            conc.append(ssl_t)
        elif k in land:
            conc.append(f_k - s_l)
        else:
            conc.append(f_k - tread)
    risers = [conc[k] - conc[k - 1] for k in range(1, n + 1)]
    return {"riser_mm": h, "ssl_bottom_mm": ssl_b, "ssl_top_mm": ssl_t, "finished_mm": finished,
            "concrete_mm": conc, "concrete_risers_mm": risers, "first_mm": risers[0], "last_mm": risers[-1],
            "closure_mm": math.fsum(risers) - (ssl_t - ssl_b)}


# ------------------------------------------------------------------ exact flight quantities
def _flight_args(n, riser, going, width, waist):
    if n < 2 or int(n) != n:
        raise ScenarioCheckError("a flight needs a whole number of at least two risers")
    for v, nm in ((riser, "riser"), (going, "going"), (width, "width"), (waist, "waist")):
        if v is None or v <= 0:
            raise ScenarioCheckError(f"{nm} must be positive")
    return int(n)


def flight_section_volume(n, riser, going, width, waist, s0=0.0, s1=None):
    n = _flight_args(n, riser, going, width, waist)
    run = (n - 1) * going
    s1 = run if s1 is None else s1
    if not -TOL <= s0 <= s1 <= run + TOL:
        raise ScenarioCheckError("the interval must lie on the flight")
    slope = riser / going
    drop = waist * math.hypot(going, riser) / going
    area = 0.0
    for i in range(n - 1):                      # tread i + 1 at z = (i + 1) riser over [i going, (i + 1) going]
        a, b = max(s0, i * going), min(s1, (i + 1) * going)
        if b <= a:
            continue
        top = (i + 1) * riser
        # integral of top - (slope s - drop) ds over [a, b]
        area += (top + drop) * (b - a) - slope * (b * b - a * a) / 2.0
    return area * width


def solid_steps_volume(n, riser, going, width):
    n = _flight_args(n, riser, going, width, 1.0)
    return math.fsum(k * riser * going * width for k in range(1, n))


def winder_bounds(tread_areas_mm2, riser, waist, walking_going):
    areas = list(tread_areas_mm2)
    if not areas or any(a <= 0 for a in areas):
        raise ScenarioCheckError("winder tread areas must be positive")
    for v, nm in ((riser, "riser"), (waist, "waist"), (walking_going, "walking-line going")):
        if v is None or v <= 0:
            raise ScenarioCheckError(f"{nm} must be positive")
    A = math.fsum(areas)
    cos = walking_going / math.hypot(walking_going, riser)
    plane = A * (waist / cos + riser / 2.0)
    flat = math.fsum(a * (i * riser + waist) for i, a in enumerate(areas))
    return {"plan_area_mm2": A, "plane_equivalent_mm3": plane, "flat_soffit_bound_mm3": flat,
            "pitch_deg": math.degrees(math.atan2(riser, walking_going))}
