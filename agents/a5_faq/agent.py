"""A5 — FAQ Agent runner."""

from __future__ import annotations

from pathlib import Path

from agents.base import ModelFn, anthropic_model, run_json_agent
from .schema import FAQInput, FAQOutput

PROMPT_PATH = Path(__file__).parent / "prompt.md"
MODEL = "claude-opus-5"
EFFORT = "low"


def _default_model(system: str, user: str) -> str:
    return anthropic_model(system, user, model=MODEL, effort=EFFORT)


def run(payload: FAQInput, model: ModelFn | None = None) -> FAQOutput:
    user = f"Language: {payload.language}\nQuestion: {payload.question}\n"
    return run_json_agent(
        PROMPT_PATH, user, FAQOutput.from_dict, model=model or _default_model
    )
