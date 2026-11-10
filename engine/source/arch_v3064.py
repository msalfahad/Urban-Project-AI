"""ARCH_TAKEOFF_V3.0.64 (T-668, lane I, CONCRETE GATE B ROUND 3 integration package): the SAME opt-in BOQ candidate
as ARCH_TAKEOFF_V3.0 .. V3.0.63 (engine.source.arch_v30, arch_v301 .. arch_v3063), extended with ONE piece built from
Checker-merged research ledgers of the B10 concrete families (STR.CONC.*, m3) not wired by V3.0.63: junction-square
ownership of five beam pieces and of the annex ground-beam corner, the boundary band under the building stretches and
the pool blinding:

  CONC_LEDGER   a named concrete line is restated as its merged ledger states it, with the V3.0.63 actions and
                states unchanged (BOUND, VALUE, HELD_BLANK, LOWER_ONLY, UPPER_ONLY, CONFIRM; engine.source.arch_v3063,
                R-T665-1 (a) .. (g) re-used as written); a BOUND may carry the exposures a drawn junction leaves
                open BESIDE it (each 0 .. x m3, named, never in the range); a BOUND, a LOWER_ONLY floor or a
                CONFIRM may name the owner of every junction square it touches (one owner per square, R-T666-1 /
                R-T669-1);
  CONC_ADD      a printed concrete element carried by NO candidate line becomes ONE new line (new in V3.0.64):
                  ADD_LOWER_ONLY  HELD blank (BLOCKED_RFI) with the drawn AT_LEAST m3 figure beside, never a range,
                                  never 0; the line names every candidate line whose plan it shares and the shared
                                  area netted out of the figure (one element once), each binding asserted.

R-T668-1 (every villa; = R-T665-1 + the two additions, ERS s.2-5, UP-QTY-STATUS-001, WORKFLOW CONTROLS s.1 / s.5):
(a) .. (g) as R-T665-1 (bind to the candidate line, STR.CONC.* m3 only, each line once, a bound leaves only with its
replacement, everything not named byte-identical, totals move only by the restatement, a released line only to HELD
under its applied downgrade); (h) an exposure beside a BOUND is 0 .. x with x > 0 and a reason, and never enters the
range; a junction square is owned by exactly one named owner (a line id, or a column / through member named by its
line); (i) an ADD line is new (its id and its (code, element) carried by no candidate line), HELD, blank, with its
AT_LEAST figure beside; every candidate line it nets against is bound (class and released value or range asserted)
and the netted area is stated; the new line adds exactly one blocked line to its code's totals and nothing else.
Files: V3_0_64_BOQ_LINES.json / .csv, V3_0_64_INTEGRATION_LEDGER.json / .csv, V3_0_64_DIFF.csv, V3_0_64_RUN.json.
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

DEFAULT_GUARD_CLASS = "TOOLING"          # T-212: re-books Checker-merged member ledgers onto candidate lines
METHOD = "ARCH_TAKEOFF_V3.0.64"
EXTENDS = A3063.METHOD
CANDIDATE = A30.METHOD
POLICY_ID = "URBAN_BOQ_T668_ARCH_V3_0_64"
INPUTS_SCHEMA = "URBAN_V3064_INPUTS_V1"
LEDGER_SCHEMA = "URBAN_V3064_INTEGRATION_LEDGER_V1"
ROLLBACK = A30.ROLLBACK
InputsError = A3063.InputsError
_r = A3063._r
_fmt = A3063._fmt
RULE_ID, RULE_VERSION = "R-T668-1", "T-668"
REC_KEY = "concrete_ledger_v3064"
P_CL, P_ADD = "CONC_LEDGER", "CONC_ADD"
ADD = "ADD_LOWER_ONLY"
ACTIONS = A3063.ACTIONS + (ADD,)
CHANGING = A3063.CHANGING
BLANK_ACTIONS = A3063.BLANK_ACTIONS
CODE_PREFIX, UNIT = A3063.CODE_PREFIX, A3063.UNIT
BOUNDED, BLANK, VALUED = A3063.BOUNDED, A3063.BLANK, A3063.VALUED
TOT_TOL, BIND_TOL, MAX_Q = A3063.TOT_TOL, A3063.BIND_TOL, A3063.MAX_Q
OWNER_KINDS = ("PIECE", "COLUMN", "THROUGH", "LINE")
line_class = A3063.line_class

PIECES = {
    P_CL: {"module": "engine/source/arch_v3064.py (named B10 beam-piece and boundary-band lines restated from the "
                     "Checker-merged T-666 / T-659 ledgers: drawn lengths, junction-square owners, the drawn band "
                     "bound; nothing else moves)",
           "policy": "CONCRETE_GATE_B_V3", "rule_id": "R-T666-1 / R-T666-2 / R-T659-3 (R-T668-1)",
           "owner_rules": ["UP-CONC-JOINT-001 (a column owns its junction to the slab top)",
                           "Q-28 A (boundary band, owner provisional reading kept beside)",
                           "UP-QTY-STATUS-001 (held is blank or bounded, never 0)", "ERS s.2-5 (drawn element first)"],
           "owner_manual_method": "beam pieces at the face-to-face length the route G net plan gives x one section; "
                                  "the boundary wall base at one section (B.W 20x60) over its run",
           "drawing_method": "the merged T-666 ledger: each unlabelled piece at its drawn edge length (DXF), one owner "
                             "per 0.20 x 0.20 junction square (column to slab top, else the piece that draws it), the "
                             "open depth exposures beside; the band at the T-659 bound (typical 0.20 x 0.40 on the run "
                             "free of footings .. B.W 0.20 x 0.60 on the whole closed run), drawn under every building "
                             "stretch at a disjoint level (T-666 R-T666-2: owned once, nothing removed)"},
    P_ADD: {"module": "engine/source/arch_v3064.py (a printed concrete element carried by no candidate line added "
                      "HELD blank with its drawn floor beside, netted against the lines that share its plan)",
            "policy": "CONCRETE_GATE_B_V3", "rule_id": "R-T667-1..5 (R-T668-1 (i))",
            "owner_rules": ["Q-26 A (flat pool floor at the printed depth; the detail's slope not used)",
                            "UP-QTY-STATUS-001", "ERS s.2.4 (one physical element once)"],
            "owner_manual_method": "pool blinding as one plate (outline x 0.10) or not at all (the freelancer carries "
                                   "a plot plate, no pool row)",
            "drawing_method": "the merged T-667 ledger: the pool base outline grown by the printed 5 + 5 cm wrap, "
                              "inside the plot line, net of the VERIFIED pit blinding layer it shares in plan, x the "
                              "printed 0.10: an AT_LEAST floor (the projection beyond the wrap is not dimensioned, "
                              "the founding levels under the pool are not printed)"},
}
WAITING = {k: v for k, v in A3063.WAITING.items()
           if k not in ("T665_JUNCTION_OWNERSHIP", "T665_POOL_BLINDING_WIRING")}          # wired here
WAITING.update({
    "T668_ROOF_COLUMN_LOWER_ENDS": "T-669 (b) (R-T669-2: the 2F roof-column lower ends from the W26 apex + slab "
                                   "thickness) is not this row's: the upper-only column lines keep their V3.0.63 "
                                   "state; a lane I row wires them",
    "T668_POOL_STEPS": "pool steps stay HELD blank (no step drawn or dimensioned: designer item); confirmed, not "
                       "valued (the freelancer's 0.228 m3 is his size, RULE_DIFFERENCE)",
    "T668_POOL_BEYOND_PLOT": "the pool's own blinding strip beyond the plot line (0.037 m3) is beside the new line "
                             "under D-14, not in any line (existence open)",
})


# ================================================================================================ inputs
def _num(x, where, top=MAX_Q, zero=False):
    return A3063._num(x, where, top, zero)


def _exposures(e, w):
    out = []
    for x in e.get("exposures_beside") or ():
        if not x.get("what") or not x.get("why"):
            raise InputsError(f"{w}: an exposure beside names what and why")
        lo, hi = _num(x.get("low"), f"{w} exposure low", zero=True), _num(x.get("high"), f"{w} exposure high")
        if lo != 0.0:
            raise InputsError(f"{w}: an exposure beside runs from 0 (it may not exist), never a floor in the range")
        out.append(dict(x, low=lo, high=hi))
    return out


def _squares(e, w):
    seen = set()
    for s in e.get("squares") or ():
        if not s.get("square") or not s.get("owner") or s.get("owner_kind") not in OWNER_KINDS:
            raise InputsError(f"{w}: a junction square names itself, its one owner and the owner kind {OWNER_KINDS}")
        if s["square"] in seen:
            raise InputsError(f"{w}: square {s['square']} named twice (one owner per square)")
        seen.add(s["square"])
        if s["owner_kind"] == "PIECE" and s["owner"] != e["line_id"]:
            raise InputsError(f"{w}: a PIECE square is owned by this line")
    return list(e.get("squares") or ())


def _add_entry(e, srcs):
    w = f"{ADD} {e.get('key')}"
    A3043._tasks(e, srcs, w)
    A3063._need(e, ("key", "add", "template_line", "basis", "why_held", "question", "beside"), w)
    x = e["add"]
    A3063._need(x, ("item_code", "unit", "element_id", "physical_element"), w)
    if not str(x["item_code"]).startswith(CODE_PREFIX) or x["unit"] != UNIT:
        raise InputsError(f"{w}: {x['item_code']} {x['unit']} is not a code this version may add (STR.CONC.* m3)")
    b = A3063._beside(e["beside"], w, need=True)
    if b["kind"] != "AT_LEAST_M3":
        raise InputsError(f"{w}: an added lower-only line carries its AT_LEAST m3 figure beside")
    for n in e.get("netted_against") or ():
        A3063._need(n, ("line_id", "item_code", "class", "overlap_m2", "why"), f"{w} netted")
        _num(n["overlap_m2"], f"{w} netted overlap", top=1000.0)
    if not e.get("netted_against"):
        raise InputsError(f"{w}: an added concrete element names the lines whose plan it shares (or says none)")
    if e.get("after") or e.get("value") is not None:
        raise InputsError(f"{w}: an added held line carries no quantity (blank, the figure beside)")
    return dict(e, action=ADD)


def load_inputs(doc, project_id=None):
    """URBAN_V3064_INPUTS_V1 -> the validated doc.
    {"schema", "project_id", "sources": [{"task", "file", "sha256", "merge_commit", "checker_run"}],
     "expect_totals": {"<code>|m3": {...}} (optional, asserted on the code totals),
     "entries": [V3.0.63 entry (+ "exposures_beside" [{what, low 0, high, why}], "squares" [{square, owner,
                 owner_kind}]) | {"action": "ADD_LOWER_ONLY", "key", "source_tasks", "template_line", "add"
                 {item_code, unit, element_id, floor, physical_element}, "basis", "why_held", "question",
                 "beside" {kind AT_LEAST_M3, value, basis}, "beside_also" [...], "netted_against" [{line_id,
                 item_code, class, value | low / high, overlap_m2, why}]}]}"""
    if not doc:
        return None
    if doc.get("schema") != INPUTS_SCHEMA:
        raise InputsError(f"project inputs: schema must be {INPUTS_SCHEMA}")
    if project_id and doc.get("project_id") not in (None, project_id):
        raise InputsError(f"project inputs are for {doc.get('project_id')!r}, the run is {project_id!r}")
    srcs = A3043._sources(doc)
    ents = []
    for x in doc.get("entries") or ():
        if x.get("action") == ADD:
            ents.append(_add_entry(x, srcs))
            continue
        e = A3063._entry(x, srcs)
        w = f"{e['action']} {e['line_id']}"
        if e.get("exposures_beside") and e["action"] != "BOUND":
            raise InputsError(f"{w}: exposures beside go with a bound")
        if e.get("squares") and e["action"] not in ("BOUND", "LOWER_ONLY", "CONFIRM"):
            raise InputsError(f"{w}: junction squares go with a bound, a lower-only floor or a confirmed line")
        e["exposures_beside"] = _exposures(e, w)
        top = (e.get("after") or {}).get("high")
        if top is not None and any(x["high"] > top for x in e["exposures_beside"]):
            raise InputsError(f"{w}: an exposure beside larger than the line's own high (unit slip)")
        e["squares"] = _squares(e, w)
        ents.append(e)
    if not ents:
        raise InputsError("no entry in the inputs")
    owners = {}
    for e in ents:                                       # R-T668-1 (h): one owner per junction square, across lines
        for s in e.get("squares") or ():
            owners.setdefault(s.get("junction") or f"{e['line_id']}:{s['square']}", set()).add(
                s.get("owner_line") or s["owner"])
    two = sorted(j for j, o in owners.items() if len(o) > 1)
    if two:
        raise InputsError(f"junction square(s) {two} claimed by two owners (one owner per square)")
    seen = set()
    for e in ents:
        k = e.get("line_id") or f"ADD:{e['key']}"
        if k in seen:
            raise InputsError(f"{k}: named twice (one line, one restatement)")
        seen.add(k)
    if any(e.get("downgrade") for e in ents):
        A3063.load_inputs(dict(doc, schema=A3063.INPUTS_SCHEMA,
                               entries=[x for x in doc["entries"] if x.get("action") != ADD]), project_id)
    return dict(doc, _sources=srcs, _entries=ents)


# ================================================================================================ lines
def _rec(srcs, piece=P_CL, **kw):
    return dict({"piece": piece, "policy": PIECES[piece]["policy"], "tasks": [s["task"] for s in srcs],
                 "ledgers": [s["file"] for s in srcs], "ledger_sha256": [s["sha256"] for s in srcs],
                 "merge_commits": [s["merge_commit"] for s in srcs], "checker_runs": [s["checker_run"] for s in srcs],
                 "rule_id": RULE_ID, "rule_version": RULE_VERSION, "release_status": "NOT RELEASED"}, **kw)


def _exp_text(xs):
    return "; ".join(f"beside, not in the range: {x['what']} 0 .. {_fmt(x['high'])} m3" for x in xs)


def _restate(b, e, srcs):
    """the V3.0.63 restatement of one line, recorded under this version (method, rule, record key)"""
    a, af = e["action"], e.get("after") or {}
    ln = copy.deepcopy(b)
    was = {"evidence_state": b["evidence_state"], "measured_net": b.get("measured_net"), "gross": b.get("gross"),
           "bounded_range": b.get("bounded_range"), "rfi": b.get("rfi"),
           "formula": (b.get("calculation") or {}).get("formula"), "class": line_class(b)}
    ex = e.get("exposures_beside") or []
    if a == "BOUND":
        lo, hi = float(af["low"]), float(af["high"])
        ln["evidence_state"], ln["measured_net"], ln["gross"] = BOUNDED, None, None
        ln["bounded_range"] = {"low": _r(lo), "high": _r(hi), "basis": f"{e['member']}: {e['basis']}"[:200]}
        ln["rfi"] = {"question": e["question"][:400], "blocks": [b["line_id"]]}
        head = f"HELD (BOUNDED) {_fmt(lo)} .. {_fmt(hi)} m3" + (f"; {_exp_text(ex)}" if ex else "")
        after = {"low": _r(lo), "high": _r(hi)}
    elif a == "VALUE":
        v = float(af["value"])
        ln["evidence_state"], ln["measured_net"], ln["gross"] = VALUED, _r(v), _r(v)
        ln["bounded_range"], ln["rfi"] = None, None
        head = f"VALUED AS DRAWN {_fmt(v)} m3 (Checker re-measure: {e['remeasure']})"[:400]
        after = {"value": _r(v)}
    else:
        ln["evidence_state"], ln["measured_net"], ln["gross"], ln["bounded_range"] = BLANK, None, None, None
        ln["rfi"] = {"question": e["question"][:400], "blocks": [b["line_id"]]}
        head = {"LOWER_ONLY": "HELD, LOWER END ONLY (blank)", "UPPER_ONLY": "HELD, UPPER END ONLY (blank)",
                "HELD_BLANK": "HELD BLANK"}[a] + "; " + A3063._beside_text(e["beside"])
        after = {"beside": e["beside"]}
    ln["deductions"], ln["additions"] = [], []
    ln["calculation"] = dict(ln["calculation"], formula=(
        f"{METHOD}: {head} = {e['member']}: {e['basis']}" + (f"; {e['why_held']}" if e.get("why_held") else ""))[:1500])
    inp = ln["calculation"]["inputs"] = dict(ln["calculation"].get("inputs") or {})
    inp[REC_KEY] = _rec(srcs, action=a, member=e["member"], was=was, after=after, basis=e["basis"],
                        why_held=(e.get("why_held") or "")[:600], beside=e.get("beside"), exposures_beside=ex,
                        squares=e.get("squares") or [], set_aside=e.get("set_aside"), remeasure=e.get("remeasure"),
                        downgrade=e.get("downgrade"), freelancer_beside=e.get("freelancer_beside"))
    A305._note(ln, f"{METHOD}: {head[:200]} (was {A302._q(A30._qty(b))}); NOT RELEASED")
    return A3063._fin(ln)


def _bind_net(n, by, w):
    """a line the added element shares plan with: present, of its code and class, at its value / range"""
    b = by.get(n["line_id"])
    if b is None or b["item_code"] != n["item_code"] or line_class(b) != n["class"]:
        raise InputsError(f"{w}: netted line {n['line_id']} is not the candidate's {n['item_code']} {n['class']}")
    q = A30._qty(b)
    for k in ("value", "low", "high"):
        if n.get(k) is not None and (q[k] is None or abs(q[k] - float(n[k])) > BIND_TOL):
            raise InputsError(f"{w}: netted line {n['line_id']} {k} {q[k]} is not the ledger's {n[k]} (stale)")


def _added(prev, e, srcs):
    from engine.source import boq_line as BL
    by = {ln["line_id"]: ln for ln in prev}
    w = f"{ADD} {e['key']}"
    tpl = by.get(e["template_line"])
    x = e["add"]
    if tpl is None or tpl["item_code"] != x["item_code"] or tpl["unit"] != x["unit"]:
        raise InputsError(f"{w}: template line {e['template_line']} is not a candidate {x['item_code']} line")
    if any(ln["item_code"] == x["item_code"] and (ln.get("location") or {}).get("element_id") == x["element_id"]
           for ln in prev):
        raise InputsError(f"{w}: {x['item_code']} {x['element_id']} is already carried by a candidate line")
    for n in e["netted_against"]:
        _bind_net(n, by, w)
    b = e["beside"]
    net = "; ".join(f"netted against {n['line_id']} {n['item_code']} ({n['class']}): {_fmt(n['overlap_m2'])} m2 "
                    f"shared plan ({n['why']})" for n in e["netted_against"])
    also = "; ".join(f"{y['what']} {y['m3']} m3 ({y['status']})" for y in e.get("beside_also") or ())
    formula = (f"{METHOD}: HELD, LOWER END ONLY (blank, never 0) {x['physical_element']}: "
               f"{A3063._beside_text(b)}; {e['basis']}; {net}; held by: {e['why_held']}"
               + (f"; also beside, not in the line: {also}" if also else "") + " (R-T668-1 (i))")[:1500]
    rec = _rec(srcs, P_ADD, action=ADD, key=e["key"], member=x["physical_element"], was=None,
               after={"beside": b}, basis=e["basis"], why_held=e["why_held"][:600], beside=b,
               beside_also=e.get("beside_also") or [], netted_against=e["netted_against"],
               template_line=e["template_line"], exposures_beside=[], squares=[], set_aside=None, remeasure=None,
               downgrade=None, freelancer_beside=e.get("freelancer_beside"))
    ln = BL.make_line(
        project_id=tpl["project"]["project_id"], revision_set_sha256=tpl["project"]["revision_set_sha256"],
        item_code=x["item_code"], unit=x["unit"], evidence_state=BLANK, measured_net=None, gross=None,
        element_id=x["element_id"], floor=x.get("floor"), physical_element=x["physical_element"], formula=formula,
        inputs={REC_KEY: rec, "evidence_status": "HELD"}, documents=copy.deepcopy(tpl["source"]["documents"]),
        geometry_source=tpl["source"]["geometry_source"], geometry_confidence=tpl["source"]["geometry_confidence"],
        rule_id=RULE_ID, rule_version=RULE_VERSION, material_state=tpl.get("material_state") or "SOURCE",
        rfi={"question": e["question"][:900], "unlocks": x["element_id"]},
        notes=f"{METHOD}: printed concrete element carried by no candidate line, added HELD (lower end only, "
              f"blank); NOT RELEASED",
        item_en=tpl["item_en"], item_ar=tpl["item_ar"], trade=tpl["trade"], subtrade=tpl.get("subtrade"))
    if ln["line_id"] in by:
        raise InputsError(f"{w}: the new line id {ln['line_id']} is a candidate id")
    ln["project"] = copy.deepcopy(ln["project"])
    return BL.validate(ln)


def changes_for(doc, prev):
    """-> (changes, log). CONFIRM entries are asserted on the candidate line and change nothing."""
    if not doc:
        return [], {"piece": "T668", "state": "NO_PROJECT_INPUT"}
    if any(((ln.get("calculation") or {}).get("inputs") or {}).get(REC_KEY) for ln in prev):
        raise InputsError("the candidate already carries V3.0.64 records (applied once)")
    by = {ln["line_id"]: ln for ln in prev}
    S = doc["_sources"]
    changes = []
    log = {"piece": "T668", "state": "RUN", "sources": doc["sources"], "by_action": {}, "lines": 0, "added": 0,
           "confirmed": [], "downgrades_materialised": A3063.assert_downgrades(doc, prev)}
    for e in doc["_entries"]:
        log["by_action"][e["action"]] = log["by_action"].get(e["action"], 0) + 1
        srcs = [S[t] for t in e["source_tasks"]]
        if e["action"] == ADD:
            after = _added(prev, e, srcs)
            changes.append(A305._change(P_ADD, "ADD", None, after, drawing_reference="; ".join(s["file"] for s in srcs),
                                        held=[{"what": e["add"]["physical_element"], "why": e["why_held"][:300],
                                               "range": None, "beside": e["beside"]}],
                                        downstream=[], verification=A3036._ver(srcs), evidence_status="HELD",
                                        codes=[P_ADD], group=after["item_code"], step=ADD))
            log["added"] += 1
            continue
        b = by.get(e["line_id"])
        A3063._assert_bound(b, e)
        for s in e.get("squares") or ():                # R-T668-1 (h): a named owner line is a candidate line
            o = s.get("owner_line")
            if o is not None and (o not in by or not by[o]["item_code"].startswith(CODE_PREFIX)):
                raise InputsError(f"{e['line_id']}: square {s['square']} owner {o} is not a candidate concrete line")
        if e["action"] == "CONFIRM":
            log["confirmed"].append(e["line_id"])
            continue
        after = _restate(b, e, srcs)
        held = None
        if e["action"] != "VALUE":
            q = A30._qty(after)
            held = [{"what": e["member"], "why": (e.get("why_held") or "")[:300],
                     "range": [q["low"], q["high"]] if q["low"] is not None else None,
                     "beside": e.get("beside"), "exposures_beside": e.get("exposures_beside") or []}]
        changes.append(A305._change(P_CL, "CHANGE", b, after, drawing_reference="; ".join(s["file"] for s in srcs),
                                    held=held, downstream=[], verification=A3036._ver(srcs),
                                    evidence_status="VERIFIED" if e["action"] == "VALUE" else "HELD",
                                    codes=[P_CL], group=b["item_code"], step=e["action"]))
    log["lines"] = len(changes)
    return changes, log


# ================================================================================================ checks
def _bucket(ln):
    return A3063._bucket(ln)


def expected_totals(t0, changes):
    """the STR.CONC.*|m3 code totals the restatement must give, from the base totals and the changes alone (an ADD
    line counts once, as one blocked line)"""
    zero = {"lines": 0, "released": 0.0, "held_low": 0.0, "held_high": 0.0, "bounded_lines": 0, "blocked_lines": 0}
    want = {}
    for c in changes:
        k = f"{c['after']['item_code']}|{c['after']['unit']}"
        z = want.setdefault(k, dict(t0.get(k) or zero))
        pairs = ((c["after"], 1),) if c["before"] is None else ((c["before"], -1), (c["after"], 1))
        if c["before"] is None:
            z["lines"] += 1
        for ln, s in pairs:
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
        out[k] = {"base": t0.get(k), "v3_0_64": a}
    return out


def check_concrete(lines, before=None):
    """on finished lines: every V3.0.64 line is in the state its action names (as V3.0.63, + an ADD line HELD blank
    with its AT_LEAST beside, absent from `before`); a BOUND's exposures stay beside (0 .. x, never in the range);
    with `before`, no STR.CONC line went from held to released except a VALUE line. -> summary"""
    out = {a: 0 for a in CHANGING + (ADD,)}
    ids = {ln["line_id"] for ln in before} if before is not None else None
    for ln in lines:
        rec = ((ln.get("calculation") or {}).get("inputs") or {}).get(REC_KEY)
        if not rec:
            continue
        a = rec["action"]
        r = A3063._range(ln)
        ok = ln["item_code"].startswith(CODE_PREFIX) and ln["unit"] == UNIT
        if a == "BOUND":
            ok = ok and r is not None and 0 < r[0] <= r[1] + 1e-9 and ln.get("measured_net") is None and \
                bool((ln.get("rfi") or {}).get("question")) and \
                all(x["low"] == 0.0 and x["high"] > 0 for x in rec.get("exposures_beside") or ())
        elif a == "VALUE":
            ok = ok and ln["evidence_state"] == VALUED and (ln.get("measured_net") or 0) > 0 and rec.get("remeasure")
        elif a == ADD:
            ok = ok and ln["evidence_state"] == BLANK and ln.get("measured_net") is None and r is None and \
                ln.get("gross") is None and not ln.get("bounded_range") and \
                (rec.get("beside") or {}).get("kind") == "AT_LEAST_M3" and bool((ln.get("rfi") or {}).get("question"))
            if ok and ids is not None and ln["line_id"] in ids:
                raise ValueError(f"{METHOD}: {ln['line_id']}: an added line was already a candidate line")
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
    """-> (V3.0.64 lines, identity). Changed lines replace their candidate line in place; added lines follow; every
    other candidate line is byte-identical (asserted); the earlier versions' checks re-run on the result (the V3.0.63
    set, which re-runs V3.0.10 .. V3.0.62)."""
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
    _o, i63 = A3063.integrate(out, [], for_lead)     # every V3.0.10 .. V3.0.63 family check, re-run on these lines
    ident = {"base_lines": len(prev), "v3_0_64_lines": len(out), "v3_0_64_rows": len(changes), "replaced": len(repl),
             "added": len(adds), "checks_v3_0_63": {k: v for k, v in i63.items() if k not in (
                 "base_lines", "v3_0_63_lines", "v3_0_63_rows", "replaced", "added", "outside_rows",
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
                     "after_v3_0_64": A30._qty(ref),
                     "class": [rec["was"]["class"] if rec.get("was") else "NEW", line_class(ref)],
                     "evidence_status": c.get("evidence_status"), "still_held": c.get("held"),
                     "beside": rec.get("beside"), "exposures_beside": rec.get("exposures_beside") or [],
                     "squares": rec.get("squares") or [], "netted_against": rec.get("netted_against"),
                     "set_aside": rec.get("set_aside"), "remeasure": rec.get("remeasure"),
                     "release_status": "NOT RELEASED", "basis": rec["basis"],
                     "owner_manual_method": PIECES[c["piece"]]["owner_manual_method"],
                     "drawing_derived_method": PIECES[c["piece"]]["drawing_method"],
                     "verification": c.get("verification") or {}, "rollback": ROLLBACK})
    return rows


LEDGER_CSV = ("version", "piece", "action", "line_id", "item_code", "floor", "member", "element_id", "unit", "v2_9",
              "base", "v3_0_64", "class", "beside", "evidence_status", "verification")
DIFF_CSV = ("line_id", "item_code", "floor", "element_id", "unit", "vs_base", "vs_released_v2_9", "v2_9", "base",
            "v3_0_64")


def ledger_csv(rows):
    def q(x):
        return A302._q(x) if x and (x.get("value") is not None or x.get("low") is not None or x.get("state")) else ""

    def bs(r):
        t = [A3063._beside_text(r["beside"])] if r.get("beside") else []
        t += [f"0 .. {_fmt(x['high'])} m3 {x['what']}" for x in r.get("exposures_beside") or ()]
        return "; ".join(t)
    return A305._csv([{"version": r["version"], "piece": r["piece"], "action": r["action"], "line_id": r["line_id"],
                       "item_code": r["item_code"], "floor": r.get("floor") or "", "member": r.get("member") or "",
                       "element_id": r.get("element_id") or "", "unit": r["unit"],
                       "v2_9": q(r.get("before_released_v2_9")), "base": q(r.get("before_base")),
                       "v3_0_64": q(r.get("after_v3_0_64")), "class": " -> ".join(r["class"]), "beside": bs(r),
                       "evidence_status": r["evidence_status"],
                       "verification": f"{r['verification'].get('task')} "
                                       f"{' '.join(x[:8] for x in r['verification'].get('merge_commits') or ())}"}
                      for r in rows], LEDGER_CSV)


def diff_rows(prev, new, released_lines=None):
    return [dict({k: v for k, v in d.items() if k != "v3_0_63"}, v3_0_64=d["v3_0_63"])
            for d in A3063.diff_rows(prev, new, released_lines)]


def write(out, prev, changes, log, released_lines=None, for_lead=(), expect_totals=None):
    """the V3_0_64_* files beside the base candidate's files. -> (file names, identity, ledger)."""
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
    ident = dict(ident, diff=dsum, confirmed=len(conf))
    moved = check_totals(A304.code_totals(prev), A304.code_totals(new), changes, expect_totals)
    led = {"schema": LEDGER_SCHEMA, "method": METHOD, "extends": EXTENDS, "candidate": CANDIDATE,
           "base": A30.BASE_METHOD, "released": A30.RELEASED_METHOD, "released_default": False, "rows": rows,
           "confirmed_unchanged": sorted(conf), "waiting_pieces": WAITING, "integration_package": True}
    run = {"method": METHOD, "policy": POLICY_ID, "extends": EXTENDS, "candidate": CANDIDATE,
           "base_method": A30.BASE_METHOD, "released_method": A30.RELEASED_METHOD, "released_default": False,
           "rollback": ROLLBACK, "identity": ident, "pieces": PIECES, "piece_logs": [log],
           "totals_moved_by_code": moved, "waiting_pieces": WAITING}
    files = {"V3_0_64_BOQ_LINES.json": BL.dumps(new),
             "V3_0_64_BOQ_LINES.csv": A30._lines_csv(new),
             "V3_0_64_INTEGRATION_LEDGER.json": A30._j(led),
             "V3_0_64_INTEGRATION_LEDGER.csv": ledger_csv(rows),
             "V3_0_64_DIFF.csv": A305._csv(diff, DIFF_CSV),
             "V3_0_64_RUN.json": A30._j(run)}
    for name, text in files.items():
        (out / name).write_text(text, encoding="utf-8")
    return sorted(files), ident, led


def policy_record():
    return {"method": METHOD, "extends": EXTENDS, "pieces": sorted(PIECES), "inputs_schema": INPUTS_SCHEMA,
            "released_default": False, "rollback": ROLLBACK, "actions": list(ACTIONS)}


__all__ = ["METHOD", "PIECES", "WAITING", "DEFAULT_GUARD_CLASS", "INPUTS_SCHEMA", "load_inputs", "changes_for",
           "check_concrete", "check_totals", "expected_totals", "integrate", "ledger_rows", "diff_rows", "write",
           "InputsError", "line_class"]
