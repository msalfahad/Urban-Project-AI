"""ARCH_TAKEOFF_V3.0.70 (T-693, lane I, CONCRETE GATE B ROUND 7 integration package): the SAME opt-in BOQ candidate as
ARCH_TAKEOFF_V3.0 .. V3.0.69 (engine.source.arch_v30, arch_v301 .. arch_v3069), extended with ONE piece built from the
Checker-merged T-689 held-range ledger (R-T689-1..3) and the Checker-merged T-688 R-T688-3 ruling; no line outside
STR.CONC.* moves, released m3 never:

  CONC_RANGE    a named STR.CONC.COLUMN line is restated as the merged ledger states it, with the figure RECOMPUTED here
                from its terms (section readings x storey height) and asserted equal to the ledger:
                  BOUND    a HELD blank line whose section is a CONFLICT with both readings known (drawn outline vs
                           schedule band) and whose height has a drawn lower datum and a printed ceiling:
                           smaller reading x lower height .. larger reading x upper height (one reading never chosen);
                  NARROW   a HELD bounded line whose end moves INSIDE its old range on a new drawn datum (never widened,
                           the other end byte-equal), e.g. a column top raised to the joint of a printed beam it supports;
                  OWNER    a line whose face the slab-region DETECTOR labels as another element (R-T688-3): the
                           detector label is not a BOQ line field, so the line gains the ownership record (physical
                           element, the wrong detector label and region, the corrected owner, the band pairing refused)
                           and its quantity, state, range and class stay exactly as they were; the line's item code must
                           be the code of the ruled owner (a ground-slab face -> STR.CONC.GROUND_SLAB).
                A height lower datum is accepted only as
                  BEAM_JOINT  (R-T689-1) a drawn head under a PRINTED beam: top >= max(head - read tolerance) + the
                              beam's printed total depth, transferred only to that beam's own support columns (a beam's top
                              at a support is the supporting column's top, one joint node, no plane premise);
                  PLANE       (R-T678-2 / R-T682-1) a slab-top lower bound on ONE_PLANE, sections checked;
                a head with no printed beam over it (a window head alone) bounds nothing: the line stays HELD.

R-T693-1 (every villa; = R-T682-2 (a) .. (u) as written, plus): (v) a column bound is the product of its own terms,
recomputed at wiring time and equal to the merged ledger to 1e-6 m3; a CONFLICT section carries both readings and is
bounded smaller x lower .. larger x upper; (w) a narrowing never widens a range and never moves the end it does not
name; (x) a slab-top bound from a beam joint reaches only that beam's supports; the plate-wide transfer of it waits for a
ruling (F-T689-1) and is refused here; (y) an ownership record changes no quantity, state, range or class, and binds only a line of the ruled owner's code; (z) the
designer items of every restated line stay named in its question (the section item and the top datum item).
Files: V3_0_70_BOQ_LINES.json / .csv, V3_0_70_INTEGRATION_LEDGER.json / .csv, V3_0_70_DIFF.csv, V3_0_70_RUN.json.
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
from engine.source import arch_v3067 as A3067
from engine.source import arch_v3068 as A3068
from engine.source import arch_v3069 as A3069

DEFAULT_GUARD_CLASS = "TOOLING"          # T-212: re-books Checker-merged member ledgers onto candidate lines
METHOD = "ARCH_TAKEOFF_V3.0.70"
EXTENDS = A3069.METHOD
CANDIDATE = A30.METHOD
POLICY_ID = "URBAN_BOQ_T693_ARCH_V3_0_70"
INPUTS_SCHEMA = "URBAN_V3070_INPUTS_V1"
LEDGER_SCHEMA = "URBAN_V3070_INTEGRATION_LEDGER_V1"
ROLLBACK = A30.ROLLBACK
InputsError = A3063.InputsError
_r = A3063._r
_fmt = A3063._fmt
line_class = A3063.line_class
RULE_ID, RULE_VERSION = "R-T693-1", "T-693"
REC_KEY = "concrete_ledger_v3070"
EARLIER_KEYS = A3067.EARLIER_KEYS + (A3067.REC_KEY,)
P_CR = "CONC_RANGE"
ACTIONS = ("BOUND", "NARROW", "OWNER")
OWNER_CODE = {"GROUND_SLAB": "STR.CONC.GROUND_SLAB", "MEMBER_STRIP": "STR.CONC.GROUND_BEAM"}   # R-T688-3 (c)
CODE_PREFIX, UNIT = A3063.CODE_PREFIX, A3063.UNIT
COLUMN = "STR.CONC.COLUMN"
BOUNDED, BLANK = A3063.BOUNDED, A3063.BLANK
TOT_TOL = A3063.TOT_TOL
TOL = 1e-6
LO_KINDS = ("BEAM_JOINT", "PLANE")
HI_KINDS = ("CEILING",)
BASE_STATUS = ("PRINTED", "APPROVED")
STATUSES = ("DRAWING-CONFIRMED", "HELD")             # WORKFLOW_CONTROLS s.5 (never VERIFIED here)
PLANE_RULE = A3067.PLANE_RULE
MAX_H = 12.0                                         # one storey of a villa column above 12 m is a unit slip

PIECES = {
    P_CR: {"module": "engine/source/arch_v3070.py (named STR.CONC.COLUMN lines restated from the Checker-merged T-689 "
                     "ledger: the 2F C2 at the B8 joint narrowed, five blank CONFLICT columns bounded; one ground-slab "
                     "line given its R-T688-3 ownership record (T-688); nothing else moves, released m3 never)",
           "policy": "CONCRETE_GATE_B_V7", "rule_id": "R-T689-1..3 / R-T678-2 / R-T688-3 (R-T693-1)",
           "owner_rules": ["R-CONC-OWN-1 / UP-CONC-JOINT-001 (column top = slab top; the column owns the shaft to "
                           "the joint)",
                           "Q-61 C / X6 (a schedule vs drawing section conflict is held with both readings, never "
                           "settled by picking the printed one)",
                           "UP-QTY-STATUS-001 (held is blank or bounded, never 0)",
                           "register ruling 'column tops under B8' (ELEMENT_REGISTER 2026-11-11 04:20)",
                           "ERS s.2-5 (drawn element first; one physical element once)"],
           "owner_manual_method": "column: section x storey height, member by member; a section conflict is held "
                                  "with both readings and a designer request; a height with no printed datum is held "
                                  "(no generic storey value)",
           "drawing_method": "the merged T-689 ledger: section readings = the drawn outline and the schedule band "
                             "(CONFLICT PRINTED_VS_DRAWN, T-217); height = base (APPROVED / PRINTED) to the slab top, "
                             "its lower end from a drawn head under a printed beam at that beam's supports (R-T689-1) or "
                             "a one-plane slab-top bound (R-T678-2), its upper end the printed finished mark (D-39 "
                             "ceiling); bound = smaller section x lower height .. larger section x upper height"},
}
WAITING = {k: v for k, v in A3069.WAITING.items() if k not in ("T682_ANNEX_COLUMNS",)}       # wired here
WAITING.update({
    "T693_COLUMN_OPEN": "2 STR.CONC.COLUMN lines stay HELD blank: the 2F tank columns C2 40F and C3 424 (D-44: the "
                        "up / down stand of B15 refuses their ceiling)",
    "T693_F_T689_1": "plate-wide transfer of the B8 joint bound (2F roof slab top >= 12.937) to the non-support 2F "
                     "columns is REFUSED (R-T678-2: 'T 18' printed inside the plate): +0.133640 m3 on the lows of C9 418, "
                     "C2 41B / 41E, C1 421 and PC-2F named, not applied; it needs the Lead's ruling on R-T669-2 vs "
                     "R-T678-2 (either both stand or the R-T669-2 plate lows lose their basis)",
    "T693_REGISTER_GAPS": "F-T689-2 (PC-2F section, FFRS 77B / SFRS 778 vs text 'P.C 20x50', no designer item) and "
                          "F-T689-3 (the five columns bounded here are not in D-66's registered list of 13 outlines): "
                          "the lines carry their section conflict in the question; the D-66 list is the Lead's",
    "T693_FORMWORK": "the STR.FORMWORK lines of the six restated columns (FW:<line>:FACES:HELD) stay HELD blank: the "
                     "formwork faces are not re-derived from the column bounds here (perimeter x height of a CONFLICT "
                     "section is a formwork package of its own)",
})


# ================================================================================================ inputs
def _num(x, w, lo=0.0, hi=100.0):
    if isinstance(x, bool) or not isinstance(x, (int, float)) or x != x or x <= lo or x > hi:
        raise InputsError(f"{w}: {x!r} is not a quantity in range ({lo} .. {hi})")
    return float(x)


def _readings(rs, w):
    """section readings in metres: [{"source", "b_m", "d_m"}], one or two; two = a CONFLICT (both kept)."""
    if not isinstance(rs, list) or not 1 <= len(rs) <= 2:
        raise InputsError(f"{w}: one section reading, or the two readings of a CONFLICT")
    out = []
    for r in rs:
        if not r.get("source"):
            raise InputsError(f"{w}: a section reading names its source (outline handle / schedule row)")
        b, d = _num(r.get("b_m"), f"{w} b", hi=3.0), _num(r.get("d_m"), f"{w} d", hi=3.0)
        if b < 0.05 or d < 0.05:
            raise InputsError(f"{w}: section {b} x {d} m below 0.05 m: a unit slip (cm or mm read as m)")
        out.append(dict(r, b_m=b, d_m=d, area_m2=_r(b * d)))
    if len(out) == 2 and abs(out[0]["area_m2"] - out[1]["area_m2"]) <= TOL:
        raise InputsError(f"{w}: two equal readings are one reading, not a CONFLICT")
    return out


def top_low(datum, member_mark, w="datum"):
    """R-T689-1 / R-T678-2: the lower bound of the column top (absolute m) from one accepted datum, or InputsError."""
    k = (datum or {}).get("kind")
    if k not in LO_KINDS:
        raise InputsError(f"{w}: lower top datum {k!r} is not a printed-beam joint or a one-plane slab bound "
                          f"(a head with no printed beam over it bounds no column top: the line stays HELD)")
    if k == "BEAM_JOINT":
        A3063._need(datum, ("beam", "heads", "beam_depth_m", "depth_source", "supports"), w)
        if member_mark not in datum["supports"]:
            raise InputsError(f"{w}: column {member_mark} is not a support of {datum['beam']} (supports "
                              f"{datum['supports']}): the joint bound is not transferred plate-wide (R-T693-1 (x), "
                              f"F-T689-1)")
        hs = datum["heads"]
        if not hs:
            raise InputsError(f"{w}: no drawn head under {datum['beam']}")
        for h in hs:
            A3063._need(h, ("id", "head_abs_m", "tol_m", "status"), w)
            if h["status"] != "DRAWING-CONFIRMED":
                raise InputsError(f"{w}: head {h['id']} is {h['status']}, not DRAWING-CONFIRMED")
            if not 0 <= float(h["tol_m"]) < 0.10:
                raise InputsError(f"{w}: head {h['id']} read tolerance {h['tol_m']} m")
        dep = _num(datum["beam_depth_m"], f"{w} beam depth", hi=2.0)
        return _r(max(float(h["head_abs_m"]) - float(h["tol_m"]) for h in hs) + dep)
    pl = A3067._plane(datum.get("plane"), w)
    return _r(float(pl["s_lo_m"]))


def height_range(h, member_mark, w="height"):
    """-> (h_lo, h_hi, record): base to the slab-top joint, lower top from an accepted datum, upper top the ceiling."""
    A3063._need(h, ("base_m", "base_status", "datum_lo", "datum_hi"), w)
    if h["base_status"] not in BASE_STATUS:
        raise InputsError(f"{w}: base status {h['base_status']!r} (printed or approved datum only)")
    base = float(h["base_m"])
    tlo = top_low(h["datum_lo"], member_mark, w)
    dh = h["datum_hi"]
    if (dh or {}).get("kind") not in HI_KINDS or dh.get("mark_abs_m") is None or not dh.get("what"):
        raise InputsError(f"{w}: the upper top is a printed ceiling mark with what it is")
    thi = float(dh["mark_abs_m"])
    lo, hi = _r(tlo - base), _r(thi - base)
    if not 0 < lo <= hi <= MAX_H:
        raise InputsError(f"{w}: height {lo} .. {hi} m (base {base}, top {tlo} .. {thi}) is not 0 < low <= high")
    for k, v in (("h_lo_m", lo), ("h_hi_m", hi)):
        if h.get(k) is not None and abs(float(h[k]) - v) > TOL:
            raise InputsError(f"{w}: ledger {k} {h[k]} is not the recomputed {v}")
    return lo, hi, dict(h, top_lo_abs_m=tlo, top_hi_abs_m=thi, h_lo_m=lo, h_hi_m=hi)


def column_bound(e, w="bound"):
    """R-T693-1 (v): smaller reading x lower height .. larger reading x upper height (m3)."""
    rs = _readings(e["readings"], w)
    hlo, hhi, hrec = height_range(e["height"], e["member_mark"], w)
    a = sorted(r["area_m2"] for r in rs)
    return _r(a[0] * hlo), _r(a[-1] * hhi), rs, hrec


def _status(s, w):
    if not isinstance(s, dict) or s.get("low_end") not in STATUSES or s.get("high_end") not in STATUSES or \
            not s.get("basis"):
        raise InputsError(f"{w}: end statuses DRAWING-CONFIRMED / HELD with their basis (WORKFLOW_CONTROLS s.5; "
                          f"never VERIFIED here)")
    return dict(s)


def _entry(x, srcs):
    a = x.get("action")
    w = f"{a} {x.get('line_id')}"
    if a not in ACTIONS:
        raise InputsError(f"entry action {a!r}: V3.0.70 restates to BOUND, NARROW or OWNER only (R-T682-2 (u): "
                          f"released m3 does not move)")
    if not isinstance(x.get("line_id"), str) or not A3063.LINE_ID_RE.match(x["line_id"]):
        raise InputsError(f"{w}: line id")
    A3043._tasks(x, srcs, w)
    A3063._need(x, ("expect", "member", "basis"), w)
    ex = x["expect"]
    A3063._need(ex, ("item_code", "element_id", "unit", "class"), w)
    if not str(ex["item_code"]).startswith(CODE_PREFIX) or ex["unit"] != UNIT:
        raise InputsError(f"{w}: {ex['item_code']} {ex['unit']} is not a code this version may change (STR.CONC.* m3)")
    e = dict(x)
    if a in ("BOUND", "NARROW"):
        if ex["item_code"] != COLUMN or ex["class"] != "HELD":
            raise InputsError(f"{w}: a range restatement here is a HELD {COLUMN} line")
        A3063._need(x, ("readings", "height", "member_mark", "question", "after", "status"), w)
        if (a == "BOUND") != (ex.get("low") is None):
            raise InputsError(f"{w}: BOUND starts from a blank line, NARROW from a bounded one")
        if (ex.get("low") is None) != (ex.get("high") is None):
            raise InputsError(f"{w}: expect low and high together, or neither (blank)")
        lo, hi, rs, hrec = column_bound(x, w)
        af = x["after"]
        if abs(_num(af.get("low"), f"{w} low") - lo) > TOL or abs(_num(af.get("high"), f"{w} high") - hi) > TOL:
            raise InputsError(f"{w}: ledger {af.get('low')} .. {af.get('high')} is not the recomputed {lo} .. {hi} "
                              f"(R-T693-1 (v))")
        if not 0 < lo <= hi:
            raise InputsError(f"{w}: bound {lo} .. {hi}")
        if a == "NARROW":
            olo, ohi = float(ex["low"]), float(ex["high"])
            if lo < olo - TOL or hi > ohi + TOL:
                raise InputsError(f"{w}: {lo} .. {hi} is not inside {olo} .. {ohi} (a narrowing never widens, "
                                  f"R-T693-1 (w))")
            moved = [k for k, o, n in (("low", olo, lo), ("high", ohi, hi)) if abs(o - n) > TOL]
            if not moved:
                raise InputsError(f"{w}: nothing narrows")
            if sorted(moved) != sorted(x.get("ends_moved") or ()):
                raise InputsError(f"{w}: ends moved {moved} are not the ledger's {x.get('ends_moved')} (R-T693-1 (w))")
        if len(rs) == 1 and a == "BOUND":
            raise InputsError(f"{w}: a blank line bounded on one reading needs no conflict: it is not this piece")
        if not x.get("items") or not all(str(i).strip() for i in x["items"]):
            raise InputsError(f"{w}: the designer items that keep the line HELD are named (R-T693-1 (z))")
        e.update(_after={"low": lo, "high": hi}, _readings=rs, _height=hrec, status=_status(x["status"], w))
    else:                                               # OWNER
        A3063._need(x, ("label", "ruling"), w)
        lb = x["label"]
        A3063._need(lb, ("detector", "region", "from", "to"), w)
        if lb["from"] == lb["to"]:
            raise InputsError(f"{w}: the detector label is not corrected")
        if OWNER_CODE.get(lb["to"]) != ex["item_code"]:
            raise InputsError(f"{w}: the ruled owner {lb['to']} is {OWNER_CODE.get(lb['to'])}, not this line's "
                              f"{ex['item_code']} (R-T693-1 (y))")
        if ex["class"] == "RELEASED" and ex.get("value") is None:
            raise InputsError(f"{w}: a released line's record is bound to its released value (expect value)")
        if x.get("after") or x.get("readings") or x.get("height"):
            raise InputsError(f"{w}: an ownership record carries no quantity terms (R-T693-1 (y))")
    return e


def load_inputs(doc, project_id=None):
    """URBAN_V3070_INPUTS_V1 -> the validated doc.
    {"schema", "project_id", "sources": [{"task", "file", "sha256", "merge_commit", "checker_run"}],
     "expect_totals": {"<code>|m3": {...}} (optional, asserted on the code totals),
     "entries": [{"action" BOUND | NARROW | OWNER, "line_id", "source_tasks", "member", "member_mark", "basis",
                  "expect" {item_code, element_id, unit, class, low, high},
                  BOUND / NARROW: "readings" [{source, b_m, d_m}], "height" {base_m, base_status, datum_lo {kind
                  BEAM_JOINT {beam, heads [{id, head_abs_m, tol_m, status}], beam_depth_m, depth_source, supports} |
                  PLANE {plane}}, datum_hi {kind CEILING, mark_abs_m, what}, h_lo_m, h_hi_m}, "after" {low, high},
                  "ends_moved" (NARROW), "items", "question", "status" {low_end, high_end, basis};
                  OWNER: "label" {detector, region, from, to, refused}, "ruling"}]}"""
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
    ids = [e["line_id"] for e in ents]
    if len(set(ids)) != len(ids):
        raise InputsError("a line is named twice (one line, one restatement)")
    return dict(doc, _sources=srcs, _entries=ents)


# ================================================================================================ lines
def _rec(srcs, **kw):
    return dict({"piece": P_CR, "policy": PIECES[P_CR]["policy"], "tasks": [s["task"] for s in srcs],
                 "ledgers": [s["file"] for s in srcs], "ledger_sha256": [s["sha256"] for s in srcs],
                 "merge_commits": [s["merge_commit"] for s in srcs], "checker_runs": [s["checker_run"] for s in srcs],
                 "rule_id": RULE_ID, "rule_version": RULE_VERSION, "release_status": "NOT RELEASED"}, **kw)


def _supersede(inp):
    return {k: inp.pop(k) for k in EARLIER_KEYS if k in inp}


def _assert_before(b, e):
    if e["action"] != "OWNER":
        A3063._assert_bound(b, e)                 # code, element, unit, class, range (blank = no range)
    else:
        x, w = e["expect"], f"OWNER {e['line_id']}"
        if b is None:
            raise InputsError(f"{w}: not in the candidate (stale binding)")
        ok = (b["item_code"] == x["item_code"] and (b.get("location") or {}).get("element_id") == x["element_id"]
              and b["unit"] == x["unit"] and line_class(b) == x["class"])
        if ok and x["class"] == "RELEASED":
            ok = b.get("measured_net") is not None and abs(float(b["measured_net"]) - float(x.get("value"))) <= TOL
        if not ok:
            raise InputsError(f"{w}: candidate line {b['item_code']} {line_class(b)} {b.get('measured_net')} is not "
                              f"the ruling's {x} (stale binding)")
    if e["action"] != "OWNER" and b["evidence_state"] not in (BOUNDED, BLANK):
        raise InputsError(f"{e['action']} {e['line_id']}: state {b['evidence_state']} is not a held column state")


def _height_text(h):
    d = h["datum_lo"]
    if d["kind"] == "BEAM_JOINT":
        hs = ", ".join(f"{x['id']} {x['head_abs_m']} - {x['tol_m']}" for x in d["heads"])
        lo = (f"top >= max({hs}) + {d['beam']} depth {d['beam_depth_m']} ({d['depth_source']}) = "
              f"{_fmt(h['top_lo_abs_m'])} (R-T689-1, support of {d['beam']})")
    else:
        lo = f"top >= slab {_fmt(h['top_lo_abs_m'])} ({PLANE_RULE} one plane)"
    return (f"base {h['base_m']} ({h['base_status']}); {lo}; top <= {h['datum_hi']['mark_abs_m']} "
            f"({h['datum_hi']['what']}); h {_fmt(h['h_lo_m'])} .. {_fmt(h['h_hi_m'])} m")


def _restate(b, e, srcs):
    a = e["action"]
    ln = copy.deepcopy(b)
    was = {"evidence_state": b["evidence_state"], "measured_net": b.get("measured_net"), "gross": b.get("gross"),
           "bounded_range": b.get("bounded_range"), "rfi": b.get("rfi"),
           "formula": (b.get("calculation") or {}).get("formula"), "class": line_class(b)}
    inp = None
    if a == "OWNER":
        lb = e["label"]
        head = (f"owner {lb['to']} ({e['ruling']}): the {lb['detector']} labels this face {lb['from']} ({lb['region']}), "
                f"wrong; quantity unchanged")
        after = {"owner": lb["to"]}
        ln["calculation"] = dict(ln["calculation"])
        inp = ln["calculation"]["inputs"] = dict(ln["calculation"].get("inputs") or {})
        sup = {}
    else:
        af = e["_after"]
        rs = " vs ".join(f"{r['source']} {r['b_m']:g} x {r['d_m']:g} = {r['area_m2']:g} m2" for r in e["_readings"])
        terms = f"section {rs}; {_height_text(e['_height'])}"
        ln["evidence_state"], ln["measured_net"], ln["gross"] = BOUNDED, None, None
        ln["bounded_range"] = {"low": af["low"], "high": af["high"], "basis": f"{e['member']}: {e['basis']}"[:200]}
        ln["rfi"] = {"question": e["question"][:400], "blocks": [b["line_id"]]}
        ln["deductions"], ln["additions"] = [], []
        head = f"HELD (BOUNDED) {_fmt(af['low'])} .. {_fmt(af['high'])} m3"
        after = dict(af)
        ln["calculation"] = dict(ln["calculation"], formula=(
            f"{METHOD}: {head} = {e['member']}: smaller section x lower height .. larger section x upper height; "
            f"{terms}; ends: low {e['status']['low_end']}, high {e['status']['high_end']}; held on "
            f"{', '.join(e['items'])}")[:1500])
        inp = ln["calculation"]["inputs"] = dict(ln["calculation"].get("inputs") or {})
        sup = _supersede(inp)
    inp[REC_KEY] = _rec(srcs, action=a, member=e["member"], member_mark=e.get("member_mark"), was=was, after=after,
                        basis=e["basis"][:600], readings=e.get("_readings"), height=e.get("_height"),
                        items=e.get("items"), ends_moved=e.get("ends_moved"), status=e.get("status"),
                        label=e.get("label"), ruling=e.get("ruling"), superseded=sup,
                        freelancer_beside=e.get("freelancer_beside"))
    A305._note(ln, f"{METHOD}: {head[:300]} (was {A302._q(A30._qty(b)) or 'blank'})"
               + ("" if a == "OWNER" else "; NOT RELEASED"))
    return A3063._fin(ln)


def changes_for(doc, prev):
    """-> (changes, log)."""
    if not doc:
        return [], {"piece": "T693", "state": "NO_PROJECT_INPUT"}
    if any(((ln.get("calculation") or {}).get("inputs") or {}).get(REC_KEY) for ln in prev):
        raise InputsError("the candidate already carries V3.0.70 records (applied once)")
    by = {ln["line_id"]: ln for ln in prev}
    S = doc["_sources"]
    changes = []
    log = {"piece": "T693", "state": "RUN", "by_action": {}, "lines": 0,
           "sources": [{k: s[k] for k in ("task", "file", "sha256", "merge_commit")} for s in doc["sources"]]}
    for e in doc["_entries"]:
        b = by.get(e["line_id"])
        _assert_before(b, e)
        srcs = [S[t] for t in e["source_tasks"]]
        after = _restate(b, e, srcs)
        log["by_action"][e["action"]] = log["by_action"].get(e["action"], 0) + 1
        q = A30._qty(after)
        held = None if e["action"] == "OWNER" else [
            {"what": e["member"], "why": "; ".join(e["items"]), "range": [q["low"], q["high"]]}]
        changes.append(A305._change(P_CR, "CHANGE", b, after, drawing_reference="; ".join(s["file"] for s in srcs),
                                    held=held, downstream=[], verification=A3036._ver(srcs),
                                    evidence_status=line_class(after) if e["action"] == "OWNER" else "HELD",
                                    codes=[P_CR], group=b["item_code"], step=e["action"]))
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
    out = {}
    for k in moved:
        if k not in want:
            raise ValueError(f"{METHOD}: {k} moved with no change on it")
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
        if k in moved:
            out[k] = {"base": t0.get(k), "v3_0_70": a}
    return out


def check_concrete(lines, before=None):
    """on finished lines: every V3.0.70 line is in the state its action names; a range line is HELD bounded with its
    question and its items, its recomputed terms equal to its range; an OWNER line kept its quantity, state and
    class; with `before`, no STR.CONC line changed class to RELEASED and no released quantity moved. -> summary"""
    out = {a: 0 for a in ACTIONS}
    old = {x["line_id"]: x for x in before} if before is not None else None
    for ln in lines:
        rec = ((ln.get("calculation") or {}).get("inputs") or {}).get(REC_KEY)
        if not rec:
            continue
        a = rec["action"]
        ok = ln["item_code"].startswith(CODE_PREFIX) and ln["unit"] == UNIT
        if a in ("BOUND", "NARROW"):
            r = A3063._range(ln)
            ok = ok and ln["item_code"] == COLUMN and line_class(ln) == "HELD" and r is not None and \
                0 < r[0] <= r[1] + 1e-9 and bool((ln.get("rfi") or {}).get("question")) and bool(rec.get("items")) \
                and abs(r[0] - rec["after"]["low"]) <= TOL and abs(r[1] - rec["after"]["high"]) <= TOL and \
                rec["was"]["class"] == "HELD"
            if ok and a == "NARROW":
                w = rec["was"]["bounded_range"] or {}
                ok = w.get("low") is not None and r[0] >= w["low"] - TOL and r[1] <= w["high"] + TOL
            if ok and a == "BOUND":
                ok = rec["was"]["bounded_range"] is None
        elif a == "OWNER":
            w = rec["was"]
            ok = ok and ln["evidence_state"] == w["evidence_state"] and ln.get("measured_net") == w["measured_net"] \
                and ln.get("bounded_range") == w["bounded_range"] and line_class(ln) == w["class"] and \
                OWNER_CODE.get((rec.get("label") or {}).get("to")) == ln["item_code"]
        else:
            ok = False
        if ok and old is not None:
            o = old.get(ln["line_id"])
            ok = o is not None and line_class(o) == rec["was"]["class"]
        if not ok:
            raise ValueError(f"{METHOD}: {ln['line_id']}: a {a} line is not in its state")
        out[a] += 1
    if old is not None:
        for ln in lines:
            o = old.get(ln["line_id"])
            if o is None or not ln["item_code"].startswith(CODE_PREFIX):
                continue
            if line_class(ln) == "RELEASED" and (line_class(o) != "RELEASED" or
                                                 o.get("measured_net") != ln.get("measured_net")):
                raise ValueError(f"{METHOD}: {ln['line_id']}: released concrete moved (R-T682-2 (u))")
    return out


def _governed(ln):
    return bool(((ln.get("calculation") or {}).get("inputs") or {}).get(REC_KEY))


# ================================================================================================ integrate / write
def integrate(prev, changes, for_lead=()):
    """-> (V3.0.70 lines, identity). Changed lines replace their candidate line in place; every other candidate line
    is byte-identical (asserted); the earlier state checks re-run: V3.0.64 .. V3.0.67 concrete, V3.0.67 lintels,
    V3.0.68 masonry, V3.0.69 finishes (nothing of theirs may move)."""
    sid = {ln["line_id"]: i for i, ln in enumerate(prev)}
    out = list(prev)
    repl = set()
    for c in changes:
        a = c["after"]
        if not a["item_code"].startswith(CODE_PREFIX) or a["unit"] != UNIT:
            raise ValueError(f"{METHOD}: {a['item_code']} is not a code this version may touch")
        if c["action"] != "CHANGE":
            raise ValueError(f"{METHOD}: action {c['action']} (V3.0.70 adds no line)")
        i = sid.get(a["line_id"])
        if i is None or a["line_id"] in repl:
            raise ValueError(f"{METHOD}: a changed line is not a candidate line or changes twice")
        out[i] = a
        repl.add(a["line_id"])
    if len({ln["line_id"] for ln in out}) != len(out):
        raise ValueError(f"{METHOD}: a BOQ line id appears twice")
    outside = [ln for ln in prev if ln["line_id"] not in repl]
    bad = [a["line_id"] for a in outside if A30.line_sha(a) != A30.line_sha(out[sid[a["line_id"]]])]
    if bad:
        raise ValueError(f"{METHOD}: {len(bad)} candidate line(s) differ outside the named changes")
    pids = {(ln["project"]["project_id"], ln["project"]["revision_set_sha256"]) for ln in out}
    if len(pids) != 1:
        raise ValueError(f"{METHOD}: {len(pids)} project identities in the lines")
    ident = {"base_lines": len(prev), "v3_0_70_lines": len(out), "v3_0_70_rows": len(changes), "replaced": len(repl),
             "added": 0, "concrete_v3_0_64": A3064.check_concrete(out), "concrete_v3_0_65": A3065.check_concrete(out),
             "concrete_v3_0_66": A3066.check_concrete(out), "concrete_v3_0_67": A3067.check_concrete(out, prev),
             "lintels_v3_0_67": A3067.check_lintels(out), "masonry_v3_0_68": A3068.check_masonry(out),
             "finishes_v3_0_69": A3069.check_finishes(out), "concrete": check_concrete(out, prev),
             "outside_rows": len(outside), "outside_rows_identical_to_base": len(outside),
             "outside_rows_sha256": hashlib.sha256("".join(A30.line_sha(x) for x in outside).encode()).hexdigest()}
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
                     "after_v3_0_70": A30._qty(ref), "class": [rec["was"]["class"], line_class(ref)],
                     "evidence_status": c.get("evidence_status"), "end_status": rec.get("status"),
                     "readings": rec.get("readings"), "height": rec.get("height"), "items": rec.get("items"),
                     "label": rec.get("label"), "still_held": c.get("held"),
                     "superseded_record_keys": sorted(rec.get("superseded") or {}),
                     "release_status": "NOT RELEASED", "basis": rec["basis"],
                     "owner_manual_method": PIECES[c["piece"]]["owner_manual_method"],
                     "drawing_derived_method": PIECES[c["piece"]]["drawing_method"],
                     "verification": c.get("verification") or {}, "rollback": ROLLBACK})
    return rows


LEDGER_CSV = ("version", "piece", "action", "line_id", "item_code", "floor", "member", "element_id", "unit", "v2_9",
              "base", "v3_0_70", "class", "ends", "evidence_status", "verification")
DIFF_CSV = ("line_id", "item_code", "floor", "element_id", "unit", "vs_base", "vs_released_v2_9", "v2_9", "base",
            "v3_0_70")


def ledger_csv(rows):
    def q(x):
        return A302._q(x) if x and (x.get("value") is not None or x.get("low") is not None or x.get("state")) else ""
    return A305._csv([{"version": r["version"], "piece": r["piece"], "action": r["action"], "line_id": r["line_id"],
                       "item_code": r["item_code"], "floor": r.get("floor") or "", "member": r.get("member") or "",
                       "element_id": r.get("element_id") or "", "unit": r["unit"],
                       "v2_9": q(r.get("before_released_v2_9")), "base": q(r.get("before_base")),
                       "v3_0_70": q(r.get("after_v3_0_70")), "class": " -> ".join(r["class"]),
                       "ends": (f"low {r['end_status']['low_end']} / high {r['end_status']['high_end']}"
                                if r.get("end_status") else f"owner {(r.get('label') or {}).get('to')}"),
                       "evidence_status": r["evidence_status"],
                       "verification": f"{r['verification'].get('task')} "
                                       f"{' '.join(x[:8] for x in r['verification'].get('merge_commits') or ())}"}
                      for r in rows], LEDGER_CSV)


def diff_rows(prev, new, released_lines=None):
    return [dict({k: v for k, v in d.items() if k != "v3_0_69"}, v3_0_70=d["v3_0_69"])
            for d in A3069.diff_rows(prev, new, released_lines)]


def write(out, prev, changes, log, released_lines=None, for_lead=(), expect_totals=None):
    """the V3_0_70_* files beside the base candidate's files. -> (file names, identity, ledger)."""
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
    ident = dict(ident, diff=dsum)
    moved = check_totals(A304.code_totals(prev), A304.code_totals(new), changes, expect_totals)
    led = {"schema": LEDGER_SCHEMA, "method": METHOD, "extends": EXTENDS, "candidate": CANDIDATE,
           "base": A30.BASE_METHOD, "released": A30.RELEASED_METHOD, "released_default": False, "rows": rows,
           "summary": log, "waiting_pieces": WAITING, "integration_package": True}
    run = {"method": METHOD, "policy": POLICY_ID, "extends": EXTENDS, "candidate": CANDIDATE,
           "base_method": A30.BASE_METHOD, "released_method": A30.RELEASED_METHOD, "released_default": False,
           "rollback": ROLLBACK, "identity": ident, "pieces": PIECES, "piece_logs": [log],
           "totals_moved_by_code": moved, "waiting_pieces": WAITING}
    files = {"V3_0_70_BOQ_LINES.json": BL.dumps(new),
             "V3_0_70_BOQ_LINES.csv": A30._lines_csv(new),
             "V3_0_70_INTEGRATION_LEDGER.json": A30._j(led),
             "V3_0_70_INTEGRATION_LEDGER.csv": ledger_csv(rows),
             "V3_0_70_DIFF.csv": A305._csv(diff, DIFF_CSV),
             "V3_0_70_RUN.json": A30._j(run)}
    for name, text in files.items():
        (out / name).write_text(text, encoding="utf-8")
    return sorted(files), ident, led


def policy_record():
    return {"method": METHOD, "extends": EXTENDS, "pieces": sorted(PIECES), "inputs_schema": INPUTS_SCHEMA,
            "released_default": False, "rollback": ROLLBACK, "actions": list(ACTIONS)}


__all__ = ["METHOD", "PIECES", "WAITING", "DEFAULT_GUARD_CLASS", "INPUTS_SCHEMA", "load_inputs", "changes_for",
           "top_low", "height_range", "column_bound", "check_concrete", "check_totals", "expected_totals", "integrate",
           "ledger_rows", "diff_rows", "write", "InputsError", "line_class"]
