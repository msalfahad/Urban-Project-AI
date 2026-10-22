"""ARCH_TAKEOFF_V3.0.2 (T-142): the SAME opt-in BOQ candidate as ARCH_TAKEOFF_V3.0 / V3.0.1 (engine.source.arch_v30,
engine.source.arch_v301), extended with three more checker-verified pieces and the fixes of the three V3.0.1 Gate B
defects. Not a new method family and not the released default (owner management decision 2026-10-20 sections 2 and
5); rollback is running the released ARCH_TAKEOFF_V2.9.

How it is built (tools/urban_boq_m9.py `arch --method ARCH_TAKEOFF_V3.0.2`):
  1. the run is the V3.0.1 candidate exactly: its V3_0_* and V3_0_1_* files are written unchanged (arch_v30 and
     arch_v301 are not edited);
  2. the V3.0.2 pieces below propose changes of named lines of the V3.0.1 lines; a line two V3.0.2 pieces change is
     refused, and a line V3.0.1 replaced or added is never replaced again here, except by a fix of a named V3.0.1
     defect (SCOPE_FIX, Gate B D3) - only EVIDENCE may otherwise be attached to a line whose V3.0.1 change was itself
     evidence;
  3. the V3_0_2_* files are written beside them: every line outside the V3.0.2 rows is byte-identical to the V3.0.1
     line (asserted on every run: identity.vs_v3_0_1), and V3_0_2_DIFF.csv lists every line against V3.0.1 and against
     the released V2.9 + route G.

Pieces added in V3.0.2 (each carries a verifier MERGED verdict; PIECES names task, merge commit and verifier run):
  FOOTING_REBAR      FOOTING_REBAR_POPULATION_V1 (T-136) on the footings route G releases: route G's footing steel lines
                     (one per footing and diameter, kg from its convention cover and fractional per-metre counts) are
                     replaced by the piece's lines, one per footing and bar component: a printed count 'n T d' with the
                     printed cover and a cited straight bar end -> its kg (SOURCE_DERIVED); a per-metre / spacing
                     count -> HELD with the A / B readings as its range (owner Q-71 open), never one value, never 0; a
                     footing held by route G (two labels, clipped outline, size conflict) -> its steel HELD; the BOXED
                     cell of a schedule row -> a held line with its printed text, unquantified. Schedule rows are read
                     from the structural drawing (block attributes); the size unit, the cover note and the bar-end
                     detail come from the project inputs (typed from the printed sheets, owner Q-17 A).
  MEMBRANE_PROOF     MEMBRANE_COVERAGE_PROOF_V1 (T-137) on every roll line: each layout of the area the run folded is
                     proved; the proof is attached to the line as evidence (calculation.inputs.v3_0_2_membrane_proof);
                     counts unchanged. A layout that leaves UNDECLARED residue FAILS THE BUILD (MembraneProofError):
                     the candidate is not written.
  SOFFITS            the soffits over outside air (T-127; owner Q-67 A cond, Q-68 C): one ceiling-area line per place
                     from the project inputs (typed DRAWING-VERIFIED records with their drawing reference and the
                     verification that checked them; URBAN-CEILING-QUANTITY-WITHOUT-MATERIAL@v1: the area is published,
                     material BY_SPEC); the finish is HELD (Q-68 C) and option A (exterior plaster + paint) is shown
                     only in its own provisional field, never as a line; head soffits of openings and frame recesses
                     (listed apart in the inputs) are listed in the run record, never added.
  SCOPE_FIX          Gate B defects of V3.0.1: D3 the held merged lower bounds of the ground-beam and strap blinding
                     (ROUTE_G_SCOPE_V1 footprint REACH: a footing without an outline takes its label window); D2 the
                     storey summary of the column lines is rebuilt from the V3.0.2 lines (columns_by_storey equals the
                     line totals; lines the scope piece does not evaluate are listed); D1 is in the runners.

Rules: owner decision 2026-10-20 sections 2 and 5, WORKFLOW_CONTROLS 2026-10-21 section 5, Q-17 A, Q-21 C, Q-31 C,
Q-58 A, Q-67 A cond, Q-68 C, Q-71 (open), URBAN-REBAR-NET-AND-PROCUREMENT@v1, URBAN-CEILING-QUANTITY-WITHOUT-MATERIAL@v1,
UP-QTY-STATUS-001 (held is a range or blocked, never 0). Nothing here names a project, a sheet, a layer, a mark or a
coordinate; every number comes from the run, the drawings or the project inputs.
"""

from __future__ import annotations

import copy
import csv
import hashlib
import io

from engine.source import arch_v30 as A30
from engine.source import arch_v301 as A301

METHOD = "ARCH_TAKEOFF_V3.0.2"
EXTENDS = A301.METHOD
CANDIDATE = A30.METHOD                  # the candidate family this version extends (never a new method family)
POLICY_ID = "URBAN_BOQ_T142_ARCH_V3_0_2"
LEDGER_SCHEMA = "URBAN_V302_INTEGRATION_LEDGER_V1"
INPUTS_SCHEMA = "URBAN_V302_PROJECT_INPUTS_V1"
ROLLBACK = A30.ROLLBACK
STEEL_TRADE = "REINFORCEMENT"
REBAR_CODE = "STR.REBAR"
SOFFIT_CODE = "FIN.CEILING"
SOFFIT_ELEMENT = "SOFFIT_OVER_OUTSIDE_AIR"
BLINDING_HELD_FAMILIES = ("GROUND_BEAM", "STRAP")
EVIDENCE_STATUS = ("VERIFIED", "DRAWING-CONFIRMED", "ASSUMED - OWNER-APPROVED", "HELD", "UNKNOWN")
FOOTING_UNIT_MASS = {"method": "D2_OVER_162"}       # the project's kg/m (rebar_unit_mass), as FOOTING_REBAR_POPULATION

PIECES = {
    "FOOTING_REBAR": {
        "module": "engine/source/footing_rebar_population_v1.py", "policy": "FOOTING_REBAR_POPULATION_V1",
        "task": "T-136", "merge_commit": "6d532c5",
        "verifier_run": "verifier MERGED 6d532c5 (Gate A; released and held footing steel re-counted)",
        "owner_rules": ["URBAN-REBAR-NET-AND-PROCUREMENT@v1 (kg = count x length x kg/m; 12 m stock)",
                        "Q-71 open (count for per-metre / spacing notation): HELD with readings A / B",
                        "Q-17 A (the printed schedule size and the printed cover note govern)",
                        "Q-31 C (a footing in conflict stays held)", "UP-QTY-STATUS-001"],
        "owner_manual_method": "manual QS take-off by footing: the schedule count, bar = side - 2 x cover from the "
                               "general notes, kg = d^2 / 162 per m; per-metre notation by hand practice as spacing "
                               "count + 1 (reading B) - not set by the owner (Q-71), so shown, never released",
        "drawing_method": "FOOTING_REBAR_POPULATION_V1: schedule rows read from the drawing's block attributes, bound "
                          "by mark to route G's footings; printed count x (side - 2 x printed cover) x d^2/162; "
                          "per-metre / spacing counts held as A = ceil(inside / s), B = A + 1, C = rate x side"},
    "MEMBRANE_PROOF": {
        "module": "engine/source/membrane_coverage_proof_v1.py", "policy": "MEMBRANE_COVERAGE_PROOF_V1",
        "task": "T-137", "merge_commit": "18913db",
        "verifier_run": "verifier 2026-10-21 04:10 UTC (MERGED 18913db; 688 layouts proved, 0 failed)",
        "owner_rules": ["UP-WP-001 .. UP-WP-005", "Q-29", "Q-35 C", "Q-49 A", "Q-58 A conditional (proven plan)"],
        "owner_manual_method": "owner Q-49 A / Q-58 A: rolls per area; a piece cut from that area's own offcut only "
                               "on a proven physical cutting plan (the count is the V2.13 count, unchanged)",
        "drawing_method": "MEMBRANE_COVERAGE_PROOF_V1: the surface rebuilt from the outline, every laid sheet and "
                          "declared patch tested against it on a 1 mm grid; undeclared residue fails the build"},
    "SOFFITS": {
        "module": "engine/source/arch_v302.py (typed project records)", "policy": "SOFFITS_OVER_OUTSIDE_AIR_V1",
        "task": "T-127", "merge_commit": "5315d48",
        "verifier_run": "verifier 2026-10-21 04:10 UTC (MERGED 5315d48; pool-court soffit re-measured)",
        "owner_rules": ["Q-67 A conditional (side passage outside air; condition met, T-123)",
                        "Q-68 C (finish held; option A exterior plaster + paint provisional only)",
                        "URBAN-CEILING-QUANTITY-WITHOUT-MATERIAL@v1 (area published, material BY_SPEC)",
                        "Q-17 A (typed drawing values, DRAWING-VERIFIED)", "UP-QTY-STATUS-001"],
        "owner_manual_method": "owner Q-68: option A (exterior plaster + exterior paint over the soffit area) as the "
                               "PROVISIONAL estimating method only; the finish itself held (C)",
        "drawing_method": "soffit plan area face to face from the printed dimensions and drawn slab faces, net of "
                          "the drawn void; opening heads and frame recesses listed apart, never added"},
    "SCOPE_FIX": {
        "module": "engine/source/route_g_scope_v1.py (footprint REACH, T-142)", "policy": "ROUTE_G_SCOPE_V1",
        "task": "T-142 (Gate B defects of T-133)", "merge_commit": "this candidate",
        "verifier_run": "verifier 2026-10-21 17:40 UTC Gate B on V3.0.1: D1 / D2 / D3",
        "owner_rules": ["Q-21 C (ground-beam blinding held while the founding detail is open)",
                        "UP-QTY-STATUS-001 (a held range holds the true value: its low end never above it)"],
        "owner_manual_method": None,
        "owner_manual_note": "no separate owner manual method for blinding scope: the owner answers bind the drawing "
                             "method; the checker's hand values are the reference the held range must contain",
        "drawing_method": "ROUTE_G_SCOPE_V1 footprint REACH: strips merged against every outlined footing and, for a "
                          "footing route G holds without an outline, against its label window (1.6 x its longest "
                          "schedule side, member_detection's own search window)"},
}
WAITING = {k: v for k, v in A301.WAITING.items() if k != "T-136 / T-137 / T-127"}
WAITING.update({
    "T-146": "slab faces released only with slab evidence (after T-139 MERGED): same candidate, next extension",
    "T-151": "column steel and ground-beam / strap steel hand ledgers, 3 planted columns HELD: same candidate",
    "SOFFIT_READER": "the five soffit areas enter as typed DRAWING-VERIFIED records (owner Q-17 A); a generic reader "
                     "of slabs over outside air from the drawing is not built yet",
    "Q-71": "footing steel per-metre / spacing count: held A .. B until the owner answers",
})


class MembraneProofError(RuntimeError):
    """a layout leaves undeclared residue: the candidate is not written."""


class InputsError(ValueError):
    pass


# ================================================================================================ helpers
def _r(x, n=6):
    return None if x is None else round(float(x), n)


def _note(ln, text):
    ln["notes"] = (ln.get("notes") + "; " if ln.get("notes") else "") + text


def _inputs(ln, key, rec):
    ln["calculation"] = dict(ln["calculation"], inputs=dict(ln["calculation"].get("inputs") or {}, **{key: rec}))


def _change(piece, action, before, after, **kw):
    return dict({"piece": piece, "action": action, "before": before, "after": after}, **kw)


def _proj(lines):
    """project id, revision sha and documents of a run (from its first line)."""
    for ln in lines:
        p = ln.get("project") or {}
        if p.get("project_id"):
            return p["project_id"], p.get("revision_set_sha256"), (ln.get("source") or {}).get("documents") or []
    return "new project", None, []


# ================================================================================================ project inputs
def load_inputs(doc, project_id=None):
    """URBAN_V302_PROJECT_INPUTS_V1 or None. Every value carries the printed place it was typed from."""
    if doc is None:
        return None
    if doc.get("schema") != INPUTS_SCHEMA:
        raise InputsError(f"project inputs: schema must be {INPUTS_SCHEMA}")
    if project_id and doc.get("project") not in (None, project_id):
        raise InputsError(f"project inputs are for {doc.get('project')!r}, the run is {project_id!r}")
    fr = doc.get("footing_rebar")
    if fr is not None:
        su = fr.get("size_unit") or {}
        if su.get("value") not in ("mm", "cm", "m") or not su.get("source"):
            raise InputsError("footing_rebar.size_unit needs value mm / cm / m and its printed source")
        cv = fr.get("cover")
        if cv is not None and (not cv.get("value_mm") or not cv.get("source") or
                               cv.get("wording") not in ("MINIMUM", "EXACT")):
            raise InputsError("footing_rebar.cover needs value_mm, wording MINIMUM / EXACT and its printed source")
        for la, e in (fr.get("end_treatment") or {}).items():
            if la not in ("BOTTOM", "TOP"):
                raise InputsError(f"footing_rebar.end_treatment: layer {la}")
            if e is not None and (e.get("state") != "STRAIGHT" or not e.get("source")):
                raise InputsError(f"footing_rebar.end_treatment.{la}: state STRAIGHT with the cited detail, or null")
    so = doc.get("soffits")
    if so is not None:
        seen = set()
        for p in so.get("places") or ():
            if not p.get("place") or p["place"] in seen:
                raise InputsError("soffits: every place has a unique id")
            seen.add(p["place"])
            if not (isinstance(p.get("m2"), (int, float)) and p["m2"] > 0):
                raise InputsError(f"soffits {p['place']}: m2 > 0 (a held area is not typed here)")
            if p.get("status") != "DRAWING-VERIFIED" or not p.get("drawing_reference") or not p.get("verification"):
                raise InputsError(f"soffits {p['place']}: status DRAWING-VERIFIED, drawing_reference and "
                                  "verification are required (owner Q-17 A)")
            if p.get("evidence_status") not in EVIDENCE_STATUS[:2]:
                raise InputsError(f"soffits {p['place']}: evidence_status VERIFIED or DRAWING-CONFIRMED")
    return doc


# ================================================================================================ FOOTING_REBAR
def schedule_rows_from_drawing(structural_path, size_unit):
    """footing schedule rows drawn as blocks with one attribute per cell (a mark attribute and bar cells SH-* / LO-*),
    read as printed (FOOTING_REBAR_POPULATION_V1.rows_from_block_attributes). -> rows"""
    import ezdxf
    from engine.source import footing_rebar_population_v1 as P
    doc = ezdxf.readfile(str(structural_path))
    rows = []
    for e in doc.modelspace().query("INSERT"):
        at = {x.dxf.tag: x.dxf.text for x in e.attribs}
        up = {str(k).upper() for k in at}
        if (up & {"FO-TY", "TYPE", "MARK"}) and any(k.startswith(("SH-", "LO-")) for k in up):
            rows.append(P.rows_from_block_attributes(at, size_unit, source=f"INSERT {e.dxf.handle} block "
                                                                           f"{e.dxf.name}"))
    return rows


def footing_rebar_changes(R, rows, lines, inputs):
    """FOOTING_REBAR_POPULATION_V1 on route G's footings; rows: schedule_rows_from_drawing(...). -> (changes, log)."""
    from engine.source import boq_line as BL
    from engine.source import footing_rebar_population_v1 as P
    log = {"piece": "FOOTING_REBAR", "state": "NOT_RUN"}
    fr = (inputs or {}).get("footing_rebar")
    if R is None:
        log["state"] = "NO_ROUTE_G_RESULT"
        return [], log
    if fr is None:
        log["state"] = "NO_PROJECT_INPUT"
        log["why"] = "no footing_rebar record in the project inputs: route G's footing steel lines stay as they are"
        return [], log
    foot = P.footings_from_route_items(R["items"])
    res = P.run(foot, rows, cover=fr.get("cover"), end_treatment=fr.get("end_treatment") or {},
                unit_mass=FOOTING_UNIT_MASS)
    if not res["check"]["all_pass"]:
        raise ValueError(f"{METHOD}: FOOTING_REBAR_POPULATION_V1 conservation check failed: {res['check']}")
    pid, rev, docs = _proj(lines)
    route = {}
    for ln in lines:
        if ln["item_code"] == REBAR_CODE and ln["trade"] == STEEL_TRADE and \
                str(ln.get("physical_element")) == "FOOTINGS":
            route.setdefault(ln["location"]["element_id"], ln)
    by_occ = {o["occurrence_id"]: [] for o in res["occurrences"]}
    for eid, ln in sorted(route.items()):
        occ = next((o for o in by_occ if str(eid).split(":", 1)[-1].startswith(str(o) + ":")), None)
        if occ is None:
            raise ValueError(f"{METHOD}: route footing steel line {eid} names no footing the piece reads")
        by_occ[occ].append(ln)
    ref = ("structural set: footing schedule (" + ", ".join(sorted({r['source'].split(' block ')[-1] for r in rows}))
           + "), foundation plan; " + f"size unit: {fr['size_unit']['source']}; cover: "
           f"{(fr.get('cover') or {}).get('source', 'not printed')}; bar ends: " +
           "; ".join(f"{k.lower()} {v['source']}" for k, v in sorted((fr.get('end_treatment') or {}).items()) if v))
    comps = {}
    for c in res["components"]:
        comps.setdefault(c["occurrence_id"], []).append(c)
    changes, rows_log = [], []
    tot = {"released_kg": 0.0, "held_low_kg": 0.0, "held_high_kg": 0.0, "held_unquantified_lines": 0,
           "route_kg": 0.0, "superseded_route_lines": 0}

    def line(occ, comp, ev, kg=None, rng=None, reasons=(), raw=None, dia=None, formula=None, extra=None):
        rfi = None
        if ev in ("BOUNDED_EXPOSURE", "BLOCKED_RFI"):
            rfi = {"question": "; ".join(reasons) or "held", "unlocks": f"{occ['occurrence_id']}:{comp}"}
        ln = BL.make_line(project_id=pid, revision_set_sha256=rev, item_code=REBAR_CODE, unit="kg",
                          evidence_state=ev, measured_net=_r(kg) if ev == "SOURCE_DERIVED" else None,
                          bounded_range=rng, element_id=f"FRP:{occ['occurrence_id']}:{comp}", floor="FOUNDATION",
                          physical_element="FOOTINGS", subtrade="FOOTINGS" + (f" / {dia:g} mm" if dia else ""),
                          formula=formula or ("held: " + "; ".join(reasons)),
                          inputs=dict({"policy": P.POLICY_ID, "mark": occ.get("mark"), "component": comp,
                                       "printed": raw, "reasons": list(reasons)}, **(extra or {})),
                          documents=docs, geometry_source="SCHEDULE_ONLY",
                          geometry_confidence="TOLERANCE_CERTIFIED" if ev == "SOURCE_DERIVED" else
                          "INFERRED_CANDIDATE", rule_id=P.RULE_ID, rule_version="v1", material_state="SOURCE",
                          rfi=rfi, notes=f"{METHOD}: footing steel by bar population (FOOTING_REBAR_POPULATION_V1, "
                                         f"T-136)")
        return ln

    for o in sorted(res["occurrences"], key=lambda x: str(x["occurrence_id"])):
        new = []
        for c in comps.get(o["occurrence_id"], []):
            if c["status"] == P.NOT_APPLICABLE:
                continue
            if c["status"] == P.RELEASED:
                new.append(line(o, c["component"], "SOURCE_DERIVED", kg=c["net_kg"], raw=c.get("raw"),
                                dia=c.get("dia_mm"), formula=c.get("formula"),
                                extra={"count": c.get("count"), "bar_length_m": _r(c.get("bar_length_m")),
                                       "kg_per_m": _r(c.get("kg_per_m")), "cover": c.get("cover_basis"),
                                       "procurement": c.get("procurement_note")}))
                tot["released_kg"] += c["net_kg"]
            elif c.get("net_kg_range"):
                lo, hi = c["net_kg_range"]
                new.append(line(o, c["component"], "BOUNDED_EXPOSURE", rng={
                    "low": _r(lo), "high": _r(hi), "basis": "count readings A (ceil inside / s) .. B (A + 1); "
                                                          "owner Q-71 open"},
                    reasons=c["reasons"], raw=c.get("raw"), dia=c.get("dia_mm"), formula=c.get("formula"),
                    extra={"count_range": list(c.get("count_range") or ()), "readings": {
                        k: {"count": _r(v["count"], 4), "kg": _r(v["kg"])} for k, v in (c.get("readings") or {}).items()},
                        "bar_length_m": _r(c.get("bar_length_m")), "cover": c.get("cover_basis")}))
                tot["held_low_kg"] += lo
                tot["held_high_kg"] += hi
            else:
                new.append(line(o, c["component"], "BLOCKED_RFI", reasons=c["reasons"], raw=c.get("raw"),
                                dia=c.get("dia_mm")))
                tot["held_unquantified_lines"] += 1
        if o.get("boxed_raw") is not None and o.get("mark"):
            new.append(line(o, "BOXED", "BLOCKED_RFI", raw=o["boxed_raw"], reasons=[
                f"BOXED bars printed {o['boxed_raw']!r} with no diameter: meaning not established (held, "
                "unquantified; an empty cell is not proof that no boxed bars exist)"]))
            tot["held_unquantified_lines"] += 1
        old = by_occ.get(o["occurrence_id"]) or []
        tot["route_kg"] += sum(x.get("measured_net") or 0.0 for x in old)
        for k in range(max(len(old), len(new))):
            if k < len(old) and k < len(new):
                changes.append(_change("FOOTING_REBAR", "REPLACE", old[k], new[k], drawing_reference=ref, held=[],
                                       downstream=[]))
            elif k < len(old):
                after = copy.deepcopy(old[k])
                after.update(evidence_state="NOT_APPLICABLE_WITH_EVIDENCE", measured_net=None, bounded_range=None,
                             rfi=None, notes=f"{METHOD}: SUPERSEDED - route G footing steel "
                                             f"({_r(old[k].get('measured_net'))} kg) is replaced by the "
                                             "FOOTING_REBAR_POPULATION_V1 lines of the same footing (T-136)")
                changes.append(_change("FOOTING_REBAR", "REPLACE", old[k], after, drawing_reference=ref, held=[],
                                       downstream=[]))
                tot["superseded_route_lines"] += 1
            else:
                changes.append(_change("FOOTING_REBAR", "ADD", None, new[k], drawing_reference=ref, held=[],
                                       downstream=[]))
        for ch in changes[-max(len(old), len(new)):] if (old or new) else ():
            a = ch["after"]
            if a["evidence_state"] in ("BOUNDED_EXPOSURE", "BLOCKED_RFI"):
                ch["held"] = [{"what": f"footing steel {o.get('mark') or '(two marks)'} "
                                       f"{a['calculation']['inputs'].get('component')}",
                               "why": (a.get("rfi") or {}).get("question"),
                               "range_kg": [a["bounded_range"]["low"], a["bounded_range"]["high"]]
                               if a.get("bounded_range") else None}]
        rows_log.append({"occurrence": o["occurrence_id"], "mark": o.get("mark"), "status": o["status"],
                         "held": o.get("held"), "released_kg": _r(o["released_kg"]),
                         "held_kg_range": [_r(x) for x in o["held_kg_range"]] if o["held_kg_range"] else None,
                         "held_unquantified": o["held_unquantified"], "route_lines": len(old), "new_lines": len(new)})
    t = res["totals"]
    for k, v in (("released_kg", t["released_kg"]), ("held_low_kg", t["held_kg_low"]),
                 ("held_high_kg", t["held_kg_high"])):
        if abs(tot[k] - v) > 1e-6:
            raise ValueError(f"{METHOD}: footing steel lines {k} {tot[k]} != piece total {v}")
    log.update(state="RUN", policy=P.POLICY_ID, cover=fr.get("cover"), size_unit=fr["size_unit"],
               end_treatment=fr.get("end_treatment"), schedule_rows=len(rows),
               schedule_rows_without_footing=res["schedule_rows_without_footing"],
               totals={k: _r(v) if isinstance(v, float) else v for k, v in tot.items()},
               count_readings_kg={k: _r(v) for k, v in res["count_readings_kg"].items()},
               occurrences=rows_log, check=res["check"])
    return changes, log


# ================================================================================================ MEMBRANE_PROOF
def prove_area(area):
    """MEMBRANE_COVERAGE_PROOF_V1 on one captured area -> the evidence record (a fold the method refuses is
    NOT_PROVEN with its reason; it never raises for that)."""
    from engine.source import membrane_coverage_proof_v1 as MP
    try:
        r = MP.prove_fold(area["polygon"], holes=area.get("holes") or (), unit_m=area.get("unit_m") or 1.0,
                          spec=area.get("spec"))
    except Exception as ex:                                  # noqa: BLE001 - listed, never dropped
        return {"state": "NOT_PROVEN", "why": f"the fold refuses the outline: {str(ex)[:200]}"}
    allx = r["v3"] + r["v4"]
    und = [f for x in allx for f in x["failures"] if f.startswith("UNDECLARED_RESIDUE")]
    c3 = r["chosen_v213"]
    s3 = r["v3"][c3["layout"]] if c3["layout"] is not None else None
    c5 = r["chosen_v5"]
    s5 = r["v4"][c5["layout"]]
    return {"state": "PROVED", "policy": MP.METHOD_ID, "verdict_all_layouts": r["verdict"],
            "layouts_proved": len(allx), "layouts_failed": sum(1 for x in allx if x["verdict"] == MP.FAILED),
            "undeclared_residue": und,
            "failure_kinds": sorted({f.split(":")[0] for x in allx for f in x["failures"]}),
            "chosen_v2_13": {"layout": s3 and s3["layout"], "rolls": c3.get("rolls"), "verdict": c3.get("verdict"),
                             "residue_m2": s3 and s3["residue_m2"], "declared_patch_m2": s3 and s3["declared_patch_m2"],
                             "patches": s3 and len(s3["patches"]), "double_need_m2": s3 and s3["double_need_m2"]},
            "chosen_v5": {"layout": s5["layout"], "rolls_by_reading": c5["rolls_by_reading"], "verdict": c5["verdict"],
                          "residue_m2": s5["residue_m2"], "declared_patch_m2": s5["declared_patch_m2"]},
            "floor_m2": _r(r["floor_m2"], 4)}


def membrane_proof_changes(areas, lines, *, prove=prove_area):
    """the coverage proof attached to every roll line as its evidence; counts unchanged; undeclared residue in any
    layout raises MembraneProofError (the build fails). -> (changes, log)."""
    log = {"piece": "MEMBRANE_PROOF", "lines": []}
    changes, cache, failed = [], {}, []
    for ln in lines:
        if ln["item_code"] not in A30.MEMBRANE_ITEMS:
            continue
        loc = ln.get("location") or {}
        a = A301._area_for(ln, areas or ())
        if a is None:
            pr = {"state": "NOT_PROVEN", "why": "HELD_LINE_NO_AREA_FOLDED" if A301._line_rolls(ln) is None else
                  "the area the run folded for this line is not identified once"}
        else:
            k = (repr(a["polygon"]), repr(tuple(a.get("holes") or ())), a.get("unit_m"), repr(a.get("spec")))
            if k not in cache:
                cache[k] = prove(a)
            pr = cache[k]
        if pr.get("undeclared_residue"):
            failed.append((ln["line_id"], loc.get("room_id"), pr["undeclared_residue"][:3]))
        after = copy.deepcopy(ln)
        _inputs(after, "v3_0_2_membrane_proof", pr)
        _note(after, f"{METHOD}: MEMBRANE_COVERAGE_PROOF_V1 attached (T-137): "
                     f"{pr.get('verdict_all_layouts') or pr['state']}; count unchanged")
        held = []
        if pr["state"] != "PROVED":
            held.append({"what": "roll count not proved by MEMBRANE_COVERAGE_PROOF_V1 (count kept; checker)",
                         "why": pr.get("why")})
        changes.append(_change("MEMBRANE_PROOF", "EVIDENCE_ATTACHED", ln, after,
                               drawing_reference=f"architectural plan {loc.get('floor')}: membrane area "
                                                 f"{loc.get('room_id')} (the outline the run folded)",
                               held=held, downstream=[]))
        log["lines"].append({"line_id": ln["line_id"], "floor": loc.get("floor"), "room_id": loc.get("room_id"),
                             "rolls": A301._line_rolls(ln), "state": pr["state"],
                             "verdict": pr.get("verdict_all_layouts"), "layouts": pr.get("layouts_proved"),
                             "chosen_v2_13": (pr.get("chosen_v2_13") or {}).get("verdict"), "why": pr.get("why")})
    if failed:
        raise MembraneProofError(f"{METHOD}: {len(failed)} roll line(s) whose layouts leave undeclared residue: "
                                 f"{failed}")
    return changes, log


# ================================================================================================ SOFFITS
def soffit_changes(inputs, lines):
    """one ceiling-area line per soffit place of the project inputs; finish HELD (Q-68 C). -> (changes, log)."""
    from engine.source import boq_line as BL
    log = {"piece": "SOFFITS", "state": "NOT_RUN", "places": [], "listed_apart": []}
    so = (inputs or {}).get("soffits")
    if so is None:
        log["state"] = "NO_PROJECT_INPUT"
        return [], log
    pid, rev, docs = _proj(lines)
    have = {ln["line_id"] for ln in lines}
    changes = []
    for p in so.get("places") or ():
        fin = {"status": "HELD", "rule": "owner Q-68 C", "question": so.get("finish_question") or "Q-68",
               "provisional_option_a": {"basis": "owner Q-68 option A, PROVISIONAL estimating method only (not a "
                                                 "line, not released)",
                                        "exterior_plaster_m2": _r(p["m2"], 4), "exterior_paint_m2": _r(p["m2"], 4)}}
        ln = BL.make_line(project_id=pid, revision_set_sha256=rev, item_code=SOFFIT_CODE, unit="m2",
                          evidence_state="SOURCE_DERIVED", measured_net=_r(p["m2"], 4),
                          element_id=f"SOFFIT:{p['floor']}:{p['place']}", floor=p["floor"], room_id=p["place"],
                          room_name_en=p.get("name_en"), physical_element=SOFFIT_ELEMENT,
                          formula=p.get("formula") or "soffit plan area, face to face (typed DRAWING-VERIFIED record)",
                          inputs={"policy": PIECES["SOFFITS"]["policy"], "record": {
                              k: p.get(k) for k in ("place", "status", "evidence_status", "drawing_reference",
                                                    "verification", "condition", "void_excluded_m2")},
                                  "finish": fin, "entered_by": "TYPED"},
                          documents=docs, geometry_source="CAD_VECTOR", geometry_confidence="TOLERANCE_CERTIFIED",
                          rule_id="URBAN-CEILING-QUANTITY-WITHOUT-MATERIAL", rule_version="v1",
                          material_state="BY_SPEC",
                          rfi={"question": "Q-68 C: soffit finish held until a finish schedule / designer answer "
                                           "(designer request filed); option A provisional only", "unlocks": p["place"]},
                          notes=f"{METHOD}: soffit over outside air (T-127); area published, finish HELD (Q-68 C)")
        if ln["line_id"] in have:
            raise ValueError(f"{METHOD}: soffit line {p['place']} repeats a V3.0.1 line id")
        changes.append(_change("SOFFITS", "ADD", None, ln, drawing_reference=p["drawing_reference"],
                               held=[{"what": f"soffit finish {p['place']}", "why": "owner Q-68 C",
                                      "provisional_option_a_m2": {"exterior_plaster": _r(p["m2"], 4),
                                                                  "exterior_paint": _r(p["m2"], 4)}}],
                               downstream=[{"what": "exterior plaster / paint lines of this soffit",
                                            "state": "NOT CREATED: finish HELD (Q-68 C)"}],
                               evidence_status=p["evidence_status"]))
        log["places"].append({"place": p["place"], "floor": p["floor"], "m2": _r(p["m2"], 4),
                              "evidence_status": p["evidence_status"], "verification": p["verification"]})
    log["listed_apart"] = [dict(x, added=False) for x in so.get("listed_apart") or ()]
    log["state"] = "RUN"
    log["total_m2"] = _r(sum(p["m2"] for p in so.get("places") or ()), 4)
    return changes, log


# ================================================================================================ SCOPE_FIX (D3, D2)
def scope_fix_changes(R, lines, to_line):
    """D3: the held ground-beam / strap blinding lines of V3.0.1 re-measured with ROUTE_G_SCOPE_V1 footprint REACH
    (the released footing blinding must not move). -> (changes, log)."""
    from engine.source import route_g_scope_v1 as SC
    log = {"piece": "SCOPE_FIX", "state": "NOT_RUN", "blinding": []}
    if R is None or not ((R.get("generic") or {}).get("D")):
        log["state"] = "NO_ROUTE_G_RESULT"
        return [], log
    v1 = SC.blinding_scope(R)
    rc = SC.blinding_scope(R, footprint="REACH")
    if v1.get("state") != "MEASURED" or rc.get("state") != "MEASURED":
        log["state"] = "BLINDING_NOT_MEASURED"
        return [], log
    if abs((v1["released_m3"] or 0) - (rc["released_m3"] or 0)) > 1e-9:
        raise ValueError(f"{METHOD}: footprint REACH moved the released footing blinding")
    sc = {"columns": [], "blinding": rc}
    new_items = {it["item_id"]: it for it in SC.apply(R, sc)}
    by_elem = {}
    for ln in lines:
        by_elem.setdefault((ln.get("location") or {}).get("element_id"), []).append(ln)
    changes = []
    ref = ("structural set: foundation plan (footing outlines and the labels of footings without an outline), "
           "ground-beam plan (beam strips), strap bands; typical detail (blinding thickness and projection)")
    for fam in BLINDING_HELD_FAMILIES:
        r1 = next((r for r in v1["records"] if r["family"] == fam), None)
        r2 = next((r for r in rc["records"] if r["family"] == fam), None)
        rec = {"family": fam, "v3_0_1_m3": r1 and (r1.get("exposure_m3") or r1.get("m3")),
               "v3_0_2_m3": r2 and (r2.get("exposure_m3") or r2.get("m3")), "status": r2 and r2["status"]}
        if r2 is None or r2["status"] != "HELD":
            log["blinding"].append(dict(rec, change="NONE (not a held family record)"))
            continue
        iid = f"U-C:PLAIN_CONCRETE:FOUNDATION:BLINDING_{fam}"
        hits = by_elem.get(iid) or []
        if len(hits) != 1 or iid not in new_items:
            log["blinding"].append(dict(rec, change="KEPT_LINE_NOT_FOUND_ONCE", lines=len(hits)))
            continue
        base = hits[0]
        after = to_line(new_items[iid])
        if A30._qty(after) == A30._qty(base):
            log["blinding"].append(dict(rec, change="NONE (same range)"))
            continue
        after["notes"] = base.get("notes") or ""
        _note(after, f"{METHOD}: held range re-measured (ROUTE_G_SCOPE_V1 footprint REACH, Gate B D3): the strips "
                     f"over a footing without an outline may merge into it, so the merged lower bound takes its "
                     f"label window; was {base.get('bounded_range')}")
        _inputs(after, "v3_0_2_scope_fix", {"footprint": "REACH", "no_outline_windows": rc.get("no_outline_windows"),
                                            "merged_low_bound": rc.get("merged_low_bound"),
                                            "v3_0_1_range": base.get("bounded_range")})
        changes.append(_change("SCOPE_FIX", "REPLACE", base, after, drawing_reference=ref, held=[{
            "what": f"blinding {fam}", "why": r2.get("reason"), "blocker": r2.get("blocker"),
            "range_m3": r2.get("exposure_m3")}], downstream=[], fixes_v3_0_1="Gate B defect D3 (verifier 2026-10-21 "
                                                                             "17:40 UTC)"))
        log["blinding"].append(dict(rec, change="CHANGED"))
    log["state"] = "RUN"
    log["no_outline_windows"] = rc.get("no_outline_windows")
    log["merged_low_bound"] = rc.get("merged_low_bound")
    return changes, log


def columns_by_storey(lines, scope_summary=None):
    """D2: the column concrete per storey from the lines themselves (released value, held range, not present), with
    the ROUTE_G_SCOPE summary reconciled: scope route total + the lines the scope piece does not evaluate = line total.
    -> {storey: {...}}"""
    out = {}
    scope_ids = set()
    for st, rec in (scope_summary or {}).items():
        for cid in rec.get("not_present") or ():
            scope_ids.add(cid)
    for ln in lines:
        if not str(ln["item_code"]).startswith("STR.CONC.COLUMN"):
            continue
        st = (ln.get("location") or {}).get("floor") or "UNKNOWN"
        k = out.setdefault(st, {"lines": 0, "released_m3": 0.0, "held_low_m3": 0.0, "held_high_m3": 0.0,
                                "held_unquantified": 0, "not_present_lines": 0})
        k["lines"] += 1
        q = A30._qty(ln)
        if q["value"] is not None:
            k["released_m3"] += q["value"]
        elif q["low"] is not None:
            k["held_low_m3"] += q["low"]
            k["held_high_m3"] += q["high"]
        elif ln["evidence_state"] == "NOT_APPLICABLE_WITH_EVIDENCE":
            k["not_present_lines"] += 1
        else:
            k["held_unquantified"] += 1
    for st, k in out.items():
        for x in ("released_m3", "held_low_m3", "held_high_m3"):
            k[x] = _r(k[x])
        s = (scope_summary or {}).get(st)
        if s is not None:
            k["scope_piece_released_m3"] = s.get("RELEASED")
            k["outside_scope_piece_released_m3"] = _r(k["released_m3"] - (s.get("RELEASED") or 0.0))
    return out


# ================================================================================================ integrate / ledger
def integrate(base_lines, v30_changes, v301_changes, v302_changes):
    """-> (V3.0.1 lines, V3.0.2 lines, identity). Every line outside the V3.0.2 rows is byte-identical to the
    V3.0.1 line; a line two V3.0.2 pieces change, or a V3.0.1 replaced / added line changed again, is refused."""
    from engine.source import boq_line as BL
    _l30, l301, _i = A301.integrate(base_lines, v30_changes, v301_changes)
    v301_touched = {}
    for c in v301_changes:
        if c["after"] is not None:
            v301_touched[c["after"]["line_id"]] = c["action"]
    ids = [ln["line_id"] for ln in l301]
    rep, adds = {}, []
    for c in v302_changes:
        if c["action"] in ("REPLACE", "EVIDENCE_ATTACHED"):
            lid = c["before"]["line_id"]
            if lid in rep:
                raise ValueError(f"{METHOD}: line {lid} changed by two V3.0.2 pieces")
            if lid in v301_touched and not (c["action"] == "EVIDENCE_ATTACHED" and
                                            v301_touched[lid] == "EVIDENCE_ATTACHED") and not c.get("fixes_v3_0_1"):
                raise ValueError(f"{METHOD}: line {lid} was changed by V3.0.1 ({v301_touched[lid]}); V3.0.2 only "
                                 "attaches evidence to such a line or fixes a named V3.0.1 defect")
            rep[lid] = c["after"]
        elif c["action"] == "ADD":
            adds.append(c["after"])
        else:
            raise ValueError(f"{METHOD}: action {c['action']}")
    if rep.keys() - set(ids):
        raise ValueError(f"{METHOD}: a change names a line the V3.0.1 run does not have")
    out = [rep.get(ln["line_id"], ln) for ln in l301]
    for a in adds:
        if a["line_id"] in set(ids):
            raise ValueError(f"{METHOD}: an added line repeats a V3.0.1 line id")
        out.append(a)
    if len({ln["line_id"] for ln in out}) != len(out):
        raise ValueError(f"{METHOD}: a BOQ line id appears twice")
    for ln in out:
        BL.validate(ln)
    touched = set(rep) | {ln["line_id"] for ln in rep.values()} | {a["line_id"] for a in adds}
    by301 = {ln["line_id"]: ln for ln in l301}
    outside = [ln for ln in out if ln["line_id"] not in touched]
    bad = [ln["line_id"] for ln in outside if ln["line_id"] not in by301 or
           A30.line_sha(by301[ln["line_id"]]) != A30.line_sha(ln)]
    lost = [i for i in by301 if i not in {ln["line_id"] for ln in out} and i not in touched]
    if bad or lost:
        raise ValueError(f"{METHOD}: {len(bad) + len(lost)} line(s) outside the V3.0.2 rows differ from {EXTENDS}")
    ident = {"v3_0_1_lines": len(l301), "v3_0_2_lines": len(out), "v3_0_2_rows": len(v302_changes),
             "replaced": sum(1 for c in v302_changes if c["action"] == "REPLACE"),
             "evidence_attached": sum(1 for c in v302_changes if c["action"] == "EVIDENCE_ATTACHED"),
             "added": len(adds), "outside_rows": len(outside), "outside_rows_identical_to_v3_0_1": len(outside),
             "outside_rows_sha256": hashlib.sha256("".join(A30.line_sha(x) for x in outside).encode()).hexdigest()}
    return l301, out, ident


def ledger_rows(changes, v301_lines, released_lines=None):
    """one row per V3.0.2 change: before (released V2.9 when given, V3.0.1), after, delta, drawing reference, owner
    manual and drawing-derived method, evidence status, verification, held, downstream."""
    rel = {A30._key(ln): ln for ln in released_lines or ()}
    rows = []
    for c in changes:
        ref = c["after"] if c["before"] is None else c["before"]
        b301 = A30._qty(c["before"]) if c["before"] is not None else dict(A30._qty(None), state="NOT_IN_V3_0_1")
        aft = A30._qty(c["after"])
        b29 = None
        if released_lines is not None:
            b29 = A30._qty(rel.get(A30._key(ref))) if A30._key(ref) in rel else dict(A30._qty(None),
                                                                                    state="NOT_IN_RELEASED")
        d = None
        if b301["value"] is not None and aft["value"] is not None:
            d = {"delta": _r(aft["value"] - b301["value"]),
                 "pct": _r(100.0 * (aft["value"] - b301["value"]) / b301["value"], 3) if b301["value"] else None}
        p = PIECES[c["piece"]]
        loc = ref.get("location") or {}
        rows.append({"version": METHOD, "piece": c["piece"], "action": c["action"], "line_id": ref["line_id"],
                     "after_line_id": c["after"]["line_id"], "item_code": ref["item_code"], "floor": loc.get("floor"),
                     "room_id": loc.get("room_id"), "element_id": c["after"]["location"].get("element_id"),
                     "unit": c["after"]["unit"], "before_released_v2_9": b29, "before_v3_0_1": b301,
                     "after_v3_0_2": aft, "change": d, "evidence_status": evidence_status(c),
                     "release_status": "NOT RELEASED", "drawing_reference": c.get("drawing_reference"),
                     "owner_manual_method": p.get("owner_manual_method") or p.get("owner_manual_note"),
                     "drawing_method": p["drawing_method"], "owner_rules": p["owner_rules"],
                     "verification": {k: p[k] for k in ("task", "merge_commit", "verifier_run", "module", "policy")},
                     "held": c.get("held") or [], "downstream": c.get("downstream") or [], "rollback": ROLLBACK})
    return rows


def evidence_status(c):
    """WORKFLOW_CONTROLS 2026-10-21 section 5, one per quantity."""
    a = c["after"]
    if c.get("evidence_status"):
        return c["evidence_status"]
    if a["evidence_state"] in ("BOUNDED_EXPOSURE", "BLOCKED_RFI"):
        return "HELD"
    if a["evidence_state"] in ("NOT_APPLICABLE_WITH_EVIDENCE", "EXCLUDED_WITH_REASON"):
        return "DRAWING-CONFIRMED"
    if c["piece"] == "MEMBRANE_PROOF":
        return "VERIFIED" if (a["calculation"]["inputs"].get("v3_0_2_membrane_proof") or {}).get(
            "state") == "PROVED" else "UNKNOWN"
    return "DRAWING-CONFIRMED"


LEDGER_CSV = ("version", "piece", "action", "line_id", "after_line_id", "item_code", "floor", "room_id", "element_id",
              "unit", "v2_9", "v3_0_1", "v3_0_2", "delta", "pct", "evidence_status", "release_status",
              "drawing_reference", "verification", "held")


def _q(x):
    if not x:
        return ""
    if x.get("value") is not None:
        return f"{x['value']:.6g}"
    if x.get("low") is not None:
        return f"{x['low']:.6g}..{x['high']:.6g}"
    return x.get("state") or ""


def ledger_csv(rows):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=LEDGER_CSV, lineterminator="\n")
    w.writeheader()
    for r in rows:
        w.writerow({"version": r["version"], "piece": r["piece"], "action": r["action"], "line_id": r["line_id"],
                    "after_line_id": r["after_line_id"], "item_code": r["item_code"], "floor": r["floor"],
                    "room_id": r["room_id"], "element_id": r["element_id"], "unit": r["unit"],
                    "v2_9": _q(r["before_released_v2_9"]), "v3_0_1": _q(r["before_v3_0_1"]),
                    "v3_0_2": _q(r["after_v3_0_2"]), "delta": (r["change"] or {}).get("delta"),
                    "pct": (r["change"] or {}).get("pct"), "evidence_status": r["evidence_status"],
                    "release_status": r["release_status"], "drawing_reference": r["drawing_reference"],
                    "verification": f"{r['verification']['task']} {r['verification']['merge_commit']}",
                    "held": "; ".join(str(h.get("why") or h.get("what")) for h in r["held"])})
    return buf.getvalue()


DIFF_CSV = ("line_id", "item_code", "floor", "room_id", "element_id", "unit", "vs_v3_0_1", "vs_released_v2_9",
            "v2_9", "v3_0_1", "v3_0_2")


def diff_rows(l301, l302, released_lines=None):
    """every V3.0.2 line against V3.0.1 (by line id) and against the released V2.9 (by item / place key), and the
    V3.0.1 lines V3.0.2 replaced (REPLACED_BY)."""
    b301 = {ln["line_id"]: ln for ln in l301}
    ids302 = {ln["line_id"] for ln in l302}
    rel = {A30._key(ln): ln for ln in released_lines or ()}
    out = []
    for ln in l302:
        o = b301.get(ln["line_id"])
        vs1 = "ADDED" if o is None else ("SAME" if A30.line_sha(o) == A30.line_sha(ln) else "CHANGED")
        r = rel.get(A30._key(ln)) if released_lines is not None else None
        vs29 = None if released_lines is None else ("NOT_IN_RELEASED" if r is None else
                                                    ("SAME_QUANTITY" if A30._qty(r) == A30._qty(ln) else
                                                     "QUANTITY_DIFFERS"))
        loc = ln["location"]
        out.append({"line_id": ln["line_id"], "item_code": ln["item_code"], "floor": loc.get("floor"),
                    "room_id": loc.get("room_id"), "element_id": loc.get("element_id"), "unit": ln["unit"],
                    "vs_v3_0_1": vs1, "vs_released_v2_9": vs29, "v2_9": _q(A30._qty(r)) if r else "",
                    "v3_0_1": _q(A30._qty(o)) if o else "", "v3_0_2": _q(A30._qty(ln))})
    for i, o in b301.items():
        if i not in ids302:
            loc = o["location"]
            out.append({"line_id": i, "item_code": o["item_code"], "floor": loc.get("floor"),
                        "room_id": loc.get("room_id"), "element_id": loc.get("element_id"), "unit": o["unit"],
                        "vs_v3_0_1": "REPLACED", "vs_released_v2_9": None, "v2_9": "", "v3_0_1": _q(A30._qty(o)),
                        "v3_0_2": ""})
    return out


def _csv(rows, cols):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=cols, lineterminator="\n")
    w.writeheader()
    w.writerows(rows)
    return buf.getvalue()


def write(out, base_lines, v30_changes, v301_changes, v302_changes, logs, inputs, released_lines=None,
          scope_summary=None):
    """the V3_0_2_* files beside the V3_0_1_* files. -> (file names, identity, ledger)."""
    from pathlib import Path
    from engine.source import boq_line as BL
    out = Path(out)
    l301, l302, ident = integrate(base_lines, v30_changes, v301_changes, v302_changes)
    rows = ledger_rows(v302_changes, l301, released_lines)
    diff = diff_rows(l301, l302, released_lines)
    dsum = {}
    for d in diff:
        dsum.setdefault("vs_v3_0_1", {}).setdefault(d["vs_v3_0_1"], 0)
        dsum["vs_v3_0_1"][d["vs_v3_0_1"]] += 1
        if d["vs_released_v2_9"] is not None:
            dsum.setdefault("vs_released_v2_9", {}).setdefault(d["vs_released_v2_9"], 0)
            dsum["vs_released_v2_9"][d["vs_released_v2_9"]] += 1
    ident = dict(ident, diff=dsum)
    cbs = columns_by_storey(l302, scope_summary)
    line_cols = sum(A30._qty(ln)["value"] or 0.0 for ln in l302 if str(ln["item_code"]).startswith("STR.CONC.COLUMN"))
    if abs(sum(v["released_m3"] for v in cbs.values()) - line_cols) > 1e-6:
        raise ValueError(f"{METHOD}: columns_by_storey does not add up to the column lines")

    totals = {"footing_steel_kg": None,
              "columns_by_storey_m3": cbs, "membrane_proof": {}, "soffits_m2": None, "blinding_m3": None}
    steel = {"lines": 0, "released": 0.0, "held_low": 0.0, "held_high": 0.0, "held_unquantified": 0}
    for ln in l302:
        if ln["item_code"] == REBAR_CODE and ln.get("physical_element") == "FOOTINGS" and \
                ln["evidence_state"] != "NOT_APPLICABLE_WITH_EVIDENCE":
            steel["lines"] += 1
            q = A30._qty(ln)
            if q["value"] is not None:
                steel["released"] += q["value"]
            elif q["low"] is not None:
                steel["held_low"] += q["low"]
                steel["held_high"] += q["high"]
            else:
                steel["held_unquantified"] += 1
    totals["footing_steel_kg"] = {k: (_r(v) if isinstance(v, float) else v) for k, v in steel.items()}
    totals["soffits_m2"] = sum(A30._qty(ln)["value"] or 0.0 for ln in l302
                               if ln.get("physical_element") == SOFFIT_ELEMENT)
    totals["soffits_m2"] = _r(totals["soffits_m2"], 4)
    bl = {"released": 0.0, "held_low": 0.0, "held_high": 0.0}
    for ln in l302:
        if ln["item_code"] == "STR.CONC.BLINDING":
            q = A30._qty(ln)
            if q["value"] is not None:
                bl["released"] += q["value"]
            elif q["low"] is not None:
                bl["held_low"] += q["low"]
                bl["held_high"] += q["high"]
    totals["blinding_m3"] = {k: _r(v) for k, v in bl.items()}
    for lg in logs:
        if lg.get("piece") == "MEMBRANE_PROOF":
            for x in lg["lines"]:
                k = x.get("verdict") or x["state"]
                totals["membrane_proof"][k] = totals["membrane_proof"].get(k, 0) + 1
    led = {"schema": LEDGER_SCHEMA, "method": METHOD, "extends": EXTENDS, "candidate": CANDIDATE,
           "base": A30.BASE_METHOD, "released": A30.RELEASED_METHOD, "released_default": False, "rows": rows,
           "waiting_pieces": WAITING, "integration_package": True}
    down = [dict(d, from_line=r["line_id"], piece=r["piece"]) for r in rows for d in r["downstream"]]
    run = {"method": METHOD, "policy": POLICY_ID, "extends": EXTENDS, "candidate": CANDIDATE,
           "base_method": A30.BASE_METHOD, "released_method": A30.RELEASED_METHOD, "released_default": False,
           "rollback": ROLLBACK, "identity": ident, "pieces": PIECES, "v3_0_1_pieces": A301.PIECES,
           "piece_logs": logs, "inputs": inputs, "totals": totals, "waiting_pieces": WAITING,
           "evidence_status_counts": _count(r["evidence_status"] for r in rows)}
    files = {"V3_0_2_BOQ_LINES.json": BL.dumps(l302),
             "V3_0_2_BOQ_LINES.csv": A30._lines_csv(l302),
             "V3_0_2_INTEGRATION_LEDGER.json": A30._j(led),
             "V3_0_2_INTEGRATION_LEDGER.csv": ledger_csv(rows),
             "V3_0_2_DIFF.csv": _csv(diff, DIFF_CSV),
             "V3_0_2_DOWNSTREAM.json": A30._j({"method": METHOD, "rows": down}),
             "V3_0_2_RUN.json": A30._j(run)}
    for name, text in files.items():
        (out / name).write_text(text, encoding="utf-8")
    return sorted(files), ident, led


def _count(it):
    c = {}
    for x in it:
        c[x] = c.get(x, 0) + 1
    return dict(sorted(c.items()))


def policy_record():
    return {"method": METHOD, "extends": EXTENDS, "pieces": sorted(PIECES), "inputs_schema": INPUTS_SCHEMA,
            "released_default": False, "rollback": ROLLBACK}


__all__ = ["METHOD", "PIECES", "WAITING", "load_inputs", "schedule_rows_from_drawing", "footing_rebar_changes",
           "membrane_proof_changes", "soffit_changes", "scope_fix_changes", "columns_by_storey", "integrate",
           "ledger_rows", "diff_rows", "write", "MembraneProofError", "InputsError"]
