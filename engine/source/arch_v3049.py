"""ARCH_TAKEOFF_V3.0.49 (T-310, stream F): the SAME opt-in BOQ candidate as ARCH_TAKEOFF_V3.0 .. V3.0.48
(engine.source.arch_v30, arch_v301 .. arch_v3048), extended with the WET-AREA WATERPROOFING fixes of the
Checker-verified T-303 inventory (merge 1d3f69b0) and the POOL MEMBRANE / SCREED lines of T-309 (merge 834ada3e) in
ONE step:

  WP_UPTURN     a wet-room upturn line whose run the inventory re-measured gets the run of waterproofing policy V3
                (engine.source.waterproofing_policy_v3 = V2 rows, UP-WP-002 2.0.0 / UP-WP-003 1.1.0): (boundary incl.
                the door crossings - the doorway segments) x 0.20; a WINDOW whose sill stands above the upturn is no
                opening of the run (never deducted); each doorway segment stays its own HELD row beside
                (DOORWAY_CONTINUATION_NOT_ESTABLISHED), never billed twice, never 0.
  WP_FLOOR      a wet floor line whose printed box holds a structural column intrusion is the box less the column
                (the room's drawn outline, as every other wet room): value from the merged pieces, the residual named.
  WP_NA         a membrane TERMINATION line on a window above the upturn (no physical membrane edge) and a DOORWAY
                TRANSITION line that repeats a door another line carries become NOT_APPLICABLE_WITH_EVIDENCE (no
                figure), the line that carries the door named.
  WP_DOOR       every DOORWAY TRANSITION (m2) line is keyed by its PHYSICAL door id (record only, quantity untouched);
                a door with no transition line gets one HELD BLANK line (BLOCKED_RFI, never 0): one per door (Q-35 C).
  POOL_LAYER    a printed pool protective layer with no line gets its line: membrane m2 and protection screed m3 on the
                protected concrete face, DRAWING-CONFIRMED (SOURCE_DERIVED), the unresolved upstand part HELD beside by
                name with its bound (never in the quantity), the membrane's function (WP or insulation) HELD by name.

R-T310-1 (every villa; integrates R-T303-WP-FAMILIES-1, R-T309-1, UP-WP-001 / -002 2.0.0 / -003 1.1.0, Q-35 C, Q-37 A,
UP-QTY-STATUS-001): (a) a re-valued line keeps its id, code, unit and location and moves only by its record's value,
which must be the policy's (upturn) or the merged closure's (floor) figure (asserted); (b) every wet-room doorway
transition line in a quantity, bounded or held state carries ONE physical door id and every door id is carried by ONE
such line; a duplicate is NOT_APPLICABLE naming the carrying line; a missing door is HELD BLANK; (c) a NOT_APPLICABLE
line carries no figure and states its evidence; (d) a pool layer line is booked on the protected face, never on the
water side, and its unresolved part is beside with its bound, never 0, never in the quantity; (e) nothing outside the
waterproofing codes moves.

Nothing else moves: every V3.0.48 line not named by the inputs is byte-identical (asserted); totals move only in the
waterproofing codes (asserted). Files: V3_0_49_BOQ_LINES.json / .csv, V3_0_49_INTEGRATION_LEDGER.json / .csv,
V3_0_49_DIFF.csv, V3_0_49_RUN.json. Nothing here names a project, a sheet, a layer or a coordinate.
"""

from __future__ import annotations

import copy
import hashlib
import re

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
from engine.source import arch_v3038 as A3038
from engine.source import arch_v3039 as A3039
from engine.source import arch_v3040 as A3040
from engine.source import arch_v3041 as A3041
from engine.source import arch_v3042 as A3042
from engine.source import arch_v3043 as A3043
from engine.source import arch_v3044 as A3044
from engine.source import arch_v3045 as A3045
from engine.source import arch_v3046 as A3046
from engine.source import arch_v3047 as A3047
from engine.source import arch_v3048 as A3048
from engine.source import waterproofing_policy_v3 as WP3

DEFAULT_GUARD_CLASS = "TOOLING"          # T-212: re-books checker-merged ledgers; adds no default value
METHOD = "ARCH_TAKEOFF_V3.0.49"
EXTENDS = A3048.METHOD
CANDIDATE = A30.METHOD
POLICY_ID = "URBAN_BOQ_T310_ARCH_V3_0_49"
INPUTS_SCHEMA = "URBAN_V3049_INPUTS_V1"
LEDGER_SCHEMA = "URBAN_V3049_INTEGRATION_LEDGER_V1"
ROLLBACK = A30.ROLLBACK
InputsError = A3031.InputsError
_r = A3018._r
_fmt = A3030._fmt
RULE_ID, RULE_VERSION = "R-T310-1", "T-310"
REC_KEY = "wet_area_wp_v3049"
P_UPTURN, P_FLOOR, P_NA, P_DOOR, P_POOL = "WP_UPTURN", "WP_FLOOR", "WP_NA", "WP_DOOR", "POOL_LAYER"
ACTIONS = ("REVALUE_UPTURN", "REVALUE_FLOOR", "NOT_APPLICABLE", "KEY_DOOR", "ADD_HELD_DOOR", "ADD_POOL_LAYER")
PIECE_OF = {"REVALUE_UPTURN": P_UPTURN, "REVALUE_FLOOR": P_FLOOR, "NOT_APPLICABLE": P_NA, "KEY_DOOR": P_DOOR,
            "ADD_HELD_DOOR": P_DOOR, "ADD_POOL_LAYER": P_POOL}
UPTURN, FLOOR, TERM = "FIN.WP.WALL_UPTURN", "FIN.WP.FLOOR", "FIN.WP.TERMINATION"
TRANS = "FIN.WP.DOORWAY_TRANSITION"
POOL_MEMBRANE, POOL_SCREED = "WP.POOL.MEMBRANE", "WP.POOL.PROTECTION_SCREED"
POOL_UNIT = {POOL_MEMBRANE: "m2", POOL_SCREED: "m3"}
POOL_TEXT = {POOL_MEMBRANE: ("Pool membrane on the base and outer wall faces (function held)",
                             "غشاء حوض السباحة على القاعدة والجدران الخارجية (الوظيفة معلقة)", "pool membrane"),
             POOL_SCREED: ("Pool protection screed 5 cm on the base and outer wall faces",
                           "طبقة حماية 5 سم لحوض السباحة على القاعدة والجدران الخارجية", "pool protection screed")}
WP_CODES = (UPTURN, FLOOR, TERM, TRANS, POOL_MEMBRANE, POOL_SCREED)
NA_CODES = (TERM, TRANS)
NA_STATE, HELD_STATE, VALUED_STATE = "NOT_APPLICABLE_WITH_EVIDENCE", "BLOCKED_RFI", "SOURCE_DERIVED"
EVIDENCE_STATUS = "DRAWING-CONFIRMED"     # WORKFLOW_CONTROLS s.5; VERIFIED is the Checker's word, never an input
TOL = 0.0000015
MAX_Q = 500.0                            # one wet-room / pool layer quantity in m2 or m3; above it is a unit slip
LINE_ID_RE = re.compile(r"^L-[0-9a-f]{20}$")
DOOR_RE = re.compile(r"^D-[0-9A-Z]{2}-[0-9]{2}(-[A-Z]+)?$")

PIECES = {
    P_UPTURN: {"module": "engine/source/arch_v3049.py (a wet-room upturn line re-valued by waterproofing policy V3: "
                         "boundary run excluding the doorway segments x 0.20; a window above the upturn is not deducted)",
               "policy": "WET_UPTURN_RUN_V3", "rule_id": "UP-WP-002 2.0.0 / UP-WP-003 1.1.0 (R-T310-1 a)",
               "owner_rules": ["UP-WP-002 2.0.0 (owner Q-03: upturn 0.20 m)",
                               "owner directive 2026-11-02 C3 (0.20 m, no door deduction: the doorway segment is its "
                               "own row)", "Q-35 C (walls only, one transition per physical door)",
                               "UP-QTY-STATUS-001 (held is blank, never 0)"],
               "owner_manual_method": "wet-room wall run at floor level less the door crossings x 0.20 m; the "
                                      "doorway segment its own row; a window above 0.20 m is wall below the upturn",
               "drawing_method": "the merged T-303 inventory (T-074 hand table) with the Checker's own re-measure of "
                                 "the room by handle: floor 2.250 x 2.100, boundary 8.700 lm, door 0.800, the 0.500 "
                                 "east opening a window with a printed sill 0.84 (T-144)"},
    P_FLOOR: {"module": "engine/source/arch_v3049.py (a wet floor line = the printed box less the structural column "
                        "intrusion drawn inside it)",
              "policy": "WET_FLOOR_BOX_LESS_COLUMN_V1", "rule_id": "UP-WP-001, Q-37 A (R-T310-1 a)",
              "owner_rules": ["Q-37 A (the pantry is wet within its printed 4.50 x 3.00 box)", "UP-WP-001 (floor face)",
                              "UP-QTY-STATUS-001"],
              "owner_manual_method": "membrane on the floor face of the wet area: printed box less what is not floor "
                                     "(a column standing in it)",
              "drawing_method": "the merged T-286 closure: box 13.500 - column notch 0.900 x 0.050 = 13.455 m2, "
                                "own re-read of the column outline and the box faces this run (0.045000 m2)"},
    P_NA: {"module": "engine/source/arch_v3049.py (a line with no physical element: NOT_APPLICABLE_WITH_EVIDENCE, no "
                     "figure, the evidence and the carrying line named)",
           "policy": "WP_LINE_NOT_APPLICABLE_V1", "rule_id": "R-T303-WP-FAMILIES-1 (R-T310-1 b, c)",
           "owner_rules": ["Q-35 C (one transition per physical door)", "UP-QTY-STATUS-001"],
           "owner_manual_method": "no membrane edge where the membrane runs on under a window; one transition per door",
           "drawing_method": "the merged T-303 inventory and the Checker's own count (2 doors twice, 3 doors none) "
                             "and window read (W18 sill 0.84 above the upturn)"},
    P_DOOR: {"module": "engine/source/arch_v3049.py (every transition m2 line keyed by its physical door; a missing "
                       "door gets a HELD BLANK line)",
             "policy": "WP_TRANSITION_PER_DOOR_V1", "rule_id": "R-T303-WP-FAMILIES-1 (R-T310-1 b)",
             "owner_rules": ["Q-35 C", "UP-WP-003 1.1.0", "ELEMENT_REGISTER 'Wet-room DOORWAY' (a door shared by two "
                             "wet rooms: one element, never billed twice, never 0)", "UP-QTY-STATUS-001"],
             "owner_manual_method": "one doorway transition per physical door from the opening inventory",
             "drawing_method": "the merged T-249 opening inventory crosswalked to the candidate's door ids (T-303)"},
    P_POOL: {"module": "engine/source/arch_v3049.py (a printed pool protective layer with no line: its own line on the "
                       "protected concrete face, the unresolved upstand beside with its bound)",
             "policy": "POOL_LAYER_LINES_V1", "rule_id": "R-T309-1 (R-T310-1 d)",
             "owner_rules": ["Q-26 A (flat pool floor)", "ELEMENT_REGISTER 'Pool membrane and protection screed' "
                             "(its own family, function HELD S8.2)", "UP-QTY-STATUS-001"],
             "owner_manual_method": "each printed layer on the faces its hatch covers, measured on the protected face",
             "drawing_method": "the merged T-309 face ledger on the verified pool shell (Checker own re-read of the "
                               "detail by handle: layer order and faces AGREE)"},
}
WAITING = dict(A3048.WAITING)
WAITING.update({
    "T310_DOORWAY_SEGMENTS": "doorway upturn segments (door width x 0.20) HELD in every wet room while the project's "
                             "doorway detail (coverage inside the floor piece or a separate return) is not printed "
                             "(UP-WP-003 1.1.0): beside the upturn line, never billed twice, never 0",
    "T310_TRANSITION_DETAIL": "every doorway transition m2 line stays bounded or HELD: the transition detail is not "
                              "printed (T-303); the per-door keying is done, the figure is not",
    "T310_PANTRY_DOOR": "the pantry's own door (D120 1.00): threshold, transition and transition number MISSING since "
                        "T-303 (insert not bound to a candidate door id): a separate binding piece",
    "T310_PANTRY_OPEN_SIDE": "the pantry's open side to the dining (4.49 m): termination line MISSING (T-303), floor "
                             "drain count not tabled: separate pieces",
    "T310_THRESHOLDS": "GF master bath and 1F west lower bath threshold lines (closure-derived, T-303 finding 2) "
                       "UNRESOLVED: unchanged",
    "T310_POOL_UPSTAND": "pool membrane / screed on the 0.15 upstand faces above the deck (C9): HELD beside the pool "
                         "lines with their bound 0 .. 1.349668 m2 / 0 .. 0.068072 m3",
    "T310_POOL_FUNCTION": "pool membrane function (waterproofing or thermal insulation, S8.2) and product: HELD by name",
})


# ================================================================================================ inputs
def _need(s, keys, where):
    for k in keys:
        if s.get(k) in (None, "", [], {}):
            raise InputsError(f"{where}: {k} missing")


def _num(x, where, pos=False, top=MAX_Q):
    if not isinstance(x, (int, float)) or isinstance(x, bool) or x != x:
        raise InputsError(f"{where}: {x!r} is not a number")
    if x < 0 or (pos and x == 0):
        raise InputsError(f"{where}: {x!r} is {'not positive' if pos else 'negative'} (held is never 0)")
    if x > top:
        raise InputsError(f"{where}: {x} is not a quantity in m / m2 / m3 (mm / cm refused)")
    return float(x)


def _lid(x, where):
    if not LINE_ID_RE.match(str(x)):
        raise InputsError(f"{where}: {x!r} is not a BOQ line id")
    return x


def _door(x, where):
    if not DOOR_RE.match(str(x)):
        raise InputsError(f"{where}: {x!r} is not a physical door id of the opening inventory")
    return x


def _entry(x, srcs):
    act = x.get("action")
    w = f"{act} {x.get('line_id') or x.get('door_id') or x.get('item_code')}"
    if act not in ACTIONS:
        raise InputsError(f"{w}: action is not one of {ACTIONS}")
    _need(x, ("basis", "source_tasks"), w)
    if any(t not in srcs for t in x["source_tasks"]):
        raise InputsError(f"{w}: no merged source named")
    out = dict(x, _piece=PIECE_OF[act])
    if act == "REVALUE_UPTURN":
        _need(x, ("line_id", "before", "boundary_lm", "door_widths_m", "evidence_status"), w)
        _lid(x["line_id"], w)
        b = _num(x["boundary_lm"], f"{w} boundary", pos=True)
        ws = [_num(v, f"{w} door width", pos=True, top=5.0) for v in x["door_widths_m"]]
        if any(o.get("kind") == "WINDOW" and _num(o.get("sill_m"), f"{w} window sill", top=10.0) <= 0.20
               for o in x.get("openings_not_deducted") or ()):
            raise InputsError(f"{w}: a window whose sill is at or below the 0.20 m upturn cuts the run (deduct it)")
        run = WP3.upturn_run(boundary_lm=b, door_widths_m=ws, room=w)
        if run["state"] != WP3.MEASURED:
            raise InputsError(f"{w}: the policy holds the run ({run.get('reason')})")
        if x.get("value") is not None and abs(_num(x["value"], f"{w} value") - run["run_m2"]) > TOL:
            raise InputsError(f"{w}: stated {x['value']} is not the policy run {run['run_m2']}")
        out.update(_value=run["run_m2"], _run=run, _before=_num(x["before"], f"{w} before"))
    elif act == "REVALUE_FLOOR":
        _need(x, ("line_id", "before", "gross_m2", "deductions", "evidence_status"), w)
        _lid(x["line_id"], w)
        g = _num(x["gross_m2"], f"{w} gross", pos=True)
        ded = 0.0
        for d in x["deductions"]:
            _need(d, ("what", "m2", "evidence"), f"{w} deduction")
            ded += _num(d["m2"], f"{w} deduction {d['what']}", pos=True)
        v = _r(g - ded)
        if x.get("value") is not None and abs(_num(x["value"], f"{w} value") - v) > TOL:
            raise InputsError(f"{w}: stated {x['value']} is not gross - deductions {v}")
        out.update(_value=v, _before=_num(x["before"], f"{w} before"))
    elif act == "NOT_APPLICABLE":
        _need(x, ("line_id", "item_code", "evidence"), w)
        _lid(x["line_id"], w)
        if x["item_code"] not in NA_CODES:
            raise InputsError(f"{w}: {x['item_code']} is not a code this version may set not applicable")
        if x.get("value") not in (None, ""):
            raise InputsError(f"{w}: a not-applicable line carries no figure")
        if x["item_code"] == TRANS:
            _need(x, ("door_id", "carried_by"), w)
            _door(x["door_id"], w)
            _lid(x["carried_by"], f"{w} carried_by")
    elif act == "KEY_DOOR":
        _need(x, ("line_id", "door_id"), w)
        _lid(x["line_id"], w)
        _door(x["door_id"], w)
    elif act == "ADD_HELD_DOOR":
        _need(x, ("door_id", "rooms", "floor", "template_line", "held_items"), w)
        _door(x["door_id"], w)
        _lid(x["template_line"], f"{w} template")
        if x.get("value") not in (None, "") or x.get("low") not in (None, ""):
            raise InputsError(f"{w}: HELD_WITH_VALUE: a held door line carries no figure")
    else:
        _need(x, ("item_code", "element_id", "value", "evidence_status", "template_code", "held_part"), w)
        if x["item_code"] not in POOL_UNIT:
            raise InputsError(f"{w}: {x['item_code']} is not a pool layer code")
        if x.get("unit") not in (None, POOL_UNIT[x["item_code"]]):
            raise InputsError(f"{w}: unit {x.get('unit')} (a pool layer {POOL_UNIT[x['item_code']]})")
        hp = x["held_part"]
        _need(hp, ("what", "low", "high", "cause"), f"{w} held part")
        lo, hi = _num(hp["low"], f"{w} held low"), _num(hp["high"], f"{w} held high")
        if lo > hi:
            raise InputsError(f"{w}: held low {lo} > high {hi}")
        if any(f.get("face") in ("WATER_FLOOR", "WATER_WALLS", "WALL_TOP") for f in x.get("faces") or ()):
            raise InputsError(f"{w}: a pool protective layer on a water-side / wall-top face (no hatch there)")
        out.update(_value=_num(x["value"], f"{w} value", pos=True), _lo=lo, _hi=hi)
    if act in ("REVALUE_UPTURN", "REVALUE_FLOOR", "ADD_POOL_LAYER") and x["evidence_status"] != EVIDENCE_STATUS:
        raise InputsError(f"{w}: evidence status {x['evidence_status']!r} (an integration input is "
                          f"{EVIDENCE_STATUS}; VERIFIED is the Checker's word)")
    return out


def load_inputs(doc, project_id=None):
    """URBAN_V3049_INPUTS_V1 -> the validated doc.
    {"schema", "project_id", "sources": [{"task", "file", "sha256", "merge_commit", "checker_run"}],
     "entries": [{"action" (ACTIONS), "basis", "source_tasks", ...per action: REVALUE_UPTURN line_id, before,
                  boundary_lm, door_widths_m, openings_not_deducted [{kind, id, sill_m}], value, evidence_status;
                  REVALUE_FLOOR line_id, before, gross_m2, deductions [{what, m2, evidence}], value, residual_risk;
                  NOT_APPLICABLE line_id, item_code, evidence (+ door_id, carried_by for a transition);
                  KEY_DOOR line_id, door_id; ADD_HELD_DOOR door_id, rooms, floor, template_line, held_items;
                  ADD_POOL_LAYER item_code, element_id, value, evidence_status, template_code, held_part {what, low,
                  high, cause}, faces, function_held}]}"""
    if not doc:
        return None
    if doc.get("schema") != INPUTS_SCHEMA:
        raise InputsError(f"project inputs: schema must be {INPUTS_SCHEMA}")
    if project_id and doc.get("project_id") not in (None, project_id):
        raise InputsError(f"project inputs are for {doc.get('project_id')!r}, the run is {project_id!r}")
    srcs = A3043._sources(doc)
    ents = [_entry(x, srcs) for x in doc.get("entries") or ()]
    if not ents:
        raise InputsError("no entry in the inputs")
    seen, doors = set(), {}
    for e in ents:
        k = e.get("line_id") or (e["action"], e.get("door_id") or e.get("item_code"))
        if k in seen:
            raise InputsError(f"{e['action']} {k}: named twice (one line, one change)")
        seen.add(k)
        if e["action"] in ("KEY_DOOR", "ADD_HELD_DOOR"):
            if e["door_id"] in doors:
                raise InputsError(f"door {e['door_id']}: keyed to two transition lines (one per physical door)")
            doors[e["door_id"]] = e
    for e in ents:
        if e["action"] == "NOT_APPLICABLE" and e["item_code"] == TRANS:
            car = doors.get(e["door_id"])
            if car is None or car.get("line_id") != e["carried_by"]:
                raise InputsError(f"{e['line_id']}: door {e['door_id']} is not keyed to the carrying line "
                                  f"{e['carried_by']}")
    return dict(doc, _sources=srcs, _entries=ents)


# ================================================================================================ lines
def _rec(piece, srcs, **kw):
    return dict({"piece": piece, "policy": PIECES[piece]["policy"], "tasks": [s["task"] for s in srcs],
                 "ledgers": [s["file"] for s in srcs], "ledger_sha256": [s["sha256"] for s in srcs],
                 "merge_commits": [s["merge_commit"] for s in srcs], "checker_runs": [s["checker_run"] for s in srcs],
                 "rule_id": RULE_ID, "rule_version": RULE_VERSION, "release_status": "NOT RELEASED"}, **kw)


def _fin(ln):
    from engine.source import boq_line as BL
    ln["project"] = copy.deepcopy(ln["project"])
    return BL.validate(ln)


def _inp(new):
    new["calculation"] = dict(new["calculation"])
    inp = new["calculation"]["inputs"] = dict(new["calculation"].get("inputs") or {})
    return inp


def _was(ln):
    return {"state": ln["evidence_state"], "measured_net": ln.get("measured_net"),
            "bounded_range": ln.get("bounded_range"), "gross": ln.get("gross")}


def _revalued(ln, e, srcs):
    new = copy.deepcopy(ln)
    piece = e["_piece"]
    new["evidence_state"] = VALUED_STATE
    new["measured_net"] = _r(e["_value"])
    new["bounded_range"] = None
    new["rfi"] = None
    if e["action"] == "REVALUE_UPTURN":
        run = e["_run"]
        segs = run["segments"]
        held = "; ".join(f"doorway segment {i + 1} HELD ({s['reason']}, {_fmt(s['if_billed_m2'])} m2 if billed)"
                         for i, s in enumerate(segs))
        nd = "; ".join(f"{o.get('kind')} {o.get('id')} sill {_fmt(o.get('sill_m'))} m above the upturn, not deducted"
                       for o in e.get("openings_not_deducted") or ())
        formula = (f"{METHOD}: wet-room upturn run (boundary incl. door crossings {_fmt(e['boundary_lm'])} lm - "
                   f"doorway segments {_fmt(sum(e['door_widths_m']))} lm) x {_fmt(run['upturn_m'])} m = "
                   f"{_fmt(run['run_m2'])} m2 ({run['upturn_authority']}; {WP3.POLICY_ID})"
                   + (f" | {nd}" if nd else "") + (f" | beside, never in it: {held}" if held else ""))
        new["gross"] = None
        new["deductions"] = []
        rec = _rec(piece, srcs, action=e["action"], was=_was(ln), value_m2=run["run_m2"], run_lm=run["run_lm"],
                   boundary_lm=e["boundary_lm"], door_widths_m=list(e["door_widths_m"]),
                   openings_not_deducted=e.get("openings_not_deducted") or [], doorway_segments=segs,
                   evidence_status=e["evidence_status"], basis=e["basis"], policy_module=WP3.POLICY_ID)
    else:
        ded = "; ".join(f"{d['what']} {_fmt(d['m2'])} m2 ({d['evidence']})" for d in e["deductions"])
        formula = (f"{METHOD}: wet floor = printed box {_fmt(e['gross_m2'])} m2 - {ded} = {_fmt(e['_value'])} m2"
                   + (f" | residual risk beside: {e['residual_risk']}" if e.get("residual_risk") else ""))
        new["gross"] = _r(e["gross_m2"])
        new["deductions"] = [{"what": d["what"], "m2": _r(d["m2"]), "evidence": d["evidence"]}
                             for d in e["deductions"]]
        rec = _rec(piece, srcs, action=e["action"], was=_was(ln), value_m2=e["_value"], gross_m2=e["gross_m2"],
                   deductions=e["deductions"], residual_risk=e.get("residual_risk"),
                   evidence_status=e["evidence_status"], basis=e["basis"])
    new["calculation"] = dict(new["calculation"], formula=formula[:1500])
    inp = _inp(new)
    inp[REC_KEY] = rec
    inp["evidence_status"] = e["evidence_status"]
    new["notes"] = (f"{ln.get('notes') or ''} | {METHOD}: {_fmt(e['_before'])} -> {_fmt(e['_value'])} "
                    f"{ln['unit']} ({e['evidence_status']}); NOT RELEASED")[:2000]
    return _fin(new)


def _not_applicable(ln, e, srcs):
    new = copy.deepcopy(ln)
    new["evidence_state"] = NA_STATE
    new["measured_net"] = None
    new["bounded_range"] = None
    new["gross"] = None
    new["rfi"] = None
    why = e["evidence"] + (f" | door {e['door_id']} is carried by {e['carried_by']} (one transition per physical "
                           f"door, Q-35 C)" if e["item_code"] == TRANS else "")
    new["calculation"] = dict(new["calculation"], formula=f"{METHOD}: NOT APPLICABLE (no figure): {why}"[:1500])
    inp = _inp(new)
    inp[REC_KEY] = _rec(P_NA, srcs, action="NOT_APPLICABLE", was=_was(ln), evidence=e["evidence"],
                        door_id=e.get("door_id"), carried_by=e.get("carried_by"), basis=e["basis"])
    new["notes"] = (f"{ln.get('notes') or ''} | {METHOD}: NOT_APPLICABLE_WITH_EVIDENCE: {why}; NOT RELEASED")[:2000]
    return _fin(new)


def _keyed(ln, e, srcs):
    new = copy.deepcopy(ln)
    inp = _inp(new)
    inp[REC_KEY] = _rec(P_DOOR, srcs, action="KEY_DOOR", door_id=e["door_id"], basis=e["basis"],
                        quantity="unchanged (record only)")
    new["notes"] = (f"{ln.get('notes') or ''} | {METHOD}: physical door {e['door_id']} (one transition per door)")[:2000]
    return _fin(new)


def _added_door(tpl, e, srcs):
    from engine.source import boq_line as BL
    eid = f"WP-T310:{e['door_id']}:TRANSITION"
    why = f"door {e['door_id']} ({' / '.join(e['rooms'])}): {e['held_items']}"
    rec = _rec(P_DOOR, srcs, action="ADD_HELD_DOOR", door_id=e["door_id"], rooms=list(e["rooms"]),
               held_items=e["held_items"], basis=e["basis"], evidence_status="HELD")
    ln = BL.make_line(
        project_id=tpl["project"]["project_id"], revision_set_sha256=tpl["project"]["revision_set_sha256"],
        item_code=TRANS, unit=tpl["unit"], evidence_state=HELD_STATE, measured_net=None, gross=None,
        element_id=eid, floor=e["floor"], room_id=e["rooms"][0],
        physical_element=f"doorway transition of door {e['door_id']}",
        formula=f"{METHOD}: HELD (no figure) doorway transition of physical door {e['door_id']}: {e['basis']}"[:1500],
        inputs={REC_KEY: rec, "evidence_status": "HELD"}, documents=copy.deepcopy(tpl["source"]["documents"]),
        geometry_source=tpl["source"]["geometry_source"], geometry_confidence=tpl["source"]["geometry_confidence"],
        rule_id=RULE_ID, rule_version=RULE_VERSION, material_state=tpl.get("material_state") or "SOURCE",
        rfi={"question": why[:900], "unlocks": eid},
        notes=f"{METHOD}: transition line added HELD BLANK for a door with none (one per physical door); NOT RELEASED",
        item_en=tpl["item_en"], item_ar=tpl["item_ar"], trade=tpl["trade"], subtrade=tpl.get("subtrade"))
    return _fin(ln)


def _added_pool(tpl, e, srcs):
    from engine.source import boq_line as BL
    code = e["item_code"]
    en, ar, word = POOL_TEXT[code]
    unit = POOL_UNIT[code]
    hp = e["held_part"]
    beside = (f"{hp['what']} HELD beside, never in it: bound {_fmt(e['_lo'])} .. {_fmt(e['_hi'])} {unit} "
              f"({hp['cause']})")
    func = e.get("function_held") or ""
    formula = (f"{METHOD}: {word} {e['basis']} = {_fmt(e['_value'])} {unit} on the protected concrete face "
               f"({e['evidence_status']}) | {beside}" + (f" | {func}" if func else ""))[:1500]
    rec = _rec(P_POOL, srcs, action="ADD_POOL_LAYER", value=e["_value"], unit=unit, faces=e.get("faces") or [],
               held_part=dict(hp, low=e["_lo"], high=e["_hi"]), function_held=func or None,
               evidence_status=e["evidence_status"], basis=e["basis"])
    ln = BL.make_line(
        project_id=tpl["project"]["project_id"], revision_set_sha256=tpl["project"]["revision_set_sha256"],
        item_code=code, unit=unit, evidence_state=VALUED_STATE, measured_net=_r(e["_value"]), gross=None,
        element_id=e["element_id"], floor=e.get("floor") or tpl["location"].get("floor"),
        physical_element=word, formula=formula,
        inputs={REC_KEY: rec, "evidence_status": e["evidence_status"]},
        documents=copy.deepcopy(tpl["source"]["documents"]), geometry_source=tpl["source"]["geometry_source"],
        geometry_confidence=tpl["source"]["geometry_confidence"], rule_id=RULE_ID, rule_version=RULE_VERSION,
        material_state="SOURCE",
        notes=f"{METHOD}: printed pool layer with no line added ({e['evidence_status']}); {beside}; NOT RELEASED",
        item_en=en, item_ar=ar, trade=tpl["trade"], subtrade="B8-09")
    return _fin(ln)


# ================================================================================================ changes
def changes_for(doc, prev):
    """-> (changes, log). Each change: piece, action (CHANGE / ADD), before (a candidate line or None), after."""
    if not doc:
        return [], {"piece": "+".join(PIECES), "state": "NO_PROJECT_INPUT"}
    if any(((ln.get("calculation") or {}).get("inputs") or {}).get(REC_KEY) for ln in prev):
        raise InputsError("the candidate already carries V3.0.49 records (applied once)")
    by = {ln["line_id"]: ln for ln in prev}
    S = doc["_sources"]
    changes, seen = [], set(by)
    log = {"piece": "+".join(PIECES), "state": "RUN", "sources": doc["sources"], "by_action": {}, "lines_added": 0,
           "lines_changed": 0}

    def add(piece, action, after, before=None, **kw):
        if before is None:
            if after["line_id"] in seen:
                raise InputsError(f"{METHOD}: added line {after['location']['element_id']} repeats an id")
            seen.add(after["line_id"])
            log["lines_added"] += 1
        else:
            if before["line_id"] != after["line_id"]:
                raise ValueError(f"{METHOD}: a changed line keeps its id")
            log["lines_changed"] += 1
        log["by_action"][action] = log["by_action"].get(action, 0) + 1
        srcs = kw.pop("srcs")
        changes.append(A305._change(piece, "ADD" if before is None else "CHANGE", before, after, step=action,
                                    drawing_reference="; ".join(s["file"] for s in srcs),
                                    verification=A3043._ver(srcs), downstream=kw.pop("downstream", []),
                                    group=after["item_code"], **kw))

    def line(lid, code, w):
        ln = by.get(lid)
        if ln is None:
            raise InputsError(f"{w}: {lid} is not a candidate line (stale binding)")
        if ln["item_code"] != code:
            raise InputsError(f"{w}: {lid} is {ln['item_code']}, not {code} (stale binding)")
        return ln

    for e in doc["_entries"]:
        act = e["action"]
        w = f"{act} {e.get('line_id') or e.get('door_id') or e.get('item_code')}"
        srcs = [S[t] for t in e["source_tasks"]]
        if act in ("REVALUE_UPTURN", "REVALUE_FLOOR"):
            ln = line(e["line_id"], UPTURN if act == "REVALUE_UPTURN" else FLOOR, w)
            if ln.get("measured_net") is None or abs(ln["measured_net"] - e["_before"]) > TOL:
                raise InputsError(f"{w}: the candidate carries {ln.get('measured_net')}, not {e['_before']} "
                                  f"(stale binding)")
            new = _revalued(ln, e, srcs)
            add(e["_piece"], act, new, before=ln, srcs=srcs, evidence_status=e["evidence_status"],
                held=[{"what": f"{ln['item_code']} {ln['location'].get('room_id')}",
                       "why": "doorway segments beside (UP-WP-003 1.1.0)" if act == "REVALUE_UPTURN" else
                       str(e.get("residual_risk") or "")[:300], "range": None, "scenario": None}],
                downstream=[f"{ln['item_code']}: {_fmt(e['_before'])} -> {_fmt(e['_value'])} {ln['unit']}"])
        elif act == "NOT_APPLICABLE":
            ln = line(e["line_id"], e["item_code"], w)
            if ln["evidence_state"] == NA_STATE:
                raise InputsError(f"{w}: already not applicable (applied once)")
            if e["item_code"] == TRANS:
                line(e["carried_by"], TRANS, f"{w} carried_by")
            add(P_NA, act, _not_applicable(ln, e, srcs), before=ln, srcs=srcs, evidence_status="NOT_APPLICABLE",
                held=[], downstream=[f"{ln['item_code']}: {ln['evidence_state']} -> {NA_STATE} (no figure)"])
        elif act == "KEY_DOOR":
            ln = line(e["line_id"], TRANS, w)
            add(P_DOOR, act, _keyed(ln, e, srcs), before=ln, srcs=srcs, evidence_status="RECORD_ONLY", held=[],
                downstream=[f"{TRANS}: keyed to door {e['door_id']} (quantity unchanged)"])
        elif act == "ADD_HELD_DOOR":
            tpl = line(e["template_line"], TRANS, f"{w} template")
            add(P_DOOR, act, _added_door(tpl, e, srcs), srcs=srcs, evidence_status="HELD",
                held=[{"what": f"{TRANS} {e['door_id']}", "why": str(e["held_items"])[:300], "range": None,
                       "scenario": None}],
                downstream=[f"coverage: door {e['door_id']} now has its own transition line (held)"])
        else:
            tpls = sorted((ln for ln in prev if ln["item_code"] == e["template_code"]), key=lambda ln: ln["line_id"])
            if not tpls:
                raise InputsError(f"{w}: no {e['template_code']} line in the candidate to share documents / trade")
            tpl = tpls[0]
            if any(ln["item_code"] == e["item_code"] for ln in prev):
                raise InputsError(f"{w}: the candidate already has a {e['item_code']} line (re-value it, do not add)")
            add(P_POOL, act, _added_pool(tpl, e, srcs), srcs=srcs, evidence_status=e["evidence_status"],
                held=[{"what": e["held_part"]["what"], "why": e["held_part"]["cause"][:300],
                       "range": f"{_fmt(e['_lo'])} .. {_fmt(e['_hi'])}", "scenario": None}],
                downstream=[f"coverage: {e['item_code']} now has its line"])
    log["by_action"] = dict(sorted(log["by_action"].items()))
    return changes, log


# ================================================================================================ checks
def check_wet_area_wp(lines, before=None):
    """R-T310-1 on the integrated lines (a no-op on lines without a V3.0.49 record): (a) a re-valued line carries its
    record's value in SOURCE_DERIVED and keeps id / code / unit / location; (b) the keyed transition lines carry each
    door once and every NA transition names a keyed carrying line; (c) NA lines carry no figure; (d) pool layer lines
    carry their value and their held part beside; a V3.0.49 record on another code is refused. -> summary."""
    out = {"revalued": 0, "not_applicable": 0, "keyed_doors": 0, "added_held_doors": 0, "pool_lines": 0,
           "doors": {}}
    b4 = {ln["line_id"]: ln for ln in before or ()}
    ids = {ln["line_id"]: ln for ln in lines}
    na_trans = []
    for ln in lines:
        rec = ((ln.get("calculation") or {}).get("inputs") or {}).get(REC_KEY)
        if not rec:
            continue
        if ln["item_code"] not in WP_CODES:
            raise ValueError(f"{METHOD}: a V3.0.49 record on {ln['item_code']} {ln['line_id']}")
        act = rec.get("action")
        blank = ln.get("measured_net") is None and ln.get("bounded_range") is None
        if act in ("REVALUE_UPTURN", "REVALUE_FLOOR"):
            if ln["evidence_state"] != VALUED_STATE or abs((ln.get("measured_net") or -1) - rec["value_m2"]) > 1e-9:
                raise ValueError(f"{METHOD}: re-valued line {ln['line_id']} does not carry its record's value")
            o = b4.get(ln["line_id"])
            if o is not None:
                for k in ("item_code", "unit", "location", "rule"):
                    if o.get(k) != ln.get(k):
                        raise ValueError(f"{METHOD}: re-valued line {ln['line_id']} moved {k}")
            out["revalued"] += 1
        elif act == "NOT_APPLICABLE":
            if ln["evidence_state"] != NA_STATE or not blank or ln.get("gross") is not None:
                raise ValueError(f"{METHOD}: not-applicable line {ln['line_id']} carries a figure")
            if ln["item_code"] == TRANS:
                na_trans.append((ln, rec))
            out["not_applicable"] += 1
        elif act in ("KEY_DOOR", "ADD_HELD_DOOR"):
            d = rec["door_id"]
            if d in out["doors"]:
                raise ValueError(f"{METHOD}: door {d} carried by two transition lines")
            out["doors"][d] = ln["line_id"]
            if act == "ADD_HELD_DOOR":
                if ln["evidence_state"] != HELD_STATE or not blank or ln.get("gross") is not None:
                    raise ValueError(f"{METHOD}: added door line {ln['line_id']} is not HELD BLANK (never 0)")
                out["added_held_doors"] += 1
            else:
                o = b4.get(ln["line_id"])
                if o is not None and A30._qty(o) != A30._qty(ln):
                    raise ValueError(f"{METHOD}: keyed line {ln['line_id']} moved its quantity")
                out["keyed_doors"] += 1
        elif act == "ADD_POOL_LAYER":
            hp = rec.get("held_part") or {}
            if ln["evidence_state"] != VALUED_STATE or abs((ln.get("measured_net") or -1) - rec["value"]) > 1e-9 \
                    or hp.get("low") is None or hp.get("high") is None:
                raise ValueError(f"{METHOD}: pool layer line {ln['line_id']} lacks its value or its held part")
            out["pool_lines"] += 1
        else:
            raise ValueError(f"{METHOD}: action {act} on {ln['line_id']}")
    for ln, rec in na_trans:
        car = ids.get(rec.get("carried_by"))
        if car is None or out["doors"].get(rec.get("door_id")) != car["line_id"]:
            raise ValueError(f"{METHOD}: NA transition {ln['line_id']} names no keyed carrying line for its door")
    out["doors"] = dict(sorted(out["doors"].items()))
    return out


# ================================================================================================ integrate / write
def integrate(prev, changes, for_lead=()):
    """-> (V3.0.49 lines, identity). Changed lines replace their candidate line in place; added lines follow; every
    other candidate line is byte-identical (asserted)."""
    sid = {ln["line_id"]: i for i, ln in enumerate(prev)}
    out = list(prev)
    adds, repl = [], set()
    for c in changes:
        a = c["after"]
        if a["item_code"] not in WP_CODES:
            raise ValueError(f"{METHOD}: {a['item_code']} is not a code this version may change or add")
        if c["action"] == "ADD":
            if a["line_id"] in sid:
                raise ValueError(f"{METHOD}: an added line repeats a candidate id")
            adds.append(a)
        elif c["action"] == "CHANGE":
            i = sid.get(a["line_id"])
            if i is None or a["line_id"] in repl:
                raise ValueError(f"{METHOD}: a changed line is not a candidate line or changes twice")
            out[i] = a
            repl.add(a["line_id"])
        else:
            raise ValueError(f"{METHOD}: action {c['action']}")
    out = out + adds
    if len({ln["line_id"] for ln in out}) != len(out):
        raise ValueError(f"{METHOD}: a BOQ line id appears twice")
    guards = A3031._family_guards(out, for_lead)
    ident = {"base_lines": len(prev), "v3_0_49_lines": len(out), "v3_0_49_rows": len(changes),
             "replaced": len(repl), "added": len(adds), "guards": guards,
             "roof_buildup": A3031.check_roof_layers(out), "ceilings": A3032.check_ceilings(out),
             "corrections": A3033.check_corrections(out), "tile_zones": A3034.check_zones(out),
             "fence": A3035.check_boundary(out), "lists": A3036.check_lists(out), "beds": A3038.check_beds(out),
             "lift": A3038.check_lift(out), "landing": A3038.check_landing(out), "flights": A3039.check_flights(out),
             "gb_runs": A3040.check_runs(out), "pieces": A3041.check_pieces(out), "slab": A3042.check_slab(out),
             "earthworks": A3048.check_earthworks(out), "skirting": A3044.check_skirting(out),
             "blinding": A3045.check_blinding(out), "tie_masonry": A3046.check_tie_masonry(out),
             "stair_rooms": A3047.check_stair_rooms(out), "wet_area_wp": check_wet_area_wp(out, prev)}
    pids = {(ln["project"]["project_id"], ln["project"]["revision_set_sha256"]) for ln in out}
    if len(pids) != 1:
        raise ValueError(f"{METHOD}: {len(pids)} project identities in the lines")
    outside = [ln for ln in prev if ln["line_id"] not in repl]
    bad = [a["line_id"] for a in outside if A30.line_sha(a) != A30.line_sha(out[sid[a["line_id"]]])]
    if bad:
        raise ValueError(f"{METHOD}: {len(bad)} candidate line(s) differ outside the named changes")
    ident.update(outside_rows=len(outside), outside_rows_identical_to_base=len(outside),
                 outside_rows_sha256=hashlib.sha256("".join(A30.line_sha(x) for x in outside).encode()).hexdigest())
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
        rows.append({"version": METHOD, "piece": c["piece"], "action": c.get("step"), "change": c["action"],
                     "line_id": ref["line_id"], "item_code": ref["item_code"], "floor": loc.get("floor"),
                     "room_id": loc.get("room_id"), "element_id": loc.get("element_id"), "unit": ref["unit"],
                     "before_released_v2_9": b29, "before_base": A30._qty(c.get("before")),
                     "after_v3_0_49": A30._qty(ref), "evidence_status": c.get("evidence_status"),
                     "still_held": c.get("held"), "release_status": "NOT RELEASED",
                     "owner_manual_method": PIECES[c["piece"]]["owner_manual_method"],
                     "drawing_derived_method": PIECES[c["piece"]]["drawing_method"],
                     "record": rec, "verification": c.get("verification") or {}, "rollback": ROLLBACK})
    return rows


LEDGER_CSV = ("version", "piece", "action", "change", "line_id", "item_code", "floor", "room_id", "element_id", "unit",
              "v2_9", "base", "v3_0_49", "evidence_status", "still_held", "verification")
DIFF_CSV = ("line_id", "item_code", "floor", "element_id", "unit", "vs_base", "vs_released_v2_9", "v2_9", "base",
            "v3_0_49")


def ledger_csv(rows):
    def q(x):
        return A302._q(x) if x and (x.get("value") is not None or x.get("low") is not None or x.get("state")) else ""

    def h(r):
        return "; ".join(f"{x['what']} {x.get('range')}" for x in (r.get("still_held") or ()))[:300]
    return A305._csv([{"version": r["version"], "piece": r["piece"], "action": r["action"], "change": r["change"],
                       "line_id": r["line_id"], "item_code": r["item_code"], "floor": r.get("floor") or "",
                       "room_id": r.get("room_id") or "", "element_id": r.get("element_id") or "", "unit": r["unit"],
                       "v2_9": q(r.get("before_released_v2_9")), "base": q(r.get("before_base")),
                       "v3_0_49": q(r.get("after_v3_0_49")), "evidence_status": r["evidence_status"],
                       "still_held": h(r),
                       "verification": f"{r['verification'].get('task')} "
                                       f"{' '.join(x[:8] for x in r['verification'].get('merge_commits') or ())}"}
                      for r in rows], LEDGER_CSV)


def diff_rows(prev, new, released_lines=None):
    b = {ln["line_id"]: ln for ln in prev}
    rel = {A30._key(ln): ln for ln in released_lines or ()}
    out = []
    for ln in new:
        o = b.get(ln["line_id"])
        vs = "ADDED" if o is None else ("SAME" if A30.line_sha(o) == A30.line_sha(ln) else "CHANGED")
        r = rel.get(A30._key(ln)) if released_lines is not None else None
        vs29 = None if released_lines is None else ("NOT_IN_RELEASED" if r is None else
                                                    ("SAME_QUANTITY" if A30._qty(r) == A30._qty(ln) else
                                                     "QUANTITY_DIFFERS"))
        out.append({"line_id": ln["line_id"], "item_code": ln["item_code"], "floor": ln["location"].get("floor"),
                    "element_id": ln["location"].get("element_id"), "unit": ln["unit"], "vs_base": vs,
                    "vs_released_v2_9": vs29, "v2_9": A302._q(A30._qty(r)) if r else "",
                    "base": A302._q(A30._qty(o)) if o else "", "v3_0_49": A302._q(A30._qty(ln))})
    return out


def write(out, prev, changes, log, released_lines=None, for_lead=()):
    """the V3_0_49_* files beside the base candidate's files. -> (file names, identity, ledger)."""
    from pathlib import Path
    from engine.source import boq_line as BL
    out = Path(out)
    new, ident = integrate(prev, changes, for_lead)
    rows = ledger_rows(changes, released_lines)
    diff = diff_rows(prev, new, released_lines)
    named = {c["after"]["line_id"] for c in changes}
    stray = [d["line_id"] for d in diff if d["vs_base"] in ("CHANGED", "ADDED") and d["line_id"] not in named]
    if stray:
        raise ValueError(f"{METHOD}: {len(stray)} line(s) changed outside the named changes")
    dsum = {}
    for d in diff:
        dsum.setdefault("vs_base", {}).setdefault(d["vs_base"], 0)
        dsum["vs_base"][d["vs_base"]] += 1
        if d["vs_released_v2_9"] is not None:
            dsum.setdefault("vs_released_v2_9", {}).setdefault(d["vs_released_v2_9"], 0)
            dsum["vs_released_v2_9"][d["vs_released_v2_9"]] += 1
    ident = dict(ident, diff=dsum)
    t0, t1 = A304.code_totals(prev), A304.code_totals(new)
    moved = {k: {"base": t0.get(k), "v3_0_49": t1.get(k)} for k in sorted(set(t0) | set(t1)) if t0.get(k) != t1.get(k)}
    for k in moved:
        if k.split("|")[0] not in WP_CODES:
            raise ValueError(f"{METHOD}: totals moved outside this version's codes: {k}")
    led = {"schema": LEDGER_SCHEMA, "method": METHOD, "extends": EXTENDS, "candidate": CANDIDATE,
           "base": A30.BASE_METHOD, "released": A30.RELEASED_METHOD, "released_default": False, "rows": rows,
           "waiting_pieces": WAITING, "integration_package": True}
    run = {"method": METHOD, "policy": POLICY_ID, "extends": EXTENDS, "candidate": CANDIDATE,
           "base_method": A30.BASE_METHOD, "released_method": A30.RELEASED_METHOD, "released_default": False,
           "rollback": ROLLBACK, "identity": ident, "pieces": PIECES, "piece_logs": [log],
           "totals_moved_by_code": moved, "waiting_pieces": WAITING}
    files = {"V3_0_49_BOQ_LINES.json": BL.dumps(new),
             "V3_0_49_BOQ_LINES.csv": A30._lines_csv(new),
             "V3_0_49_INTEGRATION_LEDGER.json": A30._j(led),
             "V3_0_49_INTEGRATION_LEDGER.csv": ledger_csv(rows),
             "V3_0_49_DIFF.csv": A305._csv(diff, DIFF_CSV),
             "V3_0_49_RUN.json": A30._j(run)}
    for name, text in files.items():
        (out / name).write_text(text, encoding="utf-8")
    return sorted(files), ident, led


def policy_record():
    return {"method": METHOD, "extends": EXTENDS, "pieces": sorted(PIECES), "inputs_schema": INPUTS_SCHEMA,
            "released_default": False, "rollback": ROLLBACK, "actions": list(ACTIONS)}


__all__ = ["METHOD", "PIECES", "WAITING", "DEFAULT_GUARD_CLASS", "INPUTS_SCHEMA", "WP_CODES", "load_inputs",
           "changes_for", "check_wet_area_wp", "integrate", "ledger_rows", "diff_rows", "write", "InputsError"]
