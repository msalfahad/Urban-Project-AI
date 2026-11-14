"""T-788 rules (every villa; research module, unwired).

PHYSICAL ELEMENT: the gypsum ceiling cornice (moulding) run at the junction of a decor (false) ceiling and the wall
faces of a room or open zone. It is an interior item: the freelancer bills it under "decor gypsum" (halls / rooms and
wet rooms, lm), not on the facades.

R-T788-1 CORNICE RUN: a zone with a decor ceiling carries one cornice run = the length of its boundary on wall lines.
  Edge classes: WALL (wall / column face, counted), OPENING (a door, window or arch gap inside a wall line: the wall
  above the head reaches the ceiling, so the run continues over it, counted), OPEN_SIDE (the same ceiling continues
  into the next zone, no wall: not counted), VOID (the ceiling edge at a slab opening / light well: a ceiling drop
  item, not cornice, not counted). A zone without a decor ceiling (open stair well under a sloped soffit) carries no
  run. A wall between two zones gives each zone its own run (both faces). Supersedes the T-147 / T-771 practice of
  leaving every open zone out ("run not closed"), which dropped the wall faces of the open zones.
R-T788-2 PERIMETER PARTITION: when one plan face (an open space) is split into zones by cut regions, every sampled
  point of the face boundary belongs to exactly one zone (the first region containing it, else the default zone), so
  the zone runs add up to the face perimeter and no clip sliver is counted twice. The cut lines themselves are not
  wall (OPEN_SIDE) unless they lie inside a wall line (then OPENING, added by the caller).
R-T788-3 ROOM SIDE ONLY (Checker F-T788 r1, 2026-11-14): a zone's run counts only boundary whose room side is the
  zone interior inside the building envelope. When a plan face leaks to the yard and a cut region takes a piece of it,
  every disjoint piece of (face x region) is tested for enclosure: a piece from which straight rays (16 directions,
  40 m) reach no barrier line (wall, column, window) in at least 2 directions is OUTDOOR. An outdoor piece is not part
  of the zone: its boundary (e.g. the OUTER face of a curved glazing line) is not counted, and a cut line that bounds
  it is OPEN_SIDE, never OPENING. A window / wall line between the room and the outdoors counts once (inner face).
"""
from __future__ import annotations

import math

COUNTED = {"WALL", "OPENING"}
NOT_COUNTED = {"OPEN_SIDE", "VOID"}
MAX_EDGE_M = 60.0          # one straight edge of a villa room above 60 m is a units error (mm read as m)


def cornice_run(edges, has_decor_ceiling):
    """R-T788-1: cornice lm of one zone from its classified edges [(length_m, class)]."""
    if has_decor_ceiling is None:
        raise ValueError("ceiling type unknown: HELD, never 0")
    if not has_decor_ceiling:
        return 0.0                         # NOT_APPLICABLE (no decor ceiling), a physical zero, stated by the caller
    if not edges:
        raise ValueError("zone has no edges: geometry missing (HELD)")
    tot = 0.0
    for length, cls in edges:
        if length is None:
            raise ValueError("edge length missing")
        if length < 0 or length > MAX_EDGE_M:
            raise ValueError(f"edge length {length} not in metres")
        if cls in COUNTED:
            tot += length
        elif cls not in NOT_COUNTED:
            raise ValueError(f"unknown edge class {cls!r}")
    return round(tot, 3)


RAY_DIRS, RAY_LEN_M, OUTDOOR_MIN_ESCAPES = 16, 40.0, 2


def is_outdoor(piece, barriers, n=RAY_DIRS, length=RAY_LEN_M, min_escapes=OUTDOOR_MIN_ESCAPES):
    """R-T788-3: True when rays from an interior point of `piece` escape the barrier lines in >= min_escapes directions."""
    from shapely import STRtree
    from shapely.geometry import LineString

    if piece is None or piece.is_empty:
        raise ValueError("piece missing")
    if not barriers:
        raise ValueError("no barrier lines: enclosure unknown (HELD, never assumed indoor)")
    tree = STRtree(list(barriers))
    p = piece.representative_point()
    escapes = 0
    for k in range(n):
        a = 2 * math.pi * k / n
        ray = LineString([(p.x, p.y), (p.x + length * math.cos(a), p.y + length * math.sin(a))])
        if not any(barriers[i].intersects(ray) for i in tree.query(ray)):
            escapes += 1
    return escapes >= min_escapes


def split_outdoor(face, region, barriers):
    """R-T788-3: (indoor part, [outdoor pieces]) of face x region; an outdoor piece is not part of the zone."""
    part = face.intersection(region)
    pieces = [part] if part.geom_type == "Polygon" else [g for g in getattr(part, "geoms", []) if g.area > 0]
    indoor, outdoor = [], []
    for g in pieces:
        (outdoor if is_outdoor(g, barriers) else indoor).append(g)
    from shapely.ops import unary_union
    return unary_union(indoor), outdoor


def partition_perimeter(parent, regions, default, step=0.005):
    """R-T788-2: {zone: boundary length} of a shapely (Multi)Polygon split by named regions (dict, checked in order)."""
    from shapely.geometry import Point

    if parent is None or parent.is_empty:
        raise ValueError("parent face missing")
    minx, miny, maxx, maxy = parent.bounds
    if max(maxx - minx, maxy - miny) > 500:
        raise ValueError("face larger than 500 m: drawing units not metres")
    grown = {k: r.buffer(0.002) for k, r in regions.items()}
    out = {k: 0.0 for k in list(regions) + [default]}
    polys = [parent] if parent.geom_type == "Polygon" else list(parent.geoms)
    for poly in polys:
        for ring in [poly.exterior, *poly.interiors]:
            c = list(ring.coords)
            for a, b in zip(c, c[1:]):
                seg = math.dist(a, b)
                n = max(1, int(seg / step))
                for k in range(n):
                    t = (k + 0.5) / n
                    p = Point(a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
                    key = next((kk for kk, g in grown.items() if g.contains(p)), default)
                    out[key] += seg / n
    return {k: round(v, 3) for k, v in out.items()}
