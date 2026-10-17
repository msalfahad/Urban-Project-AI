"""GENERIC-RULE PROMOTION (generic).

A project answer never becomes a global rule by itself. The lesson behind it can be proposed as a GENERIC_CANDIDATE
- written as a project-free statement with the claims it came from - and only an explicit review by someone other
than the proposer makes it GENERIC_APPROVED. Engine code consumes GENERIC_APPROVED rules only.

    PROJECT_ONLY  ->  GENERIC_CANDIDATE  ->  GENERIC_APPROVED
                                       \\->  REJECTED (stays on record)
Stdlib only.
"""

from __future__ import annotations

import copy
import hashlib

POLICY_ID = "RULE_PROMOTION_V1"
PROJECT_ONLY = "PROJECT_ONLY"
GENERIC_CANDIDATE = "GENERIC_CANDIDATE"
GENERIC_APPROVED = "GENERIC_APPROVED"
REJECTED = "REJECTED"
STATES = (PROJECT_ONLY, GENERIC_CANDIDATE, GENERIC_APPROVED, REJECTED)


def propose(*, statement, condition, consequence, source_claims, proposer, at, forbidden_terms=()):
    """A candidate is a project-free statement. `forbidden_terms` (e.g. the project's member marks, ids, names) must
    not appear in it - the caller passes them from the project data, the engine never knows them."""
    if not source_claims:
        raise ValueError("a candidate cites the project claim(s) it generalises")
    text = " ".join([statement, condition, consequence]).lower()
    leaked = sorted(t for t in forbidden_terms if t and str(t).lower() in text)
    if leaked:
        raise ValueError(f"candidate statement still contains project-specific terms: {leaked}")
    rid = "RULE-" + hashlib.sha256(statement.encode()).hexdigest()[:10]
    return {"rule_id": rid, "statement": statement, "condition": condition, "consequence": consequence,
            "source_claims": [{"project_id": c["project_id"], "claim_id": c["claim_id"]} for c in source_claims],
            "projects": sorted({c["project_id"] for c in source_claims}), "state": GENERIC_CANDIDATE,
            "history": [{"to": GENERIC_CANDIDATE, "by": proposer, "at": at}], "proposer": proposer}


def review(candidate, *, reviewer, at, approve, note):
    if candidate["state"] != GENERIC_CANDIDATE:
        raise ValueError(f"only a GENERIC_CANDIDATE can be reviewed (is {candidate['state']})")
    if reviewer == candidate["proposer"]:
        raise ValueError("the proposer cannot approve their own candidate")
    if not note:
        raise ValueError("a review needs a written note")
    c = copy.deepcopy(candidate)
    c["state"] = GENERIC_APPROVED if approve else REJECTED
    c["history"].append({"to": c["state"], "by": reviewer, "at": at, "note": note})
    return c


def approved(registry):
    """The only rules generic engine code may consume."""
    return [r for r in registry if r["state"] == GENERIC_APPROVED]


def schema():
    return {"schema": "RULE_PROMOTION_SCHEMA", "policy_id": POLICY_ID, "states": list(STATES),
            "fields": ["rule_id", "statement", "condition", "consequence", "source_claims", "projects", "state",
                       "history", "proposer"],
            "rules": ["every project claim is PROJECT_ONLY; nothing is promoted automatically",
                      "a GENERIC_CANDIDATE is a project-free statement citing its source claims",
                      "project terms (marks, ids, names) are rejected from the candidate text",
                      "GENERIC_APPROVED needs a written review by someone other than the proposer",
                      "engine code consumes GENERIC_APPROVED rules only; rejected candidates stay on record"]}
