"""R-T312-1 .. 4: the WALL TILE FACE-TO-LINE LEDGER (research rules, any villa; T-312). Pure Python + shapely, no
drawing access. Nothing here edits an engine module, a rule or knowledge file, a candidate line or a released line:
lane I applies the ledger (a FIN.WALL.TILE integration row).

Provenance: owner rules UP-FIN-WALL-001 (full-height wall porcelain in wet areas), UP-CER-005 (wall ceramic = the
eligible wall less its openings), UP-CER-009 (height per face, never a universal constant), UP-PANTRY-001 .. 004
(an American pantry is a zone; an open edge tiles nothing; full-wall tile on the host walls of the installation; the
height is never assumed), owner answers Q-37 A (the pantry is wet), Q-48 A (tile to the underside of the 0.15 decor
ceiling), Q-55 C (door head 2.20 where none is printed, ASSUMED - OWNER-APPROVED), Q-73 A (full openings, only where
the wall physically exists); merged ledgers T-209 (room nets), T-250 (drawn faces), T-292 (face-to-line, plaster /
paint / tile), T-255 (an opening traced per trade side), T-303 (lesson: deduct only where the opening interrupts the
layer). ENGINEERING_REASONING_STANDARD s.2.1 (physical element first), s.3 (build before deduct), s.4 (rule + test).

PHYSICAL ELEMENT. Wall tile is porcelain / ceramic laid on a WALL FACE: one drawn wall seen from one room, from the
finished floor to the tile top, less what is not wall inside that band (door and window holes). Installed m2 only;
boxes, cuts and waste are procurement (not here).

R-T312-1 SCOPE (which face is tiled):
  * WET room (owner wet list): every drawn wall face is TILED full height (UP-FIN-WALL-001).
  * OPEN PANTRY zone (UP-PANTRY-001, a zone with at least one open edge): a wall face is TILED (whole face, FULL_WALL)
    only when the BACK of a drawn installation run (counter, sink, cabinet run; read from its outline leg by leg) lies
    on it over at least 5 cm (UP-PANTRY-003, host wall); a run's END against a side wall hosts nothing; a wall
    face no installation touches is NOT_TILED (UP-PANTRY-003 exception: never tile the perimeter of an imaginary closed
    pantry); an open edge is NOT_TILED with length 0 of tile (UP-PANTRY-002); a pantry with no installation drawn is
    UNRESOLVED (PANTRY_TILE_WALLS_REQUIRE_OWNER_REVIEW), never "all walls".
  * An ENCLOSED pantry (no open edge) is an ordinary wet room (UP-PANTRY-001 exception).
  * DRY room, EXTERIOR face, open side: never wall tile (TILE_OUT_OF_SCOPE / OPEN_EDGE_TILED refused).
R-T312-2 HEIGHT: every tiled face carries its own height record {value_m, source}; a missing source or a source marked
  as a universal / default constant is refused (UNIVERSAL_HEIGHT, UP-CER-009 / UP-PANTRY-004); a height above 8 m is a
  millimetre input (BAD_UNITS); a height not established keeps the face HELD (blank, never 0).
R-T312-3 OPENINGS: each opening is deducted once per room side (OPENING_TWICE), on the face that hosts it, by its part
  inside the tiled band [0, H]: door = w x min(head, H); window = w x max(0, min(head, H) - max(sill, 0)). A window
  whose sill is at or above the tile top interrupts no tile: its deduction is 0 and a claimed deduction is refused
  (WINDOW_ABOVE_TILE). A head / sill not established -> the face is HELD (BOUNDED) with its range.
R-T312-4 BINDING AND CLOSURE: a TILED face binds to exactly ONE candidate line of item FIN.WALL.TILE, or is reported
  NO_LINE (a named MISSING line, never 0); a face in two lines is refused (FACE_TWICE). Per room the face pieces
  (TILED + NOT_TILED + open edges) close to the room's walked perimeter (residual named, or CLOSURE refused).
"""
from __future__ import annotations

from shapely.geometry import LineString

RULE_ID = "R-T312-1..4"
TOL_M = 0.002            # per face piece (the T-250 walk closes rooms to 0.0013 m)
HOST_TOL_M = 0.02        # an installation edge within 2 cm of a wall face line abuts it (drafting offset)
HOST_MIN_M = 0.05        # and over at least 5 cm of the face (a corner touch is no host)
MAX_H_M = 8.0
MAX_FACE_M = 200.0

TILED, NOT_TILED, UNRESOLVED, OPEN_EDGE = "TILED", "NOT_TILED", "UNRESOLVED", "OPEN_EDGE"
NO_LINE = "NO_LINE"
TILE = "FIN.WALL.TILE"
WET, PANTRY_OPEN, PANTRY_ENCLOSED, DRY, EXTERIOR = "WET", "PANTRY_OPEN", "PANTRY_ENCLOSED", "DRY", "EXTERIOR"
UNIVERSAL_SOURCES = ("", "DEFAULT", "UNIVERSAL", "CONSTANT", "TYPICAL")


class TileError(ValueError):
    """a ledger row, binding or total the rule refuses (the code is the first word of the message)."""


# ---------------------------------------------------------------- R-T312-1 scope

def host_overlap_m(face_xy, runs, tol=HOST_TOL_M):
    """metres of the wall face line (two points) on which the BACK of a drawn installation run lies within tol.
    An installation (counter, sink unit, cabinet run) is read from its drawn outline as its runs (legs): each run is
    its back line, the edge fixed against a wall or a free edge, with the run's depth on the other side. A run's END
    butting a side wall is not a back, so it hosts nothing (a counter's end panel against a side wall makes no host
    wall). Pure geometry: invariant under mirror / rotation / shift of the whole plan."""
    seg = LineString(face_xy)
    if seg.length <= 0:
        raise TileError("NON_POSITIVE: a wall face line of zero length")
    backs = [LineString(r) for r in runs if len(r) == 2]
    if not backs:
        return 0.0
    tot = 0.0
    for b in backs:
        if b.length <= 0:
            raise TileError("NON_POSITIVE: an installation run of zero length")
        # the part of the back line within tol of the face line, measured along the face
        near = b.intersection(seg.buffer(tol, cap_style=2))
        if near.is_empty:
            continue
        # project onto the face direction so a back line at a small skew is not counted longer than the face
        (x0, y0), (x1, y1) = face_xy
        L = seg.length
        ux, uy = (x1 - x0) / L, (y1 - y0) / L
        parts = getattr(near, "geoms", [near])
        for g in parts:
            cs = list(g.coords)
            if len(cs) < 2:
                continue
            ts = [(cx - x0) * ux + (cy - y0) * uy for cx, cy in cs]
            tot += max(0.0, min(max(ts), L) - max(min(ts), 0.0))
    return tot


def face_scope(room_class, piece, host_m=None):
    """-> (scope, rule). piece: 'WALL' (a drawn wall / column face) or 'OPEN' (an open edge, no wall)."""
    if piece == "OPEN":
        return OPEN_EDGE, "UP-PANTRY-002 / open side: no wall, nothing to tile"
    if room_class in (WET, PANTRY_ENCLOSED):
        return TILED, "UP-FIN-WALL-001 full height (wet area)"
    if room_class == PANTRY_OPEN:
        if host_m is None:
            return UNRESOLVED, "UP-PANTRY-003: installation not drawn (PANTRY_TILE_WALLS_REQUIRE_OWNER_REVIEW)"
        if host_m >= HOST_MIN_M:
            return TILED, f"UP-PANTRY-003 FULL_WALL: host wall of the installation ({host_m:.3f} m abutting)"
        return NOT_TILED, "UP-PANTRY-003 exception: no installation on this wall (no imaginary closed pantry)"
    if room_class in (DRY, EXTERIOR):
        return NOT_TILED, "not a wet area: no wall tile"
    raise TileError(f"UNKNOWN_CLASS: {room_class!r}")


def pantry_class(open_edges_m):
    """UP-PANTRY-001: a pantry with an open edge is a zone (OPEN); enclosed on every side it is an ordinary room."""
    return PANTRY_OPEN if (open_edges_m or 0) > TOL_M else PANTRY_ENCLOSED


def check_scope(face):
    """refuse a tiled face the scope rule does not allow."""
    sc = face.get("scope")
    if face.get("piece") == "OPEN" and sc == TILED:
        raise TileError(f"OPEN_EDGE_TILED: {face.get('face_id')}: an open edge tiles nothing (UP-PANTRY-002)")
    if face.get("room_class") in (DRY, EXTERIOR) and sc == TILED:
        raise TileError(f"TILE_OUT_OF_SCOPE: {face.get('face_id')}: a {face.get('room_class')} face is not wall tile")
    if face.get("room_class") == PANTRY_OPEN and sc == TILED and not (face.get("host_m") or 0) >= HOST_MIN_M:
        raise TileError(f"IMAGINARY_PANTRY: {face.get('face_id')}: an open-pantry wall with no installation is not "
                        f"tiled (UP-PANTRY-003 exception)")


# ---------------------------------------------------------------- R-T312-2 height

def check_height(h):
    """h: {'value_m': float | None, 'source': str}. -> value or None (HELD); refuses a universal constant / mm."""
    if h is None:
        raise TileError("UNIVERSAL_HEIGHT: a tiled face without a height record (UP-CER-009 / UP-PANTRY-004)")
    src = (h.get("source") or "").strip().upper()
    if src in UNIVERSAL_SOURCES:
        raise TileError(f"UNIVERSAL_HEIGHT: height source {h.get('source')!r}: a wall tile height is per face from the "
                        f"project, the drawing or the owner, never a universal constant (UP-CER-009, UP-PANTRY-004)")
    v = h.get("value_m")
    if v is None:
        return None
    if v <= 0:
        raise TileError(f"NON_POSITIVE: tile height {v!r}")
    if v > MAX_H_M:
        raise TileError(f"BAD_UNITS: tile height {v!r} is not metres")
    return float(v)


# ---------------------------------------------------------------- R-T312-3 openings

def opening_band(op, H):
    """m2 of one opening inside the tiled band [0, H]; None when a datum is missing (never 0 for unknown)."""
    w = op.get("w")
    if w is None or w <= 0:
        raise TileError(f"NON_POSITIVE: opening {op.get('id')} width {w!r}")
    if w > MAX_FACE_M:
        raise TileError(f"BAD_UNITS: opening {op.get('id')} width {w!r} is not metres")
    if H is None:
        return None
    if op.get("kind") == "door":
        head = op.get("head")
        return None if head is None else w * min(head, H)
    sill, head = op.get("sill"), op.get("head")
    if sill is None or head is None:
        return None
    if head <= sill:
        raise TileError(f"BAD_OPENING: {op.get('id')} head {head} not above sill {sill}")
    return w * max(0.0, min(head, H) - max(sill, 0.0))


def check_claimed_deduction(op, H, claimed_m2):
    """a ledger row's claimed deduction must equal the band part; a window above the tile top deducts nothing."""
    a = opening_band(op, H)
    if a is None:
        return
    if a == 0.0 and claimed_m2 and claimed_m2 > 1e-9:
        raise TileError(f"WINDOW_ABOVE_TILE: {op.get('id')} sill {op.get('sill')} >= tile top {H}: it interrupts no "
                        f"tile, a deduction of {claimed_m2} m2 is refused")
    if abs(a - (claimed_m2 or 0.0)) > 1e-6:
        raise TileError(f"BAD_DEDUCTION: {op.get('id')} claims {claimed_m2} m2, band part {a:.4f}")


def check_openings_once(face_openings):
    """face_openings: [(room, opening_id)] over every tiled face of a room side; an id twice on one side is refused."""
    seen = set()
    for key in face_openings:
        if key in seen:
            raise TileError(f"OPENING_TWICE: {key[1]} deducted twice on the {key[0]} side")
        seen.add(key)


def face_net(length_m, h, openings):
    """-> dict(gross, ded_lo, ded_hi, net_lo, net_hi, status). h: height record; openings: list of opening dicts
    (kind door / window, w, head, sill; a door with 'fallback' True takes the Q-55 C 2.20 head)."""
    if length_m is None or length_m <= 0:
        raise TileError(f"NON_POSITIVE: face length {length_m!r}")
    if length_m > MAX_FACE_M:
        raise TileError(f"BAD_UNITS: face length {length_m!r} is not metres")
    H = check_height(h)
    if H is None:
        return dict(gross=None, ded_lo=None, ded_hi=None, net_lo=None, net_hi=None, status="HELD")
    gross = length_m * H
    lo = hi = 0.0
    held = False
    for op in openings:
        op = dict(op)
        if op.get("kind") == "door" and op.get("head") is None and op.get("fallback"):
            op["head"] = 2.20
        a = opening_band(op, H)
        if a is None:
            held = True
            hi += op["w"] * H
        else:
            lo += a
            hi += a
    hi = min(hi, gross)
    return dict(gross=round(gross, 4), ded_lo=round(lo, 4), ded_hi=round(hi, 4), net_lo=round(gross - hi, 4),
                net_hi=round(gross - lo, 4), status="HELD (BOUNDED)" if held else "DETERMINATE")


# ---------------------------------------------------------------- R-T312-4 binding and closure

def bind(faces, line_of_room):
    """faces: rows with face_id, room, scope; line_of_room: room -> [line ids of FIN.WALL.TILE]. Returns
    {face_id: line id or NO_LINE}; a tiled face that two lines claim is refused."""
    out = {}
    for f in faces:
        if f["scope"] != TILED:
            continue
        ls = line_of_room.get(f["room"]) or []
        if len(ls) > 1:
            raise TileError(f"FACE_TWICE: {f['face_id']} would sit in {len(ls)} wall-tile lines {ls}")
        if f["face_id"] in out:
            raise TileError(f"FACE_TWICE: {f['face_id']} listed twice")
        out[f["face_id"]] = ls[0] if ls else NO_LINE
    return out


def check_line_claims(claims):
    """claims: [(line id, face id)] as a lane I package would book them; one face in two lines is refused."""
    owner = {}
    for line, fid in claims:
        if fid in owner and owner[fid] != line:
            raise TileError(f"FACE_TWICE: {fid} in {owner[fid]} and {line}")
        owner[fid] = line


def room_closure(pieces_m, perimeter_m, named_residual_m=0.0):
    """sum of the room's face pieces (tiled + not tiled + open edges) must equal its walked perimeter."""
    s = sum(pieces_m)
    r = perimeter_m - s - named_residual_m
    if abs(r) > TOL_M * max(1, len(pieces_m)):
        raise TileError(f"CLOSURE: pieces {s:.4f} + named {named_residual_m:.4f} vs perimeter {perimeter_m:.4f} m "
                        f"(residual {r:+.4f})")
    return round(r, 4)


def total(nets, statuses):
    """sum only determinate nets; a HELD net is counted as held (never 0)."""
    det = sum(n for n, s in zip(nets, statuses) if s == "DETERMINATE" and n is not None)
    held = sum(1 for s in statuses if s != "DETERMINATE")
    return round(det, 4), held
