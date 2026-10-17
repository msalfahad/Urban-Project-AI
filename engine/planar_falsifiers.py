"""E59 — the checks that should have existed before the face walker shipped.

A planar GRAPH has cycles. A planar EMBEDDING — a graph plus a rotation system,
drawn with no crossings except at vertices — has FACES, and a face is a
connected component of R^2 minus the embedded edges and vertices. Connected
components of any set are pairwise disjoint.

    TWO DISTINCT BOUNDED FACES CANNOT OVERLAP IN AREA.

That is definitional, not empirical. So when the engine reported SF-V2-0003 and
SF-V2-0004 overlapping, it was not a curiosity to be labelled
FACE_NESTING_ARTIFACT — it was proof that the objects produced are NOT faces.
They are closed walks in an abstract graph, and something in the embedding is
wrong.

This module holds the invariants that make that provable instead of arguable.
None of them repairs anything. They exist to FALSIFY, and to stay behind as a
regression test once the production path moves elsewhere.

    A  every directed half-edge belongs to exactly one face walk
    B  Euler: V - E + F = 1 + C for the embedding
    C  signed walk areas reconcile within a component
    D  two distinct bounded faces have zero positive-area overlap
    E  no edge pair crosses without a shared node
    F  no node has ambiguous equal-angle outgoing half-edges

A and D are the ones that catch a broken rotation system. E and F are the ones
that say WHY.
"""

from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass, field

# The invariant names, so a failure can be reported by identity.
INV_HALF_EDGE_COVERAGE = "A_EVERY_HALF_EDGE_IN_EXACTLY_ONE_FACE_WALK"
INV_EULER = "B_EULER_FORMULA_CONSISTENT"
INV_AREA_RECONCILES = "C_SIGNED_WALK_AREAS_RECONCILE"
INV_NO_FACE_OVERLAP = "D_NO_TWO_BOUNDED_FACES_OVERLAP"
INV_NO_UNNODED_CROSSING = "E_NO_EDGE_PAIR_CROSSES_WITHOUT_A_SHARED_NODE"
INV_NO_AMBIGUOUS_ROTATION = "F_NO_AMBIGUOUS_EQUAL_ANGLE_ROTATION_AT_A_NODE"

INVARIANTS = (INV_HALF_EDGE_COVERAGE, INV_EULER, INV_AREA_RECONCILES,
              INV_NO_FACE_OVERLAP, INV_NO_UNNODED_CROSSING,
              INV_NO_AMBIGUOUS_ROTATION)

# Two half-edge directions closer than this at a node cannot be ordered
# reliably: the angular sort between them is arbitrary, and `next` may pick
# either. Coincident collinear edges land here exactly.
ANGLE_EPS_RAD = 1e-6
# Area overlap below this is a floating-point artefact of shared boundaries,
# not two faces occupying the same floor.
OVERLAP_EPS_MM2 = 1.0
# Signed areas within a component should sum to zero when every walk is a
# face of the embedding (each edge traversed once in each direction).
AREA_SUM_EPS_MM2 = 1000.0


class PlanarFalsified(RuntimeError):
    """An invariant of planar embeddings does not hold for this output."""


@dataclass(frozen=True)
class Violation:
    invariant: str
    detail: str
    faces: tuple[str, ...] = ()
    nodes: tuple[str, ...] = ()
    edges: tuple[str, ...] = ()
    measure: float | None = None

    def record(self) -> dict:
        return {"invariant": self.invariant, "detail": self.detail,
                "faces": list(self.faces), "nodes": list(self.nodes),
                "edges": list(self.edges),
                "measure": (None if self.measure is None
                            else round(self.measure, 3))}


@dataclass
class FalsifierReport:
    violations: list = field(default_factory=list)
    checked: dict = field(default_factory=dict)

    @property
    def holds(self) -> bool:
        return not self.violations

    def by_invariant(self) -> dict:
        return dict(Counter(v.invariant for v in self.violations))

    def for_faces(self, *face_ids) -> list:
        want = set(face_ids)
        return [v for v in self.violations if want & set(v.faces)]

    def record(self) -> dict:
        return {
            "holds": self.holds,
            "invariants_checked": list(INVARIANTS),
            "violations": len(self.violations),
            "by_invariant": self.by_invariant(),
            "failing_invariants": sorted(self.by_invariant()),
            "checked": dict(self.checked),
            "detail": [v.record() for v in self.violations[:80]],
            "interpretation": _interpret(self.by_invariant()),
        }


def _interpret(by_invariant: dict) -> str:
    """What the failing set MEANS, mathematically. Not a label."""
    if not by_invariant:
        return ("every invariant holds: these walks are faces of a planar "
                "subdivision")
    parts = []
    if INV_NO_FACE_OVERLAP in by_invariant:
        parts.append(
            "two bounded regions share positive area, so they are NOT faces "
            "of a planar subdivision — faces are connected components of the "
            "plane minus the graph, and components are disjoint by definition")
    if INV_NO_AMBIGUOUS_ROTATION in by_invariant:
        parts.append(
            "at least one node has two outgoing half-edges at the same angle, "
            "so the rotation system is ILL-DEFINED there: the angular sort "
            "between them is arbitrary and `next` may splice two faces into "
            "one walk or split one face across two")
    if INV_NO_UNNODED_CROSSING in by_invariant:
        parts.append(
            "at least one edge pair crosses with no vertex at the crossing, so "
            "the drawing is not a planar embedding at all and walks pass "
            "THROUGH each other")
    if INV_HALF_EDGE_COVERAGE in by_invariant:
        parts.append(
            "some half-edge is used by no walk or by more than one, which a "
            "true face traversal cannot do")
    if INV_EULER in by_invariant:
        parts.append("the face count is inconsistent with V - E + F = 1 + C")
    if INV_AREA_RECONCILES in by_invariant:
        parts.append(
            "signed walk areas do not cancel within a component, which they "
            "must when every edge is traversed once in each direction")
    return ("CONCLUSION: the engine is enumerating CYCLES OF THE ABSTRACT "
            "GRAPH and calling them faces. " + " Also: ".join(parts))


# ------------------------------------------------------------------ the checks

def _signed_area(poly) -> float:
    s = 0.0
    p = list(poly)
    for (x0, y0), (x1, y1) in zip(p, p[1:] + p[:1]):
        s += x0 * y1 - x1 * y0
    return s / 2.0


def check_half_edge_coverage(half_edges: dict, faces) -> list:
    """A — every directed half-edge belongs to exactly one face walk."""
    used: Counter = Counter()
    for f in faces:
        for hid in f.half_edge_ids:
            used[hid] += 1
    out = []
    unvisited = [h for h in half_edges if used[h] == 0]
    twice = [h for h, n in used.items() if n > 1]
    if unvisited:
        out.append(Violation(
            INV_HALF_EDGE_COVERAGE,
            f"{len(unvisited)} of {len(half_edges)} half-edges belong to NO "
            "face walk. A face traversal of a sound embedding visits every "
            "half-edge exactly once",
            edges=tuple(sorted(unvisited)[:12]),
            measure=float(len(unvisited))))
    if twice:
        out.append(Violation(
            INV_HALF_EDGE_COVERAGE,
            f"{len(twice)} half-edge(s) appear in more than one face walk",
            edges=tuple(sorted(twice)[:12]), measure=float(len(twice))))
    return out


def check_euler(half_edges: dict, faces, *, nodes=None) -> list:
    """B — V - E + F = 1 + C, counting the unbounded face of each component."""
    e_ids = {h.source_edge_id for h in half_edges.values()}
    v_ids = ({h.origin_node for h in half_edges.values()}
             | {h.target_node for h in half_edges.values()})
    V, E, F = len(v_ids), len(e_ids), len(faces)
    # Components of the abstract graph, over nodes.
    parent = {v: v for v in v_ids}

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    for h in half_edges.values():
        ra, rb = find(h.origin_node), find(h.target_node)
        if ra != rb:
            parent[rb] = ra
    C = len({find(v) for v in v_ids})
    lhs, rhs = V - E + F, 1 + C
    if lhs != rhs:
        return [Violation(
            INV_EULER,
            f"V - E + F = {V} - {E} + {F} = {lhs}, but 1 + C = 1 + {C} = "
            f"{rhs}. The walks produced cannot be the faces of a planar "
            "embedding of this graph",
            measure=float(lhs - rhs))]
    return []


def check_area_reconciles(faces) -> list:
    """C — signed areas cancel within a planar component."""
    groups: dict = {}
    for f in faces:
        groups.setdefault(f.planar_component_id or "", []).append(f)
    out = []
    for pc, fs in sorted(groups.items()):
        total = sum(_signed_area(list(f.polygon_mm)) for f in fs)
        if abs(total) > AREA_SUM_EPS_MM2:
            out.append(Violation(
                INV_AREA_RECONCILES,
                f"signed walk areas in {pc or 'the component'} sum to "
                f"{total / 1e6:.3f} m2 instead of zero. Every edge of a sound "
                "embedding is traversed once in each direction, so the signed "
                "areas must cancel",
                faces=tuple(f.space_face_id if hasattr(f, "space_face_id")
                            else f.face_id for f in fs)[:12],
                measure=total))
    return out


def check_no_face_overlap(faces, *, bounded_kinds=("BOUNDED_FACE",)) -> list:
    """D — the definitional one. Library-backed area intersection."""
    from shapely.geometry import Polygon
    from shapely.validation import explain_validity

    bounded = [f for f in faces
               if getattr(f, "kind", "BOUNDED_FACE") in bounded_kinds]
    polys = {}
    out = []
    for f in bounded:
        fid = getattr(f, "space_face_id", None) or f.face_id
        p = Polygon(list(f.polygon_mm))
        if not p.is_valid:
            p = p.buffer(0)
        if p.is_empty:
            continue
        polys[fid] = p
    ids = sorted(polys)
    for i, a in enumerate(ids):
        for b in ids[i + 1:]:
            inter = polys[a].intersection(polys[b])
            area = inter.area
            if area > OVERLAP_EPS_MM2:
                out.append(Violation(
                    INV_NO_FACE_OVERLAP,
                    f"{a} and {b} share {area / 1e6:.3f} m2 of positive area. "
                    "Faces of a planar subdivision are connected components "
                    "of the plane minus the graph, and components are "
                    "DISJOINT — so these two objects are not faces",
                    faces=(a, b), measure=area))
    del explain_validity
    return out


def check_no_unnoded_crossing(noded) -> list:
    """E — an edge pair crossing with no vertex at the crossing.

    Axis-aligned edges only, which is what this graph holds: an H edge and a V
    edge cross when their spans straddle each other's fixed coordinate.
    """
    nodes_at = {(round(n.x_mm, 1), round(n.y_mm, 1)) for n in noded.nodes}
    h = [e for e in noded.edges if e.axis == "H"]
    v = [e for e in noded.edges if e.axis == "V"]
    out = []
    for a in h:
        alo, ahi = min(a.start_mm, a.end_mm), max(a.start_mm, a.end_mm)
        for b in v:
            blo, bhi = min(b.start_mm, b.end_mm), max(b.start_mm, b.end_mm)
            x, y = b.centreline_mm, a.centreline_mm
            # strictly interior to both spans: a shared endpoint is fine
            if not (alo + 0.5 < x < ahi - 0.5 and blo + 0.5 < y < bhi - 0.5):
                continue
            if (round(x, 1), round(y, 1)) in nodes_at:
                continue
            out.append(Violation(
                INV_NO_UNNODED_CROSSING,
                f"{a.edge_id} and {b.edge_id} cross at "
                f"({x:.1f}, {y:.1f}) with no node there. The drawing is not a "
                "planar embedding, and face walks pass through each other at "
                "this point",
                edges=(a.edge_id, b.edge_id)))
    return out


def check_no_ambiguous_rotation(half_edges: dict) -> list:
    """F — two outgoing half-edges at one node with the same direction.

    This is what a portal closure edge laid on its host wall's own centreline
    produces at a jamb, and what a duplicate band produces everywhere. The
    angular sort between them is arbitrary, so `next` is arbitrary, so the
    walk is arbitrary.
    """
    out_at: dict = {}
    for h in half_edges.values():
        out_at.setdefault(h.origin_node, []).append(h)
    out = []
    for nid, hs in sorted(out_at.items()):
        by_angle = sorted(hs, key=lambda h: h.angle)
        for a, b in zip(by_angle, by_angle[1:]):
            d = abs(a.angle - b.angle)
            if d < ANGLE_EPS_RAD or abs(d - 2 * math.pi) < ANGLE_EPS_RAD:
                out.append(Violation(
                    INV_NO_AMBIGUOUS_ROTATION,
                    f"node {nid} has outgoing half-edges {a.half_edge_id} and "
                    f"{b.half_edge_id} at the same angle "
                    f"({a.angle:.6f} rad). The rotation system is ill-defined "
                    "here: the order between them is arbitrary, so `next` is "
                    "arbitrary and the walk may splice or split a face",
                    nodes=(nid,),
                    edges=(a.half_edge_id, b.half_edge_id), measure=d))
    return out


def falsify(half_edges: dict, faces, *, noded=None) -> FalsifierReport:
    """Run every invariant. Repairs nothing; explains everything."""
    rep = FalsifierReport()
    rep.violations += check_half_edge_coverage(half_edges, faces)
    rep.violations += check_euler(half_edges, faces)
    rep.violations += check_area_reconciles(faces)
    rep.violations += check_no_face_overlap(faces)
    if noded is not None:
        rep.violations += check_no_unnoded_crossing(noded)
    rep.violations += check_no_ambiguous_rotation(half_edges)
    rep.checked = {
        "half_edges": len(half_edges),
        "faces": len(faces),
        "bounded_faces": sum(
            1 for f in faces
            if getattr(f, "kind", "BOUNDED_FACE") == "BOUNDED_FACE"),
        "nodes": len({h.origin_node for h in half_edges.values()}),
        "graph_edges": len({h.source_edge_id for h in half_edges.values()}),
    }
    return rep


def assert_planar(half_edges: dict, faces, *, noded=None) -> None:
    """For fixtures, where a sound embedding is the whole point of the test."""
    rep = falsify(half_edges, faces, noded=noded)
    if not rep.holds:
        raise PlanarFalsified(
            "these walks are not the faces of a planar subdivision:\n  - "
            + "\n  - ".join(v.detail for v in rep.violations[:10])
            + "\n" + rep.record()["interpretation"])
