"""SHAFT GEOMETRY - lift shafts and pits: wall rings, wall pieces, openings, storeys, tie-beam triggers (generic).

Nothing here chooses a dimension. Every function takes the outlines, thicknesses, levels and rates it is given and
says what follows from them; whether each input has authority is the caller's record.

Regions are unions of axis-parallel rectangles (x0, y0, x1, y1) in mm, which covers rectangular and orthogonal
(L-, T-, U-shaped) shafts exactly. Areas are exact (coordinate compression), never sampled.

    region_area(adds, subs=())
        area of (union of adds) minus (union of subs).
    intersect(a, b)
        the common rectangle of two rectangles, or None.
    offset(rects, t)
        each rectangle grown by t on every side: the outer outline of walls of thickness t around an orthogonal
        void (the Minkowski sum with a square is exact for orthogonal outlines).
    shaft(inner, t)
        a shaft from its inside clear outline (rectangles) and wall thickness t:
          INSIDE_CLEAR_AREA, GROSS_OUTER_AREA, WALL_RING_AREA (outer minus inner, every corner once),
          INSIDE_PERIMETER, OUTER_PERIMETER, CENTRELINE_PERIMETER (the mean of the two faces).
    wall_pieces(inner_rect, t, members=())
        the ring of a rectangular shaft split into four side bands (south and north bands run the full outer width,
        so every corner is in exactly one band), each cut by the members that occupy the ring (columns): the net
        pieces with their side, length along the wall, footprint and inner / outer face lengths, and each member's
        overlap with the ring. A member is deducted once even where it spans two bands. A member that covers only
        part of the wall thickness, or two members that overlap each other, are refused: neither is a clean cut.
    split_opening(pieces, side, a, b)
        an opening between a and b along one side (a door): its width inside the net pieces of that side and the
        pieces that remain; any part of the opening that falls on a member is reported, not deducted.
    plan_overlap(pieces, rects)
        the plan area of the net pieces standing on the given rectangles (a footing) and the area off them.
    vertical_segments(bottom, top, cuts)
        the parts of [bottom, top] not taken by the given level bands (ring beams, slabs owned elsewhere).
    storey_heights(levels)
        consecutive level differences {(lower, upper): height}.
    tie_beam_trigger(levels, threshold, offset, measure, slab=None, finish=None)
        which storeys exceed a height threshold under a stated measure of storey height:
          FLOOR_TO_FLOOR       upper level - lower level
          CLEAR_TO_SLAB_SOFFIT floor to floor - slab thickness - finish (both needed; else NOT_ESTABLISHED)
        and the required elevation (lower level + offset) where triggered.
    pit(inner, depth=None, floor_level=None)
        pit void (m3): inside area (mm2) x depth (mm) when the depth is given; NOT_ESTABLISHED otherwise.
    wall_volume(net_footprint_mm2, bottom, top)
        footprint x (top - bottom) in m3; None (not established) when either level is missing. A wall that stands
        on a footing starts at the footing top, so the base-to-wall interface is never counted twice.
    opening_volume(width, height, t)
        an opening through a wall (m3), None when the height is not given.
    group_representations(items, tol=1.0)
        items (id, view, rect) already in one frame: the same outline drawn on several views is one physical
        object. Returns groups of ids whose rectangles agree within tol; one view never contributes two members
        of a group.
    ownership_state(owner=None, measured=False, derived=False, project_basis=False, blocked=None, conflict=None)
        one of the six component states: SOURCE_CONFLICT first, then an existing owner (ALREADY_OWNED_AND_MEASURED
        only when that owner carries a quantity, OWNED_BUT_UNMEASURED otherwise), then BLOCKED_UNQUANTIFIED, then
        NEW_SOURCE_DERIVED / NEW_PROJECT_BASIS_QTO. An owner is not a measurement; with nothing established the
        state is BLOCKED_UNQUANTIFIED.
    rate_count(rate_per_m, length)  ceil(rate x length) bars along a length.
    rate_length(rate_per_m, distribution, bar_length)  equivalent length (m) of a rate spread over a distribution.

Stdlib only. No project data.
"""

from __future__ import annotations

import math

TOL = 1e-9
FLOOR_TO_FLOOR, CLEAR_TO_SLAB_SOFFIT = "FLOOR_TO_FLOOR", "CLEAR_TO_SLAB_SOFFIT"
TRIGGERED, NOT_TRIGGERED, NOT_ESTABLISHED = "TRIGGERED", "NOT_TRIGGERED", "NOT_ESTABLISHED"
ALREADY_OWNED_AND_MEASURED, OWNED_BUT_UNMEASURED = "ALREADY_OWNED_AND_MEASURED", "OWNED_BUT_UNMEASURED"
NEW_SOURCE_DERIVED, NEW_PROJECT_BASIS_QTO = "NEW_SOURCE_DERIVED", "NEW_PROJECT_BASIS_QTO"
BLOCKED_UNQUANTIFIED, SOURCE_CONFLICT = "BLOCKED_UNQUANTIFIED", "SOURCE_CONFLICT"


class ShaftGeometryError(ValueError):
    pass


def _check(r):
    x0, y0, x1, y1 = r
    if x1 - x0 <= TOL or y1 - y0 <= TOL:
        raise ShaftGeometryError(f"empty rectangle {r}")
    return r


def _covered(cell, rects):
    cx, cy = cell
    return any(r[0] - TOL <= cx <= r[2] + TOL and r[1] - TOL <= cy <= r[3] + TOL for r in rects)


def region_area(adds, subs=()):
    adds = [_check(tuple(r)) for r in adds]
    subs = [_check(tuple(r)) for r in subs]
    if not adds:
        return 0.0
    xs = sorted({v for r in adds + subs for v in (r[0], r[2])})
    ys = sorted({v for r in adds + subs for v in (r[1], r[3])})
    area = 0.0
    for i in range(len(xs) - 1):
        for j in range(len(ys) - 1):
            c = ((xs[i] + xs[i + 1]) / 2, (ys[j] + ys[j + 1]) / 2)
            if _covered(c, adds) and not _covered(c, subs):
                area += (xs[i + 1] - xs[i]) * (ys[j + 1] - ys[j])
    return area


def intersect(a, b):
    x0, y0, x1, y1 = max(a[0], b[0]), max(a[1], b[1]), min(a[2], b[2]), min(a[3], b[3])
    return (x0, y0, x1, y1) if x1 - x0 > TOL and y1 - y0 > TOL else None


def offset(rects, t):
    if t <= 0:
        raise ShaftGeometryError("wall thickness must be positive")
    return [(r[0] - t, r[1] - t, r[2] + t, r[3] + t) for r in rects]


def _perimeter(rects):
    """perimeter of a union of rectangles: edges of compressed cells that separate inside from outside."""
    xs = sorted({v for r in rects for v in (r[0], r[2])})
    ys = sorted({v for r in rects for v in (r[1], r[3])})
    inside = {}
    for i in range(len(xs) - 1):
        for j in range(len(ys) - 1):
            inside[(i, j)] = _covered(((xs[i] + xs[i + 1]) / 2, (ys[j] + ys[j + 1]) / 2), rects)
    p = 0.0
    for (i, j), v in inside.items():
        if not v:
            continue
        w, h = xs[i + 1] - xs[i], ys[j + 1] - ys[j]
        p += h * (not inside.get((i - 1, j), False)) + h * (not inside.get((i + 1, j), False))
        p += w * (not inside.get((i, j - 1), False)) + w * (not inside.get((i, j + 1), False))
    return p


def shaft(inner, t):
    inner = [_check(tuple(r)) for r in inner]
    outer = offset(inner, t)
    a_in, a_out = region_area(inner), region_area(outer)
    p_in, p_out = _perimeter(inner), _perimeter(outer)
    return {"inner": inner, "outer": outer, "INSIDE_CLEAR_AREA": a_in, "GROSS_OUTER_AREA": a_out,
            "WALL_RING_AREA": a_out - a_in, "INSIDE_PERIMETER": p_in, "OUTER_PERIMETER": p_out,
            "CENTRELINE_PERIMETER": (p_in + p_out) / 2.0, "thickness": t}


def _bands(inner_rect, t):
    x0, y0, x1, y1 = inner_rect
    X0, Y0, X1, Y1 = x0 - t, y0 - t, x1 + t, y1 + t
    # (band rectangle, axis along the wall, inner-face span along that axis)
    return {"S": ((X0, Y0, X1, y0), "x", (x0, x1)), "N": ((X0, y1, X1, Y1), "x", (x0, x1)),
            "W": ((X0, y0, x0, y1), "y", (y0, y1)), "E": ((x1, y0, X1, y1), "y", (y0, y1))}


def _piece(side, band, ax, inner_span, a, b):
    bx0, by0, bx1, by1 = band
    rect = (a, by0, b, by1) if ax == "x" else (bx0, a, bx1, b)
    depth = (by1 - by0) if ax == "x" else (bx1 - bx0)
    inner = max(0.0, min(b, inner_span[1]) - max(a, inner_span[0]))
    return {"side": side, "rect": rect, "from": a, "to": b, "length": b - a, "footprint": (b - a) * depth,
            "depth": depth, "inner_span": inner_span, "inner_face": inner, "outer_face": b - a}


def wall_pieces(inner_rect, t, members=()):
    inner_rect = _check(tuple(inner_rect))
    if t <= 0:
        raise ShaftGeometryError("wall thickness must be positive")
    x0, y0, x1, y1 = inner_rect
    ring_box = (x0 - t, y0 - t, x1 + t, y1 + t)
    members = [(mid, _check(tuple(r))) for mid, r in members]
    clipped = {mid: [c for c in (intersect(r, b[0]) for b in _bands(inner_rect, t).values()) if c]
               for mid, r in members}
    overlap = {mid: sum((c[2] - c[0]) * (c[3] - c[1]) for c in cs) for mid, cs in clipped.items()}
    all_cuts = [c for cs in clipped.values() for c in cs]
    if all_cuts and abs(region_area(all_cuts) - sum(overlap.values())) > 1e-6 * max(1.0, sum(overlap.values())):
        raise ShaftGeometryError("members overlap each other inside the wall ring")
    pieces = []
    for side, (band, ax, span) in _bands(inner_rect, t).items():
        bx0, by0, bx1, by1 = band
        cuts = [c for c in (intersect(r, band) for _, r in members) if c]
        for c in cuts:
            full = (c[1] <= by0 + TOL and c[3] >= by1 - TOL) if ax == "x" else (c[0] <= bx0 + TOL and c[2] >= bx1 - TOL)
            if not full:
                raise ShaftGeometryError(f"member covers part of the {side} wall thickness: not a clean cut")
        lo, hi = (bx0, bx1) if ax == "x" else (by0, by1)
        pos = lo
        for a, b in sorted(((c[0], c[2]) if ax == "x" else (c[1], c[3])) for c in cuts):
            if a > pos + TOL:
                pieces.append(_piece(side, band, ax, span, pos, a))
            pos = max(pos, b)
        if hi > pos + TOL:
            pieces.append(_piece(side, band, ax, span, pos, hi))
    ring = region_area([ring_box], [inner_rect])
    net = sum(p["footprint"] for p in pieces)
    if abs(net + sum(overlap.values()) - ring) > 1e-6 * max(ring, 1.0):
        raise ShaftGeometryError("wall pieces and member overlaps do not close to the ring")
    return {"pieces": pieces, "member_overlap": overlap, "ring_area": ring, "net_footprint": net,
            "inner": inner_rect, "outer": ring_box, "thickness": t}


def split_opening(pieces, side, a, b):
    if b - a <= TOL:
        raise ShaftGeometryError("opening must have positive width")
    width_in_wall, remaining = 0.0, []
    for p in pieces:
        lo, hi = max(a, p["from"]), min(b, p["to"])
        if p["side"] != side or hi - lo <= TOL:
            remaining.append(p)
            continue
        width_in_wall += hi - lo
        for s, e in ((p["from"], lo), (hi, p["to"])):
            if e - s > TOL:
                r = p["rect"]
                rect = (s, r[1], e, r[3]) if side in ("S", "N") else (r[0], s, r[2], e)
                span = p["inner_span"]
                remaining.append({"side": side, "rect": rect, "from": s, "to": e, "length": e - s,
                                  "footprint": (e - s) * p["depth"], "depth": p["depth"], "inner_span": span,
                                  "inner_face": max(0.0, min(e, span[1]) - max(s, span[0])), "outer_face": e - s})
    return {"width_in_wall": width_in_wall, "width_not_in_wall": (b - a) - width_in_wall, "pieces": remaining}


def plan_overlap(pieces, rects):
    rects = [_check(tuple(r)) for r in rects]
    on = sum(region_area([p["rect"]]) - region_area([p["rect"]], rects) for p in pieces)
    total = sum(p["footprint"] for p in pieces)
    return {"on": on, "off": total - on, "total": total}


def vertical_segments(bottom, top, cuts=()):
    if bottom is None or top is None:
        return None
    if top <= bottom:
        raise ShaftGeometryError("top must be above bottom")
    segs, pos = [], bottom
    for a, b in sorted((max(bottom, a), min(top, b)) for a, b in cuts if min(top, b) - max(bottom, a) > TOL):
        if a > pos + TOL:
            segs.append((pos, a))
        pos = max(pos, b)
    if top > pos + TOL:
        segs.append((pos, top))
    return segs


def storey_heights(levels):
    lv = list(levels)
    if len(lv) < 2 or any(b <= a for a, b in zip(lv, lv[1:])):
        raise ShaftGeometryError("levels must rise")
    return {(a, b): b - a for a, b in zip(lv, lv[1:])}


def tie_beam_trigger(levels, threshold, offset_m, measure=FLOOR_TO_FLOOR, slab=None, finish=None):
    rows = []
    for (a, b), h in storey_heights(levels).items():
        if measure == FLOOR_TO_FLOOR:
            hh = h
        elif measure == CLEAR_TO_SLAB_SOFFIT:
            hh = None if (slab is None or finish is None) else h - slab - finish
        else:
            raise ShaftGeometryError(f"unknown measure {measure}")
        if hh is None:
            state = NOT_ESTABLISHED
        else:
            state = TRIGGERED if hh > threshold + TOL else NOT_TRIGGERED
        rows.append({"lower": a, "upper": b, "measure": measure, "height": hh, "state": state,
                     "elevation": (a + offset_m) if state == TRIGGERED else None})
    return rows


def pit(inner, depth=None, floor_level=None):
    a = region_area(inner)
    if depth is None:
        return {"INSIDE_CLEAR_AREA": a, "VOID_VOLUME": None, "state": NOT_ESTABLISHED, "pit_bottom": None}
    if depth <= 0:
        raise ShaftGeometryError("pit depth must be positive")
    return {"INSIDE_CLEAR_AREA": a, "VOID_VOLUME": a * depth / 1e9, "state": "ESTABLISHED",
            "pit_bottom": None if floor_level is None else floor_level - depth / 1000.0}


def wall_volume(net_footprint_mm2, bottom, top):
    if bottom is None or top is None:
        return None
    if top <= bottom:
        raise ShaftGeometryError("wall top must be above its bottom")
    return net_footprint_mm2 / 1e6 * (top - bottom)


def opening_volume(width, height, t):
    if width <= 0 or t <= 0:
        raise ShaftGeometryError("opening width and wall thickness must be positive")
    return None if height is None else width * height * t / 1e9


def rate_count(rate_per_m, length):
    if rate_per_m <= 0 or length < 0:
        raise ShaftGeometryError("rate positive, length not negative")
    return int(math.ceil(rate_per_m * length / 1000.0 - 1e-9))


def rate_length(rate_per_m, distribution, bar_length):
    if rate_per_m <= 0 or distribution < 0 or bar_length < 0:
        raise ShaftGeometryError("rate positive, distribution and length not negative")
    return rate_per_m * distribution / 1000.0 * bar_length / 1000.0


def group_representations(items, tol=1.0):
    groups = []
    for iid, view, r in items:
        r = _check(tuple(r))
        for g in groups:
            if all(abs(a - b) <= tol for a, b in zip(g["rect"], r)):
                if view in g["views"]:
                    raise ShaftGeometryError(f"view {view} draws the outline of {g['ids'][0]} twice")
                g["ids"].append(iid)
                g["views"].append(view)
                break
        else:
            groups.append({"rect": r, "ids": [iid], "views": [view]})
    return groups


def ownership_state(owner=None, measured=False, derived=False, project_basis=False, blocked=None, conflict=None):
    if conflict:
        return SOURCE_CONFLICT
    if owner:
        return ALREADY_OWNED_AND_MEASURED if measured else OWNED_BUT_UNMEASURED
    if blocked:
        return BLOCKED_UNQUANTIFIED
    if derived:
        return NEW_SOURCE_DERIVED
    if project_basis:
        return NEW_PROJECT_BASIS_QTO
    return BLOCKED_UNQUANTIFIED
