"""R-T329-1 .. 4: the WET-ROOM PLASTER BACKING under wall tile and the plaster band ABOVE the tile (research rules,
any villa; T-329). Pure Python, no drawing access. Nothing here edits an engine module, a rule or knowledge file, a
candidate line or a released line: lane I applies the ledger (it fills the wet rooms' FIN.PLASTER lines).

Provenance (searched before any question, WORKFLOW_CONTROLS s.4):
  * UP-FIN-PAINT-001 (OWNER_APPROVED, knowledge 1.8.0) logic 'substrate': "the cementitious substrate / plaster behind
    porcelain is its own line" -> the backing EXISTS on every tiled face and is NOT inside the tile or the paint line.
  * owner answer Q-45 B (2026-10-19 21:40; practice values accepted, PROVISIONAL): "wall mortar behind wall tiles
    0.02 m, mix 1:4"; the tile adhesive is its own line (20 kg / 5 m2) -> the physical coat is a 20 mm cement-sand
    1:4 coat, then adhesive, then tile (engine/source/finish_materials_table.py WET_WALL bed 0.02 m reproduces it).
  * owner answers Q-43 (plaster and paint count to 3.65 / 3.35 m) and Q-48 A (wet-wall tile to the underside of the
    0.15 m decor ceiling, the same 3.65 / 3.35 m) -> OWNER MANUAL METHOD: plaster top = tile top, band above = 0.
  * Q-52 C MODIFIED (owner directive 2026-10-20 12:02): plaster and paint heights computed separately per room;
    "plaster may run above the false ceiling while paint stops at it, depending on the specification" + the drawing
    method URBAN-PLASTER-TO-MASONRY-TERMINATION@v1 (plaster to the structural termination) -> DRAWING-DERIVED METHOD:
    the band between the tile top and the soffit is bounded [0, length x decor depth] and HELD until a
    specification says whether plaster runs above the decor ceiling.
  * URBAN-FINISH-EXTRAS-SEPARATE-ITEMS@v1: spatter dash (m2) and reveals are separate items -> neither is in this line.
  * Conflict named, not resolved by preference: ARCH_QUANTITY_TRUTH_V1 plaster_paint() gives a full wet-tiled face
    "neither plaster nor paint (spatter / tile preparation only)"; it is an engine convention, not an owner rule; the
    owner rule UP-FIN-PAINT-001 + Q-45 B governs (ERS s.2.2 rank 3 over an undocumented convention).

PHYSICAL ELEMENT. The backing is the cement-sand coat applied to the block / concrete wall face on which the wall
tile is set: one drawn wall seen from one room, from the finished floor to the tile top, less the holes in that band
(the same holes the tile loses). Installed m2 only; its mortar volume / cement / sand are the procurement of the SAME
layer (finish_materials_table WET_WALL), never a second priced item.

R-T329-1 SCOPE: a backing face exists exactly where the tile ledger has a TILED face (wet room every face, open pantry
  host walls only). Never on an open edge (BACKING_ON_OPEN_SIDE), a NOT_TILED face, a dry or exterior face (that face's
  plaster is the dry family). A tiled face without backing is refused (BACKING_MISSING).
R-T329-2 HEIGHT: the backing top is the tile top of the same face (one height record, same source); the plaster top
  is a separate record per method. Band above the tile = length x max(0, plaster top - tile top) less the window parts
  inside that band. A height without a source or with a universal / default source is refused (UNIVERSAL_HEIGHT); a
  height above 8 m is a millimetre input (BAD_UNITS); a height not established keeps the face HELD (blank, never 0).
R-T329-3 OPENINGS: each opening is deducted from the backing once per room side with the tile ledger's id and the
  tile ledger's band part (BACKING_OPENINGS_DIFFER otherwise); window parts above the tile top come off the band only;
  a reveal (jamb / head / sill surface) is never in the backing or the band (REVEAL_IN_BACKING: T-313 / T-326 own them).
R-T329-4 BINDING AND CLOSURE: the backing and the band of a wet-room face bind to that room's own FIN.PLASTER line (one
  line per room), or NO_LINE (named MISSING); a face in two plaster lines, a band in a dry room's plaster line as well
  (BAND_TWICE), or a backing face in a paint line (PAINT_ON_TILE, UP-FIN-PAINT-001) is refused. Per room the backing
  closes to the tile faces: backing m2 - tile m2 = 0.000 below the tile height (CLOSURE_TO_TILE).
"""
from __future__ import annotations

RULE_ID = "R-T329-1..4"
MAX_H_M = 8.0
MAX_FACE_M = 200.0
EPS_M2 = 1e-4            # 4-dp ledger rounding

TILED, NOT_TILED, OPEN_EDGE = "TILED", "NOT_TILED", "OPEN_EDGE"
NO_LINE = "NO_LINE"
PLASTER, PAINT, TILE = "FIN.PLASTER", "FIN.PAINT", "FIN.WALL.TILE"
UNIVERSAL_SOURCES = ("", "DEFAULT", "UNIVERSAL", "CONSTANT", "TYPICAL")
COAT = {"layer": "cement-sand backing coat under wall tile", "thickness_m": 0.02, "mix": "1:4",
        "source": "owner Q-45 B (2026-10-19 21:40), PROVISIONAL; UP-FIN-PAINT-001 'substrate' own line",
        "status": "ASSUMED — OWNER-APPROVED"}


class BackingError(ValueError):
    """a ledger row, binding or total the rule refuses (the code is the first word of the message)."""


# ---------------------------------------------------------------- R-T329-1 scope

def backing_scope(tile_scope, piece="WALL"):
    """-> True when the face carries a backing coat. tile_scope from the tile ledger (TILED / NOT_TILED / OPEN_EDGE)."""
    if piece == "OPEN" or tile_scope == OPEN_EDGE:
        return False
    if tile_scope == TILED:
        return True
    if tile_scope == NOT_TILED:
        return False
    raise BackingError(f"UNKNOWN_SCOPE: tile scope {tile_scope!r}")


def check_scope(face):
    """face: {'face_id', 'tile_scope', 'piece', 'backing'(bool)}; refuses a backing the tile does not need and a tiled
    face without one."""
    need = backing_scope(face.get("tile_scope"), face.get("piece", "WALL"))
    has = bool(face.get("backing"))
    if has and (face.get("piece") == "OPEN" or face.get("tile_scope") == OPEN_EDGE):
        raise BackingError(f"BACKING_ON_OPEN_SIDE: {face.get('face_id')}: an open side has no wall to coat")
    if has and not need:
        raise BackingError(f"BACKING_OUT_OF_SCOPE: {face.get('face_id')}: a {face.get('tile_scope')} face carries no "
                           f"tile, so no backing (its plaster is the dry family)")
    if need and not has:
        raise BackingError(f"BACKING_MISSING: {face.get('face_id')}: a tiled face sits on a backing coat "
                           f"(UP-FIN-PAINT-001 substrate) - never dropped")
    return need


# ---------------------------------------------------------------- R-T329-2 height

def check_height(h, what="height"):
    """h: {'value_m': float | None, 'source': str} -> value or None (HELD)."""
    if h is None:
        raise BackingError(f"UNIVERSAL_HEIGHT: a {what} without a record (UP-CER-009)")
    src = (h.get("source") or "").strip().upper()
    if src in UNIVERSAL_SOURCES:
        raise BackingError(f"UNIVERSAL_HEIGHT: {what} source {h.get('source')!r}: per face from the drawing, the "
                           f"project or the owner, never a universal constant (UP-CER-009)")
    v = h.get("value_m")
    if v is None:
        return None
    if v <= 0:
        raise BackingError(f"NON_POSITIVE: {what} {v!r}")
    if v > MAX_H_M:
        raise BackingError(f"BAD_UNITS: {what} {v!r} is not metres")
    return float(v)


def _w(op):
    w = op.get("w")
    if w is None or w <= 0:
        raise BackingError(f"NON_POSITIVE: opening {op.get('id')} width {w!r}")
    if w > MAX_FACE_M:
        raise BackingError(f"BAD_UNITS: opening {op.get('id')} width {w!r} is not metres")
    return float(w)


def part_between(op, lo, hi):
    """m2 of one opening between heights lo and hi on its face; None when a datum is missing (never 0)."""
    w = _w(op)
    if hi <= lo:
        return 0.0
    if op.get("kind") == "door":
        head = op.get("head")
        if head is None:
            return None
        return w * max(0.0, min(head, hi) - lo)
    sill, head = op.get("sill"), op.get("head")
    if sill is None or head is None:
        return None
    if head <= sill:
        raise BackingError(f"BAD_OPENING: {op.get('id')} head {head} not above sill {sill}")
    return w * max(0.0, min(head, hi) - max(sill, lo))


def face_backing(length_m, tile_h, plaster_h, openings, correction=False):
    """one face: backing (floor .. tile top) and band (tile top .. plaster top), each less its own opening parts.
    tile_h / plaster_h: height records. correction=True: a NAMED walk-correction piece of the tile ledger (it may be
    negative, it carries no opening) so the room keeps its verified outline. -> dict with backing, band (None = HELD)
    and their deductions."""
    if correction:
        if length_m is None or length_m == 0 or openings:
            raise BackingError(f"BAD_CORRECTION: a correction piece needs a non-zero length and no opening")
    elif length_m is None or length_m <= 0:
        raise BackingError(f"NON_POSITIVE: face length {length_m!r}")
    if abs(length_m) > MAX_FACE_M:
        raise BackingError(f"BAD_UNITS: face length {length_m!r} is not metres")
    for op in openings:
        if op.get("kind") in ("jamb", "head", "sill", "reveal"):
            raise BackingError(f"REVEAL_IN_BACKING: {op.get('id')}: a reveal surface is its own item (T-313 / T-326)")
    H = check_height(tile_h, "tile top")
    P = check_height(plaster_h, "plaster top") if plaster_h is not None else None
    out = {"backing": None, "backing_ded": None, "band": None, "band_ded": None, "held": []}
    if H is None:
        out["held"].append("tile top not established")
        return out
    ded, held = 0.0, False
    for op in openings:
        a = part_between(op, 0.0, H)
        if a is None:
            held = True
        else:
            ded += a
    if held:
        out["held"].append("an opening head / sill not established")
    else:
        out["backing"] = round(length_m * H - ded, 4) + 0.0
        out["backing_ded"] = round(ded, 4)
    if P is None:
        out["held"].append("plaster top not established")
        return out
    top = max(P, H)              # the backing follows the tile; plaster lower than the tile adds no band
    bded, bheld = 0.0, False
    for op in openings:
        a = part_between(op, H, top)
        if a is None:
            bheld = True
        else:
            bded += a
    if bheld:
        out["held"].append("an opening above the tile top not established")
    else:
        out["band"] = round(length_m * (top - H) - bded, 4) + 0.0
        out["band_ded"] = round(bded, 4)
    return out


# ---------------------------------------------------------------- R-T329-3 openings

def check_same_openings(backing_ids, tile_ids):
    """the backing deducts exactly the tile ledger's openings on that room side (same ids, each once)."""
    b, t = list(backing_ids), list(tile_ids)
    if len(b) != len(set(b)):
        raise BackingError(f"OPENING_TWICE: {b}")
    if sorted(b) != sorted(t):
        raise BackingError(f"BACKING_OPENINGS_DIFFER: backing {sorted(b)} vs tile {sorted(t)}")


# ---------------------------------------------------------------- R-T329-4 binding and closure

def bind(face, plaster_line_of_room):
    """the room's own FIN.PLASTER line or NO_LINE; two lines for one room are refused."""
    ls = plaster_line_of_room.get(face["room"]) or []
    if len(ls) > 1:
        raise BackingError(f"FACE_TWICE: {face['face_id']} would sit in {len(ls)} plaster lines {ls}")
    return ls[0] if ls else NO_LINE


def check_claims(claims):
    """claims: [(item_code, line id, room_class of the line's room, face id, component)] as a package would book them.
    component: BACKING or ABOVE_TILE. Refuses a component in two lines, a band in a dry line, backing in paint."""
    owner = {}
    for code, line, line_class, fid, comp in claims:
        if code == PAINT and comp == "BACKING":
            raise BackingError(f"PAINT_ON_TILE: {fid}: a tiled face is never painted (UP-FIN-PAINT-001)")
        if code != PLASTER:
            raise BackingError(f"WRONG_FAMILY: {fid} {comp} in {code}: the backing is a plaster line")
        if comp == "ABOVE_TILE" and line_class not in ("WET", "PANTRY_OPEN", "PANTRY_ENCLOSED"):
            raise BackingError(f"BAND_TWICE: {fid}: the band above the tile belongs to the wet room's own plaster "
                               f"line, not a {line_class} line")
        key = (fid, comp)
        if key in owner and owner[key] != line:
            raise BackingError(f"BAND_TWICE: {fid} {comp} in {owner[key]} and {line}" if comp == "ABOVE_TILE" else
                               f"FACE_TWICE: {fid} {comp} in {owner[key]} and {line}")
        owner[key] = line
    return owner


def closure_to_tile(backing_m2, tile_m2):
    """per room: backing below the tile top equals the tile area (same faces, same holes)."""
    if backing_m2 is None or tile_m2 is None:
        if (backing_m2 is None) != (tile_m2 is None):
            raise BackingError("CLOSURE_TO_TILE: one side HELD, the other a figure (held is never 0)")
        return None
    r = round(backing_m2 - tile_m2, 4)
    if abs(r) > EPS_M2:
        raise BackingError(f"CLOSURE_TO_TILE: backing {backing_m2:.4f} vs tile {tile_m2:.4f} m2 (residual {r:+.4f})")
    return r


def total(values):
    """sum of determinate figures; None (HELD) counted apart, never as 0."""
    det = sum(v for v in values if v is not None)
    return round(det, 4), sum(1 for v in values if v is None)


def mortar_m3(backing_m2, coat=COAT):
    """the same layer's mortar volume (procurement information, Q-45 B PROVISIONAL): area x 0.02."""
    if backing_m2 is None:
        return None
    return round(backing_m2 * coat["thickness_m"], 4)
