"""A trigger word is English. A trigger beside a quantity is a benchmark.

None of these cases is from the project the engine is being tested on.
They are a school, a warehouse, a hospital and a car park, because a rule
that only works on the sentences that once broke it is not a rule.

The failure being guarded against runs both ways. A scanner that misses
"expected area" leaks the answer. A scanner that fires on "a break is
expected because a stair is its own finish" gets switched off by whoever
has to work around it, and a switched-off scanner protects nothing.
"""

from __future__ import annotations

import pytest

from engine import benchmark_protection as bp

# --- ordinary construction English, in four other buildings -------------
ORDINARY = [
    "a movement joint is expected because the slab is longer than 6 m",
    "the corridor is expected to take heavy traffic",
    "target the survey at the loading bay first",
    "a known dimension is never replaced by a default",
    "the reference drawing shows a nib at the ward entrance",
    "the ward is known as the isolation suite",
    "pupils excel in the practical rooms",
    "benchmark reconciliation is a separate phase of this job",
    "the actual polygon of the landing is what gets measured",
    "ACTUAL DRAWING DIMENSIONS take precedence over a standard detail",
    "the correct reading of the arc needs the centre point",
    "the car park deck is measured in square metres",
    "the warehouse floor is measured in lm along each bay",
    "the specification should be read with the door schedule",
]

# --- the answer, however it is phrased ----------------------------------
BENCHMARK_SHAPED = [
    "expected area",
    "expected quantity",
    "expected total",
    "expected value",
    "expected 842.0 m2",
    "correct area",
    "target quantity",
    "target dimension of 3400",
    "human Excel total",
    "the benchmark says 842.0",
    "the known total for the ward block",
    "reference area for the loading bay",
    "the qiyal total",
    "take-off total is 1290",
    "bill of quantities total",
    "the excel quantity for level 2",
    "the area should be 96",
    "no human quantity reaches a blind pass",
]


@pytest.mark.parametrize("text", ORDINARY)
def test_ordinary_construction_english_is_not_a_leak(text):
    assert bp.scan(text) == [], text


@pytest.mark.parametrize("text", BENCHMARK_SHAPED)
def test_benchmark_shaped_information_still_trips(text):
    assert bp.scan(text), text


def test_a_field_named_like_an_answer_is_caught_whatever_it_holds():
    # A KEY is a slot somebody put an answer in, so it is judged by shape
    # even where its value is innocent.
    for payload in ({"expected": "not stated"},
                    {"target_area": None},
                    {"human_excel_total": ""},
                    {"deep": {"known_total": 0}}):
        assert bp.scan(payload), payload


def test_a_weak_trigger_needs_a_word_for_an_answer_beside_it():
    # "known" means ESTABLISHED FROM THE DRAWING as often as it means given
    assert bp.scan("a known dimension") == []
    assert bp.scan("a known width") == []
    assert bp.scan("the known total")
    assert bp.scan("the known quantity")


def test_actual_is_not_a_trigger_at_all():
    # It is the word the rules use for "as drawn", which is what the engine
    # is told to measure.
    assert bp.scan("the actual polygon in m2") == []
    assert bp.scan("actual drawing dimensions first") == []
    assert bp.scan("lm along its actual going") == []


def test_a_blind_pass_is_still_refused_the_answer():
    with pytest.raises(bp.BenchmarkLeak):
        bp.assert_blind({"note": "the expected area of the ward is 842.0"})
    with pytest.raises(bp.BenchmarkLeak):
        bp.assert_blind({"expected_area_m2": 842.0})


def test_a_blind_pass_may_be_handed_ordinary_prose():
    bp.assert_blind({"note": "a movement joint is expected because the "
                             "slab is longer than 6 m",
                     "rule": "a known dimension is never replaced by a "
                             "default"})


def test_the_scanner_says_what_it_does_not_cover():
    why = bp.frozen_parameters()["why"]
    assert why["what_this_scanner_does_not_catch"]
    assert why["ordinary_language_is_not_a_leak"]


def test_the_model_name_moved_with_the_behaviour():
    assert bp.MODEL.endswith("_V2")
