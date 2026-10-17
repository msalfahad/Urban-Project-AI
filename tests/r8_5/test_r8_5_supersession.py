"""R8.5 §7-§9 — human-claim supersession needs clear correction authority (URBAN_FRAME_RELEASE_V3).

A later authorised claim no longer retires another person's claim just by naming it. Effective only when:
the same author corrects their own claim (A), or the supersession is ACCEPTED by the target's author or a
named project correction authority (B/C), who is not the proposer. No role hierarchy. Nothing is erased."""

from __future__ import annotations

import dataclasses

from engine.source import findings as F
from engine.source import frame as FR

SHA = "a" * 64
SPACE = "MS"


def decl(code=4):
    return list(FR.declaration_evidence(code, SPACE, SHA)[0])


def claim(cid, value, author="ALICE", role="PROJECT_ARCHITECT", sha=SHA, scope=(SPACE,), **kw):
    return FR.human_confirmation(cid, sha, SPACE, value, author, role, "2026-10-01T09:00Z", scope=scope,
                                 acknowledges=("MS:INSUNITS:LIBREDWG",), **kw)


def uc(ev, policy=None):
    return FR.unit_context(SHA, SPACE, FR.MODEL_SPACE, ev, insunits=4, policy=policy or FR.RELEASE_V3)


def sup(u):
    return u.confirmation["supersessions"]


def codes(u):
    return {f.code for f in u.findings}


def test_default_is_v3_and_v2_by_name_is_reproducible():
    assert FR.DEFAULT_POLICY.policy_id == "URBAN_FRAME_RELEASE_V3"
    a, b = claim("C1", 1.0, "ALICE"), claim("C2", 10.0, "BOB", supersedes="C1")
    assert uc(decl() + [a, b], FR.RELEASE_V2).confirmation["superseded"] == ["C1"]       # R8.4 behaviour kept
    assert uc(decl() + [a, b]).confirmation["superseded"] == []                          # V3: not effective


def test_same_author_corrects_own_claim():
    u = uc(decl() + [claim("C1", 1.0), claim("C2", 10.0, supersedes="C1", notes="drawn in cm")])
    assert u.confirmation["superseded"] == ["C1"] and sup(u)[0]["outcome"] == "ACCEPTED_SAME_AUTHOR"
    assert u.status == FR.CONFIRMED_BY_HUMAN and u.native_to_mm == 10.0
    assert {c["evidence_id"] for c in u.confirmation["claims"]} == {"C1", "C2"}            # never erased


def test_different_author_without_authorisation_is_pending_and_conflicts():
    u = uc(decl() + [claim("C1", 1.0), claim("C2", 10.0, "BOB", "PROJECT_ENGINEER", supersedes="C1")])
    assert sup(u)[0]["outcome"] == "PENDING_REVIEW" and not sup(u)[0]["effective"]
    assert u.status == FR.CONFLICT and F.HUMAN_CONFIRMATION_CONFLICT in codes(u)
    assert F.HUMAN_SUPERSESSION_NOT_EFFECTIVE in codes(u)


def test_accepted_reviewed_supersession_by_target_author():
    c2 = claim("C2", 10.0, "BOB", "PROJECT_ENGINEER", supersedes="C1", supersession_status="ACCEPTED",
               supersession_authorized_by="ALICE", supersession_authorizer_role="PROJECT_ARCHITECT",
               supersession_timestamp="2026-10-02T10:00Z", supersession_reason="unit read from the title block")
    u = uc(decl() + [claim("C1", 1.0), c2])
    assert sup(u)[0]["outcome"] == "ACCEPTED_BY_TARGET_AUTHOR" and u.confirmation["superseded"] == ["C1"]
    assert u.status == FR.CONFIRMED_BY_HUMAN


def test_accepted_by_project_correction_authority_only_if_named():
    kw = dict(supersedes="C1", supersession_status="ACCEPTED", supersession_authorized_by="CAROL",
              supersession_authorizer_role="URBAN_QS_LEAD", supersession_timestamp="t", supersession_reason="r")
    ev = decl() + [claim("C1", 1.0), claim("C2", 10.0, "BOB", "PROJECT_ENGINEER", **kw)]
    assert sup(uc(ev))[0]["outcome"] == "REVIEWER_WITHOUT_CORRECTION_AUTHORITY"            # a role alone is not authority
    named = dataclasses.replace(FR.RELEASE_V3, correction_authorities=("CAROL",))
    assert sup(uc(ev, named))[0]["outcome"] == "ACCEPTED_BY_PROJECT_CORRECTION_AUTHORITY"


def test_rejected_supersession_keeps_both_claims_in_conflict():
    c2 = claim("C2", 10.0, "BOB", "PROJECT_ENGINEER", supersedes="C1", supersession_status="REJECTED",
               supersession_authorized_by="ALICE", supersession_authorizer_role="PROJECT_ARCHITECT",
               supersession_timestamp="t", supersession_reason="unit is mm")
    u = uc(decl() + [claim("C1", 1.0), c2])
    assert sup(u)[0]["outcome"] == "REJECTED" and u.status == FR.CONFLICT


def test_self_review_and_incomplete_acceptance_are_not_effective():
    base = dict(supersedes="C1", supersession_status="ACCEPTED", supersession_authorizer_role="PROJECT_ENGINEER",
                supersession_timestamp="t", supersession_reason="r")
    u = uc(decl() + [claim("C1", 1.0), claim("C2", 10.0, "BOB", "PROJECT_ENGINEER", supersession_authorized_by="BOB", **base)])
    assert sup(u)[0]["outcome"] == "SELF_REVIEW_NOT_ALLOWED"
    b2 = dict(base, supersession_reason="")
    u = uc(decl() + [claim("C1", 1.0), claim("C2", 10.0, "BOB", "PROJECT_ENGINEER", supersession_authorized_by="ALICE", **b2)])
    assert sup(u)[0]["outcome"] == "ACCEPTANCE_INCOMPLETE"


def test_supersession_target_missing():
    u = uc(decl() + [claim("C2", 10.0, supersedes="C-NOPE")])
    assert sup(u)[0]["outcome"] == "TARGET_MISSING" and F.HUMAN_CONFIRMATION_REVIEW_REQUIRED in codes(u)


def test_supersession_target_outside_scope():
    far = claim("C1", 1.0, scope=("OTHER_SPACE",))
    u = uc(decl() + [far, claim("C2", 10.0, supersedes="C1")])
    assert sup(u)[0]["outcome"] == "TARGET_OUTSIDE_SCOPE"


def test_supersession_target_for_another_source_hash():
    u = uc(decl() + [claim("C1", 1.0, sha="e" * 64), claim("C2", 10.0, supersedes="C1")])
    assert sup(u)[0]["outcome"] == "TARGET_OTHER_SOURCE" and not sup(u)[0]["effective"]


def test_two_active_claims_conflict_until_supersession_accepted():
    pending = claim("C2", 10.0, "BOB", "PROJECT_ENGINEER", supersedes="C1", supersession_status="PROPOSED")
    assert uc(decl() + [claim("C1", 1.0), pending]).status == FR.CONFLICT
    accepted = dataclasses.replace(pending, supersession_status="ACCEPTED", supersession_authorized_by="ALICE",
                                   supersession_authorizer_role="PROJECT_ARCHITECT", supersession_timestamp="t",
                                   supersession_reason="r")
    assert uc(decl() + [claim("C1", 1.0), accepted]).status == FR.CONFIRMED_BY_HUMAN


def test_no_role_hierarchy_exists():
    for role in FR.AUTHORISED_ROLES:
        c2 = claim("C2", 10.0, "BOB", role, supersedes="C1")
        assert not sup(uc(decl() + [claim("C1", 1.0, role="PROJECT_ENGINEER"), c2]))[0]["effective"]
