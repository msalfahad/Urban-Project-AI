"""ARCH_TAKEOFF_V3.0.53 (T-487, stream S): the SAME opt-in BOQ candidate as ARCH_TAKEOFF_V3.0 .. V3.0.51
(engine.source.arch_v30, arch_v301 .. arch_v3051), with ONE new piece, the B9-02 LINTEL lines (F-T479-2: the family had
no candidate line at any version):

  LINTEL_LINES    one STR.CONC.LINTEL m3 line per opening in a masonry wall of the merged fill, read from the
                  Checker-verified lintel ledger (T-453 r2, MERGED b16f686b, rule R-T453-4 / R-T453-5):
                  REQUIRED  1 piece, cast-in-situ RC by the PRINTED project LINTEL SCHEDULE (level 1 project document:
                            B = wall width, D by opening-width band, MIN bearing printed): m3 = B x D x (w + 2 x
                            bearing), recomputed here from the printed band and asserted equal to the ledger;
                            PROVISIONAL (the FFL-to-structural-top build-up is a STAND-IN, jamb bearing and RC-column
                            jambs not measured: named on the line, never VERIFIED); formwork m2 and the host-wall face
                            beside, never in the quantity;
                  HELD / FLAGGED  BLOCKED_RFI BLANK by name (never 0, never a range): the ledger's reason, 'at most 1
                            piece', and the minimum-bearing volume IF built beside (not a bound: the bearing is a
                            minimum).

R-T487-1 (every villa): (1) a printed project lintel schedule governs; the owner precast lengths (owner lintel rule
2026-11-02: 1.20 / 1.50 / 2.50 / 3.00 / 4.00 m, 15 cm bearing, > 4.00 m FLAGGED) apply only where NO schedule is
printed (a run naming both is refused); (2) one opening, one lintel line, one piece at most; (3) the lintel is concrete
of B9-02: the host MAS.BLOCK line keeps its contract area byte-identical (element register ruling 'RC LINTEL', owner
Q-73; R-MAS-ABOVE-LINTEL-1 pending T-482), the face (w + 2 x bearing) x D is carried on the lintel record for the
material side (T-498) only; (4) a lintel whose host wall carries no released MAS.BLOCK line names the held wall, never
a line; (5) held / flagged stays blank, never 0.

Nothing else moves: every V3.0.51 line is byte-identical (asserted); totals move only in STR.CONC.LINTEL (asserted);
every V3.0.51 check still runs on the integrated lines. Version number: built on the merged V3.0.51 (T-483 r2, merge
ea7d375f); V3.0.52 is T-310's, in parallel (merge-order rule: whichever merges later rebases). Files: V3_0_53_BOQ_LINES.json / .csv, V3_0_53_INTEGRATION_LEDGER.json
/ .csv, V3_0_53_DIFF.csv, V3_0_53_RUN.json. Nothing here names a project, a sheet, a layer or a coordinate.
"""

from __future__ import annotations

import copy
import hashlib

from engine.source import arch_v30 as A30
from engine.source import arch_v302 as A302
from engine.source import arch_v304 as A304
from engine.source import arch_v305 as A305
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
from engine.source import arch_v3050 as A3050
from engine.source import arch_v3051 as A3051

DEFAULT_GUARD_CLASS = "TOOLING"          # T-212: books Checker-verified ledger pieces; adds no default value
METHOD = "ARCH_TAKEOFF_V3.0.53"
EXTENDS = A3051.METHOD
CANDIDATE = A30.METHOD
POLICY_ID = "URBAN_BOQ_T487_ARCH_V3_0_53"
INPUTS_SCHEMA = "URBAN_V3053_INPUTS_V1"
LEDGER_SCHEMA = "URBAN_V3053_INTEGRATION_LEDGER_V1"
ROLLBACK = A30.ROLLBACK
InputsError = A3051.InputsError
_r = A3050._r
_fmt = A3050._fmt
RULE_ID, RULE_VERSION = "R-T487-1", "T-487"
REC_KEY = "lintel_v3053"
P_LINTEL = "LINTEL_LINES"
CODE, UNIT = "STR.CONC.LINTEL", "m3"
HOST_CODE = "MAS.BLOCK"
REQUIRED, HELD, FLAGGED = "REQUIRED", "HELD", "FLAGGED"
DECISIONS = (REQUIRED, HELD, FLAGGED)
VALUED_STATE, HELD_STATE = "PROVISIONAL", "BLOCKED_RFI"
EVIDENCE = ("VERIFIED", "DRAWING-CONFIRMED", "ASSUMED - OWNER-APPROVED", "HELD", "UNKNOWN")   # WORKFLOW_CONTROLS s.5
ELEMENT_PREFIX = "LINTEL:"
TOL = 1e-6
MAX_WIDTH_M = 12.0                       # an opening wider than this is not a width in metres (mm / cm refused)
FORMULA_END_RE = A3046.FORMULA_END_RE

PIECES = {
    P_LINTEL: {"module": "engine/source/arch_v3053.py (one STR.CONC.LINTEL m3 line per opening in a masonry wall: "
                         "REQUIRED valued by the printed lintel schedule, HELD / FLAGGED blank by name)",
               "policy": "LINTEL_LINES_V1", "rule_id": "R-T487-1 (on R-T453-4 / R-T453-5)",
               "owner_rules": ["owner lintel rule 2026-11-02 (precast 1.20 .. 4.00 m, 15 cm bearing, > 4.00 m FLAGGED): "
                               "only where no lintel schedule is printed", "Q-73 (only masonry that physically exists; "
                               "no double count)", "UP-QTY-STATUS-001 (held is blank or a range, never 0)",
                               "ELEMENT_REGISTER ruling RC LINTEL vs host masonry (Lead 2026-11-03 08:17)",
                               "resolution order: drawings / project documents before company rules (AGENT_BRIEF)"],
               "owner_manual_method": "one lintel per opening in a block wall; length = opening + bearing each side; "
                                      "cast-in-situ: concrete m3 = wall width x depth x length (+ formwork m2, bar steel "
                                      "kg from the detail); precast: count by standard length",
               "drawing_method": "T-453 r2 lintel ledger (MERGED b16f686b, Verifier Gate A 2026-11-03 08:55): the "
                                 "printed structural LINTEL SCHEDULE (bands L1-L5, B = wall width, D 20 / 20 / 30 / 40 "
                                 "/ 55 cm, MIN 40 cm bearing each end) x the opening census widths x the merged fill "
                                 "pieces (masonry above the head: margin >= D + floor build-up); Checker own re-measure "
                                 "W14 0.195 m3, D-GF-06 0.072 m3, faces W14 / W15 / W18 1.705 m2 AGREE"},
}
WAITING = dict(A3051.WAITING)
WAITING.update({
    "T487_LINTEL_FORMWORK": "lintel formwork (B10-13, 2 x D x L + B x w per REQUIRED lintel) is printed beside each "
                            "lintel line, never booked as an STR.FORMWORK line in this version",
    "T487_LINTEL_BARS": "lintel bar steel kg (B11) HELD: bar cover, bend and anchorage lengths are not printed in the "
                         "detail; the printed bars per band are on the record",
    "T487_HOST_MATERIAL": "the REQUIRED face (w + 2 x bearing) x D leaves the host wall's MATERIAL base only (T-498 "
                          "blockwork materials wiring); the MAS.BLOCK contract area is unchanged (R-MAS-ABOVE-LINTEL-1, "
                          "T-482)",
})


# ================================================================================================ inputs
def _need(s, keys, where):
    for k in keys:
        if s.get(k) in (None, "", [], {}):
            raise InputsError(f"{where}: {k} missing")


def _num(x, where, pos=True, hi=None):
    if not isinstance(x, (int, float)) or isinstance(x, bool) or x != x:
        raise InputsError(f"{where}: {x!r} is not a number")
    if x < 0 or (pos and x == 0):
        raise InputsError(f"{where}: {x!r} is {'not positive' if pos else 'negative'} (held is never 0)")
    if hi is not None and x > hi:
        raise InputsError(f"{where}: {x} is above {hi} (not a quantity in metres)")
    return float(x)


def _schedule(s):
    """the PRINTED lintel schedule: {"source", "bearing_m", "rows": [{"row", "lo_m", "hi_m", "d_m"}]}. Bands are inclusive
    as printed, never overlapping; an opening between two bands is in no band (FLAGGED upstream, never forced)."""
    _need(s, ("source", "bearing_m", "rows"), "schedule")
    b = _num(s["bearing_m"], "schedule bearing_m", hi=2.0)
    rows, ids = [], set()
    for r in s["rows"]:
        _need(r, ("row", "lo_m", "hi_m", "d_m"), f"schedule row {r.get('row')}")
        if r["row"] in ids:
            raise InputsError(f"schedule row {r['row']} twice")
        ids.add(r["row"])
        lo = _num(r["lo_m"], f"row {r['row']} lo_m", pos=False, hi=MAX_WIDTH_M)
        hi = _num(r["hi_m"], f"row {r['row']} hi_m", hi=MAX_WIDTH_M)
        d = _num(r["d_m"], f"row {r['row']} d_m", hi=2.0)
        if lo > hi:
            raise InputsError(f"schedule row {r['row']}: lo {lo} > hi {hi}")
        rows.append({"row": r["row"], "lo_m": lo, "hi_m": hi, "d_m": d})
    rows.sort(key=lambda r: r["lo_m"])
    for a, c in zip(rows, rows[1:]):
        if c["lo_m"] <= a["hi_m"] + TOL:
            raise InputsError(f"schedule rows {a['row']} / {c['row']} overlap")
    return {"source": s["source"], "bearing_m": b, "rows": rows}


def band(width_m, sched):
    for r in sched["rows"]:
        if r["lo_m"] - TOL <= width_m <= r["hi_m"] + TOL:
            return r
    return None


def _entry(x, srcs, sched, seen):
    w = f"lintel {x.get('opening_id')}"
    _need(x, ("opening_id", "floor", "host_wall", "decision", "kind", "wall_t_m", "evidence_status", "source_tasks",
              "basis"), w)
    if x["opening_id"] in seen:
        raise InputsError(f"{w}: opening named twice (one opening, one lintel line)")
    seen.add(x["opening_id"])
    if x["decision"] not in DECISIONS:
        raise InputsError(f"{w}: decision {x['decision']!r} is not one of {DECISIONS}")
    if any(t not in srcs for t in x["source_tasks"]):
        raise InputsError(f"{w}: no merged / Checker source named")
    if x["evidence_status"] not in EVIDENCE:
        raise InputsError(f"{w}: evidence status {x['evidence_status']!r} is not a WORKFLOW_CONTROLS s.5 status")
    t = _num(x["wall_t_m"], f"{w} wall_t_m", hi=1.0)
    out = dict(x, _t=t)
    width = x.get("width_m")
    if width is not None:
        out["_w"] = _num(width, f"{w} width_m", hi=MAX_WIDTH_M)
    if x["decision"] == REQUIRED:
        _need(x, ("width_m", "schedule_row", "length_m", "concrete_m3", "formwork_m2", "face_m2", "open_checks"), w)
        if x["evidence_status"] in ("HELD", "UNKNOWN"):
            raise InputsError(f"{w}: a REQUIRED lintel with evidence {x['evidence_status']} is not valued here")
        if x.get("value") not in (None, ""):
            raise InputsError(f"{w}: the quantity is recomputed from the printed schedule, never typed")
        bnd = band(out["_w"], sched)
        if bnd is None or bnd["row"] != x["schedule_row"]:
            raise InputsError(f"{w}: width {out['_w']} m is not in printed band {x['schedule_row']} (stale ledger)")
        L = _r(out["_w"] + 2 * sched["bearing_m"])
        v = _r(t * bnd["d_m"] * L)
        fw = _r(2 * bnd["d_m"] * L + t * out["_w"])
        face = _r(L * bnd["d_m"])
        for k, mine in (("length_m", L), ("concrete_m3", v), ("formwork_m2", fw), ("face_m2", face)):
            if abs(_num(x[k], f"{w} {k}") - mine) > TOL:
                raise InputsError(f"{w}: ledger {k} {x[k]} is not the printed-schedule figure {mine} (recomputed)")
        out.update(_band=bnd, _L=L, _v=v, _fw=fw, _face=face)
    else:
        _need(x, ("why",), w)
        if x.get("concrete_m3") not in (None, "") or x.get("value") not in (None, ""):
            raise InputsError(f"{w}: a {x['decision']} lintel carries no volume (blank, never 0)")
        if x.get("width_m") is not None and x.get("schedule_row"):
            bnd = band(out["_w"], sched)
            if bnd is None or bnd["row"] != x["schedule_row"]:
                raise InputsError(f"{w}: width {out['_w']} m is not in printed band {x['schedule_row']}")
            L = _r(out["_w"] + 2 * sched["bearing_m"])
            out.update(_band=bnd, _L=L, _ifbuilt=_r(t * bnd["d_m"] * L), _face=_r(L * bnd["d_m"]))
    return out


def load_inputs(doc, project_id=None):
    """URBAN_V3053_INPUTS_V1 -> the validated doc.
    {"schema", "project_id", "sources": [{"task", "file", "sha256", "merge_commit", "checker_run"}],
     "schedule": {"source", "bearing_m", "rows": [{"row", "lo_m", "hi_m", "d_m"}]} (the PRINTED project schedule) |
     "precast_rule": {...} (only where no schedule is printed: not wired in this version, refused),
     "lintels": [{"opening_id", "floor", "host_wall", "host_line" (a MAS.BLOCK line id or None: held wall), "kind",
                  "wall_t_m", "block_type", "width_m", "decision" REQUIRED / HELD / FLAGGED, "schedule_row",
                  "length_m", "concrete_m3", "formwork_m2", "face_m2" (REQUIRED, recomputed and asserted), "why"
                  (HELD / FLAGGED), "open_checks", "evidence_status", "basis", "checker_remeasured", "source_tasks"}]}"""
    if not doc:
        return None
    if doc.get("schema") != INPUTS_SCHEMA:
        raise InputsError(f"project inputs: schema must be {INPUTS_SCHEMA}")
    if project_id and doc.get("project_id") not in (None, project_id):
        raise InputsError(f"project inputs are for {doc.get('project_id')!r}, the run is {project_id!r}")
    if doc.get("precast_rule") is not None:
        if doc.get("schedule") is not None:
            raise InputsError("a printed lintel schedule governs: the owner precast rule applies only where none is "
                              "printed (R-T487-1 (1)); a run naming both is refused")
        raise InputsError("precast-rule lintels (no printed schedule) are not wired in this version")
    if not doc.get("schedule"):
        raise InputsError("no printed lintel schedule named (and no precast rule): nothing to value")
    srcs = A3043._sources(doc)
    sched = _schedule(doc["schedule"])
    seen = set()
    lintels = [_entry(x, srcs, sched, seen) for x in doc.get("lintels") or ()]
    if not lintels:
        raise InputsError("no lintel in the inputs")
    return dict(doc, _sources=srcs, _schedule=sched, _lintels=lintels)


# ================================================================================================ lines
def _rec(srcs, **kw):
    return dict({"piece": P_LINTEL, "policy": PIECES[P_LINTEL]["policy"], "tasks": [s["task"] for s in srcs],
                 "ledgers": [s["file"] for s in srcs], "ledger_sha256": [s["sha256"] for s in srcs],
                 "merge_commits": [s["merge_commit"] for s in srcs], "checker_runs": [s["checker_run"] for s in srcs],
                 "rule_id": RULE_ID, "rule_version": RULE_VERSION, "release_status": "NOT RELEASED"}, **kw)


def _host_text(x):
    if x.get("host_line"):
        return f"host wall {x['host_wall']} in MAS.BLOCK line {x['host_line']} (contract area unchanged)"
    return f"host wall {x['host_wall']} carries no released MAS.BLOCK line (held wall): no line named"


def _template(prev):
    for ln in prev:
        if ln["item_code"].startswith("STR.CONC."):
            return ln
    raise InputsError("the candidate has no STR.CONC.* line to take the structural source documents from")


def _line(tpl, x, sched, srcs):
    from engine.source import boq_line as BL
    eid = ELEMENT_PREFIX + x["opening_id"]
    host = _host_text(x)
    common = dict(opening_id=x["opening_id"], floor=x["floor"], kind=x["kind"], host_wall=x["host_wall"],
                  host_line=x.get("host_line"), block_type=x.get("block_type"), wall_t_m=x["_t"],
                  width_m=x.get("_w"), decision=x["decision"], evidence_status=x["evidence_status"],
                  basis=x["basis"], schedule_source=sched["source"], bearing_m=sched["bearing_m"],
                  checker_remeasured=bool(x.get("checker_remeasured")), head_basis=x.get("head_basis"),
                  spare_margin_m=x.get("spare_margin_m"))
    if x["decision"] == REQUIRED:
        b = x["_band"]
        rec = _rec(srcs, action="ADD_LINTEL", pieces=1, schedule_row=b["row"], section_m=[x["_t"], b["d_m"]],
                   length_m=x["_L"], concrete_m3=x["_v"],
                   formwork_m2_beside=x["_fw"], host_face_m2=x["_face"], printed_bars=x.get("printed_bars"),
                   bar_steel="HELD (cover / bends / anchorage not printed)", open_checks=list(x["open_checks"]),
                   precast_alternative_beside=x.get("precast_alternative_beside"), **common)
        formula = (f"{METHOD}: 1 cast-in-situ RC lintel over {x['opening_id']} by the printed lintel schedule row "
                   f"{b['row']}: B {_fmt(x['_t'])} x D {_fmt(b['d_m'])} x L ({_fmt(x['_w'])} + 2 x "
                   f"{_fmt(sched['bearing_m'])} bearing) {_fmt(x['_L'])} = {_fmt(x['_v'])} m3 | beside, never in it: "
                   f"formwork {_fmt(x['_fw'])} m2 (2 x D x L + B x w), host face {_fmt(x['_face'])} m2 for the "
                   f"material side only; {host} | open: {'; '.join(x['open_checks'])} ({RULE_ID})")[:1500]
        ln = BL.make_line(
            project_id=tpl["project"]["project_id"], revision_set_sha256=tpl["project"]["revision_set_sha256"],
            item_code=CODE, unit=UNIT, evidence_state=VALUED_STATE, measured_net=x["_v"], gross=x["_v"],
            element_id=eid, floor=x["floor"], physical_element=f"RC lintel over opening {x['opening_id']} "
                                                              f"({x['kind'].lower()}, {_fmt(x['_w'])} m)",
            formula=formula, inputs={REC_KEY: rec, "evidence_status": x["evidence_status"]},
            documents=copy.deepcopy(tpl["source"]["documents"]), geometry_source=tpl["source"]["geometry_source"],
            geometry_confidence=tpl["source"]["geometry_confidence"], rule_id=RULE_ID, rule_version=RULE_VERSION,
            material_state=tpl.get("material_state") or "SOURCE",
            notes=(f"{METHOD}: B9-02 lintel line (T-453 r2 ledger, printed schedule {b['row']}); PROVISIONAL: "
                   f"{'; '.join(x['open_checks'])}; NOT RELEASED")[:2000])
        return A3046._fin(ln)
    if x.get("_ifbuilt") is not None:
        beside = (f"at most 1 piece; IF built: band {x['_band']['row']} B {_fmt(x['_t'])} x D "
                  f"{_fmt(x['_band']['d_m'])} x L at least {_fmt(x['_L'])} -> at least {_fmt(x['_ifbuilt'])} m3 "
                  f"(minimum bearing: not a bound), face at least {_fmt(x['_face'])} m2")
    else:
        beside = "at most 1 piece; no band / width established: no figure beside"
    rec = _rec(srcs, action="ADD_HELD_LINTEL", pieces_at_most=1, schedule_row=x.get("schedule_row"),
               if_built_at_least_m3=x.get("_ifbuilt"), if_built_face_at_least_m2=x.get("_face"), why=x["why"],
               beside=beside, **common)
    formula = (f"{METHOD}: HELD BLANK (never a value, never 0) lintel over {x['opening_id']} ({x['decision']}): "
               f"{A3043._plain(x['why'])} | {host} | {A3043._plain(beside)} ({RULE_ID})")[:1500]
    if FORMULA_END_RE.search(formula):
        raise InputsError(f"lintel {x['opening_id']}: the held formula would conclude on a figure")
    ln = BL.make_line(
        project_id=tpl["project"]["project_id"], revision_set_sha256=tpl["project"]["revision_set_sha256"],
        item_code=CODE, unit=UNIT, evidence_state=HELD_STATE, measured_net=None, gross=None, element_id=eid,
        floor=x["floor"], physical_element=f"lintel over opening {x['opening_id']} ({x['kind'].lower()})",
        formula=formula, inputs={REC_KEY: rec, "evidence_status": "HELD"},
        documents=copy.deepcopy(tpl["source"]["documents"]), geometry_source=tpl["source"]["geometry_source"],
        geometry_confidence=tpl["source"]["geometry_confidence"], rule_id=RULE_ID, rule_version=RULE_VERSION,
        material_state=tpl.get("material_state") or "SOURCE",
        rfi={"question": f"lintel over {x['opening_id']} ({x['decision']}): {x['why']}"[:900], "unlocks": eid,
             "bound_beside": beside[:300]},
        notes=f"{METHOD}: B9-02 lintel {x['decision']} by name, blank (never 0); NOT RELEASED")
    return A3046._fin(ln)


# ================================================================================================ changes
def changes_for(doc, prev):
    """-> (changes, log). Each change: piece, action ADD, before None, after (the new lintel line)."""
    if not doc:
        return [], {"piece": P_LINTEL, "state": "NO_PROJECT_INPUT"}
    if any(((ln.get("calculation") or {}).get("inputs") or {}).get(REC_KEY) for ln in prev):
        raise InputsError("the candidate already carries V3.0.53 records (applied once)")
    if any(ln["item_code"] == CODE for ln in prev):
        raise InputsError(f"the candidate already carries {CODE} lines: one opening, one lintel line (refused)")
    elems = {(ln.get("location") or {}).get("element_id") for ln in prev}
    by = {ln["line_id"]: ln for ln in prev}
    tpl = _template(prev)
    S, sched = doc["_sources"], doc["_schedule"]
    changes, ids = [], set()
    log = {"piece": P_LINTEL, "state": "RUN", "sources": doc["sources"], "lines_added": 0, "by_decision": {},
           "required_m3": 0.0, "required_pieces": 0, "formwork_m2_beside": 0.0, "host_face_m2_beside": 0.0,
           "schedule": {"source": sched["source"], "bearing_m": sched["bearing_m"],
                        "rows": [r["row"] for r in sched["rows"]]}}
    for x in doc["_lintels"]:
        w = f"lintel {x['opening_id']}"
        if ELEMENT_PREFIX + x["opening_id"] in elems:
            raise InputsError(f"{w}: element already has a line (one opening, one lintel line)")
        hl = x.get("host_line")
        if hl is not None:
            h = by.get(hl)
            if h is None or h["item_code"] != HOST_CODE:
                raise InputsError(f"{w}: host line {hl} is not a {HOST_CODE} line of the candidate (stale binding)")
            if x.get("host_net_m2") is not None and h.get("measured_net") is not None \
                    and abs(h["measured_net"] - x["host_net_m2"]) > 1e-4:
                raise InputsError(f"{w}: host line {hl} net {h['measured_net']} is not the ledger's {x['host_net_m2']} "
                                  f"(stale binding)")
        srcs = [S[t] for t in x["source_tasks"]]
        nl = _line(tpl, x, sched, srcs)
        if nl["line_id"] in by or nl["line_id"] in ids:
            raise ValueError(f"{METHOD}: lintel line {nl['line_id']} repeats an id")
        ids.add(nl["line_id"])
        if x["decision"] == REQUIRED:
            held = [{"what": f"{x['opening_id']} bar steel kg / jamb checks", "why": "; ".join(x["open_checks"])[:300],
                     "range": None, "scenario": f"formwork {_fmt(x['_fw'])} m2 beside (B10-13, not booked)"}]
            down = [f"B9-02 STR.CONC.LINTEL +{_fmt(x['_v'])} m3 (1 piece, PROVISIONAL)",
                    f"material side (T-498): host face {_fmt(x['_face'])} m2 leaves {x.get('host_line') or 'no line'}"
                    f" material base; MAS.BLOCK contract area unchanged",
                    f"B10-13 formwork {_fmt(x['_fw'])} m2 beside, not booked; B11 bar steel kg HELD"]
            log["required_m3"] = _r(log["required_m3"] + x["_v"])
            log["required_pieces"] += 1
            log["formwork_m2_beside"] = _r(log["formwork_m2_beside"] + x["_fw"])
            log["host_face_m2_beside"] = _r(log["host_face_m2_beside"] + x["_face"])
            ev = x["evidence_status"]
        else:
            held = [{"what": f"lintel {x['opening_id']}", "why": str(x["why"])[:300], "range": None,
                     "scenario": "held blank; at most 1 piece"}]
            down = ["B9-02: blocked-line count +1; no released quantity or range moves"]
            ev = "HELD"
        changes.append(A305._change(P_LINTEL, "ADD", None, nl, step="ADD_LINTEL" if x["decision"] == REQUIRED
                                    else "ADD_HELD_LINTEL", drawing_reference="; ".join(s["file"] for s in srcs),
                                    verification=A3043._ver(srcs), evidence_status=ev, held=held, downstream=down,
                                    group=CODE, decision=x["decision"]))
        log["lines_added"] += 1
        log["by_decision"][x["decision"]] = log["by_decision"].get(x["decision"], 0) + 1
    log["by_decision"] = dict(sorted(log["by_decision"].items()))
    return changes, log


# ================================================================================================ checks
def check_lintels(lines):
    """R-T487-1 on the integrated lines: every V3.0.53 record sits on a STR.CONC.LINTEL m3 line and every such line
    carries one; one line per opening; a REQUIRED line is PROVISIONAL, 1 piece, measured = gross = B x D x L with L = w + 2
    x bearing (recomputed from the record); a HELD / FLAGGED line is BLOCKED_RFI blank (no value, gross or range; never
    0) naming its reason; a named host line is a MAS.BLOCK line of the candidate. -> summary."""
    out = {"lines": 0, "required": 0, "held": 0, "flagged": 0, "required_m3": 0.0, "formwork_m2_beside": 0.0,
           "host_face_m2_beside": 0.0}
    by = {ln["line_id"]: ln for ln in lines}
    ops = set()
    for ln in lines:
        rec = ((ln.get("calculation") or {}).get("inputs") or {}).get(REC_KEY)
        if ln["item_code"] == CODE and not rec:
            raise ValueError(f"{METHOD}: {CODE} line {ln['line_id']} carries no V3.0.53 lintel record")
        if not rec:
            continue
        if ln["item_code"] != CODE or ln["unit"] != UNIT:
            raise ValueError(f"{METHOD}: a lintel record on {ln['item_code']} {ln['unit']} {ln['line_id']}")
        if rec["opening_id"] in ops:
            raise ValueError(f"{METHOD}: opening {rec['opening_id']} has two lintel lines")
        ops.add(rec["opening_id"])
        if rec.get("host_line") is not None:
            h = by.get(rec["host_line"])
            if h is None or h["item_code"] != HOST_CODE:
                raise ValueError(f"{METHOD}: lintel {ln['line_id']} names host {rec['host_line']}, not a {HOST_CODE} "
                                 f"line")
        out["lines"] += 1
        if rec["decision"] == REQUIRED:
            L = _r(rec["width_m"] + 2 * rec["bearing_m"])
            v = _r(rec["section_m"][0] * rec["section_m"][1] * L)
            if ln["evidence_state"] != VALUED_STATE or rec.get("pieces") != 1 or abs(rec["length_m"] - L) > TOL \
                    or abs((ln.get("measured_net") or -1) - v) > TOL or ln.get("gross") != ln.get("measured_net") \
                    or ln.get("bounded_range") is not None:
                raise ValueError(f"{METHOD}: REQUIRED lintel {ln['line_id']} is not 1 piece of B x D x (w + 2 x "
                                 f"bearing) PROVISIONAL")
            out["required"] += 1
            out["required_m3"] = _r(out["required_m3"] + v)
            out["formwork_m2_beside"] = _r(out["formwork_m2_beside"] + rec["formwork_m2_beside"])
            out["host_face_m2_beside"] = _r(out["host_face_m2_beside"] + rec["host_face_m2"])
        elif rec["decision"] in (HELD, FLAGGED):
            if ln["evidence_state"] != HELD_STATE or ln.get("measured_net") is not None or ln.get("gross") is not None \
                    or ln.get("bounded_range") is not None:
                raise ValueError(f"{METHOD}: {rec['decision']} lintel {ln['line_id']} is not BLOCKED_RFI blank (never "
                                 f"0)")
            if not rec.get("why") or not (ln.get("rfi") or {}).get("question"):
                raise ValueError(f"{METHOD}: {rec['decision']} lintel {ln['line_id']} names no reason")
            out["held" if rec["decision"] == HELD else "flagged"] += 1
        else:
            raise ValueError(f"{METHOD}: lintel decision {rec['decision']}")
    return out


# ================================================================================================ integrate / write
def integrate(prev, changes, for_lead=()):
    """-> (V3.0.53 lines, identity). Added lines follow the candidate lines; every candidate line is byte-identical
    (asserted). Every V3.0.51 check runs as V3.0.51 runs it (its changed skirting lines checked by check_remainder, the
    other skirting lines by the V3.0.44 check)."""
    sid = {ln["line_id"]: i for i, ln in enumerate(prev)}
    adds = []
    for c in changes:
        a = c["after"]
        if c["action"] != "ADD" or a["item_code"] != CODE:
            raise ValueError(f"{METHOD}: {c['action']} {a['item_code']} (this version only adds {CODE} lines)")
        if a["line_id"] in sid:
            raise ValueError(f"{METHOD}: an added line repeats a candidate id")
        adds.append(a)
    out = list(prev) + adds
    if len({ln["line_id"] for ln in out}) != len(out):
        raise ValueError(f"{METHOD}: a BOQ line id appears twice")
    guards = A3031._family_guards(out, for_lead)
    older = [ln for ln in out if not ((ln.get("calculation") or {}).get("inputs") or {}).get(A3051.REC_KEY)]
    ident = {"base_lines": len(prev), "v3_0_53_lines": len(out), "v3_0_53_rows": len(changes),
             "replaced": 0, "added": len(adds), "guards": guards,
             "roof_buildup": A3031.check_roof_layers(out), "ceilings": A3032.check_ceilings(out),
             "corrections": A3033.check_corrections(out), "tile_zones": A3034.check_zones(out),
             "fence": A3035.check_boundary(out), "lists": A3036.check_lists(out), "beds": A3038.check_beds(out),
             "lift": A3038.check_lift(out), "landing": A3038.check_landing(out), "flights": A3039.check_flights(out),
             "gb_runs": A3040.check_runs(out), "pieces": A3041.check_pieces(out), "slab": A3042.check_slab(out),
             "earthworks": A3050.check_zone_owner(out), "skirting": A3044.check_skirting(older),
             "blinding": A3045.check_blinding(out), "tie_masonry": A3046.check_tie_masonry(out),
             "stair_rooms": A3047.check_stair_rooms(out), "remainder": A3051.check_remainder(out),
             "lintels": check_lintels(out)}
    pids = {(ln["project"]["project_id"], ln["project"]["revision_set_sha256"]) for ln in out}
    if len(pids) != 1:
        raise ValueError(f"{METHOD}: {len(pids)} project identities in the lines")
    bad = [a["line_id"] for a in prev if A30.line_sha(a) != A30.line_sha(out[sid[a["line_id"]]])]
    if bad:
        raise ValueError(f"{METHOD}: {len(bad)} candidate line(s) differ outside the named changes")
    ident.update(outside_rows=len(prev), outside_rows_identical_to_base=len(prev),
                 outside_rows_sha256=hashlib.sha256("".join(A30.line_sha(x) for x in prev).encode()).hexdigest())
    return out, ident


def check_totals(t0, t1):
    """totals move only in STR.CONC.LINTEL (asserted)."""
    moved = {}
    for k in sorted(set(t0) | set(t1)):
        if t0.get(k) == t1.get(k):
            continue
        if k.split("|")[0] != CODE:
            raise ValueError(f"{METHOD}: totals moved outside this version's code: {k}")
        moved[k] = {"base": t0.get(k), "v3_0_53": t1.get(k)}
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
                     "element_id": loc.get("element_id"), "unit": ref["unit"], "decision": rec.get("decision"),
                     "opening_id": rec.get("opening_id"), "host_wall": rec.get("host_wall"),
                     "host_line": rec.get("host_line"), "before_released_v2_9": b29,
                     "before_base": A30._qty(c.get("before")), "after_v3_0_53": A30._qty(ref),
                     "formwork_m2_beside": rec.get("formwork_m2_beside"), "host_face_m2": rec.get("host_face_m2"),
                     "evidence_status": c.get("evidence_status"), "checker_remeasured": rec.get("checker_remeasured"),
                     "still_held": c.get("held"), "release_status": "NOT RELEASED",
                     "owner_manual_method": PIECES[c["piece"]]["owner_manual_method"],
                     "drawing_derived_method": PIECES[c["piece"]]["drawing_method"],
                     "downstream": c.get("downstream"), "record": rec, "verification": c.get("verification") or {},
                     "rollback": ROLLBACK})
    return rows


LEDGER_CSV = ("version", "action", "line_id", "item_code", "floor", "element_id", "unit", "decision", "host_wall",
              "host_line", "v2_9", "base", "v3_0_53", "formwork_m2_beside", "host_face_m2", "evidence_status",
              "checker_remeasured", "still_held", "verification")
DIFF_CSV = ("line_id", "item_code", "floor", "element_id", "unit", "vs_base", "vs_released_v2_9", "v2_9", "base",
            "v3_0_53")


def ledger_csv(rows):
    def q(x):
        return A302._q(x) if x and (x.get("value") is not None or x.get("low") is not None or x.get("state")) else ""

    def h(r):
        return "; ".join(f"{x['what']}: {x.get('why')}" for x in (r.get("still_held") or ()))[:300]
    return A305._csv([{"version": r["version"], "action": r["action"], "line_id": r["line_id"],
                       "item_code": r["item_code"], "floor": r.get("floor") or "",
                       "element_id": r.get("element_id") or "", "unit": r["unit"], "decision": r["decision"],
                       "host_wall": r.get("host_wall") or "", "host_line": r.get("host_line") or "",
                       "v2_9": q(r.get("before_released_v2_9")), "base": q(r.get("before_base")),
                       "v3_0_53": q(r.get("after_v3_0_53")),
                       "formwork_m2_beside": "" if r.get("formwork_m2_beside") is None else
                       _fmt(r["formwork_m2_beside"]),
                       "host_face_m2": "" if r.get("host_face_m2") is None else _fmt(r["host_face_m2"]),
                       "evidence_status": r["evidence_status"], "checker_remeasured": str(bool(r["checker_remeasured"])),
                       "still_held": h(r),
                       "verification": f"{r['verification'].get('task')} "
                                       f"{' '.join(x[:8] for x in r['verification'].get('merge_commits') or ())}"}
                      for r in rows], LEDGER_CSV)


def diff_rows(prev, new, released_lines=None):
    rows = A3046.diff_rows(prev, new, released_lines)
    return [dict({k: v for k, v in r.items() if k != "v3_0_46"}, v3_0_53=r["v3_0_46"]) for r in rows]


def write(out, prev, changes, log, released_lines=None, for_lead=()):
    """the V3_0_53_* files beside the base candidate's files. -> (file names, identity, ledger)."""
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
           "summary": {k: log.get(k) for k in ("by_decision", "required_m3", "required_pieces", "formwork_m2_beside",
                                               "host_face_m2_beside", "schedule")},
           "waiting_pieces": WAITING, "integration_package": True}
    run = {"method": METHOD, "policy": POLICY_ID, "extends": EXTENDS, "candidate": CANDIDATE,
           "base_method": A30.BASE_METHOD, "released_method": A30.RELEASED_METHOD, "released_default": False,
           "rollback": ROLLBACK, "identity": ident, "pieces": PIECES, "piece_logs": [log],
           "totals_moved_by_code": moved, "waiting_pieces": WAITING}
    files = {"V3_0_53_BOQ_LINES.json": BL.dumps(new),
             "V3_0_53_BOQ_LINES.csv": A30._lines_csv(new),
             "V3_0_53_INTEGRATION_LEDGER.json": A30._j(led),
             "V3_0_53_INTEGRATION_LEDGER.csv": ledger_csv(rows),
             "V3_0_53_DIFF.csv": A305._csv(diff, DIFF_CSV),
             "V3_0_53_RUN.json": A30._j(run)}
    for name, text in files.items():
        (out / name).write_text(text, encoding="utf-8")
    return sorted(files), ident, led


def policy_record():
    return {"method": METHOD, "extends": EXTENDS, "pieces": sorted(PIECES), "inputs_schema": INPUTS_SCHEMA,
            "released_default": False, "rollback": ROLLBACK, "actions": ["ADD_LINTEL", "ADD_HELD_LINTEL"]}


__all__ = ["METHOD", "PIECES", "WAITING", "DEFAULT_GUARD_CLASS", "INPUTS_SCHEMA", "CODE", "load_inputs", "band",
           "changes_for", "check_lintels", "integrate", "check_totals", "ledger_rows", "diff_rows", "write",
           "InputsError"]
