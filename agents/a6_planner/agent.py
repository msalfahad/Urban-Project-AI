"""A6 — Planner runner."""

from __future__ import annotations

from pathlib import Path

from agents.base import ModelFn, run_json_agent
from .schema import PlanInput, PlanOutput

PROMPT_PATH = Path(__file__).parent / "prompt.md"
MODEL = "claude-opus-5"


def run(payload: PlanInput, model: ModelFn | None = None) -> PlanOutput:
    user = (
        f"Contract form: {payload.contract_form}\n"
        f"Area (m2): {payload.area_m2}\n"
        f"Floors: {payload.floors}\n"
        f"Pool: {payload.pool}\nLift: {payload.lift}\n"
        f"Notes: {payload.notes}\n"
    )
    return run_json_agent(PROMPT_PATH, user, PlanOutput.from_dict, model=model)
