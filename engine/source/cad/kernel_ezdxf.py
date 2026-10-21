"""K2 — the second, independent CAD geometry route: DXF parsed and placed by ezdxf.

Purpose: challenge K1. K2 shares with K1 ONLY the neutral schemas
(observations kinds, findings, capability register, realised records). It
never imports K1's kernel, OCS or affine code: every placement below is
ezdxf's own machinery —

    Insert.matrix44() / Insert.multi_insert()   block and MINSERT placement
    DXFGraphic.copy() + .transform(Matrix44)    entity placement (ezdxf's own
                                                non-uniform fallbacks: ARC/CIRCLE ->
                                                Ellipse.from_arc, LWPOLYLINE ->
                                                virtual_entities, exactly as
                                                ezdxf.explode does)
    OCS(extrusion).to_wcs / Arc.vertices / Ellipse.vertices / bulge_to_arc

and plan orientation is read from the entity's own representation after
ezdxf placed it (sweep is CCW about the extrusion, so CW in plan when
extrusion.z < 0) — not from a composed determinant, which is how K1 decides.
Two different derivations of the same physical fact is the point of K2.

Known ezdxf limitations are PRE-REGISTERED in EZDXF_LIMITATIONS (frozen
before any K1/K2 comparison was run) and are raised as findings when their
trigger condition is met, never discovered afterwards.
"""

from __future__ import annotations

import math
from collections import Counter

import ezdxf
from ezdxf.entities.copy import CopyNotSupported
from ezdxf.lldxf.const import DXFError
from ezdxf.math import InsertTransformationError, NonUniformScalingError, Vec3, bulge_to_arc

from .. import capability as CAP
from .. import findings as F
from .. import observations as O
from ..findings import SourceFinding
from ..realised import (Lineage, RealisedAttribute, RealisedCircle, RealisedCircularArc,
                        RealisedEllipticalArc, RealisedGeometry, RealisedSegment)

ROUTE = "D2_DXF_EZDXF"
MAX_NESTING_DEPTH = 16
PLAN_EPS = 1e-12
TWO_PI = 2.0 * math.pi
REALISED, HIDDEN, CARRIED, FINDING = "REALISED", "HIDDEN", "CARRIED", "FINDING"

# ---------------------------------------------------------------- pre-registered library limitations
# Frozen 2026-09-30 from the R8.0/R8.1 characterisation, BEFORE K2 existed.
EZDXF_LIMITATIONS = {
    "EZDXF-L01": {"version": "1.4.4", "operation": "Insert.virtual_entities() on a MINSERT",
                  "behaviour": "yields the first grid cell only",
                  "fixture": "tests/r8_0/test_r8_0_library_characterisation.py (MINSERT first cell)",
                  "classification": "KNOWN_LIBRARY_LIMITATION",
                  "k2_handling": "K2 never calls virtual_entities() on a MINSERT; it uses multi_insert()",
                  "k2_final_in_domain": True},
    "EZDXF-L02": {"version": "1.4.4", "operation": "Insert.transform() of a MINSERT nested under a reflecting parent",
                  "behaviour": "row/column spacing is not transformed; rows land on the wrong side",
                  "fixture": "tests/r8_0 F06_MINSERT_MIRRORED_PARENT; research/external_engine_lab/MINSERT_REFLECTION_ORACLE.*",
                  "classification": "KNOWN_LIBRARY_LIMITATION",
                  "k2_handling": "K2 raises KNOWN_LIBRARY_LIMITATION (GEOMETRY BLOCKING) on every cell it realises there",
                  "k2_final_in_domain": False},
    "EZDXF-L03": {"version": "1.4.4", "operation": "virtual_entities() of an xref INSERT",
                  "behaviour": "yields nothing: xref content is not in the host file",
                  "fixture": "tests/r8_0 F08 scenes",
                  "classification": "KNOWN_LIBRARY_LIMITATION",
                  "k2_handling": "K2 checks the block record's xref flag first and raises the XREF finding",
                  "k2_final_in_domain": False},
}

CARRIED_DXF = {"TEXT": O.TEXT, "MTEXT": O.MTEXT, "DIMENSION": O.DIMENSION, "HATCH": O.HATCH,
               "POINT": O.POINT, "SOLID": O.SOLID, "ATTDEF": O.ATTDEF, "ARC_DIMENSION": O.DIMENSION,
               "LARGE_RADIAL_DIMENSION": O.DIMENSION}


# ---------------------------------------------------------------- loading
def load(path):
    """(Drawing | None, [SourceFinding]). A DXF ezdxf cannot load is a ROUTE_DECODE_FAILED
    finding with the exact error — never an empty drawing."""
    try:
        return ezdxf.readfile(str(path)), []
    except (OSError, UnicodeDecodeError, StopIteration, DXFError) as err:     # StopIteration: truncated header
        return None, [SourceFinding(F.ROUTE_DECODE_FAILED, None, (), f"{type(err).__name__}: {err}")]


def _attr(entity, name, default=None):
    """A DXF attribute the entity's class may not define (e.g. RTEXT has no 'layer' in ezdxf): the default,
    never an exception - an unknown entity type must reach the UNHANDLED finding, not stop the route."""
    return entity.dxf.get(name, default) if entity.dxf.is_supported(name) else default


def _hid(entity):
    src = entity if entity.dxf.hasattr("handle") and entity.dxf.handle else getattr(entity, "source_of_copy", None)
    h = src.dxf.handle if src is not None and src.dxf.hasattr("handle") else None
    return None if h is None else str(int(h, 16))


def _xy(v):
    return (float(v.x), float(v.y))


def _plan(ext):
    if ext is None:
        return 1
    if abs(ext.x) > PLAN_EPS or abs(ext.y) > PLAN_EPS:
        return 0
    return 1 if ext.z > 0 else -1


def _flip(d):
    return "CW" if d == "CCW" else "CCW"


class _K2:
    def __init__(self, doc):
        self.doc = doc
        self.out = RealisedGeometry()
        self._sub = 0                    # sub-part of a single-curve entity; None for ezdxf-exploded parts

    # -------------------------------------------------------------- bookkeeping
    def dispose(self, kind, obs_id):
        self.out.dispositions[kind] += 1
        self.out.visits += 1
        if obs_id is not None:
            self.out.obs_dispositions.setdefault(obs_id, Counter())[kind] += 1

    def finding(self, code, obs_id, path, detail="", impacts=None):
        self.out.findings.append(SourceFinding(code, obs_id, tuple(path), detail, impacts))

    def lineage(self, obs_id, path, layer, kind, sub_part=0):
        return Lineage(obs_id, obs_id[3:] if obs_id else None, tuple(path), layer, kind,
                       sub_part if self._sub is not None else None)

    # -------------------------------------------------------------- the walk
    def emit(self, e, path, depth, visible, reflected_parent, source=None, converted=None):
        t = e.dxftype()
        hid = _hid(source if source is not None else e)
        obs_id = f"D2:{hid}" if hid is not None else None
        layer = _attr(e, "layer")
        if t == "OLE2FRAME":
            self.finding(F.SKIPPED, obs_id, path, "OLE2FRAME is an embedded OLE object, not vector geometry")
            return self.dispose(FINDING, obs_id)
        if t == "ACAD_PROXY_ENTITY":
            self.finding(F.PROXY, obs_id, path, "proxy entity: proxy graphics only")
            return self.dispose(FINDING, obs_id)
        if t in ("WIPEOUT", "IMAGE"):
            self.finding(F.CUSTOM_CLASS, obs_id, path, f"{t} is not vector geometry", CAP.impacts_for_kind(t))
            return self.dispose(FINDING, obs_id)
        if not (visible and not _attr(e, "invisible", 0)):
            self.out.hidden.append({"obs_id": obs_id, "kind": t, "instance_path": list(path)})
            return self.dispose(HIDDEN, obs_id)
        if t in CARRIED_DXF:
            self.out.carried.append({"obs_id": obs_id, "kind": CARRIED_DXF[t], "instance_path": list(path)})
            if t == "SOLID":
                self.finding(F.UNVERIFIED_FOR_QTO_USE, obs_id, path, "SOLID carried; role not established by type")
            return self.dispose(CARRIED, obs_id)
        if t == "INSERT":
            return self.insert(e, obs_id, path, depth, visible, reflected_parent)
        handlers = {"LINE": self.line, "ARC": self.arc, "CIRCLE": self.circle, "LWPOLYLINE": self.lwpolyline,
                    "ELLIPSE": self.ellipse}
        h = handlers.get(t)
        if h is None:
            self.finding(F.UNHANDLED, obs_id, path, f"DXF type {t} has no K2 realisation")
            return self.dispose(FINDING, obs_id)
        ext = e.dxf.get("extrusion", None) if t != "LINE" else None
        if t != "LINE" and ext is not None and _plan(Vec3(ext)) == 0:
            self.finding(F.UNSUPPORTED_FRAME, obs_id, path, f"extrusion {tuple(ext)} is not a plan normal")
            return self.dispose(FINDING, obs_id)
        if t == "ELLIPSE":
            self.ellipse(e, obs_id, path, layer, converted or "ELLIPSE")
        else:
            h(e, obs_id, path, layer)
        self.dispose(REALISED, obs_id)

    def line(self, e, obs_id, path, layer):
        self.out.segments.append(RealisedSegment(_xy(e.dxf.start), _xy(e.dxf.end), self.lineage(obs_id, path, layer, "LINE")))

    def arc(self, e, obs_id, path, layer):
        sa, ea = e.dxf.start_angle, e.dxf.end_angle
        sw = (ea - sa) % 360.0 or 360.0
        s, m, en = list(e.vertices([sa, sa + sw / 2.0, sa + sw]))
        c = e.ocs().to_wcs(e.dxf.center)
        d = "CCW" if _plan(Vec3(e.dxf.extrusion)) > 0 else "CW"
        self.out.arcs.append(RealisedCircularArc(_xy(c), float(e.dxf.radius), _xy(s), _xy(m), _xy(en), d, "ARC",
                                                 self.lineage(obs_id, path, layer, "ARC")))

    def circle(self, e, obs_id, path, layer):
        self.out.circles.append(RealisedCircle(_xy(e.ocs().to_wcs(e.dxf.center)), float(e.dxf.radius),
                                               self.lineage(obs_id, path, layer, "CIRCLE")))

    def lwpolyline(self, e, obs_id, path, layer):
        ocs = e.ocs()
        elev = e.dxf.get("elevation", 0.0)
        pts = [(p[0], p[1], p[2]) for p in e.get_points("xyb")]
        n = len(pts)
        spans = range(n) if (e.closed and n > 2) else range(n - 1)
        sign = _plan(Vec3(e.dxf.extrusion))
        for i in spans:
            (ax, ay, b), (bx, by, _) = pts[i], pts[(i + 1) % n]
            if ax == bx and ay == by:
                self.finding(F.DEGENERATE_GEOMETRY, obs_id, path, f"span {i} has coincident end points")
                continue
            A, B = _xy(ocs.to_wcs((ax, ay, elev))), _xy(ocs.to_wcs((bx, by, elev)))
            lin = self.lineage(obs_id, path, layer, "LWPOLYLINE", i)
            if abs(b) < 1e-12:
                self.out.segments.append(RealisedSegment(A, B, lin))
                continue
            centre, a0, a1, r = bulge_to_arc((ax, ay), (bx, by), b)       # OCS, CCW from a0 to a1
            am = a0 + ((a1 - a0) % TWO_PI) / 2.0
            M = _xy(ocs.to_wcs((centre[0] + r * math.cos(am), centre[1] + r * math.sin(am), elev)))
            C = _xy(ocs.to_wcs((centre[0], centre[1], elev)))
            d = "CCW" if b > 0 else "CW"
            if sign < 0:
                d = _flip(d)
            self.out.arcs.append(RealisedCircularArc(C, float(r), A, M, B, d, "BULGE", lin))

    def ellipse(self, e, obs_id, path, layer, source="ELLIPSE"):
        t0, t1 = e.dxf.start_param, e.dxf.end_param
        sw = (t1 - t0) % TWO_PI or TWO_PI
        s, m, en = list(e.vertices([t0, t0 + sw / 2.0, t0 + sw]))
        u, v = e.dxf.major_axis, e.minor_axis
        d = "CCW" if _plan(Vec3(e.dxf.extrusion)) > 0 else "CW"
        self.out.elliptical_arcs.append(RealisedEllipticalArc(
            _xy(e.dxf.center), _xy(u), _xy(v), t0, t0 + sw, _xy(s), _xy(m), _xy(en), d,
            abs(sw - TWO_PI) < 1e-12, source, self.lineage(obs_id, path, layer, source)))
        if source != "ELLIPSE":
            self.finding(F.NON_UNIFORM_SCALE_CURVE, obs_id, path,
                         "ezdxf placed a circular curve under non-uniform scale as an ELLIPSE")

    # -------------------------------------------------------------- blocks
    def insert(self, ins, obs_id, path, depth, visible, reflected_parent):
        here = path + (obs_id,)
        name = ins.dxf.name
        blk = self.doc.blocks.get(name)
        if blk is None:
            self.finding(F.MISSING_BLOCK_DEFINITION, obs_id, here, f"block {name!r} is not defined")
            return self.dispose(FINDING, obs_id)
        rec = blk.block_record
        if rec.is_xref:
            flags = blk.block.dxf.get("flags", 0)
            code = F.XREF_CONTENT_NOT_IN_SOURCE if flags & 32 else F.XREF_NOT_RESOLVED
            att = "OVERLAY" if flags & 8 else "ATTACH"
            self.finding(code, obs_id, here, f"xref {name!r} attachment={att} (EZDXF-L03); zero children is not "
                                             "evidence of no geometry")
            return self.dispose(FINDING, obs_id)
        if name.upper().startswith("*U"):
            self.finding(F.DYNAMIC_BLOCK_UNRESOLVED, obs_id, here,
                         f"anonymous block {name!r}; K2 does not read dynamic-block parent xdata")
        if depth >= MAX_NESTING_DEPTH:
            self.finding(F.NESTING_LIMIT, obs_id, here, f"nesting deeper than {MAX_NESTING_DEPTH}")
            return self.dispose(FINDING, obs_id)
        self.dispose(REALISED, obs_id)
        grid = ins.mcount > 1
        if grid:
            cells = list(ins.multi_insert())                                   # EZDXF-L01: never virtual_entities()
            rows, cols = ins.dxf.row_count, ins.dxf.column_count
            labels = [f"[{c},{r}]" for r in range(rows) for c in range(cols)]
            if len(cells) != len(labels):
                self.finding(F.UNSUPPORTED, obs_id, here, "multi_insert() skipped coincident cells; labels not aligned")
                labels = [f"[cell{k}]" for k in range(len(cells))]
        else:
            cells, labels = [ins], [""]
        for label, cell in zip(labels, cells):
            m = cell.matrix44()
            ux, uy = m.ux, m.uy
            reflected = (ux.x * uy.y - ux.y * uy.x) < 0
            cell_path = path + (obs_id + label,)
            limited = grid and reflected_parent
            for child in blk:
                if child.dxftype() == "ATTDEF":
                    continue                                                 # values arrive as ATTRIBs
                placed = self._placed(child, m, cell_path)
                # a source entity exploded by ezdxf into several parts (virtual_entities) has no source span index
                # the route can name: those parts carry sub_part None (R8.8: never counted from the output)
                one_curve = len(placed) == 1 and (placed[0][0].dxftype() == child.dxftype() or placed[0][1] is not None)
                for v, conv in placed:
                    self._sub = 0 if one_curve else None          # reset: a nested INSERT's walk changes it
                    self.emit(v, cell_path, depth + 1, visible, reflected, source=child, converted=conv)
                    if limited and v.dxftype() != "INSERT":
                        self.finding(F.KNOWN_LIBRARY_LIMITATION, f"D2:{_hid(child)}", cell_path,
                                     "EZDXF-L02: MINSERT under a reflecting parent; ezdxf does not transform spacing",
                                     ((F.GEOMETRY, F.BLOCKING),))
                self._sub = 0
        for att in ins.attribs:
            p = att.ocs().to_wcs(att.dxf.insert)
            self.out.attributes.append(RealisedAttribute(att.dxf.get("tag", ""), att.dxf.get("text", ""), _xy(p),
                                                         obs_id[3:], self.lineage(obs_id, here, None, "INSERT")))

    def _placed(self, child, m, path):
        """ezdxf's own per-entity placement (mirrors ezdxf.explode), keeping the source child.
        Yields (placed entity, conversion) where conversion names what ezdxf turned into an ELLIPSE."""
        try:
            c = child.copy()
        except CopyNotSupported:
            if hasattr(child, "virtual_entities"):
                return [(x.transform(m), None) for x in child.virtual_entities()]
            self.finding(F.UNSUPPORTED, f"D2:{_hid(child)}", path, "entity not copyable by ezdxf")
            return []
        try:
            return [(c.transform(m), None)]
        except NonUniformScalingError:
            t = child.dxftype()
            if t in ("ARC", "CIRCLE"):
                return [(ezdxf.entities.Ellipse.from_arc(child).transform(m), t)]
            if t in ("LWPOLYLINE", "POLYLINE"):
                out = []
                for part in child.virtual_entities():
                    try:
                        out.append((part.transform(m), None))
                    except NonUniformScalingError:
                        out.append((ezdxf.entities.Ellipse.from_arc(part).transform(m), "BULGE"))
                return out
            self.finding(F.UNSUPPORTED, f"D2:{_hid(child)}", path, f"{t}: non-uniform scaling unsupported by ezdxf")
            return []
        except InsertTransformationError:
            self.finding(F.UNSUPPORTED, f"D2:{_hid(child)}", path,
                         "INSERT cannot be represented under this transform (ezdxf InsertTransformationError)")
            return []


def realise(doc) -> RealisedGeometry:
    k = _K2(doc)
    for e in doc.modelspace():
        k.emit(e, (), 0, True, False)
    return k.out


def anchor(path=None, source_sha256=None, conversion_chain=(), parser_lineage=None) -> O.SourceRevisionAnchor:
    from .. import decoder_pins as PINS
    return O.SourceRevisionAnchor(source_sha256, ROUTE, "ezdxf", ezdxf.__version__, None,
                                  parser_lineage=parser_lineage or "EZDXF_DXF_READER",
                                  conversion_chain=tuple(conversion_chain),
                                  pin_status=PINS.package_status("EZDXF", ezdxf.__version__))


def insert_blocks(doc) -> dict:
    """{INSERT handle: block-record handle} for block-lineage reconciliation (names never used)."""
    out = {}
    layouts = [doc.modelspace()] + [b for b in doc.blocks]
    for lay in layouts:
        for e in lay:
            if e.dxftype() == "INSERT":
                blk = doc.blocks.get(e.dxf.name)
                if blk is not None:
                    out[str(int(e.dxf.handle, 16))] = str(int(blk.block_record.dxf.handle, 16))
    return out
