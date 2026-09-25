"""E39 — the building envelope, and the raster trap it is built to avoid."""

from __future__ import annotations

from engine.envelope import (E_BORDER_FREE_SPACE, E_BOUNDS_TWO_FACES,
                             E_ON_UNBOUNDED_FACE, E_THICK_FOR_EXTERNAL,
                             EXTERNAL, INTERNAL, MIN_FAMILIES_FOR_VALIDATED,
                             UNRESOLVED, classify, summary)
from engine.wall_graph import WallEdge


def edge(eid, sep=200.0):
    return WallEdge(edge_id=eid, axis="H", centreline_mm=0.0, start_mm=0.0,
                    end_mm=1000.0, face_a_mm=-sep / 2, face_b_mm=sep / 2,
                    pair_id="WP-1", wall_face_separation_mm=sep)


def test_raster_free_space_alone_never_classifies_a_wall_external():
    """A terrace, a light well and an unclosed room all reach the sheet
    border. A courtyard reaches nothing while being outside."""
    out = classify([edge("A", sep=150.0)], border_free_edge_ids=["A"])
    assert out[0].classification == UNRESOLVED
    assert len(out[0].families) < MIN_FAMILIES_FOR_VALIDATED


def test_two_independent_families_validate_external():
    out = classify([edge("A", sep=300.0)], unbounded_edge_ids=["A"],
                   border_free_edge_ids=["A"])
    assert out[0].classification == EXTERNAL
    assert out[0].validated


def test_rooms_on_both_sides_is_internal_whatever_the_thickness():
    """A 300 mm party wall with a room each side is internal."""
    out = classify([edge("A", sep=300.0)], bounded_edge_counts={"A": 2})
    assert out[0].classification == INTERNAL


def test_thickness_alone_is_evidence_never_a_classification():
    """A 250 mm internal party wall exists and so does a 200 mm external one."""
    out = classify([edge("A", sep=300.0)])
    assert out[0].classification == UNRESOLVED
    assert "never a classification" in out[0].why


def test_a_wall_with_no_evidence_is_unresolved_not_internal_by_default():
    out = classify([edge("A", sep=200.0)])
    assert out[0].classification == UNRESOLVED


def test_the_summary_says_how_many_rest_on_a_single_family():
    out = summary(classify([edge("A", sep=300.0), edge("B", sep=100.0)]))
    assert "single_family_only" in out
    assert "never classifies alone" in out["note"]


def test_the_docstring_forbids_classifying_from_a_raster_union():
    import inspect

    from engine import envelope
    assert ("DO NOT CLASSIFY EXTERNAL PURELY FROM A RASTER-SPACE UNION"
            in inspect.getdoc(envelope))
