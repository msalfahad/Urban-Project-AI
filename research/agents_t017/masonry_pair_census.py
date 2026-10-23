"""T-017: PAIR_MIDLINE_CENSUS_V1, an independent masonry census from the raw wall-face linework (any villa).

Purpose (defect D-N10-03): a reader-side census of every masonry wall that shares NO code with the engine's wall stage
(engine/source/arch_walls.py), MASONRY_CENTRELINE_V1 / V2 or MASONRY_AREA_V1. It imports only the standard library.
It is a CHECK, never a quantity source: its numbers are compared with the ledger and every disagreement is named with
its cause; it never replaces or adjusts a ledger value (ERS s.2.3: reconstruct from first principles, s.2.4 reconcile).

Method (general rules, no project constant; inputs in metres):
 1. Face lines: every straight segment on the wall-face layer(s); collinear overlapping or touching segments are merged
    into maximal lines per direction (angle mod 180, tolerance ANG_TOL) and offset (perpendicular, tolerance OFF_TOL).
 2. Pairs: two parallel lines at a separation equal to a thickness class (+- T_TOL) whose projections overlap form a
    SOLID piece on their midline (both faces drawn). Nearest separation first; each stretch of a face is used once.
 3. Gaps along one midline (same thickness, same midline offset) between consecutive solid pieces are classified from
    the drawing, in this order: COLUMN (the gap strip is covered >= COL_COVER by a column outline: cut, not masonry,
    ends the run), ONE_FACE (one face continues across the gap: a junction where another wall abuts; masonry of this
    wall, IN the run), OPENING (neither face, but a door / window entity lies in the gap strip and the gap <= OPEN_MAX:
    in the run, its width listed), CROSSING (neither face, a perpendicular solid piece fills the gap: counted once, in
    the wall with the lower run key, and listed), SPLIT (none of these: the run ends; listed).
 4. Run ends: an end that meets a perpendicular run at an L (the two midlines intersect within t of both ends) is
    carried to the midline intersection (an L corner meets at the centrelines, so the corner square is counted once);
    an end on the face of a through wall (T stem) stays on that face (owner Q-69 B: masonry never in two segments);
    other ends stay as drawn (FREE).
 5. Caps: a solid piece no longer than the thickness of a perpendicular run it closes (a jamb or end cap line pair) is
    not a wall; it is listed as CAP.
 Output per run: thickness, axis direction, midline offset, start / end on the axis, solid length, opening widths,
 one-face length, end kinds, and the listed gaps. arch_run_m = solid + one-face + openings (+ L extensions); this is the
 quantity compared with the ledger's architectural run (openings stay in the run, Q-73 deducts their area).
Curved walls (concentric arcs) are not read by this census: they are reported as NOT_READ with their arc count, never 0.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

CLASSES = (0.10, 0.15, 0.20, 0.25, 0.30, 0.40)
ANG_TOL = math.radians(0.3)
OFF_TOL = 0.004
T_TOL = 0.006
JOIN_TOL = 0.003
MIN_PIECE = 0.02
COL_COVER = 0.5
OPEN_MAX = 3.0
METHOD = "PAIR_MIDLINE_CENSUS_V1"


@dataclass
class Line:
    ang: float          # direction in [0, pi)
    off: float          # perpendicular offset of the infinite line
    s0: float
    s1: float           # extent along the axis (s0 < s1)


@dataclass
class Run:
    key: str
    t: float
    ang: float
    off: float          # midline offset
    s0: float
    s1: float
    solid_m: float = 0.0
    one_face_m: float = 0.0
    openings: list = field(default_factory=list)       # widths
    crossings: list = field(default_factory=list)      # widths counted here
    crossings_elsewhere: list = field(default_factory=list)
    ends: list = field(default_factory=lambda: ["FREE", "FREE"])
    ext_m: list = field(default_factory=lambda: [0.0, 0.0])

    col_cut_m: float = 0.0

    @property
    def arch_run_m(self) -> float:
        return self.s1 - self.s0 + self.ext_m[0] + self.ext_m[1] - sum(self.crossings_elsewhere) - self.col_cut_m

    def endpoints(self):
        return (_pt(self.ang, self.off, self.s0 - self.ext_m[0]), _pt(self.ang, self.off, self.s1 + self.ext_m[1]))


def _axis(ang):
    return (math.cos(ang), math.sin(ang)), (-math.sin(ang), math.cos(ang))


def _pt(ang, off, s):
    (ux, uy), (nx, ny) = _axis(ang)
    return (ux * s + nx * off, uy * s + ny * off)


def _norm_ang(a):
    a = a % math.pi
    if math.pi - a < ANG_TOL:
        a = 0.0
    return a


def to_line(a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    if math.hypot(dx, dy) < 1e-6:
        return None
    ang = _norm_ang(math.atan2(dy, dx))
    (ux, uy), (nx, ny) = _axis(ang)
    sa, sb = a[0] * ux + a[1] * uy, b[0] * ux + b[1] * uy
    off = ((a[0] + b[0]) * nx + (a[1] + b[1]) * ny) / 2
    return Line(ang, off, min(sa, sb), max(sa, sb))


def merge_lines(segments):
    """Merge collinear segments into maximal lines (same direction class, same offset, touching or overlapping)."""
    ls = [l for l in (to_line(a, b) for a, b in segments) if l]
    groups = []
    for l in sorted(ls, key=lambda q: (q.ang, q.off)):
        for g in groups:
            if abs(g[0].ang - l.ang) < ANG_TOL and abs(g[0].off - l.off) < OFF_TOL:
                g.append(l)
                break
        else:
            groups.append([l])
    out = []
    for g in groups:
        ang = g[0].ang
        off = sum(q.off for q in g) / len(g)
        iv = sorted((q.s0, q.s1) for q in g)
        cur = list(iv[0])
        for a, b in iv[1:]:
            if a <= cur[1] + JOIN_TOL:
                cur[1] = max(cur[1], b)
            else:
                out.append(Line(ang, off, cur[0], cur[1]))
                cur = [a, b]
        out.append(Line(ang, off, cur[0], cur[1]))
    return out


def _sub(iv, a, b):
    """Interval list minus [a, b]."""
    out = []
    for x, y in iv:
        if b <= x or a >= y:
            out.append((x, y))
            continue
        if a > x:
            out.append((x, a))
        if b < y:
            out.append((b, y))
    return [(x, y) for x, y in out if y - x > 1e-6]


def pair_pieces(lines, classes=CLASSES):
    """Solid pieces: (t, ang, mid offset, s0, s1, line index A, line index B), nearest separation first."""
    cand = []
    for i, a in enumerate(lines):
        for j in range(i + 1, len(lines)):
            b = lines[j]
            if abs(a.ang - b.ang) > ANG_TOL:
                continue
            d = abs(a.off - b.off)
            t = next((c for c in classes if abs(d - c) <= T_TOL), None)
            if t is None:
                continue
            s0, s1 = max(a.s0, b.s0), min(a.s1, b.s1)
            if s1 - s0 < MIN_PIECE:
                continue
            cand.append((d, i, j, t))
    free = {i: [(l.s0, l.s1)] for i, l in enumerate(lines)}
    pieces = []
    for d, i, j, t in sorted(cand):
        a, b = lines[i], lines[j]
        for x0, x1 in list(free[i]):
            for y0, y1 in list(free[j]):
                s0, s1 = max(x0, y0, a.s0, b.s0), min(x1, y1, a.s1, b.s1)
                if s1 - s0 < MIN_PIECE:
                    continue
                pieces.append((t, a.ang, (a.off + b.off) / 2, s0, s1, i, j))
                free[i] = _sub(free[i], s0, s1)
                free[j] = _sub(free[j], s0, s1)
    return pieces


def _covered(lines_on_offset, a, b):
    """Length of [a, b] covered by the given lines."""
    iv = sorted((max(l.s0, a), min(l.s1, b)) for l in lines_on_offset if min(l.s1, b) > max(l.s0, a))
    tot, cur = 0.0, None
    for x, y in iv:
        if cur is None or x > cur[1]:
            if cur:
                tot += cur[1] - cur[0]
            cur = [x, y]
        else:
            cur[1] = max(cur[1], y)
    if cur:
        tot += cur[1] - cur[0]
    return tot


def _strip_hits(ang, off, t, a, b, pts):
    (ux, uy), (nx, ny) = _axis(ang)
    for x, y in pts:
        s, o = x * ux + y * uy, x * nx + y * ny
        if a - 0.02 <= s <= b + 0.02 and abs(o - off) <= t / 2 + 0.05:
            return True
    return False


def _col_cover(ang, off, t, a, b, columns):
    """Share of the gap strip [a, b] x t covered by axis-aligned-in-strip column outlines (polygons, metres)."""
    if b - a <= 0:
        return 0.0
    (ux, uy), (nx, ny) = _axis(ang)
    best = 0.0
    for poly in columns:
        ss = [x * ux + y * uy for x, y in poly]
        oo = [x * nx + y * ny for x, y in poly]
        ds = max(0.0, min(max(ss), b) - max(min(ss), a))
        do = max(0.0, min(max(oo), off + t / 2) - max(min(oo), off - t / 2))
        best += ds * do
    return min(1.0, best / ((b - a) * t))


def _head_lines(others, ang, off, t, a, b):
    """Both face offsets of the gap carried across it by lines on another layer (a passage head or opening symbol)."""
    w = b - a
    for o in (off - t / 2, off + t / 2):
        on = [l for l in others if abs(l.ang - ang) < ANG_TOL and abs(l.off - o) < OFF_TOL]
        if _covered(on, a, b) < w - 0.01:
            return False
    return True


def _crossing(groups, caps, ang, off, t, a, b):
    """A gap filled by a perpendicular wall drawn through it (neither face of this wall drawn): CROSSING when this wall
    keeps the square (the lower direction angle, then the lower offset: one fixed choice, counted once and listed),
    CROSSING_OTHER when the perpendicular wall keeps it; None if no perpendicular wall fills the gap."""
    w = b - a
    c = _pt(ang, off, (a + b) / 2)
    for (t2, ang2, off2), ps in groups.items():
        if abs(abs(ang2 - ang) - math.pi / 2) > ANG_TOL or abs(t2 - w) > T_TOL:
            continue
        (ux, uy), (nx, ny) = _axis(ang2)
        s, o = c[0] * ux + c[1] * uy, c[0] * nx + c[1] * ny
        if abs(o - off2) > 0.01:
            continue
        pre = any(q[4] >= s - t / 2 - 0.01 and q[3] <= s - t / 2 + 0.01 for q in ps if id(q) not in caps)
        post = any(q[3] <= s + t / 2 + 0.01 and q[4] >= s + t / 2 - 0.01 for q in ps if id(q) not in caps)
        if pre and post:
            return "CROSSING" if (round(ang, 4), off) < (round(ang2, 4), off2) else "CROSSING_OTHER"
    return None


def _column_cut(run, columns):
    """Length of the run (with its end extensions) that lies inside column outlines covering at least half of the
    wall thickness: a column is cut out of the masonry run (it is concrete), so it never counts as block length."""
    a, b = run.s0 - run.ext_m[0], run.s1 + run.ext_m[1]
    (ux, uy), (nx, ny) = _axis(run.ang)
    iv = []
    for poly in columns:
        ss = [x * ux + y * uy for x, y in poly]
        oo = [x * nx + y * ny for x, y in poly]
        do = max(0.0, min(max(oo), run.off + run.t / 2) - max(min(oo), run.off - run.t / 2))
        if do < COL_COVER * run.t:
            continue
        x0, x1 = max(min(ss), a), min(max(ss), b)
        if x1 - x0 > JOIN_TOL:
            iv.append((x0, x1))
    tot, cur = 0.0, None
    for x, y in sorted(iv):
        if cur is None or x > cur[1]:
            if cur:
                tot += cur[1] - cur[0]
            cur = [x, y]
        else:
            cur[1] = max(cur[1], y)
    if cur:
        tot += cur[1] - cur[0]
    return tot


def census(wall_segments, columns=(), opening_points=(), classes=CLASSES, floor="F", other_segments=()):
    """The census of one floor. wall_segments: [((x, y), (x, y))] in metres on the wall-face layer(s); columns: column
    outline polygons [[(x, y), ...]]; opening_points: points of door / window entities (vertices) in metres;
    other_segments: straight segments on every other layer (head lines and opening symbols drawn across a gap)."""
    check_units(wall_segments)
    lines = merge_lines(wall_segments)
    others = merge_lines(other_segments)
    pieces = pair_pieces(lines, classes)
    groups = {}
    for p in pieces:
        k = None
        for g in groups:
            if g[0] == p[0] and abs(g[1] - p[1]) < ANG_TOL and abs(g[2] - p[2]) < OFF_TOL:
                k = g
                break
        groups.setdefault(k or (p[0], p[1], p[2]), []).append(p)
    # caps: pieces no longer than the thickness of a perpendicular group they close
    def perpendicular(a1, a2):
        return abs(abs(a1 - a2) - math.pi / 2) < ANG_TOL
    caps, listed = set(), []
    for g, ps in groups.items():
        for p in ps:
            ln = p[4] - p[3]
            if ln > 0.42:
                continue
            mid = _pt(p[1], p[2], (p[3] + p[4]) / 2)
            for g2, ps2 in groups.items():
                if g2 is g or not perpendicular(g[1], g2[1]) or abs(g2[0] - ln) > T_TOL:
                    continue
                (ux, uy), (nx, ny) = _axis(g2[1])
                s, o = mid[0] * ux + mid[1] * uy, mid[0] * nx + mid[1] * ny
                if abs(o - g2[2]) <= g2[0] / 2 + 0.01 and any(abs(s - q[3]) <= p[0] / 2 + 0.01 or abs(s - q[4]) <= p[0] / 2 + 0.01 for q in ps2):
                    caps.add(id(p))
                    listed.append({"what": "CAP", "t": p[0], "len": round(ln, 4)})
                    break
    runs, gaps = [], []
    for g, ps in sorted(groups.items(), key=lambda kv: (round(kv[0][1], 4), round(kv[0][2], 3), kv[0][0])):
        t, ang, off = g
        ps = sorted((p for p in ps if id(p) not in caps), key=lambda p: p[3])
        if not ps:
            continue
        side_a = [l for l in lines if abs(l.ang - ang) < ANG_TOL and abs(l.off - (off - t / 2)) < OFF_TOL]
        side_b = [l for l in lines if abs(l.ang - ang) < ANG_TOL and abs(l.off - (off + t / 2)) < OFF_TOL]
        cur = None
        for p in ps:
            if cur is None:
                cur = Run("", t, ang, off, p[3], p[4], solid_m=p[4] - p[3])
                cur.faces = (side_a, side_b)
                continue
            a, b = cur.s1, p[3]
            if b - a <= JOIN_TOL:
                cur.s1 = max(cur.s1, p[4]); cur.solid_m += p[4] - p[3]
                continue
            # a column inside the gap ends the run there; each remaining part of the gap is classified on its own
            civ = _column_intervals(ang, off, t, a, b, columns)
            parts = []
            if civ:
                c0, c1 = civ[0][0], civ[-1][1]
                parts = [(a, c0, "BEFORE"), (c1, b, "AFTER")]
            else:
                parts = [(a, b, "WHOLE")]
            new_start = None
            split_before = split_after = False
            for x0, x1, where in parts:
                w = x1 - x0
                if w <= JOIN_TOL:
                    continue
                subs = _classify_parts(ang, off, t, x0, x1, side_a, side_b, opening_points, others, groups, caps)
                for k_, a_, b_ in subs:
                    gaps.append({"floor": floor, "t": t, "kind": k_, "width": round(b_ - a_, 4), "_ang": ang,
                                 "_off": off, "_a": a_, "_b": b_})
                inrun = all(k_ in ("ONE_FACE", "OPENING", "CROSSING") for k_, _a, _b in subs)
                kind = subs[0][0] if len(subs) == 1 or inrun else next(k_ for k_, _a, _b in subs
                                                                       if k_ not in ("ONE_FACE", "OPENING", "CROSSING"))
                if where == "AFTER":
                    if inrun:
                        new_start = (x0, subs)
                    else:
                        split_after = True
                    continue
                if where == "BEFORE" and not inrun:
                    split_before = True
                if inrun:
                    for k_, a_, b_ in subs:
                        _absorb(cur, k_, b_ - a_)
                    cur.s1 = x1
                    if where == "WHOLE":
                        cur.s1 = p[4]; cur.solid_m += p[4] - p[3]
                else:
                    stop = {"CROSSING_OTHER": "X"}.get(kind)
                    if stop:
                        cur.ends[1] = stop
                    if where == "WHOLE":
                        runs.append(cur)
                        cur = Run("", t, ang, off, p[3], p[4], solid_m=p[4] - p[3])
                        cur.faces = (side_a, side_b)
                        if stop:
                            cur.ends[0] = stop
            if civ:
                gaps.append({"floor": floor, "t": t, "kind": "COLUMN", "width": round(civ[-1][1] - civ[0][0], 4),
                             "_ang": ang, "_off": off, "_a": civ[0][0], "_b": civ[-1][1]})
                # the run ends AT the column only when nothing unbridged lies between them (else it ends as drawn)
                if not split_before:
                    cur.ends[1] = "COLUMN"
                    cur.s1 = max(cur.s1, civ[0][0])
                runs.append(cur)
                s0 = civ[-1][1] if (new_start or not split_after) else p[3]
                cur = Run("", t, ang, off, min(s0, p[3]), p[4], solid_m=p[4] - p[3])
                cur.faces = (side_a, side_b)
                if not split_after:
                    cur.ends[0] = "COLUMN"
                if new_start:
                    for k_, a_, b_ in new_start[1]:
                        _absorb(cur, k_, b_ - a_)
        runs.append(cur)
    for i, r in enumerate(runs):
        r.key = f"{floor}-PC{i + 1:03d}"
    _ends(runs)
    for r in runs:
        r.col_cut_m = _column_cut(r, columns)
        r.faces = None
    return {"method": METHOD, "floor": floor, "runs": runs, "gaps": gaps, "listed": listed,
            "lines": len(lines), "pieces": len(pieces)}


def _absorb(run, kind, w):
    if kind == "ONE_FACE":
        run.one_face_m += w
    elif kind == "CROSSING":
        run.crossings.append(round(w, 4))
    else:
        run.openings.append(round(w, 4))


def _classify_parts(ang, off, t, a, b, side_a, side_b, opening_points, others, groups, caps):
    """Classify a gap as one piece; when that gives SPLIT, cut it at every end of a face line or a head line inside
    it and classify each part (a passage head beside a junction square, for example). Consecutive parts of one kind
    are merged. Returns [(kind, a, b)]."""
    k = _classify(ang, off, t, a, b, side_a, side_b, opening_points, others, groups, caps)
    if k != "SPLIT":
        return [(k, a, b)]
    cuts = {a, b}
    for o, ls in ((off - t / 2, side_a), (off + t / 2, side_b)):
        cand = list(ls) + [l for l in others if abs(l.ang - ang) < ANG_TOL and abs(l.off - o) < OFF_TOL]
        for l in cand:
            for x in (l.s0, l.s1):
                if a + 0.02 < x < b - 0.02:
                    cuts.add(x)
    cuts = sorted(cuts)
    if len(cuts) == 2:
        return [(k, a, b)]
    out = []
    for x0, x1 in zip(cuts, cuts[1:]):
        kk = _classify(ang, off, t, x0, x1, side_a, side_b, opening_points, others, groups, caps)
        if out and out[-1][0] == kk:
            out[-1] = (kk, out[-1][1], x1)
        else:
            out.append((kk, x0, x1))
    return out


def _classify(ang, off, t, a, b, side_a, side_b, opening_points, others, groups, caps):
    w = b - a
    if max(_covered(side_a, a, b), _covered(side_b, a, b)) >= w - JOIN_TOL:
        return "ONE_FACE"
    if w <= OPEN_MAX and _strip_hits(ang, off, t, a, b, opening_points):
        return "OPENING"
    if w <= OPEN_MAX and _head_lines(others, ang, off, t, a, b):
        return "OPENING"     # a passage: head / symbol lines drawn on both faces across the gap
    return _crossing(groups, caps, ang, off, t, a, b) or "SPLIT"


def _column_intervals(ang, off, t, a, b, columns):
    (ux, uy), (nx, ny) = _axis(ang)
    iv = []
    for poly in columns:
        ss = [x * ux + y * uy for x, y in poly]
        oo = [x * nx + y * ny for x, y in poly]
        do = max(0.0, min(max(oo), off + t / 2) - max(min(oo), off - t / 2))
        if do < COL_COVER * t:
            continue
        x0, x1 = max(min(ss), a), min(max(ss), b)
        if x1 - x0 > JOIN_TOL:
            iv.append((x0, x1))
    return sorted(iv)


def _tail(run, e):
    """How far a face of the run continues beyond its end e (0 = start, 1 = end), at most 0.45 m: a corner or junction
    square drawn by this wall's face."""
    best = 0.0
    for side in run.faces or ():
        for l in side:
            if e == 1 and l.s0 <= run.s1 + JOIN_TOL and l.s1 > run.s1:
                best = max(best, min(l.s1 - run.s1, 0.45))
            if e == 0 and l.s1 >= run.s0 - JOIN_TOL and l.s0 < run.s0:
                best = max(best, min(run.s0 - l.s0, 0.45))
    return best


def _ends(runs):
    """Run ends from the drawn faces. A corner or junction square lies beyond a solid end when a perpendicular wall q
    ends against this wall's face there. If this wall's face continues across q to q's far face (a tail of q.t), the
    square is drawn by this wall: shared at the midlines when q's face also continues across this wall (an L drawn with
    both outer faces: each wall to the other's midline), else all this wall's (JUNCTION_OWN, to q's far face). No such
    tail: T_STEM when the end lies on a perpendicular wall's face (or a q ends there), else FREE."""
    tails = {(id(r), e): _tail(r, e) for r in runs for e in (0, 1)}
    for r in runs:
        for e in (0, 1):
            if r.ends[e] in ("COLUMN", "X"):
                continue
            sgn = -1.0 if e == 0 else 1.0
            s_end = r.s0 if e == 0 else r.s1
            x = tails[(id(r), e)]
            corner, on_face = None, False
            for q in runs:
                if q is r or abs(abs(q.ang - r.ang) - math.pi / 2) > ANG_TOL:
                    continue
                (ux, uy), (nx, ny) = _axis(q.ang)
                p = _pt(r.ang, r.off, s_end)
                s_q, o_q = p[0] * ux + p[1] * uy, p[0] * nx + p[1] * ny
                # signed distance from r's end to q's midline, measured along r outward
                (rux, ruy), _ = _axis(r.ang)
                qm = _pt(q.ang, q.off, s_q)
                along = sgn * ((qm[0] - p[0]) * rux + (qm[1] - p[1]) * ruy)
                ends_q = [(eq, q.s0 if eq == 0 else q.s1) for eq in (0, 1)]
                q_at_r_face = [eq for eq, sq in ends_q if abs(abs(s_q - sq) - r.t / 2) <= 0.012]
                if abs(along - q.t / 2) <= 0.012 and q_at_r_face:
                    corner = (q, q_at_r_face[0])
                    break
                if abs(along - q.t / 2) <= 0.012 and q.s0 - JOIN_TOL <= s_q <= q.s1 + JOIN_TOL:
                    on_face = True
            if corner and x >= corner[0].t - 0.012:
                q, eq = corner
                if tails[(id(q), eq)] >= r.t - 0.012:
                    r.ends[e] = "L"
                    r.ext_m[e] = q.t / 2
                else:
                    r.ends[e] = "JUNCTION_OWN"
                    r.ext_m[e] = q.t
            elif corner or on_face:
                r.ends[e] = "T_STEM"


def totals(result):
    out = {}
    for r in result["runs"]:
        k = f"{r.t:.2f}"
        d = out.setdefault(k, {"runs": 0, "arch_run_m": 0.0, "solid_m": 0.0, "openings_m": 0.0, "one_face_m": 0.0})
        d["runs"] += 1
        d["arch_run_m"] += r.arch_run_m
        d["solid_m"] += r.solid_m
        d["openings_m"] += sum(r.openings)
        d["one_face_m"] += r.one_face_m
    return {k: {kk: (round(v, 4) if isinstance(v, float) else v) for kk, v in d.items()} for k, d in out.items()}


def check_units(wall_segments, max_len_m=200.0):
    """Unit guard: the census reads metres. A face segment longer than max_len_m (a villa wall in millimetres reads
    as kilometres) is refused, never rescaled silently."""
    for a, b in wall_segments:
        if math.hypot(b[0] - a[0], b[1] - a[1]) > max_len_m:
            raise ValueError(f"wall-face segment longer than {max_len_m} m: inputs must be in metres")


def agreement(ledger_rows, result, tol=0.05):
    """Wall-by-wall agreement of a ledger with the census, by position (any villa).

    ledger_rows: [{"id", "t", "a": (x, y), "b": (x, y), "length"}] with each row's axis segment in metres (the same frame
    as the census). Each census run is matched to the ledger rows on its midline (same direction, |offset| <= 0.012 m,
    axis overlap). Statuses, never resolved toward either side:
      AGREE (|d| <= tol), DIFFERS (with a cause when one is recognised: STEM_TO_CENTRELINE = the ledger runs a T stem
      to the through wall's midline, +t_through / 2 per such end), DUPLICATE (two ledger rows overlap on one census
      run by more than tol: the same masonry counted twice), MISSING_IN_CENSUS (a ledger row with no census run),
      MISSING_IN_LEDGER (a census run no ledger row covers), THICKNESS_DIFFERS."""
    runs = result["runs"]
    out, covered = [], set()
    rows_on_run = {}
    for row in ledger_rows:
        (x0, y0), (x1, y1) = row["a"], row["b"]
        ang = _norm_ang(math.atan2(y1 - y0, x1 - x0))
        (ux, uy), (nx, ny) = _axis(ang)
        s0, s1 = sorted((x0 * ux + y0 * uy, x1 * ux + y1 * uy))
        off = x0 * nx + y0 * ny
        hit = [r for r in runs if abs(r.ang - ang) < ANG_TOL and abs(r.off - off) <= 0.012
               and min(r.s1 + r.ext_m[1], s1) - max(r.s0 - r.ext_m[0], s0) > 0.01]
        rec = {"id": row["id"], "t_ledger": row["t"], "ledger_m": round(row["length"], 4),
               "census_runs": [r.key for r in hit], "census_m": None, "d_m": None, "status": None, "cause": ""}
        for r in hit:
            rows_on_run.setdefault(r.key, []).append((row["id"], s0, s1))
            covered.add(r.key)
        if not hit:
            rec["status"] = "MISSING_IN_CENSUS"
            out.append(rec)
            continue
        c = sum(r.arch_run_m for r in hit)
        rec["census_m"] = round(c, 4)
        rec["d_m"] = round(row["length"] - c, 4)
        if any(abs(r.t - row["t"]) > T_TOL for r in hit):
            rec["status"] = "THICKNESS_DIFFERS"
        elif abs(rec["d_m"]) <= tol:
            rec["status"] = "AGREE"
        else:
            rec["status"] = "DIFFERS"
            stems = [r for r in hit for e in (0, 1) if r.ends[e] == "T_STEM"]
            if stems and rec["d_m"] > 0:
                for r in runs:
                    if abs(abs(r.ang - ang) - math.pi / 2) < ANG_TOL and abs(rec["d_m"] - r.t / 2) <= tol / 2:
                        rec["cause"] = "STEM_TO_CENTRELINE"
                        break
        out.append(rec)
    by_id = {r["id"]: r for r in out}
    for key, lst in rows_on_run.items():
        lst.sort(key=lambda q: q[1])
        for (i1, a1, b1), (i2, a2, b2) in zip(lst, lst[1:]):
            if min(b1, b2) - max(a1, a2) > tol:
                for i in (i1, i2):
                    by_id[i]["status"] = "DUPLICATE"
                    by_id[i]["cause"] = f"overlaps {i2 if i == i1 else i1} on census run {key}"
    for r in runs:
        if r.key not in covered:
            out.append({"id": r.key, "t_ledger": None, "ledger_m": None, "census_runs": [r.key],
                        "census_m": round(r.arch_run_m, 4), "d_m": None, "status": "MISSING_IN_LEDGER", "cause": ""})
    return out
