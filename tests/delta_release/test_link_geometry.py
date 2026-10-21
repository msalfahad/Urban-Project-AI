"""Generic tests: engine.source.link_geometry (synthetic sections, hand-computed answers)."""

import math

import pytest

from engine.source import link_geometry as LG


def test_single_str2_str3_topologies():
    assert LG.topology_from_closed_links(1) == {"topology": LG.SINGLE_CLOSED_LINK, "links": 1, "legs": 2}
    assert LG.topology_from_closed_links(2) == {"topology": LG.STR2, "links": 2, "legs": 4}
    assert LG.topology_from_closed_links(3) == {"topology": LG.STR3, "links": 3, "legs": 6}
    with pytest.raises(LG.LinkGeometryError):
        LG.topology_from_closed_links(4)


def test_core_path_is_the_sharp_centreline_rectangle():
    # 200 x 400, c 25, d 8 -> 2 x 142 + 2 x 342 = 968 mm
    assert LG.core_path_mm(200, 400, 25, 8) == 968.0
    # a larger cover, a thicker link or a smaller section only shortens it (monotone in the envelope)
    assert LG.core_path_mm(200, 400, 30, 8) < 968.0 < LG.core_path_mm(220, 400, 25, 8)
    assert LG.core_path_mm(200, 400, 25, 10) < 968.0
    with pytest.raises(LG.LinkGeometryError):
        LG.core_path_mm(60, 400, 25, 12)
    with pytest.raises(LG.LinkGeometryError):
        LG.core_path_mm(200, 400, 0, 8)


def test_rounded_link_is_shorter_than_the_core_path_and_hooks_are_no_proof():
    """D1.1 withdrew the D1 premise. A loop with four 90-degree bends of centreline radius R is (8 - 2 pi) R
    shorter than the sharp core path, for every R > 0. Covering that deficit with closing hooks would need a
    hook length, and no project source gives one: the sharp path is a modelled polygonal equivalent, not a
    lower bound (engine.source.delta_correction)."""
    from engine.source import delta_correction as DC
    b, h, c, d = 300, 600, 25, 10
    core = LG.core_path_mm(b, h, c, d)
    W, T = b - 2 * c - d, h - 2 * c - d
    assert core == DC.sharp_loop_mm(W, T)
    for R in (0.5 * d, 2.5 * d, 4 * d):
        assert DC.rounded_loop_mm(W, T, R) < core
        assert core - DC.rounded_loop_mm(W, T, R) == pytest.approx((8 - 2 * math.pi) * R)
    # a hook whose extension is unknown cannot promote the path, whatever its drawn angle
    assert DC.classify_link_path(hook_length_known=False) == DC.MODELLED_POLYGONAL_EQUIVALENT
    assert DC.classify_link_path(hook_length_known=True, closure_known=True) == DC.MODELLED_POLYGONAL_EQUIVALENT


def test_cb_end_leg_reaches_the_bottom_bar_level():
    # h 500, c 25, link 8, top 12, bottom 16: (500-25-8-6) - (25+8+8) = 461 - 41 = 420
    assert LG.end_leg_mm(500, 25, 8, 12, 16) == 420.0
    with pytest.raises(LG.LinkGeometryError):
        LG.end_leg_mm(80, 25, 8, 12, 16)


def test_count_lower_bound_has_no_plus_one():
    assert LG.count_lower_bound(6, 1.62) == 10                 # 9.72 -> 10
    assert LG.count_lower_bound(7, 5.45) == 39
    assert LG.count_lower_bound(10, 1.0) == 10                 # exact product: no binary-noise bump to 11
    with pytest.raises(LG.LinkGeometryError):
        LG.count_lower_bound(0, 2.0)


def test_invariant_requires_every_interpretation_to_agree():
    a = {"count": 39, "dia_mm": 8, "run_rule": ["BARS_PER_METRE", 7], "name": "FORWARD"}
    b = dict(a, name="REVERSED")
    assert LG.invariant([a, b], ("count", "dia_mm", "run_rule")) == {"count": 39, "dia_mm": 8,
                                                                     "run_rule": ["BARS_PER_METRE", 7]}
    assert LG.invariant([a, dict(b, dia_mm=10)], ("count", "dia_mm")) is None
    assert LG.invariant([], ("count",)) is None
    assert LG.invariant([dict(a, count=None)], ("count",)) is None
