"""A14 — Instagram Analyst tests (offline)."""

import json

import pytest

from agents.a14_ig_analyst.agent import run
from agents.a14_ig_analyst.schema import IGAnalysisInput


def test_analyses_posts():
    model = lambda s, u: json.dumps({
        "period": "last_30_days",
        "headline": "Progress reels drive the most saves",
        "best_posts": [{"id": "p1", "why": "3x median saves"}],
        "recommendations": ["more black-structure reels at 8pm"],
    })
    out = run(IGAnalysisInput("last_30_days", posts=[{"id": "p1", "saves": 40}]), model=model)
    assert out.headline and out.recommendations


def test_headline_required():
    with pytest.raises(ValueError):
        run(IGAnalysisInput("x"), model=lambda s, u: json.dumps({"headline": ""}))
