"""Node and split the wall graph, so planar face extraction has a graph to walk.

The previous graph stored an intersection as metadata and left the through-wall
whole. A T-junction therefore had degree 2 and reported L_JUNCTION, and planar
face construction would have walked straight past the stem. Topology needs the
through-edge divided at the node, and every consequence of dividing it handled:

  lineage      a child edge still knows which wall pair it came from
  length       splitting changes topology and must not create or destroy wall
  clustering   union-find can chain A-B-C into one node when A and C are far apart
  duplicates   two coincident edges would make a zero-width face
  micro-edges  a 5 mm fragment is tracked, not deleted for being short
  degree       only the POST-SPLIT graph owns an authoritative degree

Nothing here decides what a wall means. It decides where walls meet.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field, replace

from engine.wall_graph import (COMPLEX_JUNCTION, CONTINUATION, CROSS_JUNCTION,
                               L_JUNCTION, TERMINUS, T_JUNCTION, WallEdge,
                               WallGraph)

# Why a node exists. Endpoint-on-edge is the one the source file does not give us.
NODE_ENDPOINT = "EDGE_ENDPOINT"
NODE_CROSSING = "PERPENDICULAR_CROSSING"
NODE_ENDPOINT_ON_EDGE = "ENDPOINT_ON_EDGE_INTERIOR"

# Why an edge was divided.
SPLIT_AT_NODE = "SPLIT_AT_INTERIOR_NODE"

# Cluster health. An over-spread cluster is refused rather than collapsed.
CLUSTER_OK = "OK"
CLUSTER_OVER_SPREAD = "OVER_SPREAD"

# Duplicate handling.
DUP_EXACT = "EXACT_DUPLICATE_MERGED"
DUP_PARTIAL = "PARTIAL_OVERLAP_RECORDED"

# An edge short enough to be suspicious. Tracked, never silently dropped.
MICRO_EDGE_MM = 50.0

PROBABLE = "PROBABLE"
UNRESOLVED = "UNRESOLVED"


class NodingError(RuntimeError):
    """The graph could not be noded without violating an invariant."""


@dataclass(frozen=True)
class Node:
    """One graph node, and how confident we are that it is really one point."""

    node_id: str
    x_mm: float
    y_mm: float
    reasons: tuple[str, ...]
    member_count: int
    diameter_mm: float
    max_displacement_mm: float
    status: str = CLUSTER_OK
    edge_ids: tuple[str, ...] = ()
    kind: str = UNRESOLVED

    @property
    def degree(self) -> int:
        return len(self.edge_ids)

    def record(self) -> dict:
        return {"node_id": self.node_id, "x_mm": round(self.x_mm, 1),
                "y_mm": round(self.y_mm, 1), "kind": self.kind,
                "degree": self.degree, "reasons": list(self.reasons),
                "member_count": self.member_count,
                "diameter_mm": round(self.diameter_mm, 1),
                "max_displacement_mm": round(self.max_displacement_mm, 1),
                "status": self.status, "edge_ids": list(self.edge_ids)}


@dataclass(frozen=True)
class SplitEdge:
    """A graph edge after noding, with its whole lineage intact."""

    edge_id: str
    parent_edge_id: str
    axis: str
    centreline_mm: float
    start_mm: float
    end_mm: float
    face_a_mm: float
    face_b_mm: float
    pair_id: str
    wall_face_separation_mm: float
    separation_basis: str
    parent_start_mm: float
    parent_end_mm: float
    split_reason: str = ""
    split_node_ids: tuple[str, ...] = ()
    source_object_ids: tuple = ()
    merged_from: tuple[str, ...] = ()
    validation_status: str = PROBABLE

    @property
    def length_mm(self) -> float:
        return abs(self.end_mm - self.start_mm)

    @property
    def is_micro(self) -> bool:
        return self.length_mm < MICRO_EDGE_MM

    def record(self) -> dict:
        return {"edge_id": self.edge_id, "parent_edge_id": self.parent_edge_id,
                "pair_id": self.pair_id, "axis": self.axis,
                "centreline_mm": round(self.centreline_mm, 1),
                "start_mm": round(self.start_mm, 1),
                "end_mm": round(self.end_mm, 1),
                "length_mm": round(self.length_mm, 1),
                "parent_start_mm": round(self.parent_start_mm, 1),
                "parent_end_mm": round(self.parent_end_mm, 1),
                "wall_face_separation_mm": round(self.wall_face_separation_mm, 1),
                "separation_basis": self.separation_basis,
                "split_reason": self.split_reason,
                "split_node_ids": list(self.split_node_ids),
                "merged_from": list(self.merged_from),
                "is_micro": self.is_micro,
                "validation_status": self.validation_status}


@dataclass
class NodedGraph:
    nodes: list[Node] = field(default_factory=list)
    edges: list[SplitEdge] = field(default_factory=list)
    duplicates: list[dict] = field(default_factory=list)
    pre_split_total_length_mm: float = 0.0
    over_spread_clusters: list[str] = field(default_factory=list)

    @property
    def post_split_total_length_mm(self) -> float:
        return sum(e.length_mm for e in self.edges)

    @property
    def micro_edges(self) -> list[SplitEdge]:
        return [e for e in self.edges if e.is_micro]

    def components(self) -> int:
        """Connected components over shared nodes — an isolated island is a
        topology gap, not a graph that happens to be in pieces."""
        by_edge: dict[str, set[str]] = {}
        for n in self.nodes:
            for a in n.edge_ids:
                for b in n.edge_ids:
                    if a != b:
                        by_edge.setdefault(a, set()).add(b)
        seen, comps = set(), 0
        for e in self.edges:
            if e.edge_id in seen:
                continue
            comps += 1
            stack = [e.edge_id]
            while stack:
                cur = stack.pop()
                if cur in seen:
                    continue
                seen.add(cur)
                stack.extend(by_edge.get(cur, ()))
        return comps

    def health(self) -> dict:
        from collections import Counter
        kinds = Counter(n.kind for n in self.nodes)
        pre, post = self.pre_split_total_length_mm, self.post_split_total_length_mm
        return {
            "nodes": len(self.nodes), "edges": len(self.edges),
            **{k: kinds.get(k, 0) for k in (TERMINUS, CONTINUATION, L_JUNCTION,
                                            T_JUNCTION, CROSS_JUNCTION,
                                            COMPLEX_JUNCTION)},
            "edge_splits_performed": sum(1 for e in self.edges
                                         if e.split_reason == SPLIT_AT_NODE),
            "duplicate_resolutions": len(self.duplicates),
            "over_spread_clusters": len(self.over_spread_clusters),
            "micro_edges": len(self.micro_edges),
            "graph_components": self.components(),
            "pre_split_total_length_mm": round(pre, 1),
            "post_split_total_length_mm": round(post, 1),
            "length_difference_mm": round(post - pre, 1),
        }

    def assert_length_preserved(self, tol_mm: float = 1.0) -> None:
        """Noding changes topology. It must not create or destroy wall length."""
        d = abs(self.post_split_total_length_mm - self.pre_split_total_length_mm)
        if d > tol_mm:
            raise NodingError(
                f"noding changed total wall length by {d:.1f} mm "
                f"({self.pre_split_total_length_mm:.1f} -> "
                f"{self.post_split_total_length_mm:.1f}). Splitting divides a "
                "wall; it never lengthens or shortens one.")


# --------------------------------------------------------------- candidates

def candidate_nodes(edges: list[WallEdge], *, tol_mm: float = 60.0):
    """Every place the graph might need a node, with the reason for each."""
    pts: list[tuple[float, float, str, str]] = []
    for e in edges:
        for at in (e.start_mm, e.end_mm):
            x, y = e.point(at)
            pts.append((x, y, e.edge_id, NODE_ENDPOINT))

    for e in edges:
        for f in edges:
            if f.edge_id == e.edge_id or f.axis == e.axis:
                continue
            x, y = ((f.centreline_mm, e.centreline_mm) if e.axis == "H"
                    else (e.centreline_mm, f.centreline_mm))
            along_e = x if e.axis == "H" else y
            along_f = y if e.axis == "H" else x
            # A centreline stops at the neighbour's FACE, half a separation short
            # of its centreline, so two walls meeting at a corner never touch.
            # The reach comes from the geometry, not from a chosen constant.
            reach_e = tol_mm + f.wall_face_separation_mm / 2
            reach_f = tol_mm + e.wall_face_separation_mm / 2
            lo_e, hi_e = min(e.start_mm, e.end_mm), max(e.start_mm, e.end_mm)
            lo_f, hi_f = min(f.start_mm, f.end_mm), max(f.start_mm, f.end_mm)
            if not (lo_e - reach_e <= along_e <= hi_e + reach_e):
                continue
            if not (lo_f - reach_f <= along_f <= hi_f + reach_f):
                continue
            # Interior of e, or merely near its end? The distinction is what
            # makes a T-junction a T: the source file never divided e here.
            interior_e = lo_e + tol_mm < along_e < hi_e - tol_mm
            pts.append((x, y, e.edge_id,
                        NODE_ENDPOINT_ON_EDGE if interior_e else NODE_CROSSING))
            pts.append((x, y, f.edge_id, NODE_CROSSING))
    return pts


def cluster(points, *, tol_mm: float = 60.0, max_diameter_mm: float = 150.0):
    """Union-find on distance, with a guard against transitive over-clustering.

    A within tolerance of B, and B of C, does not make A and C one point. Naive
    chaining walks geometry across the sheet, so each cluster's diameter is
    measured and one that exceeds `max_diameter_mm` is marked OVER_SPREAD rather
    than collapsed. Edges are not split at an over-spread cluster: moving a wall
    end by more than a wall thickness to tidy a graph is how a room changes size.
    """
    n = len(points)
    parent = list(range(n))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    order = sorted(range(n), key=lambda i: points[i][0])
    for pos, i in enumerate(order):
        xi, yi = points[i][0], points[i][1]
        for j in order[pos + 1:]:
            xj, yj = points[j][0], points[j][1]
            if xj - xi > tol_mm:
                break
            if math.hypot(xj - xi, yj - yi) <= tol_mm:
                a, b = find(i), find(j)
                if a != b:
                    parent[b] = a

    groups: dict[int, list[int]] = {}
    for i in range(n):
        groups.setdefault(find(i), []).append(i)

    out: list[Node] = []
    for k, (_, idxs) in enumerate(sorted(
            groups.items(),
            key=lambda kv: (min(points[i][0] for i in kv[1]),
                            min(points[i][1] for i in kv[1]))), 1):
        xs = [points[i][0] for i in idxs]
        ys = [points[i][1] for i in idxs]
        cx, cy = sum(xs) / len(xs), sum(ys) / len(ys)
        diameter = max(
            (math.hypot(points[a][0] - points[b][0], points[a][1] - points[b][1])
             for a in idxs for b in idxs), default=0.0)
        disp = max((math.hypot(x - cx, y - cy) for x, y in zip(xs, ys)),
                   default=0.0)
        out.append(Node(
            node_id=f"WN-{k:05d}", x_mm=cx, y_mm=cy,
            reasons=tuple(sorted({points[i][3] for i in idxs})),
            member_count=len(idxs), diameter_mm=diameter,
            max_displacement_mm=disp,
            status=CLUSTER_OK if diameter <= max_diameter_mm else CLUSTER_OVER_SPREAD,
            edge_ids=tuple(sorted({points[i][2] for i in idxs}))))
    return out


# ------------------------------------------------------------------ splitting

def _along(node: Node, axis: str) -> float:
    return node.x_mm if axis == "H" else node.y_mm


def split_edges(edges: list[WallEdge], nodes: list[Node], *,
                tol_mm: float = 60.0) -> list[SplitEdge]:
    """Divide each edge at every usable interior node, keeping lineage."""
    usable = [n for n in nodes if n.status == CLUSTER_OK]
    out: list[SplitEdge] = []
    for e in edges:
        lo, hi = min(e.start_mm, e.end_mm), max(e.start_mm, e.end_mm)
        cuts: list[tuple[float, str]] = []
        for n in usable:
            if e.edge_id not in n.edge_ids:
                continue
            at = _along(n, e.axis)
            if lo + tol_mm < at < hi - tol_mm:
                cuts.append((at, n.node_id))
        cuts.sort()
        bounds = [lo] + [c[0] for c in cuts] + [hi]
        ids = [c[1] for c in cuts]
        for i, (a, b) in enumerate(zip(bounds, bounds[1:])):
            suffix = "" if len(bounds) == 2 else f"-{chr(ord('A') + i)}"
            touching = tuple(ids[max(0, i - 1):i + 1]) if ids else ()
            out.append(SplitEdge(
                edge_id=f"{e.edge_id}{suffix}", parent_edge_id=e.edge_id,
                axis=e.axis, centreline_mm=e.centreline_mm,
                start_mm=a, end_mm=b,
                face_a_mm=e.face_a_mm, face_b_mm=e.face_b_mm,
                pair_id=e.pair_id,
                wall_face_separation_mm=e.wall_face_separation_mm,
                separation_basis=e.separation_basis,
                parent_start_mm=lo, parent_end_mm=hi,
                split_reason=SPLIT_AT_NODE if len(bounds) > 2 else "",
                split_node_ids=touching,
                source_object_ids=e.source_object_ids,
                validation_status=e.validation_status))
    return out


def normalise(edges: list[SplitEdge], *, tol_mm: float = 12.0):
    """Merge exact duplicates; record partial overlaps without guessing.

    Two coincident edges would give planarization a zero-width face to walk, and
    a partial overlap is a real drafting situation that deserves a record rather
    than a silent choice.
    """
    kept: list[SplitEdge] = []
    notes: list[dict] = []
    for e in edges:
        dup = None
        for k in kept:
            if k.axis != e.axis or abs(k.centreline_mm - e.centreline_mm) > tol_mm:
                continue
            same = (abs(min(k.start_mm, k.end_mm) - min(e.start_mm, e.end_mm))
                    <= tol_mm
                    and abs(max(k.start_mm, k.end_mm) - max(e.start_mm, e.end_mm))
                    <= tol_mm)
            if same:
                dup = k
                break
            ov = (min(max(k.start_mm, k.end_mm), max(e.start_mm, e.end_mm))
                  - max(min(k.start_mm, k.end_mm), min(e.start_mm, e.end_mm)))
            if ov > tol_mm:
                notes.append({"kind": DUP_PARTIAL, "a": k.edge_id, "b": e.edge_id,
                              "overlap_mm": round(ov, 1)})
        if dup is None:
            kept.append(e)
        else:
            i = kept.index(dup)
            kept[i] = replace(dup, merged_from=tuple(
                sorted(set(dup.merged_from) | {dup.edge_id, e.edge_id})))
            notes.append({"kind": DUP_EXACT, "kept": dup.edge_id,
                          "merged": e.edge_id})
    return kept, notes


def classify_nodes(nodes: list[Node], edges: list[SplitEdge], *,
                   tol_mm: float = 60.0) -> list[Node]:
    """Degree AND orientation, computed on the POST-SPLIT graph only.

    Pre-split labels were diagnostic: an unsplit through-wall gave a T-junction
    degree 2. Incidence is recomputed here from the child edges that actually
    end at each node.
    """
    # An edge's end can legitimately stop half a wall's separation short of the
    # node, because a centreline finishes at the neighbouring wall's FACE. Using
    # the plain tolerance here missed the stem of every T-junction and reported
    # it as a CONTINUATION. The allowance is bounded by real geometry — half the
    # widest wall on the sheet — rather than chosen.
    widest = max((e.wall_face_separation_mm for e in edges), default=0.0)
    reach = tol_mm + widest / 2

    out: list[Node] = []
    for n in nodes:
        inc = [e for e in edges
               if (abs(_along(n, e.axis) - e.start_mm) <= reach
                   or abs(_along(n, e.axis) - e.end_mm) <= reach)
               and abs((e.centreline_mm - (n.y_mm if e.axis == "H" else n.x_mm)))
               <= reach]
        eids = tuple(sorted(e.edge_id for e in inc))
        axes = {e.axis for e in inc}
        d = len(eids)
        if d <= 1:
            kind = TERMINUS
        elif d == 2:
            kind = CONTINUATION if len(axes) == 1 else L_JUNCTION
        elif d == 3:
            kind = T_JUNCTION if len(axes) == 2 else COMPLEX_JUNCTION
        elif d == 4:
            kind = CROSS_JUNCTION if len(axes) == 2 else COMPLEX_JUNCTION
        else:
            kind = COMPLEX_JUNCTION
        out.append(replace(n, edge_ids=eids, kind=kind))
    return out


def node_and_split(graph: WallGraph, *, tol_mm: float = 60.0,
                   max_diameter_mm: float = 150.0) -> NodedGraph:
    """The whole pipeline, in the order the review specified.

    candidates -> cluster (with over-spread guard) -> split -> normalise ->
    incidence -> classify. Degree is computed last, on the split graph, because
    only the split graph knows it.
    """
    # Clustering and incidence must use the SAME allowance. With clustering at
    # the plain tolerance and incidence at the wider separation-derived reach,
    # two candidate points 100 mm apart on one wall line stayed two nodes while
    # both saw the same edges — producing a duplicate T-junction a wall-thickness
    # away from the real one. The allowance is half the widest wall on the sheet,
    # which is the distance a centreline can legitimately stop short.
    widest = max((e.wall_face_separation_mm for e in graph.edges), default=0.0)
    reach = tol_mm + widest / 2
    pts = candidate_nodes(graph.edges, tol_mm=tol_mm)
    nodes = cluster(pts, tol_mm=reach,
                    max_diameter_mm=max(max_diameter_mm, reach * 2))
    children = split_edges(graph.edges, nodes, tol_mm=tol_mm)
    kept, dup_notes = normalise(children)
    classified = classify_nodes(nodes, kept, tol_mm=tol_mm)
    g = NodedGraph(
        nodes=classified, edges=kept, duplicates=dup_notes,
        pre_split_total_length_mm=sum(e.length_mm for e in graph.edges),
        over_spread_clusters=[n.node_id for n in nodes
                              if n.status == CLUSTER_OVER_SPREAD])
    return g
