"""A8 — Briefer tests (offline)."""

import json

import pytest

from agents.a8_briefer.agent import run
from agents.a8_briefer.schema import BriefInput


def test_writes_a_brief():
    model = lambda s, u: json.dumps(
        {"headline": "Villa quote awaiting your approval", "decisions_needed": ["Approve villa BOQ"]}
    )
    out = run(BriefInput("daily", {"quotes_out": 1}), model=model)
    assert out.headline
    assert out.decisions_needed


def test_headline_required():
    with pytest.raises(ValueError):
        run(BriefInput(), model=lambda s, u: json.dumps({"headline": ""}))
