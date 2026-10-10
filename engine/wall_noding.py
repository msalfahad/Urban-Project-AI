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

THE PRINCIPLE THIS MODULE IS BUILT UNDER, learned from four reversals:

    DO NOT PROMOTE A PROXY INTO PHYSICAL TRUTH.

    same raster region            is not   "not a doorway"
    60-120 mm separation          is not   "not masonry"
    same region on both sides     is not   "validated doorway"
    three correlated observations are not  three independent proofs
    degree 4                      is not   "a four-way crossing"

The chain is OBSERVATION -> EVIDENCE -> HYPOTHESIS -> INDEPENDENT VALIDATION ->
PHYSICAL INTERPRETATION -> QUANTITY, and every step in it is somewhere a proxy
can be mistaken for the thing itself.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field, replace

from engine.wall_graph import (COMPLEX_JUNCTION, CONTINUATION, CROSS_JUNCTION,
                               L_JUNCTION, TERMINUS, T_JUNCTION, WallEdge,
                               WallGraph)

# Two wall representations overlapping at a building corner is mathematically a
# degree-4 node and physically an L. Calling it a cross gives planar extraction
# four outgoing half-edges where there are two, and false half-edges make false
# faces. The test is which SECTORS around the node are actually occupied: a true
# crossing occupies all four, a corner overlap only two adjacent ones.
TRUE_CROSS_JUNCTION = "TRUE_CROSS_JUNCTION"
CORNER_OVERLAP = "CORNER_OVERLAP"
UNRESOLVED_JUNCTION = "UNRESOLVED_JUNCTION"

# Why a node exists. Endpoint-on-edge is the one the source file does not give us.
NODE_ENDPOINT = "EDGE_ENDPOINT"
NODE_CROSSING = "PERPENDICULAR_CROSSING"
NODE_ENDPOINT_ON_EDGE = "ENDPOINT_ON_EDGE_INTERIOR"

# Why an edge was divided.
SPLIT_AT_NODE = "SPLIT_AT_INTERIOR_NODE"

# Cluster health. A cluster that is too spread out to be one point is
# SUBDIVIDED first — refusal is the last answer, not the first one. Only a
# cluster that stays one dense smear after subdivision is refused, and a
# borderline one is held as AMBIGUOUS rather than forced either way.
CLUSTER_VALID = "VALID_CLUSTER"
CLUSTER_AMBIGUOUS = "AMBIGUOUS_CLUSTER"
CLUSTER_REJECTED = "REJECTED_CLUSTER"

# Older readers of this module used these two names. They are the same states.
CLUSTER_OK = CLUSTER_VALID
CLUSTER_OVER_SPREAD = CLUSTER_REJECTED

# Subdivision halves the tolerance until the sub-clusters fit, but it stops
# here. Below this, "separate nodes" stops meaning anything physical: no CAD
# file distinguishes two wall ends 4 mm apart on purpose.
MIN_CLUSTER_TOL_MM = 5.0

# Duplicate handling.
DUP_EXACT = "EXACT_DUPLICATE_MERGED"
DUP_PARTIAL = "PARTIAL_OVERLAP_RECORDED"

# An edge short enough to be suspicious. This is a REVIEW TRIGGER, never a
# deletion threshold: a flagged edge may be a real narrow feature, a numerical
# artefact, duplicate geometry or a tolerance artefact, and only the four are
# told apart by topology, not by length. The trigger is local — a fragment
# shorter than the wall it belongs to is thick is not a wall run — with this
# floor for thin partitions.
MICRO_EDGE_MM = 50.0

# What to do about a flagged fragment. A recommendation, not an action: nothing
# in this module deletes an edge.
MICRO_KEEP = "KEEP_REAL_OR_UNPROVEN_FEATURE"
MICRO_COLLAPSIBLE = "COLLAPSIBLE_WITHOUT_TOPOLOGY_CHANGE"
MICRO_UNRESOLVED = "MICRO_EDGE_UNRESOLVED"

# Why two coordinate clusters turned out to be one junction.
MERGE_TRUNCATED_END = "TRUNCATED_END_AT_EXISTING_JUNCTION"

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
    status: str = CLUSTER_VALID
    edge_ids: tuple[str, ...] = ()
    kind: str = UNRESOLVED
    subdivision_depth: int = 0
    merged_node_ids: tuple[str, ...] = ()

    @property
    def degree(self) -> int:
        return len(self.edge_ids)

    @property
    def usable(self) -> bool:
        """Only a VALID node may cut a wall. Fail closed on the other two."""
        return self.status == CLUSTER_VALID

    def record(self) -> dict:
        return {"node_id": self.node_id, "x_mm": round(self.x_mm, 1),
                "y_mm": round(self.y_mm, 1), "kind": self.kind,
                "degree": self.degree, "reasons": list(self.reasons),
                "member_count": self.member_count,
                "diameter_mm": round(self.diameter_mm, 1),
                "max_displacement_mm": round(self.max_displacement_mm, 1),
                "status": self.status, "edge_ids": list(self.edge_ids),
                "subdivision_depth": self.subdivision_depth,
                "merged_node_ids": list(self.merged_node_ids)}


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
    def micro_threshold_mm(self) -> float:
        """Local, not global. A fragment shorter than its own wall is thick is
        not a wall run, whatever an absolute millimetre figure would say."""
        return max(MICRO_EDGE_MM, self.wall_face_separation_mm)

    @property
    def is_micro(self) -> bool:
        """Flagged for review. Nothing here deletes it — see micro_edge_policy."""
        return self.length_mm < self.micro_threshold_mm

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
                "micro_threshold_mm": round(self.micro_threshold_mm, 1),
                "validation_status": self.validation_status}


@dataclass
class NodedGraph:
    nodes: list[Node] = field(default_factory=list)
    edges: list[SplitEdge] = field(default_factory=list)
    duplicates: list[dict] = field(default_factory=list)
    pre_split_total_length_mm: float = 0.0
    over_spread_clusters: list[str] = field(default_factory=list)
    ambiguous_clusters: list[str] = field(default_factory=list)
    node_merges: list[dict] = field(default_factory=list)

    @property
    def post_split_total_length_mm(self) -> float:
        return sum(e.length_mm for e in self.edges)

    @property
    def duplicate_removed_length_mm(self) -> float:
        """Length that left the graph because it was counted twice.

        Merging a coincident edge is not splitting, and the length invariant
        must not be allowed to absorb it silently in either direction: the
        length is accounted for here, edge by edge, with the pair that was
        merged named in `duplicates`.
        """
        return sum(n.get("removed_length_mm", 0.0) for n in self.duplicates
                   if n["kind"] == DUP_EXACT)

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

    def micro_edge_policy(self) -> list[dict]:
        """Classify each flagged fragment. Recommend; never delete.

        The question is not "is it short" — it is "would removing it change the
        topology". A fragment between two junctions that each carry a third wall
        is load-bearing for the graph: collapsing it would fuse two distinct
        junctions into one and silently move a wall. Only a fragment whose two
        ends carry nothing but the fragment and its own collinear continuation
        can be collapsed without changing what meets what, and even then the
        decision is recorded for a human, not applied here.
        """
        deg: dict[str, list[Node]] = {}
        for n in self.nodes:
            for eid in n.edge_ids:
                deg.setdefault(eid, []).append(n)
        out: list[dict] = []
        for e in self.micro_edges:
            ends = [n for n in deg.get(e.edge_id, ())
                    if min(abs(_along(n, e.axis) - e.start_mm),
                           abs(_along(n, e.axis) - e.end_mm))
                    <= e.micro_threshold_mm + 1.0]
            junction_ends = [n for n in ends if n.degree >= 3]
            if junction_ends:
                decision, why = MICRO_KEEP, (
                    "both ends or one end is a junction carrying a third wall; "
                    "collapsing would fuse two distinct junctions")
            elif len(ends) >= 2 and all(n.degree <= 2 for n in ends):
                decision, why = MICRO_COLLAPSIBLE, (
                    "no third wall at either end, so collapsing changes no "
                    "incidence — recommendation only, not applied")
            else:
                decision, why = MICRO_UNRESOLVED, (
                    "the fragment's ends are not both resolved to nodes, so the "
                    "topology consequence of collapsing it is unknown")
            out.append({"edge_id": e.edge_id, "parent_edge_id": e.parent_edge_id,
                        "length_mm": round(e.length_mm, 1),
                        "threshold_mm": round(e.micro_threshold_mm, 1),
                        "end_degrees": sorted(n.degree for n in ends),
                        "decision": decision, "reason": why})
        return out

    def health(self) -> dict:
        from collections import Counter
        kinds = Counter(n.kind for n in self.nodes)
        pre = self.pre_split_total_length_mm
        post = self.post_split_total_length_mm
        removed = self.duplicate_removed_length_mm
        return {
            "nodes": len(self.nodes), "edges": len(self.edges),
            **{k: kinds.get(k, 0) for k in (TERMINUS, CONTINUATION, L_JUNCTION,
                                            T_JUNCTION, CROSS_JUNCTION,
                                            TRUE_CROSS_JUNCTION, CORNER_OVERLAP,
                                            UNRESOLVED_JUNCTION,
                                            COMPLEX_JUNCTION)},
            "edge_splits_performed": sum(1 for e in self.edges
                                         if e.split_reason == SPLIT_AT_NODE),
            "duplicate_resolutions": len(self.duplicates),
            "duplicate_removed_length_mm": round(removed, 1),
            "node_merges": len(self.node_merges),
            "subdivided_clusters": sum(1 for n in self.nodes
                                       if n.subdivision_depth > 0),
            "ambiguous_clusters": len(self.ambiguous_clusters),
            "rejected_clusters": len(self.over_spread_clusters),
            "over_spread_clusters": len(self.over_spread_clusters),
            "micro_edges": len(self.micro_edges),
            "micro_edges_collapsible": sum(
                1 for m in self.micro_edge_policy()
                if m["decision"] == MICRO_COLLAPSIBLE),
            "graph_components": self.components(),
            "pre_split_total_length_mm": round(pre, 1),
            "post_split_total_length_mm": round(post, 1),
            # post + removed, which is what the invariant is stated over.
            "length_accounted_mm": round(post + removed, 1),
            "length_difference_mm": round(post + removed - pre, 1),
        }

    def assert_length_preserved(self, tol_mm: float = 1.0) -> None:
        """Noding changes topology. It must not create or destroy wall length.

        Splitting is held to this exactly. Duplicate removal is the one thing
        that legitimately takes length out of the graph — it was in twice — so
        it is added back here rather than widened into the tolerance: the
        invariant stays strict and the removal stays visible and itemised.
        """
        accounted = (self.post_split_total_length_mm
                     + self.duplicate_removed_length_mm)
        d = abs(accounted - self.pre_split_total_length_mm)
        if d > tol_mm:
            raise NodingError(
                f"noding changed total wall length by {d:.1f} mm "
                f"({self.pre_split_total_length_mm:.1f} -> "
                f"{self.post_split_total_length_mm:.1f} plus "
                f"{self.duplicate_removed_length_mm:.1f} removed as duplicate). "
                "Splitting divides a wall; it never lengthens or shortens one.")


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


def _groups(points, idxs, tol_mm: float) -> list[list[int]]:
    """Union-find on distance over a subset of candidate points."""
    parent = {i: i for i in idxs}

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    order = sorted(idxs, key=lambda i: points[i][0])
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

    out: dict[int, list[int]] = {}
    for i in idxs:
        out.setdefault(find(i), []).append(i)
    return list(out.values())


def _spread(points, idxs) -> tuple[float, float, float, float]:
    xs = [points[i][0] for i in idxs]
    ys = [points[i][1] for i in idxs]
    cx, cy = sum(xs) / len(xs), sum(ys) / len(ys)
    diameter = max(
        (math.hypot(points[a][0] - points[b][0], points[a][1] - points[b][1])
         for a in idxs for b in idxs), default=0.0)
    disp = max((math.hypot(x - cx, y - cy) for x, y in zip(xs, ys)), default=0.0)
    return cx, cy, diameter, disp


def _resolve(points, idxs, tol_mm: float, max_diameter_mm: float, depth: int):
    """Subdivide an over-spread cluster before refusing it.

    A within tolerance of B, and B of C, does not make A and C one point — but
    neither does it make the whole chain unusable. Halve the tolerance and ask
    again: five wall ends 50 mm apart in a line are five nodes, not one refusal.
    Refusal is reserved for a smear that stays one blob all the way down to
    MIN_CLUSTER_TOL_MM, where "two separate nodes" has stopped meaning anything
    physical. Yields (idxs, status, depth) triples.
    """
    _, _, diameter, _ = _spread(points, idxs)
    if diameter <= max_diameter_mm:
        yield idxs, CLUSTER_VALID, depth
        return
    finer = tol_mm / 2
    if finer >= MIN_CLUSTER_TOL_MM:
        parts = _groups(points, idxs, finer)
        if len(parts) > 1:
            for part in parts:
                yield from _resolve(points, part, finer, max_diameter_mm,
                                    depth + 1)
            return
        # One group at half the tolerance too: keep halving rather than refuse.
        yield from _resolve(points, idxs, finer, max_diameter_mm, depth)
        return
    # Dense all the way down and still wider than one node may be. Held, not
    # forced: AMBIGUOUS is reviewable, REJECTED is beyond argument.
    yield idxs, (CLUSTER_AMBIGUOUS if diameter <= max_diameter_mm * 2
                 else CLUSTER_REJECTED), depth


def cluster(points, *, tol_mm: float = 60.0, max_diameter_mm: float = 150.0):
    """Group candidate points into nodes, subdividing before refusing.

    This answers ONE question: are these two candidate points the same physical
    location? That is a coordinate question and it takes a coordinate tolerance.
    Whether a wall reaches the node it produced is a different question with a
    different allowance, and it is asked in `classify_nodes`. Conflating the two
    is how a 400 mm external wall came to loosen node detection around every
    100 mm partition on the sheet.
    """
    n = len(points)
    resolved: list[tuple[list[int], str, int]] = []
    for g in _groups(points, list(range(n)), tol_mm):
        resolved.extend(_resolve(points, g, tol_mm, max_diameter_mm, 0))

    out: list[Node] = []
    for k, (idxs, status, depth) in enumerate(sorted(
            resolved,
            key=lambda r: (min(points[i][0] for i in r[0]),
                           min(points[i][1] for i in r[0]))), 1):
        cx, cy, diameter, disp = _spread(points, idxs)
        out.append(Node(
            node_id=f"WN-{k:05d}", x_mm=cx, y_mm=cy,
            reasons=tuple(sorted({points[i][3] for i in idxs})),
            member_count=len(idxs), diameter_mm=diameter,
            max_displacement_mm=disp, status=status, subdivision_depth=depth,
            edge_ids=tuple(sorted({points[i][2] for i in idxs}))))
    return out


def consolidate(nodes: list[Node], edges: list[WallEdge], *,
                tol_mm: float = 60.0):
    """Ask the WALL question the coordinate question could not answer.

    A stem's centreline stops at the through-wall's face, half a separation
    short of the through-wall's centreline, so the stem's endpoint and the
    computed crossing are two coordinate clusters of one junction. Merging them
    by loosening the coordinate tolerance would loosen it everywhere; the test
    instead is incidence: one cluster's walls are a SUBSET of the other's, and
    it lies within the separation those same walls imply.

    Two stems 100 mm apart on one through-wall each carry a wall the other does
    not, so neither is a subset and they stay two junctions. Proximity alone
    never merges anything.
    """
    sep = {e.edge_id: e.wall_face_separation_mm for e in edges}
    order = sorted(nodes, key=lambda n: (-len(n.edge_ids), n.node_id))
    absorbed: dict[str, str] = {}
    members: dict[str, list[Node]] = {n.node_id: [n] for n in nodes}
    notes: list[dict] = []

    for host in order:
        if host.node_id in absorbed:
            continue
        for other in order:
            if other.node_id == host.node_id or other.node_id in absorbed:
                continue
            small, big = set(other.edge_ids), set(host.edge_ids)
            # Subset, not proximity. `order` puts the larger incidence set (then
            # the lower id) first, so the survivor is deterministic.
            if not small or not small <= big:
                continue
            local = max([sep.get(x, 0.0) for x in small | big], default=0.0)
            reach = tol_mm + local / 2
            d = math.hypot(other.x_mm - host.x_mm, other.y_mm - host.y_mm)
            if d > reach:
                continue
            absorbed[other.node_id] = host.node_id
            members[host.node_id].append(other)
            notes.append({"kind": MERGE_TRUNCATED_END, "kept": host.node_id,
                          "merged": other.node_id, "distance_mm": round(d, 1),
                          "allowance_mm": round(reach, 1)})

    out: list[Node] = []
    for n in nodes:
        if n.node_id in absorbed:
            continue
        group = members[n.node_id]
        if len(group) == 1:
            out.append(n)
            continue
        xs = [g.x_mm for g in group]
        ys = [g.y_mm for g in group]
        cx, cy = sum(xs) / len(xs), sum(ys) / len(ys)
        diameter = max(math.hypot(a.x_mm - b.x_mm, a.y_mm - b.y_mm)
                       for a in group for b in group)
        out.append(replace(
            n, x_mm=cx, y_mm=cy,
            reasons=tuple(sorted({r for g in group for r in g.reasons})),
            member_count=sum(g.member_count for g in group),
            diameter_mm=max(diameter, max(g.diameter_mm for g in group)),
            max_displacement_mm=max(
                [g.max_displacement_mm for g in group]
                + [math.hypot(g.x_mm - cx, g.y_mm - cy) for g in group]),
            edge_ids=tuple(sorted({e for g in group for e in g.edge_ids})),
            merged_node_ids=tuple(sorted(g.node_id for g in group
                                         if g.node_id != n.node_id))))
    return out, notes


# ------------------------------------------------------------------ splitting

def _along(node: Node, axis: str) -> float:
    return node.x_mm if axis == "H" else node.y_mm


def split_edges(edges: list[WallEdge], nodes: list[Node], *,
                tol_mm: float = 60.0) -> list[SplitEdge]:
    """Divide each edge at every usable interior node, keeping lineage."""
    usable = [n for n in nodes if n.usable]
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
                          "merged": e.edge_id,
                          "removed_length_mm": round(e.length_mm, 1)})
    return kept, notes


def _sectors(node: Node, inc: list[SplitEdge], tol_mm: float) -> set[str]:
    """Which of N/S/E/W the incident edges actually extend into — as ARMS.

    This is what separates a true crossing from a corner overlap, and the word
    that does the work is "arms". At a building corner the two wall
    representations run past each other to the far FACE of the wall they meet,
    so each centreline overhangs the node by half the other wall's separation.
    That overhang is not an arm of a crossing. It is the same geometry that
    makes a centreline stop short at a T — read from the other end.

    So the allowance is local and derived: a sector counts as occupied only when
    the edge extends past the node by more than the CROSSING wall's own half
    separation. A real four-way crossing has arms far longer than that; a corner
    overlap has nothing but the overhang. Degree cannot tell them apart, which
    is the whole point — degree 4 is not "a four-way crossing".
    """
    out: set[str] = set()
    for e in inc:
        # The wall this one crosses is the one on the other axis. Its half
        # separation is exactly how far a centreline legitimately runs past.
        crossing = [f.wall_face_separation_mm for f in inc if f.axis != e.axis]
        stub = tol_mm + (max(crossing) / 2 if crossing else 0.0)
        at = _along(node, e.axis)
        lo, hi = min(e.start_mm, e.end_mm), max(e.start_mm, e.end_mm)
        if hi - at > stub:
            out.add("E" if e.axis == "H" else "S")
        if at - lo > stub:
            out.add("W" if e.axis == "H" else "N")
    return out


def _kind_from(node: Node, inc: list[SplitEdge], tol_mm: float) -> str:
    """Degree, orientation AND occupied sectors — never degree alone."""
    d = len(inc)
    axes = {e.axis for e in inc}
    if d <= 1:
        return TERMINUS
    sec = _sectors(node, inc, tol_mm)
    if d == 2:
        return CONTINUATION if len(axes) == 1 else L_JUNCTION
    if d == 3:
        if len(axes) != 2:
            return COMPLEX_JUNCTION
        return T_JUNCTION if len(sec) >= 3 else CORNER_OVERLAP
    if d == 4 and len(axes) == 2:
        if len(sec) == 4:
            return TRUE_CROSS_JUNCTION
        if len(sec) == 2:
            return CORNER_OVERLAP          # two walls crossing past each other
        return T_JUNCTION if len(sec) == 3 else UNRESOLVED_JUNCTION
    return COMPLEX_JUNCTION


def classify_nodes(nodes: list[Node], edges: list[SplitEdge], *,
                   tol_mm: float = 60.0) -> list[Node]:
    """Degree, orientation and occupied sectors, on the POST-SPLIT graph only.

    Pre-split labels were diagnostic: an unsplit through-wall gave a T-junction
    degree 2. Incidence is recomputed here from the child edges that actually
    end at each node.

    The incidence allowance is LOCAL. It was half the widest wall on the whole
    sheet, which let one 400 mm external wall loosen detection around every
    100 mm partition. It is now derived per relationship, from the separations of
    the edges being tested, so a thin partition is judged by thin-partition
    geometry.
    """
    by_id = {e.edge_id: e for e in edges}
    out: list[Node] = []
    for n in nodes:
        inc = []
        for e in edges:
            # Local allowance: this edge's own separation, plus the separation of
            # whatever else already reaches this node. Never the sheet maximum.
            local = max([e.wall_face_separation_mm]
                        + [by_id[x].wall_face_separation_mm
                           for x in n.edge_ids if x in by_id], default=0.0)
            reach = tol_mm + local / 2
            at = _along(n, e.axis)
            cross = n.y_mm if e.axis == "H" else n.x_mm
            if abs(e.centreline_mm - cross) > reach:
                continue
            if min(abs(at - e.start_mm), abs(at - e.end_mm)) <= reach:
                inc.append(e)
        eids = tuple(sorted(e.edge_id for e in inc))
        out.append(replace(n, edge_ids=eids, kind=_kind_from(n, inc, tol_mm)))
    return out


def node_and_split(graph: WallGraph, *, tol_mm: float = 60.0,
                   max_diameter_mm: float = 150.0,
                   coord_tol_mm: float | None = None) -> NodedGraph:
    """The whole pipeline, in the order the review specified.

    candidates -> cluster (coordinate identity, subdividing before refusing) ->
    consolidate (wall incidence, local) -> split -> normalise -> incidence ->
    classify. Degree is computed last, on the split graph, because only the
    split graph knows it.
    """
    # TWO DIFFERENT QUESTIONS, TWO DIFFERENT ALLOWANCES.
    #
    #   coordinate clustering  are these two candidate points the same place?
    #   wall incidence         does this wall actually reach that place?
    #
    # These were one allowance — half the widest wall on the whole sheet — and
    # that let one 400 mm external wall loosen node detection around every
    # 100 mm partition in the building. Clustering now uses a plain coordinate
    # tolerance. The gap it leaves (a stem's centreline stops at the through
    # wall's FACE, so its endpoint and the crossing are two clusters) is closed
    # by `consolidate`, which asks the wall question with LOCAL geometry, and
    # only for clusters that share walls.
    coord = tol_mm if coord_tol_mm is None else coord_tol_mm
    pts = candidate_nodes(graph.edges, tol_mm=tol_mm)
    nodes = cluster(pts, tol_mm=coord, max_diameter_mm=max_diameter_mm)
    nodes, merges = consolidate(nodes, graph.edges, tol_mm=tol_mm)
    children = split_edges(graph.edges, nodes, tol_mm=tol_mm)
    kept, dup_notes = normalise(children)
    classified = classify_nodes(nodes, kept, tol_mm=tol_mm)
    g = NodedGraph(
        nodes=classified, edges=kept, duplicates=dup_notes, node_merges=merges,
        pre_split_total_length_mm=sum(e.length_mm for e in graph.edges),
        over_spread_clusters=[n.node_id for n in nodes
                              if n.status == CLUSTER_REJECTED],
        ambiguous_clusters=[n.node_id for n in nodes
                            if n.status == CLUSTER_AMBIGUOUS])
    return g
