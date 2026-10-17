"""Opening sites v3 (PA05 §8): a site exists wherever two collinear wall
entities terminate with a span between them, whether or not a door leaf is
drawn.  Absence of geometry is a first-class site (UNRESOLVED / OPEN
PASSAGE), never an automatic merge of the rooms on both sides.
"""

from __future__ import annotations

import math

from engine.ingest import ids

CLASSES = ("CONFIRMED_DOOR_OPENING", "CONFIRMED_WINDOW_OPENING", "CONFIRMED_GLAZED_SEPARATOR", "OPEN_PASSAGE", "MATERIAL_CONTINUITY_GAP", "CAD_JUNCTION_GAP", "UNRESOLVED_OPENING_SITE")
MIN_SITE_MM, MAX_SITE_MM = 500.0, 4000.0
JUNCTION_MM = 120.0
LEAF_RADIUS_TOL_MM = 250.0     # leaf width vs structural span (frame allowance)
HINGE_TOL_MM = 450.0           # hinge sits on the far wall face: within one wall thickness of the jamb line
COLLINEAR_OFFSET_MM = 30.0
ANGLE_TOL = math.radians(1.0)


def _angle(p):
    return math.atan2(p.y2 - p.y1, p.x2 - p.x1) % math.pi


def _unit(p):
    L = math.hypot(p.x2 - p.x1, p.y2 - p.y1)
    return (p.x2 - p.x1) / L, (p.y2 - p.y1) / L


def find_sites(view_id, prims, layers, entity_ids):
    """Gaps between collinear wall-layer segments (same layer, same line, non-overlapping) become OPENING_SITEs."""
    walls = [p for p in prims if p.kind == "SEGMENT" and p.provenance.layer in layers["WALL_LAYERS"] and math.hypot(p.x2 - p.x1, p.y2 - p.y1) > 200]
    door_arcs = [p for p in prims if p.kind == "ARC" and layers.get("DOOR_LAYER") and p.provenance.layer == layers["DOOR_LAYER"] and 500 <= p.radius <= 1400]
    glazing = [p for p in prims if p.kind == "SEGMENT" and p.provenance.layer in (layers.get("GLAZING_LAYERS") or [])]
    # group by direction + line offset
    groups = {}
    for p in walls:
        ang = _angle(p)
        ux, uy = math.cos(ang), math.sin(ang)
        off = -uy * p.x1 + ux * p.y1
        key = (int(round(ang / ANGLE_TOL)), int(round(off / COLLINEAR_OFFSET_MM)))
        groups.setdefault(key, []).append((p, ux, uy))
    sites = []
    for (_, _), members in groups.items():
        ux, uy = members[0][1], members[0][2]
        spans = sorted([(min(p.x1 * ux + p.y1 * uy, p.x2 * ux + p.y2 * uy), max(p.x1 * ux + p.y1 * uy, p.x2 * ux + p.y2 * uy), p) for p, _, _ in members], key=lambda t: (t[0], t[1]))
        for (lo1, hi1, a), (lo2, hi2, b) in zip(spans, spans[1:]):
            gap = lo2 - hi1
            if gap <= 0:
                continue
            # gap chord endpoints in xy
            ax = a.x1 if abs(a.x1 * ux + a.y1 * uy - hi1) < 1e-6 else a.x2; ay = a.y1 if abs(a.x1 * ux + a.y1 * uy - hi1) < 1e-6 else a.y2
            bx = b.x1 if abs(b.x1 * ux + b.y1 * uy - lo2) < 1e-6 else b.x2; by = b.y1 if abs(b.x1 * ux + b.y1 * uy - lo2) < 1e-6 else b.y2
            mid = ((ax + bx) / 2, (ay + by) / 2)
            if gap < JUNCTION_MM:
                cls, ev = "CAD_JUNCTION_GAP", ["gap below the junction tolerance"]
            elif gap < MIN_SITE_MM:
                cls, ev = "MATERIAL_CONTINUITY_GAP", ["gap too narrow for a passage"]
            elif gap > MAX_SITE_MM:
                continue
            else:
                leaf = [d for d in door_arcs if abs(d.radius - gap) <= LEAF_RADIUS_TOL_MM and min(math.hypot(d.cx - ax, d.cy - ay), math.hypot(d.cx - bx, d.cy - by)) <= HINGE_TOL_MM]
                glz = [g for g in glazing if _dist_seg_to_point(g, mid) <= 80]
                if leaf:
                    cls, ev = "CONFIRMED_DOOR_OPENING", [f"door swing arc handle {leaf[0].provenance.handle} radius {round(leaf[0].radius)} hinged at a jamb"]
                elif glz:
                    cls, ev = "CONFIRMED_GLAZED_SEPARATOR", [f"glazing-layer line across the span ({len(glz)})"]
                else:
                    cls, ev = "UNRESOLVED_OPENING_SITE", ["wall terminations with a span and no leaf, frame or glazing line: door / passage / window undecided"]
            sites.append({"OPENING_SITE_ID": ids.opening_site_id(view_id, entity_ids[a.object_id], entity_ids[b.object_id], mid), "VIEW": view_id, "WALL_TERMINATION_A": entity_ids[a.object_id],
                          "WALL_TERMINATION_B": entity_ids[b.object_id], "SPAN_MM": round(gap, 1), "CHORD_MM": [[round(ax, 1), round(ay, 1)], [round(bx, 1), round(by, 1)]],
                          "HOST_WALL_CONTINUITY": "SAME_LINE_SAME_LAYER", "CLASS": cls, "EVIDENCE": ev, "LEAF_DRAWN": cls == "CONFIRMED_DOOR_OPENING",
                          "MERGES_ROOMS_AUTOMATICALLY": False, "LAYER": a.provenance.layer, "TWIN_SITE": None, "ANGLE_RAD": round(math.atan2(uy, ux) % math.pi, 4)})
    _pair_twins(sites)
    return sites


TWIN_MAX_OFFSET_MM = 450.0     # the two face lines of one wall


def _pair_twins(sites):
    """A wall drawn as two face lines shows one opening as two collinear-line gaps, one per face.
    Parallel sites whose chords overlap and lie within a wall thickness are twins of one opening;
    a leaf found on either face confirms both.  The pairing changes classification only, never geometry."""
    passable = [s for s in sites if s["CLASS"] in ("CONFIRMED_DOOR_OPENING", "CONFIRMED_GLAZED_SEPARATOR", "UNRESOLVED_OPENING_SITE")]
    for i, a in enumerate(passable):
        if a["TWIN_SITE"]:
            continue
        (ax, ay), (bx, by) = a["CHORD_MM"]
        ux, uy = math.cos(a["ANGLE_RAD"]), math.sin(a["ANGLE_RAD"])
        a_lo, a_hi = sorted((ax * ux + ay * uy, bx * ux + by * uy))
        a_off = -uy * ax + ux * ay
        best = None
        for b in passable[i + 1:]:
            if b["TWIN_SITE"] or abs(b["ANGLE_RAD"] - a["ANGLE_RAD"]) > 2 * ANGLE_TOL:
                continue
            (cx, cy), (dx, dy) = b["CHORD_MM"]
            off = abs((-uy * cx + ux * cy) - a_off)
            if off < JUNCTION_MM / 2 or off > TWIN_MAX_OFFSET_MM:
                continue
            b_lo, b_hi = sorted((cx * ux + cy * uy, dx * ux + dy * uy))
            overlap = min(a_hi, b_hi) - max(a_lo, b_lo)
            if overlap > 0.6 * min(a_hi - a_lo, b_hi - b_lo):
                if best is None or off < best[0]:
                    best = (off, b)
        if best:
            b = best[1]
            a["TWIN_SITE"], b["TWIN_SITE"] = b["OPENING_SITE_ID"], a["OPENING_SITE_ID"]
            for x, y in ((a, b), (b, a)):
                if x["CLASS"] == "UNRESOLVED_OPENING_SITE" and y["CLASS"] in ("CONFIRMED_DOOR_OPENING", "CONFIRMED_GLAZED_SEPARATOR"):
                    x["CLASS"] = y["CLASS"]
                    x["EVIDENCE"] = x["EVIDENCE"] + [f"twin face line site {y['OPENING_SITE_ID']} carries the evidence"]
                    x["LEAF_DRAWN"] = y["LEAF_DRAWN"]


def _dist_seg_to_point(g, pt):
    px, py = pt
    dx, dy = g.x2 - g.x1, g.y2 - g.y1
    L2 = dx * dx + dy * dy
    if L2 == 0:
        return math.hypot(px - g.x1, py - g.y1)
    t = max(0.0, min(1.0, ((px - g.x1) * dx + (py - g.y1) * dy) / L2))
    return math.hypot(px - (g.x1 + t * dx), py - (g.y1 + t * dy))


def summarise(sites):
    return {c: sum(1 for s in sites if s["CLASS"] == c) for c in CLASSES}
