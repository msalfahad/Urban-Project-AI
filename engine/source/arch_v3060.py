"""ARCH_TAKEOFF_V3.0.60 (T-423 r2, stream F; staged as V3.0.58 in r1, renumbered after T-507 / T-498 merged
V3.0.58 / V3.0.59 first, merge-order rule): the SAME opt-in BOQ candidate as ARCH_TAKEOFF_V3.0 .. V3.0.59
(engine.source.arch_v30, arch_v301 .. arch_v3059), extended with the T-246 split remainder (b)-(d): four record /
state pieces from Checker-merged ledgers. NO measured_net, range or total moves (asserted line by line and by code):

  CEILING_LIST   a FIN.CEILING line whose net is its gross less a HELD dome position over the room (T-284 restated the
                 net, T-330 FLAG EMPTY_DEDUCTIONS) gets its canonical deduction list: ONE item per dome piece, by the
                 dome's id and the room, qty = gross - net in m2, bound to the merged T-283 dome table's 4-decimal print
                 of that piece within half a unit of its last place (the T-284 LEDGER_HALF_UNIT rule; never a rounding
                 move): gross - deductions = net within the export tolerance 0.0005 (the T-330 check). A line the
                 ledger cannot close by id is SET ASIDE BY NAME in the inputs and not touched.
  FACE_PIECE     a door hole the wall-tile / backing record booked on a straight face whose drawn line carries no door,
                 while the same room walks the doorway as its own OFF:DOORWAY piece (T-388 F1, OPENING_OFF_ITS_FACE),
                 moves to that piece in the line's face record and in its canonical deduction list: the two face nets
                 change by +- the hole, the line's net, gross, state and list sum do not (asserted; R-T388-1 b).
  PAINT_NA       a wall PAINT line of a room whose every face is wall-tiled to the coat top (T-388 F3; UP-FIN-PAINT-001,
                 Q-37 A + Q-48 A: the tile owns the face) leaves BLOCKED_RFI for NOT_APPLICABLE_WITH_EVIDENCE: no
                 figure, the carrying wall-tile line named; never a quantity, never 0.
  THRESHOLD_FIELDS  (T-327 O-1 / O-2) every FIN.MARBLE.THRESHOLD line carries ONE material_state with its rule source
                 (the owner's marble threshold rule is an Urban method: URBAN_METHOD); every valued threshold / sill strip
                 line carries its three measures as a measure_pair field {m2, ml, pcs, price_one_basis} whose values are
                 byte-equal to the m2 / m.l / pcs its own formula prints (asserted; a mismatch stops).

R-T423-1 (every villa; integrates R-T246-1, R-T284-1, R-T388-1 b / d, R-T327-1, UP-FIN-PAINT-001, UP-QTY-STATUS-001):
(a) a listing binds to the line content it was read on (item, element, state, gross, net to 1e-6) and stops on a stale
line; (b) a listed deduction carries the id of what it deducts and one non-negative qty in the line's unit, and the list
closes gross to net; (c) a deduction sits on the face piece whose contour segment the opening lies on, and moving it
never moves the room total; (d) a NOT_APPLICABLE line carries no figure and names its evidence and its carrying line;
(e) one physical item has one material_state; (f) a line's alternative measures are fields equal to its formula, never
a second billable quantity; (g) nothing else moves.

Nothing else moves: every V3.0.59 line not named by the inputs is byte-identical (asserted); every code total
(A304.code_totals) is unchanged (asserted). Files: V3_0_60_BOQ_LINES.json / .csv, V3_0_60_INTEGRATION_LEDGER.json /
.csv, V3_0_60_DIFF.csv, V3_0_60_RUN.json. Nothing here names a project, a sheet, a layer or a coordinate.
"""

from __future__ import annotations

import copy
import hashlib
import re

from engine.source import arch_v30 as A30
from engine.source import arch_v302 as A302
from engine.source import arch_v304 as A304
from engine.source import arch_v305 as A305
from engine.source import arch_v3018 as A3018
from engine.source import arch_v3030 as A3030
from engine.source import arch_v3031 as A3031
from engine.source import arch_v3036 as A3036
from engine.source import arch_v3043 as A3043
from engine.source import arch_v3059 as A3059

DEFAULT_GUARD_CLASS = "TOOLING"          # T-212: re-books checker-merged ledgers and line states; adds no value
METHOD = "ARCH_TAKEOFF_V3.0.60"
EXTENDS = A3059.METHOD
CANDIDATE = A30.METHOD
POLICY_ID = "URBAN_BOQ_T423_ARCH_V3_0_60"
INPUTS_SCHEMA = "URBAN_V3060_INPUTS_V1"
LEDGER_SCHEMA = "URBAN_V3060_INTEGRATION_LEDGER_V1"
ROLLBACK = A30.ROLLBACK
InputsError = A3031.InputsError
_r = A3018._r
_fmt = A3030._fmt
RULE_ID, RULE_VERSION = "R-T423-1", "T-423"
REC_KEY = "split_remainder_v3060"
P_CEIL, P_FACE, P_NA, P_THR = "CEILING_LIST", "FACE_PIECE", "PAINT_NA", "THRESHOLD_FIELDS"
ACTIONS = ("LIST_CEILING", "MOVE_FACE_DEDUCTION", "NOT_APPLICABLE", "MATERIAL_STATE", "MEASURE_PAIR")
PIECE_OF = {"LIST_CEILING": P_CEIL, "MOVE_FACE_DEDUCTION": P_FACE, "NOT_APPLICABLE": P_NA,
            "MATERIAL_STATE": P_THR, "MEASURE_PAIR": P_THR}
CEILING = "FIN.CEILING"
PAINT = "FIN.PAINT"
TILE, BACKING = "FIN.WALL.TILE", "FIN.PLASTER"
THRESHOLD_CODES = ("FIN.MARBLE.THRESHOLD",)     # the codes the candidate carries (T-327 retypes + UP-THR-001 strips)
CODES_OF = {"LIST_CEILING": (CEILING,), "MOVE_FACE_DEDUCTION": (TILE, BACKING), "NOT_APPLICABLE": (PAINT,),
            "MATERIAL_STATE": THRESHOLD_CODES,
            "MEASURE_PAIR": THRESHOLD_CODES + ("FIN.FLOOR.PORCELAIN",)}   # the dry doorway strip carried as porcelain
VALUED_STATES = A3036.VALUED_STATES
NA_STATE, HELD_STATE = "NOT_APPLICABLE_WITH_EVIDENCE", "BLOCKED_RFI"
MATERIAL_STATES = ("SOURCE", "PROJECT_OWNER_FACT", "URBAN_METHOD", "BY_SPEC")
TOL = A3036.TOL                          # 0.0005: tools/boq_export_v1.QTY_MATCH_TOL (the T-330 check's tolerance)
BIND_TOL = 1e-6
HALF_UNIT_4DP = 0.5e-4 + 1e-9            # T-284 LEDGER_HALF_UNIT: a 4-decimal print of the same piece
MAX_Q = 500.0
LINE_ID_RE = re.compile(r"^L-[0-9a-f]{20}$")
MEASURE_RE = re.compile(r"= ([0-9]+(?:\.[0-9]+)?) m2 \(([0-9]+(?:\.[0-9]+)?) m\.l, ([0-9]+) pcs?\)")

PIECES = {
    P_CEIL: {"module": "engine/source/arch_v3060.py (a ceiling line restated by a HELD dome position gets that dome "
                       "piece as its listed deduction by id)",
             "policy": "CEILING_DOME_LIST_V1", "rule_id": "R-T246-1 + R-T284-1 (R-T423-1 a, b)",
             "owner_rules": ["Q-44 A (dome positions HELD: designer DCR-4)", "UP-QTY-STATUS-001 (held is blank)"],
             "owner_manual_method": "room ceiling = room plan less what is not decor ceiling (the open dome piece over "
                                    "the room), each deduction named",
             "drawing_method": "the merged T-283 dome table: the open disc of each dome split over the floor pieces "
                               "it covers (the structural drawing's 1F-roof slab plan, dome circle), 4-decimal print"},
    P_FACE: {"module": "engine/source/arch_v3060.py (a door hole moved to the face piece its contour segment lies "
                       "on; room total unchanged)",
             "policy": "OPENING_ON_ITS_FACE_PIECE_V1", "rule_id": "R-T388-1 b (R-T423-1 c)",
             "owner_rules": ["UP-FIN-WALL-001 (wet room tiled full height)", "Q-55 C (door head 2.20 where none is "
                             "printed)", "UP-QTY-STATUS-001"],
             "owner_manual_method": "each face = length x owner height less the openings that lie on it",
             "drawing_method": "the merged T-388 face table (T-250 walk: the straight face's drawn line carries no "
                               "door, door_m 0; the room walks the doorway as its own OFF:DOORWAY piece)"},
    P_NA: {"module": "engine/source/arch_v3060.py (a paint line of a fully wall-tiled room: NOT_APPLICABLE, no "
                     "figure, the carrying tile line named)",
           "policy": "PAINT_ON_FULL_TILE_NA_V1", "rule_id": "UP-FIN-PAINT-001 (R-T388-1 d, R-T423-1 d)",
           "owner_rules": ["UP-FIN-PAINT-001 (no paint where the wall is tiled)", "Q-37 A (pantry wet)",
                           "Q-48 A (wall tile full height)", "Q-30", "UP-QTY-STATUS-001"],
           "owner_manual_method": "paint only on the plastered faces that are not tiled; a fully tiled room has none",
           "drawing_method": "the merged T-388 face table: every pantry face tiled to the coat top (tile top = "
                             "backing top 3.65 on every determinate face)"},
    P_THR: {"module": "engine/source/arch_v3060.py (one material_state per threshold item; m2 / m.l / pcs as line "
                      "fields equal to the formula)",
            "policy": "THRESHOLD_FIELDS_V1", "rule_id": "R-T327-1 + O-T327-1 / O-T327-2 (R-T423-1 e, f)",
            "owner_rules": ["Q-55 C (wet-door marble threshold: owner rule, an Urban method)", "Q-68 C",
                            "UP-QTY-STATUS-001"],
            "owner_manual_method": "threshold = clear width x wall thickness (m2), the width (m.l), 1 pc",
            "drawing_method": "the merged T-327 strips (T-325 ledger: clear width and wall thickness by opening)"},
}
WAITING = dict(A3059.WAITING)
WAITING.update({
    "T423_GF_CEILING_LIST": "GF open-plan ceiling (V3.0.32 restated 110.922696 -> 101.137092 m2): its 9.785604 m2 gap is "
                            "explained only through still-held stair-zone / no-ceiling pieces that do not close by id "
                            "(stair zone 9.8536 + 1.7719 vs 9.7856, + the 0.777392 Checker slab): list SET ASIDE by "
                            "name, net unchanged (needs a T-284 ledger row by id)",
    "T423_1F_OPEN_PLAN": "1F open-plan ceiling parents (held by V3.0.32, no measured_net): nothing to list",
    "T423_FACE_LENGTH": "T-388 F2 face-length residuals (GF-07 0.120 m, GF-14 0.045 m, GF-08 0.140 m): NOT this "
                        "version (T-390)",
})


# ================================================================================================ inputs
def _need(s, keys, where):
    for k in keys:
        if s.get(k) in (None, ""):
            raise InputsError(f"{where}: missing {k}")


def _num(x, where, pos=False, top=MAX_Q):
    if isinstance(x, bool) or not isinstance(x, (int, float)) or x != x:
        raise InputsError(f"{where}: not a number ({x!r})")
    if x < 0 or (pos and x <= 0) or x > top:
        raise InputsError(f"{where}: {x} outside 0 .. {top} (unit slip or sign)")
    return float(x)


def _lid(x, where):
    if not isinstance(x, str) or not LINE_ID_RE.match(x):
        raise InputsError(f"{where}: line id {x!r}")
    return x


def _expect(e, where, valued):
    x = e.get("expect")
    if not isinstance(x, dict):
        raise InputsError(f"{where}: 'expect' binds the line as the ledger read it")
    _need(x, ("item_code", "element_id", "unit", "evidence_state"), where)
    if valued:
        _num(x.get("gross"), f"{where} gross")
        _num(x.get("measured_net"), f"{where} measured_net")
    return x


def _entry(e, srcs):
    a = e.get("action")
    if a not in ACTIONS:
        raise InputsError(f"entry action {a!r}")
    w = f"{a} {e.get('line_id')}"
    _lid(e.get("line_id"), w)
    A3043._tasks(e, srcs, w)
    e = dict(e)
    x = _expect(e, w, a == "LIST_CEILING")
    if x["item_code"] not in CODES_OF[a]:
        raise InputsError(f"{w}: {x['item_code']} is not a code {a} may change")
    if a == "LIST_CEILING":
        it = e.get("items") or []
        if len(it) != 1:
            raise InputsError(f"{w}: one dome piece per line (the ledger names one)")
        for i in it:
            _need(i, ("id", "print_m2", "source"), w)
            _num(i["print_m2"], f"{w} print", pos=True)
    elif a == "MOVE_FACE_DEDUCTION":
        _need(e, ("opening_id", "from_face", "to_face", "rec_key"), w)
        if e["from_face"] == e["to_face"] or not str(e["to_face"]).endswith("|OFF:DOORWAY"):
            raise InputsError(f"{w}: the hole moves to the room's OFF:DOORWAY piece, not {e['to_face']}")
    elif a == "NOT_APPLICABLE":
        _need(e, ("evidence", "carried_by"), w)
        _lid(e["carried_by"], f"{w} carried_by")
        if x["evidence_state"] != HELD_STATE:
            raise InputsError(f"{w}: only a blank paint line becomes NOT_APPLICABLE here")
    elif a == "MATERIAL_STATE":
        _need(e, ("material_state", "rule_source"), w)
        if e["material_state"] not in MATERIAL_STATES:
            raise InputsError(f"{w}: material state {e['material_state']}")
    elif a == "MEASURE_PAIR":
        for k in ("m2", "ml"):
            _num(e.get(k), f"{w} {k}", pos=True)
        if e.get("pcs") != 1:
            raise InputsError(f"{w}: one strip is 1 pc ({e.get('pcs')!r})")
    return e


def load_inputs(doc, project_id=None):
    """URBAN_V3060_INPUTS_V1 -> the validated doc.
    {"schema", "project_id", "sources": [{"task", "file", "sha256", "merge_commit", "checker_run"}],
     "set_aside": [{"line_id", "why"}],
     "entries": [{"action" (ACTIONS), "line_id", "source_tasks", "expect" {item_code, element_id, unit,
                  evidence_state, gross, measured_net}, ... per action:
                  LIST_CEILING items [{id, print_m2, source, note}];
                  MOVE_FACE_DEDUCTION rec_key, opening_id, from_face, to_face, finding;
                  NOT_APPLICABLE evidence, carried_by;
                  MATERIAL_STATE material_state, rule_source;
                  MEASURE_PAIR m2, ml, pcs}]}"""
    if not doc:
        return None
    if doc.get("schema") != INPUTS_SCHEMA:
        raise InputsError(f"project inputs: schema must be {INPUTS_SCHEMA}")
    if project_id and doc.get("project_id") not in (None, project_id):
        raise InputsError(f"project inputs are for {doc.get('project_id')!r}, the run is {project_id!r}")
    srcs = A3043._sources(doc)
    ents = [_entry(x, srcs) for x in doc.get("entries") or ()]
    if not ents:
        raise InputsError("no entry in the inputs")
    seen = set()
    for e in ents:
        k = (e["action"], e["line_id"], e.get("opening_id"))
        if k in seen:
            raise InputsError(f"{e['action']} {e['line_id']}: named twice (one line, one change per action)")
        seen.add(k)
    aside = {}
    for s in doc.get("set_aside") or ():
        _need(s, ("line_id", "why"), "set_aside")
        aside[_lid(s["line_id"], "set_aside")] = s["why"]
    clash = sorted(aside.keys() & {e["line_id"] for e in ents})
    if clash:
        raise InputsError(f"{clash}: set aside AND changed")
    return dict(doc, _sources=srcs, _entries=ents, _aside=aside)


# ================================================================================================ lines
def _rec(piece, srcs, **kw):
    return dict({"piece": piece, "policy": PIECES[piece]["policy"], "tasks": [s["task"] for s in srcs],
                 "ledgers": [s["file"] for s in srcs], "ledger_sha256": [s["sha256"] for s in srcs],
                 "merge_commits": [s["merge_commit"] for s in srcs], "checker_runs": [s["checker_run"] for s in srcs],
                 "rule_id": RULE_ID, "rule_version": RULE_VERSION, "release_status": "NOT RELEASED"}, **kw)


def _inp(new):
    new["calculation"] = dict(new["calculation"])
    inp = new["calculation"]["inputs"] = dict(new["calculation"].get("inputs") or {})
    return inp


def _fin(ln):
    from engine.source import boq_line as BL
    return BL.validate(ln)


def _assert_bound(b, e):
    x = e["expect"]
    w = f"{e['action']} {e['line_id']}"
    if b is None:
        raise InputsError(f"{w}: not in the candidate (stale binding)")
    loc = b.get("location") or {}
    ok = (b["item_code"] == x["item_code"] and loc.get("element_id") == x["element_id"] and b["unit"] == x["unit"]
          and b["evidence_state"] == x["evidence_state"])
    for k in ("gross", "measured_net"):
        if k in x:
            if x[k] is None:
                ok = ok and b.get(k) is None
            else:
                ok = ok and isinstance(b.get(k), (int, float)) and abs(b[k] - x[k]) <= BIND_TOL
    if not ok:
        raise InputsError(f"{w}: {b['item_code']} {loc.get('element_id')} {b['evidence_state']} gross {b.get('gross')} "
                          f"net {b.get('measured_net')} is not the ledger's {x} (stale binding: re-read the line)")


def _list_ceiling(b, e, srcs):
    gap = b["gross"] - b["measured_net"]
    it = e["items"][0]
    if abs(gap - it["print_m2"]) > HALF_UNIT_4DP:
        raise InputsError(f"{e['line_id']}: gap {gap:.6f} m2 is not the ledger piece {it['id']} {it['print_m2']} "
                          f"(half a unit of its 4th decimal): the list does not close by id")
    if b.get("deductions") or b.get("additions"):
        raise InputsError(f"{e['line_id']}: the line already lists {len(b.get('deductions') or [])} deductions "
                          "(applied once; a list is never merged into another)")
    ln = copy.deepcopy(b)
    item = {"id": it["id"], "qty": _r(gap), "unit": b["unit"], "source": it["source"][:300],
            "note": (it.get("note") or f"HELD piece, never ceiling: ledger print {it['print_m2']} m2")[:300]}
    ln["deductions"], ln["additions"] = [item], []
    inp = _inp(ln)
    inp[REC_KEY] = _rec(P_CEIL, srcs, action="LIST_CEILING", before={"deductions": [], "additions": []},
                        ledger_print_m2=it["print_m2"], listed_m2=_r(gap), residual_to_print=_r(gap - it["print_m2"]))
    A305._note(ln, f"{METHOD}: canonical list by id ({'+'.join(e['source_tasks'])}): gross {_fmt(ln['gross'])} - "
                   f"{_fmt(item['qty'])} ({it['id']}) = {_fmt(ln['measured_net'])} m2; quantity unchanged; NOT RELEASED")
    return _fin(ln), [{"what": it["id"], "why": "dome position HELD (Q-44 A, DCR-4): deducted, never ceiling",
                       "range": None, "scenario": None}]


def _faces_of(ln, key, where):
    rec = ((ln.get("calculation") or {}).get("inputs") or {}).get(key)
    if not isinstance(rec, dict) or not isinstance(rec.get("faces"), list):
        raise InputsError(f"{where}: no face record {key!r} on the line")
    return rec


def _move_face(b, e, srcs, ln=None):
    w = f"{e['line_id']} {e['opening_id']}"
    ln = copy.deepcopy(b) if ln is None else ln
    inp = _inp(ln)
    rec = copy.deepcopy(_faces_of(ln, e["rec_key"], w))
    inp[e["rec_key"]] = rec
    fs = {f["face_id"]: f for f in rec["faces"]}
    src, dst = fs.get(e["from_face"]), fs.get(e["to_face"])
    if src is None or dst is None:
        raise InputsError(f"{w}: face {e['from_face']} or {e['to_face']} is not on the line (stale ledger)")
    ops = [o for o in src.get("openings") or () if o.get("id") == e["opening_id"]]
    if len(ops) != 1 or any(o.get("id") == e["opening_id"] for o in dst.get("openings") or ()):
        raise InputsError(f"{w}: the opening is not once on {e['from_face']} and absent from {e['to_face']}")
    o = ops[0]
    tot0 = [f.get("net_m2") for f in rec["faces"]]
    src["openings"] = [x for x in src["openings"] if x is not o]
    dst["openings"] = list(dst.get("openings") or []) + [o]
    m2 = o.get("m2")
    if m2 is not None:
        if src.get("net_m2") is None or dst.get("net_m2") is None:
            raise InputsError(f"{w}: a valued hole between a HELD face and a valued one")
        src["net_m2"] = _r(src["net_m2"] + m2, 4)
        dst["net_m2"] = _r(dst["net_m2"] - m2, 4)
        if dst["net_m2"] < -1e-9:
            raise InputsError(f"{w}: the doorway piece {dst['net_m2']} m2 goes below 0 (the hole is not on it)")
        t0 = sum(x for x in tot0 if x is not None)
        t1 = sum(f["net_m2"] for f in rec["faces"] if f.get("net_m2") is not None)
        if abs(t0 - t1) > BIND_TOL:
            raise InputsError(f"{w}: the room's face total moves ({t0} -> {t1})")
    moved_list = 0
    om = inp.get("owner_manual_method")
    if isinstance(om, dict) and isinstance(om.get("deductions"), list):
        om = inp["owner_manual_method"] = dict(om, deductions=[dict(d) for d in om["deductions"]])
    ln["deductions"] = [dict(d) for d in ln.get("deductions") or ()]
    for d in list(ln["deductions"]) + (om["deductions"] if isinstance(om, dict) and isinstance(om.get("deductions"),
                                                                                             list) else []):
        # the canonical list item (and the owner-method record) of the hole names its face
        if e["opening_id"] in (d.get("id"), d.get("census_id"), d.get("opening"), d.get("opening_id")) and d.get("face") == e["from_face"]:
            d["face"] = e["to_face"]
            moved_list += 1
    log = rec.setdefault(REC_KEY, [])
    log.append({"action": "MOVE_FACE_DEDUCTION", "opening_id": e["opening_id"], "from_face": e["from_face"],
                "to_face": e["to_face"], "m2": m2, "list_items_moved": moved_list, "finding": e.get("finding"),
                "tasks": [s["task"] for s in srcs], "rule_id": RULE_ID})
    A305._note(ln, f"{METHOD}: {e['opening_id']} deducted on {e['to_face']} (its doorway piece), not on "
                   f"{e['from_face']} (R-T388-1 b); room total unchanged")
    return ln


def _not_applicable(b, e, srcs, by):
    car = by.get(e["carried_by"])
    if car is None or car["item_code"] != TILE or car["evidence_state"] not in VALUED_STATES or \
            (car.get("location") or {}).get("room_id") != (b.get("location") or {}).get("room_id"):
        raise InputsError(f"{e['line_id']}: carrying line {e['carried_by']} is not a valued wall-tile line of the room")
    ln = copy.deepcopy(b)
    was = {"state": b["evidence_state"], "measured_net": b.get("measured_net"),
           "bounded_range": b.get("bounded_range"), "gross": b.get("gross"), "rfi": b.get("rfi")}
    ln["evidence_state"], ln["measured_net"], ln["bounded_range"], ln["gross"], ln["rfi"] = NA_STATE, None, None, None, None
    why = f"{e['evidence']} | the face is carried by {e['carried_by']} ({car['item_code']})"
    ln["calculation"] = dict(ln["calculation"], formula=f"{METHOD}: NOT APPLICABLE (no figure): {why}"[:1500])
    inp = _inp(ln)
    inp[REC_KEY] = _rec(P_NA, srcs, action="NOT_APPLICABLE", was=was, evidence=e["evidence"],
                        carried_by=e["carried_by"])
    ln["notes"] = (f"{b.get('notes') or ''} | {METHOD}: NOT_APPLICABLE_WITH_EVIDENCE: {why}; NOT RELEASED")[:2000]
    return _fin(ln)


def formula_measures(ln):
    """(m2, m.l, pcs) as the line's own formula prints them; for a strip whose formula prints words only, as its own
    calculation inputs carry them (length_m = m.l, length_m x depth_m = m2 within 1e-6, one strip = 1 pc); or None."""
    calc = ln.get("calculation") or {}
    m = MEASURE_RE.search(calc.get("formula") or "")
    if m is not None:
        return (m.group(1), m.group(2), int(m.group(3)))
    inp = calc.get("inputs") or {}
    lm, dp = inp.get("length_m"), inp.get("depth_m")
    if isinstance(lm, (int, float)) and isinstance(dp, (int, float)) and isinstance(ln.get("measured_net"), (int, float)) \
            and lm > 0 and dp > 0 and abs(lm * dp - ln["measured_net"]) <= BIND_TOL:
        return (repr(float(ln["measured_net"])), repr(float(lm)), 1)
    return None


def _threshold(b, e, srcs, ln=None):
    ln = copy.deepcopy(b) if ln is None else ln
    inp = _inp(ln)
    rec = inp.setdefault(REC_KEY, _rec(P_THR, srcs, action="THRESHOLD_FIELDS", was={}))
    if e["action"] == "MATERIAL_STATE":
        rec["was"]["material_state"] = b["material_state"]
        rec["material_rule_source"] = e["rule_source"]
        ln["material_state"] = e["material_state"]
        A305._note(ln, f"{METHOD}: material_state {e['material_state']} ({e['rule_source'][:120]})")
    else:
        if b["evidence_state"] not in VALUED_STATES:
            raise InputsError(f"{e['line_id']}: a measure pair only on a valued strip line")
        fm = formula_measures(b)
        if fm is None:
            raise InputsError(f"{e['line_id']}: neither the formula nor the inputs carry m2 / m.l / pcs (nothing to carry)")
        if float(fm[0]) != e["m2"] or float(fm[1]) != e["ml"] or fm[2] != e["pcs"] or \
                abs(b["measured_net"] - e["m2"]) > BIND_TOL:
            raise InputsError(f"{e['line_id']}: measures {e['m2']} / {e['ml']} / {e['pcs']} are not the formula's "
                              f"{fm} or the net {b['measured_net']}")
        if b.get("measure_pair") is not None:
            raise InputsError(f"{e['line_id']}: the line already carries a measure pair (applied once)")
        rec["was"]["measure_pair"] = None
        ln["measure_pair"] = {"price_one_basis": True, "lines": [b["line_id"]], "units": ["m2", "lm", "nr"],
                              "measures": {"m2": e["m2"], "lm": e["ml"], "nr": e["pcs"]},
                              "formula_print": {"m2": fm[0], "lm": fm[1], "nr": fm[2]},
                              "physical_item": (b.get("location") or {}).get("element_id"),
                              "why": "one strip, three measures: bill the m2 OR the m.l OR the pcs, never two"}
        A305._note(ln, f"{METHOD}: measures m2 / m.l / pcs = {fm[0]} / {fm[1]} / {fm[2]} as fields (price one basis)")
    return ln


def changes_for(doc, prev):
    """-> (changes, log)."""
    if not doc:
        return [], {"piece": "T423", "state": "NO_PROJECT_INPUT"}
    if any(((ln.get("calculation") or {}).get("inputs") or {}).get(REC_KEY) for ln in prev):
        raise InputsError("the candidate already carries V3.0.60 records (applied once)")
    by = {ln["line_id"]: ln for ln in prev}
    for lid in doc["_aside"]:
        if lid not in by:
            raise InputsError(f"set aside {lid}: not in the candidate (stale name)")
    S = doc["_sources"]
    work, held, pieces, ev = {}, {}, {}, {}
    log = {"piece": "T423", "state": "RUN", "sources": doc["sources"], "by_action": {}, "set_aside": doc["_aside"]}
    for e in doc["_entries"]:
        b = by.get(e["line_id"])
        _assert_bound(b, e)
        srcs = [S[t] for t in e["source_tasks"]]
        cur = work.get(e["line_id"])
        a = e["action"]
        if a == "LIST_CEILING":
            if cur is not None:
                raise InputsError(f"{e['line_id']}: changed twice")
            cur, h = _list_ceiling(b, e, srcs)
            held.setdefault(e["line_id"], []).extend(h)
        elif a == "MOVE_FACE_DEDUCTION":
            cur = _move_face(b, e, srcs, cur)
        elif a == "NOT_APPLICABLE":
            if cur is not None:
                raise InputsError(f"{e['line_id']}: changed twice")
            cur = _not_applicable(b, e, srcs, by)
        else:
            cur = _threshold(b, e, srcs, cur)
        work[e["line_id"]] = cur
        pieces.setdefault(e["line_id"], set()).add(PIECE_OF[a])
        ev[e["line_id"]] = srcs
        log["by_action"][a] = log["by_action"].get(a, 0) + 1
    changes = []
    for lid, ln in work.items():
        b = by[lid]
        after = _fin(ln)
        ps = sorted(pieces[lid])
        changes.append(A305._change(ps[0], "CHANGE", b, after, drawing_reference="; ".join(s["file"] for s in ev[lid]),
                                    held=held.get(lid, []), downstream=[], verification=A3036._ver(ev[lid]),
                                    evidence_status="DRAWING-CONFIRMED", codes=ps, group=after["item_code"],
                                    step="+".join(ps)))
    log["by_action"] = dict(sorted(log["by_action"].items()))
    log["lines"] = len(changes)
    return changes, log


# ================================================================================================ checks
def check_split_remainder(lines, before=None):
    """on finished lines: every V3.0.60 ceiling list closes (TOL); every NOT_APPLICABLE paint line carries no figure
    and its carrying line is a valued tile line; every measure pair equals its formula; one material_state per
    threshold code; with `before`, no quantity of a changed line moved. -> summary."""
    by = {ln["line_id"]: ln for ln in lines}
    out = {"ceiling_lists": 0, "face_moves": 0, "not_applicable": 0, "measure_pairs": 0, "threshold_states": {}}
    for ln in lines:
        inp = (ln.get("calculation") or {}).get("inputs") or {}
        rec = inp.get(REC_KEY)
        if ln["item_code"] == "FIN.MARBLE.THRESHOLD":
            out["threshold_states"].setdefault(ln["material_state"], 0)
            out["threshold_states"][ln["material_state"]] += 1
        for v in inp.values():
            if isinstance(v, dict) and isinstance(v.get(REC_KEY), list):
                out["face_moves"] += len(v[REC_KEY])
        if not rec:
            continue
        if rec.get("action") == "LIST_CEILING":
            d = sum(x["qty"] for x in ln.get("deductions") or [])
            if not ln.get("deductions") or abs(ln["gross"] - d - ln["measured_net"]) > TOL or \
                    any(not x.get("id") or x.get("unit") != ln["unit"] for x in ln["deductions"]):
                raise ValueError(f"{METHOD}: {ln['line_id']}: ceiling list does not close gross to net by id")
            out["ceiling_lists"] += 1
        elif rec.get("action") == "NOT_APPLICABLE":
            car = by.get(rec.get("carried_by"))
            if ln["evidence_state"] != NA_STATE or ln.get("measured_net") is not None or ln.get("gross") is not None \
                    or car is None or car["evidence_state"] not in VALUED_STATES:
                raise ValueError(f"{METHOD}: {ln['line_id']}: NOT_APPLICABLE with a figure or no carrying line")
            out["not_applicable"] += 1
        if ln.get("measure_pair") and rec.get("action") == "THRESHOLD_FIELDS":
            fm = formula_measures(ln)
            mp = ln["measure_pair"]
            if fm is None or mp.get("price_one_basis") is not True or \
                    (mp["measures"]["m2"], mp["measures"]["lm"], mp["measures"]["nr"]) != (float(fm[0]), float(fm[1]),
                                                                                           fm[2]) \
                    or abs(ln["measured_net"] - mp["measures"]["m2"]) > BIND_TOL:
                raise ValueError(f"{METHOD}: {ln['line_id']}: measure pair is not its formula / net")
            out["measure_pairs"] += 1
    if len(out["threshold_states"]) > 1:
        raise ValueError(f"{METHOD}: FIN.MARBLE.THRESHOLD carries {sorted(out['threshold_states'])} (one item, one "
                         "material state)")
    if before is not None:
        b = {x["line_id"]: x for x in before}
        for ln in lines:
            o = b.get(ln["line_id"])
            if o is None or A30.line_sha(o) == A30.line_sha(ln):
                continue
            if ln["evidence_state"] == NA_STATE and o["evidence_state"] == HELD_STATE:
                continue
            if A30._qty(o) != A30._qty(ln) or o.get("gross") != ln.get("gross"):
                raise ValueError(f"{METHOD}: {ln['line_id']}: a quantity moved")
    return out


# ================================================================================================ integrate / write
def integrate(prev, changes, for_lead=()):
    """-> (V3.0.60 lines, identity). Changed lines replace their candidate line in place; every other candidate line
    is byte-identical (asserted); the earlier versions' checks re-run on the result (the V3.0.59 set)."""
    sid = {ln["line_id"]: i for i, ln in enumerate(prev)}
    out = list(prev)
    repl = set()
    allowed = {c for v in CODES_OF.values() for c in v}
    for c in changes:
        a = c["after"]
        if a["item_code"] not in allowed or c["action"] != "CHANGE":
            raise ValueError(f"{METHOD}: {c['action']} {a['item_code']} is not a change this version may make")
        i = sid.get(a["line_id"])
        if i is None or a["line_id"] in repl:
            raise ValueError(f"{METHOD}: a changed line is not a candidate line or changes twice")
        out[i] = a
        repl.add(a["line_id"])
    _o, i59 = A3059.integrate(out, [], for_lead)     # every V3.0.10 .. V3.0.59 family check, re-run on these lines
    ident = {"base_lines": len(prev), "v3_0_60_lines": len(out), "v3_0_60_rows": len(changes), "replaced": len(repl),
             "added": 0, "checks_v3_0_59": {k: v for k, v in i59.items() if k not in (
                 "base_lines", "v3_0_59_lines", "v3_0_59_rows", "replaced", "added", "outside_rows",
                 "outside_rows_identical_to_base", "outside_rows_sha256")},
             "split_remainder": check_split_remainder(out, prev)}
    pids = {(ln["project"]["project_id"], ln["project"]["revision_set_sha256"]) for ln in out}
    if len(pids) != 1:
        raise ValueError(f"{METHOD}: {len(pids)} project identities in the lines")
    outside = [ln for ln in prev if ln["line_id"] not in repl]
    bad = [a["line_id"] for a in outside if A30.line_sha(a) != A30.line_sha(out[sid[a["line_id"]]])]
    if bad:
        raise ValueError(f"{METHOD}: {len(bad)} candidate line(s) differ outside the named changes")
    ident.update(outside_rows=len(outside), outside_rows_identical_to_base=len(outside),
                 outside_rows_sha256=hashlib.sha256("".join(A30.line_sha(x) for x in outside).encode()).hexdigest())
    return out, ident


def ledger_rows(changes, released_lines=None):
    rel = {A30._key(ln): ln for ln in released_lines or ()}
    rows = []
    for c in changes:
        ref = c["after"]
        b29 = None
        if released_lines is not None:
            b29 = A30._qty(rel[A30._key(ref)]) if A30._key(ref) in rel else dict(A30._qty(None),
                                                                                 state="NOT_IN_RELEASED")
        loc = ref.get("location") or {}
        rows.append({"version": METHOD, "piece": c["piece"], "action": c.get("step"), "change": c["action"],
                     "line_id": ref["line_id"], "item_code": ref["item_code"], "floor": loc.get("floor"),
                     "room_id": loc.get("room_id"), "element_id": loc.get("element_id"), "unit": ref["unit"],
                     "before_released_v2_9": b29, "before_base": A30._qty(c.get("before")),
                     "after_v3_0_60": A30._qty(ref), "evidence_status": c.get("evidence_status"),
                     "still_held": c.get("held"), "release_status": "NOT RELEASED",
                     "material_state": [c["before"]["material_state"], ref["material_state"]],
                     "deductions_after": ref.get("deductions"), "measure_pair": ref.get("measure_pair"),
                     "owner_manual_method": PIECES[c["piece"]]["owner_manual_method"],
                     "drawing_derived_method": PIECES[c["piece"]]["drawing_method"],
                     "record": (ref["calculation"]["inputs"] or {}).get(REC_KEY),
                     "verification": c.get("verification") or {}, "rollback": ROLLBACK})
    return rows


LEDGER_CSV = ("version", "piece", "action", "change", "line_id", "item_code", "floor", "room_id", "element_id", "unit",
              "v2_9", "base", "v3_0_60", "material_state", "evidence_status", "still_held", "verification")
DIFF_CSV = ("line_id", "item_code", "floor", "element_id", "unit", "vs_base", "vs_released_v2_9", "v2_9", "base",
            "v3_0_60")


def ledger_csv(rows):
    def q(x):
        return A302._q(x) if x and (x.get("value") is not None or x.get("low") is not None or x.get("state")) else ""
    return A305._csv([{"version": r["version"], "piece": r["piece"], "action": r["action"], "change": r["change"],
                       "line_id": r["line_id"], "item_code": r["item_code"], "floor": r.get("floor") or "",
                       "room_id": r.get("room_id") or "", "element_id": r.get("element_id") or "", "unit": r["unit"],
                       "v2_9": q(r.get("before_released_v2_9")), "base": q(r.get("before_base")),
                       "v3_0_60": q(r.get("after_v3_0_60")), "material_state": " -> ".join(r["material_state"]),
                       "evidence_status": r["evidence_status"],
                       "still_held": "; ".join(x["what"] for x in r.get("still_held") or ())[:300],
                       "verification": f"{r['verification'].get('task')} "
                                       f"{' '.join(x[:8] for x in r['verification'].get('merge_commits') or ())}"}
                      for r in rows], LEDGER_CSV)


def diff_rows(prev, new, released_lines=None):
    b = {ln["line_id"]: ln for ln in prev}
    rel = {A30._key(ln): ln for ln in released_lines or ()}
    out = []
    for ln in new:
        o = b.get(ln["line_id"])
        vs = "ADDED" if o is None else ("SAME" if A30.line_sha(o) == A30.line_sha(ln) else
                                        ("CHANGED" if A30._qty(o) != A30._qty(ln) else "CHANGED_TEXT_ONLY"))
        r = rel.get(A30._key(ln)) if released_lines is not None else None
        vs29 = None if released_lines is None else ("NOT_IN_RELEASED" if r is None else
                                                    ("SAME_QUANTITY" if A30._qty(r) == A30._qty(ln) else
                                                     "QUANTITY_DIFFERS"))
        out.append({"line_id": ln["line_id"], "item_code": ln["item_code"], "floor": ln["location"].get("floor"),
                    "element_id": ln["location"].get("element_id"), "unit": ln["unit"], "vs_base": vs,
                    "vs_released_v2_9": vs29, "v2_9": A302._q(A30._qty(r)) if r else "",
                    "base": A302._q(A30._qty(o)) if o else "", "v3_0_60": A302._q(A30._qty(ln))})
    return out


def write(out, prev, changes, log, released_lines=None, for_lead=()):
    """the V3_0_60_* files beside the base candidate's files. -> (file names, identity, ledger)."""
    from pathlib import Path
    from engine.source import boq_line as BL
    out = Path(out)
    new, ident = integrate(prev, changes, for_lead)
    rows = ledger_rows(changes, released_lines)
    diff = diff_rows(prev, new, released_lines)
    named = {c["after"]["line_id"] for c in changes}
    stray = [d["line_id"] for d in diff if d["vs_base"] != "SAME" and d["line_id"] not in named]
    if stray:
        raise ValueError(f"{METHOD}: {len(stray)} line(s) changed outside the named changes")
    dsum = {}
    for d in diff:
        dsum.setdefault("vs_base", {}).setdefault(d["vs_base"], 0)
        dsum["vs_base"][d["vs_base"]] += 1
        if d["vs_released_v2_9"] is not None:
            dsum.setdefault("vs_released_v2_9", {}).setdefault(d["vs_released_v2_9"], 0)
            dsum["vs_released_v2_9"][d["vs_released_v2_9"]] += 1
    ident = dict(ident, diff=dsum)
    t0, t1 = A304.code_totals(prev), A304.code_totals(new)
    moved = {k: {"base": t0.get(k), "v3_0_60": t1.get(k)} for k in sorted(set(t0) | set(t1)) if t0.get(k) != t1.get(k)}
    for k, v in moved.items():      # a NOT_APPLICABLE paint line leaves the blocked count only; no figure moves
        b0, b1 = dict(v["base"] or {}), dict(v["v3_0_60"] or {})
        dl = b0.pop("lines", 0) - b1.pop("lines", 0)
        db = b0.pop("blocked_lines", 0) - b1.pop("blocked_lines", 0)
        if k.split("|")[0] != PAINT or b0 != b1 or dl != db or db < 0:
            raise ValueError(f"{METHOD}: a total moved: {k} {v}")
    led = {"schema": LEDGER_SCHEMA, "method": METHOD, "extends": EXTENDS, "candidate": CANDIDATE,
           "base": A30.BASE_METHOD, "released": A30.RELEASED_METHOD, "released_default": False, "rows": rows,
           "waiting_pieces": WAITING, "set_aside": log.get("set_aside"), "integration_package": True}
    run = {"method": METHOD, "policy": POLICY_ID, "extends": EXTENDS, "candidate": CANDIDATE,
           "base_method": A30.BASE_METHOD, "released_method": A30.RELEASED_METHOD, "released_default": False,
           "rollback": ROLLBACK, "identity": ident, "pieces": PIECES, "piece_logs": [log],
           "totals_moved_by_code": moved, "waiting_pieces": WAITING}
    files = {"V3_0_60_BOQ_LINES.json": BL.dumps(new),
             "V3_0_60_BOQ_LINES.csv": A30._lines_csv(new),
             "V3_0_60_INTEGRATION_LEDGER.json": A30._j(led),
             "V3_0_60_INTEGRATION_LEDGER.csv": ledger_csv(rows),
             "V3_0_60_DIFF.csv": A305._csv(diff, DIFF_CSV),
             "V3_0_60_RUN.json": A30._j(run)}
    for name, text in files.items():
        (out / name).write_text(text, encoding="utf-8")
    return sorted(files), ident, led


def policy_record():
    return {"method": METHOD, "extends": EXTENDS, "pieces": sorted(PIECES), "inputs_schema": INPUTS_SCHEMA,
            "released_default": False, "rollback": ROLLBACK, "actions": list(ACTIONS)}


__all__ = ["METHOD", "PIECES", "WAITING", "DEFAULT_GUARD_CLASS", "INPUTS_SCHEMA", "load_inputs", "changes_for",
           "check_split_remainder", "formula_measures", "integrate", "ledger_rows", "diff_rows", "write", "InputsError"]
