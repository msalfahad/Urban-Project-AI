"""R8.13 §27: the reviewed closure release model - an evaluator, never a release."""

from __future__ import annotations

from engine.source import closure_release as CR

ALL = {c: True for c in CR.CONDITIONS}


def test_every_condition_is_required_for_reviewed():
    assert CR.evaluate(CR.AUTHORISED_FOR_SHADOW, ALL)["level"] == CR.REVIEWED
    for c in CR.CONDITIONS:
        e = CR.evaluate(CR.AUTHORISED_FOR_SHADOW, dict(ALL, **{c: None}))
        assert e["level"] == CR.AUTHORISED_FOR_SHADOW and e["missing_for_reviewed"] == [c]


def test_a_lower_level_never_jumps_and_nothing_is_released():
    for lv in (CR.CANDIDATE, CR.DIAGNOSTIC_PASS):
        e = CR.evaluate(lv, ALL)
        assert e["level"] == lv and "AUTHORISED_FOR_SHADOW" in e["missing_for_reviewed"]
    assert not CR.evaluate(CR.AUTHORISED_FOR_SHADOW, ALL)["releases_anything"]
    assert "a release" in CR.policy_record()["never"]
