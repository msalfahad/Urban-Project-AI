"""ARCH_TAKEOFF_V3.0 (T-131): ONE opt-in BOQ candidate that consolidates the checker-verified pieces into the
ARCH_TAKEOFF_V2.13 + route G run. Not the released default (owner management decision 2026-10-20 section 2: integration
of verified pieces into a versioned opt-in candidate APPROVED, switching the released default NOT approved). Rollback is
running the released ARCH_TAKEOFF_V2.9.

How the candidate is built (tools/urban_boq_m9.py `arch --method ARCH_TAKEOFF_V3.0`):
  1. the run is ARCH_TAKEOFF_V2.13 exactly (its own outputs are written unchanged, the same files a V2.13 run writes),
     with read-only captures of what each plan region's room builder saw (capture());
  2. each integrated piece reads the run and the drawings and proposes a change of named BOQ lines;
  3. integrate() copies every other line of the base run unchanged (a test asserts byte identity) and writes the V3.0
     files beside the base outputs: V3_0_BOQ_LINES.json / .csv, V3_0_INTEGRATION_LEDGER.json / .csv,
     V3_0_DOWNSTREAM.json, V3_0_RUN.json.

Integrated pieces (each carries a verifier MERGED verdict; PIECES below names the task, merge commit and verifier run):
  STRAPS                PLOT_EDGE_MEMBERS_V1 strap_records on the route G strap bands (faces by entity handle, schedule
                        section of the bound row) and the footing outlines on the strap layers (open outlines found):
                        the clear length between footing faces x the printed section replaces the route's band volume;
                        a part inside an OPEN footing outline is a separate BOUNDED_EXPOSURE line [0, length x section]
                        (the drawing does not close the footing; owner Q-31), never 0 and never in the measured line.
  FACADE_PASSAGE        FACADE_PASSAGE_WALLS_V1 on the facade outline of each floor: the walls of an open-air side
                        passage are exterior faces, its mouth is no building opening. A single-mouth passage whose roof
                        the plan does not settle is HELD as a range (BOUNDED_EXPOSURE walked .. walked + delta) unless a
                        project decision binds it (owner Q-67 A, conditional: no door, no glazing, nothing drawn across
                        the mouth, unlabelled: the piece's own tests 1-4). Geometric perimeter and billable run are
                        separate fields (owner Q-64 B): the billable run drops return faces only where a reveal line
                        measures them; the engine identifies none, so billable = geometric and that is listed.
  STAIR_FLOOR_RESIDUE   STAIR_FLOOR_RESIDUE_V1 on every room face with a floor-finish line: a face a stair passes
                        through or a void cuts gets its floor net of the exact tread union, the opening and the well;
                        a residue the drawing does not settle makes the line a range (BOUNDED_EXPOSURE), never one value.
  MEMBRANE_V2_13        the ARCH_TAKEOFF_V2.13 membrane purchase lines (Q-58 A proven cutting plans, the typed pantry
                        zone): integrated as they are (the base run is V2.13); listed in the ledger with V2.9 before.

Pieces waiting for the checker join later as V3.0.x extensions of this same candidate (never a new method family).

Rules: owner decision 2026-10-20 sections 2 and 5, Q-12 B, Q-16, Q-31, Q-37 A, Q-49 A, Q-56 A, Q-58 A, Q-64 B,
Q-67 A (conditional), UP-QTY-STATUS-001 (held is a range or blocked, never 0), UP-KB-PREC-001, UP-FACADE-001.
Nothing here names a project, a sheet, a layer or a handle; every number comes from the run or the drawings.
"""

from __future__ import annotations

import copy
import csv
import hashlib
import io
import json
import math
import re
from contextlib import contextmanager

METHOD = "ARCH_TAKEOFF_V3.0"
BASE_METHOD = "ARCH_TAKEOFF_V2.13"
RELEASED_METHOD = "ARCH_TAKEOFF_V2.9"
POLICY_ID = "URBAN_BOQ_T131_ARCH_V3_0"
DECISIONS_SCHEMA = "URBAN_V30_PROJECT_DECISIONS_V1"
LEDGER_SCHEMA = "URBAN_V30_INTEGRATION_LEDGER_V1"
ROLLBACK = "run the released ARCH_TAKEOFF_V2.9 (tools/urban_boq_m9.py arch --method ARCH_TAKEOFF_V2.9)"
FLOOR_ITEMS = ("FIN.FLOOR.PORCELAIN", "FIN.FLOOR.WET_TILE")
UNCHANGED_SCOPES = ("NO_STAIR_NO_VOID", "LOWEST_STOREY_NOT_ASSESSED")
MEMBRANE_ITEMS = ("FIN.WP.MEMBRANE_ROLLS",)
BUILDING_ROLES = ("WALL", "COLUMN", "WINDOW", "DOOR")
LEVEL_TEXT = re.compile(r"^\s*[+-]\s*\d+(?:[.,]\d+)?\s*$")
EPS = 1e-6

# the verification evidence of every integrated piece (verifier MERGED verdicts on the board, merge commits on the
# working branch); a piece without a MERGED verdict is never listed here
PIECES = {
    "STRAPS": {
        "module": "engine/source/plot_edge_members.py", "policy": "PLOT_EDGE_MEMBERS_V1", "task": "T-073",
        "merge_commit": "c874c7b", "verifier_run": "run 33 (2026-10-20 06:55 UTC), piece re-run on the drawing",
        "hand_check": "T-073 hand: SB1 4.55 m, SB2 2.294 m at the printed 1.00 m, SB3 3.251 m -> 3.390 m3",
        "owner_rules": ["Q-12 B (separate members)", "Q-16 (no size borrowed)", "Q-31 (open outline held)",
                        "UP-KB-PREC-001 (printed section over drawn width)"],
        "owner_manual_method": None,
        "owner_manual_note": "no separate owner manual method for strap volume: the owner rules bind the drawing "
                             "method (clear length between footing faces x the printed section)",
        "drawing_method": "clear length between footing faces (the centre line minus the parts inside closed and "
                          "open footing outlines) x the schedule W x H of the bound schedule row"},
    "FACADE_PASSAGE": {
        "module": "engine/source/facade_passage_walls.py", "policy": "FACADE_PASSAGE_WALLS_V1", "task": "T-109",
        "merge_commit": "4fddf74", "verifier_run": "verifier 16:49 run (2026-10-20), merge 17:12",
        "condition_check": {"task": "T-123", "merge_commit": "6699bb6", "verifier_run": "run 45 (2026-10-20 21:05 UTC)",
                            "finding": "0 entities across the mouth, far end closed by a boundary wall, no door or "
                                       "glazing: owner Q-67 A condition met on the drawings"},
        "owner_rules": ["Q-64 B (geometric perimeter vs billable run vs reveal returns)",
                        "Q-67 A conditional (open-air passage: exterior)", "UP-FACADE-001", "Q-25 (no gap limit)"],
        "owner_manual_method": "owner Q-64 B: billable main facade run = geometric perimeter less the return faces "
                               "measured under a window / glass reveal; never both",
        "drawing_method": "FACADE_PASSAGE_WALLS_V1: walked outline - passage mouths + every building face that "
                          "bounds the passage space"},
    "STAIR_FLOOR_RESIDUE": {
        "module": "engine/source/stair_floor_residue.py", "policy": "STAIR_FLOOR_RESIDUE_V1", "task": "T-116",
        "merge_commit": "5592692", "verifier_run": "verifier 16:49 run (2026-10-20), merge 17:10",
        "owner_rules": ["Q-56 A conditional (floor net of the stair)", "UP-STAIR-002", "UP-STAIR-005",
                        "UP-QTY-STATUS-001"],
        "owner_manual_method": "owner Q-56 A: room floor = the room face less the stair footprint and the void "
                               "(the landing finish waits on Q-66 B, T-122)",
        "drawing_method": "STAIR_FLOOR_RESIDUE_V1: face - exact tread union - opening and landing - well residue; "
                          "unsettled pieces held as a range"},
    "MEMBRANE_V2_13": {
        "module": "engine/source/arch_v213.py", "policy": "URBAN_BOQ_T120_ARCH_V2_13", "task": "T-120",
        "merge_commit": "2264938", "verifier_run": "run 44 (2026-10-20 18:40 UTC)",
        "owner_rules": ["Q-49 A (rolls per area alone)", "Q-58 A conditional (proven cutting plan)",
                        "Q-37 A (pantry zone)", "Q-17 A (typed printed size)"],
        "owner_manual_method": "owner Q-49 A / Q-58 A: rolls per area, a piece cut from that area's own offcut only "
                               "on a proven physical cutting plan",
        "drawing_method": "MEMBRANE_FOLD_V3 strips with the V2.13 Q-58 A proof"},
}
WAITING = {"T-122": "1F porcelain / landing marble under Q-66 B (research only: a wiring piece is still needed)",
           "T-123": "facade condition (used here as the evidence of the Q-67 A condition; the reveal-return line is "
                    "still missing)",
           "T-124": "MEMBRANE_FOLD_V5 offcut-once audit (verified, read by no method: joins as V3.0.x)",
           "T-126": "route G blinding scope / undrawn columns (READY, not yet verified)"}


# ================================================================================================ capture
@contextmanager
def capture():
    """read-only: per plan region, what arch_rooms.spaces saw (entities, layer roles, unit) and the arrangement and
    result of its last facade_outlines call. A later run of a region replaces the earlier one (the last run is the one
    whose lines are kept, as engine.source.arch_v211.capture)."""
    from engine.source import arch_rooms as AR
    from engine.source import arch_v29 as V29
    cap, cur = {}, [None]
    o_spaces, o_facade = AR.spaces, V29.facade_outlines

    def spaces(ents, roles, unit_m, **kw):
        rid = kw.get("region_id")
        prev = cur[0]
        cur[0] = rid
        cap[rid] = {"ents": ents, "roles": dict(roles), "unit_m": unit_m, "facade": None}
        try:
            return o_spaces(ents, roles, unit_m, **kw)
        finally:
            cur[0] = prev

    def facade(arr, unit_m, min_space_m2):
        res = o_facade(arr, unit_m, min_space_m2)
        if cur[0] is not None and cur[0] in cap:
            cap[cur[0]]["facade"] = {"arr": arr, "unit_m": unit_m, "result": res}
        return res
    AR.spaces, V29.facade_outlines = spaces, facade
    try:
        yield cap
    finally:
        AR.spaces, V29.facade_outlines = o_spaces, o_facade


# ================================================================================================ small helpers
def _r(x, n=6):
    return None if x is None else round(float(x), n)


def _qty(ln):
    """(state, value, low, high) of a line: a quantity line has a value, a bounded line a range, others neither."""
    if ln is None:
        return {"state": None, "value": None, "low": None, "high": None}
    br = ln.get("bounded_range") or {}
    ev = ln["evidence_state"]
    if ev == "BOUNDED_EXPOSURE":
        return {"state": ev, "value": None, "low": _r(br.get("low")), "high": _r(br.get("high"))}
    return {"state": ev, "value": _r(ln.get("measured_net")), "low": None, "high": None}


def _key(ln):
    loc = ln.get("location") or {}
    return "|".join(str(x) for x in (ln["item_code"], loc.get("floor"), loc.get("room_id"), loc.get("element_id"),
                                     ln["unit"]))


def _new_id(*parts):
    return "L-" + hashlib.sha256("|".join(map(str, (POLICY_ID,) + parts)).encode()).hexdigest()[:20]


def _note(ln, text):
    ln["notes"] = (ln.get("notes") + "; " if ln.get("notes") else "") + text


def _change(piece, action, before, after, **kw):
    return dict({"piece": piece, "action": action, "before": before, "after": after}, **kw)


def line_sha(ln):
    return hashlib.sha256(json.dumps(ln, sort_keys=True, ensure_ascii=False, default=str).encode()).hexdigest()


# ================================================================================================ decisions
def load_decisions(doc, project_id):
    """URBAN_V30_PROJECT_DECISIONS_V1: {"schema", "project", "decisions": [{"question", "answer", "binds", "floors",
    "condition", "condition_evidence", "source"}]}. A file for another project, or a record without its condition
    evidence, binds nothing (listed, never silently used)."""
    out = {"schema": DECISIONS_SCHEMA, "used": [], "refused": []}
    if not doc:
        return out
    if doc.get("schema") != DECISIONS_SCHEMA:
        raise ValueError(f"--v30-decisions: schema must be {DECISIONS_SCHEMA}")
    for d in doc.get("decisions") or ():
        why = None
        if doc.get("project") != project_id:
            why = f"OTHER_PROJECT ({doc.get('project')} is not {project_id})"
        elif not (d.get("question") and d.get("answer") and d.get("binds")):
            why = "INCOMPLETE: question, answer and binds are required"
        elif d.get("conditional") and not d.get("condition_evidence"):
            why = "CONDITION_NOT_EVIDENCED: a conditional answer binds only with the check that its condition is met"
        (out["refused"] if why else out["used"]).append(dict(d, **({"refused": why} if why else {})))
    return out


def _binds(decisions, what, floor):
    for d in (decisions or {}).get("used") or ():
        if d["binds"] == what and (not d.get("floors") or floor in d["floors"]):
            return d
    return None


# ================================================================================================ STRAPS
def _handle_hex(h):
    """route G entity reference 'D<doc>:<decimal handle>:<sub>' -> the DXF handle (hex), else None."""
    parts = str(h).split(":")
    if len(parts) >= 2 and parts[1].isdigit():
        return format(int(parts[1]), "X")
    return None


def strap_changes(R, structural_path, base_lines):
    """the route G strap bands re-measured by PLOT_EDGE_MEMBERS_V1. -> (changes, log)."""
    from engine.source import plot_edge_members as PE
    log = {"piece": "STRAPS", "bands": [], "state": "NOT_RUN"}
    if R is None or structural_path is None:
        log["state"] = "NO_STRUCTURAL_DRAWING"
        return [], log
    D = ((R.get("generic") or {}).get("D")) or {}
    u = D.get("unit_m")
    sheets = D.get("sheets") or {}
    by_elem = {}
    for ln in base_lines:
        if ln["item_code"] == "STR.CONC.STRAP":
            by_elem.setdefault((ln.get("location") or {}).get("element_id"), []).append(ln)
    if not by_elem:
        log["state"] = "NO_STRAP_LINE"
        return [], log
    import ezdxf
    doc = ezdxf.readfile(str(structural_path))
    msp = doc.modelspace()
    changes = []
    log["state"] = "RUN"
    for sid, sh in sorted(sheets.items()):
        st = sh.get("straps") or {}
        bands = [b for b in st.get("bands") or () if b.get("family") == "STRAP_BEAM"]
        if not bands:
            continue
        layers = sorted(set(st.get("layers") or ()))
        fo = PE.footing_outlines(msp, set(layers), u)
        straps, meta = [], {}
        for b in bands:
            rec = {"band": b["band_id"], "mark": b.get("mark"), "sheet": sid, "state": None}
            faces = []
            for h in b.get("handles") or ():
                e = doc.entitydb.get(_handle_hex(h) or "")
                if e is not None and e.dxftype() == "LINE":
                    faces.append(((float(e.dxf.start.x), float(e.dxf.start.y)), (float(e.dxf.end.x), float(e.dxf.end.y))))
            if len(faces) != 2:
                log["bands"].append(dict(rec, state="KEPT_FACES_NOT_TWO_LINES",
                                         why="the band's two faces are not two LINE entities: the route line stays"))
                continue
            straps.append({"id": b["band_id"], "mark": b.get("mark"), "faces": faces, "W_m": b.get("schedule_width_m"),
                           "H_m": b.get("depth_m"), "row_source": b.get("schedule_source")})
            meta[b["band_id"]] = b
        for s in PE.strap_records(straps, fo["members"], u):
            b = meta[s["id"]]
            hits = [ln for el, lns in by_elem.items() if el and str(el).endswith(":" + b["band_id"]) for ln in lns]
            rec = {"band": b["band_id"], "mark": b.get("mark"), "sheet": sid, "record": {
                k: v for k, v in s.items() if k != "lines"}, "footing_layers": layers,
                "footings_read": len(fo["members"]), "open_outlines": [
                    {"id": m["id"], "gap_m": m["open_gap_m"]} for m in fo["members"] if m.get("open_gap_m") is not None]}
            if len(hits) != 1:
                log["bands"].append(dict(rec, state="KEPT_LINE_NOT_FOUND_ONCE", lines=len(hits)))
                continue
            base = hits[0]
            clear = next((x for x in s.get("lines") or () if x.get("part") == "CLEAR"), None)
            if clear is None or clear.get("status") != "MEASURED":
                log["bands"].append(dict(rec, state="KEPT_PIECE_HELD", why=(clear or {}).get("reason") or s.get("reason")))
                continue
            after = copy.deepcopy(base)
            v = clear["volume_m3"]
            after["measured_net"] = v
            after["bounded_range"] = {"low": v, "high": v, "basis": "ARCH_TAKEOFF_V3.0 strap piece: one value"}
            after["calculation"] = {
                "formula": "clear length between footing faces x schedule W x H (PLOT_EDGE_MEMBERS_V1, "
                           "UP-KB-PREC-001: the printed width outranks the drawn width)",
                "inputs": {"clear_length_m": s["clear_length_m"], "W_m": clear["section"]["W_m"],
                           "H_m": clear["section"]["H_m"], "schedule_row": clear["section"].get("source"),
                           "drawn_width_m": s["drawn_width_m"], "face_overlap_m": s["face_overlap_m"],
                           "in_footing_m": s["in_footing_m"], "in_open_outline_m": s["in_open_outline_m"],
                           "schedule_alternatives": b.get("alternatives") or [],
                           "base_line": {"formula": base["calculation"].get("formula"),
                                         "inputs": base["calculation"].get("inputs")}}}
            _note(after, f"{METHOD}: strap {b.get('mark')} re-measured by PLOT_EDGE_MEMBERS_V1 (T-073, verified)")
            held = []
            adds = []
            if s["in_open_outline_m"] > EPS:
                hi = s["in_open_outline_m"] * clear["section"]["W_m"] * clear["section"]["H_m"]
                add = copy.deepcopy(base)
                add["line_id"] = _new_id("STRAP_IN_OPEN_OUTLINE", b["band_id"])
                add["location"] = dict(add["location"], element_id=f"{base['location']['element_id']}:IN_OPEN_FOOTING_OUTLINE")
                add["physical_element"] = f"{base.get('physical_element')} (inside an open footing outline)"
                add["evidence_state"] = "BOUNDED_EXPOSURE"
                add["measured_net"] = None
                add["bounded_range"] = {"low": 0.0, "high": _r(hi),
                                        "basis": "the strap stops at the footing outline (0) or runs on inside it "
                                                 "(length x section): the drawing leaves the outline open"}
                add["calculation"] = {"formula": "length inside the open footing outline x schedule W x H (high); "
                                                 "0 when the footing takes it (low)",
                                      "inputs": {"length_m": s["in_open_outline_m"], "W_m": clear["section"]["W_m"],
                                                 "H_m": clear["section"]["H_m"]}}
                add["rfi"] = {"question": "FOOTING_OUTLINE_OPEN (owner Q-31): the footing outline the strap enters is "
                                          "not closed by the drawing; is that length footing or strap?",
                              "unlocks": base["location"]["element_id"]}
                add["notes"] = f"{METHOD}: held part of strap {b.get('mark')} (T-073 piece), never 0, never in the measured line"
                held.append({"what": f"strap {b.get('mark')} inside an open footing outline",
                             "length_m": s["in_open_outline_m"], "range_m3": [0.0, _r(hi)], "line_id": add["line_id"]})
                adds.append(add)
            if b.get("alternatives"):
                held.append({"what": f"schedule conflict for {b.get('mark')}: another row of the same mark",
                             "alternatives": b["alternatives"],
                             "kept": "the row the drawn width binds (within 0.015 m), as the route and the hand check"})
            ref = f"structural drawing sheet {sid} (foundation plan), strap faces {', '.join(b.get('handles') or ())}"
            changes.append(_change("STRAPS", "REPLACE", base, after, drawing_reference=ref, held=held,
                                   downstream=_rebar_downstream(base_lines, base)))
            for add in adds:
                changes.append(_change("STRAPS", "ADD", None, add, drawing_reference=ref, held=[],
                                       downstream=[]))
            log["bands"].append(dict(rec, state="CHANGED", before_m3=_r(base.get("measured_net")), after_m3=_r(v)))
    return changes, log


def _rebar_downstream(lines, base):
    el = (base.get("location") or {}).get("element_id") or ""
    tail = el.split(":", 1)[1] if ":" in el else el
    return [{"line_id": ln["line_id"], "item_code": ln["item_code"], "reads": "the strap clear span (rebar length)",
             "v3_0": "UNCHANGED (rebar stays its own line family, outside this candidate; listed for review)"}
            for ln in lines if ln["item_code"] == "STR.REBAR"
            and tail and tail in ((ln.get("location") or {}).get("element_id") or "")]


# ================================================================================================ FACADE_PASSAGE
def _outline_index(arr, unit_m, perimeter_m):
    from engine.source import arch_v29 as V29
    hits = [k for k, f in enumerate(arr.faces) if f["area"] <= 0 and f["cycle"]
            and abs(V29._outline(arr, k, unit_m)["perimeter_m"] - perimeter_m) < 1e-6]
    return hits[0] if len(hits) == 1 else None


def passage_changes(cap, base_lines, rooms, regions, decisions):
    """FACADE_PASSAGE_WALLS_V1 on the facade outline of every floor whose run line exists. -> (changes, log)."""
    from engine.source import facade_passage_walls as P
    log = {"piece": "FACADE_PASSAGE", "floors": []}
    changes = []
    floor_of = {r["region_id"]: r["floor"] for r in regions or ()}
    for rid, c in sorted((cap or {}).items(), key=lambda kv: str(kv[0])):
        floor = floor_of.get(rid)
        fac = c.get("facade")
        runs = [ln for ln in base_lines if ln["item_code"] == "ARCH.FACADE_RUN"
                and (ln.get("location") or {}).get("floor") == floor
                and ln.get("measured_net") is not None and ln["evidence_state"] in ("MEASURED", "SOURCE_DERIVED",
                                                                                     "PROVISIONAL")]
        rec = {"region_id": rid, "floor": floor}
        if fac is None or len(runs) != 1:
            log["floors"].append(dict(rec, state="NOT_ASSESSED", why="no facade capture" if fac is None else
                                      f"{len(runs)} measured facade run lines on the floor (one is needed)"))
            continue
        base = runs[0]
        per = (base["calculation"].get("inputs") or {}).get("perimeter_m")
        arr, u = fac["arr"], fac["unit_m"]
        k = _outline_index(arr, u, per) if per is not None else None
        if k is None:
            log["floors"].append(dict(rec, state="NOT_ASSESSED", why="the run line's outline is not found once"))
            continue
        ring = P.ring_with_inner(arr, k, u)
        faces = P.faces_from_arrangement(arr, u)
        roles = c["roles"]
        building = {lay for lay, ro in roles.items() if ro in BUILDING_ROLES}
        segs = (c["ents"] or {}).get("segments") or ()
        other = [{"a": (s["a"][0] * u, s["a"][1] * u), "b": (s["b"][0] * u, s["b"][1] * u), "layer": s.get("layer")}
                 for s in segs if s.get("layer") not in building]
        texts = (c["ents"] or {}).get("texts") or ()
        levels = [{"at": (t["x"] * u, t["y"] * u), "value": t.get("text")} for t in texts
                  if LEVEL_TEXT.match(str(t.get("text") or "")) and "x" in t and "y" in t]
        labels = [[r["point"][0] * u, r["point"][1] * u] for r in rooms or ()
                  if r.get("region_id") == rid and r.get("class") != "UNLABELLED" and r.get("point")]
        res = P.passage_walls(ring, faces, labels=labels, above=None, other_lines=other, levels=levels)
        dec = _binds(decisions, "PASSAGE_SINGLE_OPEN_MOUTH_EXTERIOR", floor)
        applied, held_p, released = 0.0, [], []
        for p in res["passages"]:
            if p["state"] == "OPEN_AIR":
                applied += p["delta_m"]
                released.append(p)
            elif (p["state"] == "HELD" and dec is not None and p.get("delta_m") is not None
                  and str(p.get("why", "")).startswith(("ROOF_NOT_READ", "COVERED_ONE_MOUTH"))
                  and sum(1 for m in p["mouths"] if m.get("cls") == "OPEN_MOUTH") == 1):
                applied += p["delta_m"]
                released.append(dict(p, state="OPEN_AIR", why=f"BOUND by owner {dec['question']} {dec['answer']}: "
                                     + p["why"]))
            elif p["state"] == "HELD":
                held_p.append(p)
        walked = res.get("walked_m")
        log_rec = dict(rec, state=res["state"], piece_state=res["state"], walked_m=walked, passages=[
            {k2: v for k2, v in p.items() if k2 not in ("walls",)} for p in res["passages"]],
            decision=dec, wall_end_gaps=res.get("wall_end_gaps"))
        if res["state"] in ("NO_PASSAGE", "NO_OUTLINE") or (not released and not held_p):
            log["floors"].append(dict(log_rec, change="NONE"))
            continue
        run = walked + applied
        unknown = any(p.get("delta_m") is None for p in held_p)
        lo = run + sum(min(0.0, p["delta_m"]) for p in held_p if p.get("delta_m") is not None)
        hi = run + sum(max(0.0, p["delta_m"]) for p in held_p if p.get("delta_m") is not None)
        after = copy.deepcopy(base)
        inputs = dict(after["calculation"].get("inputs") or {})
        nbo = sorted({m["opening_id"] for p in released for m in p["mouths"] if m.get("opening_id")})
        inputs.update(v3_0={"policy": P.POLICY, "walked_m": walked, "geometric_perimeter_m": _r(run) if not held_p else None,
                            "billable_run_m": _r(run) if not held_p else None,
                            "billable_basis": "Q-64 B: no return face of this outline is measured by a reveal line "
                                              "the engine identifies; billable = geometric (listed, never both)",
                            "passages_released": len(released), "passages_held": len(held_p),
                            "not_building_openings": nbo, "decision": dec and {k2: dec.get(k2) for k2 in (
                                "question", "answer", "binds", "condition_evidence")}})
        after["calculation"] = dict(after["calculation"], inputs=inputs,
                                    formula=after["calculation"].get("formula", "") +
                                    " + FACADE_PASSAGE_WALLS_V1: passage mouths out, the passage's building faces in")
        if held_p:
            after["evidence_state"] = "BOUNDED_EXPOSURE"
            after["measured_net"] = None
            if unknown:
                after["evidence_state"] = "BLOCKED_RFI"
                after["bounded_range"] = None
            else:
                after["bounded_range"] = {"low": _r(lo), "high": _r(hi),
                                          "basis": "a passage behind a doorless mouth the plan does not settle: the run "
                                                   "with and without its walls (FACADE_PASSAGE_WALLS_V1 rule 5)"}
            after["rfi"] = {"question": "PASSAGE_NOT_SETTLED: " + "; ".join(str(p.get("why")) for p in held_p) +
                            " (a project decision, e.g. owner Q-67 A with its condition checked, binds it)",
                            "unlocks": base["location"]["element_id"]}
        else:
            after["measured_net"] = _r(run)
        _note(after, f"{METHOD}: facade run with the open-air passage walls (T-109 piece; Q-67 / Q-64 B)")
        heldl = [{"what": "passage not settled by the plan", "why": p.get("why"), "delta_m": p.get("delta_m"),
                  "mouths": [m.get("opening_id") for m in p["mouths"]]} for p in held_p]
        heldl.append({"what": "Q-64 B return faces (notch beside a window frame)",
                      "state": "NOT_IDENTIFIED_BY_THE_ENGINE",
                      "why": "the billable run would drop them only where a reveal line measures them; no reveal "
                             "line of the base run does (T-123 found 0.100 m on the development villa by hand)"})
        downstream = []
        ref = f"architectural plan region {rid}: facade outline, passage mouths {', '.join(nbo) or 'none released'}"
        changes.append(_change("FACADE_PASSAGE", "REPLACE", base, after, drawing_reference=ref, held=heldl,
                               downstream=downstream))
        # downstream: the facade area lines of the floor read the run (no quantity until a height is printed)
        for ln in base_lines:
            loc = ln.get("location") or {}
            if (ln["item_code"] == "ARCH.FACADE" and loc.get("floor") == floor
                    and loc.get("room_id") == base["location"].get("room_id")
                    and (ln["calculation"].get("inputs") or {}).get("perimeter_m") == per):
                a2 = copy.deepcopy(ln)
                a2["calculation"] = dict(a2["calculation"], inputs=dict(
                    a2["calculation"].get("inputs") or {}, perimeter_m=after["measured_net"],
                    perimeter_range_m=None if not held_p or unknown else [_r(lo), _r(hi)],
                    v3_0_run_line=after["line_id"]))
                _note(a2, f"{METHOD}: reads the V3.0 facade run (was {per} m in {BASE_METHOD}); no quantity until a "
                          "facade height is printed (owner Q-07)")
                downstream.append({"line_id": ln["line_id"], "item_code": ln["item_code"],
                                   "reads": "the facade run (perimeter_m)", "v3_0": "INPUT_UPDATED, still no quantity"})
                changes.append(_change("FACADE_PASSAGE", "DOWNSTREAM_UPDATE", ln, a2, drawing_reference=ref,
                                       held=[], downstream=[]))
        # the mouths are not building openings when their passage is released
        for ln in base_lines:
            loc = ln.get("location") or {}
            if loc.get("floor") != floor:
                continue
            oid = str(loc.get("element_id") or "").rsplit(":", 1)[-1]
            strip = next((o for o in nbo if str(loc.get("room_id") or "").endswith(f"STRIP-{o}")), None)
            if ln["item_code"] == "ARCH.PASSAGE" and oid in nbo:
                a2 = copy.deepcopy(ln)
                a2["evidence_state"] = "NOT_APPLICABLE_WITH_EVIDENCE"
                a2["measured_net"] = None
                a2["bounded_range"] = None
                a2["notes"] = (f"{METHOD}: NOT_A_BUILDING_OPENING - {oid} is the mouth of an open-air passage "
                               "(FACADE_PASSAGE_WALLS_V1, T-109; owner Q-67 A); was 1 pcs in " + BASE_METHOD)
                downstream.append({"line_id": ln["line_id"], "item_code": ln["item_code"],
                                   "reads": f"opening {oid}", "v3_0": "NOT_A_BUILDING_OPENING"})
                changes.append(_change("FACADE_PASSAGE", "DOWNSTREAM_UPDATE", ln, a2, drawing_reference=ref,
                                       held=[], downstream=[]))
            elif strip is not None:
                downstream.append({"line_id": ln["line_id"], "item_code": ln["item_code"],
                                   "reads": f"the doorway strip of {strip}",
                                   "v3_0": "UNCHANGED, FLAGGED: a strip at a mouth that is no building opening "
                                           "(review; no verified piece removes it)"})
        log["floors"].append(dict(log_rec, change="CHANGED", v3_0_state="HELD" if held_p else "RESOLVED",
                                  run_m=_r(run) if not held_p else None,
                                  range_m=None if not held_p or unknown else [_r(lo), _r(hi)]))
    return changes, log


# ================================================================================================ STAIR_FLOOR_RESIDUE
def stair_changes(room_boq, arch, E):
    """STAIR_FLOOR_RESIDUE_V1 on every room face with a floor-finish line (the T-116 reading of the run). A face
    with no stair and no void, and the lowest storey, keep the base line. -> (changes, log)."""
    from engine.source import stair_floor_residue as SFR
    log = {"piece": "STAIR_FLOOR_RESIDUE", "rooms": []}
    u = arch["run"]["unit_m"]
    voids = {}
    for v in arch["run"].get("double_height") or ():
        if v.get("state") != "APPLIED":
            continue
        dx, dy = v["offset"]["dx"], v["offset"]["dy"]
        voids.setdefault(v["floor"], []).append({"void_id": v["void_id"],
                                                 "corners": [(x - dx, y - dy) for x, y in v["window"]]})
    lines = {}
    for ln in room_boq["lines"]:
        if ln["item_code"] in FLOOR_ITEMS:
            lines.setdefault((ln.get("location") or {}).get("room_id"), []).append(ln)
    doors = {}
    for o in arch.get("openings") or ():
        c = (o.get("position") or {}).get("centre_m")
        if c:
            for r in o.get("rooms") or ():
                doors.setdefault(r, []).append((c[0] / u, c[1] / u))
    changes = []
    mats = room_boq.get("materials") or ()
    for room in arch["rooms"]:
        lns = lines.get(room["room_id"]) or []
        if not lns:
            continue
        rec = {"room_id": room["room_id"], "floor": room["floor"]}
        if len(lns) != 1:
            log["rooms"].append(dict(rec, state="KEPT_SEVERAL_FLOOR_LINES", lines=len(lns)))
            continue
        base = lns[0]
        r = SFR.face_residue(room, voids=voids.get(room["floor"], ()), segments=E["segments"], arcs=E["arcs"],
                             unit_m=u, floor_points=doors.get(room["room_id"], ()))
        rr = dict(rec, scope=r.get("scope"), status=r.get("status"), low=r.get("floor_net_low_m2"),
                  high=r.get("floor_net_high_m2"), base=base.get("measured_net"))
        if r.get("scope") in UNCHANGED_SCOPES:
            log["rooms"].append(dict(rr, state="KEPT"))
            continue
        lo, hi = r.get("floor_net_low_m2"), r.get("floor_net_high_m2")
        if lo is None or hi is None:
            log["rooms"].append(dict(rr, state="KEPT_PIECE_NOT_SETTLED", why=r.get("reason") or r.get("status")))
            continue
        after = copy.deepcopy(base)
        inputs = dict(after["calculation"].get("inputs") or {})
        inputs["v3_0"] = {"policy": r.get("policy"), "scope": r.get("scope"), "face_m2": r.get("face_m2"),
                          "treads_counted_once_m2": r.get("treads_counted_once_m2"), "void_m2": r.get("void_m2"),
                          "void_residue_m2": r.get("void_residue_m2"), "stair_footprint_m2": r.get("stair_footprint_m2"),
                          "held_m2": r.get("held_m2"), "floor_before_residue_m2": r.get("floor_before_residue_m2"),
                          "conservation": r.get("conservation")}
        after["calculation"] = dict(after["calculation"], inputs=inputs,
                                    formula=after["calculation"].get("formula", "") +
                                    " - stair footprint (exact tread union), opening and well residue "
                                    "(STAIR_FLOOR_RESIDUE_V1)")
        if hi - lo > EPS:
            after["evidence_state"] = "BOUNDED_EXPOSURE"
            after["measured_net"] = None
            after["bounded_range"] = {"low": _r(lo), "high": _r(hi),
                                      "basis": "pieces the drawing does not settle (foot of a flight, an element beside "
                                               "a flight): low = not floor, high = floor"}
            after["rfi"] = {"question": "STAIR_FLOOR_PIECES_NOT_SETTLED: " + "; ".join(
                f"{h.get('category')} {h.get('m2')} m2" for h in r.get("held") or ()), "unlocks": room["room_id"]}
        else:
            after["measured_net"] = _r(lo)
        _note(after, f"{METHOD}: floor net of the stair and the void (T-116 piece; owner Q-56 A)")
        held = [{"what": h.get("category"), "m2": h.get("m2"), "why": h.get("reason")} for h in r.get("held") or ()]
        down = [{"material_result": m.get("method"), "line_id": m.get("line_id"),
                 "reads": "the floor net (net_installed_m2)", "base_net_installed_m2": m.get("net_installed_m2"),
                 "v3_0": "STALE: computed from the base floor; recomputed when the range settles (held)"}
                for m in mats if m.get("line_id") == base["line_id"]]
        changes.append(_change("STAIR_FLOOR_RESIDUE", "REPLACE", base, after,
                               drawing_reference=f"architectural plan {room['floor']}: room face {room['room_id']}, "
                                                 "stair flights, void window", held=held, downstream=down))
        log["rooms"].append(dict(rr, state="CHANGED"))
    return changes, log


# ================================================================================================ MEMBRANE (V2.13)
def membrane_rows(base_lines):
    """the V2.13 membrane purchase lines, integrated as they are (listed with V2.9 before by the ledger)."""
    return [_change("MEMBRANE_V2_13", "AS_IN_BASE", ln, ln, drawing_reference="architectural plan: wet areas and "
                    "roofs (MEMBRANE_FOLD_V3 strips, V2.13 Q-58 A proof)", held=[], downstream=[])
            for ln in base_lines if ln["item_code"] in MEMBRANE_ITEMS]


# ================================================================================================ integrate
def integrate(base_lines, changes):
    """the candidate lines: every base line, the changed ones replaced in place, the added ones after the line they
    belong to; every other line is the base line itself. -> (lines, identity record)."""
    from engine.source import boq_line as BL
    rep = {}
    adds = []
    for c in changes:
        if c["action"] in ("REPLACE", "DOWNSTREAM_UPDATE"):
            lid = c["before"]["line_id"]
            if lid in rep:
                raise ValueError(f"{METHOD}: line {lid} changed by two pieces")
            rep[lid] = c["after"]
        elif c["action"] == "ADD":
            adds.append(c["after"])
    ids = {ln["line_id"] for ln in base_lines}
    if rep.keys() - ids:
        raise ValueError(f"{METHOD}: a change names a line the base run does not have")
    out = []
    for ln in base_lines:
        out.append(rep.get(ln["line_id"], ln))
    for a in adds:
        if a["line_id"] in ids:
            raise ValueError(f"{METHOD}: an added line repeats a base line id")
        out.append(a)
    if len({ln["line_id"] for ln in out}) != len(out):
        raise ValueError(f"{METHOD}: a BOQ line id appears twice")
    for ln in out:
        BL.validate(ln)
    unchanged = [ln for ln in base_lines if ln["line_id"] not in rep]
    same = sum(1 for ln in out if ln["line_id"] not in rep and ln["line_id"] in ids)
    ident = {"base_lines": len(base_lines), "candidate_lines": len(out), "replaced": len(rep), "added": len(adds),
             "unchanged": len(unchanged), "unchanged_identical": same,
             "unchanged_sha256": hashlib.sha256("".join(line_sha(x) for x in unchanged).encode()).hexdigest()}
    if same != len(unchanged):
        raise ValueError(f"{METHOD}: an unchanged line differs from the base")
    return out, ident


def ledger(changes, released_lines=None):
    """one row per changed (or listed) line: before (released V2.9 when given, base V2.13), after, delta, drawing
    reference, owner manual and drawing-derived method, verification evidence, held items, downstream."""
    rel = {_key(ln): ln for ln in released_lines or ()}
    rows = []
    for c in changes:
        ref = c["after"] if c["before"] is None else c["before"]
        b13, aft = _qty(c["before"]), _qty(c["after"])
        b29 = None
        if released_lines is not None:
            b29 = _qty(rel.get(_key(ref))) if _key(ref) in rel else dict(_qty(None), state="NOT_IN_RELEASED")
        d = None
        if b13["value"] is not None and aft["value"] is not None:
            d = {"delta": _r(aft["value"] - b13["value"]),
                 "pct": _r(100.0 * (aft["value"] - b13["value"]) / b13["value"], 3) if b13["value"] else None}
        p = PIECES[c["piece"]]
        loc = ref.get("location") or {}
        rows.append({"piece": c["piece"], "action": c["action"], "line_id": ref["line_id"], "item_code": ref["item_code"],
                     "floor": loc.get("floor"), "room_id": loc.get("room_id"), "element_id": loc.get("element_id"),
                     "unit": ref["unit"], "before_released_v2_9": b29, "before_base_v2_13": b13, "after_v3_0": aft,
                     "change": d, "drawing_reference": c.get("drawing_reference"),
                     "owner_manual_method": p.get("owner_manual_method") or p.get("owner_manual_note"),
                     "drawing_method": p["drawing_method"], "owner_rules": p["owner_rules"],
                     "verification": {k: p[k] for k in ("task", "merge_commit", "verifier_run", "module", "policy")}
                     | ({"condition_check": p["condition_check"]} if "condition_check" in p else {}),
                     "held": c.get("held") or [], "downstream": c.get("downstream") or [], "rollback": ROLLBACK})
    return {"schema": LEDGER_SCHEMA, "method": METHOD, "base": BASE_METHOD, "released": RELEASED_METHOD,
            "released_default": False, "rows": rows, "waiting_pieces": WAITING}


LEDGER_CSV = ("piece", "action", "line_id", "item_code", "floor", "room_id", "element_id", "unit", "v2_9_state",
              "v2_9_value", "v2_9_low", "v2_9_high", "v2_13_state", "v2_13_value", "v2_13_low", "v2_13_high",
              "v3_0_state", "v3_0_value", "v3_0_low", "v3_0_high", "delta", "delta_pct", "drawing_reference",
              "verification", "held", "downstream")


def ledger_csv(led):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=list(LEDGER_CSV), lineterminator="\n")
    w.writeheader()
    for r in led["rows"]:
        row = {k: r.get(k) for k in ("piece", "action", "line_id", "item_code", "floor", "room_id", "element_id",
                                     "unit", "drawing_reference")}
        for tag, q in (("v2_9", r["before_released_v2_9"]), ("v2_13", r["before_base_v2_13"]), ("v3_0", r["after_v3_0"])):
            q = q or {}
            row.update({f"{tag}_state": q.get("state"), f"{tag}_value": q.get("value"), f"{tag}_low": q.get("low"),
                        f"{tag}_high": q.get("high")})
        row.update(delta=(r["change"] or {}).get("delta"), delta_pct=(r["change"] or {}).get("pct"),
                   verification=f"{r['verification']['task']} {r['verification']['merge_commit']} "
                                f"({r['verification']['verifier_run']})",
                   held=json.dumps(r["held"], ensure_ascii=False, default=str),
                   downstream=json.dumps(r["downstream"], ensure_ascii=False, default=str))
        w.writerow(row)
    return buf.getvalue()


def run_record(ident, logs, decisions, inputs):
    return {"method": METHOD, "policy": POLICY_ID, "base_method": BASE_METHOD, "released_method": RELEASED_METHOD,
            "released_default": False, "rollback": ROLLBACK, "identity": ident, "pieces": PIECES,
            "piece_logs": logs, "decisions": decisions, "inputs": inputs, "waiting_pieces": WAITING}


def _j(obj):
    return json.dumps(obj, indent=1, sort_keys=True, ensure_ascii=False, default=str) + "\n"


def write(out, base_lines, changes, logs, decisions, inputs, released_lines=None):
    """the V3.0 files beside the base run's outputs. -> the file names."""
    from engine.source import boq_line as BL
    from pathlib import Path
    out = Path(out)
    lines, ident = integrate(base_lines, changes)
    led = ledger([c for c in changes] + membrane_rows(base_lines), released_lines)
    down = [dict(d, from_line=r["line_id"], piece=r["piece"]) for r in led["rows"] for d in r["downstream"]]
    files = {"V3_0_BOQ_LINES.json": BL.dumps(lines),
             "V3_0_BOQ_LINES.csv": _lines_csv(lines),
             "V3_0_INTEGRATION_LEDGER.json": _j(led),
             "V3_0_INTEGRATION_LEDGER.csv": ledger_csv(led),
             "V3_0_DOWNSTREAM.json": _j({"method": METHOD, "rows": down}),
             "V3_0_RUN.json": _j(run_record(ident, logs, decisions, inputs))}
    for name, text in files.items():
        (out / name).write_text(text, encoding="utf-8")
    return sorted(files), ident, led


def _lines_csv(lines):
    from engine.source import boq_line as BL
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=list(BL.CSV_COLUMNS), extrasaction="ignore", lineterminator="\n")
    w.writeheader()
    for r in BL.csv_rows(lines):
        w.writerow(r)
    return buf.getvalue()
