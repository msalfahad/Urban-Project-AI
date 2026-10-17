"""A6 — Planner tests (offline)."""

import json

import pytest

from agents.a6_planner.agent import run
from agents.a6_planner.schema import PlanInput


def test_builds_a_dependency_graph():
    model = lambda s, u: json.dumps({"activities": [
        {"id": "foundations", "name": "Foundations"},
        {"id": "frame", "name": "Concrete frame", "depends_on": ["foundations"]},
    ]})
    out = run(PlanInput("turnkey", area_m2=400, floors=2), model=model)
    assert len(out.activities) == 2
    assert out.activities[1].depends_on == ["foundations"]


def test_dependency_on_unknown_activity_is_rejected():
    model = lambda s, u: json.dumps({"activities": [
        {"id": "frame", "name": "Frame", "depends_on": ["ghost"]},
    ]})
    with pytest.raises(ValueError):
        run(PlanInput("turnkey"), model=model)


def test_duplicate_ids_rejected():
    model = lambda s, u: json.dumps({"activities": [
        {"id": "x", "name": "A"}, {"id": "x", "name": "B"},
    ]})
    with pytest.raises(ValueError):
        run(PlanInput("finishing"), model=model)
