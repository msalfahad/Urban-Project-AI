"""ARCH_TAKEOFF_V3.0.40 (T-430): the SAME opt-in BOQ candidate as ARCH_TAKEOFF_V3.0 .. V3.0.39 (engine.source.arch_v30,
arch_v301 .. arch_v3039), extended with ONE Checker-verified piece: the GROUND-BEAM SECTION AND NECK corrections
(T-426 MERGED 1f298735: the printed section is read per RUN between founded supports; T-416 MERGED b7bb914a with the
Checker's F-C-T416-1: a founded neck cut by a band owns the joint, cuts exact).

  GB_RUN_SECTION  a candidate ground-beam line that bills a band crossed by a FOUNDED neck is split at the neck into its
                  runs (R-T426-1). Per run:
                    VALUED  a run on which nothing lands (no D-33 load), whose clear span is the same on every frame and
                            whose printed section is ONE title: b x D(printed) x L(run); evidence VERIFIED (T-242 / T-426
                            Checker re-measure); the line keeps its id (the first valued run);
                    HELD    a run on which another beam lands (D-33: the printed title says 'without concentrated load'),
                            or whose span differs between frames with a title change: BLOCKED_RFI blank, the printed
                            unloaded figure and the candidate's own figure beside as a range, never valued, never 0; an
                            ADDED line '<element>:<run>' of the same code.
                  The neck length inside the band is not billed by either run: the joint is the neck's (R-CONC-OWN-1, T-416
                  ENGINE_WRONG 0.054 m3 per band at the candidate depth, exact cut).
  GB_HOLD         a valued ground-beam line whose value is one picked end of a printed RANGE (two titles hold on its
                  span, or the span itself differs by reading) or that has NO printed section: BLOCKED_RFI blank with the
                  range beside (RANGE) or with nothing beside (BLANK); never valued, never 0.

R-T430-1 (every villa; integrates R-T426-1 .. 5, R-T416-1 .. 5 and F-C-T416-1): (a) a ground-beam section is read per
run, never from the band or the neighbour; (b) the runs and the necks of a split band add up to the candidate band length
exactly (no length lost, none borrowed); (c) a run is valued only on one printed title, one span on every frame and no
load on it; (d) a picked end of a printed range is HELD, not a value; (e) held is blank with its figure(s) beside, never 0.

Downgrade-only records (owner 2026-10-24 23:57) are the Checker's: this version neither writes nor reads one; the T-430
proposal to extend DG-a31a0d7e to the 4 short runs lives in research/agents_t430 for Checker validation.

Nothing else moves: every V3.0.39 line not named by the inputs is byte-identical (asserted); totals move only in the
ground-beam code (asserted). Files: V3_0_40_BOQ_LINES.json / .csv, V3_0_40_INTEGRATION_LEDGER.json / .csv,
V3_0_40_DIFF.csv, V3_0_40_RUN.json. Nothing here names a project, a sheet, a layer or a coordinate.
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
from engine.source import arch_v3039 as A3039

DEFAULT_GUARD_CLASS = "TOOLING"          # T-212: re-books checker-merged ledgers; adds no default value
METHOD = "ARCH_TAKEOFF_V3.0.40"
EXTENDS = A3039.METHOD
CANDIDATE = A30.METHOD
POLICY_ID = "URBAN_BOQ_T430_ARCH_V3_0_40"
INPUTS_SCHEMA = "URBAN_V3040_INPUTS_V1"
LEDGER_SCHEMA = "URBAN_V3040_INTEGRATION_LEDGER_V1"
ROLLBACK = A30.ROLLBACK
InputsError = A3031.InputsError
_r = A3018._r
_fmt = A3030._fmt
RULE_ID, RULE_VERSION = "R-T430-1", "T-430"
REC_KEY = "gb_run_section_v3040"
P_SPLIT, P_HOLD = "GB_RUN_SECTION", "GB_HOLD"
GB = "STR.CONC.GROUND_BEAM"
OWN_CODES = (GB,)
VALUED = ("MEASURED", "SOURCE_DERIVED", "PROVISIONAL")
TOL_L = 0.0006                           # m: the merged reads print 3 .. 4 decimals of a metre
TOL_V = 0.0000015                        # m3: the candidate prints 6 decimals
HOLD_KINDS = ("RANGE", "BLANK")

PIECES = {
    P_SPLIT: {"module": "engine/source/arch_v3040.py (a band crossed by a founded neck is split into its runs; each run "
                        "carries its own printed section; a loaded run is HELD with its range beside; the neck owns the "
                        "joint)",
              "policy": "GB_RUN_SECTION_V1", "rule_id": "R-T426-1..5 + R-T416-1..5 + F-C-T416-1 (R-T430-1)",
              "owner_rules": ["Q-61 C (member by member, face to face)", "UP-QTY-STATUS-001 (held is blank, never 0)",
                              "register ruling GF LIFT TIE BEAM (a section is never borrowed)",
                              "R-CONC-OWN-1 (the neck owns the joint)", "D-33 (a beam landing on a run: consultant)"],
              "owner_manual_method": "owner method: ground beam = b x D x L between the faces of its supports, member by "
                                     "member (Q-61 C), D the printed section for that member",
              "drawing_method": "runs between founded necks / columns / rings read per frame (T-416 band read, exact "
                                "cuts); the printed title per run from its own clear span (ST p.13, T-426)"},
    P_HOLD: {"module": "engine/source/arch_v3040.py (a picked end of a printed range or a line with no printed section: "
                       "HELD blank with the range beside)",
             "policy": "GB_HOLD_V1", "rule_id": "R-T426-4 (R-T430-1 d, e)",
             "owner_rules": ["UP-QTY-STATUS-001", "no-assumptions rule (2026-10-19)", "D-33 / D-34 (consultant items)",
                             "D-35 (annex exterior depth: source conflict)"],
             "owner_manual_method": "owner method: the printed section; where two titles hold, no rule picks one",
             "drawing_method": "T-426 census: spans per frame and per reading against the ST p.13 titles"},
}
WAITING = dict(A3039.WAITING)
WAITING.update({
    "T430_D33_LOADED_RUNS": "two loaded ground-beam runs (a beam lands on them; D-33, consultant): HELD with the printed "
                            "unloaded figure and the candidate's own depth beside (T-426 s.4.1)",
    "T430_D34_SHORT_RUNS": "four runs under 2.5 m valued at the 0.40 end of the unanswered D-34 pair: a downgrade-only "
                           "extension of DG-a31a0d7e is PROPOSED for the Checker (research/agents_t430), the candidate "
                           "line is not changed here (F-T426-1)",
    "T430_ROUTE_G_NECK": "route G does not read a founded neck cut by a band as a support for the CLASS (the 'clear 7.35 m' "
                         "note, T-426 s.6 (4)): the defect is fixed in the candidate lines here, not in route G",
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


def _metres(x, where, hi):
    v = _num(x, where, True)
    if v > hi:
        raise InputsError(f"{where}: {v} is not metres (mm refused)")
    return v


def _pair(x, where, hi):
    if not isinstance(x, (list, tuple)) or len(x) != 2:
        raise InputsError(f"{where}: [low, high]")
    lo, h = _metres(x[0], where, hi), _metres(x[1], where, hi)
    if lo > h + 1e-12:
        raise InputsError(f"{where}: low {lo} > high {h}")
    return lo, h


def load_inputs(doc, project_id=None):
    """URBAN_V3040_INPUTS_V1 -> the validated doc.
    {"schema", "project_id", "sources": [{"task", "file", "sha256", "merge_commit", "checker_run"}],
     "splits": [{"line_id", "band", "b", "candidate": {"D", "L", "value"}, "necks": [{"id", "length", "founded"}],
                 "runs": [{"run", "spans": [low, high] (m, over the frames), "printed_D": [d] | [d1, d2], "loaded",
                           "held_D": [low, high] | None, "cause"}], "evidence_status", "source_tasks"}],
     "holds": [{"line_id", "kind": "RANGE" | "BLANK", "candidate": {"D", "L", "value"},
                "range": {"low", "high", "low_basis", "high_basis"} | None, "cause", "items", "source_tasks"}]}"""
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

    ids = set()

    def once(lid, where):
        if not lid:
            raise InputsError(f"{where}: line_id missing")
        if lid in ids:
            raise InputsError(f"{where}: named twice (one line, one action)")
        ids.add(lid)

    def cand(c, where):
        _need(c or {}, ("D", "L", "value"), f"{where} candidate")
        return {"D": _metres(c["D"], f"{where} candidate D", 3.0), "L": _metres(c["L"], f"{where} candidate L", 60.0),
                "value": _num(c["value"], f"{where} candidate value", True)}

    splits = []
    for s in doc.get("splits") or ():
        where = f"split {s.get('line_id')}"
        _need(s, ("line_id", "band", "evidence_status"), where)
        tasks(s, where)
        once(s["line_id"], where)
        b = _metres(s.get("b"), f"{where} b", 2.0)
        c = cand(s.get("candidate"), where)
        necks = []
        for n in s.get("necks") or ():
            _need(n, ("id",), f"{where} neck")
            if n.get("founded") is not True:
                raise InputsError(f"{where}: neck {n['id']} is not a FOUNDED neck (only a founded support splits a "
                                  f"band, R-T426-1)")
            necks.append(dict(n, _len=_metres(n.get("length"), f"{where} neck {n['id']} length", 2.0)))
        if not necks:
            raise InputsError(f"{where}: a split names the founded neck(s) that cross the band")
        runs = []
        for r in s.get("runs") or ():
            rw = f"{where} run {r.get('run')}"
            _need(r, ("run",), rw)
            lo, hi = _pair(r.get("spans"), f"{rw} spans", 30.0)
            pd = r.get("printed_D")
            if not isinstance(pd, (list, tuple)) or len(pd) not in (1, 2):
                raise InputsError(f"{rw}: printed_D is one printed depth or a printed pair")
            pd = [_metres(x, f"{rw} printed_D", 3.0) for x in pd]
            if not isinstance(r.get("loaded"), bool):
                raise InputsError(f"{rw}: loaded (a beam lands on the run: D-33) is true or false")
            hd = r.get("held_D")
            if hd is not None:
                hd = _pair(hd, f"{rw} held_D", 3.0)
            runs.append(dict(r, _lo=lo, _hi=hi, _pd=pd, _hd=hd))
        if len(runs) != len(necks) + 1:
            raise InputsError(f"{where}: {len(necks)} neck(s) split a band into {len(necks) + 1} runs, "
                              f"{len(runs)} given (a founded neck ignored: one span through it)")
        if len({r["run"] for r in runs}) != len(runs):
            raise InputsError(f"{where}: a run named twice")
        total = sum(r["_lo"] for r in runs) + sum(n["_len"] for n in necks)
        if abs(total - c["L"]) > TOL_L * (len(runs) + len(necks)):
            raise InputsError(f"{where}: runs {_fmt(sum(r['_lo'] for r in runs))} + necks "
                              f"{_fmt(sum(n['_len'] for n in necks))} = {_fmt(total)} m is not the candidate band "
                              f"{_fmt(c['L'])} m (R-T430-1 b: no length lost, none borrowed)")
        if abs(b * c["D"] * c["L"] - c["value"]) > 0.0005:
            raise InputsError(f"{where}: candidate {c['value']} is not b x D x L {b} x {c['D']} x {c['L']} (stale)")
        for r in runs:
            r["_valued"] = (not r["loaded"]) and len(r["_pd"]) == 1 and abs(r["_hi"] - r["_lo"]) <= TOL_L
            if not r["_valued"] and r["_hd"] is None:
                raise InputsError(f"{where} run {r['run']}: a HELD run carries its depth range beside (never 0)")
            if r["_hd"] is not None and r["_valued"]:
                raise InputsError(f"{where} run {r['run']}: a valued run carries no held range")
        if not any(r["_valued"] for r in runs) and s["evidence_status"] != "HELD":
            raise InputsError(f"{where}: no run is valued: evidence_status HELD")
        if any(r["_valued"] for r in runs) and s["evidence_status"] not in ("VERIFIED", "DRAWING-CONFIRMED"):
            raise InputsError(f"{where}: a valued run is VERIFIED or DRAWING-CONFIRMED ({s['evidence_status']!r})")
        splits.append(dict(s, _b=b, _c=c, _necks=necks, _runs=runs))
    holds = []
    for h in doc.get("holds") or ():
        where = f"hold {h.get('line_id')}"
        _need(h, ("line_id", "kind", "cause"), where)
        tasks(h, where)
        once(h["line_id"], where)
        if h["kind"] not in HOLD_KINDS:
            raise InputsError(f"{where}: kind {h['kind']} ({' / '.join(HOLD_KINDS)})")
        c = cand(h.get("candidate"), where)
        rg = h.get("range")
        if h["kind"] == "RANGE":
            _need(rg or {}, ("low", "high", "low_basis", "high_basis"), f"{where} range")
            lo, hi = _num(rg["low"], f"{where} range low", True), _num(rg["high"], f"{where} range high", True)
            if lo > hi:
                raise InputsError(f"{where}: range low {lo} > high {hi}")
            if not (lo - TOL_V <= c["value"] <= hi + TOL_V):
                raise InputsError(f"{where}: the candidate value {c['value']} is not inside its printed range "
                                  f"{lo} .. {hi} (not a picked end)")
            rg = dict(rg, _lo=lo, _hi=hi)
        elif rg is not None:
            raise InputsError(f"{where}: a BLANK hold carries no range (no printed section)")
        holds.append(dict(h, _c=c, _range=rg))
    if not splits and not holds:
        raise InputsError("no split and no hold in the inputs")
    return dict(doc, _sources=srcs, _splits=splits, _holds=holds)


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


def _base(ln):
    new = copy.deepcopy(ln)
    new["calculation"] = copy.deepcopy(new["calculation"])
    new["calculation"]["inputs"] = dict(new["calculation"]["inputs"] or {})
    return new


def _check_line(ln, c, where):
    if ln is None:
        raise InputsError(f"{where}: not in the candidate (stale binding)")
    if ln["item_code"] != GB or ln["unit"] != "m3":
        raise InputsError(f"{where}: {ln['item_code']} {ln['unit']} is not a ground-beam m3 line")
    net = ln.get("measured_net")
    if ln["evidence_state"] not in VALUED or net is None or abs(net - c["value"]) > TOL_V:
        raise InputsError(f"{where}: candidate {ln['evidence_state']} {net} is not the merged census value "
                          f"{c['value']} (stale binding)")


def _held_figs(s, r):
    lo_d, hi_d = r["_hd"]
    return _r(s["_b"] * lo_d * r["_lo"]), _r(s["_b"] * hi_d * r["_hi"])


def _run_valued(ln, s, r, srcs, first):
    new = _base(ln)
    before = ln["measured_net"]
    d = r["_pd"][0]
    v = _r(s["_b"] * d * r["_lo"])
    new["measured_net"] = v
    if new.get("gross") is not None:
        new["gross"] = v
    new["evidence_state"] = "SOURCE_DERIVED"
    necks = "; ".join(f"{n['id']} {_fmt(n['_len'])} m" for n in s["_necks"])
    new["calculation"]["formula"] = (
        f"{new['calculation']['formula']} | {METHOD}: band {s['band']} is crossed by founded neck(s) {necks}: split into "
        f"runs (R-T426-1); this line carries run {r['run']} (nothing lands on it): {_fmt(s['_b'])} x {_fmt(d)} (printed "
        f"title for its own clear span) x {_fmt(r['_lo'])} m = {_fmt(v)} m3 (was {_fmt(before)}: {_fmt(s['_c']['D'])} "
        f"read on the band's {_fmt(s['_c']['L'])} m through the neck); the neck owns the joint (R-CONC-OWN-1)")
    new["calculation"]["inputs"][REC_KEY] = _rec(
        P_SPLIT, srcs, action="SPLIT_VALUED", band=s["band"], run=r["run"], b=s["_b"], D=d, L=r["_lo"],
        spans=[r["_lo"], r["_hi"]], before=before, after=v, candidate=s["_c"],
        necks=[{"id": n["id"], "length": n["_len"]} for n in s["_necks"]],
        sibling_runs=[x["run"] for x in s["_runs"] if x is not r], evidence_status=s["evidence_status"],
        cause=r.get("cause"))
    new["calculation"]["inputs"]["evidence_status"] = s["evidence_status"]
    new["notes"] = (f"{new.get('notes') or ''} | {METHOD}: run {r['run']} of band {s['band']} (split at the founded "
                    f"neck); section per run, never from the band (R-T426-1); NOT RELEASED")
    return _fin(new), v


def _run_held(ln, s, r, srcs, keep_id):
    """keep_id True: the line itself becomes the held run (no run valued); else an ADDED line '<element>:<run>'."""
    from engine.source import boq_line as BL
    lo, hi = _held_figs(s, r)
    cause = r.get("cause") or "a beam lands on the run (D-33)"
    q = (f"D-33: run {r['run']} of ground beam {s['band']}: {cause}; ST p.13 titles say 'without concentrated load': "
         f"section not printed for a loaded run (consultant)")[:600]
    formula = (f"{METHOD}: run {r['run']} of band {s['band']} (split at founded neck(s) "
               f"{', '.join(n['id'] for n in s['_necks'])}): HELD: {cause}; blank, never 0; beside {_fmt(lo)} .. "
               f"{_fmt(hi)} m3 = {_fmt(s['_b'])} x {_fmt(r['_hd'][0])} .. {_fmt(r['_hd'][1])} x {_fmt(r['_lo'])} .. "
               f"{_fmt(r['_hi'])} m (printed unloaded title .. the candidate's own depth; frames)")
    rec = _rec(P_SPLIT, srcs, action="SPLIT_HELD", band=s["band"], run=r["run"], b=s["_b"], held_D=list(r["_hd"]),
               spans=[r["_lo"], r["_hi"]], beside=[lo, hi], candidate=s["_c"], from_line=ln["line_id"],
               necks=[{"id": n["id"], "length": n["_len"]} for n in s["_necks"]], evidence_status="HELD", cause=cause)
    if keep_id:
        new = _base(ln)
        new["evidence_state"] = "BLOCKED_RFI"
        new["measured_net"] = None
        new["bounded_range"] = None
        new["gross"] = None
        new["rfi"] = {"question": q, "unlocks": ln["line_id"]}
        new["calculation"]["formula"] = (f"{new['calculation']['formula']} | {formula}")[:1500]
        new["calculation"]["inputs"][REC_KEY] = rec
        new["calculation"]["inputs"]["evidence_status"] = "HELD"
        new["notes"] = f"{new.get('notes') or ''} | {METHOD}: HELD run (D-33), range beside, never 0"
        return _fin(new)
    loc = ln["location"]
    eid = f"{loc['element_id']}:{r['run']}"
    new = BL.make_line(
        project_id=ln["project"]["project_id"], revision_set_sha256=ln["project"]["revision_set_sha256"],
        item_code=GB, unit="m3", evidence_state="BLOCKED_RFI", measured_net=None, element_id=eid,
        floor=loc.get("floor"), room_id=loc.get("room_id"), room_name_en=loc.get("room_name_en"),
        room_name_ar=loc.get("room_name_ar"),
        physical_element=f"ground beam run {r['run']} of band {s['band']} between its founded supports",
        formula=formula, inputs={REC_KEY: rec, "evidence_status": "HELD"},
        documents=copy.deepcopy(ln["source"]["documents"]), geometry_source=ln["source"]["geometry_source"],
        geometry_confidence=ln["source"]["geometry_confidence"], rule_id=RULE_ID, rule_version=RULE_VERSION,
        material_state=ln.get("material_state") or "BY_SPEC", rfi={"question": q, "unlocks": eid},
        notes=(f"{METHOD}: HELD run of band {s['band']} split from {ln['line_id']} at the founded neck (R-T426-1); "
               f"range beside, never 0; NOT RELEASED"),
        item_en=ln["item_en"], item_ar=ln["item_ar"], trade=ln["trade"], subtrade=ln.get("subtrade"))
    return _fin(new)


def _hold(ln, h, srcs):
    new = _base(ln)
    was = A302._q(A30._qty(ln))
    rg = h["_range"]
    new["evidence_state"] = "BLOCKED_RFI"
    new["measured_net"] = None
    new["bounded_range"] = None
    new["gross"] = None
    items = ", ".join(h.get("items") or ())
    q = (f"{items + ': ' if items else ''}{h['cause']}")[:600]
    new["rfi"] = {"question": q, "unlocks": ln["line_id"]}
    bs = (f"beside {_fmt(rg['_lo'])} ({rg['low_basis']}) .. {_fmt(rg['_hi'])} ({rg['high_basis']}) m3" if rg else
          "nothing beside (no printed section)")
    new["calculation"]["formula"] = (f"{new['calculation']['formula']} | {METHOD}: HELD ({h['kind']}): {h['cause']}; "
                                     f"blank, never 0; {bs}")[:1500]
    new["calculation"]["inputs"][REC_KEY] = _rec(
        P_HOLD, srcs, action=f"HOLD_{h['kind']}", was=was, candidate=h["_c"],
        beside=([rg["_lo"], rg["_hi"]] if rg else None), range_basis=([rg["low_basis"], rg["high_basis"]] if rg else None),
        items=list(h.get("items") or ()), evidence_status="HELD", cause=h["cause"])
    new["calculation"]["inputs"]["evidence_status"] = "HELD"
    why = "picked end of a printed range" if rg else "no printed section"
    new["notes"] = f"{new.get('notes') or ''} | {METHOD}: HELD ({why}), never valued, never 0 (R-T426-4)"
    return _fin(new)


# ================================================================================================ changes
def changes_for(doc, l3039):
    """-> (changes, log). Each change: piece, action (CHANGE / ADD), before (a V3.0.39 line or None), after."""
    if not doc:
        return [], {"piece": f"{P_SPLIT}+{P_HOLD}", "state": "NO_PROJECT_INPUT"}
    if any(((ln.get("calculation") or {}).get("inputs") or {}).get(REC_KEY) for ln in l3039):
        raise InputsError("the candidate already carries V3.0.40 records (applied once)")
    by = {ln["line_id"]: ln for ln in l3039}
    S = doc["_sources"]
    seen = set(by)
    changes = []
    log = {"piece": f"{P_SPLIT}+{P_HOLD}", "state": "RUN", "sources": doc["sources"], "by_action": {},
           "lines_changed": 0, "lines_added": 0}

    def put(piece, step, before, after, srcs, ev, held, **kw):
        if before is None:
            if after["line_id"] in seen:
                raise ValueError(f"{METHOD}: added line {after['location']['element_id']} repeats an id")
            seen.add(after["line_id"])
            log["lines_added"] += 1
        else:
            if before["line_id"] != after["line_id"]:
                raise ValueError(f"{METHOD}: a changed line keeps its id")
            log["lines_changed"] += 1
        log["by_action"][step] = log["by_action"].get(step, 0) + 1
        changes.append(A305._change(piece, "ADD" if before is None else "CHANGE", before, after, step=step,
                                    drawing_reference="; ".join(s["file"] for s in srcs), verification=_ver(srcs),
                                    downstream=kw.pop("downstream", []), group=GB, evidence_status=ev, held=held,
                                    **kw))

    for s in doc["_splits"]:
        srcs = [S[t] for t in s["source_tasks"]]
        where = f"split {s['line_id']}"
        ln = by.get(s["line_id"])
        _check_line(ln, s["_c"], where)
        first = next((r for r in s["_runs"] if r["_valued"]), None)
        down = ["formwork / blinding / waterproofing of this beam follow the run split (none read the line today)"]
        for r in s["_runs"]:
            if r is first:
                new, v = _run_valued(ln, s, r, srcs, True)
                put(P_SPLIT, "SPLIT_VALUED", ln, new, srcs, s["evidence_status"], [], run=r["run"], downstream=down)
            elif r["_valued"]:
                raise InputsError(f"{where}: two unloaded runs valued on one band: carry them as two lines in a later "
                                  f"package (this version values one run per split line)")
            else:
                keep = first is None and r is s["_runs"][0]
                new = _run_held(ln, s, r, srcs, keep)
                lo, hi = _held_figs(s, r)
                held = [{"what": f"{GB} run {r['run']}", "why": (r.get("cause") or "D-33")[:300], "range": [lo, hi],
                         "scenario": "HELD by name, the range beside, never 0"}]
                put(P_SPLIT, "SPLIT_HELD", ln if keep else None, new, srcs, "HELD", held, run=r["run"],
                    downstream=down)
    for h in doc["_holds"]:
        srcs = [S[t] for t in h["source_tasks"]]
        ln = by.get(h["line_id"])
        _check_line(ln, h["_c"], f"hold {h['line_id']}")
        rg = h["_range"]
        held = [{"what": f"{GB} {ln['location']['element_id']}", "why": h["cause"][:300],
                 "range": [rg["_lo"], rg["_hi"]] if rg else None, "scenario": "HELD by name, never 0"}]
        put(P_HOLD, f"HOLD_{h['kind']}", ln, _hold(ln, h, srcs), srcs, "HELD", held)
    log["by_action"] = dict(sorted(log["by_action"].items()))
    return changes, log


# ================================================================================================ checks
def check_runs(lines):
    """R-T430-1 on the integrated lines: every V3.0.40 record is consistent (a valued run equals b x printed D x run
    length; a held run / held line is blank with its reason; a split line's runs + necks equal the candidate band; per
    band at most the runs the record names, each once). -> summary."""
    out = {"valued_runs": 0, "held_runs": 0, "held_lines": 0, "valued_m3": 0.0, "held_beside_m3": [0.0, 0.0],
           "bands": {}}
    for ln in lines:
        rec = ((ln.get("calculation") or {}).get("inputs") or {}).get(REC_KEY)
        if not rec:
            continue
        a = rec["action"]
        if ln["item_code"] != GB:
            raise ValueError(f"{METHOD}: a V3.0.40 record on {ln['item_code']}")
        if a == "SPLIT_VALUED":
            if ln["evidence_state"] not in VALUED or abs(ln["measured_net"] - _r(rec["b"] * rec["D"] * rec["L"])) > TOL_V:
                raise ValueError(f"{METHOD}: valued run {ln['line_id']} is not b x D x L")
            if abs(rec["spans"][1] - rec["spans"][0]) > TOL_L:
                raise ValueError(f"{METHOD}: valued run {ln['line_id']} has a span that differs by frame")
            total = rec["L"] + sum(n["length"] for n in rec["necks"])
            out["bands"].setdefault(rec["band"], []).append(rec["run"])
            out["valued_runs"] += 1
            out["valued_m3"] = _r(out["valued_m3"] + ln["measured_net"])
            if total > rec["candidate"]["L"] + TOL_L:
                raise ValueError(f"{METHOD}: run {rec['run']} + necks exceed the band")
        elif a == "SPLIT_HELD" or a.startswith("HOLD_"):
            if ln["evidence_state"] != "BLOCKED_RFI" or ln.get("measured_net") is not None \
                    or not (ln.get("rfi") or {}).get("question"):
                raise ValueError(f"{METHOD}: held {ln['line_id']} is not blank with its reason")
            if rec.get("beside") is not None:
                if min(rec["beside"]) <= 0:
                    raise ValueError(f"{METHOD}: held {ln['line_id']} carries a 0 beside")
                out["held_beside_m3"] = [_r(out["held_beside_m3"][0] + rec["beside"][0]),
                                         _r(out["held_beside_m3"][1] + rec["beside"][1])]
            if a == "SPLIT_HELD":
                out["held_runs"] += 1
                out["bands"].setdefault(rec["band"], []).append(rec["run"])
            else:
                out["held_lines"] += 1
        else:
            raise ValueError(f"{METHOD}: action {a}")
    for band, runs in out["bands"].items():
        if len(set(runs)) != len(runs):
            raise ValueError(f"{METHOD}: band {band}: a run carried twice (double count)")
    out["bands"] = {k: sorted(v) for k, v in sorted(out["bands"].items())}
    return out


# ================================================================================================ integrate / write
def integrate(l3039, changes, for_lead=()):
    """-> (V3.0.40 lines, identity). Changed lines replace their V3.0.39 line in place; added lines follow; every other
    V3.0.39 line is byte-identical (asserted)."""
    sid = {ln["line_id"]: i for i, ln in enumerate(l3039)}
    out = list(l3039)
    adds, repl = [], set()
    for c in changes:
        a = c["after"]
        if a["item_code"] not in OWN_CODES:
            raise ValueError(f"{METHOD}: {a['item_code']} is not a code this version may change or add")
        if c["action"] == "ADD":
            if a["line_id"] in sid:
                raise ValueError(f"{METHOD}: an added line repeats a V3.0.39 id")
            adds.append(a)
        elif c["action"] == "CHANGE":
            i = sid.get(a["line_id"])
            if i is None or a["line_id"] in repl:
                raise ValueError(f"{METHOD}: a changed line is not a V3.0.39 line or changes twice")
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
    runs = check_runs(out)
    pids = {(ln["project"]["project_id"], ln["project"]["revision_set_sha256"]) for ln in out}
    if len(pids) != 1:
        raise ValueError(f"{METHOD}: {len(pids)} project identities in the lines")
    outside = [ln for ln in l3039 if ln["line_id"] not in repl]
    bad = [a["line_id"] for a in outside if A30.line_sha(a) != A30.line_sha(out[sid[a["line_id"]]])]
    if bad:
        raise ValueError(f"{METHOD}: {len(bad)} V3.0.39 line(s) differ outside the named changes")
    ident = {"v3_0_39_lines": len(l3039), "v3_0_40_lines": len(out), "v3_0_40_rows": len(changes),
             "replaced": len(repl), "added": len(adds), "outside_rows": len(outside),
             "outside_rows_identical_to_v3_0_39": len(outside), "gb_runs": runs, "flights": flights, "beds": beds,
             "lift": lift, "landing": landing, "lists": lists, "fence": fence, "tile_zones": zones,
             "corrections": corr, "ceilings": ceil, "roof_buildup": roof, "guards": guards,
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
                     "element_id": loc.get("element_id"), "unit": ref["unit"], "run": c.get("run"),
                     "before_released_v2_9": b29, "before_v3_0_39": A30._qty(c.get("before")),
                     "after_v3_0_40": A30._qty(ref), "evidence_status": c.get("evidence_status"),
                     "still_held": c.get("held"), "release_status": "NOT RELEASED",
                     "owner_manual_method": PIECES[c["piece"]]["owner_manual_method"],
                     "drawing_derived_method": PIECES[c["piece"]]["drawing_method"],
                     "record": rec, "verification": c.get("verification") or {}, "rollback": ROLLBACK})
    return rows


LEDGER_CSV = ("version", "piece", "action", "change", "line_id", "item_code", "floor", "element_id", "unit", "run",
              "v2_9", "v3_0_39", "v3_0_40", "evidence_status", "still_held", "verification")
DIFF_CSV = ("line_id", "item_code", "floor", "element_id", "unit", "vs_v3_0_39", "vs_released_v2_9", "v2_9",
            "v3_0_39", "v3_0_40")


def ledger_csv(rows):
    def q(x):
        return A302._q(x) if x and (x.get("value") is not None or x.get("low") is not None) else ""

    def h(r):
        return "; ".join(f"{x['what']} range {x.get('range')}" for x in (r.get("still_held") or ()))[:300]
    return A305._csv([{"version": r["version"], "piece": r["piece"], "action": r["action"], "change": r["change"],
                       "line_id": r["line_id"], "item_code": r["item_code"], "floor": r.get("floor") or "",
                       "element_id": r.get("element_id") or "", "unit": r["unit"], "run": r.get("run") or "",
                       "v2_9": q(r.get("before_released_v2_9")), "v3_0_39": q(r.get("before_v3_0_39")),
                       "v3_0_40": q(r.get("after_v3_0_40")), "evidence_status": r["evidence_status"],
                       "still_held": h(r),
                       "verification": f"{r['verification'].get('task')} "
                                       f"{' '.join(x[:8] for x in r['verification'].get('merge_commits') or ())}"}
                      for r in rows], LEDGER_CSV)


def diff_rows(l3039, l3040, released_lines=None):
    b39 = {ln["line_id"]: ln for ln in l3039}
    rel = {A30._key(ln): ln for ln in released_lines or ()}
    out = []
    for ln in l3040:
        o = b39.get(ln["line_id"])
        vs = "ADDED" if o is None else ("SAME" if A30.line_sha(o) == A30.line_sha(ln) else "CHANGED")
        r = rel.get(A30._key(ln)) if released_lines is not None else None
        vs29 = None if released_lines is None else ("NOT_IN_RELEASED" if r is None else
                                                    ("SAME_QUANTITY" if A30._qty(r) == A30._qty(ln) else
                                                     "QUANTITY_DIFFERS"))
        out.append({"line_id": ln["line_id"], "item_code": ln["item_code"], "floor": ln["location"].get("floor"),
                    "element_id": ln["location"].get("element_id"), "unit": ln["unit"], "vs_v3_0_39": vs,
                    "vs_released_v2_9": vs29, "v2_9": A302._q(A30._qty(r)) if r else "",
                    "v3_0_39": A302._q(A30._qty(o)) if o else "", "v3_0_40": A302._q(A30._qty(ln))})
    return out


def write(out, l3039, changes, log, released_lines=None, for_lead=()):
    """the V3_0_40_* files beside the V3_0_39_* files. -> (file names, identity, ledger)."""
    from pathlib import Path
    from engine.source import boq_line as BL
    out = Path(out)
    l3040, ident = integrate(l3039, changes, for_lead)
    rows = ledger_rows(changes, released_lines)
    diff = diff_rows(l3039, l3040, released_lines)
    named = {c["after"]["line_id"] for c in changes}
    stray = [d["line_id"] for d in diff if d["vs_v3_0_39"] in ("CHANGED", "ADDED") and d["line_id"] not in named]
    if stray:
        raise ValueError(f"{METHOD}: {len(stray)} line(s) changed outside the named changes")
    dsum = {}
    for d in diff:
        dsum.setdefault("vs_v3_0_39", {}).setdefault(d["vs_v3_0_39"], 0)
        dsum["vs_v3_0_39"][d["vs_v3_0_39"]] += 1
        if d["vs_released_v2_9"] is not None:
            dsum.setdefault("vs_released_v2_9", {}).setdefault(d["vs_released_v2_9"], 0)
            dsum["vs_released_v2_9"][d["vs_released_v2_9"]] += 1
    ident = dict(ident, diff=dsum)
    t39, t40 = A304.code_totals(l3039), A304.code_totals(l3040)
    moved = {k: {"v3_0_39": t39.get(k), "v3_0_40": t40.get(k)} for k in sorted(set(t39) | set(t40))
             if t39.get(k) != t40.get(k)}
    if any(k.split("|")[0] not in OWN_CODES for k in moved):
        raise ValueError(f"{METHOD}: totals moved outside this version's codes: {sorted(moved)[:5]}")
    led = {"schema": LEDGER_SCHEMA, "method": METHOD, "extends": EXTENDS, "candidate": CANDIDATE,
           "base": A30.BASE_METHOD, "released": A30.RELEASED_METHOD, "released_default": False, "rows": rows,
           "waiting_pieces": WAITING, "integration_package": True}
    run = {"method": METHOD, "policy": POLICY_ID, "extends": EXTENDS, "candidate": CANDIDATE,
           "base_method": A30.BASE_METHOD, "released_method": A30.RELEASED_METHOD, "released_default": False,
           "rollback": ROLLBACK, "identity": ident, "pieces": PIECES, "piece_logs": [log],
           "totals_moved_by_code": moved, "waiting_pieces": WAITING}
    files = {"V3_0_40_BOQ_LINES.json": BL.dumps(l3040),
             "V3_0_40_BOQ_LINES.csv": A30._lines_csv(l3040),
             "V3_0_40_INTEGRATION_LEDGER.json": A30._j(led),
             "V3_0_40_INTEGRATION_LEDGER.csv": ledger_csv(rows),
             "V3_0_40_DIFF.csv": A305._csv(diff, DIFF_CSV),
             "V3_0_40_RUN.json": A30._j(run)}
    for name, text in files.items():
        (out / name).write_text(text, encoding="utf-8")
    return sorted(files), ident, led


def policy_record():
    return {"method": METHOD, "extends": EXTENDS, "pieces": sorted(PIECES), "inputs_schema": INPUTS_SCHEMA,
            "released_default": False, "rollback": ROLLBACK,
            "actions": ["SPLIT_VALUED", "SPLIT_HELD", "HOLD_RANGE", "HOLD_BLANK"]}


__all__ = ["METHOD", "PIECES", "WAITING", "DEFAULT_GUARD_CLASS", "INPUTS_SCHEMA", "load_inputs", "changes_for",
           "check_runs", "integrate", "ledger_rows", "diff_rows", "write", "InputsError"]
