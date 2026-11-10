"""ARCH_TAKEOFF_V3.0.65 (T-671, lane I, CONCRETE GATE B ROUND 4 integration package): the SAME opt-in BOQ candidate
as ARCH_TAKEOFF_V3.0 .. V3.0.64 (engine.source.arch_v30, arch_v301 .. arch_v3064), extended with ONE piece built from
Checker-merged research ledgers of the B10 concrete families (STR.CONC.*, m3) left unwired by V3.0.64: the drawn
lower ends of the roof columns, the members a schedule prints as absent, and the split of a held strip whose
drawing fixes the low end:

  CONC_LEDGER   a named concrete line is restated as its merged ledger states it, with the V3.0.64 actions and
                states (BOUND, VALUE, HELD_BLANK, LOWER_ONLY, UPPER_ONLY, CONFIRM; R-T668-1 (a) .. (h) re-used as
                written), plus (new in V3.0.65):
                  NOT_APPLICABLE  the member is printed as ABSENT (a struck schedule row, a member drawn on no plan of
                                  that level): the line becomes NOT_APPLICABLE_WITH_EVIDENCE, no quantity, with its
                                  drawing evidence record (status DRAWING-CONFIRMED, the Checker run that confirmed
                                  it) and the bound it carried set aside by name; it is never 0 and never removed;
  CONC_SPLIT    ADD_COMPANION   a held range lo .. hi whose drawing fixes lo (R-T619-1 (c): a range is never a
                                  point): the line is VALUED at the drawn low end (a VALUE entry, the Checker's own
                                  re-measure) and ONE new companion line carries the open remainder HELD 0 .. (alt -
                                  lo) m3, bound to its VALUE line in the same inputs; low end + companion high stay
                                  inside the line's old range.

R-T671-1 (every villa; = R-T668-1 + the three additions, ERS s.2-5, UP-QTY-STATUS-001, WORKFLOW CONTROLS s.1 / s.5):
(a) .. (i) as R-T668-1; (j) a printed absence is a state with evidence, never a zero quantity: a NOT_APPLICABLE line
was HELD, keeps its id, carries no quantity, names its drawing evidence (DRAWING-CONFIRMED) and the Checker run, and
leaves the code totals only by its own bound (or blank count); (k) a companion is new (id and element carried by no
candidate line), HELD BOUNDED 0 .. x with x > 0, names its VALUE line, and value + x and value lie inside the VALUE
line's old range; (l) a line this version restates keeps every earlier version's record, moved under `superseded`
in its V3.0.65 record (the earlier version's state check then reads only the lines it still governs).
Files: V3_0_65_BOQ_LINES.json / .csv, V3_0_65_INTEGRATION_LEDGER.json / .csv, V3_0_65_DIFF.csv, V3_0_65_RUN.json.
Nothing here names a project, a sheet, a layer or a coordinate.
"""

from __future__ import annotations

import copy
import hashlib

from engine.source import arch_v30 as A30
from engine.source import arch_v302 as A302
from engine.source import arch_v304 as A304
from engine.source import arch_v305 as A305
from engine.source import arch_v3036 as A3036
from engine.source import arch_v3043 as A3043
from engine.source import arch_v3063 as A3063
from engine.source import arch_v3064 as A3064

DEFAULT_GUARD_CLASS = "TOOLING"          # T-212: re-books Checker-merged member ledgers onto candidate lines
METHOD = "ARCH_TAKEOFF_V3.0.65"
EXTENDS = A3064.METHOD
CANDIDATE = A30.METHOD
POLICY_ID = "URBAN_BOQ_T671_ARCH_V3_0_65"
INPUTS_SCHEMA = "URBAN_V3065_INPUTS_V1"
LEDGER_SCHEMA = "URBAN_V3065_INTEGRATION_LEDGER_V1"
ROLLBACK = A30.ROLLBACK
InputsError = A3063.InputsError
_r = A3063._r
_fmt = A3063._fmt
RULE_ID, RULE_VERSION = "R-T671-1", "T-671"
REC_KEY = "concrete_ledger_v3065"
EARLIER_KEYS = ("concrete_ledger_v3062", "concrete_ledger_v3063", "concrete_ledger_v3064")
P_CL, P_SPLIT = "CONC_LEDGER", "CONC_SPLIT"
NA, COMP = "NOT_APPLICABLE", "ADD_COMPANION"
NA_STATE = "NOT_APPLICABLE_WITH_EVIDENCE"
BASE_ACTIONS = A3063.ACTIONS                    # BOUND, VALUE, HELD_BLANK, LOWER_ONLY, UPPER_ONLY, CONFIRM
ACTIONS = BASE_ACTIONS + (NA, COMP)
CHANGING = A3063.CHANGING + (NA, COMP)
BLANK_ACTIONS = A3063.BLANK_ACTIONS
CODE_PREFIX, UNIT = A3063.CODE_PREFIX, A3063.UNIT
BOUNDED, BLANK, VALUED = A3063.BOUNDED, A3063.BLANK, A3063.VALUED
TOT_TOL, BIND_TOL, MAX_Q = A3063.TOT_TOL, A3063.BIND_TOL, A3063.MAX_Q
EVIDENCE_STATUS = ("DRAWING-CONFIRMED",)
line_class = A3063.line_class

PIECES = {
    P_CL: {"module": "engine/source/arch_v3065.py (named B10 column lines restated from the Checker-merged T-669 / "
                     "T-647 ledgers: drawn lower ends of the roof columns, schedule-absent members NOT_APPLICABLE; "
                     "nothing else moves)",
           "policy": "CONCRETE_GATE_B_V4", "rule_id": "R-T669-2 / FR-T647-1..5 (R-T671-1)",
           "owner_rules": ["UP-CONC-JOINT-001 (a column runs from its base to the slab top)",
                           "UP-QTY-STATUS-001 (held is blank or bounded, never 0)",
                           "ERS s.2-5 (drawn element first; a printed absence is evidence, not a zero)"],
           "owner_manual_method": "column at the printed storey height x the schedule section; a member the schedule "
                                  "strikes is not taken off",
           "drawing_method": "the merged T-669 ledger: roof column from its approved base datum to at least the "
                             "highest printed opening top under the one drawn roof slab + its printed thickness "
                             "(R-T669-2), up to the R-T658-4 ceiling; the merged T-647 census: the schedule row struck "
                             "on every level above the neck = NOT_APPLICABLE_WITH_EVIDENCE (Checker-confirmed)"},
    P_SPLIT: {"module": "engine/source/arch_v3065.py (a held strip whose drawing fixes the low end: the line valued at "
                        "that end, its depth remainder one new companion line HELD 0 .. x)",
              "policy": "CONCRETE_GATE_B_V4", "rule_id": "FR-T642-2 / R-T619-1 (c) (R-T671-1 (k))",
              "owner_rules": ["UP-QTY-STATUS-001", "ERS s.2.4 (one physical element once)"],
              "owner_manual_method": "the strip at one mark's depth over its drawn plan",
              "drawing_method": "the merged T-642 fix row: the strip plan from its face entities x the depth of the "
                                "mark its faces carry (released low end); the alternative mark's extra depth HELD as "
                                "its own companion line 0 .. x (no mark printed on the strip)"},
}
WAITING = {k: v for k, v in A3064.WAITING.items() if k not in ("T668_ROOF_COLUMN_LOWER_ENDS",)}   # wired here
WAITING.update({
    "T671_ANNEX_C3_LOW": "annex C3 column (GF): no lower end printed (no annex opening head / sill, no annex roof "
                         "slab thickness or top level; Q-54 B / D-39): R-T669-2 refuses, the line keeps its V3.0.64 "
                         "upper-only state, low open by name",
    "T671_GROUND_SLAB_T674": "T-674 (the 5 B10-05 ground-slab lines, drawing-only fix of T-180 P18) has not MERGED: "
                             "its lines keep their V3.0.64 state; the next concrete package wires it",
    "T671_2F_BLANK_COLUMNS": "2F C2 at the tank, 2F C3 and 2F C5 (blank, D-39 / D-44 / D-66): T-669 names a lower end "
                             "MEASURABLE NOW but no merged ledger states it (section conflict D-66): not wired",
})


# ================================================================================================ inputs
def _need(s, keys, where):
    return A3063._need(s, keys, where)


def _num(x, where, top=MAX_Q, zero=False):
    return A3063._num(x, where, top, zero)


def _na_entry(e, srcs):
    w = f"{NA} {e.get('line_id')}"
    if not isinstance(e.get("line_id"), str) or not A3063.LINE_ID_RE.match(e["line_id"]):
        raise InputsError(f"{w}: line id")
    A3043._tasks(e, srcs, w)
    _need(e, ("expect", "member", "basis", "evidence"), w)
    x = e["expect"]
    _need(x, ("item_code", "element_id", "unit", "class"), w)
    if not str(x["item_code"]).startswith(CODE_PREFIX) or x["unit"] != UNIT or x["class"] != "HELD":
        raise InputsError(f"{w}: only a HELD STR.CONC.* m3 line is restated NOT_APPLICABLE")
    if e.get("after") or e.get("value") is not None or e.get("downgrade"):
        raise InputsError(f"{w}: a not-applicable line carries no quantity (its evidence is the record)")
    ev = e["evidence"]
    _need(ev, ("status", "drawing", "reading", "checker_run"), f"{w} evidence")
    if ev["status"] not in EVIDENCE_STATUS:
        raise InputsError(f"{w}: the absence is {ev['status']!r}, not DRAWING-CONFIRMED (a held line stays held)")
    if x.get("low") is not None:
        sa = e.get("set_aside") or {}
        if not sa.get("why") or sa.get("low") is None or sa.get("high") is None:
            raise InputsError(f"{w}: the bound it carried leaves only with its set_aside record")
    return dict(e)


def _comp_entry(e, srcs):
    w = f"{COMP} {e.get('key')}"
    A3043._tasks(e, srcs, w)
    _need(e, ("key", "add", "companion_of", "template_line", "basis", "why_held", "question", "after"), w)
    x = e["add"]
    _need(x, ("item_code", "unit", "element_id", "physical_element"), w)
    if not str(x["item_code"]).startswith(CODE_PREFIX) or x["unit"] != UNIT:
        raise InputsError(f"{w}: {x['item_code']} {x['unit']} is not a code this version may add (STR.CONC.* m3)")
    af = e["after"]
    lo, hi = _num(af.get("low"), f"{w} low", zero=True), _num(af.get("high"), f"{w} high")
    if lo != 0.0:
        raise InputsError(f"{w}: a companion runs from 0 (the alternative may not hold), never a floor")
    if e.get("value") is not None:
        raise InputsError(f"{w}: a companion carries no value")
    return dict(e, after={"low": lo, "high": hi})


def load_inputs(doc, project_id=None):
    """URBAN_V3065_INPUTS_V1 -> the validated doc.
    {"schema", "project_id", "sources": [{"task", "file", "sha256", "merge_commit", "checker_run"}],
     "expect_totals": {"<code>|m3": {...}} (optional, asserted on the code totals),
     "entries": [V3.0.63 entry (BOUND / VALUE / blank / CONFIRM) |
                 {"action": "NOT_APPLICABLE", "line_id", "source_tasks", "member", "basis", "expect" {.. class HELD},
                  "evidence" {status DRAWING-CONFIRMED, drawing, reading, checker_run}, "set_aside" (the old bound)} |
                 {"action": "ADD_COMPANION", "key", "source_tasks", "companion_of" <line id of a VALUE entry>,
                  "template_line", "add" {item_code, unit, element_id, floor, physical_element}, "after" {low 0, high},
                  "basis", "why_held", "question"}]}"""
    if not doc:
        return None
    if doc.get("schema") != INPUTS_SCHEMA:
        raise InputsError(f"project inputs: schema must be {INPUTS_SCHEMA}")
    if project_id and doc.get("project_id") not in (None, project_id):
        raise InputsError(f"project inputs are for {doc.get('project_id')!r}, the run is {project_id!r}")
    srcs = A3043._sources(doc)
    ents = []
    for x in doc.get("entries") or ():
        a = x.get("action")
        if a == NA:
            ents.append(_na_entry(x, srcs))
        elif a == COMP:
            ents.append(_comp_entry(x, srcs))
        elif a in BASE_ACTIONS:
            if x.get("downgrade"):
                raise InputsError(f"{a} {x.get('line_id')}: no released line is restated by this version")
            ents.append(A3063._entry(x, srcs))
        else:
            raise InputsError(f"entry action {a!r}")
    if not ents:
        raise InputsError("no entry in the inputs")
    seen = set()
    for e in ents:
        k = e.get("line_id") or f"{COMP}:{e['key']}"
        if k in seen:
            raise InputsError(f"{k}: named twice (one line, one restatement)")
        seen.add(k)
    vals = {e["line_id"]: e for e in ents if e["action"] == "VALUE"}
    used = set()
    for e in ents:                                       # R-T671-1 (k): a companion belongs to one VALUE entry
        if e["action"] != COMP:
            continue
        v = vals.get(e["companion_of"])
        if v is None or e["companion_of"] in used:
            raise InputsError(f"{COMP} {e['key']}: companion_of {e['companion_of']} is not one VALUE entry here")
        used.add(e["companion_of"])
        x = v["expect"]
        if x.get("low") is None:
            raise InputsError(f"{COMP} {e['key']}: its VALUE line had no range to split")
        val, hi = float(v["after"]["value"]), e["after"]["high"]
        if val < x["low"] - BIND_TOL or val + hi > x["high"] + BIND_TOL:
            raise InputsError(f"{COMP} {e['key']}: {val} + 0 .. {hi} leaves the line's own range "
                              f"{x['low']} .. {x['high']}")
    return dict(doc, _sources=srcs, _entries=ents)


# ================================================================================================ lines
def _rec(srcs, piece=P_CL, **kw):
    return dict({"piece": piece, "policy": PIECES[piece]["policy"], "tasks": [s["task"] for s in srcs],
                 "ledgers": [s["file"] for s in srcs], "ledger_sha256": [s["sha256"] for s in srcs],
                 "merge_commits": [s["merge_commit"] for s in srcs], "checker_runs": [s["checker_run"] for s in srcs],
                 "rule_id": RULE_ID, "rule_version": RULE_VERSION, "release_status": "NOT RELEASED"}, **kw)


def _supersede(inp):
    """R-T671-1 (l): the earlier versions' records of a restated line, kept whole under this version's record"""
    return {k: inp.pop(k) for k in EARLIER_KEYS if k in inp}


def _restate(b, e, srcs):
    a, af = e["action"], e.get("after") or {}
    ln = copy.deepcopy(b)
    was = {"evidence_state": b["evidence_state"], "measured_net": b.get("measured_net"), "gross": b.get("gross"),
           "bounded_range": b.get("bounded_range"), "rfi": b.get("rfi"),
           "formula": (b.get("calculation") or {}).get("formula"), "class": line_class(b)}
    if a == "BOUND":
        lo, hi = float(af["low"]), float(af["high"])
        ln["evidence_state"], ln["measured_net"], ln["gross"] = BOUNDED, None, None
        ln["bounded_range"] = {"low": _r(lo), "high": _r(hi), "basis": f"{e['member']}: {e['basis']}"[:200]}
        ln["rfi"] = {"question": e["question"][:400], "blocks": [b["line_id"]]}
        head = f"HELD (BOUNDED) {_fmt(lo)} .. {_fmt(hi)} m3"
        after = {"low": _r(lo), "high": _r(hi)}
    elif a == "VALUE":
        v = float(af["value"])
        ln["evidence_state"], ln["measured_net"], ln["gross"] = VALUED, _r(v), _r(v)
        ln["bounded_range"], ln["rfi"] = None, None
        head = f"VALUED AS DRAWN {_fmt(v)} m3 (Checker re-measure: {e['remeasure']})"[:400]
        after = {"value": _r(v)}
    elif a == NA:
        ev = e["evidence"]
        ln["evidence_state"], ln["measured_net"], ln["gross"], ln["bounded_range"] = NA_STATE, None, None, None
        ln["rfi"] = None
        head = (f"NOT APPLICABLE WITH EVIDENCE ({ev['status']}: {ev['drawing']}: {ev['reading']}; "
                f"{ev['checker_run']})")[:600]
        after = {"state": NA_STATE}
    else:                                               # HELD_BLANK / LOWER_ONLY / UPPER_ONLY
        ln["evidence_state"], ln["measured_net"], ln["gross"], ln["bounded_range"] = BLANK, None, None, None
        ln["rfi"] = {"question": e["question"][:400], "blocks": [b["line_id"]]}
        head = {"LOWER_ONLY": "HELD, LOWER END ONLY (blank)", "UPPER_ONLY": "HELD, UPPER END ONLY (blank)",
                "HELD_BLANK": "HELD BLANK"}[a] + "; " + A3063._beside_text(e["beside"])
        after = {"beside": e["beside"]}
    ln["deductions"], ln["additions"] = [], []
    ln["calculation"] = dict(ln["calculation"], formula=(
        f"{METHOD}: {head} = {e['member']}: {e['basis']}" + (f"; {e['why_held']}" if e.get("why_held") else ""))[:1500])
    inp = ln["calculation"]["inputs"] = dict(ln["calculation"].get("inputs") or {})
    sup = _supersede(inp)
    inp[REC_KEY] = _rec(srcs, action=a, member=e["member"], was=was, after=after, basis=e["basis"],
                        why_held=(e.get("why_held") or "")[:600], beside=e.get("beside"),
                        set_aside=e.get("set_aside"), remeasure=e.get("remeasure"), evidence=e.get("evidence"),
                        squares=e.get("squares") or [], companion=None, superseded=sup,
                        freelancer_beside=e.get("freelancer_beside"))
    A305._note(ln, f"{METHOD}: {head[:300]} (was {A302._q(A30._qty(b))}); NOT RELEASED")
    return A3063._fin(ln)


def _companion(prev, e, srcs, value_line):
    from engine.source import boq_line as BL
    by = {ln["line_id"]: ln for ln in prev}
    w = f"{COMP} {e['key']}"
    tpl = by.get(e["template_line"])
    x = e["add"]
    if tpl is None or tpl["item_code"] != x["item_code"] or tpl["unit"] != x["unit"]:
        raise InputsError(f"{w}: template line {e['template_line']} is not a candidate {x['item_code']} line")
    if any(ln["item_code"] == x["item_code"] and (ln.get("location") or {}).get("element_id") == x["element_id"]
           for ln in prev):
        raise InputsError(f"{w}: {x['item_code']} {x['element_id']} is already carried by a candidate line")
    lo, hi = e["after"]["low"], e["after"]["high"]
    formula = (f"{METHOD}: HELD (BOUNDED) {_fmt(lo)} .. {_fmt(hi)} m3, companion of {e['companion_of']} (valued "
               f"{_fmt(value_line['measured_net'])} m3 at the drawn low end): {x['physical_element']}: {e['basis']}; "
               f"held by: {e['why_held']} (R-T671-1 (k), R-T619-1 (c))")[:1500]
    rec = _rec(srcs, P_SPLIT, action=COMP, key=e["key"], member=x["physical_element"], was=None,
               after={"low": _r(lo), "high": _r(hi)}, basis=e["basis"], why_held=e["why_held"][:600], beside=None,
               set_aside=None, remeasure=None, evidence=None, squares=[], superseded={},
               companion={"of": e["companion_of"], "value_m3": value_line["measured_net"]},
               template_line=e["template_line"], freelancer_beside=e.get("freelancer_beside"))
    ln = BL.make_line(
        project_id=tpl["project"]["project_id"], revision_set_sha256=tpl["project"]["revision_set_sha256"],
        item_code=x["item_code"], unit=x["unit"], evidence_state=BOUNDED, measured_net=None, gross=None,
        element_id=x["element_id"], floor=x.get("floor"), physical_element=x["physical_element"], formula=formula,
        bounded_range={"low": _r(lo), "high": _r(hi), "basis": f"companion of {e['companion_of']}: {e['basis']}"[:200]},
        inputs={REC_KEY: rec, "evidence_status": "HELD"}, documents=copy.deepcopy(tpl["source"]["documents"]),
        geometry_source=tpl["source"]["geometry_source"], geometry_confidence=tpl["source"]["geometry_confidence"],
        rule_id=RULE_ID, rule_version=RULE_VERSION, material_state=tpl.get("material_state") or "SOURCE",
        rfi={"question": e["question"][:900], "unlocks": x["element_id"]},
        notes=f"{METHOD}: depth companion of {e['companion_of']} (held 0 .. {_fmt(hi)} m3); NOT RELEASED",
        item_en=tpl["item_en"], item_ar=tpl["item_ar"], trade=tpl["trade"], subtrade=tpl.get("subtrade"))
    if ln["line_id"] in by:
        raise InputsError(f"{w}: the new line id {ln['line_id']} is a candidate id")
    return BL.validate(ln)


def _assert_na_bound(b, e):
    """the line is the HELD line the census read (code, element, range or blank) and its bound is set aside whole"""
    w = f"{NA} {e['line_id']}"
    if b is None:
        raise InputsError(f"{w}: not in the candidate (stale binding)")
    x, loc = e["expect"], b.get("location") or {}
    r = A3063._view_range(b)
    ok = b["item_code"] == x["item_code"] and loc.get("element_id") == x["element_id"] and b["unit"] == x["unit"] \
        and line_class(b) == "HELD"
    if ok and x.get("low") is None:
        ok = r is None and x.get("high") is None
    elif ok:
        sa = e["set_aside"]
        ok = r is not None and all(abs(a - c) <= BIND_TOL for a, c in ((r[0], x["low"]), (r[1], x["high"]),
                                                                        (r[0], sa["low"]), (r[1], sa["high"])))
    if not ok:
        raise InputsError(f"{w}: {b['item_code']} {loc.get('element_id')} {b['evidence_state']} range {r} is not the "
                          f"ledger's {x} (stale binding: re-read)")


def changes_for(doc, prev):
    """-> (changes, log). CONFIRM entries are asserted on the candidate line and change nothing."""
    if not doc:
        return [], {"piece": "T671", "state": "NO_PROJECT_INPUT"}
    if any(((ln.get("calculation") or {}).get("inputs") or {}).get(REC_KEY) for ln in prev):
        raise InputsError("the candidate already carries V3.0.65 records (applied once)")
    by = {ln["line_id"]: ln for ln in prev}
    S = doc["_sources"]
    changes, valued = [], {}
    log = {"piece": "T671", "state": "RUN", "sources": doc["sources"], "by_action": {}, "lines": 0, "added": 0,
           "confirmed": [], "not_applicable": []}
    for e in doc["_entries"]:
        log["by_action"][e["action"]] = log["by_action"].get(e["action"], 0) + 1
        if e["action"] == COMP:
            continue
        b = by.get(e["line_id"])
        if e["action"] == NA:
            _assert_na_bound(b, e)
        else:
            A3063._assert_bound(b, e)
        if e["action"] == "CONFIRM":
            log["confirmed"].append(e["line_id"])
            continue
        srcs = [S[t] for t in e["source_tasks"]]
        after = _restate(b, e, srcs)
        held = None
        if e["action"] == NA:
            log["not_applicable"].append(e["line_id"])
        elif e["action"] != "VALUE":
            q = A30._qty(after)
            held = [{"what": e["member"], "why": (e.get("why_held") or "")[:300],
                     "range": [q["low"], q["high"]] if q["low"] is not None else None, "beside": e.get("beside")}]
        else:
            valued[e["line_id"]] = after
        changes.append(A305._change(P_CL, "CHANGE", b, after, drawing_reference="; ".join(s["file"] for s in srcs),
                                    held=held, downstream=[], verification=A3036._ver(srcs),
                                    evidence_status={"VALUE": "VERIFIED", NA: "DRAWING-CONFIRMED"}.get(
                                        e["action"], "HELD"),
                                    codes=[P_CL], group=b["item_code"], step=e["action"]))
    for e in doc["_entries"]:
        if e["action"] != COMP:
            continue
        srcs = [S[t] for t in e["source_tasks"]]
        after = _companion(prev, e, srcs, valued[e["companion_of"]])
        changes.append(A305._change(P_SPLIT, "ADD", None, after, drawing_reference="; ".join(s["file"] for s in srcs),
                                    held=[{"what": e["add"]["physical_element"], "why": e["why_held"][:300],
                                           "range": [e["after"]["low"], e["after"]["high"]], "beside": None}],
                                    downstream=[], verification=A3036._ver(srcs), evidence_status="HELD",
                                    codes=[P_SPLIT], group=after["item_code"], step=COMP))
        log["added"] += 1
    log["lines"] = len(changes)
    return changes, log


# ================================================================================================ checks
def _bucket(ln):
    return A3063._bucket(ln)


def expected_totals(t0, changes):
    """the STR.CONC.*|m3 code totals the restatement must give, from the base totals and the changes alone: an ADD
    line counts once; a NOT_APPLICABLE line leaves its code's totals (a line, and its bound or blank count)"""
    zero = {"lines": 0, "released": 0.0, "held_low": 0.0, "held_high": 0.0, "bounded_lines": 0, "blocked_lines": 0}
    want = {}
    for c in changes:
        k = f"{c['after']['item_code']}|{c['after']['unit']}"
        z = want.setdefault(k, dict(t0.get(k) or zero))
        pairs = [(c["before"], -1), (c["after"], 1)] if c["before"] is not None else [(c["after"], 1)]
        for ln, s in pairs:
            if ln["evidence_state"] == NA_STATE:
                continue                                  # outside the code totals (A304.code_totals)
            z["lines"] += s
            q, bk = A30._qty(ln), _bucket(ln)
            if bk == "released":
                z["released"] += s * q["value"]
            elif bk == "bounded":
                z["held_low"] += s * q["low"]
                z["held_high"] += s * q["high"]
                z["bounded_lines"] += s
            else:
                z["blocked_lines"] += s
    return want


def check_totals(t0, t1, changes, expect=None):
    """only STR.CONC.*|m3 code totals move, each exactly by the restatement; optional expect = the inputs' figures"""
    moved = {k for k in set(t0) | set(t1) if t0.get(k) != t1.get(k)}
    bad = sorted(k for k in moved if not (k.startswith(CODE_PREFIX) and k.endswith(f"|{UNIT}")))
    if bad:
        raise ValueError(f"{METHOD}: totals moved outside STR.CONC.*|m3: {bad}")
    want = expected_totals(t0, changes)
    for k in moved:
        if k not in want:
            raise ValueError(f"{METHOD}: {k} moved with no change on it")
    out = {}
    for k, z in want.items():
        a = t1[k]
        ok = a["lines"] == z["lines"] and all(abs(a[f] - z[f]) <= TOT_TOL for f in ("released", "held_low",
                                                                                  "held_high")) and \
            a["bounded_lines"] == z["bounded_lines"] and a["blocked_lines"] == z["blocked_lines"]
        if not ok:
            raise ValueError(f"{METHOD}: {k} totals {t0.get(k)} -> {a} are not the restatement {z}")
        if expect and k in expect:
            for f, v in expect[k].items():
                if abs(a[f] - v) > TOT_TOL:
                    raise ValueError(f"{METHOD}: {k} {f} {a[f]} is not the inputs' {v}")
        out[k] = {"base": t0.get(k), "v3_0_65": a}
    return out


def check_concrete(lines, before=None):
    """on finished lines: every V3.0.65 line is in the state its action names (as V3.0.64; NOT_APPLICABLE: the NA
    state, no quantity, DRAWING-CONFIRMED evidence, was HELD; ADD_COMPANION: new, BOUNDED 0 .. x > 0, its VALUE line
    MEASURED); with `before`, no STR.CONC line went from held to released except a VALUE line. -> summary"""
    out = {a: 0 for a in CHANGING}
    ids = {ln["line_id"] for ln in before} if before is not None else None
    by = {ln["line_id"]: ln for ln in lines}
    for ln in lines:
        rec = ((ln.get("calculation") or {}).get("inputs") or {}).get(REC_KEY)
        if not rec:
            continue
        a = rec["action"]
        r = A3063._range(ln)
        ok = ln["item_code"].startswith(CODE_PREFIX) and ln["unit"] == UNIT
        if a == "BOUND":
            ok = ok and r is not None and 0 < r[0] <= r[1] + 1e-9 and ln.get("measured_net") is None and \
                bool((ln.get("rfi") or {}).get("question"))
        elif a == "VALUE":
            ok = ok and ln["evidence_state"] == VALUED and (ln.get("measured_net") or 0) > 0 and rec.get("remeasure")
        elif a == NA:
            ok = ok and ln["evidence_state"] == NA_STATE and ln.get("measured_net") is None and \
                not ln.get("bounded_range") and (rec.get("evidence") or {}).get("status") in EVIDENCE_STATUS and \
                rec["was"]["class"] == "HELD" and bool(ln.get("notes"))
        elif a == COMP:
            v = by.get((rec.get("companion") or {}).get("of"))
            ok = ok and r is not None and r[0] == 0.0 and r[1] > 0 and ln.get("measured_net") is None and \
                v is not None and v["evidence_state"] == VALUED and bool((ln.get("rfi") or {}).get("question"))
            if ok and ids is not None and ln["line_id"] in ids:
                raise ValueError(f"{METHOD}: {ln['line_id']}: a companion line was already a candidate line")
        else:
            ok = ok and ln["evidence_state"] == BLANK and ln.get("measured_net") is None and r is None and \
                bool((ln.get("rfi") or {}).get("question")) and rec.get("beside") is not None
        if not ok:
            raise ValueError(f"{METHOD}: {ln['line_id']}: a {a} line is not in its state")
        out[a] += 1
    if before is not None:
        b = {x["line_id"]: x for x in before}
        for ln in lines:
            o = b.get(ln["line_id"])
            if o is None or not ln["item_code"].startswith(CODE_PREFIX):
                continue
            rec = ((ln.get("calculation") or {}).get("inputs") or {}).get(REC_KEY) or {}
            if line_class(o) == "HELD" and line_class(ln) == "RELEASED" and rec.get("action") != "VALUE":
                raise ValueError(f"{METHOD}: {ln['line_id']}: a HELD concrete line was released without a re-measure")
    return out


# ================================================================================================ integrate / write
def integrate(prev, changes, for_lead=()):
    """-> (V3.0.65 lines, identity). Changed lines replace their candidate line in place; added lines follow; every
    other candidate line is byte-identical (asserted); the earlier versions' checks re-run on the result (the V3.0.64
    set, which re-runs V3.0.10 .. V3.0.63)."""
    sid = {ln["line_id"]: i for i, ln in enumerate(prev)}
    out = list(prev)
    adds, repl = [], set()
    for c in changes:
        a = c["after"]
        if not a["item_code"].startswith(CODE_PREFIX) or a["unit"] != UNIT:
            raise ValueError(f"{METHOD}: {a['item_code']} is not a code this version may touch")
        if c["action"] == "ADD":
            if a["line_id"] in sid or any(x["line_id"] == a["line_id"] for x in adds):
                raise ValueError(f"{METHOD}: an added line repeats an id")
            adds.append(a)
        elif c["action"] == "CHANGE":
            i = sid.get(a["line_id"])
            if i is None or a["line_id"] in repl:
                raise ValueError(f"{METHOD}: a changed line is not a candidate line or changes twice")
            out[i] = a
            repl.add(a["line_id"])
        else:
            raise ValueError(f"{METHOD}: action {c['action']}")
    out = out + adds
    if len({ln["line_id"] for ln in out}) != len(out):
        raise ValueError(f"{METHOD}: a BOQ line id appears twice")
    # every V3.0.10 .. V3.0.63 family check, re-run on these lines, then the V3.0.64 state check on them WITHOUT a
    # `before` (A3064.integrate(out, []) would pass these lines as their own base and refuse its own V3.0.64 added
    # line as 'already a candidate line': the V3.0.64 line is in the base by now, by design)
    _o, i63 = A3063.integrate(out, [], for_lead)
    i64 = {"checks_v3_0_63": {k: v for k, v in i63.items() if k not in (
        "base_lines", "v3_0_63_lines", "v3_0_63_rows", "replaced", "added", "outside_rows",
        "outside_rows_identical_to_base", "outside_rows_sha256")}, "concrete": A3064.check_concrete(out)}
    ident = {"base_lines": len(prev), "v3_0_65_lines": len(out), "v3_0_65_rows": len(changes), "replaced": len(repl),
             "added": len(adds), "checks_v3_0_64": i64, "concrete": check_concrete(out, prev)}
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
        rec = ref["calculation"]["inputs"][REC_KEY]
        rows.append({"version": METHOD, "piece": c["piece"], "action": c.get("step"), "change": c["action"],
                     "line_id": ref["line_id"], "item_code": ref["item_code"], "floor": loc.get("floor"),
                     "member": rec["member"], "element_id": loc.get("element_id"), "unit": ref["unit"],
                     "before_released_v2_9": b29, "before_base": A30._qty(c.get("before")),
                     "after_v3_0_65": A30._qty(ref),
                     "class": [rec["was"]["class"] if rec.get("was") else "NEW", line_class(ref)],
                     "evidence_status": c.get("evidence_status"), "still_held": c.get("held"),
                     "beside": rec.get("beside"), "evidence": rec.get("evidence"), "companion": rec.get("companion"),
                     "set_aside": rec.get("set_aside"), "remeasure": rec.get("remeasure"),
                     "superseded_record_keys": sorted(rec.get("superseded") or {}),
                     "release_status": "NOT RELEASED", "basis": rec["basis"],
                     "owner_manual_method": PIECES[c["piece"]]["owner_manual_method"],
                     "drawing_derived_method": PIECES[c["piece"]]["drawing_method"],
                     "verification": c.get("verification") or {}, "rollback": ROLLBACK})
    return rows


LEDGER_CSV = ("version", "piece", "action", "line_id", "item_code", "floor", "member", "element_id", "unit", "v2_9",
              "base", "v3_0_65", "class", "beside", "evidence_status", "verification")
DIFF_CSV = ("line_id", "item_code", "floor", "element_id", "unit", "vs_base", "vs_released_v2_9", "v2_9", "base",
            "v3_0_65")


def ledger_csv(rows):
    def q(x):
        return A302._q(x) if x and (x.get("value") is not None or x.get("low") is not None or x.get("state")) else ""

    def bs(r):
        t = [A3063._beside_text(r["beside"])] if r.get("beside") else []
        if r.get("evidence"):
            t.append(f"{r['evidence']['status']}: {r['evidence']['reading']}"[:200])
        if r.get("companion"):
            t.append(f"companion of {r['companion']['of']}")
        return "; ".join(t)
    return A305._csv([{"version": r["version"], "piece": r["piece"], "action": r["action"], "line_id": r["line_id"],
                       "item_code": r["item_code"], "floor": r.get("floor") or "", "member": r.get("member") or "",
                       "element_id": r.get("element_id") or "", "unit": r["unit"],
                       "v2_9": q(r.get("before_released_v2_9")), "base": q(r.get("before_base")),
                       "v3_0_65": q(r.get("after_v3_0_65")), "class": " -> ".join(r["class"]), "beside": bs(r),
                       "evidence_status": r["evidence_status"],
                       "verification": f"{r['verification'].get('task')} "
                                       f"{' '.join(x[:8] for x in r['verification'].get('merge_commits') or ())}"}
                      for r in rows], LEDGER_CSV)


def diff_rows(prev, new, released_lines=None):
    return [dict({k: v for k, v in d.items() if k != "v3_0_64"}, v3_0_65=d["v3_0_64"])
            for d in A3064.diff_rows(prev, new, released_lines)]


def write(out, prev, changes, log, released_lines=None, for_lead=(), expect_totals=None):
    """the V3_0_65_* files beside the base candidate's files. -> (file names, identity, ledger)."""
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
    adds = {c["after"]["line_id"] for c in changes if c["action"] == "ADD"}
    if {d["line_id"] for d in diff if d["vs_base"] == "ADDED"} != adds:
        raise ValueError(f"{METHOD}: the added lines are not the ADD changes")
    conf = set(log.get("confirmed") or ())
    if any(d["vs_base"] != "SAME" for d in diff if d["line_id"] in conf):
        raise ValueError(f"{METHOD}: a CONFIRM line moved")
    dsum = {}
    for d in diff:
        dsum.setdefault("vs_base", {}).setdefault(d["vs_base"], 0)
        dsum["vs_base"][d["vs_base"]] += 1
        if d["vs_released_v2_9"] is not None:
            dsum.setdefault("vs_released_v2_9", {}).setdefault(d["vs_released_v2_9"], 0)
            dsum["vs_released_v2_9"][d["vs_released_v2_9"]] += 1
    ident = dict(ident, diff=dsum, confirmed=len(conf), not_applicable=len(log.get("not_applicable") or ()))
    moved = check_totals(A304.code_totals(prev), A304.code_totals(new), changes, expect_totals)
    led = {"schema": LEDGER_SCHEMA, "method": METHOD, "extends": EXTENDS, "candidate": CANDIDATE,
           "base": A30.BASE_METHOD, "released": A30.RELEASED_METHOD, "released_default": False, "rows": rows,
           "confirmed_unchanged": sorted(conf), "waiting_pieces": WAITING, "integration_package": True}
    run = {"method": METHOD, "policy": POLICY_ID, "extends": EXTENDS, "candidate": CANDIDATE,
           "base_method": A30.BASE_METHOD, "released_method": A30.RELEASED_METHOD, "released_default": False,
           "rollback": ROLLBACK, "identity": ident, "pieces": PIECES, "piece_logs": [log],
           "totals_moved_by_code": moved, "waiting_pieces": WAITING}
    files = {"V3_0_65_BOQ_LINES.json": BL.dumps(new),
             "V3_0_65_BOQ_LINES.csv": A30._lines_csv(new),
             "V3_0_65_INTEGRATION_LEDGER.json": A30._j(led),
             "V3_0_65_INTEGRATION_LEDGER.csv": ledger_csv(rows),
             "V3_0_65_DIFF.csv": A305._csv(diff, DIFF_CSV),
             "V3_0_65_RUN.json": A30._j(run)}
    for name, text in files.items():
        (out / name).write_text(text, encoding="utf-8")
    return sorted(files), ident, led


def policy_record():
    return {"method": METHOD, "extends": EXTENDS, "pieces": sorted(PIECES), "inputs_schema": INPUTS_SCHEMA,
            "released_default": False, "rollback": ROLLBACK, "actions": list(ACTIONS)}


__all__ = ["METHOD", "PIECES", "WAITING", "DEFAULT_GUARD_CLASS", "INPUTS_SCHEMA", "load_inputs", "changes_for",
           "check_concrete", "check_totals", "expected_totals", "integrate", "ledger_rows", "diff_rows", "write",
           "InputsError", "line_class"]
