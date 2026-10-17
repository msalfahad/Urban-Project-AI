"""A10 — Content tests (offline)."""

import json

import pytest

from agents.a10_content.agent import run
from agents.a10_content.schema import ContentInput


def test_writes_a_caption():
    model = lambda s, u: json.dumps(
        {"hook": "هيكل خلص بـ٦ أسابيع", "caption_ar": "...", "hashtags": ["#الكويت"]}
    )
    out = run(ContentInput("finished black structure", "feed", "2026-02-24"), model=model)
    assert out.hook and out.caption_ar


def test_hook_required():
    with pytest.raises(ValueError):
        run(ContentInput("x"), model=lambda s, u: json.dumps({"hook": "", "caption_ar": "y"}))
