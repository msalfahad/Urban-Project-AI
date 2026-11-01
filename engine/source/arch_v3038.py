"""ARCH_TAKEOFF_V3.0.38 (T-421): the SAME opt-in BOQ candidate as ARCH_TAKEOFF_V3.0 .. V3.0.37 (engine.source.arch_v30,
arch_v301 .. arch_v3037), extended with two Checker-verified pieces, wired in ONE step so that no m2 is counted twice:

  STAIR_ROOM_FLOOR  (T-418 MERGED 361f6e47, R-T418-1) the floored parts of walled stair rooms, the silent omission of
             family B3-01: NEW floor-finish lines (area DRAWING-CONFIRMED; finish as the merged table states it: named
             by the owner -> FIN.FLOOR.PORCELAIN, not settled -> FIN.FLOOR.FINISH_HELD, a floor-finish line whose area
             is a quantity and whose material is HELD by name, never folded into the porcelain or marble totals), an
             unread strip as a HELD bound line (0 .. its area, never 0), and in the SAME step the stair room's
             FIN.MARBLE.LANDING upper bound reduced by the floor parts it contained (else a double count; Checker
             condition);
  LIFT_ENTRANCE     (T-413 MERGED ae87deb1, R-T413-1 .. 7; register ruling LIFT LANDING THRESHOLD 2026-11-01 08:15)
             per lift landing door: NEW B6-07 threshold marble (m2 = drawn clear width x depth, the depth ASSUMED -
             OWNER-APPROVED UP-ELEV-005; + the exposed front edge m.l), NEW B6-06 surround (HELD, a bound: the door
             height is printed nowhere); the ARCH.THRESHOLD LIFT_LANDING wall-band line lists the element without a
             quantity (it lies inside the B6-07 footprint); the landing floor-finish line deducts the threshold's floor
             part: the certain part (footprint depth - wall band) comes out of the net, the rest of the range (the
             threshold's position across the band is not drawn) stays a HELD named deduction beside, never a chosen
             value;
  FLOOR_BED         (R-T420-1, the T-420 method unchanged) a B3-05 bed pair (m2 = the finish net, installed m3 = the
             owner Q-45 range, drawing bound of the room's own zone beside) for each NEW valued floor-finish line, and
             the existing bed pair of a finish line whose net this package moves is RESTATED to the new net (a bed m2
             is its finish net, always).

Nothing else moves: every V3.0.37 line not named by the inputs is byte-identical (asserted); totals move only in the
codes these pieces own (asserted). Files: V3_0_38_BOQ_LINES.json / .csv, V3_0_38_INTEGRATION_LEDGER.json / .csv,
V3_0_38_DIFF.csv, V3_0_38_RUN.json. Nothing here names a project, a sheet, a layer or a coordinate.

R-T421-1 (every villa; integrates R-T418-1, R-T413-1 .. 7, R-T420-1): ONE physical floor area, ONE quantity:
(a) a floor part added from a stair room leaves the landing bound that held it in the same version (bound high reduced
by exactly the floor parts inside it, never below 0; a HELD unread part stays inside the bound, it may be landing); (b) a lift threshold is ONE element of B6-07: the wall-band line and
the landing floor line list it, the band without a quantity, the floor line with its floor part deducted (certain part
from the net, the position-dependent rest HELD beside), so B6-07 + band + floor never exceed the drawn footprint; (c) a
bed pair always equals its finish net: moving a finish net restates its bed in the same version; (d) a material not
settled by drawing or owner is a HELD finish on a valued area, never a chosen material; held is never 0.
"""

from __future__ import annotations

import copy
import hashlib

from engine.source import arch_v30 as A30
from engine.source import arch_v302 as A302
from engine.source import arch_v304 as A304
from engine.source import arch_v305 as A305
from engine.source import arch_v3018 as A3018
from engine.source import arch_v3030 as A3030
from engine.source import arch_v3031 as A3031
from engine.source import arch_v3032 as A3032
from engine.source import arch_v3033 as A3033
from engine.source import arch_v3034 as A3034
from engine.source import arch_v3035 as A3035
from engine.source import arch_v3036 as A3036
from engine.source import arch_v3037 as A3037

DEFAULT_GUARD_CLASS = "TOOLING"          # T-212: re-books checker-merged ledgers; adds no default value
METHOD = "ARCH_TAKEOFF_V3.0.38"
EXTENDS = A3037.METHOD
CANDIDATE = A30.METHOD
POLICY_ID = "URBAN_BOQ_T421_ARCH_V3_0_38"
INPUTS_SCHEMA = "URBAN_V3038_INPUTS_V1"
LEDGER_SCHEMA = "URBAN_V3038_INTEGRATION_LEDGER_V1"
ROLLBACK = A30.ROLLBACK
InputsError = A3031.InputsError
_r = A3018._r
_fmt = A3030._fmt
RULE_ID, RULE_VERSION = "R-T421-1", "T-421"
REC_KEY = "stair_lift_v3038"
P_FLOOR, P_LIFT, P_BED = "STAIR_ROOM_FLOOR", "LIFT_ENTRANCE", "FLOOR_BED"
OWNER_STATUS = "ASSUMED — OWNER-APPROVED"
DC = "DRAWING-CONFIRMED"
TOL = 0.00006                                # the merged tables print 4 decimals

FIN_HELD = "FIN.FLOOR.FINISH_HELD"
LIFT_THR, LIFT_SUR = "FIN.MARBLE.LIFT_THRESHOLD", "FIN.MARBLE.LIFT_SURROUND"
LANDING = "FIN.MARBLE.LANDING"
BAND = "ARCH.THRESHOLD"
FINISH_CODES = A3037.FINISH_CODES + (FIN_HELD,)
NEW_ITEMS = {   # en, ar, trade, subtrade
    FIN_HELD: ("Floor finish of a floored part, material HELD (porcelain or marble not settled by drawing or owner; "
               "B3-01)", "تشطيب أرضية - نوع المادة معلق", "FLOOR_FINISH", "FLOOR_FINISH_HELD"),
    LIFT_THR: ("Elevator threshold marble at the landing door (B6-07; installed)", "عتبة رخام المصعد",
               "MARBLE", "LIFT_THRESHOLD"),
    LIFT_SUR: ("Elevator outer door surround marble, left / top / right (B6-06; union area)", "رخام حول باب المصعد",
               "MARBLE", "LIFT_SURROUND"),
}
OWN_CODES = (FIN_HELD, LIFT_THR, LIFT_SUR, "FIN.FLOOR.PORCELAIN", LANDING, BAND, A3037.BED_DRY, A3037.BED_WET)
FAMILY = {FIN_HELD: "B3-01", "FIN.FLOOR.PORCELAIN": "B3-01", LIFT_THR: "B6-07", LIFT_SUR: "B6-06",
          A3037.BED_DRY: "B3-05", A3037.BED_WET: "B3-05"}

PIECES = {
    P_FLOOR: {"module": "engine/source/arch_v3038.py (stair-room floor parts as B3-01 lines + the landing bound "
                        "reduced in the same step)", "policy": "STAIR_ROOM_FLOOR_V1", "rule_id": "R-T418-1",
              "owner_rules": ["Q-70 A (2F lobby porcelain; arrival marble)", "UP-STAIR-005 (a landing is marble)",
                              "URBAN-DRY-FLOOR-PORCELAIN-DEFAULT@v1 (never on a STAIR face)",
                              "ELEMENT_REGISTER ROOM WITH NO FLOOR-FINISH LINE (04:15), STAIR-ROOM FLOOR PART vs "
                              "LANDING BOUND (08:15)", "UP-QTY-STATUS-001 (held is blank, never 0)"],
              "owner_manual_method": "owner method: the floor-finish area of every floored space, by room, finish by "
                                     "the schedule or the owner's rule; a landing (UP-STAIR-005) is stair marble",
              "drawing_method": "stair room face partitioned (R-T418-1): treads B7 / floor B3-01 / void / solid / "
                                "unread, re-adding to the face; floor parts at a printed level"},
    P_LIFT: {"module": "engine/source/arch_v3038.py (B6-07 threshold + B6-06 surround per landing door; band line "
                       "listed without a quantity; landing floor line deducts the threshold's floor part)",
             "policy": "LIFT_ENTRANCE_MARBLE_V1", "rule_id": "R-T413-1..7",
             "owner_rules": ["UP-ELEV-001 .. 005 (URBAN_PROJECTS_RULE_LIBRARY 1.4.0, owner_confirmed)",
                             "ELEMENT_REGISTER LIFT LANDING THRESHOLD (Lead 2026-11-01 08:15)"],
             "owner_manual_method": "owner method per landing door: threshold = drawn width x 0.50 m depth (UP-ELEV-005) "
                                    "+ front edge m.l; surround = union of 0.50 m bands left / top / right (UP-ELEV-002 "
                                    "/ 003), needs the door height",
             "drawing_method": "clear width between the drawn jambs; faces beside the jambs; the door height and the "
                               "threshold depth / position are printed nowhere"},
    P_BED: {"module": "engine/source/arch_v3038.py (R-T420-1 beds for the new floor lines; bed pairs restated to a "
                      "moved finish net)", "policy": "FLOOR_BED_V1", "rule_id": "R-T420-1",
            "owner_rules": ["Q-41", "Q-45 (dry 0.03 .. 0.04 m, wet 0.04 .. 0.06 m, a range)"],
            "owner_manual_method": A3037.PIECES[A3037.PIECE]["owner_manual_method"],
            "drawing_method": A3037.PIECES[A3037.PIECE]["drawing_method"]},
}
WAITING = dict(A3037.WAITING)
WAITING.pop("T420_BED_FOLLOWS_T421", None)
WAITING.update({
    "T421_GF_STAIR_HALL_FINISH": "the GF stair-room floor parts (hall +1.00, back lobby +0.30): area a quantity, finish "
                                 "HELD by name (porcelain if a floor, marble if a landing, UP-STAIR-005; no printed "
                                 "landing depth, no finish schedule): designer / finish-schedule list",
    "T421_GF_STAIR_STRIP": "the 0.200 strip north of the GF stair divider: two unread lines, HELD 0 .. its area",
    "T421_LIFT_DOOR_HEIGHT": "the landing-door clear height is printed nowhere: B6-06 surround HELD with its bound per "
                             "station (lift supplier / RFI L-1)",
    "T421_LIFT_2F_RIGHT_BAND": "2F landing: 0.400 m of face before the internal corner (the 0.50 default does not fit): "
                               "right band HELD 0 .. 0.400 (architect detail)",
    "T421_THRESHOLD_POSITION": "the threshold's position across the shaft wall band is not drawn: the landing floor "
                               "deducts its certain floor part, the rest stays a HELD named deduction",
})

ACTIONS = ("ADD_FLOOR", "ADD_HELD_PART", "REDUCE_BOUND", "ADD_THRESHOLD", "ADD_SURROUND", "LIST_BAND",
           "DEDUCT_FLOOR", "ADD_BED", "RESTATE_BED")


# ================================================================================================ inputs
def _need(s, keys, where):
    for k in keys:
        if s.get(k) in (None, ""):
            raise InputsError(f"{where}: {k} missing")


def _num(x, where, pos=False):
    if not isinstance(x, (int, float)) or isinstance(x, bool) or x != x:
        raise InputsError(f"{where}: {x!r} is not a number")
    if x < 0 or (pos and x == 0):
        raise InputsError(f"{where}: {x!r} is {'not positive' if pos else 'negative'}")
    return float(x)


def _metres(x, where):
    v = _num(x, where, True)
    if v > 20:
        raise InputsError(f"{where}: {v} is not a length in metres (mm refused)")
    return v


def load_inputs(doc, project_id=None):
    """URBAN_V3038_INPUTS_V1 -> the validated doc.
    {"schema", "project_id", "sources": [{"task", "file", "sha256", "merge_commit", "checker_run"}],
     "owner_bed": {"DRY"|"WET": {"lo", "hi", "rule"}}, "b_upper": {zone: {"b", "source"}},
     "floor_parts": [{"part", "room", "floor", "level", "area", "item_code", "finish", "finish_status", "area_status",
                      "zone", "b", "template_line", "threshold_station" | None, "source_tasks"}],
     "held_parts": [{"part", "room", "floor", "low", "high", "why", "template_line", "source_tasks"}],
     "landing_bounds": [{"line_id", "high_before", "parts": [part ids], "source_tasks"}],
     "stations": [{"station", "floor", "opening", "width", "width_status", "depth", "depth_status", "band", "front_edge",
                   "surround_low", "surround_high", "surround_held", "band_line", "floor_line" | None, "floor_part" | None,
                   "template_line", "source_tasks"}],
     "restate_beds": [{"finish_line", "zone"}]}"""
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

    def tasks(r, where):
        if not r.get("source_tasks") or any(t not in srcs for t in r["source_tasks"]):
            raise InputsError(f"{where}: no merged source named")

    owner = {}
    for k in A3037.KINDS:
        o = (doc.get("owner_bed") or {}).get(k)
        if not o:
            raise InputsError(f"owner bed range for {k} missing (no default thickness: DEFAULTED_THICKNESS)")
        _need(o, ("rule",), f"owner {k}")
        lo, hi = _num(o.get("lo"), f"owner {k} lo", True), _num(o.get("hi"), f"owner {k} hi", True)
        if lo > hi or hi > 0.2:
            raise InputsError(f"owner {k}: {lo} .. {hi} m is not a bed range in metres")
        owner[k] = dict(o, lo=lo, hi=hi)
    bup = {}
    for z, v in (doc.get("b_upper") or {}).items():
        _need(v, ("source",), f"b_upper {z}")
        bup[z] = dict(v, b=_num(v.get("b"), f"b_upper {z}", True))

    parts, pids = [], set()
    for r in doc.get("floor_parts") or ():
        where = f"floor part {r.get('part')}"
        _need(r, ("part", "room", "floor", "level", "item_code", "finish_status", "area_status", "zone",
                  "template_line"), where)
        tasks(r, where)
        if r["part"] in pids:
            raise InputsError(f"{where}: named twice")
        pids.add(r["part"])
        a = r.get("area")
        if isinstance(a, (int, float)) and not isinstance(a, bool) and abs(a) < 1e-9:
            raise InputsError(f"{where}: HELD_AS_ZERO: a floor part of 0 m2 is refused")
        a = _num(a, f"{where} area", True)
        if r["item_code"] not in ("FIN.FLOOR.PORCELAIN", FIN_HELD):
            raise InputsError(f"{where}: {r['item_code']} (a stair-room floor part is B3-01: porcelain when named, "
                              f"else {FIN_HELD})")
        if r["item_code"] == "FIN.FLOOR.PORCELAIN" and r["finish_status"] not in (DC, OWNER_STATUS, "VERIFIED"):
            raise InputsError(f"{where}: a porcelain line needs a settled finish (status {r['finish_status']!r}); an "
                              f"unsettled finish is {FIN_HELD}")
        if r["item_code"] == FIN_HELD and r["finish_status"] != "HELD":
            raise InputsError(f"{where}: {FIN_HELD} carries finish status HELD")
        if r["area_status"] not in (DC, OWNER_STATUS, "VERIFIED"):
            raise InputsError(f"{where}: area status {r['area_status']!r}")
        b = r.get("b")
        if b is not None:
            b = _num(b, f"{where} b", True)
            if b > 0.3:
                raise InputsError(f"{where}: b {b} is not a build-up in metres")
        parts.append(dict(r, _area=a, _b=b))
    held = []
    for r in doc.get("held_parts") or ():
        where = f"held part {r.get('part')}"
        _need(r, ("part", "room", "floor", "why", "template_line"), where)
        tasks(r, where)
        if r["part"] in pids:
            raise InputsError(f"{where}: named twice")
        pids.add(r["part"])
        lo, hi = _num(r.get("low"), f"{where} low"), _num(r.get("high"), f"{where} high", True)
        if lo > hi:
            raise InputsError(f"{where}: low above high")
        held.append(dict(r, _lo=lo, _hi=hi))
    bounds = []
    for r in doc.get("landing_bounds") or ():
        where = f"landing bound {r.get('line_id')}"
        _need(r, ("line_id",), where)
        tasks(r, where)
        _num(r.get("high_before"), f"{where} high_before", True)
        fp = {x["part"] for x in parts}
        if not r.get("parts") or any(p not in fp for p in r["parts"]):
            raise InputsError(f"{where}: the floor parts inside it are not floor parts of this package (a HELD part "
                              f"may be landing or tread: it stays inside the bound)")
        bounds.append(dict(r))
    stations, sids = [], set()
    for r in doc.get("stations") or ():
        where = f"station {r.get('station')}"
        _need(r, ("station", "floor", "opening", "width_status", "depth_status", "band_line", "template_line"), where)
        tasks(r, where)
        if r["station"] in sids:
            raise InputsError(f"{where}: named twice (one door, one station)")
        sids.add(r["station"])
        w, d = _metres(r.get("width"), f"{where} width"), _metres(r.get("depth"), f"{where} depth")
        band = _metres(r.get("band"), f"{where} band")
        if d < band:
            raise InputsError(f"{where}: depth {d} below the wall band {band}")
        if r["depth_status"] not in (DC, OWNER_STATUS):
            raise InputsError(f"{where}: THRESHOLD_DEPTH_NOT_ESTABLISHED (depth status {r['depth_status']!r}: drawn, "
                              f"or the owner's UP-ELEV-005 depth with its source)")
        if r["depth_status"] == OWNER_STATUS and not r.get("depth_source"):
            raise InputsError(f"{where}: an owner-approved depth names its source")
        if r["width_status"] != DC:
            raise InputsError(f"{where}: the threshold width is the drawn clear width (status {r['width_status']!r})")
        fe = _metres(r.get("front_edge"), f"{where} front edge")
        if abs(fe - w) > 1e-9:
            raise InputsError(f"{where}: front edge {fe} is not the clear width {w}")
        slo, shi = _num(r.get("surround_low"), f"{where} surround low", True), _num(r.get("surround_high"),
                                                                                     f"{where} surround high", True)
        if slo > shi:
            raise InputsError(f"{where}: surround low above high")
        if bool(r.get("floor_line")) == bool(r.get("floor_part")):
            raise InputsError(f"{where}: the threshold's floor part lands on ONE floor line (existing or new)")
        if r.get("floor_part") and r["floor_part"] not in pids:
            raise InputsError(f"{where}: floor part {r['floor_part']} is not added by this package")
        stations.append(dict(r, _w=w, _d=d, _band=band, _fe=fe, _slo=slo, _shi=shi,
                             _certain=_r(w * (d - band)), _rest=_r(w * band)))
    rb = []
    for r in doc.get("restate_beds") or ():
        _need(r, ("finish_line", "zone"), "restate bed")
        rb.append(dict(r))
    if not parts and not stations:
        raise InputsError("no floor part and no station in the inputs")
    return dict(doc, _sources=srcs, _owner=owner, _b_upper=bup, _parts=parts, _held=held, _bounds=bounds,
                _stations=stations, _restate=rb)


# ================================================================================================ helpers
def _ver(srcs):
    return {"task": "+".join(s["task"] for s in srcs), "merge_commit": srcs[0]["merge_commit"],
            "merge_commits": [s["merge_commit"] for s in srcs],
            "verifier_run": "; ".join(s["checker_run"] for s in srcs), "ledger": "; ".join(s["file"] for s in srcs)}


def _rec(piece, srcs, **kw):
    return dict({"piece": piece, "policy": PIECES[piece]["policy"], "tasks": [s["task"] for s in srcs],
                 "ledgers": [s["file"] for s in srcs], "ledger_sha256": [s["sha256"] for s in srcs],
                 "merge_commits": [s["merge_commit"] for s in srcs], "checker_runs": [s["checker_run"] for s in srcs],
                 "rule_id": RULE_ID, "rule_version": RULE_VERSION, "release_status": "NOT RELEASED"}, **kw)


def _common(tpl, item_code, element_id, room_id=None, floor=None):
    loc = tpl["location"]
    en, ar, tr, sub = NEW_ITEMS[item_code] if item_code in NEW_ITEMS else (tpl["item_en"], tpl["item_ar"],
                                                                           tpl["trade"], tpl.get("subtrade"))
    return dict(project_id=tpl["project"]["project_id"], revision_set_sha256=tpl["project"]["revision_set_sha256"],
                item_code=item_code, element_id=element_id, floor=floor or loc.get("floor"),
                room_id=room_id or loc.get("room_id"), room_name_en=loc.get("room_name_en"),
                room_name_ar=loc.get("room_name_ar"), documents=copy.deepcopy(tpl["source"]["documents"]),
                geometry_source=tpl["source"]["geometry_source"],
                geometry_confidence=tpl["source"]["geometry_confidence"], rule_id=RULE_ID, rule_version=RULE_VERSION,
                material_state="PROJECT_OWNER_FACT", item_en=en, item_ar=ar, trade=tr, subtrade=sub)


def _fin(ln):
    from engine.source import boq_line as BL
    ln["project"] = copy.deepcopy(ln["project"])
    return BL.validate(ln)


def _bed_lines_of(lines):
    """finish line id -> {'m2': line, 'm3': line} for the V3.0.37 beds."""
    out = {}
    for ln in lines:
        rec = ((ln.get("calculation") or {}).get("inputs") or {}).get(A3037.REC_KEY)
        if ln["item_code"] in A3037.NEW_ITEMS and rec:
            out.setdefault(rec["finish_line"], {})[ln["unit"]] = ln
    return out


# ================================================================================================ pieces
def _floor_line(p, tpl, srcs, deduction=None):
    from engine.source import boq_line as BL
    a = p["_area"]
    net = _r(a - deduction["certain"]) if deduction else a
    eid = f"{p['room']}:{p['part']}"
    ded = []
    if deduction:
        ded = [{"id": deduction["line"], "what": f"B6-07 lift threshold {deduction['station']} floor part (certain)",
                "area": deduction["certain"], "status": OWNER_STATUS,
                "held_more": [0.0, deduction["rest"]], "held_why": "threshold position across the wall band not drawn"}]
    finish_txt = (f"finish {p.get('finish')} ({p['finish_status']})" if p["item_code"] != FIN_HELD
                  else f"finish HELD by name: {p.get('finish')}")
    state = "SOURCE_DERIVED" if p["area_status"] in (DC, "VERIFIED") else "PROVISIONAL"
    rec = _rec(P_FLOOR, srcs, action="ADD_FLOOR", part=p["part"], room=p["room"], level=p["level"],
               area_status=p["area_status"], finish_status=p["finish_status"], finish=p.get("finish"),
               evidence_status=(p["area_status"] if p["finish_status"] != OWNER_STATUS else OWNER_STATUS),
               zone=p["zone"], family="B3-01", owner_trade="FLOOR FINISHES (B3-01)",
               threshold_deduction=ded or None)
    formula = (f"floor part {p['part']} of stair room {p['room']} at {p['level']}: {_fmt(a)} m2 ({p['area_status']}, "
               f"merged {'+'.join(p['source_tasks'])})")
    if deduction:
        formula += (f" - B6-07 threshold {deduction['station']} floor part {_fmt(deduction['certain'])} m2 certain "
                    f"(+ 0 .. {_fmt(deduction['rest'])} HELD by position) = {_fmt(net)} m2")
    ln = BL.make_line(unit="m2", evidence_state=state, measured_net=net, gross=a,
                      deductions=[{"id": d["id"], "unit": "m2", "qty": d["area"], "what": d["what"]} for d in ded],
                      formula=formula + f"; {finish_txt}",
                      inputs={REC_KEY: rec, "evidence_status": rec["evidence_status"]},
                      physical_element=f"floor finish of the floored part {p['part']} of {p['room']}",
                      notes=(f"{METHOD}: B3-01 floor part from the merged stair-room table (R-T418-1); {finish_txt}; "
                             f"never folded into the landing marble bound; NOT RELEASED"),
                      **_common(tpl, p["item_code"], eid, room_id=p["room"], floor=p["floor"]))
    return _fin(ln)


def _held_line(h, tpl, srcs):
    from engine.source import boq_line as BL
    eid = f"{h['room']}:{h['part']}"
    rec = _rec(P_FLOOR, srcs, action="ADD_HELD_PART", part=h["part"], room=h["room"], evidence_status="HELD",
               family="B3-01", why=h["why"])
    ln = BL.make_line(unit="m2", evidence_state="BOUNDED_EXPOSURE", measured_net=None,
                      bounded_range={"low": h["_lo"], "high": h["_hi"], "basis": h["why"][:300]},
                      formula=(f"unread part {h['part']} of {h['room']}: HELD {_fmt(h['_lo'])} .. {_fmt(h['_hi'])} m2 "
                               f"({h['why']})")[:700],
                      inputs={REC_KEY: rec, "evidence_status": "HELD"},
                      physical_element=f"unread strip {h['part']} of {h['room']} (floor, balustrade or wall)",
                      notes=f"{METHOD}: HELD bound, never 0; no bed follows a held part; NOT RELEASED",
                      **_common(tpl, FIN_HELD, eid, room_id=h["room"], floor=h["floor"]))
    return _fin(ln)


def _reduce_bound(ln, high_after, parts, srcs):
    new = copy.deepcopy(ln)
    br = dict(new["bounded_range"])
    before = br["high"]
    br["high"] = high_after
    br["basis"] = (f"{br.get('basis') or ''} | {METHOD}: upper bound {_fmt(before)} - floor parts "
                   f"{', '.join(parts)} now B3-01 lines = {_fmt(high_after)} m2")[-300:]
    new["bounded_range"] = br
    new["calculation"] = copy.deepcopy(new["calculation"])
    new["calculation"]["formula"] = (f"{new['calculation']['formula']} | {METHOD}: bound high {_fmt(before)} -> "
                                     f"{_fmt(high_after)} (floor parts {', '.join(parts)} moved to B3-01, "
                                     f"R-T418-1 / R-T421-1)")
    new["calculation"]["inputs"] = dict(new["calculation"]["inputs"] or {})
    new["calculation"]["inputs"][REC_KEY] = _rec(P_FLOOR, srcs, action="REDUCE_BOUND", high_before=before,
                                                 high_after=high_after, parts=list(parts), evidence_status="HELD")
    new["notes"] = f"{new.get('notes') or ''} | {METHOD}: landing bound reduced by the stair-room floor parts"
    return _fin(new)


SCOPE_KEY = "floor_scope_v3014"


def _supersede_scope(new, why):
    """an older floor-scope record (V3.0.14) on a line this version changes by a Checker-verified ruling is kept whole,
    wrapped as superseded (its own guard then skips it); this version's check_lift() carries its invariant forward
    (the band area / the settled figure before the deduction). -> the old record or None."""
    inp = new["calculation"]["inputs"]
    old = inp.get(SCOPE_KEY)
    if isinstance(old, dict) and "kind" in old:
        inp[SCOPE_KEY] = {"superseded_by": METHOD, "rule": RULE_ID, "why": why, "record": old}
        return old
    return None


def _band_listed(ln, thr_line, station, srcs):
    new = copy.deepcopy(ln)
    q = A302._q(A30._qty(ln))
    new["evidence_state"] = "NOT_APPLICABLE_WITH_EVIDENCE"
    new["measured_net"] = None
    new["bounded_range"] = None
    new["gross"] = None
    new["calculation"] = copy.deepcopy(new["calculation"])
    before_formula = new["calculation"]["formula"]
    new["calculation"]["formula"] = (f"{METHOD}: the lift-door wall band at {station} lies inside the B6-07 lift "
                                     f"threshold footprint (line {thr_line}): listed here, no quantity; its area is "
                                     f"the threshold's (register LIFT LANDING THRESHOLD; the former reading is kept in "
                                     f"calculation.inputs.{REC_KEY}.formula_before)")
    new["calculation"]["inputs"] = dict(new["calculation"]["inputs"] or {})
    old = _supersede_scope(new, "register LIFT LANDING THRESHOLD (Lead 2026-11-01 08:15): the band lies inside the "
                                "B6-07 threshold footprint; listed without a quantity, the area is the threshold's")
    new["calculation"]["inputs"][REC_KEY] = _rec(P_LIFT, srcs, action="LIST_BAND", station=station,
                                                 owned_by=thr_line, was=q, evidence_status="NOT_APPLICABLE",
                                                 formula_before=before_formula,
                                                 scope_superseded=(old or {}).get("kind"),
                                                 band_area_before=(old or {}).get("area_m2"))
    new["notes"] = (f"{new.get('notes') or ''} | {METHOD}: ONE element: the lift threshold {station} (B6-07, line "
                    f"{thr_line}) owns this band; listed without a quantity (R-T421-1 b)")
    return _fin(new)


def _deduct_floor(ln, st, thr_line, srcs):
    new = copy.deepcopy(ln)
    before = ln["measured_net"]
    net = _r(before - st["_certain"])
    if net <= 0:
        raise InputsError(f"floor line {ln['line_id']}: the threshold deduction exceeds its net")
    new["measured_net"] = net
    new["deductions"] = list(new.get("deductions") or []) + [
        {"id": thr_line, "unit": "m2", "qty": st["_certain"],
         "what": f"B6-07 lift threshold {st['station']} floor part (certain); 0 .. {_fmt(st['_rest'])} more HELD by position"}]
    new["calculation"] = copy.deepcopy(new["calculation"])
    new["calculation"]["formula"] = (f"{new['calculation']['formula']} | {METHOD}: - B6-07 lift threshold "
                                     f"{st['station']} floor part {_fmt(st['_certain'])} m2 certain ({_fmt(st['_w'])} x "
                                     f"({_fmt(st['_d'])} - band {_fmt(st['_band'])})) + 0 .. {_fmt(st['_rest'])} HELD by "
                                     f"position: net {_fmt(before)} - {_fmt(st['_certain'])} = {_fmt(net)} m2")
    new["calculation"]["inputs"] = dict(new["calculation"]["inputs"] or {})
    old = _supersede_scope(new, f"B6-07 lift threshold {st['station']}: the certain floor part leaves this finish net "
                                f"(register LIFT LANDING THRESHOLD); the settled figure before it is net_before")
    if old and old.get("kind") == "SETTLE_RANGE" and old.get("kept_m2") is not None \
            and abs(float(old["kept_m2"]) - before) > 1e-6:
        raise InputsError(f"floor line {ln['line_id']}: its settled figure {old['kept_m2']} is not its net {before}")
    new["calculation"]["inputs"][REC_KEY] = _rec(P_LIFT, srcs, action="DEDUCT_FLOOR", station=st["station"],
                                                 scope_superseded=(old or {}).get("kind"),
                                                 threshold_line=thr_line, net_before=before, net_after=net,
                                                 certain=st["_certain"], held_more=[0.0, st["_rest"]],
                                                 evidence_status=OWNER_STATUS)
    new["notes"] = (f"{new.get('notes') or ''} | {METHOD}: threshold floor part deducted (certain), the rest HELD 0 .. "
                    f"{_fmt(st['_rest'])} m2 by position (R-T421-1 b)")
    return _fin(new)


def _station_lines(st, tpl, srcs):
    from engine.source import boq_line as BL
    eid = f"LIFT:{st['station']}"
    a = _r(st["_w"] * st["_d"])
    rec = _rec(P_LIFT, srcs, action="ADD_THRESHOLD", station=st["station"], opening=st["opening"], width=st["_w"],
               width_status=st["width_status"], depth=st["_d"], depth_status=st["depth_status"],
               depth_source=st.get("depth_source"), band=st["_band"], floor_part_certain=st["_certain"],
               floor_part_held_more=[0.0, st["_rest"]], band_line=st["band_line"],
               floor_line=st.get("floor_line") or st.get("floor_part"), evidence_status=OWNER_STATUS, family="B6-07",
               owner_trade="B6 (register LIFT LANDING THRESHOLD)")
    c = _common(tpl, LIFT_THR, eid, floor=st["floor"])
    m2 = BL.make_line(unit="m2", evidence_state="PROVISIONAL", measured_net=a, gross=a,
                      formula=(f"lift threshold {st['station']} at {st['opening']}: clear width {_fmt(st['_w'])} m "
                               f"(drawn jambs, {st['width_status']}) x depth {_fmt(st['_d'])} m ({st['depth_status']}, "
                               f"{st.get('depth_source')}) = {_fmt(a)} m2; ONE element: the wall band line "
                               f"{st['band_line']} and the landing floor line list it"),
                      inputs={REC_KEY: rec, "evidence_status": OWNER_STATUS},
                      physical_element=f"marble threshold piece at the lift landing door {st['station']}",
                      notes=f"{METHOD}: B6-07 threshold m2 (UP-ELEV-005); NOT RELEASED", **c)
    rec_e = dict(rec, unit="lm", evidence_status=DC)
    lm = BL.make_line(unit="lm", evidence_state="SOURCE_DERIVED", measured_net=st["_fe"], gross=st["_fe"],
                      formula=(f"exposed front edge of the lift threshold {st['station']} = the drawn clear width "
                               f"{_fmt(st['_fe'])} m ({st['width_status']}; UP-ELEV-005 keeps the edge beside the area)"),
                      inputs={REC_KEY: rec_e, "evidence_status": DC},
                      physical_element=f"front edge of the marble threshold {st['station']}",
                      notes=(f"{METHOD}: B6-07 front edge m.l, the edge work of the same piece, never a second area; "
                             f"NOT RELEASED"), **dict(c, element_id=f"{eid}:edge"))
    rec_s = _rec(P_LIFT, srcs, action="ADD_SURROUND", station=st["station"], evidence_status="HELD", family="B6-06",
                 low=st["_slo"], high=st["_shi"], held=st.get("surround_held"),
                 formula=st.get("surround_formula"), owner_trade="B6")
    su = BL.make_line(unit="m2", evidence_state="BOUNDED_EXPOSURE", measured_net=None,
                      bounded_range={"low": st["_slo"], "high": st["_shi"],
                                     "basis": (f"union area A(h) {st.get('surround_formula')}; h printed nowhere: "
                                               f"{st.get('surround_held')}")[:300]},
                      formula=(f"lift door surround {st['station']} (left / top / right, union area, UP-ELEV-003): "
                               f"{st.get('surround_formula')}; HELD {_fmt(st['_slo'])} .. {_fmt(st['_shi'])} m2 "
                               f"({st.get('surround_held')})")[:700],
                      inputs={REC_KEY: rec_s, "evidence_status": "HELD"},
                      physical_element=f"marble surround of the lift landing door {st['station']}",
                      notes=(f"{METHOD}: B6-06 surround HELD with its bound (door height not printed), never 0; never "
                             f"part of the wall tile / plaster / paint quantities; NOT RELEASED"),
                      **_common(tpl, LIFT_SUR, f"{eid}:surround", floor=st["floor"]))
    return [_fin(m2), _fin(lm), _fin(su)]


def _bed_pair(fin, kind, zone, b, bh, owner, srcs, area_status, membrane="NONE", layer="MORTAR_BED"):
    """a R-T420-1 bed pair for a finish line, built by the T-420 builder (unchanged)."""
    if area_status not in A3037.AREA_STATUS:
        raise InputsError(f"bed of {fin['line_id']}: area status {area_status!r}")
    r = {"kind": kind, "layer": layer, "zone": zone, "source_tasks": [s["task"] for s in srcs],
         "area_status": area_status, "membrane_in_room": membrane, "_b": b, "_bh": bh}
    m2, m3, dbound = A3037._beds(fin, r, owner, srcs)
    return m2, m3, dbound


# ================================================================================================ changes
def changes_for(doc, l3037):
    """-> (changes, log). Each change: piece, action, before (a V3.0.37 line or None), after."""
    if not doc:
        return [], {"piece": "+".join((P_FLOOR, P_LIFT, P_BED)), "state": "NO_PROJECT_INPUT"}
    if any(ln["item_code"] in NEW_ITEMS or ((ln.get("calculation") or {}).get("inputs") or {}).get(REC_KEY)
           for ln in l3037):
        raise InputsError("the candidate already carries V3.0.38 lines (applied once)")
    by = {ln["line_id"]: ln for ln in l3037}
    beds = _bed_lines_of(l3037)
    S = doc["_sources"]
    changes, seen = [], set(by)
    log = {"piece": "+".join((P_FLOOR, P_LIFT, P_BED)), "state": "RUN", "sources": doc["sources"], "by_action": {},
           "lines_added": 0, "lines_changed": 0}

    def tpl_of(r, where):
        t = by.get(r["template_line"])
        if t is None:
            raise InputsError(f"{where}: template line {r['template_line']} not in the candidate (stale binding)")
        return t

    def add(piece, action, after, before=None, **kw):
        if before is None:
            if after["line_id"] in seen:
                raise ValueError(f"{METHOD}: added line {after['location']['element_id']} repeats an id")
            seen.add(after["line_id"])
            log["lines_added"] += 1
        else:
            if before["line_id"] != after["line_id"]:
                raise ValueError(f"{METHOD}: a changed line keeps its id")
            log["lines_changed"] += 1
        log["by_action"][action] = log["by_action"].get(action, 0) + 1
        srcs = kw.pop("srcs")
        changes.append(A305._change(piece, "ADD" if before is None else "CHANGE", before, after,
                                    step=action, drawing_reference="; ".join(s["file"] for s in srcs),
                                    verification=_ver(srcs), downstream=kw.pop("downstream", []),
                                    group=after["item_code"], **kw))

    # ---- lift stations: threshold lines first (their ids are what the band / floor lines name)
    st_thr, st_by_part = {}, {}
    for st in doc["_stations"]:
        srcs = [S[t] for t in st["source_tasks"]]
        tpl = tpl_of(st, f"station {st['station']}")
        band = by.get(st["band_line"])
        if band is None or band["item_code"] != BAND or band["evidence_state"] != "BOUNDED_EXPOSURE":
            raise InputsError(f"station {st['station']}: band line {st['band_line']} is not an ARCH.THRESHOLD bound "
                              f"(stale binding)")
        bq = band["bounded_range"]
        if abs(bq["high"] - st["_w"] * st["_band"]) > TOL:
            raise InputsError(f"station {st['station']}: band line {bq['high']} m2 is not {st['_w']} x {st['_band']}")
        m2, lm, su = _station_lines(st, tpl, srcs)
        st_thr[st["station"]] = m2["line_id"]
        for ln, act, ev in ((m2, "ADD_THRESHOLD", OWNER_STATUS), (lm, "ADD_THRESHOLD", DC), (su, "ADD_SURROUND", "HELD")):
            held = ([{"what": f"{LIFT_SUR} {st['station']}", "why": str(st.get("surround_held"))[:300],
                      "range": [st["_slo"], st["_shi"]], "scenario": "door height not printed"}] if ln is su else [])
            add(P_LIFT, act, ln, srcs=srcs, evidence_status=ev, held=held, station=st["station"])
        add(P_LIFT, "LIST_BAND", _band_listed(band, m2["line_id"], st["station"], srcs), before=band, srcs=srcs,
            evidence_status="NOT_APPLICABLE", held=[], station=st["station"])
        if st.get("floor_part"):
            st_by_part[st["floor_part"]] = st
        else:
            fl = by.get(st["floor_line"])
            if fl is None or fl["item_code"] not in A3037.FINISH_CODES or fl["evidence_state"] not in A3037.VALUED_STATES:
                raise InputsError(f"station {st['station']}: floor line {st['floor_line']} is not a valued floor-finish "
                                  f"line (stale binding)")
            new = _deduct_floor(fl, st, m2["line_id"], srcs)
            held = [{"what": f"{fl['item_code']} {fl['location']['element_id']} threshold floor part beyond the "
                             f"certain {_fmt(st['_certain'])} m2", "why": "threshold position across the wall band not drawn",
                     "range": [0.0, st["_rest"]], "scenario": "deduction 0 .. rest by position"}]
            add(P_LIFT, "DEDUCT_FLOOR", new, before=fl, srcs=srcs, evidence_status=OWNER_STATUS, held=held,
                station=st["station"], downstream=["the bed pair of this finish line (restated)"])
            by[fl["line_id"]] = new

    # ---- stair-room floor parts
    new_floor = {}
    for p in doc["_parts"]:
        srcs = [S[t] for t in p["source_tasks"]]
        tpl = tpl_of(p, f"floor part {p['part']}")
        st = st_by_part.pop(p["part"], None)
        ded = None
        if st:
            ded = {"station": st["station"], "line": st_thr[st["station"]], "certain": st["_certain"],
                   "rest": st["_rest"]}
        ln = _floor_line(p, tpl, srcs, ded)
        held = ([{"what": f"{ln['item_code']} {ln['location']['element_id']} threshold floor part beyond the certain",
                  "why": "threshold position across the wall band not drawn", "range": [0.0, ded["rest"]],
                  "scenario": "deduction 0 .. rest by position"}] if ded else [])
        if p["item_code"] == FIN_HELD:
            held.append({"what": f"{ln['item_code']} {ln['location']['element_id']} material",
                         "why": str(p.get("finish"))[:300], "range": None, "scenario": "finish HELD by name"})
        add(P_FLOOR, "ADD_FLOOR", ln, srcs=srcs, evidence_status=ln["calculation"]["inputs"]["evidence_status"],
            held=held, part=p["part"])
        new_floor[p["part"]] = (ln, p, srcs)
    if st_by_part:
        raise InputsError(f"station floor part(s) {sorted(st_by_part)} not added")
    for h in doc["_held"]:
        srcs = [S[t] for t in h["source_tasks"]]
        ln = _held_line(h, tpl_of(h, f"held part {h['part']}"), srcs)
        add(P_FLOOR, "ADD_HELD_PART", ln, srcs=srcs, evidence_status="HELD",
            held=[{"what": f"{FIN_HELD} {ln['location']['element_id']}", "why": h["why"][:300],
                   "range": [h["_lo"], h["_hi"]], "scenario": "unread"}], part=h["part"])

    # ---- landing bounds, reduced in the same step
    area_of = {p["part"]: new_floor[p["part"]][1]["_area"] for p in doc["_parts"]}
    for r in doc["_bounds"]:
        srcs = [S[t] for t in r["source_tasks"]]
        ln = by.get(r["line_id"])
        if ln is None or ln["item_code"] != LANDING or ln["evidence_state"] != "BOUNDED_EXPOSURE":
            raise InputsError(f"landing bound {r['line_id']}: not a FIN.MARBLE.LANDING bound (stale binding)")
        hb = ln["bounded_range"]["high"]
        if abs(hb - r["high_before"]) > TOL:
            raise InputsError(f"landing bound {r['line_id']}: high {hb} is not the table's {r['high_before']}")
        inside = sum(area_of[p] for p in r["parts"])
        after = _r(hb - inside)
        if after < -1e-9:
            raise InputsError(f"landing bound {r['line_id']}: the floor parts exceed the bound")
        after = max(after, 0.0)
        add(P_FLOOR, "REDUCE_BOUND", _reduce_bound(ln, after, r["parts"], srcs), before=ln, srcs=srcs,
            evidence_status="HELD", held=[{"what": f"{LANDING} {ln['location']['element_id']}",
                                           "why": "landing extent not printed", "range": [ln["bounded_range"]["low"],
                                                                                         after],
                                           "scenario": "bound"}])

    # ---- beds: new floor lines, then restated beds of moved finish lines
    owner = doc["_owner"]
    for part, (ln, p, srcs) in new_floor.items():
        b = p["_b"]
        bh = None
        if b is not None:
            u = doc["_b_upper"].get(p["zone"])
            bh = u["b"] if u else b
        m2, m3, dbound = _bed_pair(ln, "DRY", p["zone"], b, bh, owner, srcs, p["area_status"])
        for x in (m2, m3):
            x["calculation"]["inputs"][REC_KEY] = _rec(P_BED, srcs, action="ADD_BED", finish_line=ln["line_id"],
                                                       part=part, evidence_status=x["calculation"]["inputs"][
                                                           "evidence_status"])
            _fin(x)
        held = [{"what": f"{m3['item_code']} {m3['location']['element_id']} drawn layer", "why": dbound["missing"][:300],
                 "range": ([dbound["low"], dbound["high"]] if dbound["high"] is not None else None),
                 "scenario": "drawing bound beside the owner range"}]
        add(P_BED, "ADD_BED", m2, srcs=srcs, evidence_status=m2["calculation"]["inputs"]["evidence_status"], held=[],
            bound_to=ln["line_id"])
        add(P_BED, "ADD_BED", m3, srcs=srcs, evidence_status=OWNER_STATUS, held=held, bound_to=ln["line_id"],
            drawing_bound=dbound)
    for r in doc["_restate"]:
        fl = by.get(r["finish_line"])
        pair = beds.get(r["finish_line"])
        if fl is None or not pair or set(pair) != {"m2", "m3"}:
            raise InputsError(f"restate bed {r['finish_line']}: no V3.0.37 bed pair on it")
        old2, old3 = pair["m2"], pair["m3"]
        rec = old3["calculation"]["inputs"][A3037.REC_KEY]
        db = rec.get("drawing_bound") or {}
        cause = [S[t] for t in ("T-414", "T-413") if t in S]
        m2, m3, dbound = _bed_pair(fl, rec["kind"], rec.get("zone"), db.get("b"), db.get("b_upper"), owner, cause,
                                   rec["area_status"], rec.get("membrane_in_room") or "NONE", rec.get("layer") or "MORTAR_BED")
        # the T-420 record names the T-414 table it was bound by: keep its provenance, add the restatement's cause
        for new, old in ((m2, old2), (m3, old3)):
            orec = old["calculation"]["inputs"][A3037.REC_KEY]
            nrec = new["calculation"]["inputs"][A3037.REC_KEY]
            for k in ("tasks", "ledgers", "ledger_sha256", "merge_commits", "checker_runs"):
                nrec[k] = list(orec.get(k) or []) + [x for x in nrec.get(k) or [] if x not in (orec.get(k) or [])]
        for new, old in ((m2, old2), (m3, old3)):
            if new["line_id"] != old["line_id"]:
                raise ValueError(f"{METHOD}: a restated bed keeps its id ({old['line_id']})")
            new["calculation"]["inputs"][REC_KEY] = _rec(P_BED, cause, action="RESTATE_BED",
                                                         finish_line=fl["line_id"], before=A302._q(A30._qty(old)),
                                                         evidence_status=new["calculation"]["inputs"][
                                                             "evidence_status"])
            new["notes"] = f"{new['notes']} | {METHOD}: restated to the finish net moved by the lift threshold"
        held = [{"what": f"{m3['item_code']} {m3['location']['element_id']} drawn layer", "why": dbound["missing"][:300],
                 "range": ([dbound["low"], dbound["high"]] if dbound["high"] is not None else None),
                 "scenario": "drawing bound beside the owner range"}]
        add(P_BED, "RESTATE_BED", _fin(m2), before=old2, srcs=cause,
            evidence_status=m2["calculation"]["inputs"]["evidence_status"], held=[], bound_to=fl["line_id"])
        add(P_BED, "RESTATE_BED", _fin(m3), before=old3, srcs=cause, evidence_status=OWNER_STATUS, held=held,
            bound_to=fl["line_id"], drawing_bound=dbound)
    log["by_action"] = dict(sorted(log["by_action"].items()))
    return changes, log


# ================================================================================================ checks
def check_beds(lines):
    """A3037.check_beds widened to the B3-01 codes of this version (FIN.FLOOR.FINISH_HELD is a valued floor-finish
    line whose material is held): one m2 + one m3 per bed, a measure pair, bound to a valued floor-finish line, m2 =
    its net, m3 a positive owner range."""
    by = {ln["line_id"]: ln for ln in lines}
    pairs, out = {}, {"beds": 0, "lines": 0, "by_code": {}}
    for ln in lines:
        if ln["item_code"] not in A3037.NEW_ITEMS:
            continue
        rec = ((ln.get("calculation") or {}).get("inputs") or {}).get(A3037.REC_KEY)
        if not rec or rec.get("action") != "BED":
            raise ValueError(f"{METHOD}: {ln['line_id']} is not a bed line")
        fin = by.get(rec["finish_line"])
        if fin is None or fin["item_code"] not in FINISH_CODES or fin["evidence_state"] not in A3037.VALUED_STATES:
            raise ValueError(f"{METHOD}: bed {ln['line_id']} is not bound to a valued floor-finish line")
        mp = ln.get("measure_pair") or {}
        if mp.get("price_one_basis") is not True or ln["line_id"] not in (mp.get("lines") or ()):
            raise ValueError(f"{METHOD}: bed {ln['line_id']} is not in its measure pair")
        if ln["unit"] == "m2":
            if ln["evidence_state"] != fin["evidence_state"] or abs(ln["measured_net"] - fin["measured_net"]) > 1e-9:
                raise ValueError(f"{METHOD}: bed m2 {ln['line_id']} is not its finish line's net (R-T421-1 c)")
        elif ln["unit"] == "m3":
            br = ln.get("bounded_range") or {}
            if (ln["evidence_state"] != "BOUNDED_EXPOSURE" or ln.get("measured_net") is not None
                    or not br.get("high") or br["low"] <= 0):
                raise ValueError(f"{METHOD}: bed m3 {ln['line_id']} is not a positive owner range")
        else:
            raise ValueError(f"{METHOD}: bed {ln['line_id']} unit {ln['unit']}")
        k = ln["location"]["element_id"]
        pairs.setdefault(k, {})
        if ln["unit"] in pairs[k]:
            raise ValueError(f"{METHOD}: bed {k} carries two {ln['unit']} lines")
        pairs[k][ln["unit"]] = ln["line_id"]
        out["lines"] += 1
        key = f"{ln['item_code']}|{ln['unit']}"
        out["by_code"][key] = out["by_code"].get(key, 0) + 1
    fins = set()
    for k, v in pairs.items():
        if set(v) != set(A3037.ROW_UNITS):
            raise ValueError(f"{METHOD}: bed {k} has {sorted(v)}")
        f = by[v["m2"]]["calculation"]["inputs"][A3037.REC_KEY]["finish_line"]
        if f in fins:
            raise ValueError(f"{METHOD}: finish line {f} carries two beds")
        fins.add(f)
    for ln in lines:      # every valued floor-finish line of this version's codes carries a bed
        if ln["item_code"] == FIN_HELD and ln["evidence_state"] in A3037.VALUED_STATES and ln["line_id"] not in fins:
            raise ValueError(f"{METHOD}: valued floor part {ln['line_id']} carries no bed")
    out["beds"] = len(pairs)
    out["by_code"] = dict(sorted(out["by_code"].items()))
    return out


def check_lift(lines):
    """R-T421-1 (b): per lift station ONE threshold quantity. B6-07 m2 = width x depth; the band line it names is listed
    without a quantity and owned by it; the floor line it names deducts exactly its certain floor part (width x (depth
    - band)) and no more; B6-07 + band + certain floor deduction re-add to the footprint (overlap 0). -> summary."""
    by = {ln["line_id"]: ln for ln in lines}
    out = {"stations": 0, "threshold_m2": 0.0, "edge_lm": 0.0, "surround_low": 0.0, "surround_high": 0.0,
           "overlap_m2": 0.0, "floor_deducted_certain_m2": 0.0, "floor_held_more_m2": 0.0}
    for ln in lines:
        rec = ((ln.get("calculation") or {}).get("inputs") or {}).get(REC_KEY) or {}
        if ln["item_code"] == LIFT_SUR:
            if ln["evidence_state"] != "BOUNDED_EXPOSURE" or ln.get("measured_net") is not None:
                raise ValueError(f"{METHOD}: surround {ln['line_id']} is not HELD with its bound")
            out["surround_low"] = _r(out["surround_low"] + ln["bounded_range"]["low"])
            out["surround_high"] = _r(out["surround_high"] + ln["bounded_range"]["high"])
            continue
        if ln["item_code"] != LIFT_THR:
            continue
        if ln["unit"] == "lm":
            out["edge_lm"] = _r(out["edge_lm"] + ln["measured_net"])
            continue
        out["stations"] += 1
        out["threshold_m2"] = _r(out["threshold_m2"] + ln["measured_net"])
        if abs(ln["measured_net"] - rec["width"] * rec["depth"]) > 1e-9:
            raise ValueError(f"{METHOD}: threshold {ln['line_id']} is not width x depth")
        band = by.get(rec["band_line"])
        brec = ((band or {}).get("calculation") or {}).get("inputs", {}).get(REC_KEY) or {}
        if band is None or band["evidence_state"] != "NOT_APPLICABLE_WITH_EVIDENCE" or brec.get("owned_by") != ln["line_id"]:
            raise ValueError(f"{METHOD}: band {rec['band_line']} still carries a quantity beside threshold "
                             f"{ln['line_id']} (double count)")
        fl = by.get(rec["floor_line"]) or next((x for x in lines if x["location"].get("element_id", "").endswith(
            ":" + str(rec["floor_line"]))), None)
        ded = [d for d in ((fl or {}).get("deductions") or ()) if d.get("id") == ln["line_id"]]
        if fl is None or len(ded) != 1 or abs(ded[0]["qty"] - rec["floor_part_certain"]) > 1e-9:
            raise ValueError(f"{METHOD}: floor line of threshold {ln['line_id']} does not deduct its floor part once")
        frec = fl["calculation"]["inputs"].get(REC_KEY) or {}
        if frec.get("action") == "DEDUCT_FLOOR":
            if abs(fl["measured_net"] - (frec["net_before"] - rec["floor_part_certain"])) > 1e-6:
                raise ValueError(f"{METHOD}: floor line {fl['line_id']} net is not its net before less the floor part")
            sup = (fl["calculation"]["inputs"].get(SCOPE_KEY) or {}).get("record") or {}
            if sup.get("kind") == "SETTLE_RANGE" and abs(float(sup.get("kept_m2")) - frec["net_before"]) > 1e-6:
                raise ValueError(f"{METHOD}: floor line {fl['line_id']}: the superseded settled figure is not the net "
                                 f"before the deduction")
        bsup = (band["calculation"]["inputs"].get(SCOPE_KEY) or {}).get("record") or {}
        if bsup.get("kind") == "TO_THRESHOLD" and abs(float(bsup["area_m2"]) - rec["width"] * rec["band"]) > 1e-6:
            raise ValueError(f"{METHOD}: band {band['line_id']}: its superseded area is not the threshold's band part")
        fp = rec["width"] * rec["depth"]
        covered = rec["width"] * rec["band"] + rec["floor_part_certain"]
        if abs(covered - fp) > 1e-9:
            raise ValueError(f"{METHOD}: threshold {ln['line_id']} band + floor part {covered} is not the footprint {fp}")
        out["overlap_m2"] = _r(out["overlap_m2"] + 0.0)
        out["floor_deducted_certain_m2"] = _r(out["floor_deducted_certain_m2"] + rec["floor_part_certain"])
        out["floor_held_more_m2"] = _r(out["floor_held_more_m2"] + rec["floor_part_held_more"][1])
    return out


def check_landing(lines):
    """R-T421-1 (a): every floor part added here left the landing bound of its stair room. -> summary."""
    parts = {}
    for ln in lines:
        rec = ((ln.get("calculation") or {}).get("inputs") or {}).get(REC_KEY) or {}
        if rec.get("action") == "ADD_FLOOR":
            parts[rec["part"]] = ln
    moved = set()
    out = {"bounds": 0, "parts_moved": 0}
    for ln in lines:
        rec = ((ln.get("calculation") or {}).get("inputs") or {}).get(REC_KEY) or {}
        if rec.get("action") == "REDUCE_BOUND":
            out["bounds"] += 1
            if ln["bounded_range"]["high"] < -1e-9 or ln["bounded_range"]["high"] > rec["high_before"] + 1e-9:
                raise ValueError(f"{METHOD}: landing bound {ln['line_id']} not reduced within 0 .. its old high")
            moved.update(rec["parts"])
    if set(parts) - moved:
        raise ValueError(f"{METHOD}: floor part(s) {sorted(set(parts) - moved)} still inside a landing bound")
    out["parts_moved"] = len(moved)
    return out


# ================================================================================================ integrate / write
def integrate(l3037, changes, for_lead=()):
    """-> (V3.0.38 lines, identity). Changed lines replace their V3.0.37 line in place; added lines follow; every other
    V3.0.37 line is byte-identical (asserted)."""
    sid = {ln["line_id"]: i for i, ln in enumerate(l3037)}
    out = list(l3037)
    adds, repl = [], set()
    for c in changes:
        a = c["after"]
        if c["action"] == "ADD":
            if a["line_id"] in sid:
                raise ValueError(f"{METHOD}: an added line repeats a V3.0.37 id")
            if a["item_code"] not in NEW_ITEMS and a["item_code"] not in ("FIN.FLOOR.PORCELAIN",) + tuple(A3037.NEW_ITEMS):
                raise ValueError(f"{METHOD}: added code {a['item_code']} is not one this version adds")
            adds.append(a)
        elif c["action"] == "CHANGE":
            i = sid.get(a["line_id"])
            if i is None or a["line_id"] in repl:
                raise ValueError(f"{METHOD}: a changed line is not a V3.0.37 line or changes twice")
            if a["item_code"] not in OWN_CODES:
                raise ValueError(f"{METHOD}: {a['item_code']} is not a code this version may change")
            out[i] = a
            repl.add(a["line_id"])
        else:
            raise ValueError(f"{METHOD}: action {c['action']}")
    out = out + adds
    if len({ln["line_id"] for ln in out}) != len(out):
        raise ValueError(f"{METHOD}: a BOQ line id appears twice")
    guards = A3031._family_guards(out, for_lead)
    roof = A3031.check_roof_layers(out)
    ceil = A3032.check_ceilings(out)
    corr = A3033.check_corrections(out)
    zones = A3034.check_zones(out)
    fence = A3035.check_boundary(out)
    lists = A3036.check_lists(out)
    beds = check_beds(out)
    lift = check_lift(out)
    landing = check_landing(out)
    pids = {(ln["project"]["project_id"], ln["project"]["revision_set_sha256"]) for ln in out}
    if len(pids) != 1:
        raise ValueError(f"{METHOD}: {len(pids)} project identities in the lines")
    outside = [ln for ln in l3037 if ln["line_id"] not in repl]
    bad = [a["line_id"] for a in outside if A30.line_sha(a) != A30.line_sha(out[sid[a["line_id"]]])]
    if bad:
        raise ValueError(f"{METHOD}: {len(bad)} V3.0.37 line(s) differ outside the named changes")
    ident = {"v3_0_37_lines": len(l3037), "v3_0_38_lines": len(out), "v3_0_38_rows": len(changes),
             "replaced": len(repl), "added": len(adds), "outside_rows": len(outside),
             "outside_rows_identical_to_v3_0_37": len(outside), "beds": beds, "lift": lift, "landing": landing,
             "lists": lists, "fence": fence, "tile_zones": zones, "corrections": corr, "ceilings": ceil,
             "roof_buildup": roof, "guards": guards,
             "outside_rows_sha256": hashlib.sha256("".join(A30.line_sha(x) for x in outside).encode()).hexdigest()}
    return out, ident


def ledger_rows(changes, released_lines=None):
    rel = {A30._key(ln): ln for ln in released_lines or ()}
    rows = []
    for c in changes:
        ref = c["after"]
        rec = ref["calculation"]["inputs"].get(REC_KEY) or {}
        b29 = None
        if released_lines is not None:
            b29 = A30._qty(rel[A30._key(ref)]) if A30._key(ref) in rel else dict(A30._qty(None),
                                                                                 state="NOT_IN_RELEASED")
        loc = ref.get("location") or {}
        piece = c["piece"]
        rows.append({"version": METHOD, "piece": piece, "action": c.get("step"), "change": c["action"],
                     "line_id": ref["line_id"], "item_code": ref["item_code"], "floor": loc.get("floor"),
                     "element_id": loc.get("element_id"), "unit": ref["unit"],
                     "before_released_v2_9": b29, "before_v3_0_37": A30._qty(c.get("before")),
                     "after_v3_0_38": A30._qty(ref), "evidence_status": c.get("evidence_status"),
                     "still_held": c.get("held"), "bound_to": c.get("bound_to"), "station": c.get("station"),
                     "part": c.get("part"), "release_status": "NOT RELEASED",
                     "owner_manual_method": PIECES[piece]["owner_manual_method"],
                     "drawing_derived_method": PIECES[piece]["drawing_method"],
                     "record": rec, "verification": c.get("verification") or {}, "rollback": ROLLBACK})
    return rows


LEDGER_CSV = ("version", "piece", "action", "change", "line_id", "item_code", "floor", "element_id", "unit", "v2_9",
              "v3_0_37", "v3_0_38", "evidence_status", "still_held", "verification")
DIFF_CSV = ("line_id", "item_code", "floor", "element_id", "unit", "vs_v3_0_37", "vs_released_v2_9", "v2_9",
            "v3_0_37", "v3_0_38")


def ledger_csv(rows):
    def q(x):
        return A302._q(x) if x and (x.get("value") is not None or x.get("low") is not None) else ""

    def h(r):
        return "; ".join(f"{x['what']} {x['range']}" for x in (r.get("still_held") or ()))[:300]
    return A305._csv([{"version": r["version"], "piece": r["piece"], "action": r["action"], "change": r["change"],
                       "line_id": r["line_id"], "item_code": r["item_code"], "floor": r.get("floor") or "",
                       "element_id": r.get("element_id") or "", "unit": r["unit"],
                       "v2_9": q(r.get("before_released_v2_9")), "v3_0_37": q(r.get("before_v3_0_37")),
                       "v3_0_38": q(r.get("after_v3_0_38")), "evidence_status": r["evidence_status"],
                       "still_held": h(r),
                       "verification": f"{r['verification'].get('task')} "
                                       f"{' '.join(x[:8] for x in r['verification'].get('merge_commits') or ())}"}
                      for r in rows], LEDGER_CSV)


def diff_rows(l3037, l3038, released_lines=None):
    b37 = {ln["line_id"]: ln for ln in l3037}
    rel = {A30._key(ln): ln for ln in released_lines or ()}
    out = []
    for ln in l3038:
        o = b37.get(ln["line_id"])
        vs = "ADDED" if o is None else ("SAME" if A30.line_sha(o) == A30.line_sha(ln) else "CHANGED")
        r = rel.get(A30._key(ln)) if released_lines is not None else None
        vs29 = None if released_lines is None else ("NOT_IN_RELEASED" if r is None else
                                                    ("SAME_QUANTITY" if A30._qty(r) == A30._qty(ln) else
                                                     "QUANTITY_DIFFERS"))
        out.append({"line_id": ln["line_id"], "item_code": ln["item_code"], "floor": ln["location"].get("floor"),
                    "element_id": ln["location"].get("element_id"), "unit": ln["unit"], "vs_v3_0_37": vs,
                    "vs_released_v2_9": vs29, "v2_9": A302._q(A30._qty(r)) if r else "",
                    "v3_0_37": A302._q(A30._qty(o)) if o else "", "v3_0_38": A302._q(A30._qty(ln))})
    return out


def write(out, l3037, changes, log, released_lines=None, for_lead=()):
    """the V3_0_38_* files beside the V3_0_37_* files. -> (file names, identity, ledger)."""
    from pathlib import Path
    from engine.source import boq_line as BL
    out = Path(out)
    l3038, ident = integrate(l3037, changes, for_lead)
    rows = ledger_rows(changes, released_lines)
    diff = diff_rows(l3037, l3038, released_lines)
    named = {c["after"]["line_id"] for c in changes if c["action"] == "CHANGE"}
    stray = [d["line_id"] for d in diff if d["vs_v3_0_37"] == "CHANGED" and d["line_id"] not in named]
    if stray:
        raise ValueError(f"{METHOD}: {len(stray)} V3.0.37 line(s) changed outside the named changes")
    dsum = {}
    for d in diff:
        dsum.setdefault("vs_v3_0_37", {}).setdefault(d["vs_v3_0_37"], 0)
        dsum["vs_v3_0_37"][d["vs_v3_0_37"]] += 1
        if d["vs_released_v2_9"] is not None:
            dsum.setdefault("vs_released_v2_9", {}).setdefault(d["vs_released_v2_9"], 0)
            dsum["vs_released_v2_9"][d["vs_released_v2_9"]] += 1
    ident = dict(ident, diff=dsum)
    t37, t38 = A304.code_totals(l3037), A304.code_totals(l3038)
    moved = {k: {"v3_0_37": t37.get(k), "v3_0_38": t38.get(k)} for k in sorted(set(t37) | set(t38))
             if t37.get(k) != t38.get(k)}
    if any(k.split("|")[0] not in OWN_CODES for k in moved):
        raise ValueError(f"{METHOD}: totals moved outside this version's codes: {sorted(moved)[:5]}")
    led = {"schema": LEDGER_SCHEMA, "method": METHOD, "extends": EXTENDS, "candidate": CANDIDATE,
           "base": A30.BASE_METHOD, "released": A30.RELEASED_METHOD, "released_default": False, "rows": rows,
           "waiting_pieces": WAITING, "integration_package": True}
    run = {"method": METHOD, "policy": POLICY_ID, "extends": EXTENDS, "candidate": CANDIDATE,
           "base_method": A30.BASE_METHOD, "released_method": A30.RELEASED_METHOD, "released_default": False,
           "rollback": ROLLBACK, "identity": ident, "pieces": PIECES, "piece_logs": [log],
           "totals_moved_by_code": moved, "waiting_pieces": WAITING}
    files = {"V3_0_38_BOQ_LINES.json": BL.dumps(l3038),
             "V3_0_38_BOQ_LINES.csv": A30._lines_csv(l3038),
             "V3_0_38_INTEGRATION_LEDGER.json": A30._j(led),
             "V3_0_38_INTEGRATION_LEDGER.csv": ledger_csv(rows),
             "V3_0_38_DIFF.csv": A305._csv(diff, DIFF_CSV),
             "V3_0_38_RUN.json": A30._j(run)}
    for name, text in files.items():
        (out / name).write_text(text, encoding="utf-8")
    return sorted(files), ident, led


def policy_record():
    return {"method": METHOD, "extends": EXTENDS, "pieces": sorted(PIECES), "inputs_schema": INPUTS_SCHEMA,
            "released_default": False, "rollback": ROLLBACK, "actions": list(ACTIONS)}


__all__ = ["METHOD", "PIECES", "WAITING", "DEFAULT_GUARD_CLASS", "INPUTS_SCHEMA", "NEW_ITEMS", "load_inputs",
           "changes_for", "check_beds", "check_lift", "check_landing", "integrate", "ledger_rows", "diff_rows",
           "write", "InputsError"]
