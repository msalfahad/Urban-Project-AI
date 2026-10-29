"""ARCH_TAKEOFF_V3.0.25 (T-343): the SAME opt-in BOQ candidate as ARCH_TAKEOFF_V3.0 .. V3.0.24 (engine.source.arch_v30,
arch_v301 .. arch_v3024), extended with ONE piece, OUTDOOR_FLOOR: the outdoor floor surfaces of one open court that no
candidate line carried (an OMISSION found by the label census binding), each as its own line, and the pool water-face
finish as a HELD blank line. Not a new method family and not the released default (owner management decision
2026-10-20 sections 2 and 5); rollback is running the released ARCH_TAKEOFF_V2.9.

The physical question (ERS 2026-10-22 s.2.1, s.3): which outdoor surfaces are a floor finish and which belong to
another element, each counted once. An open court is ONE drawn face inside the plot boundary walls with the pool
footprint as its hole; it is cut along drawn lines into pieces (open paving, covered porch, entrance steps and landing,
side walk, pool deck), each with its own finish:

  piece area     the drawn area of the piece (CAD polygon of a merged ledger); a piece cut by a drawn curve the ledger
                 measured as a polygon is re-derived from the curve itself: area = the face it was cut from less the
                 EXACT outline it borders (a D = half disc r + rectangle 2r x straight; a printed radius never makes a
                 circle, R-T342-POOL-OUTLINE-1), and the residual of the tessellated reading is named in m2;
  closure        the plan pieces re-add to the face (filled area less its holes, each hole by its exact outline) within
                 the declared tolerance; a vertical piece (visible risers) is outside the plan closure by kind;
  finish         from an owner rule (ASSUMED - OWNER-APPROVED with its source: interlock on the chalet court, porcelain
                 on the sides, marble on every tread / riser / landing of a stair assembly) or HELD; a piece whose
                 finish is HELD keeps its area as a held range [a, a] (BOUNDED_EXPOSURE, never 0, never released) on
                 the material-blank outdoor item;
  pool water     NOT a floor: the pool finish is its own element; its surface is the water D floor plus the wall faces
                 from the finished pool floor to the rim (the printed finished depth, never the structural height to
                 the base top); while no finish is specified the line is BLOCKED_RFI blank with the surface bound
                 beside it (never 0, never a range).

  ADD     one line per piece (element '<face>#<piece>') and one pool water-face finish line.

Refused (InputsError / ValueError, nothing written): a piece or element named twice; an area <= 0 or missing (HELD is
never 0); a derived area that is not face - exact outline; a D whose width is not 2 r; a plan closure off by more than
its tolerance; a HELD material on a priced item or an ASSUMED material without its source; an owner-approved material
on the material-blank item; an item outside the family; a rim height above the structural height or without its
printed source; a cross-check line the run does not carry or that shares area; a candidate line that already carries
a piece's element or the family (added once); a declared total that is not the records' sum. Every V3.0.24 line is
byte-identical (asserted); the merged default guard runs again over the result (arch_v307.guard_changes) with the
added lines; the V3.0.24 line-state check runs over the result.

Files: V3_0_25_BOQ_LINES.json / .csv, V3_0_25_INTEGRATION_LEDGER.json / .csv (per line: before (absent), after,
released V2.9, area basis and edges, area / material status, owner manual method beside the drawing-derived method,
freelancer row beside, source task / merge / checker run), V3_0_25_CLOSURE.csv (the face re-add and the cross-check
table), V3_0_25_DIFF.csv (every line against V3.0.24 and the released V2.9), V3_0_25_RUN.json. Nothing here names a
project, a sheet, a layer or a coordinate: every value comes from the inputs.
"""

from __future__ import annotations

import copy
import hashlib
import math

from engine.source import arch_v30 as A30
from engine.source import arch_v302 as A302
from engine.source import arch_v304 as A304
from engine.source import arch_v305 as A305
from engine.source import arch_v307 as A307
from engine.source import arch_v3010 as A3010
from engine.source import arch_v3011 as A3011
from engine.source import arch_v3012 as A3012
from engine.source import arch_v3014 as A3014
from engine.source import arch_v3015 as A3015
from engine.source import arch_v3018 as A3018
from engine.source import arch_v3021 as A3021
from engine.source import arch_v3023 as A3023
from engine.source import arch_v3024 as A3024

DEFAULT_GUARD_CLASS = "GUARD_HOST"      # T-212: it adds lines; it reaches the guard through arch_v307
METHOD = "ARCH_TAKEOFF_V3.0.25"
EXTENDS = A3024.METHOD
CANDIDATE = A30.METHOD
POLICY_ID = "URBAN_BOQ_T343_ARCH_V3_0_25"
INPUTS_SCHEMA = "URBAN_V3025_INPUTS_V1"
LEDGER_SCHEMA = "URBAN_V3025_INTEGRATION_LEDGER_V1"
ROLLBACK = A30.ROLLBACK
VER, DC, OA = A3018.VER, A3018.DC, A3018.OA
InputsError = A3015.InputsError
_num = A3015._num
_r = A3018._r
TOL = 1e-6
DERIVED_TOL_M2 = 1e-6                   # a derived area vs face - exact outline (the ledger prints 6 decimals)
SUM_TOL = 1e-4                          # declared totals vs the records' sums
CLOSURE_TOL_MAX = 0.01                  # the largest closure tolerance a project may declare, m2
RIM_MIN, RIM_MAX = 0.30, 3.00           # a pool finished depth, m (mm or a typo is refused)
RULE = ("R-OUTDOOR-FLOOR-1", "T-343")
MATERIAL_HELD_ITEM = "EXT.FLOOR.OUTDOOR"
POOL_FINISH_ITEM = "EXT.POOL.WATER_FACE"
# the family's items: code -> (en, ar, trade, unit). The marble items are the item master's own (boq_line.ITEMS).
ITEMS = {
    "EXT.PAVING.INTERLOCK": ("Interlock paving (outdoor court)", "انترلوك أرضيات الحوش", "EXTERNAL_WORKS", "m2"),
    "EXT.FLOOR.PORCELAIN": ("Outdoor floor porcelain / ceramic", "بورسلان / سيراميك أرضيات خارجية", "EXTERNAL_WORKS",
                            "m2"),
    MATERIAL_HELD_ITEM: ("Outdoor floor finish (material to be confirmed)", "أرضيات خارجية (المادة تحدد لاحقا)",
                         "EXTERNAL_WORKS", "m2"),
    POOL_FINISH_ITEM: ("Pool water-face finish (floor + walls to the rim)", "تشطيب وجه المياه للمسبح (الأرضية والجدران "
                       "حتى الحافة)", "EXTERNAL_WORKS", "m2"),
}
MARBLE_ITEMS = ("FIN.MARBLE.TREAD", "FIN.MARBLE.RISER", "FIN.MARBLE.LANDING")
FAMILY_ITEMS = tuple(ITEMS) + MARBLE_ITEMS
AREA_STATUS = (VER, DC)
MATERIAL_STATUS = (VER, DC, OA, "HELD")
KINDS = ("PLAN", "VERTICAL")            # a plan piece re-adds to the face; a vertical one (visible risers) does not
STATE_HELD = "BOUNDED_EXPOSURE"
STATE_POOL = "BLOCKED_RFI"

PIECES = {
    "OUTDOOR_FLOOR": {
        "module": "engine/source/arch_v3025.py (the outdoor floor surfaces of an open court, one line per piece cut "
                  "along drawn lines, finish from the owner rule or HELD with the area kept; the pool water-face "
                  "finish HELD blank with its surface bound; from checker-merged ledgers)",
        "policy": "OUTDOOR_FLOOR_V1", "rule_id": RULE[0], "rule_version": RULE[1],
        "owner_rules": ["OWNER_RULE_OUTDOOR_FLOORS_2026-10-21 (chalet court interlock, owner choice over the renders; "
                        "sides porcelain / ceramic, never interlock; porch at court level its own line, material "
                        "later; pool deck HELD; pool water is never a floor)",
                        "UP-STAIR-001 (marble on tread, riser and landing of every stair assembly, external steps "
                        "included); UP-STAIR-002 (drawn geometry governs); UP-STAIR-003 / -006 (visible riser)",
                        "Q-67 A (open-air side passage outside); Q-26 A (pool finished depth)",
                        "UP-QTY-STATUS-001 (held never 0); UP-SPACE-001 (a label alone never decides)",
                        "WORKFLOW_CONTROLS 2026-10-21 s.4 / s.5; ERS 2026-10-22 s.2 - s.4"],
        "owner_manual_method": "the owner's manual method measures an outdoor floor by printed length x printed width "
                               "of each strip (the north side walk 1.50 x 15.97 to the plot line, incl. the boundary "
                               "wall thickness): kept beside the drawn piece where the ledger records it, never used",
        "drawing_method": "per piece: the drawn area between the boundary-wall inner faces and the drawn cut lines "
                          "(CAD polygon of the merged ledger); a piece bordering a drawn curve = its face less the "
                          "exact outline; the pieces re-add to the court face less its holes; the pool water-face "
                          "surface = water D floor + water perimeter x finished depth (floor to rim)"},
    "DEFAULT_GUARD": A307.PIECES["DEFAULT_GUARD"],
}
WAITING = dict(A3024.WAITING)
WAITING.update({
    "OUTDOOR_FLOOR_MATERIAL": "the finish of the covered porch and of the pool deck (owner: undecided): their lines "
                              "keep the drawn area as a held range on the material-blank outdoor item until he names "
                              "it",
    "POOL_WATER_FACE_FINISH": "the pool water-face finish (no sheet and no Urban rule names it): BLANK with its surface "
                              "bound until the owner / designer specifies it",
    "OUTDOOR_THRESHOLDS": "six outdoor openings with a printed 0.15 m level change and no step drawn (proposal P-3): "
                          "not a floor piece of this face, not in this version",
    "OUTDOOR_SKIRTING": "the court skirting / upstands of the outdoor faces: not a floor line, not in this version",
})


# ================================================================================================ geometry
def d_outline(r, straight, width):
    """a D outline: half disc of radius r closed by two straight sides `straight` long and a back `width` = 2 r.
    -> (area m2, perimeter m)."""
    if not (_num(r) and _num(straight) and _num(width)) or r <= 0 or straight < 0 or width <= 0:
        raise InputsError(f"D outline: r {r}, straight {straight}, width {width} must be positive numbers")
    if abs(width - 2 * r) > TOL:
        raise InputsError(f"D outline: back {width} m is not 2 r = {2 * r} m (not a D: a circle or another shape)")
    return math.pi * r * r / 2 + width * straight, math.pi * r + 2 * straight + width


def _derived_area(p, where):
    """a piece cut by a drawn curve: face_m2 less the exact outlines it borders. -> (area, residual record)."""
    dv = p["derived"]
    face = dv.get("face_m2")
    if not (_num(face) and face > 0) or not dv.get("face_source"):
        raise InputsError(f"{where}: derived.face_m2 > 0 with its source")
    less = dv.get("less") or []
    if not less:
        raise InputsError(f"{where}: derived.less names the exact outline(s) the face is cut by")
    out, res = face, []
    for x in less:
        if not x.get("what") or not x.get("edges"):
            raise InputsError(f"{where}: each outline names what it is and its drawn edges")
        a, per = d_outline(x.get("r_m"), x.get("straight_m"), x.get("width_m"))
        out -= a
        t = x.get("tessellated_m2")
        res.append({"what": x["what"], "edges": x["edges"], "exact_m2": _r(a), "exact_perimeter_m": _r(per),
                    "tessellated_m2": t, "tessellation_residual_m2": _r(t - a) if _num(t) else None})
    if out <= 0:
        raise InputsError(f"{where}: face less its outlines is {out} m2 (an outline larger than its face)")
    return out, res


# ================================================================================================ inputs
def _check_piece(p, tasks, where):
    for x in ("piece", "element_id", "floor", "item_code", "unit", "kind", "area_status", "area_basis", "edges",
              "material", "material_status", "source_task"):
        if not p.get(x):
            raise InputsError(f"{where}: {x} required")
    if p["source_task"] not in tasks:
        raise InputsError(f"{where}: source_task {p['source_task']!r} is not a source")
    code = p["item_code"]
    if code not in FAMILY_ITEMS or code == POOL_FINISH_ITEM:
        raise InputsError(f"{where}: item {code!r} is not an outdoor floor item {sorted(set(FAMILY_ITEMS) - {POOL_FINISH_ITEM})}")
    if p["unit"] != "m2":
        raise InputsError(f"{where}: unit {p['unit']!r} (an outdoor floor piece is m2)")
    if p["kind"] not in KINDS:
        raise InputsError(f"{where}: kind {p['kind']!r} not one of {KINDS}")
    if p["area_status"] not in AREA_STATUS:
        raise InputsError(f"{where}: area_status {p['area_status']!r}: a piece integrated here has a confirmed area "
                          f"{AREA_STATUS} (an unresolved area is not integrated)")
    a = p.get("area_m2")
    if not (_num(a) and a > 0):
        raise InputsError(f"{where}: area {a!r} m2 must be > 0 (a missing area is HELD, never 0)")
    if p.get("derived") is not None:
        d, _res = _derived_area(p, where)
        if abs(d - a) > DERIVED_TOL_M2:
            raise InputsError(f"{where}: area {a} m2 != face {p['derived']['face_m2']} less the exact outline(s) "
                              f"= {_r(d)} m2")
    ms = p["material_status"]
    if ms not in MATERIAL_STATUS:
        raise InputsError(f"{where}: material_status {ms!r} not one of {MATERIAL_STATUS}")
    if ms == "HELD":
        if code != MATERIAL_HELD_ITEM:
            raise InputsError(f"{where}: a HELD finish is not priced as {code}: it stays on {MATERIAL_HELD_ITEM} with "
                              "its area kept")
        if not p.get("material_item"):
            raise InputsError(f"{where}: a HELD finish names the decision that unlocks it (material_item)")
    else:
        if code == MATERIAL_HELD_ITEM:
            raise InputsError(f"{where}: material {p['material']!r} is {ms}: it goes on its own item, not on "
                              f"{MATERIAL_HELD_ITEM}")
        if not p.get("material_source"):
            raise InputsError(f"{where}: a {ms} finish names its source (owner rule / drawing), never a default")
    om = p.get("owner_manual")
    if om is not None and not (om.get("formula") and _num(om.get("m2")) and om["m2"] > 0):
        raise InputsError(f"{where}: owner_manual {{formula, m2 > 0}} (kept beside, never used)")
    return a


def _check_pool(pf, tasks):
    where = "pool_finish"
    for x in ("element_id", "floor", "water_outline", "rim_height_source", "rim_status", "material_item",
              "source_task", "rim_basis"):
        if not pf.get(x):
            raise InputsError(f"{where}: {x} required")
    if pf["source_task"] not in tasks:
        raise InputsError(f"{where}: source_task {pf['source_task']!r} is not a source")
    if pf.get("material_status") != "HELD":
        raise InputsError(f"{where}: the water-face finish is HELD until it is specified (no rule, no sheet names it)")
    if pf["rim_basis"] != "FINISHED_FLOOR_TO_RIM":
        raise InputsError(f"{where}: the wall finish rises from the finished pool floor to the rim (rim_basis "
                          "FINISHED_FLOOR_TO_RIM), never from the structural base top")
    h, hs = pf.get("rim_height_m"), pf.get("structural_height_m")
    if not (_num(h) and RIM_MIN <= h <= RIM_MAX):
        raise InputsError(f"{where}: rim height {h} m outside {RIM_MIN} .. {RIM_MAX} (mm, a typo or missing)")
    if not (_num(hs) and hs >= h - TOL):
        raise InputsError(f"{where}: structural height {hs} m must be given and >= the finished depth {h} m (the "
                          "finish stands on the floor build-up above the base top)")
    if pf["rim_status"] not in AREA_STATUS:
        raise InputsError(f"{where}: rim_status {pf['rim_status']!r} not one of {AREA_STATUS}")
    w = pf["water_outline"]
    fa, per = d_outline(w.get("r_m"), w.get("straight_m"), w.get("width_m"))
    return fa, per, h


def load_inputs(doc, project_id=None):
    """URBAN_V3025_INPUTS_V1 or None:
        {"schema", "project", "sources": [{file, sha256, task, merge_commit, checker_run}],
         "face": {"face_id", "floor", "filled_m2", "filled_source", "holes": [{what, r_m, straight_m, width_m, edges,
                  tessellated_m2}], "closure_tol_m2", "reference_total_m2", "reference_source"},
         "pieces": [{piece, element_id, floor, item_code, unit, kind PLAN | VERTICAL, area_m2, area_status,
                     area_basis, edges, derived {face_m2, face_source, less [...]} (optional), material,
                     material_status, material_source | material_item, owner_manual {formula, m2} (optional),
                     freelancer {row, m2, note} (optional), flags [...], source_task}],
         "pool_finish": {element_id, floor, water_outline {r_m, straight_m, width_m, edges}, rim_height_m,
                         structural_height_m, rim_basis, rim_height_source, rim_status, material_status HELD,
                         material_item, freelancer {row, m2, note} (optional), source_task},
         "cross_check": [{line_id, item_code, element_id, why, shared_m2}],
         "declared": {"lines", "plan_m2", "vertical_m2", "held_material_m2", "pool_bound_m2"},
         "guard": as URBAN_V307_INPUTS_V1 "guard" (optional)}"""
    if doc is None:
        return None
    if doc.get("schema") != INPUTS_SCHEMA:
        raise InputsError(f"project inputs: schema must be {INPUTS_SCHEMA}")
    if project_id and doc.get("project") not in (None, project_id):
        raise InputsError(f"project inputs are for {doc.get('project')!r}, the run is {project_id!r}")
    srcs = doc.get("sources") or []
    if not srcs:
        raise InputsError("sources: the merged ledgers the pieces come from")
    tasks = set()
    for s in srcs:
        A3018._source(s, "sources")
        tasks.add(s["task"])
    face = doc.get("face") or {}
    for x in ("face_id", "floor", "filled_source"):
        if not face.get(x):
            raise InputsError(f"face: {x} required")
    if not (_num(face.get("filled_m2")) and face["filled_m2"] > 0):
        raise InputsError("face: filled_m2 > 0 (the court face before its holes)")
    tol = face.get("closure_tol_m2")
    if not (_num(tol) and 0 < tol <= CLOSURE_TOL_MAX):
        raise InputsError(f"face: closure_tol_m2 in (0, {CLOSURE_TOL_MAX}] (a declared drawing-rounding tolerance)")
    for h in face.get("holes") or ():
        if not h.get("what") or not h.get("edges"):
            raise InputsError("face: each hole names what it is and its drawn edges")
        d_outline(h.get("r_m"), h.get("straight_m"), h.get("width_m"))
    pieces = doc.get("pieces") or []
    if not pieces:
        raise InputsError("no pieces")
    seen_p, seen_e = set(), set()
    tot = {"lines": 0, "plan_m2": 0.0, "vertical_m2": 0.0, "held_material_m2": 0.0, "pool_bound_m2": 0.0}
    for p in pieces:
        where = f"piece {p.get('piece')}"
        a = _check_piece(p, tasks, where)
        if p["piece"] in seen_p or p["element_id"] in seen_e:
            raise InputsError(f"{where}: a piece (or its element) named twice: one line per piece")
        seen_p.add(p["piece"])
        seen_e.add(p["element_id"])
        if not str(p["element_id"]).startswith(str(face["face_id"]) + "#"):
            raise InputsError(f"{where}: element {p['element_id']!r} is not a piece of face {face['face_id']!r}")
        tot["lines"] += 1
        tot["plan_m2" if p["kind"] == "PLAN" else "vertical_m2"] += a
        if p["material_status"] == "HELD":
            tot["held_material_m2"] += a
    pf = doc.get("pool_finish")
    if pf is not None:
        if pf.get("element_id") in seen_e:
            raise InputsError("pool_finish: its element is also a piece (the pool water is never a floor)")
        fa, per, h = _check_pool(pf, tasks)
        tot["lines"] += 1
        tot["pool_bound_m2"] = fa + per * h
    for i, x in enumerate(doc.get("cross_check") or ()):
        if not (x.get("line_id") and x.get("why") and _num(x.get("shared_m2"))):
            raise InputsError(f"cross_check {i}: {{line_id, why, shared_m2}}")
        if abs(x["shared_m2"]) > TOL:
            raise InputsError(f"cross_check {x['line_id']}: shares {x['shared_m2']} m2 with a piece: an area is "
                              "counted once (resolve the overlap before integrating)")
    dec = doc.get("declared") or {}
    for k, v in tot.items():
        d = dec.get(k)
        if not _num(d) or abs(d - v) > SUM_TOL:
            raise InputsError(f"declared {k} {d} != the records' {round(v, 6)}")
    g = doc.get("guard")
    if g is not None:
        A307.load_inputs({"schema": A307.INPUTS_SCHEMA, "project": doc.get("project"), "guard": g}, project_id)
    return doc


# ================================================================================================ closure
def closure(doc):
    """the plan pieces re-added against the face less its holes (exact outlines). -> record (raises beyond tol)."""
    f = doc["face"]
    holes = []
    for h in f.get("holes") or ():
        a, per = d_outline(h["r_m"], h["straight_m"], h["width_m"])
        t = h.get("tessellated_m2")
        holes.append({"what": h["what"], "edges": h["edges"], "exact_m2": _r(a), "exact_perimeter_m": _r(per),
                      "tessellated_m2": t, "tessellation_residual_m2": _r(t - a) if _num(t) else None})
    net = f["filled_m2"] - sum(h["exact_m2"] for h in holes)
    plan = sum(p["area_m2"] for p in doc["pieces"] if p["kind"] == "PLAN")
    diff = plan - net
    if abs(diff) > f["closure_tol_m2"] + TOL:
        raise InputsError(f"face {f['face_id']}: plan pieces {_r(plan)} m2 != face {f['filled_m2']} less holes "
                          f"{_r(sum(h['exact_m2'] for h in holes))} = {_r(net)} m2 (difference {_r(diff)} m2 beyond "
                          f"{f['closure_tol_m2']}): a piece is missing or counted twice")
    ref = f.get("reference_total_m2")
    return {"face_id": f["face_id"], "filled_m2": f["filled_m2"], "filled_source": f["filled_source"],
            "holes": holes, "face_net_exact_m2": _r(net), "plan_pieces_m2": _r(plan),
            "difference_m2": _r(diff), "tolerance_m2": f["closure_tol_m2"],
            "reference_total_m2": ref, "reference_source": f.get("reference_source"),
            "vs_reference_m2": _r(plan - ref) if _num(ref) else None,
            "vertical_pieces_m2": _r(sum(p["area_m2"] for p in doc["pieces"] if p["kind"] == "VERTICAL"))}


# ================================================================================================ lines
def _item(code):
    from engine.source import boq_line as BL
    if code in ITEMS:
        en, ar, tr, _u = ITEMS[code]
    else:
        en, ar, tr, _u = BL.ITEMS[code]
    return en, ar, tr


def _src_rec(src):
    return {"task": src["task"], "ledger": src["file"], "ledger_sha256": src["sha256"],
            "merge_commit": src["merge_commit"], "checker_run": src["checker_run"]}


def piece_line(pid, rev, docs, p, src):
    """ONE outdoor floor line: SOURCE_DERIVED (finish by an owner rule) or BOUNDED_EXPOSURE [a, a] (finish HELD)."""
    from engine.source import boq_line as BL
    a = p["area_m2"]
    en, ar, tr = _item(p["item_code"])
    held = p["material_status"] == "HELD"
    res = _derived_area(p, f"piece {p['piece']}")[1] if p.get("derived") else None
    rec = dict({"policy": PIECES["OUTDOOR_FLOOR"]["policy"], "piece": p["piece"], "kind": p["kind"],
                "record_state": "ADD", "area_m2": _r(a), "area_status": p["area_status"],
                "area_basis": p["area_basis"][:400], "edges": p["edges"][:400], "derived": res,
                "material": p["material"], "material_status": p["material_status"],
                "material_source": p.get("material_source"), "material_item": p.get("material_item"),
                "evidence_status": "HELD" if held else p["area_status"],
                "owner_manual": p.get("owner_manual"), "freelancer": p.get("freelancer"),
                "flags": list(p.get("flags") or ()), "release_status": "NOT RELEASED",
                "rule_id": RULE[0], "rule_version": RULE[1]}, **_src_rec(src))
    inputs = {"piece": p["piece"], "record_state": "ADD",
              "owner_manual_method": PIECES["OUTDOOR_FLOOR"]["owner_manual_method"],
              "drawing_derived_method": PIECES["OUTDOOR_FLOOR"]["drawing_method"], "outdoor_floor_v3025": rec}
    base = (f"{p['piece']}: {p['area_basis']}"[:300] +
            (f"; = face {p['derived']['face_m2']} m2 less the exact outline(s) "
             f"{' + '.join(str(x['exact_m2']) for x in res)} m2" if res else ""))
    if held:
        formula = (f"{base}; area {_r(a, 4)} m2 kept, finish HELD ({p['material_item']}): held net {_r(a, 6)} m2 .. "
                   f"{_r(a, 6)} m2")
        rfi = {"question": f"{p['piece']}: which finish? the drawn area {_r(a, 4)} m2 is kept; {p['material_item']}"
                           [:700], "items": [p["material_item"]], "blocks": f"the finish line of {p['piece']}"}
        ln = BL.make_line(project_id=pid, revision_set_sha256=rev, item_code=p["item_code"], unit="m2",
                          evidence_state=STATE_HELD, measured_net=None, element_id=p["element_id"], floor=p["floor"],
                          physical_element="outdoor_floor", gross=None,
                          bounded_range={"low": _r(a), "high": _r(a), "basis": "drawn area kept; finish HELD"},
                          formula=formula[:700], inputs=inputs, documents=docs, geometry_source="CAD_VECTOR",
                          geometry_confidence="TOLERANCE_CERTIFIED", rule_id=RULE[0], rule_version=RULE[1],
                          material_state="BY_SPEC", rfi=rfi,
                          notes=(f"{METHOD}: an OMITTED outdoor floor piece added from the merged ledger "
                                 f"({src['task']}, MERGED {src['merge_commit'][:8]}); area {p['area_status']}, finish "
                                 f"HELD (never 0, never released)"),
                          item_en=en, item_ar=ar, trade=tr)
    else:
        formula = f"{base} = {_r(a, 6)} m2 ({p['material']}, {p['material_status']})"
        ln = BL.make_line(project_id=pid, revision_set_sha256=rev, item_code=p["item_code"], unit="m2",
                          evidence_state="SOURCE_DERIVED", measured_net=_r(a), element_id=p["element_id"],
                          floor=p["floor"], physical_element="outdoor_floor", gross=None, bounded_range=None,
                          formula=formula[:700], inputs=inputs, documents=docs, geometry_source="CAD_VECTOR",
                          geometry_confidence="TOLERANCE_CERTIFIED", rule_id=RULE[0], rule_version=RULE[1],
                          material_state="PROJECT_OWNER_FACT" if p["material_status"] == OA else "SOURCE",
                          notes=(f"{METHOD}: an OMITTED outdoor floor piece added from the merged ledger "
                                 f"({src['task']}, MERGED {src['merge_commit'][:8]}); area {p['area_status']}; finish "
                                 f"{p['material']} {p['material_status']} ({str(p['material_source'])[:160]})"
                                 + (f"; owner manual method {p['owner_manual']['formula']} = "
                                    f"{p['owner_manual']['m2']} m2 kept beside, never used" if p.get("owner_manual")
                                    else "")),
                          item_en=en, item_ar=ar, trade=tr)
    return BL.validate(ln), rec


def pool_line(pid, rev, docs, pf, src):
    """the pool water-face finish: BLOCKED_RFI blank, the surface bound beside it (never 0, never a range)."""
    from engine.source import boq_line as BL
    w = pf["water_outline"]
    fa, per = d_outline(w["r_m"], w["straight_m"], w["width_m"])
    h = pf["rim_height_m"]
    bound = fa + per * h
    en, ar, tr = _item(POOL_FINISH_ITEM)
    rec = dict({"policy": PIECES["OUTDOOR_FLOOR"]["policy"], "piece": "POOL_WATER_FACE", "record_state": "ADD",
                "evidence_status": "HELD", "material_status": "HELD", "material_item": pf["material_item"],
                "water_outline": dict(w, exact_m2=_r(fa), exact_perimeter_m=_r(per)),
                "rim_height_m": h, "rim_basis": pf["rim_basis"], "rim_height_source": pf["rim_height_source"][:400],
                "rim_status": pf["rim_status"], "structural_height_m": pf["structural_height_m"],
                "structural_note": "the wall concrete rises from the base top (structural height); the finish from "
                                   "the finished floor on its build-up: the structural height is beside, not used",
                "bound": {"floor_m2": _r(fa), "walls_m2": _r(per * h), "surface_m2": _r(bound),
                          "release_status": "NOT RELEASED"},
                "freelancer": pf.get("freelancer"), "rule_id": RULE[0], "rule_version": RULE[1]}, **_src_rec(src))
    inputs = {"piece": "POOL_WATER_FACE", "record_state": "ADD", "outdoor_floor_v3025": rec,
              "owner_manual_method": "no answered owner rule measures or names the pool finish: shown beside, none",
              "drawing_derived_method": "water D floor (exact) + water perimeter (exact) x finished depth floor -> "
                                        "rim (printed)"}
    q = (f"Pool water-face finish: which finish (tile / mosaic / plaster)? {pf['material_item']}; surface bound "
         f"floor {_r(fa)} m2 + walls {_r(per)} lm x {h} m (finished depth) gives {_r(bound)} m2")
    ln = BL.make_line(project_id=pid, revision_set_sha256=rev, item_code=POOL_FINISH_ITEM, unit="m2",
                      evidence_state=STATE_POOL, measured_net=None, element_id=pf["element_id"], floor=pf["floor"],
                      physical_element="pool_water_face", gross=None, bounded_range=None,
                      formula=(f"held: {METHOD}: pool water-face finish not specified; surface floor {_r(fa)} m2 "
                               f"(water D r {w['r_m']}) + walls {_r(per)} lm x finished depth {h} m (finished floor "
                               f"to rim; structural {pf['structural_height_m']} m beside, not used), bound "
                               f"{_r(bound)} m2: BLANK, never 0")[:700],
                      inputs=inputs, documents=docs, geometry_source="CAD_VECTOR",
                      geometry_confidence="TOLERANCE_CERTIFIED", rule_id=RULE[0], rule_version=RULE[1],
                      material_state="BY_SPEC", rfi={"question": q[:700], "items": [pf["material_item"]],
                                                     "blocks": "the pool water-face finish line"},
                      notes=(f"{METHOD}: the pool finish is its own element (pool water is never a floor); BLANK "
                             f"until specified; bound {_r(bound)} m2 beside ({src['task']}, MERGED "
                             f"{src['merge_commit'][:8]})"),
                      item_en=en, item_ar=ar, trade=tr)
    return BL.validate(ln), rec


def _assert_not_carried(doc, lines):
    """the family is added once: no candidate line on a family item code of this module's own ITEMS, no line on any
    piece element or the pool finish element, no marble line naming the face, and every cross-check line present."""
    eids = {p["element_id"] for p in doc["pieces"]}
    pf = doc.get("pool_finish")
    if pf:
        eids.add(pf["element_id"])
    fid = str(doc["face"]["face_id"])
    for ln in lines:
        code, eid = ln["item_code"], str((ln.get("location") or {}).get("element_id"))
        if code in ITEMS:
            raise InputsError(f"the run already carries {code} line {ln['line_id']}: the family is added once")
        if eid in eids or eid.startswith(fid + "#"):
            raise InputsError(f"line {ln['line_id']} ({code}) already carries element {eid}: counted once")
    by = {ln["line_id"]: ln for ln in lines}
    for x in doc.get("cross_check") or ():
        ln = by.get(x["line_id"])
        if ln is None:
            raise InputsError(f"cross_check {x['line_id']}: the run carries no such line (stale inputs)")
        if x.get("item_code") and x["item_code"] != ln["item_code"]:
            raise InputsError(f"cross_check {x['line_id']}: item {x['item_code']} != the line's {ln['item_code']}")


def family_changes(doc, l3024):
    """-> (changes, log, closure record)."""
    _assert_not_carried(doc, l3024)
    clo = closure(doc)
    pid, rev, docs = A302._proj(l3024)
    have = {ln["line_id"] for ln in l3024}
    changes = []
    log = {"piece": "OUTDOOR_FLOOR", "state": "RUN", "sources": doc["sources"], "lines": 0, "released_m2": 0.0,
           "held_material_m2": 0.0, "pool_bound_m2": None, "by_item": {}, "closure": clo}
    for p in doc["pieces"]:
        src = A3018._src_of(doc, p["source_task"])
        after, rec = piece_line(pid, rev, docs, p, src)
        if after["line_id"] in have:
            raise ValueError(f"{METHOD}: an added line repeats a candidate line id")
        log["lines"] += 1
        k = f"{p['item_code']} m2"
        log["by_item"][k] = _r(log["by_item"].get(k, 0.0) + p["area_m2"])
        held = p["material_status"] == "HELD"
        if held:
            log["held_material_m2"] = _r(log["held_material_m2"] + p["area_m2"])
        else:
            log["released_m2"] = _r(log["released_m2"] + p["area_m2"])
        changes.append(A305._change(
            "OUTDOOR_FLOOR", "ADD", None, after, drawing_reference=src["file"],
            held=[{"what": f"{p['item_code']} {p['piece']}", "why": p["material_item"],
                   "range": [_r(p["area_m2"]), _r(p["area_m2"])]}] if held else [],
            downstream=[], verification={"task": src["task"], "merge_commit": src["merge_commit"],
                                         "verifier_run": src["checker_run"], "ledger": src["file"],
                                         "ledger_sha256": src["sha256"]},
            evidence_status="HELD" if held else p["area_status"], codes=["OUTDOOR_FLOOR", p["kind"]],
            group=doc["face"]["face_id"], record=rec,
            guard_element={"element_id": after["location"]["element_id"], "part": "WHOLE"}))
    pf = doc.get("pool_finish")
    if pf:
        src = A3018._src_of(doc, pf["source_task"])
        after, rec = pool_line(pid, rev, docs, pf, src)
        if after["line_id"] in have:
            raise ValueError(f"{METHOD}: the pool finish line repeats a candidate line id")
        log["lines"] += 1
        log["pool_bound_m2"] = rec["bound"]["surface_m2"]
        changes.append(A305._change(
            "OUTDOOR_FLOOR", "ADD", None, after, drawing_reference=src["file"],
            held=[{"what": f"{POOL_FINISH_ITEM} {pf['element_id']}", "why": pf["material_item"],
                   "bound_m2": rec["bound"]["surface_m2"]}],
            downstream=[], verification={"task": src["task"], "merge_commit": src["merge_commit"],
                                         "verifier_run": src["checker_run"], "ledger": src["file"],
                                         "ledger_sha256": src["sha256"]},
            evidence_status="HELD", codes=["OUTDOOR_FLOOR", "POOL_WATER_FACE"], group=pf["element_id"], record=rec,
            guard_element={"element_id": after["location"]["element_id"], "part": "WHOLE"}))
    return changes, log, clo


def changes_for(doc, l3024):
    """-> (changes, logs, closure). The guard re-check runs over the result (arch_v307) with the added lines."""
    if not doc:
        return [], [{"piece": "OUTDOOR_FLOOR", "state": "NO_PROJECT_INPUT"}], None
    ch, log, clo = family_changes(doc, l3024)
    ch_g, log_g = A307.guard_changes(doc, l3024, ch, set())
    added = {c["after"]["line_id"] for c in ch}
    for c in ch_g:
        lid = c["before"]["line_id"]
        if lid in added:
            raise ValueError(f"{METHOD}: the guard flags a line this version adds ({lid})")
        A305._note(c["after"], f"(re-check run by {METHOD})")
    return ch + ch_g, [log, log_g], clo


# ================================================================================================ integrate / write
def check_outdoor_family(lines):
    """every line of the family states one state: a priced piece > 0 with an owner-approved / confirmed finish, a held
    finish keeps its area as [a, a] (never 0), the pool finish is BLANK with its bound; each element once."""
    out = {"lines": 0, "released_m2": 0.0, "held_material_m2": 0.0, "pool_blank": 0}
    seen = set()
    for ln in lines:
        rec = ((ln.get("calculation") or {}).get("inputs") or {}).get("outdoor_floor_v3025")
        if ln["item_code"] in ITEMS and not rec:
            raise ValueError(f"{METHOD}: {ln['line_id']} ({ln['item_code']}) carries no outdoor-floor record")
        if not rec:
            continue
        out["lines"] += 1
        eid = ln["location"]["element_id"]
        if eid in seen:
            raise ValueError(f"{METHOD}: element {eid} in two outdoor-floor lines")
        seen.add(eid)
        ev = ln["evidence_state"]
        if ln["item_code"] == POOL_FINISH_ITEM:
            if ev != STATE_POOL or ln.get("measured_net") is not None or ln.get("bounded_range") is not None \
                    or not (rec.get("bound") or {}).get("surface_m2"):
                raise ValueError(f"{METHOD}: the pool finish {ln['line_id']} is BLANK with its bound (never a figure)")
            out["pool_blank"] += 1
        elif rec["material_status"] == "HELD":
            br = ln.get("bounded_range") or {}
            if ev != STATE_HELD or ln["item_code"] != MATERIAL_HELD_ITEM or not (_num(br.get("low")) and br["low"] > 0):
                raise ValueError(f"{METHOD}: held-finish piece {ln['line_id']} keeps its area as a held range")
            out["held_material_m2"] = _r(out["held_material_m2"] + br["high"])
        else:
            if ev != "SOURCE_DERIVED" or not (ln.get("measured_net") or 0) > 0 or ln["item_code"] == MATERIAL_HELD_ITEM:
                raise ValueError(f"{METHOD}: piece {ln['line_id']} with a stated finish is a quantity > 0 on its item")
            out["released_m2"] = _r(out["released_m2"] + ln["measured_net"])
    return out


def integrate(l3024, changes, for_lead=()):
    """-> (V3.0.25 lines, identity). Every V3.0.24 line is byte-identical; only the outdoor-floor lines are added."""
    from engine.source import boq_line as BL
    sid = {ln["line_id"] for ln in l3024}
    adds, rep = [], {}
    for c in changes:
        if c["action"] == "ADD":
            if c["piece"] != "OUTDOOR_FLOOR" or c["after"]["item_code"] not in FAMILY_ITEMS:
                raise ValueError(f"{METHOD}: only the outdoor-floor piece adds, and only its items")
            if c["after"]["line_id"] in sid:
                raise ValueError(f"{METHOD}: an added line repeats a V3.0.24 line id")
            adds.append(c["after"])
        elif c["action"] == "REPLACE" and c["piece"] == "DEFAULT_GUARD":
            lid = c["before"]["line_id"]
            if lid in rep or lid not in sid:
                raise ValueError(f"{METHOD}: guard line {lid} changed twice or not in V3.0.24")
            rep[lid] = c["after"]
        else:
            raise ValueError(f"{METHOD}: action {c['action']} of {c['piece']} (this version only adds outdoor lines)")
    if rep:
        raise ValueError(f"{METHOD}: the guard re-check changed {len(rep)} V3.0.24 line(s): every V3.0.24 line stays "
                         "byte-identical in this version")
    out = list(l3024) + adds
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
    par = A3023.check_parapet_family(out)
    state = A3024.check_line_state(out, for_lead)
    fam = check_outdoor_family(out)
    pids = {(ln["project"]["project_id"], ln["project"]["revision_set_sha256"]) for ln in out}
    if len(pids) != 1:
        raise ValueError(f"{METHOD}: {len(pids)} project identities in the lines (one project, one revision set)")
    by24 = {ln["line_id"]: ln for ln in l3024}
    outside = out[:len(l3024)]
    bad = [ln["line_id"] for ln in outside if A30.line_sha(by24[ln["line_id"]]) != A30.line_sha(ln)]
    if bad:
        raise ValueError(f"{METHOD}: {len(bad)} V3.0.24 line(s) differ")
    ident = {"v3_0_24_lines": len(l3024), "v3_0_25_lines": len(out), "v3_0_25_rows": len(changes),
             "replaced": 0, "added": len(adds), "outside_rows": len(outside),
             "outside_rows_identical_to_v3_0_24": len(outside), "outdoor_family": fam, "parapet_family": par,
             "wall_tile_family": tile, "line_state": state,
             "outside_rows_sha256": hashlib.sha256("".join(A30.line_sha(x) for x in outside).encode()).hexdigest()}
    return out, ident


def ledger_rows(changes, released_lines=None):
    rel = {A30._key(ln): ln for ln in released_lines or ()}
    rows = []
    for c in changes:
        if c["piece"] != "OUTDOOR_FLOOR":
            continue
        ref = c["after"]
        b29 = None
        if released_lines is not None:
            b29 = A30._qty(rel[A30._key(ref)]) if A30._key(ref) in rel else dict(A30._qty(None),
                                                                                 state="NOT_IN_RELEASED")
        rec = ref["calculation"]["inputs"]["outdoor_floor_v3025"]
        loc = ref.get("location") or {}
        rows.append({"version": METHOD, "piece": rec["piece"], "line_id": ref["line_id"],
                     "item_code": ref["item_code"], "floor": loc.get("floor"), "element_id": loc.get("element_id"),
                     "unit": ref["unit"], "before_released_v2_9": b29,
                     "before_v3_0_24": dict(A30._qty(None), state="NOT_IN_V3_0_24"), "after_v3_0_25": A30._qty(ref),
                     "evidence_status": rec["evidence_status"], "area_status": rec.get("area_status"),
                     "material": rec.get("material"), "material_status": rec.get("material_status"),
                     "material_source": rec.get("material_source"), "material_item": rec.get("material_item"),
                     "area_basis": rec.get("area_basis"), "edges": rec.get("edges"), "derived": rec.get("derived"),
                     "bound": rec.get("bound"), "rim_height_m": rec.get("rim_height_m"),
                     "rim_height_source": rec.get("rim_height_source"), "owner_manual": rec.get("owner_manual"),
                     "freelancer": rec.get("freelancer"), "flags": rec.get("flags"),
                     "release_status": "NOT RELEASED",
                     "owner_manual_method": ref["calculation"]["inputs"]["owner_manual_method"],
                     "drawing_derived_method": ref["calculation"]["inputs"]["drawing_derived_method"],
                     "verification": c.get("verification") or {}, "rollback": ROLLBACK})
    return rows


LEDGER_CSV = ("version", "piece", "line_id", "item_code", "floor", "element_id", "unit", "v2_9", "v3_0_24", "v3_0_25",
              "evidence_status", "area_status", "material", "material_status", "material_source_or_item",
              "area_basis", "edges", "owner_manual", "freelancer", "verification")
DIFF_CSV = ("line_id", "item_code", "floor", "element_id", "unit", "vs_v3_0_24", "vs_released_v2_9", "v2_9",
            "v3_0_24", "v3_0_25")
CLOSURE_CSV = ("kind", "what", "m2", "note")


def _fmt_q(q):
    return A302._q(q) if q else ""


def ledger_csv(rows):
    return A305._csv([{"version": r["version"], "piece": r["piece"], "line_id": r["line_id"],
                       "item_code": r["item_code"], "floor": r["floor"], "element_id": r["element_id"],
                       "unit": r["unit"], "v2_9": _fmt_q(r["before_released_v2_9"]),
                       "v3_0_24": _fmt_q(r["before_v3_0_24"]), "v3_0_25": _fmt_q(r["after_v3_0_25"]),
                       "evidence_status": r["evidence_status"], "area_status": r["area_status"] or "",
                       "material": r["material"] or "", "material_status": r["material_status"] or "",
                       "material_source_or_item": str(r["material_source"] or r["material_item"] or "")[:300],
                       "area_basis": str(r["area_basis"] or (r["bound"] and f"bound {r['bound']}") or "")[:400],
                       "edges": str(r["edges"] or r["rim_height_source"] or "")[:400],
                       "owner_manual": (f"{r['owner_manual']['formula']} = {r['owner_manual']['m2']} m2"
                                        if r["owner_manual"] else ""),
                       "freelancer": (f"{r['freelancer'].get('row')}: {r['freelancer'].get('m2')} m2 "
                                      f"({r['freelancer'].get('note')})"[:300] if r["freelancer"] else ""),
                       "verification": f"{r['verification'].get('task')} {r['verification'].get('merge_commit') or ''}"
                                       f" {r['verification'].get('verifier_run') or ''}".strip()[:300]}
                      for r in rows], LEDGER_CSV)


def closure_csv(clo, doc):
    rows = [{"kind": "FACE", "what": f"{clo['face_id']} filled", "m2": clo["filled_m2"], "note": clo["filled_source"]}]
    for h in clo["holes"]:
        rows.append({"kind": "HOLE_EXACT", "what": h["what"], "m2": h["exact_m2"],
                     "note": f"edges {h['edges']}; tessellated {h['tessellated_m2']}, residual "
                             f"{h['tessellation_residual_m2']}"})
    for p in doc["pieces"]:
        rows.append({"kind": f"PIECE_{p['kind']}", "what": p["piece"], "m2": p["area_m2"],
                     "note": f"{p['item_code']}; {p['area_status']}; {p['material']} {p['material_status']}"})
    rows += [{"kind": "NET_EXACT", "what": "face less holes", "m2": clo["face_net_exact_m2"], "note": ""},
             {"kind": "PLAN_SUM", "what": "plan pieces", "m2": clo["plan_pieces_m2"], "note": ""},
             {"kind": "DIFFERENCE", "what": "plan pieces - face net", "m2": clo["difference_m2"],
              "note": f"tolerance {clo['tolerance_m2']}"},
             {"kind": "REFERENCE", "what": "earlier total", "m2": clo["reference_total_m2"],
              "note": f"{clo['reference_source']}; plan pieces - reference {clo['vs_reference_m2']}"}]
    for x in doc.get("cross_check") or ():
        rows.append({"kind": "CROSS_CHECK", "what": f"{x['line_id']} {x.get('item_code') or ''} "
                                                    f"{x.get('element_id') or ''}".strip(),
                     "m2": x["shared_m2"], "note": x["why"][:300]})
    return A305._csv(rows, CLOSURE_CSV)


def diff_rows(l3024, l3025, released_lines=None):
    b24 = {ln["line_id"]: ln for ln in l3024}
    rel = {A30._key(ln): ln for ln in released_lines or ()}
    out = []
    for ln in l3025:
        o = b24.get(ln["line_id"])
        vs = "ADDED" if o is None else ("SAME" if A30.line_sha(o) == A30.line_sha(ln) else
                                        ("CHANGED" if A30._qty(o) != A30._qty(ln) else "CHANGED_TEXT_ONLY"))
        r = rel.get(A30._key(ln)) if released_lines is not None else None
        vs29 = None if released_lines is None else ("NOT_IN_RELEASED" if r is None else
                                                    ("SAME_QUANTITY" if A30._qty(r) == A30._qty(ln) else
                                                     "QUANTITY_DIFFERS"))
        out.append({"line_id": ln["line_id"], "item_code": ln["item_code"], "floor": ln["location"].get("floor"),
                    "element_id": ln["location"].get("element_id"), "unit": ln["unit"], "vs_v3_0_24": vs,
                    "vs_released_v2_9": vs29, "v2_9": A302._q(A30._qty(r)) if r else "",
                    "v3_0_24": A302._q(A30._qty(o)) if o else "", "v3_0_25": A302._q(A30._qty(ln))})
    return out


def write(out, l3024, changes, logs, clo, doc, released_lines=None, for_lead=()):
    """the V3_0_25_* files beside the V3_0_24_* files. -> (file names, identity, ledger)."""
    from pathlib import Path
    from engine.source import boq_line as BL
    out = Path(out)
    l3025, ident = integrate(l3024, changes, for_lead)
    rows = ledger_rows(changes, released_lines)
    diff = diff_rows(l3024, l3025, released_lines)
    dsum = {}
    for d in diff:
        dsum.setdefault("vs_v3_0_24", {}).setdefault(d["vs_v3_0_24"], 0)
        dsum["vs_v3_0_24"][d["vs_v3_0_24"]] += 1
        if d["vs_released_v2_9"] is not None:
            dsum.setdefault("vs_released_v2_9", {}).setdefault(d["vs_released_v2_9"], 0)
            dsum["vs_released_v2_9"][d["vs_released_v2_9"]] += 1
    v = dsum.get("vs_v3_0_24") or {}
    if v.get("CHANGED") or v.get("CHANGED_TEXT_ONLY"):
        raise ValueError(f"{METHOD}: a V3.0.24 line moved (this version only adds lines)")
    ident = dict(ident, diff=dsum, closure=clo)
    t24, t25 = A304.code_totals(l3024), A304.code_totals(l3025)
    moved = {k: {"v3_0_24": t24.get(k), "v3_0_25": t25.get(k)} for k in sorted(set(t24) | set(t25))
             if t24.get(k) != t25.get(k)}
    fam = set(FAMILY_ITEMS)
    if any(not any(str(k).startswith(c) for c in fam) for k in moved):
        raise ValueError(f"{METHOD}: totals moved outside the outdoor-floor family: {sorted(moved)[:5]}")
    led = {"schema": LEDGER_SCHEMA, "method": METHOD, "extends": EXTENDS, "candidate": CANDIDATE,
           "base": A30.BASE_METHOD, "released": A30.RELEASED_METHOD, "released_default": False, "rows": rows,
           "closure": clo, "cross_check": doc.get("cross_check") or [], "waiting_pieces": WAITING,
           "integration_package": True}
    run = {"method": METHOD, "policy": POLICY_ID, "extends": EXTENDS, "candidate": CANDIDATE,
           "base_method": A30.BASE_METHOD, "released_method": A30.RELEASED_METHOD, "released_default": False,
           "rollback": ROLLBACK, "identity": ident, "pieces": PIECES, "piece_logs": logs,
           "items": {k: list(v) for k, v in ITEMS.items()}, "totals_moved_by_code": moved, "waiting_pieces": WAITING}
    files = {"V3_0_25_BOQ_LINES.json": BL.dumps(l3025),
             "V3_0_25_BOQ_LINES.csv": A30._lines_csv(l3025),
             "V3_0_25_INTEGRATION_LEDGER.json": A30._j(led),
             "V3_0_25_INTEGRATION_LEDGER.csv": ledger_csv(rows),
             "V3_0_25_CLOSURE.csv": closure_csv(clo, doc),
             "V3_0_25_DIFF.csv": A305._csv(diff, DIFF_CSV),
             "V3_0_25_RUN.json": A30._j(run)}
    for name, text in files.items():
        (out / name).write_text(text, encoding="utf-8")
    return sorted(files), ident, led


def policy_record():
    return {"method": METHOD, "extends": EXTENDS, "pieces": sorted(PIECES), "inputs_schema": INPUTS_SCHEMA,
            "released_default": False, "rollback": ROLLBACK, "items": sorted(ITEMS)}


__all__ = ["METHOD", "PIECES", "WAITING", "ITEMS", "DEFAULT_GUARD_CLASS", "INPUTS_SCHEMA", "load_inputs", "d_outline",
           "closure", "piece_line", "pool_line", "family_changes", "changes_for", "check_outdoor_family", "integrate",
           "ledger_rows", "diff_rows", "write", "InputsError"]
