"""A1 — Extractor tests. Run offline with a stub model.

The key test proves the two halves connect: A1's records feed straight into the
engine's Unit Guard, and a record whose unit disagrees with its dimensions is
caught — the extractor cannot smuggle a bad measurement downstream.
"""

import json

import pytest

from agents.a1_extractor.agent import run
from agents.a1_extractor.schema import ExtractInput, ExtractOutput
from engine.units import Quantity, Unit
from engine.unit_guard import TakeoffRecord, check


def stub(records):
    return lambda system, user: json.dumps({"records": records})


def test_extracts_and_validates_a_wall():
    model = stub([
        {
            "description": "Plaster to wall W1",
            "trade": "plaster",
            "count": 1,
            "dimensions_m": [6.0, 3.0],
            "unit": "m2",
            "source_drawing": "A-201",
            "source_sheet": "3 of 8",
            "source_revision": "C",
            "confidence": "high",
            "notes": "",
        }
    ])
    out = run(ExtractInput("A-201", "3 of 8", "C", "plaster"), "…", model=model)
    assert isinstance(out, ExtractOutput)
    assert len(out.records) == 1
    assert out.records[0].unit == "m2"


def test_prompt_metadata_reaches_the_model():
    captured = {}

    def model(system, user):
        captured["system"] = system
        captured["user"] = user
        return json.dumps({"records": []})

    run(ExtractInput("A-201", "3 of 8", "C", "plaster"), "content", model=model)
    assert "one job" in captured["system"]  # prompt.md loaded
    assert "A-201" in captured["user"]
    assert "Revision: C" in captured["user"]


def test_unit_that_disagrees_with_dimensions_is_rejected():
    # 2 dimensions but claims 'm' — schema validation must reject it.
    model = stub([
        {
            "description": "bad line",
            "trade": "plaster",
            "count": 1,
            "dimensions_m": [6.0, 3.0],
            "unit": "m",
        }
    ])
    with pytest.raises(ValueError):
        run(ExtractInput("A-201"), "…", model=model)


def test_records_flow_into_the_unit_guard():
    model = stub([
        {
            "description": "Plaster to wall W1",
            "trade": "plaster",
            "count": 1,
            "dimensions_m": [6.0, 3.0],
            "unit": "m2",
        }
    ])
    out = run(ExtractInput("A-201"), "…", model=model)
    r = out.records[0]
    guard = check(
        TakeoffRecord(
            description=r.description,
            count=r.count,
            dimensions=[Quantity(d, Unit.LENGTH) for d in r.dimensions_m],
            claimed_unit=Unit(r.unit),
        )
    )
    assert guard.ok
    assert guard.computed == Quantity(18.0, Unit.AREA)
