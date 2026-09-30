"""D1 route: LibreDWG `dwgread` JSON -> neutral SourceEntityObservations.

Only field paths VERIFIED in real Urban decodes are mapped into geometry
(ALRASHED_ARCHITECTURAL.json and P7757_ARCHITECTURAL.json, R8.1 field audit,
see FIELD_REGISTER). A kind whose representation has never been observed in
a real decode is NOT guessed: it becomes an UNSUPPORTED observation with a
SOURCE_MAPPING_UNVERIFIED finding (MINSERT today), so it is visible and
blocks FINAL instead of being silently realised or silently dropped.

Also implements the D1 representation for URBAN-SRD-1 (the frozen R8.0
record schema over this route's raw output).
"""

from __future__ import annotations

from collections import Counter
from dataclasses import replace

from .. import findings as F
from .. import observations as O
from ..digests import canonical_source_value, source_representation_digest_of_records
from ..findings import SourceFinding

ROUTE = "D1_LIBREDWG_JSON"

# ------------------------------------------------------------ field register
# status:
#   VERIFIED                   path present with this meaning in both real decodes
#   VERIFIED_BY_FLAG_PATTERN   value tied to its DWG flag bit in every real row (LibreDWG emits
#                              LWPOLYLINE const_width iff bit 4: 95/95 + 22/22; bulges is always a key
#                              but NON-EMPTY iff bit 16: 267/267 + 21/21; extrusion/elevation never
#                              appear and bits 1/8 are never set)
#   VERIFIED_PATH_VALUE_UNOBSERVED  path present everywhere, only zero/default values seen
#   SOURCE_MAPPING_UNVERIFIED  never seen in a real decode: not mapped into geometry
FIELD_REGISTER = {
    "LINE": {"type": (19, "VERIFIED"), "start": ("start", "VERIFIED"), "end": ("end", "VERIFIED"),
             "extrusion": ("extrusion", "VERIFIED")},
    "ARC": {"type": (17, "VERIFIED"), "center": ("center", "VERIFIED"), "radius": ("radius", "VERIFIED"),
            "start_angle": ("start_angle (radians)", "VERIFIED"), "end_angle": ("end_angle (radians)", "VERIFIED"),
            "extrusion": ("extrusion", "VERIFIED")},
    "CIRCLE": {"type": (18, "VERIFIED"), "center": ("center", "VERIFIED"), "radius": ("radius", "VERIFIED"),
               "extrusion": ("extrusion", "VERIFIED")},
    "LWPOLYLINE": {"type": (77, "VERIFIED"), "vertices": ("points", "VERIFIED"),
                   "bulges": ("bulges (non-empty iff flag & 16)", "VERIFIED"),
                   "closed": ("flag & 512", "VERIFIED"),
                   "extrusion": ("extrusion (present iff flag & 1; absent in every real LWPOLYLINE, bit never set)",
                                 "VERIFIED_BY_FLAG_PATTERN"),
                   "elevation": ("elevation (present iff flag & 8; bit never set)", "VERIFIED_BY_FLAG_PATTERN")},
    "INSERT": {"type": (7, "VERIFIED"), "insertion": ("ins_pt", "VERIFIED"), "scale": ("scale [x,y,z]", "VERIFIED"),
               "rotation": ("rotation (radians)", "VERIFIED"), "extrusion": ("extrusion", "VERIFIED"),
               "block": ("block_header -> BLOCK_HEADER handle", "VERIFIED"),
               "attributes": ("ATTRIB rows with ownerhandle -> this INSERT", "VERIFIED")},
    "ATTRIB": {"type": (2, "VERIFIED"), "tag": ("tag", "VERIFIED"), "value": ("text_value", "VERIFIED"),
               "insertion": ("ins_pt", "VERIFIED"), "extrusion": ("extrusion", "VERIFIED")},
    "ELLIPSE": {"type": (35, "VERIFIED"), "center": ("center", "VERIFIED"), "major_axis": ("sm_axis", "VERIFIED"),
                "ratio": ("axis_ratio", "VERIFIED"), "start_param": ("start_angle (radians)", "VERIFIED"),
                "end_param": ("end_angle (radians)", "VERIFIED"), "extrusion": ("extrusion", "VERIFIED")},
    "TEXT": {"type": (1, "VERIFIED"), "insertion": ("ins_pt", "VERIFIED"), "value": ("text_value", "VERIFIED")},
    "MTEXT": {"type": (44, "VERIFIED"), "insertion": ("ins_pt", "VERIFIED"), "value": ("text", "VERIFIED")},
    "BLOCK_HEADER": {"type": (49, "VERIFIED (object name is EMPTY on 409/442 P7757 rows: detect by type)"),
                     "name": ("name", "VERIFIED (EMPTY on 409/442 P7757 rows -> BLOCK_NAME_UNREADABLE)"),
                     "base_point": ("base_pt", "VERIFIED_PATH_VALUE_UNOBSERVED (all zero in both decodes)"),
                     "xref_attach": ("blkisxref", "VERIFIED_PATH_VALUE_UNOBSERVED"),
                     "xref_overlay": ("xrefoverlaid", "VERIFIED_PATH_VALUE_UNOBSERVED"),
                     "xref_path": ("xref_pname", "VERIFIED_PATH_VALUE_UNOBSERVED"),
                     "xref_resolved": ("is_xref_resolved", "SOURCE_MAPPING_UNVERIFIED (semantics of 1 unseen)"),
                     "xref_unloaded": ("loaded_bit", "SOURCE_MAPPING_UNVERIFIED (semantics unseen)"),
                     "NOT_AN_XREF_FLAG": ("is_xref_ref (1 on all 442 P7757 blocks)", "VERIFIED")},
    "common": {"owner": ("ownerhandle -> BLOCK_HEADER / INSERT", "VERIFIED"),
               "layer": ("layer -> LAYER handle", "VERIFIED"), "visible": ("not invisible", "VERIFIED")},
    "MINSERT": {"type": (8, "SOURCE_MAPPING_UNVERIFIED"),
                "grid": ("num_cols/num_rows/col_spacing/row_spacing", "SOURCE_MAPPING_UNVERIFIED (no MINSERT in any real decode)")},
    "OLE2FRAME": {"type": ("entity name OLE2FRAME carries type 2 in the Al Rashed decode", "VERIFIED -> SKIPPED")},
    "ACAD_PROXY_ENTITY": {"type": (498, "SOURCE_MAPPING_UNVERIFIED (none in any real decode) -> PROXY")},
}

KIND_BY_TYPE = {19: O.LINE, 17: O.ARC, 18: O.CIRCLE, 77: O.LWPOLYLINE, 7: O.INSERT, 35: O.ELLIPSE,
                1: O.TEXT, 44: O.MTEXT, 78: O.HATCH, 20: O.DIMENSION, 21: O.DIMENSION, 22: O.DIMENSION,
                23: O.DIMENSION, 24: O.DIMENSION, 25: O.DIMENSION, 26: O.DIMENSION}
NAME_OK = {O.LINE: ("LINE",), O.ARC: ("ARC",), O.CIRCLE: ("CIRCLE",), O.LWPOLYLINE: ("LWPOLYLINE",),
           O.INSERT: ("INSERT",), O.ELLIPSE: ("ELLIPSE",), O.TEXT: ("TEXT",), O.MTEXT: ("MTEXT",),
           O.HATCH: ("HATCH",), O.DIMENSION: ("DIMENSION",)}
DELIMITER_TYPES = {4: "BLOCK", 5: "ENDBLK", 6: "SEQEND"}
T_ATTRIB, T_MINSERT, T_PROXY = 2, 8, 498


def _abs(h):
    return h[-1] if isinstance(h, list) and h else None


def block_key(ref) -> str | None:
    h = _abs(ref)
    return None if h is None else f"H{h}"


def _xy(v):
    return (float(v[0]), float(v[1]))


# ------------------------------------------------------------ URBAN-SRD-1 (D1)

# The frozen URBAN-SRD-1 record schema (R8.0, tests/r8_0/digest_contract.py).
# This is a HASH SCHEMA over the route's raw output, not a geometry mapping:
# a listed key is hashed if present and ignored if absent, so an unverified
# name here can never produce geometry.
SRD_FIELDS = ("start", "end", "center", "radius", "start_angle", "end_angle", "points",
              "bulges", "flag", "elevation", "ins_pt", "scale", "rotation", "extrusion",
              "base_pt", "num_cols", "num_rows", "col_spacing", "row_spacing",
              "blkisxref", "xrefoverlaid", "xref_pname", "is_xref_resolved", "loaded_bit",
              "text", "text_value", "tag", "height", "text_height", "xline1_pt", "xline2_pt",
              "def_pt", "act_measurement", "user_text", "dim_rotation", "sm_axis", "axis_ratio")


def _is_block_header(o):
    return o.get("object") == "BLOCK_HEADER" or o.get("type") == 49


def _is_layer(o):
    return o.get("object") == "LAYER" or o.get("type") == 51


def representation_records(decode) -> list:
    objs = decode.get("OBJECTS", [])
    layers = {_abs(o.get("handle")): o.get("name") for o in objs if _is_layer(o)}
    blocks = {_abs(o.get("handle")): o.get("name") for o in objs if _is_block_header(o)}
    recs = []
    for o in objs:
        if _is_block_header(o):
            rec = {"k": "BLOCK_HEADER", "name": o.get("name")}
        elif "entity" in o:
            rec = {"k": "ENTITY", "type": o.get("type"), "entity": o.get("entity"),
                   "handle": _abs(o.get("handle")), "owner": blocks.get(_abs(o.get("ownerhandle"))),
                   "layer": layers.get(_abs(o.get("layer")))}
            if "block_header" in o:
                rec["block"] = blocks.get(_abs(o.get("block_header")))
        else:
            continue
        for f in SRD_FIELDS:
            if f in o:
                rec[f] = canonical_source_value(o[f])
        recs.append(rec)
    hdr = decode.get("HEADER", {})
    recs.append({"k": "HEADER", "INSUNITS": hdr.get("INSUNITS"),
                 "DIMLFAC": canonical_source_value(float(hdr.get("DIMLFAC", 1.0)))})
    return recs


def source_representation_digest(decode, route_id: str = ROUTE) -> str:
    return source_representation_digest_of_records(representation_records(decode), route_id)


# ------------------------------------------------------------ observations

def _unsupported(o, obs_id, handle, stype, category, reason, layer, visible):
    return O.SourceEntityObservation(obs_id=obs_id, source_handle=handle, source_type=stype,
                                     kind=O.UNSUPPORTED_KIND, geometry=O.UnsupportedGeom(category, reason),
                                     layer=layer, extrusion=o.get("extrusion", O.DEFAULT_EXTRUSION), visible=visible)


def _entity(o, layers, attribs_by_insert):
    t = o.get("type")
    name = o.get("entity") or ""
    h = _abs(o.get("handle"))
    obs_id, handle = f"D1:{h}", str(h)
    stype = f"LIBREDWG:{t}:{name}"
    layer = layers.get(_abs(o.get("layer")))
    visible = not bool(o.get("invisible"))
    un = lambda cat, why: _unsupported(o, obs_id, handle, stype, cat, why, layer, visible)
    if name == "OLE2FRAME":
        extra = "" if t == 74 else f"; the decode also labels it type {t} (a type-code conflict)"
        return un(F.SKIPPED, "OLE2FRAME is an embedded OLE object, not vector geometry" + extra)
    if name in ("ACAD_PROXY_ENTITY", "PROXY_ENTITY") or t == T_PROXY:
        return un(F.PROXY, "proxy entity: only proxy graphics exist; representation unverified in real decodes")
    if t == T_MINSERT or name == "MINSERT":
        return un(F.SOURCE_MAPPING_UNVERIFIED,
                  "MINSERT grid fields have never been seen in a real decode; not realised, never as one instance")
    if isinstance(t, int) and t >= 500:
        return un(F.CUSTOM_CLASS, f"class-based entity {name or '(unnamed)'} (type {t}) is not realised by K1")
    kind = KIND_BY_TYPE.get(t)
    if kind is None:
        return un(F.UNHANDLED, f"type {t} {name!r} has no verified D1 mapping")
    if name and not any(name.startswith(p) for p in NAME_OK[kind]):
        return un(F.SOURCE_TYPE_CONFLICT, f"entity name {name!r} does not match type code {t} ({kind})")
    ext = o.get("extrusion", O.DEFAULT_EXTRUSION)
    prov = []
    try:
        if kind == O.LINE:
            geom = O.LineGeom(_xy(o["start"]), _xy(o["end"]))
        elif kind == O.ARC:
            geom = O.ArcGeom(_xy(o["center"]), float(o["radius"]), float(o["start_angle"]), float(o["end_angle"]))
        elif kind == O.CIRCLE:
            geom = O.CircleGeom(_xy(o["center"]), float(o["radius"]))
        elif kind == O.LWPOLYLINE:
            flag = int(o.get("flag", 0) or 0)
            if "extrusion" in o:
                ext = o["extrusion"]
            elif flag & 1:
                ext = "FLAG_BIT_1_SET_BUT_EXTRUSION_ABSENT"          # -> FRAME_UNREADABLE in K1
            else:
                ext = O.DEFAULT_EXTRUSION
                prov.append(("extrusion", "DEFAULT_BY_FLAG_PATTERN"))
            pts = tuple(_xy(p) for p in (o.get("points") or []))
            bul = tuple(float(b) for b in (o.get("bulges") or []))
            geom = O.PolylineGeom(pts, bul, bool(flag & 512))
        elif kind == O.INSERT:
            sc = o.get("scale") or [1.0, 1.0, 1.0]
            geom = O.InsertGeom(block_key(o["block_header"]), _xy(o["ins_pt"]), (float(sc[0]), float(sc[1])),
                                float(o.get("rotation", 0.0) or 0.0), None,
                                tuple(attribs_by_insert.get(h, ())))
        elif kind == O.ELLIPSE:
            geom = O.EllipseGeom(_xy(o["center"]), _xy(o["sm_axis"]), float(o["axis_ratio"]),
                                 float(o["start_angle"]), float(o["end_angle"]))
        else:   # carried kinds
            val = o.get("text_value", o.get("text", "")) or ""
            ins = o.get("ins_pt")
            geom = O.TextGeom(_xy(ins) if ins else None, str(val))
    except (KeyError, TypeError, ValueError, IndexError) as err:
        return un(F.UNSUPPORTED, f"required field unreadable: {err!r}")
    return O.SourceEntityObservation(obs_id=obs_id, source_handle=handle, source_type=stype, kind=kind,
                                     geometry=geom, layer=layer, extrusion=ext, visible=visible,
                                     provenance=tuple(prov))


def to_document(decode, source_sha256: str | None = None, decoder_version: str | None = None) -> O.SourceDocument:
    objs = decode.get("OBJECTS", [])
    layers = {_abs(o.get("handle")): o.get("name") for o in objs if _is_layer(o)}
    headers = {_abs(o.get("handle")): o for o in objs if _is_block_header(o)}
    inserts = {_abs(o.get("handle")) for o in objs if "entity" in o and o.get("type") in (7, 8)}
    attribs = {}
    for o in objs:
        if "entity" in o and o.get("type") == T_ATTRIB and (o.get("entity") or "ATTRIB") == "ATTRIB":
            owner = _abs(o.get("ownerhandle"))
            if owner in inserts:
                attribs.setdefault(owner, []).append(O.AttributeGeom(
                    str(_abs(o.get("handle"))), str(o.get("tag", "")), str(o.get("text_value", "")),
                    _xy(o.get("ins_pt") or (0.0, 0.0)), o.get("extrusion", O.DEFAULT_EXTRUSION)))
    model, per_block = [], {}
    notes = Counter()
    unresolved_owner = 0
    for o in objs:
        if "entity" not in o:
            continue
        t = o.get("type")
        if t in DELIMITER_TYPES:
            notes[f"delimiter_{DELIMITER_TYPES[t]}"] += 1
            continue
        owner = _abs(o.get("ownerhandle"))
        if t == T_ATTRIB and (o.get("entity") or "ATTRIB") == "ATTRIB" and owner in inserts:
            continue                                            # carried on its INSERT
        obs = _entity(o, layers, attribs)
        hdr = headers.get(owner)
        if hdr is None:
            if owner is not None and owner in inserts:
                notes["entities_owned_by_insert_other_than_attrib"] += 1
            unresolved_owner += owner is None or owner not in headers
            model.append(obs)
            continue
        hname = str(hdr.get("name") or "")
        if hname.upper() == "*MODEL_SPACE":
            model.append(obs)
        elif hname.upper().startswith("*PAPER_SPACE"):
            notes[f"other_layout_entities:{hname}"] += 1
        else:
            per_block.setdefault(owner, []).append(obs)
    blocks = {}
    for h, hdr in headers.items():
        name = str(hdr.get("name") or "")
        if name.upper() == "*MODEL_SPACE" or name.upper().startswith("*PAPER_SPACE"):
            continue
        bp = hdr.get("base_pt")
        xref = None
        if hdr.get("blkisxref") or hdr.get("xrefoverlaid") or hdr.get("xref_pname"):
            xref = O.XrefInfo(path=str(hdr.get("xref_pname") or ""),
                              attachment="OVERLAY" if hdr.get("xrefoverlaid") else ("ATTACH" if hdr.get("blkisxref") else "UNKNOWN"),
                              resolved=None, unloaded=None, mapping_status=F.SOURCE_MAPPING_UNVERIFIED)
        blocks[f"H{h}"] = O.BlockDefinition(key=f"H{h}", name=name, base_point=_xy(bp) if bp else (0.0, 0.0),
                                            entities=tuple(per_block.get(h, ())), xref=xref, name_readable=bool(name))
    doc_findings = []
    if unresolved_owner:
        doc_findings.append(SourceFinding(F.OWNER_UNRESOLVED, None, (),
                                          f"{unresolved_owner} entities have no owner block header; placed in model space"))
    missing_bp = [f"H{h}" for h, hdr in headers.items() if "base_pt" not in hdr]
    if missing_bp:
        doc_findings.append(SourceFinding(F.SOURCE_MAPPING_UNVERIFIED, None, (),
                                          f"{len(missing_bp)} block headers without base_pt; read as (0,0)"))
    anchor = O.SourceRevisionAnchor(source_sha256, ROUTE, "libredwg dwgread JSON", decoder_version)
    return O.SourceDocument(anchor=anchor, entities=tuple(model), blocks=blocks,
                            header=dict(decode.get("HEADER", {})), findings=tuple(doc_findings), notes=dict(notes))
