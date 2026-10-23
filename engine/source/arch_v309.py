"""ARCH_TAKEOFF_V3.0.9 (T-211, package V3.0.9a): the SAME opt-in BOQ candidate as ARCH_TAKEOFF_V3.0 .. V3.0.8
(engine.source.arch_v30, arch_v301 .. arch_v308), extended with checker-merged room-by-room internal wall finishes:
plaster and paint m2 per room face, the owner manual method and the drawing-derived method side by side on every line.
Not a new method family and not the released default (owner management decision 2026-10-20 sections 2 and 5); rollback
is running the released ARCH_TAKEOFF_V2.9.

How it is built (tools/urban_boq_m9.py `arch --method ARCH_TAKEOFF_V3.0.9`):
  1. the run is the V3.0.8 candidate exactly: its V3_0_* .. V3_0_8_* files are written unchanged (arch_v30 .. arch_v308
     are not edited);
  2. ROOM WALL-FINISH RECORDS (piece WALL_FINISH, project inputs URBAN_V309_INPUTS_V1): one record per room face and
     finish (item codes in the piece, unit m2). The piece names its checker-merged sources (file sha256, task, merge
     commit, checker run) and its scope: the floors and the candidate ROOM ids (location.room_id) whose lines of those
     item codes are the same physical wall faces. Every candidate line of the item codes in a scope room is accounted
     for before a record is added (T-179 lesson, ERS s.2.1):
       supersede_lines  the same room face carried by another line: it becomes NOT_APPLICABLE_WITH_EVIDENCE (never
                        deleted, never summed). The figure it carries is stated and must equal the line (a held line
                        without a figure is stated as NO_FIGURE);
       other_elements   another physical element in the room (kept byte-identical);
     an unaccounted scope line, or a named line the candidate does not have, refuses the run;
  3. one line per record, the quantity is the OWNER MANUAL METHOD (owner heights, the owner-controlled method of
     record, ERS s.2.2), the DRAWING-DERIVED METHOD carried beside it in the line inputs, never merged:
       RELEASED     -> PROVISIONAL (the owner heights are an owner-approved fallback, so never a confirmed number),
                       evidence status VERIFIED only where the record names the checker run that re-measured that room,
                       else ASSUMED - OWNER-APPROVED; the assumption and its source stay on the line either way
                       (WORKFLOW_CONTROLS s.4 / s.5);
       BOUNDED      -> BOUNDED_EXPOSURE (HELD): a held opening makes the net a range (lower = its full band deducted,
                       upper = no deduction), never a number;
       UNQUANTIFIED -> BLOCKED_RFI (HELD / UNKNOWN), its figures only as information; missing is never 0.
     The net is recomputed from the record's gross and deductions (known m2 and held ranges) and refused when it
     disagrees with the stated value or range by more than NET_TOL_M2 (the hand packages print 2 decimals);
  4. GUARD RE-CHECK (piece DEFAULT_GUARD): the merged guard runs again over the V3.0.9 lines with the guard inputs of
     V3.0.7 (arch_v307.guard_changes);
  5. the V3_0_9_* files are written beside them: every line outside the V3.0.9 rows is byte-identical to the V3.0.8
     line (asserted on every run), and V3_0_9_DIFF.csv lists every line against V3.0.8 and against the released V2.9.

Rules: owner decision 2026-10-20 sections 2 and 5; WORKFLOW_CONTROLS 2026-10-21 sections 1, 4, 5;
ENGINEERING_REASONING_STANDARD 2026-10-22 sections 2.2, 3 and 7; Q-43 / Q-48 A (wall height = floor to floor - beam -
0.15 decor ceiling - floor finish, one line for plaster, paint and tile); Q-55 C (door head 2.20 only where the
drawings are silent, ASSUMED); Q-73 (full openings deducted, only from what is physically built); UP-FIN-PAINT-001 (no
paint over full-height tile: one finish per face); UP-QTY-STATUS-001 (held is a range or blocked, never 0).
Nothing here names a project, a sheet, a layer, a room or a coordinate; every number comes from the run or the inputs.
"""

from __future__ import annotations

import hashlib

from engine.source import arch_v30 as A30
from engine.source import arch_v302 as A302
from engine.source import arch_v304 as A304
from engine.source import arch_v305 as A305
from engine.source import arch_v307 as A307
from engine.source import arch_v308 as A308

DEFAULT_GUARD_CLASS = "GUARD_HOST"      # T-212: a candidate method; it reaches the guard through arch_v307
METHOD = "ARCH_TAKEOFF_V3.0.9"
EXTENDS = A308.METHOD
CANDIDATE = A30.METHOD                  # the candidate family this version extends (never a new method family)
POLICY_ID = "URBAN_BOQ_T211_ARCH_V3_0_9"
LEDGER_SCHEMA = "URBAN_V309_INTEGRATION_LEDGER_V1"
INPUTS_SCHEMA = "URBAN_V309_INPUTS_V1"
ROLLBACK = A30.ROLLBACK
STATES = ("RELEASED", "BOUNDED", "UNQUANTIFIED")
HELD_STATUS = ("HELD", "UNKNOWN")
RELEASED_STATUS = ("VERIFIED", "ASSUMED - OWNER-APPROVED", "DRAWING-CONFIRMED")
LIVE_EVIDENCE = A307.LIVE_EVIDENCE
NO_FIGURE = "NO_FIGURE"                 # the stated figure of a superseded held line that carries none
NET_TOL_M2 = 0.006                      # 2-decimal hand packages: |recomputed - stated| <= 0.006 m2
InputsError = A307.InputsError

PIECES = {
    "WALL_FINISH": {
        "module": "engine/source/arch_v309.py (checker-merged room wall-finish records)",
        "policy": "WALL_FINISH_ROOM_RECORDS_V1", "rule_id": "Q-43", "rule_version": "owner-2026-10-19",
        "owner_rules": ["Q-43 / Q-48 A (owner 2026-10-19: wall height = floor to floor - 0.60 beam - 0.15 decor ceiling "
                        "- 0.10 floor finish, one line for plaster, paint and wall tile)",
                        "Q-55 C (door head 2.20 m only where the drawings are silent: ASSUMED - OWNER-APPROVED)",
                        "Q-73 (owner 2026-10-22, final: full openings deducted, only from what is physically built)",
                        "UP-FIN-PAINT-001 (one finish per face: no paint over full-height wall tile)",
                        "UP-QTY-STATUS-001 (a held opening makes the net a range, never 0)"],
        "owner_manual_method": "manual QS take-off of a room's wall face: face length (room contour less open sides) "
                               "x the owner wall height of the floor, less every opening by its own area (width x "
                               "height inside the wall height; a door head 2.20 where none is printed); one figure "
                               "for plaster and paint",
        "drawing_method": "the room contour walked on the drawn faces (walls, columns, glazing bands); height from the "
                          "drawn levels: floor to floor - slab - floor build-up b (0 .. 0.10, not printed) - decor "
                          "0.15 (paint), plaster may run to the soffit; a face under a finished roof mark is HELD on "
                          "the roof datum; openings by the same physical scope; shown beside, never merged"},
    "DEFAULT_GUARD": A307.PIECES["DEFAULT_GUARD"],
}
WAITING = dict(A308.WAITING)
WAITING.update({
    "WET_WALL_TILE_AND_KITCHEN_FLOOR": "V3.0.9b (same T-211 row): wet-room wall tiles room by room (T-209) and the GF "
                                       "kitchen floor item to WET_TILE (T-218); the wet rooms' wall-finish lines are "
                                       "NOT changed here",
    "OPENING_LEDGER_FIX": "T-238 (merged opening ledgers read an arched opening to its surround band): until it merges "
                          "the two arched windows are deducted here as a HELD range (true outline .. band rectangle)",
    "FACE_CROSSWALK": "T-237 (room face -> block wall, heights and opening ids across trades): the faces it corrects "
                      "enter as a change-log row in the next V3.0.x slot",
    "CORNERS_AND_EXTERNAL_FACES": "T-172 corners / parapet arrises (m.l, external) belong with the external plaster "
                                  "package; never converted to m2 and not wired here",
})


def _r(x, n=6):
    return None if x is None else round(float(x), n)


_num = A307._num


# ================================================================================================ project inputs
def _carried(ln):
    """the figure a line carries: its live quantity, a bounded line's range [low, high], or NO_FIGURE for a held line
    that carries none."""
    if ln["evidence_state"] in LIVE_EVIDENCE and ln.get("measured_net") is not None:
        return A30._qty(ln)["value"]
    if ln["evidence_state"] == "BOUNDED_EXPOSURE" and ln.get("bounded_range"):
        q = A30._qty(ln)
        return [q["low"], q["high"]]
    return NO_FIGURE


def _same(carried, stated):
    if carried == NO_FIGURE or stated == NO_FIGURE:
        return carried == stated
    return A308._same(carried, stated)


def net_of(method):
    """(low, high) net m2 of one method record {gross, deductions: [{opening, m2} | {opening, range: [lo, hi]}]}: lower
    = gross - known - every held opening at its largest, upper = gross - known - every held opening at its smallest."""
    g = method.get("gross")
    if not _num(g):
        return None
    lo = hi = float(g)
    for d in method.get("deductions") or ():
        if _num(d.get("m2")):
            lo -= d["m2"]
            hi -= d["m2"]
        else:
            rg = d.get("range")
            if not (isinstance(rg, (list, tuple)) and len(rg) == 2 and all(_num(x) for x in rg) and 0 <= rg[0] <= rg[1]):
                raise InputsError(f"deduction {d.get('opening')!r}: a known m2 or a range [low, high], 0 <= low <= high")
            lo -= rg[1]
            hi -= rg[0]
    return lo, hi


def _check_record(p, r, sc, codes):
    key = (r.get("room"), r.get("item_code"))
    st = r.get("state")
    if st not in STATES:
        raise InputsError(f"piece {p} {key}: state {st!r} not one of {STATES}")
    if r.get("item_code") not in codes:
        raise InputsError(f"piece {p} {key}: item code outside the piece {codes}")
    if r.get("floor") not in sc["floors"]:
        raise InputsError(f"piece {p} {key}: floor {r.get('floor')!r} outside the scope {sc['floors']}")
    if not r.get("route_rooms") or not set(r["route_rooms"]) <= set(sc["rooms"]):
        raise InputsError(f"piece {p} {key}: route_rooms must be scope rooms (the candidate room(s) of this face)")
    ge = r.get("guard_element") or {}
    if not ge.get("element_id") or not ge.get("part"):
        raise InputsError(f"piece {p} {key}: guard_element (element_id and part) is required")
    if not isinstance(r.get("drawing_method"), dict):
        raise InputsError(f"piece {p} {key}: the drawing-derived method is carried beside the owner method "
                          "(drawing_method, ERS s.2.2)")
    om = r.get("owner_method")
    if st == "RELEASED":
        if not (_num(r.get("value")) and r["value"] > 0):
            raise InputsError(f"piece {p} {key}: a RELEASED record carries a value > 0 (missing is never 0)")
        if r.get("evidence_status") not in RELEASED_STATUS:
            raise InputsError(f"piece {p} {key}: a RELEASED record is one of {RELEASED_STATUS}")
        if r["evidence_status"] == "VERIFIED" and not r.get("verified_by"):
            raise InputsError(f"piece {p} {key}: VERIFIED names the checker run that re-measured the room")
        if not r.get("assumption"):
            raise InputsError(f"piece {p} {key}: the owner-approved height assumption and its source stay on the line "
                              "(WORKFLOW_CONTROLS s.4)")
        n = net_of(om or {})
        if n is None or abs(n[1] - n[0]) > 1e-9:
            raise InputsError(f"piece {p} {key}: a RELEASED record has every deduction known (a held opening is a "
                              "BOUNDED record)")
        if abs(n[0] - r["value"]) > NET_TOL_M2:
            raise InputsError(f"piece {p} {key}: net recomputed {round(n[0], 4)} != stated {r['value']}")
    else:
        if not r.get("reasons") or r.get("evidence_status") not in HELD_STATUS:
            raise InputsError(f"piece {p} {key}: a {st} record names why and its status HELD / UNKNOWN")
    if st == "BOUNDED":
        rg = r.get("range")
        if not (isinstance(rg, (list, tuple)) and len(rg) == 2 and all(_num(x) for x in rg)
                and 0 <= rg[0] <= rg[1] and rg[1] > 0):
            raise InputsError(f"piece {p} {key}: a BOUNDED record carries a range [low, high], 0 <= low <= high, "
                              "high > 0")
        if om is not None and om.get("gross") is not None:
            n = net_of(om)
            if abs(n[0] - rg[0]) > NET_TOL_M2 or abs(n[1] - rg[1]) > NET_TOL_M2:
                raise InputsError(f"piece {p} {key}: net recomputed {round(n[0], 4)} .. {round(n[1], 4)} != stated "
                                  f"{rg[0]} .. {rg[1]}")


def load_inputs(doc, project_id=None):
    """URBAN_V309_INPUTS_V1 or None:
        {"schema", "project",
         "pieces": [{"piece": "WALL_FINISH", "item_codes": [...], "unit": "m2", "source": {...}, "sources": [...],
                     "scope": {"floors", "rooms" (candidate room ids),
                               "supersede_lines": [{element_id, floor, item_code, why, carried (value, [low, high]
                                                    or NO_FIGURE)}],
                               "other_elements": [{element_id, floor, item_code, why}]},
                     "records": [{room, item_code, floor, route_rooms, state, value | range, evidence_status,
                                  verified_by, assumption, reasons, owner_method {height, face_m, gross, deductions},
                                  drawing_method {...}, guard_element {element_id, part}, info, downstream}],
                     "declared_totals": {item_code: {released, bounded: [low, high], unquantified}}}],
         "guard": as URBAN_V307_INPUTS_V1 "guard"}"""
    if doc is None:
        return None
    if doc.get("schema") != INPUTS_SCHEMA:
        raise InputsError(f"project inputs: schema must be {INPUTS_SCHEMA}")
    if project_id and doc.get("project") not in (None, project_id):
        raise InputsError(f"project inputs are for {doc.get('project')!r}, the run is {project_id!r}")
    seen = set()
    for pc in doc.get("pieces") or ():
        p = pc.get("piece")
        if p != "WALL_FINISH" or p in seen:
            raise InputsError(f"piece {p!r}: WALL_FINISH, once")
        seen.add(p)
        codes = pc.get("item_codes")
        if pc.get("unit") != "m2" or not (isinstance(codes, list) and codes and all(codes)):
            raise InputsError(f"piece {p}: unit m2 and item_codes are required (an m.l item is never an m2 line)")
        A307._source(pc.get("source"), f"piece {p}")
        for s in pc.get("sources") or ():
            A307._source(s, f"piece {p} (supporting source)")
        sc = pc.get("scope") or {}
        if not sc.get("floors") or not sc.get("rooms"):
            raise InputsError(f"piece {p}: scope needs floors and rooms")
        for k in ("supersede_lines", "other_elements"):
            for x in sc.get(k) or ():
                if not x.get("element_id") or not x.get("floor") or not x.get("why") or x.get("item_code") not in codes:
                    raise InputsError(f"piece {p}: every scope.{k} entry has element_id, floor, item_code and why")
                if k == "supersede_lines" and x.get("carried") is None:
                    raise InputsError(f"piece {p}: scope.{k} {x['element_id']} states the figure it carries "
                                      f"(or {NO_FIGURE})")
        ids = set()
        for r in pc.get("records") or ():
            key = (r.get("room"), r.get("item_code"))
            if not r.get("room") or key in ids:
                raise InputsError(f"piece {p}: every record has a unique room / item code: {key}")
            ids.add(key)
            _check_record(p, r, sc, codes)
        if not ids:
            raise InputsError(f"piece {p}: no records")
        covered = {rr for r in pc["records"] for rr in r["route_rooms"]}
        if set(sc["rooms"]) - covered:
            raise InputsError(f"piece {p}: scope room(s) {sorted(set(sc['rooms']) - covered)} carry no record: a "
                              "superseded room face with no replacement would be a silent omission")
    g = doc.get("guard")
    if g is not None:
        A307.load_inputs({"schema": A307.INPUTS_SCHEMA, "project": doc.get("project"), "guard": g}, project_id)
    return doc


# ================================================================================================ room records
def _scope_lines(pc, lines):
    sc = pc["scope"]
    rooms, codes = set(sc["rooms"]), set(pc["item_codes"])
    return [ln for ln in lines if ln["item_code"] in codes and ln["unit"] == pc["unit"]
            and (ln.get("location") or {}).get("floor") in sc["floors"]
            and (ln.get("location") or {}).get("room_id") in rooms]


def record_line(pid, rev, docs, pc, r):
    """one BOQ line for one room record. -> (line, evidence status)"""
    from engine.source import boq_line as BL
    p, src = PIECES["WALL_FINISH"], pc["source"]
    st = r["state"]
    reasons = list(r.get("reasons") or ())
    ev = {"RELEASED": "PROVISIONAL", "BOUNDED": "BOUNDED_EXPOSURE", "UNQUANTIFIED": "BLOCKED_RFI"}[st]
    fin = r["item_code"].split(".")[-1]
    eid = f"HL:WALL_FINISH:{A305._slug(r['room'])}:{A305._slug(fin)}"
    rfi = None if st == "RELEASED" else {"question": "; ".join(reasons)[:900], "unlocks": eid}
    br = None
    if ev == "BOUNDED_EXPOSURE":
        br = {"low": _r(r["range"][0]), "high": _r(r["range"][1]),
              "basis": (r.get("range_basis") or "; ".join(reasons))[:300]}
    om = r.get("owner_method") or {}
    n = net_of(om) if om.get("gross") is not None else None
    ln = BL.make_line(project_id=pid, revision_set_sha256=rev, item_code=r["item_code"], unit="m2",
                      evidence_state=ev, measured_net=_r(r["value"]) if st == "RELEASED" else None,
                      bounded_range=br, element_id=eid, floor=r["floor"], room_id=r["route_rooms"][0],
                      physical_element=f"wall face {fin.lower()}", subtrade=f"room wall face ({fin.lower()})",
                      gross=_r(om.get("gross")) if st == "RELEASED" else None,
                      formula=r.get("formula") or ("held: " + "; ".join(reasons))[:400],
                      inputs=dict({"policy": p["policy"], "source": src["file"], "source_sha256": src["sha256"],
                                   "room": r["room"], "route_rooms": list(r["route_rooms"]),
                                   "record_state": st, "evidence_status": r.get("evidence_status"),
                                   "assumption": r.get("assumption"), "verified_by": r.get("verified_by"),
                                   "owner_manual_method": om, "owner_net_recomputed": None if n is None else
                                   [_r(n[0], 4), _r(n[1], 4)], "drawing_derived_method": r["drawing_method"],
                                   "reasons": reasons, "guard_element": r["guard_element"]}, **(r.get("info") or {})),
                      documents=docs, geometry_source="CAD_VECTOR",
                      geometry_confidence="TOLERANCE_CERTIFIED" if st == "RELEASED" else "INFERRED_CANDIDATE",
                      rule_id=p["rule_id"], rule_version=p["rule_version"], material_state="BY_SPEC", rfi=rfi,
                      notes=f"{METHOD}: room wall face by checker-merged record ({src['task']}, MERGED "
                            f"{src['merge_commit']}); owner manual method of record, drawing-derived beside")
    evs = r["evidence_status"]
    return ln, evs


def record_changes(inputs, lines, earlier_changed=()):
    """the WALL_FINISH piece on the V3.0.8 lines. -> (changes, logs)"""
    if not inputs or not inputs.get("pieces"):
        return [], [{"piece": "WALL_FINISH", "state": "NO_PROJECT_INPUT"}]
    pid, rev, docs = A302._proj(lines)
    have = {ln["line_id"] for ln in lines}
    earlier = set(earlier_changed)
    changes, logs, touched = [], [], set()
    for pc in inputs["pieces"]:
        sc, src = pc["scope"], pc["source"]
        verif = {"task": src["task"], "merge_commit": src["merge_commit"], "verifier_run": src["checker_run"],
                 "source": src["file"], "source_sha256": src["sha256"],
                 "supporting": [{k: s.get(k) for k in ("task", "merge_commit", "checker_run", "file")}
                                for s in pc.get("sources") or ()]}
        key = lambda x: (x["element_id"], x["floor"], x["item_code"])  # noqa: E731
        named = {key(x): x for x in sc.get("supersede_lines") or ()}
        other = {key(x): x for x in sc.get("other_elements") or ()}
        if set(named) & set(other):
            raise InputsError("piece WALL_FINISH: a scope line is accounted for twice (supersede / other)")
        log = {"piece": "WALL_FINISH", "state": "RUN", "source": src, "sources": pc.get("sources") or [],
               "item_codes": pc["item_codes"], "unit": pc["unit"],
               "scope": {"floors": sc["floors"], "rooms": sc["rooms"]}, "scope_lines": [], "records": [],
               "evidence_status": {}}
        seen = set()
        sup = {c: {"value": 0.0, "low": 0.0, "high": 0.0, "no_figure": 0} for c in pc["item_codes"]}
        for ln in _scope_lines(pc, lines):
            loc = ln.get("location") or {}
            k = (loc.get("element_id"), loc.get("floor"), ln["item_code"])
            entry = {"line_id": ln["line_id"], "element_id": k[0], "floor": k[1], "item_code": k[2],
                     "room_id": loc.get("room_id"), "evidence_state": ln["evidence_state"],
                     "quantity": A302._q(A30._qty(ln)), "earlier_change": ln["line_id"] in earlier}
            if k in other:
                seen.add(k)
                log["scope_lines"].append(dict(entry, accounted="OTHER_ELEMENT", why=other[k]["why"]))
                continue
            if k not in named:
                raise InputsError(f"piece WALL_FINISH: candidate line {ln['line_id']} ({k[0]} {k[1]} {k[2]}, "
                                  f"{A302._q(A30._qty(ln))}) is inside the scope and is neither superseded by name nor "
                                  "declared another element: an integration that only adds is refused")
            if ln["line_id"] in touched:
                raise ValueError(f"{METHOD}: line {ln['line_id']} superseded twice")
            x = named[k]
            A308._check_replaceable(ln, earlier, x)
            cq = _carried(ln)
            if not _same(cq, x["carried"]):
                raise InputsError(f"piece WALL_FINISH: line {k[0]} carries {cq}, the inputs state {x['carried']}: the "
                                  "superseded figure must be the one the line carries")
            seen.add(k)
            s = sup[ln["item_code"]]
            if cq == NO_FIGURE:
                s["no_figure"] += 1
            elif isinstance(cq, (list, tuple)):
                s["low"] += float(cq[0])
                s["high"] += float(cq[1])
            else:
                s["value"] += float(cq)
            note = (f"{METHOD}: SUPERSEDED - {A302._q(A30._qty(ln))} {ln['unit']} (V3.0.8 state "
                    f"{ln['evidence_state']}) replaced by the checker-merged room wall-finish records of {src['task']} "
                    f"(MERGED {src['merge_commit']}): {x['why']}")
            codes = ["SUPERSEDED_BY_RECORD"] + (["EARLIER_CHANGE"] if ln["line_id"] in earlier else [])
            changes.append(A307._retire(ln, x["why"], note, verif, "WALL_FINISH", codes,
                                        x.get("drawing_reference") or src["file"]))
            touched.add(ln["line_id"])
            log["scope_lines"].append(dict(entry, accounted="SUPERSEDED", why=x["why"], carried=cq))
        missing = (set(named) | set(other)) - seen
        if missing:
            raise InputsError(f"piece WALL_FINISH: scope names line(s) the candidate does not have: {sorted(missing)}")
        tot = {c: {"released": 0.0, "bounded": [0.0, 0.0], "unquantified": 0} for c in pc["item_codes"]}
        for r in pc["records"]:
            ln, evs = record_line(pid, rev, docs, pc, r)
            if ln["line_id"] in have:
                raise ValueError(f"{METHOD}: record {r['room']} {r['item_code']} repeats a candidate line id")
            have.add(ln["line_id"])
            t = tot[r["item_code"]]
            held = []
            if ln["evidence_state"] == "PROVISIONAL":
                t["released"] += ln["measured_net"]
            else:
                rg = ln.get("bounded_range")
                if rg:
                    t["bounded"][0] += rg["low"]
                    t["bounded"][1] += rg["high"]
                else:
                    t["unquantified"] += 1
                held = [{"what": f"{r['item_code']} {r['room']}", "why": ln["rfi"]["question"],
                         "range": [rg["low"], rg["high"]] if rg else None}]
            changes.append(A305._change("WALL_FINISH", "ADD", None, ln, drawing_reference=src["file"], held=held,
                                        downstream=list(r.get("downstream") or ()),
                                        verification=dict(verif, record_verified_by=r.get("verified_by")),
                                        evidence_status=evs, guard_element=r["guard_element"]))
            log["records"].append({"room": r["room"], "item_code": r["item_code"], "line_id": ln["line_id"],
                                   "floor": r["floor"], "route_rooms": r["route_rooms"],
                                   "evidence_state": ln["evidence_state"], "evidence_status": evs,
                                   "quantity": ln["measured_net"], "range": ln.get("bounded_range")})
            log["evidence_status"][evs] = log["evidence_status"].get(evs, 0) + 1
        log["totals"] = {c: {"released_added": _r(t["released"], 4),
                             "bounded_added": [_r(t["bounded"][0], 4), _r(t["bounded"][1], 4)],
                             "unquantified_added": t["unquantified"],
                             "superseded": {"value": _r(sup[c]["value"], 4),
                                            "bounded": [_r(sup[c]["low"], 4), _r(sup[c]["high"], 4)],
                                            "no_figure_lines": sup[c]["no_figure"]}} for c, t in tot.items()}
        for c, v in (pc.get("declared_totals") or {}).items():
            got = log["totals"].get(c) or {}
            ok = (abs((got.get("released_added") or 0) - v.get("released", 0)) <= 0.006
                  and all(abs(a - b) <= 0.006 for a, b in zip(got.get("bounded_added") or (0, 0),
                                                               v.get("bounded", (0, 0))))
                  and got.get("unquantified_added") == v.get("unquantified", 0))
            if not ok:
                raise ValueError(f"{METHOD}: {c} totals {got} != the declared {v}")
        log["declared_totals"] = pc.get("declared_totals") or {}
        logs.append(log)
    return changes, logs


# ================================================================================================ integrate / write
def changes_for(inputs, l308, earlier_changed=()):
    """the room records, then the guard re-check over the result. -> (changes, logs)"""
    ch_r, logs = record_changes(inputs, l308, earlier_changed)
    rep = {c["before"]["line_id"]: c["after"] for c in ch_r if c["action"] == "REPLACE"}
    view = [rep.get(ln["line_id"], ln) for ln in l308]
    ch_g, log_g = A307.guard_changes(inputs, view, [c for c in ch_r if c["action"] == "ADD"], set(rep))
    for c in ch_g:   # a guard hold written by the V3.0.7 code is this version's row
        A305._note(c["after"], f"(re-check run by {METHOD})")
    return ch_r + ch_g, logs + [log_g]


def integrate(l308, v309_changes):
    """-> (V3.0.9 lines, identity). Every line outside the V3.0.9 rows is byte-identical to the V3.0.8 line."""
    from engine.source import boq_line as BL
    sid = {ln["line_id"] for ln in l308}
    rep, adds = {}, []
    for c in v309_changes:
        if c["action"] == "REPLACE":
            lid = c["before"]["line_id"]
            if lid in rep:
                raise ValueError(f"{METHOD}: line {lid} changed twice")
            if lid not in sid:
                raise ValueError(f"{METHOD}: a change names a line the V3.0.8 run does not have")
            if c["after"]["line_id"] != lid:
                raise ValueError(f"{METHOD}: a changed line keeps its line id")
            rep[lid] = c["after"]
        elif c["action"] == "ADD":
            if c["after"]["line_id"] in sid:
                raise ValueError(f"{METHOD}: an added line repeats a V3.0.8 line id")
            adds.append(c["after"])
        else:
            raise ValueError(f"{METHOD}: action {c['action']}")
    out = [rep.get(ln["line_id"], ln) for ln in l308] + adds
    if len({ln["line_id"] for ln in out}) != len(out):
        raise ValueError(f"{METHOD}: a BOQ line id appears twice")
    for ln in out:
        BL.validate(ln)
    by308 = {ln["line_id"]: ln for ln in l308}
    touched = set(rep) | {a["line_id"] for a in adds}
    outside = [ln for ln in out if ln["line_id"] not in touched]
    bad = [ln["line_id"] for ln in outside if A30.line_sha(by308[ln["line_id"]]) != A30.line_sha(ln)]
    if bad or len(outside) + len(rep) != len(l308):
        raise ValueError(f"{METHOD}: {len(bad)} line(s) outside the V3.0.9 rows differ from {EXTENDS}")
    ident = {"v3_0_8_lines": len(l308), "v3_0_9_lines": len(out), "v3_0_9_rows": len(v309_changes),
             "replaced": len(rep), "added": len(adds), "outside_rows": len(outside),
             "outside_rows_identical_to_v3_0_8": len(outside),
             "outside_rows_sha256": hashlib.sha256("".join(A30.line_sha(x) for x in outside).encode()).hexdigest()}
    return out, ident


def ledger_rows(changes, released_lines=None):
    rel = {A30._key(ln): ln for ln in released_lines or ()}
    rows = []
    for c in changes:
        ref = c["after"] if c["before"] is None else c["before"]
        b308 = A30._qty(c["before"]) if c["before"] is not None else dict(A30._qty(None), state="NOT_IN_V3_0_8")
        b29 = None
        if released_lines is not None:
            b29 = A30._qty(rel[A30._key(ref)]) if A30._key(ref) in rel else dict(A30._qty(None),
                                                                                 state="NOT_IN_RELEASED")
        p = PIECES[c["piece"]]
        loc = ref.get("location") or {}
        rows.append({"version": METHOD, "piece": c["piece"], "action": c["action"], "line_id": ref["line_id"],
                     "item_code": ref["item_code"], "floor": loc.get("floor"), "room_id": loc.get("room_id"),
                     "element_id": c["after"]["location"].get("element_id"), "unit": c["after"]["unit"],
                     "before_released_v2_9": b29, "before_v3_0_8": b308, "after_v3_0_9": A30._qty(c["after"]),
                     "evidence_status": c.get("evidence_status") or "HELD", "release_status": "NOT RELEASED",
                     "codes": c.get("codes") or [], "citations": c.get("citations") or [],
                     "drawing_reference": c.get("drawing_reference"),
                     "owner_manual_method": p["owner_manual_method"], "drawing_method": p["drawing_method"],
                     "owner_rules": p["owner_rules"],
                     "verification": dict(c.get("verification") or {}, module=p["module"], policy=p["policy"]),
                     "held": c.get("held") or [], "downstream": c.get("downstream") or [], "rollback": ROLLBACK})
    return rows


LEDGER_CSV = ("version", "piece", "action", "line_id", "item_code", "floor", "room_id", "element_id", "unit", "v2_9",
              "v3_0_8", "v3_0_9", "evidence_status", "release_status", "codes", "drawing_reference", "verification",
              "held")


def ledger_csv(rows):
    return A305._csv([{"version": r["version"], "piece": r["piece"], "action": r["action"], "line_id": r["line_id"],
                       "item_code": r["item_code"], "floor": r["floor"], "room_id": r["room_id"],
                       "element_id": r["element_id"], "unit": r["unit"], "v2_9": A302._q(r["before_released_v2_9"]),
                       "v3_0_8": A302._q(r["before_v3_0_8"]), "v3_0_9": A302._q(r["after_v3_0_9"]),
                       "evidence_status": r["evidence_status"], "release_status": r["release_status"],
                       "codes": " ".join(r["codes"]), "drawing_reference": str(r["drawing_reference"])[:300],
                       "verification": f"{r['verification'].get('task')} {r['verification'].get('merge_commit')}"
                                       + (f" / {r['verification']['record_verified_by']}"
                                          if r["verification"].get("record_verified_by") else ""),
                       "held": "; ".join(str(h.get("why") or h.get("what")) for h in r["held"])[:600]}
                      for r in rows], LEDGER_CSV)


DIFF_CSV = ("line_id", "item_code", "floor", "element_id", "unit", "vs_v3_0_8", "vs_released_v2_9", "v2_9", "v3_0_8",
            "v3_0_9")


def diff_rows(l308, l309, released_lines=None):
    b308 = {ln["line_id"]: ln for ln in l308}
    rel = {A30._key(ln): ln for ln in released_lines or ()}
    out = []
    for ln in l309:
        o = b308.get(ln["line_id"])
        vs = "ADDED" if o is None else ("SAME" if A30.line_sha(o) == A30.line_sha(ln) else "CHANGED")
        r = rel.get(A30._key(ln)) if released_lines is not None else None
        vs29 = None if released_lines is None else ("NOT_IN_RELEASED" if r is None else
                                                    ("SAME_QUANTITY" if A30._qty(r) == A30._qty(ln) else
                                                     "QUANTITY_DIFFERS"))
        out.append({"line_id": ln["line_id"], "item_code": ln["item_code"], "floor": ln["location"].get("floor"),
                    "element_id": ln["location"].get("element_id"), "unit": ln["unit"], "vs_v3_0_8": vs,
                    "vs_released_v2_9": vs29, "v2_9": A302._q(A30._qty(r)) if r else "",
                    "v3_0_8": A302._q(A30._qty(o)) if o else "", "v3_0_9": A302._q(A30._qty(ln))})
    return out


def write(out, l308, v309_changes, logs, inputs, released_lines=None):
    """the V3_0_9_* files beside the V3_0_8_* files. -> (file names, identity, ledger)."""
    from pathlib import Path
    from engine.source import boq_line as BL
    out = Path(out)
    l309, ident = integrate(l308, v309_changes)
    rows = ledger_rows(v309_changes, released_lines)
    diff = diff_rows(l308, l309, released_lines)
    dsum = {}
    for d in diff:
        dsum.setdefault("vs_v3_0_8", {}).setdefault(d["vs_v3_0_8"], 0)
        dsum["vs_v3_0_8"][d["vs_v3_0_8"]] += 1
        if d["vs_released_v2_9"] is not None:
            dsum.setdefault("vs_released_v2_9", {}).setdefault(d["vs_released_v2_9"], 0)
            dsum["vs_released_v2_9"][d["vs_released_v2_9"]] += 1
    ident = dict(ident, diff=dsum)
    led = {"schema": LEDGER_SCHEMA, "method": METHOD, "extends": EXTENDS, "candidate": CANDIDATE,
           "base": A30.BASE_METHOD, "released": A30.RELEASED_METHOD, "released_default": False, "rows": rows,
           "waiting_pieces": WAITING, "integration_package": True}
    t308, t309 = A304.code_totals(l308), A304.code_totals(l309)
    moved = {k: {"v3_0_8": t308.get(k), "v3_0_9": t309.get(k)} for k in sorted(set(t308) | set(t309))
             if t308.get(k) != t309.get(k)}
    g = (inputs or {}).get("guard") or {}
    run = {"method": METHOD, "policy": POLICY_ID, "extends": EXTENDS, "candidate": CANDIDATE,
           "base_method": A30.BASE_METHOD, "released_method": A30.RELEASED_METHOD, "released_default": False,
           "rollback": ROLLBACK, "identity": ident, "pieces": PIECES, "piece_logs": logs,
           "inputs": {"pieces": [{k: pc.get(k) for k in ("piece", "item_codes", "unit", "source", "sources", "scope",
                                                          "declared_totals")}
                                 for pc in (inputs or {}).get("pieces") or ()],
                      "guard": {k: g.get(k) for k in ("source", "evidence_file", "evidence_sha256", "conventions_file",
                                                      "conventions_sha256", "holding_checks", "recorded_checks",
                                                      "equal_value_rebase", "new_records")}},
           "totals_moved_by_code": moved, "waiting_pieces": WAITING,
           "evidence_status_counts": A302._count(r["evidence_status"] for r in rows)}
    files = {"V3_0_9_BOQ_LINES.json": BL.dumps(l309),
             "V3_0_9_BOQ_LINES.csv": A30._lines_csv(l309),
             "V3_0_9_INTEGRATION_LEDGER.json": A30._j(led),
             "V3_0_9_INTEGRATION_LEDGER.csv": ledger_csv(rows),
             "V3_0_9_DIFF.csv": A305._csv(diff, DIFF_CSV),
             "V3_0_9_RUN.json": A30._j(run)}
    for name, text in files.items():
        (out / name).write_text(text, encoding="utf-8")
    return sorted(files), ident, led


def policy_record():
    return {"method": METHOD, "extends": EXTENDS, "pieces": sorted(PIECES), "inputs_schema": INPUTS_SCHEMA,
            "released_default": False, "rollback": ROLLBACK}


__all__ = ["METHOD", "PIECES", "WAITING", "DEFAULT_GUARD_CLASS", "NO_FIGURE", "load_inputs", "net_of",
           "record_changes", "changes_for", "integrate", "ledger_rows", "diff_rows", "write", "InputsError"]
