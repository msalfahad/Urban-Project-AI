"""Stable canonical ids (PA05 §2).

An id is a short hash of stable evidence: the kind, the source hash, the
sheet / view identity, the layer, a geometry fingerprint quantised to a
tolerance, and the parent id.  Never an array index, a loop order, a
flood-fill number, an AI sequence or a pixel position.

Geometry ids and semantic identity are separate: reclassifying a feature
changes nothing here.
"""

from __future__ import annotations

import hashlib
import math

KINDS = ("SHEET", "VIEW", "CAD_ENTITY", "ATOMIC_FACE", "WALL_FACE", "OPENING_SITE", "COLUMN", "BEAM", "SPACE_SEED",
         "TOPOLOGY_REGION", "PHYSICAL_SPACE", "FUNCTIONAL_ZONE", "TRADE_ZONE", "DIMENSION", "DIMENSION_CHAIN", "ANCHOR", "CLOSURE")
PREFIX = {"SHEET": "SH", "VIEW": "VW", "CAD_ENTITY": "EN", "ATOMIC_FACE": "AF", "WALL_FACE": "WF", "OPENING_SITE": "OS", "COLUMN": "CO", "BEAM": "BM",
          "SPACE_SEED": "SS", "TOPOLOGY_REGION": "TR", "PHYSICAL_SPACE": "PS", "FUNCTIONAL_ZONE": "FZ", "TRADE_ZONE": "TZ", "DIMENSION": "DM",
          "DIMENSION_CHAIN": "DC", "ANCHOR": "AN", "CLOSURE": "CL"}
DEFAULT_TOL_MM = 5.0


def q(v, tol=DEFAULT_TOL_MM):
    """Quantise a coordinate to the tolerance grid; None stays None."""
    if v is None:
        return None
    return int(math.floor(float(v) / tol + 0.5))


def fingerprint(kind, *parts, tol=DEFAULT_TOL_MM):
    """Deterministic geometry fingerprint from numbers / strings.  Numbers are
    quantised, sequences are canonicalised (sorted where order is not
    meaningful, see callers)."""
    toks = [kind]
    for p in parts:
        if p is None:
            toks.append("~")
        elif isinstance(p, bool):
            toks.append("T" if p else "F")
        elif isinstance(p, (int, float)):
            toks.append(str(q(p, tol)))
        elif isinstance(p, (list, tuple)):
            toks.append("[" + ",".join(str(q(x, tol)) if isinstance(x, (int, float)) and not isinstance(x, bool) else str(x) for x in p) + "]")
        else:
            toks.append(str(p))
    return "|".join(toks)


def make_id(kind, *parts, tol=DEFAULT_TOL_MM, length=12):
    if kind not in KINDS:
        raise ValueError(f"unknown id kind {kind}")
    h = hashlib.sha256(fingerprint(kind, *parts, tol=tol).encode()).hexdigest()[:length]
    return f"{PREFIX[kind]}-{h}"


# ---- kind-specific constructors (evidence fields are explicit so that callers cannot slip an index in) ----
def sheet_id(source_hash, page_index_or_name):
    """A sheet is identified by its source document hash and its page / sheet name (a document fact, not an order)."""
    return make_id("SHEET", source_hash, str(page_index_or_name))


def view_id(sheet, role, bbox_mm):
    """A view inside a sheet: role plus its quantised bounding box (100 mm grid: views move only when the drawing moves)."""
    x0, y0, x1, y1 = bbox_mm
    return make_id("VIEW", sheet, role, [x0, y0, x1, y1], tol=100.0)


def entity_id(view, layer, kind, geometry, handle=None):
    """Geometry fingerprint of a segment (both endpoints, canonically ordered) or an arc / circle
    (centre, radius, angles).  The DWG handle is evidence when present but the id survives a
    handle change if the geometry is identical."""
    if kind == "SEGMENT":
        (ax, ay), (bx, by) = geometry
        pts = sorted([(q(ax), q(ay)), (q(bx), q(by))])
        g = [pts[0][0], pts[0][1], pts[1][0], pts[1][1]]
        return make_id("CAD_ENTITY", view, layer, kind, [x * DEFAULT_TOL_MM for x in g])
    cx, cy, r, a0, a1 = geometry
    return make_id("CAD_ENTITY", view, layer, kind, [cx, cy, r], round(a0 or 0.0, 3), round(a1 or 0.0, 3))


def face_id(view, entity, side_normal_sign):
    """An atomic face is one side of one entity."""
    return make_id("ATOMIC_FACE", view, entity, "+" if side_normal_sign >= 0 else "-")


def opening_site_id(view, wall_a_entity, wall_b_entity, gap_mid_mm):
    ids = sorted([wall_a_entity, wall_b_entity])
    return make_id("OPENING_SITE", view, ids[0], ids[1], [gap_mid_mm[0], gap_mid_mm[1]], tol=50.0)


def region_id(view, anchor_mm, area_m2):
    """A topology region is identified by an interior anchor (quantised to 250 mm) and its area bucket (0.5 m2)."""
    return make_id("TOPOLOGY_REGION", view, [anchor_mm[0], anchor_mm[1]], f"A{int(area_m2 / 0.5)}", tol=250.0)


def space_id(view, anchor_mm, bounding_entities):
    """A physical space: interior anchor plus the sorted set of bounding entity ids (order-free)."""
    return make_id("PHYSICAL_SPACE", view, [anchor_mm[0], anchor_mm[1]], ",".join(sorted(bounding_entities)), tol=250.0)


def dimension_id(view, origins_mm, value_mm):
    (ax, ay), (bx, by) = origins_mm
    pts = sorted([(q(ax), q(ay)), (q(bx), q(by))])
    return make_id("DIMENSION", view, [pts[0][0] * DEFAULT_TOL_MM, pts[0][1] * DEFAULT_TOL_MM, pts[1][0] * DEFAULT_TOL_MM, pts[1][1] * DEFAULT_TOL_MM], round(value_mm, 1))


def chain_id(view, axis, line_coord_mm, member_ids):
    return make_id("DIMENSION_CHAIN", view, axis, line_coord_mm, ",".join(sorted(member_ids)))


def anchor_id(view, anchor_type, text, position_mm):
    return make_id("ANCHOR", view, anchor_type, text, [position_mm[0], position_mm[1]], tol=50.0)


def closure_id(view, site_or_edge, trade):
    return make_id("CLOSURE", view, site_or_edge, trade)


def column_id(view, centre_mm, size_mm):
    return make_id("COLUMN", view, [centre_mm[0], centre_mm[1]], [size_mm[0], size_mm[1]], tol=25.0)


def beam_id(view, label, from_mm, to_mm):
    pts = sorted([(q(from_mm[0], 50), q(from_mm[1], 50)), (q(to_mm[0], 50), q(to_mm[1], 50))])
    return make_id("BEAM", view, label, [pts[0][0] * 50, pts[0][1] * 50, pts[1][0] * 50, pts[1][1] * 50])
