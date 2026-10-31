"""T-369: B8-04 shower floor and tanking, as rules any villa can use (research module, unwired).

Physical elements (ERS s.2.1):
  * SHOWER ZONE: the floor area wetted by a shower, bounded by what the drawings print: a tray outline (tray symbol), or a
    screen / curtain line across the room with the end walls (walk-in zone), with its mixer and floor drain.
  * SHOWER FLOOR MEMBRANE: the waterproofing layer under that zone. Under UP-WP-004 1.0.0 (owner-confirmed, rule library
    1.4.0: "the shower's floor in m2 and the same upturn ... value SAME_AS_THE_WET_ROOM_FLOOR") it is the SAME layer as the
    wet-room floor membrane B8-01 of the room the shower stands in: never a second layer on top (double count 0), unless a
    detail prints a separate shower layer.
  * SHOWER WALL TANKING: membrane taken up the walls the shower zone touches ABOVE the wet-room upturn (B8-03, 0.20 m,
    UP-WP-UPTURN-015). Its height is printed in a detail, or set by an owner rule. Owner Q-40 A (2026-10-19 20:45): no
    extra shower tanking where the wet area is fully tiled (Q-48 A: wet-room wall tiles to the underside of the decor
    ceiling). With neither a printed height nor that owner rule's condition met, the tanking is HELD; it is never a
    default height and never 0 by omission.

Statuses: WORKFLOW_CONTROLS s.5. A HELD / UNKNOWN quantity is None, never 0.0. A decided NONE (owner rule) is 0.0 with
status ASSUMED - OWNER-APPROVED and its source, so it stays distinguishable from a measured zero.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

VERIFIED = "VERIFIED"
DC = "DRAWING-CONFIRMED"
OA = "ASSUMED - OWNER-APPROVED"
HELD = "HELD"
UNKNOWN = "UNKNOWN"

# shower kinds
TRAY = "TRAY"                    # a tray symbol (outline with the drain / diagonal) is drawn
WALK_IN = "WALK_IN_SCREENED"     # a screen / curtain line closes a zone of the room, mixer inside it
TEXT = "SHOWER_BY_TEXT"          # the plan prints SHOWER / شاور / دش at a zone
NOT_SHOWER = "NOT_A_SHOWER"      # a bath tub (or nothing) without a shower mark
MIXER_ONLY = "UNKNOWN_MIXER_ONLY"  # a wall mixer symbol with no tray, screen or text: not counted as a shower

UPTURN_M = 0.20                  # UP-WP-UPTURN-015 (owner Q-35 C); the B8-03 line owns it
Q40A = "OWNER_QUESTIONS_ANSWERED.md Q-40 A (2026-10-19 20:45): no extra shower tanking, wet areas fully tiled"
Q48A = "OWNER_QUESTIONS_ANSWERED.md Q-48 A: wet-room wall tiles to the underside of the decor ceiling"
UPWP004 = "UP-WP-004 1.0.0 (rule library 1.4.0, owner-confirmed): shower floor = the wet-room floor, same upturn"

_UNIT = {"m": 1.0, "mm": 0.001, "cm": 0.01}


class RefusedError(ValueError):
    """An input the standard forbids (a default height, a shower floor added on top, a bath taken as a shower, ...)."""


def to_m(value, unit: str) -> float:
    """A printed length in an explicit unit -> metres; a bare number without a unit is refused."""
    if unit not in _UNIT:
        raise RefusedError(f"unit {unit!r} not printed / not supported: a length needs its unit")
    if value is None:
        raise RefusedError("no value: a missing dimension is HELD by the caller, never converted")
    v = float(value) * _UNIT[unit]
    if v <= 0:
        raise RefusedError(f"impossible length {value} {unit}")
    return v


@dataclass(frozen=True)
class Evidence:
    """What one source prints for one candidate shower (by symbol / text, never by inference)."""
    tray_symbol: bool = False
    screen_line: bool = False
    mixer_symbol: bool = False
    shower_text: bool = False
    bath_tub: bool = False
    floor_drain: bool = False
    source: str = ""


def classify(ev: Evidence) -> str:
    """Kind of the candidate. A bath tub alone is NOT a shower; a mixer alone is UNKNOWN (never counted)."""
    if ev.tray_symbol:
        return TRAY
    if ev.screen_line and ev.mixer_symbol:
        return WALK_IN
    if ev.shower_text:
        return TEXT
    if ev.bath_tub:
        return NOT_SHOWER
    if ev.mixer_symbol or ev.screen_line:
        return MIXER_ONLY
    return NOT_SHOWER


def is_shower(kind: str) -> bool:
    return kind in (TRAY, WALK_IN, TEXT)


def refuse_bath_as_shower(ev: Evidence) -> None:
    if ev.bath_tub and not is_shower(classify(ev)):
        raise RefusedError("a bath tub without a printed shower mark is not a shower (B8-04 refused)")


@dataclass
class Extent:
    area_m2: Optional[float]
    status: str
    basis: str


def floor_extent(kind: str, tray_dims=None, zone_depth=None, zone_width=None, unit: str = "m") -> Extent:
    """Shower-zone floor area from PRINTED dimensions only (tray L x W, or walk-in depth x room width).
    Nothing printed -> HELD (None). Never scaled from a drawing whose notes say 'do not scale'."""
    if not is_shower(kind):
        raise RefusedError(f"{kind}: no shower, no shower floor extent")
    if kind == TRAY and tray_dims is not None:
        a, b = (to_m(x, unit) for x in tray_dims)
        return Extent(round(a * b, 6), DC, f"printed tray {tray_dims[0]} x {tray_dims[1]} {unit}")
    if kind in (WALK_IN, TEXT) and zone_depth is not None and zone_width is not None:
        d, w = to_m(zone_depth, unit), to_m(zone_width, unit)
        return Extent(round(d * w, 6), DC, f"printed zone {zone_depth} x {zone_width} {unit}")
    return Extent(None, HELD, "shower-zone dimensions not printed (tray / screen line not dimensioned)")


@dataclass
class WallRun:
    length_m: Optional[float]
    status: str
    basis: str


def walls_touched(sides=None, unit: str = "m") -> WallRun:
    """m.l of wall the shower zone touches: the printed lengths of the zone sides that lie on a wall face.
    `sides` = list of (printed length, on_wall: bool); None or any missing length -> HELD."""
    if sides is None:
        return WallRun(None, HELD, "zone sides on walls not printed")
    total = 0.0
    for length, on_wall in sides:
        if not on_wall:
            continue
        if length is None:
            return WallRun(None, HELD, "a zone side on a wall has no printed length")
        total += to_m(length, unit)
    return WallRun(round(total, 6), DC, "printed zone sides on wall faces")


@dataclass
class Tanking:
    area_m2: Optional[float]
    status: str
    basis: str


def tanking(walls: WallRun, printed_height=None, height_unit: str = "m", owner_q40a: bool = False,
            fully_tiled: Optional[bool] = None, default_height=None) -> Tanking:
    """Membrane above the 0.20 m upturn on the shower walls.
    Order (ERS s.2.2): a height printed in the project's detail first; else the owner rule Q-40 A when its condition
    (wet area fully tiled, Q-48 A) holds; else HELD. A default height is refused."""
    if default_height is not None:
        raise RefusedError("tanking height defaulted: refused (no-assumptions rule; Q-40 asked it and A was answered)")
    if printed_height is not None:
        h = to_m(printed_height, height_unit)
        if h <= UPTURN_M:
            return Tanking(0.0, DC, f"printed height {printed_height} {height_unit} is within the 0.20 m upturn (B8-03)")
        if walls.length_m is None:
            return Tanking(None, HELD, "printed height, but the shower wall run is HELD: " + walls.basis)
        return Tanking(round(walls.length_m * (h - UPTURN_M), 6), DC,
                       f"{walls.length_m} m.l x ({h} - {UPTURN_M}) m printed height above the upturn")
    if owner_q40a:
        if fully_tiled is True:
            return Tanking(0.0, OA, "NONE above the upturn: " + Q40A + "; condition met: " + Q48A)
        if fully_tiled is None:
            return Tanking(None, HELD, "Q-40 A rests on full-height wet-wall tiling; tiling height not established")
        return Tanking(None, HELD, "Q-40 A condition fails (wet walls not fully tiled): height not printed, no rule")
    return Tanking(None, HELD, "no printed tanking height and no owner rule")


@dataclass
class FloorLine:
    extra_m2: Optional[float]
    status: str
    basis: str
    covered_by: list = field(default_factory=list)


def b8_04_floor(room_id: str, b8_01_lines: dict, separate_layer_printed: bool = False,
                add_on_top: bool = False) -> FloorLine:
    """Extra B8-04 floor membrane for a shower in `room_id`, given {room_id: [B8-01 line ids]}.
    Inside a membraned wet room -> 0.0 extra (the shower floor is the room's B8-01 membrane, UP-WP-004 1.0.0).
    A shower in a room with no B8-01 line -> HELD (None): its floor is unmeasured, never 0.
    A shower floor added on top of the room membrane -> refused (double count), unless a detail prints a separate layer
    (then the extra layer is a drawing quantity the caller measures, not this function)."""
    if add_on_top and not separate_layer_printed:
        raise RefusedError("shower floor added on top of the wet-room membrane: double count refused (UP-WP-004)")
    lines = b8_01_lines.get(room_id) or []
    if separate_layer_printed:
        return FloorLine(None, HELD, "a separate shower layer is printed: measure it from that detail", lines)
    if lines:
        return FloorLine(0.0, OA, "inside the room's B8-01 floor membrane: " + UPWP004, lines)
    return FloorLine(None, HELD, "shower in a room without a B8-01 floor membrane line: unmeasured", lines)


def b8_04_upturn(room_id: str, b8_03_lines: dict) -> FloorLine:
    """The shower walls' 0.20 m upturn is the room's B8-03 upturn (same rule): extra 0.0, or HELD if no B8-03 line."""
    lines = b8_03_lines.get(room_id) or []
    if lines:
        return FloorLine(0.0, OA, "inside the room's B8-03 0.20 m upturn: " + UPWP004, lines)
    return FloorLine(None, HELD, "shower in a room without a B8-03 upturn line", lines)


def reconcile_sources(arch: Optional[str], san: Optional[str]) -> str:
    """Per room: the architectural plan's shower kind vs the sanitary sheet's. AGREE / ARCH_ONLY / SAN_ONLY / CONFLICT
    / NONE. Never picks one (the owner's Q-13 B: the plan names the room, the sanitary sheet places the fixtures)."""
    a = arch if arch and is_shower(arch) else None
    s = san if san and is_shower(san) else None
    if a and s:
        return "AGREE" if a == s else "AGREE_SHOWER_KIND_DIFFERS"
    if a:
        return "ARCH_ONLY"
    if s:
        return "SAN_ONLY"
    if (arch == MIXER_ONLY) or (san == MIXER_ONLY):
        return "UNKNOWN"
    return "NONE"
