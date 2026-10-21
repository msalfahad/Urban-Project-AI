"""INDEPENDENT REFERENCE READER - rooms and openings of a DXF plan from its raw entities, without the engine:
ezdxf reads the drawing (read-only), shapely nodes the wall-face linework and polygonises it, and each room is the
smallest face containing its room-word text. Openings: a gap of 0.30 - 2.60 m between collinear wall-face segments is
closed on that face line (not where a parallel face within 0.30 m runs on behind it - a column standing proud of a
wall); a closure is a DOOR when a door swing arc (in any block, mirrored blocks transformed to world coordinates)
has its centre at a jamb and its radius about the gap, a WINDOW when glazing lines run in the gap, else a PASSAGE.
Coordinates are taken to mm by $INSUNITS (mm, cm, m, inch; no unit: NOT_SUPPORTED); wall arcs and bulged polyline
segments are flattened to 0.5 mm; an external reference on a wall layer is NOT_SUPPORTED (its geometry is not in
the file), never read as an empty plan. DIMENSION entities are not read.

    read(path, wall_layers, door_layers, glazing_layers, text_layers) ->
        {"rooms": [{"name", "area_m2", "perimeter_m", "holes_m2", "polygon_mm", "openings": [...]}], "status"}
"""

from __future__ import annotations

import math
from collections import defaultdict

SNAP = 1.0
UNIT_MM = {1: 25.4, 4: 1.0, 5: 10.0, 6: 1000.0}               # $INSUNITS -> mm per drawing unit
SAGITTA_MM = 0.5                                              # wall arc flattening (area error < 2/3 x 0.5 mm x length)


def _flatten(e, out, layer=None, depth=0, k=1.0):
    t = e.dxftype()
    try:
        L = e.dxf.layer
    except Exception:
        L = "?"
    if L == "0" and layer is not None:
        L = layer
    if t == "LINE":
        out.append((L, "LINE", [(e.dxf.start.x * k, e.dxf.start.y * k), (e.dxf.end.x * k, e.dxf.end.y * k)], e))
    elif t == "LWPOLYLINE":
        if any(abs(q[0]) > 1e-12 for q in e.get_points("b")):
            from ezdxf import path as EP
            pts = [(v.x * k, v.y * k) for v in EP.make_path(e).flattening(SAGITTA_MM / k)]
        else:
            pts = [(p[0] * k, p[1] * k) for p in e.get_points("xy")]
            if e.closed and pts:
                pts.append(pts[0])
        out.append((L, t, pts, e))
    elif t == "ARC":
        c = e.ocs().to_wcs(e.dxf.center)
        out.append((L, t, [(v.x * k, v.y * k) for v in e.flattening(SAGITTA_MM / k)],
                    {"centre": (c.x * k, c.y * k), "r": e.dxf.radius * k}))
    elif t == "INSERT" and depth < 4:
        for v in e.virtual_entities():
            _flatten(v, out, L, depth + 1, k)
    elif t in ("TEXT", "MTEXT"):
        p = e.dxf.insert
        out.append((L, t, [(p.x * k, p.y * k)], e.dxf.text if t == "TEXT" else e.plain_text()))


def _line_key(a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    ang = math.degrees(math.atan2(dy, dx)) % 180.0
    t = math.radians(ang)
    ux, uy = math.cos(t), math.sin(t)
    return ang, (ux, uy), -uy * a[0] + ux * a[1]


def _same_dir(a, b):
    return abs(((a - b + 90) % 180) - 90) <= 0.05


def closures(segs, gmin=300.0, gmax=2600.0, behind=300.0, wall=(80.0, 320.0)):
    """the opening closures: a gap of gmin - gmax between two collinear face segments (direction within 0.05 deg,
    offset within 3 mm), closed between their actual end points, when (a) both neighbouring segments belong to a
    wall - another face runs parallel to each at a wall thickness (wall mm) - and (b) no parallel face within
    `behind` mm runs on across the gap (the face behind a column standing proud of the wall)."""
    recs = []
    for a, b in segs:
        if math.dist(a, b) >= 1.0:
            ang, u, off = _line_key(a, b)
            recs.append((ang, off, u, a, b))
    recs.sort(key=lambda r: (round(r[0] / 0.05), r[1]))
    groups = []
    for r in recs:
        g = groups[-1] if groups else None
        if g and _same_dir(r[0], g[0][0]) and abs(r[1] - g[-1][1]) <= 3.0:
            g.append(r)
        else:
            groups.append([r])

    def proj(u, p):
        return u[0] * p[0] + u[1] * p[1]

    def parallel_within(ang, off, u, s0, s1, lo, hi, need):
        for ang2, off2, _, a2, b2 in recs:
            if not _same_dir(ang2, ang) or not lo <= abs(off2 - off) <= hi:
                continue
            p0, p1 = sorted((proj(u, a2), proj(u, b2)))
            if min(p1, s1) - max(p0, s0) >= need:
                return True
        return False
    out = []
    for g in groups:
        u = g[0][2]
        iv = sorted(((proj(u, a), a), (proj(u, b), b)) if proj(u, a) <= proj(u, b) else ((proj(u, b), b), (proj(u, a), a))
                    for _, _, _, a, b in g)
        merged = []                                     # [s0, p0, s1, p1]
        for (s0, p0), (s1, p1) in iv:
            if merged and s0 <= merged[-1][2] + SNAP:
                if s1 > merged[-1][2]:
                    merged[-1][2], merged[-1][3] = s1, p1
            else:
                merged.append([s0, p0, s1, p1])
        ang, off = g[0][0], sum(r[1] for r in g) / len(g)
        for m0, m1 in zip(merged, merged[1:]):
            gap = m1[0] - m0[2]
            if not gmin <= gap <= gmax:
                continue
            if parallel_within(ang, off, u, m0[2] - 100.0, m1[0] + 100.0, 1.0, behind, 0.9 * gap + 200.0):
                continue                                # the wall face runs on behind (a pilaster / column); a
                #                                         glazing line that only spans the gap does not count
            if not all(parallel_within(ang, off, u, a, b, wall[0], wall[1], min(100.0, 0.5 * (b - a)))
                       for a, b in ((m0[0], m0[2]), (m1[0], m1[2]))):
                continue                                # a neighbour is not a wall face (a jamb, a column edge)
            out.append((m0[3], m1[1]))
    return out


def read(path, wall_layers=("A-WALL", "A-COL"), door_layers=("A-DOOR",), glazing_layers=("A-GLAZ",),
         text_layers=("A-TEXT",), min_text_height=200.0):
    import ezdxf
    from shapely.geometry import LineString, Point, Polygon
    from shapely.ops import polygonize, unary_union
    doc = ezdxf.readfile(str(path))
    k = UNIT_MM.get(doc.header.get("$INSUNITS", 0))
    if k is None:
        return {"rooms": [], "status": f"NOT_SUPPORTED: $INSUNITS {doc.header.get('$INSUNITS', 0)} (no length unit)"}
    xrefs = {b.name: b.block.dxf.xref_path for b in doc.blocks if b.block is not None and b.block.is_xref}
    for e in doc.modelspace().query("INSERT"):
        if e.dxf.name in xrefs and e.dxf.layer in wall_layers:
            return {"rooms": [], "status": f"NOT_SUPPORTED: XREF {e.dxf.name} -> {xrefs[e.dxf.name]} is not resolved "
                                           f"(the walls it draws are not in this file)"}
    ents = []
    for e in doc.modelspace():
        _flatten(e, ents, k=k)
    segs = [(a, b) for L, t, pts, _ in ents if L in wall_layers for a, b in zip(pts, pts[1:]) if math.dist(a, b) > 0]
    arcs = [x for L, t, pts, x in ents if L in door_layers and t == "ARC"]
    glaz = [LineString(pts) for L, t, pts, _ in ents if L in glazing_layers and len(pts) >= 2]
    cl = closures(segs)
    faces = list(polygonize(unary_union([LineString([a, b]) for a, b in segs] + [LineString(list(c)) for c in cl])))
    cl_lines = [LineString(list(c)) for c in cl]
    rooms = []
    texts = [(e.dxf.text, (e.dxf.insert.x * k, e.dxf.insert.y * k), e.dxf.height * k)
             for e in doc.modelspace().query("TEXT") if e.dxf.layer in text_layers]
    for word, p, h in texts:
        if h < min_text_height:
            continue
        cand = [f for f in faces if f.contains(Point(p))]
        if not cand:
            rooms.append({"name": word, "status": "NO_FACE"})
            continue
        f = min(cand, key=lambda q: q.area)
        ops = []
        for c in cl_lines:
            if c.within(f.exterior.buffer(2.0)):
                a, b = list(c.coords)
                kind = "PASSAGE"
                for arc in arcs:
                    if min(math.dist(arc["centre"], a), math.dist(arc["centre"], b)) <= 320 and \
                            abs(arc["r"] - c.length) <= 120:
                        kind = "DOOR"
                        break
                if kind == "PASSAGE" and any(gl.distance(c) <= 250 and gl.length >= 0.8 * c.length for gl in glaz):
                    kind = "WINDOW"
                ops.append({"kind": kind, "width_m": round(c.length / 1000, 4),
                            "mid_mm": ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)})
        rooms.append({"name": word, "area_m2": f.area / 1e6, "perimeter_m": f.exterior.length / 1000,
                      "holes_m2": sum(Polygon(h).area for h in f.interiors) / 1e6,
                      "polygon_mm": [tuple(q) for q in f.exterior.coords], "openings": sorted(ops, key=lambda o: o["width_m"]),
                      "status": "OK"})
    return {"rooms": rooms, "status": "OK"}
