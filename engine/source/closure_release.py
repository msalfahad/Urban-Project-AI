"""REVIEWED CLOSURE RELEASE MODEL (R8.13) - the levels above AUTHORISED_FOR_SHADOW. Design + evaluator only: this
module never releases anything and no caller may treat its top level as a release.

Levels (each requires every condition of the levels below it):
  CANDIDATE                       topology_closures derived a zero-material closure
  DIAGNOSTIC_PASS                 the closure's safety test passes
  AUTHORISED_FOR_SHADOW           cap corroboration + safety (topology_closures)
  REVIEWED_FOR_RELEASE_CANDIDATE  + POLICY_FROZEN            the closure and wall-band policies are the frozen ones
                                  + CROSS_ROUTE_AGREEMENT    an independent decode route gives the same closure
                                                             geometry (within eps_r)
                                  + OWNER_OR_SOURCE_CORROBORATION  an owner physical fact AGREES, or a source
                                                             document corroborates the wall end
                                  + SOURCE_ANCHOR            the measured source is anchored to the contract source
                                  + HUMAN_REVIEW             a signed review record names the closure and its digest
A missing condition is reported by name; nothing is inferred.

Project-agnostic; stdlib only.
"""

from __future__ import annotations

import hashlib
import json

POLICY_ID = "CLOSURE_RELEASE_MODEL_V1"
CANDIDATE, DIAGNOSTIC_PASS = "CANDIDATE", "DIAGNOSTIC_PASS"
AUTHORISED_FOR_SHADOW = "AUTHORISED_FOR_SHADOW"
REVIEWED = "REVIEWED_FOR_RELEASE_CANDIDATE"
LEVELS = (CANDIDATE, DIAGNOSTIC_PASS, AUTHORISED_FOR_SHADOW, REVIEWED)
CONDITIONS = ("POLICY_FROZEN", "CROSS_ROUTE_AGREEMENT", "OWNER_OR_SOURCE_CORROBORATION", "SOURCE_ANCHOR",
              "HUMAN_REVIEW")


def evaluate(closure_release: str, evidence: dict) -> dict:
    """closure_release: the topology_closures release; evidence: {condition: True / False / None (not available)}.
    Returns the highest level reached and every missing condition."""
    base = LEVELS.index(closure_release) if closure_release in LEVELS[:3] else -1
    missing = [c for c in CONDITIONS if evidence.get(c) is not True]
    level = REVIEWED if base == 2 and not missing else (LEVELS[base] if base >= 0 else None)
    return {"level": level, "missing_for_reviewed": missing if base == 2 else ["AUTHORISED_FOR_SHADOW"] + missing,
            "evidence": {c: evidence.get(c) for c in CONDITIONS}, "releases_anything": False}


def policy_record() -> dict:
    rec = {"policy_id": POLICY_ID, "levels": list(LEVELS), "reviewed_requires": list(CONDITIONS),
           "never": ["a release", "a level inferred from a missing condition", "an owner fact as topology "
                     "authority", "a review record without the closure digest"]}
    rec["digest"] = hashlib.sha256(json.dumps(rec, sort_keys=True).encode()).hexdigest()
    return rec
