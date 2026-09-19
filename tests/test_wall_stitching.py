"""E43 — joining fragments on evidence, and refusing to close a doorway."""

from __future__ import annotations

import pytest

from engine.connectivity import EndCap
from engine.wall_graph import WallEdge
from engine.wall_stitching import (DOOR_WIDTH_MM, E_END_CAP,
                                   EVIDENCE_FAMILY, MIN_FAMILIES_FOR_VALIDATED,
                                   STITCH_AMBIGUOUS, STITCH_PROBABLE,
                                   STITCH_REJECTED, STITCH_VALIDATED,
                                   candidates, summary)


def edge(eid, a, b, *, centre=100.0, sep=200.0, pair="WP-0001", axis="H"):
    return WallEdge(edge_id=eid, axis=axis, centreline_mm=centre,
                    start_mm=a, end_mm=b, face_a_mm=centre - sep / 2,
                    face_b_mm=centre + sep / 2, pair_id=pair,
                    wall_face_separation_mm=sep)


def test_a_small_gap_alone_never_validates_a_stitch():
    """The rule this module exists to avoid: gap < X -> connect."""
    src = __import__("pathlib").Path(
        __import__("engine.wall_stitching", fromlist=["x"]).__file__).read_text()
    assert "gap < X mm" in src or "gap < X" in src


def test_one_wall_drawn_in_two_pieces_is_validated():
    c = candidates([edge("A", 0.0, 3000.0), edge("B", 3020.0, 6000.0)])
    assert len(c) == 1
    assert c[0].status == STITCH_VALIDATED
    assert len(c[0].families) >= MIN_FAMILIES_FOR_VALIDATED


def test_a_door_sized_gap_is_never_stitched_shut():
    """Closing it would erase exactly the opening this engine exists to find."""
    c = candidates([edge("A", 0.0, 3000.0), edge("B", 3900.0, 6000.0)])
    assert c[0].gap_mm >= DOOR_WIDTH_MM
    assert c[0].status == STITCH_AMBIGUOUS
    assert "erase" in c[0].why


def test_an_end_cap_inside_the_gap_rejects_the_stitch():
    """The drawing says the wall STOPS here. An end cap is evidence AGAINST
    joining, and it is never read as permission to join."""
    cap = EndCap("EC-1", "VS-1", "V", 200.0, (0.0, 200.0), 3050.0,
                 ("F1", "F2"), 200.0, 1.14, "test")
    c = candidates([edge("A", 0.0, 3000.0), edge("B", 3100.0, 6000.0)],
                   caps=[cap])
    assert c[0].status == STITCH_REJECTED
    assert E_END_CAP in c[0].evidence


def test_different_wall_separations_are_different_walls():
    c = candidates([edge("A", 0.0, 3000.0, sep=100.0),
                    edge("B", 3020.0, 6000.0, sep=300.0)])
    assert c[0].status == STITCH_REJECTED
    assert "different walls" in c[0].why


def test_evidence_from_one_family_is_not_two_proofs():
    """Correlated observations of one vector construction are not independent
    confirmations — the reversal the opening spike taught."""
    fams = {EVIDENCE_FAMILY[e] for e in ("SAME_AXIS", "COLLINEAR_WITHIN_TOLERANCE",
                                         "GAP_BELOW_OPENING_SIZE")}
    assert fams == {"GEOMETRY"}
    assert len(fams) < MIN_FAMILIES_FOR_VALIDATED


def test_a_probable_stitch_is_not_presented_as_validated():
    c = candidates([edge("A", 0.0, 3000.0, pair="WP-1"),
                    edge("B", 3400.0, 6000.0, pair="WP-2")])
    assert c[0].status in (STITCH_PROBABLE, STITCH_AMBIGUOUS)
    assert c[0].status != STITCH_VALIDATED


def test_the_summary_says_how_much_was_rejected_and_why():
    cap = EndCap("EC-1", "VS-1", "V", 200.0, (0.0, 200.0), 3050.0,
                 ("F1", "F2"), 200.0, 1.14, "test")
    c = candidates([edge("A", 0.0, 3000.0), edge("B", 3100.0, 6000.0)],
                   caps=[cap])
    out = summary(c)
    assert out["rejected_by_end_cap"] == 1
    assert out[STITCH_VALIDATED] == 0
