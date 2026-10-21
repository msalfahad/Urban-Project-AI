"""A benchmark may not anchor an interpretation — enforced, not remembered.

The failure this guards against happened in this project: a
reconciliation document ranked a reading first BECAUSE its arithmetic
landed on the human total. The reading may well be right; the reason was
not a reason.
"""

from __future__ import annotations

import pytest

from engine import benchmark_protection as bp


def test_a_blind_pass_is_refused_the_answer_under_any_name():
    for payload in (
            {"human_excel_area_m2": 137.5},
            {"expected_area": 137.5},
            {"room": {"target_dimension_mm": 8950}},
            {"note": "the benchmark says 137.5"},
            {"qiyal_total": 137.5},
            {"deep": {"nested": {"known_total_m2": 137.5}}}):
        with pytest.raises(bp.BenchmarkLeak):
            bp.assert_blind(payload)


def test_renaming_the_field_does_not_smuggle_it_in():
    with pytest.raises(bp.BenchmarkLeak):
        bp.assert_blind({"should_be_m2": 137.5})
    with pytest.raises(bp.BenchmarkLeak):
        bp.assert_blind({"correct_area": 137.5})


def test_geometry_passes_through_untouched():
    payload = {"width_mm": 3150.0, "height_mm": 8950.0,
               "arc": {"radius_m": 4.2, "segment_height_m": 0.76}}
    bp.assert_blind(payload)
    out = bp.withhold(payload)
    assert out["payload"] == payload and out["withheld"] == []


def test_withholding_removes_the_benchmark_and_keeps_the_drawing():
    payload = {"width_mm": 3150.0, "human_excel_area_m2": 137.5,
               "rooms": [{"id": "SALON", "expected_m2": 41.9}]}
    out = bp.withhold(payload)
    assert "human_excel_area_m2" not in out["payload"]
    assert "expected_m2" not in out["payload"]["rooms"][0]
    assert out["payload"]["width_mm"] == 3150.0
    assert out["withheld"]


def test_a_reconciliation_pass_may_see_it_and_says_so():
    payload = {"human_excel_area_m2": 137.5}
    out = bp.withhold(payload, phase=bp.RECONCILIATION)
    assert out["phase"] == bp.RECONCILIATION
    assert out["payload"] == payload


# ------------------------------------------------- the freeze comes first

def test_reconciliation_needs_a_frozen_candidate():
    assert not bp.may_reconcile(None)
    assert not bp.may_reconcile({})
    frozen = bp.freeze({"SALON_m2": 41.9477})
    assert bp.may_reconcile(frozen)
    assert frozen["CANDIDATE_GEOMETRY_HASH"]


def test_the_freeze_moves_when_the_candidate_does():
    a = bp.freeze({"SALON_m2": 41.9477})
    b = bp.freeze({"SALON_m2": 41.9478})
    assert a["CANDIDATE_GEOMETRY_HASH"] != b["CANDIDATE_GEOMETRY_HASH"]


# --------------------------------------- closeness is not evidence

def test_closeness_may_not_confirm_a_hypothesis():
    h = bp.Hypothesis(hypothesis_id="H1", name="the segment fraction")
    with pytest.raises(bp.BenchmarkLeak):
        bp.confirm(h, evidence=bp.EV_BENCHMARK_CLOSENESS)
    with pytest.raises(bp.BenchmarkLeak):
        bp.confirm(h, evidence="IT_MAKES_THE_TOTAL_COME_OUT_RIGHT")
    assert h.status == bp.UNCONFIRMED


def test_drawing_evidence_may():
    h = bp.Hypothesis(hypothesis_id="H1", name="the segment fraction")
    bp.confirm(h, evidence=bp.EV_CAD_ENTITY,
               detail="the arc and the chord it stands on")
    assert h.status == bp.CONFIRMED
    assert bp.EV_CAD_ENTITY in h.independent()


def test_hypotheses_with_no_evidence_stay_unranked_however_neatly_one_lands():
    near = bp.Hypothesis(hypothesis_id="H1", name="lands on the number",
                         numeric_effect={"residual_m2": 0.0418})
    far = bp.Hypothesis(hypothesis_id="H2", name="does not",
                        numeric_effect={"residual_m2": 9.9})
    out = bp.rank([near, far])
    assert out["status"] == bp.UNRANKED
    assert bp.EV_BENCHMARK_CLOSENESS in out["never_ranked_by"]
    # and the order does not put the close one first by construction
    assert [h["id"] for h in out["hypotheses"]] == ["H1", "H2"]
    assert all(h["status"] == bp.UNCONFIRMED for h in out["hypotheses"])


def test_evidence_ranks_and_arithmetic_does_not():
    weak = bp.Hypothesis(hypothesis_id="H1", name="lands on the number",
                         numeric_effect={"residual_m2": 0.0418})
    strong = bp.Hypothesis(hypothesis_id="H2", name="is drawn",
                           evidence=(bp.EV_DRAWING_GEOMETRY,),
                           numeric_effect={"residual_m2": 9.9})
    out = bp.rank([weak, strong])
    assert out["status"] == "RANKED_ON_EVIDENCE"
    assert [h["id"] for h in out["hypotheses"]][0] == "H2"


def test_a_numeric_effect_is_always_labelled_as_not_evidence():
    h = bp.Hypothesis(hypothesis_id="H1",
                      numeric_effect={"total_m2": 137.5418})
    rec = h.record()
    assert "arithmetic" in rec["numeric_effect_is_not_evidence"]
    assert rec["status"] == bp.UNCONFIRMED


def test_the_p7757_reconciliation_document_obeys_the_protocol():
    import json
    from pathlib import Path

    d = json.loads(Path("data/runs/7757/reconciliation/"
                        "P7757_GROUND_OPEN_ZONE_RECONCILIATION.json")
                   .read_text(encoding="utf-8"))
    assert d["protocol"]["name"] == "BENCHMARK_ANCHORING_PROTECTION"
    assert d["hypothesis_ordering"]["ranked_by"] == \
        "INDEPENDENT_GEOMETRIC_EVIDENCE"
    assert bp.EV_BENCHMARK_CLOSENESS in \
        d["hypothesis_ordering"]["never_ranked_by"]
    for h in d["hypotheses"]:
        assert h["status"] == bp.UNCONFIRMED
        assert not h["rejected_as_evidence"]
