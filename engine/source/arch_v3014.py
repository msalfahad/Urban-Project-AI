"""ARCH_TAKEOFF_V3.0.14 (T-240, work packages 1 .. 4, the Gate B integration package; renumbered from V3.0.13 after
T-268 merged as V3.0.13, the door-ruling piece this version extends): the SAME opt-in BOQ candidate as
ARCH_TAKEOFF_V3.0 .. V3.0.13 (engine.source.arch_v30, arch_v301 .. arch_v3013), extended with ONE floor-scope piece: every strip and face of the
internal floor line belongs to exactly one line, by its physical class. Not a new method family and not the released
default (owner management decision 2026-10-20 sections 2 and 5); rollback is running the released ARCH_TAKEOFF_V2.9.

The physical question (ERS 2026-10-22 s.2.1, s.3): the internal floor-area line is the finished floor laid inside the
building. Four kinds of plan piece were in the wrong line (checker-merged T-223 / T-218 evidence):
  ENTER_FLOOR   an enclosed interior face reached only from interior spaces, typed from its own evidence (enclosure,
                openings, fixtures, drainage, joinery boxes): its area ENTERS the internal floor line; it is never left
                as an untyped space only. Its finish MATERIAL stays as the record states (HELD unless a material rule
                binds the class; never borrowed from the room it opens into), so the line keeps the item 'space floor
                area (finish to be confirmed)' and carries floor_key FLOOR.INTERNAL;
  TO_THRESHOLD  a doorway strip whose class is a threshold (a lift landing: the landing sill comes with the lift; an
                exterior sill: by specification) leaves the floor line for ONE ARCH.THRESHOLD line: area kept, HELD
                (BOUNDED_EXPOSURE low = high = the strip area), never 0, never dropped; a threshold line already on
                that opening is replaced in place, never a second one;
  TO_OUTDOOR    a face bound EXTERIOR by an answered owner decision (an open-air side passage, Q-67 A) leaves the
                internal key: its pieces are retired and ONE outdoor space line carries the drawn area (floor_key
                FLOOR.OUTDOOR); a piece the engine never measured is added only as the stated difference between the
                drawn area and the retired pieces (named, never silent);
  NO_FLOOR      a 'strip' that is no opening at all (a wall drawn on a non-wall layer read as a gap) and any twin
                line on the same strip are retired: no floor, no threshold;
  TO_WET        (WP2) a dry floor piece classed WET by a binding rule or decision (a pantry with a drain: Q-37 A)
                moves to the wet floor line, area unchanged: a whole line is retired and carried by one wet line; a
                part of a line moves only with its closure (the printed box less every other named piece in it, within
                TOL_CLOSURE) and the dry line keeps the rest;
  NO_OPENING_SPLIT (WP2) a 'strip' that is an edge line carried across an open zone (no opening anywhere along it):
                the strip and its threshold twin are retired and its area is placed part by part where it physically
                lies: COUNTED_IN a TO_OUTDOOR record whose stated missing piece it is (counted once there), NO_FLOOR (a
                wall top), TO_WET (wet floor by a decision) or HELD_WITH (a held zone: area kept, never 0, outside the
                internal line). The parts must add up to the carried strip.
  SETTLE_RANGE  (WP3) a floor line carried as a range [low, high] on held pieces (stair strips) that a checker verdict
                settled from the drawings: every held piece is placed FLOOR or NOT_FLOOR by its own drawn evidence,
                the pieces add up to high - low, the line takes ONE value = low + the FLOOR pieces (never the larger end
                by default); a part of the face with another finish by a binding decision (an arrival landing in
                marble, Q-66 B) leaves the finish line as its own internal space line (area from named terms, counted
                once, the finish line keeps the rest; a residual above TOL_CLOSURE is never absorbed);
  UNDER_STAIR   (WP3) on the LOWEST storey, the tread union a face figure deducts is placed flight by flight by how
                the plan draws it: a flight drawn overhead only with nothing closed under it leaves floor under it (a
                new line in the face's own finish item, the face line unchanged and still net of every tread); a
                flight drawn below the cut is HELD until a section / structural detail fixes where its soffit leaves
                the floor (area kept, never 0, outside the internal line). The flights add up to the deducted union.
Every area is recomputed from the record's printed dimensions and must equal the stated area; every retired line must
carry exactly the figure the record states (the replaced figure is the one the line carries).

How it is built (tools/urban_boq_m9.py `arch --method ARCH_TAKEOFF_V3.0.14`):
  1. the run is the V3.0.13 candidate exactly: its V3_0_* .. V3_0_13_* files are written unchanged (arch_v30 ..
     arch_v3013 are not edited);
  2. FLOOR_SCOPE (project inputs URBAN_V3014_INPUTS_V1): the records above, from checker-merged ledgers (source file
     sha256, task, merge commit, checker run); retired lines become NOT_APPLICABLE_WITH_EVIDENCE with their figure
     kept as information (never deleted, never summed), added lines carry the record and its evidence status;
  3. GUARD RE-CHECK (piece DEFAULT_GUARD): the merged guard runs again over the V3.0.14 lines with the guard inputs of
     V3.0.7 (arch_v307.guard_changes);
  4. the V3_0_14_* files are written beside them: every line outside the V3.0.14 rows is byte-identical to the V3.0.13
     line (asserted on every run), check_one_strip_one_line passes, and V3_0_14_DIFF.csv lists every line against
     V3.0.13 and against the released V2.9; V3_0_14_RUN.json carries the floor-area line by floor_key before / after.

Rules: UP-SPACE-001 / UP-SPACE-002 (interior / exterior from enclosure and connectivity; a project decision binds one
space); proposed UP-SPACE-FACE-TYPE-001 (T-223, unlabelled face typing); UP-DOOR-CLS-005 / UP-ELEV-SCHED-001 (lift
landing sill); UP-THR-001 (dry doorway: the floor continues); Q-67 A (open-air side passage, condition met);
URBAN-FINISH-QUANTITY-INDEPENDENT-OF-MATERIAL@v1 (geometry released without a proven material); defect D-C3 (a doorless
cell never takes a neighbour's scope silently); UP-QTY-STATUS-001 (held is a range or blocked, never 0);
WORKFLOW_CONTROLS 2026-10-21 s.4 / s.5; ERS 2026-10-22 s.2.1 .. s.2.5, s.3, s.7. Nothing here names a project, a
sheet, a layer, a coordinate or a client; every number comes from the run or the inputs.
"""

from __future__ import annotations

import copy
import hashlib
import re

from engine.source import arch_v30 as A30
from engine.source import arch_v302 as A302
from engine.source import arch_v304 as A304
from engine.source import arch_v305 as A305
from engine.source import arch_v307 as A307
from engine.source import arch_v308 as A308
from engine.source import arch_v3010 as A3010
from engine.source import arch_v3011 as A3011
from engine.source import arch_v3012 as A3012
from engine.source import arch_v3013 as A3013

DEFAULT_GUARD_CLASS = "GUARD_HOST"      # T-212: a candidate method; it reaches the guard through arch_v307
METHOD = "ARCH_TAKEOFF_V3.0.14"
EXTENDS = A3013.METHOD
CANDIDATE = A30.METHOD                  # the candidate family this version extends (never a new method family)
POLICY_ID = "URBAN_BOQ_T240_ARCH_V3_0_14"
LEDGER_SCHEMA = "URBAN_V3014_INTEGRATION_LEDGER_V1"
INPUTS_SCHEMA = "URBAN_V3014_INPUTS_V1"
ROLLBACK = A30.ROLLBACK
KINDS = ("ENTER_FLOOR", "TO_THRESHOLD", "TO_OUTDOOR", "NO_FLOOR", "TO_WET", "NO_OPENING_SPLIT", "SETTLE_RANGE",
         "UNDER_STAIR")
SETTLE_TO = ("FLOOR", "NOT_FLOOR")                  # WP3: a held piece of a bounded floor line, settled by a verdict
FLIGHT_DRAWN = ("OVERHEAD_ONLY", "BELOW_CUT")       # WP3: how a flight on the lowest storey is drawn on its plan
FLOOR_ITEMS = A30.FLOOR_ITEMS                       # the finished internal floor items
DRY_ITEM, WET_ITEM = "FIN.FLOOR.PORCELAIN", "FIN.FLOOR.WET_TILE"
SPLIT_TO = ("COUNTED_IN", "NO_FLOOR", "TO_WET", "HELD_WITH")
TOL_CLOSURE = 1e-3                      # an engine-geometry part vs its printed box less the named pieces
SPACE_ITEM = "ARCH.SPACE"                           # space floor area (finish to be confirmed)
THRESHOLD_ITEM = "ARCH.THRESHOLD"
FLOOR_KEYS = ("FLOOR.INTERNAL", "FLOOR.OUTDOOR")
THRESHOLD_CLASSES = ("LIFT_LANDING", "EXTERIOR_SILL")
MATERIAL_STATUS = ("HELD", "ASSUMED - OWNER-APPROVED", "DRAWING-CONFIRMED", "VERIFIED")
LIVE_EVIDENCE = A307.LIVE_EVIDENCE
TOL_M2 = 1e-6                           # a stated area vs its recomputed printed dimensions (same printed values)
TOL_CARRIED = 1e-6
MAX_DIM_M = 30.0                        # a floor piece side above this is a unit slip (mm / cm given as m), refused
InputsError = A307.InputsError
_num = A307._num
_STRIP_OPENING = re.compile(r"STRIP-(OP-\d+)")

PIECES = {
    "FLOOR_SCOPE": {
        "module": "engine/source/arch_v3014.py (one strip / face, one line, by its physical class)",
        "policy": "FLOOR_SCOPE_V1", "rule_id": "UP-SPACE-FACE-TYPE-001", "rule_version": "T223-2026-10-23",
        "owner_rules": ["UP-SPACE-001 / UP-SPACE-002 (interior / exterior from enclosure and connectivity; a project "
                        "decision binds one space)",
                        "UP-SPACE-FACE-TYPE-001 proposed (T-223, Checker MERGED 48d1d846: an enclosed interior face "
                        "reached through an open passage enters the floor line, material HELD unless printed)",
                        "UP-DOOR-CLS-005 / UP-ELEV-SCHED-001 (the lift landing sill comes with the lift: a threshold, "
                        "not floor porcelain)",
                        "UP-THR-001 (a dry doorway between interior spaces: the floor continues)",
                        "Q-67 A (owner 2026-10-20: an open-air side passage with nothing across its mouth is exterior)",
                        "URBAN-FINISH-QUANTITY-INDEPENDENT-OF-MATERIAL@v1 (area released, material kept apart)",
                        "D-C3 (a doorless cell never takes a neighbour's scope silently)",
                        "UP-QTY-STATUS-001 (held is a range or blocked, never 0)"],
        "owner_manual_method": "manual QS floor take-off: room by room, clear area between the finished wall faces, "
                               "doorway strips with the room they belong to, thresholds and sills billed separately, "
                               "external areas outside the internal floor",
        "drawing_method": "each face typed from its own drawn evidence (enclosure, openings, fixtures, drainage plan, "
                          "joinery boxes, binding decisions); area from the printed dimensions of its faces; each "
                          "doorway strip classed by what it joins (interior / lift / exterior); one strip, one line"},
    "DEFAULT_GUARD": A307.PIECES["DEFAULT_GUARD"],
}
WAITING = dict(A3013.WAITING)
WAITING.update({
    "FLOOR_PANTRY_DOORWAY_ZONE": "the pantry's doorway-zone piece (about 1.10 m2 inside the printed 4.50 x 3.00 box, "
                                 "an RFI line in the candidate) stays as carried: held stays held; its wet class "
                                 "applies when its own RFI closes",
    "FLOOR_PANTRY_PART_RECHECK": "T-240 WP2 moves the pantry part of the open dining / living face to the wet line on "
                                 "the engine face geometry clipped to the printed pantry box (closure in the inputs); "
                                 "the Checker's figure of that part differs and is re-measured at WP4",
    "FLOOR_UNDER_STAIR_BELOW_CUT": "the floor under round-stair flights drawn below the cut on the lowest storey "
                                   "stays HELD (area kept) until a section or structural detail of that stair fixes "
                                   "where its soffit leaves the floor (designer item proposed by T-269)",
    "FLOOR_LANDING_MARBLE_LINE": "T-122: the marble line of an arrival landing split out of a porcelain face under "
                                 "Q-66 B (printed vs drawn area, RULE_DIFFERENCE named) is the marble trade's wiring "
                                 "piece; it reads the split-out space line's area once",
    "FLOOR_LINE_WHOLE_VERIFICATION": "the whole floor-area line becomes VERIFIED only when every piece is checker-"
                                     "verified and nothing in its scope is HELD: Gate B of this package re-measures "
                                     "the pieces it moves; the held pieces it names stay held",
    "FLOOR_MATERIAL_UNTYPED_FACES": "the finish material of a face entered by ENTER_FLOOR stays HELD until a material "
                                    "rule binds its class (the DRY class rests on the absence of fixtures and the "
                                    "drainage-plan read); never borrowed from the neighbouring room",
})


def _r(x, n=6):
    return None if x is None else round(float(x), n)


# ================================================================================================ project inputs
def _dim(x, what):
    if not (_num(x) and x > 0):
        raise InputsError(f"{what}: a dimension > 0 is required (missing is never 0)")
    if x > MAX_DIM_M:
        raise InputsError(f"{what}: {x} m is not a floor piece dimension (unit slip? metres only)")
    return float(x)


def area_of(rec):
    """the record's area recomputed from its printed dimensions: a list of [a, b] rectangles (metres)."""
    rid = rec.get("id")
    dims = rec.get("dims")
    if not (isinstance(dims, list) and dims):
        raise InputsError(f"record {rid}: dims is a list of [a, b] rectangles from the printed dimensions")
    tot = 0.0
    for i, d in enumerate(dims):
        if not (isinstance(d, (list, tuple)) and len(d) == 2):
            raise InputsError(f"record {rid}: dims[{i}] is [a, b]")
        tot += _dim(d[0], f"{rid} dims[{i}][0]") * _dim(d[1], f"{rid} dims[{i}][1]")
    st = rec.get("area_m2")
    if not (_num(st) and st > 0):
        raise InputsError(f"record {rid}: area_m2 > 0 is stated (missing is never 0)")
    if abs(float(st) - tot) > TOL_M2:
        raise InputsError(f"record {rid}: stated area {st} != {_r(tot)} recomputed from its printed dimensions")
    return tot


def _line_ref(rid, x, what, items):
    for k in ("item_code", "floor", "element_id", "why"):
        if x.get(k) in (None, ""):
            raise InputsError(f"record {rid} {what}: {k} is required (the candidate line and why it moves)")
    if x["item_code"] not in items:
        raise InputsError(f"record {rid} {what}: item {x['item_code']!r} is not one of {items}")
    if x.get("unit", "m2") != "m2":
        raise InputsError(f"record {rid} {what}: unit m2")
    if "carried" not in x:
        raise InputsError(f"record {rid} {what}: carried (the figure the line carries now) is required")


def _check_record(rec):
    rid = rec.get("id")
    k = rec.get("kind")
    if k not in KINDS:
        raise InputsError(f"record {rid}: kind {k!r} not one of {KINDS}")
    for f in ("id", "floor", "evidence", "drawing_reference"):
        if rec.get(f) in (None, ""):
            raise InputsError(f"record {rid}: {f} is required")
    if k == "ENTER_FLOOR":
        area_of(rec)
        if rec.get("class") != "INTERIOR":
            raise InputsError(f"record {rid}: only an INTERIOR face enters the internal floor (class "
                              f"{rec.get('class')!r}); an exterior, open-ended or shaft face never does")
        if rec.get("wet_dry") not in ("DRY", "WET"):
            raise InputsError(f"record {rid}: the wet / dry class is stated (a face whose class is HELD is not "
                              "entered here)")
        if rec.get("area_status") not in ("VERIFIED", "DRAWING-CONFIRMED"):
            raise InputsError(f"record {rid}: area_status VERIFIED or DRAWING-CONFIRMED")
        ms = rec.get("material_status")
        if ms not in MATERIAL_STATUS:
            raise InputsError(f"record {rid}: material_status one of {MATERIAL_STATUS}")
        if ms != "HELD" and not rec.get("material_source"):
            raise InputsError(f"record {rid}: a material that is not HELD names its source (a rule or a print), "
                              "never the neighbouring room")
        if rec.get("material_from_neighbour"):
            raise InputsError(f"record {rid}: a material borrowed from the neighbouring room is refused (D-C3)")
        _line_ref(rid, rec.get("line") or {}, "line", (SPACE_ITEM,))
    elif k == "TO_THRESHOLD":
        area_of(rec)
        if rec.get("class") not in THRESHOLD_CLASSES:
            raise InputsError(f"record {rid}: threshold class one of {THRESHOLD_CLASSES}")
        if not re.fullmatch(r"OP-\d+", str(rec.get("opening") or "")) or not rec.get("rule"):
            raise InputsError(f"record {rid}: the opening (OP-nnn, as the plan's opening id) and the rule that "
                              "classes it are required")
        _line_ref(rid, rec.get("line") or {}, "line", FLOOR_ITEMS)
        if rec.get("twin") is not None:
            _line_ref(rid, rec["twin"], "twin", (THRESHOLD_ITEM,))
        if rec.get("release"):
            raise InputsError(f"record {rid}: a threshold whose finish is unspecified is HELD, never released")
    elif k == "TO_OUTDOOR":
        tot = area_of(rec)
        if not rec.get("decision"):
            raise InputsError(f"record {rid}: an exterior face leaves the internal key only by a binding decision "
                              "(name it); unbound it stays HELD in place")
        lines = rec.get("lines") or ()
        if not lines:
            raise InputsError(f"record {rid}: the internal lines the face leaves are named")
        for i, x in enumerate(lines):
            _line_ref(rid, x, f"lines[{i}]", (SPACE_ITEM,) + FLOOR_ITEMS + (THRESHOLD_ITEM,))
        retired = sum(float(x["carried"]) for x in lines if _num(x.get("carried")))
        miss = rec.get("missing") or {}
        mm2 = float(miss.get("m2") or 0.0)
        if abs(retired + mm2 - tot) > TOL_M2 * 10:
            raise InputsError(f"record {rid}: the retired pieces {_r(retired)} + the stated missing piece {_r(mm2)} "
                              f"!= the drawn area {_r(tot)}: every difference is named")
        if mm2 > TOL_M2 and not miss.get("why"):
            raise InputsError(f"record {rid}: the missing piece {_r(mm2)} m2 names why the engine has no line for it")
        if rec.get("material_status") not in MATERIAL_STATUS:
            raise InputsError(f"record {rid}: material_status one of {MATERIAL_STATUS}")
        if rec["material_status"] != "HELD" and not rec.get("material_source"):
            raise InputsError(f"record {rid}: a material that is not HELD names its source")
    elif k == "TO_WET":
        if not rec.get("decision"):
            raise InputsError(f"record {rid}: a floor piece is classed WET only by a binding rule or decision (name "
                              "it); unbound its class stays as carried")
        _line_ref(rid, rec.get("line") or {}, "line", (DRY_ITEM,))
        mv = rec.get("move_m2")
        if not (_num(mv) and mv > 0):
            raise InputsError(f"record {rid}: move_m2 > 0 (the wet part of the line; missing is never 0)")
        if rec.get("whole") is True:
            if not A308._same(float(mv), rec["line"].get("carried")):
                raise InputsError(f"record {rid}: a whole-line move moves exactly the carried figure")
        else:
            cl = rec.get("closure") or {}
            if not (_num(cl.get("box_m2")) and cl["box_m2"] > 0 and isinstance(cl.get("terms"), dict)):
                raise InputsError(f"record {rid}: a part of a line moves only with its closure: the printed box "
                                  "area and every other named piece in it")
            if abs(float(cl["box_m2"]) - sum(float(v) for v in cl["terms"].values()) - float(mv)) > TOL_CLOSURE:
                raise InputsError(f"record {rid}: the part {mv} does not close the printed box {cl['box_m2']} with "
                                  f"the named pieces (residual above {TOL_CLOSURE} m2 is never absorbed)")
            if not (_num(rec["line"].get("carried")) and float(mv) < float(rec["line"]["carried"])):
                raise InputsError(f"record {rid}: a part is smaller than the line it leaves")
        if rec.get("area_status") not in ("VERIFIED", "DRAWING-CONFIRMED"):
            raise InputsError(f"record {rid}: area_status VERIFIED or DRAWING-CONFIRMED")
    elif k == "NO_OPENING_SPLIT":
        x = rec.get("line") or {}
        _line_ref(rid, x, "line", FLOOR_ITEMS)
        if rec.get("twin") is not None:
            _line_ref(rid, rec["twin"], "twin", (THRESHOLD_ITEM,))
        parts = rec.get("parts") or ()
        if not parts:
            raise InputsError(f"record {rid}: a strip with no opening is split into the named places it lies in")
        tot, names = 0.0, set()
        for i, p in enumerate(parts):
            pn = p.get("part")
            if not pn or pn in names:
                raise InputsError(f"record {rid}: parts[{i}] names its part, once")
            names.add(pn)
            a = area_of(dict(p, id=f"{rid}:{pn}"))
            tot += a
            to = p.get("to")
            if to not in SPLIT_TO:
                raise InputsError(f"record {rid} part {pn}: to one of {SPLIT_TO}")
            if to == "COUNTED_IN" and not p.get("record"):
                raise InputsError(f"record {rid} part {pn}: COUNTED_IN names the record whose line counts it")
            if to == "TO_WET" and not p.get("decision"):
                raise InputsError(f"record {rid} part {pn}: a wet part names its binding rule or decision")
            if to == "HELD_WITH" and not (p.get("held_with") and p.get("why")):
                raise InputsError(f"record {rid} part {pn}: a held part names what it waits with and why (never 0)")
            if to == "NO_FLOOR" and not p.get("why"):
                raise InputsError(f"record {rid} part {pn}: a part with no floor says why")
        if not (_num(x.get("carried")) and abs(tot - float(x["carried"])) <= TOL_M2 * 10):
            raise InputsError(f"record {rid}: the parts {_r(tot)} != the carried strip {x.get('carried')}: every "
                              "part of the strip is placed, none twice")
    elif k == "SETTLE_RANGE":
        _check_settle(rec)
    elif k == "UNDER_STAIR":
        _check_under_stair(rec)
    else:   # NO_FLOOR
        _line_ref(rid, rec.get("line") or {}, "line", FLOOR_ITEMS)
        if rec.get("twin") is not None:
            _line_ref(rid, rec["twin"], "twin", (THRESHOLD_ITEM,))


def _terms_area(rid, what, t):
    """an area given as named signed terms (a printed box less / plus named pieces); every term named, sum > 0."""
    if not (isinstance(t, dict) and t):
        raise InputsError(f"record {rid} {what}: terms is a dict of named signed areas (m2)")
    for n, v in t.items():
        if not n or not _num(v) or abs(v) > MAX_DIM_M * MAX_DIM_M:
            raise InputsError(f"record {rid} {what}: term {n!r} = {v!r} is not a named area in m2 (unit slip?)")
    tot = sum(float(v) for v in t.values())
    if tot <= 0:
        raise InputsError(f"record {rid} {what}: the terms add to {_r(tot)} (an area > 0; missing is never 0)")
    return tot


def _check_settle(rec):
    """SETTLE_RANGE (WP3): a floor line carried as a range [low, high] whose held pieces a checker verdict settled
    from the drawings. Every held piece is named with its printed dimensions and placed FLOOR or NOT_FLOOR; the held
    pieces add up to high - low; the value is low + the FLOOR pieces. A part of the settled face with another finish
    (split_out) leaves the line by its binding decision, with its area from named terms; the line keeps the rest."""
    rid = rec["id"]
    x = rec.get("line") or {}
    _line_ref(rid, x, "line", FLOOR_ITEMS)
    c = x.get("carried")
    if not (isinstance(c, (list, tuple)) and len(c) == 2 and all(_num(v) for v in c) and 0 < c[0] < c[1]):
        raise InputsError(f"record {rid}: a settled line carries a range [low, high] with 0 < low < high (a live "
                          "figure is not settled here)")
    if rec.get("area_status") not in ("VERIFIED", "DRAWING-CONFIRMED"):
        raise InputsError(f"record {rid}: area_status VERIFIED or DRAWING-CONFIRMED")
    pieces = rec.get("pieces") or ()
    if not pieces:
        raise InputsError(f"record {rid}: the held pieces of the range are named, each settled")
    names, held, floor = set(), 0.0, 0.0
    for i, p in enumerate(pieces):
        pn = p.get("piece")
        if not pn or pn in names:
            raise InputsError(f"record {rid}: pieces[{i}] names its piece, once")
        names.add(pn)
        a = area_of(dict(p, id=f"{rid}:{pn}"))
        if p.get("to") not in SETTLE_TO:
            raise InputsError(f"record {rid} piece {pn}: to one of {SETTLE_TO} (a piece still open is not settled: "
                              "the line stays a range)")
        if not (p.get("why") and p.get("evidence")):
            raise InputsError(f"record {rid} piece {pn}: the drawn evidence and why it is {p['to']} are stated")
        held += a
        floor += a if p["to"] == "FLOOR" else 0.0
    if abs(held - (float(c[1]) - float(c[0]))) > TOL_M2 * 10:
        raise InputsError(f"record {rid}: the settled pieces {_r(held)} != the carried range width "
                          f"{_r(float(c[1]) - float(c[0]))}: every held piece is settled, none twice")
    v = rec.get("value_m2")
    if not (_num(v) and abs(float(c[0]) + floor - float(v)) <= TOL_M2 * 10):
        raise InputsError(f"record {rid}: value_m2 {v} != low {c[0]} + the FLOOR pieces {_r(floor)}")
    so = rec.get("split_out")
    if so is not None:
        for f in ("part", "decision", "material", "material_status", "material_source", "area_status"):
            if not so.get(f):
                raise InputsError(f"record {rid} split_out: {f} is required (a part with another finish leaves the "
                                  "line only by a binding decision, its area named)")
        if so["material_status"] not in MATERIAL_STATUS or so["area_status"] not in ("VERIFIED", "DRAWING-CONFIRMED"):
            raise InputsError(f"record {rid} split_out: material_status one of {MATERIAL_STATUS}, area_status "
                              "VERIFIED or DRAWING-CONFIRMED")
        a = _terms_area(rid, "split_out", so.get("terms"))
        if not (_num(so.get("area_m2")) and abs(float(so["area_m2"]) - a) <= TOL_M2):
            raise InputsError(f"record {rid} split_out: area_m2 {so.get('area_m2')} != its terms {_r(a)}")
        if a >= float(v):
            raise InputsError(f"record {rid} split_out: a part is smaller than the settled face")
        k = so.get("kept_m2")
        if not (_num(k) and abs(float(v) - a - float(k)) <= TOL_CLOSURE):
            raise InputsError(f"record {rid} split_out: kept_m2 {k} != the settled value {v} - the part {_r(a)} (a "
                              f"residual above {TOL_CLOSURE} m2 is never absorbed)")
        if abs(float(v) - a - float(k)) > TOL_M2 and not so.get("residual_why"):
            raise InputsError(f"record {rid} split_out: the residual {_r(float(v) - a - float(k))} m2 is named "
                              "(residual_why)")


def _check_under_stair(rec):
    """UNDER_STAIR (WP3): on the LOWEST storey, a floor line whose figure deducts the tread union of a stair. Each
    flight is placed by how its plan draws it: drawn only overhead with nothing closed under it -> the floor runs
    under it (FLOOR, the face's own finish); drawn below the cut -> HELD until a section or structural detail fixes
    where the soffit leaves the floor (area kept, never 0). The flights add up to the deducted union; the face line
    itself is not changed (its figure stays net of every tread)."""
    rid = rec["id"]
    if rec.get("lowest_storey") is not True:
        raise InputsError(f"record {rid}: only on the lowest storey (above it the space under a flight is the "
                          "storey below)")
    x = rec.get("face") or {}
    _line_ref(rid, x, "face", FLOOR_ITEMS)
    if not (_num(x.get("carried")) and x["carried"] > 0):
        raise InputsError(f"record {rid}: the face line carries a live figure")
    d = rec.get("deducted_m2")
    if not (_num(d) and d > 0):
        raise InputsError(f"record {rid}: deducted_m2 (the tread union the face figure deducts) > 0")
    if rec.get("area_status") not in ("VERIFIED", "DRAWING-CONFIRMED"):
        raise InputsError(f"record {rid}: area_status VERIFIED or DRAWING-CONFIRMED")
    fl = rec.get("flights") or ()
    if not fl:
        raise InputsError(f"record {rid}: the flights of the union are named")
    names, tot, n_floor = set(), 0.0, 0
    for i, f in enumerate(fl):
        fn = f.get("flight")
        if not fn or fn in names:
            raise InputsError(f"record {rid}: flights[{i}] names its flight, once")
        names.add(fn)
        if not (_num(f.get("area_m2")) and f["area_m2"] > 0):
            raise InputsError(f"record {rid} flight {fn}: area_m2 > 0 (the flight's part of the union)")
        tot += float(f["area_m2"])
        if f.get("drawn") not in FLIGHT_DRAWN or not f.get("evidence"):
            raise InputsError(f"record {rid} flight {fn}: drawn one of {FLIGHT_DRAWN}, with its drawn evidence")
        if f.get("to") == "FLOOR":
            if f["drawn"] != "OVERHEAD_ONLY" or f.get("closed_under") is not False:
                raise InputsError(f"record {rid} flight {fn}: FLOOR only under a flight drawn overhead only with "
                                  "nothing closed under it (closed_under False)")
            n_floor += 1
        elif f.get("to") == "HELD":
            if not f.get("why"):
                raise InputsError(f"record {rid} flight {fn}: a held flight says what it waits on (never 0)")
        else:
            raise InputsError(f"record {rid} flight {fn}: to FLOOR or HELD")
        if f["drawn"] == "BELOW_CUT" and f.get("to") != "HELD":
            raise InputsError(f"record {rid} flight {fn}: a flight drawn below the cut is HELD")
    if abs(tot - float(d)) > TOL_M2 * 10:
        raise InputsError(f"record {rid}: the flights {_r(tot)} != the deducted union {d}: every tread placed once")
    if rec.get("material_from_neighbour"):
        raise InputsError(f"record {rid}: a material borrowed from another room is refused (D-C3)")


def _check_counted_in(recs, p):
    """a NO_OPENING_SPLIT part COUNTED_IN another record: that record is a TO_OUTDOOR of the same piece whose stated
    missing piece is exactly this part (so the area is counted once, in that line, and the strip leaves nothing)."""
    by = {r["id"]: r for r in recs}
    for rec in recs:
        if rec["kind"] != "NO_OPENING_SPLIT":
            continue
        for part in rec["parts"]:
            if part["to"] != "COUNTED_IN":
                continue
            tgt = by.get(part["record"])
            if tgt is None or tgt["kind"] != "TO_OUTDOOR":
                raise InputsError(f"piece {p}: record {rec['id']} part {part['part']}: COUNTED_IN names a TO_OUTDOOR "
                                  f"record of the same piece ({part['record']!r} is not one)")
            miss = float((tgt.get("missing") or {}).get("m2") or 0.0)
            if abs(miss - float(part["area_m2"])) > TOL_M2 * 10:
                raise InputsError(f"piece {p}: record {rec['id']} part {part['part']} ({part['area_m2']} m2) is not "
                                  f"the missing piece {miss} m2 that {tgt['id']} adds: counted twice or lost")
            if (tgt.get("missing") or {}).get("carried_by") != rec["id"]:
                raise InputsError(f"piece {p}: {tgt['id']} names the line that carried its missing piece "
                                  f"(carried_by {rec['id']})")


def load_inputs(doc, project_id=None):
    """URBAN_V3014_INPUTS_V1 or None:
        {"schema", "project",
         "pieces": [{"piece": "FLOOR_SCOPE", "source": {file, sha256, task, merge_commit, checker_run},
                     "sources": [...], "records": [...], "declared": {"floor_internal_delta_m2", "threshold_m2",
                     "outdoor_m2"}}],
         "guard": as URBAN_V307_INPUTS_V1 "guard"}
    records: {"id", "kind", "floor", "evidence", "drawing_reference", "verified_by", ...}
        ENTER_FLOOR  + dims, area_m2, class INTERIOR, wet_dry, area_status, material_status (+ material_source),
                       line {item_code ARCH.SPACE, floor, element_id, carried, why}
        TO_THRESHOLD + dims, area_m2, opening, class LIFT_LANDING | EXTERIOR_SILL, rule,
                       line {floor item, ...}, twin {ARCH.THRESHOLD, ...} (optional)
        TO_OUTDOOR   + dims, area_m2, decision, material_status (+ material_source), lines [...],
                       missing {m2, why}
        NO_FLOOR     + line {floor item, ...}, twin {ARCH.THRESHOLD, ...} (optional)
        TO_WET       + decision, move_m2, whole | closure {box_m2, terms}, area_status, line {dry floor item, ...}
        NO_OPENING_SPLIT + line, twin (optional), parts [{part, dims, area_m2, to, ...}]
        SETTLE_RANGE + line {floor item, carried [low, high]}, value_m2, area_status, pieces [{piece, dims, area_m2,
                       to FLOOR | NOT_FLOOR, why, evidence}], split_out {part, terms, area_m2, kept_m2, decision,
                       material, material_status, material_source, area_status} (optional)
        UNDER_STAIR  + lowest_storey True, face {floor item, carried}, deducted_m2, area_status, flights [{flight,
                       area_m2, drawn OVERHEAD_ONLY | BELOW_CUT, closed_under, to FLOOR | HELD, why, evidence}]"""
    if doc is None:
        return None
    if doc.get("schema") != INPUTS_SCHEMA:
        raise InputsError(f"project inputs: schema must be {INPUTS_SCHEMA}")
    if project_id and doc.get("project") not in (None, project_id):
        raise InputsError(f"project inputs are for {doc.get('project')!r}, the run is {project_id!r}")
    seen = set()
    for pc in doc.get("pieces") or ():
        p = pc.get("piece")
        if p != "FLOOR_SCOPE" or p in seen:
            raise InputsError(f"piece {p!r}: FLOOR_SCOPE, once")
        seen.add(p)
        A307._source(pc.get("source"), f"piece {p}")
        for s in pc.get("sources") or ():
            A307._source(s, f"piece {p} (supporting source)")
        recs = pc.get("records") or ()
        if not recs:
            raise InputsError(f"piece {p}: no records")
        ids, named = set(), set()
        for rec in recs:
            if not rec.get("id") or rec["id"] in ids:
                raise InputsError(f"piece {p}: every record names its id, once")
            ids.add(rec["id"])
            _check_record(rec)
            for x in _refs(rec):
                key = (x["item_code"], x["floor"], x["element_id"])
                if key in named:
                    raise InputsError(f"piece {p}: line {key} is named by two records (one strip, one line)")
                named.add(key)
        _check_counted_in(recs, p)
    g = doc.get("guard")
    if g is not None:
        A307.load_inputs({"schema": A307.INPUTS_SCHEMA, "project": doc.get("project"), "guard": g}, project_id)
    return doc


def _refs(rec):
    out = []
    if rec.get("line"):
        out.append(rec["line"])
    if rec.get("twin"):
        out.append(rec["twin"])
    out += list(rec.get("lines") or ())
    return out


# ================================================================================================ changes
def _find(lines, x, rid):
    hit = [ln for ln in lines if ln["item_code"] == x["item_code"] and ln["unit"] == x.get("unit", "m2")
           and (ln.get("location") or {}).get("element_id") == x["element_id"]
           and (ln.get("location") or {}).get("floor") == x["floor"]]
    if len(hit) != 1:
        raise InputsError(f"record {rid}: candidate line {x['item_code']} {x['floor']} {x['element_id']} found "
                          f"{len(hit)} time(s); exactly one")
    return hit[0]


def _check_carried(ln, x, rid):
    cq = A308._carried(ln)
    st = x.get("carried")
    if st is None:
        if cq is not None:
            raise InputsError(f"record {rid}: line {x['element_id']} carries {cq}, the inputs state none")
        return cq
    if not A308._same(cq, st):
        raise InputsError(f"record {rid}: line {x['element_id']} carries {cq}, the inputs state {st}: the replaced "
                          "figure must be the one the line carries")
    return cq


def _verif(src, pc, rec):
    return {"task": src["task"], "merge_commit": src["merge_commit"], "verifier_run": src["checker_run"],
            "source": src["file"], "source_sha256": src["sha256"], "verified_by": rec.get("verified_by"),
            "supporting": [{k: s.get(k) for k in ("task", "merge_commit", "checker_run", "file")}
                           for s in pc.get("sources") or ()]}


def _scope_rec(rec, area, **kw):
    return dict({"policy": PIECES["FLOOR_SCOPE"]["policy"], "record": rec["id"], "kind": rec["kind"],
                 "area_m2": _r(area), "dims": rec.get("dims"), "evidence": rec["evidence"],
                 "verified_by": rec.get("verified_by")}, **kw)


def _new_line(pid, rev, docs, item, floor, eid, ev, *, value=None, rng=None, formula, inputs, notes, rfi=None,
              material_state="BY_SPEC", physical="FLOOR"):
    from engine.source import boq_line as BL
    p = PIECES["FLOOR_SCOPE"]
    return BL.make_line(project_id=pid, revision_set_sha256=rev, item_code=item, unit="m2", evidence_state=ev,
                        measured_net=_r(value) if ev in BL.QUANTITY_STATES else None, bounded_range=rng,
                        element_id=eid, floor=floor, physical_element=physical, formula=formula[:400],
                        inputs={"floor_scope_v3014": inputs},
                        documents=docs, geometry_source="CAD_VECTOR", geometry_confidence="TOLERANCE_CERTIFIED",
                        rule_id=p["rule_id"], rule_version=p["rule_version"], material_state=material_state, rfi=rfi,
                        notes=notes)


def scope_changes(pc, lines, earlier_changed=()):
    """the FLOOR_SCOPE piece on the V3.0.13 lines. -> (changes, log)"""
    pid, rev, docs = A302._proj(lines)
    earlier = set(earlier_changed)
    src = pc["source"]
    have = {ln["line_id"] for ln in lines}
    changes, touched = [], set()
    log = {"piece": "FLOOR_SCOPE", "state": "RUN", "source": src, "sources": pc.get("sources") or [], "records": [],
           "totals": {"floor_internal_in_m2": 0.0, "floor_internal_out_m2": 0.0, "threshold_m2": 0.0,
                      "outdoor_m2": 0.0, "no_floor_m2": 0.0, "dry_to_wet_m2": 0.0, "held_with_m2": 0.0,
                      "counted_in_m2": 0.0, "settled_m2": 0.0,
                      "under_stair_floor_m2": 0.0, "under_stair_held_m2": 0.0}}

    def take(x, rid):
        ln = _find(lines, x, rid)
        if ln["line_id"] in touched:
            raise ValueError(f"{METHOD}: line {ln['line_id']} changed twice")
        A308._check_replaceable(ln, earlier, x)
        cq = _check_carried(ln, x, rid)
        touched.add(ln["line_id"])
        return ln, cq

    def retire(ln, rid, why, note, verif, codes, ref):
        changes.append(A307._retire(ln, why, note, verif, "FLOOR_SCOPE", codes, ref))

    def live(ln):
        return ln["evidence_state"] in LIVE_EVIDENCE and ln.get("measured_net") is not None

    for rec in pc["records"]:
        rid, k, fl = rec["id"], rec["kind"], rec["floor"]
        verif = _verif(src, pc, rec)
        ref = str(rec["drawing_reference"])[:300]
        entry = {"id": rid, "kind": k, "floor": fl}
        if k == "ENTER_FLOOR":
            area = area_of(rec)
            x = rec["line"]
            ln, cq = take(x, rid)
            after = copy.deepcopy(ln)
            calc = dict(after.get("calculation") or {})
            calc["formula"] = (" + ".join(f"{a} x {b}" for a, b in rec["dims"]) + f" = {_r(area, 4)} m2 (enclosed "
                               f"{rec['wet_dry'].lower()} interior face; finish material {rec['material_status']})")
            calc["inputs"] = dict(calc.get("inputs") or {}, floor_scope_v3014=_scope_rec(
                rec, area, floor_key="FLOOR.INTERNAL", face_class=rec["class"], wet_dry=rec["wet_dry"],
                area_status=rec["area_status"], material_status=rec["material_status"],
                material_source=rec.get("material_source"), was=A30._qty(ln)))
            after.update(evidence_state="SOURCE_DERIVED", measured_net=_r(area), bounded_range=None, gross=_r(area),
                         rfi=None, physical_element="FLOOR", calculation=calc)
            A305._note(after, f"{METHOD}: ENTERS the internal floor line (floor_key FLOOR.INTERNAL) - {rec['class']} "
                              f"{rec['wet_dry']} face, area {_r(area, 4)} m2 {rec['area_status']} ({src['task']}, "
                              f"MERGED {src['merge_commit']}); finish material {rec['material_status']} (never "
                              f"borrowed from the neighbouring room); V3.0.13 figure {A302._q(A30._qty(ln))} replaced")
            changes.append(A305._change(
                "FLOOR_SCOPE", "REPLACE", ln, after, drawing_reference=ref,
                held=[] if rec["material_status"] != "HELD" else [
                    {"what": f"finish material of {x['element_id']} {fl}", "why": rec.get("material_why") or
                     "material not printed; the class rule binds no material yet", "range": None}],
                downstream=[], verification=verif, evidence_status=rec["area_status"],
                codes=["ENTER_FLOOR", "FLOOR.INTERNAL", f"MATERIAL_{rec['material_status'].split()[0]}"]
                + (["EARLIER_CHANGE"] if ln["line_id"] in earlier else []), why=x["why"]))
            moved_in = area - (float(cq) if live(ln) and _num(cq) else 0.0)
            log["totals"]["floor_internal_in_m2"] += area
            entry.update(line_id=ln["line_id"], element_id=x["element_id"], was=A30._qty(ln), area_m2=_r(area),
                         floor_internal_delta_m2=_r(area), live_before=live(ln), released_moved=_r(moved_in))
        elif k == "TO_THRESHOLD":
            area = area_of(rec)
            x = rec["line"]
            ln, cq = take(x, rid)
            why = f"{rec['opening']} is a threshold ({rec['class']}, {rec['rule']}): {x['why']}"
            retire(ln, rid, why, f"{METHOD}: NOT FLOOR - {A302._q(A30._qty(ln))} m2 leaves the internal floor line "
                                 f"for the threshold line of {rec['opening']} ({src['task']}, MERGED "
                                 f"{src['merge_commit']}); figure kept as information, never summed", verif,
                   ["TO_THRESHOLD", rec["class"]], ref)
            q = (f"{rec['opening']} ({rec['class']}): the sill finish is not specified on the drawings ("
                 f"{rec['rule']}); the area {_r(area, 4)} m2 is held until the specification / supplier fixes it")
            sc = _scope_rec(rec, area, floor_key=None, opening=rec["opening"], threshold_class=rec["class"],
                            rule=rec["rule"], from_line=ln["line_id"], evidence_status="HELD")
            rng = {"low": _r(area), "high": _r(area),
                   "basis": f"threshold {rec['opening']} {rec['class']}: area {_r(area, 4)} m2 kept, finish HELD"}
            if rec.get("twin") is not None:
                tw, tq = take(rec["twin"], rid)
                after = copy.deepcopy(tw)
                calc = dict(after.get("calculation") or {})
                calc["formula"] = (" + ".join(f"{a} x {b}" for a, b in rec["dims"]) +
                                   f" = {_r(area, 4)} m2 threshold, HELD (finish not specified)")
                calc["inputs"] = dict(calc.get("inputs") or {}, floor_scope_v3014=dict(sc, was=A30._qty(tw)))
                after.update(evidence_state="BOUNDED_EXPOSURE", measured_net=None, gross=None, bounded_range=rng,
                             rfi={"question": q[:900], "unlocks": rec["twin"]["element_id"]}, calculation=calc)
                A305._note(after, f"{METHOD}: the ONE threshold line of {rec['opening']} - area kept, HELD")
                changes.append(A305._change(
                    "FLOOR_SCOPE", "REPLACE", tw, after, drawing_reference=ref,
                    held=[{"what": f"{THRESHOLD_ITEM} {rec['opening']} {fl}", "why": q, "range": [_r(area), _r(area)]}],
                    downstream=[], verification=verif, evidence_status="HELD",
                    codes=["TO_THRESHOLD", rec["class"], "ONE_STRIP_ONE_LINE"], why=why))
                tid = tw["line_id"]
            else:
                eid = f"HL:FLOOR_SCOPE:THRESHOLD:{fl}:{rec['opening']}"
                nl = _new_line(pid, rev, docs, THRESHOLD_ITEM, fl, eid, "BOUNDED_EXPOSURE", rng=rng,
                               formula=" + ".join(f"{a} x {b}" for a, b in rec["dims"]) +
                               f" = {_r(area, 4)} m2 threshold, HELD (finish not specified)",
                               inputs=sc, rfi={"question": q[:900], "unlocks": eid}, physical="THRESHOLD",
                               notes=f"{METHOD}: threshold {rec['opening']} ({rec['class']}) moved out of the floor "
                                     f"line ({src['task']}, MERGED {src['merge_commit']}); area kept, HELD, never 0")
                if nl["line_id"] in have:
                    raise ValueError(f"{METHOD}: an added threshold line repeats a V3.0.13 line id")
                changes.append(A305._change(
                    "FLOOR_SCOPE", "ADD", None, nl, drawing_reference=ref,
                    held=[{"what": f"{THRESHOLD_ITEM} {rec['opening']} {fl}", "why": q, "range": [_r(area), _r(area)]}],
                    downstream=[], verification=verif, evidence_status="HELD",
                    codes=["TO_THRESHOLD", rec["class"], "NEW_LINE"], why=why,
                    guard_element={"element_id": eid, "part": "WHOLE"}))   # the guard re-check carries it as drawn
                tid = nl["line_id"]
            out_m2 = float(cq) if live(ln) and _num(cq) else 0.0
            log["totals"]["floor_internal_out_m2"] += out_m2
            log["totals"]["threshold_m2"] += area
            entry.update(opening=rec["opening"], threshold_class=rec["class"], from_line=ln["line_id"],
                         threshold_line=tid, area_m2=_r(area), floor_internal_delta_m2=_r(-out_m2))
        elif k == "TO_OUTDOOR":
            area = area_of(rec)
            out_m2, retired_ids = 0.0, []
            for x in rec["lines"]:
                ln, cq = take(x, rid)
                if live(ln) and _num(cq) and (ln["item_code"] in FLOOR_ITEMS or _space_key(ln) == "FLOOR.INTERNAL"):
                    out_m2 += float(cq)     # an untyped space piece was in no floor line: it leaves nothing
                retire(ln, rid, f"exterior by {rec['decision']}: {x['why']}",
                       f"{METHOD}: EXTERIOR - {A302._q(A30._qty(ln))} m2 leaves the internal floor key for the outdoor "
                       f"line of {rid} ({rec['decision']}; {src['task']}, MERGED {src['merge_commit']}); figure kept "
                       "as information, never summed", verif, ["TO_OUTDOOR", "FLOOR.OUTDOOR"], ref)
                retired_ids.append(ln["line_id"])
            miss = rec.get("missing") or {}
            eid = f"HL:FLOOR_SCOPE:OUTDOOR:{fl}:{rid}"
            ms = rec["material_status"]
            nl = _new_line(pid, rev, docs, SPACE_ITEM, fl, eid, "SOURCE_DERIVED", value=area,
                           formula=" + ".join(f"{a} x {b}" for a, b in rec["dims"]) +
                           f" = {_r(area, 4)} m2 exterior floor ({rec['decision']}; finish {ms})",
                           inputs=_scope_rec(rec, area, floor_key="FLOOR.OUTDOOR", decision=rec["decision"],
                                             retired_lines=retired_ids, missing=miss or None,
                                             material_status=ms, material_source=rec.get("material_source"),
                                             area_status=rec.get("area_status")),
                           material_state="PROJECT_OWNER_FACT" if ms == "ASSUMED - OWNER-APPROVED" else "BY_SPEC",
                           notes=f"{METHOD}: exterior floor of {rid} (floor_key FLOOR.OUTDOOR, never in the internal "
                                 f"floor line; {rec['decision']}); {len(retired_ids)} internal line(s) retired"
                                 + (f"; the piece {_r(miss.get('m2'), 4)} m2 no engine line carried is named: "
                                    f"{miss.get('why')}" if miss.get("m2") else ""))
            if nl["line_id"] in have:
                raise ValueError(f"{METHOD}: an added outdoor line repeats a V3.0.13 line id")
            changes.append(A305._change(
                "FLOOR_SCOPE", "ADD", None, nl, drawing_reference=ref, held=[], downstream=[], verification=verif,
                evidence_status=rec.get("area_status") or "DRAWING-CONFIRMED",
                codes=["TO_OUTDOOR", "FLOOR.OUTDOOR", "NEW_LINE"] + (["MISSING_PIECE_NAMED"] if miss.get("m2")
                                                                     else []),
                why=f"exterior by {rec['decision']}", guard_element={"element_id": eid, "part": "WHOLE"}))
            log["totals"]["floor_internal_out_m2"] += out_m2
            log["totals"]["outdoor_m2"] += area
            entry.update(outdoor_line=nl["line_id"], retired=retired_ids, area_m2=_r(area),
                         floor_internal_delta_m2=_r(-out_m2), missing=miss or None)
        elif k == "TO_WET":
            x = rec["line"]
            ln, cq = take(x, rid)
            if not live(ln):
                raise InputsError(f"record {rid}: line {x['element_id']} is not live ({ln['evidence_state']}); a held "
                                  "or retired piece is not reclassed here")
            mv = float(rec["move_m2"])
            ev = ln["evidence_state"] if ln["evidence_state"] in ("MEASURED", "SOURCE_DERIVED", "PROVISIONAL") \
                else "SOURCE_DERIVED"
            why = f"WET by {rec['decision']}: {x['why']}"
            if rec.get("whole"):
                retire(ln, rid, why, f"{METHOD}: WET - {A302._q(A30._qty(ln))} m2 leaves the dry porcelain line for "
                                     f"the wet floor line of {rid} ({rec['decision']}); figure kept as information, "
                                     "never summed", verif, ["TO_WET", "WHOLE_LINE"], ref)
                kept = None
            else:
                after = copy.deepcopy(ln)
                kept = float(cq) - mv
                calc = dict(after.get("calculation") or {})
                calc["formula"] = (f"{_r(float(cq), 6)} - {_r(mv, 6)} (wet part, {rec['decision']}) = {_r(kept, 6)} m2 "
                                   "dry porcelain")[:400]
                calc["inputs"] = dict(calc.get("inputs") or {}, floor_scope_v3014=_scope_rec(
                    rec, mv, floor_key="FLOOR.INTERNAL", part="DRY_REMAINDER", was=A30._qty(ln), kept_m2=_r(kept),
                    closure=rec.get("closure"), area_basis=rec.get("area_basis")))
                after.update(measured_net=_r(kept), gross=_r(kept), calculation=calc)
                A305._note(after, f"{METHOD}: the wet part {_r(mv, 4)} m2 ({rec['decision']}) leaves this dry line for "
                                  f"the wet floor line of {rid}; V3.0.13 figure {A302._q(A30._qty(ln))} replaced")
                changes.append(A305._change(
                    "FLOOR_SCOPE", "REPLACE", ln, after, drawing_reference=ref, held=[], downstream=[],
                    verification=verif, evidence_status=rec["area_status"], codes=["TO_WET", "DRY_REMAINDER"]
                    + (["EARLIER_CHANGE"] if ln["line_id"] in earlier else []), why=why))
            eid = f"HL:FLOOR_SCOPE:WET:{fl}:{rid}"
            nl = _new_line(pid, rev, docs, WET_ITEM, fl, eid, ev, value=mv,
                           formula=(f"{_r(mv, 6)} m2 wet floor ({rec['decision']}); from {x['element_id']}"
                                    + ("" if rec.get("whole") else " (part, closure in inputs)")),
                           inputs=_scope_rec(rec, mv, floor_key="FLOOR.INTERNAL", decision=rec["decision"],
                                             from_line=ln["line_id"], whole=bool(rec.get("whole")),
                                             closure=rec.get("closure"), area_basis=rec.get("area_basis"),
                                             area_status=rec["area_status"]),
                           notes=f"{METHOD}: wet floor of {rid} ({rec['decision']}); area from {x['element_id']} "
                                 "unchanged, class only")
            if nl["line_id"] in have:
                raise ValueError(f"{METHOD}: an added wet line repeats a V3.0.13 line id")
            changes.append(A305._change(
                "FLOOR_SCOPE", "ADD", None, nl, drawing_reference=ref, held=[], downstream=list(
                    rec.get("downstream") or []), verification=verif, evidence_status=rec["area_status"],
                codes=["TO_WET", "NEW_LINE"], why=why, guard_element={"element_id": eid, "part": "WHOLE"}))
            log["totals"]["dry_to_wet_m2"] += mv
            entry.update(line_id=ln["line_id"], wet_line=nl["line_id"], moved_m2=_r(mv), dry_kept_m2=_r(kept),
                         floor_internal_delta_m2=0.0)
        elif k == "NO_OPENING_SPLIT":
            x = rec["line"]
            ln, cq = take(x, rid)
            out_m2 = float(cq) if live(ln) and _num(cq) else 0.0
            retire(ln, rid, f"no opening: {x['why']}",
                   f"{METHOD}: NO OPENING - {A302._q(A30._qty(ln))} m2 is split into the places it lies in (record "
                   f"{rid}); figure kept as information, never summed", verif, ["NO_OPENING_SPLIT", "ENGINE_DEFECT"],
                   ref)
            retired_ids = [ln["line_id"]]
            if rec.get("twin"):
                tw, _ = take(rec["twin"], rid)
                retire(tw, rid, f"no opening: {rec['twin']['why']}",
                       f"{METHOD}: NO OPENING - the threshold twin of a strip that is no opening (record {rid})", verif,
                       ["NO_OPENING_SPLIT", "TWIN"], ref)
                retired_ids.append(tw["line_id"])
            parts_out, in_m2 = [], 0.0
            for part in rec["parts"]:
                pa = area_of(dict(part, id=f"{rid}:{part['part']}"))
                to = part["to"]
                pe = {"part": part["part"], "to": to, "area_m2": _r(pa)}
                if to in ("TO_WET", "HELD_WITH"):
                    eid = f"HL:FLOOR_SCOPE:{to}:{fl}:{rid}:{part['part']}"
                    sc = _scope_rec(dict(rec, dims=part["dims"]), pa, part=part["part"], to=to, from_line=ln["line_id"],
                                    floor_key="FLOOR.INTERNAL" if to == "TO_WET" else None,
                                    decision=part.get("decision"), held_with=part.get("held_with"),
                                    why=part.get("why"))
                    fml = " + ".join(f"{a} x {b}" for a, b in part["dims"]) + f" = {_r(pa, 4)} m2"
                    if to == "TO_WET":
                        nl = _new_line(pid, rev, docs, WET_ITEM, fl, eid, "SOURCE_DERIVED", value=pa,
                                       formula=fml + f" wet floor ({part['decision']}), part of a strip with no "
                                                     "opening",
                                       inputs=sc, notes=f"{METHOD}: part {part['part']} of {x['element_id']} (no "
                                                        f"opening) is wet floor ({part['decision']})")
                        in_m2 += pa
                        held = []
                    else:
                        q = f"part {part['part']} of {x['element_id']} waits with {part['held_with']}: {part['why']}"
                        nl = _new_line(pid, rev, docs, SPACE_ITEM, fl, eid, "BOUNDED_EXPOSURE",
                                       rng={"low": _r(pa), "high": _r(pa), "basis": q[:300]},
                                       formula=fml + f" HELD with {part['held_with']} (never 0)", inputs=sc,
                                       rfi={"question": q[:900], "unlocks": eid},
                                       notes=f"{METHOD}: part {part['part']} of a strip with no opening; HELD with "
                                             f"{part['held_with']}, area kept, outside the internal floor line")
                        held = [{"what": f"{x['element_id']} part {part['part']}", "why": q, "range": [_r(pa), _r(pa)]}]
                        log["totals"]["held_with_m2"] += pa
                    if nl["line_id"] in have:
                        raise ValueError(f"{METHOD}: an added split line repeats a V3.0.13 line id")
                    changes.append(A305._change(
                        "FLOOR_SCOPE", "ADD", None, nl, drawing_reference=ref, held=held, downstream=[],
                        verification=verif, evidence_status="HELD" if held else "DRAWING-CONFIRMED",
                        codes=["NO_OPENING_SPLIT", to, "NEW_LINE"], why=f"no opening: {x['why']}",
                        guard_element={"element_id": eid, "part": "WHOLE"}))
                    pe["line"] = nl["line_id"]
                elif to == "COUNTED_IN":
                    pe["record"] = part["record"]
                    log["totals"]["counted_in_m2"] += pa
                else:
                    log["totals"]["no_floor_m2"] += pa
                parts_out.append(pe)
            log["totals"]["floor_internal_out_m2"] += out_m2
            log["totals"]["floor_internal_in_m2"] += in_m2
            entry.update(retired=retired_ids, parts=parts_out, floor_internal_delta_m2=_r(in_m2 - out_m2))
        elif k == "SETTLE_RANGE":
            x = rec["line"]
            ln, cq = take(x, rid)
            if ln["evidence_state"] != "BOUNDED_EXPOSURE":
                raise InputsError(f"record {rid}: line {x['element_id']} is {ln['evidence_state']}; only a bounded "
                                  "line is settled here")
            v = float(rec["value_m2"])
            so = rec.get("split_out")
            kept = float(so["kept_m2"]) if so else v
            after = copy.deepcopy(ln)
            calc = dict(after.get("calculation") or {})
            pz = "; ".join(f"{p['piece']} {_r(area_of(dict(p, id=rid)), 4)} {p['to']}" for p in rec["pieces"])
            calc["formula"] = (f"{_r(float(cq[0]), 6)} (low) + the pieces settled FLOOR = {_r(v, 6)} m2 [{pz}]"
                               + (f"; less {so['part']} {_r(float(so['area_m2']), 6)} ({so['decision']}) = "
                                  f"{_r(kept, 6)} m2" if so else ""))[:400]
            calc["inputs"] = dict(calc.get("inputs") or {}, floor_scope_v3014=_scope_rec(
                rec, v, floor_key="FLOOR.INTERNAL", part="SETTLED", was=A30._qty(ln), value_m2=_r(v), kept_m2=_r(kept),
                pieces=rec["pieces"], area_status=rec["area_status"],
                split_out={k2: so.get(k2) for k2 in ("part", "area_m2", "terms", "decision", "material",
                                                     "residual_why")} if so else None))
            ev = "SOURCE_DERIVED"
            after.update(evidence_state=ev, measured_net=_r(kept), gross=_r(kept), bounded_range=None, rfi=None,
                         calculation=calc)
            A305._note(after, f"{METHOD}: range {A302._q(A30._qty(ln))} SETTLED to {_r(v, 4)} m2 {rec['area_status']} "
                              f"({src['task']}, MERGED {src['merge_commit']}: every held piece placed from the drawings)"
                              + (f"; {so['part']} {_r(float(so['area_m2']), 4)} m2 leaves this line ({so['decision']})"
                                 if so else ""))
            down = list(rec.get("downstream") or [])
            changes.append(A305._change(
                "FLOOR_SCOPE", "REPLACE", ln, after, drawing_reference=ref, held=[], downstream=down,
                verification=verif, evidence_status=rec["area_status"], codes=["SETTLE_RANGE", "ONE_VALUE"]
                + (["SPLIT_OUT"] if so else []) + (["EARLIER_CHANGE"] if ln["line_id"] in earlier else []),
                why=x["why"]))
            split_line = None
            if so:
                eid = f"HL:FLOOR_SCOPE:SPLIT_OUT:{fl}:{rid}:{so['part']}"
                ms = so["material_status"]
                nl = _new_line(pid, rev, docs, SPACE_ITEM, fl, eid, ev, value=float(so["area_m2"]),
                               formula=(" + ".join(f"{n} {_r(t, 6)}" for n, t in so["terms"].items())
                                        + f" = {_r(float(so['area_m2']), 4)} m2 floor ({so['material']}, "
                                          f"{so['decision']})"),
                               inputs=_scope_rec(dict(rec, dims=None), float(so["area_m2"]), floor_key="FLOOR.INTERNAL",
                                                 part="SPLIT_OUT", from_line=ln["line_id"], terms=so["terms"],
                                                 decision=so["decision"], material=so["material"],
                                                 material_status=ms, material_source=so["material_source"],
                                                 area_status=so["area_status"], material_line=so.get("material_line")),
                               material_state="PROJECT_OWNER_FACT" if ms == "ASSUMED - OWNER-APPROVED" else "BY_SPEC",
                               notes=f"{METHOD}: {so['part']} of {x['element_id']} - floor area in the internal line "
                                     f"(counted once, here), finish {so['material']} ({so['decision']}; "
                                     f"{ms}); never also in {x['item_code']}")
                if nl["line_id"] in have:
                    raise ValueError(f"{METHOD}: an added split line repeats a V3.0.13 line id")
                changes.append(A305._change(
                    "FLOOR_SCOPE", "ADD", None, nl, drawing_reference=ref, held=[],
                    downstream=list(so.get("downstream") or []), verification=verif,
                    evidence_status=so["area_status"], codes=["SETTLE_RANGE", "SPLIT_OUT", "NEW_LINE"],
                    why=f"{so['part']}: {so['decision']}", guard_element={"element_id": eid, "part": "WHOLE"}))
                split_line = nl["line_id"]
            log["totals"]["floor_internal_in_m2"] += v       # a range was in no internal figure; the face enters whole
            log["totals"]["settled_m2"] += v
            entry.update(line_id=ln["line_id"], was=A30._qty(ln), value_m2=_r(v), kept_m2=_r(kept),
                         split_line=split_line, floor_internal_delta_m2=_r(v))
        elif k == "UNDER_STAIR":
            x = rec["face"]
            face = _find(lines, x, rid)
            fq = _check_carried(face, x, rid)
            if not live(face):
                raise InputsError(f"record {rid}: face line {x['element_id']} is not live")
            fl_m2 = sum(float(f["area_m2"]) for f in rec["flights"] if f["to"] == "FLOOR")
            hd_m2 = sum(float(f["area_m2"]) for f in rec["flights"] if f["to"] == "HELD")
            fz = "; ".join(f"{f['flight']} {_r(float(f['area_m2']), 4)} {f['drawn']} -> {f['to']}"
                           for f in rec["flights"])
            added = []
            if fl_m2 > 0:
                eid = f"HL:FLOOR_SCOPE:UNDER_STAIR:{fl}:{rid}"
                nl = _new_line(pid, rev, docs, x["item_code"], fl, eid, "SOURCE_DERIVED", value=fl_m2,
                               formula=(f"{_r(fl_m2, 6)} m2 floor under the flights drawn overhead only, out of the "
                                        f"{_r(float(rec['deducted_m2']), 6)} m2 tread union {x['element_id']} deducts "
                                        f"[{fz}]"),
                               inputs=_scope_rec(dict(rec, dims=None), fl_m2, floor_key="FLOOR.INTERNAL",
                                                 part="UNDER_STAIR_FLOOR", face_line=face["line_id"], face_m2=_r(fq),
                                                 deducted_m2=rec["deducted_m2"], flights=rec["flights"],
                                                 area_status=rec["area_status"]),
                               notes=f"{METHOD}: the floor of {x['element_id']} runs under the overhead flights (same "
                                     f"face, its own finish {x['item_code']}); the face line stays net of every tread")
                if nl["line_id"] in have:
                    raise ValueError(f"{METHOD}: an added under-stair line repeats a V3.0.13 line id")
                changes.append(A305._change(
                    "FLOOR_SCOPE", "ADD", None, nl, drawing_reference=ref, held=[],
                    downstream=list(rec.get("downstream") or []), verification=verif,
                    evidence_status=rec["area_status"], codes=["UNDER_STAIR", "FLOOR", "NEW_LINE"],
                    why=f"lowest storey: floor under overhead flights ({x['element_id']})",
                    guard_element={"element_id": eid, "part": "WHOLE"}))
                added.append(nl["line_id"])
            if hd_m2 > 0:
                eid = f"HL:FLOOR_SCOPE:UNDER_STAIR_HELD:{fl}:{rid}"
                q = "; ".join(f"{f['flight']} {_r(float(f['area_m2']), 4)} m2: {f['why']}" for f in rec["flights"]
                              if f["to"] == "HELD")
                nl = _new_line(pid, rev, docs, SPACE_ITEM, fl, eid, "BOUNDED_EXPOSURE",
                               rng={"low": _r(hd_m2), "high": _r(hd_m2), "basis": ("under flights drawn below the cut, "
                                                                                 "HELD: " + q)[:300]},
                               formula=f"{_r(hd_m2, 6)} m2 under the flights drawn below the cut, HELD (never 0) [{fz}]",
                               inputs=_scope_rec(dict(rec, dims=None), hd_m2, floor_key=None, part="UNDER_STAIR_HELD",
                                                 to="HELD", face_line=face["line_id"], flights=rec["flights"],
                                                 why=q[:600]),
                               rfi={"question": q[:900], "unlocks": eid},
                               notes=f"{METHOD}: under-stair of {x['element_id']} HELD, area kept, outside the internal "
                                     "floor line")
                if nl["line_id"] in have:
                    raise ValueError(f"{METHOD}: an added under-stair line repeats a V3.0.13 line id")
                changes.append(A305._change(
                    "FLOOR_SCOPE", "ADD", None, nl, drawing_reference=ref,
                    held=[{"what": f"under-stair of {x['element_id']} {fl}", "why": q, "range": [_r(hd_m2), _r(hd_m2)]}],
                    downstream=[], verification=verif, evidence_status="HELD",
                    codes=["UNDER_STAIR", "HELD", "NEW_LINE"], why="flights drawn below the cut",
                    guard_element={"element_id": eid, "part": "WHOLE"}))
                added.append(nl["line_id"])
                log["totals"]["under_stair_held_m2"] += hd_m2
            log["totals"]["floor_internal_in_m2"] += fl_m2
            log["totals"]["under_stair_floor_m2"] += fl_m2
            entry.update(face_line=face["line_id"], face_m2=_r(fq), floor_m2=_r(fl_m2), held_m2=_r(hd_m2),
                         added=added, floor_internal_delta_m2=_r(fl_m2))
        else:   # NO_FLOOR
            out_m2, retired_ids = 0.0, []
            for x in [rec["line"]] + ([rec["twin"]] if rec.get("twin") else []):
                ln, cq = take(x, rid)
                if live(ln) and ln["item_code"] in FLOOR_ITEMS and _num(cq):
                    out_m2 += float(cq)
                retire(ln, rid, f"no floor: {x['why']}",
                       f"{METHOD}: NO FLOOR - {A302._q(A30._qty(ln))} m2: {x['why']} ({src['task']}, MERGED "
                       f"{src['merge_commit']}); figure kept as information, never summed", verif,
                       ["NO_FLOOR", "ENGINE_DEFECT"], ref)
                retired_ids.append(ln["line_id"])
            log["totals"]["floor_internal_out_m2"] += out_m2
            log["totals"]["no_floor_m2"] += out_m2
            entry.update(retired=retired_ids, floor_internal_delta_m2=_r(-out_m2))
        log["records"].append(entry)
    log["totals"] = {k: _r(v) for k, v in log["totals"].items()}
    log["totals"]["floor_internal_delta_m2"] = _r(log["totals"]["floor_internal_in_m2"]
                                                  - log["totals"]["floor_internal_out_m2"])
    dec = pc.get("declared") or {}
    for k, v in dec.items():
        got = log["totals"].get(k)
        if got is None or abs(got - float(v)) > 1e-5:
            raise ValueError(f"{METHOD}: {k} {got} != the declared {v}")
    log["declared"] = dec
    return changes, log


# ================================================================================================ integrate / write
def changes_for(inputs, l3013, earlier_changed=()):
    """the floor-scope records, then the guard re-check over the result. -> (changes, logs)"""
    if not inputs or not inputs.get("pieces"):
        ch_g, log_g = A307.guard_changes(inputs, l3013, [], set())
        return ch_g, [{"piece": "FLOOR_SCOPE", "state": "NO_PROJECT_INPUT"}, log_g]
    ch, log = scope_changes(inputs["pieces"][0], l3013, earlier_changed)
    rep = {c["before"]["line_id"]: c["after"] for c in ch if c["action"] == "REPLACE"}
    view = [rep.get(ln["line_id"], ln) for ln in l3013]
    ch_g, log_g = A307.guard_changes(inputs, view, [c for c in ch if c["action"] == "ADD"], set(rep))
    for c in ch_g:   # a guard hold written by the V3.0.7 code is this version's row
        A305._note(c["after"], f"(re-check run by {METHOD})")
    return ch + ch_g, [log, log_g]


def _space_key(ln):
    sc = ((ln.get("calculation") or {}).get("inputs") or {}).get("floor_scope_v3014")
    return sc.get("floor_key") if isinstance(sc, dict) else None


def _live(ln):
    return ln["evidence_state"] in LIVE_EVIDENCE and ln.get("measured_net") is not None


def _opening_of(ln):
    m = _STRIP_OPENING.search(str((ln.get("location") or {}).get("element_id") or ""))
    if m:
        return m.group(1)
    sc = ((ln.get("calculation") or {}).get("inputs") or {}).get("floor_scope_v3014") or {}
    if ln.get("item_code") == THRESHOLD_ITEM and isinstance(sc, dict) and sc.get("opening"):
        return sc["opening"]
    return None


def strip_duplicates(lines):
    """every opening strip carried by more than ONE line that is not retired (a live floor line and a threshold line,
    or two of either). -> {(floor, opening): [line ids]}"""
    by = {}
    for ln in lines:
        if ln["item_code"] not in FLOOR_ITEMS + (THRESHOLD_ITEM,):
            continue
        if ln["evidence_state"] in ("NOT_APPLICABLE_WITH_EVIDENCE", "EXCLUDED_WITH_REASON"):
            continue
        op = _opening_of(ln)
        if op is None:
            continue
        by.setdefault(((ln.get("location") or {}).get("floor"), op), []).append(ln)
    return by, {k: [x["line_id"] for x in v] for k, v in by.items() if len(v) > 1}


def check_one_strip_one_line(lines, scope_ids=None):
    """on finished lines: a strip this version touched (its line ids, or every line carrying a floor-scope record) is
    carried by exactly one line that is not retired; a duplicate this version did not touch is returned as a named
    finding for its own work package (never silently accepted, never silently fixed here).
    -> {"strips": n, "pre_existing_duplicates": [{floor, opening, lines}]}"""
    by, dup = strip_duplicates(lines)
    mine = set(scope_ids or ())
    for ln in lines:
        if isinstance(((ln.get("calculation") or {}).get("inputs") or {}).get("floor_scope_v3014"), dict):
            mine.add(ln["line_id"])
    pre = []
    for k, ids in sorted(dup.items(), key=lambda kv: (str(kv[0][0]), str(kv[0][1]))):
        if mine & set(ids):
            raise InputsError(f"one strip, one line: opening {k[1]} on {k[0]} is carried by {len(ids)} lines {ids}")
        pre.append({"floor": k[0], "opening": k[1], "lines": ids})
    return {"strips": len(by), "pre_existing_duplicates": pre}


def check_floor_scope(lines):
    """on finished lines: every line this version typed is consistent - an entered face is live with its area, a
    threshold is HELD with its area (never 0), an outdoor line is never internal. -> counts by kind"""
    n = {}
    for ln in lines:
        sc = ((ln.get("calculation") or {}).get("inputs") or {}).get("floor_scope_v3014")
        if not sc or not isinstance(sc, dict) or "kind" not in sc:
            continue
        k = sc["kind"]
        n[k] = n.get(k, 0) + 1
        if k == "ENTER_FLOOR":
            if not _live(ln) or abs(float(ln["measured_net"]) - float(sc["area_m2"])) > TOL_M2 * 10:
                raise InputsError(f"line {ln['line_id']}: an entered face is live with its area")
            if sc.get("floor_key") != "FLOOR.INTERNAL":
                raise InputsError(f"line {ln['line_id']}: an entered face is in FLOOR.INTERNAL")
        elif k == "TO_THRESHOLD":
            br = ln.get("bounded_range") or {}
            if (ln["item_code"] != THRESHOLD_ITEM or ln["evidence_state"] != "BOUNDED_EXPOSURE"
                    or not (_num(br.get("low")) and br["low"] > 0)):
                raise InputsError(f"line {ln['line_id']}: a threshold is HELD with its area kept (never 0, never "
                                  "released)")
        elif k == "TO_OUTDOOR":
            if sc.get("floor_key") != "FLOOR.OUTDOOR" or ln["item_code"] in FLOOR_ITEMS:
                raise InputsError(f"line {ln['line_id']}: an exterior face is never in the internal floor line")
        elif k == "TO_WET":
            if ln["evidence_state"] == "NOT_APPLICABLE_WITH_EVIDENCE":
                continue
            if not _live(ln) or ln["item_code"] not in FLOOR_ITEMS or float(ln["measured_net"]) <= 0:
                raise InputsError(f"line {ln['line_id']}: a wet move leaves two live floor lines (wet + dry rest)")
            if sc.get("part") != "DRY_REMAINDER" and ln["item_code"] != WET_ITEM:
                raise InputsError(f"line {ln['line_id']}: the moved part is on the wet floor line")
        elif k == "NO_OPENING_SPLIT" and sc.get("to") == "TO_WET":
            if not _live(ln) or ln["item_code"] != WET_ITEM:
                raise InputsError(f"line {ln['line_id']}: a wet part of a split strip is live wet floor")
        elif k == "NO_OPENING_SPLIT" and sc.get("to") == "HELD_WITH":
            br = ln.get("bounded_range") or {}
            if ln["evidence_state"] != "BOUNDED_EXPOSURE" or not (_num(br.get("low")) and br["low"] > 0):
                raise InputsError(f"line {ln['line_id']}: a held part keeps its area (never 0, never released)")
        elif k == "SETTLE_RANGE":
            if not _live(ln) or sc.get("floor_key") != "FLOOR.INTERNAL":
                raise InputsError(f"line {ln['line_id']}: a settled line is live in FLOOR.INTERNAL (one value)")
            want = sc["area_m2"] if sc.get("part") == "SPLIT_OUT" else sc.get("kept_m2")
            if want is None or abs(float(ln["measured_net"]) - float(want)) > TOL_M2 * 10:
                raise InputsError(f"line {ln['line_id']}: a settled line carries its settled figure")
            if (sc.get("part") == "SPLIT_OUT") != (ln["item_code"] == SPACE_ITEM):
                raise InputsError(f"line {ln['line_id']}: the split-out part is its own space line, the rest stays on "
                                  "the finish line")
        elif k == "UNDER_STAIR":
            br = ln.get("bounded_range") or {}
            if sc.get("part") == "UNDER_STAIR_FLOOR":
                if not _live(ln) or ln["item_code"] not in FLOOR_ITEMS:
                    raise InputsError(f"line {ln['line_id']}: the floor under overhead flights is a live floor line")
            elif ln["evidence_state"] != "BOUNDED_EXPOSURE" or not (_num(br.get("low")) and br["low"] > 0):
                raise InputsError(f"line {ln['line_id']}: the under-stair held part keeps its area (never 0, never "
                                  "released)")
    return n


def floor_line(lines):
    """the internal floor-area line of a run: live FIN.FLOOR.* lines + live space lines typed FLOOR.INTERNAL; the
    outdoor key, the held thresholds and the untyped spaces apart. -> {by_floor, totals}"""
    out = {"internal": {}, "outdoor": {}, "threshold_held": {}, "space_untyped": {}, "space_held": {}}

    def add(key, fl, v):
        out[key][fl] = _r(out[key].get(fl, 0.0) + float(v), 6)

    for ln in lines:
        fl = (ln.get("location") or {}).get("floor")
        sc = ((ln.get("calculation") or {}).get("inputs") or {}).get("floor_scope_v3014") or {}
        if ln["item_code"] in FLOOR_ITEMS and _live(ln):
            add("internal", fl, ln["measured_net"])
        elif ln["item_code"] == SPACE_ITEM and _live(ln):
            fk = sc.get("floor_key") if isinstance(sc, dict) else None
            add({"FLOOR.INTERNAL": "internal", "FLOOR.OUTDOOR": "outdoor"}.get(fk, "space_untyped"), fl,
                ln["measured_net"])
        elif ln["item_code"] == THRESHOLD_ITEM and ln["evidence_state"] == "BOUNDED_EXPOSURE" and sc:
            add("threshold_held", fl, (ln.get("bounded_range") or {}).get("high") or 0.0)
        elif (ln["item_code"] == SPACE_ITEM and ln["evidence_state"] == "BOUNDED_EXPOSURE" and isinstance(sc, dict)
              and sc.get("to") in ("HELD_WITH", "HELD")):
            add("space_held", fl, (ln.get("bounded_range") or {}).get("high") or 0.0)
    return {k: dict(v, total=_r(sum(v.values()), 6)) for k, v in out.items()}


def integrate(l3013, v3014_changes):
    """-> (V3.0.14 lines, identity). Every line outside the V3.0.14 rows is byte-identical to the V3.0.13 line."""
    from engine.source import boq_line as BL
    sid = {ln["line_id"] for ln in l3013}
    rep, adds = {}, []
    for c in v3014_changes:
        if c["action"] == "REPLACE":
            lid = c["before"]["line_id"]
            if lid in rep:
                raise ValueError(f"{METHOD}: line {lid} changed twice")
            if lid not in sid:
                raise ValueError(f"{METHOD}: a change names a line the V3.0.13 run does not have")
            if c["after"]["line_id"] != lid:
                raise ValueError(f"{METHOD}: a changed line keeps its line id")
            rep[lid] = c["after"]
        elif c["action"] == "ADD":
            if c["after"]["line_id"] in sid:
                raise ValueError(f"{METHOD}: an added line repeats a V3.0.13 line id")
            adds.append(c["after"])
        else:
            raise ValueError(f"{METHOD}: action {c['action']}")
    out = [rep.get(ln["line_id"], ln) for ln in l3013] + adds
    if len({ln["line_id"] for ln in out}) != len(out):
        raise ValueError(f"{METHOD}: a BOQ line id appears twice")
    for ln in out:
        BL.validate(ln)
    A3011.check_conflicts(out)
    A3010.check_same_openings(out)
    A3012.check_partition(out)
    check_floor_scope(out)
    by12 = {ln["line_id"]: ln for ln in l3013}
    touched = set(rep) | {a["line_id"] for a in adds}
    outside = [ln for ln in out if ln["line_id"] not in touched]
    bad = [ln["line_id"] for ln in outside if A30.line_sha(by12[ln["line_id"]]) != A30.line_sha(ln)]
    if bad or len(outside) + len(rep) != len(l3013):
        raise ValueError(f"{METHOD}: {len(bad)} line(s) outside the V3.0.14 rows differ from {EXTENDS}")
    ident = {"v3_0_13_lines": len(l3013), "v3_0_14_lines": len(out), "v3_0_14_rows": len(v3014_changes),
             "replaced": len(rep), "added": len(adds), "outside_rows": len(outside),
             "outside_rows_identical_to_v3_0_13": len(outside),
             "outside_rows_sha256": hashlib.sha256("".join(A30.line_sha(x) for x in outside).encode()).hexdigest()}
    return out, ident


def ledger_rows(changes, released_lines=None):
    rel = {A30._key(ln): ln for ln in released_lines or ()}
    rows = []
    for c in changes:
        ref = c["after"] if c["before"] is None else c["before"]
        b12 = A30._qty(c["before"]) if c["before"] is not None else dict(A30._qty(None), state="NOT_IN_V3_0_13")
        b29 = None
        if released_lines is not None:
            b29 = A30._qty(rel[A30._key(ref)]) if A30._key(ref) in rel else dict(A30._qty(None),
                                                                                 state="NOT_IN_RELEASED")
        p = PIECES[c["piece"]]
        loc = ref.get("location") or {}
        rows.append({"version": METHOD, "piece": c["piece"], "action": c["action"], "line_id": ref["line_id"],
                     "item_code": ref["item_code"], "floor": loc.get("floor"), "room_id": loc.get("room_id"),
                     "element_id": c["after"]["location"].get("element_id"), "unit": c["after"]["unit"],
                     "before_released_v2_9": b29, "before_v3_0_13": b12, "after_v3_0_14": A30._qty(c["after"]),
                     "evidence_status": c.get("evidence_status") or "HELD", "release_status": "NOT RELEASED",
                     "codes": c.get("codes") or [], "citations": c.get("citations") or [],
                     "drawing_reference": c.get("drawing_reference"),
                     "owner_manual_method": p["owner_manual_method"], "drawing_method": p["drawing_method"],
                     "owner_rules": p["owner_rules"],
                     "verification": dict(c.get("verification") or {}, module=p["module"], policy=p["policy"]),
                     "held": c.get("held") or [], "downstream": c.get("downstream") or [], "rollback": ROLLBACK})
    return rows


LEDGER_CSV = ("version", "piece", "action", "line_id", "item_code", "floor", "room_id", "element_id", "unit", "v2_9",
              "v3_0_13", "v3_0_14", "evidence_status", "release_status", "codes", "drawing_reference", "verification",
              "held")


def ledger_csv(rows):
    return A305._csv([{"version": r["version"], "piece": r["piece"], "action": r["action"], "line_id": r["line_id"],
                       "item_code": r["item_code"], "floor": r["floor"], "room_id": r["room_id"],
                       "element_id": r["element_id"], "unit": r["unit"], "v2_9": A302._q(r["before_released_v2_9"]),
                       "v3_0_13": A302._q(r["before_v3_0_13"]), "v3_0_14": A302._q(r["after_v3_0_14"]),
                       "evidence_status": r["evidence_status"], "release_status": r["release_status"],
                       "codes": " ".join(r["codes"]), "drawing_reference": str(r["drawing_reference"])[:300],
                       "verification": f"{r['verification'].get('task')} {r['verification'].get('merge_commit')}",
                       "held": "; ".join(str(h.get("why") or h.get("what")) for h in r["held"])[:600]}
                      for r in rows], LEDGER_CSV)


DIFF_CSV = ("line_id", "item_code", "floor", "element_id", "unit", "vs_v3_0_13", "vs_released_v2_9", "v2_9",
            "v3_0_13", "v3_0_14")


def diff_rows(l3013, l3014, released_lines=None):
    b12 = {ln["line_id"]: ln for ln in l3013}
    rel = {A30._key(ln): ln for ln in released_lines or ()}
    out = []
    for ln in l3014:
        o = b12.get(ln["line_id"])
        vs = "ADDED" if o is None else ("SAME" if A30.line_sha(o) == A30.line_sha(ln) else "CHANGED")
        r = rel.get(A30._key(ln)) if released_lines is not None else None
        vs29 = None if released_lines is None else ("NOT_IN_RELEASED" if r is None else
                                                    ("SAME_QUANTITY" if A30._qty(r) == A30._qty(ln) else
                                                     "QUANTITY_DIFFERS"))
        out.append({"line_id": ln["line_id"], "item_code": ln["item_code"], "floor": ln["location"].get("floor"),
                    "element_id": ln["location"].get("element_id"), "unit": ln["unit"], "vs_v3_0_13": vs,
                    "vs_released_v2_9": vs29, "v2_9": A302._q(A30._qty(r)) if r else "",
                    "v3_0_13": A302._q(A30._qty(o)) if o else "", "v3_0_14": A302._q(A30._qty(ln))})
    return out


def write(out, l3013, v3014_changes, logs, inputs, released_lines=None):
    """the V3_0_14_* files beside the V3_0_13_* files. -> (file names, identity, ledger)."""
    from pathlib import Path
    from engine.source import boq_line as BL
    out = Path(out)
    l3014, ident = integrate(l3013, v3014_changes)
    touched = {c["after"]["line_id"] for c in v3014_changes}
    strips = check_one_strip_one_line(l3014, touched)
    rows = ledger_rows(v3014_changes, released_lines)
    diff = diff_rows(l3013, l3014, released_lines)
    dsum = {}
    for d in diff:
        dsum.setdefault("vs_v3_0_13", {}).setdefault(d["vs_v3_0_13"], 0)
        dsum["vs_v3_0_13"][d["vs_v3_0_13"]] += 1
        if d["vs_released_v2_9"] is not None:
            dsum.setdefault("vs_released_v2_9", {}).setdefault(d["vs_released_v2_9"], 0)
            dsum["vs_released_v2_9"][d["vs_released_v2_9"]] += 1
    ident = dict(ident, diff=dsum, opening_strips=strips["strips"],
                 pre_existing_strip_duplicates=strips["pre_existing_duplicates"])
    led = {"schema": LEDGER_SCHEMA, "method": METHOD, "extends": EXTENDS, "candidate": CANDIDATE,
           "base": A30.BASE_METHOD, "released": A30.RELEASED_METHOD, "released_default": False, "rows": rows,
           "waiting_pieces": WAITING, "integration_package": True,
           "work_package": "T-240 WP1 .. WP4 (the one Gate B integration package of the floor-area line)"}
    t12, t13 = A304.code_totals(l3013), A304.code_totals(l3014)
    moved = {k: {"v3_0_13": t12.get(k), "v3_0_14": t13.get(k)} for k in sorted(set(t12) | set(t13))
             if t12.get(k) != t13.get(k)}
    g = (inputs or {}).get("guard") or {}
    run = {"method": METHOD, "policy": POLICY_ID, "extends": EXTENDS, "candidate": CANDIDATE,
           "base_method": A30.BASE_METHOD, "released_method": A30.RELEASED_METHOD, "released_default": False,
           "rollback": ROLLBACK, "identity": ident, "pieces": PIECES, "piece_logs": logs,
           "inputs": {"pieces": [{k: pc.get(k) for k in ("piece", "source", "sources", "records", "declared")}
                                 for pc in (inputs or {}).get("pieces") or ()],
                      "guard": {k: g.get(k) for k in ("source", "evidence_file", "evidence_sha256", "conventions_file",
                                                      "conventions_sha256", "holding_checks", "recorded_checks",
                                                      "equal_value_rebase", "new_records")}},
           "floor_line_v3_0_13": floor_line(l3013), "floor_line_v3_0_14": floor_line(l3014),
           "floor_scope_lines": check_floor_scope(l3014),
           "totals_moved_by_code": moved, "waiting_pieces": WAITING,
           "evidence_status_counts": A302._count(r["evidence_status"] for r in rows)}
    files = {"V3_0_14_BOQ_LINES.json": BL.dumps(l3014),
             "V3_0_14_BOQ_LINES.csv": A30._lines_csv(l3014),
             "V3_0_14_INTEGRATION_LEDGER.json": A30._j(led),
             "V3_0_14_INTEGRATION_LEDGER.csv": ledger_csv(rows),
             "V3_0_14_DIFF.csv": A305._csv(diff, DIFF_CSV),
             "V3_0_14_RUN.json": A30._j(run)}
    for name, text in files.items():
        (out / name).write_text(text, encoding="utf-8")
    return sorted(files), ident, led


def policy_record():
    return {"method": METHOD, "extends": EXTENDS, "pieces": sorted(PIECES), "inputs_schema": INPUTS_SCHEMA,
            "released_default": False, "rollback": ROLLBACK}


__all__ = ["METHOD", "PIECES", "WAITING", "DEFAULT_GUARD_CLASS", "KINDS", "load_inputs", "area_of", "scope_changes",
           "changes_for", "integrate", "strip_duplicates", "check_one_strip_one_line", "check_floor_scope",
           "floor_line", "ledger_rows", "diff_rows", "write", "InputsError"]
