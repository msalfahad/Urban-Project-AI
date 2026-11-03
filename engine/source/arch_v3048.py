"""ARCH_TAKEOFF_V3.0.48 (T-483, stream F): the SAME opt-in BOQ candidate as ARCH_TAKEOFF_V3.0 .. V3.0.47
(engine.source.arch_v30, arch_v301 .. arch_v3047), extended with the SKIRTING REMAINDER of the merged T-481 census
(a8609a7a; Checker own re-measure AGREE on W17 / W11 / W02 / the 1F dressing) in ONE step:

  SILL_RELEASE  a window whose sill is now ESTABLISHED above the room floor (> 0.02 m, read in a section or a printed
                elevation chain) has wall under it, so the skirting runs under the sill: its listed halves (held
                UNRESOLVED since V3.0.36) leave the room's determinate line, whose net rises by the window edge; the
                room's held range line, which held exactly that edge, is counted in the determinate line now:
                NOT_APPLICABLE_WITH_EVIDENCE (no figure, never 0, names the line that carries it).
  RANGE_CLOSE   every window of a held range line now has an established reason for NO room skirting under it
                (FLOOR_GLAZING: sill at the floor; STAIR_OWNED: the stretch is a flight / landing face owned by the
                merged stair side table, B7-07 / B7-08): the range is closed NOT_APPLICABLE_WITH_EVIDENCE when the
                windows account for its whole high; a partial close is refused (that is V3.0.44's narrowing).
  CELL_WALK     a BLOCKED skirting line of a dry room with a merged drawing walk of the cell gets its value: sides cut
                into stretches by DXF handle (faces skirted; openings deducted by id; joinery in front of a face is
                not a boundary, reported beside), gross = sides, net = faces, gross - deductions = net.

R-T483-1 (every villa; integrates R-T481-1 / R-T481-2 / R-T481-3 as merged, UP-SKIRT-001 1.4.0, UP-CER-003,
R-T422-1, UP-QTY-STATUS-001): (a) a sill is released only with its status DRAWING-CONFIRMED / PRINTED and a sill above
0.02 m in m; floor glazing needs a sill <= 0.02 m; a stair-owned window names its stair stretch owner; (b) a released
edge is carried once (determinate up, range NA); (c) a range is closed only when its windows take its whole high
(residual <= TOL), otherwise refused; (d) a walk covers each side exactly once with handles on faces and ids on
openings, a door jamb is never skirted, and closes on the declared gross; (e) every binding is checked against the
candidate (state, net, gross, range) and refused if stale; (f) held stays blank, never 0.

NOT IN THIS VERSION (named, unchanged): the 1F ST-1F shaft binding of R-T481-3 (9.050 lm of the 1F living line's
determinate net to B7) needs the engine edges of that line by handle (WAITING T483_1F_SHAFT); the W02 pier D-53.

Nothing else moves: every V3.0.47 line not named by the inputs is byte-identical (asserted); totals move only in
FIN.SKIRTING (asserted). Files: V3_0_48_BOQ_LINES.json / .csv, V3_0_48_INTEGRATION_LEDGER.json / .csv,
V3_0_48_DIFF.csv, V3_0_48_RUN.json. Nothing here names a project, a sheet, a layer or a coordinate.
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
from engine.source import arch_v3044 as A3044
from engine.source import arch_v3045 as A3045
from engine.source import arch_v3046 as A3046
from engine.source import arch_v3047 as A3047

DEFAULT_GUARD_CLASS = "TOOLING"          # T-212: re-books checker-merged ledgers; adds no default value
METHOD = "ARCH_TAKEOFF_V3.0.48"
EXTENDS = A3047.METHOD
CANDIDATE = A30.METHOD
POLICY_ID = "URBAN_BOQ_T483_ARCH_V3_0_48"
INPUTS_SCHEMA = "URBAN_V3048_INPUTS_V1"
LEDGER_SCHEMA = "URBAN_V3048_INTEGRATION_LEDGER_V1"
ROLLBACK = A30.ROLLBACK
InputsError = A3031.InputsError
_r = A3018._r
_fmt = A3030._fmt
RULE_ID, RULE_VERSION = "R-T483-1", "T-483"
REC_KEY = "skirting_remainder_v3048"
CODE, UNIT = "FIN.SKIRTING", "lm"
P_SILL, P_CLOSE, P_WALK = "SILL_RELEASE", "RANGE_CLOSE", "CELL_WALK"
ACTIONS = ("RELEASE", "ABSORB_RANGE", "CLOSE_RANGE", "WALK")
FLOOR_GLAZING_MAX_SILL_M = 0.02          # UP-SKIRT-001 1.4.0 / R-T481-1: masonry base above the FFL > 0.02 m is wall
VALUED_STATES = ("MEASURED", "SOURCE_DERIVED", "PROVISIONAL")
RANGE_STATE, HELD_STATE, NA_STATE = "BOUNDED_EXPOSURE", "BLOCKED_RFI", "NOT_APPLICABLE_WITH_EVIDENCE"
SKIRTED_STATUS = ("DRAWING-CONFIRMED", "PRINTED")
CLOSE_WHY = ("FLOOR_GLAZING", "STAIR_OWNED")
FACE = ("WALL", "COLUMN")
OPENINGS = ("DOOR", "PASSAGE", "ARCH", "LIFT_OPENING")
WALK_KINDS = FACE + OPENINGS
TOL = 0.0005                             # tools/boq_export_v1.QTY_MATCH_TOL (the T-330 check's tolerance)
BIND_TOL = 1e-6
GEOM_TOL = 1e-6
MAX_EDGE_M = 20.0                        # one window edge / one side in m; above it is a unit slip (mm / cm)
MAX_SILL_M = 6.0
LINE_ID_RE = re.compile(r"^L-[0-9a-f]{20}$")

PIECES = {
    P_SILL: {"module": "engine/source/arch_v3048.py (a window sill established above the floor by a section or a "
                       "printed chain: its base released into the room's determinate skirting line; the room's range "
                       "line counted in it)", "policy": "SKIRTING_SILL_RELEASE_V2", "rule_id": "R-T481-1 (R-T483-1 a, b)",
             "owner_rules": ["UP-SKIRT-001 1.4.0 (the wall base continues under a sill above the floor)",
                             "UP-CER-002 (skirting in lm)", "UP-CER-003 (doors / passages deducted)",
                             "UP-QTY-STATUS-001 (held is blank, never 0)"],
             "owner_manual_method": "room perimeter at floor level less each door / passage width by opening; a "
                                    "window is deducted only where no wall continues under it (sill at the floor)",
             "drawing_method": "the merged T-481 sill reading of each window (section cut on printed level markers, "
                               "elevation chain; spread across views named): sill above the floor -> both listed "
                               "halves leave the list"},
    P_CLOSE: {"module": "engine/source/arch_v3048.py (a held range whose every window has no room skirting under it "
                        "closed NOT_APPLICABLE_WITH_EVIDENCE)", "policy": "SKIRTING_RANGE_CLOSE_V1",
              "rule_id": "R-T481-1 / R-T481-3 (R-T483-1 a, c)",
              "owner_rules": ["UP-SKIRT-001 1.4.0 (floor glazing: no wall base)",
                              "OWNER_RULE_STAIRS (a face along a flight / landing is stair skirting, B7-07 / B7-08)",
                              "UP-QTY-STATUS-001"],
              "owner_manual_method": "not a quantity: the held window edge is either floor glazing (no base) or a "
                                     "stair face (the stair skirting owns it)",
              "drawing_method": "the merged T-481 readings: sill 0.00 drawing-confirmed (floor glazing), or the "
                                "window's stretch inside a merged T-410 stair side stretch (station by nosing)"},
    P_WALK: {"module": "engine/source/arch_v3048.py (a blocked dry-cell skirting line valued from the merged walk: "
                       "sides by handle, openings by id)", "policy": "SKIRTING_CELL_WALK_V1",
             "rule_id": "R-T481-2 (R-T483-1 d)",
             "owner_rules": ["UP-SKIRT-001 (dry room: skirting at the wall base)", "UP-CER-003 (doors deducted)",
                             "WALL_CONTACT_PATH_POLICY V1 / V2 (joinery is never a site boundary)",
                             "UP-QTY-STATUS-001"],
             "owner_manual_method": "room perimeter at floor level less the door / arch widths by id",
             "drawing_method": "the merged T-481 cell walk on the plan by handle: each side cut into stretches, faces "
                               "skirted, openings deducted by id, joinery-backed length beside (not deducted)"},
}
WAITING = dict(A3047.WAITING)
WAITING.pop("T443_1F_SHAFT", None)
WAITING.update({
    "T483_1F_SHAFT": "1F living line: the ST-1F shaft faces (R-T481-3: 9.050 lm along flights / landings to B7, 1.175 "
                     "lm room) stay inside the determinate net until the engine edges of that line are bound by handle "
                     "(no edge-level record in the line): a separate package; its W13 / W25 range is closed here "
                     "(STAIR_OWNED)",
    "T483_W02_PIER": "W02 pier (D-53): if the designer confirms one, its room face takes skirting; no width drawn, "
                     "nothing valued",
})


# ================================================================================================ inputs
def _need(s, keys, where):
    for k in keys:
        if s.get(k) in (None, ""):
            raise InputsError(f"{where}: {k} missing")


def _num(x, where, pos=False, top=2000.0):
    if not isinstance(x, (int, float)) or isinstance(x, bool) or x != x:
        raise InputsError(f"{where}: {x!r} is not a number")
    if x < 0 or (pos and x == 0):
        raise InputsError(f"{where}: {x!r} is {'not positive' if pos else 'negative'}")
    if x > top:
        raise InputsError(f"{where}: {x} is not a length in m (mm / cm refused)")
    return float(x)


def _lid(x, where):
    if not LINE_ID_RE.match(str(x)):
        raise InputsError(f"{where}: {x!r} is not a BOQ line id")
    return x


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


def _sill(x, where):
    if not isinstance(x, (int, float)) or isinstance(x, bool) or x != x or x < 0 or x > MAX_SILL_M:
        raise InputsError(f"{where}: sill {x!r} is not a sill height in m above the FFL (mm refused)")
    return float(x)


def _window(w, where, mode):
    """mode RELEASE: sill established above the floor; CLOSE: FLOOR_GLAZING (sill <= 0.02) or STAIR_OWNED (owner)."""
    _need(w, ("census_id", "status", "why"), where)
    e = _num(w.get("edge_lm"), f"{where} edge_lm", pos=True, top=MAX_EDGE_M)
    if w["status"] not in SKIRTED_STATUS:
        raise InputsError(f"{where}: status {w['status']!r} is not {SKIRTED_STATUS} (an unread sill stays held)")
    if mode == "RELEASE":
        s = _sill(w.get("sill_m"), where)
        if s <= FLOOR_GLAZING_MAX_SILL_M:
            raise InputsError(f"{where}: sill {s} m is not above the floor: nothing to release")
    else:
        why = w.get("reason")
        if why not in CLOSE_WHY:
            raise InputsError(f"{where}: a range close needs its reason {CLOSE_WHY}")
        if why == "FLOOR_GLAZING" and _sill(w.get("sill_m"), where) > FLOOR_GLAZING_MAX_SILL_M:
            raise InputsError(f"{where}: floor glazing needs an established sill <= {FLOOR_GLAZING_MAX_SILL_M} m")
        if why == "STAIR_OWNED" and not w.get("owner"):
            raise InputsError(f"{where}: a stair-owned window names its stair side stretch owner")
    return dict(w, _edge=e)


def check_walk(wk, where):
    """R-T483-1 d: each side covered once by its stretches; faces carry handles; openings carry ids. -> measured."""
    gross, net, ded, rows, ids = 0.0, 0.0, [], [], set()
    for sd in wk.get("sides") or ():
        sw = f"{where} side {sd.get('id')}"
        _need(sd, ("id",), sw)
        L = _num(sd.get("length"), f"{sw} length", pos=True, top=MAX_EDGE_M)
        pos = 0.0
        for st in sd.get("stretches") or ():
            k = st.get("kind")
            if k not in WALK_KINDS:
                raise InputsError(f"{sw}: unknown stretch kind {k!r} (joinery is never a boundary)")
            a = _num(st.get("s0"), f"{sw} s0", top=MAX_EDGE_M)
            b = _num(st.get("s1"), f"{sw} s1", top=MAX_EDGE_M)
            if b - a <= GEOM_TOL:
                raise InputsError(f"{sw}: empty or reversed stretch {a} .. {b}")
            if abs(a - pos) > GEOM_TOL:
                raise InputsError(f"{sw}: {'gap' if a > pos else 'overlap'} at s {pos:.4f} .. {a:.4f}")
            ln = _r(b - a)
            if k in FACE:
                if not str(st.get("handles") or "").split():
                    raise InputsError(f"{sw}: {k} face at s {a:.4f} without a drawn handle")
                net += ln
            else:
                oid = st.get("opening_id")
                if not oid:
                    raise InputsError(f"{sw}: {k} at s {a:.4f} deducted without an opening id (R-T246)")
                if oid in ids:
                    raise InputsError(f"{sw}: opening {oid} deducted twice")
                ids.add(oid)
                ded.append({"opening_id": oid, "kind": k, "qty": ln, "side": sd["id"], "jamb_skirting": False,
                            "why": "opening deducted by id (UP-CER-003); no jamb return"})
            gross += ln
            rows.append({"side": sd["id"], "s0": a, "s1": b, "kind": k, "length_m": ln,
                         "handles": st.get("handles") or "", "opening_id": st.get("opening_id") or ""})
            pos = b
        if abs(pos - L) > GEOM_TOL:
            raise InputsError(f"{sw}: stretches end at {pos:.4f}, the side is {L:.4f} (short cover)")
    if not rows:
        raise InputsError(f"{where}: no side walked")
    if wk.get("jambs"):
        raise InputsError(f"{where}: a jamb return given skirting (a door / arch jamb is never skirted here)")
    gross, net = _r(gross), _r(net)
    if net <= 0:
        raise InputsError(f"{where}: no skirted face")
    return {"gross": gross, "net": net, "deductions": ded, "deducted": _r(sum(d["qty"] for d in ded)), "rows": rows}


def load_inputs(doc, project_id=None):
    """URBAN_V3048_INPUTS_V1 -> the validated doc.
    {"schema", "project_id", "sources": [{"task", "file", "sha256", "merge_commit", "checker_run"}],
     "releases": [{"line_id", "expect": {"gross", "measured_net"}, "windows": [{"census_id", "edge_lm", "sill_m",
                   "status", "why"}], "range_line": {"line_id", "expect": {"low", "high"}}, "source_tasks"}],
     "closes": [{"line_id", "expect": {"low", "high"}, "windows": [{"census_id", "edge_lm", "sill_m", "status",
                 "reason" FLOOR_GLAZING / STAIR_OWNED, "owner", "why"}], "source_tasks"}],
     "walks": [{"line_id", "room", "floor", "expect": {"evidence_state"}, "gross_lm", "evidence_status",
                "evidence_state", "joinery_backed_lm", "sides": [{"id", "length", "stretches": [{"s0", "s1", "kind",
                "handles" | "opening_id"}]}], "source_tasks"}]}"""
    if not doc:
        return None
    if doc.get("schema") != INPUTS_SCHEMA:
        raise InputsError(f"project inputs: schema must be {INPUTS_SCHEMA}")
    if project_id and doc.get("project_id") not in (None, project_id):
        raise InputsError(f"project inputs are for {doc.get('project_id')!r}, the run is {project_id!r}")
    srcs = _sources(doc)
    named = set()

    def once(lid, where):
        if lid in named:
            raise InputsError(f"{where}: line {lid} named twice (one change per line)")
        named.add(lid)

    rel = []
    for r in doc.get("releases") or ():
        w = f"release {r.get('line_id')}"
        _need(r, ("line_id", "expect", "windows", "range_line"), w)
        _tasks(r, srcs, w)
        once(_lid(r["line_id"], w), w)
        _num(r["expect"].get("gross"), f"{w} expect.gross", pos=True)
        _num(r["expect"].get("measured_net"), f"{w} expect.measured_net")
        ws = [_window(x, f"{w} {x.get('census_id')}", "RELEASE") for x in r["windows"]]
        if not ws or len({x["census_id"] for x in ws}) != len(ws):
            raise InputsError(f"{w}: no window, or a window named twice")
        rg = r["range_line"]
        once(_lid(rg.get("line_id"), w), w)
        _num((rg.get("expect") or {}).get("low"), f"{w} range expect.low")
        _num((rg.get("expect") or {}).get("high"), f"{w} range expect.high", pos=True)
        rel.append(dict(r, _windows=ws, _released=_r(sum(x["_edge"] for x in ws))))
    clo = []
    for r in doc.get("closes") or ():
        w = f"close {r.get('line_id')}"
        _need(r, ("line_id", "expect", "windows"), w)
        _tasks(r, srcs, w)
        once(_lid(r["line_id"], w), w)
        _num((r["expect"] or {}).get("low"), f"{w} expect.low")
        _num((r["expect"] or {}).get("high"), f"{w} expect.high", pos=True)
        ws = [_window(x, f"{w} {x.get('census_id')}", "CLOSE") for x in r["windows"]]
        if not ws or len({x["census_id"] for x in ws}) != len(ws):
            raise InputsError(f"{w}: no window, or a window named twice")
        clo.append(dict(r, _windows=ws, _out=_r(sum(x["_edge"] for x in ws))))
    wal = []
    for r in doc.get("walks") or ():
        w = f"walk {r.get('line_id')}"
        _need(r, ("line_id", "room", "floor", "expect", "evidence_status", "evidence_state", "sides"), w)
        _tasks(r, srcs, w)
        once(_lid(r["line_id"], w), w)
        if r["evidence_state"] not in VALUED_STATES:
            raise InputsError(f"{w}: a walked line is valued {VALUED_STATES}")
        if r["evidence_status"] not in ("VERIFIED", "DRAWING-CONFIRMED"):
            raise InputsError(f"{w}: evidence status {r['evidence_status']!r} is not established")
        m = check_walk(r, w)
        g = _num(r.get("gross_lm"), f"{w} gross_lm", pos=True)
        if abs(g - m["gross"]) > TOL:
            raise InputsError(f"{w}: sides sum {m['gross']} lm, the declared gross is {g} (a side missing or twice)")
        jb = r.get("joinery_backed_lm")
        wal.append(dict(r, _m=m, _joinery=None if jb in (None, "") else _num(jb, f"{w} joinery_backed_lm")))
    if not (rel or clo or wal):
        raise InputsError("no release, range close or walk in the inputs")
    return dict(doc, _sources=srcs, _releases=rel, _closes=clo, _walks=wal)


# ================================================================================================ lines
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
    return ln is not None and ln["item_code"] == CODE and ln["unit"] == UNIT


def _room(ln):
    return (ln.get("location") or {}).get("room_id")


def _sum(items):
    return sum(float(x.get("qty") or 0) for x in items or () if isinstance(x, dict))


def _released(b, r, srcs):
    lid = r["line_id"]
    if not _is_skirting(b):
        raise InputsError(f"release {lid}: not a {CODE} {UNIT} line of the candidate (stale binding)")
    e = r["expect"]
    if b["evidence_state"] not in VALUED_STATES or not isinstance(b.get("gross"), (int, float)) or \
            b.get("measured_net") is None or abs(b["gross"] - e["gross"]) > BIND_TOL or \
            abs(b["measured_net"] - e["measured_net"]) > BIND_TOL:
        raise InputsError(f"release {lid}: {b['evidence_state']} gross {b.get('gross')} net {b.get('measured_net')} "
                          f"is not the ledger's {e} (stale binding)")
    cids = {x["census_id"] for x in r["_windows"]}
    ded = list(b.get("deductions") or [])
    out = [x for x in ded if isinstance(x, dict) and x.get("census_id") in cids]
    keep = [x for x in ded if not (isinstance(x, dict) and x.get("census_id") in cids)]
    for x in r["_windows"]:
        got = [y for y in out if y.get("census_id") == x["census_id"]]
        if not got:
            raise InputsError(f"release {lid}: window {x['census_id']} is not in the line's list (nothing to release)")
        if abs(_sum(got) - x["_edge"]) > TOL:
            raise InputsError(f"release {lid}: window {x['census_id']} listed {_r(_sum(got))} lm, the ledger edge is "
                              f"{x['_edge']} (partial or doubled listing)")
    gone = _r(_sum(out))
    net = _r(b["measured_net"] + gone)
    if net - b["gross"] > TOL:
        raise InputsError(f"release {lid}: net {net} would exceed the gross {b['gross']}")
    new = copy.deepcopy(b)
    new["deductions"] = copy.deepcopy(keep)
    new["measured_net"] = net
    if abs(new["gross"] - _sum(keep) + _sum(new.get("additions")) - net) > TOL:
        raise InputsError(f"release {lid}: gross - list + additions is not the released net {net}")
    wtxt = ", ".join(f"{x['census_id']} {_fmt(x['_edge'])} (sill {_fmt(x['sill_m'])} m {x['status']})"
                     for x in r["_windows"])
    _inputs(new)[REC_KEY] = _rec(P_SILL, srcs, action="RELEASE", windows=[
        {"census_id": x["census_id"], "edge_lm": x["_edge"], "sill_m": x["sill_m"], "status": x["status"],
         "why": x["why"][:300]} for x in r["_windows"]], removed_items=copy.deepcopy(out),
        was={"measured_net": b["measured_net"]}, released_lm=gone, range_line=r["range_line"]["line_id"],
        evidence_status="DRAWING-CONFIRMED")
    new["calculation"]["formula"] = (f"{b['calculation'].get('formula') or ''}; {METHOD}: + {_fmt(gone)} lm window "
                                     f"base(s) under a sill above the floor ({wtxt}) = {_fmt(net)} lm")[:1500]
    A305._note(new, f"{METHOD}: sill release {wtxt}: net {_fmt(b['measured_net'])} -> {_fmt(net)} lm; NOT RELEASED")
    return _fin(new)


def _range_na(rg, r, srcs, outlm, text, action, **kw):
    lid = rg["line_id"] if rg else r.get("line_id")
    if not _is_skirting(rg):
        raise InputsError(f"range line {lid}: not a {CODE} {UNIT} line of the candidate (stale binding)")
    br, e = rg.get("bounded_range") or {}, (r.get("range_line") or r)["expect"]
    if rg["evidence_state"] != RANGE_STATE or rg.get("measured_net") is not None or \
            abs((br.get("low") or 0) - e["low"]) > BIND_TOL or abs((br.get("high") or 0) - e["high"]) > BIND_TOL:
        raise InputsError(f"range line {lid}: {rg['evidence_state']} {br.get('low')} .. {br.get('high')} is not the "
                          f"ledger's held range {e['low']} .. {e['high']} (stale binding)")
    if abs(br["high"] - outlm) > TOL:
        raise InputsError(f"range line {lid}: the windows take {outlm} lm of a held high {br['high']} (a range is "
                          f"closed only whole; a partial close is a narrowing, not this version)")
    new = copy.deepcopy(rg)
    was = {"low": br.get("low"), "high": br.get("high"), "basis": br.get("basis")}
    new["evidence_state"], new["bounded_range"], new["rfi"] = NA_STATE, None, None
    new["calculation"]["formula"] = (f"NOT_APPLICABLE: {text} ({METHOD}); was range {_fmt(was['low'])} .. "
                                     f"{_fmt(was['high'])}")[:1500]
    A305._note(new, f"{METHOD}: NOT_APPLICABLE_WITH_EVIDENCE: {text}"[:400])
    _inputs(new)[REC_KEY] = _rec(P_SILL if action == "ABSORB_RANGE" else P_CLOSE, srcs, action=action, was=was,
                                 evidence_status="DRAWING-CONFIRMED", **kw)
    return _fin(new)


def _walked(b, r, srcs):
    lid = r["line_id"]
    if not _is_skirting(b):
        raise InputsError(f"walk {lid}: not a {CODE} {UNIT} line of the candidate (stale binding)")
    if b["evidence_state"] != r["expect"].get("evidence_state") or b.get("measured_net") is not None or \
            b.get("bounded_range") is not None:
        raise InputsError(f"walk {lid}: {b['evidence_state']} net {b.get('measured_net')} is not the held blank line "
                          f"the ledger walked (stale binding)")
    if _room(b) != r["room"] or (b.get("location") or {}).get("floor") != r["floor"]:
        raise InputsError(f"walk {lid}: line room / floor is not {r['floor']} {r['room']}")
    m = r["_m"]
    new = copy.deepcopy(b)
    new["evidence_state"] = r["evidence_state"]
    new["gross"], new["measured_net"], new["bounded_range"] = m["gross"], m["net"], None
    new["deductions"] = copy.deepcopy(m["deductions"])
    new["additions"] = []
    new["rfi"] = None
    faces = "; ".join(f"{x['side']} {_fmt(x['length_m'])} ({x['handles']})" for x in m["rows"] if x["kind"] in FACE)
    dtxt = " + ".join(f"{d['opening_id']} {_fmt(d['qty'])}" for d in m["deductions"]) or "none"
    jb = "" if r["_joinery"] is None else f"; joinery-backed {_fmt(r['_joinery'])} lm beside, not deducted"
    new["calculation"]["formula"] = (f"{METHOD}: cell walk by handle: gross {_fmt(m['gross'])} lm - {dtxt} = "
                                     f"{_fmt(m['net'])} lm; faces {faces}{jb}")[:1500]
    _inputs(new)[REC_KEY] = _rec(P_WALK, srcs, action="WALK", was={"evidence_state": b["evidence_state"],
                                                                   "rfi": b.get("rfi")},
                                 stretches=m["rows"], gross=m["gross"], deducted=m["deducted"], net=m["net"],
                                 joinery_backed_lm=r["_joinery"], evidence_status=r["evidence_status"])
    _inputs(new)["evidence_status"] = r["evidence_status"]
    A305._note(new, f"{METHOD}: walked {_fmt(m['net'])} lm ({r['evidence_status']}); was {b['evidence_state']} "
                    f"blank; NOT RELEASED")
    return _fin(new)


# ================================================================================================ changes
def changes_for(doc, prev):
    """-> (changes, log). Each change: piece, action (CHANGE), before (a candidate line), after."""
    if not doc:
        return [], {"piece": "+".join((P_SILL, P_CLOSE, P_WALK)), "state": "NO_PROJECT_INPUT"}
    if any(((ln.get("calculation") or {}).get("inputs") or {}).get(REC_KEY) for ln in prev):
        raise InputsError("the candidate already carries V3.0.48 records (applied once)")
    by = {ln["line_id"]: ln for ln in prev}
    S = doc["_sources"]
    changes = []
    log = {"piece": "+".join((P_SILL, P_CLOSE, P_WALK)), "state": "RUN", "sources": doc["sources"], "by_action": {},
           "lines_changed": 0, "released_lm": 0.0, "range_absorbed_lm": 0.0, "range_closed_lm": 0.0,
           "walked_lm": 0.0}

    def add(piece, action, after, before, srcs, **kw):
        if before["line_id"] != after["line_id"]:
            raise ValueError(f"{METHOD}: a changed line keeps its id")
        log["lines_changed"] += 1
        log["by_action"][action] = log["by_action"].get(action, 0) + 1
        changes.append(A305._change(piece, "CHANGE", before, after, step=action,
                                    drawing_reference="; ".join(s["file"] for s in srcs),
                                    verification=A3043._ver(srcs), downstream=kw.pop("downstream", []),
                                    group=after["item_code"], **kw))

    for r in doc["_releases"]:
        srcs = [S[t] for t in r["source_tasks"]]
        b = by.get(r["line_id"])
        det = _released(b, r, srcs)
        add(P_SILL, "RELEASE", det, b, srcs, evidence_status="DRAWING-CONFIRMED", held=[],
            downstream=["skirting roll-up: certain lm up by the released edge(s)"])
        rg = by.get(r["range_line"]["line_id"])
        if rg is not None and (_room(rg) != _room(b) or
                               (rg.get("location") or {}).get("floor") != (b.get("location") or {}).get("floor")):
            raise InputsError(f"release {r['line_id']}: range line {rg['line_id']} is of another room")
        na = _range_na(rg, r, srcs, r["_released"],
                       f"the held window base(s) {', '.join(x['census_id'] for x in r['_windows'])} "
                       f"({_fmt(r['_released'])} lm) are carried by the determinate line {det['line_id']}",
                       "ABSORB_RANGE", carried_by=det["line_id"], released_lm=r["_released"])
        add(P_SILL, "ABSORB_RANGE", na, rg, srcs, evidence_status="DRAWING-CONFIRMED", held=[],
            downstream=["skirting roll-up: held high down by the same edge(s) (carried once)"])
        log["released_lm"] = _r(log["released_lm"] + r["_released"])
        log["range_absorbed_lm"] = _r(log["range_absorbed_lm"] + r["_released"])
    for r in doc["_closes"]:
        srcs = [S[t] for t in r["source_tasks"]]
        rg = by.get(r["line_id"])
        wtxt = ", ".join(f"{x['census_id']} {_fmt(x['_edge'])} ({x['reason']}"
                         f"{': ' + x['owner'] if x['reason'] == 'STAIR_OWNED' else ''})" for x in r["_windows"])
        na = _range_na(rg, r, srcs, r["_out"], f"no room skirting under {wtxt}", "CLOSE_RANGE",
                       windows=[{"census_id": x["census_id"], "edge_lm": x["_edge"], "sill_m": x.get("sill_m"),
                                 "reason": x["reason"], "owner": x.get("owner"), "status": x["status"],
                                 "why": x["why"][:300]} for x in r["_windows"]], closed_lm=r["_out"])
        add(P_CLOSE, "CLOSE_RANGE", na, rg, srcs, evidence_status="DRAWING-CONFIRMED", held=[],
            downstream=["skirting roll-up: held high down; no certain value moves"])
        log["range_closed_lm"] = _r(log["range_closed_lm"] + r["_out"])
    for r in doc["_walks"]:
        srcs = [S[t] for t in r["source_tasks"]]
        b = by.get(r["line_id"])
        new = _walked(b, r, srcs)
        add(P_WALK, "WALK", new, b, srcs, evidence_status=r["evidence_status"], held=[],
            downstream=[f"skirting roll-up: certain lm +{_fmt(r['_m']['net'])} (was a HELD BLANK line)"])
        log["walked_lm"] = _r(log["walked_lm"] + r["_m"]["net"])
    log["by_action"] = dict(sorted(log["by_action"].items()))
    return changes, log


# ================================================================================================ checks
def check_remainder(lines, before=None):
    """R-T483-1 on the integrated lines: a released line is valued, closes, lists no released window and rose by
    exactly its released edges; an absorbed / closed range line is NOT_APPLICABLE with no figure (an absorbed one names
    a candidate line); a walked line is valued and closes gross - deductions = net with every deduction by id and no
    jamb skirting. -> summary."""
    out = {"released_lines": 0, "released_lm": 0.0, "absorbed": 0, "closed": 0, "closed_lm": 0.0, "walked": 0,
           "walked_lm": 0.0}
    ids = {ln["line_id"]: ln for ln in lines}
    b4 = {ln["line_id"]: ln for ln in before or ()}
    for ln in lines:
        rec = ((ln.get("calculation") or {}).get("inputs") or {}).get(REC_KEY)
        if not rec:
            continue
        if not _is_skirting(ln):
            raise ValueError(f"{METHOD}: a V3.0.48 record on {ln['item_code']} {ln['line_id']}")
        act = rec.get("action")
        if act in ("RELEASE", "WALK"):
            if ln["evidence_state"] not in VALUED_STATES or ln.get("measured_net") is None:
                raise ValueError(f"{METHOD}: {act.lower()} line {ln['line_id']} is not valued")
            if abs(ln["gross"] - _sum(ln.get("deductions")) + _sum(ln.get("additions")) - ln["measured_net"]) > TOL:
                raise ValueError(f"{METHOD}: {act.lower()} line {ln['line_id']} does not close")
            if act == "RELEASE":
                cids = {w["census_id"] for w in rec["windows"]}
                if any(isinstance(x, dict) and x.get("census_id") in cids for x in ln.get("deductions") or ()):
                    raise ValueError(f"{METHOD}: released line {ln['line_id']} still lists a released window")
                o = b4.get(ln["line_id"])
                if o is not None and abs(ln["measured_net"] - o["measured_net"] - rec["released_lm"]) > TOL:
                    raise ValueError(f"{METHOD}: released line {ln['line_id']} moved by other than its released edges")
                out["released_lines"] += 1
                out["released_lm"] = _r(out["released_lm"] + rec["released_lm"])
            else:
                for x in ln.get("deductions") or ():
                    if not x.get("opening_id") or x.get("jamb_skirting") is not False:
                        raise ValueError(f"{METHOD}: walked line {ln['line_id']}: a deduction without an id or with "
                                         f"jamb skirting")
                out["walked"] += 1
                out["walked_lm"] = _r(out["walked_lm"] + ln["measured_net"])
        elif act in ("ABSORB_RANGE", "CLOSE_RANGE"):
            if ln["evidence_state"] != NA_STATE or ln.get("measured_net") is not None or ln.get("bounded_range") or \
                    ln.get("gross") is not None:
                raise ValueError(f"{METHOD}: {act.lower()} line {ln['line_id']} carries a figure")
            if act == "ABSORB_RANGE":
                if rec.get("carried_by") not in ids:
                    raise ValueError(f"{METHOD}: absorbed range line {ln['line_id']} names no candidate line")
                out["absorbed"] += 1
            else:
                out["closed"] += 1
                out["closed_lm"] = _r(out["closed_lm"] + rec["closed_lm"])
        else:
            raise ValueError(f"{METHOD}: action {act} on {ln['line_id']}")
    return out


# ================================================================================================ integrate / write
def integrate(prev, changes, for_lead=()):
    """-> (V3.0.48 lines, identity). Changed lines replace their candidate line in place; every other candidate line is
    byte-identical (asserted)."""
    sid = {ln["line_id"]: i for i, ln in enumerate(prev)}
    out = list(prev)
    repl = set()
    for c in changes:
        a = c["after"]
        if a["item_code"] != CODE:
            raise ValueError(f"{METHOD}: {a['item_code']} is not the code this version may change")
        if c["action"] != "CHANGE":
            raise ValueError(f"{METHOD}: action {c['action']} (this version adds no line)")
        i = sid.get(a["line_id"])
        if i is None or a["line_id"] in repl:
            raise ValueError(f"{METHOD}: a changed line is not a candidate line or changes twice")
        out[i] = a
        repl.add(a["line_id"])
    if len({ln["line_id"] for ln in out}) != len(out):
        raise ValueError(f"{METHOD}: a BOQ line id appears twice")
    guards = A3031._family_guards(out, for_lead)
    ident = {"base_lines": len(prev), "v3_0_48_lines": len(out), "v3_0_48_rows": len(changes),
             "replaced": len(repl), "added": 0, "guards": guards,
             "roof_buildup": A3031.check_roof_layers(out), "ceilings": A3032.check_ceilings(out),
             "corrections": A3033.check_corrections(out), "tile_zones": A3034.check_zones(out),
             "fence": A3035.check_boundary(out), "lists": A3036.check_lists(out), "beds": A3038.check_beds(out),
             "lift": A3038.check_lift(out), "landing": A3038.check_landing(out), "flights": A3039.check_flights(out),
             "gb_runs": A3040.check_runs(out), "pieces": A3041.check_pieces(out), "slab": A3042.check_slab(out),
             "earthworks": A3043.check_earthworks(out), "skirting": A3044.check_skirting(out),
             "blinding": A3045.check_blinding(out), "tie_masonry": A3046.check_tie_masonry(out),
             "stair_rooms": A3047.check_stair_rooms(out), "remainder": check_remainder(out, prev)}
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
        rec = ref["calculation"]["inputs"].get(REC_KEY) or {}
        b29 = None
        if released_lines is not None:
            b29 = A30._qty(rel[A30._key(ref)]) if A30._key(ref) in rel else dict(A30._qty(None),
                                                                                 state="NOT_IN_RELEASED")
        loc = ref.get("location") or {}
        rows.append({"version": METHOD, "piece": c["piece"], "action": c.get("step"), "change": c["action"],
                     "line_id": ref["line_id"], "item_code": ref["item_code"], "floor": loc.get("floor"),
                     "room_id": loc.get("room_id"), "element_id": loc.get("element_id"), "unit": ref["unit"],
                     "before_released_v2_9": b29, "before_base": A30._qty(c.get("before")),
                     "after_v3_0_48": A30._qty(ref), "evidence_status": c.get("evidence_status"),
                     "still_held": c.get("held"), "release_status": "NOT RELEASED",
                     "owner_manual_method": PIECES[c["piece"]]["owner_manual_method"],
                     "drawing_derived_method": PIECES[c["piece"]]["drawing_method"],
                     "record": rec, "verification": c.get("verification") or {}, "rollback": ROLLBACK})
    return rows


LEDGER_CSV = ("version", "piece", "action", "change", "line_id", "item_code", "floor", "room_id", "element_id", "unit",
              "v2_9", "base", "v3_0_48", "evidence_status", "still_held", "verification")
DIFF_CSV = ("line_id", "item_code", "floor", "element_id", "unit", "vs_base", "vs_released_v2_9", "v2_9", "base",
            "v3_0_48")


def ledger_csv(rows):
    def q(x):
        return A302._q(x) if x and (x.get("value") is not None or x.get("low") is not None or x.get("state")) else ""
    return A305._csv([{"version": r["version"], "piece": r["piece"], "action": r["action"], "change": r["change"],
                       "line_id": r["line_id"], "item_code": r["item_code"], "floor": r.get("floor") or "",
                       "room_id": r.get("room_id") or "", "element_id": r.get("element_id") or "", "unit": r["unit"],
                       "v2_9": q(r.get("before_released_v2_9")), "base": q(r.get("before_base")),
                       "v3_0_48": q(r.get("after_v3_0_48")), "evidence_status": r["evidence_status"],
                       "still_held": "",
                       "verification": f"{r['verification'].get('task')} "
                                       f"{' '.join(x[:8] for x in r['verification'].get('merge_commits') or ())}"}
                      for r in rows], LEDGER_CSV)


def diff_rows(prev, new, released_lines=None):
    b = {ln["line_id"]: ln for ln in prev}
    rel = {A30._key(ln): ln for ln in released_lines or ()}
    out = []
    for ln in new:
        o = b.get(ln["line_id"])
        vs = "ADDED" if o is None else ("SAME" if A30.line_sha(o) == A30.line_sha(ln) else "CHANGED")
        r = rel.get(A30._key(ln)) if released_lines is not None else None
        vs29 = None if released_lines is None else ("NOT_IN_RELEASED" if r is None else
                                                    ("SAME_QUANTITY" if A30._qty(r) == A30._qty(ln) else
                                                     "QUANTITY_DIFFERS"))
        out.append({"line_id": ln["line_id"], "item_code": ln["item_code"], "floor": ln["location"].get("floor"),
                    "element_id": ln["location"].get("element_id"), "unit": ln["unit"], "vs_base": vs,
                    "vs_released_v2_9": vs29, "v2_9": A302._q(A30._qty(r)) if r else "",
                    "base": A302._q(A30._qty(o)) if o else "", "v3_0_48": A302._q(A30._qty(ln))})
    return out


def write(out, prev, changes, log, released_lines=None, for_lead=()):
    """the V3_0_48_* files beside the base candidate's files. -> (file names, identity, ledger)."""
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
    t0, t1 = A304.code_totals(prev), A304.code_totals(new)
    moved = {k: {"base": t0.get(k), "v3_0_48": t1.get(k)} for k in sorted(set(t0) | set(t1)) if t0.get(k) != t1.get(k)}
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
    files = {"V3_0_48_BOQ_LINES.json": BL.dumps(new),
             "V3_0_48_BOQ_LINES.csv": A30._lines_csv(new),
             "V3_0_48_INTEGRATION_LEDGER.json": A30._j(led),
             "V3_0_48_INTEGRATION_LEDGER.csv": ledger_csv(rows),
             "V3_0_48_DIFF.csv": A305._csv(diff, DIFF_CSV),
             "V3_0_48_RUN.json": A30._j(run)}
    for name, text in files.items():
        (out / name).write_text(text, encoding="utf-8")
    return sorted(files), ident, led


def policy_record():
    return {"method": METHOD, "extends": EXTENDS, "pieces": sorted(PIECES), "inputs_schema": INPUTS_SCHEMA,
            "released_default": False, "rollback": ROLLBACK, "actions": list(ACTIONS)}


__all__ = ["METHOD", "PIECES", "WAITING", "DEFAULT_GUARD_CLASS", "INPUTS_SCHEMA", "load_inputs", "changes_for",
           "check_walk", "check_remainder", "integrate", "ledger_rows", "diff_rows", "write", "InputsError"]
