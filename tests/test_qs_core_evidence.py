"""A claim has a life, not just a rank.

R5 resolved every window height from an owner input that the project had explicitly retired for exactly that
case.  Rank alone cannot see that: an owner input outranks a standard for ever, so a resolver that asks only
"who is most senior" keeps choosing a value that was taken back.  Eligibility has to be decided first.

These tests are about the mechanism.  No project height appears in them, and none should: a test that asserts a
particular millimetre figure passes just as well when the mechanism is wrong and the constant is right.
"""

from __future__ import annotations

from engine.qs_core import evidence as EV

TOL = 0.001
WINDOW_NO_SOURCE = {"OBJECT_KIND": "WINDOW", "HAS_SOURCE_HEIGHT": False}


def retired_owner_value_and_active_standard():
    """An owner input, retired for one scope by a standard that covers that scope."""
    owner = EV.Claim(9.0, EV.OWNER_PROJECT_INPUT, "OWNER-1")
    standard = EV.Claim(3.0, EV.APPROVED_GUIDE, "STANDARD::A", scope={"OBJECT_KIND": "WINDOW"})
    return EV.supersede([owner, standard], "OWNER-1", by="STANDARD::A",
                        reason="the owner retired this value for windows with no source height",
                        scope={"HAS_SOURCE_HEIGHT": False})


def test_a_superseded_claim_cannot_resolve_a_dimension_however_senior_it_is():
    rec = EV.resolve("height", retired_owner_value_and_active_standard(), TOL, subject=WINDOW_NO_SOURCE)
    assert rec["STATUS"] == EV.ESTABLISHED
    assert rec["SOURCE"] == EV.APPROVED_GUIDE
    assert EV.rank_of(EV.OWNER_PROJECT_INPUT) < EV.rank_of(EV.APPROVED_GUIDE), "the loser did outrank the winner"


def test_the_winning_record_says_why_each_passed_over_claim_could_not_answer():
    rec = EV.resolve("height", retired_owner_value_and_active_standard(), TOL, subject=WINDOW_NO_SOURCE)
    reasons = {d["REFERENCE"]: d["INELIGIBLE_BECAUSE"] for d in rec["INELIGIBLE"]}
    assert reasons["OWNER-1"] == EV.SUPERSEDED_OUT
    assert all(d["WHY"] for d in rec["INELIGIBLE"])


def test_supersession_is_scoped_and_the_same_claim_still_answers_elsewhere():
    claims = retired_owner_value_and_active_standard()
    inside = EV.resolve("height", claims, TOL, subject=WINDOW_NO_SOURCE)
    outside = EV.resolve("height", claims, TOL,
                         subject={"OBJECT_KIND": "DOOR", "HAS_SOURCE_HEIGHT": True})
    assert inside["SOURCE"] == EV.APPROVED_GUIDE
    assert outside["SOURCE"] == EV.OWNER_PROJECT_INPUT
    assert outside["VALUE"] == 9.0, "the retirement was for one scope, not for the claim"


def test_a_withdrawn_claim_never_answers_anywhere():
    claims = [EV.Claim(9.0, EV.OWNER_PROJECT_INPUT, "OWNER-1", status=EV.WITHDRAWN),
              EV.Claim(3.0, EV.APPROVED_GUIDE, "STANDARD::A")]
    for subject in (WINDOW_NO_SOURCE, {"OBJECT_KIND": "DOOR"}, None):
        rec = EV.resolve("height", claims, TOL, subject=subject)
        assert rec["SOURCE"] == EV.APPROVED_GUIDE, subject


def test_a_claim_out_of_scope_is_not_consulted_even_when_it_is_the_only_one():
    claims = [EV.Claim(3.0, EV.APPROVED_GUIDE, "STANDARD::WINDOWS", scope={"OBJECT_KIND": "WINDOW"})]
    rec = EV.resolve("height", claims, TOL, subject={"OBJECT_KIND": "DOOR"})
    assert rec["STATUS"] == EV.NOT_ESTABLISHED and rec["VALUE"] is None
    assert rec["INELIGIBLE"][0]["INELIGIBLE_BECAUSE"] == EV.INELIGIBLE_SCOPE


def test_a_subject_that_does_not_state_a_scoped_key_does_not_silently_match():
    claims = [EV.Claim(3.0, EV.APPROVED_GUIDE, "STANDARD::A", scope={"HAS_SOURCE_HEIGHT": False})]
    rec = EV.resolve("height", claims, TOL, subject={"OBJECT_KIND": "WINDOW"})
    assert rec["STATUS"] == EV.NOT_ESTABLISHED
    assert "does not state" in rec["INELIGIBLE"][0]["WHY"]


def test_a_conditional_claim_answers_only_while_its_condition_is_established():
    claims = [EV.Claim(3.0, EV.OWNER_PROJECT_INPUT, "OWNER-2", status=EV.CONDITIONAL,
                       condition="the roof slab is cast at this level")]
    assert EV.resolve("height", claims, TOL)["STATUS"] == EV.NOT_ESTABLISHED
    held = EV.resolve("height", claims, TOL, conditions_met=("the roof slab is cast at this level",))
    assert held["STATUS"] == EV.ESTABLISHED and held["VALUE"] == 3.0


def test_a_claim_that_is_not_yet_effective_does_not_answer_an_earlier_revision():
    claims = [EV.Claim(3.0, EV.OWNER_PROJECT_INPUT, "OWNER-3", effective_from="2026-01-01"),
              EV.Claim(4.0, EV.APPROVED_GUIDE, "STANDARD::A")]
    early = EV.resolve("height", claims, TOL, revision="2025-06-01")
    assert early["SOURCE"] == EV.APPROVED_GUIDE
    late = EV.resolve("height", claims, TOL, revision="2026-06-01")
    assert late["SOURCE"] == EV.OWNER_PROJECT_INPUT


def test_nothing_is_deleted_so_a_reader_can_see_what_was_retired():
    rec = EV.resolve("height", retired_owner_value_and_active_standard(), TOL, subject=WINDOW_NO_SOURCE)
    refs = {c["REFERENCE"] for c in rec["CONSIDERED"]}
    assert "OWNER-1" in refs
    retired = next(c for c in rec["CONSIDERED"] if c["REFERENCE"] == "OWNER-1")
    assert retired["STATUS"] == EV.SUPERSEDED and retired["SUPERSEDED_BY"] and retired["SUPERSEDED_REASON"]


def test_the_mutation_that_ignores_lifecycle_picks_the_retired_value():
    """The R5 resolver, re-implemented: rank only.  It must come to the answer the review objected to."""
    claims = retired_owner_value_and_active_standard()

    def rank_only(claims_):
        usable = [c for c in claims_ if c.value is not None]
        best = min(EV.rank_of(c.source) for c in usable)
        return sorted((c for c in usable if EV.rank_of(c.source) == best), key=lambda c: c.value)[0]

    assert rank_only(claims).reference.startswith("OWNER-1")
    honest = EV.resolve("height", claims, TOL, subject=WINDOW_NO_SOURCE)
    assert honest["REFERENCE"] != rank_only(claims).reference


def test_two_eligible_claims_of_equal_authority_that_disagree_are_a_question():
    claims = [EV.Claim(3.0, EV.DRAWING_DIMENSION, "DIM-A"), EV.Claim(4.0, EV.DRAWING_DIMENSION, "DIM-B")]
    rec = EV.resolve("height", claims, TOL)
    assert rec["STATUS"] == EV.CONFLICTED and rec["VALUE"] is None and len(rec["CONFLICTS"]) == 2


def test_every_lifecycle_state_is_reachable_and_named_in_the_record():
    rec = EV.resolve("height", retired_owner_value_and_active_standard(), TOL, subject=WINDOW_NO_SOURCE)
    assert set(rec["LIFECYCLE"]) == {EV.ACTIVE, EV.SUPERSEDED, EV.WITHDRAWN, EV.CONDITIONAL}
