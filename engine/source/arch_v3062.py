"""ARCH_TAKEOFF_V3.0.62 (T-661, lane I, CONCRETE GATE B integration package): the SAME opt-in BOQ candidate as
ARCH_TAKEOFF_V3.0 .. V3.0.61 (engine.source.arch_v30, arch_v301 .. arch_v3061), extended with ONE piece built from
Checker-merged member ledgers of the B10 concrete families (STR.CONC.*, m3):

  CONC_LEDGER   each named HELD concrete line is restated member by member as its merged ledger states it, one of:
                  BOUND       a new drawn bound low .. high (BOUNDED_EXPOSURE), the old range kept in the record;
                  VALUE       a Checker re-measured value (MEASURED), the old bound kept in the record;
                  HELD_BLANK  no drawn bound (BLOCKED_RFI, blank, the RFI named): the measure the drawings DO fix
                              (a plan area, an AT_LEAST floor) is BESIDE the line in its record, never the quantity;
                              an old bound with no drawn basis leaves the line only with this replacement and is
                              kept in the record labelled 'not drawn';
                  LOWER_ONLY  a drawn lower end and an upper end open by a named item (BLOCKED_RFI, blank): the
                              AT_LEAST figure beside, never a range, never 0;
                  CONFIRM     the ledger states the line exactly as the candidate carries it: no change, the binding
                              asserted (a ledger that disagrees with the line refuses the run).

R-T661-1 (every villa; wires the merged member ledgers of the concrete lane, ERS s.2-5, UP-QTY-STATUS-001, WORKFLOW
CONTROLS s.1 / s.5): (a) every entry binds to the line as the candidate carries it (item, element, unit, class, value
or range to 1e-6) and stops on a stale line; (b) only STR.CONC.* m3 lines may change, each once; (c) a VALUE needs a
Checker re-measure named in its entry and is > 0; a BOUND has 0 < low <= high; a held line is never 0 and never
gains a value without (c); (d) a bound that leaves a line leaves only with its replacement (blank with the measure
beside, or lower only) and stays in the record with its reason; (e) every line not named, and every CONFIRM line, is
byte-identical (asserted); only STR.CONC.*|m3 code totals move, each by exactly the restatement (asserted).
Files: V3_0_62_BOQ_LINES.json / .csv, V3_0_62_INTEGRATION_LEDGER.json / .csv, V3_0_62_DIFF.csv, V3_0_62_RUN.json.
Nothing here names a project, a sheet, a layer or a coordinate.
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
from engine.source import arch_v3061 as A3061

DEFAULT_GUARD_CLASS = "TOOLING"          # T-212: re-books Checker-merged member ledgers onto candidate lines
METHOD = "ARCH_TAKEOFF_V3.0.62"
EXTENDS = A3061.METHOD
CANDIDATE = A30.METHOD
POLICY_ID = "URBAN_BOQ_T661_ARCH_V3_0_62"
INPUTS_SCHEMA = "URBAN_V3062_INPUTS_V1"
LEDGER_SCHEMA = "URBAN_V3062_INTEGRATION_LEDGER_V1"
ROLLBACK = A30.ROLLBACK
InputsError = A3031.InputsError
_r = A3018._r
_fmt = A3030._fmt
RULE_ID, RULE_VERSION = "R-T661-1", "T-661"
REC_KEY = "concrete_ledger_v3062"
P_CL = "CONC_LEDGER"
ACTIONS = ("BOUND", "VALUE", "HELD_BLANK", "LOWER_ONLY", "CONFIRM")
CHANGING = ("BOUND", "VALUE", "HELD_BLANK", "LOWER_ONLY")
CODE_PREFIX = "STR.CONC."
UNIT = "m3"
BOUNDED, BLANK, VALUED = "BOUNDED_EXPOSURE", "BLOCKED_RFI", "MEASURED"
VALUED_STATES = A3036.VALUED_STATES
EXCLUDED = ("EXCLUDED_WITH_REASON", "NOT_APPLICABLE_WITH_EVIDENCE")
CLASSES = ("RELEASED", "HELD")
BESIDE_KINDS = ("PLAN_AREA_M2", "AT_LEAST_M3", "NONE")
BIND_TOL = 1e-6
TOT_TOL = 1e-4
MAX_Q = 100.0                            # one concrete member line above 100 m3 is a unit slip
LINE_ID_RE = re.compile(r"^L-[0-9a-f]{20}$")

PIECES = {
    P_CL: {"module": "engine/source/arch_v3062.py (HELD B10 concrete lines restated member by member from the "
                     "Checker-merged ledgers: drawn bounds, a re-measured value, blank with the drawn measure beside, "
                     "lower only; nothing else moves)",
           "policy": "CONCRETE_GATE_B_V1", "rule_id": "R-T657-1..4 + R-T659-1..5 + R-T660-1..6 (R-T661-1)",
           "owner_rules": ["Q-21 C (no change of founding level without engineering approval)",
                           "Q-61 C (beams member by member; two marks never both)", "Q-65 C / Q-27 A / Q-28 A",
                           "UP-QTY-STATUS-001 (held is blank, never 0)", "ERS s.2-5 (drawn element first)"],
           "owner_manual_method": "one flat neck height 1.50 m x section; the beam-schedule section on every band; "
                                  "the boundary band at one section; parapets / dome / pit at a borrowed detail",
           "drawing_method": "the merged ledgers: necks h from the printed minimum (ST p.9 note 1) to the single-row "
                             "'LESS THAN 2.5m' detail (ST p.13) x schedule sections (T-657); beams member by member "
                             "between owning faces x printed depth, strips with no mark / bars / depth held with their "
                             "plan area (T-660); small elements bound only where printed (T-659)"},
}
WAITING = dict(A3061.WAITING)
WAITING.update({
    "T661_T658_COLUMNS_GROUND_BEAMS": "T-658 r2 (B10-06 columns, B10-04 ground beam / strap, B10-02 footing) is "
                                      "restaged into this package only after it is MERGED, never before",
    "T661_BOUNDARY_BAND": "the boundary band line keeps its V3.0.61 state: the Checker's T-659 residual (does the band "
                          "continue below the stretches where the building stands on the plot line with its own "
                          "exterior G.B?) is a cross-trade check not settled by any merged ledger; until it is, the "
                          "drawn bound 5.6392 .. 11.0328 m3 is not wired (its low end may not be a lower bound)",
    "T661_T642_COMPANION": "the T-642 GF BAND0030.2 depth companion (0 .. 0.025 m3) is a trial-BOQ overlay line, not a "
                           "candidate line: it enters with the T-642 split wiring, not as an add here",
    "T661_POOL_BLINDING": "pool blinding (ST p.7 '10cm PLAIN CONCRETE') is MISSING from the candidate (named by T-659, "
                          "never 0): a lane S row adds it",
})


# ================================================================================================ inputs
def _need(s, keys, where):
    for k in keys:
        if s.get(k) in (None, ""):
            raise InputsError(f"{where}: missing {k}")


def _num(x, where, top=MAX_Q, zero=False):
    if isinstance(x, bool) or not isinstance(x, (int, float)) or x != x:
        raise InputsError(f"{where}: not a number ({x!r})")
    if (x < 0 if zero else x <= 0) or x > top:
        raise InputsError(f"{where}: {x} outside 0 .. {top} m3 (unit slip, sign or HELD-as-0)")
    return float(x)


def _beside(b, where, need):
    """the measure beside a held line: {kind PLAN_AREA_M2 | AT_LEAST_M3 | NONE, value, basis}"""
    if b is None:
        if need:
            raise InputsError(f"{where}: a held line carries the measure the drawings fix beside it (or kind NONE)")
        return None
    k = b.get("kind")
    if k not in BESIDE_KINDS:
        raise InputsError(f"{where}: beside kind {k!r}")
    if k == "NONE":
        if b.get("value") is not None:
            raise InputsError(f"{where}: beside NONE carries no figure")
    else:
        _num(b.get("value"), f"{where} beside", top=1000.0)
        _need(b, ("basis",), f"{where} beside")
    return dict(b)


def _entry(e, srcs):
    a = e.get("action")
    if a not in ACTIONS:
        raise InputsError(f"entry action {a!r}")
    w = f"{a} {e.get('line_id')}"
    if not isinstance(e.get("line_id"), str) or not LINE_ID_RE.match(e["line_id"]):
        raise InputsError(f"{w}: line id")
    A3043._tasks(e, srcs, w)
    _need(e, ("expect", "member", "basis"), w)
    x = e["expect"]
    _need(x, ("item_code", "element_id", "unit", "class"), w)
    if not str(x["item_code"]).startswith(CODE_PREFIX) or x["unit"] != UNIT:
        raise InputsError(f"{w}: {x['item_code']} {x['unit']} is not a code this version may change (STR.CONC.* m3)")
    if x["class"] not in CLASSES:
        raise InputsError(f"{w}: class {x['class']}")
    if x["class"] == "RELEASED":
        raise InputsError(f"{w}: a released line is not restated by this version (held concrete lines only)")
    af = e.get("after") or {}
    if a == "BOUND":
        lo, hi = _num(af.get("low"), f"{w} low"), _num(af.get("high"), f"{w} high")
        if lo > hi + 1e-9:
            raise InputsError(f"{w}: low {lo} > high {hi}")
        _need(e, ("why_held", "question"), w)
    elif a == "VALUE":
        _num(af.get("value"), f"{w} value")
        _need(e, ("remeasure",), w)                     # the Checker's own re-measure of this member
        if af.get("low") is not None or af.get("high") is not None:
            raise InputsError(f"{w}: a value carries no range")
    elif a in ("HELD_BLANK", "LOWER_ONLY"):
        if af.get("value") is not None or af.get("low") is not None or af.get("high") is not None:
            raise InputsError(f"{w}: a {a} line carries no quantity and no range (blank, the measure beside)")
        _need(e, ("why_held", "question"), w)
        b = _beside(e.get("beside"), w, need=True)
        if a == "LOWER_ONLY" and (b is None or b["kind"] != "AT_LEAST_M3"):
            raise InputsError(f"{w}: a lower-only line carries its AT_LEAST m3 figure beside")
    else:                                               # CONFIRM
        if af:
            raise InputsError(f"{w}: a CONFIRM entry changes nothing (no after)")
    if a in ("HELD_BLANK", "LOWER_ONLY") and (x.get("low") is not None):
        _need(e, ("set_aside",), w)                     # a bound leaves only with its reason, kept in the record
    return dict(e)


def load_inputs(doc, project_id=None):
    """URBAN_V3062_INPUTS_V1 -> the validated doc.
    {"schema", "project_id", "sources": [{"task", "file", "sha256", "merge_commit", "checker_run"}],
     "expect_totals": {"<code>|m3": {released, held_low, held_high, ...}} (optional, asserted on the code totals),
     "entries": [{"action", "line_id", "source_tasks", "member", "basis",
                  "expect" {item_code, element_id, unit, class HELD, low / high (None = blank)},
                  "after" {low, high} | {value} | {}, "why_held", "question", "beside" {kind, value, basis},
                  "set_aside" (the old bound's reason), "remeasure" (VALUE: the Checker's own re-measure)}]}"""
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
        if e["line_id"] in seen:
            raise InputsError(f"{e['line_id']}: named twice (one line, one restatement)")
        seen.add(e["line_id"])
    return dict(doc, _sources=srcs, _entries=ents)


# ================================================================================================ lines
def line_class(ln):
    if ln["evidence_state"] in EXCLUDED:
        return "EXCLUDED"
    if ln["evidence_state"] in VALUED_STATES and ln.get("measured_net") is not None:
        return "RELEASED"
    return "HELD"


def _range(ln):
    if ln.get("evidence_state") != BOUNDED:
        return None
    b = ln.get("bounded_range") or {}
    lo, hi = b.get("low"), b.get("high")
    return (float(lo), float(hi)) if isinstance(lo, (int, float)) and isinstance(hi, (int, float)) else None


def _assert_bound(b, e):
    x = e["expect"]
    w = f"{e['action']} {e['line_id']}"
    if b is None:
        raise InputsError(f"{w}: not in the candidate (stale binding)")
    loc = b.get("location") or {}
    ok = (b["item_code"] == x["item_code"] and loc.get("element_id") == x["element_id"] and b["unit"] == x["unit"]
          and line_class(b) == x["class"])
    if ok:
        r = _range(b)
        if x.get("low") is None:
            ok = r is None and x.get("high") is None
        else:
            ok = r is not None and abs(r[0] - x["low"]) <= BIND_TOL and abs(r[1] - x["high"]) <= BIND_TOL
    if not ok:
        raise InputsError(f"{w}: {b['item_code']} {loc.get('element_id')} {b['evidence_state']} range {_range(b)} is "
                          f"not the ledger's {x} (stale binding: re-read)")
    if e["action"] in ("HELD_BLANK", "LOWER_ONLY") and _range(b) is not None:
        sa = e.get("set_aside") or {}
        if not sa.get("why") or sa.get("low") is None or abs(sa["low"] - _range(b)[0]) > BIND_TOL or \
                abs(sa["high"] - _range(b)[1]) > BIND_TOL:
            raise InputsError(f"{w}: the bound {_range(b)} leaves the line: its set_aside record must state it and why")


def _fin(ln):
    from engine.source import boq_line as BL
    return BL.validate(ln)


def _rec(srcs, **kw):
    return dict({"piece": P_CL, "policy": PIECES[P_CL]["policy"], "tasks": [s["task"] for s in srcs],
                 "ledgers": [s["file"] for s in srcs], "ledger_sha256": [s["sha256"] for s in srcs],
                 "merge_commits": [s["merge_commit"] for s in srcs], "checker_runs": [s["checker_run"] for s in srcs],
                 "rule_id": RULE_ID, "rule_version": RULE_VERSION, "release_status": "NOT RELEASED"}, **kw)


def _beside_text(b):
    if not b or b["kind"] == "NONE":
        return "no drawn measure beside"
    u = "m2 plan" if b["kind"] == "PLAN_AREA_M2" else "m3 at least"
    return f"beside: {_fmt(b['value'])} {u} ({b['basis']})"


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
    else:                                               # HELD_BLANK / LOWER_ONLY
        ln["evidence_state"], ln["measured_net"], ln["gross"], ln["bounded_range"] = BLANK, None, None, None
        ln["rfi"] = {"question": e["question"][:400], "blocks": [b["line_id"]]}
        head = ("HELD, LOWER END ONLY (blank)" if a == "LOWER_ONLY" else "HELD BLANK") + "; " + _beside_text(
            e["beside"])
        after = {"beside": e["beside"]}
    ln["deductions"], ln["additions"] = [], []
    ln["calculation"] = dict(ln["calculation"], formula=(
        f"{METHOD}: {head} = {e['member']}: {e['basis']}" + (f"; {e['why_held']}" if e.get("why_held") else ""))[:1500])
    inp = ln["calculation"]["inputs"] = dict(ln["calculation"].get("inputs") or {})
    inp[REC_KEY] = _rec(srcs, action=a, member=e["member"], was=was, after=after, basis=e["basis"],
                        why_held=(e.get("why_held") or "")[:600], beside=e.get("beside"),
                        set_aside=e.get("set_aside"), remeasure=e.get("remeasure"),
                        freelancer_beside=e.get("freelancer_beside"))
    A305._note(ln, f"{METHOD}: {head[:200]} (was {A302._q(A30._qty(b))}); NOT RELEASED")
    return _fin(ln)


def changes_for(doc, prev):
    """-> (changes, log). CONFIRM entries are asserted on the candidate line and change nothing."""
    if not doc:
        return [], {"piece": "T661", "state": "NO_PROJECT_INPUT"}
    if any(((ln.get("calculation") or {}).get("inputs") or {}).get(REC_KEY) for ln in prev):
        raise InputsError("the candidate already carries V3.0.62 records (applied once)")
    by = {ln["line_id"]: ln for ln in prev}
    S = doc["_sources"]
    changes = []
    log = {"piece": "T661", "state": "RUN", "sources": doc["sources"], "by_action": {}, "lines": 0,
           "confirmed": []}
    for e in doc["_entries"]:
        b = by.get(e["line_id"])
        _assert_bound(b, e)
        log["by_action"][e["action"]] = log["by_action"].get(e["action"], 0) + 1
        if e["action"] == "CONFIRM":
            log["confirmed"].append(e["line_id"])
            continue
        srcs = [S[t] for t in e["source_tasks"]]
        after = _restate(b, e, srcs)
        held = None
        if e["action"] != "VALUE":
            q = A30._qty(after)
            held = [{"what": e["member"], "why": (e.get("why_held") or "")[:300],
                     "range": [q["low"], q["high"]] if q["low"] is not None else None,
                     "beside": e.get("beside")}]
        changes.append(A305._change(P_CL, "CHANGE", b, after, drawing_reference="; ".join(s["file"] for s in srcs),
                                    held=held, downstream=[], verification=A3036._ver(srcs),
                                    evidence_status="VERIFIED" if e["action"] == "VALUE" else "HELD",
                                    codes=[P_CL], group=b["item_code"], step=e["action"]))
    log["lines"] = len(changes)
    return changes, log


# ================================================================================================ checks
def _bucket(ln):
    q = A30._qty(ln)
    if q["value"] is not None and ln["evidence_state"] != "BLOCKED_RFI":
        return "released"
    return "bounded" if q["low"] is not None else "blocked"


def expected_totals(t0, changes):
    """the STR.CONC.*|m3 code totals the restatement must give, from the base totals and the changes alone"""
    want = {}
    for c in changes:
        k = f"{c['after']['item_code']}|{c['after']['unit']}"
        z = want.setdefault(k, dict(t0[k]))
        for ln, s in ((c["before"], -1), (c["after"], 1)):
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
            raise ValueError(f"{METHOD}: {k} totals {t0[k]} -> {a} are not the restatement {z}")
        if expect and k in expect:
            for f, v in expect[k].items():
                if abs(a[f] - v) > TOT_TOL:
                    raise ValueError(f"{METHOD}: {k} {f} {a[f]} is not the inputs' {v}")
        out[k] = {"base": t0[k], "v3_0_62": a}
    return out


def check_concrete(lines, before=None):
    """on finished lines: every V3.0.62 line is in the state its action names (BOUND bounded 0 < low <= high with an
    RFI; VALUE MEASURED > 0; HELD_BLANK / LOWER_ONLY blank with an RFI and the measure beside); with `before`, no
    STR.CONC line went from held to released except a VALUE line. -> summary"""
    out = {a: 0 for a in CHANGING}
    for ln in lines:
        rec = ((ln.get("calculation") or {}).get("inputs") or {}).get(REC_KEY)
        if not rec:
            continue
        a = rec["action"]
        r = _range(ln)
        ok = ln["item_code"].startswith(CODE_PREFIX) and ln["unit"] == UNIT
        if a == "BOUND":
            ok = ok and r is not None and 0 < r[0] <= r[1] + 1e-9 and ln.get("measured_net") is None and \
                bool((ln.get("rfi") or {}).get("question"))
        elif a == "VALUE":
            ok = ok and ln["evidence_state"] == VALUED and (ln.get("measured_net") or 0) > 0 and rec.get("remeasure")
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
    """-> (V3.0.62 lines, identity). Changed lines replace their candidate line in place; every other candidate line
    is byte-identical (asserted); the earlier versions' checks re-run on the result (the V3.0.61 set)."""
    sid = {ln["line_id"]: i for i, ln in enumerate(prev)}
    out = list(prev)
    repl = set()
    for c in changes:
        a = c["after"]
        if not a["item_code"].startswith(CODE_PREFIX) or a["unit"] != UNIT or c["action"] != "CHANGE":
            raise ValueError(f"{METHOD}: {c['action']} {a['item_code']} is not a change this version may make")
        i = sid.get(a["line_id"])
        if i is None or a["line_id"] in repl:
            raise ValueError(f"{METHOD}: a changed line is not a candidate line or changes twice")
        out[i] = a
        repl.add(a["line_id"])
    _o, i61 = A3061.integrate(out, [], for_lead)     # every V3.0.10 .. V3.0.61 family check, re-run on these lines
    ident = {"base_lines": len(prev), "v3_0_62_lines": len(out), "v3_0_62_rows": len(changes), "replaced": len(repl),
             "added": 0, "checks_v3_0_61": {k: v for k, v in i61.items() if k not in (
                 "base_lines", "v3_0_61_lines", "v3_0_61_rows", "replaced", "added", "outside_rows",
                 "outside_rows_identical_to_base", "outside_rows_sha256")},
             "concrete": check_concrete(out, prev)}
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
                     "after_v3_0_62": A30._qty(ref), "class": [rec["was"]["class"], line_class(ref)],
                     "evidence_status": c.get("evidence_status"), "still_held": c.get("held"),
                     "beside": rec.get("beside"), "set_aside": rec.get("set_aside"), "remeasure": rec.get("remeasure"),
                     "release_status": "NOT RELEASED", "basis": rec["basis"],
                     "owner_manual_method": PIECES[c["piece"]]["owner_manual_method"],
                     "drawing_derived_method": PIECES[c["piece"]]["drawing_method"],
                     "verification": c.get("verification") or {}, "rollback": ROLLBACK})
    return rows


LEDGER_CSV = ("version", "piece", "action", "line_id", "item_code", "floor", "member", "element_id", "unit", "v2_9",
              "base", "v3_0_62", "class", "beside", "evidence_status", "verification")
DIFF_CSV = ("line_id", "item_code", "floor", "element_id", "unit", "vs_base", "vs_released_v2_9", "v2_9", "base",
            "v3_0_62")


def ledger_csv(rows):
    def q(x):
        return A302._q(x) if x and (x.get("value") is not None or x.get("low") is not None or x.get("state")) else ""
    return A305._csv([{"version": r["version"], "piece": r["piece"], "action": r["action"], "line_id": r["line_id"],
                       "item_code": r["item_code"], "floor": r.get("floor") or "", "member": r.get("member") or "",
                       "element_id": r.get("element_id") or "", "unit": r["unit"],
                       "v2_9": q(r.get("before_released_v2_9")), "base": q(r.get("before_base")),
                       "v3_0_62": q(r.get("after_v3_0_62")), "class": " -> ".join(r["class"]),
                       "beside": _beside_text(r.get("beside")) if r.get("beside") else "",
                       "evidence_status": r["evidence_status"],
                       "verification": f"{r['verification'].get('task')} "
                                       f"{' '.join(x[:8] for x in r['verification'].get('merge_commits') or ())}"}
                      for r in rows], LEDGER_CSV)


def diff_rows(prev, new, released_lines=None):
    return [dict({k: v for k, v in d.items() if k != "v3_0_61"}, v3_0_62=d["v3_0_61"])
            for d in A3061.diff_rows(prev, new, released_lines)]


def write(out, prev, changes, log, released_lines=None, for_lead=(), expect_totals=None):
    """the V3_0_62_* files beside the base candidate's files. -> (file names, identity, ledger)."""
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
    ident = dict(ident, diff=dsum, confirmed=len(conf))
    moved = check_totals(A304.code_totals(prev), A304.code_totals(new), changes, expect_totals)
    led = {"schema": LEDGER_SCHEMA, "method": METHOD, "extends": EXTENDS, "candidate": CANDIDATE,
           "base": A30.BASE_METHOD, "released": A30.RELEASED_METHOD, "released_default": False, "rows": rows,
           "confirmed_unchanged": sorted(conf), "waiting_pieces": WAITING, "integration_package": True}
    run = {"method": METHOD, "policy": POLICY_ID, "extends": EXTENDS, "candidate": CANDIDATE,
           "base_method": A30.BASE_METHOD, "released_method": A30.RELEASED_METHOD, "released_default": False,
           "rollback": ROLLBACK, "identity": ident, "pieces": PIECES, "piece_logs": [log],
           "totals_moved_by_code": moved, "waiting_pieces": WAITING}
    files = {"V3_0_62_BOQ_LINES.json": BL.dumps(new),
             "V3_0_62_BOQ_LINES.csv": A30._lines_csv(new),
             "V3_0_62_INTEGRATION_LEDGER.json": A30._j(led),
             "V3_0_62_INTEGRATION_LEDGER.csv": ledger_csv(rows),
             "V3_0_62_DIFF.csv": A305._csv(diff, DIFF_CSV),
             "V3_0_62_RUN.json": A30._j(run)}
    for name, text in files.items():
        (out / name).write_text(text, encoding="utf-8")
    return sorted(files), ident, led


def policy_record():
    return {"method": METHOD, "extends": EXTENDS, "pieces": sorted(PIECES), "inputs_schema": INPUTS_SCHEMA,
            "released_default": False, "rollback": ROLLBACK, "actions": list(ACTIONS)}


__all__ = ["METHOD", "PIECES", "WAITING", "DEFAULT_GUARD_CLASS", "INPUTS_SCHEMA", "load_inputs", "changes_for",
           "check_concrete", "check_totals", "expected_totals", "integrate", "ledger_rows", "diff_rows", "write",
           "InputsError", "line_class"]
