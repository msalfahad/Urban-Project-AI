"""ARCH_TAKEOFF_V3.0.43 (T-350): the SAME opt-in BOQ candidate as ARCH_TAKEOFF_V3.0 .. V3.0.42 (engine.source.arch_v30,
arch_v301 .. arch_v3042), extended with the MISSING EARTHWORKS categories (B1-02 excavation, B1-03 backfill, B1-04
disposal) from the Checker-verified FILL tables, and the held-range fixes the same tables name, in ONE step:

  EW_ZONE     one new earthworks line per FILL zone (excavation / backfill / disposal x the zones the drawings zone it).
              Every line is HELD BLANK (BLOCKED_RFI, no measured_net, no range): its formation, working space or zone
              extent is a designer item. Beside it, never in it: the bound the merged ledger proved (AT_LEAST from a
              printed minimum depth or level, ZERO_BY_BOUND under a named condition, the m3 per metre of an unknown
              depth), the held items by name, and the buried-structure lines whose displacement it binds.
  RANGE_FIX   a held (BOUNDED_EXPOSURE) concrete line whose audit range the merged ledger corrects gets that range;
              its state, measured_net (blank), rfi and id stay; the former range is kept in the record.

R-T350-1 (every villa; integrates R-T347-1 .. 5, R-T356, R-EG-REF-1 / 2, R-EG-COEF-1): (a) an earthworks quantity is
excavated minus displacement (backfill) and excavated minus re-used fill (disposal); while the formation, working space
or extent is unprinted the line is HELD BLANK, never 0 and never a convention; (b) a printed minimum depth gives an
AT_LEAST bound beside the line, never its quantity; (c) a bulking factor only from an answered rule (none: disposal in
situ); (d) each zone once; a buried line is bound by id (a line whose components sit in two zones is named in both and
listed, its components split once in the merged binding); (e) a range fix moves only a held
line's range, never a value, never a state upwards; (f) held is never 0.

Nothing else moves: every V3.0.42 line not named by the inputs is byte-identical (asserted); totals move only in the
earthworks codes (new, blocked lines only) and the held range of the named concrete codes (asserted). Files:
V3_0_43_BOQ_LINES.json / .csv, V3_0_43_INTEGRATION_LEDGER.json / .csv, V3_0_43_DIFF.csv, V3_0_43_RUN.json. Nothing
here names a project, a sheet, a layer or a coordinate.
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

DEFAULT_GUARD_CLASS = "TOOLING"          # T-212: re-books checker-merged ledgers; adds no default value
METHOD = "ARCH_TAKEOFF_V3.0.43"
EXTENDS = A3042.METHOD
CANDIDATE = A30.METHOD
POLICY_ID = "URBAN_BOQ_T350_ARCH_V3_0_43"
INPUTS_SCHEMA = "URBAN_V3043_INPUTS_V1"
LEDGER_SCHEMA = "URBAN_V3043_INTEGRATION_LEDGER_V1"
ROLLBACK = A30.ROLLBACK
InputsError = A3031.InputsError
_r = A3018._r
_fmt = A3030._fmt
RULE_ID, RULE_VERSION = "R-T350-1", "T-350"
REC_KEY = "earthworks_v3043"
P_ZONE, P_RANGE = "EW_ZONE", "RANGE_FIX"
EXC, BKF, DSP = "STR.EARTH.EXCAVATION", "STR.EARTH.BACKFILL", "STR.EARTH.DISPOSAL"
FAMILY_CODE = {"B1-02": EXC, "B1-03": BKF, "B1-04": DSP}
ITEM_TEXT = {EXC: ("Excavation (by zone)", "حفريات", "excavation"),
             BKF: ("Backfill and compaction (by zone)", "ردم ودك", "backfill"),
             DSP: ("Disposal of surplus excavated material", "نقل الفائض", "disposal")}
EW_CODES = (EXC, BKF, DSP)
BOUNDS = ("AT_LEAST", "ZERO_BY_BOUND", "HELD")
HELD_STATE = "BLOCKED_RFI"
RANGE_STATE = "BOUNDED_EXPOSURE"
RANGE_CODES = ("STR.CONC.BLINDING", "STR.CONC.STRAP", "STR.CONC.FOOTING", "STR.CONC.GROUND_BEAM")
TOL = 0.0000015
LINE_ID_RE = re.compile(r"^L-[0-9a-f]{20}$")
# a held line's formula never concludes on '= <x> m3' / 'net <x> m3' (T-334 FORMULA_END): bounds are written 'at least'
FORMULA_END_RE = re.compile(r"(?:=|\bnet)\s*-?\d+(?:\.\d+)?\s*m3(?![A-Za-z0-9])")

PIECES = {
    P_ZONE: {"module": "engine/source/arch_v3043.py (one HELD BLANK earthworks line per FILL zone; the proved bound, "
                       "the held items and the bound buried lines beside, never in the quantity)",
             "policy": "EW_ZONE_V1", "rule_id": "R-T347-1 .. 5, R-T357 (R-T350-1 a .. d, f)",
             "owner_rules": ["Q-21 C (the printed 1.50 m is a minimum below the existing plot level, not the founding "
                             "level)", "OQ-13 / RFI S1 (working space, pits vs bulk dig: designer / contractor items)",
                             "UP-QTY-STATUS-001 (held is blank, never 0)",
                             "ELEMENT_REGISTER buried structure: blinding = CONC.BLINDING, membrane + screed = WP, "
                             "excavation / backfill / disposal = EARTHWORKS, each element once"],
             "owner_manual_method": "owner method: excavation = plan of each pit / trench (neat + working space) x "
                                    "depth from the existing ground to the formation; backfill = excavation - the "
                                    "buried structure (blinding, membrane + screed, footings, necks, ground beams) "
                                    "below the existing ground; disposal = excavation - backfill re-used (- fill "
                                    "above ground re-used), a bulking factor only by an answered rule",
             "drawing_method": "the merged FILL table: neat pit plans by DXF outline handle net of the real overlaps "
                               "(Checker re-measure 129.234375 m2), the printed minimum depth 1.50 m below the "
                               "existing plot level (a bound), the printed pool formation -1.50, the net displacement "
                               "ledger bound line by line; formation, working space and every unprinted section "
                               "held by name"},
    P_RANGE: {"module": "engine/source/arch_v3043.py (a held concrete line's audit range corrected to the merged "
                        "ledger; no value, no state)", "policy": "EW_RANGE_FIX_V1",
              "rule_id": "R-T347 F-T347-1, R-T356 F-T347-2 (R-T350-1 e)",
              "owner_rules": ["UP-QTY-STATUS-001", "owner 2026-10-24 23:57 downgrade-only record rules (a range is "
                              "corrected to the merged ledger, a state never rises)", "D-15 (blinding under straps)"],
              "owner_manual_method": "not a new quantity: the held line shows the range the printed sources allow, "
                                     "both ends on an admissible basis",
              "drawing_method": "the merged range by line id (T-233 / T-230 strap ledger; T-356 own strip by the "
                                "printed B + 0.20 x the axis clear between footing faces)"},
}
WAITING = dict(A3042.WAITING)
WAITING.update({
    "T350_B1_01_SITE_CLEARANCE": "NOT IN DRAWN SCOPE (T-357 MERGED 90135e91: no site plan, no clearance note in the "
                                 "issued set, sheet by sheet): no line; the coverage registry says so",
    "T350_NECK_END_RANGE": "T-356 F-T347-4 neck-end ranges of L-0e852cca (15C+7CC: low 0.216 -> 0.207) and L-0bb78acc "
                           "(17E+17F: high 0.291231 -> 0.295391 m3): since V3.0.40 both lines are VALUED and named by "
                           "the downgrade proposal DGP-T430-GB-D34-SHORT (audit 0.864171 .. 1.152231 m3, 4 lines): "
                           "the corrected ends belong in that Checker record's audit range, not in a line; no line "
                           "moves here (T-356: lengths not re-measured by the Checker)",
    "T350_DOWNGRADE_RECORDS": "DGP-T356-BAND (L-6290a9f3) and DGP-T356-GB-D34 (9 GB lines) live as the Checker's "
                              "downgrade-only records outside the lines (owner 2026-10-24 23:57); this version reads "
                              "them (the bound lists name the lines) and edits no m3 of those lines",
    "T350_S01_ESTIMATED": "RFI re-review 2026-11-02 S01 ESTIMATED (founding level = the printed 1.50 m minimum below "
                          "the existing plot level, +-0.10 m sensitivity): not applied; the owner's Checker condition "
                          "(5) and 'the Checker verifies each basis before any line uses it' hold it until T-180 clears "
                          "it; even then the working space (OQ-13) keeps the excavation lines held. Scenario beside: "
                          "pits at d = 0 equal the AT_LEAST bound, +-0.10 m moves them +-12.923 m3",
    "T350_S05_SB3": "RFI re-review S05 (SB3 concrete invariant to top / bottom alignment): Checker condition (2) open; "
                    "the SB3-in-F3 line keeps the merged T-230 / T-233 held range, no value",
    "T350_PITS_BOUND_N_T347_1": "the pits AT_LEAST bound subtracts the F8 n envelope n beyond-plot strip 0.067873 m2 "
                                "twice (0.1018 m3 low; still a valid lower bound): add it back once when D-14 / "
                                "F-T320-05 resolve (Checker N-T347-1)",
})
ACTIONS = ("ADD_ZONE", "RANGE_FIX")


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
    if x > 100000:
        raise InputsError(f"{where}: {x} is not a quantity in m3 (litres / mm3 refused)")
    return float(x)


def _opt(x, where, pos=False):
    return None if x in (None, "") else _num(x, where, pos)


def _sources(doc):
    srcs = {}
    for s in doc.get("sources") or ():
        _need(s, ("task", "file", "sha256", "merge_commit", "checker_run"), f"source {s.get('task')}")
        srcs[s["task"]] = s
    if not srcs:
        raise InputsError("sources: the merged ledgers the lines come from")
    return srcs


def _tasks(r, srcs, where):
    if not r.get("source_tasks") or any(t not in srcs for t in r["source_tasks"]):
        raise InputsError(f"{where}: no merged source named")


def _zone(z, srcs, seen):
    w = f"zone {z.get('family')} {z.get('zone')}"
    _need(z, ("family", "zone", "bound", "held_items", "element_id", "floor"), w)
    _tasks(z, srcs, w)
    if z["family"] not in FAMILY_CODE:
        raise InputsError(f"{w}: family {z['family']} is not B1-02 / B1-03 / B1-04")
    if z["bound"] not in BOUNDS:
        raise InputsError(f"{w}: bound {z['bound']} is not one of {BOUNDS}")
    key = (z["family"], z["zone"])
    if key in seen or z["element_id"] in {v for v in seen.values()}:
        raise InputsError(f"{w}: zone named twice (one zone, one line)")
    seen[key] = z["element_id"]
    if "value" in z and z["value"] not in (None, ""):
        raise InputsError(f"{w}: HELD_WITH_VALUE: an earthworks zone carries no value in this version (held blank)")
    lo, hi = _opt(z.get("at_least"), f"{w} at_least"), _opt(z.get("upper"), f"{w} upper")
    coef = _opt(z.get("coef_per_m"), f"{w} coef_per_m")
    if z["bound"] == "AT_LEAST":
        if lo is None or lo <= 0:
            raise InputsError(f"{w}: an AT_LEAST bound needs its positive figure (a held 0 is refused)")
        if hi is not None:
            raise InputsError(f"{w}: an AT_LEAST bound has no upper end")
    elif z["bound"] == "ZERO_BY_BOUND":
        if hi is None or hi != 0 or lo is not None or not z.get("condition"):
            raise InputsError(f"{w}: ZERO_BY_BOUND needs upper 0 and its condition, and no lower figure")
    else:
        if lo is not None or hi is not None:
            raise InputsError(f"{w}: a HELD zone carries no bound figure")
    lines = list(z.get("bound_lines") or ())
    for lid in lines:
        if not LINE_ID_RE.match(str(lid)):
            raise InputsError(f"{w}: {lid!r} is not a BOQ line id")
    if len(set(lines)) != len(lines):
        raise InputsError(f"{w}: a bound line is named twice")
    return dict(z, _code=FAMILY_CODE[z["family"]], _lo=lo, _hi=hi, _coef=coef, _lines=lines)


def load_inputs(doc, project_id=None):
    """URBAN_V3043_INPUTS_V1 -> the validated doc.
    {"schema", "project_id", "sources": [{"task", "file", "sha256", "merge_commit", "checker_run"}],
     "existing_ground": {"status", "datum", "source", "residual"},
     "template_line": a candidate line id whose project / documents the new lines carry,
     "zones": [{"family" (B1-02 / B1-03 / B1-04), "zone", "element_id", "floor", "bound" (AT_LEAST / ZERO_BY_BOUND /
                HELD), "at_least", "upper", "coef_per_m", "condition", "held_items", "bound_lines", "known_parts",
                "basis", "eg_coef_per_m", "physical_element", "source_tasks"}],
     "ranges": [{"line_id", "item_code", "expect": {"low", "high"}, "low", "high", "basis", "why", "source_tasks"}]}"""
    if not doc:
        return None
    if doc.get("schema") != INPUTS_SCHEMA:
        raise InputsError(f"project inputs: schema must be {INPUTS_SCHEMA}")
    if project_id and doc.get("project_id") not in (None, project_id):
        raise InputsError(f"project inputs are for {doc.get('project_id')!r}, the run is {project_id!r}")
    srcs = _sources(doc)
    eg = doc.get("existing_ground") or {}
    _need(eg, ("status", "source"), "existing_ground")
    if eg["status"] not in ("PRINTED", "DERIVED", "HELD"):
        raise InputsError(f"existing_ground: status {eg['status']} (PRINTED / DERIVED / HELD; never assumed)")
    if eg["status"] == "HELD" and eg.get("datum") not in (None, ""):
        raise InputsError("existing_ground: a HELD reference carries no datum (never assumed 0.00)")
    if not doc.get("template_line"):
        raise InputsError("template_line missing")
    seen = {}
    zones = [_zone(z, srcs, seen) for z in doc.get("zones") or ()]
    if not zones:
        raise InputsError("no earthworks zone in the inputs")
    ranges, rseen = [], set()
    for x in doc.get("ranges") or ():
        w = f"range fix {x.get('line_id')}"
        _need(x, ("line_id", "item_code", "basis", "why"), w)
        _tasks(x, srcs, w)
        if x["line_id"] in rseen:
            raise InputsError(f"{w}: named twice")
        rseen.add(x["line_id"])
        if x["item_code"] not in RANGE_CODES:
            raise InputsError(f"{w}: {x['item_code']} is not a buried concrete code this version may re-range")
        lo, hi = _num(x.get("low"), f"{w} low"), _num(x.get("high"), f"{w} high", pos=True)
        if lo > hi:
            raise InputsError(f"{w}: low {lo} > high {hi}")
        e = x.get("expect") or {}
        _num(e.get("low"), f"{w} expect.low")
        _num(e.get("high"), f"{w} expect.high")
        ranges.append(dict(x, _lo=lo, _hi=hi))
    return dict(doc, _sources=srcs, _eg=eg, _zones=zones, _ranges=ranges)


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


def _fin(ln):
    from engine.source import boq_line as BL
    ln["project"] = copy.deepcopy(ln["project"])
    return BL.validate(ln)


def _bound_text(z):
    if z["bound"] == "AT_LEAST":
        t = f"bound beside (never the quantity): at least {_fmt(z['_lo'])} m3"
    elif z["bound"] == "ZERO_BY_BOUND":
        t = f"bound beside (never the quantity): nothing below the existing ground while {z['condition']}"
    else:
        t = "no bound proved"
    if z["_coef"] is not None:
        t += f"; every metre of the unknown depth below the printed minimum adds {_fmt(z['_coef'])} m3"
    if z.get("eg_coef_per_m") not in (None, ""):
        t += f"; existing-ground coefficient {z['eg_coef_per_m']}"
    return t


def _plain(text):
    """a merged held text shown in a held line's formula: 'a = 2.5 m3' -> 'a equals 2.5 m3' and 'net 2.5 m3' -> 'net of
    2.5 m3', so the formula never reads as concluding on a figure (T-334); the record keeps the merged text verbatim."""
    t = re.sub(r"=\s*(-?\d+(?:\.\d+)?\s*m3(?![A-Za-z0-9]))", r"equals \1", str(text or ""))
    return re.sub(r"\bnet\s+(?=-?\d)", "net of ", t)


def _zone_line(z, tpl, eg, srcs):
    from engine.source import boq_line as BL
    code = z["_code"]
    en, ar, word = ITEM_TEXT[code]
    held = str(z["held_items"])
    bound = _bound_text(z)
    formula = (f"{METHOD}: HELD (never a value) {word} zone '{_plain(z['zone'])}': {_plain(z.get('basis'))} | held by: "
               f"{_plain(held)} | "
               f"{bound} | existing ground {eg['status']} {eg.get('datum') or ''} ({eg['source']})")
    formula = formula[:1500]
    if FORMULA_END_RE.search(formula):
        raise InputsError(f"zone {z['zone']}: the formula would conclude on a figure (write bounds as 'at least')")
    rec = _rec(P_ZONE, srcs, action="ADD_ZONE", family=z["family"], zone=z["zone"], bound=z["bound"],
               at_least_m3=z["_lo"], upper_m3=z["_hi"], coef_m3_per_m_depth=z["_coef"],
               condition=z.get("condition"), held_items=held, basis=z.get("basis"), known_parts=z.get("known_parts"),
               bound_lines=z["_lines"], existing_ground=dict(eg), eg_coef_per_m=z.get("eg_coef_per_m"),
               bulking="none (no answered rule; R-T347-5): in situ", evidence_status="HELD")
    ln = BL.make_line(
        project_id=tpl["project"]["project_id"], revision_set_sha256=tpl["project"]["revision_set_sha256"],
        item_code=code, unit="m3", evidence_state=HELD_STATE, measured_net=None, gross=None,
        element_id=z["element_id"], floor=z["floor"], physical_element=z.get("physical_element") or f"{word} zone",
        formula=formula, inputs={REC_KEY: rec, "evidence_status": "HELD"},
        documents=copy.deepcopy(tpl["source"]["documents"]), geometry_source=tpl["source"]["geometry_source"],
        geometry_confidence=tpl["source"]["geometry_confidence"], rule_id=RULE_ID, rule_version=RULE_VERSION,
        material_state="SOURCE",
        rfi={"question": f"{word} zone '{z['zone']}': {held}"[:900], "unlocks": z["element_id"],
             "bound_beside": bound[:300]},
        notes=(f"{METHOD}: earthworks zone line, HELD BLANK ({z['bound']} beside); bound lines "
               f"{len(z['_lines'])}; NOT RELEASED"),
        item_en=en, item_ar=ar, trade="EARTHWORKS", subtrade=z["family"])
    return _fin(ln)


def _ranged(ln, x, srcs):
    new = copy.deepcopy(ln)
    br = dict(new.get("bounded_range") or {})
    was = {"low": br.get("low"), "high": br.get("high"), "basis": br.get("basis")}
    br.update({"low": x["_lo"], "high": x["_hi"], "basis": f"{x['basis']} (was {_fmt(was['low'])} .. "
                                                           f"{_fmt(was['high'])}; {RULE_ID})"[:300]})
    new["bounded_range"] = br
    inp = new["calculation"]["inputs"] = dict(new["calculation"]["inputs"] or {})
    inp[REC_KEY] = _rec(P_RANGE, srcs, action="RANGE_FIX", was=was, low=x["_lo"], high=x["_hi"], why=x["why"],
                        evidence_status=inp.get("evidence_status") or "HELD")
    new["notes"] = (f"{new.get('notes') or ''} | {METHOD}: held range {_fmt(was['low'])} .. {_fmt(was['high'])} -> "
                    f"{_fmt(x['_lo'])} .. {_fmt(x['_hi'])} m3 ({x['why']}); state unchanged")[:2000]
    return _fin(new)


# ================================================================================================ changes
def changes_for(doc, l3042):
    """-> (changes, log). Each change: piece, action (CHANGE / ADD), before (a V3.0.42 line or None), after."""
    if not doc:
        return [], {"piece": "+".join((P_ZONE, P_RANGE)), "state": "NO_PROJECT_INPUT"}
    if any(((ln.get("calculation") or {}).get("inputs") or {}).get(REC_KEY) for ln in l3042):
        raise InputsError("the candidate already carries V3.0.43 records (applied once)")
    if any(ln["item_code"] in EW_CODES for ln in l3042):
        raise InputsError("the candidate already carries earthworks lines (re-value them, do not add)")
    by = {ln["line_id"]: ln for ln in l3042}
    S = doc["_sources"]
    tpl = by.get(doc["template_line"])
    if tpl is None:
        raise InputsError(f"template line {doc['template_line']} is not in the candidate (stale binding)")
    changes, seen = [], set(by)
    log = {"piece": "+".join((P_ZONE, P_RANGE)), "state": "RUN", "sources": doc["sources"], "by_action": {},
           "lines_added": 0, "lines_changed": 0, "zones": {}, "at_least_m3": {}, "bound_lines": 0}

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

    for z in doc["_zones"]:
        srcs = [S[t] for t in z["source_tasks"]]
        miss = [lid for lid in z["_lines"] if lid not in by]
        if miss:
            raise InputsError(f"zone {z['zone']}: bound line(s) {miss[:3]} not in the candidate (stale binding)")
        bad = [lid for lid in z["_lines"] if by[lid]["item_code"] in EW_CODES]
        if bad:
            raise InputsError(f"zone {z['zone']}: an earthworks line cannot be a displacement line")
        new = _zone_line(z, tpl, doc["_eg"], srcs)
        held = [{"what": f"{z['_code']} {z['zone']}", "why": str(z["held_items"])[:300],
                 "range": (f">= {_fmt(z['_lo'])}" if z["_lo"] is not None else
                           ("0 under its condition" if z["bound"] == "ZERO_BY_BOUND" else None)),
                 "scenario": "held blank: formation / working space / extent are designer items"}]
        add(P_ZONE, "ADD_ZONE", new, srcs=srcs, evidence_status="HELD", held=held,
            downstream=["coverage registry " + z["family"] + " -> in the candidate (held)",
                        "trade completeness: EARTHWORKS lines present, every one held",
                        "no concrete / WP line moves (displacement lines are only named)"])
        log["zones"][z["family"]] = log["zones"].get(z["family"], 0) + 1
        if z["_lo"] is not None:
            log["at_least_m3"][f"{z['family']}|{z['zone']}"] = z["_lo"]
        log["bound_lines"] += len(z["_lines"])
    for x in doc["_ranges"]:
        srcs = [S[t] for t in x["source_tasks"]]
        w = f"range fix {x['line_id']}"
        ln = by.get(x["line_id"])
        if ln is None or ln["item_code"] != x["item_code"] or ln["unit"] != "m3":
            raise InputsError(f"{w}: not a {x['item_code']} m3 line of the candidate (stale binding)")
        if ln["evidence_state"] != RANGE_STATE or ln.get("measured_net") is not None:
            raise InputsError(f"{w}: {ln['evidence_state']} {ln.get('measured_net')} is not a held ranged line (a "
                              f"valued line is never re-ranged here: downgrade-only records belong to the Checker)")
        br = ln.get("bounded_range") or {}
        e = x["expect"]
        if abs((br.get("low") or 0) - e["low"]) > TOL or abs((br.get("high") or 0) - e["high"]) > TOL:
            raise InputsError(f"{w}: held range {br.get('low')} .. {br.get('high')} is not the range the merged "
                              f"ledger corrected ({e['low']} .. {e['high']}; stale binding)")
        new = _ranged(ln, x, srcs)
        add(P_RANGE, "RANGE_FIX", new, before=ln, srcs=srcs, evidence_status="HELD",
            held=[{"what": f"{ln['item_code']} {x['line_id']}", "why": x["why"][:300],
                   "range": f"{_fmt(x['_lo'])} .. {_fmt(x['_hi'])}", "scenario": "held range only"}],
            downstream=["concrete roll-up: held range of the code moves; released total unchanged"])
    log["by_action"] = dict(sorted(log["by_action"].items()))
    return changes, log


# ================================================================================================ checks
def check_earthworks(lines, before=None):
    """R-T350-1 on the integrated lines: every earthworks line is HELD BLANK (BLOCKED_RFI, no net, no range, no gross)
    with its record, each (family, zone) once, each bound line in one zone per family, no earthworks line among the
    bound lines, an AT_LEAST bound positive; a re-ranged line stays held and blank and keeps its rfi, state and id
    (when `before` is given). -> summary."""
    out = {"lines": 0, "by_family": {}, "at_least_m3": 0.0, "ranges_fixed": 0}
    ids = {ln["line_id"] for ln in lines}
    zones, owner = set(), {}
    b4 = {ln["line_id"]: ln for ln in before or ()}
    for ln in lines:
        rec = ((ln.get("calculation") or {}).get("inputs") or {}).get(REC_KEY)
        if ln["item_code"] in EW_CODES:
            if not rec or rec.get("action") != "ADD_ZONE":
                raise ValueError(f"{METHOD}: earthworks line {ln['line_id']} carries no zone record")
            if ln["evidence_state"] != HELD_STATE or ln.get("measured_net") is not None or ln.get("gross") is not None \
                    or ln.get("bounded_range") is not None:
                raise ValueError(f"{METHOD}: earthworks line {ln['line_id']} is not HELD BLANK (held is never 0 and "
                                 f"never a value here)")
            if FORMULA_END_RE.search(ln["calculation"].get("formula") or ""):
                raise ValueError(f"{METHOD}: earthworks line {ln['line_id']} formula concludes on a figure")
            k = (rec["family"], rec["zone"])
            if k in zones:
                raise ValueError(f"{METHOD}: zone {k} carries two lines")
            zones.add(k)
            if rec["bound"] == "AT_LEAST":
                if not rec.get("at_least_m3") or rec["at_least_m3"] <= 0:
                    raise ValueError(f"{METHOD}: AT_LEAST zone {k} without its positive figure")
                out["at_least_m3"] = _r(out["at_least_m3"] + rec["at_least_m3"])
            if len(set(rec["bound_lines"])) != len(rec["bound_lines"]):
                raise ValueError(f"{METHOD}: zone {k} names a bound line twice")
            for lid in rec["bound_lines"]:
                if lid not in ids:
                    raise ValueError(f"{METHOD}: zone {k} names line {lid} that is not in the candidate")
                owner.setdefault((rec["family"], lid), []).append(rec["zone"])
            out["lines"] += 1
            out["by_family"][rec["family"]] = out["by_family"].get(rec["family"], 0) + 1
        elif rec:
            if rec.get("action") != "RANGE_FIX":
                raise ValueError(f"{METHOD}: action {rec.get('action')} on a non-earthworks line")
            br = ln.get("bounded_range") or {}
            if ln["evidence_state"] != RANGE_STATE or ln.get("measured_net") is not None or \
                    abs(br.get("low") - rec["low"]) > 1e-9 or abs(br.get("high") - rec["high"]) > 1e-9:
                raise ValueError(f"{METHOD}: re-ranged line {ln['line_id']} is not held at its corrected range")
            o = b4.get(ln["line_id"])
            if o is not None:
                for k in ("evidence_state", "measured_net", "gross", "rfi", "item_code", "unit", "location"):
                    if o.get(k) != ln.get(k):
                        raise ValueError(f"{METHOD}: re-ranged line {ln['line_id']} moved {k}")
            out["ranges_fixed"] += 1
    out["by_family"] = dict(sorted(out["by_family"].items()))
    out["bound_line_pairs"] = len(owner)
    # a line whose displacement components sit in two zones (one blinding line under pits and the lift raft; a run
    # crossing two trench classes) is named in both lists; its components are split once in the merged binding
    # (T-347: 256 components, one line each), never here: the shared lines are listed, not netted
    out["lines_in_two_zones"] = sorted(f"{f}:{lid}" for (f, lid), zs in owner.items() if len(zs) > 1)
    return out


# ================================================================================================ integrate / write
def integrate(l3042, changes, for_lead=()):
    """-> (V3.0.43 lines, identity). Changed lines replace their V3.0.42 line in place; added lines follow; every other
    V3.0.42 line is byte-identical (asserted)."""
    sid = {ln["line_id"]: i for i, ln in enumerate(l3042)}
    out = list(l3042)
    adds, repl = [], set()
    for c in changes:
        a = c["after"]
        if c["action"] == "ADD":
            if a["line_id"] in sid:
                raise ValueError(f"{METHOD}: an added line repeats a V3.0.42 id")
            if a["item_code"] not in EW_CODES:
                raise ValueError(f"{METHOD}: added code {a['item_code']} is not one this version adds")
            adds.append(a)
        elif c["action"] == "CHANGE":
            i = sid.get(a["line_id"])
            if i is None or a["line_id"] in repl:
                raise ValueError(f"{METHOD}: a changed line is not a V3.0.42 line or changes twice")
            if a["item_code"] not in RANGE_CODES:
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
    beds = A3038.check_beds(out)
    lift = A3038.check_lift(out)
    landing = A3038.check_landing(out)
    flights = A3039.check_flights(out)
    runs = A3040.check_runs(out)
    pieces = A3041.check_pieces(out)
    slab = A3042.check_slab(out)
    earth = check_earthworks(out, l3042)
    pids = {(ln["project"]["project_id"], ln["project"]["revision_set_sha256"]) for ln in out}
    if len(pids) != 1:
        raise ValueError(f"{METHOD}: {len(pids)} project identities in the lines")
    outside = [ln for ln in l3042 if ln["line_id"] not in repl]
    bad = [a["line_id"] for a in outside if A30.line_sha(a) != A30.line_sha(out[sid[a["line_id"]]])]
    if bad:
        raise ValueError(f"{METHOD}: {len(bad)} V3.0.42 line(s) differ outside the named changes")
    ident = {"v3_0_42_lines": len(l3042), "v3_0_43_lines": len(out), "v3_0_43_rows": len(changes),
             "replaced": len(repl), "added": len(adds), "outside_rows": len(outside),
             "outside_rows_identical_to_v3_0_42": len(outside), "earthworks": earth, "slab": slab, "pieces": pieces,
             "gb_runs": runs, "flights": flights, "beds": beds, "lift": lift, "landing": landing, "lists": lists,
             "fence": fence, "tile_zones": zones, "corrections": corr, "ceilings": ceil, "roof_buildup": roof,
             "guards": guards,
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
        rows.append({"version": METHOD, "piece": c["piece"], "action": c.get("step"), "change": c["action"],
                     "line_id": ref["line_id"], "item_code": ref["item_code"], "floor": loc.get("floor"),
                     "element_id": loc.get("element_id"), "unit": ref["unit"],
                     "before_released_v2_9": b29, "before_v3_0_42": A30._qty(c.get("before")),
                     "after_v3_0_43": A30._qty(ref), "evidence_status": c.get("evidence_status"),
                     "still_held": c.get("held"), "release_status": "NOT RELEASED",
                     "owner_manual_method": PIECES[c["piece"]]["owner_manual_method"],
                     "drawing_derived_method": PIECES[c["piece"]]["drawing_method"],
                     "record": rec, "verification": c.get("verification") or {}, "rollback": ROLLBACK})
    return rows


LEDGER_CSV = ("version", "piece", "action", "change", "line_id", "item_code", "floor", "element_id", "unit", "v2_9",
              "v3_0_42", "v3_0_43", "evidence_status", "still_held", "verification")
DIFF_CSV = ("line_id", "item_code", "floor", "element_id", "unit", "vs_v3_0_42", "vs_released_v2_9", "v2_9",
            "v3_0_42", "v3_0_43")


def ledger_csv(rows):
    def q(x):
        return A302._q(x) if x and (x.get("value") is not None or x.get("low") is not None or x.get("state")) else ""

    def h(r):
        return "; ".join(f"{x['what']} {x.get('range')}" for x in (r.get("still_held") or ()))[:300]
    return A305._csv([{"version": r["version"], "piece": r["piece"], "action": r["action"], "change": r["change"],
                       "line_id": r["line_id"], "item_code": r["item_code"], "floor": r.get("floor") or "",
                       "element_id": r.get("element_id") or "", "unit": r["unit"],
                       "v2_9": q(r.get("before_released_v2_9")), "v3_0_42": q(r.get("before_v3_0_42")),
                       "v3_0_43": q(r.get("after_v3_0_43")), "evidence_status": r["evidence_status"],
                       "still_held": h(r),
                       "verification": f"{r['verification'].get('task')} "
                                       f"{' '.join(x[:8] for x in r['verification'].get('merge_commits') or ())}"}
                      for r in rows], LEDGER_CSV)


def diff_rows(l3042, l3043, released_lines=None):
    b42 = {ln["line_id"]: ln for ln in l3042}
    rel = {A30._key(ln): ln for ln in released_lines or ()}
    out = []
    for ln in l3043:
        o = b42.get(ln["line_id"])
        vs = "ADDED" if o is None else ("SAME" if A30.line_sha(o) == A30.line_sha(ln) else "CHANGED")
        r = rel.get(A30._key(ln)) if released_lines is not None else None
        vs29 = None if released_lines is None else ("NOT_IN_RELEASED" if r is None else
                                                    ("SAME_QUANTITY" if A30._qty(r) == A30._qty(ln) else
                                                     "QUANTITY_DIFFERS"))
        out.append({"line_id": ln["line_id"], "item_code": ln["item_code"], "floor": ln["location"].get("floor"),
                    "element_id": ln["location"].get("element_id"), "unit": ln["unit"], "vs_v3_0_42": vs,
                    "vs_released_v2_9": vs29, "v2_9": A302._q(A30._qty(r)) if r else "",
                    "v3_0_42": A302._q(A30._qty(o)) if o else "", "v3_0_43": A302._q(A30._qty(ln))})
    return out


def write(out, l3042, changes, log, released_lines=None, for_lead=()):
    """the V3_0_43_* files beside the V3_0_42_* files. -> (file names, identity, ledger)."""
    from pathlib import Path
    from engine.source import boq_line as BL
    out = Path(out)
    l3043, ident = integrate(l3042, changes, for_lead)
    rows = ledger_rows(changes, released_lines)
    diff = diff_rows(l3042, l3043, released_lines)
    named = {c["after"]["line_id"] for c in changes}
    stray = [d["line_id"] for d in diff if d["vs_v3_0_42"] in ("CHANGED", "ADDED") and d["line_id"] not in named]
    if stray:
        raise ValueError(f"{METHOD}: {len(stray)} line(s) changed outside the named changes")
    dsum = {}
    for d in diff:
        dsum.setdefault("vs_v3_0_42", {}).setdefault(d["vs_v3_0_42"], 0)
        dsum["vs_v3_0_42"][d["vs_v3_0_42"]] += 1
        if d["vs_released_v2_9"] is not None:
            dsum.setdefault("vs_released_v2_9", {}).setdefault(d["vs_released_v2_9"], 0)
            dsum["vs_released_v2_9"][d["vs_released_v2_9"]] += 1
    ident = dict(ident, diff=dsum)
    t42, t43 = A304.code_totals(l3042), A304.code_totals(l3043)
    moved = {k: {"v3_0_42": t42.get(k), "v3_0_43": t43.get(k)} for k in sorted(set(t42) | set(t43))
             if t42.get(k) != t43.get(k)}
    for k, v in moved.items():
        code = k.split("|")[0]
        if code in EW_CODES:
            n = v["v3_0_43"]
            if v["v3_0_42"] is not None or n["released"] or n["held_low"] or n["held_high"] or \
                    n["blocked_lines"] != n["lines"]:
                raise ValueError(f"{METHOD}: earthworks totals {k} carry a figure (held blank only)")
        elif code in RANGE_CODES:
            a, b = v["v3_0_42"], v["v3_0_43"]
            if a is None or b is None or any(a[x] != b[x] for x in ("lines", "released", "bounded_lines",
                                                                       "blocked_lines")):
                raise ValueError(f"{METHOD}: totals {k} moved beyond the held range")
        else:
            raise ValueError(f"{METHOD}: totals moved outside this version's codes: {k}")
    led = {"schema": LEDGER_SCHEMA, "method": METHOD, "extends": EXTENDS, "candidate": CANDIDATE,
           "base": A30.BASE_METHOD, "released": A30.RELEASED_METHOD, "released_default": False, "rows": rows,
           "waiting_pieces": WAITING, "integration_package": True}
    run = {"method": METHOD, "policy": POLICY_ID, "extends": EXTENDS, "candidate": CANDIDATE,
           "base_method": A30.BASE_METHOD, "released_method": A30.RELEASED_METHOD, "released_default": False,
           "rollback": ROLLBACK, "identity": ident, "pieces": PIECES, "piece_logs": [log],
           "totals_moved_by_code": moved, "waiting_pieces": WAITING}
    files = {"V3_0_43_BOQ_LINES.json": BL.dumps(l3043),
             "V3_0_43_BOQ_LINES.csv": A30._lines_csv(l3043),
             "V3_0_43_INTEGRATION_LEDGER.json": A30._j(led),
             "V3_0_43_INTEGRATION_LEDGER.csv": ledger_csv(rows),
             "V3_0_43_DIFF.csv": A305._csv(diff, DIFF_CSV),
             "V3_0_43_RUN.json": A30._j(run)}
    for name, text in files.items():
        (out / name).write_text(text, encoding="utf-8")
    return sorted(files), ident, led


def policy_record():
    return {"method": METHOD, "extends": EXTENDS, "pieces": sorted(PIECES), "inputs_schema": INPUTS_SCHEMA,
            "released_default": False, "rollback": ROLLBACK, "actions": list(ACTIONS)}


__all__ = ["METHOD", "PIECES", "WAITING", "DEFAULT_GUARD_CLASS", "INPUTS_SCHEMA", "EW_CODES", "load_inputs",
           "changes_for", "check_earthworks", "integrate", "ledger_rows", "diff_rows", "write", "InputsError"]
