"""R-T292-1: the PLASTER / PAINT FACE-TO-LINE LEDGER (research rule, any villa; T-292). Pure Python, no drawing access.

Provenance: the merged wall-face ledgers T-128 r3 (room walk, owner and drawing-derived heights), T-237 (part 4: the
merged opening sizes per face), T-238 (arched outlines), T-250 (geometric face length per wall, R-T250-1 .. 3, the
roof-datum faces), T-262 (room / opening identity by geometry), T-286 (W03 / W06 settled; R-T286-2 / -3);
WORKFLOW_CONTROLS s.5 (statuses), ENGINEERING_REASONING_STANDARD s.2.2 (owner manual method and drawing-derived method
side by side), s.2.4 (reconcile to named causes, never to a plug), s.3 (one element, several trades; build before
deduct). Nothing here edits an engine module, a rule or knowledge file, a candidate line or a released line: lane I
(T-244) applies the ledger.

PHYSICAL ELEMENT. A wall FACE is one wall seen from one room: the stretch of the wall's face line the room touches
(T-250), from the floor to the finish top (plaster to the slab soffit / the owner height; paint to the decor ceiling /
the owner height). Its m2 = face length x height less the openings in it, each opening by its own area inside that
height. One face has ONE finish owner per layer: a dry interior face is plastered and painted; a wet-room face is tiled
full height (owner Q-48 A, UP-FIN-PAINT-001: no paint behind or above full-height wall tile); an exterior face belongs
to the exterior finish (Sigma / FIN.EXT.FINISH); an open side (VIRTUAL) carries no finish at all.

Rules (each refusal code is the first word of the error):
1. LENGTH. A face length comes from a drawn geometry walk (source class DRAWN); a schedule width, a dimension text, a
   census length or a register run used as a face length is refused (SCHEDULE_LENGTH). Lengths in mm (> 200 m for
   one face) or <= 0 are refused (BAD_UNITS / NON_POSITIVE).
2. OWNER. Per face and layer exactly one owner (FINISH_OWNER): DRY -> FIN.PLASTER + FIN.PAINT; WET -> FIN.WALL.TILE
   (FIN.PAINT refused: TILED_FACE_PAINTED; FIN.PLASTER carried only as the HELD substrate question); SHAFT -> plaster
   and paint on the shaft's own basis; EXTERIOR -> FIN.EXT.FINISH only (an internal code refused: EXTERIOR_INTERNAL);
   VIRTUAL -> nothing (FINISHED_OPEN_SIDE).
3. BINDING. A face binds, per item code, to the candidate line(s) of its room (engine room id by geometry, never by a
   name). A face in two lines of one item code is refused (FACE_TWICE) unless both are declared shares that sum to 1
   (SHARE_SUM). A face in no line is LISTED (UNMATCHED_FACE), never dropped; a line holding no face is LISTED
   (UNMATCHED_LINE) with its reason.
4. STATUS. Every row carries one status per method: VERIFIED (with its Checker run, else NO_CHECKER_RUN),
   DRAWING-CONFIRMED, ASSUMED - OWNER-APPROVED (with its source), HELD (BOUNDED) (a held opening as [lo, hi], both
   > 0, the held item named; a HELD quantity in WORKFLOW_CONTROLS s.5 that keeps its two bounds), HELD (blank quantity, named item; a 0 or a figure is refused: HELD_AS_ZERO / HELD_UNNAMED).
   A RULE_DIFFERENCE between trades (e.g. a window line on the printed pool-side face vs the room's own face) is
   carried by name OUTSIDE every total (DIFFERENCE_IN_TOTAL refused).
5. OPENINGS. Each opening is deducted once per room side by its opening id on the face that hosts it; a second
   deduction of the same id on the same room side is refused (OPENING_TWICE).
6. CLOSURE. Per room: sum of the face lengths (open sides out) = the walked finish length (to 0.002 m per face piece);
   per room and method: sum of face gross - deductions = the room net of the source ledger (to 0.01 m2, its rounding);
   per line: the line quantity minus the ledger net is split into named causes only (each opening whose merged size
   differs, held items); the remainder must be 0 (UNEXPLAINED) or the row is refused.
"""
from __future__ import annotations

RULE_ID = "R-T292-1"
TOL_M = 0.002           # per face piece (the walk samples every 5 mm; T-250 closes rooms to 0.0013 m)
TOL_M2 = 0.011          # the source ledgers state room nets to 0.01 m2

VERIFIED = "VERIFIED"
DC = "DRAWING-CONFIRMED"
AOA = "ASSUMED — OWNER-APPROVED"
BOUNDED = "HELD (BOUNDED)"   # WORKFLOW_CONTROLS s.5: a HELD quantity that carries its two bounds
HELD = "HELD"
STATUSES = (VERIFIED, DC, AOA, BOUNDED, HELD)
DETERMINATE = (VERIFIED, DC, AOA)

DRAWN = "DRAWN"
LENGTH_SOURCES_REFUSED = ("SCHEDULE", "DIMENSION_TEXT", "CENSUS", "REGISTER_RUN", "WINDOW_WIDTH")

PLASTER, PAINT, TILE, EXT = "FIN.PLASTER", "FIN.PAINT", "FIN.WALL.TILE", "FIN.EXT.FINISH"
OWNERS = {"DRY": (PLASTER, PAINT), "SHAFT": (PLASTER, PAINT), "WET": (TILE, PLASTER), "EXTERIOR": (EXT,),
          "VIRTUAL": ()}
SUBSTRATE_ONLY = {("WET", PLASTER)}      # plaster under full-height tile: carried HELD, never as a paint face


class LedgerError(ValueError):
    """a ledger row, binding or total the rule refuses (the code is the first word of the message)."""


def check_length(face):
    """rule 1: a face length must be a drawn walk, in metres."""
    src = (face.get("length_source") or "").upper()
    fid = face.get("face_id")
    if any(src.startswith(s) for s in LENGTH_SOURCES_REFUSED) or src != DRAWN:
        raise LedgerError(f"SCHEDULE_LENGTH: {fid} length source {face.get('length_source')!r}: a face length is the "
                          f"drawn face the room touches, never a schedule / text / census / register run")
    L = face.get("length_m")
    if L is None:
        raise LedgerError(f"NON_POSITIVE: {fid} has no length")
    if L > 200.0:
        raise LedgerError(f"BAD_UNITS: {fid} length {L!r} is not metres")
    if L <= 0:
        raise LedgerError(f"NON_POSITIVE: {fid} length {L!r}")
    return True


def owners(finish_class):
    """rule 2: the item codes a face of this class feeds (first = the visible finish)."""
    if finish_class not in OWNERS:
        raise LedgerError(f"UNKNOWN_CLASS: finish class {finish_class!r}")
    return OWNERS[finish_class]


def check_owner(face, item_code):
    """rule 2: refuse a face booked to a trade that does not own it."""
    fc, fid = face.get("finish_class"), face.get("face_id")
    allowed = owners(fc)
    if fc == "VIRTUAL":
        raise LedgerError(f"FINISHED_OPEN_SIDE: {fid} is an open side; it carries no {item_code}")
    if fc == "WET" and item_code == PAINT:
        raise LedgerError(f"TILED_FACE_PAINTED: {fid} is tiled full height (Q-48 A, UP-FIN-PAINT-001); no paint")
    if fc == "EXTERIOR" and item_code in (PLASTER, PAINT, TILE):
        raise LedgerError(f"EXTERIOR_INTERNAL: {fid} is an exterior face; it belongs to {EXT}, not {item_code}")
    if item_code not in allowed:
        raise LedgerError(f"FINISH_OWNER: {fid} ({fc}) is not owned by {item_code}")
    return True


def check_row(r):
    """rule 4: refuse a ledger row whose quantity contradicts its status."""
    st, fid = r.get("status"), r.get("face_id")
    if st not in STATUSES:
        raise LedgerError(f"UNKNOWN_STATUS: {fid} {st!r}")
    lo, hi = r.get("net_lo"), r.get("net_hi")
    if st in DETERMINATE:
        if lo is None or hi is None or abs(hi - lo) > 1e-9:
            raise LedgerError(f"NOT_DETERMINATE: {fid} {st} must carry one figure (lo = hi), got {lo!r} .. {hi!r}")
        if lo < -1e-9 and not r.get("residual"):     # a named walk-class residual piece may be negative
            raise LedgerError(f"NEGATIVE: {fid} {st} {lo!r}")
        if st == VERIFIED and not r.get("verified_by"):
            raise LedgerError(f"NO_CHECKER_RUN: {fid} VERIFIED without its Checker run")
        if st == AOA and not r.get("source"):
            raise LedgerError(f"NO_SOURCE: {fid} ASSUMED — OWNER-APPROVED without its owner source")
    elif st == BOUNDED:
        if lo is None or hi is None or not (0 < lo <= hi) or not r.get("held_item"):
            raise LedgerError(f"HELD_AS_ZERO: {fid} BOUNDED keeps lo > 0, hi >= lo and the held item named")
    elif st == HELD:
        if lo is not None or hi is not None:
            raise LedgerError(f"HELD_AS_ZERO: {fid} is HELD; its quantity is blank with the named item, never {lo!r}")
        if not r.get("held_item"):
            raise LedgerError(f"HELD_UNNAMED: {fid} is HELD without its named item")
    if r.get("rule_difference_m2") not in (None, 0) and r.get("difference_in_total"):
        raise LedgerError(f"DIFFERENCE_IN_TOTAL: {fid} a rule difference stays outside every total")
    return True


def bind(faces, lines, room_map, shares=None):
    """rule 3. faces: [{face_id, room, finish_class, ...}]; lines: [{line_id, item_code, room_id, ...}] (the
    candidate's room-face lines of the four codes); room_map: {ledger room: [engine room ids]} (by geometry);
    shares: {(face_id, item_code): {line_id: fraction}}. Returns (bindings, unmatched_faces, unmatched_lines) with
    bindings {(face_id, item_code): [(line_id, fraction)]}."""
    shares = shares or {}
    by_room = {}
    for ln in lines:
        by_room.setdefault((ln["room_id"], ln["item_code"]), []).append(ln["line_id"])
    out, unmatched_faces, used = {}, [], set()
    for f in faces:
        if f.get("finish_class") == "VIRTUAL":
            continue
        for code in owners(f["finish_class"]):
            cands = []
            for eng in room_map.get(f["room"], []):
                cands += by_room.get((eng, code), [])
            key = (f["face_id"], code)
            if key in shares:
                sh = shares[key]
                if abs(sum(sh.values()) - 1.0) > 1e-9:
                    raise LedgerError(f"SHARE_SUM: {f['face_id']} {code} shares sum to {sum(sh.values())!r}")
                if not set(sh) <= set(cands):
                    raise LedgerError(f"SHARE_LINE: {f['face_id']} {code} share on a line outside its room")
                out[key] = sorted(sh.items())
            elif len(cands) == 1:
                out[key] = [(cands[0], 1.0)]
            elif not cands:
                unmatched_faces.append(dict(face_id=f["face_id"], item_code=code, room=f["room"],
                                            reason="no candidate line of this code in the face's room"))
                continue
            else:
                raise LedgerError(f"FACE_TWICE: {f['face_id']} {code} lies in {len(cands)} lines {sorted(cands)}; "
                                  f"declare the shares or the face is carried twice")
            used.update(l for l, _ in out[key])
    unmatched_lines = [ln for ln in lines if ln["line_id"] not in used]
    return out, unmatched_faces, unmatched_lines


def check_openings(deductions):
    """rule 5: deductions [{room, opening_id, face_id}]: one opening once per room side."""
    seen = {}
    for d in deductions:
        k = (d["room"], d["opening_id"])
        if k in seen:
            raise LedgerError(f"OPENING_TWICE: {d['opening_id']} deducted twice in {d['room']} "
                              f"({seen[k]} and {d['face_id']})")
        seen[k] = d["face_id"]
    return True


def room_closure(face_lengths, walked_finish_m):
    """rule 6a: the face pieces of one room (open sides out) close on the walked finish length."""
    s = sum(face_lengths)
    tol = TOL_M * max(1, len(face_lengths))
    if abs(s - walked_finish_m) > tol:
        raise LedgerError(f"ROOM_OPEN: face pieces {s:.4f} m vs walked {walked_finish_m:.4f} m "
                          f"(residual {s - walked_finish_m:+.4f})")
    return round(s - walked_finish_m, 4)


def face_net(length_m, h_lo, h_hi, openings):
    """one face (or one room) net as (gross_lo, gross_hi, ded_lo, ded_hi, net_lo, net_hi, held_ids) with the T-128 /
    T-237 convention: an opening with a known band deducts w x (min(head, H) - sill); a merged outline deducts its
    fixed m2; a HELD opening deducts [min(w x H, cap), 0] (net lo takes the full deduction, net hi none)."""
    if h_lo is None or h_hi is None:
        return None
    g_lo, g_hi = length_m * h_lo, length_m * h_hi
    k_lo = k_hi = 0.0
    held = []
    for o in openings:
        if o.get("fixed_m2") is not None:
            k_lo += o["fixed_m2"]; k_hi += o["fixed_m2"]; continue
        if o.get("sill") is None or o.get("head") is None:
            held.append(o["id"])
            full = o["w"] * h_lo
            k_lo += min(full, o["cap_m2"]) if o.get("cap_m2") is not None else full
            continue
        k_lo += o["w"] * max(0.0, min(o["head"], h_lo) - max(o["sill"], 0.0))
        k_hi += o["w"] * max(0.0, min(o["head"], h_hi) - max(o["sill"], 0.0))
    # net lo = smallest gross - largest deduction; net hi = largest gross - smallest deduction
    return g_lo, g_hi, k_lo, k_hi, g_lo - k_lo, g_hi - k_hi, held


def reconcile(line_qty, ledger_net, causes):
    """rule 6c: line - ledger split into named causes [{cause, m2}]; the remainder must be 0."""
    if line_qty is None or ledger_net is None:
        return None
    named = sum(c["m2"] for c in causes)
    rest = round(line_qty - ledger_net - named, 4)
    if abs(rest) > TOL_M2:
        raise LedgerError(f"UNEXPLAINED: line {line_qty!r} - ledger {ledger_net!r} - named {named:.4f} = {rest:+.4f}")
    return rest
