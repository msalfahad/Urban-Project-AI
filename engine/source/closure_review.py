"""CLOSURE HUMAN REVIEW (R8.20) - a human review is versioned evidence for ONE exact closure record.

A review record {closure, packet_digest, decision, reviewer_role, ...} satisfies the HUMAN_REVIEW condition of
CLOSURE_RELEASE_MODEL_V1 only when:
  * the reviewer is a human role (PROJECT_OWNER / QS_REVIEWER) - never the engine, Claude or a script;
  * the decision is ACCEPT;
  * its packet digest equals the digest of the CURRENT closure record (geometry / evidence) - a changed closure voids it;
  * it names this closure (a review never transfers to another closure).
A review changes authority / review state only: never geometry, topology, quantity or trade.

Project-agnostic; stdlib only.
"""

from __future__ import annotations

import hashlib
import json

POLICY_ID = "CLOSURE_HUMAN_REVIEW_POLICY_V1"
HUMAN_ROLES = ("PROJECT_OWNER", "QS_REVIEWER")
ACCEPT, REJECT = "ACCEPT", "REJECT"
ACCEPTED, REJECTED, STALE, NOT_HUMAN, WRONG_CLOSURE, ABSENT = (
    "ACCEPTED", "REJECTED", "STALE_DIGEST", "NOT_A_HUMAN_REVIEW", "REVIEW_OF_ANOTHER_CLOSURE", "ABSENT")


def record_digest(record: dict) -> str:
    return hashlib.sha256(json.dumps(record, sort_keys=True, default=str).encode()).hexdigest()


def review_state(review: dict | None, *, closure: str, current_digest: str) -> dict:
    if not review:
        return {"state": ABSENT, "satisfies_human_review": None}
    if review.get("reviewer_role") not in HUMAN_ROLES:
        st = NOT_HUMAN
    elif review.get("closure") != closure:
        st = WRONG_CLOSURE
    elif review.get("packet_digest") != current_digest:
        st = STALE
    elif review.get("decision") == ACCEPT:
        st = ACCEPTED
    elif review.get("decision") == REJECT:
        st = REJECTED
    else:
        st = NOT_HUMAN
    return {"state": st, "satisfies_human_review": True if st == ACCEPTED else (False if st == REJECTED else None),
            "review": review.get("review_id"), "decision": review.get("decision")}


def policy_record() -> dict:
    rec = {"policy_id": POLICY_ID, "human_roles": list(HUMAN_ROLES),
           "satisfies": "decision ACCEPT by a human role, bound to the CURRENT closure record digest, for this closure",
           "effect": "HUMAN_REVIEW condition only (authority / review state)",
           "never": ["self-approval by the engine / Claude / a script", "a review transferred to another closure",
                     "a review surviving a changed closure record", "a geometry, topology, quantity or trade change",
                     "a release"]}
    rec["digest"] = hashlib.sha256(json.dumps(rec, sort_keys=True).encode()).hexdigest()
    return rec
