"""STRUCTURAL RECONCILIATION - whole-building ownership, version precedence and lane-safe totals (generic).

Nothing here measures a drawing. Every function takes records a caller built from frozen stage outputs and says what
follows: which version of a family's quantity is authoritative, whether every component has exactly one owner,
whether a total contains only eligible lanes, and simple closed-form geometry used to recompute a quantity on an
independent path.

Geometry
    polygon_area(points)                 shoelace area of a simple polygon (any orientation), in the input units^2
    polygon_area_with_holes(outer, holes) outer area minus the hole areas
    rect_overlap(a, b)                   overlap area of two axis-aligned boxes (x0, y0, x1, y1)
    prism(l, w, d)                       l x w x d (refuses negative or missing dimensions)

Versions
    resolve_chain(chain)                 chain = [(version_id, kind, quantity)] in date order: kind BASELINE starts it,
                                         DELTA / CORRECTION add their signed quantity, STATE_ONLY / NO_CHANGE / QA_ONLY
                                         add nothing, SUPERSEDING replaces the running value. Returns the
                                         authoritative value, the version that holds it and the superseded versions.
                                         A correction may never be positive (an erratum never adds steel).

Ownership and totals
    assert_single_owner(components)      every component id appears once and has one owning family
    eligible_total(rows, value_key, lane_key, eligible_lanes)
                                         sum over eligible lanes only; a non-eligible row that carries a value is
                                         reported, never added
    group_totals(rows, keys, value_key, lane_key, eligible_lanes)

Stdlib only. No project data.
"""

from __future__ import annotations

import math
from collections import defaultdict

TOL = 1e-9
BASELINE, DELTA, CORRECTION, SUPERSEDING = "BASELINE", "DELTA", "CORRECTION", "SUPERSEDING"
STATE_ONLY, NO_CHANGE, QA_ONLY = "STATE_ONLY", "NO_CHANGE", "QA_ONLY"
KINDS = (BASELINE, DELTA, CORRECTION, SUPERSEDING, STATE_ONLY, NO_CHANGE, QA_ONLY)


class ReconciliationError(ValueError):
    pass


# ------------------------------------------------------------------ geometry
def polygon_area(points):
    pts = [tuple(map(float, p[:2])) for p in points]
    if len(pts) < 3:
        raise ReconciliationError("a polygon needs at least three vertices")
    if pts[0] == pts[-1]:
        pts = pts[:-1]
    s = 0.0
    for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]):
        s += x0 * y1 - x1 * y0
    return abs(s) / 2.0


def polygon_area_with_holes(outer, holes=()):
    a = polygon_area(outer)
    h = math.fsum(polygon_area(x) for x in holes)
    if h > a + TOL:
        raise ReconciliationError("holes larger than the outline")
    return a - h


def rect_overlap(a, b):
    ax0, ay0, ax1, ay1 = (min(a[0], a[2]), min(a[1], a[3]), max(a[0], a[2]), max(a[1], a[3]))
    bx0, by0, bx1, by1 = (min(b[0], b[2]), min(b[1], b[3]), max(b[0], b[2]), max(b[1], b[3]))
    w = min(ax1, bx1) - max(ax0, bx0)
    h = min(ay1, by1) - max(ay0, by0)
    return w * h if (w > 0 and h > 0) else 0.0


def prism(l, w, d):
    vals = (l, w, d)
    if any(v is None for v in vals):
        raise ReconciliationError("a missing dimension is not zero")
    if any(float(v) < 0 for v in vals):
        raise ReconciliationError("negative dimension")
    return float(l) * float(w) * float(d)


# ------------------------------------------------------------------ versions
def resolve_chain(chain):
    if not chain or chain[0][1] not in (BASELINE, SUPERSEDING):
        raise ReconciliationError("a version chain starts with a BASELINE")
    value, holder, history, superseded = None, None, [], []
    for vid, kind, q in chain:
        if kind not in KINDS:
            raise ReconciliationError(f"{vid}: unknown version kind {kind!r}")
        if kind in (BASELINE, SUPERSEDING):
            if holder is not None:
                superseded.append(holder)
            value, holder = float(q), vid
        elif kind == DELTA:
            if float(q) < -TOL:
                raise ReconciliationError(f"{vid}: a delta never subtracts (record a CORRECTION)")
            superseded.append(holder)
            value, holder = value + float(q), vid
        elif kind == CORRECTION:
            if float(q) > TOL:
                raise ReconciliationError(f"{vid}: a correction never adds")
            superseded.append(holder)
            value, holder = value + float(q), vid
        else:                                                    # STATE_ONLY / NO_CHANGE / QA_ONLY
            if q not in (None, 0, 0.0):
                raise ReconciliationError(f"{vid}: a {kind} layer carries no quantity")
        history.append({"version": vid, "kind": kind, "quantity": q, "running": value})
    return {"authoritative": value, "holder": holder, "superseded": [s for s in superseded if s is not None],
            "history": history}


# ------------------------------------------------------------------ ownership / totals
def assert_single_owner(components, id_key="COMPONENT_ID", owner_key="OWNER_FAMILY"):
    seen = {}
    for c in components:
        cid, own = c.get(id_key), c.get(owner_key)
        if not cid:
            raise ReconciliationError("a component without an id")
        if not own:
            raise ReconciliationError(f"{cid}: no owning family")
        if cid in seen:
            raise ReconciliationError(f"{cid}: listed twice ({seen[cid]} / {own})")
        seen[cid] = own
    return len(seen)


def eligible_total(rows, value_key, lane_key, eligible_lanes):
    total, leaks = 0.0, []
    for r in rows:
        v = r.get(value_key)
        if v in (None, ""):
            continue
        if r.get(lane_key) in eligible_lanes:
            total += float(v)
        elif abs(float(v)) > TOL:
            leaks.append(r)
    return {"total": total, "non_eligible_rows_with_value": len(leaks)}


def group_totals(rows, keys, value_key, lane_key, eligible_lanes):
    out = defaultdict(float)
    for r in rows:
        v = r.get(value_key)
        if v in (None, "") or r.get(lane_key) not in eligible_lanes:
            continue
        out[tuple(r.get(k) for k in keys)] += float(v)
    return dict(out)
