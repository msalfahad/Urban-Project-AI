"""A15 — Marketing Strategist tests (offline)."""

import json

import pytest

from agents.a15_marketing.agent import run
from agents.a15_marketing.schema import MarketingInput


def test_builds_a_plan():
    model = lambda s, u: json.dumps({
        "goal": "more turnkey enquiries",
        "themes": ["progress", "finished villas"],
        "calendar": [{"date": "2026-02-24", "type": "reel", "topic": "National Day tour"}],
        "cadence": "3x/week",
    })
    out = run(MarketingInput("Feb 2026", goal="more turnkey enquiries"), model=model)
    assert out.calendar and out.themes


def test_empty_calendar_rejected():
    with pytest.raises(ValueError):
        run(MarketingInput("x"), model=lambda s, u: json.dumps({"goal": "x", "calendar": []}))
