"""ARCH_TAKEOFF_V3.0.20 (T-244): the SAME opt-in BOQ candidate as ARCH_TAKEOFF_V3.0 .. V3.0.19 (engine.source.arch_v30,
arch_v301 .. arch_v3019), extended with ONE piece, WALL_FINISH_REVISION: the internal plaster / paint room-face lines of
V3.0.9 (arch_v309 WALL_FINISH) take the opening outlines that checker-merged ledgers settled after V3.0.9, in place.
Not a new method family and not the released default (owner management decision 2026-10-20 sections 2 and 5);
rollback is running the released ARCH_TAKEOFF_V2.9.

The physical question (ERS 2026-10-22 s.2.1, s.3): a room-face finish line is the face built around the room (face
length x the owner wall height, Q-43 / Q-48 A) less every opening by ITS OWN physical outline inside that height (Q-73),
once per face (rule R-OPENING-ONCE-1, T-255). When a merged ledger settles an opening's outline (an arched hole by its
developed outline; a range closed to a value; a deduction once taken as known shown to be unsettled), the deduction of
that opening in EVERY line of that face changes, and only that deduction:

  REVISION  one room-face line (FIN.PLASTER or FIN.PAINT), same line id: each named deduction of its owner manual
            method is asserted against the line (the opening is named exactly once, with the stated before m2 or
            range), replaced by the after m2 or range with its source, and the net RECOMPUTED from the line's own gross
            and deductions (net_of of arch_v309): every deduction known -> a quantity at the record's status; any held
            deduction -> BOUNDED_EXPOSURE [low, high] with the held item (never a single figure, never 0). A line that
            carried a released figure and now holds a deduction leaves the released total (ENGINE_WRONG to release).
  CARRIED   an opening a ledger settled whose face lines already deduct it at that value (asserted: named once, m2
            equal): recorded, no line changes.
  NOT_APPLIED  an opening delta whose face line carries no figure (a held line without one) or has no room-face line in
            this candidate (a wet room, a held shaft part): recorded with its reason and its carrier; asserted that no
            line of the two codes carrying a figure deducts the opening with another value (else a REVISION is due).

The two codes are ONE face in the owner method (one figure for plaster and paint, Q-43): a revision of an opening on
one code's line while the other code's line of the same room still deducts it the old way is refused (stale twin).

Refused (InputsError / ValueError, nothing written): a record whose line the run does not carry, or whose before (state,
value / range) is not the line's (stale ledger); a line named twice; an opening named zero or two times in the line's
deductions, or with another before value; a recomputed net that is not the record's stated value / range (> 0.006 m2);
a known deduction <= 0 or a range not 0 <= low <= high; a quantity record with a held deduction, or a BOUNDED record
with none; a VERIFIED record without the checker run; a stale twin; a CARRIED entry whose line does not deduct the
opening once at the value; a NOT_APPLIED entry while a figure-carrying line deducts the opening at another value.
Inside a revised line only quantity, state, range, rfi, gross, geometry confidence, calculation and notes change;
every other line is byte-identical to V3.0.19 (asserted), including the project identity block.

Files: V3_0_20_BOQ_LINES.json / .csv, V3_0_20_INTEGRATION_LEDGER.json / .csv (per line: before V3.0.19, after, released
V2.9, each deduction before / after, owner manual method beside the drawing-derived method, status, source task /
merge / checker run), V3_0_20_OPENING_DELTAS.csv (every settled opening: REVISED / CARRIED / NOT_APPLIED),
V3_0_20_DIFF.csv (every line against V3.0.19 and the released V2.9), V3_0_20_RUN.json. Nothing here names a project, a
sheet, a layer or a coordinate: every value comes from the inputs.
"""

from __future__ import annotations

import copy
import hashlib
import json

from engine.source import arch_v30 as A30
from engine.source import arch_v302 as A302
from engine.source import arch_v304 as A304
from engine.source import arch_v305 as A305
from engine.source import arch_v309 as A309
from engine.source import arch_v3010 as A3010
from engine.source import arch_v3011 as A3011
from engine.source import arch_v3012 as A3012
from engine.source import arch_v3014 as A3014
from engine.source import arch_v3015 as A3015
from engine.source import arch_v3018 as A3018
from engine.source import arch_v3019 as A3019

DEFAULT_GUARD_CLASS = "TOOLING"          # T-212: brings named lines to a checker reading; adds no default value
METHOD = "ARCH_TAKEOFF_V3.0.20"
EXTENDS = A3019.METHOD
CANDIDATE = A30.METHOD
POLICY_ID = "URBAN_BOQ_T244_ARCH_V3_0_20"
INPUTS_SCHEMA = "URBAN_V3020_INPUTS_V1"
LEDGER_SCHEMA = "URBAN_V3020_INTEGRATION_LEDGER_V1"
ROLLBACK = A30.ROLLBACK
VER, DC, OA = A3018.VER, A3018.DC, A3018.OA
InputsError = A3015.InputsError
_num = A3015._num
_r = A3018._r
TOL = 1e-6
NET_TOL_M2 = A309.NET_TOL_M2             # 0.006 m2: the hand packages quote 4 decimals
CODES = ("FIN.PLASTER", "FIN.PAINT")
STATES = ("RELEASED", "BOUNDED")
QTY_STATUS = (VER, DC, OA)
HELD_STATUS = ("HELD", "UNKNOWN")
DELTA_KINDS = ("CARRIED", "NOT_APPLIED")
RULE = ("R-FINISH-OPENING-REVISION-1", "T-244")

PIECES = {
    "WALL_FINISH_REVISION": {
        "module": "engine/source/arch_v3020.py (room-face finish deductions brought to the merged opening outlines)",
        "policy": "WALL_FINISH_REVISION_V1", "rule_id": RULE[0], "rule_version": RULE[1],
        "owner_rules": ["Q-43 / Q-48 A (one owner wall height; one figure for plaster and paint)",
                        "Q-73 (full openings deducted, by what is physically built)",
                        "Q-55 C (door head 2.20 where none is printed: ASSUMED - OWNER-APPROVED)",
                        "Q-32 A / Q-38 A (window supply m2 = printed width x height; never a finish deduction)",
                        "UP-FIN-PLASTER-001", "UP-FIN-PAINT-001", "UP-OPEN-ARCH-001 (T-227 r2)",
                        "UP-QTY-STATUS-001 (held never 0)", "WORKFLOW_CONTROLS 2026-10-21 s.4 / s.5",
                        "R-OPENING-ONCE-1 (T-255: each opening once per trade face)"],
        "owner_manual_method": "manual QS take-off of a room's wall face: face length x the owner wall height of the "
                               "floor, less every opening by its own area inside that height (an arched opening by "
                               "its outline, never its band rectangle; door head 2.20 where none is printed); one "
                               "figure for plaster and paint",
        "drawing_method": "the room contour walked on the drawn faces, the opening outline on the face the finish "
                          "covers (room side) read from the plan arc and the elevation chain; shown beside on the "
                          "line (V3.0.9 drawing_derived_method), never merged"},
}
WAITING = dict(A3019.WAITING)
WAITING.update({
    "WALL_FINISH_HELD_HEADS": "the room-face openings whose head / sill is still not printed (lift landing doors, W02, "
                              "W11 / W12 sills, A-GF-01 / A-1F-01, the GF-11 / ST-GF doorless opening): the lines stay "
                              "BOUNDED; the roof datum DCR-6 / annex G2 rooms stay without a figure",
})


# ================================================================================================ inputs
def _ded_value(d, where):
    """a deduction entry -> ('m2', v) or ('range', [lo, hi]); refused if neither."""
    if _num(d.get("m2")):
        if d["m2"] <= 0:
            raise InputsError(f"{where}: a known deduction is > 0 (a missing one is HELD as a range, never 0)")
        return ("m2", float(d["m2"]))
    rg = d.get("range")
    if isinstance(rg, (list, tuple)) and len(rg) == 2 and all(_num(x) for x in rg) and 0 <= rg[0] <= rg[1]:
        return ("range", [float(rg[0]), float(rg[1])])
    raise InputsError(f"{where}: a deduction is a known m2 > 0 or a range [low, high], 0 <= low <= high")


def _same_ded(a, b):
    ka, va = a
    kb, vb = b
    if ka != kb:
        return False
    if ka == "m2":
        return abs(va - vb) <= TOL
    return abs(va[0] - vb[0]) <= TOL and abs(va[1] - vb[1]) <= TOL


def _check_record(r, where, tasks):
    for k in ("line_id", "item_code", "room", "task", "state", "evidence_status"):
        if not r.get(k):
            raise InputsError(f"{where}: {k} required")
    if r["item_code"] not in CODES:
        raise InputsError(f"{where}: item code {r['item_code']!r} not one of {CODES}")
    if r["task"] not in tasks:
        raise InputsError(f"{where}: task {r['task']!r} is not one of the sources {sorted(tasks)}")
    b = r.get("before") or {}
    if not b.get("evidence_state"):
        raise InputsError(f"{where}: before {{evidence_state, measured_net | bounded_range}} is asserted against the "
                          "line")
    st = r["state"]
    if st not in STATES:
        raise InputsError(f"{where}: state {st!r} not one of {STATES}")
    if st == "RELEASED":
        if not (_num(r.get("value")) and r["value"] > 0):
            raise InputsError(f"{where}: a RELEASED record carries a value > 0")
        if r["evidence_status"] not in QTY_STATUS:
            raise InputsError(f"{where}: a RELEASED record is one of {QTY_STATUS}")
        if r["evidence_status"] == VER and not r.get("verified_by"):
            raise InputsError(f"{where}: VERIFIED names the checker run")
        if not r.get("assumption"):
            raise InputsError(f"{where}: the owner-approved height assumption stays on the line (WORKFLOW_CONTROLS s.4)")
    else:
        rg = r.get("range")
        if not (isinstance(rg, (list, tuple)) and len(rg) == 2 and all(_num(x) for x in rg)
                and 0 <= rg[0] <= rg[1] and rg[1] > 0):
            raise InputsError(f"{where}: a BOUNDED record carries a range [low, high], 0 <= low <= high, high > 0")
        if r["evidence_status"] not in HELD_STATUS or not r.get("reasons"):
            raise InputsError(f"{where}: a BOUNDED record names why (reasons) and its status HELD / UNKNOWN")
    revs = r.get("revisions") or []
    if not revs:
        raise InputsError(f"{where}: a record revises at least one deduction")
    names = [v.get("opening") for v in revs]
    if not all(names) or len(set(names)) != len(names):
        raise InputsError(f"{where}: every revision names its opening, once")
    for v in revs:
        w = f"{where} {v['opening']}"
        _ded_value(v.get("before") or {}, f"{w} before")
        _ded_value(v.get("after") or {}, f"{w} after")
        if not v.get("source_task") or v["source_task"] not in tasks:
            raise InputsError(f"{w}: source_task names one of the sources")
        if not v.get("why"):
            raise InputsError(f"{w}: why (the physical cause of the change)")


def _check_delta(x, where, tasks):
    for k in ("opening", "room", "kind", "task", "why"):
        if not x.get(k):
            raise InputsError(f"{where}: {k} required")
    if x["kind"] not in DELTA_KINDS:
        raise InputsError(f"{where}: kind {x['kind']!r} not one of {DELTA_KINDS}")
    if x["task"] not in tasks:
        raise InputsError(f"{where}: task {x['task']!r} is not one of the sources")
    ids = x.get("line_ids") or []
    if len(ids) != len(set(ids)):
        raise InputsError(f"{where}: a line named twice")
    if x["kind"] == "CARRIED":
        if not ids or not (_num(x.get("m2")) and x["m2"] > 0):
            raise InputsError(f"{where}: CARRIED names the line(s) and the m2 they deduct")
    elif not x.get("carrier"):
        raise InputsError(f"{where}: NOT_APPLIED names what carries the delta when the line is settled (carrier)")


def load_inputs(doc, project_id=None):
    """URBAN_V3020_INPUTS_V1 or None:
        {"schema", "project", "sources": [{file, sha256, task, merge_commit, checker_run}],
         "records": [{line_id, item_code, room, task, before {evidence_state, measured_net | bounded_range [lo, hi]},
                      state RELEASED | BOUNDED, value | range, evidence_status, verified_by, assumption, reasons,
                      revisions [{opening, before {m2 | range}, after {m2 | range, basis}, source_task, why}],
                      downstream}],
         "deltas": [{opening, room, kind CARRIED | NOT_APPLIED, task, why, line_ids, m2, token, carrier, value_delta}]}"""
    if doc is None:
        return None
    if doc.get("schema") != INPUTS_SCHEMA:
        raise InputsError(f"project inputs: schema must be {INPUTS_SCHEMA}")
    if project_id and doc.get("project") not in (None, project_id):
        raise InputsError(f"project inputs are for {doc.get('project')!r}, the run is {project_id!r}")
    srcs = doc.get("sources") or []
    if not srcs:
        raise InputsError("sources: the merged ledgers the records come from")
    tasks = set()
    for s in srcs:
        A3018._source(s, "sources")
        tasks.add(s["task"])
    recs = doc.get("records") or []
    if not recs:
        raise InputsError("no records")
    seen = set()
    for r in recs:
        lid = r.get("line_id")
        if not lid or lid in seen:
            raise InputsError(f"record: line {lid!r} missing or named twice")
        seen.add(lid)
        _check_record(r, f"record {lid}", tasks)
    keys = set()
    for x in doc.get("deltas") or ():
        k = (x.get("opening"), x.get("room"))
        if k in keys:
            raise InputsError(f"delta {k}: named twice")
        keys.add(k)
        _check_delta(x, f"delta {k}", tasks)
    return doc


# ================================================================================================ lines
def _om(ln):
    return ((ln.get("calculation") or {}).get("inputs") or {}).get("owner_manual_method") or {}


def _room(ln):
    return ((ln.get("calculation") or {}).get("inputs") or {}).get("room")


def _match(deds, opening, where):
    """the index of the ONE deduction naming `opening` (exact name, or its leading token before a space / '(')."""
    hit = [k for k, d in enumerate(deds) if isinstance(d.get("opening"), str)
           and (d["opening"] == opening or d["opening"].split(" ")[0].split("(")[0] == opening)]
    if len(hit) != 1:
        raise InputsError(f"{where}: the line names {opening} {len(hit)} times in its deductions (exactly once)")
    return hit[0]


def _assert_before(ln, r, where):
    if ln is None:
        raise InputsError(f"{where}: the run carries no line {r['line_id']}")
    if ln["item_code"] != r["item_code"] or _room(ln) != r["room"]:
        raise InputsError(f"{where}: the line is {ln['item_code']} {_room(ln)!r}, the record {r['item_code']} "
                          f"{r['room']!r}")
    b = r["before"]
    q = A30._qty(ln)
    if q["state"] != b["evidence_state"]:
        raise InputsError(f"{where}: before state {b['evidence_state']} is not the line's {q['state']} (stale ledger)")
    if q["state"] == "BOUNDED_EXPOSURE":
        br = b.get("bounded_range") or [None, None]
        if not (_num(br[0]) and _num(br[1]) and abs(br[0] - q["low"]) <= TOL and abs(br[1] - q["high"]) <= TOL):
            raise InputsError(f"{where}: before range {br} is not the line's {q['low']} .. {q['high']} (stale ledger)")
    elif not (_num(b.get("measured_net")) and q["value"] is not None and abs(b["measured_net"] - q["value"]) <= TOL):
        raise InputsError(f"{where}: before {b.get('measured_net')} is not the line's {q['value']} (stale ledger)")


def revised_line(before, r, src):
    """the line of one REVISION record. -> (line, revised owner method, deduction rows)"""
    from engine.source import boq_line as BL
    where = f"record {r['line_id']}"
    om = copy.deepcopy(_om(before))
    if not _num(om.get("gross")):
        raise InputsError(f"{where}: the line carries no owner-method gross (a line without a figure is NOT_APPLIED)")
    deds = om.get("deductions") or []
    rows = []
    for v in r["revisions"]:
        k = _match(deds, v["opening"], where)
        got = _ded_value(deds[k], f"{where} {v['opening']} (line)")
        want = _ded_value(v["before"], f"{where} {v['opening']} before")
        if not _same_ded(got, want):
            raise InputsError(f"{where}: {v['opening']} is deducted {got[1]} on the line, the record's before "
                              f"{want[1]} (stale ledger)")
        kind, val = _ded_value(v["after"], f"{where} {v['opening']} after")
        new = {"opening": deds[k]["opening"], kind: _r(val) if kind == "m2" else [_r(val[0]), _r(val[1])],
               "basis": (v["after"].get("basis") or v["why"])[:400],
               "revised_by": {"method": METHOD, "task": v["source_task"], "before": copy.deepcopy(deds[k])}}
        rows.append({"opening": deds[k]["opening"], "before": got[1], "after": val, "source_task": v["source_task"],
                     "why": v["why"]})
        deds[k] = new
    om["deductions"] = deds
    lo, hi = A309.net_of(om)
    st = r["state"]
    if st == "RELEASED":
        if abs(hi - lo) > 1e-9:
            raise InputsError(f"{where}: a RELEASED record has every deduction known (a held one is BOUNDED)")
        if abs(lo - r["value"]) > NET_TOL_M2:
            raise InputsError(f"{where}: net recomputed {round(lo, 4)} != stated {r['value']}")
    else:
        if abs(hi - lo) <= 1e-9:
            raise InputsError(f"{where}: a BOUNDED record with every deduction known (it is a quantity)")
        if abs(lo - r["range"][0]) > NET_TOL_M2 or abs(hi - r["range"][1]) > NET_TOL_M2:
            raise InputsError(f"{where}: net recomputed {round(lo, 4)} .. {round(hi, 4)} != stated "
                              f"{r['range'][0]} .. {r['range'][1]}")
    ln = copy.deepcopy(before)
    inp = ln["calculation"]["inputs"]
    reasons = list(r.get("reasons") or ())
    if st == "RELEASED":
        ln["evidence_state"] = "PROVISIONAL"
        ln["measured_net"] = _r(r["value"])
        ln["bounded_range"] = None
        ln["rfi"] = None
        ln["gross"] = _r(om["gross"])
        ln["source"]["geometry_confidence"] = "TOLERANCE_CERTIFIED"
    else:
        ln["evidence_state"] = "BOUNDED_EXPOSURE"
        ln["measured_net"] = None
        ln["bounded_range"] = {"low": _r(r["range"][0]), "high": _r(r["range"][1]),
                               "basis": (r.get("range_basis") or "; ".join(reasons))[:300]}
        ln["rfi"] = {"question": "; ".join(reasons)[:900], "unlocks": ln["location"].get("element_id")}
        ln["gross"] = None
        ln["source"]["geometry_confidence"] = "INFERRED_CANDIDATE"
    inp["owner_manual_method"] = om
    inp["owner_net_recomputed"] = [_r(lo, 4), _r(hi, 4)]
    inp["record_state"] = st
    inp["evidence_status"] = r["evidence_status"]
    inp["verified_by"] = r.get("verified_by")
    inp["assumption"] = r.get("assumption") or inp.get("assumption")
    inp["reasons"] = reasons
    inp["wall_finish_revision_v3020"] = {
        "policy": PIECES["WALL_FINISH_REVISION"]["policy"], "task": src["task"], "ledger": src["file"],
        "ledger_sha256": src["sha256"], "merge_commit": src["merge_commit"], "checker_run": src["checker_run"],
        "before": A3018._before_rec(before), "revisions": rows, "rule_id": RULE[0], "rule_version": RULE[1]}
    shown = (f"{_r(r['value'], 4)} m2" if st == "RELEASED" else f"{_r(r['range'][0], 4)} .. {_r(r['range'][1], 4)} m2 "
             "HELD")
    ln["calculation"]["formula"] = (f"{ln['calculation'].get('formula')}; {METHOD}: "
                                    + ", ".join(f"{x['opening']} {x['before']} -> {x['after']}" for x in rows)
                                    + f" (net {shown})")[:600]
    A305._note(ln, f"{METHOD}: opening outline(s) settled by merged ledgers ("
                   + ", ".join(sorted({x['source_task'] for x in rows})) + f"): {st} {r['evidence_status']}")
    return BL.validate(ln), om, rows


def _check_twins(records, by):
    """one face, one figure for plaster and paint (Q-43): a revised opening must be revised on every line of the same
    room and code pair that deducts it."""
    revised = {(r["room"], v["opening"], r["item_code"]) for r in records for v in r["revisions"]}
    rec_ids = {r["line_id"] for r in records}
    for room, opening, code in sorted(revised):
        for lid, ln in by.items():
            if lid in rec_ids or ln["item_code"] not in CODES or _room(ln) != room:
                continue
            deds = _om(ln).get("deductions") or []
            if any(isinstance(d.get("opening"), str) and (d["opening"] == opening
                                                           or d["opening"].split(" ")[0].split("(")[0] == opening)
                   for d in deds):
                raise InputsError(f"room {room}: {opening} revised on {code} but {ln['item_code']} line {lid} still "
                                  "deducts it the old way (one face, one figure: stale twin)")


def _delta_rows(doc, by, revised_rows):
    out = []
    for x in doc.get("deltas") or ():
        w = f"delta {x['opening']} {x['room']}"
        if x["kind"] == "CARRIED":
            for lid in x["line_ids"]:
                ln = by.get(lid)
                if ln is None:
                    raise InputsError(f"{w}: line {lid} is not a line of the run")
                deds = _om(ln).get("deductions") or []
                tok = x.get("token") or x["opening"]
                hit = [d for d in deds if isinstance(d.get("opening"), str) and tok in d["opening"]]
                if len(hit) != 1:
                    raise InputsError(f"{w}: {lid} names {tok!r} {len(hit)} times in its deductions (exactly once)")
                got = _ded_value(hit[0], f"{w} {lid}")
                if got[0] != "m2" or abs(got[1] - x["m2"]) > 1e-4:
                    raise InputsError(f"{w}: {lid} deducts {got[1]} for {tok!r}, the delta {x['m2']}")
        else:
            for lid in x.get("line_ids") or ():
                ln = by.get(lid)
                if ln is None:
                    raise InputsError(f"{w}: line {lid} is not a line of the run")
                if A309._carried(ln) != A309.NO_FIGURE:
                    raise InputsError(f"{w}: {lid} carries a figure ({A309._carried(ln)}): the delta is a REVISION "
                                      "record, never NOT_APPLIED")
            tok = x.get("token") or x["opening"]
            for lid, ln in by.items():   # no figure-carrying finish line of the room may deduct it the old way
                if ln["item_code"] not in CODES or _room(ln) != x["room"] or A309._carried(ln) == A309.NO_FIGURE:
                    continue
                if any(isinstance(d.get("opening"), str) and tok in d["opening"]
                       for d in (_om(ln).get("deductions") or [])):
                    raise InputsError(f"{w}: {lid} carries a figure and deducts {tok}: a REVISION record is due")
        out.append({"opening": x["opening"], "room": x["room"], "kind": x["kind"], "task": x["task"],
                    "line_ids": list(x.get("line_ids") or ()), "m2": x.get("m2"), "value_delta": x.get("value_delta"),
                    "carrier": x.get("carrier"), "why": x["why"]})
    for r in revised_rows:
        out.append(r)
    return out


def changes_for(doc, l3019):
    """-> (changes, log, delta rows)."""
    if not doc:
        return [], {"piece": "WALL_FINISH_REVISION", "state": "NO_PROJECT_INPUT"}, []
    by = {ln["line_id"]: ln for ln in l3019}
    recs = doc.get("records") or ()
    for r in recs:
        _assert_before(by.get(r["line_id"]), r, f"record {r['line_id']}")
    _check_twins(recs, by)
    changes, revised_rows = [], []
    for r in recs:
        src = A3018._src_of(doc, r["task"])
        b = by[r["line_id"]]
        after, om, rows = revised_line(b, r, src)
        ver = {"task": src["task"], "merge_commit": src["merge_commit"], "verifier_run": src["checker_run"],
               "ledger": src["file"], "ledger_sha256": src["sha256"], "record_verified_by": r.get("verified_by")}
        changes.append(A305._change("WALL_FINISH_REVISION", "REPLACE", b, after, drawing_reference=r.get("printed"),
                                    held=list(r.get("reasons") or ()),
                                    downstream=[d if isinstance(d, dict) else {"item": d}   # Gate B tools read dicts
                                                for d in r.get("downstream") or ()],
                                    verification=ver, evidence_status=r["evidence_status"],
                                    codes=["WALL_FINISH_REVISION", "STATE_CHANGE" if b["evidence_state"] !=
                                           after["evidence_state"] else "REBASE"],
                                    group=r["room"], revisions=rows))
        for x in rows:
            revised_rows.append({"opening": x["opening"], "room": r["room"], "kind": "REVISED", "task": x["source_task"],
                                 "line_ids": [r["line_id"]], "m2": x["after"] if not isinstance(x["after"], list)
                                 else None, "value_delta": None, "carrier": None,
                                 "why": f"{r['item_code']}: {x['before']} -> {x['after']}: {x['why']}"[:400]})
    deltas = _delta_rows(doc, by, revised_rows)
    log = {"piece": "WALL_FINISH_REVISION", "state": "RUN", "sources": doc["sources"], "records": len(changes),
           "delta_rows": len(deltas), "delta_kinds": A302._count(d["kind"] for d in deltas)}
    return changes, log, deltas


# ================================================================================================ integrate / write
ROW_KEYS = ("evidence_state", "measured_net", "bounded_range", "rfi", "notes", "gross", "calculation")


def integrate(l3019, changes):
    """-> (V3.0.20 lines, identity). Every line outside the V3.0.20 rows is byte-identical to the V3.0.19 line."""
    from engine.source import boq_line as BL
    sid = {ln["line_id"] for ln in l3019}
    rep = {}
    for c in changes:
        if c["action"] != "REPLACE":
            raise ValueError(f"{METHOD}: action {c['action']} (V3.0.20 replaces lines in place only)")
        lid = c["before"]["line_id"]
        if lid in rep or lid not in sid or c["after"]["line_id"] != lid:
            raise ValueError(f"{METHOD}: line {lid}: changed twice, not in V3.0.19, or its id changed")
        rep[lid] = c["after"]
    out = [rep.get(ln["line_id"], ln) for ln in l3019]
    for ln in out:
        BL.validate(ln)
    A3011.check_conflicts(out)
    A3010.check_same_openings(out)
    A3012.check_partition(out)
    A3014.check_floor_scope(out)
    A3015.check_family(out)
    A3018.check_splits(out)
    pids = {(ln["project"]["project_id"], ln["project"]["revision_set_sha256"]) for ln in out}
    if len(pids) != 1:
        raise ValueError(f"{METHOD}: {len(pids)} project identities in the lines (one project, one revision set)")
    by19 = {ln["line_id"]: ln for ln in l3019}
    outside = [ln for ln in out if ln["line_id"] not in rep]
    bad = [ln["line_id"] for ln in outside if A30.line_sha(by19[ln["line_id"]]) != A30.line_sha(ln)]
    if bad or len(outside) + len(rep) != len(l3019):
        raise ValueError(f"{METHOD}: {len(bad)} line(s) outside the V3.0.20 rows differ from {EXTENDS}")
    for lid, ln in rep.items():   # inside a row only quantity, state, basis and notes change
        a, b = copy.deepcopy(by19[lid]), copy.deepcopy(ln)
        for x in (a, b):
            for k in ROW_KEYS:
                x.pop(k, None)
            x["source"].pop("geometry_confidence", None)
        if json.dumps(a, sort_keys=True) != json.dumps(b, sort_keys=True):
            raise ValueError(f"{METHOD}: line {lid} changed outside quantity / state / basis")
    ident = {"v3_0_19_lines": len(l3019), "v3_0_20_lines": len(out), "v3_0_20_rows": len(changes),
             "replaced": len(rep), "added": 0, "outside_rows": len(outside),
             "outside_rows_identical_to_v3_0_19": len(outside),
             "outside_rows_sha256": hashlib.sha256("".join(A30.line_sha(x) for x in outside).encode()).hexdigest()}
    return out, ident


def ledger_rows(changes, released_lines=None):
    rel = {A30._key(ln): ln for ln in released_lines or ()}
    p = PIECES["WALL_FINISH_REVISION"]
    rows = []
    for c in changes:
        ref = c["before"]
        b29 = None
        if released_lines is not None:
            b29 = A30._qty(rel[A30._key(ref)]) if A30._key(ref) in rel else dict(A30._qty(None),
                                                                                 state="NOT_IN_RELEASED")
        inp = c["after"]["calculation"]["inputs"]
        loc = c["after"].get("location") or {}
        rows.append({"version": METHOD, "piece": c["piece"], "action": c["action"], "line_id": c["after"]["line_id"],
                     "item_code": c["after"]["item_code"], "floor": loc.get("floor"), "room": inp.get("room"),
                     "room_id": loc.get("room_id"), "element_id": loc.get("element_id"), "unit": c["after"]["unit"],
                     "before_released_v2_9": b29, "before_v3_0_19": A30._qty(c["before"]),
                     "after_v3_0_20": A30._qty(c["after"]), "evidence_status": c.get("evidence_status"),
                     "release_status": "NOT RELEASED", "revisions": c.get("revisions") or [],
                     "owner_manual_method": inp.get("owner_manual_method"),
                     "owner_net_recomputed": inp.get("owner_net_recomputed"),
                     "drawing_derived_method": inp.get("drawing_derived_method"),
                     "codes": c.get("codes") or [], "drawing_reference": c.get("drawing_reference"),
                     "owner_rules": p["owner_rules"], "owner_manual_method_text": p["owner_manual_method"],
                     "drawing_method_text": p["drawing_method"],
                     "verification": dict(c.get("verification") or {}, module=p["module"], policy=p["policy"]),
                     "held": c.get("held") or [], "downstream": c.get("downstream") or [], "rollback": ROLLBACK})
    return rows


LEDGER_CSV = ("version", "room", "line_id", "item_code", "floor", "element_id", "unit", "v2_9", "v3_0_19", "v3_0_20",
              "evidence_status", "release_status", "revisions", "verification")


def ledger_csv(rows):
    return A305._csv([{"version": r["version"], "room": r["room"], "line_id": r["line_id"],
                       "item_code": r["item_code"], "floor": r["floor"], "element_id": r["element_id"],
                       "unit": r["unit"], "v2_9": A302._q(r["before_released_v2_9"]),
                       "v3_0_19": A302._q(r["before_v3_0_19"]), "v3_0_20": A302._q(r["after_v3_0_20"]),
                       "evidence_status": r["evidence_status"], "release_status": r["release_status"],
                       "revisions": "; ".join(f"{x['opening']} {x['before']} -> {x['after']} ({x['source_task']})"
                                              for x in r["revisions"])[:400],
                       "verification": f"{r['verification'].get('task')} {r['verification'].get('merge_commit')} "
                                       f"{r['verification'].get('verifier_run')}"} for r in rows], LEDGER_CSV)


DELTA_CSV = ("opening", "room", "kind", "task", "line_ids", "m2", "value_delta", "carrier", "why")
DIFF_CSV = ("line_id", "item_code", "floor", "element_id", "unit", "vs_v3_0_19", "vs_released_v2_9", "v2_9",
            "v3_0_19", "v3_0_20")


def diff_rows(l3019, l3020, released_lines=None):
    b19 = {ln["line_id"]: ln for ln in l3019}
    rel = {A30._key(ln): ln for ln in released_lines or ()}
    out = []
    for ln in l3020:
        o = b19.get(ln["line_id"])
        vs = "ADDED" if o is None else ("SAME" if A30.line_sha(o) == A30.line_sha(ln) else "CHANGED")
        r = rel.get(A30._key(ln)) if released_lines is not None else None
        vs29 = None if released_lines is None else ("NOT_IN_RELEASED" if r is None else
                                                    ("SAME_QUANTITY" if A30._qty(r) == A30._qty(ln) else
                                                     "QUANTITY_DIFFERS"))
        out.append({"line_id": ln["line_id"], "item_code": ln["item_code"], "floor": ln["location"].get("floor"),
                    "element_id": ln["location"].get("element_id"), "unit": ln["unit"], "vs_v3_0_19": vs,
                    "vs_released_v2_9": vs29, "v2_9": A302._q(A30._qty(r)) if r else "",
                    "v3_0_19": A302._q(A30._qty(o)) if o else "", "v3_0_20": A302._q(A30._qty(ln))})
    return out


def write(out, l3019, changes, log, deltas, doc, released_lines=None):
    """the V3_0_20_* files beside the V3_0_19_* files. -> (file names, identity, ledger)."""
    from pathlib import Path
    from engine.source import boq_line as BL
    out = Path(out)
    l3020, ident = integrate(l3019, changes)
    rows = ledger_rows(changes, released_lines)
    diff = diff_rows(l3019, l3020, released_lines)
    dsum = {}
    for d in diff:
        dsum.setdefault("vs_v3_0_19", {}).setdefault(d["vs_v3_0_19"], 0)
        dsum["vs_v3_0_19"][d["vs_v3_0_19"]] += 1
        if d["vs_released_v2_9"] is not None:
            dsum.setdefault("vs_released_v2_9", {}).setdefault(d["vs_released_v2_9"], 0)
            dsum["vs_released_v2_9"][d["vs_released_v2_9"]] += 1
    ident = dict(ident, diff=dsum)
    t19, t20 = A304.code_totals(l3019), A304.code_totals(l3020)
    moved = {k: {"v3_0_19": t19.get(k), "v3_0_20": t20.get(k)} for k in sorted(set(t19) | set(t20))
             if t19.get(k) != t20.get(k)}
    led = {"schema": LEDGER_SCHEMA, "method": METHOD, "extends": EXTENDS, "candidate": CANDIDATE,
           "base": A30.BASE_METHOD, "released": A30.RELEASED_METHOD, "released_default": False, "rows": rows,
           "deltas": deltas, "waiting_pieces": WAITING, "integration_package": True}
    run = {"method": METHOD, "policy": POLICY_ID, "extends": EXTENDS, "candidate": CANDIDATE,
           "base_method": A30.BASE_METHOD, "released_method": A30.RELEASED_METHOD, "released_default": False,
           "rollback": ROLLBACK, "identity": ident, "pieces": PIECES, "piece_log": log,
           "totals_moved_by_code": moved, "waiting_pieces": WAITING,
           "evidence_status_counts": A302._count(r["evidence_status"] for r in rows)}
    files = {"V3_0_20_BOQ_LINES.json": BL.dumps(l3020),
             "V3_0_20_BOQ_LINES.csv": A30._lines_csv(l3020),
             "V3_0_20_INTEGRATION_LEDGER.json": A30._j(led),
             "V3_0_20_INTEGRATION_LEDGER.csv": ledger_csv(rows),
             "V3_0_20_OPENING_DELTAS.csv": A305._csv([dict(d, line_ids=" ".join(d["line_ids"])) for d in deltas],
                                                     DELTA_CSV),
             "V3_0_20_DIFF.csv": A305._csv(diff, DIFF_CSV),
             "V3_0_20_RUN.json": A30._j(run)}
    for name, text in files.items():
        (out / name).write_text(text, encoding="utf-8")
    return sorted(files), ident, led


def policy_record():
    return {"method": METHOD, "extends": EXTENDS, "pieces": sorted(PIECES), "inputs_schema": INPUTS_SCHEMA,
            "released_default": False, "rollback": ROLLBACK}


__all__ = ["METHOD", "PIECES", "WAITING", "DEFAULT_GUARD_CLASS", "INPUTS_SCHEMA", "load_inputs", "revised_line",
           "changes_for", "integrate", "ledger_rows", "diff_rows", "write", "InputsError"]
