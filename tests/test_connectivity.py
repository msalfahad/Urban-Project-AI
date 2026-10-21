"""E42 — explaining a disconnected graph before touching a tolerance."""

from __future__ import annotations

from pathlib import Path

import pytest

from engine.connectivity import (CAUSES, MAJOR, MICRO, SMALL, TERM_FRAGMENT,
                                 TERM_MISSING_CONNECTION, TERMINUS_KINDS,
                                 classify_termini, components, end_caps,
                                 summarise)
from engine.vector_source import AXIS_H, AXIS_V, STROKE, VectorSegment

PDF = Path("data/golden/23010/inputs/AR-00_MAR2023.pdf")


def s(sid, axis, fixed, a, b, w=1.14):
    if axis == AXIS_H:
        x0, y0, x1, y1 = a, fixed, b, fixed
    else:
        x0, y0, x1, y1 = fixed, a, fixed, b
    return VectorSegment(sid, "VP-1", 0, axis, fixed, a, b, STROKE, w, False,
                         0.0, x0, y0, x1, y1)


# Two long parallel faces 200 mm apart, closed at x = 3000 by a short mark.
CAPPED = [s("F1", AXIS_H, 0.0, 0.0, 3000.0),
          s("F2", AXIS_H, 200.0, 0.0, 3000.0),
          s("CAP", AXIS_V, 3000.0, 0.0, 200.0)]


def test_an_end_cap_is_recognised_by_geometry_not_by_being_short():
    caps = end_caps(CAPPED)
    assert len(caps) == 1
    assert caps[0].segment_id == "CAP"
    assert caps[0].separation_mm == 200.0
    assert len(caps[0].touches) == 2


def test_a_short_mark_touching_only_one_run_is_not_a_cap():
    """A wall end closes BETWEEN two faces. A stub touching one thing is a
    stub."""
    stub = [s("F1", AXIS_H, 0.0, 0.0, 3000.0),
            s("STUB", AXIS_V, 1500.0, 0.0, 200.0)]
    assert end_caps(stub) == []


def test_a_mark_too_long_to_be_a_thickness_is_not_a_cap():
    long_ = [s("F1", AXIS_H, 0.0, 0.0, 3000.0),
             s("F2", AXIS_H, 200.0, 0.0, 3000.0),
             s("X", AXIS_V, 3000.0, -2000.0, 2000.0)]
    assert all(c.segment_id != "X" for c in end_caps(long_))


def test_the_cause_list_is_the_one_the_review_asked_for():
    """Ten categories, A to J. The histogram is only readable against the
    question that was asked."""
    assert len(CAUSES) == 10
    assert CAUSES[0].startswith("A_") and CAUSES[-1].startswith("J_")


def test_every_terminus_kind_the_review_named_exists():
    assert len(TERMINUS_KINDS) == 6
    assert TERM_MISSING_CONNECTION in TERMINUS_KINDS


def test_components_are_not_counted_as_equal():
    """115 components is not 115 problems. A handful may hold nearly all the
    wall length, and the report must make that visible."""
    from decimal import Decimal as D

    from engine.topology import wall_pairs
    from engine.wall_graph import build
    from engine.wall_noding import node_and_split
    lines = [("H", 0.0, 0.0, 6000.0), ("H", 200.0, 0.0, 6000.0),
             ("V", 20000.0, 0.0, 300.0), ("V", 20200.0, 0.0, 300.0)]
    g = node_and_split(build(wall_pairs(lines, D(1))))
    comps = components(g)
    assert len(comps) >= 2
    assert comps[0].total_length_mm > comps[-1].total_length_mm
    assert {c.size_class for c in comps} <= {MAJOR, SMALL, MICRO}
    assert sum(c.share_of_length for c in comps) == pytest.approx(1.0, abs=1e-6)


def test_a_terminus_report_says_why_it_was_not_joined():
    """"228 termini" is not a diagnosis. "nearest compatible continuation is
    340 mm away with a matching separation" is a repair instruction."""
    from decimal import Decimal as D

    from engine.topology import wall_pairs
    from engine.wall_graph import build
    from engine.wall_noding import node_and_split
    # A 900 mm break — too wide to node, narrow enough to be a doorway.
    lines = [("H", 0.0, 0.0, 3000.0), ("H", 200.0, 0.0, 3000.0),
             ("H", 0.0, 3900.0, 6000.0), ("H", 200.0, 3900.0, 6000.0)]
    g = node_and_split(build(wall_pairs(lines, D(1))))
    reports = classify_termini(g)
    assert reports
    assert all(r.why_not_joined for r in reports)
    across = [r for r in reports if r.gap_mm is not None
              and 800 < r.gap_mm < 1000]
    assert across, [r.record() for r in reports]
    assert across[0].separation_difference_mm == 0.0
    assert across[0].nearest_id


def test_the_summary_reports_where_the_length_actually_is():
    from decimal import Decimal as D

    from engine.topology import wall_pairs
    from engine.wall_graph import build
    from engine.wall_noding import node_and_split
    lines = [("H", 0.0, 0.0, 6000.0), ("H", 200.0, 0.0, 6000.0)]
    g = node_and_split(build(wall_pairs(lines, D(1))))
    out = summarise(components(g), classify_termini(g))
    assert "share_of_length_in_major_components_pct" in out
    assert set(out["terminus_histogram"]) == set(TERMINUS_KINDS)


@pytest.mark.slow
@pytest.mark.skipif(not PDF.exists(), reason="audited input not present")
def test_the_real_sheet_has_wall_end_caps_at_real_wall_thicknesses():
    """157 of 185 short heavy-pen marks touch a perpendicular run. They are
    wall ENDS, and a parallel-face pairing cannot represent one — which is why
    every wall end was a break in the graph."""
    from engine.vector_source import read
    caps = end_caps(read(str(PDF)).axis_aligned())
    assert len(caps) > 100
    at_wall_pen = [c for c in caps if c.stroke_width_pt == 1.14]
    assert len(at_wall_pen) > 50


# --- dashed topology (§15) ----------------------------------------------------

def test_this_sheet_has_no_pdf_level_dash_patterns_at_all():
    """A NEGATIVE RESULT worth recording. Every stroke path on AR-00 is solid
    ("[] 0") and every fill path has no dash array. The dashed thresholds the
    space map describes were exported as EXPLODED linetypes — rows of short
    solid segments — so `VectorPath.is_dashed` is correct and finds nothing,
    and a dash pattern has to be recovered from geometry instead."""
    from engine.vector_source import read
    if not PDF.exists():
        pytest.skip("audited input not present")
    d = read(str(PDF))
    assert [s for s in d.segments if s.is_dashed] == []
    assert any(p.dashes == "[] 0" for p in d.paths)


def test_a_dashed_run_needs_repetition_not_just_two_short_marks():
    from engine.connectivity import MIN_DASHES, dashed_runs
    two = [s("A", AXIS_H, 0.0, 0.0, 100.0, 0.3),
           s("B", AXIS_H, 0.0, 200.0, 300.0, 0.3)]
    assert MIN_DASHES == 3
    assert dashed_runs(two) == []


def test_a_regular_sequence_of_short_marks_is_a_boundary_candidate():
    from engine.connectivity import (TOPOLOGY_BOUNDARY_CANDIDATE, dashed_runs)
    marks = [s(f"M{i}", AXIS_H, 0.0, i * 300.0, i * 300.0 + 150.0, 0.3)
             for i in range(6)]
    runs = dashed_runs(marks)
    assert len(runs) == 1
    assert runs[0].marks == 6
    assert runs[0].classification == TOPOLOGY_BOUNDARY_CANDIDATE
    assert runs[0].record()["boundary_type"] == "UNKNOWN"


def test_a_dashed_run_is_never_a_door_or_a_wall():
    """It is a place the architect drew a boundary that is not a solid wall.
    What kind of boundary is a separate question with its own evidence."""
    from engine.connectivity import dashed_runs
    marks = [s(f"M{i}", AXIS_H, 0.0, i * 300.0, i * 300.0 + 150.0, 0.3)
             for i in range(6)]
    r = dashed_runs(marks)[0].record()
    assert r["classification"] == "TOPOLOGY_BOUNDARY_CANDIDATE"
    assert r["boundary_type"] == "UNKNOWN"
    assert "door" not in str(r).lower() or r["boundary_type"] == "UNKNOWN"


def test_fill_paths_are_excluded_because_a_hatch_is_regular_by_construction():
    """Admitting fills filled the candidate list with glyph outlines: 197 of
    733 candidates came from paths with no stroke width at all."""
    from engine.connectivity import dashed_runs
    from engine.vector_source import FILL, VectorSegment
    fills = [VectorSegment(f"F{i}", "VP-1", 0, AXIS_H, 0.0, i * 300.0,
                           i * 300.0 + 150.0, FILL, 0.0, False, 0.0,
                           i * 300.0, 0.0, i * 300.0 + 150.0, 0.0)
             for i in range(6)]
    assert dashed_runs(fills) == []


def test_irregular_gaps_are_not_a_pattern():
    """A row of unrelated fixture ticks must not read as a drawn boundary."""
    from engine.connectivity import dashed_runs
    marks = [s("A", AXIS_H, 0.0, 0.0, 100.0, 0.3),
             s("B", AXIS_H, 0.0, 120.0, 220.0, 0.3),
             s("C", AXIS_H, 0.0, 480.0, 580.0, 0.3),
             s("D", AXIS_H, 0.0, 600.0, 700.0, 0.3)]
    assert all(r.marks < 4 for r in dashed_runs(marks))
