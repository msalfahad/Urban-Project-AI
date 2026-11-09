"""ARCH_TAKEOFF_V3.0.58 (T-507, stream F): the SAME opt-in BOQ candidate as ARCH_TAKEOFF_V3.0 .. V3.0.57
(engine.source.arch_v30 .. arch_v3057), extended with the EXPOSED-SLAB ROOF WATERPROOFING of family B8-06 that the
Checker-verified T-494 pieces measured (merge cddfdf7f) under WP_APPLICABILITY_RULES_V1 (an exposed slab top that no
roof line carries: e.g. the open-sky slab round a court void and its upturn):

  ZONE_LINES    one exposed zone -> its own lines, never merged into another roof's:
                  FIN.WP.ROOF (m2)          the flat membrane MEASURED (SOURCE_DERIVED, DRAWING-CONFIRMED);
                  FIN.WP.ROOF_UPTURN (lm)   the MEASURED upturn runs summed (the same unit as every candidate roof
                                            upturn line; m2 at the 0.20 m height in its record, UP-WP-003);
                  a HELD part with a measured bound (a covered ledge open at a side, a run under a window whose sill
                  is not read, a held zone's upturn) is its OWN BOUNDED_EXPOSURE line 0 .. bound, never summed in;
                  a HELD part with no length is its own BLOCKED_RFI line, BLANK ('length not measured'), never 0.
                Terminations (slab / void edge: treatment by the detail, R-WP-APPL-EDGE-1) and the drainage / falls
                RFI (R-WP-APPL-DRAIN-1) are named HELD items beside the zone's membrane line with their length bound
                (no B8-06 code carries them; never a quantity, never dropped). An edge the inputs state but did not
                measure gives a HELD 'length not measured' item, never no item (Checker F-C-T494-1).

R-T507-1 (every villa; integrates WP_APPLICABILITY_RULES_V1 R-WP-APPL-EXPOSED-1 / -FUNCTION-1 / -ONCE-1 / -UPTURN-1 /
-EDGE-1 / -DRAIN-1, UP-WP-ROOF-001, UP-WP-003, UP-QTY-STATUS-001): (a) the component rows are recomputed in the engine
by wp_applicability_rules_v1.component_rows from the zone the inputs state and must equal the merged piece's rows
(asserted, row by row); (b) only a B8-06 (no door) zone is booked here: a B8-07 or access-unknown zone is refused;
(c) ONCE: every FIN.WP.ROOF line of the candidate is named in the inputs' overlap census with its overlap; a non-zero
overlap or an unnamed roof line refuses the run (one membrane, one line); (d) a HELD part is never in a quantity and
never 0; (e) nothing outside FIN.WP.ROOF / FIN.WP.ROOF_UPTURN moves and every V3.0.57 line is byte-identical.

DEFAULT GUARD (T-212 P2 / P4): this stage wires the producer wp_applicability_rules_v1 into the candidate, so the
merged default guard runs at integration over the V3.0.57 lines + the added lines (arch_v307.guard_changes), as
V3.0.57 does; with no "guard" block only the log says so (NO_PROJECT_INPUT).

CODE TOTALS VIEW (F-C-T508-1 / T-512): the run file carries code_totals_view: every item code and unit of the result
printed by the T-512 rule (ALL_VALUED number; PARTIAL 'AT_LEAST x + HELD (n lines)'; HELD_BOUNDED range; HELD
'(n blank lines)'), so an all-blank or bounded-only code never prints 0.0 (asserted). arch_v304.code_totals (frozen
chain) is unchanged; totals_moved_by_code keeps its raw records beside their view.

Files: V3_0_58_BOQ_LINES.json / .csv, V3_0_58_INTEGRATION_LEDGER.json / .csv, V3_0_58_DIFF.csv, V3_0_58_RUN.json.
Nothing here names a project, a sheet, a layer or a coordinate.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re

from engine.source import arch_v30 as A30
from engine.source import arch_v302 as A302
from engine.source import arch_v304 as A304
from engine.source import arch_v305 as A305
from engine.source import arch_v307 as A307
from engine.source import arch_v3018 as A3018
from engine.source import arch_v3030 as A3030
from engine.source import arch_v3031 as A3031
from engine.source import arch_v3043 as A3043
from engine.source import arch_v3057 as A3057
from engine.source import wp_applicability_rules_v1 as WPA

DEFAULT_GUARD_CLASS = "GUARD_HOST"      # wires wp_applicability_rules_v1; the guard re-check runs (arch_v307)
METHOD = "ARCH_TAKEOFF_V3.0.58"
EXTENDS = A3057.METHOD
CANDIDATE = A30.METHOD
POLICY_ID = "URBAN_BOQ_T507_ARCH_V3_0_58"
INPUTS_SCHEMA = "URBAN_V3058_INPUTS_V1"
LEDGER_SCHEMA = "URBAN_V3058_INTEGRATION_LEDGER_V1"
ROLLBACK = A30.ROLLBACK
InputsError = A3031.InputsError
_r = A3018._r
_fmt = A3030._fmt
RULE_ID, RULE_VERSION = "R-T507-1", "T-507"
REC_KEY = "exposed_slab_wp_v3058"
P_ZONE = "ZONE_LINES"
ACTIONS = ("ADD_ZONE",)
ROOF, UPTURN = "FIN.WP.ROOF", "FIN.WP.ROOF_UPTURN"
CODES = (ROOF, UPTURN)
FAMILY = WPA.FAMILY_ROOF
VALUED_STATE, BOUNDED_STATE, HELD_STATE = "SOURCE_DERIVED", "BOUNDED_EXPOSURE", "BLOCKED_RFI"
EVIDENCE_STATUS = "DRAWING-CONFIRMED"     # WORKFLOW_CONTROLS s.5; VERIFIED is the Checker's word, never an input
TOL = 0.0000015
MAX_Q = 2000.0                            # one zone's area (m2) or run (lm); above it is a unit slip (mm refused)
LINE_ID_RE = re.compile(r"^L-[0-9a-f]{20}$")
ZONE_RE = re.compile(r"^[A-Z0-9][A-Z0-9-]{1,40}$")
FLOOR_RE = re.compile(r"^(B|GF|[0-9]F|RF)$")
BESIDE = ("SLAB_EDGE_TERMINATION", "VOID_EDGE_TERMINATION", "DRAINAGE_FALLS", "WINDOW_TRANSITION")
EDGE_KEYS = (("SLAB_EDGE_TERMINATION", "open_edge_lm"), ("VOID_EDGE_TERMINATION", "void_edge_lm"))
TEXT = {ROOF: ("Roof waterproofing membrane on an exposed slab top (B8-06)",
               "عازل مائي على سطح بلاطة مكشوفة (B8-06)", "exposed slab membrane"),
        UPTURN: ("Roof waterproofing upturn 0.20 m on an exposed slab (B8-06)",
                 "رفعة العازل 0.20 م على بلاطة مكشوفة (B8-06)", "exposed slab upturn")}

PIECES = {
    P_ZONE: {"module": "engine/source/arch_v3058.py (an exposed slab top no roof line carries: its own B8-06 membrane "
                       "and upturn lines from WP_APPLICABILITY_RULES_V1 component rows; held parts their own bounded "
                       "or blank lines; terminations and drainage named beside)",
             "policy": "EXPOSED_SLAB_WP_LINES_V1", "rule_id": "WP_APPLICABILITY_RULES_V1 (R-T507-1)",
             "owner_rules": ["UP-WP-ROOF-001 (purpose: exterior horizontal surfaces exposed to water; scope extended by "
                             "R-WP-APPL-EXPOSED-1, agent-derived, provenance T-486, Checker-endorsed)",
                             "UP-WP-003 (upturn 0.20 m, owner Q-03 / Q-24)", "UP-WP-004 (terminations by the detail)",
                             "UP-QTY-STATUS-001 (held is blank or bounded, never 0)"],
             "owner_manual_method": "membrane on the exposed slab top inside its edges less what stands on it (piers) "
                                    "and the void; 0.20 m upturn on every wall / parapet / solid face; a run under a "
                                    "window only with the sill 0.20 m above the slab",
             "drawing_method": "the merged T-494 component rows (T-486 geometry; Checker own DXF re-measure AGREE: flat "
                               "4.907 m2, upturn 5.194 lm / 1.039 m2), recomputed here by component_rows"},
}
WAITING = dict(A3057.WAITING)
WAITING.update({
    "T507_TERMINATIONS": "exposed-slab edge terminations (slab edge and void edge, R-WP-APPL-EDGE-1): lengths named "
                         "beside the zone's membrane line, treatment HELD until a detail prints it (designer item)",
    "T507_DRAINAGE": "exposed-slab drainage / falls (R-WP-APPL-DRAIN-1): RFI beside the zone's line; never blocks or "
                     "zeroes the membrane",
    "T507_BUILDUP": "the exposed zone's roof build-up (falls screed, insulation, protection: B13-01) and its membrane "
                    "rolls (procurement) are not in this package: installed membrane and upturn only",
    "T507_WINDOW_SILL": "an upturn run under a window whose sill height above the slab is not read: its own bounded "
                        "line 0 .. run (it may be a transition, R-WP-APPL-UPTURN-1)",
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
        raise InputsError(f"{where}: {x} is not a quantity in m / m2 (mm / cm refused)")
    return float(x)


def _lid(x, where):
    if not LINE_ID_RE.match(str(x)):
        raise InputsError(f"{where}: {x!r} is not a BOQ line id")
    return x


def _canon(rows):
    return json.dumps(rows, sort_keys=True, ensure_ascii=False)


def _zone(z, srcs):
    w = f"zone {z.get('zone_id')}"
    _need(z, ("zone_id", "floor", "geometry", "expected_rows", "source_tasks", "evidence_status", "basis"), w)
    if not ZONE_RE.match(str(z["zone_id"])):
        raise InputsError(f"{w}: zone id {z['zone_id']!r} (upper-case letters, digits, '-')")
    if not FLOOR_RE.match(str(z["floor"])):
        raise InputsError(f"{w}: floor {z['floor']!r}")
    if any(t not in srcs for t in z["source_tasks"]):
        raise InputsError(f"{w}: no merged source named")
    if z["evidence_status"] != EVIDENCE_STATUS:
        raise InputsError(f"{w}: evidence status {z['evidence_status']!r} (an integration input is {EVIDENCE_STATUS}; "
                          f"VERIFIED is the Checker's word)")
    g = z["geometry"]
    if g.get("zone_id") != z["zone_id"]:
        raise InputsError(f"{w}: geometry is for {g.get('zone_id')!r}")
    if g.get("membrane_m2") is not None:
        _num(g["membrane_m2"], f"{w} membrane", pos=True)
    for u in g.get("upturn_runs") or ():
        _need(u, ("run", "kind"), f"{w} upturn run")
        if u.get("lm") is not None:
            _num(u["lm"], f"{w} run {u['run']}", pos=True)
    for comp, key in EDGE_KEYS:          # F-C-T494-1: every edge is stated: a length, null (not measured) or 0 by evidence
        if key not in g:
            raise InputsError(f"{w}: {key} not stated (a length, null = not measured, or 0 with evidence of no edge)")
        if g[key] is None:
            continue
        v = _num(g[key], f"{w} {key}")
        if v == 0 and not (g.get("evidence") or {}).get(comp):
            raise InputsError(f"{w}: {key} 0 without evidence that the zone has no such edge (missing is never 0)")
    fam, _func = WPA.family_of(g.get("doors"), g.get("label"))
    if fam != FAMILY:
        raise InputsError(f"{w}: family {fam} (doors {g.get('doors')!r}): this version books B8-06 roof zones only "
                          f"(a door -> B8-07, access unknown -> HELD family)")
    rows = WPA.component_rows(g)
    if _canon(rows) != _canon(z["expected_rows"]):
        raise InputsError(f"{w}: component_rows of the stated zone differ from the merged piece's rows (stale input)")
    return dict(z, _rows=rows)


def load_inputs(doc, project_id=None):
    """URBAN_V3058_INPUTS_V1 -> the validated doc.
    {"schema", "project_id", "sources": [{"task", "file", "sha256", "merge_commit", "checker_run"}],
     "template_line": a FIN.WP.ROOF line of the candidate (documents / trade of the added lines),
     "zones": [{"zone_id", "floor", "element_prefix" (optional, default '<floor>-<zone_id>'), "geometry" (the
                wp_applicability_rules_v1 zone dict), "expected_rows" (the merged piece's component rows),
                "source_tasks", "evidence_status", "basis"}],
     "overlap": [{"line_id", "overlap_m2", "evidence"}] (EVERY FIN.WP.ROOF line of the candidate),
     "guard": as URBAN_V307_INPUTS_V1 "guard" (optional)}"""
    if not doc:
        return None
    if doc.get("schema") != INPUTS_SCHEMA:
        raise InputsError(f"project inputs: schema must be {INPUTS_SCHEMA}")
    if project_id and doc.get("project_id") not in (None, project_id):
        raise InputsError(f"project inputs are for {doc.get('project_id')!r}, the run is {project_id!r}")
    srcs = A3043._sources(doc)
    _lid(doc.get("template_line"), "template_line")
    zones, seen = [], set()
    for z in doc.get("zones") or ():
        zz = _zone(z, srcs)
        if zz["zone_id"] in seen:
            raise InputsError(f"zone {zz['zone_id']}: named twice")
        seen.add(zz["zone_id"])
        zones.append(zz)
    if not zones:
        raise InputsError("no zone in the inputs")
    ov = {}
    for o in doc.get("overlap") or ():
        _need(o, ("line_id", "evidence"), "overlap")
        _lid(o["line_id"], "overlap")
        if o["line_id"] in ov:
            raise InputsError(f"overlap {o['line_id']}: named twice")
        if _num(o.get("overlap_m2"), f"overlap {o['line_id']}") > TOL:
            raise InputsError(f"overlap {o['line_id']}: {o['overlap_m2']} m2 of the zone is carried by a roof line "
                              f"(R-WP-APPL-ONCE-1: carried, never added; re-measure the zone)")
        ov[o["line_id"]] = o
    if not ov:
        raise InputsError("overlap: every roof line of the candidate is named with its overlap (none named)")
    g = doc.get("guard")
    if g is not None:
        A307.load_inputs({"schema": A307.INPUTS_SCHEMA, "project": doc.get("project_id"), "guard": g}, project_id)
    return dict(doc, _sources=srcs, _zones=zones, _overlap=ov)


# ================================================================================================ lines
def _rec(srcs, **kw):
    return dict({"piece": P_ZONE, "policy": PIECES[P_ZONE]["policy"], "tasks": [s["task"] for s in srcs],
                 "ledgers": [s["file"] for s in srcs], "ledger_sha256": [s["sha256"] for s in srcs],
                 "merge_commits": [s["merge_commit"] for s in srcs], "checker_runs": [s["checker_run"] for s in srcs],
                 "rule_id": RULE_ID, "rule_version": RULE_VERSION, "applicability_rules": WPA.RULE_VERSION,
                 "family": FAMILY, "release_status": "NOT RELEASED"}, **kw)


def _beside_items(z):
    """the zone's terminations, drainage RFI and window transitions: named, bound shown, never a quantity."""
    out = []
    for r in z["_rows"]:
        if r["component"] in BESIDE:
            out.append({"what": r["component"], "zone": z["zone_id"], "run": r.get("run"), "unit": r["unit"],
                        "bound": r.get("held_bound"), "status": r["status"], "why": r.get("held_reason"),
                        "basis": r["rule_basis"]})
    g = z["geometry"]
    for comp, key in EDGE_KEYS:          # F-C-T494-1: an edge stated but not measured -> a HELD item, never no item
        if g.get(key) is None:
            out.append({"what": comp, "zone": z["zone_id"], "run": None, "unit": "lm", "bound": None,
                        "status": WPA.HELD, "why": "length not measured", "basis": "R-WP-APPL-EDGE-1 / F-C-T494-1"})
    return out


def _parts(z):
    """-> [(code, suffix, state, value, bound, rows, why)] the lines of one zone."""
    rows = z["_rows"]
    parts = []
    flat = [r for r in rows if r["component"] == "FLAT_MEMBRANE"]
    for r in flat:
        if r["status"] == WPA.MEASURED:
            parts.append((ROOF, "wp_membrane", VALUED_STATE, r["qty"], None, [r], None))
        elif r["status"] == WPA.HELD:
            parts.append((ROOF, "wp_membrane", BOUNDED_STATE if r.get("held_bound") is not None else HELD_STATE,
                          None, r.get("held_bound"), [r], r.get("held_reason")))
        # NOT_APPLICABLE / CARRIED: no line (the evidence stays in the record of the run log)
    ups = [r for r in rows if r["component"] == "UPTURN"]
    meas = [r for r in ups if r["status"] == WPA.MEASURED]
    if meas:
        parts.append((UPTURN, "wp_upturn", VALUED_STATE, _r(sum(r["length_lm"] for r in meas)), None, meas, None))
    for r in ups:
        if r["status"] != WPA.HELD:
            continue
        lm = r.get("length_lm")
        suffix = "wp_upturn" if not meas and len([x for x in ups if x["status"] == WPA.HELD]) == 1 else \
            f"wp_upturn {r['run']}"
        parts.append((UPTURN, suffix, BOUNDED_STATE if lm is not None else HELD_STATE, None, lm, [r],
                      r.get("held_reason") or ("length not measured" if lm is None else "")))
    if any(r["component"] == "DOORWAY_TRANSITION" for r in rows):
        raise InputsError(f"zone {z['zone_id']}: a doorway on a B8-06 zone (a door makes it B8-07)")
    return parts


def _line(tpl, z, part, srcs, beside):
    from engine.source import boq_line as BL
    code, suffix, state, value, bound, rows, why = part
    en, ar, word = TEXT[code]
    unit = "m2" if code == ROOF else "lm"
    eid = f"{z.get('element_prefix') or (z['floor'] + '-' + z['zone_id'])}:{suffix}"
    runs = [{"run": r.get("run") or r["component"], "lm": r.get("length_lm"), "m2": r.get("qty"),
             "bound": r.get("held_bound"), "status": r["status"]} for r in rows]
    m2_at_h = None
    if code == UPTURN and state == VALUED_STATE:
        m2_at_h = _r(sum(r["qty"] for r in rows))
        if abs(m2_at_h - _r(value * WPA.UPTURN_H_M)) > 1e-6:
            raise ValueError(f"{METHOD}: {eid}: run m2 {m2_at_h} != {value} x {WPA.UPTURN_H_M}")
    rec = _rec(srcs, action="ADD_ZONE", zone_id=z["zone_id"], component=rows[0]["component"], unit=unit,
               value=value, bound=bound, state=state, runs=runs, upturn_m2_at_0_20=m2_at_h,
               height_m=WPA.UPTURN_H_M if code == UPTURN else None, held_reason=why,
               rule_basis=sorted({r["rule_basis"] for r in rows}), evidence=[e for r in rows for e in r["evidence"]],
               held_beside=beside, evidence_status=z["evidence_status"] if state == VALUED_STATE else "HELD",
               basis=z["basis"])
    bs = "; ".join(f"{b['what']} {b.get('run') or ''} {'bound ' + _fmt(b['bound']) + ' ' + b['unit'] if b.get('bound') is not None else '(' + str(b.get('why')) + ')'}".replace("  ", " ")
                   for b in beside)
    if state == VALUED_STATE:
        f = (f"{METHOD}: {word} {z['zone_id']} = " +
             (f"{_fmt(value)} m2 (exposed slab top, net of piers and void)" if code == ROOF else
              " + ".join(_fmt(r["length_lm"]) for r in rows) + f" = {_fmt(value)} lm x {WPA.UPTURN_H_M} = "
              f"{_fmt(m2_at_h)} m2") + f" ({z['evidence_status']}, {WPA.RULE_VERSION})")
    elif state == BOUNDED_STATE:
        f = (f"{METHOD}: {word} {z['zone_id']} {suffix} HELD ({why}): bound 0 .. {_fmt(bound)} {unit} shown, "
             f"never summed in")
    else:
        f = f"{METHOD}: {word} {z['zone_id']} {suffix} HELD BLANK ({why}); never 0"
    if beside:
        f += f" | beside, HELD, never in the quantity: {bs}"
    kw = {}
    if state == BOUNDED_STATE:
        kw["bounded_range"] = {"low": 0.0, "high": _r(bound), "basis": f"0 .. measured bound ({why})"[:300]}
    if state == HELD_STATE:
        kw["rfi"] = {"question": f"{z['zone_id']} {suffix}: {why}"[:900], "unlocks": eid}
    ln = BL.make_line(
        project_id=tpl["project"]["project_id"], revision_set_sha256=tpl["project"]["revision_set_sha256"],
        item_code=code, unit=unit, evidence_state=state, measured_net=_r(value) if state == VALUED_STATE else None,
        gross=None, element_id=eid, floor=z["floor"], physical_element=word, formula=f[:1500],
        inputs={REC_KEY: rec, "evidence_status": rec["evidence_status"]},
        documents=copy.deepcopy(tpl["source"]["documents"]), geometry_source=tpl["source"]["geometry_source"],
        geometry_confidence=tpl["source"]["geometry_confidence"], rule_id=RULE_ID, rule_version=RULE_VERSION,
        material_state=tpl.get("material_state") or "SOURCE",
        notes=f"{METHOD}: B8-06 exposed slab {z['zone_id']} ({'measured' if state == VALUED_STATE else 'held'}); "
              f"NOT RELEASED", item_en=en, item_ar=ar, trade=tpl["trade"], subtrade=FAMILY, **kw)
    return A3057._fin(ln)


# ================================================================================================ changes
def changes_for(doc, prev):
    """-> (changes, log). Each change: piece, action ADD, before None, after the new line."""
    if not doc:
        return [], {"piece": P_ZONE, "state": "NO_PROJECT_INPUT"}
    if any(((ln.get("calculation") or {}).get("inputs") or {}).get(REC_KEY) for ln in prev):
        raise InputsError("the candidate already carries V3.0.58 records (applied once)")
    by = {ln["line_id"]: ln for ln in prev}
    tpl = by.get(doc["template_line"])
    if tpl is None or tpl["item_code"] != ROOF:
        raise InputsError(f"template_line {doc['template_line']}: not a {ROOF} line of the candidate (stale binding)")
    roofs = {ln["line_id"] for ln in prev if ln["item_code"] == ROOF}
    if set(doc["_overlap"]) != roofs:
        raise InputsError(f"overlap census names {sorted(set(doc['_overlap']) ^ roofs)} not as the candidate's "
                          f"{ROOF} lines (every roof line, once: R-WP-APPL-ONCE-1)")
    S = doc["_sources"]
    changes, seen = [], set(by)
    log = {"piece": P_ZONE, "state": "RUN", "sources": doc["sources"], "zones": [], "lines_added": 0,
           "by_state": {}, "overlap_census": {k: doc["_overlap"][k]["overlap_m2"] for k in sorted(doc["_overlap"])}}
    for z in doc["_zones"]:
        srcs = [S[t] for t in z["source_tasks"]]
        beside = _beside_items(z)
        parts = _parts(z)
        zl = {"zone_id": z["zone_id"], "lines": [], "beside": beside,
              "no_line": [{"component": r["component"], "status": r["status"]} for r in z["_rows"]
                          if r["component"] == "FLAT_MEMBRANE" and r["status"] in (WPA.NOT_APPLICABLE, WPA.CARRIED)]}
        if not parts and not zl["no_line"]:
            raise InputsError(f"zone {z['zone_id']}: no membrane row (an exposed zone is never silently dropped)")
        for i, p in enumerate(parts):
            bes = beside if (p[0] == ROOF and i == 0) else []
            new = _line(tpl, z, p, srcs, bes)
            if new["line_id"] in seen:
                raise InputsError(f"zone {z['zone_id']}: line {new['location']['element_id']} repeats an id")
            seen.add(new["line_id"])
            log["lines_added"] += 1
            log["by_state"][new["evidence_state"]] = log["by_state"].get(new["evidence_state"], 0) + 1
            zl["lines"].append(new["line_id"])
            held = [{"what": f"{b['what']} {z['zone_id']} {b.get('run') or ''}".strip(), "why": str(b.get("why"))[:300],
                     "range": None if b.get("bound") is None else f"0 .. {_fmt(b['bound'])} {b['unit']}",
                     "scenario": None} for b in bes]
            if new["evidence_state"] != VALUED_STATE:
                held.insert(0, {"what": f"{new['item_code']} {z['zone_id']} {p[1]}", "why": str(p[6])[:300],
                                "range": None if p[4] is None else f"0 .. {_fmt(p[4])}", "scenario": None})
            changes.append(A305._change(
                P_ZONE, "ADD", None, new, step="ADD_ZONE", drawing_reference="; ".join(s["file"] for s in srcs),
                verification=A3043._ver(srcs), group=new["item_code"],
                evidence_status=z["evidence_status"] if new["evidence_state"] == VALUED_STATE else "HELD",
                held=held, guard_element={"element_id": new["location"]["element_id"], "part": "WHOLE"},
                downstream=[f"coverage: {new['item_code']} {z['zone_id']} {p[1]} now has its line "
                            f"({new['evidence_state']})"]))
        log["zones"].append(zl)
    log["by_state"] = dict(sorted(log["by_state"].items()))
    log["default_guard"] = guard_recheck(doc, prev, changes)
    return changes, log


def guard_recheck(doc, prev, changes):
    """the merged default guard over the V3.0.57 lines + this version's added lines (arch_v307). Any finding that
    would hold a line refuses the run (this version only adds its own lines)."""
    ch_g, log_g = A307.guard_changes(doc, list(prev), changes, set())
    if ch_g:
        raise ValueError(f"{METHOD}: the default guard holds {len(ch_g)} line(s) "
                         f"({', '.join(sorted(c['before']['line_id'] for c in ch_g)[:5])}): an earlier stage owns "
                         f"them; the run is refused, nothing outside the roof waterproofing codes moves")
    return log_g


# ================================================================================================ checks
def check_exposed_slab(lines):
    """R-T507-1 on the integrated lines (a no-op on lines without a V3.0.58 record): a valued line carries its
    record's value; a held line carries no figure (bounded 0 .. its bound, or blank with its question); one line per
    (zone, code, element); only FIN.WP.ROOF / FIN.WP.ROOF_UPTURN. -> summary."""
    out = {"lines": 0, "valued": {}, "bounded": {}, "blank": 0, "zones": set(), "beside_items": 0}
    seen = set()
    for ln in lines:
        rec = ((ln.get("calculation") or {}).get("inputs") or {}).get(REC_KEY)
        if not rec:
            continue
        if ln["item_code"] not in CODES:
            raise ValueError(f"{METHOD}: a V3.0.58 record on {ln['item_code']} {ln['line_id']}")
        k = ln["location"]["element_id"]
        if k in seen:
            raise ValueError(f"{METHOD}: element {k} carried by two lines")
        seen.add(k)
        st = ln["evidence_state"]
        key = f"{ln['item_code']}|{ln['unit']}"
        if st == VALUED_STATE:
            if ln.get("measured_net") is None or abs(ln["measured_net"] - rec["value"]) > 1e-9 or not rec["value"]:
                raise ValueError(f"{METHOD}: {ln['line_id']} does not carry its record's value")
            out["valued"][key] = _r(out["valued"].get(key, 0.0) + ln["measured_net"])
        elif st == BOUNDED_STATE:
            br = ln.get("bounded_range") or {}
            if ln.get("measured_net") is not None or br.get("low") != 0.0 or abs(br.get("high", -1) - rec["bound"]) > 1e-9:
                raise ValueError(f"{METHOD}: held line {ln['line_id']} is not 0 .. its bound")
            out["bounded"][key] = _r(out["bounded"].get(key, 0.0) + br["high"])
        elif st == HELD_STATE:
            if ln.get("measured_net") is not None or ln.get("bounded_range"):
                raise ValueError(f"{METHOD}: held line {ln['line_id']} carries a figure (held is BLANK, never 0)")
            out["blank"] += 1
        else:
            raise ValueError(f"{METHOD}: {ln['line_id']} state {st}")
        for b in rec.get("held_beside") or ():
            if b.get("status") not in (WPA.HELD, WPA.RFI):
                raise ValueError(f"{METHOD}: {ln['line_id']} beside item {b.get('what')} is {b.get('status')}")
        out["beside_items"] += len(rec.get("held_beside") or ())
        out["zones"].add(rec["zone_id"])
        out["lines"] += 1
    out["zones"] = sorted(out["zones"])
    out["valued"] = dict(sorted(out["valued"].items()))
    out["bounded"] = dict(sorted(out["bounded"].items()))
    return out


# ================================================================================================ totals view (T-512)
def total_view(e):
    """one arch_v304.code_totals record -> its export view (T-512 T512_HELD_TOTALS_VIEW_V1, the CT schema)."""
    lines, bounded, blank = e["lines"], e["bounded_lines"], e["blocked_lines"]
    valued = lines - bounded - blank
    if min(lines, valued, bounded, blank) < 0:
        raise ValueError(f"{METHOD}: inconsistent line counts {e}")
    out = {"lines": lines, "valued_lines": valued, "bounded_lines": bounded, "blank_lines": blank,
           "released": None, "held_range": None}
    if lines == 0:
        out.update(status="NO_LINES", text="no lines")
    elif valued == lines:
        out.update(status="ALL_VALUED", released=_r(e["released"]), text=f"{_r(e['released'])}")
    elif valued:
        out.update(status="PARTIAL", released=_r(e["released"]),
                   text=f"AT_LEAST {_r(e['released'])} + HELD ({lines - valued} lines: {bounded} bounded, "
                        f"{blank} blank)")
        if bounded and not blank:
            out["held_range"] = [_r(e["held_low"]), _r(e["held_high"])]
    elif blank == 0:
        out.update(status="HELD_BOUNDED", held_range=[_r(e["held_low"]), _r(e["held_high"])],
                   text=f"HELD range {_r(e['held_low'])}..{_r(e['held_high'])} ({bounded} bounded lines)")
    else:
        out.update(status="HELD", text=f"HELD ({blank} blank lines" + (f", {bounded} bounded)" if bounded else ")"))
    return out


def totals_view(totals):
    v = {k: (None if e is None else total_view(e)) for k, e in sorted(totals.items())}
    bad = [k for k, x in v.items() if x and x["valued_lines"] == 0 and x["lines"] and
           re.fullmatch(r"-?[0-9.]+", x["text"])]
    if bad:
        raise ValueError(f"{METHOD}: codes with no valued line print a number: {bad[:5]}")
    return v


# ================================================================================================ integrate / write
def integrate(prev, changes, for_lead=()):
    """-> (V3.0.58 lines, identity). Added lines follow the candidate lines; every candidate line is byte-identical
    (asserted); the earlier versions' checks re-run on the result (the V3.0.57 set)."""
    sid = {ln["line_id"]: i for i, ln in enumerate(prev)}
    adds = []
    for c in changes:
        a = c["after"]
        if a["item_code"] not in CODES or c["action"] != "ADD":
            raise ValueError(f"{METHOD}: {c['action']} {a['item_code']} is not a change this version may make")
        if a["line_id"] in sid:
            raise ValueError(f"{METHOD}: an added line repeats a candidate id")
        adds.append(a)
    out = list(prev) + adds
    if len({ln["line_id"] for ln in out}) != len(out):
        raise ValueError(f"{METHOD}: a BOQ line id appears twice")
    _o, i57 = A3057.integrate(out, [], for_lead)     # every V3.0.10 .. V3.0.57 family check, re-run on these lines
    ident = {"base_lines": len(prev), "v3_0_58_lines": len(out), "v3_0_58_rows": len(changes), "replaced": 0,
             "added": len(adds), "checks_v3_0_57": {k: v for k, v in i57.items() if k not in (
                 "base_lines", "v3_0_57_lines", "v3_0_57_rows", "replaced", "added", "outside_rows",
                 "outside_rows_identical_to_base", "outside_rows_sha256")},
             "exposed_slab_wp": check_exposed_slab(out)}
    pids = {(ln["project"]["project_id"], ln["project"]["revision_set_sha256"]) for ln in out}
    if len(pids) != 1:
        raise ValueError(f"{METHOD}: {len(pids)} project identities in the lines")
    bad = [a["line_id"] for a in prev if A30.line_sha(a) != A30.line_sha(out[sid[a["line_id"]]])]
    if bad:
        raise ValueError(f"{METHOD}: {len(bad)} candidate line(s) differ")
    ident.update(outside_rows=len(prev), outside_rows_identical_to_base=len(prev),
                 outside_rows_sha256=hashlib.sha256("".join(A30.line_sha(x) for x in prev).encode()).hexdigest())
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
                     "before_released_v2_9": b29, "before_base": A30._qty(None), "after_v3_0_58": A30._qty(ref),
                     "evidence_status": c.get("evidence_status"), "still_held": c.get("held"),
                     "release_status": "NOT RELEASED",
                     "owner_manual_method": PIECES[c["piece"]]["owner_manual_method"],
                     "drawing_derived_method": PIECES[c["piece"]]["drawing_method"],
                     "record": rec, "verification": c.get("verification") or {}, "rollback": ROLLBACK})
    return rows


LEDGER_CSV = ("version", "piece", "action", "change", "line_id", "item_code", "floor", "element_id", "unit",
              "v2_9", "base", "v3_0_58", "evidence_status", "still_held", "verification")
DIFF_CSV = ("line_id", "item_code", "floor", "element_id", "unit", "vs_base", "vs_released_v2_9", "v2_9", "base",
            "v3_0_58")


def ledger_csv(rows):
    def q(x):
        return A302._q(x) if x and (x.get("value") is not None or x.get("low") is not None or x.get("state")) else ""

    def h(r):
        return "; ".join(f"{x['what']} {x.get('range') or ''}".strip() for x in (r.get("still_held") or ()))[:300]
    return A305._csv([{"version": r["version"], "piece": r["piece"], "action": r["action"], "change": r["change"],
                       "line_id": r["line_id"], "item_code": r["item_code"], "floor": r.get("floor") or "",
                       "element_id": r.get("element_id") or "", "unit": r["unit"],
                       "v2_9": q(r.get("before_released_v2_9")), "base": "",
                       "v3_0_58": q(r.get("after_v3_0_58")), "evidence_status": r["evidence_status"],
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
                    "base": A302._q(A30._qty(o)) if o else "", "v3_0_58": A302._q(A30._qty(ln))})
    return out


def check_totals(t0, t1):
    """-> the moved totals with their views; refuses a move outside FIN.WP.ROOF / FIN.WP.ROOF_UPTURN."""
    keys = [k for k in sorted(set(t0) | set(t1)) if t0.get(k) != t1.get(k)]
    for k in keys:
        if k.split("|")[0] not in CODES:
            raise ValueError(f"{METHOD}: totals moved outside this version's codes: {k}")
    return {k: {"base": t0.get(k), "v3_0_58": t1.get(k),
                "view_base": None if t0.get(k) is None else total_view(t0[k]),
                "view_v3_0_58": None if t1.get(k) is None else total_view(t1[k])} for k in keys}


def write(out, prev, changes, log, released_lines=None, for_lead=()):
    """the V3_0_58_* files beside the base candidate's files. -> (file names, identity, ledger)."""
    from pathlib import Path
    from engine.source import boq_line as BL
    out = Path(out)
    new, ident = integrate(prev, changes, for_lead)
    rows = ledger_rows(changes, released_lines)
    diff = diff_rows(prev, new, released_lines)
    named = {c["after"]["line_id"] for c in changes}
    stray = [d["line_id"] for d in diff if d["vs_base"] != "SAME" and d["line_id"] not in named]
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
    moved = check_totals(t0, t1)
    view = totals_view(t1)
    held_codes = sorted(k for k, v in view.items() if v and v["status"] in ("HELD", "HELD_BOUNDED"))
    led = {"schema": LEDGER_SCHEMA, "method": METHOD, "extends": EXTENDS, "candidate": CANDIDATE,
           "base": A30.BASE_METHOD, "released": A30.RELEASED_METHOD, "released_default": False, "rows": rows,
           "zones": log.get("zones"), "waiting_pieces": WAITING, "integration_package": True}
    run = {"method": METHOD, "policy": POLICY_ID, "extends": EXTENDS, "candidate": CANDIDATE,
           "base_method": A30.BASE_METHOD, "released_method": A30.RELEASED_METHOD, "released_default": False,
           "rollback": ROLLBACK, "identity": ident, "pieces": PIECES, "piece_logs": [log],
           "totals_moved_by_code": moved, "code_totals_view": view,
           "code_totals_view_rule": "T-512 T512_HELD_TOTALS_VIEW_V1 (AGENT_BRIEF 'HELD is never 0', R-T499-1, "
                                    "UP-QTY-STATUS-001): a code with no valued line never prints a number",
           "codes_held_no_valued_line": held_codes, "waiting_pieces": WAITING}
    files = {"V3_0_58_BOQ_LINES.json": BL.dumps(new),
             "V3_0_58_BOQ_LINES.csv": A30._lines_csv(new),
             "V3_0_58_INTEGRATION_LEDGER.json": A30._j(led),
             "V3_0_58_INTEGRATION_LEDGER.csv": ledger_csv(rows),
             "V3_0_58_DIFF.csv": A305._csv(diff, DIFF_CSV),
             "V3_0_58_RUN.json": A30._j(run)}
    for name, text in files.items():
        (out / name).write_text(text, encoding="utf-8")
    return sorted(files), ident, led


def policy_record():
    return {"method": METHOD, "extends": EXTENDS, "pieces": sorted(PIECES), "inputs_schema": INPUTS_SCHEMA,
            "released_default": False, "rollback": ROLLBACK, "actions": list(ACTIONS)}


__all__ = ["METHOD", "PIECES", "WAITING", "DEFAULT_GUARD_CLASS", "INPUTS_SCHEMA", "CODES", "load_inputs",
           "changes_for", "guard_recheck", "check_exposed_slab", "total_view", "totals_view", "check_totals",
           "integrate", "ledger_rows", "diff_rows", "write", "InputsError"]
