"""ARCH_TAKEOFF_V3.0.48 (T-350 r4, stream S): the SAME opt-in BOQ candidate as ARCH_TAKEOFF_V3.0 .. V3.0.47
(engine.source.arch_v30, arch_v301 .. arch_v3047), extended with the CALCULATED EARTHWORKS quantities of the
Checker-merged T-350 r2 piece (merge 42a99508) and the T-484 displacement re-measure (merge 12395ea4) in ONE step:

  EW_VALUE   a HELD BLANK earthworks zone line of V3.0.43 whose quantity the merged pieces calculate gets it: one figure
             (PROVISIONAL for a scenario-level ESTIMATED basis, SOURCE_DERIVED for a DRAWING-CONFIRMED one) or one
             admissible range (BOUNDED_EXPOSURE, both ends from the merged ledgers). The line keeps its id, its V3.0.43
             zone record and its rule; the new record carries the evidence status of WORKFLOW_CONTROLS s.5, the
             sensitivity, the corrected printed-minimum bound and every still-held item by name, beside, never in the
             quantity.
  EW_ADD     a zone the excavation family has and the backfill family lacks (a coverage gap) gets its own HELD BLANK
             line (BLOCKED_RFI, never 0), the scenario figures beside.

R-T350-2 (every villa; integrates R-T350-1, R-T350R2 (EARTHWORKS_QTY_V1) and R-T484-1): (a) excavation = zone plan x
(existing ground - formation) at the governing level basis; a scenario basis is ESTIMATED (PROVISIONAL), a printed one
DRAWING-CONFIRMED (SOURCE_DERIVED), a basis with two admissible readings a RANGE (BOUNDED_EXPOSURE); (b) backfill of a
zone = its excavation - every displacement below the existing ground at its actual position, once: the range must
close excavation - displacement at both ends (asserted to TOL) and never exceed its excavation; (c) the parts of a
zone that are designer items (working space, beyond the plot line, a drawing conflict, an unprinted section) stay
HELD by name beside the line, never 0, never silently in or out; (d) a lift is a layer COUNT beside the backfill
(ceil(zone depth / OWNER-PROVISIONAL lift)), never a quantity; (e) disposal stays HELD until the dry-mass balance has
its densities (owner 2026-11-02 18:00 (3)); (f) a backfill zone with no line is added HELD BLANK; (g) nothing outside
the earthworks codes moves.

Nothing else moves: every V3.0.47 line not named by the inputs is byte-identical (asserted); totals move only in the
earthworks codes (asserted). Files: V3_0_48_BOQ_LINES.json / .csv, V3_0_48_INTEGRATION_LEDGER.json / .csv,
V3_0_48_DIFF.csv, V3_0_48_RUN.json. Nothing here names a project, a sheet, a layer or a coordinate.
"""

from __future__ import annotations

import copy
import hashlib
import math
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

DEFAULT_GUARD_CLASS = "TOOLING"          # T-212: re-books checker-merged ledgers; adds no default value
METHOD = "ARCH_TAKEOFF_V3.0.48"
EXTENDS = A3047.METHOD
CANDIDATE = A30.METHOD
POLICY_ID = "URBAN_BOQ_T350R4_ARCH_V3_0_48"
INPUTS_SCHEMA = "URBAN_V3048_INPUTS_V1"
LEDGER_SCHEMA = "URBAN_V3048_INTEGRATION_LEDGER_V1"
ROLLBACK = A30.ROLLBACK
InputsError = A3031.InputsError
_r = A3018._r
_fmt = A3030._fmt
RULE_ID, RULE_VERSION = "R-T350-2", "T-350 r4"
REC_KEY = "earthworks_v3048"
PRIOR_KEY = A3043.REC_KEY                # the V3.0.43 zone record every earthworks line carries
P_VALUE, P_ADD = "EW_VALUE", "EW_ADD"
EXC, BKF, DSP = A3043.EXC, A3043.BKF, A3043.DSP
EW_CODES = A3043.EW_CODES
FAMILY_CODE = A3043.FAMILY_CODE
HELD_STATE = A3043.HELD_STATE            # BLOCKED_RFI
RANGE_STATE = "BOUNDED_EXPOSURE"
# WORKFLOW_CONTROLS s.5 evidence status -> the line's evidence state (one map, never a guess)
STATE_FOR = {"ESTIMATED": "PROVISIONAL", "DRAWING-CONFIRMED": "SOURCE_DERIVED"}
RANGE_STATUSES = ("ESTIMATED", "DRAWING-CONFIRMED", "PARTIALLY VERIFIED", "HELD")
VALUED = ("PROVISIONAL", "SOURCE_DERIVED")
ACTIONS = ("VALUE", "RANGE", "ADD_HELD")
TOL = 0.0000015
MAX_M3 = 100000.0
LINE_ID_RE = A3043.LINE_ID_RE
FORMULA_END_RE = A3043.FORMULA_END_RE
PARTIAL_RE = re.compile(r"^PARTIALLY VERIFIED (\d+) / (\d+)$")

PIECES = {
    P_VALUE: {"module": "engine/source/arch_v3048.py (a HELD BLANK V3.0.43 earthworks zone line valued or ranged from "
                        "the merged calculated quantities; held parts by name beside)",
              "policy": "EW_VALUE_V1", "rule_id": "R-T350R2 (EARTHWORKS_QTY_V1), R-T484-1 (R-T350-2 a .. e, g)",
              "owner_rules": ["RFI RE-REVIEW 2026-11-02 S01 ESTIMATED (owner-accepted): footing underside at the "
                              "printed 1.50 m minimum, underlay + blinding under it; +-0.10 m sensitivity",
                              "owner 2026-11-02 18:00 (1) maximum 150 mm finished compacted lift, OWNER-PROVISIONAL",
                              "owner 2026-11-02 18:00 (3) acceptance density is not procurement density; (4) geometry "
                              "is always calculated", "Q-21 C", "OQ-13 (working space: designer / contractor item)",
                              "UP-QTY-STATUS-001 (held is blank or a range, never 0)",
                              "ELEMENT_REGISTER ruling FOUNDATION BACKFILL displacement (each buried element once, "
                              "at its actual position)"],
              "owner_manual_method": "excavation = plan of each pit / trench x depth from the existing ground to the "
                                     "formation (working space a separate item); backfill = excavation - the buried "
                                     "structure below the existing ground (blinding, underlay, footings, necks, strap "
                                     "ends, ground-beam solids); disposal = excavation - re-used fill, by dry mass",
              "drawing_method": "the merged T-350 r2 FILL table (neat pit union by DXF outline handle in the plot, "
                                "outside the pool envelope; Checker own re-measure 124.649020 m2 / 208.163863 m3 "
                                "AGREE) and the T-484 displacement re-measure (necks 29 by handle 5.154, strap ends "
                                "0.179618 VERIFIED; beam solids per piece; F10 + F union), Checker verdicts "
                                "2026-11-03 06:05 and 09:56"},
    P_ADD: {"module": "engine/source/arch_v3048.py (a backfill zone with no line added HELD BLANK, scenarios beside)",
            "policy": "EW_ADD_HELD_V1", "rule_id": "R-T350R2 coverage gap (R-T350-2 f)",
            "owner_rules": ["UP-QTY-STATUS-001", "Q-31 C (necks C10 / C held)"],
            "owner_manual_method": "every excavated zone is backfilled: one backfill line per excavation zone",
            "drawing_method": "the merged T-350 r2 FILL gap rows (PROPOSED_NEW_LINE_HELD) with the T-484 F10 + F union"},
}
WAITING = dict(A3047.WAITING)
WAITING.update({
    "T350R4_WORKING_SPACE": "working space round pits and trenches: not printed, no documented method (OQ-13 / RFI S1):"
                            " HELD by name on every excavation and backfill line, never 0",
    "T350R4_BEYOND_PLOT": "the parts of pit / trench / pool plans beyond the plot line (S06 / D-14): HELD by name",
    "T350R4_POOL_CONFLICT": "F-T350R2-2 CONFLICT: F8 / F4 / FN pit chains inside the pool envelope under the pool "
                            "formation 0.458211 m3: owned by neither line until the designer settles the pit-to-pool "
                            "interface; named on the pits excavation line",
    "T350R4_BEAM_SECTIONS": "D-33 / D-35 ground-beam sections (designer items): the width 8.650212 m3 of the pits "
                            "backfill range; C8 mark conflict 0.030 m3 (drawn 0.24 vs schedule 0.27 m2)",
    "T350R4_DISPOSAL": "B1-04 disposal: in-situ dry density, placement target density, suitable share, loose densities "
                       "and the Z2 draw all HELD (owner 18:00 (3)); the line stays HELD BLANK",
    "T350R4_LIFT_PIT": "Z1-PIT-FF lift raft and pit: pit depth 'as per lift manufacturer', not printed: HELD",
    "T350R4_LOWER_GB_ROW": "Z1-LOWER-GB-ROW: not required under S01 (2.45 m < 2.50 m), REQUIRED at +0.10 m (2.55 m): "
                           "the scenario flips it, the line stays HELD BLANK",
    "T350R4_TRENCHES": "the annex, court, strap, boundary, interior D-33 and ZERO trench zones and Z2: S01 does not "
                       "settle their open dimension: V3.0.43 lines unchanged",
})


# ================================================================================================ inputs
def _need(s, keys, where):
    for k in keys:
        if s.get(k) in (None, "", [], {}):
            raise InputsError(f"{where}: {k} missing")


def _num(x, where, pos=False):
    if not isinstance(x, (int, float)) or isinstance(x, bool) or x != x:
        raise InputsError(f"{where}: {x!r} is not a number")
    if x < 0 or (pos and x == 0):
        raise InputsError(f"{where}: {x!r} is {'not positive' if pos else 'negative'} (held is never 0)")
    if x > MAX_M3:
        raise InputsError(f"{where}: {x} is not a quantity in m3 (litres / mm3 refused)")
    return float(x)


def _status(st, where, ranged):
    if st in STATE_FOR and not ranged:
        return st
    if ranged and (st in RANGE_STATUSES or PARTIAL_RE.match(str(st))):
        m = PARTIAL_RE.match(str(st))
        if m and not (0 < int(m.group(1)) < int(m.group(2))):
            raise InputsError(f"{where}: {st} is not a partial count (0 < n < m)")
        return st
    raise InputsError(f"{where}: evidence status {st!r} is not admissible for a {'range' if ranged else 'value'} "
                      f"(VERIFIED is the Checker's word, never an integration input)")


def _components(x, where):
    comps = x.get("displacement") or {}
    _need(comps, ("verified_m3", "remeasured_low_m3", "remeasured_high_m3"), f"{where} displacement")
    v = _num(comps["verified_m3"], f"{where} verified displacement")
    lo = _num(comps["remeasured_low_m3"], f"{where} displacement low")
    hi = _num(comps["remeasured_high_m3"], f"{where} displacement high")
    if lo > hi:
        raise InputsError(f"{where}: displacement low {lo} > high {hi}")
    return {"verified": v, "low": lo, "high": hi}


def _entry(x, srcs, seen):
    w = f"{x.get('action')} {x.get('family')} {x.get('zone')}"
    _need(x, ("action", "family", "zone", "element_id", "evidence_status", "basis", "held_items", "source_tasks"), w)
    if x["action"] not in ACTIONS:
        raise InputsError(f"{w}: action {x['action']} is not one of {ACTIONS}")
    if x["family"] not in FAMILY_CODE:
        raise InputsError(f"{w}: family {x['family']} is not B1-02 / B1-03 / B1-04")
    if any(t not in srcs for t in x["source_tasks"]):
        raise InputsError(f"{w}: no merged source named")
    key = (x["family"], x["element_id"])
    if key in seen:
        raise InputsError(f"{w}: zone named twice (one zone, one line)")
    seen.add(key)
    code = FAMILY_CODE[x["family"]]
    if code == DSP and x["action"] != "ADD_HELD":
        raise InputsError(f"{w}: disposal is never valued without its densities (R-T350-2 e)")
    out = dict(x, _code=code, _value=None, _lo=None, _hi=None, _disp=None)
    if x["action"] == "VALUE":
        if x.get("low") not in (None, "") or x.get("high") not in (None, ""):
            raise InputsError(f"{w}: a valued zone carries no range (the sensitivity goes beside)")
        out["_value"] = _num(x.get("value"), f"{w} value", pos=True)
        out["_status"] = _status(x["evidence_status"], w, False)
    elif x["action"] == "RANGE":
        if x.get("value") not in (None, ""):
            raise InputsError(f"{w}: a ranged zone carries no single value")
        lo, hi = _num(x.get("low"), f"{w} low", pos=True), _num(x.get("high"), f"{w} high", pos=True)
        if lo > hi + TOL:
            raise InputsError(f"{w}: low {lo} > high {hi}")
        out.update(_lo=lo, _hi=hi, _status=_status(x["evidence_status"], w, True))
        if code == BKF:
            out["_disp"] = _components(x, w)
            _need(x, ("excavation_element_id",), w)
    else:
        if any(x.get(k) not in (None, "") for k in ("value", "low", "high")):
            raise InputsError(f"{w}: HELD_WITH_VALUE: an added held zone carries its figures beside, never in it")
        if x["evidence_status"] != "HELD":
            raise InputsError(f"{w}: an added zone is HELD")
        out["_status"] = "HELD"
    lay = x.get("layers")
    if lay is not None:
        if code != BKF:
            raise InputsError(f"{w}: a layer count belongs beside a backfill line")
        _need(lay, ("depth_m", "lift_m", "status"), f"{w} layers")
        d, l = _num(lay["depth_m"], f"{w} depth", pos=True), _num(lay["lift_m"], f"{w} lift", pos=True)
        if l > 0.15 + 1e-9:
            raise InputsError(f"{w}: lift {l} m exceeds the OWNER-PROVISIONAL 150 mm finished lift")
        n = math.ceil(round(d / l, 9))
        if lay.get("count") is not None and lay["count"] != n:
            raise InputsError(f"{w}: layer count {lay['count']} is not ceil({d} / {l}) = {n}")
        out["_layers"] = dict(lay, count=n)
    return out


def load_inputs(doc, project_id=None):
    """URBAN_V3048_INPUTS_V1 -> the validated doc.
    {"schema", "project_id", "sources": [{"task", "file", "sha256", "merge_commit", "checker_run"}],
     "zones": [{"action" (VALUE / RANGE / ADD_HELD), "family", "zone", "element_id" (the V3.0.43 zone element, or the
                new one for ADD_HELD), "evidence_status" (WORKFLOW_CONTROLS s.5), "value" | "low", "high", "basis",
                "sensitivity", "printed_minimum_bound", "held_items", "displacement" (backfill: verified_m3,
                remeasured_low_m3, remeasured_high_m3, residual), "excavation_element_id" (backfill), "layers"
                (depth_m, lift_m, status, count), "scenarios_beside", "source_tasks"}]}"""
    if not doc:
        return None
    if doc.get("schema") != INPUTS_SCHEMA:
        raise InputsError(f"project inputs: schema must be {INPUTS_SCHEMA}")
    if project_id and doc.get("project_id") not in (None, project_id):
        raise InputsError(f"project inputs are for {doc.get('project_id')!r}, the run is {project_id!r}")
    srcs = A3043._sources(doc)
    seen = set()
    zones = [_entry(x, srcs, seen) for x in doc.get("zones") or ()]
    if not zones:
        raise InputsError("no earthworks zone in the inputs")
    return dict(doc, _sources=srcs, _zones=zones)


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


def _beside(z):
    parts = []
    if z.get("sensitivity"):
        parts.append(f"sensitivity beside: {z['sensitivity']}")
    if z.get("printed_minimum_bound"):
        parts.append(f"printed-minimum bound beside: {z['printed_minimum_bound']}")
    if z.get("_layers"):
        L = z["_layers"]
        parts.append(f"{L['count']} layers at {_fmt(L['lift_m'])} m over {_fmt(L['depth_m'])} m ({L['status']})")
    if z.get("scenarios_beside"):
        parts.append(f"scenarios beside (never the quantity): {z['scenarios_beside']}")
    return "; ".join(parts)


def _valued(ln, z, srcs):
    new = copy.deepcopy(ln)
    word = A3043.ITEM_TEXT[z["_code"]][2]
    beside = _beside(z)
    if z["action"] == "VALUE":
        new["evidence_state"] = STATE_FOR[z["_status"]]
        new["measured_net"] = _r(z["_value"])
        new["bounded_range"] = None
        qty = f"{_fmt(z['_value'])} m3 ({z['_status']})"
    else:
        new["evidence_state"] = RANGE_STATE
        new["measured_net"] = None
        new["bounded_range"] = {"low": _r(z["_lo"]), "high": _r(z["_hi"]),
                                "basis": f"{z['basis']} ({RULE_ID})"[:300]}
        qty = f"range {_fmt(z['_lo'])} .. {_fmt(z['_hi'])} m3 ({z['_status']})"
    new["gross"] = None
    new["rfi"] = None if z["action"] == "VALUE" else {
        "question": f"{word} zone '{z['zone']}': {z['held_items']}"[:900], "unlocks": z["element_id"],
        "bound_beside": beside[:300]}
    formula = (f"{METHOD}: {word} zone '{A3043._plain(z['zone'])}' {qty}: {A3043._plain(z['basis'])} | held beside, "
               f"never in it: {A3043._plain(z['held_items'])}" + (f" | {A3043._plain(beside)}" if beside else ""))
    new["calculation"] = dict(new["calculation"], formula=formula[:1500])
    inp = new["calculation"]["inputs"] = dict(new["calculation"]["inputs"] or {})
    was = {"state": ln["evidence_state"], "measured_net": ln.get("measured_net"),
           "bounded_range": ln.get("bounded_range")}
    disp = None
    if z["_disp"]:
        d = z["_disp"]
        disp = {"verified_m3": d["verified"], "remeasured_low_m3": d["low"], "remeasured_high_m3": d["high"],
                "residual": z["displacement"].get("residual"), "excavation_line": z.get("_exc_line"),
                "excavation_m3": z.get("_exc_value")}
    inp[REC_KEY] = _rec(P_VALUE, srcs, action=z["action"], family=z["family"], zone=z["zone"], was=was,
                        value_m3=z["_value"], low_m3=z["_lo"], high_m3=z["_hi"], evidence_status=z["_status"],
                        basis=z["basis"], sensitivity=z.get("sensitivity"),
                        printed_minimum_bound=z.get("printed_minimum_bound"), held_items=z["held_items"],
                        displacement=disp, layers=z.get("_layers"), scenarios_beside=z.get("scenarios_beside"),
                        bulking="none (no answered rule; R-T347-5): in situ")
    inp["evidence_status"] = z["_status"]
    new["notes"] = (f"{ln.get('notes') or ''} | {METHOD}: {word} zone HELD BLANK -> {qty}; held parts by name beside; "
                    f"NOT RELEASED")[:2000]
    return _fin(new)


def _added(tpl, z, srcs):
    from engine.source import boq_line as BL
    code = z["_code"]
    en, ar, word = A3043.ITEM_TEXT[code]
    beside = _beside(z)
    formula = (f"{METHOD}: HELD (never a value) {word} zone '{A3043._plain(z['zone'])}': {A3043._plain(z['basis'])} | "
               f"held by: {A3043._plain(z['held_items'])}" + (f" | {A3043._plain(beside)}" if beside else ""))[:1500]
    if FORMULA_END_RE.search(formula):
        raise InputsError(f"zone {z['zone']}: the formula would conclude on a figure")
    rec = _rec(P_ADD, srcs, action="ADD_HELD", family=z["family"], zone=z["zone"], evidence_status="HELD",
               basis=z["basis"], held_items=z["held_items"], scenarios_beside=z.get("scenarios_beside"))
    ln = BL.make_line(
        project_id=tpl["project"]["project_id"], revision_set_sha256=tpl["project"]["revision_set_sha256"],
        item_code=code, unit="m3", evidence_state=HELD_STATE, measured_net=None, gross=None,
        element_id=z["element_id"], floor=tpl["location"].get("floor"),
        physical_element=f"{word} zone {z['zone'].split(' ')[0]}", formula=formula,
        inputs={REC_KEY: rec, "evidence_status": "HELD"}, documents=copy.deepcopy(tpl["source"]["documents"]),
        geometry_source=tpl["source"]["geometry_source"], geometry_confidence=tpl["source"]["geometry_confidence"],
        rule_id=RULE_ID, rule_version=RULE_VERSION, material_state="SOURCE",
        rfi={"question": f"{word} zone '{z['zone']}': {z['held_items']}"[:900], "unlocks": z["element_id"],
             "bound_beside": beside[:300]},
        notes=f"{METHOD}: earthworks zone line added HELD BLANK (coverage gap); NOT RELEASED",
        item_en=en, item_ar=ar, trade="EARTHWORKS", subtrade=z["family"])
    return _fin(ln)


# ================================================================================================ changes
def _ew_line(by_elem, z, w):
    ln = by_elem.get((z["_code"], z["element_id"]))
    if ln is None:
        raise InputsError(f"{w}: no {z['_code']} line {z['element_id']} in the candidate (stale binding)")
    rec = ((ln.get("calculation") or {}).get("inputs") or {}).get(PRIOR_KEY) or {}
    if rec.get("action") != "ADD_ZONE" or rec.get("family") != z["family"]:
        raise InputsError(f"{w}: {ln['line_id']} carries no V3.0.43 zone record of {z['family']}")
    if ln["evidence_state"] != HELD_STATE or ln.get("measured_net") is not None or ln.get("bounded_range") is not None:
        raise InputsError(f"{w}: {ln['line_id']} is {ln['evidence_state']}, not the HELD BLANK zone line "
                          f"(applied once; stale binding)")
    return ln


def changes_for(doc, prev):
    """-> (changes, log). Each change: piece, action (CHANGE / ADD), before (a candidate line or None), after."""
    if not doc:
        return [], {"piece": "+".join((P_VALUE, P_ADD)), "state": "NO_PROJECT_INPUT"}
    if any(((ln.get("calculation") or {}).get("inputs") or {}).get(REC_KEY) for ln in prev):
        raise InputsError("the candidate already carries V3.0.48 records (applied once)")
    by = {ln["line_id"]: ln for ln in prev}
    by_elem = {(ln["item_code"], (ln.get("location") or {}).get("element_id")): ln for ln in prev
               if ln["item_code"] in EW_CODES}
    if not by_elem:
        raise InputsError("the candidate carries no earthworks zone lines (V3.0.43 first)")
    tpl = next(iter(by_elem.values()))
    S = doc["_sources"]
    changes, seen = [], set(by)
    log = {"piece": "+".join((P_VALUE, P_ADD)), "state": "RUN", "sources": doc["sources"], "by_action": {},
           "lines_added": 0, "lines_changed": 0, "valued_m3": {}, "ranged_m3": {}}

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
        changes.append(A305._change(piece, "ADD" if before is None else "CHANGE", before, after, step=action,
                                    drawing_reference="; ".join(s["file"] for s in srcs),
                                    verification=A3043._ver(srcs), downstream=kw.pop("downstream", []),
                                    group=after["item_code"], **kw))

    exc_value = {}
    for z in doc["_zones"]:
        if z["action"] == "VALUE" and z["_code"] == EXC:
            exc_value[z["element_id"]] = z["_value"]
    for z in doc["_zones"]:
        w = f"{z['action']} {z['family']} {z['zone']}"
        srcs = [S[t] for t in z["source_tasks"]]
        held = [{"what": f"{z['_code']} {z['zone']}", "why": str(z["held_items"])[:300],
                 "range": (f"{_fmt(z['_lo'])} .. {_fmt(z['_hi'])}" if z["_lo"] is not None else None),
                 "scenario": _beside(z)[:300] or None}]
        if z["action"] == "ADD_HELD":
            if (z["_code"], z["element_id"]) in by_elem:
                raise InputsError(f"{w}: the candidate already has this zone line (re-value it, do not add)")
            add(P_ADD, "ADD_HELD", _added(tpl, z, srcs), srcs=srcs, evidence_status="HELD", held=held,
                downstream=[f"coverage: {z['family']} zone {z['zone']} now has its own line (held)"])
            continue
        ln = _ew_line(by_elem, z, w)
        if z["_disp"]:
            ev = z["excavation_element_id"]
            ex = exc_value.get(ev)
            if ex is None:
                raise InputsError(f"{w}: its excavation {ev} is not valued in the same inputs (backfill follows it)")
            d = z["_disp"]
            lo_close, hi_close = ex - d["verified"] - d["high"], ex - d["verified"] - d["low"]
            if abs(lo_close - z["_lo"]) > TOL or abs(hi_close - z["_hi"]) > TOL:
                raise InputsError(f"{w}: range {z['_lo']} .. {z['_hi']} does not close excavation {ex} - displacement "
                                  f"({_fmt(lo_close)} .. {_fmt(hi_close)})")
            if z["_hi"] > ex + TOL:
                raise InputsError(f"{w}: backfill exceeds its excavation")
            exc_ln = by_elem.get((EXC, ev))
            z = dict(z, _exc_line=exc_ln["line_id"] if exc_ln else None, _exc_value=ex)
        new = _valued(ln, z, srcs)
        add(P_VALUE, z["action"], new, before=ln, srcs=srcs, evidence_status=z["_status"], held=held,
            downstream=[f"earthworks roll-up {z['_code']}: HELD BLANK -> "
                        + (f"{_fmt(z['_value'])} m3" if z["_value"] is not None else
                           f"{_fmt(z['_lo'])} .. {_fmt(z['_hi'])} m3"),
                        "no concrete / WP line moves (displacement lines are only read)"])
        if z["_value"] is not None:
            log["valued_m3"][f"{z['family']}|{z['zone']}"] = z["_value"]
        else:
            log["ranged_m3"][f"{z['family']}|{z['zone']}"] = [z["_lo"], z["_hi"]]
    log["by_action"] = dict(sorted(log["by_action"].items()))
    return changes, log


# ================================================================================================ checks
def check_earthworks(lines, before=None):
    """R-T350-1 / R-T350-2 on the integrated lines: every earthworks line carries a zone record (V3.0.43 or V3.0.48),
    each (family, element) once; a line without a V3.0.48 record is HELD BLANK (as V3.0.43 left it); a V3.0.48 line is
    valued in the state its evidence status maps to, or ranged low <= high, or HELD BLANK when added; a backfill range
    never exceeds its excavation line's value; disposal is never valued; a re-valued line keeps its id, code, unit and
    location (when `before` is given). -> summary."""
    out = {"lines": 0, "held_blank": 0, "valued": 0, "ranged": 0, "added_held": 0, "by_family": {},
           "valued_m3": 0.0, "range_low_m3": 0.0, "range_high_m3": 0.0}
    ids = {ln["line_id"]: ln for ln in lines}
    b4 = {ln["line_id"]: ln for ln in before or ()}
    seen = set()
    for ln in lines:
        inp = (ln.get("calculation") or {}).get("inputs") or {}
        rec, prior = inp.get(REC_KEY), inp.get(PRIOR_KEY)
        if ln["item_code"] not in EW_CODES:
            if rec:
                raise ValueError(f"{METHOD}: a V3.0.48 record on {ln['item_code']} {ln['line_id']}")
            continue
        fam = (rec or prior or {}).get("family")
        if not rec and not prior:
            raise ValueError(f"{METHOD}: earthworks line {ln['line_id']} carries no zone record")
        k = (fam, ln["location"].get("element_id"))
        if k in seen:
            raise ValueError(f"{METHOD}: zone {k} carries two lines")
        seen.add(k)
        blank = ln.get("measured_net") is None and ln.get("bounded_range") is None and ln.get("gross") is None
        act = (rec or {}).get("action")
        if not rec or act == "ADD_HELD":
            if ln["evidence_state"] != HELD_STATE or not blank:
                raise ValueError(f"{METHOD}: earthworks line {ln['line_id']} is not HELD BLANK (held is never 0)")
            if FORMULA_END_RE.search(ln["calculation"].get("formula") or ""):
                raise ValueError(f"{METHOD}: held earthworks line {ln['line_id']} formula concludes on a figure")
            out["added_held" if rec else "held_blank"] += 1
        elif act == "VALUE":
            if ln["item_code"] == DSP:
                raise ValueError(f"{METHOD}: disposal {ln['line_id']} valued without its densities")
            if ln["evidence_state"] != STATE_FOR.get(rec.get("evidence_status")) or ln.get("bounded_range") is not None \
                    or abs((ln.get("measured_net") or -1) - rec["value_m3"]) > 1e-9:
                raise ValueError(f"{METHOD}: valued line {ln['line_id']} does not carry its record's value / state")
            out["valued"] += 1
            out["valued_m3"] = _r(out["valued_m3"] + ln["measured_net"])
        elif act == "RANGE":
            br = ln.get("bounded_range") or {}
            if ln["evidence_state"] != RANGE_STATE or ln.get("measured_net") is not None or \
                    abs(br.get("low", -1) - rec["low_m3"]) > 1e-9 or abs(br.get("high", -1) - rec["high_m3"]) > 1e-9 \
                    or br["low"] > br["high"]:
                raise ValueError(f"{METHOD}: ranged line {ln['line_id']} is not held at its record's range")
            disp = rec.get("displacement") or {}
            exl = ids.get(disp.get("excavation_line")) if disp else None
            if ln["item_code"] == BKF and disp:
                if exl is None or exl.get("measured_net") is None:
                    raise ValueError(f"{METHOD}: backfill {ln['line_id']} names no valued excavation line")
                if br["high"] > exl["measured_net"] + TOL:
                    raise ValueError(f"{METHOD}: backfill {ln['line_id']} exceeds its excavation")
            out["ranged"] += 1
            out["range_low_m3"] = _r(out["range_low_m3"] + br["low"])
            out["range_high_m3"] = _r(out["range_high_m3"] + br["high"])
        else:
            raise ValueError(f"{METHOD}: action {act} on {ln['line_id']}")
        o = b4.get(ln["line_id"])
        if rec and o is not None:
            for key in ("item_code", "unit", "location", "line_id", "rule"):
                if o.get(key) != ln.get(key):
                    raise ValueError(f"{METHOD}: re-valued line {ln['line_id']} moved {key}")
            if ((o.get("calculation") or {}).get("inputs") or {}).get(PRIOR_KEY) != prior:
                raise ValueError(f"{METHOD}: re-valued line {ln['line_id']} lost its V3.0.43 zone record")
        out["lines"] += 1
        out["by_family"][fam] = out["by_family"].get(fam, 0) + 1
    out["by_family"] = dict(sorted(out["by_family"].items()))
    return out


# ================================================================================================ integrate / write
def integrate(prev, changes, for_lead=()):
    """-> (V3.0.48 lines, identity). Changed lines replace their candidate line in place; added lines follow; every
    other candidate line is byte-identical (asserted)."""
    sid = {ln["line_id"]: i for i, ln in enumerate(prev)}
    out = list(prev)
    adds, repl = [], set()
    for c in changes:
        a = c["after"]
        if a["item_code"] not in EW_CODES:
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
    ident = {"base_lines": len(prev), "v3_0_48_lines": len(out), "v3_0_48_rows": len(changes),
             "replaced": len(repl), "added": len(adds), "guards": guards,
             "roof_buildup": A3031.check_roof_layers(out), "ceilings": A3032.check_ceilings(out),
             "corrections": A3033.check_corrections(out), "tile_zones": A3034.check_zones(out),
             "fence": A3035.check_boundary(out), "lists": A3036.check_lists(out), "beds": A3038.check_beds(out),
             "lift": A3038.check_lift(out), "landing": A3038.check_landing(out), "flights": A3039.check_flights(out),
             "gb_runs": A3040.check_runs(out), "pieces": A3041.check_pieces(out), "slab": A3042.check_slab(out),
             "earthworks": check_earthworks(out, prev), "skirting": A3044.check_skirting(out),
             "blinding": A3045.check_blinding(out), "tie_masonry": A3046.check_tie_masonry(out),
             "stair_rooms": A3047.check_stair_rooms(out)}
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
                     "element_id": loc.get("element_id"), "unit": ref["unit"],
                     "before_released_v2_9": b29, "before_base": A30._qty(c.get("before")),
                     "after_v3_0_48": A30._qty(ref), "evidence_status": c.get("evidence_status"),
                     "still_held": c.get("held"), "release_status": "NOT RELEASED",
                     "owner_manual_method": PIECES[c["piece"]]["owner_manual_method"],
                     "drawing_derived_method": PIECES[c["piece"]]["drawing_method"],
                     "record": rec, "verification": c.get("verification") or {}, "rollback": ROLLBACK})
    return rows


LEDGER_CSV = ("version", "piece", "action", "change", "line_id", "item_code", "floor", "element_id", "unit", "v2_9",
              "base", "v3_0_48", "evidence_status", "still_held", "verification")
DIFF_CSV = ("line_id", "item_code", "floor", "element_id", "unit", "vs_base", "vs_released_v2_9", "v2_9", "base",
            "v3_0_48")


def ledger_csv(rows):
    def q(x):
        return A302._q(x) if x and (x.get("value") is not None or x.get("low") is not None or x.get("state")) else ""

    def h(r):
        return "; ".join(f"{x['what']} {x.get('range')}" for x in (r.get("still_held") or ()))[:300]
    return A305._csv([{"version": r["version"], "piece": r["piece"], "action": r["action"], "change": r["change"],
                       "line_id": r["line_id"], "item_code": r["item_code"], "floor": r.get("floor") or "",
                       "element_id": r.get("element_id") or "", "unit": r["unit"],
                       "v2_9": q(r.get("before_released_v2_9")), "base": q(r.get("before_base")),
                       "v3_0_48": q(r.get("after_v3_0_48")), "evidence_status": r["evidence_status"],
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
                    "base": A302._q(A30._qty(o)) if o else "", "v3_0_48": A302._q(A30._qty(ln))})
    return out


def write(out, prev, changes, log, released_lines=None, for_lead=()):
    """the V3_0_48_* files beside the base candidate's files. -> (file names, identity, ledger)."""
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
    moved = {k: {"base": t0.get(k), "v3_0_48": t1.get(k)} for k in sorted(set(t0) | set(t1)) if t0.get(k) != t1.get(k)}
    for k in moved:
        if k.split("|")[0] not in EW_CODES:
            raise ValueError(f"{METHOD}: totals moved outside this version's codes: {k}")
    led = {"schema": LEDGER_SCHEMA, "method": METHOD, "extends": EXTENDS, "candidate": CANDIDATE,
           "base": A30.BASE_METHOD, "released": A30.RELEASED_METHOD, "released_default": False, "rows": rows,
           "waiting_pieces": WAITING, "integration_package": True}
    run = {"method": METHOD, "policy": POLICY_ID, "extends": EXTENDS, "candidate": CANDIDATE,
           "base_method": A30.BASE_METHOD, "released_method": A30.RELEASED_METHOD, "released_default": False,
           "rollback": ROLLBACK, "identity": ident, "pieces": PIECES, "piece_logs": [log],
           "totals_moved_by_code": moved, "waiting_pieces": WAITING}
    files = {"V3_0_48_BOQ_LINES.json": BL.dumps(new),
             "V3_0_48_BOQ_LINES.csv": A30._lines_csv(new),
             "V3_0_48_INTEGRATION_LEDGER.json": A30._j(led),
             "V3_0_48_INTEGRATION_LEDGER.csv": ledger_csv(rows),
             "V3_0_48_DIFF.csv": A305._csv(diff, DIFF_CSV),
             "V3_0_48_RUN.json": A30._j(run)}
    for name, text in files.items():
        (out / name).write_text(text, encoding="utf-8")
    return sorted(files), ident, led


def policy_record():
    return {"method": METHOD, "extends": EXTENDS, "pieces": sorted(PIECES), "inputs_schema": INPUTS_SCHEMA,
            "released_default": False, "rollback": ROLLBACK, "actions": list(ACTIONS)}


__all__ = ["METHOD", "PIECES", "WAITING", "DEFAULT_GUARD_CLASS", "INPUTS_SCHEMA", "EW_CODES", "load_inputs",
           "changes_for", "check_earthworks", "integrate", "ledger_rows", "diff_rows", "write", "InputsError"]
