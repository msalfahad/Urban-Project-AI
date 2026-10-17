"""OPENING CENSUS - wall openings from plan wall faces, with the evidence that makes each one an opening (generic).

A plan draws a masonry wall as two parallel face lines. An opening is an interval along the wall where BOTH faces
stop and start again, so it has a jamb at each end. A T-junction, a corner or two unrelated parallel lines are never
openings.

Inputs are plain data. The caller maps its own drawing layers to roles; this module knows no layer name.

Plan geometry (points in mm)
  face_lines(segments, ang_res_deg, off_tol)
      segments [(id, (x0, y0), (x1, y1))] -> collinear face lines {ang, u, n, off, cover: [[t0, t1, [ids]]]}. Segments
      on one supporting line merge; touching or overlapping intervals union.
  wall_bands(lines, t_min, t_max, min_overlap)
      pairs of parallel face lines at a separation t in [t_min, t_max], overlapping over at least min_overlap, with
      no other face line between them over that overlap (the nearest facing pair only).
  band_gaps(band, min_gap, jamb_tol, obstacles)
      intervals of the band where neither face covers. Each end must be a JAMB:
        MASONRY_JAMB   both faces end within jamb_tol of the gap end;
        COLUMN_JAMB    an obstacle (a column polygon) occupies the band strip at that end;
        CLOSURE_JAMB   a supplied closure segment (a jamb line, a perpendicular wall face) crosses the band at
                       that end over at least cover_ratio of the thickness.
      Any other end is UNBOUNDED, and the gap is reported as REJECTED, never as an opening.
  arc_bands(arcs, t_min, t_max, centre_tol) and arc_gaps(band, min_gap_mm, jamb_tol_mm)
      the same on concentric arc faces (a curved wall). Lengths are measured on the band's mid radius.
  in_strip(point, frame, s0, s1, lo, hi, margin)
      whether a point lies in the band strip over [s0, s1] (with a margin): used to bind door, glazing and arch
      evidence to one gap.
  overhead_cover(band, s0, s1, segments, off_tol, ratio)
      whether lines drawn along BOTH faces cover the gap (a header or arch drawn over an open passage).
  decide_gap(gap, evidence)
      OPENING / REJECTED with a reason. An UNBOUNDED end is a wall bend or junction (WALL_DEFLECTION). A gap closed
      at an end only by a crossing wall face is an opening only with positive evidence inside it (a door, glazing,
      an arch or overhead lines): two unrelated wall ends on one line are never an opening by themselves.
  parallel_runs(segments, ang_res_deg, max_width, join_tol, min_len)
      parallel lines grouped into runs (a glazing screen drawn with no wall faces), and run_ends(run, obstacles,
      closures) for what stands at each end of a run: a column, a crossing wall face, or nothing.
  side_points(gap, band, d)
      one point on each side of a band gap, d beyond its faces: used to find the space each side faces.

Elevations (points in mm, elevation frame)
  chain_levels(dims, anchors, node_tol)
      printed vertical dimensions [(y_a, y_b, value)] form a graph whose nodes are the measured points; from the
      anchor nodes [(y, level_mm)] each connected node gets a level by summing PRINTED values, never by measuring
      the drawing. A node reached two ways with different sums is a CHAIN_CONFLICT.
  vote_offset(e_edges, p_edges, mirror, tol)
      the offset c with e = mirror * p + c that the most (elevation edge, plan edge) pairs agree on, the runner-up
      count, and the agreeing pairs: registers an elevation's horizontal axis to a plan axis.

Stdlib only. No project data.
"""

from __future__ import annotations

import math
from collections import defaultdict

TOL = 1e-9
MASONRY_JAMB, COLUMN_JAMB, CLOSURE_JAMB, UNBOUNDED = "MASONRY_JAMB", "COLUMN_JAMB", "CLOSURE_JAMB", "UNBOUNDED"
OPENING, REJECTED = "OPENING", "REJECTED"
WALL_DEFLECTION = "WALL_DEFLECTION"
CLOSURE_WITHOUT_EVIDENCE = "CLOSURE_WITHOUT_OPENING_EVIDENCE"
EVIDENCE_KINDS = ("DOOR", "GLAZING", "ARCH", "OVERHEAD_LINES")


class OpeningCensusError(ValueError):
    pass


# ------------------------------------------------------------------ frames
def frame_of(ang_deg):
    th = math.radians(ang_deg)
    u = (math.cos(th), math.sin(th))
    return u, (-u[1], u[0])


def along(p, u):
    return p[0] * u[0] + p[1] * u[1]


def _union(iv, join_tol):
    out = []
    for t0, t1, ids in sorted(iv, key=lambda x: (x[0], x[1])):
        if out and t0 <= out[-1][1] + join_tol:
            out[-1][1] = max(out[-1][1], t1)
            out[-1][2] = sorted(set(out[-1][2]) | set(ids))
        else:
            out.append([t0, t1, sorted(set(ids))])
    return out


def face_lines(segments, ang_res_deg=0.1, off_tol=2.0, join_tol=1.0, min_len=1.0):
    groups = defaultdict(list)
    for sid, a, b in segments:
        L = math.dist(a, b)
        if L < min_len:
            continue
        ang = math.degrees(math.atan2(b[1] - a[1], b[0] - a[0])) % 180.0
        ang = round(round(ang / ang_res_deg) * ang_res_deg, 6) % 180.0
        u, n = frame_of(ang)
        off = along(a, n)
        t0, t1 = sorted((along(a, u), along(b, u)))
        groups[ang].append((off, t0, t1, sid))
    lines = []
    for ang in sorted(groups):
        u, n = frame_of(ang)
        items = sorted(groups[ang])
        cur = None
        for off, t0, t1, sid in items:
            if cur is not None and off - cur["_last"] <= off_tol:
                cur["_iv"].append((t0, t1, [sid]))
                cur["_offs"].append(off)
                cur["_last"] = off
            else:
                cur = {"ang": ang, "u": u, "n": n, "_iv": [(t0, t1, [sid])], "_offs": [off], "_last": off}
                lines.append(cur)
    for ln in lines:
        ln["off"] = sum(ln["_offs"]) / len(ln["_offs"])
        ln["cover"] = _union(ln.pop("_iv"), join_tol)
        ln["lo"], ln["hi"] = ln["cover"][0][0], ln["cover"][-1][1]
        del ln["_offs"], ln["_last"]
    for i, ln in enumerate(lines):
        ln["line_id"] = f"FL{i + 1:04d}"
    return lines


def wall_bands(lines, t_min, t_max, min_overlap=300.0):
    if t_min <= 0 or t_max < t_min:
        raise OpeningCensusError("band thickness range")
    by_ang = defaultdict(list)
    for ln in lines:
        by_ang[ln["ang"]].append(ln)
    bands = []
    for ang, ls in sorted(by_ang.items()):
        ls = sorted(ls, key=lambda l: l["off"])
        for i, A in enumerate(ls):
            for B in ls[i + 1:]:
                t = B["off"] - A["off"]
                if t > t_max + TOL:
                    break
                if t < t_min - TOL:
                    continue
                lo, hi = max(A["lo"], B["lo"]), min(A["hi"], B["hi"])
                if hi - lo < min_overlap:
                    continue
                between = [C for C in ls if A["off"] + TOL < C["off"] < B["off"] - TOL and
                           min(C["hi"], hi) - max(C["lo"], lo) > TOL]
                if between:
                    continue
                bands.append({"ang": ang, "u": A["u"], "n": A["n"], "A": A, "B": B, "t": t, "lo": lo, "hi": hi,
                              "band_id": f"WB-{A['line_id']}-{B['line_id']}"})
    return bands


def _covers(cov, lo, hi):
    out = []
    for t0, t1, ids in cov:
        if t1 < lo or t0 > hi:
            continue
        out.append((max(t0, lo), min(t1, hi), ids))
    return out


def in_strip(p, frame, s0, s1, lo, hi, margin=0.0):
    u, n = frame
    s, o = along(p, u), along(p, n)
    return s0 - margin <= s <= s1 + margin and lo - margin <= o <= hi + margin


def _obstacle_at(band, s, side, obstacles, reach):
    """an obstacle polygon occupies the band strip just beyond the gap end s (side -1 = before, +1 = after)."""
    u, n = band["u"], band["n"]
    lo, hi = sorted((band["A"]["off"], band["B"]["off"]))
    for oid, poly in obstacles:
        ss = [along(p, u) for p in poly]
        oo = [along(p, n) for p in poly]
        if max(oo) < lo + TOL or min(oo) > hi - TOL:
            continue
        if side < 0 and min(ss) <= s + TOL and max(ss) >= s - reach:
            if abs(max(ss) - s) <= reach:
                return oid
        if side > 0 and max(ss) >= s - TOL and min(ss) <= s + reach:
            if abs(min(ss) - s) <= reach:
                return oid
    return None


def _closure_at(band, s, closures, jamb_tol, cover_ratio):
    """a segment crossing the band strip at s (within jamb_tol), spanning at least cover_ratio of the thickness."""
    u, n = band["u"], band["n"]
    lo, hi = sorted((band["A"]["off"], band["B"]["off"]))
    t = hi - lo
    for cid, a, b in closures:
        sa, sb, oa, ob = along(a, u), along(b, u), along(a, n), along(b, n)
        if abs(oa - ob) <= TOL:
            continue
        o0, o1 = max(lo, min(oa, ob)), min(hi, max(oa, ob))
        if o1 - o0 < cover_ratio * t:
            continue
        for o in (o0, o1, (o0 + o1) / 2):
            ss = sa + (sb - sa) * (o - oa) / (ob - oa)
            if abs(ss - s) > jamb_tol:
                break
        else:
            return cid
    return None


def band_gaps(band, min_gap=250.0, jamb_tol=30.0, obstacles=(), column_reach=60.0, closures=(), cover_ratio=0.9):
    """closures: [(id, a, b)] segments that may close a gap end across the band (a jamb line, a perpendicular wall
    face). An end closed only by a closure is a CLOSURE_JAMB."""
    lo, hi = band["lo"], band["hi"]
    A, B = _covers(band["A"]["cover"], lo, hi), _covers(band["B"]["cover"], lo, hi)
    both = _union([(a, b, ids) for a, b, ids in A + B], 1.0)
    out = []
    for (x0, e0, ids0), (s1, x1, ids1) in zip(both, both[1:]):
        g = s1 - e0
        if g < min_gap:
            continue
        ends = {}
        for side, s in ((-1, e0), (1, s1)):
            fa = [t for t in A if (abs(t[1] - s) <= jamb_tol if side < 0 else abs(t[0] - s) <= jamb_tol)]
            fb = [t for t in B if (abs(t[1] - s) <= jamb_tol if side < 0 else abs(t[0] - s) <= jamb_tol)]
            col = _obstacle_at(band, s, side, obstacles, column_reach)
            if col is not None:
                ends[side] = (COLUMN_JAMB, col)
            elif fa and fb:
                ends[side] = (MASONRY_JAMB, None)
            else:
                cl = _closure_at(band, s, closures, jamb_tol, cover_ratio)
                ends[side] = (CLOSURE_JAMB, cl) if cl is not None else (UNBOUNDED, None)
        state = OPENING if all(v[0] != UNBOUNDED for v in ends.values()) else REJECTED
        out.append({"band_id": band["band_id"], "s0": e0, "s1": s1, "width": g, "t": band["t"],
                    "start_jamb": ends[-1][0], "start_column": ends[-1][1],
                    "end_jamb": ends[1][0], "end_column": ends[1][1], "state": state})
    return out


def overhead_cover(band, s0, s1, segments, off_tol=30.0, ratio=0.9, ang_tol_deg=0.2):
    """True when segments parallel to the band, lying on EACH face offset (within off_tol), cover at least `ratio`
    of [s0, s1]."""
    if s1 <= s0:
        raise OpeningCensusError("empty interval")
    u, n = band["u"], band["n"]
    out = []
    for face in (band["A"]["off"], band["B"]["off"]):
        iv = []
        for sid, a, b in segments:
            ang = math.degrees(math.atan2(b[1] - a[1], b[0] - a[0])) % 180.0
            d = abs(ang - band["ang"]) % 180.0
            if min(d, 180.0 - d) > ang_tol_deg:
                continue
            if abs(along(a, n) - face) > off_tol or abs(along(b, n) - face) > off_tol:
                continue
            t0, t1 = sorted((along(a, u), along(b, u)))
            if t1 > s0 and t0 < s1:
                iv.append((max(t0, s0), min(t1, s1), [sid]))
        cov = math.fsum(t1 - t0 for t0, t1, _ in _union(iv, 1.0))
        out.append(cov >= ratio * (s1 - s0) - TOL)
    return all(out)


def decide_gap(gap, evidence):
    """gap: a band_gaps / arc_gaps / run record; evidence: iterable of EVIDENCE_KINDS found inside it."""
    ev = sorted(set(evidence))
    bad = [k for k in ev if k not in EVIDENCE_KINDS]
    if bad:
        raise OpeningCensusError(f"unknown evidence {bad}")
    ends = (gap["start_jamb"], gap["end_jamb"])
    if UNBOUNDED in ends:
        return REJECTED, WALL_DEFLECTION
    if CLOSURE_JAMB in ends and not ev:
        return REJECTED, CLOSURE_WITHOUT_EVIDENCE
    return OPENING, None


def side_points(gap, band, d):
    """(point on face A's side, point on face B's side) at the gap middle, d beyond each face."""
    u, n = band["u"], band["n"]
    sm = (gap["s0"] + gap["s1"]) / 2.0
    lo, hi = sorted((band["A"]["off"], band["B"]["off"]))
    pt = lambda o: (sm * u[0] + o * n[0], sm * u[1] + o * n[1])
    a_side = lo - d if band["A"]["off"] <= band["B"]["off"] else hi + d
    b_side = hi + d if band["A"]["off"] <= band["B"]["off"] else lo - d
    return pt(a_side), pt(b_side)


def parallel_runs(segments, ang_res_deg=0.1, max_width=300.0, join_tol=1.0, min_len=100.0):
    """segments [(id, a, b)] -> runs of parallel lines that overlap along their direction and lie within max_width
    of each other across it: {ang, u, n, s0, s1, lo, hi, width, ids, run_id}. A single line is a run of width 0."""
    lines = face_lines(segments, ang_res_deg=ang_res_deg, off_tol=0.5, join_tol=join_tol, min_len=1.0)
    by_ang = defaultdict(list)
    for ln in lines:
        for t0, t1, ids in ln["cover"]:
            if t1 - t0 >= min_len:
                by_ang[ln["ang"]].append([ln["off"], t0, t1, ids])
    runs = []
    for ang in sorted(by_ang):
        u, n = frame_of(ang)
        items = sorted(by_ang[ang], key=lambda x: (x[1], x[0]))
        groups = []
        for off, t0, t1, ids in items:
            for g in groups:
                if (min(g["s1"], t1) - max(g["s0"], t0) > join_tol and
                        max(g["hi"], off) - min(g["lo"], off) <= max_width + TOL):
                    g["s0"], g["s1"] = min(g["s0"], t0), max(g["s1"], t1)
                    g["lo"], g["hi"] = min(g["lo"], off), max(g["hi"], off)
                    g["ids"] = sorted(set(g["ids"]) | set(ids))
                    break
            else:
                groups.append({"ang": ang, "u": u, "n": n, "s0": t0, "s1": t1, "lo": off, "hi": off,
                               "ids": sorted(set(ids))})
        runs += groups
    for i, r in enumerate(runs):
        r["width"] = r["s1"] - r["s0"]
        r["run_id"] = f"PR{i + 1:04d}"
    return runs


def run_ends(run, obstacles=(), closures=(), reach=60.0, jamb_tol=30.0, cover_ratio=0.9):
    """what stands at each end of a run: COLUMN_JAMB (an obstacle polygon), CLOSURE_JAMB (a crossing segment) or
    UNBOUNDED. Returned in the band_gaps record shape (s0, s1, width, start_/end_jamb and the id found)."""
    band = {"u": run["u"], "n": run["n"], "A": {"off": run["lo"]}, "B": {"off": run["hi"]}}
    if run["hi"] - run["lo"] <= TOL:
        raise OpeningCensusError("a run of one line has no thickness to close")
    ends = {}
    for side, s in ((-1, run["s0"]), (1, run["s1"])):
        col = _obstacle_at(band, s, side, obstacles, reach)
        if col is not None:
            ends[side] = (COLUMN_JAMB, col)
            continue
        cl = _closure_at(band, s, closures, jamb_tol, cover_ratio)
        ends[side] = (CLOSURE_JAMB, cl) if cl is not None else (UNBOUNDED, None)
    return {"band_id": run["run_id"], "s0": run["s0"], "s1": run["s1"], "width": run["width"],
            "t": run["hi"] - run["lo"], "start_jamb": ends[-1][0], "start_column": ends[-1][1],
            "end_jamb": ends[1][0], "end_column": ends[1][1]}


# ------------------------------------------------------------------ elevations
CHAIN_CONFLICT = "CHAIN_CONFLICT"


def chain_levels(dims, anchors, node_tol=1.0):
    """dims [(y_a, y_b, value)], anchors [(y, level)] -> ({node_y: level}, conflicts). Node y values that lie
    within node_tol are one node."""
    nodes = []

    def node(y):
        for i, v in enumerate(nodes):
            if abs(v - y) <= node_tol:
                return i
        nodes.append(y)
        return len(nodes) - 1

    adj = defaultdict(list)
    for ya, yb, v in dims:
        if v <= 0:
            raise OpeningCensusError("dimension value must be positive")
        a, b = node(ya), node(yb)
        if a == b:
            continue
        lo, hi = (a, b) if nodes[a] < nodes[b] else (b, a)
        adj[lo].append((hi, v))
        adj[hi].append((lo, -v))
    level, conflicts = {}, []
    queue = []
    for y, lv in anchors:
        i = node(y)
        if i in level and abs(level[i] - lv) > 1e-6:
            conflicts.append((nodes[i], level[i], lv))
        level[i] = lv
        queue.append(i)
    while queue:
        i = queue.pop(0)
        for j, v in sorted(adj[i]):
            lv = level[i] + v
            if j in level:
                if abs(level[j] - lv) > 0.5:
                    conflicts.append((nodes[j], level[j], lv))
                continue
            level[j] = lv
            queue.append(j)
    return {nodes[i]: lv for i, lv in level.items()}, conflicts


def vote_offset(e_edges, p_edges, mirror=1, tol=1.0):
    """every (e, p) pair proposes c = e - mirror * p; a candidate's support is the number of elevation edges that
    some plan edge places within tol of it. The runner-up is the best candidate more than 10 tol away."""
    if mirror not in (1, -1):
        raise OpeningCensusError("mirror is +1 or -1")
    cands = sorted({round(e - mirror * p, 6) for e in e_edges for p in p_edges})
    if not cands:
        return None, 0, 0, []

    def support(c):
        return sorted((i, j) for i, e in enumerate(e_edges) for j, p in enumerate(p_edges)
                      if abs(e - mirror * p - c) <= tol)

    scored = []
    for c in cands:
        pairs = support(c)
        scored.append((len({i for i, _ in pairs}), c, pairs))
    scored.sort(key=lambda x: (-x[0], x[1]))
    n, best, pairs = scored[0]
    # the centre of the agreeing pairs (a stable offset, not the first rounding)
    best = sum(e_edges[i] - mirror * p_edges[j] for i, j in pairs) / len(pairs)
    second = max([k for k, c, _ in scored if abs(c - best) > 10 * tol] or [0])
    return best, n, second, pairs


# ------------------------------------------------------------------ curved walls
def _norm(a):
    return a % 360.0


def arc_bands(arcs, t_min, t_max, centre_tol=2.0):
    """arcs [(id, (cx, cy), r, a0_deg, a1_deg)] counter-clockwise. Concentric arcs whose radii differ by t in
    [t_min, t_max] and whose angular extents overlap form a curved band."""
    groups = []
    for aid, c, r, a0, a1 in arcs:
        for g in groups:
            if math.dist(g["c"], c) <= centre_tol:
                g["arcs"].append((aid, r, _norm(a0), _norm(a1)))
                break
        else:
            groups.append({"c": c, "arcs": [(aid, r, _norm(a0), _norm(a1))]})
    bands = []
    for g in groups:
        radii = defaultdict(list)
        for aid, r, a0, a1 in g["arcs"]:
            radii[round(r, 1)].append((a0, a1 if a1 > a0 else a1 + 360.0, aid))
        rs = sorted(radii)
        for i, r1 in enumerate(rs):
            for r2 in rs[i + 1:]:
                t = r2 - r1
                if not t_min - TOL <= t <= t_max + TOL:
                    continue
                if any(r1 + TOL < r < r2 - TOL for r in rs):
                    continue
                bands.append({"c": g["c"], "r_in": r1, "r_out": r2, "t": t,
                              "inner": _union([(a, b, [i_]) for a, b, i_ in radii[r1]], 0.05),
                              "outer": _union([(a, b, [i_]) for a, b, i_ in radii[r2]], 0.05),
                              "band_id": f"WA-{round(g['c'][0])}-{round(g['c'][1])}-{r1:g}-{r2:g}"})
    return bands


def arc_gaps(band, min_gap_mm=250.0, jamb_tol_mm=30.0):
    rm = (band["r_in"] + band["r_out"]) / 2.0
    inner, outer = band["inner"], band["outer"]
    lo = max(inner[0][0], outer[0][0])
    hi = min(inner[-1][1], outer[-1][1])
    both = _union([(a, b, ids) for a, b, ids in _covers(inner, lo, hi) + _covers(outer, lo, hi)], 0.05)
    tol = math.degrees(jamb_tol_mm / rm)
    out = []
    for (x0, e0, _), (s1, x1, _) in zip(both, both[1:]):
        g = math.radians(s1 - e0) * rm
        if g < min_gap_mm:
            continue
        ok = all(any(abs(t[1] - e0) <= tol for t in f) and any(abs(t[0] - s1) <= tol for t in f) for f in (inner, outer))
        out.append({"band_id": band["band_id"], "a0": e0, "a1": s1, "width_mid_arc": g,
                    "chord_mid": 2 * rm * math.sin(math.radians(s1 - e0) / 2), "r_mid": rm, "t": band["t"],
                    "start_jamb": MASONRY_JAMB if ok else UNBOUNDED, "end_jamb": MASONRY_JAMB if ok else UNBOUNDED,
                    "state": OPENING if ok else REJECTED})
    return out


def in_arc_strip(p, band, a0, a1, margin_deg=1.0, margin_mm=30.0):
    cx, cy = band["c"]
    r = math.dist(p, (cx, cy))
    a = _norm(math.degrees(math.atan2(p[1] - cy, p[0] - cx)))
    if a < a0 - margin_deg - 180.0:
        a += 360.0
    return (band["r_in"] - margin_mm <= r <= band["r_out"] + margin_mm and
            a0 - margin_deg <= a <= a1 + margin_deg)
