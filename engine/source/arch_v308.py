"""ARCH_TAKEOFF_V3.0.8 (T-231): the SAME opt-in BOQ candidate as ARCH_TAKEOFF_V3.0 .. V3.0.7 (engine.source.arch_v30,
arch_v301 .. arch_v307), extended with checker-merged structural pieces: element records that replace the candidate
lines of the same physical element, and released lines whose member no drawing of the issued set draws turned HELD.
Not a new method family and not the released default (owner management decision 2026-10-20 sections 2 and 5); rollback
is running the released ARCH_TAKEOFF_V2.9.

How it is built (tools/urban_boq_m9.py `arch --method ARCH_TAKEOFF_V3.0.8`):
  1. the run is the V3.0.7 candidate exactly: its V3_0_* .. V3_0_7_* files are written unchanged (arch_v30 .. arch_v307
     are not edited);
  2. ELEMENT RECORDS (one entry per piece of the project inputs, URBAN_V308_INPUTS_V1): the piece names its checker-
     merged source (file sha256, task, merge commit, checker run), the item code, unit m3 and its scope: the item, the
     floors, the physical elements and, where the item holds many other members (columns), the element-id markers of
     the lines that can be the same member. Every candidate line inside the scope is accounted for before a record is
     added (T-179 lesson):
       supersede_lines  the same physical element carried by another line: it becomes NOT_APPLICABLE_WITH_EVIDENCE
                        (never deleted, never summed). The figure it carries (a value, or a range for a bounded line) is
                        stated in the inputs and must equal the line; a line an earlier version (V3.0.1 .. V3.0.7)
                        changed is superseded only when the inputs name that and why (`earlier_change`);
       other_elements   another physical element of the item (kept byte-identical);
     an unaccounted scope line, or a named line the candidate does not have, refuses the run;
  3. one line per record: RELEASED -> SOURCE_DERIVED, evidence status VERIFIED only where the record names the checker
     run that re-measured that piece (`verified_by`), else DRAWING-CONFIRMED (NOT RELEASED: only the owner releases);
     BOUNDED -> BOUNDED_EXPOSURE with its range (HELD: the range is known, the value is not); UNQUANTIFIED ->
     BLOCKED_RFI (HELD or UNKNOWN as the record says), its figures only as information; missing is never 0. A record
     with dimensions is recomputed (arch_v307.dims_check: PRISM, height basis STRUCTURAL) and refused when it
     disagrees (> 0.0005 m3); a BOUNDED record's range must satisfy 0 <= low <= high;
  4. EXISTENCE HOLDS (piece MEMBER_EXISTENCE): a line whose member the issued set does not draw (the checker-merged
     classification NOT_DRAWN) turns BLOCKED_RFI naming the consultant item; its figure stays as information, never
     summed and never a verified 0. A live line leaves the released total; a line an earlier version set
     NOT_APPLICABLE as NOT_PRESENT (route figure kept in its inputs) becomes a visible HELD line (an absence of a drawn
     member is not a measured nothing). Only a MACHINE_ONLY / REVIEWED line, the figure must equal the line's, and a
     line an earlier version changed only with that change named (`earlier_change`);
  5. GUARD RE-CHECK (piece DEFAULT_GUARD): the merged guard runs again over the V3.0.8 lines with the guard inputs of
     V3.0.7 (arch_v307.guard_changes: a new holding finding on a live line holds it; a finding on an added line or a
     silent drawn part refuses);
  6. the V3_0_8_* files are written beside them: every line outside the V3.0.8 rows is byte-identical to the V3.0.7
     line (asserted on every run), and V3_0_8_DIFF.csv lists every line against V3.0.7 and against the released V2.9.

Rules: owner decision 2026-10-20 sections 2 and 5; WORKFLOW_CONTROLS 2026-10-21 sections 1, 4, 5;
ENGINEERING_REASONING_STANDARD 2026-10-22 sections 2.2, 3 and 7; UP-QTY-STATUS-001 (held is a range or blocked, never
0); Q-74 (a strap at its axis length between the faces it frames into; the overlap with a footing owned by the footing
up to the footing's own depth); R-CONC-OWN-1 (one intersection counted once); R-PLANTED-COL-1 proposed (a planted column
from the carrying beam top to the slab top, or to the soffit of a member billed through it); the member-existence rule
of T-220 (a column line exists on a storey only where that storey's slab plan draws it).
Nothing here names a project, a sheet, a layer, a mark or a coordinate; every number comes from the run or the inputs.
"""

from __future__ import annotations

import copy
import hashlib

from engine.source import arch_v30 as A30
from engine.source import arch_v302 as A302
from engine.source import arch_v304 as A304
from engine.source import arch_v305 as A305
from engine.source import arch_v307 as A307

DEFAULT_GUARD_CLASS = "GUARD_HOST"      # T-212: a candidate method; it reaches the guard through arch_v307
METHOD = "ARCH_TAKEOFF_V3.0.8"
EXTENDS = A307.METHOD
CANDIDATE = A30.METHOD                  # the candidate family this version extends (never a new method family)
POLICY_ID = "URBAN_BOQ_T231_ARCH_V3_0_8"
LEDGER_SCHEMA = "URBAN_V308_INTEGRATION_LEDGER_V1"
INPUTS_SCHEMA = "URBAN_V308_INPUTS_V1"
ROLLBACK = A30.ROLLBACK
STATES = ("RELEASED", "BOUNDED", "UNQUANTIFIED")
HELD_STATUS = ("HELD", "UNKNOWN")
LIVE_EVIDENCE = A307.LIVE_EVIDENCE
InputsError = A307.InputsError

PIECES = {
    "STRAP_CONCRETE": {
        "module": "engine/source/arch_v308.py (typed checker-merged element records)",
        "policy": "STRAP_CONCRETE_AXIS_V1", "rule_id": "Q-74", "rule_version": "owner-2026-10-22",
        "owner_rules": ["Q-74 (owner 2026-10-22, confirmed: concrete = section x the actual axis length between the "
                        "established faces; concrete inside a footing counted once)",
                        "R-CONC-OWN-1 (one intersection counted once)",
                        "Q-31 C (the open two-footing outline stays HELD)", "UP-QTY-STATUS-001"],
        "owner_manual_method": "manual QS take-off of a strap beam: printed section (width x depth from the beam "
                               "schedule) x the length along the beam axis between the faces of the two footings it "
                               "frames into; the part inside a footing is the footing's, once",
        "drawing_method": "strap edge lines and footing outlines from the foundation plan: the printed-width strip on "
                          "the drawn axis outside both footing outlines x the printed depth (= width x axis length "
                          "where each edge crosses one straight face); inside a footing the strap is footing concrete "
                          "up to the footing thickness, the excess depth (strap deeper than the footing) is strap "
                          "concrete kept as a HELD range while the strap level is not printed"},
    "PLANTED_COLUMN": {
        "module": "engine/source/arch_v308.py (typed checker-merged element records)",
        "policy": "PLANTED_COLUMN_V1_RECORDS", "rule_id": "R-PLANTED-COL-1", "rule_version": "proposed-2026-10-23",
        "owner_rules": ["R-CONC-OWN-1 (the carrying beam keeps the junction under the column)",
                        "URBAN-COLUMN-HEIGHT-TO-CONTROLLING-MEMBER@v1 + URBAN-NON-OVERLAPPING-SLAB-BEAM-MODEL@v1 "
                        "(the owner split, shown beside)",
                        "owner directive X6 (a schedule no longer wins automatically: plan text, dimension chain, "
                        "drawn outline and schedule kept apart)", "ERS s.3 (never the larger end)",
                        "UP-QTY-STATUS-001"],
        "owner_manual_method": "manual QS take-off of a column per storey: section x the storey interval split into "
                               "column to the controlling member, joint and slab part (T-119 owner split)",
        "drawing_method": "the planted column's start symbol on the carrying beam's plan and its own outline on the "
                          "storey above; section from the plan text and the two outlines kept apart; height from the "
                          "carrying beam top to the slab top (every framing member net of the column) or to the "
                          "soffit of a member billed through it; a section conflict or an unprinted top is HELD"},
    "MEMBER_EXISTENCE": {
        "module": "engine/source/arch_v308.py (checker-merged existence classification)",
        "policy": "MEMBER_EXISTENCE_HOLD_V1", "rule_id": "R-COL-EXIST-1", "rule_version": "proposed-2026-10-23",
        "owner_rules": ["T-220 (MERGED): a column line exists on a storey only where that storey's slab plan draws "
                        "the member (outline with its hatch); a schedule band carried to every storey is not a member",
                        "UP-QTY-STATUS-001 (NOT_DRAWN is a consultant item, never a verified 0)"],
        "owner_manual_method": "the owner prices a column only where the drawings show it on that storey",
        "drawing_method": "the storey's slab plan, the column schedule, the sections and the architectural plans "
                          "searched at the member: nothing drawn -> NOT_DRAWN, the released line HELD with the "
                          "consultant item, its figure kept as information"},
    "DEFAULT_GUARD": A307.PIECES["DEFAULT_GUARD"],
}
WAITING = dict(A307.WAITING)
WAITING.update({
    "STRAP_FOOTING_OWNERSHIP": "T-230 decides every strap / tie-beam end intersection; until it merges the SB3 / F3 "
                               "excess depth and the strap inside the open two-footing outline stay HELD here",
    "BEAMS_AT_PLANTED_COLUMNS": "the carrying beams cut at the planted columns by route G (short under the column) are "
                                "T-229's (merged, rule proposal R-BEAM-CONT-1); their lines are NOT changed here",
    "STRAP_STEEL_FORMWORK_EXCAVATION": "strap bars at the axis run, side formwork and excavation (T-174 ledger) are a "
                                       "later package (bar / formwork / earthworks lines, T-199 for formwork)",
})


def _r(x, n=6):
    return None if x is None else round(float(x), n)


_num = A307._num


# ================================================================================================ project inputs
def _carried(ln):
    """the figure a line carries: its live quantity, a bounded line's range [low, high], or the figure an earlier
    version kept as information when it held the line (V3.0.6 / V3.0.7 hold records)."""
    if ln["evidence_state"] in LIVE_EVIDENCE:
        return A30._qty(ln)["value"]
    if ln["evidence_state"] == "BOUNDED_EXPOSURE":
        q = A30._qty(ln)
        return [q["low"], q["high"]]
    return A307._carried_qty(ln)


def _same(carried, stated):
    if carried is None or stated is None:
        return False
    if isinstance(stated, (list, tuple)):
        return (isinstance(carried, (list, tuple)) and len(carried) == len(stated) == 2
                and all(_num(c) and _num(s) and abs(float(c) - float(s)) <= 1e-6 for c, s in zip(carried, stated)))
    return _num(carried) and _num(stated) and abs(float(carried) - float(stated)) <= 1e-6


def _check_record(p, r, sc):
    key = (r.get("element"), r.get("component"), r.get("part") or "")
    st = r.get("state")
    if st not in STATES:
        raise InputsError(f"piece {p} {key}: state {st!r} not one of {STATES}")
    if st == "RELEASED" and not (_num(r.get("value")) and r["value"] > 0):
        raise InputsError(f"piece {p} {key}: a RELEASED record carries a value > 0 (missing is never 0)")
    if st == "BOUNDED":
        rg = r.get("range")
        if not (isinstance(rg, (list, tuple)) and len(rg) == 2 and all(_num(x) for x in rg)
                and 0 <= rg[0] <= rg[1] and rg[1] > 0):
            raise InputsError(f"piece {p} {key}: a BOUNDED record carries a range [low, high], 0 <= low <= high, "
                              "high > 0")
    if st != "RELEASED" and (not r.get("reasons") or r.get("evidence_status") not in HELD_STATUS):
        raise InputsError(f"piece {p} {key}: a {st} record names why and its status HELD / UNKNOWN")
    if st == "RELEASED" and r.get("evidence_status") in HELD_STATUS:
        raise InputsError(f"piece {p} {key}: a RELEASED record cannot be {r['evidence_status']}")
    if r.get("floor") not in sc["floors"]:
        raise InputsError(f"piece {p} {key}: floor {r.get('floor')!r} outside the scope {sc['floors']}")
    ge = r.get("guard_element") or {}
    if not ge.get("element_id") or not ge.get("part"):
        raise InputsError(f"piece {p} {key}: guard_element (register element_id and part) is required")
    if r.get("dims") and st == "RELEASED":
        A307.dims_check(r)


def load_inputs(doc, project_id=None):
    """URBAN_V308_INPUTS_V1 or None:
        {"schema", "project",
         "pieces": [{"piece": STRAP_CONCRETE | PLANTED_COLUMN, "item_code", "unit": "m3", "source": {...},
                     "scope": {"floors", "physical_elements" (list, or None = every physical element of the item),
                               "element_markers" (list of substrings of the element id, or None = every line),
                               "supersede_lines": [{element_id, floor, why, carried (value or [low, high]),
                                                    earlier_change (text, when an earlier version changed the line)}],
                               "other_elements": [{element_id, floor, why}]},
                     "records": [{element, component, part, floor, state, value | range, dims, verified_by, reasons,
                                  evidence_status, guard_element: {element_id, part}, printed, formula, info}],
                     "declared_totals": {...}, "line_group": {...}}],
         "existence": {"source": {...}, "item_code", "unit", "lines": [{element_id, floor, carried, why,
                       consultant_item, evidence}]},
         "guard": as URBAN_V307_INPUTS_V1 "guard" (new_records may be empty)}"""
    if doc is None:
        return None
    if doc.get("schema") != INPUTS_SCHEMA:
        raise InputsError(f"project inputs: schema must be {INPUTS_SCHEMA}")
    if project_id and doc.get("project") not in (None, project_id):
        raise InputsError(f"project inputs are for {doc.get('project')!r}, the run is {project_id!r}")
    seen = set()
    for pc in doc.get("pieces") or ():
        p = pc.get("piece")
        if p not in ("STRAP_CONCRETE", "PLANTED_COLUMN") or p in seen:
            raise InputsError(f"piece {p!r}: one of STRAP_CONCRETE / PLANTED_COLUMN, once each")
        seen.add(p)
        if pc.get("unit") != "m3" or not pc.get("item_code"):
            raise InputsError(f"piece {p}: unit m3 and an item_code are required")
        A307._source(pc.get("source"), f"piece {p}")
        sc = pc.get("scope") or {}
        if not sc.get("floors"):
            raise InputsError(f"piece {p}: scope needs floors")
        for k in ("physical_elements", "element_markers"):
            if sc.get(k) is not None and not (isinstance(sc[k], list) and sc[k] and all(sc[k])):
                raise InputsError(f"piece {p}: scope.{k} is a non-empty list or absent")
        for k in ("supersede_lines", "other_elements"):
            for x in sc.get(k) or ():
                if not x.get("element_id") or not x.get("floor") or not x.get("why"):
                    raise InputsError(f"piece {p}: every scope.{k} entry has element_id, floor and why")
                if k == "supersede_lines" and x.get("carried") is None:
                    raise InputsError(f"piece {p}: scope.{k} {x['element_id']} states the figure it carries")
        ids = set()
        for r in pc.get("records") or ():
            key = (r.get("element"), r.get("component"), r.get("part") or "")
            if not r.get("element") or not r.get("component") or key in ids:
                raise InputsError(f"piece {p}: every record has a unique element / component / part: {key}")
            ids.add(key)
            _check_record(p, r, sc)
        if not ids:
            raise InputsError(f"piece {p}: no records")
    ex = doc.get("existence")
    if ex is not None:
        A307._source(ex.get("source"), "existence")
        if ex.get("unit") != "m3" or not ex.get("item_code"):
            raise InputsError("existence: unit m3 and an item_code are required")
        keys = set()
        for x in ex.get("lines") or ():
            for k in ("element_id", "floor", "why", "consultant_item"):
                if not x.get(k):
                    raise InputsError(f"existence: every line names {k}")
            if not (_num(x.get("carried")) and x["carried"] > 0):
                raise InputsError(f"existence: line {x['element_id']} states the figure it carries (> 0)")
            if (x["element_id"], x["floor"]) in keys:
                raise InputsError(f"existence: line {x['element_id']} {x['floor']} named twice")
            keys.add((x["element_id"], x["floor"]))
        if not keys:
            raise InputsError("existence: no lines")
    g = doc.get("guard")
    if g is not None:
        A307.load_inputs({"schema": A307.INPUTS_SCHEMA, "project": doc.get("project"), "guard": g}, project_id)
    return doc


# ================================================================================================ element records
def _scope_lines(pc, lines):
    sc = pc["scope"]
    pes, marks = sc.get("physical_elements"), sc.get("element_markers")
    out = []
    for ln in lines:
        loc = ln.get("location") or {}
        if ln["item_code"] != pc["item_code"] or ln["unit"] != pc["unit"] or loc.get("floor") not in sc["floors"]:
            continue
        if pes is not None and str(ln.get("physical_element")) not in pes:
            continue
        if marks is not None and not any(m in str(loc.get("element_id")) for m in marks):
            continue
        out.append(ln)
    return out


def _check_replaceable(ln, earlier, x=None):
    lid = ln["line_id"]
    if lid in earlier and not (x or {}).get("earlier_change"):
        raise InputsError(f"{METHOD}: line {lid} ({(ln.get('location') or {}).get('element_id')}) was changed by an "
                          "earlier candidate version: superseded only when the inputs name that change and why "
                          "(earlier_change)")
    if ln.get("approval_state") not in ("MACHINE_ONLY", "REVIEWED"):
        raise ValueError(f"{METHOD}: line {lid} is {ln.get('approval_state')}: an approved line is never replaced")


def record_line(pid, rev, docs, piece, pc, r):
    """one BOQ line for one record. -> (line, evidence status, recomputed m3)"""
    from engine.source import boq_line as BL
    p, src = PIECES[piece], pc["source"]
    v, dim_hold = A307.dims_check(r) if r["state"] == "RELEASED" else (None, None)
    st = r["state"]
    reasons = list(r.get("reasons") or ())
    info = dict(r.get("info") or {})
    evs = r.get("evidence_status")
    if st == "RELEASED" and dim_hold:
        st, evs = "UNQUANTIFIED", "HELD"
        reasons.append(dim_hold)
        info["figure_not_released_m3"] = _r(r["value"])
    ev = {"RELEASED": "SOURCE_DERIVED", "BOUNDED": "BOUNDED_EXPOSURE", "UNQUANTIFIED": "BLOCKED_RFI"}[st]
    eid = f"HL:{piece}:{r['element']}:{A305._slug(r['component'])}" + (
        f":{A305._slug(r['part'])}" if r.get("part") else "")
    rfi = None if ev == "SOURCE_DERIVED" else {"question": "; ".join(reasons)[:900], "unlocks": eid}
    br = None
    if ev == "BOUNDED_EXPOSURE":
        br = {"low": _r(r["range"][0]), "high": _r(r["range"][1]),
              "basis": (r.get("range_basis") or "; ".join(reasons))[:300]}
    pe = r.get("physical_element") or (pc["scope"].get("physical_elements") or [piece])[0]
    ln = BL.make_line(project_id=pid, revision_set_sha256=rev, item_code=pc["item_code"], unit="m3",
                      evidence_state=ev, measured_net=_r(r["value"]) if ev == "SOURCE_DERIVED" else None,
                      bounded_range=br, element_id=eid, floor=r["floor"], physical_element=pe, subtrade=pe,
                      formula=r.get("formula") or ("held: " + "; ".join(reasons))[:400],
                      inputs=dict({"policy": p["policy"], "source": src["file"], "source_sha256": src["sha256"],
                                   "element": r["element"], "component": r["component"], "part": r.get("part"),
                                   "printed": r.get("printed"), "dims": r.get("dims"), "range": r.get("range"),
                                   "recomputed_m3": _r(v), "reasons": reasons, "record_state": r["state"],
                                   "guard_element": r["guard_element"]}, **info),
                      documents=docs, geometry_source=r.get("geometry_source") or "SCHEDULE_ONLY",
                      geometry_confidence="TOLERANCE_CERTIFIED" if ev == "SOURCE_DERIVED" else "INFERRED_CANDIDATE",
                      rule_id=p["rule_id"], rule_version=p["rule_version"], material_state="SOURCE", rfi=rfi,
                      notes=f"{METHOD}: {piece.lower().replace('_', ' ')} by checker-merged record ({src['task']}, "
                            f"MERGED {src['merge_commit']})")
    if st == "RELEASED":
        evs = "VERIFIED" if r.get("verified_by") else "DRAWING-CONFIRMED"
    return ln, evs, v


def record_changes(inputs, lines, earlier_changed=()):
    """the element-record pieces on the V3.0.7 lines. -> (changes, logs)"""
    if not inputs or not inputs.get("pieces"):
        return [], [{"piece": p, "state": "NO_PROJECT_INPUT"} for p in ("STRAP_CONCRETE", "PLANTED_COLUMN")]
    pid, rev, docs = A302._proj(lines)
    have = {ln["line_id"] for ln in lines}
    earlier = set(earlier_changed)
    changes, logs, touched = [], [], set()
    for pc in inputs["pieces"]:
        piece, sc, src = pc["piece"], pc["scope"], pc["source"]
        verif = {"task": src["task"], "merge_commit": src["merge_commit"], "verifier_run": src["checker_run"],
                 "source": src["file"], "source_sha256": src["sha256"]}
        named = {(x["element_id"], x["floor"]): x for x in sc.get("supersede_lines") or ()}
        other = {(x["element_id"], x["floor"]): x for x in sc.get("other_elements") or ()}
        if set(named) & set(other):
            raise InputsError(f"piece {piece}: a scope line is accounted for twice (supersede / other)")
        log = {"piece": piece, "state": "RUN", "source": src, "item_code": pc["item_code"], "unit": pc["unit"],
               "scope": {k: sc.get(k) for k in ("floors", "physical_elements", "element_markers")},
               "scope_lines": [], "records": [], "evidence_status": {}, "line_group": pc.get("line_group")}
        seen = set()
        sup_value, sup_low, sup_high = 0.0, 0.0, 0.0
        for ln in _scope_lines(pc, lines):
            k = ((ln.get("location") or {}).get("element_id"), ln["location"].get("floor"))
            entry = {"line_id": ln["line_id"], "element_id": k[0], "floor": k[1],
                     "evidence_state": ln["evidence_state"], "quantity": A302._q(A30._qty(ln)),
                     "earlier_change": ln["line_id"] in earlier}
            if k in other:
                seen.add(k)
                log["scope_lines"].append(dict(entry, accounted="OTHER_ELEMENT", why=other[k]["why"]))
                continue
            if k not in named:
                raise InputsError(f"piece {piece}: candidate line {ln['line_id']} ({k[0]} {k[1]}, "
                                  f"{A302._q(A30._qty(ln))}) is inside the scope and is neither superseded by name nor "
                                  "declared another element: an integration that only adds is refused")
            if ln["line_id"] in touched:
                raise ValueError(f"{METHOD}: line {ln['line_id']} superseded twice")
            x = named[k]
            _check_replaceable(ln, earlier, x)
            cq = _carried(ln)
            if not _same(cq, x["carried"]):
                raise InputsError(f"piece {piece}: line {k[0]} carries {cq}, the inputs state {x['carried']}: the "
                                  "superseded figure must be the one the line carries")
            seen.add(k)
            if isinstance(cq, (list, tuple)):
                sup_low += float(cq[0])
                sup_high += float(cq[1])
            else:
                sup_value += float(cq)
            note = (f"{METHOD}: SUPERSEDED - {A302._q(A30._qty(ln))} {ln['unit']} (V3.0.7 state {ln['evidence_state']}) "
                    f"replaced by the checker-merged {piece.lower().replace('_', ' ')} records of {src['task']} "
                    f"(MERGED {src['merge_commit']}): {x['why']}")
            codes = ["SUPERSEDED_BY_RECORD"] + (["EARLIER_CHANGE"] if ln["line_id"] in earlier else [])
            changes.append(A307._retire(ln, x["why"], note, verif, piece, codes,
                                        x.get("drawing_reference") or src["file"]))
            touched.add(ln["line_id"])
            log["scope_lines"].append(dict(entry, accounted="SUPERSEDED", why=x["why"], carried=cq,
                                           earlier_change_why=x.get("earlier_change")))
        missing = (set(named) | set(other)) - seen
        if missing:
            raise InputsError(f"piece {piece}: scope names line(s) the candidate does not have: {sorted(missing)}")
        released, b_low, b_high = 0.0, 0.0, 0.0
        for r in pc["records"]:
            key = f"{r['element']}:{r['component']}" + (f":{r['part']}" if r.get("part") else "")
            ln, evs, v = record_line(pid, rev, docs, piece, pc, r)
            if ln["line_id"] in have:
                raise ValueError(f"{METHOD}: record {key} repeats a candidate line id")
            have.add(ln["line_id"])
            held = []
            if ln["evidence_state"] == "SOURCE_DERIVED":
                released += ln["measured_net"]
            else:
                rg = ln.get("bounded_range")
                if rg:
                    b_low += rg["low"]
                    b_high += rg["high"]
                held = [{"what": f"{r['element']} {r['component']}", "why": ln["rfi"]["question"],
                         "range": [rg["low"], rg["high"]] if rg else None}]
            changes.append(A305._change(piece, "ADD", None, ln, drawing_reference=r.get("printed") or src["file"],
                                        held=held, downstream=list(r.get("downstream") or ()),
                                        verification=dict(verif, record_verified_by=r.get("verified_by")),
                                        evidence_status=evs, guard_element=r["guard_element"]))
            log["records"].append({"record": key, "line_id": ln["line_id"], "floor": r["floor"],
                                   "evidence_state": ln["evidence_state"], "evidence_status": evs,
                                   "quantity": ln["measured_net"], "range": ln.get("bounded_range"),
                                   "recomputed_m3": _r(v)})
            log["evidence_status"][evs] = log["evidence_status"].get(evs, 0) + 1
        log["totals"] = {"released_added": _r(released), "superseded_value": _r(sup_value),
                         "item_move": _r(released - sup_value), "bounded_added": [_r(b_low), _r(b_high)],
                         "bounded_superseded": [_r(sup_low), _r(sup_high)]}
        for k, v in (pc.get("declared_totals") or {}).items():
            got = log["totals"].get(k)
            if isinstance(v, (list, tuple)):
                ok = isinstance(got, list) and all(abs((a or 0) - b) <= 0.0006 for a, b in zip(got, v))
            else:
                ok = got is not None and abs(got - v) <= 0.0006
            if not ok:
                raise ValueError(f"{METHOD}: piece {piece} {k} {got} != the declared {v}")
        log["declared_totals"] = pc.get("declared_totals") or {}
        logs.append(log)
    return changes, logs


# ================================================================================================ existence holds
def _not_present(ln):
    """the route figure an earlier version kept on a line it set NOT_APPLICABLE as NOT_PRESENT (V3.0.1 route scope:
    `inputs.v3_0_1 = {status: NOT_PRESENT, route_m3}`), or None."""
    inp = (ln.get("calculation") or {}).get("inputs") or {}
    for v in inp.values():
        if isinstance(v, dict) and v.get("status") == "NOT_PRESENT" and _num(v.get("route_m3")):
            return float(v["route_m3"])
    return None


def existence_changes(inputs, lines, touched=(), earlier_changed=()):
    """MEMBER_EXISTENCE: lines whose member the issued set does not draw -> BLOCKED_RFI (HELD, consultant item). A live
    line leaves the released total; a line an earlier version set NOT_APPLICABLE as NOT_PRESENT (an absence read as
    nothing to measure) becomes visible as HELD, its route figure as information (never a verified 0). -> (changes,
    log)"""
    earlier = set(earlier_changed)
    ex = (inputs or {}).get("existence")
    if not ex:
        return [], {"piece": "MEMBER_EXISTENCE", "state": "NO_PROJECT_INPUT"}
    src = ex["source"]
    verif = {"task": src["task"], "merge_commit": src["merge_commit"], "verifier_run": src["checker_run"],
             "source": src["file"], "source_sha256": src["sha256"]}
    log = {"piece": "MEMBER_EXISTENCE", "state": "RUN", "source": src, "held": [], "held_total_info": 0.0}
    changes = []
    for x in ex["lines"]:
        hit = [ln for ln in lines if ln["item_code"] == ex["item_code"] and ln["unit"] == ex["unit"]
               and (ln.get("location") or {}).get("element_id") == x["element_id"]
               and ln["location"].get("floor") == x["floor"]]
        if len(hit) != 1:
            raise InputsError(f"existence: line {x['element_id']} {x['floor']} found {len(hit)} time(s); exactly one")
        ln = hit[0]
        if ln["line_id"] in touched:
            raise ValueError(f"{METHOD}: line {ln['line_id']} held for existence and changed by a record piece")
        live = ln["evidence_state"] in LIVE_EVIDENCE and ln.get("measured_net") is not None
        absent = _not_present(ln) if ln["evidence_state"] == "NOT_APPLICABLE_WITH_EVIDENCE" else None
        if not live and absent is None:
            raise InputsError(f"existence: line {x['element_id']} {x['floor']} is {ln['evidence_state']}: only a live "
                              "line, or a line an earlier version set not applicable as NOT_PRESENT, is held here (a "
                              "held line stays as it is)")
        if ln["line_id"] in earlier and not x.get("earlier_change"):
            raise InputsError(f"existence: line {x['element_id']} {x['floor']} was changed by an earlier candidate "
                              "version: held only when the inputs name that change and why (earlier_change)")
        if ln.get("approval_state") not in ("MACHINE_ONLY", "REVIEWED"):
            raise ValueError(f"{METHOD}: line {ln['line_id']} is {ln.get('approval_state')}: never re-held")
        figure = float(ln["measured_net"]) if live else absent
        if abs(figure - float(x["carried"])) > 1e-6:
            raise InputsError(f"existence: line {x['element_id']} carries {_r(figure)}, the inputs state "
                              f"{x['carried']}")
        why = (f"MEMBER NOT DRAWN: {x['why']}; consultant item {x['consultant_item']} (never a verified 0; the line "
               "returns only on a drawing or a consultant answer)")
        after = copy.deepcopy(ln)
        after.update(evidence_state="BLOCKED_RFI", measured_net=None, bounded_range=None, gross=None)
        after["rfi"] = {"question": why[:900], "unlocks": x["element_id"]}
        after["calculation"] = dict(after["calculation"], inputs=dict(
            after["calculation"].get("inputs") or {},
            member_existence_v308={"policy": PIECES["MEMBER_EXISTENCE"]["policy"], "info_qty_v3_0_7": A30._qty(ln),
                                   "figure_m3_information": _r(figure),
                                   "was": "LIVE" if live else "NOT_APPLICABLE (earlier NOT_PRESENT: an absence of a "
                                                              "drawn member, not a verified 0)",
                                   "classification": "NOT_DRAWN", "consultant_item": x["consultant_item"],
                                   "evidence": list(x.get("evidence") or ()), "source": src["file"],
                                   "task": src["task"]}))
        A305._note(after, f"{METHOD}: HELD - member not drawn on its storey ({src['task']}, MERGED "
                          f"{src['merge_commit']}); consultant item {x['consultant_item']}; figure {_r(figure)} "
                          f"{ln['unit']} kept as information, never summed")
        changes.append(A305._change("MEMBER_EXISTENCE", "REPLACE", ln, after,
                                    drawing_reference="; ".join(x.get("evidence") or ())[:600],
                                    held=[{"what": f"{ln['item_code']} {x['element_id']} {x['floor']}", "why": why[:900],
                                           "range": None}], downstream=list(x.get("downstream") or ()),
                                    verification=dict(verif, record_verified_by=x.get("verified_by")),
                                    evidence_status="HELD", codes=["MEMBER_NOT_DRAWN", x["consultant_item"]]))
        log["held"].append({"line_id": ln["line_id"], "element_id": x["element_id"], "floor": x["floor"],
                            "was": "LIVE" if live else "NOT_APPLICABLE", "info_qty": _r(figure),
                            "released_moved": -_r(figure) if live else 0.0, "consultant_item": x["consultant_item"],
                            "checker_re_measured": bool(x.get("verified_by"))})
        log["held_total_info"] += figure
        log["released_moved"] = _r(log.get("released_moved", 0.0) - (figure if live else 0.0))
    log["held_total_info"] = _r(log["held_total_info"])
    if ex.get("declared_total") is not None and abs(log["held_total_info"] - ex["declared_total"]) > 0.0006:
        raise ValueError(f"{METHOD}: existence held {log['held_total_info']} != the declared {ex['declared_total']}")
    return changes, log


# ================================================================================================ integrate / write
def changes_for(inputs, l307, earlier_changed=()):
    """element records, then the existence holds, then the guard re-check over the result. -> (changes, logs)"""
    ch_r, logs = record_changes(inputs, l307, earlier_changed)
    rep = {c["before"]["line_id"]: c["after"] for c in ch_r if c["action"] == "REPLACE"}
    ch_e, log_e = existence_changes(inputs, l307, set(rep), earlier_changed)
    rep.update({c["before"]["line_id"]: c["after"] for c in ch_e})
    view = [rep.get(ln["line_id"], ln) for ln in l307]
    ch_g, log_g = A307.guard_changes(inputs, view, [c for c in ch_r if c["action"] == "ADD"], set(rep))
    for c in ch_g:   # a guard hold written by the V3.0.7 code is this version's row
        A305._note(c["after"], f"(re-check run by {METHOD})")
    return ch_r + ch_e + ch_g, logs + [log_e, log_g]


def integrate(l307, v308_changes):
    """-> (V3.0.8 lines, identity). Every line outside the V3.0.8 rows is byte-identical to the V3.0.7 line."""
    from engine.source import boq_line as BL
    sid = {ln["line_id"] for ln in l307}
    rep, adds = {}, []
    for c in v308_changes:
        if c["action"] == "REPLACE":
            lid = c["before"]["line_id"]
            if lid in rep:
                raise ValueError(f"{METHOD}: line {lid} changed twice")
            if lid not in sid:
                raise ValueError(f"{METHOD}: a change names a line the V3.0.7 run does not have")
            if c["after"]["line_id"] != lid:
                raise ValueError(f"{METHOD}: a changed line keeps its line id")
            rep[lid] = c["after"]
        elif c["action"] == "ADD":
            if c["after"]["line_id"] in sid:
                raise ValueError(f"{METHOD}: an added line repeats a V3.0.7 line id")
            adds.append(c["after"])
        else:
            raise ValueError(f"{METHOD}: action {c['action']}")
    out = [rep.get(ln["line_id"], ln) for ln in l307] + adds
    if len({ln["line_id"] for ln in out}) != len(out):
        raise ValueError(f"{METHOD}: a BOQ line id appears twice")
    for ln in out:
        BL.validate(ln)
    by307 = {ln["line_id"]: ln for ln in l307}
    touched = set(rep) | {a["line_id"] for a in adds}
    outside = [ln for ln in out if ln["line_id"] not in touched]
    bad = [ln["line_id"] for ln in outside if A30.line_sha(by307[ln["line_id"]]) != A30.line_sha(ln)]
    if bad or len(outside) + len(rep) != len(l307):
        raise ValueError(f"{METHOD}: {len(bad)} line(s) outside the V3.0.8 rows differ from {EXTENDS}")
    ident = {"v3_0_7_lines": len(l307), "v3_0_8_lines": len(out), "v3_0_8_rows": len(v308_changes),
             "replaced": len(rep), "added": len(adds), "outside_rows": len(outside),
             "outside_rows_identical_to_v3_0_7": len(outside),
             "outside_rows_sha256": hashlib.sha256("".join(A30.line_sha(x) for x in outside).encode()).hexdigest()}
    return out, ident


def ledger_rows(changes, released_lines=None):
    rel = {A30._key(ln): ln for ln in released_lines or ()}
    rows = []
    for c in changes:
        ref = c["after"] if c["before"] is None else c["before"]
        b307 = A30._qty(c["before"]) if c["before"] is not None else dict(A30._qty(None), state="NOT_IN_V3_0_7")
        b29 = None
        if released_lines is not None:
            b29 = A30._qty(rel[A30._key(ref)]) if A30._key(ref) in rel else dict(A30._qty(None),
                                                                                 state="NOT_IN_RELEASED")
        p = PIECES[c["piece"]]
        loc = ref.get("location") or {}
        rows.append({"version": METHOD, "piece": c["piece"], "action": c["action"], "line_id": ref["line_id"],
                     "item_code": ref["item_code"], "floor": loc.get("floor"),
                     "element_id": c["after"]["location"].get("element_id"), "unit": c["after"]["unit"],
                     "before_released_v2_9": b29, "before_v3_0_7": b307, "after_v3_0_8": A30._qty(c["after"]),
                     "evidence_status": c.get("evidence_status") or "HELD", "release_status": "NOT RELEASED",
                     "codes": c.get("codes") or [], "citations": c.get("citations") or [],
                     "drawing_reference": c.get("drawing_reference"),
                     "owner_manual_method": p["owner_manual_method"], "drawing_method": p["drawing_method"],
                     "owner_rules": p["owner_rules"],
                     "verification": dict(c.get("verification") or {}, module=p["module"], policy=p["policy"]),
                     "held": c.get("held") or [], "downstream": c.get("downstream") or [], "rollback": ROLLBACK})
    return rows


LEDGER_CSV = ("version", "piece", "action", "line_id", "item_code", "floor", "element_id", "unit", "v2_9", "v3_0_7",
              "v3_0_8", "evidence_status", "release_status", "codes", "drawing_reference", "verification", "held")


def ledger_csv(rows):
    return A305._csv([{"version": r["version"], "piece": r["piece"], "action": r["action"], "line_id": r["line_id"],
                       "item_code": r["item_code"], "floor": r["floor"], "element_id": r["element_id"],
                       "unit": r["unit"], "v2_9": A302._q(r["before_released_v2_9"]),
                       "v3_0_7": A302._q(r["before_v3_0_7"]), "v3_0_8": A302._q(r["after_v3_0_8"]),
                       "evidence_status": r["evidence_status"], "release_status": r["release_status"],
                       "codes": " ".join(r["codes"]), "drawing_reference": str(r["drawing_reference"])[:300],
                       "verification": f"{r['verification'].get('task')} {r['verification'].get('merge_commit')}"
                                       + (f" / {r['verification']['record_verified_by']}"
                                          if r["verification"].get("record_verified_by") else ""),
                       "held": "; ".join(str(h.get("why") or h.get("what")) for h in r["held"])[:600]}
                      for r in rows], LEDGER_CSV)


DIFF_CSV = ("line_id", "item_code", "floor", "element_id", "unit", "vs_v3_0_7", "vs_released_v2_9", "v2_9", "v3_0_7",
            "v3_0_8")


def diff_rows(l307, l308, released_lines=None):
    b307 = {ln["line_id"]: ln for ln in l307}
    rel = {A30._key(ln): ln for ln in released_lines or ()}
    out = []
    for ln in l308:
        o = b307.get(ln["line_id"])
        vs = "ADDED" if o is None else ("SAME" if A30.line_sha(o) == A30.line_sha(ln) else "CHANGED")
        r = rel.get(A30._key(ln)) if released_lines is not None else None
        vs29 = None if released_lines is None else ("NOT_IN_RELEASED" if r is None else
                                                    ("SAME_QUANTITY" if A30._qty(r) == A30._qty(ln) else
                                                     "QUANTITY_DIFFERS"))
        out.append({"line_id": ln["line_id"], "item_code": ln["item_code"], "floor": ln["location"].get("floor"),
                    "element_id": ln["location"].get("element_id"), "unit": ln["unit"], "vs_v3_0_7": vs,
                    "vs_released_v2_9": vs29, "v2_9": A302._q(A30._qty(r)) if r else "",
                    "v3_0_7": A302._q(A30._qty(o)) if o else "", "v3_0_8": A302._q(A30._qty(ln))})
    return out


def write(out, l307, v308_changes, logs, inputs, released_lines=None):
    """the V3_0_8_* files beside the V3_0_7_* files. -> (file names, identity, ledger)."""
    from pathlib import Path
    from engine.source import boq_line as BL
    out = Path(out)
    l308, ident = integrate(l307, v308_changes)
    rows = ledger_rows(v308_changes, released_lines)
    diff = diff_rows(l307, l308, released_lines)
    dsum = {}
    for d in diff:
        dsum.setdefault("vs_v3_0_7", {}).setdefault(d["vs_v3_0_7"], 0)
        dsum["vs_v3_0_7"][d["vs_v3_0_7"]] += 1
        if d["vs_released_v2_9"] is not None:
            dsum.setdefault("vs_released_v2_9", {}).setdefault(d["vs_released_v2_9"], 0)
            dsum["vs_released_v2_9"][d["vs_released_v2_9"]] += 1
    ident = dict(ident, diff=dsum)
    led = {"schema": LEDGER_SCHEMA, "method": METHOD, "extends": EXTENDS, "candidate": CANDIDATE,
           "base": A30.BASE_METHOD, "released": A30.RELEASED_METHOD, "released_default": False, "rows": rows,
           "waiting_pieces": WAITING, "integration_package": True}
    t307, t308 = A304.code_totals(l307), A304.code_totals(l308)
    moved = {k: {"v3_0_7": t307.get(k), "v3_0_8": t308.get(k)} for k in sorted(set(t307) | set(t308))
             if t307.get(k) != t308.get(k)}
    g = (inputs or {}).get("guard") or {}
    run = {"method": METHOD, "policy": POLICY_ID, "extends": EXTENDS, "candidate": CANDIDATE,
           "base_method": A30.BASE_METHOD, "released_method": A30.RELEASED_METHOD, "released_default": False,
           "rollback": ROLLBACK, "identity": ident, "pieces": PIECES, "piece_logs": logs,
           "inputs": {"pieces": [{k: pc.get(k) for k in ("piece", "item_code", "unit", "source", "scope",
                                                          "declared_totals", "line_group")}
                                 for pc in (inputs or {}).get("pieces") or ()],
                      "existence": (inputs or {}).get("existence"),
                      "guard": {k: g.get(k) for k in ("source", "evidence_file", "evidence_sha256", "conventions_file",
                                                      "conventions_sha256", "holding_checks", "recorded_checks",
                                                      "equal_value_rebase", "new_records")}},
           "totals_moved_by_code": moved, "waiting_pieces": WAITING,
           "evidence_status_counts": A302._count(r["evidence_status"] for r in rows)}
    files = {"V3_0_8_BOQ_LINES.json": BL.dumps(l308),
             "V3_0_8_BOQ_LINES.csv": A30._lines_csv(l308),
             "V3_0_8_INTEGRATION_LEDGER.json": A30._j(led),
             "V3_0_8_INTEGRATION_LEDGER.csv": ledger_csv(rows),
             "V3_0_8_DIFF.csv": A305._csv(diff, DIFF_CSV),
             "V3_0_8_RUN.json": A30._j(run)}
    for name, text in files.items():
        (out / name).write_text(text, encoding="utf-8")
    return sorted(files), ident, led


def policy_record():
    return {"method": METHOD, "extends": EXTENDS, "pieces": sorted(PIECES), "inputs_schema": INPUTS_SCHEMA,
            "released_default": False, "rollback": ROLLBACK}


__all__ = ["METHOD", "PIECES", "WAITING", "DEFAULT_GUARD_CLASS", "load_inputs", "record_changes", "existence_changes",
           "changes_for", "integrate", "ledger_rows", "diff_rows", "write", "InputsError"]
