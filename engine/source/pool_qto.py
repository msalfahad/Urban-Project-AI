"""SWIMMING POOL QTO - source-controlled concrete and reinforcement quantities for a pool shell (generic).

A pool quantity is released only when every dimension it needs is established. A dimension is established when it is
printed (STATED_DIMENSION) or drawn at true size on a scaled plan and corroborated (CAD_GEOMETRY). A length read off a
not-to-scale detail (NTS_GRAPHIC) is never a measurement. A missing dimension gives no quantity (None), never 0.

Notation
    parse_notation(text)        'n%%cd/m' RATE, '%%cd/s cm' SPACING (1000/s bars per m), 'n%%cd' FINITE_GROUP
                                (n bars, never a rate), anything else UNPARSED. Ø, %%c and %%C are all accepted.

Plan geometry (exact lines and arcs, through ground_slab_qto rings)
    region_area_m2, band_area_m2   a wall band is the structural outline minus the water outline
    ring_length_m                  exact face length (lines and arcs)
    tiling(parts, whole)           the wall runs cover the band exactly once

Concrete
    prism(area, height)            area x height, released only when both are established
    wall_base_split(...)           ownership: the base owns the whole structural footprint x base thickness (the wall
                                   footprint below the base top included); a wall owns its band x its height above
                                   the base top. The wall/base intersection is counted once, in the base.
    sloped_slab_m3(...)            plan area x perpendicular thickness / cos(slope) for a plane slab

Reinforcement (the controlled methodology of slab_rebar_qto: rate x width x run, D^2 / 162, never rounded)
    rate_qty(...)                  equivalent count = rate x distribution width (unrounded); length = count x run
    finite_qty(...)                count x run; a finite group is never converted to a rate

Drawn bars (topology only: lengths stay in drawing units and never become millimetres)
    chain_runs(segments)           bar runs joined end to end; a T contact is not continuity; duplicates collapse
    run_shape(run)                 legs, bends, hooks, shape (STRAIGHT, L, U, CRANKED, COMPOUND)
    bind_leaders(...)              a label binds the bars or dots its leader tips touch
    bind_nearest(...)              a label with no leader binds the nearest bar only when no other bar is as close
    run_diameters(...)             one drawn run carrying two diameters is a SOURCE_CONFLICT, not one bar
    leg_lengths_in(...)            drawn length of a run inside each convex region
    classify_interface(...)        per wall/base junction: SINGLE_BENT_BAR, SEPARATE_STARTER, LAP_BETWEEN_DISTINCT_BARS,
                                   ANCHORED_STRAIGHT, BASE_ONLY or UNRESOLVED; every run gets exactly one
                                   COMPONENT_OWNER_ID (the region holding the larger share of its drawn length)

Stdlib + engine.source.ground_slab_qto / slab_rebar_qto only. No project data.
"""

from __future__ import annotations

import math
import re

from engine.source import ground_slab_qto as GS
from engine.source import slab_rebar_qto as SR


RELEASED = SR.PROJECT_BASIS_QTO
BLOCKED = SR.BLOCKED_UNQUANTIFIED
CONFLICT = SR.SOURCE_CONFLICT
SENSITIVITY_ONLY = "SENSITIVITY_ONLY"
NOT_PRESENT = "NOT_PRESENT_IN_SOURCE"
LANES = (RELEASED, BLOCKED, CONFLICT, SENSITIVITY_ONLY, NOT_PRESENT)

# source authority of a dimension
STATED = "STATED_DIMENSION"
CAD_GEOMETRY = "CAD_GEOMETRY"
NTS_GRAPHIC = "NTS_GRAPHIC"
NOT_ESTABLISHED = "NOT_ESTABLISHED"
AUTHORITIES = (STATED, CAD_GEOMETRY, NTS_GRAPHIC, NOT_ESTABLISHED)
MEASURING = (STATED, CAD_GEOMETRY)

# notation kinds
RATE = "RATE"
SPACING = "SPACING"
FINITE_GROUP = "FINITE_GROUP"
UNPARSED = "UNPARSED"

# drawn bar shapes
STRAIGHT, L_SHAPE, U_SHAPE, CRANKED, COMPOUND = "STRAIGHT", "L", "U", "CRANKED", "COMPOUND"
SHAPES = (STRAIGHT, L_SHAPE, U_SHAPE, CRANKED, COMPOUND)

# wall/base interface classes
SINGLE_BENT_BAR = "SINGLE_BENT_BAR"
ANCHORED_STRAIGHT = "ANCHORED_STRAIGHT"
LAP_BETWEEN_DISTINCT_BARS = "LAP_BETWEEN_DISTINCT_BARS"
SEPARATE_STARTER = "SEPARATE_STARTER"
BASE_ONLY = "BASE_ONLY"
UNRESOLVED = "UNRESOLVED"
INTERFACE_CLASSES = (SINGLE_BENT_BAR, ANCHORED_STRAIGHT, LAP_BETWEEN_DISTINCT_BARS, SEPARATE_STARTER, BASE_ONLY,
                     UNRESOLVED)

TOL = 1e-9


class PoolQtoError(ValueError):
    pass


def established(authority):
    """True for a measuring authority (stated or CAD-established); an unknown authority is an error."""
    if authority not in AUTHORITIES:
        raise PoolQtoError(f"unknown authority {authority!r}")
    return authority in MEASURING


def _blocked(missing, **extra):
    return {"lane": BLOCKED, "missing": sorted(missing), **extra}


# ------------------------------------------------------------------ notation
_DIA = r"(?:%%[cC]|Ø|∅|ø)"
_RATE = re.compile(rf"^\s*(\d+)\s*{_DIA}\s*(\d+(?:\.\d+)?)\s*/\s*m\s*$")
_SPACING = re.compile(rf"^\s*{_DIA}\s*(\d+(?:\.\d+)?)\s*/\s*(\d+(?:\.\d+)?)\s*cm\s*$")
_FINITE = re.compile(rf"^\s*(\d+)\s*{_DIA}\s*(\d+(?:\.\d+)?)\s*$")


def parse_notation(text):
    """Parse one bar label. Never guesses: an unrecognised label is UNPARSED."""
    raw = text
    t = (text or "").strip()
    m = _RATE.match(t)
    if m:
        return {"kind": RATE, "count": int(m.group(1)), "dia_mm": float(m.group(2)), "per_m": float(m.group(1)),
                "spacing_mm": 1000.0 / float(m.group(1)), "raw": raw}
    m = _SPACING.match(t)
    if m:
        s_mm = float(m.group(2)) * 10.0
        if s_mm <= 0:
            raise PoolQtoError(f"zero spacing in {raw!r}")
        return {"kind": SPACING, "count": None, "dia_mm": float(m.group(1)), "per_m": 1000.0 / s_mm,
                "spacing_mm": s_mm, "raw": raw}
    m = _FINITE.match(t)
    if m:
        return {"kind": FINITE_GROUP, "count": int(m.group(1)), "dia_mm": float(m.group(2)), "per_m": None,
                "spacing_mm": None, "raw": raw}
    return {"kind": UNPARSED, "count": None, "dia_mm": None, "per_m": None, "spacing_mm": None, "raw": raw}


# ------------------------------------------------------------------ plan geometry
def region_area_m2(region):
    """Exact net area of a ground_slab_qto region (rings in mm), in m2."""
    return GS.area(region) / 1e6


def band_area_m2(outer_region, inner_region):
    """Wall band = structural outline minus water outline (exact), in m2."""
    a_out, a_in = region_area_m2(outer_region), region_area_m2(inner_region)
    if a_in >= a_out:
        raise PoolQtoError("the water outline must lie inside the structural outline")
    return a_out - a_in


def ring_length_m(ring):
    """Exact length of a ring (lines and arcs), in m."""
    GS.check_ring(ring)
    s = []
    for e in ring:
        if e[0] == GS.LINE:
            s.append(math.dist(e[1], e[2]))
        else:
            s.append(e[2] * abs(e[4] - e[3]))
    return math.fsum(s) / 1000.0


def tiling(parts_m2, whole_m2, *, tol_m2=1e-9):
    s = math.fsum(parts_m2)
    return {"sum_m2": s, "whole_m2": whole_m2, "gap_m2": whole_m2 - s, "exact": abs(whole_m2 - s) <= tol_m2}


# ------------------------------------------------------------------ concrete
def prism(area_m2, area_authority, height_m, height_authority):
    """Volume of a vertical prism. Released only when the plan area and the height are both established."""
    missing = [n for n, a, v in (("plan_area", area_authority, area_m2), ("height", height_authority, height_m))
               if not established(a) or v is None]
    if missing:
        return _blocked(missing, m3=None)
    if area_m2 < 0 or height_m < 0:
        raise PoolQtoError("area and height must be non-negative")
    return {"lane": RELEASED, "m3": float(area_m2) * float(height_m), "missing": []}


def wall_base_split(footprint_m2, band_m2, base_t_m, wall_h_m, *, footprint_authority, band_authority,
                    base_t_authority, wall_h_authority):
    """Base = structural footprint x base thickness (it owns the wall footprint below the base top); walls = band x
    height above the base top. The two never overlap, so their sum is the whole shell once."""
    if band_m2 is not None and footprint_m2 is not None and band_m2 > footprint_m2:
        raise PoolQtoError("a wall band cannot exceed the structural footprint")
    base = prism(footprint_m2, footprint_authority, base_t_m, base_t_authority)
    wall = prism(band_m2, band_authority, wall_h_m, wall_h_authority)
    both = base["lane"] == RELEASED and wall["lane"] == RELEASED
    return {"base": {**base, "owns": "STRUCTURAL_FOOTPRINT x BASE_THICKNESS (wall footprint below the base top included)"},
            "wall": {**wall, "owns": "WALL_BAND x HEIGHT_ABOVE_BASE_TOP"},
            "shell_m3": base["m3"] + wall["m3"] if both else None,
            "intersection_owner": "BASE"}


def sloped_slab_m3(plan_area_m2, t_perp_m, rise_m, run_m):
    """Plane slab of uniform perpendicular thickness over a plan area: V = A x t / cos(theta), tan(theta) = rise/run."""
    if min(plan_area_m2, t_perp_m, run_m) <= 0 or rise_m < 0:
        raise PoolQtoError("plan area, thickness and run must be positive and the rise non-negative")
    return float(plan_area_m2) * float(t_perp_m) * math.hypot(1.0, float(rise_m) / float(run_m))


# ------------------------------------------------------------------ reinforcement quantities
def rate_qty(notation, width_m, width_authority, run_m, run_authority):
    """A RATE or SPACING family over a distribution width with one run length. Equivalent count = bars per metre x
    width, never rounded, never +1. Blocked when the width or the run is not established."""
    if notation["kind"] not in (RATE, SPACING):
        raise PoolQtoError(f"rate_qty needs a RATE or SPACING notation, got {notation['kind']}")
    missing = [n for n, a, v in (("distribution_width", width_authority, width_m), ("bar_run", run_authority, run_m))
               if not established(a) or v is None]
    if missing:
        return _blocked(missing, equivalent_count=None, length_m=None, kg=None, dia_mm=notation["dia_mm"])
    count = notation["per_m"] * float(width_m)
    length = SR.rectangle_length_m(notation["per_m"], width_m, run_m)
    return {"lane": RELEASED, "equivalent_count": count, "length_m": length,
            "kg": SR.mass(notation["dia_mm"], length)["kg"], "dia_mm": notation["dia_mm"], "missing": [],
            "physical_bbs_count": SR.UNRESOLVED}


def finite_qty(notation, run_m, run_authority):
    """A finite group ('3Ø16'): count x run. Never a rate, never spread over a width."""
    if notation["kind"] != FINITE_GROUP:
        raise PoolQtoError(f"finite_qty needs a FINITE_GROUP notation, got {notation['kind']}")
    if not established(run_authority) or run_m is None:
        return _blocked(["bar_run"], count=notation["count"], length_m=None, kg=None, dia_mm=notation["dia_mm"])
    length = notation["count"] * float(run_m)
    return {"lane": RELEASED, "count": notation["count"], "length_m": length,
            "kg": SR.mass(notation["dia_mm"], length)["kg"], "dia_mm": notation["dia_mm"], "missing": []}


def released_total(rows, key):
    """Sum of a quantity over released rows only; a blocked row never enters a total and never reads as 0."""
    out = []
    for r in rows:
        if r.get("lane") == RELEASED:
            if r.get(key) is None:
                raise PoolQtoError(f"released row without {key}")
            out.append(float(r[key]))
        elif r.get(key) not in (None, ""):
            raise PoolQtoError(f"a {r.get('lane')} row carries {key}")
    return math.fsum(out)


# ------------------------------------------------------------------ drawn bar runs
def _seg_end(s, k):
    if s[0] == "LINE":
        return s[2] if k == 0 else s[3]
    t = s[4] if k == 0 else s[5]
    return (s[2][0] + s[3] * math.cos(t), s[2][1] + s[3] * math.sin(t))


def _seg_len(s):
    if s[0] == "LINE":
        return math.dist(s[2], s[3])
    return s[3] * abs(s[5] - s[4])


def _geom_key(s, nd=3):
    """Direction-free geometry key: identical drawn bars collapse whatever their handle or direction."""
    if s[0] == "LINE":
        a, b = (round(s[2][0], nd), round(s[2][1], nd)), (round(s[3][0], nd), round(s[3][1], nd))
        return ("LINE",) + tuple(sorted((a, b)))
    return ("ARC", round(s[2][0], nd), round(s[2][1], nd), round(s[3], nd)) + tuple(sorted((round(s[4], 6),
                                                                                       round(s[5], 6))))


def chain_runs(segments, *, tol=0.5):
    """Join drawn bar segments end to end. segments: ("LINE", id, a, b) or ("ARC", id, centre, r, t0, t1).
    Two segments continue each other only when an END of one meets an END of the other within tol; an end touching
    the middle of another bar (a T contact) is not continuity. A node where three or more ends meet is a branch: the
    run stops there. Segments with identical geometry collapse into the first (reported as duplicates)."""
    seen, segs, dups = {}, [], []
    for s in segments:
        k = _geom_key(s)
        if k in seen:
            dups.append((s[1], seen[k]))
            continue
        seen[k] = s[1]
        segs.append(s)
    ends = []                                   # (seg index, end k, point)
    for i, s in enumerate(segs):
        for k in (0, 1):
            ends.append((i, k, _seg_end(s, k)))
    nodes = []                                  # clusters of ends
    for e in ends:
        for n in nodes:
            if math.dist(n[0][2], e[2]) <= tol:
                n.append(e)
                break
        else:
            nodes.append([e])
    node_of = {}
    for ni, n in enumerate(nodes):
        for (i, k, _) in n:
            node_of[(i, k)] = ni
    used, runs = set(), []

    def walk(i, k_in):
        order = [(i, 1 - k_in)]                 # (seg, exit end)
        used.add(i)
        while True:
            j, k_out = order[-1]
            n = nodes[node_of[(j, k_out)]]
            nxt = [(a, b) for (a, b, _) in n if a not in used]
            if len(n) != 2 or len(nxt) != 1:
                return order
            a, b = nxt[0]
            used.add(a)
            order.append((a, 1 - b))

    starts = sorted(range(len(segs)), key=lambda i: (len(nodes[node_of[(i, 0)]]) == 2 and
                                                      len(nodes[node_of[(i, 1)]]) == 2, i))
    for i in starts:
        if i in used:
            continue
        free0 = len(nodes[node_of[(i, 0)]]) != 2
        order = walk(i, 0 if free0 else 1)
        if not free0 and len(nodes[node_of[(i, 0)]]) == 2:          # extend backwards from the start
            back = []
            j, k = i, 0
            while True:
                n = nodes[node_of[(j, k)]]
                prv = [(a, b) for (a, b, _) in n if a not in used]
                if len(n) != 2 or len(prv) != 1:
                    break
                a, b = prv[0]
                used.add(a)
                back.append((a, b))
                j, k = a, 1 - b
            order = [(a, b) for (a, b) in reversed(back)] + order
        ids = [segs[j][1] for j, _ in order]
        first, last = order[0], order[-1]
        p0 = _seg_end(segs[first[0]], 1 - first[1])
        p1 = _seg_end(segs[last[0]], last[1])
        closed = len(ids) > 2 and math.dist(p0, p1) <= tol
        runs.append({"run_segments": ids, "start": p0, "end": p1, "closed": closed,
                     "drawn_length_units": math.fsum(_seg_len(segs[j]) for j, _ in order),
                     "_segs": [segs[j] if kk == 1 else _reverse(segs[j]) for j, kk in order]})
    runs.sort(key=lambda r: (-r["drawn_length_units"], r["run_segments"][0]))
    return {"runs": runs, "duplicates": dups}


def _reverse(s):
    if s[0] == "LINE":
        return (s[0], s[1], s[3], s[2])
    return (s[0], s[1], s[2], s[3], s[5], s[4])


def _dir(s, k):
    """Unit direction of travel at end k (0 = start, 1 = end) of a segment."""
    if s[0] == "LINE":
        dx, dy = s[3][0] - s[2][0], s[3][1] - s[2][1]
    else:
        t = s[4] if k == 0 else s[5]
        sg = 1.0 if s[5] > s[4] else -1.0
        dx, dy = -math.sin(t) * sg, math.cos(t) * sg
    n = math.hypot(dx, dy)
    return (dx / n, dy / n)


def run_shape(run, *, hook_max_units, bend_deg=20.0, crank_max_deg=75.0):
    """Straight legs between bends: an arc, or a direction change above bend_deg, is one bend. An end leg no longer
    than hook_max_units is a hook. Shape from the remaining (core) legs: STRAIGHT (1); L (2, turn about 90 deg);
    U (3, first and last antiparallel); CRANKED (every core turn at most crank_max_deg); else COMPOUND."""
    legs, turns, cur, pending = [], [], [], 0.0
    for s in run["_segs"]:
        if s[0] == "ARC":
            if cur:
                legs.append(cur)
                cur = []
            if legs:
                pending += math.degrees(abs(s[5] - s[4]))
            continue
        if cur:
            a, b = _dir(cur[-1], 1), _dir(s, 0)
            ang = math.degrees(math.acos(max(-1.0, min(1.0, a[0] * b[0] + a[1] * b[1]))))
            if ang > bend_deg:
                legs.append(cur)
                cur = []
                turns.append(ang)
        elif legs:
            turns.append(pending)
        pending = 0.0
        cur.append(s)
    if cur:
        legs.append(cur)
    leg_len = [math.fsum(_seg_len(s) for s in lg) for lg in legs]
    h0 = 1 if len(legs) > 1 and leg_len[0] <= hook_max_units else 0
    h1 = 1 if len(legs) - h0 > 1 and leg_len[-1] <= hook_max_units else 0
    core = legs[h0:len(legs) - h1]
    core_turns = turns[h0:len(turns) - h1]
    n = len(core)
    if n == 1:
        shape = STRAIGHT
    elif n == 2 and abs(core_turns[0] - 90.0) <= 15.0:
        shape = L_SHAPE
    elif n == 3 and _dir(core[0][0], 0)[0] * _dir(core[-1][-1], 1)[0] + \
            _dir(core[0][0], 0)[1] * _dir(core[-1][-1], 1)[1] < -0.95:
        shape = U_SHAPE
    elif core_turns and all(t <= crank_max_deg for t in core_turns):
        shape = CRANKED
    else:
        shape = COMPOUND
    return {"legs": len(legs), "core_legs": n, "bends": len(turns), "hooks": h0 + h1, "shape": shape,
            "leg_lengths_units": leg_len, "turns_deg": turns}


# ------------------------------------------------------------------ label binding
def _pt_seg(p, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    L2 = dx * dx + dy * dy
    if L2 <= TOL:
        return math.dist(p, a)
    t = max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / L2))
    return math.dist(p, (a[0] + t * dx, a[1] + t * dy))


def target_distance(p, geom):
    """Distance from a point to a target: SEG (a, b), ARC (centre, r, t0, t1) or DOT (centre, r)."""
    if geom[0] == "SEG":
        return _pt_seg(p, geom[1], geom[2])
    if geom[0] == "ARC":
        return abs(math.dist(p, geom[1]) - geom[2])
    if geom[0] == "DOT":
        return max(0.0, math.dist(p, geom[1]) - geom[2])
    raise PoolQtoError(f"unknown target geometry {geom[0]!r}")


def bind_leaders(labels, targets, *, tol):
    """labels: [(label_id, [leader tip points])]; targets: [(target_id, geom)]. A label binds every target one of
    its tips touches (within tol). A label touching nothing is UNBOUND."""
    out = {}
    for lid, tips in labels:
        hit = sorted({tid for tid, g in targets for p in tips if target_distance(p, g) <= tol})
        out[lid] = {"targets": hit, "state": "BOUND" if hit else "UNBOUND"}
    return out


def bind_nearest(labels, targets, *, max_d, margin=1.5):
    """labels with no leader: [(label_id, anchor point)]. A target id may repeat (the pieces of one bar shape); its
    distance is that of its nearest piece. Binds the nearest target within max_d only when the next target is at
    least `margin` times further; otherwise AMBIGUOUS. Nothing within max_d is UNBOUND."""
    out = {}
    for lid, p in labels:
        best = {}
        for tid, g in targets:
            best[tid] = min(best.get(tid, math.inf), target_distance(p, g))
        ds = sorted((d, tid) for tid, d in best.items())
        if not ds or ds[0][0] > max_d:
            out[lid] = {"targets": [], "state": "UNBOUND", "distance": ds[0][0] if ds else None}
        elif len(ds) > 1 and ds[1][0] < margin * ds[0][0]:
            out[lid] = {"targets": [ds[0][1], ds[1][1]], "state": "AMBIGUOUS", "distance": ds[0][0]}
        else:
            out[lid] = {"targets": [ds[0][1]], "state": "BOUND", "distance": ds[0][0]}
    return out


def run_diameters(run_labels, notations):
    """run_labels: label ids bound to one drawn run; notations: {label_id: parsed}. One diameter is consistent; two
    diameters on one drawn run mean the drawing does not show one physical bar (SOURCE_CONFLICT)."""
    dias = sorted({notations[l]["dia_mm"] for l in run_labels if notations[l]["dia_mm"] is not None})
    if not dias:
        return {"diameters": [], "state": "UNLABELLED"}
    return {"diameters": dias, "state": "CONSISTENT" if len(dias) == 1 else CONFLICT}


# ------------------------------------------------------------------ legs in regions and wall/base interfaces
def _clip_convex(a, b, poly):
    """Parameter interval [t0, t1] of segment a-b inside a convex polygon (Cyrus-Beck); None when outside."""
    area2 = math.fsum(poly[i][0] * poly[(i + 1) % len(poly)][1] - poly[(i + 1) % len(poly)][0] * poly[i][1]
                      for i in range(len(poly)))
    if abs(area2) <= TOL:
        raise PoolQtoError("degenerate region")
    sgn = 1.0 if area2 > 0 else -1.0
    t0, t1 = 0.0, 1.0
    dx, dy = b[0] - a[0], b[1] - a[1]
    for i in range(len(poly)):
        p, q = poly[i], poly[(i + 1) % len(poly)]
        nx, ny = -(q[1] - p[1]) * sgn, (q[0] - p[0]) * sgn          # inward normal
        num = nx * (a[0] - p[0]) + ny * (a[1] - p[1])
        den = nx * dx + ny * dy
        if abs(den) <= TOL:
            if num < -1e-9:
                return None
            continue
        t = -num / den
        if den > 0:
            t0 = max(t0, t)
        else:
            t1 = min(t1, t)
        if t0 - t1 > 1e-12:
            return None
    return (t0, t1)


def leg_lengths_in(run, regions):
    """Drawn length (drawing units) of a run inside each region. regions: {region_id: [convex polygons]}. An arc
    counts in the region holding its midpoint."""
    out = {rid: 0.0 for rid in regions}
    for s in run["_segs"]:
        if s[0] == "LINE":
            L = _seg_len(s)
            for rid, parts in regions.items():
                for poly in parts:
                    iv = _clip_convex(s[2], s[3], poly)
                    if iv:
                        out[rid] += (iv[1] - iv[0]) * L
        else:
            tm = 0.5 * (s[4] + s[5])
            m = (s[2][0] + s[3] * math.cos(tm), s[2][1] + s[3] * math.sin(tm))
            for rid, parts in regions.items():
                if any(_clip_convex(m, m, poly) for poly in parts):
                    out[rid] += _seg_len(s)
    return out


def owner_of(lengths, *, priority=()):
    """One COMPONENT_OWNER_ID per physical run: the region holding the larger share of its drawn length; ties by
    priority. Drawn lengths decide ownership only, never a quantity."""
    best = max(lengths.values()) if lengths else 0.0
    if best <= 0:
        return None
    tied = [r for r, v in lengths.items() if abs(v - best) <= 1e-6]
    for p in priority:
        if p in tied:
            return p
    return sorted(tied)[0]


def classify_interface(runs, regions, wall_id, base_id, *, eps_units, parallel_tol_units, priority=()):
    """runs: {run_id: run with '_segs' and 'shape'}; regions: {region_id: [convex polygons]}. For one wall/base
    junction, every run reaching the wall or the base region is classified:

      bent run with legs in the wall and the base, no parallel partner        SINGLE_BENT_BAR (one bar, counted once)
      bent run with legs in both that runs beside a wall bar                  SEPARATE_STARTER
      straight run in both regions, or a run beside a distinct partner        LAP_BETWEEN_DISTINCT_BARS (partner)
      straight run in both regions with no partner                            ANCHORED_STRAIGHT
      run only in the base                                                    BASE_ONLY
      run only in the wall (stops above the base)                             UNRESOLVED (no anchorage shown)

    Every run gets exactly one COMPONENT_OWNER_ID: the region holding the larger share of its drawn length."""
    lens = {rid: leg_lengths_in(r, regions) for rid, r in runs.items()}
    touching = {rid: l for rid, l in lens.items() if l.get(wall_id, 0) > eps_units or l.get(base_id, 0) > eps_units}

    def parallel_partner(rid):
        for oid in sorted(touching):
            if oid == rid:
                continue
            for s in runs[rid]["_segs"]:
                for t in runs[oid]["_segs"]:
                    if s[0] != "LINE" or t[0] != "LINE":
                        continue
                    da, db = _dir(s, 0), _dir(t, 0)
                    if abs(da[0] * db[1] - da[1] * db[0]) > 1e-3:
                        continue
                    if min(_pt_seg(p, t[2], t[3]) for p in (s[2], s[3])) > parallel_tol_units:
                        continue
                    proj = sorted((p[0] - s[2][0]) * da[0] + (p[1] - s[2][1]) * da[1] for p in (t[2], t[3]))
                    if min(_seg_len(s), proj[1]) - max(0.0, proj[0]) > eps_units:
                        return oid
        return None

    rows = []
    for rid in sorted(touching):
        l = touching[rid]
        in_w, in_b = l.get(wall_id, 0.0) > eps_units, l.get(base_id, 0.0) > eps_units
        bent = runs[rid].get("shape") not in (None, STRAIGHT)
        partner = parallel_partner(rid)
        if in_w and in_b:
            cls = (SEPARATE_STARTER if partner else SINGLE_BENT_BAR) if bent else \
                (LAP_BETWEEN_DISTINCT_BARS if partner else ANCHORED_STRAIGHT)
        elif partner:
            cls = LAP_BETWEEN_DISTINCT_BARS
        else:
            cls = BASE_ONLY if in_b else UNRESOLVED
        rows.append({"run_id": rid, "class": cls, "in_wall_units": l.get(wall_id, 0.0),
                     "in_base_units": l.get(base_id, 0.0), "partner": partner,
                     "component_owner_id": owner_of({wall_id: l.get(wall_id, 0.0), base_id: l.get(base_id, 0.0)},
                                                    priority=priority)})
    return rows
