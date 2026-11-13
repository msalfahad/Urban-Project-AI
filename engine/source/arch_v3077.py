"""ARCH_TAKEOFF_V3.0.77 (T-749, lane I, PAINT RULE WIRING integration package, hub H1P; OWNER RULE PAINT 2026-11-12):
the SAME opt-in BOQ candidate as ARCH_TAKEOFF_V3.0 .. V3.0.76 (engine.source.arch_v30, arch_v301 .. arch_v3076),
extended with THREE pieces built from Checker-merged research, by line id as the merged T-748 readiness map (R6, hub
H1P) names them. No line outside FIN.PAINT (m2), FIN.PAINT.EDGE (lm, new) and FIN.EXT.PAINT.EDGE (lm, new) moves:

  PAINT_RESTATE  (T-740, UP-FIN-PAINT-002 1.0.0) a HELD room paint line restated HELD BOUNDED at the rule range: paint =
                 plaster of the same face - the band above the false ceiling - the tiled faces; the line must be the
                 HELD bounded FIN.PAINT line the map read (stale = stop); a released line never moves here.
  RETURN_LM      (T-746, Lead ruling reading B: 'lm for windows doors and corners') a door / arch / gate return paint m2
                 line leaves the paint area: EXCLUDED_WITH_REASON (EDGE_AS_LM, naming its lm line), never valued, never
                 0 by omission; its painted edge becomes ONE new FIN.PAINT.EDGE lm line per opening, bound to the
                 return's plaster line: HELD BOUNDED low .. high (jambs + head + painted sill by component) or HELD blank
                 where the opening's size / frame is not printed.
  EXT_EDGE       (T-747 + T-751) the exterior paint edges as FIN.EXT.PAINT.EDGE lm lines, HELD (the exterior paint face
                 is HELD: its render host waits T-314 r3), bound to the floor's facade line: one line per window by
                 opening id (arched heads developed, never the rectangle; a window whose height / curved frame is not
                 printed HELD blank) and one line per corner group by face key (closures read from the merged ledger,
                 an unprinted part kept as a bound). A door's exterior edge is the reveal its RETURN_LM line already
                 carries: never a second line.

R-T749-1 (every villa): (a) a line is wired only from a Checker-merged ledger that names it (or its host) by id, through
the merged readiness map; (b) every entry binds the candidate line as the map read it (item, element, unit, class,
range) and stops on a stale line; (c) paint m2 is restated only on a HELD line and stays inside its plaster face; (d) an
opening edge or a corner is an lm item on its own line, never paint m2: a return line that becomes an edge line is
EXCLUDED with its lm line named, the edge counted once (an opening id once per code, a door reveal never on two codes);
(e) a held host never yields a released edge, a blank edge is never numbered and never 0; (f) only FIN.PAINT|m2,
FIN.PAINT.EDGE|lm and FIN.EXT.PAINT.EDGE|lm totals move, each exactly by the changes; every other line byte-identical
(asserted); the earlier state checks re-run on the result (a return line this version EXCLUDES is shown to them in its
base form and checked by this version); nothing here is VERIFIED; blank is never 0.
Files: V3_0_77_BOQ_LINES.json / .csv, V3_0_77_INTEGRATION_LEDGER.json / .csv, V3_0_77_DIFF.csv, V3_0_77_RUN.json.
Nothing here names a project, a sheet, a layer or a coordinate.
"""

from __future__ import annotations

import copy
import hashlib
import re
from decimal import Decimal

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
from engine.source import arch_v3070 as A3070
from engine.source import arch_v3071 as A3071
from engine.source import arch_v3072 as A3072
from engine.source import arch_v3073 as A3073
from engine.source import arch_v3074 as A3074
from engine.source import arch_v3075 as A3075
from engine.source import arch_v3076 as A3076

DEFAULT_GUARD_CLASS = "TOOLING"          # T-212: books Checker-merged paint ledgers
METHOD = "ARCH_TAKEOFF_V3.0.77"
EXTENDS = A3076.METHOD
CANDIDATE = A30.METHOD
POLICY_ID = "URBAN_BOQ_T749_ARCH_V3_0_77"
INPUTS_SCHEMA = "URBAN_V3077_INPUTS_V1"
LEDGER_SCHEMA = "URBAN_V3077_INTEGRATION_LEDGER_V1"
ROLLBACK = A30.ROLLBACK
InputsError = A3063.InputsError
_r = A3063._r
_fmt = A3063._fmt
line_class = A3063.line_class
RULE_ID, RULE_VERSION = "R-T749-1", "T-749"
REC_KEY = "paint_rule_v3077"
PAINT, PLASTER, FACADE = "FIN.PAINT", "FIN.PLASTER", "FIN.EXT.FINISH"
EDGE, EXT_EDGE = "FIN.PAINT.EDGE", "FIN.EXT.PAINT.EDGE"
EDGE_ITEM = ("Paint at opening edges (returns: jambs, head, painted sill)", "دهان حواف الفتحات", "PAINT")
EXT_EDGE_ITEM = ("External paint edges (window jambs / heads, outside corners)", "دهان حواف وزوايا خارجية", "PAINT")
CODES = {PAINT: "m2", EDGE: "lm", EXT_EDGE: "lm"}
P_RS, P_RET, P_EXT = "PAINT_RESTATE", "RETURN_LM", "EXT_EDGE"
ACTIONS = {P_RS: ("RANGE",), P_RET: ("EDGE", "EDGE_BLANK"), P_EXT: ("OPENING", "OPENING_BLANK", "CORNER")}
BOUNDED, BLANK = A3063.BOUNDED, A3063.BLANK
EXCLUDED_STATE = "EXCLUDED_WITH_REASON"
STATUSES = ("DRAWING-CONFIRMED", "HELD", "ASSUMED — OWNER-APPROVED")      # WORKFLOW_CONTROLS s.5; never VERIFIED
TOL = 1e-6
TOT_TOL = 5e-6
MAX_LM = 300.0                           # one edge line above 300 m is a unit slip
MAX_M2 = 1000.0
D = Decimal

PIECES = {
    P_RS: {"module": "engine/source/arch_v3077.py (a HELD room paint line restated at the UP-FIN-PAINT-002 range of "
                     "the merged T-740 face ledger, as mapped by T-748 hub H1P)",
           "policy": "PAINT_GATE_B_V1", "rule_id": "UP-FIN-PAINT-002 1.0.0 / R-T740-1 (R-T749-1)",
           "owner_rules": ["OWNER RULE PAINT 2026-11-12 ('the Area is the same': paint = plaster on the same faces)",
                           "Q-72 (paint to the finished ceiling: the band above a false ceiling is not painted)",
                           "owner 2026-11-02 wet-area walls (no paint on tiled faces)",
                           "UP-QTY-STATUS-001 (held is blank or bounded, never 0)"],
           "owner_manual_method": "paint m2 = the plaster m2 of the same faces, inside and outside, minus the band "
                                  "above a false ceiling and minus tiled faces",
           "drawing_method": "the merged T-740 face ledger: each face's plaster bound from the candidate, the band "
                             "(ceiling height from the reflected plans, T-709) and the tiled part (T-702) deducted item "
                             "by item; the engine paint line's own differences named (opening basis, beam ends)"},
    P_RET: {"module": "engine/source/arch_v3077.py (a return paint m2 line EXCLUDED EDGE_AS_LM; one FIN.PAINT.EDGE lm "
                      "line per opening from the merged T-746 edge ledger)",
            "policy": "PAINT_EDGE_GATE_B_V1", "rule_id": "R-T746-1 / R-T746-2 (R-T749-1)",
            "owner_rules": ["OWNER RULE PAINT 2026-11-12 ('lm for windows doors and corners')",
                            "Lead ruling on T-746: reading B (a door / window return is an lm item per opening)",
                            "UP-FIN-PAINT-002 1.0.0 param edges = LM_ITEMS_NOT_AREA", "UP-QTY-STATUS-001"],
            "owner_manual_method": "per opening: painted jambs 2 x h + head w (+ painted sill w), in lm; never paint m2",
            "drawing_method": "the merged T-746 ledger by opening id: the plan door block's frame posts read against the "
                              "drawn masonry jambs (covered jamb = 0 lm), the head 0 .. w where no section shows the "
                              "head member, a missing size HELD blank"},
    P_EXT: {"module": "engine/source/arch_v3077.py (exterior window edges by opening id and corner groups by face key "
                      "from the merged T-747 / T-751 ledgers, HELD on the floor's facade line)",
            "policy": "EXT_PAINT_EDGE_GATE_B_V1", "rule_id": "R-T747-2 / R-T751-1 / R-T751-2 (R-T749-1)",
            "owner_rules": ["OWNER RULE PAINT 2026-11-12 (corners and window / door edges are lm items)",
                            "register: an arris once per item; arched heads by developed length (L-T377)",
                            "UP-QTY-STATUS-001"],
            "owner_manual_method": "outside corners x exposed height and window jambs + heads, in lm, once each",
            "drawing_method": "elevations + plans: corner heights from printed levels and the frame lines by handle "
                              "(T-751), arched heads by the drawn arc chain, window sizes from the T-313 / T-746 "
                              "ledger; an unprinted end kept as a bound, a missing height HELD blank"},
}
WAITING = dict(A3076.WAITING)
WAITING.update({
    "T749_EXT_PAINT_M2": "exterior paint m2 = render of the same faces (T-747 / T-751: 1,009.110254 .. 1,087.619176 m2 "
                         "on 126 faces, 6 1F slab-edge faces blank) waits its render host: the T-314 r3 face rows are "
                         "not in the candidate (FIN.EXT.FINISH lines HELD blank); no paint m2 line is formed before",
    "T749_EDGES_HELD": "every paint edge line is HELD: interior returns on their head frame coverage (not printed) or "
                       "size; exterior edges on their host face (exterior paint HELD with its render host)",
    "T749_FENCE": "boundary-wall plaster / paint pairs (8) stay HELD blank: refused by R-T747-1 rule 3 / Q-65",
    "T749_FALSE_CEILING_PAINT": "FIN.PAINT.CEILING (31 released) has no plaster soffit line: outside this restatement",
})


# ================================================================================================ inputs
def _d(x, w, hi, zero=False):
    return A3076._d(x, w, hi, zero)


def _range_of(x, w, top, zero_low):
    if x.get("low") is None or x.get("high") is None:
        raise InputsError(f"{w}: a bounded entry carries low and high")
    lo, hi = _d(x["low"], f"{w} low", top, zero=zero_low), _d(x["high"], f"{w} high", top)
    if lo > hi:
        raise InputsError(f"{w}: low {lo} > high {hi}")
    return lo, hi


def _entry(x, srcs):
    p, a = x.get("piece"), x.get("action")
    w = f"{p} {a} {x.get('line_id') or x.get('element_id')}"
    A3043._tasks(x, srcs, w)
    if p not in ACTIONS or a not in ACTIONS[p]:
        raise InputsError(f"{w}: piece / action not one of {ACTIONS}")
    if x.get("status") not in STATUSES:
        raise InputsError(f"{w}: status {x.get('status')!r} ({STATUSES}; never VERIFIED here)")
    A3063._need(x, ("why",), w)
    e = dict(x)
    blank = a in ("EDGE_BLANK", "OPENING_BLANK")
    if blank:
        if x.get("low") is not None or x.get("high") is not None:
            raise InputsError(f"{w}: a blank edge carries a figure (blank is never numbered, never 0)")
    if p == P_RS:
        A3063._need(x, ("line_id", "expect", "plaster"), w)
        ex = x["expect"]
        if ex.get("item_code") != PAINT or ex.get("unit") != "m2" or ex.get("class") != "HELD" or ex.get("low") is None:
            raise InputsError(f"{w}: a restatement moves a HELD bounded FIN.PAINT m2 line only, not {ex}")
        lo, hi = _range_of(x, w, MAX_M2, zero_low=False)
        pl = x["plaster"]
        if hi > D(str(pl[1])) + D("0.000001") or lo > D(str(pl[0])) + D("0.000001"):
            raise InputsError(f"{w}: paint {lo} .. {hi} is above its plaster face {pl} (paint = plaster - band - tiled)")
        e.update(_low=lo, _high=hi)
    elif p == P_RET:
        A3063._need(x, ("line_id", "expect", "host_line_id", "host_expect", "element_id", "opening"), w)
        ex = x["expect"]
        if ex.get("item_code") != PAINT or ex.get("unit") != "m2" or ex.get("class") != "HELD":
            raise InputsError(f"{w}: a return line is a HELD FIN.PAINT m2 line, not {ex}")
        if (x["host_expect"] or {}).get("item_code") != PLASTER:
            raise InputsError(f"{w}: the edge line binds the return's FIN.PLASTER line")
        if not blank:
            lo, hi = _range_of(x, w, MAX_LM, zero_low=True)
            if hi == 0:
                raise InputsError(f"{w}: an edge of 0 .. 0 lm is no painted edge (no line), never a 0 line")
            e.update(_low=lo, _high=hi)
    else:
        A3063._need(x, ("host_line_id", "host_expect", "element_id", "face_id"), w)
        if (x["host_expect"] or {}).get("item_code") != FACADE or (x["host_expect"] or {}).get("class") != "HELD":
            raise InputsError(f"{w}: an exterior edge binds its floor's HELD {FACADE} line")
        if a in ("OPENING", "OPENING_BLANK") and (x.get("kind") != "WINDOW" or not x.get("opening")):
            raise InputsError(f"{w}: an exterior opening line is a window by id (a door reveal is its return line)")
        if not blank:
            lo, hi = _range_of(x, w, MAX_LM, zero_low=False)
            e.update(_low=lo, _high=hi)
    return e


def load_inputs(doc, project_id=None):
    """URBAN_V3077_INPUTS_V1 -> the validated doc.
    {"schema", "project_id", "sources": [{"task", "file", "sha256", "merge_commit", "checker_run"}],
     "entries": [{"piece" PAINT_RESTATE | RETURN_LM | EXT_EDGE, "action", "source_tasks", "rule", "status", "why",
                  PAINT_RESTATE: "line_id", "low", "high", "plaster" [low, high], "expect" {item_code, element_id,
                                 unit, class, low, high};
                  RETURN_LM: "line_id" (the return m2 line), "expect", "host_line_id" (its plaster line), "host_expect",
                             "element_id" (the new lm line), "opening", "low" / "high" (EDGE) or none (EDGE_BLANK);
                  EXT_EDGE: "host_line_id" (the floor's facade line), "host_expect", "element_id", "face_id",
                            OPENING / OPENING_BLANK: "opening", "kind" WINDOW; CORNER: "corner_group"; "low" / "high"}],
     "exterior_doors_counted_once": [{"opening", "lm", "under"}] (optional, asserted against the return lines)}"""
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
    lids = [e["line_id"] for e in ents if e.get("line_id")]
    if len(set(lids)) != len(lids):
        raise InputsError("a line is named twice (one line, one statement)")
    eids = [e["element_id"] for e in ents if e["piece"] != P_RS]
    if len(set(eids)) != len(eids):
        raise InputsError("an edge line element is named twice")
    ops = [(e["piece"], e["opening"]) for e in ents if e.get("opening")]
    if len(set(ops)) != len(ops):
        raise InputsError("an opening is named twice on one code (an edge is counted once)")
    ret_ops = {e["opening"]: e for e in ents if e["piece"] == P_RET}
    ext_ops = {e["opening"] for e in ents if e["piece"] == P_EXT and e.get("opening")}
    if ext_ops & set(ret_ops):
        raise InputsError(f"opening(s) {sorted(ext_ops & set(ret_ops))} on a return line AND an exterior line: one "
                          "reveal, one line")
    for dd in doc.get("exterior_doors_counted_once") or ():
        r = ret_ops.get(dd.get("opening"))
        if r is None or r["line_id"] != dd.get("under") or r.get("_low") is None or \
                (D(str(dd["lm"][0])), D(str(dd["lm"][1]))) != (r["_low"], r["_high"]):
            raise InputsError(f"exterior door {dd.get('opening')}: not the reveal its return line carries")
    return dict(doc, _sources=srcs, _entries=ents)


# ================================================================================================ lines
def _rec(srcs, **kw):
    return dict({"policy": PIECES[kw["piece"]]["policy"], "tasks": [s["task"] for s in srcs],
                 "ledgers": [s["file"] for s in srcs], "ledger_sha256": [s["sha256"] for s in srcs],
                 "merge_commits": [s["merge_commit"] for s in srcs], "checker_runs": [s["checker_run"] for s in srcs],
                 "rule_id": RULE_ID, "rule_version": RULE_VERSION, "release_status": "NOT RELEASED"}, **kw)


def _expect(b, x, w):
    if b is None:
        raise InputsError(f"{w}: not in the candidate (stale binding)")
    loc = b.get("location") or {}
    ok = b["item_code"] == x["item_code"] and loc.get("element_id") == x["element_id"] and b["unit"] == x["unit"] and \
        line_class(b) == x["class"]
    if ok and x["class"] == "HELD":
        r = A3063._range(b)
        if x.get("low") is None:
            ok = r is None and b.get("measured_net") is None
        else:
            ok = r is not None and abs(r[0] - float(x["low"])) <= TOL and abs(r[1] - float(x["high"])) <= TOL
    if not ok:
        raise InputsError(f"{w}: candidate line {b['item_code']} {loc.get('element_id')} {b['evidence_state']} "
                          f"{A30._qty(b)} is not the map's {x} (stale binding: re-read)")


def host_cause(h):
    q = ((h.get("rfi") or {}).get("question") or "").strip()
    return q[:300] if q else "host HELD (no question recorded)"


def _edge_line(h, e, srcs, code):
    from engine.source import boq_line as BL
    item = EDGE_ITEM if code == EDGE else EXT_EDGE_ITEM
    blank = e["action"] in ("EDGE_BLANK", "OPENING_BLANK")
    hc = host_cause(h)
    what = e.get("opening") or e.get("corner_group")
    rec = _rec(srcs, piece=e["piece"], action=e["action"], host_line_id=h["line_id"],
               host_element=(h.get("location") or {}).get("element_id"), host_cause=hc, opening=e.get("opening"),
               corner_group=e.get("corner_group"), face_id=e.get("face_id"), parts=e.get("parts"),
               basis=e.get("basis"), why=str(e["why"])[:400], rule=e.get("rule"), evidence_status=e["status"])
    if blank:
        state, br = BLANK, None
        head = f"HELD (blank): {what}: edge not measurable from the drawings read (never 0)"
    else:
        lo, hi = float(e["_low"]), float(e["_high"])
        state = BOUNDED
        br = {"low": _r(lo), "high": _r(hi), "basis": f"{e.get('rule')}: {what} own edge lm, host HELD"[:200]}
        head = f"HELD (BOUNDED) {_fmt(lo)} .. {_fmt(hi)} m.l ({what})"
    f = (f"{METHOD}: {head}; {e.get('rule')}: an edge is an lm item on its own line, never paint m2 (owner paint rule "
         f"2026-11-12); {str(e['why'])[:500]}; held on: host {h['line_id']}: {hc}")[:1500]
    loc = h.get("location") or {}
    ln = BL.make_line(project_id=h["project"]["project_id"], revision_set_sha256=h["project"]["revision_set_sha256"],
                      item_code=code, unit="lm", evidence_state=state, element_id=e["element_id"],
                      floor=e.get("floor") or loc.get("floor"), room_id=loc.get("room_id"),
                      room_name_en=loc.get("room_name_en"), room_name_ar=loc.get("room_name_ar"),
                      physical_element=("the painted return edge of the opening (jambs, head, painted sill)"
                                        if code == EDGE else "the painted exterior arris (window jamb / head edge or "
                                                             "outside corner), exposed length"),
                      bounded_range=br, formula=f, inputs={REC_KEY: rec, "evidence_status": e["status"]},
                      documents=copy.deepcopy(h["source"]["documents"]), geometry_source=h["source"]["geometry_source"],
                      geometry_confidence=h["source"]["geometry_confidence"], rule_id=RULE_ID,
                      rule_version=RULE_VERSION, material_state="BY_SPEC",
                      rfi={"question": (f"open: {what}: {str(e['why'])[:200]}; host {h['line_id']} HELD: {hc}")[:400],
                           "blocks": [h["line_id"]]},
                      notes=f"paint edge line of {what} (host {h['line_id']}; never summed into paint m2); HELD, never "
                            f"0; NOT RELEASED", item_en=item[0], item_ar=item[1], trade=item[2],
                      subtrade="PAINT_EDGE")
    if A3043.FORMULA_END_RE.search(ln["calculation"]["formula"]):
        raise InputsError(f"{e['element_id']}: the formula would conclude on a figure")
    return A3063._fin(ln)


def _restate(b, e, srcs, edge=None):
    ln = copy.deepcopy(b)
    was = {"evidence_state": b["evidence_state"], "measured_net": b.get("measured_net"), "gross": b.get("gross"),
           "bounded_range": b.get("bounded_range"), "rfi": b.get("rfi"), "class": line_class(b),
           "formula": (b.get("calculation") or {}).get("formula")}
    why = str(e["why"])[:400]
    if e["piece"] == P_RET:
        ln["evidence_state"], ln["measured_net"], ln["gross"], ln["bounded_range"] = EXCLUDED_STATE, None, None, None
        ln["rfi"] = None
        head = (f"EXCLUDED (EDGE_AS_LM: {e['opening']} return paint is the lm line {edge['line_id']}): owner paint rule "
                f"2026-11-12 reading B, an opening edge is never paint m2")
        after = {"excluded": "EDGE_AS_LM", "edge_line_id": edge["line_id"]}
        extra = {"edge_line_id": edge["line_id"], "cause": "EDGE_AS_LM", "opening": e["opening"]}
        ln["notes"] = (f"{METHOD}: EXCLUDED_WITH_REASON EDGE_AS_LM, its edge is {edge['line_id']} (lm): never valued, "
                       f"never 0 by omission; " + str(b.get("notes") or ""))[:600]
    else:
        lo, hi = float(e["_low"]), float(e["_high"])
        ln["evidence_state"], ln["measured_net"], ln["gross"] = BOUNDED, None, None
        ln["bounded_range"] = {"low": _r(lo), "high": _r(hi),
                               "basis": f"{e.get('rule')}: plaster of the same face - band - tiled"[:200]}
        q = ((b.get("rfi") or {}).get("question") or "").strip()
        ln["rfi"] = {"question": (q or f"open: {b['line_id']} HELD with its plaster face")[:400],
                     "blocks": list((b.get("rfi") or {}).get("blocks") or [b["line_id"]])}
        head = f"HELD (BOUNDED) {_fmt(lo)} .. {_fmt(hi)} m2 by UP-FIN-PAINT-002 (paint = plaster - band - tiled)"
        after = {"low": _r(lo), "high": _r(hi)}
        extra = {"plaster_line_id": e.get("plaster_line_id"), "plaster": e.get("plaster"), "band": e.get("band"),
                 "tiled": e.get("tiled")}
    ln["deductions"], ln["additions"] = [], []
    ln["calculation"] = dict(ln["calculation"], formula=f"{METHOD}: {head}; {e.get('rule')}: {why}"[:1500])
    if A3043.FORMULA_END_RE.search(ln["calculation"]["formula"]):
        raise InputsError(f"{b['line_id']}: the formula would conclude on a figure")
    inp = ln["calculation"]["inputs"] = dict(ln["calculation"].get("inputs") or {})
    inp[REC_KEY] = _rec(srcs, piece=e["piece"], action=e["action"], was=was, after=after, why=why,
                        rule=e.get("rule"), evidence_status=e["status"], **extra)
    A305._note(ln, f"{METHOD}: {head[:300]} (was {A302._q(A30._qty(b)) or 'blank'}); NOT RELEASED")
    return A3063._fin(ln)


def changes_for(doc, prev):
    """-> (changes, log)."""
    if not doc:
        return [], {"piece": "T749", "state": "NO_PROJECT_INPUT"}
    if any(((ln.get("calculation") or {}).get("inputs") or {}).get(REC_KEY) for ln in prev):
        raise InputsError("the candidate already carries V3.0.77 records (applied once)")
    if any(ln["item_code"] in (EDGE, EXT_EDGE) for ln in prev):
        raise InputsError(f"the candidate already carries {EDGE} / {EXT_EDGE} lines")
    by = {ln["line_id"]: ln for ln in prev}
    S = doc["_sources"]
    changes, ids = [], set()
    log = {"piece": "T749", "state": "RUN", "by_piece_action": {}, "lines": 0,
           "sources": [{k: s[k] for k in ("task", "file", "sha256", "merge_commit")} for s in doc["sources"]]}
    for e in doc["_entries"]:
        srcs = [S[t] for t in e["source_tasks"]]
        k = f"{e['piece']}:{e['action']}"
        log["by_piece_action"][k] = log["by_piece_action"].get(k, 0) + 1
        ref = "; ".join(s["file"] for s in srcs)
        ver = A3036._ver(srcs)
        if e["piece"] == P_RS:
            b = by.get(e["line_id"])
            _expect(b, e["expect"], k)
            after = _restate(b, e, srcs)
            q = A30._qty(after)
            changes.append(A305._change(e["piece"], "CHANGE", b, after, drawing_reference=ref, held=[
                {"what": e["line_id"], "why": str(e["why"])[:300], "range": [q["low"], q["high"]]}], downstream=[],
                verification=ver, evidence_status=e["status"], group=PAINT, step=e["action"]))
            continue
        h = by.get(e["host_line_id"])
        _expect(h, e["host_expect"], f"{k} host {e['host_line_id']}")
        if line_class(h) != "HELD" and e["piece"] == P_EXT:
            raise InputsError(f"{k}: a held host only (R-T749-1 e)")
        code = EDGE if e["piece"] == P_RET else EXT_EDGE
        edge = _edge_line(h, e, srcs, code)
        if edge["line_id"] in by or edge["line_id"] in ids:
            raise InputsError(f"{k}: the edge line id is already a line")
        ids.add(edge["line_id"])
        q = A30._qty(edge)
        changes.append(A305._change(e["piece"], "ADD", None, edge, drawing_reference=ref, held=[
            {"what": e.get("opening") or e.get("corner_group"), "why": str(e["why"])[:300],
             "range": [q["low"], q["high"]] if q["low"] is not None else None}], downstream=[], verification=ver,
            evidence_status=e["status"], group=code, step=e["action"]))
        if e["piece"] == P_RET:
            b = by.get(e["line_id"])
            _expect(b, e["expect"], k)
            if (b.get("location") or {}).get("floor") != (h.get("location") or {}).get("floor"):
                raise InputsError(f"{k}: the return line and its plaster host are on two floors")
            after = _restate(b, e, srcs, edge)
            changes.append(A305._change(e["piece"], "CHANGE", b, after, drawing_reference=ref, held=[], downstream=[
                {"what": edge["line_id"], "why": "the edge moved to its own lm line"}], verification=ver,
                evidence_status=e["status"], group=PAINT, step="EXCLUDE"))
    log["lines"] = len(changes)
    return changes, log


# ================================================================================================ checks
def expected_totals(t0, changes):
    return A3068.expected_totals(t0, changes)


def check_totals(t0, t1, changes, expect=None):
    """R-T749-1 (f): only the three codes move, each exactly by the changes."""
    moved = {k for k in set(t0) | set(t1) if t0.get(k) != t1.get(k)}
    bad = sorted(k for k in moved if CODES.get(k.split("|")[0]) != k.split("|")[1])
    if bad:
        raise ValueError(f"{METHOD}: totals moved outside {sorted(CODES)}: {bad}")
    want = expected_totals(t0, changes)
    out = {}
    for k in moved:
        z, a = want.get(k), t1.get(k)
        if z is None or a is None:
            raise ValueError(f"{METHOD}: {k} moved with no change on it")
        if a["lines"] != z["lines"] or a["bounded_lines"] != z["bounded_lines"] or \
                a["blocked_lines"] != z["blocked_lines"] or \
                any(abs(a[f] - z[f]) > TOT_TOL for f in ("released", "held_low", "held_high")):
            raise ValueError(f"{METHOD}: {k} totals {a} are not the changes' {z}")
        if expect and k in expect:
            for f, v in expect[k].items():
                if abs(a[f] - v) > TOT_TOL:
                    raise ValueError(f"{METHOD}: {k} {f} {a[f]} is not the inputs' {v}")
        out[k] = {"base": t0.get(k), "v3_0_77": a}
    return out


def check_lines(lines, before=None):
    """on finished lines: every V3.0.77 line is in the state its piece names; an edge line binds a HELD host by id, an
    opening once per code, never on two codes; an EDGE_AS_LM exclusion names an edge line of its opening; with
    `before`: no line became RELEASED and no released quantity moved. -> {piece:action: n}"""
    by = {ln["line_id"]: ln for ln in lines}
    out, seen = {}, set()
    edge_of = {}
    for ln in lines:
        rec = ((ln.get("calculation") or {}).get("inputs") or {}).get(REC_KEY)
        if not rec:
            if ln["item_code"] in (EDGE, EXT_EDGE):
                raise ValueError(f"{METHOD}: {ln['line_id']} an edge line with no V3.0.77 record")
            continue
        p, a, cls, r = rec["piece"], rec["action"], line_class(ln), A3063._range(ln)
        if ln["item_code"] in (EDGE, EXT_EDGE):
            h = by.get(rec["host_line_id"])
            key = (ln["item_code"], rec.get("opening") or rec.get("corner_group"))
            ok = ln["unit"] == "lm" and cls == "HELD" and ln.get("measured_net") is None and h is not None and \
                key not in seen and (ln["item_code"] == EDGE) == (p == P_RET)
            ok = ok and (h["item_code"] == PLASTER if p == P_RET else (h["item_code"] == FACADE and
                                                                      line_class(h) == "HELD"))
            if a in ("EDGE_BLANK", "OPENING_BLANK"):
                ok = ok and ln["evidence_state"] == BLANK and r is None
            else:
                ok = ok and r is not None and 0 <= r[0] <= r[1] + 1e-9 and r[1] > 0
            seen.add(key)
            if rec.get("opening"):
                edge_of.setdefault(rec["opening"], set()).add(ln["item_code"])
        elif p == P_RET:
            e = by.get(rec.get("edge_line_id"))
            ok = ln["evidence_state"] == EXCLUDED_STATE and ln.get("measured_net") is None and e is not None and \
                e["item_code"] == EDGE and e["calculation"]["inputs"][REC_KEY].get("opening") == rec["opening"] and \
                ln["item_code"] == PAINT and bool(ln.get("notes"))
        else:
            ok = ln["item_code"] == PAINT and cls == "HELD" and r is not None and 0 < r[0] <= r[1] and \
                rec["was"]["class"] == "HELD"
        ok = ok and rec["release_status"] == "NOT RELEASED" and (cls == "EXCLUDED" or
                                                                  bool((ln.get("rfi") or {}).get("question")))
        if not ok:
            raise ValueError(f"{METHOD}: {ln['line_id']}: a {p} {a} line is not in its state")
        out[f"{p}:{a}" if ln["item_code"] != PAINT or p == P_RS else f"{p}:EXCLUDE"] = \
            out.get(f"{p}:{a}" if ln["item_code"] != PAINT or p == P_RS else f"{p}:EXCLUDE", 0) + 1
    two = sorted(o for o, c in edge_of.items() if len(c) > 1)
    if two:
        raise ValueError(f"{METHOD}: opening(s) {two} on two edge codes (one reveal, one line)")
    if before is not None:
        old = {x["line_id"]: x for x in before}
        for ln in lines:
            o = old.get(ln["line_id"])
            if o is None:
                continue
            if line_class(ln) == "RELEASED" and (line_class(o) != "RELEASED" or
                                                 o.get("measured_net") != ln.get("measured_net")):
                raise ValueError(f"{METHOD}: {ln['line_id']}: a released quantity moved")
            if line_class(o) == "RELEASED" and line_class(ln) != "RELEASED":
                raise ValueError(f"{METHOD}: {ln['line_id']}: a released line left RELEASED (no record here)")
    return out


def census(lines, codes=tuple(CODES)):
    """per code: released n / qty, bounded n / low .. high, blank n, excluded n (run-record sums only)."""
    out = {}
    for ln in lines:
        c = ln["item_code"]
        if c not in codes:
            continue
        z = out.setdefault(c, {"unit": ln["unit"], "lines": 0, "released": 0, "released_q": 0.0, "bounded": 0,
                               "low": 0.0, "high": 0.0, "blank": 0, "excluded": 0})
        z["lines"] += 1
        k, r = line_class(ln), A3063._range(ln)
        if k == "EXCLUDED":
            z["excluded"] += 1
        elif k == "RELEASED":
            z["released"] += 1
            z["released_q"] += float(ln["measured_net"])
        elif r is not None:
            z["bounded"] += 1
            z["low"] += r[0]
            z["high"] += r[1]
        else:
            z["blank"] += 1
    for z in out.values():
        for f in ("released_q", "low", "high"):
            z[f] = round(z[f], 6)
    return out


# ================================================================================================ integrate / write
def _older_view(out, prev):
    """the result as the earlier state checks see it: a return line this version EXCLUDES (EDGE_AS_LM) in its base
    form (its V3.0.74 record names a 0 .. face range; this version's own check holds the exclusion)."""
    old = {x["line_id"]: x for x in prev}
    view = []
    for ln in out:
        rec = ((ln.get("calculation") or {}).get("inputs") or {}).get(REC_KEY)
        view.append(old[ln["line_id"]] if rec and rec["piece"] == P_RET and ln["item_code"] == PAINT else ln)
    return view


def integrate(prev, changes, for_lead=()):
    """-> (V3.0.77 lines, identity). Changed lines replace their candidate line in place, added edge lines follow the
    base; every other candidate line byte-identical (asserted); the earlier state checks re-run."""
    sid = {ln["line_id"]: i for i, ln in enumerate(prev)}
    out, repl, add = list(prev), set(), []
    for c in changes:
        a = c["after"]
        if CODES.get(a["item_code"]) != a["unit"]:
            raise ValueError(f"{METHOD}: {a['item_code']} {a['unit']} is not a code this version may touch")
        if c["action"] == "CHANGE":
            i = sid.get(a["line_id"])
            if i is None or a["line_id"] in repl or a["item_code"] != PAINT:
                raise ValueError(f"{METHOD}: a changed line is not a candidate paint line or changes twice")
            out[i] = a
            repl.add(a["line_id"])
        elif c["action"] == "ADD":
            if a["line_id"] in sid or a["item_code"] not in (EDGE, EXT_EDGE):
                raise ValueError(f"{METHOD}: only edge lines are added, never over a candidate id")
            add.append(a)
        else:
            raise ValueError(f"{METHOD}: action {c['action']}")
    out = out + add
    if len({ln["line_id"] for ln in out}) != len(out):
        raise ValueError(f"{METHOD}: a BOQ line id appears twice")
    outside = [ln for ln in prev if ln["line_id"] not in repl]
    bad = [a["line_id"] for a in outside if A30.line_sha(a) != A30.line_sha(out[sid[a["line_id"]]])]
    if bad:
        raise ValueError(f"{METHOD}: {len(bad)} candidate line(s) differ outside the named changes")
    pids = {(ln["project"]["project_id"], ln["project"]["revision_set_sha256"]) for ln in out}
    if len(pids) != 1:
        raise ValueError(f"{METHOD}: {len(pids)} project identities in the lines")
    v = _older_view(out, prev)
    ident = {"base_lines": len(prev), "v3_0_77_lines": len(out), "v3_0_77_rows": len(changes), "replaced": len(repl),
             "added": len(add), "concrete_v3_0_64": A3064.check_concrete(v),
             "concrete_v3_0_65": A3065.check_concrete(v), "concrete_v3_0_66": A3066.check_concrete(v),
             "concrete_v3_0_67": A3067.check_concrete(v, prev), "lintels_v3_0_67": A3067.check_lintels(v),
             "masonry_v3_0_68": A3068.check_masonry(v), "finishes_v3_0_69": A3069.check_finishes(v),
             "concrete_v3_0_70": A3070.check_concrete(v, prev), "lintels_v3_0_71": A3071.check_lintels(v, prev),
             "masonry_v3_0_72": A3072.check_masonry(v, prev), "concrete_v3_0_73": A3073.check_concrete(v, prev),
             "finishes_v3_0_74": A3074.check_finishes(v, prev), "formwork_concrete_v3_0_75":
                 A3075.check_lines(v, prev), "beads_ceiling_v3_0_76": A3076.check_lines(v, prev),
             "paint_rule": check_lines(out, prev),
             "older_checks_view_substituted": sum(1 for a, b in zip(v, out) if a is not b),
             "outside_rows": len(outside), "outside_rows_identical_to_base": len(outside),
             "outside_rows_sha256": hashlib.sha256("".join(A30.line_sha(x) for x in outside).encode()).hexdigest()}
    return out, ident


def ledger_rows(changes, released_lines=None):
    rel = {A30._key(ln): ln for ln in released_lines or ()}
    rows = []
    for c in changes:
        a = c["after"]
        b29 = None
        if released_lines is not None:
            b29 = A30._qty(rel[A30._key(a)]) if A30._key(a) in rel else dict(A30._qty(None), state="NOT_IN_RELEASED")
        rec = a["calculation"]["inputs"][REC_KEY]
        loc = a.get("location") or {}
        rows.append({"version": METHOD, "piece": c["piece"], "action": c.get("step"), "change": c["action"],
                     "line_id": a["line_id"], "item_code": a["item_code"], "floor": loc.get("floor"),
                     "element_id": loc.get("element_id"), "unit": a["unit"], "host_line_id": rec.get("host_line_id"),
                     "edge_line_id": rec.get("edge_line_id"), "opening": rec.get("opening"),
                     "corner_group": rec.get("corner_group"), "face_id": rec.get("face_id"),
                     "before_released_v2_9": b29, "before_base": A30._qty(c.get("before")), "after_v3_0_77": A30._qty(a),
                     "class": [None if c.get("before") is None else line_class(c["before"]), line_class(a)],
                     "evidence_state_after": a["evidence_state"], "parts": rec.get("parts"), "basis": rec.get("basis"),
                     "plaster": rec.get("plaster"), "band": rec.get("band"), "tiled": rec.get("tiled"),
                     "evidence_status": c.get("evidence_status"), "still_held": c.get("held"),
                     "rule": rec.get("rule"), "why": rec.get("why"), "release_status": "NOT RELEASED",
                     "owner_manual_method": PIECES[c["piece"]]["owner_manual_method"],
                     "drawing_derived_method": PIECES[c["piece"]]["drawing_method"],
                     "verification": c.get("verification") or {}, "rollback": ROLLBACK})
    return rows


LEDGER_CSV = ("version", "piece", "action", "change", "line_id", "item_code", "floor", "element_id", "unit", "v2_9",
              "base", "v3_0_77", "beside", "class", "rule", "evidence_status", "verification")
DIFF_CSV = ("line_id", "item_code", "floor", "element_id", "unit", "vs_base", "vs_released_v2_9", "v2_9", "base",
            "v3_0_77")


def ledger_csv(rows):
    def q(x):
        return A302._q(x) if x and (x.get("value") is not None or x.get("low") is not None or x.get("state")) else ""

    def bs(r):
        if r.get("edge_line_id"):
            return f"EXCLUDED: EDGE_AS_LM, edge {r['edge_line_id']}"
        if r.get("host_line_id"):
            return f"host {r['host_line_id']}"
        return "none"
    return A305._csv([{"version": r["version"], "piece": r["piece"], "action": r["action"], "change": r["change"],
                       "line_id": r["line_id"], "item_code": r["item_code"], "floor": r.get("floor") or "",
                       "element_id": r.get("element_id") or "", "unit": r["unit"],
                       "v2_9": q(r.get("before_released_v2_9")), "base": q(r.get("before_base")),
                       "v3_0_77": q(r.get("after_v3_0_77")), "beside": bs(r),
                       "class": " -> ".join(str(x) for x in r["class"]), "rule": r.get("rule") or "",
                       "evidence_status": r["evidence_status"],
                       "verification": f"{r['verification'].get('task')} "
                                       f"{' '.join(x[:8] for x in r['verification'].get('merge_commits') or ())}"}
                      for r in rows], LEDGER_CSV)


def diff_rows(prev, new, released_lines=None):
    return [dict({k: v for k, v in d.items() if k != "v3_0_76"}, v3_0_77=d["v3_0_76"])
            for d in A3076.diff_rows(prev, new, released_lines)]


def write(out, prev, changes, log, released_lines=None, for_lead=(), expect_totals=None):
    """the V3_0_77_* files beside the base candidate's files. -> (file names, identity, ledger)."""
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
    dsum = {}
    for d in diff:
        dsum.setdefault("vs_base", {}).setdefault(d["vs_base"], 0)
        dsum["vs_base"][d["vs_base"]] += 1
        if d["vs_released_v2_9"] is not None:
            dsum.setdefault("vs_released_v2_9", {}).setdefault(d["vs_released_v2_9"], 0)
            dsum["vs_released_v2_9"][d["vs_released_v2_9"]] += 1
    ident = dict(ident, diff=dsum, census_before=census(prev), census_after=census(new))
    moved = check_totals(A304.code_totals(prev), A304.code_totals(new), changes, expect_totals)
    led = {"schema": LEDGER_SCHEMA, "method": METHOD, "extends": EXTENDS, "candidate": CANDIDATE,
           "base": A30.BASE_METHOD, "released": A30.RELEASED_METHOD, "released_default": False, "rows": rows,
           "summary": log, "waiting_pieces": WAITING, "integration_package": True}
    run = {"method": METHOD, "policy": POLICY_ID, "extends": EXTENDS, "candidate": CANDIDATE,
           "base_method": A30.BASE_METHOD, "released_method": A30.RELEASED_METHOD, "released_default": False,
           "rollback": ROLLBACK, "identity": ident, "pieces": PIECES, "piece_logs": [log],
           "totals_moved_by_code": moved, "waiting_pieces": WAITING}
    files = {"V3_0_77_BOQ_LINES.json": BL.dumps(new),
             "V3_0_77_BOQ_LINES.csv": A30._lines_csv(new),
             "V3_0_77_INTEGRATION_LEDGER.json": A30._j(led),
             "V3_0_77_INTEGRATION_LEDGER.csv": ledger_csv(rows),
             "V3_0_77_DIFF.csv": A305._csv(diff, DIFF_CSV),
             "V3_0_77_RUN.json": A30._j(run)}
    for name, text in files.items():
        (out / name).write_text(text, encoding="utf-8")
    return sorted(files), ident, led


def policy_record():
    return {"method": METHOD, "extends": EXTENDS, "pieces": sorted(PIECES), "inputs_schema": INPUTS_SCHEMA,
            "released_default": False, "rollback": ROLLBACK, "codes": sorted(CODES)}


__all__ = ["METHOD", "PIECES", "WAITING", "DEFAULT_GUARD_CLASS", "INPUTS_SCHEMA", "load_inputs", "changes_for",
           "census", "check_lines", "check_totals", "expected_totals", "integrate", "ledger_rows", "diff_rows", "write",
           "InputsError", "line_class", "host_cause"]
