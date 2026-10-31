"""ARCH_TAKEOFF_V3.0.33 (T-397): the SAME opt-in BOQ candidate as ARCH_TAKEOFF_V3.0 .. V3.0.32 (engine.source.arch_v30,
arch_v301 .. arch_v3032), with ONE piece, STRUCTURAL_CORRECTIONS: the structural-concrete corrections that Checker-
verified reconciliations proposed for lane I, applied line id by line id:

  HELD_BOUND      a HELD line whose held bound covered more than its element: the bound restated to the element's
                  own measured pieces (T-391 F1: the held ground-slab cell's bound covers its slab panels only, not the
                  lift shaft and strips round it). The line stays HELD; its range is a range, never a value.
  GAP_RESTORE     a valued line that carried a deduction no drawn cell supports (T-392: the T-146 'ring overlap' of a
                  fitted band set, R-T392-1) or that ran past / short of its carrier face (R-T392-2, DOUBLE and GAP
                  reported apart): the line restated to its drawn cell. Same state; only the quantity moves.
  CONFLICT_RANGE  a valued line whose printed and drawn sections disagree (R-COLUMN-EVIDENCE-1, T-256 / T-394 P1):
                  the single figure at one reading becomes a BOUNDED range between the two readings (never a mid
                  value, never one end), with the designer item named.
  MISSING_HELD    an element the drawings show that no candidate line carried (T-394 P2: the lift pit walls): a NEW
                  line, HELD BLANK (never 0), its drawing-confirmed plan figure beside, what holds it named.

Every value comes from the inputs (each a Checker-merged ledger pinned by sha256); this module types none. Every line
outside the rows is byte-identical to V3.0.32; inside a row only quantity, state, range, rfi, calculation and notes
change (asserted). Totals may move only in the structural concrete codes the rows name (asserted). Files:
V3_0_33_BOQ_LINES.json / .csv, V3_0_33_INTEGRATION_LEDGER.json / .csv, V3_0_33_DIFF.csv, V3_0_33_RUN.json.
Nothing here names a project, a sheet, a layer or a coordinate.

R-T397-1 (every villa): a lane I correction moves only the line id it binds, and only when the line still stands in
the candidate exactly as the verified ledger read it (item, element, state, figure: a stale binding stops); a held
bound is a range [0, the element's own pieces], never a value; a printed-vs-drawn conflict is the range of the two
readings with the candidate's figure at one end (else stop); a GAP restore never moves a line by more than the named
cause (else stop); a missing element is a HELD BLANK line with its plan beside, never 0 and never a guessed depth.
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
from engine.source import arch_v3032 as A3032

DEFAULT_GUARD_CLASS = "TOOLING"          # T-212: re-books checker-merged ledgers; adds no default value
METHOD = "ARCH_TAKEOFF_V3.0.33"
EXTENDS = A3032.METHOD
CANDIDATE = A30.METHOD
POLICY_ID = "URBAN_BOQ_T397_ARCH_V3_0_33"
INPUTS_SCHEMA = "URBAN_V3033_INPUTS_V1"
LEDGER_SCHEMA = "URBAN_V3033_INTEGRATION_LEDGER_V1"
ROLLBACK = A30.ROLLBACK
InputsError = A3031.InputsError
_r = A3018._r
_fmt = A3030._fmt
RULE_ID, RULE_VERSION = "R-T397-1", "T-397"
PIECE = "STRUCTURAL_CORRECTIONS"
REC_KEY = "structural_corrections_v3033"
ACTIONS = ("HELD_BOUND", "GAP_RESTORE", "CONFLICT_RANGE", "MISSING_HELD")
CONCRETE = ("STR.CONC.GROUND_SLAB", "STR.CONC.BEAM", "STR.CONC.COLUMN", "STR.CONC.LIFT")
HELD_STATES = ("BLOCKED_RFI", "BOUNDED_EXPOSURE")
VALUED_STATES = ("MEASURED", "SOURCE_DERIVED", "PROVISIONAL")
TOL = 1e-6
ROW_KEYS = ("evidence_state", "measured_net", "bounded_range", "rfi", "notes", "calculation", "gross")

PIECES = {
    PIECE: {
        "module": "engine/source/arch_v3033.py (structural concrete corrections from Checker-verified "
                  "reconciliations: T-391 F1 held bound, T-392 GAP / DOUBLE restores, T-394 P1 CONFLICT ranges "
                  "(per-member readings of T-256), T-394 P2 the missing lift-pit wall line HELD)",
        "policy": "STRUCTURAL_CORRECTIONS_V1", "rule_id": RULE_ID, "rule_version": RULE_VERSION,
        "owner_rules": ["Q-61 C (member by member)", "UP-QTY-STATUS-001 (held is blank, never 0)",
                        "R-T391-5 (a held cell's bound covers its slab panels only)",
                        "R-T392-1 (a neighbour-overlap deduction only against drawn cells)",
                        "R-T392-2 (a member to its carrier face; beyond / short reported apart)",
                        "R-COLUMN-EVIDENCE-1 (T-256: a printed-vs-drawn section is a range, never the schedule end)",
                        "R-T394-6 (a ring through columns owns its net band only)",
                        "WORKFLOW_CONTROLS 2026-10-21 s.4 / s.5; ERS 2026-10-22 s.2 - s.4"],
        "owner_manual_method": "owner Q-61 C: every structural member measured member by member to its drawn faces "
                               "(slab panel between the beam faces, beam to the carrier face, column to its drawn "
                               "outline x storey height); an element whose dimension the drawings do not print stays "
                               "HELD (never a typical value)",
        "drawing_method": "per member on the ST sheets: own polygonisation of the ground-beam plan (T-391, 180 faces), "
                          "the GF-roof beam cells to their carrier faces (T-392), the 15 column outlines against the "
                          "schedule band (T-256 / T-394), the lift ring S-BW outer less inner less the four lift "
                          "column pieces (T-394 R-T394-6)"},
}
WAITING = dict(A3032.WAITING)
WAITING.update({
    "LIFT_PIT_DEPTH_D43": "lift pit depth: 'as per lift manufacturer' (ST p.14, designer D-43): the pit-wall line is "
                          "HELD blank, plan ring net beside; pit base slab / membrane are not this line (T-353)",
    "COLUMN_SECTION_D16_D63": "15 column sections printed-vs-drawn CONFLICT (D-16, D-63, column-band item): BOUNDED "
                              "ranges until the designer answers",
    "GS_HELD_CELL_T042": "ground-slab cell with the lift-shaft corner columns read as free columns (T-042): HELD, "
                         "bound 0 .. its own slab panels",
    "BEAM_JOINT_HEAD_T395": "T-394 P3 joint + head 3.774 m3 and the T-395 beam result: not in this version",
})


# ================================================================================================ inputs
def _need(s, keys, where):
    for k in keys:
        if s.get(k) in (None, ""):
            raise InputsError(f"{where}: {k} missing")


def _pos(x, where, zero_ok=False):
    if not isinstance(x, (int, float)) or isinstance(x, bool) or x != x or x < 0 or (x == 0 and not zero_ok):
        raise InputsError(f"{where}: {x!r} is not a positive figure (held is BLANK, never 0)")
    return float(x)


def _print_m2(txt, unit, where):
    """'GR 25x50' with unit cm, '200x500 mm' with unit mm -> m2 (the section as printed / drawn)."""
    import re
    m = re.search(r"(\d+(?:\.\d+)?)\s*x\s*(\d+(?:\.\d+)?)", str(txt))
    if not m:
        raise InputsError(f"{where}: section print {txt!r} is not 'a x b'")
    k = {"cm": 1e-2, "mm": 1e-3}[unit]
    return float(m.group(1)) * k * float(m.group(2)) * k


def load_inputs(doc, project_id=None):
    """URBAN_V3033_INPUTS_V1 -> the validated doc. {"schema", "project_id", "sources": [{"task", "file", "sha256",
    "merge_commit", "checker_run"}], "rows": [{"action", "line_id" (not for MISSING_HELD), "expect": {"item_code",
    "element_id", "evidence_state", "measured_net" | "high"}, "source_tasks": [...], "evidence_status", "cause", ...}]}"""
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
    rows, seen = [], set()
    for i, r in enumerate(doc.get("rows") or ()):
        act = r.get("action")
        where = f"row {i} {act} {r.get('line_id') or r.get('element_id')}"
        if act not in ACTIONS:
            raise InputsError(f"{where}: action {act!r}")
        _need(r, ("cause", "evidence_status"), where)
        if not r.get("source_tasks"):
            raise InputsError(f"{where}: no merged source named")
        for t in r["source_tasks"]:
            if t not in srcs:
                raise InputsError(f"{where}: no merged source for {t!r}")
        if act == "MISSING_HELD":
            _need(r, ("item_code", "element_id", "floor", "physical_element", "held_reason", "beside_unit"), where)
            _pos(r.get("beside"), f"{where} beside")
            if r.get("value") is not None:
                raise InputsError(f"{where}: a missing element is added HELD BLANK, never with a value")
            if r["item_code"] not in CONCRETE:
                raise InputsError(f"{where}: {r['item_code']} is not a structural concrete code of this piece")
            key = ("NEW", r["item_code"], r["element_id"], r["floor"])
        else:
            _need(r, ("line_id",), where)
            e = r.get("expect") or {}
            _need(e, ("item_code", "floor", "evidence_state"), f"{where} expect")
            if e["item_code"] not in CONCRETE:
                raise InputsError(f"{where}: {e['item_code']} is not a structural concrete code of this piece")
            key = r["line_id"]
            if act == "HELD_BOUND":
                if e["evidence_state"] not in HELD_STATES:
                    raise InputsError(f"{where}: a held bound is restated on a HELD line only")
                hi = _pos(r.get("high"), f"{where} high")
                if _pos(r.get("low"), f"{where} low", zero_ok=True) > hi:
                    raise InputsError(f"{where}: low above high")
                _pos(e.get("high"), f"{where} expect high")
                if hi > e["high"] + TOL:
                    raise InputsError(f"{where}: the new bound {hi} is above the old {e['high']} (a bound fix "
                                      f"removes what is not the element, never adds)")
            elif act == "GAP_RESTORE":
                if e["evidence_state"] not in VALUED_STATES:
                    raise InputsError(f"{where}: a GAP restore moves a valued line only")
                b, a = _pos(e.get("measured_net"), f"{where} before"), _pos(r.get("value"), f"{where} value")
                named = r.get("named_terms") or []
                if not named:
                    raise InputsError(f"{where}: a restore names its cause terms (never 'rounding')")
                for t in named:
                    _need(t, ("name", "m3", "kind"), f"{where} term")
                    if t["kind"] not in ("GAP", "DOUBLE", "LEDGER_PRINT"):
                        raise InputsError(f"{where}: term kind {t['kind']!r}")
                net = sum(t["m3"] if t["kind"] != "DOUBLE" else -t["m3"] for t in named)
                if abs((a - b) - net) > 1e-5:
                    raise InputsError(f"{where}: after - before {_r(a - b)} is not the named terms {_r(net)} "
                                      f"(GAP + LEDGER_PRINT - DOUBLE; never netted silently)")
            elif act == "CONFLICT_RANGE":
                if e["evidence_state"] not in VALUED_STATES:
                    raise InputsError(f"{where}: a conflict range replaces a valued single figure")
                q = _pos(e.get("measured_net"), f"{where} before")
                rd = r.get("readings") or {}
                if set(rd) != {"SCHEDULE", "DRAWN"}:
                    raise InputsError(f"{where}: a printed-vs-drawn conflict carries both readings")
                vals = [_pos(v, f"{where} reading {k}") for k, v in rd.items()]
                if abs(vals[0] - vals[1]) <= TOL:
                    raise InputsError(f"{where}: equal readings are not a conflict")
                if min(abs(q - v) for v in vals) > TOL:
                    raise InputsError(f"{where}: the candidate figure {q} is at neither reading {rd} (stale binding)")
                _need(r, ("designer_item", "schedule_print", "drawn_print"), where)
                h = _pos(r.get("height_m"), f"{where} height")
                want = {"SCHEDULE": _print_m2(r["schedule_print"], "cm", where) * h,
                        "DRAWN": _print_m2(r["drawn_print"], "mm", where) * h}
                for k, v in want.items():
                    if abs(rd[k] - v) > 1e-6:
                        raise InputsError(f"{where}: reading {k} {rd[k]} is not its print x height {_r(v)} (units: "
                                          f"the schedule in cm, the outline in mm, the height in m)")
        if key in seen:
            raise InputsError(f"{where}: line in two rows (one line, one row)")
        seen.add(key)
        rows.append(r)
    if not rows:
        raise InputsError("no correction row in the inputs")
    return dict(doc, _sources=srcs, _rows=rows)


# ================================================================================================ lines
def _rec(srcs, **kw):
    return dict({"policy": PIECES[PIECE]["policy"], "tasks": [s["task"] for s in srcs],
                 "ledgers": [s["file"] for s in srcs], "ledger_sha256": [s["sha256"] for s in srcs],
                 "merge_commits": [s["merge_commit"] for s in srcs], "checker_runs": [s["checker_run"] for s in srcs],
                 "rule_id": RULE_ID, "rule_version": RULE_VERSION, "release_status": "NOT RELEASED"}, **kw)


def _ver(srcs):
    return {"task": "+".join(s["task"] for s in srcs), "merge_commit": srcs[0]["merge_commit"],
            "merge_commits": [s["merge_commit"] for s in srcs], "verifier_run": "; ".join(s["checker_run"] for s in
                                                                                            srcs),
            "ledger": "; ".join(s["file"] for s in srcs)}


def _assert_bound(b, r):
    """the bound line must stand in the candidate exactly as the verified ledger read it (stale binding stops)."""
    e = r["expect"]
    if b is None:
        raise InputsError(f"line {r['line_id']}: not in the candidate (stale binding)")
    loc = b.get("location") or {}
    ok = b["item_code"] == e["item_code"] and loc.get("floor") == e["floor"] and \
        b["evidence_state"] == e["evidence_state"]
    if ok and e.get("element_id") is not None:     # the line id is a hash over the element; the id is optional
        ok = loc.get("element_id") == e["element_id"]
    if ok and e.get("measured_net") is not None:
        ok = b.get("measured_net") is not None and abs(b["measured_net"] - e["measured_net"]) <= TOL
    if ok and e.get("high") is not None:
        ok = abs(_held_high(b) - e["high"]) <= TOL if _held_high(b) is not None else False
    if not ok:
        raise InputsError(f"line {r['line_id']}: {b['item_code']} {loc.get('element_id')} {b['evidence_state']} "
                          f"{b.get('measured_net')} / held high {_held_high(b)} is not the bound {e} (stale binding: "
                          f"re-bind before integrating)")
    if ((b.get("calculation") or {}).get("inputs") or {}).get(REC_KEY):
        raise InputsError(f"line {r['line_id']}: already corrected (applied once)")


def _held_high(ln):
    """the held line's upper bound: its range high, else the high its V3.0.18 closure record names."""
    br = ln.get("bounded_range") or {}
    if br.get("high") is not None:
        return float(br["high"])
    return None


def _restate(b, **kw):
    from engine.source import boq_line as BL
    ln = copy.deepcopy(b)
    for k, v in kw.items():
        if k in ("formula", "rec", "note"):
            continue
        ln[k] = v
    ln["calculation"] = dict(ln.get("calculation") or {}, formula=kw["formula"][:700],
                             inputs=dict((ln.get("calculation") or {}).get("inputs") or {}, **{REC_KEY: kw["rec"]}))
    A305._note(ln, kw["note"])
    return BL.validate(ln)


def changes_for(doc, l3032):
    """-> (changes, log)."""
    if not doc:
        return [], {"piece": PIECE, "state": "NO_PROJECT_INPUT"}
    by = {ln["line_id"]: ln for ln in l3032}
    if any(((ln.get("calculation") or {}).get("inputs") or {}).get(REC_KEY) for ln in l3032):
        raise InputsError("the candidate already carries the V3.0.33 structural corrections (applied once)")
    seen = set(by)
    changes = []
    log = {"piece": PIECE, "state": "RUN", "sources": doc["sources"], "by_action": {}, "m3_moved": {},
           "lines_added": 0, "lines_restated": 0}
    S = doc["_sources"]
    for r in doc["_rows"]:
        srcs = [S[t] for t in r["source_tasks"]]
        act = r["action"]
        log["by_action"][act] = log["by_action"].get(act, 0) + 1
        if act == "MISSING_HELD":
            tmpl = next((x for x in l3032 if x["item_code"] == r["item_code"]), None) or \
                next(x for x in l3032 if x["item_code"].startswith("STR.CONC."))
            q = (f"HELD (blank in the BOQ, never 0): {r['physical_element']} ({r['element_id']}): {r['held_reason']}; "
                 f"plan {_fmt(r['beside'])} {r['beside_unit']} DRAWING-CONFIRMED beside ({r['cause']})")
            rec = _rec(srcs, action=act, evidence_status=r["evidence_status"], beside=r["beside"],
                       beside_unit=r["beside_unit"], cause=r["cause"], held_reason=r["held_reason"],
                       owner_trade=r.get("owner_trade"), not_this_line=r.get("not_this_line"))
            ln = _new_held(tmpl, r, q, rec)
            if ln["line_id"] in seen:
                raise ValueError(f"{METHOD}: added line {r['element_id']} repeats an id")
            seen.add(ln["line_id"])
            changes.append(A305._change(PIECE, "ADD", None, ln, drawing_reference="; ".join(s["file"] for s in srcs),
                                        held=[{"what": f"{r['item_code']} {r['element_id']}", "why": r["held_reason"],
                                               "range": None, "scenario": None}],
                                        downstream=r.get("downstream") or [], verification=_ver(srcs),
                                        evidence_status=r["evidence_status"], codes=[PIECE, act],
                                        group=r["item_code"]))
            log["lines_added"] += 1
            continue
        b = by.get(r["line_id"])
        _assert_bound(b, r)
        before = A3018._before_rec(b)
        if act == "HELD_BOUND":
            lo, hi = _r(r["low"]), _r(r["high"])
            basis = (f"held bound {_fmt(lo)} .. {_fmt(hi)} m3 = 0 .. the element's own pieces "
                     f"({r['cause']})")[:300]
            br = dict(b.get("bounded_range") or {}, low=lo, high=hi, basis=basis)
            rec = _rec(srcs, action=act, evidence_status="HELD", before=before, cause=r["cause"],
                       removed_from_bound=r.get("removed"), kept_in_bound=r.get("kept"))
            formula = (f"HELD (never a value): bound {_fmt(lo)} .. {_fmt(hi)} m3 (was .. {_fmt(r['expect']['high'])}): "
                       f"{r['cause']}")
            after = _restate(b, bounded_range=br, formula=formula, rec=rec,
                             note=f"{METHOD}: held bound restated ({'+'.join(r['source_tasks'])}); still HELD; NOT "
                                  f"RELEASED")
            held = [{"what": f"{b['item_code']} {b['location'].get('element_id')}", "why": r["cause"][:300],
                     "range": [lo, hi], "scenario": None}]
            log["m3_moved"].setdefault("held_high", 0.0)
            log["m3_moved"]["held_high"] = _r(log["m3_moved"]["held_high"] + hi - r["expect"]["high"])
        elif act == "GAP_RESTORE":
            v = _r(r["value"])
            terms = "; ".join(f"{t['kind']} {_fmt(t['m3'])} m3 {t['name']}" for t in r["named_terms"])
            rec = _rec(srcs, action=act, evidence_status=r["evidence_status"], before=before, value=v,
                       named_terms=r["named_terms"], cause=r["cause"])
            old = b["calculation"]["formula"]
            formula = (f"{v} m3 = the drawn cell ({r['cause']}); was {_fmt(b['measured_net'])}: {terms}; previous "
                       f"basis: {old}")
            kw = {"measured_net": v}
            if b.get("gross") is not None:
                kw["gross"] = _r(b["gross"] + v - b["measured_net"])
            after = _restate(b, formula=formula, rec=rec,
                             note=f"{METHOD}: restated to the drawn cell ({'+'.join(r['source_tasks'])}); "
                                  f"{r['evidence_status']}; NOT RELEASED", **kw)
            held = []
            log["m3_moved"].setdefault("valued", 0.0)
            log["m3_moved"]["valued"] = _r(log["m3_moved"]["valued"] + v - b["measured_net"])
        else:   # CONFLICT_RANGE
            rd = r["readings"]
            lo, hi = _r(min(rd.values())), _r(max(rd.values()))
            end = "SCHEDULE" if abs(rd["SCHEDULE"] - b["measured_net"]) <= TOL else "DRAWN"
            basis = (f"CONFLICT printed-vs-drawn section: schedule {_fmt(rd['SCHEDULE'])} | drawn "
                     f"{_fmt(rd['DRAWN'])} m3 ({r['designer_item']})")[:300]
            q = (f"{b['location'].get('element_id')}: the schedule prints {r.get('schedule_print')} and the plan draws "
                 f"{r.get('drawn_print')}: which section is built? ({r['designer_item']}); range {_fmt(lo)} .. "
                 f"{_fmt(hi)} m3 held, never one end")
            rec = _rec(srcs, action=act, evidence_status="HELD", before=before, readings=rd, candidate_end=end,
                       designer_item=r["designer_item"], cause=r["cause"], member=r.get("member"))
            formula = (f"CONFLICT (held, never one reading): schedule {_fmt(rd['SCHEDULE'])} | drawn "
                       f"{_fmt(rd['DRAWN'])} -> range {_fmt(lo)} .. {_fmt(hi)} m3 (was the {end.lower()} end "
                       f"{_fmt(b['measured_net'])})")
            after = _restate(b, evidence_state="BOUNDED_EXPOSURE", measured_net=None, gross=None,
                             bounded_range={"low": lo, "high": hi, "basis": basis},
                             rfi={"question": q[:900], "unlocks": b["location"].get("element_id")},
                             formula=formula, rec=rec,
                             note=f"{METHOD}: HELD CONFLICT range ({'+'.join(r['source_tasks'])}); never one end; NOT "
                                  f"RELEASED")
            held = [{"what": f"{b['item_code']} {b['location'].get('element_id')}", "why": basis, "range": [lo, hi],
                     "scenario": None}]
            log["m3_moved"].setdefault("valued_to_range", 0.0)
            log["m3_moved"]["valued_to_range"] = _r(log["m3_moved"]["valued_to_range"] - b["measured_net"])
            log["m3_moved"].setdefault("range_low", 0.0)
            log["m3_moved"].setdefault("range_high", 0.0)
            log["m3_moved"]["range_low"] = _r(log["m3_moved"]["range_low"] + lo)
            log["m3_moved"]["range_high"] = _r(log["m3_moved"]["range_high"] + hi)
        changes.append(A305._change(PIECE, "REPLACE", b, after, drawing_reference="; ".join(s["file"] for s in srcs),
                                    held=held, downstream=r.get("downstream") or [], verification=_ver(srcs),
                                    evidence_status=r["evidence_status"], codes=[PIECE, act],
                                    group=after["item_code"]))
        log["lines_restated"] += 1
    log["by_action"] = dict(sorted(log["by_action"].items()))
    return changes, log


def _new_held(tmpl, r, q, rec):
    from engine.source import boq_line as BL
    pr = tmpl["project"]
    ln = BL.make_line(project_id=pr["project_id"], revision_set_sha256=pr["revision_set_sha256"],
                      item_code=r["item_code"], unit="m3", evidence_state="BLOCKED_RFI", measured_net=None,
                      element_id=r["element_id"], floor=r["floor"], room_id=None,
                      physical_element=r["physical_element"], formula=q.replace(" = ", " -> ")[:700],
                      inputs={REC_KEY: rec}, documents=copy.deepcopy(tmpl["source"]["documents"]),
                      geometry_source=tmpl["source"]["geometry_source"],
                      geometry_confidence=tmpl["source"].get("geometry_confidence") or "INFERRED_CANDIDATE",
                      rule_id=RULE_ID, rule_version=RULE_VERSION, rfi={"question": q[:900],
                                                                      "unlocks": r["element_id"]},
                      notes=f"{METHOD}: missing element added HELD BLANK ({'+'.join(r['source_tasks'])}); never 0; "
                            f"NOT RELEASED"[:600])
    ln["project"] = copy.deepcopy(pr)
    return BL.validate(ln)


# ================================================================================================ integrate / write
def check_corrections(lines):
    """on finished lines: every V3.0.33 record line is a structural concrete line; HELD_BOUND / CONFLICT_RANGE /
    MISSING_HELD lines carry no value (held is BLANK, a range is a range); a CONFLICT range has the two readings as
    its ends; a GAP restore is valued. -> summary."""
    out = {"by_action": {}, "valued_m3": 0.0, "range_low_m3": 0.0, "range_high_m3": 0.0, "blank": 0}
    for ln in lines:
        rec = ((ln.get("calculation") or {}).get("inputs") or {}).get(REC_KEY)
        if not rec:
            continue
        act = rec["action"]
        if ln["item_code"] not in CONCRETE or ln["unit"] != "m3":
            raise ValueError(f"{METHOD}: {ln['line_id']} {ln['item_code']} {ln['unit']} is not structural concrete")
        out["by_action"][act] = out["by_action"].get(act, 0) + 1
        q, br = ln.get("measured_net"), ln.get("bounded_range") or {}
        if act == "GAP_RESTORE":
            if ln["evidence_state"] not in VALUED_STATES or not (q or 0) > 0:
                raise ValueError(f"{METHOD}: GAP restore {ln['line_id']} is not valued")
            out["valued_m3"] = _r(out["valued_m3"] + q)
            continue
        if q is not None:
            raise ValueError(f"{METHOD}: held / ranged line {ln['line_id']} carries a value {q} (held is BLANK)")
        if act == "CONFLICT_RANGE":
            rd = rec["readings"]
            if ln["evidence_state"] != "BOUNDED_EXPOSURE" or abs(br["low"] - min(rd.values())) > TOL or \
                    abs(br["high"] - max(rd.values())) > TOL:
                raise ValueError(f"{METHOD}: conflict line {ln['line_id']} range is not its two readings")
            out["range_low_m3"] = _r(out["range_low_m3"] + br["low"])
            out["range_high_m3"] = _r(out["range_high_m3"] + br["high"])
        elif act == "HELD_BOUND":
            if ln["evidence_state"] not in HELD_STATES or br.get("low") is None or br["low"] > br["high"]:
                raise ValueError(f"{METHOD}: held bound line {ln['line_id']} lost its range")
        elif act == "MISSING_HELD":
            if ln["evidence_state"] != "BLOCKED_RFI" or br:
                raise ValueError(f"{METHOD}: missing-element line {ln['line_id']} is not HELD BLANK")
            out["blank"] += 1
    out["by_action"] = dict(sorted(out["by_action"].items()))
    return out


def integrate(l3032, changes, for_lead=()):
    """-> (V3.0.33 lines, identity). Every line outside the rows is byte-identical to V3.0.32."""
    sid = {ln["line_id"] for ln in l3032}
    rep, adds = {}, []
    for c in changes:
        if c["piece"] != PIECE:
            raise ValueError(f"{METHOD}: piece {c['piece']} (this version only carries the structural corrections)")
        if c["action"] == "REPLACE":
            lid = c["before"]["line_id"]
            if lid in rep or lid not in sid or c["after"]["line_id"] != lid or \
                    c["after"]["item_code"] != c["before"]["item_code"] or c["after"]["item_code"] not in CONCRETE:
                raise ValueError(f"{METHOD}: line {lid}: changed twice, not in V3.0.32, its id / item changed or not "
                                 f"structural concrete")
            rep[lid] = c["after"]
        elif c["action"] == "ADD":
            a = c["after"]
            if a["line_id"] in sid or a["item_code"] not in CONCRETE:
                raise ValueError(f"{METHOD}: an added line repeats a V3.0.32 id or is not structural concrete")
            adds.append(a)
        else:
            raise ValueError(f"{METHOD}: action {c['action']}")
    out = [rep.get(ln["line_id"], ln) for ln in l3032] + adds
    if len({ln["line_id"] for ln in out}) != len(out):
        raise ValueError(f"{METHOD}: a BOQ line id appears twice")
    guards = A3031._family_guards(out, for_lead)   # every family guard up to V3.0.30
    roof = A3031.check_roof_layers(out)
    ceil = A3032.check_ceilings(out)
    corr = check_corrections(out)
    pids = {(ln["project"]["project_id"], ln["project"]["revision_set_sha256"]) for ln in out}
    if len(pids) != 1:
        raise ValueError(f"{METHOD}: {len(pids)} project identities in the lines (one project, one revision set)")
    by32 = {ln["line_id"]: ln for ln in l3032}
    touched = set(rep) | {a["line_id"] for a in adds}
    outside = [ln for ln in out if ln["line_id"] not in touched]
    bad = [ln["line_id"] for ln in outside if A30.line_sha(by32[ln["line_id"]]) != A30.line_sha(ln)]
    if bad or len(outside) + len(rep) != len(l3032):
        raise ValueError(f"{METHOD}: {len(bad)} line(s) outside the V3.0.33 rows differ from {EXTENDS}")
    for lid, ln in rep.items():   # inside a row only quantity, state, range, rfi, calculation and notes change
        a, b = copy.deepcopy(by32[lid]), copy.deepcopy(ln)
        for x in (a, b):
            for k in ROW_KEYS:
                x.pop(k, None)
        if json.dumps(a, sort_keys=True) != json.dumps(b, sort_keys=True):
            raise ValueError(f"{METHOD}: line {lid} changed outside quantity / state / range")
    ident = {"v3_0_32_lines": len(l3032), "v3_0_33_lines": len(out), "v3_0_33_rows": len(changes),
             "replaced": len(rep), "added": len(adds), "outside_rows": len(outside),
             "outside_rows_identical_to_v3_0_32": len(outside), "corrections": corr, "ceilings": ceil,
             "roof_buildup": roof, "guards": guards,
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
                     "item_code": ref["item_code"], "floor": loc.get("floor"), "element_id": loc.get("element_id"),
                     "unit": ref["unit"], "record_action": rec.get("action"),
                     "before_released_v2_9": b29,
                     "before_v3_0_32": (A30._qty(c["before"]) if c["before"] else
                                        dict(A30._qty(None), state="NOT_IN_V3_0_32")),
                     "before_held_range_v3_0_32": (c["before"] or {}).get("bounded_range"),
                     "after_v3_0_33": A30._qty(ref), "after_held_range_v3_0_33": ref.get("bounded_range"),
                     "evidence_status": c.get("evidence_status"), "cause": rec.get("cause"),
                     "still_held": c.get("held"), "release_status": "NOT RELEASED",
                     "owner_manual_method": PIECES[PIECE]["owner_manual_method"],
                     "drawing_derived_method": PIECES[PIECE]["drawing_method"],
                     "verification": c.get("verification") or {}, "rollback": ROLLBACK})
    return rows


LEDGER_CSV = ("version", "action", "line_id", "item_code", "floor", "element_id", "unit", "record_action", "v2_9",
              "v3_0_32", "v3_0_33", "held_range_v3_0_32", "held_range_v3_0_33", "evidence_status", "cause",
              "verification")
DIFF_CSV = ("line_id", "item_code", "floor", "element_id", "unit", "vs_v3_0_32", "vs_released_v2_9", "v2_9",
            "v3_0_32", "v3_0_33")


def _rg(br):
    return "" if not br else f"{_fmt(br.get('low'))} .. {_fmt(br.get('high'))}"


def ledger_csv(rows):
    return A305._csv([{"version": r["version"], "action": r["action"], "line_id": r["line_id"],
                       "item_code": r["item_code"], "floor": r["floor"] or "", "element_id": r["element_id"],
                       "unit": r["unit"], "record_action": r["record_action"],
                       "v2_9": A302._q(r["before_released_v2_9"]) if r["before_released_v2_9"] else "",
                       "v3_0_32": A302._q(r["before_v3_0_32"]), "v3_0_33": A302._q(r["after_v3_0_33"]),
                       "held_range_v3_0_32": _rg(r["before_held_range_v3_0_32"]),
                       "held_range_v3_0_33": _rg(r["after_held_range_v3_0_33"]),
                       "evidence_status": r["evidence_status"], "cause": (r["cause"] or "")[:400],
                       "verification": f"{r['verification'].get('task')} "
                                       f"{' '.join(x[:8] for x in r['verification'].get('merge_commits') or ())}"
                       } for r in rows], LEDGER_CSV)


def diff_rows(l3032, l3033, released_lines=None):
    b32 = {ln["line_id"]: ln for ln in l3032}
    rel = {A30._key(ln): ln for ln in released_lines or ()}
    out = []
    for ln in l3033:
        o = b32.get(ln["line_id"])
        vs = "ADDED" if o is None else ("SAME" if A30.line_sha(o) == A30.line_sha(ln) else
                                        ("CHANGED" if (A30._qty(o) != A30._qty(ln) or
                                                       o.get("bounded_range") != ln.get("bounded_range"))
                                         else "CHANGED_TEXT_ONLY"))
        r = rel.get(A30._key(ln)) if released_lines is not None else None
        vs29 = None if released_lines is None else ("NOT_IN_RELEASED" if r is None else
                                                    ("SAME_QUANTITY" if A30._qty(r) == A30._qty(ln) else
                                                     "QUANTITY_DIFFERS"))
        out.append({"line_id": ln["line_id"], "item_code": ln["item_code"], "floor": ln["location"].get("floor"),
                    "element_id": ln["location"].get("element_id"), "unit": ln["unit"], "vs_v3_0_32": vs,
                    "vs_released_v2_9": vs29, "v2_9": A302._q(A30._qty(r)) if r else "",
                    "v3_0_32": A302._q(A30._qty(o)) if o else "", "v3_0_33": A302._q(A30._qty(ln))})
    return out


def write(out, l3032, changes, log, doc, released_lines=None, for_lead=()):
    """the V3_0_33_* files beside the V3_0_32_* files. -> (file names, identity, ledger)."""
    from pathlib import Path
    from engine.source import boq_line as BL
    out = Path(out)
    l3033, ident = integrate(l3032, changes, for_lead)
    rows = ledger_rows(changes, released_lines)
    diff = diff_rows(l3032, l3033, released_lines)
    dsum = {}
    for d in diff:
        dsum.setdefault("vs_v3_0_32", {}).setdefault(d["vs_v3_0_32"], 0)
        dsum["vs_v3_0_32"][d["vs_v3_0_32"]] += 1
        if d["vs_released_v2_9"] is not None:
            dsum.setdefault("vs_released_v2_9", {}).setdefault(d["vs_released_v2_9"], 0)
            dsum["vs_released_v2_9"][d["vs_released_v2_9"]] += 1
    ident = dict(ident, diff=dsum)
    t32, t33 = A304.code_totals(l3032), A304.code_totals(l3033)
    moved = {k: {"v3_0_32": t32.get(k), "v3_0_33": t33.get(k)} for k in sorted(set(t32) | set(t33))
             if t32.get(k) != t33.get(k)}
    named = {r.get("item_code") or (r.get("expect") or {}).get("item_code") for r in (doc or {}).get("_rows") or ()}
    if any(k.split("|")[0] not in named for k in moved):
        raise ValueError(f"{METHOD}: totals moved outside the structural codes the rows name: {sorted(moved)[:5]}")
    led = {"schema": LEDGER_SCHEMA, "method": METHOD, "extends": EXTENDS, "candidate": CANDIDATE,
           "base": A30.BASE_METHOD, "released": A30.RELEASED_METHOD, "released_default": False, "rows": rows,
           "waiting_pieces": WAITING, "integration_package": True}
    run = {"method": METHOD, "policy": POLICY_ID, "extends": EXTENDS, "candidate": CANDIDATE,
           "base_method": A30.BASE_METHOD, "released_method": A30.RELEASED_METHOD, "released_default": False,
           "rollback": ROLLBACK, "identity": ident, "pieces": PIECES, "piece_logs": [log],
           "totals_moved_by_code": moved, "waiting_pieces": WAITING}
    files = {"V3_0_33_BOQ_LINES.json": BL.dumps(l3033),
             "V3_0_33_BOQ_LINES.csv": A30._lines_csv(l3033),
             "V3_0_33_INTEGRATION_LEDGER.json": A30._j(led),
             "V3_0_33_INTEGRATION_LEDGER.csv": ledger_csv(rows),
             "V3_0_33_DIFF.csv": A305._csv(diff, DIFF_CSV),
             "V3_0_33_RUN.json": A30._j(run)}
    for name, text in files.items():
        (out / name).write_text(text, encoding="utf-8")
    return sorted(files), ident, led


def policy_record():
    return {"method": METHOD, "extends": EXTENDS, "pieces": sorted(PIECES), "inputs_schema": INPUTS_SCHEMA,
            "released_default": False, "rollback": ROLLBACK, "actions": list(ACTIONS)}


__all__ = ["METHOD", "PIECES", "WAITING", "DEFAULT_GUARD_CLASS", "INPUTS_SCHEMA", "load_inputs", "changes_for",
           "check_corrections", "integrate", "ledger_rows", "diff_rows", "write", "InputsError"]
