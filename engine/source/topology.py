"""ROOM / SPACE TOPOLOGY (R8.8): certified planar sites from positively admitted boundary geometry.

PHYSICAL_GEOMETRY  ->  TOPOLOGICAL_SITES  ->  (later) TRADE_MEASUREMENT_REGIONS  ->  QUANTITIES

Input
    BoundaryItem   an admitted curve (SEGMENT / ARC / CIRCLE) with its SOURCE identity and role; opening
                   closures are BoundaryItems too, derived from a proven opening (role OPENING_BOUNDARY)
    Probe          any other part (furniture, unknown, stair, ...) - located, never a boundary
    LabelText      a visible room text with its label OCCURRENCE (the source insert that places it, or the text)

Build (no axis predicates, no rasters, no sampling)
    1  noding: exact pairwise intersections (segment/segment, segment/arc, arc/arc) and end-point-on-curve tests
       within eps; every curve is split at its nodes
    2  nodes: split points within eps are ONE topological node (union-find); node position = cluster mean, used
       for topology only - source coordinates are not rewritten
    3  planar half-edge graph; coincident edges between the same nodes are merged (their source ids united)
    4  faces by the left-face walk; signed area exact for arcs (chord polygon + circular segments)
    5  holes: the outer cycle of a nested component is subtracted from the innermost face containing it
Sites
    every bounded face is a site. site_id = digest(revision, region, sorted boundary SOURCE identities) - not its
    name, not its coordinates. A room name is an attribute (its label occurrences).
Certificate
    the build is repeated at eps_r (topology_policy). A site is CERTIFIED only if the eps_r build contains the same
    site (same id, area within eps_r x perimeter); otherwise TOLERANCE_SENSITIVE. A site found ONLY in the eps_r
    build is a SITE_ONLY_IN_AUTHORED_BUILD finding (it is never measured: its labels lie outside every site).
Labels
    each label text is located exactly (point in face, arcs included). A site holding more than one label
    OCCURRENCE is MULTIPLE_SEMANTIC_LABELS (never merged by rule: no wet-wins / first / largest / alphabetical);
    a label within eps_r of its site boundary is LABEL_ON_BOUNDARY; one occurrence split over two sites is
    LABEL_OCCURRENCE_SPLIT. No nearest-label fallback exists.
Blocking
    a probe whose role blocks topology (unknown physical, unsupported boundary curve) blocks every site it touches
    (exactly: its pieces between boundary crossings are located); an opening whose closure was not established
    blocks every site its symbol touches.

Project-agnostic; stdlib only.
"""

from __future__ import annotations

import hashlib
import math
from collections import defaultdict
from dataclasses import dataclass, field
from functools import cmp_to_key

from . import region_membership as RM
from . import topology_policy as TP

TWO_PI = 2.0 * math.pi

# site issues (any issue -> not certified)
TOLERANCE_SENSITIVE = "TOLERANCE_SENSITIVE"
MULTIPLE_SEMANTIC_LABELS = "MULTIPLE_SEMANTIC_LABELS"
LABEL_ON_BOUNDARY = "LABEL_ON_BOUNDARY"
LABEL_OCCURRENCE_SPLIT = "LABEL_OCCURRENCE_SPLIT"
TOPOLOGY_ROLE_UNRESOLVED = "TOPOLOGY_ROLE_UNRESOLVED"
OPENING_CLOSURE_UNRESOLVED = "OPENING_CLOSURE_UNRESOLVED"
ZERO_WIDTH_SLIVER = "ZERO_WIDTH_SLIVER"
NODE_CLUSTER_CHAIN = "NODE_CLUSTER_CHAIN"
SITE_ID_COLLISION = "SITE_ID_COLLISION"
UNIT_UNRESOLVED = "UNIT_UNRESOLVED"
SITE_ONLY_IN_AUTHORED_BUILD = "SITE_ONLY_IN_AUTHORED_BUILD"
NOISE_NEAR_EPS_N = "NOISE_NEAR_EPS_N"
CERTIFIED = "CERTIFIED"
REVIEW_REQUIRED = "REVIEW_REQUIRED"

OPENING_SITE = "OPENING_SITE"
SLIVER = "SLIVER"
LABELLED = "LABELLED_SITE"
UNLABELLED = "UNLABELLED_SITE"


@dataclass(frozen=True)
class BoundaryItem:
    source_id: str
    kind: str                      # SEGMENT (x1, y1, x2, y2) | ARC (cx, cy, r, a0, a1) CCW | CIRCLE (cx, cy, r)
    geometry: tuple
    role: str
    derived_from: tuple = ()


@dataclass(frozen=True)
class Probe:
    source_id: str
    kind: str                      # SEGMENT | ARC | CIRCLE | ELLIPTICAL_ARC
    geometry: tuple
    role: str
    occurrence: str | None = None


@dataclass(frozen=True)
class LabelText:
    text_id: str
    occurrence: str                # the label OCCURRENCE (insert handle, or the text itself)
    value: str
    x: float
    y: float


# ====================================================================== primitives
class _Prim:
    __slots__ = ("i", "item", "kind", "a", "b", "c", "r", "a0", "sw", "bbox")

    def __init__(self, i, item):
        self.i, self.item = i, item
        g = item.geometry
        if item.kind == "SEGMENT":
            self.kind, self.a, self.b = "S", (g[0], g[1]), (g[2], g[3])
            self.bbox = (min(g[0], g[2]), min(g[1], g[3]), max(g[0], g[2]), max(g[1], g[3]))
        else:
            self.kind = "A"
            if item.kind == "CIRCLE":
                cx, cy, r = g
                a0, sw = 0.0, TWO_PI
            else:
                cx, cy, r, a0, a1 = g
                sw = (a1 - a0) % TWO_PI or TWO_PI
            self.c, self.r, self.a0, self.sw = (cx, cy), r, a0 % TWO_PI, sw
            self.bbox = RM.exact_bbox("ARC", (cx, cy, r, a0, a0 + sw)) if sw < TWO_PI else (cx - r, cy - r, cx + r, cy + r)

    @property
    def full(self):
        return self.kind == "A" and self.sw >= TWO_PI

    def point(self, t):
        if self.kind == "S":
            return (self.a[0] + t * (self.b[0] - self.a[0]), self.a[1] + t * (self.b[1] - self.a[1]))
        ang = self.a0 + t
        return (self.c[0] + self.r * math.cos(ang), self.c[1] + self.r * math.sin(ang))

    def end_params(self):
        return (0.0, 1.0) if self.kind == "S" else ((0.0, math.pi) if self.full else (0.0, self.sw))


def _d(p, q):
    return math.hypot(p[0] - q[0], p[1] - q[1])


def _proj_seg(pt, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    L2 = dx * dx + dy * dy
    if L2 == 0.0:
        return 0.0, _d(pt, a)
    t = max(0.0, min(1.0, ((pt[0] - a[0]) * dx + (pt[1] - a[1]) * dy) / L2))
    return t, _d(pt, (a[0] + t * dx, a[1] + t * dy))


def _arc_param(prim, pt, eps):
    """Sweep parameter of the point's angle on the arc, or None if outside the sweep (tolerance eps / r)."""
    ang = math.atan2(pt[1] - prim.c[1], pt[0] - prim.c[0])
    s = (ang - prim.a0) % TWO_PI
    tol = eps / prim.r if prim.r > 0 else 0.0
    if prim.full:
        return s
    if s <= prim.sw + tol:
        return min(s, prim.sw)
    if s >= TWO_PI - tol:
        return 0.0
    return None


def _near_on_arc(prim, pt, eps):
    if abs(_d(pt, prim.c) - prim.r) > eps:
        return None
    return _arc_param(prim, pt, eps)


def _side(p, a, b):
    """Signed distance of p from the line a-b."""
    L = _d(a, b)
    return 0.0 if L == 0.0 else ((b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0])) / L


def _decisive_crossing(a, b, c, d, eps):
    """A proper crossing is decided only when each segment's ends lie on opposite sides of the other's line by MORE
    than eps. An end within eps of the other line is a touch (handled by the end-point tests), never a crossing
    computed from a near-zero determinant: near-collinear overlap cannot produce a crossing that depends on noise."""
    s1, s2 = _side(c, a, b), _side(d, a, b)
    s3, s4 = _side(a, c, d), _side(b, c, d)
    return (abs(s1) > eps and abs(s2) > eps and abs(s3) > eps and abs(s4) > eps
            and (s1 > 0) != (s2 > 0) and (s3 > 0) != (s4 > 0))


def _pair_splits(P, Q, eps):
    """[(prim, param, point)] split points of a pair (both directions)."""
    out = []
    if P.kind == "S" and Q.kind == "S":
        for X, Y in ((P, Q), (Q, P)):
            for pt, tx in ((X.a, 0.0), (X.b, 1.0)):
                u, dist = _proj_seg(pt, Y.a, Y.b)
                if dist <= eps:
                    out.append((Y, u, pt))
                    out.append((X, tx, pt))
        a, b, c, d = P.a, P.b, Q.a, Q.b
        r = (b[0] - a[0], b[1] - a[1])
        s = (d[0] - c[0], d[1] - c[1])
        den = r[0] * s[1] - r[1] * s[0]
        if den != 0.0 and _decisive_crossing(a, b, c, d, eps):
            qp = (c[0] - a[0], c[1] - a[1])
            t = (qp[0] * s[1] - qp[1] * s[0]) / den
            u = (qp[0] * r[1] - qp[1] * r[0]) / den
            if 0.0 < t < 1.0 and 0.0 < u < 1.0:
                pt = (a[0] + t * r[0], a[1] + t * r[1])
                if min(_d(pt, a), _d(pt, b), _d(pt, c), _d(pt, d)) > eps:
                    out.append((P, t, pt))
                    out.append((Q, u, pt))
        return out
    if P.kind == "A" and Q.kind == "S":
        P, Q = Q, P
    if P.kind == "S" and Q.kind == "A":
        S_, A_ = P, Q
        for pt, ts in ((S_.a, 0.0), (S_.b, 1.0)):
            s = _near_on_arc(A_, pt, eps)
            if s is not None:
                out.append((A_, s, pt))
                out.append((S_, ts, pt))
        if not A_.full:
            for ta in (0.0, A_.sw):
                pt = A_.point(ta)
                u, dist = _proj_seg(pt, S_.a, S_.b)
                if dist <= eps:
                    out.append((S_, u, pt))
                    out.append((A_, ta, pt))
        a, b, c, r = S_.a, S_.b, A_.c, A_.r
        dx, dy = b[0] - a[0], b[1] - a[1]
        fx, fy = a[0] - c[0], a[1] - c[1]
        A2 = dx * dx + dy * dy
        if A2 == 0.0:
            return out
        B2 = 2 * (fx * dx + fy * dy)
        C2 = fx * fx + fy * fy - r * r
        disc = B2 * B2 - 4 * A2 * C2
        roots = []
        if disc >= 0.0:
            sq = math.sqrt(disc)
            roots = [(-B2 - sq) / (2 * A2), (-B2 + sq) / (2 * A2)]
        else:
            t0 = -B2 / (2 * A2)
            foot = (a[0] + t0 * dx, a[1] + t0 * dy)
            if abs(_d(foot, c) - r) <= eps:                      # tangent within eps
                roots = [t0]
        for t in roots:
            if 0.0 < t < 1.0:
                pt = (a[0] + t * dx, a[1] + t * dy)
                s = _arc_param(A_, pt, eps)
                ends = [S_.a, S_.b] + ([] if A_.full else [A_.point(0.0), A_.point(A_.sw)])
                if s is not None and min(_d(pt, e) for e in ends) > eps:
                    out.append((S_, t, pt))
                    out.append((A_, s, pt))
        return out
    # arc / arc
    for X, Y in ((P, Q), (Q, P)):
        if not X.full:
            for tx in (0.0, X.sw):
                pt = X.point(tx)
                s = _near_on_arc(Y, pt, eps)
                if s is not None:
                    out.append((Y, s, pt))
                    out.append((X, tx, pt))
    c1, r1, c2, r2 = P.c, P.r, Q.c, Q.r
    dd = _d(c1, c2)
    if dd == 0.0:
        return out
    pts = []
    if abs(dd - (r1 + r2)) <= eps or abs(dd - abs(r1 - r2)) <= eps:
        ux, uy = (c2[0] - c1[0]) / dd, (c2[1] - c1[1]) / dd
        sgn = 1.0 if abs(dd - (r1 + r2)) <= eps or r1 >= r2 else -1.0
        pts = [(c1[0] + sgn * ux * r1, c1[1] + sgn * uy * r1)]
    elif abs(r1 - r2) < dd < r1 + r2:
        a = (r1 * r1 - r2 * r2 + dd * dd) / (2 * dd)
        h = math.sqrt(max(0.0, r1 * r1 - a * a))
        mx, my = c1[0] + a * (c2[0] - c1[0]) / dd, c1[1] + a * (c2[1] - c1[1]) / dd
        ox, oy = -(c2[1] - c1[1]) * h / dd, (c2[0] - c1[0]) * h / dd
        pts = [(mx + ox, my + oy), (mx - ox, my - oy)]
    for pt in pts:
        s1, s2 = _arc_param(P, pt, eps), _arc_param(Q, pt, eps)
        ends = ([] if P.full else [P.point(0.0), P.point(P.sw)]) + ([] if Q.full else [Q.point(0.0), Q.point(Q.sw)])
        if s1 is not None and s2 is not None and (not ends or min(_d(pt, e) for e in ends) > eps):
            out.append((P, s1, pt))
            out.append((Q, s2, pt))
    return out


def _candidate_pairs(prims, eps):
    """Sweep on x over bounding boxes expanded by eps; deterministic order."""
    order = sorted(range(len(prims)), key=lambda k: (prims[k].bbox[0], k))
    active, pairs = [], []
    for k in order:
        bx0 = prims[k].bbox[0] - eps
        active = [j for j in active if prims[j].bbox[2] + eps >= bx0]
        for j in active:
            a, b = prims[j].bbox, prims[k].bbox
            if a[1] - eps <= b[3] + eps and b[1] - eps <= a[3] + eps:
                pairs.append((min(j, k), max(j, k)))
        active.append(k)
    return sorted(pairs)


def end_distances(items, eps):
    """Distance of every curve end to every OTHER curve within eps (the node-equivalence decisions a build at eps
    makes), deterministic order. Used only to measure the noise / authored separation (topology_policy)."""
    prims = [_Prim(i, it) for i, it in enumerate(items)]
    out = []
    for j, k in _candidate_pairs(prims, eps):
        for P, Q in ((prims[j], prims[k]), (prims[k], prims[j])):
            if P.full:
                continue
            for t in P.end_params():
                pt = P.point(t)
                if Q.kind == "S":
                    d = _proj_seg(pt, Q.a, Q.b)[1]
                else:
                    s_ = _arc_param(Q, pt, eps)
                    d = abs(_d(pt, Q.c) - Q.r) if s_ is not None else \
                        min(_d(pt, Q.point(u)) for u in Q.end_params())
                if d <= eps:
                    out.append(d)
    return out


# ====================================================================== the arrangement
class _UF:
    def __init__(self, n):
        self.p = list(range(n))

    def find(self, x):
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]
            x = self.p[x]
        return x

    def union(self, a, b):
        a, b = self.find(a), self.find(b)
        if a != b:
            self.p[max(a, b)] = min(a, b)


@dataclass
class Arrangement:
    eps: float
    nodes: list = field(default_factory=list)            # positions
    edges: list = field(default_factory=list)            # dicts
    faces: list = field(default_factory=list)            # dicts
    findings: list = field(default_factory=list)


def _cluster(points, eps):
    uf = _UF(len(points))
    grid = defaultdict(list)
    cell = eps if eps > 0 else 1e-12
    for k, (x, y) in enumerate(points):
        gx, gy = math.floor(x / cell), math.floor(y / cell)
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for j in grid.get((gx + dx, gy + dy), ()):
                    if _d(points[j], (x, y)) <= eps:
                        uf.union(j, k)
        grid[(gx, gy)].append(k)
    roots = {}
    members = defaultdict(list)
    for k in range(len(points)):
        members[uf.find(k)].append(k)
    nodes, chains = [], []
    for root in sorted(members):
        ks = members[root]
        pos = (sum(points[k][0] for k in ks) / len(ks), sum(points[k][1] for k in ks) / len(ks))
        diam = max((_d(points[a], points[b]) for a in ks for b in ks), default=0.0) if len(ks) <= 64 else \
            2 * max(_d(points[a], pos) for a in ks)
        if diam > 2 * eps:
            chains.append({"node": len(nodes), "points": len(ks), "diameter": diam})
        for k in ks:
            roots[k] = len(nodes)
        nodes.append(pos)
    return roots, nodes, chains


def build(items, eps) -> Arrangement:
    prims = [_Prim(i, it) for i, it in enumerate(items)]
    splits = defaultdict(list)                            # prim index -> [(param, point index)]
    points = []

    def add(prim, t, pt):
        points.append(pt)
        splits[prim.i].append((t, len(points) - 1))
    for pr in prims:
        for t in pr.end_params():
            add(pr, t, pr.point(t))
        if pr.full:
            pass
    for j, k in _candidate_pairs(prims, eps):
        for prim, t, pt in _pair_splits(prims[j], prims[k], eps):
            add(prim, t, pt)
    node_of, nodes, chains = _cluster(points, eps)
    arr = Arrangement(eps, nodes)
    for ch in chains:
        arr.findings.append({"code": NODE_CLUSTER_CHAIN, **ch})
    # ---- edges
    raw = []
    for pr in prims:
        ss = sorted(splits[pr.i], key=lambda tp: (tp[0], tp[1]))
        seq = []
        for t, pidx in ss:
            n = node_of[pidx]
            if seq and seq[-1][1] == n:
                continue
            seq.append((t, n))
        if pr.full:                                     # close the circle
            seq.append((TWO_PI, seq[0][1]))
        for (t0, n0), (t1, n1) in zip(seq, seq[1:]):
            if t1 <= t0:
                continue
            if n0 == n1:
                if pr.kind == "S" or (t1 - t0) * pr.r <= 2 * eps:
                    continue
                # an arc returning to its start node: split at its middle so the graph is simple
                tm = (t0 + t1) / 2
                arr.nodes.append(pr.point(tm))
                nm = len(arr.nodes) - 1
                raw.append((pr, t0, tm, n0, nm))
                raw.append((pr, tm, t1, nm, n1))
                continue
            raw.append((pr, t0, t1, n0, n1))
    # ---- merge coincident edges (same nodes, same geometry); the source ids are united
    groups = defaultdict(list)
    for pr, t0, t1, n0, n1 in raw:
        groups[(min(n0, n1), max(n0, n1))].append((pr, t0, t1, n0, n1))
    for key in sorted(groups):
        uniq = []
        for pr, t0, t1, n0, n1 in groups[key]:
            mid = pr.point((t0 + t1) / 2)
            for u in uniq:
                if _d(u["mid"], mid) <= 2 * eps and (u["kind"] == "S") == (pr.kind == "S"):
                    u["sources"].add(pr.item.source_id)
                    u["roles"].add(pr.item.role)
                    break
            else:
                uniq.append({"kind": pr.kind, "n0": n0, "n1": n1, "prim": pr, "t0": t0, "t1": t1, "mid": mid,
                             "sources": {pr.item.source_id}, "roles": {pr.item.role}})
        arr.edges.extend(uniq)
    _faces(arr)
    return arr


# ====================================================================== faces
def _half_angle(arr, e, forward):
    """(tangent angle leaving the start node, signed curvature) of an edge traversed forward / backward."""
    if e["kind"] == "S":
        p, q = (arr.nodes[e["n0"]], arr.nodes[e["n1"]]) if forward else (arr.nodes[e["n1"]], arr.nodes[e["n0"]])
        return math.atan2(q[1] - p[1], q[0] - p[0]) % TWO_PI, 0.0
    pr = e["prim"]
    if forward:
        ang = pr.a0 + e["t0"] + math.pi / 2
        return ang % TWO_PI, 1.0 / pr.r
    ang = pr.a0 + e["t1"] - math.pi / 2
    return ang % TWO_PI, -1.0 / pr.r


def _sweep(e, forward):
    s = e["t1"] - e["t0"]
    return s if forward else -s


def _faces(arr):
    out = defaultdict(list)                     # node -> [(angle, curvature, edge idx, forward)]
    for k, e in enumerate(arr.edges):
        a, c = _half_angle(arr, e, True)
        out[e["n0"]].append((a, c, k, True))
        a, c = _half_angle(arr, e, False)
        out[e["n1"]].append((a, c, k, False))

    def cmp(x, y):
        da = x[0] - y[0]
        if abs(da) > 1e-12:
            return -1 if da < 0 else 1
        if x[1] != y[1]:
            return -1 if x[1] < y[1] else 1
        return -1 if (x[2], x[3]) < (y[2], y[3]) else 1
    order = {}
    for n in out:
        out[n].sort(key=cmp_to_key(cmp))
        for idx, h in enumerate(out[n]):
            order[(h[2], h[3])] = (n, idx)
    seen = set()
    for k in range(len(arr.edges)):
        for fw in (True, False):
            if (k, fw) in seen:
                continue
            cyc, h = [], (k, fw)
            guard = 0
            while h not in seen:
                seen.add(h)
                cyc.append(h)
                e = arr.edges[h[0]]
                v = e["n1"] if h[1] else e["n0"]
                twin = (h[0], not h[1])
                n, idx = order[twin]
                lst = out[v]
                nxt = lst[(idx - 1) % len(lst)]
                h = (nxt[2], nxt[3])
                guard += 1
                if guard > 4 * len(arr.edges) + 8:
                    break
            arr.faces.append({"cycle": cyc, "area": _cycle_area(arr, cyc)})


def _cycle_area(arr, cyc):
    a = 0.0
    for k, fw in cyc:
        e = arr.edges[k]
        p, q = (arr.nodes[e["n0"]], arr.nodes[e["n1"]]) if fw else (arr.nodes[e["n1"]], arr.nodes[e["n0"]])
        a += (p[0] * q[1] - q[0] * p[1]) / 2.0
        if e["kind"] == "A":
            s = _sweep(e, fw)
            r = e["prim"].r
            a += (r * r / 2.0) * (s - math.sin(s))
    return a


def _cycle_perimeter(arr, cyc):
    tot = 0.0
    for k, _ in cyc:
        e = arr.edges[k]
        tot += _d(arr.nodes[e["n0"]], arr.nodes[e["n1"]]) if e["kind"] == "S" else e["prim"].r * (e["t1"] - e["t0"])
    return tot


def _winding(arr, cyc, pt):
    """Winding number of the closed cycle around pt (chord polygon + exact circular-segment correction)."""
    wn = 0
    x, y = pt
    for k, fw in cyc:
        e = arr.edges[k]
        p, q = (arr.nodes[e["n0"]], arr.nodes[e["n1"]]) if fw else (arr.nodes[e["n1"]], arr.nodes[e["n0"]])
        if p[1] <= y:
            if q[1] > y and (q[0] - p[0]) * (y - p[1]) - (x - p[0]) * (q[1] - p[1]) > 0:
                wn += 1
        elif q[1] <= y and (q[0] - p[0]) * (y - p[1]) - (x - p[0]) * (q[1] - p[1]) < 0:
            wn -= 1
        if e["kind"] == "A":
            pr = e["prim"]
            if _d(pt, pr.c) < pr.r:
                m = pr.point((e["t0"] + e["t1"]) / 2)
                side_m = (q[0] - p[0]) * (m[1] - p[1]) - (m[0] - p[0]) * (q[1] - p[1])
                side_p = (q[0] - p[0]) * (y - p[1]) - (x - p[0]) * (q[1] - p[1])
                if side_m * side_p > 0:
                    wn += 1 if _sweep(e, fw) > 0 else -1
    return wn


def _dist_to_cycle(arr, cyc, pt):
    best = math.inf
    for k, _ in cyc:
        e = arr.edges[k]
        if e["kind"] == "S":
            best = min(best, _proj_seg(pt, arr.nodes[e["n0"]], arr.nodes[e["n1"]])[1])
        else:
            pr = e["prim"]
            ang = math.atan2(pt[1] - pr.c[1], pt[0] - pr.c[0])
            s = (ang - pr.a0) % TWO_PI
            if e["t0"] <= s <= e["t1"]:
                best = min(best, abs(_d(pt, pr.c) - pr.r))
            best = min(best, _d(pt, pr.point(e["t0"])), _d(pt, pr.point(e["t1"])))
    return best


def _cycle_bbox(arr, cyc):
    xs, ys = [], []
    for k, _ in cyc:
        e = arr.edges[k]
        if e["kind"] == "S":
            for n in (e["n0"], e["n1"]):
                xs.append(arr.nodes[n][0])
                ys.append(arr.nodes[n][1])
        else:
            pr = e["prim"]
            b = RM.exact_bbox("ARC", (pr.c[0], pr.c[1], pr.r, pr.a0 + e["t0"], pr.a0 + e["t1"]))
            xs += [b[0], b[2]]
            ys += [b[1], b[3]]
    return min(xs), min(ys), max(xs), max(ys)


# ====================================================================== sites
def _components(arr):
    uf = _UF(len(arr.nodes))
    for e in arr.edges:
        uf.union(e["n0"], e["n1"])
    return uf


def sites_of(arr, revision_id, region_id):
    """Bounded faces with holes subtracted; ids from boundary source identities."""
    uf = _components(arr)
    pos = [k for k, f in enumerate(arr.faces) if f["area"] > 0]
    neg = [k for k, f in enumerate(arr.faces) if f["area"] <= 0]
    comp_of_face = {k: uf.find(arr.edges[arr.faces[k]["cycle"][0][0]]["n0"]) for k in range(len(arr.faces))}
    for k in pos:
        arr.faces[k]["bbox"] = _cycle_bbox(arr, arr.faces[k]["cycle"])
    holes = defaultdict(list)
    outer_of_comp = {}
    for k in neg:
        c = comp_of_face[k]
        if c not in outer_of_comp or arr.faces[k]["area"] < arr.faces[outer_of_comp[c]]["area"]:
            outer_of_comp[c] = k
    for c, k in sorted(outer_of_comp.items()):
        e0 = arr.edges[arr.faces[k]["cycle"][0][0]]
        pt = arr.nodes[e0["n0"]]
        best = None
        for j in pos:
            if comp_of_face[j] == c:
                continue
            b = arr.faces[j]["bbox"]
            if not (b[0] <= pt[0] <= b[2] and b[1] <= pt[1] <= b[3]):
                continue
            if _winding(arr, arr.faces[j]["cycle"], pt) != 0:
                if best is None or arr.faces[j]["area"] < arr.faces[best]["area"]:
                    best = j
        if best is not None:
            holes[best].append(k)
    sites = []
    for k in pos:
        f = arr.faces[k]
        cyc = f["cycle"]
        hole_cycles = [arr.faces[h]["cycle"] for h in holes.get(k, [])]
        src = sorted({s for (ei, _) in cyc for s in arr.edges[ei]["sources"]})
        hsrc = sorted({s for hc in hole_cycles for (ei, _) in hc for s in arr.edges[ei]["sources"]})
        area = f["area"] - sum(abs(arr.faces[h]["area"]) for h in holes.get(k, []))
        per = _cycle_perimeter(arr, cyc) + sum(_cycle_perimeter(arr, hc) for hc in hole_cycles)
        sid = "SITE-" + hashlib.sha256("|".join([revision_id or "", region_id or "", "OUTER"] + src + ["HOLES"] + hsrc)
                                       .encode()).hexdigest()[:16]
        roles = defaultdict(float)
        for ei, _ in cyc:
            e = arr.edges[ei]
            ln = _d(arr.nodes[e["n0"]], arr.nodes[e["n1"]]) if e["kind"] == "S" else e["prim"].r * (e["t1"] - e["t0"])
            for r in e["roles"]:
                roles[r] += ln / len(e["roles"])
        sites.append({"site_id": sid, "face": k, "area": area, "gross_outer_area": f["area"], "perimeter": per,
                      "boundary_source_ids": src, "hole_source_ids": hsrc, "holes": len(hole_cycles),
                      "boundary_role_lengths": dict(sorted(roles.items())), "bbox": f["bbox"],
                      "cycle": cyc, "hole_cycles": hole_cycles})
    ids = defaultdict(list)
    for s in sites:
        ids[s["site_id"]].append(s)
    for sid, group in ids.items():
        if len(group) > 1:
            for n, s in enumerate(sorted(group, key=lambda z: (z["area"], z["face"]))):
                s["site_id"] = f"{sid}#{n}"
                s.setdefault("issues", []).append(SITE_ID_COLLISION)
    sites.sort(key=lambda s: s["site_id"])
    return sites


def locate(arr, sites, pt, tol):
    """(innermost site containing pt or None, [sites whose boundary is within tol of pt])."""
    inside, near = [], []
    for s in sites:
        b = s["bbox"]
        if not (b[0] - tol <= pt[0] <= b[2] + tol and b[1] - tol <= pt[1] <= b[3] + tol):
            continue
        dist = min([_dist_to_cycle(arr, s["cycle"], pt)] + [_dist_to_cycle(arr, hc, pt) for hc in s["hole_cycles"]])
        if dist <= tol:
            near.append(s["site_id"])
        if _winding(arr, s["cycle"], pt) != 0 and not any(_winding(arr, hc, pt) != 0 for hc in s["hole_cycles"]):
            inside.append(s)
    inside.sort(key=lambda s: s["area"])
    return (inside[0]["site_id"] if inside else None), near


# ====================================================================== probes (pieces between boundary crossings)
def _probe_pieces(probe, prims, eps):
    """Sample-free: split the probe at every crossing with the boundary, return one interior point per piece."""
    if probe.kind == "ELLIPTICAL_ARC":
        return None
    pp = _Prim(-1, BoundaryItem(probe.source_id, probe.kind if probe.kind != "CIRCLE" else "CIRCLE", probe.geometry,
                                probe.role))
    ts = list(pp.end_params()) + ([TWO_PI] if pp.full else [])
    for q in prims:
        b, a = q.bbox, pp.bbox
        if a[0] - eps > b[2] or b[0] - eps > a[2] or a[1] - eps > b[3] or b[1] - eps > a[3]:
            continue
        for prim, t, _pt in _pair_splits(pp, q, eps):
            if prim is pp:
                ts.append(t)
    # split parameters closer than eps along the probe are ONE split: a zero-length piece at a shared end point is
    # numerical, and must not let the probe "touch" a site it only meets at a point (route-noise robustness)
    scale = _d(pp.a, pp.b) if pp.kind == "S" else pp.r
    merged = []
    for t in sorted(set(ts)):
        if merged and (t - merged[-1]) * scale <= eps:
            continue
        merged.append(t)
    end = ts and max(ts)
    if merged and end is not None and merged[-1] != end and (end - merged[-1]) * scale <= eps:
        merged[-1] = end
    return [pp.point((t0 + t1) / 2) for t0, t1 in zip(merged, merged[1:]) if t1 > t0] or [pp.point(merged[0])]


def touched_sites(arr, sites, items, probe, eps, tol):
    """Every site the probe touches (its interior pieces located; a piece on a boundary touches the sites there).
    An elliptical probe is treated conservatively: every site whose box meets the ellipse's exact box."""
    if probe.kind == "ELLIPTICAL_ARC":
        bb = RM.exact_bbox("ELLIPTICAL_ARC", probe.geometry)
        return sorted(s["site_id"] for s in sites if bb and not (bb[0] > s["bbox"][2] or s["bbox"][0] > bb[2]
                                                                     or bb[1] > s["bbox"][3] or s["bbox"][1] > bb[3]))
    prims = [_Prim(i, it) for i, it in enumerate(items)]
    hit = set()
    for pt in _probe_pieces(probe, prims, eps):
        sid, near = locate(arr, sites, pt, tol)
        if sid:
            hit.add(sid)
        hit.update(near)
    return sorted(hit)


# ====================================================================== opening closures
def _ray_hit(o, d, items, eps, max_s, exclude=()):
    """First admitted boundary hit by the ray o + s d (-eps <= s <= max_s): (s, point, item) or None. Among hits at
    the same distance (within eps) a CROSSING curve is preferred to one collinear with the ray (the jamb cap, not
    the wall face line continuing past it)."""
    hits = []
    for it in items:
        if it.source_id in exclude:
            continue
        if it.kind == "SEGMENT":
            a, b = (it.geometry[0], it.geometry[1]), (it.geometry[2], it.geometry[3])
            r = (b[0] - a[0], b[1] - a[1])
            L = math.hypot(*r)
            if L == 0.0:
                continue
            den = d[0] * r[1] - d[1] * r[0]
            ao = (a[0] - o[0], a[1] - o[1])
            if abs(den) <= 1e-12 * L:
                dist = abs(ao[0] * d[1] - ao[1] * d[0])          # parallel: collinear within eps -> nearest end ahead
                if dist > eps:
                    continue
                cands = [(ao[0] * d[0] + ao[1] * d[1], a), ((b[0] - o[0]) * d[0] + (b[1] - o[1]) * d[1], b)]
                cands = [c for c in cands if -eps <= c[0] <= max_s]
                if cands:
                    sv, pt = min(cands)
                    hits.append((sv, 1, pt, it))
                continue
            sv = (ao[0] * r[1] - ao[1] * r[0]) / den
            t = (ao[0] * d[1] - ao[1] * d[0]) / den
            if -eps / L <= t <= 1 + eps / L and -eps <= sv <= max_s:
                hits.append((sv, 0, (o[0] + sv * d[0], o[1] + sv * d[1]), it))
        else:
            pr = _Prim(0, it)
            fx, fy = o[0] - pr.c[0], o[1] - pr.c[1]
            B2 = 2 * (fx * d[0] + fy * d[1])
            C2 = fx * fx + fy * fy - pr.r * pr.r
            disc = B2 * B2 - 4 * C2
            if disc < 0:
                continue
            for sv in sorted(((-B2 - math.sqrt(disc)) / 2, (-B2 + math.sqrt(disc)) / 2)):
                if -eps <= sv <= max_s:
                    pt = (o[0] + sv * d[0], o[1] + sv * d[1])
                    if _arc_param(pr, pt, eps) is not None:
                        hits.append((sv, 0, pt, it))
                        break
    if not hits:
        return None
    s0 = min(h[0] for h in hits)
    tied = sorted((h for h in hits if h[0] <= s0 + eps), key=lambda h: (h[1], h[0], h[3].source_id))
    sv, _, pt, it = tied[0]
    return sv, pt, it


def _other_end(item, pt, eps):
    if item.kind != "SEGMENT":
        return None
    a, b = (item.geometry[0], item.geometry[1]), (item.geometry[2], item.geometry[3])
    if _d(a, pt) <= eps:
        return b
    if _d(b, pt) <= eps:
        return a
    return None


def opening_closures(doors: dict, items, eps, jamb_ratio=TP.JAMB_ALLOWANCE_RATIO):
    """Virtual closures for proven doors. For each door (hinge, radius, two swing ends), each end is tried as the
    closed-leaf end: a ray forward from it and a ray backward from the hinge must both meet an admitted boundary
    within jamb_ratio x radius. Exactly one hypothesis must succeed (else OPENING_CLOSURE_UNRESOLVED).
    Closure A runs between the two hits (along the closed leaf). When both hits land on end points of straight
    jamb caps whose far ends are parallel to A at A's length, closure B joins those far ends (the other wall
    face): the opening between them becomes its own OPENING_SITE and neither room absorbs it."""
    closures, status = [], {}
    for occ in sorted(doors):
        sig = doors[occ]
        c, r = sig["hinge"], sig["radius"]
        reach = jamb_ratio * r
        ok = []
        for end in sig["ends"]:
            L = _d(end, c)
            if L == 0:
                continue
            d = ((end[0] - c[0]) / L, (end[1] - c[1]) / L)
            f = _ray_hit(end, d, items, eps, reach)
            b = _ray_hit(c, (-d[0], -d[1]), items, eps, reach)
            if f is not None and b is not None:
                ok.append((end, f, b))
        if len(ok) != 1:
            status[occ] = {"state": OPENING_CLOSURE_UNRESOLVED,
                           "why": "no leaf hypothesis lands on admitted walls at both ends" if not ok
                           else "both leaf hypotheses land on admitted walls"}
            continue
        end, (s1, h1, it1), (s2, h2, it2) = ok[0]
        a_id = f"CLOSURE|{occ}|A"
        closures.append(BoundaryItem(a_id, "SEGMENT", (h2[0], h2[1], h1[0], h1[1]), "OPENING_BOUNDARY",
                                     (sig["swing_part"], it1.source_id, it2.source_id)))
        rec = {"state": "CLOSED", "closure_a": a_id, "hits": [it2.source_id, it1.source_id],
               "reach": [round(s2, 9), round(s1, 9)], "width": _d(h1, h2), "closure_b": None}
        f1, f2 = _other_end(it1, h1, eps), _other_end(it2, h2, eps)
        if f1 is not None and f2 is not None:
            A = (h1[0] - h2[0], h1[1] - h2[1])
            B = (f1[0] - f2[0], f1[1] - f2[1])
            la, lb = math.hypot(*A), math.hypot(*B)
            if la > 0 and lb > 0 and abs(A[0] * B[1] - A[1] * B[0]) <= eps * max(la, lb) and abs(la - lb) <= 2 * eps \
                    and (A[0] * B[0] + A[1] * B[1]) > 0:
                b_id = f"CLOSURE|{occ}|B"
                closures.append(BoundaryItem(b_id, "SEGMENT", (f2[0], f2[1], f1[0], f1[1]), "OPENING_BOUNDARY",
                                             (sig["swing_part"], it1.source_id, it2.source_id)))
                rec["closure_b"] = b_id
        status[occ] = rec
    return closures, status


def glazing_closures(items, eps_n, eps_r):
    """Wall-face closures across GLAZED openings. A glazed opening is proven by structure, not by a layer alone:
    a glazing line G, and on EACH side of it the nearest parallel wall-face line (wall / column role) with a GAP
    whose ends align on both faces (within eps_r) and which G spans; between the two face lines, over the gap,
    nothing but glazing is drawn. Both faces are then closed between their own jamb end points (source points, not
    moved), so the room ends at its wall face and the reveal becomes an OPENING_SITE. An open passage (no glazing,
    no proven door) is never closed."""
    faces = [it for it in items if it.kind == "SEGMENT" and it.role in ("TOPOLOGY_BOUNDARY", "STRUCTURAL_OBSTACLE")]
    glaz = [it for it in items if it.kind == "SEGMENT" and it.role == "GLAZING_BOUNDARY"]
    out, seen, status = [], {}, {}
    for G in sorted(glaz, key=lambda z: z.source_id):
        a, b = (G.geometry[0], G.geometry[1]), (G.geometry[2], G.geometry[3])
        L = _d(a, b)
        if L == 0:
            continue
        u = ((b[0] - a[0]) / L, (b[1] - a[1]) / L)
        n = (-u[1], u[0])
        proj = lambda p: ((p[0] - a[0]) * u[0] + (p[1] - a[1]) * u[1], (p[0] - a[0]) * n[0] + (p[1] - a[1]) * n[1])
        lines = []                                            # [offset, [(t0, t1, item, pt0, pt1)]]
        for F in faces:
            p0, p1 = (F.geometry[0], F.geometry[1]), (F.geometry[2], F.geometry[3])
            (t0, o0), (t1, o1) = proj(p0), proj(p1)
            if abs(o0 - o1) > eps_r:                          # not parallel to G within the authored band
                continue
            o = (o0 + o1) / 2
            if t0 > t1:
                t0, t1, p0, p1 = t1, t0, p1, p0
            for ln in lines:
                if abs(ln[0] - o) <= eps_n:
                    ln[1].append((t0, t1, F, p0, p1))
                    break
            else:
                lines.append([o, [(t0, t1, F, p0, p1)]])
        cands = []
        for o, segs in lines:
            segs.sort(key=lambda z: (z[0], z[1]))
            reach, last = None, None
            for t0, t1, F, p0, p1 in segs:
                if reach is not None and t0 > reach + eps_n:
                    lo, hi = reach, t0
                    if lo <= 0.0 + eps_r and hi >= L - eps_r or (0.0 <= lo + eps_r and L >= hi - eps_r and
                                                                  lo >= -eps_r and hi <= L + eps_r):
                        if -eps_r <= lo and hi <= L + eps_r:      # G spans the whole gap
                            cands.append({"offset": o, "lo": lo, "hi": hi, "p_lo": last[1], "p_hi": p0,
                                          "f_lo": last[0], "f_hi": F.source_id})
                if reach is None or t1 > reach:
                    reach, last = t1, (F.source_id, p1)
        neg = sorted((c for c in cands if c["offset"] < -eps_r), key=lambda c: -c["offset"])
        pos = sorted((c for c in cands if c["offset"] > eps_r), key=lambda c: c["offset"])
        zero = [c for c in cands if abs(c["offset"]) <= eps_r]
        sides = [x for x in ((zero[0] if zero else None), (neg[0] if neg else None), (pos[0] if pos else None)) if x]
        if zero:
            other = [c for c in (neg[:1] + pos[:1])]
            pair = (zero[0], other[0]) if len(other) == 1 else None
        else:
            pair = (neg[0], pos[0]) if neg and pos else None
        if pair is None:
            status[G.source_id] = {"state": "NO_ALIGNED_FACE_PAIR", "faces_found": len(sides)}
            continue
        c1, c2 = pair
        if abs(c1["lo"] - c2["lo"]) > eps_r or abs(c1["hi"] - c2["hi"]) > eps_r:
            status[G.source_id] = {"state": "JAMBS_NOT_ALIGNED"}
            continue
        lo_o, hi_o = sorted((c1["offset"], c2["offset"]))
        lo_t, hi_t = max(c1["lo"], c2["lo"]), min(c1["hi"], c2["hi"])
        intruder = False
        for F in faces:
            p0, p1 = (F.geometry[0], F.geometry[1]), (F.geometry[2], F.geometry[3])
            (t0, o0), (t1, o1) = proj(p0), proj(p1)
            if min(o0, o1) > lo_o + eps_r and max(o0, o1) < hi_o - eps_r and max(t0, t1) > lo_t + eps_r \
                    and min(t0, t1) < hi_t - eps_r:
                intruder = True
                break
        if intruder:
            status[G.source_id] = {"state": "ZONE_NOT_CLEAR"}
            continue
        key = tuple(sorted((round(c1["offset"] / eps_r), round(c2["offset"] / eps_r)))) + \
            (round(lo_t / eps_r), round(hi_t / eps_r))
        oid = seen.get(key)
        if oid is None:
            oid = f"GLAZED|{G.source_id}"
            seen[key] = oid
            for tag, c in (("F1", c1), ("F2", c2)):
                out.append(BoundaryItem(f"CLOSURE|{oid}|{tag}", "SEGMENT",
                                        (c["p_lo"][0], c["p_lo"][1], c["p_hi"][0], c["p_hi"][1]), "OPENING_BOUNDARY",
                                        (G.source_id, c["f_lo"], c["f_hi"])))
        status[G.source_id] = {"state": "CLOSED", "opening": oid}
    openings = defaultdict(list)
    for it in out:
        openings[it.source_id.split("|")[1] + "|" + it.source_id.split("|")[2]].append(it.source_id)
    return out, status, dict(openings)


# ====================================================================== the analysis
def analyse(items, probes, labels, *, revision_id, region_id, unit_native_to_mm, max_abs_coordinate=None,
            blocking_roles=(), opening_status=None, opening_symbol_occurrences=None, glazed_openings=None):
    """Sites, certificate, labels and blocking for one admitted input. Returns a JSON-able dict (plus private
    arrangement handles under '_arr')."""
    if max_abs_coordinate is None:
        max_abs_coordinate = max([abs(v) for it in items for v in it.geometry[:2]] or [1.0])
    tol = TP.tolerances(max_abs_coordinate, unit_native_to_mm)
    out = {"policy": TP.POLICY_ID, "policy_digest": TP.record()["digest"], "tolerances": tol, "sites": [],
           "findings": []}
    if not tol["valid"]:
        out["state"] = UNIT_UNRESOLVED
        return out
    e_n, e_r = tol["eps_n"], tol["eps_r"]
    arr_n = build(items, e_n)
    arr_r = build(items, e_r)
    out["separation"] = TP.separation(end_distances(items, e_r), e_n, e_r)
    if not out["separation"]["separated"]:
        out["findings"].append({"code": NOISE_NEAR_EPS_N, "decisions": out["separation"]["near_eps_n"]})
    sites_n = sites_of(arr_n, revision_id, region_id)
    sites_r = {s["site_id"]: s for s in sites_of(arr_r, revision_id, region_id)}
    out["findings"] += [dict(f, build="eps_n") for f in arr_n.findings] + [dict(f, build="eps_r") for f in arr_r.findings]
    by_id = {s["site_id"]: s for s in sites_n}
    # a site that exists only when the ambiguous band is closed (eps_r) has no eps_n twin to carry the
    # TOLERANCE_SENSITIVE issue (e.g. a room whose only gap, inside the band, opens to the outside): it is stated
    for sid in sorted(set(sites_r) - set(by_id)):
        t = sites_r[sid]
        out["findings"].append({"code": SITE_ONLY_IN_AUTHORED_BUILD, "site_id": sid, "area": t["area"],
                                "boundary_source_ids": t["boundary_source_ids"]})
    for s in sites_n:
        s.setdefault("issues", [])
        twin = sites_r.get(s["site_id"])
        bound = e_r * s["perimeter"]
        s["certificate"] = {"eps_r_site_found": twin is not None,
                            "area_difference": None if twin is None else abs(twin["area"] - s["area"]),
                            "area_bound": bound}
        if twin is None or abs(twin["area"] - s["area"]) > bound:
            s["issues"].append(TOLERANCE_SENSITIVE)
        if s["area"] <= e_r * s["perimeter"] / 2.0:
            s["kind"] = SLIVER
            s["issues"].append(ZERO_WIDTH_SLIVER)
        s["labels"], s["label_texts"], s["contents"], s["blocked_by"] = [], [], defaultdict(int), []
    # ---- labels
    occ_sites = defaultdict(set)
    for lt in sorted(labels, key=lambda z: z.text_id):
        sid, near = locate(arr_n, sites_n, (lt.x, lt.y), e_r)
        if sid is None:
            out["findings"].append({"code": "LABEL_OUTSIDE_EVERY_SITE", "text": lt.text_id, "value": lt.value})
            continue
        occ_sites[lt.occurrence].add(sid)
        s = by_id[sid]
        s["label_texts"].append({"text": lt.text_id, "occurrence": lt.occurrence, "value": lt.value})
        if lt.occurrence not in s["labels"]:
            s["labels"].append(lt.occurrence)
        if near:
            s["issues"].append(LABEL_ON_BOUNDARY)
            out["findings"].append({"code": LABEL_ON_BOUNDARY, "text": lt.text_id, "sites": sorted(set(near) | {sid})})
    for occ, ss in occ_sites.items():
        if len(ss) > 1:
            for sid in ss:
                by_id[sid]["issues"].append(LABEL_OCCURRENCE_SPLIT)
            out["findings"].append({"code": LABEL_OCCURRENCE_SPLIT, "occurrence": occ, "sites": sorted(ss)})
    # ---- probes
    blocking_roles = set(blocking_roles)
    out["probe_sites"] = {}
    for pb in sorted(probes, key=lambda z: z.source_id):
        hit = touched_sites(arr_n, sites_n, items, pb, e_n, e_n)
        out["probe_sites"][pb.source_id] = hit
        for sid in hit:
            s = by_id[sid]
            s["contents"][pb.role] += 1
            if pb.role in blocking_roles:
                s["blocked_by"].append(pb.source_id)
    # ---- openings
    opening_status = opening_status or {}
    closure_sites = defaultdict(set)
    for s in sites_n:
        for src in s["boundary_source_ids"]:
            if src.startswith("CLOSURE|"):
                closure_sites[src].add(s["site_id"])
    pairs = [(occ, (st["closure_a"], st["closure_b"])) for occ, st in sorted(opening_status.items())
             if st.get("state") == "CLOSED" and st.get("closure_b")]
    pairs += [(oid, tuple(cl)) for oid, cl in sorted((glazed_openings or {}).items()) if len(cl) == 2]
    geom_of = {it.source_id: it.geometry for it in items if it.source_id.startswith("CLOSURE|")}
    for occ, (ca, cb) in pairs:
        # an OPENING_SITE is the zone BETWEEN the two closures: bounded by both and lying inside their extent.
        # A room that merely touches both closures (it wraps round the opening) is not one.
        xs = [geom_of[c][k] for c in (ca, cb) for k in (0, 2)]
        ys = [geom_of[c][k] for c in (ca, cb) for k in (1, 3)]
        zone = (min(xs) - e_r, min(ys) - e_r, max(xs) + e_r, max(ys) + e_r)
        for sid in closure_sites.get(ca, set()) & closure_sites.get(cb, set()):
            b = by_id[sid]["bbox"]
            if zone[0] <= b[0] and zone[1] <= b[1] and b[2] <= zone[2] and b[3] <= zone[3]:
                by_id[sid]["kind"] = OPENING_SITE
                by_id[sid]["opening_of"] = occ
    if opening_symbol_occurrences:
        for occ, st in sorted(opening_status.items()):
            if st.get("state") != "CLOSED":
                for pb in opening_symbol_occurrences.get(occ, ()):
                    for sid in touched_sites(arr_n, sites_n, items, pb, e_n, e_n):
                        if OPENING_CLOSURE_UNRESOLVED not in by_id[sid]["issues"]:
                            by_id[sid]["issues"].append(OPENING_CLOSURE_UNRESOLVED)
    # ---- status
    for s in sites_n:
        if len(s["labels"]) > 1:
            s["issues"].append(MULTIPLE_SEMANTIC_LABELS)
        if s["blocked_by"]:
            s["issues"].append(TOPOLOGY_ROLE_UNRESOLVED)
        s.setdefault("kind", LABELLED if s["labels"] else UNLABELLED)
        s["issues"] = sorted(set(s["issues"]))
        s["status"] = CERTIFIED if not s["issues"] else REVIEW_REQUIRED
        s["contents"] = dict(sorted(s["contents"].items()))
        s["blocked_by"] = sorted(set(s["blocked_by"]))
        s["area_m2"] = s["area"] * (unit_native_to_mm ** 2) / 1e6
        s["area_bound_m2"] = e_r * s["perimeter"] * (unit_native_to_mm ** 2) / 1e6
    # ---- adjacency through openings (closure edges only)
    adj = []
    for occ, st in sorted(opening_status.items()):
        if st.get("state") != "CLOSED":
            continue
        rooms = set()
        for cid in (st["closure_a"], st.get("closure_b")):
            if cid:
                rooms |= {sid for sid in closure_sites.get(cid, set()) if by_id[sid].get("kind") != OPENING_SITE}
        adj.append({"opening": occ, "sites": sorted(rooms)})
    out["opening_adjacency"] = adj
    out["sites"] = sites_n
    out["_arr"] = arr_n
    out["state"] = "BUILT"
    return out


def public(site) -> dict:
    """A site without the private cycle handles."""
    return {k: v for k, v in site.items() if k not in ("cycle", "hole_cycles", "face")}
