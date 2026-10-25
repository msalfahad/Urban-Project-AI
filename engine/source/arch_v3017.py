"""ARCH_TAKEOFF_V3.0.17 (T-254): the SAME opt-in BOQ candidate as ARCH_TAKEOFF_V3.0 .. V3.0.16 (engine.source.arch_v30,
arch_v301 .. arch_v3016), extended with ONE basis-correction piece: candidate lines whose quantity rests on a depth or
height the drawings do not print for that element are corrected line id by line id from a checker-merged basis ledger.
Not a new method family and not the released default (owner management decision 2026-10-20 sections 2 and 5);
rollback is running the released ARCH_TAKEOFF_V2.9.

The physical question (ERS 2026-10-22 s.2.1, s.3): a ground beam is the concrete between its drawn faces from its
printed soffit to its printed top; a column runs from the top of the member under it to the soffit of the member over
it. A line that takes the depth of ANOTHER class (an interior beam depth on an exterior run) or a FINISHED level as a
structural end has no printed basis for its quantity (owner 2026-10-24 23:57 (2): UNSUPPORTED BASIS). Each such line
becomes, in place (same line id, so a verdict or a downgrade record bound to it stays bound):

  REBASE    the drawing-derived value of the merged ledger (the element's own printed depth / levels): SOURCE_DERIVED,
            evidence DRAWING-CONFIRMED (VERIFIED only where the record names the checker run that re-measured it);
            a rebase must name the printed support for THIS element and the sheets, never a borrowed class depth;
  HOLD      BLOCKED_RFI, BLANK (no figure, no range in the BOQ: owner 2026-10-24 10:56) with the named item that holds
            it; drawing readings go to V3_0_17_SCENARIOS.json only, never summed, never 0;
  CONFLICT  as HOLD, naming both readings (a numeric reading, if any, only in the scenario file, never adopted).

A missing line can be ADDED only HELD (a drawn element the candidate omits whose quantity is not yet closable), with
its named item; the figure it would carry stays in the scenario file.

Refused (InputsError / ValueError, nothing written): a record whose line the candidate does not carry, or whose stated
'before' (evidence state, quantity) is not the line's (stale ledger); a line named twice; a REBASE with no value > 0,
no printed support, or a support marked borrowed / finished / from an unmerged task (PENDING); a HOLD / CONFLICT with a
figure (0 included) or with no named item; a scenario reading <= 0; a record of a task that is not a merged source; a
group whose line ids do not sum to its declared before / after totals; a run binding that leaves a drawn exterior run
unmatched or an exterior run inside a line the correction list does not name (bind_runs: the list is built from the
drawn runs, never from the engine's own side flag; lessons 2026-10-25, T-289). Everything outside the records is
byte-identical to V3.0.16 (asserted), including the project identity block.

Files: V3_0_17_BOQ_LINES.json / .csv, V3_0_17_INTEGRATION_LEDGER.json / .csv (per line: before V3.0.16, after,
released V2.9, evidence status, printed support, source task / merge / checker run, held item), V3_0_17_DIFF.csv
(every line against V3.0.16 and the released V2.9), V3_0_17_SCENARIOS.json (held readings), V3_0_17_RUN.json. Nothing
here names a project, a sheet, a layer or a coordinate: every value comes from the inputs.
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
from engine.source import arch_v3016 as A3016

DEFAULT_GUARD_CLASS = "TOOLING"          # T-212: corrects named lines from a merged ledger; adds no default value
METHOD = "ARCH_TAKEOFF_V3.0.17"
EXTENDS = A3016.METHOD
CANDIDATE = A30.METHOD
POLICY_ID = "URBAN_BOQ_T254_ARCH_V3_0_17"
INPUTS_SCHEMA = "URBAN_V3017_INPUTS_V1"
LEDGER_SCHEMA = "URBAN_V3017_INTEGRATION_LEDGER_V1"
ROLLBACK = A30.ROLLBACK
ACTIONS = ("REBASE", "HOLD", "CONFLICT")
DC, VER = "DRAWING-CONFIRMED", "VERIFIED"
SUPPORT_KINDS = ("OWN_PRINT", "TWO_PRINTED_LEVELS", "PRINTED_LEVELS_AND_FLOOR_CONTINUITY")
REFUSED_SUPPORT = ("BORROWED_CLASS_DEPTH", "FINISHED_LEVEL", "PROFILE_DEFAULT", "PENDING")
TOL = 1e-6
TOL_RUNS = 5e-4                          # a line's runs (4-decimal ledgers) vs its value
InputsError = A3015.InputsError
_num = A3015._num

PIECES = {
    "BASIS_CORRECTION": {
        "module": "engine/source/arch_v3017.py (checker-merged basis ledger applied line id by line id)",
        "policy": "BASIS_CORRECTION_V1", "rule_id": "R-BASIS-LEDGER-1", "rule_version": "T-289-merged",
        "owner_rules": ["owner 2026-10-24 23:57 (2): UNSUPPORTED BASIS (a confirmed wrong-basis quantity is never a "
                        "usable quantity)", "owner 2026-10-24 10:56 (held BLANK in the BOQ; readings only in the "
                        "scenario file)", "UP-QTY-STATUS-001 (held never 0)", "WORKFLOW_CONTROLS 2026-10-21 s.4 / s.5",
                        "Q-54 B (annex roof datum: finished level only)", "D-35 / D-39 / D-44 (designer items)"],
        "owner_manual_method": "the owner's manual method takes a ground beam at its section as printed and a column "
                               "from the structure below to the structure above (storey height only where both ends "
                               "are structural levels); no owner fallback depth or height exists for an unprinted "
                               "exterior depth or a roof without a slab level (WORKFLOW_CONTROLS s.4): HELD",
        "drawing_method": "each run face to face x the depth printed for its own class (exterior: the two printed "
                          "levels top and outer ground); a column between the printed structural levels of the "
                          "members it meets; a run whose class has no printed section, or a column whose end is only "
                          "a finished level, is HELD with the designer item named"},
}
WAITING = dict(A3014.WAITING)
WAITING.update({
    "ANNEX_EXTERIOR_DEPTH": "annex exterior ground beams: CONFLICT (literal 'FOLLOW ARCH.' 0.25 m vs the printed exterior "
                            "section; designer D-35)",
    "COURT_SECTION": "court ground beams: HELD (no printed section for outside ground on both sides; GS-16 architect)",
    "ROOF_DATUM": "2F and annex column tops: HELD (only finished roof levels printed; D-39, Q-54 B, D-44)",
    "BOUNDARY_COLUMNS": "boundary ground beam: HELD on the boundary column count / positions (M4: 'SEE ARCH PLAN', none "
                        "drawn); the band figure in V3_0_17_SCENARIOS.json only",
})


def _r(x, n=6):
    return None if x is None else round(float(x), n)


# ================================================================================================ generic binding
def bind_runs(runs, lines, tol=0.05):
    """bind DRAWN runs to candidate lines by geometry (never by the engine's own side flag).

    runs   [{"id", "cls": EXTERIOR | INTERIOR | ..., "axis": "X" | "Y", "at": offset, "a": start, "b": end}]
    lines  [{"line_id", "typed": the class the candidate gave the line, "axis", "at", "a", "b"}]
    -> {"by_line": {line_id: [run ids]}, "typed_mismatch": [(line_id, typed, run cls, run id)],
        "unmatched_runs": [run ids]}: a run binds to every line on its axis within tol of its offset whose interval
    overlaps it by more than tol; a run bound to no line is reported (never dropped); a line typed one class that holds
    a run of another class is reported (the T-289 case: an exterior run in a line typed interior)."""
    by_line, mism, unmatched = {}, [], []
    for r in runs:
        lo, hi = sorted((float(r["a"]), float(r["b"])))
        hit = False
        for ln in lines:
            if ln["axis"] != r["axis"] or abs(float(ln["at"]) - float(r["at"])) > tol:
                continue
            la, lb = sorted((float(ln["a"]), float(ln["b"])))
            if min(hi, lb) - max(lo, la) > tol:
                hit = True
                by_line.setdefault(ln["line_id"], []).append(r["id"])
                if ln["typed"] != r["cls"]:
                    mism.append((ln["line_id"], ln["typed"], r["cls"], r["id"]))
        if not hit:
            unmatched.append(r["id"])
    return {"by_line": {k: sorted(v) for k, v in sorted(by_line.items())}, "typed_mismatch": sorted(mism),
            "unmatched_runs": sorted(unmatched)}


def check_correction_list(binding, cls, named_line_ids):
    """refuse a correction list that misses a line holding a drawn run of class cls, or a drawn run of that class that
    binds to no line (it must be reported, never silently dropped). -> the line ids holding cls runs."""
    if binding["unmatched_runs"]:
        raise InputsError(f"{METHOD}: drawn run(s) {binding['unmatched_runs']} bind to no candidate line: reported, a "
                          "correction cannot close while a drawn run has no line")
    runs_cls = {m[3] for m in binding["typed_mismatch"] if m[2] == cls}
    holding = sorted({lid for lid, rs in binding["by_line"].items()
                      if any(r in runs_cls for r in rs)} | {m[0] for m in binding["typed_mismatch"] if m[2] == cls})
    miss = sorted(set(holding) - set(named_line_ids))
    if miss:
        raise InputsError(f"{METHOD}: line(s) {miss} hold a drawn {cls} run in a line typed otherwise and are not in the "
                          "correction list (a list taken from the engine's own flag misses them)")
    return holding


# ================================================================================================ inputs
def _source(s, where):
    for k in ("file", "sha256", "task", "merge_commit", "checker_run"):
        if not (isinstance(s, dict) and isinstance(s.get(k), str) and s[k].strip()):
            raise InputsError(f"{where}: source needs {k} (a merged ledger: file sha256, task, merge commit, checker run)")


def _check_record(r, tasks, seen):
    lid = r.get("line_id")
    if not lid:
        raise InputsError("every record names its candidate line id")
    if lid in seen:
        raise InputsError(f"line {lid} named twice (one record per line)")
    seen.add(lid)
    for k in ("item_code", "element_id", "group", "task", "physical_element"):
        if not r.get(k):
            raise InputsError(f"record {lid}: {k} required")
    if r["task"] not in tasks:
        raise InputsError(f"record {lid}: task {r['task']!r} is not one of the merged sources {sorted(tasks)}")
    b = r.get("before") or {}
    if b.get("evidence_state") is None or "measured_net" not in b:
        raise InputsError(f"record {lid}: before {{evidence_state, measured_net}} is asserted against the line")
    act = r.get("action")
    if act not in ACTIONS:
        raise InputsError(f"record {lid}: action {act!r} not one of {ACTIONS}")
    if act == "REBASE":
        v = r.get("value")
        if not (_num(v) and v > 0):
            raise InputsError(f"record {lid}: a rebase carries value > 0 (a missing value is HELD, never 0)")
        sp = r.get("support") or {}
        if sp.get("kind") in REFUSED_SUPPORT:
            raise InputsError(f"record {lid}: support {sp.get('kind')}: a borrowed class depth, a finished level, a "
                              "profile default or an unmerged value is no printed basis (HELD)")
        if sp.get("kind") not in SUPPORT_KINDS or not sp.get("printed") or not sp.get("sheets"):
            raise InputsError(f"record {lid}: a rebase names its printed support for this element: kind in "
                              f"{SUPPORT_KINDS}, printed text and sheets")
        st = r.get("status")
        if st not in (DC, VER):
            raise InputsError(f"record {lid}: status {st!r}: {DC} or {VER}")
        if st == VER and not r.get("verified_by"):
            raise InputsError(f"record {lid}: VERIFIED names the checker run that re-measured it")
        runs = r.get("runs")
        if runs is not None:
            if not runs or any(not (_num(x.get("value")) and x["value"] > 0) or not x.get("id") for x in runs):
                raise InputsError(f"record {lid}: each run carries id and value > 0")
            s = sum(x["value"] for x in runs)
            if abs(s - v) > TOL_RUNS:
                raise InputsError(f"record {lid}: value {v} != the sum of its runs {_r(s)}")
    else:
        for k in ("value", "low", "high", "runs"):
            if r.get(k) is not None:
                raise InputsError(f"record {lid}: a {act} record carries no figure ({k}): BLANK in the BOQ, readings "
                                  "only in the scenario")
        if not r.get("held_item") or not r.get("reasons"):
            raise InputsError(f"record {lid}: a {act} record names the item that holds it and why")
        if act == "CONFLICT" and len(r.get("readings_named") or ()) < 2:
            raise InputsError(f"record {lid}: a CONFLICT names both readings (readings_named)")
    sc = r.get("scenario")
    if sc is not None:
        if not isinstance(sc, dict) or not sc.get("readings"):
            raise InputsError(f"record {lid}: scenario carries its readings")
        for k, x in sc["readings"].items():
            if not (_num(x) and x > 0):
                raise InputsError(f"record {lid}: scenario reading {k} must be > 0 (a reading of 0 is no reading)")


def _check_add(a, tasks, seen):
    aid = a.get("id")
    if not aid or aid in seen:
        raise InputsError(f"added line {aid!r}: an id, once")
    seen.add(aid)
    for k in ("item_code", "unit", "floor", "element", "physical_element", "task", "item_en", "item_ar", "trade",
              "like_line_id"):
        if not a.get(k):
            raise InputsError(f"added line {aid}: {k} required")
    if a["task"] not in tasks:
        raise InputsError(f"added line {aid}: task {a['task']!r} is not a merged source")
    if a.get("state") != "HELD":
        raise InputsError(f"added line {aid}: an added line is HELD here (a released addition is its own package)")
    for k in ("value", "low", "high"):
        if a.get(k) is not None:
            raise InputsError(f"added line {aid}: a held line carries no figure ({k})")
    if not a.get("held_item") or not a.get("reasons"):
        raise InputsError(f"added line {aid}: names the item that holds it and why")
    sc = a.get("scenario") or {}
    for k, x in (sc.get("readings") or {}).items():
        if not (_num(x) and x > 0):
            raise InputsError(f"added line {aid}: scenario reading {k} must be > 0")


def load_inputs(doc, project_id=None):
    """URBAN_V3017_INPUTS_V1 or None:
        {"schema", "project", "sources": [{file, sha256, task, merge_commit, checker_run}],
         "records": [{line_id, item_code, element_id, group, task, physical_element, before: {evidence_state,
                      measured_net}, action REBASE | HOLD | CONFLICT, value, runs, support: {kind, printed, sheets},
                      status, verified_by, own_check, held_item, reasons, readings_named, scenario: {readings, basis}}],
         "adds": [{id, item_code, unit, floor, element, physical_element, task, item_en, item_ar, trade,
                   like_line_id, state HELD, held_item, reasons, scenario}],
         "groups": {name: {"lines", "before", "released_after", "held_lines"}},
         "not_in_this_package": [{line_id, why}] (named lines left byte-identical, e.g. carried by another package),
         "binding": {"cls", "source", "holding_line_ids"} (the drawn-run binding behind the list)}"""
    if doc is None:
        return None
    if doc.get("schema") != INPUTS_SCHEMA:
        raise InputsError(f"project inputs: schema must be {INPUTS_SCHEMA}")
    if project_id and doc.get("project") not in (None, project_id):
        raise InputsError(f"project inputs are for {doc.get('project')!r}, the run is {project_id!r}")
    srcs = doc.get("sources") or []
    if not srcs:
        raise InputsError("sources: the merged ledgers the records come from")
    tasks = set()
    for s in srcs:
        _source(s, "sources")
        tasks.add(s["task"])
    seen = set()
    recs = doc.get("records") or []
    if not recs:
        raise InputsError("no records")
    for r in recs:
        _check_record(r, tasks, seen)
    sa = set()
    for a in doc.get("adds") or ():
        _check_add(a, tasks, sa)
    for x in doc.get("not_in_this_package") or ():
        if not x.get("line_id") or not x.get("why"):
            raise InputsError("not_in_this_package names line_id and why")
        if x["line_id"] in seen:
            raise InputsError(f"line {x['line_id']} is both corrected and left out")
    groups = doc.get("groups") or {}
    have = {r["group"] for r in recs}
    if set(groups) != have:
        raise InputsError(f"groups declared {sorted(groups)} != the records' groups {sorted(have)}")
    for g, d in groups.items():
        rs = [r for r in recs if r["group"] == g]
        if d.get("lines") != len(rs):
            raise InputsError(f"group {g}: {len(rs)} lines, declared {d.get('lines')}")
        bsum = sum((r["before"].get("measured_net") or 0.0) for r in rs)
        if abs(bsum - d.get("before", -1)) > TOL_RUNS:
            raise InputsError(f"group {g}: line ids sum to {_r(bsum)} before, declared {d.get('before')}")
        asum = sum(r["value"] for r in rs if r["action"] == "REBASE")
        if abs(asum - d.get("released_after", -1)) > TOL_RUNS:
            raise InputsError(f"group {g}: released after {_r(asum)}, declared {d.get('released_after')}")
        if d.get("held_lines") != sum(1 for r in rs if r["action"] != "REBASE"):
            raise InputsError(f"group {g}: held lines differ from the declared {d.get('held_lines')}")
    bd = doc.get("binding")
    if bd is not None:
        named = {r["line_id"] for r in recs} | {x["line_id"] for x in doc.get("not_in_this_package") or ()}
        miss = sorted(set(bd.get("holding_line_ids") or ()) - named)
        if miss:
            raise InputsError(f"binding: line(s) {miss} hold a drawn {bd.get('cls')} run and are not corrected")
    return doc


def _src_of(doc, task):
    for s in doc["sources"]:
        if s["task"] == task:
            return s
    raise InputsError(f"no merged source for task {task}")


# ================================================================================================ lines
def corrected_line(before, r, src):
    """the V3.0.17 line for one record: the V3.0.16 line in place, only its quantity, state and basis changed."""
    from engine.source import boq_line as BL
    p = PIECES["BASIS_CORRECTION"]
    ln = copy.deepcopy(before)
    rec = {"policy": p["policy"], "group": r["group"], "action": r["action"], "task": src["task"],
           "ledger": src["file"], "ledger_sha256": src["sha256"], "merge_commit": src["merge_commit"],
           "checker_run": src["checker_run"], "physical_element": r["physical_element"],
           "before": {"evidence_state": before["evidence_state"], "measured_net": before.get("measured_net"),
                      "bounded_range": before.get("bounded_range"), "formula": before["calculation"]["formula"]},
           "engine_basis": r.get("engine_basis")}
    if r["action"] == "REBASE":
        rec.update(value=_r(r["value"]), runs=r.get("runs"), support=r["support"], status=r["status"],
                   verified_by=r.get("verified_by"), own_check=r.get("own_check"))
        ln["evidence_state"] = "SOURCE_DERIVED"
        ln["measured_net"] = _r(r["value"])
        ln["bounded_range"] = None
        ln["rfi"] = None
        ln["calculation"]["formula"] = (r.get("formula") or f"{r['support']['kind']}: {r['support']['printed']}")[:400]
        A305._note(ln, f"{METHOD}: basis corrected ({src['task']} MERGED {src['merge_commit']}, {src['checker_run']}): "
                       f"{r['status']}")
    else:
        rec.update(held_item=r["held_item"], reasons=list(r["reasons"]), readings_named=r.get("readings_named"),
                   scenario_ref=("V3_0_17_SCENARIOS.json#" + r["line_id"]) if r.get("scenario") else None)
        ln["evidence_state"] = "BLOCKED_RFI"
        ln["measured_net"] = None
        ln["bounded_range"] = None
        ln["rfi"] = {"question": f"{r['held_item']}: " + "; ".join(r["reasons"])[:800],
                     "unlocks": ln["location"].get("element_id")}
        ln["calculation"]["formula"] = (f"{r['action']} (blank in the BOQ, never 0): {r['held_item']}")[:400]
        A305._note(ln, f"{METHOD}: {r['action']} on an unsupported basis ({src['task']} MERGED {src['merge_commit']}); "
                       "blank in the BOQ, never 0")
    ln["calculation"]["inputs"] = dict(ln["calculation"].get("inputs") or {}, basis_correction_v3017=rec)
    return BL.validate(ln)


def added_line(lines, a, src):
    """a HELD line for a drawn element the candidate omits, stamped like its sibling line (identity, documents)."""
    from engine.source import boq_line as BL
    by = {ln["line_id"]: ln for ln in lines}
    sib = by.get(a["like_line_id"])
    if sib is None:
        raise InputsError(f"added line {a['id']}: like_line_id {a['like_line_id']} is not a candidate line")
    if sib["item_code"] != a["item_code"] or sib["unit"] != a["unit"]:
        raise InputsError(f"added line {a['id']}: its sibling line is another item / unit")
    p = PIECES["BASIS_CORRECTION"]
    pr = sib["project"]
    eid = f"T254:{a['element']}"
    rec = {"policy": p["policy"], "action": "ADD_HELD", "task": src["task"], "ledger": src["file"],
           "ledger_sha256": src["sha256"], "merge_commit": src["merge_commit"], "checker_run": src["checker_run"],
           "held_item": a["held_item"], "reasons": list(a["reasons"]), "printed": a.get("printed"),
           "scenario_ref": ("V3_0_17_SCENARIOS.json#" + a["id"]) if a.get("scenario") else None}
    ln = BL.make_line(project_id=pr["project_id"], revision_set_sha256=pr["revision_set_sha256"],
                      item_code=a["item_code"], unit=a["unit"], evidence_state="BLOCKED_RFI", measured_net=None,
                      element_id=eid, floor=a["floor"], physical_element=a["physical_element"],
                      formula=f"HELD (blank in the BOQ, never 0): {a['held_item']}"[:400],
                      inputs={"basis_correction_v3017": rec}, documents=copy.deepcopy(sib["source"]["documents"]),
                      geometry_source=sib["source"]["geometry_source"], geometry_confidence="INFERRED_CANDIDATE",
                      rule_id=p["rule_id"], rule_version=p["rule_version"], material_state=sib["material_state"],
                      rfi={"question": f"{a['held_item']}: " + "; ".join(a["reasons"])[:800], "unlocks": eid},
                      notes=f"{METHOD}: drawn element the candidate omitted ({src['task']} MERGED {src['merge_commit']}); "
                            "HELD: blank in the BOQ, never 0",
                      subtrade=sib.get("subtrade"), item_en=a["item_en"], item_ar=a["item_ar"], trade=a["trade"])
    ln["project"] = copy.deepcopy(pr)
    return BL.validate(ln)


def changes_for(doc, l3016):
    """-> (changes, log)."""
    if not doc:
        return [], {"piece": "BASIS_CORRECTION", "state": "NO_PROJECT_INPUT"}
    by = {ln["line_id"]: ln for ln in l3016}
    changes, rows = [], []
    for r in doc["records"]:
        b = by.get(r["line_id"])
        if b is None:
            raise InputsError(f"record {r['line_id']}: the candidate does not carry this line")
        if b["item_code"] != r["item_code"] or b["location"].get("element_id") != r["element_id"]:
            raise InputsError(f"record {r['line_id']}: item / element {r['item_code']} {r['element_id']} is not the "
                              f"line's {b['item_code']} {b['location'].get('element_id')}")
        bq = b.get("measured_net")
        if b["evidence_state"] != r["before"]["evidence_state"] or \
                (bq is None) != (r["before"]["measured_net"] is None) or \
                (bq is not None and abs(bq - r["before"]["measured_net"]) > TOL):
            raise InputsError(f"record {r['line_id']}: the ledger's before {r['before']} is not the line's "
                              f"{b['evidence_state']} {bq} (stale ledger: refused)")
        src = _src_of(doc, r["task"])
        after = corrected_line(b, r, src)
        held = []
        if r["action"] != "REBASE":
            held = [{"what": f"{r['item_code']} {r['element_id']}", "why": f"{r['held_item']}: " +
                     "; ".join(r["reasons"]), "range": None,
                     "scenario": ("V3_0_17_SCENARIOS.json#" + r["line_id"]) if r.get("scenario") else None}]
        evs = r["status"] if r["action"] == "REBASE" else ("CONFLICT" if r["action"] == "CONFLICT" else "HELD")
        changes.append(A305._change("BASIS_CORRECTION", "REPLACE", b, after,
                                    drawing_reference=(r.get("support") or {}).get("sheets") or r.get("held_item"),
                                    held=held, downstream=list(r.get("downstream") or ()),
                                    verification={"task": src["task"], "merge_commit": src["merge_commit"],
                                                  "verifier_run": src["checker_run"], "ledger": src["file"],
                                                  "ledger_sha256": src["sha256"],
                                                  "record_verified_by": r.get("verified_by"),
                                                  "own_check": r.get("own_check")},
                                    evidence_status=evs, codes=["BASIS_CORRECTION", r["action"], r["group"]]))
    for a in doc.get("adds") or ():
        src = _src_of(doc, a["task"])
        ln = added_line(l3016, a, src)
        if ln["line_id"] in by:
            raise ValueError(f"{METHOD}: added line {a['id']} repeats a candidate line id")
        changes.append(A305._change("BASIS_CORRECTION", "ADD", None, ln, drawing_reference=a.get("printed"),
                                    held=[{"what": f"{a['item_code']} {a['element']}",
                                           "why": f"{a['held_item']}: " + "; ".join(a["reasons"]), "range": None,
                                           "scenario": "V3_0_17_SCENARIOS.json#" + a["id"]}],
                                    downstream=list(a.get("downstream") or ()),
                                    verification={"task": src["task"], "merge_commit": src["merge_commit"],
                                                  "verifier_run": src["checker_run"], "ledger": src["file"],
                                                  "ledger_sha256": src["sha256"]},
                                    evidence_status="HELD", codes=["BASIS_CORRECTION", "ADD_HELD"]))
    gt = {}
    for c in changes:
        if c["action"] != "REPLACE":
            continue
        g = c["codes"][2]
        d = gt.setdefault(g, {"lines": 0, "before": 0.0, "released_after": 0.0, "held_lines": 0})
        d["lines"] += 1
        d["before"] += c["before"].get("measured_net") or 0.0
        if c["after"]["evidence_state"] == "SOURCE_DERIVED":
            d["released_after"] += c["after"]["measured_net"]
        else:
            d["held_lines"] += 1
    for g, d in gt.items():
        dec = doc["groups"][g]
        if abs(d["before"] - dec["before"]) > TOL_RUNS or abs(d["released_after"] - dec["released_after"]) > TOL_RUNS:
            raise ValueError(f"{METHOD}: group {g} lines give {d}, declared {dec}")
    log = {"piece": "BASIS_CORRECTION", "state": "RUN", "sources": doc["sources"],
           "groups": {g: {k: (_r(v) if isinstance(v, float) else v) for k, v in d.items()} for g, d in sorted(gt.items())},
           "not_in_this_package": doc.get("not_in_this_package") or [], "binding": doc.get("binding"),
           "adds": [c["after"]["line_id"] for c in changes if c["action"] == "ADD"]}
    return changes, log


def scenarios(doc):
    out = []
    for r in list((doc or {}).get("records") or ()) + list((doc or {}).get("adds") or ()):
        sc = r.get("scenario")
        if sc and r.get("action", "HOLD") != "REBASE":
            out.append({"id": r.get("line_id") or r.get("id"), "item_code": r["item_code"], "group": r.get("group"),
                        "held_item": r.get("held_item"), "readings": sc["readings"], "basis": sc.get("basis"),
                        "readings_named": r.get("readings_named"),
                        "status": "HELD - SCENARIO ONLY, NOT A BOQ QUANTITY"})
    return out


# ================================================================================================ integrate / write
def integrate(l3016, changes):
    """-> (V3.0.17 lines, identity). Every line outside the V3.0.17 rows is byte-identical to the V3.0.16 line."""
    from engine.source import boq_line as BL
    sid = {ln["line_id"] for ln in l3016}
    rep, adds = {}, []
    for c in changes:
        if c["action"] == "REPLACE":
            lid = c["before"]["line_id"]
            if lid in rep:
                raise ValueError(f"{METHOD}: line {lid} changed twice")
            if lid not in sid:
                raise ValueError(f"{METHOD}: a change names a line the V3.0.16 run does not have")
            if c["after"]["line_id"] != lid:
                raise ValueError(f"{METHOD}: a changed line keeps its line id")
            rep[lid] = c["after"]
        elif c["action"] == "ADD":
            if c["after"]["line_id"] in sid:
                raise ValueError(f"{METHOD}: an added line repeats a V3.0.16 line id")
            adds.append(c["after"])
        else:
            raise ValueError(f"{METHOD}: action {c['action']}")
    out = [rep.get(ln["line_id"], ln) for ln in l3016] + adds
    if len({ln["line_id"] for ln in out}) != len(out):
        raise ValueError(f"{METHOD}: a BOQ line id appears twice")
    for ln in out:
        BL.validate(ln)
        if ln["evidence_state"] in BL.QUANTITY_STATES and (ln.get("calculation") or {}).get("inputs", {}).get(
                "basis_correction_v3017") and not (ln["measured_net"] or 0) > 0:
            raise ValueError(f"{METHOD}: {ln['line_id']} corrected to 0")
    A3011.check_conflicts(out)
    A3010.check_same_openings(out)
    A3012.check_partition(out)
    A3014.check_floor_scope(out)
    A3015.check_family(out)
    pids = {(ln["project"]["project_id"], ln["project"]["revision_set_sha256"]) for ln in out}
    if len(pids) != 1:
        raise ValueError(f"{METHOD}: {len(pids)} project identities in the lines (one project, one revision set)")
    by16 = {ln["line_id"]: ln for ln in l3016}
    touched = set(rep) | {a["line_id"] for a in adds}
    outside = [ln for ln in out if ln["line_id"] not in touched]
    bad = [ln["line_id"] for ln in outside if A30.line_sha(by16[ln["line_id"]]) != A30.line_sha(ln)]
    if bad or len(outside) + len(rep) != len(l3016):
        raise ValueError(f"{METHOD}: {len(bad)} line(s) outside the V3.0.17 rows differ from {EXTENDS}")
    for lid, ln in rep.items():   # inside a row only quantity, state, basis and notes change
        a, b = copy.deepcopy(by16[lid]), copy.deepcopy(ln)
        for x in (a, b):
            for k in ("evidence_state", "measured_net", "bounded_range", "rfi", "notes"):
                x.pop(k, None)
            x["calculation"] = None
        if json.dumps(a, sort_keys=True) != json.dumps(b, sort_keys=True):
            raise ValueError(f"{METHOD}: line {lid} changed outside quantity / state / basis")
    ident = {"v3_0_16_lines": len(l3016), "v3_0_17_lines": len(out), "v3_0_17_rows": len(changes),
             "replaced": len(rep), "added": len(adds), "outside_rows": len(outside),
             "outside_rows_identical_to_v3_0_16": len(outside),
             "outside_rows_sha256": hashlib.sha256("".join(A30.line_sha(x) for x in outside).encode()).hexdigest()}
    return out, ident


def ledger_rows(changes, released_lines=None):
    rel = {A30._key(ln): ln for ln in released_lines or ()}
    p = PIECES["BASIS_CORRECTION"]
    rows = []
    for c in changes:
        ref = c["after"] if c["before"] is None else c["before"]
        b16 = A30._qty(c["before"]) if c["before"] is not None else dict(A30._qty(None), state="NOT_IN_V3_0_16")
        b29 = None
        if released_lines is not None:
            b29 = A30._qty(rel[A30._key(ref)]) if A30._key(ref) in rel else dict(A30._qty(None),
                                                                                 state="NOT_IN_RELEASED")
        rec = c["after"]["calculation"]["inputs"]["basis_correction_v3017"]
        loc = ref.get("location") or {}
        rows.append({"version": METHOD, "piece": c["piece"], "action": c["action"], "line_id": ref["line_id"],
                     "item_code": ref["item_code"], "floor": loc.get("floor"), "element_id": loc.get("element_id"),
                     "unit": ref["unit"], "group": rec.get("group"), "before_released_v2_9": b29,
                     "before_v3_0_16": b16, "after_v3_0_17": A30._qty(c["after"]),
                     "evidence_status": c.get("evidence_status"), "release_status": "NOT RELEASED",
                     "codes": c.get("codes") or [], "drawing_reference": c.get("drawing_reference"),
                     "support": rec.get("support"), "engine_basis": rec.get("engine_basis"),
                     "owner_manual_method": p["owner_manual_method"], "drawing_method": p["drawing_method"],
                     "owner_rules": p["owner_rules"], "verification": dict(c.get("verification") or {},
                                                                            module=p["module"], policy=p["policy"]),
                     "held": c.get("held") or [], "downstream": c.get("downstream") or [], "rollback": ROLLBACK})
    return rows


LEDGER_CSV = ("version", "action", "group", "line_id", "item_code", "floor", "element_id", "unit", "v2_9", "v3_0_16",
              "v3_0_17", "evidence_status", "release_status", "support", "verification", "held")


def ledger_csv(rows):
    return A305._csv([{"version": r["version"], "action": r["action"], "group": r["group"], "line_id": r["line_id"],
                       "item_code": r["item_code"], "floor": r["floor"], "element_id": r["element_id"],
                       "unit": r["unit"], "v2_9": A302._q(r["before_released_v2_9"]),
                       "v3_0_16": A302._q(r["before_v3_0_16"]), "v3_0_17": A302._q(r["after_v3_0_17"]),
                       "evidence_status": r["evidence_status"], "release_status": r["release_status"],
                       "support": (f"{r['support'].get('kind')}: {r['support'].get('printed')}" if r["support"]
                                   else "")[:300],
                       "verification": f"{r['verification'].get('task')} {r['verification'].get('merge_commit')} "
                                       f"{r['verification'].get('verifier_run')}",
                       "held": "; ".join(str(h.get("why")) for h in r["held"])[:600]} for r in rows], LEDGER_CSV)


DIFF_CSV = ("line_id", "item_code", "floor", "element_id", "unit", "vs_v3_0_16", "vs_released_v2_9", "v2_9",
            "v3_0_16", "v3_0_17")


def diff_rows(l3016, l3017, released_lines=None):
    b16 = {ln["line_id"]: ln for ln in l3016}
    rel = {A30._key(ln): ln for ln in released_lines or ()}
    out = []
    for ln in l3017:
        o = b16.get(ln["line_id"])
        vs = "ADDED" if o is None else ("SAME" if A30.line_sha(o) == A30.line_sha(ln) else "CHANGED")
        r = rel.get(A30._key(ln)) if released_lines is not None else None
        vs29 = None if released_lines is None else ("NOT_IN_RELEASED" if r is None else
                                                    ("SAME_QUANTITY" if A30._qty(r) == A30._qty(ln) else
                                                     "QUANTITY_DIFFERS"))
        out.append({"line_id": ln["line_id"], "item_code": ln["item_code"], "floor": ln["location"].get("floor"),
                    "element_id": ln["location"].get("element_id"), "unit": ln["unit"], "vs_v3_0_16": vs,
                    "vs_released_v2_9": vs29, "v2_9": A302._q(A30._qty(r)) if r else "",
                    "v3_0_16": A302._q(A30._qty(o)) if o else "", "v3_0_17": A302._q(A30._qty(ln))})
    return out


def write(out, l3016, changes, log, doc, released_lines=None):
    """the V3_0_17_* files beside the V3_0_16_* files. -> (file names, identity, ledger)."""
    from pathlib import Path
    from engine.source import boq_line as BL
    out = Path(out)
    l3017, ident = integrate(l3016, changes)
    rows = ledger_rows(changes, released_lines)
    diff = diff_rows(l3016, l3017, released_lines)
    dsum = {}
    for d in diff:
        dsum.setdefault("vs_v3_0_16", {}).setdefault(d["vs_v3_0_16"], 0)
        dsum["vs_v3_0_16"][d["vs_v3_0_16"]] += 1
        if d["vs_released_v2_9"] is not None:
            dsum.setdefault("vs_released_v2_9", {}).setdefault(d["vs_released_v2_9"], 0)
            dsum["vs_released_v2_9"][d["vs_released_v2_9"]] += 1
    ident = dict(ident, diff=dsum)
    t16, t17 = A304.code_totals(l3016), A304.code_totals(l3017)
    moved = {k: {"v3_0_16": t16.get(k), "v3_0_17": t17.get(k)} for k in sorted(set(t16) | set(t17))
             if t16.get(k) != t17.get(k)}
    led = {"schema": LEDGER_SCHEMA, "method": METHOD, "extends": EXTENDS, "candidate": CANDIDATE,
           "base": A30.BASE_METHOD, "released": A30.RELEASED_METHOD, "released_default": False, "rows": rows,
           "waiting_pieces": WAITING, "integration_package": True}
    run = {"method": METHOD, "policy": POLICY_ID, "extends": EXTENDS, "candidate": CANDIDATE,
           "base_method": A30.BASE_METHOD, "released_method": A30.RELEASED_METHOD, "released_default": False,
           "rollback": ROLLBACK, "identity": ident, "pieces": PIECES, "piece_log": log,
           "totals_moved_by_code": moved, "waiting_pieces": WAITING,
           "evidence_status_counts": A302._count(r["evidence_status"] for r in rows)}
    files = {"V3_0_17_BOQ_LINES.json": BL.dumps(l3017),
             "V3_0_17_BOQ_LINES.csv": A30._lines_csv(l3017),
             "V3_0_17_INTEGRATION_LEDGER.json": A30._j(led),
             "V3_0_17_INTEGRATION_LEDGER.csv": ledger_csv(rows),
             "V3_0_17_DIFF.csv": A305._csv(diff, DIFF_CSV),
             "V3_0_17_SCENARIOS.json": A30._j({"method": METHOD, "note": "HELD readings only: never a BOQ quantity, "
                                                                          "never summed (owner 2026-10-24 10:56)",
                                               "scenarios": scenarios(doc)}),
             "V3_0_17_RUN.json": A30._j(run)}
    for name, text in files.items():
        (out / name).write_text(text, encoding="utf-8")
    return sorted(files), ident, led


def policy_record():
    return {"method": METHOD, "extends": EXTENDS, "pieces": sorted(PIECES), "inputs_schema": INPUTS_SCHEMA,
            "released_default": False, "rollback": ROLLBACK}


__all__ = ["METHOD", "PIECES", "WAITING", "DEFAULT_GUARD_CLASS", "INPUTS_SCHEMA", "bind_runs", "check_correction_list",
           "load_inputs", "corrected_line", "added_line", "changes_for", "scenarios", "integrate", "ledger_rows",
           "diff_rows", "write", "InputsError"]
