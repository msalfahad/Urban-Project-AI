"""T-368 rules: EXPOSED WALL-TILE EDGES (BOQ family B4-10; UP-CER-006 45-degree ceramic edge / UP-CER-007 steel edge
profile), any villa.

Research module (unwired). Pure functions, no I/O. It decides, edge by edge, which edges of a tiled wall face are
EXPOSED (and so take a 45-degree mitre or a steel profile) and which are not, with the evidence for each, in m.l.

The physical element (ERS s.2.1). A wall tile has four kinds of boundary. An edge is EXPOSED when the tile's cut edge /
body is visible because nothing covers it: it is not against another tiled face in the same plane, nor against a frame,
a ceiling or a floor. Types, each a vertical or horizontal line on one tiled face:

  EXTERNAL_CORNER  a convex (outside) corner of the wall where two tiled faces meet (room-polygon reflex vertex: the
                   interior angle is above 180 degrees; a column or pier standing proud, a wall end inside the room, an
                   obtuse 135-degree corner). Length = the tile band at that corner. The classic mitre position.
  WALL_END         a tiled face that ends at the arris of a free wall end whose end face is NOT tiled (an open pantry's
                   host wall ending at the open edge, a lobby wall ending at an open side). Length = the band.
  FLAT_STOP        a tiled face that stops in the plane of a wall face that continues untiled (the tile's edge stands
                   proud of the continuing face by its own thickness). Length = the band. A 45-degree mitre needs a
                   second tiled face to meet; at a flat stop nothing meets it (finding F-T368-1, below).
  OPENING_DOOR     the perimeter of a door / doorway inside the band on that face: 2 jambs x min(head, top) + head width
                   when the head is below the tile top. EXPOSED only when the drawing shows no frame / architrave over
                   it; when the frame detail is not drawn the exposure is HELD with the range 0 .. perimeter.
  OPENING_WINDOW   the perimeter of a window on that face. A frame drawn FLUSH with the room face (room-side reveal depth
                   0.000, measured) covers the tile edge: NOT exposed, with that evidence. A window with a drawn
                   room-side reveal is a door-like case (exposure by its reveal / frame detail).

  NOT EXPOSED by definition (listed with their reason, never counted): INTERNAL_CORNER (concave: the two tiled faces
  butt), the TOP edge where the tile meets the ceiling (UP-FIN-WALL-001 / Q-48 A: tile top = underside of the decor
  ceiling), the BOTTOM edge on the floor, an edge under a frame.

Finish (UP-CER-006 / UP-CER-007): ONE finish per edge, never both. When the drawings print which finish, each edge gets
it; when nothing is printed both alternatives are SHOWN with the same m.l and the choice is HELD (never summed).

Rules (research, proposed; scope every villa; provenance T-368):
  R-T368-1  An exposed tile edge is one of EXTERNAL_CORNER / WALL_END / FLAT_STOP / OPENING_* ; an INTERNAL_CORNER,
            a top edge against a ceiling, a bottom edge on a floor and an edge under a frame are never exposed.
  R-T368-2  A vertical exposed edge is as long as the tile band at that point (floor to tile top); with the band HELD,
            the edge length is HELD (count kept, length None, never 0).
  R-T368-3  An opening perimeter is exposed only on drawing evidence: a flush frame = NOT exposed (DRAWING-CONFIRMED);
            no frame / architrave detail = HELD with its range 0 .. perimeter; it is never a default exposed figure.
  R-T368-4  One edge, one finish: the 45-degree and the steel-profile quantities are alternatives on the same m.l;
            with no printed finish both are shown and the choice is HELD; a total that adds both is refused.
  R-T368-5  Each exposed edge is tied to its tiled face's FIN.WALL.TILE line id; one physical edge is counted once per
            tiled face it bounds (a door between two tiled rooms has one perimeter on EACH face).
  R-T368-6  A corner is a tile corner only between two solid faces (wall / column): a room polygon that closes on a
            counter, a zone line or an open side is read on the wall and column entities, never on the polygon alone.
  R-T368-7  (r2, Checker D-T368-1; every villa) An open side crossed in plan by a HIDDEN-linetype element (an
            overhead head, bulkhead, header wall or beam drawn above the cut) is an OPENING UNDER A HEAD, never a
            full-height side, until the head level is established from a drawing (structural beam depth on the slab
            plan / schedule, a section, an elevation, a printed level). Head at or above the tile top: the wall end and
            flat stop take the full band and there is no head arris. Head below the tile top: they are head-high and
            the head's underside arris (the opening width) is a third exposed edge on that face. Head not established:
            wall end and flat stop are HELD in the range head .. band top (never 0, never the full band) and the head
            arris is HELD in the range 0 .. width, by name OVERHEAD_ELEMENT_HEAD_NOT_ESTABLISHED. A door-height
            fallback (Q-55 C, doors) is not a head level for a doorless opening. The overhead element may be drawn
            only on the structural slab plan (a beam band along or across the open side, no HIDDEN line on the
            architectural plan): every open side is therefore also read on the slab plan, and a beam there is treated
            the same way (crossing "BEAM"; head = storey - printed depth - floor allowance, in the band's own frame).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

UNIT = "m"
MITRE = "MITRED_45_DEGREE_EDGE"          # UP-CER-006
PROFILE = "STEEL_EDGE_PROFILE"           # UP-CER-007
FINISHES = (MITRE, PROFILE)

EXPOSED_TYPES = ("EXTERNAL_CORNER", "WALL_END", "FLAT_STOP", "OPENING_DOOR", "OPENING_WINDOW", "HEAD_ARRIS")
HEAD_HELD = "OVERHEAD_ELEMENT_HEAD_NOT_ESTABLISHED"
NOT_EXPOSED_TYPES = ("INTERNAL_CORNER", "TOP_AT_CEILING", "BOTTOM_AT_FLOOR", "UNDER_FRAME")

OA = "ASSUMED — OWNER-APPROVED"
DC = "DRAWING-CONFIRMED"
HELD = "HELD"

REFLEX_DEG = 1.0   # a turn of more than 1 degree to the inside of the room is a corner (drafting noise is below 0.1)


class EdgeError(ValueError):
    """A ledger that breaks an R-T368 rule."""


@dataclass(frozen=True)
class Band:
    """The tile band of a face: bottom and top in m above the finished floor; top None = HELD (with the reason)."""
    top_m: float | None
    source: str
    status: str
    held_item: str = ""


@dataclass(frozen=True)
class Opening:
    oid: str
    kind: str            # "door" | "doorway" | "window"
    width_m: float
    head_m: float | None  # None = head not established
    sill_m: float = 0.0
    frame: str = "NOT_DRAWN"   # "FLUSH" (room-side reveal 0, measured) | "ARCHITRAVE" (drawn) | "NONE" | "NOT_DRAWN"
    frame_source: str = ""


@dataclass
class Edge:
    edge_id: str
    room: str
    etype: str
    count: int
    length_m: float | None      # determinate m.l (exposed) or the m.l listed for a not-exposed edge
    range_m: tuple | None       # (lo, hi) when the exposure is HELD
    exposed: str                # "EXPOSED" | "NOT_EXPOSED" | "HELD"
    status: str                 # evidence status (WORKFLOW_CONTROLS s.5)
    source: str
    line_id: str
    note: str = ""
    finish: dict = field(default_factory=dict)


# ----------------------------------------------------------------------------------------------- geometry helpers

def to_m(value, unit):
    if unit == "m":
        return float(value)
    if unit == "mm":
        return float(value) / 1000.0
    raise EdgeError(f"unit {unit!r}: only m or mm")


def polygon_turns(points):
    """Signed turn (degrees) at every vertex of a closed polygon, walked counter-clockwise (positive = convex)."""
    pts = [tuple(p) for p in points]
    if len(pts) > 1 and pts[0] == pts[-1]:
        pts = pts[:-1]
    if len(pts) < 3:
        raise EdgeError("a room polygon needs at least 3 vertices")
    area2 = sum(pts[i][0] * pts[(i + 1) % len(pts)][1] - pts[(i + 1) % len(pts)][0] * pts[i][1]
                for i in range(len(pts)))
    if area2 < 0:      # mirrored / clockwise input: walk it the other way
        pts = pts[::-1]
    out = []
    n = len(pts)
    for i in range(n):
        p0, p1, p2 = pts[i - 1], pts[i], pts[(i + 1) % n]
        v1 = (p1[0] - p0[0], p1[1] - p0[1])
        v2 = (p2[0] - p1[0], p2[1] - p1[1])
        cr = v1[0] * v2[1] - v1[1] * v2[0]
        dt = v1[0] * v2[0] + v1[1] * v2[1]
        out.append(math.degrees(math.atan2(cr, dt)))
    return out


def corner_classes(points):
    """(external, internal) corner counts of a closed room polygon. External = reflex vertex (turn < -1 degree)."""
    turns = polygon_turns(points)
    ext = sum(1 for t in turns if t < -REFLEX_DEG)
    inn = sum(1 for t in turns if t > REFLEX_DEG)
    return ext, inn


# ----------------------------------------------------------------------------------------------- edge builders

def _vertical(room, eid, etype, count, band, line_id, source, note=""):
    if count < 0:
        raise EdgeError("negative edge count")
    if count == 0:   # a measured absence (no such vertex on the drawn polygon), not a missing value
        return Edge(eid, room, etype, 0, 0.0, None, "EXPOSED", DC, source, line_id,
                    note or "none on the drawn outline")
    if band.top_m is None:
        return Edge(eid, room, etype, count, None, None, HELD, HELD, source, line_id,
                    note or f"band HELD: {band.held_item}")
    if band.top_m > 20.0:
        raise EdgeError(f"band top {band.top_m}: metres expected (mm given?)")
    return Edge(eid, room, etype, count, round(count * band.top_m, 4), None, "EXPOSED", band.status,
                source + f"; band {band.top_m:.2f} m ({band.source})", line_id, note)


def corner_edges(room, ext, inn, band, line_id, source):
    """External corners exposed (R-T368-1/2); internal corners listed, never exposed."""
    e = _vertical(room, f"{room}#EXT", "EXTERNAL_CORNER", ext, band, line_id, source)
    i = Edge(f"{room}#INT", room, "INTERNAL_CORNER", inn,
             None if band.top_m is None else round(inn * band.top_m, 4), None, "NOT_EXPOSED", DC, source,
             line_id, "concave: the two tiled faces butt")
    return [e, i]


def end_edges(room, wall_ends, flat_stops, band, line_id, source):
    out = []
    if wall_ends:
        out.append(_vertical(room, f"{room}#WEND", "WALL_END", wall_ends, band, line_id, source))
    if flat_stops:
        out.append(_vertical(room, f"{room}#FSTOP", "FLAT_STOP", flat_stops, band, line_id, source,
                             "F-T368-1: no second tiled face meets it; a mitre has nothing to meet"))
    return out


@dataclass(frozen=True)
class OpenSide:
    """An open side of a tiled room (a gap in its wall line with no door leaf) and what the plan draws across it.
    crossing: "NONE" (nothing drawn across on either plan: clear to the ceiling, R-T368-1/2) | "HIDDEN" (an overhead
    element drawn with a HIDDEN linetype, R-T368-7) | "BEAM" (a beam on the slab plan over the side's ends, R-T368-7) |
    "CONTINUOUS" (a solid line: not an open side, refused here).
    head_m: soffit of the overhead element above the finished floor, m; None = not established."""
    side_id: str
    width_m: float
    wall_ends: int
    flat_stops: int
    crossing: str = "NONE"
    head_m: float | None = None
    evidence: str = ""


def open_side_edges(room, side: OpenSide, band: Band, line_id, source):
    """R-T368-7. Edges of one open side: the wall end(s) / flat stop(s) at its two ends and, under a head below the
    tile top, the head arris on this face."""
    if side.crossing not in ("NONE", "HIDDEN", "BEAM"):
        raise EdgeError(f"{room} {side.side_id}: crossing {side.crossing!r} is not an open side")
    if side.width_m <= 0 or side.width_m > 20:
        raise EdgeError(f"{room} {side.side_id}: width {side.width_m} m out of range (mm given?)")
    if side.head_m is not None and (side.head_m <= 0 or side.head_m > 20):
        raise EdgeError(f"{room} {side.side_id}: head {side.head_m} m out of range (mm given?)")
    src = source + (f"; {side.evidence}" if side.evidence else "")
    if side.crossing == "NONE" or band.top_m is None:
        if side.crossing != "NONE" and band.top_m is None:
            src += f"; {HEAD_HELD} too"
        return end_edges(room, side.wall_ends, side.flat_stops, band, line_id, src)
    top = band.top_m
    if side.head_m is not None and side.head_m >= top - 1e-9:   # head at or above the tile top: full band
        return end_edges(room, side.wall_ends, side.flat_stops, band, line_id,
                         src + f"; head {side.head_m:.2f} m >= tile top {top:.2f} m (R-T368-7)")
    out = []
    if side.head_m is not None:     # head inside the band: head-high ends + the head arris
        h = side.head_m
        for n, etype, tag, note in ((side.wall_ends, "WALL_END", "WEND", ""),
                                    (side.flat_stops, "FLAT_STOP", "FSTOP", "F-T368-1: no second tiled face meets it")):
            if n:
                out.append(Edge(f"{room}#{tag}", room, etype, n, round(n * h, 4), None, "EXPOSED", band.status,
                                src + f"; head {h:.2f} m below tile top {top:.2f} m (R-T368-7)", line_id, note))
        out.append(Edge(f"{room}#{side.side_id}#HEAD", room, "HEAD_ARRIS", 1, round(side.width_m, 4), None,
                        "EXPOSED", band.status, src, line_id, "underside arris of the head on this face"))
        return out
    for n, etype, tag in ((side.wall_ends, "WALL_END", "WEND"), (side.flat_stops, "FLAT_STOP", "FSTOP")):
        if n:   # range head .. top per edge: the lower bound is the unknown head, never 0
            out.append(Edge(f"{room}#{tag}", room, etype, n, None, (None, round(n * top, 4)), HELD, HELD, src,
                            line_id, f"{HEAD_HELD}: {n} edge(s), each head .. {top:.2f} m (never 0, never the full "
                                     "band by default)"))
    out.append(Edge(f"{room}#{side.side_id}#HEAD", room, "HEAD_ARRIS", 1, None, (0.0, round(side.width_m, 4)), HELD,
                    HELD, src, line_id, f"{HEAD_HELD}: 0 when the head is at or above the tile top, "
                                        f"{side.width_m:.3f} m when below"))
    return out


def check_open_sides(edges, sides):
    """Refuse a ledger that gives a HIDDEN-crossed open side with no established head a determinate band
    (R-T368-7). sides = {room: OpenSide}."""
    for room, side in sides.items():
        if side.crossing == "NONE" or side.head_m is not None:
            continue
        for e in edges:
            if e.room == room and e.etype in ("WALL_END", "FLAT_STOP", "HEAD_ARRIS") and e.exposed != HELD:
                raise EdgeError(f"{e.edge_id}: open side {side.side_id} lies under a {side.crossing} overhead element with no "
                                f"established head: {HEAD_HELD} (R-T368-7)")
        if not any(e.room == room and e.etype == "HEAD_ARRIS" for e in edges):
            raise EdgeError(f"{room}: head arris of {side.side_id} missing (R-T368-7)")
    return True


def opening_perimeter(op: Opening, band: Band):
    """Perimeter of the opening inside [0, tile top] on one face, m.l; None when a needed level is HELD."""
    if band.top_m is None or op.head_m is None:
        return None
    if op.width_m <= 0 or op.width_m > 20:
        raise EdgeError(f"{op.oid}: width {op.width_m} m out of range (mm given?)")
    top = band.top_m
    lo = max(op.sill_m, 0.0)
    hi = min(op.head_m, top)
    if hi <= lo:
        return 0.0
    per = 2.0 * (hi - lo)
    if op.head_m < top:
        per += op.width_m            # head edge inside the band
    if op.kind == "window" and op.sill_m > 0.0:
        per += op.width_m            # sill edge inside the band
    return round(per, 4)


def opening_edge(room, op: Opening, band: Band, line_id):
    per = opening_perimeter(op, band)
    etype = "OPENING_WINDOW" if op.kind == "window" else "OPENING_DOOR"
    eid = f"{room}#{op.oid}"
    if op.frame == "FLUSH":
        return Edge(eid, room, "UNDER_FRAME", 1, per, None, "NOT_EXPOSED", DC, op.frame_source, line_id,
                    f"{op.oid}: frame flush with the room face covers the tile edge")
    if op.frame == "ARCHITRAVE":
        return Edge(eid, room, "UNDER_FRAME", 1, per, None, "NOT_EXPOSED", DC, op.frame_source, line_id,
                    f"{op.oid}: drawn architrave covers the tile edge")
    if op.frame == "NONE":   # drawn with no frame at all (an open doorway with its arris drawn)
        if per is None:
            return Edge(eid, room, etype, 1, None, None, HELD, HELD, op.frame_source, line_id,
                        f"{op.oid}: perimeter HELD (band or head not established)")
        return Edge(eid, room, etype, 1, per, None, "EXPOSED", DC, op.frame_source, line_id)
    # NOT_DRAWN: exposure HELD between 0 (a frame / architrave covers it) and the whole perimeter (R-T368-3)
    return Edge(eid, room, etype, 1, None, None if per is None else (0.0, per), HELD, HELD,
                op.frame_source or "frame / architrave detail not drawn", line_id,
                f"{op.oid}: exposure HELD: FRAME_DETAIL_NOT_DRAWN" + ("" if per is not None else
                                                                       "; perimeter HELD too"))


def top_edge(room, tiled_m, band, line_id, ceiling_source):
    return Edge(f"{room}#TOP", room, "TOP_AT_CEILING", 1, round(tiled_m, 4), None, "NOT_EXPOSED", OA,
                ceiling_source, line_id, "the tile stops at the decor ceiling: covered")


# ----------------------------------------------------------------------------------------------- finish + checks

def finish_alternatives(exposed_m, printed=None):
    """R-T368-4. printed = MITRE / PROFILE when a drawing prints it, else both alternatives shown, choice HELD."""
    if printed is not None:
        if printed not in FINISHES:
            raise EdgeError(f"unknown finish {printed!r}")
        return {"choice": printed, MITRE: exposed_m if printed == MITRE else 0.0,
                PROFILE: exposed_m if printed == PROFILE else 0.0, "status": "PRINTED"}
    return {"choice": HELD, "alternative_" + MITRE: exposed_m, "alternative_" + PROFILE: exposed_m,
            "status": "EDGE_FINISH_NOT_ESTABLISHED (UP-CER-007: alternatives on the same m.l, never summed)"}


def check_ledger(edges):
    """Refuse every R-T368 breach. Returns the totals by type and status."""
    seen = set()
    tot = {"EXPOSED_m": 0.0, "HELD_count": 0, "HELD_range_hi_m": 0.0, "NOT_EXPOSED_m": 0.0, "by_type": {},
           "held_by_type": {}}
    for e in edges:
        if e.edge_id in seen:
            raise EdgeError(f"{e.edge_id}: edge counted twice")
        seen.add(e.edge_id)
        if not e.line_id:
            raise EdgeError(f"{e.edge_id}: no FIN.WALL.TILE line id (R-T368-5)")
        if e.etype in NOT_EXPOSED_TYPES and e.exposed != "NOT_EXPOSED":
            raise EdgeError(f"{e.edge_id}: {e.etype} is never exposed (R-T368-1)")
        if e.exposed == "EXPOSED":
            if e.etype not in EXPOSED_TYPES:
                raise EdgeError(f"{e.edge_id}: {e.etype} cannot be exposed")
            if e.length_m is None:
                raise EdgeError(f"{e.edge_id}: exposed without a length")
            if e.etype == "OPENING_DOOR" and e.status != DC:
                raise EdgeError(f"{e.edge_id}: a door edge is exposed only on drawn frame evidence (R-T368-3)")
            tot["EXPOSED_m"] += e.length_m
            tot["by_type"][e.etype] = round(tot["by_type"].get(e.etype, 0.0) + e.length_m, 4)
        elif e.exposed == HELD:
            if e.length_m is not None:
                raise EdgeError(f"{e.edge_id}: a HELD edge carries no determinate length (never 0)")
            tot["HELD_count"] += e.count
            if e.range_m:
                tot["HELD_range_hi_m"] += e.range_m[1]
                hb = tot.setdefault("held_by_type", {}).setdefault(e.etype, {"count": 0, "hi_m": 0.0})
                hb["count"] += e.count
                hb["hi_m"] = round(hb["hi_m"] + e.range_m[1], 4)
        elif e.exposed == "NOT_EXPOSED":
            if e.length_m is not None:
                tot["NOT_EXPOSED_m"] += e.length_m
        else:
            raise EdgeError(f"{e.edge_id}: exposure {e.exposed!r}")
        fin = e.finish or {}
        if fin and fin.get("choice") in FINISHES and fin.get(MITRE, 0) and fin.get(PROFILE, 0):
            raise EdgeError(f"{e.edge_id}: both finishes on one edge (UP-CER-007)")
    for k in ("EXPOSED_m", "HELD_range_hi_m", "NOT_EXPOSED_m"):
        tot[k] = round(tot[k], 4)
    return tot


def refuse_summed_finishes(total_m, mitre_m, profile_m):
    """total_m = exposed edge m.l; the finish m.l may split it edge by edge but never exceed it (UP-CER-007)."""
    if mitre_m < 0 or profile_m < 0:
        raise EdgeError("negative finish m.l")
    if mitre_m + profile_m > total_m + 1e-6:
        raise EdgeError("finish m.l exceed the exposed edge m.l: an edge carries two finishes")
    return True


SOLID = ("WALL", "COLUMN")


def wall_corner_classes(points, edge_classes):
    """R-T368-6 (lesson F-T368-2). Corners counted only between two SOLID edges (a wall or column face). edge_classes[i]
    is the class of the edge from vertex i to vertex i+1 (WALL / COLUMN / COUNTER / ZONE / OPEN / DOOR). A room polygon
    that closes on a counter, a zone line or an open side has reflex vertices that are not wall corners: they are
    refused as external corners here (the pantry engine room's one reflex is a counter end)."""
    pts = [tuple(p) for p in points]
    if len(pts) > 1 and pts[0] == pts[-1]:
        pts = pts[:-1]
    if len(edge_classes) != len(pts):
        raise EdgeError("one class per polygon edge")
    area2 = sum(pts[i][0] * pts[(i + 1) % len(pts)][1] - pts[(i + 1) % len(pts)][0] * pts[i][1]
                for i in range(len(pts)))
    classes = list(edge_classes)
    if area2 < 0:   # reversed walk: vertex i of the reversed list sits between reversed edges
        pts = pts[::-1]
        classes = [classes[(len(pts) - 2 - i) % len(pts)] for i in range(len(pts))]
    turns = polygon_turns(pts)
    ext = inn = other = 0
    n = len(pts)
    for i, t in enumerate(turns):
        if abs(t) <= REFLEX_DEG:
            continue
        solid = classes[i - 1] in SOLID and classes[i] in SOLID
        if not solid:
            other += 1
        elif t < 0:
            ext += 1
        else:
            inn += 1
    return ext, inn, other
