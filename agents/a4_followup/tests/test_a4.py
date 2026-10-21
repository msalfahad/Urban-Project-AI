"""A4 — Follow-up tests (offline)."""

import json

import pytest

from agents.a4_followup.agent import run
from agents.a4_followup.schema import FollowupInput


def test_day2_nudge():
    model = lambda s, u: json.dumps(
        {"should_send": True, "message_ar": "هلا، لا زلنا بخدمتك", "step": "day2"}
    )
    out = run(FollowupInput(days_silent=2, last_stage="awaiting_drawings"), model=model)
    assert out.should_send and out.step == "day2"


def test_no_send_when_client_replied():
    model = lambda s, u: json.dumps(
        {"should_send": False, "message_ar": "", "step": "stop", "reason": "replied"}
    )
    out = run(FollowupInput(days_silent=2, client_replied_since=True), model=model)
    assert not out.should_send


def test_send_without_message_is_rejected():
    model = lambda s, u: json.dumps({"should_send": True, "message_ar": "", "step": "day5"})
    with pytest.raises(ValueError):
        run(FollowupInput(days_silent=5), model=model)
