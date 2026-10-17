"""A13 — Contract Reader tests (offline)."""

import json

import pytest

from agents.a13_contract_reader.agent import run
from agents.a13_contract_reader.schema import ContractInput


def test_extracts_milestones():
    model = lambda s, u: json.dumps({
        "payment_milestones": [
            {"trigger": "on signing", "percent": 25},
            {"trigger": "on frame completion", "percent": 35},
        ],
        "retention": {"percent": 5, "release": "final handover"},
    })
    out = run(ContractInput("... 25% on signing ..."), model=model)
    assert len(out.payment_milestones) == 2
    assert out.payment_milestones[0].percent == 25


def test_out_of_range_percent_rejected():
    model = lambda s, u: json.dumps({
        "payment_milestones": [{"trigger": "x", "percent": 250}]
    })
    with pytest.raises(ValueError):
        run(ContractInput("x"), model=model)
