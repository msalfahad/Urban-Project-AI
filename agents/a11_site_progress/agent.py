"""A11 — Site Progress runner."""

from __future__ import annotations

from pathlib import Path

from agents.base import ModelFn, run_json_agent
from .schema import SiteInput, SiteOutput

PROMPT_PATH = Path(__file__).parent / "prompt.md"
MODEL = "claude-opus-5"


def run(payload: SiteInput, model: ModelFn | None = None) -> SiteOutput:
    acts = ", ".join(payload.known_activities) or "unknown"
    user = (
        f"Timestamp: {payload.timestamp}\n"
        f"Known activities: {acts}\n\n"
        f"Observation:\n{payload.observation}\n"
    )
    return run_json_agent(PROMPT_PATH, user, SiteOutput.from_dict, model=model)
