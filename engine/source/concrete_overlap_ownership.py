"""CONCRETE_OVERLAP_OWNERSHIP_V1 (T-189): concrete at intersecting structural elements is measured EXACTLY ONCE.

Pure, unwired check (imported by no method, no CLI; rollback: delete). It never produces a BOQ quantity: it tells
whether a set of BOQ / ledger lines bills the physical concrete of intersecting elements once, and which element owns
each intersection.

Model. Every element is a union of disjoint CONVEX pieces, each a set of half-spaces a . x <= b (x, y, z in metres;
builders below take a length unit and refuse an unknown one). Volumes are exact for the polyhedra (vertex enumeration
from the half-spaces, facets ordered round their centroid, pyramids from an interior point): no voxels, no sampling.
Curved parts are given as their own convex polygon pieces by the caller (the module never invents a chord).

Two solids per element:
  physical  what is built (the drawing), and
  billed    what the element's BOQ / ledger line measures by its stated basis (default: the physical solid).
The check (check_ownership):
  union        = vol(U physical)                         the concrete that exists
  billed_sum   = sum vol(billed_i)                       what the BOQ lines carry
  billed_union = vol(U billed)
  DOUBLE       = billed_sum - billed_union  > tol        some volume is in two (or more) lines
  GAP          = union - billed_union       > tol        some built concrete is in no line
  OUTSIDE      = vol(billed_i minus physical_i) > tol    a line bills concrete its element does not have
and per intersecting pair: the volume, how many lines bill it, the owner by the precedence profile, OK / DOUBLE / GAP
/ OWNER_UNDEFINED. PASS only when DOUBLE = GAP = OUTSIDE = 0 and every intersecting pair has an owner; PASS_HELD when
that holds for every determined pair and some pair is UNDETERMINED (listed under held).
An element whose levels are not printed (levels_known False) is given with an unbounded z range: any plan overlap with
it is UNDETERMINED with the bounded exposure 0 .. vol(intersection with the unbounded prism); it is never deducted and
never enters the union (missing never becomes 0, held never becomes a deduction).

Ownership (rule R-CONC-OWN-1, proposed, research/agents_t189/R-CONC-OWN-1.json): the intersection of two elements is
owned by the element whose BOQ line, by its measurement basis, is billed THROUGH the junction (full section); the other
is measured net of it and keeps the deduction in its ledger (owner Q-62 A cond, Q-20). If no line bills it, the element
that would lose it keeps it. A pair with no established precedence is OWNER_UNDEFINED (held), never guessed.
PRECEDENCE_ROUTE_G records the precedence of the released route G measurement bases (higher number owns):
  COLUMN 50 > BEAM 40 (route G: 'column footprint split out; junction squares owned by one band')
  BEAM 40 > SLAB 30 (route G: 'slab panels stop at band faces'; beams billed at the full depth)
  SLAB / LANDING 30 > STAIR 10 (owner Q-62 A cond: the intersection is assigned to the slab / landing, deducted from
  the stair), BEAM 40 > STAIR 10 (R-CONC-OWN-1: a beam billed at its full section through the stair head owns the
  flight solid inside its band)
  POOL_BASE 25 > POOL_WALL 20 (T-183 / frozen pool_qto.wall_base_split: base = outer footprint x t, walls above it)
Pairs NOT in the profile (footing / neck, footing / strap, pool / footing, ...) are OWNER_UNDEFINED until a drawing-
based rule records them (T-174 for straps). A project using the slab-plate / downstand basis
(URBAN-NON-OVERLAPPING-SLAB-BEAM-MODEL@v1) passes its own profile (SLAB over BEAM).
"""

from __future__ import annotations

import functools
import itertools
import math
from dataclasses import dataclass

import numpy as np

SCHEMA = "CONCRETE_OVERLAP_OWNERSHIP_V1"
TOL_M3 = 1e-5  # m3 (0.01 litre): below the 6th decimal of the readings (riser 0.166667 for 2.00 / 12)
_EPS = 1e-9
_BIG = 1.0e4  # m: the unbounded z range of an element whose levels are not printed

UNIT_TO_M = {"m": 1.0, "cm": 0.01, "mm": 0.001}

PRECEDENCE_ROUTE_G = {
    "COLUMN": 50, "BEAM": 40, "SLAB": 30, "LANDING": 30, "POOL_BASE": 25, "POOL_WALL": 20, "STAIR": 10,
}
# pairs whose owner IS established (unordered); any other intersecting pair is OWNER_UNDEFINED
ESTABLISHED_PAIRS_ROUTE_G = {
    frozenset(p): src for p, src in (
        (("COLUMN", "BEAM"), "route G beam lines: net plan B x L - column - junction"),
        (("BEAM", "SLAB"), "route G: slab panels stop at band faces; beam at full depth"),
        (("SLAB", "STAIR"), "owner Q-62 A cond"),
        (("LANDING", "STAIR"), "owner Q-62 A cond"),
        (("BEAM", "STAIR"), "R-CONC-OWN-1 (T-189, proposed; Q-62 A cond extended to a beam billed through)"),
        (("POOL_BASE", "POOL_WALL"), "T-183 / pool_qto.wall_base_split: base = outer footprint x t"),
        (("COLUMN", "SLAB"), "route G: column footprint split out of the slab faces"),
    )
}


def _unit(unit):
    if unit not in UNIT_TO_M:
        raise ValueError(f"unknown length unit {unit!r}: one of {sorted(UNIT_TO_M)}")
    return UNIT_TO_M[unit]


# ---------------------------------------------------------------- convex pieces (H-representation)

@dataclass(frozen=True)
class Piece:
    """convex polyhedron {x : A x <= b}; label names the part (e.g. 'MS1-U step 11')."""
    A: tuple
    b: tuple
    label: str = ""

    def arrays(self):
        return np.asarray(self.A, dtype=float).reshape(-1, 3), np.asarray(self.b, dtype=float)


def _piece(rows, label=""):
    A, b = [], []
    for a, c in rows:
        a = np.asarray(a, dtype=float)
        n = float(np.linalg.norm(a))
        if n < _EPS:
            raise ValueError("degenerate half-space")
        A.append(tuple(a / n))
        b.append(float(c) / n)
    return Piece(tuple(A), tuple(b), label)


def intersect(p, q, label=None):
    return Piece(p.A + q.A, p.b + q.b, label if label is not None else f"{p.label} & {q.label}")


@functools.lru_cache(maxsize=200000)
def _hrep_vertices(A, b):
    """vertices of {x : A x <= b} (tuples in, cached): batched triple-plane solves, feasibility, dedupe."""
    A = np.asarray(A, dtype=float).reshape(-1, 3)
    b = np.asarray(b, dtype=float)
    # dedupe identical planes (a facet listed twice would be counted twice)
    key = np.round(np.hstack([A, b[:, None]]), 12)
    _, idx = np.unique(key, axis=0, return_index=True)
    idx = np.sort(idx)
    A, b = A[idx], b[idx]
    scale = max(1.0, float(np.max(np.abs(b)))) if len(b) else 1.0
    tol = 1e-9 * scale
    n = len(A)
    if n < 4:
        return A, b, np.zeros((0, 3)), tol
    tri = np.array(list(itertools.combinations(range(n), 3)))
    M = A[tri]                                   # (T, 3, 3)
    det = np.linalg.det(M)
    ok = np.abs(det) > 1e-12
    if not ok.any():
        return A, b, np.zeros((0, 3)), tol
    V = np.linalg.solve(M[ok], b[tri[ok]][..., None])[..., 0]
    feas = np.all(V @ A.T <= b + tol, axis=1)
    V = V[feas]
    if len(V) == 0:
        return A, b, np.zeros((0, 3)), tol
    Vr = np.round(V / (1e-8 * scale))
    _, first = np.unique(Vr, axis=0, return_index=True)
    return A, b, V[np.sort(first)], tol


def _vertices(A, b):
    A2, b2, V, tol = _hrep_vertices(tuple(map(tuple, np.asarray(A).reshape(-1, 3))), tuple(np.asarray(b).ravel()))
    return A2, b2, list(V), tol


def bbox(piece):
    _, _, V, _ = _hrep_vertices(piece.A, piece.b)
    if len(V) == 0:
        return None
    return V.min(axis=0), V.max(axis=0)


def _bbox_overlap(p, q, eps=1e-9):
    bp, bq = bbox(p), bbox(q)
    if bp is None or bq is None:
        return False
    return bool(np.all(bp[0] <= bq[1] + eps) and np.all(bq[0] <= bp[1] + eps))


@functools.lru_cache(maxsize=200000)
def _volume_cached(A, b):
    A, b, V, tol = _hrep_vertices(A, b)
    if len(V) < 4:
        return 0.0
    c = V.mean(axis=0)
    vol = 0.0
    for a, bb in zip(A, b):
        on = V[np.abs(V @ a - bb) <= max(tol, 1e-9)]
        if len(on) < 3:
            continue
        fc = on.mean(axis=0)
        d = on - fc
        k = int(np.argmax(np.linalg.norm(d, axis=1)))
        u = d[k] / np.linalg.norm(d[k])
        w = np.cross(a, u)
        poly = on[np.argsort(np.arctan2(d @ w, d @ u))]
        area_vec = np.cross(poly - fc, np.roll(poly, -1, axis=0) - fc).sum(axis=0)
        vol += abs(float(area_vec @ a)) / 2.0 * float(bb - a @ c) / 3.0
    return max(vol, 0.0)


def volume(piece):
    """exact volume of one convex piece (0.0 when empty or flat)."""
    return _volume_cached(piece.A, piece.b)


def total_volume(pieces):
    return sum(volume(p) for p in pieces)


def clip(pieces, a, c, label_suffix=""):
    """keep the part of every piece with a . x <= c (a cut plane, e.g. a beam face)."""
    h = _piece([(a, c)])
    return [Piece(p.A + h.A, p.b + h.b, p.label + label_suffix) for p in pieces]


def difference(pieces, cutter):
    """pieces minus the convex piece `cutter`, as disjoint convex pieces (exact)."""
    out = []
    CA, Cb = cutter.A, cutter.b
    for p in pieces:
        if not _bbox_overlap(p, cutter) or volume(intersect(p, cutter)) <= _EPS:
            out.append(p)
            continue
        keep_A, keep_b = list(p.A), list(p.b)
        for a, c in zip(CA, Cb):
            # the part of p beyond this face of the cutter (and inside the earlier faces): disjoint pieces
            neg = tuple(-x for x in a)
            q = Piece(tuple(keep_A) + (neg,), tuple(keep_b) + (-c,), p.label)
            if volume(q) > _EPS:
                out.append(q)
            keep_A.append(a)
            keep_b.append(c)
    return out


def intersection_volume(P, Q):
    return sum(volume(intersect(p, q)) for p in P for q in Q if _bbox_overlap(p, q))


def union_volume(sets):
    """vol of the union of several elements (each a list of disjoint convex pieces), by inclusion-exclusion over
    elements; the intersection of k elements is the union of pairwise-disjoint convex products of their pieces."""
    sets = [s for s in sets if s]
    tot = 0.0
    for k in range(1, len(sets) + 1):
        sign = 1.0 if k % 2 else -1.0
        for combo in itertools.combinations(sets, k):
            acc = list(combo[0])
            for s in combo[1:]:
                acc = [intersect(p, q) for p in acc for q in s if _bbox_overlap(p, q)]
                acc = [p for p in acc if volume(p) > _EPS]
                if not acc:
                    break
            tot += sign * total_volume(acc)
    return tot


# ---------------------------------------------------------------- builders

def box(x0, x1, y0, y1, z0, z1, unit="m", label="box"):
    f = _unit(unit)
    x0, x1, y0, y1, z0, z1 = (v * f for v in (x0, x1, y0, y1, z0, z1))
    if not (x1 > x0 and y1 > y0 and z1 > z0):
        raise ValueError("box needs positive extents")
    return [_piece([((-1, 0, 0), -x0), ((1, 0, 0), x1), ((0, -1, 0), -y0), ((0, 1, 0), y1),
                    ((0, 0, -1), -z0), ((0, 0, 1), z1)], label)]


def plan_prism(polygon, z0, z1, unit="m", label="prism"):
    """a convex plan polygon (any orientation) extruded from z0 to z1 (z0 / z1 None = levels not printed: unbounded)."""
    f = _unit(unit)
    pts = [(x * f, y * f) for x, y in polygon]
    if len(pts) < 3:
        raise ValueError("polygon needs 3 points")
    area2 = sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]))
    if abs(area2) < _EPS:
        raise ValueError("flat polygon")
    if area2 < 0:
        pts = pts[::-1]
    rows = []
    n = len(pts)
    for i in range(n):
        (x0, y0), (x1, y1) = pts[i], pts[(i + 1) % n]
        nx, ny = (y1 - y0), -(x1 - x0)  # outward normal of a CCW polygon
        rows.append(((nx, ny, 0.0), nx * x0 + ny * y0))
    for i in range(n):  # convexity: every vertex inside every edge
        for a, c in rows:
            if a[0] * pts[i][0] + a[1] * pts[i][1] > c + 1e-9 * max(1.0, abs(c)):
                raise ValueError("plan polygon is not convex: split it into convex pieces")
    lo = -_BIG if z0 is None else z0 * f
    hi = _BIG if z1 is None else z1 * f
    rows += [((0, 0, -1), -lo), ((0, 0, 1), hi)]
    return [_piece(rows, label)]


def beam(p0, p1, width, z_top, depth, unit="m", label="beam"):
    """a straight beam band of `width` centred on the plan axis p0 -> p1, from z_top - depth to z_top (any angle)."""
    f = _unit(unit)
    (x0, y0), (x1, y1) = (p0[0] * f, p0[1] * f), (p1[0] * f, p1[1] * f)
    L = math.hypot(x1 - x0, y1 - y0)
    if L < _EPS:
        raise ValueError("zero-length beam")
    dx, dy = (x1 - x0) / L, (y1 - y0) / L
    nx, ny = -dy, dx
    h = width * f / 2.0
    poly = [(x0 + nx * h, y0 + ny * h), (x1 + nx * h, y1 + ny * h), (x1 - nx * h, y1 - ny * h), (x0 - nx * h, y0 - ny * h)]
    return plan_prism(poly, z_top * f - depth * f, z_top * f, unit="m", label=label)


@dataclass
class Flight:
    """a straight flight (owner Q-19 steps, Q-47 A waist): origin = plan point of the FIRST riser line on one string;
    direction = plan direction of travel (up the flight); the width runs to the LEFT of the direction (mirror: side -1).
    risers / goings as counted (Q-46 A: the section counts); n_triangles = step triangles (owner ledger: one per riser,
    the last one beyond the last riser line is the arrival wedge inside the receiving member)."""
    id: str
    origin: tuple
    direction: tuple
    width: float
    z0: float
    riser: float
    going: float
    goings: int
    n_triangles: int
    waist: float
    side: int = 1
    unit: str = "m"

    def frame(self):
        f = _unit(self.unit)
        dx, dy = self.direction
        L = math.hypot(dx, dy)
        d = np.array([dx / L, dy / L, 0.0])
        n = np.array([-d[1], d[0], 0.0]) * (1 if self.side >= 0 else -1)
        O = np.array([self.origin[0] * f, self.origin[1] * f, self.z0 * f])
        return f, O, d, n

    def _local(self, rows, label):
        """rows in local (s, u, z') coordinates, z' = z - z0 -> global half-spaces."""
        f, O, d, n = self.frame()
        out = []
        for (a_s, a_u, a_z), c in rows:
            a = a_s * d + a_u * n + np.array([0.0, 0.0, a_z])
            out.append((a, c + float(a @ O)))
        return _piece(out, label)

    def pieces(self, include_arrival_wedge=True):
        f = _unit(self.unit)
        r, g, w, t = self.riser * f, self.going * f, self.width * f, self.waist * f
        slope = r / g
        width_rows = [((0, -1, 0), 0.0), ((0, 1, 0), w)]
        out = []
        for k in range(1, self.n_triangles + 1):
            if k > self.goings and not include_arrival_wedge:
                continue
            s0 = (k - 1) * g
            rows = width_rows + [((-1, 0, 0), -s0), ((0, 0, 1), k * r), ((slope, 0, -1), 0.0)]  # z' >= slope s
            tag = "arrival wedge" if k > self.goings else f"step {k}"
            out.append(self._local(rows, f"{self.id} {tag}"))
        L = self.goings * g
        cos = g / math.hypot(g, r)
        rows = width_rows + [((-1, 0, 0), 0.0), ((1, 0, 0), L), ((-slope, 0, 1), 0.0), ((slope, 0, -1), t / cos)]
        out.append(self._local(rows, f"{self.id} waist"))
        return out

    def ledger_m3(self):
        """the owner formulas: n_triangles x 1/2 r g w + w x t x hypot(goings g, goings r)."""
        f = _unit(self.unit)
        r, g, w, t = self.riser * f, self.going * f, self.width * f, self.waist * f
        return dict(steps=self.n_triangles * 0.5 * r * g * w,
                    waist=w * t * math.hypot(self.goings * g, self.goings * r))


# ---------------------------------------------------------------- the check

@dataclass
class Element:
    id: str
    kind: str
    physical: list
    billed: list | None = None          # None = billed as built
    ledger_m3: float | None = None      # the line's own figure, cross-checked against vol(billed)
    levels_known: bool = True
    note: str = ""

    def billed_pieces(self):
        return self.physical if self.billed is None else self.billed


def _owner(e1, e2, precedence, established):
    pair = frozenset((e1.kind, e2.kind))
    if e1.kind == e2.kind:
        return None, "same kind: two elements of one kind must not intersect (drawing or ledger error)"
    if pair not in established:
        return None, "no established precedence for this pair"
    p1, p2 = precedence.get(e1.kind), precedence.get(e2.kind)
    if p1 is None or p2 is None or p1 == p2:
        return None, "precedence missing"
    return (e1 if p1 > p2 else e2), established[pair]


def check_ownership(elements, precedence=None, established=None, tol=TOL_M3):
    precedence = PRECEDENCE_ROUTE_G if precedence is None else precedence
    established = ESTABLISHED_PAIRS_ROUTE_G if established is None else established
    ids = [e.id for e in elements]
    if len(set(ids)) != len(ids):
        raise ValueError("element ids must be unique")
    known = [e for e in elements if e.levels_known]
    unknown = [e for e in elements if not e.levels_known]
    rows, issues = [], []
    per = {}
    for e in elements:
        gross = total_volume(e.physical)
        billed = total_volume(e.billed_pieces())
        outside = total_volume([q for p in e.billed_pieces() for q in _minus_all([p], e.physical)])
        per[e.id] = dict(kind=e.kind, physical_m3=gross if e.levels_known else None,
                         billed_m3=billed if e.levels_known else None, ledger_m3=e.ledger_m3,
                         outside_m3=outside, levels_known=e.levels_known)
        if e.levels_known and e.ledger_m3 is not None and abs(e.ledger_m3 - billed) > max(tol, 1e-4):
            issues.append(dict(kind="LEDGER_MISMATCH", element=e.id, ledger_m3=e.ledger_m3, geometry_m3=billed))
        if e.levels_known and outside > tol:
            issues.append(dict(kind="OUTSIDE", element=e.id, m3=outside))
    for e1, e2 in itertools.combinations(elements, 2):
        v = intersection_volume(e1.physical, e2.physical)
        if v <= tol:
            continue
        if not (e1.levels_known or e2.levels_known):
            unit_slab = box(-_BIG, _BIG, -_BIG, _BIG, 0.0, 1.0)
            area = intersection_volume([intersect(p, q) for p in e1.physical for q in e2.physical], unit_slab)
            rows.append(dict(pair=(e1.id, e2.id), m3=None, exposure_m3=None, plan_overlap_m2=area,
                             status="UNDETERMINED", why="levels printed on neither element: plan overlap only, "
                             "no volume bound, never deducted"))
            continue
        if not (e1.levels_known and e2.levels_known):
            rows.append(dict(pair=(e1.id, e2.id), m3=None, exposure_m3=(0.0, v), status="UNDETERMINED",
                             why="levels not printed on one element: bounded by the plan overlap over the other "
                             "element's height, never deducted"))
            continue
        both = intersection_volume(e1.billed_pieces(), e2.billed_pieces())
        own, src = _owner(e1, e2, precedence, established)
        status = "OK"
        if both > tol:
            status = "DOUBLE"
        if own is None:
            status = "OWNER_UNDEFINED" if status == "OK" else status + "+OWNER_UNDEFINED"
        rows.append(dict(pair=(e1.id, e2.id), m3=v, billed_twice_m3=both,
                         owner=own.id if own else None, source=src, status=status))
    union = union_volume([e.physical for e in known])
    billed_sum = sum(total_volume(e.billed_pieces()) for e in known)
    billed_union = union_volume([e.billed_pieces() for e in known])
    double = billed_sum - billed_union
    gap = union - billed_union
    owned = owned_volumes(known, precedence, established)
    ok = (double <= tol and gap <= tol and not any(i["kind"] == "OUTSIDE" for i in issues)
          and all(r["status"] == "OK" for r in rows if r["status"] != "UNDETERMINED"))
    held = [r for r in rows if r["status"] == "UNDETERMINED"]
    status = "FAIL" if not ok else ("PASS_HELD" if held else "PASS")
    return dict(schema=SCHEMA, status=status, union_m3=union, billed_sum_m3=billed_sum,
                billed_union_m3=billed_union, double_m3=max(double, 0.0), gap_m3=max(gap, 0.0), pairs=rows,
                elements=per, owned=owned, issues=issues, held=held,
                unknown_level_elements=[e.id for e in unknown])


def _minus_all(pieces, others):
    out = list(pieces)
    for c in others:
        nxt = []
        for p in out:
            nxt += difference([p], c)
        out = nxt
    return out


def owned_volumes(elements, precedence=None, established=None):
    """owned_i = vol(physical_i minus every intersecting element that owns the pair); a pair without an owner keeps
    its volume in BOTH (it is reported OWNER_UNDEFINED by check_ownership, never silently split)."""
    precedence = PRECEDENCE_ROUTE_G if precedence is None else precedence
    established = ESTABLISHED_PAIRS_ROUTE_G if established is None else established
    out = {}
    for e in elements:
        cutters = []
        for o in elements:
            if o is e or intersection_volume(e.physical, o.physical) <= TOL_M3:
                continue
            own, _ = _owner(e, o, precedence, established)
            if own is o:
                cutters += o.physical
        out[e.id] = total_volume(_minus_all(e.physical, cutters))
    return out
