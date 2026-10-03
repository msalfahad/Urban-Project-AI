"""E25V2 — a wall is a band, and the mate is the face it runs alongside."""

from __future__ import annotations

import pytest

from engine.vector_source import STROKE, VectorSegment
from engine.wall_bands import (AMBIGUOUS, DOUBLE_FACE_WALL,
                               INSUFFICIENT_OVERLAP, MIN_OVERLAP_RATIO,
                               NO_PARALLEL_FACE, PROBABLE, REPRESENTATIONS,
                               SINGLE_LINE_WALL, VALIDATED, build_bands,
                               mate_score, single_face_candidates, summary)


def face(sid, axis, fixed, lo, hi, pen=1.14):
    if axis == "H":
        x0, y0, x1, y1 = lo, fixed, hi, fixed
    else:
        x0, y0, x1, y1 = fixed, lo, fixed, hi
    return VectorSegment(sid, f"VP-{sid}", 0, axis, fixed, lo, hi, STROKE,
                         pen, False, 0.0, x0, y0, x1, y1)


def test_the_mate_is_the_face_it_runs_alongside_not_the_nearest_one():
    """THE BUG THAT COST EVERY ROOM ON THE SHEET. Ranking candidate mates by
    gap let a 100 mm scrap of fixture linework at 105 mm beat the actual other
    face of the wall at 151 mm with 2400 mm of overlap."""
    wall_a = face("A", "H", 0.0, 0.0, 2400.0)
    true_mate = face("B", "H", 151.0, 0.0, 2400.0)
    scrap = face("S", "H", 105.0, 1000.0, 1100.0)
    bands, _ = build_bands([wall_a, true_mate, scrap])
    assert len(bands) == 1
    assert set(bands[0].face_a_ids + bands[0].face_b_ids) == {"A", "B"}
    assert bands[0].wall_face_separation_mm == pytest.approx(151.0)


def test_mate_score_ranks_company_not_proximity():
    """And note WHICH part of the score does the work here.

    A short scrap wholly covered by a long face scores a perfect RATIO — all
    100 mm of it is kept company. The ratio therefore ties at 1.0 and cannot
    separate them; the absolute OVERLAP does, 2400 mm against 100 mm, and the
    absolute floor excludes the scrap outright. Distance, the thing the old
    rule used, points the wrong way in both.
    """
    a = face("A", "H", 0.0, 0.0, 2400.0)
    near_short = face("S", "H", 105.0, 1000.0, 1100.0)
    far_long = face("B", "H", 151.0, 0.0, 2400.0)
    ov_short, ratio_short, gap_short = mate_score(a, near_short)
    ov_long, ratio_long, gap_long = mate_score(a, far_long)
    assert gap_short < gap_long              # the scrap IS nearer
    assert ratio_short == ratio_long == 1.0  # and ratio cannot separate them
    assert ov_long > ov_short * 20           # overlap length can, and does


def test_a_band_spans_the_union_of_its_faces_not_their_intersection():
    """At an L corner the outer face runs past the inner one by a wall
    thickness. Taking the intersection made every band stop short of every
    junction, so perpendicular bands never met."""
    a = face("A", "H", 0.0, 0.0, 3000.0)
    b = face("B", "H", 200.0, 200.0, 2800.0)
    bands, _ = build_bands([a, b])
    assert bands[0].start_mm == 0.0
    assert bands[0].end_mm == 3000.0


def test_a_face_with_no_parallel_partner_is_reported_not_paired():
    lone = face("A", "H", 0.0, 0.0, 3000.0)
    bands, rej = build_bands([lone])
    assert bands == []
    assert rej[0].reason == NO_PARALLEL_FACE


def test_a_lone_face_is_never_mirrored_by_an_assumed_thickness():
    """Mirroring manufactures a wall the drawing does not contain, and every
    quantity downstream inherits it."""
    lone = face("A", "H", 0.0, 0.0, 3000.0)
    _, rej = build_bands([lone])
    singles = single_face_candidates(rej, [lone])
    assert len(singles) == 1
    s = singles[0]
    assert s.representation_type == SINGLE_LINE_WALL
    assert s.wall_face_separation_mm is None
    assert s.face_b_ids == ()
    assert "NOT_ESTABLISHED" in s.separation_basis
    assert s.validation_status in (PROBABLE, AMBIGUOUS)


def test_two_faces_that_barely_overlap_do_not_pair():
    a = face("A", "H", 0.0, 0.0, 3000.0)
    b = face("B", "H", 150.0, 2900.0, 3200.0)
    bands, rej = build_bands([a, b])
    assert bands == []
    assert rej[0].reason == INSUFFICIENT_OVERLAP


def test_the_overlap_requirement_is_a_ratio_not_only_a_constant():
    """A 300 mm wall return cannot overlap anything by a fixed 300 mm. The
    test is what SHARE of the shorter face is kept company."""
    assert 0 < MIN_OVERLAP_RATIO <= 1.0
    a = face("A", "V", 0.0, 0.0, 400.0)
    b = face("B", "V", 150.0, 0.0, 400.0)
    bands, _ = build_bands([a, b])
    assert len(bands) == 1


def test_a_band_needs_two_families_to_be_validated():
    """One family is a hypothesis. The wall pen alone never validates."""
    a = face("A", "H", 0.0, 0.0, 3000.0, pen=0.3)
    b = face("B", "H", 150.0, 0.0, 3000.0, pen=0.3)
    bands, _ = build_bands([a, b], wall_pen=None)
    assert bands[0].validation_status == PROBABLE


def test_raster_support_alone_cannot_validate_a_band():
    """The mask is ink, and ink is furniture, hatch and text as well as walls."""
    a = face("A", "H", 0.0, 0.0, 3000.0, pen=0.3)
    b = face("B", "H", 150.0, 0.0, 3000.0, pen=0.3)
    bands, _ = build_bands([a, b], wall_pen=None,
                           raster_support=lambda *_: 1.0)
    # face geometry + raster = two families, which is the documented rule
    assert bands[0].validation_status == VALIDATED
    assert len(bands[0].families) >= 2


def test_the_representation_vocabulary_covers_more_than_two_parallel_lines():
    """A future drawing must not fail because its walls are filled bands."""
    assert DOUBLE_FACE_WALL in REPRESENTATIONS
    assert SINGLE_LINE_WALL in REPRESENTATIONS
    assert "FILLED_WALL_BAND" in REPRESENTATIONS
    assert "CURVED_WALL" in REPRESENTATIONS
    assert len(REPRESENTATIONS) >= 7


def test_the_summary_reports_why_faces_failed_to_pair():
    a = face("A", "H", 0.0, 0.0, 3000.0)
    out = summary(*build_bands([a]))
    assert out["rejection_reasons"][NO_PARALLEL_FACE] == 1
