"""A8 — Briefer runner. Usually invoked as a Cowork scheduled task."""

from __future__ import annotations

import json
from pathlib import Path

from agents.base import ModelFn, run_json_agent
from .schema import BriefInput, BriefOutput

PROMPT_PATH = Path(__file__).parent / "prompt.md"
MODEL = "claude-opus-5"


def run(payload: BriefInput, model: ModelFn | None = None) -> BriefOutput:
    user = (
        f"Period: {payload.period}\n\n"
        f"Snapshot (already computed):\n"
        f"{json.dumps(payload.snapshot, ensure_ascii=False, indent=2)}\n"
    )
    return run_json_agent(PROMPT_PATH, user, BriefOutput.from_dict, model=model)
