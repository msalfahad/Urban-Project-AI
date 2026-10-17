"""PLANAR_SHADOW_TOPOLOGY_V1 - an independent planar-graph route for validating physical spaces (Route B).

It never replaces the production topology (room_topology_v3, Route A); it re-derives faces from the same linework by a
different, minimal algorithm so that the two routes can be compared region by region:

    1. arcs are discretised (fixed angular step)
    2. ENDPOINT MERGE        endpoints within eps snap to one node (grid hashing, first-come representative)
    3. SPLITTING             every segment is cut at proper intersections, T-junctions and at the nodes of collinear
                             overlapping segments (COLLINEAR FRAGMENTATION); identical fragments are deduplicated with
                             the union of their source ids
    4. DANGLING ANALYSIS     degree-1 nodes are peeled iteratively; the peeled edges are recorded (they bound no face)
    5. HALF-EDGE FACE WALK   outgoing half-edges sorted by angle; next(h) = the half-edge after twin(h) clockwise;
                             cycles with positive signed area are bounded faces, negative ones are component outers
    6. NESTING               a component's outer cycle lying inside a bounded face of another component is a HOLE of
                             the smallest such face (net area = face - holes)

Input segments carry a source id. Output faces carry ring, holes, area, perimeter, centroid and boundary source ids.
Deterministic (sorted iteration); project-agnostic; stdlib only.
"""

from __future__ import annotations

import hashlib
import math
from collections import defaultdict

POLICY_ID = "PLANAR_SHADOW_TOPOLOGY_V1"


def discretise_arc(cx, cy, r, a0, a1, step_deg=5.0):
    """Points along a CCW arc from a0 to a1 (radians)."""
    sweep = (a1 - a0) % (2 * math.pi) or 2 * math.pi
    n = max(2, int(math.ceil(math.degrees(sweep) / step_deg)))
    return [(cx + r * math.cos(a0 + sweep * i / n), cy + r * math.sin(a0 + sweep * i / n)) for i in range(n + 1)]


class _Nodes:
    def __init__(self, eps):
        self.eps = eps
        self.pts = []
        self.grid = defaultdict(list)

    def get(self, p):
        e = self.eps
        gx, gy = int(math.floor(p[0] / e)), int(math.floor(p[1] / e))
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for i in self.grid[(gx + dx, gy + dy)]:
                    q = self.pts[i]
                    if (q[0] - p[0]) ** 2 + (q[1] - p[1]) ** 2 <= e * e:
                        return i
        self.pts.append((p[0], p[1]))
        self.grid[(gx, gy)].append(len(self.pts) - 1)
        return len(self.pts) - 1


def _param(a, b, p):
    dx, dy = b[0] - a[0], b[1] - a[1]
    L2 = dx * dx + dy * dy
    return ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / L2 if L2 else 0.0


def _dist_point_seg(p, a, b):
    t = max(0.0, min(1.0, _param(a, b, p)))
    q = (a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1]))
    return math.hypot(p[0] - q[0], p[1] - q[1]), t


def _intersect(a, b, c, d):
    r = (b[0] - a[0], b[1] - a[1])
    s = (d[0] - c[0], d[1] - c[1])
    den = r[0] * s[1] - r[1] * s[0]
    if abs(den) < 1e-12:
        return None
    t = ((c[0] - a[0]) * s[1] - (c[1] - a[1]) * s[0]) / den
    u = ((c[0] - a[0]) * r[1] - (c[1] - a[1]) * r[0]) / den
    if -1e-9 <= t <= 1 + 1e-9 and -1e-9 <= u <= 1 + 1e-9:
        return (a[0] + t * r[0], a[1] + t * r[1])
    return None


def signed_area(ring):
    return 0.5 * sum(ring[i][0] * ring[(i + 1) % len(ring)][1] - ring[(i + 1) % len(ring)][0] * ring[i][1]
                     for i in range(len(ring)))


def point_in_ring(p, ring):
    x, y = p
    inside = False
    n = len(ring)
    for i in range(n):
        x1, y1 = ring[i]
        x2, y2 = ring[(i + 1) % n]
        if (y1 > y) != (y2 > y):
            xi = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
            if xi > x:
                inside = not inside
    return inside


def interior_point(ring):
    """A point strictly inside a simple ring (horizontal scanline through the bbox middle, widest span)."""
    ys = sorted({p[1] for p in ring})
    cand = []
    for k in range(len(ys) - 1):
        cand.append((ys[k] + ys[k + 1]) / 2.0)
    best = None
    for y in cand:
        xs = []
        n = len(ring)
        for i in range(n):
            (x1, y1), (x2, y2) = ring[i], ring[(i + 1) % n]
            if (y1 > y) != (y2 > y):
                xs.append(x1 + (y - y1) * (x2 - x1) / (y2 - y1))
        xs.sort()
        for i in range(0, len(xs) - 1, 2):
            w = xs[i + 1] - xs[i]
            if best is None or w > best[0]:
                best = (w, ((xs[i] + xs[i + 1]) / 2.0, y))
    return best[1] if best else ring[0]


def bridge_gaps(segments, *, min_gap, max_gap, eps=1.0, align=0.985):
    """GAP BRIDGING (an explicit, recorded closure rule - never material): a free end of a line whose continuation meets
    another free end FACING it along the same line, min_gap <= gap <= max_gap (an opening in a drawn wall face), is
    closed by a zero-material segment. Mutual nearest pairs only. Returns [(x0, y0, x1, y1, 'BRIDGE|a|b')]."""
    nodes = _Nodes(eps)
    ends = defaultdict(list)
    for x0, y0, x1, y1, sid in segments:
        a, b = nodes.get((x0, y0)), nodes.get((x1, y1))
        if a == b:
            continue
        ends[a].append((b, sid))
        ends[b].append((a, sid))
    P = nodes.pts
    free = {}
    for n, lst in ends.items():
        if len(lst) != 1:
            continue
        m, sid = lst[0]
        L = math.dist(P[n], P[m])
        # an end lying on another segment (T-junction) is not free
        free[n] = ((P[n][0] - P[m][0]) / L, (P[n][1] - P[m][1]) / L, sid)
    for x0, y0, x1, y1, _ in segments:
        for n in list(free):
            d, t = _dist_point_seg(P[n], (x0, y0), (x1, y1))
            if d <= eps and 1e-6 < t < 1 - 1e-6:
                free.pop(n)
    best = {}
    keys = sorted(free)
    for n in keys:
        vx, vy, _ = free[n]
        cand = None
        for m in keys:
            if m == n:
                continue
            wx, wy = P[m][0] - P[n][0], P[m][1] - P[n][1]
            g = math.hypot(wx, wy)
            if not (min_gap <= g <= max_gap):
                continue
            ux, uy, _ = free[m]
            if (vx * wx + vy * wy) / g >= align and -(ux * wx + uy * wy) / g >= align:
                if cand is None or g < cand[0]:
                    cand = (g, m)
        if cand:
            best[n] = cand[1]
    out = []
    for n, m in sorted(best.items()):
        if best.get(m) == n and n < m:
            out.append((P[n][0], P[n][1], P[m][0], P[m][1], f"BRIDGE|{free[n][2]}|{free[m][2]}"))
    return out


def build(segments, *, eps=1.0, arcs=(), arc_step_deg=5.0, unit_to_m=0.001):
    """segments: [(x0, y0, x1, y1, source_id)]; arcs: [(cx, cy, r, a0, a1, source_id)] (radians, CCW).
    Returns {policy, nodes, edges, dangling_edges, faces, counts}."""
    raw = []
    for x0, y0, x1, y1, sid in segments:
        if math.hypot(x1 - x0, y1 - y0) > eps:
            raw.append(((x0, y0), (x1, y1), sid))
    for cx, cy, r, a0, a1, sid in arcs:
        pts = discretise_arc(cx, cy, r, a0, a1, arc_step_deg)
        for p, q in zip(pts, pts[1:]):
            if math.hypot(q[0] - p[0], q[1] - p[1]) > eps:
                raw.append((p, q, sid))
    nodes = _Nodes(eps)
    # snap endpoints first so every split point refers to merged nodes
    snapped = [(nodes.pts[nodes.get(a)], nodes.pts[nodes.get(b)], sid) for a, b, sid in raw]
    snapped = [(a, b, sid) for a, b, sid in snapped if a != b]
    # spatial grid of segment bboxes
    cell = max(eps * 200.0, 500.0)
    grid = defaultdict(list)
    for i, (a, b, _) in enumerate(snapped):
        for gx in range(int(math.floor(min(a[0], b[0]) / cell)), int(math.floor(max(a[0], b[0]) / cell)) + 1):
            for gy in range(int(math.floor(min(a[1], b[1]) / cell)), int(math.floor(max(a[1], b[1]) / cell)) + 1):
                grid[(gx, gy)].append(i)
    cuts = defaultdict(list)
    seen_pairs = set()
    for idxs in grid.values():
        for ii in range(len(idxs)):
            i = idxs[ii]
            a, b, _ = snapped[i]
            for jj in range(ii + 1, len(idxs)):
                j = idxs[jj]
                if (i, j) in seen_pairs:
                    continue
                seen_pairs.add((i, j))
                c, d, _ = snapped[j]
                if max(a[0], b[0]) + eps < min(c[0], d[0]) or max(c[0], d[0]) + eps < min(a[0], b[0]) or \
                        max(a[1], b[1]) + eps < min(c[1], d[1]) or max(c[1], d[1]) + eps < min(a[1], b[1]):
                    continue
                p = _intersect(a, b, c, d)
                if p is not None:
                    cuts[i].append(p)
                    cuts[j].append(p)
                # T-junctions / collinear overlaps: an endpoint of one lying on the other
                for q in (c, d):
                    dq, t = _dist_point_seg(q, a, b)
                    if dq <= eps and 0.0 < t < 1.0:
                        cuts[i].append(q)
                for q in (a, b):
                    dq, t = _dist_point_seg(q, c, d)
                    if dq <= eps and 0.0 < t < 1.0:
                        cuts[j].append(q)
    edges = {}
    for i, (a, b, sid) in enumerate(snapped):
        pts = [(0.0, a), (1.0, b)] + [(_param(a, b, p), p) for p in cuts.get(i, [])]
        pts.sort(key=lambda z: z[0])
        ids = []
        for _, p in pts:
            n = nodes.get(p)
            if not ids or ids[-1] != n:
                ids.append(n)
        for u, v in zip(ids, ids[1:]):
            if u == v:
                continue
            key = (min(u, v), max(u, v))
            edges.setdefault(key, set()).add(sid)
    # dangling peel
    adj = defaultdict(set)
    for u, v in edges:
        adj[u].add(v)
        adj[v].add(u)
    dangling = []
    stack = sorted(n for n in adj if len(adj[n]) == 1)
    while stack:
        n = stack.pop()
        if len(adj[n]) != 1:
            continue
        m = next(iter(adj[n]))
        key = (min(n, m), max(n, m))
        dangling.append({"edge": key, "sources": sorted(edges[key]),
                         "length": math.dist(nodes.pts[n], nodes.pts[m])})
        adj[n].discard(m)
        adj[m].discard(n)
        if len(adj[m]) == 1:
            stack.append(m)
    live = {k: v for k, v in edges.items() if k[1] in adj[k[0]]}
    # half-edge walk
    P = nodes.pts
    out = defaultdict(list)
    for u, v in live:
        out[u].append(v)
        out[v].append(u)
    order = {}
    for u, vs in out.items():
        vs.sort(key=lambda v: math.atan2(P[v][1] - P[u][1], P[v][0] - P[u][0]))
        order[u] = {v: k for k, v in enumerate(vs)}
    used = set()
    cycles = []
    for u in sorted(out):
        for v in out[u]:
            if (u, v) in used:
                continue
            cyc = []
            a, b = u, v
            while (a, b) not in used:
                used.add((a, b))
                cyc.append((a, b))
                vs = out[b]
                k = order[b][a]
                c = vs[(k - 1) % len(vs)]                # next edge clockwise from the reversed half-edge
                a, b = b, c
            cycles.append(cyc)
    faces, outers = [], []
    for cyc in cycles:
        ring = [P[a] for a, _ in cyc]
        A = signed_area(ring)
        srcs = set()
        for a, b in cyc:
            srcs |= live[(min(a, b), max(a, b))]
        rec = {"ring": ring, "signed_area": A, "sources": sorted(srcs),
               "perimeter": sum(math.dist(P[a], P[b]) for a, b in cyc)}
        (faces if A > 0 else outers).append(rec)
    # nesting: every outer cycle (negative) of a component is a hole of the smallest face containing it,
    # unless it is the outer boundary of that same face's component (same ring reversed)
    face_rings = [f["ring"] for f in faces]
    for f in faces:
        f["holes"] = []
    for o in outers:
        ring = o["ring"]
        p = interior_point(list(reversed(ring)))
        best = None
        for k, f in enumerate(faces):
            if abs(abs(f["signed_area"]) - abs(o["signed_area"])) < 1e-6 * max(1.0, abs(f["signed_area"])) and \
                    sorted(map(tuple, f["ring"])) == sorted(map(tuple, ring)):
                continue
            if abs(f["signed_area"]) <= abs(o["signed_area"]):
                continue
            if point_in_ring(p, face_rings[k]):
                if best is None or faces[best]["signed_area"] > f["signed_area"]:
                    best = k
        if best is not None:
            faces[best]["holes"].append({"ring": ring, "area": -o["signed_area"], "sources": o["sources"]})
    res = []
    for f in faces:
        ring = f["ring"]
        A = f["signed_area"] - sum(h["area"] for h in f["holes"])
        cx = sum(p[0] for p in ring) / len(ring)
        cy = sum(p[1] for p in ring) / len(ring)
        key = hashlib.sha256(repr(sorted((round(x, 1), round(y, 1)) for x, y in ring)).encode()).hexdigest()[:16]
        res.append({"face_id": f"RB-{key}", "ring": [(round(x, 3), round(y, 3)) for x, y in ring],
                    "holes": [[(round(x, 3), round(y, 3)) for x, y in h["ring"]] for h in f["holes"]],
                    "gross_area_m2": round(f["signed_area"] * unit_to_m ** 2, 6),
                    "net_area_m2": round(A * unit_to_m ** 2, 6),
                    "perimeter_m": round(f["perimeter"] * unit_to_m, 6), "vertex_centroid": (round(cx, 3), round(cy, 3)),
                    "interior_point": interior_point(ring), "boundary_sources": f["sources"]})
    res.sort(key=lambda r: r["face_id"])
    return {"policy": POLICY_ID, "eps": eps, "nodes": len(P), "edges": len(edges), "live_edges": len(live),
            "dangling_edges": dangling, "faces": res,
            "counts": {"input_segments": len(raw), "faces": len(res), "component_outers": len(outers),
                       "dangling": len(dangling),
                       "dangling_length_m": round(sum(d["length"] for d in dangling) * unit_to_m, 6)}}
