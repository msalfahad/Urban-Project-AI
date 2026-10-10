"""ezdxf as an INDEPENDENT corroboration oracle for the hand-derived truth.

ezdxf 1.4.4 (MIT) is a separate code base from Urban's kernel and from the
test-side reference realiser. It is used here only to confirm that the
hand-written point maps in ``scenes.py`` agree with a mature DXF
implementation. It is not a production dependency of anything in this round.

Known ezdxf behaviour this module works around, and that
``test_r8_0_library_characterisation.py`` pins:
* ``Insert.virtual_entities()`` on a MINSERT yields only the first grid cell;
  ``multi_insert()`` yields every cell.
* An xref INSERT yields no virtual entities.
"""

from __future__ import annotations

import math

import ezdxf

from .geometry import close


def build(scene):
    doc = ezdxf.new()
    msp = doc.modelspace()
    for name, blk in scene.get("blocks", {}).items():
        if blk.get("xref"):
            doc.add_xref_def(blk["xref"]["path"], name)
        else:
            doc.blocks.new(name, base_point=(*blk.get("base", (0.0, 0.0)), 0.0))
    for name, blk in scene.get("blocks", {}).items():
        if blk.get("xref"):
            continue
        layout = doc.blocks.get(name)
        for e in blk.get("entities", []):
            _add(layout, e)
    for e in scene.get("entities", []):
        _add(msp, e)
    return doc


def _add(layout, e):
    k = e["kind"]
    ext = tuple(e.get("extrusion", (0.0, 0.0, 1.0)))
    if k == "LINE":
        return layout.add_line((*e["a"], 0.0), (*e["b"], 0.0), dxfattribs={"extrusion": ext})
    if k == "ARC":
        return layout.add_arc(e["c"], e["r"], e["a0"], e["a1"], dxfattribs={"extrusion": ext})
    if k == "LWPOLYLINE":
        pts = [(p[0], p[1], 0.0, 0.0, b) for p, b in zip(e["pts"], e.get("bulges", [0.0] * len(e["pts"])))]
        return layout.add_lwpolyline(pts, format="xyseb", close=bool(e.get("closed")),
                                     dxfattribs={"extrusion": ext})
    if k in ("INSERT", "MINSERT"):
        sx, sy = e.get("scale", (1.0, 1.0))
        ref = layout.add_blockref(e["block"], (*e["at"], 0.0),
                                  dxfattribs={"xscale": sx, "yscale": sy, "rotation": e.get("rot", 0.0),
                                              "extrusion": ext})
        if k == "MINSERT":
            ref.grid(size=(e["rows"], e["cols"]), spacing=(e["row_sp"], e["col_sp"]))
        return ref
    raise ValueError(f"no ezdxf form for {k}")


def _explode(entity, depth=0):
    if entity.dxftype() == "INSERT":
        if depth > 16:
            raise RuntimeError("nesting too deep")
        cells = entity.multi_insert() if entity.mcount > 1 else [entity]
        for cell in cells:
            for child in cell.virtual_entities():
                yield from _explode(child, depth + 1)
    else:
        yield entity


def _P(v):
    return (float(v.x), float(v.y))


def _arc_record(a):
    sa, ea = a.dxf.start_angle, a.dxf.end_angle
    sw = (ea - sa) % 360.0 or 360.0
    s, m, e = list(a.vertices([sa, sa + sw / 2.0, ea]))
    c = a.ocs().to_wcs(a.dxf.center)
    d = "CCW" if a.dxf.extrusion.z > 0 else "CW"   # OCS CCW about N, seen from +Z
    return {"CENTER": _P(c), "P0": _P(s), "PM": _P(m), "P1": _P(e), "DIR": d, "RADIUS": float(a.dxf.radius)}


def realise(scene):
    doc = build(scene)
    arcs, bulges, segs = [], [], []
    for top in doc.modelspace():
        for e in _explode(top):
            t = e.dxftype()
            if t == "LINE":
                segs.append((_P(e.dxf.start), _P(e.dxf.end)))
            elif t == "ARC":
                arcs.append(_arc_record(e))
            elif t == "LWPOLYLINE":
                verts = [_P(v) for v in e.vertices_in_wcs()]
                for sub in e.virtual_entities():
                    if sub.dxftype() == "ARC":
                        r = _arc_record(sub)
                        a, b = verts[0], verts[1]
                        if close(a, r["P0"]):
                            d = r["DIR"]
                        elif close(a, r["P1"]):
                            d = {"CCW": "CW", "CW": "CCW"}[r["DIR"]]
                        else:
                            d = "INCONSISTENT"
                        bulges.append({"VERTEX_A": a, "VERTEX_B": b, "ARC_MIDPOINT": r["PM"],
                                       "CENTER": r["CENTER"], "DIR_A_TO_B": d})
                    elif sub.dxftype() == "LINE":
                        segs.append((_P(sub.dxf.start), _P(sub.dxf.end)))
    return {"arcs": arcs, "bulges": bulges, "segments": segs}
