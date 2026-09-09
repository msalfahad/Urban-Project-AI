"""A7 — Quotation Writer runner.

Serialises the approved BOQ into the user turn so the model has exact numbers to
echo. The numbers are computed by the engine, never here.
"""

from __future__ import annotations

import json
from pathlib import Path

from agents.base import ModelFn, run_json_agent
from .schema import QuotationInput, QuotationOutput

PROMPT_PATH = Path(__file__).parent / "prompt.md"
MODEL = "claude-opus-5"


def run(payload: QuotationInput, model: ModelFn | None = None) -> QuotationOutput:
    boq = [
        {
            "description": l.description,
            "quantity": l.quantity,
            "unit": l.unit,
            "rate": l.rate,
            "line_total": l.line_total,
        }
        for l in payload.boq
    ]
    user = (
        f"Client: {payload.client_name}\n"
        f"Project: {payload.project}\n"
        f"Contract form: {payload.contract_form}\n"
        f"Currency: {payload.currency}\n"
        f"Grand total: {payload.grand_total}\n\n"
        f"Approved BOQ (echo these exactly):\n{json.dumps(boq, ensure_ascii=False, indent=2)}\n"
    )
    return run_json_agent(PROMPT_PATH, user, QuotationOutput.from_dict, model=model)
