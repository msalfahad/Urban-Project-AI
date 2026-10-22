"""ARCH_TAKEOFF_V3.0.3 (T-151): the SAME opt-in BOQ candidate as ARCH_TAKEOFF_V3.0 / V3.0.1 / V3.0.2
(engine.source.arch_v30, arch_v301, arch_v302), extended with the checker-verified steel hand ledgers of the columns, the
ground beams / straps and the suspended beams, and the evidence-text fix of the V3.0.2 Gate B defect D4. Not a new
method family and not the released default (owner management decision 2026-10-20 sections 2 and 5); rollback is
running the released ARCH_TAKEOFF_V2.9.

How it is built (tools/urban_boq_m9.py `arch --method ARCH_TAKEOFF_V3.0.3`):
  1. the run is the V3.0.2 candidate exactly: its V3_0_*, V3_0_1_* and V3_0_2_* files are written unchanged
     (arch_v30, arch_v301 and arch_v302 are not edited);
  2. the V3.0.3 pieces below propose changes of named lines of the V3.0.2 lines; a line two V3.0.3 pieces change is
     refused, and a line an earlier version changed is never changed again here, except by the fix of a named
     V3.0.2 Gate B defect (EVIDENCE_FIX, D4);
  3. the V3_0_3_* files are written beside them: every line outside the V3.0.3 rows is byte-identical to the V3.0.2
     line (asserted on every run: identity.vs_v3_0_2), and V3_0_3_DIFF.csv lists every line against V3.0.2 and
     against the released V2.9 + route G.

Pieces added in V3.0.3 (each carries a verifier MERGED verdict; the project inputs name the ledger file, its sha256,
the task, the merge commit and the checker run):
  COLUMN_STEEL        a column steel hand ledger by bar population (per column, storey and component)
  GROUND_SYSTEM_STEEL a ground-beam and strap steel hand ledger (per span / strap and bar mark)
  BEAM_STEEL          a suspended-beam steel hand ledger (per span and component)
     For each: route G's provisional steel lines of the ledger's scope (physical element + storeys) are SUPERSEDED
     (NOT_APPLICABLE_WITH_EVIDENCE, the route kg kept in the note), and one line per ledger record is added:
       RELEASED          -> SOURCE_DERIVED kg; evidence DRAWING-CONFIRMED (VERIFIED only where the record names the
                            checker run that re-measured it); NOT RELEASED (only the owner releases)
       HELD_RANGE        -> BOUNDED_EXPOSURE low .. high (readings listed); HELD
       HELD_DEFINED      -> BLOCKED_RFI, the defined kg shown in its inputs only (held: never added as quantity)
       HELD_LOWER_BOUND  -> BLOCKED_RFI, the lower bound shown in its inputs only (no upper bound printed)
       UNQUANTIFIED      -> BLOCKED_RFI; evidence UNKNOWN
     A RELEASED record whose bar count does not come from a printed schedule row of its own (schedule_row
     DUPLICATE_ROW / NOT_PRINTED / missing) is NEVER released: it becomes BLOCKED_RFI (SCHEDULE_ROW_NOT_PRINTED),
     its would-be kg kept in the inputs as information. Missing is never 0.
     Route lines of a member the drawing does not have (V3.0.1 NOT_PRESENT pieces, listed in the inputs or found in
     the V3.0.1 scope log) are superseded with that reason (they leave the candidate with their concrete).
  EVIDENCE_FIX        Gate B D4 of V3.0.2: footing top-layer steel lines that say the top bar ends are not drawn are
                      re-cited for the marks whose ends ARE drawn closed (the cited details); their held quantity does
                      not move; the end leg length is added as its own unquantified line per footing.

Rules: owner decision 2026-10-20 sections 2 and 5, WORKFLOW_CONTROLS 2026-10-21 section 5, URBAN-REBAR-NET-AND-
PROCUREMENT@v1 (kg = count x length x kg/m; never kg/m3; hooks / bends only from a detail), URBAN-COLUMN-HEIGHT-TO-
CONTROLLING-MEMBER@v1, Q-17 A, Q-71 (open), Q-74 (open), UP-QTY-STATUS-001 (held is a range or blocked, never 0).
Nothing here names a project, a sheet, a layer, a mark or a coordinate; every number comes from the run or the
project inputs.
"""

from __future__ import annotations

import copy
import csv
import hashlib
import io
import re

from engine.source import arch_v30 as A30
from engine.source import arch_v301 as A301
from engine.source import arch_v302 as A302

METHOD = "ARCH_TAKEOFF_V3.0.3"
EXTENDS = A302.METHOD
CANDIDATE = A30.METHOD                  # the candidate family this version extends (never a new method family)
POLICY_ID = "URBAN_BOQ_T151_ARCH_V3_0_3"
LEDGER_SCHEMA = "URBAN_V303_INTEGRATION_LEDGER_V1"
INPUTS_SCHEMA = "URBAN_V303_STEEL_LEDGERS_V1"
ROLLBACK = A30.ROLLBACK
STEEL_TRADE = "REINFORCEMENT"
REBAR_CODE = "STR.REBAR"
RULE_ID = "URBAN-REBAR-NET-AND-PROCUREMENT"
STEEL_PIECES = ("COLUMN_STEEL", "GROUND_SYSTEM_STEEL", "BEAM_STEEL")
STATES = ("RELEASED", "HELD_RANGE", "HELD_DEFINED", "HELD_LOWER_BOUND", "UNQUANTIFIED")
PRINTED = "PRINTED"
EVIDENCE_STATUS = A302.EVIDENCE_STATUS

PIECES = {
    "COLUMN_STEEL": {
        "module": "engine/source/arch_v303.py (typed hand-ledger records)", "policy": "COLUMN_STEEL_HAND_LEDGER_V1",
        "owner_rules": ["URBAN-REBAR-NET-AND-PROCUREMENT@v1", "URBAN-COLUMN-HEIGHT-TO-CONTROLLING-MEMBER@v1",
                        "Q-71 open (links per metre: readings A / B / C held)", "Q-17 A", "UP-QTY-STATUS-001"],
        "owner_manual_method": "manual QS take-off by column and storey: the printed schedule count x the storey "
                               "interval (bars through the joint) x d^2/162; links / laps / bends held where the "
                               "count or the detail is not printed",
        "drawing_method": "hand ledger typed from the column schedule and the column heights to the controlling "
                          "member; route G's provisional lines (profile heights + convention ties) superseded"},
    "GROUND_SYSTEM_STEEL": {
        "module": "engine/source/arch_v303.py (typed hand-ledger records)", "policy": "GROUND_SYSTEM_STEEL_HAND_LEDGER_V1",
        "owner_rules": ["URBAN-REBAR-NET-AND-PROCUREMENT@v1", "Q-71 open", "Q-74 open (strap length basis)",
                        "Q-21 C", "UP-QTY-STATUS-001"],
        "owner_manual_method": "manual QS take-off: ground-beam section class from the typical sections by length, "
                               "bars face to face on the plan; strap bars from the strap schedule over the strap "
                               "length (basis not set by the owner: Q-74, held over its readings)",
        "drawing_method": "hand ledger typed from the ground-beam plan, the typical ground-beam sections and the strap "
                          "schedule; route G's provisional strap lines (convention anchorage) superseded"},
    "BEAM_STEEL": {
        "module": "engine/source/arch_v303.py (typed hand-ledger records)", "policy": "BEAM_STEEL_HAND_LEDGER_V1",
        "owner_rules": ["URBAN-REBAR-NET-AND-PROCUREMENT@v1", "Q-71 open", "Q-61 C", "UP-QTY-STATUS-001"],
        "owner_manual_method": "manual QS take-off by beam and span: schedule bars over the clear span face to face; "
                               "support bars 0.22 Ln each side of the support face as the typical detail prints; "
                               "links, side bars, bar ends held where the count or the length is not printed",
        "drawing_method": "hand ledger typed from the simple / continuous beam schedules and the span register; "
                          "route G's provisional lines (clear span + convention anchorage) superseded"},
    "EVIDENCE_FIX": {
        "module": "engine/source/arch_v303.py", "policy": "FOOTING_TOP_END_CITATION_V1",
        "task": "T-151 (Gate B defect D4 of T-142)", "merge_commit": "this candidate",
        "verifier_run": "verifier 2026-10-22 00:30 UTC Gate B on V3.0.2: D4",
        "owner_rules": ["URBAN-REBAR-NET-AND-PROCUREMENT@v1 (hooks / bends only from a detail)", "Q-71 open",
                        "UP-QTY-STATUS-001"],
        "owner_manual_method": None,
        "owner_manual_note": "evidence text only: the held quantity of each line is unchanged",
        "drawing_method": "the held reason names the detail that draws the top bar ends closed; the leg length the "
                          "detail does not dimension is its own unquantified line"},
}
WAITING = {k: v for k, v in A302.WAITING.items() if k != "T-151"}
WAITING.update({
    "NECK_STEEL": "column steel in the necks (foundation band): no checker-verified ledger yet; route G lines kept",
    "SLAB_STEEL": "suspended-slab steel (T-152 MERGED 798e3b9): next extension of this candidate",
    "Q-74": "strap length basis: strap steel held over the readings until the owner answers",
})


class InputsError(ValueError):
    pass


# ================================================================================================ helpers
def _r(x, n=6):
    return None if x is None else round(float(x), n)


def _note(ln, text):
    ln["notes"] = (ln.get("notes") + "; " if ln.get("notes") else "") + text


def _change(piece, action, before, after, **kw):
    return dict({"piece": piece, "action": action, "before": before, "after": after}, **kw)


def _slug(s):
    return re.sub(r"[^A-Za-z0-9]+", "_", str(s)).strip("_").upper()[:48] or "X"


def _num(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool) and x == x


# ================================================================================================ project inputs
def load_inputs(doc, project_id=None):
    """URBAN_V303_STEEL_LEDGERS_V1 or None. Every ledger names its file sha256, the task, the merge commit and the
    checker run; every record its state, its quantity in that state and why it is held."""
    if doc is None:
        return None
    if doc.get("schema") != INPUTS_SCHEMA:
        raise InputsError(f"project inputs: schema must be {INPUTS_SCHEMA}")
    if project_id and doc.get("project") not in (None, project_id):
        raise InputsError(f"project inputs are for {doc.get('project')!r}, the run is {project_id!r}")
    seen = set()
    for lg in doc.get("ledgers") or ():
        p = lg.get("piece")
        if p not in STEEL_PIECES or p in seen:
            raise InputsError(f"ledger piece {p!r}: one of {STEEL_PIECES}, once each")
        seen.add(p)
        src = lg.get("source") or {}
        for k in ("file", "sha256", "task", "merge_commit", "checker_run"):
            if not src.get(k):
                raise InputsError(f"ledger {p}: source.{k} is required (a ledger without a checker MERGED verdict "
                                  "is not integrated)")
        sc = lg.get("scope") or {}
        if not sc.get("physical_element") or not sc.get("floors"):
            raise InputsError(f"ledger {p}: scope needs physical_element and floors")
        ids = set()
        for r in lg.get("records") or ():
            st = r.get("state")
            key = (r.get("element"), r.get("component"), r.get("part") or "")
            if not r.get("element") or not r.get("component") or key in ids:
                raise InputsError(f"ledger {p}: every record has a unique element / component / part: {key}")
            ids.add(key)
            if st not in STATES:
                raise InputsError(f"ledger {p} {key}: state {st!r} not one of {STATES}")
            if st == "RELEASED" and not (_num(r.get("kg")) and r["kg"] >= 0):
                raise InputsError(f"ledger {p} {key}: a RELEASED record carries kg >= 0")
            if st == "HELD_RANGE" and not (_num(r.get("low")) and _num(r.get("high")) and 0 <= r["low"] <= r["high"]):
                raise InputsError(f"ledger {p} {key}: a HELD_RANGE record carries 0 <= low <= high")
            if st == "HELD_DEFINED" and not _num(r.get("kg")):
                raise InputsError(f"ledger {p} {key}: a HELD_DEFINED record carries its defined kg")
            if st == "HELD_LOWER_BOUND" and not _num(r.get("low")):
                raise InputsError(f"ledger {p} {key}: a HELD_LOWER_BOUND record carries its lower bound")
            if st != "RELEASED" and not r.get("reasons"):
                raise InputsError(f"ledger {p} {key}: a held record names why it is held")
            if not r.get("floor"):
                raise InputsError(f"ledger {p} {key}: floor is required")
    ef = doc.get("evidence_fix")
    if ef is not None:
        for m, cite in (ef.get("closed_top_ends") or {}).items():
            if not cite:
                raise InputsError(f"evidence_fix.closed_top_ends.{m}: the detail that draws the ends is required")
        if not ef.get("source"):
            raise InputsError("evidence_fix.source (the verified task that read the details) is required")
    return doc


# ================================================================================================ steel ledgers
def _not_present(v301_log):
    """line ids of steel lines whose member V3.0.1 found NOT_PRESENT (ROUTE_G_SCOPE_V1) -> {line_id: reason}"""
    out = {}
    for x in (v301_log or {}).get("steel_stale") or ():
        if "(NOT_PRESENT)" in str(x.get("reads")):
            out[x["line_id"]] = x["reads"]
    return out


def ledger_record_line(pid, rev, docs, piece, src, r):
    """one BOQ line for one ledger record. -> (line, evidence status, totals contribution)"""
    from engine.source import boq_line as BL
    st = r["state"]
    reasons = list(r.get("reasons") or ())
    info = dict(r.get("info") or {})
    if st == "RELEASED" and r.get("schedule_row") != PRINTED:
        info.update(would_be_kg=_r(r["kg"]), schedule_row=r.get("schedule_row"))
        reasons = [f"SCHEDULE_ROW_NOT_PRINTED: the bar count of this record does not come from a printed schedule row "
                   f"of its own (schedule_row {r.get('schedule_row')!r}): held, never released or verified"] + reasons
        st = "UNQUANTIFIED"
    if st == "HELD_DEFINED":
        info.update(held_defined_kg=_r(r["kg"]))
    elif st == "HELD_LOWER_BOUND":
        info.update(lower_bound_kg=_r(r["low"]), upper_bound="NOT_ESTABLISHED")
    ev = {"RELEASED": "SOURCE_DERIVED", "HELD_RANGE": "BOUNDED_EXPOSURE"}.get(st, "BLOCKED_RFI")
    rng = None
    if st == "HELD_RANGE":
        rng = {"low": _r(r["low"]), "high": _r(r["high"]), "basis": r.get("range_basis") or "ledger readings"}
    eid = f"HL:{piece}:{r['element']}:{_slug(r['component'])}" + (f":{_slug(r['part'])}" if r.get("part") else "")
    rfi = None if ev == "SOURCE_DERIVED" else {"question": "; ".join(reasons)[:900], "unlocks": eid}
    dia = r.get("dia_mm")
    ln = BL.make_line(project_id=pid, revision_set_sha256=rev, item_code=REBAR_CODE, unit="kg", evidence_state=ev,
                      measured_net=_r(r["kg"]) if ev == "SOURCE_DERIVED" else None, bounded_range=rng,
                      element_id=eid, floor=r["floor"], physical_element=r.get("physical_element"),
                      subtrade=(r.get("physical_element") or piece) + (f" / {dia:g} mm" if _num(dia) else ""),
                      formula=r.get("formula") or ("held: " + "; ".join(reasons))[:400],
                      inputs=dict({"policy": PIECES[piece]["policy"], "ledger": src["file"],
                                   "ledger_sha256": src["sha256"], "element": r["element"], "mark": r.get("mark"),
                                   "component": r["component"], "part": r.get("part"), "printed": r.get("printed"),
                                   "count": r.get("count"), "length_m": r.get("length_m"),
                                   "readings": r.get("readings"), "reasons": reasons,
                                   "ledger_state": r["state"]}, **info),
                      documents=docs, geometry_source="SCHEDULE_ONLY",
                      geometry_confidence="TOLERANCE_CERTIFIED" if ev == "SOURCE_DERIVED" else "INFERRED_CANDIDATE",
                      rule_id=RULE_ID, rule_version="v1", material_state="SOURCE", rfi=rfi,
                      notes=f"{METHOD}: {piece.lower().replace('_', ' ')} by hand ledger ({src['task']}, "
                            f"MERGED {src['merge_commit']})")
    if st == "RELEASED":
        evs = "VERIFIED" if r.get("verified_by") else "DRAWING-CONFIRMED"
    elif st == "UNQUANTIFIED":
        evs = "UNKNOWN"
    else:
        evs = "HELD"
    t = {"released": r["kg"] if st == "RELEASED" else 0.0,
         "held_low": r["low"] if st == "HELD_RANGE" else 0.0, "held_high": r["high"] if st == "HELD_RANGE" else 0.0,
         "held_defined": r["kg"] if st == "HELD_DEFINED" else 0.0,
         "held_lower_bound": r["low"] if st == "HELD_LOWER_BOUND" else 0.0,
         "unquantified": 1 if st == "UNQUANTIFIED" else 0, "forced_held": 1 if info.get("would_be_kg") is not None
         else 0}
    return ln, evs, t


def steel_changes(inputs, lines, v301_log=None):
    """the steel ledgers of the project inputs on the V3.0.2 lines. -> (changes, logs)"""
    logs = []
    if not inputs:
        return [], [{"piece": p, "state": "NO_PROJECT_INPUT"} for p in STEEL_PIECES]
    pid, rev, docs = A302._proj(lines)
    gone = _not_present(v301_log)
    gone.update({k: v for k, v in (inputs.get("not_present_lines") or {}).items()})
    have = {ln["line_id"] for ln in lines}
    changes = []
    done = {lg["piece"] for lg in inputs.get("ledgers") or ()}
    for lg in inputs.get("ledgers") or ():
        piece, src, sc = lg["piece"], lg["source"], lg["scope"]
        floors = set(sc["floors"])
        ref = lg.get("drawing_reference") or src["file"]
        verif = {"task": src["task"], "merge_commit": src["merge_commit"], "verifier_run": src["checker_run"],
                 "ledger": src["file"], "ledger_sha256": src["sha256"]}
        old = [ln for ln in lines if ln["item_code"] == REBAR_CODE and ln["trade"] == STEEL_TRADE
               and str(ln.get("physical_element")) == sc["physical_element"]
               and (ln.get("location") or {}).get("floor") in floors]
        log = {"piece": piece, "state": "RUN", "ledger": src["file"], "ledger_sha256": src["sha256"],
               "scope": sc, "route_lines": len(old), "route_kg": 0.0, "route_by_floor": {}, "by_floor": {},
               "superseded_not_present": 0, "evidence_status": {}}
        for o in old:
            fl = o["location"]["floor"]
            q = o.get("measured_net") or 0.0
            log["route_kg"] += q
            rb = log["route_by_floor"].setdefault(fl, {"lines": 0, "kg": 0.0})
            rb["lines"] += 1
            rb["kg"] += q
            after = copy.deepcopy(o)
            why = gone.get(o["line_id"])
            after.update(evidence_state="NOT_APPLICABLE_WITH_EVIDENCE", measured_net=None, bounded_range=None, rfi=None)
            if why:
                after["notes"] = (f"{METHOD}: NOT_PRESENT - the member is not drawn ({why}; V3.0.1 ROUTE_G_SCOPE_V1): "
                                  f"its steel leaves the candidate with its concrete; was {_r(o.get('measured_net'))} kg")
                log["superseded_not_present"] += 1
            else:
                after["notes"] = (f"{METHOD}: SUPERSEDED - route G provisional steel ({_r(o.get('measured_net'))} kg) "
                                  f"is replaced by the {src['task']} hand ledger lines of {sc['physical_element']} "
                                  f"{fl} (MERGED {src['merge_commit']})")
            changes.append(_change(piece, "REPLACE", o, after, drawing_reference=ref, held=[], downstream=[],
                                   verification=verif, evidence_status="DRAWING-CONFIRMED"))
        for r in lg.get("records") or ():
            r = dict(r, physical_element=r.get("physical_element") or sc["physical_element"])
            if r["floor"] not in floors:
                raise InputsError(f"ledger {piece}: record {r['element']} floor {r['floor']} outside the scope {floors}")
            ln, evs, t = ledger_record_line(pid, rev, docs, piece, src, r)
            if ln["line_id"] in have:
                raise ValueError(f"{METHOD}: ledger line {r['element']} {r['component']} repeats a V3.0.2 line id")
            held = []
            if ln["evidence_state"] != "SOURCE_DERIVED":
                held = [{"what": f"{r['element']} {r['component']}", "why": ln["rfi"]["question"] if ln.get("rfi")
                         else None, "range_kg": [ln["bounded_range"]["low"], ln["bounded_range"]["high"]]
                         if ln.get("bounded_range") else None}]
            changes.append(_change(piece, "ADD", None, ln, drawing_reference=r.get("printed") or ref, held=held,
                                   downstream=list(r.get("downstream") or ()), verification=verif,
                                   evidence_status=evs))
            b = log["by_floor"].setdefault(r["floor"], {k: 0.0 for k in ("released", "held_low", "held_high",
                                                                          "held_defined", "held_lower_bound")} |
                                           {"unquantified": 0, "forced_held": 0, "lines": 0})
            b["lines"] += 1
            for k, v in t.items():
                b[k] += v
            log["evidence_status"][evs] = log["evidence_status"].get(evs, 0) + 1
        log["route_kg"] = _r(log["route_kg"])
        for d in (log["route_by_floor"], log["by_floor"]):
            for v in d.values():
                for k in list(v):
                    if isinstance(v[k], float):
                        v[k] = _r(v[k])
        tot = {}
        for v in log["by_floor"].values():
            for k, x in v.items():
                tot[k] = tot.get(k, 0) + x
        log["totals"] = {k: _r(v) if isinstance(v, float) else v for k, v in tot.items()}
        dec = lg.get("declared_totals") or {}
        for k, v in dec.items():
            if k in log["totals"] and abs((log["totals"][k] or 0) - v) > 0.006:
                raise ValueError(f"{METHOD}: ledger {piece} {k} {log['totals'][k]} != the ledger's own total {v}")
        log["declared_totals"] = dec
        logs.append(log)
    for p in STEEL_PIECES:
        if p not in done:
            logs.append({"piece": p, "state": "NO_PROJECT_INPUT"})
    return changes, logs


# ================================================================================================ EVIDENCE_FIX (D4)
NOT_DRAWN = "END_TREATMENT_NOT_DRAWN"


def evidence_fix_changes(inputs, lines):
    """D4: the footing top-layer steel lines (V3.0.2) whose reason says the top bar ends are not drawn, for a mark the
    inputs list with the detail that draws them closed: the reason re-cited (quantity unchanged) + one unquantified
    end-leg line per footing. -> (changes, log)"""
    from engine.source import boq_line as BL
    log = {"piece": "EVIDENCE_FIX", "state": "NOT_RUN", "lines": []}
    ef = (inputs or {}).get("evidence_fix")
    if ef is None:
        log["state"] = "NO_PROJECT_INPUT"
        return [], log
    closed = ef.get("closed_top_ends") or {}
    pid, rev, docs = A302._proj(lines)
    changes, legs = [], {}
    for ln in lines:
        inp = (ln.get("calculation") or {}).get("inputs") or {}
        if ln["item_code"] != REBAR_CODE or ln.get("physical_element") != "FOOTINGS":
            continue
        rs = inp.get("reasons") or []
        if not any(str(x).startswith(NOT_DRAWN) for x in rs) or "TOP" not in str(inp.get("component") or "").upper():
            continue
        mark = inp.get("mark")
        if mark not in closed:
            log["lines"].append({"line_id": ln["line_id"], "mark": mark, "change": "NONE (ends not drawn: kept)"})
            continue
        after = copy.deepcopy(ln)
        new = [x for x in rs if not str(x).startswith(NOT_DRAWN)] + [
            f"END_TREATMENT_DRAWN_CLOSED: the top bar ends are drawn closed ({closed[mark]}); the leg length is not "
            f"dimensioned: held as its own unquantified line"]
        after["calculation"] = dict(after["calculation"], inputs=dict(inp, reasons=new))
        if after.get("rfi"):
            after["rfi"] = dict(after["rfi"], question="; ".join(new)[:900])
        _note(after, f"{METHOD}: Gate B D4 - top bar end citation corrected ({ef['source']}); quantity unchanged")
        if A30._qty(after) != A30._qty(ln):
            raise ValueError(f"{METHOD}: D4 must not move a quantity ({ln['line_id']})")
        changes.append(_change("EVIDENCE_FIX", "REPLACE", ln, after, drawing_reference=closed[mark], held=[{
            "what": f"footing steel {mark} {inp.get('component')}", "why": "; ".join(new)}], downstream=[],
            fixes_v3_0_2="Gate B defect D4 (verifier 2026-10-22 00:30 UTC)", evidence_status="HELD"))
        eid0 = str(ln["location"]["element_id"])            # FRP:<occurrence>:<component>
        occ = eid0[4:].rsplit(":", 1)[0] if eid0.startswith("FRP:") and eid0.count(":") >= 2 else str(mark)
        legs.setdefault(occ, (mark, ln))
        log["lines"].append({"line_id": ln["line_id"], "mark": mark, "component": inp.get("component"),
                             "change": "RE-CITED"})
    for occ, (mark, ln) in sorted(legs.items()):
        eid = f"FRP:{occ}:TOP_END_LEGS"
        q = (f"TOP_END_LEG_LENGTH_NOT_DIMENSIONED: footing {mark} top bars are drawn closed ({closed[mark]}); the "
             f"leg length is not printed (URBAN-REBAR-NET-AND-PROCUREMENT@v1: bends only from a dimensioned detail)")
        add = BL.make_line(project_id=pid, revision_set_sha256=rev, item_code=REBAR_CODE, unit="kg",
                           evidence_state="BLOCKED_RFI", element_id=eid, floor=ln["location"]["floor"],
                           physical_element="FOOTINGS", subtrade="FOOTINGS", formula="held: " + q,
                           inputs={"policy": PIECES["EVIDENCE_FIX"]["policy"], "mark": mark, "component": "TOP_END_LEGS",
                                   "reasons": [q]}, documents=docs, geometry_source="SCHEDULE_ONLY",
                           geometry_confidence="INFERRED_CANDIDATE", rule_id=RULE_ID, rule_version="v1",
                           material_state="SOURCE", rfi={"question": q, "unlocks": eid},
                           notes=f"{METHOD}: Gate B D4 - closed top bar ends, leg length held")
        changes.append(_change("EVIDENCE_FIX", "ADD", None, add, drawing_reference=closed[mark],
                               held=[{"what": f"footing {mark} top end legs", "why": q}], downstream=[],
                               evidence_status="UNKNOWN"))
    log["state"] = "RUN"
    log["source"] = ef["source"]
    log["end_leg_lines"] = len(legs)
    return changes, log


# ================================================================================================ integrate / ledger
def integrate(base_lines, v30_changes, v301_changes, v302_changes, v303_changes):
    """-> (V3.0.2 lines, V3.0.3 lines, identity). Every line outside the V3.0.3 rows is byte-identical to the
    V3.0.2 line; a line two V3.0.3 pieces change, or a line an earlier version changed (other than a named V3.0.2
    defect fix), is refused."""
    from engine.source import boq_line as BL
    l301, l302, _i = A302.integrate(base_lines, v30_changes, v301_changes, v302_changes)
    earlier = {}
    for c in list(v301_changes) + list(v302_changes):
        if c["after"] is not None:
            earlier[c["after"]["line_id"]] = c["action"]
    ids = [ln["line_id"] for ln in l302]
    sid = set(ids)
    rep, adds = {}, []
    for c in v303_changes:
        if c["action"] == "REPLACE":
            lid = c["before"]["line_id"]
            if lid in rep:
                raise ValueError(f"{METHOD}: line {lid} changed by two V3.0.3 pieces")
            if lid in earlier and not c.get("fixes_v3_0_2"):
                raise ValueError(f"{METHOD}: line {lid} was changed by an earlier version ({earlier[lid]}); V3.0.3 "
                                 "changes such a line only to fix a named V3.0.2 defect")
            rep[lid] = c["after"]
        elif c["action"] == "ADD":
            adds.append(c["after"])
        else:
            raise ValueError(f"{METHOD}: action {c['action']}")
    if rep.keys() - sid:
        raise ValueError(f"{METHOD}: a change names a line the V3.0.2 run does not have")
    out = [rep.get(ln["line_id"], ln) for ln in l302]
    for a in adds:
        if a["line_id"] in sid:
            raise ValueError(f"{METHOD}: an added line repeats a V3.0.2 line id")
        out.append(a)
    if len({ln["line_id"] for ln in out}) != len(out):
        raise ValueError(f"{METHOD}: a BOQ line id appears twice")
    for ln in out:
        BL.validate(ln)
    touched = set(rep) | {a["line_id"] for a in adds}
    by302 = {ln["line_id"]: ln for ln in l302}
    outside = [ln for ln in out if ln["line_id"] not in touched]
    bad = [ln["line_id"] for ln in outside if A30.line_sha(by302[ln["line_id"]]) != A30.line_sha(ln)]
    if bad or len(outside) + len(rep) != len(l302):
        raise ValueError(f"{METHOD}: {len(bad)} line(s) outside the V3.0.3 rows differ from {EXTENDS}")
    ident = {"v3_0_2_lines": len(l302), "v3_0_3_lines": len(out), "v3_0_3_rows": len(v303_changes),
             "replaced": len(rep), "added": len(adds), "outside_rows": len(outside),
             "outside_rows_identical_to_v3_0_2": len(outside),
             "outside_rows_sha256": hashlib.sha256("".join(A30.line_sha(x) for x in outside).encode()).hexdigest()}
    return l302, out, ident


def ledger_rows(changes, released_lines=None):
    rel = {A30._key(ln): ln for ln in released_lines or ()}
    rows = []
    for c in changes:
        ref = c["after"] if c["before"] is None else c["before"]
        b302 = A30._qty(c["before"]) if c["before"] is not None else dict(A30._qty(None), state="NOT_IN_V3_0_2")
        aft = A30._qty(c["after"])
        b29 = None
        if released_lines is not None:
            b29 = A30._qty(rel[A30._key(ref)]) if A30._key(ref) in rel else dict(A30._qty(None),
                                                                                 state="NOT_IN_RELEASED")
        d = None
        if b302["value"] is not None and aft["value"] is not None:
            d = {"delta": _r(aft["value"] - b302["value"]),
                 "pct": _r(100.0 * (aft["value"] - b302["value"]) / b302["value"], 3) if b302["value"] else None}
        p = PIECES[c["piece"]]
        loc = ref.get("location") or {}
        ver = c.get("verification") or {k: p.get(k) for k in ("task", "merge_commit", "verifier_run")}
        rows.append({"version": METHOD, "piece": c["piece"], "action": c["action"], "line_id": ref["line_id"],
                     "after_line_id": c["after"]["line_id"], "item_code": ref["item_code"], "floor": loc.get("floor"),
                     "room_id": loc.get("room_id"), "element_id": c["after"]["location"].get("element_id"),
                     "unit": c["after"]["unit"], "before_released_v2_9": b29, "before_v3_0_2": b302,
                     "after_v3_0_3": aft, "change": d, "evidence_status": c.get("evidence_status") or "HELD",
                     "release_status": "NOT RELEASED", "drawing_reference": c.get("drawing_reference"),
                     "owner_manual_method": p.get("owner_manual_method") or p.get("owner_manual_note"),
                     "drawing_method": p["drawing_method"], "owner_rules": p["owner_rules"],
                     "verification": dict(ver, module=p["module"], policy=p["policy"]),
                     "held": c.get("held") or [], "downstream": c.get("downstream") or [], "rollback": ROLLBACK})
    return rows


LEDGER_CSV = ("version", "piece", "action", "line_id", "after_line_id", "item_code", "floor", "element_id", "unit",
              "v2_9", "v3_0_2", "v3_0_3", "delta", "pct", "evidence_status", "release_status", "drawing_reference",
              "verification", "held")


def _csv(rows, cols):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=cols, lineterminator="\n", extrasaction="ignore")
    w.writeheader()
    w.writerows(rows)
    return buf.getvalue()


def ledger_csv(rows):
    return _csv([{"version": r["version"], "piece": r["piece"], "action": r["action"], "line_id": r["line_id"],
                  "after_line_id": r["after_line_id"], "item_code": r["item_code"], "floor": r["floor"],
                  "element_id": r["element_id"], "unit": r["unit"], "v2_9": A302._q(r["before_released_v2_9"]),
                  "v3_0_2": A302._q(r["before_v3_0_2"]), "v3_0_3": A302._q(r["after_v3_0_3"]),
                  "delta": (r["change"] or {}).get("delta"), "pct": (r["change"] or {}).get("pct"),
                  "evidence_status": r["evidence_status"], "release_status": r["release_status"],
                  "drawing_reference": r["drawing_reference"],
                  "verification": f"{r['verification'].get('task')} {r['verification'].get('merge_commit')}",
                  "held": "; ".join(str(h.get("why") or h.get("what")) for h in r["held"])[:600]} for r in rows],
                LEDGER_CSV)


DIFF_CSV = ("line_id", "item_code", "floor", "element_id", "unit", "vs_v3_0_2", "vs_released_v2_9", "v2_9", "v3_0_2",
            "v3_0_3")


def diff_rows(l302, l303, released_lines=None):
    b302 = {ln["line_id"]: ln for ln in l302}
    rel = {A30._key(ln): ln for ln in released_lines or ()}
    out = []
    for ln in l303:
        o = b302.get(ln["line_id"])
        vs = "ADDED" if o is None else ("SAME" if A30.line_sha(o) == A30.line_sha(ln) else "CHANGED")
        r = rel.get(A30._key(ln)) if released_lines is not None else None
        vs29 = None if released_lines is None else ("NOT_IN_RELEASED" if r is None else
                                                    ("SAME_QUANTITY" if A30._qty(r) == A30._qty(ln) else
                                                     "QUANTITY_DIFFERS"))
        out.append({"line_id": ln["line_id"], "item_code": ln["item_code"], "floor": ln["location"].get("floor"),
                    "element_id": ln["location"].get("element_id"), "unit": ln["unit"], "vs_v3_0_2": vs,
                    "vs_released_v2_9": vs29, "v2_9": A302._q(A30._qty(r)) if r else "",
                    "v3_0_2": A302._q(A30._qty(o)) if o else "", "v3_0_3": A302._q(A30._qty(ln))})
    return out


def steel_totals(lines):
    """reinforcement per physical element and floor of a line set: released kg, held range, unquantified lines."""
    out = {}
    for ln in lines:
        if ln["item_code"] != REBAR_CODE or ln["evidence_state"] == "NOT_APPLICABLE_WITH_EVIDENCE":
            continue
        k = out.setdefault(f"{ln.get('physical_element')}|{ln['location'].get('floor')}",
                           {"lines": 0, "value_kg": 0.0, "held_low_kg": 0.0, "held_high_kg": 0.0, "blocked_lines": 0})
        k["lines"] += 1
        q = A30._qty(ln)
        if q["value"] is not None:
            k["value_kg"] += q["value"]
        elif q["low"] is not None:
            k["held_low_kg"] += q["low"]
            k["held_high_kg"] += q["high"]
        else:
            k["blocked_lines"] += 1
    return {k: {a: _r(b) if isinstance(b, float) else b for a, b in v.items()} for k, v in sorted(out.items())}


def write(out, base_lines, v30_changes, v301_changes, v302_changes, v303_changes, logs, inputs, released_lines=None):
    """the V3_0_3_* files beside the V3_0_2_* files. -> (file names, identity, ledger)."""
    from pathlib import Path
    from engine.source import boq_line as BL
    out = Path(out)
    l302, l303, ident = integrate(base_lines, v30_changes, v301_changes, v302_changes, v303_changes)
    rows = ledger_rows(v303_changes, released_lines)
    diff = diff_rows(l302, l303, released_lines)
    dsum = {}
    for d in diff:
        dsum.setdefault("vs_v3_0_2", {}).setdefault(d["vs_v3_0_2"], 0)
        dsum["vs_v3_0_2"][d["vs_v3_0_2"]] += 1
        if d["vs_released_v2_9"] is not None:
            dsum.setdefault("vs_released_v2_9", {}).setdefault(d["vs_released_v2_9"], 0)
            dsum["vs_released_v2_9"][d["vs_released_v2_9"]] += 1
    ident = dict(ident, diff=dsum)
    led = {"schema": LEDGER_SCHEMA, "method": METHOD, "extends": EXTENDS, "candidate": CANDIDATE,
           "base": A30.BASE_METHOD, "released": A30.RELEASED_METHOD, "released_default": False, "rows": rows,
           "waiting_pieces": WAITING, "integration_package": True}
    down = [dict(d, from_line=r["line_id"], piece=r["piece"]) for r in rows for d in r["downstream"]]
    run = {"method": METHOD, "policy": POLICY_ID, "extends": EXTENDS, "candidate": CANDIDATE,
           "base_method": A30.BASE_METHOD, "released_method": A30.RELEASED_METHOD, "released_default": False,
           "rollback": ROLLBACK, "identity": ident, "pieces": PIECES, "v3_0_2_pieces": A302.PIECES,
           "piece_logs": logs, "inputs_ledgers": [{k: lg.get(k) for k in ("piece", "source", "scope",
                                                                           "declared_totals")}
                                                  for lg in (inputs or {}).get("ledgers") or ()],
           "steel_v3_0_2": steel_totals(l302), "steel_v3_0_3": steel_totals(l303), "waiting_pieces": WAITING,
           "evidence_status_counts": A302._count(r["evidence_status"] for r in rows)}
    files = {"V3_0_3_BOQ_LINES.json": BL.dumps(l303),
             "V3_0_3_BOQ_LINES.csv": A30._lines_csv(l303),
             "V3_0_3_INTEGRATION_LEDGER.json": A30._j(led),
             "V3_0_3_INTEGRATION_LEDGER.csv": ledger_csv(rows),
             "V3_0_3_DIFF.csv": _csv(diff, DIFF_CSV),
             "V3_0_3_DOWNSTREAM.json": A30._j({"method": METHOD, "rows": down}),
             "V3_0_3_RUN.json": A30._j(run)}
    for name, text in files.items():
        (out / name).write_text(text, encoding="utf-8")
    return sorted(files), ident, led


def policy_record():
    return {"method": METHOD, "extends": EXTENDS, "pieces": sorted(PIECES), "inputs_schema": INPUTS_SCHEMA,
            "released_default": False, "rollback": ROLLBACK}


__all__ = ["METHOD", "PIECES", "WAITING", "load_inputs", "steel_changes", "evidence_fix_changes", "integrate",
           "ledger_rows", "diff_rows", "steel_totals", "write", "InputsError"]
