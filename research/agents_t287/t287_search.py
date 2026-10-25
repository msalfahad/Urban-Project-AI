"""T-287 designer-gap sheet search (DESIGNER_GAP_SEARCH_V1): is an item printed on the issued sheets, or missing?

Research only, not wired into the engine. ERS s.2 (search every sheet first), s.2.7 / s.6 (only genuinely unresolved
items go to the designer). The search never produces a quantity: a question is FOUND (with the printed value and its
handle) or MISSING (no printed value; the quantity stays HELD, never a default).

Pure core (stdlib): entities in one common plan frame (`Ent`), a region = the extent of named anchor handles plus a
margin, mapped onto every plan sheet; evidence patterns per question; a verdict per question and sheet.
DXF layer (`read_dxf`, ezdxf imported lazily): flattens a structural DXF whose plan sheets sit side by side at a fixed
pitch (ST7757 frames, T-217) and an architectural DXF registered to it by matching level marks at runtime (no offset
is committed), so a region drawn on one sheet is searched on every other sheet at the same plan position.

    python3 -I research/agents_t287/t287_alsenan.py <ST7757 dxf> <P7757 dxf> [--write]
"""
from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass, field

SCHEMA = "T287_DESIGNER_GAP_SEARCH_V1"

# ---- evidence patterns (what would SETTLE a question if printed inside its region) -------------------------------
LEVEL_RE = re.compile(r"^(?:%%[pP]|±|\+|-)?\s?\d{1,2}\.\d{2}$")
THICK_RE = re.compile(r"^(?:T\s*=?\s*\d{1,3}(?:\s*cm)?(?:\s.*)?|t\s*=\s*\d{1,3}(?:\.\d+)?\s*(?:cm|m)?|"
                      r"(?:THICK(?:NESS)?\.?|WAIST)\s*[:=]?\s*\d{1,3}(?:\s*cm)?|\d{1,3}\s*cm\s*(?:THICK|WAIST).*)$",
                      re.IGNORECASE)
STRUCT_LEVEL_RE = re.compile(r"T\.?\s?O\.?\s?S\b|S\.\s?S\.\s?L|T\.\s?O\.\s?B|N\.\s?G\.\s?L|\bNECK\b|رقب", re.IGNORECASE)
STAIR_SHAPE_RE = re.compile(r"WINDER|LANDING|S\.\s?S\.\s?L|SOFFIT|TURN", re.IGNORECASE)
DOME_RE = re.compile(r"DOME|\bRING\b|DRUM|قب[ةه]|OPENING|VOID", re.IGNORECASE)
THICK_WORD_RE = re.compile(r"THICK|WAIST|سم[اك]", re.IGNORECASE)


@dataclass(frozen=True)
class Ent:
    """One drawn entity in the common plan frame (metres). sheet: e.g. 'ST p.4' / 'ARCH GF plan' / 'ARCH other'."""
    sheet: str
    kind: str            # TEXT, DIMENSION, TAG (a block whose texts are read, e.g. 'T 16'), CIRCLE, ARC, LINE, HATCH, ...
    layer: str
    handle: str
    box: tuple           # (x0, y0, x1, y1) in metres
    text: str = ""
    value: float | None = None   # a dimension's measurement in metres
    pts: tuple = ()              # LINE / LWPOLYLINE vertices in metres (closed outlines repeat the first vertex)


@dataclass
class Question:
    qid: str
    asks: str
    anchors: tuple               # (sheet, handle, ...) the element outline: the region is their extent
    margin: float                # m around the anchors' extent
    evidence: tuple              # regexes; a TEXT / TAG matching one inside the region settles (FOUND)
    sheets: tuple = ()           # sheets searched by region (empty = every plan sheet)
    dims_settle: bool = False    # a DIMENSION lying wholly inside the region also counts (a long chain passing through
                                 # measures something else and is context only)
    shapes_settle: tuple = ()    # entity kinds that settle (e.g. CIRCLE for a dome opening) ...
    min_shape: float = 1.0       # ... when at least this size (m): a callout bubble is not an opening or a ring
    context: tuple = ()          # regexes recorded (not settling): what the sheet does print there


@dataclass
class Finding:
    qid: str
    sheet: str
    searched: int
    hits: list = field(default_factory=list)       # [(handle, kind, text or value)]
    context: list = field(default_factory=list)

    @property
    def verdict(self) -> str:
        return "FOUND" if self.hits else "MISSING"


def inflate(b, m):
    return (b[0] - m, b[1] - m, b[2] + m, b[3] + m)


def intersects(a, b):
    return not (a[2] < b[0] or a[0] > b[2] or a[3] < b[1] or a[1] > b[3])


def union(boxes):
    boxes = list(boxes)
    if not boxes:
        raise ValueError("region has no anchor: an element without an outline is never searched as 'nothing printed'")
    return (min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes))


def region(ents_by_handle, anchors):
    """Extent of the anchor handles on their own sheet. anchors = ((sheet, handle), ...). A missing handle raises."""
    boxes = []
    for sheet, h in anchors:
        e = ents_by_handle.get((sheet, h))
        if e is None:
            raise KeyError(f"anchor {sheet}:{h} not in the drawing")
        boxes.append(e.box)
    return union(boxes)


def contains(outer, inner):
    return outer[0] <= inner[0] and outer[1] <= inner[1] and inner[2] <= outer[2] and inner[3] <= outer[3]


def _matches(e, pats):
    return e.kind in ("TEXT", "TAG") and any(p.search(e.text.strip()) for p in pats)


def search(ents, q, plan_sheets):
    """One Finding per searched sheet: every entity inside the region (+ margin) counted, evidence listed."""
    by_h = {(e.sheet, e.handle): e for e in ents}
    box = inflate(region(by_h, q.anchors), q.margin)
    anchors = set(q.anchors)
    out = []
    for sheet in (q.sheets or plan_sheets):
        f = Finding(q.qid, sheet, 0)
        for e in ents:
            if e.sheet != sheet or not intersects(e.box, box) or (e.sheet, e.handle) in anchors:
                continue
            f.searched += 1
            dim = q.dims_settle and e.kind == "DIMENSION" and contains(box, e.box)
            shape = e.kind in q.shapes_settle and max(e.box[2] - e.box[0], e.box[3] - e.box[1]) >= q.min_shape
            if _matches(e, q.evidence) or dim or shape:
                f.hits.append((e.handle, e.kind, e.text if e.kind != "DIMENSION" else round(e.value or 0.0, 3)))
            elif _matches(e, q.context):
                f.context.append((e.handle, e.kind, e.text))
            elif e.kind == "DIMENSION" and q.dims_settle:
                f.context.append((e.handle, "DIMENSION passing through", round(e.value or 0.0, 3)))
        out.append(f)
    return out


def global_hits(ents, pats, sheets=None):
    """Every TEXT / TAG on the named sheets (all when None) that matches a pattern: the whole-sheet search."""
    return [(e.sheet, e.handle, e.kind, e.text[:40]) for e in ents
            if (sheets is None or e.sheet in sheets) and _matches(e, pats)]


def verdict(findings):
    """FOUND when any searched sheet prints the evidence; MISSING otherwise. Never a value by default."""
    hits = [(f.sheet,) + h for f in findings for h in f.hits]
    return {"verdict": "FOUND" if hits else "MISSING", "hits": hits,
            "sheets_searched": [(f.sheet, f.searched) for f in findings]}


# ---- G1: which ground slab adjoins a column on a ground-beam line (the column / neck boundary) -------------------
def crossings(p, q, segments):
    """Number of segments crossed by the open segment p -> q (proper intersections only)."""
    def orient(a, b, c):
        return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
    n = 0
    for a, b in segments:
        d1, d2 = orient(p, q, a), orient(p, q, b)
        d3, d4 = orient(a, b, p), orient(a, b, q)
        if d1 * d2 < 0 and d3 * d4 < 0:
            n += 1
    return n


def adjoining_levels(centre, marks, beam_edges, radius, own_band_edges=1):
    """Level marks in the bays that touch the column: within `radius` and reached from the column centre by crossing at
    most `own_band_edges` ground-beam edge lines (the column's own band). marks = [(handle, value, (x, y))]."""
    out = []
    for h, v, xy in marks:
        if math.dist(centre, xy) > radius:
            continue
        if crossings(centre, xy, beam_edges) <= own_band_edges:
            out.append((h, v, round(xy[0] - centre[0], 3), round(xy[1] - centre[1], 3)))
    return out


def segments(ents, sheet, kinds=("LINE", "LWPOLYLINE")):
    """Every drawn straight segment on a sheet (the plan's walls, steps, door leaves, outlines)."""
    out = []
    for e in ents:
        if e.sheet == sheet and e.kind in kinds:
            out.extend(zip(e.pts, e.pts[1:]))
    return out


def same_space_levels(probes, marks, drawn, radius):
    """Level marks printed in the same floor space as a probe point: reached by a straight sight line that crosses no
    drawn line of the plan (no wall, step, door or outline between them), within `radius`. A bay that prints no mark
    of its own takes the mark of the space it is open to; nothing else is inferred."""
    out = []
    for name, p in probes:
        for h, v, xy in marks:
            if math.dist(p, xy) <= radius and crossings(p, xy, drawn) == 0:
                out.append((h, v, name))
    return out


def settle_column_base(adjoining, exterior_levels, build_up):
    """The GF column base (= neck top = ground-beam top) where a column sits on a ground-beam line.

    adjoining: [(handle, FFL, dx, dy)] from `adjoining_levels`; exterior_levels: finished ground levels that are not a
    building ground slab (drawing-confirmed per project); build_up: FFL - slab top (drawing-confirmed per project).
    One indoor FFL -> SETTLED (FFL - build_up); two different indoor FFL -> UNRESOLVED (the boundary is the designer's);
    none -> MISSING. The drawing settles only what it prints: never the higher, lower or nearer level by preference."""
    if build_up is None:
        return {"status": "MISSING", "reason": "floor build-up not drawing-confirmed", "base": None}
    indoor = sorted({round(v, 3) for _, v, _, _ in adjoining if round(v, 3) not in {round(x, 3) for x in exterior_levels}})
    exterior = sorted({round(v, 3) for _, v, _, _ in adjoining} - set(indoor))
    if not indoor:
        return {"status": "MISSING", "reason": "no building floor level printed beside the column", "base": None,
                "exterior": exterior}
    if len(indoor) > 1:
        return {"status": "UNRESOLVED", "reason": "two building floor levels meet at the column", "base": None,
                "readings": [round(v - build_up, 3) for v in indoor], "exterior": exterior}
    return {"status": "SETTLED", "base": round(indoor[0] - build_up, 3), "indoor_ffl": indoor[0], "exterior": exterior}


# ---- DXF layer ---------------------------------------------------------------------------------------------------
def _text_of(e):
    t = e.dxftype()
    if t == "MTEXT":
        return e.plain_text()
    if t in ("TEXT", "ATTRIB", "ATTDEF"):
        return e.dxf.text
    return ""


def _flatten(msp, sheet_of, scale):
    """Ents in metres; INSERT blocks that carry texts become one TAG ('T 16'); returns [Ent]."""
    from ezdxf import bbox
    out = []
    for e in msp:
        t = e.dxftype()
        if not e.dxf.is_supported("layer"):    # RTEXT kept as raw tags: plot / date stamp fields only (T-287 read)
            continue
        try:
            b = bbox.extents([e], fast=True)
        except Exception:      # noqa: BLE001 (a proxy / unsupported entity carries no searchable content)
            continue
        if not b.has_data:
            continue
        box = (b.extmin.x, b.extmin.y, b.extmax.x, b.extmax.y)
        sh = sheet_of(box)
        if sh is None:
            continue
        sheet, (dx, dy) = sh
        mbox = ((box[0] + dx) / scale, (box[1] + dy) / scale, (box[2] + dx) / scale, (box[3] + dy) / scale)
        layer = e.dxf.layer
        if t in ("TEXT", "MTEXT"):
            out.append(Ent(sheet, "TEXT", layer, e.dxf.handle, mbox, _text_of(e).strip()))
        elif t == "INSERT":
            texts = [_text_of(v).strip() for v in e.virtual_entities() if v.dxftype() in ("TEXT", "MTEXT")]
            texts += [a.dxf.text.strip() for a in e.attribs]
            texts = [x for x in texts if x]
            out.append(Ent(sheet, "TAG" if texts else "INSERT", layer, e.dxf.handle, mbox, " ".join(texts)))
        elif t == "DIMENSION":
            try:
                v = e.get_measurement()
                v = float(v) / scale if not hasattr(v, "x") else None
            except Exception:  # noqa: BLE001
                v = None
            out.append(Ent(sheet, "DIMENSION", layer, e.dxf.handle, mbox, e.dxf.get("text", "") or "", v))
        elif t == "LINE":
            a, b = e.dxf.start, e.dxf.end
            out.append(Ent(sheet, t, layer, e.dxf.handle, mbox, pts=(((a.x + dx) / scale, (a.y + dy) / scale),
                                                                     ((b.x + dx) / scale, (b.y + dy) / scale))))
        elif t == "LWPOLYLINE":
            v = [((p[0] + dx) / scale, (p[1] + dy) / scale) for p in e.get_points()]
            if e.closed and v:
                v.append(v[0])
            out.append(Ent(sheet, t, layer, e.dxf.handle, mbox, pts=tuple(v)))
        else:
            out.append(Ent(sheet, t, layer, e.dxf.handle, mbox))
    return out


def register_by_marks(a_marks, b_marks, min_votes):
    """Translation b -> a from level marks with the same text: the offset most pairs agree on (rounded to 1 mm).
    Returns ((dx, dy), votes, n_a) or raises when fewer than min_votes pairs agree (never a guessed offset)."""
    votes = Counter()
    for ta, xa, ya in a_marks:
        for tb, xb, yb in b_marks:
            if ta == tb:
                votes[(round(xa - xb), round(ya - yb))] += 1
    if not votes:
        raise ValueError("no common level mark: the sheets cannot be registered")
    (off, n), = votes.most_common(1)
    if n < min_votes:
        raise ValueError(f"registration too weak: {n} agreeing marks < {min_votes}")
    return off, n, len(a_marks)
