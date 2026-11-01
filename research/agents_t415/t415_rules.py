"""T-415 curved (helical) stair flight concrete: element definition, measurement and reconciliation rules (any villa).

Research module (lane S). It changes no engine module, candidate line, rule or knowledge version and releases nothing.
Physical element (ERS s.2.1): a curved flight on a circular plan lane between an inner edge r_in and an outer edge r_out
(the structural lane, R-STAIR-LANE-1), divided by DRAWN riser lines. Its concrete is three solids, each its own piece:

  steps  = for every tread k between drawn riser lines k and k+1: 1/2 x riser x A_k (owner Q-51 A cond: the step's own
           DRAWN plan area; exact for a curved tread because, on every walking path at radius r, the step is a triangle
           of height R over the path length g(r), so the volume is R/2 x the integral of g dr = R/2 x A_k);
  waist  = t x K, with K = integral of sec(alpha) over the plan, tan(alpha) = R / g(r) (the slope differs with the
           radius on a curved flight, so a waist is never t x plan area x one secant, and never t x chord x width);
  joints = foot / head wedges, beams, columns, slabs it meets: each carried by ONE owner (R-CONC-OWN-1, T-189).

Rules (R-T415-n), every villa:
  R-T415-1 DEVELOPED, NOT CHORD: a curved flight's length is the developed arc at the radius it is measured on; a chord
           between the end points is refused (CurvedLengthError) when the element is curved.
  R-T415-2 ONE OWNER PER TREAD: a tread (identified by its two bounding riser lines) belongs to exactly one flight piece;
           the junction tread between a curved part and a straight flight is listed once (StepsTwiceError).
  R-T415-3 DRAWN RISERS ONLY: treads come only from drawn riser lines; dividing a curve or a landing into winders /
           curved steps by angle or count when the lines are not drawn is refused (UndrawnWinderError, owner S-9).
  R-T415-4 WAIST THICKNESS FROM ITS OWN PANEL: the waist thickness is the value printed for THIS element; a value printed
           in another panel (e.g. 'T 16' on the straight flight) is not borrowed; unprinted -> the waist is HELD with its
           coefficient K beside it (m3 per m of thickness), never 0 and never a default.
  R-T415-5 BOUND FROM PHYSICS ONLY: where the plan prints reinforcement in the curved panel (a reinforced slab exists),
           the curved flight concrete is AT_LEAST its steps (waist > 0); no upper bound without a printed thickness.
  R-T415-6 PLATE ROW DECOMPOSITION: a plate row (W x L x T over a whole stair) is compared piece by piece by plan area:
           THICKNESS_BASIS on valued pieces, HELD_BINDING on held pieces (his T x their drawn area, carried as HELD,
           never closed), AREA_BEYOND_DRAWN for his area above the drawn plan (UNTRACED unless his figure is a drawn
           figure with evidence beyond the figure itself). The terms sum exactly to the residual.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

TOL = 1e-9


class CurvedLengthError(ValueError):
    """R-T415-1: a chord offered as the length of a curved element."""


class StepsTwiceError(ValueError):
    """R-T415-2: one tread owned by two pieces (or a plate equivalent thickness plus separate steps)."""


class UndrawnWinderError(ValueError):
    """R-T415-3: treads generated where no riser lines are drawn."""


class BorrowedThicknessError(ValueError):
    """R-T415-4: a thickness printed for another element used for this one."""


# ----------------------------------------------------------------------------------------------- geometry (closed form)

def annular_area(r_in: float, r_out: float, dtheta: float) -> float:
    """Plan area of an annular sector (dtheta in radians)."""
    if not (0 <= r_in < r_out) or dtheta <= 0:
        raise ValueError("annular sector needs 0 <= r_in < r_out and dtheta > 0")
    if r_out > 100.0:
        raise ValueError(f"radius {r_out} m: a villa stair radius above 100 m is a millimetre value read as metres")
    return 0.5 * (r_out ** 2 - r_in ** 2) * dtheta


def _sec_primitive(r: float, a: float) -> float:
    s = math.sqrt(r * r + a * a)
    return 0.5 * r * s + 0.5 * a * a * math.log(r + s)


def annular_waist_coefficient(r_in: float, r_out: float, dtheta: float, rise: float) -> float:
    """K = integral of sec(alpha) dA over an annular tread with going g(r) = r dtheta and riser `rise`:
    sec = sqrt(1 + (rise / (r dtheta))^2), dA = r dtheta dr -> dtheta x integral sqrt(r^2 + a^2) dr with a = rise / dtheta.
    Waist volume = t (normal thickness) x K."""
    annular_area(r_in, r_out, dtheta)
    a = rise / dtheta
    return dtheta * (_sec_primitive(r_out, a) - _sec_primitive(r_in, a))


def arc_length(r: float, dtheta: float) -> float:
    return r * dtheta


def chord_length(r: float, dtheta: float) -> float:
    return 2.0 * r * math.sin(dtheta / 2.0)


def resolve_curved_length(offered: float, r: float, dtheta: float, tol: float = 1e-4) -> float:
    """R-T415-1: return the developed arc; refuse the chord (and any value that is neither within tol)."""
    arc, ch = arc_length(r, dtheta), chord_length(r, dtheta)
    if abs(offered - arc) <= tol:
        return arc
    if abs(offered - ch) <= tol and abs(arc - ch) > tol:
        raise CurvedLengthError(f"chord {ch:.6f} offered for a curved element; developed arc is {arc:.6f}")
    raise CurvedLengthError(f"length {offered:.6f} is neither the developed arc {arc:.6f} at r {r:.6f}")


# ----------------------------------------------------------------------------------------------- tread assembly

@dataclass(frozen=True)
class Tread:
    """A tread between two DRAWN riser lines (ids), with its drawn plan area (m2) and its waist coefficient K (m2)."""
    lower: str
    upper: str
    area: float
    k_waist: float
    piece: str
    drawn: bool = True

    @property
    def key(self):
        return (self.lower, self.upper)


@dataclass
class FlightPieces:
    rise: float
    rise_status: str
    treads: list = field(default_factory=list)

    def add(self, tread: Tread):
        if not tread.drawn:
            raise UndrawnWinderError(f"tread {tread.key} is not bounded by drawn riser lines (owner S-9: no generated "
                                     "winders / curved steps; HELD / UNSUPPORTED)")
        for t in self.treads:
            if t.key == tread.key or {t.lower, t.upper} == {tread.lower, tread.upper}:
                raise StepsTwiceError(f"tread {tread.key} already owned by {t.piece}; offered again to {tread.piece}")
        self.treads.append(tread)

    def steps_m3(self, piece: str | None = None) -> float:
        return sum(0.5 * self.rise * t.area for t in self.treads if piece is None or t.piece == piece)

    def area(self, piece: str | None = None) -> float:
        return sum(t.area for t in self.treads if piece is None or t.piece == piece)

    def k_waist(self, piece: str | None = None) -> float:
        return sum(t.k_waist for t in self.treads if piece is None or t.piece == piece)


def treads_from_riser_angles(angles_deg, r_in, r_out, rise, piece, ids=None):
    """Curved treads from DRAWN riser-line angles (degrees, ascending along the walking direction). Each consecutive
    pair is one tread; nothing is generated between them."""
    if rise is None or rise <= 0:
        raise ValueError("riser height not established: the steps are HELD, never computed with 0 or a default")
    if len(angles_deg) < 2:
        raise UndrawnWinderError("a curved tread needs two drawn riser lines")
    ids = ids or [f"L{i}" for i in range(len(angles_deg))]
    out = []
    for i in range(len(angles_deg) - 1):
        d = math.radians(angles_deg[i + 1] - angles_deg[i])
        if d <= 0:
            raise ValueError("riser angles must ascend along the walking direction")
        out.append(Tread(ids[i], ids[i + 1], annular_area(r_in, r_out, d),
                         annular_waist_coefficient(r_in, r_out, d, rise), piece))
    return out


def subdivide_undrawn(span_deg: float, count: int):
    """R-T415-3: never generate treads by dividing an arc or a landing. Always refused."""
    raise UndrawnWinderError(f"refused: {count} treads over {span_deg} deg are not drawn (owner S-9)")


# ----------------------------------------------------------------------------------------------- waist and bound

def waist_m3(k_waist: float, thickness: float | None, thickness_element: str | None, element: str):
    """R-T415-4: returns (value, status). None thickness -> (None, 'HELD'); another element's thickness -> refused."""
    if thickness is None:
        return None, "HELD"
    if thickness_element != element:
        raise BorrowedThicknessError(f"thickness printed for {thickness_element!r} offered for {element!r}")
    if thickness <= 0:
        raise ValueError("a printed waist thickness is > 0")
    return thickness * k_waist, "CALCULATED"


def curved_flight_bound(steps: float, reinforcement_printed: bool):
    """R-T415-5: AT_LEAST steps when a reinforced slab is printed in the panel; otherwise unbounded (None)."""
    if reinforcement_printed:
        return dict(kind="AT_LEAST", low=steps, high=None)
    return dict(kind="UNBOUNDED", low=None, high=None)


def plate_equivalent_check(steps_separately: bool, plate_thickness_includes_steps: bool):
    """R-T415-2 corollary: a plate thickness that already represents 'slab + steps' plus separate step triangles is the
    steps counted twice."""
    if steps_separately and plate_thickness_includes_steps:
        raise StepsTwiceError("plate thickness 'slab + steps' combined with separate step triangles")
    return True


# ----------------------------------------------------------------------------------------------- reconciliation

def decompose_plate_row(his_w: float, his_l: float, his_t: float, pieces: list) -> dict:
    """R-T415-6. pieces: dicts {id, area (drawn plan m2), m3 (valued, or None when HELD)}.
    residual = engine valued - his figure = sum(THICKNESS_BASIS) + sum(HELD_BINDING) + AREA_BEYOND_DRAWN."""
    his = his_w * his_l * his_t
    his_area = his_w * his_l
    drawn = sum(p["area"] for p in pieces)
    terms = []
    for p in pieces:
        if p["m3"] is None:
            terms.append(dict(id=p["id"], kind="HELD_BINDING", m3=-his_t * p["area"]))
        else:
            terms.append(dict(id=p["id"], kind="THICKNESS_BASIS", m3=p["m3"] - his_t * p["area"]))
    beyond = -his_t * (his_area - drawn)
    terms.append(dict(id="his area beyond the drawn plan", kind="AREA_BEYOND_DRAWN", m3=beyond,
                      area=his_area - drawn))
    engine = sum(p["m3"] for p in pieces if p["m3"] is not None)
    residual = engine - his
    closure = residual - sum(t["m3"] for t in terms)
    assert abs(closure) < 1e-9, closure
    return dict(his_m3=his, his_area=his_area, drawn_area=drawn, engine_valued=engine, residual=residual,
                terms=terms, closure=closure)
