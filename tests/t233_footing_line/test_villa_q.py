"""T-233 hand-calculated fixture, villa Q (not Alsenan): three footing types including a combined footing with its
own schedule row; one outline clipped by its neighbour; one rotated (L / W swapped); one on the plot line.

Hand calculation (m, m2, m3):
  schedule FA 1.20 x 1.00 x 0.40, FB 2.00 x 1.50 x 0.50, CF1 (combined, own row) 3.60 x 1.40 x 0.60
  FA x 3 (one drawn 1.00 x 1.20): 3 x 0.48 = 1.440
  FB-1 full: 1.500; FB-2 clipped at a corner by FA-3 (0.20 x 0.30 = 0.06 m2): 2.94 x 0.50 = 1.470
  CF1: 3.024                                             footings total 7.434
  blinding, projection 0.10, thickness 0.10:
    FA 1.40 x 1.20 = 1.68 x 3 = 5.04; FB-1 2.20 x 1.70 = 3.74; FB-2 3.74 - 0.06 = 3.68; CF1 3.80 x 1.60 = 6.08
    sum 18.54; FA-3 / FB-2 grown plans overlap [1.7, 2.1] x [1.1, 1.6] less the notch 0.2 x 0.3 = 0.14
    union 18.40; CF1 projection beyond the plot line 3.80 x 0.10 = 0.38 (HELD 0 .. 0.038 m3)
    measured (18.40 - 0.38) x 0.10 = 1.802
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
from shapely.geometry import box

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t233"))
import footing_line as FL  # noqa: E402

SCHED = {"FA": FL.ScheduleRow("FA", 1.20, 1.00, 0.40), "FB": FL.ScheduleRow("FB", 2.00, 1.50, 0.50),
         "CF1": FL.ScheduleRow("CF1", 3.60, 1.40, 0.60)}


def _outlines():
    fb2 = box(0, 0, 2.0, 1.5).difference(box(1.8, 1.2, 2.0, 1.5))
    fa3 = box(1.8, 1.2, 3.0, 2.2)
    g_fb2, g_fa3 = fb2.buffer(0.10, join_style=2), fa3.buffer(0.10, join_style=2)
    assert g_fb2.area == pytest.approx(3.68) and g_fb2.intersection(g_fa3).area == pytest.approx(0.14)
    return [
        FL.Outline("FA-1", ("FA",), 1.20, 1.00, 1.20, blind_m2=1.68),
        FL.Outline("FA-2", ("FA",), 1.00, 1.20, 1.20, blind_m2=1.68),           # rotated / mirrored: L and W swapped
        FL.Outline("FA-3", ("FA",), 1.20, 1.00, fa3.area, blind_m2=g_fa3.area),
        FL.Outline("FB-1", ("FB",), 2.00, 1.50, 3.00, blind_m2=3.74),
        FL.Outline("FB-2", ("FB",), 2.00, 1.50, fb2.area, clipped_by=("FA-3",), blind_m2=g_fb2.area),
        FL.Outline("CF1-1", ("CF1",), 3.60, 1.40, 5.04, blind_m2=6.08, blind_outside_m2=0.38),
    ]


def test_footing_table_by_hand():
    res = FL.footing_line(_outlines(), SCHED)
    assert res.measured_m3 == pytest.approx(7.434, abs=1e-9)
    assert res.by_type == {"FA": (3, 1.44), "FB": (2, 2.97), "CF1": (1, 3.024)}
    st = {r.outline: r.status for r in res.rows}
    assert st["FA-2"] == "AGREE" and st["FB-2"] == "CLIPPED" and st["CF1-1"] == "AGREE"
    assert res.closable


def test_blinding_by_hand_union_and_boundary():
    outl = _outlines()
    fres = FL.footing_line(outl, SCHED)
    bres = FL.blinding_line(outl, fres, projection_m=0.10, thickness_m=0.10, union_m2_measured=18.40)
    assert bres.by_type["plan_sum_m2"] == pytest.approx(18.54)
    assert bres.by_type["overlap_once_m2"] == pytest.approx(0.14)
    assert bres.measured_m3 == pytest.approx(1.802, abs=1e-9)
    assert bres.held == [("BLINDING-OUTSIDE-BOUNDARY", "projection beyond the plot line (designer item)",
                          (0.0, 0.038))]


def test_adverse_footing_under_two_types_refused():
    outl = _outlines() + [FL.Outline("FA-1", ("FB",), 1.20, 1.00, 1.20, blind_m2=1.68)]
    with pytest.raises(FL.RefusedError, match="listed twice"):
        FL.footing_line(outl, SCHED)


def test_adverse_two_tags_one_outline_held_never_in_total():
    outl = _outlines()[:2] + [FL.Outline("X", ("FA", "FB"), 3.20, 1.50, 4.80, blind_m2=5.94)]
    res = FL.footing_line(outl, SCHED)
    row = [r for r in res.rows if r.outline == "X"][0]
    assert row.status == "HELD" and row.m3 is None
    # (A) rows separately 0.48 + 1.50 = 1.98; (B) outline 4.80 x deepest H 0.50 = 2.40
    assert row.m3_range == (1.98, 2.4)
    assert res.measured_m3 == pytest.approx(0.96) and not res.closable


def test_adverse_blinding_without_printed_projection_refused():
    outl = _outlines()
    outl[0] = FL.Outline("FA-1", ("FA",), 1.20, 1.00, 1.20, blind_m2=1.20)    # footing plan offered as blinding
    fres = FL.footing_line(outl, SCHED)
    with pytest.raises(FL.RefusedError, match="projection"):
        FL.blinding_line(outl, fres, projection_m=0.10, thickness_m=0.10)


def test_adverse_underlay_as_concrete_refused():
    outl = _outlines() + [FL.Outline("SCR-1", ("FA",), 1.20, 1.00, 1.20, element_class="SCREED", blind_m2=1.68)]
    with pytest.raises(FL.RefusedError, match="not footing concrete"):
        FL.footing_line(outl, SCHED)


def test_adverse_held_is_never_zero():
    fres = FL.footing_line(_outlines(), SCHED)
    m, held, verdict = FL.keyed_line({"footings": (fres.measured_m3, fres.held), "straps": None})
    assert m == pytest.approx(7.434) and held == [("straps", "not measured", None)]
    assert verdict.startswith("NOT CLOSABLE")
    nb = FL.blinding_line(_outlines(), fres, projection_m=None, thickness_m=0.10)
    assert nb.measured_m3 == 0.0 and nb.held and nb.held[0][2] is None     # HELD, no number invented


def test_adverse_drawn_size_conflict_is_a_range():
    outl = [FL.Outline("FB-9", ("FB",), 2.45, 1.50, 3.675, blind_m2=4.625)]
    res = FL.footing_line(outl, SCHED)
    assert res.rows[0].status == "CONFLICT" and res.rows[0].m3 is None
    assert res.rows[0].m3_range == (1.5, 1.8375)


def test_adverse_clip_without_neighbour_is_conflict():
    outl = [FL.Outline("FB-8", ("FB",), 2.00, 1.50, 2.94, blind_m2=3.68)]
    res = FL.footing_line(outl, SCHED)
    assert res.rows[0].status == "CONFLICT"


def test_adverse_units_mm_refused():
    with pytest.raises(FL.RefusedError, match="metres"):
        FL.footing_line([FL.Outline("FA-mm", ("FA",), 1200.0, 1000.0, 1.2e6, blind_m2=1.68e6)], SCHED)


def test_adverse_union_above_sum_refused():
    outl = _outlines()
    fres = FL.footing_line(outl, SCHED)
    with pytest.raises(FL.RefusedError, match="union"):
        FL.blinding_line(outl, fres, projection_m=0.10, thickness_m=0.10, union_m2_measured=19.0)


def test_held_footing_keeps_blinding_held():
    outl = _outlines()[:1] + [FL.Outline("X", ("FA", "FB"), 3.20, 1.50, 4.80, blind_m2=5.94, blind_outside_m2=0.32)]
    fres = FL.footing_line(outl, SCHED)
    b = FL.blinding_line(outl, fres, projection_m=0.10, thickness_m=0.10, schedule=SCHED)
    assert b.measured_m3 == pytest.approx(0.168)
    # inside the boundary 5.62 m2 .. max(outline 5.94, rows separately 1.68 + 3.74 = 5.42) -> 0.562 .. 0.594
    assert b.held == [("X", "follows its footing (HELD)", (0.562, 0.594))]
