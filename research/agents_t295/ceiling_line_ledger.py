"""R-T295-1: the CEILING FACE-TO-LINE LEDGER (research rule, any villa; T-295). Pure Python, no drawing access.

Provenance: the merged ceiling ledgers (T-271 r2b MERGED 789ebbb4: R-CEIL-R2-1 slab opening = the marked outline;
T-283 r3 MERGED 6e141df6: R-CEIL-R3-1 stair footprint over every face, R-CEIL-R3-2 one edge one surface), the stair
soffit ledger (T-281 MERGED 40518c58: STAIR_SOFFIT_V1), the Checker's one-owner-per-piece rulings of the T-281 / T-283
batch (Verifier 2026-10-25 05:32 / 05:34), the owner bulkhead rule (Q-48 A + Q-43, ASSUMED - OWNER-APPROVED), the dome
rule (Q-44 A, DCR-4: the open disc is HELD and never in the decor ceiling), WORKFLOW_CONTROLS s.5 (statuses) and
ENGINEERING_REASONING_STANDARD s.2.4 (reconcile to named causes, never to a plug). The T-291 wall-to-line ledger
(R-T291-1) is the pattern. Nothing here edits an engine module, a rule or knowledge file, a candidate line or a released
line: lane I (T-284) applies the ledger.

PHYSICAL ELEMENT. Under every slab, per floor piece, one of: the horizontal decor ceiling; a bulkhead vertical face
where a beam drops below it (owner method); the underside of a stair flight or landing (the stair soffit, a stair
finish); no ceiling (an outlined slab opening, a shaft, a stair well); an open dome position; a held part. The formwork
soffit is a form, not a finish area: it owns no ceiling face. Each plan piece has exactly ONE owner surface.

Rules (each refusal code is the first word of the error):
1. ONE OWNER PER PIECE. Every face names its physical piece (`physical_id`) and its owner surface (OWNERS). Two faces
   on one physical piece are refused (TWO_OWNERS), unless the second is declared an ALTERNATIVE measurement of the same
   plan area (`alternative_of`): an alternative is listed, carried in no total and bound to no line.
2. BINDING. A face binds to the candidate line(s) of its owner surface in its room: DECOR, BULKHEAD and HELD_CEILING to
   the room's ceiling line; STAIR_SOFFIT to the stair's soffit line where the candidate has one; VOID and DOME to none
   (a VOID or DOME face in a ceiling line is refused: VOID_AS_CEILING / DOME_AS_CEILING). A face whose owner has no
   candidate line is LISTED as NO_LINE with the line that books its area today (`engine_books_in`), never dropped.
   A face bound to two lines needs declared shares summing to 1 (FACE_TWICE otherwise); a piece whose room has several
   lines of the item and no established per-line split is bound to the LINE GROUP with SPLIT_NOT_ESTABLISHED (never a
   pro-rata share: PRO_RATA refused). A line that holds no face is LISTED (UNMATCHED_LINE) with its reason.
   A face bound to a formwork line is refused (FORMWORK_AS_FINISH).
3. STATUS. One status per row: VERIFIED (with its Checker run, else NO_CHECKER_RUN), DRAWING-CONFIRMED, ASSUMED -
   OWNER-APPROVED (with its source, else NO_SOURCE), HELD or UNKNOWN (carried BLANK with the named item; a 0 or a figure in the
   carried column is refused, HELD_AS_ZERO; the plan area stays visible in `plan_m2`), CONFLICT (both readings shown as
   a range; never summed, RANGE_SUMMED; carried blank).
4. CLOSURE. Per source ledger piece: the faces on it sum to the piece (residual 0.0000 m2, or a named residual); per
   status: the ledger rows sum to the source totals (residual 0.0000 m2).
5. LINE VS FACES. Per line (or line group): line quantity minus the determinate faces carried in it, split into named
   parts only: the faces of its room that the line books but another owner (or HELD) carries, and the remainder
   (polygon chord, rounding) reported with its sign, never plugged. A BLOCKED line's 'before' is BLANK, never 0.
"""
from __future__ import annotations

RULE_ID = "R-T295-1"
TOL = 0.00011           # closure tolerance (the source ledgers state areas to 0.0001 m2)

VERIFIED = "VERIFIED"
DC = "DRAWING-CONFIRMED"
AOA = "ASSUMED — OWNER-APPROVED"
HELD = "HELD"
UNKNOWN = "UNKNOWN"
CONFLICT = "CONFLICT"
STATUSES = (VERIFIED, DC, AOA, HELD, UNKNOWN, CONFLICT)
DETERMINATE = (VERIFIED, DC, AOA)

DECOR = "DECOR"                 # horizontal gypsum decor ceiling (incl. bulkhead undersides)
BULKHEAD = "BULKHEAD"           # bulkhead vertical faces, owner method (an addition to the ceiling line)
HELD_CEILING = "HELD_CEILING"   # a piece the ceiling trade will own, withheld (class, held part, beam underside)
STAIR_SOFFIT = "STAIR_SOFFIT"   # underside of a flight / landing (stair finish)
STAIR_TOP = "STAIR_TOP"         # landing / shaft top under the slab over a stair room (owner trade not decided)
VOID = "VOID"                   # no ceiling: outlined slab opening, shaft, stair well, column head
DOME = "DOME"                   # open dome position (DCR-4)
OWNERS = (DECOR, BULKHEAD, HELD_CEILING, STAIR_SOFFIT, STAIR_TOP, VOID, DOME)
NO_LINE_OWNERS = (VOID, DOME)
CEILING_ITEMS = ("FIN.CEILING",)
FORMWORK_PREFIXES = ("STR.FORM", "FORM.", "STR.FORMWORK")
M2_UNITS = ("m2",)


class LedgerError(ValueError):
    """a face, binding or total the rule refuses (the code is the first word of the message)."""


def _area(v, what):
    if v is None:
        return None
    v = float(v)
    if v < 0:
        raise LedgerError(f"NEGATIVE: {what} {v!r}")
    return v


def check_face(f):
    """rules 1 and 3 on one face dict: face_id, physical_id, owner, unit, status, plan_m2, carried, held_item,
    verified_by, source, range (lo, hi) for CONFLICT, alternative_of."""
    fid = f.get("face_id")
    if f.get("unit") not in M2_UNITS:
        raise LedgerError(f"BAD_UNITS: {fid} unit {f.get('unit')!r}; faces are m2 (edges in m are listed apart)")
    if f.get("owner") not in OWNERS:
        raise LedgerError(f"UNKNOWN_OWNER: {fid} {f.get('owner')!r}")
    st = f.get("status")
    if st not in STATUSES:
        raise LedgerError(f"UNKNOWN_STATUS: {fid} {st!r}")
    plan = _area(f.get("plan_m2"), fid)
    q = f.get("carried")
    if plan is not None and plan > 2000:
        raise LedgerError(f"BAD_UNITS: {fid} plan {plan!r} m2 is not a villa piece (millimetres squared?)")
    if st in DETERMINATE:
        if q is None or q <= 0:
            raise LedgerError(f"NON_POSITIVE: {fid} {st} carries {q!r}")
        if f.get("owner") != STAIR_SOFFIT and plan is not None and abs(q - plan) > TOL:
            raise LedgerError(f"CARRIED_NOT_PLAN: {fid} carries {q!r} but its plan area is {plan!r}")
        if st == VERIFIED and not f.get("verified_by"):
            raise LedgerError(f"NO_CHECKER_RUN: {fid} VERIFIED without its Checker run")
        if st == AOA and not f.get("source"):
            raise LedgerError(f"NO_SOURCE: {fid} ASSUMED - OWNER-APPROVED without its owner source")
    elif st in (HELD, UNKNOWN):
        if q is not None:
            raise LedgerError(f"HELD_AS_ZERO: {fid} is {st}; carried is blank with the named item, never {q!r}")
        if not f.get("held_item"):
            raise LedgerError(f"HELD_UNNAMED: {fid} is {st} without its named item")
        r = f.get("range")
        if r is not None and (len(r) != 2 or r[0] is None or r[1] is None or r[0] > r[1]):
            raise LedgerError(f"CONFLICT_UNSTATED: {fid} range needs both readings (lo, hi)")
    elif st == CONFLICT:
        if q is not None:
            raise LedgerError(f"RANGE_SUMMED: {fid} is a CONFLICT; both readings are shown, carried is blank")
        r = f.get("range")
        if not r or len(r) != 2 or r[0] is None or r[1] is None or r[0] > r[1]:
            raise LedgerError(f"CONFLICT_UNSTATED: {fid} needs both readings (lo, hi)")
    return True


def one_owner(faces):
    """rule 1: refuse two carried faces on one physical piece; alternatives are listed apart."""
    seen = {}
    for f in faces:
        if f.get("alternative_of"):
            continue
        pid = f["physical_id"]
        if pid in seen:
            raise LedgerError(f"TWO_OWNERS: piece {pid} is {seen[pid]} and {f['face_id']} ({f['owner']}); one piece, "
                              f"one owner surface (declare the second as an alternative measurement)")
        seen[pid] = f["face_id"]
    ids = [f["face_id"] for f in faces]
    if len(ids) != len(set(ids)):
        dup = sorted({i for i in ids if ids.count(i) > 1})
        raise LedgerError(f"FACE_TWICE: face id(s) {dup} listed twice")
    for f in faces:
        a = f.get("alternative_of")
        if a and a not in seen.values() and a not in seen:
            raise LedgerError(f"ALTERNATIVE_OF_NOTHING: {f['face_id']} names {a!r}, which is not a carried face")
    return True


def _line_owner_ok(face, line):
    code = line["item_code"]
    if any(code.startswith(p) for p in FORMWORK_PREFIXES):
        raise LedgerError(f"FORMWORK_AS_FINISH: {face['face_id']} in formwork line {line['line_id']} ({code}); a form "
                          f"owns no finish area")
    if face["owner"] == VOID:
        raise LedgerError(f"VOID_AS_CEILING: {face['face_id']} (no ceiling) booked in line {line['line_id']}")
    if face["owner"] == DOME:
        raise LedgerError(f"DOME_AS_CEILING: {face['face_id']} (open dome, DCR-4) booked in line {line['line_id']}")
    return True


def bind(faces, lines, plan):
    """rule 2. faces: checked faces; lines: candidate lines [{line_id, item_code, room_id, unit, evidence_state,
    measured_net, role}]; plan: {face_id: target} where target is None (no line by owner), a line id, a list of line ids
    (a LINE GROUP: SPLIT_NOT_ESTABLISHED) or {line_id: share} (declared shares). Returns (rows, unmatched_lines)."""
    by_id = {l["line_id"]: l for l in lines}
    rows = []
    used = set()
    for f in faces:
        if f.get("alternative_of"):
            if plan.get(f["face_id"]):
                raise LedgerError(f"ALTERNATIVE_BOUND: {f['face_id']} is an alternative measurement; it binds to no line")
            rows.append(dict(f, line_id=None, line_group=None, share=None, binding="ALTERNATIVE (outside totals)"))
            continue
        tgt = plan.get(f["face_id"], "MISSING")
        if tgt == "MISSING":
            raise LedgerError(f"UNPLANNED_FACE: {f['face_id']} has no binding decision")
        if tgt is None:
            b = "NO_LINE (owner)" if f["owner"] in NO_LINE_OWNERS else "NO_LINE (no candidate line of this owner)"
            rows.append(dict(f, line_id=None, line_group=None, share=None, binding=b))
            continue
        if isinstance(tgt, str):
            tgt = {tgt: 1.0}
        if isinstance(tgt, list):
            for lid in tgt:
                if lid not in by_id:
                    raise LedgerError(f"UNKNOWN_LINE: {f['face_id']} -> {lid}")
                _line_owner_ok(f, by_id[lid])
                used.add(lid)
            if len(tgt) < 2:
                raise LedgerError(f"GROUP_OF_ONE: {f['face_id']} line group {tgt}")
            rows.append(dict(f, line_id=None, line_group=" + ".join(tgt), share=None,
                             binding="LINE GROUP (SPLIT_NOT_ESTABLISHED)"))
            continue
        if isinstance(tgt, dict):
            if len(tgt) > 1 and any(v is None for v in tgt.values()):
                raise LedgerError(f"FACE_TWICE: {f['face_id']} in {sorted(tgt)} without declared shares")
            s = sum(tgt.values())
            if abs(s - 1.0) > 1e-9:
                raise LedgerError(f"FACE_TWICE: {f['face_id']} shares sum to {s!r}, not 1 (a face in two lines)")
            for lid, sh in sorted(tgt.items()):
                if lid not in by_id:
                    raise LedgerError(f"UNKNOWN_LINE: {f['face_id']} -> {lid}")
                _line_owner_ok(f, by_id[lid])
                used.add(lid)
                q = None if f.get("carried") is None else round(f["carried"] * sh, 6)
                pl = None if f.get("plan_m2") is None else round(f["plan_m2"] * sh, 6)
                rows.append(dict(f, line_id=lid, line_group=None, share=sh, carried=q, plan_m2=pl,
                                 binding="LINE" if sh == 1.0 else "DECLARED SHARE"))
            continue
        raise LedgerError(f"BAD_BINDING: {f['face_id']} -> {tgt!r}")
    unmatched = [l for l in lines if l["line_id"] not in used]
    return rows, unmatched


def pro_rata(face, lines):
    """refused: a face is never split over lines in proportion to their quantities (rule 2)."""
    raise LedgerError(f"PRO_RATA: {face.get('face_id')} over {[l['line_id'] for l in lines]}; the per-line split is "
                      f"a geometric fact or SPLIT_NOT_ESTABLISHED, never a proportion of the engine quantities")


def total(rows, status, key="carried"):
    """sum of the rows of one status; a CONFLICT range or a HELD row is never summed (rule 3)."""
    if status == CONFLICT and key == "carried":
        raise LedgerError("RANGE_SUMMED: a CONFLICT has no carried total; both readings are listed")
    if status in (HELD, UNKNOWN) and key == "carried":
        raise LedgerError(f"HELD_AS_ZERO: {status} rows have no carried total (blank by item)")
    return round(sum((r.get(key) or 0.0) for r in rows if r["status"] == status and not r.get("alternative_of")), 6)


def piece_closure(faces, pieces):
    """rule 4: per source piece {piece_id: (area, named_residual)}: piece - sum(plan of its carried faces) - named
    residual -> 0. Returns {piece_id: residual}; refuses a residual above TOL (UNNAMED_RESIDUAL)."""
    out = {}
    for pid, (area, named) in sorted(pieces.items()):
        s = sum(f["plan_m2"] for f in faces if f.get("piece") == pid and not f.get("alternative_of")
                and f.get("plan_m2") is not None)
        res = round(area - s - (named or 0.0), 6)
        if abs(res) > TOL:
            raise LedgerError(f"UNNAMED_RESIDUAL: piece {pid} {area} - faces {round(s, 6)} - named {named} = {res}")
        out[pid] = res
    return out


def line_keys(rows):
    """the line keys of a ledger: single line ids and line groups ('L-a + L-b')."""
    ks = {r["line_id"] for r in rows if r.get("line_id")} | {r["line_group"] for r in rows if r.get("line_group")}
    return sorted(ks)


def line_compare(rows, lines, key):
    """rule 5 for one line key (a line id or a line group 'L-a + L-b'). Every face carries `engine_books_in` = the line
    key whose plan area includes it today (the engine ceils it there) or None. Returns the comparison:
      engine_m2            the line (group) quantity, None (BLANK) when a line is BLOCKED / has no quantity
      booked_m2[owner/st]  the plan of the faces the engine books in it, by owner and status
      remainder_m2         engine - sum(booked plan): polygon chord / rounding, with its sign, never plugged
      carried_m2[st]       what this ledger carries in it (determinate rows bound to it), by status."""
    by_id = {l["line_id"]: l for l in lines}
    lids = key.split(" + ")
    for lid in lids:
        if lid not in by_id:
            raise LedgerError(f"UNKNOWN_LINE: {lid}")
    qs = [by_id[l].get("measured_net") for l in lids]
    engine = None if any(q is None for q in qs) else round(sum(qs), 6)
    booked = {}
    for r in rows:
        if r.get("alternative_of") or r.get("engine_books_in") != key or r["owner"] == BULKHEAD:
            continue            # a bulkhead is a vertical face: the engine line is a plan area
        k = f"{r['owner']} / {r['status']}"
        booked[k] = round(booked.get(k, 0.0) + (r.get("plan_m2") or 0.0), 6)
    bsum = round(sum(booked.values()), 6)
    carried = {}
    for r in rows:
        if (r.get("line_id") == key or r.get("line_group") == key) and r["status"] in DETERMINATE:
            k = f"{r['owner']} / {r['status']}"
            carried[k] = round(carried.get(k, 0.0) + r["carried"], 6)
    return {"key": key, "lines": lids, "engine_m2": engine,
            "engine_states": [by_id[l]["evidence_state"] for l in lids],
            "booked_m2": dict(sorted(booked.items())), "booked_total_m2": bsum,
            "remainder_m2": None if engine is None else round(engine - bsum, 6),
            "carried_m2": dict(sorted(carried.items())),
            "carried_total_m2": round(sum(carried.values()), 6)}
