"""A11 — Site Progress tests (offline)."""

import json

import pytest

from agents.a11_site_progress.agent import run
from agents.a11_site_progress.schema import SiteInput


def test_logs_completion_and_flags_stall():
    model = lambda s, u: json.dumps({
        "completed": [{"activity": "blockwork", "detail": "GF done", "confidence": "high"}],
        "trade_status": [{"trade": "plaster", "status": "stalled"}],
        "flags": ["plaster not moved in 6 days"],
    })
    out = run(SiteInput("photo of finished blockwork", known_activities=["blockwork"]), model=model)
    assert out.completed[0].activity == "blockwork"
    assert out.flags


def test_invalid_trade_status_rejected():
    model = lambda s, u: json.dumps({"trade_status": [{"trade": "x", "status": "vibing"}]})
    with pytest.raises(ValueError):
        run(SiteInput("x"), model=model)
