"""A13 — Contract Reader runner."""

from __future__ import annotations

from pathlib import Path

from agents.base import ModelFn, run_json_agent
from .schema import ContractInput, ContractOutput

PROMPT_PATH = Path(__file__).parent / "prompt.md"
MODEL = "claude-opus-5"


def run(payload: ContractInput, model: ModelFn | None = None) -> ContractOutput:
    user = f"Signed contract text:\n{payload.text}\n"
    return run_json_agent(PROMPT_PATH, user, ContractOutput.from_dict, model=model)
