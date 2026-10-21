"""PROJECT CLAIM STORE (generic schema; the claims themselves are project data).

A human / consultant answer is stored as a claim bound to ONE project, ONE drawing revision and an explicit member
scope. It never edits a source fact: it either ASSERTS a value the sources do not give, or ADJUDICATES a recorded
flag / conflict. A claim never transfers to another project or revision, and it is born PROJECT_ONLY (see
rule_promotion for the only way a lesson becomes generic).

Stdlib only.
"""

from __future__ import annotations

import copy

from . import engineering_flags as EF

POLICY_ID = "PROJECT_CLAIM_V1"
ASSERTION = "ASSERTION"
ADJUDICATION = "ADJUDICATION"
KINDS = (ASSERTION, ADJUDICATION)
FIELDS = ("project_id", "claim_id", "kind", "element_filter", "flag_keys", "fact", "value", "source_person",
          "source_office", "date", "drawing_revision", "supersedes", "evidence_attachment", "scope_note",
          "promotion_state")

APPLIES = "APPLIES"
PROJECT_MISMATCH = "PROJECT_MISMATCH"
REVISION_MISMATCH = "REVISION_MISMATCH"
SCOPE_MISMATCH = "SCOPE_MISMATCH"
FACT_MISMATCH = "FACT_MISMATCH"
SUPERSEDED_CLAIM = "SUPERSEDED_CLAIM"


def make_claim(*, project_id, claim_id, kind, fact, value, source_person, date, drawing_revision, source_office=None,
               element_filter=None, flag_keys=(), supersedes=None, evidence_attachment=None, scope_note=None):
    if kind not in KINDS:
        raise ValueError(f"kind {kind}")
    if not (project_id and drawing_revision and source_person and date):
        raise ValueError("a claim needs project, drawing revision, person and date")
    if kind == ADJUDICATION and not flag_keys:
        raise ValueError("an adjudication names the flag(s) it answers")
    if kind == ASSERTION and not element_filter:
        raise ValueError("an assertion names its member scope")
    return {"project_id": project_id, "claim_id": claim_id, "kind": kind, "element_filter": element_filter or {},
            "flag_keys": list(flag_keys), "fact": fact, "value": value, "source_person": source_person,
            "source_office": source_office, "date": date, "drawing_revision": drawing_revision,
            "supersedes": supersedes, "evidence_attachment": evidence_attachment, "scope_note": scope_note,
            "promotion_state": "PROJECT_ONLY"}   # never anything else at birth


def active(claims):
    """Drop claims superseded by a later claim of the same project."""
    gone = {(c["project_id"], c["supersedes"]) for c in claims if c.get("supersedes")}
    return [c for c in claims if (c["project_id"], c["claim_id"]) not in gone]


def _match_filter(flt, element):
    for k, v in (flt or {}).items():
        allowed = v if isinstance(v, (list, tuple, set)) else [v]
        if element.get(k) not in allowed:
            return False
    return True


def applicability(claim, *, project_id, drawing_revision, element=None, fact=None, flag_key=None, claims=None):
    if claims is not None and claim not in active(claims):
        return SUPERSEDED_CLAIM
    if claim["project_id"] != project_id:
        return PROJECT_MISMATCH
    if claim["drawing_revision"] != drawing_revision:
        return REVISION_MISMATCH
    if fact is not None and claim["fact"] != fact:
        return FACT_MISMATCH
    if claim["kind"] == ADJUDICATION:
        return APPLIES if flag_key in claim["flag_keys"] else SCOPE_MISMATCH
    return APPLIES if element is not None and _match_filter(claim["element_filter"], element) else SCOPE_MISMATCH


def apply_to_flags(flags, claims, *, project_id, drawing_revision, at=None):
    """Adjudications for this project + revision move their flags to RESOLVED (history kept). Returns (flags, log)."""
    live = [c for c in active(claims)]
    out, log = [], []
    for f in flags:
        hit = [c for c in live if c["kind"] == ADJUDICATION and applicability(
            c, project_id=project_id, drawing_revision=drawing_revision, flag_key=f["flag_key"]) == APPLIES]
        refused = [(c["claim_id"], applicability(c, project_id=project_id, drawing_revision=drawing_revision,
                                                 flag_key=f["flag_key"]))
                   for c in claims if c["kind"] == ADJUDICATION and f["flag_key"] in c["flag_keys"] and c not in hit]
        for cid, why in refused:
            log.append({"flag_key": f["flag_key"], "claim_id": cid, "result": why})
        if len(hit) == 1 and EF.is_open(f):
            c = hit[0]
            f2 = f
            if f2["status"] != EF.ANSWERED:
                f2 = EF.transition(f2, EF.ANSWERED, by=c["source_person"], at=c["date"], note=c["claim_id"],
                                   resolution=c["value"], resolution_source=c["claim_id"])
            f2 = EF.transition(f2, EF.RESOLVED, by=c["source_person"], at=at or c["date"], note=c["claim_id"],
                               resolution=c["value"], resolution_source=c["claim_id"])
            out.append(f2)
            log.append({"flag_key": f["flag_key"], "claim_id": c["claim_id"], "result": "RESOLVED"})
        elif len(hit) > 1:
            out.append(copy.deepcopy(f))
            log.append({"flag_key": f["flag_key"], "claim_ids": [c["claim_id"] for c in hit],
                        "result": "CONFLICTING_CLAIMS_NOT_APPLIED"})
        else:
            out.append(f)
    return out, log


def schema():
    return {"schema": "PROJECT_CLAIM_SCHEMA", "policy_id": POLICY_ID, "fields": list(FIELDS), "kinds": list(KINDS),
            "applicability_results": [APPLIES, PROJECT_MISMATCH, REVISION_MISMATCH, SCOPE_MISMATCH, FACT_MISMATCH,
                                      SUPERSEDED_CLAIM],
            "rules": ["bound to project_id + drawing_revision + member scope (element_filter or flag_keys)",
                      "never transferred to another project or revision",
                      "ASSERTION fills a fact the sources do not give (authority PROJECT_HUMAN_CLAIM)",
                      "ADJUDICATION answers named flags; the conflicting sources stay on record",
                      "superseded claims stay stored but stop applying",
                      "promotion_state is PROJECT_ONLY at birth; only rule_promotion can change the lesson's state",
                      "two live adjudications for one flag are not applied (CONFLICTING_CLAIMS_NOT_APPLIED)"]}
