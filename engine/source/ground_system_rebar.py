"""GROUND_SYSTEM_REBAR (S5) - accurate ground-beam and strap-beam reinforcement, occurrence by occurrence, component
by component (generic; stdlib + engine.source only).

Inputs are controlled registers, never a drawing:
  * occurrences  one physical member each (a ground-beam span or a strap):
                 {occurrence_id, family (GROUND_BEAM | STRAP_BEAM), mark, drawing_sha, sheet_region,
                  start_node {kind, refs}, end_node {kind, refs}, geometry_handles [...],
                  lengths {centreline_m, clear_concrete_m, face_to_face_m, bar_run_lb_m (None = unresolved),
                           length_state, bar_run_state, issues [...], stirrup_distribution_m (None = not established),
                           stirrup_distribution_basis},
                  width {state, value_mm, candidates}, depth {state, value_mm, bound_max_m, candidates, why},
                  detail_ids [...], applicability (ground_system_provenance.DETAIL_APPLICABILITY_STATES),
                  why_candidate, why_not_resolved, node_issues {"1": reason | None, "2": reason | None},
                  questions {topic: question_id}, flags [...]}
  * definitions  {detail_id: {detail_id, source_handles, source_text, sheet_region, authority,
                  longitudinal {TOP_MAIN: [n, dia] | None, BOTTOM_ROW_1: ..., BOTTOM_ROW_2: ...},
                  side: text | None, stirrup {dia_mm, mode (SPACING_MM | BARS_PER_METRE), value} | None,
                  end_zone: text | None, extras [...], section {B_mm, D_mm, D_state}}}
                 A detail id that an occurrence names but `definitions` does not define (e.g. "no project detail
                 for the concentrated-load case") is an UNDEFINED candidate: its content is unknown, so no
                 component can be candidate-invariant across it.
  * rules        {development {state, why}, bar_end_hooks {state, why}, stirrup_hooks {state, why},
                  stirrup_topology {state, why}, cover {value_mm, rule_id, authority}}
  * context      {PROJECT_ID, DRAWING_ID, DRAWING_SHA, REVISION, ENGINE_COMMIT, REGISTER_VERSION,
                  CALCULATION_ROUND, unit_mass {method ...}}

Rules (no exceptions):
  * one record per physical occurrence; the member identity is generic (ELEMENT_*), never FOOTING_*;
  * the detail applicability is taken as given - this engine never chooses between candidate details. A component
    releases under CANDIDATE_DETAIL only when every candidate defines it identically (CANDIDATE_INVARIANT); any
    difference, or an undefined candidate, leaves it BLOCKED_UNQUANTIFIED;
  * longitudinal steel: kg = bar count x BAR_STRAIGHT_RUN_LOWER_BOUND x kg/m. No min(clear, centreline), no
    member length, no development folded in. Known straight steel with unresolved ends is a LOWER_BOUND;
  * the two lower rows of a ground beam are separate components; they are never collapsed;
  * development / anchorage, bar-end hooks and stirrup hooks are BLOCKED_UNQUANTIFIED unless the rules carry a
    source-established method (V1 accepts none: no code, starter-note or practice default is ever generalised);
  * stirrups: diameter and spacing are attribute records, the count is a COUNT record (lower bound
    ceil(rate x distribution); the +1 end bar is not adopted), and the stirrup MASS (core path) is released only
    when width, depth, cover, legs / topology and hooks are all source-supported - V1 never has all of them;
  * side bars that depend on an unestablished depth are BLOCKED_UNQUANTIFIED; a detail that prints none is
    NOT_APPLICABLE for that occurrence (a <2.5 m section prints no stirrup: nothing is inherited);
  * blocked components stay listed and carry no kg (not even 0); kg/m from rebar_unit_mass (D^2/162); net only.
"""

from __future__ import annotations

from collections import Counter, defaultdict

from engine.source import accurate_boq_rebar as AR
from engine.source import ground_system_provenance as GP
from engine.source import rebar_model as RM
from engine.source import rebar_provenance as RP
from engine.source import rebar_unit_mass as UM

POLICY_ID = "GROUND_SYSTEM_REBAR_S5_V1"
NOT_REQUIRED, NOT_APPLICABLE = "NOT_REQUIRED", "NOT_APPLICABLE"
COMPONENT_STATES = AR.STATES + (NOT_REQUIRED, NOT_APPLICABLE)
GROUND_BEAM, STRAP_BEAM = "GROUND_BEAM", "STRAP_BEAM"
FAMILIES = (GROUND_BEAM, STRAP_BEAM)

# quantity kinds: MASS components are accurate parts (kg); COUNT / ATTRIBUTE records never carry kg
MASS, COUNT, ATTRIBUTE = "MASS", "COUNT", "ATTRIBUTE"

LONGITUDINAL = {GROUND_BEAM: ("TOP_MAIN", "BOTTOM_ROW_1", "BOTTOM_ROW_2"), STRAP_BEAM: ("TOP_MAIN", "BOTTOM_MAIN")}
# the detail field each longitudinal component reads (a strap schedule gives one BOTTOM total)
_DETAIL_FIELD = {"TOP_MAIN": "TOP_MAIN", "BOTTOM_ROW_1": "BOTTOM_ROW_1", "BOTTOM_ROW_2": "BOTTOM_ROW_2",
                 "BOTTOM_MAIN": "BOTTOM_ROW_1"}
STIRRUP = ("STIRRUP_DIAMETER", "STIRRUP_SPACING", "STIRRUP_COUNT", "STIRRUP_CORE_PATH", "STIRRUP_HOOK_1",
           "STIRRUP_HOOK_2", "STIRRUP_END_ZONE_EXTRA")
ENDS = {GROUND_BEAM: ("HOOK_1", "HOOK_2", "DEVELOPMENT_SUPPORT_1", "DEVELOPMENT_SUPPORT_2"),
        STRAP_BEAM: ("HOOK_1", "HOOK_2", "DEVELOPMENT_FOOTING_1", "DEVELOPMENT_FOOTING_2")}
EXTRAS = {GROUND_BEAM: ("EXTRA_SUPPORT", "MID", "OTHER_EXPLICIT_EXTRA"), STRAP_BEAM: ("OTHER_EXPLICIT_EXTRA",)}
COMPONENTS = {f: LONGITUDINAL[f] + (("SIDE_REBAR",) if f == GROUND_BEAM else ()) + STIRRUP + ENDS[f] + EXTRAS[f]
              for f in FAMILIES}
REQUIRED_PER_OCCURRENCE = COMPONENTS        # every component of the family terminates exactly once per occurrence

ACCURATE_COMPONENT = {
    GROUND_BEAM: {"TOP_MAIN": "BEAM_TOP_BAR", "BOTTOM_ROW_1": "BEAM_BOTTOM_BAR", "BOTTOM_ROW_2": "BEAM_BOTTOM_BAR",
                  "SIDE_REBAR": "BEAM_SIDE_BAR", "STIRRUP_DIAMETER": "BEAM_STIRRUP",
                  "STIRRUP_SPACING": "BEAM_STIRRUP", "STIRRUP_COUNT": "BEAM_STIRRUP",
                  "STIRRUP_CORE_PATH": "BEAM_STIRRUP", "STIRRUP_HOOK_1": "BEAM_STIRRUP",
                  "STIRRUP_HOOK_2": "BEAM_STIRRUP", "STIRRUP_END_ZONE_EXTRA": "BEAM_STIRRUP",
                  "HOOK_1": "ANCHORAGE", "HOOK_2": "ANCHORAGE", "DEVELOPMENT_SUPPORT_1": "ANCHORAGE",
                  "DEVELOPMENT_SUPPORT_2": "ANCHORAGE", "EXTRA_SUPPORT": "BEAM_EXTRA_BAR", "MID": "BEAM_EXTRA_BAR",
                  "OTHER_EXPLICIT_EXTRA": "SPECIAL_DETAIL_BAR"},
    STRAP_BEAM: {"TOP_MAIN": "STRAP_BEAM_BAR", "BOTTOM_MAIN": "STRAP_BEAM_BAR",
                 "STIRRUP_DIAMETER": "STRAP_BEAM_STIRRUP", "STIRRUP_SPACING": "STRAP_BEAM_STIRRUP",
                 "STIRRUP_COUNT": "STRAP_BEAM_STIRRUP", "STIRRUP_CORE_PATH": "STRAP_BEAM_STIRRUP",
                 "STIRRUP_HOOK_1": "STRAP_BEAM_STIRRUP", "STIRRUP_HOOK_2": "STRAP_BEAM_STIRRUP",
                 "STIRRUP_END_ZONE_EXTRA": "STRAP_BEAM_STIRRUP", "HOOK_1": "ANCHORAGE", "HOOK_2": "ANCHORAGE",
                 "DEVELOPMENT_FOOTING_1": "ANCHORAGE", "DEVELOPMENT_FOOTING_2": "ANCHORAGE",
                 "OTHER_EXPLICIT_EXTRA": "SPECIAL_DETAIL_BAR"}}
KIND = {c: (COUNT if c == "STIRRUP_COUNT" else ATTRIBUTE if c in ("STIRRUP_DIAMETER", "STIRRUP_SPACING") else MASS)
        for f in FAMILIES for c in COMPONENTS[f]}

NOT_ESTABLISHED = "NOT_ESTABLISHED"
# depth states an occurrence may carry (the depth never comes from a level bound or a candidate pick)
DEPTH_STATES = ("SOURCE_EXPLICIT", "CANDIDATE_INVARIANT", "BOUNDED_ABOVE", "UNRESOLVED", "SOURCE_CONFLICT",
                "CANDIDATE_CONFLICT", "AI_TRANSCRIPTION_ONLY")
DEPTH_KNOWN = ("SOURCE_EXPLICIT", "CANDIDATE_INVARIANT")
OCC_VERIFIED, OCC_LOWER_BOUND, OCC_PROVISIONAL, OCC_BLOCKED = "VERIFIED", "LOWER_BOUND", "PROVISIONAL", "BLOCKED"
_BLOCKING_APPLICABILITY = ("SOURCE_CONFLICT", "NO_APPLICABLE_DETAIL")
RECORD_FIELDS = RP.BASE_FIELDS + GP.S5_EXTRA_FIELDS + ("S5_COMPONENT", "QUANTITY_KIND")


class GroundSystemRebarError(ValueError):
    pass


# ------------------------------------------------------------------------------------------------- record contract
def validate_record(rec: dict) -> dict:
    """The generic contract for EVERY S5 component row (mass, count, attribute, blocked, not-applicable). Mass parts
    additionally pass ground_system_provenance.validate_s5_part (accurate part + generic provenance + S5 fields).
    Raises GroundSystemRebarError naming the first defect."""
    pid = f"{rec.get('occurrence_id')}:{rec.get('component')}"
    pv = rec.get("provenance")
    if not isinstance(pv, dict):
        raise GroundSystemRebarError(f"{pid}: every S5 component carries a provenance record")
    try:
        ident = RP.element_identity(pv)
    except RP.ProvenanceError as e:
        raise GroundSystemRebarError(f"{pid}: {e}") from None
    if ident["ELEMENT_FAMILY"] not in FAMILIES or ident["ELEMENT_OCCURRENCE_ID"] != rec["occurrence_id"]:
        raise GroundSystemRebarError(f"{pid}: provenance identity {ident} does not name this occurrence")
    missing = [f for f in RECORD_FIELDS if f not in pv or pv[f] is None or (pv[f] in ("", [], ()) and f != "INPUTS")]
    if missing:
        raise GroundSystemRebarError(f"{pid}: provenance missing {missing}")
    if pv["S5_COMPONENT"] != rec["component"] or pv["QUANTITY_KIND"] != rec["quantity_kind"]:
        raise GroundSystemRebarError(f"{pid}: provenance component / kind disagree with the row")
    if pv["RELEASE_STATE"] != rec["state"] or rec["state"] not in COMPONENT_STATES:
        raise GroundSystemRebarError(f"{pid}: RELEASE_STATE {pv['RELEASE_STATE']} != row state {rec['state']}")
    if pv["AUTHORITY_STATE"] not in AR.AUTHORITY_STATES or pv["MEASUREMENT_STATE"] not in AR.MEASUREMENT_STATES:
        raise GroundSystemRebarError(f"{pid}: unknown authority / measurement state")
    if pv["AUTHORITY_STATE"] in AR.NON_QUANTIFYING_AUTHORITIES and rec["state"] in AR.RELEASED_STATES:
        raise GroundSystemRebarError(f"{pid}: authority {pv['AUTHORITY_STATE']} cannot release {rec['state']}")
    if rec["state"] == AR.BLOCKED_UNQUANTIFIED and not pv.get("BLOCKING_REASON"):
        raise GroundSystemRebarError(f"{pid}: a blocked component names its BLOCKING_REASON")
    if pv["DETAIL_APPLICABILITY_STATE"] not in GP.DETAIL_APPLICABILITY_STATES:
        raise GroundSystemRebarError(f"{pid}: unknown DETAIL_APPLICABILITY_STATE")
    for k in ("START_NODE", "END_NODE"):
        if not isinstance(pv[k], dict) or pv[k].get("kind") not in GP.NODE_KINDS:
            raise GroundSystemRebarError(f"{pid}: {k} must name a node kind in {GP.NODE_KINDS}")
    released = rec["state"] in AR.RELEASED_STATES
    if released and not GP.may_release(pv["DETAIL_APPLICABILITY_STATE"],
                                       candidate_invariant=pv.get("CANDIDATE_INVARIANT") is True):
        raise GroundSystemRebarError(f"{pid}: applicability {pv['DETAIL_APPLICABILITY_STATE']} cannot release")
    if rec["quantity_kind"] == MASS:
        if (rec["kg"] is None) != (rec["state"] in (AR.BLOCKED_UNQUANTIFIED, NOT_REQUIRED, NOT_APPLICABLE)):
            raise GroundSystemRebarError(f"{pid}: a mass component carries kg iff it is quantified")
    elif rec["kg"] is not None:
        raise GroundSystemRebarError(f"{pid}: a {rec['quantity_kind']} record never carries kg")
    if rec["quantity_kind"] == COUNT and released:
        lo, best, hi = pv.get("LOW"), pv.get("BEST"), pv.get("HIGH")
        if not (isinstance(rec.get("count"), int) and lo == rec["count"] and best is not None and lo <= best and
                (hi is None or best <= hi)):
            raise GroundSystemRebarError(f"{pid}: a released count states LOW = count <= BEST (<= HIGH)")
    return rec


# ------------------------------------------------------------------------------------------------------- helpers
def _bar(v):
    return None if v is None else (int(v[0]), int(v[1]))


def _txt(v):
    if v is None:
        return "none"
    if isinstance(v, tuple) and len(v) == 3:                     # stirrup (dia, mode, value)
        return f"Ø{v[0]}/{v[2]:g} mm" if v[1] == "SPACING_MM" else f"{v[2]:g}Ø{v[0]}/m"
    return f"{v[0]}Ø{v[1]}" if isinstance(v, tuple) else str(v)


def _candidates(occ, defs):
    ids = list(occ["detail_ids"])
    return ids, [d for d in ids if d not in defs]


def _prov(ctx, occ, defs, comp, *, state, rule_id, convention, measurement, authority, formula, inputs, handles=(),
          text=None, **extra):
    fam = occ["family"]
    ids, _ = _candidates(occ, defs)
    dh = [h for d in ids if d in defs for h in defs[d].get("source_handles", [])]
    hs = list(dict.fromkeys([h for h in list(handles) + dh + list(occ["geometry_handles"]) if h]))
    srcs = [defs[d].get("source_text") for d in ids if d in defs]
    pv = {"PROJECT_ID": ctx["PROJECT_ID"], "DRAWING_ID": ctx["DRAWING_ID"], "DRAWING_SHA": ctx["DRAWING_SHA"],
          "REVISION": ctx["REVISION"],
          "SHEET_REGION": " + ".join(dict.fromkeys(x for x in [occ.get("sheet_region")] +
                                                   [defs[d].get("sheet_region") for d in ids if d in defs] if x)),
          "SOURCE_HANDLES": hs, "SOURCE_TEXT": text or " || ".join(s for s in srcs if s) or occ["mark"],
          "COMPONENT": ACCURATE_COMPONENT[fam][comp], "S5_COMPONENT": comp, "QUANTITY_KIND": KIND[comp],
          "RULE_ID": rule_id, "CONVENTION_ID": convention, "MEASUREMENT_STATE": measurement,
          "AUTHORITY_STATE": authority, "RELEASE_STATE": state, "FORMULA": formula, "INPUTS": inputs,
          "ENGINE_COMMIT": ctx["ENGINE_COMMIT"], "REGISTER_VERSION": ctx["REGISTER_VERSION"],
          "CALCULATION_ROUND": ctx["CALCULATION_ROUND"],
          "START_NODE": occ["start_node"], "END_NODE": occ["end_node"],
          "GEOMETRY_HANDLES": list(occ["geometry_handles"]), "DETAIL_ID": ids or ["NONE"],
          "DETAIL_APPLICABILITY_STATE": occ["applicability"], "DETAIL_CANDIDATES": ids,
          "WHY_CANDIDATE": occ.get("why_candidate") or "", "WHY_NOT_RESOLVED": occ.get("why_not_resolved") or "",
          "OCCURRENCE_FLAGS": list(occ.get("flags") or [])}
    pv.update(RP.identity_fields(family=fam, occurrence_id=occ["occurrence_id"], mark=occ["mark"]))
    pv.update(extra)
    return pv


def _row(occ, comp, state, *, kg=None, provenance=None, why=None, question_id=None, **fields):
    fam = occ["family"]
    if state not in COMPONENT_STATES:
        raise GroundSystemRebarError(f"{occ['occurrence_id']}/{comp}: unknown state {state}")
    rec = {"occurrence_id": occ["occurrence_id"], "family": fam, "mark": occ["mark"], "component": comp,
           "accurate_component": ACCURATE_COMPONENT[fam][comp], "quantity_kind": KIND[comp], "state": state,
           "kg": kg, "why": why, "question_id": question_id, "provenance": provenance}
    rec.update(fields)
    return rec


def _blocked(ctx, occ, defs, comp, reason, *, authority="UNRESOLVED", question_id=None, rule_id="S5-BLOCKED",
             **fields):
    pv = _prov(ctx, occ, defs, comp, state=AR.BLOCKED_UNQUANTIFIED, rule_id=rule_id, convention="NONE",
               measurement="NOT_MEASURED", authority=authority, formula="NONE (blocked)", inputs={},
               BLOCKING_REASON=reason, **({"QUESTION_ID": question_id} if question_id else {}))
    return _row(occ, comp, AR.BLOCKED_UNQUANTIFIED, provenance=pv, why=reason, question_id=question_id, **fields)


def _not_applicable(ctx, occ, defs, comp, reason, *, rule_id="S5-NOT-APPLICABLE"):
    pv = _prov(ctx, occ, defs, comp, state=NOT_APPLICABLE, rule_id=rule_id, convention="NONE",
               measurement="NOT_MEASURED", authority="SOURCE_EXPLICIT", formula="NONE (not applicable)",
               inputs={}, NOT_APPLICABLE_REASON=reason)
    return _row(occ, comp, NOT_APPLICABLE, provenance=pv, why=reason)


def _q(occ, topic):
    return (occ.get("questions") or {}).get(topic)


def _occurrence_block(occ, defs):
    """A reason every type-specific component shares (detail conflict / no detail), else None."""
    app = occ["applicability"]
    if app in _BLOCKING_APPLICABILITY:
        return (f"detail applicability {app}: candidates {occ['detail_ids']} - none is chosen "
                f"({occ.get('why_not_resolved') or occ.get('why_candidate') or 'no applicable detail'})"), \
            ("SOURCE_CONFLICT" if app == "SOURCE_CONFLICT" else "UNRESOLVED")
    if app not in GP.DETAIL_APPLICABILITY_STATES:
        raise GroundSystemRebarError(f"{occ['occurrence_id']}: unknown applicability {app}")
    return None, None


def _invariant(occ, defs, getter, label):
    """(state, value, invariant, reason). state: SAME | NONE | DIFFERENT | UNDEFINED."""
    ids, undefined = _candidates(occ, defs)
    if not ids:
        return "UNDEFINED", None, False, "no detail is applicable"
    if undefined:
        return "UNDEFINED", None, False, (f"candidate {undefined} has no project definition: its {label} is unknown, "
                                          "so no value can be candidate-invariant")
    vals = {d: getter(defs[d]) for d in ids}
    distinct = set(vals.values())
    if len(distinct) > 1:
        return "DIFFERENT", None, False, "candidate details disagree: " + "; ".join(
            f"{d} {_txt(v)}" for d, v in sorted(vals.items()))
    v = distinct.pop()
    if v is None:
        return "NONE", None, False, f"no applicable detail ({', '.join(ids)}) prints {label}"
    return "SAME", v, len(ids) > 1, None


def _authority(occ, defs, field="longitudinal"):
    auths = [defs[d]["authority"].get(field, "UNRESOLVED") for d in occ["detail_ids"] if d in defs]
    for a in auths:
        if a not in AR.RELEASING_AUTHORITIES:
            return a
    return "SOURCE_DERIVED_HIGH_CONFIDENCE"     # explicit detail values x a deterministic geometry measurement


# ------------------------------------------------------------------------------------------------------ components
def _longitudinal(ctx, occ, defs, comp, kgm_of, occ_block):
    if occ_block[0]:
        return _blocked(ctx, occ, defs, comp, occ_block[0], authority=occ_block[1],
                        question_id=_q(occ, "applicability"), rule_id="S5-OCCURRENCE-BLOCKED")
    field = _DETAIL_FIELD[comp]
    st, val, inv, why = _invariant(occ, defs, lambda d: _bar((d.get("longitudinal") or {}).get(field)),
                                   f"{field} bars")
    if st == "NONE":
        return _not_applicable(ctx, occ, defs, comp, why)
    if st != "SAME":
        return _blocked(ctx, occ, defs, comp, why, authority="SOURCE_CONFLICT" if st == "DIFFERENT" else "UNRESOLVED",
                        question_id=_q(occ, "applicability"), rule_id="S5-CANDIDATE-NOT-INVARIANT",
                        candidate_values={d: _txt(_bar((defs[d].get("longitudinal") or {}).get(field)))
                                          for d in occ["detail_ids"] if d in defs})
    L = occ["lengths"]
    run = L.get("bar_run_lb_m")
    if run is None or run <= 0:
        return _blocked(ctx, occ, defs, comp, f"bar straight run not established ({L.get('bar_run_state')}: "
                        f"{'; '.join(L.get('issues') or []) or 'no lower bound'})", question_id=_q(occ, "bar_run"),
                        rule_id="S5-BAR-RUN-UNRESOLVED")
    authority = _authority(occ, defs)
    if authority not in AR.RELEASING_AUTHORITIES:
        return _blocked(ctx, occ, defs, comp, f"detail authority {authority} cannot release longitudinal steel",
                        authority=authority if authority in AR.NON_QUANTIFYING_AUTHORITIES else "UNRESOLVED")
    n, dia = val
    kgm = kgm_of(dia)
    total = n * run
    kg = total * kgm
    missing = ["DEVELOPMENT / ANCHORAGE at both ends (not source-established)",
               "BAR-END HOOK / BEND at both ends (not detailed)"]
    inputs = {"bar_count": n, "dia_mm": dia, "straight_run_m": run, "straight_run_basis": "BAR_STRAIGHT_RUN_LOWER_BOUND",
              "total_straight_length_m": total, "kg_per_m": kgm, "unit_mass": ctx["unit_mass"]["method"],
              "candidate_invariant": inv, "detail_field": field,
              "not_used": "member centreline / clear concrete length / min(clear, centreline)"}
    formula = (f"n x BAR_STRAIGHT_RUN_LOWER_BOUND x D^2/162 = {n} x {run:.4f} m x {dia}^2/162 "
               f"= {total:.4f} m x {kgm:.6f} kg/m = {kg:.4f} kg")
    pv = _prov(ctx, occ, defs, comp, state=AR.LOWER_BOUND, rule_id=f"S5-{comp}-STRAIGHT-RUN-LB",
               convention="BAR_STRAIGHT_RUN_LOWER_BOUND|" + ctx["unit_mass"]["method"], measurement="MEASURED",
               authority=authority, formula=formula, inputs=inputs, CANDIDATE_INVARIANT=inv,
               LOW=kg, BEST=kg, HIGH=None, UNQUANTIFIED_COMPONENTS=[], MISSING=missing,
               KNOWN_STRAIGHT_RUN_M=run)
    return _row(occ, comp, AR.LOWER_BOUND, kg=kg, provenance=pv, why="; ".join(missing), dia_mm=dia, bar_count=n,
                straight_run_m=run, total_length_m=total, kg_per_m=kgm, candidate_invariant=inv, missing=missing)


def _side(ctx, occ, defs, occ_block):
    comp = "SIDE_REBAR"
    if occ_block[0]:
        return _blocked(ctx, occ, defs, comp, occ_block[0], authority=occ_block[1],
                        question_id=_q(occ, "applicability"), rule_id="S5-OCCURRENCE-BLOCKED")
    st, val, inv, why = _invariant(occ, defs, lambda d: d.get("side"), "side bars")
    if st == "NONE":
        return _not_applicable(ctx, occ, defs, comp, why)
    if st != "SAME":
        return _blocked(ctx, occ, defs, comp, why, authority="SOURCE_CONFLICT" if st == "DIFFERENT" else "UNRESOLVED",
                        question_id=_q(occ, "applicability"), rule_id="S5-CANDIDATE-NOT-INVARIANT")
    dp = occ["depth"]
    reason = (f"side bars '{val}' are specified per depth; depth {dp['state']}"
              f"{' (D <= %.2f m, no lower bound)' % dp['bound_max_m'] if dp.get('bound_max_m') else ''} - "
              "the side-bar count is not source-quantified")
    if dp["state"] in DEPTH_KNOWN:
        reason = (f"side bars '{val}': the per-depth distribution (first / last position, count over the depth) "
                  "is not stated as a count")
    return _blocked(ctx, occ, defs, comp, reason, question_id=_q(occ, "depth"), rule_id="S5-SIDE-DEPTH-DEPENDENT",
                    side_spec=val, depth_state=dp["state"])


def _stirrups(ctx, occ, defs, rules, occ_block):
    out = {}
    fam = occ["family"]
    if occ_block[0]:
        for c in STIRRUP:
            out[c] = _blocked(ctx, occ, defs, c, occ_block[0], authority=occ_block[1],
                              question_id=_q(occ, "applicability"), rule_id="S5-OCCURRENCE-BLOCKED")
        return out
    st, val, inv, why = _invariant(occ, defs, lambda d: None if d.get("stirrup") is None else
                                   (int(d["stirrup"]["dia_mm"]), d["stirrup"]["mode"], d["stirrup"]["value"]),
                                   "a stirrup")
    if st == "NONE":
        for c in STIRRUP:
            out[c] = _not_applicable(ctx, occ, defs, c, why + " - nothing is inherited from another section",
                                     rule_id="S5-NO-STIRRUP-PRINTED")
        return out
    if st != "SAME":
        q = _q(occ, "stirrup_supersession") if st == "DIFFERENT" else _q(occ, "applicability")
        for c in STIRRUP:
            out[c] = _blocked(ctx, occ, defs, c, why, question_id=q, rule_id="S5-CANDIDATE-NOT-INVARIANT",
                              authority="SOURCE_CONFLICT" if st == "DIFFERENT" else "UNRESOLVED")
        return out
    dia, mode, value = val
    auth = _authority(occ, defs, "stirrup")
    attr_ok = auth in AR.RELEASING_AUTHORITIES
    for c, v, unit in (("STIRRUP_DIAMETER", dia, "mm"),
                       ("STIRRUP_SPACING", value, "mm" if mode == "SPACING_MM" else "per m")):
        if not attr_ok:
            out[c] = _blocked(ctx, occ, defs, c, f"stirrup source authority {auth}")
            continue
        pv = _prov(ctx, occ, defs, c, state=AR.VERIFIED, rule_id=f"S5-{c}", convention="NONE",
                   measurement="SCHEDULE_DERIVED", authority="SOURCE_EXPLICIT", formula=f"{c} = {v:g} {unit} (printed)",
                   inputs={"value": v, "unit": unit, "mode": mode, "candidate_invariant": inv},
                   CANDIDATE_INVARIANT=inv)
        out[c] = _row(occ, c, AR.VERIFIED, provenance=pv, value=v, unit=unit, candidate_invariant=inv)
    d_m = occ["lengths"].get("stirrup_distribution_m")
    if not attr_ok:
        out["STIRRUP_COUNT"] = _blocked(ctx, occ, defs, "STIRRUP_COUNT", f"stirrup source authority {auth}")
    elif d_m is None or d_m <= 0:
        out["STIRRUP_COUNT"] = _blocked(
            ctx, occ, defs, "STIRRUP_COUNT", "stirrup distribution length not established "
            f"({occ['lengths'].get('length_state')}: {'; '.join(occ['lengths'].get('issues') or []) or 'no run'})",
            question_id=_q(occ, "bar_run"), rule_id="S5-STIRRUP-DISTRIBUTION-UNRESOLVED")
    else:
        rm = RM.bar_count(mode, value, d_m, basis=occ["lengths"].get("stirrup_distribution_basis") or "")
        n = rm["verified"]
        pv = _prov(ctx, occ, defs, "STIRRUP_COUNT", state=AR.LOWER_BOUND, rule_id="S5-STIRRUP-COUNT-LB",
                   convention=rm["rule_id"] + " (verified lower bound only; +1 end bar NOT adopted)",
                   measurement="MEASURED", authority="SOURCE_DERIVED_HIGH_CONFIDENCE",
                   formula=f"n >= ceil(rate x distribution) = {rm['formula'].split(';')[0]}",
                   inputs={"mode": mode, "value": value, "distribution_m": d_m,
                           "distribution_basis": occ["lengths"].get("stirrup_distribution_basis"),
                           "count_lower_bound": n, "end_bar_convention_count_not_adopted": rm["convention"],
                           "candidate_invariant": inv},
                   CANDIDATE_INVARIANT=inv, LOW=n, BEST=n, HIGH=None, UNQUANTIFIED_COMPONENTS=[],
                   MISSING=["first / last stirrup position not stated (count is a lower bound)"])
        out["STIRRUP_COUNT"] = _row(occ, "STIRRUP_COUNT", AR.LOWER_BOUND, provenance=pv, count=n,
                                    count_convention_not_adopted=rm["convention"], distribution_m=d_m,
                                    dia_mm=dia, candidate_invariant=inv,
                                    why="first / last stirrup position not stated")
    # stirrup mass (core path): every facet must be source-supported
    facets = []
    w, dp = occ["width"], occ["depth"]
    if w["state"] not in DEPTH_KNOWN:
        facets.append(f"WIDTH {w['state']}" + (f" {w.get('candidates')}" if w.get("candidates") else ""))
    if dp["state"] not in DEPTH_KNOWN:
        facets.append(f"DEPTH {dp['state']}" + (f" (D <= {dp['bound_max_m']:.2f} m, no lower bound)"
                                                 if dp.get("bound_max_m") else "") +
                      (f" {dp.get('candidates')}" if dp.get("candidates") else ""))
    cov = rules.get("cover") or {}
    if cov.get("authority") not in AR.RELEASING_AUTHORITIES:
        facets.append("COVER not source-established")
    topo = rules["stirrup_topology"].get(fam, rules["stirrup_topology"].get("ALL"))
    if topo["state"] != "SOURCE_ESTABLISHED":
        facets.append(f"LEGS / LINK TOPOLOGY {topo['state']}: {topo['why']}")
    if rules["stirrup_hooks"]["state"] != "SOURCE_ESTABLISHED":
        facets.append(f"HOOKS {rules['stirrup_hooks']['state']}")
    if not facets:
        raise GroundSystemRebarError(f"{occ['occurrence_id']}: every stirrup facet is source-supported - S5 V1 "
                                     "computes no stirrup mass; add the path rule first")
    out["STIRRUP_CORE_PATH"] = _blocked(ctx, occ, defs, "STIRRUP_CORE_PATH",
                                        "stirrup mass needs width, depth, cover, legs, path and hooks; missing: " +
                                        "; ".join(facets), question_id=_q(occ, "stirrup_geometry"),
                                        rule_id="S5-STIRRUP-MASS-BLOCKED", missing_facets=facets,
                                        stirrup_count_known=out["STIRRUP_COUNT"]["state"] == AR.LOWER_BOUND)
    for c in ("STIRRUP_HOOK_1", "STIRRUP_HOOK_2"):
        out[c] = _blocked(ctx, occ, defs, c, f"stirrup hook angle / extension: {rules['stirrup_hooks']['why']}",
                          question_id=_q(occ, "stirrup_geometry"), rule_id="S5-STIRRUP-HOOK-BLOCKED")
    est, _, _, ewhy = _invariant(occ, defs, lambda d: d.get("end_zone"), "an end-zone stirrup callout")
    if est == "NONE":
        out["STIRRUP_END_ZONE_EXTRA"] = _not_applicable(ctx, occ, defs, "STIRRUP_END_ZONE_EXTRA",
                                                        ewhy + " (one uniform spacing / rate)")
    else:
        out["STIRRUP_END_ZONE_EXTRA"] = _blocked(ctx, occ, defs, "STIRRUP_END_ZONE_EXTRA",
                                                 ewhy or "end-zone callout not quantified")
    return out


def _ends(ctx, occ, defs, rules):
    out = {}
    fam = occ["family"]
    hook_c, dev_c = ENDS[fam][:2], ENDS[fam][2:]
    for i, (h, d) in enumerate(zip(hook_c, dev_c), start=1):
        node = occ["start_node" if i == 1 else "end_node"]
        issue = (occ.get("node_issues") or {}).get(str(i))
        tail = f" at end {i} ({node['kind']} {node.get('refs')})"
        if issue:
            tail += f"; support / end treatment unresolved: {issue}"
        out[h] = _blocked(ctx, occ, defs, h, f"bar-end hook / bend: {rules['bar_end_hooks']['why']}{tail}",
                          question_id=_q(occ, "end") if issue else _q(occ, "development"),
                          rule_id="S5-BAR-END-HOOK-BLOCKED", end=i, node_kind=node["kind"])
        out[d] = _blocked(ctx, occ, defs, d, f"development / anchorage: {rules['development']['why']}{tail}",
                          question_id=_q(occ, "end") if issue else _q(occ, "development"),
                          rule_id="S5-DEVELOPMENT-BLOCKED", end=i, node_kind=node["kind"])
    return out


def _extras(ctx, occ, defs, occ_block):
    out = {}
    for c in EXTRAS[occ["family"]]:
        if occ_block[0]:
            out[c] = _blocked(ctx, occ, defs, c, occ_block[0], authority=occ_block[1],
                              question_id=_q(occ, "applicability"), rule_id="S5-OCCURRENCE-BLOCKED")
            continue
        st, _, _, why = _invariant(occ, defs, lambda d, c=c: tuple(sorted(x for x in d.get("extras") or []
                                                                           if x.startswith(c))) or None,
                                   f"a {c} bar")
        if st == "NONE":
            out[c] = _not_applicable(ctx, occ, defs, c, why)
        else:
            out[c] = _blocked(ctx, occ, defs, c, why or f"{c} printed but not quantified",
                              question_id=_q(occ, "applicability"))
    return out


# ------------------------------------------------------------------------------------------------------ occurrence
def _check_rules(rules):
    for k in ("development", "bar_end_hooks", "stirrup_hooks"):
        if rules[k]["state"] != NOT_ESTABLISHED:
            raise GroundSystemRebarError(f"rule {k} is {rules[k]['state']}: S5 V1 computes no {k}; a project / "
                                         "engineer method must be approved and the engine extended first")


def occurrence_rebar(occ, defs, rules, ctx) -> dict:
    """All components of ONE physical ground-beam span or strap occurrence."""
    fam = occ.get("family")
    if fam not in FAMILIES:
        raise GroundSystemRebarError(f"{occ.get('occurrence_id')}: family {fam!r} not in {FAMILIES}")
    if occ.get("drawing_sha") != ctx["DRAWING_SHA"]:
        raise GroundSystemRebarError(f"{occ['occurrence_id']}: drawing sha {occ.get('drawing_sha')} != run drawing")
    for k in ("depth", "width"):
        if occ[k]["state"] not in DEPTH_STATES:
            raise GroundSystemRebarError(f"{occ['occurrence_id']}: {k} state {occ[k]['state']} not in {DEPTH_STATES}")
    _check_rules(rules)
    UM.validate(ctx["unit_mass"])
    kgm_of = lambda dia: UM.kg_per_m(dia, ctx["unit_mass"])  # noqa: E731
    occ_block = _occurrence_block(occ, defs)
    comps = {}
    for c in LONGITUDINAL[fam]:
        comps[c] = _longitudinal(ctx, occ, defs, c, kgm_of, occ_block)
    if fam == GROUND_BEAM:
        comps["SIDE_REBAR"] = _side(ctx, occ, defs, occ_block)
    comps.update(_stirrups(ctx, occ, defs, rules, occ_block))
    comps.update(_ends(ctx, occ, defs, rules))
    comps.update(_extras(ctx, occ, defs, occ_block))
    out = [comps[c] for c in COMPONENTS[fam]]
    return _finish(occ, out)


def _part(c):
    fam = c["family"]
    return {"part_id": f"{c['occurrence_id']}:{c['component']}", "category": GP.CATEGORY[fam],
            "component": c["accurate_component"], "state": c["state"], "kg": c["kg"],
            "basis": ["DRAWING_OCCURRENCE", "SCHEDULE", "STRUCTURAL_DETAIL", "DETERMINISTIC_GEOMETRY"],
            "provenance": c["provenance"]}


def _finish(occ, comps):
    unq = sorted({c["accurate_component"] for c in comps
                  if c["state"] == AR.BLOCKED_UNQUANTIFIED and c["quantity_kind"] == MASS})
    for c in comps:
        if "UNQUANTIFIED_COMPONENTS" in c["provenance"]:
            c["provenance"]["UNQUANTIFIED_COMPONENTS"] = unq
    parts = []
    for c in comps:
        validate_record(c)
        if c["quantity_kind"] == MASS and c["state"] in AR.STATES:
            p = _part(c)
            GP.validate_s5_part(p)
            parts.append(p)
    mass = [c for c in comps if c["quantity_kind"] == MASS]
    known = [c for c in mass if c["kg"] is not None]
    states = Counter(c["state"] for c in mass)
    if known and all(c["state"] == AR.VERIFIED for c in known) and not states[AR.BLOCKED_UNQUANTIFIED]:
        occ_state = OCC_VERIFIED
    elif any(c["state"] in (AR.LOWER_BOUND, AR.VERIFIED) for c in known):
        occ_state = OCC_LOWER_BOUND
    elif any(c["state"] == AR.PROVISIONAL for c in known):
        occ_state = OCC_PROVISIONAL
    else:
        occ_state = OCC_BLOCKED
    cnt = next((c for c in comps if c["component"] == "STIRRUP_COUNT"), None)
    L = occ["lengths"]
    row = {"occurrence_id": occ["occurrence_id"], "family": occ["family"], "mark": occ["mark"],
           "occurrence_state": occ_state, "known_kg": sum(c["kg"] for c in known),
           "known_straight_length_m": sum(c["total_length_m"] for c in known if "total_length_m" in c),
           "stirrup_count_lower_bound": cnt["count"] if cnt and cnt["state"] == AR.LOWER_BOUND else None,
           "unquantified_components": unq,
           "components_by_state": dict(sorted(Counter(c["state"] for c in comps).items())),
           "start_node": occ["start_node"], "end_node": occ["end_node"],
           "geometry_handles": list(occ["geometry_handles"]),
           "member_centerline_length_m": L.get("centreline_m"), "member_clear_concrete_length_m":
               L.get("clear_concrete_m"), "support_face_to_face_run_m": L.get("face_to_face_m"),
           "bar_straight_run_lower_bound_m": L.get("bar_run_lb_m"), "length_state": L.get("length_state"),
           "width_mm": occ["width"].get("value_mm"), "width_state": occ["width"]["state"],
           "depth_mm": occ["depth"].get("value_mm"), "depth_state": occ["depth"]["state"],
           "depth_bound_max_m": occ["depth"].get("bound_max_m"),
           "detail_ids": list(occ["detail_ids"]), "detail_applicability_state": occ["applicability"],
           "why_candidate": occ.get("why_candidate") or "", "why_not_resolved": occ.get("why_not_resolved") or "",
           "flags": list(occ.get("flags") or [])}
    return {"occurrence": row, "components": comps, "parts": parts}


def bbs_lines(components) -> list:
    """Net BBS: one STRAIGHT line per quantified longitudinal component (development / hooks not included)."""
    out = []
    for c in components:
        if c["quantity_kind"] != MASS or c["kg"] is None:
            continue
        out.append({"bbs_id": f"{c['occurrence_id']}:{c['component']}", "occurrence_id": c["occurrence_id"],
                    "family": c["family"], "mark": c["mark"], "component": c["component"], "state": c["state"],
                    "dia_mm": c["dia_mm"], "shape": "STRAIGHT (ends not included)",
                    "bar_length_m": c["straight_run_m"], "count": c["bar_count"],
                    "total_length_m": c["total_length_m"], "kg_per_m": c["kg_per_m"], "net_bbs_kg": c["kg"],
                    "development_included": False, "hooks_included": False, "used_kg": None, "purchased_kg": None,
                    "waste_kg": None, "procurement": "NOT_COMPUTED (procurement layer not invoked)"})
    return out


def _family_summary(fam, occ_rows, comps):
    fc = [c for c in comps if c["family"] == fam]
    fo = [r for r in occ_rows if r["family"] == fam]
    by = defaultdict(float)
    for c in fc:
        if c["kg"] is not None:
            by[c["state"]] += c["kg"]
    blocked = [c for c in fc if c["state"] == AR.BLOCKED_UNQUANTIFIED]
    final = not blocked and not by.get(AR.LOWER_BOUND) and not by.get(AR.PROVISIONAL) and \
        not by.get(AR.BLOCKED_MODELLED)
    cnt = [c for c in fc if c["component"] == "STIRRUP_COUNT"]
    return {"family": fam, "occurrences": len(fo),
            "occurrences_by_state": dict(sorted(Counter(r["occurrence_state"] for r in fo).items())),
            "VERIFIED_KG": by.get(AR.VERIFIED, 0.0), "LOWER_BOUND_KNOWN_KG": by.get(AR.LOWER_BOUND, 0.0),
            "PROVISIONAL_KG": by.get(AR.PROVISIONAL, 0.0), "BLOCKED_MODELLED_KG": by.get(AR.BLOCKED_MODELLED, 0.0),
            "BLOCKED_UNQUANTIFIED_COMPONENTS": len(blocked),
            "blocked_unquantified_by_component": dict(sorted(Counter(c["component"] for c in blocked).items())),
            "known_straight_length_m": sum(c.get("total_length_m", 0.0) for c in fc if c["kg"] is not None),
            "stirrup_counts_quantified": sum(1 for c in cnt if c["state"] == AR.LOWER_BOUND),
            "stirrup_count_lower_bound_total": sum(c["count"] for c in cnt if c["state"] == AR.LOWER_BOUND),
            "stirrup_masses_quantified": sum(1 for c in fc if c["component"] == "STIRRUP_CORE_PATH"
                                             and c["kg"] is not None),
            "kg_by_diameter": {str(d): sum(c["kg"] for c in fc if c["kg"] is not None and c.get("dia_mm") == d)
                               for d in sorted({c.get("dia_mm") for c in fc if c["kg"] is not None})},
            "final": "FINAL_ESTABLISHED" if final else "FINAL NOT ESTABLISHED"}


def run(occurrences, definitions, rules, ctx) -> dict:
    ids = Counter(o["occurrence_id"] for o in occurrences)
    dup = [k for k, n in ids.items() if n > 1]
    if dup:
        raise GroundSystemRebarError(f"occurrence id entered twice: {dup}")
    res = [occurrence_rebar(o, definitions, rules, ctx) for o in sorted(occurrences, key=lambda z: z["occurrence_id"])]
    comps = [c for r in res for c in r["components"]]
    parts = [p for r in res for p in r["parts"]]
    occ_rows = [r["occurrence"] for r in res]
    bbs = bbs_lines(comps)
    summ = AR.summarise(parts)
    fams = {f: _family_summary(f, occ_rows, comps) for f in FAMILIES}
    known = sum(f["VERIFIED_KG"] + f["LOWER_BOUND_KNOWN_KG"] for f in fams.values())
    final = all(f["final"] == "FINAL_ESTABLISHED" for f in fams.values())
    summary = {
        "policy": POLICY_ID, "headline": "KNOWN SOURCE-DERIVED GROUND-SYSTEM REBAR",
        "known_source_derived_ground_system_rebar_kg": known,
        "final_ground_system_rebar": "FINAL GROUND-SYSTEM REBAR ESTABLISHED" if final else
        "FINAL GROUND-SYSTEM REBAR NOT ESTABLISHED",
        "families": fams, "occurrences": len(occ_rows),
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
    occ_len = all(abs(sum(c.get("total_length_m", 0.0) for c in by_occ[r["occurrence_id"]] if c["kg"] is not None)
                      - r["known_straight_length_m"]) <= tol for r in occ_rows)
    occ_kg = all(abs(sum(c["kg"] for c in by_occ[r["occurrence_id"]] if c["kg"] is not None) - r["known_kg"]) <= tol
                 for r in occ_rows)
    proj_kg = sum(r["known_kg"] for r in occ_rows)
    part_kg = sum(p["kg"] for p in parts if p["kg"] is not None)
    bbs_kg = sum(b["net_bbs_kg"] for b in bbs)
    each_once = all(sorted(c["component"] for c in by_occ[r["occurrence_id"]]) ==
                    sorted(REQUIRED_PER_OCCURRENCE[r["family"]]) for r in occ_rows)
    pop = Counter(c["state"] for c in comps)
    no_kg = all(c["kg"] is None for c in comps
                if c["state"] in (AR.BLOCKED_UNQUANTIFIED, NOT_REQUIRED, NOT_APPLICABLE) or c["quantity_kind"] != MASS)
    mass_blocked = sum(1 for c in comps if c["quantity_kind"] == MASS and c["state"] == AR.BLOCKED_UNQUANTIFIED)
    cats = summ["categories"]
    summ_ok = abs(sum(v.get("verified_kg", 0) + v.get("lower_bound_kg", 0) + v.get("provisional_kg", 0)
                      for v in cats.values()) - proj_kg) <= 1e-6 and \
        sum(v.get("blocked_unquantified_parts", 0) for v in cats.values()) == mass_blocked
    parts_once = len({p["part_id"] for p in parts}) == len(parts) == sum(
        1 for c in comps if c["quantity_kind"] == MASS and c["state"] in AR.STATES)
    prov_ok = True
    try:
        for c in comps:
            validate_record(c)
        for p in parts:
            GP.validate_s5_part(p)
    except (GroundSystemRebarError, ValueError):
        prov_ok = False
    checks = {"component_length_equals_occurrence_known_length": occ_len,
              "component_kg_equals_occurrence_known_kg": occ_kg,
              "occurrence_kg_equals_project_known_kg": abs(proj_kg - part_kg) <= 1e-6,
              "bbs_net_kg_equals_known_parts_kg": abs(bbs_kg - part_kg) <= 1e-6,
              "every_component_terminates_once_per_occurrence": each_once,
              "every_mass_component_is_one_accurate_part": parts_once,
              "population_reconciles": sum(pop.values()) == len(comps),
              "blocked_and_non_mass_components_carry_no_kg": no_kg,
              "accurate_summary_reconciles": summ_ok,
              "every_component_passes_the_generic_contract": prov_ok}
    return {"checks": checks, "all_pass": all(checks.values()), "project_known_kg": proj_kg,
            "population_by_state": dict(sorted(pop.items())),
            "population_by_component_state": {k: dict(sorted(Counter(c["state"] for c in comps
                                                                     if c["component"] == k).items()))
                                              for k in sorted({c["component"] for c in comps})}}


def policy_record() -> dict:
    return {"policy_id": POLICY_ID, "families": list(FAMILIES),
            "components": {f: list(COMPONENTS[f]) for f in FAMILIES},
            "accurate_component": ACCURATE_COMPONENT, "quantity_kind": KIND,
            "component_states": list(COMPONENT_STATES), "depth_states": list(DEPTH_STATES),
            "rules": ["one record per physical occurrence; generic ELEMENT_* identity, never FOOTING_*",
                      "detail applicability taken as given; candidates are never chosen",
                      "candidate detail: a component releases only when identical in every candidate",
                      "longitudinal kg = n x BAR_STRAIGHT_RUN_LOWER_BOUND x D^2/162 (no centreline / clear / min)",
                      "two lower rows kept separate",
                      "development, bar-end hooks, stirrup hooks BLOCKED_UNQUANTIFIED (no code / note default)",
                      "stirrup count = ceil(rate x distribution) lower bound; +1 end bar not adopted",
                      "stirrup mass only when width, depth, cover, legs, path and hooks are all source-supported",
                      "side bars per depth blocked while depth is not source-explicit",
                      "blocked components stay listed and carry no kg", "net only; procurement not computed"]}
