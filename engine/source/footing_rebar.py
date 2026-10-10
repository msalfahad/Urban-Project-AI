"""FOOTING_REBAR (S4) - accurate footing reinforcement, occurrence by occurrence, component by component (generic).

Inputs are the controlled Urban structures, never a drawing:
  * occurrences  one physical footing each: {occurrence_id, mark, state, candidate_marks, outline, tag_handles,
                 columns, sheet_region, drawing_sha, flags}
  * definitions  one schedule row per mark: {mark, layers, L_mm, W_mm, D_mm, row_handle, sheet_region, drawing_sha,
                 components [...], boxed {...} | None, extras [...]}
                 each component: {component, count_mode, count_value, dia_mm, run_dir, dist_dir, end_treatment
                 {state, rule_id, authority, evidence}, source_handles, source_text, admission (footing_rebar_guard
                 admit_* result), authority}
  * rules        {"cover": {value_mm, rule_id, authority, evidence}, "direction": {rule_id, authority, evidence},
                 "distribution": {rule_id, authority, evidence}}
  * context      {PROJECT_ID, DRAWING_ID, DRAWING_SHA, REVISION, ENGINE_COMMIT, REGISTER_VERSION,
                 CALCULATION_ROUND, unit_mass {method ...}}

Rules (no exceptions):
  * the plan decides occurrence; each physical occurrence is computed on its own - never "count x schedule steel";
  * bar run / distribution directions come from the normalised schedule interpretation (run_dir / dist_dir),
    never from a project constant;
  * net straight length = raw span - cover at end 1 - cover at end 2; hooks, bends, anchorage and laps only when
    independently source-supported (an end treatment that is not established leaves the straight run as a
    LOWER_BOUND and names the missing end);
  * count modes are never converted silently: EXPLICIT_COUNT -> the printed count; BARS_PER_METRE /
    SPACING_RATE -> the verified lower bound ceil(rate x distribution) and the both-edges convention as BEST
    (edge behaviour not established -> LOWER_BOUND); UNKNOWN -> BLOCKED_UNQUANTIFIED;
  * a token the pre-S4 guard did not admit, a missing diameter / count / dimension -> BLOCKED_UNQUANTIFIED;
  * BOXED (or any component whose semantics are not quantifiable) is BLOCKED_UNQUANTIFIED - no kg, not even 0;
  * an occurrence in source conflict blocks its type-specific components (the candidates are recorded, never
    chosen); an occurrence held PROVISIONAL by a project authority makes its computed parts PROVISIONAL;
  * unit mass from rebar_unit_mass (kg/m = D^2 / 162 by default); mass = total net length x kg/m; no ratio;
  * every quantity part passes accurate_boq_rebar.validate_s4_part; net only - waste / procurement are a separate
    layer and are never computed here.
Stdlib + engine.source only; project-agnostic.
"""

from __future__ import annotations

import math
from collections import Counter, defaultdict

from engine.source import accurate_boq_rebar as AR
from engine.source import footing_rebar_guard as FG
from engine.source import rebar_model as RM
from engine.source import rebar_unit_mass as UM

POLICY_ID = "FOOTING_REBAR_S4_V1"
NOT_REQUIRED, NOT_APPLICABLE = "NOT_REQUIRED", "NOT_APPLICABLE"
COMPONENT_STATES = AR.STATES + (NOT_REQUIRED, NOT_APPLICABLE)

BOTTOM_SHORT, BOTTOM_LONG, TOP_SHORT, TOP_LONG = "BOTTOM_SHORT", "BOTTOM_LONG", "TOP_SHORT", "TOP_LONG"
BOXED, STARTER, EXTRA = "BOXED", "STARTER_DOWEL_REFERENCE", "OTHER_EXPLICIT_EXTRA"
MESH = (BOTTOM_SHORT, BOTTOM_LONG, TOP_SHORT, TOP_LONG)
COMPONENTS = MESH + (BOXED, STARTER, EXTRA)
ACCURATE_COMPONENT = {BOTTOM_SHORT: "FOOTING_BOTTOM_SHORT", BOTTOM_LONG: "FOOTING_BOTTOM_LONG",
                      TOP_SHORT: "FOOTING_TOP_SHORT", TOP_LONG: "FOOTING_TOP_LONG", BOXED: "BOXED_REBAR",
                      STARTER: "STARTER", EXTRA: "SPECIAL_DETAIL_BAR"}
REQUIRED_PER_OCCURRENCE = MESH + (BOXED, STARTER)       # each appears exactly once per occurrence (conservation)

EXPLICIT_COUNT, SPACING_RATE, BARS_PER_METRE, UNKNOWN = "EXPLICIT_COUNT", "SPACING_RATE", "BARS_PER_METRE", "UNKNOWN"
COUNT_MODES = (EXPLICIT_COUNT, SPACING_RATE, BARS_PER_METRE, UNKNOWN)
_RM_MODE = {EXPLICIT_COUNT: "ABSOLUTE_COUNT", SPACING_RATE: "SPACING_MM", BARS_PER_METRE: "BARS_PER_METRE",
            UNKNOWN: "UNKNOWN"}
END_STRAIGHT, END_UNKNOWN = "STRAIGHT_SOURCE_SUPPORTED", "END_TREATMENT_NOT_ESTABLISHED"

OCC_ESTABLISHED, OCC_PROVISIONAL = "ESTABLISHED", "PROVISIONAL"
OCC_SOURCE_CONFLICT, OCC_BLOCKED = "SOURCE_CONFLICT", "BLOCKED"
OCC_STATES = (OCC_ESTABLISHED, OCC_PROVISIONAL, OCC_SOURCE_CONFLICT, OCC_BLOCKED)
_GUARD_OCC = {OCC_ESTABLISHED: FG.OCC_RELEASED, OCC_PROVISIONAL: FG.OCC_PROVISIONAL,
              OCC_SOURCE_CONFLICT: FG.OCC_BLOCKED, OCC_BLOCKED: FG.OCC_BLOCKED}
_AUTH_RANK = {a: i for i, a in enumerate(("SOURCE_EXPLICIT", "APPROVED_PROJECT_CLAIM", "SOURCE_DERIVED_HIGH_CONFIDENCE",
                                          "APPROVED_ENGINEERING_METHOD", "UNAPPROVED_METHOD"))}


class FootingRebarError(ValueError):
    pass


def _weakest(*auth):
    for a in auth:
        if a not in _AUTH_RANK:
            raise FootingRebarError(f"authority {a!r} cannot stand behind a computed footing bar")
    return max(auth, key=lambda a: _AUTH_RANK[a])


def _prov(ctx, occ, d, comp, *, handles, text, rule_id, convention, measurement, authority, state, formula, inputs,
          **extra):
    pv = {"PROJECT_ID": ctx["PROJECT_ID"], "DRAWING_ID": ctx["DRAWING_ID"], "DRAWING_SHA": ctx["DRAWING_SHA"],
          "REVISION": ctx["REVISION"], "SHEET_REGION": " + ".join(x for x in (d and d.get("sheet_region"),
                                                                                occ.get("sheet_region")) if x),
          "SOURCE_HANDLES": list(handles), "SOURCE_TEXT": text, "FOOTING_OCCURRENCE_ID": occ["occurrence_id"],
          "FOOTING_MARK": occ["mark"], "COMPONENT": ACCURATE_COMPONENT[comp], "RULE_ID": rule_id,
          "CONVENTION_ID": convention, "MEASUREMENT_STATE": measurement, "AUTHORITY_STATE": authority,
          "RELEASE_STATE": state, "FORMULA": formula, "INPUTS": inputs, "ENGINE_COMMIT": ctx["ENGINE_COMMIT"],
          "REGISTER_VERSION": ctx["REGISTER_VERSION"], "CALCULATION_ROUND": ctx["CALCULATION_ROUND"]}
    pv.update(extra)
    return pv


def _record(occ, comp, state, *, kg=None, provenance=None, why=None, **fields):
    rec = {"occurrence_id": occ["occurrence_id"], "mark": occ["mark"], "component": comp,
           "accurate_component": ACCURATE_COMPONENT[comp], "state": state, "kg": kg, "why": why,
           "provenance": provenance}
    rec.update(fields)
    if state not in COMPONENT_STATES:
        raise FootingRebarError(f"{occ['occurrence_id']}/{comp}: unknown state {state}")
    return rec


def _blocked(ctx, occ, d, comp, reason, *, authority="UNRESOLVED", handles=(), text="", rule_id="S4-BLOCKED",
             question_id=None, **fields):
    hs = [h for h in handles if h] or [occ["occurrence_id"]]
    pv = _prov(ctx, occ, d, comp, handles=hs, text=text or "(none)", rule_id=rule_id, convention="NONE",
               measurement="NOT_MEASURED", authority=authority, state=AR.BLOCKED_UNQUANTIFIED,
               formula="NONE (blocked)", inputs={}, BLOCKING_REASON=reason,
               **({"QUESTION_ID": question_id} if question_id else {}))
    return _record(occ, comp, AR.BLOCKED_UNQUANTIFIED, provenance=pv, why=reason, question_id=question_id, **fields)


def _mesh_component(ctx, rules, occ, d, c, kgm_of):
    comp = c["component"]
    handles = list(c.get("source_handles") or [])
    text = c.get("source_text") or ""
    adm = c.get("admission") or {}
    if adm.get("decision") != FG.ADMITTED:
        return _blocked(ctx, occ, d, comp, f"token not admitted by the S4 guard: {adm.get('reason')}",
                        handles=handles, text=text, rule_id="S4-GUARD-FAIL-CLOSED")
    mode = c.get("count_mode")
    if mode not in COUNT_MODES:
        raise FootingRebarError(f"{comp}: count mode {mode!r} is not one of {COUNT_MODES}")
    if mode == UNKNOWN:
        return _blocked(ctx, occ, d, comp, "count mode UNKNOWN", handles=handles, text=text)
    form = adm["form"]
    dia = c.get("dia_mm")
    if not dia:
        return _blocked(ctx, occ, d, comp, "diameter missing", handles=handles, text=text)
    if c.get("count_value") in (None, 0):
        return _blocked(ctx, occ, d, comp, "count / rate missing", handles=handles, text=text)
    if dia != form["dia_mm"] or c.get("count_value") != form["count"] or \
            (mode == BARS_PER_METRE) != bool(form["per_m"]):
        raise FootingRebarError(f"{occ['occurrence_id']}/{comp}: normalised component disagrees with the admitted "
                                f"token form {form}")
    run, dist = c.get("run_dir"), c.get("dist_dir")
    if {run, dist} != {"L", "W"}:
        return _blocked(ctx, occ, d, comp, "bar run / distribution direction not established", handles=handles,
                        text=text)
    span_mm, dist_mm = d.get(f"{run}_mm"), d.get(f"{dist}_mm")
    if not span_mm or not dist_mm:
        return _blocked(ctx, occ, d, comp, f"footing dimension missing ({run}={span_mm}, {dist}={dist_mm})",
                        handles=handles, text=text)
    cov = rules["cover"]
    c1 = c2 = float(cov["value_mm"])
    net_mm = span_mm - c1 - c2
    dist_net_mm = dist_mm - c1 - c2
    if net_mm <= 0 or dist_net_mm <= 0:
        return _blocked(ctx, occ, d, comp, "footing smaller than its covers", handles=handles, text=text)
    rm = RM.bar_count(_RM_MODE[mode], c["count_value"], dist_net_mm / 1000.0,
                      basis=rules["distribution"]["rule_id"])
    n_lo, n_conv = rm["verified"], rm["convention"]
    end = c.get("end_treatment") or {"state": END_UNKNOWN}
    kgm = kgm_of(dia)
    L = net_mm / 1000.0
    total_lo = n_lo * L
    kg_lo = total_lo * kgm
    exact_count = mode == EXPLICIT_COUNT
    end_known = end["state"] == END_STRAIGHT
    missing = []
    if not exact_count:
        missing.append("EDGE_BAR_CONVENTION (count = ceil(rate x distribution); +1 edge bar not established)")
    if not end_known:
        missing.append("END_TREATMENT (straight core only; hook / bend / end leg not drawn or dimensioned)")
    auth = [c.get("authority", "SOURCE_EXPLICIT"), cov["authority"], rules["direction"]["authority"]]
    if end_known:
        auth.append(end["authority"])
    if not exact_count:
        auth.append(rules["distribution"]["authority"])
    authority = _weakest(*auth)
    state = AR.VERIFIED if not missing else AR.LOWER_BOUND
    if occ["state"] == OCC_PROVISIONAL:
        state = AR.PROVISIONAL
    formula = (f"n x (span - c1 - c2) x D^2/162 = {n_lo} x ({span_mm:g} - {c1:g} - {c2:g}) mm x {dia}^2/162 "
               f"= {n_lo} x {L:.4f} m x {kgm:.6f} kg/m = {kg_lo:.4f} kg")
    inputs = {"count_mode": mode, "count_value": c["count_value"], "dia_mm": dia, "run_dir": run, "dist_dir": dist,
              "raw_span_mm": span_mm, "cover_1_mm": c1, "cover_2_mm": c2, "net_straight_mm": net_mm,
              "distribution_mm": dist_mm, "distribution_inside_cover_mm": dist_net_mm, "count_used": n_lo,
              "count_rule": rm["rule_id"], "count_formula": rm["formula"], "kg_per_m": kgm,
              "end_treatment": end["state"], "unit_mass": ctx["unit_mass"]["method"]}
    extra = {}
    if state == AR.LOWER_BOUND or (state == AR.PROVISIONAL and missing):
        best = n_conv * L * kgm
        extra = {"LOW": kg_lo, "BEST": best, "HIGH": best if end_known else None,
                 "UNQUANTIFIED_COMPONENTS": [], "MISSING": missing}
    pv = _prov(ctx, occ, d, comp, handles=handles + [h for h in (occ.get("outline") or {}).get("handles", [])],
               text=text, rule_id=f"S4-{comp}-STRAIGHT-NET", convention="|".join(
                   [cov["rule_id"], rules["direction"]["rule_id"]] + ([end["rule_id"]] if end_known else []) +
                   ([rules["distribution"]["rule_id"]] if not exact_count else [])),
               measurement="SCHEDULE_DERIVED", authority=authority, state=state, formula=formula, inputs=inputs,
               **extra)
    return _record(occ, comp, state, kg=kg_lo, provenance=pv, why="; ".join(missing) or None, dia_mm=dia,
                   kg_per_m=kgm, count=n_lo, count_convention=n_conv, count_mode=mode, bar_length_m=L,
                   total_length_m=total_lo, raw_span_mm=span_mm, cover_1_mm=c1, cover_2_mm=c2,
                   net_straight_mm=net_mm, end_treatment=end["state"], missing=missing)


def occurrence_rebar(occ, d, rules, ctx, candidate_defs=None) -> dict:
    """All components of ONE physical footing occurrence. candidate_defs: the schedule definitions of a conflict
    occurrence's candidate marks (used only to say which components no candidate has - never to choose one)."""
    if occ.get("state") not in OCC_STATES:
        raise FootingRebarError(f"{occ.get('occurrence_id')}: occurrence state {occ.get('state')} not in {OCC_STATES}")
    for src in (occ, d):
        if src is not None and src.get("drawing_sha") != ctx["DRAWING_SHA"]:
            raise FootingRebarError(f"{occ['occurrence_id']}: input drawing sha {src.get('drawing_sha')} != run "
                                    f"drawing {ctx['DRAWING_SHA']}")
    UM.validate(ctx["unit_mass"])
    kgm_of = lambda dia: UM.kg_per_m(dia, ctx["unit_mass"])  # noqa: E731
    out = []
    starter = _record(occ, STARTER, NOT_APPLICABLE, why="column starters / dowels are owned by the column engine; "
                                                        "no footing-side steel is assigned by the source")
    if occ["state"] in (OCC_SOURCE_CONFLICT, OCC_BLOCKED) or d is None:
        cands = occ.get("candidate_marks") or []
        reason = (f"occurrence {occ['state']}: candidates {cands} - none is chosen" if cands else
                  f"occurrence {occ['state']}: {occ.get('why') or 'no schedule definition'}")
        cdefs = [c for c in (candidate_defs or []) if c is not None]
        complete = cands and len(cdefs) == len(cands)
        for comp in MESH + (BOXED,):
            has = [comp == BOXED and c.get("boxed") is not None or
                   comp != BOXED and any(x["component"] == comp for x in c["components"]) for c in cdefs]
            if complete and not any(has):
                out.append(_record(occ, comp, NOT_APPLICABLE, why=f"no candidate definition {cands} has {comp}",
                                   candidates=cands))
                continue
            out.append(_blocked(ctx, occ, d, comp, reason, authority="SOURCE_CONFLICT" if cands else "UNRESOLVED",
                                handles=occ.get("tag_handles", []) + (occ.get("outline") or {}).get("handles", []),
                                text=occ["mark"], rule_id="S4-OCCURRENCE-BLOCKED", candidates=cands))
        out.append(starter)
        return _finish(occ, out)
    present = {c["component"] for c in d["components"]}
    for comp in MESH:
        if comp in present:
            out.append(_mesh_component(ctx, rules, occ, d, next(c for c in d["components"] if c["component"] == comp),
                                       kgm_of))
        else:
            out.append(_record(occ, comp, NOT_APPLICABLE,
                               why=f"{d['layers']} footing: the schedule row has no {comp} field"))
    bx = d.get("boxed")
    if bx is None:
        out.append(_record(occ, BOXED, NOT_APPLICABLE, why="the schedule carries no BOXED value for this footing "
                                                           "type (two-layer row: the column holds layer labels)"))
    else:
        if FG.may_quantify(bx["semantics_class"]):
            raise FootingRebarError(f"{occ['occurrence_id']}: BOXED semantics {bx['semantics_class']} are "
                                    "quantifiable - S4 V1 computes no BOXED steel; add the source rule first")
        out.append(_blocked(ctx, occ, d, BOXED, bx["reason"], handles=bx.get("source_handles", []),
                            text=bx.get("raw_value") or "(empty cell)", rule_id="S4-BOXED-UNRESOLVED",
                            question_id=bx.get("question_id"), raw_value=bx.get("raw_value"),
                            detail_reference=bx.get("detail_reference"), semantics_class=bx["semantics_class"]))
    out.append(starter)
    for x in d.get("extras", []):
        out.append(_blocked(ctx, occ, d, EXTRA, x["reason"], handles=x.get("source_handles", []),
                            text=x.get("source_text", ""), rule_id="S4-EXTRA-UNRESOLVED",
                            question_id=x.get("question_id")))
    return _finish(occ, out)


def _finish(occ, comps):
    parts = []
    for c in comps:
        if c["state"] in AR.STATES:
            p = {"part_id": f"{c['occurrence_id']}:{c['component']}", "category": "FOUNDATIONS",
                 "component": c["accurate_component"], "state": c["state"], "kg": c["kg"],
                 "basis": ["DRAWING_OCCURRENCE", "SCHEDULE", "STRUCTURAL_DETAIL"], "provenance": c["provenance"]}
            AR.validate_s4_part(p)
            parts.append(p)
    rel = FG.footing_release(parts, occurrence_state=_GUARD_OCC[occ["state"]])
    unq = sorted({c["accurate_component"] for c in comps if c["state"] == AR.BLOCKED_UNQUANTIFIED})
    for p in parts:                                   # a lower-bound part names what the occurrence still lacks
        pv = p["provenance"]
        if "UNQUANTIFIED_COMPONENTS" in pv:
            pv["UNQUANTIFIED_COMPONENTS"] = unq
            AR.validate_s4_part(p)
    known = [c for c in comps if c["state"] in (AR.VERIFIED, AR.LOWER_BOUND, AR.PROVISIONAL)]
    row = {"occurrence_id": occ["occurrence_id"], "mark": occ["mark"], "occurrence_state": occ["state"],
           "release_state": rel["release_state"], "known_kg": sum(c["kg"] for c in known),
           "known_length_m": sum(c["total_length_m"] for c in known),
           "released_kg": rel["released_kg"], "unquantified_components": unq,
           "components_by_state": dict(sorted(Counter(c["state"] for c in comps).items())),
           "candidate_marks": occ.get("candidate_marks") or [], "flags": list(occ.get("flags") or [])}
    return {"occurrence": row, "components": comps, "parts": parts}


def bbs_lines(components) -> list:
    """Net BBS: one line per computed straight component. Count = the verified (lower-bound) count. Procurement
    columns are not computed here."""
    out = []
    for c in components:
        if c["state"] not in (AR.VERIFIED, AR.LOWER_BOUND, AR.PROVISIONAL):
            continue
        out.append({"bbs_id": f"{c['occurrence_id']}:{c['component']}", "occurrence_id": c["occurrence_id"],
                    "mark": c["mark"], "component": c["component"], "state": c["state"], "dia_mm": c["dia_mm"],
                    "shape": "STRAIGHT", "bar_length_m": c["bar_length_m"], "count": c["count"],
                    "count_basis": c["count_mode"], "total_length_m": c["total_length_m"], "kg_per_m": c["kg_per_m"],
                    "net_bbs_kg": c["kg"], "used_kg": None, "purchased_kg": None, "waste_kg": None,
                    "procurement": "NOT_COMPUTED (procurement layer not invoked)"})
    return out


def run(occurrences, definitions, rules, ctx) -> dict:
    defs = {d["mark"]: d for d in definitions}
    ids = Counter(o["occurrence_id"] for o in occurrences)
    dup = [k for k, n in ids.items() if n > 1]
    if dup:
        raise FootingRebarError(f"occurrence id entered twice: {dup}")
    res = [occurrence_rebar(o, defs.get(o["mark"]) if o["state"] != OCC_SOURCE_CONFLICT else None, rules, ctx,
                            candidate_defs=[defs.get(m) for m in o.get("candidate_marks") or []])
           for o in sorted(occurrences, key=lambda z: z["occurrence_id"])]
    comps = [c for r in res for c in r["components"]]
    parts = [p for r in res for p in r["parts"]]
    occ_rows = [r["occurrence"] for r in res]
    bbs = bbs_lines(comps)
    summ = AR.summarise_s4(parts)
    by = defaultdict(float)
    for c in comps:
        if c["kg"] is not None:
            by[c["state"]] += c["kg"]
    blocked_unq = sum(1 for c in comps if c["state"] == AR.BLOCKED_UNQUANTIFIED)
    final = blocked_unq == 0 and not by.get(AR.LOWER_BOUND) and not by.get(AR.PROVISIONAL) and \
        not by.get(AR.BLOCKED_MODELLED)
    summary = {
        "policy": POLICY_ID, "headline": "KNOWN SOURCE-DERIVED FOOTING REBAR",
        "final_footing_rebar": "FINAL_FOOTING_REBAR_ESTABLISHED" if final else "FINAL FOOTING REBAR NOT ESTABLISHED",
        "verified_kg": by.get(AR.VERIFIED, 0.0), "lower_bound_known_kg": by.get(AR.LOWER_BOUND, 0.0),
        "provisional_kg": by.get(AR.PROVISIONAL, 0.0), "blocked_modelled_kg": by.get(AR.BLOCKED_MODELLED, 0.0),
        "blocked_unquantified_component_count": blocked_unq,
        "occurrences": len(occ_rows),
        "occurrences_by_release": dict(sorted(Counter(r["release_state"] for r in occ_rows).items())),
        "components_by_state": dict(sorted(Counter(c["state"] for c in comps).items())),
        "accurate_summary": summ,
        "stamp": {k: ctx[k] for k in ("ENGINE_COMMIT", "REGISTER_VERSION", "DRAWING_SHA", "CALCULATION_ROUND")}}
    return {"occurrences": occ_rows, "components": comps, "parts": parts, "bbs": bbs, "summary": summary,
            "conservation": conservation(occ_rows, comps, parts, bbs, summ)}


def conservation(occ_rows, comps, parts, bbs, summ, tol=1e-9) -> dict:
    """Independent checks; every one must be True."""
    by_occ = defaultdict(list)
    for c in comps:
        by_occ[c["occurrence_id"]].append(c)
    known_states = (AR.VERIFIED, AR.LOWER_BOUND, AR.PROVISIONAL)
    occ_len = all(abs(sum(c["total_length_m"] for c in by_occ[r["occurrence_id"]] if c["state"] in known_states)
                      - r["known_length_m"]) <= tol for r in occ_rows)
    occ_kg = all(abs(sum(c["kg"] for c in by_occ[r["occurrence_id"]] if c["state"] in known_states)
                     - r["known_kg"]) <= tol for r in occ_rows)
    proj_kg = sum(r["known_kg"] for r in occ_rows)
    part_kg = sum(p["kg"] for p in parts if p["kg"] is not None and p["state"] in known_states)
    bbs_kg = sum(b["net_bbs_kg"] for b in bbs)
    each_once = all(Counter(c["component"] for c in by_occ[r["occurrence_id"]])[k] == 1
                    for r in occ_rows for k in REQUIRED_PER_OCCURRENCE)
    pop = Counter(c["state"] for c in comps)
    blocked_kept = all(c["kg"] is None for c in comps if c["state"] in (AR.BLOCKED_UNQUANTIFIED, NOT_REQUIRED,
                                                                      NOT_APPLICABLE))
    cats = summ["categories"].get("FOUNDATIONS", {})
    summ_ok = abs(cats.get("verified_kg", 0) + cats.get("lower_bound_kg", 0) + cats.get("provisional_kg", 0)
                  - proj_kg) <= 1e-6 and cats.get("blocked_unquantified_parts", 0) == pop[AR.BLOCKED_UNQUANTIFIED]
    checks = {"component_length_equals_occurrence_known_length": occ_len,
              "component_kg_equals_occurrence_known_kg": occ_kg,
              "occurrence_kg_equals_project_known_kg": abs(proj_kg - part_kg) <= 1e-6,
              "bbs_net_kg_equals_known_parts_kg": abs(bbs_kg - part_kg) <= 1e-6,
              "every_required_component_once_per_occurrence": each_once,
              "population_reconciles": sum(pop.values()) == len(comps) and
              len(comps) == sum(len(v) for v in by_occ.values()),
              "blocked_components_carry_no_kg": blocked_kept,
              "accurate_summary_reconciles": summ_ok}
    return {"checks": checks, "all_pass": all(checks.values()), "project_known_kg": proj_kg,
            "population_by_state": dict(sorted(pop.items())),
            "population_by_component_state": {k: dict(sorted(Counter(c["state"] for c in comps
                                                                     if c["component"] == k).items()))
                                              for k in COMPONENTS}}


def policy_record() -> dict:
    return {"policy_id": POLICY_ID, "components": list(COMPONENTS), "component_states": list(COMPONENT_STATES),
            "count_modes": list(COUNT_MODES), "occurrence_states": list(OCC_STATES),
            "rules": ["occurrence first; never count x schedule steel",
                      "net straight length = span - cover - cover; ends only when source-supported",
                      "rate counts: verified lower bound ceil(rate x distribution inside cover); +1 edge bar is BEST",
                      "BOXED is BLOCKED_UNQUANTIFIED until its semantics are quantifiable",
                      "a source-conflict occurrence blocks its type-specific components; candidates are not chosen",
                      "kg/m from rebar_unit_mass; never a ratio", "net only; waste / procurement not computed"]}
