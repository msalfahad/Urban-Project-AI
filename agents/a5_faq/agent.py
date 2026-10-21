"""A5 — FAQ Agent runner."""

from __future__ import annotations

from pathlib import Path

from agents.base import ModelFn, run_json_agent
from .schema import FAQInput, FAQOutput

PROMPT_PATH = Path(__file__).parent / "prompt.md"


def run(payload: FAQInput, model: ModelFn | None = None) -> FAQOutput:
    user = f"Language: {payload.language}\nQuestion: {payload.question}\n"
    return run_json_agent(
        PROMPT_PATH, user, FAQOutput.from_dict, model=model
    )
