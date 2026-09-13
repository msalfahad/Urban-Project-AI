"""A2 — Reviewer runner.

Reads the same drawing as A1, blind, and emits its own records in A1's schema so
the engine can compare the two sets number-for-number. A2 must never be given
A1's output — enforced simply by the runner not accepting it as an argument.
"""

from __future__ import annotations

from pathlib import Path

from agents.base import ModelFn, run_json_agent
from agents.a1_extractor.agent import DRAWING_MODEL
from agents.a1_extractor.schema import ExtractInput, ExtractOutput
from agents.a1_extractor.semantic import SemanticInput, SemanticOutput

PROMPT_PATH = Path(__file__).parent / "prompt.md"
BLIND_PROMPT_PATH = Path(__file__).parent / "prompt_blind.md"

# Anything that would leak the answer into a "blind" pass.
# Compared against a LOWERCASED field name, so every entry must be lowercase.
# "measurer" and the legacy "qiyal" both appear: old records still carry the old
# word, and a leak does not stop being a leak because the vocabulary moved.
FORBIDDEN_BLIND_INPUTS = ("a1", "a1_output", "a1_result", "a1_record",
                          "semantic_comparison", "comparison", "measurer",
                          "qiyal", "benchmark", "ground_truth", "manual_takeoff",
                          "site_measured", "expected")


def run(payload: ExtractInput, drawing_text: str, model: ModelFn | None = None) -> ExtractOutput:
    user = (
        f"Drawing: {payload.drawing_number}\n"
        f"Sheet: {payload.sheet}\n"
        f"Revision: {payload.revision}\n"
        f"Trade in focus: {payload.trade or 'all'}\n\n"
        f"--- drawing content ---\n{drawing_text}\n"
    )
    return run_json_agent(PROMPT_PATH, user, ExtractOutput.from_dict, model=model or DRAWING_MODEL())


class BlindIsolationError(RuntimeError):
    """Something that would answer the question was passed into the blind pass."""


def run_blind(payload: SemanticInput, model: ModelFn | None = None,
              **kwargs: object) -> SemanticOutput:
    """A2's independent semantic pass. It cannot be given A1's work.

    The isolation is structural, not a promise in the prompt: this function
    takes a SemanticInput and a model, and NOTHING ELSE. Any extra keyword —
    a1_output, the comparison result, the MEASURER benchmark, expected answers —
    raises rather than being quietly ignored, because a "blind" review that
    silently saw the answer is worse than no review at all.

    Two agents agreeing on something they were both shown proves nothing. This
    signature is what makes their agreement mean anything.
    """
    if kwargs:
        leaked = sorted(kwargs)
        raise BlindIsolationError(
            f"run_blind was given {leaked} — a blind pass takes the drawing and "
            "the geometry only. Pass A1's output to the CHALLENGER instead.")
    for field_name in vars(payload):
        low = field_name.lower()
        if any(bad in low for bad in FORBIDDEN_BLIND_INPUTS):
            raise BlindIsolationError(
                f"SemanticInput carries {field_name!r}, which would answer the "
                "question this pass exists to ask independently.")
    lines = [
        f"Project: {payload.project_id}",
        f"Drawing: {payload.drawing_id}  revision {payload.drawing_revision}",
        f"Floor: {payload.floor_id}",
        f"Scope brief: {payload.scope_brief or '(none supplied)'}",
        "",
        "--- spaces the geometry engine established (DO NOT re-measure) ---",
    ]
    for sid, geo in payload.geometry.items():
        lines.append(f"{sid}: " + ", ".join(f"{k}={v}" for k, v in geo.items()))
    user = "\n".join(lines) + "\n"
    return run_json_agent(BLIND_PROMPT_PATH, user, SemanticOutput.from_dict,
                          model=model or DRAWING_MODEL())
