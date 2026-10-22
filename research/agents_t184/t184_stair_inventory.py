"""T-184: every staircase of a villa identified project-wide, chained floor by floor and reconstructed flight by flight.

NOT WIRED: research module, read by no method version (the released default ARCH_TAKEOFF_V2.9 + route G and the V3.0
candidate are untouched). It reads no drawing: its inputs are flight / landing records typed from the drawings (plan,
section, structural slab plan), each with its source. Units: metres, levels in metres (finished levels unless stated).

Why (ENGINEERING_REASONING_STANDARD s.2, s.3; owner teaching case 2026-10-22):
  * a stair is identified by WHERE it is and WHICH LEVELS it joins, never by a name in a contractor's sheet;
  * a flight drawn at the same plan place on the slab plans of two storeys is TWO physical flights when the two drawings
    join different levels (a stacked dog-leg core), and ONE flight only when they join the same levels (the plan above
    shows the flight below through the opening). When either drawing's levels are unknown the pair is UNDETERMINED
    (held), never merged silently (defect D-T184-1 of the released route: the 1F -> 2F flights of a dog-leg were folded
    into the GF -> 1F flights as "drawn again on" the 1F slab plan);
  * a stair continues above a floor only when a flight LEAVING that floor is drawn; a lower plan never implies it;
  * a landing at a floor level inside the floor-slab panel is FLOOR SLAB concrete (once), an intermediate landing is
    stair concrete;
  * an architectural and a structural reading of the same flight that differ are a CONFLICT with both values, never a
    silent pick;
  * concrete: steps n x 1/2 r g w (owner Q-19), waist w x t x hypot(goings x g, goings x r) between the first and the
    last riser line (Q-47 A 'T' = waist), landings L x W x t; an unknown dimension makes that part HELD (None), never 0.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Iterable

LEVEL_TOL = 0.02        # m: two levels are the same level (printed to the centimetre)
SAME_PLACE_SHARE = 0.5  # share of the smaller footprint two drawings must share to be at the same plan place
CHAIN_GAP = 0.60        # m: a flight's top edge and the next flight's foot / landing within this plan gap are connected


# ---------------------------------------------------------------- records
@dataclass
class FlightDrawing:
    """one drawing of one flight on one sheet (architectural plan, structural slab plan or section)."""
    sheet: str
    sheet_kind: str                      # 'ARCH_PLAN' | 'SLAB_PLAN' | 'SECTION'
    box: tuple                           # (x0, y0, x1, y1) in metres, one coordinate frame for every sheet
    z_from: float | None                 # level at the foot (None: not established on this drawing)
    z_to: float | None                   # level at the head
    risers: int | None = None
    going: float | None = None
    width: float | None = None
    source: str = ""


@dataclass
class Flight:
    fid: str
    z_from: float | None
    z_to: float | None
    box: tuple
    drawings: list = field(default_factory=list)
    status: str = "ESTABLISHED"          # ESTABLISHED | UNDETERMINED (levels unknown on a stacked pair)


def _area(b):
    return max(0.0, b[2] - b[0]) * max(0.0, b[3] - b[1])


def _shared(a, b):
    ix = max(0.0, min(a[2], b[2]) - max(a[0], b[0]))
    iy = max(0.0, min(a[3], b[3]) - max(a[1], b[1]))
    sm = min(_area(a), _area(b))
    return 0.0 if sm <= 0 else ix * iy / sm


def _gap(a, b):
    dx = max(0.0, max(a[0], b[0]) - min(a[2], b[2]))
    dy = max(0.0, max(a[1], b[1]) - min(a[3], b[3]))
    return math.hypot(dx, dy)


def same_level(a, b):
    return a is not None and b is not None and abs(a - b) <= LEVEL_TOL


def to_m(value, unit):
    """drawing units to metres (mm / cm / m); any other unit is refused, never guessed."""
    f = {"mm": 0.001, "cm": 0.01, "m": 1.0}.get(unit)
    if f is None:
        raise ValueError(f"unit {unit!r} not supported")
    return value * f


# ---------------------------------------------------------------- 1. physical flights from drawings
def physical_flights(drawings: Iterable[FlightDrawing]):
    """group drawings into physical flights.

    Same physical flight  <=> same plan place (shared footprint >= SAME_PLACE_SHARE) AND the same level range.
    Same place, different level ranges -> different flights (stacked core).
    Same place, a level range unknown on either drawing -> both kept, status UNDETERMINED (held, never merged)."""
    flights: list[Flight] = []
    for d in drawings:
        hit = None
        undetermined = False
        for f in flights:
            if _shared(f.box, d.box) < SAME_PLACE_SHARE:
                continue
            if None in (f.z_from, f.z_to, d.z_from, d.z_to):
                undetermined = True
                continue
            if same_level(f.z_from, d.z_from) and same_level(f.z_to, d.z_to):
                hit = f
                break
        if hit is not None:
            hit.drawings.append(d)
            continue
        f = Flight(f"F{len(flights) + 1:02d}", d.z_from, d.z_to, d.box, [d])
        if undetermined:
            f.status = "UNDETERMINED"
            for g in flights:
                if _shared(g.box, d.box) >= SAME_PLACE_SHARE:
                    g.status = "UNDETERMINED"
        flights.append(f)
    return flights


def released_twin_rule(drawings: Iterable[FlightDrawing]):
    """the released route's twin rule for structural stair signals (concrete_completeness: same layer, same box on
    another sheet -> 'drawn again', one finding), reproduced for the adverse test: levels are ignored."""
    kept: list[Flight] = []
    for d in drawings:
        if any(_shared(k.box, d.box) >= SAME_PLACE_SHARE for k in kept):
            continue
        kept.append(Flight(f"F{len(kept) + 1:02d}", d.z_from, d.z_to, d.box, [d]))
    return kept


# ---------------------------------------------------------------- 2. stairs: flights chained by levels and place
@dataclass
class Landing:
    lid: str
    level: float
    box: tuple
    thickness: float | None
    inside_floor_slab: bool = False      # the outline lies inside a floor-slab panel of that level (structural plan)


def assemble_stairs(flights: list[Flight], landings: list[Landing] = ()):
    """chain flights into staircases: B follows A when B leaves at A's arrival level and B's foot is within CHAIN_GAP
    of A (directly or through a landing at that level). Ids ST-01.. by lowest foot level, then plan x, then y."""
    parent = {f.fid: f.fid for f in flights}

    def root(k):
        while parent[k] != k:
            k = parent[k]
        return k

    for a in flights:
        for b in flights:
            if a is b or not same_level(a.z_to, b.z_from):
                continue
            near = _gap(a.box, b.box) <= CHAIN_GAP or any(
                same_level(l.level, a.z_to) and _gap(l.box, a.box) <= CHAIN_GAP and _gap(l.box, b.box) <= CHAIN_GAP
                for l in landings)
            if near:
                parent[root(b.fid)] = root(a.fid)
    groups: dict[str, list[Flight]] = {}
    for f in flights:
        groups.setdefault(root(f.fid), []).append(f)

    def key(g):
        zs = [f.z_from for f in g if f.z_from is not None]
        return (min(zs) if zs else 1e9, min(f.box[0] for f in g), min(f.box[1] for f in g))

    stairs = []
    for i, g in enumerate(sorted(groups.values(), key=key)):
        g.sort(key=lambda f: (f.z_from if f.z_from is not None else 1e9))
        stairs.append(dict(stair_id=f"ST-{i + 1:02d}", flights=g,
                           levels=sorted({round(z, 3) for f in g for z in (f.z_from, f.z_to) if z is not None})))
    return stairs


def continues_above(stair, level):
    """True only when a flight of this stair LEAVES `level` (drawn); a stair that only arrives there ends there."""
    return any(same_level(f.z_from, level) for f in stair["flights"])


def floors_served(stair, floor_levels):
    """the floor levels the stair reaches (arrives at or leaves), lowest to highest, and where it ends."""
    hit = [z for z in floor_levels if any(same_level(z, f.z_from) or same_level(z, f.z_to) for f in stair["flights"])]
    top = max(hit) if hit else None
    return dict(floors=hit, ends_at=top, continues_above_top=bool(top is not None and continues_above(stair, top)))


# ---------------------------------------------------------------- 3. landing ownership
def landing_owner(landing: Landing, floor_levels):
    """a landing at a floor level whose outline lies inside the floor-slab panel is FLOOR_SLAB concrete (counted once
    in the slab line); every other landing (intermediate level, or a floor-level landing outside any slab panel) is
    STAIR concrete."""
    at_floor = any(same_level(landing.level, z) for z in floor_levels)
    return "FLOOR_SLAB" if at_floor and landing.inside_floor_slab else "STAIR"


# ---------------------------------------------------------------- 4. architectural vs structural reading
def compare_readings(arch: FlightDrawing, struct: FlightDrawing, tol=0.01):
    """differences between two readings of the same flight; each difference keeps BOTH values (no pick)."""
    out = []
    for k in ("risers", "going", "width", "z_from", "z_to"):
        a, s = getattr(arch, k), getattr(struct, k)
        if a is None or s is None:
            continue
        if (k == "risers" and a != s) or (k != "risers" and abs(a - s) > tol):
            out.append(dict(field=k, architectural=a, structural=s, status="CONFLICT",
                            action="record both; the governing reading follows the owner rule for that field "
                                   "(Q-46 A: section counts for risers), never the larger or the freelancer's"))
    return out


# ---------------------------------------------------------------- 5. concrete
def flight_concrete(risers, riser, going, goings, width, waist):
    """steps n x 1/2 r g w (all n wedges, the arrival wedge included; its overlap goes to the intersection ledger) and
    the waist w x t x hypot(goings x g, goings x r). A None input makes that part None (HELD), never 0."""
    steps = None if None in (risers, riser, going, width) else risers * 0.5 * riser * going * width
    wst = None if None in (riser, going, goings, width, waist) else \
        width * waist * math.hypot(goings * going, goings * riser)
    return dict(steps=steps, waist=wst)


def landing_concrete(length, width, thickness, deduct_m2=0.0):
    if None in (length, width, thickness):
        return None
    return (length * width - deduct_m2) * thickness


def stair_total(parts):
    """sum of the measured parts; None parts are listed as held, never added as 0."""
    measured = sum(v for _, v in parts if v is not None)
    held = [k for k, v in parts if v is None]
    return dict(measured_m3=measured, held=held)


# ---------------------------------------------------------------- 6. omission census
def unassigned(drawn: Iterable[FlightDrawing], stairs):
    """drawings that belong to no stair of the inventory (a silent omission if non-empty)."""
    owned = {id(d) for s in stairs for f in s["flights"] for d in f.drawings}
    return [d for d in drawn if id(d) not in owned]


# ---------------------------------------------------------------- 7. owner stair rule as a CHECK (OWNER_RULE_STAIRS S-1)
def owner_rule_check(floor_height, drawn_risers, max_riser=0.16):
    """owner rule risers = ceil(H / max_riser) (computed in millimetres to avoid 4.48 / 0.16 = 28.000000000000004);
    the drawn count governs (S-1): a drawn riser above max_riser is FLAGGED, never changed."""
    h_mm, m_mm = round(floor_height * 1000), round(max_riser * 1000)
    rule = -(-h_mm // m_mm)
    actual = floor_height / drawn_risers
    return dict(rule_risers=rule, drawn_risers=drawn_risers, drawn_riser_m=actual,
                flag=actual > max_riser + 1e-9, governs="DRAWN")
