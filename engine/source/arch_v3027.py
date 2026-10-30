"""ARCH_TAKEOFF_V3.0.27 (T-318): the SAME opt-in BOQ candidate as ARCH_TAKEOFF_V3.0 .. V3.0.26 (engine.source.arch_v30,
arch_v301 .. arch_v3026), extended with ONE piece, SLAB_BAR_END_SPLIT: the candidate's suspended-slab reinforcement
lines of the two bar-end populations (DEVELOPMENT / ANCHORAGE and TOP BARS OVER SUPPORTS, one line per panel and bar
direction, all BOUNDED_EXPOSURE kg since V3.0.5) are re-booked bar end by bar end from the Checker-merged support-class
ledgers: only drawn / printed bar parts are counted, an undrawn part stays HELD blank by name (owner 2026-10-29 21:22,
option B; 22:05: every structural note and typical detail read before an end is held, no anchorage, bend or hook
invented). Not a new method family and not the released default (owner management decision 2026-10-20 sections 2
and 5); rollback is running the released ARCH_TAKEOFF_V2.9.

The physical element (ERS 2026-10-22 s.2.1, s.3): ONE END of one slab bar where it meets the support at the panel edge.
The governing typical detail (ST p.15 TYP. SLAB ON BEAMS DETAIL) draws:

  continuous support  bottom bars: no development, no lap (50 % stop short, the rest run on, booked in the bottom line)
                      -> 0 m; top bars: 0.30 x max(L1, L2) from the face + the part over the band;
  edge beam           bottom bars: straight past the inner face to 40 mm of the outer face (w - 0.040), the curtailed
                      bar turns up (leg drawn, not dimensioned: HELD); top anchor: 0.25 L1 from the inner face, across
                      the edge beam [w - 0.040, w], hook-down leg HELD, dashed 'extend 50 % into adjacent slab where
                      possible' UNRESOLVED;
  step / irregular /  no detail draws a bar end there -> HELD (never 0, never a default).
  opening end

Per line (the records of the inputs; each line once):

  NA        DEVELOPMENT line whose every end is continuous: NOT_APPLICABLE_WITH_EVIDENCE in place (no development is
            drawn at a continuous support; the note-9 40 d .. 70 d starter-bar note is not a slab rule);
  RESTATE   a line with no valued end (development: no edge-beam end; top: every end held, or a (T&B) tank panel
            where p.15 note 3 governs): BLANK in place (BLOCKED_RFI), its held ends named;
  PARENT    a line with valued and held ends: BLANK in place, every held end class / leg / unresolved extension named,
            the part line id listed;
  PART      the valued ends of a PARENT as their own BOUNDED_EXPOSURE line: development = the drawn straight part
            (DRAWING-DERIVED length, count A .. B); top = the envelope of the two printed documents on the SAME valued
            ends: [min(plan note 2 reading i at count A, p.15 at count A), max(note 2 reading ii + crossing at count B,
            p.15 at count B)] (note 2 vs p.15 is a designer item, never chosen here; the p.15 reading carries the
            across-beam part F-T316-01 and the clear-span cap F-T316-02 of the merged ledger);
  REBASE    a top line whose every end is valued and nothing is held: the same envelope in place (no parent needed).

Refused (InputsError / ValueError, nothing written): a line the candidate does not carry, or whose 'before' range is
not the candidate's (stale ledger), or that is not a BOUNDED_EXPOSURE STR.REBAR slab line of the stated element,
component and direction; a record applied twice; an NA line with a valued part; a HELD / RESTATE line given a value;
a value for a leg / hook / extension (held is BLANK, never 0); a PART with no held item (it is a REBASE) or a REBASE
with held items; a part bound with low > high, a high <= 0 or a negative low; a note-9 / 40 d / 60 d / 70 d basis on
a development part; an unknown status or population; a unit other than kg. Every line outside the records is
byte-identical to V3.0.26 (asserted); inside a record only state, quantity, range, rfi, calculation and notes change.

Files: V3_0_27_BOQ_LINES.json / .csv, V3_0_27_INTEGRATION_LEDGER.json / .csv (per line: before V3.0.26, after,
released V2.9, evidence status, ends by class, held items, source task / merge / checker run), V3_0_27_DIFF.csv
(every line against V3.0.26 and the released V2.9), V3_0_27_RUN.json. Nothing here names a project, a sheet, a layer
or a coordinate: every value comes from the inputs.
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
from engine.source import arch_v3021 as A3021
from engine.source import arch_v3023 as A3023
from engine.source import arch_v3024 as A3024
from engine.source import arch_v3025 as A3025
from engine.source import arch_v3026 as A3026

DEFAULT_GUARD_CLASS = "TOOLING"          # T-212: re-books checker-merged ledgers; adds no default value
METHOD = "ARCH_TAKEOFF_V3.0.27"
EXTENDS = A3026.METHOD
CANDIDATE = A30.METHOD
POLICY_ID = "URBAN_BOQ_T318_ARCH_V3_0_27"
INPUTS_SCHEMA = "URBAN_V3027_INPUTS_V1"
LEDGER_SCHEMA = "URBAN_V3027_INTEGRATION_LEDGER_V1"
ROLLBACK = A30.ROLLBACK
InputsError = A3015.InputsError
_r = A3018._r
RULE_ID, RULE_VERSION = "R-T318-1", "T-318"
ITEM, UNIT = "STR.REBAR", "kg"
DEV, TOP = "DEVELOPMENT / ANCHORAGE", "TOP BARS OVER SUPPORTS"
COMPONENT = {DEV: "DEVELOPMENT / ANCHORAGE", TOP: "TOP BARS OVER SUPPORTS"}
DEV_STATUS = {"NOT_APPLICABLE_WITH_EVIDENCE": "NA", "HELD": "RESTATE", "BOUND_PART_WITH_HELD": "PARENT"}
TOP_STATUS = {"DRAWING_DERIVED_P15": "REBASE", "DRAWING_DERIVED_P15_PART_WITH_HELD": "PARENT",
              "DRAWING_DERIVED_P15_PART_WITH_HELD_LEGS": "PARENT", "HELD": "RESTATE",
              "UNRESOLVED_TB_PANEL": "RESTATE"}
FORBIDDEN_DEV_BASIS = ("note 9", "note-9", "40 d", "60 d", "70 d", "40d", "60d", "70d", "lap")
TOL = 1e-6
TOL_BEFORE = 0.0005                       # the candidate range is stored to 3 dp, the ledger reads it to 3 dp

PIECES = {
    "SLAB_BAR_END_SPLIT": {
        "module": "engine/source/arch_v3027.py (the suspended-slab DEVELOPMENT and TOP lines re-booked bar end by bar "
                  "end from the checker-merged support-class ledgers: drawn parts valued, undrawn ends BLANK by name)",
        "policy": "SLAB_BAR_END_SPLIT_V1", "rule_id": RULE_ID, "rule_version": RULE_VERSION,
        "owner_rules": ["owner 2026-10-29 21:22 option B (only drawn / printed bar parts are counted; an undrawn part "
                        "HELD blank unless physically certain from the drawings)",
                        "owner 2026-10-29 22:05 (read ST p.8 notes and p.15 typical slab details before an end is "
                        "unresolved; never invent an anchorage, bend or hook)",
                        "OWNER_RULE_REBAR_2026-10-24 (kg internal, t at the export boundary; note 9 is a starter-bar "
                        "anchorage note, not a general slab rule; owner 40 d / 60 d never where it conflicts)",
                        "owner 2026-10-24 10:56 (held BLANK in the BOQ)", "UP-QTY-STATUS-001 (held never 0)",
                        "WORKFLOW_CONTROLS 2026-10-21 s.4 / s.5; ERS 2026-10-22 s.2 - s.4"],
        "owner_manual_method": "no owner manual method for slab bar ends or top-bar extents (owner rebar decisions: t at "
                               "export; the lap proposal is not approved and not used; Q-71 not extended to slabs); "
                               "the freelancer books one lump 5,400 kg for all slabs with no bar population",
        "drawing_method": "every bar end classified by the support it meets from the drawn slab faces (continuous / "
                          "edge beam with its drawn width / step / irregular / opening); p.15 lengths applied only to "
                          "the classes p.15 draws (development: continuous 0, edge beam w - 0.040; top: 0.30 x max(L1, "
                          "L2) from the face + band, 0.25 L1 + across the edge beam [w - 0.040, w], never past the "
                          "clear span); legs, hooks, the 50 % extension and the undrawn classes HELD"},
}
WAITING = dict(A3026.WAITING)
WAITING.update({
    "SLAB_END_LEGS": "the up-turn leg of the curtailed bottom bar and the hook-down leg of the top anchor at edge beams "
                     "(drawn on p.15, not dimensioned): designer item, BLANK by name",
    "SLAB_END_UNDRAWN_CLASSES": "bar ends at sunken-panel level steps (D-41), composite / irregular supports and opening "
                                "edges: no detail draws them, BLANK by name",
    "SLAB_TOP_EXTENT_DOCUMENTS": "top-bar extent: plan note 2 'one third of the span' vs p.15 (0.30 max L / 0.25 L1): "
                                 "two printed documents, carried as a bound until the designer answers",
    "SLAB_TOP_EXTENSION_50PCT": "p.15 dashed 'extend 50 % of top reinf. into adjacent slab where possible' at edge beams "
                                "with concrete beyond: UNRESOLVED, BLANK",
    "SLAB_TB_PANELS": "the (T&B) tank panels' top lines: p.15 note 3 'where top reinf. differs between adjacent spans "
                      "use larger reinf.' (F-T316-03): BLANK",
})


# ================================================================================================ inputs
def _range(v, where, allow_zero_low=True):
    if not isinstance(v, dict):
        raise InputsError(f"{where}: a range {{low, high}} is required")
    lo, hi = v.get("low"), v.get("high")
    if not isinstance(lo, (int, float)) or not isinstance(hi, (int, float)):
        raise InputsError(f"{where}: low / high must be numbers (held is BLANK, not a figure)")
    if lo < -TOL or (lo <= TOL and not allow_zero_low):
        raise InputsError(f"{where}: low {lo} kg")
    if hi <= TOL:
        raise InputsError(f"{where}: high {hi} kg: a valued part is > 0 (a 0 part is NOT_APPLICABLE or HELD)")
    if lo > hi + TOL:
        raise InputsError(f"{where}: low {lo} > high {hi}")
    return {"low": float(lo), "high": float(hi)}


def held_items(rec):
    """the named held / unresolved items of one line (never a figure)."""
    out = []
    if rec["population"] == DEV:
        for part in str(rec.get("held_items") or "").split(" | "):
            if part.strip():
                out.append({"kind": "UPTURN_LEG" if part.startswith("UPTURN_LEG") else "HELD_ENDS",
                            "item": part.strip()})
    else:
        for cls, (a, b) in sorted((rec.get("held_ends") or {}).items()):
            out.append({"kind": "HELD_ENDS", "item": f"{cls} ends {a}..{b} (no detail draws a top bar there)"})
        for what, (a, b) in sorted((rec.get("unresolved_ends") or {}).items()):
            out.append({"kind": "UNRESOLVED", "item": f"{what} at {a}..{b} edge-beam ends (p.15 dashed, no length)"})
        if rec.get("hook_legs_held"):
            a, b = rec["hook_legs_held"]
            out.append({"kind": "HOOK_DOWN_LEG", "item": f"hook-down leg of the top anchor at {a}..{b} edge-beam ends "
                                                         f"(drawn, not dimensioned)"})
        if rec["status"] == "UNRESOLVED_TB_PANEL":
            out.append({"kind": "TB_PANEL", "item": "(T&B) tank panel: p.15 note 3 'use larger reinf.' where top "
                                                    "reinforcement differs (F-T316-03); note-2 bar over a T&B mesh open"})
    return out


def load_inputs(doc, project_id=None):
    """URBAN_V3027_INPUTS_V1 -> the validated doc (records keyed by line id, each with its action)."""
    if not doc:
        return None
    if doc.get("schema") != INPUTS_SCHEMA:
        raise InputsError(f"project inputs: schema must be {INPUTS_SCHEMA}")
    if project_id and doc.get("project_id") not in (None, project_id):
        raise InputsError(f"project inputs are for {doc.get('project_id')!r}, the run is {project_id!r}")
    if doc.get("unit") != UNIT:
        raise InputsError(f"inputs unit {doc.get('unit')!r}: slab steel is booked in kg (t only at export)")
    srcs = {}
    for s in doc.get("sources") or ():
        for k in ("task", "file", "sha256", "merge_commit", "checker_run"):
            if not s.get(k):
                raise InputsError(f"source {s}: {k} missing (a merged, checker-verified ledger only)")
        srcs.setdefault(s["task"], s)
    out, seen = [], set()
    for rec in doc.get("lines") or ():
        lid = rec.get("line_id")
        where = f"line {lid}"
        if lid in seen:
            raise InputsError(f"{where}: twice in the inputs (each line once)")
        seen.add(lid)
        pop = rec.get("population")
        table = DEV_STATUS if pop == DEV else TOP_STATUS if pop == TOP else None
        if table is None:
            raise InputsError(f"{where}: population {pop!r}")
        st = rec.get("status")
        if st not in table:
            raise InputsError(f"{where}: status {st!r} is not a {pop} status")
        if rec.get("source_task") not in srcs:
            raise InputsError(f"{where}: no merged source for {rec.get('source_task')!r}")
        for k in ("leg_kg", "hook_kg", "extension_kg", "held_kg"):
            if rec.get(k) not in (None, ""):
                raise InputsError(f"{where}: {k} = {rec[k]}: legs, hooks, extensions and held ends carry no figure")
        r = dict(rec, action=table[st])
        r["before"] = _range(rec.get("before"), f"{where} before")
        held = held_items(rec)
        if r["action"] == "NA":
            if rec.get("valued") or held:
                raise InputsError(f"{where}: an all-continuous development line carries no part and no held item")
        elif r["action"] == "RESTATE":
            if rec.get("valued") or rec.get("p15_valued") or rec.get("note2_valued"):
                raise InputsError(f"{where}: a HELD line is given a value (held is BLANK, never a figure)")
            if not held:
                raise InputsError(f"{where}: a HELD line names no held item")
        else:
            if pop == DEV:
                v = rec.get("valued") or {}
                basis = str(v.get("basis") or "").lower()
                if any(x in basis for x in FORBIDDEN_DEV_BASIS):
                    raise InputsError(f"{where}: development part on a note-9 / lap basis ({v.get('basis')!r}): only "
                                      f"the p.15 drawn length is a slab development basis")
                r["part"] = dict(_range(v, f"{where} valued"), basis=v.get("basis"))
            else:
                n2 = _range(rec.get("note2_valued"), f"{where} note-2 on the valued ends")
                p15 = _range(rec.get("p15_valued"), f"{where} p.15 on the valued ends")
                r["part"] = {"low": min(n2["low"], p15["low"]), "high": max(n2["high"], p15["high"]),
                             "note2": n2, "p15": p15,
                             "basis": "envelope of plan note 2 (i at A .. ii + crossing at B) and p.15 (across-beam "
                                      "part and clear-span cap included) on the same valued ends"}
            if r["action"] == "PARENT" and not held:
                raise InputsError(f"{where}: a part with no held item is a REBASE, not a split")
            if r["action"] == "REBASE" and held:
                raise InputsError(f"{where}: a REBASE line has held items {held[:2]} (it must be split)")
        r["held"] = held
        out.append(r)
    return dict(doc, lines=out, _sources=srcs)


# ================================================================================================ lines
def _slug(s):
    return A3018._slug(s)


def part_element_id(parent_element_id):
    return f"{parent_element_id}#SLAB_BAR_ENDS:VALUED"


def _rec(src, **kw):
    return dict({"policy": PIECES["SLAB_BAR_END_SPLIT"]["policy"], "task": src["task"], "ledger": src["file"],
                 "ledger_sha256": src["sha256"], "merge_commit": src["merge_commit"], "checker_run": src["checker_run"],
                 "rule_id": RULE_ID, "rule_version": RULE_VERSION, "release_status": "NOT RELEASED"}, **kw)


def _ends(rec):
    return {"A": rec.get("ends_A"), "B": rec.get("ends_B")}


def _held_text(held):
    return "; ".join(h["item"] for h in held)


def _evidence(rec):
    if rec["population"] == DEV:
        return "DRAWING-CONFIRMED (drawn straight length; count A .. B BOUND; legs HELD)"
    return "DRAWING-CONFIRMED (BOUND between two printed documents: plan note 2 vs p.15; designer item)"


def part_line(parent, rec, src):
    """the valued ends of a split line: the parent's identity / documents / item, its own element id and range."""
    from engine.source import boq_line as BL
    pr, loc, p = parent["project"], parent["location"], rec["part"]
    eid = part_element_id(loc.get("element_id"))
    lrec = _rec(src, action="PART", parent_line_id=parent["line_id"], population=rec["population"],
                element=rec["element"], direction=rec["direction"], status=rec["status"],
                evidence_status=_evidence(rec), ends=_ends(rec), range={"low": _r(p["low"]), "high": _r(p["high"])},
                readings={k: p[k] for k in ("note2", "p15") if k in p}, basis=p["basis"])
    if rec["population"] == DEV:
        formula = (f"valued ends of {rec['element']} {rec['direction']} development: p.15 straight part w - 0.040 m at "
                   f"the edge-beam ends, count A .. B = {_r(p['low'], 3)} .. {_r(p['high'], 3)} kg (legs and the "
                   f"undrawn ends on {parent['line_id']}, BLANK)")
    else:
        formula = (f"valued ends of {rec['element']} {rec['direction']} top bars: note 2 {_r(p['note2']['low'], 3)} .. "
                   f"{_r(p['note2']['high'], 3)} kg | p.15 {_r(p['p15']['low'], 3)} .. {_r(p['p15']['high'], 3)} kg "
                   f"-> bound {_r(p['low'], 3)} .. {_r(p['high'], 3)} kg (held ends on {parent['line_id']}, BLANK)")
    ln = BL.make_line(project_id=pr["project_id"], revision_set_sha256=pr["revision_set_sha256"],
                      item_code=parent["item_code"], unit=parent["unit"], evidence_state="BOUNDED_EXPOSURE",
                      measured_net=None, element_id=eid, floor=loc.get("floor"), room_id=loc.get("room_id"),
                      room_name_en=loc.get("room_name_en"), room_name_ar=loc.get("room_name_ar"),
                      physical_element=parent.get("physical_element"),
                      bounded_range={"basis": p["basis"][:200], "low": _r(p["low"], 3), "high": _r(p["high"], 3)},
                      formula=formula[:700], inputs={"slab_bar_end_split_v3027": lrec},
                      documents=copy.deepcopy(parent["source"]["documents"]),
                      geometry_source=parent["source"]["geometry_source"],
                      geometry_confidence=parent["source"].get("geometry_confidence") or "INFERRED_CANDIDATE",
                      rule_id=RULE_ID, rule_version=RULE_VERSION, material_state=parent["material_state"],
                      rfi={"question": (f"bound, not a measured net: {p['basis']}")[:900], "unlocks": eid},
                      notes=(f"{METHOD}: valued ends of held line {parent['line_id']} ({src['task']} MERGED "
                             f"{src['merge_commit'][:8]}): {_evidence(rec)}")[:600],
                      subtrade=parent.get("subtrade"), item_en=parent.get("item_en"), item_ar=parent.get("item_ar"),
                      trade=parent.get("trade"))
    ln["project"] = copy.deepcopy(pr)
    return BL.validate(ln), lrec


def replaced_line(parent, rec, src, part_id=None):
    """the line in place: NA (no development drawn), BLANK (held ends named) or REBASE (the envelope)."""
    from engine.source import boq_line as BL
    ln = copy.deepcopy(parent)
    act = rec["action"]
    base = _rec(src, action=act, before=A3018._before_rec(parent), population=rec["population"],
                element=rec["element"], direction=rec["direction"], status=rec["status"], ends=_ends(rec),
                still_held=rec["held"], part=part_id)
    if act == "NA":
        ln["evidence_state"] = "NOT_APPLICABLE_WITH_EVIDENCE"
        ln["measured_net"] = None
        ln["bounded_range"] = None
        ln["rfi"] = None
        ln["calculation"]["formula"] = (f"every bar end of {rec['element']} {rec['direction']} meets a continuous "
                                        f"support (A {rec['ends_A']}, B {rec['ends_B']}): p.15 draws no development "
                                        f"there -> no quantity (was note-9 {rec['before']['low']} .. "
                                        f"{rec['before']['high']} kg, a starter-bar note)")[:600]
        A305._note(ln, f"{METHOD}: NOT_APPLICABLE_WITH_EVIDENCE: p.15 TYP. SLAB ON BEAMS DETAIL draws no development "
                       f"at a continuous support ({src['task']} MERGED {src['merge_commit'][:8]})")
    elif act == "REBASE":
        p = rec["part"]
        ln["evidence_state"] = "BOUNDED_EXPOSURE"
        ln["measured_net"] = None
        ln["bounded_range"] = {"basis": p["basis"][:200], "low": _r(p["low"], 3), "high": _r(p["high"], 3)}
        ln["rfi"] = {"question": f"bound, not a measured net: {p['basis']}"[:900],
                     "unlocks": ln["location"].get("element_id")}
        ln["calculation"]["formula"] = (f"every end valued: note 2 {_r(p['note2']['low'], 3)} .. "
                                        f"{_r(p['note2']['high'], 3)} kg | p.15 {_r(p['p15']['low'], 3)} .. "
                                        f"{_r(p['p15']['high'], 3)} kg -> bound {_r(p['low'], 3)} .. "
                                        f"{_r(p['high'], 3)} kg")[:600]
        base["range"] = {"low": _r(p["low"]), "high": _r(p["high"])}
        base["readings"] = {"note2": p["note2"], "p15": p["p15"]}
        A305._note(ln, f"{METHOD}: top bars re-based end by end ({src['task']} MERGED {src['merge_commit'][:8]}); "
                       f"note 2 vs p.15 carried as a bound")
    else:  # PARENT / RESTATE: blank, held items named
        q = (f"HELD bar ends (blank, never 0; no leg, hook or anchorage invented): {_held_text(rec['held'])}")
        if len(q) > 900:
            raise ValueError(f"{METHOD}: the held list of {parent['line_id']} does not fit the RFI question")
        ln["evidence_state"] = "BLOCKED_RFI"
        ln["measured_net"] = None
        ln["bounded_range"] = None
        ln["rfi"] = {"question": q, "unlocks": ln["location"].get("element_id")}
        ln["calculation"]["formula"] = (f"HELD remainder (blank in the BOQ, never 0): {len(rec['held'])} named item(s)"
                                        + (f" | valued ends carried on {part_id}" if part_id else
                                           " | no valued end in this line"))[:600]
        A305._note(ln, f"{METHOD}: bar ends re-booked by support class ({src['task']} MERGED "
                       f"{src['merge_commit'][:8]}); " + ("its valued ends are their own line; " if part_id else "")
                   + "blank in the BOQ, never 0")
    ln["calculation"]["inputs"] = dict(ln["calculation"].get("inputs") or {}, slab_bar_end_split_v3027=base)
    return BL.validate(ln)


def _assert_before(b, rec):
    if b is None:
        raise InputsError(f"line {rec['line_id']}: the candidate does not carry this line (stale ledger)")
    inp = (b.get("calculation") or {}).get("inputs") or {}
    if inp.get("slab_bar_end_split_v3027"):
        raise InputsError(f"line {rec['line_id']}: already re-booked (applied once)")
    if (b["item_code"], b["unit"]) != (ITEM, UNIT):
        raise InputsError(f"line {rec['line_id']}: {b['item_code']} {b['unit']} is not a slab steel kg line")
    if (inp.get("element"), inp.get("component"), str(inp.get("part") or "").lower()) != \
            (rec["element"], COMPONENT[rec["population"]], str(rec["direction"]).lower()):
        raise InputsError(f"line {rec['line_id']}: element / component / direction is not the line's "
                          f"({inp.get('element')} {inp.get('component')} {inp.get('part')})")
    br = b.get("bounded_range") or {}
    if b["evidence_state"] != "BOUNDED_EXPOSURE" or b.get("measured_net") is not None or \
            abs((br.get("low") or 0) - rec["before"]["low"]) > TOL_BEFORE or \
            abs((br.get("high") or 0) - rec["before"]["high"]) > TOL_BEFORE:
        raise InputsError(f"line {rec['line_id']}: the candidate line is {b['evidence_state']} {br.get('low')} .. "
                          f"{br.get('high')}, not the {rec['before']} the ledger was made on (stale ledger: refused)")


def changes_for(doc, l3026):
    """-> (changes, log)."""
    if not doc:
        return [], {"piece": "SLAB_BAR_END_SPLIT", "state": "NO_PROJECT_INPUT"}
    by = {ln["line_id"]: ln for ln in l3026}
    seen_ids = set(by)
    changes = []
    log = {"piece": "SLAB_BAR_END_SPLIT", "state": "RUN", "sources": doc["sources"], "by_action": {},
           "kg": {}, "lines": {}}
    for rec in doc["lines"]:
        b = by.get(rec["line_id"])
        _assert_before(b, rec)
        src = doc["_sources"][rec["source_task"]]
        ver = {"task": src["task"], "merge_commit": src["merge_commit"], "verifier_run": src["checker_run"],
               "ledger": src["file"], "ledger_sha256": src["sha256"]}
        pid, pl = None, None
        if rec["action"] == "PARENT":
            pl, _lrec = part_line(b, rec, src)
            if pl["line_id"] in seen_ids:
                raise ValueError(f"{METHOD}: the part of {b['line_id']} repeats a line id")
            seen_ids.add(pl["line_id"])
            pid = pl["line_id"]
        after = replaced_line(b, rec, src, pid)
        ev = {"NA": "NOT_APPLICABLE_WITH_EVIDENCE (p.15)", "RESTATE": "HELD", "PARENT": "HELD (remainder)",
              "REBASE": _evidence(rec)}[rec["action"]]
        changes.append(A305._change("SLAB_BAR_END_SPLIT", "REPLACE", b, after, drawing_reference=src["file"],
                                    held=[{"what": f"{ITEM} {rec['element']} {rec['direction']} {rec['population']}",
                                           "why": f"{h['kind']}: {h['item']}"[:300], "range": None, "scenario": None}
                                          for h in rec["held"]],
                                    downstream=[], verification=ver, evidence_status=ev,
                                    codes=["SLAB_BAR_END_SPLIT", rec["action"]], group=rec["population"]))
        if pl is not None:
            changes.append(A305._change("SLAB_BAR_END_SPLIT", "ADD", None, pl, drawing_reference=src["file"],
                                        held=[], downstream=[], verification=ver, evidence_status=_evidence(rec),
                                        codes=["SLAB_BAR_END_SPLIT", "PART"], group=rec["population"],
                                        parent_line_id=b["line_id"]))
        k = f"{rec['population']} {rec['action']}"
        log["by_action"][k] = log["by_action"].get(k, 0) + 1
        g = log["kg"].setdefault(rec["population"], {"before_low": 0.0, "before_high": 0.0, "valued_low": 0.0,
                                                     "valued_high": 0.0, "held_lines": 0, "na_lines": 0})
        g["before_low"] = _r(g["before_low"] + rec["before"]["low"])
        g["before_high"] = _r(g["before_high"] + rec["before"]["high"])
        if rec.get("part"):
            g["valued_low"] = _r(g["valued_low"] + _r(rec["part"]["low"], 3))
            g["valued_high"] = _r(g["valued_high"] + _r(rec["part"]["high"], 3))
        g["held_lines"] += rec["action"] in ("PARENT", "RESTATE")
        g["na_lines"] += rec["action"] == "NA"
        log["lines"][rec["line_id"]] = {"action": rec["action"], "part_line_id": pid, "held": len(rec["held"])}
    return changes, log


# ================================================================================================ integrate / write
def check_slab_ends(lines):
    """on finished lines: every part names a blank parent that names it; a part is BOUNDED with 0 <= low <= high,
    high > 0; parents / restated lines carry no figure; NA lines carry no figure and a reason. -> summary."""
    by = {ln["line_id"]: ln for ln in lines}
    out = {"parts": 0, "parents": 0, "restated": 0, "not_applicable": 0, "rebased": 0, "valued": {}}
    for ln in lines:
        rec = ((ln.get("calculation") or {}).get("inputs") or {}).get("slab_bar_end_split_v3027") or {}
        act = rec.get("action")
        if not act:
            continue
        if act in ("PARENT", "RESTATE"):
            out["parents" if act == "PARENT" else "restated"] += 1
            if ln["evidence_state"] != "BLOCKED_RFI" or ln.get("measured_net") is not None or ln.get("bounded_range"):
                raise ValueError(f"{METHOD}: held line {ln['line_id']} carries a figure (held is BLANK)")
            if act == "PARENT" and rec.get("part") not in by:
                raise ValueError(f"{METHOD}: parent {ln['line_id']} names a part the run does not carry")
            continue
        if act == "NA":
            out["not_applicable"] += 1
            if ln["evidence_state"] != "NOT_APPLICABLE_WITH_EVIDENCE" or ln.get("measured_net") is not None or \
                    ln.get("bounded_range") or not ln.get("notes"):
                raise ValueError(f"{METHOD}: NA line {ln['line_id']} carries a figure or no reason")
            continue
        br = ln.get("bounded_range") or {}
        if ln["evidence_state"] != "BOUNDED_EXPOSURE" or ln.get("measured_net") is not None or \
                br.get("low") is None or br["low"] < -TOL or br["high"] <= TOL or br["low"] > br["high"] + TOL:
            raise ValueError(f"{METHOD}: valued line {ln['line_id']} is {ln['evidence_state']} {br}")
        if act == "PART":
            out["parts"] += 1
            par = by.get(rec.get("parent_line_id"))
            prec = (((par or {}).get("calculation") or {}).get("inputs") or {}).get("slab_bar_end_split_v3027") or {}
            if par is None or prec.get("part") != ln["line_id"]:
                raise ValueError(f"{METHOD}: part {ln['line_id']}: its parent does not name it")
            if par["evidence_state"] != "BLOCKED_RFI" or par.get("bounded_range") or par.get("measured_net") is not None:
                raise ValueError(f"{METHOD}: part {ln['line_id']} beside a parent with a figure (double count)")
        elif act == "REBASE":
            out["rebased"] += 1
        else:
            raise ValueError(f"{METHOD}: action {act}")
        k = rec.get("population")
        v = out["valued"].setdefault(k, {"low": 0.0, "high": 0.0, "lines": 0})
        v["low"] = _r(v["low"] + br["low"])
        v["high"] = _r(v["high"] + br["high"])
        v["lines"] += 1
    out["valued"] = dict(sorted(out["valued"].items()))
    return out


def integrate(l3026, changes, for_lead=()):
    """-> (V3.0.27 lines, identity). Every line outside the V3.0.27 rows is byte-identical to the V3.0.26 line."""
    from engine.source import boq_line as BL
    sid = {ln["line_id"] for ln in l3026}
    rep, adds = {}, []
    for c in changes:
        if c["piece"] != "SLAB_BAR_END_SPLIT":
            raise ValueError(f"{METHOD}: piece {c['piece']} (this version only re-books the slab bar-end lines)")
        if c["action"] == "REPLACE":
            lid = c["before"]["line_id"]
            if lid in rep or lid not in sid or c["after"]["line_id"] != lid:
                raise ValueError(f"{METHOD}: line {lid}: changed twice, not in V3.0.26, or its id changed")
            rep[lid] = c["after"]
        elif c["action"] == "ADD":
            if c["after"]["line_id"] in sid or (c["after"]["item_code"], c["after"]["unit"]) != (ITEM, UNIT):
                raise ValueError(f"{METHOD}: an added line repeats a V3.0.26 line id or is not a slab steel kg line")
            adds.append(c["after"])
        else:
            raise ValueError(f"{METHOD}: action {c['action']}")
    out = [rep.get(ln["line_id"], ln) for ln in l3026] + adds
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
    outdoor = A3025.check_outdoor_family(out)
    blk = A3026.check_blockwork(out)
    ends = check_slab_ends(out)
    pids = {(ln["project"]["project_id"], ln["project"]["revision_set_sha256"]) for ln in out}
    if len(pids) != 1:
        raise ValueError(f"{METHOD}: {len(pids)} project identities in the lines (one project, one revision set)")
    by26 = {ln["line_id"]: ln for ln in l3026}
    touched = set(rep) | {a["line_id"] for a in adds}
    outside = [ln for ln in out if ln["line_id"] not in touched]
    bad = [ln["line_id"] for ln in outside if A30.line_sha(by26[ln["line_id"]]) != A30.line_sha(ln)]
    if bad or len(outside) + len(rep) != len(l3026):
        raise ValueError(f"{METHOD}: {len(bad)} line(s) outside the V3.0.27 rows differ from {EXTENDS}")
    for lid, ln in rep.items():   # inside a row only quantity, state, basis and notes change
        a, b = copy.deepcopy(by26[lid]), copy.deepcopy(ln)
        for x in (a, b):
            for k in ("evidence_state", "measured_net", "bounded_range", "rfi", "notes"):
                x.pop(k, None)
            x["calculation"] = None
        if json.dumps(a, sort_keys=True) != json.dumps(b, sort_keys=True):
            raise ValueError(f"{METHOD}: line {lid} changed outside quantity / state / basis")
    ident = {"v3_0_26_lines": len(l3026), "v3_0_27_lines": len(out), "v3_0_27_rows": len(changes),
             "replaced": len(rep), "added": len(adds), "outside_rows": len(outside),
             "outside_rows_identical_to_v3_0_26": len(outside), "slab_bar_ends": ends, "blockwork": blk,
             "outdoor_family": outdoor, "parapet_family": par, "wall_tile_family": tile, "line_state": state,
             "outside_rows_sha256": hashlib.sha256("".join(A30.line_sha(x) for x in outside).encode()).hexdigest()}
    return out, ident


def ledger_rows(changes, released_lines=None):
    rel = {A30._key(ln): ln for ln in released_lines or ()}
    rows = []
    for c in changes:
        ref = c["after"]
        rec = ref["calculation"]["inputs"]["slab_bar_end_split_v3027"]
        b29 = None
        if released_lines is not None:
            b29 = A30._qty(rel[A30._key(ref)]) if A30._key(ref) in rel else dict(A30._qty(None),
                                                                                 state="NOT_IN_RELEASED")
        loc = ref.get("location") or {}
        rows.append({"version": METHOD, "action": rec["action"], "line_id": ref["line_id"],
                     "parent_line_id": rec.get("parent_line_id"), "part_line_id": rec.get("part")
                     if rec["action"] != "PART" else None, "item_code": ref["item_code"],
                     "floor": loc.get("floor"), "element_id": loc.get("element_id"), "unit": ref["unit"],
                     "population": rec.get("population"), "element": rec.get("element"),
                     "direction": rec.get("direction"), "ledger_status": rec.get("status"), "ends": rec.get("ends"),
                     "before_released_v2_9": b29,
                     "before_v3_0_26": (A30._qty(c["before"]) if c["before"] is not None else
                                        dict(A30._qty(None), state="NOT_IN_V3_0_26")),
                     "after_v3_0_27": A30._qty(ref), "evidence_status": c.get("evidence_status"),
                     "readings": rec.get("readings"), "still_held": rec.get("still_held"),
                     "release_status": "NOT RELEASED",
                     "owner_manual_method": PIECES["SLAB_BAR_END_SPLIT"]["owner_manual_method"],
                     "drawing_derived_method": PIECES["SLAB_BAR_END_SPLIT"]["drawing_method"],
                     "verification": c.get("verification") or {}, "rollback": ROLLBACK})
    return rows


LEDGER_CSV = ("version", "action", "line_id", "parent_line_id", "part_line_id", "item_code", "floor", "element",
              "direction", "population", "ledger_status", "unit", "v2_9", "v3_0_26", "v3_0_27", "evidence_status",
              "ends_A", "ends_B", "held", "verification")
DIFF_CSV = ("line_id", "item_code", "floor", "element_id", "unit", "vs_v3_0_26", "vs_released_v2_9", "v2_9",
            "v3_0_26", "v3_0_27")


def _fmt_q(q):
    return A302._q(q) if q else ""


def ledger_csv(rows):
    return A305._csv([{"version": r["version"], "action": r["action"], "line_id": r["line_id"],
                       "parent_line_id": r["parent_line_id"] or "", "part_line_id": r["part_line_id"] or "",
                       "item_code": r["item_code"], "floor": r["floor"], "element": r["element"],
                       "direction": r["direction"], "population": r["population"],
                       "ledger_status": r["ledger_status"], "unit": r["unit"],
                       "v2_9": _fmt_q(r["before_released_v2_9"]), "v3_0_26": _fmt_q(r["before_v3_0_26"]),
                       "v3_0_27": _fmt_q(r["after_v3_0_27"]), "evidence_status": r["evidence_status"],
                       "ends_A": (r["ends"] or {}).get("A") or "", "ends_B": (r["ends"] or {}).get("B") or "",
                       "held": "; ".join(f"{h['kind']}: {h['item']}" for h in r["still_held"] or ())[:900],
                       "verification": f"{r['verification'].get('task')} {r['verification'].get('merge_commit') or ''}"
                                       .strip()} for r in rows], LEDGER_CSV)


def diff_rows(l3026, l3027, released_lines=None):
    b26 = {ln["line_id"]: ln for ln in l3026}
    rel = {A30._key(ln): ln for ln in released_lines or ()}
    out = []
    for ln in l3027:
        o = b26.get(ln["line_id"])
        vs = "ADDED" if o is None else ("SAME" if A30.line_sha(o) == A30.line_sha(ln) else
                                        ("CHANGED" if A30._qty(o) != A30._qty(ln) else "CHANGED_TEXT_ONLY"))
        r = rel.get(A30._key(ln)) if released_lines is not None else None
        vs29 = None if released_lines is None else ("NOT_IN_RELEASED" if r is None else
                                                    ("SAME_QUANTITY" if A30._qty(r) == A30._qty(ln) else
                                                     "QUANTITY_DIFFERS"))
        out.append({"line_id": ln["line_id"], "item_code": ln["item_code"], "floor": ln["location"].get("floor"),
                    "element_id": ln["location"].get("element_id"), "unit": ln["unit"], "vs_v3_0_26": vs,
                    "vs_released_v2_9": vs29, "v2_9": A302._q(A30._qty(r)) if r else "",
                    "v3_0_26": A302._q(A30._qty(o)) if o else "", "v3_0_27": A302._q(A30._qty(ln))})
    return out


def write(out, l3026, changes, log, doc, released_lines=None, for_lead=()):
    """the V3_0_27_* files beside the V3_0_26_* files. -> (file names, identity, ledger)."""
    from pathlib import Path
    from engine.source import boq_line as BL
    out = Path(out)
    l3027, ident = integrate(l3026, changes, for_lead)
    rows = ledger_rows(changes, released_lines)
    diff = diff_rows(l3026, l3027, released_lines)
    dsum = {}
    for d in diff:
        dsum.setdefault("vs_v3_0_26", {}).setdefault(d["vs_v3_0_26"], 0)
        dsum["vs_v3_0_26"][d["vs_v3_0_26"]] += 1
        if d["vs_released_v2_9"] is not None:
            dsum.setdefault("vs_released_v2_9", {}).setdefault(d["vs_released_v2_9"], 0)
            dsum["vs_released_v2_9"][d["vs_released_v2_9"]] += 1
    ident = dict(ident, diff=dsum)
    t26, t27 = A304.code_totals(l3026), A304.code_totals(l3027)
    moved = {k: {"v3_0_26": t26.get(k), "v3_0_27": t27.get(k)} for k in sorted(set(t26) | set(t27))
             if t26.get(k) != t27.get(k)}
    if any(k != f"{ITEM}|{UNIT}" for k in moved):
        raise ValueError(f"{METHOD}: totals moved outside {ITEM} {UNIT}: {sorted(moved)[:5]}")
    led = {"schema": LEDGER_SCHEMA, "method": METHOD, "extends": EXTENDS, "candidate": CANDIDATE,
           "base": A30.BASE_METHOD, "released": A30.RELEASED_METHOD, "released_default": False, "rows": rows,
           "waiting_pieces": WAITING, "integration_package": True}
    run = {"method": METHOD, "policy": POLICY_ID, "extends": EXTENDS, "candidate": CANDIDATE,
           "base_method": A30.BASE_METHOD, "released_method": A30.RELEASED_METHOD, "released_default": False,
           "rollback": ROLLBACK, "identity": ident, "pieces": PIECES, "piece_logs": [log],
           "totals_moved_by_code": moved, "waiting_pieces": WAITING}
    files = {"V3_0_27_BOQ_LINES.json": BL.dumps(l3027),
             "V3_0_27_BOQ_LINES.csv": A30._lines_csv(l3027),
             "V3_0_27_INTEGRATION_LEDGER.json": A30._j(led),
             "V3_0_27_INTEGRATION_LEDGER.csv": ledger_csv(rows),
             "V3_0_27_DIFF.csv": A305._csv(diff, DIFF_CSV),
             "V3_0_27_RUN.json": A30._j(run)}
    for name, text in files.items():
        (out / name).write_text(text, encoding="utf-8")
    return sorted(files), ident, led


def policy_record():
    return {"method": METHOD, "extends": EXTENDS, "pieces": sorted(PIECES), "inputs_schema": INPUTS_SCHEMA,
            "released_default": False, "rollback": ROLLBACK, "items": [ITEM]}


__all__ = ["METHOD", "PIECES", "WAITING", "DEFAULT_GUARD_CLASS", "INPUTS_SCHEMA", "load_inputs", "held_items",
           "part_line", "replaced_line", "changes_for", "check_slab_ends", "integrate", "ledger_rows", "diff_rows",
           "write", "InputsError"]
