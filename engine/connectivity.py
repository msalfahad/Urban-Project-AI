"""E42 — why the wall graph is in pieces, answered before anything is loosened.

The full-sheet run produced 115 components and 228 termini. The review's first
instruction was the right one: do not assume that is one bug, and do not touch a
tolerance until the dominant cause is known. So this module explains before it
repairs. It classifies, counts and reports; `engine.wall_stitching` is the only
place anything is joined.

WHAT THE DIAGNOSIS FOUND ON AR-00, and it was not what we expected:

  NOT path fragmentation.  Of 55,144 sub-50 mm marks only 993 sit in a path
                           that also holds a long run. A heavy-pen wall path
                           holds exactly ONE item. Flattening broke nothing.
  NOT rotated geometry.    Stroke length is 1,070.9 m at 0 degrees and 991.0 m
                           at 90. Every off-axis bucket together is ~350 m of
                           16 mm average marks: flattened curves, not walls.
  IT WAS POPULATION MIXING. We handed the pairing engine 35,835 segments of
                           which 462 were drawn with the wall pen. Mutual
                           nearest-neighbour pairing then married hatch lines
                           to dimension lines.
  AND END CAPS.            157 of 185 short heavy-pen segments touch a
                           perpendicular long one. They are wall ENDS - the
                           closure across a wall's thickness at an opening or a
                           free end. A parallel-face pairing cannot represent
                           one, so every wall end was invisible, and an
                           invisible end is a break in the graph.

A wall end cap is the strongest connectivity evidence on the sheet: it names
both faces of one wall and says where that wall stops. It is recovered here as
an OBSERVATION with the geometry that supports it, never as a decision.
"""

from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass, field

# Why a component is separate from the rest. The review's list, unchanged, so
# the histogram can be read against the question that was asked.
CAUSE_SEPARATE_GEOMETRY = "A_GENUINE_SEPARATE_PHYSICAL_GEOMETRY"
CAUSE_FACE_FRAGMENTATION = "B_WALL_FACE_FRAGMENTATION"
CAUSE_OBJECT_FRAGMENTATION = "C_SOURCE_VECTOR_OBJECT_FRAGMENTATION"
CAUSE_NON_AXIS_OMITTED = "D_NON_AXIS_ALIGNED_WALL_OMITTED"
CAUSE_ANNOTATION = "E_ANNOTATION_TEXT_OR_HATCH_CONTAMINATION"
CAUSE_DOORWAY = "F_DOORWAY_OR_OPEN_TRANSITION"
CAUSE_JUNCTION_NOT_STITCHED = "G_JUNCTION_NOT_STITCHED"
CAUSE_PATH_CONTINUITY_LOST = "H_SOURCE_PATH_CONTINUITY_LOST"
CAUSE_PROBABLE_NON_WALL = "I_PROBABLE_NON_WALL_GEOMETRY"
CAUSE_UNRESOLVED = "J_UNRESOLVED"

CAUSES = (CAUSE_SEPARATE_GEOMETRY, CAUSE_FACE_FRAGMENTATION,
          CAUSE_OBJECT_FRAGMENTATION, CAUSE_NON_AXIS_OMITTED, CAUSE_ANNOTATION,
          CAUSE_DOORWAY, CAUSE_JUNCTION_NOT_STITCHED,
          CAUSE_PATH_CONTINUITY_LOST, CAUSE_PROBABLE_NON_WALL,
          CAUSE_UNRESOLVED)

# What a wall end is. 228 termini is too many to be one number.
TERM_OPENING_END = "EXPECTED_OPENING_END"
TERM_MISSING_CONNECTION = "LIKELY_MISSING_CONNECTION"
TERM_EXTERIOR = "EXTERIOR_END"
TERM_FRAGMENT = "DRAWING_FRAGMENT"
TERM_NON_WALL = "PROBABLE_NON_WALL"
TERM_UNRESOLVED = "UNRESOLVED"

TERMINUS_KINDS = (TERM_OPENING_END, TERM_MISSING_CONNECTION, TERM_EXTERIOR,
                  TERM_FRAGMENT, TERM_NON_WALL, TERM_UNRESOLVED)

# Component size classes. They are not equal and must not be counted as equal:
# on this sheet a handful of components may hold nearly all the wall length.
MAJOR = "MAJOR_BUILDING_COMPONENT"
SMALL = "SMALL_ISOLATED_COMPONENT"
MICRO = "MICRO_OR_NOISE_COMPONENT"

# A component holding at least this share of the sheet's wall length is major.
MAJOR_SHARE = 0.02
# Below this total length a component cannot be a room boundary at any scale a
# building uses.
MICRO_LENGTH_MM = 1000.0


class ConnectivityError(RuntimeError):
    """The graph could not be explained without inventing a reason."""


@dataclass(frozen=True)
class EndCap:
    """A short mark closing a wall across its thickness, with its evidence.

    An observation. It says "these two faces are one wall and it stops here";
    it does not say the wall is real, that the gap beyond it is a door, or that
    anything should be joined.
    """

    cap_id: str
    segment_id: str
    axis: str
    length_mm: float
    span_mm: tuple[float, float]
    at_mm: float
    touches: tuple[str, ...]
    separation_mm: float
    stroke_width_pt: float
    why: str

    def record(self) -> dict:
        return {"cap_id": self.cap_id, "segment_id": self.segment_id,
                "axis": self.axis, "length_mm": round(self.length_mm, 1),
                "touches": list(self.touches),
                "separation_mm": round(self.separation_mm, 1),
                "stroke_width_pt": self.stroke_width_pt, "why": self.why}


@dataclass(frozen=True)
class TerminusReport:
    """One wall end, its classification, and the continuation it did not join.

    The second half is the useful half: "nearest compatible continuation is
    340 mm away with a matching separation" is a repair instruction. "228
    termini" is not.
    """

    node_id: str
    kind: str
    edge_id: str
    x_mm: float
    y_mm: float
    nearest_id: str = ""
    gap_mm: float | None = None
    angle_difference_deg: float | None = None
    separation_difference_mm: float | None = None
    same_source_path: bool = False
    why_not_joined: str = ""

    def record(self) -> dict:
        return {"node_id": self.node_id, "kind": self.kind,
                "edge_id": self.edge_id, "x_mm": round(self.x_mm, 1),
                "y_mm": round(self.y_mm, 1), "nearest_id": self.nearest_id,
                "gap_mm": None if self.gap_mm is None else round(self.gap_mm, 1),
                "angle_difference_deg": self.angle_difference_deg,
                "separation_difference_mm": (
                    None if self.separation_difference_mm is None
                    else round(self.separation_difference_mm, 1)),
                "same_source_path": self.same_source_path,
                "why_not_joined": self.why_not_joined}


@dataclass(frozen=True)
class ComponentReport:
    """One connected piece of the graph, sized and classified."""

    component_id: str
    edge_ids: tuple[str, ...]
    total_length_mm: float
    bbox_mm: tuple[float, float, float, float]
    termini: int
    junctions: int
    separation_bands: dict
    source_object_count: int
    size_class: str
    likely_cause: str
    share_of_length: float

    def record(self) -> dict:
        return {"component_id": self.component_id,
                "edges": len(self.edge_ids),
                "total_length_m": round(self.total_length_mm / 1000, 2),
                "share_of_length_pct": round(self.share_of_length * 100, 2),
                "bbox_mm": [round(v) for v in self.bbox_mm],
                "termini": self.termini, "junctions": self.junctions,
                "separation_bands": self.separation_bands,
                "source_object_count": self.source_object_count,
                "size_class": self.size_class,
                "likely_cause": self.likely_cause}


def _band(s: float) -> str:
    return ("<60" if s < 60 else "60-120" if s < 120 else "120-180" if s < 180
            else "180-260" if s < 260 else "260-400" if s <= 400 else ">400")


def end_caps(segments, *, tol_mm: float = 60.0, min_separation_mm: float = 60.0,
             max_separation_mm: float = 400.0) -> list[EndCap]:
    """Short marks that close a wall across its thickness.

    A cap is recognised by geometry, not by length alone: it must be short
    enough to be a thickness rather than a wall, its length must fall in the
    separation range a wall can have, and BOTH its ends must touch a
    perpendicular mark — because a wall end closes between two faces, and a
    short mark touching only one thing is a stub, not a closure.
    """
    long_by_axis: dict[str, list] = {"H": [], "V": []}
    for s in segments:
        if s.is_axis_aligned and s.length_mm >= max_separation_mm:
            long_by_axis[s.axis].append(s)

    out: list[EndCap] = []
    n = 0
    for s in segments:
        if not s.is_axis_aligned:
            continue
        L = s.length_mm
        if not (min_separation_mm <= L <= max_separation_mm):
            continue
        other = "V" if s.axis == "H" else "H"
        ends = ((s.start_mm, s.fixed_mm), (s.end_mm, s.fixed_mm))
        hit: list[str] = []
        for at, fixed in ends:
            for f in long_by_axis[other]:
                # `at` runs along s; f is perpendicular, so f's fixed coordinate
                # is compared with `at` and f's extent with s's fixed value.
                if abs(f.fixed_mm - at) > tol_mm:
                    continue
                lo, hi = min(f.start_mm, f.end_mm), max(f.start_mm, f.end_mm)
                if lo - tol_mm <= fixed <= hi + tol_mm:
                    hit.append(f.segment_id)
                    break
        if len(hit) < 2 or hit[0] == hit[1]:
            continue
        n += 1
        out.append(EndCap(
            cap_id=f"EC-{n:05d}", segment_id=s.segment_id, axis=s.axis,
            length_mm=L, span_mm=(s.start_mm, s.end_mm), at_mm=s.fixed_mm,
            touches=tuple(hit[:2]), separation_mm=L,
            stroke_width_pt=s.stroke_width_pt,
            why=("both ends meet a perpendicular run and the span is within "
                 "the range a wall thickness can take, so this mark closes a "
                 "wall rather than being one")))
    return out


def classify_termini(noded, *, search_mm: float = 1200.0) -> list[TerminusReport]:
    """Every wall end, with the continuation it did not join and why.

    Nothing is joined here. The output is a repair list: for each end, the
    nearest compatible continuation, the gap, the difference in separation, and
    the reason the graph left them apart.
    """
    from engine.wall_graph import TERMINUS

    by_id = {e.edge_id: e for e in noded.edges}
    out: list[TerminusReport] = []
    for n in noded.nodes:
        if n.kind != TERMINUS:
            continue
        eid = n.edge_ids[0] if n.edge_ids else ""
        e = by_id.get(eid)
        if e is None:
            out.append(TerminusReport(
                node_id=n.node_id, kind=TERM_UNRESOLVED, edge_id=eid,
                x_mm=n.x_mm, y_mm=n.y_mm,
                why_not_joined="the node carries no edge the split graph knows"))
            continue

        best = None
        for f in noded.edges:
            if f.edge_id == eid:
                continue
            for at in (f.start_mm, f.end_mm):
                fx, fy = f.point(at) if hasattr(f, "point") else (
                    (at, f.centreline_mm) if f.axis == "H"
                    else (f.centreline_mm, at))
                d = math.hypot(fx - n.x_mm, fy - n.y_mm)
                if d > search_mm:
                    continue
                if best is None or d < best[0]:
                    best = (d, f)
        if best is None:
            out.append(TerminusReport(
                node_id=n.node_id, kind=TERM_FRAGMENT, edge_id=eid,
                x_mm=n.x_mm, y_mm=n.y_mm,
                why_not_joined=(f"nothing else in the graph within "
                                f"{search_mm:.0f} mm: this run stands alone")))
            continue

        gap, f = best
        dsep = abs(e.wall_face_separation_mm - f.wall_face_separation_mm)
        same_axis = e.axis == f.axis
        if same_axis and dsep <= 20 and gap <= 250:
            kind = TERM_MISSING_CONNECTION
            why = ("same axis, matching separation and a gap smaller than a "
                   "doorway: this looks like one wall the graph left in two")
        elif same_axis and dsep <= 20:
            kind = TERM_OPENING_END
            why = ("same wall continues beyond a gap of doorway size, which is "
                   "what a doorway looks like and also what a missing run "
                   "looks like — not decided here")
        elif not same_axis and gap <= 250:
            kind = TERM_MISSING_CONNECTION
            why = ("a perpendicular run ends within reach: a corner or T the "
                   "noder did not stitch")
        elif dsep > 20:
            kind = TERM_UNRESOLVED
            why = (f"nearest neighbour has a different wall separation "
                   f"({dsep:.0f} mm apart), so it is not obviously the same wall")
        else:
            kind = TERM_UNRESOLVED
            why = "no compatible continuation within reach"
        out.append(TerminusReport(
            node_id=n.node_id, kind=kind, edge_id=eid, x_mm=n.x_mm,
            y_mm=n.y_mm, nearest_id=f.edge_id, gap_mm=gap,
            angle_difference_deg=0.0 if same_axis else 90.0,
            separation_difference_mm=dsep, why_not_joined=why))
    return out


def components(noded) -> list[ComponentReport]:
    """Each connected piece, sized, bounded and classified.

    The target is never "one component". A drawing legitimately contains
    shafts, detached walls, balconies and separate blocks. The target is that
    every disconnect is explainable.
    """
    from engine.wall_graph import TERMINUS

    adj: dict[str, set] = {e.edge_id: set() for e in noded.edges}
    node_of: dict[str, list] = {}
    for n in noded.nodes:
        for a in n.edge_ids:
            node_of.setdefault(a, []).append(n)
            for b in n.edge_ids:
                if a != b and a in adj:
                    adj[a].add(b)

    by_id = {e.edge_id: e for e in noded.edges}
    seen: set = set()
    groups: list[list[str]] = []
    for e in noded.edges:
        if e.edge_id in seen:
            continue
        stack, grp = [e.edge_id], []
        while stack:
            cur = stack.pop()
            if cur in seen:
                continue
            seen.add(cur)
            grp.append(cur)
            stack.extend(adj.get(cur, ()))
        groups.append(sorted(grp))

    total = sum(e.length_mm for e in noded.edges) or 1.0
    out: list[ComponentReport] = []
    for i, grp in enumerate(sorted(groups, key=lambda g: -sum(
            by_id[x].length_mm for x in g)), 1):
        edges = [by_id[x] for x in grp]
        length = sum(e.length_mm for e in edges)
        xs, ys = [], []
        for e in edges:
            for at in (e.start_mm, e.end_mm):
                if e.axis == "H":
                    xs.append(at)
                    ys.append(e.centreline_mm)
                else:
                    xs.append(e.centreline_mm)
                    ys.append(at)
        nodes = {n.node_id: n for x in grp for n in node_of.get(x, ())}
        term = sum(1 for n in nodes.values() if n.kind == TERMINUS)
        share = length / total
        if share >= MAJOR_SHARE:
            size = MAJOR
        elif length < MICRO_LENGTH_MM:
            size = MICRO
        else:
            size = SMALL

        if size == MICRO:
            cause = CAUSE_PROBABLE_NON_WALL
        elif len(grp) == 1 and term >= 1:
            cause = CAUSE_JUNCTION_NOT_STITCHED
        elif size == MAJOR:
            cause = CAUSE_SEPARATE_GEOMETRY
        else:
            cause = CAUSE_UNRESOLVED
        out.append(ComponentReport(
            component_id=f"GC-{i:04d}", edge_ids=tuple(grp),
            total_length_mm=length,
            bbox_mm=(min(xs), min(ys), max(xs), max(ys)) if xs else (0, 0, 0, 0),
            termini=term, junctions=len(nodes) - term,
            separation_bands=dict(Counter(
                _band(e.wall_face_separation_mm) for e in edges)),
            source_object_count=len({e.pair_id for e in edges}),
            size_class=size, likely_cause=cause, share_of_length=share))
    return out


def summarise(comps: list[ComponentReport], terms: list[TerminusReport]) -> dict:
    """The three numbers a reviewer actually needs, not one hundred and fifteen."""
    by_size = Counter(c.size_class for c in comps)
    length_by_size: dict[str, float] = {}
    for c in comps:
        length_by_size[c.size_class] = length_by_size.get(
            c.size_class, 0.0) + c.total_length_mm
    major = [c for c in comps if c.size_class == MAJOR]
    return {
        "components": len(comps),
        "by_size_class": dict(by_size),
        "length_m_by_size_class": {k: round(v / 1000, 1)
                                   for k, v in length_by_size.items()},
        "major_components": len(major),
        "share_of_length_in_major_components_pct": round(
            sum(c.share_of_length for c in major) * 100, 1),
        "largest_components": [c.record() for c in comps[:5]],
        "cause_histogram": dict(Counter(c.likely_cause for c in comps)),
        "termini": len(terms),
        "terminus_histogram": {k: sum(1 for t in terms if t.kind == k)
                               for k in TERMINUS_KINDS},
        "repairable_termini": sum(1 for t in terms
                                  if t.kind == TERM_MISSING_CONNECTION),
    }
