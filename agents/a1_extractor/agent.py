"""A1 — Extractor runner.

Thin by design: load the prompt, call the model, validate against the schema.
All the judgement lives in prompt.md; all the arithmetic lives in the engine.
"""

from __future__ import annotations

from pathlib import Path

from agents.base import ModelFn, best, run_json_agent
from .schema import ExtractInput, ExtractOutput
from .semantic import SemanticInput, SemanticOutput

PROMPT_PATH = Path(__file__).parent / "prompt.md"
SEMANTIC_PROMPT_PATH = Path(__file__).parent / "prompt_semantic.md"

# A misread dimension becomes a wrong quantity, a wrong price, a wrong order —
# the strongest model at high effort, never the cheap ladder.
DRAWING_MODEL = lambda: best(effort="xhigh")


def run(payload: ExtractInput, drawing_text: str, model: ModelFn | None = None) -> ExtractOutput:
    """Extract measurement records from one drawing/schedule.

    `drawing_text` is the text (or, in production, the image content) of the
    sheet. The metadata in `payload` is echoed onto the user turn so the model
    stamps every record with the right drawing/sheet/revision.
    """
    user = (
        f"Drawing: {payload.drawing_number}\n"
        f"Sheet: {payload.sheet}\n"
        f"Revision: {payload.revision}\n"
        f"Trade in focus: {payload.trade or 'all'}\n\n"
        f"--- drawing content ---\n{drawing_text}\n"
    )
    return run_json_agent(PROMPT_PATH, user, ExtractOutput.from_dict, model=model or DRAWING_MODEL())


def run_semantic(payload: SemanticInput, model: ModelFn | None = None) -> SemanticOutput:
    """A1's primary job now: attach meaning to geometry that already exists.

    The geometry is passed in and echoed back untouched — A1 reads it to reason
    about what a space is, and has nowhere in its schema to change it.
    """
    lines = [
        f"Project: {payload.project_id}",
        f"Drawing: {payload.drawing_id}  revision {payload.drawing_revision}",
        f"Floor: {payload.floor_id}",
        f"Scope brief: {payload.scope_brief or '(none supplied)'}",
        "",
        "--- spaces the geometry engine established (DO NOT re-measure) ---",
    ]
    for sid, geo in payload.geometry.items():
        facts = ", ".join(f"{k}={v}" for k, v in geo.items())
        lines.append(f"{sid}: {facts}")
    user = "\n".join(lines) + "\n"
    return run_json_agent(SEMANTIC_PROMPT_PATH, user, SemanticOutput.from_dict,
                          model=model or DRAWING_MODEL())
