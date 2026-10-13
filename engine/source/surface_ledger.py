"""SURFACE LEDGER (M9 Phase 2A P2-08a, ARCH_TAKEOFF_V2.1) - read-only: one record per (element, surface, trade) of the
versioned eligibility table, with the state of what the run produced for it. It never adds, changes or removes a BOQ
line and never changes the exit code; it only reports, and every record without a line becomes a finding.

ELIGIBILITY_V0 is a PROPOSAL (owner decision D3: diagnostics only), not an owner-approved measurement standard. A row
names the authority that makes the pair eligible: an owner-approved rule id (from the rule store, or the owner door
rule of 2026-10-13) or PROPOSAL / an open owner question. Reveals and head soffits are NOT automatically payable: they
stay UNRESOLVED_ELIGIBILITY while reveal measurement is undecided (owner requirement 3).

Statuses (exactly one primary status per record; every applicable condition is listed in `conditions`):
    MEASURED                a line with a source-derived quantity
    PROVISIONAL             a provisional / bounded quantity, or a provisional element (never in a released total)
    BLOCKED_MISSING_SOURCE  a line / RFI exists and the drawings lack the information (heights, schedules, specs)
    BLOCKED_OWNER_DECISION  a line / RFI exists and an owner decision is open
    UNRESOLVED_ELIGIBILITY  no line, and the pair is eligible only by a PROPOSAL row or an open owner question
    NO_EMITTER              no line: the engine has no code that produces it (or its code stops on an engine limit)
    CONFIRMED_MISSING       no line although an owner-approved rule makes it eligible, the source is present and an
                            emitter exists: an engineering defect
    EXCLUDED                excluded by a rule (named)
    NOT_APPLICABLE          a line says NOT_APPLICABLE_WITH_EVIDENCE
Priority for a record without a line: UNRESOLVED_ELIGIBILITY > BLOCKED_* (an RFI in UNRESOLVED) > NO_EMITTER >
CONFIRMED_MISSING. No summary adds NO_EMITTER, UNRESOLVED_ELIGIBILITY or BLOCKED_* records into "missing items".

    ledger(lines, rooms, openings, unresolved, *, method, doors=None, walls=None)  -> {records, findings, summary}
Project-agnostic; stdlib + engine.source.rule_store.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
from collections import Counter, defaultdict

POLICY_ID = "SURFACE_LEDGER_V0"
TABLE_ID = "ELIGIBILITY_V0"
TABLE_STATUS = "PROPOSAL"
STATUSES = ("MEASURED", "PROVISIONAL", "BLOCKED_MISSING_SOURCE", "BLOCKED_OWNER_DECISION", "UNRESOLVED_ELIGIBILITY",
            "NO_EMITTER", "CONFIRMED_MISSING", "EXCLUDED", "NOT_APPLICABLE")
DOOR_RULE = "OWNER_DOOR_CLASSES_2026_10_13"
P = "PROPOSAL"

# row: (surface, trade, item codes, element-suffix filter or None, authority, emitter exists)
_DRY = [("FLOOR", "FLOOR_FINISH", ("FIN.FLOOR.PORCELAIN",), "floor", "UP-CER-001", True),
        ("CEILING", "CEILING", ("FIN.CEILING",), "ceiling", P, True),
        ("WALLS", "PLASTER", ("FIN.PLASTER",), None, "UP-CER-009", True),
        ("WALLS", "PAINT", ("FIN.PAINT",), None, "UP-CER-009", True),
        ("SKIRTING", "SKIRTING", ("FIN.SKIRTING",), None, "UP-CER-003", True)]
ELIGIBILITY_V0 = {
    "DRY": _DRY,
    "CIRCULATION": _DRY,
    # a kitchen / pantry / plant room stays as the drawings and owner rules class it (SERVICE): its wet-room
    # eligibility is an open owner question, never inferred (owner requirement 4)
    "SERVICE": _DRY + [("FLOOR", "WATERPROOFING_FLOOR", ("FIN.WP.FLOOR",), None,
                        "OWNER_DECISION_OPEN: a SERVICE space (kitchen) as wet-eligible", True)],
    "WET": [("FLOOR", "WET_FLOOR_TILE", ("FIN.FLOOR.WET_TILE",), "floor", "UP-CER-001", True),
            ("FLOOR", "WATERPROOFING_FLOOR", ("FIN.WP.FLOOR",), None, "UP-WP-001", True),
            ("WALL_BASE", "WATERPROOFING_UPTURN", ("FIN.WP.UPTURN",), None, "UP-WP-002", True),
            ("CEILING", "CEILING", ("FIN.CEILING",), "ceiling", P, True),
            ("WALLS", "WALL_TILE", ("FIN.WALL.TILE",), None, "UP-CER-009", True),
            ("WALLS", "PLASTER", ("FIN.PLASTER",), None, "UP-CER-009", True),
            ("SKIRTING", "SKIRTING", ("FIN.SKIRTING",), None, "UP-CER-004", True)],
    "STAIR": [("TREADS", "MARBLE_TREAD", ("FIN.MARBLE.TREAD",), None, "UP-STAIR-003", True),
              ("RISERS", "MARBLE_RISER", ("FIN.MARBLE.RISER",), None, "UP-STAIR-005", True),
              ("LANDINGS", "MARBLE_LANDING", ("FIN.MARBLE.LANDING",), None, P, True),
              ("BALUSTRADE", "RAILING", ("FIN.RAILING",), None, P, False),
              ("WALLS", "PLASTER", ("FIN.PLASTER",), None, "UP-CER-009", True),
              ("WALLS", "PAINT", ("FIN.PAINT",), None, "UP-CER-009", True)],
    "EXTERIOR": [("GROUND", "EXTERIOR_SCOPE", ("ARCH.EXTERIOR",), None, P, True)],
    "UNKNOWN": [("FLOOR", "FLOOR (space kind not established)", ("FIN.FLOOR.PORCELAIN", "FIN.FLOOR.WET_TILE",
                                                                  "ARCH.SPACE"), None, P, True)],
    "SHAFT": "EXCLUDED: a lift / service shaft carries no ordinary architectural finish (owner door rule "
             "2026-10-13 for the lift; the shaft stays in the gross floor geometry)",
    "VOID": "EXCLUDED: a void has no floor at this level (the space below is double height)",
    "DOOR": [("OPENING", "DOOR_ITEM", ("ARCH.DOOR", "DOOR.INTERNAL.PVC", "DOOR.EXTERNAL.ALUMINIUM",
                                       "DOOR.MAIN_ENTRANCE"), None, DOOR_RULE, True),
             ("THRESHOLD", "THRESHOLD_FINISH", ("ARCH.THRESHOLD",), None, "OWNER_DECISION_OPEN: Q-S6-1", True),
             ("REVEAL_JAMBS", "REVEAL_FINISH", (), None, "OWNER_DECISION_OPEN: reveal measurement", False),
             ("HEAD_SOFFIT", "REVEAL_FINISH", (), None, "OWNER_DECISION_OPEN: reveal measurement", False)],
    "WINDOW": [("OPENING", "WINDOW_ITEM", ("ARCH.WINDOW",), None, P, True),
               ("SILL_STRIP", "SILL / FLOOR STATUS", ("ARCH.WINDOW_REVEAL",), None, P, True),
               ("REVEAL_JAMBS", "REVEAL_FINISH", (), None, "OWNER_DECISION_OPEN: reveal measurement", False),
               ("HEAD_SOFFIT", "REVEAL_FINISH", (), None, "OWNER_DECISION_OPEN: reveal measurement", False)],
    "PASSAGE": [("OPENING", "PASSAGE_ITEM", ("ARCH.PASSAGE",), None, P, True),
                ("THRESHOLD", "FLOOR_STRIP", ("ARCH.THRESHOLD",), None, "OWNER_DECISION_OPEN: Q-S6-1", True),
                ("REVEAL_JAMBS", "REVEAL_FINISH", (), None, "OWNER_DECISION_OPEN: reveal measurement", False),
                ("HEAD_SOFFIT", "REVEAL_FINISH", (), None, "OWNER_DECISION_OPEN: reveal measurement", False)],
    "LIFT_ENTRANCE": "EXCLUDED: LIFT_SYSTEM / LIFT_DOOR (owner door rule 2026-10-13): outside the ordinary "
                     "opening and door BOQ",
    "WALL_GROUP": [("WALL_LINE", "WALL_RUN", ("ARCH.WALL_RUN",), None, P, True),
                   ("WALL_BODY", "MASONRY", ("MAS.BLOCK",), None, P, True)],
}
KIND_OF = {"DRY": "DRY", "WET": "WET", "SERVICE": "SERVICE", "CIRCULATION": "CIRCULATION", "STAIR": "STAIR",
           "SHAFT": "SHAFT", "EXTERIOR": "EXTERIOR", "VOID": "VOID"}
LINE_STATE = {"MEASURED": "MEASURED", "SOURCE_DERIVED": "MEASURED", "PROVISIONAL": "PROVISIONAL",
              "BOUNDED_EXPOSURE": "PROVISIONAL", "NOT_APPLICABLE_WITH_EVIDENCE": "NOT_APPLICABLE",
              "EXCLUDED_WITH_REASON": "EXCLUDED"}
OWNER_Q = re.compile(r"Q-S6-\d|\(Q\d+\)|Q-OPN-\d|OWNER", re.I)
SOURCE_Q = re.compile(r"HEIGHT|SCHEDULE|SECTION|ELEVATION|SPEC|LEGEND|NOT_ESTABLISHED|MISSING_SOURCE|riser", re.I)
ENGINE_Q = re.compile(r"STRIP_NOT_ATTRIBUTED|STAIR_DRAWN_ON_TWO_PLANS|STAIR_LANDING_POLYGON|ENGINE", re.I)


def table_digest():
    return hashlib.sha256(json.dumps(ELIGIBILITY_V0, sort_keys=True).encode("utf-8")).hexdigest()


def _approved(authority):
    """an owner-approved authority: a rule-store rule id that is OWNER_APPROVED, or the owner door rule."""
    if authority == DOOR_RULE:
        return True
    if not authority or authority == P or authority.startswith("OWNER_DECISION_OPEN"):
        return False
    from engine.source import rule_store as RS
    r = RS.rule_set()["rules"].get(authority)
    return bool(r) and r.get("status") == RS.APPROVED


def _blocker(text):
    t = text or ""
    if ENGINE_Q.search(t):
        return "ENGINE"
    if OWNER_Q.search(t):
        return "OWNER_DECISION"
    if SOURCE_Q.search(t):
        return "MISSING_SOURCE"
    return "MISSING_SOURCE"


def _record(element, ekind, floor, row, lines, rfi_text=None, rule=None, element_state=None):
    surface, trade, codes, _suf, authority, emitter = row if row else ("ALL", "-", (), None, None, False)
    rec = {"element": element, "element_kind": ekind, "floor": floor, "surface": surface, "trade": trade,
           "item_codes": list(codes), "authority": authority, "authority_approved": _approved(authority) if row else None,
           "line_ids": [ln["line_id"] for ln in lines], "quantity": None, "unit": None, "conditions": [],
           "blocker": None}
    if rule:
        rec.update(status="EXCLUDED", rule=rule)
        return rec
    if element_state:
        rec.update(status=element_state[0], blocker=element_state[1])
        if element_state[0] in ("PROVISIONAL",):
            rec["conditions"].append("NOT_RELEASED (provisional element: never in a released total)")
        return rec
    if lines:
        states = [ln["evidence_state"] for ln in lines]
        if "BLOCKED_RFI" in states:
            q = next(((ln.get("rfi") or {}).get("question") or ln.get("notes") or "") for ln in lines
                     if ln["evidence_state"] == "BLOCKED_RFI")
            b = _blocker(q)
            rec["blocker"] = q[:200]
            rec["status"] = {"OWNER_DECISION": "BLOCKED_OWNER_DECISION", "MISSING_SOURCE": "BLOCKED_MISSING_SOURCE",
                             "ENGINE": "NO_EMITTER"}[b]
            if b == "ENGINE":
                rec["conditions"].append("ENGINE_LIMIT: the emitter exists but stops on an engine limitation")
            return rec
        st = [LINE_STATE.get(s, "PROVISIONAL") for s in states]
        rec["status"] = next(s for s in ("PROVISIONAL", "MEASURED", "NOT_APPLICABLE", "EXCLUDED") if s in st) \
            if any(s in st for s in ("PROVISIONAL", "MEASURED", "NOT_APPLICABLE", "EXCLUDED")) else "PROVISIONAL"
        q = [ln["measured_net"] for ln in lines if ln.get("measured_net") is not None]
        rec["quantity"] = round(sum(q), 6) if q and rec["status"] in ("MEASURED", "PROVISIONAL") else None
        rec["unit"] = lines[0]["unit"]
        return rec
    # no line
    cond = []
    if not rec["authority_approved"]:
        cond.append("UNRESOLVED_ELIGIBILITY: " + (authority or P))
    if rfi_text:
        cond.append(f"{_blocker(rfi_text)}: {rfi_text[:160]}")
    if not emitter:
        cond.append("NO_EMITTER: the engine has no code for this surface")
    rec["conditions"] = cond
    if not rec["authority_approved"]:
        rec["status"] = "UNRESOLVED_ELIGIBILITY"
    elif rfi_text:
        b = _blocker(rfi_text)
        rec["status"] = {"OWNER_DECISION": "BLOCKED_OWNER_DECISION", "MISSING_SOURCE": "BLOCKED_MISSING_SOURCE",
                         "ENGINE": "NO_EMITTER"}[b]
        rec["blocker"] = rfi_text[:200]
    elif not emitter:
        rec["status"] = "NO_EMITTER"
    else:
        rec["status"] = "CONFIRMED_MISSING"
    return rec


def ledger(lines, rooms, openings, unresolved, *, method, doors=None, walls=None):
    """the read-only ledger of one architectural run (its inputs are never modified)."""
    lines = copy.deepcopy(list(lines))
    by_room, by_op, by_floor_code, by_elem = defaultdict(list), defaultdict(list), defaultdict(list), defaultdict(list)
    for ln in lines:
        loc = ln["location"]
        by_room[loc.get("room_id")].append(ln)
        for oid in re.findall(r"OP-\d+", loc.get("element_id") or ""):
            by_op[(loc.get("floor"), oid)].append(ln)
        by_floor_code[(loc.get("floor"), ln["item_code"])].append(ln)
        by_elem[ln.get("physical_element")].append(ln)
    rfi = defaultdict(list)
    for u in unresolved or ():
        rfi[(u.get("room_id"), u.get("item"))].append(u.get("reason") or "")
    recs = []
    for r in rooms:
        if r.get("class") not in ("ROOM", "MIXED", "MERGED", "UNLABELLED"):
            continue
        kind = KIND_OF.get(r.get("kind"), "UNKNOWN")
        elig = ELIGIBILITY_V0[kind]
        el = f"{r['room_id']} ({r.get('name_en') or r['class']})"
        if isinstance(elig, str):
            recs.append(_record(el, "SPACE:" + kind, r["floor"], None, [], rule=elig))
            continue
        mine = by_room.get(r["room_id"], [])
        for row in elig:
            surface, trade, codes, suf, _a, _e = row
            hit = [ln for ln in mine if ln["item_code"] in codes and
                   (suf is None or suf in (ln["location"].get("element_id") or "").lower() or
                    suf in (ln.get("physical_element") or "").lower())]
            q = next((t for code in codes for t in rfi.get((r["room_id"], code), ())), None)
            recs.append(_record(el, "SPACE:" + kind, r["floor"], row, hit, rfi_text=q))
    door_of_op = {}
    if doors is not None:
        for e in doors["elements"]:
            if e.get("opening_id"):
                door_of_op[(e["floor"], e["opening_id"])] = e
    lift_ops = {(o["floor"], o["opening_id"]) for o in (doors or {}).get("lift_openings") or ()}
    for o in openings:
        key = (o["floor"], o["opening_id"])
        el = f"{o['floor']}:{o['opening_id']} ({o['kind']})"
        if key in lift_ops:
            recs.append(_record(el, "OPENING:LIFT_ENTRANCE", o["floor"], None, [], rule=ELIGIBILITY_V0["LIFT_ENTRANCE"]))
            continue
        mine = by_op.get(key, [])
        d = door_of_op.get(key)
        for row in ELIGIBILITY_V0[o["kind"]]:
            surface, trade, codes, *_ = row
            hit = [ln for ln in mine if ln["item_code"] in codes]
            if d is not None and surface == "OPENING":
                hit += by_elem.get(d["element_id"], [])
                st = _door_state(d)
                if st:
                    recs.append(_record(el, "OPENING:DOOR", o["floor"], row, hit, element_state=st,
                                        rule=ELIGIBILITY_V0["LIFT_ENTRANCE"] if st[0] == "EXCLUDED" else None))
                    continue
            recs.append(_record(el, "OPENING:" + o["kind"], o["floor"], row, hit))
    if doors is not None:                           # door elements with no band opening (V2.1: provisional / unresolved)
        for e in doors["elements"]:
            if e.get("opening_id"):
                continue
            el = f"{e['floor']}:{e['element_id']} (DOOR without a band opening)"
            for row in ELIGIBILITY_V0["DOOR"]:
                if row[0] == "OPENING":
                    recs.append(_record(el, "DOOR_ELEMENT", e["floor"], row, [], element_state=_door_state(e) or
                                        ("PROVISIONAL", None)))
                elif row[0] in ("REVEAL_JAMBS", "HEAD_SOFFIT"):
                    recs.append(_record(el, "DOOR_ELEMENT", e["floor"], row, []))
    for fl in sorted({w["floor"] for w in walls or ()}):
        for row in ELIGIBILITY_V0["WALL_GROUP"]:
            recs.append(_record(f"{fl}:walls", "WALL_GROUP", fl, row, by_floor_code.get((fl, row[2][0]), [])))
    findings = []
    groups = Counter((r["element_kind"], r["surface"], r["status"]) for r in recs
                     if r["status"] in ("NO_EMITTER", "CONFIRMED_MISSING", "UNRESOLVED_ELIGIBILITY"))
    for (ek, sf, st), n in sorted(groups.items()):
        findings.append({"level": "ENGINEERING" if st in ("NO_EMITTER", "CONFIRMED_MISSING") else "OWNER_QUESTION",
                         "code": f"LEDGER_{st}", "element_kind": ek, "surface": sf, "records": n,
                         "message": {"NO_EMITTER": "the engine produces no record for this surface",
                                     "CONFIRMED_MISSING": "eligible by an owner-approved rule, source present, emitter "
                                                          "exists, and no record: an engineering defect",
                                     "UNRESOLVED_ELIGIBILITY": "eligible only by a PROPOSAL row or an open owner "
                                                               "question: not a BOQ omission"}[st]})
    return {"policy": POLICY_ID, "method": method, "table": {"id": TABLE_ID, "status": TABLE_STATUS,
                                                              "digest": table_digest()},
            "records": recs, "findings": findings, "summary": summary(recs)}


def _door_state(e):
    """the ledger status of a door element (V2.1): released -> from its line; else its own state."""
    if e.get("released"):
        return None
    if e.get("boq_class") == "LIFT_SYSTEM/LIFT_DOOR":
        return ("EXCLUDED", None)
    if e.get("state") == "UNRESOLVED":
        return ("BLOCKED_MISSING_SOURCE", "the swing closes no gap: no opening is drawn for it")
    if e.get("boq_class") == "MAIN_ENTRANCE_CANDIDATE":
        return ("BLOCKED_OWNER_DECISION", "a main-entrance candidate: a reviewer names the main entrance")
    if e.get("boq_class") == "CLASS_UNRESOLVED":
        return ("BLOCKED_OWNER_DECISION", "the door's class (internal / external) needs review")
    return ("PROVISIONAL", "a provisional door (no band opening): shown apart, never released")


def summary(recs):
    by = Counter(r["status"] for r in recs)
    return {"records": len(recs), "by_status": {s: by.get(s, 0) for s in STATUSES},
            "confirmed_missing": by.get("CONFIRMED_MISSING", 0),
            "never_added_to_missing": ["NO_EMITTER", "UNRESOLVED_ELIGIBILITY", "BLOCKED_MISSING_SOURCE",
                                       "BLOCKED_OWNER_DECISION"],
            "by_element_kind": {k: dict(Counter(r["status"] for r in recs if r["element_kind"] == k))
                                for k in sorted({r["element_kind"] for r in recs})}}


CSV_COLUMNS = ("floor", "element", "element_kind", "surface", "trade", "status", "authority", "authority_approved",
               "quantity", "unit", "blocker", "conditions", "line_ids", "item_codes")


def policy_record():
    return {"policy": POLICY_ID, "table": TABLE_ID, "table_status": TABLE_STATUS, "table_digest": table_digest(),
            "statuses": list(STATUSES), "read_only": True,
            "never": ["a BOQ line added, changed or removed", "the exit code changed",
                      "a reveal / head soffit counted as a confirmed omission while reveal measurement is undecided",
                      "a kitchen reclassified as wet without an owner decision",
                      "NO_EMITTER / UNRESOLVED_ELIGIBILITY / BLOCKED records added into a 'missing items' total"]}
