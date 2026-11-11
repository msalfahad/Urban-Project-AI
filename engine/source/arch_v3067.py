"""ARCH_TAKEOFF_V3.0.67 (T-682, lane I, CONCRETE GATE B ROUND 6 integration package, the last concrete package before
masonry): the SAME opt-in BOQ candidate as ARCH_TAKEOFF_V3.0 .. V3.0.66 (engine.source.arch_v30, arch_v301 ..
arch_v3066), extended with ONE piece built from the Checker-merged T-678 ledger of concrete lines left HELD blank by
V3.0.66: lintels whose existence a LOWER BOUND of the soffit decides (R-T678-1), the planted column PC-2F the slab
outline 778 is (T-220), and the lower end of an annex roof column (R-T678-2):

  CONC_LEDGER   a named HELD concrete line is restated as the merged ledger states it, with the V3.0.63 states
                BOUND (both ends drawn-derived) and LOWER_ONLY (one end OPEN, R-T678-3: blank, its AT_LEAST m3
                figure beside, never a high invented for the open end); two records are new in V3.0.67:
                  assumption    a line whose EXISTENCE rests on an owner-approved fallback (the owner door-height
                                fallback, Q-55 C) carries it: status ASSUMED - OWNER-APPROVED, its source, the
                                assumed value, the spare it leaves, and the re-run trigger (the drawn value that
                                would reverse existence = assumed + spare) (Checker F-V678-1);
                  plane         a line whose soffit or top bound is transferred from a slab-top lower bound
                                (R-T678-2) carries the R-T682-1 plane record: ONE_PLANE in plan and in every
                                section read; a section step inside the plane, or one whose position is not stated,
                                is refused here too (Checker F-V678-2).

R-T682-2 (every villa; = R-T677-1 (a) .. (q) as written, plus): (r) existence that rests on an owner-approved
fallback is labelled ASSUMED - OWNER-APPROVED with its source and a re-run trigger stated as a number (assumed value +
spare), never silently DRAWING-CONFIRMED; (s) a bound transferred over a slab plane carries the plane record and is
refused when that record is not ONE_PLANE with every drawn section step outside the plane; (t) the V3.0.66 lintel
check (R-T677-1 (q)) governs the lintel lines V3.0.66 restated or added, this version's lintel check governs the lines
it restates, the V3.0.53 check every other lintel line; one lintel line per opening across all three; a lintel line
is restated only from a V3.0.53 BLANK record, HELD or FLAGGED (FLAGGED = 'room under some pieces only, which piece is
over the opening not read': a position-resolved soffit bound answers it), never from a REQUIRED (valued) one;
(u) released m3 does not move in this version (no VALUE, no REVALUE action is accepted).
Files: V3_0_67_BOQ_LINES.json / .csv, V3_0_67_INTEGRATION_LEDGER.json / .csv, V3_0_67_DIFF.csv, V3_0_67_RUN.json.
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
from engine.source import arch_v3065 as A3065
from engine.source import arch_v3066 as A3066

DEFAULT_GUARD_CLASS = "TOOLING"          # T-212: re-books Checker-merged member ledgers onto candidate lines
METHOD = "ARCH_TAKEOFF_V3.0.67"
EXTENDS = A3066.METHOD
CANDIDATE = A30.METHOD
POLICY_ID = "URBAN_BOQ_T682_ARCH_V3_0_67"
INPUTS_SCHEMA = "URBAN_V3067_INPUTS_V1"
LEDGER_SCHEMA = "URBAN_V3067_INTEGRATION_LEDGER_V1"
ROLLBACK = A30.ROLLBACK
InputsError = A3063.InputsError
_r = A3063._r
_fmt = A3063._fmt
RULE_ID, RULE_VERSION = "R-T682-2", "T-682"
REC_KEY = "concrete_ledger_v3067"
EARLIER_KEYS = A3066.EARLIER_KEYS + (A3066.REC_KEY,)
LINTEL_CODE, LINTEL_KEY = A3066.LINTEL_CODE, A3066.LINTEL_KEY
P_CL = "CONC_LEDGER"
ACTIONS = ("BOUND", "LOWER_ONLY")
CODE_PREFIX, UNIT = A3063.CODE_PREFIX, A3063.UNIT
BOUNDED, BLANK = A3063.BOUNDED, A3063.BLANK
TOT_TOL, BIND_TOL = A3063.TOT_TOL, A3063.BIND_TOL
OA = "ASSUMED - OWNER-APPROVED"
EXISTENCE_STATUS = ("DRAWING-CONFIRMED", OA)          # WORKFLOW_CONTROLS s.5 (existence of the member)
PLANE_RULE = "R-T682-1"
BLANK_DECISIONS = ("HELD", "FLAGGED")                 # the R-T487-1 blank lintel states (V3.0.53); REQUIRED is valued
line_class = A3063.line_class

PIECES = {
    P_CL: {"module": "engine/source/arch_v3067.py (named HELD concrete lines restated from the Checker-merged T-678 "
                     "ledger: lintels whose existence a soffit lower bound decides, the planted column PC-2F, an "
                     "annex roof column's lower end; nothing else moves, released m3 never)",
           "policy": "CONCRETE_GATE_B_V6", "rule_id": "R-T678-1..3 / R-T682-1 (R-T682-2)",
           "owner_rules": ["owner lintel rule 2026-11-02 (precast pieces kept beside; one per opening)",
                           "ST p.13 LINTEL SCHEDULE (RC cast: B = wall width, D by width band, MIN 40 cm bearing)",
                           "Q-55 C (owner door-height fallback 2.20 m where no head is printed)",
                           "UP-CONC-JOINT-001 (column top = slab top; a member billed through owns the joint)",
                           "UP-QTY-STATUS-001 (held is blank or bounded, never 0)",
                           "ERS s.2-5 (drawn element first; one physical element once)"],
           "owner_manual_method": "lintel: opening width + 2 x 0.15 bearing -> the shortest standard precast piece "
                                  "(1.20 / 1.50 / 2.50 / 3.00 / 4.00 m, kept beside, never the m3); column: section x "
                                  "storey height",
           "drawing_method": "the merged T-678 ledger: a lintel exists where the LOWER bound of every soffit over the "
                             "opening's own extent leaves head + D + bed (R-T678-1), length 0.40 bearing each side .. "
                             "the drawn jamb ceilings (R-T673-3), an end with no recorded stopper OPEN (R-T678-3); the "
                             "annex slab top bounded below by a drawn head under a printed beam on one plane (R-T678-2, "
                             "the plane checked in plan and section, R-T682-1); PC-2F = the 778 outline, drawn 20x40 "
                             "vs printed 'P.C 20x50' (CONFLICT range) x base to the soffit of the beam billed through"},
}
WAITING = {k: v for k, v in A3066.WAITING.items() if k not in ("T677_LINTEL_DESIGNER_OPEN",)}
WAITING.update({
    "T682_LINTEL_OPEN": "19 STR.CONC.LINTEL lines stay HELD blank: 6 DESIGNER ITEM (T-673 census) and 13 OPEN BOUND "
                        "each naming its missing datum (T-678 census): W04 / W08 annex slab top (Q-54 B), W11 / W12 "
                        "sill level, W25 / W27 stair-shaft member level (R-T228-3), D-2F-02 BM-2F-017 depth (D-04), "
                        "D-GF-05 side-passage FFL + START stopper, D-GF-08 unsized lift tie beam (ST p.8 n.19), "
                        "D-GF-14 no run / jamb record, D-1F-01 / D-1F-09 dome wall top (T-227), A-GF-01 arched crown",
    "T682_LINTEL_LOWER_ONLY": "D-1F-06 (END crossing wall) and D-GF-04 (END search limit, no extension): existence "
                              "REQUIRED, quantity lower end only (blank, AT_LEAST beside); the open end has no "
                              "recorded stopper (R-T678-3): never closed by a guess",
    "T682_ANNEX_COLUMNS": "the 4 other GF annex column lines (L-694a75c8, L-c0b3340a, L-e6c1c9a7, L-9f5a6470) take "
                          "the same height bound 3.294 .. 4.05 m once D-66 settles their section: not here",
    "T682_OWNER_FALLBACK": "6 lintel lines exist on the Q-55 C door-height fallback (ASSUMED - OWNER-APPROVED): a "
                           "drawn or printed head above each line's re-run trigger reverses existence: re-run T-678 "
                           "R-T678-1 for that opening",
})


# ================================================================================================ inputs
def _assumption(a, w):
    if not isinstance(a, dict):
        raise InputsError(f"{w}: assumption must be a record")
    A3063._need(a, ("status", "source", "what", "assumed_m", "spare_m", "trigger_m", "rerun_trigger"), w)
    if a["status"] != OA:
        raise InputsError(f"{w}: an assumption is {OA!r} (R-T682-2 (r)), not {a['status']!r}")
    for k in ("assumed_m", "spare_m", "trigger_m"):
        x = a[k]
        if isinstance(x, bool) or not isinstance(x, (int, float)) or x != x or x < 0 or x > 20:
            raise InputsError(f"{w}: assumption {k} {x!r} not metres")
    if abs(a["assumed_m"] + a["spare_m"] - a["trigger_m"]) > 1e-6:
        raise InputsError(f"{w}: re-run trigger {a['trigger_m']} is not assumed {a['assumed_m']} + spare "
                          f"{a['spare_m']} (R-T682-2 (r))")
    if f"{a['trigger_m']:.3f}" not in a["rerun_trigger"]:
        raise InputsError(f"{w}: the re-run trigger text does not state {a['trigger_m']:.3f}")
    return dict(a)


def _plane(p, w):
    """R-T682-2 (s): the R-T682-1 plane record a transferred bound rests on."""
    if not isinstance(p, dict) or p.get("rule") != f"{PLANE_RULE} 1.0.0" or not p.get("outline"):
        raise InputsError(f"{w}: a transferred slab bound carries the {PLANE_RULE} plane record")
    if p.get("state") != "ONE_PLANE":
        raise InputsError(f"{w}: plane state {p.get('state')!r}: a stepped or unchecked plane transfers nothing")
    if not p.get("sections_checked"):
        raise InputsError(f"{w}: no section read for the plane (F-V678-2: the plan alone does not make one plane)")
    for s in p.get("steps_outside") or ():
        if not s.get("evidence") or not s.get("section"):
            raise InputsError(f"{w}: a step outside the plane names its section and evidence")
    for s in p.get("section_steps") or ():
        if s.get("inside_plane") is not False and float(s.get("step_m") or 0) > 0:
            raise InputsError(f"{w}: section {s.get('section')} step inside the plane or unplaced: refused")
    if p.get("s_lo_m") is None:
        raise InputsError(f"{w}: the plane record states the transferred lower bound s_lo_m")
    return dict(p)


def load_inputs(doc, project_id=None):
    """URBAN_V3067_INPUTS_V1 -> the validated doc.
    {"schema", "project_id", "sources": [{"task", "file", "sha256", "merge_commit", "checker_run"}],
     "expect_totals": {"<code>|m3": {...}} (optional, asserted on the code totals),
     "entries": [V3.0.63 BOUND or LOWER_ONLY entry on a HELD blank line + "existence" {status DRAWING-CONFIRMED |
                 ASSUMED - OWNER-APPROVED, basis} + "assumption" (when existence is ASSUMED - OWNER-APPROVED)
                 {status, source, what, assumed_m, spare_m, trigger_m, rerun_trigger} + "plane" (when a slab bound
                 is transferred) {rule R-T682-1 1.0.0, state ONE_PLANE, outline, sections_checked, steps_outside,
                 section_steps, s_lo_m}]}"""
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
        w = f"{a} {x.get('line_id')}"
        if a not in ACTIONS:
            raise InputsError(f"entry action {a!r}: V3.0.67 restates HELD lines to BOUND or LOWER_ONLY only "
                              f"(R-T682-2 (u): released m3 does not move)")
        if (x.get("expect") or {}).get("class") != "HELD" or (x.get("expect") or {}).get("low") is not None:
            raise InputsError(f"{w}: only a HELD blank line is restated here")
        e = A3063._entry(x, srcs)
        ex = x.get("existence") or {}
        if ex.get("status") not in EXISTENCE_STATUS or not ex.get("basis"):
            raise InputsError(f"{w}: existence status {ex.get('status')!r} with its basis (WORKFLOW_CONTROLS s.5)")
        if ex["status"] == OA:
            e["assumption"] = _assumption(x.get("assumption"), w)
        elif x.get("assumption") is not None:
            raise InputsError(f"{w}: an assumption record belongs to an {OA} existence")
        if x.get("plane") is not None:
            e["plane"] = _plane(x["plane"], w)
        e["existence"] = dict(ex)
        ents.append(e)
    if not ents:
        raise InputsError("no entry in the inputs")
    seen = set()
    for e in ents:
        if e["line_id"] in seen:
            raise InputsError(f"{e['line_id']}: named twice (one line, one restatement)")
        seen.add(e["line_id"])
    return dict(doc, _sources=srcs, _entries=ents)


# ================================================================================================ lines
def _rec(srcs, **kw):
    return dict({"piece": P_CL, "policy": PIECES[P_CL]["policy"], "tasks": [s["task"] for s in srcs],
                 "ledgers": [s["file"] for s in srcs], "ledger_sha256": [s["sha256"] for s in srcs],
                 "merge_commits": [s["merge_commit"] for s in srcs], "checker_runs": [s["checker_run"] for s in srcs],
                 "rule_id": RULE_ID, "rule_version": RULE_VERSION, "release_status": "NOT RELEASED"}, **kw)


def _supersede(inp, code=None):
    keys = EARLIER_KEYS + ((LINTEL_KEY,) if code == LINTEL_CODE else ())
    return {k: inp.pop(k) for k in keys if k in inp}


def _ex_text(e):
    t = f"existence {e['existence']['status']}"
    a = e.get("assumption")
    if a:
        t += f" ({a['source']}: {a['what']}; re-run if {a['rerun_trigger']})"
    if e.get("plane"):
        t += f"; plane {e['plane']['state']} ({PLANE_RULE}, sections {', '.join(e['plane']['sections_checked'])})"
    return t


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
        head = f"HELD (BOUNDED) {_fmt(lo)} .. {_fmt(hi)} m3"
        after = {"low": _r(lo), "high": _r(hi)}
    else:                                               # LOWER_ONLY
        ln["evidence_state"], ln["measured_net"], ln["gross"], ln["bounded_range"] = BLANK, None, None, None
        head = "HELD, LOWER END ONLY (blank); " + A3063._beside_text(e["beside"])
        after = {"beside": e["beside"]}
    ln["rfi"] = {"question": e["question"][:400], "blocks": [b["line_id"]]}
    ln["deductions"], ln["additions"] = [], []
    ln["calculation"] = dict(ln["calculation"], formula=(
        f"{METHOD}: {head} = {e['member']}: {e['basis']}; {_ex_text(e)}"
        + (f"; {e['why_held']}" if e.get("why_held") else ""))[:1500])
    inp = ln["calculation"]["inputs"] = dict(ln["calculation"].get("inputs") or {})
    sup = _supersede(inp, b["item_code"])
    if b["item_code"] == LINTEL_CODE:
        lr = sup.get(LINTEL_KEY) or {}
        if lr.get("decision") not in BLANK_DECISIONS or not lr.get("opening_id"):
            raise InputsError(f"{a} {b['line_id']}: a lintel line is restated only from its V3.0.53 blank record "
                              f"(HELD / FLAGGED), never a REQUIRED one (found {lr.get('decision')!r})")
        if A3066.REC_KEY in sup:
            raise InputsError(f"{a} {b['line_id']}: a lintel line V3.0.66 restated is not restated again here")
    inp[REC_KEY] = _rec(srcs, action=a, member=e["member"], was=was, after=after, basis=e["basis"],
                        why_held=(e.get("why_held") or "")[:600], beside=e.get("beside"),
                        existence=e["existence"], assumption=e.get("assumption"), plane=e.get("plane"),
                        superseded=sup, freelancer_beside=e.get("freelancer_beside"))
    A305._note(ln, f"{METHOD}: {head[:300]} (was {A302._q(A30._qty(b))}); NOT RELEASED")
    return A3063._fin(ln)


def changes_for(doc, prev):
    """-> (changes, log)."""
    if not doc:
        return [], {"piece": "T682", "state": "NO_PROJECT_INPUT"}
    if any(((ln.get("calculation") or {}).get("inputs") or {}).get(REC_KEY) for ln in prev):
        raise InputsError("the candidate already carries V3.0.67 records (applied once)")
    by = {ln["line_id"]: ln for ln in prev}
    S = doc["_sources"]
    changes = []
    log = {"piece": "T682", "state": "RUN", "sources": doc["sources"], "by_action": {}, "lines": 0,
           "assumed_owner_approved": [], "plane_transferred": []}
    for e in doc["_entries"]:
        b = by.get(e["line_id"])
        A3063._assert_bound(b, e)
        log["by_action"][e["action"]] = log["by_action"].get(e["action"], 0) + 1
        srcs = [S[t] for t in e["source_tasks"]]
        after = _restate(b, e, srcs)
        if e.get("assumption"):
            log["assumed_owner_approved"].append({"line_id": e["line_id"], "trigger_m": e["assumption"]["trigger_m"]})
        if e.get("plane"):
            log["plane_transferred"].append(e["line_id"])
        q = A30._qty(after)
        held = [{"what": e["member"], "why": (e.get("why_held") or "")[:300],
                 "range": [q["low"], q["high"]] if q["low"] is not None else None, "beside": e.get("beside")}]
        changes.append(A305._change(P_CL, "CHANGE", b, after, drawing_reference="; ".join(s["file"] for s in srcs),
                                    held=held, downstream=[], verification=A3036._ver(srcs), evidence_status="HELD",
                                    existence_status=e["existence"]["status"], codes=[P_CL], group=b["item_code"],
                                    step=e["action"]))
    log["lines"] = len(changes)
    return changes, log


# ================================================================================================ checks
def expected_totals(t0, changes):
    return A3065.expected_totals(t0, changes)


def check_totals(t0, t1, changes, expect=None):
    """only STR.CONC.*|m3 code totals move, each exactly by the restatement, released never (R-T682-2 (u))"""
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
        if abs(a["released"] - t0[k]["released"]) > TOT_TOL:
            raise ValueError(f"{METHOD}: {k} released moved {t0[k]['released']} -> {a['released']}")
        if expect and k in expect:
            for f, v in expect[k].items():
                if abs(a[f] - v) > TOT_TOL:
                    raise ValueError(f"{METHOD}: {k} {f} {a[f]} is not the inputs' {v}")
        out[k] = {"base": t0.get(k), "v3_0_67": a}
    return out


def check_concrete(lines, before=None):
    """on finished lines: every V3.0.67 line is in the state its action names, carries its existence status (and
    its assumption / plane record where it rests on one); with `before`, no STR.CONC line changed class to RELEASED
    and no released quantity moved. -> summary"""
    out = {a: 0 for a in ACTIONS}
    out.update(assumed=0, plane=0)
    for ln in lines:
        rec = ((ln.get("calculation") or {}).get("inputs") or {}).get(REC_KEY)
        if not rec:
            continue
        a = rec["action"]
        r = A3063._range(ln)
        ok = ln["item_code"].startswith(CODE_PREFIX) and ln["unit"] == UNIT and rec["was"]["class"] == "HELD" and \
            bool((ln.get("rfi") or {}).get("question")) and ln.get("measured_net") is None
        if a == "BOUND":
            ok = ok and r is not None and 0 < r[0] <= r[1] + 1e-9
        elif a == "LOWER_ONLY":
            ok = ok and ln["evidence_state"] == BLANK and r is None and \
                (rec.get("beside") or {}).get("kind") == "AT_LEAST_M3"
        else:
            ok = False
        ex = rec.get("existence") or {}
        ok = ok and ex.get("status") in EXISTENCE_STATUS
        if ex.get("status") == OA:
            ok = ok and bool((rec.get("assumption") or {}).get("rerun_trigger"))
            out["assumed"] += 1
        if rec.get("plane") is not None:
            ok = ok and rec["plane"].get("state") == "ONE_PLANE"
            out["plane"] += 1
        if not ok:
            raise ValueError(f"{METHOD}: {ln['line_id']}: a {a} line is not in its state")
        out[a] += 1
    if before is not None:
        b = {x["line_id"]: x for x in before}
        for ln in lines:
            o = b.get(ln["line_id"])
            if o is None or not ln["item_code"].startswith(CODE_PREFIX):
                continue
            if line_class(ln) == "RELEASED" and (line_class(o) != "RELEASED" or
                                                 o.get("measured_net") != ln.get("measured_net")):
                raise ValueError(f"{METHOD}: {ln['line_id']}: released concrete moved (R-T682-2 (u))")
    return out


def _governed(ln):
    return bool(((ln.get("calculation") or {}).get("inputs") or {}).get(REC_KEY))


def check_lintels(lines):
    """R-T682-2 (t): a lintel line this version restated keeps its V3.0.53 blank record under `superseded` only;
    one lintel line per opening across the V3.0.53 / V3.0.66 / V3.0.67 records. -> summary"""
    ops, out = {}, {"restated_v3_0_67": 0, "other": 0}
    for ln in lines:
        if ln["item_code"] != LINTEL_CODE:
            continue
        inp = (ln.get("calculation") or {}).get("inputs") or {}
        rec = inp.get(REC_KEY)
        if rec:
            lr = (rec.get("superseded") or {}).get(LINTEL_KEY) or {}
            if inp.get(LINTEL_KEY) or lr.get("decision") not in BLANK_DECISIONS:
                raise ValueError(f"{METHOD}: {ln['line_id']}: a restated lintel line keeps its V3.0.53 blank record "
                                 f"(HELD / FLAGGED) under superseded only")
            o = lr.get("opening_id")
            out["restated_v3_0_67"] += 1
        else:
            r66 = inp.get(A3066.REC_KEY)
            if r66 and r66.get("action") == A3066.SHARED:
                out["other"] += 1
                continue
            src = ((r66.get("superseded") or {}).get(LINTEL_KEY) if r66 else inp.get(LINTEL_KEY)) or {}
            o = src.get("opening_id")
            out["other"] += 1
        if not o or o in ops:
            raise ValueError(f"{METHOD}: lintel opening {o!r} has no record or two lintel lines")
        ops[o] = ln["line_id"]
    return out


# ================================================================================================ integrate / write
def integrate(prev, changes, for_lead=()):
    """-> (V3.0.67 lines, identity). Changed lines replace their candidate line in place; every other candidate line
    is byte-identical (asserted); the earlier checks re-run: the V3.0.63 chain on every line no later version
    governs, the V3.0.64 / V3.0.65 / V3.0.66 state checks, the V3.0.66 lintel check on the lintel lines it governs."""
    sid = {ln["line_id"]: i for i, ln in enumerate(prev)}
    out = list(prev)
    repl = set()
    for c in changes:
        a = c["after"]
        if not a["item_code"].startswith(CODE_PREFIX) or a["unit"] != UNIT:
            raise ValueError(f"{METHOD}: {a['item_code']} is not a code this version may touch")
        if c["action"] != "CHANGE":
            raise ValueError(f"{METHOD}: action {c['action']} (V3.0.67 adds no line)")
        i = sid.get(a["line_id"])
        if i is None or a["line_id"] in repl:
            raise ValueError(f"{METHOD}: a changed line is not a candidate line or changes twice")
        out[i] = a
        repl.add(a["line_id"])
    if len({ln["line_id"] for ln in out}) != len(out):
        raise ValueError(f"{METHOD}: a BOQ line id appears twice")
    view = [ln for ln in out if not _governed(ln) and not A3066._governed(ln)]
    _o, i63 = A3063.integrate(view, [], for_lead)
    i63 = {k: v for k, v in i63.items() if k not in (
        "base_lines", "v3_0_63_lines", "v3_0_63_rows", "replaced", "added", "outside_rows",
        "outside_rows_identical_to_base", "outside_rows_sha256")}
    v66 = [ln for ln in out if not _governed(ln)]
    i66 = {"checks_v3_0_63": i63, "concrete_v3_0_64": A3064.check_concrete(out),
           "concrete_v3_0_65": A3065.check_concrete(out), "concrete_v3_0_66": A3066.check_concrete(out),
           "lintels_v3_0_66": A3066.check_lintels(v66), "governed_outside_v3_0_53": len(out) - len(view)}
    ident = {"base_lines": len(prev), "v3_0_67_lines": len(out), "v3_0_67_rows": len(changes), "replaced": len(repl),
             "added": 0, "checks_v3_0_66": i66, "concrete": check_concrete(out, prev), "lintels": check_lintels(out)}
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
                     "after_v3_0_67": A30._qty(ref), "class": [rec["was"]["class"], line_class(ref)],
                     "evidence_status": c.get("evidence_status"), "existence": rec.get("existence"),
                     "assumption": rec.get("assumption"), "plane": rec.get("plane"), "still_held": c.get("held"),
                     "beside": rec.get("beside"), "superseded_record_keys": sorted(rec.get("superseded") or {}),
                     "release_status": "NOT RELEASED", "basis": rec["basis"],
                     "owner_manual_method": PIECES[c["piece"]]["owner_manual_method"],
                     "drawing_derived_method": PIECES[c["piece"]]["drawing_method"],
                     "verification": c.get("verification") or {}, "rollback": ROLLBACK})
    return rows


LEDGER_CSV = ("version", "piece", "action", "line_id", "item_code", "floor", "member", "element_id", "unit", "v2_9",
              "base", "v3_0_67", "class", "existence", "beside", "evidence_status", "verification")
DIFF_CSV = ("line_id", "item_code", "floor", "element_id", "unit", "vs_base", "vs_released_v2_9", "v2_9", "base",
            "v3_0_67")


def ledger_csv(rows):
    def q(x):
        return A302._q(x) if x and (x.get("value") is not None or x.get("low") is not None or x.get("state")) else ""

    def ex(r):
        t = (r.get("existence") or {}).get("status") or ""
        if r.get("assumption"):
            t += f" ({r['assumption']['source']}; trigger {r['assumption']['trigger_m']:.3f} m)"
        if r.get("plane"):
            t += f"; plane {r['plane']['state']}"
        return t
    return A305._csv([{"version": r["version"], "piece": r["piece"], "action": r["action"], "line_id": r["line_id"],
                       "item_code": r["item_code"], "floor": r.get("floor") or "", "member": r.get("member") or "",
                       "element_id": r.get("element_id") or "", "unit": r["unit"],
                       "v2_9": q(r.get("before_released_v2_9")), "base": q(r.get("before_base")),
                       "v3_0_67": q(r.get("after_v3_0_67")), "class": " -> ".join(r["class"]), "existence": ex(r),
                       "beside": A3063._beside_text(r["beside"]) if r.get("beside") else "",
                       "evidence_status": r["evidence_status"],
                       "verification": f"{r['verification'].get('task')} "
                                       f"{' '.join(x[:8] for x in r['verification'].get('merge_commits') or ())}"}
                      for r in rows], LEDGER_CSV)


def diff_rows(prev, new, released_lines=None):
    return [dict({k: v for k, v in d.items() if k != "v3_0_66"}, v3_0_67=d["v3_0_66"])
            for d in A3066.diff_rows(prev, new, released_lines)]


def write(out, prev, changes, log, released_lines=None, for_lead=(), expect_totals=None):
    """the V3_0_67_* files beside the base candidate's files. -> (file names, identity, ledger)."""
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
    if any(d["vs_base"] == "ADDED" for d in diff):
        raise ValueError(f"{METHOD}: a line was added")
    dsum = {}
    for d in diff:
        dsum.setdefault("vs_base", {}).setdefault(d["vs_base"], 0)
        dsum["vs_base"][d["vs_base"]] += 1
        if d["vs_released_v2_9"] is not None:
            dsum.setdefault("vs_released_v2_9", {}).setdefault(d["vs_released_v2_9"], 0)
            dsum["vs_released_v2_9"][d["vs_released_v2_9"]] += 1
    ident = dict(ident, diff=dsum, assumed_owner_approved=log.get("assumed_owner_approved") or [],
                 plane_transferred=log.get("plane_transferred") or [])
    moved = check_totals(A304.code_totals(prev), A304.code_totals(new), changes, expect_totals)
    led = {"schema": LEDGER_SCHEMA, "method": METHOD, "extends": EXTENDS, "candidate": CANDIDATE,
           "base": A30.BASE_METHOD, "released": A30.RELEASED_METHOD, "released_default": False, "rows": rows,
           "waiting_pieces": WAITING, "integration_package": True}
    run = {"method": METHOD, "policy": POLICY_ID, "extends": EXTENDS, "candidate": CANDIDATE,
           "base_method": A30.BASE_METHOD, "released_method": A30.RELEASED_METHOD, "released_default": False,
           "rollback": ROLLBACK, "identity": ident, "pieces": PIECES, "piece_logs": [log],
           "totals_moved_by_code": moved, "waiting_pieces": WAITING}
    files = {"V3_0_67_BOQ_LINES.json": BL.dumps(new),
             "V3_0_67_BOQ_LINES.csv": A30._lines_csv(new),
             "V3_0_67_INTEGRATION_LEDGER.json": A30._j(led),
             "V3_0_67_INTEGRATION_LEDGER.csv": ledger_csv(rows),
             "V3_0_67_DIFF.csv": A305._csv(diff, DIFF_CSV),
             "V3_0_67_RUN.json": A30._j(run)}
    for name, text in files.items():
        (out / name).write_text(text, encoding="utf-8")
    return sorted(files), ident, led


def policy_record():
    return {"method": METHOD, "extends": EXTENDS, "pieces": sorted(PIECES), "inputs_schema": INPUTS_SCHEMA,
            "released_default": False, "rollback": ROLLBACK, "actions": list(ACTIONS)}


__all__ = ["METHOD", "PIECES", "WAITING", "DEFAULT_GUARD_CLASS", "INPUTS_SCHEMA", "load_inputs", "changes_for",
           "check_concrete", "check_totals", "expected_totals", "integrate", "ledger_rows", "diff_rows", "write",
           "InputsError", "line_class"]
