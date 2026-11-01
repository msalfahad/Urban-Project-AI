"""ZONE_EXTENT_V1 (T-427, research only, not wired): how far a labelled zone inside a room really extends.

Defect it answers (T-427, from T-153 / T-240 / T-418 on the development villa): a zone drawn inside a room (a garden /
planter band, a raised platform, a sunken area) was carried by the engine further than its own drawn outline: the
engine prolonged the zone's edge line past the line that ENDS the zone, so a piece of the room's floor between the zone's
drawn end and the room walls was cut off and HELD with the zone (and a strip along the prolonged edge line was HELD
with it). The floor-finish family lost that piece silently; the comparison with a gross-outline BOQ left it as an
"unexplained" residual.

Rule R-T427-1 (every villa; floor finishes / rooms; provenance T-427):
  1. a piece of a room's plan belongs to the room's FLOOR when it is joined to the room floor across an edge that NO
     drawn line marks (an undrawn edge of at least MIN_OPEN_M; an engine zone line or a prolonged edge line is not a
     drawn line): there is no physical element there to stop the floor;
  2. joining propagates (a piece joined to a joined piece is floor too); a piece separated from the floor on every edge
     by drawn lines (zone outline, curb, wall, column) keeps the engine's class (a ZONE or STRIP stays HELD with its zone,
     with its area, never 0; a SOLID piece is no floor);
  3. a printed dimension never extends a zone over a piece whose edges the drawing leaves open (a chain dimension may
     start at another element's line); the drawn outline governs, the dimension is reported beside it;
  4. the pieces re-add to the input (closure 0), never overlap, and a moved piece keeps its measured area: only its class
     and evidence change (area DRAWING-CONFIRMED; the finish takes the room's own finish status).

Units: 'm' or 'mm' on input (polygons and segments in the same unit); output m / m2. Geometry with shapely (pinned in
requirements.txt). No layer name, room id or dimension of any project is coded here.
"""
from __future__ import annotations

from shapely.geometry import LineString, Polygon
from shapely.ops import unary_union

METHOD = "ZONE_EXTENT_V1"
RULE = "R-T427-1"
CLASSES = ("ROOM_FLOOR", "ZONE", "STRIP", "SOLID")
STATUS_DC = "DRAWING-CONFIRMED"
STATUS_HELD = "HELD"
SCALE = {"m": 1.0, "mm": 0.001}
MIN_OPEN_M = 0.30      # an undrawn shared edge shorter than this is a drafting gap, not an open boundary
TOL_M = 0.01           # a drawn line within 10 mm of an edge marks that edge
TOL_M2 = 1e-6


class Refused(ValueError):
    """An input the rule refuses (no seed, overlap, unknown class / unit, missing polygon)."""


def _poly(pts, s):
    if not pts or len(pts) < 3:
        raise Refused("a piece has no polygon")
    p = Polygon([(x * s, y * s) for x, y in pts])
    if not p.is_valid or p.area <= TOL_M2:
        raise Refused("a piece polygon is invalid or empty")
    return p


def _undrawn(a, b, drawn, tol):
    """length (m) of the boundary a and b share that no drawn line marks"""
    shared = a.boundary.intersection(b.buffer(tol)).intersection(b.boundary.buffer(tol))
    if shared.is_empty or shared.length <= 0:
        return 0.0
    if drawn is None:
        return shared.length
    return shared.difference(drawn).length


def classify(pieces, drawn_segments, unit="m", min_open_m=MIN_OPEN_M, tol_m=TOL_M):
    """pieces: [{id, poly, engine_class in CLASSES, (zone), (status)}]; at least one ROOM_FLOOR piece (the seed: the
    room's floor as the engine has it). drawn_segments: [((x0, y0), (x1, y1)), ...] every drawn line near the zone (walls,
    zone outline, curb, column outlines, fixture lines); never an engine zone line. Returns a dict with one row per
    piece (physical class, change, open edge, status), the moved area and the closure."""
    if unit not in SCALE:
        raise Refused(f"unknown unit {unit!r}")
    s = SCALE[unit]
    rows, polys = [], {}
    for p in pieces:
        c = p.get("engine_class")
        if c not in CLASSES:
            raise Refused(f"piece {p.get('id')!r}: unknown class {c!r}")
        if p.get("id") in polys:
            raise Refused(f"piece {p['id']!r} given twice")
        polys[p["id"]] = _poly(p.get("poly"), s)
    if not any(p["engine_class"] == "ROOM_FLOOR" for p in pieces):
        raise Refused("no ROOM_FLOOR seed: the room's own floor must be given")
    ids = [p["id"] for p in pieces]
    for i, a in enumerate(ids):
        for b in ids[i + 1:]:
            if polys[a].intersection(polys[b]).area > TOL_M2:
                raise Refused(f"pieces {a!r} and {b!r} overlap (one m2, one piece)")
    segs = [LineString([(x0 * s, y0 * s), (x1 * s, y1 * s)]) for (x0, y0), (x1, y1) in drawn_segments]
    drawn = unary_union(segs).buffer(tol_m) if segs else None

    floor = {p["id"] for p in pieces if p["engine_class"] == "ROOM_FLOOR"}
    via = {}
    changed = True
    while changed:
        changed = False
        for p in pieces:
            if p["id"] in floor or p["engine_class"] == "SOLID":
                continue
            for f in sorted(floor):
                L = _undrawn(polys[p["id"]], polys[f], drawn, tol_m)
                if L >= min_open_m:
                    floor.add(p["id"])
                    via[p["id"]] = (f, round(L, 4))
                    changed = True
                    break
    moved = 0.0
    for p in pieces:
        a = polys[p["id"]].area
        phys = "ROOM_FLOOR" if p["id"] in floor else p["engine_class"]
        change = phys != p["engine_class"]
        if change:
            moved += a
        if phys == "ROOM_FLOOR":
            status = STATUS_DC if change else p.get("status", STATUS_DC)
        elif phys == "SOLID":
            status = "NOT_FLOOR"
        else:
            status = STATUS_HELD
        rows.append({"id": p["id"], "area_m2": round(a, 6), "engine_class": p["engine_class"], "physical_class": phys,
                     "changed": change, "joined_via": via.get(p["id"], (None, None))[0],
                     "open_edge_m": via.get(p["id"], (None, None))[1], "zone": p.get("zone"), "status": status})
    total_in = sum(polys[i].area for i in ids)
    total_out = sum(r["area_m2"] for r in rows)
    return {"method": METHOD, "rule": RULE, "rows": rows, "moved_to_floor_m2": round(moved, 6),
            "held_m2": round(sum(r["area_m2"] for r in rows if r["status"] == STATUS_HELD), 6),
            "closure_m2": round(total_out - total_in, 6)}


def close_residual(other_m2, parts):
    """re-add a comparison figure (a gross-outline row of another BOQ) against named parts [(name, m2, class)]; class is
    one of TRACED / HELD / NOT_FLOOR / UNEXPLAINED. The residual left after the named parts is returned as UNEXPLAINED,
    never dropped and never forced to 0."""
    for n, m2, c in parts:
        if m2 is None:
            raise Refused(f"part {n!r} has no quantity (HELD is a figure with a status, never None or 0)")
        if c not in ("TRACED", "HELD", "NOT_FLOOR", "UNEXPLAINED"):
            raise Refused(f"part {n!r}: unknown class {c!r}")
    named = round(sum(m2 for _, m2, _ in parts), 6)
    return {"other_m2": other_m2, "named_m2": named, "unexplained_m2": round(other_m2 - named, 6)}
