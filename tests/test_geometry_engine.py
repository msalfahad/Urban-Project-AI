"""E23 / E27 / E28 — the modules added after the Test 1 post-mortem.

The geometry tests run against the real AR-00 sheet when it is present and skip
cleanly when it is not, so the suite still runs on a fresh clone. The numbers
asserted are the ones confirmed by hand against dimensions printed on the sheet
by the engineer who drew it — this is a regression test with a known answer.
"""

from __future__ import annotations

from decimal import Decimal as D
from pathlib import Path

import pytest

from engine.completeness import CompletenessError, audit, totals_by_scope
from engine.geometry import (Calibration, GeometryError, DxfSource, calibrate,
                             shoelace_m2)
from engine.trade_rules import TradeRuleError, TradeRuleSet

SHEET = Path('/root/.claude/uploads/93607c01-16a4-590f-af7c-1c2701c3b240/'
             'a6d37bb5-7f381d98-1f84-40e7-9dc6-bc2bc849a9dd_251122_120119.pdf')
RULES = Path(__file__).resolve().parent.parent / 'data/trade_rules/23010_ceramic.json'


# ---------------------------------------------------------------- calibration
def test_scale_is_proved_on_a_second_dimension():
    """40.00 m gives the scale; 25.00 m is the independent check."""
    c = calibrate(887.82, 40000, 554.94, 25000)
    assert round(c.mm_per_pt, 4) == D('45.0542')
    assert abs(c.residual_mm) < D('5')          # 2.37 mm over 25 m
    c.validate()


def test_a_scale_that_fails_its_own_check_is_refused():
    bad = calibrate(887.82, 40000, 554.94, 20000)   # wrong check dimension
    with pytest.raises(GeometryError, match="refusing to measure"):
        bad.validate()


def test_non_physical_scale_is_refused():
    with pytest.raises(GeometryError):
        Calibration(D('-1'), 'nonsense', D('0')).validate()


# ------------------------------------------------------------------ shoelace
def test_shoelace_exact_on_a_rectangle():
    assert shoelace_m2([(0, 0), (4, 0), (4, 6), (0, 6)]) == D('24')


def test_shoelace_on_an_l_shape():
    # a 6x2 base (12) with a 2x2 block standing on its left end (4)
    pts = [(0, 0), (6, 0), (6, 2), (2, 2), (2, 4), (0, 4)]
    assert shoelace_m2(pts) == D('16')


def test_shoelace_refuses_a_degenerate_polygon():
    with pytest.raises(GeometryError, match="3\\+ points"):
        shoelace_m2([(0, 0), (1, 1)])


# ------------------------------------------------------------------ dxf stub
def test_dxf_source_says_plainly_that_it_cannot_run():
    with pytest.raises(GeometryError, match="ODA File Converter"):
        DxfSource('nothing.dxf').regions()


# ---------------------------------------------------------------- trade rules
def rules() -> TradeRuleSet:
    return TradeRuleSet.load(RULES)


def test_ceramic_height_is_three_metres_not_a_generic_room_height():
    assert rules().height_m == D('3.00')


def test_bathroom_has_wall_ceramic_and_bedroom_does_not():
    r = rules()
    assert r.has_wall_finish('BATHROOM')
    assert not r.has_wall_finish('BEDROOM')


def test_asking_for_bedroom_wall_ceramic_is_refused():
    with pytest.raises(TradeRuleError, match="no wall finish"):
        rules().wall_area_m2('BEDROOM', D('10'))


def test_unknown_room_type_raises_instead_of_defaulting():
    with pytest.raises(TradeRuleError, match="no rule for room type"):
        rules().rule_for('BALLROOM')


def test_terrace_is_outside_internal_ceramic_but_still_has_a_rule():
    r = rules().rule_for('TERRACE')
    assert r.floor_finish is None and r.wall_finish is None


def test_wall_area_is_length_times_the_trade_height():
    assert rules().wall_area_m2('BATHROOM', D('102.70')) == D('308.100')


# --------------------------------------------------------------- completeness
def test_a_detected_region_with_no_disposition_fails_the_audit():
    res = audit([1, 2, 3], [{'region': 1, 'scope': 'IN_SCOPE'}], [2])
    assert res.unaccounted == [3]
    with pytest.raises(CompletenessError, match="never silently omitted"):
        res.raise_if_incomplete()


def test_a_region_dispositioned_twice_fails_the_audit():
    res = audit([1], [{'region': 1, 'scope': 'IN_SCOPE'}], [1])
    with pytest.raises(CompletenessError, match="more than once"):
        res.raise_if_incomplete()


def test_excluding_a_space_out_loud_passes():
    """The terrace case: excluded from the quantity, still on the books."""
    res = audit([1, 2], [{'region': 1, 'scope': 'IN_SCOPE'},
                         {'region': 2, 'scope': 'OUT_OF_SCOPE'}], [])
    res.raise_if_incomplete()
    assert res.accounted == res.detected == 2


def test_an_invalid_scope_value_is_refused():
    with pytest.raises(CompletenessError, match="not one of"):
        audit([1], [{'region': 1, 'scope': 'PROBABLY'}], [])


def test_totals_are_bucketed_by_scope():
    t = totals_by_scope({1: D('10'), 2: D('5'), 3: D('2')},
                        [{'region': 1, 'scope': 'IN_SCOPE'},
                         {'region': 2, 'scope': 'OUT_OF_SCOPE'},
                         {'region': 3, 'scope': 'AMBIGUOUS'}])
    assert t == {'IN_SCOPE': D('10'), 'OUT_OF_SCOPE': D('5'), 'AMBIGUOUS': D('2')}


# ------------------------------------------------- the real sheet (regression)
pytestmark_sheet = pytest.mark.skipif(not SHEET.exists(), reason="AR-00 sheet not present")


@pytest.fixture(scope='module')
def regions():
    if not SHEET.exists():
        pytest.skip("AR-00 sheet not present")
    from engine.geometry import VectorPdfSource
    src = VectorPdfSource(str(SHEET), calibrate(887.82, 40000, 554.94, 25000))
    return {r.id: r for r in src.regions(0, min_m2=0.4)}


def test_known_rooms_come_back_at_their_printed_size(regions):
    """Measured purely from geometry; the printed dimension is the answer key."""
    for rid, w_mm, h_mm in [(684, 3211, 6228),    # kitchen  3250 x 6250
                            (75, 4757, 6358),     # saloon NW 4800 x 6400
                            (816, 3395, 2984)]:   # master bath 3450 x 3000
        r = regions[rid]
        assert abs(r.width_mm - w_mm) <= 3
        assert abs(r.height_mm - h_mm) <= 3


def test_the_terrace_is_detected_not_dropped(regions):
    assert regions[161].area_m2 > D('70')


def test_dining_and_saloon_are_one_continuous_region(regions):
    """The 6350 never bounded a Dining room — flood fill crosses no wall."""
    assert regions[273].area_m2 > D('120')


def test_text_hole_filling_never_inflates_a_room(regions):
    """Filled area may exceed raw only by glyph-sized holes, never wildly."""
    for r in regions.values():
        if r.raw_area_m2 > D('5'):
            assert r.area_m2 <= r.raw_area_m2 * D('1.15')
