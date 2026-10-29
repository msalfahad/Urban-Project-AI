"""ARCH_TAKEOFF_V3.0.22 (T-331): the SAME opt-in BOQ candidate as ARCH_TAKEOFF_V3.0 .. V3.0.21 (engine.source.arch_v30,
arch_v301 .. arch_v3021), extended with ONE piece, WET_ROOM_PLASTER_BACKING: the plaster lines (FIN.PLASTER) of the
rooms whose walls carry wall tile are carried from a checker-merged backing ledger, face by face, bound to the
candidate's own wall-tile line of the same room. Not a new method family and not the released default (owner
management decision 2026-10-20 sections 2 and 5); rollback is running the released ARCH_TAKEOFF_V2.9.

The physical question (ERS 2026-10-22 s.2.1, s.3): behind a wall tile there is ONE layer of its own, the cementitious
backing coat (UP-FIN-PAINT-001 logic 'substrate': the substrate / plaster behind porcelain is its own line; its mix and
thickness are an answered owner value, e.g. Q-45 B), then the adhesive (its own line), then the tile. So the backing
covers exactly the TILED faces of the room, face by face, from the floor to the tile top, less the same openings by the
same parts as the tile (backing - tile = 0 on every face). Above the tile top there may be a BAND of plaster up to the
plaster top: the owner manual method takes the plaster top from the owner's room height (when it equals the tile top,
the band is 0); the drawing-derived method takes it from the drawn soffit and stays HELD while no specification prints
whether plaster runs above the ceiling. Both are carried side by side: the owner-method figure on the line, the HELD
band range beside it on the same line (calculation.inputs, formula, notes), never the band as 0 and never the backing
alone presented as the room's whole plaster. The coat's mortar (m2 x thickness) is procurement of the SAME layer,
never a second quantity.

  FILL    a candidate FIN.PLASTER line that carries no figure (BLOCKED_RFI) takes the ledger figure, same line id: the
          sum of the backing faces (each = the tile face of the same id: length x tile top - its openings' parts) plus
          the owner-method band. Its faces must be EXACTLY the faces of the room's valued FIN.WALL.TILE line in the run
          (same ids, lengths, heights, openings and nets): a face missing, extra, or different is refused. The line
          carries gross (sum of length x height), its canonical deductions (each opening by id and m2, unit m2, so
          gross - deductions = net) and the band record. State PROVISIONAL, evidence ASSUMED - OWNER-APPROVED with its
          owner sources on the line (WORKFLOW_CONTROLS s.4), or DRAWING-CONFIRMED / VERIFIED where the record says so.
  HELD    a candidate FIN.PLASTER line of a room whose tile line is itself held (its height not established) stays
          BLANK with its named item (never 0): only its note and a calculation record (reason, drawing band range)
          are added.
  KEEP    a superseded room record (NOT_APPLICABLE_WITH_EVIDENCE) named by the ledger is asserted to stay as it is.
  NOTE    a note on a line of an earlier version that was cut short is completed from the full text the line itself
          carries in calculation.inputs (the cut fragment must be its exact prefix): notes only.

Refused (InputsError / ValueError, nothing written): a record whose line the run does not carry, or that is not a
blank FIN.PLASTER line of its engine room (stale ledger, or a paint / dry line named); a line named twice; a room in two
records; a face in two records; an opening twice in one room; a face net that is not length x height - openings
(> 1e-4 m2); a record value that is not the sum of its faces plus its owner band (> 0.006 m2); a height outside
1.0 .. 6.0 m (mm or a typo) or without its source; a FILL whose tile line is blank or not a FIN.WALL.TILE line of the
same engine room, or whose faces differ from that tile line's faces; a band that is missing, a bare number, a range
the faces do not sum to, or a drawing range wider than the owner figure that is not HELD; a HELD record with a figure,
or whose tile line carries one; a VERIFIED record without the checker run; a figure on a paint line of a room whose
faces are all backed (paint never over porcelain, UP-FIN-PAINT-001: 0 by rule, the rule named); a tiled room of the
run with no record (the family is integrated whole). Inside a FILL line only quantity, state, rfi, gross, deductions,
geometry confidence, calculation and notes change; inside a HELD / NOTE line only notes and calculation; every other
line is byte-identical to V3.0.21 (asserted), including the project identity block; the merged default guard runs
again over the result (arch_v307.guard_changes) and may not flag a line this version fills.

Files: V3_0_22_BOQ_LINES.json / .csv, V3_0_22_INTEGRATION_LEDGER.json / .csv (per line: before V3.0.21, after,
released V2.9, faces, owner manual method beside the drawing-derived method and the HELD band, status, source task /
merge / checker run), V3_0_22_FACES.csv (every backing face once: plaster line, tile line, length, height, openings,
net, tile net, closure, band), V3_0_22_CROSS_TRADE.csv (per room: tile line + backing line = two layers by rule, paint
lines 0 by rule), V3_0_22_DIFF.csv (every line against V3.0.21 and the released V2.9), V3_0_22_RUN.json. Nothing here
names a project, a sheet, a layer or a coordinate: every value comes from the inputs.
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
from engine.source import arch_v3021 as A3021

DEFAULT_GUARD_CLASS = "GUARD_HOST"      # T-212: it fills valued lines; it reaches the guard through arch_v307
METHOD = "ARCH_TAKEOFF_V3.0.22"
EXTENDS = A3021.METHOD
CANDIDATE = A30.METHOD
POLICY_ID = "URBAN_BOQ_T331_ARCH_V3_0_22"
INPUTS_SCHEMA = "URBAN_V3022_INPUTS_V1"
LEDGER_SCHEMA = "URBAN_V3022_INTEGRATION_LEDGER_V1"
ROLLBACK = A30.ROLLBACK
VER, DC, OA = A3018.VER, A3018.DC, A3018.OA
InputsError = A3015.InputsError
_num = A3015._num
_r = A3018._r
TOL = 1e-6
FACE_TOL_M2 = A3021.FACE_TOL_M2         # 1e-4 m2: a face net vs length x height - openings (4-decimal ledgers)
NET_TOL_M2 = A309.NET_TOL_M2            # 0.006 m2: a record value vs the sum of its faces
DED_TOL = 5e-4                          # gross - canonical deductions vs net (tools/boq_export_v1 QTY_MATCH_TOL)
H_MIN, H_MAX = A3021.H_MIN, A3021.H_MAX
PLASTER = "FIN.PLASTER"
TILE = A3021.TILE
PAINT_CODES = A3021.PAINT_CODES
KINDS = ("FILL", "HELD")
QTY_STATUS = (VER, DC, OA)
HELD_STATUS = ("HELD", "UNKNOWN")
KEEP_STATE = "NOT_APPLICABLE_WITH_EVIDENCE"
RULE = ("R-WET-BACKING-1", "T-331")
FILL_KEYS = ("evidence_state", "measured_net", "bounded_range", "rfi", "notes", "gross", "deductions", "calculation")
NOTE_KEYS = ("notes", "calculation")

PIECES = {
    "WET_ROOM_PLASTER_BACKING": {
        "module": "engine/source/arch_v3022.py (the plaster backing behind the wall tile carried face by face from a "
                  "checker-merged ledger, bound to the room's own wall-tile line)",
        "policy": "WET_ROOM_PLASTER_BACKING_V1", "rule_id": RULE[0], "rule_version": RULE[1],
        "owner_rules": ["UP-FIN-PAINT-001 (logic 'substrate': the cementitious substrate / plaster behind porcelain is "
                        "its own line; no paint over porcelain)",
                        "Q-45 B (wall mortar behind wall tiles 0.02 m, mix 1:4: PROVISIONAL practice value; adhesive its "
                        "own line)",
                        "Q-43 (plaster height GF 3.65, 1F / 2F 3.35) = Q-48 A (wall tile to the underside of the 0.15 "
                        "decor ceiling): owner plaster top = tile top, band 0",
                        "Q-55 C (door head 2.20 where none is printed)",
                        "Q-52 C MODIFIED (plaster and paint heights per room; plaster may run above the false ceiling "
                        "depending on the specification: the drawing-derived band stays HELD)",
                        "UP-FIN-PLASTER-001", "UP-HGT-001", "UP-QTY-STATUS-001 (held never 0)",
                        "WORKFLOW_CONTROLS 2026-10-21 s.4 / s.5"],
        "owner_manual_method": "manual QS take-off of the wet-wall backing coat: the tiled faces of the room, each face "
                               "length x the owner plaster height of the floor (Q-43, = the tile top Q-48 A), less "
                               "every door (head 2.20 where none is printed, Q-55 C) and window by its part inside the "
                               "height; one line per room; the band above the tile = 0 when plaster and tile share the "
                               "height",
        "drawing_method": "the same tiled faces with the plaster taken to the drawn slab soffit and the tile to the "
                          "underside of the decor ceiling: the band above the tile is the decor zone x face length, "
                          "HELD (no specification prints whether plaster runs above the ceiling; the beam faces on the "
                          "wall line in that band are not split); shown beside on the line, never used as its figure"},
    "NOTE_COMPLETION": {
        "module": "engine/source/arch_v3022.py (a cut note completed from the line's own calculation record)",
        "policy": "NOTE_COMPLETION_V1", "rule_id": RULE[0], "rule_version": RULE[1],
        "owner_rules": ["UP-QA-001 (a line states its basis in full)"],
        "owner_manual_method": "not a quantity: the note text only",
        "drawing_method": "not a quantity: the note text only"},
    "DEFAULT_GUARD": A307.PIECES["DEFAULT_GUARD"],
}
WAITING = dict(A3021.WAITING)
WAITING.pop("WALL_TILE_BACKING", None)        # carried here
WAITING.update({
    "WET_BACKING_HELD_ROOMS": "plaster backing of the rooms whose wall-tile height is not established (annex rooms: "
                              "G2 / Q-54 B / D-39; rooms with an undrawn level: T-088): the lines stay BLANK with the "
                              "tile, never 0",
    "WET_BACKING_BAND_SPECIFICATION": "the band of plaster between the tile top and the drawn soffit: owner method 0 "
                                      "(Q-43 = Q-48 A), drawing-derived 0 .. high HELD per line until a specification "
                                      "prints whether plaster runs above the decor ceiling (Q-52 C)",
    "WET_WALL_SPATTER_DASH": "the spatter-dash coat on wet walls is a separate item "
                             "(URBAN-FINISH-EXTRAS-SEPARATE-ITEMS@v1): its carrier is not settled here",
    "WET_OPENING_REVEALS": "reveal surfaces of wet-room openings stay with the reveal ledgers (T-313 / T-326)",
})


# ================================================================================================ inputs
def _check_band(band, faces, where):
    """the band above the tile: {owner_m2 >= 0, owner_basis, drawing_low, drawing_high, status, reason}; the drawing
    range is the sum of the faces' band ranges. -> owner m2"""
    if band is None or isinstance(band, (int, float)) or not isinstance(band, dict):
        raise InputsError(f"{where}: the band above the tile is a record {{owner_m2, owner_basis, drawing_low, "
                          "drawing_high, status, reason}} beside the figure, never a bare number and never omitted")
    om, lo, hi = band.get("owner_m2"), band.get("drawing_low"), band.get("drawing_high")
    if not (_num(om) and om >= 0 and band.get("owner_basis")):
        raise InputsError(f"{where}: band owner_m2 >= 0 with its owner_basis")
    if not (_num(lo) and _num(hi) and 0 <= lo <= hi):
        raise InputsError(f"{where}: band drawing range 0 <= drawing_low <= drawing_high")
    if hi > lo + TOL and (band.get("status") not in HELD_STATUS or not band.get("reason")):
        raise InputsError(f"{where}: a band range is HELD with its reason (never released, never written as 0)")
    if faces is not None:
        s_lo = sum(f["band_dwg"][0] for f in faces)
        s_hi = sum(f["band_dwg"][1] for f in faces)
        s_om = sum(f["band_owner_m2"] for f in faces)
        if abs(s_lo - lo) > 1e-3 or abs(s_hi - hi) > 1e-3 or abs(s_om - om) > 1e-3:
            raise InputsError(f"{where}: band owner {om} / drawing {lo} .. {hi} != its faces {round(s_om, 4)} / "
                              f"{round(s_lo, 4)} .. {round(s_hi, 4)} (the band written as 0, or edited)")
    return om


def _check_faces(faces, where, seen_faces):
    """the backing faces of one FILL record. -> (sum of nets, gross, deductions [{opening_id, area, unit, face}])"""
    if not faces:
        raise InputsError(f"{where}: a FILL record lists its backing faces (each face once)")
    tot, gross, deds, opened = 0.0, 0.0, [], set()
    for f in faces:
        fid = f.get("face_id")
        w = f"{where} face {fid}"
        if not fid:
            raise InputsError(f"{where}: every face names its face_id")
        if fid in seen_faces:
            raise InputsError(f"{w}: the face is backed twice (each tiled face in exactly one plaster line)")
        seen_faces.add(fid)
        ln, h, corr = f.get("length_m"), f.get("height_m"), bool(f.get("correction"))
        if corr:
            if not (_num(ln) and ln != 0 and f.get("basis")) or f.get("openings"):
                raise InputsError(f"{w}: a closure correction names its basis, carries a length != 0 and no opening")
        elif not (_num(ln) and ln > 0):
            raise InputsError(f"{w}: length_m > 0 (a missing length is HELD, never 0)")
        if not _num(h) or not (H_MIN <= h <= H_MAX):
            raise InputsError(f"{w}: height {h} m is outside {H_MIN} .. {H_MAX} m (mm, a typo or missing)")
        if not f.get("height_source"):
            raise InputsError(f"{w}: the height names its source (owner rule or printed value), never a default")
        g, sub = ln * h, 0.0
        for o in f.get("openings") or ():
            oid, m2 = o.get("id"), o.get("m2")
            if not oid:
                raise InputsError(f"{w}: an opening names its id")
            if oid in opened:
                raise InputsError(f"{w}: opening {oid} deducted twice in this room (once per room side)")
            opened.add(oid)
            if not (_num(m2) and 0 < m2 <= g + TOL):
                raise InputsError(f"{w}: opening {oid} deducts its part inside the height, 0 < m2 <= the face")
            sub += m2
            deds.append({"opening_id": oid, "area": _r(m2, 4), "unit": "m2", "face": fid})
        net = f.get("net_m2")
        if not (_num(net) and (net > 0 or corr)) or abs(net - (g - sub)) > FACE_TOL_M2:
            raise InputsError(f"{w}: net {net} != {ln} x {h} - {round(sub, 4)} = {round(g - sub, 4)}")
        tn = f.get("tile_net_m2")
        if not _num(tn) or abs(tn - net) > FACE_TOL_M2:
            raise InputsError(f"{w}: backing {net} != tile {tn} on the same face (backing - tile = 0)")
        b = f.get("band_dwg")       # a closure correction carries its (negative) band part as [0, its part]
        if not (isinstance(b, (list, tuple)) and len(b) == 2 and all(_num(x) for x in b) and
                (0 <= b[0] <= b[1] or (corr and b[0] == 0 and b[1] * ln >= 0))) or \
                not (_num(f.get("band_owner_m2")) and f["band_owner_m2"] >= 0):
            raise InputsError(f"{w}: band_owner_m2 >= 0 and band_dwg [low, high] on every face (never omitted)")
        tot += net
        gross += g
    return tot, gross, deds


def _check_record(r, where, tasks, seen_faces):
    k = r.get("kind")
    if k not in KINDS:
        raise InputsError(f"{where}: kind {k!r} not one of {KINDS}")
    for x in ("line_id", "tile_line_id", "room", "engine_room", "floor", "task", "evidence_status"):
        if not r.get(x):
            raise InputsError(f"{where}: {x} required")
    if r["task"] not in tasks:
        raise InputsError(f"{where}: task {r['task']!r} is not one of the sources {sorted(tasks)}")
    if k == "HELD":
        for x in ("value", "faces"):
            if r.get(x) not in (None, [], ()):
                raise InputsError(f"{where}: a HELD record carries no figure ({x}): BLANK in the BOQ, never 0")
        if r["evidence_status"] not in HELD_STATUS or not r.get("reasons"):
            raise InputsError(f"{where}: a HELD record names why (reasons) and its status {HELD_STATUS}")
        _check_band(r.get("band"), None, where)
        return None
    v = r.get("value")
    if not (_num(v) and v > 0):
        raise InputsError(f"{where}: a FILL record carries a value > 0 (a missing one is HELD, never 0)")
    if r["evidence_status"] not in QTY_STATUS:
        raise InputsError(f"{where}: a valued record is one of {QTY_STATUS}")
    if r["evidence_status"] == VER and not r.get("verified_by"):
        raise InputsError(f"{where}: VERIFIED names the checker run")
    if r["evidence_status"] == OA and not r.get("assumption"):
        raise InputsError(f"{where}: ASSUMED - OWNER-APPROVED carries its owner sources on the line "
                          "(WORKFLOW_CONTROLS s.4)")
    tot, gross, deds = _check_faces(r.get("faces") or [], where, seen_faces)
    om = _check_band(r.get("band"), r["faces"], where)
    if abs(tot + om - v) > NET_TOL_M2:
        raise InputsError(f"{where}: value {v} != its faces {round(tot, 4)} + owner band {om}")
    return tot, gross, deds


def load_inputs(doc, project_id=None):
    """URBAN_V3022_INPUTS_V1 or None:
        {"schema", "project", "sources": [{file, sha256, task, merge_commit, checker_run}],
         "records": [{kind FILL | HELD, line_id, tile_line_id, room, engine_room, floor, task, evidence_status, value,
                      assumption, verified_by, reasons, band {owner_m2, owner_basis, drawing_low, drawing_high,
                      status, reason}, faces [{face_id, wall_id, length_m, height_m, height_source, openings [{id, m2}],
                      net_m2, tile_net_m2, band_owner_m2, band_dwg [low, high], correction, basis}], info, downstream}],
         "keep": [{line_id, task, why}], "note_fixes": [{line_id, task, field}],
         "declared": {"FILL": {"lines", "m2"}, "HELD": {"lines"}},
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
    seen_lines, seen_tiles, seen_faces, seen_rooms = set(), set(), set(), set()
    tot = {k: {"lines": 0, "m2": 0.0} for k in KINDS}
    for i, r in enumerate(recs):
        where = f"record {r.get('line_id') or r.get('room') or i}"
        for key, seen, what in (("line_id", seen_lines, "line named twice"),
                                ("tile_line_id", seen_tiles, "tile line bound twice (one backing line per tile line)"),
                                ("room", seen_rooms, "room in two records (one plaster line per room)")):
            if r.get(key) in seen:
                raise InputsError(f"{where}: {what}")
            seen.add(r.get(key))
        res = _check_record(r, where, tasks, seen_faces)
        tot[r["kind"]]["lines"] += 1
        if res is not None:
            tot[r["kind"]]["m2"] += r["value"]
    for i, kp in enumerate(doc.get("keep") or ()):
        if not (kp.get("line_id") and kp.get("why") and kp.get("task") in tasks) or kp["line_id"] in seen_lines:
            raise InputsError(f"keep {i}: {{line_id (not also a record), task (a source), why}}")
        seen_lines.add(kp["line_id"])
    for i, nf in enumerate(doc.get("note_fixes") or ()):
        if not (nf.get("line_id") and nf.get("field") and nf.get("task")) or nf["line_id"] in seen_lines:
            raise InputsError(f"note fix {i}: {{line_id (named once), task, field (the calculation record holding the "
                              "full text)}}")
        seen_lines.add(nf["line_id"])
    dec = doc.get("declared") or {}
    for k in KINDS:
        d = dec.get(k) or {"lines": 0, "m2": 0.0}
        if d.get("lines", 0) != tot[k]["lines"] or (k == "FILL" and abs(d.get("m2", 0.0) - tot[k]["m2"]) > 1e-4):
            raise InputsError(f"declared {k} {d} != the records' {tot[k]['lines']} lines / {round(tot[k]['m2'], 4)} m2")
    g = doc.get("guard")
    if g is not None:
        A307.load_inputs({"schema": A307.INPUTS_SCHEMA, "project": doc.get("project"), "guard": g}, project_id)
    return doc


# ================================================================================================ lines
def _room_id(ln):
    return (ln.get("location") or {}).get("room_id")


def _floor(ln):
    return (ln.get("location") or {}).get("floor")


def _assert_blank_plaster(ln, r, where):
    if ln is None:
        raise InputsError(f"{where}: the run carries no line {r['line_id']}")
    if ln["item_code"] != PLASTER:
        raise InputsError(f"{where}: line {r['line_id']} is {ln['item_code']}, not {PLASTER} (the backing is a plaster "
                          "line: never on a paint or tile line)")
    if _room_id(ln) != r["engine_room"] or _floor(ln) != r["floor"]:
        raise InputsError(f"{where}: the line is in {_room_id(ln)!r} {_floor(ln)}, the record {r['engine_room']!r} "
                          f"{r['floor']} (stale ledger, or another room's line)")
    if ln["evidence_state"] != "BLOCKED_RFI" or A309._carried(ln) != A309.NO_FIGURE:
        raise InputsError(f"{where}: line {r['line_id']} is {ln['evidence_state']} carrying {A309._carried(ln)}: only "
                          "a blank plaster line is filled here (stale ledger)")


def _tile_faces(tl):
    return {f["face_id"]: f for f in ((tl.get("calculation") or {}).get("inputs") or {}).get(
        "wall_tile_v3021", {}).get("faces") or ()}


def _assert_tile(tl, r, where):
    """the record's tile line in the run: a FIN.WALL.TILE line of the same engine room and floor; valued with the
    same faces for a FILL, blank for a HELD."""
    if tl is None:
        raise InputsError(f"{where}: the run carries no tile line {r['tile_line_id']}")
    if tl["item_code"] != TILE or _room_id(tl) != r["engine_room"] or _floor(tl) != r["floor"]:
        raise InputsError(f"{where}: {r['tile_line_id']} is {tl['item_code']} in {_room_id(tl)} {_floor(tl)}: not the "
                          f"{TILE} line of {r['engine_room']} {r['floor']}")
    fig = A309._carried(tl)
    if r["kind"] == "HELD":
        if fig != A309.NO_FIGURE:
            raise InputsError(f"{where}: the tile line carries {fig}: a backing held with the tile height while the "
                              "tile is valued is stale")
        return
    if fig == A309.NO_FIGURE or isinstance(fig, list):
        raise InputsError(f"{where}: the tile line {r['tile_line_id']} carries no figure: the backing of a held tile "
                          "face is HELD with it (a held line is never filled)")
    tf = _tile_faces(tl)
    bf = {f["face_id"]: f for f in r["faces"]}
    if set(tf) != set(bf):
        raise InputsError(f"{where}: backing faces != the tile line's faces (missing {sorted(set(tf) - set(bf))[:4]}, "
                          f"extra {sorted(set(bf) - set(tf))[:4]}): the coat lies on exactly the tiled faces")
    for fid, t in tf.items():
        b = bf[fid]
        same = (abs(t["length_m"] - _r(b["length_m"], 4)) <= 1e-9 and abs(t["height_m"] - _r(b["height_m"], 4)) <= 1e-9
                and abs(t["net_m2"] - _r(b["net_m2"], 4)) <= 1e-9
                and sorted((o["id"], o["m2"]) for o in t.get("openings") or ()) ==
                sorted((o["id"], _r(o["m2"], 4)) for o in b.get("openings") or ()))
        if not same:
            raise InputsError(f"{where}: face {fid} differs from the tile line's face (length / height / openings / net)")
    if abs(tl["measured_net"] - sum(f["net_m2"] for f in r["faces"])) > NET_TOL_M2:
        raise InputsError(f"{where}: the faces sum {round(sum(f['net_m2'] for f in r['faces']), 4)} != the tile line "
                          f"{tl['measured_net']}")


def _faces_rec(r):
    return [{"face_id": f["face_id"], "wall_id": f.get("wall_id"), "length_m": _r(f["length_m"], 4),
             "height_m": _r(f["height_m"], 4), "height_source": f["height_source"][:200],
             "openings": [{"id": o["id"], "m2": _r(o["m2"], 4)} for o in f.get("openings") or ()],
             "net_m2": _r(f["net_m2"], 4), "tile_net_m2": _r(f["tile_net_m2"], 4),
             "closure_m2": _r(f["net_m2"] - f["tile_net_m2"], 4), "band_owner_m2": _r(f["band_owner_m2"], 4),
             "band_dwg": [_r(f["band_dwg"][0], 4), _r(f["band_dwg"][1], 4)],
             "correction": (f.get("basis") or "")[:300] if f.get("correction") else None} for f in r.get("faces") or ()]


def _band_rec(r):
    b = r["band"]
    return {"owner_method_m2": _r(b["owner_m2"], 4), "owner_basis": b["owner_basis"][:300],
            "drawing_derived_m2": {"low": _r(b["drawing_low"], 4), "high": _r(b["drawing_high"], 4)},
            "status": b.get("status") or ("DETERMINATE" if b["drawing_high"] <= b["drawing_low"] + TOL else None),
            "reason": (b.get("reason") or "")[:400], "release_status": "NOT RELEASED"}


def _band_text(r):
    b = r["band"]
    return (f"band above the tile: owner method {_r(b['owner_m2'], 4)} m2 ({b['owner_basis']}); drawing-derived "
            f"{_r(b['drawing_low'], 4)} .. {_r(b['drawing_high'], 4)} m2 {b.get('status') or ''}".strip())


def _rec(r, src):
    p = PIECES["WET_ROOM_PLASTER_BACKING"]
    return {"policy": p["policy"], "kind": r["kind"], "task": src["task"], "ledger": src["file"],
            "ledger_sha256": src["sha256"], "merge_commit": src["merge_commit"], "checker_run": src["checker_run"],
            "room": r["room"], "tile_line_id": r["tile_line_id"], "band_above_tile": _band_rec(r),
            "faces": _faces_rec(r), "rule_id": RULE[0], "rule_version": RULE[1]}


def filled_line(before, r, src, gross, deds):
    """the line of one FILL record (same line id). -> line"""
    from engine.source import boq_line as BL
    ln = copy.deepcopy(before)
    inp = ln["calculation"].setdefault("inputs", {})
    ln["evidence_state"] = A3018.STATE_OF[r["evidence_status"]]
    ln["measured_net"] = _r(r["value"])
    ln["bounded_range"] = None
    ln["rfi"] = None
    ln["gross"] = _r(gross)
    ln["deductions"] = [dict(d) for d in deds]
    ln["source"]["geometry_confidence"] = "TOLERANCE_CERTIFIED"
    inp["owner_manual_method"] = {"gross": _r(gross, 4), "deductions": deds, "band_above_tile_m2":
                                  _r(r["band"]["owner_m2"], 4), "net": _r(r["value"], 4),
                                  "height_basis": sorted({f["height_source"][:200] for f in r["faces"]})}
    inp["drawing_derived_method"] = r.get("drawing_derived_method")
    inp["record_state"] = "FILL"
    inp["evidence_status"] = r["evidence_status"]
    inp["verified_by"] = r.get("verified_by")
    inp["assumption"] = r.get("assumption")
    inp["wet_backing_v3022"] = dict(_rec(r, src), before=A3018._before_rec(before))
    ln["calculation"]["formula"] = (f"{METHOD}: backing behind the wall tile = sum of {len(r['faces'])} tiled faces "
                                    f"(length x tile top - openings, = tile line {r['tile_line_id']}) "
                                    f"{_r(r['value'] - r['band']['owner_m2'], 4)} + owner band "
                                    f"{_r(r['band']['owner_m2'], 4)} = {_r(r['value'], 4)} m2; {_band_text(r)}")[:600]
    A305._note(ln, f"{METHOD}: plaster backing under the wall tile from the merged ledger ({src['task']}, MERGED "
                   f"{src['merge_commit'][:8]}): {r['evidence_status']} ({r.get('assumption') or ''}); "
                   f"{_band_text(r)}; paint on these faces 0 by rule (UP-FIN-PAINT-001)")
    return BL.validate(ln)


def held_line(before, r, src):
    """the line of one HELD record: still BLANK, its reason and band recorded. -> line"""
    from engine.source import boq_line as BL
    ln = copy.deepcopy(before)
    ln["calculation"].setdefault("inputs", {})["wet_backing_v3022"] = dict(
        _rec(r, src), reasons=list(r["reasons"]), before=A3018._before_rec(before))
    A305._note(ln, f"{METHOD}: plaster backing under the wall tile is its own line (UP-FIN-PAINT-001 substrate, Q-45 B)"
                   f"; HELD with the tile height, BLANK, never 0: {'; '.join(r['reasons'])[:300]}; {_band_text(r)}")
    return BL.validate(ln)


def note_line(before, nf):
    """a cut note completed from the line's own calculation record. -> line"""
    from engine.source import boq_line as BL
    rec = ((before.get("calculation") or {}).get("inputs") or {}).get(nf["field"]) or {}
    full = rec.get("assumption") or ""
    notes = before.get("notes") or ""
    n = len(full)
    cut = None
    for k in range(n - 1, 39, -1):          # the longest proper prefix of the full text that ends the cut fragment
        if notes.count(full[:k] + ")") == 1 and full[:k] + ")" not in full:
            cut = full[:k]
            break
    if not full or cut is None or notes.count(full) > 0:
        raise InputsError(f"note fix {before['line_id']}: no cut prefix of {nf['field']}.assumption in the notes "
                          "(nothing cut, or already complete)")
    ln = copy.deepcopy(before)
    ln["notes"] = notes.replace(cut + ")", full + ")", 1)
    ln["calculation"].setdefault("inputs", {})["note_completion_v3022"] = {
        "policy": PIECES["NOTE_COMPLETION"]["policy"], "task": nf["task"], "field": f"{nf['field']}.assumption",
        "cut_at_chars": len(cut), "full_chars": n}
    return BL.validate(ln)


def _tiled_rooms(lines):
    return {(_room_id(ln), _floor(ln)) for ln in lines if ln["item_code"] == TILE}


def family_changes(doc, l3021):
    """-> (changes, log, face rows)."""
    by = {ln["line_id"]: ln for ln in l3021}
    tiles = {ln["line_id"] for ln in l3021 if ln["item_code"] == TILE}
    bound = {r["tile_line_id"] for r in doc["records"]}
    missing = sorted(tiles - bound)
    if missing:
        raise InputsError(f"{len(missing)} {TILE} line(s) of the run with no backing record (the family is integrated "
                          f"whole: FILL or HELD each): {missing[:5]}")
    changes, faces_out = [], []
    log = {"piece": "WET_ROOM_PLASTER_BACKING", "state": "RUN", "sources": doc["sources"], "kinds": {}, "m2": {},
           "band_owner_m2": 0.0, "band_drawing_m2": {"low": 0.0, "high": 0.0}}
    for r in doc["records"]:
        where = f"record {r['line_id']} ({r['room']})"
        src = A3018._src_of(doc, r["task"])
        k = r["kind"]
        log["kinds"][k] = log["kinds"].get(k, 0) + 1
        b = by.get(r["line_id"])
        _assert_blank_plaster(b, r, where)
        _assert_tile(by.get(r["tile_line_id"]), r, where)
        log["band_drawing_m2"]["low"] = _r(log["band_drawing_m2"]["low"] + r["band"]["drawing_low"], 4)
        log["band_drawing_m2"]["high"] = _r(log["band_drawing_m2"]["high"] + r["band"]["drawing_high"], 4)
        ver = {"task": src["task"], "merge_commit": src["merge_commit"], "verifier_run": src["checker_run"],
               "ledger": src["file"], "ledger_sha256": src["sha256"], "record_verified_by": r.get("verified_by")}
        if k == "HELD":
            after = held_line(b, r, src)
            changes.append(A305._change("WET_ROOM_PLASTER_BACKING", "REPLACE", b, after, drawing_reference=src["file"],
                                        held=[{"what": f"{PLASTER} {r['room']}", "why": "; ".join(r["reasons"])[:900]}],
                                        downstream=list(r.get("downstream") or ()), verification=ver,
                                        evidence_status=r["evidence_status"], codes=["WET_ROOM_PLASTER_BACKING", k],
                                        group=r["room"], record=r))
            continue
        _tot, gross, deds = _check_faces(r["faces"], where, set())
        after = filled_line(b, r, src, gross, deds)
        log["m2"][k] = _r(log["m2"].get(k, 0.0) + r["value"], 4)
        log["band_owner_m2"] = _r(log["band_owner_m2"] + r["band"]["owner_m2"], 4)
        changes.append(A305._change("WET_ROOM_PLASTER_BACKING", "REPLACE", b, after, drawing_reference=src["file"],
                                    held=[{"what": f"band above the tile, {r['room']}",
                                           "why": f"{_band_text(r)}: {(r['band'].get('reason') or '')[:300]}"}],
                                    downstream=[d if isinstance(d, dict) else {"item": d}
                                                for d in r.get("downstream") or ()],
                                    verification=ver, evidence_status=r["evidence_status"],
                                    codes=["WET_ROOM_PLASTER_BACKING", k], group=r["room"], record=r,
                                    guard_element={"element_id": after["location"]["element_id"], "part": "WHOLE"}))
        for f in _faces_rec(r):
            faces_out.append(dict(f, room=r["room"], engine_room=r["engine_room"], floor=r["floor"],
                                  line_id=r["line_id"], tile_line_id=r["tile_line_id"], kind=k,
                                  evidence_status=r["evidence_status"]))
    return changes, log, faces_out


def keep_and_notes(doc, l3021):
    """-> changes of the note fixes; the kept lines are asserted."""
    by = {ln["line_id"]: ln for ln in l3021}
    for kp in doc.get("keep") or ():
        ln = by.get(kp["line_id"])
        if ln is None or ln["item_code"] != PLASTER or ln["evidence_state"] != KEEP_STATE:
            raise InputsError(f"keep {kp['line_id']}: not a {KEEP_STATE} {PLASTER} line of the run (stale ledger)")
    ch = []
    for nf in doc.get("note_fixes") or ():
        ln = by.get(nf["line_id"])
        if ln is None:
            raise InputsError(f"note fix {nf['line_id']}: the run carries no such line")
        after = note_line(ln, nf)
        ch.append(A305._change("NOTE_COMPLETION", "REPLACE", ln, after, drawing_reference=None, held=[],
                               downstream=[], verification={"task": nf["task"]}, evidence_status=None,
                               codes=["NOTE_COMPLETION"], group=nf["line_id"]))
    return ch


def cross_trade(lines, doc):
    """per record: the tile line and the backing line (two layers by rule), the paint lines of the room (0 by rule).
    A paint figure in the engine room of a FILL record whose ledger room is the record's room (or names none) is
    refused: paint never goes over porcelain (UP-FIN-PAINT-001)."""
    by = {ln["line_id"]: ln for ln in lines}
    rows = []
    for r in doc["records"]:
        paint = [ln for ln in lines if ln["item_code"] in PAINT_CODES and _room_id(ln) == r["engine_room"]
                 and _floor(ln) == r["floor"]
                 and ((ln.get("calculation") or {}).get("inputs") or {}).get("room") in (None, r["room"])]
        for ln in paint:
            fig = A309._carried(ln)
            if r["kind"] == "FILL" and fig != A309.NO_FIGURE:
                raise ValueError(f"{METHOD}: paint line {ln['line_id']} of backed room {r['room']} carries {fig}: no "
                                 "paint over porcelain (UP-FIN-PAINT-001)")
        tl, pl = by[r["tile_line_id"]], by[r["line_id"]]
        rows.append({"room": r["room"], "engine_room": r["engine_room"], "floor": r["floor"], "kind": r["kind"],
                     "tile_line": tl["line_id"], "tile": f"{tl['evidence_state']} {A309._carried(tl)}",
                     "backing_line": pl["line_id"], "backing": f"{pl['evidence_state']} {A309._carried(pl)}",
                     "layers": "tile + backing on one face = two layers by rule (UP-FIN-PAINT-001 substrate): "
                               "never one quantity",
                     "paint_lines": "; ".join(f"{x['line_id']} {x['evidence_state']} {A309._carried(x)}" for x in paint),
                     "paint": "0 BY RULE (UP-FIN-PAINT-001: no paint over porcelain), not by omission",
                     "band": _band_text(r), "mortar": "the coat's mortar is procurement of the same layer, never a "
                                                      "second quantity"})
    return rows


def check_backing_family(lines, doc):
    """every bound plaster line: valued > 0 with gross - deductions = net, or BLANK (no figure, no range)."""
    by = {ln["line_id"]: ln for ln in lines}
    out = {"lines": 0, "valued": 0, "blank": 0, "m2": 0.0}
    for r in doc["records"]:
        ln = by[r["line_id"]]
        out["lines"] += 1
        if r["kind"] == "FILL":
            if not (ln.get("measured_net") or 0) > 0:
                raise ValueError(f"{METHOD}: {ln['line_id']} carried at 0")
            ded = sum(d["area"] for d in ln["deductions"])
            if abs(ln["gross"] - ded + r["band"]["owner_m2"] - ln["measured_net"]) > DED_TOL:
                raise ValueError(f"{METHOD}: {ln['line_id']} gross {ln['gross']} - deductions {round(ded, 4)} + owner "
                                 f"band != net {ln['measured_net']}")
            out["valued"] += 1
            out["m2"] += ln["measured_net"]
        else:
            if ln["evidence_state"] != "BLOCKED_RFI" or ln.get("measured_net") is not None or \
                    ln.get("bounded_range") is not None:
                raise ValueError(f"{METHOD}: held backing line {ln['line_id']} carries a figure")
            out["blank"] += 1
    out["m2"] = _r(out["m2"], 4)
    return out


def changes_for(doc, l3021):
    """-> (changes, logs, face rows). The guard re-check runs over the result (arch_v307)."""
    if not doc:
        return [], [{"piece": "WET_ROOM_PLASTER_BACKING", "state": "NO_PROJECT_INPUT"}], []
    ch, log, faces = family_changes(doc, l3021)
    nch = keep_and_notes(doc, l3021)
    log["note_fixes"] = [c["before"]["line_id"] for c in nch]
    ch = ch + nch
    rep = {c["before"]["line_id"]: c["after"] for c in ch}
    view = [rep.get(ln["line_id"], ln) for ln in l3021]
    ch_g, log_g = A307.guard_changes(doc, view, [], set(rep))
    for c in ch_g:
        lid = c["before"]["line_id"]
        if lid in rep:
            raise ValueError(f"{METHOD}: the guard flags a line this version fills ({lid})")
        A305._note(c["after"], f"(re-check run by {METHOD})")
    return ch + ch_g, [log, log_g], faces


# ================================================================================================ integrate / write
def integrate(l3021, changes, doc=None):
    """-> (V3.0.22 lines, identity). Every line outside the V3.0.22 rows is byte-identical to the V3.0.21 line."""
    from engine.source import boq_line as BL
    sid = {ln["line_id"] for ln in l3021}
    rep, pieces, kinds = {}, {}, {}
    for c in changes:
        if c["action"] != "REPLACE":
            raise ValueError(f"{METHOD}: action {c['action']} (this version adds no line)")
        lid = c["before"]["line_id"]
        if lid in rep or lid not in sid or c["after"]["line_id"] != lid:
            raise ValueError(f"{METHOD}: line {lid}: changed twice, not in V3.0.21, or its id changed")
        if c["piece"] == "WET_ROOM_PLASTER_BACKING" and c["before"]["item_code"] != PLASTER:
            raise ValueError(f"{METHOD}: the backing piece replaces {PLASTER} lines only ({lid})")
        rep[lid] = c["after"]
        pieces[lid] = c["piece"]
        kinds[lid] = (c.get("codes") or [None, None])[1] if c["piece"] == "WET_ROOM_PLASTER_BACKING" else None
    out = [rep.get(ln["line_id"], ln) for ln in l3021]
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
    tile = A3021.check_tile_family(out)
    fam = check_backing_family(out, doc) if doc else None
    pids = {(ln["project"]["project_id"], ln["project"]["revision_set_sha256"]) for ln in out}
    if len(pids) != 1:
        raise ValueError(f"{METHOD}: {len(pids)} project identities in the lines (one project, one revision set)")
    by21 = {ln["line_id"]: ln for ln in l3021}
    outside = [ln for ln in out if ln["line_id"] not in rep]
    bad = [ln["line_id"] for ln in outside if A30.line_sha(by21[ln["line_id"]]) != A30.line_sha(ln)]
    if bad or len(outside) + len(rep) != len(l3021):
        raise ValueError(f"{METHOD}: {len(bad)} line(s) outside the V3.0.22 rows differ from {EXTENDS}")
    for lid, ln in rep.items():   # inside a row only quantity, state, basis and notes change
        a, b = copy.deepcopy(by21[lid]), copy.deepcopy(ln)
        keys = FILL_KEYS if kinds[lid] == "FILL" else NOTE_KEYS
        for x in (a, b):
            for k in keys:
                x.pop(k, None)
            if kinds[lid] == "FILL":
                x["source"].pop("geometry_confidence", None)
        if json.dumps(a, sort_keys=True) != json.dumps(b, sort_keys=True):
            raise ValueError(f"{METHOD}: line {lid} changed outside quantity / state / basis")
        if kinds[lid] != "FILL":   # a HELD / NOTE line keeps its quantity and state
            if A30._qty(by21[lid]) != A30._qty(ln):
                raise ValueError(f"{METHOD}: line {lid} is a held / note line and changed its quantity")
    ident = {"v3_0_21_lines": len(l3021), "v3_0_22_lines": len(out), "v3_0_22_rows": len(changes),
             "replaced": len(rep), "added": 0, "outside_rows": len(outside),
             "filled": sum(1 for k in kinds.values() if k == "FILL"),
             "held_noted": sum(1 for k in kinds.values() if k == "HELD"),
             "notes_completed": sum(1 for p in pieces.values() if p == "NOTE_COMPLETION"),
             "outside_rows_identical_to_v3_0_21": len(outside), "wet_backing_family": fam,
             "wall_tile_family": tile,
             "outside_rows_sha256": hashlib.sha256("".join(A30.line_sha(x) for x in outside).encode()).hexdigest()}
    return out, ident


def ledger_rows(changes, doc, released_lines=None):
    rel = {A30._key(ln): ln for ln in released_lines or ()}
    rows = []
    for c in changes:
        ref = c["after"]
        b29 = None
        if released_lines is not None:
            b29 = A30._qty(rel[A30._key(ref)]) if A30._key(ref) in rel else dict(A30._qty(None),
                                                                                 state="NOT_IN_RELEASED")
        inp = ref["calculation"]["inputs"]
        wb = inp.get("wet_backing_v3022") or {}
        loc = ref.get("location") or {}
        pp = PIECES.get(c["piece"]) or {}
        r = c.get("record") or {}
        rows.append({"version": METHOD, "piece": c["piece"], "action": c["action"],
                     "kind": (c.get("codes") or [None, None])[1] if c["piece"] == "WET_ROOM_PLASTER_BACKING" else
                     c["piece"], "line_id": ref["line_id"], "item_code": ref["item_code"], "floor": loc.get("floor"),
                     "room": r.get("room") or c.get("group"), "room_id": loc.get("room_id"),
                     "element_id": loc.get("element_id"), "unit": ref["unit"], "tile_line_id": r.get("tile_line_id"),
                     "before_released_v2_9": b29, "before_v3_0_21": A30._qty(c["before"]),
                     "after_v3_0_22": A30._qty(ref), "gross": ref.get("gross") if r.get("kind") == "FILL" else None,
                     "deductions": ref.get("deductions") if r.get("kind") == "FILL" else [],
                     "band_above_tile": wb.get("band_above_tile"), "evidence_status": c.get("evidence_status"),
                     "assumption": r.get("assumption"), "release_status": "NOT RELEASED",
                     "faces": wb.get("faces") or [], "owner_manual_method": inp.get("owner_manual_method")
                     if r.get("kind") == "FILL" else None,
                     "drawing_derived_method": r.get("drawing_derived_method"), "codes": c.get("codes") or [],
                     "owner_rules": pp.get("owner_rules"), "owner_manual_method_text": pp.get("owner_manual_method"),
                     "drawing_method_text": pp.get("drawing_method"),
                     "verification": dict(c.get("verification") or {}, module=pp.get("module"),
                                          policy=pp.get("policy")),
                     "held": c.get("held") or [], "downstream": c.get("downstream") or [], "rollback": ROLLBACK})
    for kp in doc.get("keep") or ():
        rows.append({"version": METHOD, "piece": "WET_ROOM_PLASTER_BACKING", "action": "KEEP", "kind": "KEEP",
                     "line_id": kp["line_id"], "item_code": PLASTER, "floor": None, "room": None, "room_id": None,
                     "element_id": None, "unit": "m2", "tile_line_id": None, "before_released_v2_9": None,
                     "before_v3_0_21": {"state": KEEP_STATE, "value": None, "low": None, "high": None},
                     "after_v3_0_22": {"state": KEEP_STATE, "value": None, "low": None, "high": None},
                     "gross": None, "deductions": [], "band_above_tile": None, "evidence_status": None,
                     "assumption": None, "release_status": "NOT RELEASED", "faces": [], "owner_manual_method": None,
                     "drawing_derived_method": None, "codes": ["WET_ROOM_PLASTER_BACKING", "KEEP"],
                     "owner_rules": None, "owner_manual_method_text": None, "drawing_method_text": None,
                     "verification": {"task": kp["task"]}, "held": [], "downstream": [], "info": kp["why"],
                     "rollback": ROLLBACK})
    return rows


LEDGER_CSV = ("version", "kind", "room", "line_id", "tile_line_id", "item_code", "floor", "unit", "v2_9", "v3_0_21",
              "v3_0_22", "gross", "deductions", "band_owner_m2", "band_drawing_m2", "band_status", "evidence_status",
              "assumption", "release_status", "faces", "held", "verification")
FACES_CSV = ("face_id", "room", "engine_room", "floor", "line_id", "tile_line_id", "kind", "wall_id", "length_m",
             "height_m", "height_source", "openings", "net_m2", "tile_net_m2", "closure_m2", "band_owner_m2",
             "band_dwg", "correction", "evidence_status")
CROSS_CSV = ("room", "engine_room", "floor", "kind", "tile_line", "tile", "backing_line", "backing", "layers",
             "paint_lines", "paint", "band", "mortar")
DIFF_CSV = ("line_id", "item_code", "floor", "element_id", "unit", "vs_v3_0_21", "vs_released_v2_9", "v2_9",
            "v3_0_21", "v3_0_22")


def ledger_csv(rows):
    def _band(r):
        b = r.get("band_above_tile") or {}
        d = b.get("drawing_derived_m2") or {}
        return (b.get("owner_method_m2", ""), f"{d.get('low')} .. {d.get('high')}" if d else "", b.get("status") or "")
    return A305._csv([{"version": r["version"], "kind": r["kind"], "room": r["room"], "line_id": r["line_id"],
                       "tile_line_id": r.get("tile_line_id") or "", "item_code": r["item_code"], "floor": r["floor"],
                       "unit": r["unit"],
                       "v2_9": A302._q(r["before_released_v2_9"]) if r["before_released_v2_9"] else "",
                       "v3_0_21": A302._q(r["before_v3_0_21"]), "v3_0_22": A302._q(r["after_v3_0_22"]),
                       "gross": "" if r.get("gross") is None else r["gross"],
                       "deductions": " ".join(f"{d['opening_id']} {d['area']}" for d in r.get("deductions") or ()),
                       "band_owner_m2": _band(r)[0], "band_drawing_m2": _band(r)[1], "band_status": _band(r)[2],
                       "evidence_status": r["evidence_status"] or "", "assumption": (r.get("assumption") or "")[:200],
                       "release_status": r["release_status"], "faces": len(r["faces"]),
                       "held": "; ".join(h["why"] for h in r["held"])[:300] or (r.get("info") or "")[:300],
                       "verification": f"{r['verification'].get('task')} {r['verification'].get('merge_commit') or ''} "
                                       f"{r['verification'].get('verifier_run') or ''}".strip()} for r in rows],
                     LEDGER_CSV)


def diff_rows(l3021, l3022, released_lines=None):
    b21 = {ln["line_id"]: ln for ln in l3021}
    rel = {A30._key(ln): ln for ln in released_lines or ()}
    out = []
    for ln in l3022:
        o = b21.get(ln["line_id"])
        vs = "ADDED" if o is None else ("SAME" if A30.line_sha(o) == A30.line_sha(ln) else
                                        ("CHANGED" if A30._qty(o) != A30._qty(ln) else "CHANGED_TEXT_ONLY"))
        r = rel.get(A30._key(ln)) if released_lines is not None else None
        vs29 = None if released_lines is None else ("NOT_IN_RELEASED" if r is None else
                                                    ("SAME_QUANTITY" if A30._qty(r) == A30._qty(ln) else
                                                     "QUANTITY_DIFFERS"))
        out.append({"line_id": ln["line_id"], "item_code": ln["item_code"], "floor": ln["location"].get("floor"),
                    "element_id": ln["location"].get("element_id"), "unit": ln["unit"], "vs_v3_0_21": vs,
                    "vs_released_v2_9": vs29, "v2_9": A302._q(A30._qty(r)) if r else "",
                    "v3_0_21": A302._q(A30._qty(o)) if o else "", "v3_0_22": A302._q(A30._qty(ln))})
    return out


def write(out, l3021, changes, logs, faces, doc, released_lines=None):
    """the V3_0_22_* files beside the V3_0_21_* files. -> (file names, identity, ledger)."""
    from pathlib import Path
    from engine.source import boq_line as BL
    out = Path(out)
    l3022, ident = integrate(l3021, changes, doc)
    xrows = cross_trade(l3022, doc)
    rows = ledger_rows(changes, doc, released_lines)
    diff = diff_rows(l3021, l3022, released_lines)
    dsum = {}
    for d in diff:
        dsum.setdefault("vs_v3_0_21", {}).setdefault(d["vs_v3_0_21"], 0)
        dsum["vs_v3_0_21"][d["vs_v3_0_21"]] += 1
        if d["vs_released_v2_9"] is not None:
            dsum.setdefault("vs_released_v2_9", {}).setdefault(d["vs_released_v2_9"], 0)
            dsum["vs_released_v2_9"][d["vs_released_v2_9"]] += 1
    ident = dict(ident, diff=dsum, faces=len(faces), cross_trade_rows=len(xrows))
    t21, t22 = A304.code_totals(l3021), A304.code_totals(l3022)
    moved = {k: {"v3_0_21": t21.get(k), "v3_0_22": t22.get(k)} for k in sorted(set(t21) | set(t22))
             if t21.get(k) != t22.get(k)}
    led = {"schema": LEDGER_SCHEMA, "method": METHOD, "extends": EXTENDS, "candidate": CANDIDATE,
           "base": A30.BASE_METHOD, "released": A30.RELEASED_METHOD, "released_default": False, "rows": rows,
           "faces": faces, "cross_trade": xrows, "waiting_pieces": WAITING, "integration_package": True}
    run = {"method": METHOD, "policy": POLICY_ID, "extends": EXTENDS, "candidate": CANDIDATE,
           "base_method": A30.BASE_METHOD, "released_method": A30.RELEASED_METHOD, "released_default": False,
           "rollback": ROLLBACK, "identity": ident, "pieces": PIECES, "piece_logs": logs,
           "totals_moved_by_code": moved, "waiting_pieces": WAITING,
           "evidence_status_counts": A302._count(r["evidence_status"] or "NONE" for r in rows)}
    files = {"V3_0_22_BOQ_LINES.json": BL.dumps(l3022),
             "V3_0_22_BOQ_LINES.csv": A30._lines_csv(l3022),
             "V3_0_22_INTEGRATION_LEDGER.json": A30._j(led),
             "V3_0_22_INTEGRATION_LEDGER.csv": ledger_csv(rows),
             "V3_0_22_FACES.csv": A305._csv([dict(f, openings=" ".join(f"{o['id']} {o['m2']}" for o in f["openings"]),
                                                  band_dwg=f"{f['band_dwg'][0]} .. {f['band_dwg'][1]}")
                                             for f in faces], FACES_CSV),
             "V3_0_22_CROSS_TRADE.csv": A305._csv(xrows, CROSS_CSV),
             "V3_0_22_DIFF.csv": A305._csv(diff, DIFF_CSV),
             "V3_0_22_RUN.json": A30._j(run)}
    for name, text in files.items():
        (out / name).write_text(text, encoding="utf-8")
    return sorted(files), ident, led


def policy_record():
    return {"method": METHOD, "extends": EXTENDS, "pieces": sorted(PIECES), "inputs_schema": INPUTS_SCHEMA,
            "released_default": False, "rollback": ROLLBACK}


__all__ = ["METHOD", "PIECES", "WAITING", "DEFAULT_GUARD_CLASS", "INPUTS_SCHEMA", "load_inputs", "filled_line",
           "held_line", "note_line", "family_changes", "keep_and_notes", "cross_trade", "check_backing_family",
           "changes_for", "integrate", "ledger_rows", "diff_rows", "write", "InputsError"]
