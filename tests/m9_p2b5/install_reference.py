"""INSTALLATION REFERENCE - Phase 2B-5: the independent construction calculator of Phase 2B-4
(tests/m9_p2b4/construct_reference.py) generalised to the rooms of the ten ARCH_TAKEOFF_V2.6 worked examples. It keeps
that calculator's primitives (the cutting tree, the material balance, the 10 mm coverage grid, the offcut classes,
exact roll packing, the developed surface of method B) and adds what the examples need:

    closed band loops   a room with no doorway: every band piece laps the one before, the first over the last; the
                        best arrangement also searches the start of the loop (10 mm steps)
    obstructions        room["holes"]: a column or shaft inside the room; the floor strips are cut around it (its
                        footprint is an offcut of the strip), its faces carry a closed band loop whose corners are
                        EXTERNAL seen from the room
    breaks              room["breaks"]: an open edge or a passage of the outer ring (no upturn); a band run that ends
                        there ends at a TERMINATION, a run that ends at a door at a BUTT_JOINT_OPEN jamb
    spliced strips      a floor strip longer than a roll is a list of pieces joined by end laps; the end laps of
                        neighbouring strips are reported with their stagger
    drains              room["drains"]: like pipes - the clear distance to every floor lap and band flange; a drain
                        inside a lap zone is ON_SEAM
    shared packing      pack_shared(...): the fewest rolls for the cut lengths of several areas of ONE membrane system

Stdlib only, integer millimetres. It imports the Phase 2B-4 calculator and nothing else of the project: neither the
engine nor any other calculator (an AST test checks this). The plan format is construct_reference's; a band piece list
per run follows runs(room) order (outer ring first, then each obstruction).
"""

from __future__ import annotations

import itertools
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "m9_p2b4"))

import construct_reference as CR                             # noqa: E402

CELL, URBAN = CR.CELL, CR.URBAN
INTERNAL, EXTERNAL = CR.INTERNAL, CR.EXTERNAL


# --------------------------------------------------------------------------------------------------- rings and runs
def rings(room):
    return [room["poly"]] + [h for h in room.get("holes", ())]


def _kind(poly, v, hole):
    k = CR.corner_kind(poly, v)
    if not hole:
        return k
    return EXTERNAL if k == INTERNAL else INTERNAL


def _ring_runs(poly, gaps, ring, hole):
    n = len(poly)
    lens = [CR._dir(a, b)[1] for a, b in CR._edges(poly)]
    if not gaps:
        parts, corners, r = [], [], 0
        for i in range(n):
            parts.append((i, 0, lens[i], r))
            r += lens[i]
            corners.append((r if (i + 1) % n else 0, _kind(poly, (i + 1) % n, hole), (i + 1) % n))
        return [{"length": r, "closed": True, "parts": parts, "corners": sorted(corners), "from": None, "to": None,
                 "from_kind": None, "to_kind": None, "ring": ring}]
    out = []
    for q, d in enumerate(gaps):
        nxt = gaps[(q + 1) % len(gaps)]
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
            corners.append((r, _kind(poly, v, hole), v))
            e, t = v, 0
        corners = [c for c in corners if 0 < c[0] < r]        # a run that starts or ends at a vertex: an upturn end
        if r > 0:
            out.append({"length": r, "closed": False, "parts": parts, "corners": corners, "from": d["id"],
                        "to": nxt["id"], "from_kind": d["kind"], "to_kind": nxt["kind"], "ring": ring})
    return out


def gaps_of(room):
    return sorted([dict(d, kind="DOOR") for d in room.get("doors", ())] +
                  [dict(b) for b in room.get("breaks", ())], key=lambda g: (g["edge"], g["t0"]))


def runs(room):
    """The band runs: the outer ring's runs between its gaps in ring order (the first after the first gap by edge,
    then position), then one closed loop per obstruction."""
    out = _ring_runs(room["poly"], gaps_of(room), 0, False)
    for k, h in enumerate(room.get("holes", ()), 1):
        CR.check_poly(h)
        out += _ring_runs(h, [], k, True)
    return out


def run_point(room, rn, r):
    poly = rings(room)[rn["ring"]]
    E = CR._edges(poly)
    for e, ta, tb, r0 in rn["parts"]:
        if r0 <= r <= r0 + tb - ta:
            a, b = E[e]
            (dx, dy), _ = CR._dir(a, b)
            t = ta + r - r0
            return (a[0] + dx * t, a[1] + dy * t)
    raise ValueError("position outside the run")


def flange_zones(room, j):
    """Method A: the band flange on the floor along every wall part, j into the room: [(run index, rect)]."""
    out = []
    for k, rn in enumerate(runs(room)):
        poly = rings(room)[rn["ring"]]
        E = CR._edges(poly)
        hole = rn["ring"] > 0
        for e, ta, tb, r0 in rn["parts"]:
            a, b = E[e]
            (dx, dy), _ = CR._dir(a, b)
            nx, ny = (-dy, dx) if not hole else (dy, -dx)       # into the room
            p0 = (a[0] + dx * ta, a[1] + dy * ta)
            p1 = (a[0] + dx * tb, a[1] + dy * tb)
            xs = sorted((p0[0], p1[0], p0[0] + nx * j, p1[0] + nx * j))
            ys = sorted((p0[1], p1[1], p0[1] + ny * j, p1[1] + ny * j))
            out.append((k, (xs[0], ys[0], xs[-1], ys[-1])))
    return out


# ------------------------------------------------------------------------------------------------------- floor
def _intervals_at(room, along, c):
    ci, ai = CR._axes(along)
    hits = sorted(a[ai] for ring in rings(room) for a, b in CR._edges(ring)
                  if a[ai] == b[ai] and min(a[ci], b[ci]) < c < max(a[ci], b[ci]))
    return [(hits[k], hits[k + 1]) for k in range(0, len(hits), 2)]


def _slabs(room, along, c0, c1):
    ci, _ = CR._axes(along)
    cuts = sorted({c0, c1} | {p[ci] for ring in rings(room) for p in ring if c0 < p[ci] < c1})
    return list(zip(cuts, cuts[1:]))


def floor_layout(room, along, prm):
    """As construct_reference.floor_layout, with the obstructions cut out: each strip is one stretch from its first
    to its last room cell; what lies outside the room inside that stretch (beyond a stepped wall, the footprint of a
    column) is listed per slab and joined over consecutive slabs."""
    ci, ai = CR._axes(along)
    W, s = prm["W"], prm["s"]
    cs = [p[ci] for p in room["poly"]]
    cmin, cmax = min(cs), max(cs)
    n = 1
    while cmin + (n - 1) * (W - s) + W < cmax:
        n += 1
    strips = []
    for i in range(n):
        c0 = cmin + i * (W - s)
        c1 = min(c0 + W, cmax)
        rects = []
        for u, v in _slabs(room, along, c0, c1):
            rects += [(u, v, a0, a1) for a0, a1 in _intervals_at(room, along, (u + v) / 2)]
        a0, a1 = min(r[2] for r in rects), max(r[3] for r in rects)
        outside = []
        for u, v in _slabs(room, along, c0, c1):
            p = a0
            for x0, x1 in sorted((r[2], r[3]) for r in rects if r[0] == u):
                if x0 > p:
                    outside.append((u, v, p, x0))
                p = x1
            if p < a1:
                outside.append((u, v, p, a1))
        strips.append({"i": i, "c0": c0, "c1": c1, "w": c1 - c0, "a0": a0, "a1": a1, "len": a1 - a0,
                       "rects": rects, "laid": sum((r[1] - r[0]) * (r[3] - r[2]) for r in rects),
                       "outside": CR._merge(outside)})
    return {"along": along, "n": n, "strips": strips, "cmin": cmin, "cmax": cmax}


def _in_room(room, x, y):
    return CR._inside(room["poly"], x, y) and not any(CR._inside(h, x, y) for h in room.get("holes", ()))


def _room_cells(room, g):
    out = []
    for jj in range(g.ny):
        y = g.y0 + jj * CELL + CELL / 2
        for i in range(g.nx):
            if _in_room(room, g.x0 + i * CELL + CELL / 2, y):
                out.append((i, jj))
    return out


# ------------------------------------------------------------------------------------------------ seams and joints
def floor_zones(lay, pieces):
    """SIDE laps between neighbouring strips over their common stretch; END laps where a strip is spliced
    (pieces: per strip the list of (from, to) along). -> [(kind, label, (x0, y0, x1, y1))]."""
    st = lay["strips"]
    out = []
    for i in range(len(st) - 1):
        a0, a1 = max(st[i]["a0"], st[i + 1]["a0"]), min(st[i]["a1"], st[i + 1]["a1"])
        if a1 > a0:
            out.append(("SIDE", f"S{i + 1}/S{i + 2}", CR._rect_xy(lay["along"], st[i + 1]["c0"], st[i]["c1"], a0, a1)))
    for i, ps in enumerate(pieces):
        for (p0, p1), (q0, q1) in zip(ps, ps[1:]):
            out.append(("END", f"S{i + 1} splice", CR._rect_xy(lay["along"], st[i]["c0"], st[i]["c1"], q0, p1)))
    return out


def _clip(p, q, rect):
    """The parameter interval of segment p-q inside the closed rectangle, or None (integer endpoints)."""
    x0, y0, x1, y1 = rect
    t0, t1 = 0.0, 1.0
    dx, dy = q[0] - p[0], q[1] - p[1]
    for pk, qk in ((-dx, p[0] - x0), (dx, x1 - p[0]), (-dy, p[1] - y0), (dy, y1 - p[1])):
        if pk == 0:
            if qk < 0:
                return None
        else:
            t = qk / pk
            if pk < 0:
                t0 = max(t0, t)
            else:
                t1 = min(t1, t)
    return (t0, t1) if t1 > t0 else None


def seam_ends(room, zones):
    """Where each floor lap zone meets the boundary: on a band run (WALL, as a run interval), in a doorway, at a
    break, or along a wall (the boundary runs inside the zone over more than the zone's width)."""
    rns = runs(room)
    out = []
    for ring_k, poly in enumerate(rings(room)):
        for e, (a, b) in enumerate(CR._edges(poly)):
            (dx, dy), ln = CR._dir(a, b)
            for kind, label, rect in zones:
                t = _clip(a, b, rect)
                if t is None:
                    continue
                s0, s1 = round(t[0] * ln), round(t[1] * ln)
                zw = min(rect[2] - rect[0], rect[3] - rect[1])
                shape = "ALONG" if s1 - s0 > zw else "END"
                hit = None
                if ring_k == 0:
                    for g in gaps_of(room):
                        if g["edge"] == e and g["t0"] <= s0 and s1 <= g["t1"]:
                            hit = ("DOORWAY" if g["kind"] == "DOOR" else "BREAK", g["id"], None)
                if hit is None:
                    for ri, rn in enumerate(rns):
                        if rn["ring"] != ring_k:
                            continue
                        for pe, ta, tb, r0 in rn["parts"]:
                            if pe == e and ta <= s0 and s1 <= tb:
                                hit = ("WALL", ri, (r0 + s0 - ta, r0 + s1 - ta))
                assert hit is not None, f"a seam end straddles a jamb ({label})"
                out.append({"zone": label, "seam": kind, "ring": ring_k, "edge": e, "kind": hit[0],
                            "where": hit[1], "r": hit[2], "shape": shape})
    return out


def joint_layout(rn, lens, e, reverse=False, offset=0):
    """Run positions of the pieces laid in order from the run start: an open run's first piece covers its length,
    every later piece laps e over the one before; a closed loop's first piece laps e over the last. Reversed: laid
    from the far end; offset: a closed loop started offset mm along the run. -> (positions, joint zones)."""
    R, closed = rn["length"], rn["closed"]
    pos, cur = [], 0
    for k, ln in enumerate(lens):
        lap = e if (closed or k) else 0
        pos.append((cur - lap, cur - lap + ln))
        cur += ln - lap
    assert cur == R, f"run covered to {cur}, needs {R}"
    joints = [(a, a + e) for k, (a, _) in enumerate(pos) if closed or k]
    if reverse:
        pos = [(R - b, R - a) for a, b in pos]
        joints = [(R - b, R - a) for a, b in joints]
    if offset:
        pos = [(a + offset, b + offset) for a, b in pos]
        joints = [(a + offset, b + offset) for a, b in joints]
    return pos, joints


def _cdist(a, b, x, R):
    return min(max(0, a - (x + k * R), (x + k * R) - b) for k in ((-1, 0, 1) if R else (0,)))


def _cgap(a, b, u, v, R):
    best = None
    for k in ((-1, 0, 1) if R else (0,)):
        g, o = max(0, u + k * R - b, a - v - k * R), min(b, v + k * R) - max(a, u + k * R)
        if best is None or (g, -o) < (best[0], -best[1]):
            best = (g, o)
    return best


def joint_metrics(rn, joints, seam_r):
    R = rn["length"] if rn["closed"] else 0
    cs = [c for c, _, _ in rn["corners"]]
    cd = [min(_cdist(a, b, c, R) for c in cs) for a, b in joints] if cs else []
    sd, stack, touch = [], 0, 0
    for a, b in joints:
        gs = [_cgap(a, b, u, v, R) for u, v in seam_r]
        stack += sum(1 for _, o in gs if o > 0)
        touch += sum(1 for _, o in gs if o == 0)
        if gs:
            sd.append(min(g for g, _ in gs))
    return {"corner": min(cd) if cd else None, "seam_end": min(sd) if sd else None, "corner_each": cd,
            "seam_end_each": sd, "stacked": stack, "touching": touch}


def best_arrangement(rn, lens, e, seam_r):
    """Every order of the run's pieces, laid from either end (and for a closed loop from every start in 10 mm
    steps): the arrangement whose joints are farthest from the corners and the floor-seam ends (the smaller of the two
    first, then the corner distance, then the seam-end distance)."""
    closed, R = rn["closed"], rn["length"]
    perms = sorted(set(itertools.permutations(lens)))
    if closed:
        first = min(lens)
        perms = [p for p in perms if p[0] == first]
    offs = range(0, R, CELL) if closed else (0,)
    best = None
    for perm in perms:
        for rev in (False, True):
            for off in offs:
                _, joints = joint_layout(rn, perm, e, rev, off)
                m = joint_metrics(rn, joints, seam_r)
                c = m["corner"] if m["corner"] is not None else 10 ** 9
                s = m["seam_end"] if m["seam_end"] is not None else 10 ** 9
                key = (min(c, s), c, s)
                if best is None or key > best[0]:
                    best = (key, list(perm), rev, off, m)
    return {"order": best[1], "reversed": best[2], "offset": best[3], "corner_mm": best[4]["corner"],
            "seam_end_mm": best[4]["seam_end"]}


# ------------------------------------------------------------------------------------------------- verification
def _floor_pieces(nodes, ent, st, along, e):
    """The pieces of one floor strip entry along the strip: [(piece, from, to)]."""
    pcs = [ent] if isinstance(ent, str) else list(ent)
    out, a = [], st["a0"]
    for q, p in enumerate(pcs):
        w, ln = nodes[p]
        assert w == st["w"], f"{p} is {w} wide, strip {st['i'] + 1} needs {st['w']}"
        a0 = a if q == 0 else a - e
        out.append((p, a0, a0 + ln))
        a = a0 + ln
    assert a == st["a1"], f"strip {st['i'] + 1} reaches {a}, needs {st['a1']}"
    return out


def verify_A(room, prm, plan):
    """Method A (separate upstand), generalised: closed loops, obstructions, breaks, spliced floor strips, drains.
    Returns the quantities and the construction inventory; raises AssertionError when the plan is not complete."""
    poly = room["poly"]
    CR.check_poly(poly)
    W, e, h, dl = prm["W"], prm["e"], prm["h"], prm["dl"]
    j = plan["j"]
    b = h + j
    lay = floor_layout(room, plan["along"], prm)
    rns = runs(room)
    assert len(plan["floor"]) == lay["n"], f"{len(plan['floor'])} floor entries for {lay['n']} strips"
    floor_out = {}
    for k, ent in enumerate(plan["floor"]):
        if isinstance(ent, str):
            outs = lay["strips"][k]["outside"]
            floor_out[ent] = [(f"{ent}.o{q + 1}", o[1] - o[0], o[3] - o[2]) for q, o in enumerate(outs)]
    nodes, kids, roll_of, tails = CR._material(plan, prm, floor_out)
    placed = {}
    xs = [p[0] for p in poly]
    ys = [p[1] for p in poly]
    g = CR.Grid(min(xs), min(ys), max(xs), max(ys))
    pieces_along = []
    for k, ent in enumerate(plan["floor"]):
        st = lay["strips"][k]
        fp = _floor_pieces({n: nodes[n] for n in nodes}, ent, st, plan["along"], e)
        pieces_along.append([(a0, a1) for _, a0, a1 in fp])
        if isinstance(ent, str):
            for r in st["rects"]:
                g.add(*CR._rect_xy(plan["along"], *r))
            placed[ent] = ("FLOOR", st["laid"])
        else:
            assert not st["outside"], "a spliced strip with material outside the room is not modelled"
            for p, a0, a1 in fp:
                g.add(*CR._rect_xy(plan["along"], st["c0"], st["c1"], a0, a1))
                w, ln = nodes[p]
                placed[p] = ("FLOOR", w * ln)
    fc = _room_cells(room, g)
    assert all(g.n[jj][ii] >= 1 for ii, jj in fc), "the floor strips leave part of the floor uncovered"
    floor_net = len(fc) * CELL * CELL
    floor_laps = sum(g.n[jj][ii] - 1 for ii, jj in fc) * CELL * CELL
    zones = floor_zones(lay, pieces_along)
    end_laps = 0
    for kind, _, rect in zones:
        if kind == "END":
            end_laps += sum(1 for ii, jj in g.cells(*rect) if _in_room(room, g.x0 + ii * CELL + CELL / 2,
                                                                       g.y0 + jj * CELL + CELL / 2)) * CELL * CELL
    doors = {d["id"]: d for d in room.get("doors", ())}
    dw = {}
    for did, pid in plan.get("doorways", {}).items():
        d = doors[did]
        w, ln = nodes[pid]
        assert ln == d["t1"] - d["t0"] and w == d["depth"] + dl, f"{pid} is {w} x {ln} for door {did}"
        placed[pid] = ("DOORWAY", w * ln)
        dw[did] = pid
    assert set(dw) == set(doors), "every doorway needs its continuation piece"
    assert len(plan["runs"]) == len(rns), f"{len(plan['runs'])} band runs for {len(rns)}"
    se = seam_ends(room, zones)
    band, joints_all, corner_rows, jambs = [], [], [], []
    for ri, (rn, pcs) in enumerate(zip(rns, plan["runs"])):
        lens = []
        for pid in pcs:
            w, ln = nodes[pid]
            assert w == b, f"band piece {pid} is {w} wide, the band is {b}"
            assert ln > e, f"band piece {pid} ({ln}) covers nothing past its lap"
            lens.append(ln)
            placed[pid] = ("BAND", w * ln)
        rev = ri in plan.get("reversed", ())
        off = plan.get("offsets", {}).get(ri, 0)
        pos, joints = joint_layout(rn, lens, e, rev, off)
        seam_r = [x["r"] for x in se if x["kind"] == "WALL" and x["where"] == ri]
        m = joint_metrics(rn, joints, seam_r)
        R = rn["length"] if rn["closed"] else 0
        for c, kind, v in rn["corners"]:
            inside = [pcs[k] for k, (a, bb) in enumerate(pos) if any(a < c + q * R < bb for q in ((-1, 0, 1)
                                                                                                 if R else (0,)))]
            edge = [pcs[k] for k, (a, bb) in enumerate(pos) if any(c + q * R in (a, bb) for q in ((-1, 0, 1)
                                                                                                if R else (0,)))]
            corner_rows.append({"run": ri + 1, "r": c, "kind": kind, "vertex": v, "ring": rn["ring"],
                                "continuous_in": inside, "piece_edge_at_corner": edge})
        band.append({"run": ri + 1, "length": rn["length"], "closed": rn["closed"], "pieces": list(zip(pcs, lens, pos)),
                     "joints": joints, "min_corner_mm": m["corner"], "min_seam_end_mm": m["seam_end"],
                     "stacked_on_seam_ends": m["stacked"], "touching_seam_ends": m["touching"],
                     "from": rn["from"], "to": rn["to"], "best": best_arrangement(rn, lens, e, seam_r)})
        joints_all += joints
        if not rn["closed"]:
            for at, gid, kind in (("run start", rn["from"], rn["from_kind"]), ("run end", rn["to"], rn["to_kind"])):
                jambs.append({"door" if kind == "DOOR" else "break": gid, "at": at,
                              "state": "BUTT_JOINT_OPEN" if kind == "DOOR" else "TERMINATION_OPEN"})
    R = sum(rn["length"] for rn in rns)
    n_int = sum(1 for c in corner_rows if c["kind"] == INTERNAL)
    n_ext = sum(1 for c in corner_rows if c["kind"] == EXTERNAL)
    upturn = R * h
    dw_net = sum((d["t1"] - d["t0"]) * d["depth"] for d in doors.values())
    laps = {"side": floor_laps - end_laps, "floor_end": end_laps, "junction_flange": R * j,
            "band_end": len(joints_all) * e * b, "doorway": sum((d["t1"] - d["t0"]) * dl for d in doors.values())}
    installed = sum(a for _, a in placed.values())
    net = floor_net + upturn + dw_net
    assert installed == net + sum(laps.values()), "installed membrane does not close against net + laps"
    off_ = CR._offcuts(nodes, kids, placed, e)
    consumed = sum(ln for roll in plan["rolls"] for _, ln in roll) * W
    CR._balance(nodes, kids, placed, plan, consumed)
    big = 10 ** 7
    lap_rects = [("floor seam", r) for _, _, r in zones]
    lap_rects += [("band flange", r) for _, r in flange_zones(room, j)]
    points = []
    for what in ("pipes", "drains"):
        for p in room.get(what, ()):
            ds = sorted((CR._linf(p["x"], p["y"], r), w) for w, r in lap_rects)
            on = any(CR._linf(p["x"], p["y"], r) == 0 for w, r in lap_rects if w == "floor seam")
            points.append({"what": what[:-1], "id": p["id"], "at": (p["x"], p["y"]), "nearest": ds[0][1],
                           "clear_mm": ds[0][0], "max_centred_square_patch_mm": 2 * ds[0][0], "on_seam": on,
                           "clearances_mm": {w: min(d for d, ww in ds if ww == w) for _, w in ds}})
    stagger = []
    ends_by = [[(a1 - e, a1) for (_, a1) in ps[:-1]] for ps in pieces_along]
    for i in range(len(ends_by) - 1):
        for u in ends_by[i]:
            for v in ends_by[i + 1]:
                stagger.append({"strips": (i + 1, i + 2), "stagger_mm": max(0, v[0] - u[1], u[0] - v[1])})
    tp = Counter(x["kind"] for x in se if x["shape"] == "END")
    lay_order = None
    drains = room.get("drains", ())
    if len(drains) == 1:                                       # the strip with the drain first, then outwards
        ci, _ = CR._axes(plan["along"])
        cd = (drains[0]["x"], drains[0]["y"])[ci]
        mids = [(abs((st["c0"] + st["c1"]) - 2 * cd), st["i"] + 1) for st in lay["strips"]]
        lay_order = [i for _, i in sorted(mids)]
    return {
        "method": "A", "along": plan["along"], "j": j, "band_w": b,
        "floor_net": floor_net, "upturn": upturn, "doorway_net": dw_net, "proven_subtotal": net,
        "laps": laps, "laps_total": sum(laps.values()), "installed": installed, "consumed": consumed,
        "offcuts": off_, "true_waste": sum(o["area"] for o in off_ if o["state"] == "TRUE_WASTE"),
        "reusable": sum(o["area"] for o in off_ if o["state"] != "TRUE_WASTE"),
        "stock": sum(tails) * W, "tails": tails, "rolls": len(plan["rolls"]),
        "floor_seams": lay["n"] - 1, "floor_end_laps": sum(len(ps) - 1 for ps in pieces_along),
        "band_joints": len(joints_all), "seams": lay["n"] - 1 + sum(len(ps) - 1 for ps in pieces_along) +
        len(joints_all),
        "corners": corner_rows, "corners_internal": n_int, "corners_external": n_ext,
        "flange_pleats": n_int * j * j, "flange_gaps": n_ext * j * j,
        "band": band, "jambs": jambs, "seam_ends": se, "end_lap_stagger": stagger,
        "t_points": {"flange_over_seam_end": tp.get("WALL", 0), "doorway_lap_over_seam_end": tp.get("DOORWAY", 0),
                     "seam_end_at_break": tp.get("BREAK", 0),
                     "band_joint_over_seam_end": sum(x["stacked_on_seam_ends"] for x in band)},
        "points": points, "lay_order": lay_order,
    }


def summary(res):
    """The quantities of a verified method-A plan in metres / square metres."""
    m2, m = CR._m2, CR._m
    cm = [x["min_corner_mm"] for x in res["band"] if x["min_corner_mm"] is not None]
    sm = [x["min_seam_end_mm"] for x in res["band"] if x["min_seam_end_mm"] is not None]
    bc = [x["best"]["corner_mm"] for x in res["band"] if x["best"]["corner_mm"] is not None]
    bs = [x["best"]["seam_end_mm"] for x in res["band"] if x["best"]["seam_end_mm"] is not None]
    lp = res["laps"]
    q = {"consumed_m2": m2(res["consumed"]), "installed_m2": m2(res["installed"]),
         "laps_total_m2": m2(res["laps_total"]), "laps_side_m2": m2(lp["side"]), "laps_floor_end_m2": m2(
             lp["floor_end"]), "laps_junction_m2": m2(lp["junction_flange"]), "laps_band_end_m2": m2(lp["band_end"]),
         "laps_doorway_m2": m2(lp["doorway"]), "true_waste_m2": m2(res["true_waste"]),
         "reusable_m2": m2(res["reusable"]), "stock_m2": m2(res["stock"]), "rolls": res["rolls"],
         "floor_seams": res["floor_seams"], "floor_end_laps": res["floor_end_laps"], "band_joints": res["band_joints"],
         "seams": res["seams"], "proven_subtotal_m2": m2(res["proven_subtotal"]),
         "min_joint_corner_m": m(min(cm)) if cm else None, "min_joint_seam_end_m": m(min(sm)) if sm else None,
         "joints_stacked_on_seam_ends": sum(x["stacked_on_seam_ends"] for x in res["band"]),
         "jamb_butt_joints": sum(1 for x in res["jambs"] if x["state"] == "BUTT_JOINT_OPEN"),
         "terminations": sum(1 for x in res["jambs"] if x["state"] == "TERMINATION_OPEN"),
         "corners_internal": res["corners_internal"], "corners_external": res["corners_external"],
         "flange_pleats_m2": m2(res["flange_pleats"]), "flange_gaps_m2": m2(res["flange_gaps"]),
         "t_flange_over_seam_end": res["t_points"]["flange_over_seam_end"],
         "t_doorway_lap_over_seam_end": res["t_points"]["doorway_lap_over_seam_end"],
         "t_seam_end_at_break": res["t_points"]["seam_end_at_break"],
         "piece_edges_at_corners": sum(len(c["piece_edge_at_corner"]) for c in res["corners"]),
         "best_corner_m": m(min(bc)) if bc else None, "best_seam_end_m": m(min(bs)) if bs else None,
         "min_end_lap_stagger_m": m(min(x["stagger_mm"] for x in res["end_lap_stagger"]))
         if res["end_lap_stagger"] else None,
         "seams_along_walls": sum(1 for x in res["seam_ends"] if x["shape"] == "ALONG"),
         "run_min_joint_corner_m": [m(x["min_corner_mm"]) for x in res["band"]],
         "run_min_joint_seam_end_m": [m(x["min_seam_end_mm"]) for x in res["band"]],
         "band_pieces_m": sorted(m(ln) for x in res["band"] for _, ln, _ in x["pieces"]),
         "lay_order": res["lay_order"]}
    for p in res["points"]:
        q[f"{p['what']}_{p['id']}_clear_m"] = m(p["clear_mm"])
        q[f"{p['what']}_{p['id']}_on_seam"] = p["on_seam"]
    return q


# ------------------------------------------------------------------------------------------------------ packing
def pack_shared(groups, L):
    """Fewest rolls of length L for the cut lengths of several areas, per membrane system: {system: {area: [mm]}}
    -> {system: rolls}. Pieces of different systems never share a roll."""
    return {sid: len(CR.pack([x for area in sorted(areas) for x in areas[area]], L))
            for sid, areas in sorted(groups.items())}
