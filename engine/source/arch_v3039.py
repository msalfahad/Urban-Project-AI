"""ARCH_TAKEOFF_V3.0.39 (T-429): the SAME opt-in BOQ candidate as ARCH_TAKEOFF_V3.0 .. V3.0.38 (engine.source.arch_v30,
arch_v301 .. arch_v3038), extended with ONE Checker-verified piece: the stair TREAD / STEP binding (T-425 MERGED
6f159091, with the governing count of the ST-01 winder turn from T-434 MERGED a6b325b3).

  TREAD_BINDING  every candidate stair reading (FIN.MARBLE.TREAD m2 = B7-02, FIN.STAIR.STEP_LM lm = B7-06, and the
                 FIN.MARBLE.RISER line of a superseded / held reading, B7-03) is bound to ONE drawn physical flight with
                 a role (OWN / PARTIAL / SEEN_THROUGH); per flight exactly one reading carries the valued tread and step
                 lines (the carrier). The merged binding table names one action per line:
                   KEEP       the line is right as it stands: asserted (stale binding refused), never rewritten;
                   CORRECT    the carrier takes the drawn figure (drawn tread fronts x drawn going x drawn width; step lm =
                              treads x width), same line id; a tread whose going is drawn on no sheet keeps its piece and
                              step lm, its m2 stays HELD by name beside the valued line (never a uniform-going default);
                   SUPERSEDE  a SEEN_THROUGH reading of a flight valued on another plan (DOUBLE_COUNT) or a PARTIAL
                              reading folded into its carrier (FOLDED): listed, no quantity (NOT_APPLICABLE_WITH_EVIDENCE),
                              owned by the carrier line it repeats, never deleted;
                   HOLD       a reading of a flight the owner holds (winder turn S-9, curved part Q-50 A cond): BLOCKED_RFI
                              blank with the reason and the figure(s) beside, never 0, never valued.

R-T429-1 (every villa; integrates R-T425-1 .. 3, R-T434-1 .. 3 and Checker finding F-C-T425-1): ONE physical flight,
ONE valued tread line and ONE valued step line. (a) Cross-plan class by LEVEL: two readings on different plans whose
physical flights span the SAME levels are the same flight (SEEN_THROUGH): at most one of them is valued, the other is
SUPERSEDED; a repeat is a new flight (STACKED) only when its level span differs. (b) The carrier's tread count is the
drawn fronts (both layers), never "lines - 1". (c) A held flight is never valued in any reading. (d) Held is never 0.

Nothing else moves: every V3.0.38 line not named by the inputs is byte-identical (asserted); totals move only in the
codes this piece owns (asserted). Files: V3_0_39_BOQ_LINES.json / .csv, V3_0_39_INTEGRATION_LEDGER.json / .csv,
V3_0_39_DIFF.csv, V3_0_39_RUN.json. Nothing here names a project, a sheet, a layer or a coordinate.
"""

from __future__ import annotations

import copy
import hashlib

from engine.source import arch_v30 as A30
from engine.source import arch_v302 as A302
from engine.source import arch_v304 as A304
from engine.source import arch_v305 as A305
from engine.source import arch_v3018 as A3018
from engine.source import arch_v3030 as A3030
from engine.source import arch_v3031 as A3031
from engine.source import arch_v3032 as A3032
from engine.source import arch_v3033 as A3033
from engine.source import arch_v3034 as A3034
from engine.source import arch_v3035 as A3035
from engine.source import arch_v3036 as A3036
from engine.source import arch_v3038 as A3038

DEFAULT_GUARD_CLASS = "TOOLING"          # T-212: re-books checker-merged ledgers; adds no default value
METHOD = "ARCH_TAKEOFF_V3.0.39"
EXTENDS = A3038.METHOD
CANDIDATE = A30.METHOD
POLICY_ID = "URBAN_BOQ_T429_ARCH_V3_0_39"
INPUTS_SCHEMA = "URBAN_V3039_INPUTS_V1"
LEDGER_SCHEMA = "URBAN_V3039_INTEGRATION_LEDGER_V1"
ROLLBACK = A30.ROLLBACK
InputsError = A3031.InputsError
_r = A3018._r
_fmt = A3030._fmt
RULE_ID, RULE_VERSION = "R-T429-1", "T-429"
REC_KEY = "tread_binding_v3039"
PIECE = "TREAD_BINDING"
DC = "DRAWING-CONFIRMED"
TOL = 0.0006                                 # the merged table prints 3 .. 6 decimals; the candidate 6

TREAD, STEP, RISER = "FIN.MARBLE.TREAD", "FIN.STAIR.STEP_LM", "FIN.MARBLE.RISER"
CODE_OF = {"B7-02": (TREAD, "m2"), "B7-06": (STEP, "lm"), "B7-03": (RISER, "m2")}
OWN_CODES = (TREAD, STEP, RISER)
ROLES = ("OWN", "PARTIAL", "SEEN_THROUGH")
ACTIONS = ("KEEP", "CORRECT", "SUPERSEDE", "HOLD")
SUPERSEDE_KINDS = ("DOUBLE_COUNT", "FOLDED")
EVIDENCE_OK = ("VERIFIED", DC)
VALUED = ("MEASURED", "SOURCE_DERIVED", "PROVISIONAL")

PIECES = {
    PIECE: {"module": "engine/source/arch_v3039.py (one physical flight, one valued tread and step line; superseded "
                      "readings listed without a quantity; held flights blank with the figure beside)",
            "policy": "TREAD_BINDING_V1", "rule_id": "R-T425-1..3 + R-T434-1..3 (R-T429-1)",
            "owner_rules": ["OWNER_RULE_STAIRS_2026-10-24 s.1 (one verified stair geometry) and s.4 S-9 (winders never "
                            "generated; HELD blank)", "UP-STAIR-002 (drawing governs)", "UP-STAIR-005 (landing polygons)",
                            "UP-STAIR-008 (commercial step lm)", "Q-46 A (section A-A counts for ST-01)",
                            "Q-50 A cond (round stair: curved part HELD)", "T-184 R-STAIR-CONT-1 (no flight leaves 2F)",
                            "UP-QTY-STATUS-001 (held is blank, never 0)"],
            "owner_manual_method": "owner method: tread marble = drawn treads x going x stair width; the commercial "
                                   "step basis = number of steps x width (UP-STAIR-008); every flight once; winders "
                                   "and the curved part of a round stair HELD (S-9, Q-50)",
            "drawing_method": "each candidate reading bound to a drawn flight by handle (T-425: run positions, both "
                              "layers, levels); treads = drawn fronts; the governing count of the winder turn from "
                              "section A-A (T-434)"},
}
WAITING = dict(A3038.WAITING)
WAITING.update({
    "T429_WINDER_TURN": "ST-01 MS1-T winder turn: section A-A governs 5 winders (Q-46 A, T-434); the plans draw a 4-riser "
                        "fan: winder subdivision not drawn (S-9, A8): tread / step / riser HELD with their figures beside "
                        "(designer list C-ST-3)",
    "T429_ROUND_STAIR_CURVED": "ST-02 RS-C curved part: Q-50 A cond, reconstructed from the plans: tread / step HELD "
                               "with their figures beside (RFI-S27)",
    "T429_LAST_GOING": "ST-01 MS2-U: the 11th tread's going (the 2F floor edge) is drawn on no sheet: its m2 HELD beside "
                       "the valued line; the piece and its step lm stand on the drawn front",
    "T429_NOSING_BINDS_HERE": "B7-05 nosing (T-424) binds to this tread set: the landing nosing ST01-MS1T-N05 1.150 lm is "
                              "DRAWING-CONFIRMED (T-434); no B7-05 line exists in the candidate before T-424",
    "T429_ST02_STRAIGHT_PART": "ST-02 straight-part drawing conflict (arch GF frame 27 risers vs ST p.4 / arch 1F 28, "
                               "T-432): NOT settled here; RS-S / RS-LD / RS-A move only on the drawn tread fronts "
                               "(T-438)",
})


# ================================================================================================ inputs
def _need(s, keys, where):
    for k in keys:
        if s.get(k) in (None, ""):
            raise InputsError(f"{where}: {k} missing")


def _num(x, where, pos=False):
    if not isinstance(x, (int, float)) or isinstance(x, bool) or x != x:
        raise InputsError(f"{where}: {x!r} is not a number")
    if x < 0 or (pos and x == 0):
        raise InputsError(f"{where}: {x!r} is {'not positive' if pos else 'negative'}")
    return float(x)


def _levels(x, where):
    if not isinstance(x, (list, tuple)) or len(x) != 2:
        raise InputsError(f"{where}: levels [from, to] in metres")
    for v in x:
        if not isinstance(v, (int, float)) or isinstance(v, bool) or v != v:
            raise InputsError(f"{where}: level {v!r} is not a number")
    lo, hi = float(x[0]), float(x[1])
    if not hi > lo:
        raise InputsError(f"{where}: a flight rises (levels {x})")
    if hi - lo > 6.0:
        raise InputsError(f"{where}: {hi - lo} m in one flight is not a storey rise in metres (mm refused)")
    return (round(lo, 4), round(hi, 4))


def load_inputs(doc, project_id=None):
    """URBAN_V3039_INPUTS_V1 -> the validated doc.
    {"schema", "project_id", "sources": [{"task", "file", "sha256", "merge_commit", "checker_run"}],
     "flights": [{"flight", "stair", "levels": [from, to], "drawn_treads", "width", "held": None | {"cause", "count",
                  "source"}, "source_tasks"}],
     "readings": [{"line_id", "family": "B7-02"|"B7-06"|"B7-03", "reading", "flight", "role", "plan", "action",
                   "before", "after", "supersede": None | {"kind", "carrier_line"}, "held_beside": None | {"value",
                   "why"}, "beside": [{"value", "unit", "basis"}], "cause", "evidence_status", "source_tasks"}]}"""
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

    def tasks(r, where):
        if not r.get("source_tasks") or any(t not in srcs for t in r["source_tasks"]):
            raise InputsError(f"{where}: no merged source named")

    flights = {}
    for f in doc.get("flights") or ():
        where = f"flight {f.get('flight')}"
        _need(f, ("flight", "stair"), where)
        tasks(f, where)
        if f["flight"] in flights:
            raise InputsError(f"{where}: named twice")
        lv = _levels(f.get("levels"), where)
        n = f.get("drawn_treads")
        if not isinstance(n, int) or isinstance(n, bool) or n <= 0:
            raise InputsError(f"{where}: drawn tread count {n!r} (a count of drawn fronts, never 0)")
        w = _num(f.get("width"), f"{where} width", True)
        if w > 5:
            raise InputsError(f"{where}: width {w} is not metres (mm refused)")
        h = f.get("held")
        if h is not None:
            _need(h, ("cause", "source"), f"{where} held")
        flights[f["flight"]] = dict(f, _levels=lv, _w=w)
    if not flights:
        raise InputsError("no flight in the inputs")
    reads, ids = [], set()
    for r in doc.get("readings") or ():
        where = f"reading {r.get('line_id')}"
        _need(r, ("line_id", "family", "reading", "flight", "role", "plan", "action", "evidence_status"), where)
        tasks(r, where)
        if r["line_id"] in ids:
            raise InputsError(f"{where}: named twice (one line, one action)")
        ids.add(r["line_id"])
        if r["family"] not in CODE_OF:
            raise InputsError(f"{where}: family {r['family']} (B7-02 / B7-06 / B7-03)")
        if r["flight"] not in flights:
            raise InputsError(f"{where}: flight {r['flight']} is not a drawn flight of the inputs (UNBOUND: HELD by "
                              f"name, never valued)")
        if r["role"] not in ROLES:
            raise InputsError(f"{where}: role {r['role']}")
        if r["action"] not in ACTIONS:
            raise InputsError(f"{where}: action {r['action']}")
        fl = flights[r["flight"]]
        b = r.get("before")
        if b is not None:
            b = _num(b, f"{where} before")
        a = r.get("after")
        if r["action"] in ("CORRECT", "KEEP") and b is not None:
            if a is None:
                raise InputsError(f"{where}: a {r['action']} line carries its figure")
            a = _num(a, f"{where} after", True)
            if r["evidence_status"] not in EVIDENCE_OK:
                raise InputsError(f"{where}: a valued reading is VERIFIED or DRAWING-CONFIRMED "
                                  f"({r['evidence_status']!r})")
            if fl.get("held"):
                raise InputsError(f"{where}: flight {r['flight']} is HELD ({fl['held']['cause'][:60]}): never valued")
        elif r["action"] in ("SUPERSEDE", "HOLD"):
            if a is not None:
                if isinstance(a, (int, float)) and abs(a) < 1e-12:
                    raise InputsError(f"{where}: HELD_AS_ZERO: a {r['action']} line carries no figure, never 0")
                raise InputsError(f"{where}: a {r['action']} line carries no figure")
        if r["action"] == "CORRECT" and r["role"] == "SEEN_THROUGH":
            raise InputsError(f"{where}: a SEEN_THROUGH reading is never the carrier (DOUBLE_COUNT)")
        if r["action"] == "SUPERSEDE":
            s = r.get("supersede") or {}
            _need(s, ("kind", "carrier_line"), f"{where} supersede")
            if s["kind"] not in SUPERSEDE_KINDS:
                raise InputsError(f"{where}: supersede kind {s['kind']}")
            if s["kind"] == "DOUBLE_COUNT" and r["role"] != "SEEN_THROUGH":
                raise InputsError(f"{where}: DOUBLE_COUNT is a SEEN_THROUGH reading ({r['role']})")
            if s["kind"] == "FOLDED" and r["role"] != "PARTIAL":
                raise InputsError(f"{where}: FOLDED is a PARTIAL reading ({r['role']})")
        if r["action"] == "HOLD":
            if not fl.get("held"):
                raise InputsError(f"{where}: HOLD needs a held flight (cause and source)")
            for x in r.get("beside") or ():
                _num(x.get("value"), f"{where} beside", True)
                _need(x, ("unit", "basis"), f"{where} beside")
        hb = r.get("held_beside")
        if hb is not None:
            _need(hb, ("why",), f"{where} held_beside")
            v = hb.get("value")
            if isinstance(v, (int, float)) and not isinstance(v, bool) and abs(v) < 1e-12:
                raise InputsError(f"{where}: HELD_AS_ZERO: a held tread beside is never 0")
            _num(v, f"{where} held_beside", True)
            if r["family"] != "B7-02" or r["action"] != "CORRECT":
                raise InputsError(f"{where}: a held tread m2 sits beside a valued tread line")
        reads.append(dict(r, _before=b, _after=a if isinstance(a, (int, float)) else None))
    if not reads:
        raise InputsError("no reading in the inputs")
    _check_binding(reads, flights)
    return dict(doc, _sources=srcs, _flights=flights, _readings=reads)


def _check_binding(reads, flights):
    """R-T429-1 on the inputs: per flight and family at most one valued reading; a valued tread / step line equals the
    drawn count x width; a superseded reading's carrier is a valued reading of the SAME flight on another line."""
    by_line = {r["line_id"]: r for r in reads}
    valued = {}
    for r in reads:
        if r["family"] == "B7-03" or r["_after"] is None:
            continue
        key = (r["flight"], r["family"])
        if key in valued:
            raise InputsError(f"flight {r['flight']} {r['family']}: valued on {valued[key]} and {r['line_id']} "
                              f"(DOUBLE_COUNT: one physical flight, one valued line)")
        valued[key] = r["line_id"]
        fl = flights[r["flight"]]
        n = fl["drawn_treads"]
        if r["family"] == "B7-06" and abs(r["_after"] - n * fl["_w"]) > TOL:
            raise InputsError(f"reading {r['line_id']}: step lm {r['_after']} is not drawn treads {n} x width "
                              f"{fl['_w']} (R-T425-2)")
        if r["family"] == "B7-02":
            held = 1 if r.get("held_beside") else 0
            going = fl.get("going")
            if going is not None and abs(r["_after"] - (n - held) * going * fl["_w"]) > TOL:
                raise InputsError(f"reading {r['line_id']}: tread m2 {r['_after']} is not {n - held} valued treads x "
                                  f"going {going} x width {fl['_w']} (R-T425-2)")
    for r in reads:
        if r["action"] != "SUPERSEDE":
            continue
        c = by_line.get(r["supersede"]["carrier_line"])
        if c is None or c["flight"] != r["flight"] or c["family"] != r["family"] or c["line_id"] == r["line_id"]:
            raise InputsError(f"reading {r['line_id']}: carrier {r['supersede']['carrier_line']} is not another "
                              f"reading of flight {r['flight']} in {r['family']}")
        if r["family"] != "B7-03" and c["_after"] is None:
            raise InputsError(f"reading {r['line_id']}: carrier {c['line_id']} carries no valued figure")


def level_class(a_levels, b_levels, a_plan, b_plan):
    """F-C-T425-1: two readings of flights drawn at the same plan position on different plans. Same level span ->
    SEEN_THROUGH (one physical flight, valued once); different span -> STACKED (a new flight). Same plan -> SAME_PLAN."""
    if a_plan == b_plan:
        return "SAME_PLAN"
    if any(abs(x - y) > 0.0015 for x, y in zip(a_levels, b_levels)):
        return "STACKED"
    return "SEEN_THROUGH"


# ================================================================================================ helpers
def _ver(srcs):
    return {"task": "+".join(s["task"] for s in srcs), "merge_commit": srcs[0]["merge_commit"],
            "merge_commits": [s["merge_commit"] for s in srcs],
            "verifier_run": "; ".join(s["checker_run"] for s in srcs), "ledger": "; ".join(s["file"] for s in srcs)}


def _rec(srcs, **kw):
    return dict({"piece": PIECE, "policy": PIECES[PIECE]["policy"], "tasks": [s["task"] for s in srcs],
                 "ledgers": [s["file"] for s in srcs], "ledger_sha256": [s["sha256"] for s in srcs],
                 "merge_commits": [s["merge_commit"] for s in srcs], "checker_runs": [s["checker_run"] for s in srcs],
                 "rule_id": RULE_ID, "rule_version": RULE_VERSION, "release_status": "NOT RELEASED"}, **kw)


def _fin(ln):
    from engine.source import boq_line as BL
    ln["project"] = copy.deepcopy(ln["project"])
    return BL.validate(ln)


def _base(ln):
    new = copy.deepcopy(ln)
    new["calculation"] = copy.deepcopy(new["calculation"])
    new["calculation"]["inputs"] = dict(new["calculation"]["inputs"] or {})
    return new


def _flight_txt(fl):
    lo, hi = fl["_levels"]
    return f"flight {fl['flight']} ({fl['stair']}, {lo:+.3f} -> {hi:+.3f})"


# ================================================================================================ the four actions
def _correct(ln, r, fl, srcs):
    new = _base(ln)
    before = ln["measured_net"]
    after = r["_after"]
    new["measured_net"] = after
    if new.get("gross") is not None:
        new["gross"] = after
    new["evidence_state"] = "SOURCE_DERIVED"
    hb = r.get("held_beside")
    held_txt = (f"; + {_fmt(hb['value'])} m2 HELD beside ({hb['why']})" if hb else "")
    unit = ln["unit"]
    basis = (f"{fl['drawn_treads']} drawn treads x {_fmt(fl['_w'])} m width" if r["family"] == "B7-06" else
             f"{fl['drawn_treads'] - (1 if hb else 0)} valued treads x drawn going x {_fmt(fl['_w'])} m width")
    new["calculation"]["formula"] = (f"{new['calculation']['formula']} | {METHOD}: {_flight_txt(fl)} carried by this "
                                     f"reading ({r['role']}, {r['plan']}): {basis} = {_fmt(after)} {unit} (was "
                                     f"{_fmt(before)}: {r.get('cause') or 'drawn fronts'}){held_txt}")
    new["calculation"]["inputs"][REC_KEY] = _rec(srcs, action="CORRECT", flight=fl["flight"], role=r["role"],
                                                 plan=r["plan"], drawn_treads=fl["drawn_treads"],
                                                 levels=list(fl["_levels"]), before=before, after=after,
                                                 held_beside=hb, evidence_status=r["evidence_status"],
                                                 cause=r.get("cause"))
    new["calculation"]["inputs"]["evidence_status"] = r["evidence_status"]
    new["notes"] = (f"{new.get('notes') or ''} | {METHOD}: the carrier of {fl['flight']}: drawn fronts (both layers), "
                    f"never lines - 1 (R-T425-2){'; one tread m2 HELD beside' if hb else ''}; NOT RELEASED")
    return _fin(new)


def _supersede(ln, r, fl, carrier_after, srcs):
    new = _base(ln)
    was = A302._q(A30._qty(ln))
    kind = r["supersede"]["kind"]
    carrier = r["supersede"]["carrier_line"]
    new["evidence_state"] = "NOT_APPLICABLE_WITH_EVIDENCE"
    new["measured_net"] = None
    new["bounded_range"] = None
    new["gross"] = None
    new["rfi"] = None
    before_formula = new["calculation"]["formula"]
    what = ("the same physical treads seen down through the stair opening from the plan above (a repeat at the same "
            "levels: SEEN_THROUGH, F-C-T425-1)" if kind == "DOUBLE_COUNT" else
            "a partial reading of the flight (above the cut) whose whole drawn flight is valued once on the carrier")
    new["calculation"]["formula"] = (f"{METHOD}: {kind}: this {r['plan']} reading of {_flight_txt(fl)} is {what}; "
                                     f"listed here, no quantity; the flight is valued on line {carrier} (R-T425-1; the "
                                     f"former reading is kept in calculation.inputs.{REC_KEY}.formula_before)")
    new["calculation"]["inputs"][REC_KEY] = _rec(srcs, action="SUPERSEDE", kind=kind, flight=fl["flight"],
                                                 role=r["role"], plan=r["plan"], owned_by=carrier, was=was,
                                                 carrier_after=carrier_after, formula_before=before_formula,
                                                 levels=list(fl["_levels"]), evidence_status=r["evidence_status"],
                                                 cause=r.get("cause"))
    new["calculation"]["inputs"]["evidence_status"] = "NOT_APPLICABLE"
    new["notes"] = (f"{new.get('notes') or ''} | {METHOD}: SUPERSEDED ({kind}): one physical flight, one valued line; "
                    f"owned by {carrier}; never deleted")
    return _fin(new)


def _hold(ln, r, fl, srcs):
    new = _base(ln)
    was = A302._q(A30._qty(ln))
    h = fl["held"]
    beside = [dict(x) for x in r.get("beside") or ()]
    new["evidence_state"] = "BLOCKED_RFI"
    new["measured_net"] = None
    new["bounded_range"] = None
    new["gross"] = None
    q = (f"{h['cause']} ({h['source']})")[:600]
    new["rfi"] = {"question": q, "unlocks": ln["line_id"]}
    bs = "; ".join(f"{_fmt(x['value'])} {x['unit']} ({x['basis']})" for x in beside) or "none"
    cnt = f"; governing count {h['count']}" if h.get("count") else ""
    new["calculation"]["formula"] = (f"{new['calculation']['formula']} | {METHOD}: {_flight_txt(fl)} is HELD: "
                                     f"{h['cause']}{cnt}; blank, never 0; beside: {bs}")[:1500]
    new["calculation"]["inputs"][REC_KEY] = _rec(srcs, action="HOLD", flight=fl["flight"], role=r["role"],
                                                 plan=r["plan"], was=was, held_cause=h["cause"],
                                                 held_source=h["source"], held_count=h.get("count"), beside=beside,
                                                 levels=list(fl["_levels"]), evidence_status="HELD",
                                                 cause=r.get("cause"))
    new["calculation"]["inputs"]["evidence_status"] = "HELD"
    new["notes"] = (f"{new.get('notes') or ''} | {METHOD}: HELD by name ({h['cause'].split(':')[0]}), figure(s) "
                    f"beside, never valued (R-T425-3)")
    return _fin(new)


# ================================================================================================ changes
def changes_for(doc, l3038):
    """-> (changes, log). Each change: piece, action, before (a V3.0.38 line), after (same id)."""
    if not doc:
        return [], {"piece": PIECE, "state": "NO_PROJECT_INPUT"}
    if any(((ln.get("calculation") or {}).get("inputs") or {}).get(REC_KEY) for ln in l3038):
        raise InputsError("the candidate already carries V3.0.39 records (applied once)")
    by = {ln["line_id"]: ln for ln in l3038}
    S = doc["_sources"]
    F = doc["_flights"]
    changes = []
    log = {"piece": PIECE, "state": "RUN", "sources": doc["sources"], "by_action": {}, "lines_changed": 0,
           "lines_kept": 0}
    after_of = {r["line_id"]: r["_after"] for r in doc["_readings"]}
    for r in doc["_readings"]:
        srcs = [S[t] for t in r["source_tasks"]]
        fl = F[r["flight"]]
        ln = by.get(r["line_id"])
        code, unit = CODE_OF[r["family"]]
        where = f"reading {r['line_id']}"
        if ln is None:
            raise InputsError(f"{where}: not in the candidate (stale binding)")
        if ln["item_code"] != code or ln["unit"] != unit:
            raise InputsError(f"{where}: {ln['item_code']} {ln['unit']} is not {r['family']} ({code} {unit})")
        fid = ((ln.get("calculation") or {}).get("inputs") or {}).get("flight_id")
        if r.get("reading") and fid not in (None, r["reading"]):
            raise InputsError(f"{where}: the line reads flight {fid}, the table {r['reading']} (stale binding)")
        net = ln.get("measured_net")
        if r["_before"] is None:
            if ln["evidence_state"] in VALUED:
                raise InputsError(f"{where}: the table says not valued, the candidate values {net} (stale binding)")
        else:
            if ln["evidence_state"] not in VALUED or net is None or abs(net - r["_before"]) > TOL:
                raise InputsError(f"{where}: candidate {ln['evidence_state']} {net} is not the table's "
                                  f"{r['_before']} (stale binding)")
        act = r["action"]
        if act == "KEEP":
            if r["_after"] is not None and abs(r["_after"] - (r["_before"] or 0.0)) > TOL:
                raise InputsError(f"{where}: KEEP with a different figure")
            log["lines_kept"] += 1
            log["by_action"]["KEEP"] = log["by_action"].get("KEEP", 0) + 1
            continue
        held = []
        if act == "CORRECT":
            if r["_before"] is None:
                raise InputsError(f"{where}: CORRECT needs a valued candidate line")
            new = _correct(ln, r, fl, srcs)
            ev = r["evidence_status"]
            if r.get("held_beside"):
                hb = r["held_beside"]
                held = [{"what": f"{code} {ln['location']['element_id']} tread(s) with undrawn going",
                         "why": hb["why"][:300], "range": None, "beside": hb["value"],
                         "scenario": "HELD by name beside the valued line"}]
        elif act == "SUPERSEDE":
            new = _supersede(ln, r, fl, after_of.get(r["supersede"]["carrier_line"]), srcs)
            ev = "NOT_APPLICABLE"
        else:
            new = _hold(ln, r, fl, srcs)
            ev = "HELD"
            held = [{"what": f"{code} {ln['location']['element_id']}", "why": fl["held"]["cause"][:300], "range": None,
                     "beside": [x["value"] for x in r.get("beside") or ()], "scenario": "HELD by name, never 0"}]
        if new["line_id"] != ln["line_id"]:
            raise ValueError(f"{METHOD}: a changed line keeps its id")
        log["lines_changed"] += 1
        log["by_action"][act] = log["by_action"].get(act, 0) + 1
        changes.append(A305._change(PIECE, "CHANGE", ln, new, step=act,
                                    drawing_reference="; ".join(s["file"] for s in srcs), verification=_ver(srcs),
                                    downstream=(["B7-05 nosing (T-424) binds to this flight's tread set"]
                                                if r["family"] == "B7-02" else []),
                                    group=code, evidence_status=ev, held=held, flight=fl["flight"], role=r["role"]))
    log["by_action"] = dict(sorted(log["by_action"].items()))
    return changes, log


# ================================================================================================ checks
def check_flights(lines, doc=None):
    """R-T429-1 on the integrated lines: every V3.0.39 record is consistent (a superseded line has no quantity and is
    owned by a VALUED line of the same code; a held line is blank with its reason; a corrected line is valued), and per
    flight at most one valued tread and one valued step line among the bound readings. -> summary."""
    by = {ln["line_id"]: ln for ln in lines}
    out = {"corrected": 0, "superseded": 0, "held": 0, "valued_by_flight": {}}
    flight_of = {}
    for ln in lines:
        rec = ((ln.get("calculation") or {}).get("inputs") or {}).get(REC_KEY)
        if not rec:
            continue
        flight_of[ln["line_id"]] = rec["flight"]
        a = rec["action"]
        if a == "CORRECT":
            if ln["evidence_state"] not in VALUED or ln["measured_net"] is None or ln["measured_net"] <= 0:
                raise ValueError(f"{METHOD}: corrected {ln['line_id']} is not valued")
            out["corrected"] += 1
        elif a == "SUPERSEDE":
            c = by.get(rec["owned_by"])
            if ln["evidence_state"] != "NOT_APPLICABLE_WITH_EVIDENCE" or ln.get("measured_net") is not None:
                raise ValueError(f"{METHOD}: superseded {ln['line_id']} still carries a quantity (double count)")
            if c is None or c["item_code"] != ln["item_code"]:
                raise ValueError(f"{METHOD}: superseded {ln['line_id']} is owned by no line of its code")
            if ln["item_code"] != RISER and c["evidence_state"] not in VALUED:
                raise ValueError(f"{METHOD}: superseded {ln['line_id']}: its carrier {c['line_id']} is not valued")
            out["superseded"] += 1
        elif a == "HOLD":
            if ln["evidence_state"] != "BLOCKED_RFI" or ln.get("measured_net") is not None \
                    or not (ln.get("rfi") or {}).get("question"):
                raise ValueError(f"{METHOD}: held {ln['line_id']} is not blank with its reason")
            out["held"] += 1
    if doc:
        for r in doc["_readings"]:
            flight_of.setdefault(r["line_id"], r["flight"])
    seen = {}
    for lid, f in flight_of.items():
        ln = by.get(lid)
        if ln is None or ln["item_code"] == RISER or ln["evidence_state"] not in VALUED:
            continue
        key = (f, ln["item_code"])
        if key in seen:
            raise ValueError(f"{METHOD}: flight {f} {ln['item_code']} valued on {seen[key]} and {lid} (DOUBLE_COUNT)")
        seen[key] = lid
        out["valued_by_flight"][f"{f}|{ln['item_code']}"] = ln["measured_net"]
    out["valued_by_flight"] = dict(sorted(out["valued_by_flight"].items()))
    return out


# ================================================================================================ integrate / write
def integrate(l3038, changes, for_lead=(), doc=None):
    """-> (V3.0.39 lines, identity). Changed lines replace their V3.0.38 line in place; nothing is added or removed;
    every other V3.0.38 line is byte-identical (asserted)."""
    sid = {ln["line_id"]: i for i, ln in enumerate(l3038)}
    out = list(l3038)
    repl = set()
    for c in changes:
        a = c["after"]
        if c["action"] != "CHANGE":
            raise ValueError(f"{METHOD}: action {c['action']} (this version adds and removes no line)")
        i = sid.get(a["line_id"])
        if i is None or a["line_id"] in repl:
            raise ValueError(f"{METHOD}: a changed line is not a V3.0.38 line or changes twice")
        if a["item_code"] not in OWN_CODES:
            raise ValueError(f"{METHOD}: {a['item_code']} is not a code this version may change")
        out[i] = a
        repl.add(a["line_id"])
    if len({ln["line_id"] for ln in out}) != len(out) or len(out) != len(l3038):
        raise ValueError(f"{METHOD}: the line set changed")
    guards = A3031._family_guards(out, for_lead)
    roof = A3031.check_roof_layers(out)
    ceil = A3032.check_ceilings(out)
    corr = A3033.check_corrections(out)
    zones = A3034.check_zones(out)
    fence = A3035.check_boundary(out)
    lists = A3036.check_lists(out)
    beds = A3038.check_beds(out)
    lift = A3038.check_lift(out)
    landing = A3038.check_landing(out)
    flights = check_flights(out, doc)
    pids = {(ln["project"]["project_id"], ln["project"]["revision_set_sha256"]) for ln in out}
    if len(pids) != 1:
        raise ValueError(f"{METHOD}: {len(pids)} project identities in the lines")
    outside = [ln for ln in l3038 if ln["line_id"] not in repl]
    bad = [a["line_id"] for a in outside if A30.line_sha(a) != A30.line_sha(out[sid[a["line_id"]]])]
    if bad:
        raise ValueError(f"{METHOD}: {len(bad)} V3.0.38 line(s) differ outside the named changes")
    ident = {"v3_0_38_lines": len(l3038), "v3_0_39_lines": len(out), "v3_0_39_rows": len(changes),
             "replaced": len(repl), "added": 0, "outside_rows": len(outside),
             "outside_rows_identical_to_v3_0_38": len(outside), "flights": flights, "beds": beds, "lift": lift,
             "landing": landing, "lists": lists, "fence": fence, "tile_zones": zones, "corrections": corr,
             "ceilings": ceil, "roof_buildup": roof, "guards": guards,
             "outside_rows_sha256": hashlib.sha256("".join(A30.line_sha(x) for x in outside).encode()).hexdigest()}
    return out, ident


def ledger_rows(changes, released_lines=None):
    rel = {A30._key(ln): ln for ln in released_lines or ()}
    rows = []
    for c in changes:
        ref = c["after"]
        rec = ref["calculation"]["inputs"].get(REC_KEY) or {}
        b29 = None
        if released_lines is not None:
            b29 = A30._qty(rel[A30._key(ref)]) if A30._key(ref) in rel else dict(A30._qty(None),
                                                                                 state="NOT_IN_RELEASED")
        loc = ref.get("location") or {}
        rows.append({"version": METHOD, "piece": PIECE, "action": c.get("step"), "change": c["action"],
                     "line_id": ref["line_id"], "item_code": ref["item_code"], "floor": loc.get("floor"),
                     "element_id": loc.get("element_id"), "unit": ref["unit"], "flight": c.get("flight"),
                     "role": c.get("role"), "before_released_v2_9": b29, "before_v3_0_38": A30._qty(c.get("before")),
                     "after_v3_0_39": A30._qty(ref), "evidence_status": c.get("evidence_status"),
                     "still_held": c.get("held"), "release_status": "NOT RELEASED",
                     "owner_manual_method": PIECES[PIECE]["owner_manual_method"],
                     "drawing_derived_method": PIECES[PIECE]["drawing_method"],
                     "record": rec, "verification": c.get("verification") or {}, "rollback": ROLLBACK})
    return rows


LEDGER_CSV = ("version", "piece", "action", "change", "line_id", "item_code", "floor", "element_id", "unit", "flight",
              "role", "v2_9", "v3_0_38", "v3_0_39", "evidence_status", "still_held", "verification")
DIFF_CSV = ("line_id", "item_code", "floor", "element_id", "unit", "vs_v3_0_38", "vs_released_v2_9", "v2_9",
            "v3_0_38", "v3_0_39")


def ledger_csv(rows):
    def q(x):
        return A302._q(x) if x and (x.get("value") is not None or x.get("low") is not None) else ""

    def h(r):
        return "; ".join(f"{x['what']} beside {x.get('beside')}" for x in (r.get("still_held") or ()))[:300]
    return A305._csv([{"version": r["version"], "piece": r["piece"], "action": r["action"], "change": r["change"],
                       "line_id": r["line_id"], "item_code": r["item_code"], "floor": r.get("floor") or "",
                       "element_id": r.get("element_id") or "", "unit": r["unit"], "flight": r.get("flight") or "",
                       "role": r.get("role") or "", "v2_9": q(r.get("before_released_v2_9")),
                       "v3_0_38": q(r.get("before_v3_0_38")), "v3_0_39": q(r.get("after_v3_0_39")),
                       "evidence_status": r["evidence_status"], "still_held": h(r),
                       "verification": f"{r['verification'].get('task')} "
                                       f"{' '.join(x[:8] for x in r['verification'].get('merge_commits') or ())}"}
                      for r in rows], LEDGER_CSV)


def diff_rows(l3038, l3039, released_lines=None):
    b38 = {ln["line_id"]: ln for ln in l3038}
    rel = {A30._key(ln): ln for ln in released_lines or ()}
    out = []
    for ln in l3039:
        o = b38.get(ln["line_id"])
        vs = "ADDED" if o is None else ("SAME" if A30.line_sha(o) == A30.line_sha(ln) else "CHANGED")
        r = rel.get(A30._key(ln)) if released_lines is not None else None
        vs29 = None if released_lines is None else ("NOT_IN_RELEASED" if r is None else
                                                    ("SAME_QUANTITY" if A30._qty(r) == A30._qty(ln) else
                                                     "QUANTITY_DIFFERS"))
        out.append({"line_id": ln["line_id"], "item_code": ln["item_code"], "floor": ln["location"].get("floor"),
                    "element_id": ln["location"].get("element_id"), "unit": ln["unit"], "vs_v3_0_38": vs,
                    "vs_released_v2_9": vs29, "v2_9": A302._q(A30._qty(r)) if r else "",
                    "v3_0_38": A302._q(A30._qty(o)) if o else "", "v3_0_39": A302._q(A30._qty(ln))})
    return out


def write(out, l3038, changes, log, released_lines=None, for_lead=(), doc=None):
    """the V3_0_39_* files beside the V3_0_38_* files. -> (file names, identity, ledger)."""
    from pathlib import Path
    from engine.source import boq_line as BL
    out = Path(out)
    l3039, ident = integrate(l3038, changes, for_lead, doc)
    rows = ledger_rows(changes, released_lines)
    diff = diff_rows(l3038, l3039, released_lines)
    named = {c["after"]["line_id"] for c in changes}
    stray = [d["line_id"] for d in diff if d["vs_v3_0_38"] == "CHANGED" and d["line_id"] not in named]
    if stray:
        raise ValueError(f"{METHOD}: {len(stray)} V3.0.38 line(s) changed outside the named changes")
    dsum = {}
    for d in diff:
        dsum.setdefault("vs_v3_0_38", {}).setdefault(d["vs_v3_0_38"], 0)
        dsum["vs_v3_0_38"][d["vs_v3_0_38"]] += 1
        if d["vs_released_v2_9"] is not None:
            dsum.setdefault("vs_released_v2_9", {}).setdefault(d["vs_released_v2_9"], 0)
            dsum["vs_released_v2_9"][d["vs_released_v2_9"]] += 1
    ident = dict(ident, diff=dsum)
    t38, t39 = A304.code_totals(l3038), A304.code_totals(l3039)
    moved = {k: {"v3_0_38": t38.get(k), "v3_0_39": t39.get(k)} for k in sorted(set(t38) | set(t39))
             if t38.get(k) != t39.get(k)}
    if any(k.split("|")[0] not in OWN_CODES for k in moved):
        raise ValueError(f"{METHOD}: totals moved outside this version's codes: {sorted(moved)[:5]}")
    led = {"schema": LEDGER_SCHEMA, "method": METHOD, "extends": EXTENDS, "candidate": CANDIDATE,
           "base": A30.BASE_METHOD, "released": A30.RELEASED_METHOD, "released_default": False, "rows": rows,
           "waiting_pieces": WAITING, "integration_package": True}
    run = {"method": METHOD, "policy": POLICY_ID, "extends": EXTENDS, "candidate": CANDIDATE,
           "base_method": A30.BASE_METHOD, "released_method": A30.RELEASED_METHOD, "released_default": False,
           "rollback": ROLLBACK, "identity": ident, "pieces": PIECES, "piece_logs": [log],
           "totals_moved_by_code": moved, "waiting_pieces": WAITING}
    files = {"V3_0_39_BOQ_LINES.json": BL.dumps(l3039),
             "V3_0_39_BOQ_LINES.csv": A30._lines_csv(l3039),
             "V3_0_39_INTEGRATION_LEDGER.json": A30._j(led),
             "V3_0_39_INTEGRATION_LEDGER.csv": ledger_csv(rows),
             "V3_0_39_DIFF.csv": A305._csv(diff, DIFF_CSV),
             "V3_0_39_RUN.json": A30._j(run)}
    for name, text in files.items():
        (out / name).write_text(text, encoding="utf-8")
    return sorted(files), ident, led


def policy_record():
    return {"method": METHOD, "extends": EXTENDS, "pieces": sorted(PIECES), "inputs_schema": INPUTS_SCHEMA,
            "released_default": False, "rollback": ROLLBACK, "actions": list(ACTIONS)}


__all__ = ["METHOD", "PIECES", "WAITING", "DEFAULT_GUARD_CLASS", "INPUTS_SCHEMA", "load_inputs", "level_class",
           "changes_for", "check_flights", "integrate", "ledger_rows", "diff_rows", "write", "InputsError"]
