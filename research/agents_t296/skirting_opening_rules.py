"""T-296 rules: the SKIRTING OPENING-TO-LINE LEDGER of one room, and the re-adding trail of one skirting BOQ line
(every villa; research only, no engine module, rule file or released line changed).

Physical element (ERS s.2.1): conventional skirting is a strip fixed at the foot of a finished dry wall / column face, at
floor level, along the face (UP-SKIRT-001 1.4.0, UP-CER-002 lm, UP-CER-003). It is built where a finished wall base
exists at floor level, so it is measured from the FACE PIECES of the room's boundary, each with one owner:

  piece kind        skirted?                                                         rule
  WALL, COLUMN      yes (dry room, wall base owned by the skirting)                  UP-SKIRT-001 eligible
  DOOR, PASSAGE     no: no wall base at floor level; deducted ONCE by opening id     UP-CER-003
  WINDOW            the wall continues under a sill: skirted when the sill is         UP-SKIRT-001 1.4.0 windows
                    ESTABLISHED above the floor (sill_m > FLOOR_GLAZING_MAX_SILL_M);
                    not skirted when the sill is at the floor (floor glazing);
                    sill not established -> HELD range [0, length], never certain
  TILED_WALL, STAIR,
  GLAZED_FRONT      no: another finish owns the wall base (one owner per base)       ERS s.3; UP-CER-004
  OPEN_SIDE         no: nothing is built                                             -

A WET room whose wall porcelain runs full height carries NO skirting (UP-CER-004 / UP-FIN-WALL-001): its line is
NOT_APPLICABLE, not 0. A room whose finish class is not established is HELD (no figure, never 0).

Refusals (ValueError, never a silent fix): an opening deducted twice in one room; a window with an established sill above
the floor deducted; a tiled / stair / glazed base marked skirted; a HELD quantity written as 0; an unknown piece kind or a
negative / missing length.

    room_ledger(room) -> {"room_id", "status", "certain_lm", "range_lm": (lo, hi), "pieces": [...], "deductions": [...]}
    line_trail(line, deductions) -> {"line_id", "gross", "listed", "unlisted", "net", "readds", ...}
"""

from __future__ import annotations

import math

POLICY = "T296_SKIRTING_OPENING_LEDGER_V1"
RULES = ("UP-SKIRT-001", "UP-CER-002", "UP-CER-003", "UP-CER-004", "UP-QTY-STATUS-001")
FLOOR_GLAZING_MAX_SILL_M = 0.02          # UP-SKIRT-001 1.4.0 / UP-OPEN-SCHED-001: sill <= 0.02 m is floor glazing
TOL_M = 0.0005                           # ledger lengths carry 3 decimals (mm); a sum of rounded terms stays inside
SKIRTED_KINDS = ("WALL", "COLUMN")
OPENING_KINDS = ("DOOR", "PASSAGE", "WINDOW")
OTHER_OWNER_KINDS = ("TILED_WALL", "STAIR", "GLAZED_FRONT")
NOTHING_KINDS = ("OPEN_SIDE",)
KINDS = SKIRTED_KINDS + OPENING_KINDS + OTHER_OWNER_KINDS + NOTHING_KINDS
FINISH_CLASSES = ("DRY", "WET_FULL_HEIGHT_TILE", "UNKNOWN")


def _len(p):
    v = p.get("length_m")
    if not isinstance(v, (int, float)) or isinstance(v, bool) or not math.isfinite(v) or v < 0:
        raise ValueError(f"piece {p.get('piece_id')}: length_m must be a finite number >= 0 (missing is never 0)")
    return float(v)


def window_reading(p):
    """(skirted, held, why) of a window piece from its sill evidence."""
    st, sill = p.get("sill_state"), p.get("sill_m")
    if st == "ESTABLISHED":
        if not isinstance(sill, (int, float)) or isinstance(sill, bool):
            raise ValueError(f"window {p.get('opening_id')}: sill ESTABLISHED needs sill_m")
        if sill > FLOOR_GLAZING_MAX_SILL_M:
            return True, False, f"sill {sill:.2f} m above the floor: the wall base continues under the window"
        return False, False, f"sill {sill:.2f} m: floor-level glazing, no wall base"
    if st in (None, "", "HELD", "UNKNOWN"):
        return False, True, "sill not established: skirted under one reading only (range [0, length])"
    raise ValueError(f"window {p.get('opening_id')}: unknown sill_state {st!r}")


def room_ledger(room):
    rid = room.get("room_id")
    fc = room.get("finish_class")
    if fc not in FINISH_CLASSES:
        raise ValueError(f"room {rid}: finish_class must be one of {FINISH_CLASSES}")
    pieces_out, deds = [], []
    seen_openings = set()
    certain = 0.0
    held_hi = 0.0
    for p in room.get("pieces") or ():
        k = p.get("kind")
        if k not in KINDS:
            raise ValueError(f"room {rid}: unknown piece kind {k!r}")
        L = _len(p)
        if p.get("skirted") is True and k in OTHER_OWNER_KINDS:
            raise ValueError(f"room {rid}: {k} piece {p.get('piece_id')} carries skirting: another finish owns that "
                             "wall base (one owner per base)")
        oid = p.get("opening_id")
        rec = {"piece_id": p.get("piece_id"), "kind": k, "opening_id": oid, "length_m": round(L, 3)}
        if k in OPENING_KINDS:
            if not oid:
                raise ValueError(f"room {rid}: an opening piece needs its opening id")
            if oid in seen_openings:
                raise ValueError(f"room {rid}: opening {oid} deducted twice")
            seen_openings.add(oid)
        if k in SKIRTED_KINDS:
            rec.update(skirted="YES", why="dry wall / column base")
            certain += L
        elif k in ("DOOR", "PASSAGE"):
            rec.update(skirted="NO", why="no wall base at floor level (UP-CER-003)")
            deds.append({"opening_id": oid, "kind": k, "length_m": round(L, 3), "basis": "DEDUCTED"})
        elif k == "WINDOW":
            sk, held, why = window_reading(p)
            if p.get("deduct") is True and sk:
                raise ValueError(f"room {rid}: window {oid} has an established sill above the floor; deducting it "
                                 "removes skirting that is built")
            if sk:
                rec.update(skirted="YES", why=why)
                certain += L
            elif held:
                rec.update(skirted="HELD", why=why)
                held_hi += L
                deds.append({"opening_id": oid, "kind": k, "length_m": round(L, 3), "basis": "HELD_RANGE"})
            else:
                rec.update(skirted="NO", why=why)
                deds.append({"opening_id": oid, "kind": k, "length_m": round(L, 3), "basis": "DEDUCTED"})
        elif k in OTHER_OWNER_KINDS:
            rec.update(skirted="NO", why=f"{k}: another finish owns the wall base")
        else:
            rec.update(skirted="NO", why="open side: nothing built")
        pieces_out.append(rec)
    out = {"room_id": rid, "finish_class": fc, "pieces": pieces_out, "deductions": deds,
           "boundary_lm": round(sum(x["length_m"] for x in pieces_out), 3)}
    if fc == "WET_FULL_HEIGHT_TILE":
        out.update(status="NOT_APPLICABLE", certain_lm=None, range_lm=None,
                   why="full-height wall porcelain: no conventional skirting (UP-CER-004)")
    elif fc == "UNKNOWN":
        out.update(status="HELD", certain_lm=None, range_lm=None, why="finish class not established")
    else:
        out.update(status="HELD" if held_hi > TOL_M else "DETERMINATE", certain_lm=round(certain, 3),
                   range_lm=(round(certain, 3), round(certain + held_hi, 3)))
    given = room.get("reported_lm", "absent")
    if out["status"] in ("HELD", "NOT_APPLICABLE") and out["certain_lm"] is None and given == 0:
        raise ValueError(f"room {rid}: a {out['status']} skirting quantity reported as 0")
    return out


def check_report(status, value):
    """a quantity reported for a status: HELD / NOT_APPLICABLE / UNKNOWN never carry 0 as their figure."""
    if status in ("HELD", "NOT_APPLICABLE", "UNKNOWN") and value == 0:
        raise ValueError(f"a {status} quantity reported as 0 (missing is never 0)")
    return value


def line_trail(line, deductions, tol=TOL_M):
    """the re-adding trail of one skirting line: gross - sum(deductions) = net.

    line: {"line_id", "gross", "net"}; deductions: [{"opening_id" or "cause", "length_m", "listed": bool}]. Each
    deduction key (opening id or named cause) once; the unlisted part is what the line took off without naming it."""
    g, n = line.get("gross"), line.get("net")
    if not isinstance(g, (int, float)) or not isinstance(n, (int, float)):
        raise ValueError(f"line {line.get('line_id')}: gross and net are needed to re-add (missing is never 0)")
    keys = set()
    listed = unlisted = 0.0
    for d in deductions:
        key = d.get("opening_id") or d.get("cause")
        if not key:
            raise ValueError(f"line {line.get('line_id')}: a deduction needs its opening id or a named cause")
        if key in keys:
            raise ValueError(f"line {line.get('line_id')}: deduction {key} listed twice")
        keys.add(key)
        if d.get("signed"):             # a named residual of an aggregate (may be negative); still a number
            v = d.get("length_m")
            if not isinstance(v, (int, float)) or isinstance(v, bool) or not math.isfinite(v):
                raise ValueError(f"line {line.get('line_id')}: residual {key} must be a number (missing is never 0)")
            L = float(v)
        else:
            L = _len({"piece_id": key, "length_m": d.get("length_m")})
        if d.get("listed"):
            listed += L
        else:
            unlisted += L
    resid = g - listed - unlisted - n
    return {"line_id": line.get("line_id"), "gross": round(g, 6), "listed_lm": round(listed, 6),
            "unlisted_lm": round(unlisted, 6), "net": round(n, 6), "residual_lm": round(resid, 6),
            "readds_as_listed": abs(g - listed - n) <= tol, "readds_with_named": abs(resid) <= tol}
