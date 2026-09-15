"""A12 — Call Summariser tests (offline)."""

import json

import pytest

from agents.a12_call_summariser.agent import run
from agents.a12_call_summariser.schema import CallInput


def test_summarises_a_call():
    model = lambda s, u: json.dumps({
        "requirements": ["turnkey villa"],
        "objections": ["worried about timeline"],
        "contract_form": "turnkey",
        "next_action": "send WhatsApp asking for DWG",
        "sentiment": "positive",
    })
    out = run(CallInput("client wants a villa, asked about time"), model=model)
    assert out.contract_form == "turnkey"
    assert out.next_action


def test_next_action_required():
    model = lambda s, u: json.dumps({"next_action": "", "sentiment": "neutral"})
    with pytest.raises(ValueError):
        run(CallInput("x"), model=model)
