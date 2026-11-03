"""ARCH_TAKEOFF_V3.0.46 (T-419, stream S): the SAME opt-in BOQ candidate as ARCH_TAKEOFF_V3.0 .. V3.0.45
(engine.source.arch_v30, arch_v301 .. arch_v3045), extended with the LIFT TIE BEAM and the HOUSE BELOW-GROUND MASONRY
of the Checker-verified pieces T-408 (merged e3d9a092) and T-407 (merged 8c0e8349) in ONE step:

  ADD_HELD   a printed element carried by no line becomes a HELD BLANK line by name (BLOCKED_RFI: no value, no range,
             never 0), its drawing-confirmed measure (a length, an AT_LEAST plane) BESIDE the quantity in the record and
             the rfi, never in it; every fact still missing is named. A component line of the same element (forms,
             bars) is tied to its parent line by id.
  RESTATE    a held line whose reason names only some of the facts it depends on is restated to name EVERY fact (ERS
             lesson 2026-10-31: a held quantity names every fact it depends on); its state, quantity, range, code,
             unit and location are unchanged (asserted).
  BIND_CHECK lines the merged pieces confirmed (ring beams, shaft cap, the GF block lines paired with the tie) are
             re-checked by id, code, state and value; nothing on them moves.

R-T419-1 (every villa; integrates R-T408-1 .. 6 and R-T407-1 .. 5): (a) a member printed by a note with no section
gets its own HELD BLANK line per component (concrete, each form face, bars), its length measured between the supports
drawn at its own level beside; never a value borrowed from another member, and never inside a column, ring-beam or
block line (columns own the joints; the block lines take the displaced face once the section arrives, paired, never a
second concrete quantity); (b) block printed below a ground beam is its own line per run under the owner trade
BLOCKWORK BELOW N.G., its AT_LEAST plane beside (run net of columns x the height bound from printed minima), never
inside the fence masonry, the ground-beam concrete or the foundation band (the band partition house + fence + pool =
band is asserted); a run with a CONFLICT soffit gets no bound; a run whose existence is unprinted gets NO line (a
register item by name); (c) a held line names every fact it depends on; (d) held is never 0.

Nothing else moves: every V3.0.45 line not named by the inputs is byte-identical (asserted); totals move only by
blocked-line counts of the codes the added lines carry (asserted: no released quantity and no held range moves).
Files: V3_0_46_BOQ_LINES.json / .csv, V3_0_46_INTEGRATION_LEDGER.json / .csv, V3_0_46_DIFF.csv, V3_0_46_RUN.json.
Nothing here names a project, a sheet, a layer or a coordinate. Standard library only.
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

DEFAULT_GUARD_CLASS = "TOOLING"          # T-212: re-books checker-merged ledgers; adds no default value
METHOD = "ARCH_TAKEOFF_V3.0.46"
EXTENDS = A3045.METHOD
CANDIDATE = A30.METHOD
POLICY_ID = "URBAN_BOQ_T419_ARCH_V3_0_46"
INPUTS_SCHEMA = "URBAN_V3046_INPUTS_V1"
LEDGER_SCHEMA = "URBAN_V3046_INTEGRATION_LEDGER_V1"
ROLLBACK = A30.ROLLBACK
InputsError = A3031.InputsError
_r = A3018._r
_fmt = A3030._fmt
RULE_ID, RULE_VERSION = "R-T419-1", "T-419"
REC_KEY = "lift_tie_gb_masonry_v3046"
P_TIE, P_MAS, P_TEXT, P_BIND = "LIFT_TIE_BEAM", "HOUSE_BELOW_NG_MASONRY", "HELD_REASON", "BIND_CHECK"
HELD_STATE = "BLOCKED_RFI"
LINE_ID_RE = re.compile(r"^L-[0-9a-f]{20}$")
FORMULA_END_RE = A3043.FORMULA_END_RE
TOL = 0.0005                              # metres / m2 on the beside measures (3-dp printed figures)
# the codes each piece may ADD; anything else is refused (a tie beam never in a column / ring-beam line, masonry
# below N.G. of the house never in the fence masonry, the ground-beam concrete or the band)
ADD_CODES = {P_TIE: ("STR.CONC.LIFT", "STR.FORMWORK", "STR.REBAR"), P_MAS: ("MAS.BLOCK",)}
REFUSED_CODES = {P_TIE: ("STR.CONC.COLUMN", "STR.CONC.BEAM", "STR.CONC.RING_BEAM", "MAS.BLOCK"),
                 P_MAS: ("EXT.FENCE.MASONRY_BELOW_NG", "EXT.FENCE.BLOCK", "EXT.FENCE.WALL", "STR.CONC.GROUND_BEAM",
                         "STR.CONC.FOOTING", "STR.CONC.BOUNDARY_WALL")}
BESIDE_KINDS = ("LENGTH", "AT_LEAST_AREA", "NO_BOUND")
ACTIONS = ("ADD_HELD", "RESTATE", "BIND_CHECK")

PIECES = {
    P_TIE: {"module": "engine/source/arch_v3046.py (the GF lift tie beam: concrete, side forms, soffit form and bars, "
                      "each HELD BLANK, the drawing-confirmed length beside)", "policy": "LIFT_TIE_ADD_HELD_V1",
            "rule_id": "R-T408-1 .. 6 (T-408), R-T419-1 a, c, d",
            "owner_rules": ["D-43 / RFI-B-S14 (tie section printed nowhere)", "UP-QTY-STATUS-001 (held is never 0)",
                            "ELEMENT_REGISTER GF LIFT TIE BEAM 2026-11-01 04:15 (owner trade STRUCTURE; columns own "
                            "the joints; block lines paired)"],
            "owner_manual_method": "owner method: beam between the column faces x printed section (column > beam > "
                                   "slab); forms 2 sides x length x depth + soffit length x width; section only as "
                                   "printed",
            "drawing_method": "clear runs between the GF storey's own lift columns on the GF roof slab plan, the "
                              "column plan and the ground-beam plan (5.500 m on three sheets, band closure 0 overlap); "
                              "section not printed: every component HELD BLANK, the length beside"},
    P_MAS: {"module": "engine/source/arch_v3046.py (black block under the neighbour-side house ground beams, one HELD "
                      "BLANK line per printed run, the AT_LEAST plane beside)", "policy": "HOUSE_BELOW_NG_ADD_HELD_V1",
            "rule_id": "R-T407-1 .. 5 (T-407), R-T419-1 b, c, d",
            "owner_rules": ["Q-60 A (block to the underside of the beam above it)", "owner block rule 2026-10-20 10:45 "
                            "(the engineering-office note decides black / white)", "Q-21 C (1.50 m is a minimum)",
                            "Q-65 C (block product HELD until specified)", "D-35 / RFI-S09 (annex beam depth)",
                            "ELEMENT_REGISTER BELOW-GROUND MASONRY UNDER THE HOUSE GROUND BEAMS (owner trade BLOCKWORK "
                            "BELOW N.G.)", "UP-QTY-STATUS-001"],
            "owner_manual_method": "Q-60 A: run (net of columns) x height from the foundation top to the beam "
                                   "underside; type from the engineering note; thickness only as printed",
            "drawing_method": "run axis on the 0.20 lower band net of the S-COL.BON columns on the axis (corner columns "
                              "split once); height bounded below by soffit - 0.10 blinding max - highest printed "
                              "foundation top (AT_LEAST, no upper bound); value HELD on the formation level"},
    P_TEXT: {"module": "engine/source/arch_v3046.py (a held line restated to name every fact it depends on)",
             "policy": "HELD_REASON_RESTATE_V1", "rule_id": "R-T408 F-T408-1 / F-T408-2, R-T419-1 c",
             "owner_rules": ["ERS lesson 2026-10-31 (ADOPTED): a held quantity names every fact it depends on"],
             "owner_manual_method": "pit-wall height = raft top -> slab-on-grade top: pit depth below the landing "
                                    "F.F.L. AND the GF build-up F.F.L. -> slab top",
             "drawing_method": "both facts unprinted (lift supplier; structural / architect): named on every pit-wall "
                               "height line; no quantity moves"},
    P_BIND: {"module": "engine/source/arch_v3046.py (merged bindings re-checked by id, code, state and value)",
             "policy": "LIFT_BIND_CHECK_V1", "rule_id": "R-T408-6",
             "owner_rules": ["WORKFLOW_CONTROLS s.10.5 (verified inputs re-checked, not re-derived)"],
             "owner_manual_method": "ring beams and shaft cap as measured (Checker-verified)",
             "drawing_method": "line ids, codes, states and values on the candidate equal the merged binding"},
}
WAITING = dict(A3045.WAITING)
WAITING.update({
    "T419_TIE_SECTION": "lift tie beam section b x d printed nowhere (D-43, RFI-B-S14): concrete, forms and bars stay "
                        "HELD BLANK; the GF block lines L-4165954c / L-4423d85b / L-63fa7862 keep their tie hold "
                        "(paired: they take the displaced face once, never a second concrete quantity)",
    "T419_TIE_CLASH": "tie vs GF roof ring beams: separate members only while d < 0.75 - build-up (S / W), < 0.40 + "
                      "the slab - build-up (E / N): OPEN by name (no structural slab level printed)",
    "T419_LIFT_DOOR_HEAD": "whether the tie (soffit +4.00) heads the GF lift door or a separate lintel is needed is OPEN "
                           "until the door height is known (lintel owner)",
    "T419_MAIN_S_FORMATION": "house below-ground masonry MAIN_S: formation level under the neighbour-side beams, band "
                             "blinding and block thickness unprinted (designer items 1, 2, 4 of T-407 s.7)",
    "T419_ANNEX_S_D35": "ANNEX_S: annex beam soffit CONFLICT (D-35, RFI-S09): no bound (reading L 7.000 m2 shown in "
                        "T-407, not adopted)",
    "T419_E_W_EXISTENCE": "MAIN_E_SEA (6.600 m net) and ANNEX_W_STREET (6.000 m net): band drawn, nothing printed "
                          "between: existence UNKNOWN (designer item 3): register items by name, NO line",
})


# ================================================================================================ inputs
def _need(s, keys, where):
    for k in keys:
        if s.get(k) in (None, "", [], {}):
            raise InputsError(f"{where}: {k} missing")


def _num(x, where):
    if not isinstance(x, (int, float)) or isinstance(x, bool) or x != x or x <= 0:
        raise InputsError(f"{where}: {x!r} is not a positive number (held is never 0)")
    if x > 10000:
        raise InputsError(f"{where}: {x} is not a measure in m / m2 (mm refused)")
    return float(x)


def _beside(b, where):
    """the measure beside a held line: LENGTH {length_m} | AT_LEAST_AREA {run_m, height_at_least_m, area_m2,
    gross_area_m2?} (area = run x height asserted) | NO_BOUND {why}."""
    if not isinstance(b, dict) or b.get("kind") not in BESIDE_KINDS:
        raise InputsError(f"{where}: beside.kind must be one of {BESIDE_KINDS}")
    for k in ("value", "measured_net", "quantity"):
        if k in b:
            raise InputsError(f"{where}: a held line carries no value ({k}); the measure stays beside")
    k = b["kind"]
    if k == "LENGTH":
        b["_len"] = _num(b.get("length_m"), f"{where} length_m")
        if b["_len"] > 500:
            raise InputsError(f"{where}: length {b['_len']} is not a member length in m (mm refused)")
        if b.get("sheets") in (None, []) or len(b["sheets"]) < 1:
            raise InputsError(f"{where}: a length beside names the sheet(s) it is drawn on")
    elif k == "AT_LEAST_AREA":
        run, h, a = (_num(b.get(x), f"{where} {x}") for x in ("run_m", "height_at_least_m", "area_m2"))
        if abs(run * h - a) > TOL:
            raise InputsError(f"{where}: AT_LEAST area {a} is not run {run} x height {h}")
        if b.get("gross_area_m2") is not None and _num(b["gross_area_m2"], f"{where} gross") + TOL < a:
            raise InputsError(f"{where}: gross below net")
        b["_run"], b["_h"], b["_a"] = run, h, a
    else:
        _need(b, ("why",), where)
        for x in ("area_m2", "length_m", "height_at_least_m"):
            if b.get(x) is not None:
                raise InputsError(f"{where}: a NO_BOUND line carries no bound ({x}); a CONFLICT soffit gives none")
    return b


def load_inputs(doc, project_id=None):
    """URBAN_V3046_INPUTS_V1 -> the validated doc.
    {"schema", "project_id", "sources": [{"task", "file", "sha256", "merge_commit", "checker_run"}],
     "add": [{"key", "piece" (LIFT_TIE_BEAM | HOUSE_BELOW_NG_MASONRY), "item_code", "unit", "element_id", "floor",
              "physical_element", "owner_trade", "template_line", "beside": {...}, "missing_facts": [..],
              "tied_to" (key of the parent added line or None), "basis", "source_tasks"}],
     "restate": [{"line_id", "expect": {"item_code", "evidence_state"}, "facts": [..], "why", "source_tasks"}],
     "bind": [{"what", "line_ids": [..], "expect": {"item_code", "total"} , "source_tasks"}],
     "partition": {"house_m", "fence_m", "pool_m", "band_m", "source_tasks"},
     "register_only": [{"key", "why", "net_run_m"}]}"""
    if not doc:
        return None
    if doc.get("schema") != INPUTS_SCHEMA:
        raise InputsError(f"project inputs: schema must be {INPUTS_SCHEMA}")
    if project_id and doc.get("project_id") not in (None, project_id):
        raise InputsError(f"project inputs are for {doc.get('project_id')!r}, the run is {project_id!r}")
    doc = copy.deepcopy(doc)
    srcs = A3043._sources(doc)
    keys, elems, named = set(), set(), set()
    adds = []
    for x in doc.get("add") or ():
        w = f"add {x.get('key')}"
        _need(x, ("key", "piece", "item_code", "unit", "element_id", "physical_element", "owner_trade",
                  "template_line", "beside", "missing_facts", "basis", "source_tasks"), w)
        A3043._tasks(x, srcs, w)
        if x["key"] in keys or x["element_id"] in elems:
            raise InputsError(f"{w}: one key and one element id per added line")
        keys.add(x["key"])
        elems.add(x["element_id"])
        if x["piece"] not in ADD_CODES:
            raise InputsError(f"{w}: piece {x['piece']} is not {sorted(ADD_CODES)}")
        if x["item_code"] in REFUSED_CODES[x["piece"]]:
            raise InputsError(f"{w}: {x['item_code']} refused for {x['piece']} (never inside that line: R-T419-1 a / b)")
        if x["item_code"] not in ADD_CODES[x["piece"]]:
            raise InputsError(f"{w}: {x['item_code']} is not a code of {x['piece']} {ADD_CODES[x['piece']]}")
        if not LINE_ID_RE.match(str(x["template_line"])):
            raise InputsError(f"{w}: template_line is not a BOQ line id")
        for k in ("value", "measured_net", "gross", "bounded_range", "low", "high"):
            if x.get(k) is not None:
                raise InputsError(f"{w}: an added held line carries no {k} (HELD BLANK, never 0)")
        x["beside"] = _beside(dict(x["beside"]), w)
        if x["piece"] == P_MAS and x["beside"]["kind"] == "LENGTH":
            raise InputsError(f"{w}: a masonry run carries an AT_LEAST plane or NO_BOUND beside")
        if not isinstance(x["missing_facts"], list) or not all(isinstance(f, str) and f for f in x["missing_facts"]):
            raise InputsError(f"{w}: missing_facts is a list of named facts")
        adds.append(x)
    for x in adds:
        t = x.get("tied_to")
        if t is not None and (t not in keys or t == x["key"] or next(a for a in adds if a["key"] == t).get("tied_to")):
            raise InputsError(f"add {x['key']}: tied_to {t!r} is not a parent added line")
    rest = []
    for x in doc.get("restate") or ():
        w = f"restate {x.get('line_id')}"
        _need(x, ("line_id", "expect", "facts", "why", "source_tasks"), w)
        A3043._tasks(x, srcs, w)
        if not LINE_ID_RE.match(str(x["line_id"])) or x["line_id"] in named:
            raise InputsError(f"{w}: not a BOQ line id, or named twice")
        named.add(x["line_id"])
        if len(x["facts"]) < 2:
            raise InputsError(f"{w}: a restatement names every fact (at least the two it was missing)")
        rest.append(x)
    binds = []
    for x in doc.get("bind") or ():
        w = f"bind {x.get('what')}"
        _need(x, ("what", "line_ids", "expect", "source_tasks"), w)
        A3043._tasks(x, srcs, w)
        binds.append(x)
    part = doc.get("partition")
    if part:
        _need(part, ("house_m", "fence_m", "pool_m", "band_m", "source_tasks"), "partition")
        A3043._tasks(part, srcs, "partition")
        h, f, p, b = (_num(part[k], f"partition {k}") for k in ("house_m", "fence_m", "pool_m", "band_m"))
        if abs(h + f + p - b) > TOL:
            raise InputsError(f"partition: house {h} + fence {f} + pool {p} = {_r(h + f + p)} is not the band {b} "
                              f"(an overlap or a gap between the house and fence masonry)")
    if any(x["piece"] == P_MAS for x in adds) and not part:
        raise InputsError("house below-ground masonry needs the band partition (house + fence + pool = band)")
    for x in doc.get("register_only") or ():
        _need(x, ("key", "why"), f"register item {x.get('key')}")
        if x["key"] in keys:
            raise InputsError(f"register item {x['key']}: existence UNKNOWN is a register item, never a line")
    doc["_sources"], doc["_adds"], doc["_restate"], doc["_binds"] = srcs, adds, rest, binds
    return doc


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


def beside_text(b):
    if b["kind"] == "LENGTH":
        return (f"length {_fmt(b['_len'])} m DRAWING-CONFIRMED ({'; '.join(b['sheets'])}), beside, never the "
                f"quantity")
    if b["kind"] == "AT_LEAST_AREA":
        g = f", gross at least {_fmt(b['gross_area_m2'])} m2" if b.get("gross_area_m2") is not None else ""
        return (f"net run {_fmt(b['_run'])} m x height at least {_fmt(b['_h'])} m: AT_LEAST {_fmt(b['_a'])} m2 net{g}, "
                f"beside, never the quantity (no upper bound printed)")
    return f"no bound: {b['why']}"


def _added(tpl, x, srcs, parent_id=None):
    from engine.source import boq_line as BL
    b = x["beside"]
    bt = beside_text(b)
    facts = "; ".join(x["missing_facts"])
    tied = f" | component of {parent_id} (same element, tied by id)" if parent_id else ""
    formula = (f"{METHOD}: HELD BLANK (never a value, never 0) {A3043._plain(x['physical_element'])} | owner trade "
               f"{x['owner_trade']} | {A3043._plain(x['basis'])} | held by: {A3043._plain(facts)} | {bt}{tied} "
               f"({RULE_ID})")[:1500]
    if FORMULA_END_RE.search(formula):
        raise InputsError(f"add {x['key']}: the formula would conclude on a figure")
    rec = _rec(x["piece"], srcs, action="ADD_HELD", key=x["key"], owner_trade=x["owner_trade"],
               beside={k: v for k, v in b.items() if not k.startswith("_")}, missing_facts=list(x["missing_facts"]),
               parent_line=parent_id, basis=x["basis"], evidence_status="HELD")
    inputs = {REC_KEY: rec, "evidence_status": "HELD"}
    if x["item_code"] == A3030.FW_CODE:
        # the formwork book (V3.0.30 guard): every STR.FORMWORK line carries its formwork record, each face once, the
        # concrete line it forms named; a held face is blank beside a held concrete line
        face = x["element_id"].replace(":", ".")
        inputs[A3030.REC_KEY] = A3030._rec(srcs[0], A3030.FW_PIECE, action="ADD", status="HELD", tie="TIED",
                                           face_ids=[face], faces=1, element=x["piece"], method=None,
                                           alternative=None, bounds=None, concrete_line=parent_id,
                                           evidence_status="HELD", added_by=METHOD)
    ln = BL.make_line(
        project_id=tpl["project"]["project_id"], revision_set_sha256=tpl["project"]["revision_set_sha256"],
        item_code=x["item_code"], unit=x["unit"], evidence_state=HELD_STATE, measured_net=None, gross=None,
        element_id=x["element_id"], floor=x.get("floor"), physical_element=x["physical_element"], formula=formula,
        inputs=inputs, documents=copy.deepcopy(tpl["source"]["documents"]),
        geometry_source=tpl["source"]["geometry_source"], geometry_confidence=tpl["source"]["geometry_confidence"],
        rule_id=RULE_ID, rule_version=RULE_VERSION, material_state=tpl.get("material_state") or "SOURCE",
        rfi={"question": f"{x['physical_element']}: {facts}"[:900], "unlocks": x["element_id"],
             "bound_beside": bt[:300]},
        notes=f"{METHOD}: printed element carried by no line, added HELD BLANK ({x['owner_trade']}); NOT RELEASED",
        item_en=x.get("item_en") or tpl["item_en"], item_ar=x.get("item_ar") or tpl["item_ar"], trade=tpl["trade"],
        subtrade=tpl.get("subtrade"))
    return _fin(ln)


QTY_KEYS = ("evidence_state", "measured_net", "gross", "bounded_range", "item_code", "unit", "location", "deductions",
            "additions", "project", "line_id")


def _restated(ln, x, srcs):
    new = copy.deepcopy(ln)
    new["calculation"]["inputs"] = dict(new["calculation"]["inputs"] or {})
    facts = "; ".join(x["facts"])
    old_q = (ln.get("rfi") or {}).get("question")
    rfi = dict(new.get("rfi") or {})
    tie = (f" | tied to the concrete line {x['tie_to']} (it exists in the candidate; an older 'no candidate concrete "
           f"line' remark above is superseded)") if x.get("tie_to") else ""
    rfi["question"] = (f"every fact this quantity depends on: {facts}{tie} | was: "
                       f"{old_q or ln.get('physical_element') or ln['item_code']}")[:900]
    new["rfi"] = rfi
    new["calculation"]["inputs"][REC_KEY] = _rec(
        P_TEXT, srcs, action="RESTATE", facts=list(x["facts"]), why=x["why"], question_before=old_q,
        tied_to_concrete_line=x.get("tie_to"),
        evidence_status=new["calculation"]["inputs"].get("evidence_status") or "HELD")
    new["notes"] = (f"{new.get('notes') or ''} | {METHOD}: held reason restated to name every fact ({facts}); "
                    f"quantity, range and state unchanged")[:2000]
    return _fin(new)


# ================================================================================================ changes
def changes_for(doc, prev):
    """-> (changes, log). Each change: piece, action (CHANGE / ADD), before (a candidate line or None), after."""
    pieces = "+".join((P_TIE, P_MAS, P_TEXT, P_BIND))
    if not doc:
        return [], {"piece": pieces, "state": "NO_PROJECT_INPUT"}
    if any(((ln.get("calculation") or {}).get("inputs") or {}).get(REC_KEY) for ln in prev):
        raise InputsError("the candidate already carries V3.0.46 records (applied once)")
    by = {ln["line_id"]: ln for ln in prev}
    S = doc["_sources"]
    changes, seen = [], set(by)
    log = {"piece": pieces, "state": "RUN", "sources": doc["sources"], "by_action": {}, "lines_added": 0,
           "lines_changed": 0, "binds": [], "register_only": doc.get("register_only") or [],
           "partition": {k: v for k, v in (doc.get("partition") or {}).items()}}
    elems = {(ln["location"] or {}).get("element_id") for ln in prev}

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
                                    drawing_reference="; ".join(s["file"] for s in srcs), verification=A3043._ver(srcs),
                                    downstream=kw.pop("downstream", []), group=after["item_code"], **kw))

    ids = {}
    for x in sorted(doc["_adds"], key=lambda a: a.get("tied_to") is not None):   # parents first
        w = f"add {x['key']}"
        tpl = by.get(x["template_line"])
        if tpl is None or tpl["item_code"] != x["item_code"] or tpl["unit"] != x["unit"]:
            raise InputsError(f"{w}: template {x['template_line']} is not a {x['item_code']} {x['unit']} line of the "
                              f"candidate (stale binding)")
        if x["element_id"] in elems:
            raise InputsError(f"{w}: element {x['element_id']} already has a line (one element, one line)")
        srcs = [S[t] for t in x["source_tasks"]]
        parent = ids.get(x["tied_to"]) if x.get("tied_to") else None
        nl = _added(tpl, x, srcs, parent)
        ids[x["key"]] = nl["line_id"]
        add(x["piece"], "ADD_HELD", nl, srcs=srcs, evidence_status="HELD",
            held=[{"what": x["key"], "why": "; ".join(x["missing_facts"])[:300], "range": None,
                   "scenario": "held blank; " + beside_text(x["beside"])[:200]}],
            downstream=[f"coverage: the printed element is now a line (held, {x['owner_trade']})",
                        "totals: blocked-line count of the code +1; no released quantity or held range moves"])
    for x in doc["_restate"]:
        w = f"restate {x['line_id']}"
        ln = by.get(x["line_id"])
        e = x["expect"]
        if ln is None or ln["item_code"] != e.get("item_code") or ln["evidence_state"] != e.get("evidence_state"):
            raise InputsError(f"{w}: not the {e.get('item_code')} {e.get('evidence_state')} line of the candidate "
                              f"(stale binding)")
        if ln.get("measured_net") is not None:
            raise InputsError(f"{w}: a restatement is for a held line")
        if x.get("tie_to") and (x["tie_to"] not in by or not by[x["tie_to"]]["item_code"].startswith("STR.CONC.")):
            raise InputsError(f"{w}: tie_to {x['tie_to']} is not a concrete line of the candidate")
        srcs = [S[t] for t in x["source_tasks"]]
        add(P_TEXT, "RESTATE", _restated(ln, x, srcs), before=ln, srcs=srcs, evidence_status="HELD",
            held=[{"what": x["line_id"], "why": "; ".join(x["facts"])[:300], "range": None,
                   "scenario": "text only; quantity unchanged"}], downstream=["none (held reason only)"])
    for x in doc["_binds"]:
        log["binds"].append(bind_check(prev, x))
    log["by_action"] = dict(sorted(log["by_action"].items()))
    return changes, log


def bind_check(lines, x):
    """R-T408-6: the merged binding re-checked by id, code, state and value; a drift is refused (stale binding)."""
    by = {ln["line_id"]: ln for ln in lines}
    e = x["expect"]
    tot, states = 0.0, []
    for lid in x["line_ids"]:
        ln = by.get(lid)
        if ln is None or ln["item_code"] != e["item_code"]:
            raise InputsError(f"bind {x['what']}: {lid} is not a {e['item_code']} line of the candidate (drift)")
        q = A30._qty(ln)
        if "total" in e:
            if q["value"] is None:
                raise InputsError(f"bind {x['what']}: {lid} is not valued ({ln['evidence_state']}) (drift)")
            tot += q["value"]
        if e.get("text") and e["text"].lower() not in A30._j(ln).lower():
            raise InputsError(f"bind {x['what']}: {lid} no longer names {e['text']!r} (pairing lost)")
        if e.get("evidence_state") and ln["evidence_state"] != e["evidence_state"]:
            raise InputsError(f"bind {x['what']}: {lid} is {ln['evidence_state']}, not {e['evidence_state']} (drift)")
        states.append(ln["evidence_state"])
    if "total" in e and abs(tot - e["total"]) > 1e-6:
        raise InputsError(f"bind {x['what']}: total {_r(tot)} is not {e['total']} (drift)")
    return {"what": x["what"], "lines": len(x["line_ids"]), "total": _r(tot) if "total" in e else None,
            "states": sorted(set(states)), "result": "BOUND"}


# ================================================================================================ checks
def check_tie_masonry(lines, before=None):
    """R-T419-1 on the integrated lines: every ADD_HELD line is BLOCKED_RFI blank (no value, gross or range; held never
    0), carries its beside measure in the record and the rfi, names its missing facts and, if a component, an existing
    parent; a tie component is never on a column / beam / block code and a house masonry run never on a fence /
    ground-beam / footing code; a RESTATE line keeps every quantity field of its candidate line. -> summary."""
    out = {"added_held": 0, "tie_lines": 0, "masonry_lines": 0, "restated": 0, "components_tied": 0}
    ids = {ln["line_id"] for ln in lines}
    b4 = {ln["line_id"]: ln for ln in before or ()}
    for ln in lines:
        rec = ((ln.get("calculation") or {}).get("inputs") or {}).get(REC_KEY)
        if not rec:
            continue
        act, piece = rec.get("action"), rec.get("piece")
        if act == "ADD_HELD":
            if ln["evidence_state"] != HELD_STATE or ln.get("measured_net") is not None or \
                    ln.get("gross") is not None or ln.get("bounded_range") is not None:
                raise ValueError(f"{METHOD}: added line {ln['line_id']} is not HELD BLANK (held is never 0)")
            if ln["item_code"] in REFUSED_CODES[piece] or ln["item_code"] not in ADD_CODES[piece]:
                raise ValueError(f"{METHOD}: {piece} line {ln['line_id']} on code {ln['item_code']}")
            if not rec.get("missing_facts") or not rec.get("beside") or not (ln.get("rfi") or {}).get("bound_beside"):
                raise ValueError(f"{METHOD}: added line {ln['line_id']} names no missing fact or no beside measure")
            if rec.get("parent_line") is not None:
                if rec["parent_line"] not in ids:
                    raise ValueError(f"{METHOD}: component {ln['line_id']} names no parent in the candidate")
                out["components_tied"] += 1
            if FORMULA_END_RE.search(ln["calculation"].get("formula") or ""):
                raise ValueError(f"{METHOD}: held line {ln['line_id']} formula concludes on a figure")
            out["added_held"] += 1
            out["tie_lines" if piece == P_TIE else "masonry_lines"] += 1
        elif act == "RESTATE":
            o = b4.get(ln["line_id"])
            if o is not None:
                for k in QTY_KEYS:
                    if o.get(k) != ln.get(k):
                        raise ValueError(f"{METHOD}: restated line {ln['line_id']} moved {k}")
            q = (ln.get("rfi") or {}).get("question") or ""
            if not all(f[:40].lower() in q.lower() for f in rec.get("facts") or ()):
                raise ValueError(f"{METHOD}: restated line {ln['line_id']} does not name every fact")
            out["restated"] += 1
        else:
            raise ValueError(f"{METHOD}: action {act}")
    return out


# ================================================================================================ integrate / write
def integrate(prev, changes, for_lead=()):
    """-> (V3.0.46 lines, identity). Changed lines replace their candidate line in place; added lines follow; every
    other candidate line is byte-identical (asserted)."""
    sid = {ln["line_id"]: i for i, ln in enumerate(prev)}
    out = list(prev)
    adds, repl = [], set()
    for c in changes:
        a = c["after"]
        if c["action"] == "ADD":
            if a["line_id"] in sid:
                raise ValueError(f"{METHOD}: an added line repeats a candidate id")
            adds.append(a)
        elif c["action"] == "CHANGE":
            i = sid.get(a["line_id"])
            if i is None or a["line_id"] in repl:
                raise ValueError(f"{METHOD}: a changed line is not a candidate line or changes twice")
            if c["step"] != "RESTATE":
                raise ValueError(f"{METHOD}: only a RESTATE may change a candidate line")
            out[i] = a
            repl.add(a["line_id"])
        else:
            raise ValueError(f"{METHOD}: action {c['action']}")
    out = out + adds
    if len({ln["line_id"] for ln in out}) != len(out):
        raise ValueError(f"{METHOD}: a BOQ line id appears twice")
    guards = A3031._family_guards(out, for_lead)
    ident = {"base_lines": len(prev), "v3_0_46_lines": len(out), "v3_0_46_rows": len(changes),
             "replaced": len(repl), "added": len(adds), "guards": guards,
             "roof_buildup": A3031.check_roof_layers(out), "ceilings": A3032.check_ceilings(out),
             "corrections": A3033.check_corrections(out), "tile_zones": A3034.check_zones(out),
             "fence": A3035.check_boundary(out), "lists": A3036.check_lists(out), "beds": A3038.check_beds(out),
             "lift": A3038.check_lift(out), "landing": A3038.check_landing(out), "flights": A3039.check_flights(out),
             "gb_runs": A3040.check_runs(out), "pieces": A3041.check_pieces(out), "slab": A3042.check_slab(out),
             "earthworks": A3043.check_earthworks(out), "skirting": A3044.check_skirting(out),
             "blinding": A3045.check_blinding(out), "tie_masonry": check_tie_masonry(out, prev)}
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


def check_totals(t0, t1):
    """only blocked-line counts (and line counts) may move: no released quantity and no held range (asserted)."""
    moved = {}
    for k in sorted(set(t0) | set(t1)):
        a, b = t0.get(k), t1.get(k)
        if a == b:
            continue
        a = a or {"lines": 0, "released": 0.0, "held_low": 0.0, "held_high": 0.0, "bounded_lines": 0,
                  "blocked_lines": 0}
        for f in ("released", "held_low", "held_high", "bounded_lines"):
            if a.get(f) != b.get(f):
                raise ValueError(f"{METHOD}: {k} {f} moved {a.get(f)} -> {b.get(f)} (held blank lines only)")
        moved[k] = {"base": t0.get(k), "v3_0_46": b}
    return moved


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
                     "after_v3_0_46": A30._qty(ref), "evidence_status": c.get("evidence_status"),
                     "beside": rec.get("beside"), "missing_facts": rec.get("missing_facts") or rec.get("facts"),
                     "still_held": c.get("held"), "release_status": "NOT RELEASED",
                     "owner_manual_method": PIECES[c["piece"]]["owner_manual_method"],
                     "drawing_derived_method": PIECES[c["piece"]]["drawing_method"],
                     "record": rec, "verification": c.get("verification") or {}, "rollback": ROLLBACK})
    return rows


LEDGER_CSV = ("version", "piece", "action", "change", "line_id", "item_code", "floor", "element_id", "unit", "v2_9",
              "base", "v3_0_46", "evidence_status", "beside", "still_held", "verification")
DIFF_CSV = ("line_id", "item_code", "floor", "element_id", "unit", "vs_base", "vs_released_v2_9", "v2_9", "base",
            "v3_0_46")


def ledger_csv(rows):
    def q(x):
        return A302._q(x) if x and (x.get("value") is not None or x.get("low") is not None or x.get("state")) else ""

    def h(r):
        return "; ".join(f"{x['what']}: {x.get('why')}" for x in (r.get("still_held") or ()))[:300]

    def b(r):
        x = r.get("beside") or {}
        return "; ".join(f"{k} {v}" for k, v in sorted(x.items()) if not isinstance(v, (list, dict)))[:300]
    return A305._csv([{"version": r["version"], "piece": r["piece"], "action": r["action"], "change": r["change"],
                       "line_id": r["line_id"], "item_code": r["item_code"], "floor": r.get("floor") or "",
                       "element_id": r.get("element_id") or "", "unit": r["unit"],
                       "v2_9": q(r.get("before_released_v2_9")), "base": q(r.get("before_base")),
                       "v3_0_46": q(r.get("after_v3_0_46")), "evidence_status": r["evidence_status"],
                       "beside": b(r), "still_held": h(r),
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
                    "base": A302._q(A30._qty(o)) if o else "", "v3_0_46": A302._q(A30._qty(ln))})
    return out


def write(out, prev, changes, log, released_lines=None, for_lead=(), doc=None):
    """the V3_0_46_* files beside the base candidate's files. -> (file names, identity, ledger)."""
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
    moved = check_totals(A304.code_totals(prev), A304.code_totals(new))
    led = {"schema": LEDGER_SCHEMA, "method": METHOD, "extends": EXTENDS, "candidate": CANDIDATE,
           "base": A30.BASE_METHOD, "released": A30.RELEASED_METHOD, "released_default": False, "rows": rows,
           "binds": log.get("binds"), "register_only": log.get("register_only"), "partition": log.get("partition"),
           "waiting_pieces": WAITING, "integration_package": True}
    run = {"method": METHOD, "policy": POLICY_ID, "extends": EXTENDS, "candidate": CANDIDATE,
           "base_method": A30.BASE_METHOD, "released_method": A30.RELEASED_METHOD, "released_default": False,
           "rollback": ROLLBACK, "identity": ident, "pieces": PIECES, "piece_logs": [log],
           "totals_moved_by_code": moved, "waiting_pieces": WAITING}
    files = {"V3_0_46_BOQ_LINES.json": BL.dumps(new),
             "V3_0_46_BOQ_LINES.csv": A30._lines_csv(new),
             "V3_0_46_INTEGRATION_LEDGER.json": A30._j(led),
             "V3_0_46_INTEGRATION_LEDGER.csv": ledger_csv(rows),
             "V3_0_46_DIFF.csv": A305._csv(diff, DIFF_CSV),
             "V3_0_46_RUN.json": A30._j(run)}
    for name, text in files.items():
        (out / name).write_text(text, encoding="utf-8")
    return sorted(files), ident, led


def policy_record():
    return {"method": METHOD, "extends": EXTENDS, "pieces": sorted(PIECES), "inputs_schema": INPUTS_SCHEMA,
            "released_default": False, "rollback": ROLLBACK, "actions": list(ACTIONS)}


__all__ = ["METHOD", "PIECES", "WAITING", "DEFAULT_GUARD_CLASS", "INPUTS_SCHEMA", "ADD_CODES", "REFUSED_CODES",
           "load_inputs", "changes_for", "bind_check", "check_tie_masonry", "check_totals", "integrate", "ledger_rows",
           "diff_rows", "write", "beside_text", "InputsError"]
