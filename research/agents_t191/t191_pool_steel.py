"""T-191 POOL_STEEL_REV2 (research, NEW and UNWIRED): swimming-pool reinforcement by bar mark, on the VERIFIED pool
structure, for any villa.  Rev2 of the pool part of T-166 (rev1); T-166 and T-183 are not changed.

Nothing imports this module; no released quantity changes (rollback: delete research/agents_t191 and tests/t191_*).
Stdlib + engine.source.rebar_unit_mass (read only).  Lengths in metres after `to_m`; inputs in mm / cm / m.

PHYSICAL ELEMENT.  An open RC tank: walls (two curtains) standing on an RC base (two mats).  Per printed population
(one zone of a pool detail) the bar marks are:
    WV_OUT  wall verticals, soil (outer) face        rate n/m, closed loop round the wall      shape from the detail
    WV_IN   wall verticals, water face                rate n/m, closed loop                    shape from the detail
    WH_OUT  wall horizontals (hoops), outer face      spacing s, over the wall height above the base top (R-POOL-6)
    WH_IN   wall horizontals (hoops), water face      spacing s, idem
    FB_X/FB_Y, FT_X/FT_Y  base bottom / top mat, the two directions (main n/m and distribution n/m; which plan
            direction carries the main bars is read from the plan or, when not marked, both assignments are carried)
    RIM     printed count of rings at the wall top     CORNER  printed count of rings at the base / wall corner

NOTATION MEANING (ENGINEERING_REASONING_STANDARD s.3).  "n ø d/m" is read two ways until the ELEMENT's own evidence
settles it: density (n bars per metre of width) or maximum c/c spacing 1/n (T-171 proved the second for FOOTINGS only;
r2, D-T191-2: that meaning is not carried to the pool base without the pool's own evidence; ST p.7 / p.8 print none:
no mesh spacing dimension, no edge-bar position, no note defining '/m'; p.7 itself uses both notations, 'n ø d/m' on
the pool and 'ø12MM/15cm' on the dome, which shows two notations, not which count the first one means).  "ø d/s cm"
prints a spacing.  Counts:
    closed loop (wall verticals round the ring):  N = ceil(P_bar / s)            (no ends: both meanings agree)
    open run (mesh), L_eff = extent - d (bar centre to bar centre across the bar-end outline):
        count A (density)      = ceil(n x L_eff)          (= ceil(L_eff / s))
        count B (max spacing)  = ceil(L_eff / s) + 1      (an edge bar each side)
        carried as a HELD range A .. B: low end on A, high end on B (HIGH_FROM_COUNT_B, the merged T-179 slab /
        stair convention); density on the bar-end extent E = L_eff + d gives ceil(n E), which lies in [A, B]
        because n d < 1, so the range covers it.  An input may fix one meaning only with a cited evidence string
        (mesh_count_meaning MAX_SPACING / DENSITY + mesh_count_evidence); without the evidence it is refused.
    hoops over the wall height H (end positions not dimensioned): N in [ceil(H / s), ceil(H / s) + 1]
        low  = the top / bottom line is taken by the rim bars / top mat (bars between them),
        high = a hoop at both ends of H (T-171 form with L_eff = H).  A held count range carries its HIGH count at
        the high end (HIGH_FROM_COUNT_B, Lead 2026-10-23 from T-179 r1), never the low count at both ends.
    printed counts ("3ø16") are never re-counted.

BAR LINES (centrelines).  Soil-face cover c_s (printed note) to the outer verticals; non-soil cover c_n (water face,
wall top, base top) where not printed is HELD and bounded by geometry: 0 <= c_n <= wall_t - c_s - (d_vo + d_ho +
d_hi + d_vi) (the two-face cage must fit in the wall).  Verticals are outermost (hoops inside them), as drawn.
Wall verticals run from the bottom mat (c_s + d/2 above the base underside) to the wall top (c_n + d/2 below the
rim): length = base_t + wall_h - c_s - c_n - d.  Bends are measured on centrelines; no hook / lap allowance is added
that the detail does not draw (URBAN-REBAR-NET-AND-PROCUREMENT@v1).

SHAPES (from the detail's exploded bar views):
    STRAIGHT              vertical only
    L_LEG_FLOOR_BOTTOM    vertical + a leg along the base bottom whose length is NOT dimensioned: the vertical is
                          measured, the leg is HELD_LENGTH (count and diameter carried; its drawn minimum, across the
                          wall to the water-face bar line, is reported, never a guessed extent)
    TOP_HOOK_BOTTOM_BOX   vertical + a hook across the wall top to the outer bar line + a closed box in the base
                          (bottom leg and top leg across the wall between the bar lines, one leg up between the
                          bottom and top mats): all legs fixed by the element's own dimensions and covers.

WALL HEIGHT (R-POOL-4 r2, the T-183 lesson): wall_h = rim -> STRUCTURAL base top.  A finished water depth is never a
concrete height: with only a finished depth (no structure line and no build-up) the population is HELD (None); a
wall_h equal to the finished depth while a build-up is drawn is refused (the rev1 error).

LAPS.  Net design weight carries no laps.  Rings (hoops, rim, corner bars) are closed loops: a ring of perimeter P
made of stock bars <= 12 m needs k pieces and k laps with k = min{k : P + k x L_lap <= 12 k}.  The lap length comes
from the structural notes (tension / compression values); where the zone is not printed the lap is a bounded range.
Laps are listed separately (procurement information), HELD, never 0 and never inside the net.

UNIT MASS: engine.source.rebar_unit_mass with the project's method (Urban default D2_OVER_162, authority
URBAN_OWNER_RULE, as every merged Alsenan steel ledger); exact 7,850 kg/m3 reported as a check only.

CLI:  python3 -I research/agents_t191/t191_pool_steel.py --check
      python3 -I research/agents_t191/t191_pool_steel.py ledger research/agents_t191/ALSENAN_POOL_STEEL_INPUT.json
"""

from __future__ import annotations

import itertools
import json
import math
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
from engine.source import rebar_unit_mass as RUM  # noqa: E402

EPS = 1e-9
UNITS = {"mm": 0.001, "cm": 0.01, "m": 1.0}
STOCK_M = 12.0
HELD = "HELD"
DRAWING_CONFIRMED = "DRAWING-CONFIRMED"
UNIT_MASS = {"method": RUM.D2_OVER_162, "authority": "URBAN_OWNER_RULE", "selected_by": "project (Urban default)"}


class PoolSteelError(ValueError):
    """refused input"""


def to_m(value, unit):
    if value is None:
        return None
    if unit not in UNITS:
        raise PoolSteelError(f"unknown unit {unit!r}")
    v = float(value) * UNITS[unit]
    if not v > 0:
        raise PoolSteelError(f"a dimension must be positive, got {value} {unit}")
    return v


def kg_per_m(d_mm, method=None):
    return RUM.kg_per_m(d_mm, method or UNIT_MASS)


def kg_per_m_exact(d_mm):
    return RUM.kg_per_m(d_mm, {"method": RUM.EXACT_DENSITY, "density_kg_m3": 7850.0})


def _ceil(x):
    return int(math.ceil(round(x, 9) - EPS))


# ---------------------------------------------------------------- plan outlines (exact, analytic; mirror-free)

class Outline:
    """Closed convex plan outline of the pool's OUTER wall face.
        RECT(a, b)        a along x, b along y
        D(r, b)           straight back of length 2r on y = 0 (along x), sides of length b, half circle of radius r
        STADIUM(r, s)     two half circles of radius r joined by straight sides of length s (along x)
    offset(t): the outline moved INWARDS by t (t < 0: outwards); straight faces move parallel, arcs keep their
    centre (a wall of constant thickness).  The perimeter is linear in t.  chord(direction, p): length of a bar
    parallel to `direction` ('x' or 'y') at position p measured across the outline from its first edge."""

    def __init__(self, kind, **d):
        self.kind = kind
        if kind == "RECT":
            self.a, self.b = d["a"], d["b"]
            ok = self.a > 0 and self.b > 0
        elif kind == "D":
            self.r, self.b = d["r"], d["b"]
            ok = self.r > 0 and self.b >= 0
        elif kind == "STADIUM":
            self.r, self.s = d["r"], d["s"]
            ok = self.r > 0 and self.s >= 0
        else:
            raise PoolSteelError(f"unknown outline {kind!r}")
        if not ok:
            raise PoolSteelError(f"degenerate {kind} outline {d}")

    def offset(self, t):
        if self.kind == "RECT":
            if not (self.a > 2 * t and self.b > 2 * t):
                raise PoolSteelError("offset larger than the outline")
            return Outline("RECT", a=self.a - 2 * t, b=self.b - 2 * t)
        if self.kind == "D":
            if not (self.r > t and self.b >= t):
                raise PoolSteelError("offset larger than the outline")
            return Outline("D", r=self.r - t, b=self.b - t)
        if not self.r > t:
            raise PoolSteelError("offset larger than the outline")
        return Outline("STADIUM", r=self.r - t, s=self.s)

    def area(self):
        if self.kind == "RECT":
            return self.a * self.b
        if self.kind == "D":
            return 2 * self.r * self.b + math.pi * self.r ** 2 / 2
        return 2 * self.r * self.s + math.pi * self.r ** 2

    def perimeter(self):
        if self.kind == "RECT":
            return 2 * (self.a + self.b)
        if self.kind == "D":
            return 2 * self.r + 2 * self.b + math.pi * self.r
        return 2 * self.s + 2 * math.pi * self.r

    def extent_across(self, direction):
        """extent over which bars parallel to `direction` are spread"""
        if self.kind == "RECT":
            return self.b if direction == "x" else self.a
        if self.kind == "D":
            return (self.b + self.r) if direction == "x" else 2 * self.r
        return 2 * self.r if direction == "x" else self.s + 2 * self.r

    def chord(self, direction, p):
        if direction not in ("x", "y"):
            raise PoolSteelError("direction is 'x' or 'y'")
        if self.kind == "RECT":
            return self.a if direction == "x" else self.b
        r = self.r
        if self.kind == "D":
            b = self.b
            if direction == "x":                     # bar parallel to the back at distance p from it
                return 2 * r if p <= b + EPS else 2 * math.sqrt(max(r * r - (p - b) ** 2, 0.0))
            u = p - r                                # bar across the back at x = u
            return b + math.sqrt(max(r * r - u * u, 0.0))
        s = self.s
        if direction == "x":                         # along the stadium at y = p - r
            u = p - r
            return s + 2 * math.sqrt(max(r * r - u * u, 0.0))
        x = p - (s / 2 + r)
        if abs(x) <= s / 2 + EPS:
            return 2 * r
        u = abs(x) - s / 2
        return 2 * math.sqrt(max(r * r - u * u, 0.0))


# ---------------------------------------------------------------- counts (notation meaning: maximum c/c spacing)

def spacing_of(rate_or_spacing):
    """{'n_per_m': n} -> 1/n ; {'s': s} -> s (metres)"""
    if "n_per_m" in rate_or_spacing:
        n = rate_or_spacing["n_per_m"]
        if not n > 0:
            raise PoolSteelError("rate must be positive")
        return 1.0 / n
    s = rate_or_spacing.get("s")
    if s is None or not s > 0:
        raise PoolSteelError("spacing must be positive")
    return s


def count_closed_loop(perimeter, s):
    return _ceil(perimeter / s)


def count_open_run(l_eff, s):
    if not l_eff > 0:
        raise PoolSteelError("L_eff must be positive")
    return _ceil(l_eff / s) + 1


def count_hoops(height, s):
    """(low, high) whole hoops at a spacing <= s over a height whose end positions are not dimensioned"""
    k = _ceil(height / s)
    return k, k + 1


MESH_COUNTS = ("A", "B")
MESH_MEANING = {"DENSITY": ("A",), "MAX_SPACING": ("B",), None: MESH_COUNTS}


def count_mesh(l_eff, s):
    """(A, B): A = density count ceil(L_eff / s) = ceil(n x L_eff), B = maximum-spacing count A + 1"""
    if not l_eff > 0:
        raise PoolSteelError("L_eff must be positive")
    return _ceil(l_eff / s), count_open_run(l_eff, s)


def mesh(outline, direction, s, d_mm, count="B"):
    """bars parallel to `direction` spread across `outline` (the bar-end outline), count A or B (see NOTATION
    MEANING); the bars are spread evenly between the outermost positions d/2 .. E - d/2 (edge bars at the bar
    ends under either count: the outline is the same, only the number of bars differs); returns (count, total
    metres, positions)"""
    E = outline.extent_across(direction)
    d = d_mm / 1000.0
    l_eff = E - d
    a, b = count_mesh(l_eff, s)
    if count not in MESH_COUNTS:
        raise PoolSteelError(f"mesh count is 'A' or 'B', got {count!r}")
    n = a if count == "A" else b
    if n < 2:
        raise PoolSteelError("a mesh needs at least two bars")
    pos = [d / 2 + k * l_eff / (n - 1) for k in range(n)]
    return n, sum(outline.chord(direction, p) for p in pos), pos


def ring_laps(perimeter, lap_m):
    """k pieces and k laps to close one ring from stock bars of STOCK_M (k >= 1)"""
    if lap_m is None:
        return None
    if lap_m >= STOCK_M:
        raise PoolSteelError("lap longer than a stock bar")
    k = 1
    while perimeter + k * lap_m > k * STOCK_M + EPS:
        k += 1
    return k


# ---------------------------------------------------------------- wall height guard (R-POOL-4 r2)

def wall_height(levels=None, wall_h=None, finished_depth=None, floor_buildup=None, *, tol=1e-6):
    """Structural wall height above the base top, or None (HELD).
    levels: {'rim', 'base_top_structural'?, 'finished_floor'?, 'floor_buildup'?} on one datum.
    A wall_h that equals a finished depth while a build-up > 0 is drawn is REFUSED (the rev1 / D-T183-1 error)."""
    if levels is not None:
        if wall_h is not None:
            raise PoolSteelError("give the wall height either as wall_h or as levels, not both")
        rim = levels["rim"]
        st = levels.get("base_top_structural")
        ff = levels.get("finished_floor")
        bu = levels.get("floor_buildup")
        if st is not None:
            h = rim - st
            if not h > 0:
                raise PoolSteelError("rim must be above the structural base top")
            if ff is not None:
                if ff < st - tol:
                    raise PoolSteelError("finished floor below the structure line")
                if bu is not None and abs((ff - st) - bu) > tol:
                    raise PoolSteelError("levels and the printed build-up disagree")
            return h
        if ff is not None and bu is not None:
            return rim - ff + bu
        return None                                   # finished depth alone: HELD
    if wall_h is not None and finished_depth is not None and floor_buildup:
        if abs(wall_h - finished_depth) <= tol:
            raise PoolSteelError("wall height equals the FINISHED water depth although a floor build-up is drawn: "
                                 "the RC wall runs to the structure line (R-POOL-4 r2)")
        if abs(wall_h - (finished_depth + floor_buildup)) > tol:
            raise PoolSteelError("wall height disagrees with finished depth + build-up")
    return wall_h


# ---------------------------------------------------------------- one population, one reading

def _bar(mark, label, d, count, length=None, metres=None, status=DRAWING_CONFIRMED, note=""):
    m = count * length if metres is None else metres
    return {"mark": mark, "label": label, "d": d, "count": count, "length_m": length, "m": m,
            "kg_per_m": kg_per_m(d), "kg": m * kg_per_m(d), "kg_exact_density": m * kg_per_m_exact(d),
            "status": status, "note": note}


def population_rows(pop, outer, wall_t, base_t, wall_h, c_s, c_n, *, hoops="high", main_dir="x", mesh_count="B"):
    """rows of one population for ONE reading (c_n, hoop count end, main-bar direction, mesh count A / B) + held
    items."""
    if wall_h is None:
        raise PoolSteelError("wall height HELD: no bar population")
    if c_s is None:
        raise PoolSteelError("soil cover not printed: population HELD")
    vo, vi = pop.get("WV_OUT"), pop.get("WV_IN")
    ho, hi = pop.get("WH_OUT"), pop.get("WH_IN")
    d_vo = vo["d"] / 1000 if vo else 0.0
    d_vi = vi["d"] / 1000 if vi else 0.0
    d_ho = ho["d"] / 1000 if ho else 0.0
    d_hi = hi["d"] / 1000 if hi else 0.0
    if c_n < 0 or c_s + c_n + d_vo + d_ho + d_hi + d_vi > wall_t + EPS:
        raise PoolSteelError("covers and bars do not fit in the wall")
    H = base_t + wall_h
    rows, held = [], []
    t_vo = c_s + d_vo / 2                                  # inward offset of the outer vertical centreline
    t_vi = wall_t - c_n - d_vi / 2                         # inward offset of the water-face vertical centreline
    w_cage = t_vi - t_vo                                   # across the wall, bar line to bar line
    for key, t, spec in (("WV_OUT", t_vo, vo), ("WV_IN", t_vi, vi)):
        if not spec:
            continue
        d = spec["d"]
        P = outer.offset(t).perimeter()
        n = count_closed_loop(P, spacing_of(spec))
        v = H - c_s - c_n - d / 1000
        shape = spec.get("shape", "STRAIGHT")
        length = v
        note = f"closed loop P_bar {P:.4f} m, N = ceil(P / s); vertical {v:.4f} m"
        if shape == "TOP_HOOK_BOTTOM_BOX":
            box_h = base_t - c_s - c_n - d / 1000
            length = v + w_cage + 2 * w_cage + box_h
            note += f" + top hook {w_cage:.4f} + box 2 x {w_cage:.4f} + {box_h:.4f} m"
        elif shape == "L_LEG_FLOOR_BOTTOM":
            held.append({"mark": key + "_LEG", "d": d, "count": n, "status": "HELD_LENGTH",
                         "drawn_minimum_m_each": w_cage, "drawn_minimum_kg": n * w_cage * kg_per_m(d),
                         "basis": "leg along the base bottom drawn in the bar view, length not dimensioned; "
                                  "minimum drawn in the section = across the wall to the water-face bar line"})
            note += "; floor leg HELD (not dimensioned)"
        elif shape != "STRAIGHT":
            raise PoolSteelError(f"unknown shape {shape!r}")
        rows.append(_bar(key, spec.get("label", ""), d, n, length, note=note))
    for key, t, spec in (("WH_OUT", c_s + d_vo + d_ho / 2, ho), ("WH_IN", wall_t - c_n - d_vi - d_hi / 2, hi)):
        if not spec:
            continue
        lo, hi_n = count_hoops(wall_h, spacing_of(spec))
        n = hi_n if hoops == "high" else lo
        P = outer.offset(t).perimeter()
        rows.append(_bar(key, spec.get("label", ""), spec["d"], n, P,
                         status=HELD + "_COUNT_RANGE",
                         note=f"ring P {P:.4f} m; hoops over wall_h {wall_h:.3f} m: {lo} .. {hi_n} (this reading {n})"))
        held.append({"mark": key + "_LAPS", "d": spec["d"], "count": n, "perimeter_m": P, "status": "HELD_LAP"})
    mesh_out = outer.offset(c_s + d_vo)
    other = "y" if main_dir == "x" else "x"
    for key, dirn in (("F_MAIN", main_dir), ("F_DIST", other)):
        spec = pop.get(key)
        if not spec:
            continue
        s_ = spacing_of(spec)
        n, m, _ = mesh(mesh_out, dirn, s_, spec["d"], count=mesh_count)
        a, b = count_mesh(mesh_out.extent_across(dirn) - spec["d"] / 1000.0, s_)
        for layer in ("BOTTOM", "TOP"):
            rows.append(_bar(f"F{layer[0]}_{key[2:]}_{dirn.upper()}", spec.get("label", ""), spec["d"], n,
                             metres=m, status=HELD + "_COUNT_RANGE" if a != b else DRAWING_CONFIRMED,
                             note=f"{layer.lower()} mat, bars along {dirn}, count {mesh_count} = {n} chords "
                                  f"(A {a} .. B {b}), ends inside the outer verticals (offset {c_s + d_vo:.3f} m)"))
    for key in ("RIM", "CORNER"):
        spec = pop.get(key)
        if not spec:
            continue
        k, d = spec["count"], spec["d"] / 1000
        t0, t1 = c_s + d_vo + d / 2, wall_t - c_n - d_vi - d / 2
        offs = [t0] if k == 1 else [t0 + i * (t1 - t0) / (k - 1) for i in range(k)]
        m = sum(outer.offset(t).perimeter() for t in offs)
        rows.append(_bar(key, spec.get("label", ""), spec["d"], k, metres=m,
                         note=f"{k} rings spread across the wall between the bar lines, total {m:.4f} m"))
        for t in offs:
            held.append({"mark": key + "_LAPS", "d": spec["d"], "count": 1,
                         "perimeter_m": outer.offset(t).perimeter(), "status": "HELD_LAP"})
    return rows, held


def c_n_max(pop, wall_t, c_s):
    ds = sum(pop[k]["d"] / 1000 for k in ("WV_OUT", "WH_OUT", "WH_IN", "WV_IN") if pop.get(k))
    cm = wall_t - c_s - ds
    if cm < 0:
        raise PoolSteelError("the printed bars do not fit in the wall with the soil cover")
    return cm


def mesh_counts_for(meaning=None, evidence=None):
    """the mesh count readings carried: both (A .. B) unless the element's own evidence fixes the meaning"""
    if meaning not in MESH_MEANING:
        raise PoolSteelError(f"unknown mesh count meaning {meaning!r}")
    if meaning is not None and not (isinstance(evidence, str) and evidence.strip()):
        raise PoolSteelError("a mesh count meaning is fixed only with this element's own cited evidence "
                             "(ERS s.3: a meaning proven for another element type is not carried over)")
    return MESH_MEANING[meaning]


def population_range(pop, outer, wall_t, base_t, wall_h, c_s, c_n=None, *, main_dirs=("x", "y"),
                     mesh_counts=MESH_COUNTS):
    """every reading (c_n at both bounds if not printed, hoop count low / high, both main-bar directions if the
    plan does not mark it, mesh count A / B unless fixed) -> per-mark low / high kg and total low / high; the low
    end carries the low counts and the high end the high counts (HIGH_FROM_COUNT_B)."""
    cns = [c_n] if c_n is not None else [0.0, c_n_max(pop, wall_t, c_s)]
    readings = []
    for cn, hp, md, mc in itertools.product(cns, ("low", "high"), main_dirs, mesh_counts):
        rows, held = population_rows(pop, outer, wall_t, base_t, wall_h, c_s, cn, hoops=hp, main_dir=md,
                                     mesh_count=mc)
        readings.append({"c_n": cn, "hoops": hp, "main_dir": md, "mesh_count": mc, "rows": rows, "held": held,
                         "kg": sum(r["kg"] for r in rows)})
    lo = min(readings, key=lambda r: r["kg"])
    hi = max(readings, key=lambda r: r["kg"])
    if hi["hoops"] != "high" or hi["mesh_count"] != max(mesh_counts):
        raise PoolSteelError("HIGH_FROM_COUNT_B: the high end must carry the high hoop and mesh counts")
    if lo["hoops"] != "low" or lo["mesh_count"] != min(mesh_counts):
        raise PoolSteelError("the low end must carry the low hoop and mesh counts")
    return {"low": lo, "high": hi, "readings": readings}


def lap_range(held_items, lap_d_factors):
    """procurement information: laps of every ring at lap = f x d for f in the printed (min, max) factors"""
    if lap_d_factors is None:
        return None
    out = []
    for f in lap_d_factors:
        kg = 0.0
        for h in held_items:
            if h["status"] != "HELD_LAP":
                continue
            lap = f * h["d"] / 1000
            k = ring_laps(h["perimeter_m"], lap)
            kg += h["count"] * k * lap * kg_per_m(h["d"])
        out.append(kg)
    return min(out), max(out)


# ---------------------------------------------------------------- ledger from JSON

def load(inp):
    u = inp.get("unit", "m")
    o = inp["outline"]
    dims = {k: to_m(v, u) if k != "kind" else v for k, v in o.items()}
    outer = Outline(o["kind"], **{k: v for k, v in dims.items() if k != "kind"})
    lv = inp.get("levels")
    if lv is not None:
        lv = {k: (None if v is None else float(v) * UNITS[u]) for k, v in lv.items()}
    wh = wall_height(levels=lv, wall_h=to_m(inp.get("wall_h"), u),
                     finished_depth=to_m(inp.get("finished_depth"), u),
                     floor_buildup=to_m(inp.get("floor_buildup"), u))
    return {"outer": outer, "wall_t": to_m(inp["wall_t"], u), "base_t": to_m(inp["base_t"], u), "wall_h": wh,
            "c_s": to_m(inp.get("soil_cover"), u),
            "c_n": None if inp.get("nonsoil_cover") is None else to_m(inp["nonsoil_cover"], u),
            "main_dirs": tuple(inp.get("main_dirs", ("x", "y"))), "lap_d_factors": inp.get("lap_d_factors"),
            "mesh_counts": mesh_counts_for(inp.get("mesh_count_meaning"), inp.get("mesh_count_evidence"))}


def ledger(inp):
    g = load(inp)
    out = {"wall_h_m": g["wall_h"], "unit_mass": RUM.describe(UNIT_MASS), "populations": {}}
    for name, pop in inp["populations"].items():
        if g["wall_h"] is None:
            out["populations"][name] = {"status": HELD, "kg": None, "basis": "wall height HELD (finished depth only)"}
            continue
        rg = population_range(pop, g["outer"], g["wall_t"], g["base_t"], g["wall_h"], g["c_s"], g["c_n"],
                              main_dirs=g["main_dirs"], mesh_counts=g["mesh_counts"])
        lo, hi = rg["low"], rg["high"]
        marks = {}
        for end, rd in (("low", lo), ("high", hi)):
            for r in rd["rows"]:
                mk = marks.setdefault(r["mark"], {"d": r["d"], "label": r["label"]})
                mk[end] = {"count": r["count"], "m": round(r["m"], 4), "kg": round(r["kg"], 3), "note": r["note"]}
        legs = [h for h in hi["held"] if h["status"] == "HELD_LENGTH"]
        out["populations"][name] = {
            "kg_low": round(lo["kg"], 2), "kg_high": round(hi["kg"], 2),
            "kg_exact_density_low": round(sum(r["kg_exact_density"] for r in lo["rows"]), 2),
            "kg_exact_density_high": round(sum(r["kg_exact_density"] for r in hi["rows"]), 2),
            "low_reading": {k: lo[k] for k in ("c_n", "hoops", "main_dir", "mesh_count")},
            "high_reading": {k: hi[k] for k in ("c_n", "hoops", "main_dir", "mesh_count")},
            "marks": marks,
            "held_legs": [{"mark": h["mark"], "d": h["d"], "count": h["count"],
                           "drawn_minimum_kg": round(h["drawn_minimum_kg"], 3)} for h in legs],
            "laps_kg_range_procurement": None if g["lap_d_factors"] is None else
            [round(x, 2) for x in lap_range(hi["held"], g["lap_d_factors"])],
            "status": "HELD (which population governs: designer item; non-soil cover, hoop end positions and "
                      "the base-mat count meaning of '/m' (A density .. B max spacing) not printed; legs and laps "
                      "listed apart)"}
    return out


# ---------------------------------------------------------------- synthetic self-check (not any real villa)

def check():
    """small hand cases; the full fixture with adversarial cases is tests/t191_pool_steel"""
    o = Outline("RECT", a=4.0, b=3.0)
    assert count_closed_loop(o.perimeter(), 0.2) == 70                  # 14.0 / 0.2 exactly
    assert count_open_run(2.986, 0.2) == 16                               # ceil(14.93) + 1
    assert count_mesh(2.986, 0.2) == (15, 16)                             # open mesh: A != B
    assert _ceil(7 * 11.947884) == count_closed_loop(11.947884, 1 / 7) == 84   # closed loop: both meanings agree
    assert count_hoops(1.20, 0.20) == (6, 7)
    assert ring_laps(11.0, 0.84) == 1 and ring_laps(11.5, 0.84) == 2
    try:
        wall_height(wall_h=1.15, finished_depth=1.15, floor_buildup=0.05)
    except PoolSteelError:
        pass
    else:
        raise AssertionError("finished depth taken as the wall height must be refused")
    assert wall_height(levels={"rim": 0.30, "finished_floor": -0.85}) is None
    print("t191 --check PASS")
    return True


if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "--check":
        check()
    elif len(sys.argv) == 3 and sys.argv[1] == "ledger":
        print(json.dumps(ledger(json.load(open(sys.argv[2], encoding="utf-8"))), indent=1, ensure_ascii=False))
    else:
        print(__doc__)
        sys.exit(2)
