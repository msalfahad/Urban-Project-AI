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
# Phase 2B-0 (ARCH_TAKEOFF_V2.2, conserve=True only; finding F-21): the rows V0 lacks, so that every emitted line has
# its record (still PROPOSAL rows where no owner rule names the surface), the two extra statuses, and the stair rows
# for a stair drawn inside a room of another kind. ELIGIBILITY_V0 itself (and its digest) is unchanged.
STATUSES_V2_2 = STATUSES + ("ENGINE_LIMIT", "OUT_OF_LEDGER_SCOPE")
_STAIR_ROWS = [("TREADS", "MARBLE_TREAD", ("FIN.MARBLE.TREAD",), None, "UP-STAIR-003", True),
               ("RISERS", "MARBLE_RISER", ("FIN.MARBLE.RISER",), None, "UP-STAIR-005", True),
               ("LANDINGS", "MARBLE_LANDING", ("FIN.MARBLE.LANDING",), None, P, True),
               ("FLIGHTS", "STAIR_FLIGHT_FINISH", ("FIN.STAIR.FLIGHT",), None, P, True),
               ("STEP_LENGTH", "STAIR_STEP_LENGTH", ("FIN.STAIR.STEP_LM",), None, P, True),
               ("BALUSTRADE", "RAILING", ("FIN.RAILING",), None, P, True)]
STAIR_CODES = tuple(c for row in _STAIR_ROWS for c in row[2])
# Phase 2B-1 (ARCH_TAKEOFF_V2.3, owner_scope=True only): the rows the knowledge registry answers - the owner wet-area
# scope (a kitchen / pantry / ironing room is WET; its floor stays porcelain), the doorway strip (UP-THR-001), the door
# jamb and head plaster (UP-FIN-PLASTER-001), and the line-driven passage-jamb skirting and exterior waterproofing.
TABLE_ID_V0_2 = "ELIGIBILITY_V0_2_OWNER_SCOPE"


def _owner_scope_table():
    t = copy.deepcopy(ELIGIBILITY_V0)
    t["WET"] = [("FLOOR", "WET_AREA_FLOOR", ("FIN.FLOOR.WET_TILE", "FIN.FLOOR.PORCELAIN"), "floor", "UP-WET-001", True)] \
        + [r for r in t["WET"] if r[1] != "WET_FLOOR_TILE"]
    thr = ("ARCH.THRESHOLD", "FIN.MARBLE.THRESHOLD", "FIN.FLOOR.PORCELAIN")
    t["DOOR"] = [r if r[0] != "THRESHOLD" else ("THRESHOLD", "THRESHOLD_FINISH", thr, None, "UP-THR-001", True)
                 for r in t["DOOR"] if r[0] != "HEAD_SOFFIT"]
    t["DOOR"] = [r if r[0] != "REVEAL_JAMBS" else ("REVEAL_JAMBS_AND_HEAD", "PLASTER", ("FIN.PLASTER",), None,
                                                   "UP-FIN-PLASTER-001", True) for r in t["DOOR"]]
    t["PASSAGE"] = [r if r[0] != "THRESHOLD" else ("THRESHOLD", "FLOOR_STRIP", thr, None, "UP-THR-001", True)
                    for r in t["PASSAGE"]]
    return t


OWNER_SCOPE_LINE_DRIVEN = {
    "PASSAGE": [("JAMB_SKIRTING", "SKIRTING", ("FIN.SKIRTING",), None, "UP-SKIRT-001", True)],
    "EXTERIOR": [("WATERPROOFING", "WATERPROOFING_FLOOR", ("FIN.WP.FLOOR",), None, "UP-WP-ROOF-001", True),
                 ("WATERPROOFING_UPTURN", "WATERPROOFING_UPTURN", ("FIN.WP.UPTURN",), None, "UP-WP-ROOF-001", True)]}
# Phase 2B-2 (ARCH_TAKEOFF_V2.4, wp_system=True only): the waterproofing system of the knowledge registry 1.1.0 - the
# upturn on eligible wall boundaries (FIN.WP.WALL_UPTURN replaces FIN.WP.UPTURN), the doorway transitions, the edge
# terminations and the penetration treatments (line-driven rows: a record only where the room has such a line).
TABLE_ID_V0_3 = "ELIGIBILITY_V0_3_WP_SYSTEM"
WP_SYSTEM_LINE_DRIVEN = {
    kind: [("DOORWAY_TRANSITION", "WATERPROOFING_TRANSITION", ("FIN.WP.DOORWAY_TRANSITION",), None, P, True),
           ("EDGE_TERMINATION", "WATERPROOFING_TERMINATION", ("FIN.WP.TERMINATION",), None, P, True),
           ("PENETRATIONS", "WATERPROOFING_PENETRATIONS", ("FIN.WP.PENETRATION",), None, P, True)]
    for kind in ("WET", "EXTERIOR")}


def _wp_system_table():
    t = _owner_scope_table()
    t["WET"] = [r if r[1] != "WATERPROOFING_UPTURN" else (r[0], r[1], ("FIN.WP.WALL_UPTURN",)) + r[3:]
                for r in t["WET"]]
    return t


def _wp_line_driven():
    d = copy.deepcopy(OWNER_SCOPE_LINE_DRIVEN)
    d["EXTERIOR"] = [r if r[1] != "WATERPROOFING_UPTURN" else (r[0], r[1], ("FIN.WP.WALL_UPTURN",)) + r[3:]
                     for r in d["EXTERIOR"]]
    return d


ELIGIBILITY_V0_1_ADDITIONS = {
    "WET": [("WALLS_ABOVE_TILE", "PAINT", ("FIN.PAINT",), None, "UP-CER-009", True),
            ("DOORWAY", "WATERPROOFING_DOORWAY", ("FIN.WP.DOORWAY",), None, "UP-WP-003", True)],
    "STAIR": [("FLIGHTS", "STAIR_FLIGHT_FINISH", ("FIN.STAIR.FLIGHT",), None, P, True),
              ("STEP_LENGTH", "STAIR_STEP_LENGTH", ("FIN.STAIR.STEP_LM",), None, P, True),
              ("CEILING", "CEILING", ("FIN.CEILING",), None, P, True),
              ("SKIRTING", "SKIRTING", ("FIN.SKIRTING",), None, P, True)],
}
OUT_OF_SCOPE = {"ARCH.SPACE": "the area of a space with no finish row (shaft, stair, unlabelled): geometry, not a "
                              "finish quantity",
                "ARCH.THRESHOLD": "a doorway / closure strip that no opening or room record owns",
                "ARCH.WINDOW_REVEAL": "a window strip that no opening record owns"}
BOQ_COMPLETENESS_WHY = [
    "the eligibility table is a PROPOSAL (ELIGIBILITY_V0 + V0.1 additions), not an owner-approved measurement standard",
    "external works, facade finishes, roof works, sills and MEP are outside the architectural plan route",
    "UNRESOLVED_ELIGIBILITY / BLOCKED / ENGINE_LIMIT records are open, not absent",
    "CONFIRMED_MISSING = 0 says only that no owner-approved, sourced, emitted surface is silently missing"]

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


def _record(element, ekind, floor, row, lines, rfi_text=None, rule=None, element_state=None,
            engine_status="NO_EMITTER"):
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
                             "ENGINE": engine_status}[b]
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
                         "ENGINE": engine_status}[b]
        rec["blocker"] = rfi_text[:200]
    elif not emitter:
        rec["status"] = "NO_EMITTER"
    else:
        rec["status"] = "CONFIRMED_MISSING"
    return rec


def ledger(lines, rooms, openings, unresolved, *, method, doors=None, walls=None, conserve=False, owner_scope=False,
           wp_system=False):
    """the read-only ledger of one architectural run (its inputs are never modified). conserve (ARCH_TAKEOFF_V2.2,
    F-21): the V0.1 rows, ENGINE_LIMIT apart from NO_EMITTER, every line in exactly one record (or a named
    out-of-scope category), coverage by floor and trade, and no completeness claim; False is the V2.1 ledger.
    owner_scope (ARCH_TAKEOFF_V2.3): the V0.2 rows of the knowledge registry (_owner_scope_table).
    wp_system (ARCH_TAKEOFF_V2.4): the V0.3 waterproofing rows (_wp_system_table, WP_SYSTEM_LINE_DRIVEN)."""
    table = _wp_system_table() if wp_system else _owner_scope_table() if owner_scope else ELIGIBILITY_V0
    line_driven = _wp_line_driven() if wp_system else OWNER_SCOPE_LINE_DRIVEN
    lines = copy.deepcopy(list(lines))
    eng = {"engine_status": "ENGINE_LIMIT"} if conserve else {}
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
        if owner_scope and (r.get("finish_scope") or {}).get("scope") == "WET":
            kind = "WET"                            # UP-WET-001: the owner wet-area scope
        elig = table[kind]
        el = f"{r['room_id']} ({r.get('name_en') or r['class']})"
        if isinstance(elig, str):
            recs.append(_record(el, "SPACE:" + kind, r["floor"], None, [], rule=elig))
            continue
        mine = by_room.get(r["room_id"], [])
        rows = list(elig)
        if conserve:
            # the V0.1 rows are line-driven: a record only where the room has such a line (they conserve lines, they
            # do not make a surface eligible - a wet room without a doorway piece is not a CONFIRMED_MISSING)
            rows += [x for x in ELIGIBILITY_V0_1_ADDITIONS.get(kind, []) + (line_driven.get(kind, [])
                                                                             if owner_scope else []) +
                     (WP_SYSTEM_LINE_DRIVEN.get(kind, []) if wp_system else [])
                     if any(ln["item_code"] in x[2] for ln in mine)]
            if kind != "STAIR" and any(ln["item_code"] in STAIR_CODES for ln in mine):
                rows += [(f"STAIR_IN_ROOM:{x[0]}",) + x[1:] for x in _STAIR_ROWS
                         if any(ln["item_code"] in x[2] for ln in mine)]
        taken = set()
        for row in rows:
            surface, trade, codes, suf, _a, _e = row
            hit = [ln for ln in mine if ln["item_code"] in codes and
                   (suf is None or suf in (ln["location"].get("element_id") or "").lower() or
                    suf in (ln.get("physical_element") or "").lower())]
            if conserve:
                # V0 rows share codes (WET plaster / paint above tile; stair skirting): a line is taken once
                if surface == "WALLS" and kind == "WET" and codes == ("FIN.PAINT",):
                    hit = []
                hit = [ln for ln in hit if ln["line_id"] not in taken]
                if surface == "WALLS_ABOVE_TILE":
                    hit = [ln for ln in hit if "above wall tile" in (ln.get("physical_element") or "")]
                taken.update(ln["line_id"] for ln in hit)
            q = next((t for code in codes for t in rfi.get((r["room_id"], code), ())), None)
            recs.append(_record(el, "SPACE:" + kind, r["floor"], row, hit, rfi_text=q, **eng))
    door_of_op = {}
    if doors is not None:
        for e in doors["elements"]:
            if e.get("opening_id"):
                door_of_op[(e["floor"], e["opening_id"])] = e
    lift_ops = {(o["floor"], o["opening_id"]) for o in (doors or {}).get("lift_openings") or ()}
    lift_cand = {(o["floor"], o["opening_id"]): o for o in (doors or {}).get("lift_candidates") or ()} \
        if conserve else {}
    op_taken = set()
    for o in openings:
        key = (o["floor"], o["opening_id"])
        el = f"{o['floor']}:{o['opening_id']} ({o['kind']})"
        if key in lift_ops:
            recs.append(_record(el, "OPENING:LIFT_ENTRANCE", o["floor"], None, [], rule=table["LIFT_ENTRANCE"]))
            continue
        if key in lift_cand:
            mine = by_op.get(key, [])
            for row in table[o["kind"]]:
                hit = [ln for ln in mine if ln["item_code"] in row[2]]
                recs.append(_record(el, "OPENING:LIFT_ENTRANCE_CANDIDATE", o["floor"], row, hit, element_state=(
                    "BLOCKED_OWNER_DECISION", "LIFT_ENTRANCE_CANDIDATE: " + lift_cand[key]["evidence"]), **eng))
            continue
        mine = by_op.get(key, [])
        d = door_of_op.get(key)
        o_rows = list(table[o["kind"]])
        if owner_scope:
            o_rows += [x for x in line_driven.get(o["kind"], []) if any(ln["item_code"] in x[2] for ln in mine)]
        for row in o_rows:
            surface, trade, codes, *_ = row
            hit = [ln for ln in mine if ln["item_code"] in codes]
            shared = []
            if conserve:
                # a strip between two openings names both: it is counted under the first one only
                shared = [ln for ln in hit if ln["line_id"] in op_taken]
                hit = [ln for ln in hit if ln["line_id"] not in op_taken]
                op_taken.update(ln["line_id"] for ln in hit)
            if d is not None and surface == "OPENING":
                hit += by_elem.get(d["element_id"], [])
                st = _door_state(d)
                if st:
                    recs.append(_record(el, "OPENING:DOOR", o["floor"], row, hit, element_state=st,
                                        rule=table["LIFT_ENTRANCE"] if st[0] == "EXCLUDED" else None))
                    continue
            recs.append(_record(el, "OPENING:" + o["kind"], o["floor"], row, hit, **eng))
            if shared:
                recs[-1]["conditions"].append("SHARED_STRIP: " + ", ".join(ln["line_id"] for ln in shared) +
                                              " counted under the other opening it names")
    if doors is not None:                           # door elements with no band opening (V2.1: provisional / unresolved)
        for e in doors["elements"]:
            if e.get("opening_id"):
                continue
            el = f"{e['floor']}:{e['element_id']} (DOOR without a band opening)"
            for row in table["DOOR"]:
                if row[0] == "OPENING":
                    recs.append(_record(el, "DOOR_ELEMENT", e["floor"], row, [], element_state=_door_state(e) or
                                        ("PROVISIONAL", None)))
                elif row[0] in ("REVEAL_JAMBS", "HEAD_SOFFIT", "REVEAL_JAMBS_AND_HEAD"):
                    recs.append(_record(el, "DOOR_ELEMENT", e["floor"], row, []))
    for fl in sorted({w["floor"] for w in walls or ()}):
        for row in table["WALL_GROUP"]:
            recs.append(_record(f"{fl}:walls", "WALL_GROUP", fl, row, by_floor_code.get((fl, row[2][0]), [])))
    if conserve:
        recs += _conserve(recs, lines, rooms)
    findings = []
    groups = Counter((r["element_kind"], r["surface"], r["status"]) for r in recs
                     if r["status"] in ("NO_EMITTER", "CONFIRMED_MISSING", "UNRESOLVED_ELIGIBILITY") +
                     (("ENGINE_LIMIT", "OUT_OF_LEDGER_SCOPE") if conserve else ()))
    for (ek, sf, st), n in sorted(groups.items()):
        findings.append({"level": "ENGINEERING" if st in ("NO_EMITTER", "CONFIRMED_MISSING") else "OWNER_QUESTION",
                         "code": f"LEDGER_{st}", "element_kind": ek, "surface": sf, "records": n,
                         "message": {"ENGINE_LIMIT": "the emitter exists but stops on an engine limitation",
                                 "OUT_OF_LEDGER_SCOPE": "lines outside every surface row, named with their reason",
                                 "NO_EMITTER": "the engine produces no record for this surface",
                                     "CONFIRMED_MISSING": "eligible by an owner-approved rule, source present, emitter "
                                                          "exists, and no record: an engineering defect",
                                     "UNRESOLVED_ELIGIBILITY": "eligible only by a PROPOSAL row or an open owner "
                                                               "question: not a BOQ omission"}[st]})
    out = {"policy": POLICY_ID, "method": method, "table": {"id": TABLE_ID, "status": TABLE_STATUS,
                                                             "digest": table_digest()},
           "records": recs, "findings": findings, "summary": summary(recs)}
    if owner_scope:
        from engine.source import knowledge as K               # V2.3: 1.0.0; V2.4: 1.1.0 (the active registry)
        out["table"]["owner_scope"] = TABLE_ID_V0_2 + f" (knowledge registry {K.version()} rules)"
    if wp_system:
        out["table"]["wp_system"] = TABLE_ID_V0_3 + " (knowledge registry 1.1.0 waterproofing rules)"
    if conserve:
        out["table"]["additions"] = "ELIGIBILITY_V0_1_ADDITIONS (PROPOSAL)"
        out["summary"] = summary(recs, statuses=STATUSES_V2_2)
        out["summary"]["conservation"] = conservation(recs, lines)
        out["summary"]["coverage_by_floor_trade"] = coverage(recs)
        out["summary"]["boq_completeness"] = {"state": "NOT_ESTABLISHED", "why": BOQ_COMPLETENESS_WHY}
    return out


def _conserve(recs, lines, rooms):
    """F-21: a record for every line no surface row took - the room's other lines (by item code), strips that no
    opening owns, then the named out-of-scope categories; nothing is left unaccounted."""
    taken = {i for r in recs for i in r["line_ids"]}
    by_id = {r["room_id"]: r for r in rooms}
    left = defaultdict(list)
    for ln in lines:
        if ln["line_id"] in taken:
            continue
        loc = ln["location"]
        rid = loc.get("room_id")
        left[(loc.get("floor"), rid, ln["item_code"])].append(ln)
    out = []
    for (fl, rid, code), lns in sorted(left.items(), key=lambda kv: tuple(str(x) for x in kv[0])):
        r = by_id.get(rid)
        if r is not None and code not in OUT_OF_SCOPE:
            kind = KIND_OF.get(r.get("kind"), "UNKNOWN")
            el = f"{rid} ({r.get('name_en') or r['class']})"
            row = (f"OTHER:{code}", code, (code,), None, P, True)
            out.append(_record(el, "SPACE:" + kind, fl, row, lns, engine_status="ENGINE_LIMIT"))
            continue
        why = OUT_OF_SCOPE.get(code) or f"no surface row owns {code}"
        rec = _record(f"{fl}:{rid}", "OUT_OF_LEDGER_SCOPE", fl, (f"SCOPE:{code}", code, (code,), None, P, True), lns,
                      engine_status="ENGINE_LIMIT")
        rec.update(status="OUT_OF_LEDGER_SCOPE", blocker=why,
                   conditions=rec["conditions"] + [f"OUT_OF_LEDGER_SCOPE: {why}"])
        out.append(rec)
    return out


def conservation(recs, lines):
    seen = Counter(i for r in recs for i in r["line_ids"])
    ids = [ln["line_id"] for ln in lines]
    missing = sorted(set(ids) - set(seen))
    dup = sorted(i for i, n in seen.items() if n > 1)
    return {"lines": len(ids), "in_records": sum(1 for i in ids if i in seen), "not_in_any_record": missing,
            "duplicates": dup, "out_of_scope_lines": sum(len(r["line_ids"]) for r in recs
                                                          if r["status"] == "OUT_OF_LEDGER_SCOPE"),
            "ok": not missing and not dup}


def coverage(recs):
    """records by floor and trade with their statuses (and the quantity of the measured / provisional ones)."""
    out = defaultdict(lambda: defaultdict(lambda: {"records": 0, "by_status": Counter(), "quantity": defaultdict(float)}))
    for r in recs:
        c = out[r.get("floor") or "-"][r.get("trade") or "-"]
        c["records"] += 1
        c["by_status"][r["status"]] += 1
        if r.get("quantity") is not None and r.get("unit"):
            c["quantity"][r["unit"]] += r["quantity"]
    return {fl: {tr: {"records": v["records"], "by_status": dict(sorted(v["by_status"].items())),
                      "quantity": {u: round(q, 6) for u, q in sorted(v["quantity"].items())}}
                 for tr, v in sorted(t.items())} for fl, t in sorted(out.items())}


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
    if e.get("hold"):                                  # ARCH_TAKEOFF_V2.2 only (F-18)
        return ("BLOCKED_MISSING_SOURCE", e["hold"])
    if e.get("boq_class") == "CLASS_REVIEW":           # ARCH_TAKEOFF_V2.2 only (F-20)
        return ("BLOCKED_OWNER_DECISION", "CLASS_REVIEW: " + (e.get("class_evidence") or ""))
    return ("PROVISIONAL", "a provisional door (no band opening): shown apart, never released")


def summary(recs, statuses=STATUSES):
    by = Counter(r["status"] for r in recs)
    return {"records": len(recs), "by_status": {s: by.get(s, 0) for s in statuses},
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
