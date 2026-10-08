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
    # a larger cover, a thicker link or a smaller section only shortens it (monotone lower bound)
    assert LG.core_path_mm(200, 400, 30, 8) < 968.0 < LG.core_path_mm(220, 400, 25, 8)
    assert LG.core_path_mm(200, 400, 25, 10) < 968.0
    with pytest.raises(LG.LinkGeometryError):
        LG.core_path_mm(60, 400, 25, 12)
    with pytest.raises(LG.LinkGeometryError):
        LG.core_path_mm(200, 400, 0, 8)


def test_core_path_stays_below_a_rounded_link_with_its_closing_hooks():
    """Premise check: corners of centreline radius R shorten the loop by (8 - 2 pi) R, while two 135° closing hooks
    add at least 2 x (pi/4) R of arc before any extension -> the hooked link is never shorter than the core path
    once the hook extensions exceed (8 - 2 pi - pi/2) R / 2."""
    b, h, c, d = 300, 600, 25, 10
    core = LG.core_path_mm(b, h, c, d)
    for R in (2.5 * d, 4 * d):
        loop = core - (8 - 2 * math.pi) * R
        ext_needed = max(0.0, ((8 - 2 * math.pi) * R - 2 * (math.pi / 4) * R) / 2)
        assert loop + 2 * (math.pi / 4) * R + 2 * ext_needed >= core - 1e-9
        assert ext_needed < 6 * d                                 # any drawn hook extension exceeds this


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
