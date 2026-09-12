"""A16 — Post Designer runner.

Produces the image brief + caption + interactive structure. The image itself is
rendered by a separate generator (e.g. the Higgsfield MCP tools) from the
`image_brief` this agent writes — this agent never renders pixels, it designs.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from agents.base import ModelFn, anthropic_model, extract_json, run_json_agent
from .schema import GridBrief, GridDesign, PostBrief, PostDesign

PROMPT_PATH = Path(__file__).parent / "prompt.md"
GRID_PROMPT_PATH = Path(__file__).parent / "prompt_grid.md"
MODEL = "claude-opus-5"
EFFORT = "medium"


def _default_model(system: str, user: str) -> str:
    return anthropic_model(system, user, model=MODEL, effort=EFFORT)


def _grid_model(system: str, user: str) -> str:
    # Nine tiles of bilingual copy is a long answer; give it room.
    return anthropic_model(system, user, model=MODEL, effort=EFFORT, max_tokens=24000)


def run_grid(payload: GridBrief, model: ModelFn | None = None) -> GridDesign:
    payload.validate()
    system = GRID_PROMPT_PATH.read_text(encoding="utf-8")
    user = "Design this grid.\n\n" + json.dumps(asdict(payload), ensure_ascii=False, indent=1)
    raw = (model or _grid_model)(system, user)
    return GridDesign.from_dict(
        extract_json(raw),
        expected_tiles=payload.tiles,
        inventory={p.ref for p in payload.photos} if payload.photos else None,
        languages=payload.languages,
    )


def run(payload: PostBrief, model: ModelFn | None = None) -> PostDesign:
    refs = ", ".join(payload.photo_refs) or "none"
    user = (
        f"Post type: {payload.type}\nTopic: {payload.topic}\n"
        f"Goal: {payload.goal}\nCTA: {payload.cta}\nPhoto refs: {refs}\n"
    )
    return run_json_agent(PROMPT_PATH, user, PostDesign.from_dict, model=model or _default_model)
