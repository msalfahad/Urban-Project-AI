"""A5 — FAQ tests (offline)."""

import json

import pytest

from agents.a5_faq.agent import run
from agents.a5_faq.schema import FAQInput


def test_answers_a_permit_question():
    model = lambda s, u: json.dumps(
        {"category": "permits", "answer_ar": "نعم نساعدك بالتراخيص", "needs_human": False}
    )
    out = run(FAQInput("تحتاجون رخصة؟"), model=model)
    assert out.category == "permits"


def test_unknown_routes_to_human():
    model = lambda s, u: json.dumps(
        {"category": "other", "needs_human": True, "answer_ar": ""}
    )
    out = run(FAQInput("سؤال صعب"), model=model)
    assert out.needs_human


def test_answer_required_unless_human():
    model = lambda s, u: json.dumps(
        {"category": "process", "needs_human": False, "answer_ar": ""}
    )
    with pytest.raises(ValueError):
        run(FAQInput("كيف تشتغلون؟"), model=model)
