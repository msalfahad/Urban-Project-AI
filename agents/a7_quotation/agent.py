"""A7 — Quotation & Contract Writer runner.

The system prompt is the instructions plus the clause library plus every example
document in `references/examples/`. Adding an example is a file drop; no code
changes.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from agents.base import ModelFn, anthropic_model, extract_json
from .schema import DocumentInput, DocumentOutput

HERE = Path(__file__).parent
PROMPT_PATH = HERE / "prompt.md"
CLAUSES_PATH = HERE / "references" / "clauses_ar.md"
EXAMPLES_DIR = HERE / "references" / "examples"
MODEL = "claude-opus-5"
EFFORT = "medium"


def _default_model(system: str, user: str) -> str:
    return anthropic_model(system, user, model=MODEL, effort=EFFORT, max_tokens=24000)


def system_prompt() -> str:
    parts = [PROMPT_PATH.read_text(encoding="utf-8")]
    parts.append("\n\n---\n\n# مكتبة البنود القياسية\n\n" + CLAUSES_PATH.read_text(encoding="utf-8"))
    examples = sorted(EXAMPLES_DIR.glob("*.md")) if EXAMPLES_DIR.is_dir() else []
    for path in examples:
        parts.append(f"\n\n---\n\n# مثال: {path.stem}\n\n" + path.read_text(encoding="utf-8"))
    return "".join(parts)


def _user_text(payload: DocumentInput) -> str:
    p = payload.project
    facts = {
        "kind": payload.kind,
        "project": {
            "description": p.description,
            "name": p.name,
            "location": p.location,
            "plot": p.plot,
            "floors": p.floors,
            "built_area_m2": p.built_area_m2,
            "scopes_in_order": p.scopes,
        },
        "client": {"title": payload.client.title, "name": payload.client.name},
        "special_requests": payload.special_requests,
        "extra_exclusions": payload.extra_exclusions,
        "owner_supplied_materials": [m.item for m in payload.owner_materials],
        "payment_milestone_triggers": [m.trigger for m in payload.payment_milestones],
    }
    return (
        "Write the Arabic body for this document. Money, dates and durations are "
        "rendered by code — leave them out.\n\n"
        + json.dumps(facts, ensure_ascii=False, indent=1)
    )


def run(payload: DocumentInput, model: ModelFn | None = None) -> DocumentOutput:
    payload.validate()
    system = system_prompt()
    model = model or _default_model
    raw = model(system, _user_text(payload))
    return DocumentOutput.from_dict(extract_json(raw))


def to_json(out: DocumentOutput) -> str:
    return json.dumps(asdict(out), ensure_ascii=False, indent=2)
