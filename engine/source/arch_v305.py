"""ARCH_TAKEOFF_V3.0.5 (T-179): the SAME opt-in BOQ candidate as ARCH_TAKEOFF_V3.0 .. V3.0.4 (engine.source.arch_v30,
arch_v301 .. arch_v304), extended with three checker-verified hand ledgers: suspended-slab steel, stair / landing /
pool / tank steel and the dome ring concrete. Not a new method family and not the released default (owner management
decision 2026-10-20 sections 2 and 5); rollback is running the released ARCH_TAKEOFF_V2.9.

How it is built (tools/urban_boq_m9.py `arch --method ARCH_TAKEOFF_V3.0.5`):
  1. the run is the V3.0.4 candidate exactly: its V3_0_* .. V3_0_4_* files are written unchanged (arch_v30 .. arch_v304
     are not edited);
  2. each ledger of the project inputs (URBAN_V305_VERIFIED_LEDGERS_V1) names its file sha256, the task, the merge
     commit and the checker run (a ledger without a checker MERGED verdict is not integrated), the item code and unit
     it measures, and the route G lines it replaces:
       scope.supersede = ELEMENT_AND_FLOORS  every route line of that item code / trade, physical element and floors
                       = NAMED_LINES         exactly the route lines named by element id (each must exist once, with
                                             the ledger's item code and a floor in scope; otherwise refused)
     a replaced line becomes NOT_APPLICABLE_WITH_EVIDENCE (its route quantity kept in the note: never deleted, never
     summed); a line an earlier version (V3.0.1 .. V3.0.4) changed is never replaced here (refused);
  3. one line is added per ledger record:
       RELEASED          -> SOURCE_DERIVED; evidence DRAWING-CONFIRMED, VERIFIED only where the record names the
                            checker run that re-measured it; NOT RELEASED (only the owner releases)
       HELD_RANGE        -> BOUNDED_EXPOSURE low .. high (the readings it rests on are listed); HELD
       HELD_DEFINED      -> BLOCKED_RFI, the defined figure in its inputs only (never added as a quantity); HELD
       UNQUANTIFIED      -> BLOCKED_RFI (figures it was given, if any, in its inputs as information); UNKNOWN
     a held record names why it is held; missing is never 0;
  4. the V3_0_5_* files are written beside them: every line outside the V3.0.5 rows is byte-identical to the V3.0.4
     line (asserted on every run), and V3_0_5_DIFF.csv lists every line against V3.0.4 and against the released V2.9.

Rules: owner decision 2026-10-20 sections 2 and 5, WORKFLOW_CONTROLS 2026-10-21 sections 1, 3, 5,
ENGINEERING_REASONING_STANDARD 2026-10-22 section 3, URBAN-REBAR-NET-AND-PROCUREMENT@v1 (kg = count x length x kg/m;
never kg/m3), Q-44 A / Q-61 C (one ring, never the full annulus, never twice), UP-QTY-STATUS-001.
Nothing here names a project, a sheet, a layer, a mark or a coordinate; every number comes from the run or the
project inputs.
"""

from __future__ import annotations

import copy
import csv
import hashlib
import io
import re

from engine.source import arch_v30 as A30
from engine.source import arch_v302 as A302
from engine.source import arch_v304 as A304

METHOD = "ARCH_TAKEOFF_V3.0.5"
EXTENDS = A304.METHOD
CANDIDATE = A30.METHOD                  # the candidate family this version extends (never a new method family)
POLICY_ID = "URBAN_BOQ_T179_ARCH_V3_0_5"
LEDGER_SCHEMA = "URBAN_V305_INTEGRATION_LEDGER_V1"
INPUTS_SCHEMA = "URBAN_V305_VERIFIED_LEDGERS_V1"
ROLLBACK = A30.ROLLBACK
STATES = ("RELEASED", "HELD_RANGE", "HELD_DEFINED", "UNQUANTIFIED")
SUPERSEDE = ("ELEMENT_AND_FLOORS", "NAMED_LINES")
EVIDENCE_STATUS = A302.EVIDENCE_STATUS
UNITS = {"kg": "REINFORCEMENT", "m3": "CONCRETE"}

PIECES = {
    "SLAB_STEEL": {
        "module": "engine/source/arch_v305.py (typed hand-ledger records)", "policy": "SLAB_STEEL_HAND_LEDGER_V1",
        "rule_id": "URBAN-REBAR-NET-AND-PROCUREMENT", "rule_version": "v1",
        "owner_rules": ["URBAN-REBAR-NET-AND-PROCUREMENT@v1", "Q-71 (meaning of 'n o d/m' established for footings "
                        "only, T-171: not extended to slabs without its own evidence)", "UP-QTY-STATUS-001"],
        "owner_manual_method": "manual QS take-off panel by panel: printed bars per metre x panel width = count, x bar "
                               "length face to face with the typical slab detail's curtailment; top bars, laps and "
                               "development held where the detail and the sheet note disagree or do not dimension them",
        "drawing_method": "hand ledger by bar population per panel and direction from the roof-slab plans and the "
                          "typical slab-on-beams detail; route G's provisional slab steel lines superseded"},
    "STAIR_POOL_TANK_STEEL": {
        "module": "engine/source/arch_v305.py (typed hand-ledger records)", "policy": "STAIR_POOL_TANK_STEEL_LEDGER_V1",
        "rule_id": "URBAN-REBAR-NET-AND-PROCUREMENT", "rule_version": "v1",
        "owner_rules": ["URBAN-REBAR-NET-AND-PROCUREMENT@v1", "Q-71 (footings only)", "Q-50 (curved stair held)",
                        "Q-62 A cond", "UP-QTY-STATUS-001"],
        "owner_manual_method": "manual QS take-off by flight and landing: plan-printed main bars per metre x width = "
                               "count, x sloped waist face to face; typical-section families only where a plan "
                               "reference ties them to the stair; pool and tank steel only from their own detail",
        "drawing_method": "hand ledger by flight, landing strip and component from the slab plans and the stair / pool "
                          "details; route G has no stair / pool / tank steel lines, so nothing is superseded"},
    "DOME_RING": {
        "module": "engine/source/arch_v305.py (typed hand-ledger records)", "policy": "DOME_RING_IN_BAY_V1",
        "rule_id": "URBAN-NON-OVERLAPPING-SLAB-BEAM-MODEL", "rule_version": "v1",
        "owner_rules": ["Q-44 A (the ring round each structural dome opening stays)", "Q-61 C(2) / C(3) (never "
                        "duplicate concrete; the B4 section only where the ring is identified as B4, else HELD)",
                        "URBAN-NON-OVERLAPPING-SLAB-BEAM-MODEL@v1", "UP-QTY-STATUS-001"],
        "owner_manual_method": "manual QS take-off: the ring beam at its printed section over the part of the annulus "
                               "inside the bay; the parts inside the straight framing beams stay with those beams",
        "drawing_method": "in-bay annulus by closed-form circle segments (rings, framing faces read from the slab "
                          "plan) x the printed ring depth; route G's partial arc band pieces of the same ring "
                          "superseded (one ring, measured once)"},
}
WAITING = dict(A304.WAITING)
WAITING.pop("SLAB_STEEL", None)
WAITING.update({
    "DOME_SHELL": "dome shells (route G STR.CONC.DOME, convention thickness): dome scenarios S0 / S1 / S2 (T-185, READY "
                  "for the checker), not integrated here",
    "POOL_STEEL_GEOMETRY": "pool steel (T-166 R1 / R2) held blocked: its bar lengths rest on a 1.15 m wall height that "
                           "the checker-merged T-183 r2 replaced by 1.20 m to the structure line; re-derivation needed",
    "SLAB_FACES": "slab faces released only with slab evidence (T-146), after this candidate",
})


class InputsError(ValueError):
    pass


# ================================================================================================ helpers
def _r(x, n=6):
    return None if x is None else round(float(x), n)


def _num(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool) and x == x


def _slug(s):
    return re.sub(r"[^A-Za-z0-9]+", "_", str(s)).strip("_").upper()[:48] or "X"


def _note(ln, text):
    ln["notes"] = (ln.get("notes") + "; " if ln.get("notes") else "") + text


def _change(piece, action, before, after, **kw):
    return dict({"piece": piece, "action": action, "before": before, "after": after}, **kw)


# ================================================================================================ project inputs
def load_inputs(doc, project_id=None):
    """URBAN_V305_VERIFIED_LEDGERS_V1 or None:
        {"schema", "project", "ledgers": [{"piece", "item_code", "unit",
            "source": {"file", "sha256", "task", "merge_commit", "checker_run"},
            "scope": {"physical_element", "floors": [...], "supersede": ELEMENT_AND_FLOORS | NAMED_LINES,
                      "lines": [{"element_id", "floor", "why"}] (NAMED_LINES)},
            "records": [{"element", "component", "part", "floor", "state", "value" | "low"/"high", "reasons",
                         "readings", "verified_by", "info", ...}],
            "declared_totals": {...}}]}"""
    if doc is None:
        return None
    if doc.get("schema") != INPUTS_SCHEMA:
        raise InputsError(f"project inputs: schema must be {INPUTS_SCHEMA}")
    if project_id and doc.get("project") not in (None, project_id):
        raise InputsError(f"project inputs are for {doc.get('project')!r}, the run is {project_id!r}")
    seen = set()
    for lg in doc.get("ledgers") or ():
        p = lg.get("piece")
        if p not in PIECES or p in seen:
            raise InputsError(f"ledger piece {p!r}: one of {sorted(PIECES)}, once each")
        seen.add(p)
        if lg.get("unit") not in UNITS or not lg.get("item_code"):
            raise InputsError(f"ledger {p}: item_code and a unit of {sorted(UNITS)} are required")
        src = lg.get("source") or {}
        for k in ("file", "sha256", "task", "merge_commit", "checker_run"):
            if not src.get(k):
                raise InputsError(f"ledger {p}: source.{k} is required (a ledger without a checker MERGED verdict "
                                  "is not integrated)")
        sc = lg.get("scope") or {}
        if not sc.get("physical_element") or not sc.get("floors"):
            raise InputsError(f"ledger {p}: scope needs physical_element and floors")
        if sc.get("supersede") not in SUPERSEDE:
            raise InputsError(f"ledger {p}: scope.supersede must be one of {SUPERSEDE}")
        if sc["supersede"] == "NAMED_LINES":
            for x in sc.get("lines") or ():
                if not x.get("element_id") or not x.get("floor") or not x.get("why"):
                    raise InputsError(f"ledger {p}: every named route line has element_id, floor and why")
        ids = set()
        for r in lg.get("records") or ():
            st = r.get("state")
            key = (r.get("element"), r.get("component"), r.get("part") or "")
            if not r.get("element") or not r.get("component") or key in ids:
                raise InputsError(f"ledger {p}: every record has a unique element / component / part: {key}")
            ids.add(key)
            if st not in STATES:
                raise InputsError(f"ledger {p} {key}: state {st!r} not one of {STATES}")
            if st == "RELEASED" and not (_num(r.get("value")) and r["value"] >= 0):
                raise InputsError(f"ledger {p} {key}: a RELEASED record carries value >= 0")
            if st == "HELD_RANGE" and not (_num(r.get("low")) and _num(r.get("high")) and 0 <= r["low"] <= r["high"]):
                raise InputsError(f"ledger {p} {key}: a HELD_RANGE record carries 0 <= low <= high")
            if st == "HELD_DEFINED" and not _num(r.get("value")):
                raise InputsError(f"ledger {p} {key}: a HELD_DEFINED record carries its defined value")
            if st != "RELEASED" and not r.get("reasons"):
                raise InputsError(f"ledger {p} {key}: a held record names why it is held")
            if r.get("floor") not in sc["floors"]:
                raise InputsError(f"ledger {p} {key}: floor {r.get('floor')!r} outside the scope {sc['floors']}")
    return doc


# ================================================================================================ ledger lines
def record_line(pid, rev, docs, piece, lg, r):
    """one BOQ line for one ledger record. -> (line, evidence status)"""
    from engine.source import boq_line as BL
    p = PIECES[piece]
    src, unit = lg["source"], lg["unit"]
    st = r["state"]
    reasons = list(r.get("reasons") or ())
    info = dict(r.get("info") or {})
    if st == "HELD_DEFINED":
        info.update(held_defined=_r(r["value"]))
    ev = {"RELEASED": "SOURCE_DERIVED", "HELD_RANGE": "BOUNDED_EXPOSURE"}.get(st, "BLOCKED_RFI")
    rng = None
    if st == "HELD_RANGE":
        rng = {"low": _r(r["low"]), "high": _r(r["high"]), "basis": r.get("range_basis") or "ledger readings"}
    eid = f"HL:{piece}:{r['element']}:{_slug(r['component'])}" + (f":{_slug(r['part'])}" if r.get("part") else "")
    rfi = None if ev == "SOURCE_DERIVED" else {"question": "; ".join(reasons)[:900], "unlocks": eid}
    dia = r.get("dia_mm")
    pe = r.get("physical_element") or lg["scope"]["physical_element"]
    ln = BL.make_line(project_id=pid, revision_set_sha256=rev, item_code=lg["item_code"], unit=unit,
                      evidence_state=ev, measured_net=_r(r["value"]) if ev == "SOURCE_DERIVED" else None,
                      bounded_range=rng, element_id=eid, floor=r["floor"], physical_element=pe,
                      subtrade=pe + (f" / {dia:g} mm" if _num(dia) else ""),
                      formula=r.get("formula") or ("held: " + "; ".join(reasons))[:400],
                      inputs=dict({"policy": p["policy"], "ledger": src["file"], "ledger_sha256": src["sha256"],
                                   "element": r["element"], "component": r["component"], "part": r.get("part"),
                                   "printed": r.get("printed"), "readings": r.get("readings"), "reasons": reasons,
                                   "ledger_state": st}, **info),
                      documents=docs, geometry_source=r.get("geometry_source") or "SCHEDULE_ONLY",
                      geometry_confidence="TOLERANCE_CERTIFIED" if ev == "SOURCE_DERIVED" else "INFERRED_CANDIDATE",
                      rule_id=p["rule_id"], rule_version=p["rule_version"], material_state="SOURCE", rfi=rfi,
                      notes=f"{METHOD}: {piece.lower().replace('_', ' ')} by hand ledger ({src['task']}, "
                            f"MERGED {src['merge_commit']})")
    if st == "RELEASED":
        evs = "VERIFIED" if r.get("verified_by") else "DRAWING-CONFIRMED"
    elif st == "UNQUANTIFIED":
        evs = "UNKNOWN"
    else:
        evs = "HELD"
    return ln, evs


def _route_lines(lg, lines):
    """the route G lines a ledger replaces (refused when a named line is not there exactly once)."""
    sc = lg["scope"]
    floors = set(sc["floors"])
    trade = UNITS[lg["unit"]]
    if sc["supersede"] == "ELEMENT_AND_FLOORS":
        return [(ln, None) for ln in lines if ln["item_code"] == lg["item_code"] and ln["trade"] == trade
                and str(ln.get("physical_element")) == sc["physical_element"]
                and (ln.get("location") or {}).get("floor") in floors]
    out = []
    for x in sc.get("lines") or ():
        hit = [ln for ln in lines if (ln.get("location") or {}).get("element_id") == x["element_id"]
               and (ln.get("location") or {}).get("floor") == x["floor"] and ln["item_code"] == lg["item_code"]]
        if len(hit) != 1 or x["floor"] not in floors:
            raise InputsError(f"ledger {lg['piece']}: named route line {x['element_id']} {x['floor']} found "
                              f"{len(hit)} time(s) (exactly one {lg['item_code']} line on a floor in scope is "
                              "required): nothing is superseded silently")
        out.append((hit[0], x["why"]))
    return out


def ledger_changes(inputs, lines, earlier_changed=()):
    """the ledgers of the project inputs on the V3.0.4 lines. -> (changes, logs)"""
    logs = []
    if not inputs:
        return [], [{"piece": p, "state": "NO_PROJECT_INPUT"} for p in PIECES]
    pid, rev, docs = A302._proj(lines)
    have = {ln["line_id"] for ln in lines}
    earlier = set(earlier_changed)
    changes, done, replaced = [], set(), set()
    for lg in inputs.get("ledgers") or ():
        piece, src, sc = lg["piece"], lg["source"], lg["scope"]
        done.add(piece)
        verif = {"task": src["task"], "merge_commit": src["merge_commit"], "verifier_run": src["checker_run"],
                 "ledger": src["file"], "ledger_sha256": src["sha256"]}
        ref = lg.get("drawing_reference") or src["file"]
        log = {"piece": piece, "state": "RUN", "ledger": src["file"], "ledger_sha256": src["sha256"], "scope": sc,
               "item_code": lg["item_code"], "unit": lg["unit"], "route_lines": 0, "route_value": 0.0,
               "route_bounded_low": 0.0, "route_bounded_high": 0.0, "route_by_floor": {}, "by_floor": {},
               "evidence_status": {}}
        for o, why in _route_lines(lg, lines):
            lid = o["line_id"]
            if lid in earlier:
                raise ValueError(f"{METHOD}: route line {lid} was changed by an earlier version; V3.0.5 never "
                                 "replaces it")
            if lid in replaced:
                raise ValueError(f"{METHOD}: route line {lid} replaced by two V3.0.5 ledgers")
            replaced.add(lid)
            q = A30._qty(o)
            fl = o["location"]["floor"]
            log["route_lines"] += 1
            rb = log["route_by_floor"].setdefault(fl, {"lines": 0, "value": 0.0, "bounded_low": 0.0,
                                                       "bounded_high": 0.0})
            rb["lines"] += 1
            if q["value"] is not None and o["evidence_state"] not in ("NOT_APPLICABLE_WITH_EVIDENCE",
                                                                      "EXCLUDED_WITH_REASON", "BLOCKED_RFI"):
                log["route_value"] += q["value"]
                rb["value"] += q["value"]
            elif q["low"] is not None:
                log["route_bounded_low"] += q["low"]
                log["route_bounded_high"] += q["high"]
                rb["bounded_low"] += q["low"]
                rb["bounded_high"] += q["high"]
            after = copy.deepcopy(o)
            after.update(evidence_state="NOT_APPLICABLE_WITH_EVIDENCE", measured_net=None, bounded_range=None,
                         rfi=None)
            _note(after, f"{METHOD}: SUPERSEDED - route G {o['evidence_state']} {A302._q(q)} {o['unit']} is replaced "
                         f"by the {src['task']} hand ledger lines of {sc['physical_element']} {fl} (MERGED "
                         f"{src['merge_commit']})" + (f": {why}" if why else ""))
            changes.append(_change(piece, "REPLACE", o, after, drawing_reference=ref, held=[], downstream=[],
                                   verification=verif, evidence_status="DRAWING-CONFIRMED"))
        for r in lg.get("records") or ():
            ln, evs = record_line(pid, rev, docs, piece, lg, r)
            if ln["line_id"] in have:
                raise ValueError(f"{METHOD}: ledger line {r['element']} {r['component']} repeats a V3.0.4 line id")
            held = []
            if ln["evidence_state"] != "SOURCE_DERIVED":
                held = [{"what": f"{r['element']} {r['component']}" + (f" {r['part']}" if r.get("part") else ""),
                         "why": ln["rfi"]["question"],
                         "range": [ln["bounded_range"]["low"], ln["bounded_range"]["high"]]
                         if ln.get("bounded_range") else None}]
            changes.append(_change(piece, "ADD", None, ln, drawing_reference=r.get("printed") or ref, held=held,
                                   downstream=list(r.get("downstream") or ()),
                                   verification=dict(verif, record_verified_by=r.get("verified_by")),
                                   evidence_status=evs))
            b = log["by_floor"].setdefault(r["floor"], {"lines": 0, "released": 0.0, "held_low": 0.0,
                                                        "held_high": 0.0, "held_defined": 0.0, "unquantified": 0})
            b["lines"] += 1
            if r["state"] == "RELEASED":
                b["released"] += r["value"]
            elif r["state"] == "HELD_RANGE":
                b["held_low"] += r["low"]
                b["held_high"] += r["high"]
            elif r["state"] == "HELD_DEFINED":
                b["held_defined"] += r["value"]
            else:
                b["unquantified"] += 1
            log["evidence_status"][evs] = log["evidence_status"].get(evs, 0) + 1
        tot = {}
        for v in log["by_floor"].values():
            for k, x in v.items():
                tot[k] = tot.get(k, 0) + x
        log["totals"] = {k: _r(v) if isinstance(v, float) else v for k, v in sorted(tot.items())}
        for d in (log["route_by_floor"], log["by_floor"]):
            for v in d.values():
                for k in list(v):
                    if isinstance(v[k], float):
                        v[k] = _r(v[k])
        for k in ("route_value", "route_bounded_low", "route_bounded_high"):
            log[k] = _r(log[k])
        dec = lg.get("declared_totals") or {}
        for k, v in dec.items():
            if k in log["totals"] and abs((log["totals"][k] or 0) - v) > 0.006:
                raise ValueError(f"{METHOD}: ledger {piece} {k} {log['totals'][k]} != the ledger's own total {v}")
        log["declared_totals"] = dec
        logs.append(log)
    for p in PIECES:
        if p not in done:
            logs.append({"piece": p, "state": "NO_PROJECT_INPUT"})
    return changes, logs


# ================================================================================================ integrate / ledger
def integrate(l304, v305_changes):
    """-> (V3.0.5 lines, identity). Every line outside the V3.0.5 rows is byte-identical to the V3.0.4 line; a line
    two V3.0.5 rows change, an added line repeating an id, or a row naming a line V3.0.4 does not have, is refused."""
    from engine.source import boq_line as BL
    sid = {ln["line_id"] for ln in l304}
    rep, adds = {}, []
    for c in v305_changes:
        if c["action"] == "REPLACE":
            lid = c["before"]["line_id"]
            if lid in rep:
                raise ValueError(f"{METHOD}: line {lid} changed twice")
            if lid not in sid:
                raise ValueError(f"{METHOD}: a change names a line the V3.0.4 run does not have")
            if c["after"]["line_id"] != lid:
                raise ValueError(f"{METHOD}: a superseded line keeps its line id")
            rep[lid] = c["after"]
        elif c["action"] == "ADD":
            if c["after"]["line_id"] in sid:
                raise ValueError(f"{METHOD}: an added line repeats a V3.0.4 line id")
            adds.append(c["after"])
        else:
            raise ValueError(f"{METHOD}: action {c['action']}")
    out = [rep.get(ln["line_id"], ln) for ln in l304] + adds
    if len({ln["line_id"] for ln in out}) != len(out):
        raise ValueError(f"{METHOD}: a BOQ line id appears twice")
    for ln in out:
        BL.validate(ln)
    by304 = {ln["line_id"]: ln for ln in l304}
    touched = set(rep) | {a["line_id"] for a in adds}
    outside = [ln for ln in out if ln["line_id"] not in touched]
    bad = [ln["line_id"] for ln in outside if A30.line_sha(by304[ln["line_id"]]) != A30.line_sha(ln)]
    if bad or len(outside) + len(rep) != len(l304):
        raise ValueError(f"{METHOD}: {len(bad)} line(s) outside the V3.0.5 rows differ from {EXTENDS}")
    ident = {"v3_0_4_lines": len(l304), "v3_0_5_lines": len(out), "v3_0_5_rows": len(v305_changes),
             "replaced": len(rep), "added": len(adds), "outside_rows": len(outside),
             "outside_rows_identical_to_v3_0_4": len(outside),
             "outside_rows_sha256": hashlib.sha256("".join(A30.line_sha(x) for x in outside).encode()).hexdigest()}
    return out, ident


def ledger_rows(changes, released_lines=None):
    rel = {A30._key(ln): ln for ln in released_lines or ()}
    rows = []
    for c in changes:
        ref = c["after"] if c["before"] is None else c["before"]
        b304 = A30._qty(c["before"]) if c["before"] is not None else dict(A30._qty(None), state="NOT_IN_V3_0_4")
        aft = A30._qty(c["after"])
        b29 = None
        if released_lines is not None:
            b29 = A30._qty(rel[A30._key(ref)]) if A30._key(ref) in rel else dict(A30._qty(None),
                                                                                 state="NOT_IN_RELEASED")
        p = PIECES[c["piece"]]
        loc = ref.get("location") or {}
        rows.append({"version": METHOD, "piece": c["piece"], "action": c["action"], "line_id": ref["line_id"],
                     "item_code": ref["item_code"], "floor": loc.get("floor"),
                     "element_id": c["after"]["location"].get("element_id"), "unit": c["after"]["unit"],
                     "before_released_v2_9": b29, "before_v3_0_4": b304, "after_v3_0_5": aft,
                     "evidence_status": c.get("evidence_status") or "HELD", "release_status": "NOT RELEASED",
                     "drawing_reference": c.get("drawing_reference"),
                     "owner_manual_method": p["owner_manual_method"], "drawing_method": p["drawing_method"],
                     "owner_rules": p["owner_rules"],
                     "verification": dict(c.get("verification") or {}, module=p["module"], policy=p["policy"]),
                     "held": c.get("held") or [], "downstream": c.get("downstream") or [], "rollback": ROLLBACK})
    return rows


LEDGER_CSV = ("version", "piece", "action", "line_id", "item_code", "floor", "element_id", "unit", "v2_9", "v3_0_4",
              "v3_0_5", "evidence_status", "release_status", "drawing_reference", "verification", "held")


def _csv(rows, cols):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=cols, lineterminator="\n", extrasaction="ignore")
    w.writeheader()
    w.writerows(rows)
    return buf.getvalue()


def ledger_csv(rows):
    return _csv([{"version": r["version"], "piece": r["piece"], "action": r["action"], "line_id": r["line_id"],
                  "item_code": r["item_code"], "floor": r["floor"], "element_id": r["element_id"], "unit": r["unit"],
                  "v2_9": A302._q(r["before_released_v2_9"]), "v3_0_4": A302._q(r["before_v3_0_4"]),
                  "v3_0_5": A302._q(r["after_v3_0_5"]), "evidence_status": r["evidence_status"],
                  "release_status": r["release_status"], "drawing_reference": str(r["drawing_reference"])[:300],
                  "verification": f"{r['verification'].get('task')} {r['verification'].get('merge_commit')}"
                                  + (f" / {r['verification']['record_verified_by']}"
                                     if r["verification"].get("record_verified_by") else ""),
                  "held": "; ".join(str(h.get("why") or h.get("what")) for h in r["held"])[:600]} for r in rows],
                LEDGER_CSV)


DIFF_CSV = ("line_id", "item_code", "floor", "element_id", "unit", "vs_v3_0_4", "vs_released_v2_9", "v2_9", "v3_0_4",
            "v3_0_5")


def diff_rows(l304, l305, released_lines=None):
    b304 = {ln["line_id"]: ln for ln in l304}
    rel = {A30._key(ln): ln for ln in released_lines or ()}
    out = []
    for ln in l305:
        o = b304.get(ln["line_id"])
        vs = "ADDED" if o is None else ("SAME" if A30.line_sha(o) == A30.line_sha(ln) else "CHANGED")
        r = rel.get(A30._key(ln)) if released_lines is not None else None
        vs29 = None if released_lines is None else ("NOT_IN_RELEASED" if r is None else
                                                    ("SAME_QUANTITY" if A30._qty(r) == A30._qty(ln) else
                                                     "QUANTITY_DIFFERS"))
        out.append({"line_id": ln["line_id"], "item_code": ln["item_code"], "floor": ln["location"].get("floor"),
                    "element_id": ln["location"].get("element_id"), "unit": ln["unit"], "vs_v3_0_4": vs,
                    "vs_released_v2_9": vs29, "v2_9": A302._q(A30._qty(r)) if r else "",
                    "v3_0_4": A302._q(A30._qty(o)) if o else "", "v3_0_5": A302._q(A30._qty(ln))})
    return out


def write(out, l304, v305_changes, logs, inputs, released_lines=None):
    """the V3_0_5_* files beside the V3_0_4_* files. -> (file names, identity, ledger)."""
    from pathlib import Path
    from engine.source import boq_line as BL
    out = Path(out)
    l305, ident = integrate(l304, v305_changes)
    rows = ledger_rows(v305_changes, released_lines)
    diff = diff_rows(l304, l305, released_lines)
    dsum = {}
    for d in diff:
        dsum.setdefault("vs_v3_0_4", {}).setdefault(d["vs_v3_0_4"], 0)
        dsum["vs_v3_0_4"][d["vs_v3_0_4"]] += 1
        if d["vs_released_v2_9"] is not None:
            dsum.setdefault("vs_released_v2_9", {}).setdefault(d["vs_released_v2_9"], 0)
            dsum["vs_released_v2_9"][d["vs_released_v2_9"]] += 1
    ident = dict(ident, diff=dsum)
    led = {"schema": LEDGER_SCHEMA, "method": METHOD, "extends": EXTENDS, "candidate": CANDIDATE,
           "base": A30.BASE_METHOD, "released": A30.RELEASED_METHOD, "released_default": False, "rows": rows,
           "waiting_pieces": WAITING, "integration_package": True}
    t304, t305 = A304.code_totals(l304), A304.code_totals(l305)
    moved = {k: {"v3_0_4": t304.get(k), "v3_0_5": t305.get(k)} for k in sorted(set(t304) | set(t305))
             if t304.get(k) != t305.get(k)}
    down = [dict(d, from_line=r["line_id"], piece=r["piece"]) for r in rows for d in r["downstream"]]
    run = {"method": METHOD, "policy": POLICY_ID, "extends": EXTENDS, "candidate": CANDIDATE,
           "base_method": A30.BASE_METHOD, "released_method": A30.RELEASED_METHOD, "released_default": False,
           "rollback": ROLLBACK, "identity": ident, "pieces": PIECES, "piece_logs": logs,
           "inputs_ledgers": [{k: lg.get(k) for k in ("piece", "item_code", "unit", "source", "scope",
                                                       "declared_totals")}
                              for lg in (inputs or {}).get("ledgers") or ()],
           "totals_moved_by_code": moved, "waiting_pieces": WAITING,
           "evidence_status_counts": A302._count(r["evidence_status"] for r in rows)}
    files = {"V3_0_5_BOQ_LINES.json": BL.dumps(l305),
             "V3_0_5_BOQ_LINES.csv": A30._lines_csv(l305),
             "V3_0_5_INTEGRATION_LEDGER.json": A30._j(led),
             "V3_0_5_INTEGRATION_LEDGER.csv": ledger_csv(rows),
             "V3_0_5_DIFF.csv": _csv(diff, DIFF_CSV),
             "V3_0_5_DOWNSTREAM.json": A30._j({"method": METHOD, "rows": down}),
             "V3_0_5_RUN.json": A30._j(run)}
    for name, text in files.items():
        (out / name).write_text(text, encoding="utf-8")
    return sorted(files), ident, led


def policy_record():
    return {"method": METHOD, "extends": EXTENDS, "pieces": sorted(PIECES), "inputs_schema": INPUTS_SCHEMA,
            "released_default": False, "rollback": ROLLBACK}


__all__ = ["METHOD", "PIECES", "WAITING", "load_inputs", "record_line", "ledger_changes", "integrate", "ledger_rows",
           "diff_rows", "write", "InputsError"]
