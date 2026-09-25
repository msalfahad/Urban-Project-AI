"""Synthetic drawing builders for the PA07 tests.  Everything is in mm; no P7757 geometry."""

from __future__ import annotations

import math
from types import SimpleNamespace

_n = [0]


def reset():
    _n[0] = 0


def seg(layer, a, b, block=(), linetype="CONTINUOUS", role=None):
    _n[0] += 1
    return SimpleNamespace(kind="SEGMENT", object_id=f"E{_n[0]}", x1=float(a[0]), y1=float(a[1]), x2=float(b[0]), y2=float(b[1]), cx=0.0, cy=0.0, radius=0.0, start_angle=0.0, end_angle=0.0,
                           provenance=SimpleNamespace(layer=layer, handle=_n[0], entity_type="LINE", block_path=tuple(block), instance_path=(), linetype=linetype, linetype_source="TEST", invisible=False, lineweight=None),
                           _role=role)


def arc(layer, c, r, a0, a1, block=(), linetype="CONTINUOUS", role=None):
    _n[0] += 1
    return SimpleNamespace(kind="ARC", object_id=f"E{_n[0]}", x1=0.0, y1=0.0, x2=0.0, y2=0.0, cx=float(c[0]), cy=float(c[1]), radius=float(r), start_angle=float(a0), end_angle=float(a1),
                           provenance=SimpleNamespace(layer=layer, handle=_n[0], entity_type="ARC", block_path=tuple(block), instance_path=(), linetype=linetype, linetype_source="TEST", invisible=False, lineweight=None),
                           _role=role)


def wall(a, b, t=200.0, layer="W"):
    """Two parallel faces from a to b (axis), thickness t."""
    L = math.hypot(b[0] - a[0], b[1] - a[1]); ux, uy = (b[0] - a[0]) / L, (b[1] - a[1]) / L; nx, ny = -uy, ux
    return [seg(layer, (a[0] + nx * t / 2, a[1] + ny * t / 2), (b[0] + nx * t / 2, b[1] + ny * t / 2)),
            seg(layer, (a[0] - nx * t / 2, a[1] - ny * t / 2), (b[0] - nx * t / 2, b[1] - ny * t / 2))]


def cap(a, b, t=200.0, at="both", layer="W"):
    """End faces across the wall thickness at the axis ends."""
    L = math.hypot(b[0] - a[0], b[1] - a[1]); ux, uy = (b[0] - a[0]) / L, (b[1] - a[1]) / L; nx, ny = -uy, ux
    out = []
    if at in ("both", "start"):
        out.append(seg(layer, (a[0] + nx * t / 2, a[1] + ny * t / 2), (a[0] - nx * t / 2, a[1] - ny * t / 2)))
    if at in ("both", "end"):
        out.append(seg(layer, (b[0] + nx * t / 2, b[1] + ny * t / 2), (b[0] - nx * t / 2, b[1] - ny * t / 2)))
    return out


def rect(x0, y0, x1, y1, layer="W", block=()):
    return [seg(layer, (x0, y0), (x1, y0), block), seg(layer, (x1, y0), (x1, y1), block), seg(layer, (x1, y1), (x0, y1), block), seg(layer, (x0, y1), (x0, y0), block)]


def curved_wall(c, r_axis, t, a0, a1, layer="W"):
    return [arc(layer, c, r_axis - t / 2, a0, a1), arc(layer, c, r_axis + t / 2, a0, a1)]


def hatch(x0, y0, x1, y1, pitch=100.0, layer="H"):
    """45-degree strokes filling a rectangle (a section hatch), each stroke clipped to the box."""
    out = []
    d = x0 + y0 - 2 * pitch
    while d < x1 + y1:
        pts = []
        for (x, y) in ((x0, d - x0), (x1, d - x1), (d - y0, y0), (d - y1, y1)):
            if x0 - 1e-6 <= x <= x1 + 1e-6 and y0 - 1e-6 <= y <= y1 + 1e-6:
                pts.append((x, y))
        pts = sorted(set((round(x, 3), round(y, 3)) for x, y in pts))
        if len(pts) >= 2 and math.hypot(pts[-1][0] - pts[0][0], pts[-1][1] - pts[0][1]) > 5:
            out.append(seg(layer, pts[0], pts[-1]))
        d += pitch
    return out


def roles_of(prims):
    """Role rows the way PA06 hands them over: explicit test roles, otherwise UNKNOWN_GEOMETRY (layer names carry nothing)."""
    return {p.object_id: {"OBJECT_ID": p.object_id, "ROLE": p._role or "UNKNOWN_GEOMETRY", "ROLE_STATUS": "TEST", "LAYER": p.provenance.layer} for p in prims}


def room(x0, y0, x1, y1, t=200.0, layer="W"):
    """Four walls around a clear rectangle x0..x1, y0..y1 drawn the CAD way: an inner face rectangle and an outer face rectangle."""
    return rect(x0, y0, x1, y1, layer) + rect(x0 - t, y0 - t, x1 + t, y1 + t, layer)
