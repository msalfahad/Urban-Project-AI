"""ARCH_TAKEOFF_V3.0.28 (T-326): the SAME opt-in BOQ candidate as ARCH_TAKEOFF_V3.0 .. V3.0.27 (engine.source.arch_v30,
arch_v301 .. arch_v3027), extended with ONE piece, OPENING_REVEAL_FILL: the candidate's opening reveal lines filled and
the missing reveal scope added, opening by opening and face by face, from the Checker-merged reveal ledger (T-313 r2)
cross-checked against the Checker-merged sills / thresholds ledger (T-325). Not a new method family and not the
released default (owner management decision 2026-10-20 sections 2 and 5); rollback is running ARCH_TAKEOFF_V2.9.

The physical element (ERS 2026-10-22 s.2.1): ONE FACE of the wall thickness at an opening: a jamb (two per opening),
the head soffit, the sill (raised window, outside) or the floor-level threshold, on the room side (IN), the outside
(OUT) or, for a door / arch / gate, once through the wall (THROUGH). Each face is booked in exactly ONE line:

  FILL      an ARCH.WINDOW_REVEAL line (BLOCKED_RFI since V2, 'strip faces in the wall thickness') bound to ONE window's
            measured outside sill / floor-level threshold: filled with that external surface only, MEASURED m2 (the
            w x wall plan strip includes the frame bed, which is not a finish surface; the room side is NONE where the
            frame is drawn flush with the room face). Material stays as the ledger states it (UNKNOWN / by spec);
  NARROW    a FIN.PLASTER 'door jambs and head' line held as a bound only because the door height class was pending,
            where the drawing prints the height: the one figure at the printed height (inside the old bound);
  ADD       a face no line carries: valued faces of one opening, side and face group in ONE line (window jambs +
            head and an external sill with no line: ARCH.WINDOW_REVEAL, the code of BOQ family B4-08 'Reveals and
            returns', the sill and the jambs / head in separate lines, the physical element naming which; a reveal
            through the wall of a door / arch / gate (UP-FIN-PLASTER-001 2 x t x h + t x w): FIN.PLASTER '<kind> jambs
            and head', as the candidate's other door lines); HELD / UNRESOLVED faces of one opening, side and group in
            ONE BLANK line naming each face (never 0). No new item code: every face sits in a family the registry
            already names.

Refused (InputsError / ValueError, nothing written): a FILL on a line that is not a blank ARCH.WINDOW_REVEAL line, or a
second window on one line, or a fill with no measured external surface; a NARROW whose figure is outside the line's
bound or whose line is not the stated bound; an ADD of a face that a candidate line already carries (the 22 door reveals
in FIN.PLASTER, a door's floor face in its threshold / closure line: T-325) or that another record books (each opening /
side / face once); a valued face without m2 > 0 or with a sum that is not its components; a held face given a figure;
an unknown component, side, item or state; a unit other than m2; a source that is not a merged, checker-verified ledger.
Every line outside the records is byte-identical to V3.0.27 (asserted); inside a FILL / NARROW only state, quantity,
range, rfi, calculation and notes change.

Files: V3_0_28_BOQ_LINES.json / .csv, V3_0_28_INTEGRATION_LEDGER.json / .csv (per line: before V3.0.27, after,
released V2.9, evidence status, opening / side / faces, source task / merge / checker run), V3_0_28_DIFF.csv, V3_0_28_RUN
.json. Nothing here names a project, a sheet, a layer or a coordinate: every value comes from the inputs.
"""

from __future__ import annotations

import copy
import hashlib
import json

from engine.source import arch_v30 as A30
from engine.source import arch_v302 as A302
from engine.source import arch_v304 as A304
from engine.source import arch_v305 as A305
from engine.source import arch_v3010 as A3010
from engine.source import arch_v3011 as A3011
from engine.source import arch_v3012 as A3012
from engine.source import arch_v3014 as A3014
from engine.source import arch_v3015 as A3015
from engine.source import arch_v3018 as A3018
from engine.source import arch_v3021 as A3021
from engine.source import arch_v3023 as A3023
from engine.source import arch_v3024 as A3024
from engine.source import arch_v3025 as A3025
from engine.source import arch_v3026 as A3026
from engine.source import arch_v3027 as A3027

DEFAULT_GUARD_CLASS = "TOOLING"          # T-212: re-books checker-merged ledgers; adds no default value
METHOD = "ARCH_TAKEOFF_V3.0.28"
EXTENDS = A3027.METHOD
CANDIDATE = A30.METHOD
POLICY_ID = "URBAN_BOQ_T326_ARCH_V3_0_28"
INPUTS_SCHEMA = "URBAN_V3028_INPUTS_V1"
LEDGER_SCHEMA = "URBAN_V3028_INTEGRATION_LEDGER_V1"
ROLLBACK = A30.ROLLBACK
InputsError = A3015.InputsError
_r = A3018._r
RULE_ID, RULE_VERSION = "R-T326-1", "T-326"
UNIT = "m2"
PIECE = "OPENING_REVEAL_FILL"
REC_KEY = "opening_reveal_v3028"
SIDES = ("IN", "OUT", "THROUGH")
FACE = {"JAMBS": "jambs", "HEAD": "head soffit", "SILL": "external sill", "THRESHOLD": "floor-level threshold",
        "FLOOR_STRIP": "floor strip"}
SILL_FACES = ("SILL", "THRESHOLD", "FLOOR_STRIP")
SILL_CODE, PLASTER_CODE = "ARCH.WINDOW_REVEAL", "FIN.PLASTER"
DOOR_PHYSICAL = "door jambs and head"
JAMB_FACES = ("JAMBS", "HEAD")
GROUPS = {"SILL": SILL_FACES, "JAMBS_HEAD": JAMB_FACES}
ITEMS = {SILL_CODE: ("SILL", "JAMBS_HEAD"), PLASTER_CODE: ("JAMBS_HEAD",)}       # item -> the face groups it books
JAMB_ITEM = ("Window reveal jambs and head (finish to be confirmed)", "جوانب وسقف فتحة الشباك (التشطيب يحدد لاحقاً)")
THROUGH_KINDS = ("DOOR", "ARCH", "GATE")
VALUED_STATES = ("MEASURED",)
HELD_STATES = ("HELD", "UNRESOLVED")
TOL = 1e-6

PIECES = {
    PIECE: {
        "module": "engine/source/arch_v3028.py (opening reveal faces: the ARCH.WINDOW_REVEAL lines filled with the "
                  "external sill / threshold surface, D-GF-07-type bounds narrowed at a printed height, missing faces "
                  "added once per opening / side / item, held faces BLANK by name)",
        "policy": "OPENING_REVEAL_FILL_V1", "rule_id": RULE_ID, "rule_version": RULE_VERSION,
        "owner_rules": ["UP-REVEAL-001 (window reveals: jambs + head where wall remains; the sill surface its own "
                        "item)", "UP-FIN-PLASTER-001 (door reveal through the wall: 2 x t x h + t x w, PROVISIONAL "
                        "until the frame detail)", "Q-32 A", "Q-55 C (door height 2.20 where none is printed: "
                        "ASSUMED - OWNER-APPROVED)", "UP-REF-REVEAL-001 (reference only)",
                        "UP-QTY-STATUS-001 (held never 0)", "WORKFLOW_CONTROLS 2026-10-21 s.4 / s.5; ERS 2026-10-22 "
                        "s.2 - s.4"],
        "owner_manual_method": "owner method (UP-REVEAL-001 / UP-FIN-PLASTER-001): window reveal = 2 x depth x height "
                               "+ depth x width where a reveal exists, the sill its own item; door reveal = 2 x t x h + "
                               "t x w through the wall; finish candidate URBAN-REVEAL-FINISH-METHOD v1 (default plaster, "
                               "not drawing-confirmed)",
        "drawing_method": "per opening and side from the drawn wall faces and frame band (T-313: frame flush with the "
                          "room face -> room side NONE; outside depth 0.080 / 0.100 m), window sizes T-237, wall "
                          "thickness T-150, door heights printed or Q-55 C; external sills re-read by T-325 (equal)"},
}
WAITING = dict(A3027.WAITING)
WAITING.update({
    "REVEAL_FINISH": "the finish of the reveal faces (plaster / paint / cladding): URBAN-REVEAL-FINISH-METHOD v1 "
                     "candidate, WIN-REVEAL owner decision queued; the faces carry area only",
    "REVEAL_HELD_FACES": "curved openings (W03, W17), W02 outside jambs (height HELD), gate D-GF-15, arches A-GF-01 "
                         "(D-45) / A-1F-01 (not drawn): BLANK by name",
    "THRESHOLD_RETYPE": "the five T-325 closure strips (door floor faces) are retyped by the sills / thresholds "
                        "package (T-327), never here",
})


# ================================================================================================ inputs
def _src(s):
    for k in ("task", "file", "sha256", "merge_commit", "checker_run"):
        if not s.get(k):
            raise InputsError(f"source {s}: {k} missing (a merged, checker-verified ledger only)")


def _pos(x, where):
    if not isinstance(x, (int, float)) or x <= TOL:
        raise InputsError(f"{where}: {x!r} m2 (a valued face is > 0 m2; held is BLANK, never 0)")
    return float(x)


def load_inputs(doc, project_id=None):
    """URBAN_V3028_INPUTS_V1 -> the validated doc."""
    if not doc:
        return None
    if doc.get("schema") != INPUTS_SCHEMA:
        raise InputsError(f"project inputs: schema must be {INPUTS_SCHEMA}")
    if project_id and doc.get("project_id") not in (None, project_id):
        raise InputsError(f"project inputs are for {doc.get('project_id')!r}, the run is {project_id!r}")
    if doc.get("unit") != UNIT:
        raise InputsError(f"inputs unit {doc.get('unit')!r}: reveal faces are booked in m2")
    srcs = {}
    for s in doc.get("sources") or ():
        _src(s)
        srcs.setdefault(s["task"], s)
    faces = {}                      # (opening, side, face) -> who books it

    def book(op, side, face, who):
        if side not in SIDES:
            raise InputsError(f"{op}: side {side!r}")
        if face not in FACE:
            raise InputsError(f"{op}: component {face!r}")
        k = (op, side, face)
        if k in faces:
            raise InputsError(f"{op} {side} {face}: already carried by {faces[k]} (each face once; a second "
                              f"carrier is a double count)")
        faces[k] = who

    for c in doc.get("carried") or ():
        if c.get("source_task") not in srcs:
            raise InputsError(f"carried {c.get('opening')}: no merged source for {c.get('source_task')!r}")
        book(c["opening"], c["side"], c["component"], f"{c['item_code']} {c['line_id']}")
    fills, seen_lines = [], set()
    for f in doc.get("fills") or ():
        where = f"fill {f.get('opening')} {f.get('line_id')}"
        if f.get("source_task") not in srcs:
            raise InputsError(f"{where}: no merged source")
        if f.get("side") != "OUT" or f.get("component") not in ("SILL", "THRESHOLD"):
            raise InputsError(f"{where}: a reveal-strip line is filled with the external sill / threshold only")
        if f["line_id"] in seen_lines:
            raise InputsError(f"{where}: a second window on one line")
        seen_lines.add(f["line_id"])
        book(f["opening"], "OUT", f["component"], f"{SILL_CODE} {f['line_id']}")
        fills.append(dict(f, m2=_pos(f.get("m2"), where)))
    narrow = []
    for n in doc.get("narrow") or ():
        where = f"narrow {n.get('opening')} {n.get('line_id')}"
        if n.get("source_task") not in srcs:
            raise InputsError(f"{where}: no merged source")
        if n["line_id"] in seen_lines:
            raise InputsError(f"{where}: line booked twice")
        seen_lines.add(n["line_id"])
        m2 = _pos(n.get("m2"), where)
        b = n.get("before") or {}
        if not (isinstance(b.get("low"), (int, float)) and isinstance(b.get("high"), (int, float))):
            raise InputsError(f"{where}: the line's bound before is required")
        if not b["low"] - TOL <= m2 <= b["high"] + TOL:
            raise InputsError(f"{where}: {m2} m2 is outside the line's bound {b['low']} .. {b['high']} (a narrowing "
                              f"never moves a figure out of its bound)")
        comps = n.get("components") or ()
        if abs(sum(c["m2"] for c in comps) - m2) > TOL:
            raise InputsError(f"{where}: faces {[c['m2'] for c in comps]} do not sum to {m2}")
        narrow.append(dict(n, m2=m2))
    adds, seen_add = [], set()
    for a in doc.get("adds") or ():
        where = f"add {a.get('opening')} {a.get('side')} {a.get('item_code')} {a.get('status')}"
        if a.get("source_task") not in srcs:
            raise InputsError(f"{where}: no merged source")
        if a.get("item_code") not in ITEMS:
            raise InputsError(f"{where}: item {a.get('item_code')!r}")
        if a.get("group") not in ITEMS[a["item_code"]]:
            raise InputsError(f"{where}: face group {a.get('group')!r} is not booked under {a['item_code']}")
        if a.get("status") not in ("VALUED", "HELD"):
            raise InputsError(f"{where}: status {a.get('status')!r}")
        key = (a["opening"], a["side"], a["group"], a["status"])
        if key in seen_add:
            raise InputsError(f"{where}: twice")
        seen_add.add(key)
        if (a["item_code"] == PLASTER_CODE) != (a["side"] == "THROUGH"):
            raise InputsError(f"{where}: a reveal through the wall (door / arch / gate) is FIN.PLASTER, a window "
                              f"side is {SILL_CODE}")
        if a["side"] == "THROUGH" and a.get("kind") not in THROUGH_KINDS:
            raise InputsError(f"{where}: kind {a.get('kind')!r} has no reveal through the wall")
        comps = a.get("components") or ()
        if not comps:
            raise InputsError(f"{where}: no face")
        for c in comps:
            if c.get("component") not in GROUPS[a["group"]]:
                raise InputsError(f"{where}: face {c.get('component')!r} is not a {a['group']} face")
            if a["status"] == "VALUED":
                if c.get("state") not in VALUED_STATES:
                    raise InputsError(f"{where}: {c['component']} state {c.get('state')!r} in a valued line")
                _pos(c.get("m2"), f"{where} {c['component']}")
            else:
                if c.get("state") not in HELD_STATES:
                    raise InputsError(f"{where}: {c['component']} state {c.get('state')!r} in a held line")
                if c.get("m2") not in (None, "") or c.get("ml") not in (None, ""):
                    raise InputsError(f"{where}: held face {c['component']} given a figure (held is BLANK, never 0)")
            book(a["opening"], a["side"], c["component"], f"added {a['item_code']} ({a['status']})")
        adds.append(a)
    return dict(doc, fills=fills, narrow=narrow, adds=adds, _sources=srcs, _faces=faces)


# ================================================================================================ lines
def _rec(src, **kw):
    return dict({"policy": PIECES[PIECE]["policy"], "task": src["task"], "ledger": src["file"],
                 "ledger_sha256": src["sha256"], "merge_commit": src["merge_commit"], "checker_run": src["checker_run"],
                 "rule_id": RULE_ID, "rule_version": RULE_VERSION, "release_status": "NOT RELEASED"}, **kw)


def _ver(src):
    return {"task": src["task"], "merge_commit": src["merge_commit"], "verifier_run": src["checker_run"],
            "ledger": src["file"], "ledger_sha256": src["sha256"]}


def _fmt(x):
    return f"{_r(x, 4):.4f}".rstrip("0").rstrip(".") if x is not None else ""


def element_id(a):
    return f"{a['floor']}-REVEAL-{a['opening']}:{a['side']}:{a['group']}:{a['status']}"


def _template(lines, floor):
    """the plan documents of this floor's reveal-strip lines (the new faces are read on the same plan)."""
    cand = [ln for ln in lines if ln["item_code"] == SILL_CODE]
    same = [ln for ln in cand if (ln.get("location") or {}).get("floor") == floor]
    pick = (same or cand)
    if not pick:
        raise InputsError(f"no {SILL_CODE} line in the candidate to take the plan documents from")
    return sorted(pick, key=lambda x: x["line_id"])[0]


def fill_line(b, f, src):
    from engine.source import boq_line as BL
    ln = copy.deepcopy(b)
    ln["evidence_state"] = "MEASURED"
    ln["measured_net"] = _r(f["m2"])
    ln["bounded_range"] = None
    ln["rfi"] = None
    ln["calculation"]["formula"] = (f"{f['opening']} outside {FACE[f['component']]} only ({f['basis']}; the room side "
                                    f"is NONE: frame flush with the room face; the frame bed under the frame is not a "
                                    f"finish surface) = {_fmt(f['m2'])} m2")[:600]
    ln["calculation"]["inputs"] = dict(ln["calculation"].get("inputs") or {}, **{REC_KEY: _rec(
        src, action="FILL", before=A3018._before_rec(b), opening=f["opening"], side="OUT",
        faces=[{"component": f["component"], "m2": _r(f["m2"]), "ml": _r(f.get("ml")), "depth_m": f.get("depth_m"),
                "basis": f["basis"], "evidence": f["evidence"]}], material=f.get("material"),
        evidence_status=f["evidence"], cross_check=f.get("cross_check"))})
    A305._note(ln, f"{METHOD}: filled with {f['opening']}'s outside {FACE[f['component']]} ({src['task']} MERGED "
                   f"{src['merge_commit'][:8]}, {f.get('cross_check') or ''}); material {f.get('material')}")
    return BL.validate(ln)


def narrow_line(b, n, src):
    from engine.source import boq_line as BL
    ln = copy.deepcopy(b)
    ln["evidence_state"] = "PROVISIONAL"
    ln["measured_net"] = _r(n["m2"])
    ln["bounded_range"] = None
    ln["rfi"] = None
    ln["calculation"]["formula"] = (f"{n['opening']} door jambs and head at the printed height: {n['basis']} = "
                                    f"{_fmt(n['m2'])} m2 (was the class bound {n['before']['low']} .. "
                                    f"{n['before']['high']} m2)")[:600]
    ln["calculation"]["inputs"] = dict(ln["calculation"].get("inputs") or {}, **{REC_KEY: _rec(
        src, action="NARROW", before=A3018._before_rec(b), opening=n["opening"], side="THROUGH",
        faces=n["components"], evidence_status="DRAWING-CONFIRMED (height printed); plastered extent PROVISIONAL "
                                                "(UP-FIN-PLASTER-001: the frame detail)")})
    A305._note(ln, f"{METHOD}: height printed on the drawing ({src['task']} MERGED {src['merge_commit'][:8]}); "
                   f"PROVISIONAL as the other door reveal lines (frame detail)")
    return BL.validate(ln)


def _held_basis(text):
    """a held face's basis as words: a candidate figure in it is never stated as the line's result."""
    return str(text or "").replace(" = ", " would give ").replace("=", " would give ")


def _add_evidence(a):
    evs = sorted({c["evidence"] for c in a["components"]})
    return " + ".join(evs)


def add_line(a, src, tmpl):
    from engine.source import boq_line as BL
    pr = tmpl["project"]
    eid = element_id(a)
    valued = a["status"] == "VALUED"
    total = _r(sum(c["m2"] for c in a["components"])) if valued else None
    faces = [{k: c.get(k) for k in ("component", "m2", "ml", "depth_m", "basis", "state", "evidence",
                                    "height_status")} for c in a["components"]]
    lrec = _rec(src, action="ADD", opening=a["opening"], kind=a.get("kind"), side=a["side"], group=a["group"],
                status=a["status"],
                faces=faces, rooms=a.get("rooms"), evidence_status=_add_evidence(a) if valued else "HELD")
    names = " + ".join(f"{FACE[c['component']]} {c['basis']}" for c in a["components"])
    if valued:
        ev = "PROVISIONAL" if a["item_code"] == PLASTER_CODE or any(
            str(c["evidence"]).startswith("ASSUMED") for c in a["components"]) else "MEASURED"
        formula = f"{a['opening']} {a['side'].lower()} {names} = {_fmt(total)} m2"
        rfi = None
        note = (f"{METHOD}: missing reveal scope added ({src['task']} MERGED {src['merge_commit'][:8]}): "
                f"{_add_evidence(a)}")
    else:
        ev = "BLOCKED_RFI"
        formula = (f"HELD faces (blank in the BOQ, never 0): {a['opening']} {a['side'].lower()} "
                   + "; ".join(f"{FACE[c['component']]} {c['state']}: {_held_basis(c['basis'])}"
                               for c in a["components"]))
        rfi = {"question": formula[:900], "unlocks": eid}
        note = f"{METHOD}: reveal faces HELD by name ({src['task']} MERGED {src['merge_commit'][:8]})"
    if a["item_code"] == PLASTER_CODE:
        item_kw = {"physical_element": f"{str(a.get('kind')).lower()} jambs and head"}
    elif a["group"] == "JAMBS_HEAD":
        item_kw = {"physical_element": f"window reveal jambs and head ({'outside' if a['side'] == 'OUT' else 'room side'})",
                   "item_en": JAMB_ITEM[0], "item_ar": JAMB_ITEM[1]}
    else:
        item_kw = {"physical_element": "window reveal strip"}
    ln = BL.make_line(project_id=pr["project_id"], revision_set_sha256=pr["revision_set_sha256"],
                      item_code=a["item_code"], unit=UNIT, evidence_state=ev, measured_net=total, element_id=eid,
                      floor=a["floor"], room_id=(a.get("rooms") or "").split(";")[0] or None,
                      formula=formula[:700], inputs={REC_KEY: lrec},
                      documents=copy.deepcopy(tmpl["source"]["documents"]),
                      geometry_source=tmpl["source"]["geometry_source"],
                      geometry_confidence=tmpl["source"].get("geometry_confidence") or "INFERRED_CANDIDATE",
                      rule_id=RULE_ID, rule_version=RULE_VERSION, material_state="BY_SPEC", rfi=rfi,
                      notes=note[:600], **item_kw)
    ln["project"] = copy.deepcopy(pr)
    return BL.validate(ln), lrec


def _assert_fill(b, f):
    if b is None:
        raise InputsError(f"line {f['line_id']}: the candidate does not carry this line (stale ledger)")
    inp = (b.get("calculation") or {}).get("inputs") or {}
    if inp.get(REC_KEY):
        raise InputsError(f"line {f['line_id']}: already filled (applied once)")
    if (b["item_code"], b["unit"]) != (SILL_CODE, UNIT) or b["evidence_state"] != "BLOCKED_RFI" or \
            b.get("measured_net") is not None or b.get("bounded_range"):
        raise InputsError(f"line {f['line_id']}: {b['item_code']} {b['evidence_state']} is not a blank reveal strip")


def _assert_narrow(b, n):
    if b is None:
        raise InputsError(f"line {n['line_id']}: the candidate does not carry this line (stale ledger)")
    if ((b.get("calculation") or {}).get("inputs") or {}).get(REC_KEY):
        raise InputsError(f"line {n['line_id']}: already narrowed (applied once)")
    br = b.get("bounded_range") or {}
    if (b["item_code"], b["unit"], b.get("physical_element")) != (PLASTER_CODE, UNIT, DOOR_PHYSICAL) or \
            b["evidence_state"] != "BOUNDED_EXPOSURE" or abs((br.get("low") or 0) - n["before"]["low"]) > TOL or \
            abs((br.get("high") or 0) - n["before"]["high"]) > TOL:
        raise InputsError(f"line {n['line_id']}: {b['item_code']} {b['evidence_state']} {br.get('low')} .. "
                          f"{br.get('high')} is not the door bound {n['before']} (stale ledger)")


def changes_for(doc, l3027):
    """-> (changes, log)."""
    if not doc:
        return [], {"piece": PIECE, "state": "NO_PROJECT_INPUT"}
    by = {ln["line_id"]: ln for ln in l3027}
    for c in doc.get("carried") or ():
        if c["line_id"] not in by:
            raise InputsError(f"carried {c['opening']}: line {c['line_id']} is not in the candidate (stale ledger)")
    seen = set(by)
    changes = []
    log = {"piece": PIECE, "state": "RUN", "sources": doc["sources"], "by_action": {}, "m2": {}, "lines": {}}

    def tally(k, m2):
        log["by_action"][k] = log["by_action"].get(k, 0) + 1
        if m2 is not None:
            log["m2"][k] = _r(log["m2"].get(k, 0.0) + m2)

    for f in doc["fills"]:
        b = by.get(f["line_id"])
        _assert_fill(b, f)
        src = doc["_sources"][f["source_task"]]
        after = fill_line(b, f, src)
        changes.append(A305._change(PIECE, "REPLACE", b, after, drawing_reference=src["file"], held=[], downstream=[],
                                    verification=_ver(src), evidence_status=f["evidence"],
                                    codes=[PIECE, "FILL"], group=SILL_CODE))
        tally("FILL", f["m2"])
        log["lines"][b["line_id"]] = {"action": "FILL", "opening": f["opening"]}
    for n in doc["narrow"]:
        b = by.get(n["line_id"])
        _assert_narrow(b, n)
        src = doc["_sources"][n["source_task"]]
        after = narrow_line(b, n, src)
        changes.append(A305._change(PIECE, "REPLACE", b, after, drawing_reference=src["file"], held=[], downstream=[],
                                    verification=_ver(src), evidence_status="DRAWING-CONFIRMED (height printed)",
                                    codes=[PIECE, "NARROW"], group=PLASTER_CODE))
        tally("NARROW", n["m2"] - n["before"]["low"])
        log["lines"][b["line_id"]] = {"action": "NARROW", "opening": n["opening"]}
    for a in doc["adds"]:
        src = doc["_sources"][a["source_task"]]
        ln, _lrec = add_line(a, src, _template(l3027, a["floor"]))
        if ln["line_id"] in seen:
            raise ValueError(f"{METHOD}: the added line of {a['opening']} repeats a line id")
        seen.add(ln["line_id"])
        held = [] if a["status"] == "VALUED" else [
            {"what": f"{a['item_code']} {a['opening']} {a['side']} {c['component']}", "why": f"{c['state']}: "
             f"{c['basis']}"[:300], "range": None, "scenario": None} for c in a["components"]]
        changes.append(A305._change(PIECE, "ADD", None, ln, drawing_reference=src["file"], held=held, downstream=[],
                                    verification=_ver(src), evidence_status=ln["calculation"]["inputs"][REC_KEY]
                                    ["evidence_status"], codes=[PIECE, f"ADD_{a['status']}"], group=a["item_code"]))
        tally(f"ADD_{a['status']} {a['item_code']}", ln.get("measured_net"))
        log["lines"][ln["line_id"]] = {"action": f"ADD_{a['status']}", "opening": a["opening"], "side": a["side"]}
    return changes, log


# ================================================================================================ integrate / write
def check_reveals(lines):
    """on finished lines: each (opening, side, face) is booked by ONE reveal record; valued lines carry their faces'
    sum, held lines no figure. -> summary."""
    out = {"filled": 0, "narrowed": 0, "added_valued": 0, "added_held": 0, "m2": {}}
    faces = {}
    for ln in lines:
        rec = ((ln.get("calculation") or {}).get("inputs") or {}).get(REC_KEY)
        if not rec:
            continue
        act = rec.get("action")
        for c in rec.get("faces") or ():
            k = (rec["opening"], rec["side"], c["component"])
            if k in faces:
                raise ValueError(f"{METHOD}: {k} booked by {faces[k]} and {ln['line_id']} (double count)")
            faces[k] = ln["line_id"]
        if act == "ADD" and rec["status"] == "HELD":
            out["added_held"] += 1
            if ln["evidence_state"] != "BLOCKED_RFI" or ln.get("measured_net") is not None or ln.get("bounded_range"):
                raise ValueError(f"{METHOD}: held reveal line {ln['line_id']} carries a figure (held is BLANK)")
            continue
        net = ln.get("measured_net")
        if not isinstance(net, (int, float)) or net <= TOL or ln.get("bounded_range"):
            raise ValueError(f"{METHOD}: valued reveal line {ln['line_id']} is {ln['evidence_state']} {net}")
        s = sum(float(c["m2"]) for c in rec.get("faces") or ())
        if abs(s - net) > TOL:
            raise ValueError(f"{METHOD}: reveal line {ln['line_id']}: {net} m2 is not its faces' {s}")
        k = {"FILL": "filled", "NARROW": "narrowed", "ADD": "added_valued"}[act]
        out[k] += 1
        m = out["m2"].setdefault(ln["item_code"], 0.0)
        out["m2"][ln["item_code"]] = _r(m + net)
    out["m2"] = dict(sorted(out["m2"].items()))
    out["faces"] = len(faces)
    return out


def integrate(l3027, changes, for_lead=()):
    """-> (V3.0.28 lines, identity). Every line outside the V3.0.28 rows is byte-identical to the V3.0.27 line."""
    from engine.source import boq_line as BL
    sid = {ln["line_id"] for ln in l3027}
    rep, adds = {}, []
    for c in changes:
        if c["piece"] != PIECE:
            raise ValueError(f"{METHOD}: piece {c['piece']} (this version only books opening reveal faces)")
        if c["action"] == "REPLACE":
            lid = c["before"]["line_id"]
            if lid in rep or lid not in sid or c["after"]["line_id"] != lid:
                raise ValueError(f"{METHOD}: line {lid}: changed twice, not in V3.0.27, or its id changed")
            rep[lid] = c["after"]
        elif c["action"] == "ADD":
            a = c["after"]
            if a["line_id"] in sid or a["item_code"] not in ITEMS or a["unit"] != UNIT:
                raise ValueError(f"{METHOD}: an added line repeats a V3.0.27 line id or is not a reveal m2 line")
            adds.append(a)
        else:
            raise ValueError(f"{METHOD}: action {c['action']}")
    out = [rep.get(ln["line_id"], ln) for ln in l3027] + adds
    if len({ln["line_id"] for ln in out}) != len(out):
        raise ValueError(f"{METHOD}: a BOQ line id appears twice")
    for ln in out:
        BL.validate(ln)
    A3011.check_conflicts(out)
    A3010.check_same_openings(out)
    A3012.check_partition(out)
    A3014.check_floor_scope(out)
    A3015.check_family(out)
    A3018.check_splits(out)
    tile = A3021.check_tile_family(out)
    par = A3023.check_parapet_family(out)
    state = A3024.check_line_state(out, for_lead)
    outdoor = A3025.check_outdoor_family(out)
    blk = A3026.check_blockwork(out)
    ends = A3027.check_slab_ends(out)
    rev = check_reveals(out)
    pids = {(ln["project"]["project_id"], ln["project"]["revision_set_sha256"]) for ln in out}
    if len(pids) != 1:
        raise ValueError(f"{METHOD}: {len(pids)} project identities in the lines (one project, one revision set)")
    by27 = {ln["line_id"]: ln for ln in l3027}
    touched = set(rep) | {a["line_id"] for a in adds}
    outside = [ln for ln in out if ln["line_id"] not in touched]
    bad = [ln["line_id"] for ln in outside if A30.line_sha(by27[ln["line_id"]]) != A30.line_sha(ln)]
    if bad or len(outside) + len(rep) != len(l3027):
        raise ValueError(f"{METHOD}: {len(bad)} line(s) outside the V3.0.28 rows differ from {EXTENDS}")
    for lid, ln in rep.items():   # inside a row only quantity, state, basis and notes change
        a, b = copy.deepcopy(by27[lid]), copy.deepcopy(ln)
        for x in (a, b):
            for k in ("evidence_state", "measured_net", "bounded_range", "rfi", "notes"):
                x.pop(k, None)
            x["calculation"] = None
        if json.dumps(a, sort_keys=True) != json.dumps(b, sort_keys=True):
            raise ValueError(f"{METHOD}: line {lid} changed outside quantity / state / basis")
    ident = {"v3_0_27_lines": len(l3027), "v3_0_28_lines": len(out), "v3_0_28_rows": len(changes),
             "replaced": len(rep), "added": len(adds), "outside_rows": len(outside),
             "outside_rows_identical_to_v3_0_27": len(outside), "opening_reveals": rev, "slab_bar_ends": ends,
             "blockwork": blk, "outdoor_family": outdoor, "parapet_family": par, "wall_tile_family": tile,
             "line_state": state,
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
        rows.append({"version": METHOD, "action": rec["action"] + (f"_{rec['status']}" if rec.get("status") else ""),
                     "line_id": ref["line_id"], "item_code": ref["item_code"], "floor": loc.get("floor"),
                     "element_id": loc.get("element_id"), "unit": ref["unit"], "opening": rec.get("opening"),
                     "side": rec.get("side"), "faces": rec.get("faces"),
                     "before_released_v2_9": b29,
                     "before_v3_0_27": (A30._qty(c["before"]) if c["before"] is not None else
                                        dict(A30._qty(None), state="NOT_IN_V3_0_27")),
                     "after_v3_0_28": A30._qty(ref), "evidence_status": c.get("evidence_status"),
                     "still_held": c.get("held"), "release_status": "NOT RELEASED",
                     "owner_manual_method": PIECES[PIECE]["owner_manual_method"],
                     "drawing_derived_method": PIECES[PIECE]["drawing_method"],
                     "verification": c.get("verification") or {}, "rollback": ROLLBACK})
    return rows


LEDGER_CSV = ("version", "action", "line_id", "item_code", "floor", "opening", "side", "faces", "unit", "v2_9",
              "v3_0_27", "v3_0_28", "evidence_status", "held", "verification")
DIFF_CSV = ("line_id", "item_code", "floor", "element_id", "unit", "vs_v3_0_27", "vs_released_v2_9", "v2_9",
            "v3_0_27", "v3_0_28")


def _fmt_q(q):
    return A302._q(q) if q else ""


def ledger_csv(rows):
    return A305._csv([{"version": r["version"], "action": r["action"], "line_id": r["line_id"],
                       "item_code": r["item_code"], "floor": r["floor"], "opening": r["opening"], "side": r["side"],
                       "faces": "; ".join(f"{f['component']} {f.get('m2') if f.get('m2') is not None else 'HELD'}"
                                          for f in r["faces"] or ()),
                       "unit": r["unit"], "v2_9": _fmt_q(r["before_released_v2_9"]),
                       "v3_0_27": _fmt_q(r["before_v3_0_27"]), "v3_0_28": _fmt_q(r["after_v3_0_28"]),
                       "evidence_status": r["evidence_status"],
                       "held": "; ".join(f"{h['what']}: {h['why']}" for h in r["still_held"] or ())[:900],
                       "verification": f"{r['verification'].get('task')} {r['verification'].get('merge_commit') or ''}"
                                       .strip()} for r in rows], LEDGER_CSV)


def diff_rows(l3027, l3028, released_lines=None):
    b27 = {ln["line_id"]: ln for ln in l3027}
    rel = {A30._key(ln): ln for ln in released_lines or ()}
    out = []
    for ln in l3028:
        o = b27.get(ln["line_id"])
        vs = "ADDED" if o is None else ("SAME" if A30.line_sha(o) == A30.line_sha(ln) else
                                        ("CHANGED" if A30._qty(o) != A30._qty(ln) else "CHANGED_TEXT_ONLY"))
        r = rel.get(A30._key(ln)) if released_lines is not None else None
        vs29 = None if released_lines is None else ("NOT_IN_RELEASED" if r is None else
                                                    ("SAME_QUANTITY" if A30._qty(r) == A30._qty(ln) else
                                                     "QUANTITY_DIFFERS"))
        out.append({"line_id": ln["line_id"], "item_code": ln["item_code"], "floor": ln["location"].get("floor"),
                    "element_id": ln["location"].get("element_id"), "unit": ln["unit"], "vs_v3_0_27": vs,
                    "vs_released_v2_9": vs29, "v2_9": A302._q(A30._qty(r)) if r else "",
                    "v3_0_27": A302._q(A30._qty(o)) if o else "", "v3_0_28": A302._q(A30._qty(ln))})
    return out


def write(out, l3027, changes, log, doc, released_lines=None, for_lead=()):
    """the V3_0_28_* files beside the V3_0_27_* files. -> (file names, identity, ledger)."""
    from pathlib import Path
    from engine.source import boq_line as BL
    out = Path(out)
    l3028, ident = integrate(l3027, changes, for_lead)
    rows = ledger_rows(changes, released_lines)
    diff = diff_rows(l3027, l3028, released_lines)
    dsum = {}
    for d in diff:
        dsum.setdefault("vs_v3_0_27", {}).setdefault(d["vs_v3_0_27"], 0)
        dsum["vs_v3_0_27"][d["vs_v3_0_27"]] += 1
        if d["vs_released_v2_9"] is not None:
            dsum.setdefault("vs_released_v2_9", {}).setdefault(d["vs_released_v2_9"], 0)
            dsum["vs_released_v2_9"][d["vs_released_v2_9"]] += 1
    ident = dict(ident, diff=dsum)
    t27, t28 = A304.code_totals(l3027), A304.code_totals(l3028)
    moved = {k: {"v3_0_27": t27.get(k), "v3_0_28": t28.get(k)} for k in sorted(set(t27) | set(t28))
             if t27.get(k) != t28.get(k)}
    if any(k.split("|")[0] not in ITEMS or not k.endswith(f"|{UNIT}") for k in moved):
        raise ValueError(f"{METHOD}: totals moved outside the reveal items: {sorted(moved)[:5]}")
    led = {"schema": LEDGER_SCHEMA, "method": METHOD, "extends": EXTENDS, "candidate": CANDIDATE,
           "base": A30.BASE_METHOD, "released": A30.RELEASED_METHOD, "released_default": False, "rows": rows,
           "waiting_pieces": WAITING, "integration_package": True}
    run = {"method": METHOD, "policy": POLICY_ID, "extends": EXTENDS, "candidate": CANDIDATE,
           "base_method": A30.BASE_METHOD, "released_method": A30.RELEASED_METHOD, "released_default": False,
           "rollback": ROLLBACK, "identity": ident, "pieces": PIECES, "piece_logs": [log],
           "totals_moved_by_code": moved, "waiting_pieces": WAITING}
    files = {"V3_0_28_BOQ_LINES.json": BL.dumps(l3028),
             "V3_0_28_BOQ_LINES.csv": A30._lines_csv(l3028),
             "V3_0_28_INTEGRATION_LEDGER.json": A30._j(led),
             "V3_0_28_INTEGRATION_LEDGER.csv": ledger_csv(rows),
             "V3_0_28_DIFF.csv": A305._csv(diff, DIFF_CSV),
             "V3_0_28_RUN.json": A30._j(run)}
    for name, text in files.items():
        (out / name).write_text(text, encoding="utf-8")
    return sorted(files), ident, led


def policy_record():
    return {"method": METHOD, "extends": EXTENDS, "pieces": sorted(PIECES), "inputs_schema": INPUTS_SCHEMA,
            "released_default": False, "rollback": ROLLBACK, "items": sorted(ITEMS)}


__all__ = ["METHOD", "PIECES", "WAITING", "DEFAULT_GUARD_CLASS", "INPUTS_SCHEMA", "load_inputs", "fill_line",
           "narrow_line", "add_line", "element_id", "changes_for", "check_reveals", "integrate", "ledger_rows",
           "diff_rows", "write", "InputsError"]
