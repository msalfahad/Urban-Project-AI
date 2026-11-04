"""ARCH_TAKEOFF_V3.0.50 (T-497, stream S): the SAME opt-in BOQ candidate as ARCH_TAKEOFF_V3.0 .. V3.0.48
(engine.source.arch_v30, arch_v301 .. arch_v3048), with ONE earthworks fix (Checker F-C-T350R4-1, Gate B 2026-11-03
23:24 on the T-350 r4 package):

  EW_ZONE_OWNER   a V3.0.48 RANGED earthworks zone line whose plan overlapped the plan of another excavation zone is
                  RESTATED on the plan it alone owns (EXCAVATION_ZONE_OWNERSHIP_V1, rule R-T497-1): its new range, the
                  ground it gives up to each earlier zone (m2) and the scenario figures beside. The line keeps its id,
                  code, unit, location, its V3.0.43 zone record and its V3.0.48 record (history); the new record says
                  what superseded it. Evidence state stays BOUNDED_EXPOSURE (HELD), never valued.

R-T497-1 (every villa): one owner zone per excavated m3: every excavation zone subtracts the plans of ALL earlier zones in
the dig sequence of the drawings, in the plot AND beyond the plot line, by geometry, never from a list of known
interfaces; a restated range only ever SHRINKS onto its own plan (asserted: new low <= old low, new high <= old high).

Nothing else moves: every V3.0.48 line not named by the inputs is byte-identical (asserted), totals move only in the
restated code (asserted); every V3.0.48 earthworks invariant still holds on the lines it did not restate (its own check
runs on them). The version number follows V3.0.49, claimed by T-483 r2 in parallel (merge-order rule: whichever merges
second rebases). Files: V3_0_50_BOQ_LINES.json / .csv, V3_0_50_INTEGRATION_LEDGER.json / .csv, V3_0_50_DIFF.csv,
V3_0_50_RUN.json. Nothing here names a project, a sheet, a layer or a coordinate.
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
from engine.source import arch_v3048 as A3048

DEFAULT_GUARD_CLASS = "TOOLING"          # T-212: re-books a Checker-corrected zone plan; adds no default value
METHOD = "ARCH_TAKEOFF_V3.0.50"
EXTENDS = A3048.METHOD
CANDIDATE = A30.METHOD
POLICY_ID = "URBAN_BOQ_T497_ARCH_V3_0_50"
INPUTS_SCHEMA = "URBAN_V3050_INPUTS_V1"
LEDGER_SCHEMA = "URBAN_V3050_INTEGRATION_LEDGER_V1"
ROLLBACK = A30.ROLLBACK
InputsError = A3048.InputsError
_r = A3048._r
_fmt = A3048._fmt
RULE_ID, RULE_VERSION = "R-T497-1", "T-497"
REC_KEY = "earthworks_v3050"
PRIOR_KEY = A3048.REC_KEY                # the V3.0.48 record the restated line carries
ZONE_KEY = A3043.REC_KEY                 # the V3.0.43 zone record
P_OWNER = "EW_ZONE_OWNER"
EW_CODES = A3048.EW_CODES
FAMILY_CODE = A3048.FAMILY_CODE
RANGE_STATE = A3048.RANGE_STATE          # BOUNDED_EXPOSURE
TOL = A3048.TOL

PIECES = {
    P_OWNER: {"module": "engine/source/arch_v3050.py (a V3.0.48 ranged earthworks zone line restated on the plan it "
                        "alone owns; ground given up to earlier zones and scenarios beside)",
              "policy": "EW_ZONE_OWNER_V1", "rule_id": "R-T497-1 (EXCAVATION_ZONE_OWNERSHIP_V1)",
              "owner_rules": ["owner earthworks notes 2026-11-02 17:20 / 17:45 / 18:00 (geometry is always calculated; "
                              "one consistent scenario set)", "Q-21 C", "UP-QTY-STATUS-001 (held is blank or a range, "
                              "never 0)", "ELEMENT_REGISTER ruling EXCAVATION ZONES (Lead 2026-11-04 00:20): one owner "
                              "zone per excavated m3, the zone first in the dig sequence owns it",
                              "S06 / D-14 beyond-plot ground HELD by name"],
              "owner_manual_method": "excavation = plan of each pit / trench x depth from the existing ground to the "
                                     "formation; where two digs overlap the ground is taken once, by the deeper / "
                                     "earlier dig",
              "drawing_method": "T-484 strips and zone plans (MERGED 12395ea4) re-measured under R-T497-1: the trench "
                                "strip less the pool envelope, the grown pit union, the F10F reading and the FF raft, "
                                "in the plot and beyond (research/agents_t497); Checker own re-measure F-C-T350R4-1 "
                                "1.069269 .. 1.176467 m3 (drawn-outline scenario)"},
}
WAITING = dict(A3048.WAITING)
WAITING.update({
    "T497_F10F_SCENARIO": "the trench is stated in the drawn-outline F10F scenario (the F10F line's high end); under the "
                          "other S02 readings the trench owns up to 0.037 m3 more in the plot (0.047499 with beyond-plot)"
                          ", ground the F10F line's low end then does not dig: named beside, never added",
})


# ================================================================================================ inputs
def _need(s, keys, where):
    for k in keys:
        if s.get(k) in (None, "", [], {}):
            raise InputsError(f"{where}: {k} missing")


def _entry(x, srcs, seen):
    w = f"{x.get('action')} {x.get('family')} {x.get('zone')}"
    _need(x, ("action", "family", "zone", "element_id", "evidence_status", "basis", "held_items", "source_tasks",
              "given_up_m2", "was_low", "was_high"), w)
    if x["action"] != "RESTATE_RANGE":
        raise InputsError(f"{w}: action {x['action']} is not RESTATE_RANGE")
    if x["family"] not in FAMILY_CODE:
        raise InputsError(f"{w}: family {x['family']} is not B1-02 / B1-03 / B1-04")
    if FAMILY_CODE[x["family"]] != A3048.EXC:
        raise InputsError(f"{w}: zone ownership restates an EXCAVATION zone only (B1-02)")
    if any(t not in srcs for t in x["source_tasks"]):
        raise InputsError(f"{w}: no merged / Checker source named")
    if x["element_id"] in seen:
        raise InputsError(f"{w}: zone named twice (one zone, one line)")
    seen.add(x["element_id"])
    if x["evidence_status"] != "HELD":
        raise InputsError(f"{w}: a restated zone stays HELD (BOUNDED_EXPOSURE), never valued here")
    if x.get("value") not in (None, ""):
        raise InputsError(f"{w}: a restated zone carries a range, never a single value")
    lo = A3048._num(x.get("low"), f"{w} low", pos=True)
    hi = A3048._num(x.get("high"), f"{w} high", pos=True)
    wlo = A3048._num(x["was_low"], f"{w} was_low", pos=True)
    whi = A3048._num(x["was_high"], f"{w} was_high", pos=True)
    if lo > hi + TOL:
        raise InputsError(f"{w}: low {lo} > high {hi}")
    if lo > wlo + TOL or hi > whi + TOL:
        raise InputsError(f"{w}: an owned plan never grows a zone ({lo} .. {hi} vs {wlo} .. {whi})")
    g = x["given_up_m2"]
    if not isinstance(g, dict) or any(not isinstance(v, (int, float)) or v <= 0 for v in g.values()):
        raise InputsError(f"{w}: given_up_m2 names each earlier zone with a positive area")
    return dict(x, _lo=lo, _hi=hi, _wlo=wlo, _whi=whi)


def load_inputs(doc, project_id=None):
    """URBAN_V3050_INPUTS_V1 -> the validated doc.
    {"schema", "project_id", "sources": [{"task", "file", "sha256", "merge_commit", "checker_run"}],
     "zones": [{"action": "RESTATE_RANGE", "family": "B1-02", "zone", "element_id" (the V3.0.43 zone element),
                "evidence_status": "HELD", "low", "high", "was_low", "was_high" (the V3.0.48 range it replaces),
                "given_up_m2" {earlier zone: m2}, "basis", "held_items", "scenarios_beside", "source_tasks"}]}"""
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
def _rec(srcs, **kw):
    return dict({"piece": P_OWNER, "policy": PIECES[P_OWNER]["policy"], "tasks": [s["task"] for s in srcs],
                 "ledgers": [s["file"] for s in srcs], "ledger_sha256": [s["sha256"] for s in srcs],
                 "merge_commits": [s["merge_commit"] for s in srcs], "checker_runs": [s["checker_run"] for s in srcs],
                 "rule_id": RULE_ID, "rule_version": RULE_VERSION, "release_status": "NOT RELEASED",
                 "supersedes": f"{PRIOR_KEY} range (kept in the line as history)"}, **kw)


def _given(z):
    return "; ".join(f"{k} {_fmt(v)} m2" for k, v in sorted(z["given_up_m2"].items()))


def _restated(ln, z, srcs):
    new = copy.deepcopy(ln)
    word = A3043.ITEM_TEXT[A3048.EXC][2]
    qty = f"range {_fmt(z['_lo'])} .. {_fmt(z['_hi'])} m3 (HELD)"
    new["bounded_range"] = {"low": _r(z["_lo"]), "high": _r(z["_hi"]), "basis": f"{z['basis']} ({RULE_ID})"[:300]}
    beside = (f"ground given up to earlier zones: {_given(z)}"
              + (f"; scenarios beside (never the quantity): {z['scenarios_beside']}" if z.get("scenarios_beside")
                 else ""))
    new["rfi"] = {"question": f"{word} zone '{z['zone']}': {z['held_items']}"[:900], "unlocks": z["element_id"],
                  "bound_beside": beside[:300]}
    formula = (f"{METHOD}: {word} zone '{A3043._plain(z['zone'])}' {qty} on the plan it alone owns (R-T497-1): "
               f"{A3043._plain(z['basis'])} | held beside, never in it: {A3043._plain(z['held_items'])} | "
               f"{A3043._plain(beside)}")
    new["calculation"] = dict(new["calculation"], formula=formula[:1500])
    inp = new["calculation"]["inputs"] = dict(new["calculation"]["inputs"] or {})
    was = {"state": ln["evidence_state"], "bounded_range": ln.get("bounded_range")}
    inp[REC_KEY] = _rec(srcs, action="RESTATE_RANGE", family=z["family"], zone=z["zone"], was=was,
                        low_m3=z["_lo"], high_m3=z["_hi"], evidence_status="HELD", basis=z["basis"],
                        given_up_m2=dict(sorted(z["given_up_m2"].items())), held_items=z["held_items"],
                        scenarios_beside=z.get("scenarios_beside"))
    new["notes"] = (f"{ln.get('notes') or ''} | {METHOD}: {word} zone restated on its own plan (R-T497-1, "
                    f"F-C-T350R4-1) -> {qty}; NOT RELEASED")[:2000]
    return A3048._fin(new)


# ================================================================================================ changes
def changes_for(doc, prev):
    """-> (changes, log). Each change: piece, action CHANGE, before (the V3.0.48 line), after."""
    if not doc:
        return [], {"piece": P_OWNER, "state": "NO_PROJECT_INPUT"}
    if any(((ln.get("calculation") or {}).get("inputs") or {}).get(REC_KEY) for ln in prev):
        raise InputsError("the candidate already carries V3.0.50 records (applied once)")
    by_elem = {(ln["item_code"], (ln.get("location") or {}).get("element_id")): ln for ln in prev
               if ln["item_code"] in EW_CODES}
    S = doc["_sources"]
    changes = []
    log = {"piece": P_OWNER, "state": "RUN", "sources": doc["sources"], "lines_changed": 0, "restated_m3": {}}
    for z in doc["_zones"]:
        w = f"{z['action']} {z['family']} {z['zone']}"
        ln = by_elem.get((A3048.EXC, z["element_id"]))
        if ln is None:
            raise InputsError(f"{w}: no {A3048.EXC} line {z['element_id']} in the candidate (stale binding)")
        rec = ((ln.get("calculation") or {}).get("inputs") or {}).get(PRIOR_KEY) or {}
        br = ln.get("bounded_range") or {}
        if rec.get("action") != "RANGE" or ln["evidence_state"] != RANGE_STATE:
            raise InputsError(f"{w}: {ln['line_id']} is not a V3.0.48 ranged zone line (stale binding)")
        if abs(br.get("low", -1) - z["_wlo"]) > TOL or abs(br.get("high", -1) - z["_whi"]) > TOL:
            raise InputsError(f"{w}: the candidate range {br.get('low')} .. {br.get('high')} is not the was_low / "
                              f"was_high the inputs replace (stale binding)")
        srcs = [S[t] for t in z["source_tasks"]]
        new = _restated(ln, z, srcs)
        held = [{"what": f"{A3048.EXC} {z['zone']}", "why": str(z["held_items"])[:300],
                 "range": f"{_fmt(z['_lo'])} .. {_fmt(z['_hi'])}", "scenario": (z.get("scenarios_beside") or "")[:300]
                 or None}]
        changes.append(A305._change(P_OWNER, "CHANGE", ln, new, step="RESTATE_RANGE",
                                    drawing_reference="; ".join(s["file"] for s in srcs),
                                    verification=A3043._ver(srcs), evidence_status="HELD", held=held,
                                    downstream=[f"earthworks roll-up {A3048.EXC}: held range {_fmt(z['_wlo'])} .. "
                                                f"{_fmt(z['_whi'])} -> {_fmt(z['_lo'])} .. {_fmt(z['_hi'])} m3",
                                                "no other zone line moves (the ground given up is already in "
                                                "the earlier zones' lines or held with them)"],
                                    group=A3048.EXC))
        log["lines_changed"] += 1
        log["restated_m3"][f"{z['family']}|{z['zone']}"] = {"was": [z["_wlo"], z["_whi"]], "now": [z["_lo"], z["_hi"]]}
    return changes, log


# ================================================================================================ checks
def check_zone_owner(lines, before=None):
    """R-T497-1 on the integrated lines: a V3.0.50 record sits only on a B1-02 line that also carries its V3.0.43 zone
    and V3.0.48 range records; the line is BOUNDED_EXPOSURE at the record's range, low <= high, never above the range it
    replaced; when `before` is given, the restated line kept its id, code, unit, location and rule. Every OTHER
    earthworks invariant is the V3.0.48 one: its check runs on the lines with each restated line swapped back to its
    V3.0.48 form. -> summary."""
    out = {"restated": 0, "restated_low_m3": 0.0, "restated_high_m3": 0.0}
    b4 = {ln["line_id"]: ln for ln in before or ()}
    view = []
    for ln in lines:
        inp = (ln.get("calculation") or {}).get("inputs") or {}
        rec = inp.get(REC_KEY)
        if not rec:
            view.append(ln)
            continue
        if ln["item_code"] != A3048.EXC or not inp.get(PRIOR_KEY) or not inp.get(ZONE_KEY):
            raise ValueError(f"{METHOD}: a V3.0.50 record on {ln['item_code']} {ln['line_id']} without its zone / "
                             f"V3.0.48 records")
        br = ln.get("bounded_range") or {}
        if ln["evidence_state"] != RANGE_STATE or ln.get("measured_net") is not None or ln.get("gross") is not None \
                or abs(br.get("low", -1) - rec["low_m3"]) > 1e-9 or abs(br.get("high", -1) - rec["high_m3"]) > 1e-9 \
                or br["low"] > br["high"]:
            raise ValueError(f"{METHOD}: restated line {ln['line_id']} is not held at its record's range")
        was = (rec.get("was") or {}).get("bounded_range") or {}
        if br["low"] > was.get("low", -1) + TOL or br["high"] > was.get("high", -1) + TOL:
            raise ValueError(f"{METHOD}: restated line {ln['line_id']} grew beyond the range it replaced")
        o = b4.get(ln["line_id"])
        if o is not None:
            for key in ("item_code", "unit", "location", "line_id", "rule"):
                if o.get(key) != ln.get(key):
                    raise ValueError(f"{METHOD}: restated line {ln['line_id']} moved {key}")
            oi = (o.get("calculation") or {}).get("inputs") or {}
            if oi.get(PRIOR_KEY) != inp.get(PRIOR_KEY) or oi.get(ZONE_KEY) != inp.get(ZONE_KEY):
                raise ValueError(f"{METHOD}: restated line {ln['line_id']} lost its V3.0.43 / V3.0.48 records")
            view.append(o)
        else:
            old = copy.deepcopy(ln)                      # no `before`: rebuild the V3.0.48 form from the record
            old["bounded_range"] = dict(br, low=was.get("low"), high=was.get("high"))
            del old["calculation"]["inputs"][REC_KEY]
            view.append(old)
        out["restated"] += 1
        out["restated_low_m3"] = _r(out["restated_low_m3"] + br["low"])
        out["restated_high_m3"] = _r(out["restated_high_m3"] + br["high"])
    out["earthworks_v3048"] = A3048.check_earthworks(view)
    return out


# ================================================================================================ integrate / write
def integrate(prev, changes, for_lead=()):
    """-> (V3.0.50 lines, identity). Changed lines replace their candidate line in place; every other candidate line
    is byte-identical (asserted)."""
    sid = {ln["line_id"]: i for i, ln in enumerate(prev)}
    out = list(prev)
    repl = set()
    for c in changes:
        a = c["after"]
        if a["item_code"] != A3048.EXC:
            raise ValueError(f"{METHOD}: {a['item_code']} is not a code this version may change")
        if c["action"] != "CHANGE":
            raise ValueError(f"{METHOD}: action {c['action']} (this version adds no line)")
        i = sid.get(a["line_id"])
        if i is None or a["line_id"] in repl:
            raise ValueError(f"{METHOD}: a changed line is not a candidate line or changes twice")
        out[i] = a
        repl.add(a["line_id"])
    if len({ln["line_id"] for ln in out}) != len(out):
        raise ValueError(f"{METHOD}: a BOQ line id appears twice")
    guards = A3031._family_guards(out, for_lead)
    ident = {"base_lines": len(prev), "v3_0_50_lines": len(out), "v3_0_50_rows": len(changes),
             "replaced": len(repl), "added": 0, "guards": guards,
             "roof_buildup": A3031.check_roof_layers(out), "ceilings": A3032.check_ceilings(out),
             "corrections": A3033.check_corrections(out), "tile_zones": A3034.check_zones(out),
             "fence": A3035.check_boundary(out), "lists": A3036.check_lists(out), "beds": A3038.check_beds(out),
             "lift": A3038.check_lift(out), "landing": A3038.check_landing(out), "flights": A3039.check_flights(out),
             "gb_runs": A3040.check_runs(out), "pieces": A3041.check_pieces(out), "slab": A3042.check_slab(out),
             "earthworks": check_zone_owner(out, prev), "skirting": A3044.check_skirting(out),
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
                     "after_v3_0_50": A30._qty(ref), "evidence_status": c.get("evidence_status"),
                     "still_held": c.get("held"), "release_status": "NOT RELEASED",
                     "owner_manual_method": PIECES[c["piece"]]["owner_manual_method"],
                     "drawing_derived_method": PIECES[c["piece"]]["drawing_method"],
                     "record": rec, "verification": c.get("verification") or {}, "rollback": ROLLBACK})
    return rows


LEDGER_CSV = ("version", "piece", "action", "change", "line_id", "item_code", "floor", "element_id", "unit", "v2_9",
              "base", "v3_0_50", "evidence_status", "still_held", "verification")
DIFF_CSV = ("line_id", "item_code", "floor", "element_id", "unit", "vs_base", "vs_released_v2_9", "v2_9", "base",
            "v3_0_50")


def ledger_csv(rows):
    def q(x):
        return A302._q(x) if x and (x.get("value") is not None or x.get("low") is not None or x.get("state")) else ""

    def h(r):
        return "; ".join(f"{x['what']} {x.get('range')}" for x in (r.get("still_held") or ()))[:300]
    return A305._csv([{"version": r["version"], "piece": r["piece"], "action": r["action"], "change": r["change"],
                       "line_id": r["line_id"], "item_code": r["item_code"], "floor": r.get("floor") or "",
                       "element_id": r.get("element_id") or "", "unit": r["unit"],
                       "v2_9": q(r.get("before_released_v2_9")), "base": q(r.get("before_base")),
                       "v3_0_50": q(r.get("after_v3_0_50")), "evidence_status": r["evidence_status"],
                       "still_held": h(r),
                       "verification": f"{r['verification'].get('task')} "
                                       f"{' '.join(x[:8] for x in r['verification'].get('merge_commits') or ())}"}
                      for r in rows], LEDGER_CSV)


def diff_rows(prev, new, released_lines=None):
    rows = A3048.diff_rows(prev, new, released_lines)
    return [dict({k: v for k, v in r.items() if k != "v3_0_48"}, v3_0_50=r["v3_0_48"]) for r in rows]


def write(out, prev, changes, log, released_lines=None, for_lead=()):
    """the V3_0_50_* files beside the base candidate's files. -> (file names, identity, ledger)."""
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
    moved = {k: {"base": t0.get(k), "v3_0_50": t1.get(k)} for k in sorted(set(t0) | set(t1)) if t0.get(k) != t1.get(k)}
    for k in moved:
        if k.split("|")[0] != A3048.EXC:
            raise ValueError(f"{METHOD}: totals moved outside this version's code: {k}")
    led = {"schema": LEDGER_SCHEMA, "method": METHOD, "extends": EXTENDS, "candidate": CANDIDATE,
           "base": A30.BASE_METHOD, "released": A30.RELEASED_METHOD, "released_default": False, "rows": rows,
           "waiting_pieces": WAITING, "integration_package": True}
    run = {"method": METHOD, "policy": POLICY_ID, "extends": EXTENDS, "candidate": CANDIDATE,
           "base_method": A30.BASE_METHOD, "released_method": A30.RELEASED_METHOD, "released_default": False,
           "rollback": ROLLBACK, "identity": ident, "pieces": PIECES, "piece_logs": [log],
           "totals_moved_by_code": moved, "waiting_pieces": WAITING}
    files = {"V3_0_50_BOQ_LINES.json": BL.dumps(new),
             "V3_0_50_BOQ_LINES.csv": A30._lines_csv(new),
             "V3_0_50_INTEGRATION_LEDGER.json": A30._j(led),
             "V3_0_50_INTEGRATION_LEDGER.csv": ledger_csv(rows),
             "V3_0_50_DIFF.csv": A305._csv(diff, DIFF_CSV),
             "V3_0_50_RUN.json": A30._j(run)}
    for name, text in files.items():
        (out / name).write_text(text, encoding="utf-8")
    return sorted(files), ident, led


def policy_record():
    return {"method": METHOD, "extends": EXTENDS, "pieces": sorted(PIECES), "inputs_schema": INPUTS_SCHEMA,
            "released_default": False, "rollback": ROLLBACK, "actions": ["RESTATE_RANGE"]}


__all__ = ["METHOD", "PIECES", "WAITING", "DEFAULT_GUARD_CLASS", "INPUTS_SCHEMA", "EW_CODES", "load_inputs",
           "changes_for", "check_zone_owner", "integrate", "ledger_rows", "diff_rows", "write", "InputsError"]
