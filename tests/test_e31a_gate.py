"""The E31A gates — measurable conditions, proposed before they are used."""

from __future__ import annotations

from engine.e31a_gate import (FAIL, GATES, NOT_MEASURED, PASS, evaluate)


def test_the_gates_are_measurable_not_aspirational():
    """Each names a number and the reason a face walk depends on it."""
    assert len(GATES) == 8
    for g in GATES:
        assert g.threshold and g.why_a_face_walk_needs_it
        assert g.question.endswith("?")


def test_one_connected_component_is_deliberately_not_a_gate():
    """A drawing legitimately contains shafts, detached walls and balconies.
    Forcing one component would join things the building does not join."""
    import inspect

    from engine import e31a_gate
    doc = inspect.getdoc(e31a_gate)
    assert "graph_components == 1" in doc
    assert "NOT a gate" in doc or "NOT A GATE" in doc.upper()
    assert not any("components == 1" in g.threshold for g in GATES)


def test_zero_termini_is_deliberately_not_a_gate():
    """A wall genuinely ends at an opening and at the building edge."""
    import inspect

    from engine import e31a_gate
    assert "zero termini" in inspect.getdoc(e31a_gate)


def test_an_unmeasured_gate_is_never_a_passed_gate():
    out = evaluate({})
    assert PASS not in [g["status"] for g in out["gates"]]
    assert out["ready_for_e31a"] is False


def test_a_failing_gate_blocks_readiness():
    out = evaluate({"noded_graph": {"length_difference_mm": 500.0}})
    g1 = [g for g in out["gates"] if g["gate_id"] == "G1-LENGTH"][0]
    assert g1["status"] == FAIL
    assert not out["ready_for_e31a"]


def test_the_length_gate_admits_no_percentage_tolerance():
    """A percentage would hide exactly the loss that matters."""
    assert any("== 0.0 mm" in g.threshold for g in GATES)
    out = evaluate({"noded_graph": {"length_difference_mm": 0.2}})
    assert [g for g in out["gates"] if g["gate_id"] == "G1-LENGTH"][0][
        "status"] == PASS


def test_the_verdict_names_what_is_failing_and_what_is_unmeasured():
    out = evaluate({"noded_graph": {"length_difference_mm": 500.0}})
    assert "NOT READY" in out["verdict"]
    assert out["failed"] and out["not_measured"]


def test_the_real_sheet_does_not_pass_the_gates():
    """Recorded as a test so the answer cannot quietly change: on AR-00 today
    the graph is not ready, and the three failures name why."""
    out = evaluate({
        "noded_graph": {"length_difference_mm": 0.2, "rejected_clusters": 0,
                        "UNRESOLVED_JUNCTION": 0, "CORNER_OVERLAP": 4,
                        "TRUE_CROSS_JUNCTION": 1},
        "connectivity": {"terminus_histogram": {"UNRESOLVED": 109},
                         "termini": 228,
                         "share_of_length_in_major_components_pct": 57.9,
                         "major_components": 7,
                         "cause_histogram": {"J_UNRESOLVED": 23}},
        "source": {"path_fragmentation": {
            "short_segments": 55144,
            "short_in_a_path_that_also_has_a_long_run": 993}},
    })
    assert not out["ready_for_e31a"]
    assert set(out["failed"]) == {"G3-TERMINI", "G4-MAJOR-CONNECTIVITY",
                                 "G5-EXPLAINED-DISCONNECTS"}
