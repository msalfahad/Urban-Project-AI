"""Template agent tests — run offline with a fake model.

Shows the pattern: give the runner a stubbed model function, then assert on the
validated output. Real agents add cases of (known input -> known correct
output) here.
"""

import json

import pytest

from agents._template.agent import run
from agents._template.schema import Input


def fake_model(system_prompt: str, user_text: str) -> str:
    assert "one job" in system_prompt  # the prompt was actually loaded
    return json.dumps({"result": user_text.upper(), "notes": "stub"})


def test_run_validates_and_returns_output():
    out = run(Input(text="hello"), model=fake_model)
    assert out.result == "HELLO"
    assert out.notes == "stub"


def test_invalid_json_is_rejected():
    with pytest.raises(ValueError):
        run(Input(text="x"), model=lambda s, u: "not json")


def test_empty_result_is_rejected():
    with pytest.raises(ValueError):
        run(Input(text="x"), model=lambda s, u: json.dumps({"result": ""}))
