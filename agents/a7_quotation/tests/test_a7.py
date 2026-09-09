"""A7 — Quotation Writer tests (offline)."""

import json

import pytest

from agents.a7_quotation.agent import run
from agents.a7_quotation.schema import QuotationInput, BOQLine


def _input():
    return QuotationInput(
        client_name="Al Fahad",
        project="Villa, Sabah Al Salem",
        contract_form="turnkey",
        boq=[BOQLine("Plaster", 120.0, "m2", 2.5, 300.0)],
        grand_total=300.0,
    )


def test_writes_quotation_and_passes_boq_numbers():
    captured = {}

    def model(s, u):
        captured["user"] = u
        return json.dumps({"quotation_ar": "عرض سعر ...", "exclusions": ["الأثاث"]})

    out = run(_input(), model=model)
    assert out.quotation_ar
    assert "300.0" in captured["user"]  # exact numbers reach the model to echo


def test_empty_quotation_rejected():
    with pytest.raises(ValueError):
        run(_input(), model=lambda s, u: json.dumps({"quotation_ar": ""}))
