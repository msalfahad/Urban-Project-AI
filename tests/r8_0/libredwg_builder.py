"""Build LibreDWG-JSON-shaped decodes from a scene description.

This is INPUT construction only. It makes no geometric decision: every number
it writes is copied from the scene as authored, in the entity's own frame
(OCS for ARC/CIRCLE/LWPOLYLINE/INSERT), exactly as a DWG stores it.

Field names follow the LibreDWG ``dwgread -O JSON`` shape already consumed by
``engine/cad_adapter.py`` and seen in the frozen P7757 decode:

* entities carry ``entity``, a numeric ``type``, ``handle`` [0,1,h],
  ``ownerhandle`` [4,1,h,h], ``layer`` [5,1,h,h] and ``extrusion``;
* BLOCK_HEADER objects carry ``base_pt``, ``blkisxref``, ``xrefoverlaid``,
  ``xref_pname``, ``is_xref_resolved`` and ``loaded_bit``.

Fields not yet seen in a real decode of this project are marked
``TO_REVERIFY`` in ``R8_0_FIXTURE_REGISTER.json``: MINSERT ``num_cols`` /
``num_rows`` / ``col_spacing`` / ``row_spacing`` (LibreDWG dwg.spec names),
OLE2FRAME (type 74) and ACAD_PROXY_ENTITY (type 498). They must be re-checked
against a real ``dwgread`` decode before R8.1 relies on them.
"""

from __future__ import annotations

import math

MODEL_SPACE_HANDLE = 2

TYPE = {"TEXT": 1, "ATTRIB": 2, "INSERT": 7, "MINSERT": 8, "ARC": 17,
        "CIRCLE": 18, "LINE": 19, "DIMENSION_LINEAR": 21, "MTEXT": 44,
        "OLE2FRAME": 74, "LWPOLYLINE": 77, "HATCH": 78,
        "ACAD_PROXY_ENTITY": 498}


def _ref(code, h):
    return [code, 1, h, h]


class Decode:
    """A LibreDWG-shaped decode assembled from a scene."""

    def __init__(self, insunits=4, dimlfac=1.0):
        self.insunits = insunits
        self.dimlfac = dimlfac
        self.objects = [{"object": "BLOCK_HEADER", "type": 49,
                         "handle": [0, 1, MODEL_SPACE_HANDLE],
                         "name": "*MODEL_SPACE", "base_pt": [0.0, 0.0, 0.0],
                         "blkisxref": 0, "xrefoverlaid": 0, "entities": []}]
        self.layers = {}
        self.blocks = {"*MODEL_SPACE": MODEL_SPACE_HANDLE}
        self._next = 100

    def _h(self):
        self._next += 1
        return self._next

    def layer(self, name):
        if name not in self.layers:
            h = self._h()
            self.layers[name] = h
            self.objects.append({"object": "LAYER", "type": 51,
                                 "handle": [0, 1, h], "name": name})
        return _ref(5, self.layers[name])

    def block(self, name, base=(0.0, 0.0), xref=None):
        h = self._h()
        self.blocks[name] = h
        row = {"object": "BLOCK_HEADER", "type": 49, "handle": [0, 1, h],
               "name": name, "base_pt": [float(base[0]), float(base[1]), 0.0],
               "blkisxref": 0, "xrefoverlaid": 0, "xref_pname": "",
               "is_xref_resolved": 0, "loaded_bit": 0, "entities": []}
        if xref:
            row.update({"blkisxref": 1,
                        "xrefoverlaid": 1 if xref.get("overlay") else 0,
                        "xref_pname": xref.get("path", ""),
                        "is_xref_resolved": 1 if xref.get("resolved") else 0,
                        "loaded_bit": 1 if xref.get("unloaded") else 0})
        self.objects.append(row)
        return h

    def add(self, kind, owner="*MODEL_SPACE", layer="0", extrusion=(0.0, 0.0, 1.0),
            **fields):
        h = self._h()
        row = {"entity": kind, "type": TYPE[kind], "handle": [0, 1, h],
               "ownerhandle": _ref(4, self.blocks[owner]),
               "layer": self.layer(layer)}
        if extrusion == "NULL":           # the decoder emitted the field but no value
            row["extrusion"] = None
        elif extrusion is not None:
            row["extrusion"] = list(extrusion) if isinstance(extrusion, (list, tuple)) else extrusion
        row.update(fields)
        self.objects.append(row)
        return h

    def build(self):
        hdr = {"INSUNITS": self.insunits, "LUNITS": 2, "TILEMODE": 1}
        if self.dimlfac != 1.0:
            hdr["DIMLFAC"] = self.dimlfac
        return {"FILEHEADER": {"version": "AC1018"}, "HEADER": hdr,
                "OBJECTS": list(self.objects)}


def build(scene) -> dict:
    """Scene description -> LibreDWG-shaped decode (native values only)."""
    d = Decode(insunits=scene.get("insunits", 4), dimlfac=scene.get("dimlfac", 1.0))
    # blocks first so INSERTs can reference them; definition order is the
    # scene's, which deliberately differs from use order in nested cases
    for name, blk in scene.get("blocks", {}).items():
        d.block(name, blk.get("base", (0.0, 0.0)), blk.get("xref"))
    for name, blk in scene.get("blocks", {}).items():
        for e in blk.get("entities", []):
            _emit(d, e, owner=name)
    for e in scene.get("entities", []):
        _emit(d, e, owner="*MODEL_SPACE")
    return d.build()


def _emit(d, e, owner):
    k = e["kind"]
    ext = e.get("extrusion", (0.0, 0.0, 1.0))
    lay = e.get("layer", "0")
    if k == "LINE":
        return d.add("LINE", owner, lay, ext,
                     start=[*map(float, e["a"]), 0.0], end=[*map(float, e["b"]), 0.0])
    if k == "ARC":
        return d.add("ARC", owner, lay, ext, center=[*map(float, e["c"]), 0.0],
                     radius=float(e["r"]), start_angle=math.radians(e["a0"]),
                     end_angle=math.radians(e["a1"]))
    if k == "CIRCLE":
        return d.add("CIRCLE", owner, lay, ext, center=[*map(float, e["c"]), 0.0],
                     radius=float(e["r"]))
    if k == "LWPOLYLINE":
        return d.add("LWPOLYLINE", owner, lay, ext,
                     points=[list(map(float, p)) for p in e["pts"]],
                     bulges=[float(b) for b in e.get("bulges", [])],
                     flag=0x200 if e.get("closed") else 0,
                     elevation=float(e.get("elevation", 0.0)))
    if k in ("INSERT", "MINSERT"):
        sx, sy = e.get("scale", (1.0, 1.0))
        fields = dict(ins_pt=[*map(float, e["at"]), 0.0], scale=[float(sx), float(sy), 1.0],
                      rotation=math.radians(e.get("rot", 0.0)),
                      block_header=_ref(5, d.blocks[e["block"]]))
        if k == "MINSERT":
            fields.update(num_cols=int(e["cols"]), num_rows=int(e["rows"]),
                          col_spacing=float(e["col_sp"]), row_spacing=float(e["row_sp"]))
        return d.add(k, owner, lay, ext, **fields)
    if k == "DIMENSION_LINEAR":        # rotated linear dimension; dim_rotation is TO_REVERIFY
        return d.add("DIMENSION_LINEAR", owner, lay, ext,
                     xline1_pt=[*map(float, e["x1"]), 0.0], xline2_pt=[*map(float, e["x2"]), 0.0],
                     def_pt=[*map(float, e.get("def", e["x2"])), 0.0],
                     dim_rotation=math.radians(e.get("rot", 0.0)),
                     act_measurement=float(e["act"]), user_text=e.get("user_text", ""))
    if k == "MTEXT":
        return d.add("MTEXT", owner, lay, ext, ins_pt=[*map(float, e["at"]), 0.0],
                     text_height=float(e.get("h", 250.0)), text=e["text"])
    if k == "TEXT":
        return d.add("TEXT", owner, lay, ext, ins_pt=[*map(float, e["at"]), 0.0],
                     height=float(e.get("h", 250.0)), text_value=e["text"])
    if k == "ELLIPSE":                 # type 35, WCS-native; fields TO_REVERIFY
        h = d._h()
        d.objects.append({"entity": "ELLIPSE", "type": 35, "handle": [0, 1, h],
                          "ownerhandle": _ref(4, d.blocks[owner]), "layer": d.layer(lay),
                          "center": [*map(float, e["c"]), 0.0], "sm_axis": [*map(float, e["major"]), 0.0],
                          "axis_ratio": float(e["ratio"]), "start_angle": float(e.get("t0", 0.0)),
                          "end_angle": float(e.get("t1", 2 * math.pi)),
                          "extrusion": list(e.get("extrusion", (0.0, 0.0, 1.0)))})
        return h
    if k == "INSERT_WITH_ATTRIB":      # an ATTRIB is owned by its INSERT, not by the block
        ins = _emit(d, dict(e, kind="INSERT"), owner)
        h = d._h()
        d.objects.append({"entity": "ATTRIB", "type": 2, "handle": [0, 1, h],
                          "ownerhandle": _ref(4, ins), "layer": d.layer(lay),
                          "ins_pt": [*map(float, e["attrib_at"]), 0.0], "height": 200.0,
                          "tag": e["tag"], "text_value": e["value"]})
        return ins
    if k in ("OLE2FRAME", "ACAD_PROXY_ENTITY"):
        return d.add(k, owner, lay, ext)
    if k == "CUSTOM":
        h = d._h()
        d.objects.append({"entity": e.get("name", "CUSTOM_CLASS"), "type": int(e["type_code"]),
                          "handle": [0, 1, h], "ownerhandle": _ref(4, d.blocks[owner]),
                          "layer": d.layer(lay)})
        return h
    raise ValueError(f"scene kind {k!r} has no LibreDWG shape in this builder")
