"""A16 — Post Designer runner.

Produces the image brief + caption + interactive structure. The image itself is
rendered by a separate generator (e.g. the Higgsfield MCP tools) from the
`image_brief` this agent writes — this agent never renders pixels, it designs.
"""

from __future__ import annotations

from pathlib import Path

from agents.base import ModelFn, anthropic_model, run_json_agent
from .schema import PostBrief, PostDesign

PROMPT_PATH = Path(__file__).parent / "prompt.md"
MODEL = "claude-opus-5"
EFFORT = "medium"


def _default_model(system: str, user: str) -> str:
    return anthropic_model(system, user, model=MODEL, effort=EFFORT)


def run(payload: PostBrief, model: ModelFn | None = None) -> PostDesign:
    refs = ", ".join(payload.photo_refs) or "none"
    user = (
        f"Post type: {payload.type}\nTopic: {payload.topic}\n"
        f"Goal: {payload.goal}\nCTA: {payload.cta}\nPhoto refs: {refs}\n"
    )
    return run_json_agent(PROMPT_PATH, user, PostDesign.from_dict, model=model or _default_model)
