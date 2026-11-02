"""ARCH_TAKEOFF_V3.0.42 (T-442): the SAME opt-in BOQ candidate as ARCH_TAKEOFF_V3.0 .. V3.0.41 (engine.source.arch_v30,
arch_v301 .. arch_v3041), extended with the Checker-verified GROUND-SLAB PANELS the candidate left out and two CAUSE-TEXT
corrections, wired in ONE step so that no m3 is counted twice:

  GS_CELL_VALUE   a held slab-on-grade cell whose panels a Checker re-measured (closed on drawn ground-beam faces, the
                  printed slab thickness T) is VALUED at sum(panels) x T; the parts of the engine's cell that are not
                  slab (a pit shaft whose floor is the raft top, a pit ring that is the pit wall) are named beside with
                  their owner line, never valued here. The cell's older held record is kept whole (superseded, by name).
  GS_PANEL_ADD    a slab-on-grade panel the engine dropped as a 'stair zone' (a flight drawn HIDDEN over a panel closed
                  by band faces, no void / pit / base drawn: R-T436-1) gets ONE new ground-slab line = panel x T; the
                  engine's exclusion reason for the cell is retired by name (the ledger carries it).
  CAUSE_TEXT      a held / ranged line whose cause text cites the wrong designer item gets the right one; its state,
                  quantity, range and rfi stay byte-identical (only the formula / notes / record text change).

R-T442-1 (every villa; integrates R-T436-1, R-T444-1 .. 7): (a) a valued slab cell = sum of its re-measured panels x the
printed T, every non-slab part of the cell named beside with its owner, none of them valued here (no pit floor over a
raft, no ring under two owners); (b) a slab panel is never dropped because a flight is drawn hidden over it; (c) a panel
line is added once: its cell carries no ground-slab line already, its panel is in no other cell's panel list; (d) a
cause-text change moves no figure; (e) held is never 0.

Nothing else moves: every V3.0.41 line not named by the inputs is byte-identical (asserted); totals move only in the
ground-slab code (asserted). Files: V3_0_42_BOQ_LINES.json / .csv, V3_0_42_INTEGRATION_LEDGER.json / .csv,
V3_0_42_DIFF.csv, V3_0_42_RUN.json. Nothing here names a project, a sheet, a layer or a coordinate.
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
from engine.source import arch_v3038 as A3038
from engine.source import arch_v3039 as A3039
from engine.source import arch_v3040 as A3040
from engine.source import arch_v3041 as A3041

DEFAULT_GUARD_CLASS = "TOOLING"          # T-212: re-books checker-merged ledgers; adds no default value
METHOD = "ARCH_TAKEOFF_V3.0.42"
EXTENDS = A3041.METHOD
CANDIDATE = A30.METHOD
POLICY_ID = "URBAN_BOQ_T442_ARCH_V3_0_42"
INPUTS_SCHEMA = "URBAN_V3042_INPUTS_V1"
LEDGER_SCHEMA = "URBAN_V3042_INTEGRATION_LEDGER_V1"
ROLLBACK = A30.ROLLBACK
InputsError = A3031.InputsError
_r = A3018._r
_fmt = A3030._fmt
RULE_ID, RULE_VERSION = "R-T442-1", "T-442"
REC_KEY = "ground_slab_v3042"
SUPERSEDED_KEY = "superseded_by_v3042"
P_CELL, P_PANEL, P_TEXT = "GS_CELL_VALUE", "GS_PANEL_ADD", "CAUSE_TEXT"
GS = "STR.CONC.GROUND_SLAB"
DC, VER = "DRAWING-CONFIRMED", "VERIFIED"
HELD_STATES = ("BLOCKED_RFI", "BOUNDED_EXPOSURE")
VALUED = ("MEASURED", "SOURCE_DERIVED", "PROVISIONAL")
TOL = 0.0000015                          # the merged tables print 6 decimals (m3) / 4 decimals (m2 x 0.10)
OWN_CODES = (GS,)                        # the only code whose totals may move
TEXT_CODES = ("STR.CONC.COLUMN", "STR.CONC.LIFT", GS)

PIECES = {
    P_CELL: {"module": "engine/source/arch_v3042.py (a held slab cell valued at its re-measured panels x the printed T; "
                       "shaft / ring named beside with their owners)", "policy": "GS_CELL_VALUE_V1",
             "rule_id": "R-T444-1 .. 7 (R-T442-1 a, e)",
             "owner_rules": ["UP-QTY-STATUS-001 (held is blank, never 0)", "register ruling LIFT PIT vs GROUND SLAB "
                             "(Lead 2026-11-01 20:17: the pit floor is the raft top; the ring is the pit wall)"],
             "owner_manual_method": "owner method: slab on grade = the plan area between the ground-beam faces x the "
                                    "printed thickness, by panel; no slab over a pit or under a member",
             "drawing_method": "panels closed on the drawn band faces of the ground-beam plan (Checker re-measure by "
                               "handle) x the printed 'T=10cm'; the engine cell net minus the shaft (raft-top pit "
                               "floor) and the ring (pit wall) = the panels"},
    P_PANEL: {"module": "engine/source/arch_v3042.py (a slab panel dropped as a stair zone gets one ground-slab line)",
              "policy": "GS_PANEL_ADD_V1", "rule_id": "R-T436-1 (R-T442-1 b, c)",
              "owner_rules": ["Q-62 A (the flight-to-slab junction is the slab's)", "lessons row 2026-11-01 'a stair "
                              "on grade is never a reason to drop the slab panel under it' (adopted 20:20)",
                              "UP-QTY-STATUS-001"],
              "owner_manual_method": "owner method: slab on grade = the plan area between the ground-beam faces x the "
                                     "printed thickness; no answered rule removes the slab under a flight on grade",
              "drawing_method": "the panel closed by four drawn band faces, only HIDDEN flight lines inside (drawn "
                                "above the plan), no void / pit / opening on the slab plan, no stair base on the "
                                "foundation plan (only a column footing): slab, whole, x the printed T"},
    P_TEXT: {"module": "engine/source/arch_v3042.py (the cause text of a held / ranged line names the right designer "
                       "item; no figure moves)", "policy": "CAUSE_TEXT_V1", "rule_id": "R-T433 (R-T442-1 d)",
             "owner_rules": ["ERS s.2.6 (a held quantity names what unlocks it)"],
             "owner_manual_method": "not a quantity: the blocker named on the line is the designer / supplier item "
                                    "that unlocks it",
             "drawing_method": "the merged T-433 split by blocker: the item that holds each line, by line id"},
}
WAITING = dict(A3041.WAITING)
WAITING.update({
    "T442_GS_BEYOND_NETWORK": "the freelancer's plate area beyond everything drawn (6.3864 m2, -0.638616 m3, T-436 "
                              "B-HIS): UNRESOLVED on his side; no engine line, never a cause without a drawn line",
    "T442_GS_LIFT_SIDE": "the two panels against the lift ring (engine 2.615573 + 2.244696 vs own 2.721160 + 2.253380 "
                         "m2, -0.011427 m3, T-436 F-LIFT): UNRESOLVED, 0.1143 m2 not placed; lines unchanged",
    "T442_GS_STUB_ENDS": "the 45-degree end triangles of the beam stub BAND0038 (slab face -0.09 m2 / -0.009 m3 with "
                         "the stub +0.027 m3, T-436 F-018-ENDS / E-T436-1): worker-traced, not re-measured by the "
                         "Checker (T-436 verdict: panel only); not wired, lines unchanged",
})
ACTIONS = ("VALUE_CELL", "ADD_PANEL", "CAUSE_TEXT")


# ================================================================================================ inputs
def _need(s, keys, where):
    for k in keys:
        if s.get(k) in (None, ""):
            raise InputsError(f"{where}: {k} missing")


def _num(x, where, pos=True):
    if not isinstance(x, (int, float)) or isinstance(x, bool) or x != x:
        raise InputsError(f"{where}: {x!r} is not a number")
    if x < 0 or (pos and x == 0):
        raise InputsError(f"{where}: {x!r} is {'not positive' if pos else 'negative'}")
    return float(x)


def _area(x, where):
    if isinstance(x, (int, float)) and not isinstance(x, bool) and abs(x) < 1e-9:
        raise InputsError(f"{where}: HELD_AS_ZERO: a panel of 0 m2 is refused")
    v = _num(x, where)
    if v > 2000:
        raise InputsError(f"{where}: {v} is not an area in m2 (mm2 refused)")
    return v


def _t(x, where):
    v = _num(x, where)
    if v > 1.0:
        raise InputsError(f"{where}: T {v} is not a slab thickness in metres (mm refused)")
    return v


def _sources(doc):
    srcs = {}
    for s in doc.get("sources") or ():
        _need(s, ("task", "file", "sha256", "merge_commit", "checker_run"), f"source {s.get('task')}")
        srcs[s["task"]] = s
    return srcs


def _tasks(r, srcs, where):
    if not r.get("source_tasks") or any(t not in srcs for t in r["source_tasks"]):
        raise InputsError(f"{where}: no merged source named")


def _panels(rows, where, seen):
    out = []
    for p in rows or ():
        _need(p, ("id",), f"{where} panel")
        if p["id"] in seen:
            raise InputsError(f"{where}: panel {p['id']} named twice (one panel, one owner line)")
        seen.add(p["id"])
        out.append(dict(p, _a=_area(p.get("area"), f"{where} panel {p['id']}")))
    if not out:
        raise InputsError(f"{where}: no panel named")
    return out


def load_inputs(doc, project_id=None):
    """URBAN_V3042_INPUTS_V1 -> the validated doc.
    {"schema", "project_id", "sources": [{"task", "file", "sha256", "merge_commit", "checker_run"}],
     "cells": [{"line_id", "cell", "floor", "expect": {"evidence_state", "high"}, "t", "t_status", "area_status",
                "panels": [{"id", "area"}], "declared_m2", "declared_m3",
                "beside": [{"kind", "area", "owner", "why"}], "source_tasks"}],
     "panels": [{"cell", "element_id", "floor", "t", "t_status", "area_status", "template_line", "exclusion_retired",
                 "panels": [{"id", "area"}], "declared_m3", "physical_element", "source_tasks"}],
     "texts": [{"line_id", "item_code", "old", "new", "why", "source_tasks"}]}"""
    if not doc:
        return None
    if doc.get("schema") != INPUTS_SCHEMA:
        raise InputsError(f"project inputs: schema must be {INPUTS_SCHEMA}")
    if project_id and doc.get("project_id") not in (None, project_id):
        raise InputsError(f"project inputs are for {doc.get('project_id')!r}, the run is {project_id!r}")
    srcs = _sources(doc)
    seen_panels, seen_lines, seen_cells = set(), set(), set()
    cells = []
    for c in doc.get("cells") or ():
        w = f"cell line {c.get('line_id')}"
        _need(c, ("line_id", "cell", "floor", "t_status", "area_status"), w)
        _tasks(c, srcs, w)
        if c["line_id"] in seen_lines or c["cell"] in seen_cells:
            raise InputsError(f"{w}: named twice")
        seen_lines.add(c["line_id"])
        seen_cells.add(c["cell"])
        if c["area_status"] not in (DC, VER) or c["t_status"] not in (DC, VER):
            raise InputsError(f"{w}: area / T status {c['area_status']} / {c['t_status']} (a valued panel is "
                              f"DRAWING-CONFIRMED or VERIFIED; anything else stays HELD)")
        e = c.get("expect") or {}
        if e.get("evidence_state") not in HELD_STATES:
            raise InputsError(f"{w}: the bound line is not a held line (expect.evidence_state)")
        t = _t(c.get("t"), f"{w} t")
        ps = _panels(c.get("panels"), w, seen_panels)
        a = _r(sum(p["_a"] for p in ps))
        m3 = _r(a * t)
        if c.get("declared_m2") is not None and abs(_num(c["declared_m2"], f"{w} declared_m2") - a) > 0.00006:
            raise InputsError(f"{w}: panels {_fmt(a)} m2 are not the merged {c['declared_m2']}")
        if c.get("declared_m3") is not None and abs(_num(c["declared_m3"], f"{w} declared_m3") - m3) > TOL:
            raise InputsError(f"{w}: panels x T {_fmt(m3)} m3 are not the merged {c['declared_m3']}")
        bs = []
        for b in c.get("beside") or ():
            _need(b, ("kind", "owner", "why"), f"{w} beside")
            bs.append(dict(b, _a=_area(b.get("area"), f"{w} beside {b['kind']}")))
        cells.append(dict(c, _t=t, _panels=ps, _a=a, _m3=m3, _beside=bs, _high=e.get("high")))
    adds = []
    for p in doc.get("panels") or ():
        w = f"panel line {p.get('element_id')}"
        _need(p, ("cell", "element_id", "floor", "t_status", "area_status", "template_line", "exclusion_retired",
                  "physical_element"), w)
        _tasks(p, srcs, w)
        if p["cell"] in seen_cells:
            raise InputsError(f"{w}: cell {p['cell']} named twice (one cell, one line)")
        seen_cells.add(p["cell"])
        if p["area_status"] not in (DC, VER) or p["t_status"] not in (DC, VER):
            raise InputsError(f"{w}: area / T status {p['area_status']} / {p['t_status']} (HELD, not this version)")
        t = _t(p.get("t"), f"{w} t")
        ps = _panels(p.get("panels"), w, seen_panels)
        a = _r(sum(q["_a"] for q in ps))
        m3 = _r(a * t)
        if p.get("declared_m3") is not None and abs(_num(p["declared_m3"], f"{w} declared_m3") - m3) > TOL:
            raise InputsError(f"{w}: panel x T {_fmt(m3)} m3 is not the merged {p['declared_m3']}")
        adds.append(dict(p, _t=t, _panels=ps, _a=a, _m3=m3))
    texts = []
    for x in doc.get("texts") or ():
        w = f"cause text {x.get('line_id')}"
        _need(x, ("line_id", "item_code", "old", "new", "why"), w)
        _tasks(x, srcs, w)
        if x["line_id"] in seen_lines:
            raise InputsError(f"{w}: line named twice (one line, one action)")
        seen_lines.add(x["line_id"])
        if x["item_code"] not in TEXT_CODES:
            raise InputsError(f"{w}: {x['item_code']} is not a structural code this version may re-text")
        if x["old"] == x["new"] or x["old"] in x["new"]:
            raise InputsError(f"{w}: the new text must replace the old item, not repeat it")
        texts.append(dict(x))
    if not (cells or adds or texts):
        raise InputsError("no cell, panel or cause text in the inputs")
    return dict(doc, _sources=srcs, _cells=cells, _adds=adds, _texts=texts)


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


def _base(ln):
    new = copy.deepcopy(ln)
    new["calculation"] = copy.deepcopy(new["calculation"])
    new["calculation"]["inputs"] = dict(new["calculation"]["inputs"] or {})
    return new


def _high(ln):
    br = ln.get("bounded_range") or {}
    return br.get("high")


def _plist(ps):
    return " + ".join(f"{p['id']} {_fmt(p['_a'])}" for p in ps)


# ================================================================================================ pieces
def _cell_valued(ln, c, srcs):
    """the held cell line VALUED at its panels x T; its older held records kept whole under SUPERSEDED_KEY."""
    new = _base(ln)
    inp = new["calculation"]["inputs"]
    was = A302._q(A30._qty(ln))
    old = {}
    for k in (A3033.REC_KEY,):                # a held-bound record of an older version is superseded by name
        if k in inp:
            old[k] = inp.pop(k)
    new["evidence_state"] = "SOURCE_DERIVED"
    new["measured_net"] = c["_m3"]
    new["gross"] = c["_m3"]
    new["bounded_range"] = None
    new["rfi"] = None
    ev = VER if (c["area_status"] == VER and c["t_status"] in (VER, DC)) else DC
    beside = "; ".join(f"{b['kind']} {_fmt(b['_a'])} m2 -> {b['owner']} ({b['why']})" for b in c["_beside"])
    new["calculation"]["formula"] = (
        f"{METHOD}: slab on grade of cell {c['cell']} = panels {_plist(c['_panels'])} = {_fmt(c['_a'])} m2 "
        f"(Checker re-measure, {c['area_status']}) x printed T {_fmt(c['_t'])} m ({c['t_status']}) = "
        f"{_fmt(c['_m3'])} m3 (R-T444-1); not slab, not in this figure: {beside or 'none'}; was {was} "
        f"(the former reading is kept in calculation.inputs.{REC_KEY}.formula_before)")[:1500]
    inp[REC_KEY] = _rec(P_CELL, srcs, action="VALUE_CELL", cell=c["cell"], was=was, panels=[
        {"id": p["id"], "area": p["_a"]} for p in c["_panels"]], area_m2=c["_a"], t=c["_t"], value_m3=c["_m3"],
        area_status=c["area_status"], t_status=c["t_status"], evidence_status=ev,
        beside=[{"kind": b["kind"], "area": b["_a"], "owner": b["owner"], "why": b["why"]} for b in c["_beside"]],
        formula_before=ln["calculation"]["formula"], high_before=_high(ln))
    if old:
        inp[SUPERSEDED_KEY] = {"superseded_by": METHOD, "rule": RULE_ID, "records": old,
                               "why": "the held bound is replaced by the Checker-verified panels x T (R-T444-1)"}
    inp["evidence_status"] = ev
    new["notes"] = (f"{new.get('notes') or ''} | {METHOD}: VALUED at the re-measured panels x T ({ev}); shaft / ring "
                    f"named beside with their owners; NOT RELEASED")
    return _fin(new), ev


def _panel_line(p, tpl, srcs):
    from engine.source import boq_line as BL
    ev = VER if (p["area_status"] == VER and p["t_status"] in (VER, DC)) else DC
    rec = _rec(P_PANEL, srcs, action="ADD_PANEL", cell=p["cell"], panels=[{"id": q["id"], "area": q["_a"]}
                                                                          for q in p["_panels"]],
               area_m2=p["_a"], t=p["_t"], value_m3=p["_m3"], area_status=p["area_status"], t_status=p["t_status"],
               exclusion_retired=p["exclusion_retired"], evidence_status=ev, template_line=tpl["line_id"])
    loc = tpl["location"]
    ln = BL.make_line(
        project_id=tpl["project"]["project_id"], revision_set_sha256=tpl["project"]["revision_set_sha256"],
        item_code=GS, unit="m3", evidence_state="SOURCE_DERIVED", measured_net=p["_m3"], gross=p["_m3"],
        element_id=p["element_id"], floor=p["floor"], room_id=loc.get("room_id"),
        physical_element=p["physical_element"],
        formula=(f"{METHOD}: slab on grade of cell {p['cell']} = panel {_plist(p['_panels'])} m2 ({p['area_status']}, "
                 f"closed on drawn band faces) x printed T {_fmt(p['_t'])} m ({p['t_status']}) = {_fmt(p['_m3'])} m3; "
                 f"a flight drawn hidden over the panel does not remove the slab (R-T436-1); the engine's exclusion "
                 f"'{p['exclusion_retired']}' is retired")[:1500],
        inputs={REC_KEY: rec, "evidence_status": ev}, documents=copy.deepcopy(tpl["source"]["documents"]),
        geometry_source=tpl["source"]["geometry_source"], geometry_confidence=tpl["source"]["geometry_confidence"],
        rule_id=RULE_ID, rule_version=RULE_VERSION, material_state=tpl.get("material_state") or "BY_SPEC",
        notes=(f"{METHOD}: slab panel the engine left out as a stair zone (R-T436-1); one line for the cell; NOT "
               f"RELEASED"),
        item_en=tpl["item_en"], item_ar=tpl["item_ar"], trade=tpl["trade"], subtrade=tpl.get("subtrade"))
    return _fin(ln), ev


def _retexted(ln, x, srcs):
    """the designer item named in the line's cause texts (formula, notes, rfi question, range basis) replaced; every
    figure (state, net, gross, range ends, rfi unlocks) kept; older records keep their own text (history)."""
    new = _base(ln)
    o, n_ = x["old"], x["new"]
    f = new["calculation"].get("formula") or ""
    nt = new.get("notes") or ""
    rq = (new.get("rfi") or {}).get("question") or ""
    bb = (new.get("bounded_range") or {}).get("basis") or ""
    hits = {"formula": f.count(o), "notes": nt.count(o), "rfi_question": rq.count(o), "range_basis": bb.count(o)}
    if not any(hits.values()):
        raise InputsError(f"cause text {ln['line_id']}: '{o}' is not in its formula, notes, rfi or range basis (stale "
                          f"binding)")
    if hits["formula"]:
        new["calculation"]["formula"] = f.replace(o, n_)[:1500]
    if hits["notes"]:
        new["notes"] = nt.replace(o, n_)
    if hits["rfi_question"]:
        new["rfi"] = dict(new["rfi"], question=rq.replace(o, n_)[:900])
    if hits["range_basis"]:
        new["bounded_range"] = dict(new["bounded_range"], basis=bb.replace(o, n_)[:300])
    inp = new["calculation"]["inputs"]
    inp[REC_KEY] = _rec(P_TEXT, srcs, action="CAUSE_TEXT", old=o, new=n_, why=x["why"], hits=hits,
                        evidence_status=inp.get("evidence_status") or "HELD")
    new["notes"] = (f"{new.get('notes') or ''} | {METHOD}: cause text '{o}' -> '{n_}' ({x['why']}); no figure "
                    f"moves")[:2000]
    return _fin(new)


def _figures(ln):
    br = dict(ln.get("bounded_range") or {})
    br.pop("basis", None)
    rfi = dict(ln.get("rfi") or {})
    rfi.pop("question", None)
    return [ln.get(k) for k in ("evidence_state", "measured_net", "gross", "deductions", "additions", "unit",
                                "item_code", "location", "line_id")] + [br, rfi]


def _texts_of(ln):
    return " ".join([ln["calculation"].get("formula") or "", ((ln.get("rfi") or {}).get("question") or ""),
                     ((ln.get("bounded_range") or {}).get("basis") or "")])


# ================================================================================================ changes
def _cells_of(lines):
    """-> {cell id: [GS line ids]} (a cell id is the last ':' part of the element id)."""
    out = {}
    for ln in lines:
        if ln["item_code"] == GS:
            out.setdefault(str((ln["location"] or {}).get("element_id") or "").split(":")[-1], []).append(ln["line_id"])
    return out


def changes_for(doc, l3041):
    """-> (changes, log). Each change: piece, action (CHANGE / ADD), before (a V3.0.41 line or None), after."""
    if not doc:
        return [], {"piece": "+".join((P_CELL, P_PANEL, P_TEXT)), "state": "NO_PROJECT_INPUT"}
    if any(((ln.get("calculation") or {}).get("inputs") or {}).get(REC_KEY) for ln in l3041):
        raise InputsError("the candidate already carries V3.0.42 records (applied once)")
    by = {ln["line_id"]: ln for ln in l3041}
    S = doc["_sources"]
    cells = _cells_of(l3041)
    changes, seen = [], set(by)
    log = {"piece": "+".join((P_CELL, P_PANEL, P_TEXT)), "state": "RUN", "sources": doc["sources"],
           "by_action": {}, "lines_added": 0, "lines_changed": 0, "m3_valued": 0.0, "exclusions_retired": []}

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

    for c in doc["_cells"]:
        srcs = [S[t] for t in c["source_tasks"]]
        w = f"cell line {c['line_id']}"
        ln = by.get(c["line_id"])
        if ln is None or ln["item_code"] != GS or ln["unit"] != "m3":
            raise InputsError(f"{w}: not a {GS} m3 line of the candidate (stale binding)")
        if ln["evidence_state"] != c["expect"]["evidence_state"] or ln.get("measured_net") is not None:
            raise InputsError(f"{w}: {ln['evidence_state']} {ln.get('measured_net')} is not the held line the merged "
                              f"ledger bound (stale binding)")
        if not str(ln["location"].get("element_id") or "").endswith(c["cell"]):
            raise InputsError(f"{w}: the line is not cell {c['cell']}")
        h = _high(ln)
        if c["_high"] is not None and (h is None or abs(h - c["_high"]) > TOL):
            raise InputsError(f"{w}: held high {h} is not the merged bound {c['_high']} (stale binding)")
        if h is not None and c["_m3"] > h + TOL:
            raise InputsError(f"{w}: the value {c['_m3']} exceeds the line's own held bound {h}")
        new, ev = _cell_valued(ln, c, srcs)
        held = [{"what": f"{GS} {c['cell']} {b['kind']}", "why": f"{b['owner']}: {b['why']}"[:300], "range": None,
                 "scenario": "not slab: owned by its own line"} for b in c["_beside"]]
        add(P_CELL, "VALUE_CELL", new, before=ln, srcs=srcs, evidence_status=ev, held=held,
            downstream=["concrete roll-up (I-07 term -> AGREE)", "formwork: none (slab on grade on fill)"])
        log["m3_valued"] = _r(log["m3_valued"] + c["_m3"])
    for p in doc["_adds"]:
        srcs = [S[t] for t in p["source_tasks"]]
        w = f"panel line {p['element_id']}"
        if cells.get(p["cell"]):
            raise InputsError(f"{w}: cell {p['cell']} already carries a ground-slab line {cells[p['cell']]} "
                              f"(re-value it, do not add one)")
        tpl = by.get(p["template_line"])
        if tpl is None or tpl["item_code"] != GS:
            raise InputsError(f"{w}: template {p['template_line']} is not a {GS} line")
        new, ev = _panel_line(p, tpl, srcs)
        add(P_PANEL, "ADD_PANEL", new, srcs=srcs, evidence_status=ev, held=[],
            downstream=["concrete roll-up (GS-STAIR-ZONE term -> ENGINE_RIGHT after integration)"])
        log["m3_valued"] = _r(log["m3_valued"] + p["_m3"])
        log["exclusions_retired"].append({"cell": p["cell"], "reason": p["exclusion_retired"],
                                          "line": new["line_id"]})
    for x in doc["_texts"]:
        srcs = [S[t] for t in x["source_tasks"]]
        ln = by.get(x["line_id"])
        if ln is None or ln["item_code"] != x["item_code"]:
            raise InputsError(f"cause text {x['line_id']}: not a {x['item_code']} line of the candidate (stale binding)")
        if ln["evidence_state"] in VALUED and ln.get("measured_net") is not None:
            raise InputsError(f"cause text {x['line_id']}: a valued line has no held cause to correct")
        new = _retexted(ln, x, srcs)
        add(P_TEXT, "CAUSE_TEXT", new, before=ln, srcs=srcs,
            evidence_status=(ln["calculation"]["inputs"] or {}).get("evidence_status") or "HELD", held=[])
    log["by_action"] = dict(sorted(log["by_action"].items()))
    return changes, log


# ================================================================================================ checks
def check_slab(lines, before=None):
    """R-T442-1 on the integrated lines: a valued cell = its panels x T, no older held record live on it; an added panel
    line = its panel x T, one GS line per cell, no panel in two lines; a re-texted line keeps every figure of its
    V3.0.41 line (when `before` is given) and no longer cites the old item in its formula. -> summary."""
    out = {"cells_valued": 0, "panels_added": 0, "texts": 0, "m3_valued": 0.0}
    cells = _cells_of(lines)
    for k, v in cells.items():
        if len(v) > 1 and any(((ln.get("calculation") or {}).get("inputs") or {}).get(REC_KEY)
                              for ln in lines if ln["line_id"] in v):
            raise ValueError(f"{METHOD}: cell {k} carries {len(v)} ground-slab lines")
    pan = {}
    b4 = {ln["line_id"]: ln for ln in before or ()}
    for ln in lines:
        rec = ((ln.get("calculation") or {}).get("inputs") or {}).get(REC_KEY)
        if not rec:
            continue
        a = rec["action"]
        if a in ("VALUE_CELL", "ADD_PANEL"):
            if ln["item_code"] != GS or ln["unit"] != "m3" or ln["evidence_state"] not in VALUED:
                raise ValueError(f"{METHOD}: slab line {ln['line_id']} is not a valued {GS} m3 line")
            s = _r(sum(p["area"] for p in rec["panels"]))
            if abs(s - rec["area_m2"]) > 1e-9 or abs(ln["measured_net"] - _r(s * rec["t"])) > 1e-9:
                raise ValueError(f"{METHOD}: slab line {ln['line_id']} is not its panels x T")
            for p in rec["panels"]:
                if p["id"] in pan:
                    raise ValueError(f"{METHOD}: panel {p['id']} in two lines (double count)")
                pan[p["id"]] = ln["line_id"]
            if A3033.REC_KEY in ln["calculation"]["inputs"]:
                raise ValueError(f"{METHOD}: valued cell {ln['line_id']} still carries a live held-bound record")
            out["cells_valued" if a == "VALUE_CELL" else "panels_added"] += 1
            out["m3_valued"] = _r(out["m3_valued"] + ln["measured_net"])
        elif a == "CAUSE_TEXT":
            if rec["old"] in _texts_of(ln).replace(rec["new"], ""):
                raise ValueError(f"{METHOD}: re-texted line {ln['line_id']} still cites {rec['old']}")
            o = b4.get(ln["line_id"])
            if o is not None and _figures(o) != _figures(ln):
                raise ValueError(f"{METHOD}: re-texted line {ln['line_id']} moved a figure")
            out["texts"] += 1
        else:
            raise ValueError(f"{METHOD}: action {a}")
    return out


# ================================================================================================ integrate / write
def integrate(l3041, changes, for_lead=()):
    """-> (V3.0.42 lines, identity). Changed lines replace their V3.0.41 line in place; added lines follow; every other
    V3.0.41 line is byte-identical (asserted)."""
    sid = {ln["line_id"]: i for i, ln in enumerate(l3041)}
    out = list(l3041)
    adds, repl = [], set()
    for c in changes:
        a = c["after"]
        if c["action"] == "ADD":
            if a["line_id"] in sid:
                raise ValueError(f"{METHOD}: an added line repeats a V3.0.41 id")
            if a["item_code"] != GS:
                raise ValueError(f"{METHOD}: added code {a['item_code']} is not one this version adds")
            adds.append(a)
        elif c["action"] == "CHANGE":
            i = sid.get(a["line_id"])
            if i is None or a["line_id"] in repl:
                raise ValueError(f"{METHOD}: a changed line is not a V3.0.41 line or changes twice")
            if a["item_code"] not in TEXT_CODES:
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
    slab = check_slab(out, l3041)
    pids = {(ln["project"]["project_id"], ln["project"]["revision_set_sha256"]) for ln in out}
    if len(pids) != 1:
        raise ValueError(f"{METHOD}: {len(pids)} project identities in the lines")
    outside = [ln for ln in l3041 if ln["line_id"] not in repl]
    bad = [a["line_id"] for a in outside if A30.line_sha(a) != A30.line_sha(out[sid[a["line_id"]]])]
    if bad:
        raise ValueError(f"{METHOD}: {len(bad)} V3.0.41 line(s) differ outside the named changes")
    ident = {"v3_0_41_lines": len(l3041), "v3_0_42_lines": len(out), "v3_0_42_rows": len(changes),
             "replaced": len(repl), "added": len(adds), "outside_rows": len(outside),
             "outside_rows_identical_to_v3_0_41": len(outside), "slab": slab, "pieces": pieces, "gb_runs": runs,
             "flights": flights, "beds": beds, "lift": lift, "landing": landing, "lists": lists, "fence": fence,
             "tile_zones": zones, "corrections": corr, "ceilings": ceil, "roof_buildup": roof, "guards": guards,
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
                     "before_released_v2_9": b29, "before_v3_0_41": A30._qty(c.get("before")),
                     "after_v3_0_42": A30._qty(ref), "evidence_status": c.get("evidence_status"),
                     "still_held": c.get("held"), "release_status": "NOT RELEASED",
                     "owner_manual_method": PIECES[c["piece"]]["owner_manual_method"],
                     "drawing_derived_method": PIECES[c["piece"]]["drawing_method"],
                     "record": rec, "verification": c.get("verification") or {}, "rollback": ROLLBACK})
    return rows


LEDGER_CSV = ("version", "piece", "action", "change", "line_id", "item_code", "floor", "element_id", "unit", "v2_9",
              "v3_0_41", "v3_0_42", "evidence_status", "still_held", "verification")
DIFF_CSV = ("line_id", "item_code", "floor", "element_id", "unit", "vs_v3_0_41", "vs_released_v2_9", "v2_9",
            "v3_0_41", "v3_0_42")


def ledger_csv(rows):
    def q(x):
        return A302._q(x) if x and (x.get("value") is not None or x.get("low") is not None) else ""

    def h(r):
        return "; ".join(f"{x['what']} {x.get('range')}" for x in (r.get("still_held") or ()))[:300]
    return A305._csv([{"version": r["version"], "piece": r["piece"], "action": r["action"], "change": r["change"],
                       "line_id": r["line_id"], "item_code": r["item_code"], "floor": r.get("floor") or "",
                       "element_id": r.get("element_id") or "", "unit": r["unit"],
                       "v2_9": q(r.get("before_released_v2_9")), "v3_0_41": q(r.get("before_v3_0_41")),
                       "v3_0_42": q(r.get("after_v3_0_42")), "evidence_status": r["evidence_status"],
                       "still_held": h(r),
                       "verification": f"{r['verification'].get('task')} "
                                       f"{' '.join(x[:8] for x in r['verification'].get('merge_commits') or ())}"}
                      for r in rows], LEDGER_CSV)


def diff_rows(l3041, l3042, released_lines=None):
    b41 = {ln["line_id"]: ln for ln in l3041}
    rel = {A30._key(ln): ln for ln in released_lines or ()}
    out = []
    for ln in l3042:
        o = b41.get(ln["line_id"])
        vs = "ADDED" if o is None else ("SAME" if A30.line_sha(o) == A30.line_sha(ln) else "CHANGED")
        r = rel.get(A30._key(ln)) if released_lines is not None else None
        vs29 = None if released_lines is None else ("NOT_IN_RELEASED" if r is None else
                                                    ("SAME_QUANTITY" if A30._qty(r) == A30._qty(ln) else
                                                     "QUANTITY_DIFFERS"))
        out.append({"line_id": ln["line_id"], "item_code": ln["item_code"], "floor": ln["location"].get("floor"),
                    "element_id": ln["location"].get("element_id"), "unit": ln["unit"], "vs_v3_0_41": vs,
                    "vs_released_v2_9": vs29, "v2_9": A302._q(A30._qty(r)) if r else "",
                    "v3_0_41": A302._q(A30._qty(o)) if o else "", "v3_0_42": A302._q(A30._qty(ln))})
    return out


def write(out, l3041, changes, log, released_lines=None, for_lead=()):
    """the V3_0_42_* files beside the V3_0_41_* files. -> (file names, identity, ledger)."""
    from pathlib import Path
    from engine.source import boq_line as BL
    out = Path(out)
    l3042, ident = integrate(l3041, changes, for_lead)
    rows = ledger_rows(changes, released_lines)
    diff = diff_rows(l3041, l3042, released_lines)
    named = {c["after"]["line_id"] for c in changes}
    stray = [d["line_id"] for d in diff if d["vs_v3_0_41"] in ("CHANGED", "ADDED") and d["line_id"] not in named]
    if stray:
        raise ValueError(f"{METHOD}: {len(stray)} line(s) changed outside the named changes")
    dsum = {}
    for d in diff:
        dsum.setdefault("vs_v3_0_41", {}).setdefault(d["vs_v3_0_41"], 0)
        dsum["vs_v3_0_41"][d["vs_v3_0_41"]] += 1
        if d["vs_released_v2_9"] is not None:
            dsum.setdefault("vs_released_v2_9", {}).setdefault(d["vs_released_v2_9"], 0)
            dsum["vs_released_v2_9"][d["vs_released_v2_9"]] += 1
    ident = dict(ident, diff=dsum)
    t41, t42 = A304.code_totals(l3041), A304.code_totals(l3042)
    moved = {k: {"v3_0_41": t41.get(k), "v3_0_42": t42.get(k)} for k in sorted(set(t41) | set(t42))
             if t41.get(k) != t42.get(k)}
    if any(k.split("|")[0] not in OWN_CODES for k in moved):
        raise ValueError(f"{METHOD}: totals moved outside this version's codes: {sorted(moved)[:5]}")
    led = {"schema": LEDGER_SCHEMA, "method": METHOD, "extends": EXTENDS, "candidate": CANDIDATE,
           "base": A30.BASE_METHOD, "released": A30.RELEASED_METHOD, "released_default": False, "rows": rows,
           "exclusions_retired": log.get("exclusions_retired") or [], "waiting_pieces": WAITING,
           "integration_package": True}
    run = {"method": METHOD, "policy": POLICY_ID, "extends": EXTENDS, "candidate": CANDIDATE,
           "base_method": A30.BASE_METHOD, "released_method": A30.RELEASED_METHOD, "released_default": False,
           "rollback": ROLLBACK, "identity": ident, "pieces": PIECES, "piece_logs": [log],
           "totals_moved_by_code": moved, "waiting_pieces": WAITING}
    files = {"V3_0_42_BOQ_LINES.json": BL.dumps(l3042),
             "V3_0_42_BOQ_LINES.csv": A30._lines_csv(l3042),
             "V3_0_42_INTEGRATION_LEDGER.json": A30._j(led),
             "V3_0_42_INTEGRATION_LEDGER.csv": ledger_csv(rows),
             "V3_0_42_DIFF.csv": A305._csv(diff, DIFF_CSV),
             "V3_0_42_RUN.json": A30._j(run)}
    for name, text in files.items():
        (out / name).write_text(text, encoding="utf-8")
    return sorted(files), ident, led


def policy_record():
    return {"method": METHOD, "extends": EXTENDS, "pieces": sorted(PIECES), "inputs_schema": INPUTS_SCHEMA,
            "released_default": False, "rollback": ROLLBACK, "actions": list(ACTIONS)}


__all__ = ["METHOD", "PIECES", "WAITING", "DEFAULT_GUARD_CLASS", "INPUTS_SCHEMA", "load_inputs", "changes_for",
           "check_slab", "integrate", "ledger_rows", "diff_rows", "write", "InputsError"]
