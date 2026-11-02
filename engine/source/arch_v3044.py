"""ARCH_TAKEOFF_V3.0.44 (T-422): the SAME opt-in BOQ candidate as ARCH_TAKEOFF_V3.0 .. V3.0.43 (engine.source.arch_v30,
arch_v301 .. arch_v3043), with the SKIRTING QUANTITY RELEASE of the merged T-296 opening-to-line ledger (split row (a)
of T-246), in ONE step:

  RELEASE      a window whose sill is ESTABLISHED above the floor (T-296 SKIRTED, DRAWING-CONFIRMED / PRINTED) has a
               wall base under it, so the skirting runs under the sill: its two listed halves (glazing + threshold,
               physical_check UNRESOLVED since V3.0.36) leave the room's determinate line, whose net rises by the window
               edge; gross and every other listed item stay. The room's held range line, which held exactly that edge,
               is counted in the determinate line now: NOT_APPLICABLE_WITH_EVIDENCE (no figure, never 0, names the
               line that carries it). A range line that holds more than the released edges keeps the rest as its range.
  RANGE_NARROW a window with NO skirting under it (sill at the floor: floor glazing; or the base of a wet room whose
               full-height wall tile owns it) leaves the held range of its room: the range high falls by the edge, the
               low never rises above the high; state, net (blank) and rfi stay.
  MISSING      a dry room with no skirting line at all gets one HELD BLANK line (BLOCKED_RFI, no net, no range): the
               omission is named, never 0; the engine's own boundary figure is shown beside, never as the quantity.

R-T422-1 (every villa; integrates R-T296-1, UP-SKIRT-001 1.4.0 windows, UP-CER-003): a skirting line's window base
follows the merged sill record: skirted when the sill is established above the floor (> 0.02 m), not skirted at the
floor or on a base another finish owns, held whole in a range when the sill is unknown; a released edge is carried
once (determinate line up, its range line counted in it); a narrowing moves only a held range, never a value; a
missing dry-room line is HELD BLANK, never 0.

Nothing else moves: every V3.0.43 line not named by the inputs is byte-identical (asserted); totals move only in the
FIN.SKIRTING code (asserted). Files: V3_0_44_BOQ_LINES.json / .csv, V3_0_44_INTEGRATION_LEDGER.json / .csv,
V3_0_44_DIFF.csv, V3_0_44_RUN.json. Nothing here names a project, a sheet, a layer or a coordinate.
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

DEFAULT_GUARD_CLASS = "TOOLING"          # T-212: re-books checker-merged ledgers; adds no default value
METHOD = "ARCH_TAKEOFF_V3.0.44"
EXTENDS = A3043.METHOD
CANDIDATE = A30.METHOD
POLICY_ID = "URBAN_BOQ_T422_ARCH_V3_0_44"
INPUTS_SCHEMA = "URBAN_V3044_INPUTS_V1"
LEDGER_SCHEMA = "URBAN_V3044_INTEGRATION_LEDGER_V1"
ROLLBACK = A30.ROLLBACK
InputsError = A3031.InputsError
_r = A3018._r
_fmt = A3030._fmt
RULE_ID, RULE_VERSION = "R-T422-1", "T-422"
REC_KEY = "skirting_release_v3044"
CODE, UNIT = "FIN.SKIRTING", "lm"
P_RELEASE, P_NARROW, P_MISSING = "THRESHOLD_RELEASE", "RANGE_NARROW", "MISSING_LINE"
ACTIONS = ("RELEASE", "ABSORB_RANGE", "NARROW_RANGE", "ADD_MISSING")
FLOOR_GLAZING_MAX_SILL_M = 0.02          # UP-SKIRT-001 1.4.0 / UP-OPEN-SCHED-001: sill <= 0.02 m is floor glazing
VALUED_STATES = ("MEASURED", "SOURCE_DERIVED", "PROVISIONAL")
RANGE_STATE = "BOUNDED_EXPOSURE"
HELD_STATE = "BLOCKED_RFI"
NA_STATE = "NOT_APPLICABLE_WITH_EVIDENCE"
SKIRTED_STATUS = ("DRAWING-CONFIRMED", "PRINTED")
NOT_SKIRTED_WHY = ("FLOOR_GLAZING", "WET_BASE")
TOL = 0.0005                             # tools/boq_export_v1.QTY_MATCH_TOL (the T-330 check's tolerance)
BIND_TOL = 1e-6
MAX_WINDOW_EDGE_LM = 20.0                # one window base edge in lm; a figure above it is a unit slip (mm / cm)
MAX_SILL_M = 6.0                         # a sill height in m above the floor; above it is a unit slip
LINE_ID_RE = re.compile(r"^L-[0-9a-f]{20}$")

PIECES = {
    P_RELEASE: {"module": "engine/source/arch_v3044.py (a window threshold with an established sill above the floor "
                          "released into its room's determinate skirting line; the room's range line counted in it)",
                "policy": "SKIRTING_THRESHOLD_RELEASE_V1", "rule_id": "R-T296-1 (R-T422-1 a, b)",
                "owner_rules": ["UP-SKIRT-001 1.4.0 (windows: the wall base continues under a sill above the floor)",
                                "UP-CER-002 (skirting in lm)", "UP-CER-003 (doors / passages deducted)",
                                "UP-QTY-STATUS-001 (held is blank, never 0)"],
                "owner_manual_method": "room perimeter at floor level less each door / passage width by opening; a "
                                       "window is deducted only where no wall continues under it (sill at the floor)",
                "drawing_method": "engine skirting runs with the V3.0.36 list by opening id; the merged T-296 reading "
                                  "of each window from the merged sill record (T-201 / T-175 printed or drawing-"
                                  "confirmed sill): sill above the floor -> both listed halves leave the list"},
    P_NARROW: {"module": "engine/source/arch_v3044.py (a window with no skirting under it taken out of its room's held "
                         "range; no value, no state)", "policy": "SKIRTING_RANGE_NARROW_V1",
               "rule_id": "R-T296-1 (R-T422-1 c)",
               "owner_rules": ["UP-SKIRT-001 1.4.0 (floor glazing: no wall base)",
                               "Q-37 A / Q-48 A (wet room walls fully tiled: the tile owns the base)",
                               "UP-QTY-STATUS-001"],
               "owner_manual_method": "not a new quantity: a held range shows only what the drawings leave open",
               "drawing_method": "the merged T-296 reading: sill 0.00 printed / drawing-confirmed (floor glazing), or "
                                 "the window of an owner wet room; its edge leaves the room's range"},
    P_MISSING: {"module": "engine/source/arch_v3044.py (a dry room with no skirting line: one HELD BLANK line)",
                "policy": "SKIRTING_MISSING_LINE_V1", "rule_id": "R-T296-1 (R-T422-1 d)",
                "owner_rules": ["UP-SKIRT-001 (dry room: skirting at the wall base)", "UP-QTY-STATUS-001"],
                "owner_manual_method": "room perimeter at floor level less the door widths (no walk of this room is "
                                      "merged yet)",
                "drawing_method": "the engine boundary of the cell, shown beside as the engine's own figure, never the "
                                  "quantity (no independent walk merged)"},
}
WAITING = dict(A3043.WAITING)
WAITING.update({
    "T422_HELD_SILLS": "W02, W11, W12, W17: sill not established (T-144 / T-207 / T-238 designer items): their edges stay "
                       "whole in the room range lines, listed halves UNRESOLVED; nothing released",
    "T422_STAIR_SHAFT": "1F living line: the ST-1F shaft wall bases (10.232 lm, T-250 walk) and W13 / W25 carry no owner "
                        "rule for skirting along a stair (stringer / landing): the determinate line keeps them, the "
                        "range keeps W13 / W25; T-296 ledger low 31.203 is not applied here (stair-skirting rule first)",
    "T422_2F01_LOBBY": "2F-01 stair lobby 6.138 lm determinate (T-250 walk) stays inside its BLOCKED_RFI stair line "
                       "(engine room = lobby + ST-2F): a split of that line is a separate package",
    "T422_OPEN_PLAN_WET": "GF open-plan line L-71e2e002: about 5.1 lm of wet-pantry base inside the engine cell (T-296 "
                          "information, no merged face split): unchanged",
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
    if x > 2000:
        raise InputsError(f"{where}: {x} is not a skirting length in lm (mm / cm refused)")
    return float(x)


def _sources(doc):
    srcs = {}
    for s in doc.get("sources") or ():
        _need(s, ("task", "file", "sha256", "merge_commit", "checker_run"), f"source {s.get('task')}")
        srcs[s["task"]] = s
    if not srcs:
        raise InputsError("sources: the merged ledgers the rows come from")
    return srcs


def _tasks(r, srcs, where):
    if not r.get("source_tasks") or any(t not in srcs for t in r["source_tasks"]):
        raise InputsError(f"{where}: no merged source named")


def _lid(x, where):
    if not LINE_ID_RE.match(str(x)):
        raise InputsError(f"{where}: {x!r} is not a BOQ line id")
    return x


def _window(w, where, skirted):
    _need(w, ("census_id", "status", "why"), where)
    e = _num(w.get("edge_lm"), f"{where} edge_lm", pos=True)
    if e > MAX_WINDOW_EDGE_LM:
        raise InputsError(f"{where}: edge {e} is not one window edge in lm (mm / cm refused)")
    sill = w.get("sill_m")
    if sill not in (None, "") and (not isinstance(sill, (int, float)) or isinstance(sill, bool) or sill < 0 or
                                   sill > MAX_SILL_M):
        raise InputsError(f"{where}: sill {sill!r} is not a sill height in m (mm refused)")
    if skirted:
        if w["status"] not in SKIRTED_STATUS:
            raise InputsError(f"{where}: a released window needs its sill {SKIRTED_STATUS} (got {w['status']})")
        if not isinstance(sill, (int, float)) or isinstance(sill, bool) or sill <= FLOOR_GLAZING_MAX_SILL_M:
            raise InputsError(f"{where}: sill {sill!r} is not established above the floor: nothing to release")
    else:
        if w.get("reason") not in NOT_SKIRTED_WHY:
            raise InputsError(f"{where}: a narrowing needs its reason {NOT_SKIRTED_WHY}")
        if w["reason"] == "FLOOR_GLAZING" and (not isinstance(sill, (int, float)) or isinstance(sill, bool) or
                                              sill > FLOOR_GLAZING_MAX_SILL_M):
            raise InputsError(f"{where}: floor glazing needs an established sill <= {FLOOR_GLAZING_MAX_SILL_M} m")
    return dict(w, _edge=e)


def load_inputs(doc, project_id=None):
    """URBAN_V3044_INPUTS_V1 -> the validated doc.
    {"schema", "project_id", "sources": [{"task", "file", "sha256", "merge_commit", "checker_run"}],
     "releases": [{"line_id", "expect": {"gross", "measured_net"}, "windows": [{"census_id", "edge_lm", "sill_m",
                   "status", "why"}], "range_line": {"line_id", "expect": {"low", "high"}}, "source_tasks"}],
     "narrows": [{"line_id", "expect": {"low", "high"}, "windows": [{"census_id", "edge_lm", "sill_m", "status",
                  "reason" (FLOOR_GLAZING / WET_BASE), "why"}], "source_tasks"}],
     "missing": [{"engine_room", "floor", "template_line", "room_kind", "engine_boundary_lm", "why", "source_tasks"}]}"""
    if not doc:
        return None
    if doc.get("schema") != INPUTS_SCHEMA:
        raise InputsError(f"project inputs: schema must be {INPUTS_SCHEMA}")
    if project_id and doc.get("project_id") not in (None, project_id):
        raise InputsError(f"project inputs are for {doc.get('project_id')!r}, the run is {project_id!r}")
    srcs = _sources(doc)
    named, wins = set(), set()

    def once(lid, where):
        if lid in named:
            raise InputsError(f"{where}: line {lid} named twice (one change per line)")
        named.add(lid)

    def win_once(lid, w, where):
        k = (lid, w["census_id"])
        if k in wins:
            raise InputsError(f"{where}: window {w['census_id']} taken twice on {lid}")
        wins.add(k)

    rel = []
    for r in doc.get("releases") or ():
        w = f"release {r.get('line_id')}"
        _need(r, ("line_id", "expect", "windows"), w)
        _tasks(r, srcs, w)
        once(_lid(r["line_id"], w), w)
        e = r["expect"]
        _num(e.get("gross"), f"{w} expect.gross", pos=True)
        _num(e.get("measured_net"), f"{w} expect.measured_net")
        ws = [_window(x, f"{w} {x.get('census_id')}", True) for x in r["windows"]]
        if not ws:
            raise InputsError(f"{w}: no window to release")
        for x in ws:
            win_once(r["line_id"], x, w)
        rg = r.get("range_line")
        if rg:
            once(_lid(rg.get("line_id"), w), w)
            _num((rg.get("expect") or {}).get("low"), f"{w} range expect.low")
            _num((rg.get("expect") or {}).get("high"), f"{w} range expect.high", pos=True)
        rel.append(dict(r, _windows=ws, _released=_r(sum(x["_edge"] for x in ws))))
    nar = []
    for r in doc.get("narrows") or ():
        w = f"narrow {r.get('line_id')}"
        _need(r, ("line_id", "expect", "windows"), w)
        _tasks(r, srcs, w)
        once(_lid(r["line_id"], w), w)
        _num((r["expect"] or {}).get("low"), f"{w} expect.low")
        _num((r["expect"] or {}).get("high"), f"{w} expect.high", pos=True)
        ws = [_window(x, f"{w} {x.get('census_id')}", False) for x in r["windows"]]
        if not ws:
            raise InputsError(f"{w}: no window to take out of the range")
        for x in ws:
            win_once(r["line_id"], x, w)
        nar.append(dict(r, _windows=ws, _out=_r(sum(x["_edge"] for x in ws))))
    mis, rooms = [], set()
    for m in doc.get("missing") or ():
        w = f"missing {m.get('engine_room')}"
        _need(m, ("engine_room", "floor", "template_line", "room_kind", "why"), w)
        _tasks(m, srcs, w)
        _lid(m["template_line"], w)
        if m["room_kind"] != "DRY":
            raise InputsError(f"{w}: a skirting line is added only for a DRY room (got {m['room_kind']})")
        if m["engine_room"] in rooms:
            raise InputsError(f"{w}: room named twice")
        rooms.add(m["engine_room"])
        if "value" in m and m["value"] not in (None, ""):
            raise InputsError(f"{w}: HELD_WITH_VALUE: a missing line is added held blank (no independent measure)")
        b = m.get("engine_boundary_lm")
        mis.append(dict(m, _boundary=None if b in (None, "") else _num(b, f"{w} engine_boundary_lm", pos=True)))
    if not (rel or nar or mis):
        raise InputsError("no release, narrowing or missing line in the inputs")
    return dict(doc, _sources=srcs, _releases=rel, _narrows=nar, _missing=mis)


# ================================================================================================ helpers
def _ver(srcs):
    return {"task": "+".join(s["task"] for s in srcs), "merge_commit": srcs[0]["merge_commit"],
            "merge_commits": [s["merge_commit"] for s in srcs],
            "verifier_run": "; ".join(s["checker_run"] for s in srcs), "ledger": "; ".join(s["file"] for s in srcs)}


def _rec(piece, srcs, **kw):
    return dict({"piece": piece, "policy": PIECES[piece]["policy"], "tasks": [s["task"] for s in srcs],
                 "ledgers": [s["file"] for s in srcs], "ledger_sha256": [s["sha256"] for s in srcs],
                 "merge_commits": [s["merge_commit"] for s in srcs], "checker_runs": [s["checker_run"] for s in srcs],
                 "rule_id": RULE_ID, "rule_version": RULE_VERSION, "release_status": "NOT RELEASED"}, **kw)


def _fin(ln):
    from engine.source import boq_line as BL
    ln["project"] = copy.deepcopy(ln["project"])
    return BL.validate(ln)


def _inputs(ln):
    c = ln["calculation"] = dict(ln.get("calculation") or {})
    c["inputs"] = dict(c.get("inputs") or {})
    return c["inputs"]


def _is_skirting(ln):
    return ln["item_code"] == CODE and ln["unit"] == UNIT


def _room(ln):
    return (ln.get("location") or {}).get("room_id")


def _released(b, r, srcs):
    """the determinate line with the released windows' listed halves out of its list. -> (line, removed items)"""
    if b is None or not _is_skirting(b):
        raise InputsError(f"release {r['line_id']}: not a {CODE} {UNIT} line of the candidate (stale binding)")
    e = r["expect"]
    if b["evidence_state"] not in VALUED_STATES or not isinstance(b.get("gross"), (int, float)) or \
            b.get("measured_net") is None or abs(b["gross"] - e["gross"]) > BIND_TOL or \
            abs(b["measured_net"] - e["measured_net"]) > BIND_TOL:
        raise InputsError(f"release {r['line_id']}: {b['evidence_state']} gross {b.get('gross')} net "
                          f"{b.get('measured_net')} is not the ledger's {e} (stale binding)")
    cids = {x["census_id"] for x in r["_windows"]}
    ded = list(b.get("deductions") or [])
    out = [x for x in ded if isinstance(x, dict) and x.get("census_id") in cids]
    keep = [x for x in ded if not (isinstance(x, dict) and x.get("census_id") in cids)]
    for x in r["_windows"]:
        got = [y for y in out if y.get("census_id") == x["census_id"]]
        if not got:
            raise InputsError(f"release {r['line_id']}: window {x['census_id']} is not in the line's list (nothing "
                              f"to release; a line never rises past its gross)")
        if any(y.get("physical_check") == "CONSISTENT" for y in got):
            raise InputsError(f"release {r['line_id']}: window {x['census_id']} is listed CONSISTENT (no skirting) "
                              f"by the merged listing; the readings disagree (stopped)")
        s = sum(float(y.get("qty") or 0) for y in got)
        if abs(s - x["_edge"]) > TOL:
            raise InputsError(f"release {r['line_id']}: window {x['census_id']} listed {s} lm, the ledger edge is "
                              f"{x['_edge']} (partial or doubled listing)")
    gone = _r(sum(float(y.get("qty") or 0) for y in out))
    new = copy.deepcopy(b)
    new["deductions"] = copy.deepcopy(keep)
    net = _r(b["measured_net"] + gone)
    if net - b["gross"] > TOL:
        raise InputsError(f"release {r['line_id']}: net {net} would exceed the gross {b['gross']}")
    new["measured_net"] = net
    d = sum(float(x.get("qty") or 0) for x in keep if isinstance(x, dict))
    a = sum(float(x.get("qty") or 0) for x in (new.get("additions") or []) if isinstance(x, dict))
    if abs(new["gross"] - d + a - net) > TOL:
        raise InputsError(f"release {r['line_id']}: gross - list + additions {_r(new['gross'] - d + a)} is not the "
                          f"released net {net}")
    wtxt = ", ".join(f"{x['census_id']} {_fmt(x['_edge'])} (sill {_fmt(x['sill_m'])} m {x['status']})"
                     for x in r["_windows"])
    inp = _inputs(new)
    inp[REC_KEY] = _rec(P_RELEASE, srcs, action="RELEASE", windows=[
        {"census_id": x["census_id"], "edge_lm": x["_edge"], "sill_m": x["sill_m"], "status": x["status"],
         "why": x["why"][:300]} for x in r["_windows"]], removed_items=copy.deepcopy(out),
        was={"measured_net": b["measured_net"], "deductions_sum": _r(d + gone)}, released_lm=gone,
        range_line=(r.get("range_line") or {}).get("line_id"), evidence_status="DRAWING-CONFIRMED")
    new["calculation"]["formula"] = (f"{b['calculation'].get('formula') or ''}; {METHOD}: + {_fmt(gone)} lm window "
                                     f"base(s) under a sill above the floor ({wtxt}) = {_fmt(net)} lm")[:1500]
    A305._note(new, f"{METHOD}: threshold release {wtxt}: net {_fmt(b['measured_net'])} -> {_fmt(net)} lm; listed "
                    f"halves out of the list; NOT RELEASED")
    return _fin(new), out


def _absorbed(rg, r, det, srcs):
    """the room's range line once the released edges are carried by the determinate line. -> line"""
    lid = r["range_line"]["line_id"]
    if rg is None or not _is_skirting(rg):
        raise InputsError(f"range line {lid}: not a {CODE} {UNIT} line of the candidate (stale binding)")
    br, e = rg.get("bounded_range") or {}, r["range_line"]["expect"]
    if rg["evidence_state"] != RANGE_STATE or rg.get("measured_net") is not None or \
            abs((br.get("low") or 0) - e["low"]) > BIND_TOL or abs((br.get("high") or 0) - e["high"]) > BIND_TOL:
        raise InputsError(f"range line {lid}: {rg['evidence_state']} {br.get('low')} .. {br.get('high')} is not the "
                          f"ledger's held range {e['low']} .. {e['high']} (stale binding)")
    if _room(rg) != _room(det) or (rg.get("location") or {}).get("floor") != (det.get("location") or {}).get("floor"):
        raise InputsError(f"range line {lid}: not the range line of the released line's room")
    hi = _r(br["high"] - r["_released"])
    if hi < -TOL:
        raise InputsError(f"range line {lid}: releases {r['_released']} lm, more than its range high {br['high']}")
    new = copy.deepcopy(rg)
    inp = _inputs(new)
    was = {"low": br.get("low"), "high": br.get("high"), "basis": br.get("basis")}
    if abs(hi) <= TOL:
        new["evidence_state"] = NA_STATE
        new["bounded_range"] = None
        new["rfi"] = None
        new["calculation"]["formula"] = (f"NOT_APPLICABLE: the held window base(s) "
                                         f"{', '.join(x['census_id'] for x in r['_windows'])} "
                                         f"({_fmt(r['_released'])} lm) are carried by the determinate line "
                                         f"{det['line_id']} ({METHOD}); was range {_fmt(was['low'])} .. "
                                         f"{_fmt(was['high'])}")[:1500]
        A305._note(new, f"{METHOD}: NOT_APPLICABLE_WITH_EVIDENCE: counted in {det['line_id']} (sill above the floor "
                        f"established; carried once)")
        action = "ABSORB_RANGE"
    else:
        new["bounded_range"] = dict(br, high=hi, low=min(br.get("low") or 0, hi),
                                    basis=f"{br.get('basis') or ''} ({METHOD}: - {_fmt(r['_released'])} released)"[:300])
        A305._note(new, f"{METHOD}: range {_fmt(was['low'])} .. {_fmt(was['high'])} -> "
                        f"{_fmt(new['bounded_range']['low'])} .. {_fmt(hi)} lm ({_fmt(r['_released'])} released into "
                        f"{det['line_id']})")
        action = "NARROW_RANGE"
    inp[REC_KEY] = _rec(P_RELEASE, srcs, action=action, was=was, released_lm=r["_released"],
                        carried_by=det["line_id"], evidence_status="DRAWING-CONFIRMED")
    return _fin(new), action


def _narrowed(ln, r, srcs):
    lid = r["line_id"]
    if ln is None or not _is_skirting(ln):
        raise InputsError(f"narrow {lid}: not a {CODE} {UNIT} line of the candidate (stale binding)")
    br, e = ln.get("bounded_range") or {}, r["expect"]
    if ln["evidence_state"] != RANGE_STATE or ln.get("measured_net") is not None or \
            abs((br.get("low") or 0) - e["low"]) > BIND_TOL or abs((br.get("high") or 0) - e["high"]) > BIND_TOL:
        raise InputsError(f"narrow {lid}: {ln['evidence_state']} {br.get('low')} .. {br.get('high')} is not the "
                          f"ledger's held range {e['low']} .. {e['high']} (a valued line is never narrowed; stale)")
    hi = _r(br["high"] - r["_out"])
    if hi <= TOL:
        raise InputsError(f"narrow {lid}: the windows take the whole range {br['high']} (that is not a narrowing: "
                          f"re-read the line)")
    new = copy.deepcopy(ln)
    was = {"low": br.get("low"), "high": br.get("high"), "basis": br.get("basis")}
    wtxt = ", ".join(f"{x['census_id']} {_fmt(x['_edge'])} ({x['reason']})" for x in r["_windows"])
    new["bounded_range"] = dict(br, high=hi, low=min(br.get("low") or 0, hi),
                                basis=f"{br.get('basis') or ''} ({METHOD}: - {wtxt})"[:300])
    _inputs(new)[REC_KEY] = _rec(P_NARROW, srcs, action="NARROW_RANGE", was=was, low=new["bounded_range"]["low"],
                                 high=hi, windows=[{"census_id": x["census_id"], "edge_lm": x["_edge"],
                                                    "sill_m": x.get("sill_m"), "reason": x["reason"],
                                                    "status": x["status"], "why": x["why"][:300]}
                                                   for x in r["_windows"]],
                                 evidence_status=ln["calculation"]["inputs"].get("evidence_status") or "HELD")
    A305._note(new, f"{METHOD}: held range {_fmt(was['low'])} .. {_fmt(was['high'])} -> "
                    f"{_fmt(new['bounded_range']['low'])} .. {_fmt(hi)} lm (no skirting under {wtxt}); state unchanged")
    return _fin(new)


def _missing_line(m, tpl, srcs):
    from engine.source import boq_line as BL
    room = m["engine_room"]
    beside = (f"engine boundary {_fmt(m['_boundary'])} m (the engine's own figure, not an independent measure; "
              f"doors not deducted): beside, never the quantity" if m["_boundary"] is not None else
              "no boundary figure")
    formula = (f"{METHOD}: HELD (never a value) skirting of the dry room {room}: the candidate carries no skirting "
               f"line for it (engine omission); {m['why'][:400]} | {beside}")[:1500]
    rec = _rec(P_MISSING, srcs, action="ADD_MISSING", engine_room=room, room_kind=m["room_kind"],
               engine_boundary_lm=m["_boundary"], why=m["why"][:600], evidence_status="HELD")
    loc = tpl.get("location") or {}
    ln = BL.make_line(
        project_id=tpl["project"]["project_id"], revision_set_sha256=tpl["project"]["revision_set_sha256"],
        item_code=CODE, unit=UNIT, evidence_state=HELD_STATE, measured_net=None, gross=None,
        element_id=f"SKIRT-T422:{room}", floor=m["floor"], room_id=room,
        room_name_en=m.get("room_name_en"), room_name_ar=m.get("room_name_ar"),
        physical_element="skirting at the foot of the finished dry wall faces of the room",
        formula=formula, inputs={REC_KEY: rec, "evidence_status": "HELD"},
        documents=copy.deepcopy(tpl["source"]["documents"]), geometry_source=tpl["source"]["geometry_source"],
        geometry_confidence=tpl["source"]["geometry_confidence"], rule_id=RULE_ID, rule_version=RULE_VERSION,
        material_state=tpl.get("material_state") or "BY_SPEC",
        rfi={"question": f"skirting of the dry room {room}: walk the wall bases and deduct the doors by id "
                         f"(no merged independent walk)"[:900], "unlocks": f"SKIRT-T422:{room}",
             "bound_beside": beside[:300]},
        notes=f"{METHOD}: MISSING skirting line named, HELD BLANK (never 0); NOT RELEASED",
        trade=tpl.get("trade"), subtrade=tpl.get("subtrade"))
    if loc.get("floor") != m["floor"]:
        raise InputsError(f"missing {room}: template line floor {loc.get('floor')} is not {m['floor']}")
    return _fin(ln)


# ================================================================================================ changes
def changes_for(doc, l3043):
    """-> (changes, log). Each change: piece, action (CHANGE / ADD), before (a V3.0.43 line or None), after."""
    if not doc:
        return [], {"piece": "+".join((P_RELEASE, P_NARROW, P_MISSING)), "state": "NO_PROJECT_INPUT"}
    if any(((ln.get("calculation") or {}).get("inputs") or {}).get(REC_KEY) for ln in l3043):
        raise InputsError("the candidate already carries V3.0.44 records (applied once)")
    by = {ln["line_id"]: ln for ln in l3043}
    S = doc["_sources"]
    changes, seen = [], set(by)
    log = {"piece": "+".join((P_RELEASE, P_NARROW, P_MISSING)), "state": "RUN", "sources": doc["sources"],
           "by_action": {}, "lines_added": 0, "lines_changed": 0, "released_lm": 0.0, "range_out_lm": 0.0,
           "range_absorbed_lm": 0.0, "missing_rooms": []}

    def add(piece, action, after, before=None, **kw):
        if before is None:
            if after["line_id"] in seen:
                raise InputsError(f"{METHOD}: added line {after['location']['element_id']} repeats an id")
            seen.add(after["line_id"])
            log["lines_added"] += 1
        else:
            if before["line_id"] != after["line_id"]:
                raise ValueError(f"{METHOD}: a changed line keeps its id")
            log["lines_changed"] += 1
        log["by_action"][action] = log["by_action"].get(action, 0) + 1
        srcs = kw.pop("srcs")
        changes.append(A305._change(piece, "ADD" if before is None else "CHANGE", before, after,
                                    step=action, drawing_reference="; ".join(s["file"] for s in srcs),
                                    verification=_ver(srcs), downstream=kw.pop("downstream", []),
                                    group=after["item_code"], **kw))

    for r in doc["_releases"]:
        srcs = [S[t] for t in r["source_tasks"]]
        b = by.get(r["line_id"])
        det, removed = _released(b, r, srcs)
        add(P_RELEASE, "RELEASE", det, before=b, srcs=srcs, evidence_status="DRAWING-CONFIRMED", held=[],
            downstream=["skirting roll-up: certain lm up by the released edge(s)",
                        "T-330 check: the line closes gross - list + additions = net (list shorter)"])
        log["released_lm"] = _r(log["released_lm"] + r["_released"])
        if r.get("range_line"):
            rg = by.get(r["range_line"]["line_id"])
            after, action = _absorbed(rg, r, det, srcs)
            add(P_RELEASE, action, after, before=rg, srcs=srcs, evidence_status="DRAWING-CONFIRMED",
                held=[] if action == "ABSORB_RANGE" else [
                    {"what": f"{CODE} {rg['line_id']}", "why": "rest of the range not released",
                     "range": f"{_fmt(after['bounded_range']['low'])} .. {_fmt(after['bounded_range']['high'])}",
                     "scenario": "held range only"}],
                downstream=["skirting roll-up: held high down by the same edge(s) (carried once)"])
            log["range_absorbed_lm"] = _r(log["range_absorbed_lm"] + r["_released"])
    for r in doc["_narrows"]:
        srcs = [S[t] for t in r["source_tasks"]]
        ln = by.get(r["line_id"])
        new = _narrowed(ln, r, srcs)
        add(P_NARROW, "NARROW_RANGE", new, before=ln, srcs=srcs, evidence_status="HELD",
            held=[{"what": f"{CODE} {r['line_id']}", "why": "the rest of the range stays held (sill / stair)",
                   "range": f"{_fmt(new['bounded_range']['low'])} .. {_fmt(new['bounded_range']['high'])}",
                   "scenario": "held range only"}],
            downstream=["skirting roll-up: held high down; no value moves"])
        log["range_out_lm"] = _r(log["range_out_lm"] + r["_out"])
    for m in doc["_missing"]:
        srcs = [S[t] for t in m["source_tasks"]]
        tpl = by.get(m["template_line"])
        if tpl is None or not _is_skirting(tpl):
            raise InputsError(f"missing {m['engine_room']}: template {m['template_line']} is not a {CODE} line "
                              f"(stale binding)")
        have = [ln["line_id"] for ln in l3043 if _is_skirting(ln) and _room(ln) == m["engine_room"]]
        if have:
            raise InputsError(f"missing {m['engine_room']}: the candidate already carries skirting line(s) {have[:3]} "
                              f"for this room (not missing)")
        new = _missing_line(m, tpl, srcs)
        add(P_MISSING, "ADD_MISSING", new, srcs=srcs, evidence_status="HELD",
            held=[{"what": f"{CODE} {m['engine_room']}", "why": m["why"][:300], "range": None,
                   "scenario": "held blank: no merged independent walk of the room"}],
            downstream=["skirting completeness: the dry room now has a line (held)"])
        log["missing_rooms"].append(m["engine_room"])
    log["by_action"] = dict(sorted(log["by_action"].items()))
    return changes, log


# ================================================================================================ checks
def check_skirting(lines, before=None):
    """R-T422-1 on the integrated lines: a released line is valued, closes gross - list + additions = net, carries no
    item of a released window and rose by exactly its released edges (when `before` is given); an absorbed range line
    is NOT_APPLICABLE without a figure and names a determinate line that is in the candidate; a narrowed line stays a
    held range with low <= high; a missing line is HELD BLANK. -> summary."""
    out = {"released_lines": 0, "released_lm": 0.0, "absorbed": 0, "narrowed": 0, "missing": 0}
    ids = {ln["line_id"]: ln for ln in lines}
    b4 = {ln["line_id"]: ln for ln in before or ()}
    for ln in lines:
        rec = ((ln.get("calculation") or {}).get("inputs") or {}).get(REC_KEY)
        if not rec:
            continue
        if not _is_skirting(ln):
            raise ValueError(f"{METHOD}: a V3.0.44 record on {ln['item_code']} {ln['line_id']}")
        act = rec.get("action")
        if act == "RELEASE":
            cids = {w["census_id"] for w in rec["windows"]}
            if ln["evidence_state"] not in VALUED_STATES or ln.get("measured_net") is None:
                raise ValueError(f"{METHOD}: released line {ln['line_id']} is not valued")
            if any(isinstance(x, dict) and x.get("census_id") in cids for x in ln.get("deductions") or ()):
                raise ValueError(f"{METHOD}: released line {ln['line_id']} still lists a released window")
            d = sum(float(x.get("qty") or 0) for x in ln.get("deductions") or () if isinstance(x, dict))
            a = sum(float(x.get("qty") or 0) for x in ln.get("additions") or () if isinstance(x, dict))
            if abs(ln["gross"] - d + a - ln["measured_net"]) > TOL:
                raise ValueError(f"{METHOD}: released line {ln['line_id']} does not close")
            o = b4.get(ln["line_id"])
            if o is not None and abs(ln["measured_net"] - o["measured_net"] - rec["released_lm"]) > TOL:
                raise ValueError(f"{METHOD}: released line {ln['line_id']} moved by other than its released edges")
            out["released_lines"] += 1
            out["released_lm"] = _r(out["released_lm"] + rec["released_lm"])
        elif act == "ABSORB_RANGE":
            if ln["evidence_state"] != NA_STATE or ln.get("measured_net") is not None or ln.get("bounded_range"):
                raise ValueError(f"{METHOD}: absorbed range line {ln['line_id']} carries a figure")
            if rec.get("carried_by") not in ids:
                raise ValueError(f"{METHOD}: absorbed range line {ln['line_id']} names no candidate line")
            out["absorbed"] += 1
        elif act == "NARROW_RANGE":
            br = ln.get("bounded_range") or {}
            if ln["evidence_state"] != RANGE_STATE or ln.get("measured_net") is not None or \
                    br.get("low") is None or br.get("high") is None or br["low"] > br["high"] + 1e-12:
                raise ValueError(f"{METHOD}: narrowed line {ln['line_id']} is not a held range")
            o = b4.get(ln["line_id"])
            if o is not None:
                for k in ("evidence_state", "measured_net", "gross", "rfi", "item_code", "unit", "location"):
                    if o.get(k) != ln.get(k):
                        raise ValueError(f"{METHOD}: narrowed line {ln['line_id']} moved {k}")
                if br["high"] > (o.get("bounded_range") or {}).get("high", 0) + 1e-12:
                    raise ValueError(f"{METHOD}: narrowed line {ln['line_id']} rose")
            out["narrowed"] += 1
        elif act == "ADD_MISSING":
            if ln["evidence_state"] != HELD_STATE or ln.get("measured_net") is not None or \
                    ln.get("gross") is not None or ln.get("bounded_range") is not None:
                raise ValueError(f"{METHOD}: missing line {ln['line_id']} is not HELD BLANK (never 0)")
            out["missing"] += 1
        else:
            raise ValueError(f"{METHOD}: action {act} on {ln['line_id']}")
    return out


# ================================================================================================ integrate / write
def integrate(l3043, changes, for_lead=()):
    """-> (V3.0.44 lines, identity). Changed lines replace their V3.0.43 line in place; added lines follow; every other
    V3.0.43 line is byte-identical (asserted)."""
    sid = {ln["line_id"]: i for i, ln in enumerate(l3043)}
    out = list(l3043)
    adds, repl = [], set()
    for c in changes:
        a = c["after"]
        if a["item_code"] != CODE:
            raise ValueError(f"{METHOD}: {a['item_code']} is not the code this version may change or add")
        if c["action"] == "ADD":
            if a["line_id"] in sid:
                raise ValueError(f"{METHOD}: an added line repeats a V3.0.43 id")
            adds.append(a)
        elif c["action"] == "CHANGE":
            i = sid.get(a["line_id"])
            if i is None or a["line_id"] in repl:
                raise ValueError(f"{METHOD}: a changed line is not a V3.0.43 line or changes twice")
            out[i] = a
            repl.add(a["line_id"])
        else:
            raise ValueError(f"{METHOD}: action {c['action']}")
    out = out + adds
    if len({ln["line_id"] for ln in out}) != len(out):
        raise ValueError(f"{METHOD}: a BOQ line id appears twice")
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
    flights = A3039.check_flights(out)
    runs = A3040.check_runs(out)
    pieces = A3041.check_pieces(out)
    slab = A3042.check_slab(out)
    earth = A3043.check_earthworks(out)
    skirt = check_skirting(out, l3043)
    pids = {(ln["project"]["project_id"], ln["project"]["revision_set_sha256"]) for ln in out}
    if len(pids) != 1:
        raise ValueError(f"{METHOD}: {len(pids)} project identities in the lines")
    outside = [ln for ln in l3043 if ln["line_id"] not in repl]
    bad = [a["line_id"] for a in outside if A30.line_sha(a) != A30.line_sha(out[sid[a["line_id"]]])]
    if bad:
        raise ValueError(f"{METHOD}: {len(bad)} V3.0.43 line(s) differ outside the named changes")
    ident = {"v3_0_43_lines": len(l3043), "v3_0_44_lines": len(out), "v3_0_44_rows": len(changes),
             "replaced": len(repl), "added": len(adds), "outside_rows": len(outside),
             "outside_rows_identical_to_v3_0_43": len(outside), "skirting": skirt, "earthworks": earth, "slab": slab,
             "pieces": pieces, "gb_runs": runs, "flights": flights, "beds": beds, "lift": lift, "landing": landing,
             "lists": lists, "fence": fence, "tile_zones": zones, "corrections": corr, "ceilings": ceil,
             "roof_buildup": roof, "guards": guards,
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
        rows.append({"version": METHOD, "piece": c["piece"], "action": c.get("step"), "change": c["action"],
                     "line_id": ref["line_id"], "item_code": ref["item_code"], "floor": loc.get("floor"),
                     "room_id": loc.get("room_id"), "element_id": loc.get("element_id"), "unit": ref["unit"],
                     "before_released_v2_9": b29, "before_v3_0_43": A30._qty(c.get("before")),
                     "after_v3_0_44": A30._qty(ref), "evidence_status": c.get("evidence_status"),
                     "still_held": c.get("held"), "release_status": "NOT RELEASED",
                     "owner_manual_method": PIECES[c["piece"]]["owner_manual_method"],
                     "drawing_derived_method": PIECES[c["piece"]]["drawing_method"],
                     "record": rec, "verification": c.get("verification") or {}, "rollback": ROLLBACK})
    return rows


LEDGER_CSV = ("version", "piece", "action", "change", "line_id", "item_code", "floor", "room_id", "element_id", "unit",
              "v2_9", "v3_0_43", "v3_0_44", "evidence_status", "still_held", "verification")
DIFF_CSV = ("line_id", "item_code", "floor", "element_id", "unit", "vs_v3_0_43", "vs_released_v2_9", "v2_9",
            "v3_0_43", "v3_0_44")


def ledger_csv(rows):
    def q(x):
        return A302._q(x) if x and (x.get("value") is not None or x.get("low") is not None or x.get("state")) else ""

    def h(r):
        return "; ".join(f"{x['what']} {x.get('range')}" for x in (r.get("still_held") or ()))[:300]
    return A305._csv([{"version": r["version"], "piece": r["piece"], "action": r["action"], "change": r["change"],
                       "line_id": r["line_id"], "item_code": r["item_code"], "floor": r.get("floor") or "",
                       "room_id": r.get("room_id") or "", "element_id": r.get("element_id") or "", "unit": r["unit"],
                       "v2_9": q(r.get("before_released_v2_9")), "v3_0_43": q(r.get("before_v3_0_43")),
                       "v3_0_44": q(r.get("after_v3_0_44")), "evidence_status": r["evidence_status"],
                       "still_held": h(r),
                       "verification": f"{r['verification'].get('task')} "
                                       f"{' '.join(x[:8] for x in r['verification'].get('merge_commits') or ())}"}
                      for r in rows], LEDGER_CSV)


def diff_rows(l3043, l3044, released_lines=None):
    b43 = {ln["line_id"]: ln for ln in l3043}
    rel = {A30._key(ln): ln for ln in released_lines or ()}
    out = []
    for ln in l3044:
        o = b43.get(ln["line_id"])
        vs = "ADDED" if o is None else ("SAME" if A30.line_sha(o) == A30.line_sha(ln) else "CHANGED")
        r = rel.get(A30._key(ln)) if released_lines is not None else None
        vs29 = None if released_lines is None else ("NOT_IN_RELEASED" if r is None else
                                                    ("SAME_QUANTITY" if A30._qty(r) == A30._qty(ln) else
                                                     "QUANTITY_DIFFERS"))
        out.append({"line_id": ln["line_id"], "item_code": ln["item_code"], "floor": ln["location"].get("floor"),
                    "element_id": ln["location"].get("element_id"), "unit": ln["unit"], "vs_v3_0_43": vs,
                    "vs_released_v2_9": vs29, "v2_9": A302._q(A30._qty(r)) if r else "",
                    "v3_0_43": A302._q(A30._qty(o)) if o else "", "v3_0_44": A302._q(A30._qty(ln))})
    return out


def write(out, l3043, changes, log, released_lines=None, for_lead=()):
    """the V3_0_44_* files beside the V3_0_43_* files. -> (file names, identity, ledger)."""
    from pathlib import Path
    from engine.source import boq_line as BL
    out = Path(out)
    l3044, ident = integrate(l3043, changes, for_lead)
    rows = ledger_rows(changes, released_lines)
    diff = diff_rows(l3043, l3044, released_lines)
    named = {c["after"]["line_id"] for c in changes}
    stray = [d["line_id"] for d in diff if d["vs_v3_0_43"] in ("CHANGED", "ADDED") and d["line_id"] not in named]
    if stray:
        raise ValueError(f"{METHOD}: {len(stray)} line(s) changed outside the named changes")
    dsum = {}
    for d in diff:
        dsum.setdefault("vs_v3_0_43", {}).setdefault(d["vs_v3_0_43"], 0)
        dsum["vs_v3_0_43"][d["vs_v3_0_43"]] += 1
        if d["vs_released_v2_9"] is not None:
            dsum.setdefault("vs_released_v2_9", {}).setdefault(d["vs_released_v2_9"], 0)
            dsum["vs_released_v2_9"][d["vs_released_v2_9"]] += 1
    ident = dict(ident, diff=dsum)
    t43, t44 = A304.code_totals(l3043), A304.code_totals(l3044)
    moved = {k: {"v3_0_43": t43.get(k), "v3_0_44": t44.get(k)} for k in sorted(set(t43) | set(t44))
             if t43.get(k) != t44.get(k)}
    for k in moved:
        if k.split("|")[0] != CODE:
            raise ValueError(f"{METHOD}: totals moved outside this version's code: {k}")
    led = {"schema": LEDGER_SCHEMA, "method": METHOD, "extends": EXTENDS, "candidate": CANDIDATE,
           "base": A30.BASE_METHOD, "released": A30.RELEASED_METHOD, "released_default": False, "rows": rows,
           "waiting_pieces": WAITING, "integration_package": True}
    run = {"method": METHOD, "policy": POLICY_ID, "extends": EXTENDS, "candidate": CANDIDATE,
           "base_method": A30.BASE_METHOD, "released_method": A30.RELEASED_METHOD, "released_default": False,
           "rollback": ROLLBACK, "identity": ident, "pieces": PIECES, "piece_logs": [log],
           "totals_moved_by_code": moved, "waiting_pieces": WAITING}
    files = {"V3_0_44_BOQ_LINES.json": BL.dumps(l3044),
             "V3_0_44_BOQ_LINES.csv": A30._lines_csv(l3044),
             "V3_0_44_INTEGRATION_LEDGER.json": A30._j(led),
             "V3_0_44_INTEGRATION_LEDGER.csv": ledger_csv(rows),
             "V3_0_44_DIFF.csv": A305._csv(diff, DIFF_CSV),
             "V3_0_44_RUN.json": A30._j(run)}
    for name, text in files.items():
        (out / name).write_text(text, encoding="utf-8")
    return sorted(files), ident, led


def policy_record():
    return {"method": METHOD, "extends": EXTENDS, "pieces": sorted(PIECES), "inputs_schema": INPUTS_SCHEMA,
            "released_default": False, "rollback": ROLLBACK, "actions": list(ACTIONS)}


__all__ = ["METHOD", "PIECES", "WAITING", "DEFAULT_GUARD_CLASS", "INPUTS_SCHEMA", "load_inputs", "changes_for",
           "check_skirting", "integrate", "ledger_rows", "diff_rows", "write", "InputsError"]
