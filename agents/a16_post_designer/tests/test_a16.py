"""A16 — Post Designer tests (offline)."""

import json

import pytest

from agents.a16_post_designer.agent import run
from agents.a16_post_designer.schema import PostBrief


def test_designs_a_post_with_poll():
    model = lambda s, u: json.dumps({
        "image_brief": "finished villa façade at dusk, warm light, Arabic overlay 'أي واجهة تختار؟'",
        "caption_ar": "أي واجهة تفضل؟",
        "hashtags": ["#الكويت", "#مقاولات"],
        "interactive": {"kind": "poll_abc", "question_ar": "أي واجهة؟", "options": ["A", "B", "C"]},
    })
    out = run(PostBrief("poll", "façade styles", goal="engagement", cta="صوّت"), model=model)
    assert out.image_brief and out.caption_ar
    assert out.interactive["kind"] == "poll_abc"


def test_poll_abc_needs_three_options():
    model = lambda s, u: json.dumps({
        "image_brief": "x", "caption_ar": "y",
        "interactive": {"kind": "poll_abc", "options": ["A", "B"]},
    })
    with pytest.raises(ValueError):
        run(PostBrief("poll", "x"), model=model)


def test_image_brief_required():
    with pytest.raises(ValueError):
        run(PostBrief("reel", "x"), model=lambda s, u: json.dumps({"image_brief": "", "caption_ar": "y"}))
