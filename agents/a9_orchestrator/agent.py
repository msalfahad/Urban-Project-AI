"""A9 — Orchestrator runner."""

from __future__ import annotations

import json
from pathlib import Path

from agents.base import ModelFn, run_json_agent
from .schema import Event, Routing

PROMPT_PATH = Path(__file__).parent / "prompt.md"


def run(payload: Event, model: ModelFn | None = None) -> Routing:
    user = (
        f"Event type: {payload.type}\n"
        f"State: {payload.state}\n"
        f"Record:\n{json.dumps(payload.record, ensure_ascii=False, indent=2)}\n"
    )
    return run_json_agent(PROMPT_PATH, user, Routing.from_dict, model=model)
