"""CONSTRUCTABILITY REFERENCE - Phase 2B-4: an independent construction calculator for the audit of the V2.5
waterproofing cutting plans. It rebuilds a cutting plan piece by piece - cut from a roll, ripped into lanes,
cross-cut into pieces, laid at a place - and checks that the installation it describes is physically complete:
every floor, wall-upturn and doorway surface is covered (a 10 mm coverage grid), every joint laps, every piece fits
the material it is cut from, and the material balances (consumed = installed + offcuts). It then sorts the material
into installed, reusable offcut, true waste and untouched roll stock, and lists every side lap, end lap,
floor-to-wall junction, corner, doorway transition and penetration condition separately.

Stdlib only, integer millimetres. It imports neither the engine nor the Phase 2B-3 reference calculator and copies no
value from either. The hand calculations of construct_cases.py are checked against it; the engine is compared with it
only in construct_engine.py.

The floor-to-wall junction is a parameter of the calculation, never assumed to be the project's detail:

    A  SEPARATE_UPSTAND   the floor strips stop at the wall; a band strip (h + j) wide is folded along the junction:
                          h up the wall and a flange j lapped onto the floor membrane (V2.5 models this with j = the
                          0.10 m lap of UP-WP-002)
    B  CONTINUOUS_FOLD    the floor strips are folded up the walls and laid flat into the doorways: no band, no junction
                          lap; the strips cover the developed surface (floor + upturns + doorway floors); each
                          internal corner leaves an h x h square of excess sheet (folded, or cut out and patched)

Plans (dicts written in construct_cases.py, or built by plan_A / plan_B):

    method    "A" | "B";  along "X" | "Y" (the strip direction);  j  the junction flange (A)
    rolls     [[(cut_id, length), ...], ...]           cuts in roll order, each the full roll width W
    rip       {node: [(part_id, width), ...]}          lengthwise into parts (the rest of the width -> "<node>~w")
    cross     {node: [(piece_id, length), ...]}        crosswise into pieces (the rest of the length -> "<node>~l")
    floor     [piece_id | [piece_id, ...], ...]        one entry per floor strip in cross order (a list = the strip
                                                       spliced from pieces joined by end laps)
    runs      [[piece_id, ...], ...]                   band pieces in laying order, one list per upturn run (A)
    doorways  {door_id: piece_id}                      the doorway continuation piece of each door (A)
    reversed  [run index, ...]                         runs laid from their far jamb (A, optional)

A floor piece of method A that reaches beyond a stepped wall leaves its outside part as an offcut "<piece>.o<k>",
which a plan may rip and cross-cut like any other node.
"""

from __future__ import annotations

import itertools
from collections import Counter

CELL = 10                       # coverage grid cell (mm); every coordinate is a multiple of it
MIN_PIECE_W = 300               # narrowest piece any audited plan cuts (a 0.30 m band lane, a doorway piece)
URBAN = {"W": 1000, "L": 10000, "s": 100, "e": 100, "h": 200, "j": 100, "dl": 100}
INTERNAL, EXTERNAL = "INTERNAL", "EXTERNAL"


# --------------------------------------------------------------- orthogonal polygon geometry (mm, counter-clockwise)
def _edges(poly):
    n = len(poly)
    return [(tuple(poly[i]), tuple(poly[(i + 1) % n])) for i in range(n)]


def _dir(a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    assert (dx == 0) != (dy == 0), "orthogonal polygons only"
    ln = abs(dx) + abs(dy)
    return (dx // ln, dy // ln), ln


def area2(poly):
    return sum(a[0] * b[1] - b[0] * a[1] for a, b in _edges(poly))


def check_poly(poly):
    assert area2(poly) > 0, "a counter-clockwise ring is required"
    for p in poly:
        assert p[0] % CELL == 0 and p[1] % CELL == 0, "coordinates on the 10 mm grid"
    for a, b in _edges(poly):
        _dir(a, b)


def corner_kind(poly, v):
    """INTERNAL: the walls meet at 90 degrees on the room side (a left turn of the ring); EXTERNAL: 270 degrees."""
    (dx0, dy0), _ = _dir(poly[v - 1], poly[v])
    (dx1, dy1), _ = _dir(poly[v], poly[(v + 1) % len(poly)])
    return INTERNAL if dx0 * dy1 - dy0 * dx1 > 0 else EXTERNAL


def perimeter(poly):
    return sum(_dir(a, b)[1] for a, b in _edges(poly))


def runs(room):
    """The wall-upturn runs in ring order. With doorways: open runs from jamb to jamb, the first starting after the
    first doorway in ring order (by edge, then position). Each run: length, the wall parts it follows
    (edge, t_from, t_to, r_from) and its corners (run position, kind, vertex)."""
    poly = room["poly"]
    n = len(poly)
    lens = [_dir(a, b)[1] for a, b in _edges(poly)]
    doors = sorted(room.get("doors", ()), key=lambda d: (d["edge"], d["t0"]))
    if not doors:
        parts, corners, r = [], [], 0
        for i in range(n):
            parts.append((i, 0, lens[i], r))
            r += lens[i]
            corners.append((r if (i + 1) % n else 0, corner_kind(poly, (i + 1) % n), (i + 1) % n))
        return [{"length": r, "closed": True, "parts": parts, "corners": sorted(corners), "from": None, "to": None}]
    out = []
    for q, d in enumerate(doors):
        nxt = doors[(q + 1) % len(doors)]
        e, t, r = d["edge"], d["t1"], 0
        parts, corners = [], []
        while True:
            if nxt["edge"] == e and nxt["t0"] >= t:
                if nxt["t0"] > t:
                    parts.append((e, t, nxt["t0"], r))
                r += nxt["t0"] - t
                break
            if lens[e] > t:
                parts.append((e, t, lens[e], r))
            r += lens[e] - t
            v = (e + 1) % n
            corners.append((r, corner_kind(poly, v), v))
            e, t = v, 0
        out.append({"length": r, "closed": False, "parts": parts, "corners": corners, "from": d["id"],
                    "to": nxt["id"]})
    return out


def run_point(poly, run, r):
    """The point of the wall line at run position r."""
    E = _edges(poly)
    for e, ta, tb, r0 in run["parts"]:
        if r0 <= r <= r0 + tb - ta:
            a, b = E[e]
            (dx, dy), _ = _dir(a, b)
            t = ta + r - r0
            return (a[0] + dx * t, a[1] + dy * t)
    raise ValueError("position outside the run")


def flange_zones(room, j):
    """Method A: the band flange on the floor along every wall part, j into the room: (x0, y0, x1, y1)."""
    poly = room["poly"]
    E = _edges(poly)
    out = []
    for rn in runs(room):
        for e, ta, tb, r0 in rn["parts"]:
            a, b = E[e]
            (dx, dy), _ = _dir(a, b)
            nx, ny = -dy, dx                                    # into the room: left of a counter-clockwise edge
            p0 = (a[0] + dx * ta, a[1] + dy * ta)
            p1 = (a[0] + dx * tb, a[1] + dy * tb)
            xs = sorted((p0[0], p1[0], p0[0] + nx * j, p1[0] + nx * j))
            ys = sorted((p0[1], p1[1], p0[1] + ny * j, p1[1] + ny * j))
            out.append((xs[0], ys[0], xs[-1], ys[-1]))
    return out


def door_segment(room, d):
    """(axis, fixed coordinate, from, to): a doorway as a stretch of a horizontal ('y' fixed) or vertical edge."""
    a, b = _edges(room["poly"])[d["edge"]]
    (dx, dy), _ = _dir(a, b)
    p0 = (a[0] + dx * d["t0"], a[1] + dy * d["t0"])
    p1 = (a[0] + dx * d["t1"], a[1] + dy * d["t1"])
    if dy == 0:
        return ("y", a[1]) + tuple(sorted((p0[0], p1[0])))
    return ("x", a[0]) + tuple(sorted((p0[1], p1[1])))


def _axes(along):
    """(cross axis, along axis) indices for strips laid along X or Y."""
    return (0, 1) if along == "Y" else (1, 0)


def _intervals_at(poly, along, c):
    """The polygon's intervals along the strip direction on the line cross = c (c never a vertex coordinate)."""
    ci, ai = _axes(along)
    hits = sorted(a[ai] for a, b in _edges(poly)
                  if a[ai] == b[ai] and min(a[ci], b[ci]) < c < max(a[ci], b[ci]))
    return [(hits[k], hits[k + 1]) for k in range(0, len(hits), 2)]


def _slabs(poly, along, c0, c1):
    ci, _ = _axes(along)
    cuts = sorted({c0, c1} | {p[ci] for p in poly if c0 < p[ci] < c1})
    return list(zip(cuts, cuts[1:]))


def _merge(rects):
    """Join (c0, c1, a0, a1) rectangles of consecutive slabs that have the same along interval."""
    out = []
    for r in sorted(rects, key=lambda x: (x[2], x[3], x[0])):
        if out and out[-1][2:] == r[2:] and out[-1][1] == r[0]:
            out[-1] = (out[-1][0], r[1], r[2], r[3])
        else:
            out.append(r)
    return sorted(out)


def floor_layout(poly, along, prm):
    """Floor strips across the cross width: the smallest n with W + (n - 1)(W - s) >= width; strip i starts at
    cmin + i (W - s) and the last is cut down lengthwise. Each strip is one piece as long as the room under it."""
    ci, ai = _axes(along)
    W, s = prm["W"], prm["s"]
    cs = [p[ci] for p in poly]
    cmin, cmax = min(cs), max(cs)
    n = 1
    while cmin + (n - 1) * (W - s) + W < cmax:
        n += 1
    strips = []
    for i in range(n):
        c0 = cmin + i * (W - s)
        c1 = min(c0 + W, cmax)
        rects = []
        for u, v in _slabs(poly, along, c0, c1):
            rects += [(u, v, a0, a1) for a0, a1 in _intervals_at(poly, along, (u + v) / 2)]
        a0, a1 = min(r[2] for r in rects), max(r[3] for r in rects)
        outside = []
        for u, v in _slabs(poly, along, c0, c1):
            p = a0
            for x0, x1 in sorted((r[2], r[3]) for r in rects if r[0] == u):
                if x0 > p:
                    outside.append((u, v, p, x0))
                p = x1
            if p < a1:
                outside.append((u, v, p, a1))
        strips.append({"i": i, "c0": c0, "c1": c1, "w": c1 - c0, "a0": a0, "a1": a1, "len": a1 - a0,
                       "rects": rects, "laid": sum((r[1] - r[0]) * (r[3] - r[2]) for r in rects),
                       "outside": _merge(outside)})
    return {"along": along, "n": n, "strips": strips, "cmin": cmin, "cmax": cmax}


def developed(room, prm):
    """Method B: the developed surface of a rectangular room: the floor, the upturn of every wall folded out flat
    and the floor of every doorway (its depth must equal the upturn height). Returns the developed rectangle, the
    four h x h corner squares (no surface: excess sheet) and the required area."""
    poly = room["poly"]
    assert len(poly) == 4, "method B is calculated for rectangular rooms only"
    h = prm["h"]
    for d in room.get("doors", ()):
        assert d["depth"] == h, "method B needs doorway depth = upturn height"
    xs, ys = [p[0] for p in poly], [p[1] for p in poly]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    rect = [(x0 - h, y0 - h), (x1 + h, y0 - h), (x1 + h, y1 + h), (x0 - h, y1 + h)]
    corners = [(x0 - h, y0 - h, x0, y0), (x1, y0 - h, x1 + h, y0), (x1, y1, x1 + h, y1 + h), (x0 - h, y1, x0, y1 + h)]
    req = (x1 - x0) * (y1 - y0) + perimeter(poly) * h
    return {"rect": rect, "floor": (x0, y0, x1, y1), "corners": corners, "required": req}


# --------------------------------------------------------------------------------------------- coverage grid
class Grid:
    def __init__(self, x0, y0, x1, y1):
        self.x0, self.y0 = x0, y0
        self.nx, self.ny = (x1 - x0) // CELL, (y1 - y0) // CELL
        self.n = [bytearray(self.nx) for _ in range(self.ny)]

    def _span(self, lo, hi, o, m):
        return max(0, (lo - o) // CELL), min(m, (hi - o) // CELL)

    def add(self, x0, y0, x1, y1):
        i0, i1 = self._span(x0, x1, self.x0, self.nx)
        j0, j1 = self._span(y0, y1, self.y0, self.ny)
        for j in range(j0, j1):
            row = self.n[j]
            for i in range(i0, i1):
                row[i] += 1

    def cells(self, x0, y0, x1, y1):
        i0, i1 = self._span(x0, x1, self.x0, self.nx)
        j0, j1 = self._span(y0, y1, self.y0, self.ny)
        return [(i, j) for j in range(j0, j1) for i in range(i0, i1)]


def _inside(poly, x, y):
    c = False
    for a, b in _edges(poly):
        if (a[1] > y) != (b[1] > y) and x < a[0] + (y - a[1]) * (b[0] - a[0]) / (b[1] - a[1]):
            c = not c
    return c


def _poly_cells(poly, g):
    out = []
    for j in range(g.ny):
        y = g.y0 + j * CELL + CELL / 2
        for i in range(g.nx):
            if _inside(poly, g.x0 + i * CELL + CELL / 2, y):
                out.append((i, j))
    return out


def _rect_xy(along, c0, c1, a0, a1):
    """(x0, y0, x1, y1) of a strip rectangle given in cross / along coordinates."""
    return (c0, a0, c1, a1) if along == "Y" else (a0, c0, a1, c1)


# ------------------------------------------------------------------------------------------- material tree
def _material(plan, prm, floor_nodes=None):
    """The cutting tree: every node with its width x length and children. Rip remainders are '<id>~w', cross-cut
    remainders '<id>~l'. floor_nodes: {piece: [(outside_id, width, length), ...]} adds the outside offcuts of floor
    pieces once they are laid."""
    W, L = prm["W"], prm["L"]
    nodes, kids, roll_of, tails = {}, {}, {}, []
    for k, roll in enumerate(plan["rolls"]):
        used = 0
        for cid, ln in roll:
            assert cid not in nodes, f"duplicate node {cid}"
            nodes[cid] = (W, ln)
            roll_of[cid] = k + 1
            used += ln
        assert used <= L, f"roll {k + 1} is {used} mm long, more than {L}"
        tails.append(L - used)
    todo = [("rip", n, parts) for n, parts in plan.get("rip", {}).items()] + \
        [("cross", n, parts) for n, parts in plan.get("cross", {}).items()]
    while True:
        rest = []
        for kind, n, parts in todo:
            if n not in nodes:
                rest.append((kind, n, parts))
                continue
            w, ln = nodes[n]
            assert n not in kids, f"{n} is cut twice"
            kids[n] = []
            if kind == "rip":
                tot = sum(x for _, x in parts)
                assert tot <= w, f"rip of {n}: {tot} > width {w}"
                for pid, x in parts:
                    nodes[pid] = (x, ln)
                    kids[n].append(pid)
                if w - tot:
                    nodes[n + "~w"] = (w - tot, ln)
                    kids[n].append(n + "~w")
            else:
                tot = sum(x for _, x in parts)
                assert tot <= ln, f"cross-cut of {n}: {tot} > length {ln}"
                for pid, x in parts:
                    nodes[pid] = (w, x)
                    kids[n].append(pid)
                if ln - tot:
                    nodes[n + "~l"] = (w, ln - tot)
                    kids[n].append(n + "~l")
        if floor_nodes:
            for p, outs in floor_nodes.items():
                if outs and p in nodes and outs[0][0] not in nodes:
                    for oid, w, ln in outs:
                        nodes[oid] = (w, ln)
                        kids.setdefault(p, []).append(oid)
        if len(rest) == len(todo):
            break
        todo = rest
    assert not todo, f"unresolved cuts: {[t[1] for t in todo]}"
    return nodes, kids, roll_of, tails


def _src_roll(n, nodes, kids, roll_of):
    parent = {c: p for p, cs in kids.items() for c in cs}
    while n in parent:
        n = parent[n]
    return roll_of.get(n)


# ----------------------------------------------------------------------------------------------- verification
def verify(room, prm, plan):
    """Check a plan piece by piece and return its quantities and its construction inventory (see module doc).
    Raises AssertionError when the plan is not physically complete."""
    if plan["method"] == "B":
        return _verify_B(room, prm, plan)
    return _verify_A(room, prm, plan)


def _offcuts(nodes, kids, placed, e):
    leaves = [n for n in nodes if n not in kids and n not in placed]
    out = []
    for n in sorted(leaves):
        w, ln = nodes[n]
        state = "TRUE_WASTE" if (w < MIN_PIECE_W or ln <= e) else "REUSABLE_SUBJECT_TO_N7"
        out.append({"id": n, "w": w, "l": ln, "area": w * ln, "state": state})
    return out


def _seam_zones(lay):
    """Lap zones between neighbouring strips: (cross from, cross to)."""
    st = lay["strips"]
    return [(st[i + 1]["c0"], st[i]["c1"]) for i in range(len(st) - 1)]


def _seam_ends(room, lay, rns):
    """Where each floor-strip lap zone meets the boundary (the walls across the strip ends): on a wall part (as a run
    interval) or inside a doorway."""
    poly = room["poly"]
    ci, ai = _axes(lay["along"])
    E = _edges(poly)
    out = []
    for k, (u, v) in enumerate(_seam_zones(lay)):
        for e, (a, b) in enumerate(E):
            if a[ai] != b[ai]:
                continue                                  # not an edge across the strip direction
            lo, hi = sorted((a[ci], b[ci]))
            p, q = max(lo, u), min(hi, v)
            if p >= q:
                continue
            (dx, dy), _ = _dir(a, b)
            t = sorted(abs(x - a[ci]) for x in (p, q))
            hit = None
            for d in room.get("doors", ()):
                if d["edge"] == e and d["t0"] <= t[0] and t[1] <= d["t1"]:
                    hit = ("DOORWAY", d["id"], None)
            if hit is None:
                for ri, rn in enumerate(rns):
                    for pe, ta, tb, r0 in rn["parts"]:
                        if pe == e and ta <= t[0] and t[1] <= tb:
                            hit = ("WALL", ri, (r0 + t[0] - ta, r0 + t[1] - ta))
            assert hit is not None, "a seam end straddles a jamb"
            out.append({"seam": k + 1, "edge": e, "kind": hit[0], "where": hit[1], "r": hit[2]})
    return out


def _dist_int(a, b, u, v):
    return max(0, u - b, a - v)


def joint_layout(rn, pieces_len, e, reverse=False):
    """Run positions of the pieces laid in order from the run start (or from its far jamb): [(start, end)], and
    the joint zones [(from, to)] (each the end lap of a piece over the one before)."""
    pos, cur = [], 0
    for k, ln in enumerate(pieces_len):
        s0 = 0 if k == 0 else cur - e
        pos.append((s0, s0 + ln))
        cur = s0 + ln
    assert cur == rn["length"], f"run covered to {cur}, needs {rn['length']}"
    if reverse:
        R = rn["length"]
        pos = [(R - b, R - a) for a, b in pos]
    joints = sorted((pos[k][0], pos[k - 1][1]) if not reverse else (pos[k - 1][0], pos[k][1])
                    for k in range(1, len(pos)))
    return pos, joints


def _joint_metrics(rn, joints, seam_r):
    """Per joint zone: the distance to the nearest corner of the run and to the nearest floor-seam end on it."""
    cd = [min(_dist_int(a, b, c, c) for c, _, _ in rn["corners"]) for a, b in joints] if rn["corners"] else []
    sd = [min(_dist_int(a, b, u, v) for u, v in seam_r) for a, b in joints] if seam_r else []
    return (min(cd) if cd else None), (min(sd) if sd else None), cd, sd


def best_arrangement(rn, pieces_len, e, seam_r):
    """Every order of the run's pieces, laid from either jamb: the arrangement that keeps the joints farthest from
    the corners and from the floor-seam ends (maximise the smaller distance, then the corner distance)."""
    best = None
    for perm in sorted(set(itertools.permutations(pieces_len))):
        for rev in (False, True):
            _, joints = joint_layout(rn, perm, e, rev)
            cdm, sdm, _, _ = _joint_metrics(rn, joints, seam_r)
            c = cdm if cdm is not None else 10 ** 9
            s = sdm if sdm is not None else 10 ** 9
            key = (min(c, s), c, s)
            if best is None or key > best[0]:
                best = (key, list(perm), rev, cdm, sdm)
    return {"order": best[1], "reversed": best[2], "corner_mm": best[3], "seam_end_mm": best[4]}


def _linf(px, py, r):
    x0, y0, x1, y1 = r
    return max(x0 - px, px - x1, y0 - py, py - y1, 0)


def _verify_A(room, prm, plan):
    poly = room["poly"]
    check_poly(poly)
    W, e, h, dl = prm["W"], prm["e"], prm["h"], prm["dl"]
    j = plan["j"]
    b = h + j
    lay = floor_layout(poly, plan["along"], prm)
    ci, ai = _axes(plan["along"])
    rns = runs(room)
    assert len(plan["floor"]) == lay["n"], f"{len(plan['floor'])} floor entries for {lay['n']} strips"
    floor_out = {}
    for k, ent in enumerate(plan["floor"]):
        if isinstance(ent, str):
            outs = lay["strips"][k]["outside"]
            floor_out[ent] = [(f"{ent}.o{q + 1}", o[1] - o[0], o[3] - o[2]) for q, o in enumerate(outs)]
    nodes, kids, roll_of, tails = _material(plan, prm, floor_out)
    placed = {}
    # floor strips
    xs = [p[0] for p in poly]
    ys = [p[1] for p in poly]
    g = Grid(min(xs), min(ys), max(xs), max(ys))
    for k, ent in enumerate(plan["floor"]):
        st = lay["strips"][k]
        assert isinstance(ent, str), "method A strips are single pieces"
        w, ln = nodes[ent]
        assert w == st["w"] and ln == st["len"], f"{ent} is {w} x {ln}, strip {k + 1} needs {st['w']} x {st['len']}"
        for r in st["rects"]:
            g.add(*_rect_xy(plan["along"], *r))
        placed[ent] = ("FLOOR", st["laid"])
    fc = _poly_cells(poly, g)
    assert all(g.n[jj][ii] >= 1 for ii, jj in fc), "the floor strips leave part of the floor uncovered"
    floor_net = len(fc) * CELL * CELL
    side_laps = sum(g.n[jj][ii] - 1 for ii, jj in fc) * CELL * CELL
    # doorway pieces
    doors = {d["id"]: d for d in room.get("doors", ())}
    dw = {}
    for did, pid in plan.get("doorways", {}).items():
        d = doors[did]
        w, ln = nodes[pid]
        assert ln == d["t1"] - d["t0"] and w == d["depth"] + dl, f"{pid} is {w} x {ln} for door {did}"
        placed[pid] = ("DOORWAY", w * ln)
        dw[did] = pid
    assert set(dw) == set(doors), "every doorway needs its continuation piece"
    # band runs
    assert len(plan["runs"]) == len(rns)
    seam_e = _seam_ends(room, lay, rns)
    band, joints_all, corner_rows = [], [], []
    for ri, (rn, pcs) in enumerate(zip(rns, plan["runs"])):
        lens = []
        for pid in pcs:
            w, ln = nodes[pid]
            assert w == b, f"band piece {pid} is {w} wide, the band is {b}"
            assert ln > e, f"band piece {pid} ({ln}) covers nothing past its lap"
            lens.append(ln)
            placed[pid] = ("BAND", w * ln)
        rev = ri in plan.get("reversed", ())
        pos, joints = joint_layout(rn, lens, e, rev)
        seam_r = [x["r"] for x in seam_e if x["kind"] == "WALL" and x["where"] == ri]
        cdm, sdm, cd, sd = _joint_metrics(rn, joints, seam_r)
        stack = sum(1 for a, bb in joints for u, v in seam_r if min(bb, v) - max(a, u) > 0)   # lap on lap
        touch = sum(1 for a, bb in joints for u, v in seam_r if min(bb, v) - max(a, u) == 0)  # edge to edge
        for c, kind, v in rn["corners"]:
            inside = [pcs[k] for k, (a, bb) in enumerate(pos) if a < c < bb]
            edge = [pcs[k] for k, (a, bb) in enumerate(pos) if c in (a, bb)]
            corner_rows.append({"run": ri + 1, "r": c, "kind": kind, "vertex": v, "continuous_in": inside,
                                "piece_edge_at_corner": edge})
        band.append({"run": ri + 1, "length": rn["length"], "pieces": list(zip(pcs, lens, pos)), "joints": joints,
                     "joint_corner_mm": cd, "joint_seam_end_mm": sd, "min_corner_mm": cdm, "min_seam_end_mm": sdm,
                     "stacked_on_seam_ends": stack, "touching_seam_ends": touch, "from": rn["from"], "to": rn["to"],
                     "best": best_arrangement(rn, lens, e, seam_r)})
        joints_all += joints
    R = sum(rn["length"] for rn in rns)
    n_int = sum(1 for rn in rns for c in rn["corners"] if c[1] == INTERNAL)
    n_ext = sum(1 for rn in rns for c in rn["corners"] if c[1] == EXTERNAL)
    upturn = R * h
    dw_net = sum((d["t1"] - d["t0"]) * d["depth"] for d in doors.values())
    laps = {"side": side_laps, "floor_end": 0, "junction_flange": R * j, "band_end": len(joints_all) * e * b,
            "doorway": sum((d["t1"] - d["t0"]) * dl for d in doors.values())}
    installed = sum(a for _, a in placed.values())
    net = floor_net + upturn + dw_net
    assert installed == net + sum(laps.values()), "installed membrane does not close against net + laps"
    off = _offcuts(nodes, kids, placed, e)
    consumed = sum(ln for roll in plan["rolls"] for _, ln in roll) * W
    _balance(nodes, kids, placed, plan, consumed)
    jambs = []
    for rn in rns:
        jambs += [{"door": rn["from"], "at": "run start", "overlap_mm": 0, "state": "BUTT_JOINT_OPEN"},
                  {"door": rn["to"], "at": "run end", "overlap_mm": 0, "state": "BUTT_JOINT_OPEN"}]
    pipes = []
    big = 10 ** 7
    zones = [("floor seam", _rect_xy(plan["along"], u, v, -big, big)) for u, v in _seam_zones(lay)]
    zones += [("band flange", r) for r in flange_zones(room, j)]
    for p in room.get("pipes", ()):
        ds = sorted((_linf(p["x"], p["y"], r), what) for what, r in zones)
        pipes.append({"id": p["id"], "at": (p["x"], p["y"]), "nearest": ds[0][1], "clear_mm": ds[0][0],
                      "max_centred_square_patch_mm": 2 * ds[0][0],
                      "clearances_mm": {w: min(d for d, ww in ds if ww == w) for _, w in ds}})
    t_points = Counter(x["kind"] for x in seam_e)
    return {
        "method": "A", "along": plan["along"], "j": j, "band_w": b,
        "floor_net": floor_net, "upturn": upturn, "doorway_net": dw_net, "proven_subtotal": net,
        "laps": laps, "laps_total": sum(laps.values()), "installed": installed, "consumed": consumed,
        "offcuts": off, "true_waste": sum(o["area"] for o in off if o["state"] == "TRUE_WASTE"),
        "reusable": sum(o["area"] for o in off if o["state"] != "TRUE_WASTE"),
        "stock": sum(t for t in tails) * W, "tails": tails, "rolls": len(plan["rolls"]),
        "floor_seams": lay["n"] - 1, "floor_end_laps": 0, "band_joints": len(joints_all),
        "seams": lay["n"] - 1 + len(joints_all),
        "floor_wall_junction": {"type": "SEPARATE_UPSTAND", "flange_mm": j, "length_mm": R,
                                "internal_corner_flange_pleats": n_int, "pleat_area": n_int * j * j,
                                "external_corner_flange_gaps": n_ext, "gap_area": n_ext * j * j},
        "corners": corner_rows, "corners_internal": n_int, "corners_external": n_ext,
        "band": band, "jambs": jambs, "seam_ends": seam_e,
        "t_points": {"flange_over_seam_end": t_points.get("WALL", 0),
                     "doorway_lap_over_seam_end": t_points.get("DOORWAY", 0),
                     "band_joint_over_seam_end": sum(x["stacked_on_seam_ends"] for x in band)},
        "pipes": pipes, "pieces": _piece_table(plan, nodes, kids, roll_of, placed, lay, band, dw),
    }


def _balance(nodes, kids, placed, plan, consumed):
    """Material conservation over the cutting tree: every cut = its installed part + its offcuts."""
    leaves = [n for n in nodes if n not in kids]
    tot = 0
    for n in nodes:
        if n in placed:
            tot += placed[n][1]
        elif n in leaves:
            tot += nodes[n][0] * nodes[n][1]
    assert tot == consumed, f"material balance: {tot} placed + offcuts != {consumed} consumed"


def _piece_table(plan, nodes, kids, roll_of, placed, lay, band, dw):
    dest = {}
    for k, ent in enumerate(plan["floor"]):
        for p in ([ent] if isinstance(ent, str) else ent):
            st = lay["strips"][k]
            dest[p] = f"floor strip {k + 1}, laid {st['c0'] / 1000:.2f}-{st['c1'] / 1000:.2f} m across"
    for bd in band:
        for pid, ln, (a, bb) in bd["pieces"]:
            dest[pid] = f"run {bd['run']} at {a / 1000:.2f}-{bb / 1000:.2f} m"
    for did, pid in dw.items():
        dest[pid] = f"doorway {did}"
    parent = {c: p for p, cs in kids.items() for c in cs}
    rows = []
    for n in nodes:
        w, ln = nodes[n]
        rows.append({"id": n, "w": w, "l": ln, "roll": _src_roll(n, nodes, kids, roll_of), "from": parent.get(n),
                     "to": dest.get(n) or ("cut further" if n in kids else "offcut")})
    return rows


def _verify_B(room, prm, plan):
    poly = room["poly"]
    check_poly(poly)
    W, e, h = prm["W"], prm["e"], prm["h"]
    dv = developed(room, prm)
    lay = floor_layout(dv["rect"], plan["along"], prm)
    nodes, kids, roll_of, tails = _material(plan, prm)
    rx = [p[0] for p in dv["rect"]]
    ry = [p[1] for p in dv["rect"]]
    g = Grid(min(rx), min(ry), max(rx), max(ry))
    placed, end_laps = {}, 0
    assert len(plan["floor"]) == lay["n"]
    for k, ent in enumerate(plan["floor"]):
        st = lay["strips"][k]
        pcs = [ent] if isinstance(ent, str) else ent
        a = st["a0"]
        for q, p in enumerate(pcs):
            w, ln = nodes[p]
            assert w == st["w"], f"{p} is {w} wide, strip {k + 1} needs {st['w']}"
            a0 = a if q == 0 else a - e
            a1 = a0 + ln
            g.add(*_rect_xy(plan["along"], st["c0"], st["c1"], a0, a1))
            placed[p] = ("FLOOR", w * ln)
            a = a1
            end_laps += 1 if q else 0
        assert a == st["a1"], f"strip {k + 1} reaches {a}, needs {st['a1']}"
    allc = {(i, jj) for jj in range(g.ny) for i in range(g.nx)}
    corner_c = set()
    for c in dv["corners"]:
        corner_c |= set(g.cells(*c))
    req = allc - corner_c
    assert all(g.n[jj][i] >= 1 for i, jj in req), "the strips leave part of the developed surface uncovered"
    assert len(req) * CELL * CELL == dv["required"]
    laps = sum(g.n[jj][i] - 1 for i, jj in allc if g.n[jj][i] > 1) * CELL * CELL
    corner_excess = sum(g.n[jj][i] for i, jj in corner_c) * CELL * CELL
    installed = sum(a for _, a in placed.values())
    assert installed == dv["required"] + laps + corner_excess
    _balance(nodes, kids, placed, plan, sum(ln for roll in plan["rolls"] for _, ln in roll) * W)
    off = _offcuts(nodes, kids, placed, e)
    consumed = sum(ln for roll in plan["rolls"] for _, ln in roll) * W
    x0, y0, x1, y1 = dv["floor"]
    ci, ai = _axes(plan["along"])
    seams = _seam_zones(lay)
    crossings = []
    fixed = "y" if plan["along"] == "Y" else "x"        # the fold lines the seams run across
    folds = (y0, y1) if plan["along"] == "Y" else (x0, x1)
    dsegs = [door_segment(room, d) for d in room.get("doors", ())]
    for k, (u, v) in enumerate(seams):
        for end, fold in zip(("start", "end"), folds):
            kind = "WALL_FOLD"
            for ax, c, lo, hi in dsegs:
                if ax == fixed and c == fold and lo < v and u < hi:
                    kind = "DOORWAY_FLAP"
            crossings.append({"seam": k + 1, "end": end, "kind": kind})
    pipes = []
    for p in room.get("pipes", ()):
        zones = [("floor seam", _rect_xy(plan["along"], u, v, -10 ** 7, 10 ** 7)) for u, v in seams]
        zones += [("fold line", (x0, -10 ** 7, x0, 10 ** 7)), ("fold line", (x1, -10 ** 7, x1, 10 ** 7)),
                  ("fold line", (-10 ** 7, y0, 10 ** 7, y0)), ("fold line", (-10 ** 7, y1, 10 ** 7, y1))]
        ds = sorted((_linf(p["x"], p["y"], r), what) for what, r in zones)
        pipes.append({"id": p["id"], "at": (p["x"], p["y"]), "nearest": ds[0][1], "clear_mm": ds[0][0],
                      "max_centred_square_patch_mm": 2 * ds[0][0],
                      "clearances_mm": {w: min(d for d, ww in ds if ww == w) for _, w in ds}})
    n_doors = len(room.get("doors", ()))
    return {
        "method": "B", "along": plan["along"], "proven_subtotal": dv["required"],
        "floor_net": (x1 - x0) * (y1 - y0), "laps": {"side_and_end": laps, "floor_end_laps": end_laps},
        "laps_total": laps, "corner_excess": corner_excess, "installed": installed, "consumed": consumed,
        "offcuts": off, "true_waste": sum(o["area"] for o in off if o["state"] == "TRUE_WASTE"),
        "reusable": sum(o["area"] for o in off if o["state"] != "TRUE_WASTE"),
        "stock": sum(tails) * W, "tails": tails, "rolls": len(plan["rolls"]),
        "floor_seams": lay["n"] - 1, "floor_end_laps": end_laps, "band_joints": 0,
        "seams": lay["n"] - 1 + end_laps,
        "floor_wall_junction": {"type": "CONTINUOUS_FOLD", "fold_length_mm": perimeter(poly)},
        "corners_internal": 4, "corner_squares": [(c, (c[2] - c[0]) * (c[3] - c[1])) for c in dv["corners"]],
        "jamb_slits": 2 * n_doors, "slit_length_mm": h, "seam_crossings": crossings, "pipes": pipes,
        "pieces": _piece_table(plan, nodes, kids, roll_of, placed, lay, [], {}),
    }


# --------------------------------------------------------------------------------------------- packing
def pack(lengths, L):
    """Fewest rolls for a list of cut lengths: exact search (few cuts). Returns lists of indices per roll."""
    order = sorted(range(len(lengths)), key=lambda i: (-lengths[i], i))
    lb = -(-sum(lengths) // L)
    for nb in range(max(lb, 1), len(lengths) + 1):
        bins = [[] for _ in range(nb)]
        load = [0] * nb

        def place(k):
            if k == len(order):
                return True
            i = order[k]
            seen = set()
            for q in range(nb):
                if load[q] + lengths[i] <= L and load[q] not in seen:
                    seen.add(load[q])
                    load[q] += lengths[i]
                    bins[q].append(i)
                    if place(k + 1):
                        return True
                    bins[q].pop()
                    load[q] -= lengths[i]
            return False

        if place(0):
            return [sorted(b, key=lambda i: (-lengths[i], i)) for b in bins if b]
    raise ValueError("a cut is longer than a roll")


# --------------------------------------------------------------------------------------------- planners
LEAST_MEMBRANE, FEWEST_JOINTS = "LEAST_MEMBRANE", "FEWEST_JOINTS"


def _key(objective, rolls, seams, consumed):
    return (rolls, consumed, seams) if objective == LEAST_MEMBRANE else (rolls, seams, consumed)


class _BandSearch:
    """Method A, one open run and one doorway: the material that can supply the band and the doorway piece."""

    def __init__(self, room, prm, along, j):
        rns = runs(room)
        assert len(rns) == 1 and not rns[0]["closed"] and len(room["doors"]) == 1, "one open run, one doorway"
        self.R = rns[0]["length"]
        d = room["doors"][0]
        self.wd, self.dwW = d["t1"] - d["t0"], d["depth"] + prm["dl"]
        self.W, self.L, self.e = prm["W"], prm["L"], prm["e"]
        self.b = prm["h"] + j
        self.k = self.W // self.b
        self.sres = self.W - self.k * self.b
        self.lay = floor_layout(room["poly"], along, prm)
        self.flo = [st["len"] for st in self.lay["strips"]]
        self.tl = [(st["len"], ("T", st["i"], q)) for st in self.lay["strips"] if st["w"] < self.W
                   for q in range((self.W - st["w"]) // self.b)]
        self.tr = [((self.W - st["w"]) % self.b, st["len"], ("T", st["i"])) for st in self.lay["strips"]
                   if st["w"] < self.W and (self.W - st["w"]) % self.b]
        self._packs = {}

    def rolls(self, segs):
        key = tuple(sorted(segs))
        if key not in self._packs:
            self._packs[key] = len(pack(self.flo + list(segs), self.L))
        return self._packs[key]

    def best(self, segs):
        """Fewest band pieces over the doorway-piece sources: (pieces, source, chosen lanes) or None."""
        lanes = self.tl + [(g, ("G", s, q)) for s, g in enumerate(segs) for q in range(self.k)]
        opts = []
        if self.b >= self.dwW:
            opts += [("LANE", x) for x, (ln, _) in enumerate(lanes) if ln >= self.wd]
        opts += [("RES", src) for w, ln, src in self.tr if w >= self.dwW and ln >= self.wd]
        opts += [("RES", ("G", s)) for s, g in enumerate(segs) if self.sres >= self.dwW and g >= self.wd]
        out = None
        for o in opts:
            ls = [((ln - self.wd) if o == ("LANE", x) else ln, src) for x, (ln, src) in enumerate(lanes)]
            srt = sorted(ls, key=lambda t: (-t[0], t[1]))
            tot = m = 0
            for ln, _ in srt:
                if ln <= self.e or tot >= self.R:
                    break
                tot += ln - (self.e if m else 0)
                m += 1
            if tot >= self.R and (out is None or m < out[0]):
                out = (m, o, srt[:m])
        return out


def plan_A(room, prm, along, objective, j):
    """The best method-A plan under the objective: LEAST_MEMBRANE ranks (rolls, consumed, seams), FEWEST_JOINTS
    (rolls, seams, consumed). The band material comes from the strip trims and from up to two new full-width
    segments in 10 mm steps (each in a roll tail or a new roll). Returns (key, plan, summary)."""
    S = _BandSearch(room, prm, along, j)
    nfl = S.lay["n"] - 1
    best = None

    def consider(segs, det):
        nonlocal best
        key = _key(objective, S.rolls(segs), nfl + det[0] - 1, sum(S.flo) + sum(segs))
        if best is None or key < best[0]:
            best = (key, list(segs), det)

    det = S.best([])
    if det:
        consider([], det)
    steps = list(range(CELL, S.L + 1, CELL))
    for g in steps:
        det = S.best([g])
        if det:
            consider([g], det)
    mmax = len(S.tl) + 2 * S.k
    for g1 in steps:
        for cap in range(1, mmax + 1):
            lo, hi = 0, steps.index(g1)
            ok = S.best([g1, steps[hi]])
            if not ok or ok[0] > cap:
                continue
            while lo < hi:                                      # the shortest second segment within the cap
                mid = (lo + hi) // 2
                t = S.best([g1, steps[mid]])
                if t and t[0] <= cap:
                    hi = mid
                else:
                    lo = mid + 1
            consider([g1, steps[lo]], S.best([g1, steps[lo]]))
    key, segs, det = best
    plan = _build_A(room, prm, along, j, S, segs, det)
    return key, plan, {"rolls": key[0], "segments": segs, "band_pieces": det[0], "doorway_from": det[1][0]}


def _build_A(room, prm, along, j, S, segs, det):
    W, e, b, k = S.W, S.e, S.b, S.k
    m, opt, chosen = det
    lay = S.lay
    cuts = [(f"S{st['i'] + 1}" if st["w"] == W else f"C{st['i'] + 1}", st["len"]) for st in lay["strips"]]
    cuts += [(f"G{s + 1}", g) for s, g in enumerate(segs)]
    rolls = [[cuts[i] for i in bn] for bn in pack([ln for _, ln in cuts], S.L)]
    rip, cross = {}, {}
    for st in lay["strips"]:
        if st["w"] < W:
            rip[f"C{st['i'] + 1}"] = [(f"S{st['i'] + 1}", st["w"])] + \
                [(f"T{st['i'] + 1}.{q + 1}", b) for q in range((W - st["w"]) // b)]
    for s in range(len(segs)):
        rip[f"G{s + 1}"] = [(f"G{s + 1}.{q + 1}", b) for q in range(k)]

    def lane_id(src):
        return f"{src[0]}{src[1] + 1}.{src[2] + 1}"

    lanes = S.tl + [(g, ("G", s, q)) for s, g in enumerate(segs) for q in range(k)]
    if opt[0] == "LANE":
        lid = lane_id(lanes[opt[1]][1])
        if b > S.dwW:
            cross[lid] = [(lid + "d", S.wd)]
            rip[lid + "d"] = [("DW", S.dwW)]
        else:
            cross[lid] = [("DW", S.wd)]
    else:
        src = opt[1]
        par = (f"C{src[1] + 1}~w" if src[0] == "T" else f"G{src[1] + 1}~w")
        width = (W - lay["strips"][src[1]]["w"]) % b if src[0] == "T" else S.sres
        if width > S.dwW:
            rip[par] = [(par + "d", S.dwW)]
            cross[par + "d"] = [("DW", S.wd)]
        else:
            cross[par] = [("DW", S.wd)]
    pieces, cover = [], 0
    for q, (ln, src) in enumerate(chosen):
        use = min(ln, S.R - cover + (e if q else 0))
        pid = f"B{q + 1}"
        cross.setdefault(lane_id(src), []).append((pid, use))
        pieces.append(pid)
        cover += use - (e if q else 0)
    floor = [f"S{st['i'] + 1}" for st in lay["strips"]]
    return {"id": f"plan_A {along} j={j}", "method": "A", "along": along, "j": j, "rolls": rolls, "rip": rip,
            "cross": cross, "floor": floor, "runs": [pieces], "doorways": {room["doors"][0]["id"]: "DW"}}


def plan_B(room, prm, along, objective, splice=True):
    """The best method-B plan: strips over the developed surface; one full-width strip may be spliced from two
    pieces joined by an end lap e when that saves a roll. Returns (key, plan)."""
    W, L, e = prm["W"], prm["L"], prm["e"]
    lay = floor_layout(developed(room, prm)["rect"], along, prm)
    n = lay["n"]
    full = [st["i"] for st in lay["strips"] if st["w"] == W]
    opts = [None]
    if splice and full:
        ln = lay["strips"][full[len(full) // 2]]["len"]
        opts += [(full[len(full) // 2], x, ln - x + e) for x in range(CELL, ln, CELL) if x > e and ln - x > 0]
    best = None
    for sp in opts:
        cuts, floor = [], []
        for st in lay["strips"]:
            sid = f"S{st['i'] + 1}"
            if sp is not None and st["i"] == sp[0]:
                cuts += [(sid + "a", sp[1]), (sid + "b", sp[2])]
                floor.append([sid + "a", sid + "b"])
            else:
                cuts.append((sid if st["w"] == W else f"C{st['i'] + 1}", st["len"]))
                floor.append(sid)
        bins = pack([c[1] for c in cuts], L)
        key = _key(objective, len(bins), n - 1 + (1 if sp else 0), sum(c[1] for c in cuts))
        if best is None or key < best[0]:
            best = (key, cuts, floor, bins)
    key, cuts, floor, bins = best
    rip = {f"C{st['i'] + 1}": [(f"S{st['i'] + 1}", st["w"])] for st in lay["strips"] if st["w"] < W}
    return key, {"id": f"plan_B {along}", "method": "B", "along": along,
                 "rolls": [[cuts[i] for i in bn] for bn in bins], "rip": rip, "cross": {}, "floor": floor}


# --------------------------------------------------------------------------------------------- reporting
def _m2(x):
    return round(x / 1e6, 6)


def _m(x):
    return None if x is None else round(x / 1000, 6)


def summary(res):
    """The quantities of a verified plan in metres / square metres, keyed like the cases' expected values."""
    q = {"consumed_m2": _m2(res["consumed"]), "installed_m2": _m2(res["installed"]),
         "laps_total_m2": _m2(res["laps_total"]), "true_waste_m2": _m2(res["true_waste"]),
         "reusable_m2": _m2(res["reusable"]), "stock_m2": _m2(res["stock"]), "rolls": res["rolls"],
         "floor_seams": res["floor_seams"], "band_joints": res["band_joints"], "seams": res["seams"],
         "proven_subtotal_m2": _m2(res["proven_subtotal"]), "floor_end_laps": res["floor_end_laps"]}
    if res["method"] == "A":
        lp = res["laps"]
        cm = [b["min_corner_mm"] for b in res["band"] if b["min_corner_mm"] is not None]
        sm = [b["min_seam_end_mm"] for b in res["band"] if b["min_seam_end_mm"] is not None]
        bc = [b["best"]["corner_mm"] for b in res["band"] if b["best"]["corner_mm"] is not None]
        bs = [b["best"]["seam_end_mm"] for b in res["band"] if b["best"]["seam_end_mm"] is not None]
        fj = res["floor_wall_junction"]
        q.update({"laps_side_m2": _m2(lp["side"]), "laps_junction_m2": _m2(lp["junction_flange"]),
                  "laps_band_end_m2": _m2(lp["band_end"]), "laps_doorway_m2": _m2(lp["doorway"]),
                  "min_joint_corner_m": _m(min(cm)) if cm else None,
                  "min_joint_seam_end_m": _m(min(sm)) if sm else None,
                  "joints_stacked_on_seam_ends": sum(b["stacked_on_seam_ends"] for b in res["band"]),
                  "jamb_butt_joints": len(res["jambs"]), "corners_internal": res["corners_internal"],
                  "corners_external": res["corners_external"], "flange_pleats_m2": _m2(fj["pleat_area"]),
                  "flange_gaps_m2": _m2(fj["gap_area"]),
                  "t_flange_over_seam_end": res["t_points"]["flange_over_seam_end"],
                  "t_doorway_lap_over_seam_end": res["t_points"]["doorway_lap_over_seam_end"],
                  "piece_edges_at_corners": sum(len(c["piece_edge_at_corner"]) for c in res["corners"]),
                  "best_corner_m": _m(min(bc)) if bc else None, "best_seam_end_m": _m(min(bs)) if bs else None})
    else:
        q.update({"corner_excess_m2": _m2(res["corner_excess"]), "jamb_slits": res["jamb_slits"],
                  "seam_crossings_doorway": sum(1 for c in res["seam_crossings"] if c["kind"] == "DOORWAY_FLAP"),
                  "seam_crossings_wall": sum(1 for c in res["seam_crossings"] if c["kind"] == "WALL_FOLD")})
    if res["pipes"]:
        p = res["pipes"][0]
        q.update({"pipe_clear_m": _m(p["clear_mm"]), "pipe_patch_max_m": _m(p["max_centred_square_patch_mm"]),
                  "pipe_seam_clear_m": _m(p["clearances_mm"].get("floor seam"))})
    return q


def sweep(room, prm, js):
    """Method A on a one-run room for each junction flange j (mm): per direction the least-membrane and the
    fewest-joints plan; 'V25' = the least-membrane plans compared by rolls -> seams -> membrane (V2.5's reading),
    'RULE' = every plan compared by rolls -> seams -> membrane (UP-WP-LAY-001 throughout)."""
    rows = []
    for j in js:
        row = {"j_mm": j, "by_direction": {}}
        for along in ("Y", "X"):
            for obj in (LEAST_MEMBRANE, FEWEST_JOINTS):
                _, plan, _ = plan_A(room, prm, along, obj, j)
                r = summary(verify(room, prm, plan))
                row["by_direction"][(along, obj)] = (r["rolls"], r["consumed_m2"], r["seams"])
        for name, obj in (("V25", LEAST_MEMBRANE), ("RULE", FEWEST_JOINTS)):
            best = min(((v[0], v[2], v[1]), a) for (a, o), v in row["by_direction"].items() if o == obj)
            row[name] = (best[1], best[0][0], best[0][2], best[0][1])
        rows.append(row)
    return rows
