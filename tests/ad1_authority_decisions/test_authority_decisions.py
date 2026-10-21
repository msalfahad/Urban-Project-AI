"""Generic tests: engine.source.authority_decisions (provenance, owner decisions, facet errata, loaded spans).

Synthetic records and hand-built candidate sets only. No project number is used."""

import pytest

from engine.source import authority_decisions as AD

CLAUSE = ("D-LT5", "D-GT5")
NO = AD.NO_DETAIL_IF_LOADED


def _dec(**kw):
    base = dict(decision_id="X-1", topic="t", rulings={"HOOKS": AD.NOT_ESTABLISHED}, recorded="2026-01-01")
    base.update(kw)
    return AD.decision(**base)


# ------------------------------------------------------------------ provenance
def test_only_project_source_or_an_engineer_claim_carries_a_quantity():
    assert AD.may_carry_quantity(AD.PROJECT_SOURCE) and AD.may_carry_quantity(AD.PROJECT_ENGINEER_CLAIM)
    for p in (AD.OWNER_AUTHORITY_DECISION, AD.ENGINEERING_DERIVED, AD.CLAUDE_ENGINEERING_ANALYSIS, AD.CODE_OR_EXTERNAL):
        assert not AD.may_carry_quantity(p), p


def test_engineering_derivation_decides_applicability_only():
    assert AD.may_decide_applicability(AD.ENGINEERING_DERIVED)
    assert not AD.may_carry_quantity(AD.ENGINEERING_DERIVED)
    assert not AD.may_decide_applicability(AD.CLAUDE_ENGINEERING_ANALYSIS)
    assert not AD.may_decide_applicability(AD.CODE_OR_EXTERNAL)


def test_analysis_and_code_values_are_never_promoted():
    for src in (AD.CLAUDE_ENGINEERING_ANALYSIS, AD.CODE_OR_EXTERNAL):
        for to in (AD.PROJECT_SOURCE, AD.PROJECT_ENGINEER_CLAIM, AD.OWNER_AUTHORITY_DECISION, AD.ENGINEERING_DERIVED):
            with pytest.raises(AD.AuthorityError):
                AD.promote({"PROVENANCE": src, "VALUE": 1}, to)
    with pytest.raises(AD.AuthorityError):            # only the engineer creates an engineer claim
        AD.promote({"PROVENANCE": AD.OWNER_AUTHORITY_DECISION}, AD.PROJECT_ENGINEER_CLAIM)
    with pytest.raises(AD.AuthorityError):
        AD.promote({"PROVENANCE": "GUESS"}, AD.PROJECT_SOURCE)
    assert AD.promote({"PROVENANCE": AD.PROJECT_SOURCE}, AD.PROJECT_SOURCE)["PROVENANCE"] == AD.PROJECT_SOURCE


# ------------------------------------------------------------------ records
def test_a_decision_is_an_owner_ruling_not_an_engineer_claim_or_a_note():
    d = _dec(forbids=["x"], preserves=["y"])
    assert d["PROVENANCE"] == AD.OWNER_AUTHORITY_DECISION and d["RECORD_TYPE"] == AD.DECISION_RECORD
    assert d["IS_ENGINEER_CLAIM"] is False and d["IS_DRAWING_NOTE"] is False
    with pytest.raises(AD.AuthorityError):
        _dec(provenance=AD.PROJECT_ENGINEER_CLAIM)
    with pytest.raises(AD.AuthorityError):
        _dec(rulings={})
    with pytest.raises(AD.AuthorityError):
        _dec(rulings={"HOOKS": "PROBABLY"})


def test_no_confidence_value_travels_with_a_ruling():
    with pytest.raises(AD.AuthorityError):
        _dec(confidence=0.8)
    with pytest.raises(AD.AuthorityError):
        _dec(scope_notes={"HOOKS": {"confidence_pct": 70}})
    with pytest.raises(AD.AuthorityError):
        AD.analysis_value(value_id="V", topic="t", value="12Ø", decision_id="X-1", notes=[{"percent": 90}])


def test_rejected_analysis_values_are_qa_only():
    v = AD.analysis_value(value_id="V", topic="hook", value="20d", decision_id="X-1",
                          provenance=AD.CODE_OR_EXTERNAL)
    assert v["ALLOWED_USE"] == AD.QA_ONLY and v["PROMOTED"] is False and v["QUANTITY_BASIS"] is False
    with pytest.raises(AD.AuthorityError):
        AD.analysis_value(value_id="V", topic="t", value="x", decision_id="X-1", provenance=AD.PROJECT_SOURCE)


def test_a_facet_erratum_changes_state_and_carries_no_kg():
    e = AD.facet_erratum(errata_id="E1", target_id="T", facet="HOOKS", old_state="no hooks",
                         new_state=AD.NOT_ESTABLISHED, decision_id="X-1", evidence="ev")
    assert e["KG_EFFECT"] == 0.0 and e["RECORD_TYPE"] == AD.FACET_ERRATUM
    bad = [dict(kg_effect=1.5), dict(new_state="SOMETHING"), dict(old_state=AD.NOT_ESTABLISHED),
           dict(decision_id=""), dict(evidence="")]
    for b in bad:
        kw = dict(errata_id="E1", target_id="T", facet="HOOKS", old_state="no hooks", new_state=AD.NOT_ESTABLISHED,
                  decision_id="X-1", evidence="ev")
        kw.update(b)
        with pytest.raises(AD.AuthorityError):
            AD.facet_erratum(**kw)


# ------------------------------------------------------------------ concentrated reactions
def test_a_beam_framing_in_between_supports_is_an_engineering_derived_reaction():
    r = AD.concentrated_reaction({"BEAM_END_REACTION"}, "UNKNOWN")
    assert r == {"STATE": AD.ENGINEERING_DERIVED_CONCENTRATED_REACTION, "PROVENANCE": AD.ENGINEERING_DERIVED,
                 "CHANGED": True, "KINDS": ["BEAM_END_REACTION"]}
    p = AD.concentrated_reaction({"PLANTED_COLUMN_ON_SPAN"}, "NO_CONCENTRATED_LOAD_EVIDENCE")
    assert p["STATE"] == AD.ENGINEERING_DERIVED_CONCENTRATED_REACTION
    mixed = AD.concentrated_reaction({"BEAM_END_REACTION", "UNIDENTIFIED_SYMBOL"}, "UNKNOWN")
    assert mixed["STATE"] == AD.ENGINEERING_DERIVED_CONCENTRATED_REACTION


def test_support_junctions_symbols_and_drawn_loads_are_not_reclassified():
    for kinds, frozen in (({"JUNCTION_AT_SUPPORT"}, "NO_CONCENTRATED_LOAD_EVIDENCE"),
                          ({"UNIDENTIFIED_SYMBOL"}, "UNKNOWN"), ({"STAIR_BEARING_CANDIDATE"}, "UNKNOWN"),
                          (set(), "NO_CONCENTRATED_LOAD_EVIDENCE")):
        r = AD.concentrated_reaction(kinds, frozen)
        assert r["STATE"] == frozen and r["CHANGED"] is False
    src = AD.concentrated_reaction({"BEAM_END_REACTION"}, AD.SOURCE_PRESENT)
    assert src["STATE"] == AD.SOURCE_PRESENT and src["PROVENANCE"] == AD.PROJECT_SOURCE


def test_loaded_candidates_are_taken_per_length_basis():
    # basis 1 says <2.5 m and <5 m, basis 2 says <5 m only: loaded, basis 2 has no detail
    assert AD.loaded_candidates([["D-LT25", "D-LT5"], ["D-LT5"]], CLAUSE) == ["D-LT25", NO]
    # nested on every basis: the loaded span keeps the unclaused <2.5 m section only
    assert AD.loaded_candidates([["D-LT25", "D-LT5"]] * 3, CLAUSE) == ["D-LT25"]
    # only clause details on every basis
    assert AD.loaded_candidates([["D-GT5"], ["D-GT5"]], CLAUSE) == [NO]
    # an unresolved exterior section stays a candidate
    assert AD.loaded_candidates([["D-LT5"]], CLAUSE, always=["D-EXT"]) == ["D-EXT", NO]
    with pytest.raises(AD.AuthorityError):
        AD.loaded_candidates([], CLAUSE)


def test_a_release_survives_only_on_a_narrower_detail_set_without_the_no_detail_case():
    assert AD.release_survives(["D-LT25", "D-LT5"], ["D-LT25"])
    assert not AD.release_survives(["D-LT25", "D-LT5"], ["D-LT25", NO])
    assert AD.release_survives([NO, "D-LT5"], [NO])                  # nothing released there anyway
    assert not AD.release_survives(["D-LT5"], ["D-LT25"])            # a new detail is not covered by the old release


def test_policy_record():
    p = AD.policy_record()
    assert set(p["never_promoted"]) == {AD.CLAUDE_ENGINEERING_ANALYSIS, AD.CODE_OR_EXTERNAL}
    assert set(p["quantity_authorities"]) == {AD.PROJECT_SOURCE, AD.PROJECT_ENGINEER_CLAIM}
