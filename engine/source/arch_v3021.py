"""ARCH_TAKEOFF_V3.0.21 (T-315): the SAME opt-in BOQ candidate as ARCH_TAKEOFF_V3.0 .. V3.0.20 (engine.source.arch_v30,
arch_v301 .. arch_v3020), extended with ONE piece, WALL_TILE_FAMILY: the wall-tile lines (FIN.WALL.TILE) are carried
from a checker-merged face ledger, face by face. Not a new method family and not the released default (owner
management decision 2026-10-20 sections 2 and 5); rollback is running the released ARCH_TAKEOFF_V2.9.

The physical question (ERS 2026-10-22 s.2.1, s.3): wall tile is porcelain / ceramic on a WALL FACE (one drawn wall seen
from one room) from the finished floor to the tile top, less the part of every hole inside that band (UP-CER-005,
Q-73). Which faces carry it is the owner's scope rule (a wet room: every face, full height, UP-FIN-WALL-001; an open
pantry: the host walls of the installation only, UP-PANTRY-001 .. 004); the height is the owner wall height of the
floor (Q-48 A) or a printed tile height, never a default. Each tiled face is in exactly ONE tile line, and a tiled face
carries no paint (UP-FIN-PAINT-001); the plaster / render behind the tile is its own line (UP-FIN-PAINT-001 logic
'substrate'), never folded into the tile figure.

  FILL    a candidate FIN.WALL.TILE line that carries no figure (BLOCKED_RFI) takes the ledger figure, same line id: its
          value is the sum of its faces, each face = length x its own height (with the height's source) less each
          opening's part inside the band, named once per room side. State PROVISIONAL, evidence ASSUMED - OWNER-APPROVED
          with the owner source on the line (the height and the door heads are owner-approved fallbacks,
          WORKFLOW_CONTROLS s.4), or DRAWING-CONFIRMED / VERIFIED where the record says so (VERIFIED names the run).
  HELD    a candidate FIN.WALL.TILE line whose height is not established stays BLANK with its named item: asserted that
          it carries no figure and that the record supplies none (never 0); recorded, the line is not changed.
  ADD     a measured tile scope the candidate has no line for (a NO_LINE row of the ledger, e.g. an open pantry) becomes
          ONE new FIN.WALL.TILE line of the same family in its engine room (refused when that room already has one).

The whole family is integrated at once: every FIN.WALL.TILE line of the run is named by exactly one FILL or HELD
record (a line left out is refused, never silently kept). CROSS-TRADE (per face, cross_trade): in a room whose faces
are all in its tile record, a figure on a paint line (paint under tile) or a skirting line (full-height tile) is
refused; a room with not-tiled faces gets its paint figure named for a per-face check; in a shared engine room a line
naming no room is listed as not attributable; the plaster lines are listed with what they carry (backing: its own
line, reported, never derived here).

Refused (InputsError / ValueError, nothing written): a record whose line the run does not carry, or that is not a
blank FIN.WALL.TILE line of its engine room (stale ledger); a line named twice; a face in two records; an opening twice
in one room; a face net that is not length x height - its openings (> 1e-4 m2), a record value that is not the sum of
its faces (> 0.006 m2), a height without its source, a height outside 1.0 .. 6.0 m (mm or a typo), a known value <= 0;
a HELD record with a figure; a VERIFIED record without the checker run; an ADD into a room with a tile line; a candidate
tile line no record names; a figure on a paint or skirting line of a room whose faces are all tiled. Inside a FILL line only quantity, state, rfi,
gross, geometry confidence, calculation and notes change; every other line is byte-identical to V3.0.20 (asserted),
including the project identity block; the merged default guard runs again over the result (arch_v307.guard_changes)
and may not flag a line this version adds or fills.

Files: V3_0_21_BOQ_LINES.json / .csv, V3_0_21_INTEGRATION_LEDGER.json / .csv (per line: before V3.0.20, after, released
V2.9, faces, owner manual method beside the drawing-derived method, status, source task / merge / checker run),
V3_0_21_FACES.csv (every face once: line, length, height and source, openings, net), V3_0_21_CROSS_TRADE.csv (per
face: tile line, paint lines and what they carry, plaster lines and what they carry), V3_0_21_DIFF.csv (every line
against V3.0.20 and the released V2.9), V3_0_21_RUN.json. Nothing here names a project, a sheet, a layer or a
coordinate: every value comes from the inputs.
"""

from __future__ import annotations

import copy
import hashlib
import json

from engine.source import arch_v30 as A30
from engine.source import arch_v302 as A302
from engine.source import arch_v304 as A304
from engine.source import arch_v305 as A305
from engine.source import arch_v307 as A307
from engine.source import arch_v309 as A309
from engine.source import arch_v3010 as A3010
from engine.source import arch_v3011 as A3011
from engine.source import arch_v3012 as A3012
from engine.source import arch_v3014 as A3014
from engine.source import arch_v3015 as A3015
from engine.source import arch_v3018 as A3018
from engine.source import arch_v3020 as A3020

DEFAULT_GUARD_CLASS = "GUARD_HOST"      # T-212: it adds a valued line; it reaches the guard through arch_v307
METHOD = "ARCH_TAKEOFF_V3.0.21"
EXTENDS = A3020.METHOD
CANDIDATE = A30.METHOD
POLICY_ID = "URBAN_BOQ_T315_ARCH_V3_0_21"
INPUTS_SCHEMA = "URBAN_V3021_INPUTS_V1"
LEDGER_SCHEMA = "URBAN_V3021_INTEGRATION_LEDGER_V1"
ROLLBACK = A30.ROLLBACK
VER, DC, OA = A3018.VER, A3018.DC, A3018.OA
InputsError = A3015.InputsError
_num = A3015._num
_r = A3018._r
TOL = 1e-6
FACE_TOL_M2 = 1e-4                      # a face net vs length x height - openings (4-decimal ledgers)
NET_TOL_M2 = A309.NET_TOL_M2            # 0.006 m2: a record value vs the sum of its faces
H_MIN, H_MAX = 1.0, 6.0                 # a tile height in metres (mm or a typo is refused)
TILE = "FIN.WALL.TILE"
PAINT_CODES = ("FIN.PAINT",)
PLASTER_CODES = ("FIN.PLASTER",)
SKIRT_CODES = ("FIN.SKIRTING",)
KINDS = ("FILL", "HELD", "ADD")
QTY_STATUS = (VER, DC, OA)
HELD_STATUS = ("HELD", "UNKNOWN")
RULE = ("R-WALL-TILE-FAMILY-1", "T-315")

PIECES = {
    "WALL_TILE_FAMILY": {
        "module": "engine/source/arch_v3021.py (the wall-tile family carried face by face from a checker-merged ledger)",
        "policy": "WALL_TILE_FAMILY_V1", "rule_id": RULE[0], "rule_version": RULE[1],
        "owner_rules": ["UP-FIN-WALL-001 (wet room: every face, full height)",
                        "Q-48 A (tile top = underside of the 0.15 decor ceiling: GF 3.65, 1F / 2F 3.35; a printed tile "
                        "height replaces it: ASSUMED - OWNER-APPROVED)",
                        "Q-55 C (door head 2.20 where none is printed: ASSUMED - OWNER-APPROVED)",
                        "UP-CER-005 / Q-73 (gross - openings: each hole by its part inside the tile band)",
                        "UP-PANTRY-001 .. 004 (open pantry: host walls of the installation, whole wall; open edge "
                        "nothing; project height)", "Q-30 / Q-37 A (wet set)",
                        "UP-FIN-PAINT-001 (no paint over porcelain; the substrate behind it is its own line)",
                        "URBAN-NO-SKIRTING-FULL-TILE-WET@v1", "UP-QTY-STATUS-001 (held never 0)",
                        "WORKFLOW_CONTROLS 2026-10-21 s.4 / s.5"],
        "owner_manual_method": "manual QS take-off of a tiled wall: each face length x the owner wall height of the "
                               "floor (Q-48 A), less every door (door head 2.20 where none is printed, Q-55 C) and "
                               "window by its part inside the tile height; one line per room; an open pantry only on "
                               "the walls the counters stand against",
        "drawing_method": "the room contour walked on the drawn faces (each face once, closure per room), the openings "
                          "from the merged opening list, the height from the drawn section / roof datum: shown beside "
                          "on the line (drawing_derived_method), never used to fill a blank"},
    "DEFAULT_GUARD": A307.PIECES["DEFAULT_GUARD"],
}
WAITING = dict(A3020.WAITING)
WAITING.update({
    "WALL_TILE_HELD_HEIGHTS": "wall-tile lines whose owner height is not established (annex rooms: G2 / Q-54 B / D-39; "
                              "rooms with an undrawn level: T-088): the lines stay BLANK, never 0",
    "WALL_TILE_BACKING": "the plaster / render behind the wall tile is its own line (UP-FIN-PAINT-001 'substrate'): no "
                         "checker-merged ledger carries it yet; the tiled rooms' plaster lines are listed per face in "
                         "V3_0_21_CROSS_TRADE.csv, nothing is derived here",
})


# ================================================================================================ inputs
def _check_faces(faces, where, seen_faces, contour=None):
    """every face of one record: -> (sum of nets, gross, deductions [{opening, m2, face}]). With the room contour, the
    face lengths + the open edges close to it."""
    if not faces:
        raise InputsError(f"{where}: a valued record lists its faces (each face once)")
    tot, gross, deds, opened, run = 0.0, 0.0, [], set(), 0.0
    for f in faces:
        fid = f.get("face_id")
        w = f"{where} face {fid}"
        if not fid:
            raise InputsError(f"{where}: every face names its face_id")
        if fid in seen_faces:
            raise InputsError(f"{w}: the face is in two records (each tiled face in exactly one line)")
        seen_faces.add(fid)
        ln, h = f.get("length_m"), f.get("height_m")
        corr = bool(f.get("correction"))
        if corr:      # a closure correction piece of the merged walk (it brings the pieces to the verified contour)
            if not (_num(ln) and ln != 0 and f.get("basis")) or f.get("openings"):
                raise InputsError(f"{w}: a closure correction names its basis, carries a length != 0 and no opening")
        elif not (_num(ln) and ln > 0):
            raise InputsError(f"{w}: length_m > 0 (a missing length is HELD, never 0)")
        if not _num(h):
            raise InputsError(f"{w}: height_m is required (a missing height is HELD: the record is HELD)")
        if not (H_MIN <= h <= H_MAX):
            raise InputsError(f"{w}: height {h} m is outside {H_MIN} .. {H_MAX} m (mm or a typo)")
        if not f.get("height_source"):
            raise InputsError(f"{w}: the height names its source (owner rule or printed value), never a default")
        g = ln * h
        sub = 0.0
        for o in f.get("openings") or ():
            oid = o.get("id")
            if not oid:
                raise InputsError(f"{w}: an opening names its id")
            if oid in opened:
                raise InputsError(f"{w}: opening {oid} deducted twice in this room (once per room side)")
            opened.add(oid)
            m2 = o.get("m2")
            if not (_num(m2) and m2 > 0):
                raise InputsError(f"{w}: opening {oid} deducts its part inside the band, > 0 (none inside: not listed)")
            if m2 > g + TOL:
                raise InputsError(f"{w}: opening {oid} {m2} m2 is larger than its face {round(g, 4)} m2")
            sub += m2
            deds.append({"opening": oid, "m2": _r(m2, 4), "face": fid, "basis": (o.get("basis") or "")[:200]})
        net = f.get("net_m2")
        if not (_num(net) and (net > 0 or corr)):
            raise InputsError(f"{w}: net_m2 > 0")
        if abs(net - (g - sub)) > FACE_TOL_M2:
            raise InputsError(f"{w}: net {net} != {ln} x {h} - {round(sub, 4)} = {round(g - sub, 4)}")
        tot += net
        gross += g
        run += ln
    if contour is not None:
        c, o, nt = contour.get("contour_m"), contour.get("open_m"), contour.get("not_tiled_m", 0.0)
        if not (_num(c) and c > 0 and _num(o) and o >= 0 and _num(nt) and nt >= 0 and contour.get("source")):
            raise InputsError(f"{where}: contour {{contour_m > 0, open_m >= 0, not_tiled_m >= 0, source}}")
        if abs(run + o + nt - c) > FACE_TOL_M2:
            raise InputsError(f"{where}: the faces close to {round(run, 4)} m + open {o} + not tiled {nt} m, the room "
                              f"contour is {c} m (each face once, the room closes)")
    if not (tot > 0 and gross > 0):
        raise InputsError(f"{where}: the faces sum to {round(tot, 4)} m2 (> 0)")
    return tot, gross, deds


def _check_record(r, where, tasks, seen_faces):
    k = r.get("kind")
    if k not in KINDS:
        raise InputsError(f"{where}: kind {k!r} not one of {KINDS}")
    for x in ("room", "engine_room", "floor", "task", "evidence_status"):
        if not r.get(x):
            raise InputsError(f"{where}: {x} required")
    if r["task"] not in tasks:
        raise InputsError(f"{where}: task {r['task']!r} is not one of the sources {sorted(tasks)}")
    if k in ("FILL", "HELD") and not r.get("line_id"):
        raise InputsError(f"{where}: a {k} record names its candidate line_id")
    if k == "ADD" and r.get("line_id"):
        raise InputsError(f"{where}: an ADD record names no candidate line (its line id is made by this version)")
    if k == "HELD":
        for x in ("value", "faces"):
            if r.get(x) not in (None, [], ()):
                raise InputsError(f"{where}: a HELD record carries no figure ({x}): BLANK in the BOQ, never 0")
        if r["evidence_status"] not in HELD_STATUS or not r.get("reasons"):
            raise InputsError(f"{where}: a HELD record names why (reasons) and its status {HELD_STATUS}")
        return None
    v = r.get("value")
    if not (_num(v) and v > 0):
        raise InputsError(f"{where}: a {k} record carries a value > 0 (a missing one is HELD, never 0)")
    if r["evidence_status"] not in QTY_STATUS:
        raise InputsError(f"{where}: a valued record is one of {QTY_STATUS}")
    if r["evidence_status"] == VER and not r.get("verified_by"):
        raise InputsError(f"{where}: VERIFIED names the checker run")
    if r["evidence_status"] == OA and not r.get("assumption"):
        raise InputsError(f"{where}: ASSUMED - OWNER-APPROVED carries its owner source on the line "
                          "(WORKFLOW_CONTROLS s.4)")
    if not r.get("contour"):
        raise InputsError(f"{where}: a valued record carries its room contour (closure)")
    tot, gross, deds = _check_faces(r.get("faces") or [], where, seen_faces, r["contour"])
    if abs(tot - v) > NET_TOL_M2:
        raise InputsError(f"{where}: value {v} != the sum of its faces {round(tot, 4)}")
    return tot, gross, deds


def load_inputs(doc, project_id=None):
    """URBAN_V3021_INPUTS_V1 or None:
        {"schema", "project", "sources": [{file, sha256, task, merge_commit, checker_run}],
         "records": [{kind FILL | HELD | ADD, line_id (FILL / HELD), room, engine_room, floor, task, evidence_status,
                      value, assumption, verified_by, reasons, faces [{face_id, wall_id, length_m, height_m,
                      height_source, openings [{id, m2, basis}], net_m2}], drawing_derived_method, info, downstream}],
         "declared": {"FILL": {"lines", "m2"}, "HELD": {"lines"}, "ADD": {"lines", "m2"}},
         "guard": as URBAN_V307_INPUTS_V1 "guard" (optional)}"""
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
    seen_lines, seen_faces, seen_rooms = set(), set(), set()
    tot = {k: {"lines": 0, "m2": 0.0} for k in KINDS}
    for i, r in enumerate(recs):
        where = f"record {r.get('line_id') or r.get('room') or i}"
        lid = r.get("line_id")
        if lid:
            if lid in seen_lines:
                raise InputsError(f"{where}: line named twice")
            seen_lines.add(lid)
        if r.get("room") in seen_rooms:
            raise InputsError(f"{where}: room {r.get('room')!r} in two records (one tile line per room)")
        seen_rooms.add(r.get("room"))
        res = _check_record(r, where, tasks, seen_faces)
        t = tot[r["kind"]]
        t["lines"] += 1
        if res is not None:
            t["m2"] += r["value"]
    dec = doc.get("declared") or {}
    for k in KINDS:
        d = dec.get(k) or {"lines": 0, "m2": 0.0}
        if d.get("lines", 0) != tot[k]["lines"] or (k != "HELD" and abs(d.get("m2", 0.0) - tot[k]["m2"]) > 1e-4):
            raise InputsError(f"declared {k} {d} != the records' {tot[k]['lines']} lines / {round(tot[k]['m2'], 4)} m2")
    g = doc.get("guard")
    if g is not None:
        A307.load_inputs({"schema": A307.INPUTS_SCHEMA, "project": doc.get("project"), "guard": g}, project_id)
    return doc


# ================================================================================================ lines
def _room_id(ln):
    return (ln.get("location") or {}).get("room_id")


def _assert_blank_tile(ln, r, where):
    if ln is None:
        raise InputsError(f"{where}: the run carries no line {r['line_id']}")
    if ln["item_code"] != TILE:
        raise InputsError(f"{where}: line {r['line_id']} is {ln['item_code']}, not {TILE}")
    if _room_id(ln) != r["engine_room"] or (ln.get("location") or {}).get("floor") != r["floor"]:
        raise InputsError(f"{where}: the line is in {_room_id(ln)!r} {ln['location'].get('floor')}, the record "
                          f"{r['engine_room']!r} {r['floor']} (stale ledger)")
    if ln["evidence_state"] != "BLOCKED_RFI" or A309._carried(ln) != A309.NO_FIGURE:
        raise InputsError(f"{where}: line {r['line_id']} is {ln['evidence_state']} carrying {A309._carried(ln)}: "
                          "only a blank tile line is filled here (stale ledger)")


def _faces_rec(r):
    return [{"face_id": f["face_id"], "wall_id": f.get("wall_id"), "length_m": _r(f["length_m"], 4),
             "height_m": _r(f["height_m"], 4), "height_source": f["height_source"][:200],
             "openings": [{"id": o["id"], "m2": _r(o["m2"], 4)} for o in f.get("openings") or ()],
             "net_m2": _r(f["net_m2"], 4), "correction": f.get("basis")[:300] if f.get("correction") else None} for f in r.get("faces") or ()]


def _tile_inputs(r, src, gross, deds):
    p = PIECES["WALL_TILE_FAMILY"]
    return {"policy": p["policy"], "kind": r["kind"], "task": src["task"], "ledger": src["file"],
            "ledger_sha256": src["sha256"], "merge_commit": src["merge_commit"], "checker_run": src["checker_run"],
            "room": r["room"], "faces": _faces_rec(r), "rule_id": RULE[0], "rule_version": RULE[1]}


def _owner_method(r, gross, deds):
    return {"gross": _r(gross, 4), "deductions": deds, "net": _r(r["value"], 4),
            "height_basis": sorted({f["height_source"][:200] for f in r["faces"]})}


def filled_line(before, r, src, gross, deds):
    """the line of one FILL record (same line id). -> line"""
    from engine.source import boq_line as BL
    ln = copy.deepcopy(before)
    inp = ln["calculation"]["inputs"]
    ln["evidence_state"] = A3018.STATE_OF[r["evidence_status"]]
    ln["measured_net"] = _r(r["value"])
    ln["bounded_range"] = None
    ln["rfi"] = None
    ln["gross"] = _r(gross)
    ln["source"]["geometry_confidence"] = "TOLERANCE_CERTIFIED"
    inp["owner_manual_method"] = _owner_method(r, gross, deds)
    inp["drawing_derived_method"] = r.get("drawing_derived_method")
    inp["record_state"] = "FILL"
    inp["evidence_status"] = r["evidence_status"]
    inp["verified_by"] = r.get("verified_by")
    inp["assumption"] = r.get("assumption")
    inp["wall_tile_v3021"] = dict(_tile_inputs(r, src, gross, deds), before=A3018._before_rec(before))
    ln["calculation"]["formula"] = (f"{ln['calculation'].get('formula')}; {METHOD}: sum of {len(r['faces'])} tiled "
                                    f"faces (length x owner height - openings inside the band) = "
                                    f"{_r(r['value'], 4)} m2")[:600]
    A305._note(ln, f"{METHOD}: wall tile from the merged face ledger ({src['task']}, MERGED {src['merge_commit']}): "
                   f"{r['evidence_status']} ({(r.get('assumption') or '')[:160]})")
    return BL.validate(ln)


def added_line(template, r, src, gross, deds):
    """ONE new FIN.WALL.TILE line in the record's engine room, shaped as the family's lines (item, trade, subtrade,
    documents and identity of the template)."""
    from engine.source import boq_line as BL
    pid, rev = template["project"]["project_id"], template["project"]["revision_set_sha256"]
    eid = f"{r['engine_room']}#WALL_TILE:{r['room']}"
    inputs = {"room": r["room"], "owner_manual_method": _owner_method(r, gross, deds),
              "drawing_derived_method": r.get("drawing_derived_method"), "record_state": "ADD",
              "evidence_status": r["evidence_status"], "verified_by": r.get("verified_by"),
              "assumption": r.get("assumption"), "wall_tile_v3021": _tile_inputs(r, src, gross, deds)}
    ln = BL.make_line(project_id=pid, revision_set_sha256=rev, item_code=TILE, unit="m2",
                      evidence_state=A3018.STATE_OF[r["evidence_status"]], measured_net=_r(r["value"]),
                      element_id=eid, floor=r["floor"], room_id=r["engine_room"],
                      physical_element=template.get("physical_element") or "wall_tile", gross=_r(gross),
                      formula=(f"{METHOD}: sum of {len(r['faces'])} tiled faces (length x owner height - openings "
                               f"inside the band) = {_r(r['value'], 4)} m2")[:600],
                      inputs=inputs, documents=(template.get("source") or {}).get("documents") or [],
                      geometry_source=(template.get("source") or {}).get("geometry_source") or "CAD_VECTOR",
                      geometry_confidence="TOLERANCE_CERTIFIED", rule_id=RULE[0], rule_version=RULE[1],
                      material_state=template.get("material_state") or "BY_SPEC",
                      notes=(f"{METHOD}: a measured wall-tile scope with no candidate line (NO_LINE in {src['task']}, "
                             f"MERGED {src['merge_commit']}): {r['evidence_status']} "
                             f"({(r.get('assumption') or '')[:160]})"),
                      subtrade=template.get("subtrade"), item_en=template.get("item_en"),
                      item_ar=template.get("item_ar"), trade=template.get("trade"))
    return BL.validate(ln)


def _tile_lines(lines):
    return [ln for ln in lines if ln["item_code"] == TILE]


def family_changes(doc, l3020):
    """-> (changes, log, face rows)."""
    by = {ln["line_id"]: ln for ln in l3020}
    tiles = _tile_lines(l3020)
    if not tiles:
        raise InputsError(f"the run carries no {TILE} line: the family is integrated against its candidate lines")
    named = {r["line_id"] for r in doc["records"] if r.get("line_id")}
    missing = sorted(ln["line_id"] for ln in tiles if ln["line_id"] not in named)
    if missing:
        raise InputsError(f"{len(missing)} candidate {TILE} line(s) named by no record (the family is integrated "
                          f"whole): {missing[:5]}")
    rooms_with_tile = {_room_id(ln) for ln in tiles}
    changes, faces_out = [], []
    log = {"piece": "WALL_TILE_FAMILY", "state": "RUN", "sources": doc["sources"], "kinds": {}, "m2": {}}
    for r in doc["records"]:
        where = f"record {r.get('line_id') or r['room']}"
        src = A3018._src_of(doc, r["task"])
        k = r["kind"]
        log["kinds"][k] = log["kinds"].get(k, 0) + 1
        if k == "HELD":
            _assert_blank_tile(by.get(r["line_id"]), r, where)
            continue
        tot, gross, deds = _check_faces(r["faces"], where, set(), r["contour"])
        if k == "FILL":
            b = by.get(r["line_id"])
            _assert_blank_tile(b, r, where)
            after = filled_line(b, r, src, gross, deds)
            action, before = "REPLACE", b
        else:
            if r["engine_room"] in rooms_with_tile:
                raise InputsError(f"{where}: engine room {r['engine_room']} already has a {TILE} line (one tile line "
                                  "per room: a FILL, never a second line)")
            after = added_line(tiles[0], r, src, gross, deds)
            if after["line_id"] in by:
                raise ValueError(f"{METHOD}: the added line repeats a candidate line id")
            action, before = "ADD", None
        log["m2"][k] = _r(log["m2"].get(k, 0.0) + r["value"], 4)
        ver = {"task": src["task"], "merge_commit": src["merge_commit"], "verifier_run": src["checker_run"],
               "ledger": src["file"], "ledger_sha256": src["sha256"], "record_verified_by": r.get("verified_by")}
        changes.append(A305._change("WALL_TILE_FAMILY", action, before, after, drawing_reference=src["file"],
                                    held=[], downstream=[d if isinstance(d, dict) else {"item": d}
                                                         for d in r.get("downstream") or ()],
                                    verification=ver, evidence_status=r["evidence_status"],
                                    codes=["WALL_TILE_FAMILY", k], group=r["room"],
                                    guard_element={"element_id": after["location"]["element_id"], "part": "WHOLE"}))
        for f in _faces_rec(r):
            faces_out.append(dict(f, room=r["room"], engine_room=r["engine_room"], floor=r["floor"],
                                  line_id=after["line_id"], kind=k, evidence_status=r["evidence_status"]))
    return changes, log, faces_out


def _ledger_room(ln):
    return ((ln.get("calculation") or {}).get("inputs") or {}).get("room")


def cross_trade(lines, doc, faces):
    """per face: the tile line, the paint / skirting lines of its room and the plaster lines of its room. -> rows

    A finish line belongs to a tiled room when it lies in the record's engine room AND names the record's room, or names
    no room while the engine room is the record's alone. In a SHARED engine room (one engine room holding several
    drawn rooms, the record says engine_room_shared), a line naming no room is listed as not attributable, never
    attributed. Every face of a room in its tile record (a wet room, or a pantry whose drawn walls all host): a paint
    figure is refused (UP-FIN-PAINT-001: no paint under tile) and a skirting figure is refused
    (URBAN-NO-SKIRTING-FULL-TILE-WET@v1). A room with not-tiled drawn faces: a paint figure is named for a per-face
    check, never refused. Plaster lines are listed with what they carry: the backing behind the tile is its own line
    (UP-FIN-PAINT-001 substrate), reported, never derived here."""
    recs = {(r["engine_room"], r["room"]): r for r in doc["records"]}
    by_er = {}
    for ln in lines:
        if ln["item_code"] in PAINT_CODES + PLASTER_CODES + SKIRT_CODES:
            by_er.setdefault(_room_id(ln), []).append(ln)
    own, unattributed, partial = {}, {}, {}
    for (er, room), r in sorted(recs.items()):
        shared = bool(r.get("engine_room_shared"))
        mine, other = [], []
        for ln in by_er.get(er, ()):
            lr = _ledger_room(ln)
            if lr == room or (lr is None and not shared):
                mine.append(ln)
            elif lr is None:
                other.append(ln)
        own[room], unattributed[room] = mine, other
        all_tiled = r["kind"] == "HELD" or not (r.get("contour") or {}).get("not_tiled_m")
        for ln in mine:
            fig = A309._carried(ln)
            if fig == A309.NO_FIGURE or ln["item_code"] in PLASTER_CODES:
                continue
            if all_tiled:
                why = ("paint under wall tile (UP-FIN-PAINT-001)" if ln["item_code"] in PAINT_CODES else
                       "skirting on a full-height tiled face (URBAN-NO-SKIRTING-FULL-TILE-WET@v1)")
                raise ValueError(f"{METHOD}: {ln['item_code']} line {ln['line_id']} of tiled room {room} ({er}) "
                                 f"carries {fig}: {why}; every face of the room is in its tile record")
            partial.setdefault(room, []).append(ln["line_id"])

    def _desc(lns, codes):
        return "; ".join(f"{x['line_id']} {x['evidence_state']} {A309._carried(x)}" for x in lns
                         if x["item_code"] in codes)

    def _row(face_id, room, er, tile_line, net, backing):
        un = unattributed.get(room) or []
        return {"face_id": face_id, "room": room, "engine_room": er, "tile_line": tile_line, "tile_net_m2": net,
                "paint_lines": _desc(own.get(room) or (), PAINT_CODES),
                "paint_figure": ("NONE" if room not in partial else
                                 "FIGURE ON THE NOT-TILED FACES ONLY (the line must exclude the tiled faces: check by "
                                 "face): " + " ".join(partial[room])),
                "skirting_lines": _desc(own.get(room) or (), SKIRT_CODES),
                "plaster_lines": _desc(own.get(room) or (), PLASTER_CODES),
                "shared_engine_room_lines": ("NOT ATTRIBUTABLE to this room (shared engine room, the line names no "
                                             "room): " + _desc(un, PAINT_CODES + PLASTER_CODES + SKIRT_CODES))
                if un else "",
                "backing": backing}
    rows = []
    for f in faces:
        rows.append(_row(f["face_id"], f["room"], f["engine_room"], f["line_id"], f["net_m2"],
                         "OWN LINE (UP-FIN-PAINT-001 substrate): not carried by a merged ledger; HELD by name"))
    for r in doc["records"]:
        if r["kind"] == "HELD":
            rows.append(_row(f"{r['room']} (all faces, HELD line)", r["room"], r["engine_room"], r["line_id"], "HELD",
                             "OWN LINE: HELD with the tile height"))
    return rows


def check_tile_family(lines):
    """every FIN.WALL.TILE line: a quantity line > 0, or BLANK (BLOCKED_RFI, no figure, no range); one per room."""
    seen, out = set(), {"lines": 0, "valued": 0, "blank": 0, "m2": 0.0}
    for ln in _tile_lines(lines):
        rid = (_room_id(ln), ln["location"].get("floor"))
        if rid in seen:
            raise ValueError(f"{METHOD}: two {TILE} lines in room {rid} (a face in two tile lines)")
        seen.add(rid)
        out["lines"] += 1
        if ln["evidence_state"] in ("PROVISIONAL", "SOURCE_DERIVED", "MEASURED"):
            if not (ln.get("measured_net") or 0) > 0:
                raise ValueError(f"{METHOD}: {ln['line_id']} carried at 0")
            out["valued"] += 1
            out["m2"] += ln["measured_net"]
        elif ln["evidence_state"] == "BLOCKED_RFI":
            if ln.get("measured_net") is not None or ln.get("bounded_range") is not None:
                raise ValueError(f"{METHOD}: held tile line {ln['line_id']} carries a figure")
            out["blank"] += 1
        else:
            raise ValueError(f"{METHOD}: tile line {ln['line_id']} state {ln['evidence_state']}")
    out["m2"] = _r(out["m2"], 4)
    return out


def changes_for(doc, l3020):
    """-> (changes, logs, face rows). The guard re-check runs over the result (arch_v307)."""
    if not doc:
        return [], [{"piece": "WALL_TILE_FAMILY", "state": "NO_PROJECT_INPUT"}], []
    ch, log, faces = family_changes(doc, l3020)
    rep = {c["before"]["line_id"]: c["after"] for c in ch if c["action"] == "REPLACE"}
    view = [rep.get(ln["line_id"], ln) for ln in l3020]
    ch_g, log_g = A307.guard_changes(doc, view, [c for c in ch if c["action"] == "ADD"], set(rep))
    for c in ch_g:
        lid = c["before"]["line_id"]
        if lid in rep:
            raise ValueError(f"{METHOD}: the guard flags a line this version fills ({lid})")
        A305._note(c["after"], f"(re-check run by {METHOD})")
    return ch + ch_g, [log, log_g], faces


# ================================================================================================ integrate / write
ROW_KEYS = ("evidence_state", "measured_net", "bounded_range", "rfi", "notes", "gross", "calculation")


def integrate(l3020, changes):
    """-> (V3.0.21 lines, identity). Every line outside the V3.0.21 rows is byte-identical to the V3.0.20 line."""
    from engine.source import boq_line as BL
    sid = {ln["line_id"] for ln in l3020}
    rep, adds = {}, []
    for c in changes:
        if c["action"] == "REPLACE":
            lid = c["before"]["line_id"]
            if lid in rep or lid not in sid or c["after"]["line_id"] != lid:
                raise ValueError(f"{METHOD}: line {lid}: changed twice, not in V3.0.20, or its id changed")
            if c["piece"] == "WALL_TILE_FAMILY" and c["before"]["item_code"] != TILE:
                raise ValueError(f"{METHOD}: the family piece replaces {TILE} lines only ({lid})")
            rep[lid] = c["after"]
        elif c["action"] == "ADD":
            if c["piece"] != "WALL_TILE_FAMILY" or c["after"]["item_code"] != TILE:
                raise ValueError(f"{METHOD}: only the family piece adds, and only {TILE} lines")
            if c["after"]["line_id"] in sid:
                raise ValueError(f"{METHOD}: an added line repeats a V3.0.20 line id")
            adds.append(c["after"])
        else:
            raise ValueError(f"{METHOD}: action {c['action']}")
    out = [rep.get(ln["line_id"], ln) for ln in l3020] + adds
    if len({ln["line_id"] for ln in out}) != len(out):
        raise ValueError(f"{METHOD}: a BOQ line id appears twice")
    for ln in out:
        BL.validate(ln)
    A3011.check_conflicts(out)
    A3010.check_same_openings(out)
    A3012.check_partition(out)
    A3014.check_floor_scope(out)
    A3015.check_family(out)
    A3018.check_splits(out)
    fam = check_tile_family(out)
    pids = {(ln["project"]["project_id"], ln["project"]["revision_set_sha256"]) for ln in out}
    if len(pids) != 1:
        raise ValueError(f"{METHOD}: {len(pids)} project identities in the lines (one project, one revision set)")
    by20 = {ln["line_id"]: ln for ln in l3020}
    touched = set(rep) | {a["line_id"] for a in adds}
    outside = [ln for ln in out if ln["line_id"] not in touched]
    bad = [ln["line_id"] for ln in outside if A30.line_sha(by20[ln["line_id"]]) != A30.line_sha(ln)]
    if bad or len(outside) + len(rep) != len(l3020):
        raise ValueError(f"{METHOD}: {len(bad)} line(s) outside the V3.0.21 rows differ from {EXTENDS}")
    for lid, ln in rep.items():   # inside a row only quantity, state, basis and notes change
        a, b = copy.deepcopy(by20[lid]), copy.deepcopy(ln)
        for x in (a, b):
            for k in ROW_KEYS:
                x.pop(k, None)
            x["source"].pop("geometry_confidence", None)
        if json.dumps(a, sort_keys=True) != json.dumps(b, sort_keys=True):
            raise ValueError(f"{METHOD}: line {lid} changed outside quantity / state / basis")
    ident = {"v3_0_20_lines": len(l3020), "v3_0_21_lines": len(out), "v3_0_21_rows": len(changes),
             "replaced": len(rep), "added": len(adds), "outside_rows": len(outside),
             "outside_rows_identical_to_v3_0_20": len(outside), "wall_tile_family": fam,
             "outside_rows_sha256": hashlib.sha256("".join(A30.line_sha(x) for x in outside).encode()).hexdigest()}
    return out, ident


def ledger_rows(changes, doc, released_lines=None):
    rel = {A30._key(ln): ln for ln in released_lines or ()}
    p = PIECES["WALL_TILE_FAMILY"]
    rows = []
    for c in changes:
        ref = c["after"]
        b29 = None
        if released_lines is not None:
            b29 = A30._qty(rel[A30._key(ref)]) if A30._key(ref) in rel else dict(A30._qty(None),
                                                                                 state="NOT_IN_RELEASED")
        inp = ref["calculation"]["inputs"]
        loc = ref.get("location") or {}
        pp = PIECES[c["piece"]]
        rows.append({"version": METHOD, "piece": c["piece"], "action": c["action"], "line_id": ref["line_id"],
                     "item_code": ref["item_code"], "floor": loc.get("floor"), "room": inp.get("room") or c.get("group"),
                     "room_id": loc.get("room_id"), "element_id": loc.get("element_id"), "unit": ref["unit"],
                     "before_released_v2_9": b29,
                     "before_v3_0_20": A30._qty(c["before"]) if c["before"] else dict(A30._qty(None),
                                                                                      state="NOT_IN_V3_0_20"),
                     "after_v3_0_21": A30._qty(ref), "evidence_status": c.get("evidence_status"),
                     "assumption": inp.get("assumption"), "release_status": "NOT RELEASED",
                     "faces": (inp.get("wall_tile_v3021") or {}).get("faces") or [],
                     "owner_manual_method": inp.get("owner_manual_method"),
                     "drawing_derived_method": inp.get("drawing_derived_method"),
                     "codes": c.get("codes") or [], "owner_rules": pp.get("owner_rules"),
                     "owner_manual_method_text": pp.get("owner_manual_method"),
                     "drawing_method_text": pp.get("drawing_method"),
                     "verification": dict(c.get("verification") or {}, module=pp.get("module"),
                                          policy=pp.get("policy")),
                     "held": c.get("held") or [], "downstream": c.get("downstream") or [], "rollback": ROLLBACK})
    for r in doc["records"]:
        if r["kind"] != "HELD":
            continue
        rows.append({"version": METHOD, "piece": "WALL_TILE_FAMILY", "action": "KEEP_HELD", "line_id": r["line_id"],
                     "item_code": TILE, "floor": r["floor"], "room": r["room"], "room_id": r["engine_room"],
                     "element_id": None, "unit": "m2", "before_released_v2_9": None,
                     "before_v3_0_20": {"state": "BLOCKED_RFI", "value": None, "low": None, "high": None},
                     "after_v3_0_21": {"state": "BLOCKED_RFI", "value": None, "low": None, "high": None},
                     "evidence_status": r["evidence_status"], "assumption": None, "release_status": "NOT RELEASED",
                     "faces": [], "owner_manual_method": None, "info": r.get("info"),
                     "drawing_derived_method": r.get("drawing_derived_method"), "codes": ["WALL_TILE_FAMILY", "HELD"],
                     "owner_rules": p["owner_rules"], "owner_manual_method_text": p["owner_manual_method"],
                     "drawing_method_text": p["drawing_method"],
                     "verification": {"task": r["task"], "module": p["module"], "policy": p["policy"]},
                     "held": [{"what": f"{TILE} {r['room']}", "why": "; ".join(r["reasons"])[:900]}],
                     "downstream": list(r.get("downstream") or ()), "rollback": ROLLBACK})
    return rows


LEDGER_CSV = ("version", "action", "room", "line_id", "item_code", "floor", "unit", "v2_9", "v3_0_20", "v3_0_21",
              "evidence_status", "assumption", "release_status", "faces", "held", "verification")
FACES_CSV = ("face_id", "room", "engine_room", "floor", "line_id", "kind", "wall_id", "length_m", "height_m",
             "height_source", "openings", "net_m2", "correction", "evidence_status")
CROSS_CSV = ("face_id", "room", "engine_room", "tile_line", "tile_net_m2", "paint_lines", "paint_figure",
             "skirting_lines", "plaster_lines", "shared_engine_room_lines", "backing")
DIFF_CSV = ("line_id", "item_code", "floor", "element_id", "unit", "vs_v3_0_20", "vs_released_v2_9", "v2_9",
            "v3_0_20", "v3_0_21")


def ledger_csv(rows):
    return A305._csv([{"version": r["version"], "action": r["action"], "room": r["room"], "line_id": r["line_id"],
                       "item_code": r["item_code"], "floor": r["floor"], "unit": r["unit"],
                       "v2_9": A302._q(r["before_released_v2_9"]) if r["before_released_v2_9"] else "",
                       "v3_0_20": A302._q(r["before_v3_0_20"]), "v3_0_21": A302._q(r["after_v3_0_21"]),
                       "evidence_status": r["evidence_status"], "assumption": (r.get("assumption") or "")[:200],
                       "release_status": r["release_status"], "faces": len(r["faces"]),
                       "held": "; ".join(h["why"] for h in r["held"])[:300],
                       "verification": f"{r['verification'].get('task')} {r['verification'].get('merge_commit') or ''} "
                                       f"{r['verification'].get('verifier_run') or ''}".strip()} for r in rows],
                     LEDGER_CSV)


def diff_rows(l3020, l3021, released_lines=None):
    b20 = {ln["line_id"]: ln for ln in l3020}
    rel = {A30._key(ln): ln for ln in released_lines or ()}
    out = []
    for ln in l3021:
        o = b20.get(ln["line_id"])
        vs = "ADDED" if o is None else ("SAME" if A30.line_sha(o) == A30.line_sha(ln) else "CHANGED")
        r = rel.get(A30._key(ln)) if released_lines is not None else None
        vs29 = None if released_lines is None else ("NOT_IN_RELEASED" if r is None else
                                                    ("SAME_QUANTITY" if A30._qty(r) == A30._qty(ln) else
                                                     "QUANTITY_DIFFERS"))
        out.append({"line_id": ln["line_id"], "item_code": ln["item_code"], "floor": ln["location"].get("floor"),
                    "element_id": ln["location"].get("element_id"), "unit": ln["unit"], "vs_v3_0_20": vs,
                    "vs_released_v2_9": vs29, "v2_9": A302._q(A30._qty(r)) if r else "",
                    "v3_0_20": A302._q(A30._qty(o)) if o else "", "v3_0_21": A302._q(A30._qty(ln))})
    return out


def write(out, l3020, changes, logs, faces, doc, released_lines=None):
    """the V3_0_21_* files beside the V3_0_20_* files. -> (file names, identity, ledger)."""
    from pathlib import Path
    from engine.source import boq_line as BL
    out = Path(out)
    l3021, ident = integrate(l3020, changes)
    xrows = cross_trade(l3021, doc, faces)
    rows = ledger_rows(changes, doc, released_lines)
    diff = diff_rows(l3020, l3021, released_lines)
    dsum = {}
    for d in diff:
        dsum.setdefault("vs_v3_0_20", {}).setdefault(d["vs_v3_0_20"], 0)
        dsum["vs_v3_0_20"][d["vs_v3_0_20"]] += 1
        if d["vs_released_v2_9"] is not None:
            dsum.setdefault("vs_released_v2_9", {}).setdefault(d["vs_released_v2_9"], 0)
            dsum["vs_released_v2_9"][d["vs_released_v2_9"]] += 1
    ident = dict(ident, diff=dsum, faces=len(faces), cross_trade_rows=len(xrows))
    t20, t21 = A304.code_totals(l3020), A304.code_totals(l3021)
    moved = {k: {"v3_0_20": t20.get(k), "v3_0_21": t21.get(k)} for k in sorted(set(t20) | set(t21))
             if t20.get(k) != t21.get(k)}
    led = {"schema": LEDGER_SCHEMA, "method": METHOD, "extends": EXTENDS, "candidate": CANDIDATE,
           "base": A30.BASE_METHOD, "released": A30.RELEASED_METHOD, "released_default": False, "rows": rows,
           "faces": faces, "cross_trade": xrows, "waiting_pieces": WAITING, "integration_package": True}
    run = {"method": METHOD, "policy": POLICY_ID, "extends": EXTENDS, "candidate": CANDIDATE,
           "base_method": A30.BASE_METHOD, "released_method": A30.RELEASED_METHOD, "released_default": False,
           "rollback": ROLLBACK, "identity": ident, "pieces": PIECES, "piece_logs": logs,
           "totals_moved_by_code": moved, "waiting_pieces": WAITING,
           "evidence_status_counts": A302._count(r["evidence_status"] for r in rows)}
    files = {"V3_0_21_BOQ_LINES.json": BL.dumps(l3021),
             "V3_0_21_BOQ_LINES.csv": A30._lines_csv(l3021),
             "V3_0_21_INTEGRATION_LEDGER.json": A30._j(led),
             "V3_0_21_INTEGRATION_LEDGER.csv": ledger_csv(rows),
             "V3_0_21_FACES.csv": A305._csv([dict(f, openings=" ".join(f"{o['id']} {o['m2']}" for o in f["openings"]))
                                             for f in faces], FACES_CSV),
             "V3_0_21_CROSS_TRADE.csv": A305._csv(xrows, CROSS_CSV),
             "V3_0_21_DIFF.csv": A305._csv(diff, DIFF_CSV),
             "V3_0_21_RUN.json": A30._j(run)}
    for name, text in files.items():
        (out / name).write_text(text, encoding="utf-8")
    return sorted(files), ident, led


def policy_record():
    return {"method": METHOD, "extends": EXTENDS, "pieces": sorted(PIECES), "inputs_schema": INPUTS_SCHEMA,
            "released_default": False, "rollback": ROLLBACK}


__all__ = ["METHOD", "PIECES", "WAITING", "DEFAULT_GUARD_CLASS", "INPUTS_SCHEMA", "load_inputs", "filled_line",
           "added_line", "family_changes", "cross_trade", "check_tile_family", "changes_for", "integrate",
           "ledger_rows", "diff_rows", "write", "InputsError"]
