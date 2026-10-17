"""A2 — Reviewer tests (offline)."""

import json

from agents.a2_reviewer.agent import run
from agents.a1_extractor.schema import ExtractInput, ExtractOutput


def test_reviewer_produces_records_in_a1_schema():
    model = lambda s, u: json.dumps({
        "records": [{
            "description": "Plaster to wall W1",
            "trade": "plaster",
            "count": 1,
            "dimensions_m": [6.0, 2.9],
            "unit": "m2",
        }]
    })
    out = run(ExtractInput("A-201", "3 of 8", "C"), "…", model=model)
    assert isinstance(out, ExtractOutput)
    assert out.records[0].dimensions_m == [6.0, 2.9]


def test_reviewer_prompt_is_blind():
    captured = {}
    run(
        ExtractInput("A-201"),
        "content",
        model=lambda s, u: captured.update(system=s) or json.dumps({"records": []}),
    )
    # The blind-review intent must be present in the prompt.
    assert "never seen" in captured["system"].lower()
