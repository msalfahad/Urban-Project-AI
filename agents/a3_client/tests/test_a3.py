"""A3 — Client Agent tests (offline)."""

import json

import pytest

from agents.a3_client.agent import run
from agents.a3_client.schema import Message, ClientReply


def test_qualifies_a_lead():
    model = lambda s, u: json.dumps({
        "reply_ar": "هلا والله، تقصد على المفتاح؟",
        "lead": {"contract_form": "turnkey", "project_type": "house", "area_m2": 400},
        "stage": "qualifying",
    })
    out = run(Message("ابغى ابني بيت"), model=model)
    assert isinstance(out, ClientReply)
    assert out.lead.contract_form == "turnkey"
    assert out.lead.area_m2 == 400


def test_history_reaches_the_model():
    captured = {}
    run(
        Message("ايه", history=[{"role": "client", "text": "مرحبا"}]),
        model=lambda s, u: captured.update(user=u) or json.dumps(
            {"reply_ar": "هلا", "lead": {}, "stage": "qualifying"}
        ),
    )
    assert "Conversation so far" in captured["user"]
    assert "مرحبا" in captured["user"]


def test_invalid_contract_form_is_rejected():
    model = lambda s, u: json.dumps({
        "reply_ar": "x", "lead": {"contract_form": "guesswork"}, "stage": "qualifying"
    })
    with pytest.raises(ValueError):
        run(Message("hi"), model=model)


def test_empty_reply_is_rejected():
    model = lambda s, u: json.dumps({"reply_ar": "", "lead": {}, "stage": "qualifying"})
    with pytest.raises(ValueError):
        run(Message("hi"), model=model)
