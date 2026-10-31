"""ARCH_TAKEOFF_V3.0.32 (T-284): the SAME opt-in BOQ candidate as ARCH_TAKEOFF_V3.0 .. V3.0.31 (engine.source.arch_v30,
arch_v301 .. arch_v3031), with its ceiling line family filled from the Checker-merged ceiling ledgers:

  CEILING_FILL  every interior FIN.CEILING line of the candidate (plan area of the room, PROVISIONAL since V3.0.x) is
                restated to the horizontal gypsum decor ceiling of the merged ceilings-r3 ledger (T-283) as bound to the
                line ids by the merged T-335 FILL table; the owner-method bulkhead vertical faces and the paintable
                gypsum surface become their own lines (owner Q-57 A modified: 'measure separately'); stair soffits and
                dome intrados are their own lines, HELD BLANK by item; exterior soffit lines untouched.

The physical element (ERS 2026-10-22 s.2.1): under each slab face, what is built: the horizontal gypsum decor ceiling
(0.15 below the slab, Q-48 A), bulkhead vertical faces on free beam edges with decor on the open side (owner method Q-48
A + Q-43, R-CEIL-R3-2), the paint system on the gypsum (Q-57 A mod (6)), and APART from them the stair soffit (the
flight's underside: a stair finish, T-281), the open dome position (its intrados is the dome finish, DCR-4) and
no-ceiling parts (void, shaft, light well). One surface, one line, one layer per line (R-T335-1).

Line states (never a value of this module's own):
  decor ceiling (FIN.CEILING)        quantity = the ledger's decor DRAWING-CONFIRMED; the line keeps its state
                                     (PROVISIONAL: board type not in a plan, O-P8-02 / Q-52 C), material BY_SPEC;
  a line group whose split is not drawn (the 1F living normal + double-height lines): both lines BLANK parents naming
                                     the group line, ONE group line carries the decor (never split pro rata);
  a held stair-well line             stays BLANK; its determinate decor part (if any) is its own line;
  bulkhead faces (FIN.CEILING.BULKHEAD) ASSUMED — OWNER-APPROVED (Q-48 A + Q-43) -> PROVISIONAL;
  ceiling paint (FIN.PAINT.CEILING)  ASSUMED — OWNER-APPROVED (Q-57 A mod (6)) = decor + bulkhead faces of the room,
                                     -> PROVISIONAL;
  stair soffit (FIN.STAIR.SOFFIT) / dome intrados (FIN.DOME.SOFFIT): BLOCKED_RFI, BLANK, the merged figures beside.

R-T284-1 (every villa): a room's decor ceiling in ONE FIN.CEILING figure (a group of lines carries it once); bulkhead
faces and ceiling paint never inside the ceiling area line; paint of a room = its decor + its bulkhead faces (one layer,
one line); stair soffit and dome intrados never in a ceiling line; HELD / UNKNOWN are BLANK, never 0; the bound lines
must stand in the candidate as bound (stale binding stops).

Every line outside the rows is byte-identical to V3.0.31; inside a row only quantity, state, basis, rfi, calculation and
notes change (asserted). Files: V3_0_32_BOQ_LINES.json / .csv, V3_0_32_INTEGRATION_LEDGER.json / .csv, V3_0_32_DIFF.csv,
V3_0_32_RUN.json. Nothing here names a project, a sheet, a layer or a coordinate: every value comes from the inputs.
"""

from __future__ import annotations

import copy
import hashlib
import json

from engine.source import arch_v30 as A30
from engine.source import arch_v302 as A302
from engine.source import arch_v304 as A304
from engine.source import arch_v305 as A305
from engine.source import arch_v3018 as A3018
from engine.source import arch_v3030 as A3030
from engine.source import arch_v3031 as A3031

DEFAULT_GUARD_CLASS = "TOOLING"          # T-212: re-books checker-merged ledgers; adds no default value
METHOD = "ARCH_TAKEOFF_V3.0.32"
EXTENDS = A3031.METHOD
CANDIDATE = A30.METHOD
POLICY_ID = "URBAN_BOQ_T284_ARCH_V3_0_32"
INPUTS_SCHEMA = "URBAN_V3032_INPUTS_V1"
LEDGER_SCHEMA = "URBAN_V3032_INTEGRATION_LEDGER_V1"
ROLLBACK = A30.ROLLBACK
InputsError = A3031.InputsError
_r = A3018._r
_fmt = A3030._fmt
RULE_ID, RULE_VERSION = "R-T284-1", "T-284"
PIECE = "CEILING_FILL"
REC_KEY = "ceiling_fill_v3032"
CEILING, BULKHEAD, PAINT = "FIN.CEILING", "FIN.CEILING.BULKHEAD", "FIN.PAINT.CEILING"
STAIR_SOFFIT, DOME_SOFFIT = "FIN.STAIR.SOFFIT", "FIN.DOME.SOFFIT"
NEW_ITEMS = {   # item master entries for the codes boq_line.ITEMS does not carry (en, ar, trade, subtrade)
    BULKHEAD: ("Ceiling bulkhead vertical faces (gypsum)", "واجهات الجسور الجبسية (البلكهيد)", "CEILING", "BULKHEAD"),
    PAINT: ("Paint on gypsum ceilings (horizontal + bulkhead faces)", "صبغ الأسقف الجبسية", "PAINT", "CEILING"),
    STAIR_SOFFIT: ("Stair soffit finish (flight / landing undersides)", "تشطيب بطنية الدرج", "STAIR_FINISH", "SOFFIT"),
    DOME_SOFFIT: ("Dome intrados finish", "تشطيب باطن القبة", "CEILING", "DOME"),
}
ITEMS = {CEILING: "m2", BULKHEAD: "m2", PAINT: "m2", STAIR_SOFFIT: "m2", DOME_SOFFIT: "m2"}
ROLES = ("CEILING", "STAIRWELL", "EXTERIOR")
TOL = 1e-6
# inside a REPLACE row only these line keys change (everything else byte-identical to V3.0.31)
ROW_KEYS = ("evidence_state", "measured_net", "bounded_range", "rfi", "notes", "calculation", "gross")
# (a blank parent drops its numeric gross: a held line carries no figure, V3.0.24 NA_GROSS; a valued line keeps it)

PIECES = {
    PIECE: {
        "module": "engine/source/arch_v3032.py (ceiling line family filled from the Checker-merged ceilings r3 ledger "
                  "(T-283) bound to the candidate's line ids by the Checker-merged T-335 FILL table; bulkhead faces "
                  "and ceiling paint their own lines; stair soffits (T-281) and dome intrados HELD BLANK by item)",
        "policy": "CEILING_FILL_V1", "rule_id": RULE_ID, "rule_version": RULE_VERSION,
        "owner_rules": ["Q-48 A (decor ceiling 0.15 m below the slab, wet rooms included)",
                        "Q-43 (owner heights; bulkhead depth below the decor plane)",
                        "Q-57 A modified (owner 2026-10-20 12:02: measure separately horizontal gypsum, vertical "
                        "bulkhead faces, actual paintable surfaces; no cement plaster on a gypsum ceiling)",
                        "Q-52 C / O-P8-02 (board type not in a plan: every ceiling line PROVISIONAL, material BY_SPEC)",
                        "Q-44 A + designer DCR-4 (dome opening: what closes it)", "UP-CEIL-001", "UP-QTY-STATUS-001",
                        "WORKFLOW_CONTROLS 2026-10-21 s.4 / s.5; ERS 2026-10-22 s.2 - s.4"],
        "owner_manual_method": "owner Q-48 A / Q-57 A mod: the ceiling of a room is its horizontal gypsum decor "
                               "ceiling 0.15 below the slab (area between the finish faces, less what is not decor: "
                               "void, shaft, light well, stair zone, open dome), bulkhead vertical faces = free beam "
                               "edge x 0.15 where decor is on the open side (Q-43), paint = decor + bulkhead faces",
        "drawing_method": "per slab face on the roof-slab plans (T-139 faces, T-271 r2b / T-283 r3): the room's floor "
                          "piece less the drawn no-ceiling parts, stair footprints distributed over every face they "
                          "cross (R-CEIL-R3-1), dome discs from the drawn circles; beam edges run by run "
                          "(R-CEIL-R3-2); bound to the candidate line ids by T-335 (R-T335-1)"},
}
WAITING = dict(A3031.WAITING)
WAITING.update({
    "CEILING_BOARD_TYPE": "ceiling board type per room (gypsum / moisture-resistant): not in a plan (Q-52 C, Q-57 A "
                          "mod (2)): the area lines are PROVISIONAL, material BY_SPEC",
    "CEILING_COVES_EDGES": "coves / cornices (no detail drawn), opening edges, bulkhead edges on CONFLICT / HELD beams, "
                           "the drawing-derived bulkhead candidate (D-40): HELD by name in each room line's record",
    "STAIR_SOFFIT_T281": "stair soffit finish per stair: T-281 ledger not verified whole; method O vs D; curved / "
                         "winder rows HELD: one BLANK line per stair, the merged figures beside",
    "DOME_INTRADOS_DCR4": "dome intrados finish: what closes the opening (designer DCR-4): one BLANK line per dome, the "
                          "disc and the S0 intrados beside",
    "HIDDEN_BAND_Q52C": "the wall band above the decor underside (0 .. 53.851 m2, T-335): HELD (Q-52 C), in no line",
})


# ================================================================================================ inputs
def _need(s, keys, where):
    for k in keys:
        if s.get(k) in (None, ""):
            raise InputsError(f"{where}: {k} missing")


def _pos(x, where):
    if not isinstance(x, (int, float)) or isinstance(x, bool) or x != x or x <= 0:
        raise InputsError(f"{where}: {x!r} is not a positive figure (held is BLANK, never 0)")
    return float(x)


def _held_list(h, where):
    for it in h or ():
        _need(it, ("what", "why"), f"{where} held item")
        b = it.get("beside")
        if b is not None and (not isinstance(b, (int, float)) or isinstance(b, bool) or b <= 0):
            raise InputsError(f"{where} held item {it['what']}: beside {b!r} (a held item is blank or named with its "
                              f"positive figure beside, never 0)")


def load_inputs(doc, project_id=None):
    """URBAN_V3032_INPUTS_V1 -> the validated doc."""
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
    rows, seen_lines, seen_rooms = [], set(), set()
    for i, r in enumerate(doc.get("rows") or ()):
        where = f"row {i} {r.get('room_id') or r.get('line_ids')}"
        role = r.get("role")
        if role not in ROLES:
            raise InputsError(f"{where}: role {role!r}")
        for lid in r.get("line_ids") or ():
            if lid in seen_lines:
                raise InputsError(f"{where}: line {lid} in two rows (one line, one row)")
            seen_lines.add(lid)
        if role == "EXTERIOR":
            if r.get("action") != "UNCHANGED" or len(r.get("line_ids") or ()) != 1:
                raise InputsError(f"{where}: an exterior soffit line is carried unchanged, by its id")
            rows.append(r)
            continue
        _need(r, ("room_id", "floor", "source_task", "held_source_task"), where)
        for t in (r["source_task"], r["held_source_task"]):
            if t not in srcs:
                raise InputsError(f"{where}: no merged source for {t!r}")
        if r["room_id"] in seen_rooms:
            raise InputsError(f"{where}: room {r['room_id']} in two rows (one room, one decor figure)")
        seen_rooms.add(r["room_id"])
        ids = r.get("line_ids") or []
        bound = {b["line_id"]: b for b in r.get("bound") or ()}
        if set(bound) != set(ids):
            raise InputsError(f"{where}: bound lines {sorted(bound)} are not the row's {ids}")
        decor = r.get("decor_m2")
        if role == "CEILING":
            _pos(decor, f"{where} decor")
            if r.get("decor_status") != "DRAWING-CONFIRMED":
                raise InputsError(f"{where}: decor status {r.get('decor_status')!r}")
            if len(ids) > 1 and not r.get("group_cause"):
                raise InputsError(f"{where}: a group of {len(ids)} lines needs its named cause (never pro rata)")
            if not ids and r.get("before_m2") is not None:
                raise InputsError(f"{where}: a new line has no 'before'")
        else:
            if len(ids) != 1:
                raise InputsError(f"{where}: a stair-well row restates ONE held line")
            if decor is not None:
                _pos(decor, f"{where} decor part")
        bh = r.get("bulkhead_m2")
        if bh is not None:
            _pos(bh, f"{where} bulkhead")
            if not r.get("bulkhead_source"):
                raise InputsError(f"{where}: an owner-method bulkhead names its owner rule (WORKFLOW_CONTROLS s.4)")
        p = r.get("paint_m2")
        if p is not None:
            _pos(p, f"{where} paint")
            if not r.get("paint_source"):
                raise InputsError(f"{where}: ceiling paint names its owner rule (WORKFLOW_CONTROLS s.4)")
            if abs(p - ((decor or 0.0) + (bh or 0.0))) > TOL:
                raise InputsError(f"{where}: paint {p} is not decor {decor} + bulkhead faces {bh} (one layer, one "
                                  f"surface: R-T284-1)")
        elif decor:
            raise InputsError(f"{where}: a decor ceiling without its paint row (Q-57 A mod (6))")
        _held_list(r.get("held"), where)
        rows.append(r)
    domes, stairs = [], []
    for d in doc.get("domes") or ():
        where = f"dome {d.get('dome')}"
        _need(d, ("dome", "element_id", "floor", "held_reason", "source_task"), where)
        _pos(d.get("disc_m2"), f"{where} disc")
        if abs(d["disc_m2"] - d["over_pieces_m2"] - d["over_walls_m2"]) > 1e-3:
            raise InputsError(f"{where}: disc {d['disc_m2']} is not over pieces + over walls (closure)")
        domes.append(d)
    for s in doc.get("stairs") or ():
        where = f"stair {s.get('stair')}"
        _need(s, ("stair", "element_id", "floor", "held_reason", "range_cause", "source_task"), where)
        lo, hi = _pos(s.get("true_lo_m2"), where), _pos(s.get("true_hi_m2"), where)
        if lo > hi + TOL:
            raise InputsError(f"{where}: low {lo} above high {hi}")
        stairs.append(s)
    for x in domes + stairs:
        if x["source_task"] not in srcs:
            raise InputsError(f"{x['element_id']}: no merged source for {x['source_task']!r}")
    if not any(r["role"] == "CEILING" for r in rows):
        raise InputsError("no ceiling row in the inputs")
    return dict(doc, _sources=srcs, _rows=rows, _domes=domes, _stairs=stairs)


# ================================================================================================ lines
def _rec(src, **kw):
    return dict({"policy": PIECES[PIECE]["policy"], "task": src["task"], "ledger": src["file"],
                 "ledger_sha256": src["sha256"], "merge_commit": src["merge_commit"], "checker_run": src["checker_run"],
                 "rule_id": RULE_ID, "rule_version": RULE_VERSION, "release_status": "NOT RELEASED"}, **kw)


def _ver(src):
    return {"task": src["task"], "merge_commit": src["merge_commit"], "verifier_run": src["checker_run"],
            "ledger": src["file"], "ledger_sha256": src["sha256"]}


def _held_txt(held, limit=700):
    t = "; ".join(f"{h['what']}" + (f" ({_fmt(h['beside'])} {h.get('unit') or ''} beside)".replace(" )", ")")
                                    if h.get("beside") is not None else "") for h in held or ())
    return t[:limit]


def _new(tmpl, *, item_code, unit, evidence_state, element_id, floor, room_id, phys, formula, rec, measured_net=None,
         rfi=None, notes=""):
    from engine.source import boq_line as BL
    pr = tmpl["project"]
    kw = {}
    if item_code in NEW_ITEMS:
        en, ar, tr, sub = NEW_ITEMS[item_code]
        kw = {"item_en": en, "item_ar": ar, "trade": tr, "subtrade": sub}
    loc = tmpl.get("location") or {}
    ln = BL.make_line(project_id=pr["project_id"], revision_set_sha256=pr["revision_set_sha256"], item_code=item_code,
                      unit=unit, evidence_state=evidence_state, measured_net=measured_net, element_id=element_id,
                      floor=floor, room_id=room_id,
                      room_name_en=loc.get("room_name_en") if loc.get("room_id") == room_id else None,
                      room_name_ar=loc.get("room_name_ar") if loc.get("room_id") == room_id else None,
                      physical_element=phys, formula=formula.replace(" = ", " -> ")[:700] if measured_net is None
                      else formula[:700], inputs={REC_KEY: rec},
                      documents=copy.deepcopy(tmpl["source"]["documents"]),
                      geometry_source=tmpl["source"]["geometry_source"],
                      geometry_confidence=tmpl["source"].get("geometry_confidence") or "INFERRED_CANDIDATE",
                      rule_id=RULE_ID, rule_version=RULE_VERSION, material_state="BY_SPEC", rfi=rfi,
                      notes=notes[:600], **kw)
    ln["project"] = copy.deepcopy(pr)
    return BL.validate(ln)


def _assert_bound(b, c):
    """a bound line must stand in the candidate exactly as bound (stale binding stops)."""
    if b is None:
        raise InputsError(f"bound line {c['line_id']}: not in the candidate (stale binding)")
    q, cq = b.get("measured_net"), c.get("measured_net")
    same = b["item_code"] == CEILING and b["evidence_state"] == c["evidence_state"] and \
        (b.get("location") or {}).get("element_id") == c["element_id"] and (
        (q is None and cq is None) or (q is not None and cq is not None and abs(q - cq) <= TOL))
    if not same:
        raise InputsError(f"bound line {c['line_id']}: {b['item_code']} {b['evidence_state']} {q} is not the bound "
                          f"{CEILING} {c['evidence_state']} {cq} (stale binding: re-bind before integrating)")
    if ((b.get("calculation") or {}).get("inputs") or {}).get(REC_KEY):
        raise InputsError(f"line {c['line_id']}: already filled (the fill is applied once)")


def _restate(b, *, measured_net, state, formula, rec, note, rfi=None):
    """the line in place: only quantity, state, rfi, calculation and notes change."""
    from engine.source import boq_line as BL
    ln = copy.deepcopy(b)
    ln["evidence_state"] = state
    ln["measured_net"] = None if measured_net is None else _r(measured_net)
    ln["bounded_range"] = None
    ln["rfi"] = rfi
    if measured_net is None:
        ln["gross"] = None
        formula = formula.replace(" = ", " -> ")
    ln["calculation"] = dict(ln.get("calculation") or {}, formula=formula[:700],
                             inputs=dict((ln.get("calculation") or {}).get("inputs") or {}, **{REC_KEY: rec}))
    A305._note(ln, note)
    return BL.validate(ln)


def _ev_line(ev):
    return {"DRAWING-CONFIRMED": "DRAWING-CONFIRMED", "OA": "ASSUMED — OWNER-APPROVED", "HELD": "HELD"}[ev]


def changes_for(doc, l3031):
    """-> (changes, log)."""
    if not doc:
        return [], {"piece": PIECE, "state": "NO_PROJECT_INPUT"}
    by = {ln["line_id"]: ln for ln in l3031}
    if any(ln["item_code"] in NEW_ITEMS for ln in l3031) or \
            any(((ln.get("calculation") or {}).get("inputs") or {}).get(REC_KEY) for ln in l3031):
        raise InputsError("the candidate already carries the V3.0.32 ceiling fill (applied once)")
    seen = set(by)
    changes = []
    log = {"piece": PIECE, "state": "RUN", "sources": doc["sources"], "by_action": {}, "m2": {}, "blank": {},
           "rows": len(doc["_rows"]), "lines_added": 0, "lines_restated": 0}
    S = doc["_sources"]
    ceil_tmpl = A3030._template(l3031, (CEILING,))

    def add(ln, src, ev, held=None, parent=None, codes=()):
        if ln["line_id"] in seen:
            raise ValueError(f"{METHOD}: line {ln['location']['element_id']} repeats an id")
        seen.add(ln["line_id"])
        h = []
        if ln["evidence_state"] == "BLOCKED_RFI":
            h = [{"what": f"{ln['item_code']} {ln['location']['element_id']}", "why": ln["rfi"]["question"][:300],
                  "range": (ln["calculation"]["inputs"][REC_KEY].get("beside")), "scenario": None}]
        changes.append(A305._change(PIECE, "ADD", None, ln, drawing_reference=src["file"], held=h + (held or []),
                                    downstream=[], verification=_ver(src), evidence_status=ev,
                                    codes=[PIECE, "ADD"] + list(codes), group=ln["item_code"],
                                    parent_line_id=parent))
        log["lines_added"] += 1
        _count(ln)

    def rep(b, after, src, ev, held=None, codes=()):
        changes.append(A305._change(PIECE, "REPLACE", b, after, drawing_reference=src["file"], held=held or [],
                                    downstream=[], verification=_ver(src), evidence_status=ev,
                                    codes=[PIECE, "REPLACE"] + list(codes), group=after["item_code"]))
        log["lines_restated"] += 1
        _count(after)

    def _count(ln):
        k = f"{ln['item_code']} {ln['evidence_state']}"
        log["by_action"][k] = log["by_action"].get(k, 0) + 1
        if ln.get("measured_net") is not None:
            log["m2"][ln["item_code"]] = _r(log["m2"].get(ln["item_code"], 0.0) + ln["measured_net"])
        else:
            log["blank"][ln["item_code"]] = log["blank"].get(ln["item_code"], 0) + 1

    for r in doc["_rows"]:
        if r["role"] == "EXTERIOR":
            b = by.get(r["line_ids"][0])
            if b is None or b["item_code"] != CEILING:
                raise InputsError(f"exterior soffit line {r['line_ids'][0]}: not in the candidate (stale binding)")
            continue
        src, hsrc = S[r["source_task"]], S[r["held_source_task"]]
        for c in r.get("bound") or ():
            _assert_bound(by.get(c["line_id"]), c)
        room, fl = r["room_id"], r["floor"]
        held = r.get("held") or []
        bl = [by[lid] for lid in r["line_ids"]]
        tmpl = bl[0] if bl else ceil_tmpl
        hrows = [{"what": f"{CEILING} {room}: {h['what']}", "why": h["why"][:300], "range": None, "scenario": None}
                 for h in held]
        base = dict(room=room, role=r["role"], classes=r.get("classes"), decor_status=r.get("decor_status"),
                    held_ledger=hsrc["task"], still_held=held, before=[A3018._before_rec(x) for x in bl])
        decor_line = None
        if r["role"] == "CEILING" and len(bl) == 1:
            b = bl[0]
            rec = _rec(src, action="RESTATE", decor_m2=r["decor_m2"], evidence_status="DRAWING-CONFIRMED",
                       decor_confirms_line=bool(r.get("decor_confirms_line")), **base)
            formula = (f"{room} horizontal gypsum decor ceiling {_fmt(r['decor_m2'])} m2 (DRAWING-CONFIRMED, ceilings "
                       f"r3 {hsrc['task']} bound by {src['task']}): plan area {_fmt(b.get('measured_net'))} less what "
                       f"is not decor (named in calculation.inputs.{REC_KEY}.still_held); bulkhead faces and paint "
                       f"their own lines")
            after = _restate(b, measured_net=r["decor_m2"], state=b["evidence_state"], formula=formula, rec=rec,
                             note=f"{METHOD}: decor ceiling ({src['task']} MERGED {src['merge_commit'][:8]}); "
                                  f"DRAWING-CONFIRMED; board type BY_SPEC; NOT RELEASED")
            rep(b, after, src, "DRAWING-CONFIRMED", hrows, codes=("DECOR",))
            decor_line = after
        elif r["role"] == "CEILING" and not bl:
            eid = r["elements"][0]
            rec = _rec(src, action="ADD", decor_m2=r["decor_m2"], evidence_status="DRAWING-CONFIRMED", **base)
            ln = _new(tmpl, item_code=CEILING, unit="m2", evidence_state="PROVISIONAL", element_id=eid, floor=fl,
                      room_id=room, phys="horizontal gypsum decor ceiling",
                      formula=f"{room} horizontal gypsum decor ceiling {_fmt(r['decor_m2'])} m2 (DRAWING-CONFIRMED; "
                              f"the candidate carried no ceiling line for this room: missing scope)",
                      rec=rec, measured_net=_r(r["decor_m2"]),
                      notes=f"{METHOD}: missing ceiling line added ({src['task']} MERGED {src['merge_commit'][:8]}); "
                            f"DRAWING-CONFIRMED; board type BY_SPEC; NOT RELEASED")
            add(ln, src, "DRAWING-CONFIRMED", hrows, codes=("DECOR", "MISSING_SCOPE"))
            decor_line = ln
        else:
            # a group of lines whose split is not drawn, or a held stair-well line: parents BLANK, one part line
            eid = f"{room}:ceiling#DECOR" + ("_GROUP" if r["role"] == "CEILING" else "_PART")
            part = None
            if r.get("decor_m2"):
                rec = _rec(src, action="PART", parents=[x["line_id"] for x in bl], decor_m2=r["decor_m2"],
                           evidence_status="DRAWING-CONFIRMED", group_cause=r.get("group_cause"), **base)
                part = _new(tmpl, item_code=CEILING, unit="m2", evidence_state="PROVISIONAL", element_id=eid,
                            floor=fl, room_id=room, phys="horizontal gypsum decor ceiling",
                            formula=f"{room} horizontal gypsum decor ceiling {_fmt(r['decor_m2'])} m2 "
                                    f"(DRAWING-CONFIRMED) for line(s) {', '.join(x['line_id'] for x in bl)}"
                                    + (f": {r['group_cause']}" if r.get("group_cause") else
                                       ": the determinate part of a held stair-well ceiling"),
                            rec=rec, measured_net=_r(r["decor_m2"]),
                            notes=f"{METHOD}: decor ceiling part ({src['task']} MERGED {src['merge_commit'][:8]}); "
                                  f"DRAWING-CONFIRMED; board type BY_SPEC; NOT RELEASED")
            for b in bl:
                q = (f"HELD (blank in the BOQ, never 0): {room} ceiling line {b['location'].get('element_id')}: "
                     + (f"the room's decor ceiling is carried ONCE on line {part['line_id']} ({r['group_cause']}); "
                        if part is not None and r["role"] == "CEILING" else "")
                     + (f"its determinate decor part is line {part['line_id']}; " if part is not None and
                        r["role"] == "STAIRWELL" else "")
                     + (f"stair soffit pieces are the stair soffit lines ({STAIR_SOFFIT}); " if r["role"] ==
                        "STAIRWELL" else "")
                     + f"held: {_held_txt(held, 500)}")
                rec = _rec(src, action="PARENT", part_line=part["line_id"] if part else None,
                           evidence_status="HELD", **base)
                after = _restate(b, measured_net=None, state="BLOCKED_RFI", formula=q, rec=rec,
                                 rfi={"question": q[:900], "unlocks": b["location"].get("element_id")},
                                 note=f"{METHOD}: held ceiling parent ({src['task']} MERGED "
                                      f"{src['merge_commit'][:8]}); blank in the BOQ, never 0")
                rep(b, after, src, "HELD", hrows, codes=("PARENT",))
            if part is not None:
                add(part, src, "DRAWING-CONFIRMED", [], parent=bl[0]["line_id"] if bl else None, codes=("PART",))
                decor_line = part
        bh = r.get("bulkhead_m2")
        if bh:
            rec = _rec(src, action="ADD", bulkhead_m2=bh, evidence_status="ASSUMED — OWNER-APPROVED",
                       owner_source=r["bulkhead_source"], ceiling_line=decor_line["line_id"], room=room)
            ln = _new(tmpl, item_code=BULKHEAD, unit="m2", evidence_state="PROVISIONAL",
                      element_id=f"{room}:bulkhead", floor=fl, room_id=room,
                      phys="bulkhead vertical faces under the decor ceiling",
                      formula=f"{room} bulkhead vertical faces {_fmt(bh)} m2 = free beam edges with decor on the open "
                              f"side x 0.15 m (owner method, {r['bulkhead_source']})",
                      rec=rec, measured_net=_r(bh),
                      notes=f"{METHOD}: ASSUMED — OWNER-APPROVED ({r['bulkhead_source'][:80]}); NOT RELEASED")
            add(ln, src, "ASSUMED — OWNER-APPROVED (" + r["bulkhead_source"][:60] + ")", codes=("BULKHEAD",))
        if r.get("paint_m2"):
            rec = _rec(src, action="ADD", paint_m2=r["paint_m2"], decor_m2=r["decor_m2"], bulkhead_m2=bh,
                       evidence_status="ASSUMED — OWNER-APPROVED", owner_source=r["paint_source"],
                       ceiling_line=decor_line["line_id"], room=room)
            ln = _new(tmpl, item_code=PAINT, unit="m2", evidence_state="PROVISIONAL",
                      element_id=f"{room}:ceiling paint", floor=fl, room_id=room,
                      phys="paint system on the gypsum ceiling (horizontal + bulkhead faces)",
                      formula=f"{room} ceiling paint {_fmt(r['paint_m2'])} m2 = decor {_fmt(r['decor_m2'])}"
                              + (f" + bulkhead faces {_fmt(bh)}" if bh else "") + f" ({r['paint_source']})",
                      rec=rec, measured_net=_r(r["paint_m2"]),
                      notes=f"{METHOD}: ASSUMED — OWNER-APPROVED (Q-57 A mod (6)); NOT RELEASED")
            add(ln, src, "ASSUMED — OWNER-APPROVED (Q-57 A mod (6))", codes=("PAINT",))
    for d in doc["_domes"]:
        src = S[d["source_task"]]
        beside = {"disc_m2": d["disc_m2"], "over_pieces_m2": d["over_pieces_m2"], "over_walls_m2": d["over_walls_m2"],
                  "intrados_s0": d.get("intrados_s0_beside")}
        q = (f"HELD (blank in the BOQ, never 0): {d['dome']} dome intrados finish: {d['held_reason']}; open disc "
             f"{_fmt(d['disc_m2'])} m2 beside (over the rooms {d.get('rooms')}; never in {CEILING}); S0 intrados "
             f"{d.get('intrados_s0_beside')}")
        rec = _rec(src, action="ADD", dome=d["dome"], evidence_status="HELD", beside=beside,
                   held_reason=d["held_reason"])
        ln = _new(ceil_tmpl, item_code=DOME_SOFFIT, unit="m2", evidence_state="BLOCKED_RFI",
                  element_id=d["element_id"], floor=d["floor"], room_id=None, phys="dome intrados finish", formula=q,
                  rec=rec, rfi={"question": q[:900], "unlocks": d["element_id"]},
                  notes=f"{METHOD}: dome intrados HELD by item ({src['task']} MERGED {src['merge_commit'][:8]})")
        add(ln, src, "HELD", codes=("DOME",))
    for s in doc["_stairs"]:
        src = S[s["source_task"]]
        beside = {"lo": s["true_lo_m2"], "hi": s["true_hi_m2"], "cause": s["range_cause"],
                  "held_rows": s.get("held_rows"), "held_plan_m2": s.get("held_plan_m2")}
        q = (f"HELD (blank in the BOQ, never 0): {s['stair']} stair soffit finish: {s['held_reason']}; measured true "
             f"area {_fmt(s['true_lo_m2'])} .. {_fmt(s['true_hi_m2'])} m2 beside ({s['range_cause']}), plus "
             f"{_fmt(s.get('held_plan_m2'))} m2 plan in held rows; never in {CEILING}")
        rec = _rec(src, action="ADD", stair=s["stair"], evidence_status="HELD", beside=beside,
                   held_reason=s["held_reason"])
        ln = _new(ceil_tmpl, item_code=STAIR_SOFFIT, unit="m2", evidence_state="BLOCKED_RFI",
                  element_id=s["element_id"], floor=s["floor"], room_id=None, phys="stair soffit finish", formula=q,
                  rec=rec, rfi={"question": q[:900], "unlocks": s["element_id"]},
                  notes=f"{METHOD}: stair soffit HELD by item ({src['task']} MERGED {src['merge_commit'][:8]})")
        add(ln, src, "HELD", codes=("STAIR_SOFFIT",))
    log["by_action"] = dict(sorted(log["by_action"].items()))
    return changes, log


# ================================================================================================ integrate / write
def check_ceilings(lines):
    """on finished lines: a room's decor in ONE FIN.CEILING figure; parents blank and naming their part; paint of a
    room = its decor + bulkhead lines; bulkhead / paint / stair / dome lines carry their record; stair soffit and dome
    intrados blank and never a FIN.CEILING element; no element twice per item. -> summary."""
    by = {ln["line_id"]: ln for ln in lines}
    out = {"valued": {}, "blank": {}, "rooms": 0}
    seen = set()
    decor, bulk, paint = {}, {}, {}
    for ln in lines:
        rec = ((ln.get("calculation") or {}).get("inputs") or {}).get(REC_KEY)
        code = ln["item_code"]
        if code in NEW_ITEMS and not rec:
            raise ValueError(f"{METHOD}: {ln['line_id']} {code} has no V3.0.32 record")
        if not rec:
            continue
        if code not in ITEMS or ln["unit"] != ITEMS[code]:
            raise ValueError(f"{METHOD}: {ln['line_id']} {code} {ln['unit']} is not a ceiling-family line")
        k = (code, (ln.get("location") or {}).get("element_id"))
        if k in seen:
            raise ValueError(f"{METHOD}: {k} carried twice")
        seen.add(k)
        room = rec.get("room")
        kk = f"{code}|{ln['unit']}"
        if ln["evidence_state"] == "BLOCKED_RFI":
            if ln.get("measured_net") is not None or ln.get("bounded_range"):
                raise ValueError(f"{METHOD}: held line {ln['line_id']} carries a figure (held is BLANK)")
            out["blank"][kk] = out["blank"].get(kk, 0) + 1
            if rec.get("action") == "PARENT" and rec.get("part_line"):
                p = by.get(rec["part_line"])
                if p is None or ln["line_id"] not in (p["calculation"]["inputs"][REC_KEY].get("parents") or ()):
                    raise ValueError(f"{METHOD}: parent {ln['line_id']} and its part {rec['part_line']} do not name "
                                     f"each other")
            continue
        if not (ln.get("measured_net") or 0) > 0:
            raise ValueError(f"{METHOD}: {ln['line_id']} {code} valued at {ln.get('measured_net')!r}")
        if code in (STAIR_SOFFIT, DOME_SOFFIT):
            raise ValueError(f"{METHOD}: {ln['line_id']} {code} valued: stair soffit / dome intrados stay HELD")
        out["valued"][kk] = _r(out["valued"].get(kk, 0.0) + ln["measured_net"])
        tgt = {CEILING: decor, BULKHEAD: bulk, PAINT: paint}[code]
        if room in tgt:
            raise ValueError(f"{METHOD}: room {room} has two valued {code} lines (one figure per room)")
        tgt[room] = ln["measured_net"]
    for room, p in paint.items():
        want = decor.get(room, 0.0) + bulk.get(room, 0.0)
        if room not in decor or abs(p - want) > 1e-5:
            raise ValueError(f"{METHOD}: ceiling paint of {room} {p} is not its decor + bulkhead lines {_r(want)}")
    for room in decor:
        if room not in paint:
            raise ValueError(f"{METHOD}: decor ceiling of {room} has no paint line (Q-57 A mod (6))")
    for room in bulk:
        if room not in decor:
            raise ValueError(f"{METHOD}: bulkhead faces of {room} without a decor ceiling (R-CEIL-R3-2)")
    for ln in lines:   # a stair soffit / dome element never inside a ceiling area line, a wall paint line no ceiling
        e = str((ln.get("location") or {}).get("element_id") or "")
        if ln["item_code"] == CEILING and (e.startswith("STAIR:") or e.startswith("DOME:")):
            raise ValueError(f"{METHOD}: {ln['line_id']} books a stair / dome soffit as a ceiling")
        if ln["item_code"] == "FIN.PAINT" and "ceiling" in e.lower():
            raise ValueError(f"{METHOD}: {ln['line_id']} FIN.PAINT on a ceiling element (ceiling paint is {PAINT})")
    out["rooms"] = len(decor)
    out["valued"] = dict(sorted(out["valued"].items()))
    out["blank"] = dict(sorted(out["blank"].items()))
    return out


def integrate(l3031, changes, for_lead=()):
    """-> (V3.0.32 lines, identity). Every line outside the rows is byte-identical to V3.0.31."""
    sid = {ln["line_id"] for ln in l3031}
    rep, adds = {}, []
    for c in changes:
        if c["piece"] != PIECE:
            raise ValueError(f"{METHOD}: piece {c['piece']} (this version only fills the ceiling family)")
        if c["action"] == "REPLACE":
            lid = c["before"]["line_id"]
            if lid in rep or lid not in sid or c["after"]["line_id"] != lid or c["after"]["item_code"] != CEILING:
                raise ValueError(f"{METHOD}: line {lid}: changed twice, not in V3.0.31, its id changed or not a "
                                 f"ceiling line")
            rep[lid] = c["after"]
        elif c["action"] == "ADD":
            a = c["after"]
            if a["line_id"] in sid or a["item_code"] not in ITEMS or a["unit"] != ITEMS[a["item_code"]]:
                raise ValueError(f"{METHOD}: an added line repeats a V3.0.31 id or is not a ceiling-family line")
            adds.append(a)
        else:
            raise ValueError(f"{METHOD}: action {c['action']}")
    out = [rep.get(ln["line_id"], ln) for ln in l3031] + adds
    if len({ln["line_id"] for ln in out}) != len(out):
        raise ValueError(f"{METHOD}: a BOQ line id appears twice")
    guards = A3031._family_guards(out, for_lead)   # every family guard up to V3.0.30
    roof = A3031.check_roof_layers(out)
    ceil = check_ceilings(out)
    pids = {(ln["project"]["project_id"], ln["project"]["revision_set_sha256"]) for ln in out}
    if len(pids) != 1:
        raise ValueError(f"{METHOD}: {len(pids)} project identities in the lines (one project, one revision set)")
    by31 = {ln["line_id"]: ln for ln in l3031}
    touched = set(rep) | {a["line_id"] for a in adds}
    outside = [ln for ln in out if ln["line_id"] not in touched]
    bad = [ln["line_id"] for ln in outside if A30.line_sha(by31[ln["line_id"]]) != A30.line_sha(ln)]
    if bad or len(outside) + len(rep) != len(l3031):
        raise ValueError(f"{METHOD}: {len(bad)} line(s) outside the V3.0.32 rows differ from {EXTENDS}")
    for lid, ln in rep.items():   # inside a row only quantity, state, basis, rfi, calculation and notes change
        a, b = copy.deepcopy(by31[lid]), copy.deepcopy(ln)
        for x in (a, b):
            for k in ROW_KEYS:
                x.pop(k, None)
        if json.dumps(a, sort_keys=True) != json.dumps(b, sort_keys=True):
            raise ValueError(f"{METHOD}: line {lid} changed outside quantity / state / basis")
    ident = {"v3_0_31_lines": len(l3031), "v3_0_32_lines": len(out), "v3_0_32_rows": len(changes),
             "replaced": len(rep), "added": len(adds), "outside_rows": len(outside),
             "outside_rows_identical_to_v3_0_31": len(outside), "ceilings": ceil, "roof_buildup": roof,
             "guards": guards,
             "outside_rows_sha256": hashlib.sha256("".join(A30.line_sha(x) for x in outside).encode()).hexdigest()}
    return out, ident


def ledger_rows(changes, released_lines=None):
    rel = {A30._key(ln): ln for ln in released_lines or ()}
    rows = []
    for c in changes:
        ref = c["after"]
        rec = ref["calculation"]["inputs"][REC_KEY]
        b29 = None
        if released_lines is not None:
            b29 = A30._qty(rel[A30._key(ref)]) if A30._key(ref) in rel else dict(A30._qty(None),
                                                                                 state="NOT_IN_RELEASED")
        loc = ref.get("location") or {}
        rows.append({"version": METHOD, "piece": PIECE, "action": c["action"], "line_id": ref["line_id"],
                     "item_code": ref["item_code"], "floor": loc.get("floor"), "room_id": loc.get("room_id"),
                     "element_id": loc.get("element_id"), "unit": ref["unit"], "record_action": rec.get("action"),
                     "before_released_v2_9": b29,
                     "before_v3_0_31": (A30._qty(c["before"]) if c["before"] else
                                        dict(A30._qty(None), state="NOT_IN_V3_0_31")),
                     "after_v3_0_32": A30._qty(ref), "evidence_status": c.get("evidence_status"),
                     "still_held": c.get("held"), "release_status": "NOT RELEASED",
                     "owner_manual_method": PIECES[PIECE]["owner_manual_method"],
                     "drawing_derived_method": PIECES[PIECE]["drawing_method"],
                     "verification": c.get("verification") or {}, "rollback": ROLLBACK})
    return rows


LEDGER_CSV = ("version", "action", "line_id", "item_code", "floor", "room_id", "element_id", "unit", "record_action",
              "v2_9", "v3_0_31", "v3_0_32", "evidence_status", "held", "verification")
DIFF_CSV = ("line_id", "item_code", "floor", "element_id", "unit", "vs_v3_0_31", "vs_released_v2_9", "v2_9",
            "v3_0_31", "v3_0_32")


def ledger_csv(rows):
    return A305._csv([{"version": r["version"], "action": r["action"], "line_id": r["line_id"],
                       "item_code": r["item_code"], "floor": r["floor"] or "", "room_id": r["room_id"] or "",
                       "element_id": r["element_id"], "unit": r["unit"], "record_action": r["record_action"],
                       "v2_9": A302._q(r["before_released_v2_9"]) if r["before_released_v2_9"] else "",
                       "v3_0_31": A302._q(r["before_v3_0_31"]), "v3_0_32": A302._q(r["after_v3_0_32"]),
                       "evidence_status": r["evidence_status"],
                       "held": "; ".join(f"{h['what']}: {h['why']}" for h in r["still_held"] or ())[:900],
                       "verification": f"{r['verification'].get('task')} {r['verification'].get('merge_commit', '')[:8]}"
                       } for r in rows], LEDGER_CSV)


def diff_rows(l3031, l3032, released_lines=None):
    b31 = {ln["line_id"]: ln for ln in l3031}
    rel = {A30._key(ln): ln for ln in released_lines or ()}
    out = []
    for ln in l3032:
        o = b31.get(ln["line_id"])
        vs = "ADDED" if o is None else ("SAME" if A30.line_sha(o) == A30.line_sha(ln) else
                                        ("CHANGED" if A30._qty(o) != A30._qty(ln) else "CHANGED_TEXT_ONLY"))
        r = rel.get(A30._key(ln)) if released_lines is not None else None
        vs29 = None if released_lines is None else ("NOT_IN_RELEASED" if r is None else
                                                    ("SAME_QUANTITY" if A30._qty(r) == A30._qty(ln) else
                                                     "QUANTITY_DIFFERS"))
        out.append({"line_id": ln["line_id"], "item_code": ln["item_code"], "floor": ln["location"].get("floor"),
                    "element_id": ln["location"].get("element_id"), "unit": ln["unit"], "vs_v3_0_31": vs,
                    "vs_released_v2_9": vs29, "v2_9": A302._q(A30._qty(r)) if r else "",
                    "v3_0_31": A302._q(A30._qty(o)) if o else "", "v3_0_32": A302._q(A30._qty(ln))})
    return out


def write(out, l3031, changes, log, doc, released_lines=None, for_lead=()):
    """the V3_0_32_* files beside the V3_0_31_* files. -> (file names, identity, ledger)."""
    from pathlib import Path
    from engine.source import boq_line as BL
    out = Path(out)
    l3032, ident = integrate(l3031, changes, for_lead)
    rows = ledger_rows(changes, released_lines)
    diff = diff_rows(l3031, l3032, released_lines)
    dsum = {}
    for d in diff:
        dsum.setdefault("vs_v3_0_31", {}).setdefault(d["vs_v3_0_31"], 0)
        dsum["vs_v3_0_31"][d["vs_v3_0_31"]] += 1
        if d["vs_released_v2_9"] is not None:
            dsum.setdefault("vs_released_v2_9", {}).setdefault(d["vs_released_v2_9"], 0)
            dsum["vs_released_v2_9"][d["vs_released_v2_9"]] += 1
    ident = dict(ident, diff=dsum)
    t31, t32 = A304.code_totals(l3031), A304.code_totals(l3032)
    moved = {k: {"v3_0_31": t31.get(k), "v3_0_32": t32.get(k)} for k in sorted(set(t31) | set(t32))
             if t31.get(k) != t32.get(k)}
    if any(k.split("|")[0] not in ITEMS for k in moved):
        raise ValueError(f"{METHOD}: totals moved outside the ceiling family: {sorted(moved)[:5]}")
    led = {"schema": LEDGER_SCHEMA, "method": METHOD, "extends": EXTENDS, "candidate": CANDIDATE,
           "base": A30.BASE_METHOD, "released": A30.RELEASED_METHOD, "released_default": False, "rows": rows,
           "waiting_pieces": WAITING, "integration_package": True}
    run = {"method": METHOD, "policy": POLICY_ID, "extends": EXTENDS, "candidate": CANDIDATE,
           "base_method": A30.BASE_METHOD, "released_method": A30.RELEASED_METHOD, "released_default": False,
           "rollback": ROLLBACK, "identity": ident, "pieces": PIECES, "piece_logs": [log],
           "totals_moved_by_code": moved, "waiting_pieces": WAITING}
    files = {"V3_0_32_BOQ_LINES.json": BL.dumps(l3032),
             "V3_0_32_BOQ_LINES.csv": A30._lines_csv(l3032),
             "V3_0_32_INTEGRATION_LEDGER.json": A30._j(led),
             "V3_0_32_INTEGRATION_LEDGER.csv": ledger_csv(rows),
             "V3_0_32_DIFF.csv": A305._csv(diff, DIFF_CSV),
             "V3_0_32_RUN.json": A30._j(run)}
    for name, text in files.items():
        (out / name).write_text(text, encoding="utf-8")
    return sorted(files), ident, led


def policy_record():
    return {"method": METHOD, "extends": EXTENDS, "pieces": sorted(PIECES), "inputs_schema": INPUTS_SCHEMA,
            "released_default": False, "rollback": ROLLBACK, "items": sorted(ITEMS)}


__all__ = ["METHOD", "PIECES", "WAITING", "DEFAULT_GUARD_CLASS", "INPUTS_SCHEMA", "load_inputs", "changes_for",
           "check_ceilings", "integrate", "ledger_rows", "diff_rows", "write", "InputsError"]
