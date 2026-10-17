"""Test-side PAIRED fixtures: one scene -> (DXF document, LibreDWG-shaped decode) with the SAME handles.

A real DWG decoded by dwgread and exported by dwg2dxf keeps its handles in both
representations; this builder reproduces exactly that relation for synthetic
scenes so K1 (D1 decode) and K2 (DXF) can be correlated by SOURCE IDENTITY.
It makes no geometric decision: every number is copied from the ezdxf entity
as authored (OCS for ARC / CIRCLE / LWPOLYLINE / INSERT).
"""

from __future__ import annotations

import math

import ezdxf

from tests.r8_0 import ezdxf_oracle as EO


def _h(entity_or_handle):
    h = entity_or_handle if isinstance(entity_or_handle, str) else entity_or_handle.dxf.handle
    return int(h, 16)


def _ref(code, h):
    return [code, 1, h, h]


def build_dxf(scene):
    doc = EO.build(scene) if not scene.get("_extra") else EO.build(scene)
    for name, blk in scene.get("blocks", {}).items():                   # xref flags the oracle builder omits
        x = blk.get("xref")
        if x:
            b = doc.blocks.get(name).block
            flags = b.dxf.get("flags", 0) | 4 | (8 if x.get("overlay") else 0) | (32 if x.get("resolved") else 0)
            b.dxf.flags = flags
    return doc


def dxf_to_d1(doc, insunits=4):
    objs = []
    layers = {}

    def layer_ref(name):
        if name not in layers:
            lay = doc.layers.get(name) if doc.layers.has_entry(name) else None
            h = _h(lay) if lay is not None else 900000 + len(layers)
            layers[name] = h
            objs.append({"object": "LAYER", "type": 51, "handle": [0, 1, h], "name": name})
        return _ref(5, layers[name])

    msp_rec = _h(doc.modelspace().block_record)
    objs.append({"object": "BLOCK_HEADER", "type": 49, "handle": [0, 1, msp_rec], "name": "*MODEL_SPACE",
                 "base_pt": [0.0, 0.0, 0.0], "blkisxref": 0, "xrefoverlaid": 0, "entities": []})
    for blk in doc.blocks:
        if blk.name.lower() in ("*model_space",) or blk.name.lower().startswith("*paper_space"):
            continue
        rec = blk.block_record
        flags = blk.block.dxf.get("flags", 0)
        bp = blk.block.dxf.get("base_point", (0.0, 0.0, 0.0))
        objs.append({"object": "BLOCK_HEADER", "type": 49, "handle": [0, 1, _h(rec)], "name": blk.name,
                     "base_pt": [float(bp[0]), float(bp[1]), 0.0], "blkisxref": 1 if flags & 4 else 0,
                     "xrefoverlaid": 1 if flags & 8 else 0, "xref_pname": blk.block.dxf.get("xref_path", "") if flags & 4 else "",
                     "is_xref_resolved": 1 if flags & 32 else 0, "loaded_bit": 0, "entities": []})
        for e in blk:
            objs.append(_entity(e, _h(rec), layer_ref, doc))
    for e in doc.modelspace():
        objs.append(_entity(e, msp_rec, layer_ref, doc))
        if e.dxftype() == "INSERT":
            for a in e.attribs:
                objs.append({"entity": "ATTRIB", "type": 2, "handle": [0, 1, _h(a)], "ownerhandle": _ref(4, _h(e)),
                             "layer": layer_ref(a.dxf.layer), "ins_pt": _xy0(a.dxf.insert),
                             "tag": a.dxf.tag, "text_value": a.dxf.text, "extrusion": list(a.dxf.extrusion)})
    return {"FILEHEADER": {"version": "AC1018"}, "HEADER": {"INSUNITS": insunits}, "OBJECTS": objs}


def _xy0(v):
    return [float(v[0]), float(v[1]), 0.0]


def _entity(e, owner, layer_ref, doc):
    t = e.dxftype()
    row = {"entity": t, "handle": [0, 1, _h(e)], "ownerhandle": _ref(4, owner), "layer": layer_ref(e.dxf.layer)}
    ext = list(e.dxf.get("extrusion", (0.0, 0.0, 1.0)))
    if e.dxf.get("invisible", 0):
        row["invisible"] = 1
    if t == "LINE":
        row.update(type=19, start=_xy0(e.dxf.start), end=_xy0(e.dxf.end), extrusion=ext)
    elif t == "ARC":
        row.update(type=17, center=_xy0(e.dxf.center), radius=e.dxf.radius,
                   start_angle=math.radians(e.dxf.start_angle), end_angle=math.radians(e.dxf.end_angle), extrusion=ext)
    elif t == "CIRCLE":
        row.update(type=18, center=_xy0(e.dxf.center), radius=e.dxf.radius, extrusion=ext)
    elif t == "LWPOLYLINE":
        pts = list(e.get_points("xyb"))
        bul = [p[2] for p in pts]
        flag = (512 if e.closed else 0) | (16 if any(abs(b) > 0 for b in bul) else 0)
        row.update(type=77, points=[[p[0], p[1]] for p in pts], bulges=bul if flag & 16 else [], flag=flag)
        if tuple(ext) != (0.0, 0.0, 1.0):
            row["extrusion"] = ext
            row["flag"] = flag | 1
    elif t == "INSERT":
        rec = doc.blocks.get(e.dxf.name).block_record
        row.update(type=8 if e.mcount > 1 else 7, ins_pt=_xy0(e.dxf.insert),
                   scale=[e.dxf.xscale, e.dxf.yscale, e.dxf.zscale], rotation=math.radians(e.dxf.rotation),
                   block_header=_ref(5, _h(rec)), extrusion=ext)
        if e.mcount > 1:
            row.update(entity="MINSERT", num_cols=e.dxf.column_count, num_rows=e.dxf.row_count,
                       col_spacing=e.dxf.column_spacing, row_spacing=e.dxf.row_spacing)
    elif t == "ELLIPSE":
        row.update(type=35, center=_xy0(e.dxf.center), sm_axis=_xy0(e.dxf.major_axis),
                   axis_ratio=e.dxf.ratio, start_angle=e.dxf.start_param, end_angle=e.dxf.end_param, extrusion=ext)
    else:
        raise ValueError(f"pairing has no D1 shape for {t}")
    return row


def pair(scene):
    doc = build_dxf(scene)
    return doc, dxf_to_d1(doc)
