"""R-T640-1 FINISHES HOLD CENSUS (every villa; research provenance, proposed): every HELD-blank wall / ceiling finish line
of a candidate gets exactly one class, a named cause and, where the evidence allows it, a fix row; nothing is wired here.

Classes (T-640 row, owner directive 2026-11-08 12:40 item 3):
  A_BOUND    a merged, Checker-verified ledger gives the line's area or a bound -> fix row SET HELD-blank -> HELD
             [low, high] (low > 0: the row may also release the low end with a HELD companion; low 0: bound only,
             a HELD 0 .. 0 or a RELEASED 0 is refused, UP-QTY-STATUS-001)
  A_CARRIED  the line's quantity already sits in another line or in a queued integration package that writes the same
             line (an own fix row would double count or collide, overlay R1): no fix row, the carrier is named
  B_HELD     a genuine missing height, level, size or design decision that no merged evidence or owner rule settles:
             stays HELD blank, the cause names the decision / RFI / owner answer that closes it
  C_DRAWING  measurable from the drawing by handle under Q-72 / Q-73: a fix row from the own read; C_PENDING when the
             read was not done in the run (the cause says what is to be read; never a figure)

Physical rules used by the generic finishes calculator (room_finishes):
  plaster coat   face length x height to the structural slab / roof underside (Q-72), every opening deducted in full
                 (Q-73), only on the faces that physically exist; on a tiled face only above the tile top (the band
                 under the tile is spatter dash + levelling render, owner 2026-11-02 wet-area walls)
  paint film     face length x height to the finished ceiling (Q-72), openings in full, never on a tiled face band
                 (owner 2026-11-02): a paint figure on a tiled band is refused
  wall tile      tiled face length x tile top, openings inside the band in full
  window reveal  per side: jambs 2 x d x h + head d x w; sill d x w its own item; d = 0 where the frame is flush with
                 that face (UP-REVEAL-001, R-T326-1)
  door reveal    through the wall: 2 x t x h + t x w (UP-FIN-PLASTER-001)
"""
from __future__ import annotations

from decimal import Decimal

CLASSES = ("A_BOUND", "A_CARRIED", "B_HELD", "C_DRAWING", "C_PENDING")
FIX_CLASSES = ("A_BOUND", "C_DRAWING")
STATUSES = ("VERIFIED", "PARTIALLY VERIFIED", "DRAWING-CONFIRMED", "ASSUMED - OWNER-APPROVED", "HELD", "UNKNOWN")
Q6 = Decimal("0.000001")


class RuleError(Exception):
    pass


def D(x):
    return None if x is None else Decimal(str(x))


def q(x):
    return D(x).quantize(Q6)


def S(x):
    if x is None:
        return None
    s = format(D(x).normalize(), "f")
    return "0" if s in ("-0", "0.0") else s


# ---- census rules ---------------------------------------------------------------------------------------------------

def check_entry(e):
    """one census entry {line_id, item_code, class, cause, sources, fix?}: refusals of R-T640-1."""
    lid = e.get("line_id")
    if e.get("class") not in CLASSES:
        raise RuleError(f"{lid}: unknown class {e.get('class')!r}")
    if not (e.get("cause") or "").strip():
        raise RuleError(f"{lid}: a HELD line needs a named cause (blank cause refused)")
    if not e.get("sources"):
        raise RuleError(f"{lid}: no source cited")
    fix = e.get("fix")
    if e["class"] in FIX_CLASSES:
        if fix is None:
            raise RuleError(f"{lid}: class {e['class']} needs a fix row")
        check_fix(lid, fix)
    elif fix is not None and fix.get("kind") != "RETIRE_CARRIED":
        raise RuleError(f"{lid}: class {e['class']} carries no quantity fix row")
    if e["class"] == "A_CARRIED" and not e.get("carrier"):
        raise RuleError(f"{lid}: A_CARRIED must name its carrier line or package")
    if fix is not None and fix.get("kind") == "RETIRE_CARRIED" and not e.get("carrier"):
        raise RuleError(f"{lid}: a retire needs the carrier line that holds the quantity")


def check_fix(lid, fix):
    """the after state of a fix row: HELD never 0, never a value; a bound must be ordered and sourced."""
    a, b = fix.get("after") or {}, fix.get("before") or {}
    if b.get("class") != "HELD" or b.get("measured_net") is not None or b.get("held_low") is not None \
            or b.get("held_high") is not None:
        raise RuleError(f"{lid}: a T-640 fix row starts from a HELD-blank line (before stated)")
    cls = a.get("class")
    if cls == "HELD":
        if a.get("measured_net") is not None:
            raise RuleError(f"{lid}: HELD with a value refused")
        lo, hi = D(a.get("held_low")), D(a.get("held_high"))
        if lo is None:
            raise RuleError(f"{lid}: a bound needs its low end (0 where only the top is sourced)")
        if lo < 0 or (hi is not None and hi < lo):
            raise RuleError(f"{lid}: bound out of order {lo} .. {hi}")
        if hi is not None and hi == 0:
            raise RuleError(f"{lid}: HELD 0 .. 0 refused (a HELD line set to 0)")
    elif cls == "RELEASED":
        v = D(a.get("measured_net"))
        if v is None or v <= 0:
            raise RuleError(f"{lid}: a HELD line released as 0 / blank refused")
        if not fix.get("companion"):
            raise RuleError(f"{lid}: a released low end needs its HELD companion (the rest of the range)")
    else:
        raise RuleError(f"{lid}: fix row after class {cls!r} not allowed")
    if not fix.get("basis"):
        raise RuleError(f"{lid}: a fix row states its arithmetic basis")


def census_counts(entries):
    out = {c: 0 for c in CLASSES}
    for e in entries:
        out[e["class"]] += 1
    moved = sum(1 for e in entries if e.get("fix"))
    return {"by_class": out, "lines": len(entries), "fix_rows": moved, "stay_held_blank": len(entries) - moved}


# ---- generic finishes calculator (fixture side; every villa) --------------------------------------------------------

def room_finishes(faces, slab_h, ceiling_h, openings, tiled=None, wall_t=None):
    """faces: {face: length}; openings: [{id, face, kind 'window'|'door', w, h, sill?, d_in?, d_out?}];
    tiled: {face: tile_top}; returns plaster / paint / tile / reveal m2 (Decimal, unrounded).
    Openings are deducted in full from every finish band they cut (Q-73)."""
    tiled = tiled or {}
    slab_h, ceiling_h = D(slab_h), D(ceiling_h)
    if ceiling_h > slab_h:
        raise RuleError("finished ceiling above the structural soffit")
    for f in tiled:
        if f not in faces:
            raise RuleError(f"tiled face {f} is not a face of the room")
    plaster = paint = tile = Decimal(0)
    for f, L in faces.items():
        L = D(L)
        if L <= 0:
            raise RuleError(f"face {f} length {L}")
        t = D(tiled.get(f, 0))
        plaster += L * (slab_h - t)
        paint += L * max(ceiling_h - t, Decimal(0))
        tile += L * t
    reveals = {}
    for o in openings:
        w, h = D(o["w"]), D(o["h"])
        if w is None or h is None:
            raise RuleError(f"opening {o.get('id')}: size missing (HELD, never 0)")
        sill = D(o.get("sill", 0))
        t = D(tiled.get(o["face"], 0))
        lo, hi = sill, sill + h
        plaster -= w * max(Decimal(0), min(hi, slab_h) - max(lo, t))
        paint -= w * max(Decimal(0), min(hi, ceiling_h) - max(lo, t))
        tile -= w * max(Decimal(0), min(hi, t) - lo)
        if o["kind"] == "door":
            if wall_t is None:
                raise RuleError(f"door {o['id']}: wall thickness missing")
            reveals[o["id"]] = {"THROUGH": 2 * D(wall_t) * h + D(wall_t) * w}
        else:
            r = {}
            for side, key in (("IN", "d_in"), ("OUT", "d_out")):
                d = D(o.get(key))
                if d is None:
                    raise RuleError(f"window {o['id']} {side}: reveal depth missing (HELD, never 0)")
                r[side] = {"jambs_head": 2 * d * h + d * w, "sill": d * w}
            reveals[o["id"]] = r
    return {"plaster": plaster, "paint": paint, "tile": tile, "reveals": reveals}


def paint_on_face(face, tiled, paint_m2):
    """adverse guard: a paint figure booked on a tiled face band is refused (owner 2026-11-02)."""
    if face in (tiled or {}) and D(paint_m2) > 0:
        raise RuleError(f"paint on the tiled face {face} refused (no paint on tiled faces)")
    return D(paint_m2)
