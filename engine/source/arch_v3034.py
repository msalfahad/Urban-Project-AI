"""ARCH_TAKEOFF_V3.0.34 (T-399): the SAME opt-in BOQ candidate as ARCH_TAKEOFF_V3.0 .. V3.0.33 (engine.source.arch_v30,
arch_v301 .. arch_v3033), with ONE piece, TILE_ZONES: the BOQ family B4-02 'kitchen / laundry / pantry tiled zones'
integrated from the Checker-verified face table of T-351, room by room:

  ZONE_COVERED    the zone of a closed wet kitchen / laundry or an open pantry under the owner wet scope (UP-WET-001,
                  UP-FIN-WALL-001, Q-37 A, Q-48 A) IS the full-height wall tile of that room: every zone face is
                  already one face of the room's ONE FIN.WALL.TILE line (B4-01). No B4-02 line is added (a band on a
                  wall-tile face counts the same tile twice, R-T351-2): the zone is bound to that carrier line by
                  room id, and the run asserts it (carrier present in the state and figure the verified table read,
                  held carrier stays BLANK; a named residual between the table and the line is reported, never
                  netted; no valued plaster line on the room but the tile backing; no valued paint line on the room).
                  Record only: it changes no line.
  ZONE_PAINT_NA   a paint line of a zone room that is still BLOCKED_RFI although the zone covers every one of its
                  faces to the coat top (band above the tile 0 by the owner height, Q-43 = Q-48 A): the paint under
                  the zone is reduced by exactly the zone, i.e. to nothing, so the line becomes
                  NOT_APPLICABLE_WITH_EVIDENCE (UP-FIN-PAINT-001: no paint on a tiled face; the same state the
                  'paint above wall tile' lines of the other wet rooms carry). Its old hold reason is named; no
                  quantity appears, none disappears (the line was blank).

Every value comes from the inputs (the Checker-merged T-351 ledgers pinned by sha256); this module types none. Every
line outside the rows is byte-identical to V3.0.33; inside a row only state, quantity (none), range, rfi, calculation
and notes change (asserted). No total of a valued quantity may move (asserted). Files: V3_0_34_BOQ_LINES.json / .csv,
V3_0_34_INTEGRATION_LEDGER.json / .csv, V3_0_34_DIFF.csv, V3_0_34_RUN.json. Nothing here names a project, a sheet, a
layer or a coordinate.

R-T399-1 (every villa): a 'missing' finish family whose physical layer an owner rule already gives to another family
is integrated as a COVERAGE binding by room / face id to that family's line, never as a second quantity; the binding
stops when the carrier line is absent, in another state or at another figure than the verified table read (stale), or
when the table and the line differ by more than the named residual; a held carrier stays blank; the paint and plaster
of the zone faces are reduced by exactly the zone: paint to NOT_APPLICABLE_WITH_EVIDENCE only when the zone reaches
the coat top on every face of that paint line, plaster only through the tile-backing line (never an ordinary plaster
line on a zone face).
"""

from __future__ import annotations

import copy
import hashlib
import json

from engine.source import arch_v30 as A30
from engine.source import arch_v302 as A302
from engine.source import arch_v304 as A304
from engine.source import arch_v305 as A305
from engine.source import arch_v3018 as A3018
from engine.source import arch_v3030 as A3030
from engine.source import arch_v3031 as A3031
from engine.source import arch_v3032 as A3032
from engine.source import arch_v3033 as A3033

DEFAULT_GUARD_CLASS = "TOOLING"          # T-212: re-books checker-merged ledgers; adds no default value
METHOD = "ARCH_TAKEOFF_V3.0.34"
EXTENDS = A3033.METHOD
CANDIDATE = A30.METHOD
POLICY_ID = "URBAN_BOQ_T399_ARCH_V3_0_34"
INPUTS_SCHEMA = "URBAN_V3034_INPUTS_V1"
LEDGER_SCHEMA = "URBAN_V3034_INTEGRATION_LEDGER_V1"
ROLLBACK = A30.ROLLBACK
InputsError = A3031.InputsError
_r = A3018._r
_fmt = A3030._fmt
RULE_ID, RULE_VERSION = "R-T399-1", "T-399"
PIECE = "TILE_ZONES"
FAMILY = "B4-02"
CARRIER_FAMILY = "B4-01"
REC_KEY = "tile_zones_v3034"
ACTIONS = ("ZONE_COVERED", "ZONE_PAINT_NA")
TILE = "FIN.WALL.TILE"
PLASTER = "FIN.PLASTER"
PAINT = "FIN.PAINT"
NA = "NOT_APPLICABLE_WITH_EVIDENCE"
VALUED_STATES = ("MEASURED", "SOURCE_DERIVED", "PROVISIONAL")
ZONE_CODES = ("KITCHEN", "LAUNDRY", "PANTRY")
ZONE_KINDS = ("FULL_HEIGHT", "HOST_FULL_WALL")   # closed wet room / open-pantry host walls; a printed band is a
#                                                    real B4-02 line of its own (not reached on this villa)
TOL = 1e-6
RESIDUAL_MAX = 0.01                      # a table-vs-line residual above 1 % of the line is a Gate A matter, not lane I
ROW_KEYS = ("evidence_state", "measured_net", "bounded_range", "rfi", "notes", "calculation", "gross")

PIECES = {
    PIECE: {
        "module": "engine/source/arch_v3034.py (B4-02 kitchen / laundry / pantry tiled zones from the Checker-"
                  "verified T-351 face table: each zone bound to its room's FIN.WALL.TILE carrier line, no second "
                  "quantity; the paint of a zone room reduced by exactly the zone)",
        "policy": "TILE_ZONES_V1", "rule_id": RULE_ID, "rule_version": RULE_VERSION,
        "owner_rules": ["UP-WET-001 1.1.0 (wet codes KITCHEN / PANTRY / LAUNDRY: full-height wall porcelain, paint "
                        "none)", "UP-FIN-WALL-001 1.8.0 (locations include KITCHEN / PANTRY / LAUNDRY)",
                        "Q-48 A (tile height floor-to-floor - 0.60 - 0.15 - 0.10)", "Q-43 (plaster top = tile top)",
                        "Q-37 A (pantry wet)", "Q-30 A (kitchen waterproofed like a bathroom)",
                        "UP-PANTRY-001 .. 004 (open pantry: host walls whole, open edge nothing)",
                        "UP-FIN-PAINT-001 (no paint on a tiled face; the substrate under tile is the backing)",
                        "UP-QTY-STATUS-001 (held is blank, never 0)",
                        "R-T351-1 .. 5 (band only from a print; zone = wall tile; held blank; opening once; no paint "
                        "under a zone)", "WORKFLOW_CONTROLS 2026-10-21 s.4 / s.5; ERS 2026-10-22 s.2 - s.4"],
        "owner_manual_method": "owner wet scope: the zone of a closed kitchen / laundry and of an open pantry's host "
                               "walls is the full-height wall tile, every face, floor to the Q-48 A tile top, "
                               "openings inside the band deducted once; no paint under it, the plaster there is the "
                               "tile backing (its own line); a room whose owner height is not established stays "
                               "HELD (blank)",
        "drawing_method": "a splashback band behind the drawn counter / sink runs (layer 5 outlines; T-351 "
                          "DRAWING_DERIVED_T351.csv): no sheet prints a band, so it is HELD TILE_BAND_NOT_PRINTED on "
                          "every room and never fills a blank"},
}
WAITING = dict(A3033.WAITING)
WAITING.update({
    "B4_02_PRINTED_BAND": "a villa whose drawings print a kitchen band, or whose kitchen opens onto a dry open plan "
                          "(UP-WET-001 precondition fails): a real B4-02 band line (R-T351-1 / -3); not reached on "
                          "the development villa (no band printed, every zone room wet)",
    "PANTRY_FACE_REWALK_F_T351_1": "pantry tiled faces 10.500 m own vector reading (T-351, Checker re-measured) vs "
                                   "the per-face walk 10.491 m of the tile / backing lines (+0.0328 m2, +0.10 %): "
                                   "named residual, not applied; needs a face-by-face re-walk binding the six walk "
                                   "pieces to the drawn handles before a line moves",
    "KITCHEN_ANNEX_HEIGHT_G2": "kitchen GF-06 zone HELD with its carrier and backing lines (annex owner height, "
                               "G2 / Q-54 B, D-39)",
})


# ================================================================================================ inputs
def _need(s, keys, where):
    for k in keys:
        if s.get(k) in (None, ""):
            raise InputsError(f"{where}: {k} missing")


def _num(x, where, zero_ok=False):
    if not isinstance(x, (int, float)) or isinstance(x, bool) or x != x or x < 0 or (x == 0 and not zero_ok):
        raise InputsError(f"{where}: {x!r} is not a positive figure (held is BLANK, never 0)")
    return float(x)


def load_inputs(doc, project_id=None):
    """URBAN_V3034_INPUTS_V1 -> the validated doc. {"schema", "project_id", "sources": [{"task", "file", "sha256",
    "merge_commit", "checker_run"}], "zones": [{"room", "code", "engine_room", "floor", "zone", "faces",
    "carrier_line", "carrier_expect": {"evidence_state", "measured_net" | None}, "table_net_m2" | None, "held_item"
    (when the table is HELD), "residual": {"m2", "cause"} (when table and line differ), "backing_line",
    "band_above_tile_m2", "source_tasks"}], "rows": [{"action": "ZONE_PAINT_NA", "line_id", "room", "expect":
    {"item_code", "floor", "room_id", "element_id", "evidence_state"}, "cause", "old_hold", "evidence_status",
    "source_tasks"}]}"""
    if not doc:
        return None
    if doc.get("schema") != INPUTS_SCHEMA:
        raise InputsError(f"project inputs: schema must be {INPUTS_SCHEMA}")
    if project_id and doc.get("project_id") not in (None, project_id):
        raise InputsError(f"project inputs are for {doc.get('project_id')!r}, the run is {project_id!r}")
    srcs = {}
    for s in doc.get("sources") or ():
        _need(s, ("task", "file", "sha256", "merge_commit", "checker_run"), f"source {s.get('task')}")
        srcs[s["task"]] = s
    zones, seen_room, seen_line = {}, set(), set()
    for i, z in enumerate(doc.get("zones") or ()):
        where = f"zone {i} {z.get('room')}"
        _need(z, ("room", "code", "engine_room", "floor", "zone", "carrier_line", "backing_line"), where)
        if z["code"] not in ZONE_CODES:
            raise InputsError(f"{where}: code {z['code']!r} is not a kitchen / laundry / pantry zone")
        if z["zone"] not in ZONE_KINDS:
            raise InputsError(f"{where}: zone kind {z['zone']!r}: a printed band is a B4-02 line of its own, not a "
                              f"coverage binding (R-T351-1)")
        if not z.get("source_tasks") or any(t not in srcs for t in z["source_tasks"]):
            raise InputsError(f"{where}: no merged source named")
        if not isinstance(z.get("faces"), int) or z["faces"] <= 0:
            raise InputsError(f"{where}: faces must be the count of the verified zone faces")
        e = z.get("carrier_expect") or {}
        _need(e, ("evidence_state",), f"{where} carrier_expect")
        tn = z.get("table_net_m2")
        if tn is None:
            _need(z, ("held_item",), where)
            if e["evidence_state"] in VALUED_STATES or e.get("measured_net") is not None:
                raise InputsError(f"{where}: the verified table holds the zone; its carrier cannot be valued")
            if z.get("residual"):
                raise InputsError(f"{where}: a held zone has no residual")
        else:
            tn = _num(tn, f"{where} table_net_m2")
            if e["evidence_state"] not in VALUED_STATES:
                raise InputsError(f"{where}: the table values the zone ({tn} m2) but the carrier is "
                                  f"{e['evidence_state']} (re-bind)")
            ln = _num(e.get("measured_net"), f"{where} carrier measured_net")
            d = tn - ln
            res = z.get("residual")
            if abs(d) > 5e-5:
                if not res:
                    raise InputsError(f"{where}: table {tn} vs line {ln} differ by {_r(d)} m2 with no named residual "
                                      f"(never netted silently)")
                _need(res, ("cause",), f"{where} residual")
                if abs(res.get("m2", 0) - d) > 5e-5:
                    raise InputsError(f"{where}: residual {res.get('m2')} is not table - line {_r(d)}")
                if abs(d) > RESIDUAL_MAX * ln:
                    raise InputsError(f"{where}: residual {_r(d)} m2 is above {RESIDUAL_MAX:.0%} of the line: a "
                                      f"material discrepancy goes to Gate A, not to a coverage binding")
            elif res:
                raise InputsError(f"{where}: a residual is named but table and line agree")
        if _num(z.get("band_above_tile_m2", -1), f"{where} band_above_tile_m2", zero_ok=True) != 0:
            raise InputsError(f"{where}: a band above the tile is paint / plaster scope: not a full-height zone")
        if z["engine_room"] in seen_room or z["carrier_line"] in seen_line:
            raise InputsError(f"{where}: room or carrier line in two zones (one face, one owner)")
        seen_room.add(z["engine_room"])
        seen_line.add(z["carrier_line"])
        zones[z["engine_room"]] = z
    if not zones:
        raise InputsError("no zone in the inputs")
    rows, seen = [], set()
    for i, r in enumerate(doc.get("rows") or ()):
        act = r.get("action")
        where = f"row {i} {act} {r.get('line_id')}"
        if act != "ZONE_PAINT_NA":
            raise InputsError(f"{where}: action {act!r} (ZONE_COVERED is derived from the zones, never a row)")
        _need(r, ("line_id", "room", "cause", "old_hold", "evidence_status"), where)
        if not r.get("source_tasks") or any(t not in srcs for t in r["source_tasks"]):
            raise InputsError(f"{where}: no merged source named")
        e = r.get("expect") or {}
        _need(e, ("item_code", "floor", "room_id", "evidence_state"), f"{where} expect")
        if e["item_code"] != PAINT:
            raise InputsError(f"{where}: {e['item_code']} is not a paint line (plaster under a zone is the backing "
                              f"line, never cancelled)")
        if e["room_id"] not in zones:
            raise InputsError(f"{where}: room {e['room_id']} is not a verified zone room")
        if e["evidence_state"] in VALUED_STATES:
            raise InputsError(f"{where}: a valued paint line is a double count to investigate, not a state change")
        if r["line_id"] in seen:
            raise InputsError(f"{where}: line in two rows (one line, one row)")
        seen.add(r["line_id"])
        rows.append(r)
    return dict(doc, _sources=srcs, _zones=zones, _rows=rows)


# ================================================================================================ lines
def _rec(srcs, **kw):
    return dict({"policy": PIECES[PIECE]["policy"], "family": FAMILY, "tasks": [s["task"] for s in srcs],
                 "ledgers": [s["file"] for s in srcs], "ledger_sha256": [s["sha256"] for s in srcs],
                 "merge_commits": [s["merge_commit"] for s in srcs], "checker_runs": [s["checker_run"] for s in srcs],
                 "rule_id": RULE_ID, "rule_version": RULE_VERSION, "release_status": "NOT RELEASED"}, **kw)


def _ver(srcs):
    return {"task": "+".join(s["task"] for s in srcs), "merge_commit": srcs[0]["merge_commit"],
            "merge_commits": [s["merge_commit"] for s in srcs],
            "verifier_run": "; ".join(s["checker_run"] for s in srcs), "ledger": "; ".join(s["file"] for s in srcs)}


def _room(ln):
    return (ln.get("location") or {}).get("room_id")


def zone_check(doc, lines):
    """ZONE_COVERED, on the lines given (V3.0.33 or V3.0.34): every verified zone stands on its carrier exactly as the
    table read; nothing else on the room's faces carries tile, valued paint or ordinary plaster. -> rows (records)."""
    if not doc:
        return []
    by = {ln["line_id"]: ln for ln in lines}
    if any(ln["item_code"].startswith(TILE.rsplit(".", 1)[0] + ".") and ln["item_code"] != TILE for ln in lines):
        raise ValueError(f"{METHOD}: a B4-02 line exists in the candidate (a zone on a wall-tile face is a double "
                         f"count, R-T351-2)")
    out = []
    S = doc["_sources"]
    for rid, z in sorted(doc["_zones"].items()):
        c = by.get(z["carrier_line"])
        e = z["carrier_expect"]
        if c is None or c["item_code"] != TILE or c["unit"] != "m2" or _room(c) != rid or \
                c["evidence_state"] != e["evidence_state"]:
            raise ValueError(f"{METHOD}: zone {z['room']}: carrier {z['carrier_line']} is not the {TILE} line of "
                             f"{rid} in state {e['evidence_state']} (stale binding)")
        if e.get("measured_net") is None:
            if c.get("measured_net") is not None or c.get("bounded_range"):
                raise ValueError(f"{METHOD}: zone {z['room']}: held carrier carries a figure (held is BLANK)")
        elif c.get("measured_net") is None or abs(c["measured_net"] - e["measured_net"]) > TOL:
            raise ValueError(f"{METHOD}: zone {z['room']}: carrier {c.get('measured_net')} is not the bound "
                             f"{e['measured_net']} (stale binding)")
        tiles = [ln["line_id"] for ln in lines if ln["item_code"] == TILE and _room(ln) == rid]
        if tiles != [z["carrier_line"]]:
            raise ValueError(f"{METHOD}: zone {z['room']}: tile lines {tiles} (one room, one carrier)")
        b = by.get(z["backing_line"])
        if b is None or b["item_code"] != PLASTER or _room(b) != rid or \
                (b["evidence_state"] in VALUED_STATES) != (c["evidence_state"] in VALUED_STATES) or \
                (b.get("measured_net") is not None and abs(b["measured_net"] - c["measured_net"]) > TOL):
            raise ValueError(f"{METHOD}: zone {z['room']}: backing {z['backing_line']} is not the tile backing of "
                             f"its carrier (same faces, same figure, same held / valued)")
        plaster = [ln["line_id"] for ln in lines if ln["item_code"] == PLASTER and _room(ln) == rid and
                   ln["evidence_state"] in VALUED_STATES and ln["line_id"] != z["backing_line"]]
        paint = [ln["line_id"] for ln in lines if ln["item_code"] == PAINT and _room(ln) == rid and
                 ln["evidence_state"] in VALUED_STATES]
        if plaster or paint:
            raise ValueError(f"{METHOD}: zone {z['room']}: valued plaster {plaster} / paint {paint} on zone faces "
                             f"(the zone reduces them to the backing and to nothing)")
        paint_lines = sorted((ln["line_id"], ln["evidence_state"]) for ln in lines if ln["item_code"] == PAINT and
                             _room(ln) == rid)
        srcs = [S[t] for t in z["source_tasks"]]
        q = c.get("measured_net")
        out.append({"version": METHOD, "piece": PIECE, "action": "ZONE_COVERED", "family": FAMILY,
                    "covered_by": CARRIER_FAMILY, "room": z["room"], "code": z["code"], "engine_room": rid,
                    "floor": z["floor"], "faces": z["faces"], "zone": z["zone"], "carrier_line": c["line_id"],
                    "carrier_state": c["evidence_state"], "zone_m2_on_carrier": q,
                    "table_net_m2": z.get("table_net_m2"), "residual": z.get("residual"),
                    "held_item": z.get("held_item"), "backing_line": b["line_id"],
                    "backing_m2": b.get("measured_net"), "paint_lines": paint_lines, "b4_02_lines_added": 0,
                    "double_count_m2": 0.0, "evidence_status": ("HELD" if q is None else
                                                                "ASSUMED — OWNER-APPROVED"),
                    "verification": _ver(srcs), "release_status": "NOT RELEASED"})
    return out


def changes_for(doc, l3033):
    """-> (changes, log)."""
    if not doc:
        return [], {"piece": PIECE, "state": "NO_PROJECT_INPUT"}
    if any(((ln.get("calculation") or {}).get("inputs") or {}).get(REC_KEY) for ln in l3033):
        raise InputsError("the candidate already carries the V3.0.34 tile-zone rows (applied once)")
    by = {ln["line_id"]: ln for ln in l3033}
    zrows = zone_check(doc, l3033)
    S = doc["_sources"]
    log = {"piece": PIECE, "state": "RUN", "sources": doc["sources"], "zones": len(zrows),
           "zones_valued": sum(1 for z in zrows if z["zone_m2_on_carrier"] is not None),
           "zone_m2_on_carriers": _r(sum(z["zone_m2_on_carrier"] or 0 for z in zrows)),
           "b4_02_lines_added": 0, "by_action": {"ZONE_COVERED": len(zrows)}, "lines_restated": 0}
    changes = []
    for r in doc["_rows"]:
        b = by.get(r["line_id"])
        e = r["expect"]
        z = doc["_zones"][e["room_id"]]
        if b is None or b["item_code"] != e["item_code"] or _room(b) != e["room_id"] or \
                (b.get("location") or {}).get("floor") != e["floor"] or b["evidence_state"] != e["evidence_state"] \
                or (e.get("element_id") and (b.get("location") or {}).get("element_id") != e["element_id"]):
            raise InputsError(f"line {r['line_id']}: not in the candidate as bound {e} (stale binding)")
        if b.get("measured_net") is not None or b.get("bounded_range"):
            raise InputsError(f"line {r['line_id']}: carries a figure; a paint line under a zone is reduced only "
                              f"when it is blank (a valued one is a double count to investigate)")
        srcs = [S[t] for t in r["source_tasks"]]
        rec = _rec(srcs, action="ZONE_PAINT_NA", evidence_status=r["evidence_status"],
                   before=A3018._before_rec(b), cause=r["cause"], old_hold=r["old_hold"], room=z["room"],
                   carrier_line=z["carrier_line"], backing_line=z["backing_line"], zone_faces=z["faces"])
        formula = (f"NOT APPLICABLE (no paint under a full-height tile zone): every face of {z['room']} is tiled "
                   f"to the coat top by {z['carrier_line']} ({z['faces']} drawn faces, T-351; band above the tile 0 by "
                   f"Q-43 = Q-48 A); the paint under the zone is reduced by exactly the zone ({r['cause']}); was held: "
                   f"{r['old_hold']}")
        ln = copy.deepcopy(b)
        ln.update(evidence_state=NA, measured_net=None, gross=None, bounded_range=None, rfi=None)
        ln["calculation"] = dict(ln.get("calculation") or {}, formula=formula[:700],
                                 inputs=dict((ln.get("calculation") or {}).get("inputs") or {}, **{REC_KEY: rec}))
        A305._note(ln, f"{METHOD}: no paint under the {FAMILY} zone ({'+'.join(r['source_tasks'])}): "
                       f"UP-FIN-PAINT-001 / UP-WET-001 paint none; NOT RELEASED")
        from engine.source import boq_line as BL
        after = BL.validate(ln)
        changes.append(A305._change(PIECE, "REPLACE", b, after, drawing_reference="; ".join(s["file"] for s in srcs),
                                    held=[], downstream=[], verification=_ver(srcs),
                                    evidence_status=r["evidence_status"], codes=[PIECE, "ZONE_PAINT_NA"],
                                    group=after["item_code"]))
        log["by_action"]["ZONE_PAINT_NA"] = log["by_action"].get("ZONE_PAINT_NA", 0) + 1
        log["lines_restated"] += 1
    log["zone_rows"] = zrows
    return changes, log


# ================================================================================================ integrate / write
def check_zones(lines):
    """on finished lines: every V3.0.34 record line is a blank NOT_APPLICABLE paint line of a zone room. -> summary."""
    out = {"ZONE_PAINT_NA": 0}
    for ln in lines:
        rec = ((ln.get("calculation") or {}).get("inputs") or {}).get(REC_KEY)
        if not rec:
            continue
        if rec["action"] != "ZONE_PAINT_NA" or ln["item_code"] != PAINT or ln["evidence_state"] != NA or \
                ln.get("measured_net") is not None or ln.get("gross") is not None or ln.get("bounded_range"):
            raise ValueError(f"{METHOD}: {ln['line_id']} is not a blank NOT_APPLICABLE paint line of a zone room")
        out["ZONE_PAINT_NA"] += 1
    return out


def integrate(l3033, changes, for_lead=(), doc=None):
    """-> (V3.0.34 lines, identity). Every line outside the rows is byte-identical to V3.0.33."""
    sid = {ln["line_id"] for ln in l3033}
    rep = {}
    for c in changes:
        if c["piece"] != PIECE or c["action"] != "REPLACE":
            raise ValueError(f"{METHOD}: {c['piece']} {c['action']} (this version only restates tile-zone paint)")
        lid = c["before"]["line_id"]
        if lid in rep or lid not in sid or c["after"]["line_id"] != lid or c["after"]["item_code"] != PAINT or \
                c["before"]["item_code"] != PAINT:
            raise ValueError(f"{METHOD}: line {lid}: changed twice, not in V3.0.33, its id / item changed or not "
                             f"paint")
        rep[lid] = c["after"]
    out = [rep.get(ln["line_id"], ln) for ln in l3033]
    if len({ln["line_id"] for ln in out}) != len(out):
        raise ValueError(f"{METHOD}: a BOQ line id appears twice")
    guards = A3031._family_guards(out, for_lead)   # every family guard up to V3.0.30
    roof = A3031.check_roof_layers(out)
    ceil = A3032.check_ceilings(out)
    corr = A3033.check_corrections(out)
    zones = check_zones(out)
    zrows = zone_check(doc, out) if doc else []
    pids = {(ln["project"]["project_id"], ln["project"]["revision_set_sha256"]) for ln in out}
    if len(pids) != 1:
        raise ValueError(f"{METHOD}: {len(pids)} project identities in the lines (one project, one revision set)")
    by33 = {ln["line_id"]: ln for ln in l3033}
    outside = [ln for ln in out if ln["line_id"] not in rep]
    bad = [ln["line_id"] for ln in outside if A30.line_sha(by33[ln["line_id"]]) != A30.line_sha(ln)]
    if bad or len(outside) + len(rep) != len(l3033):
        raise ValueError(f"{METHOD}: {len(bad)} line(s) outside the V3.0.34 rows differ from {EXTENDS}")
    for lid, ln in rep.items():   # inside a row only state, range, rfi, calculation and notes change
        a, b = copy.deepcopy(by33[lid]), copy.deepcopy(ln)
        for x in (a, b):
            for k in ROW_KEYS:
                x.pop(k, None)
        if json.dumps(a, sort_keys=True) != json.dumps(b, sort_keys=True):
            raise ValueError(f"{METHOD}: line {lid} changed outside state / range / text")
    ident = {"v3_0_33_lines": len(l3033), "v3_0_34_lines": len(out), "v3_0_34_rows": len(changes),
             "replaced": len(rep), "added": 0, "outside_rows": len(outside),
             "outside_rows_identical_to_v3_0_33": len(outside), "tile_zones": zones,
             "zones_covered": len(zrows), "corrections": corr, "ceilings": ceil, "roof_buildup": roof,
             "guards": guards,
             "outside_rows_sha256": hashlib.sha256("".join(A30.line_sha(x) for x in outside).encode()).hexdigest()}
    return out, ident


def ledger_rows(changes, zrows, released_lines=None):
    rel = {A30._key(ln): ln for ln in released_lines or ()}
    rows = [dict(z, owner_manual_method=PIECES[PIECE]["owner_manual_method"],
                 drawing_derived_method=PIECES[PIECE]["drawing_method"], rollback=ROLLBACK) for z in zrows]
    for c in changes:
        ref = c["after"]
        rec = ref["calculation"]["inputs"][REC_KEY]
        b29 = None
        if released_lines is not None:
            b29 = A30._qty(rel[A30._key(ref)]) if A30._key(ref) in rel else dict(A30._qty(None),
                                                                                 state="NOT_IN_RELEASED")
        loc = ref.get("location") or {}
        rows.append({"version": METHOD, "piece": PIECE, "action": "ZONE_PAINT_NA", "family": FAMILY,
                     "line_id": ref["line_id"], "item_code": ref["item_code"], "floor": loc.get("floor"),
                     "engine_room": loc.get("room_id"), "element_id": loc.get("element_id"), "unit": ref["unit"],
                     "room": rec.get("room"), "carrier_line": rec.get("carrier_line"),
                     "before_released_v2_9": b29, "before_v3_0_33": A30._qty(c["before"]),
                     "after_v3_0_34": A30._qty(ref), "evidence_status": c.get("evidence_status"),
                     "cause": rec.get("cause"), "old_hold": rec.get("old_hold"), "release_status": "NOT RELEASED",
                     "owner_manual_method": PIECES[PIECE]["owner_manual_method"],
                     "drawing_derived_method": PIECES[PIECE]["drawing_method"],
                     "verification": c.get("verification") or {}, "rollback": ROLLBACK})
    return rows


LEDGER_CSV = ("version", "action", "family", "room", "engine_room", "floor", "line_id", "carrier_line",
              "backing_line", "faces", "zone_m2_on_carrier", "table_net_m2", "residual_m2", "v2_9", "v3_0_33",
              "v3_0_34", "evidence_status", "cause", "verification")
DIFF_CSV = ("line_id", "item_code", "floor", "element_id", "unit", "vs_v3_0_33", "vs_released_v2_9", "v2_9",
            "v3_0_33", "v3_0_34")


def ledger_csv(rows):
    def q(x):
        return A302._q(x) if x else ""
    return A305._csv([{"version": r["version"], "action": r["action"], "family": r["family"], "room": r.get("room"),
                       "engine_room": r.get("engine_room"), "floor": r.get("floor") or "",
                       "line_id": r.get("line_id") or "", "carrier_line": r.get("carrier_line"),
                       "backing_line": r.get("backing_line") or "", "faces": r.get("faces") or "",
                       "zone_m2_on_carrier": ("" if r.get("zone_m2_on_carrier") is None else
                                              _fmt(r["zone_m2_on_carrier"])) if r["action"] == "ZONE_COVERED" else "",
                       "table_net_m2": "" if r.get("table_net_m2") is None else _fmt(r["table_net_m2"]),
                       "residual_m2": "" if not r.get("residual") else _fmt(r["residual"]["m2"]),
                       "v2_9": q(r.get("before_released_v2_9")), "v3_0_33": q(r.get("before_v3_0_33")),
                       "v3_0_34": q(r.get("after_v3_0_34")), "evidence_status": r["evidence_status"],
                       "cause": (r.get("cause") or (r.get("residual") or {}).get("cause") or r.get("held_item") or
                                 "")[:400],
                       "verification": f"{r['verification'].get('task')} "
                                       f"{' '.join(x[:8] for x in r['verification'].get('merge_commits') or ())}"
                       } for r in rows], LEDGER_CSV)


def diff_rows(l3033, l3034, released_lines=None):
    b33 = {ln["line_id"]: ln for ln in l3033}
    rel = {A30._key(ln): ln for ln in released_lines or ()}
    out = []
    for ln in l3034:
        o = b33.get(ln["line_id"])
        vs = "ADDED" if o is None else ("SAME" if A30.line_sha(o) == A30.line_sha(ln) else
                                        ("CHANGED" if (A30._qty(o) != A30._qty(ln) or
                                                       o.get("bounded_range") != ln.get("bounded_range"))
                                         else "CHANGED_TEXT_ONLY"))
        r = rel.get(A30._key(ln)) if released_lines is not None else None
        vs29 = None if released_lines is None else ("NOT_IN_RELEASED" if r is None else
                                                    ("SAME_QUANTITY" if A30._qty(r) == A30._qty(ln) else
                                                     "QUANTITY_DIFFERS"))
        out.append({"line_id": ln["line_id"], "item_code": ln["item_code"], "floor": ln["location"].get("floor"),
                    "element_id": ln["location"].get("element_id"), "unit": ln["unit"], "vs_v3_0_33": vs,
                    "vs_released_v2_9": vs29, "v2_9": A302._q(A30._qty(r)) if r else "",
                    "v3_0_33": A302._q(A30._qty(o)) if o else "", "v3_0_34": A302._q(A30._qty(ln))})
    return out


def write(out, l3033, changes, log, doc, released_lines=None, for_lead=()):
    """the V3_0_34_* files beside the V3_0_33_* files. -> (file names, identity, ledger)."""
    from pathlib import Path
    from engine.source import boq_line as BL
    out = Path(out)
    l3034, ident = integrate(l3033, changes, for_lead, doc)
    zrows = zone_check(doc, l3034) if doc else []
    rows = ledger_rows(changes, zrows, released_lines)
    diff = diff_rows(l3033, l3034, released_lines)
    dsum = {}
    for d in diff:
        dsum.setdefault("vs_v3_0_33", {}).setdefault(d["vs_v3_0_33"], 0)
        dsum["vs_v3_0_33"][d["vs_v3_0_33"]] += 1
        if d["vs_released_v2_9"] is not None:
            dsum.setdefault("vs_released_v2_9", {}).setdefault(d["vs_released_v2_9"], 0)
            dsum["vs_released_v2_9"][d["vs_released_v2_9"]] += 1
    ident = dict(ident, diff=dsum)
    t33, t34 = A304.code_totals(l3033), A304.code_totals(l3034)
    moved = {k: {"v3_0_33": t33.get(k), "v3_0_34": t34.get(k)} for k in sorted(set(t33) | set(t34))
             if t33.get(k) != t34.get(k)}
    n_na = sum(1 for c in changes if c["after"]["unit"] == "m2")
    for k, v in moved.items():   # NOT_APPLICABLE lines leave the code totals: only the blank-line counts may move
        a, b = v["v3_0_33"] or {}, v["v3_0_34"] or {}
        if k != f"{PAINT}|m2" or any(a.get(x) != b.get(x) for x in ("released", "held_low", "held_high",
                                                                       "bounded_lines")) or \
                a.get("lines", 0) - b.get("lines", 0) != n_na or \
                a.get("blocked_lines", 0) - b.get("blocked_lines", 0) != n_na:
            raise ValueError(f"{METHOD}: a total moved outside the paint line states: {k} {v}")
    log = {k: v for k, v in log.items() if k != "zone_rows"}
    led = {"schema": LEDGER_SCHEMA, "method": METHOD, "extends": EXTENDS, "candidate": CANDIDATE,
           "base": A30.BASE_METHOD, "released": A30.RELEASED_METHOD, "released_default": False, "rows": rows,
           "waiting_pieces": WAITING, "integration_package": True}
    run = {"method": METHOD, "policy": POLICY_ID, "extends": EXTENDS, "candidate": CANDIDATE,
           "base_method": A30.BASE_METHOD, "released_method": A30.RELEASED_METHOD, "released_default": False,
           "rollback": ROLLBACK, "identity": ident, "pieces": PIECES, "piece_logs": [log],
           "totals_moved_by_code": moved, "waiting_pieces": WAITING}
    files = {"V3_0_34_BOQ_LINES.json": BL.dumps(l3034),
             "V3_0_34_BOQ_LINES.csv": A30._lines_csv(l3034),
             "V3_0_34_INTEGRATION_LEDGER.json": A30._j(led),
             "V3_0_34_INTEGRATION_LEDGER.csv": ledger_csv(rows),
             "V3_0_34_DIFF.csv": A305._csv(diff, DIFF_CSV),
             "V3_0_34_RUN.json": A30._j(run)}
    for name, text in files.items():
        (out / name).write_text(text, encoding="utf-8")
    return sorted(files), ident, led


def policy_record():
    return {"method": METHOD, "extends": EXTENDS, "pieces": sorted(PIECES), "inputs_schema": INPUTS_SCHEMA,
            "released_default": False, "rollback": ROLLBACK, "actions": list(ACTIONS)}


__all__ = ["METHOD", "PIECES", "WAITING", "DEFAULT_GUARD_CLASS", "INPUTS_SCHEMA", "load_inputs", "zone_check",
           "changes_for", "check_zones", "integrate", "ledger_rows", "diff_rows", "write", "InputsError"]
