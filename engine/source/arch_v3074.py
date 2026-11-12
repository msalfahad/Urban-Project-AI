"""ARCH_TAKEOFF_V3.0.74 (T-717, lane I, PLASTER / PAINT GATE B ROUND 2 integration package, hub H1): the SAME opt-in BOQ
candidate as ARCH_TAKEOFF_V3.0 .. V3.0.73 (engine.source.arch_v30, arch_v301 .. arch_v3073), extended with THREE pieces
built from the Checker-merged plaster / paint research T-701 (R-T701-2: annex plaster ENGINE_WRONG, bound too narrow),
T-702 (part (c): wet-room band beam crossings and sunken panels) and T-709 (R-T709-1 double-height band, R-T709-4
return paint, F-T709-1 W12 deduction), as mapped line by line by the merged T-723 readiness (R-T723-1, hub T-717);
no line outside FIN.PLASTER / FIN.PAINT moves, no released quantity moves:

  FIN_RESTATE   a named HELD FIN.PLASTER line is restated to the merged ledger's BOUND low .. high: the annex rooms
                GF-01 / GF-04 (R-T701-2: the V3.0.69 point / narrow range sat inside the merged R-T678-2 / T-686 datum
                bound, so the line is widened to that bound; GF-01 with the F-T709-1 W12 deduction correction applied
                to both ends) and the GF wet-room bands GF-07 / GF-14 (T-702 (c): beam B27 crossing and the sunken
                panels 280 / 287 over the band, D-41). The candidate figure each ledger started from is asserted.
  RETURN_PAINT  one NEW FIN.PAINT line per plastered door / reveal return face (R-T709-4): '<face id>:RETURN_PAINT',
                bound by id to its FIN.PLASTER return line (never summed into a room paint line): HELD bounded 0 ..
                the face's plaster m2 (the frame-covered jamb depth is printed nowhere: the low 0 is the physical
                extreme where the frame covers the whole jamb, a bound end, never a value) or HELD blank where the
                plaster face itself is blank; the high asserted equal to the live plaster figure.
  DH_BAND       one NEW FIN.PLASTER and one NEW FIN.PAINT band line on a wall that runs through a slab-free stairwell
                (R-T709-1): the face between the lower room's top (plaster: its soffit; paint: its ceiling) and the
                upper floor, over the solid run below; bound by id to the lower room's line (never added into it);
                low .. high RECOMPUTED here from run x (upper - lower) (- a landing piece at the low end, + column
                returns at the high end) and asserted equal to the ledger.

R-T717-1 (every villa): (a) a line is restated or added only from a Checker-merged ledger that names it (line id or
host line id) through the merged readiness map, the candidate state each row started from asserted (stale = stop); a
named correction (finding, delta) is applied to both ends exactly; (b) every changed or added line is HELD (bounded or
blank), never VERIFIED, never released; a downgraded line never keeps a value; (c) a return-paint line binds one
plaster return face, one line per face; its high is the face's plaster m2 on the live line; a blank face gives a blank
paint line; the low 0 is allowed ONLY on this piece, as the frame-covered extreme; a flagged face (wet rooms both
sides, R-T701-3) keeps its flag; (d) a band line binds its room line by id and carries its recomputed terms; 0 < low <=
high; (e) only FIN.PLASTER|m2 / FIN.PAINT|m2 code totals move, each exactly by the changes; every other line is
byte-identical (asserted); the earlier concrete / lintel / masonry / finish checks re-run on the result.
Files: V3_0_74_BOQ_LINES.json / .csv, V3_0_74_INTEGRATION_LEDGER.json / .csv, V3_0_74_DIFF.csv, V3_0_74_RUN.json.
Nothing here names a project, a sheet, a layer or a coordinate.
"""

from __future__ import annotations

import copy
import hashlib
from decimal import Decimal

from engine.source import arch_v30 as A30
from engine.source import arch_v302 as A302
from engine.source import arch_v304 as A304
from engine.source import arch_v305 as A305
from engine.source import arch_v3043 as A3043
from engine.source import arch_v3046 as A3046
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

DEFAULT_GUARD_CLASS = "TOOLING"          # T-212: books Checker-merged finish ledgers onto candidate lines
METHOD = "ARCH_TAKEOFF_V3.0.74"
EXTENDS = A3073.METHOD
CANDIDATE = A30.METHOD
POLICY_ID = "URBAN_BOQ_T717_ARCH_V3_0_74"
INPUTS_SCHEMA = "URBAN_V3074_INPUTS_V1"
LEDGER_SCHEMA = "URBAN_V3074_INTEGRATION_LEDGER_V1"
ROLLBACK = A30.ROLLBACK
InputsError = A3063.InputsError
_r = A3063._r
_fmt = A3063._fmt
line_class = A3063.line_class
RULE_ID, RULE_VERSION = "R-T717-1", "T-717"
REC_KEY = "finish_gate_b_v3074"
PLASTER, PAINT = A3069.PLASTER, A3069.PAINT
CODES = (PLASTER, PAINT)
UNIT = "m2"
BOUNDED, BLANK = A3063.BOUNDED, A3063.BLANK
STATUSES = ("DRAWING-CONFIRMED", "HELD", "UNKNOWN")      # WORKFLOW_CONTROLS s.5; every line here stays HELD
P_FIN, P_RET, P_BAND = "FIN_RESTATE", "RETURN_PAINT", "DH_BAND"
RET_SUFFIX = ":RETURN_PAINT"
TOL = 1e-6
TOT_TOL = 5e-6
X = Decimal

PIECES = {
    P_FIN: {"module": "engine/source/arch_v3074.py (named HELD FIN.PLASTER lines restated to the Checker-merged T-701 "
                      "R-T701-2 annex datum bound (F-T709-1 W12 applied) and the T-702 (c) GF wet-band bounds)",
            "policy": "FINISH_GATE_B_V2", "rule_id": "R-T701-2 / T-702 (c) / F-T709-1 (R-T717-1)",
            "owner_rules": ["Q-72 (plaster to the structural slab underside)",
                            "Q-48 A (tile top / paint = finished ceiling)",
                            "Q-54 B (annex +4.30 datum held: bounds only, no point)",
                            "Q-73 (full deduction of every actual opening)",
                            "UP-QTY-STATUS-001 (held is blank or bounded, never 0)",
                            "ERS s.2-5 (drawn element first; one physical element once)"],
            "owner_manual_method": "wall face length x height (plaster to the slab underside) - openings; the "
                                   "freelancer's flat heights and half-deducted openings are not the owner rule",
            "drawing_method": "annex: face lm x S over the merged R-T678-2 / T-686 datum bound (S 3.084 .. 3.84 GF-04, "
                              "the GF-01 terms of T-701) - fixed openings (W12 1.95492 x 2.20 = 4.300824, F-T709-1) - "
                              "beam ends; GF wet bands: face x (S - H) with beam B27 filling its stretch and the "
                              "sunken panels 280 / 287 (drop d printed nowhere, D-41) at 0 .. full band (T-702 (c))"},
    P_RET: {"module": "engine/source/arch_v3074.py (one FIN.PAINT return line per plastered return face id, bound "
                      "0 .. the face's plaster m2, R-T709-4)",
            "policy": "FINISH_GATE_B_V2", "rule_id": "R-T709-4 (R-T717-1 (c))",
            "owner_rules": ["Q-73 (full deduction of every actual opening: the return is a separate face)",
                            "R-T701-3 (one finish per face)", "UP-QTY-STATUS-001"],
            "owner_manual_method": "paint on the plastered return faces of each opening (jambs + head x wall "
                                   "thickness) less the depth the door frame covers",
            "drawing_method": "the plastered return face (T-634 by handle: t x (2 x head + width)) is the high end; "
                              "the frame-covered depth is printed nowhere (frame / casing detail, designer datum): "
                              "low 0 = frame over the whole jamb"},
    P_BAND: {"module": "engine/source/arch_v3074.py (double-height stairwell band: plaster soffit -> upper floor, "
                       "paint ceiling -> upper floor, over the solid run below, R-T709-1)",
             "policy": "FINISH_GATE_B_V2", "rule_id": "R-T709-1 (R-T717-1 (d)); void V-01 by T-719 R-T719-1..5",
             "owner_rules": ["Q-72 (continuous exposed height through a stairwell; plaster to the slab underside)",
                             "Q-48 A (paint to the finished ceiling)", "register ruling 2026-11-11 (double-height "
                             "bands -> plaster; voids B2-05 deducted once, union)"],
             "owner_manual_method": "the stairwell wall is one face from the lower floor to the upper floor; the "
                                    "lower room's line stops at its soffit / ceiling, the upper room's starts at its "
                                    "floor: the band between is measured once",
             "drawing_method": "solid run below the upper wall by handle (wall face + two column faces = 3.997201 m), "
                               "plaster +5.29 (GF soffit, T-556) .. +5.50 (1F floor), paint +4.65 (GF ceiling G1) .. "
                               "+5.50; high adds the column returns 0.15 lm; paint low takes the ST-02 corner landing "
                               "+4.696 against the wall over at most 1.15 m (0 .. 0.0529 m2)"},
}
WAITING = dict(A3073.WAITING)
WAITING.update({
    "T717_PAINT_GF01_W12": "F-T709-1 also puts the GF-01 PAINT line 0.010824 m2 high (same W12 deduction): it is not in "
                           "the T-723 H1 map; it moves with the next GF-01 paint restatement (lane I), named here",
    "T717_BAND_BEAMS": "the beam faces under the 1F well walls (south 3.020 lm, west 4.000 lm, below +5.50) stay HELD by "
                       "name: beam depth on the structural GF roof slab plan (T-709 (a)); no line is opened for them",
    "T717_RETURN_LOW": "every return-paint low stays 0 until the frame-covered jamb depth is printed (frame / casing "
                       "detail, designer datum); 5 faces between two wet rooms are NOT_ESTABLISHED (R-T701-3)",
    "T717_SHAFT_ROW": "the freelancer's 2.50 x 5.40 = 13.50 m2 plaster row (paint row the same) is NO_FACE (T-726 "
                      "R-T726-1..3): shown apart in the like-for-like line, never added, never removed from his total",
    "T717_F_V709_1": "Checker re-measure of the GF solid run 4.000 m vs the ledger 3.997201 m (2.8 mm frame offset, "
                     "immaterial): the band is wired as merged; the residual is named, not applied",
})


# ================================================================================================ inputs
def _num(x, w, lo=0.0, hi=100000.0):
    if isinstance(x, bool) or not isinstance(x, (int, float)) or x != x or x < lo or x > hi:
        raise InputsError(f"{w}: {x!r} is not a quantity in range")
    return float(x)


def _status(s, w):
    if not isinstance(s, dict) or s.get("status") not in STATUSES or not s.get("basis"):
        raise InputsError(f"{w}: evidence status {(s or {}).get('status')!r} with its basis (WORKFLOW_CONTROLS s.5; a "
                          f"V3.0.74 line stays HELD, never VERIFIED or owner-approved here)")
    return dict(s)


def _d(x, w):
    try:
        v = X(str(x))
    except Exception:
        raise InputsError(f"{w}: {x!r} is not a number")
    if not v.is_finite():
        raise InputsError(f"{w}: {x!r} is not finite")
    return v


def corrected(ledger_after, correction, w="correction"):
    """a named finding applied to both ends exactly: (low + delta, high + delta), Decimal, 6 dp"""
    if not correction:
        return tuple(float(x) for x in ledger_after)
    dl = _d(correction.get("delta_m2"), w)
    if not correction.get("finding") or dl == 0:
        raise InputsError(f"{w}: a correction names its finding and a non-zero delta")
    if abs(dl) > X("1"):
        raise InputsError(f"{w}: delta {dl} m2 is not a deduction correction (unit slip?)")
    lo, hi = (_d(x, w) + dl for x in ledger_after)
    return float(lo.quantize(X("0.000001"))), float(hi.quantize(X("0.000001")))


def _restate_entry(x, srcs):
    w = f"BOUND {x.get('line_id')}"
    if x.get("action") != "BOUND":
        raise InputsError(f"{w}: V3.0.74 restates to BOUND only")
    A3063._need(x, ("line_id", "item_code", "expect", "ledger_after", "after", "basis", "status", "still_open",
                    "source_tasks"), w)
    if x["item_code"] != PLASTER:
        raise InputsError(f"{w}: {x['item_code']} is not FIN.PLASTER (the H1 restatements are plaster lines)")
    if any(t not in srcs for t in x["source_tasks"]):
        raise InputsError(f"{w}: no merged source named")
    ex = x["expect"]
    if ex.get("class") != "HELD" or ex.get("low") is None or ex.get("high") is None:
        raise InputsError(f"{w}: the ledger starts from a HELD range on the candidate")
    st = _status(x["status"], w)
    if st["status"] != "HELD":
        raise InputsError(f"{w}: a BOUND line is HELD")
    la = [_num(v, w) for v in x["ledger_after"]]
    lo, hi = corrected(la, x.get("correction"), w)
    af = x["after"]
    if abs(_num(af.get("low"), w) - lo) > TOL or abs(_num(af.get("high"), w) - hi) > TOL:
        raise InputsError(f"{w}: after {af} is not the ledger bound {la} with its correction ({lo} .. {hi})")
    if not 0 < lo < hi:
        raise InputsError(f"{w}: a bound is 0 < low < high ({lo} .. {hi})")
    return dict(x, status=st, after={"low": lo, "high": hi})


def _return_entry(x, srcs):
    w = f"RETURN {x.get('host_line_id')}"
    A3063._need(x, ("host_line_id", "face_id", "element_id", "expect_host", "after", "basis", "status",
                    "source_tasks"), w)
    if any(t not in srcs for t in x["source_tasks"]):
        raise InputsError(f"{w}: no merged source named")
    if x["element_id"] != x["face_id"] + RET_SUFFIX:
        raise InputsError(f"{w}: element {x['element_id']!r} is not '<face id>{RET_SUFFIX}'")
    st = _status(x["status"], w)
    if st["status"] != "HELD":
        raise InputsError(f"{w}: a return-paint line is HELD (never a value: R-T709-4)")
    eh, af = x["expect_host"], x["after"]
    if eh.get("item_code") != PLASTER or eh.get("class") not in ("RELEASED", "HELD"):
        raise InputsError(f"{w}: the host is a FIN.PLASTER return line")
    if af.get("kind") == "BLANK":
        if af.get("low") is not None or af.get("high") is not None or eh.get("value") is not None:
            raise InputsError(f"{w}: a blank return-paint line binds a blank plaster face and carries no figure")
        if not x.get("still_open"):
            raise InputsError(f"{w}: a blank line names what holds it")
        return dict(x, status=st, after={"kind": "BLANK"})
    if af.get("kind") != "BOUND":
        raise InputsError(f"{w}: kind {af.get('kind')!r}")
    lo, hi = _num(af.get("low"), w), _num(af.get("high"), w, lo=1e-9)
    if lo != 0.0:
        raise InputsError(f"{w}: the return-paint low is the frame-covered extreme 0 until the depth is printed "
                          f"(R-T709-4); {lo} is not a ledger figure")
    hv = eh.get("value")
    if hv is None or abs(_num(hv, w) - hi) > TOL:
        raise InputsError(f"{w}: high {hi} is not the plaster face's {hv} m2 (R-T717-1 (c))")
    if not x.get("still_open"):
        raise InputsError(f"{w}: a HELD bound names what stays open")
    return dict(x, status=st, after={"kind": "BOUND", "low": 0.0, "high": hi})


def band_figure(b):
    """R-T709-1: (low, high) m2 = run x (top - bottom) - low_deduction_max, + returns_lm x (top - bottom); Decimal,
    6 dp half-even on the exact product (the ledger's own figures)."""
    w = f"band {b.get('element_id')}"
    run, rl = _d(b["run_m"], w), _d(b.get("returns_lm") or 0, w)
    bot, top = (_d(v, w) for v in b["levels_m"])
    ded = _d(b.get("low_deduction_max_m2") or 0, w)
    if run <= 0 or rl < 0 or ded < 0:
        raise InputsError(f"{w}: run / returns / deduction must be positive")
    if run > 100 or top - bot > 10:
        raise InputsError(f"{w}: run {run} m / height {top - bot} m (unit slip?)")
    if top <= bot:
        raise InputsError(f"{w}: the upper level {top} is not above the lower top {bot}")
    h = top - bot
    q = X("0.000001")
    lo = (run * h - ded).quantize(q)
    hi = (run * h + rl * h).quantize(q)
    if lo <= 0:
        raise InputsError(f"{w}: band low {lo} (blank is never 0)")
    return float(lo), float(hi)


def _band_entry(b, srcs):
    w = f"band {b.get('element_id')}"
    A3063._need(b, ("host_line_id", "item_code", "element_id", "run_m", "levels_m", "low", "high", "status",
                    "still_open", "source_tasks", "expect_host"), w)
    if b["item_code"] not in CODES:
        raise InputsError(f"{w}: {b['item_code']} is not FIN.PLASTER / FIN.PAINT")
    if any(t not in srcs for t in b["source_tasks"]):
        raise InputsError(f"{w}: no merged source named")
    lo, hi = _num(b["low"], w), _num(b["high"], w)
    flo, fhi = band_figure(b)
    if abs(flo - lo) > TOL or abs(fhi - hi) > TOL:
        raise InputsError(f"{w}: ledger band {lo} .. {hi} is not the recomputed {flo} .. {fhi}")
    if not 0 < lo <= hi:
        raise InputsError(f"{w}: band 0 < low <= high")
    st = _status(b["status"], w)
    if st["status"] != "HELD":
        raise InputsError(f"{w}: a band line is HELD")
    if b["expect_host"].get("item_code") != b["item_code"]:
        raise InputsError(f"{w}: the band binds a room line of its own code")
    return dict(b, low=lo, high=hi, status=st)


def load_inputs(doc, project_id=None):
    """URBAN_V3074_INPUTS_V1 -> the validated doc.
    {"schema", "project_id", "sources": [{"task", "file", "sha256", "merge_commit", "checker_run"}],
     "restate": [{"line_id", "item_code", "action" BOUND, "expect" {"class" HELD, "low", "high"}, "ledger_after"
                  [lo, hi], "correction" {"finding", "delta_m2", "why"} | None, "after" {"low", "high"}, "basis",
                  "status", "still_open", "source_tasks", "map_row"}],
     "returns": [{"host_line_id", "face_id", "element_id", "expect_host" {"item_code", "class", "value"}, "after"
                  {"kind" BOUND, "low" 0, "high"} | {"kind" BLANK}, "flag", "basis", "status", "still_open",
                  "source_tasks", "map_row"}],
     "bands": [{"host_line_id", "expect_host" {"item_code", "class", "low", "high"}, "item_code", "element_id",
                "run_m", "levels_m" [bottom, top], "returns_lm", "low_deduction_max_m2", "low", "high", "status",
                "still_open", "source_tasks", "map_row"}],
     "expect_totals": {"<code>|m2": {...}} (optional)}"""
    if not doc:
        return None
    if doc.get("schema") != INPUTS_SCHEMA:
        raise InputsError(f"project inputs: schema must be {INPUTS_SCHEMA}")
    if project_id and doc.get("project_id") not in (None, project_id):
        raise InputsError(f"project inputs are for {doc.get('project_id')!r}, the run is {project_id!r}")
    srcs = A3043._sources(doc)
    res = [_restate_entry(x, srcs) for x in doc.get("restate") or ()]
    rets = [_return_entry(x, srcs) for x in doc.get("returns") or ()]
    bands = [_band_entry(b, srcs) for b in doc.get("bands") or ()]
    if not res and not rets and not bands:
        raise InputsError("no entry in the inputs")
    ids = [e["line_id"] for e in res]
    if len(set(ids)) != len(ids):
        raise InputsError("a line is named twice (one line, one restatement)")
    hosts = [e["host_line_id"] for e in rets]
    if len(set(hosts)) != len(hosts):
        raise InputsError("a plaster face has two return-paint lines (one per face)")
    keys = [e["element_id"] for e in rets] + [b["element_id"] for b in bands]
    if len(set(keys)) != len(keys):
        raise InputsError("an added element id is named twice")
    bk = [(b["host_line_id"], b["item_code"]) for b in bands]
    if len(set(bk)) != len(bk):
        raise InputsError("a room line has two bands of one code")
    return dict(doc, _sources=srcs, _restate=res, _returns=rets, _bands=bands)


# ================================================================================================ lines
def _rec(srcs, **kw):
    return dict({"policy": "FINISH_GATE_B_V2", "tasks": [s["task"] for s in srcs],
                 "ledgers": [s["file"] for s in srcs], "ledger_sha256": [s["sha256"] for s in srcs],
                 "merge_commits": [s["merge_commit"] for s in srcs], "checker_runs": [s["checker_run"] for s in srcs],
                 "rule_id": RULE_ID, "rule_version": RULE_VERSION, "release_status": "NOT RELEASED"}, **kw)


_state = A3069._state


def _host(by, lid, eh, w):
    h = by.get(lid)
    if h is None:
        raise InputsError(f"{w}: host {lid} is not a candidate line (stale map)")
    if h["item_code"] != eh["item_code"] or h["unit"] != UNIT:
        raise InputsError(f"{w}: host {lid} is {h['item_code']} {h['unit']}, not {eh['item_code']} m2")
    if eh.get("element_id") and (h.get("location") or {}).get("element_id") != eh["element_id"]:
        raise InputsError(f"{w}: host {lid} element is not {eh['element_id']!r}")
    if line_class(h) != eh["class"]:
        raise InputsError(f"{w}: host {lid} is {line_class(h)}, the ledger read {eh['class']}")
    s = _state(h)
    if "value" in eh:
        v = eh["value"]
        if (v is None) != (s[0] == "BLANK") or (v is not None and (s[0] != "VALUE" or abs(s[1] - v) > TOL)):
            raise InputsError(f"{w}: host {lid} is {s}, the ledger read {v}")
    if eh.get("low") is not None and (s[0] != "RANGE" or abs(s[1][0] - eh["low"]) > TOL or
                                      abs(s[1][1] - eh["high"]) > TOL):
        raise InputsError(f"{w}: host {lid} is {s}, the ledger read {eh['low']} .. {eh['high']}")
    return h


def _assert_before(b, e):
    w = f"BOUND {e['line_id']}"
    if b is None:
        raise InputsError(f"{w}: not a candidate line (stale map)")
    if b["item_code"] != e["item_code"] or b["unit"] != UNIT or line_class(b) != "HELD":
        raise InputsError(f"{w}: candidate line is {b['item_code']} {b['unit']} {line_class(b)}, not a HELD "
                          f"{e['item_code']} m2 line")
    s, ex = _state(b), e["expect"]
    if s[0] != "RANGE" or abs(s[1][0] - ex["low"]) > TOL or abs(s[1][1] - ex["high"]) > TOL:
        raise InputsError(f"{w}: the ledger started from {ex['low']} .. {ex['high']}, the candidate is {s} "
                          f"(R-T717-1 (a))")
    if (ex.get("element_id") and (b.get("location") or {}).get("element_id") != ex["element_id"]):
        raise InputsError(f"{w}: element is not {ex['element_id']!r}")


def _restate(b, e, srcs):
    ln = copy.deepcopy(b)
    was = {"evidence_state": b["evidence_state"], "measured_net": b.get("measured_net"),
           "bounded_range": b.get("bounded_range"), "rfi": b.get("rfi"),
           "formula": (b.get("calculation") or {}).get("formula"), "class": line_class(b)}
    lo, hi = _r(e["after"]["low"]), _r(e["after"]["high"])
    open_ = e["still_open"] if isinstance(e["still_open"], str) else "; ".join(e["still_open"])
    ln["evidence_state"], ln["measured_net"], ln["gross"] = BOUNDED, None, None
    ln["bounded_range"] = {"low": lo, "high": hi, "basis": e["basis"][:200]}
    ln["rfi"] = {"question": f"open: {open_}"[:400], "blocks": [b["line_id"]]}
    cor = e.get("correction")
    head = f"HELD (BOUNDED) {_fmt(lo)} .. {_fmt(hi)} m2"
    ln["calculation"] = dict(ln["calculation"], formula=(
        f"{METHOD}: {head} = {e['basis']}"
        + (f"; correction {cor['finding']} {cor['delta_m2']} m2 on both ends ({cor.get('why')})" if cor else "")
        + f"; open: {open_}")[:1500])
    inp = ln["calculation"]["inputs"] = dict(ln["calculation"].get("inputs") or {})
    inp[REC_KEY] = _rec(srcs, piece=P_FIN, action="BOUND", was=was, after={"low": lo, "high": hi},
                        ledger_after=list(e["ledger_after"]), correction=cor, basis=e["basis"][:600],
                        evidence_status=e["status"], still_open=open_[:600], map_row=e.get("map_row"))
    A305._note(ln, f"{METHOD}: {head[:300]} (was {A302._q(A30._qty(b)) or 'blank'}); NOT RELEASED")
    return A3063._fin(ln)


def _common(src, item_code, eid, physical, formula, rec, srcs):
    loc = src.get("location") or {}
    return dict(project_id=src["project"]["project_id"], revision_set_sha256=src["project"]["revision_set_sha256"],
                item_code=item_code, unit=UNIT, element_id=eid, floor=loc.get("floor"), room_id=loc.get("room_id"),
                room_name_en=loc.get("room_name_en"), room_name_ar=loc.get("room_name_ar"),
                physical_element=physical, formula=formula[:1500],
                inputs={REC_KEY: rec, "evidence_status": rec["evidence_status"]["status"]},
                documents=copy.deepcopy(src["source"]["documents"]), geometry_source=src["source"]["geometry_source"],
                geometry_confidence=src["source"]["geometry_confidence"], rule_id=RULE_ID, rule_version=RULE_VERSION,
                material_state="PROJECT_OWNER_FACT")


def _return_line(src, e, srcs):
    from engine.source import boq_line as BL
    af = e["after"]
    rec = _rec(srcs, piece=P_RET, action=af["kind"], evidence_status=e["status"], host_line_id=src["line_id"],
               face_id=e["face_id"], flag=e.get("flag"), basis=e["basis"][:600], still_open=e["still_open"][:600],
               map_row=e.get("map_row"))
    flag = f"; FLAG {e['flag']}" if e.get("flag") else ""
    if af["kind"] == "BLANK":
        f = (f"{METHOD}: return paint on the plastered return face {e['face_id']} (R-T709-4) = HELD blank (never 0): "
             f"the plaster face itself is blank ({e['still_open']}){flag}")
        c = _common(src, PAINT, e["element_id"], "paint on a plastered opening return face (jambs + head)", f, rec,
                    srcs)
        ln = BL.make_line(evidence_state=BLANK, rfi={"question": f"open: {e['still_open']}"[:400],
                                                     "blocks": [src["line_id"]]},
                          notes=f"beside {PLASTER} {src['line_id']} (its return face); HELD blank, never 0; "
                                f"NOT RELEASED", **c)
    else:
        f = (f"{METHOD}: return paint on the plastered return face {e['face_id']} (R-T709-4) = HELD (BOUNDED) "
             f"0 .. {_fmt(af['high'])} m2: high = the face's plaster m2 on {src['line_id']}; low 0 = the frame / "
             f"casing over the whole jamb depth (printed nowhere: {e['still_open']}){flag}")
        c = _common(src, PAINT, e["element_id"], "paint on a plastered opening return face (jambs + head)", f, rec,
                    srcs)
        ln = BL.make_line(evidence_state=BOUNDED,
                          bounded_range={"low": 0.0, "high": _r(af["high"]),
                                         "basis": f"frame-covered extreme 0 .. plaster face {_fmt(af['high'])}"},
                          rfi={"question": f"open: {e['still_open']}"[:400], "blocks": [src["line_id"]]},
                          notes=f"beside {PLASTER} {src['line_id']} (its return face; never summed into a room paint "
                                f"line); HELD bounded, a range, never a picked point{flag}; NOT RELEASED", **c)
    return A3046._fin(ln)


def _band_line(src, b, srcs):
    from engine.source import boq_line as BL
    lo, hi = b["low"], b["high"]
    bot, top = b["levels_m"]
    terms = (f"run {b['run_m']} m x ({top} - {bot}) m" + (f" - landing piece <= {b['low_deduction_max_m2']} m2 (low)"
                                                          if b.get("low_deduction_max_m2") else "")
             + (f" + returns {b['returns_lm']} lm (high)" if b.get("returns_lm") else ""))
    rec = _rec(srcs, piece=P_BAND, action="BOUND", evidence_status=b["status"], host_line_id=src["line_id"],
               terms=terms, levels_m=list(b["levels_m"]), run_m=b["run_m"], returns_lm=b.get("returns_lm"),
               low_deduction_max_m2=b.get("low_deduction_max_m2"), still_open=b["still_open"][:600],
               map_row=b.get("map_row"))
    what = "plaster" if b["item_code"] == PLASTER else "paint"
    f = (f"{METHOD}: double-height stairwell band ({what}) on the wall that runs through the slab-free well "
         f"(R-T709-1; void V-01, T-719): {terms} = {_fmt(lo)} .. {_fmt(hi)} m2; beside the room line {src['line_id']} "
         f"(it stops at its own {'soffit' if what == 'plaster' else 'ceiling'}; never summed into it)")
    c = _common(src, b["item_code"], b["element_id"], f"{what} band of a wall through a double-height stairwell, "
                "between the lower room's top and the upper floor", f, rec, srcs)
    ln = BL.make_line(evidence_state=BOUNDED, bounded_range={"low": lo, "high": hi, "basis": b["still_open"][:200]},
                      rfi={"question": f"open: {b['still_open']}"[:400], "blocks": [src["line_id"]]},
                      notes=f"beside {b['item_code']} {src['line_id']} (never summed into it); HELD bounded; a range, "
                            f"never a picked point; NOT RELEASED", **c)
    return A3046._fin(ln)


def changes_for(doc, prev):
    """-> (changes, log): FIN_RESTATE on the named lines, then RETURN_PAINT and DH_BAND lines beside their hosts."""
    if not doc:
        return [], {"piece": "T717", "state": "NO_PROJECT_INPUT"}
    if any(((ln.get("calculation") or {}).get("inputs") or {}).get(REC_KEY) for ln in prev):
        raise InputsError("the candidate already carries V3.0.74 records (applied once)")
    by = {ln["line_id"]: ln for ln in prev}
    eids = {(ln.get("location") or {}).get("element_id") for ln in prev}
    S = doc["_sources"]
    changes = []
    log = {"piece": "T717", "state": "RUN", "restated": 0, "returns": {"BOUND": 0, "BLANK": 0, "flagged": 0},
           "bands": 0, "sources": [{k: s[k] for k in ("task", "file", "sha256", "merge_commit")}
                                   for s in doc["sources"]]}
    for e in doc["_restate"]:
        b = by.get(e["line_id"])
        _assert_before(b, e)
        srcs = [S[t] for t in e["source_tasks"]]
        after = _restate(b, e, srcs)
        log["restated"] += 1
        q = A30._qty(after)
        changes.append(A305._change(P_FIN, "CHANGE", b, after, step="BOUND", evidence_status="HELD",
                                    held=[{"what": e["line_id"], "why": after["rfi"]["question"],
                                           "range": [q["low"], q["high"]]}],
                                    verification={"task": " + ".join(e["source_tasks"]),
                                                  "merge_commits": [s["merge_commit"] for s in srcs]}))
    new_ids = set()
    for e in doc["_returns"]:
        w = f"RETURN {e['face_id']}"
        src = _host(by, e["host_line_id"], dict(e["expect_host"], element_id=e["face_id"]), w)
        if e["element_id"] in eids:
            raise InputsError(f"{w}: the candidate already carries {e['element_id']}")
        srcs = [S[t] for t in e["source_tasks"]]
        ln = _return_line(src, e, srcs)
        if ln["line_id"] in by or ln["line_id"] in new_ids:
            raise InputsError(f"{w}: line id {ln['line_id']} is already a line")
        new_ids.add(ln["line_id"])
        log["returns"][e["after"]["kind"]] += 1
        log["returns"]["flagged"] += bool(e.get("flag"))
        q = A30._qty(ln)
        changes.append(A305._change(P_RET, "ADD", None, ln, step=e["after"]["kind"], evidence_status="HELD",
                                    held=[{"what": e["element_id"], "why": e["still_open"],
                                           "range": [q["low"], q["high"]] if q["low"] is not None else None}],
                                    verification={"task": " + ".join(e["source_tasks"]),
                                                  "merge_commits": [s["merge_commit"] for s in srcs]}))
    for bd in doc["_bands"]:
        w = f"band {bd['element_id']}"
        src = _host(by, bd["host_line_id"], bd["expect_host"], w)
        if line_class(src) == "EXCLUDED":
            raise InputsError(f"{w}: an excluded room line carries no band")
        if bd["element_id"] in eids:
            raise InputsError(f"{w}: the candidate already carries this band")
        srcs = [S[t] for t in bd["source_tasks"]]
        ln = _band_line(src, bd, srcs)
        if ln["line_id"] in by or ln["line_id"] in new_ids:
            raise InputsError(f"{w}: line id {ln['line_id']} is already a line")
        new_ids.add(ln["line_id"])
        log["bands"] += 1
        changes.append(A305._change(P_BAND, "ADD", None, ln, step="BOUND", evidence_status="HELD",
                                    held=[{"what": bd["element_id"], "why": bd["still_open"],
                                           "range": [bd["low"], bd["high"]]}],
                                    verification={"task": " + ".join(bd["source_tasks"]),
                                                  "merge_commits": [s["merge_commit"] for s in srcs]}))
    log["lines"] = len(changes)
    return changes, log


# ================================================================================================ checks
def expected_totals(t0, changes):
    return A3068.expected_totals(t0, changes)


def check_totals(t0, t1, changes, expect=None):
    """only FIN.PLASTER|m2 / FIN.PAINT|m2 move, each exactly by the changes; released never moves (R-T717-1 (e))."""
    moved = {k for k in set(t0) | set(t1) if t0.get(k) != t1.get(k)}
    bad = sorted(k for k in moved if k not in (f"{c}|{UNIT}" for c in CODES))
    if bad:
        raise ValueError(f"{METHOD}: totals moved outside FIN.PLASTER / FIN.PAINT: {bad}")
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
        if abs(a["released"] - (t0.get(k) or {}).get("released", 0.0)) > TOT_TOL:
            raise ValueError(f"{METHOD}: {k} released moved")
        if expect and k in expect:
            for f, v in expect[k].items():
                if abs(a[f] - v) > TOT_TOL:
                    raise ValueError(f"{METHOD}: {k} {f} {a[f]} is not the inputs' {v}")
        out[k] = {"base": t0.get(k), "v3_0_74": a, "view": A3058_view(a)}
    return out


def A3058_view(a):
    from engine.source import arch_v3058 as A3058
    return A3058.total_view(a)


def check_finishes(lines, before=None):
    """on finished lines: every V3.0.74 record is in the state its piece names; never VERIFIED, never a value; a
    return / band line binds its host by id (same room, one per host and code); with `before`: a restated line was
    HELD. -> summary"""
    by = {ln["line_id"]: ln for ln in lines}
    out = {"BOUND": 0, "return_bound": 0, "return_blank": 0, "band": 0}
    hosts = set()
    old = {x["line_id"]: x for x in before} if before is not None else None
    for ln in lines:
        rec = ((ln.get("calculation") or {}).get("inputs") or {}).get(REC_KEY)
        eid = (ln.get("location") or {}).get("element_id") or ""
        if not rec:
            if (ln.get("rule") or {}).get("rule_id") == RULE_ID:
                raise ValueError(f"{METHOD}: {ln['line_id']} a V3.0.74 line with no V3.0.74 record")
            continue
        s = _state(ln)
        if (rec.get("evidence_status") or {}).get("status") != "HELD" or ln["item_code"] not in CODES or \
                ln.get("measured_net") is not None:
            raise ValueError(f"{METHOD}: {ln['line_id']} a V3.0.74 line is a HELD FIN line with no value")
        if rec["piece"] == P_FIN:
            ok = rec["was"]["class"] == "HELD" and s[0] == "RANGE" and 0 < s[1][0] < s[1][1] and \
                bool((ln.get("rfi") or {}).get("question"))
            if old is not None:
                ok = ok and ln["line_id"] in old and line_class(old[ln["line_id"]]) == "HELD"
            if not ok:
                raise ValueError(f"{METHOD}: {ln['line_id']} a restated line is not HELD bounded")
            out["BOUND"] += 1
            continue
        h = by.get(rec["host_line_id"])
        if h is None or (h.get("location") or {}).get("floor") != (ln.get("location") or {}).get("floor"):
            raise ValueError(f"{METHOD}: {ln['line_id']} binds no host line on its floor")
        key = (rec["host_line_id"], ln["item_code"], rec["piece"])
        if key in hosts:
            raise ValueError(f"{METHOD}: {ln['line_id']} a second {rec['piece']} line on {rec['host_line_id']}")
        hosts.add(key)
        if rec["piece"] == P_RET:
            if ln["item_code"] != PAINT or h["item_code"] != PLASTER or not eid.endswith(RET_SUFFIX) or \
                    eid != rec["face_id"] + RET_SUFFIX or (h.get("location") or {}).get("element_id") != rec["face_id"]:
                raise ValueError(f"{METHOD}: {ln['line_id']} a return-paint line binds no plaster face of its id")
            hs = _state(h)
            if s[0] == "BLANK" and hs[0] == "BLANK":
                out["return_blank"] += 1
            elif s[0] == "RANGE" and s[1][0] == 0.0 and hs[0] == "VALUE" and abs(s[1][1] - hs[1]) <= TOL:
                out["return_bound"] += 1
            else:
                raise ValueError(f"{METHOD}: {ln['line_id']} a return-paint line is not 0 .. its face or blank")
        elif rec["piece"] == P_BAND:
            if h["item_code"] != ln["item_code"] or not (s[0] == "RANGE" and 0 < s[1][0] <= s[1][1]):
                raise ValueError(f"{METHOD}: {ln['line_id']} a band line is not HELD bounded on its own code's host")
            out["band"] += 1
        else:
            raise ValueError(f"{METHOD}: {ln['line_id']} unknown piece {rec['piece']}")
    return out


def census(lines, codes=CODES):
    """per code: released n / m2, bounded n / low .. high, blank n, excluded n (index convention, A304 code totals
    semantics; a range with a 0 low counts bounded)."""
    out = {}
    for c in codes:
        z = {"released": 0, "released_m2": 0.0, "bounded": 0, "low": 0.0, "high": 0.0, "blank": 0, "excluded": 0}
        for ln in lines:
            if ln["item_code"] != c or ln["unit"] != UNIT:
                continue
            k = line_class(ln)
            s = _state(ln)
            if k == "EXCLUDED" or s[0] == "NA":
                z["excluded"] += 1
            elif k == "RELEASED":
                z["released"] += 1
                z["released_m2"] += s[1] if s[0] == "VALUE" else 0.0
            elif s[0] == "RANGE":
                z["bounded"] += 1
                z["low"] += s[1][0]
                z["high"] += s[1][1]
            elif s[0] == "VALUE":          # a HELD point (held low = high)
                z["bounded"] += 1
                z["low"] += s[1]
                z["high"] += s[1]
            else:
                z["blank"] += 1
        out[c] = {k: (_r(v) if isinstance(v, float) else v) for k, v in z.items()}
    return out


# ================================================================================================ integrate / write
def integrate(prev, changes, for_lead=()):
    """-> (V3.0.74 lines, identity). Changed lines replace their candidate line in place, added lines follow the base;
    every other candidate line byte-identical (asserted); the earlier state checks re-run (V3.0.64 .. V3.0.67 / V3.0.70
    / V3.0.73 concrete, V3.0.67 / V3.0.71 lintels, V3.0.68 / V3.0.72 masonry, V3.0.69 finishes): nothing of theirs may
    move."""
    sid = {ln["line_id"]: i for i, ln in enumerate(prev)}
    out, repl, add = list(prev), set(), []
    for c in changes:
        a = c["after"]
        if a["item_code"] not in CODES or a["unit"] != UNIT:
            raise ValueError(f"{METHOD}: {a['item_code']} is not a code this version may touch")
        if c["action"] == "CHANGE":
            i = sid.get(a["line_id"])
            if i is None or a["line_id"] in repl or c["piece"] != P_FIN:
                raise ValueError(f"{METHOD}: a changed line is not a candidate line, changes twice or is not a "
                                 f"restatement")
            out[i] = a
            repl.add(a["line_id"])
        elif c["action"] == "ADD":
            if c["piece"] not in (P_RET, P_BAND) or a["line_id"] in sid:
                raise ValueError(f"{METHOD}: only return-paint and band lines are added, never over a candidate id")
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
    ident = {"base_lines": len(prev), "v3_0_74_lines": len(out), "v3_0_74_rows": len(changes), "replaced": len(repl),
             "added": len(add), "concrete_v3_0_64": A3064.check_concrete(out),
             "concrete_v3_0_65": A3065.check_concrete(out), "concrete_v3_0_66": A3066.check_concrete(out),
             "concrete_v3_0_67": A3067.check_concrete(out, prev), "lintels_v3_0_67": A3067.check_lintels(out),
             "masonry_v3_0_68": A3068.check_masonry(out), "finishes_v3_0_69": A3069.check_finishes(out),
             "concrete_v3_0_70": A3070.check_concrete(out, prev), "lintels_v3_0_71": A3071.check_lintels(out, prev),
             "masonry_v3_0_72": A3072.check_masonry(out, prev), "concrete_v3_0_73": A3073.check_concrete(out, prev),
             "finishes": check_finishes(out, prev),
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
                     "before_released_v2_9": b29, "before_base": A30._qty(c.get("before")),
                     "after_v3_0_74": A30._qty(a), "class": [None if c.get("before") is None else
                                                            line_class(c["before"]), line_class(a)],
                     "evidence_status": c.get("evidence_status"), "still_held": c.get("held"),
                     "flag": rec.get("flag"), "correction": rec.get("correction"), "map_row": rec.get("map_row"),
                     "record": {k: v for k, v in rec.items() if k not in ("ledger_sha256", "was")},
                     "release_status": "NOT RELEASED",
                     "owner_manual_method": PIECES[c["piece"]]["owner_manual_method"],
                     "drawing_derived_method": PIECES[c["piece"]]["drawing_method"],
                     "verification": c.get("verification") or {}, "rollback": ROLLBACK})
    return rows


LEDGER_CSV = ("version", "piece", "action", "change", "line_id", "item_code", "floor", "element_id", "unit", "host",
              "v2_9", "base", "v3_0_74", "class", "flag", "evidence_status", "verification")
DIFF_CSV = ("line_id", "item_code", "floor", "element_id", "unit", "vs_base", "vs_released_v2_9", "v2_9", "base",
            "v3_0_74")


def ledger_csv(rows):
    def q(x):
        return A302._q(x) if x and (x.get("value") is not None or x.get("low") is not None or x.get("state")) else ""
    return A305._csv([{"version": r["version"], "piece": r["piece"], "action": r["action"], "change": r["change"],
                       "line_id": r["line_id"], "item_code": r["item_code"], "floor": r.get("floor") or "",
                       "element_id": r.get("element_id") or "", "unit": r["unit"], "host": r.get("host_line_id") or "",
                       "v2_9": q(r.get("before_released_v2_9")), "base": q(r.get("before_base")),
                       "v3_0_74": q(r.get("after_v3_0_74")), "class": " -> ".join(str(x) for x in r["class"]),
                       "flag": r.get("flag") or "", "evidence_status": r["evidence_status"],
                       "verification": f"{r['verification'].get('task')} "
                                       f"{' '.join(x[:8] for x in r['verification'].get('merge_commits') or ())}"}
                      for r in rows], LEDGER_CSV)


def diff_rows(prev, new, released_lines=None):
    return [dict({k: v for k, v in d.items() if k != "v3_0_73"}, v3_0_74=d["v3_0_73"])
            for d in A3073.diff_rows(prev, new, released_lines)]


def write(out, prev, changes, log, released_lines=None, for_lead=(), expect_totals=None):
    """the V3_0_74_* files beside the base candidate's files. -> (file names, identity, ledger)."""
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
    ident = dict(ident, diff=dsum, fin_census_before=census(prev), fin_census_after=census(new))
    moved = check_totals(A304.code_totals(prev), A304.code_totals(new), changes, expect_totals)
    led = {"schema": LEDGER_SCHEMA, "method": METHOD, "extends": EXTENDS, "candidate": CANDIDATE,
           "base": A30.BASE_METHOD, "released": A30.RELEASED_METHOD, "released_default": False, "rows": rows,
           "summary": log, "waiting_pieces": WAITING, "integration_package": True}
    run = {"method": METHOD, "policy": POLICY_ID, "extends": EXTENDS, "candidate": CANDIDATE,
           "base_method": A30.BASE_METHOD, "released_method": A30.RELEASED_METHOD, "released_default": False,
           "rollback": ROLLBACK, "identity": ident, "pieces": PIECES, "piece_logs": [log],
           "totals_moved_by_code": moved, "waiting_pieces": WAITING}
    files = {"V3_0_74_BOQ_LINES.json": BL.dumps(new),
             "V3_0_74_BOQ_LINES.csv": A30._lines_csv(new),
             "V3_0_74_INTEGRATION_LEDGER.json": A30._j(led),
             "V3_0_74_INTEGRATION_LEDGER.csv": ledger_csv(rows),
             "V3_0_74_DIFF.csv": A305._csv(diff, DIFF_CSV),
             "V3_0_74_RUN.json": A30._j(run)}
    for name, text in files.items():
        (out / name).write_text(text, encoding="utf-8")
    return sorted(files), ident, led


def policy_record():
    return {"method": METHOD, "extends": EXTENDS, "pieces": sorted(PIECES), "inputs_schema": INPUTS_SCHEMA,
            "released_default": False, "rollback": ROLLBACK, "codes": list(CODES)}


__all__ = ["METHOD", "PIECES", "WAITING", "DEFAULT_GUARD_CLASS", "INPUTS_SCHEMA", "CODES", "load_inputs",
           "changes_for", "band_figure", "corrected", "census", "expected_totals", "check_totals", "check_finishes",
           "integrate", "ledger_rows", "diff_rows", "write", "InputsError", "line_class"]
