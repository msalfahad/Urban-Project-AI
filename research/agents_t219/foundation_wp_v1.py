"""T-219: foundation and lift-pit waterproofing as BOQ lines (research piece, not wired; FOUNDATION_WP_V1).

Pure functions, stdlib only, no I/O, any villa. Inputs are VALUES only (polygons in a declared unit, printed depths,
the printed underlay chain of the footing detail). Nothing here reads a drawing; the development-villa runner
`t219_alsenan_check.py` builds the inputs and states every source.

Physical elements (ERS s.2.1), from the typical footing details of a set like ST p.13 / p.14:
- FOOTING UNDERLAY (every isolated footing): under the footing, from the top down, a protection screed (printed
  thickness), a waterproofing membrane (printed thickness / name), the plain-concrete blinding (printed thickness,
  projecting beyond the footing). The membrane and the screed lie inside the footing outline (the detail ends both at
  the footing faces); the blinding projection belongs to the blinding line (STRUCTURE) and is REFUSED here.
  Installed membrane = the outline area, one layer (UP-WP-MAT-001: net = installed for a single flat layer; laps and
  rolls are procurement). Screed = outline area (m2) and area x printed thickness (m3).
- FOOTING SIDE FACES: what covers them depends on the detail that applies (a detail chosen by a level condition,
  e.g. 'level difference between the upper ground beam and the footing more / less than 2.5 m'): one detail may
  print a liquid coating on every face in contact with earth (face = perimeter x H), the other the sheet membrane
  wrapped down the sides (face = perimeter x (H + screed + membrane)). While the governing level is not printed the
  side line is HELD with BOTH readings; never one picked, never 0. Faces against another concrete member (a
  neighbour footing in a one-owner clip, a strap end) are not in contact with earth: deducted with their own status.
- NO UPTURN: the owner's 0.20 m upturn (UP-WP-003) is scoped to wet areas, balconies, terraces and roofs; a footing
  membrane turns up only where a detail prints it (the side reading above). An upturn requested here is REFUSED.
- LIFT PIT (base footing + RC pit ring, detail like ST p.14): membrane under the base (base area), up the base sides
  and the screed edge (perimeter x (H + screed)), over the base top outside the pit envelope (base - envelope), up the
  outer pit wall faces (envelope perimeter x pit height); protection board on the sides, the top outside the envelope
  and the walls (never under the base); screed under the base (m2, m3). Everything with the pit height is HELD while
  the height is not printed ('as per lift manufacturer'), never 0.
- PROCUREMENT (rolls, laps, coats, kg): only by the owner's layout rules (UP-WP-001 / -002 / -005 / UP-WP-LAY-001)
  and only when the PRODUCT is printed as a sheet membrane; otherwise HELD (PRODUCT_NOT_PRINTED). A liquid coating's
  material is BY_SPEC (UP-WP-MAT-001): HELD.

A footing outline that carries two schedule tags (one outline, two types) is HELD with the readings 'outline' and
'rows separately' (T-233 / T-239 rule), never one picked.

Statuses (WORKFLOW_CONTROLS s.5): DRAWING-CONFIRMED, HELD (never 0, never in a measured total), UNKNOWN.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

METHOD = "FOUNDATION_WP_V1"
TOL = 1e-9
UNIT_SCALE = {"m": 1.0, "mm": 0.001, "cm": 0.01}
DC = "DRAWING-CONFIRMED"
HELD = "HELD"
UPTURN_SCOPE_UP_WP_003 = ("WET_AREA", "BALCONY", "TERRACE", "ROOF")


class RefusedError(ValueError):
    """An input that would put a wrong or invented quantity into a waterproofing line."""


# ------------------------------------------------------------------------------------------------ geometry (stdlib)
def to_m(points, unit):
    if unit not in UNIT_SCALE:
        raise RefusedError(f"unit {unit!r} not declared (m, cm, mm): a polygon without its unit is refused")
    s = UNIT_SCALE[unit]
    pts = [(float(x) * s, float(y) * s) for x, y in points]
    if len(pts) >= 2 and pts[0] == pts[-1]:
        pts = pts[:-1]
    if len(pts) < 3:
        raise RefusedError("an outline needs at least 3 vertices")
    return pts


def area(pts):
    a = 0.0
    for i, (x1, y1) in enumerate(pts):
        x2, y2 = pts[(i + 1) % len(pts)]
        a += x1 * y2 - x2 * y1
    return abs(a) / 2.0


def perimeter(pts):
    return sum(math.dist(pts[i], pts[(i + 1) % len(pts)]) for i in range(len(pts)))


def r6(x):
    return None if x is None else round(x + 0.0, 6)


# ------------------------------------------------------------------------------------------------ inputs
@dataclass(frozen=True)
class UnderlayChain:
    """The printed chain under a footing (one detail). None = not printed."""
    screed_t: float | None            # m, e.g. '5cm Screed'
    membrane_t: float | None          # m, the printed membrane thickness ('2' on the chain), level chain only
    blinding_t: float | None          # m, blinding line (STRUCTURE): carried for the level chain only
    membrane_extent: str              # 'FOOTING_OUTLINE' (the detail ends membrane and screed at the footing faces)
    membrane_product: str | None      # printed product / system (None = not printed -> procurement HELD)
    source: str


@dataclass(frozen=True)
class SideDetails:
    """Side-face treatment readings by the governing detail. selected: None while the level condition is unprinted."""
    single: str | None                # e.g. 'LIQUID_2_LAYERS' on perimeter x H (detail A)
    double: str | None                # e.g. 'SHEET_MEMBRANE' on perimeter x (H + screed + membrane) (detail B)
    selected: str | None              # 'single' / 'double' / None (HELD)
    why_held: str = ""


@dataclass(frozen=True)
class Contact:
    """A footing face against another concrete member over (length x height), not in contact with earth."""
    with_id: str
    length_m: float
    height_m: float | None            # None = level not printed -> the deduction is HELD
    status: str
    note: str = ""


@dataclass
class Footing:
    id: str
    tags: tuple                       # schedule types printed in / at the outline
    points: list                      # outline polygon
    unit: str
    H: float | None                   # printed depth (schedule), m
    rows_separately_m2: float | None = None   # two-tag outline: sum of the rows' L x W (reading B)
    contacts: tuple = ()
    projection_m: float = 0.0         # must be 0: the blinding projection is the blinding line's
    upturn_m: float = 0.0             # must be 0 unless a detail prints one on the side reading


@dataclass
class Component:
    element: str
    item: str
    unit: str
    qty: float | None
    status: str
    basis: str
    low: float | None = None
    high: float | None = None
    readings: dict = field(default_factory=dict)
    held_why: str = ""

    def row(self):
        return {"element": self.element, "item": self.item, "unit": self.unit, "qty": r6(self.qty),
                "status": self.status, "low": r6(self.low), "high": r6(self.high),
                "readings": {k: r6(v) for k, v in self.readings.items()}, "basis": self.basis,
                "held_why": self.held_why}


# ------------------------------------------------------------------------------------------------ footings
def _check_chain(chain: UnderlayChain):
    if chain.membrane_extent != "FOOTING_OUTLINE":
        raise RefusedError(f"membrane extent {chain.membrane_extent!r}: only a printed 'footing outline' extent is "
                           "supported; anything wider is the blinding's projection (STRUCTURE)")


def footing_components(f: Footing, chain: UnderlayChain, side: SideDetails) -> list:
    """Membrane under, protection screed, side faces and procurement for ONE drawn footing outline."""
    _check_chain(chain)
    if f.projection_m:
        raise RefusedError(f"{f.id}: a projection {f.projection_m} m beyond the footing is the BLINDING line "
                           "(STRUCTURE): the blinding area is never the membrane area")
    if f.upturn_m:
        raise RefusedError(f"{f.id}: an upturn of {f.upturn_m} m on a footing membrane: UP-WP-003 is scoped to "
                           f"{', '.join(UPTURN_SCOPE_UP_WP_003)}; a footing side is covered only as a printed detail "
                           "reading (side faces), never by the 0.20 m wet-area upturn")
    pts = to_m(f.points, f.unit)
    A, P = area(pts), perimeter(pts)
    if A > 400.0:
        raise RefusedError(f"{f.id}: outline area {A:.1f} m2 is not an isolated footing (unit?)")
    out = []
    two_tags = len(set(f.tags)) > 1
    el = f"FTG:{f.id}"

    # 1. membrane under the footing
    if two_tags:
        lo, hi = sorted([A, f.rows_separately_m2 if f.rows_separately_m2 is not None else A])
        why = (f"one outline carries {len(set(f.tags))} schedule tags {'+'.join(sorted(set(f.tags)))}: readings "
               "'outline' and 'rows separately' (designer item), never one picked")
        if f.rows_separately_m2 is None:
            why += "; the rows-separately reading is missing"
        out.append(Component(el, "WP.FOOTING_MEMBRANE", "m2", None, HELD, "plan of the outline vs rows separately",
                             lo, hi, {"outline": A, "rows_separately": f.rows_separately_m2}, why))
    elif chain.membrane_t is None and chain.screed_t is None:
        out.append(Component(el, "WP.FOOTING_MEMBRANE", "m2", None, HELD, "no underlay printed", held_why=(
            "no membrane / screed printed under the footing: scope UNKNOWN, never assumed")))
    else:
        out.append(Component(el, "WP.FOOTING_MEMBRANE", "m2", A, DC,
                             f"installed = outline area, one layer ({chain.source})"))

    # 2. protection screed over the membrane (under the footing)
    if chain.screed_t is None:
        out.append(Component(el, "SCREED.FOOTING_PROTECTION", "m3", None, HELD, "screed thickness not printed",
                             held_why="screed thickness not printed"))
    elif two_tags:
        lo_a, hi_a = out[0].low, out[0].high
        out.append(Component(el, "SCREED.FOOTING_PROTECTION", "m2", None, HELD, "follows the held outline",
                             lo_a, hi_a, held_why=out[0].held_why))
        out.append(Component(el, "SCREED.FOOTING_PROTECTION", "m3", None, HELD, "follows the held outline",
                             lo_a * chain.screed_t, hi_a * chain.screed_t, held_why=out[0].held_why))
    else:
        out.append(Component(el, "SCREED.FOOTING_PROTECTION", "m2", A, DC, "outline area"))
        out.append(Component(el, "SCREED.FOOTING_PROTECTION", "m3", A * chain.screed_t, DC,
                             f"outline area x {chain.screed_t} m printed"))

    # 3. side faces (detail-dependent)
    out.append(_side(f, el, P, chain, side, two_tags))

    # 4. procurement
    out.append(procurement(el, chain))
    return out


def _side(f, el, P, chain, side, two_tags):
    if f.H is None or two_tags:
        return Component(el, "WP.FOOTING_SIDES", "m2", None, HELD, "footing depth not established",
                         held_why="footing depth not established (no schedule row / two tags)")
    known = [c for c in f.contacts if c.height_m is not None]
    open_c = [c for c in f.contacts if c.height_m is None]
    ded_a = sum(c.length_m * min(c.height_m, f.H) for c in known)
    readings = {}
    if side.single:
        readings["single:" + side.single] = P * f.H - ded_a
    if side.double:
        hb = f.H + (chain.screed_t or 0.0) + (chain.membrane_t or 0.0)
        ded_b = sum(c.length_m * min(c.height_m, hb) for c in known)
        if chain.screed_t is None or chain.membrane_t is None:
            readings["double:" + side.double] = None
        else:
            readings["double:" + side.double] = P * hb - ded_b
    basis = (f"perimeter {P:.4f} m x height by detail; contacts deducted: "
             + ", ".join(f"{c.with_id} {c.length_m:.4f} x {c.height_m} ({c.status})" for c in known))
    vals = [v for v in readings.values() if v is not None]
    if side.selected in ("single", "double") and readings.get(
            f"{side.selected}:{getattr(side, side.selected)}") is not None and not open_c:
        q = readings[f"{side.selected}:{getattr(side, side.selected)}"]
        return Component(el, "WP.FOOTING_SIDES", "m2", q, DC, basis, readings=readings)
    why = side.why_held or "governing detail not selected"
    if open_c:
        why += "; contact height not printed at " + ", ".join(c.with_id for c in open_c)
    return Component(el, "WP.FOOTING_SIDES", "m2", None, HELD, basis,
                     min(vals) if vals else None, max(vals) if vals else None, readings, why)


def procurement(el, chain):
    if not chain.membrane_product:
        return Component(el, "WP.FOOTING_MEMBRANE_PROCUREMENT", "rolls", None, HELD, "UP-WP-MAT-001",
                         held_why="PRODUCT_NOT_PRINTED: membrane product / system not printed; rolls and laps only "
                                  "by UP-WP-001 / -002 / -005 / UP-WP-LAY-001 for a printed sheet membrane")
    return Component(el, "WP.FOOTING_MEMBRANE_PROCUREMENT", "rolls", None, HELD, "UP-WP-LAY-001",
                     held_why=f"product printed ({chain.membrane_product}): layout by UP-WP-LAY-001 in the "
                              "integration package (not computed by this research piece)")


# ------------------------------------------------------------------------------------------------ lift pit
@dataclass
class LiftPit:
    id: str
    base_points: list
    envelope_points: list             # outer face of the pit ring incl. any column projecting beyond it
    unit: str
    H: float | None                   # base (footing) depth, printed (schedule)
    screed_t: float | None            # printed under the base
    pit_height_m: float | None        # base top to the top of the waterproofed wall face; None = not printed
    board_printed: bool = True


def lift_pit_components(p: LiftPit) -> list:
    base = to_m(p.base_points, p.unit)
    env = to_m(p.envelope_points, p.unit)
    Ab, Pb, Ae, Pe = area(base), perimeter(base), area(env), perimeter(env)
    if Ae >= Ab - TOL:
        raise RefusedError(f"{p.id}: pit envelope {Ae:.3f} m2 not inside the base {Ab:.3f} m2")
    el = f"LIFT:{p.id}"
    out = []
    held_h = "pit height not printed ('as per lift manufacturer'): wall parts HELD, never 0"
    if p.H is None or p.screed_t is None:
        out.append(Component(el, "WP.LIFT_PIT_MEMBRANE_FIXED", "m2", None, HELD, "base depth / screed not printed",
                             held_why="base depth or screed thickness not printed"))
        side = None
    else:
        side = Pb * (p.H + p.screed_t)
        fixed = Ab + side + (Ab - Ae)
        out.append(Component(el, "WP.LIFT_PIT_MEMBRANE_FIXED", "m2", fixed, DC,
                             f"soffit {Ab:.3f} + sides {Pb:.3f} x ({p.H} + {p.screed_t}) = {side:.3f} + top outside "
                             f"the envelope {Ab:.3f} - {Ae:.3f} = {Ab - Ae:.3f}"))
    if p.pit_height_m is None:
        out.append(Component(el, "WP.LIFT_PIT_MEMBRANE_WALLS", "m2", None, HELD, f"envelope {Pe:.3f} m x h",
                             readings={"per_m_height": Pe}, held_why=held_h))
    else:
        out.append(Component(el, "WP.LIFT_PIT_MEMBRANE_WALLS", "m2", Pe * p.pit_height_m, DC,
                             f"envelope {Pe:.3f} m x {p.pit_height_m} m"))
    if p.board_printed:
        if side is None:
            out.append(Component(el, "WP.LIFT_PIT_BOARD_FIXED", "m2", None, HELD, "base depth / screed not printed",
                                 held_why="base depth or screed thickness not printed"))
        else:
            out.append(Component(el, "WP.LIFT_PIT_BOARD_FIXED", "m2", side + (Ab - Ae), DC,
                                 "sides + top outside the envelope (no board under the base)"))
        if p.pit_height_m is None:
            out.append(Component(el, "WP.LIFT_PIT_BOARD_WALLS", "m2", None, HELD, f"envelope {Pe:.3f} m x h",
                                 readings={"per_m_height": Pe}, held_why=held_h))
        else:
            out.append(Component(el, "WP.LIFT_PIT_BOARD_WALLS", "m2", Pe * p.pit_height_m, DC,
                                 f"envelope {Pe:.3f} m x {p.pit_height_m} m"))
    if p.screed_t is None:
        out.append(Component(el, "SCREED.LIFT_PIT_BASE", "m3", None, HELD, "screed thickness not printed",
                             held_why="screed thickness not printed"))
    else:
        out.append(Component(el, "SCREED.LIFT_PIT_BASE", "m2", Ab, DC, "base area"))
        out.append(Component(el, "SCREED.LIFT_PIT_BASE", "m3", Ab * p.screed_t, DC, f"base area x {p.screed_t}"))
    return out


# ------------------------------------------------------------------------------------------------ totals
def totals(components) -> dict:
    """Per (item, unit): measured (DRAWING-CONFIRMED) sum, and the HELD components listed apart with their bounds.
    HELD is never added as 0; a HELD component without bounds keeps the line's held bound open (None)."""
    res = {}
    for c in components:
        k = f"{c.item}|{c.unit}"
        t = res.setdefault(k, {"measured": 0.0, "measured_n": 0, "held": [], "held_low": 0.0, "held_high": 0.0,
                               "held_open": False})
        if c.status == DC:
            t["measured"] += c.qty
            t["measured_n"] += 1
        else:
            t["held"].append(c.element)
            if c.low is None or c.high is None:
                t["held_open"] = True
            else:
                t["held_low"] += c.low
                t["held_high"] += c.high
    for t in res.values():
        t["measured"] = r6(t["measured"])
        t["held_low"] = None if t["held_open"] else r6(t["held_low"])
        t["held_high"] = None if t["held_open"] else r6(t["held_high"])
    return res
