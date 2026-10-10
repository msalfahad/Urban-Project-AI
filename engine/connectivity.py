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
    # A component's own cycle count, computed here rather than joined from a
    # separately-sorted list by position. `cycle_capacity` sorts by cycles and
    # `components` by length: matching them on index silently paired every
    # component with another component's numbers.
    independent_cycles: int = 0
    node_count: int = 0

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
                "likely_cause": self.likely_cause,
                "independent_cycles": self.independent_cycles,
                "nodes": self.node_count}


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
        # Independent cycles for one connected component: E - V + 1. Zero
        # means a tree, which bounds no face however much wall it holds.
        cycles = max(0, len(grp) - len(nodes) + 1)
        out.append(ComponentReport(
            independent_cycles=cycles, node_count=len(nodes),
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


def cycle_capacity(noded) -> list[dict]:
    """Can each component hold a face at all? The cyclomatic number says so.

    For a connected component, independent cycles = E - V + 1. Zero means the
    component is a tree: it has no closed loop, so it bounds no face however
    much wall length it carries. This is the measurement gate G8 needs and it
    was previously unimplemented, which is why G8 read NOT_MEASURED.
    """
    node_of: dict[str, list] = {}
    adj: dict[str, set] = {e.edge_id: set() for e in noded.edges}
    for n in noded.nodes:
        for a in n.edge_ids:
            node_of.setdefault(a, []).append(n)
            for b in n.edge_ids:
                if a != b and a in adj:
                    adj[a].add(b)

    by_id = {e.edge_id: e for e in noded.edges}
    seen: set = set()
    out: list[dict] = []
    i = 0
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
        i += 1
        nodes = {n.node_id for x in grp for n in node_of.get(x, ())}
        edges = len(grp)
        verts = len(nodes)
        # E - V + 1 for one connected component.
        cycles = max(0, edges - verts + 1)
        xs, ys = [], []
        for x in grp:
            f = by_id[x]
            for at in (f.start_mm, f.end_mm):
                if f.axis == "H":
                    xs.append(at)
                    ys.append(f.centreline_mm)
                else:
                    xs.append(f.centreline_mm)
                    ys.append(at)
        out.append({
            "component_index": i, "edges": edges, "nodes": verts,
            "independent_cycles": cycles,
            "total_length_m": round(
                sum(by_id[x].length_mm for x in grp) / 1000, 2),
            "bbox_mm": (min(xs), min(ys), max(xs), max(ys)) if xs else None,
        })
    out.sort(key=lambda c: -c["independent_cycles"])
    return out


def cycles_over_regions(noded, region_points: dict) -> dict:
    """Do closed cycles exist WHERE the raster says rooms are?

    This is the only check that tests the graph against the building rather
    than against itself.

    IT MEASURES A NECESSARY CONDITION, NOT A SUFFICIENT ONE. A region point
    inside the bounding box of a component that has at least one independent
    cycle is not proof that a face encloses that room — proving that needs the
    face extraction this gate exists to authorise. So the result is reported as
    NECESSARY_CONDITION_ONLY and a region that FAILS it is conclusive (no cycle
    can possibly enclose it) while one that passes is merely not yet excluded.
    """
    caps = [c for c in cycle_capacity(noded) if c["independent_cycles"] > 0
            and c["bbox_mm"]]
    covered, uncovered = [], []
    for space_id, (x, y) in sorted(region_points.items()):
        hit = any(bb[0] <= x <= bb[2] and bb[1] <= y <= bb[3]
                  for bb in (c["bbox_mm"] for c in caps))
        (covered if hit else uncovered).append(space_id)
    return {
        "basis": "NECESSARY_CONDITION_ONLY",
        "why": ("a region inside a cyclic component's bounding box MIGHT be "
                "enclosed by a face; one outside every such box certainly is "
                "not. Only face extraction can upgrade this to proof"),
        "regions_tested": len(region_points),
        "regions_with_a_possible_enclosing_cycle": len(covered),
        "regions_with_no_possible_enclosing_cycle": len(uncovered),
        "uncovered": uncovered[:20],
        "components_with_cycles": len(caps),
        "total_independent_cycles": sum(c["independent_cycles"] for c in caps),
    }


# --------------------------------------------------------------- dashed runs

# A dashed run is a TOPOLOGY_BOUNDARY_CANDIDATE and nothing more. It is not a
# door, not a wall, and not an opening. It is a place the architect drew a
# boundary that is not a solid wall, and it may close a cycle the graph cannot
# otherwise close.
TOPOLOGY_BOUNDARY_CANDIDATE = "TOPOLOGY_BOUNDARY_CANDIDATE"

# A dash sequence needs at least this many marks. Two collinear short segments
# are two segments; a pattern needs repetition to be a pattern.
MIN_DASHES = 3
# A dash mark longer than this is a wall fragment, not a dash.
MAX_DASH_MM = 700.0
# Gap between marks, as a multiple of the marks' own median length. A regular
# linetype keeps this roughly constant, which is what separates an exploded
# dashed line from a row of unrelated short marks.
MAX_GAP_RATIO = 3.0
# How much the gaps may vary and still be called regular.
GAP_REGULARITY = 0.6


@dataclass(frozen=True)
class DashedRun:
    """A sequence of collinear short marks that reads as a drawn dashed line.

    On AR-00 there are ZERO PDF-level dash patterns: every stroke path is
    solid ("[] 0"). The dashed thresholds the space map describes were exported
    as exploded linetypes — individual short solid segments — so a dash
    pattern has to be recovered from geometry, and `VectorPath.is_dashed`
    correctly reports nothing to find.
    """

    run_id: str
    axis: str
    centreline_mm: float
    start_mm: float
    end_mm: float
    marks: int
    median_mark_mm: float
    median_gap_mm: float
    gap_regularity: float
    stroke_width_pt: float
    segment_ids: tuple[str, ...]
    classification: str = TOPOLOGY_BOUNDARY_CANDIDATE

    @property
    def span_mm(self) -> float:
        return abs(self.end_mm - self.start_mm)

    def record(self) -> dict:
        return {"run_id": self.run_id, "axis": self.axis,
                "centreline_mm": round(self.centreline_mm, 1),
                "span_mm": round(self.span_mm, 1), "marks": self.marks,
                "median_mark_mm": round(self.median_mark_mm, 1),
                "median_gap_mm": round(self.median_gap_mm, 1),
                "gap_regularity": round(self.gap_regularity, 2),
                "stroke_width_pt": self.stroke_width_pt,
                "classification": self.classification,
                "boundary_type": "UNKNOWN"}


def dashed_runs(segments, *, tol_mm: float = 3.0) -> list[DashedRun]:
    """Recover exploded dashed lines from collinear short marks.

    Grouped by axis, pen weight and centreline — a dashed line is drawn with
    one pen on one line — then split wherever the gap stops being regular. The
    regularity test is what keeps a row of unrelated fixture ticks from being
    called a boundary.
    """
    import statistics

    groups: dict[tuple, list] = {}
    for s in segments:
        if not s.is_axis_aligned or s.length_mm > MAX_DASH_MM:
            continue
        # A FILL path is a glyph outline or a hatch body, not a drawn line. Its
        # short marks are regularly spaced by construction, so admitting them
        # would fill this list with text. Excluding them is not tuning: a fill
        # is a different kind of object from a stroke and the PDF says which.
        if s.path_type != "STROKE" or s.stroke_width_pt <= 0.0:
            continue
        key = (s.axis, round(s.stroke_width_pt, 2),
               round(s.fixed_mm / tol_mm))
        groups.setdefault(key, []).append(s)

    out: list[DashedRun] = []
    n = 0
    for (axis, pen, _), marks in groups.items():
        marks.sort(key=lambda s: min(s.start_mm, s.end_mm))
        run: list = []

        def flush(run):
            nonlocal n
            if len(run) < MIN_DASHES:
                return
            lens = [m.length_mm for m in run]
            gaps = [min(b.start_mm, b.end_mm) - max(a.start_mm, a.end_mm)
                    for a, b in zip(run, run[1:])]
            gaps = [g for g in gaps if g > 0]
            if not gaps:
                return
            med_gap = statistics.median(gaps)
            spread = (statistics.pstdev(gaps) / med_gap) if med_gap else 99.0
            if spread > GAP_REGULARITY:
                return
            n += 1
            out.append(DashedRun(
                run_id=f"DR-{n:04d}", axis=axis,
                centreline_mm=statistics.median([m.fixed_mm for m in run]),
                start_mm=min(min(m.start_mm, m.end_mm) for m in run),
                end_mm=max(max(m.start_mm, m.end_mm) for m in run),
                marks=len(run), median_mark_mm=statistics.median(lens),
                median_gap_mm=med_gap, gap_regularity=spread,
                stroke_width_pt=pen,
                segment_ids=tuple(m.segment_id for m in run)))

        for m in marks:
            if not run:
                run = [m]
                continue
            prev = run[-1]
            gap = min(m.start_mm, m.end_mm) - max(prev.start_mm, prev.end_mm)
            limit = MAX_GAP_RATIO * max(prev.length_mm, m.length_mm)
            if 0 < gap <= limit:
                run.append(m)
            else:
                flush(run)
                run = [m]
        flush(run)
    return out


def dashed_summary(runs: list[DashedRun]) -> dict:
    from collections import Counter
    return {
        "runs": len(runs),
        "total_span_m": round(sum(r.span_mm for r in runs) / 1000, 1),
        "by_pen": dict(Counter(r.stroke_width_pt for r in runs)),
        "by_axis": dict(Counter(r.axis for r in runs)),
        "span_bands_mm": dict(Counter(
            ("<300" if r.span_mm < 300 else "300-900" if r.span_mm < 900
             else "900-1800" if r.span_mm < 1800 else "1800+") for r in runs)),
        "classification": TOPOLOGY_BOUNDARY_CANDIDATE,
        "boundary_type": "UNKNOWN — a dashed run is NOT a door and NOT a wall",
    }
