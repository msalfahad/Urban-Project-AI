"""R8.0 DIGEST CONTRACTS — reference definition (test side).

Two digests answer two different questions and must never be confused:

SOURCE_REPRESENTATION_DIGEST  (prefix URBAN-SRD-1)
    "What exact normalised representation did this decoder route produce?"
    Input: one route's decode, native units, nothing realised. Covers entity
    type, handle, owner, layer name, raw local geometry, INSERT transform
    fields, extrusion, block base points and xref flags, grid fields,
    attributes, text and dimension fields.

REALISED_GEOMETRY_DIGEST      (prefix URBAN-RGD-1)
    "What physical geometry does Urban say exists after every valid
    transformation?"  Input: realised plan primitives in MILLIMETRES after
    OCS, base point, insertion, nesting, rotation, scale, reflection, MINSERT
    placement and units. Covers geometry only: no handle, no type, no layer,
    no traversal direction. A curve is its point set: centre, radius, the
    two end points (sorted) and the mid-sweep point, so the same physical
    arc written CCW, CW, as an ARC or as a bulge digests identically, and an
    arc on the other side of its chord does not.

CANONICAL NUMBERS (fixed BEFORE any real-project comparison)
    realised lengths : millimetres, quantum 1e-6 mm (one nanometre)
    source values    : native units / radians, quantum 1e-9
    rounding         : ROUND_HALF_EVEN on Decimal(repr(float)); -0 -> 0
    Why these quanta: float64 carries ~15.9 significant digits, so at
    building extents up to 1e7 mm the representation noise is ~1e-9 mm; one
    nanometre is 1000x above that noise and 1000x below the finest drafting
    precision (1e-3 mm). Neither value was chosen by comparing any project,
    and none may be changed to make a project match.
    A digest is an IDENTITY check. Tolerance belongs to reconciliation, not
    here: two realisations that differ by less than the quantum but straddle
    a rounding boundary are reconciled by field tolerance classes, never by
    loosening the digest.
"""

from __future__ import annotations

import hashlib
import json
import math
from decimal import ROUND_HALF_EVEN, Decimal

REALISED_QUANTUM = Decimal("0.000001")
SOURCE_QUANTUM = Decimal("0.000000001")
SRD_PREFIX = "URBAN-SRD-1"
RGD_PREFIX = "URBAN-RGD-1"

SOURCE_FIELDS = ("start", "end", "center", "radius", "start_angle", "end_angle", "points",
                 "bulges", "flag", "elevation", "ins_pt", "scale", "rotation", "extrusion",
                 "base_pt", "num_cols", "num_rows", "col_spacing", "row_spacing",
                 "blkisxref", "xrefoverlaid", "xref_pname", "is_xref_resolved", "loaded_bit",
                 "text", "text_value", "tag", "height", "text_height", "xline1_pt", "xline2_pt",
                 "def_pt", "act_measurement", "user_text", "dim_rotation", "sm_axis", "axis_ratio")


def q(value, quantum):
    d = Decimal(repr(float(value))).quantize(quantum, rounding=ROUND_HALF_EVEN)
    if d == 0:
        d = abs(d)
    return format(d, "f")


def _canon_source(v):
    if isinstance(v, bool) or v is None or isinstance(v, str):
        return v
    if isinstance(v, int):
        return v
    if isinstance(v, float):
        if not math.isfinite(v):
            return f"NONFINITE:{v!r}"
        return q(v, SOURCE_QUANTUM)
    if isinstance(v, (list, tuple)):
        return [_canon_source(x) for x in v]
    if isinstance(v, dict):
        return {k: _canon_source(x) for k, x in sorted(v.items())}
    return repr(v)


def _abs(h):
    return h[-1] if isinstance(h, list) and h else None


def source_representation_records(decode, route_id):
    objs = decode.get("OBJECTS", [])
    layers = {_abs(o.get("handle")): o.get("name") for o in objs if o.get("object") == "LAYER"}
    blocks = {_abs(o.get("handle")): o.get("name") for o in objs if o.get("object") == "BLOCK_HEADER"}
    recs = []
    for o in objs:
        if o.get("object") == "BLOCK_HEADER":
            rec = {"k": "BLOCK_HEADER", "name": o.get("name")}
        elif "entity" in o:
            rec = {"k": "ENTITY", "type": o.get("type"), "entity": o.get("entity"),
                   "handle": _abs(o.get("handle")), "owner": blocks.get(_abs(o.get("ownerhandle"))),
                   "layer": layers.get(_abs(o.get("layer")))}
            if "block_header" in o:
                rec["block"] = blocks.get(_abs(o.get("block_header")))
        else:
            continue
        for f in SOURCE_FIELDS:
            if f in o:
                rec[f] = _canon_source(o[f])
        recs.append(rec)
    hdr = decode.get("HEADER", {})
    recs.append({"k": "HEADER", "INSUNITS": hdr.get("INSUNITS"),
                 "DIMLFAC": _canon_source(float(hdr.get("DIMLFAC", 1.0)))})
    return route_id, recs


def source_representation_digest(decode, route_id):
    route, recs = source_representation_records(decode, route_id)
    lines = sorted(json.dumps(r, sort_keys=True, separators=(",", ":"), ensure_ascii=True) for r in recs)
    return hashlib.sha256("\n".join([SRD_PREFIX, str(route)] + lines).encode()).hexdigest()


# --------------------------------------------------------------- realised

def _p(pt, unit_to_mm):
    return [q(pt[0] * unit_to_mm, REALISED_QUANTUM), q(pt[1] * unit_to_mm, REALISED_QUANTUM)]


def realised_records(realised, unit_to_mm):
    """`realised` = {'arcs': [...], 'bulges': [...], 'segments': [...]} in the
    physical form used by geometry.py. unit_to_mm is REQUIRED: a realised
    digest without a unit is not a physical statement."""
    if unit_to_mm is None or not (unit_to_mm > 0):
        raise ValueError("REALISED_GEOMETRY_DIGEST requires an established unit_to_mm")
    recs = []
    for a, b in realised.get("segments", []):
        recs.append({"k": "SEGMENT", "p": sorted([_p(a, unit_to_mm), _p(b, unit_to_mm)])})
    for arc in realised.get("arcs", []):
        c = arc["CENTER"]
        r = arc.get("RADIUS")
        if r is None:
            r = math.hypot(arc["P0"][0] - c[0], arc["P0"][1] - c[1])
        recs.append({"k": "CIRCULAR_ARC", "c": _p(c, unit_to_mm), "r": q(r * unit_to_mm, REALISED_QUANTUM),
                     "e": sorted([_p(arc["P0"], unit_to_mm), _p(arc["P1"], unit_to_mm)]),
                     "m": _p(arc["PM"], unit_to_mm)})
    for bl in realised.get("bulges", []):
        c = bl["CENTER"]
        r = math.hypot(bl["VERTEX_A"][0] - c[0], bl["VERTEX_A"][1] - c[1])
        recs.append({"k": "CIRCULAR_ARC", "c": _p(c, unit_to_mm), "r": q(r * unit_to_mm, REALISED_QUANTUM),
                     "e": sorted([_p(bl["VERTEX_A"], unit_to_mm), _p(bl["VERTEX_B"], unit_to_mm)]),
                     "m": _p(bl["ARC_MIDPOINT"], unit_to_mm)})
    return recs


def realised_geometry_digest(realised, unit_to_mm):
    lines = sorted(json.dumps(r, sort_keys=True, separators=(",", ":")) for r in realised_records(realised, unit_to_mm))
    return hashlib.sha256("\n".join([RGD_PREFIX] + lines).encode()).hexdigest()


def as_realised(obj):
    """Accept a reference-realiser `Realised` or a plain dict."""
    if isinstance(obj, dict):
        return obj
    return {"arcs": obj.arcs, "bulges": obj.bulges, "segments": obj.segments}
