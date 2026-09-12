"""A10 — Content Agent runner."""

from __future__ import annotations

from pathlib import Path

from agents.base import ModelFn, run_json_agent
from .schema import ContentInput, ContentOutput

PROMPT_PATH = Path(__file__).parent / "prompt.md"


def run(payload: ContentInput, model: ModelFn | None = None) -> ContentOutput:
    user = (
        f"Topic: {payload.topic}\nSurface: {payload.surface}\nDate: {payload.date}\n"
    )
    return run_json_agent(
        PROMPT_PATH, user, ContentOutput.from_dict, model=model
    )
