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
from .. import capability as CAP
from .. import decoder_pins as PINS

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
    "common": {"owner": ("ownerhandle -> BLOCK_HEADER / INSERT", "VERIFIED where it resolves (15055/15055 real rows "
                         "agree with the header's owned-entity list)"),
               "entmode": ("entmode: 0 owned by ownerhandle, 1 paper space, 2 model space",
                           "VERIFIED (every model-space row in the three real decodes: no ownerhandle, entmode 2, "
                           "listed by *MODEL_SPACE)"),
               "owner_list": ("BLOCK_HEADER.entities (owned-entity list)",
                              "VERIFIED_BY_CROSS_CHECK; *D headers' lists overlap *U lists in LibreDWG 0.13.3 "
                              "-> a doubly-listed entity is AMBIGUOUS, never guessed"),
               "layer": ("layer -> LAYER handle", "VERIFIED"), "visible": ("not invisible", "VERIFIED")},
    "POINT": {"type": (27, "VERIFIED"), "position": ("x, y", "VERIFIED")},
    "SOLID": {"type": (31, "VERIFIED"), "corners": ("corner1..corner4", "VERIFIED")},
    "ATTDEF": {"type": (3, "VERIFIED"), "insertion": ("ins_pt", "VERIFIED"), "tag": ("tag", "VERIFIED")},
    "MINSERT": {"type": (8, "SOURCE_MAPPING_UNVERIFIED"),
                "grid": ("num_cols/num_rows/col_spacing/row_spacing", "SOURCE_MAPPING_UNVERIFIED (no MINSERT in any real decode)")},
    "OLE2FRAME": {"type": ("entity name OLE2FRAME carries type 2 in the Al Rashed decode", "VERIFIED -> SKIPPED")},
    "ACAD_PROXY_ENTITY": {"type": (498, "SOURCE_MAPPING_UNVERIFIED (none in any real decode) -> PROXY")},
}

KIND_BY_TYPE = {19: O.LINE, 17: O.ARC, 18: O.CIRCLE, 77: O.LWPOLYLINE, 7: O.INSERT, 35: O.ELLIPSE,
                27: O.POINT, 31: O.SOLID, 3: O.ATTDEF, 1: O.TEXT, 44: O.MTEXT, 78: O.HATCH, 20: O.DIMENSION, 21: O.DIMENSION, 22: O.DIMENSION,
                23: O.DIMENSION, 24: O.DIMENSION, 25: O.DIMENSION, 26: O.DIMENSION}
NAME_OK = {O.LINE: ("LINE",), O.ARC: ("ARC",), O.CIRCLE: ("CIRCLE",), O.LWPOLYLINE: ("LWPOLYLINE",),
           O.INSERT: ("INSERT",), O.ELLIPSE: ("ELLIPSE",), O.TEXT: ("TEXT",), O.MTEXT: ("MTEXT",),
           O.HATCH: ("HATCH",), O.DIMENSION: ("DIMENSION",), O.POINT: ("POINT",), O.SOLID: ("SOLID",),
           O.ATTDEF: ("ATTDEF",)}
# class-based entities are identified by NAME (type codes >= 500 are per-file class indices)
NAMED_CLASS_KIND = {"WIPEOUT": "WIPEOUT", "IMAGE": "IMAGE"}
DELIMITER_TYPES = {4: "BLOCK", 5: "ENDBLK", 6: "SEQEND"}
T_ATTRIB, T_MINSERT, T_PROXY = 2, 8, 498


def _abs(h):
    """Raw handle VALUE as the route printed it (used by the frozen SRD record schema only)."""
    return h[-1] if isinstance(h, list) and h else None


# ------------------------------------------------------------ handle identity (R8.2)
# LibreDWG JSON output prints a 3-byte handle with only its low 16 bits
# ([0, 3, 10388] is some handle 0x??2894). R8.3: first observed in the historical
# decodes (pin NOT_ESTABLISHED); a pinned re-decode with the REGISTERED dwgread 0.13.3
# build reproduced it byte for byte, so it is attributed to that build
# (decoder_pins.KNOWN_REPRESENTATION_DEFECTS); whether the parser, the internal representation or the JSON writer
# drops the high byte is not localised
# (PINNED_LIBREDWG_DWGREAD_JSON_HANDLE_REPRESENTATION_DEFECT). Two different objects can then share a
# value; (byte size, value) stays unique in every real decode. Absolute references
# (codes 2-5) carry the target's byte size, so they resolve exactly; relative
# references (codes 6/8/10/12) carry an OFFSET size, and their computed absolute
# value is trustworthy only when that value is unique in the decode.
RELATIVE_CODES = frozenset({6, 8, 10, 12})


def handle_id(h) -> str | None:
    """Identity of an object's OWN handle: 'v' for 1-2 byte handles, 'v+3B' when truncated."""
    if not isinstance(h, list) or not h:
        return None
    if len(h) < 3:
        return str(h[-1])
    size, v = h[1], h[-1]
    return str(v) if size < 3 else f"{v}+{size}B"


def ref_id(ref, unique_by_value=None) -> str | None:
    """Identity of the object a REFERENCE points to, or None when the route does not establish it."""
    if not isinstance(ref, list) or not ref:
        return None
    if len(ref) < 3:
        return str(ref[-1])
    code, size, v = ref[0], ref[1], ref[-1]
    if code in RELATIVE_CODES:
        if unique_by_value is None:
            return str(v)
        return unique_by_value.get(v)
    return str(v) if size < 3 else f"{v}+{size}B"


def block_key(ref) -> str | None:
    h = ref_id(ref)
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

def _unsupported(o, obs_id, handle, stype, category, reason, layer, visible, impacts=None):
    return O.SourceEntityObservation(obs_id=obs_id, source_handle=handle, source_type=stype,
                                     kind=O.UNSUPPORTED_KIND, geometry=O.UnsupportedGeom(category, reason, impacts),
                                     layer=layer, extrusion=o.get("extrusion", O.DEFAULT_EXTRUSION), visible=visible)


def _entity(o, layers, attribs_by_insert):
    t = o.get("type")
    name = o.get("entity") or ""
    h = handle_id(o.get("handle"))
    obs_id, handle = f"D1:{h}", str(h)
    stype = f"LIBREDWG:{t}:{name}"
    layer = layers.get(ref_id(o.get("layer")))
    visible = not bool(o.get("invisible"))
    un = lambda cat, why, imp=None: _unsupported(o, obs_id, handle, stype, cat, why, layer, visible, imp)
    if name == "OLE2FRAME":
        extra = "" if t == 74 else f"; the decode also labels it type {t} (a type-code conflict)"
        return un(F.SKIPPED, "OLE2FRAME is an embedded OLE object, not vector geometry" + extra)
    if name in ("ACAD_PROXY_ENTITY", "PROXY_ENTITY") or t == T_PROXY:
        return un(F.PROXY, "proxy entity: only proxy graphics exist; representation unverified in real decodes")
    if t == T_MINSERT or name == "MINSERT":
        return un(F.SOURCE_MAPPING_UNVERIFIED,
                  "MINSERT grid fields have never been seen in a real decode; not realised, never as one instance")
    if isinstance(t, int) and t >= 500:
        cls = NAMED_CLASS_KIND.get(name) or NAMED_CLASS_KIND.get(o.get("dxfname") or "")
        if cls:
            return un(F.CUSTOM_CLASS, f"class-based {cls} (type {t} in this file) is not vector geometry",
                      CAP.impacts_for_kind(cls))
        return un(F.CUSTOM_CLASS, f"class-based entity {name or '(unnamed)'}"
                                  f"{' / ' + o['dxfname'] if o.get('dxfname') else ''} (type {t}) is not realised by K1")
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
        elif kind == O.POINT:
            geom = O.CarriedGeom((float(o["x"]), float(o["y"])))
        elif kind == O.SOLID:
            cs = tuple(_xy(o[f"corner{i}"]) for i in (1, 2, 3, 4))
            geom = O.CarriedGeom(cs[0], cs)
        elif kind == O.ATTDEF:
            geom = O.CarriedGeom(_xy(o["ins_pt"]), (), str(o.get("tag", "")))
        else:   # TEXT / MTEXT / DIMENSION / HATCH
            val = o.get("text_value", o.get("text", "")) or ""
            ins = o.get("ins_pt")
            geom = O.TextGeom(_xy(ins) if ins else None, str(val))
    except (KeyError, TypeError, ValueError, IndexError) as err:
        return un(F.UNSUPPORTED, f"required field unreadable: {err!r}")
    return O.SourceEntityObservation(obs_id=obs_id, source_handle=handle, source_type=stype, kind=kind,
                                     geometry=geom, layer=layer, extrusion=ext, visible=visible,
                                     provenance=tuple(prov))


# ------------------------------------------------------------ ownership (R8.2 Phase 0)
MODEL, PAPER, BLOCK, ATTACHED, UNPLACED = "MODEL", "PAPER", "BLOCK", "ATTACHED", "UNPLACED"


def _space(hdr):
    n = str(hdr.get("name") or "").upper()
    return MODEL if n == "*MODEL_SPACE" else PAPER if n.startswith("*PAPER_SPACE") else BLOCK


def resolve_owner(o, headers, owned_by, inserts, unique=None, attrib_owner=None):
    """(placement, owner_header_handle, evidence, reason).

    Ownership sources, all VERIFIED on the real decodes:
      1. ownerhandle -> a BLOCK_HEADER
      2. entmode (2 model space, 1 paper space; 0 means "owned by ownerhandle")
      3. the owned-entity lists of the BLOCK_HEADERs
    An established placement needs the sources that speak to agree. Anything
    else is UNPLACED with the reason; nothing is guessed into model space."""
    raw = o.get("ownerhandle")
    own = handle_id(o.get("handle"))
    oh = ref_id(raw, unique)
    if raw is not None and oh is None:
        oh = "AMBIGUOUS_REFERENCE"
    if attrib_owner and own in attrib_owner:          # the INSERT's own absolute ATTRIB list wins
        oh = attrib_owner[own]
    em = o.get("entmode")
    listed = owned_by.get(own, ())
    ev = (("ownerhandle", oh), ("entmode", em), ("listed_by", tuple(sorted(listed))))
    list_spaces = {_space(headers[x]) for x in listed}
    if oh in headers:
        sp = _space(headers[oh])
        em_ok = em is None or (em == 0) or (em == 2 and sp == MODEL) or (em == 1 and sp == PAPER)
        list_ok = not listed or oh in listed
        if em_ok and list_ok:
            extra = [x for x in listed if x != oh]
            return sp, oh, ev, ("OWNER_ESTABLISHED_WITH_EXTRA_LISTING" if extra else None)
        return UNPLACED, None, ev, "OWNER_EVIDENCE_CONFLICT"
    if oh is not None and oh in inserts:
        return ATTACHED, oh, ev, None
    if em in (1, 2):
        sp = MODEL if em == 2 else PAPER
        if oh is not None:
            return UNPLACED, None, ev, ("OWNER_REFERENCE_AMBIGUOUS" if oh == "AMBIGUOUS_REFERENCE" else "OWNER_HANDLE_UNKNOWN")
        if listed and list_spaces != {sp}:
            return UNPLACED, None, ev, "OWNER_EVIDENCE_CONFLICT"
        hdr = next((x for x in listed), None) or next((h for h, v in headers.items() if _space(v) == sp), None)
        return sp, hdr, ev, None
    if len(listed) == 1:
        (only,) = listed
        return _space(headers[only]), only, ev, ("OWNER_BY_HEADER_LIST" if oh is not None else None)
    if len(listed) > 1:
        return UNPLACED, None, ev, "OWNER_AMBIGUOUS"
    if oh == "AMBIGUOUS_REFERENCE":
        return UNPLACED, None, ev, "OWNER_REFERENCE_AMBIGUOUS"
    return UNPLACED, None, ev, ("OWNER_HANDLE_UNKNOWN" if oh is not None else "NO_OWNER_EVIDENCE")


def to_document(decode, source_sha256: str | None = None, decoder_version: str | None = None,
                decoder_binary_sha256: str | None = None, conversion_chain: tuple = ()) -> O.SourceDocument:
    objs = decode.get("OBJECTS", [])
    layers = {handle_id(o.get("handle")): o.get("name") for o in objs if _is_layer(o)}
    headers = {handle_id(o.get("handle")): o for o in objs if _is_block_header(o)}
    by_handle, value_count = {}, Counter()
    for o in objs:
        hid = handle_id(o.get("handle"))
        if hid is not None:
            by_handle.setdefault(hid, o)
            value_count[_abs(o.get("handle"))] += 1
    unique = {_abs(o.get("handle")): handle_id(o.get("handle")) for o in objs
              if o.get("handle") is not None and value_count[_abs(o.get("handle"))] == 1}
    truncated = sum(1 for o in objs if isinstance(o.get("handle"), list) and len(o["handle"]) >= 3 and o["handle"][1] >= 3)
    collisions = sum(1 for v in value_count.values() if v > 1)
    inserts = {handle_id(o.get("handle")) for o in objs if "entity" in o and o.get("type") in (7, 8)}
    owned_by = {}
    for hh, hdr in headers.items():
        for r in hdr.get("entities") or []:
            owned_by.setdefault(ref_id(r), []).append(hh)
    attrib_owner = {}
    for o in objs:
        if "entity" in o and o.get("type") in (7, 8):
            for r in o.get("attribs") or []:
                attrib_owner[ref_id(r)] = handle_id(o.get("handle"))
    attribs = {}
    for o in objs:
        if "entity" in o and o.get("type") == T_ATTRIB and (o.get("entity") or "ATTRIB") == "ATTRIB":
            owner = attrib_owner.get(handle_id(o.get("handle"))) or ref_id(o.get("ownerhandle"), unique)
            if owner in inserts:
                attribs.setdefault(owner, []).append(O.AttributeGeom(
                    str(handle_id(o.get("handle"))), str(o.get("tag", "")), str(o.get("text_value", "")),
                    _xy(o.get("ins_pt") or (0.0, 0.0)), o.get("extrusion", O.DEFAULT_EXTRUSION)))
    model, per_block, unplaced, other = [], {}, [], []
    notes = Counter()
    notes["raw_entity_rows"] = sum(1 for o in objs if "entity" in o)
    doc_findings = []
    for o in objs:
        if "entity" not in o:
            continue
        t = o.get("type")
        if t in DELIMITER_TYPES:
            notes[f"delimiter_{DELIMITER_TYPES[t]}"] += 1
            continue
        own = handle_id(o.get("handle"))
        owner = attrib_owner.get(own) or ref_id(o.get("ownerhandle"), unique)
        if t == T_ATTRIB and (o.get("entity") or "ATTRIB") == "ATTRIB" and owner in inserts:
            continue                                            # carried on its INSERT
        obs = _entity(o, layers, attribs)
        placement, hdr_h, ev, reason = resolve_owner(o, headers, owned_by, inserts, unique, attrib_owner)
        if placement == ATTACHED:                               # owned by an INSERT but not an ATTRIB
            placement, reason = UNPLACED, "OWNER_IS_INSERT"
        if placement == UNPLACED:
            unplaced.append(O.UnplacedObservation(obs, o.get("ownerhandle"), reason, ev))
            doc_findings.append(SourceFinding(
                F.OWNER_UNRESOLVED, obs.obs_id, (),
                f"{reason}: {obs.source_type} handle {obs.source_handle} layer {obs.layer!r} raw owner "
                f"{o.get('ownerhandle')!r} entmode {o.get('entmode')!r} listed_by {dict(ev)['listed_by']}; "
                "kept UNPLACED, not realised"))
            continue
        if reason:
            notes[f"owner_note:{reason}"] += 1
            if reason == "OWNER_ESTABLISHED_WITH_EXTRA_LISTING":
                doc_findings.append(SourceFinding(
                    F.OWNER_LISTING_CONFLICT, obs.obs_id, (),
                    f"owner {hdr_h} established by ownerhandle + entmode; also listed by "
                    f"{[x for x in dict(ev)['listed_by'] if x != hdr_h]}"))
        obs = O.SourceEntityObservation(**{**obs.__dict__, "provenance": obs.provenance + (("owner", placement, hdr_h),)})
        if placement == MODEL:
            model.append(obs)
        elif placement == PAPER:
            other.append((str(headers[hdr_h].get("name")) if hdr_h in headers else "PAPER_SPACE", obs))
        else:
            per_block.setdefault(hdr_h, []).append(obs)
    blocks = {}
    for h, hdr in headers.items():
        if _space(hdr) != BLOCK:
            continue
        name = str(hdr.get("name") or "")
        bp = hdr.get("base_pt")
        xref = None
        if hdr.get("blkisxref") or hdr.get("xrefoverlaid") or hdr.get("xref_pname"):
            xref = O.XrefInfo(path=str(hdr.get("xref_pname") or ""),
                              attachment="OVERLAY" if hdr.get("xrefoverlaid") else ("ATTACH" if hdr.get("blkisxref") else "UNKNOWN"),
                              resolved=None, unloaded=None, mapping_status=F.SOURCE_MAPPING_UNVERIFIED)
        anonymous = bool(hdr.get("anonymous")) if "anonymous" in hdr else name.startswith("*")
        blocks[f"H{h}"] = O.BlockDefinition(key=f"H{h}", name=name, base_point=_xy(bp) if bp else (0.0, 0.0),
                                            entities=tuple(per_block.get(h, ())), xref=xref, name_readable=bool(name),
                                            anonymous=anonymous, parent_ref=_parent_ref(hdr, by_handle, unique) if anonymous else None)
    if truncated:
        doc_findings.append(SourceFinding(
            F.HANDLE_VALUE_TRUNCATED, None, (),
            f"{truncated} objects carry 3-byte handles printed with 16 bits; {collisions} handle values collide. "
            "Identity uses (byte size, value); relative references to colliding values are not trusted"))
    missing_bp = [f"H{h}" for h, hdr in headers.items() if "base_pt" not in hdr]
    if missing_bp:
        doc_findings.append(SourceFinding(F.SOURCE_MAPPING_UNVERIFIED, None, (),
                                          f"{len(missing_bp)} block headers without base_pt; read as (0,0)"))
    anchor = O.SourceRevisionAnchor(source_sha256, ROUTE, "libredwg dwgread JSON",
                                    decoder_version or _created_by(decode), decoder_binary_sha256,
                                    parser_lineage="LIBREDWG", conversion_chain=tuple(conversion_chain) or
                                    ("DWG", "LIBREDWG dwgread -O JSON"),
                                    pin_status=PINS.status("LIBREDWG_DWGREAD", decoder_binary_sha256))
    return O.SourceDocument(anchor=anchor, entities=tuple(model), blocks=blocks,
                            header=dict(decode.get("HEADER", {})), findings=tuple(doc_findings), notes=dict(notes),
                            unplaced=tuple(unplaced), other_layouts=tuple(other))


def _parent_ref(hdr, by_handle, unique):
    """Evidence of a dynamic-block parent: the header's application xdata (EED)
    code-5 handle. Recorded as evidence only (mapping UNVERIFIED)."""
    refs = [e.get("value") for e in (hdr.get("eed") or []) if isinstance(e, dict) and e.get("code") == 5]
    if not refs:
        return None
    # EED handles print a byte-size field of 8 (the xdata encoding), not the target's size:
    # resolve by value, and only when that value is unique in the decode
    v = _abs(refs[0])
    tgt = by_handle.get(unique.get(v)) if v is not None else None
    if tgt is None and v is not None and v not in unique:
        return ("AMBIGUOUS_REFERENCE", str(v))
    if tgt is None:
        return ("NON_BLOCK", "ABSENT")
    if _is_block_header(tgt):
        return ("BLOCK_HEADER", f"H{handle_id(tgt.get('handle'))}", str(tgt.get("name") or ""))
    return ("NON_BLOCK", str(tgt.get("object") or tgt.get("entity") or tgt.get("type")))


def _created_by(decode):
    cb = decode.get("created_by")
    return str(cb) if cb else None


def insert_blocks(document) -> dict:
    """{INSERT handle id: block-record handle id} for block-lineage reconciliation (names never used)."""
    out = {}
    obs = (list(document.entities) + [o for b in document.blocks.values() for o in b.entities]
           + [o for _, o in document.other_layouts])
    for o in obs:
        if o.kind == O.INSERT and o.geometry.block_key:
            out[o.source_handle] = o.geometry.block_key[1:]
    return out
