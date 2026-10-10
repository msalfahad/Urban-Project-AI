"""§1/§3 — local eligibility, and the split between building and releasing."""

from __future__ import annotations

import pytest

from engine.face_eligibility import (FACE_BLOCKED, FACE_ELIGIBLE,
                                     FACE_HYPOTHESIS_ONLY,
                                     NOT_ENOUGH_LOCAL_TOPOLOGY,
                                     READY_FOR_DIAGNOSTIC_RUN,
                                     TOPOLOGY_RELEASE_BLOCKED,
                                     ComponentEligibility, EligibilityError,
                                     assess_components,
                                     engine_development_status,
                                     project_release_status)
from engine.connectivity import ComponentReport, TerminusReport


def comp(cid, edges=("A", "B", "C", "D"), cycles=1, length=20000.0):
    return ComponentReport(
        component_id=cid, edge_ids=tuple(edges), total_length_mm=length,
        bbox_mm=(0, 0, 1000, 1000), termini=0, junctions=4,
        separation_bands={}, source_object_count=4, size_class="MAJOR",
        likely_cause="A", share_of_length=1.0, independent_cycles=cycles,
        node_count=len(edges))


def test_a_component_with_a_cycle_is_eligible():
    out = assess_components(components=[comp("GC-1")], termini=[])
    assert out[0].verdict == FACE_ELIGIBLE


def test_a_tree_component_is_blocked_because_it_bounds_no_face():
    out = assess_components(components=[comp("GC-1", cycles=0)], termini=[])
    assert out[0].verdict == FACE_BLOCKED
    assert any("bounds no face" in r for r in out[0].reasons)


def test_an_unresolved_terminus_makes_a_component_hypothesis_only():
    t = TerminusReport(node_id="N1", kind="UNRESOLVED", edge_id="A",
                       x_mm=0.0, y_mm=0.0, why_not_joined="x")
    out = assess_components(components=[comp("GC-1")], termini=[t])
    assert out[0].verdict == FACE_HYPOTHESIS_ONLY
    assert out[0].unresolved_termini == 1


def test_one_bad_component_does_not_block_a_good_one_elsewhere():
    """109 unresolved termini somewhere on the sheet must not stop the engine
    working on a closed bathroom on the other side of the building."""
    t = TerminusReport(node_id="N1", kind="UNRESOLVED", edge_id="X",
                       x_mm=0.0, y_mm=0.0, why_not_joined="x")
    out = assess_components(
        components=[comp("GC-1"), comp("GC-2", edges=("X", "Y", "Z", "W"))],
        termini=[t])
    by_id = {c.component_id: c for c in out}
    assert by_id["GC-1"].verdict == FACE_ELIGIBLE
    assert by_id["GC-2"].verdict == FACE_HYPOTHESIS_ONLY


def test_global_length_drift_blocks_every_component():
    """A wall that vanished could have vanished from anywhere."""
    out = assess_components(components=[comp("GC-1")], termini=[],
                            length_drift_mm=50.0)
    assert out[0].verdict == FACE_BLOCKED


def test_a_refusal_must_name_a_reason():
    with pytest.raises(EligibilityError, match="no reason"):
        ComponentEligibility("GC-1", FACE_BLOCKED, 4, 0, 0, 0, 0, 0, 1.0)


def test_building_the_engine_and_releasing_from_it_are_separate_questions():
    elig = assess_components(components=[comp("GC-1")], termini=[])
    dev = engine_development_status(elig)
    rel = project_release_status({"failed": ["G3-TERMINI"]}, elig)
    assert dev["E31A_ENGINE_DEVELOPMENT_STATUS"] == READY_FOR_DIAGNOSTIC_RUN
    assert rel["PROJECT_TOPOLOGY_RELEASE_STATUS"] == TOPOLOGY_RELEASE_BLOCKED


def test_no_cycle_anywhere_means_there_is_nothing_to_build_on():
    elig = assess_components(components=[comp("GC-1", cycles=0)], termini=[])
    assert engine_development_status(elig)[
        "E31A_ENGINE_DEVELOPMENT_STATUS"] == NOT_ENOUGH_LOCAL_TOPOLOGY


def test_release_gates_are_not_weakened_by_local_eligibility():
    """Every face is unreleasable by construction; a clean local run does not
    change that."""
    elig = assess_components(components=[comp("GC-1")], termini=[])
    rel = project_release_status({"failed": ["G3-TERMINI"]}, elig)
    assert rel["blockers"]
    assert "unreleasable by construction" in rel["why"]


def test_a_component_records_which_in_scope_spaces_it_affects():
    """Connectivity effort should go where it unlocks a room, not to a 20 mm
    annotation fragment."""
    out = assess_components(components=[comp("GC-1")], termini=[],
                            region_points={"BTH-01": (500.0, 500.0),
                                           "FAR-01": (90000.0, 90000.0)})
    assert out[0].affected_space_ids == ("BTH-01",)
