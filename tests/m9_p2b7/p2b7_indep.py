"""Phase 2B-7 independent readers (ezdxf and math only - no engine module is imported here): the checks of the
per-line source-entity provenance and of the door-opening position read the DXF itself.

    resolve(doc, ref)        a traced reference {"handle", "insert_path", "part"} -> (entity, inserts); asserts the
                             handle exists, every insert of the path is an INSERT, each lives in the block of the one
                             before it (the first in model space) and the entity in the block of the last
    world(doc, ref, step)    the referenced piece (a LINE, an ARC / CIRCLE, one segment of an LWPOLYLINE - straight or
                             bulged - or any other curve through ezdxf.path) as a polyline in world metres: sampled in
                             its own block, carried out through the INSERT matrices of its path
    jamb_span(doc, layer, t) the door-layer LINEs spanning a wall of thickness t (world, through every block level):
                             their extreme positions along the wall, the span and its middle at mid wall"""

from __future__ import annotations

import math

import ezdxf
from ezdxf import disassemble
from ezdxf.math import OCS, Matrix44, Vec3, bulge_to_arc

UNITS_M = {4: 0.001, 5: 0.01, 6: 1.0}


def unit_m(doc):
    return UNITS_M[doc.header.get("$INSUNITS", 4)]


def resolve(doc, ref):
    db = doc.entitydb
    e = db.get(ref["handle"])
    assert e is not None and e.is_alive, ref
    ins = [db.get(h) for h in ref["insert_path"]]
    assert all(i is not None and i.dxftype() == "INSERT" for i in ins), ref
    owners = [doc.modelspace().block_record_handle] + [doc.blocks.get(i.dxf.name).block_record_handle for i in ins]
    for k, i in enumerate(ins):
        assert i.dxf.owner == owners[k], (ref, k, "insert outside its parent block")
    assert e.dxf.owner == owners[-1], (ref, "entity outside the innermost block of its path")
    return e, ins


def _arc_pts(c, r, a0, a1, step):
    sweep = (a1 - a0) % (2 * math.pi) or 2 * math.pi
    n = max(3, int(sweep * r / step) + 2)
    return [(c[0] + r * math.cos(a0 + sweep * k / (n - 1)), c[1] + r * math.sin(a0 + sweep * k / (n - 1)))
            for k in range(n)]


def _local(e, part, step):
    t = e.dxftype()
    if t == "LINE":
        return [Vec3(e.dxf.start), Vec3(e.dxf.end)]
    if t in ("ARC", "CIRCLE"):
        ocs, c = OCS(e.dxf.extrusion), Vec3(e.dxf.center)
        a0, a1 = (math.radians(e.dxf.start_angle), math.radians(e.dxf.end_angle)) if t == "ARC" else (0.0, 0.0)
        return [ocs.to_wcs(Vec3(x, y, c.z)) for x, y in _arc_pts(c, e.dxf.radius, a0, a1, step)]
    if t == "LWPOLYLINE":
        pts = list(e.get_points("xyb"))
        assert 0 <= part < len(pts) - (0 if e.closed else 1), (e.dxf.handle, part)
        (x0, y0, b), (x1, y1, _) = pts[part], pts[(part + 1) % len(pts)]
        ocs, z = OCS(e.dxf.extrusion), e.dxf.elevation
        if abs(b) < 1e-12:
            xy = [(x0, y0), (x1, y1)]
        else:
            c, sa, ea, r = bulge_to_arc((x0, y0), (x1, y1), b)
            xy = _arc_pts(c, r, sa, ea, step)
            if b < 0:                                        # a clockwise bulge: the arc runs from the end point
                xy.reverse()
        return [ocs.to_wcs(Vec3(x, y, z)) for x, y in xy]
    return list(ezdxf.path.make_path(e).flattening(step / 10))


def world(doc, ref, step_m=0.005):
    e, ins = resolve(doc, ref)
    k = unit_m(doc)
    pts = _local(e, ref["part"], step_m / k)
    if ins:
        m = Matrix44.chain(*[i.matrix44() for i in reversed(ins)])
        pts = list(m.transform_vertices(pts))
    return [(p.x * k, p.y * k) for p in pts]


def d_seg(p, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    L2 = dx * dx + dy * dy
    t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / L2))
    return math.dist(p, (a[0] + t * dx, a[1] + t * dy))


def d_poly(p, poly, closed=False):
    n = len(poly)
    return min(d_seg(p, poly[i], poly[(i + 1) % n]) for i in range(n if closed else n - 1))


def sample(poly, step_m=0.005, closed=False):
    """points every step along a polyline (its vertices included)."""
    out = []
    n = len(poly)
    for i in range(n if closed else n - 1):
        a, b = poly[i], poly[(i + 1) % n]
        L = math.dist(a, b)
        k = max(1, int(L / step_m))
        out += [(a[0] + (b[0] - a[0]) * j / k, a[1] + (b[1] - a[1]) * j / k) for j in range(k)]
    if not closed:
        out.append(poly[-1])
    return out


def length(poly, closed=False):
    n = len(poly)
    return sum(math.dist(poly[i], poly[(i + 1) % n]) for i in range(n if closed else n - 1))


def jamb_span(doc, layer, t_m, tol_m=0.001):
    """-> {"axis", "lo", "hi", "width_m", "centre_m"} from the world LINEs on `layer` whose length is the wall thickness
    (every block level decomposed by ezdxf); the axis is perpendicular to them."""
    k = unit_m(doc)
    js = []
    for e in disassemble.recursive_decompose(doc.modelspace()):
        if e.dxftype() == "LINE" and e.dxf.layer == layer:
            a, b = (e.dxf.start.x * k, e.dxf.start.y * k), (e.dxf.end.x * k, e.dxf.end.y * k)
            if abs(math.dist(a, b) - t_m) <= tol_m:
                js.append((a, b))
    assert js, "no jamb line"
    a, b = js[0]
    L = math.dist(a, b)
    n = ((b[0] - a[0]) / L, (b[1] - a[1]) / L)                 # across the wall
    u = (n[1], -n[0])                                          # along the wall
    mids = [((p[0] + q[0]) / 2, (p[1] + q[1]) / 2) for p, q in js]
    s = [m[0] * u[0] + m[1] * u[1] for m in mids]
    i_lo, i_hi = s.index(min(s)), s.index(max(s))
    lo, hi = mids[i_lo], mids[i_hi]
    return {"axis": u, "width_m": max(s) - min(s), "centre_m": ((lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2),
            "lines": len(js)}
