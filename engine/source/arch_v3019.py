"""ARCH_TAKEOFF_V3.0.19 (T-255): the SAME opt-in BOQ candidate as ARCH_TAKEOFF_V3.0 .. V3.0.18 (engine.source.arch_v30,
arch_v301 .. arch_v3018), extended with ONE piece, END_CLOSURE_AND_OPENING_TRACE. Not a new method family and not the
released default (owner management decision 2026-10-20 sections 2 and 5); rollback is running the released
ARCH_TAKEOFF_V2.9.

The physical questions (ERS 2026-10-22 s.2.1, s.3):

  END_CLOSURE   an ARC BAND (a curved beam between two drawn arcs) ends where the DRAWING closes it: on the faces that
                meet it (the face of an adjoining beam, the faces of a column), never on a chord between its arc ends
                and never on an arc span (rule R-ARC-BAND-END-1, T-255; provenance: Checker 2026-10-25 16:00
                F-T254-01 read + ERS s.2.1). A column standing in the band is deducted as its own trade. The concrete
                in the closed boundary that the chord reading left out (a closing triangle) is owned by exactly ONE
                line: the band's.
                A record REBASEs the band line in place to (net plan by drawn faces) x (printed depth), with the
                reconciliation to the reading it retires carried on the line: drawn net = chord net + closing pieces.
  OPENING_TRACE every drawn opening is deducted ONCE per trade face (masonry, each finish side) and counted once in its
                supply line (rule R-OPENING-ONCE-1, T-255; provenance T-237 crosswalk, T-249 inventory, T-250 room
                sides). The trace changes NO line: per opening and trade it records the candidate line ids that carry
                the supply quantity or the deduction, or why none does (NOT_APPLICABLE: nothing is built there; HELD:
                the line that would carry it is held / its integration package is named), asserted against the lines
                of the run. A deduction found missing or doubled in a quantity line refuses the package (it is applied
                only by a record a merged checker verdict supports, never silently).

Refused (InputsError / ValueError, nothing written): an end reading CHORD / ARC_SPAN (or any reading) where drawn faces
close the end, or an end with no drawn closing face (then the line is HELD, its own record); a closing piece owned by
another line, or booked on two lines; a column overlapping the band and not deducted; a reconciliation that does not
close (drawn net != retired net + closing pieces - pieces the retired reading counted and the drawing excludes); a value
that is not net x depth; a before that is not the line's (stale ledger); a trace naming a line the run does not carry,
naming a quantity line twice for one opening and trade side, or an opening deducted in two quantity lines of one trade
side; a supply line whose pcs / m2 do not include the opening. Everything outside the records is byte-identical to
V3.0.18 (asserted), including the project identity block.

Files: V3_0_19_BOQ_LINES.json / .csv, V3_0_19_INTEGRATION_LEDGER.json / .csv, V3_0_19_OPENING_TRACE.json / .csv,
V3_0_19_DIFF.csv (every line against V3.0.18 and the released V2.9), V3_0_19_RUN.json. Nothing here names a project, a
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
from engine.source import arch_v3010 as A3010
from engine.source import arch_v3011 as A3011
from engine.source import arch_v3012 as A3012
from engine.source import arch_v3014 as A3014
from engine.source import arch_v3015 as A3015
from engine.source import arch_v3018 as A3018

DEFAULT_GUARD_CLASS = "TOOLING"          # T-212: brings named lines to a checker reading; adds no default value
METHOD = "ARCH_TAKEOFF_V3.0.19"
EXTENDS = A3018.METHOD
CANDIDATE = A30.METHOD
POLICY_ID = "URBAN_BOQ_T255_ARCH_V3_0_19"
INPUTS_SCHEMA = "URBAN_V3019_INPUTS_V1"
LEDGER_SCHEMA = "URBAN_V3019_INTEGRATION_LEDGER_V1"
TRACE_SCHEMA = "URBAN_V3019_OPENING_TRACE_V1"
ROLLBACK = A30.ROLLBACK
VER, DC, OA = A3018.VER, A3018.DC, A3018.OA
STATE_OF = A3018.STATE_OF
InputsError = A3015.InputsError
_num = A3015._num
_r = A3018._r
TOL = 1e-6
TOL_M2 = 1e-4            # reconciliation identities on plan areas quoted to 5 decimals
TOL_REL = 1e-5           # value vs net x depth
END_READINGS = ("DRAWN_FACES", "CHORD", "ARC_SPAN")
TRACE_STATES = ("CARRIED_ONCE", "NOT_APPLICABLE", "HELD", "NO_LINE")
TRADES = ("WINDOW_SUPPLY_PCS", "WINDOW_SUPPLY_M2", "WINDOW_REVEAL", "MASONRY", "PLASTER_ROOM_SIDE", "PAINT_ROOM_SIDE",
          "WALL_TILE_ROOM_SIDE", "EXTERNAL_FINISH")
REQUIRED_TRADES = ("WINDOW_SUPPLY_PCS", "WINDOW_SUPPLY_M2", "MASONRY")
RULE_END = ("R-ARC-BAND-END-1", "T-255")
RULE_TRACE = ("R-OPENING-ONCE-1", "T-255")

PIECES = {
    "END_CLOSURE_AND_OPENING_TRACE": {
        "module": "engine/source/arch_v3019.py (arc-band end closure by drawn faces; opening deduction trace)",
        "policy": "END_CLOSURE_V1", "rule_id": RULE_END[0], "rule_version": RULE_END[1],
        "trace_rule_id": RULE_TRACE[0], "trace_rule_version": RULE_TRACE[1],
        "owner_rules": ["UP-QTY-STATUS-001 (held never 0)", "WORKFLOW_CONTROLS 2026-10-21 s.4 / s.5",
                        "R-CONC-OWN-1 (one owner per piece)", "owner 2026-10-24 23:57 (2): UNSUPPORTED BASIS",
                        "Q-32 A (window m2 = width x height of the opening)",
                        "Q-38 A (curved window width = the printed width)", "build before deduct (ERS s.3)"],
        "owner_manual_method": "the owner measures a ground beam as plan area between its drawn faces x the printed "
                               "depth, columns deducted as their own trade; a window once in its supply line (pcs "
                               "and m2 by Q-32 A / Q-38 A) and its opening once from each wall face that is built "
                               "around it",
        "drawing_method": "the band polygon closed on the drawn faces that meet the arcs (adjoining beam face, column "
                          "faces), columns standing in the band deducted, x the printed depth; per opening and "
                          "trade the candidate line that carries it, read from the line's own calculation, or the "
                          "reason none does (nothing built there; the carrying line held)"},
}
WAITING = dict(A3018.WAITING)


# ================================================================================================ geometry (any villa)
def _poly(ring, where):
    from shapely.geometry import Polygon
    if not ring or len(ring) < 3:
        raise InputsError(f"{where}: not a valid closed outline (fewer than 3 points)")
    p = Polygon(ring)
    if not p.is_valid or p.area <= 0:
        raise InputsError(f"{where}: not a valid closed outline")
    return p


def check_end_reading(reading, closing_faces, where="end"):
    """an arc band end: DRAWN_FACES only, and only where drawn faces close it. A chord or arc-span reading is never an
    end; an end no drawn face closes is not established (the line is HELD, its own record)."""
    if reading not in END_READINGS:
        raise InputsError(f"{where}: end reading {reading!r} not one of {END_READINGS}")
    if not closing_faces:
        raise InputsError(f"{where}: no drawn face closes this end: the end is not established (HOLD the line; a chord "
                          "or an arc span is never an end)")
    if reading != "DRAWN_FACES":
        raise InputsError(f"{where}: {reading} reading refused: drawn faces {list(closing_faces)} close this end")


def arc_band_net(boundary, columns=(), neighbours=(), tol_m2=1e-6):
    """the net plan area (m2) of an arc band closed on its drawn faces.

    boundary    [(x, y), ...] metres: the band outline (arc parts as points, ends along the drawn closing faces)
    columns     [{id, ring, deducted}]: every column outline the drawing shows at the band; one overlapping the band
                and not deducted is refused (a column is its own trade)
    neighbours  [{line_id, ring}]: the plan outlines of the OTHER lines' members that meet the band; an overlap above
                tol_m2 is refused (a closing piece in two lines)
    -> {gross_m2, columns_m2 {id: m2}, net_m2}"""
    band = _poly(boundary, "arc band")
    cols = {}
    for c in columns:
        cp = _poly(c["ring"], f"column {c.get('id')}")
        ov = band.intersection(cp).area
        if ov <= tol_m2:
            continue
        if not c.get("deducted"):
            raise InputsError(f"column {c.get('id')} stands in the band ({ov:.6f} m2) and is not deducted (a column is "
                              "its own trade)")
        cols[c["id"]] = ov
    for n in neighbours:
        ov = band.intersection(_poly(n["ring"], f"neighbour {n.get('line_id')}")).area
        if ov > tol_m2:
            raise InputsError(f"the band overlaps {n.get('line_id')} by {ov:.6f} m2: a closing piece booked on two "
                              "lines (one owner per piece)")
    gross = band.area
    return {"gross_m2": gross, "columns_m2": cols, "net_m2": gross - sum(cols.values())}


# ================================================================================================ inputs
def _check_end_closure(r, where):
    A3018._check_before(r, where)
    A3018._check_status(r, where)
    ab = r.get("arc_band") or {}
    for side in ("end_a", "end_b"):
        e = ab.get(side) or {}
        check_end_reading(e.get("reading"), e.get("closing_faces"), f"{where} {side}")
    for k in ("drawn_net_m2", "retired_net_m2", "depth_m"):
        if not (_num(ab.get(k)) and ab[k] > 0):
            raise InputsError(f"{where}: arc_band.{k} > 0 required")
    if r.get("retired") is None or not r["retired"].get("reading"):
        raise InputsError(f"{where}: the reading the rebase retires is named (retired.reading / value)")
    add = 0.0
    for p in ab.get("closing_pieces") or ():
        if p.get("owned_by") != r["line_id"]:
            raise InputsError(f"{where}: closing piece {p.get('id')} owned by {p.get('owned_by')!r}, not this band's "
                              "line (one owner per piece)")
        if p.get("also_in"):
            raise InputsError(f"{where}: closing piece {p.get('id')} also in {p['also_in']} (double count)")
        if not (_num(p.get("m2")) and p["m2"] > 0):
            raise InputsError(f"{where}: closing piece {p.get('id')} m2 > 0")
        add += p["m2"]
    sub = 0.0
    for p in ab.get("excluded_pieces") or ():
        if not (_num(p.get("m2")) and p["m2"] > 0) or not p.get("why"):
            raise InputsError(f"{where}: an excluded piece names m2 > 0 and why")
        sub += p["m2"]
    for c in ab.get("columns_in_band") or ():
        if not c.get("deducted"):
            raise InputsError(f"{where}: column {c.get('id')} stands in the band and is not deducted (its own trade)")
    if abs(ab["retired_net_m2"] + add - sub - ab["drawn_net_m2"]) > TOL_M2:
        raise InputsError(f"{where}: reconciliation does not close: retired {ab['retired_net_m2']} + closing "
                          f"{_r(add)} - excluded {_r(sub)} != drawn {ab['drawn_net_m2']}")
    want = ab["drawn_net_m2"] * ab["depth_m"]
    if abs(r["value"] - want) > TOL_REL * max(1.0, want):
        raise InputsError(f"{where}: value {r['value']} is not drawn net {ab['drawn_net_m2']} x depth {ab['depth_m']} "
                          f"= {_r(want)}")
    ret = r["retired"].get("value")
    if ret is not None and abs(ret - r["before"]["measured_net"]) > TOL:
        raise InputsError(f"{where}: the retired value {ret} is not the line's before {r['before']['measured_net']}")
    if ret is not None:      # the carried value vs the retired reading re-measured: any residual is named, never hidden
        implied = ret / ab["depth_m"]
        res = ab.get("retired_residual") or {}
        if abs(implied - ab["retired_net_m2"]) > TOL_M2:
            if not (_num(res.get("m2")) and abs(res["m2"] - (implied - ab["retired_net_m2"])) <= 1e-5
                    and res.get("cause")):
                raise InputsError(f"{where}: the carried {ret} / D = {_r(implied)} m2 is not the retired reading "
                                  f"{ab['retired_net_m2']} m2: name the residual {_r(implied - ab['retired_net_m2'])} "
                                  "m2 and its cause (retired_residual)")
        elif res:
            raise InputsError(f"{where}: retired_residual named where the carried value is the retired reading")


def _check_entry(x, w):
    st = x.get("state")
    if st not in TRACE_STATES:
        raise InputsError(f"{w}: state {st!r} not one of {TRACE_STATES}")
    ids = x.get("line_ids") or []
    if len(ids) != len(set(ids)):
        raise InputsError(f"{w}: a line named twice")
    if st == "CARRIED_ONCE":
        if len(ids) != 1:
            raise InputsError(f"{w}: CARRIED_ONCE names exactly one quantity line ({len(ids)} named: an opening "
                              "deducted in two lines of one trade side is a double count; a split opening names its "
                              "parts)")
        if not x.get("evidence"):
            raise InputsError(f"{w}: CARRIED_ONCE names what in the line carries it")
    elif st == "NOT_APPLICABLE":
        if ids or not x.get("why"):
            raise InputsError(f"{w}: NOT_APPLICABLE names why (nothing built there) and no line")
    elif st == "HELD":
        if not x.get("held_item") or not x.get("named_task"):
            raise InputsError(f"{w}: HELD names its item and the package / task that carries it (never 0)")
    else:   # NO_LINE: a scope no candidate line carries for this opening: a finding, never a quantity
        if ids or not x.get("finding"):
            raise InputsError(f"{w}: NO_LINE names the finding (which scope has no line) and no line")
    if x.get("value") is not None and not (_num(x["value"]) and x["value"] > 0):
        raise InputsError(f"{w}: a traced value is > 0 (a missing value is HELD, never 0)")


def _check_trace(t, where):
    for k in ("opening", "floor", "physical_element", "kind"):
        if not t.get(k):
            raise InputsError(f"{where}: {k} required")
    trades = t.get("trades") or {}
    if set(trades) - set(TRADES):
        raise InputsError(f"{where}: trades {sorted(set(trades) - set(TRADES))} not in {TRADES}")
    if any(k not in trades for k in REQUIRED_TRADES):
        raise InputsError(f"{where}: an opening is traced at least in {REQUIRED_TRADES}")
    for tr, x in trades.items():
        w = f"{where} {tr}"
        parts = x.get("parts")
        if parts is None:
            _check_entry(x, w)
            continue
        names = [p.get("part") for p in parts]
        if len(parts) < 2 or not all(names) or len(set(names)) != len(names):
            raise InputsError(f"{w}: a split side names two or more parts, each once")
        lids = [lid for p in parts for lid in (p.get("line_ids") or ())]
        if len(lids) != len(set(lids)):
            raise InputsError(f"{w}: one line carries two parts of the opening (double count)")
        for p in parts:
            if p.get("value") is None:
                raise InputsError(f"{w} part {p['part']}: a part names its value")
            _check_entry(p, f"{w} part {p['part']}")
        if not _num(x.get("value")) or abs(sum(p["value"] for p in parts) - x["value"]) > TOL_M2:
            raise InputsError(f"{w}: the parts {_r(sum(p['value'] for p in parts))} do not close to the opening's "
                              f"{x.get('value')} on this side (a part missing or counted twice)")


def load_inputs(doc, project_id=None):
    """URBAN_V3019_INPUTS_V1 or None:
        {"schema", "project", "sources": [{file, sha256, task, merge_commit, checker_run}],
         "records": [{kind END_CLOSURE, line_id, item_code, element_id, task, physical_element,
                      before {evidence_state, measured_net}, status, value, pieces [{id, value, status}], verified_by,
                      formula, retired {reading, value},
                      arc_band {end_a / end_b {reading, closing_faces}, drawn_net_m2, retired_net_m2, depth_m,
                                closing_pieces [{id, m2, owned_by}], excluded_pieces [{id, m2, why}],
                                columns_in_band [{id, m2, deducted}]}}],
         "opening_trace": [{opening, floor, kind, physical_element, task,
                            trades {WINDOW_SUPPLY_PCS | WINDOW_SUPPLY_M2 | WINDOW_REVEAL | MASONRY | PLASTER_ROOM_SIDE |
                                    PAINT_ROOM_SIDE | WALL_TILE_ROOM_SIDE | EXTERNAL_FINISH:
                                    {state CARRIED_ONCE | NOT_APPLICABLE | HELD | NO_LINE, line_ids, evidence, token,
                                     deduction_text, value, value_field, why, held_item, named_task, finding,
                                     line_quantity_excludes_opening_area}
                                    or {value, parts [{part, <the same entry>}]} (an opening split between lines:
                                    the parts close to the side's value, one line per part)}}]}"""
    if doc is None:
        return None
    if doc.get("schema") != INPUTS_SCHEMA:
        raise InputsError(f"project inputs: schema must be {INPUTS_SCHEMA}")
    if project_id and doc.get("project") not in (None, project_id):
        raise InputsError(f"project inputs are for {doc.get('project')!r}, the run is {project_id!r}")
    srcs = doc.get("sources") or []
    if not srcs:
        raise InputsError("sources: the checker readings / merged ledgers the records come from")
    tasks = set()
    for s in srcs:
        A3018._source(s, "sources")
        tasks.add(s["task"])
    recs = doc.get("records") or []
    trace = doc.get("opening_trace") or []
    if not recs and not trace:
        raise InputsError("no records and no opening trace")
    seen, seen_pieces = set(), set()
    for r in recs:
        if r.get("kind") != "END_CLOSURE":
            raise InputsError(f"record kind {r.get('kind')!r}: V3.0.19 carries END_CLOSURE records only")
        lid = r.get("line_id")
        if not lid or lid in seen:
            raise InputsError(f"END_CLOSURE: line {lid!r} missing or named twice")
        seen.add(lid)
        for k in ("item_code", "element_id", "task", "physical_element"):
            if not r.get(k):
                raise InputsError(f"record {lid}: {k} required")
        if r["task"] not in tasks:
            raise InputsError(f"record {lid}: task {r['task']!r} is not one of the sources {sorted(tasks)}")
        A3018._check_pieces(r.get("pieces"), r.get("status"), r.get("value"), f"record {lid}", seen_pieces)
        _check_end_closure(r, f"record {lid}")
    ops = set()
    for t in trace:
        key = (t.get("opening"), t.get("floor"))
        if key in ops:
            raise InputsError(f"opening trace: {key} named twice")
        ops.add(key)
        if t.get("task") not in tasks:
            raise InputsError(f"opening trace {key}: task {t.get('task')!r} is not one of the sources")
        _check_trace(t, f"opening trace {key}")
    return doc


# ================================================================================================ lines
def end_closed_line(before, r, src):
    from engine.source import boq_line as BL
    ln = copy.deepcopy(before)
    st = r["status"]
    ab = r["arc_band"]
    ln["evidence_state"] = STATE_OF[st]
    ln["measured_net"] = _r(r["value"])
    ln["bounded_range"] = None
    ln["rfi"] = None
    ln["calculation"]["formula"] = (r.get("formula") or (
        f"net plan by drawn faces {ab['drawn_net_m2']} m2 x D {ab['depth_m']} = {_r(r['value'])} m3"))[:600]
    rec = {"policy": PIECES["END_CLOSURE_AND_OPENING_TRACE"]["policy"], "kind": "END_CLOSURE", "task": src["task"],
           "ledger": src["file"], "ledger_sha256": src["sha256"], "merge_commit": src["merge_commit"],
           "checker_run": src["checker_run"], "physical_element": r["physical_element"],
           "before": A3018._before_rec(before), "status": st, "evidence_status": st, "value": _r(r["value"]),
           "pieces": copy.deepcopy(r["pieces"]), "verified_by": r.get("verified_by"),
           "retired": copy.deepcopy(r["retired"]), "arc_band": copy.deepcopy(ab),
           "rule_id": RULE_END[0], "rule_version": RULE_END[1]}
    ln["calculation"]["inputs"] = dict(ln["calculation"].get("inputs") or {}, end_closure_v3019=rec)
    A305._note(ln, f"{METHOD}: arc band closed on its drawn faces ({src['task']} {src['merge_commit']}, "
                   f"{src['checker_run']}): {st}; retired {r['retired']['reading']}")
    return BL.validate(ln)


def _line_blob(ln):
    return json.dumps({"c": ln.get("calculation"), "n": ln.get("notes"), "p": ln.get("physical_element"),
                       "l": ln.get("location")}, sort_keys=True, default=str, ensure_ascii=False)


def _deductions(obj, text):
    """every {opening: ..., m2: ...} entry in a line record whose opening names `text`."""
    out = []
    if isinstance(obj, dict):
        if isinstance(obj.get("opening"), str) and text in obj["opening"] and _num(obj.get("m2")):
            out.append(obj["m2"])
        for v in obj.values():
            out += _deductions(v, text)
    elif isinstance(obj, list):
        for v in obj:
            out += _deductions(v, text)
    return out


def _trace_entry(x, w, opening, by):
    from engine.source import boq_line as BL
    for lid in x.get("line_ids") or ():
        ln = by.get(lid)
        if ln is None:
            raise InputsError(f"{w}: line {lid} is not a line of the run")
        q = ln["evidence_state"] in BL.QUANTITY_STATES and (ln.get("measured_net") or 0) > 0
        if x["state"] == "CARRIED_ONCE":
            if not q:
                raise InputsError(f"{w}: {lid} carries no quantity ({ln['evidence_state']}): the opening is then HELD "
                                  "with it, not CARRIED_ONCE")
            tok = x.get("token") or opening
            if tok not in _line_blob(ln):
                raise InputsError(f"{w}: {lid} does not name {tok} in its calculation (the trace reads the line's own "
                                  "record, never a ledger's word)")
        elif q and not x.get("line_quantity_excludes_opening_area"):
            raise InputsError(f"{w}: {lid} carries a quantity while the deduction is HELD: state whether the line's "
                              "quantity includes the opening area (line_quantity_excludes_opening_area)")
        if x.get("deduction_text"):
            got = _deductions(ln.get("calculation"), x["deduction_text"])
            if len(got) != 1:
                raise InputsError(f"{w}: {lid} names '{x['deduction_text']}' {len(got)} times (exactly once)")
            if x.get("value") is not None and abs(got[0] - x["value"]) > TOL_M2:
                raise InputsError(f"{w}: {lid} deducts {got[0]} for '{x['deduction_text']}', the trace {x['value']}")
        if x.get("value_field") and x.get("value") is not None:
            got = ((ln.get("calculation") or {}).get("inputs") or {})
            for k in x["value_field"]:
                got = got.get(k) if isinstance(got, dict) else None
            if not _num(got) or abs(got - x["value"]) > TOL_M2:
                raise InputsError(f"{w}: {lid} carries {got} at {x['value_field']}, the trace {x['value']}")


def trace_rows(doc, lines):
    """the opening trace asserted against the run's lines (no line changes). -> rows (one per opening, trade, part)."""
    if not doc:
        return []
    by = {ln["line_id"]: ln for ln in lines}
    rows = []
    for t in doc.get("opening_trace") or ():
        for tr in TRADES:
            x = (t["trades"] or {}).get(tr)
            if x is None:
                continue
            for p in (x.get("parts") or [x]):
                w = f"opening {t['opening']} {tr}" + (f" part {p['part']}" if p.get("part") else "")
                _trace_entry(p, w, t["opening"], by)
                rows.append({"opening": t["opening"], "floor": t["floor"], "kind": t["kind"], "trade": tr,
                             "part": p.get("part") or "", "state": p["state"],
                             "line_ids": list(p.get("line_ids") or ()),
                             "evidence": p.get("evidence") or p.get("why") or p.get("held_item") or p.get("finding"),
                             "named_task": p.get("named_task"), "value": p.get("value"), "unit": p.get("unit"),
                             "side_value": x.get("value") if x.get("parts") else None, "task": t["task"]})
    seen = {}       # one opening part, one quantity line per trade side
    for r in rows:
        if r["state"] != "CARRIED_ONCE":
            continue
        k = (r["opening"], r["floor"], r["trade"], r["part"])
        if k in seen:
            raise InputsError(f"opening {r['opening']} {r['trade']}: carried on {seen[k]} and {r['line_ids']}")
        seen[k] = r["line_ids"]
    return rows


TRACE_CSV = ("opening", "floor", "kind", "trade", "part", "state", "line_ids", "value", "unit", "side_value",
             "named_task", "evidence")


def changes_for(doc, l3018):
    """-> (changes, log, trace rows)."""
    if not doc:
        return [], {"piece": "END_CLOSURE_AND_OPENING_TRACE", "state": "NO_PROJECT_INPUT"}, []
    by = {ln["line_id"]: ln for ln in l3018}
    changes = []
    for r in doc.get("records") or ():
        src = A3018._src_of(doc, r["task"])
        b = by.get(r["line_id"])
        A3018._assert_before(b, r)
        for lid, ln in by.items():      # a closing piece another line books with a quantity is a double count
            if lid == r["line_id"]:
                continue
            blob = json.dumps(ln.get("calculation") or {}, sort_keys=True, default=str)
            for p in r["arc_band"].get("closing_pieces") or ():
                if p["id"] in blob:
                    raise InputsError(f"record {r['line_id']}: closing piece {p['id']} is also booked on {lid}")
        after = end_closed_line(b, r, src)
        ver = {"task": src["task"], "merge_commit": src["merge_commit"], "verifier_run": src["checker_run"],
               "ledger": src["file"], "ledger_sha256": src["sha256"], "record_verified_by": r.get("verified_by")}
        changes.append(A305._change("END_CLOSURE_AND_OPENING_TRACE", "REPLACE", b, after,
                                    drawing_reference=r.get("printed"), held=[],
                                    downstream=list(r.get("downstream") or ()), verification=ver,
                                    evidence_status=r["status"], codes=["END_CLOSURE", "REBASE"],
                                    group=r.get("group") or "END_CLOSURE"))
    trace = trace_rows(doc, l3018)
    log = {"piece": "END_CLOSURE_AND_OPENING_TRACE", "state": "RUN", "sources": doc["sources"],
           "records": len(changes), "trace_rows": len(trace),
           "trace_states": A302._count(t["state"] for t in trace)}
    return changes, log, trace


# ================================================================================================ integrate / write
def integrate(l3018, changes):
    """-> (V3.0.19 lines, identity). Every line outside the V3.0.19 rows is byte-identical to the V3.0.18 line."""
    from engine.source import boq_line as BL
    sid = {ln["line_id"] for ln in l3018}
    rep = {}
    for c in changes:
        if c["action"] != "REPLACE":
            raise ValueError(f"{METHOD}: action {c['action']} (V3.0.19 replaces lines in place only)")
        lid = c["before"]["line_id"]
        if lid in rep or lid not in sid or c["after"]["line_id"] != lid:
            raise ValueError(f"{METHOD}: line {lid}: changed twice, not in V3.0.18, or its id changed")
        rep[lid] = c["after"]
    out = [rep.get(ln["line_id"], ln) for ln in l3018]
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
    by18 = {ln["line_id"]: ln for ln in l3018}
    outside = [ln for ln in out if ln["line_id"] not in rep]
    bad = [ln["line_id"] for ln in outside if A30.line_sha(by18[ln["line_id"]]) != A30.line_sha(ln)]
    if bad or len(outside) + len(rep) != len(l3018):
        raise ValueError(f"{METHOD}: {len(bad)} line(s) outside the V3.0.19 rows differ from {EXTENDS}")
    for lid, ln in rep.items():   # inside a row only quantity, state, basis and notes change
        a, b = copy.deepcopy(by18[lid]), copy.deepcopy(ln)
        for x in (a, b):
            for k in ("evidence_state", "measured_net", "bounded_range", "rfi", "notes"):
                x.pop(k, None)
            x["calculation"] = None
        if json.dumps(a, sort_keys=True) != json.dumps(b, sort_keys=True):
            raise ValueError(f"{METHOD}: line {lid} changed outside quantity / state / basis")
    ident = {"v3_0_18_lines": len(l3018), "v3_0_19_lines": len(out), "v3_0_19_rows": len(changes),
             "replaced": len(rep), "added": 0, "outside_rows": len(outside),
             "outside_rows_identical_to_v3_0_18": len(outside),
             "outside_rows_sha256": hashlib.sha256("".join(A30.line_sha(x) for x in outside).encode()).hexdigest()}
    return out, ident


def ledger_rows(changes, released_lines=None):
    rel = {A30._key(ln): ln for ln in released_lines or ()}
    p = PIECES["END_CLOSURE_AND_OPENING_TRACE"]
    rows = []
    for c in changes:
        ref = c["before"]
        b29 = None
        if released_lines is not None:
            b29 = A30._qty(rel[A30._key(ref)]) if A30._key(ref) in rel else dict(A30._qty(None),
                                                                                 state="NOT_IN_RELEASED")
        rec = c["after"]["calculation"]["inputs"]["end_closure_v3019"]
        loc = c["after"].get("location") or {}
        rows.append({"version": METHOD, "piece": c["piece"], "action": c["action"], "kind": rec["kind"],
                     "line_id": c["after"]["line_id"], "item_code": c["after"]["item_code"], "floor": loc.get("floor"),
                     "element_id": loc.get("element_id"), "unit": c["after"]["unit"], "group": c.get("group"),
                     "before_released_v2_9": b29, "before_v3_0_18": A30._qty(c["before"]),
                     "after_v3_0_19": A30._qty(c["after"]), "evidence_status": c.get("evidence_status"),
                     "release_status": "NOT RELEASED", "pieces": rec.get("pieces") or [],
                     "arc_band": rec.get("arc_band"), "retired": rec.get("retired"),
                     "codes": c.get("codes") or [], "drawing_reference": c.get("drawing_reference"),
                     "owner_manual_method": p["owner_manual_method"], "drawing_method": p["drawing_method"],
                     "owner_rules": p["owner_rules"], "verification": dict(c.get("verification") or {},
                                                                            module=p["module"], policy=p["policy"]),
                     "held": c.get("held") or [], "downstream": c.get("downstream") or [], "rollback": ROLLBACK})
    return rows


LEDGER_CSV = ("version", "kind", "group", "line_id", "item_code", "floor", "element_id", "unit", "v2_9", "v3_0_18",
              "v3_0_19", "evidence_status", "release_status", "pieces", "verification")


def ledger_csv(rows):
    return A305._csv([{"version": r["version"], "kind": r["kind"], "group": r["group"], "line_id": r["line_id"],
                       "item_code": r["item_code"], "floor": r["floor"], "element_id": r["element_id"],
                       "unit": r["unit"], "v2_9": A302._q(r["before_released_v2_9"]),
                       "v3_0_18": A302._q(r["before_v3_0_18"]), "v3_0_19": A302._q(r["after_v3_0_19"]),
                       "evidence_status": r["evidence_status"], "release_status": r["release_status"],
                       "pieces": " + ".join(f"{p.get('id')} {_r(p.get('value'))}" for p in r["pieces"])[:400],
                       "verification": f"{r['verification'].get('task')} {r['verification'].get('merge_commit')} "
                                       f"{r['verification'].get('verifier_run')}"} for r in rows], LEDGER_CSV)


DIFF_CSV = ("line_id", "item_code", "floor", "element_id", "unit", "vs_v3_0_18", "vs_released_v2_9", "v2_9",
            "v3_0_18", "v3_0_19")


def diff_rows(l3018, l3019, released_lines=None):
    b18 = {ln["line_id"]: ln for ln in l3018}
    rel = {A30._key(ln): ln for ln in released_lines or ()}
    out = []
    for ln in l3019:
        o = b18.get(ln["line_id"])
        vs = "ADDED" if o is None else ("SAME" if A30.line_sha(o) == A30.line_sha(ln) else "CHANGED")
        r = rel.get(A30._key(ln)) if released_lines is not None else None
        vs29 = None if released_lines is None else ("NOT_IN_RELEASED" if r is None else
                                                    ("SAME_QUANTITY" if A30._qty(r) == A30._qty(ln) else
                                                     "QUANTITY_DIFFERS"))
        out.append({"line_id": ln["line_id"], "item_code": ln["item_code"], "floor": ln["location"].get("floor"),
                    "element_id": ln["location"].get("element_id"), "unit": ln["unit"], "vs_v3_0_18": vs,
                    "vs_released_v2_9": vs29, "v2_9": A302._q(A30._qty(r)) if r else "",
                    "v3_0_18": A302._q(A30._qty(o)) if o else "", "v3_0_19": A302._q(A30._qty(ln))})
    return out


def write(out, l3018, changes, log, trace, doc, released_lines=None):
    """the V3_0_19_* files beside the V3_0_18_* files. -> (file names, identity, ledger)."""
    from pathlib import Path
    from engine.source import boq_line as BL
    out = Path(out)
    l3019, ident = integrate(l3018, changes)
    rows = ledger_rows(changes, released_lines)
    diff = diff_rows(l3018, l3019, released_lines)
    dsum = {}
    for d in diff:
        dsum.setdefault("vs_v3_0_18", {}).setdefault(d["vs_v3_0_18"], 0)
        dsum["vs_v3_0_18"][d["vs_v3_0_18"]] += 1
        if d["vs_released_v2_9"] is not None:
            dsum.setdefault("vs_released_v2_9", {}).setdefault(d["vs_released_v2_9"], 0)
            dsum["vs_released_v2_9"][d["vs_released_v2_9"]] += 1
    ident = dict(ident, diff=dsum)
    t18, t19 = A304.code_totals(l3018), A304.code_totals(l3019)
    moved = {k: {"v3_0_18": t18.get(k), "v3_0_19": t19.get(k)} for k in sorted(set(t18) | set(t19))
             if t18.get(k) != t19.get(k)}
    led = {"schema": LEDGER_SCHEMA, "method": METHOD, "extends": EXTENDS, "candidate": CANDIDATE,
           "base": A30.BASE_METHOD, "released": A30.RELEASED_METHOD, "released_default": False, "rows": rows,
           "waiting_pieces": WAITING, "integration_package": True}
    tr = {"schema": TRACE_SCHEMA, "method": METHOD, "rule_id": RULE_TRACE[0], "rule_version": RULE_TRACE[1],
          "rows": trace, "changes_lines": False}
    run = {"method": METHOD, "policy": POLICY_ID, "extends": EXTENDS, "candidate": CANDIDATE,
           "base_method": A30.BASE_METHOD, "released_method": A30.RELEASED_METHOD, "released_default": False,
           "rollback": ROLLBACK, "identity": ident, "pieces": PIECES, "piece_log": log,
           "totals_moved_by_code": moved, "waiting_pieces": WAITING,
           "evidence_status_counts": A302._count(r["evidence_status"] for r in rows)}
    files = {"V3_0_19_BOQ_LINES.json": BL.dumps(l3019),
             "V3_0_19_BOQ_LINES.csv": A30._lines_csv(l3019),
             "V3_0_19_INTEGRATION_LEDGER.json": A30._j(led),
             "V3_0_19_INTEGRATION_LEDGER.csv": ledger_csv(rows),
             "V3_0_19_OPENING_TRACE.json": A30._j(tr),
             "V3_0_19_OPENING_TRACE.csv": A305._csv([dict(r, line_ids=" ".join(r["line_ids"])) for r in trace],
                                                    TRACE_CSV),
             "V3_0_19_DIFF.csv": A305._csv(diff, DIFF_CSV),
             "V3_0_19_RUN.json": A30._j(run)}
    for name, text in files.items():
        (out / name).write_text(text, encoding="utf-8")
    return sorted(files), ident, led


def policy_record():
    return {"method": METHOD, "extends": EXTENDS, "pieces": sorted(PIECES), "inputs_schema": INPUTS_SCHEMA,
            "released_default": False, "rollback": ROLLBACK}


__all__ = ["METHOD", "PIECES", "WAITING", "DEFAULT_GUARD_CLASS", "INPUTS_SCHEMA", "check_end_reading", "arc_band_net",
           "load_inputs", "end_closed_line", "trace_rows", "changes_for", "integrate", "ledger_rows", "diff_rows",
           "write", "InputsError"]
