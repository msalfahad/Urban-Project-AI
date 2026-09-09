"""A12 — Call Summariser runner."""

from __future__ import annotations

from pathlib import Path

from agents.base import ModelFn, run_json_agent
from .schema import CallInput, CallOutput

PROMPT_PATH = Path(__file__).parent / "prompt.md"
MODEL = "claude-opus-5"


def run(payload: CallInput, model: ModelFn | None = None) -> CallOutput:
    user = f"Call transcript / notes:\n{payload.transcript}\n"
    return run_json_agent(PROMPT_PATH, user, CallOutput.from_dict, model=model)
