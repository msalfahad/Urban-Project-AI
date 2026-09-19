"""A15 — Marketing Strategist runner."""

from __future__ import annotations

import json
from pathlib import Path

from agents.base import ModelFn, run_json_agent
from .schema import MarketingInput, MarketingPlan

PROMPT_PATH = Path(__file__).parent / "prompt.md"


def run(payload: MarketingInput, model: ModelFn | None = None) -> MarketingPlan:
    user = (
        f"Plan for: {payload.date_range}\nGoal: {payload.goal or 'grow enquiries'}\n\n"
        f"Analyst findings (A14):\n{json.dumps(payload.analysis, ensure_ascii=False, indent=1)}\n"
    )
    return run_json_agent(PROMPT_PATH, user, MarketingPlan.from_dict, model=model)
