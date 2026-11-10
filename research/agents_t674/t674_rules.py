"""T-674 rules (pure, stdlib): a ground-slab panel is bounded only by DRAWN geometry (every villa; provenance T-674,
T-180 P18, T-391 F3, T-282, T-230). Coordinates in metres; areas in m2; volumes in m3.

R-T674-1  DEDUCT ONLY A DRAWN MEMBER. A slab panel loses plan area only to a member whose two faces are drawn (a beam
          band of two parallel drawn edges, a column outline, a shaft / pit ring). An overlap with a member that has no
          drawn face is refused (deduction_basis). A drawn member's strip runs between its two drawn faces up to the
          drawn faces of the members it frames into (its carriers), whether or not one face line is drafted short
          (T-282 closure, C1: the beam owns its strip full depth): strip_to_carriers. A face line that stops short of
          its carrier is a drafting gap, not the end of the member; the gap is reported, never billed twice.
R-T674-2  A PANEL SPLITS ONLY ON A DRAWN EDGE. Two engine cells that together make one drawn panel are refused unless
          the line between them is drawn (split_basis). A drawn line that ends ON a true arc (|distance - radius| within
          tolerance) is a node of that arc: a polygonisation that flattens the arc to chords must node the end on the arc
          (node_on_arc), otherwise panel + strip + panel merge into one false face (the T-391 / P18 read).
R-T674-3  A JUNCTION BOX NEVER CROSSES A DRAWN SUPPORT FACE. A junction box (band ends closed around a support) takes
          no area from a slab panel beyond the drawn face of a support that is on the plan (a wall ring, a column
          outline): the panel runs to that face (junction_clip). An area that neither the slab nor any member line
          carries is LOST and is reported with its m2, never left silent.
R-T674-4  MISSING NEVER 0. A panel without a printed thickness, or an area that is None, is refused (volume); a member
          line that is HELD keeps its own quantity: a slab correction that moves area to a held member names that
          member line and never values it.
"""

from __future__ import annotations

import math

TOL_M = 0.0005          # 0.5 mm node tolerance (a CAD end on an arc)
TOL_M2 = 1e-6


class RefusedT674(ValueError):
    pass


def _r6(x):
    return round(float(x) + 0.0, 6)


def area(poly):
    """shoelace area (m2) of a simple polygon [(x, y), ...] in metres."""
    if poly is None or len(poly) < 3:
        raise RefusedT674("polygon missing")
    s = 0.0
    for (x1, y1), (x2, y2) in zip(poly, poly[1:] + poly[:1]):
        s += x1 * y2 - x2 * y1
    return abs(s) / 2.0


def to_m(poly, unit_m):
    """drawing units -> metres; the unit must be stated (mm 0.001, m 1.0), never guessed."""
    if unit_m not in (0.001, 0.01, 1.0):
        raise RefusedT674(f"unit {unit_m!r} not stated as mm / cm / m")
    return [(x * unit_m, y * unit_m) for x, y in poly]


def _line(p, q):
    """infinite line through p, q as (a, b, c) with a x + b y = c, (a, b) unit."""
    dx, dy = q[0] - p[0], q[1] - p[1]
    n = math.hypot(dx, dy)
    if n < 1e-12:
        raise RefusedT674("degenerate edge")
    a, b = -dy / n, dx / n
    return a, b, a * p[0] + b * p[1]


def _cross(l1, l2):
    a1, b1, c1 = l1
    a2, b2, c2 = l2
    det = a1 * b2 - a2 * b1
    if abs(det) < 1e-12:
        raise RefusedT674("parallel lines do not meet")
    return ((c1 * b2 - c2 * b1) / det, (a1 * c2 - a2 * c1) / det)


def deduction_basis(overlaps):
    """overlaps: [{"member", "area_m2", "drawn_faces": [handles], "line_id" or None}] for one panel.
    Returns the m2 to deduct; an overlap whose member has fewer than two drawn faces (a band) or no drawn outline is
    refused (R-T674-1)."""
    tot = 0.0
    for o in overlaps:
        if o.get("area_m2") is None or o["area_m2"] < 0:
            raise RefusedT674(f"{o.get('member')}: overlap area missing")
        faces = o.get("drawn_faces") or []
        need = 1 if o.get("kind") in ("COLUMN", "RING") else 2
        if len(faces) < need:
            raise RefusedT674(f"{o.get('member')}: {o['area_m2']:.4f} m2 deducted for a member with no drawn faces")
        tot += o["area_m2"]
    return _r6(tot)


def strip_to_carriers(face_a, face_b, carrier_1, carrier_2):
    """the plan of a straight member between its two drawn faces (each a pair of points; only the LINE matters, so a
    face drafted short still defines it) and the drawn faces of the two carriers it frames into. -> (polygon, m2)."""
    la, lb = _line(*face_a), _line(*face_b)
    if abs(la[0] * lb[1] - la[1] * lb[0]) > 1e-9:
        raise RefusedT674("member faces not parallel: not one straight band")
    c1, c2 = _line(*carrier_1), _line(*carrier_2)
    poly = [_cross(la, c1), _cross(la, c2), _cross(lb, c2), _cross(lb, c1)]
    return poly, _r6(area(poly))


def face_gap(face_end, carrier):
    """distance (m) from the end of a drafted face line to its carrier's face line: > TOL_M is a drafting gap."""
    a, b, c = _line(*carrier)
    return abs(a * face_end[0] + b * face_end[1] - c)


def node_on_arc(point, centre, radius, tol=TOL_M):
    """True when a line end lies on the true arc (it must be noded there, R-T674-2)."""
    return abs(math.dist(point, centre) - radius) <= tol


def arc_points(centre, radius, a0_deg, a1_deg, n, line_ends=(), tol=TOL_M):
    """an arc (counter-clockwise a0 -> a1) flattened to n chords, with every line end that lies on the true arc
    inserted as a vertex (R-T674-2), so that a polygonisation nodes the line there; any one length unit, tol in the
    same unit (0.5 mm). -> (points, noded ends)."""
    a0, a1 = math.radians(a0_deg), math.radians(a1_deg)
    if a1 < a0:
        a1 += 2 * math.pi
    pts = [(a0 + (a1 - a0) * i / n, (centre[0] + radius * math.cos(a0 + (a1 - a0) * i / n),
                                     centre[1] + radius * math.sin(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]
    noded = []
    for p in line_ends:
        if node_on_arc(p, centre, radius, tol):
            th = math.atan2(p[1] - centre[1], p[0] - centre[0])
            while th < a0 - 1e-12:
                th += 2 * math.pi
            if a0 < th < a1:
                pts.append((th, tuple(p)))        # the line end itself: an exact shared vertex, not a recomputed one
                noded.append(p)
    pts.sort(key=lambda t: t[0])
    return [q for _, q in pts], noded


def split_basis(cells_m2, own_panel_m2, split_drawn, strip_m2=0.0):
    """two engine cells vs one own face. split_drawn: True when the dividing line(s) are drawn edges. When the split
    is drawn, the own face is a false merge and must equal cells + the strip between them (R-T674-2); otherwise the
    split is refused."""
    if any(v is None for v in cells_m2) or own_panel_m2 is None:
        raise RefusedT674("area missing")
    if not split_drawn:
        raise RefusedT674("panel split on a line that is not drawn")
    resid = own_panel_m2 - sum(cells_m2) - strip_m2
    return {"cells_m2": _r6(sum(cells_m2)), "strip_m2": _r6(strip_m2), "residual_m2": _r6(resid),
            "verdict": "ENGINE_RIGHT" if abs(resid) <= 0.01 else "UNRESOLVED"}


def junction_clip(panel_drawn_m2, engine_cell_m2, support_drawn):
    """R-T674-3: a junction box next to a DRAWN support returns to the panel the area it took beyond that support's
    face. -> {"returned_m2", "corrected_m2"}; with no drawn support the box stands (returned 0, reported)."""
    if panel_drawn_m2 is None or engine_cell_m2 is None:
        raise RefusedT674("area missing")
    taken = panel_drawn_m2 - engine_cell_m2
    if taken < -TOL_M2:
        raise RefusedT674("engine cell larger than the drawn panel: not a junction overreach")
    if not support_drawn:
        return {"returned_m2": 0.0, "corrected_m2": _r6(engine_cell_m2), "lost_m2_reported": _r6(taken)}
    return {"returned_m2": _r6(taken), "corrected_m2": _r6(panel_drawn_m2), "lost_m2_reported": 0.0}


def volume(area_m2, t_m):
    """R-T674-4: area x printed thickness; a missing thickness or area is refused, never 0."""
    if area_m2 is None or t_m is None:
        raise RefusedT674("area or thickness missing: HELD, never 0")
    if t_m <= 0 or t_m > 1.0:
        raise RefusedT674(f"thickness {t_m} m is not a slab thickness in metres")
    return _r6(area_m2 * t_m)
