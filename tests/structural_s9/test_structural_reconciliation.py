"""engine/source/structural_reconciliation.py - synthetic known answers (no project data)."""

from __future__ import annotations

import math
import random

import pytest

from engine.source import structural_reconciliation as SR


def test_polygon_area_orientation_closure_and_holes():
    sq = [(0, 0), (4, 0), (4, 3), (0, 3)]
    assert SR.polygon_area(sq) == pytest.approx(12.0)
    assert SR.polygon_area(list(reversed(sq))) == pytest.approx(12.0)
    assert SR.polygon_area(sq + [sq[0]]) == pytest.approx(12.0)
    L = [(0, 0), (3, 0), (3, 1), (1, 1), (1, 3), (0, 3)]
    assert SR.polygon_area(L) == pytest.approx(5.0)
    assert SR.polygon_area_with_holes(sq, [[(1, 1), (2, 1), (2, 2), (1, 2)]]) == pytest.approx(11.0)
    with pytest.raises(SR.ReconciliationError):
        SR.polygon_area([(0, 0), (1, 1)])
    with pytest.raises(SR.ReconciliationError):
        SR.polygon_area_with_holes([(0, 0), (1, 0), (1, 1)], [sq])
    rnd = random.Random(3)                                   # regular n-gons: (n/2) r^2 sin(2 pi / n)
    for _ in range(50):
        n, r = rnd.randint(3, 40), rnd.uniform(0.5, 9)
        pts = [(r * math.cos(2 * math.pi * k / n), r * math.sin(2 * math.pi * k / n)) for k in range(n)]
        assert SR.polygon_area(pts) == pytest.approx(n / 2 * r * r * math.sin(2 * math.pi / n))


def test_rect_overlap_and_prism():
    assert SR.rect_overlap((0, 0, 4, 3), (3, 2, 6, 6)) == pytest.approx(1.0)
    assert SR.rect_overlap((0, 0, 1, 1), (1, 0, 2, 1)) == 0.0           # touching is not overlapping
    assert SR.rect_overlap((4, 3, 0, 0), (3, 6, 6, 2)) == pytest.approx(1.0)
    assert SR.prism(4.6, 4.5, 0.55) == pytest.approx(11.385)
    with pytest.raises(SR.ReconciliationError):
        SR.prism(1.0, None, 0.3)                                       # missing is never zero
    with pytest.raises(SR.ReconciliationError):
        SR.prism(1.0, -1.0, 0.3)


def test_resolve_chain_precedence():
    r = SR.resolve_chain([("S5", SR.BASELINE, 100.0), ("S5.1", SR.DELTA, 10.0), ("AD1", SR.CORRECTION, -4.0),
                          ("D1.2", SR.STATE_ONLY, None), ("D1.1", SR.CORRECTION, -6.0)])
    assert r["authoritative"] == pytest.approx(100.0) and r["holder"] == "D1.1"
    assert r["superseded"] == ["S5", "S5.1", "AD1"]
    s = SR.resolve_chain([("S8.6", SR.BASELINE, 0.745), ("S8.6A", SR.SUPERSEDING, 0.366)])
    assert s["authoritative"] == pytest.approx(0.366) and s["superseded"] == ["S8.6"]      # never added together
    with pytest.raises(SR.ReconciliationError):
        SR.resolve_chain([("X", SR.BASELINE, 1.0), ("Y", SR.CORRECTION, 0.5)])             # an erratum never adds
    with pytest.raises(SR.ReconciliationError):
        SR.resolve_chain([("X", SR.BASELINE, 1.0), ("Y", SR.DELTA, -0.5)])
    with pytest.raises(SR.ReconciliationError):
        SR.resolve_chain([("X", SR.BASELINE, 1.0), ("Y", SR.QA_ONLY, 0.5)])
    with pytest.raises(SR.ReconciliationError):
        SR.resolve_chain([("Y", SR.DELTA, 1.0)])


def test_single_owner_and_lane_safe_totals():
    comps = [{"COMPONENT_ID": "A", "OWNER_FAMILY": "F1"}, {"COMPONENT_ID": "B", "OWNER_FAMILY": "F2"}]
    assert SR.assert_single_owner(comps) == 2
    with pytest.raises(SR.ReconciliationError):
        SR.assert_single_owner(comps + [{"COMPONENT_ID": "A", "OWNER_FAMILY": "F3"}])
    with pytest.raises(SR.ReconciliationError):
        SR.assert_single_owner([{"COMPONENT_ID": "C", "OWNER_FAMILY": ""}])
    rows = [{"v": 2.0, "lane": "REL", "f": "x"}, {"v": 3.0, "lane": "COND", "f": "x"}, {"v": None, "lane": "BLK", "f": "y"},
            {"v": 1.5, "lane": "REL", "f": "y"}]
    t = SR.eligible_total(rows, "v", "lane", ("REL",))
    assert t == {"total": pytest.approx(3.5), "non_eligible_rows_with_value": 1}
    assert SR.group_totals(rows, ("f",), "v", "lane", ("REL",)) == {("x",): 2.0, ("y",): 1.5}
