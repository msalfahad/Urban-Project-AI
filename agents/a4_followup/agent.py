"""A4 — Follow-up Agent runner."""

from __future__ import annotations

from pathlib import Path

from agents.base import ModelFn, anthropic_model, run_json_agent
from .schema import FollowupInput, FollowupOutput

PROMPT_PATH = Path(__file__).parent / "prompt.md"
MODEL = "claude-opus-5"
EFFORT = "low"  # short templated nudges


def _default_model(system: str, user: str) -> str:
    return anthropic_model(system, user, model=MODEL, effort=EFFORT)


def run(payload: FollowupInput, model: ModelFn | None = None) -> FollowupOutput:
    user = (
        f"Days silent: {payload.days_silent}\n"
        f"Last stage: {payload.last_stage}\n"
        f"Client replied since last message: {payload.client_replied_since}\n"
        f"Lead: {payload.lead_summary}\n"
    )
    return run_json_agent(
        PROMPT_PATH, user, FollowupOutput.from_dict, model=model or _default_model
    )
