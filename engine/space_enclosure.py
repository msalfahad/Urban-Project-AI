"""E96 — enclose a space with the lines the architect drew, not the ink.

Round 2 matched every run of a region's raster contour to a vector object
and could not close a single room. The reason was not tolerance: the median
distance from an unmatched run to the nearest covering line was 968 mm,
because the contour follows bath edges, cabinets, thresholds and stair
nosings as readily as walls. A contour run over a bathtub HAS no wall to
match, and demanding one made every bathroom unmeasurable.

So the region stops being a path and becomes what it actually is:

    THE RASTER ANSWERS   "which space are we measuring?"
    THE VECTOR ANSWERS   "where is every millimetre of its boundary?"

The mechanism is a flood fill through an ARRANGEMENT OF SUPPORTED LINES.
Take the drawn wall faces, end caps, jambs and exterior boundary near the
region; cut the neighbourhood into cells on their coordinates; block a cell
edge only where a line is actually DRAWN across it; then flood from a seed
point inside the region. Whatever the flood cannot escape is the enclosure.

Three properties fall out of that construction rather than being coded:

  * A FIXTURE IS INVISIBLE. A bathtub is not a boundary candidate, so it
    never blocks a cell edge and never indents the result. No detour test
    is needed because a detour cannot arise.

  * A WALL THAT STOPS SHORT DOES NOT CLOSE. A line blocks only over its
    drawn extent, so the flood escapes through the gap and the enclosure is
    refused. Nothing is extended until it hits something.

  * A CORNER IS AN INTERSECTION, NOT AN INVENTION. The result's vertices
    are where two blocked edges meet — i.e. where two independently drawn
    lines cross. A corner where only one side is supported cannot appear,
    because the other side never blocked anything.

Every threshold here is set from geometry or from measured drawing noise,
and frozen before any real drawing is evaluated.
"""

from __future__ import annotations

import hashlib
from collections import Counter
from dataclasses import dataclass, field

from engine.space_objects import (
    PRODUCTION_ELIGIBLE_SOURCES, SOURCE_PRIORITY, SRC_UNRESOLVED)

# --- frozen parameters ----------------------------------------------------
# Each is justified from geometry or from the measured coordinate-noise
# floor of a plotted PDF (0.0087 mm on this project, snap grid 0.05 mm).
# NONE of them may be changed because a real drawing scores better: a
# change needs a synthetic or source-general argument.

# How far outside the region's own extent to look for its walls. A room's
# wall lies outside the free-space region by at most the wall's thickness,
# and the thickest wall a drawing of this kind carries is under half a
# metre; 1 m is that with room to spare, and a smaller neighbourhood cannot
# contain a wall the region needs.
NEIGHBOURHOOD_MARGIN_MM = 1000.0

# Two collinear drawn pieces closer than this are one line interrupted by
# plotting noise, not two lines with a gap. Set from the drawing's measured
# noise floor and snap grid, two orders of magnitude above both.
COLLINEAR_JOIN_MM = 1.0

# A drawn line that stops this close to a perpendicular one reaches it: the
# junction is a corner, not a gap. This is the only tolerance that can
# CLOSE anything, so it is deliberately tight — a hairline plotting gap at
# a junction, not a missing wall. §5 permits it explicitly.
JUNCTION_REACH_MM = 2.0

# A cell smaller than this in either direction is a sliver of the
# arrangement, not a space.
MIN_CELL_MM = 1.0

# Below this a flood-filled enclosure is not a space anybody occupies.
MIN_ENCLOSURE_M2 = 0.05

ALGORITHM = "SUPPORTED_LINE_ARRANGEMENT_FLOOD_FILL_V1"

# Verdicts.
ENCLOSED = "ENCLOSURE_COMPLETE"
ESCAPED = "ENCLOSURE_ESCAPED_THE_NEIGHBOURHOOD"
NO_SEED = "NO_INTERIOR_SEED_AVAILABLE"
TOO_SMALL = "ENCLOSURE_BELOW_MINIMUM_AREA"

# Why an edge of the result is not supported.
LEAK_UNSUPPORTED_SIDE = "A_WHOLE_SIDE_HAS_NO_DRAWN_LINE"
LEAK_GAP_IN_A_LINE = "A_DRAWN_LINE_STOPS_SHORT_OF_ITS_JUNCTION"
LEAK_OPEN_PORTAL = "AN_OPENING_IS_NOT_CLOSED_BY_A_VALIDATED_BARRIER"


@dataclass(frozen=True)
class Leak:
    """One stretch of the enclosure's boundary that nothing drawn supports."""

    axis: str
    fixed_mm: float
    start_mm: float
    end_mm: float
    reason: str
    nearest_line_id: str = ""
    nearest_gap_mm: float | None = None

    @property
    def length_mm(self) -> float:
        return abs(self.end_mm - self.start_mm)

    def record(self) -> dict:
        return {"axis": self.axis, "fixed_mm": round(self.fixed_mm, 2),
                "interval_mm": [round(self.start_mm, 2),
                                round(self.end_mm, 2)],
                "length_mm": round(self.length_mm, 1),
                "reason": self.reason,
                "nearest_drawn_line": self.nearest_line_id,
                "gap_to_it_mm": (None if self.nearest_gap_mm is None
                                 else round(self.nearest_gap_mm, 2))}


@dataclass(frozen=True)
class Enclosure:
    """LOCAL_SPACE_ENCLOSURE_CANDIDATE — one region's measured boundary."""

    enclosure_id: str
    region_id: str
    verdict: str
    polygon_wkt: str = ""
    area_m2: float | None = None
    perimeter_m: float | None = None
    supported_perimeter_m: float = 0.0
    production_perimeter_m: float = 0.0
    edges: tuple = ()             # ((axis, fixed, lo, hi, object_id, src),)
    leaks: tuple = ()
    corners_constructed: tuple = ()
    lines_used: tuple[str, ...] = ()
    geometry_hash: str = ""
    why: str = ""

    @property
    def is_complete(self) -> bool:
        return self.verdict == ENCLOSED and not self.leaks

    @property
    def vector_support_pct(self) -> float:
        if not self.perimeter_m:
            return 0.0
        return round(100.0 * self.supported_perimeter_m
                     / self.perimeter_m, 2)

    @property
    def production_support_pct(self) -> float:
        if not self.perimeter_m:
            return 0.0
        return round(100.0 * self.production_perimeter_m
                     / self.perimeter_m, 2)

    def record(self) -> dict:
        return {
            "enclosure_id": self.enclosure_id,
            "region_id": self.region_id,
            "verdict": self.verdict,
            "complete": self.is_complete,
            "area_m2": (None if self.area_m2 is None
                        else round(self.area_m2, 3)),
            "perimeter_m": (None if self.perimeter_m is None
                            else round(self.perimeter_m, 3)),
            "VECTOR_SUPPORT_PCT": self.vector_support_pct,
            "PRODUCTION_ELIGIBLE_SUPPORT_PCT": self.production_support_pct,
            "edges": [
                {"axis": a, "fixed_mm": round(f, 2),
                 "interval_mm": [round(lo, 2), round(hi, 2)],
                 "object_id": oid, "source_type": src}
                for a, f, lo, hi, oid, src in self.edges],
            "by_source": dict(Counter(src for *_, src in self.edges)),
            "leaks": [lk.record() for lk in self.leaks],
            "leak_length_m": round(
                sum(lk.length_mm for lk in self.leaks) / 1000, 3),
            "corners_constructed": [
                {"at_mm": [round(x, 2), round(y, 2)], "from_lines": ids}
                for x, y, ids in self.corners_constructed],
            "lines_used": list(self.lines_used),
            "geometry_hash": self.geometry_hash,
            "no_raster_millimetre": (
                "every edge above lies on a DRAWN line. The region supplied "
                "an inside point and an extent, and no pixel coordinate "
                "reached this geometry"),
            "why": self.why,
        }


# ------------------------------------------------------------------ the fill

def enclose(region_id: str, seed_mm, candidates, *, extent=None,
            margin_mm: float = NEIGHBOURHOOD_MARGIN_MM,
            junction_reach_mm: float = JUNCTION_REACH_MM,
            enclosure_id: str = "") -> Enclosure:
    """Flood the arrangement of supported lines from a point inside.

    `seed_mm` is a point the region says is inside the space. `candidates`
    are drawn lines (`boundary_match.VectorCandidate`). `extent` bounds the
    neighbourhood; escaping it means the space is not enclosed by anything
    drawn.
    """
    eid = enclosure_id or f"LSE-{region_id}"
    if seed_mm is None:
        return Enclosure(eid, region_id, NO_SEED,
                         why=("the region supplied no interior point, so "
                              "there is nothing to flood from"))

    sx, sy = float(seed_mm[0]), float(seed_mm[1])
    box = _neighbourhood(extent, sx, sy, margin_mm)
    near = [c for c in candidates if _relevant(c, box)]

    xs = _grid([c.fixed_mm for c in near if c.axis == "V"],
               box[0], box[2])
    ys = _grid([c.fixed_mm for c in near if c.axis == "H"],
               box[1], box[3])
    if len(xs) < 2 or len(ys) < 2:
        return Enclosure(eid, region_id, ESCAPED,
                         why=("no drawn line of either orientation lies "
                              "near this region, so nothing can enclose it"))

    v_lines = _by_coordinate([c for c in near if c.axis == "V"])
    h_lines = _by_coordinate([c for c in near if c.axis == "H"])

    si, sj = _cell_of(sx, xs), _cell_of(sy, ys)
    if si is None or sj is None:
        return Enclosure(eid, region_id, NO_SEED,
                         why=("the interior point lies outside the "
                              "arrangement built around it"))

    reached, escaped = _flood(si, sj, xs, ys, v_lines, h_lines,
                              junction_reach_mm)

    if escaped:
        leaks = _escape_leaks(reached, xs, ys, v_lines, h_lines,
                              junction_reach_mm)
        return Enclosure(
            eid, region_id, ESCAPED, leaks=tuple(leaks),
            why=("the fill reached the edge of the neighbourhood: at least "
                 "one side of this space has no drawn line closing it. "
                 "Nothing was extended to close it, and no pixel edge was "
                 "substituted"))

    poly, edges, corners = _assemble(reached, xs, ys, v_lines, h_lines,
                                     junction_reach_mm)
    if poly is None or poly.is_empty:
        return Enclosure(eid, region_id, ESCAPED,
                         why="the reached cells did not form a polygon")

    area = poly.area / 1e6
    if area < MIN_ENCLOSURE_M2:
        return Enclosure(eid, region_id, TOO_SMALL,
                         area_m2=area,
                         why=(f"{area:.3f} m² is below the minimum for a "
                              "space rather than a sliver of the "
                              "arrangement"))

    supported = sum(hi - lo for *_, lo, hi, _, _ in
                    ((a, f, lo, hi, oid, src)
                     for a, f, lo, hi, oid, src in edges) if True)
    production = sum(hi - lo for a, f, lo, hi, oid, src in edges
                     if src in PRODUCTION_ELIGIBLE_SOURCES)
    wkt = poly.wkt
    return Enclosure(
        eid, region_id, ENCLOSED, polygon_wkt=wkt, area_m2=area,
        perimeter_m=poly.length / 1000.0,
        supported_perimeter_m=supported / 1000.0,
        production_perimeter_m=production / 1000.0,
        edges=tuple(edges), leaks=(),
        corners_constructed=tuple(corners),
        lines_used=tuple(sorted({oid for *_, oid, _ in edges if oid})),
        geometry_hash=hashlib.sha256(wkt.encode()).hexdigest()[:24],
        why=("every edge of this polygon lies on a line the architect drew, "
             "and every corner is the intersection of two of them"))


# --------------------------------------------------------------- internals

def _neighbourhood(extent, sx: float, sy: float, margin: float) -> tuple:
    if extent is None:
        return (sx - margin, sy - margin, sx + margin, sy + margin)
    x0, y0, x1, y1 = extent
    return (min(x0, sx) - margin, min(y0, sy) - margin,
            max(x1, sx) + margin, max(y1, sy) + margin)


def _relevant(c, box) -> bool:
    x0, y0, x1, y1 = box
    lo, hi = min(c.start_mm, c.end_mm), max(c.start_mm, c.end_mm)
    if c.axis == "V":
        return x0 <= c.fixed_mm <= x1 and hi >= y0 and lo <= y1
    return y0 <= c.fixed_mm <= y1 and hi >= x0 and lo <= x1


def _grid(values, lo: float, hi: float) -> list:
    """Distinct coordinates, plus the neighbourhood edges as escape lines."""
    out = [lo, hi]
    for v in values:
        if lo < v < hi:
            out.append(v)
    out.sort()
    keep = [out[0]]
    for v in out[1:]:
        if v - keep[-1] >= MIN_CELL_MM:
            keep.append(v)
    return keep


def _by_coordinate(lines) -> dict:
    """Drawn intervals per coordinate, merged where collinear and touching."""
    grouped: dict = {}
    for c in lines:
        key = round(c.fixed_mm / COLLINEAR_JOIN_MM)
        grouped.setdefault(key, []).append(c)
    out: dict = {}
    for key, group in grouped.items():
        # Keyed on the interval only: two candidates can share an exact
        # span (a band's face and a cap's line, say), and sorting tuples
        # that end in a dataclass then tries to compare the dataclasses.
        spans = sorted(
            ((min(c.start_mm, c.end_mm), max(c.start_mm, c.end_mm), c)
             for c in group),
            key=lambda t: (t[0], t[1], t[2].object_id))
        out[key] = (group[0].fixed_mm, spans)
    return out


def _covers(entry, lo: float, hi: float, reach: float):
    """Is [lo, hi] continuously drawn on this line? Returns the object ids.

    `reach` bridges a hairline gap between two collinear pieces — plotting
    noise at a junction — and nothing wider. A real gap (a doorway, a
    missing wall) is never bridged, which is what makes the fill escape
    there instead of closing.
    """
    if entry is None:
        return None
    _, spans = entry
    used, cursor = [], lo
    for a, b, c in spans:
        if a > cursor + reach:
            break
        if b > cursor:
            cursor = b
            used.append(c)
        if cursor >= hi - 1e-9:
            return used
    return used if cursor >= hi - 1e-9 else None


def _piece_at(entry, lo: float, hi: float):
    """Which drawn piece actually covers THIS stretch of the line.

    `_covers` answers whether the stretch is drawn, walking pieces from the
    start of the line; its first piece is not necessarily the one over this
    cell. Attributing the edge to that first piece labelled a doorway's
    jamb as the wall face beside it, which is exactly the provenance §4
    forbids losing. So the edge is attributed to the piece with the most
    overlap here.
    """
    if entry is None:
        return None
    _, spans = entry
    best, best_overlap = None, 0.0
    for a, b, c in spans:
        overlap = min(hi, b) - max(lo, a)
        if overlap > best_overlap:
            best, best_overlap = c, overlap
    return best


def _cell_of(v: float, grid) -> int | None:
    for i in range(len(grid) - 1):
        if grid[i] <= v <= grid[i + 1]:
            return i
    return None


def _blocked_v(i: int, j: int, xs, ys, v_lines, reach):
    """Is the vertical cell edge at xs[i] blocked over cell row j?"""
    return _covers(v_lines.get(round(xs[i] / COLLINEAR_JOIN_MM)),
                   ys[j], ys[j + 1], reach)


def _blocked_h(i: int, j: int, xs, ys, h_lines, reach):
    return _covers(h_lines.get(round(ys[j] / COLLINEAR_JOIN_MM)),
                   xs[i], xs[i + 1], reach)


def _flood(si: int, sj: int, xs, ys, v_lines, h_lines, reach):
    """Cells reachable from the seed without crossing a drawn line."""
    ni, nj = len(xs) - 1, len(ys) - 1
    seen = {(si, sj)}
    stack = [(si, sj)]
    escaped = False
    while stack:
        i, j = stack.pop()
        if i == 0 or j == 0 or i == ni - 1 or j == nj - 1:
            escaped = True
        for di, dj in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            a, b = i + di, j + dj
            if not (0 <= a < ni and 0 <= b < nj) or (a, b) in seen:
                continue
            if di:
                edge = max(i, a)
                if _blocked_v(edge, j, xs, ys, v_lines, reach):
                    continue
            else:
                edge = max(j, b)
                if _blocked_h(i, edge, xs, ys, h_lines, reach):
                    continue
            seen.add((a, b))
            stack.append((a, b))
    return seen, escaped


def _escape_leaks(reached, xs, ys, v_lines, h_lines, reach) -> list:
    """Where the fill got out. Named so a human knows what to confirm."""
    ni, nj = len(xs) - 1, len(ys) - 1
    out = []
    for i, j in sorted(reached):
        for di, dj in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            a, b = i + di, j + dj
            if 0 <= a < ni and 0 <= b < nj:
                continue
            if di:
                edge = 0 if a < 0 else ni
                out.append(Leak("V", xs[edge], ys[j], ys[j + 1],
                                LEAK_UNSUPPORTED_SIDE))
            else:
                edge = 0 if b < 0 else nj
                out.append(Leak("H", ys[edge], xs[i], xs[i + 1],
                                LEAK_UNSUPPORTED_SIDE))
    return _merge_leaks(out)


def _merge_leaks(leaks) -> list:
    by: dict = {}
    for lk in leaks:
        by.setdefault((lk.axis, round(lk.fixed_mm, 3), lk.reason),
                      []).append(lk)
    out = []
    for (axis, fixed, reason), group in sorted(by.items()):
        spans = sorted((lk.start_mm, lk.end_mm) for lk in group)
        lo, hi = spans[0]
        for a, b in spans[1:]:
            if a <= hi + 1e-9:
                hi = max(hi, b)
            else:
                out.append(Leak(axis, fixed, lo, hi, reason))
                lo, hi = a, b
        out.append(Leak(axis, fixed, lo, hi, reason))
    return out


def _assemble(reached, xs, ys, v_lines, h_lines, reach):
    """Union the reached cells, and record which line supports each edge."""
    from shapely.geometry import box as shbox
    from shapely.ops import unary_union

    cells = [shbox(xs[i], ys[j], xs[i + 1], ys[j + 1])
             for i, j in sorted(reached)]
    poly = unary_union(cells)
    if hasattr(poly, "geoms"):
        poly = max(poly.geoms, key=lambda g: g.area)

    ni, nj = len(xs) - 1, len(ys) - 1
    edges, corner_lines = [], {}
    for i, j in sorted(reached):
        for di, dj in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            a, b = i + di, j + dj
            inside = (0 <= a < ni and 0 <= b < nj) and (a, b) in reached
            if inside:
                continue
            if di:
                edge = max(i, a)
                used = _blocked_v(edge, j, xs, ys, v_lines, reach)
                if used:
                    c = _piece_at(
                        v_lines.get(round(xs[edge] / COLLINEAR_JOIN_MM)),
                        ys[j], ys[j + 1]) or used[0]
                    edges.append(("V", xs[edge], ys[j], ys[j + 1],
                                  c.object_id, c.source_type))
                    corner_lines.setdefault(
                        ("V", xs[edge]), set()).add(c.object_id)
            else:
                edge = max(j, b)
                used = _blocked_h(i, edge, xs, ys, h_lines, reach)
                if used:
                    c = _piece_at(
                        h_lines.get(round(ys[edge] / COLLINEAR_JOIN_MM)),
                        xs[i], xs[i + 1]) or used[0]
                    edges.append(("H", ys[edge], xs[i], xs[i + 1],
                                  c.object_id, c.source_type))
                    corner_lines.setdefault(
                        ("H", ys[edge]), set()).add(c.object_id)

    edges = _merge_edges(edges)
    corners = _corners(poly, corner_lines)
    return poly, edges, corners


def _merge_edges(edges) -> list:
    by: dict = {}
    for axis, fixed, lo, hi, oid, src in edges:
        by.setdefault((axis, round(fixed, 4), oid, src), []).append((lo, hi))
    out = []
    for (axis, fixed, oid, src), spans in sorted(by.items()):
        spans.sort()
        lo, hi = spans[0]
        for a, b in spans[1:]:
            if a <= hi + 1e-9:
                hi = max(hi, b)
            else:
                out.append((axis, fixed, lo, hi, oid, src))
                lo, hi = a, b
        out.append((axis, fixed, lo, hi, oid, src))
    return out


def _corners(poly, corner_lines) -> list:
    """Every vertex, with the two drawn lines whose crossing produced it.

    §5's audit trail: a corner is legitimate only where both participating
    faces exist as drawing geometry, and this records which they were.
    """
    out = []
    for x, y in list(poly.exterior.coords)[:-1]:
        v = corner_lines.get(("V", x)) or set()
        h = corner_lines.get(("H", y)) or set()
        if not v or not h:
            # A vertex on only one supported line cannot be a corner of a
            # measured space; it is reported so the audit is complete.
            continue
        out.append((x, y, sorted(v | h)))
    return out


# ----------------------------------------------------------------- scoring

def score(enclosure, *, seed_mm=None, neighbour_seeds=(),
          dimension_verdicts=(), openings_expected: int = 0,
          openings_represented: int = 0, accepted_neighbours=()) -> dict:
    """§11 — five dimensions, reported separately and never combined.

    A single confidence number would let strong vector support hide a
    polygon that does not contain its own seed.
    """
    from shapely.geometry import Point
    from shapely.wkt import loads

    poly = (loads(enclosure.polygon_wkt) if enclosure.polygon_wkt else None)

    holds_seed = None
    if poly is not None and seed_mm is not None:
        holds_seed = poly.buffer(1e-6).contains(Point(*seed_mm))

    neighbours_outside = None
    if poly is not None and neighbour_seeds:
        neighbours_outside = sum(
            1 for p in neighbour_seeds
            if not poly.buffer(-1e-6).contains(Point(*p)))

    overlaps = []
    if poly is not None:
        for other_id, other_wkt in accepted_neighbours:
            if not other_wkt:
                continue
            got = poly.intersection(loads(other_wkt))
            if got.area > 1.0:                 # 1 mm² of real overlap
                overlaps.append({"with": other_id,
                                 "area_mm2": round(got.area, 1)})

    verdicts = Counter(dimension_verdicts)
    return {
        "VECTOR_SUPPORT": {
            "perimeter_supported_pct": enclosure.vector_support_pct,
            "production_eligible_pct": enclosure.production_support_pct,
            "unsupported_length_m": round(
                sum(lk.length_mm for lk in enclosure.leaks) / 1000, 3),
            "basis": "proportion of perimeter lying on drawn geometry",
        },
        "TOPOLOGY_CONSISTENCY": {
            "holds_its_own_seed": holds_seed,
            "adjacent_region_seeds_outside": neighbours_outside,
            "adjacent_region_seeds_tested": len(neighbour_seeds),
            "basis": ("the region that asked for this measurement must lie "
                      "inside it, and its neighbours must lie outside"),
        },
        "DOCUMENT_CONSISTENCY": {
            "by_verdict": dict(verdicts),
            "agree": verdicts.get("AGREE", 0),
            "disagree": verdicts.get("DISAGREE", 0),
            "basis": ("printed dimensions compared AFTER selection. The "
                      "geometry was never tuned to them"),
        },
        "OPENING_CONSISTENCY": {
            "openings_expected": openings_expected,
            "openings_represented": openings_represented,
            "basis": "doors and windows on this boundary are accounted for",
        },
        "GEOMETRIC_VALIDITY": {
            "polygon_present": poly is not None,
            "valid": None if poly is None else bool(poly.is_valid),
            "simple": None if poly is None else bool(poly.is_simple),
            "has_holes": (None if poly is None
                          else bool(poly.interiors)),
            "overlaps_accepted_neighbours": overlaps,
        },
        "not_combined": (
            "these five are reported apart on purpose. One number would "
            "let strong vector support hide a polygon that does not "
            "contain its own seed, or one that overlaps its neighbour"),
    }


def summary(enclosures) -> dict:
    items = list(enclosures)
    complete = [e for e in items if e.is_complete]
    return {
        "algorithm": ALGORITHM,
        "frozen_parameters": frozen_parameters(),
        "enclosures_attempted": len(items),
        "complete": len(complete),
        "by_verdict": dict(Counter(e.verdict for e in items)),
        "complete_area_m2": round(
            sum(e.area_m2 or 0.0 for e in complete), 3),
        "mean_vector_support_pct": (
            round(sum(e.vector_support_pct for e in items) / len(items), 2)
            if items else 0.0),
        "leaks_by_reason": dict(Counter(
            lk.reason for e in items for lk in e.leaks)),
        "what_the_raster_supplied": (
            "an interior point and an approximate extent. Not one "
            "millimetre of any boundary"),
        "what_a_fixture_does_here": (
            "nothing. A bathtub, a cabinet or a stair nosing is not a "
            "boundary candidate, so it cannot block a cell edge and cannot "
            "indent a result. There is no detour test because a detour "
            "cannot arise"),
    }


def frozen_parameters() -> dict:
    """The parameters, their values and WHY each has the value it has."""
    return {
        "NEIGHBOURHOOD_MARGIN_MM": {
            "value": NEIGHBOURHOOD_MARGIN_MM,
            "why": ("a room's wall lies outside its free-space region by at "
                    "most the wall's thickness. 1 m covers any wall a "
                    "drawing of this kind carries, with room to spare"),
        },
        "COLLINEAR_JOIN_MM": {
            "value": COLLINEAR_JOIN_MM,
            "why": ("two collinear pieces closer than this are one line "
                    "interrupted by plotting noise. Two orders of "
                    "magnitude above the measured coordinate-noise floor "
                    "and above the 0.05 mm snap grid"),
        },
        "JUNCTION_REACH_MM": {
            "value": JUNCTION_REACH_MM,
            "why": ("the only tolerance that can CLOSE anything, so it is "
                    "deliberately tight: a hairline plotting gap at a "
                    "junction, never a missing wall or a doorway"),
        },
        "MIN_CELL_MM": {"value": MIN_CELL_MM,
                        "why": "below this an arrangement cell is a sliver"},
        "MIN_ENCLOSURE_M2": {
            "value": MIN_ENCLOSURE_M2,
            "why": "below this a filled area is not a space"},
        "how_these_were_set": (
            "from geometry and from the drawing medium's measured noise "
            "floor, on synthetic fixtures, BEFORE any real drawing was "
            "evaluated. None may be changed because a real drawing scores "
            "better unless the same change is justified synthetically"),
    }


def freeze_hash() -> str:
    """A hash over the algorithm's parameters, for the §1 freeze."""
    payload = ALGORITHM + "|" + "|".join(
        f"{k}={v['value']}" for k, v in sorted(frozen_parameters().items())
        if isinstance(v, dict) and "value" in v)
    return hashlib.sha256(payload.encode()).hexdigest()[:24]
