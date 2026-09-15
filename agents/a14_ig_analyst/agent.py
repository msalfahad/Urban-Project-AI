"""A14 — Instagram Analyst runner."""

from __future__ import annotations

import json
from pathlib import Path

from agents.base import ModelFn, run_json_agent
from .schema import IGAnalysisInput, IGAnalysis

PROMPT_PATH = Path(__file__).parent / "prompt.md"


def run(payload: IGAnalysisInput, model: ModelFn | None = None) -> IGAnalysis:
    user = (
        f"Period: {payload.period}\n"
        f"Account metrics:\n{json.dumps(payload.account, ensure_ascii=False)}\n\n"
        f"Posts ({len(payload.posts)}):\n{json.dumps(payload.posts, ensure_ascii=False, indent=1)}\n"
    )
    return run_json_agent(PROMPT_PATH, user, IGAnalysis.from_dict, model=model)
