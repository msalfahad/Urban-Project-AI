"""A2 blind: isolation is structural, not a promise in a prompt.

The first blind test on this project showed two agents can agree and both be
missing a third of the floor. Agreement is only evidence if the second opinion
was genuinely independent — so these tests are about what CANNOT reach A2.
"""

from __future__ import annotations

import json

import pytest

from agents.a1_extractor.semantic import SemanticInput, SemanticOutput
from agents.a2_reviewer.agent import BlindIsolationError, run_blind


def geometry_input(**kw) -> SemanticInput:
    base = dict(project_id="23010", drawing_id="AR-00", drawing_revision="MAR.2023",
                floor_id="2F", scope_brief="right-hand apartment",
                geometry={"IRN-01": {"area_m2": "7.90", "label": "كوي IRON"}})
    base.update(kw)
    return SemanticInput(**base)


def stub(_system: str, _user: str) -> str:
    return json.dumps({"spaces": [{
        "space_id": "IRN-01", "semantic_label": "IRON_ROOM",
        "label_source": "PDF_TEXT", "label_confidence": "MEDIUM",
        "confidence_basis": "label + geometry + adjacency",
        "scope_status": "IN_SCOPE"}]})


def test_a_blind_pass_runs_on_drawing_and_geometry_alone():
    out = run_blind(geometry_input(), model=stub)
    assert out.spaces[0].semantic_label == "IRON_ROOM"


@pytest.mark.parametrize("leak", [
    "a1_output", "a1_result", "a1_record", "semantic_comparison", "comparison",
    "qiyal", "benchmark", "ground_truth", "manual_takeoff", "site_measured",
    "expected",
])
def test_every_answer_leaking_input_is_refused(leak):
    with pytest.raises(BlindIsolationError, match="blind pass takes"):
        run_blind(geometry_input(), model=stub, **{leak: "anything"})


def test_a_leak_hidden_inside_the_payload_is_also_refused():
    """Smuggling it into the input object must fail the same way."""
    payload = geometry_input()
    payload.qiyal_total = 395.67          # type: ignore[attr-defined]
    with pytest.raises(BlindIsolationError, match="answer the question"):
        run_blind(payload, model=stub)


def test_the_blind_prompt_is_not_a1s_prompt():
    from agents.a2_reviewer.agent import BLIND_PROMPT_PATH
    from agents.a1_extractor.agent import SEMANTIC_PROMPT_PATH
    assert BLIND_PROMPT_PATH != SEMANTIC_PROMPT_PATH
    assert BLIND_PROMPT_PATH.read_text(encoding="utf-8").strip()


def test_blind_output_uses_the_same_schema_so_fields_can_be_compared():
    out = run_blind(geometry_input(), model=stub)
    assert isinstance(out, SemanticOutput)


def test_the_blind_pass_cannot_return_geometry_either():
    def measuring_stub(_s, _u):
        return json.dumps({"spaces": [{
            "space_id": "IRN-01", "semantic_label": "IRON_ROOM",
            "label_source": "PDF_TEXT", "label_confidence": "MEDIUM",
            "confidence_basis": "x", "scope_status": "IN_SCOPE",
            "area_m2": 7.9}]})
    from agents.a1_extractor.semantic import SemanticError
    with pytest.raises(SemanticError, match="belongs to E23/E25"):
        run_blind(geometry_input(), model=measuring_stub)
