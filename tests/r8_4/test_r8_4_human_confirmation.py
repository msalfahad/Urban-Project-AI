"""R8.4 §2-§7, §33 — URBAN_FRAME_RELEASE_V2: authoritative, INFORMED project confirmation.

Candidate evidence never raises authority; a confirmation is a versioned claim; two active claims that
disagree conflict; supersession retires, never erases. Synthetic only: no project unit is asserted."""

from __future__ import annotations

from engine.source import findings as F
from engine.source import frame as FR

SHA = "d" * 64
SPACE = "MS"


def decl(code):
    return list(FR.declaration_evidence(code, SPACE, SHA)[0])


def claim(cid="HC1", v=1000.0, sha=SHA, role="PROJECT_OWNER", scope=None, supersedes=None, ack=(), author="owner",
          ts="2026-10-01T09:00:00Z", producer=FR.HUMAN):
    return FR.human_confirmation(cid, sha, SPACE, v, author, role, ts, scope=scope, supersedes=supersedes,
                                 acknowledges=ack, producer=producer)


def plot(v=1000.0):
    return FR.UnitEvidence("PLOT", FR.NATIVE_UNIT, FR.KNOWN_PLOT_DIMENSION, SPACE, ("AUTHORED:PLOT_CERT",), v,
                           source_sha256=SHA, producer=FR.HUMAN)


def family(values, eid="FAM"):
    return FR.UnitEvidence(eid, FR.NATIVE_UNIT, FR.DIMENSION_STYLE, SPACE,
                           ("AUTHORED:DIMSTYLE:1", "ASSUMPTION:DISPLAY_IN_STANDARD_UNIT"), None,
                           derived_set=tuple(values), source_sha256=SHA, review_status=FR.CANDIDATE)


def uc(ev, ins=6, policy=None):
    return FR.unit_context(SHA, SPACE, FR.MODEL_SPACE, ev, insunits=ins, policy=policy or FR.RELEASE_V2)


def final(u):
    return FR.FINAL_MEASUREMENT in u.allowed_use


INCH = f"{SPACE}:INSUNITS:LIBREDWG"


def test_default_policy_is_v2_and_v1_is_reproducible():
    assert FR.DEFAULT_POLICY.policy_id == "URBAN_FRAME_RELEASE_V2"
    assert FR.RELEASE_V1.policy_id == "URBAN_FRAME_RELEASE_V1"


def test_A_exact_source_confirmation_agreeing_with_the_declaration():
    u = uc(decl(6) + [claim()])
    assert u.status == FR.CONFIRMED_BY_HUMAN and final(u)
    assert u.machine_status == FR.UNCONFIRMED and u.machine_support == "DECLARATION_ONLY"


def test_B_wrong_source_confirmation_is_inadmissible():
    u = uc(decl(6) + [claim(sha="e" * 64)])
    assert u.status == FR.UNCONFIRMED and ("HC1", "HUMAN_CONFIRMATION_SOURCE_MISMATCH") in u.excluded_evidence


def test_C_two_conflicting_active_confirmations_conflict():
    u = uc(decl(6) + [claim("HC1", 1000.0), claim("HC2", 10.0, author="architect", role="PROJECT_ARCHITECT")])
    assert u.status == FR.CONFLICT and not final(u)
    assert F.HUMAN_CONFIRMATION_CONFLICT in {f.code for f in u.findings}
    assert u.confirmation["active"] == ["HC1", "HC2"]


def test_D_a_later_confirmation_supersedes_never_erases():
    u = uc(decl(5) + [claim("HC1", 1000.0, ack=(f"{SPACE}:INSUNITS:LIBREDWG",)),
                      claim("HC2", 10.0, supersedes="HC1", ts="2026-10-02T09:00:00Z")], ins=5)
    assert u.status == FR.CONFIRMED_BY_HUMAN and u.native_to_mm == 10.0 and final(u)
    assert u.confirmation["superseded"] == ["HC1"] and len(u.confirmation["claims"]) == 2    # history kept


def test_D2_supersession_of_an_unknown_claim_is_flagged_for_review():
    u = uc(decl(6) + [claim("HC2", 1000.0, supersedes="HC_MISSING")])
    assert u.confirmation["supersession_target_unknown"] == ["HC2"]
    assert F.HUMAN_CONFIRMATION_REVIEW_REQUIRED in {f.code for f in u.findings}


def test_E_candidate_agreement_is_never_positive_corroboration():
    """INSUNITS inch; an assumption-bearing family set that CONTAINS metre; a human says metre. V1 let the
    set count as agreement (FINAL). V2: the set is ignored as support; the confirmation must name the
    contradicted declaration explicitly before it can stand."""
    ev = decl(1) + [family((100.0, 1000.0, 1e5, 2540.0, 30480.0)), claim(v=1000.0)]
    u = uc(ev, ins=1)
    assert u.status == FR.CONFIRMED_BY_HUMAN and not final(u)
    assert u.machine_support != "AGREEING_PHYSICAL_EVIDENCE"
    assert F.HUMAN_CONFIRMATION_REVIEW_REQUIRED in {f.code for f in u.findings}
    v1 = uc(ev, ins=1, policy=FR.RELEASE_V1)            # the V1 defect, reproducible for audit
    assert final(v1)
    informed = uc(decl(1) + [family((100.0, 1000.0)), claim(v=1000.0, ack=(INCH,))], ins=1)
    assert final(informed) and informed.machine_support == "HUMAN_AUTHORITY_ONLY"


def test_F_candidate_contradicting_the_human_needs_explicit_acknowledgement():
    ev = decl(6) + [family((25.4, 254.0), "FAMX"), claim(v=1000.0)]
    u = uc(ev)
    assert u.status == FR.CONFIRMED_BY_HUMAN and not final(u)
    assert u.human_basis == "UNACKNOWLEDGED_CONTRADICTION:FAMX"                  # deterministic, names it
    assert final(uc(decl(6) + [family((25.4, 254.0), "FAMX"), claim(v=1000.0, ack=("FAMX",))]))


def test_G_admitted_physical_evidence_contradicting_the_human_blocks_final():
    u = uc(decl(6) + [plot(1.0), claim(v=1000.0, ack=("PLOT",))])
    assert u.status == FR.CONFLICT and not final(u)            # admitted evidence cannot be acknowledged away


def test_H_human_matching_the_declaration_only():
    u = uc(decl(6) + [claim()])
    assert final(u) and u.machine_support == "DECLARATION_ONLY"
    assert not final(uc(decl(6) + [claim()], policy=FR.RELEASE_V2_H2))      # option H2 needs corroboration


def test_I_human_matching_admitted_independent_physical_evidence():
    u = uc(decl(6) + [plot(1000.0), claim()])
    assert u.status == FR.CONFIRMED_BY_HUMAN and final(u) and u.machine_support == "AGREEING_PHYSICAL_EVIDENCE"
    assert final(uc(decl(6) + [plot(1000.0), claim()], policy=FR.RELEASE_V2_H2))


def test_J_agent_generated_human_record_is_rejected():
    u = uc(decl(6) + [claim(producer=FR.AGENT)])
    assert u.status == FR.UNCONFIRMED and ("HC1", "AGENT_GENERATED_HUMAN_RECORD") in u.excluded_evidence
    assert F.AGENT_STATUS_ESCALATION_REJECTED in {f.code for f in u.findings}


def test_K_missing_author_role_or_timestamp_is_rejected():
    for kw in ({"role": None}, {"author": None}, {"ts": None}):
        u = uc(decl(6) + [claim(**kw)])
        assert u.status == FR.UNCONFIRMED and ("HC1", "HUMAN_CONFIRMATION_INCOMPLETE") in u.excluded_evidence, kw
    u = uc(decl(6) + [claim(role="SITE_VISITOR")])
    assert ("HC1", "HUMAN_ROLE_NOT_AUTHORISED") in u.excluded_evidence


def test_L_confirmation_whose_scope_does_not_cover_the_space_is_inadmissible():
    u = uc(decl(6) + [claim(scope=("LAYOUT1",))])
    assert u.status == FR.UNCONFIRMED and ("HC1", "HUMAN_CONFIRMATION_SCOPE_MISMATCH") in u.excluded_evidence


def test_candidates_never_raise_in_any_v2_path():
    """Exhaustive: adding an AGREEING candidate to any fixture never turns a non-FINAL frame FINAL."""
    agree = family((1000.0,), "AGREE")
    fixtures = [decl(6), decl(1), decl(6) + [claim(ack=())], decl(1) + [claim()], [claim()],
                decl(6) + [plot(1000.0)], []]
    for ev in fixtures:
        base, plus = uc(ev), uc(ev + [agree])
        assert not (final(plus) and not final(base)), [e.evidence_id for e in ev]
        assert FR.STRENGTH[plus.status] <= FR.STRENGTH[base.status], [e.evidence_id for e in ev]
