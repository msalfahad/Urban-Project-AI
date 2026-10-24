"""ARCH_TAKEOFF_V3.0.11 (T-239): the SAME opt-in BOQ candidate as ARCH_TAKEOFF_V3.0 .. V3.0.10 (engine.source.arch_v30,
arch_v301 .. arch_v3010), extended with one integration fix: a footing outline that carries MORE THAN ONE footing tag is
a CONFLICT that carries every drawing-supported reading, never one tag. Not a new method family and not the released
default (owner management decision 2026-10-20 sections 2 and 5); rollback is running the released ARCH_TAKEOFF_V2.9.

The physical question (ERS 2026-10-22 s.2.1): one drawn footing outline with two schedule tags describes either the
footings of the schedule rows as printed (reading A: the sum of L x W x H of each tagged row) or one combined footing
cast to the drawn outline (reading B: the outline area at the DEEPEST tagged depth; a shallower single depth would leave
the deeper type's printed depth unbuilt under its own column, contradicting that type's schedule row, so it is not a
reading). The drawings do not say which; the engine never chooses. Its blinding follows it: reading A = the sum of each
row grown by the blinding projection each side, reading B = the outline grown the same, both x the printed thickness.

How it is built (tools/urban_boq_m9.py `arch --method ARCH_TAKEOFF_V3.0.11`):
  1. the run is the V3.0.10 candidate exactly: its V3_0_* .. V3_0_10_* files are written unchanged (arch_v30 ..
     arch_v3010 are not edited);
  2. CONFLICT RECORDS (piece MULTI_TAG_OUTLINE, project inputs URBAN_V3011_INPUTS_V1): one record per drawn outline that
     carries two or more footing tags, from a checker-merged footing ledger (source file sha256, task, merge commit and
     checker run). The record carries the outline (its two sides and area), each tag's schedule row (L, W, H) and the
     blinding projection and thickness with their printed sources. The module RECOMPUTES both readings for the footing
     and for its blinding from these values; a stated reading that differs from the recomputed one is refused, as is a
     record with fewer than two tags or fewer than two readings (one tag picked), or a stated range that excludes a
     reading;
  3. each record names the ONE candidate footing line and the ONE candidate blinding line of that outline (item code,
     floor, element id, unit m3) and the figure each carries now (asserted against the line). Both lines are REPLACED
     in place (same line id): evidence state BOUNDED_EXPOSURE, low / high = the smallest / largest reading, every reading
     with its basis and source in the line's inputs, evidence status HELD (WORKFLOW_CONTROLS s.5), never MEASURED, never
     one reading, never 0. The blinding of a held footing is never released (refused). The owner's Q-31 C provisional
     view (the bigger footing reading, marked PROVISIONAL and flagged) is written on the line as information only and is
     never in a total; the blinding's provisional view follows the footing's reading, not the larger blinding figure;
  4. GUARD RE-CHECK (piece DEFAULT_GUARD): the merged guard runs again over the V3.0.11 lines with the guard inputs of
     V3.0.7 (arch_v307.guard_changes);
  5. the V3_0_11_* files are written beside them: every line outside the V3.0.11 rows is byte-identical to the V3.0.10
     line (asserted on every run), and V3_0_11_DIFF.csv lists every line against V3.0.10 and against the released V2.9.

Rules: Q-31 C (owner 2026-10-19: hold, RFI to the designer, flag in the final BOQ; the bigger reading only as an
explicit PROVISIONAL view); the no-assumptions rule (a CONFLICT is never picked; held is a range, never 0;
UP-QTY-STATUS-001); R-CONC-OWN-1 (one owner per piece of concrete); WORKFLOW_CONTROLS 2026-10-21 s.4 / s.5; ERS
2026-10-22 s.2.1, s.2.2, s.3, s.7. Nothing here names a project, a sheet, a layer, a coordinate or a client; every
number comes from the run or the inputs.
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

DEFAULT_GUARD_CLASS = "GUARD_HOST"      # T-212: a candidate method; it reaches the guard through arch_v307
METHOD = "ARCH_TAKEOFF_V3.0.11"
EXTENDS = A3010.METHOD
CANDIDATE = A30.METHOD                  # the candidate family this version extends (never a new method family)
POLICY_ID = "URBAN_BOQ_T239_ARCH_V3_0_11"
LEDGER_SCHEMA = "URBAN_V3011_INTEGRATION_LEDGER_V1"
INPUTS_SCHEMA = "URBAN_V3011_INPUTS_V1"
ROLLBACK = A30.ROLLBACK
READINGS = ("ROWS_SEPARATELY", "OUTLINE_AT_DEEPEST_DEPTH")
COMPONENTS = ("footing", "blinding")
LIVE_EVIDENCE = A307.LIVE_EVIDENCE
TOL_M3 = 1e-6                           # stated vs recomputed reading (both from the same printed values)
TOL_M = 0.005                           # outline sides vs its stated area (5 mm, the footing ledger's tolerance)
MAX_DIM_M = 20.0                        # a footing dimension above this is a unit slip (mm given as m), refused
InputsError = A307.InputsError
_num = A307._num

PIECES = {
    "MULTI_TAG_OUTLINE": {
        "module": "engine/source/arch_v3011.py (a footing outline with two or more tags: CONFLICT with every reading)",
        "policy": "MULTI_TAG_OUTLINE_CONFLICT_V1", "rule_id": "Q-31", "rule_version": "owner-2026-10-19",
        "owner_rules": ["Q-31 C (owner 2026-10-19: one outline with two footing tags is HELD with a request for "
                        "information to the designer and flagged in the final BOQ; the bigger reading only as an "
                        "explicit PROVISIONAL view, never by default)",
                        "no-assumptions rule (MISSION.md; WORKFLOW_CONTROLS s.4): a CONFLICT is never picked",
                        "UP-QTY-STATUS-001 (a held quantity is a range or blocked, never 0)",
                        "R-CONC-OWN-1 (each piece of concrete has one owner; the blinding follows its footing)"],
        "owner_manual_method": "manual QS footing schedule: one row per footing type, L x W x H from the schedule, "
                               "times the number of that type on the plan; blinding = (L + 2 x projection) x (W + 2 x "
                               "projection) x thickness under each footing",
        "drawing_method": "each footing from its drawn outline on the foundation plan checked against its schedule row; "
                          "an outline carrying two tags has no own schedule row: both readings (rows as printed; the "
                          "outline at the deepest tagged depth) are carried, the blinding grown from each"},
    "DEFAULT_GUARD": A307.PIECES["DEFAULT_GUARD"],
}
WAITING = dict(A3010.WAITING)
WAITING.update({
    "MULTI_TAG_OUTLINE_DESIGNER_ANSWER": "the designer's answer to the two-tag outline (one combined footing, or the "
                                         "schedule rows separately): until then the footing and its blinding stay "
                                         "HELD as the range of both readings (owner Q-31 C)",
    "BLINDING_PLOT_LINE_CLIP": "the blinding projection beyond the plot line (designer item D-14) is held by its own "
                               "item: the conflict range is stated before that clip, as for every other footing's "
                               "blinding in the candidate; the in-plot figure of the outline reading is information",
})


def _r(x, n=6):
    return None if x is None else round(float(x), n)


# ================================================================================================ readings
def _pos(x, what):
    if not (_num(x) and x > 0):
        raise InputsError(f"{what}: a dimension > 0 is required (missing is never 0)")
    if x > MAX_DIM_M:
        raise InputsError(f"{what}: {x} m is not a footing dimension (unit slip? metres only)")
    return float(x)


def readings_of(rec):
    """the two readings of one multi-tag outline, recomputed from its printed values.
    -> {"footing": {reading: m3}, "blinding": {reading: m3}, "blinding_m2": {reading: m2}, "deepest_tag": tag}"""
    oid = rec.get("outline")
    tags = rec.get("tags")
    if not (isinstance(tags, list) and len(tags) >= 2 and len(set(tags)) == len(tags) and all(tags)):
        raise InputsError(f"outline {oid}: a multi-tag record carries two or more distinct tags (one tag is not a "
                          "conflict and is never this piece)")
    rows = rec.get("schedule") or {}
    if set(rows) != set(tags):
        raise InputsError(f"outline {oid}: every tag needs its schedule row and no other row ({sorted(rows)} vs "
                          f"{sorted(tags)}); a tag without a row is HELD by its own cause, not this piece")
    dims = {}
    for t in tags:
        r = rows[t]
        if not r.get("source"):
            raise InputsError(f"outline {oid}: schedule row {t} names its printed source")
        dims[t] = (_pos(r.get("L"), f"{oid} {t} L"), _pos(r.get("W"), f"{oid} {t} W"), _pos(r.get("H"), f"{oid} {t} H"))
    d = rec.get("drawn") or {}
    a, b, area = _pos(d.get("a"), f"{oid} drawn a"), _pos(d.get("b"), f"{oid} drawn b"), _pos(d.get("area"),
                                                                                              f"{oid} drawn area")
    if not d.get("source"):
        raise InputsError(f"outline {oid}: the drawn outline names its source (entity / sheet)")
    if d.get("rectangular") is not True:
        raise InputsError(f"outline {oid}: only a rectangular outline is grown by its sides here (state rectangular)")
    if abs(a * b - area) > TOL_M * max(a, b):
        raise InputsError(f"outline {oid}: area {area} != {a} x {b} (a rectangular outline)")
    bl = rec.get("blinding") or {}
    p = _pos(bl.get("projection_m"), f"{oid} blinding projection")
    th = _pos(bl.get("thickness_m"), f"{oid} blinding thickness")
    if not bl.get("source"):
        raise InputsError(f"outline {oid}: the blinding projection and thickness name their printed source")
    deepest = max(tags, key=lambda t: (dims[t][2], t))
    h_max = dims[deepest][2]
    foot = {"ROWS_SEPARATELY": sum(L * W * H for L, W, H in dims.values()),
            "OUTLINE_AT_DEEPEST_DEPTH": area * h_max}
    m2 = {"ROWS_SEPARATELY": sum((L + 2 * p) * (W + 2 * p) for L, W, _H in dims.values()),
          "OUTLINE_AT_DEEPEST_DEPTH": (a + 2 * p) * (b + 2 * p)}
    blind = {k: v * th for k, v in m2.items()}
    return {"footing": foot, "blinding": blind, "blinding_m2": m2, "deepest_tag": deepest}


def _check_stated(rec, comp, got):
    """the record's stated readings for one component equal the recomputed ones; its range covers them all."""
    oid = rec.get("outline")
    c = rec.get(comp) or {}
    st = c.get("readings") or {}
    if set(st) != set(READINGS):
        raise InputsError(f"outline {oid} {comp}: both readings {READINGS} are stated (a single reading is a tag "
                          "picked, refused)")
    for k in READINGS:
        if not (_num(st[k]) and st[k] > 0):
            raise InputsError(f"outline {oid} {comp}: reading {k} > 0 (missing is never 0)")
        if abs(float(st[k]) - got[k]) > TOL_M3:
            raise InputsError(f"outline {oid} {comp}: stated {k} {st[k]} != recomputed {_r(got[k])} from the printed "
                              "values")
    rg = c.get("range")
    if rg is not None:
        lo, hi = min(got.values()), max(got.values())
        if not (isinstance(rg, (list, tuple)) and len(rg) == 2 and all(_num(x) for x in rg)):
            raise InputsError(f"outline {oid} {comp}: range is [low, high]")
        if rg[0] > lo + TOL_M3 or rg[1] < hi - TOL_M3:
            raise InputsError(f"outline {oid} {comp}: range {list(rg)} excludes a reading ({_r(lo)} .. {_r(hi)})")
        if abs(rg[0] - lo) > TOL_M3 or abs(rg[1] - hi) > TOL_M3:
            raise InputsError(f"outline {oid} {comp}: range {list(rg)} is not the smallest / largest reading "
                              f"({_r(lo)} .. {_r(hi)}): no figure outside the readings is added")
    if c.get("state") not in (None, "HELD"):
        raise InputsError(f"outline {oid} {comp}: a conflict is HELD (state {c.get('state')!r}); the "
                          + ("blinding of a held footing is never released" if comp == "blinding" else
                             "footing is never released on one reading"))


def _check_line_ref(rec, comp):
    oid = rec.get("outline")
    c = rec.get(comp) or {}
    for k in ("item_code", "floor", "element_id", "carried", "why"):
        if c.get(k) in (None, ""):
            raise InputsError(f"outline {oid} {comp}: {k} is required (the candidate line it replaces and the figure "
                              "it carries now)")
    if c.get("unit", "m3") != "m3":
        raise InputsError(f"outline {oid} {comp}: unit m3")
    for d in c.get("downstream") or ():
        if not (isinstance(d, dict) and d.get("line_id") and d.get("element_id") and d.get("why")):
            raise InputsError(f"outline {oid} {comp}: a downstream entry names the dependent line (line_id, "
                              "element_id) and why it depends on this outline")


def load_inputs(doc, project_id=None):
    """URBAN_V3011_INPUTS_V1 or None:
        {"schema", "project",
         "pieces": [{"piece": "MULTI_TAG_OUTLINE", "source": {file, sha256, task, merge_commit, checker_run},
                     "sources": [...],
                     "records": [{"outline", "tags", "floor", "owner_item", "reasons": [...],
                                  "schedule": {tag: {L, W, H, source}}, "drawn": {a, b, area, rectangular, source},
                                  "blinding": {projection_m, thickness_m, source},
                                  "footing":  {item_code, floor, element_id, unit, carried, why, earlier_change,
                                               readings: {ROWS_SEPARATELY, OUTLINE_AT_DEEPEST_DEPTH}, range, state},
                                  "blinding_line": {... the same for the blinding line ...},
                                  "provisional_view": "OUTLINE_AT_DEEPEST_DEPTH" | "ROWS_SEPARATELY" (Q-31 C: the
                                                      bigger footing reading, information only),
                                  "info": {...}}],
                     "declared": {"footing": [low, high], "blinding": [low, high]}}],
         "guard": as URBAN_V307_INPUTS_V1 "guard"}"""
    if doc is None:
        return None
    if doc.get("schema") != INPUTS_SCHEMA:
        raise InputsError(f"project inputs: schema must be {INPUTS_SCHEMA}")
    if project_id and doc.get("project") not in (None, project_id):
        raise InputsError(f"project inputs are for {doc.get('project')!r}, the run is {project_id!r}")
    seen = set()
    for pc in doc.get("pieces") or ():
        p = pc.get("piece")
        if p != "MULTI_TAG_OUTLINE" or p in seen:
            raise InputsError(f"piece {p!r}: MULTI_TAG_OUTLINE, once")
        seen.add(p)
        A307._source(pc.get("source"), f"piece {p}")
        for s in pc.get("sources") or ():
            A307._source(s, f"piece {p} (supporting source)")
        recs = pc.get("records") or ()
        if not recs:
            raise InputsError(f"piece {p}: no records")
        ids = set()
        for rec in recs:
            if not rec.get("outline") or rec["outline"] in ids:
                raise InputsError(f"piece {p}: every record names its outline, once")
            ids.add(rec["outline"])
            if not rec.get("reasons") or not rec.get("owner_item"):
                raise InputsError(f"piece {p} {rec['outline']}: reasons and the owner / designer item are required")
            got = readings_of(rec)
            _check_stated(rec, "footing", got["footing"])
            _check_stated(dict(rec, blinding=rec.get("blinding_line")), "blinding", got["blinding"])
            _check_line_ref(rec, "footing")
            _check_line_ref(dict(rec, blinding=rec.get("blinding_line")), "blinding")
            pv = rec.get("provisional_view")
            if pv is not None:
                big = max(READINGS, key=lambda k: (got["footing"][k], k))
                if pv != big:
                    raise InputsError(f"outline {rec['outline']}: Q-31 C allows the BIGGER footing reading ({big}) as "
                                      f"the provisional view, not {pv}")
    g = doc.get("guard")
    if g is not None:
        A307.load_inputs({"schema": A307.INPUTS_SCHEMA, "project": doc.get("project"), "guard": g}, project_id)
    return doc


# ================================================================================================ changes
def _find(lines, c, oid, comp):
    hit = [ln for ln in lines if ln["item_code"] == c["item_code"] and ln["unit"] == c.get("unit", "m3")
           and (ln.get("location") or {}).get("element_id") == c["element_id"]
           and (ln.get("location") or {}).get("floor") == c["floor"]]
    if len(hit) != 1:
        raise InputsError(f"outline {oid} {comp}: candidate line {c['element_id']} {c['floor']} {c['item_code']} "
                          f"found {len(hit)} time(s); exactly one")
    return hit[0]


def _conflict_line(ln, oid, comp, got, rec, src, view):
    lo, hi = min(got.values()), max(got.values())
    reasons = list(rec["reasons"])
    after = copy.deepcopy(ln)
    basis = (f"CONFLICT, outline {oid} tags {'+'.join(rec['tags'])}: " + "; ".join(
        f"{k} {_r(got[k], 4)}" for k in READINGS) + f" ({rec['owner_item']})")
    q = (f"outline {oid} carries {len(rec['tags'])} footing tags ({', '.join(rec['tags'])}): one combined footing to "
         f"the drawn outline, or the schedule rows as printed? " + "; ".join(reasons))
    after.update(evidence_state="BOUNDED_EXPOSURE", measured_net=None, gross=None,
                 bounded_range={"low": _r(lo), "high": _r(hi), "basis": basis[:300]},
                 rfi={"question": q[:900], "unlocks": (ln.get("location") or {}).get("element_id")})
    calc = dict(after.get("calculation") or {})
    calc["formula"] = ("CONFLICT (held, never one reading): " + " | ".join(
        f"{k} = {_r(got[k], 4)}" for k in READINGS) + f" -> range {_r(lo, 4)} .. {_r(hi, 4)} m3")[:600]
    calc["inputs"] = dict(calc.get("inputs") or {}, multi_tag_outline_v3011={
        "policy": PIECES["MULTI_TAG_OUTLINE"]["policy"], "component": comp, "outline": oid, "tags": rec["tags"],
        "status": "CONFLICT", "evidence_status": "HELD", "readings": {k: _r(got[k]) for k in READINGS},
        "reading_basis": {
            "ROWS_SEPARATELY": "each tagged schedule row as printed, L x W x H" + (
                " grown by the projection each side x thickness" if comp == "blinding" else ""),
            "OUTLINE_AT_DEEPEST_DEPTH": "the drawn outline at the deepest tagged depth" + (
                " grown by the projection each side x thickness" if comp == "blinding" else "")},
        "schedule": rec["schedule"], "drawn": rec["drawn"],
        "blinding": rec["blinding"] if comp == "blinding" else None,
        "provisional_view": None if view is None else {
            "reading": view, "value": _r(got[view]), "status": "PROVISIONAL (owner Q-31 C), information only: "
                                                               "never in a total, flagged in the final BOQ"},
        "info_qty_v3_0_10": A30._qty(ln), "owner_item": rec["owner_item"], "reasons": reasons,
        "info": rec.get("info"), "source": src["file"], "task": src["task"]})
    after["calculation"] = calc
    A305._note(after, f"{METHOD}: HELD CONFLICT - outline {oid} carries tags {'+'.join(rec['tags'])}; range "
                      f"{_r(lo, 4)} .. {_r(hi, 4)} m3 of both readings ({src['task']}, MERGED {src['merge_commit']}); "
                      f"V3.0.10 figure {A302._q(A30._qty(ln))} kept as information, never summed")
    return after, lo, hi


def record_changes(inputs, lines, earlier_changed=()):
    """the MULTI_TAG_OUTLINE piece on the V3.0.10 lines. -> (changes, logs)"""
    if not inputs or not inputs.get("pieces"):
        return [], [{"piece": "MULTI_TAG_OUTLINE", "state": "NO_PROJECT_INPUT"}]
    earlier = set(earlier_changed)
    changes, logs, touched = [], [], set()
    for pc in inputs["pieces"]:
        src = pc["source"]
        verif = {"task": src["task"], "merge_commit": src["merge_commit"], "verifier_run": src["checker_run"],
                 "source": src["file"], "source_sha256": src["sha256"],
                 "supporting": [{k: s.get(k) for k in ("task", "merge_commit", "checker_run", "file")}
                                for s in pc.get("sources") or ()]}
        log = {"piece": "MULTI_TAG_OUTLINE", "state": "RUN", "source": src, "sources": pc.get("sources") or [],
               "records": [], "totals": {"footing": [0.0, 0.0], "blinding": [0.0, 0.0]}, "released_moved": {}}
        for rec in pc["records"]:
            oid = rec["outline"]
            got = readings_of(rec)
            view = rec.get("provisional_view")
            entry = {"outline": oid, "tags": rec["tags"], "owner_item": rec["owner_item"],
                     "deepest_tag": got["deepest_tag"],
                     "blinding_m2": {k: _r(v, 4) for k, v in got["blinding_m2"].items()}}
            for comp, key in (("footing", "footing"), ("blinding", "blinding_line")):
                c = rec[key]
                ln = _find(lines, c, oid, comp)
                if ln["line_id"] in touched:
                    raise ValueError(f"{METHOD}: line {ln['line_id']} changed twice")
                A308._check_replaceable(ln, earlier, c)
                cq = A308._carried(ln)
                if not A308._same(cq, c["carried"]):
                    raise InputsError(f"outline {oid} {comp}: line {c['element_id']} carries {cq}, the inputs state "
                                      f"{c['carried']}: the replaced figure must be the one the line carries")
                cview = view
                byid = {x["line_id"]: x for x in lines}
                for d in c.get("downstream") or ():
                    dl = byid.get(d["line_id"])
                    if dl is None or (dl.get("location") or {}).get("element_id") != d["element_id"]:
                        raise InputsError(f"outline {oid} {comp}: downstream line {d['element_id']} is not in the "
                                          "candidate under that line id")
                    if dl["evidence_state"] in LIVE_EVIDENCE:
                        raise InputsError(f"outline {oid} {comp}: downstream line {d['element_id']} is released "
                                          f"({dl['evidence_state']}) while the outline it depends on is a CONFLICT: "
                                          "a quantity resting on a held element is never released")
                after, lo, hi = _conflict_line(ln, oid, comp, got[comp], rec, src, cview)
                live = ln["evidence_state"] in LIVE_EVIDENCE and ln.get("measured_net") is not None
                moved = -float(ln["measured_net"]) if live else 0.0
                why = (f"CONFLICT: outline {oid} carries tags {'+'.join(rec['tags'])}; {c['why']}; "
                       f"{rec['owner_item']}")
                changes.append(A305._change(
                    "MULTI_TAG_OUTLINE", "REPLACE", ln, after, drawing_reference=str(rec["drawn"]["source"])[:300],
                    held=[{"what": f"{ln['item_code']} {c['element_id']} {c['floor']}", "why": why[:900],
                           "range": [_r(lo), _r(hi)]}], downstream=list(c.get("downstream") or ()),
                    verification=verif, evidence_status="HELD",
                    codes=["MULTI_TAG_CONFLICT", rec["owner_item"]] + (
                        ["EARLIER_CHANGE"] if ln["line_id"] in earlier else []), why=why))
                touched.add(ln["line_id"])
                t = log["totals"][comp]
                t[0] += lo
                t[1] += hi
                log["released_moved"][comp] = _r(log["released_moved"].get(comp, 0.0) + moved)
                entry[comp] = {"line_id": ln["line_id"], "element_id": c["element_id"], "floor": c["floor"],
                               "item_code": ln["item_code"], "was": A30._qty(ln), "readings": {
                                   k: _r(v) for k, v in got[comp].items()}, "range": [_r(lo), _r(hi)],
                               "released_moved": _r(moved), "earlier_change": ln["line_id"] in earlier,
                               "provisional_view": None if cview is None else _r(got[comp][cview])}
            log["records"].append(entry)
        log["totals"] = {k: [_r(v[0]), _r(v[1])] for k, v in log["totals"].items()}
        dec = pc.get("declared") or {}
        for comp, v in dec.items():
            got_t = log["totals"].get(comp)
            if got_t is None or any(abs(a - b) > TOL_M3 * 10 for a, b in zip(got_t, v)):
                raise ValueError(f"{METHOD}: {comp} held range {got_t} != the declared {v}")
        log["declared"] = dec
        logs.append(log)
    return changes, logs


# ================================================================================================ integrate / write
def changes_for(inputs, l3010, earlier_changed=()):
    """the conflict records, then the guard re-check over the result. -> (changes, logs)"""
    ch_r, logs = record_changes(inputs, l3010, earlier_changed)
    rep = {c["before"]["line_id"]: c["after"] for c in ch_r if c["action"] == "REPLACE"}
    view = [rep.get(ln["line_id"], ln) for ln in l3010]
    ch_g, log_g = A307.guard_changes(inputs, view, [], set(rep))
    for c in ch_g:   # a guard hold written by the V3.0.7 code is this version's row
        A305._note(c["after"], f"(re-check run by {METHOD})")
    return ch_r + ch_g, logs + [log_g]


def integrate(l3010, v3011_changes):
    """-> (V3.0.11 lines, identity). Every line outside the V3.0.11 rows is byte-identical to the V3.0.10 line."""
    from engine.source import boq_line as BL
    sid = {ln["line_id"] for ln in l3010}
    rep, adds = {}, []
    for c in v3011_changes:
        if c["action"] == "REPLACE":
            lid = c["before"]["line_id"]
            if lid in rep:
                raise ValueError(f"{METHOD}: line {lid} changed twice")
            if lid not in sid:
                raise ValueError(f"{METHOD}: a change names a line the V3.0.10 run does not have")
            if c["after"]["line_id"] != lid:
                raise ValueError(f"{METHOD}: a changed line keeps its line id")
            rep[lid] = c["after"]
        elif c["action"] == "ADD":
            if c["after"]["line_id"] in sid:
                raise ValueError(f"{METHOD}: an added line repeats a V3.0.10 line id")
            adds.append(c["after"])
        else:
            raise ValueError(f"{METHOD}: action {c['action']}")
    out = [rep.get(ln["line_id"], ln) for ln in l3010] + adds
    if len({ln["line_id"] for ln in out}) != len(out):
        raise ValueError(f"{METHOD}: a BOQ line id appears twice")
    for ln in out:
        BL.validate(ln)
    check_conflicts(out)
    A3010.check_same_openings(out)
    by3010 = {ln["line_id"]: ln for ln in l3010}
    touched = set(rep) | {a["line_id"] for a in adds}
    outside = [ln for ln in out if ln["line_id"] not in touched]
    bad = [ln["line_id"] for ln in outside if A30.line_sha(by3010[ln["line_id"]]) != A30.line_sha(ln)]
    if bad or len(outside) + len(rep) != len(l3010):
        raise ValueError(f"{METHOD}: {len(bad)} line(s) outside the V3.0.11 rows differ from {EXTENDS}")
    ident = {"v3_0_10_lines": len(l3010), "v3_0_11_lines": len(out), "v3_0_11_rows": len(v3011_changes),
             "replaced": len(rep), "added": len(adds), "outside_rows": len(outside),
             "outside_rows_identical_to_v3_0_10": len(outside),
             "outside_rows_sha256": hashlib.sha256("".join(A30.line_sha(x) for x in outside).encode()).hexdigest()}
    return out, ident


def check_conflicts(lines):
    """on finished lines: every line carrying a multi-tag conflict record is HELD as the exact range of its readings
    (never a quantity, never one reading). -> number of conflict lines"""
    n = 0
    for ln in lines:
        rec = ((ln.get("calculation") or {}).get("inputs") or {}).get("multi_tag_outline_v3011")
        if rec is None:
            continue
        n += 1
        vals = [v for v in (rec.get("readings") or {}).values() if _num(v)]
        if len(vals) < 2:
            raise InputsError(f"line {ln['line_id']}: a conflict line carries two or more readings")
        if ln["evidence_state"] != "BOUNDED_EXPOSURE" or ln.get("measured_net") is not None:
            raise InputsError(f"line {ln['line_id']}: a conflict line is BOUNDED_EXPOSURE with no quantity")
        br = ln.get("bounded_range") or {}
        if abs(br.get("low") - min(vals)) > TOL_M3 or abs(br.get("high") - max(vals)) > TOL_M3:
            raise InputsError(f"line {ln['line_id']}: range {br.get('low')} .. {br.get('high')} is not its readings "
                              f"{min(vals)} .. {max(vals)}")
    return n


def ledger_rows(changes, released_lines=None):
    rel = {A30._key(ln): ln for ln in released_lines or ()}
    rows = []
    for c in changes:
        ref = c["after"] if c["before"] is None else c["before"]
        b10 = A30._qty(c["before"]) if c["before"] is not None else dict(A30._qty(None), state="NOT_IN_V3_0_10")
        b29 = None
        if released_lines is not None:
            b29 = A30._qty(rel[A30._key(ref)]) if A30._key(ref) in rel else dict(A30._qty(None),
                                                                                 state="NOT_IN_RELEASED")
        p = PIECES[c["piece"]]
        loc = ref.get("location") or {}
        rows.append({"version": METHOD, "piece": c["piece"], "action": c["action"], "line_id": ref["line_id"],
                     "item_code": ref["item_code"], "floor": loc.get("floor"), "room_id": loc.get("room_id"),
                     "element_id": c["after"]["location"].get("element_id"), "unit": c["after"]["unit"],
                     "before_released_v2_9": b29, "before_v3_0_10": b10, "after_v3_0_11": A30._qty(c["after"]),
                     "evidence_status": c.get("evidence_status") or "HELD", "release_status": "NOT RELEASED",
                     "codes": c.get("codes") or [], "citations": c.get("citations") or [],
                     "drawing_reference": c.get("drawing_reference"),
                     "owner_manual_method": p["owner_manual_method"], "drawing_method": p["drawing_method"],
                     "owner_rules": p["owner_rules"],
                     "verification": dict(c.get("verification") or {}, module=p["module"], policy=p["policy"]),
                     "held": c.get("held") or [], "downstream": c.get("downstream") or [], "rollback": ROLLBACK})
    return rows


LEDGER_CSV = ("version", "piece", "action", "line_id", "item_code", "floor", "room_id", "element_id", "unit", "v2_9",
              "v3_0_10", "v3_0_11", "evidence_status", "release_status", "codes", "drawing_reference", "verification",
              "held")


def ledger_csv(rows):
    return A305._csv([{"version": r["version"], "piece": r["piece"], "action": r["action"], "line_id": r["line_id"],
                       "item_code": r["item_code"], "floor": r["floor"], "room_id": r["room_id"],
                       "element_id": r["element_id"], "unit": r["unit"], "v2_9": A302._q(r["before_released_v2_9"]),
                       "v3_0_10": A302._q(r["before_v3_0_10"]), "v3_0_11": A302._q(r["after_v3_0_11"]),
                       "evidence_status": r["evidence_status"], "release_status": r["release_status"],
                       "codes": " ".join(r["codes"]), "drawing_reference": str(r["drawing_reference"])[:300],
                       "verification": f"{r['verification'].get('task')} {r['verification'].get('merge_commit')}",
                       "held": "; ".join(str(h.get("why") or h.get("what")) for h in r["held"])[:600]}
                      for r in rows], LEDGER_CSV)


DIFF_CSV = ("line_id", "item_code", "floor", "element_id", "unit", "vs_v3_0_10", "vs_released_v2_9", "v2_9",
            "v3_0_10", "v3_0_11")


def diff_rows(l3010, l3011, released_lines=None):
    b10 = {ln["line_id"]: ln for ln in l3010}
    rel = {A30._key(ln): ln for ln in released_lines or ()}
    out = []
    for ln in l3011:
        o = b10.get(ln["line_id"])
        vs = "ADDED" if o is None else ("SAME" if A30.line_sha(o) == A30.line_sha(ln) else "CHANGED")
        r = rel.get(A30._key(ln)) if released_lines is not None else None
        vs29 = None if released_lines is None else ("NOT_IN_RELEASED" if r is None else
                                                    ("SAME_QUANTITY" if A30._qty(r) == A30._qty(ln) else
                                                     "QUANTITY_DIFFERS"))
        out.append({"line_id": ln["line_id"], "item_code": ln["item_code"], "floor": ln["location"].get("floor"),
                    "element_id": ln["location"].get("element_id"), "unit": ln["unit"], "vs_v3_0_10": vs,
                    "vs_released_v2_9": vs29, "v2_9": A302._q(A30._qty(r)) if r else "",
                    "v3_0_10": A302._q(A30._qty(o)) if o else "", "v3_0_11": A302._q(A30._qty(ln))})
    return out


def write(out, l3010, v3011_changes, logs, inputs, released_lines=None):
    """the V3_0_11_* files beside the V3_0_10_* files. -> (file names, identity, ledger)."""
    from pathlib import Path
    from engine.source import boq_line as BL
    out = Path(out)
    l3011, ident = integrate(l3010, v3011_changes)
    rows = ledger_rows(v3011_changes, released_lines)
    diff = diff_rows(l3010, l3011, released_lines)
    dsum = {}
    for d in diff:
        dsum.setdefault("vs_v3_0_10", {}).setdefault(d["vs_v3_0_10"], 0)
        dsum["vs_v3_0_10"][d["vs_v3_0_10"]] += 1
        if d["vs_released_v2_9"] is not None:
            dsum.setdefault("vs_released_v2_9", {}).setdefault(d["vs_released_v2_9"], 0)
            dsum["vs_released_v2_9"][d["vs_released_v2_9"]] += 1
    ident = dict(ident, diff=dsum)
    led = {"schema": LEDGER_SCHEMA, "method": METHOD, "extends": EXTENDS, "candidate": CANDIDATE,
           "base": A30.BASE_METHOD, "released": A30.RELEASED_METHOD, "released_default": False, "rows": rows,
           "waiting_pieces": WAITING, "integration_package": True}
    t10, t11 = A304.code_totals(l3010), A304.code_totals(l3011)
    moved = {k: {"v3_0_10": t10.get(k), "v3_0_11": t11.get(k)} for k in sorted(set(t10) | set(t11))
             if t10.get(k) != t11.get(k)}
    g = (inputs or {}).get("guard") or {}
    run = {"method": METHOD, "policy": POLICY_ID, "extends": EXTENDS, "candidate": CANDIDATE,
           "base_method": A30.BASE_METHOD, "released_method": A30.RELEASED_METHOD, "released_default": False,
           "rollback": ROLLBACK, "identity": ident, "pieces": PIECES, "piece_logs": logs,
           "inputs": {"pieces": [{k: pc.get(k) for k in ("piece", "source", "sources", "records", "declared")}
                                 for pc in (inputs or {}).get("pieces") or ()],
                      "guard": {k: g.get(k) for k in ("source", "evidence_file", "evidence_sha256", "conventions_file",
                                                      "conventions_sha256", "holding_checks", "recorded_checks",
                                                      "equal_value_rebase", "new_records")}},
           "totals_moved_by_code": moved, "waiting_pieces": WAITING, "conflict_lines": check_conflicts(l3011),
           "evidence_status_counts": A302._count(r["evidence_status"] for r in rows)}
    files = {"V3_0_11_BOQ_LINES.json": BL.dumps(l3011),
             "V3_0_11_BOQ_LINES.csv": A30._lines_csv(l3011),
             "V3_0_11_INTEGRATION_LEDGER.json": A30._j(led),
             "V3_0_11_INTEGRATION_LEDGER.csv": ledger_csv(rows),
             "V3_0_11_DIFF.csv": A305._csv(diff, DIFF_CSV),
             "V3_0_11_RUN.json": A30._j(run)}
    for name, text in files.items():
        (out / name).write_text(text, encoding="utf-8")
    return sorted(files), ident, led


def policy_record():
    return {"method": METHOD, "extends": EXTENDS, "pieces": sorted(PIECES), "inputs_schema": INPUTS_SCHEMA,
            "released_default": False, "rollback": ROLLBACK}


__all__ = ["METHOD", "PIECES", "WAITING", "DEFAULT_GUARD_CLASS", "READINGS", "load_inputs", "readings_of",
           "record_changes", "changes_for", "integrate", "check_conflicts", "ledger_rows", "diff_rows", "write",
           "InputsError"]
