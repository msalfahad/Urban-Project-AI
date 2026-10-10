"""Template agent runner (~50 lines).

The shape every agent shares: load the prompt, call the model, validate the
output against the schema, hand it back. The model call is left as a single
seam (`_call_model`) so tests can run without network or API keys — a test
passes in a fake model function and checks the plumbing.

This file deliberately contains no business logic. All judgement lives in
prompt.md; all arithmetic lives in the engine.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Callable

from .schema import Input, Output

PROMPT_PATH = Path(__file__).parent / "prompt.md"

# A model function takes (system_prompt, user_text) and returns raw JSON text.
ModelFn = Callable[[str, str], str]


def load_prompt() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8")


def run(payload: Input, model: ModelFn) -> Output:
    """Run the agent over one input and return validated output.

    `model` is injected rather than imported so this is testable offline and so
    the real Anthropic client lives in exactly one place (wired in later).
    """
    system_prompt = load_prompt()
    raw = model(system_prompt, payload.text)

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"model did not return valid JSON: {exc}") from exc

    output = Output(result=data.get("result", ""), notes=data.get("notes", ""))
    output.validate()
    return output
