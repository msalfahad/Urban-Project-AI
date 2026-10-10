"""The vector wall graph — walls, their junctions, and what a gap means in context.

Two things this replaces.

Gaps were classified in isolation. A collinear pair of faces that stops and
resumes was treated as a possible opening wherever it happened, and on AR-00
that produced 21 candidates wider than two metres. A wall ending at a corner
interrupts both its faces in exactly the way a doorway does; the difference is
only visible in the topology. So a gap is now classified RELATIVE TO THE GRAPH:
if a perpendicular wall arrives at the break, it is a junction.

And separation was called thickness. It is not. The distance between two drawn
faces may be finish-to-finish, a block wall, a light partition, a door leaf, a
cabinet or an annotation, and 60-120 mm covers a genuine thin partition as
readily as a fixture. The field is `wall_face_separation_mm` and it stays that
until a wall basis proves what the separation represents. No band is excluded on
its own; thickness is evidence, never a classification.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from decimal import Decimal

# Junction kinds. A terminus is a real answer: a wall that ends at nothing is
# either an opening edge, a drawing boundary, or a face the pairing missed.
L_JUNCTION = "L_JUNCTION"
T_JUNCTION = "T_JUNCTION"
CROSS_JUNCTION = "CROSS_JUNCTION"
COMPLEX_JUNCTION = "COMPLEX_JUNCTION"
CONTINUATION = "CONTINUATION"
TERMINUS = "TERMINUS"
OPENING_EDGE = "OPENING_EDGE"
JUNCTION_KINDS = (TERMINUS, CONTINUATION, L_JUNCTION, T_JUNCTION,
                  CROSS_JUNCTION, COMPLEX_JUNCTION, OPENING_EDGE)

# Why a break in a wall run exists. The distinction the graph adds.
BREAK_JUNCTION = "BREAK_AT_JUNCTION"
BREAK_OPENING = "BREAK_IS_CANDIDATE_OPENING"
BREAK_UNRESOLVED = "BREAK_UNRESOLVED"

VALIDATED = "VALIDATED"
PROBABLE = "PROBABLE"
AMBIGUOUS = "AMBIGUOUS"
UNRESOLVED = "UNRESOLVED"


class WallGraphError(RuntimeError):
    """The graph could not be built from the geometry supplied."""


@dataclass(frozen=True)
class WallEdge:
    """One wall, as a centreline run with both its faces recorded."""

    edge_id: str
    axis: str                          # H or V
    centreline_mm: float
    start_mm: float
    end_mm: float
    face_a_mm: float
    face_b_mm: float
    pair_id: str = ""
    # Never "thickness". What the separation MEANS is a later question.
    wall_face_separation_mm: float = 0.0
    separation_basis: str = "VECTOR_PAIRED_FACES"
    validation_status: str = PROBABLE
    source_object_ids: tuple = ()

    @property
    def length_mm(self) -> float:
        return abs(self.end_mm - self.start_mm)

    def point(self, at_mm: float) -> tuple[float, float]:
        """(x, y) of a position along this wall."""
        return ((at_mm, self.centreline_mm) if self.axis == "H"
                else (self.centreline_mm, at_mm))

    def record(self) -> dict:
        return {"edge_id": self.edge_id, "axis": self.axis, "pair_id": self.pair_id,
                "centreline_mm": round(self.centreline_mm, 1),
                "start_mm": round(self.start_mm, 1), "end_mm": round(self.end_mm, 1),
                "length_mm": round(self.length_mm, 1),
                "face_a_mm": round(self.face_a_mm, 1),
                "face_b_mm": round(self.face_b_mm, 1),
                "wall_face_separation_mm": round(self.wall_face_separation_mm, 1),
                "separation_basis": self.separation_basis,
                "validation_status": self.validation_status}


@dataclass
class Junction:
    """Where walls meet, or where one stops."""

    junction_id: str
    x_mm: float
    y_mm: float
    kind: str
    edge_ids: tuple = ()

    @property
    def degree(self) -> int:
        return len(self.edge_ids)

    def record(self) -> dict:
        return {"junction_id": self.junction_id, "x_mm": round(self.x_mm, 1),
                "y_mm": round(self.y_mm, 1), "kind": self.kind,
                "degree": self.degree, "edge_ids": list(self.edge_ids)}


@dataclass
class WallGraph:
    edges: list[WallEdge] = field(default_factory=list)
    junctions: list[Junction] = field(default_factory=list)

    def by_edge(self) -> dict[str, WallEdge]:
        return {e.edge_id: e for e in self.edges}

    def counts(self) -> dict[str, int]:
        from collections import Counter
        c = Counter(j.kind for j in self.junctions)
        return {"edges": len(self.edges), "junctions": len(self.junctions),
                **{k: c.get(k, 0) for k in JUNCTION_KINDS}}

    def separation_bands(self) -> dict[str, int]:
        """Every band reported, none excluded. Thickness is evidence."""
        from collections import Counter
        def band(s):
            return ("<60" if s < 60 else "60-120" if s < 120 else
                    "120-180" if s < 180 else "180-260" if s < 260 else
                    "260-400" if s <= 400 else ">400")
        return dict(Counter(band(e.wall_face_separation_mm) for e in self.edges))


def _cluster(points: list[tuple[float, float, str]], tol_mm: float):
    """Group points by proximity with union-find, not by snapping to a grid.

    Grid snapping was adequate for diagnostics and is not adequate for planar
    topology. Two endpoints 10 mm apart can fall either side of a cell boundary
    and become two junctions, and E31A would then see a false terminus, an open
    loop and a missing face where there is a perfectly good corner. Distance
    decides membership here, so two points within the tolerance are always one
    node however they sit relative to any grid.
    """
    n = len(points)
    parent = list(range(n))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def union(i, j):
        a, b = find(i), find(j)
        if a != b:
            parent[b] = a

    # Sort by x so the sweep only compares points that can be close enough.
    order = sorted(range(n), key=lambda i: points[i][0])
    for a_pos, i in enumerate(order):
        xi, yi, _ = points[i]
        for j in order[a_pos + 1:]:
            xj, yj, _ = points[j]
            if xj - xi > tol_mm:
                break
            if math.hypot(xj - xi, yj - yi) <= tol_mm:
                union(i, j)

    groups: dict[int, list[int]] = {}
    for i in range(n):
        groups.setdefault(find(i), []).append(i)
    return groups


def _junction_kind(edges_at: list[WallEdge], *, collinear_tol_deg: float = 15.0
                   ) -> str:
    """Degree AND orientation. Degree alone calls a straight run a corner.

    Two walls meeting at a node may be an L — or they may be one wall drawn as
    two collinear pieces, which is a CONTINUATION and not a corner at all. E31A
    treats those differently: a continuation does not bound a face, a corner
    does.
    """
    d = len(edges_at)
    if d <= 1:
        return TERMINUS
    axes = {e.axis for e in edges_at}
    if d == 2:
        return CONTINUATION if len(axes) == 1 else L_JUNCTION
    if d == 3:
        return T_JUNCTION if len(axes) == 2 else COMPLEX_JUNCTION
    if d == 4:
        return CROSS_JUNCTION if len(axes) == 2 else COMPLEX_JUNCTION
    return COMPLEX_JUNCTION


def build(pairs, *, tol_mm: float = 60.0) -> WallGraph:
    """Turn wall pairs into edges, then node them geometrically.

    Nodes come from three places, and the third is the one planar topology needs:
    edge endpoints, perpendicular crossings, and endpoints that land on another
    edge's BODY rather than on its end. Relying on original vector endpoints
    alone leaves a T-junction unnoded, and an unnoded T leaves a face open.

    THIS GRAPH IS NOT SPLIT, and it stays that way on purpose. A true
    T-junction is a through-wall plus a stem, so here the meeting point has
    degree 2 and `_junction_kind` reports L_JUNCTION rather than T_JUNCTION. The
    node is found and positioned correctly; only the degree is understated. Read
    the L/T/CROSS labels from this function as "walls meet here", never as a
    count of how many.

    `engine.wall_noding.node_and_split` does the splitting and owns the
    authoritative degree, junction kind and length invariant. Anything that
    needs to know what meets what — planar face extraction above all — must use
    that graph, not this one.
    """
    g = WallGraph()
    for i, p in enumerate(pairs, 1):
        g.edges.append(WallEdge(
            edge_id=f"WE-{i:04d}", axis=p.axis, centreline_mm=p.centreline_mm,
            start_mm=p.start_mm, end_mm=p.end_mm,
            face_a_mm=p.face_a_mm, face_b_mm=p.face_b_mm, pair_id=p.pair_id,
            wall_face_separation_mm=p.thickness_mm))

    pts: list[tuple[float, float, str]] = []
    for e in g.edges:
        for at in (e.start_mm, e.end_mm):
            x, y = e.point(at)
            pts.append((x, y, e.edge_id))

    # Perpendicular crossings, and endpoints landing on another edge's body.
    # Both must become nodes or planarization leaves faces open.
    for e in g.edges:
        for f in g.edges:
            if f.axis == e.axis or f.edge_id == e.edge_id:
                continue
            if e.axis == "H":
                x, y = f.centreline_mm, e.centreline_mm
            else:
                x, y = e.centreline_mm, f.centreline_mm
            along_e = x if e.axis == "H" else y
            along_f = y if e.axis == "H" else x
            # A centreline legitimately stops at the NEIGHBOUR'S FACE, which sits
            # half that wall's separation short of its centreline. Two walls
            # meeting at a corner therefore have centrelines that never touch,
            # and testing containment without allowing for it turned every corner
            # on the test fixture into two termini. The reach is derived from the
            # geometry rather than picked: half the other wall's separation.
            reach_e = tol_mm + f.wall_face_separation_mm / 2
            reach_f = tol_mm + e.wall_face_separation_mm / 2
            on_e = (min(e.start_mm, e.end_mm) - reach_e <= along_e
                    <= max(e.start_mm, e.end_mm) + reach_e)
            on_f = (min(f.start_mm, f.end_mm) - reach_f <= along_f
                    <= max(f.start_mm, f.end_mm) + reach_f)
            if on_e and on_f:
                pts.append((x, y, e.edge_id))
                pts.append((x, y, f.edge_id))

    by_edge = g.by_edge()
    for n, (_, idxs) in enumerate(sorted(
            _cluster(pts, tol_mm).items(),
            key=lambda kv: (points_key := (min(pts[i][0] for i in kv[1]),
                                           min(pts[i][1] for i in kv[1])))), 1):
        xs = [pts[i][0] for i in idxs]
        ys = [pts[i][1] for i in idxs]
        eids = tuple(sorted({pts[i][2] for i in idxs}))
        kind = _junction_kind([by_edge[e] for e in eids])
        g.junctions.append(Junction(f"WJ-{n:04d}", sum(xs) / len(xs),
                                    sum(ys) / len(ys), kind, eids))
    return g


def perpendicular_at(graph: WallGraph, axis: str, centreline_mm: float,
                     at_mm: float, *, tol_mm: float = 200.0) -> list[str]:
    """Edges perpendicular to this wall that arrive at this point along it.

    This is the test that separates a corner from a doorway. A break with a
    perpendicular wall arriving at it is a junction; a break with nothing there
    is a candidate opening.
    """
    x, y = ((at_mm, centreline_mm) if axis == "H" else (centreline_mm, at_mm))
    out = []
    for e in graph.edges:
        if e.axis == axis:
            continue
        ex, ey = (e.centreline_mm, None) if e.axis == "V" else (None, e.centreline_mm)
        if e.axis == "V":
            if abs(e.centreline_mm - x) > tol_mm:
                continue
            if not (min(e.start_mm, e.end_mm) - tol_mm <= y
                    <= max(e.start_mm, e.end_mm) + tol_mm):
                continue
        else:
            if abs(e.centreline_mm - y) > tol_mm:
                continue
            if not (min(e.start_mm, e.end_mm) - tol_mm <= x
                    <= max(e.start_mm, e.end_mm) + tol_mm):
                continue
        out.append(e.edge_id)
    return out


def classify_break(graph: WallGraph, axis: str, centreline_mm: float,
                   start_mm: float, end_mm: float, *, tol_mm: float = 200.0
                   ) -> tuple[str, dict]:
    """Is this break in a wall run a junction, or a candidate opening?

    Reported with the evidence, because "there is a perpendicular wall here" and
    "there is nothing here" are both worth being able to read back.
    """
    at_start = perpendicular_at(graph, axis, centreline_mm, start_mm, tol_mm=tol_mm)
    at_end = perpendicular_at(graph, axis, centreline_mm, end_mm, tol_mm=tol_mm)
    ev = {"perpendicular_at_start": at_start, "perpendicular_at_end": at_end,
          "width_mm": round(abs(end_mm - start_mm), 1)}
    if at_start and at_end:
        return BREAK_JUNCTION, {**ev, "why": (
            "perpendicular walls arrive at BOTH ends: the run is bounded by "
            "junctions, so the break is a corner or a recess between them")}
    if at_start or at_end:
        return BREAK_UNRESOLVED, {**ev, "why": (
            "a perpendicular wall arrives at one end only — a doorway beside a "
            "junction looks like this, and so does a wall simply ending")}
    return BREAK_OPENING, {**ev, "why": (
        "no perpendicular wall at either end: the run stops and resumes on its "
        "own, which is what an opening does")}
