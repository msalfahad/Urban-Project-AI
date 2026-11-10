"""ARCH_TAKEOFF_V3.0.66 (T-677, lane I, CONCRETE GATE B ROUND 5 integration package): the SAME opt-in BOQ candidate
as ARCH_TAKEOFF_V3.0 .. V3.0.65 (engine.source.arch_v30, arch_v301 .. arch_v3065), extended with ONE piece built from
Checker-merged research ledgers of concrete families (STR.CONC.*, m3) left unwired by V3.0.65: the lintels whose
heads were already drawn, a stair flight whose steps part is drawn, and the ground-slab panels re-derived from the
drawn faces (with the beam strip they border, wired in the same diff):

  CONC_LEDGER   a named concrete line is restated as its merged ledger states it, with the V3.0.65 actions and
                states (BOUND, VALUE, HELD_BLANK, LOWER_ONLY, UPPER_ONLY, CONFIRM, NOT_APPLICABLE, ADD_COMPANION;
                R-T671-1 re-used as written), plus (new in V3.0.66):
                  REVALUE        a RELEASED line whose drawn quantity a merged ledger re-derived and the Checker
                                 re-measured on its own: the line stays released at the drawn value (the old value,
                                 formula and deductions kept in the record, the delta stated and asserted); a plan
                                 area that the re-derivation moves to another line (`moves_to`) moves ONLY with that
                                 line's restatement in the same inputs (both or neither, ERS s.2.4);
                  CONFIRM        (on a RELEASED line) the ledger re-derived the drawn value and found it equal: the
                                 line is asserted at that value and stays byte-identical;
  CONC_SHARED   ADD_SHARED       a remainder between two (or more) BOUND lines of the same code that belongs to
                                 exactly one of them, which one not drawn (a pier shorter than both bearings): ONE
                                 new line HELD 0 .. x, named by its sharers; no sharer's high carries it (one
                                 physical element once).

R-T677-1 (every villa; = R-T671-1 + the four additions, ERS s.2-5, UP-QTY-STATUS-001, WORKFLOW CONTROLS s.1 / s.5):
(a) .. (l) as R-T671-1; (m) a released concrete line moves only by a Checker-merged drawn re-derivation with the
Checker's own re-measure: it stays released, its old value and deductions stay in its record and the delta is the
inputs' stated delta; (n) a plan area that leaves one line for another leaves only with the other line's restatement
in the same inputs; (o) a remainder shared by two bounded lines is one new line 0 .. x, never inside either sharer's
high, never in both; (p) a line this version restates keeps every earlier version's record, moved under
`superseded` (now including the V3.0.65 record); (q) a lintel line this version restates or adds is governed by
this version's lintel check (one line per opening, its V3.0.53 HELD record kept whole under `superseded`, a shared
remainder naming its sharers' openings), not by the V3.0.53 check whose states (REQUIRED valued / HELD blank) have
no bounded state; every other lintel line stays under the V3.0.53 check, which still re-runs on them.
Files: V3_0_66_BOQ_LINES.json / .csv, V3_0_66_INTEGRATION_LEDGER.json / .csv, V3_0_66_DIFF.csv, V3_0_66_RUN.json.
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

DEFAULT_GUARD_CLASS = "TOOLING"          # T-212: re-books Checker-merged member ledgers onto candidate lines
METHOD = "ARCH_TAKEOFF_V3.0.66"
EXTENDS = A3065.METHOD
CANDIDATE = A30.METHOD
POLICY_ID = "URBAN_BOQ_T677_ARCH_V3_0_66"
INPUTS_SCHEMA = "URBAN_V3066_INPUTS_V1"
LEDGER_SCHEMA = "URBAN_V3066_INTEGRATION_LEDGER_V1"
ROLLBACK = A30.ROLLBACK
InputsError = A3063.InputsError
_r = A3063._r
_fmt = A3063._fmt
RULE_ID, RULE_VERSION = "R-T677-1", "T-677"
REC_KEY = "concrete_ledger_v3066"
EARLIER_KEYS = A3065.EARLIER_KEYS + (A3065.REC_KEY,)
LINTEL_CODE, LINTEL_KEY = "STR.CONC.LINTEL", "lintel_v3053"   # engine.source.arch_v3053 REC_KEY (R-T487-1 record)
P_CL, P_SHARED = "CONC_LEDGER", "CONC_SHARED"
NA, COMP, REVALUE, SHARED = A3065.NA, A3065.COMP, "REVALUE", "ADD_SHARED"
NA_STATE = A3065.NA_STATE
BASE_ACTIONS = A3063.ACTIONS                    # BOUND, VALUE, HELD_BLANK, LOWER_ONLY, UPPER_ONLY, CONFIRM
ACTIONS = A3065.ACTIONS + (REVALUE, SHARED)
CHANGING = A3065.CHANGING + (REVALUE, SHARED)
CODE_PREFIX, UNIT = A3063.CODE_PREFIX, A3063.UNIT
BOUNDED, BLANK, VALUED = A3063.BOUNDED, A3063.BLANK, A3063.VALUED
TOT_TOL, BIND_TOL, MAX_Q = A3063.TOT_TOL, A3063.BIND_TOL, A3063.MAX_Q
EVIDENCE_STATUS = A3065.EVIDENCE_STATUS
line_class = A3063.line_class

PIECES = {
    P_CL: {"module": "engine/source/arch_v3066.py (named concrete lines restated from the Checker-merged T-673 / T-674 "
                     "ledgers: lintels with drawn heads bounded, a stair flight's drawn steps part beside its held "
                     "waist, ground-slab panels re-derived from the drawn faces with the beam strip they border; "
                     "nothing else moves)",
           "policy": "CONCRETE_GATE_B_V5", "rule_id": "R-T673-1..3 / R-T674-1..4 (R-T677-1)",
           "owner_rules": ["owner lintel rule 2026-11-02 (one per opening; bearing)",
                           "ST p.13 LINTEL SCHEDULE (B = wall width, D by width band, MIN 40 cm bearing)",
                           "C1 strip ownership (the ground beam owns its strip to its carriers' faces)",
                           "UP-QTY-STATUS-001 (held is blank or bounded, never 0)",
                           "ERS s.2-5 (drawn element first; one physical element once)"],
           "owner_manual_method": "lintel: opening width + bearing each side x the schedule section; stair: steps "
                                  "triangles x flight width + waist slab; ground slab: the panel between the "
                                  "ground-beam faces x T",
           "drawing_method": "the merged T-673 ledger: a lintel exists where its drawn head (T-201 / T-238 reads) "
                             "leaves masonry under the lowest piece (R-T673-1), length = opening + the drawn jamb ends "
                             "(R-T673-3: 0.40 bearing each side .. both end ceilings; a shared pier once); the steps "
                             "of ST-03 drawn, the waist not (S-9); the merged T-674 ledger: each panel rebuilt from "
                             "the drawn faces noded on the true arcs, an oblique beam's strip to its carriers' faces "
                             "(R-T674-1), no junction box over a drawn support (R-T674-3)"},
    P_SHARED: {"module": "engine/source/arch_v3066.py (a shared pier remainder between two bounded lintels: one new "
                         "line HELD 0 .. x)",
               "policy": "CONCRETE_GATE_B_V5", "rule_id": "R-T673-3 / R-T544-1 (4) (R-T677-1 (o))",
               "owner_rules": ["UP-QTY-STATUS-001", "ERS s.2.4 (one physical element once)"],
               "owner_manual_method": "each lintel takes its bearing on the pier; the remainder is not taken off",
               "drawing_method": "the pier between two openings minus both 0.40 bearings, x B x D, owned by one of "
                                 "the two lintels (which one not drawn): HELD 0 .. x on its own line"},
}
WAITING = {k: v for k, v in A3065.WAITING.items() if k not in ("T671_GROUND_SLAB_T674",)}   # wired here
WAITING.update({
    "T677_LINTEL_DESIGNER_OPEN": "28 STR.CONC.LINTEL lines stay HELD blank by the T-673 census: 6 DESIGNER ITEM (D-45 "
                                 "lift doors, D-GF-09 width conflict, W26 D-39) and 22 OPEN BOUND (20 host wall / piece "
                                 "HELD in the merged fill, W11 / W12 sill datum, W13 piece over the head not read)",
    "T677_STAIR_DESIGNER": "4 STR.CONC.STAIR lines keep their state (ST-01 remainder C-ST-4 / RFI-A04 / D-67, ST-01 "
                           "MS2 turn riser C-ST-3, ST-02 curved remainder D-08 / Q-50 / Q-51, ST-01b waist S-9); "
                           "ST-03's waist S-9 stays open (lower end only)",
    "T677_JUNCTION_FACE": "route G junction face (lift corner) keeps 0.7112 m2 that no slab line carries (lift ring, "
                          "shaft, two beam ends; T-401 / T-444): NO_LINE, named, unchanged",
    "T677_ENGINE_PROPOSALS": "R-T674-1 / -3 as method changes of the slab / junction modules (oblique band deducted to "
                             "the carriers, junction box clipped to drawn supports) are proposals: route G and the "
                             "released default are unchanged; V3.0.66 restates the named lines only",
})


# ================================================================================================ inputs
def _need(s, keys, where):
    return A3063._need(s, keys, where)


def _num(x, where, top=MAX_Q, zero=False):
    return A3063._num(x, where, top, zero)


def _released_x(e, w):
    x = e["expect"]
    _need(x, ("item_code", "element_id", "unit", "class"), w)
    if not str(x["item_code"]).startswith(CODE_PREFIX) or x["unit"] != UNIT or x["class"] != "RELEASED":
        raise InputsError(f"{w}: only a RELEASED STR.CONC.* m3 line is revalued or confirmed at a value")
    _num(x.get("value"), f"{w} expect value")


def _revalue_entry(e, srcs):
    w = f"{REVALUE} {e.get('line_id')}"
    if not isinstance(e.get("line_id"), str) or not A3063.LINE_ID_RE.match(e["line_id"]):
        raise InputsError(f"{w}: line id")
    A3043._tasks(e, srcs, w)
    _need(e, ("expect", "member", "basis", "remeasure", "after", "delta"), w)
    _released_x(e, w)
    if e.get("downgrade") or e.get("set_aside"):
        raise InputsError(f"{w}: a revalued line stays released (no downgrade, no bound set aside)")
    af = e["after"]
    v = _num(af.get("value"), f"{w} value")
    if af.get("low") is not None or af.get("high") is not None:
        raise InputsError(f"{w}: a value carries no range")
    d = e["delta"]
    if isinstance(d, bool) or not isinstance(d, (int, float)) or d != d:
        raise InputsError(f"{w}: delta not a number ({d!r})")
    if abs(v - e["expect"]["value"] - d) > BIND_TOL:
        raise InputsError(f"{w}: {e['expect']['value']} + delta {d} is not the value {v} (R-T677-1 (m))")
    if abs(d) <= BIND_TOL:
        raise InputsError(f"{w}: no change: a re-derivation that agrees is a CONFIRM")
    mv = e.get("moves_to")
    if mv is not None:
        _need(mv, ("line_id", "plan_m2", "why"), f"{w} moves_to")
        _num(mv["plan_m2"], f"{w} moves_to plan", top=1000.0)
    return dict(e, after={"value": v})


def _confirm_released_entry(e, srcs):
    w = f"CONFIRM {e.get('line_id')}"
    if not isinstance(e.get("line_id"), str) or not A3063.LINE_ID_RE.match(e["line_id"]):
        raise InputsError(f"{w}: line id")
    A3043._tasks(e, srcs, w)
    _need(e, ("expect", "member", "basis"), w)
    _released_x(e, w)
    if e.get("after") or e.get("downgrade"):
        raise InputsError(f"{w}: a CONFIRM entry changes nothing (no after)")
    return dict(e)


def _shared_entry(e, srcs):
    w = f"{SHARED} {e.get('key')}"
    A3043._tasks(e, srcs, w)
    _need(e, ("key", "add", "shared_by", "template_line", "basis", "why_held", "question", "after"), w)
    x = e["add"]
    _need(x, ("item_code", "unit", "element_id", "physical_element"), w)
    if not str(x["item_code"]).startswith(CODE_PREFIX) or x["unit"] != UNIT:
        raise InputsError(f"{w}: {x['item_code']} {x['unit']} is not a code this version may add (STR.CONC.* m3)")
    sb = e["shared_by"]
    if not isinstance(sb, list) or len(sb) < 2 or len(set(sb)) != len(sb):
        raise InputsError(f"{w}: a shared remainder names two or more distinct sharers")
    af = e["after"]
    lo, hi = _num(af.get("low"), f"{w} low", zero=True), _num(af.get("high"), f"{w} high")
    if lo != 0.0:
        raise InputsError(f"{w}: a shared remainder runs from 0 (it may belong to the other sharer), never a floor")
    if e.get("value") is not None:
        raise InputsError(f"{w}: a shared remainder carries no value")
    return dict(e, after={"low": lo, "high": hi})


def load_inputs(doc, project_id=None):
    """URBAN_V3066_INPUTS_V1 -> the validated doc.
    {"schema", "project_id", "sources": [{"task", "file", "sha256", "merge_commit", "checker_run"}],
     "expect_totals": {"<code>|m3": {...}} (optional, asserted on the code totals),
     "entries": [V3.0.65 entry (BOUND / VALUE / blank / CONFIRM on a HELD line / NOT_APPLICABLE / ADD_COMPANION) |
                 {"action": "REVALUE", "line_id", "source_tasks", "member", "basis", "remeasure",
                  "expect" {item_code, element_id, unit, class RELEASED, value}, "after" {value}, "delta",
                  "moves_to" {line_id, plan_m2, why} (optional; that line restated here too)} |
                 {"action": "CONFIRM", ..., "expect" {.. class RELEASED, value}} |
                 {"action": "ADD_SHARED", "key", "source_tasks", "shared_by" [line ids of BOUND entries],
                  "template_line", "add" {item_code, unit, element_id, floor, physical_element}, "after" {low 0, high},
                  "basis", "why_held", "question"}]}"""
    if not doc:
        return None
    if doc.get("schema") != INPUTS_SCHEMA:
        raise InputsError(f"project inputs: schema must be {INPUTS_SCHEMA}")
    if project_id and doc.get("project_id") not in (None, project_id):
        raise InputsError(f"project inputs are for {doc.get('project_id')!r}, the run is {project_id!r}")
    srcs = A3043._sources(doc)
    ents, v65 = [], []
    for x in doc.get("entries") or ():
        a = x.get("action")
        if a == REVALUE:
            ents.append(_revalue_entry(x, srcs))
        elif a == SHARED:
            ents.append(_shared_entry(x, srcs))
        elif a == "CONFIRM" and (x.get("expect") or {}).get("class") == "RELEASED":
            ents.append(_confirm_released_entry(x, srcs))
        elif a in A3065.ACTIONS:
            v65.append(x)
            ents.append(None)                             # placeholder: validated by the V3.0.65 loader below
        else:
            raise InputsError(f"entry action {a!r}")
    if v65:
        sub = A3065.load_inputs(dict(doc, schema=A3065.INPUTS_SCHEMA, entries=v65), project_id)["_entries"]
        it = iter(sub)
        ents = [e if e is not None else next(it) for e in ents]
    if not ents:
        raise InputsError("no entry in the inputs")
    seen = set()
    for e in ents:
        k = e.get("line_id") or f"{e['action']}:{e['key']}"
        if k in seen:
            raise InputsError(f"{k}: named twice (one line, one restatement)")
        seen.add(k)
    restated = {e["line_id"]: e for e in ents if e.get("line_id") and e["action"] not in ("CONFIRM",)}
    for e in ents:                                       # R-T677-1 (n): both or neither
        mv = e.get("moves_to") if e["action"] == REVALUE else None
        if mv and (mv["line_id"] not in restated or restated[mv["line_id"]]["action"] not in ("BOUND", "VALUE")):
            raise InputsError(f"{REVALUE} {e['line_id']}: {mv['plan_m2']} m2 moves to {mv['line_id']}, which these "
                              f"inputs do not restate (both or neither)")
    bounds = {e["line_id"]: e for e in ents if e["action"] == "BOUND"}
    taken = set()
    for e in ents:                                       # R-T677-1 (o): one remainder, named by its sharers
        if e["action"] != SHARED:
            continue
        for s in e["shared_by"]:
            b = bounds.get(s)
            if b is None or b["expect"]["item_code"] != e["add"]["item_code"]:
                raise InputsError(f"{SHARED} {e['key']}: sharer {s} is not a BOUND {e['add']['item_code']} entry here")
        k = frozenset(e["shared_by"])
        if k in taken:
            raise InputsError(f"{SHARED} {e['key']}: a second remainder for the same sharers")
        taken.add(k)
        if e["template_line"] not in e["shared_by"]:
            raise InputsError(f"{SHARED} {e['key']}: the template line is one of its sharers")
    return dict(doc, _sources=srcs, _entries=ents)


# ================================================================================================ lines
def _rec(srcs, piece=P_CL, **kw):
    return dict({"piece": piece, "policy": PIECES[piece]["policy"], "tasks": [s["task"] for s in srcs],
                 "ledgers": [s["file"] for s in srcs], "ledger_sha256": [s["sha256"] for s in srcs],
                 "merge_commits": [s["merge_commit"] for s in srcs], "checker_runs": [s["checker_run"] for s in srcs],
                 "rule_id": RULE_ID, "rule_version": RULE_VERSION, "release_status": "NOT RELEASED"}, **kw)


def _supersede(inp, code=None):
    """R-T677-1 (p) / (q): the earlier versions' records of a restated line, kept whole under this version's record
    (a lintel line's V3.0.53 record too)"""
    keys = EARLIER_KEYS + ((LINTEL_KEY,) if code == LINTEL_CODE else ())
    return {k: inp.pop(k) for k in keys if k in inp}


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
    elif a == REVALUE:
        v = float(af["value"])
        was["deductions"], was["additions"] = b.get("deductions") or [], b.get("additions") or []
        ln["measured_net"], ln["gross"] = _r(v), _r(v)           # its released state is kept
        ln["bounded_range"], ln["rfi"] = None, None
        head = (f"RE-DERIVED AS DRAWN {_fmt(v)} m3 (was {_fmt(b.get('measured_net'))}, delta "
                f"{e['delta']:+.6f}; Checker re-measure: {e['remeasure']})")[:400]
        after = {"value": _r(v), "delta": _r(e["delta"])}
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
    sup = _supersede(inp, b["item_code"])
    if b["item_code"] == LINTEL_CODE and a != "CONFIRM":
        lr = sup.get(LINTEL_KEY) or {}
        if lr.get("decision") != "HELD" or not lr.get("opening_id"):
            raise InputsError(f"{a} {b['line_id']}: a lintel line is restated only from its V3.0.53 HELD record "
                              f"(found {lr.get('decision')!r})")
    inp[REC_KEY] = _rec(srcs, action=a, member=e["member"], was=was, after=after, basis=e["basis"],
                        why_held=(e.get("why_held") or "")[:600], beside=e.get("beside"),
                        set_aside=e.get("set_aside"), remeasure=e.get("remeasure"), evidence=e.get("evidence"),
                        moves_to=e.get("moves_to"), shared=None, companion=None, superseded=sup,
                        freelancer_beside=e.get("freelancer_beside"))
    rel = "RELEASED (re-derived, Checker re-measure)" if a == REVALUE else "NOT RELEASED"
    A305._note(ln, f"{METHOD}: {head[:300]} (was {A302._q(A30._qty(b))}); {rel}")
    return A3063._fin(ln)


def _new_line(prev, e, srcs, piece, rec_extra, note):
    from engine.source import boq_line as BL
    by = {ln["line_id"]: ln for ln in prev}
    w = f"{e['action']} {e['key']}"
    tpl = by.get(e["template_line"])
    x = e["add"]
    if tpl is None or tpl["item_code"] != x["item_code"] or tpl["unit"] != x["unit"]:
        raise InputsError(f"{w}: template line {e['template_line']} is not a candidate {x['item_code']} line")
    if any(ln["item_code"] == x["item_code"] and (ln.get("location") or {}).get("element_id") == x["element_id"]
           for ln in prev):
        raise InputsError(f"{w}: {x['item_code']} {x['element_id']} is already carried by a candidate line")
    lo, hi = e["after"]["low"], e["after"]["high"]
    formula = (f"{METHOD}: HELD (BOUNDED) {_fmt(lo)} .. {_fmt(hi)} m3, {note}: {x['physical_element']}: {e['basis']}; "
               f"held by: {e['why_held']} (R-T677-1)")[:1500]
    rec = _rec(srcs, piece, action=e["action"], key=e["key"], member=x["physical_element"], was=None,
               after={"low": _r(lo), "high": _r(hi)}, basis=e["basis"], why_held=e["why_held"][:600], beside=None,
               set_aside=None, remeasure=None, evidence=None, moves_to=None, superseded={},
               template_line=e["template_line"], freelancer_beside=e.get("freelancer_beside"), **rec_extra)
    ln = BL.make_line(
        project_id=tpl["project"]["project_id"], revision_set_sha256=tpl["project"]["revision_set_sha256"],
        item_code=x["item_code"], unit=x["unit"], evidence_state=BOUNDED, measured_net=None, gross=None,
        element_id=x["element_id"], floor=x.get("floor"), physical_element=x["physical_element"], formula=formula,
        bounded_range={"low": _r(lo), "high": _r(hi), "basis": f"{note}: {e['basis']}"[:200]},
        inputs={REC_KEY: rec, "evidence_status": "HELD"}, documents=copy.deepcopy(tpl["source"]["documents"]),
        geometry_source=tpl["source"]["geometry_source"], geometry_confidence=tpl["source"]["geometry_confidence"],
        rule_id=RULE_ID, rule_version=RULE_VERSION, material_state=tpl.get("material_state") or "SOURCE",
        rfi={"question": e["question"][:900], "unlocks": x["element_id"]},
        notes=f"{METHOD}: {note} (held 0 .. {_fmt(hi)} m3); NOT RELEASED",
        item_en=tpl["item_en"], item_ar=tpl["item_ar"], trade=tpl["trade"], subtrade=tpl.get("subtrade"))
    if ln["line_id"] in by:
        raise InputsError(f"{w}: the new line id {ln['line_id']} is a candidate id")
    return BL.validate(ln)


def _assert_released(b, e):
    """the line is the RELEASED line the ledger read, at the value it read"""
    w = f"{e['action']} {e['line_id']}"
    if b is None:
        raise InputsError(f"{w}: not in the candidate (stale binding)")
    x, loc = e["expect"], b.get("location") or {}
    ok = b["item_code"] == x["item_code"] and loc.get("element_id") == x["element_id"] and b["unit"] == x["unit"] \
        and line_class(b) == "RELEASED" and abs(float(b["measured_net"]) - x["value"]) <= BIND_TOL
    if not ok:
        raise InputsError(f"{w}: {b['item_code']} {loc.get('element_id')} {b['evidence_state']} "
                          f"{b.get('measured_net')} is not the ledger's {x} (stale binding: re-read)")


def changes_for(doc, prev):
    """-> (changes, log). CONFIRM entries are asserted on the candidate line and change nothing."""
    if not doc:
        return [], {"piece": "T677", "state": "NO_PROJECT_INPUT"}
    if any(((ln.get("calculation") or {}).get("inputs") or {}).get(REC_KEY) for ln in prev):
        raise InputsError("the candidate already carries V3.0.66 records (applied once)")
    by = {ln["line_id"]: ln for ln in prev}
    S = doc["_sources"]
    changes, valued = [], {}
    log = {"piece": "T677", "state": "RUN", "sources": doc["sources"], "by_action": {}, "lines": 0, "added": 0,
           "confirmed": [], "not_applicable": [], "revalued": [], "moved_plan": []}
    for e in doc["_entries"]:
        log["by_action"][e["action"]] = log["by_action"].get(e["action"], 0) + 1
        if e["action"] in (COMP, SHARED):
            continue
        b = by.get(e["line_id"])
        if e["action"] == NA:
            A3065._assert_na_bound(b, e)
        elif e["action"] == REVALUE or (e["action"] == "CONFIRM" and e["expect"]["class"] == "RELEASED"):
            _assert_released(b, e)
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
        elif e["action"] == REVALUE:
            log["revalued"].append(e["line_id"])
            if e.get("moves_to"):
                log["moved_plan"].append({"from": e["line_id"], "to": e["moves_to"]["line_id"],
                                          "plan_m2": e["moves_to"]["plan_m2"]})
        elif e["action"] != "VALUE":
            q = A30._qty(after)
            held = [{"what": e["member"], "why": (e.get("why_held") or "")[:300],
                     "range": [q["low"], q["high"]] if q["low"] is not None else None, "beside": e.get("beside")}]
        else:
            valued[e["line_id"]] = after
        changes.append(A305._change(P_CL, "CHANGE", b, after, drawing_reference="; ".join(s["file"] for s in srcs),
                                    held=held, downstream=[], verification=A3036._ver(srcs),
                                    evidence_status={"VALUE": "VERIFIED", REVALUE: "VERIFIED",
                                                     NA: "DRAWING-CONFIRMED"}.get(e["action"], "HELD"),
                                    codes=[P_CL], group=b["item_code"], step=e["action"]))
    for e in doc["_entries"]:
        if e["action"] not in (COMP, SHARED):
            continue
        srcs = [S[t] for t in e["source_tasks"]]
        if e["action"] == COMP:
            v = valued[e["companion_of"]]
            after = _new_line(prev, e, srcs, P_CL, {"companion": {"of": e["companion_of"],
                                                                  "value_m3": v["measured_net"]}, "shared": None},
                              f"companion of {e['companion_of']} (valued {_fmt(v['measured_net'])} m3 at the drawn "
                              "low end)")
        else:
            sh = {"by": list(e["shared_by"])}
            if e["add"]["item_code"] == LINTEL_CODE:
                byid = {ln["line_id"]: ln for ln in prev}
                sh["openings"] = [((byid[s]["calculation"].get("inputs") or {}).get(LINTEL_KEY) or {}).get(
                    "opening_id") for s in e["shared_by"]]
                if not all(sh["openings"]):
                    raise InputsError(f"{SHARED} {e['key']}: a sharer carries no V3.0.53 lintel record")
            after = _new_line(prev, e, srcs, P_SHARED, {"shared": sh, "companion": None},
                              f"remainder shared by {' / '.join(e['shared_by'])} (owned by one of them, not drawn)")
        changes.append(A305._change(P_SHARED if e["action"] == SHARED else P_CL, "ADD", None, after,
                                    drawing_reference="; ".join(s["file"] for s in srcs),
                                    held=[{"what": e["add"]["physical_element"], "why": e["why_held"][:300],
                                           "range": [e["after"]["low"], e["after"]["high"]], "beside": None}],
                                    downstream=[], verification=A3036._ver(srcs), evidence_status="HELD",
                                    codes=[P_SHARED if e["action"] == SHARED else P_CL], group=after["item_code"],
                                    step=e["action"]))
        log["added"] += 1
    log["lines"] = len(changes)
    return changes, log


# ================================================================================================ checks
def expected_totals(t0, changes):
    """as V3.0.65 (an ADD line counts once; a NOT_APPLICABLE line leaves its code's totals); a REVALUE line moves its
    code's released total by its delta"""
    return A3065.expected_totals(t0, changes)


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
        out[k] = {"base": t0.get(k), "v3_0_66": a}
    return out


def check_concrete(lines, before=None):
    """on finished lines: every V3.0.66 line is in the state its action names (as V3.0.65; REVALUE: was RELEASED,
    stays RELEASED at a positive value with the Checker re-measure and its old value kept; ADD_SHARED: new, BOUNDED
    0 .. x > 0, every sharer BOUNDED with no sharer's high below x); with `before`, no STR.CONC line went from held
    to released except a VALUE line. -> summary"""
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
        elif a == REVALUE:
            ok = ok and line_class(ln) == "RELEASED" and (ln.get("measured_net") or 0) > 0 and \
                bool(rec.get("remeasure")) and rec["was"]["class"] == "RELEASED" and \
                abs(ln["measured_net"] - rec["was"]["measured_net"] - rec["after"]["delta"]) <= BIND_TOL
        elif a == NA:
            ok = ok and ln["evidence_state"] == NA_STATE and ln.get("measured_net") is None and \
                not ln.get("bounded_range") and (rec.get("evidence") or {}).get("status") in EVIDENCE_STATUS and \
                rec["was"]["class"] == "HELD" and bool(ln.get("notes"))
        elif a == COMP:
            v = by.get((rec.get("companion") or {}).get("of"))
            ok = ok and r is not None and r[0] == 0.0 and r[1] > 0 and ln.get("measured_net") is None and \
                v is not None and v["evidence_state"] == VALUED and bool((ln.get("rfi") or {}).get("question"))
        elif a == SHARED:
            sh = [by.get(s) for s in (rec.get("shared") or {}).get("by") or ()]
            ok = ok and r is not None and r[0] == 0.0 and r[1] > 0 and ln.get("measured_net") is None and \
                len(sh) >= 2 and all(s is not None and A3063._range(s) is not None and
                                     s["item_code"] == ln["item_code"] for s in sh) and \
                bool((ln.get("rfi") or {}).get("question"))
        else:
            ok = ok and ln["evidence_state"] == BLANK and ln.get("measured_net") is None and r is None and \
                bool((ln.get("rfi") or {}).get("question")) and rec.get("beside") is not None
        if not ok:
            raise ValueError(f"{METHOD}: {ln['line_id']}: a {a} line is not in its state")
        if a in (COMP, SHARED) and ids is not None and ln["line_id"] in ids:
            raise ValueError(f"{METHOD}: {ln['line_id']}: an added line was already a candidate line")
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
            if line_class(o) == "RELEASED" and line_class(ln) == "RELEASED" and \
                    o.get("measured_net") != ln.get("measured_net") and rec.get("action") != REVALUE:
                raise ValueError(f"{METHOD}: {ln['line_id']}: a released concrete line moved without a re-derivation")
    return out


def _governed(ln):
    """R-T677-1 (q): a lintel line this version restated or added (the V3.0.53 check does not read it)"""
    return ln["item_code"] == LINTEL_CODE and bool(((ln.get("calculation") or {}).get("inputs") or {}).get(REC_KEY))


def check_lintels(lines):
    """R-T677-1 (q) on finished lines: one lintel line per opening over the V3.0.53 records and the records this
    version superseded; a restated lintel line carries its V3.0.53 HELD record under `superseded` (never a REQUIRED
    one) and no live V3.0.53 record; a shared remainder names the openings of its sharers. -> summary"""
    ops, out = {}, {"restated": 0, "shared": 0, "v3_0_53": 0}
    by = {ln["line_id"]: ln for ln in lines}
    for ln in lines:
        if ln["item_code"] != LINTEL_CODE:
            continue
        inp = (ln.get("calculation") or {}).get("inputs") or {}
        rec = inp.get(REC_KEY)
        if not rec:
            o = (inp.get(LINTEL_KEY) or {}).get("opening_id")
            out["v3_0_53"] += 1
        elif rec["action"] == SHARED:
            sh = rec.get("shared") or {}
            want = [(((by.get(s) or {}).get("calculation") or {}).get("inputs") or {}).get(REC_KEY) or {}
                    for s in sh.get("by") or ()]
            got = [((w.get("superseded") or {}).get(LINTEL_KEY) or {}).get("opening_id") for w in want]
            if inp.get(LINTEL_KEY) or not got or got != sh.get("openings"):
                raise ValueError(f"{METHOD}: {ln['line_id']}: a shared lintel remainder does not name its sharers' "
                                 f"openings")
            out["shared"] += 1
            continue
        else:
            lr = (rec.get("superseded") or {}).get(LINTEL_KEY) or {}
            if inp.get(LINTEL_KEY) or lr.get("decision") != "HELD":
                raise ValueError(f"{METHOD}: {ln['line_id']}: a restated lintel line keeps its V3.0.53 HELD record "
                                 f"under superseded only")
            o = lr.get("opening_id")
            out["restated"] += 1
        if not o or o in ops:
            raise ValueError(f"{METHOD}: lintel opening {o!r} has no record or two lintel lines")
        ops[o] = ln["line_id"]
    return out


# ================================================================================================ integrate / write
def integrate(prev, changes, for_lead=()):
    """-> (V3.0.66 lines, identity). Changed lines replace their candidate line in place; added lines follow; every
    other candidate line is byte-identical (asserted); the earlier versions' checks re-run on the result: the V3.0.63
    chain (V3.0.10 .. V3.0.63), the V3.0.64 and V3.0.65 state checks, each WITHOUT these lines as their own base (the
    T-671 lesson: an earlier version's added line is in the base by now, by design)."""
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
    view = [ln for ln in out if not _governed(ln)]              # R-T677-1 (q)
    _o, i63 = A3063.integrate(view, [], for_lead)
    i63 = {k: v for k, v in i63.items() if k not in (
        "base_lines", "v3_0_63_lines", "v3_0_63_rows", "replaced", "added", "outside_rows",
        "outside_rows_identical_to_base", "outside_rows_sha256")}
    i65 = {"checks_v3_0_63": i63, "concrete_v3_0_64": A3064.check_concrete(out),
           "concrete_v3_0_65": A3065.check_concrete(out), "governed_lintels_outside_v3_0_53": len(out) - len(view)}
    ident = {"base_lines": len(prev), "v3_0_66_lines": len(out), "v3_0_66_rows": len(changes), "replaced": len(repl),
             "added": len(adds), "checks_v3_0_65": i65, "concrete": check_concrete(out, prev),
             "lintels": check_lintels(out)}
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
                     "after_v3_0_66": A30._qty(ref),
                     "class": [rec["was"]["class"] if rec.get("was") else "NEW", line_class(ref)],
                     "evidence_status": c.get("evidence_status"), "still_held": c.get("held"),
                     "beside": rec.get("beside"), "evidence": rec.get("evidence"), "companion": rec.get("companion"),
                     "shared": rec.get("shared"), "moves_to": rec.get("moves_to"),
                     "set_aside": rec.get("set_aside"), "remeasure": rec.get("remeasure"),
                     "superseded_record_keys": sorted(rec.get("superseded") or {}),
                     "release_status": "RELEASED (re-derived)" if c.get("step") == REVALUE else "NOT RELEASED",
                     "basis": rec["basis"],
                     "owner_manual_method": PIECES[c["piece"]]["owner_manual_method"],
                     "drawing_derived_method": PIECES[c["piece"]]["drawing_method"],
                     "verification": c.get("verification") or {}, "rollback": ROLLBACK})
    return rows


LEDGER_CSV = ("version", "piece", "action", "line_id", "item_code", "floor", "member", "element_id", "unit", "v2_9",
              "base", "v3_0_66", "class", "beside", "evidence_status", "verification")
DIFF_CSV = ("line_id", "item_code", "floor", "element_id", "unit", "vs_base", "vs_released_v2_9", "v2_9", "base",
            "v3_0_66")


def ledger_csv(rows):
    def q(x):
        return A302._q(x) if x and (x.get("value") is not None or x.get("low") is not None or x.get("state")) else ""

    def bs(r):
        t = [A3063._beside_text(r["beside"])] if r.get("beside") else []
        if r.get("evidence"):
            t.append(f"{r['evidence']['status']}: {r['evidence']['reading']}"[:200])
        if r.get("companion"):
            t.append(f"companion of {r['companion']['of']}")
        if r.get("shared"):
            t.append(f"remainder shared by {' / '.join(r['shared']['by'])}")
        if r.get("moves_to"):
            t.append(f"{r['moves_to']['plan_m2']} m2 moves to {r['moves_to']['line_id']}")
        return "; ".join(t)
    return A305._csv([{"version": r["version"], "piece": r["piece"], "action": r["action"], "line_id": r["line_id"],
                       "item_code": r["item_code"], "floor": r.get("floor") or "", "member": r.get("member") or "",
                       "element_id": r.get("element_id") or "", "unit": r["unit"],
                       "v2_9": q(r.get("before_released_v2_9")), "base": q(r.get("before_base")),
                       "v3_0_66": q(r.get("after_v3_0_66")), "class": " -> ".join(r["class"]), "beside": bs(r),
                       "evidence_status": r["evidence_status"],
                       "verification": f"{r['verification'].get('task')} "
                                       f"{' '.join(x[:8] for x in r['verification'].get('merge_commits') or ())}"}
                      for r in rows], LEDGER_CSV)


def diff_rows(prev, new, released_lines=None):
    return [dict({k: v for k, v in d.items() if k != "v3_0_65"}, v3_0_66=d["v3_0_65"])
            for d in A3065.diff_rows(prev, new, released_lines)]


def write(out, prev, changes, log, released_lines=None, for_lead=(), expect_totals=None):
    """the V3_0_66_* files beside the base candidate's files. -> (file names, identity, ledger)."""
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
    ident = dict(ident, diff=dsum, confirmed=len(conf), not_applicable=len(log.get("not_applicable") or ()),
                 revalued=len(log.get("revalued") or ()), moved_plan=log.get("moved_plan") or [])
    moved = check_totals(A304.code_totals(prev), A304.code_totals(new), changes, expect_totals)
    led = {"schema": LEDGER_SCHEMA, "method": METHOD, "extends": EXTENDS, "candidate": CANDIDATE,
           "base": A30.BASE_METHOD, "released": A30.RELEASED_METHOD, "released_default": False, "rows": rows,
           "confirmed_unchanged": sorted(conf), "waiting_pieces": WAITING, "integration_package": True}
    run = {"method": METHOD, "policy": POLICY_ID, "extends": EXTENDS, "candidate": CANDIDATE,
           "base_method": A30.BASE_METHOD, "released_method": A30.RELEASED_METHOD, "released_default": False,
           "rollback": ROLLBACK, "identity": ident, "pieces": PIECES, "piece_logs": [log],
           "totals_moved_by_code": moved, "waiting_pieces": WAITING}
    files = {"V3_0_66_BOQ_LINES.json": BL.dumps(new),
             "V3_0_66_BOQ_LINES.csv": A30._lines_csv(new),
             "V3_0_66_INTEGRATION_LEDGER.json": A30._j(led),
             "V3_0_66_INTEGRATION_LEDGER.csv": ledger_csv(rows),
             "V3_0_66_DIFF.csv": A305._csv(diff, DIFF_CSV),
             "V3_0_66_RUN.json": A30._j(run)}
    for name, text in files.items():
        (out / name).write_text(text, encoding="utf-8")
    return sorted(files), ident, led


def policy_record():
    return {"method": METHOD, "extends": EXTENDS, "pieces": sorted(PIECES), "inputs_schema": INPUTS_SCHEMA,
            "released_default": False, "rollback": ROLLBACK, "actions": list(ACTIONS)}


__all__ = ["METHOD", "PIECES", "WAITING", "DEFAULT_GUARD_CLASS", "INPUTS_SCHEMA", "load_inputs", "changes_for",
           "check_concrete", "check_totals", "expected_totals", "integrate", "ledger_rows", "diff_rows", "write",
           "InputsError", "line_class"]
