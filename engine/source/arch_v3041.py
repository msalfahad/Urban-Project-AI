"""ARCH_TAKEOFF_V3.0.41 (T-431): the SAME opt-in BOQ candidate as ARCH_TAKEOFF_V3.0 .. V3.0.40 (engine.source.arch_v30,
arch_v301 .. arch_v3040), extended with ONE Checker-verified piece and its cross-trade consequences, wired in ONE step
so that no m2 or lm is counted twice: a ZONE PROLONGED PAST ITS OWN DRAWN END (T-427 MERGED 65ce8f6d, R-T427-1,
ZONE_EXTENT_V1) gives the floor it cut off back to the room it is open to.

  ZONE_EXTENT_FLOOR  a piece of a room's plan joined to the room floor across an edge no drawn line marks is room
                     FLOOR: ONE new floor-finish line for the piece (area DRAWING-CONFIRMED, finish as the room it opens
                     to, with that line's own finish status), built from the merged parts it re-adds; in the SAME step
                     the candidate lines that held those parts give them up, part by part, by id:
                       RETIRE  a held zone line made wholly of moved parts: NOT_APPLICABLE_WITH_EVIDENCE, naming the
                               new floor line that owns its area (never deleted, never 0);
                       SHRINK  a held zone line that keeps a part: its figure falls by exactly the moved parts, its state
                               stays (held stays held, never 0);
  FLOOR_BED          (R-T420-1, the T-420 method unchanged) the B3-05 bed pair of the new floor line (m2 = its net,
                     installed m3 = the owner Q-45 range, the drawing bound of the room's own zone beside);
  SKIRTING_ADD       the base of the piece's own wall / column faces (drawn faces, DRAWING-CONFIRMED) added to the
                     skirting line of the room it joins, as named ADDITION rows (one per face kind), on the merged net
                     (stale binding refused): gross - deductions + additions = net;
  CEILING_ADD        the ceiling of the piece in the class of the room it joins (a ceiling-ledger face HELD only for
                     its class, now decidable): ONE decor ceiling line (FIN.CEILING) for the face's ledger area, its
                     paint (FIN.PAINT.CEILING = decor + bulkhead faces of the face, Q-57 A mod (6)) with the bulkhead
                     part HELD by name, the bulkhead faces (FIN.CEILING.BULKHEAD) HELD blank with the edge length
                     beside, and a part of the piece the ledger never read (no ceiling reading) HELD blank with its
                     area beside; never 0.

R-T431-1 (every villa; integrates R-T427-1 and R-T420-1): ONE physical floor piece, ONE quantity per layer. (a) The new
floor line re-adds exactly the parts the zone lines give up (closure 0); (b) a zone line gives up only parts it held,
by id, and keeps the rest in its own state; (c) the piece's bed m2 is its finish net; (d) the piece's skirting is added
once, to the one line of the room it joins, on that line's merged net; (e) the piece's ceiling is one decor line, its
paint one line, its bulkhead and any unread part HELD blank with their figures beside; (f) held is never 0.

Nothing else moves: every V3.0.40 line not named by the inputs is byte-identical (asserted); totals move only in the
codes this piece owns (asserted). Files: V3_0_41_BOQ_LINES.json / .csv, V3_0_41_INTEGRATION_LEDGER.json / .csv,
V3_0_41_DIFF.csv, V3_0_41_RUN.json. Nothing here names a project, a sheet, a layer or a coordinate.
"""

from __future__ import annotations

import copy
import hashlib

from engine.source import arch_v30 as A30
from engine.source import arch_v302 as A302
from engine.source import arch_v304 as A304
from engine.source import arch_v305 as A305
from engine.source import arch_v3018 as A3018
from engine.source import arch_v3030 as A3030
from engine.source import arch_v3031 as A3031
from engine.source import arch_v3032 as A3032
from engine.source import arch_v3033 as A3033
from engine.source import arch_v3034 as A3034
from engine.source import arch_v3035 as A3035
from engine.source import arch_v3036 as A3036
from engine.source import arch_v3037 as A3037
from engine.source import arch_v3038 as A3038
from engine.source import arch_v3039 as A3039
from engine.source import arch_v3040 as A3040

DEFAULT_GUARD_CLASS = "TOOLING"          # T-212: re-books checker-merged ledgers; adds no default value
METHOD = "ARCH_TAKEOFF_V3.0.41"
EXTENDS = A3040.METHOD
CANDIDATE = A30.METHOD
POLICY_ID = "URBAN_BOQ_T431_ARCH_V3_0_41"
INPUTS_SCHEMA = "URBAN_V3041_INPUTS_V1"
LEDGER_SCHEMA = "URBAN_V3041_INTEGRATION_LEDGER_V1"
ROLLBACK = A30.ROLLBACK
InputsError = A3031.InputsError
_r = A3018._r
_fmt = A3030._fmt
RULE_ID, RULE_VERSION = "R-T431-1", "T-431"
REC_KEY = "zone_extent_v3041"
P_FLOOR, P_BED, P_SKIRT, P_CEIL = "ZONE_EXTENT_FLOOR", "FLOOR_BED", "SKIRTING_ADD", "CEILING_ADD"
OWNER_STATUS = "ASSUMED — OWNER-APPROVED"
DC = "DRAWING-CONFIRMED"
TOL = 0.00006                            # the merged tables print 4 decimals
TOL_LM = 0.0000015                       # the skirting nets print 6 decimals

FLOOR = "FIN.FLOOR.PORCELAIN"
SPACE = "ARCH.SPACE"
SKIRT = "FIN.SKIRTING"
CEILING, BULKHEAD, PAINT = A3032.CEILING, A3032.BULKHEAD, A3032.PAINT
VALUED = A3037.VALUED_STATES
OWN_CODES = (FLOOR, SPACE, SKIRT, CEILING, BULKHEAD, PAINT, A3037.BED_DRY)
ADD_CODES = (FLOOR, CEILING, BULKHEAD, PAINT, A3037.BED_DRY)
FAMILY = {FLOOR: "B3-01", A3037.BED_DRY: "B3-05", SKIRT: "B3-06", CEILING: "B5-01", PAINT: "B4-06", BULKHEAD: "B5-04",
          SPACE: "B2-02"}
NEW_ITEMS = dict(A3032.NEW_ITEMS)

PIECES = {
    P_FLOOR: {"module": "engine/source/arch_v3041.py (a piece cut off by a prolonged zone edge becomes room floor: one "
                        "B3-01 line; the zone lines give the parts up by id in the same step)",
              "policy": "ZONE_EXTENT_FLOOR_V1", "rule_id": "R-T427-1 (R-T431-1 a, b)",
              "owner_rules": ["URBAN-DRY-FLOOR-PORCELAIN-DEFAULT@v1 (the open room's finish, its own status)",
                              "OWNER_RULE_OUTDOOR_FLOORS_2026-10-21 (a garden band is not a room floor until the "
                              "designer says so: D-48 keeps the band)", "UP-QTY-STATUS-001 (held is blank, never 0)"],
              "owner_manual_method": "owner method: the floor-finish area of every floored space by room, finish by "
                                     "the schedule or the owner's default; a printed dimension is read as a chain "
                                     "(T-153 read 1082 as the band length)",
              "drawing_method": "the zone ends at its own drawn end line; a piece joined to the room floor across an "
                                "undrawn edge (>= 0.30 m) is room floor (R-T427-1, ZONE_EXTENT_V1); parts re-add to "
                                "the input"},
    P_BED: {"module": "engine/source/arch_v3041.py (R-T420-1 bed pair for the new floor line)",
            "policy": "FLOOR_BED_V1", "rule_id": "R-T420-1",
            "owner_rules": ["Q-41", "Q-45 (dry 0.03 .. 0.04 m, a range)"],
            "owner_manual_method": A3037.PIECES[A3037.PIECE]["owner_manual_method"],
            "drawing_method": A3037.PIECES[A3037.PIECE]["drawing_method"]},
    P_SKIRT: {"module": "engine/source/arch_v3041.py (the piece's own wall / column base faces added to the skirting "
                        "line of the room it joins, named rows)", "policy": "SKIRTING_ADD_V1",
              "rule_id": "R-T427-1 + R-T440-1 (R-T431-1 d)",
              "owner_rules": ["UP-SKIRT-001 (dry rooms skirted on wall and column faces; openings off)",
                              "R-T440-1 (an addition never lands on a tiled face)"],
              "owner_manual_method": "owner method: skirting = the run of wall and column faces of the dry room at "
                                     "floor level, openings deducted",
              "drawing_method": "the piece's own drawn wall faces (less the column) + the column's three exposed faces "
                                "(V2.9 face runs of the piece, T-440 own route)"},
    P_CEIL: {"module": "engine/source/arch_v3041.py (the piece's ceiling in the class of the room it joins: decor + "
                       "paint lines, bulkhead and unread part HELD blank)", "policy": "CEILING_ADD_V1",
             "rule_id": "R-T284-1 + R-T427-1 (R-T431-1 e)",
             "owner_rules": ["Q-48 A (gypsum decor ceiling 0.15 below the slab)", "Q-43 + R-CEIL-R3-2 (bulkhead "
                             "faces, decor side only)", "Q-57 A mod (6) (paint = decor + bulkhead faces)",
                             "Q-52 C / O-P8-02 (board type not in a plan: PROVISIONAL)"],
             "owner_manual_method": "owner method: decor ceiling = the plan area of the room under the slab; bulkhead "
                                    "faces by the owner depth; ceiling paint = decor + bulkhead",
             "drawing_method": "merged ceiling ledger face area (T-283 r3) in the class of the room it now belongs to "
                               "(T-427); the bulkhead edge length printed beside, its depth not decided for this face"},
}
WAITING = dict(A3040.WAITING)
WAITING.update({
    "T431_D48_GARDEN_BAND": "the garden band proper and its curb (9.101 + 0.604 m2): planter or floor (designer D-48); "
                            "HELD as the band lines, never 0",
    "T431_CEILING_STRIP": "the ceiling over the 0.760 m2 west strip of the dining piece: no ceiling-ledger reading "
                          "(T-283 never read it): HELD blank with its area beside",
    "T431_BULKHEAD_FACES": "the bulkhead faces of the beam pieces over the dining piece (edge length printed by the "
                           "ledger, depth for this face not decided): HELD blank, the edge beside; the paint line "
                           "carries the decor part only",
})

ACTIONS = ("ADD_FLOOR", "RETIRE_ZONE", "SHRINK_ZONE", "ADD_BED", "ADD_SKIRTING", "ADD_CEILING", "ADD_PAINT",
           "ADD_BULKHEAD_HELD", "ADD_CEILING_HELD")


# ================================================================================================ inputs
def _need(s, keys, where):
    for k in keys:
        if s.get(k) in (None, ""):
            raise InputsError(f"{where}: {k} missing")


def _num(x, where, pos=False):
    if not isinstance(x, (int, float)) or isinstance(x, bool) or x != x:
        raise InputsError(f"{where}: {x!r} is not a number")
    if x < 0 or (pos and x == 0):
        raise InputsError(f"{where}: {x!r} is {'not positive' if pos else 'negative'}")
    return float(x)


def _area(x, where):
    if isinstance(x, (int, float)) and not isinstance(x, bool) and abs(x) < 1e-9:
        raise InputsError(f"{where}: HELD_AS_ZERO: a piece of 0 m2 is refused")
    v = _num(x, where, True)
    if v > 2000:
        raise InputsError(f"{where}: {v} is not an area in m2 (mm2 refused)")
    return v


def _length(x, where):
    v = _num(x, where, True)
    if v > 200:
        raise InputsError(f"{where}: {v} is not a length in metres (mm refused)")
    return v


def load_inputs(doc, project_id=None):
    """URBAN_V3041_INPUTS_V1 -> the validated doc.
    {"schema", "project_id", "sources": [{"task", "file", "sha256", "merge_commit", "checker_run"}],
     "owner_bed": {"DRY": {"lo", "hi", "rule"}, ...},
     "pieces": [{"piece", "room", "floor", "joins_room", "area_status", "finish", "finish_status", "zone", "b",
                 "b_upper" | None, "template_line", "parts": [{"id", "area", "from_line", "from_value"}],
                 "zone_lines": [{"line_id", "action": "RETIRE" | "SHRINK", "value_before", "parts": [part ids],
                                 "keeps": [{"id", "area", "why"}]}],
                 "skirting": {"line_id", "net_before", "rows": [{"id", "kind", "qty", "what"}]} | None,
                 "ceiling": {"face", "decor_m2", "decor_status", "template_line", "class_of",
                             "bulkhead_edge_m", "bulkhead_why", "unread": [{"id", "area", "why"}]} | None,
                 "source_tasks"}]}"""
    if not doc:
        return None
    if doc.get("schema") != INPUTS_SCHEMA:
        raise InputsError(f"project inputs: schema must be {INPUTS_SCHEMA}")
    if project_id and doc.get("project_id") not in (None, project_id):
        raise InputsError(f"project inputs are for {doc.get('project_id')!r}, the run is {project_id!r}")
    srcs = {}
    for s in doc.get("sources") or ():
        _need(s, ("task", "file", "sha256", "merge_commit", "checker_run"), f"source {s.get('task')}")
        srcs[s["task"]] = s
    owner = {}
    o = (doc.get("owner_bed") or {}).get("DRY")
    if not o:
        raise InputsError("owner bed range for DRY missing (no default thickness: DEFAULTED_THICKNESS)")
    _need(o, ("rule",), "owner DRY")
    lo, hi = _num(o.get("lo"), "owner DRY lo", True), _num(o.get("hi"), "owner DRY hi", True)
    if lo > hi or hi > 0.2:
        raise InputsError(f"owner DRY: {lo} .. {hi} m is not a bed range in metres")
    owner["DRY"] = dict(o, lo=lo, hi=hi)

    pieces, pids, part_ids, lids = [], set(), set(), set()
    for p in doc.get("pieces") or ():
        where = f"piece {p.get('piece')}"
        _need(p, ("piece", "room", "floor", "joins_room", "area_status", "finish", "finish_status", "zone",
                  "template_line"), where)
        if not p.get("source_tasks") or any(t not in srcs for t in p["source_tasks"]):
            raise InputsError(f"{where}: no merged source named")
        if p["piece"] in pids:
            raise InputsError(f"{where}: named twice")
        pids.add(p["piece"])
        if p["area_status"] not in (DC, "VERIFIED"):
            raise InputsError(f"{where}: area status {p['area_status']!r} (a moved piece keeps its drawn area: "
                              f"DRAWING-CONFIRMED)")
        if p["finish_status"] not in (DC, OWNER_STATUS, "VERIFIED"):
            raise InputsError(f"{where}: finish status {p['finish_status']!r} (the room's own settled finish; an "
                              f"unsettled finish is a HELD finish, not this version)")
        b = _num(p.get("b"), f"{where} b", True)
        if b > 0.3:
            raise InputsError(f"{where}: b {b} is not a build-up in metres")
        bh = p.get("b_upper")
        bh = b if bh is None else _num(bh, f"{where} b_upper", True)
        parts = []
        for q in p.get("parts") or ():
            _need(q, ("id", "from_line"), f"{where} part")
            if q["id"] in part_ids:
                raise InputsError(f"{where}: part {q['id']} named twice (one part, one owner)")
            part_ids.add(q["id"])
            parts.append(dict(q, _a=_area(q.get("area"), f"{where} part {q['id']}")))
        if not parts:
            raise InputsError(f"{where}: a piece names the parts it re-adds")
        total = _r(sum(q["_a"] for q in parts))
        zl = []
        moved = set()
        for z in p.get("zone_lines") or ():
            zw = f"{where} zone line {z.get('line_id')}"
            _need(z, ("line_id", "action"), zw)
            if z["line_id"] in lids:
                raise InputsError(f"{zw}: named twice (one line, one action)")
            lids.add(z["line_id"])
            if z["action"] not in ("RETIRE", "SHRINK"):
                raise InputsError(f"{zw}: action {z['action']} (RETIRE / SHRINK)")
            vb = _area(z.get("value_before"), f"{zw} value_before")
            gives = [q for q in parts if q["id"] in (z.get("parts") or ())]
            if len(gives) != len(z.get("parts") or ()) or not gives:
                raise InputsError(f"{zw}: gives up parts that are not parts of the piece")
            if any(q["from_line"] != z["line_id"] for q in gives):
                raise InputsError(f"{zw}: a part given up was not held by this line")
            keeps = []
            for k in z.get("keeps") or ():
                _need(k, ("id", "why"), f"{zw} keeps")
                keeps.append(dict(k, _a=_area(k.get("area"), f"{zw} keeps {k['id']}")))
            g = _r(sum(q["_a"] for q in gives))
            kk = _r(sum(k["_a"] for k in keeps))
            if abs(g + kk - vb) > TOL:
                raise InputsError(f"{zw}: parts given {_fmt(g)} + kept {_fmt(kk)} m2 is not the line's "
                                  f"{_fmt(vb)} (no area lost, none borrowed)")
            if z["action"] == "RETIRE" and keeps:
                raise InputsError(f"{zw}: a retired line keeps nothing (SHRINK keeps a part)")
            if z["action"] == "SHRINK" and not keeps:
                raise InputsError(f"{zw}: a shrunk line keeps a part (else RETIRE)")
            moved.update(q["id"] for q in gives)
            zl.append(dict(z, _vb=vb, _gives=gives, _keeps=keeps, _g=g, _kk=kk))
        if moved != {q["id"] for q in parts}:
            raise InputsError(f"{where}: parts {sorted({q['id'] for q in parts} - moved)} are given up by no zone "
                              f"line (a part held twice or never held)")
        sk = p.get("skirting")
        if sk:
            _need(sk, ("line_id",), f"{where} skirting")
            _num(sk.get("net_before"), f"{where} skirting net_before", True)
            rows = []
            for r in sk.get("rows") or ():
                _need(r, ("id", "kind", "what"), f"{where} skirting row")
                rows.append(dict(r, _q=_length(r.get("qty"), f"{where} skirting row {r['id']}")))
            if not rows or len({r["id"] for r in rows}) != len(rows):
                raise InputsError(f"{where}: skirting rows missing or an id twice")
            sk = dict(sk, _rows=rows, _add=_r(sum(r["_q"] for r in rows)))
        ce = p.get("ceiling")
        if ce:
            _need(ce, ("face", "decor_status", "template_line", "class_of", "bulkhead_why"), f"{where} ceiling")
            dm = _area(ce.get("decor_m2"), f"{where} ceiling decor")
            be = _length(ce.get("bulkhead_edge_m"), f"{where} ceiling bulkhead edge")
            un = []
            for u in ce.get("unread") or ():
                _need(u, ("id", "why"), f"{where} ceiling unread")
                un.append(dict(u, _a=_area(u.get("area"), f"{where} ceiling unread {u['id']}")))
            if abs(dm + sum(u["_a"] for u in un) - total) > TOL:
                raise InputsError(f"{where}: ceiling decor {_fmt(dm)} + unread parts is not the floor piece "
                                  f"{_fmt(total)} (one plan area, one ceiling)")
            ce = dict(ce, _decor=dm, _edge=be, _unread=un)
        pieces.append(dict(p, _b=b, _bh=bh, _parts=parts, _area=total, _zl=zl, _sk=sk, _ce=ce))
    if not pieces:
        raise InputsError("no piece in the inputs")
    return dict(doc, _sources=srcs, _owner=owner, _pieces=pieces)


# ================================================================================================ helpers
def _ver(srcs):
    return {"task": "+".join(s["task"] for s in srcs), "merge_commit": srcs[0]["merge_commit"],
            "merge_commits": [s["merge_commit"] for s in srcs],
            "verifier_run": "; ".join(s["checker_run"] for s in srcs), "ledger": "; ".join(s["file"] for s in srcs)}


def _rec(piece, srcs, **kw):
    return dict({"piece": piece, "policy": PIECES[piece]["policy"], "tasks": [s["task"] for s in srcs],
                 "ledgers": [s["file"] for s in srcs], "ledger_sha256": [s["sha256"] for s in srcs],
                 "merge_commits": [s["merge_commit"] for s in srcs], "checker_runs": [s["checker_run"] for s in srcs],
                 "rule_id": RULE_ID, "rule_version": RULE_VERSION, "release_status": "NOT RELEASED"}, **kw)


def _fin(ln):
    from engine.source import boq_line as BL
    ln["project"] = copy.deepcopy(ln["project"])
    return BL.validate(ln)


def _base(ln):
    new = copy.deepcopy(ln)
    new["calculation"] = copy.deepcopy(new["calculation"])
    new["calculation"]["inputs"] = dict(new["calculation"]["inputs"] or {})
    return new


def _common(tpl, item_code, element_id, room_id, floor):
    loc = tpl["location"]
    en, ar, tr, sub = NEW_ITEMS[item_code] if item_code in NEW_ITEMS else (tpl["item_en"], tpl["item_ar"],
                                                                           tpl["trade"], tpl.get("subtrade"))
    return dict(project_id=tpl["project"]["project_id"], revision_set_sha256=tpl["project"]["revision_set_sha256"],
                item_code=item_code, element_id=element_id, floor=floor, room_id=room_id,
                room_name_en=loc.get("room_name_en"), room_name_ar=loc.get("room_name_ar"),
                documents=copy.deepcopy(tpl["source"]["documents"]), geometry_source=tpl["source"]["geometry_source"],
                geometry_confidence=tpl["source"]["geometry_confidence"], rule_id=RULE_ID, rule_version=RULE_VERSION,
                item_en=en, item_ar=ar, trade=tr, subtrade=sub)


def _qv(ln):
    """the line's figure: its net, else its bounded high (a held zone line carries its area as a bound)."""
    if ln.get("measured_net") is not None:
        return ln["measured_net"]
    br = ln.get("bounded_range") or {}
    return br.get("high")


# ================================================================================================ pieces
def _floor_line(p, tpl, srcs):
    from engine.source import boq_line as BL
    a = p["_area"]
    eid = f"{p['room']}:{p['piece']}"
    parts = " + ".join(f"{q['id']} {_fmt(q['_a'])}" for q in p["_parts"])
    state = "SOURCE_DERIVED" if p["area_status"] in (DC, "VERIFIED") else "PROVISIONAL"
    ev = OWNER_STATUS if p["finish_status"] == OWNER_STATUS else p["area_status"]
    rec = _rec(P_FLOOR, srcs, action="ADD_FLOOR", floor_piece=p["piece"], room=p["room"], joins_room=p["joins_room"],
               parts=[{"id": q["id"], "area": q["_a"], "from_line": q["from_line"]} for q in p["_parts"]],
               area_status=p["area_status"], finish=p["finish"], finish_status=p["finish_status"],
               finish_line=p["template_line"], evidence_status=ev, zone=p["zone"], family="B3-01",
               owner_trade="FLOOR FINISHES (B3-01)")
    ln = BL.make_line(unit="m2", evidence_state=state, measured_net=a, gross=a,
                      formula=(f"floor piece {p['piece']} of {p['room']} joined to {p['joins_room']} across an undrawn "
                               f"edge (R-T427-1): {parts} = {_fmt(a)} m2 ({p['area_status']}, merged "
                               f"{'+'.join(p['source_tasks'])}); finish {p['finish']} ({p['finish_status']}, as the "
                               f"room's line {p['template_line']})"),
                      inputs={REC_KEY: rec, "evidence_status": ev},
                      physical_element=f"floor finish of the piece {p['piece']} (room floor of {p['joins_room']})",
                      material_state=tpl.get("material_state") or "BY_SPEC",
                      notes=(f"{METHOD}: B3-01 floor piece given back by a zone prolonged past its own drawn end "
                             f"(R-T427-1); the zone lines give the parts up by id in the same version; NOT RELEASED"),
                      **_common(tpl, FLOOR, eid, p["room"], p["floor"]))
    return _fin(ln)


def _zone_retired(ln, z, floor_line, srcs):
    new = _base(ln)
    was = A302._q(A30._qty(ln))
    new["evidence_state"] = "NOT_APPLICABLE_WITH_EVIDENCE"
    new["measured_net"] = None
    new["bounded_range"] = None
    new["gross"] = None
    new["rfi"] = None
    parts = ", ".join(f"{q['id']} {_fmt(q['_a'])}" for q in z["_gives"])
    new["calculation"]["formula"] = (f"{METHOD}: the zone does not reach this piece (no drawn edge between it and the "
                                     f"room floor, R-T427-1): its area ({parts} m2) is room floor, owned by line "
                                     f"{floor_line}; listed here, no quantity (the former reading is kept in "
                                     f"calculation.inputs.{REC_KEY}.formula_before)")[:1500]
    new["calculation"]["inputs"][REC_KEY] = _rec(P_FLOOR, srcs, action="RETIRE_ZONE", was=was, owned_by=floor_line,
                                                 parts=[q["id"] for q in z["_gives"]], value_before=z["_vb"],
                                                 formula_before=ln["calculation"]["formula"],
                                                 evidence_status="NOT_APPLICABLE")
    new["calculation"]["inputs"]["evidence_status"] = "NOT_APPLICABLE"
    new["notes"] = (f"{new.get('notes') or ''} | {METHOD}: ONE floor piece: this zone line's area is room floor on "
                    f"{floor_line} (R-T431-1 b); listed without a quantity, never 0")
    return _fin(new)


def _zone_shrunk(ln, z, floor_line, srcs):
    new = _base(ln)
    before = _qv(ln)
    after = _r(z["_kk"])
    if new.get("measured_net") is not None:
        new["measured_net"] = after
        if new.get("gross") is not None:
            new["gross"] = after
    else:
        br = dict(new["bounded_range"])
        br["high"] = after
        if br.get("low") is not None and br["low"] > after:
            br["low"] = after
        br["basis"] = (f"{br.get('basis') or ''} | {METHOD}: {_fmt(before)} - "
                       f"{', '.join(q['id'] for q in z['_gives'])} {_fmt(z['_g'])} now room floor = {_fmt(after)} m2")[-300:]
        new["bounded_range"] = br
    keeps = "; ".join(f"{k['id']} {_fmt(k['_a'])} ({k['why']})" for k in z["_keeps"])
    new["calculation"]["formula"] = (f"{new['calculation']['formula']} | {METHOD}: "
                                     f"{', '.join(q['id'] for q in z['_gives'])} {_fmt(z['_g'])} m2 is room floor on "
                                     f"{floor_line} (R-T427-1); this line keeps {keeps}, state unchanged: {_fmt(before)} - "
                                     f"{_fmt(z['_g'])} = {_fmt(after)} m2")[-1500:]
    new["calculation"]["inputs"][REC_KEY] = _rec(P_FLOOR, srcs, action="SHRINK_ZONE", value_before=before,
                                                 value_after=after, gives=[q["id"] for q in z["_gives"]],
                                                 given_m2=z["_g"], keeps=[{"id": k["id"], "area": k["_a"],
                                                                           "why": k["why"]} for k in z["_keeps"]],
                                                 owned_by=floor_line, evidence_status="HELD")
    new["notes"] = (f"{new.get('notes') or ''} | {METHOD}: gave {_fmt(z['_g'])} m2 to the floor line {floor_line}; "
                    f"keeps {_fmt(after)} m2 in its own state, never 0")
    return _fin(new)


def _skirting(ln, p, floor_line, srcs):
    sk = p["_sk"]
    new = _base(ln)
    before = ln["measured_net"]
    after = _r(before + sk["_add"])
    new["measured_net"] = after
    adds = list(new.get("additions") or [])
    have = {x.get("id") for x in adds + list(new.get("deductions") or [])}
    for r in sk["_rows"]:
        if r["id"] in have:
            raise InputsError(f"skirting {ln['line_id']}: row {r['id']} is already on the line (added twice)")
        adds.append({"id": r["id"], "unit": "lm", "qty": r["_q"], "what": r["what"]})
    new["additions"] = adds
    g = new.get("gross")
    d = sum(x["qty"] for x in new.get("deductions") or [])
    a = sum(x["qty"] for x in adds)
    if g is not None and abs(g - d + a - after) > 0.0005:
        raise InputsError(f"skirting {ln['line_id']}: gross {g} - {d} + {a} is not the net {after}")
    rows = " + ".join(f"{r['kind']} {_fmt(r['_q'])}" for r in sk["_rows"])
    new["calculation"]["formula"] = (f"{new['calculation']['formula']} | {METHOD}: + base of the piece {p['piece']} "
                                     f"(room floor on {floor_line}, R-T427-1): {rows} = {_fmt(sk['_add'])} lm "
                                     f"({DC}); net {_fmt(before)} + {_fmt(sk['_add'])} = {_fmt(after)} lm")[:1500]
    new["calculation"]["inputs"][REC_KEY] = _rec(P_SKIRT, srcs, action="ADD_SKIRTING", floor_piece=p["piece"],
                                                 net_before=before, net_after=after, added_lm=sk["_add"],
                                                 rows=[{"id": r["id"], "kind": r["kind"], "qty": r["_q"]}
                                                       for r in sk["_rows"]], floor_line=floor_line,
                                                 evidence_status=DC)
    new["notes"] = (f"{new.get('notes') or ''} | {METHOD}: + {_fmt(sk['_add'])} lm base of the piece {p['piece']} "
                    f"(named addition rows, R-T431-1 d)")
    return _fin(new)


def _ceilings(p, tpl, floor_line, srcs):
    """-> [(line, action, held)] for the piece's ceiling: decor, paint (decor part), bulkhead HELD, unread HELD."""
    from engine.source import boq_line as BL
    ce = p["_ce"]
    room = p["room"]
    face = ce["face"]
    out = []
    dm = ce["_decor"]

    def r32(action):     # R-T284-1 runs on these lines too (A3032.check_ceilings: one figure per room, paint = decor +
        return {"policy": "CEILING_FILL_V1 (R-T284-1 checks)", "action": action, "room": face,   # bulkhead, held blank)
                "task": "T-431", "rule_id": RULE_ID, "rule_version": RULE_VERSION, "release_status": "NOT RELEASED",
                "integrated_by": METHOD}
    rec = _rec(P_CEIL, srcs, action="ADD_CEILING", room=face, floor_piece=p["piece"], class_of=ce["class_of"],
               decor_m2=dm, decor_status=ce["decor_status"], floor_line=floor_line, family=FAMILY[CEILING],
               evidence_status=ce["decor_status"])
    dec = BL.make_line(unit="m2", evidence_state="PROVISIONAL", measured_net=dm, gross=dm,
                       formula=(f"horizontal gypsum decor ceiling of face {face} (piece {p['piece']}, now room floor of "
                                f"{p['joins_room']}): ledger plan area {_fmt(dm)} m2 ({ce['decor_status']}), in the "
                                f"class of {ce['class_of']} (Q-48 A); board type not in a plan (Q-52 C): PROVISIONAL"),
                       inputs={REC_KEY: rec, "evidence_status": ce["decor_status"], A3032.REC_KEY: r32("DECOR")},
                       physical_element=f"gypsum decor ceiling over the piece {p['piece']}",
                       material_state="BY_SPEC",
                       notes=(f"{METHOD}: decor ceiling of the piece in the class of the room it joins (R-T427-1); "
                              f"bulkhead faces and paint on their own lines; NOT RELEASED"),
                       **_common(tpl, CEILING, f"{face}:decor", room, p["floor"]))
    out.append((_fin(dec), "ADD_CEILING", []))
    held_b = {"what": f"{BULKHEAD} {face}", "why": ce["bulkhead_why"][:300], "range": None,
              "scenario": f"edge {_fmt(ce['_edge'])} m beside, depth not decided: HELD blank"}
    prec = _rec(P_CEIL, srcs, action="ADD_PAINT", room=face, floor_line=floor_line, floor_piece=p["piece"], decor_line=dec["line_id"],
                decor_m2=dm, bulkhead_m2=None, bulkhead_status="HELD", evidence_status=OWNER_STATUS)
    pai = BL.make_line(unit="m2", evidence_state="PROVISIONAL", measured_net=dm, gross=dm,
                       additions=[],
                       formula=(f"ceiling paint of face {face} = decor {_fmt(dm)} m2 (line {dec['line_id']}) + its "
                                f"bulkhead faces (HELD blank: depth not decided, edge {_fmt(ce['_edge'])} m beside) "
                                f"(Q-57 A mod (6), ASSUMED — OWNER-APPROVED); the bulkhead part is not in this figure"),
                       inputs={REC_KEY: prec, "evidence_status": OWNER_STATUS, A3032.REC_KEY: r32("PAINT")},
                       physical_element=f"paint on the gypsum ceiling over the piece {p['piece']}",
                       material_state="BY_SPEC",
                       notes=(f"{METHOD}: paint = decor + bulkhead (Q-57 A mod (6)); the bulkhead part HELD by name, "
                              f"never 0; NOT RELEASED"),
                       **_common(tpl, PAINT, f"{face}:paint", room, p["floor"]))
    out.append((_fin(pai), "ADD_PAINT", [held_b]))
    brec = _rec(P_CEIL, srcs, action="ADD_BULKHEAD_HELD", room=face, floor_line=floor_line, floor_piece=p["piece"], edge_m=ce["_edge"],
                why=ce["bulkhead_why"], evidence_status="HELD")
    q = f"{face}: bulkhead faces over the piece: {ce['bulkhead_why']}"[:600]
    blk = BL.make_line(unit="m2", evidence_state="BLOCKED_RFI", measured_net=None,
                       formula=(f"bulkhead vertical faces of the beam pieces over face {face}: edge {_fmt(ce['_edge'])} m "
                                f"(ledger) x depth not decided for this face: HELD blank, never 0 "
                                f"({ce['bulkhead_why']})")[:700],
                       inputs={REC_KEY: brec, "evidence_status": "HELD", A3032.REC_KEY: r32("BULKHEAD_HELD")},
                       physical_element=f"gypsum bulkhead faces over the piece {p['piece']}",
                       rfi={"question": q, "unlocks": f"{face}:bulkhead"},
                       notes=f"{METHOD}: HELD blank, the edge beside; NOT RELEASED",
                       **_common(tpl, BULKHEAD, f"{face}:bulkhead", room, p["floor"]))
    out.append((_fin(blk), "ADD_BULKHEAD_HELD", [held_b]))
    for u in ce["_unread"]:
        urec = _rec(P_CEIL, srcs, action="ADD_CEILING_HELD", room=u["id"], floor_line=floor_line, floor_piece=p["piece"], area_beside=u["_a"],
                    why=u["why"], evidence_status="HELD")
        ul = BL.make_line(unit="m2", evidence_state="BLOCKED_RFI", measured_net=None,
                          formula=(f"ceiling over the part {u['id']} of the piece {p['piece']} ({_fmt(u['_a'])} m2 of "
                                   f"floor): {u['why']}: HELD blank, never 0")[:700],
                          inputs={REC_KEY: urec, "evidence_status": "HELD", A3032.REC_KEY: r32("CEILING_HELD")},
                          physical_element=f"ceiling over the part {u['id']}",
                          rfi={"question": f"{u['id']}: {u['why']}"[:600], "unlocks": f"{u['id']}:ceiling"},
                          notes=f"{METHOD}: HELD blank, its floor area beside; NOT RELEASED",
                          **_common(tpl, CEILING, f"{u['id']}:ceiling", room, p["floor"]))
        out.append((_fin(ul), "ADD_CEILING_HELD", [{"what": f"{CEILING} {u['id']}", "why": u["why"][:300],
                                                    "range": [0.0, u["_a"]], "scenario": "no ceiling reading"}]))
    return out


# ================================================================================================ changes
def changes_for(doc, l3040):
    """-> (changes, log). Each change: piece, action (CHANGE / ADD), before (a V3.0.40 line or None), after."""
    if not doc:
        return [], {"piece": "+".join((P_FLOOR, P_BED, P_SKIRT, P_CEIL)), "state": "NO_PROJECT_INPUT"}
    if any(((ln.get("calculation") or {}).get("inputs") or {}).get(REC_KEY) for ln in l3040):
        raise InputsError("the candidate already carries V3.0.41 records (applied once)")
    by = {ln["line_id"]: ln for ln in l3040}
    S = doc["_sources"]
    changes, seen = [], set(by)
    log = {"piece": "+".join((P_FLOOR, P_BED, P_SKIRT, P_CEIL)), "state": "RUN", "sources": doc["sources"],
           "by_action": {}, "lines_added": 0, "lines_changed": 0}

    def add(piece, action, after, before=None, **kw):
        if before is None:
            if after["line_id"] in seen:
                raise ValueError(f"{METHOD}: added line {after['location']['element_id']} repeats an id")
            seen.add(after["line_id"])
            log["lines_added"] += 1
        else:
            if before["line_id"] != after["line_id"]:
                raise ValueError(f"{METHOD}: a changed line keeps its id")
            log["lines_changed"] += 1
        log["by_action"][action] = log["by_action"].get(action, 0) + 1
        srcs = kw.pop("srcs")
        changes.append(A305._change(piece, "ADD" if before is None else "CHANGE", before, after,
                                    step=action, drawing_reference="; ".join(s["file"] for s in srcs),
                                    verification=_ver(srcs), downstream=kw.pop("downstream", []),
                                    group=after["item_code"], **kw))

    for p in doc["_pieces"]:
        srcs = [S[t] for t in p["source_tasks"]]
        where = f"piece {p['piece']}"
        tpl = by.get(p["template_line"])
        if tpl is None or tpl["item_code"] != FLOOR or tpl["evidence_state"] not in VALUED:
            raise InputsError(f"{where}: the room's floor line {p['template_line']} is not a valued {FLOOR} line "
                              f"(stale binding)")
        if tpl["location"].get("room_id") not in (p["joins_room"], None) and \
                tpl["location"].get("element_id") != p["joins_room"]:
            raise InputsError(f"{where}: the floor line {p['template_line']} is not the floor of {p['joins_room']}")
        st = (tpl["calculation"]["inputs"] or {}).get("evidence_status")
        if p["finish_status"] == OWNER_STATUS and tpl["evidence_state"] != "PROVISIONAL" and st != OWNER_STATUS:
            raise InputsError(f"{where}: the finish status is the room line's own (it is not owner-approved)")
        fl = _floor_line(p, tpl, srcs)
        held = [{"what": f"{FLOOR} {fl['location']['element_id']} finish", "why": f"{p['finish']} ({p['finish_status']})"[:300],
                 "range": None, "scenario": "finish as the room's line"}] if p["finish_status"] == OWNER_STATUS else []
        add(P_FLOOR, "ADD_FLOOR", fl, srcs=srcs, evidence_status=fl["calculation"]["inputs"]["evidence_status"],
            held=held, part=p["piece"], downstream=["B3-05 bed pair (this version)", "skirting / ceiling (this version)"])
        for z in p["_zl"]:
            ln = by.get(z["line_id"])
            zw = f"{where} zone line {z['line_id']}"
            if ln is None or ln["item_code"] != SPACE:
                raise InputsError(f"{zw}: not an {SPACE} line of the candidate (stale binding)")
            if ln["evidence_state"] in ("NOT_APPLICABLE_WITH_EVIDENCE", "EXCLUDED_WITH_REASON"):
                raise InputsError(f"{zw}: already carries no quantity (stale binding)")
            v = _qv(ln)
            if v is None or abs(v - z["_vb"]) > TOL:
                raise InputsError(f"{zw}: candidate {v} is not the merged {z['_vb']} (stale binding)")
            if z["action"] == "RETIRE":
                new = _zone_retired(ln, z, fl["line_id"], srcs)
                add(P_FLOOR, "RETIRE_ZONE", new, before=ln, srcs=srcs, evidence_status="NOT_APPLICABLE", held=[])
            else:
                new = _zone_shrunk(ln, z, fl["line_id"], srcs)
                kh = [{"what": f"{SPACE} {ln['location']['element_id']} {k['id']}", "why": k["why"][:300],
                       "range": [0.0, k["_a"]] if new.get("measured_net") is None else None,
                       "scenario": "kept in the zone line, its own state"} for k in z["_keeps"]]
                add(P_FLOOR, "SHRINK_ZONE", new, before=ln, srcs=srcs, evidence_status="HELD", held=kh)
        # bed pair (R-T420-1), on the new floor line
        m2, m3, dbound = A3038._bed_pair(fl, "DRY", p["zone"], p["_b"], p["_bh"], doc["_owner"], srcs,
                                         p["area_status"])
        for x in (m2, m3):
            x["calculation"]["inputs"][REC_KEY] = _rec(P_BED, srcs, action="ADD_BED", finish_line=fl["line_id"],
                                                       floor_piece=p["piece"], evidence_status=x["calculation"]["inputs"][
                                                           "evidence_status"])
            _fin(x)
        bh = [{"what": f"{m3['item_code']} {m3['location']['element_id']} drawn layer", "why": dbound["missing"][:300],
               "range": ([dbound["low"], dbound["high"]] if dbound["high"] is not None else None),
               "scenario": "drawing bound beside the owner range"}]
        add(P_BED, "ADD_BED", m2, srcs=srcs, evidence_status=m2["calculation"]["inputs"]["evidence_status"], held=[],
            bound_to=fl["line_id"])
        add(P_BED, "ADD_BED", m3, srcs=srcs, evidence_status=OWNER_STATUS, held=bh, bound_to=fl["line_id"],
            drawing_bound=dbound)
        # skirting of the room it joins
        if p["_sk"]:
            sk = by.get(p["_sk"]["line_id"])
            if sk is None or sk["item_code"] != SKIRT or sk["unit"] != "lm" or sk["evidence_state"] not in VALUED:
                raise InputsError(f"{where}: skirting line {p['_sk']['line_id']} is not a valued {SKIRT} lm line")
            if abs(sk["measured_net"] - p["_sk"]["net_before"]) > TOL_LM:
                raise InputsError(f"{where}: skirting net {sk['measured_net']} is not the merged "
                                  f"{p['_sk']['net_before']} (stale binding)")
            add(P_SKIRT, "ADD_SKIRTING", _skirting(sk, p, fl["line_id"], srcs), before=sk, srcs=srcs,
                evidence_status=DC, held=[], bound_to=fl["line_id"])
        # ceiling of the piece
        if p["_ce"]:
            ct = by.get(p["_ce"]["template_line"])
            if ct is None or ct["item_code"] != CEILING:
                raise InputsError(f"{where}: ceiling template {p['_ce']['template_line']} is not a {CEILING} line")
            for k in by.values():
                if k["item_code"] in (CEILING, PAINT, BULKHEAD) and \
                        (k["location"].get("room_id") == p["_ce"]["face"]
                         or str(k["location"].get("element_id") or "").startswith(p["_ce"]["face"])):
                    raise InputsError(f"{where}: face {p['_ce']['face']} already carries a ceiling-family line "
                                      f"{k['line_id']} (re-class it, do not add one)")
            for ln, act, held in _ceilings(p, ct, fl["line_id"], srcs):
                ev = ln["calculation"]["inputs"]["evidence_status"]
                add(P_CEIL, act, ln, srcs=srcs, evidence_status=ev, held=held, bound_to=fl["line_id"])
    log["by_action"] = dict(sorted(log["by_action"].items()))
    return changes, log


# ================================================================================================ checks
def check_pieces(lines):
    """R-T431-1 on the integrated lines. Per piece: the floor line = the sum of its parts; every part given up by
    exactly one zone line (retired: no quantity, naming the floor line; shrunk: before - given = kept); the bed m2 is
    the floor net; the skirting addition rows sum to its recorded addition and the line closes; the decor ceiling + the
    unread parts = the floor area; paint = decor (bulkhead HELD) ; held lines blank. -> summary."""
    by = {ln["line_id"]: ln for ln in lines}
    out = {"pieces": 0, "floor_m2": 0.0, "zone_given_m2": 0.0, "retired": 0, "shrunk": 0, "skirting_added_lm": 0.0,
           "ceiling_decor_m2": 0.0, "ceiling_held_lines": 0, "overlap_m2": 0.0}
    floors, given, decor, unread, paint = {}, {}, {}, {}, {}
    for ln in lines:
        rec = ((ln.get("calculation") or {}).get("inputs") or {}).get(REC_KEY)
        if not rec:
            continue
        a = rec["action"]
        if a == "ADD_FLOOR":
            if abs(ln["measured_net"] - _r(sum(q["area"] for q in rec["parts"]))) > 1e-9:
                raise ValueError(f"{METHOD}: floor piece {ln['line_id']} is not the sum of its parts")
            floors[ln["line_id"]] = ln
        elif a in ("RETIRE_ZONE", "SHRINK_ZONE"):
            fl = rec["owned_by"]
            ids = rec["parts"] if a == "RETIRE_ZONE" else rec["gives"]
            for i in ids:
                if i in given.setdefault(fl, {}):
                    raise ValueError(f"{METHOD}: part {i} given up twice (double count)")
                given[fl][i] = ln["line_id"]
            if a == "RETIRE_ZONE":
                if ln["evidence_state"] != "NOT_APPLICABLE_WITH_EVIDENCE" or _qv(ln) is not None:
                    raise ValueError(f"{METHOD}: retired zone line {ln['line_id']} still carries a quantity")
                out["retired"] += 1
            else:
                if abs(_qv(ln) - rec["value_after"]) > 1e-9 or \
                        abs(rec["value_before"] - rec["given_m2"] - rec["value_after"]) > TOL:
                    raise ValueError(f"{METHOD}: shrunk zone line {ln['line_id']} is not before - given")
                if not rec["value_after"] > 0:
                    raise ValueError(f"{METHOD}: shrunk zone line {ln['line_id']} kept 0 (held is never 0)")
                out["shrunk"] += 1
        elif a == "ADD_BED":
            continue
        elif a == "ADD_SKIRTING":
            rows = {r["id"]: r["qty"] for r in rec["rows"]}
            on = {x["id"]: x["qty"] for x in ln.get("additions") or () if x["id"] in rows}
            if on != rows or abs(ln["measured_net"] - (rec["net_before"] + rec["added_lm"])) > 1e-6 \
                    or abs(sum(rows.values()) - rec["added_lm"]) > 1e-9:
                raise ValueError(f"{METHOD}: skirting {ln['line_id']} addition rows do not close")
            out["skirting_added_lm"] = _r(out["skirting_added_lm"] + rec["added_lm"])
        elif a == "ADD_CEILING":
            decor[rec["floor_line"]] = ln
        elif a == "ADD_PAINT":
            paint[rec["floor_line"]] = (ln, rec)
        elif a in ("ADD_BULKHEAD_HELD", "ADD_CEILING_HELD"):
            if ln["evidence_state"] != "BLOCKED_RFI" or ln.get("measured_net") is not None \
                    or not (ln.get("rfi") or {}).get("question"):
                raise ValueError(f"{METHOD}: held {ln['line_id']} is not blank with its reason")
            out["ceiling_held_lines"] += 1
            if a == "ADD_CEILING_HELD":
                unread[rec["floor_line"]] = unread.get(rec["floor_line"], 0.0) + rec["area_beside"]
        else:
            raise ValueError(f"{METHOD}: action {a}")
    for fid, fl in floors.items():
        parts = {q["id"] for q in fl["calculation"]["inputs"][REC_KEY]["parts"]}
        if set(given.get(fid, {})) != parts:
            raise ValueError(f"{METHOD}: floor piece {fid}: parts {sorted(parts)} not each given up once by a zone "
                             f"line ({sorted(given.get(fid, {}))})")
        if fid in decor:
            d = decor[fid]["measured_net"]
            if abs(d + unread.get(fid, 0.0) - fl["measured_net"]) > TOL:
                raise ValueError(f"{METHOD}: ceiling of {fid}: decor + unread is not the floor piece")
            pl, prec = paint.get(fid, (None, None))
            if pl is None or abs(pl["measured_net"] - d) > 1e-9 or prec.get("decor_line") != decor[fid]["line_id"]:
                raise ValueError(f"{METHOD}: ceiling paint of {fid} is not its decor (bulkhead HELD)")
            out["ceiling_decor_m2"] = _r(out["ceiling_decor_m2"] + d)
        bed = [x for x in lines if x["item_code"] == A3037.BED_DRY and x["unit"] == "m2" and
               ((x["calculation"]["inputs"] or {}).get(A3037.REC_KEY) or {}).get("finish_line") == fid]
        if len(bed) != 1 or abs(bed[0]["measured_net"] - fl["measured_net"]) > 1e-9:
            raise ValueError(f"{METHOD}: floor piece {fid} has no bed m2 equal to its net")
        out["pieces"] += 1
        out["floor_m2"] = _r(out["floor_m2"] + fl["measured_net"])
        out["zone_given_m2"] = _r(out["zone_given_m2"] + sum(
            q["area"] for q in fl["calculation"]["inputs"][REC_KEY]["parts"]))
    out["overlap_m2"] = _r(out["zone_given_m2"] - out["floor_m2"])
    if abs(out["overlap_m2"]) > 1e-9:
        raise ValueError(f"{METHOD}: floor pieces and zone parts given differ by {out['overlap_m2']} m2")
    _ = by
    return out


# ================================================================================================ integrate / write
def integrate(l3040, changes, for_lead=()):
    """-> (V3.0.41 lines, identity). Changed lines replace their V3.0.40 line in place; added lines follow; every other
    V3.0.40 line is byte-identical (asserted)."""
    sid = {ln["line_id"]: i for i, ln in enumerate(l3040)}
    out = list(l3040)
    adds, repl = [], set()
    for c in changes:
        a = c["after"]
        if c["action"] == "ADD":
            if a["line_id"] in sid:
                raise ValueError(f"{METHOD}: an added line repeats a V3.0.40 id")
            if a["item_code"] not in ADD_CODES:
                raise ValueError(f"{METHOD}: added code {a['item_code']} is not one this version adds")
            adds.append(a)
        elif c["action"] == "CHANGE":
            i = sid.get(a["line_id"])
            if i is None or a["line_id"] in repl:
                raise ValueError(f"{METHOD}: a changed line is not a V3.0.40 line or changes twice")
            if a["item_code"] not in OWN_CODES:
                raise ValueError(f"{METHOD}: {a['item_code']} is not a code this version may change")
            out[i] = a
            repl.add(a["line_id"])
        else:
            raise ValueError(f"{METHOD}: action {c['action']}")
    out = out + adds
    if len({ln["line_id"] for ln in out}) != len(out):
        raise ValueError(f"{METHOD}: a BOQ line id appears twice")
    guards = A3031._family_guards(out, for_lead)
    roof = A3031.check_roof_layers(out)
    ceil = A3032.check_ceilings(out)
    corr = A3033.check_corrections(out)
    zones = A3034.check_zones(out)
    fence = A3035.check_boundary(out)
    lists = A3036.check_lists(out)
    beds = A3038.check_beds(out)
    lift = A3038.check_lift(out)
    landing = A3038.check_landing(out)
    flights = A3039.check_flights(out)
    runs = A3040.check_runs(out)
    pieces = check_pieces(out)
    pids = {(ln["project"]["project_id"], ln["project"]["revision_set_sha256"]) for ln in out}
    if len(pids) != 1:
        raise ValueError(f"{METHOD}: {len(pids)} project identities in the lines")
    outside = [ln for ln in l3040 if ln["line_id"] not in repl]
    bad = [a["line_id"] for a in outside if A30.line_sha(a) != A30.line_sha(out[sid[a["line_id"]]])]
    if bad:
        raise ValueError(f"{METHOD}: {len(bad)} V3.0.40 line(s) differ outside the named changes")
    ident = {"v3_0_40_lines": len(l3040), "v3_0_41_lines": len(out), "v3_0_41_rows": len(changes),
             "replaced": len(repl), "added": len(adds), "outside_rows": len(outside),
             "outside_rows_identical_to_v3_0_40": len(outside), "pieces": pieces, "gb_runs": runs,
             "flights": flights, "beds": beds, "lift": lift, "landing": landing, "lists": lists, "fence": fence,
             "tile_zones": zones, "corrections": corr, "ceilings": ceil, "roof_buildup": roof, "guards": guards,
             "outside_rows_sha256": hashlib.sha256("".join(A30.line_sha(x) for x in outside).encode()).hexdigest()}
    return out, ident


def ledger_rows(changes, released_lines=None):
    rel = {A30._key(ln): ln for ln in released_lines or ()}
    rows = []
    for c in changes:
        ref = c["after"]
        rec = ref["calculation"]["inputs"].get(REC_KEY) or {}
        b29 = None
        if released_lines is not None:
            b29 = A30._qty(rel[A30._key(ref)]) if A30._key(ref) in rel else dict(A30._qty(None),
                                                                                 state="NOT_IN_RELEASED")
        loc = ref.get("location") or {}
        rows.append({"version": METHOD, "piece": c["piece"], "action": c.get("step"), "change": c["action"],
                     "line_id": ref["line_id"], "item_code": ref["item_code"], "floor": loc.get("floor"),
                     "element_id": loc.get("element_id"), "unit": ref["unit"],
                     "before_released_v2_9": b29, "before_v3_0_40": A30._qty(c.get("before")),
                     "after_v3_0_41": A30._qty(ref), "evidence_status": c.get("evidence_status"),
                     "still_held": c.get("held"), "bound_to": c.get("bound_to"), "release_status": "NOT RELEASED",
                     "owner_manual_method": PIECES[c["piece"]]["owner_manual_method"],
                     "drawing_derived_method": PIECES[c["piece"]]["drawing_method"],
                     "record": rec, "verification": c.get("verification") or {}, "rollback": ROLLBACK})
    return rows


LEDGER_CSV = ("version", "piece", "action", "change", "line_id", "item_code", "floor", "element_id", "unit", "v2_9",
              "v3_0_40", "v3_0_41", "evidence_status", "still_held", "verification")
DIFF_CSV = ("line_id", "item_code", "floor", "element_id", "unit", "vs_v3_0_40", "vs_released_v2_9", "v2_9",
            "v3_0_40", "v3_0_41")


def ledger_csv(rows):
    def q(x):
        return A302._q(x) if x and (x.get("value") is not None or x.get("low") is not None) else ""

    def h(r):
        return "; ".join(f"{x['what']} {x.get('range')}" for x in (r.get("still_held") or ()))[:300]
    return A305._csv([{"version": r["version"], "piece": r["piece"], "action": r["action"], "change": r["change"],
                       "line_id": r["line_id"], "item_code": r["item_code"], "floor": r.get("floor") or "",
                       "element_id": r.get("element_id") or "", "unit": r["unit"],
                       "v2_9": q(r.get("before_released_v2_9")), "v3_0_40": q(r.get("before_v3_0_40")),
                       "v3_0_41": q(r.get("after_v3_0_41")), "evidence_status": r["evidence_status"],
                       "still_held": h(r),
                       "verification": f"{r['verification'].get('task')} "
                                       f"{' '.join(x[:8] for x in r['verification'].get('merge_commits') or ())}"}
                      for r in rows], LEDGER_CSV)


def diff_rows(l3040, l3041, released_lines=None):
    b40 = {ln["line_id"]: ln for ln in l3040}
    rel = {A30._key(ln): ln for ln in released_lines or ()}
    out = []
    for ln in l3041:
        o = b40.get(ln["line_id"])
        vs = "ADDED" if o is None else ("SAME" if A30.line_sha(o) == A30.line_sha(ln) else "CHANGED")
        r = rel.get(A30._key(ln)) if released_lines is not None else None
        vs29 = None if released_lines is None else ("NOT_IN_RELEASED" if r is None else
                                                    ("SAME_QUANTITY" if A30._qty(r) == A30._qty(ln) else
                                                     "QUANTITY_DIFFERS"))
        out.append({"line_id": ln["line_id"], "item_code": ln["item_code"], "floor": ln["location"].get("floor"),
                    "element_id": ln["location"].get("element_id"), "unit": ln["unit"], "vs_v3_0_40": vs,
                    "vs_released_v2_9": vs29, "v2_9": A302._q(A30._qty(r)) if r else "",
                    "v3_0_40": A302._q(A30._qty(o)) if o else "", "v3_0_41": A302._q(A30._qty(ln))})
    return out


def write(out, l3040, changes, log, released_lines=None, for_lead=()):
    """the V3_0_41_* files beside the V3_0_40_* files. -> (file names, identity, ledger)."""
    from pathlib import Path
    from engine.source import boq_line as BL
    out = Path(out)
    l3041, ident = integrate(l3040, changes, for_lead)
    rows = ledger_rows(changes, released_lines)
    diff = diff_rows(l3040, l3041, released_lines)
    named = {c["after"]["line_id"] for c in changes}
    stray = [d["line_id"] for d in diff if d["vs_v3_0_40"] in ("CHANGED", "ADDED") and d["line_id"] not in named]
    if stray:
        raise ValueError(f"{METHOD}: {len(stray)} line(s) changed outside the named changes")
    dsum = {}
    for d in diff:
        dsum.setdefault("vs_v3_0_40", {}).setdefault(d["vs_v3_0_40"], 0)
        dsum["vs_v3_0_40"][d["vs_v3_0_40"]] += 1
        if d["vs_released_v2_9"] is not None:
            dsum.setdefault("vs_released_v2_9", {}).setdefault(d["vs_released_v2_9"], 0)
            dsum["vs_released_v2_9"][d["vs_released_v2_9"]] += 1
    ident = dict(ident, diff=dsum)
    t40, t41 = A304.code_totals(l3040), A304.code_totals(l3041)
    moved = {k: {"v3_0_40": t40.get(k), "v3_0_41": t41.get(k)} for k in sorted(set(t40) | set(t41))
             if t40.get(k) != t41.get(k)}
    if any(k.split("|")[0] not in OWN_CODES for k in moved):
        raise ValueError(f"{METHOD}: totals moved outside this version's codes: {sorted(moved)[:5]}")
    led = {"schema": LEDGER_SCHEMA, "method": METHOD, "extends": EXTENDS, "candidate": CANDIDATE,
           "base": A30.BASE_METHOD, "released": A30.RELEASED_METHOD, "released_default": False, "rows": rows,
           "waiting_pieces": WAITING, "integration_package": True}
    run = {"method": METHOD, "policy": POLICY_ID, "extends": EXTENDS, "candidate": CANDIDATE,
           "base_method": A30.BASE_METHOD, "released_method": A30.RELEASED_METHOD, "released_default": False,
           "rollback": ROLLBACK, "identity": ident, "pieces": PIECES, "piece_logs": [log],
           "totals_moved_by_code": moved, "waiting_pieces": WAITING}
    files = {"V3_0_41_BOQ_LINES.json": BL.dumps(l3041),
             "V3_0_41_BOQ_LINES.csv": A30._lines_csv(l3041),
             "V3_0_41_INTEGRATION_LEDGER.json": A30._j(led),
             "V3_0_41_INTEGRATION_LEDGER.csv": ledger_csv(rows),
             "V3_0_41_DIFF.csv": A305._csv(diff, DIFF_CSV),
             "V3_0_41_RUN.json": A30._j(run)}
    for name, text in files.items():
        (out / name).write_text(text, encoding="utf-8")
    return sorted(files), ident, led


def policy_record():
    return {"method": METHOD, "extends": EXTENDS, "pieces": sorted(PIECES), "inputs_schema": INPUTS_SCHEMA,
            "released_default": False, "rollback": ROLLBACK, "actions": list(ACTIONS)}


__all__ = ["METHOD", "PIECES", "WAITING", "DEFAULT_GUARD_CLASS", "INPUTS_SCHEMA", "load_inputs", "changes_for",
           "check_pieces", "integrate", "ledger_rows", "diff_rows", "write", "InputsError"]
