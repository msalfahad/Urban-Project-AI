"""T-286: pieces an engine labels 'doorway' or 'zone' inside an open room, closed by what is DRAWN around them; the
room-side line of a curved glazed opening from its drawn line; a held face never summed as 0 (research tool, unwired;
rules R-T286-1 .. 3, proposed, any villa).

R-T286-1 (floor pieces): a floor piece is a doorway / threshold strip only when an opening's jamb bounds it. A piece
  bounded only by wall faces, fixture outlines (counter, joinery, furniture: never a floor boundary, never deducted:
  UP-CER-001 deducts only a stair footprint, a marble threshold and another finish's area), a printed room edge and
  undrawn zone lines (an engine extension of a line that stops elsewhere) lies in the room whose printed box contains
  it and takes that room's floor class, its full polygon area moved once. Outside every box, across two boxes or in a
  room whose class is HELD -> HELD with the reason; its area is kept, never 0.
R-T286-2 (room-side line): the developed room-side line of a curved opening is the drawn line the room touches (arcs as
  arcs) + its jamb returns - the partition ends standing on it. A width from the opening schedule, a dimension text or
  the line on the other face of the band is refused as the room face.
R-T286-3 (totals): a line total reports established and HELD separately; a HELD item carried as 0 (or a quantity without
  a status) is refused.
"""
from __future__ import annotations

import math

from shapely.geometry import Polygon

TOL_M2 = 0.001          # area agreement / closure tolerance (m2)
TOL_INSIDE_M2 = 1e-4    # a piece is inside a box when less than this lies outside it
BOUND_KINDS = {"WALL_FACE", "OPENING_JAMB", "FIXTURE_OUTLINE", "ROOM_EDGE", "ZONE_LINE_UNDRAWN", "ZONE_LINE_DRAWN"}
CLASSES = {"WET", "DRY", "HELD"}
FACE_SOURCES_OK = {"DRAWN_LINE"}
STATUSES = {"VERIFIED", "DRAWING-CONFIRMED", "ASSUMED — OWNER-APPROVED", "HELD", "UNKNOWN"}


class ZoneError(ValueError):
    """Input refused (units, sources, statuses); nothing is guessed."""


# ------------------------------------------------------------------------------------------------ R-T286-1 pieces
def _poly(pts, what):
    if not pts or len(pts) < 3:
        raise ZoneError(f"{what}: polygon needs at least 3 points")
    g = Polygon(pts)
    if not g.is_valid:
        g = g.buffer(0)
    if g.is_empty or g.area <= 0:
        raise ZoneError(f"{what}: empty polygon")
    return g


def _check_units(g, stated_m2, what):
    if stated_m2 is None:
        raise ZoneError(f"{what}: stated area missing (never 0)")
    if g.area > 1000.0 * max(stated_m2, 1e-9):
        raise ZoneError(f"{what}: polygon in millimetres (area {g.area:.1f} vs stated {stated_m2} m2)")
    if abs(g.area - stated_m2) > TOL_M2:
        raise ZoneError(f"{what}: polygon area {g.area:.6f} != stated {stated_m2} m2")


def reclass_piece(piece, bounds, rooms):
    """Classify one engine floor piece by what is drawn around it (R-T286-1).

    piece: {id, polygon_m [[x, y] ...], area_m2, engine_class}
    bounds: [{kind, length_m, ref}] every edge of the piece with what lies on it (ref = drawing handle or 'engine')
    rooms: [{id, box_m [[x, y] ...], floor_class WET / DRY / HELD, class_source}]
    """
    pid = piece.get("id", "?")
    g = _poly(piece.get("polygon_m"), pid)
    _check_units(g, piece.get("area_m2"), pid)
    if not bounds:
        raise ZoneError(f"{pid}: bounding edges not stated")
    for b in bounds:
        if b.get("kind") not in BOUND_KINDS:
            raise ZoneError(f"{pid}: unknown bound kind {b.get('kind')!r}")
        if b.get("length_m") is None or b["length_m"] <= 0:
            raise ZoneError(f"{pid}: bound without a length")
        if b["kind"] != "ZONE_LINE_UNDRAWN" and not b.get("ref"):
            raise ZoneError(f"{pid}: a drawn bound needs its drawing reference")
    blen = sum(b["length_m"] for b in bounds)
    if abs(blen - g.length) > 0.002:
        raise ZoneError(f"{pid}: bounds {blen:.4f} m do not close the perimeter {g.length:.4f} m")
    area = round(g.area, 6)
    kinds = sorted({b["kind"] for b in bounds})
    out = {"id": pid, "engine_class": piece.get("engine_class"), "area_m2": area, "bound_kinds": kinds,
           "fixture_outline_m": round(sum(b["length_m"] for b in bounds if b["kind"] == "FIXTURE_OUTLINE"), 4),
           "undrawn_m": round(sum(b["length_m"] for b in bounds if b["kind"] == "ZONE_LINE_UNDRAWN"), 4)}
    if "OPENING_JAMB" in kinds:
        out.update(disposition="DOORWAY_STRIP", status="UNCHANGED",
                   reason="an opening jamb bounds it: strip / threshold treatment (T-218 / T-240), not this rule")
        return out
    inside = []
    for r in rooms:
        if r.get("floor_class") not in CLASSES:
            raise ZoneError(f"room {r.get('id')}: floor class must be one of {sorted(CLASSES)}")
        box = _poly(r.get("box_m"), r.get("id", "room"))
        if g.difference(box).area <= TOL_INSIDE_M2:
            inside.append(r)
        elif g.intersection(box).area > TOL_INSIDE_M2:
            out.update(disposition="HELD", status="HELD", room=None,
                       reason=f"crosses the printed box of {r.get('id')}: split by the box first")
            return out
    if len(inside) != 1:
        out.update(disposition="HELD", status="HELD", room=None,
                   reason="inside no printed room box" if not inside else "inside two room boxes")
        return out
    r = inside[0]
    if r["floor_class"] == "HELD":
        out.update(disposition="HELD", status="HELD", room=r["id"],
                   reason=f"room {r['id']} floor class HELD ({r.get('class_source') or 'no source'})")
        return out
    if not r.get("class_source"):
        raise ZoneError(f"room {r['id']}: a floor class needs its source (decision / rule)")
    out.update(disposition=f"TO_ROOM_FLOOR_{r['floor_class']}", status="DRAWING-CONFIRMED", room=r["id"],
               class_source=r["class_source"],
               reason="no opening bounds it; fixture outlines and undrawn zone lines are no floor boundary")
    return out


def box_closure(box_m2, notches_m2, pieces_m2):
    """A printed room box closes with every piece in it named: residual within TOL_M2 (R-T286-1)."""
    terms = dict(notches_m2 or {})
    for k, v in (pieces_m2 or {}).items():
        if v is None:
            raise ZoneError(f"piece {k}: no area (a held piece keeps its area, never 0 / None)")
        terms[k] = v
    if any(v < 0 for v in terms.values()):
        raise ZoneError("negative term")
    res = box_m2 - sum((notches_m2 or {}).values()) - sum((pieces_m2 or {}).values())
    return {"box_m2": box_m2, "terms": terms, "residual_m2": round(res, 6), "closes": abs(res) <= TOL_M2}


# --------------------------------------------------------------------------------------------- R-T286-2 room side
def polyline_length(pts_xyb):
    """Length of a polyline [(x, y, bulge) ...] in metres, arcs as arcs; returns (total, [(radius, arc_len) ...])."""
    if len(pts_xyb) < 2:
        raise ZoneError("polyline needs two points")
    total, arcs = 0.0, []
    for a, b in zip(pts_xyb, pts_xyb[1:]):
        ch = math.dist(a[:2], b[:2])
        bu = a[2] if len(a) > 2 else 0.0
        if abs(bu) > 1e-12:
            th = 4.0 * math.atan(abs(bu))
            r = ch / (2.0 * math.sin(th / 2.0))
            seg = r * th
            arcs.append((r, seg))
        else:
            seg = ch
        total += seg
    return total, arcs


def arc_between(center, radius, p1, p2, tol=0.002):
    """Arc length between two points on one circle (the shorter way)."""
    for p in (p1, p2):
        if abs(math.dist(center, p) - radius) > tol:
            raise ZoneError(f"point {p} is not on the arc (r {math.dist(center, p):.4f} vs {radius})")
    a1 = math.atan2(p1[1] - center[1], p1[0] - center[0])
    a2 = math.atan2(p2[1] - center[1], p2[0] - center[0])
    d = abs(a1 - a2) % (2 * math.pi)
    return radius * min(d, 2 * math.pi - d)


def room_side_line(face, partition_ends, other_face=None, printed_width_m=None):
    """R-T286-2: developed room-side line of a curved opening from the drawn line the room touches.

    face: {source, ref, polyline_xyb, room_touches: bool}; partition_ends: [{ref, length_m}] (arc lengths on the face);
    other_face: optional {ref, polyline_xyb} (the band's other face, shown beside); printed_width_m: shown beside only.
    """
    if face.get("source") not in FACE_SOURCES_OK:
        raise ZoneError(f"room face source {face.get('source')!r} refused: only a drawn line is a room face")
    if not face.get("room_touches"):
        raise ZoneError(f"{face.get('ref')}: no room touches this line; it is not the room face")
    total, arcs = polyline_length(face["polyline_xyb"])
    if total > 500:
        raise ZoneError("face length > 500 m: coordinates in millimetres")
    ends = 0.0
    for p in partition_ends or ():
        if p.get("length_m") is None or p["length_m"] < 0 or p["length_m"] > 2.0:
            raise ZoneError(f"partition end {p.get('ref')}: length not established in metres")
        ends += p["length_m"]
    out = {"ref": face.get("ref"), "drawn_line_m": round(total, 4), "arcs": [(round(r, 4), round(s, 4)) for r, s in arcs],
           "partition_ends_m": round(ends, 4), "room_side_m": round(total - ends, 4)}
    if other_face is not None:
        o, _ = polyline_length(other_face["polyline_xyb"])
        out["other_face_ref"] = other_face.get("ref")
        out["other_face_m"] = round(o, 4)
        out["room_minus_other_m"] = round(total - ends - o, 4)
    if printed_width_m is not None:
        out["printed_width_m"] = printed_width_m
        out["room_minus_printed_m"] = round(total - ends - printed_width_m, 4)
    return out


# ------------------------------------------------------------------------------------------------ R-T286-3 totals
def line_total(items):
    """Established total and HELD items kept apart; a HELD item as 0 or a quantity without status is refused."""
    est, held = 0.0, []
    for it in items:
        st = it.get("status")
        if st not in STATUSES:
            raise ZoneError(f"{it.get('id')}: status {st!r} not a standard status")
        q = it.get("quantity")
        if st in ("HELD", "UNKNOWN"):
            if q == 0:
                raise ZoneError(f"{it.get('id')}: a {st} item carried as 0")
            held.append(it.get("id"))
            continue
        if q is None:
            raise ZoneError(f"{it.get('id')}: {st} without a quantity")
        est += q
    return {"established": round(est, 6), "held": held, "whole": not held}
