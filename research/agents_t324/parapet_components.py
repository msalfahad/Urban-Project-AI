"""T-324 parapet composite components: one physical component, one item, one unit, one owner line (every villa).

Research module (unwired; no engine, rule or knowledge version file is changed). Rules, provenance T-324 (proposed for a
future rule version; scope: any roof / terrace parapet of any villa):

R-T324-1  INNER FACE SPLIT AT THE UPTURN TOP. The exposed inner face of a parapet (finished roof level -> parapet top, on
          the drawn inner face line) is ONE physical face. The roof membrane upturn (UP-WP-003, 0.20 m above the membrane
          plane) may rise above the finished roof by e = max(0, 0.20 - c), c = the build-up thickness ABOVE the membrane at
          the edge. The face above the upturn top is the face finish item; the strip of height e is the upturn zone, whose
          finish over the membrane (render protection, tile skirting) is its own item. With c not printed, e is the bounded
          range 0 .. min(0.20, h): the split is HELD, the face total is not. Never a deduction, never booked twice.
R-T324-2  TOP SURFACE FROM THE DRAWN THICKNESS. Top = centreline x t, t the parapet thickness the section / plan draws for
          that run; no default t (refused). A plan outline wider than the drawn wall at parapet level is a PROJECTING
          element (frame, moulding, cap): its excess plan area belongs to that element's item, never to the parapet top.
          A printed cap / coping profile keyed to the run replaces the plain top; an unkeyed profile is an alternative.
R-T324-3  EDGES ONCE, IN METRES RUN. Outer and inner top arrises each on their own drawn run; a stop-end (2 x h + t) only
          at a FREE end; a parapet end against higher construction has none; vertical external corners at parapet height
          belong to the vertical-corner line of the facade (they run from the ground), never to the parapet; the inner
          base junction is a termination, not an arris; a corner bead is an accessory ON an arris (same physical edge,
          never a second length). m.l is never converted to m2 ('2 m.l = 1 m2' is a half-rate payment convention: the
          physical length stays whole; payable = length x rate factor, a separate figure).
R-T324-4  UNPRINTED ITEMS HAVE NO NUMBER. Coping, drip / throat, beads exist only by a print or a specification; without
          one they are UNKNOWN rows with no quantity (never 0, never a default size).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

UPTURN_H = 0.20          # UP-WP-003 1.1.0 (owner approved): membrane upturn height above the membrane plane
STATUSES = ("VERIFIED", "DRAWING-CONFIRMED", "ASSUMED — OWNER-APPROVED", "HELD", "UNKNOWN")
STATES = ("IN_LINE", "NO_LINE", "OTHER_LINE", "NOT_APPLICABLE")
UNITS = ("m2", "m.l", "m3", "nr")


class RefusedError(ValueError):
    """A measurement the rules refuse (default value, double booking, unit conversion, held shown as 0)."""


def _num(v, name):
    if v is None:
        raise RefusedError(f"{name} missing: no default value (R-T324-4)")
    v = float(v)
    if v < 0:
        raise RefusedError(f"{name} negative")
    return v


def inner_face_split(inner_run_m, h_m, cover_above_membrane_m=None, upturn_h=UPTURN_H):
    """R-T324-1. Returns dict: total (fixed), above_lo/above_hi, zone_lo/zone_hi (m2)."""
    L = _num(inner_run_m, "inner run")
    h = _num(h_m, "exposed height")
    total = L * h
    cap = min(upturn_h, h)
    if cover_above_membrane_m is None:
        e_lo, e_hi = 0.0, cap
    else:
        c = _num(cover_above_membrane_m, "cover above membrane")
        e_lo = e_hi = min(cap, max(0.0, upturn_h - c))
    return {"total": total, "above_lo": L * (h - e_hi), "above_hi": L * (h - e_lo),
            "zone_lo": L * e_lo, "zone_hi": L * e_hi,
            "split_status": "HELD" if cover_above_membrane_m is None else "DRAWING-CONFIRMED"}


def top_surface(centreline_m, t_m, plan_area_m2=None):
    """R-T324-2. Returns (top m2, projecting excess m2 or None). t is the drawn thickness, never a default."""
    L = _num(centreline_m, "centreline")
    t = _num(t_m, "drawn thickness")
    if t == 0:
        raise RefusedError("zero thickness")
    top = L * t
    excess = None
    if plan_area_m2 is not None:
        excess = float(plan_area_m2) - top
        if excess < -1e-6:
            raise RefusedError("plan outline narrower than the drawn wall: re-read the section")
        excess = max(0.0, excess)
    return top, excess


def stop_end(h_m, t_m, free: Optional[bool]):
    """R-T324-3. Stop-end edges (m.l) and end face (m2) at one parapet end: free -> (2h + t, t x h); abut -> (0, 0);
    unknown end -> HELD range (lo, hi) tuples."""
    h = _num(h_m, "height")
    t = _num(t_m, "thickness")
    if free is None:
        return {"ml": (0.0, round(2 * h + t, 6)), "m2": (0.0, round(t * h, 6)), "status": "HELD"}
    if free:
        ml, m2 = round(2 * h + t, 6), round(t * h, 6)
        return {"ml": (ml, ml), "m2": (m2, m2), "status": "DRAWING-CONFIRMED"}
    return {"ml": (0.0, 0.0), "m2": (0.0, 0.0), "status": "DRAWING-CONFIRMED"}


def ml_to_m2(*_a, **_k):
    """R-T324-3: refused always (the flagged '2 m.l = 1 m2' corner convention is payment, not area)."""
    raise RefusedError("m.l is never converted to m2: '2 m.l = 1 m2' is a half-rate payment convention (owner notes "
                       "Sigma 2026-10-22 correction), FLAGGED, not an owner rule")


def payable_ml(physical_ml, rate_factor):
    """Payable figure beside the physical length (never replaces it): physical x factor."""
    return _num(physical_ml, "physical length") * _num(rate_factor, "rate factor")


@dataclass
class Row:
    key: str            # component id: <chain>/<run or ALL>/<component>
    component: str
    unit: str
    qty_lo: Optional[float]
    qty_hi: Optional[float]
    status: str
    state: str
    owner: str          # owner trade
    line: str           # candidate line id, 'NO LINE' or 'OTHER_LINE: ...'
    basis: str = ""
    edge: str = ""      # physical edge / face identity for the no-double rule


@dataclass
class Book:
    """R-T324-3 / -4: each component once, each physical face or edge in one row, held never 0, unknown without number."""
    rows: list = field(default_factory=list)
    _keys: set = field(default_factory=set)
    _edges: dict = field(default_factory=dict)

    def add(self, row: Row):
        if row.unit not in UNITS:
            raise RefusedError(f"unit {row.unit}")
        if row.status not in STATUSES:
            raise RefusedError(f"status {row.status}")
        if row.state not in STATES:
            raise RefusedError(f"state {row.state}")
        if row.key in self._keys:
            raise RefusedError(f"component {row.key} booked twice")
        if row.edge:
            prev = self._edges.get(row.edge)
            if prev is not None:
                raise RefusedError(f"physical face / edge {row.edge} already in {prev} (one physical item, one row)")
        if row.status == "UNKNOWN" and (row.qty_lo is not None or row.qty_hi is not None):
            raise RefusedError(f"{row.key}: an UNKNOWN item carries no quantity (R-T324-4)")
        if row.status == "HELD" and row.qty_hi is not None and row.qty_hi == 0 and row.qty_lo == 0:
            raise RefusedError(f"{row.key}: HELD shown as 0")
        if row.status in ("DRAWING-CONFIRMED", "VERIFIED", "ASSUMED — OWNER-APPROVED") and row.qty_lo is None:
            raise RefusedError(f"{row.key}: a measured status needs a quantity")
        if row.qty_lo is not None and row.qty_hi is not None and row.qty_hi < row.qty_lo - 1e-9:
            raise RefusedError(f"{row.key}: range reversed")
        self._keys.add(row.key)
        if row.edge:
            self._edges[row.edge] = row.key
        self.rows.append(row)
        return row

    def total(self, component, unit):
        lo = hi = 0.0
        for r in self.rows:
            if r.component == component and r.unit == unit and r.qty_lo is not None:
                lo += r.qty_lo
                hi += r.qty_hi if r.qty_hi is not None else r.qty_lo
        return lo, hi


def parapet_from_outer(outer_pts, t, inner_side, scale=1.0):
    """Outer polyline (open, ordered) -> (outer run, inner run, centreline) in metres. inner_side 'left' / 'right' of
    the travel direction; a mirror flips the side, a rotation changes nothing. Mitred corners; free ends square."""
    from shapely.geometry import LineString
    if t is None:
        raise RefusedError("thickness missing")
    pts = [(x * scale, y * scale) for x, y in outer_pts]
    outer = LineString(pts)
    inner = outer.offset_curve(t if inner_side == "left" else -t, join_style=2)
    centre = outer.offset_curve((t if inner_side == "left" else -t) / 2.0, join_style=2)
    return outer.length, inner.length, centre.length
