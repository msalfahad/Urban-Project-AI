"""SOURCE EXCEPTIONS (R8.5 §10-§14) — resolve unrealised source objects by POSITIVE evidence, never by look.

V-CAD-5 (no UNHANDLED class on a profile-relevant layer of the region) is NOT weakened: an object the
kernel cannot realise stays blocking unless source evidence establishes, per region, what it is and where
it is. Evidence used (all read from the source, none invented):

    CLASS IDENTITY   the CLASSES record (dxfname + cppname + application) of a class-based entity AND the
                     entity's own subclass marker must agree; a built-in type needs its type name and
                     subclass marker to agree. Type numbers >= 500 are per file and never identify a class.
    PLACEMENT        the object's own placement fields (IMAGE: pt0 / uvec / vvec / pixel size;
                     OLE2FRAME: its four stored corners) or its stored entity graphics (the `preview`
                     proxy-graphics stream), composed through the instance path of every INSERT above it.
                     A text record in the graphics gives a point, not an extent: it cannot prove absence.
    REGION           the region bounds being measured.
    LAYER ROLE       the caller's explicit layer -> reason map (adapter roles, layer-profile roles).

States (per object, per region):
    PROFILE_IRRELEVANT_PROVEN   located (exact or guaranteed bound) wholly outside the region
    PRESENTATION_ONLY_PROVEN    class proven to be a presentation mask (it hides plotted geometry, adds none)
    ANNOTATION_ONLY_PROVEN      class proven to be a dimension annotation: it cannot carry wall / opening /
                                column / room-boundary / finish geometry; it blocks only methods that
                                consume dimensions
    IDENTITY_ONLY               class proven to be text: it may carry a label (identity), not geometry
    PROFILE_RELEVANT_BLOCKING   inside (or not excluded from) the region on a profile-relevant layer, with
                                no role that rules out geometry
    UNRESOLVED_REVIEW_REQUIRED  class or location not established; blocking on a profile-relevant layer
                                (fail closed), REVIEW elsewhere
"""

from __future__ import annotations

import math
import re
import struct
from dataclasses import dataclass, field

from . import findings as F
from . import observations as O

PROFILE_IRRELEVANT_PROVEN = "PROFILE_IRRELEVANT_PROVEN"
PRESENTATION_ONLY_PROVEN = "PRESENTATION_ONLY_PROVEN"
ANNOTATION_ONLY_PROVEN = "ANNOTATION_ONLY_PROVEN"
IDENTITY_ONLY = "IDENTITY_ONLY"
PROFILE_RELEVANT_BLOCKING = "PROFILE_RELEVANT_BLOCKING"
UNRESOLVED_REVIEW_REQUIRED = "UNRESOLVED_REVIEW_REQUIRED"
STATES = (PROFILE_IRRELEVANT_PROVEN, PRESENTATION_ONLY_PROVEN, ANNOTATION_ONLY_PROVEN, IDENTITY_ONLY,
          PROFILE_RELEVANT_BLOCKING, UNRESOLVED_REVIEW_REQUIRED)

# location quality
EXACT, BOUNDED, POINT_ONLY, LOCATION_UNRESOLVED = "EXACT", "BOUNDED", "POINT_ONLY", "LOCATION_UNRESOLVED"

# roles of standard AutoCAD / ObjectARX classes: (dxfname, cppname) -> role. Generic product classes only.
DIMENSION_ANNOTATION, TEXT_ANNOTATION = "DIMENSION_ANNOTATION", "TEXT_ANNOTATION"
PRESENTATION_MASK, RASTER_CONTENT, EMBEDDED_DOCUMENT = "PRESENTATION_MASK", "RASTER_CONTENT", "EMBEDDED_DOCUMENT"
CLASS_ROLES = {
    ("ARC_DIMENSION", "AcDbArcDimension"): DIMENSION_ANNOTATION,
    ("LARGE_RADIAL_DIMENSION", "AcDbRadialDimensionLarge"): DIMENSION_ANNOTATION,
    ("RTEXT", "RText"): TEXT_ANNOTATION,
    ("WIPEOUT", "AcDbWipeout"): PRESENTATION_MASK,
    ("IMAGE", "AcDbRasterImage"): RASTER_CONTENT,
}
BUILTIN_ROLES = {("OLE2FRAME", "AcDbOle2Frame"): EMBEDDED_DOCUMENT}
# what each role can influence (reported per object, §10)
INFLUENCE = {
    DIMENSION_ANNOTATION: {"wall": False, "opening": False, "column": False, "room_boundary": False, "label": False,
                           "dimension": True, "finish": False, "measurement_completeness": "DIMENSION_METHODS_ONLY"},
    TEXT_ANNOTATION: {"wall": False, "opening": False, "column": False, "room_boundary": False, "label": True,
                      "dimension": False, "finish": False, "measurement_completeness": "IDENTITY_METHODS_ONLY"},
    PRESENTATION_MASK: {"wall": False, "opening": False, "column": False, "room_boundary": False, "label": False,
                        "dimension": False, "finish": False, "measurement_completeness": "PLOT_APPEARANCE_ONLY"},
    RASTER_CONTENT: {k: "UNKNOWN" for k in ("wall", "opening", "column", "room_boundary", "label", "dimension",
                                            "finish", "measurement_completeness")},
    EMBEDDED_DOCUMENT: {k: "UNKNOWN" for k in ("wall", "opening", "column", "room_boundary", "label", "dimension",
                                               "finish", "measurement_completeness")},
}
_UNKNOWN_INFLUENCE = {k: "UNKNOWN" for k in ("wall", "opening", "column", "room_boundary", "label", "dimension",
                                             "finish", "measurement_completeness")}

# ---------------------------------------------------------------- proxy graphics (entity preview) stream
_POLY = (6, 7, 32)                 # polyline, polygon, polyline with normal: int32 n + n * 3 doubles
_CIRCLE, _ARC = 2, 4               # centre (3d), radius, ... -> guaranteed bound centre +- r
_EXTENTS = 1                       # two 3d points
_TEXT = (10, 11, 36, 38)           # position only
_ATTRIBUTE_RECORDS = frozenset(range(14, 32)) | {19, 20}   # colour / layer / linetype / marker / transform stack
_GEOMETRY_UNPARSED = frozenset({3, 5, 8, 9, 12, 13, 33, 44})


def proxy_graphics(hexstr: str | None) -> dict:
    """Decode an entity graphics stream: {points, quality, records, unparsed_geometry, text_points}."""
    if not hexstr:
        return {"points": [], "quality": LOCATION_UNRESOLVED, "records": [], "unparsed_geometry": [], "text_points": []}
    b = bytes.fromhex(hexstr)
    if len(b) < 8:
        return {"points": [], "quality": LOCATION_UNRESOLVED, "records": [], "unparsed_geometry": ["TRUNCATED"],
                "text_points": []}
    _, count = struct.unpack_from("<ii", b, 0)
    off, recs, pts, texts, unparsed, bounded, pushed = 8, [], [], [], [], False, 0
    while off + 8 <= len(b) and len(recs) < count:
        size, typ = struct.unpack_from("<ii", b, off)
        if size < 8 or off + size > len(b):
            unparsed.append(f"BAD_RECORD@{off}")
            break
        p = b[off + 8:off + size]
        recs.append((typ, size))
        try:
            if typ in _POLY:
                n = struct.unpack_from("<i", p, 0)[0]
                pts += [struct.unpack_from("<3d", p, 4 + 24 * i)[:2] for i in range(n)]
            elif typ in (_CIRCLE, _ARC):
                cx, cy, _, r = struct.unpack_from("<4d", p, 0)
                pts += [(cx - r, cy - r), (cx + r, cy + r)]
                bounded = True
            elif typ == _EXTENTS:
                x0, y0, _, x1, y1, _ = struct.unpack_from("<6d", p, 0)
                pts += [(x0, y0), (x1, y1)]
            elif typ in _TEXT:
                texts.append(struct.unpack_from("<3d", p, 0)[:2])
            elif typ == 29:
                mtx = struct.unpack_from("<16d", p, 0)
                ident = (1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0)
                if any(abs(a - b) > 1e-12 for a, b in zip(mtx, ident)):
                    pushed += 1                   # a non-identity model transform: extents not composed
            elif typ in _GEOMETRY_UNPARSED:
                unparsed.append(typ)
        except struct.error:
            unparsed.append(f"SHORT_RECORD_{typ}")
        off += size
    finite = [q for q in pts if all(math.isfinite(v) for v in q)]
    if unparsed or not finite:
        quality = LOCATION_UNRESOLVED if not finite else POINT_ONLY
    elif texts:
        quality = POINT_ONLY                      # glyph extents are not in the stream
    else:
        quality = BOUNDED if bounded else EXACT
    return {"points": finite, "quality": quality, "records": recs, "unparsed_geometry": unparsed,
            "text_points": texts, "model_transform_records": pushed}


# ---------------------------------------------------------------- placement
def instance_matrix(document: O.SourceDocument, instance_path):
    """The composed placement of an object reached through `instance_path` (kernel convention)."""
    from .cad import kernel as K
    from .cad.affine import Affine2
    by_id = {}
    for o in document.entities:
        by_id[o.obs_id] = o
    for blk in document.blocks.values():
        for o in blk.entities:
            by_id[o.obs_id] = o
    m = Affine2.identity()
    for step in instance_path or ():
        oid, label = (step.split("[", 1)[0], "[" + step.split("[", 1)[1]) if "[" in step else (step, "")
        ins = by_id.get(oid)
        if ins is None or ins.kind != O.INSERT:
            return None
        g = ins.geometry
        blk = document.blocks.get(g.block_key)
        if blk is None:
            return None
        off = dict(K.grid_offsets(g.grid, g.rotation)).get(label, (0.0, 0.0))
        m = m @ K.frame_matrix(ins.extrusion) @ K.insert_matrix(g, blk.base_point, off)
    return m


def raw_extent(raw: dict) -> tuple:
    """(local points, quality, basis) from the object's own fields, else its graphics stream."""
    if raw.get("entity") == "IMAGE" and raw.get("pt0") and raw.get("uvec") and raw.get("vvec") \
            and isinstance(raw.get("size"), list):
        p0, u, v, (w, h) = raw["pt0"], raw["uvec"], raw["vvec"], raw["size"]
        pts = [(p0[0] + a * u[0] * w + c * v[0] * h, p0[1] + a * u[1] * w + c * v[1] * h) for a in (0, 1) for c in (0, 1)]
        return pts, EXACT, "IMAGE pt0/uvec/vvec/size"
    if raw.get("entity") == "OLE2FRAME" and raw.get("data"):
        try:
            vals = struct.unpack("<12d", bytes.fromhex(raw["data"][4:4 + 192]))
            pts = [(vals[i], vals[i + 1]) for i in range(0, 12, 3)]
            if all(math.isfinite(c) for q in pts for c in q):
                return pts, EXACT, "OLE2FRAME stored corners"
        except (ValueError, struct.error):
            pass
    pg = proxy_graphics(raw.get("preview"))
    if pg["points"] and pg.get("model_transform_records"):
        return pg["points"], POINT_ONLY, "entity graphics (model transform pushed: extents not composed)"
    return pg["points"], pg["quality"], "entity graphics stream"


def placed_bounds(points, matrix):
    if not points or matrix is None:
        return None
    q = [matrix.apply(p) for p in points]
    xs, ys = [p[0] for p in q], [p[1] for p in q]
    return (min(xs), min(ys), max(xs), max(ys))


# ---------------------------------------------------------------- text content (RTEXT)
_DIESEL = re.compile(r"\$\(\s*(\w+)\s*,\s*([^)]*)\)")
# system variables that only describe the drawing file / session (a plot stamp), never the building
PLOT_STAMP_VARIABLES = frozenset({"dwgprefix", "dwgname", "ctab", "loginname", "date", "cdate", "plotter", "plotid"})


def embedded_strings(raw: dict) -> list:
    """Printable strings in the object's undecoded bit stream (ASCII and UTF-16LE, every bit alignment)."""
    ub = raw.get("unknown_bits")
    if not ub:
        return []
    b = bytes.fromhex(ub)
    out = []
    for sh in range(8):
        v = int.from_bytes(b, "big") << sh
        bb = v.to_bytes(len(b) + 1, "big")
        out += [m.decode("ascii") for m in re.findall(rb"[ -~]{16,}", bb)]
        out += [m.decode("utf-16le") for m in re.findall(rb"(?:[ -~]\x00){16,}", bb)]
    return out


def text_content_class(raw: dict) -> tuple:
    """(PLOT_STAMP | UNKNOWN, detail). PLOT_STAMP only if a DIESEL expression is found whose every
    function is getvar of a file / session variable or edtime, and nothing else of substance remains."""
    for t in embedded_strings(raw):
        calls = _DIESEL.findall(t)
        if not calls:
            continue
        ok = all((fn.lower() == "getvar" and arg.strip().strip('"').lower() in PLOT_STAMP_VARIABLES)
                 or fn.lower() == "edtime" for fn, arg in calls)
        rest = _DIESEL.sub("", t)
        if ok and not re.search(r"[A-Za-z0-9\u0600-\u06FF]{3,}", rest):
            return "PLOT_STAMP", t.strip()[:200]
    return "UNKNOWN", ""


# ---------------------------------------------------------------- classification
def class_identity(raw: dict, class_record: dict | None) -> tuple:
    """(role or None, basis). Two source fields must agree: the class record and either the entity's
    subclass marker or, for text classes, a DIESEL expression in the object's own data."""
    sub = raw.get("_subclass")
    if class_record:
        key = (class_record.get("dxfname"), class_record.get("cppname"))
        role = CLASS_ROLES.get(key)
        if role and sub == key[1]:
            return role, f"CLASSES {key[0]}/{key[1]} ({class_record.get('appname')}) + subclass {sub}"
        if role == TEXT_ANNOTATION and text_content_class(raw)[0] == "PLOT_STAMP":
            return role, f"CLASSES {key[0]}/{key[1]} ({class_record.get('appname')}) + DIESEL content in the object"
        if role:
            return None, f"class record {key} but entity subclass {sub!r}: not agreed"
        return None, f"class {key} has no established role"
    key = (raw.get("entity"), sub)
    role = BUILTIN_ROLES.get(key)
    return (role, f"built-in {key[0]} + subclass {sub}") if role else (None, f"built-in {key} has no established role")


def _disjoint(a, b):
    return a[2] < b[0] or b[2] < a[0] or a[3] < b[1] or b[3] < a[1]


@dataclass(frozen=True)
class SourceException:
    region_id: str
    obs_id: str
    handle: str
    code: str
    source_type: str
    layer: str | None
    layer_relevance: str | None          # reason the layer is profile-relevant, or None
    class_role: str | None
    class_basis: str
    location_quality: str
    location_basis: str
    placed_bounds: tuple | None
    region_overlap: str                  # DISJOINT / OVERLAPS / UNKNOWN
    state: str
    reason: str
    influence: dict = field(default_factory=dict)
    instance_path: tuple = ()

    def as_dict(self):
        d = dict(self.__dict__)
        d["instance_path"] = list(self.instance_path)
        return d


def classify(row: dict, raw: dict, class_record: dict | None, document: O.SourceDocument, region_id: str,
             region_bounds, relevant_layers: dict) -> SourceException:
    role, cbasis = class_identity(raw, class_record)
    local, quality, lbasis = raw_extent(raw)
    m = instance_matrix(document, row.get("instance_path") or ())
    pb = placed_bounds(local, m) if quality in (EXACT, BOUNDED, POINT_ONLY) else None
    if m is None:
        quality, lbasis = LOCATION_UNRESOLVED, lbasis + "; instance path not composable"
    overlap = "UNKNOWN" if pb is None or region_bounds is None else (
        "DISJOINT" if _disjoint(pb, region_bounds) else "OVERLAPS")
    rel = relevant_layers.get(row.get("layer"))
    if overlap == "DISJOINT" and quality in (EXACT, BOUNDED):
        state, why = PROFILE_IRRELEVANT_PROVEN, f"located ({quality}, {lbasis}) wholly outside region {region_id}"
    elif role == PRESENTATION_MASK:
        state, why = PRESENTATION_ONLY_PROVEN, f"{cbasis}: masks plotted geometry, adds none"
    elif role == DIMENSION_ANNOTATION:
        state, why = ANNOTATION_ONLY_PROVEN, f"{cbasis}: dimension annotation, not measured geometry"
    elif role == TEXT_ANNOTATION and text_content_class(raw)[0] == "PLOT_STAMP":
        state = ANNOTATION_ONLY_PROVEN
        why = f"{cbasis}: text content is a plot stamp ({text_content_class(raw)[1][:80]!r}); not a label, not geometry"
    elif role == TEXT_ANNOTATION:
        state, why = IDENTITY_ONLY, f"{cbasis}: text; may carry a label, not geometry"
    elif rel and role is None:
        state, why = PROFILE_RELEVANT_BLOCKING, f"no established role; on profile-relevant layer ({rel}); " \
                                                f"location {overlap.lower()}"
    else:
        state = UNRESOLVED_REVIEW_REQUIRED
        why = (f"role {role or 'unknown'} does not rule out geometry; location {overlap.lower()} ({quality})"
               + (f"; profile-relevant layer ({rel})" if rel else "; layer not profile-relevant"))
    infl = dict(INFLUENCE.get(role, _UNKNOWN_INFLUENCE))
    if state == ANNOTATION_ONLY_PROVEN and role == TEXT_ANNOTATION:
        infl.update(label=False, measurement_completeness="NONE (plot stamp)")
    return SourceException(region_id, row.get("obs_id"), str(row.get("handle")), row.get("code"),
                           row.get("source_type"), row.get("layer"), rel, role, cbasis, quality, lbasis, pb, overlap,
                           state, why, infl, tuple(row.get("instance_path") or ()))


def impacts_for(exc: SourceException, census_impacts) -> tuple:
    s = exc.state
    if s == PROFILE_IRRELEVANT_PROVEN:
        return ((F.GEOMETRY_COMPLETENESS, F.INFO),)
    if s == PRESENTATION_ONLY_PROVEN:
        return ((F.PRESENTATION, F.REVIEW),)
    if s == ANNOTATION_ONLY_PROVEN:
        return ((F.DOCUMENT_CONTENT, F.REVIEW), (F.SEMANTICS, F.REVIEW))
    if s == IDENTITY_ONLY:
        return ((F.IDENTITY, F.BLOCKING), (F.SEMANTICS, F.REVIEW))
    if s == PROFILE_RELEVANT_BLOCKING or (s == UNRESOLVED_REVIEW_REQUIRED and exc.layer_relevance):
        # fail closed: whatever the capability row declares, an unresolved object on a profile-relevant
        # layer may be geometry of the region
        imp = dict(census_impacts)
        imp[F.GEOMETRY_COMPLETENESS] = F.BLOCKING
        return tuple(imp.items())
    return ((F.GEOMETRY_COMPLETENESS, F.REVIEW),)


def region_findings(exceptions) -> list:
    """SourceFindings in region scope from classified exceptions (the census impacts are replaced only
    by a state that positive evidence established)."""
    out = []
    for e, census_impacts in exceptions:
        out.append(F.SourceFinding(e.code, None, (), f"{e.source_type} handle {e.handle} layer {e.layer!r}: {e.state} "
                                                       f"— {e.reason}", impacts_for(e, census_impacts), scope=e.region_id))
    return out
