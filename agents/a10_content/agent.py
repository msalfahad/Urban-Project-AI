"""A10 — Content Agent runner."""

from __future__ import annotations

from pathlib import Path

from agents.base import ModelFn, anthropic_model, run_json_agent
from .schema import ContentInput, ContentOutput

PROMPT_PATH = Path(__file__).parent / "prompt.md"
MODEL = "claude-opus-5"
EFFORT = "medium"


def _default_model(system: str, user: str) -> str:
    return anthropic_model(system, user, model=MODEL, effort=EFFORT)


def run(payload: ContentInput, model: ModelFn | None = None) -> ContentOutput:
    user = (
        f"Topic: {payload.topic}\nSurface: {payload.surface}\nDate: {payload.date}\n"
    )
    return run_json_agent(
        PROMPT_PATH, user, ContentOutput.from_dict, model=model or _default_model
    )
