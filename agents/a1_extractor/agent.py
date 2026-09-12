"""A1 — Extractor runner.

Thin by design: load the prompt, call the model, validate against the schema.
All the judgement lives in prompt.md; all the arithmetic lives in the engine.
"""

from __future__ import annotations

from pathlib import Path

from agents.base import ModelFn, best, run_json_agent
from .schema import ExtractInput, ExtractOutput

PROMPT_PATH = Path(__file__).parent / "prompt.md"

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
