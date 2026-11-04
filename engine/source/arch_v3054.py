"""ARCH_TAKEOFF_V3.0.54 (T-480, stream F): the SAME opt-in BOQ candidate as ARCH_TAKEOFF_V3.0 .. V3.0.53
(engine.source.arch_v30, arch_v301 .. arch_v3051, arch_v3053), with ONE new piece, the B7-09 stair guardrail RUNS of the
merged T-476 per-flight census (88e70ffe; Checker own re-measure of one flight, AGREE 0.000 %):

  RAIL_RUNS   (a) VALUE   a railing run line held blank whose flights the census reads DRAWING-CONFIRMED is valued
                          along the pitch line, flight by flight: an INCLINED flight = hypot(plan, rise) from nosing to
                          nosing (never its plan length), a HORIZONTAL piece = its plan length (rise 0); the run's figure
                          is the sum of its confirmed pieces, each piece printed on the line; a piece the census HOLDS
                          (a turn whose rail profile is not drawn) is never in the figure: it gets its own HELD BLANK
                          line by name (never 0, never a range);
              (b) CONFIRM a run line already valued is re-measured by the census and must AGREE within the export
                          tolerance: the line stays byte-identical (a disagreement is refused: a re-measure, not this
                          version);
              (c) KEEP    a run line held blank whose census pieces are all HELD / UNKNOWN stays byte-identical;
              (d) RETIRE  a per-flight line of the plan reader (one reading of a physical flight, several readings of
                          the same flight on several plans) is NOT_APPLICABLE_WITH_EVIDENCE, naming the physical flight
                          and the run line(s) that carry it (no figure, never 0);
              (e) UNKNOWN a census piece with no run (a drawn band whose rail existence is not established) gets a HELD
                          BLANK line by name.

R-T480-1 (every villa; integrates R-T476-1 .. 3 as merged, UP-STAIR-012 v2.0.0, UP-STAIR-013, OWNER_RULE_STAIRS
2026-10-21 / 2026-10-24, UP-QTY-STATUS-001): (1) an inclined rail is billed along its pitch line, recomputed here from
plan and rise and asserted equal to the census; plan length for an inclined piece, a rise on a horizontal piece and a
valued turn are refused; (2) one physical run, one valued line: the run lines of V3.0.30 keep their record (its family
guard forbids a figure on a per-flight line beside a run line), the flight breakdown is on the run line; (3) every
reader line is retired against a run line that exists; (4) held / unknown stays blank, never 0; (5) open side only: a
wall side with no rail drawn is NOT_APPLICABLE in the census and carries no line.

Nothing else moves: every V3.0.53 line not named by the inputs is byte-identical (asserted); totals move only in
FIN.RAILING (asserted). Version number: built on the merged V3.0.53 (T-487, merge dbc619fd); V3.0.54 may also be taken
by T-310 in parallel (merge-order rule: whichever merges later rebases and renumbers). Files: V3_0_54_BOQ_LINES.json /
.csv, V3_0_54_INTEGRATION_LEDGER.json / .csv, V3_0_54_DIFF.csv, V3_0_54_RUN.json. Nothing here names a project, a sheet,
a layer or a coordinate.
"""

from __future__ import annotations

import copy
import hashlib
import math
import re

from engine.source import arch_v30 as A30
from engine.source import arch_v302 as A302
from engine.source import arch_v304 as A304
from engine.source import arch_v305 as A305
from engine.source import arch_v3030 as A3030
from engine.source import arch_v3031 as A3031
from engine.source import arch_v3032 as A3032
from engine.source import arch_v3033 as A3033
from engine.source import arch_v3034 as A3034
from engine.source import arch_v3035 as A3035
from engine.source import arch_v3036 as A3036
from engine.source import arch_v3038 as A3038
from engine.source import arch_v3039 as A3039
from engine.source import arch_v3040 as A3040
from engine.source import arch_v3041 as A3041
from engine.source import arch_v3042 as A3042
from engine.source import arch_v3043 as A3043
from engine.source import arch_v3044 as A3044
from engine.source import arch_v3045 as A3045
from engine.source import arch_v3046 as A3046
from engine.source import arch_v3047 as A3047
from engine.source import arch_v3050 as A3050
from engine.source import arch_v3051 as A3051
from engine.source import arch_v3053 as A3053

DEFAULT_GUARD_CLASS = "TOOLING"          # T-212: books a Checker-merged census; adds no default value
METHOD = "ARCH_TAKEOFF_V3.0.54"
EXTENDS = A3053.METHOD
CANDIDATE = A30.METHOD
POLICY_ID = "URBAN_BOQ_T480_ARCH_V3_0_54"
INPUTS_SCHEMA = "URBAN_V3054_INPUTS_V1"
LEDGER_SCHEMA = "URBAN_V3054_INTEGRATION_LEDGER_V1"
ROLLBACK = A30.ROLLBACK
InputsError = A3051.InputsError
_r = A3050._r
_fmt = A3050._fmt
RULE_ID, RULE_VERSION = "R-T480-1", "T-480"
REC_KEY = "rail_runs_v3054"
RUN_REC_KEY = A3030.REC_KEY              # the V3.0.30 metalwork record a railing run line carries
P_RUNS = "RAIL_RUNS"
CODE, UNIT = "FIN.RAILING", "lm"
GUARD_CODE = A3030.RAIL_GUARD            # MET.RAILING.GUARD (B13-08): a reader line may be carried by a guard run
HOME_CODES = (CODE, GUARD_CODE)
RUN_PREFIX = "RAIL:"
VALUE, CONFIRM, KEEP = "VALUE", "CONFIRM", "KEEP"
RUN_ACTIONS = (VALUE, CONFIRM, KEEP)
ACTIONS = ("VALUE_RUN", "ADD_HELD_PIECE", "ADD_UNKNOWN", "RETIRE_READER")
INCLINED, HORIZONTAL, TURN = "INCLINED", "HORIZONTAL", "TURN"
KINDS = (INCLINED, HORIZONTAL, TURN)
CONFIRMED, HELD, UNKNOWN = "DRAWING-CONFIRMED", "HELD", "UNKNOWN"
PIECE_STATUS = (CONFIRMED, HELD, UNKNOWN)
PER_GOING = "PER_GOING"                  # a census length summed per going (variable pitch): bounded, not recomputed
VALUED_STATES = ("MEASURED", "SOURCE_DERIVED", "PROVISIONAL")
VALUED_STATE, HELD_STATE, NA_STATE = "PROVISIONAL", "BLOCKED_RFI", "NOT_APPLICABLE_WITH_EVIDENCE"
TOL = 1e-6                               # a census length against its own hypot (6 decimals)
CONFIRM_TOL = 0.0005                     # tools/boq_export_v1.QTY_MATCH_TOL: a 3-decimal line against the census
MAX_PIECE_M = 30.0                       # one flight / piece in m; above it is a unit slip (mm / cm refused)
MAX_RISE_M = 6.0
LINE_ID_RE = re.compile(r"^L-[0-9a-f]{20}$")
RUN_RE = re.compile(r"^RL-\d{2}$")
READER_EID_RE = re.compile(r":flight (\d+)$")

PIECES = {
    P_RUNS: {"module": "engine/source/arch_v3054.py (B7-09 railing runs valued flight by flight along the pitch line "
                       "from the merged census; per-flight reader lines retired against their run; held / unknown "
                       "pieces blank by name)", "policy": "RAIL_RUNS_PITCH_LINE_V1",
             "rule_id": "R-T480-1 (on R-T476-1 .. 3)",
             "owner_rules": ["UP-STAIR-012 v2.0.0 (railing per open side along the installed 3D path)",
                             "UP-STAIR-013 (a wall handrail only where one is shown)",
                             "OWNER_RULE_STAIRS 2026-10-21 / 2026-10-24 (release per item on its own evidence; held "
                             "stays blank)", "UP-QTY-STATUS-001 (held is blank, never 0)"],
             "owner_manual_method": "per flight, open side only: rail length = sqrt(going run^2 + rise^2) nosing to "
                                    "nosing, plus the level runs at landings / floor edges drawn with the same band",
             "drawing_method": "merged T-476 flight census (88e70ffe; Verifier 2026-11-02 18:40, own re-measure MS2-L "
                               "3.782209 lm AGREE): per flight the goings x going (plan), risers x riser (rise) from "
                               "the stair reconstruction (T-184 riser counts) and the drawn rail band; each reader line "
                               "bound to its physical flight by riser lines and lane"},
}
WAITING = dict(A3053.WAITING)
WAITING.update({
    "T480_TURN_PROFILES": "the rail over a well-end turn whose profile is not drawn (5 winders at a 0.10 m well; the "
                          "half landing closing riser) is HELD by name, blank: bind it when a detail draws the profile",
    "T480_OUTER_BANDS": "an outer band whose guard / string meaning is not drawn (a curved flight's outer band; a band "
                        "beside a short flight with no level change printed) stays UNKNOWN, blank",
    "T480_UNRAILED_EDGES": "an open stair edge with no rail drawn (an outside stair) stays a designer item (held run "
                           "line unchanged)",
})


# ================================================================================================ inputs
def _need(s, keys, where):
    for k in keys:
        if s.get(k) in (None, "", [], {}):
            raise InputsError(f"{where}: {k} missing")


def _num(x, where, pos=True, hi=MAX_PIECE_M):
    if not isinstance(x, (int, float)) or isinstance(x, bool) or x != x:
        raise InputsError(f"{where}: {x!r} is not a number")
    if x < 0 or (pos and x == 0):
        raise InputsError(f"{where}: {x!r} is {'not positive' if pos else 'negative'} (held is never 0)")
    if x > hi:
        raise InputsError(f"{where}: {x} is above {hi} (not a length in m; mm / cm refused)")
    return float(x)


def _lid(x, where):
    if not LINE_ID_RE.match(str(x)):
        raise InputsError(f"{where}: {x!r} is not a BOQ line id")
    return x


def pitch_length(kind, plan_m, rise_m):
    """R-T480-1 (1): the installed rail length of one piece. INCLINED: hypot(plan, rise), rise > 0 (a plan length for an
    inclined piece is refused); HORIZONTAL: plan, rise 0; TURN: never valued here (profile not drawn)."""
    if kind == INCLINED:
        if rise_m <= 0:
            raise InputsError("an inclined piece with no rise: plan length is never billed for a rail on a slope")
        return _r(math.hypot(plan_m, rise_m))
    if kind == HORIZONTAL:
        if rise_m != 0:
            raise InputsError(f"a horizontal piece with a rise {rise_m} m is inclined (pitch line, not plan)")
        return _r(plan_m)
    raise InputsError("a turn is valued only from a drawn rail profile (not in this version): held by name")


def _piece(p, where):
    w = f"{where} piece {p.get('piece_id')}"
    _need(p, ("piece_id", "stair", "flight", "side", "kind", "status", "source"), w)
    if p["kind"] not in KINDS:
        raise InputsError(f"{w}: kind {p['kind']!r} is not one of {KINDS}")
    if p["status"] not in PIECE_STATUS:
        raise InputsError(f"{w}: status {p['status']!r} is not one of {PIECE_STATUS}")
    out = dict(p)
    if p["status"] == CONFIRMED:
        plan = _num(p.get("plan_m"), f"{w} plan_m")
        rise = _num(p.get("rise_m"), f"{w} rise_m", pos=False, hi=MAX_RISE_M)
        try:
            L = pitch_length(p["kind"], plan, rise)
        except InputsError as e:
            raise InputsError(f"{w}: {e}") from None
        got = _num(p.get("length_lm"), f"{w} length_lm")
        if p.get("pitch") == PER_GOING:
            # a variable-pitch flight (one sloped piece per going): the per-going sum is not recomputable from the
            # totals; it lies between the straight pitch line and plan + rise (triangle inequality), else refused
            if p["kind"] != INCLINED or not (L - TOL <= got <= _r(plan + rise) + TOL):
                raise InputsError(f"{w}: per-going length {got} lm is outside [{L}, {_r(plan + rise)}] (not a rail "
                                  f"along that flight)")
            out.update(_plan=plan, _rise=rise, _L=_r(got), _recomputed=False)
        elif abs(got - L) > TOL:
            raise InputsError(f"{w}: census length {p['length_lm']} lm is not the pitch-line length {L} (recomputed)")
        else:
            out.update(_plan=plan, _rise=rise, _L=L, _recomputed=True)
    else:
        _need(p, ("missing",), w)
        if p.get("length_lm") not in (None, ""):
            raise InputsError(f"{w}: a {p['status']} piece carries no length (blank, never 0)")
    return out


def load_inputs(doc, project_id=None):
    """URBAN_V3054_INPUTS_V1 -> the validated doc.
    {"schema", "project_id", "sources": [{"task", "file", "sha256", "merge_commit", "checker_run"}],
     "runs": [{"run", "action" VALUE / CONFIRM / KEEP, "pieces": [{"piece_id", "stair", "flight", "side", "kind",
               "status", "plan_m", "rise_m", "length_lm", "missing", "source"}], "source_tasks"}],
     "unknowns": [{piece as above, status UNKNOWN, "floor", "source_tasks"}],
     "retire": [{"reader_line_id" (the census task's reader id, recorded), "floor", "reader_flight", "treads" (the
                 reading's tread count: binds it to its candidate line by floor + flight + treads, unique or refused),
                 "physical_flight", "reading", "homes": [run ids], "why", "source_tasks"}],
     "no_rail_sides": [{"stair", "flight", "side", "why"}] (open side only: recorded, no line)}"""
    if not doc:
        return None
    if doc.get("schema") != INPUTS_SCHEMA:
        raise InputsError(f"project inputs: schema must be {INPUTS_SCHEMA}")
    if project_id and doc.get("project_id") not in (None, project_id):
        raise InputsError(f"project inputs are for {doc.get('project_id')!r}, the run is {project_id!r}")
    srcs = A3043._sources(doc)
    runs, seen, pids = [], set(), set()
    for r in doc.get("runs") or ():
        w = f"run {r.get('run')}"
        _need(r, ("run", "action", "pieces"), w)
        A3043._tasks(r, srcs, w)
        if not RUN_RE.match(str(r["run"])) or r["run"] in seen:
            raise InputsError(f"{w}: not a run id, or named twice (one run, one line)")
        seen.add(r["run"])
        if r["action"] not in RUN_ACTIONS:
            raise InputsError(f"{w}: action {r['action']!r} is not one of {RUN_ACTIONS}")
        ps = [_piece(p, w) for p in r["pieces"]]
        for p in ps:
            if p["piece_id"] in pids:
                raise InputsError(f"{w}: piece {p['piece_id']} named twice")
            pids.add(p["piece_id"])
        conf = [p for p in ps if p["status"] == CONFIRMED]
        if r["action"] in (VALUE, CONFIRM) and not conf:
            raise InputsError(f"{w}: {r['action']} needs at least one DRAWING-CONFIRMED piece")
        if r["action"] == KEEP and conf:
            raise InputsError(f"{w}: KEEP with a confirmed piece (value it, or say why not)")
        if r["action"] == VALUE and any(p.get("_recomputed") is False for p in conf):
            raise InputsError(f"{w}: a per-going piece is valued only from its goings (not in this version)")
        if r["action"] == CONFIRM and any(p["status"] != CONFIRMED for p in ps):
            raise InputsError(f"{w}: a valued run with a held piece is not confirmed whole (re-measure)")
        runs.append(dict(r, _pieces=ps, _L=_r(sum(p["_L"] for p in conf)) if conf else None))
    unk = []
    for p in doc.get("unknowns") or ():
        w = "unknown"
        A3043._tasks(p, srcs, f"{w} {p.get('piece_id')}")
        _need(p, ("floor",), f"{w} {p.get('piece_id')}")
        x = _piece(p, w)
        if x["status"] != UNKNOWN or x["piece_id"] in pids:
            raise InputsError(f"{w} {x['piece_id']}: an unknown piece is UNKNOWN and named once")
        pids.add(x["piece_id"])
        unk.append(x)
    ret, rl = [], set()
    for r in doc.get("retire") or ():
        w = f"retire {r.get('reader_line_id')}"
        _need(r, ("reader_line_id", "floor", "reader_flight", "treads", "physical_flight", "reading", "homes", "why"),
              w)
        A3043._tasks(r, srcs, w)
        _lid(r["reader_line_id"], w)
        key = (r["floor"], r["reader_flight"], r["treads"])
        if key in rl:
            raise InputsError(f"{w}: reading {key} named twice")
        rl.add(key)
        if not isinstance(r["treads"], int) or isinstance(r["treads"], bool) or r["treads"] <= 0:
            raise InputsError(f"{w}: treads {r['treads']!r} is not a count")
        if not re.match(r"^F\d+$", str(r["reader_flight"])):
            raise InputsError(f"{w}: reader flight {r['reader_flight']!r} is not F<n>")
        if any(not RUN_RE.match(str(h)) for h in r["homes"]):
            raise InputsError(f"{w}: a home is not a run id")
        ret.append(dict(r))
    if not (runs or unk or ret):
        raise InputsError("no run, unknown piece or reader line in the inputs")
    return dict(doc, _sources=srcs, _runs=runs, _unknowns=unk, _retire=ret,
                _no_rail=list(doc.get("no_rail_sides") or ()))


# ================================================================================================ lines
def _rec(srcs, **kw):
    return dict({"piece": P_RUNS, "policy": PIECES[P_RUNS]["policy"], "tasks": [s["task"] for s in srcs],
                 "ledgers": [s["file"] for s in srcs], "ledger_sha256": [s["sha256"] for s in srcs],
                 "merge_commits": [s["merge_commit"] for s in srcs], "checker_runs": [s["checker_run"] for s in srcs],
                 "rule_id": RULE_ID, "rule_version": RULE_VERSION, "release_status": "NOT RELEASED"}, **kw)


def _inputs(ln):
    c = ln["calculation"] = dict(ln.get("calculation") or {})
    c["inputs"] = dict(c.get("inputs") or {})
    return c["inputs"]


def _eid(ln):
    return (ln.get("location") or {}).get("element_id")


def _blank(ln):
    return ln.get("measured_net") is None and not ln.get("bounded_range") and ln.get("gross") is None


def _run_lines(prev):
    """run id -> its run line (a FIN.RAILING / MET.RAILING.GUARD line with element RAIL:<run> and a V3.0.30 record)."""
    out = {}
    for ln in prev:
        e = str(_eid(ln) or "")
        if ln["item_code"] in HOME_CODES and e.startswith(RUN_PREFIX) and RUN_RE.match(e[len(RUN_PREFIX):]):
            if e[len(RUN_PREFIX):] in out:
                raise InputsError(f"run {e} has two lines in the candidate")
            out[e[len(RUN_PREFIX):]] = ln
    return out


def _ptxt(p):
    if p["status"] != CONFIRMED:
        return f"{p['piece_id']} {p['status']} ({p['missing']})"
    if p["kind"] == INCLINED:
        return f"{p['piece_id']} hypot({_fmt(p['_plan'])}, {_fmt(p['_rise'])}) {_fmt(p['_L'])}"
    return f"{p['piece_id']} level {_fmt(p['_L'])}"


def _valued(b, r, srcs):
    run = r["run"]
    ps = r["_pieces"]
    conf = [p for p in ps if p["status"] == CONFIRMED]
    held = [p for p in ps if p["status"] != CONFIRMED]
    new = copy.deepcopy(b)
    new["evidence_state"], new["measured_net"], new["gross"] = VALUED_STATE, r["_L"], r["_L"]
    new["deductions"], new["additions"], new["bounded_range"], new["rfi"] = [], [], None, None
    htxt = ("; held by name OUTSIDE the figure (own blank lines): " + ", ".join(p["piece_id"] for p in held)) if held \
        else ""
    new["calculation"]["formula"] = (f"{METHOD}: run {run} along the pitch line, flight by flight (open side): "
                                     f"{' + '.join(_ptxt(p) for p in conf)} = {_fmt(r['_L'])} lm{htxt} "
                                     f"({RULE_ID})")[:1500]
    _inputs(new)[REC_KEY] = _rec(srcs, action="VALUE_RUN", run=run, length_lm=r["_L"], was={
        "evidence_state": b["evidence_state"], "rfi": b.get("rfi")},
        pieces=[{"piece_id": p["piece_id"], "stair": p["stair"], "flight": p["flight"], "side": p["side"],
                 "kind": p["kind"], "status": p["status"], "plan_m": p.get("_plan"), "rise_m": p.get("_rise"),
                 "length_lm": p.get("_L"), "missing": p.get("missing"), "source": str(p["source"])[:300]}
                for p in ps], held_pieces=[p["piece_id"] for p in held], evidence_status=CONFIRMED)
    _inputs(new)["evidence_status"] = CONFIRMED
    A305._note(new, f"{METHOD}: run {run} valued {_fmt(r['_L'])} lm from {len(conf)} drawing-confirmed piece(s)"
                    f"{'; ' + str(len(held)) + ' held blank by name' if held else ''}; PROVISIONAL; NOT RELEASED")
    return A3046._fin(new)


def _held_line(tpl, p, run, srcs, floor):
    from engine.source import boq_line as BL
    eid = f"{RUN_PREFIX}{run}:{p['piece_id']}" if run else f"{RUN_PREFIX}{p['piece_id']}"
    st = p["status"]
    rec = _rec(srcs, action="ADD_HELD_PIECE" if run else "ADD_UNKNOWN", run=run, piece_id=p["piece_id"],
               stair=p["stair"], flight=p["flight"], side=p["side"], kind=p["kind"], status=st,
               plan_m=p.get("plan_m"), rise_m=p.get("rise_m"), missing=p["missing"], source=str(p["source"])[:300])
    what = f"rail piece {p['piece_id']} ({p['stair']} {p['flight']}, {p['side']})"
    formula = (f"{METHOD}: HELD BLANK (never a value, never 0) {what}, {st}: {p['missing']}"
               f"{'; part of run ' + run + ', outside its figure' if run else '; no run established'} "
               f"({RULE_ID})")[:1500]
    ln = BL.make_line(
        project_id=tpl["project"]["project_id"], revision_set_sha256=tpl["project"]["revision_set_sha256"],
        item_code=CODE, unit=UNIT, evidence_state=HELD_STATE, measured_net=None, gross=None, element_id=eid,
        floor=floor, physical_element=what, formula=formula, inputs={REC_KEY: rec, "evidence_status": st},
        documents=copy.deepcopy(tpl["source"]["documents"]), geometry_source=tpl["source"]["geometry_source"],
        geometry_confidence=tpl["source"]["geometry_confidence"], rule_id=RULE_ID, rule_version=RULE_VERSION,
        material_state=tpl.get("material_state") or "BY_SPEC",
        rfi={"question": f"{what}: {p['missing']}"[:900], "unlocks": eid},
        notes=f"{METHOD}: B7-09 piece {st} by name, blank (never 0); NOT RELEASED")
    return A3046._fin(ln)


def reader_line(prev, r):
    """the ONE candidate FIN.RAILING per-flight reader line of a reading: same floor, element '<room>:flight n' with
    F<n> = the reading's flight, and the reading's tread count; none or several -> refused (stale binding)."""
    w = f"retire {r['reader_line_id']}"
    hits = []
    for ln in prev:
        m = READER_EID_RE.search(str(_eid(ln) or ""))
        if ln["item_code"] != CODE or not m or f"F{m.group(1)}" != r["reader_flight"] or \
                (ln.get("location") or {}).get("floor") != r["floor"]:
            continue
        if ((ln.get("calculation") or {}).get("inputs") or {}).get("treads") == r["treads"]:
            hits.append(ln)
    if len(hits) != 1:
        raise InputsError(f"{w}: {len(hits)} candidate reader lines on {r['floor']} {r['reader_flight']} with "
                          f"{r['treads']} treads (one expected; stale binding)")
    return hits[0]


def _retired(b, r, homes, srcs):
    lid = b["line_id"]
    if b["item_code"] != CODE or b["unit"] != UNIT:
        raise InputsError(f"retire {lid}: not a {CODE} {UNIT} line of the candidate (stale binding)")
    ins = (b.get("calculation") or {}).get("inputs") or {}
    if ins.get(RUN_REC_KEY):
        raise InputsError(f"retire {lid}: a run line is never retired (only a reader line)")
    if not _blank(b):
        raise InputsError(f"retire {lid}: the reader line carries a figure (a valued reading is re-measured, not "
                          f"retired here)")
    new = copy.deepcopy(b)
    hl = ", ".join(f"{h} ({homes[h]['line_id']})" for h in r["homes"])
    text = (f"reader reading {r['reading']} of physical flight {r['physical_flight']}, carried by run line(s) {hl}: "
            f"{r['why']}")
    new["evidence_state"], new["bounded_range"], new["rfi"], new["gross"] = NA_STATE, None, None, None
    new["measured_net"], new["deductions"], new["additions"] = None, [], []
    new["calculation"]["formula"] = f"NOT_APPLICABLE: {text} ({METHOD})"[:1500]
    _inputs(new)[REC_KEY] = _rec(srcs, action="RETIRE_READER", physical_flight=r["physical_flight"],
                                 reader_flight=r["reader_flight"], treads=r["treads"],
                                 census_reader_line_id=r["reader_line_id"], reading=r["reading"], homes=list(r["homes"]),
                                 home_lines=[homes[h]["line_id"] for h in r["homes"]],
                                 was={"evidence_state": b["evidence_state"], "rfi": b.get("rfi")},
                                 why=str(r["why"])[:300], evidence_status=CONFIRMED)
    A305._note(new, f"{METHOD}: NOT_APPLICABLE_WITH_EVIDENCE: {text}"[:400])
    return A3046._fin(new)


# ================================================================================================ changes
def changes_for(doc, prev):
    """-> (changes, log). CHANGE: a run valued, a reader line retired; ADD: a held / unknown piece line."""
    if not doc:
        return [], {"piece": P_RUNS, "state": "NO_PROJECT_INPUT"}
    if any(((ln.get("calculation") or {}).get("inputs") or {}).get(REC_KEY) for ln in prev):
        raise InputsError("the candidate already carries V3.0.54 records (applied once)")
    by = {ln["line_id"]: ln for ln in prev}
    runs = _run_lines(prev)
    S = doc["_sources"]
    changes, ids = [], set(by)
    log = {"piece": P_RUNS, "state": "RUN", "sources": doc["sources"], "by_action": {}, "valued_lm": 0.0,
           "runs": {}, "confirmed": {}, "kept": [], "retired": 0, "held_pieces": [], "unknowns": [],
           "no_rail_sides": len(doc["_no_rail"])}

    def add(action, after, before, srcs, ev, held, down):
        if before is not None and before["line_id"] != after["line_id"]:
            raise ValueError(f"{METHOD}: a changed line keeps its id")
        if before is None:
            if after["line_id"] in ids:
                raise ValueError(f"{METHOD}: an added line {after['line_id']} repeats an id")
            ids.add(after["line_id"])
        log["by_action"][action] = log["by_action"].get(action, 0) + 1
        changes.append(A305._change(P_RUNS, "ADD" if before is None else "CHANGE", before, after, step=action,
                                    drawing_reference="; ".join(s["file"] for s in srcs),
                                    verification=A3043._ver(srcs), evidence_status=ev, held=held, downstream=down,
                                    group=CODE))

    for r in doc["_runs"]:
        w = f"run {r['run']}"
        srcs = [S[t] for t in r["source_tasks"]]
        b = runs.get(r["run"])
        if b is None:
            raise InputsError(f"{w}: no run line RAIL:{r['run']} in the candidate (stale binding)")
        if not ((b.get("calculation") or {}).get("inputs") or {}).get(RUN_REC_KEY):
            raise InputsError(f"{w}: line {b['line_id']} carries no V3.0.30 run record")
        if r["action"] == VALUE:
            if b["item_code"] != CODE or b["unit"] != UNIT or b["evidence_state"] != HELD_STATE or not _blank(b):
                raise InputsError(f"{w}: {b['item_code']} {b['evidence_state']} {b.get('measured_net')} is not the held "
                                  f"blank {CODE} run the census values (stale binding)")
            nl = _valued(b, r, srcs)
            hp = [p for p in r["_pieces"] if p["status"] != CONFIRMED]
            add("VALUE_RUN", nl, b, srcs, CONFIRMED,
                [{"what": p["piece_id"], "why": p["missing"], "range": None, "scenario": "own blank line"} for p in hp],
                [f"B7-09 FIN.RAILING +{_fmt(r['_L'])} lm (run {r['run']}, PROVISIONAL)"])
            fl = (b.get("location") or {}).get("floor")
            for p in hp:
                add("ADD_HELD_PIECE", _held_line(b, p, r["run"], srcs, fl), None, srcs, p["status"],
                    [{"what": p["piece_id"], "why": p["missing"], "range": None, "scenario": "held blank"}],
                    ["B7-09: blocked-line count +1; no figure moves"])
                log["held_pieces"].append(p["piece_id"])
            log["valued_lm"] = _r(log["valued_lm"] + r["_L"])
            log["runs"][r["run"]] = r["_L"]
        elif r["action"] == CONFIRM:
            if b["evidence_state"] not in VALUED_STATES or b.get("measured_net") is None:
                raise InputsError(f"{w}: line {b['line_id']} is not valued (nothing to confirm; stale binding)")
            d = _r(b["measured_net"] - r["_L"])
            if abs(d) > CONFIRM_TOL:
                raise InputsError(f"{w}: line {_fmt(b['measured_net'])} lm vs census {_fmt(r['_L'])} lm differ by "
                                  f"{_fmt(d)} (a re-measure, not this version)")
            log["confirmed"][r["run"]] = {"line_id": b["line_id"], "item_code": b["item_code"],
                                          "line_lm": b["measured_net"], "census_lm": r["_L"], "difference_lm": d}
        else:
            if not _blank(b):
                raise InputsError(f"{w}: KEEP on a line with a figure (stale binding)")
            log["kept"].append({"run": r["run"], "line_id": b["line_id"],
                                "pieces": [f"{p['piece_id']} {p['status']}" for p in r["_pieces"]]})
    tpl = runs.get(next(iter(sorted(runs)), None)) if runs else None
    for p in doc["_unknowns"]:
        if tpl is None:
            raise InputsError("no run line in the candidate to take the source documents from")
        srcs = [S[t] for t in p["source_tasks"]]
        add("ADD_UNKNOWN", _held_line(tpl, p, None, srcs, p["floor"]), None, srcs, UNKNOWN,
            [{"what": p["piece_id"], "why": p["missing"], "range": None, "scenario": "held blank"}],
            ["B7-09: blocked-line count +1; no figure moves"])
        log["unknowns"].append(p["piece_id"])
    seen_ret = set()
    for r in doc["_retire"]:
        srcs = [S[t] for t in r["source_tasks"]]
        homes = {}
        for h in r["homes"]:
            if h not in runs:
                raise InputsError(f"retire {r['reader_line_id']}: home run {h} has no line in the candidate")
            homes[h] = runs[h]
        b = reader_line(prev, r)
        if b["line_id"] in seen_ret:
            raise InputsError(f"retire {r['reader_line_id']}: candidate line {b['line_id']} bound twice")
        seen_ret.add(b["line_id"])
        add("RETIRE_READER", _retired(b, r, homes, srcs), b, srcs, CONFIRMED,
            [], ["B7-09: one reader reading leaves the held count; its flight is carried by its run line"])
        log["retired"] += 1
    log["by_action"] = dict(sorted(log["by_action"].items()))
    return changes, log


# ================================================================================================ checks
def check_runs(lines):
    """R-T480-1 on the integrated lines: a valued run is PROVISIONAL, measured = gross = the sum of its confirmed pieces'
    pitch-line lengths (recomputed), keeps its V3.0.30 record and names every held piece by a blank line; a held /
    unknown piece line is BLOCKED_RFI blank naming its reason; a retired reader line is NOT_APPLICABLE with no figure
    and names run lines that exist. -> summary."""
    out = {"valued_runs": 0, "valued_lm": 0.0, "held_pieces": 0, "unknowns": 0, "retired": 0}
    by = {ln["line_id"]: ln for ln in lines}
    elems = {_eid(ln) for ln in lines}
    for ln in lines:
        rec = ((ln.get("calculation") or {}).get("inputs") or {}).get(REC_KEY)
        if not rec:
            continue
        if ln["item_code"] != CODE or ln["unit"] != UNIT:
            raise ValueError(f"{METHOD}: a V3.0.54 record on {ln['item_code']} {ln['line_id']}")
        act = rec.get("action")
        if act == "VALUE_RUN":
            L = 0.0
            for p in rec["pieces"]:
                if p["status"] == CONFIRMED:
                    L += pitch_length(p["kind"], p["plan_m"], p["rise_m"])
                elif f"{RUN_PREFIX}{rec['run']}:{p['piece_id']}" not in elems:
                    raise ValueError(f"{METHOD}: held piece {p['piece_id']} of run {rec['run']} has no blank line")
            L = _r(L)
            if ln["evidence_state"] != VALUED_STATE or abs((ln.get("measured_net") or -1) - L) > TOL or \
                    ln.get("gross") != ln.get("measured_net") or ln.get("bounded_range") is not None or \
                    not ((ln.get("calculation") or {}).get("inputs") or {}).get(RUN_REC_KEY):
                raise ValueError(f"{METHOD}: valued run {ln['line_id']} is not its pieces' pitch-line sum {L}")
            out["valued_runs"] += 1
            out["valued_lm"] = _r(out["valued_lm"] + L)
        elif act in ("ADD_HELD_PIECE", "ADD_UNKNOWN"):
            if ln["evidence_state"] != HELD_STATE or not _blank(ln) or not (ln.get("rfi") or {}).get("question") \
                    or not rec.get("missing"):
                raise ValueError(f"{METHOD}: piece line {ln['line_id']} is not BLOCKED_RFI blank with its reason")
            out["held_pieces" if act == "ADD_HELD_PIECE" else "unknowns"] += 1
        elif act == "RETIRE_READER":
            if ln["evidence_state"] != NA_STATE or not _blank(ln):
                raise ValueError(f"{METHOD}: retired reader line {ln['line_id']} carries a figure")
            if not rec.get("home_lines") or any(h not in by or by[h]["item_code"] not in HOME_CODES
                                                for h in rec["home_lines"]):
                raise ValueError(f"{METHOD}: retired reader line {ln['line_id']} names no run line")
            out["retired"] += 1
        else:
            raise ValueError(f"{METHOD}: action {act} on {ln['line_id']}")
    return out


# ================================================================================================ integrate / write
def integrate(prev, changes, for_lead=()):
    """-> (V3.0.54 lines, identity). Changed lines replace their candidate line in place, added lines follow; every
    other candidate line is byte-identical (asserted). Every V3.0.53 check runs as V3.0.53 runs it."""
    sid = {ln["line_id"]: i for i, ln in enumerate(prev)}
    out, adds, repl = list(prev), [], set()
    for c in changes:
        a = c["after"]
        if a["item_code"] != CODE:
            raise ValueError(f"{METHOD}: {a['item_code']} is not the code this version may change")
        if c["action"] == "CHANGE":
            i = sid.get(a["line_id"])
            if i is None or a["line_id"] in repl:
                raise ValueError(f"{METHOD}: a changed line is not a candidate line or changes twice")
            out[i] = a
            repl.add(a["line_id"])
        elif c["action"] == "ADD":
            if a["line_id"] in sid:
                raise ValueError(f"{METHOD}: an added line repeats a candidate id")
            adds.append(a)
        else:
            raise ValueError(f"{METHOD}: action {c['action']}")
    out = out + adds
    if len({ln["line_id"] for ln in out}) != len(out):
        raise ValueError(f"{METHOD}: a BOQ line id appears twice")
    guards = A3031._family_guards(out, for_lead)
    older = [ln for ln in out if not ((ln.get("calculation") or {}).get("inputs") or {}).get(A3051.REC_KEY)]
    ident = {"base_lines": len(prev), "v3_0_54_lines": len(out), "v3_0_54_rows": len(changes),
             "replaced": len(repl), "added": len(adds), "guards": guards,
             "roof_buildup": A3031.check_roof_layers(out), "ceilings": A3032.check_ceilings(out),
             "corrections": A3033.check_corrections(out), "tile_zones": A3034.check_zones(out),
             "fence": A3035.check_boundary(out), "lists": A3036.check_lists(out), "beds": A3038.check_beds(out),
             "lift": A3038.check_lift(out), "landing": A3038.check_landing(out), "flights": A3039.check_flights(out),
             "gb_runs": A3040.check_runs(out), "pieces": A3041.check_pieces(out), "slab": A3042.check_slab(out),
             "earthworks": A3050.check_zone_owner(out), "skirting": A3044.check_skirting(older),
             "blinding": A3045.check_blinding(out), "tie_masonry": A3046.check_tie_masonry(out),
             "stair_rooms": A3047.check_stair_rooms(out), "remainder": A3051.check_remainder(out),
             "lintels": A3053.check_lintels(out), "rail_runs": check_runs(out)}
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


def check_totals(t0, t1):
    """totals move only in FIN.RAILING (asserted)."""
    moved = {}
    for k in sorted(set(t0) | set(t1)):
        if t0.get(k) == t1.get(k):
            continue
        if k.split("|")[0] != CODE:
            raise ValueError(f"{METHOD}: totals moved outside this version's code: {k}")
        moved[k] = {"base": t0.get(k), "v3_0_54": t1.get(k)}
    return moved


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
        rows.append({"version": METHOD, "piece": c["piece"], "action": c.get("step"), "change": c["action"],
                     "line_id": ref["line_id"], "item_code": ref["item_code"], "floor": loc.get("floor"),
                     "element_id": loc.get("element_id"), "unit": ref["unit"], "run": rec.get("run"),
                     "physical_flight": rec.get("physical_flight") or rec.get("piece_id"),
                     "before_released_v2_9": b29, "before_base": A30._qty(c.get("before")),
                     "after_v3_0_54": A30._qty(ref), "evidence_status": c.get("evidence_status"),
                     "still_held": c.get("held"), "release_status": "NOT RELEASED",
                     "owner_manual_method": PIECES[c["piece"]]["owner_manual_method"],
                     "drawing_derived_method": PIECES[c["piece"]]["drawing_method"],
                     "downstream": c.get("downstream"), "record": rec, "verification": c.get("verification") or {},
                     "rollback": ROLLBACK})
    return rows


LEDGER_CSV = ("version", "action", "change", "line_id", "item_code", "floor", "element_id", "unit", "run",
              "physical_flight", "v2_9", "base", "v3_0_54", "evidence_status", "still_held", "verification")
DIFF_CSV = ("line_id", "item_code", "floor", "element_id", "unit", "vs_base", "vs_released_v2_9", "v2_9", "base",
            "v3_0_54")


def ledger_csv(rows):
    def q(x):
        return A302._q(x) if x and (x.get("value") is not None or x.get("low") is not None or x.get("state")) else ""

    def h(r):
        return "; ".join(f"{x['what']}: {x.get('why')}" for x in (r.get("still_held") or ()))[:300]
    return A305._csv([{"version": r["version"], "action": r["action"], "change": r["change"], "line_id": r["line_id"],
                       "item_code": r["item_code"], "floor": r.get("floor") or "",
                       "element_id": r.get("element_id") or "", "unit": r["unit"], "run": r.get("run") or "",
                       "physical_flight": r.get("physical_flight") or "",
                       "v2_9": q(r.get("before_released_v2_9")), "base": q(r.get("before_base")),
                       "v3_0_54": q(r.get("after_v3_0_54")), "evidence_status": r["evidence_status"],
                       "still_held": h(r),
                       "verification": f"{r['verification'].get('task')} "
                                       f"{' '.join(x[:8] for x in r['verification'].get('merge_commits') or ())}"}
                      for r in rows], LEDGER_CSV)


def diff_rows(prev, new, released_lines=None):
    rows = A3046.diff_rows(prev, new, released_lines)
    return [dict({k: v for k, v in r.items() if k != "v3_0_46"}, v3_0_54=r["v3_0_46"]) for r in rows]


def write(out, prev, changes, log, released_lines=None, for_lead=()):
    """the V3_0_54_* files beside the base candidate's files. -> (file names, identity, ledger)."""
    from pathlib import Path
    from engine.source import boq_line as BL
    out = Path(out)
    new, ident = integrate(prev, changes, for_lead)
    rows = ledger_rows(changes, released_lines)
    diff = diff_rows(prev, new, released_lines)
    named = {c["after"]["line_id"] for c in changes}
    stray = [d["line_id"] for d in diff if d["vs_base"] in ("CHANGED", "ADDED") and d["line_id"] not in named]
    if stray:
        raise ValueError(f"{METHOD}: {len(stray)} line(s) changed outside the named changes")
    dsum = {}
    for d in diff:
        dsum.setdefault("vs_base", {}).setdefault(d["vs_base"], 0)
        dsum["vs_base"][d["vs_base"]] += 1
        if d["vs_released_v2_9"] is not None:
            dsum.setdefault("vs_released_v2_9", {}).setdefault(d["vs_released_v2_9"], 0)
            dsum["vs_released_v2_9"][d["vs_released_v2_9"]] += 1
    ident = dict(ident, diff=dsum)
    moved = check_totals(A304.code_totals(prev), A304.code_totals(new))
    led = {"schema": LEDGER_SCHEMA, "method": METHOD, "extends": EXTENDS, "candidate": CANDIDATE,
           "base": A30.BASE_METHOD, "released": A30.RELEASED_METHOD, "released_default": False, "rows": rows,
           "summary": {k: log.get(k) for k in ("by_action", "valued_lm", "runs", "confirmed", "kept", "retired",
                                               "held_pieces", "unknowns", "no_rail_sides")},
           "waiting_pieces": WAITING, "integration_package": True}
    run = {"method": METHOD, "policy": POLICY_ID, "extends": EXTENDS, "candidate": CANDIDATE,
           "base_method": A30.BASE_METHOD, "released_method": A30.RELEASED_METHOD, "released_default": False,
           "rollback": ROLLBACK, "identity": ident, "pieces": PIECES, "piece_logs": [log],
           "totals_moved_by_code": moved, "waiting_pieces": WAITING}
    files = {"V3_0_54_BOQ_LINES.json": BL.dumps(new),
             "V3_0_54_BOQ_LINES.csv": A30._lines_csv(new),
             "V3_0_54_INTEGRATION_LEDGER.json": A30._j(led),
             "V3_0_54_INTEGRATION_LEDGER.csv": ledger_csv(rows),
             "V3_0_54_DIFF.csv": A305._csv(diff, DIFF_CSV),
             "V3_0_54_RUN.json": A30._j(run)}
    for name, text in files.items():
        (out / name).write_text(text, encoding="utf-8")
    return sorted(files), ident, led


def policy_record():
    return {"method": METHOD, "extends": EXTENDS, "pieces": sorted(PIECES), "inputs_schema": INPUTS_SCHEMA,
            "released_default": False, "rollback": ROLLBACK, "actions": list(ACTIONS)}


__all__ = ["METHOD", "PIECES", "WAITING", "DEFAULT_GUARD_CLASS", "INPUTS_SCHEMA", "CODE", "load_inputs",
           "pitch_length", "reader_line", "changes_for", "check_runs", "integrate", "check_totals", "ledger_rows", "diff_rows",
           "write", "InputsError"]
