"""ARCH INTAKE (M9 S2) - the architectural route's extra readings of a DXF, next to tools/urban_intake.py (unchanged).

    hatches(path) -> [{"id", "layer", "pattern", "rings": [outer, island, ...], "area_native", "owner", "mirrored"}]

Why a second reader: urban_intake.read_dxf keeps only the FIRST boundary path of a model-space hatch, in the hatch's
own OCS. That loses islands (a hatch with a hole reads as the full outer ring) and places a mirrored hatch (extrusion
0,0,-1) at mirrored coordinates; hatches inside blocks are not read at all. Route G reads those hatch records, so the
M2-M8 outputs depend on them: the fix is NOT applied there (it would change frozen results and needs owner approval).
This reader is used by the architectural route only:
    - every boundary path (external + islands), polyline bulges flattened, edge paths (lines / arcs / ellipses /
      splines) flattened by ezdxf
    - OCS -> WCS for every vertex (a mirrored hatch lands where it is drawn)
    - hatches inside blocks placed by ezdxf's virtual entities (INSERT transforms, mirrored INSERTs included)
    - area = outer ring - islands (nested-path parity), in drawing units squared
"""

from __future__ import annotations

import math


def _ring_area(r):
    return abs(sum(r[i - 1][0] * r[i][1] - r[i][0] * r[i - 1][1] for i in range(len(r)))) / 2.0


def _point_in(p, ring):
    ins = False
    for i in range(len(ring)):
        (x1, y1), (x2, y2) = ring[i], ring[(i + 1) % len(ring)]
        if (y1 > p[1]) != (y2 > p[1]) and p[0] < (x2 - x1) * (p[1] - y1) / (y2 - y1 + 1e-300) + x1:
            ins = not ins
    return ins


def _path_points(path, ocs, elevation):
    """one boundary path as WCS points: ezdxf.path converts the OCS path (bulges / arcs / ellipses / splines) to WCS."""
    from ezdxf import path as P_
    p = P_.from_hatch_boundary_path(path, ocs=ocs, elevation=elevation)
    pts = [(v.x, v.y) for v in p.flattening(distance=0.5)]
    if len(pts) > 1 and math.dist(pts[0], pts[-1]) < 1e-9:
        pts = pts[:-1]
    return pts


def _read(h, owner=None):
    ocs = h.ocs()
    elev = h.dxf.elevation.z if h.dxf.hasattr("elevation") else 0.0
    rings = []
    for path in h.paths:
        try:
            r = _path_points(path, ocs, elev)
        except Exception:                                             # noqa: BLE001 - an unreadable path is reported
            r = []
        if len(r) >= 3:
            rings.append(r)
    rings.sort(key=_ring_area, reverse=True)
    # parity: a ring inside an odd number of others is an island
    area = 0.0
    for i, r in enumerate(rings):
        depth = sum(1 for j, o in enumerate(rings) if j != i and _point_in(r[0], o))
        area += _ring_area(r) * (1 if depth % 2 == 0 else -1)
    ext = tuple(h.dxf.get("extrusion", (0, 0, 1)))
    return {"id": h.dxf.handle, "layer": h.dxf.layer, "pattern": h.dxf.pattern_name, "rings": rings,
            "area_native": area, "owner": owner, "mirrored": ext[2] < 0, "islands": max(len(rings) - 1, 0)}


def hatches(path):
    import ezdxf
    doc = ezdxf.readfile(str(path))
    out = []
    msp = doc.modelspace()
    for h in msp.query("HATCH"):
        out.append(_read(h))
    for ins in msp.query("INSERT"):
        try:
            for e in ins.virtual_entities():
                if e.dxftype() == "HATCH":
                    out.append(_read(e, owner=ins.dxf.handle))
        except Exception:                                             # noqa: BLE001 - a block that cannot explode
            continue
    return out
