"""SUPERSTRUCTURE_BEAM_REBAR (S6) - accurate simple-beam and continuous-beam reinforcement, occurrence by occurrence,
component by component, bar run by bar run (generic; stdlib + engine.source only).

Inputs are controlled registers, never a drawing:
  * occurrences  one physical member each (a simple-beam span, or one continuous-beam group of spans):
                 {occurrence_id, subfamily (SIMPLE_BEAM | CONTINUOUS_BEAM), mark, drawing_sha, sheet, floor,
                  identity {SOURCE_HANDLES, GEOMETRY_HANDLES, TAG_HANDLES, SCHEDULE_HANDLES, START_SUPPORT, END_SUPPORT,
                            DRAWN_WIDTH_MM, SCHEDULE_WIDTH_MM, WIDTH_MATCH_STATE, DETAIL_ID, DETAIL_CANDIDATES,
                            SCHEDULE_ROW, BINDING_STATE, GEOMETRY_OBJECTS},
                  geometry {...known physical geometry, kept even when the rebar is blocked...},
                  cb None | {CB_GROUP_ID, SPAN_SEQUENCE, READING_DIRECTION_STATE, SEQUENCE_STATE,
                             spans {"<schedule span index>": {cc_m, clear_m, ...}}},
                  blocks [{reason, authority, question_id, kind}]   occurrence-level blocking reasons (binding,
                            width conflict, span sequence, an undefined candidate detail) - they block every
                            schedule-dependent component, never the physical geometry,
                  bar_runs [{BAR_RUN_ID, component, frame_role, label, count, dia_mm, segments [{kind, length_m,
                             state, rule_id?, span?, support?}], register_run_m, start_location, end_location,
                             spans_crossed, intermediate_supports, source_extent, source_handles, schedule_handles,
                             geometry_handles, support_ids, detail_id, authority, convention_id, run_rule_id,
                             missing [...], source_block None | reason, question_id, interpretations None | [...],
                             source_tokens [...]}],
                  stirrups [{SPAN_INDEX, dia_mm, mode (BARS_PER_METRE | SPACING_MM), value, distribution_m,
                             distribution_basis, register_count, legs, hooks, end_zone, first_last,
                             core_path_missing [...], interpretations, source_block, question_id, source_tokens}],
                  status {component: {state (NOT_APPLICABLE | BLOCKED), why, question_id, authority}},
                  side None | {applicability, raw_text, count, dia_mm, spacing_cm, why, token_handles},
                  hanger {state (ABSENT | ...), why, question_id}, openings [...], questions {...}, flags [...]}
  * rules        {typical {rule_id: {state BOUND | UNRESOLVED, kind FIXED_EXTENSION_M | FACTOR_OF_SPAN, value,
                  span_basis AXIS_TO_AXIS | FACE_TO_FACE, applies_to [...], text, why}},
                  span_symbols {Ln: AXIS_TO_AXIS, L: FACE_TO_FACE, authority, why},
                  development, bar_end_hooks, stirrup_hooks, stirrup_topology, side_bar_semantics, hanger
                  {state NOT_ESTABLISHED, why}}
  * context      {PROJECT_ID, DRAWING_ID, DRAWING_SHA, REVISION, ENGINE_COMMIT, REGISTER_VERSION, CALCULATION_ROUND,
                  unit_mass {method ...}}

Rules (no exceptions):
  * one record per physical occurrence; generic identity ELEMENT_FAMILY = BEAM with ELEMENT_SUBFAMILY SIMPLE_BEAM |
    CONTINUOUS_BEAM (rebar_provenance knows BEAM, not the subfamilies);
  * a continuous bar is ONE bar run (BAR_RUN_ID) however many supports it crosses; never split at a support;
  * straight run = the sum of its source segments: measured geometry (face to face, clear span, through a support)
    plus an extension only when its typical-detail rule is BOUND and applies to that bar role (the 7.5 cm rule is
    never generalised); an unbound / unresolved extension (0.15L, 0.3 Ln2, ...) adds no length and is listed missing;
  * a MID / support bar extent is factor x the span named by the drawing's own symbol definition (Ln axis to axis,
    L face to face on ST7757) - recomputed here and checked against the register;
  * kg = count x straight run x kg/m (rebar_unit_mass, D^2/162). Known straight steel whose ends (development,
    hooks, in-span end treatment) are not established is a LOWER_BOUND: the known segment is not downgraded and the
    bar is never called complete (no VERIFIED_COMPLETE in V1);
  * an ambiguous reading direction releases a component only when every interpretation gives the same component,
    count, diameter and run rule (CANDIDATE_INVARIANT); any difference is BLOCKED_UNQUANTIFIED; nothing is chosen;
  * development, bar-end hooks, hangers, side bars and stirrup mass are BLOCKED_UNQUANTIFIED (V1 accepts no code /
    practice default); stirrup COUNT is a lower bound ceil(rate x clear run) with no +1;
  * a design load (T/M) or any non-rebar token can never produce steel: every quantified record names rebar tokens
    and a non-rebar token anywhere in a bar's source raises;
  * a beam opening activates the opening components only when a physical opening is source-identified in the beam;
  * blocked components stay listed and carry no kg; net only.
"""

from __future__ import annotations

import math
from collections import Counter, defaultdict

from engine.source import accurate_boq_rebar as AR
from engine.source import rebar_model as RM
from engine.source import rebar_provenance as RP
from engine.source import rebar_unit_mass as UM

POLICY_ID = "SUPERSTRUCTURE_BEAM_REBAR_S6_V1"
ELEMENT_FAMILY = "BEAM"
CATEGORY = "BEAMS"
SIMPLE_BEAM, CONTINUOUS_BEAM = "SIMPLE_BEAM", "CONTINUOUS_BEAM"
SUBFAMILIES = (SIMPLE_BEAM, CONTINUOUS_BEAM)
NOT_APPLICABLE = "NOT_APPLICABLE"
COMPONENT_STATES = AR.STATES + (NOT_APPLICABLE,)
MASS, COUNT = "MASS", "COUNT"

BAR_RUN_COMPONENTS = ("TOP_MAIN", "BOTTOM_MAIN", "TOP_SUPPORT", "BOTTOM_SUPPORT", "MID_TOP", "MID_BOTTOM", "HANGER")
STIRRUP_COMPONENTS = ("STIRRUP_COUNT", "STIRRUP_CORE_PATH")
END_COMPONENTS = ("HOOK_1", "HOOK_2", "DEVELOPMENT_1", "DEVELOPMENT_2")
OPENING_COMPONENTS = ("OPENING_EXTRA_TOP", "OPENING_EXTRA_BOTTOM", "OPENING_EXTRA_SIDE", "OPENING_EXTRA_STIRRUP")
COMPONENTS = (BAR_RUN_COMPONENTS + ("SIDE_REBAR",) + STIRRUP_COMPONENTS + END_COMPONENTS + OPENING_COMPONENTS +
              ("OTHER_EXPLICIT_EXTRA",))
ACCURATE_COMPONENT = {
    "TOP_MAIN": "BEAM_TOP_BAR", "BOTTOM_MAIN": "BEAM_BOTTOM_BAR", "TOP_SUPPORT": "BEAM_EXTRA_BAR",
    "BOTTOM_SUPPORT": "BEAM_EXTRA_BAR", "MID_TOP": "BEAM_EXTRA_BAR", "MID_BOTTOM": "BEAM_EXTRA_BAR",
    "HANGER": "BEAM_EXTRA_BAR", "SIDE_REBAR": "BEAM_SIDE_BAR", "STIRRUP_COUNT": "BEAM_STIRRUP",
    "STIRRUP_CORE_PATH": "BEAM_STIRRUP", "HOOK_1": "ANCHORAGE", "HOOK_2": "ANCHORAGE", "DEVELOPMENT_1": "ANCHORAGE",
    "DEVELOPMENT_2": "ANCHORAGE", "OPENING_EXTRA_TOP": "SPECIAL_DETAIL_BAR",
    "OPENING_EXTRA_BOTTOM": "SPECIAL_DETAIL_BAR", "OPENING_EXTRA_SIDE": "SPECIAL_DETAIL_BAR",
    "OPENING_EXTRA_STIRRUP": "BEAM_STIRRUP", "OTHER_EXPLICIT_EXTRA": "SPECIAL_DETAIL_BAR"}
KIND = {c: (COUNT if c == "STIRRUP_COUNT" else MASS) for c in COMPONENTS}

# straight-run segments: measured geometry needs no rule; an extension needs a BOUND typical rule for its bar role
GEOMETRY_SEGMENTS = ("FACE_TO_FACE", "CLEAR_SPAN", "THROUGH_SUPPORT")
RULE_SEGMENTS = ("BEYOND_FAR_FACE", "INTO_SPAN_LEFT", "INTO_SPAN_RIGHT")
RULE_KINDS = ("FIXED_EXTENSION_M", "FACTOR_OF_SPAN")
SPAN_BASES = ("AXIS_TO_AXIS", "FACE_TO_FACE")
READING_STATES = ("FORWARD", "REVERSED", "AMBIGUOUS", "NONE")
NOT_ESTABLISHED = "NOT_ESTABLISHED"
# segment / complete-bar vocabularies (section 23 of the S6 brief)
SEGMENT_SOURCE_VERIFIED, SEGMENT_LOWER_BOUND = "SOURCE_VERIFIED", "LOWER_BOUND_SEGMENT"
COMPLETE_NOT_ESTABLISHED = "NOT_ESTABLISHED"
RELEASE_BASIS = ("SOURCE_BOUND", "CANDIDATE_INVARIANT")
OCC_VERIFIED, OCC_LOWER_BOUND, OCC_BLOCKED = "VERIFIED", "LOWER_BOUND", "BLOCKED"

# token guard: only these schedule field families can ever carry steel; a load / section / span token never does
REBAR_FIELD_FAMILIES = ("TOP_MAIN", "BOTTOM_MAIN", "TOP", "BOTTOM", "MID", "STIRRUP", "SIDE_REBAR")
LOAD_GRAMMARS = ("DESIGN_LOAD_T_PER_M",)
QUANTIFYING_TOKEN_TERMINALS = ("PARSED_BOUND",)
TOKEN_TERMINALS = ("CONSUMED_BY_RELEASED_COMPONENT", "CONSUMED_BY_BLOCKED_COMPONENT_ONLY", "EXCLUDED_DESIGN_LOAD",
                   "EXCLUDED_NOT_REBAR", "RETAINED_BLOCKED_SEMANTICS", "RETAINED_UNBOUND_IN_BLOCKED_OCCURRENCE",
                   "NO_S6_OCCURRENCE")

S6_EXTRA_FIELDS = ("ELEMENT_SUBFAMILY", "S6_COMPONENT", "QUANTITY_KIND", "SCHEDULE_HANDLES", "GEOMETRY_HANDLES",
                   "TAG_HANDLES", "DETAIL_ID", "SCHEDULE_ROW", "BINDING_STATE", "START_SUPPORT", "END_SUPPORT",
                   "DRAWN_WIDTH_MM", "SCHEDULE_WIDTH_MM", "WIDTH_MATCH_STATE")
CB_FIELDS = ("CB_GROUP_ID", "SPAN_SEQUENCE", "READING_DIRECTION_STATE")
RECORD_FIELDS = RP.BASE_FIELDS + S6_EXTRA_FIELDS


class SuperstructureBeamRebarError(ValueError):
    pass


# ------------------------------------------------------------------------------------------------- token guard
def is_rebar_token(tok: dict) -> bool:
    """True only for a parsed reinforcement token. A T/M design load, a section size, a span length, a point-load
    number or an unparsed fragment is never steel."""
    fam, gram = tok.get("field_family"), tok.get("grammar")
    norm = str(tok.get("normalised") or "").lower().replace(" ", "")
    return (tok.get("terminal") in QUANTIFYING_TOKEN_TERMINALS and fam in REBAR_FIELD_FAMILIES and
            gram not in LOAD_GRAMMARS and not norm.endswith("t/m"))


def assert_rebar_tokens(tokens, where: str):
    """Every token a quantity is built from must be a rebar token; raises otherwise (a T/M value can never produce
    steel, whatever field it was mis-filed under)."""
    for t in tokens or ():
        if not is_rebar_token(t):
            raise SuperstructureBeamRebarError(
                f"{where}: token {t.get('token_id')} ({t.get('field_family')} / {t.get('grammar')} "
                f"'{t.get('normalised') or t.get('raw')}', terminal {t.get('terminal')}) is not reinforcement - "
                "a design load or non-rebar value can never produce steel")
    return True


def is_load_or_non_rebar_token(tok: dict) -> bool:
    """A design load (T/M), a section size, a span length or a load-line number: never steel, in any role."""
    norm = str(tok.get("normalised") or "").lower().replace(" ", "")
    return tok.get("terminal") == "NOT_REBAR" or tok.get("grammar") in LOAD_GRAMMARS or norm.endswith("t/m") or \
        tok.get("field_family") not in REBAR_FIELD_FAMILIES


def assert_no_load_tokens(tokens, where: str):
    """Any component (released or blocked) may cite an empty / ambiguous schedule cell as evidence, but never a
    non-rebar token: a T/M value attached to a bar raises."""
    for t in tokens or ():
        if is_load_or_non_rebar_token(t):
            raise SuperstructureBeamRebarError(
                f"{where}: token {t.get('token_id')} ({t.get('field_family')} / {t.get('grammar')} "
                f"'{t.get('normalised') or t.get('raw')}') is not reinforcement - a design load or non-rebar value "
                "can never produce steel")
    return True


def token_terminal(tok: dict, consumers: list, *, in_blocked_occurrence: bool = False) -> str:
    """The S6 terminal of one source token. consumers: the states of the components built from it. A rebar token of
    a blocked occurrence that no component can bind (e.g. a schedule span without a plan span) is retained, never
    dropped; a schedule row with no plan occurrence at all is NO_S6_OCCURRENCE."""
    if tok.get("terminal") == "NOT_REBAR":
        return "EXCLUDED_DESIGN_LOAD" if (tok.get("grammar") in LOAD_GRAMMARS or tok.get("field_family") == "T/M") \
            else "EXCLUDED_NOT_REBAR"
    if tok.get("terminal") in ("PARSED_AMBIGUOUS", "BLOCKED_SEMANTICS"):
        return "RETAINED_BLOCKED_SEMANTICS"
    if not consumers:
        return "RETAINED_UNBOUND_IN_BLOCKED_OCCURRENCE" if in_blocked_occurrence else "NO_S6_OCCURRENCE"
    return "CONSUMED_BY_RELEASED_COMPONENT" if any(s in AR.RELEASED_STATES for s in consumers) \
        else "CONSUMED_BY_BLOCKED_COMPONENT_ONLY"


# ------------------------------------------------------------------------------------------------- record contract
def validate_record(rec: dict) -> dict:
    """The contract for EVERY S6 component row. Mass parts additionally pass rebar_provenance.validate_part.
    Raises SuperstructureBeamRebarError naming the first defect."""
    pid = rec.get("record_id")
    pv = rec.get("provenance")
    if not isinstance(pv, dict):
        raise SuperstructureBeamRebarError(f"{pid}: every S6 component carries a provenance record")
    try:
        ident = RP.element_identity(pv)
    except RP.ProvenanceError as e:
        raise SuperstructureBeamRebarError(f"{pid}: {e}") from None
    if ident["ELEMENT_FAMILY"] != ELEMENT_FAMILY or ident["ELEMENT_OCCURRENCE_ID"] != rec["occurrence_id"]:
        raise SuperstructureBeamRebarError(f"{pid}: provenance identity {ident} does not name this occurrence")
    missing = [f for f in RECORD_FIELDS if f not in pv or pv[f] is None or (pv[f] in ("", [], ()) and f != "INPUTS")]
    if rec["subfamily"] == CONTINUOUS_BEAM:
        missing += [f for f in CB_FIELDS if pv.get(f) in (None, "", [], ())]
    if rec.get("bar_run_id") and not pv.get("BAR_RUN_ID"):
        missing.append("BAR_RUN_ID")
    if rec.get("span_index") is not None and pv.get("SPAN_INDEX") is None:
        missing.append("SPAN_INDEX")
    if missing:
        raise SuperstructureBeamRebarError(f"{pid}: provenance missing {missing}")
    if pv["ELEMENT_SUBFAMILY"] != rec["subfamily"] or pv["ELEMENT_SUBFAMILY"] not in SUBFAMILIES:
        raise SuperstructureBeamRebarError(f"{pid}: ELEMENT_SUBFAMILY disagrees with the row")
    if pv["S6_COMPONENT"] != rec["component"] or pv["QUANTITY_KIND"] != rec["quantity_kind"]:
        raise SuperstructureBeamRebarError(f"{pid}: provenance component / kind disagree with the row")
    if pv["RELEASE_STATE"] != rec["state"] or rec["state"] not in COMPONENT_STATES:
        raise SuperstructureBeamRebarError(f"{pid}: RELEASE_STATE {pv['RELEASE_STATE']} != row state {rec['state']}")
    if pv["AUTHORITY_STATE"] not in AR.AUTHORITY_STATES or pv["MEASUREMENT_STATE"] not in AR.MEASUREMENT_STATES:
        raise SuperstructureBeamRebarError(f"{pid}: unknown authority / measurement state")
    if pv["AUTHORITY_STATE"] in AR.NON_QUANTIFYING_AUTHORITIES and rec["state"] in AR.RELEASED_STATES:
        raise SuperstructureBeamRebarError(f"{pid}: authority {pv['AUTHORITY_STATE']} cannot release {rec['state']}")
    if rec["state"] == AR.BLOCKED_UNQUANTIFIED and not pv.get("BLOCKING_REASON"):
        raise SuperstructureBeamRebarError(f"{pid}: a blocked component names its BLOCKING_REASON")
    if rec["state"] == AR.VERIFIED or rec.get("complete_bar_state") == "VERIFIED_COMPLETE":
        raise SuperstructureBeamRebarError(f"{pid}: S6 V1 never calls a beam bar complete / VERIFIED")
    released = rec["state"] in AR.RELEASED_STATES
    if released:
        if not rec.get("source_tokens"):
            raise SuperstructureBeamRebarError(f"{pid}: a released quantity names the rebar tokens it comes from")
        assert_rebar_tokens(rec["source_tokens"], pid)
        if pv.get("RELEASE_BASIS") not in RELEASE_BASIS:
            raise SuperstructureBeamRebarError(f"{pid}: a released row states its RELEASE_BASIS {RELEASE_BASIS}")
    if rec["quantity_kind"] == MASS:
        if (rec["kg"] is None) != (rec["state"] in (AR.BLOCKED_UNQUANTIFIED, NOT_APPLICABLE)):
            raise SuperstructureBeamRebarError(f"{pid}: a mass component carries kg iff it is quantified")
        if rec["kg"] is not None:
            exp = rec["bar_count"] * rec["straight_run_m"] * rec["kg_per_m"]
            if abs(exp - rec["kg"]) > 1e-9 or abs(rec["total_length_m"] - rec["bar_count"] * rec["straight_run_m"]) \
                    > 1e-9:
                raise SuperstructureBeamRebarError(f"{pid}: kg != count x straight run x kg/m")
    elif rec["kg"] is not None:
        raise SuperstructureBeamRebarError(f"{pid}: a {rec['quantity_kind']} record never carries kg")
    if rec["quantity_kind"] == COUNT and released:
        lo, best, hi = pv.get("LOW"), pv.get("BEST"), pv.get("HIGH")
        if not (isinstance(rec.get("count"), int) and lo == rec["count"] and best is not None and lo <= best and
                (hi is None or best <= hi)):
            raise SuperstructureBeamRebarError(f"{pid}: a released count states LOW = count <= BEST (<= HIGH)")
    return rec


def validate_part(p: dict) -> dict:
    """An S6 mass part: the generic accurate part + provenance contract (rebar_provenance) + the S6 fields."""
    RP.validate_part(p)
    pv = p["provenance"]
    miss = [f for f in S6_EXTRA_FIELDS if pv.get(f) in (None, "", [], ())]
    if pv.get("ELEMENT_SUBFAMILY") == CONTINUOUS_BEAM:
        miss += [f for f in CB_FIELDS if pv.get(f) in (None, "", [], ())]
    if miss:
        raise SuperstructureBeamRebarError(f"{p['part_id']}: S6 provenance missing {miss}")
    if p["category"] != CATEGORY:
        raise SuperstructureBeamRebarError(f"{p['part_id']}: category {p['category']} != {CATEGORY}")
    return p


# ------------------------------------------------------------------------------------------------------- helpers
def _ids(*lists):
    return list(dict.fromkeys(str(h) for lst in lists for h in (lst or ()) if h not in (None, "")))


def _prov(ctx, occ, comp, *, state, rule_id, convention, measurement, authority, formula, inputs, run=None,
          span_index=None, text=None, handles=(), schedule_handles=(), geometry_handles=(), **extra):
    idn = occ["identity"]
    run = run or {}
    pv = {"PROJECT_ID": ctx["PROJECT_ID"], "DRAWING_ID": ctx["DRAWING_ID"], "DRAWING_SHA": ctx["DRAWING_SHA"],
          "REVISION": ctx["REVISION"], "SHEET_REGION": occ.get("sheet") or "UNKNOWN_SHEET",
          "SOURCE_HANDLES": _ids(handles, run.get("source_handles"), idn.get("SOURCE_HANDLES")),
          "SOURCE_TEXT": text or run.get("source_text") or idn.get("SOURCE_TEXT") or occ["mark"],
          "COMPONENT": ACCURATE_COMPONENT[comp], "S6_COMPONENT": comp, "QUANTITY_KIND": KIND[comp],
          "RULE_ID": rule_id, "CONVENTION_ID": convention, "MEASUREMENT_STATE": measurement,
          "AUTHORITY_STATE": authority, "RELEASE_STATE": state, "FORMULA": formula, "INPUTS": inputs,
          "ENGINE_COMMIT": ctx["ENGINE_COMMIT"], "REGISTER_VERSION": ctx["REGISTER_VERSION"],
          "CALCULATION_ROUND": ctx["CALCULATION_ROUND"], "ELEMENT_SUBFAMILY": occ["subfamily"],
          "SCHEDULE_HANDLES": _ids(schedule_handles, run.get("schedule_handles"), idn.get("SCHEDULE_HANDLES")),
          "GEOMETRY_HANDLES": _ids(geometry_handles, run.get("geometry_handles"), idn.get("GEOMETRY_HANDLES")),
          "TAG_HANDLES": _ids(idn.get("TAG_HANDLES")),
          "DETAIL_ID": run.get("detail_id") or idn.get("DETAIL_ID") or "NONE",
          "DETAIL_CANDIDATES": list(idn.get("DETAIL_CANDIDATES") or []),
          "SCHEDULE_ROW": idn.get("SCHEDULE_ROW") or "NONE", "BINDING_STATE": idn.get("BINDING_STATE"),
          "START_SUPPORT": idn.get("START_SUPPORT"), "END_SUPPORT": idn.get("END_SUPPORT"),
          "SUPPORT_IDS": list(run.get("support_ids") or idn.get("SUPPORT_IDS") or []),
          "DRAWN_WIDTH_MM": idn.get("DRAWN_WIDTH_MM"), "SCHEDULE_WIDTH_MM": idn.get("SCHEDULE_WIDTH_MM"),
          "WIDTH_MATCH_STATE": idn.get("WIDTH_MATCH_STATE"), "OCCURRENCE_FLAGS": list(occ.get("flags") or [])}
    if occ.get("cb"):
        cb = occ["cb"]
        pv.update({"CB_GROUP_ID": cb["CB_GROUP_ID"], "SPAN_SEQUENCE": cb["SPAN_SEQUENCE"],
                   "READING_DIRECTION_STATE": cb["READING_DIRECTION_STATE"]})
    if run.get("BAR_RUN_ID"):
        pv["BAR_RUN_ID"] = run["BAR_RUN_ID"]
        pv["SPAN_INDEX"] = list(run.get("spans_crossed") or [])
    if span_index is not None:
        pv["SPAN_INDEX"] = span_index
    pv.update(RP.identity_fields(family=ELEMENT_FAMILY, occurrence_id=occ["occurrence_id"], mark=occ["mark"]))
    pv.update(extra)
    return pv


def _record_id(occ, comp, run=None, span_index=None):
    if run is not None:
        return f"{occ['occurrence_id']}|{comp}|{run['BAR_RUN_ID']}"
    if span_index is not None:
        return f"{occ['occurrence_id']}|{comp}|SPAN{span_index}"
    return f"{occ['occurrence_id']}|{comp}"


def _row(occ, comp, state, *, kg=None, provenance=None, why=None, question_id=None, run=None, span_index=None,
         **fields):
    if state not in COMPONENT_STATES:
        raise SuperstructureBeamRebarError(f"{occ['occurrence_id']}/{comp}: unknown state {state}")
    rec = {"record_id": _record_id(occ, comp, run, span_index), "occurrence_id": occ["occurrence_id"],
           "subfamily": occ["subfamily"], "mark": occ["mark"], "component": comp,
           "accurate_component": ACCURATE_COMPONENT[comp], "quantity_kind": KIND[comp], "state": state, "kg": kg,
           "why": why, "question_id": question_id, "provenance": provenance,
           "bar_run_id": run["BAR_RUN_ID"] if run else None, "span_index": span_index,
           "cb_group_id": (occ.get("cb") or {}).get("CB_GROUP_ID")}
    rec.update(fields)
    return rec


def _run_fields(run):
    """Attribute fields a bar-run row always keeps (released or blocked): count / diameter are never dropped."""
    return {"bar_count": run.get("count"), "dia_mm": run.get("dia_mm"), "frame_role": run.get("frame_role"),
            "label": run.get("label"), "start_location": run.get("start_location"),
            "end_location": run.get("end_location"), "spans_crossed": list(run.get("spans_crossed") or []),
            "intermediate_supports": list(run.get("intermediate_supports") or []),
            "source_extent": run.get("source_extent"), "segments": list(run.get("segments") or []),
            "register_run_m": run.get("register_run_m"), "source_tokens": list(run.get("source_tokens") or [])}


def _blocked(ctx, occ, comp, reason, *, authority="UNRESOLVED", question_id=None, rule_id="S6-BLOCKED", run=None,
             span_index=None, **fields):
    if authority in AR.RELEASING_AUTHORITIES or authority in AR.PROVISIONAL_AUTHORITIES:
        authority = "UNRESOLVED"
    pv = _prov(ctx, occ, comp, state=AR.BLOCKED_UNQUANTIFIED, rule_id=rule_id, convention="NONE",
               measurement="NOT_MEASURED", authority=authority, formula="NONE (blocked)", inputs={}, run=run,
               span_index=span_index, BLOCKING_REASON=reason, **({"QUESTION_ID": question_id} if question_id else {}))
    if run is not None:
        fields = dict(_run_fields(run), **fields)
    return _row(occ, comp, AR.BLOCKED_UNQUANTIFIED, provenance=pv, why=reason, question_id=question_id, run=run,
                span_index=span_index, **fields)


def _not_applicable(ctx, occ, comp, reason, *, rule_id="S6-NOT-APPLICABLE", span_index=None):
    pv = _prov(ctx, occ, comp, state=NOT_APPLICABLE, rule_id=rule_id, convention="NONE", measurement="NOT_MEASURED",
               authority="SOURCE_EXPLICIT", formula="NONE (not applicable)", inputs={}, span_index=span_index,
               NOT_APPLICABLE_REASON=reason)
    return _row(occ, comp, NOT_APPLICABLE, provenance=pv, why=reason, span_index=span_index)


def _q(occ, topic):
    return (occ.get("questions") or {}).get(topic)


def occurrence_block(occ):
    """(reason, authority, question_id) shared by every schedule-dependent component, else (None, None, None)."""
    blocks = occ.get("blocks") or []
    if not blocks:
        return None, None, None
    auth = "SOURCE_CONFLICT" if any(b.get("authority") == "SOURCE_CONFLICT" for b in blocks) else "UNRESOLVED"
    qs = "+".join(dict.fromkeys(b["question_id"] for b in blocks if b.get("question_id")))
    return "; ".join(b["reason"] for b in blocks), auth, qs or None


def candidate_invariant(interpretations):
    """(state, value, why). state SAME | DIFFERENT | NONE. Every interpretation must give the same component, count,
    diameter and run rule; nothing is averaged and no interpretation is preferred."""
    if not interpretations:
        return "NONE", None, "no interpretation supplied"
    keys = {(i.get("component"), i.get("count"), i.get("dia_mm"), tuple(i.get("run_rule") or ()))
            for i in interpretations}
    if len(keys) == 1:
        return "SAME", keys.pop(), None
    return "DIFFERENT", None, "reading interpretations disagree: " + "; ".join(
        f"{i.get('name')}: {i.get('count')}Ø{i.get('dia_mm')} {i.get('component')} rule {list(i.get('run_rule') or [])}"
        for i in interpretations)


def _span_length(occ, span, basis):
    spans = (occ.get("cb") or {}).get("spans") or occ.get("geometry", {}).get("spans") or {}
    sp = spans.get(str(span))
    if not sp:
        return None
    return sp.get("cc_m") if basis == "AXIS_TO_AXIS" else sp.get("clear_m")


def straight_run(occ, run, rules, tol=1e-6):
    """Sum the source segments of one bar run. Returns {run_m, included, excluded, segment_state, missing}.
    Measured geometry is included as given; an extension only under a BOUND typical rule that applies to this bar
    role, at the rule's own value (re-computed from the drawing's span definition for a factor rule)."""
    comp = run["component"]
    inc, exc, missing = [], [], list(run.get("missing") or [])
    typ = rules.get("typical") or {}
    sym = rules.get("span_symbols") or {}
    for s in run.get("segments") or []:
        kind, L = s.get("kind") or "FACE_TO_FACE", s.get("length_m")
        if kind not in GEOMETRY_SEGMENTS + RULE_SEGMENTS:
            raise SuperstructureBeamRebarError(f"{run['BAR_RUN_ID']}: unknown segment kind {kind}")
        if L is None or L < 0:
            raise SuperstructureBeamRebarError(f"{run['BAR_RUN_ID']}: segment {kind} without a length")
        if s.get("state") != "VERIFIED":
            exc.append(s)
            missing.append(f"{kind} segment not verified ({s.get('state')})")
            continue
        if kind in GEOMETRY_SEGMENTS:
            if kind == "CLEAR_SPAN" and s.get("span") is not None:
                clear = _span_length(occ, s["span"], "FACE_TO_FACE")
                if clear is not None and abs(clear - L) > 1e-3:
                    raise SuperstructureBeamRebarError(f"{run['BAR_RUN_ID']}: clear span {L} != span {s['span']} "
                                                       f"face-to-face {clear}")
            inc.append(s)
            continue
        rid = s.get("rule_id")
        rule = typ.get(rid)
        if rule is None or rule.get("state") != "BOUND":
            exc.append(s)
            missing.append(f"{kind} extension: rule {rid} is {'not in the register' if rule is None else rule['state']}"
                           f"{' (' + rule['text'] + ')' if rule and rule.get('text') else ''} - adds no length")
            continue
        if comp not in (rule.get("applies_to") or ()):
            exc.append(s)
            missing.append(f"{kind} extension: rule {rid} ({rule.get('text')}) is bound to "
                           f"{rule.get('applies_to')}, not to {comp} - never generalised")
            continue
        if rule["kind"] == "FIXED_EXTENSION_M":
            if abs(rule["value"] - L) > tol:
                raise SuperstructureBeamRebarError(f"{run['BAR_RUN_ID']}: {kind} {L} m != rule {rid} {rule['value']} m")
        elif rule["kind"] == "FACTOR_OF_SPAN":
            basis = rule.get("span_basis") or sym.get(rule.get("symbol_class") or "Ln")
            if basis not in SPAN_BASES:
                raise SuperstructureBeamRebarError(f"{rid}: span basis {basis} not established")
            span_m = _span_length(occ, s.get("span"), basis)
            if span_m is None:
                exc.append(s)
                missing.append(f"{kind}: span {s.get('span')} {basis} length unknown")
                continue
            exp = rule["value"] * span_m
            if abs(exp - L) > 5e-4:
                raise SuperstructureBeamRebarError(
                    f"{run['BAR_RUN_ID']}: {kind} {L} m != {rule['value']} x {basis} span {s.get('span')} "
                    f"({span_m} m) = {exp:.4f} m")
            s = dict(s, factor=rule["value"], span_m=span_m, span_basis=basis)
        else:
            raise SuperstructureBeamRebarError(f"{rid}: unknown rule kind {rule['kind']}")
        inc.append(s)
    total = sum(s["length_m"] for s in inc)
    reg = run.get("register_run_m")
    if reg is not None and inc and abs(reg - total) > 1e-3:
        if exc and abs(reg - total - sum(s["length_m"] for s in exc)) <= 1e-3:
            missing.append(f"register run {reg} m counted unbound / unverified length; S6 counts {total:.4f} m")
        else:
            raise SuperstructureBeamRebarError(f"{run['BAR_RUN_ID']}: segments sum {total:.4f} != register run {reg}")
    has_geometry = any((s.get("kind") or "FACE_TO_FACE") in GEOMETRY_SEGMENTS for s in inc)
    if comp in ("MID_TOP", "MID_BOTTOM", "TOP_SUPPORT", "BOTTOM_SUPPORT"):
        complete_extent = bool(inc) and not exc and any(s.get("kind") in RULE_SEGMENTS for s in inc)
    else:
        complete_extent = bool(inc) and not exc and has_geometry
    return {"run_m": total if inc else None, "included": inc, "excluded": exc, "missing": missing,
            "segment_state": SEGMENT_SOURCE_VERIFIED if complete_extent else SEGMENT_LOWER_BOUND,
            "has_geometry": has_geometry, "complete_extent": complete_extent}


# ------------------------------------------------------------------------------------------------------ bar runs
def _bar_run(ctx, occ, run, rules, kgm_of, occ_blk):
    comp = run["component"]
    if comp not in BAR_RUN_COMPONENTS:
        raise SuperstructureBeamRebarError(f"{run['BAR_RUN_ID']}: {comp} is not a bar-run component")
    assert_no_load_tokens(run.get("source_tokens"), run["BAR_RUN_ID"])
    if occ_blk[0]:
        own = f"; this bar: {run['source_block']}" if run.get("source_block") else ""
        return _blocked(ctx, occ, comp, occ_blk[0] + own, authority=occ_blk[1], question_id=occ_blk[2],
                        rule_id="S6-OCCURRENCE-BLOCKED", run=run,
                        straight_run_known_geometry_m=run.get("register_run_m"))
    if comp == "HANGER":
        return _blocked(ctx, occ, comp, f"hanger: {rules['hanger']['why']}", question_id=_q(occ, "hanger"),
                        rule_id="S6-HANGER-BLOCKED", run=run)
    if run.get("source_block"):
        return _blocked(ctx, occ, comp, run["source_block"], authority=run.get("source_block_authority") or
                        "UNRESOLVED", question_id=run.get("question_id"), rule_id="S6-BAR-SOURCE-BLOCKED", run=run)
    if run.get("count") is None or run.get("dia_mm") is None:
        return _blocked(ctx, occ, comp, "count / diameter not source-established", question_id=run.get("question_id"),
                        rule_id="S6-BAR-COUNT-UNRESOLVED", run=run)
    reading = (occ.get("cb") or {}).get("READING_DIRECTION_STATE")
    basis = "SOURCE_BOUND"
    if reading == "AMBIGUOUS":
        st, val, why = candidate_invariant(run.get("interpretations"))
        if st != "SAME":
            return _blocked(ctx, occ, comp, "reading direction ambiguous: " + (why if st == "DIFFERENT" else
                            "no candidate-invariance evidence"), authority="SOURCE_CONFLICT" if st == "DIFFERENT"
                            else "UNRESOLVED", question_id=_q(occ, "reading_direction"),
                            rule_id="S6-CANDIDATE-DIFFERENT", run=run,
                            candidate_values=list(run.get("interpretations") or []))
        if (val[0], val[1], val[2]) != (comp, run["count"], run["dia_mm"]):
            raise SuperstructureBeamRebarError(f"{run['BAR_RUN_ID']}: invariant value {val} != bar run")
        basis = "CANDIDATE_INVARIANT"
    elif reading == "NONE":
        return _blocked(ctx, occ, comp, "span sequence not established (no reading direction)",
                        question_id=_q(occ, "sequence"), rule_id="S6-SEQUENCE-BLOCKED", run=run)
    sr = straight_run(occ, run, rules)
    if sr["run_m"] is None or sr["run_m"] <= 0 or (comp not in ("MID_TOP", "MID_BOTTOM") and not sr["has_geometry"]):
        return _blocked(ctx, occ, comp, "bar straight run not established: " + ("; ".join(sr["missing"]) or
                        "no source segment"), question_id=run.get("question_id"), rule_id="S6-BAR-RUN-UNRESOLVED",
                        run=run)
    if comp in ("MID_TOP", "MID_BOTTOM", "TOP_SUPPORT", "BOTTOM_SUPPORT") and not sr["complete_extent"]:
        return _blocked(ctx, occ, comp, "support-bar extent not established: " + "; ".join(sr["missing"]),
                        question_id=run.get("question_id"), rule_id="S6-SUPPORT-EXTENT-UNRESOLVED", run=run)
    authority = run.get("authority") or "UNRESOLVED"
    if authority not in AR.RELEASING_AUTHORITIES:
        return _blocked(ctx, occ, comp, f"bar-run authority {authority} cannot release steel",
                        authority=authority, rule_id="S6-AUTHORITY", run=run)
    n, dia, L = int(run["count"]), int(run["dia_mm"]), sr["run_m"]
    kgm = kgm_of(dia)
    total = n * L
    kg = total * kgm
    is_mid = comp in ("MID_TOP", "MID_BOTTOM")
    ends = ["in-span end treatment drawn straight on an N.T.S. typical, not dimensioned"] if is_mid else \
        ["DEVELOPMENT / ANCHORAGE at the end supports (not source-established)",
         "BAR-END HOOK / BEND at the end supports (not detailed)"]
    missing = list(dict.fromkeys(sr["missing"] + ends))
    rules_used = sorted({s["rule_id"] for s in sr["included"] if s.get("rule_id")})
    seg_txt = " + ".join(f"{s.get('kind') or 'FACE_TO_FACE'} {s['length_m']:.4f}" for s in sr["included"])
    formula = (f"n x STRAIGHT_RUN x D^2/162 = {n} x ({seg_txt} = {L:.4f} m) x {dia}^2/162 = {total:.4f} m x "
               f"{kgm:.6f} kg/m = {kg:.4f} kg")
    mid = None
    if is_mid:
        mid = {"factor": sorted({s["factor"] for s in sr["included"] if "factor" in s}),
               "span_basis": sorted({s["span_basis"] for s in sr["included"] if "span_basis" in s}),
               "spans": {str(s["span"]): {"Ln_m": s["span_m"], "extent_m": s["length_m"], "side": s["kind"]}
                         for s in sr["included"] if "span_m" in s},
               "support_face": "measured from the support face (INTO_SPAN segments start at the face)",
               "support_width_m": sum(s["length_m"] for s in sr["included"] if s.get("kind") == "THROUGH_SUPPORT"),
               "straight_extent_m": L}
    inputs = {"bar_count": n, "dia_mm": dia, "straight_run_m": L, "segments": sr["included"],
              "excluded_segments": sr["excluded"], "total_straight_length_m": total, "kg_per_m": kgm,
              "unit_mass": ctx["unit_mass"]["method"], "release_basis": basis, "rules": rules_used,
              "interpretations": run.get("interpretations") or [], "mid": mid,
              "not_used": "member centreline / schedule span / min(clear, c/c) / any development or hook default"}
    pv = _prov(ctx, occ, comp, state=AR.LOWER_BOUND, rule_id="+".join(rules_used) or run.get("run_rule_id") or
               "S6-MEASURED-SEGMENTS", convention=(run.get("convention_id") or "BAR_STRAIGHT_RUN_LOWER_BOUND") + "|" +
               ctx["unit_mass"]["method"], measurement="MEASURED", authority=authority, formula=formula,
               inputs=inputs, run=run, LOW=kg, BEST=kg, HIGH=None, UNQUANTIFIED_COMPONENTS=[], MISSING=missing,
               RELEASE_BASIS=basis, KNOWN_SOURCE_SEGMENT_STATE=sr["segment_state"],
               TEMPLATE_RULE_ID=run.get("run_rule_id") or "NONE",
               COMPLETE_BAR_STATE=COMPLETE_NOT_ESTABLISHED,
               **({"MID_STRAIGHT_RUN_STATE": sr["segment_state"], "MID_RULE": mid} if is_mid else {}))
    return _row(occ, comp, AR.LOWER_BOUND, kg=kg, provenance=pv, why="; ".join(missing), run=run,
                **dict(_run_fields(run), bar_count=n, dia_mm=dia, straight_run_m=L, total_length_m=total,
                       kg_per_m=kgm, release_basis=basis, known_source_segment_state=sr["segment_state"],
                       complete_bar_state=COMPLETE_NOT_ESTABLISHED, missing=missing, rules_used=rules_used, mid=mid,
                       mid_straight_run_state=sr["segment_state"] if is_mid else None))


# ------------------------------------------------------------------------------------------------------ stirrups
def _stirrups(ctx, occ, rules, occ_blk):
    out = []
    for st in occ.get("stirrups") or []:
        k = st["SPAN_INDEX"]
        attrs = {"dia_mm": st.get("dia_mm"), "rate_or_spacing": {"mode": st.get("mode"), "value": st.get("value")},
                 "distribution_m": st.get("distribution_m"), "legs": st.get("legs"), "hooks": st.get("hooks"),
                 "end_zone": st.get("end_zone"), "first_last": st.get("first_last"),
                 "source_tokens": list(st.get("source_tokens") or [])}
        assert_no_load_tokens(st.get("source_tokens"), f"{occ['occurrence_id']} stirrups span {k}")
        reason, auth, qid, rule = None, "UNRESOLVED", None, "S6-STIRRUP-COUNT-BLOCKED"
        if occ_blk[0]:
            reason, auth, qid, rule = occ_blk[0], occ_blk[1], occ_blk[2], "S6-OCCURRENCE-BLOCKED"
        elif st.get("source_block"):
            reason, qid = st["source_block"], st.get("question_id")
        elif (occ.get("cb") or {}).get("READING_DIRECTION_STATE") == "AMBIGUOUS":
            cs, _, why = candidate_invariant(st.get("interpretations"))
            if cs != "SAME":
                reason = "reading direction ambiguous: " + (why if cs == "DIFFERENT" else
                                                            "no candidate-invariance evidence")
                auth = "SOURCE_CONFLICT" if cs == "DIFFERENT" else "UNRESOLVED"
                qid, rule = _q(occ, "reading_direction"), "S6-CANDIDATE-DIFFERENT"
        if reason is None and (st.get("first_last") or {}).get("state") == "SOURCE_ESTABLISHED":
            raise SuperstructureBeamRebarError(f"{occ['occurrence_id']}: a source first/last stirrup rule needs the "
                                               "engine extended first (V1 adopts no end bar)")
        if reason is None and (st.get("dia_mm") is None or st.get("value") is None or not st.get("distribution_m")):
            reason, qid = "stirrup diameter / rate or clear distribution run not established", st.get("question_id")
        if reason is None and not st.get("source_tokens"):
            reason = "no rebar source token for this stirrup"
        if reason is not None:
            out.append(_blocked(ctx, occ, "STIRRUP_COUNT", reason, authority=auth, question_id=qid, rule_id=rule,
                                span_index=k, **attrs))
        else:
            rm = RM.bar_count(st["mode"], st["value"], st["distribution_m"],
                              basis=st.get("distribution_basis") or "")
            n = rm["verified"]
            if st.get("register_count") is not None and int(st["register_count"]) != n:
                raise SuperstructureBeamRebarError(f"{occ['occurrence_id']} span {k}: count {n} != register "
                                                   f"{st['register_count']}")
            basis = "CANDIDATE_INVARIANT" if (occ.get("cb") or {}).get("READING_DIRECTION_STATE") == "AMBIGUOUS" \
                else "SOURCE_BOUND"
            pv = _prov(ctx, occ, "STIRRUP_COUNT", state=AR.LOWER_BOUND, rule_id="S6-STIRRUP-COUNT-LB",
                       convention=rm["rule_id"] + " (verified lower bound only; +1 end bar NOT adopted)",
                       measurement="MEASURED", authority="SOURCE_DERIVED_HIGH_CONFIDENCE",
                       formula=f"n >= {rm['formula'].split(';')[0]}",
                       inputs={"mode": st["mode"], "value": st["value"], "distribution_m": st["distribution_m"],
                               "distribution_basis": st.get("distribution_basis"), "count_lower_bound": n,
                               "end_bar_convention_count_not_adopted": rm["convention"], "release_basis": basis},
                       span_index=k, handles=st.get("source_handles") or (),
                       schedule_handles=st.get("schedule_handles") or (),
                       geometry_handles=st.get("geometry_handles") or (), LOW=n, BEST=n, HIGH=None,
                       UNQUANTIFIED_COMPONENTS=[], RELEASE_BASIS=basis,
                       MISSING=["first / last stirrup position not stated (count is a lower bound)"])
            out.append(_row(occ, "STIRRUP_COUNT", AR.LOWER_BOUND, provenance=pv, count=n, span_index=k,
                            count_convention_not_adopted=rm["convention"], release_basis=basis,
                            why="first / last stirrup position not stated; no +1", **attrs))
        # stirrup mass: every facet must be source-supported - V1 never has all of them
        facets = list(st.get("core_path_missing") or [])
        if rules["stirrup_topology"]["state"] != "SOURCE_ESTABLISHED":
            facets.append(f"LEGS / LINK TOPOLOGY {rules['stirrup_topology']['state']}")
        if rules["stirrup_hooks"]["state"] != "SOURCE_ESTABLISHED":
            facets.append(f"STIRRUP HOOKS {rules['stirrup_hooks']['state']}")
        wm = occ["identity"].get("WIDTH_MATCH_STATE")
        if "SOURCE_CONFLICT" in (wm if isinstance(wm, list) else [wm]):
            facets.append("WIDTH SOURCE_CONFLICT")
        if occ_blk[0]:
            facets.append(f"occurrence blocked: {occ_blk[0]}")
        facets = list(dict.fromkeys(facets))
        if not facets:
            raise SuperstructureBeamRebarError(f"{occ['occurrence_id']}: every stirrup facet is source-supported - "
                                               "S6 V1 computes no stirrup mass; add the path rule first")
        out.append(_blocked(ctx, occ, "STIRRUP_CORE_PATH", "stirrup mass needs legs, path, hooks and section; missing: "
                            + "; ".join(facets), question_id=_q(occ, "stirrup_geometry"),
                            rule_id="S6-STIRRUP-MASS-BLOCKED", span_index=k, missing_facets=facets,
                            dia_mm=st.get("dia_mm"), stirrup_count_known=out[-1]["state"] == AR.LOWER_BOUND))
    return out


# --------------------------------------------------------------------------------------------- other components
def opening_activation(openings):
    """(active, checked). An opening activates the beam-opening detail only when it is a source-identified physical
    opening inside this beam (closed outline in the band); open slab-opening line work never does."""
    active = [o for o in openings or [] if o.get("state") == "PHYSICAL_BEAM_OPENING"]
    return active, len(openings or [])


def _openings(ctx, occ, rules):
    active, n = opening_activation(occ.get("openings"))
    out = []
    for c in OPENING_COMPONENTS:
        if active:
            out.append(_blocked(ctx, occ, c, "beam-opening detail ACTIVATED by " +
                                ", ".join(o["opening_id"] for o in active) + ": the opening reinforcement is not "
                                "quantified in S6 V1 (detail must be bound to the opening first)",
                                question_id=_q(occ, "opening"), rule_id="S6-OPENING-DETAIL-ACTIVATED",
                                activated_by=[o["opening_id"] for o in active]))
        else:
            out.append(_not_applicable(ctx, occ, c, "no source-identified physical opening in this beam "
                                       f"({rules.get('openings_checked', n)} opening objects checked project-wide; "
                                       "the generic opening detail is not applied globally)",
                                       rule_id="S6-NO-BEAM-OPENING"))
    return out


def _side(ctx, occ, rules, occ_blk):
    s = occ.get("side")
    if s is None or s.get("applicability") != "PRINTED":
        return _not_applicable(ctx, occ, "SIDE_REBAR", (s or {}).get("why") or "no side bars printed",
                               rule_id="S6-SIDE-NONE-PRINTED")
    if rules["side_bar_semantics"]["state"] != NOT_ESTABLISHED:
        raise SuperstructureBeamRebarError("side-bar semantics established: S6 V1 computes no side-bar kg; extend "
                                           "the engine with the approved arrangement first")
    reason = (f"side bars '{s.get('raw_text')}' printed ({s.get('count')}Ø{s.get('dia_mm')}"
              f"{'/' + str(s.get('spacing_cm')) + 'cm' if s.get('spacing_cm') else ''}): "
              f"{rules['side_bar_semantics']['why']} - quantity / mass not source-quantified")
    if occ_blk[0]:
        reason += f"; occurrence blocked: {occ_blk[0]}"
    return _blocked(ctx, occ, "SIDE_REBAR", reason, question_id=_q(occ, "side"), rule_id="S6-SIDE-SEMANTICS",
                    raw_text=s.get("raw_text"), bar_count=s.get("count"), dia_mm=s.get("dia_mm"),
                    spacing_cm=s.get("spacing_cm"), side_token_handles=list(s.get("token_handles") or []))


def _ends(ctx, occ, rules, occ_blk):
    out = []
    for i in (1, 2):
        node = occ["identity"].get("START_SUPPORT" if i == 1 else "END_SUPPORT")
        tail = f" at end {i} ({node})"
        if occ_blk[0]:
            tail += f"; occurrence blocked: {occ_blk[0]}"
        out.append(_blocked(ctx, occ, f"HOOK_{i}", f"bar-end hook / bend: {rules['bar_end_hooks']['why']}{tail}",
                            question_id=_q(occ, "development"), rule_id="S6-BAR-END-HOOK-BLOCKED", end=i))
        out.append(_blocked(ctx, occ, f"DEVELOPMENT_{i}", f"development / anchorage: {rules['development']['why']}"
                            f"{tail}", question_id=_q(occ, "development"), rule_id="S6-DEVELOPMENT-BLOCKED", end=i))
    return out


def _status_component(ctx, occ, comp, occ_blk):
    st = (occ.get("status") or {}).get(comp)
    if st is None:
        raise SuperstructureBeamRebarError(f"{occ['occurrence_id']}: {comp} has neither a bar run nor a status")
    if st["state"] == NOT_APPLICABLE:
        return _not_applicable(ctx, occ, comp, st["why"], rule_id=st.get("rule_id") or "S6-NOT-APPLICABLE")
    if st["state"] != "BLOCKED":
        raise SuperstructureBeamRebarError(f"{occ['occurrence_id']}: {comp} status {st['state']} must be "
                                           "NOT_APPLICABLE or BLOCKED (a quantity needs a bar run)")
    assert_no_load_tokens(st.get("source_tokens"), f"{occ['occurrence_id']}/{comp}")
    return _blocked(ctx, occ, comp, st["why"], authority=st.get("authority") or "UNRESOLVED",
                    question_id=st.get("question_id"), rule_id=st.get("rule_id") or "S6-COMPONENT-BLOCKED",
                    source_tokens=list(st.get("source_tokens") or []))


def _check_rules(rules):
    for k in ("development", "bar_end_hooks", "stirrup_hooks", "side_bar_semantics", "hanger"):
        if rules[k]["state"] != NOT_ESTABLISHED:
            raise SuperstructureBeamRebarError(f"rule {k} is {rules[k]['state']}: S6 V1 computes no {k}; a project / "
                                               "engineer method must be approved and the engine extended first")
    sym = rules.get("span_symbols") or {}
    if sym.get("authority") not in AR.RELEASING_AUTHORITIES:
        raise SuperstructureBeamRebarError("the drawing's own Ln / L definition must be source-established")


# ------------------------------------------------------------------------------------------------------ occurrence
def occurrence_rebar(occ, rules, ctx) -> dict:
    """All components of ONE physical simple beam or continuous-beam group."""
    sub = occ.get("subfamily")
    if sub not in SUBFAMILIES:
        raise SuperstructureBeamRebarError(f"{occ.get('occurrence_id')}: subfamily {sub!r} not in {SUBFAMILIES}")
    if occ.get("drawing_sha") != ctx["DRAWING_SHA"]:
        raise SuperstructureBeamRebarError(f"{occ['occurrence_id']}: drawing sha != run drawing")
    if (sub == CONTINUOUS_BEAM) != bool(occ.get("cb")):
        raise SuperstructureBeamRebarError(f"{occ['occurrence_id']}: CB identity iff CONTINUOUS_BEAM")
    if occ.get("cb") and occ["cb"]["READING_DIRECTION_STATE"] not in READING_STATES:
        raise SuperstructureBeamRebarError(f"{occ['occurrence_id']}: reading state not in {READING_STATES}")
    _check_rules(rules)
    UM.validate(ctx["unit_mass"])
    kgm_of = lambda dia: UM.kg_per_m(dia, ctx["unit_mass"])  # noqa: E731
    blk = occurrence_block(occ)
    runs = occ.get("bar_runs") or []
    ids = Counter(r["BAR_RUN_ID"] for r in runs)
    if any(v > 1 for v in ids.values()):
        raise SuperstructureBeamRebarError(f"{occ['occurrence_id']}: a bar run entered twice {ids}")
    out = []
    for comp in BAR_RUN_COMPONENTS:
        mine = [r for r in runs if r["component"] == comp]
        if mine and comp in (occ.get("status") or {}):
            raise SuperstructureBeamRebarError(f"{occ['occurrence_id']}: {comp} has bar runs and a status")
        if mine:
            out += [_bar_run(ctx, occ, r, rules, kgm_of, blk) for r in mine]
        elif comp == "HANGER":
            h = occ.get("hanger") or {}
            if h.get("state") == "ABSENT":
                out.append(_not_applicable(ctx, occ, comp, h.get("why") or "no hanger field and no hanger detail",
                                           rule_id="S6-HANGER-ABSENT"))
            else:
                out.append(_blocked(ctx, occ, comp, f"hanger {h.get('state')}: {h.get('why') or rules['hanger']['why']}"
                                    " - not inferred from practice", question_id=h.get("question_id"),
                                    rule_id="S6-HANGER-BLOCKED"))
        else:
            out.append(_status_component(ctx, occ, comp, blk))
    out.append(_side(ctx, occ, rules, blk))
    if not occ.get("stirrups"):
        raise SuperstructureBeamRebarError(f"{occ['occurrence_id']}: no stirrup record (one per span required)")
    out += _stirrups(ctx, occ, rules, blk)
    out += _ends(ctx, occ, rules, blk)
    out += _openings(ctx, occ, rules)
    out.append(_status_component(ctx, occ, "OTHER_EXPLICIT_EXTRA", blk))
    return _finish(occ, out, blk)


def _part(c):
    return {"part_id": c["record_id"], "category": CATEGORY, "component": c["accurate_component"],
            "state": c["state"], "kg": c["kg"],
            "basis": ["DRAWING_OCCURRENCE", "SCHEDULE", "STRUCTURAL_DETAIL", "DETERMINISTIC_GEOMETRY"],
            "provenance": c["provenance"]}


def _finish(occ, comps, blk):
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
            validate_part(p)
            parts.append(p)
    known = [c for c in comps if c["quantity_kind"] == MASS and c["kg"] is not None]
    if known and all(c["state"] == AR.VERIFIED for c in known) and not unq:
        occ_state = OCC_VERIFIED
    elif any(c["state"] in AR.RELEASED_STATES for c in known):
        occ_state = OCC_LOWER_BOUND
    else:
        occ_state = OCC_BLOCKED
    cnts = [c for c in comps if c["component"] == "STIRRUP_COUNT"]
    idn, cb = occ["identity"], occ.get("cb") or {}
    row = {"occurrence_id": occ["occurrence_id"], "subfamily": occ["subfamily"], "element_family": ELEMENT_FAMILY,
           "mark": occ["mark"], "sheet": occ.get("sheet"), "floor": occ.get("floor"),
           "occurrence_terminal": "S6_OCCURRENCE", "occurrence_state": occ_state,
           "known_kg": sum(c["kg"] for c in known),
           "known_straight_length_m": sum(c["total_length_m"] for c in known),
           "mid_known_kg": sum(c["kg"] for c in known if c["component"] in ("MID_TOP", "MID_BOTTOM")),
           "stirrup_count_lower_bound": sum(c["count"] for c in cnts if c["state"] == AR.LOWER_BOUND) or None,
           "stirrup_count_records_released": sum(1 for c in cnts if c["state"] == AR.LOWER_BOUND),
           "unquantified_components": unq, "occurrence_blocking_reason": blk[0] or "",
           "components_by_state": dict(sorted(Counter(c["state"] for c in comps).items())),
           "cb_group_id": cb.get("CB_GROUP_ID"), "span_sequence": cb.get("SPAN_SEQUENCE"),
           "reading_direction_state": cb.get("READING_DIRECTION_STATE"), "sequence_state": cb.get("SEQUENCE_STATE"),
           "geometry": occ.get("geometry"), "flags": list(occ.get("flags") or [])}
    for k in ("SOURCE_HANDLES", "GEOMETRY_HANDLES", "TAG_HANDLES", "SCHEDULE_HANDLES", "START_SUPPORT", "END_SUPPORT",
              "DRAWN_WIDTH_MM", "SCHEDULE_WIDTH_MM", "WIDTH_MATCH_STATE", "DETAIL_ID", "DETAIL_CANDIDATES",
              "SCHEDULE_ROW", "BINDING_STATE", "AUTHORITY_STATE", "GEOMETRY_OBJECTS"):
        row[k.lower()] = idn.get(k)
    return {"occurrence": row, "components": comps, "parts": parts}


def untagged_record(obj: dict) -> dict:
    """A beam geometry no tag binds: it stays visible with its known geometry, terminal GEOMETRY_WITHOUT_TAG and
    rebar BLOCKED_TYPE - a schedule row is never assigned from nearby marks."""
    return {"occurrence_id": obj["object_id"], "subfamily": "UNTAGGED_GEOMETRY", "element_family": ELEMENT_FAMILY,
            "mark": "", "sheet": obj.get("sheet"), "floor": obj.get("floor"),
            "occurrence_terminal": "GEOMETRY_WITHOUT_TAG", "occurrence_state": "BLOCKED_TYPE", "known_kg": None,
            "known_straight_length_m": None, "mid_known_kg": None, "stirrup_count_lower_bound": None,
            "stirrup_count_records_released": 0, "unquantified_components": ["ALL (type unknown)"],
            "occurrence_blocking_reason": "no tag binds this geometry: type, schedule row and reinforcement unknown "
                                          f"(never assigned from nearby marks); {obj.get('why') or ''}".rstrip("; "),
            "components_by_state": {}, "geometry": {k: obj.get(k) for k in ("object_kind", "length_m", "clear_m",
                                                                            "drawn_width_mm", "start_support",
                                                                            "end_support", "s1_source_id")},
            "flags": ["GEOMETRY_WITHOUT_TAG"], "geometry_objects": [obj["object_id"]]}


def bbs_lines(components) -> list:
    """Net BBS: one STRAIGHT line per quantified bar run (development, hooks, laps not included)."""
    out = []
    for c in components:
        if c["quantity_kind"] != MASS or c["kg"] is None:
            continue
        out.append({"bbs_id": c["record_id"], "occurrence_id": c["occurrence_id"], "subfamily": c["subfamily"],
                    "mark": c["mark"], "cb_group_id": c["cb_group_id"], "bar_run_id": c["bar_run_id"],
                    "component": c["component"], "state": c["state"], "release_basis": c["release_basis"],
                    "dia_mm": c["dia_mm"], "shape": "STRAIGHT (known source segment; ends not included)",
                    "bar_length_m": c["straight_run_m"], "count": c["bar_count"],
                    "total_length_m": c["total_length_m"], "kg_per_m": c["kg_per_m"], "net_bbs_kg": c["kg"],
                    "known_source_segment_state": c["known_source_segment_state"],
                    "complete_bar_state": c["complete_bar_state"], "development_included": False,
                    "hooks_included": False, "used_kg": None, "purchased_kg": None, "waste_kg": None,
                    "procurement": "NOT_COMPUTED (procurement layer not invoked)"})
    return out


def _family_summary(sub, occ_rows, comps):
    fc = [c for c in comps if c["subfamily"] == sub]
    fo = [r for r in occ_rows if r["subfamily"] == sub]
    by = defaultdict(float)
    for c in fc:
        if c["kg"] is not None:
            by[c["state"]] += c["kg"]
    mass_blocked = [c for c in fc if c["state"] == AR.BLOCKED_UNQUANTIFIED and c["quantity_kind"] == MASS]
    count_blocked = [c for c in fc if c["state"] == AR.BLOCKED_UNQUANTIFIED and c["quantity_kind"] == COUNT]
    final = not mass_blocked and not count_blocked and not by.get(AR.LOWER_BOUND) and not by.get(AR.PROVISIONAL) \
        and not by.get(AR.BLOCKED_MODELLED)
    cnt = [c for c in fc if c["component"] == "STIRRUP_COUNT"]
    q = [c for c in fc if c["kg"] is not None]
    return {"subfamily": sub, "occurrences": len(fo),
            "occurrences_by_state": dict(sorted(Counter(r["occurrence_state"] for r in fo).items())),
            "VERIFIED_KG": by.get(AR.VERIFIED, 0.0), "LOWER_BOUND_KNOWN_KG": by.get(AR.LOWER_BOUND, 0.0),
            "PROVISIONAL_KG": by.get(AR.PROVISIONAL, 0.0), "BLOCKED_MODELLED_KG": by.get(AR.BLOCKED_MODELLED, 0.0),
            "BLOCKED_UNQUANTIFIED_COMPONENTS": len(mass_blocked),
            "BLOCKED_UNQUANTIFIED_COUNT_RECORDS": len(count_blocked),
            "blocked_unquantified_by_component": dict(sorted(Counter(c["component"] for c in mass_blocked +
                                                                     count_blocked).items())),
            "released_by_component": dict(sorted(Counter(c["component"] for c in fc
                                                         if c["state"] in AR.RELEASED_STATES).items())),
            "kg_by_component": {k: sum(c["kg"] for c in q if c["component"] == k)
                                for k in sorted({c["component"] for c in q})},
            "MID_KNOWN_KG": sum(c["kg"] for c in q if c["component"] in ("MID_TOP", "MID_BOTTOM")),
            "known_straight_length_m": sum(c["total_length_m"] for c in q),
            "candidate_invariant_releases": sum(1 for c in fc if c.get("release_basis") == "CANDIDATE_INVARIANT"
                                                and c["state"] in AR.RELEASED_STATES),
            "stirrup_counts_quantified": sum(1 for c in cnt if c["state"] == AR.LOWER_BOUND),
            "stirrup_count_lower_bound_total": sum(c["count"] for c in cnt if c["state"] == AR.LOWER_BOUND),
            "stirrup_masses_quantified": sum(1 for c in fc if c["component"] == "STIRRUP_CORE_PATH"
                                             and c["kg"] is not None),
            "kg_by_diameter": {str(d): sum(c["kg"] for c in q if c["dia_mm"] == d)
                               for d in sorted({c["dia_mm"] for c in q})},
            "length_by_diameter_m": {str(d): sum(c["total_length_m"] for c in q if c["dia_mm"] == d)
                                     for d in sorted({c["dia_mm"] for c in q})},
            "final": "FINAL_ESTABLISHED" if final else "FINAL NOT ESTABLISHED"}


def run(occurrences, rules, ctx, untagged=()) -> dict:
    ids = Counter(o["occurrence_id"] for o in occurrences)
    dup = [k for k, n in ids.items() if n > 1]
    if dup:
        raise SuperstructureBeamRebarError(f"occurrence id entered twice: {dup}")
    res = [occurrence_rebar(o, rules, ctx) for o in sorted(occurrences, key=lambda z: z["occurrence_id"])]
    comps = [c for r in res for c in r["components"]]
    parts = [p for r in res for p in r["parts"]]
    occ_rows = [r["occurrence"] for r in res]
    ut_rows = [untagged_record(u) for u in sorted(untagged, key=lambda z: z["object_id"])]
    bbs = bbs_lines(comps)
    summ = AR.summarise(parts)
    fams = {f: _family_summary(f, occ_rows, comps) for f in SUBFAMILIES}
    known = sum(f["VERIFIED_KG"] + f["LOWER_BOUND_KNOWN_KG"] for f in fams.values())
    final = all(f["final"] == "FINAL_ESTABLISHED" for f in fams.values()) and not ut_rows
    cnt = [c for c in comps if c["component"] == "STIRRUP_COUNT" and c["state"] == AR.LOWER_BOUND]
    summary = {
        "policy": POLICY_ID, "headline": "KNOWN SOURCE-DERIVED SUPERSTRUCTURE BEAM REBAR",
        "known_source_derived_superstructure_beam_rebar_kg": known,
        "final_superstructure_beam_rebar": "FINAL SUPERSTRUCTURE BEAM REBAR ESTABLISHED" if final else
        "FINAL SUPERSTRUCTURE BEAM REBAR NOT ESTABLISHED",
        **{f"{f}_{k}": fams[f][k] for f in SUBFAMILIES for k in ("VERIFIED_KG", "LOWER_BOUND_KNOWN_KG",
                                                                 "PROVISIONAL_KG", "BLOCKED_MODELLED_KG",
                                                                 "BLOCKED_UNQUANTIFIED_COMPONENTS")},
        "MID_KNOWN_KG": sum(f["MID_KNOWN_KG"] for f in fams.values()),
        "STIRRUP_COUNT_KNOWN": {"records": len(cnt), "stirrups_lower_bound": sum(c["count"] for c in cnt)},
        "STIRRUP_MASS_KNOWN": {"records": sum(f["stirrup_masses_quantified"] for f in fams.values()), "kg": 0.0},
        "families": fams, "occurrences": len(occ_rows), "untagged_geometry": len(ut_rows),
        "components_by_state": dict(sorted(Counter(c["state"] for c in comps).items())),
        "accurate_summary": summ,
        "stamp": {k: ctx[k] for k in ("ENGINE_COMMIT", "REGISTER_VERSION", "DRAWING_SHA", "CALCULATION_ROUND")}}
    return {"occurrences": occ_rows, "untagged": ut_rows, "components": comps, "parts": parts, "bbs": bbs,
            "summary": summary, "conservation": conservation(occ_rows, comps, parts, bbs, summ, occurrences)}


def conservation(occ_rows, comps, parts, bbs, summ, occurrences=(), tol=1e-9) -> dict:
    """Independent checks; every one must be True."""
    by_occ = defaultdict(list)
    for c in comps:
        by_occ[c["occurrence_id"]].append(c)
    occ_len = all(abs(sum(c.get("total_length_m") or 0.0 for c in by_occ[r["occurrence_id"]] if c["kg"] is not None)
                      - r["known_straight_length_m"]) <= tol for r in occ_rows)
    occ_kg = all(abs(sum(c["kg"] for c in by_occ[r["occurrence_id"]] if c["kg"] is not None) - r["known_kg"]) <= tol
                 for r in occ_rows)
    proj_kg = sum(r["known_kg"] for r in occ_rows)
    part_kg = sum(p["kg"] for p in parts if p["kg"] is not None)
    bbs_kg = sum(b["net_bbs_kg"] for b in bbs)
    bbs_len = sum(b["total_length_m"] for b in bbs)
    every_comp = all(set(COMPONENTS) <= {c["component"] for c in by_occ[r["occurrence_id"]]} for r in occ_rows)
    rec_ids = [c["record_id"] for c in comps]
    run_ids = [c["bar_run_id"] for c in comps if c["bar_run_id"]]
    declared_runs = [r["BAR_RUN_ID"] for o in occurrences for r in o.get("bar_runs") or []]
    frames = Counter((o["occurrence_id"], (r.get("source_extent") or {}).get("frame_handle"))
                     for o in occurrences for r in o.get("bar_runs") or []
                     if (r.get("source_extent") or {}).get("frame_handle"))
    spans_ok = all(sorted(c["span_index"] for c in by_occ[o["occurrence_id"]] if c["component"] == k) ==
                   sorted(s["SPAN_INDEX"] for s in o.get("stirrups") or [])
                   for o in occurrences for k in STIRRUP_COMPONENTS)
    pop = Counter(c["state"] for c in comps)
    no_kg = all(c["kg"] is None for c in comps
                if c["state"] in (AR.BLOCKED_UNQUANTIFIED, NOT_APPLICABLE) or c["quantity_kind"] != MASS)
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
            validate_part(p)
    except (SuperstructureBeamRebarError, ValueError):
        prov_ok = False
    released_tokens = all(c["source_tokens"] and all(is_rebar_token(t) for t in c["source_tokens"])
                          for c in comps if c["state"] in AR.RELEASED_STATES)
    checks = {"component_length_equals_occurrence_known_length": occ_len,
              "component_kg_equals_occurrence_known_kg": occ_kg,
              "occurrence_kg_equals_project_known_kg": abs(proj_kg - part_kg) <= 1e-6,
              "bbs_net_kg_equals_known_parts_kg": abs(bbs_kg - part_kg) <= 1e-6,
              "bbs_length_equals_known_length": abs(bbs_len - sum(r["known_straight_length_m"] for r in occ_rows))
              <= 1e-6,
              "every_component_terminates_per_occurrence": every_comp,
              "component_records_unique": len(rec_ids) == len(set(rec_ids)),
              "bar_run_ids_unique_and_each_declared_run_terminates_once":
                  len(run_ids) == len(set(run_ids)) and sorted(run_ids) == sorted(declared_runs),
              "one_bar_run_per_source_frame_bar": all(v == 1 for v in frames.values()),
              "stirrup_records_one_per_span": spans_ok,
              "every_mass_component_is_one_accurate_part": parts_once,
              "population_reconciles": sum(pop.values()) == len(comps),
              "blocked_and_non_mass_components_carry_no_kg": no_kg,
              "accurate_summary_reconciles": summ_ok,
              "every_component_passes_the_contract": prov_ok,
              "every_released_quantity_traces_to_rebar_tokens": released_tokens,
              "no_verified_complete_bar": all(c["state"] != AR.VERIFIED and c.get("complete_bar_state") !=
                                              "VERIFIED_COMPLETE" for c in comps)}
    return {"checks": checks, "all_pass": all(checks.values()), "project_known_kg": proj_kg,
            "population_by_state": dict(sorted(pop.items())),
            "population_by_component_state": {k: dict(sorted(Counter(c["state"] for c in comps
                                                                     if c["component"] == k).items()))
                                              for k in sorted({c["component"] for c in comps})}}


def policy_record() -> dict:
    return {"policy_id": POLICY_ID, "element_family": ELEMENT_FAMILY, "subfamilies": list(SUBFAMILIES),
            "components": list(COMPONENTS), "accurate_component": ACCURATE_COMPONENT, "quantity_kind": KIND,
            "component_states": list(COMPONENT_STATES), "segment_kinds": {"geometry": list(GEOMETRY_SEGMENTS),
                                                                          "rule": list(RULE_SEGMENTS)},
            "rebar_field_families": list(REBAR_FIELD_FAMILIES), "load_grammars": list(LOAD_GRAMMARS),
            "rules": ["one record per physical occurrence; ELEMENT_FAMILY BEAM + ELEMENT_SUBFAMILY",
                      "a continuous bar is one BAR_RUN_ID; never split at a support",
                      "straight run = measured segments + extensions only under a BOUND rule bound to that bar role",
                      "MID extent = factor x span named by the drawing's own Ln / L definition (re-computed)",
                      "kg = count x straight run x D^2/162; known segment LOWER_BOUND, never VERIFIED_COMPLETE",
                      "ambiguous reading: release only CANDIDATE_INVARIANT components; differences blocked",
                      "development, hooks, hangers, side bars, stirrup mass BLOCKED_UNQUANTIFIED (no defaults)",
                      "stirrup count = ceil(rate x clear run) lower bound; no +1",
                      "a design load (T/M) or non-rebar token can never produce steel",
                      "beam-opening detail only where a physical opening is source-identified in the beam",
                      "blocked components stay listed and carry no kg", "net only; procurement not computed"]}
