"""ARCH_TAKEOFF_V3.0.1 (T-133): the SAME opt-in BOQ candidate as ARCH_TAKEOFF_V3.0 (engine.source.arch_v30), extended
with checker-verified pieces that waited for the skeleton. Not a new method family and not the released default (owner
management decision 2026-10-20 sections 2 and 5); rollback is running the released ARCH_TAKEOFF_V2.9.

How it is built (tools/urban_boq_m9.py `arch --method ARCH_TAKEOFF_V3.0.1`):
  1. the run is the V3.0 candidate exactly: ARCH_TAKEOFF_V2.13 + route G, its outputs unchanged, the V3_0_* files
     written unchanged (arch_v30 is not edited);
  2. the V3.0.1 pieces below propose changes of named lines of the same base run; a line a V3.0 piece already
     changed is never changed again (integrate refuses it);
  3. the V3_0_1_* files are written beside the V3_0_* files: every line outside the V3.0.1 rows is byte-identical
     to the V3.0 candidate line (asserted on every run: identity.vs_v3_0), and with the released V2.9 lines every
     line outside the ledger is byte-identical to V2.9 (arch_v30.released_identity).

Pieces added in V3.0.1 (each carries a verifier MERGED verdict; PIECES names task, merge commit and verifier run):
  ROUTE_G_SCOPE      ROUTE_G_SCOPE_V1 (T-126) on the route G result:
                     columns  a column piece above the necks is RELEASED only where the roof-slab plan of its storey
                              draws it; a piece the plan does not draw becomes NOT_APPLICABLE_WITH_EVIDENCE (listed by
                              name with the plan and the nearest outline, never a silent 0, never deleted); a piece
                              whose presence cannot be read becomes its held line (BOUNDED_EXPOSURE 0 .. route value);
                              reinforcement lines of those pieces are NOT changed (rebar is its own line family,
                              outside this candidate): they are listed as downstream STALE for review;
                     blinding the two route lines (footing layer, ground-beam layer) become the family lines: the
                              footings whose own concrete is released (RELEASED), each footing in conflict held with
                              its range (owner Q-31 C), the ground-beam blinding held as a range while the founding
                              detail is open (owner Q-21 C), the strap blinding held until a strap section prints it
                              (designer request): separate lines, never summed into one value, never 0.
  MEMBRANE_AUDIT_V5  MEMBRANE_FOLD_V5 (T-124) audit of every V2.13 roll line: the area the run folded is folded
                     again by V5 (one set of rolls, every offcut booked once) and the V3 Q-58 A counts audited
                     (VALID / INVALID / NOT_PROVEN). No count changes: the audit is attached to the line as its
                     evidence field (calculation.inputs.v3_0_1_membrane_audit); a line the audit contradicts keeps
                     its count, carries the flag and is listed held in the ledger for the checker. A roll line whose
                     area cannot be identified carries NOT_AUDITED with the reason.

Waiting (listed in WAITING, never silently dropped): the finish moves of T-122 / T-129 (hand ledgers only: a wiring
piece that reads the landing from the drawing is still needed), STAIR_FLIGHT_ONCE_V1 (T-135, needs the slab-above
evidence read from the structural drawing by a generic reader), the stair ledger of T-111 (hand ledger), concrete ledger
V3 beams and stair concrete V1 (T-105) and the section-cut spans (T-102) on the route G beam lines.

Rules: owner decision 2026-10-20 sections 2 and 5, Q-17 A, Q-21 C, Q-31 C, Q-49 A, Q-58 A, URBAN-NON-OVERLAPPING-SLAB-
BEAM-MODEL@v1, UP-QTY-STATUS-001 (held is a range or blocked, never 0). Nothing here names a project, a sheet, a
layer, a mark or a coordinate; every number comes from the run or the drawings.
"""

from __future__ import annotations

import copy
import hashlib
import json
from contextlib import contextmanager

from engine.source import arch_v30 as A30

METHOD = "ARCH_TAKEOFF_V3.0.1"
CANDIDATE = A30.METHOD                       # the candidate this version extends (never a new method family)
POLICY_ID = "URBAN_BOQ_T133_ARCH_V3_0_1"
LEDGER_SCHEMA = "URBAN_V301_INTEGRATION_LEDGER_V1"
ROLLBACK = A30.ROLLBACK
BLINDING_PREFIX = "PLAIN_CONCRETE:FOUNDATION:BLINDING_"
# the route's two blinding lines and the family line that takes each one's place (the others are added lines)
BLINDING_PAIRS = {BLINDING_PREFIX + "FOOTINGS": BLINDING_PREFIX + "FOOTINGS_RELEASED",
                  BLINDING_PREFIX + "GROUND_BEAMS": BLINDING_PREFIX + "GROUND_BEAM"}
STEEL_TRADE = "REINFORCEMENT"

PIECES = {
    "ROUTE_G_SCOPE": {
        "module": "engine/source/route_g_scope_v1.py", "policy": "ROUTE_G_SCOPE_V1", "task": "T-126",
        "merge_commit": "cd34bd0", "verifier_run": "run 46 (2026-10-20 21:58 UTC), footing union re-measured",
        "owner_rules": ["Q-17 A (drawing first: a column piece only where its storey plan draws it)",
                        "Q-21 C (ground-beam blinding: the founding level decides the detail, held)",
                        "Q-31 C (footing in conflict: held with its range)",
                        "URBAN-NON-OVERLAPPING-SLAB-BEAM-MODEL@v1", "UP-QTY-STATUS-001"],
        "owner_manual_method": None,
        "owner_manual_note": "no separate owner manual method for column presence or blinding scope: the owner "
                             "answers (Q-17 A, Q-21 C, Q-31 C) bind the drawing method",
        "drawing_method": "ROUTE_G_SCOPE_V1: a column piece counted where the storey's roof-slab plan draws an outline "
                          "at its position (column-plan outline, else the same mark's foundation outline, else one "
                          "outline at a printed section); blinding per member family, each m2 once"},
    "MEMBRANE_AUDIT_V5": {
        "module": "engine/source/membrane_fold_v5.py", "policy": "MEMBRANE_FOLD_V5", "task": "T-124",
        "merge_commit": "f47ae01", "verifier_run": "run 45 (2026-10-20 21:05 UTC)",
        "owner_rules": ["Q-49 A (rolls per area alone)", "Q-58 A conditional (proven cutting plan)",
                        "owner 2026-10-20 17:54 (5) (ledger kept apart per layout)"],
        "owner_manual_method": "owner Q-49 A / Q-58 A: rolls per area, a piece cut from that area's own offcut only "
                               "on a proven physical cutting plan",
        "drawing_method": "MEMBRANE_FOLD_V5: the V4 layouts counted on one set of rolls (every leftover booked once) "
                          "and the V3 Q-58 A count audited on the rolls V3 itself packs"},
}
WAITING = {
    "T-122": "1F landing to stair marble once, 1F living porcelain range 33.594 .. 33.711 m2 (owner Q-66 B): hand "
             "ledger only; a piece that reads the landing outline from the drawing is still needed",
    "T-129": "2F arrival 4.875 m2 marble and 2.500 m2 porcelain in front of the stair (owner Q-70 A cond): hand "
             "ledger only; same wiring piece as T-122",
    "T-135": "STAIR_FLIGHT_ONCE_V1 (tread marble / step lm counted once): needs the slab-above evidence from the "
             "structural drawing; the reader of the T-135 research run names sheet titles and layers of one project",
    "T-111": "main stair 4.920 m3 owner basis / 4.746 drawn, entrance and round stair HELD on a missing drawing, "
             "slab under the winders 0.230 .. 0.250 m3 HELD: hand ledger only",
    "T-105": "CONCRETE_LEDGER_V3 beams and STAIR_CONCRETE_V1 on the route G beam / stair lines: not wired here",
    "T-102": "BEAM_SECTION_CUT_BINDING (two section-cut spans): rides with the T-105 beam ledger",
    "T-136 / T-137 / T-127": "ARCH_TAKEOFF_V3.0.2 (T-142)",
}


# ================================================================================================ capture
@contextmanager
def capture():
    """read-only: every membrane area the run folds (MEMBRANE_FOLD_V3.area keyword arguments), so the V5 audit folds
    the same outline. Results are returned unchanged."""
    from engine.source import membrane_fold_v3 as F3
    cap = []
    o_area = F3.area

    def area(**kw):
        res = o_area(**kw)
        cap.append({k: kw.get(k) for k in ("floor", "room_id", "polygon", "holes", "unit_m", "name", "spec")})
        return res
    F3.area = area
    try:
        yield cap
    finally:
        F3.area = o_area


# ================================================================================================ helpers
def _r(x, n=6):
    return None if x is None else round(float(x), n)


def _note(ln, text):
    ln["notes"] = (ln.get("notes") + "; " if ln.get("notes") else "") + text


def _change(piece, action, before, after, **kw):
    return dict({"piece": piece, "action": action, "before": before, "after": after}, **kw)


def _inputs(ln, key, rec):
    ln["calculation"] = dict(ln["calculation"], inputs=dict(ln["calculation"].get("inputs") or {}, **{key: rec}))


# ================================================================================================ ROUTE_G_SCOPE
def scope_changes(R, base_lines, to_line, *, beam_detail=None, strap_blinding_printed=False):
    """ROUTE_G_SCOPE_V1 on the route G result R. to_line(item) -> the canonical line of a route G item (the run's
    own converter, tools.urban_boq_m9.structural_lines). -> (changes, log)."""
    from engine.source import route_g_scope_v1 as SC
    log = {"piece": "ROUTE_G_SCOPE", "state": "NOT_RUN", "columns": [], "blinding": None}
    if R is None or not ((R.get("generic") or {}).get("D")):
        log["state"] = "NO_ROUTE_G_RESULT"
        return [], log
    sc = SC.measure(R, beam_detail=beam_detail, strap_blinding_printed=strap_blinding_printed)
    new_items = SC.apply(R, sc)
    by_elem = {}
    for ln in base_lines:
        if str(ln["item_code"]).startswith("STR."):
            by_elem.setdefault((ln.get("location") or {}).get("element_id"), []).append(ln)

    def one(item_id):
        hits = by_elem.get(item_id) or []
        return hits[0] if len(hits) == 1 else None
    new_by_id = {it["item_id"]: it for it in new_items}
    changes = []
    log["state"] = "RUN"
    steel_down = []
    for c in sc["columns"]:
        rec = {k: c.get(k) for k in ("component_id", "mark", "storey", "status", "basis", "plan", "nearest_outline_m",
                                     "route_m3", "reason")}
        if c["status"] == "RELEASED" or c.get("route_category") == "UNRESOLVED" or not c.get("item_ids"):
            log["columns"].append(dict(rec, change="NONE" if c["status"] != "NOT_PRESENT" else
                                       "NONE (the route counts nothing here: listed)"))
            continue
        ref = (f"structural set: {c['storey']} roof-slab plan" + (f" {c['plan']}" if c.get("plan") else "") +
               f", column piece {c['component_id']}")
        held_item = None
        if c["status"] == "HELD":
            held_item = new_by_id.get(f"U-C:{c['component_id']}")
        concrete_done = False
        for iid in c["item_ids"]:
            base = one(iid)
            if base is None:
                log["columns"].append(dict(rec, change="KEPT_LINE_NOT_FOUND_ONCE", item=iid))
                continue
            if base["trade"] == STEEL_TRADE:
                steel_down.append({"line_id": base["line_id"], "item_code": base["item_code"],
                                   "reads": f"column piece {c['component_id']} ({c['status']})",
                                   "v3_0_1": "UNCHANGED, STALE: the concrete piece is " + c["status"] +
                                             "; reinforcement stays its own line family, outside this candidate"})
                continue
            if c["status"] == "HELD" and base["trade"] == "CONCRETE" and held_item is not None and not concrete_done:
                after = to_line(held_item)
                concrete_done = True
                _note(after, f"{METHOD}: column piece held (ROUTE_G_SCOPE_V1, T-126): {c['reason']}")
            else:
                after = copy.deepcopy(base)
                after["measured_net"] = None
                after["bounded_range"] = None
                if c["status"] == "NOT_PRESENT":
                    after["evidence_state"] = "NOT_APPLICABLE_WITH_EVIDENCE"
                    after["rfi"] = None
                    after["notes"] = (f"{METHOD}: NOT_PRESENT - {c['reason']} (ROUTE_G_SCOPE_V1, T-126; owner Q-17 A)"
                                      f"; was {_r(base.get('measured_net'))} {base['unit']} in {A30.BASE_METHOD}")
                else:
                    after["evidence_state"] = "BLOCKED_RFI"
                    after["rfi"] = {"question": f"COLUMN_PRESENCE_UNVERIFIED: {c['reason']}",
                                    "unlocks": c["component_id"]}
                    _note(after, f"{METHOD}: held with its column piece (ROUTE_G_SCOPE_V1, T-126)")
            _inputs(after, "v3_0_1", {"policy": SC.METHOD, "status": c["status"], "basis": c.get("basis"),
                                      "plan": c.get("plan"), "nearest_outline_m": c.get("nearest_outline_m"),
                                      "route_m3": c.get("route_m3"), "section_m": c.get("section_m"),
                                      "height_m": c.get("height_m")})
            held = []
            if c["status"] == "HELD":
                held.append({"what": f"column piece {c['component_id']}", "why": c["reason"],
                             "range": [0.0, c.get("route_m3")] if base["trade"] == "CONCRETE" else None})
            changes.append(_change("ROUTE_G_SCOPE", "REPLACE", base, after, drawing_reference=ref, held=held,
                                   downstream=[]))
        log["columns"].append(dict(rec, change="CHANGED"))
    if steel_down and changes:
        changes[0]["downstream"] = changes[0]["downstream"] + steel_down
    log["steel_stale"] = steel_down
    log["columns_by_storey"] = sc["columns_by_storey"]
    # blinding: the route's family lines -> the family records of the piece
    bl = sc["blinding"]
    log["blinding"] = {k: bl.get(k) for k in ("state", "reason", "released_m3", "released_footing_m3",
                                              "held_exposure_m3", "total_range_m3", "thickness_m", "projection_m",
                                              "registration")}
    log["blinding"]["records"] = [{k: r.get(k) for k in ("family", "member", "mark", "status", "m3", "exposure_m3",
                                                         "blocker", "reason")} for r in bl.get("records") or ()]
    if bl.get("state") == "MEASURED":
        old = [it for it in R["items"] if it.get("family") == "PLAIN_CONCRETE"
               and (it.get("component_id") or "").startswith(BLINDING_PREFIX)]
        new = [it for it in new_items if it.get("family") == "PLAIN_CONCRETE"
               and (it.get("component_id") or "").startswith(BLINDING_PREFIX) and it["item_id"] not in
               {o["item_id"] for o in old}]
        ref = "structural set: foundation plan (footing outlines), ground-beam plan (beam strips), strap bands; " \
              "typical detail (blinding thickness and projection)"
        held_all = [{"what": f"blinding {r['family']}" + (f" {r.get('member')}" if r.get("member") else ""),
                     "why": r.get("reason"), "blocker": r.get("blocker"), "range_m3": r.get("exposure_m3")}
                    for r in bl.get("records") or () if r["status"] == "HELD"]
        used = set()
        for o in old:
            base = one(o["item_id"])
            if base is None:
                log["blinding"]["kept"] = (log["blinding"].get("kept") or []) + [o["item_id"]]
                continue
            pair = BLINDING_PAIRS.get(o.get("component_id"))
            nit = next((n for n in new if n.get("component_id") == pair and n["item_id"] not in used), None)
            if nit is not None:
                used.add(nit["item_id"])
                after = to_line(nit)
                _note(after, f"{METHOD}: blinding by member family (ROUTE_G_SCOPE_V1, T-126); replaces the route's "
                             f"{o.get('component_id')} ({_r(base.get('measured_net'))} m3)")
            else:
                after = copy.deepcopy(base)
                after["evidence_state"] = "NOT_APPLICABLE_WITH_EVIDENCE"
                after["measured_net"] = None
                after["bounded_range"] = None
                after["rfi"] = None
                after["notes"] = (f"{METHOD}: SUPERSEDED - the route's {o.get('component_id')} "
                                  f"({_r(base.get('measured_net'))} m3) is replaced by the blinding family lines of "
                                  "ROUTE_G_SCOPE_V1 (T-126), each m2 once")
            changes.append(_change("ROUTE_G_SCOPE", "REPLACE", base, after, drawing_reference=ref,
                                   held=held_all if o is old[0] else [], downstream=[]))
        for n in new:
            if n["item_id"] in used:
                continue
            after = to_line(n)
            _note(after, f"{METHOD}: blinding by member family (ROUTE_G_SCOPE_V1, T-126)")
            changes.append(_change("ROUTE_G_SCOPE", "ADD", None, after, drawing_reference=ref, held=[], downstream=[]))
    return changes, log


# ================================================================================================ MEMBRANE_AUDIT_V5
def _area_for(line, areas):
    """the captured area of a roll line: the same floor and room id, else the one area of the floor whose id ends
    with the line's last id part (roofs: '<room>:<text>' vs '<floor>-<code>-<text>'); else None."""
    loc = line.get("location") or {}
    fl, rid = loc.get("floor"), str(loc.get("room_id") or "")
    same = [a for a in areas if a.get("floor") == fl and str(a.get("room_id")) == rid]
    if not same:
        tail = rid.rsplit("-", 1)[-1]
        same = [a for a in areas if a.get("floor") == fl and tail and str(a.get("room_id") or "").rsplit(":", 1)[-1]
                == tail and ":" in str(a.get("room_id") or "")]
    keys = {(repr(a["polygon"]), repr(tuple(a.get("holes") or ())), a.get("unit_m")) for a in same}
    return same[-1] if same and len(keys) == 1 else None


def audit_area(area):
    """MEMBRANE_FOLD_V5 on one captured area -> the audit record (never raises: a fold error is NOT_AUDITED)."""
    from engine.source import membrane_fold_v5 as F5
    try:
        f = F5.fold(area["polygon"], holes=area.get("holes") or (), unit_m=area.get("unit_m") or 1.0,
                    spec=area.get("spec"))
    except F5.FoldError as ex:
        return {"state": "NOT_AUDITED", "why": f"MEMBRANE_FOLD_V5 cannot fold the outline: {ex}"}
    sp = f["spec"]
    v3 = []
    for x in f["layouts_v3"]:
        au = F5.audit_v3(x, sp)
        v3.append({"layout": f"{x['direction']} / {x['start']}", "claimed_q58_a": x["rolls_by_basis"]["Q58_A"],
                   "verdict": au["verdict"], "why": au.get("why"), "corrected": au.get("corrected")})
    ch = f["choice_v5"]
    return {"state": "AUDITED", "policy": F5.METHOD_ID, "floor_m2": _r(f["floor_m2"], 4),
            "v5_state": ch["state"], "v5_by_reading": {b: x["rolls"] for b, x in ch["by_reading"].items()},
            "v5_q58_a_layout": ch["q58_a"]["name"], "v5_ledger": ch["q58_a"]["ledger"],
            "v3_layouts": v3, "flags_v5": list(f["flags_v5"])}


def _line_rolls(ln):
    """the line's count: a released value, a range, or None (held)."""
    if ln.get("measured_net") is not None:
        return {"value": ln["measured_net"]}
    br = ln.get("bounded_range") or {}
    if br.get("low") is not None:
        return {"low": br["low"], "high": br["high"]}
    return None


def agreement(ln, au):
    """does the V5 audit support the line's count? AGREES / DIFFERS / NOT_COMPARABLE (never changes the count)."""
    if au.get("state") != "AUDITED":
        return "NOT_COMPARABLE"
    lr, rd = _line_rolls(ln), au["v5_by_reading"]
    if lr is None:
        return "NOT_COMPARABLE"
    if "value" in lr:
        # a released count is supported when V5 shows a real plan with that many rolls under one reading (a V3
        # layout whose own count is INVALID stays listed in v3_layouts: V5's pieces may still make it real)
        return "AGREES" if lr["value"] in [v for v in rd.values() if v is not None] else "DIFFERS"
    known = [v for v in rd.values() if v is not None]
    if not known:
        return "NOT_COMPARABLE"
    return "AGREES" if lr["low"] <= min(known) and max(known) <= lr["high"] else "DIFFERS"


def membrane_changes(areas, base_lines, *, audit=audit_area):
    """the V5 audit attached to every roll line as its evidence; counts unchanged. -> (changes, log)."""
    log = {"piece": "MEMBRANE_AUDIT_V5", "lines": []}
    changes = []
    cache = {}
    for ln in base_lines:
        if ln["item_code"] not in A30.MEMBRANE_ITEMS:
            continue
        loc = ln.get("location") or {}
        a = _area_for(ln, areas or ())
        if a is None and _line_rolls(ln) is None:
            au = {"state": "NOT_AUDITED", "why": "HELD_LINE_NO_AREA_FOLDED: the line holds the area without a count "
                                                 "(the run folded no outline for it)"}
        elif a is None:
            au = {"state": "NOT_AUDITED", "why": "the area the run folded for this line is not identified once"}
        else:
            k = (repr(a["polygon"]), repr(tuple(a.get("holes") or ())), a.get("unit_m"), repr(a.get("spec")))
            if k not in cache:
                cache[k] = audit(a)
            au = cache[k]
        verdict = agreement(ln, au)
        after = copy.deepcopy(ln)
        _inputs(after, "v3_0_1_membrane_audit", dict(au, agreement=verdict))
        _note(after, f"{METHOD}: MEMBRANE_FOLD_V5 audit attached (T-124): {verdict}; count unchanged")
        held = []
        if verdict == "DIFFERS":
            held.append({"what": "roll count not supported by the MEMBRANE_FOLD_V5 audit (count kept; checker)",
                         "line_rolls": _line_rolls(ln), "v5_by_reading": au.get("v5_by_reading")})
        changes.append(_change("MEMBRANE_AUDIT_V5", "EVIDENCE_ATTACHED", ln, after,
                               drawing_reference=f"architectural plan {loc.get('floor')}: membrane area "
                                                 f"{loc.get('room_id')} (the outline the run folded)",
                               held=held, downstream=[]))
        log["lines"].append({"line_id": ln["line_id"], "floor": loc.get("floor"), "room_id": loc.get("room_id"),
                             "rolls": _line_rolls(ln), "audit": au.get("state"), "agreement": verdict,
                             "v5_by_reading": au.get("v5_by_reading"), "why": au.get("why")})
    return changes, log


# ================================================================================================ integrate / ledger
def integrate(base_lines, v30_changes, v301_changes):
    """-> (V3.0 lines, V3.0.1 lines, identity record). A line both versions change is refused; every line outside
    the V3.0.1 changes is byte-identical to the V3.0 candidate line."""
    as30 = [dict(c, action="REPLACE") if c["action"] == "EVIDENCE_ATTACHED" else c for c in v301_changes]
    l30, _i30 = A30.integrate(base_lines, v30_changes)
    l301, _i301 = A30.integrate(base_lines, list(v30_changes) + as30)
    touched = set()
    for c in v301_changes:
        for x in (c["before"], c["after"]):
            if x is not None:
                touched.add(x["line_id"])
    by30 = {ln["line_id"]: ln for ln in l30}
    outside = [ln for ln in l301 if ln["line_id"] not in touched]
    bad = [ln["line_id"] for ln in outside if ln["line_id"] not in by30 or A30.line_sha(by30[ln["line_id"]])
           != A30.line_sha(ln)]
    lost = [i for i in by30 if i not in {ln["line_id"] for ln in l301} and i not in touched]
    if bad or lost:
        raise ValueError(f"{METHOD}: {len(bad) + len(lost)} line(s) outside the V3.0.1 rows differ from {CANDIDATE}")
    ident = {"v3_0_lines": len(l30), "v3_0_1_lines": len(l301), "v3_0_1_rows": len(v301_changes),
             "outside_rows": len(outside), "outside_rows_identical_to_v3_0": len(outside),
             "outside_rows_sha256": hashlib.sha256("".join(A30.line_sha(x) for x in outside).encode()).hexdigest()}
    return l30, l301, ident


def ledger_rows(v301_changes, v30_lines, released_lines=None):
    """one row per V3.0.1 change: before (released V2.9 when given, base V2.13, candidate V3.0), after, delta,
    drawing reference, owner manual and drawing-derived method, verification evidence, held, downstream."""
    rel = {A30._key(ln): ln for ln in released_lines or ()}
    v30 = {ln["line_id"]: ln for ln in v30_lines}
    rows = []
    for c in v301_changes:
        ref = c["after"] if c["before"] is None else c["before"]
        b13, aft = A30._qty(c["before"]), A30._qty(c["after"])
        b30 = A30._qty(v30.get(ref["line_id"])) if c["before"] is not None else dict(A30._qty(None),
                                                                                    state="NOT_IN_V3_0")
        b29 = None
        if released_lines is not None:
            b29 = A30._qty(rel.get(A30._key(ref))) if A30._key(ref) in rel else dict(A30._qty(None),
                                                                                    state="NOT_IN_RELEASED")
        d = None
        if b30["value"] is not None and aft["value"] is not None:
            d = {"delta": _r(aft["value"] - b30["value"]),
                 "pct": _r(100.0 * (aft["value"] - b30["value"]) / b30["value"], 3) if b30["value"] else None}
        p = PIECES[c["piece"]]
        loc = ref.get("location") or {}
        rows.append({"piece": c["piece"], "action": c["action"], "line_id": ref["line_id"],
                     "item_code": ref["item_code"], "floor": loc.get("floor"), "room_id": loc.get("room_id"),
                     "element_id": loc.get("element_id"), "unit": ref["unit"], "before_released_v2_9": b29,
                     "before_base_v2_13": b13, "before_candidate_v3_0": b30, "after_v3_0": aft, "after_v3_0_1": aft,
                     "change": d, "drawing_reference": c.get("drawing_reference"),
                     "owner_manual_method": p.get("owner_manual_method") or p.get("owner_manual_note"),
                     "drawing_method": p["drawing_method"], "owner_rules": p["owner_rules"],
                     "verification": {k: p[k] for k in ("task", "merge_commit", "verifier_run", "module", "policy")},
                     "held": c.get("held") or [], "downstream": c.get("downstream") or [], "rollback": ROLLBACK,
                     "after_line_id": c["after"]["line_id"],
                     "line_ids": sorted({x["line_id"] for x in (c["before"], c["after"]) if x is not None})})
    return rows


def family_totals(rows, item_prefix):
    """before / after sums of one line family over the rows (released values and held ranges apart, never one)."""
    t = {"lines": 0, "before_v3_0": 0.0, "after_released": 0.0, "after_held_low": 0.0, "after_held_high": 0.0,
         "after_not_present_or_superseded": 0}
    for r in rows:
        if not str(r["item_code"]).startswith(item_prefix):
            continue
        t["lines"] += 1
        t["before_v3_0"] += r["before_candidate_v3_0"]["value"] or 0.0
        a = r["after_v3_0_1"]
        if a["value"] is not None:
            t["after_released"] += a["value"]
        elif a["low"] is not None:
            t["after_held_low"] += a["low"]
            t["after_held_high"] += a["high"]
        else:
            t["after_not_present_or_superseded"] += 1
    return {k: (_r(v) if isinstance(v, float) else v) for k, v in t.items()}


def write(out, base_lines, v30_changes, v301_changes, logs, inputs, released_lines=None, history=None):
    """the V3_0_1_* files beside the V3_0_* files. -> (file names, identity, ledger)."""
    from pathlib import Path
    from engine.source import boq_line as BL
    out = Path(out)
    l30, l301, ident = integrate(base_lines, v30_changes, v301_changes)
    rows = ledger_rows(v301_changes, l30, released_lines)
    v30_led = A30.ledger(list(v30_changes) + [r for r in A30.membrane_rows(base_lines)
                                             if r["before"]["line_id"] not in {c["before"]["line_id"] for c in
                                                                               v301_changes if c["before"]}],
                         released_lines)
    for r in v30_led["rows"]:
        r["before_candidate_v3_0"] = r["after_v3_0"]
        r["after_v3_0_1"] = r["after_v3_0"]
        r["version"] = CANDIDATE
    for r in rows:
        r["version"] = METHOD
    led = {"schema": LEDGER_SCHEMA, "method": METHOD, "extends": CANDIDATE, "base": A30.BASE_METHOD,
           "released": A30.RELEASED_METHOD, "released_default": False, "rows": v30_led["rows"] + rows,
           "waiting_pieces": WAITING, "v3_0_waiting_pieces": A30.WAITING}
    if released_lines is not None:
        rel = A30._by_id(released_lines)
        hist = {v: (A30._by_id(history[v]) if history and history.get(v) is not None else None) for v in A30.HISTORY}
        chain = {A30.CHAIN[0]: rel, A30.BASE_METHOD: A30._by_id(base_lines), CANDIDATE: A30._by_id(l30), **hist}
        by301 = A30._by_id(l301)
        for r in led["rows"]:
            r["since_v2_9"] = A30.version_steps(r["line_id"], chain)
            if r["version"] == METHOD:
                a, b = by301.get(r["after_line_id"]), chain[CANDIDATE].get(r["line_id"])
                r["since_v2_9"].append({"version": METHOD, "change": "ADDED" if b is None else "CHANGED",
                                        "fields": A30._fields(b, a) if b is not None else None})
        documented = {i for r in led["rows"] for i in [r["line_id"]] + (r.get("line_ids") or [])}
        led["rows"] += A30.inherited_rows(l301, base_lines, released_lines, documented, history)
        ident = dict(ident, vs_released_v2_9=A30.released_identity(l301, released_lines, led),
                     history_given=sorted(v for v in A30.HISTORY if history and history.get(v) is not None))
    totals = {"columns_m3": family_totals(rows, "STR.CONC.COLUMN"),
              "blinding_m3": family_totals([r for r in rows if "BLINDING" in str(r.get("element_id") or "")],
                                           "STR.CONC"),
              "membrane_rolls_audit": {}}
    for lg in logs:
        if lg.get("piece") == "MEMBRANE_AUDIT_V5":
            for x in lg["lines"]:
                totals["membrane_rolls_audit"][x["agreement"]] = totals["membrane_rolls_audit"].get(
                    x["agreement"], 0) + 1
    down = [dict(d, from_line=r["line_id"], piece=r["piece"]) for r in rows for d in r["downstream"]]
    run = {"method": METHOD, "policy": POLICY_ID, "extends": CANDIDATE, "base_method": A30.BASE_METHOD,
           "released_method": A30.RELEASED_METHOD, "released_default": False, "rollback": ROLLBACK,
           "identity": ident, "pieces": PIECES, "v3_0_pieces": A30.PIECES, "piece_logs": logs, "inputs": inputs,
           "totals": totals, "waiting_pieces": WAITING}
    files = {"V3_0_1_BOQ_LINES.json": BL.dumps(l301),
             "V3_0_1_BOQ_LINES.csv": A30._lines_csv(l301),
             "V3_0_1_INTEGRATION_LEDGER.json": A30._j(led),
             "V3_0_1_INTEGRATION_LEDGER.csv": A30.ledger_csv(led),
             "V3_0_1_DOWNSTREAM.json": A30._j({"method": METHOD, "rows": down}),
             "V3_0_1_RUN.json": A30._j(run)}
    for name, text in files.items():
        (out / name).write_text(text, encoding="utf-8")
    return sorted(files), ident, led
