"""A1 — Extractor runner.

Thin by design: load the prompt, call the model, validate against the schema.
All the judgement lives in prompt.md; all the arithmetic lives in the engine.
"""

from __future__ import annotations

from pathlib import Path

from agents.base import ModelFn, run_json_agent
from .schema import ExtractInput, ExtractOutput

PROMPT_PATH = Path(__file__).parent / "prompt.md"
MODEL = "claude-opus-5"  # drawing reading benefits from the strongest model


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
    return run_json_agent(PROMPT_PATH, user, ExtractOutput.from_dict, model=model)
