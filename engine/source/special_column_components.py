"""SPECIAL COLUMN COMPONENTS - turned (twisted), dead and planted columns (generic).

A special-column label marks an event on an ordinary column chain. It is never a second column:
  TURN     the column changes orientation at a slab. A typical detail may add bars and a spiral over a stated zone
           either side of that slab.
  DEAD     the column stops under a slab or beam and does not continue above.
  PLANTED  the column starts on a beam or slab and belongs to the storey above that slab.

Reading a plan
  parse_special_label(text)    'T.C' -> TURN; 'D.C' -> DEAD; 'P.C 20x70' -> PLANTED with section (20, 70) cm.
                               Anything else -> None. The label names the event only, never the reinforcement.
  parse_bar_count(text)        'N<bar symbol>D' -> {count N, dia_mm D}. A rate ('/m') or a bare number -> None.
  planted_storey(slab_sheet, storeys, closing)
                               the storey a planted column belongs to: the one ABOVE the storey whose closing slab is
                               drawn on slab_sheet.

Plan geometry (points in mm)
  axis_rect(points)            an axis-aligned rectangle -> (x0, y0, x1, y1); anything else is refused.
  rect_intersection(a, b)      the common rectangle of two axis-aligned rectangles, or None.
  extent_along(points, angle_deg)
                               the width of a polygon's projection on a direction (the column length along a beam).
  span_relation(t, t0, t1, half_extent, tol)
                               where a column footprint centred at t sits on a beam span [t0, t1] along the beam line:
                               INSIDE (the footprint is clear of both ends), AT_END (it reaches an end) or OUTSIDE.
  resolve_host(relations)      one INSIDE span -> RESOLVED. No INSIDE span but span ends meet -> NODE (a beam-on-beam
                               junction; no single carrying beam). Two INSIDE spans -> CROSSING. Nothing -> NONE. Only
                               RESOLVED names a host.

Quantities (unit mass from engine.source.rebar_unit_mass, the project's single method)
  pitch_from_rate(per_m)       a stated rate N/m of a spiral -> pitch 1000 / N mm.
  turns_over(zone_mm, per_m)   turns in a stated zone at a stated rate: zone x rate (never rounded, never +1).
  ellipse_perimeter(a, b)      Ramanujan's second approximation on the semi-axes (exact for a circle).
  helix_length(perimeter, pitch, turns)
                               the helix centreline: turns x sqrt(perimeter^2 + pitch^2). The pitch alone is not the
                               bar length.
  inscribed_centreline(w, h, cover, bar)
                               the largest spiral centreline that fits a w x h zone with cover to the bar's outer face:
                               (w - 2 cover - bar, h - 2 cover - bar). It bounds a spiral from ABOVE; it is never a
                               spiral dimension.
  beam_extra_projection_mm(count, depth_mm, along_mm)
                               a 'DEPTH past each column face' beam extra over its horizontal projection:
                               count x (2 x depth + column length along the beam). Cranks and hooks are excluded and
                               must be reported apart. It is a lower bound.
  straight_kg(length_mm, dia_mm, unit_mass)
                               mass of a straight length.

Ownership
  decide(required, existing_state, established)
                               ALREADY_OWNED when another stage holds the role in a released state, alone or with
                               blocked parts ('BLOCKED+LOWER_BOUND'); it is never added again. Otherwise NOT_REQUIRED
                               when the source says the role is absent, INCREMENTAL only when the source requires the
                               role AND its quantity is established, else BLOCKED (a role another stage holds blocked
                               stays blocked).
  duplicate_roles(rows, key)   the physical roles assigned to more than one owner (must be empty).

Stdlib + engine.source.rebar_unit_mass only. No project data.
"""

from __future__ import annotations

import math
import re
from collections import Counter

from engine.source import rebar_unit_mass as UM

TURN, DEAD, PLANTED = "TURN", "DEAD", "PLANTED"
FAMILIES = (TURN, DEAD, PLANTED)
INSIDE, AT_END, OUTSIDE = "INSIDE", "AT_END", "OUTSIDE"
RESOLVED, NODE, CROSSING, NONE = "RESOLVED", "NODE", "CROSSING", "NONE"
ALREADY_OWNED, INCREMENTAL, BLOCKED, NOT_REQUIRED = "ALREADY_OWNED", "INCREMENTAL", "BLOCKED", "NOT_REQUIRED"
OWNED_STATES = ("VERIFIED", "PROVISIONAL", "LOWER_BOUND")
TOL = 1e-9

_BAR = r"(?:%%[cC]|[ØøΦφ])"
_COUNT = re.compile(r"^\s*(\d+)\s*" + _BAR + r"\s*(\d+)\s*$")
_LABEL = re.compile(r"^\s*([TDP])\s*\.\s*C(?![A-Za-z])\s*(?:(\d+(?:\.\d+)?)\s*[xX×]\s*(\d+(?:\.\d+)?))?\s*$")
_FAMILY = {"T": TURN, "D": DEAD, "P": PLANTED}


class SpecialColumnError(ValueError):
    pass


# ------------------------------------------------------------------ plan reading
def parse_special_label(text):
    """'T.C' / 'D.C' / 'P.C [b x h]' -> {family, section_cm}. A section is read only when printed in the label."""
    m = _LABEL.match(text or "")
    if not m:
        return None
    sec = None
    if m.group(2):
        sec = (float(m.group(2)), float(m.group(3)))
    return {"family": _FAMILY[m.group(1)], "section_cm": sec}


def parse_bar_count(text):
    """'10%%C16' -> {count 10, dia_mm 16}; a rate per metre, a bare number or a zero count -> None."""
    m = _COUNT.match(text or "")
    if not m:
        return None
    n, d = int(m.group(1)), int(m.group(2))
    if n <= 0 or d <= 0:
        return None
    return {"count": n, "dia_mm": d}


def planted_storey(slab_sheet, storeys, closing):
    """storeys: ordered storey names; closing: {storey: sheet of the slab that closes it}. A column planted on the slab
    drawn on slab_sheet belongs to the storey above the one that slab closes."""
    below = [s for s in storeys if closing.get(s) == slab_sheet]
    if len(below) != 1:
        raise SpecialColumnError(f"{slab_sheet} closes {len(below)} storeys")
    i = list(storeys).index(below[0])
    if i + 1 >= len(storeys):
        raise SpecialColumnError(f"no storey above {below[0]}")
    return storeys[i + 1]


# ------------------------------------------------------------------ plan geometry
def axis_rect(points, tol=1e-6):
    """(x0, y0, x1, y1) of an axis-aligned rectangle; refuses anything else."""
    pts = [tuple(map(float, p)) for p in points]
    if len(pts) == 5 and math.dist(pts[0], pts[-1]) <= tol:
        pts = pts[:4]
    if len(pts) != 4:
        raise SpecialColumnError("a rectangle has four corners")
    for a, b in zip(pts, pts[1:] + pts[:1]):
        if abs(a[0] - b[0]) > tol and abs(a[1] - b[1]) > tol:
            raise SpecialColumnError("not an axis-aligned rectangle")
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    if x1 - x0 <= tol or y1 - y0 <= tol:
        raise SpecialColumnError("degenerate rectangle")
    return (x0, y0, x1, y1)


def rect_intersection(a, b):
    x0, y0, x1, y1 = max(a[0], b[0]), max(a[1], b[1]), min(a[2], b[2]), min(a[3], b[3])
    if x1 - x0 <= TOL or y1 - y0 <= TOL:
        return None
    return (x0, y0, x1, y1)


def extent_along(points, angle_deg):
    """Width of the polygon's projection on the direction angle_deg (degrees from +x)."""
    if len(points) < 2:
        raise SpecialColumnError("a footprint needs at least two points")
    c, s = math.cos(math.radians(angle_deg)), math.sin(math.radians(angle_deg))
    t = [p[0] * c + p[1] * s for p in points]
    return max(t) - min(t)


def span_relation(t, t0, t1, half_extent, tol=1.0):
    """A column footprint [t - half_extent, t + half_extent] against a span [t0, t1] on the same beam line."""
    if half_extent < 0 or tol < 0:
        raise SpecialColumnError("half extent and tolerance must be >= 0")
    lo, hi = min(t0, t1), max(t0, t1)
    if t - half_extent > lo + tol and t + half_extent < hi - tol:
        return INSIDE
    if lo - half_extent - tol <= t <= hi + half_extent + tol:
        return AT_END
    return OUTSIDE


def resolve_host(relations):
    """relations: [(span_id, relation)]. -> {state, host, inside, at_end}. Only RESOLVED names a host."""
    inside = sorted(s for s, r in relations if r == INSIDE)
    at_end = sorted(s for s, r in relations if r == AT_END)
    if len(inside) == 1:
        return {"state": RESOLVED, "host": inside[0], "inside": inside, "at_end": at_end}
    if len(inside) > 1:
        return {"state": CROSSING, "host": None, "inside": inside, "at_end": at_end}
    if at_end:
        return {"state": NODE, "host": None, "inside": [], "at_end": at_end}
    return {"state": NONE, "host": None, "inside": [], "at_end": []}


# ------------------------------------------------------------------ quantities
def pitch_from_rate(per_m):
    if not per_m or per_m <= 0:
        raise SpecialColumnError("a spiral rate must be > 0 per metre")
    return 1000.0 / per_m


def turns_over(zone_mm, per_m):
    if zone_mm <= 0:
        raise SpecialColumnError("a spiral zone must be > 0")
    pitch_from_rate(per_m)
    return zone_mm * per_m / 1000.0


def ellipse_perimeter(a, b):
    """Perimeter of an ellipse with semi-axes a, b (Ramanujan II; exact for a circle)."""
    if a <= 0 or b <= 0:
        raise SpecialColumnError("semi-axes must be > 0")
    h = ((a - b) / (a + b)) ** 2
    return math.pi * (a + b) * (1.0 + 3.0 * h / (10.0 + math.sqrt(4.0 - 3.0 * h)))


def helix_length(perimeter_mm, pitch_mm, turns):
    if perimeter_mm <= 0 or pitch_mm <= 0 or turns <= 0:
        raise SpecialColumnError("perimeter, pitch and turns must be > 0")
    return turns * math.hypot(perimeter_mm, pitch_mm)


def inscribed_centreline(width_mm, depth_mm, cover_mm, bar_mm):
    w = width_mm - 2.0 * cover_mm - bar_mm
    h = depth_mm - 2.0 * cover_mm - bar_mm
    if w <= 0 or h <= 0:
        raise SpecialColumnError("no spiral fits the zone")
    return (w, h)


def beam_extra_projection_mm(count, depth_mm, along_mm):
    if count <= 0 or depth_mm <= 0 or along_mm <= 0:
        raise SpecialColumnError("count, depth and column length must be > 0")
    return count * (2.0 * depth_mm + along_mm)


def straight_kg(length_mm, dia_mm, unit_mass):
    if length_mm < 0:
        raise SpecialColumnError("length must be >= 0")
    return length_mm / 1000.0 * UM.kg_per_m(dia_mm, unit_mass)


# ------------------------------------------------------------------ ownership
def decide(required, existing_state, established):
    """required: True (the source requires the role), False (the source says it is absent) or None (not established).
    existing_state: the release state of the role in another stage, or None. established: the quantity is fixed by
    the source."""
    if existing_state and any(x in OWNED_STATES for x in str(existing_state).split("+")):
        return ALREADY_OWNED
    if required is False:
        return NOT_REQUIRED
    if required is True and established:
        return INCREMENTAL
    return BLOCKED


def duplicate_roles(rows, key=("PHYSICAL_ROLE_KEY",)):
    """Roles held by more than one owning row (key fields joined)."""
    c = Counter(tuple(r[k] for k in key) for r in rows)
    return sorted(k for k, n in c.items() if n > 1)
