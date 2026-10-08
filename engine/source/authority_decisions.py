"""AUTHORITY DECISIONS - owner authority rulings, provenance classes and facet-state errata (generic, stdlib only).

An authority decision says what a kind of evidence may establish. It is not a drawing note and not an engineer
answer. Every quantity-bearing fact keeps one provenance class:

  PROJECT_SOURCE               the issued plan set (text, schedule, dimension, drawn geometry)
  PROJECT_ENGINEER_CLAIM       a versioned statement confirmed by the project engineer / consultant
  OWNER_AUTHORITY_DECISION     the owner's ruling on what evidence may establish (this module's records)
  ENGINEERING_DERIVED          applicability logic derived from project geometry (never a length, count or kg)
  CLAUDE_ENGINEERING_ANALYSIS  analysis written by the assistant; never promoted, never a quantity basis
  CODE_OR_EXTERNAL             design-code / generic-practice values; QA only in the accurate product

Rules:
  * only PROJECT_SOURCE and PROJECT_ENGINEER_CLAIM may carry a length, count, diameter or kg;
  * ENGINEERING_DERIVED may decide applicability (which detail applies), never a quantity;
  * CLAUDE_ENGINEERING_ANALYSIS and CODE_OR_EXTERNAL are never promoted to project authority, and a confidence
    percentage never travels with a ruling;
  * a facet-state erratum changes a facet's authority state and carries 0 kg (kg changes are delta_correction
    errata).

Concentrated loads (generic): a beam that frames into a span between its supports, or a planted column on the span,
makes the span an ENGINEERING_DERIVED_CONCENTRATED_REACTION case. A detail whose title says 'without concentrated
load' then does not apply. Under each length basis only the details without that clause remain; a basis left with
none has NO_PROJECT_DETAIL_FOR_CONCENTRATED_LOAD.
"""

from __future__ import annotations

PROJECT_SOURCE = "PROJECT_SOURCE"
PROJECT_ENGINEER_CLAIM = "PROJECT_ENGINEER_CLAIM"
OWNER_AUTHORITY_DECISION = "OWNER_AUTHORITY_DECISION"
ENGINEERING_DERIVED = "ENGINEERING_DERIVED"
CLAUDE_ENGINEERING_ANALYSIS = "CLAUDE_ENGINEERING_ANALYSIS"
CODE_OR_EXTERNAL = "CODE_OR_EXTERNAL"
PROVENANCE_CLASSES = (PROJECT_SOURCE, PROJECT_ENGINEER_CLAIM, OWNER_AUTHORITY_DECISION, ENGINEERING_DERIVED,
                      CLAUDE_ENGINEERING_ANALYSIS, CODE_OR_EXTERNAL)
QUANTITY_AUTHORITIES = (PROJECT_SOURCE, PROJECT_ENGINEER_CLAIM)
APPLICABILITY_AUTHORITIES = QUANTITY_AUTHORITIES + (ENGINEERING_DERIVED,)
NEVER_PROMOTED = (CLAUDE_ENGINEERING_ANALYSIS, CODE_OR_EXTERNAL)

# facet authority states a ruling or an erratum may set
SOURCE_EXPLICIT = "SOURCE_EXPLICIT"
SOURCE_EXPLICIT_SHAPE_ONLY = "SOURCE_EXPLICIT_SHAPE_ONLY"
PROJECT_PATTERN_ONLY = "PROJECT_PATTERN_ONLY"
SOURCE_EXPECTED_NOT_LOCATED = "SOURCE_EXPECTED_NOT_LOCATED"
NOT_ESTABLISHED = "NOT_ESTABLISHED"
UNRESOLVED = "UNRESOLVED"
BLOCKED_UNQUANTIFIED = "BLOCKED_UNQUANTIFIED"
CANDIDATE_ONLY = "CANDIDATE_ONLY"
RETAINED_WHERE_SOURCE_ESTABLISHED = "RETAINED_WHERE_SOURCE_ESTABLISHED"
CONTEXT_RESTRICTED = "CONTEXT_RESTRICTED"
BOUND_ONLY = "BOUND_ONLY"
RATE_COUNT_ONLY = "RATE_COUNT_ONLY"
CLASSIFIED_SIDE_SKIN_REINFORCEMENT = "CLASSIFIED_SIDE_SKIN_REINFORCEMENT"
NOT_A_PROJECT_RULE = "NOT_A_PROJECT_RULE"
QA_ONLY = "QA_ONLY"
ENGINEERING_DERIVED_CONCENTRATED_REACTION = "ENGINEERING_DERIVED_CONCENTRATED_REACTION"
FACET_STATES = (SOURCE_EXPLICIT, SOURCE_EXPLICIT_SHAPE_ONLY, PROJECT_PATTERN_ONLY, SOURCE_EXPECTED_NOT_LOCATED,
                NOT_ESTABLISHED, UNRESOLVED, BLOCKED_UNQUANTIFIED, CANDIDATE_ONLY, RETAINED_WHERE_SOURCE_ESTABLISHED,
                CONTEXT_RESTRICTED, BOUND_ONLY, RATE_COUNT_ONLY, CLASSIFIED_SIDE_SKIN_REINFORCEMENT,
                NOT_A_PROJECT_RULE, QA_ONLY, ENGINEERING_DERIVED_CONCENTRATED_REACTION)

DECISION_RECORD = "OWNER_AUTHORITY_DECISION"
ANALYSIS_RECORD = "REJECTED_ANALYSIS_VALUE"
FACET_ERRATUM = "AUTHORITY_STATE_ERRATA"
NO_DETAIL_IF_LOADED = "NO_PROJECT_DETAIL_FOR_CONCENTRATED_LOAD"
REACTION_KINDS = ("BEAM_END_REACTION",)          # a beam framing into the span between its supports
PLANTED_KINDS = ("PLANTED_COLUMN_ON_SPAN",)
SOURCE_PRESENT = "CONCENTRATED_LOAD_PRESENT"     # a frozen PRESENT state rests on a drawn member / symbol / note


class AuthorityError(ValueError):
    pass


def _no_confidence(obj, where):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if "confidence" in str(k).lower() or "percent" in str(k).lower():
                raise AuthorityError(f"{where}: a confidence value never travels with an authority ruling")
            _no_confidence(v, where)
    elif isinstance(obj, (list, tuple)):
        for v in obj:
            _no_confidence(v, where)


# ------------------------------------------------------------------ provenance
def may_carry_quantity(provenance):
    return provenance in QUANTITY_AUTHORITIES


def may_decide_applicability(provenance):
    return provenance in APPLICABILITY_AUTHORITIES


def promote(record, to):
    """Return a copy of `record` under provenance `to`. Analysis and code values are never promoted."""
    src = record.get("PROVENANCE")
    if src not in PROVENANCE_CLASSES or to not in PROVENANCE_CLASSES:
        raise AuthorityError(f"unknown provenance {src!r} -> {to!r}")
    if src in NEVER_PROMOTED and to != src:
        raise AuthorityError(f"{src} is never promoted to {to}")
    if to == PROJECT_ENGINEER_CLAIM and src != PROJECT_ENGINEER_CLAIM:
        raise AuthorityError("only the project engineer creates a PROJECT_ENGINEER_CLAIM")
    return dict(record, PROVENANCE=to)


# ------------------------------------------------------------------ records
def decision(*, decision_id, topic, rulings, forbids=(), preserves=(), recorded, provenance=OWNER_AUTHORITY_DECISION,
             **extra):
    """One owner authority decision: {facet: state} rulings, what it forbids, what it preserves."""
    if provenance != OWNER_AUTHORITY_DECISION:
        raise AuthorityError(f"{decision_id}: an authority decision is an OWNER_AUTHORITY_DECISION")
    if not rulings:
        raise AuthorityError(f"{decision_id}: a decision rules on at least one facet")
    for facet, state in rulings.items():
        if state not in FACET_STATES:
            raise AuthorityError(f"{decision_id}: {facet} -> unknown state {state!r}")
    rec = {"RECORD_TYPE": DECISION_RECORD, "DECISION_ID": decision_id, "TOPIC": topic, "PROVENANCE": provenance,
           "RULINGS": dict(rulings), "FORBIDS": list(forbids), "PRESERVES": list(preserves), "RECORDED": recorded,
           "IS_ENGINEER_CLAIM": False, "IS_DRAWING_NOTE": False}
    rec.update(extra)
    _no_confidence(rec, decision_id)
    return rec


def analysis_value(*, value_id, topic, value, decision_id, provenance=CLAUDE_ENGINEERING_ANALYSIS, **extra):
    """A value proposed by analysis or code, recorded so it can be refused by name. It never carries a quantity."""
    if provenance not in NEVER_PROMOTED:
        raise AuthorityError(f"{value_id}: only analysis / code values are recorded here")
    rec = {"RECORD_TYPE": ANALYSIS_RECORD, "VALUE_ID": value_id, "TOPIC": topic, "VALUE": value,
           "PROVENANCE": provenance, "DECISION_ID": decision_id, "ALLOWED_USE": QA_ONLY, "PROMOTED": False,
           "QUANTITY_BASIS": False}
    rec.update(extra)
    _no_confidence(rec, value_id)
    return rec


def facet_erratum(*, errata_id, target_id, facet, old_state, new_state, decision_id, evidence, kg_effect=0.0,
                  **extra):
    """A 0 kg correction of one facet's authority state on a frozen record."""
    if new_state not in FACET_STATES:
        raise AuthorityError(f"{errata_id}: unknown state {new_state!r}")
    if str(old_state) == str(new_state):
        raise AuthorityError(f"{errata_id}: an erratum changes the state")
    if abs(float(kg_effect or 0.0)) > 1e-12:
        raise AuthorityError(f"{errata_id}: a facet erratum carries no kg (use a delta_correction erratum)")
    if not decision_id or not evidence:
        raise AuthorityError(f"{errata_id}: an erratum names its decision and evidence")
    rec = {"ERRATA_ID": errata_id, "RECORD_TYPE": FACET_ERRATUM, "TARGET_ID": target_id, "FACET": facet,
           "OLD_STATE": old_state, "NEW_STATE": new_state, "DECISION_ID": decision_id, "EVIDENCE": evidence,
           "KG_EFFECT": 0.0}
    rec.update(extra)
    return rec


# ------------------------------------------------------------------ concentrated reactions
def concentrated_reaction(evidence_kinds, frozen_state):
    """Load state of a span after the concentrated-reaction ruling.

    A frozen CONCENTRATED_LOAD_PRESENT stays (it rests on a drawn member or symbol). A beam end on the span between
    its supports, or a planted column on it, makes an ENGINEERING_DERIVED_CONCENTRATED_REACTION. A junction at a
    support, an unidentified symbol or a stair-bearing candidate change nothing."""
    kinds = set(evidence_kinds or ())
    if frozen_state == SOURCE_PRESENT:
        return {"STATE": SOURCE_PRESENT, "PROVENANCE": PROJECT_SOURCE, "CHANGED": False}
    hit = sorted(kinds & set(REACTION_KINDS + PLANTED_KINDS))
    if hit:
        return {"STATE": ENGINEERING_DERIVED_CONCENTRATED_REACTION, "PROVENANCE": ENGINEERING_DERIVED,
                "CHANGED": True, "KINDS": hit}
    return {"STATE": frozen_state, "PROVENANCE": PROJECT_SOURCE, "CHANGED": False}


def loaded_candidates(details_by_basis, clause_details, always=()):
    """Candidate details of a loaded span: per length basis drop the 'without concentrated load' details; a basis
    with none left gives NO_DETAIL_IF_LOADED. `always` (e.g. an unresolved exterior section) is added as is."""
    clause = set(clause_details)
    out = set(always)
    if not details_by_basis:
        raise AuthorityError("at least one length basis is needed")
    for basis in details_by_basis:
        keep = [d for d in basis if d not in clause]
        out |= set(keep) if keep else {NO_DETAIL_IF_LOADED}
    return sorted(out)


def release_survives(old_candidates, new_candidates):
    """A quantity released as invariant over `old_candidates` stays valid only if the new set is a subset of the old
    one and does not newly hold the no-detail case."""
    old, new = set(old_candidates), set(new_candidates)
    if NO_DETAIL_IF_LOADED in new and NO_DETAIL_IF_LOADED not in old:
        return False
    return new <= old


def policy_record():
    return {"provenance_classes": list(PROVENANCE_CLASSES), "quantity_authorities": list(QUANTITY_AUTHORITIES),
            "applicability_authorities": list(APPLICABILITY_AUTHORITIES), "never_promoted": list(NEVER_PROMOTED),
            "facet_states": list(FACET_STATES),
            "rules": ["only project source or a project-engineer claim carries a quantity",
                      "engineering-derived logic decides applicability, never a quantity",
                      "analysis and code values are never promoted; no confidence value travels with a ruling",
                      "a facet erratum carries 0 kg; kg changes are delta_correction errata",
                      "a loaded span keeps, per length basis, only the details without a 'without concentrated "
                      "load' clause"]}
