"""A17 — Campaign Manager runner."""

from __future__ import annotations

import json
from pathlib import Path

from agents.base import ModelFn, anthropic_model, run_json_agent
from .schema import Campaign, CampaignInput

PROMPT_PATH = Path(__file__).parent / "prompt.md"
MODEL = "claude-opus-5"
EFFORT = "medium"


def _default_model(system: str, user: str) -> str:
    return anthropic_model(system, user, model=MODEL, effort=EFFORT)


def _block(label: str, payload: dict) -> str:
    if not payload:
        return ""
    return f"\n{label}:\n{json.dumps(payload, ensure_ascii=False, indent=1)}\n"


def run(payload: CampaignInput, model: ModelFn | None = None) -> Campaign:
    project = payload.project
    user = (
        f"Project: {project.name}\n"
        f"Type: {project.type or 'unspecified'}\n"
        f"Location: {project.location or 'unspecified'}\n"
        f"Current stage: {project.stage or 'unspecified'}\n"
        f"Selling points: {', '.join(project.usps) or 'none given'}\n"
        f"Existing assets: {', '.join(project.photo_refs) or 'none'}\n\n"
        f"Window: {payload.window}\n"
        f"Objective: {payload.objective or 'generate qualified enquiries'}\n"
        f"Channels allowed: {', '.join(payload.channels) or 'instagram, whatsapp'}\n"
        + _block("Instagram evidence (A14)", payload.evidence)
        + _block("Progress since the last review — correct the campaign", payload.progress)
    )
    return run_json_agent(PROMPT_PATH, user, Campaign.from_dict, model=model or _default_model)
