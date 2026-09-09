"""A3 — Client Agent runner.

Answers a WhatsApp turn in Kuwaiti Arabic and updates the lead record. High
volume, so it runs at lower effort than the drawing readers — tune MODEL/EFFORT
here without touching logic.
"""

from __future__ import annotations

import json
from pathlib import Path

from agents.base import ModelFn, anthropic_model, run_json_agent
from .schema import Message, ClientReply

PROMPT_PATH = Path(__file__).parent / "prompt.md"
MODEL = "claude-opus-5"
EFFORT = "medium"  # conversational; does not need max reasoning


def _default_model(system: str, user: str) -> str:
    return anthropic_model(system, user, model=MODEL, effort=EFFORT)


def run(payload: Message, model: ModelFn | None = None) -> ClientReply:
    history = "\n".join(f"{m.get('role')}: {m.get('text')}" for m in payload.history)
    user = (
        (f"Conversation so far:\n{history}\n\n" if history else "")
        + f"New client message:\n{payload.text}\n"
    )
    return run_json_agent(
        PROMPT_PATH, user, ClientReply.from_dict, model=model or _default_model
    )
