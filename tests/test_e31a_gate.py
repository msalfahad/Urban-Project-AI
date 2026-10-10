"""The E31A gates — measurable conditions, proposed before they are used."""

from __future__ import annotations

from engine.e31a_gate import (ABSOLUTE_NUMERICAL_EPSILON_MM, DIAGNOSTIC, FAIL,
                              GATES, NOT_MEASURED, PASS, evaluate)


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


def test_the_length_gate_states_the_tolerance_it_actually_applies():
    """The gate said "= 0" while the implementation accepted 0.2 mm. It now
    names an ABSOLUTE epsilon — which does not grow with the drawing, so it can
    never hide a proportional loss the way a percentage would."""
    g1 = next(g for g in GATES if g.gate_id == "G1-LENGTH")
    assert "ABSOLUTE, never a percentage" in g1.threshold
    assert str(ABSOLUTE_NUMERICAL_EPSILON_MM) in g1.threshold
    assert "%" not in g1.threshold
    out = evaluate({"noded_graph": {"length_difference_mm": 0.2}})
    assert [g for g in out["gates"] if g["gate_id"] == "G1-LENGTH"][0][
        "status"] == PASS
    out = evaluate({"noded_graph": {"length_difference_mm": 50.0}})
    assert [g for g in out["gates"] if g["gate_id"] == "G1-LENGTH"][0][
        "status"] == FAIL


def test_length_concentration_is_a_diagnostic_not_a_gate():
    """80% was a number I chose, not one the building justifies. A component
    holding 90% of the metres and no cycle bounds nothing; one holding 3%
    around a shaft bounds a real room."""
    g4 = next(g for g in GATES if g.gate_id == "G4-CONCENTRATION")
    assert "DIAGNOSTIC ONLY" in g4.threshold
    out = evaluate({"connectivity": {
        "share_of_length_in_major_components_pct": 12.0,
        "major_components": 2}})
    row = next(g for g in out["gates"] if g["gate_id"] == "G4-CONCENTRATION")
    assert row["status"] == DIAGNOSTIC
    assert "G4-CONCENTRATION" not in out["failed"]
    assert "G4-CONCENTRATION" not in out["not_measured"]


def test_g8_is_measured_and_a_region_with_no_possible_cycle_fails_it():
    """The gate that checks the graph against the building rather than against
    itself. It now carries the weight G4 was wrongly given."""
    out = evaluate({"cycles_over_regions": {
        "regions_tested": 17, "regions_with_a_possible_enclosing_cycle": 14,
        "regions_with_no_possible_enclosing_cycle": 3,
        "total_independent_cycles": 43, "components_with_cycles": 12,
        "basis": "NECESSARY_CONDITION_ONLY"}})
    row = next(g for g in out["gates"]
               if g["gate_id"] == "G8-CYCLES-IN-REAL-ROOMS")
    assert row["status"] == FAIL
    assert "NECESSARY_CONDITION_ONLY" in row["note"]


def test_g8_passing_is_explicitly_not_proof():
    """A necessary condition met is not a face proved. Only extraction can
    upgrade it."""
    g8 = next(g for g in GATES if g.gate_id == "G8-CYCLES-IN-REAL-ROOMS")
    assert "NECESSARY" in g8.threshold
    assert "passing is not" in g8.threshold


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
        "cycles_over_regions": {
            "regions_tested": 17,
            "regions_with_a_possible_enclosing_cycle": 14,
            "regions_with_no_possible_enclosing_cycle": 3,
            "total_independent_cycles": 43, "components_with_cycles": 12,
            "basis": "NECESSARY_CONDITION_ONLY"},
    })
    assert not out["ready_for_e31a"]
    assert set(out["failed"]) == {"G3-TERMINI", "G5-EXPLAINED-DISCONNECTS",
                                 "G8-CYCLES-IN-REAL-ROOMS"}
    assert out["diagnostic_only"] == ["G4-CONCENTRATION"]
