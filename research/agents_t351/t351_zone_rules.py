"""T-351 rules: wall tile ZONES of kitchens, laundries and pantries (BOQ family B4-02), any villa.

Research module (unwired). Pure functions, no I/O. It decides, face by face, which tile zone a kitchen / laundry /
pantry wall face carries and under which evidence, and whether that zone is a NEW quantity (B4-02) or a face the
wall-tile family (B4-01, FIN.WALL.TILE) already carries.

Evidence order (ERS s.2.2; UP-FIN-WALL-001 precedence):
  1. a tile band / height printed on a drawing, schedule or detail for that room or face (PRINTED);
  2. the owner rules: a CLOSED wet room (UP-WET-001 wet codes KITCHEN / PANTRY / LAUNDRY / IRONING / BATHROOM) is
     tiled FULL HEIGHT on every wall face (UP-FIN-WALL-001, height Q-48 A); an OPEN (American) pantry tiles its
     installation's HOST walls, each whole, full height, and nothing on an open edge (UP-PANTRY-001 .. 004);
  3. otherwise (a kitchen / pantry that the owner wet scope does not reach, e.g. one opening onto a dry open plan
     without a zone extent): a splashback band only where printed, else HELD by name. Never a default band height.

Rules (research, proposed; scope every villa; provenance T-351):
  R-T351-1  A tile zone's band (bottom, top) comes from a printed source or an owner rule; a band with no source, or a
            'typical' / 'default' source, is refused (no 0.60 m splashback is ever assumed).
  R-T351-2  Under the owner wet scope the zone of a closed kitchen / laundry / pantry IS the full-height wall tile:
            each such face is carried once, by its FIN.WALL.TILE line; B4-02 books it as BOUND_TO_WALL_TILE with
            that line id and adds 0 faces. A face carried by two tile lines (B4-01 and B4-02) is refused.
  R-T351-3  A HELD zone (no band, no height) carries no m2 (blank, never 0); a held face written as 0 is refused.
  R-T351-4  An opening is deducted only for its part inside the band [bottom, top] (a window sill above the band
            top deducts nothing); each opening once per face.
  R-T351-5  Under a tiled zone the face carries no paint and its plaster is the tile backing (UP-FIN-PAINT-001
            substrate); the reduction is NAMED per face for the integration, never applied here.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

WET_CODES = ("BATHROOM", "KITCHEN", "PANTRY", "IRONING", "LAUNDRY")  # UP-WET-001 1.1.0 wet_codes
ZONE_ROOM_CODES = ("KITCHEN", "PANTRY", "LAUNDRY")                    # family B4-02
UNIT_FACTOR = {"m": 1.0, "mm": 0.001, "cm": 0.01}
REFUSED_BAND_SOURCES = ("", "default", "typical", "assumed", "practice", "convention")


class ZoneError(ValueError):
    """A refused input or result (the message names the rule)."""


def seg_length(p0, p1, unit: str) -> float:
    """Length of a drawn face segment in metres; mirror / rotation invariant; the unit must be named."""
    if unit not in UNIT_FACTOR:
        raise ZoneError(f"unit {unit!r} not named (m / cm / mm): refused, never guessed")
    return math.hypot(p1[0] - p0[0], p1[1] - p0[1]) * UNIT_FACTOR[unit]


@dataclass(frozen=True)
class Opening:
    opening_id: str
    width_m: float
    sill_m: float      # 0.0 for a door
    head_m: float


@dataclass(frozen=True)
class Face:
    face_id: str
    length_m: float
    openings: tuple = ()
    open_edge: bool = False        # no wall: an open side toward a dry space
    host: bool | None = None       # True: an installation (counter / sink / cabinets) is fixed along it; None: not read


@dataclass(frozen=True)
class Band:
    bottom_m: float
    top_m: float | None            # None = height not established (HELD)
    source: str                    # printed drawing ref, or the owner rule / answer id
    status: str                    # DRAWING-CONFIRMED / ASSUMED — OWNER-APPROVED / HELD
    held_item: str = ""


@dataclass
class FaceZone:
    room: str
    code: str
    face_id: str
    length_m: float
    zone: str                      # FULL_HEIGHT / HOST_FULL_WALL / SPLASHBACK_PRINTED / NONE_OPEN_EDGE / NOT_HOST / HELD
    basis: str
    band_bottom_m: float | None
    band_top_m: float | None
    deductions: list = field(default_factory=list)   # (opening_id, m2)
    net_m2: float | None = None
    status: str = "HELD"
    held_item: str = ""
    carrier: str = ""              # BOUND_TO_WALL_TILE:<line id> / NEW_B4_02 / NO_LINE / NONE
    paint_under_zone: str = ""
    plaster_under_zone: str = ""


def check_band(band: Band) -> None:
    """R-T351-1: a band needs a named, non-default source; a top without a source is refused."""
    if band.source.strip().lower() in REFUSED_BAND_SOURCES or any(
            w in band.source.lower() for w in ("default", "typical band", "assumed")):
        raise ZoneError(f"R-T351-1: band source {band.source!r} refused (printed source or owner rule only)")
    if band.top_m is not None and band.top_m <= band.bottom_m:
        raise ZoneError("R-T351-1: band top not above its bottom")
    if band.top_m is None and band.status != "HELD":
        raise ZoneError("R-T351-3: a band with no top must be HELD")


def deduct(face: Face, bottom: float, top: float):
    """R-T351-4: each opening once, only its part inside [bottom, top]."""
    seen, out = set(), []
    for o in face.openings:
        if o.opening_id in seen:
            raise ZoneError(f"R-T351-4: opening {o.opening_id} twice on face {face.face_id}")
        seen.add(o.opening_id)
        h = min(o.head_m, top) - max(o.sill_m, bottom)
        out.append((o.opening_id, round(o.width_m * h, 6) if h > 0 else 0.0))
    return out


def decide_room(room: str, code: str, closed: bool, faces, *, owner_band: Band | None = None,
                printed_band: Band | None = None, wall_tile_line: str = "") -> list[FaceZone]:
    """Zone of every face of one kitchen / laundry / pantry.

    closed        the room is enclosed by walls and doors only (UP-WET-001 precondition); False for an open pantry
    owner_band    the owner full height (bottom 0, top = Q-48 A height, or top None = HELD by name)
    printed_band  a tile band printed for this room (governs; UP-FIN-WALL-001 precedence)
    wall_tile_line the FIN.WALL.TILE line that carries this room's tiled faces ('' = none: NO_LINE)
    """
    if code not in ZONE_ROOM_CODES:
        raise ZoneError(f"{room}: code {code} is not a B4-02 room (kitchen / laundry / pantry)")
    out = []
    if printed_band is not None:
        check_band(printed_band)
        band, basis, mode = printed_band, f"printed tile band ({printed_band.source})", "SPLASHBACK_PRINTED"
    elif code in WET_CODES and (closed or code == "PANTRY"):
        if owner_band is None:
            raise ZoneError(f"{room}: owner wet scope applies but no owner height record was given (UP-PANTRY-004 /"
                            " UP-FIN-WALL-001: the height is never assumed)")
        check_band(owner_band)
        band = owner_band
        if closed:
            basis, mode = "UP-WET-001 closed wet room: full-height wall tile (UP-FIN-WALL-001, Q-48 A)", "FULL_HEIGHT"
        else:
            basis, mode = "UP-PANTRY-001..004 open pantry: host walls whole, open edge nothing", "HOST_FULL_WALL"
    else:
        band, basis, mode = None, "no printed band, owner wet scope not established for this face", "HELD"
    for f in faces:
        z = FaceZone(room, code, f.face_id, round(f.length_m, 6), mode, basis, None, None)
        if f.open_edge:
            z.zone, z.status, z.carrier, z.basis = "NONE_OPEN_EDGE", "ASSUMED — OWNER-APPROVED", "NONE", \
                "UP-PANTRY-002 / UP-WET-001 never: an open edge tiles nothing"
            out.append(z)
            continue
        if mode == "HOST_FULL_WALL" and f.host is not True:
            if f.host is None:
                z.zone, z.held_item = "HELD", "UP-PANTRY-003: host status of this wall not read (owner review)"
                z.status = "HELD"
            else:
                z.zone, z.status, z.carrier = "NOT_HOST", "ASSUMED — OWNER-APPROVED", "NONE"
            out.append(z)
            continue
        if band is None:
            z.held_item = "TILE_BAND_NOT_PRINTED: no printed band and no owner rule reaching this face"
            out.append(z)
            continue
        z.band_bottom_m = band.bottom_m
        z.band_top_m = band.top_m
        if band.top_m is None:
            z.status, z.held_item = "HELD", band.held_item or "tile top not established"
        else:
            z.deductions = deduct(f, band.bottom_m, band.top_m)
            gross = f.length_m * (band.top_m - band.bottom_m)
            z.net_m2 = round(gross - sum(d for _, d in z.deductions), 6)
            z.status = band.status
        if mode in ("FULL_HEIGHT", "HOST_FULL_WALL"):
            z.carrier = f"BOUND_TO_WALL_TILE:{wall_tile_line}" if wall_tile_line else "NO_LINE"
        else:
            z.carrier = "NEW_B4_02"
        z.paint_under_zone = "NONE (no paint on a tiled face, UP-FIN-PAINT-001)"
        z.plaster_under_zone = "TILE BACKING to the zone top (UP-FIN-PAINT-001 substrate), not ordinary plaster"
        out.append(z)
    return out


def check_results(zones, wall_tile_faces: dict | None = None) -> None:
    """R-T351-2 / -3: held carries no figure, a valued zone carries one; no face in two tile lines."""
    seen = {}
    for z in zones:
        if z.status == "HELD" and z.net_m2 is not None:
            raise ZoneError(f"R-T351-3: held face {z.face_id} carries a figure ({z.net_m2})")
        if z.status != "HELD" and z.zone not in ("NONE_OPEN_EDGE", "NOT_HOST") and z.net_m2 is None:
            raise ZoneError(f"R-T351-3: valued face {z.face_id} has no figure")
        key = (z.room, z.face_id)
        if key in seen:
            raise ZoneError(f"R-T351-2: face {z.face_id} zoned twice")
        seen[key] = z
        if wall_tile_faces is not None and z.carrier == "NEW_B4_02" and key in wall_tile_faces:
            raise ZoneError(f"R-T351-2: face {z.face_id} is already on wall-tile line {wall_tile_faces[key]}: "
                            "a B4-02 band on it would count it twice")
        if wall_tile_faces is not None and z.carrier.startswith("BOUND_TO_WALL_TILE:"):
            line = z.carrier.split(":", 1)[1]
            if wall_tile_faces.get(key) not in (line, None):
                raise ZoneError(f"R-T351-2: face {z.face_id} bound to {line} but the ledger has {wall_tile_faces[key]}")


def room_total(zones):
    """Sum of valued faces; None if any tiled face is HELD (a total with a held part is not a figure)."""
    vals = [z for z in zones if z.zone not in ("NONE_OPEN_EDGE", "NOT_HOST")]
    if any(z.net_m2 is None for z in vals):
        return None
    return round(sum(z.net_m2 for z in vals), 4)
