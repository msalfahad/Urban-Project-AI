"""FACADE_GAP_CLOSURE_V1 (T-014, defects D-N10-01 and D-N10-02): where the facade outline meets a window, close it on
the face line of the wall only when the drawing shows glazing there. A check piece: NOT wired into any method version
(ARCH_TAKEOFF_V2.9 .. V2.12 and their FACADE output are unchanged); nothing here is read by a released line.

Rules: UP-FACADE-001 (the facade of a floor is the exterior face of its wall network; every opening is closed on its
outer wall face, so the run includes the openings), UP-WALL-GEOM-001 (a wall band is two drawn faces at its
thickness), UP-QTY-STATUS-001 (a quantity the drawing does not settle is HELD with its possible values, never a
number picked by a tolerance and never 0). Owner Q-25 answer: no gap-size limit is assumed; every closure is listed
with its width. Owner Q-07 (facade height slab to slab) is not touched here: this piece works on the run (m) only.

Two independent parts, stdlib only, every length in metres:

1. recess_closures(ring, ...) - D-N10-01. The engine's facade outline (a ring of edges with their drawing roles) can
   step into the open outer strip of a wall opening whose window frame sits in the inner part of the wall (the census
   did not detect the window, typically one set beside a column): the run then walks the two returns of that strip.
   A RECESS is a run of ring edges between two edges that lie on one straight line (the face line) in the same
   direction, every edge between them on the building side of that line and between the two jambs. It is closed at
   the face line (the chord replaces the walked path) only when all of these hold, each read from the drawing:
     - glazing (a WINDOW / GLAZING role edge of the ring, or a given glazing segment inside the recess) parallel to
       the face line covers the whole chord, jamb to jamb;
     - the recess is no deeper than the wall it is cut into (the thickness of the wall band whose face the two
       jamb edges are; a recess deeper than its wall is the building stepping back: the facade follows it, KEPT);
     - no opening threshold or door closure of the engine lies in it (an opening already measured is not re-closed).
   Glazing covering part of the chord, no glazing at all, or a wall thickness that cannot be read -> HELD: the run
   is given as the range [closed, walked], never one of them chosen. A closed recess is also reported as a window
   opening the census missed (beside_column when one jamb is a column side).
   A CORNER NOTCH is a recess whose face line continues on one side only (the far side turns along glazing, e.g. the
   frame end of a glazed bay beside a column). With no glass across its mouth its sides are real exterior faces and
   the facade follows them (KEPT, UP-FACADE-001); glass across its mouth -> HELD with the range.

2. glazed_gap_closures(face_segments, window_pieces, ...) - D-N10-02, for an independent reading. Along every face
   line (collinear wall / column pieces) each gap between two pieces, of ANY width, is examined: jamb lines (wall or
   column pieces across the wall at the gap ends) give the wall thickness; window pieces inside the gap give the
   evidence. Glazing that covers the gap inside the wall band -> CLOSED_GLAZED (the chord on the face line and on the
   other face of the band); glazing that leaves the band (a bay curved or set back into the building) is HELD here and
   anything else -> HELD with the reason. No closure is made on width alone.
   glass_chain_closures(face_segments, window_pieces): a chain of window pieces whose two ends lie on wall or column
   lines is a glass wall and bounds the plan as a wall does (a curved or set-back glazed bay)."""

from __future__ import annotations

import math

POLICY = "FACADE_GAP_CLOSURE_V1"
EPS_M = 0.001                       # drawing noise: two points this close are one point (1 mm, not a gap limit)
ANG_EPS = 1e-4                      # parallel / collinear test on unit vectors (sin of the angle)
GLAZING_ROLES = ("WINDOW", "GLAZING")
JAMB_ROLES = ("WALL", "WALL_CAP", "COLUMN")
OPENING_ROLE_SUFFIXES = ("_THRESHOLD", "DOOR_CLOSURE")
RULES = ("UP-FACADE-001", "UP-WALL-GEOM-001", "UP-QTY-STATUS-001", "owner Q-25 (no assumed gap limit)")


# ============================================================================================ small geometry
def _len(a, b):
    return math.hypot(b[0] - a[0], b[1] - a[1])


def _unit(a, b):
    L = _len(a, b)
    return ((b[0] - a[0]) / L, (b[1] - a[1]) / L) if L > 0 else (0.0, 0.0)


def _cross(u, v):
    return u[0] * v[1] - u[1] * v[0]


def _dot(u, v):
    return u[0] * v[0] + u[1] * v[1]


def _off(p, o, u):
    """signed offset of p from the line through o along u (left of u is positive)."""
    return _cross(u, (p[0] - o[0], p[1] - o[1]))


def _proj(p, o, u):
    return _dot(u, (p[0] - o[0], p[1] - o[1]))


def _union_len(intervals, lo, hi):
    """length of [lo, hi] covered by the union of the intervals."""
    iv = sorted((max(lo, a), min(hi, b)) for a, b in intervals if min(hi, b) > max(lo, a))
    tot, cur = 0.0, None
    for a, b in iv:
        if cur is None or a > cur[1]:
            if cur:
                tot += cur[1] - cur[0]
            cur = [a, b]
        else:
            cur[1] = max(cur[1], b)
    if cur:
        tot += cur[1] - cur[0]
    return tot


def _signed_area(pts):
    return 0.5 * sum(pts[i][0] * pts[(i + 1) % len(pts)][1] - pts[(i + 1) % len(pts)][0] * pts[i][1]
                     for i in range(len(pts)))


def _norm_edge(e):
    a, b = tuple(map(float, e["a"])), tuple(map(float, e["b"]))
    return {"a": a, "b": b, "len": float(e.get("len_m", _len(a, b))), "role": str(e.get("role") or "NONE"),
            "roles": tuple(e.get("roles") or (e.get("role") or "NONE",)), "straight": bool(e.get("straight", True)),
            "sources": tuple(e.get("sources") or ()), "wall_t_m": e.get("wall_t_m")}


def _has_role(e, names):
    return any(r in names for r in e["roles"])


def _is_opening(e):
    return any(r.endswith(OPENING_ROLE_SUFFIXES) for r in e["roles"])


# ============================================================================================ 1. recesses on a ring
def recess_closures(ring, *, glazing=(), eps_m=EPS_M):
    """ring: the facade outline as consecutive edges, closed (the last edge ends where the first starts), each
    {"a": [x, y], "b": [x, y], "roles": [...] (or "role"), "straight": bool, "len_m": length (an arc's true
    length; its a-b chord otherwise), "wall_t_m": thickness of the wall band this edge is a face of (None when not
    known), "sources": [...]}. Arcs may be given as one edge (straight False) or as short steps; a curved edge is
    never a face line. glazing: extra glazing segments [[x, y], [x, y]] that are not on the ring (window insert
    lines). -> {"policy", "state": RESOLVED | HELD_RANGE | NO_RECESS | NO_OUTLINE, "walked_m", "closed_m" (every
    CLOSED recess applied), "range_m" [low, high] (HELD recesses closed / walked), "recesses": [...],
    "undetected_openings": [...]}. Missing never becomes 0: an empty ring is NO_OUTLINE with no value."""
    E = [_norm_edge(e) for e in ring or ()]
    out = {"policy": POLICY, "rules": list(RULES)}
    if len(E) < 3:
        return dict(out, state="NO_OUTLINE", walked_m=None, closed_m=None, range_m=None, recesses=[],
                    undetected_openings=[], why="no closed outline was given")
    walked = sum(e["len"] for e in E)
    pts = [e["a"] for e in E]
    # the building side of an edge: left of a counter-clockwise ring, right of a clockwise one
    side = 1.0 if _signed_area(pts) > 0 else -1.0
    n = len(E)
    # walked forward and backward: a corner notch has its face line on one side only, which a walk meets either
    # before or after the notch; a recess found both ways is kept once
    rev = [dict(e, a=e["b"], b=e["a"]) for e in reversed(E)]
    found, seen = [], set()
    for edges, sd, back in ((E, side, lambda m: m), (rev, -side, lambda m: n - 1 - m)):
        for r in _scan(edges, sd, glazing, eps_m):
            r["edges"] = sorted(back(m) for m in r["edges"])
            key = frozenset(r["edges"])
            if key in seen or any(key & frozenset(x["edges"]) for x in found):
                continue
            seen.add(key)
            found.append(r)
    recs = [r for r in found if r]
    closed = walked - sum(r["saved_m"] for r in recs if r["state"] == "CLOSED")
    held = [r for r in recs if r["state"] == "HELD"]
    low = closed - sum(r["saved_m"] for r in held)
    state = ("NO_RECESS" if not recs else "HELD_RANGE" if held else "RESOLVED")
    und = [{"kind": "WINDOW", "width_m": r["chord_m"], "beside_column": r["beside_column"], "at": r["chord"],
            "evidence": r["evidence"], "note": "a window in the face wall that no opening threshold covers"}
           for r in recs if r["state"] == "CLOSED"]
    return dict(out, state=state, walked_m=round(walked, 6), closed_m=round(closed, 6),
                range_m=[round(low, 6), round(closed, 6)] if held else None,
                recesses=[{k: v for k, v in r.items() if k != "edges"} | {"edge_index": r["edges"]} for r in recs],
                undetected_openings=und)


def _scan(E, side, glazing, eps_m):
    n = len(E)
    found, used = [], set()
    for i in range(n):
        s = E[i]
        if not s["straight"] or s["len"] <= eps_m or i in used:
            continue
        u = _unit(s["a"], s["b"])
        o = s["a"]
        p0 = _proj(s["b"], o, u)
        chain = []
        for k in range(1, n - 1):
            j = (i + k) % n
            e = E[j]
            # the face line resumes: a straight edge on the line, same direction, ahead of s
            if abs(_off(e["a"], o, u)) <= eps_m and abs(_off(e["b"], o, u)) <= eps_m:
                if chain and e["straight"] and e["len"] > eps_m and _dot(_unit(e["a"], e["b"]), u) > 0:
                    found.append(_recess(E, i, j, chain, o, u, side, p0, glazing, eps_m, kind="RECESS"))
                    used.update(chain)
                break                       # the line goes on (no recess yet) or turns back on itself
            # every edge of a recess stays on the building side of the face line and ahead of s's end
            if any(side * _off(p, o, u) < -eps_m for p in (e["a"], e["b"])) or \
                    any(_proj(p, o, u) < p0 - eps_m for p in (e["a"], e["b"])):
                notch = _corner_notch(E, i, chain, o, u, side, p0, glazing, eps_m)
                if notch:
                    found.append(notch)
                    used.update(notch["edges"])
                break
            chain.append(j)
    return [r for r in found if r]


def _pocket_record(E, chain, chord_a, chord_b, o, u, side, glazing, eps_m):
    path = sum(E[j]["len"] for j in chain)
    chord = _len(chord_a, chord_b)
    lo, hi = sorted((_proj(chord_a, o, u), _proj(chord_b, o, u)))
    depth = max(side * _off(p, o, u) for j in chain for p in (E[j]["a"], E[j]["b"]))
    cover = []
    gl_ids = []
    for j in chain:
        e = E[j]
        if _has_role(e, GLAZING_ROLES) and e["straight"] and abs(_cross(_unit(e["a"], e["b"]), u)) <= ANG_EPS:
            cover.append(tuple(sorted((_proj(e["a"], o, u), _proj(e["b"], o, u)))))
            gl_ids.append(j)
    for g in glazing or ():
        a, b = tuple(map(float, g[0])), tuple(map(float, g[1]))
        if _len(a, b) <= eps_m or abs(_cross(_unit(a, b), u)) > ANG_EPS:
            continue
        da, db = side * _off(a, o, u), side * _off(b, o, u)
        if -eps_m <= da <= depth + eps_m and -eps_m <= db <= depth + eps_m:
            cover.append(tuple(sorted((_proj(a, o, u), _proj(b, o, u)))))
    covered = _union_len(cover, lo, hi)
    return path, chord, depth, covered, gl_ids


def _recess(E, i, j, chain, o, u, side, p0, glazing, eps_m, kind):
    a, b = E[i]["b"], E[j]["a"]
    path, chord, depth, covered, gl_ids = _pocket_record(E, chain, a, b, o, u, side, glazing, eps_m)
    ts = sorted({float(E[x]["wall_t_m"]) for x in (i, j) if E[x].get("wall_t_m")})
    t = ts[0] if ts else None
    beside_col = any(_has_role(E[x], ("COLUMN",)) and not _has_role(E[x], GLAZING_ROLES) for x in chain)
    rec = {"kind": kind, "edges": list(chain), "path_m": round(path, 6), "chord_m": round(chord, 6),
           "depth_m": round(depth, 6), "saved_m": round(path - chord, 6), "wall_t_m": t,
           "glazing_cover": round(covered / chord, 6) if chord > 0 else 0.0, "beside_column": beside_col,
           "chord": [[round(a[0], 6), round(a[1], 6)], [round(b[0], 6), round(b[1], 6)]],
           "evidence": {"glazing_edges": gl_ids, "roles": sorted({r for x in chain for r in E[x]["roles"]}),
                        "jamb_wall_t_m": ts}}
    if any(_is_opening(E[x]) for x in chain):
        return dict(rec, state="KEPT", why="RECESS_HOLDS_A_MEASURED_OPENING: an opening threshold or door closure "
                                           "lies in it; the facade follows it as drawn")
    if t is not None and depth > t + eps_m:
        return dict(rec, state="KEPT", why="DEEPER_THAN_ITS_WALL: the building steps back here; the facade follows "
                                           "the step (UP-FACADE-001)")
    if t is None:
        return dict(rec, state="HELD", why="WALL_THICKNESS_NOT_READ: the wall band of the face line is not known, so "
                                           "an opening strip cannot be told from a step of the building")
    if chord > 0 and covered >= chord - eps_m:
        return dict(rec, state="CLOSED", why="GLAZED_WALL_OPENING: glazing covers the gap jamb to jamb inside the wall "
                                             "(D-N10-01); closed on the face line (UP-FACADE-001)")
    if covered > eps_m:
        return dict(rec, state="HELD", why="PARTLY_GLAZED: glazing covers %.3f of %.3f m" % (covered, chord))
    return dict(rec, state="HELD", why="NO_GLAZING_EVIDENCE: nothing drawn says this strip is an opening; never "
                                       "closed by its size alone")


def _corner_notch(E, i, chain, o, u, side, p0, glazing, eps_m):
    """a notch whose face line does not resume as a ring edge: the walk returns to the face line at a vertex where a
    glazing edge turns away (the frame end of a glazed bay beside a column). Held with its range."""
    for m in range(len(chain) - 1, 0, -1):
        j = chain[m]
        e = E[j]
        if abs(_off(e["b"], o, u)) <= eps_m and _proj(e["b"], o, u) > p0 + eps_m:
            sub = chain[:m + 1]
            nxt = E[(j + 1) % len(E)]
            if not (_has_role(e, GLAZING_ROLES) or _has_role(nxt, GLAZING_ROLES)):
                return None
            # a glazing frame line on the face line beyond the notch (given glazing) continues the face line
            cont = any(abs(_off(tuple(g[0]), o, u)) <= eps_m and abs(_off(tuple(g[1]), o, u)) <= eps_m and
                       min(_proj(tuple(g[0]), o, u), _proj(tuple(g[1]), o, u)) >= _proj(e["b"], o, u) - eps_m
                       for g in glazing or ())
            a, b = E[i]["b"], e["b"]
            path, chord, depth, covered, gl = _pocket_record(E, sub, a, b, o, u, side, glazing, eps_m)
            if path - chord <= eps_m:
                return None
            rec = {"kind": "CORNER_NOTCH", "edges": list(sub), "path_m": round(path, 6), "chord_m": round(chord, 6),
                   "depth_m": round(depth, 6), "saved_m": round(path - chord, 6), "wall_t_m": None,
                   "glazing_cover": round(covered / chord, 6) if chord > 0 else 0.0,
                   "beside_column": any(_has_role(E[x], ("COLUMN",)) for x in sub + [i]),
                   "chord": [[round(a[0], 6), round(a[1], 6)], [round(b[0], 6), round(b[1], 6)]],
                   "evidence": {"glazing_edges": gl, "frame_line_continues_face": cont,
                                "roles": sorted({r for x in sub for r in E[x]["roles"]})}}
            if covered > eps_m:
                return dict(rec, state="HELD",
                            why="CORNER_NOTCH_GLAZED_ACROSS: glass lies across the notch mouth but the face line "
                                "does not resume beyond it; no drawing or Urban rule says where the facade runs")
            return dict(rec, state="KEPT",
                        why="CORNER_NOTCH_OPEN: no glass across its mouth; its sides are exterior faces of a column, "
                            "a wall and the frame end, so the facade follows them (UP-FACADE-001)")
    return None


# ============================================================================================ 2. glazed gaps
def _lines(segments, eps_m):
    """straight pieces grouped by the infinite line they lie on: [(origin, unit, [(t0, t1, idx)])]."""
    groups = []
    for idx, (a, b) in enumerate(segments):
        if _len(a, b) <= eps_m:
            continue
        u = _unit(a, b)
        if u[0] < -ANG_EPS or (abs(u[0]) <= ANG_EPS and u[1] < 0):
            u = (-u[0], -u[1])
        for g in groups:
            o, gu, items = g
            if abs(_cross(u, gu)) <= ANG_EPS and abs(_off(a, o, gu)) <= eps_m and abs(_off(b, o, gu)) <= eps_m:
                items.append(tuple(sorted((_proj(a, o, gu), _proj(b, o, gu)))) + (idx,))
                break
        else:
            groups.append((a, u, [tuple(sorted((0.0, _proj(b, a, u)))) + (idx,)]))
    return groups


def _jamb(segments, p, u, eps_m):
    """the jamb at a gap end p: wall / column pieces across the face line (perpendicular) with one end at p ->
    [(signed offset of the far end, piece index)]."""
    out = []
    for idx, (a, b) in enumerate(segments):
        if _len(a, b) <= eps_m or abs(_dot(_unit(a, b), u)) > ANG_EPS:
            continue
        for x, y in ((a, b), (b, a)):
            if _len(x, p) <= eps_m:
                out.append((_off(y, p, u), idx))
    return out


def _chains(pieces, eps_m):
    """window pieces joined end to end -> chains [(start, end, length, [piece idx])]."""
    n = len(pieces)
    parent = list(range(n))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    ends = [(p[0], p[-1]) for p in pieces]
    for i in range(n):
        for j in range(i + 1, n):
            if any(_len(x, y) <= eps_m for x in ends[i] for y in ends[j]):
                parent[find(j)] = find(i)
    groups = {}
    for i in range(n):
        groups.setdefault(find(i), []).append(i)
    out = []
    for idx in groups.values():
        deg = {}
        for i in idx:
            for e in ends[i]:
                key = (round(e[0] / eps_m), round(e[1] / eps_m))
                deg[key] = deg.get(key, []) + [e]
        free = [v[0] for v in deg.values() if len(v) == 1]
        length = sum(sum(_len(a, b) for a, b in zip(pieces[i], pieces[i][1:])) for i in idx)
        if len(free) == 2:
            out.append((free[0], free[1], length, sorted(idx)))
    return out


def glazed_gap_closures(face_segments, window_pieces, *, min_gap_m=None, eps_m=EPS_M):
    """face_segments: straight wall and column lines [[x, y], [x, y]] (metres); window_pieces: window-role pieces as
    point lists (curves flattened). Every gap between two collinear face pieces whose two ends both carry a jamb
    (a wall / column piece across the wall, giving its thickness t) is examined; min_gap_m only filters the report
    (a caller that already closes narrower gaps), it never decides a closure.
    -> [{"line": [o, u], "gap": [lo, hi], "width_m", "wall_t_m", "state", "why", "closure": [[a, b], ...] (lines to
       add to the face graph), "glazing_cover", "path_m" (the closure length on the face line or the bay chain)}]."""
    segs = [(tuple(map(float, a)), tuple(map(float, b))) for a, b in face_segments]
    wins = [[tuple(map(float, q)) for q in p] for p in window_pieces if len(p) >= 2]
    res = []
    for o, u, items in _lines(segs, eps_m):
        items.sort()
        hi_t, hi_i = items[0][1], items[0][2]
        for t0, t1, idx in items[1:]:
            if t0 - hi_t > eps_m:
                lo, hi = hi_t, t0
                if min_gap_m is None or hi - lo > min_gap_m:
                    res.append(_gap(segs, wins, o, u, lo, hi, eps_m))
            if t1 > hi_t:
                hi_t, hi_i = t1, idx
    return [r for r in res if r]


def _pt(o, u, t, d=0.0):
    return (o[0] + u[0] * t - u[1] * d, o[1] + u[1] * t + u[0] * d)


def _gap(segs, wins, o, u, lo, hi, eps_m):
    pa, pb = _pt(o, u, lo), _pt(o, u, hi)
    rec = {"line": [[round(o[0], 6), round(o[1], 6)], [round(u[0], 9), round(u[1], 9)]],
           "gap": [[round(pa[0], 6), round(pa[1], 6)], [round(pb[0], 6), round(pb[1], 6)]],
           "width_m": round(hi - lo, 6), "closure": [], "policy": POLICY}
    ja, jb = _jamb(segs, pa, u, eps_m), _jamb(segs, pb, u, eps_m)
    sides = {1 if d > 0 else -1 for d, _ in ja} & {1 if d > 0 else -1 for d, _ in jb}
    if not ja or not jb or len(sides) != 1:
        return dict(rec, state="HELD", wall_t_m=None, glazing_cover=None,
                    why="NO_JAMB_PAIR: no wall or column line crosses the wall at both gap ends on one side, so the "
                        "gap is not shown as an opening in one wall")
    sd = sides.pop()
    ta = min(abs(d) for d, _ in ja if d * sd > 0)
    tb = min(abs(d) for d, _ in jb if d * sd > 0)
    t = min(ta, tb)
    rec["wall_t_m"] = round(t, 6)
    inside, beyond = [], []
    for k, p in enumerate(wins):
        ds = [sd * _off(q, o, u) for q in p]
        ts = [_proj(q, o, u) for q in p]
        if min(ds) < -eps_m or min(ts) < lo - eps_m or max(ts) > hi + eps_m:
            continue
        (inside if max(ds) <= t + eps_m else beyond).append(k)
    cover = _union_len([(min(_proj(q, o, u) for q in wins[k]), max(_proj(q, o, u) for q in wins[k]))
                        for k in inside + beyond], lo, hi)
    rec["glazing_cover"] = round(cover / (hi - lo), 6) if hi > lo else 0.0
    if cover < (hi - lo) - eps_m:
        why = ("PARTLY_GLAZED: glazing covers %.3f of %.3f m" % (cover, hi - lo)) if cover > eps_m else \
            "NO_GLAZING_EVIDENCE: no window piece in the gap; never closed on its width alone"
        return dict(rec, state="HELD", why=why)
    qa, qb = _pt(o, u, lo, sd * t), _pt(o, u, hi, sd * t)
    if beyond:
        return dict(rec, state="HELD", why="GLAZING_LEAVES_THE_WALL_BAND: a bay set back or curved into the building; "
                                           "the glass itself is the facade there (glass_chain_closures)")
    return dict(rec, state="CLOSED_GLAZED", path_m=round(hi - lo, 6),
                closure=[[list(pa), list(pb)], [list(qa), list(qb)]],
                why="glazing covers the gap inside the wall band: closed on both faces (UP-FACADE-001)")


def _on_segment(p, a, b, eps_m):
    L = _len(a, b)
    if L <= eps_m:
        return _len(p, a) <= eps_m
    u = _unit(a, b)
    t = _proj(p, a, u)
    return -eps_m <= t <= L + eps_m and abs(_off(p, a, u)) <= eps_m


def glass_chain_closures(face_segments, window_pieces, *, eps_m=EPS_M):
    """a glass wall: a chain of window pieces joined end to end whose two free ends each lie on a wall or column line
    (within eps_m) is a boundary of the plan, as a wall is (UP-FACADE-001: the facade follows the glass of a bay that
    stands outside or inside the wall line). A chain with a free end on no wall is left out and listed (never
    extended to a wall). -> {"closed": [{"length_m", "pieces", "ends", "lines"}], "open": [{"length_m", "ends"}]}"""
    segs = [(tuple(map(float, a)), tuple(map(float, b))) for a, b in face_segments]
    wins = [[tuple(map(float, q)) for q in p] for p in window_pieces if len(p) >= 2]
    closed, open_ = [], []
    for s, e, L, idx in _chains(wins, eps_m):
        hit = [any(_on_segment(p, a, b, eps_m) for a, b in segs) for p in (s, e)]
        rec = {"length_m": round(L, 6), "pieces": idx,
               "ends": [[round(s[0], 6), round(s[1], 6)], [round(e[0], 6), round(e[1], 6)]]}
        if all(hit) and _len(s, e) > eps_m:
            closed.append(dict(rec, lines=[[list(q0), list(q1)] for i in idx for q0, q1 in zip(wins[i], wins[i][1:])]))
        else:
            open_.append(dict(rec, ends_on_wall=hit))
    return {"policy": POLICY, "closed": closed, "open": open_}


# ============================================================================================ engine adapter
def ring_from_arrangement(arr, k, unit_m, wall_t_by_source=None):
    """the outer cycle k of an engine.source.topology arrangement as recess_closures() edges (metres). Roles as
    arch_v29._outline reads them: an opening's outer threshold THR|<id> -> '<KIND>_THRESHOLD' (its roles), a door
    closure -> DOOR_CLOSURE. wall_t_by_source: {source id: wall band thickness m} (from the ARCH_WALLS bands)."""
    wt = wall_t_by_source or {}
    out = []
    for ei, fw in arr.faces[k]["cycle"]:
        e = arr.edges[ei]
        a = arr.nodes[e["n0"] if fw else e["n1"]]
        b = arr.nodes[e["n1"] if fw else e["n0"]]
        if e["kind"] == "S":
            L = _len(a, b) * unit_m
        else:
            L = e["prim"].r * (e["t1"] - e["t0"]) * unit_m
        src = sorted(str(s) for s in e["sources"])
        roles = sorted(e["roles"]) or ["NONE"]
        if any(s.startswith("CLOSURE|") for s in src):
            roles = ["DOOR_CLOSURE"]
        ts = sorted({wt[s] for s in src if s in wt})
        out.append({"a": [a[0] * unit_m, a[1] * unit_m], "b": [b[0] * unit_m, b[1] * unit_m], "roles": roles,
                    "straight": e["kind"] == "S", "len_m": L, "sources": src, "wall_t_m": ts[0] if ts else None})
    return out
