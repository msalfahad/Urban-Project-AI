"""The sanitary set is a second source, and its alignment is a claim.

A sanitary drawing put on the wrong place is worse than no sanitary
drawing: it puts a floor drain in the next room and tiles a wall nobody
asked for. So the alignment is searched for, tested, and refused when it
does not win.
"""

from __future__ import annotations

import math

import pytest

from engine import sanitary_source as ss


def _page(v_lines=(), h_lines=(), blobs=(), index=1):
    return ss.Page(index=index, width_pt=1191.0, height_pt=842.0,
                   rotation=270, v_lines=tuple(v_lines),
                   h_lines=tuple(h_lines), blobs=tuple(blobs))


def _synthetic(scale=38.0, ox=-160000.0, oy=-800000.0, orient=None):
    """A sheet drawn from known walls, so the answer is known."""
    wall_x = [0.0, 3000.0, 7000.0, 12000.0, 18000.0, 24000.0, 30000.0]
    wall_y = [0.0, 4000.0, 9000.0, 13000.0, 15000.0]
    ax = [x + ox for x in wall_x]
    ay = [y + oy for y in wall_y]
    # ROT_QUARTER: page y -> plan x, page x -> plan y
    v = [((y - oy) / scale, 0.0, 400.0) for y in ay]        # page x <- plan y
    h = [((x - ox) / scale, 0.0, 400.0) for x in ax]        # page y <- plan x
    return _page(v_lines=[(x, y0, y1) for x, y0, y1 in v],
                 h_lines=[(y, x0, x1) for y, x0, x1 in h]), ax, ay


def test_a_known_sheet_aligns_at_its_own_scale():
    page, ax, ay = _synthetic(scale=38.0)
    out = ss.align(page, wall_x=ax, wall_y=ay)
    assert out.status == ss.ESTABLISHED, out.record()
    assert out.scale_mm_per_pt == pytest.approx(38.0, abs=0.5)
    assert out.orientation == ss.ROT_QUARTER
    assert out.matched_x >= 0.9 and out.matched_y >= 0.9


def test_the_transform_puts_a_point_back_where_it_came_from():
    page, ax, ay = _synthetic(scale=38.0, ox=-160000.0, oy=-800000.0)
    out = ss.align(page, wall_x=ax, wall_y=ay)
    # the sheet point that is plan (ax[0], ay[0])
    px = (ay[0] - (-800000.0)) / 38.0
    py = (ax[0] - (-160000.0)) / 38.0
    mx, my = out.to_model(px, py)
    assert abs(mx - ax[0]) <= ss.ALIGN_TOL_MM
    assert abs(my - ay[0]) <= ss.ALIGN_TOL_MM


def test_a_sheet_of_another_building_does_not_align():
    page, ax, ay = _synthetic(scale=38.0)
    other_x = [v + 137.0 * i for i, v in enumerate(ax)]   # a different plan
    other_y = [v - 211.0 * i for i, v in enumerate(ay)]
    out = ss.align(page, wall_x=other_x, wall_y=other_y)
    assert out.status in (ss.NOT_ESTABLISHED, ss.AMBIGUOUS)


def test_an_empty_sheet_is_refused_not_guessed():
    out = ss.align(_page(), wall_x=[0.0, 1000.0], wall_y=[0.0, 1000.0])
    assert out.status == ss.NO_GEOMETRY
    assert out.scale_mm_per_pt == 0.0


def test_nothing_is_measured_through_an_alignment_that_failed():
    page, ax, ay = _synthetic()
    bad = ss.Alignment(status=ss.NOT_ESTABLISHED)
    assert ss.fixtures(page, bad) == []
    ev = ss.drainage_evidence(page, bad, polygons=[], arch_v=[], arch_h=[])
    assert ev["rows"] == [] and ev["status"] == ss.NOT_ESTABLISHED


def test_the_architecture_is_subtracted_before_anything_is_counted():
    """A wall redrawn on the drainage sheet is a wall, not drainage."""
    page, ax, ay = _synthetic(scale=38.0)
    out = ss.align(page, wall_x=ax, wall_y=ay)
    assert out.status == ss.ESTABLISHED
    kept, dropped = ss._sanitary_only(page, out, ax, ay)
    assert dropped > 0
    assert len(kept) < len(page.v_lines) + len(page.h_lines)


def test_linework_spread_evenly_names_no_wall():
    page, ax, ay = _synthetic(scale=38.0)
    out = ss.align(page, wall_x=ax, wall_y=ay)
    # a place with the sheet's own lines around it, in every direction
    x = (ax[0] + ax[-1]) / 2.0
    y = (ay[0] + ay[-1]) / 2.0
    near = ss.evidence_near(page, out, x, y, radius_mm=3000.0,
                            arch_v=[], arch_h=[])
    if near["sanitary_linework_lm"]:
        assert near["largest_quadrant_share"] <= 1.0
        if near["largest_quadrant_share"] < 0.6:
            assert not near["names_a_host_wall"]
            assert near["what_it_is_not"] == ss.NO_DIRECTION


def test_the_sanitary_source_never_claims_to_replace_the_architecture():
    src = ss.Source(name="x.pdf")
    assert src.record()["never_replaces"] == ss.DESIGN_ARCHITECTURAL
    assert src.record()["representation"] == ss.DESIGN_SANITARY


def test_a_symbol_is_never_a_tiled_wall():
    page = _page(blobs=[(100.0, 100.0, 3.0, 3.0)])
    good = ss.Alignment(status=ss.ESTABLISHED, scale_mm_per_pt=38.0,
                        orientation=ss.ROT_QUARTER)
    found = ss.fixtures(page, good)
    assert found
    assert found[0]["what_it_is"] == "A_DRAWING_SYMBOL_ON_THE_SANITARY_SHEET"
    assert "reason to tile a wall" in found[0]["what_it_is_not"]
