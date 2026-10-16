"""WATERPROOFING BOUNDARY GEOMETRY (M9 Phase 2B-2, ARCH_TAKEOFF_V2.4 only) - the boundary of a waterproofed area,
edge by edge, typed by what it is, so the upturn, the doorway transitions, the terminations and the corners come from
the polygon and not from a ratio (UP-WP-003, UP-WP-004, UP-WP-DOOR-001).

    features(S, ents, roles, unit_m, room)  -> typed segments (metres) that may lie on the room's boundary: wall faces,
                                               column sides, opening thresholds (door / passage / window), glazing
                                               lines, door closures, zone lines
    segments(ring, feats, tol)              -> the ring cut into runs of one role each, in ring order
    corners(segs, ring, hole=False)         -> corners where two upturned boundaries meet: INTERNAL (the room-side angle
                                               below 180 degrees) or EXTERNAL (above); upturn ends at a break
    runs(segs)                              -> the eligible upturn runs: one closed loop, or the open runs between breaks
    boundary(room, feats)                   -> all of the above for the outer ring and every obstruction ring

Roles, by priority where two features coincide: DOOR > PASSAGE > WINDOW_THRESHOLD > GLAZING > ZONE_LINE > COLUMN >
WALL; an edge no feature explains is OTHER (an open edge). Upturn-eligible: WALL, COLUMN, WINDOW_THRESHOLD (the sill wall
below a recognised window; a floor-level window is the window-type question). A window-layer line on the face of a
recognised window opening is its frame, not floor-level glazing; glazing no opening explains breaks the upturn.
Nothing is moved, snapped or invented; a ring the features do not explain is reported, not repaired.
Project-agnostic; stdlib only."""

from __future__ import annotations

import math

PRIORITY = ("DOOR", "PASSAGE", "WINDOW_THRESHOLD", "GLAZING", "ZONE_LINE", "COLUMN", "WALL")
ELIGIBLE = ("WALL", "COLUMN", "WINDOW_THRESHOLD")
TOL_M = 0.01
ANG_TOL = 1e-3
EPS = 1e-9


def _sub(a, b):
    return (a[0] - b[0], a[1] - b[1])


def _dot(a, b):
    return a[0] * b[0] + a[1] * b[1]


def _cross(a, b):
    return a[0] * b[1] - a[1] * b[0]


def signed_area(ring):
    return 0.5 * sum(_cross(ring[i], ring[(i + 1) % len(ring)]) for i in range(len(ring)))


def features(S, ents, roles, unit_m, room, *, wall_roles=("WALL",), window_roles=("WINDOW",)):
    """typed segments in metres: {"role", "id", "a", "b"} (roles maps a layer to its role)."""
    u = unit_m
    m = lambda p: (p[0] * u, p[1] * u)                                    # noqa: E731
    out = []
    for s in ents.get("segments") or ():
        ro = roles.get(s["layer"])
        if ro in wall_roles:
            out.append({"role": "WALL", "id": s["id"], "a": m(s["a"]), "b": m(s["b"])})
        elif ro in window_roles:
            out.append({"role": "GLAZING", "id": s["id"], "a": m(s["a"]), "b": m(s["b"])})
    for k, b in enumerate(S.get("column_boxes") or (), 1):
        x0, y0, x1, y1 = b
        for i, (a_, b_) in enumerate((((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)), ((x1, y1), (x0, y1)),
                                       ((x0, y1), (x0, y0)))):
            out.append({"role": "COLUMN", "id": f"COL{k}", "a": m(a_), "b": m(b_)})
    kind_role = {"DOOR": "DOOR", "PASSAGE": "PASSAGE", "WINDOW": "WINDOW_THRESHOLD"}
    for o in S.get("openings") or ():
        (ux, uy), (nx, ny) = o["u"], o["n"]
        for off in (o["o0"], o["o1"]):
            a_ = (ux * o["s0"] + nx * off, uy * o["s0"] + ny * off)
            b_ = (ux * o["s1"] + nx * off, uy * o["s1"] + ny * off)
            out.append({"role": kind_role[o["kind"]], "id": o["opening_id"], "a": m(a_), "b": m(b_)})
    for r in S.get("repairs") or ():
        if r.get("kind") == "DOOR_CLOSURE" and r.get("a") is not None:
            out.append({"role": "DOOR", "id": str(r.get("id", "")).rsplit("|", 1)[0], "a": m(r["a"]), "b": m(r["b"])})
    for ln in ((room.get("zone") or {}).get("lines") or ()):
        out.append({"role": "ZONE_LINE", "id": ln["id"], "a": m(ln["a"]), "b": m(ln["b"])})
    return out


def segments(ring, feats, tol=TOL_M):
    """-> [{"role", "id", "length_m", "a", "b", "edge"}] covering the ring exactly, in ring order (consecutive pieces
    of one role and id merged within an edge)."""
    out = []
    n = len(ring)
    for i in range(n):
        p, q = ring[i], ring[(i + 1) % n]
        d = _sub(q, p)
        L = math.hypot(*d)
        if L <= EPS:
            continue
        uu = (d[0] / L, d[1] / L)
        nn = (-uu[1], uu[0])
        ivs = []
        for f in feats:
            fa, fb = f["a"], f["b"]
            fd = _sub(fb, fa)
            fl = math.hypot(*fd)
            if fl <= EPS:
                continue
            if abs(_cross(uu, (fd[0] / fl, fd[1] / fl))) > ANG_TOL:
                continue
            if abs(_dot(_sub(fa, p), nn)) > tol or abs(_dot(_sub(fb, p), nn)) > tol:
                continue
            t0, t1 = sorted((_dot(_sub(fa, p), uu), _dot(_sub(fb, p), uu)))
            lo, hi = max(t0, 0.0), min(t1, L)
            if hi - lo > tol / 2:
                ivs.append((lo, hi, f["role"], f["id"]))
        cuts = sorted({0.0, L} | {x for lo, hi, _, _ in ivs for x in (lo, hi)})
        pieces = []
        for s0, s1 in zip(cuts, cuts[1:]):
            if s1 - s0 <= EPS:
                continue
            mid = (s0 + s1) / 2
            cover = [(PRIORITY.index(r), fid, r) for lo, hi, r, fid in ivs if lo - EPS <= mid <= hi + EPS]
            role, fid = ("OTHER", None) if not cover else (min(cover)[2], min(cover)[1])
            if pieces and pieces[-1][2] == role and pieces[-1][3] == fid:
                pieces[-1][1] = s1
            else:
                pieces.append([s0, s1, role, fid])
        for s0, s1, role, fid in pieces:
            out.append({"role": role, "id": fid, "length_m": s1 - s0, "edge": i,
                        "a": (p[0] + uu[0] * s0, p[1] + uu[1] * s0), "b": (p[0] + uu[0] * s1, p[1] + uu[1] * s1)})
    return out


def corners(segs, hole=False):
    """corners where two upturn-eligible segments of different edges meet. The room side is to the left of a
    counter-clockwise outer ring and outside an obstruction ring. -> {"internal", "external", "upturn_ends", "items"}."""
    out = {"internal": 0, "external": 0, "upturn_ends": 0, "items": []}
    n = len(segs)
    if n == 0:
        return out
    area_sign = 1.0
    ring_pts = [s["a"] for s in segs]
    if len(ring_pts) >= 3:
        area_sign = 1.0 if signed_area(ring_pts) >= 0 else -1.0
    for k in range(n):
        a, b = segs[k - 1], segs[k]
        ea, eb = a["role"] in ELIGIBLE, b["role"] in ELIGIBLE
        if ea != eb:
            out["upturn_ends"] += 1
            continue
        if not ea or a["edge"] == b["edge"]:
            continue
        da, db = _sub(a["b"], a["a"]), _sub(b["b"], b["a"])
        la, lb = math.hypot(*da), math.hypot(*db)
        if la <= EPS or lb <= EPS:
            continue
        c = _cross(da, db) / (la * lb) * area_sign
        if abs(c) <= ANG_TOL and _dot(da, db) > 0:
            continue
        convex = c > 0                         # a left turn on the ring's own orientation
        internal = convex if not hole else not convex
        kind = "INTERNAL" if internal else "EXTERNAL"
        out["internal" if internal else "external"] += 1
        out["items"].append({"kind": kind, "at": [round(b["a"][0], 4), round(b["a"][1], 4)],
                             "roles": [a["role"], b["role"]]})
    return out


def runs(segs):
    """eligible upturn runs: [{"length_m", "closed"}]; a ring with no break is one closed loop."""
    if not segs:
        return []
    elig = [s["role"] in ELIGIBLE for s in segs]
    if all(elig):
        return [{"length_m": sum(s["length_m"] for s in segs), "closed": True}]
    k0 = next(i for i, e in enumerate(elig) if not e)            # start just after a break
    order = segs[k0 + 1:] + segs[:k0 + 1]
    out, cur = [], 0.0
    for s in order:
        if s["role"] in ELIGIBLE:
            cur += s["length_m"]
        elif cur > EPS:
            out.append({"length_m": cur, "closed": False})
            cur = 0.0
        else:
            cur = 0.0
    if cur > EPS:
        out.append({"length_m": cur, "closed": False})
    return out


def _ccw(ring):
    r = [tuple(map(float, p)) for p in ring]
    return r if signed_area(r) >= 0 else r[::-1]


def boundary(room, feats, tol=TOL_M):
    """the boundary of one room: outer ring (counter-clockwise) and obstruction rings, typed; lengths by role; the
    eligible runs; the corners; the breaks (doorways, passages, glazing, zone lines, open edges) with their ids."""
    outer = _ccw(room.get("polygon_m") or ())
    rings = [("OUTER", outer)] + [("HOLE", _ccw(h)) for h in room.get("hole_polygons_m") or ()]
    by_role, all_runs, cor = {}, [], {"internal": 0, "external": 0, "upturn_ends": 0, "items": []}
    breaks, ring_out = [], []
    for kind, ring in rings:
        segs = segments(ring, feats, tol) if len(ring) >= 3 else []
        if kind == "HOLE":
            # an obstruction inside the area (a column or a boxed shaft): its faces are upturned unless a feature says
            # otherwise
            segs = [dict(s, role="COLUMN" if s["role"] == "OTHER" else s["role"]) for s in segs]
        for s in segs:
            by_role[s["role"]] = by_role.get(s["role"], 0.0) + s["length_m"]
            if s["role"] not in ELIGIBLE:
                breaks.append({"role": s["role"], "id": s["id"], "length_m": round(s["length_m"], 6), "ring": kind})
        all_runs += runs(segs)
        c = corners(segs, hole=kind == "HOLE")
        for k in ("internal", "external", "upturn_ends"):
            cor[k] += c[k]
        cor["items"] += c["items"]
        ring_out.append({"ring": kind, "segments": len(segs),
                         "length_m": round(sum(s["length_m"] for s in segs), 6)})
    merged = {}
    for b in breaks:
        key = (b["role"], b["id"], b["ring"])
        merged[key] = merged.get(key, 0.0) + b["length_m"]
    return {"by_role_lm": {k: round(v, 6) for k, v in sorted(by_role.items())},
            "eligible_lm": round(sum(v for k, v in by_role.items() if k in ELIGIBLE), 6),
            "runs": [{"length_m": round(r["length_m"], 6), "closed": r["closed"]} for r in all_runs],
            "corners": cor, "breaks": [{"role": k[0], "id": k[1], "ring": k[2], "length_m": round(v, 6)}
                                       for k, v in sorted(merged.items(), key=lambda x: (x[0][2], x[0][0],
                                                                                         str(x[0][1])))],
            "rings": ring_out, "total_lm": round(sum(by_role.values()), 6)}


def policy_record():
    return {"policy": "WP_GEOMETRY_V1", "priority": list(PRIORITY), "eligible": list(ELIGIBLE), "tolerance_m": TOL_M}
