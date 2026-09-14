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
