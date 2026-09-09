"""A2 — Reviewer runner.

Reads the same drawing as A1, blind, and emits its own records in A1's schema so
the engine can compare the two sets number-for-number. A2 must never be given
A1's output — enforced simply by the runner not accepting it as an argument.
"""

from __future__ import annotations

from pathlib import Path

from agents.base import ModelFn, run_json_agent
from agents.a1_extractor.schema import ExtractInput, ExtractOutput

PROMPT_PATH = Path(__file__).parent / "prompt.md"
MODEL = "claude-opus-5"


def run(payload: ExtractInput, drawing_text: str, model: ModelFn | None = None) -> ExtractOutput:
    user = (
        f"Drawing: {payload.drawing_number}\n"
        f"Sheet: {payload.sheet}\n"
        f"Revision: {payload.revision}\n"
        f"Trade in focus: {payload.trade or 'all'}\n\n"
        f"--- drawing content ---\n{drawing_text}\n"
    )
    return run_json_agent(PROMPT_PATH, user, ExtractOutput.from_dict, model=model)
