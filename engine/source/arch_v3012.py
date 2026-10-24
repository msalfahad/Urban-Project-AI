"""ARCH_TAKEOFF_V3.0.12 (T-146 + T-247): the SAME opt-in BOQ candidate as ARCH_TAKEOFF_V3.0 .. V3.0.11 (engine.source.
arch_v30, arch_v301 .. arch_v3011), extended with ONE slab / beam partition: the checker-merged beam ledger replaces the
candidate's beam lines run by run, and every candidate slab face that is not slab leaves the slab line for the line that
owns it. Not a new method family and not the released default (owner management decision 2026-10-20 sections 2 and 5);
rollback is running the released ARCH_TAKEOFF_V2.9.

The physical question (ERS 2026-10-22 s.2.1, s.3): a suspended RC floor is a set of plates between the faces of the
members that carry them and the members at their full depth (convention C1, "panel between beam faces, beam at full
depth"; the convention of the released route, the beam register, the slab ledger and the freelancer). Each piece of the
plan belongs to ONE line: a panel to the slab, a band, a ring, a strip or a box outside the outer beams to the beam lane
(measured, a CONFLICT range or HELD), a drafting mark to no line. The slab and the beam ledgers must therefore be
integrated together: a face that leaves the slab line has its home in the beam ledger of the same package (or is no
concrete), and no piece of plan is in both.

How it is built (tools/urban_boq_m9.py `arch --method ARCH_TAKEOFF_V3.0.12`):
  1. the run is the V3.0.11 candidate exactly: its V3_0_* .. V3_0_11_* files are written unchanged (arch_v30 ..
     arch_v3011 are not edited);
  2. BEAM_LEDGER (project inputs URBAN_V3012_INPUTS_V1): one checker-merged beam ledger (source file sha256, task,
     merge commit, checker run). Every candidate line of the item on the scope floors is accounted for, or the run is
     refused (an integration that only adds is refused):
       keep_lines       the line already carries its ledger run exactly (same single piece, same figure): kept
                        byte-identical;
       supersede_lines  the line is (part of) a ledger run whose figure or state differs: NOT_APPLICABLE_WITH_EVIDENCE
                        (never deleted, never summed), its figure kept as information; it must be named by exactly one
                        record (`supersedes`), and a line an earlier version changed only with that change named;
     then one line per superseding ledger run: CALCULATED -> SOURCE_DERIVED (VERIFIED only where the record names the
     checker run that re-measured it, else DRAWING-CONFIRMED); CONFLICT -> BOUNDED_EXPOSURE with its two readings
     (HELD, never the larger end); HELD with a candidate range -> BOUNDED_EXPOSURE (HELD); HELD with no value ->
     BLOCKED_RFI (HELD, never 0). A record's value is recomputed from its base and its named adjustments (an
     intersection removed once) and refused when it disagrees;
  3. SLAB_FACE_HOME: every candidate slab line whose face the checker-merged slab ledger classes as not slab is
     retired (NOT_APPLICABLE_WITH_EVIDENCE, its figure kept as information) with its home: a run of the beam ledger
     of THIS package (it must be a record or a kept run) or NOT_CONCRETE (a drafting mark, with why). The slab line
     left on each floor must equal the slab ledger's hand figure within the stated tolerance and named residual;
  4. GUARD RE-CHECK (piece DEFAULT_GUARD): the merged guard runs again over the V3.0.12 lines with the guard inputs of
     V3.0.7 (arch_v307.guard_changes);
  5. the V3_0_12_* files are written beside them: every line outside the V3.0.12 rows is byte-identical to the V3.0.11
     line (asserted on every run), and V3_0_12_DIFF.csv lists every line against V3.0.11 and against the released V2.9.

Rules: R-CONC-OWN-1 (one owner per piece of concrete; each intersection once); convention C1 (T-234, URBAN slab /
beam partition as billed by the route, the register and the freelancer); Q-61 C (unlabelled / contested pieces held
member by member, never the largest); Q-16 (no copied depth); Q-44 A (ring beams round openings stay); UP-QTY-STATUS-001
(held is a range or blocked, never 0); WORKFLOW_CONTROLS 2026-10-21 s.4 / s.5; ERS 2026-10-22 s.2.1, s.2.2, s.3, s.5,
s.7. Nothing here names a project, a sheet, a layer, a coordinate or a client; every number comes from the run or the
inputs.
"""

from __future__ import annotations

import copy
import hashlib

from engine.source import arch_v30 as A30
from engine.source import arch_v302 as A302
from engine.source import arch_v304 as A304
from engine.source import arch_v305 as A305
from engine.source import arch_v307 as A307
from engine.source import arch_v308 as A308
from engine.source import arch_v3010 as A3010
from engine.source import arch_v3011 as A3011

DEFAULT_GUARD_CLASS = "GUARD_HOST"      # T-212: a candidate method; it reaches the guard through arch_v307
METHOD = "ARCH_TAKEOFF_V3.0.12"
EXTENDS = A3011.METHOD
CANDIDATE = A30.METHOD                  # the candidate family this version extends (never a new method family)
POLICY_ID = "URBAN_BOQ_T146_T247_ARCH_V3_0_12"
LEDGER_SCHEMA = "URBAN_V3012_INTEGRATION_LEDGER_V1"
INPUTS_SCHEMA = "URBAN_V3012_INPUTS_V1"
ROLLBACK = A30.ROLLBACK
RUN_STATES = ("CALCULATED", "CONFLICT", "HELD")
HOME_KINDS = ("BEAM_RUN", "NOT_CONCRETE")
HELD_STATUS = ("HELD", "UNKNOWN")
LIVE_EVIDENCE = A307.LIVE_EVIDENCE
MAX_RUN_M3 = 50.0                       # one beam run above this is a unit slip (cm / mm given as m), refused
TOL_M3 = 1e-6                           # a record recomputed from its own base and adjustments
TOL_KEEP_M3 = 6e-5                      # a kept line equals its ledger run (the ledger rounds some runs to 4 decimals)
InputsError = A307.InputsError
_num = A307._num

PIECES = {
    "BEAM_LEDGER": {
        "module": "engine/source/arch_v3012.py (checker-merged beam ledger, run by run)",
        "policy": "BEAM_LEDGER_RUNS_V1", "rule_id": "R-CONC-OWN-1", "rule_version": "C1-2026-10-23",
        "owner_rules": ["R-CONC-OWN-1 (each piece of concrete has one owner; a column owns its footprint, each "
                        "intersection once)",
                        "convention C1 (T-234: panel between beam faces, beam at full depth; the route, the beam "
                        "register and the freelancer bill this way)",
                        "Q-61 C (owner 2026-10-20: contested / unlabelled pieces HELD member by member with location, "
                        "length and candidate volume; never the largest volume to be conservative)",
                        "Q-16 (an unlabelled span never takes the neighbour's depth)",
                        "Q-44 A (the ring beam round a dome / void opening stays)",
                        "UP-QTY-STATUS-001 (held is a range or blocked, never 0)"],
        "owner_manual_method": "manual QS beam take-off: per beam mark, schedule width x full depth x the length "
                               "between the faces of its supports (the column owns its footprint), slab panels "
                               "billed between the beam faces",
        "drawing_method": "each beam run between its own drawn edges on the slab plan, measured to the face of each "
                          "carrier on each edge (oblique carriers as trapezoids), curved members between their own "
                          "arcs less the void; the width checked against the schedule (a disagreement is a CONFLICT "
                          "of both readings); an unlabelled or contested piece HELD with its candidate range"},
    "SLAB_FACE_HOME": {
        "module": "engine/source/arch_v3012.py (checker-merged slab ledger: a face billed as slab only with slab "
                  "evidence)",
        "policy": "SLAB_FACE_HOME_V1", "rule_id": "URBAN-SLAB-FACE-HOME", "rule_version": "C1-2026-10-23",
        "owner_rules": ["R-CONC-OWN-1 (one owner per piece of concrete)",
                        "convention C1 (T-234)",
                        "Q-44 A (the ring belongs to the beam lane; T-139 s.4)",
                        "Q-61 C (strips and boxes outside the outer beams HELD in the beam lane, never omitted)",
                        "UP-QTY-STATUS-001"],
        "owner_manual_method": "manual QS slab take-off: plan area between the faces of the carrying beams per panel x "
                               "the printed (tag) or general-note thickness, openings deducted once",
        "drawing_method": "the slab ledger's panel partition of each slab sheet: a face is slab only with slab evidence "
                          "(tag, bars, or bounded by beam faces); band, ring, strip, box and junction faces belong to "
                          "the beam lane, drafting marks to no line"},
    "DEFAULT_GUARD": A307.PIECES["DEFAULT_GUARD"],
}
WAITING = dict(A3011.WAITING)
WAITING.update({
    "BEAM_HELD_DESIGNER_ITEMS": "the beam runs held by designer items D-02 / D-27 (width CONFLICT), D-04 (unlabelled "
                                "spans), D-05 / D-26 (projection strips and boxes) stay HELD as ranges (or with no "
                                "value where no depth is printed) until the designer answers; never 0",
    "BEAM_FORMWORK_REBAR_OF_CHANGED_RUNS": "formwork and reinforcement of the beam runs whose concrete changed here "
                                           "(trapezoid ends, the drawn void ring, the continuous runs) are later "
                                           "packages (formwork T-199, rebar T-009); their lines are not changed here",
    "SLAB_NO_PROFILE_TAG_SPREAD": "the released route's spread of a panel tag to untagged panels of a sheet is a "
                                  "released / no-profile rule fix (R-SLAB-T-1, a new rule version); the candidate's "
                                  "profile already gives untagged panels the general note thickness",
})


def _r(x, n=6):
    return None if x is None else round(float(x), n)


# ================================================================================================ project inputs
def _close(a, b, tol):
    """two figures of one measure: both values, or both [low, high] ranges, within tol."""
    if isinstance(a, (list, tuple)) or isinstance(b, (list, tuple)):
        return (isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)) and len(a) == len(b) == 2
                and all(_num(x) and _num(y) and abs(float(x) - float(y)) <= tol for x, y in zip(a, b)))
    return _num(a) and _num(b) and abs(float(a) - float(b)) <= tol


def _check_run(pc, r):
    run = r.get("run")
    st = r.get("status")
    if st not in RUN_STATES:
        raise InputsError(f"beam run {run}: status {st!r} not one of {RUN_STATES}")
    for k in ("floor", "mark", "source"):
        if r.get(k) in (None, ""):
            raise InputsError(f"beam run {run}: {k} is required")
    ge = r.get("guard_element") or {}
    if not ge.get("element_id") or not ge.get("part"):
        raise InputsError(f"beam run {run}: guard_element (register element_id and part) is required")
    if r["floor"] not in pc["scope"]["floors"]:
        raise InputsError(f"beam run {run}: floor {r['floor']!r} outside the scope {pc['scope']['floors']}")
    if st == "CALCULATED":
        if not (_num(r.get("base")) and r["base"] > 0):
            raise InputsError(f"beam run {run}: a CALCULATED run carries its measured base > 0 (missing is never 0)")
        adj = 0.0
        for a in r.get("adjust") or ():
            if not (isinstance(a, dict) and a.get("why") and a.get("what") and _num(a.get("m3"))):
                raise InputsError(f"beam run {run}: an adjustment names what, why and its m3")
            adj += float(a["m3"])
        v = float(r["base"]) - adj
        if not (_num(r.get("value")) and abs(float(r["value"]) - v) <= TOL_M3):
            raise InputsError(f"beam run {run}: value {r.get('value')} != base {r['base']} less its adjustments "
                              f"{_r(adj)} = {_r(v)}")
        if v <= 0:
            raise InputsError(f"beam run {run}: a measured run is > 0")
        if v > MAX_RUN_M3:
            raise InputsError(f"beam run {run}: {v} m3 is not one beam run (unit slip? m3 only)")
        if r.get("evidence_status") in HELD_STATUS:
            raise InputsError(f"beam run {run}: a CALCULATED run cannot be {r['evidence_status']}")
        if r.get("range") is not None:
            raise InputsError(f"beam run {run}: a CALCULATED run carries one value, no range")
    else:
        if not r.get("reasons") or r.get("evidence_status") not in HELD_STATUS:
            raise InputsError(f"beam run {run}: a {st} run names why and its status HELD / UNKNOWN")
        if r.get("value") is not None:
            raise InputsError(f"beam run {run}: a {st} run carries no released value")
        rg = r.get("range")
        if st == "CONFLICT" and rg is None:
            raise InputsError(f"beam run {run}: a CONFLICT carries the range of its readings (never one reading)")
        if rg is not None and not (isinstance(rg, (list, tuple)) and len(rg) == 2 and all(_num(x) for x in rg)
                                   and 0 < rg[0] <= rg[1]):
            raise InputsError(f"beam run {run}: a range is [low, high] with 0 < low <= high (held is never 0)")
        if rg is not None and rg[1] > MAX_RUN_M3:
            raise InputsError(f"beam run {run}: range {list(rg)} is not one beam run (unit slip? m3 only)")
        if st == "CONFLICT" and not (rg[0] < rg[1]):
            raise InputsError(f"beam run {run}: a CONFLICT has two distinct readings (low < high)")


def _check_beam(pc):
    sc = pc.get("scope") or {}
    if not sc.get("floors"):
        raise InputsError("piece BEAM_LEDGER: scope needs floors")
    runs = {}
    for r in pc.get("records") or ():
        if not r.get("run") or r["run"] in runs:
            raise InputsError(f"piece BEAM_LEDGER: every record names its run, once ({r.get('run')!r})")
        _check_run(pc, r)
        runs[r["run"]] = r
    if not runs:
        raise InputsError("piece BEAM_LEDGER: no records")
    named = {}
    for k in ("keep_lines", "supersede_lines"):
        for x in sc.get(k) or ():
            if not x.get("element_id") or not x.get("floor") or not x.get("why") or x.get("carried") is None:
                raise InputsError(f"piece BEAM_LEDGER: every scope.{k} entry has element_id, floor, carried and why")
            key = (x["element_id"], x["floor"])
            if key in named:
                raise InputsError(f"piece BEAM_LEDGER: line {key} accounted for twice")
            named[key] = k
            if k == "keep_lines":
                if not x.get("run") or x.get("ledger") is None:
                    raise InputsError(f"piece BEAM_LEDGER: kept line {key} names its ledger run and figure")
                if x["carried"] == "BLOCKED":
                    if x.get("run_status") != "HELD" or not x.get("ledger_info"):
                        raise InputsError(f"piece BEAM_LEDGER: kept blocked line {key} needs a HELD run and the "
                                          "ledger figure as information (ledger_info)")
                elif not _close(x["carried"], x["ledger"], TOL_KEEP_M3):
                    raise InputsError(f"piece BEAM_LEDGER: kept line {key} carries {x['carried']}, its run "
                                      f"{x['run']} is {x['ledger']}: a line that differs from its run is superseded")
                if x["run"] in runs:
                    raise InputsError(f"piece BEAM_LEDGER: run {x['run']} is kept on a candidate line AND added as a "
                                      "record (counted twice)")
    by_sup = {}
    for run, r in runs.items():
        for eid in r.get("supersedes") or ():
            key = (eid, r["floor"])
            if named.get(key) != "supersede_lines":
                raise InputsError(f"piece BEAM_LEDGER: run {run} supersedes {key}, which is not a supersede line")
            by_sup.setdefault(key, []).append(run)
    orphan = [k for k, v in named.items() if v == "supersede_lines" and k not in by_sup]
    if orphan:
        raise InputsError(f"piece BEAM_LEDGER: superseded line(s) with no run that replaces them: {orphan}")
    kept_runs = {x["run"] for x in sc.get("keep_lines") or ()}
    return set(runs) | kept_runs


def _check_slab(pc, beam_runs):
    faces = pc.get("faces") or ()
    if not faces:
        raise InputsError("piece SLAB_FACE_HOME: no faces")
    seen = set()
    for f in faces:
        key = (f.get("element_id"), f.get("floor"))
        if not all(key) or key in seen:
            raise InputsError(f"piece SLAB_FACE_HOME: every face names its candidate line (element_id, floor), once")
        seen.add(key)
        for k in ("face", "why"):
            if not f.get(k):
                raise InputsError(f"piece SLAB_FACE_HOME {key}: {k} is required")
        if not (_num(f.get("carried")) and f["carried"] > 0):
            raise InputsError(f"piece SLAB_FACE_HOME {key}: the figure the line carries (> 0)")
        h = f.get("home") or {}
        if h.get("kind") not in HOME_KINDS:
            raise InputsError(f"piece SLAB_FACE_HOME {key}: home kind one of {HOME_KINDS}")
        if h["kind"] == "BEAM_RUN":
            if beam_runs is None:
                raise InputsError(f"piece SLAB_FACE_HOME {key}: a face moved to the beam lane needs the beam ledger "
                                  "in the SAME package (slab and beam integrated once)")
            if h.get("run") not in beam_runs:
                raise InputsError(f"piece SLAB_FACE_HOME {key}: home run {h.get('run')!r} is not a run of the beam "
                                  "ledger of this package: the face would leave the slab line for no line")
        elif not h.get("evidence"):
            raise InputsError(f"piece SLAB_FACE_HOME {key}: NOT_CONCRETE names its drawing evidence")
    after = pc.get("declared_after") or {}
    if not after:
        raise InputsError("piece SLAB_FACE_HOME: declared_after per floor (the slab ledger's hand figure) is required")
    for fl, d in after.items():
        if not (_num(d.get("drawing")) and _num(d.get("tol_m3")) and 0 <= d["tol_m3"] <= 0.001):
            raise InputsError(f"piece SLAB_FACE_HOME floor {fl}: drawing figure and a tolerance <= 0.001 m3")


def load_inputs(doc, project_id=None):
    """URBAN_V3012_INPUTS_V1 or None:
        {"schema", "project",
         "pieces": [{"piece": "BEAM_LEDGER", "item_code", "unit": "m3", "source": {file, sha256, task, merge_commit,
                     checker_run}, "sources": [...],
                     "scope": {"floors", "keep_lines": [{element_id, floor, run, carried, ledger, why}],
                               "supersede_lines": [{element_id, floor, carried (value or [low, high] or the held
                                                    figure), why, earlier_change}]},
                     "records": [{run, floor, mark, member, status (CALCULATED / CONFLICT / HELD), base, adjust:
                                  [{what, m3, why}], value, range, supersedes: [element_id], evidence_status,
                                  verified_by, reasons, source, formula, info}],
                     "declared_totals": {"measured", "conflict": [lo, hi], "held": [lo, hi], "held_no_value"}},
                    {"piece": "SLAB_FACE_HOME", "item_code", "unit": "m3", "source": {...}, "sources": [...],
                     "faces": [{element_id, floor, face, t139_face, carried, why, home: {kind, run | evidence}}],
                     "declared_after": {floor: {drawing, tol_m3, residual_why}}}],
         "guard": as URBAN_V307_INPUTS_V1 "guard"}"""
    if doc is None:
        return None
    if doc.get("schema") != INPUTS_SCHEMA:
        raise InputsError(f"project inputs: schema must be {INPUTS_SCHEMA}")
    if project_id and doc.get("project") not in (None, project_id):
        raise InputsError(f"project inputs are for {doc.get('project')!r}, the run is {project_id!r}")
    by = {}
    for pc in doc.get("pieces") or ():
        p = pc.get("piece")
        if p not in ("BEAM_LEDGER", "SLAB_FACE_HOME") or p in by:
            raise InputsError(f"piece {p!r}: one of BEAM_LEDGER / SLAB_FACE_HOME, once each")
        if pc.get("unit") != "m3" or not pc.get("item_code"):
            raise InputsError(f"piece {p}: unit m3 and an item_code are required")
        A307._source(pc.get("source"), f"piece {p}")
        for s in pc.get("sources") or ():
            A307._source(s, f"piece {p} (supporting source)")
        by[p] = pc
    beam_runs = _check_beam(by["BEAM_LEDGER"]) if "BEAM_LEDGER" in by else None
    if "SLAB_FACE_HOME" in by:
        _check_slab(by["SLAB_FACE_HOME"], beam_runs)
    g = doc.get("guard")
    if g is not None:
        A307.load_inputs({"schema": A307.INPUTS_SCHEMA, "project": doc.get("project"), "guard": g}, project_id)
    return doc


# ================================================================================================ beam ledger
def _scope_lines(pc, lines):
    fl = pc["scope"]["floors"]
    return [ln for ln in lines if ln["item_code"] == pc["item_code"] and ln["unit"] == pc["unit"]
            and (ln.get("location") or {}).get("floor") in fl]


def run_line(pid, rev, docs, pc, r):
    """one BOQ line for one ledger run. -> (line, evidence status)"""
    from engine.source import boq_line as BL
    p, src = PIECES["BEAM_LEDGER"], pc["source"]
    st = r["status"]
    reasons = list(r.get("reasons") or ())
    if st == "CALCULATED":
        ev = "SOURCE_DERIVED"
    elif r.get("range") is not None:
        ev = "BOUNDED_EXPOSURE"
    else:
        ev = "BLOCKED_RFI"
    eid = f"HL:BEAM_LEDGER:{r['floor']}:{r['run']}"
    rfi = None if ev == "SOURCE_DERIVED" else {"question": "; ".join(reasons)[:900], "unlocks": eid}
    br = None
    if ev == "BOUNDED_EXPOSURE":
        br = {"low": _r(r["range"][0]), "high": _r(r["range"][1]),
              "basis": ((("CONFLICT of two readings: " if st == "CONFLICT" else "HELD candidate range: ")
                         + "; ".join(reasons)))[:300]}
    formula = r.get("formula") or (
        f"{r['base']} m3 measured" + "".join(f" - {a['m3']} ({a['what']})" for a in r.get("adjust") or ())
        if st == "CALCULATED" else ("held: " + "; ".join(reasons)))
    ln = BL.make_line(project_id=pid, revision_set_sha256=rev, item_code=pc["item_code"], unit="m3",
                      evidence_state=ev, measured_net=_r(r["value"]) if ev == "SOURCE_DERIVED" else None,
                      bounded_range=br, element_id=eid, floor=r["floor"], physical_element="BEAMS", subtrade="BEAMS",
                      formula=str(formula)[:400],
                      inputs={"policy": p["policy"], "source": src["file"], "source_sha256": src["sha256"],
                              "run": r["run"], "mark": r["mark"], "member": r.get("member"), "status": st,
                              "base_m3": _r(r.get("base")), "adjust": r.get("adjust") or [], "range": r.get("range"),
                              "supersedes": list(r.get("supersedes") or ()), "reasons": reasons,
                              "printed": r["source"], "info": r.get("info")},
                      documents=docs, geometry_source="CAD_VECTOR",
                      geometry_confidence="TOLERANCE_CERTIFIED" if ev == "SOURCE_DERIVED" else "INFERRED_CANDIDATE",
                      rule_id=p["rule_id"], rule_version=p["rule_version"], material_state="SOURCE", rfi=rfi,
                      notes=f"{METHOD}: beam run {r['run']} by the checker-merged beam ledger ({src['task']}, MERGED "
                            f"{src['merge_commit']})")
    evs = (r.get("evidence_status") or "HELD") if ev != "SOURCE_DERIVED" else (
        "VERIFIED" if r.get("verified_by") else "DRAWING-CONFIRMED")
    return ln, evs


def beam_changes(pc, lines, earlier_changed=()):
    """the BEAM_LEDGER piece on the V3.0.11 lines. -> (changes, log, superseded line ids)"""
    pid, rev, docs = A302._proj(lines)
    have = {ln["line_id"] for ln in lines}
    earlier = set(earlier_changed)
    src, sc = pc["source"], pc["scope"]
    verif = {"task": src["task"], "merge_commit": src["merge_commit"], "verifier_run": src["checker_run"],
             "source": src["file"], "source_sha256": src["sha256"],
             "supporting": [{k: s.get(k) for k in ("task", "merge_commit", "checker_run", "file")}
                            for s in pc.get("sources") or ()]}
    keep = {(x["element_id"], x["floor"]): x for x in sc.get("keep_lines") or ()}
    sup = {(x["element_id"], x["floor"]): x for x in sc.get("supersede_lines") or ()}
    log = {"piece": "BEAM_LEDGER", "state": "RUN", "source": src, "sources": pc.get("sources") or [],
           "item_code": pc["item_code"], "scope_lines": [], "records": [], "evidence_status": {}}
    changes, seen, touched = [], set(), set()
    kept_value = sup_value = sup_low = sup_high = 0.0
    kept_conf, kept_held, kept_none = [0.0, 0.0], [0.0, 0.0], []
    for ln in _scope_lines(pc, lines):
        k = ((ln.get("location") or {}).get("element_id"), ln["location"].get("floor"))
        cq = A308._carried(ln)
        entry = {"line_id": ln["line_id"], "element_id": k[0], "floor": k[1], "evidence_state": ln["evidence_state"],
                 "quantity": A302._q(A30._qty(ln)), "earlier_change": ln["line_id"] in earlier}
        if ln["evidence_state"] == "NOT_APPLICABLE_WITH_EVIDENCE":
            if k in keep or k in sup:
                raise InputsError(f"beam line {k}: already retired by an earlier version (carries nothing); it is "
                                  "neither kept nor superseded here")
            log["scope_lines"].append(dict(entry, accounted="ALREADY_RETIRED"))
            continue
        if k in keep:
            x = keep[k]
            live = ln["evidence_state"] in LIVE_EVIDENCE
            if ln["evidence_state"] == "BLOCKED_RFI" and x["carried"] == "BLOCKED" and x.get("run_status") == "HELD":
                seen.add(k)            # a held run the candidate already holds with no value: kept, never 0
                kept_none.append(x["run"])
                log["scope_lines"].append(dict(entry, accounted="KEPT", run=x["run"], why=x["why"]))
                continue
            if not (live or ln["evidence_state"] == "BOUNDED_EXPOSURE") or not A308._same(cq, x["carried"]) or \
                    isinstance(cq, (list, tuple)) == live:
                raise InputsError(f"beam line {k}: kept as run {x['run']} but carries {cq} "
                                  f"({ln['evidence_state']}), the inputs state {x['carried']}")
            if x.get("run_status") not in (("CALCULATED",) if live else ("CONFLICT", "HELD")):
                raise InputsError(f"beam line {k}: a {ln['evidence_state']} line is kept only for a run of the same "
                                  f"kind (run status {x.get('run_status')!r})")
            seen.add(k)
            if live:
                kept_value += float(cq)
            elif x["run_status"] == "CONFLICT":
                kept_conf[0] += float(cq[0])
                kept_conf[1] += float(cq[1])
            else:
                kept_held[0] += float(cq[0])
                kept_held[1] += float(cq[1])
            log["scope_lines"].append(dict(entry, accounted="KEPT", run=x["run"], why=x["why"]))
            continue
        if k not in sup:
            raise InputsError(f"beam line {ln['line_id']} ({k[0]} {k[1]}, {A302._q(A30._qty(ln))}) is inside the scope "
                              "and is neither kept as its run nor superseded: an integration that only adds is refused")
        x = sup[k]
        A308._check_replaceable(ln, earlier, x)
        if not A308._same(cq, x["carried"]):
            raise InputsError(f"beam line {k}: carries {cq}, the inputs state {x['carried']}: the superseded figure "
                              "must be the one the line carries")
        seen.add(k)
        if ln["evidence_state"] in LIVE_EVIDENCE:
            sup_value += float(cq)
        elif isinstance(cq, (list, tuple)):
            sup_low += float(cq[0])
            sup_high += float(cq[1])
        note = (f"{METHOD}: SUPERSEDED - {A302._q(A30._qty(ln))} {ln['unit']} (V3.0.11 state {ln['evidence_state']}) "
                f"replaced by beam run(s) of the checker-merged ledger {src['task']} (MERGED {src['merge_commit']}): "
                f"{x['why']}")
        codes = ["SUPERSEDED_BY_LEDGER_RUN"] + (["EARLIER_CHANGE"] if ln["line_id"] in earlier else [])
        changes.append(A307._retire(ln, x["why"], note, verif, "BEAM_LEDGER", codes,
                                    x.get("drawing_reference") or src["file"]))
        touched.add(ln["line_id"])
        log["scope_lines"].append(dict(entry, accounted="SUPERSEDED", why=x["why"], carried=cq,
                                       earlier_change_why=x.get("earlier_change")))
    missing = (set(keep) | set(sup)) - seen
    if missing:
        raise InputsError(f"piece BEAM_LEDGER: scope names line(s) the candidate does not have: {sorted(missing)}")
    measured, c_lo, c_hi, h_lo, h_hi, h_none = 0.0, 0.0, 0.0, 0.0, 0.0, []
    for r in pc["records"]:
        ln, evs = run_line(pid, rev, docs, pc, r)
        if ln["line_id"] in have:
            raise ValueError(f"{METHOD}: run {r['run']} repeats a candidate line id")
        have.add(ln["line_id"])
        held = []
        if ln["evidence_state"] == "SOURCE_DERIVED":
            measured += ln["measured_net"]
        else:
            rg = ln.get("bounded_range")
            if r["status"] == "CONFLICT":
                c_lo += rg["low"]
                c_hi += rg["high"]
            elif rg:
                h_lo += rg["low"]
                h_hi += rg["high"]
            else:
                h_none.append(r["run"])
            held = [{"what": f"beam run {r['run']} ({r['mark']})", "why": ln["rfi"]["question"],
                     "range": [rg["low"], rg["high"]] if rg else None}]
        changes.append(A305._change("BEAM_LEDGER", "ADD", None, ln, drawing_reference=str(r["source"])[:300],
                                    held=held, downstream=list(r.get("downstream") or ()),
                                    verification=dict(verif, record_verified_by=r.get("verified_by")),
                                    evidence_status=evs, codes=[f"RUN_{r['status']}"],
                                    guard_element=r["guard_element"]))
        log["records"].append({"run": r["run"], "line_id": ln["line_id"], "floor": r["floor"], "mark": r["mark"],
                               "status": r["status"], "evidence_state": ln["evidence_state"], "evidence_status": evs,
                               "quantity": ln["measured_net"], "range": ln.get("bounded_range"),
                               "supersedes": list(r.get("supersedes") or ()), "adjust": r.get("adjust") or []})
        log["evidence_status"][evs] = log["evidence_status"].get(evs, 0) + 1
    log["totals"] = {"measured": _r(measured + kept_value), "measured_added": _r(measured),
                     "kept": _r(kept_value), "superseded_value": _r(sup_value),
                     "superseded_bounded": [_r(sup_low), _r(sup_high)],
                     "conflict": [_r(c_lo + kept_conf[0]), _r(c_hi + kept_conf[1])],
                     "held": [_r(h_lo + kept_held[0]), _r(h_hi + kept_held[1])], "held_no_value": sorted(h_none + kept_none)}
    for k, v in (pc.get("declared_totals") or {}).items():
        got = log["totals"].get(k)
        if k == "held_no_value":
            ok = sorted(v) == got
        elif isinstance(v, (list, tuple)):
            ok = isinstance(got, list) and all(abs(a - b) <= 0.0006 for a, b in zip(got, v))
        else:
            ok = got is not None and abs(got - v) <= 0.0006
        if not ok:
            raise ValueError(f"{METHOD}: beam ledger {k} {got} != the declared {v}")
    log["declared_totals"] = pc.get("declared_totals") or {}
    return changes, log, touched


# ================================================================================================ slab faces
def slab_changes(pc, lines, earlier_changed=(), touched=()):
    """the SLAB_FACE_HOME piece on the V3.0.11 lines. -> (changes, log)"""
    earlier = set(earlier_changed)
    src = pc["source"]
    verif = {"task": src["task"], "merge_commit": src["merge_commit"], "verifier_run": src["checker_run"],
             "source": src["file"], "source_sha256": src["sha256"],
             "supporting": [{k: s.get(k) for k in ("task", "merge_commit", "checker_run", "file")}
                            for s in pc.get("sources") or ()]}
    log = {"piece": "SLAB_FACE_HOME", "state": "RUN", "source": src, "item_code": pc["item_code"], "faces": [],
           "by_floor": {}}
    changes, retired = [], set()
    for f in pc["faces"]:
        hit = [ln for ln in lines if ln["item_code"] == pc["item_code"] and ln["unit"] == pc["unit"]
               and (ln.get("location") or {}).get("element_id") == f["element_id"]
               and (ln.get("location") or {}).get("floor") == f["floor"]]
        if len(hit) != 1:
            raise InputsError(f"slab face {f['element_id']} {f['floor']}: found {len(hit)} candidate line(s); exactly "
                              "one")
        ln = hit[0]
        if ln["line_id"] in touched or ln["line_id"] in retired:
            raise ValueError(f"{METHOD}: line {ln['line_id']} changed twice")
        A308._check_replaceable(ln, earlier, f)
        if ln["evidence_state"] not in LIVE_EVIDENCE:
            raise InputsError(f"slab face {f['element_id']}: the line is {ln['evidence_state']}; only a live slab "
                              "line is moved out of the slab total here")
        cq = A308._carried(ln)
        if not A308._same(cq, f["carried"]):
            raise InputsError(f"slab face {f['element_id']}: carries {cq}, the inputs state {f['carried']}")
        h = f["home"]
        home = (f"beam run {h['run']} of this package" if h["kind"] == "BEAM_RUN" else
                f"no concrete ({h['evidence']})")
        why = f"face {f['face']} is not slab: {f['why']}; home: {home}"
        note = (f"{METHOD}: NOT SLAB - {A302._q(A30._qty(ln))} {ln['unit']} leaves the slab line ({src['task']}, MERGED "
                f"{src['merge_commit']}): {why}; figure kept as information, never summed")
        codes = ["SLAB_FACE_NOT_SLAB", f"HOME_{h['kind']}"] + ([f"COUNTED_BY {h['run']}"] if h["kind"] == "BEAM_RUN"
                                                              else [])
        changes.append(A307._retire(ln, why, note, verif, "SLAB_FACE_HOME", codes,
                                    f.get("drawing_reference") or src["file"]))
        retired.add(ln["line_id"])
        log["faces"].append({"line_id": ln["line_id"], "element_id": f["element_id"], "floor": f["floor"],
                             "face": f["face"], "t139_face": f.get("t139_face"), "was_m3": _r(cq), "home": h})
    # the slab line left on each floor = the slab ledger's hand figure
    for fl, d in pc["declared_after"].items():
        left = [ln for ln in lines if ln["item_code"] == pc["item_code"] and ln["unit"] == pc["unit"]
                and (ln.get("location") or {}).get("floor") == fl and ln["line_id"] not in retired]
        held = [ln["line_id"] for ln in left if ln["evidence_state"] not in LIVE_EVIDENCE
                and ln["evidence_state"] != "NOT_APPLICABLE_WITH_EVIDENCE"]
        if held:
            raise InputsError(f"slab floor {fl}: {len(held)} slab line(s) left that are not live: the slab ledger is "
                              "closable (no held component); state them before integrating")
        tot = sum(float(ln["measured_net"]) for ln in left if ln["evidence_state"] in LIVE_EVIDENCE)
        diff = tot - float(d["drawing"])
        if abs(diff) > float(d["tol_m3"]) + 1e-9:
            raise ValueError(f"{METHOD}: slab floor {fl} left {_r(tot)} != the slab ledger {d['drawing']} "
                             f"(+- {d['tol_m3']}): a face is missing or one too many")
        log["by_floor"][fl] = {"left_m3": _r(tot), "drawing_m3": d["drawing"], "residual_m3": _r(diff),
                               "residual_why": d.get("residual_why"),
                               "lines_left": sum(1 for ln in left if ln["evidence_state"] in LIVE_EVIDENCE),
                               "retired": sum(1 for x in log["faces"] if x["floor"] == fl)}
    log["totals"] = {"retired_m3": _r(sum(x["was_m3"] for x in log["faces"])),
                     "left_m3": _r(sum(v["left_m3"] for v in log["by_floor"].values())),
                     "drawing_m3": _r(sum(float(v["drawing_m3"]) for v in log["by_floor"].values())),
                     "to_beam_run": _r(sum(x["was_m3"] for x in log["faces"] if x["home"]["kind"] == "BEAM_RUN")),
                     "not_concrete": _r(sum(x["was_m3"] for x in log["faces"]
                                            if x["home"]["kind"] == "NOT_CONCRETE"))}
    return changes, log


# ================================================================================================ integrate / write
def changes_for(inputs, l3011, earlier_changed=()):
    """the beam ledger, the slab faces, then the guard re-check over the result. -> (changes, logs)"""
    if not inputs or not inputs.get("pieces"):
        logs = [{"piece": p, "state": "NO_PROJECT_INPUT"} for p in ("BEAM_LEDGER", "SLAB_FACE_HOME")]
        ch_g, log_g = A307.guard_changes(inputs, l3011, [], set())
        return ch_g, logs + [log_g]
    by = {pc["piece"]: pc for pc in inputs["pieces"]}
    ch, logs, touched = [], [], set()
    if "BEAM_LEDGER" in by:
        c, lg, t = beam_changes(by["BEAM_LEDGER"], l3011, earlier_changed)
        ch += c
        logs.append(lg)
        touched |= t
    if "SLAB_FACE_HOME" in by:
        c, lg = slab_changes(by["SLAB_FACE_HOME"], l3011, earlier_changed, touched)
        ch += c
        logs.append(lg)
    rep = {c["before"]["line_id"]: c["after"] for c in ch if c["action"] == "REPLACE"}
    view = [rep.get(ln["line_id"], ln) for ln in l3011]
    ch_g, log_g = A307.guard_changes(inputs, view, [c for c in ch if c["action"] == "ADD"], set(rep))
    for c in ch_g:   # a guard hold written by the V3.0.7 code is this version's row
        A305._note(c["after"], f"(re-check run by {METHOD})")
    return ch + ch_g, logs + [log_g]


def check_partition(lines):
    """on finished lines: no beam-ledger run twice, no retired slab face counted, every slab face sent to a beam run
    has that run in the lines. -> {"runs": n, "faces_to_beam": n}"""
    runs, faces = {}, []
    for ln in lines:
        inp = (ln.get("calculation") or {}).get("inputs") or {}
        if inp.get("policy") == PIECES["BEAM_LEDGER"]["policy"] and ln["evidence_state"] != \
                "NOT_APPLICABLE_WITH_EVIDENCE":
            run = inp.get("run")
            if run in runs:
                raise ValueError(f"{METHOD}: beam run {run} appears twice")
            runs[run] = ln
    return {"runs": len(runs), "faces_to_beam": len(faces)}


def integrate(l3011, v3012_changes):
    """-> (V3.0.12 lines, identity). Every line outside the V3.0.12 rows is byte-identical to the V3.0.11 line."""
    from engine.source import boq_line as BL
    sid = {ln["line_id"] for ln in l3011}
    rep, adds = {}, []
    for c in v3012_changes:
        if c["action"] == "REPLACE":
            lid = c["before"]["line_id"]
            if lid in rep:
                raise ValueError(f"{METHOD}: line {lid} changed twice")
            if lid not in sid:
                raise ValueError(f"{METHOD}: a change names a line the V3.0.11 run does not have")
            if c["after"]["line_id"] != lid:
                raise ValueError(f"{METHOD}: a changed line keeps its line id")
            rep[lid] = c["after"]
        elif c["action"] == "ADD":
            if c["after"]["line_id"] in sid:
                raise ValueError(f"{METHOD}: an added line repeats a V3.0.11 line id")
            adds.append(c["after"])
        else:
            raise ValueError(f"{METHOD}: action {c['action']}")
    out = [rep.get(ln["line_id"], ln) for ln in l3011] + adds
    if len({ln["line_id"] for ln in out}) != len(out):
        raise ValueError(f"{METHOD}: a BOQ line id appears twice")
    for ln in out:
        BL.validate(ln)
    A3011.check_conflicts(out)
    A3010.check_same_openings(out)
    part = check_partition(out)
    by11 = {ln["line_id"]: ln for ln in l3011}
    touched = set(rep) | {a["line_id"] for a in adds}
    outside = [ln for ln in out if ln["line_id"] not in touched]
    bad = [ln["line_id"] for ln in outside if A30.line_sha(by11[ln["line_id"]]) != A30.line_sha(ln)]
    if bad or len(outside) + len(rep) != len(l3011):
        raise ValueError(f"{METHOD}: {len(bad)} line(s) outside the V3.0.12 rows differ from {EXTENDS}")
    ident = {"v3_0_11_lines": len(l3011), "v3_0_12_lines": len(out), "v3_0_12_rows": len(v3012_changes),
             "replaced": len(rep), "added": len(adds), "outside_rows": len(outside),
             "outside_rows_identical_to_v3_0_11": len(outside), "beam_runs": part["runs"],
             "outside_rows_sha256": hashlib.sha256("".join(A30.line_sha(x) for x in outside).encode()).hexdigest()}
    return out, ident


def ledger_rows(changes, released_lines=None):
    rel = {A30._key(ln): ln for ln in released_lines or ()}
    rows = []
    for c in changes:
        ref = c["after"] if c["before"] is None else c["before"]
        b11 = A30._qty(c["before"]) if c["before"] is not None else dict(A30._qty(None), state="NOT_IN_V3_0_11")
        b29 = None
        if released_lines is not None:
            b29 = A30._qty(rel[A30._key(ref)]) if A30._key(ref) in rel else dict(A30._qty(None),
                                                                                 state="NOT_IN_RELEASED")
        p = PIECES[c["piece"]]
        loc = ref.get("location") or {}
        rows.append({"version": METHOD, "piece": c["piece"], "action": c["action"], "line_id": ref["line_id"],
                     "item_code": ref["item_code"], "floor": loc.get("floor"), "room_id": loc.get("room_id"),
                     "element_id": c["after"]["location"].get("element_id"), "unit": c["after"]["unit"],
                     "before_released_v2_9": b29, "before_v3_0_11": b11, "after_v3_0_12": A30._qty(c["after"]),
                     "evidence_status": c.get("evidence_status") or "HELD", "release_status": "NOT RELEASED",
                     "codes": c.get("codes") or [], "citations": c.get("citations") or [],
                     "drawing_reference": c.get("drawing_reference"),
                     "owner_manual_method": p["owner_manual_method"], "drawing_method": p["drawing_method"],
                     "owner_rules": p["owner_rules"],
                     "verification": dict(c.get("verification") or {}, module=p["module"], policy=p["policy"]),
                     "held": c.get("held") or [], "downstream": c.get("downstream") or [], "rollback": ROLLBACK})
    return rows


LEDGER_CSV = ("version", "piece", "action", "line_id", "item_code", "floor", "room_id", "element_id", "unit", "v2_9",
              "v3_0_11", "v3_0_12", "evidence_status", "release_status", "codes", "drawing_reference", "verification",
              "held")


def ledger_csv(rows):
    return A305._csv([{"version": r["version"], "piece": r["piece"], "action": r["action"], "line_id": r["line_id"],
                       "item_code": r["item_code"], "floor": r["floor"], "room_id": r["room_id"],
                       "element_id": r["element_id"], "unit": r["unit"], "v2_9": A302._q(r["before_released_v2_9"]),
                       "v3_0_11": A302._q(r["before_v3_0_11"]), "v3_0_12": A302._q(r["after_v3_0_12"]),
                       "evidence_status": r["evidence_status"], "release_status": r["release_status"],
                       "codes": " ".join(r["codes"]), "drawing_reference": str(r["drawing_reference"])[:300],
                       "verification": f"{r['verification'].get('task')} {r['verification'].get('merge_commit')}",
                       "held": "; ".join(str(h.get("why") or h.get("what")) for h in r["held"])[:600]}
                      for r in rows], LEDGER_CSV)


DIFF_CSV = ("line_id", "item_code", "floor", "element_id", "unit", "vs_v3_0_11", "vs_released_v2_9", "v2_9",
            "v3_0_11", "v3_0_12")


def diff_rows(l3011, l3012, released_lines=None):
    b11 = {ln["line_id"]: ln for ln in l3011}
    rel = {A30._key(ln): ln for ln in released_lines or ()}
    out = []
    for ln in l3012:
        o = b11.get(ln["line_id"])
        vs = "ADDED" if o is None else ("SAME" if A30.line_sha(o) == A30.line_sha(ln) else "CHANGED")
        r = rel.get(A30._key(ln)) if released_lines is not None else None
        vs29 = None if released_lines is None else ("NOT_IN_RELEASED" if r is None else
                                                    ("SAME_QUANTITY" if A30._qty(r) == A30._qty(ln) else
                                                     "QUANTITY_DIFFERS"))
        out.append({"line_id": ln["line_id"], "item_code": ln["item_code"], "floor": ln["location"].get("floor"),
                    "element_id": ln["location"].get("element_id"), "unit": ln["unit"], "vs_v3_0_11": vs,
                    "vs_released_v2_9": vs29, "v2_9": A302._q(A30._qty(r)) if r else "",
                    "v3_0_11": A302._q(A30._qty(o)) if o else "", "v3_0_12": A302._q(A30._qty(ln))})
    return out


def item_summary(lines, item_codes=("STR.CONC.SLAB", "STR.CONC.BEAM")):
    """per item and floor: live total, bounded low / high, blocked count (held never summed as 0)."""
    out = {}
    for ln in lines:
        if ln["item_code"] not in item_codes:
            continue
        d = out.setdefault(ln["item_code"], {}).setdefault((ln.get("location") or {}).get("floor"),
                                                           {"live": 0.0, "low": 0.0, "high": 0.0, "blocked": 0,
                                                            "n_live": 0})
        ev = ln["evidence_state"]
        if ev in LIVE_EVIDENCE and ln.get("measured_net") is not None:
            d["live"] += float(ln["measured_net"])
            d["n_live"] += 1
        elif ev == "BOUNDED_EXPOSURE":
            d["low"] += float(ln["bounded_range"]["low"])
            d["high"] += float(ln["bounded_range"]["high"])
        elif ev != "NOT_APPLICABLE_WITH_EVIDENCE":
            d["blocked"] += 1
    return {k: {f: {kk: (_r(vv) if isinstance(vv, float) else vv) for kk, vv in d.items()} for f, d in v.items()}
            for k, v in out.items()}


def write(out, l3011, v3012_changes, logs, inputs, released_lines=None):
    """the V3_0_12_* files beside the V3_0_11_* files. -> (file names, identity, ledger)."""
    from pathlib import Path
    from engine.source import boq_line as BL
    out = Path(out)
    l3012, ident = integrate(l3011, v3012_changes)
    rows = ledger_rows(v3012_changes, released_lines)
    diff = diff_rows(l3011, l3012, released_lines)
    dsum = {}
    for d in diff:
        dsum.setdefault("vs_v3_0_11", {}).setdefault(d["vs_v3_0_11"], 0)
        dsum["vs_v3_0_11"][d["vs_v3_0_11"]] += 1
        if d["vs_released_v2_9"] is not None:
            dsum.setdefault("vs_released_v2_9", {}).setdefault(d["vs_released_v2_9"], 0)
            dsum["vs_released_v2_9"][d["vs_released_v2_9"]] += 1
    ident = dict(ident, diff=dsum)
    led = {"schema": LEDGER_SCHEMA, "method": METHOD, "extends": EXTENDS, "candidate": CANDIDATE,
           "base": A30.BASE_METHOD, "released": A30.RELEASED_METHOD, "released_default": False, "rows": rows,
           "waiting_pieces": WAITING, "integration_package": True}
    t11, t12 = A304.code_totals(l3011), A304.code_totals(l3012)
    moved = {k: {"v3_0_11": t11.get(k), "v3_0_12": t12.get(k)} for k in sorted(set(t11) | set(t12))
             if t11.get(k) != t12.get(k)}
    g = (inputs or {}).get("guard") or {}
    run = {"method": METHOD, "policy": POLICY_ID, "extends": EXTENDS, "candidate": CANDIDATE,
           "base_method": A30.BASE_METHOD, "released_method": A30.RELEASED_METHOD, "released_default": False,
           "rollback": ROLLBACK, "identity": ident, "pieces": PIECES, "piece_logs": logs,
           "inputs": {"pieces": [{k: pc.get(k) for k in ("piece", "source", "sources", "declared_totals",
                                                         "declared_after")}
                                 for pc in (inputs or {}).get("pieces") or ()],
                      "guard": {k: g.get(k) for k in ("source", "evidence_file", "evidence_sha256", "conventions_file",
                                                      "conventions_sha256", "holding_checks", "recorded_checks",
                                                      "equal_value_rebase", "new_records")}},
           "totals_moved_by_code": moved, "waiting_pieces": WAITING,
           "items_v3_0_11": item_summary(l3011), "items_v3_0_12": item_summary(l3012),
           "evidence_status_counts": A302._count(r["evidence_status"] for r in rows)}
    files = {"V3_0_12_BOQ_LINES.json": BL.dumps(l3012),
             "V3_0_12_BOQ_LINES.csv": A30._lines_csv(l3012),
             "V3_0_12_INTEGRATION_LEDGER.json": A30._j(led),
             "V3_0_12_INTEGRATION_LEDGER.csv": ledger_csv(rows),
             "V3_0_12_DIFF.csv": A305._csv(diff, DIFF_CSV),
             "V3_0_12_RUN.json": A30._j(run)}
    for name, text in files.items():
        (out / name).write_text(text, encoding="utf-8")
    return sorted(files), ident, led


def policy_record():
    return {"method": METHOD, "extends": EXTENDS, "pieces": sorted(PIECES), "inputs_schema": INPUTS_SCHEMA,
            "released_default": False, "rollback": ROLLBACK}


__all__ = ["METHOD", "PIECES", "WAITING", "DEFAULT_GUARD_CLASS", "load_inputs", "beam_changes", "slab_changes",
           "changes_for", "integrate", "check_partition", "ledger_rows", "diff_rows", "item_summary", "write",
           "InputsError"]
