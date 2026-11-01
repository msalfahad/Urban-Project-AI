"""T-412 B7-05 nosing / edge finishing and the tread / riser piece census per flight: research method, any villa.

Physical element first (ERS s.2.1). A NOSING is the exposed FRONT edge of a stepped surface, across the stair width,
at the top of a riser: one riser, one nosing. The surface behind it is either
  TREAD         a going inside the flight (straight or radial / curved front edge),
  WINDER        a tapered tread in a turn (its front edge is the RADIAL edge, never the lane width or the going arc),
  LANDING_EDGE  an intermediate landing reached by the riser (a landing edge is a nosing, NOT a tread),
  FLOOR_EDGE    a floor reached by the last riser of a flight (also a nosing, not a tread).
So per flight: risers = nosings (drawn or held), treads = nosings of kind TREAD / WINDER, and the riser count is never
assumed from the treads (no n - 1 / n arithmetic: owner S-9 (1), engine/stair_assembly.py).

Length (lm, UP-STAIR-004): the length of the DRAWN front edge, less any column / wall face that stands proud inside the
stair width ON that edge (a column whose downhill face lies on the edge line blocks the tread behind it, a column whose
uphill face lies on the edge line does not: half-open interval [c0, c1)). A front edge drawn as an ARC is measured on
its developed arc, a chord is refused; a radial (straight) front edge is its straight length. Winders are never
generated (owner S-9): a turn is measured only from its drawn and dimensioned edges, otherwise HELD with the drawn
figures BESIDE the blank. A HELD or UNKNOWN edge carries no quantity (never 0) and names its cause.

Item ownership (one edge, one item): the nosing is the FRONT edge; railings (B7-09) and stair skirting (B7-07 / B7-08)
run along the SIDES (along the going), so an edge id bound to a railing or skirting run is refused here. The owner's
commercial step basis UP-STAIR-008 (B7-06, lm of step width) "covers tread, riser and nosing together": a TREAD /
WINDER nosing is inside that basis and must never be priced beside it; a LANDING_EDGE / FLOOR_EDGE nosing is not a step
and is outside it. Whether nosing is its own BOQ item is OWNER_RULE_STAIRS_2026-10-24 s.1 (listed); its FORM (profile,
separate strip or worked edge) comes only from an Urban rule or a printed note, else the specification stays HELD by
name (NOSING_FORM_NOT_PRINTED) while the drawn length stays a measured geometry quantity.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

UNIT = "lm"
TREAD, WINDER, LANDING_EDGE, FLOOR_EDGE = "TREAD", "WINDER", "LANDING_EDGE", "FLOOR_EDGE"
KINDS = (TREAD, WINDER, LANDING_EDGE, FLOOR_EDGE)
STRAIGHT, ARC = "STRAIGHT", "ARC"
CONFIRMED, HELD, UNKNOWN = "DRAWING-CONFIRMED", "HELD", "UNKNOWN"
STATUSES = (CONFIRMED, HELD, UNKNOWN)
MAX_EDGE_M = 20.0          # a front edge longer than this is a unit error (mm passed as m)
TOL = 1e-6


class NosingInputError(ValueError):
    """A refused input: the method never guesses an edge, a count, a winder or a unit."""


@dataclass(frozen=True)
class Edge:
    """One nosing (front) edge, at the top of riser `riser_no` (1 = lowest) of flight `flight`."""
    eid: str
    flight: str
    riser_no: int
    kind: str
    status: str
    shape: str = STRAIGHT
    length_m: float | None = None        # straight: drawn edge length (m)
    radius_m: float | None = None        # arc: radius of the front edge (m)
    angle_deg: float | None = None       # arc: swept angle (deg)
    notch_m: float = 0.0                 # face proud inside the width ON this edge (m)
    source: str = "drawn"                # 'drawn' | 'section' | 'generated' (refused)
    handles: tuple = ()
    cause: str = ""
    evidence: str = ""
    beside_lm: float | None = None       # a HELD edge's drawn figure, reported beside the blank, never the quantity
    binds: tuple = ()                    # item ids this edge is bound to (B7-05 only)

    @property
    def geometry_lm(self) -> float | None:
        if self.shape == ARC:
            if self.radius_m is None or self.angle_deg is None:
                return None
            return self.radius_m * math.radians(self.angle_deg) - self.notch_m
        if self.length_m is None:
            return None
        return self.length_m - self.notch_m

    @property
    def qty_lm(self) -> float | None:
        """The B7-05 quantity: only a DRAWING-CONFIRMED edge has one; HELD / UNKNOWN stay blank (None), never 0."""
        return self.geometry_lm if self.status == CONFIRMED else None

    @property
    def in_step_basis(self) -> bool:
        """UP-STAIR-008: a step's commercial lm covers tread + riser + nosing; landing / floor edges are no step."""
        return self.kind in (TREAD, WINDER)


def chord(radius_m: float, angle_deg: float) -> float:
    return 2.0 * radius_m * math.sin(math.radians(angle_deg) / 2.0)


def notch_on_edge(s_edge: float, c0: float, c1: float, proud_m: float, tol: float = 1e-4) -> float:
    """A face proud by `proud_m` over run positions [c0, c1) of the flight: it shortens the edge at s_edge when the tread
    BEHIND that edge (uphill of it) starts inside the column: c0 <= s_edge < c1 (tolerance tol, metres)."""
    if proud_m < 0 or c1 <= c0:
        raise NosingInputError("column interval or projection invalid")
    return proud_m if (c0 - tol) <= s_edge < (c1 - tol) else 0.0


def validate_edge(e: Edge) -> None:
    if e.kind not in KINDS:
        raise NosingInputError(f"{e.eid}: kind {e.kind!r}")
    if e.status not in STATUSES:
        raise NosingInputError(f"{e.eid}: status {e.status!r}")
    if e.source == "generated":
        raise NosingInputError(f"{e.eid}: a generated edge (winder or tread nobody drew) is refused (owner S-9)")
    if e.riser_no < 1:
        raise NosingInputError(f"{e.eid}: riser numbers start at 1")
    if e.shape == ARC:
        if e.length_m is not None:
            raise NosingInputError(f"{e.eid}: an arc front edge is measured on its developed arc; a straight length "
                                   "(the chord) is refused")
        if e.radius_m is None or e.angle_deg is None:
            raise NosingInputError(f"{e.eid}: an arc edge needs its radius and swept angle")
        if e.radius_m > MAX_EDGE_M * 5:
            raise NosingInputError(f"{e.eid}: radius {e.radius_m} m: millimetres passed as metres")
    elif e.shape == STRAIGHT:
        if e.status == CONFIRMED and e.length_m is None:
            raise NosingInputError(f"{e.eid}: a confirmed straight edge needs its drawn length")
    else:
        raise NosingInputError(f"{e.eid}: shape {e.shape!r}")
    g = e.geometry_lm
    for v in (e.length_m, e.beside_lm, g):
        if v is not None and (v <= 0 or v > MAX_EDGE_M):
            raise NosingInputError(f"{e.eid}: length {v} outside (0, {MAX_EDGE_M}] m: millimetres passed as metres?")
    if e.notch_m < 0 or (e.length_m is not None and e.notch_m >= e.length_m):
        raise NosingInputError(f"{e.eid}: notch {e.notch_m}")
    if e.status != CONFIRMED and not e.cause:
        raise NosingInputError(f"{e.eid}: a {e.status} edge names its cause")
    if e.status == CONFIRMED and e.cause:
        raise NosingInputError(f"{e.eid}: a confirmed edge carries no hold cause")
    if e.kind == WINDER and e.status == CONFIRMED and e.source != "drawn":
        raise NosingInputError(f"{e.eid}: a winder is confirmed only from its own drawn edge")
    for b in e.binds:
        if not str(b).startswith("B7-05"):
            raise NosingInputError(f"{e.eid}: bound to {b}: a front edge belongs to B7-05 only (one edge, one item)")


@dataclass
class FlightCensus:
    flight: str
    stair: str
    risers: int                 # from the governing source (section count Q-46 A, or the plan reconstruction)
    risers_source: str
    edges: list = field(default_factory=list)

    def check(self) -> None:
        if self.risers < 1:
            raise NosingInputError(f"{self.flight}: risers {self.risers}")
        nos = sorted(e.riser_no for e in self.edges)
        if nos != list(range(1, self.risers + 1)):
            raise NosingInputError(f"{self.flight}: every riser has exactly one nosing edge (drawn or held): risers "
                                   f"{self.risers}, edges at {nos}")
        ids = [e.eid for e in self.edges]
        if len(set(ids)) != len(ids):
            raise NosingInputError(f"{self.flight}: an edge counted twice")
        for e in self.edges:
            validate_edge(e)
            if e.flight != self.flight:
                raise NosingInputError(f"{e.eid}: belongs to {e.flight}, not {self.flight}")
        top = max(self.edges, key=lambda e: e.riser_no)
        for e in self.edges:
            if e.kind in (LANDING_EDGE, FLOOR_EDGE) and e is not top:
                raise NosingInputError(f"{e.eid}: a landing / floor edge is the TOP nosing of its flight; one in the "
                                       "middle is a tread counted as a landing (or the flight is two flights)")

    def summary(self) -> dict:
        self.check()
        by = lambda st, kinds=KINDS: [e for e in self.edges if e.status == st and e.kind in kinds]  # noqa: E731
        conf = by(CONFIRMED)
        return {
            "flight": self.flight, "stair": self.stair, "risers": self.risers, "risers_source": self.risers_source,
            "visible_risers": self.risers,
            "treads": sum(1 for e in self.edges if e.kind in (TREAD, WINDER)),
            "treads_confirmed": len(by(CONFIRMED, (TREAD, WINDER))),
            "landing_edges": sum(1 for e in self.edges if e.kind == LANDING_EDGE),
            "floor_edges": sum(1 for e in self.edges if e.kind == FLOOR_EDGE),
            "nosings_confirmed": len(conf),
            "nosings_held": len(by(HELD)), "nosings_unknown": len(by(UNKNOWN)),
            "nosing_lm_confirmed": round(sum(e.qty_lm for e in conf), 6),
            "nosing_lm_confirmed_in_step_basis": round(sum(e.qty_lm for e in conf if e.in_step_basis), 6),
            "nosing_lm_confirmed_landing_floor": round(sum(e.qty_lm for e in conf if not e.in_step_basis), 6),
            "held_beside_lm": round(sum(e.beside_lm for e in self.edges
                                        if e.status != CONFIRMED and e.beside_lm is not None), 6),
        }


def overlap_check(edges, side_items: dict) -> None:
    """side_items: {item id: set of edge / stretch ids it is bound to} for B7-09 railings and B7-07 / B7-08 skirting.
    A nosing edge id appearing in any of them is one physical edge in two items: refused."""
    ids = {e.eid for e in edges}
    for item, bound in side_items.items():
        both = ids & set(bound)
        if both:
            raise NosingInputError(f"{sorted(both)} bound to {item} AND to B7-05: one edge, one item")


def straight_edges_from_segments(segs, unit: str, tol_deg: float = 0.05):
    """segs: [((x0, y0), (x1, y1)), ...] the drawn front edges of ONE straight flight in drawing units, lowest riser
    first. Returns [(s_m, length_m)]: s along the flight (perpendicular to the edges, from the first edge), length of
    each edge. Units 'mm' or 'm' only (anything else refused); every edge must be parallel to the first. Rotation and
    mirroring of the drawing do not change the result."""
    if unit not in ("mm", "m"):
        raise NosingInputError(f"unit {unit!r}: 'mm' or 'm' only")
    k = 0.001 if unit == "mm" else 1.0
    (ax, ay), (bx, by) = segs[0]
    ux, uy = bx - ax, by - ay
    n = math.hypot(ux, uy)
    if n == 0:
        raise NosingInputError("zero-length edge")
    ux, uy = ux / n, uy / n
    nx, ny = -uy, ux
    out = []
    for (px, py), (qx, qy) in segs:
        vx, vy = qx - px, qy - py
        ln = math.hypot(vx, vy)
        if ln == 0 or abs(math.degrees(math.asin(max(-1.0, min(1.0, (ux * vy - uy * vx) / ln))))) > tol_deg:
            raise NosingInputError("front edges of one straight flight must be parallel")
        out.append((((px - ax) * nx + (py - ay) * ny) * k, ln * k))
    sgn = 1.0 if len(out) < 2 or out[-1][0] >= 0 else -1.0
    res = [(round(s * sgn + 0.0, 9), round(ln, 9)) for s, ln in out]
    for v in res:
        if v[1] > MAX_EDGE_M:
            raise NosingInputError(f"edge {v[1]} m: millimetres passed as metres")
    return res


def piece_reconciliation(ours: dict, his: dict) -> list:
    """ours / his: {stair: pieces}. Returns one row per stair: difference his - ours (pieces) and %, quantities only.
    The verdict is the caller's (ENGINE_RIGHT with the hand count / RULE_DIFFERENCE / UNRESOLVED / AGREE)."""
    out = []
    for st in sorted(set(ours) | set(his)):
        o, h = ours.get(st), his.get(st)
        d = None if (o is None or h is None) else h - o
        out.append({"stair": st, "ours": o, "his": h, "his_minus_ours": d,
                    "pct_of_ours": None if d is None or not o else round(100.0 * d / o, 2)})
    return out
