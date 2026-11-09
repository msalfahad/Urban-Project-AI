"""ARCH_TAKEOFF_V3.0.61 (T-563, lane I, PLASTER_HEIGHT_V1_WIRING of the T-558 WIRING MANIFEST V6): the SAME opt-in BOQ
candidate as ARCH_TAKEOFF_V3.0 .. V3.0.60 (engine.source.arch_v30, arch_v301 .. arch_v3060), extended with ONE piece
from Checker-merged ledgers:

  PLASTER_HEIGHT  a dry FIN.PLASTER wall line whose candidate value was taken at the PAINT height (the finished
                  ceiling G1, shared code path: T-552 / T-556 ENGINE_WRONG) is restated at its OWN height, the soffit
                  of the structural slab / roof over the room (owner Q-72; Q-14: storey interval - build-up of the
                  floor above - slab), net of every hole re-cut at that height (Q-73; a head above G1 now deducts in
                  full: W03) and of the crossing-beam end sections (Q-57): PLASTER_HEIGHT_METHOD_V1 (R-T556-1, the
                  merged T-556 table). Every such line has some face under a ROOF whose build-up is not printed
                  (D-39 / DCR-6, designer): it is HELD (BOUNDED_EXPOSURE) at the T-556 low / high, the RFI named,
                  never a released value and never 0. A RELEASED line therefore leaves the released total (the
                  4 released lines 217.2081 m2 -> HELD 262.01799 .. 262.05199 m2); a blank line gains its bound.

R-T563-1 (every villa; wires R-T556-1 + R-T558-1; owner Q-72, Q-73, Q-57, UP-QTY-STATUS-001; ELEMENT_REGISTER 'WALL
PLASTER HEIGHT vs PAINT HEIGHT'): (a) a restatement binds to the line as the candidate carries it (item, element, unit,
class, released net or held range to 1e-6) and stops on a stale line; (b) the new range is the merged method's, low <=
high, both > 0, and a line whose room has a face under an unprinted roof build-up is never released (refused);
(c) plaster and paint are separate layers: the room's paint line is named, must exist in the same room and is never
changed by this version (a FIN.PAINT change is refused; asserted byte-identical); (d) the stale paint-height list
(gross, deductions and the earlier records that close it, NET_RECORDS) is kept in the record, not on the line: a bounded line prints its range, never a gross at another
layer's height; (e) nothing else moves.

Nothing else moves: every V3.0.60 line not named by the inputs is byte-identical (asserted); every code total
(A304.code_totals) is unchanged except FIN.PLASTER|m2, whose released total falls by exactly the released lines
restated and whose held range rises by exactly the new bounds less the old (asserted). Files: V3_0_61_BOQ_LINES.json /
.csv, V3_0_61_INTEGRATION_LEDGER.json / .csv, V3_0_61_DIFF.csv, V3_0_61_RUN.json. Nothing here names a project, a sheet,
a layer or a coordinate.
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
from engine.source import arch_v3036 as A3036
from engine.source import arch_v3043 as A3043
from engine.source import arch_v3060 as A3060

DEFAULT_GUARD_CLASS = "TOOLING"          # T-212: re-books a Checker-merged method table onto candidate lines
METHOD = "ARCH_TAKEOFF_V3.0.61"
EXTENDS = A3060.METHOD
CANDIDATE = A30.METHOD
POLICY_ID = "URBAN_BOQ_T563_ARCH_V3_0_61"
INPUTS_SCHEMA = "URBAN_V3061_INPUTS_V1"
LEDGER_SCHEMA = "URBAN_V3061_INTEGRATION_LEDGER_V1"
ROLLBACK = A30.ROLLBACK
InputsError = A3031.InputsError
_r = A3018._r
_fmt = A3030._fmt
RULE_ID, RULE_VERSION = "R-T563-1", "T-563"
REC_KEY = "plaster_height_v3061"
P_PH = "PLASTER_HEIGHT"
ACTIONS = ("PLASTER_HEIGHT",)
PLASTER, PAINT = "FIN.PLASTER", "FIN.PAINT"
CODE_KEY = f"{PLASTER}|m2"
HELD_STATE = "BOUNDED_EXPOSURE"
VALUED_STATES = A3036.VALUED_STATES
EXCLUDED = ("EXCLUDED_WITH_REASON", "NOT_APPLICABLE_WITH_EVIDENCE")
CLASSES = ("RELEASED", "HELD")
BIND_TOL = 1e-6
TOT_TOL = 1e-4                           # code totals are rounded 6; a sum of 11 lines within 1e-4 m2
MAX_Q = 2000.0                           # a room's wall plaster above it is a unit slip
MAX_RISE = 1.0                           # a restated value more than double the old one is refused (unit / scope slip)
LINE_ID_RE = re.compile(r"^L-[0-9a-f]{20}$")
# earlier versions' records whose own check presupposes a VALUED line (gross - list = net, V3.0.36 check_lists): on a
# line restated to HELD they describe the superseded paint-height figure, so they move into this version's 'was'
# record (kept, never deleted) and leave the line's live inputs
NET_RECORDS = ("deduction_listing_v3036",)

PIECES = {
    P_PH: {"module": "engine/source/arch_v3061.py (a dry plaster line restated at its own height, slab / roof "
                     "soffit, HELD at the merged method's bounds; paint untouched)",
           "policy": "PLASTER_HEIGHT_V1_WIRING", "rule_id": "R-T556-1 + R-T558-1 (R-T563-1)",
           "owner_rules": ["Q-72 (plaster to the structural slab / roof underside; paint to the finished ceiling)",
                           "Q-14 (plaster height = interval - floor build-up above - slab)",
                           "Q-73 (full deduction of every actual opening)", "Q-57 (beam sides / soffit are ceiling)",
                           "UP-QTY-STATUS-001 (held is blank, never 0)"],
           "owner_manual_method": "plaster face = wall length x (storey interval - build-up of the floor above - slab) "
                                  "less every opening and crossing-beam end; paint stays at the finished ceiling G1",
           "drawing_method": "the merged T-556 table (R-T556-1): T-128 r3 face lengths, A-A section intervals 4.50 / "
                             "4.20, T-214 floor build-up 0.05, slab 0.16; faces under a roof at the drawn-section "
                             "scenario (roof build-up not printed, D-39 / DCR-6); T-292 opening ledger re-cut at H"},
}
WAITING = dict(A3060.WAITING)
WAITING.update({
    "T563_ROOF_BUILDUP": "every restated line keeps its RFI: the roof build-up over the room (D-39 / DCR-6, designer) "
                         "-> the roof-face share of each plaster line becomes DRAWING-CONFIRMED; until then HELD",
    "T563_OTHER_DRY_PLASTER": "dry FIN.PLASTER lines outside the 11 T-556 rooms are not restated by this version (the "
                              "T-556 table names these 11; any other dry room is a next method run, never a guess)",
})


# ================================================================================================ inputs
def _need(s, keys, where):
    for k in keys:
        if s.get(k) in (None, ""):
            raise InputsError(f"{where}: missing {k}")


def _num(x, where, top=MAX_Q):
    if isinstance(x, bool) or not isinstance(x, (int, float)) or x != x:
        raise InputsError(f"{where}: not a number ({x!r})")
    if x <= 0 or x > top:
        raise InputsError(f"{where}: {x} outside 0 .. {top} m2 (unit slip, sign or HELD-as-0)")
    return float(x)


def _entry(e, srcs):
    a = e.get("action")
    if a not in ACTIONS:
        raise InputsError(f"entry action {a!r}")
    w = f"{a} {e.get('line_id')}"
    if not isinstance(e.get("line_id"), str) or not LINE_ID_RE.match(e["line_id"]):
        raise InputsError(f"{w}: line id")
    A3043._tasks(e, srcs, w)
    _need(e, ("expect", "after", "basis", "why_held", "question", "paint_line_id", "room"), w)
    x = e["expect"]
    _need(x, ("item_code", "element_id", "unit", "class"), w)
    if x["item_code"] != PLASTER or x["unit"] != "m2":
        raise InputsError(f"{w}: {x['item_code']} {x['unit']} is not a code this version may change (FIN.PLASTER m2; "
                          "paint is its own layer)")
    if x["class"] not in CLASSES:
        raise InputsError(f"{w}: class {x['class']}")
    if x["class"] == "RELEASED":
        _num(x.get("measured_net"), f"{w} expect net")
    lo, hi = _num(e["after"].get("low"), f"{w} low"), _num(e["after"].get("high"), f"{w} high")
    if lo > hi + 1e-9:
        raise InputsError(f"{w}: low {lo} > high {hi}")
    if e["after"].get("state") not in (None, HELD_STATE):
        raise InputsError(f"{w}: after state {e['after']['state']}: a line with an unprinted roof build-up is HELD "
                          "(never released)")
    if not str(e["paint_line_id"]).startswith("L-") or e["paint_line_id"] == e["line_id"]:
        raise InputsError(f"{w}: paint line {e['paint_line_id']!r}")
    return dict(e)


def load_inputs(doc, project_id=None):
    """URBAN_V3061_INPUTS_V1 -> the validated doc.
    {"schema", "project_id", "sources": [{"task", "file", "sha256", "merge_commit", "checker_run"}],
     "expect_totals": {released_before_m2, released_after_bound_m2, ...} (optional, asserted when present),
     "entries": [{"action": "PLASTER_HEIGHT", "line_id", "source_tasks", "room",
                  "expect" {item_code, element_id, unit, class RELEASED | HELD, measured_net | low / high},
                  "after" {low, high}, "basis" {...T-556 row...}, "why_held", "question", "paint_line_id",
                  "remeasure_beside" (optional)}]}"""
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
    seen, paints = set(), set()
    for e in ents:
        if e["line_id"] in seen:
            raise InputsError(f"{e['line_id']}: named twice (one line, one restatement)")
        if e["paint_line_id"] in paints:
            raise InputsError(f"{e['paint_line_id']}: one paint line named for two plaster lines")
        seen.add(e["line_id"])
        paints.add(e["paint_line_id"])
    if seen & paints:
        raise InputsError("a line is both a restated plaster line and a paint pair")
    return dict(doc, _sources=srcs, _entries=ents)


# ================================================================================================ lines
def line_class(ln):
    """RELEASED (a valued quantity state with a net) / HELD / EXCLUDED: the T-469 class."""
    if ln["evidence_state"] in EXCLUDED:
        return "EXCLUDED"
    if ln["evidence_state"] in VALUED_STATES and ln.get("measured_net") is not None:
        return "RELEASED"
    return "HELD"


def _range(ln):
    b = ln.get("bounded_range") or {}
    lo, hi = b.get("low"), b.get("high")
    return (float(lo), float(hi)) if isinstance(lo, (int, float)) and isinstance(hi, (int, float)) else None


def _assert_bound(b, e):
    x = e["expect"]
    w = f"{e['action']} {e['line_id']}"
    if b is None:
        raise InputsError(f"{w}: not in the candidate (stale binding)")
    loc = b.get("location") or {}
    ok = (b["item_code"] == x["item_code"] and loc.get("element_id") == x["element_id"] and b["unit"] == x["unit"]
          and line_class(b) == x["class"])
    if ok and x["class"] == "RELEASED":
        ok = abs(b["measured_net"] - x["measured_net"]) <= BIND_TOL
    if ok and x["class"] == "HELD" and ("low" in x or "high" in x):
        r = _range(b)
        if x.get("low") is None:
            ok = r is None
        else:
            ok = r is not None and abs(r[0] - x["low"]) <= BIND_TOL and abs(r[1] - x["high"]) <= BIND_TOL
    if not ok:
        raise InputsError(f"{w}: {b['item_code']} {loc.get('element_id')} {b['evidence_state']} net "
                          f"{b.get('measured_net')} range {_range(b)} is not the ledger's {x} (stale binding: re-read)")
    if x["class"] == "RELEASED" and e["after"]["high"] > b["measured_net"] * (1 + MAX_RISE):
        raise InputsError(f"{w}: {b['measured_net']} -> {e['after']['high']} m2 more than doubles (unit or scope slip)")


def _fin(ln):
    from engine.source import boq_line as BL
    return BL.validate(ln)


def _rec(srcs, **kw):
    return dict({"piece": P_PH, "policy": PIECES[P_PH]["policy"], "tasks": [s["task"] for s in srcs],
                 "ledgers": [s["file"] for s in srcs], "ledger_sha256": [s["sha256"] for s in srcs],
                 "merge_commits": [s["merge_commit"] for s in srcs], "checker_runs": [s["checker_run"] for s in srcs],
                 "rule_id": RULE_ID, "rule_version": RULE_VERSION, "release_status": "NOT RELEASED"}, **kw)


def _restate(b, e, srcs, paint):
    lo, hi = float(e["after"]["low"]), float(e["after"]["high"])
    bs = e["basis"]
    ln = copy.deepcopy(b)
    was = {"evidence_state": b["evidence_state"], "measured_net": b.get("measured_net"), "gross": b.get("gross"),
           "bounded_range": b.get("bounded_range"), "deductions": b.get("deductions") or [],
           "additions": b.get("additions") or [], "rfi": b.get("rfi"), "formula": (b.get("calculation") or {}).get(
               "formula"), "class": line_class(b), "height_basis": "PAINT height G1 (finished ceiling): ENGINE_WRONG "
                                                                  "for plaster (T-552 / T-556)"}
    ln["evidence_state"], ln["measured_net"], ln["gross"] = HELD_STATE, None, None
    ln["deductions"], ln["additions"] = [], []
    ln["bounded_range"] = {"low": _r(lo), "high": _r(hi),
                           "basis": f"PLASTER_HEIGHT_METHOD_V1 (R-T556-1): H to the slab / roof soffit; roof build-up "
                                    f"at the drawn-section scenario (D-39 / DCR-6)"[:200]}
    ln["rfi"] = {"question": e["question"][:400], "blocks": [b["line_id"]]}
    pt = (f"H floor {bs.get('H_floor_m')} / roof scenario {bs.get('H_roof_scenario_m')} m on face {bs.get('face_lm')} lm "
          f"(floor {bs.get('face_floor_lm')} + roof {bs.get('face_roof_lm')}); gross {bs.get('gross_m2')} - openings "
          f"{' .. '.join(bs.get('openings_m2') or [])} - beam ends {' .. '.join(bs.get('beam_ends_m2') or [])}")
    ln["calculation"] = dict(ln["calculation"], formula=(
        f"{METHOD}: HELD (BOUNDED) {_fmt(lo)} .. {_fmt(hi)} m2 = plaster at its own height (Q-72): {pt}; "
        f"{e['why_held']}")[:1500])
    inp = ln["calculation"]["inputs"] = dict(ln["calculation"].get("inputs") or {})
    was["records"] = {k: inp.pop(k) for k in NET_RECORDS if k in inp}
    inp[REC_KEY] = _rec(srcs, action="PLASTER_HEIGHT", room=e["room"], was=was, after={"low": _r(lo), "high": _r(hi)},
                        basis=bs, why_held=e["why_held"][:600], paint_line_id=paint["line_id"],
                        paint_line_sha256=A30.line_sha(paint), remeasure_beside=e.get("remeasure_beside"))
    A305._note(ln, f"{METHOD}: plaster at its own height (slab / roof soffit, Q-72), HELD {_fmt(lo)} .. {_fmt(hi)} m2 "
                   f"(was {A302._q(A30._qty(b))} at the paint height); paint line {paint['line_id']} unchanged; "
                   "NOT RELEASED")
    return _fin(ln)


def changes_for(doc, prev):
    """-> (changes, log)."""
    if not doc:
        return [], {"piece": "T563", "state": "NO_PROJECT_INPUT"}
    if any(((ln.get("calculation") or {}).get("inputs") or {}).get(REC_KEY) for ln in prev):
        raise InputsError("the candidate already carries V3.0.61 records (applied once)")
    by = {ln["line_id"]: ln for ln in prev}
    S = doc["_sources"]
    changes = []
    log = {"piece": "T563", "state": "RUN", "sources": doc["sources"], "by_action": {}, "lines": 0}
    for e in doc["_entries"]:
        b = by.get(e["line_id"])
        _assert_bound(b, e)
        p = by.get(e["paint_line_id"])
        if p is None or p["item_code"] != PAINT or (p.get("location") or {}).get("room_id") != \
                (b.get("location") or {}).get("room_id"):
            raise InputsError(f"{e['line_id']}: paint line {e['paint_line_id']} is not the room's FIN.PAINT line")
        srcs = [S[t] for t in e["source_tasks"]]
        after = _restate(b, e, srcs, p)
        changes.append(A305._change(P_PH, "CHANGE", b, after, drawing_reference="; ".join(s["file"] for s in srcs),
                                    held=[{"what": f"{e['room']} roof build-up", "why": e["why_held"][:300],
                                           "range": [after["bounded_range"]["low"], after["bounded_range"]["high"]],
                                           "scenario": "drawn-section 0.05 roof layer"}],
                                    downstream=[{"line_id": p["line_id"], "item_code": PAINT,
                                                 "reads": "the same room's wall faces at G1",
                                                 "v3_0_61": "UNCHANGED (paint stays at the finished ceiling)"}],
                                    verification=A3036._ver(srcs), evidence_status="HELD",
                                    codes=[P_PH], group=PLASTER, step=P_PH))
        log["by_action"]["PLASTER_HEIGHT"] = log["by_action"].get("PLASTER_HEIGHT", 0) + 1
    log["lines"] = len(changes)
    tot = doc.get("expect_totals")
    if tot:
        check_expect(changes, tot)
    return changes, log


# ================================================================================================ checks
def restated_sums(changes):
    rel = [c for c in changes if line_class(c["before"]) == "RELEASED"]
    return {"released_before_m2": _r(sum(c["before"]["measured_net"] for c in rel), 6),
            "released_after_bound_m2": [_r(sum(c["after"]["bounded_range"]["low"] for c in rel), 6),
                                        _r(sum(c["after"]["bounded_range"]["high"] for c in rel), 6)],
            "all_after_bound_m2": [_r(sum(c["after"]["bounded_range"]["low"] for c in changes), 6),
                                   _r(sum(c["after"]["bounded_range"]["high"] for c in changes), 6)],
            "released_lines": len(rel), "lines": len(changes)}


def check_expect(changes, tot):
    s = restated_sums(changes)
    want = {"released_before_m2": tot.get("released_before_m2"),
            "released_after_bound_m2": tot.get("released_after_bound_m2"),
            "all_after_bound_m2": tot.get("all_11_after_bound_m2")}
    for k, v in want.items():
        if v is None:
            continue
        got = s[k]
        bad = abs(got - v) > TOT_TOL if not isinstance(v, list) else any(abs(a - b) > TOT_TOL for a, b in zip(got, v))
        if bad:
            raise InputsError(f"{k}: {got} is not the manifest's {v}")
    return s


def check_plaster_height(lines, before=None):
    """on finished lines: every V3.0.61 plaster line is HELD (bounded, low <= high, no net, an RFI); its paint line
    exists in the same room; with `before`, every FIN.PAINT line is byte-identical and no plaster line went from HELD
    to RELEASED. -> summary."""
    by = {ln["line_id"]: ln for ln in lines}
    out = {"restated": 0, "released_before": 0, "paint_pairs_unchanged": 0}
    for ln in lines:
        rec = ((ln.get("calculation") or {}).get("inputs") or {}).get(REC_KEY)
        if not rec:
            continue
        r = _range(ln)
        if ln["item_code"] != PLASTER or ln["evidence_state"] != HELD_STATE or ln.get("measured_net") is not None or \
                r is None or r[0] > r[1] + 1e-9 or r[0] <= 0 or not (ln.get("rfi") or {}).get("question"):
            raise ValueError(f"{METHOD}: {ln['line_id']}: a restated plaster line is not HELD (bounded, RFI named)")
        p = by.get(rec.get("paint_line_id"))
        if p is None or p["item_code"] != PAINT or A30.line_sha(p) != rec.get("paint_line_sha256"):
            raise ValueError(f"{METHOD}: {ln['line_id']}: its paint line is missing or moved")
        out["restated"] += 1
        out["paint_pairs_unchanged"] += 1
        out["released_before"] += rec["was"]["class"] == "RELEASED"
    if before is not None:
        b = {x["line_id"]: x for x in before}
        for ln in lines:
            o = b.get(ln["line_id"])
            if o is None:
                continue
            if ln["item_code"] == PAINT and A30.line_sha(o) != A30.line_sha(ln):
                raise ValueError(f"{METHOD}: {ln['line_id']}: a paint line moved with the plaster (paint stays at G1)")
            if ln["item_code"] == PLASTER and line_class(o) == "HELD" and line_class(ln) == "RELEASED":
                raise ValueError(f"{METHOD}: {ln['line_id']}: a HELD plaster line was released")
    return out


def _bucket(ln):
    """the A304.code_totals bucket of a line: released / bounded / blocked."""
    q = A30._qty(ln)
    if q["value"] is not None and ln["evidence_state"] != "BLOCKED_RFI":
        return "released"
    return "bounded" if q["low"] is not None else "blocked"


def check_totals(t0, t1, changes):
    """only FIN.PLASTER|m2 moves: released down by the restated released nets; held range up by new - old bounds;
    line count the same; blocked count down by the blank lines that gained a bound."""
    moved = {k for k in set(t0) | set(t1) if t0.get(k) != t1.get(k)}
    if moved - {CODE_KEY}:
        raise ValueError(f"{METHOD}: totals moved outside {CODE_KEY}: {sorted(moved - {CODE_KEY})}")
    if not moved:
        return {}
    a, z = t0[CODE_KEY], t1[CODE_KEY]
    rel = sum(c["before"]["measured_net"] for c in changes if _bucket(c["before"]) == "released")
    d_lo = sum(c["after"]["bounded_range"]["low"] - (A30._qty(c["before"])["low"] or 0.0) for c in changes)
    d_hi = sum(c["after"]["bounded_range"]["high"] - (A30._qty(c["before"])["high"] or 0.0) for c in changes)
    newly_bounded = sum(1 for c in changes if _bucket(c["before"]) != "bounded")
    was_blocked = sum(1 for c in changes if _bucket(c["before"]) == "blocked")
    ok = (z["lines"] == a["lines"] and abs((a["released"] - z["released"]) - rel) <= TOT_TOL
          and abs((z["held_low"] - a["held_low"]) - d_lo) <= TOT_TOL
          and abs((z["held_high"] - a["held_high"]) - d_hi) <= TOT_TOL
          and z["bounded_lines"] - a["bounded_lines"] == newly_bounded
          and a["blocked_lines"] - z["blocked_lines"] == was_blocked)
    if not ok:
        raise ValueError(f"{METHOD}: {CODE_KEY} totals {a} -> {z} are not the restatement (released -{rel}, held "
                         f"+{d_lo} .. +{d_hi}, +{newly_bounded} bounded, -{was_blocked} blocked)")
    return {CODE_KEY: {"base": a, "v3_0_61": z}}


# ================================================================================================ integrate / write
def integrate(prev, changes, for_lead=()):
    """-> (V3.0.61 lines, identity). Changed lines replace their candidate line in place; every other candidate line
    is byte-identical (asserted); the earlier versions' checks re-run on the result (the V3.0.60 set)."""
    sid = {ln["line_id"]: i for i, ln in enumerate(prev)}
    out = list(prev)
    repl = set()
    for c in changes:
        a = c["after"]
        if a["item_code"] != PLASTER or c["action"] != "CHANGE":
            raise ValueError(f"{METHOD}: {c['action']} {a['item_code']} is not a change this version may make")
        i = sid.get(a["line_id"])
        if i is None or a["line_id"] in repl:
            raise ValueError(f"{METHOD}: a changed line is not a candidate line or changes twice")
        out[i] = a
        repl.add(a["line_id"])
    _o, i60 = A3060.integrate(out, [], for_lead)     # every V3.0.10 .. V3.0.60 family check, re-run on these lines
    ident = {"base_lines": len(prev), "v3_0_61_lines": len(out), "v3_0_61_rows": len(changes), "replaced": len(repl),
             "added": 0, "checks_v3_0_60": {k: v for k, v in i60.items() if k not in (
                 "base_lines", "v3_0_60_lines", "v3_0_60_rows", "replaced", "added", "outside_rows",
                 "outside_rows_identical_to_base", "outside_rows_sha256")},
             "plaster_height": check_plaster_height(out, prev)}
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
                     "room_id": loc.get("room_id"), "room": rec["room"], "element_id": loc.get("element_id"),
                     "unit": ref["unit"], "before_released_v2_9": b29, "before_base": A30._qty(c.get("before")),
                     "after_v3_0_61": A30._qty(ref), "class": [rec["was"]["class"], line_class(ref)],
                     "evidence_status": c.get("evidence_status"), "still_held": c.get("held"),
                     "release_status": "NOT RELEASED", "paint_line_id": rec["paint_line_id"],
                     "basis": rec["basis"], "remeasure_beside": rec.get("remeasure_beside"),
                     "owner_manual_method": PIECES[c["piece"]]["owner_manual_method"],
                     "drawing_derived_method": PIECES[c["piece"]]["drawing_method"],
                     "verification": c.get("verification") or {}, "rollback": ROLLBACK})
    return rows


LEDGER_CSV = ("version", "piece", "change", "line_id", "item_code", "floor", "room", "element_id", "unit", "v2_9",
              "base", "v3_0_61", "class", "paint_line_id", "evidence_status", "still_held", "verification")
DIFF_CSV = ("line_id", "item_code", "floor", "element_id", "unit", "vs_base", "vs_released_v2_9", "v2_9", "base",
            "v3_0_61")


def ledger_csv(rows):
    def q(x):
        return A302._q(x) if x and (x.get("value") is not None or x.get("low") is not None or x.get("state")) else ""
    return A305._csv([{"version": r["version"], "piece": r["piece"], "change": r["change"], "line_id": r["line_id"],
                       "item_code": r["item_code"], "floor": r.get("floor") or "", "room": r.get("room") or "",
                       "element_id": r.get("element_id") or "", "unit": r["unit"],
                       "v2_9": q(r.get("before_released_v2_9")), "base": q(r.get("before_base")),
                       "v3_0_61": q(r.get("after_v3_0_61")), "class": " -> ".join(r["class"]),
                       "paint_line_id": r["paint_line_id"], "evidence_status": r["evidence_status"],
                       "still_held": "; ".join(x["what"] for x in r.get("still_held") or ())[:300],
                       "verification": f"{r['verification'].get('task')} "
                                       f"{' '.join(x[:8] for x in r['verification'].get('merge_commits') or ())}"}
                      for r in rows], LEDGER_CSV)


def diff_rows(prev, new, released_lines=None):
    return [dict({k: v for k, v in d.items() if k != "v3_0_60"}, v3_0_61=d["v3_0_60"])
            for d in A3060.diff_rows(prev, new, released_lines)]


def write(out, prev, changes, log, released_lines=None, for_lead=()):
    """the V3_0_61_* files beside the base candidate's files. -> (file names, identity, ledger)."""
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
    ident = dict(ident, diff=dsum, restated=restated_sums(changes))
    moved = check_totals(A304.code_totals(prev), A304.code_totals(new), changes)
    led = {"schema": LEDGER_SCHEMA, "method": METHOD, "extends": EXTENDS, "candidate": CANDIDATE,
           "base": A30.BASE_METHOD, "released": A30.RELEASED_METHOD, "released_default": False, "rows": rows,
           "waiting_pieces": WAITING, "integration_package": True}
    run = {"method": METHOD, "policy": POLICY_ID, "extends": EXTENDS, "candidate": CANDIDATE,
           "base_method": A30.BASE_METHOD, "released_method": A30.RELEASED_METHOD, "released_default": False,
           "rollback": ROLLBACK, "identity": ident, "pieces": PIECES, "piece_logs": [log],
           "totals_moved_by_code": moved, "waiting_pieces": WAITING}
    files = {"V3_0_61_BOQ_LINES.json": BL.dumps(new),
             "V3_0_61_BOQ_LINES.csv": A30._lines_csv(new),
             "V3_0_61_INTEGRATION_LEDGER.json": A30._j(led),
             "V3_0_61_INTEGRATION_LEDGER.csv": ledger_csv(rows),
             "V3_0_61_DIFF.csv": A305._csv(diff, DIFF_CSV),
             "V3_0_61_RUN.json": A30._j(run)}
    for name, text in files.items():
        (out / name).write_text(text, encoding="utf-8")
    return sorted(files), ident, led


def policy_record():
    return {"method": METHOD, "extends": EXTENDS, "pieces": sorted(PIECES), "inputs_schema": INPUTS_SCHEMA,
            "released_default": False, "rollback": ROLLBACK, "actions": list(ACTIONS)}


__all__ = ["METHOD", "PIECES", "WAITING", "DEFAULT_GUARD_CLASS", "INPUTS_SCHEMA", "load_inputs", "changes_for",
           "check_plaster_height", "check_totals", "restated_sums", "integrate", "ledger_rows", "diff_rows", "write",
           "InputsError", "line_class"]
