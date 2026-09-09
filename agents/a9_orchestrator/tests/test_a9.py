"""A9 — Orchestrator tests (offline)."""

import json

import pytest

from agents.a9_orchestrator.agent import run
from agents.a9_orchestrator.schema import Event


def test_routes_a_variance_to_engineer():
    model = lambda s, u: json.dumps(
        {"route_to": "engineer_review", "priority": "urgent", "reason": "12% variance"}
    )
    out = run(Event("takeoff_variance", {"pct": 12}, "blocks a quote due today"), model=model)
    assert out.route_to == "engineer_review"
    assert out.priority == "urgent"


def test_invalid_route_rejected():
    model = lambda s, u: json.dumps({"route_to": "somewhere", "priority": "normal"})
    with pytest.raises(ValueError):
        run(Event("x", {}), model=model)
