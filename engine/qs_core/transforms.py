"""Changing the description without changing the building.

These exist so a result can be asked the only question that distinguishes measuring from pattern-matching: if
the same building is handed over somewhere else, turned round, or cut into different pieces by the extractor,
does it measure the same?  They belong in the engine rather than in a test because the real adapter runs them
against the real drawing, and a check that only ever runs on fixtures proves nothing about production.
"""

from __future__ import annotations

import copy

from engine.qs_core import geom
from engine.qs_core.entities import GeometryComponent, KIND_WALL_BAND


def transform_plan(plan, dx=0.0, dy=0.0, quarter_turns=0):
    """The same building, drawn somewhere else and turned through right angles.

    Right angles only: this engine reasons about axis-aligned geometry, and a helper that quietly produced a
    rotated rectangle would be a lie about what it can measure.
    """
    out = copy.deepcopy(plan)

    def move(rect):
        return geom.translate(geom.rotate90(rect, quarter_turns), dx, dy)

    for c in out["COMPONENTS"]:
        c.rects = [move(r) for r in c.rects]
        c.axis = geom.rotate_axis(c.axis, quarter_turns)
        if c.material_rects:
            c.material_rects = [move(r) for r in c.material_rects]
    for c in out.get("CANDIDATES", []):
        x, y = geom.rotate_point(c.centre[0], c.centre[1], quarter_turns)
        c.centre = (x + dx, y + dy)
        c.axis = geom.rotate_axis(c.axis, quarter_turns)
        if c.jamb_points:
            moved = []
            for jx, jy in c.jamb_points:
                rx, ry = geom.rotate_point(jx, jy, quarter_turns)
                moved.append((rx + dx, ry + dy))
            c.jamb_points = moved
        if c.rotation is not None:
            c.rotation = (c.rotation + 90 * (quarter_turns % 4)) % 360
    for b in out.get("BARRIERS", []):
        for _ in range(quarter_turns % 4):
            # (x, y) -> (-y, x): a line along x at y=p becomes a line along y at x=-p, and the reverse
            if b.axis == geom.AXIS_X:
                b.axis, b.position, b.lo, b.hi = geom.AXIS_Y, -b.position, b.lo, b.hi
            else:
                b.axis, b.position, b.lo, b.hi = geom.AXIS_X, b.position, -b.hi, -b.lo
        if b.axis == geom.AXIS_X:
            b.position, b.lo, b.hi = b.position + dy, b.lo + dx, b.hi + dx
        else:
            b.position, b.lo, b.hi = b.position + dx, b.lo + dy, b.hi + dy
    for lb in out.get("LABELS", []):
        x, y = geom.rotate_point(lb.x, lb.y, quarter_turns)
        lb.x, lb.y = x + dx, y + dy
    return out


def resegment_plan(plan, cuts=2):
    """The same building, cut into more pieces: every wall band split along its own run."""
    out = copy.deepcopy(plan)
    comps = []
    for c in out["COMPONENTS"]:
        if c.kind != KIND_WALL_BAND or len(c.rects) != 1:
            comps.append(c)
            continue
        r = c.rects[0]
        if c.axis == geom.AXIS_X:
            xs = [r.x0 + (r.x1 - r.x0) * i / cuts for i in range(cuts + 1)]
            pieces = [geom.Rect(xs[i], r.y0, xs[i + 1], r.y1) for i in range(cuts)]
        else:
            ys = [r.y0 + (r.y1 - r.y0) * i / cuts for i in range(cuts + 1)]
            pieces = [geom.Rect(r.x0, ys[i], r.x1, ys[i + 1]) for i in range(cuts)]
        for n, piece in enumerate(pieces):
            comps.append(GeometryComponent(f"{c.component_ref}::S{n}", c.kind, [piece], c.floor,
                                           c.source_revision, thickness=c.thickness, axis=c.axis,
                                           layer=c.layer))
    out["COMPONENTS"] = comps
    if "ANNOTATIONS" in out:
        ann = dict(out["ANNOTATIONS"])
        for c in comps:
            base = c.component_ref.split("::S")[0]
            if base in ann:
                ann[c.component_ref] = ann[base]
        out["ANNOTATIONS"] = ann
    return out


def quantity_fingerprint(result):
    """What the building is, stripped of every name and coordinate the description happened to choose."""
    return {
        "WALLS": sorted((round(r["THICKNESS_FAMILY_M"] or 0, 6), round(r["NET_AREA_M2"], 6))
                        for r in result["WALL_ROWS"] if r["NET_AREA_M2"] is not None),
        "BLOCKED": sorted(round(r["THICKNESS_FAMILY_M"] or 0, 6) for r in result["WALL_ROWS"]
                          if r["NET_AREA_M2"] is None),
        "SPACES": sorted(round(s["AREA_M2"], 6) for s in result["SPACES"]),
        "OPENINGS": sorted(round(o["AREA_M2"], 6) for o in result["OPENING_REGISTER"]["REGISTER"]
                           if o["AREA_M2"] is not None),
        "PUBLISHED": sorted((k, v["FINAL_QUANTITY"])
                            for k, v in (result["PUBLICATION"] or {"SUBTOTALS": {}})["SUBTOTALS"].items()),
    }
