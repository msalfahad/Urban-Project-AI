"""A6 — Planner runner."""

from __future__ import annotations

from pathlib import Path

from agents.base import ModelFn, ladder, run_json_agent
from .schema import PlanInput, PlanOutput

PROMPT_PATH = Path(__file__).parent / "prompt.md"


def run(payload: PlanInput, model: ModelFn | None = None) -> PlanOutput:
    user = (
        f"Contract form: {payload.contract_form}\n"
        f"Area (m2): {payload.area_m2}\n"
        f"Floors: {payload.floors}\n"
        f"Pool: {payload.pool}\nLift: {payload.lift}\n"
        f"Notes: {payload.notes}\n"
    )
    # A full programme is ~30 activities of JSON; give the output room.
    return run_json_agent(PROMPT_PATH, user, PlanOutput.from_dict, model=model or ladder(max_tokens=32000))
