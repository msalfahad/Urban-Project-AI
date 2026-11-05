"""T-515 synthetic villa S (not the training villa), every figure by hand.

Schedule of villa S (invented): band A 0-150 cm 2Ø12 bottom / 2Ø10 top / 5Ø8/M; band B 151-300 cm 3Ø16 / 2Ø12 / 4Ø8/M;
printed minimum bearing 25 cm on lintels LA and LB; lintel LC has no printed bearing.
kg/m = d^2 / 162: 12 -> 144/162, 10 -> 100/162, 16 -> 256/162, 8 -> 64/162.
  LA  w 1.20, band A: span (2 x 144 + 2 x 100)/162 x 1.20 = 488/162 x 1.2 = 3.614815 kg; L 1.70; ceiling 488/162 x 1.7
      = 5.120988 kg; links ceil(5 x 1.70) = 9 over L, ceil(5 x 1.20) = 6 over the span.
  LB  w 2.40, band B: span (3 x 256 + 2 x 144)/162 x 2.40 = 1056/162 x 2.4 = 15.644444 kg; L 2.90; ceiling 18.903704 kg;
      links ceil(4 x 2.9) = 12 over L, ceil(4 x 2.4) = 10 over the span.
  LC  w 0.90, band A, no bearing: span 488/162 x 0.9 = 2.711111 kg; L unknown: in-bearing HELD with no ceiling, links over
      L HELD (None), ceil(5 x 0.9) = 5 over the span; laps HELD (no run ceiling).
  project AT_LEAST 3.614815 + 15.644444 + 2.711111 = 21.970370 kg = 0.021970 t; never a full figure.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research" / "agents_t515"))

import t515_lintel_bars as T  # noqa: E402


def villa():
    a = dict(bottom="2Ø12", top="2Ø10", stirrups="5Ø8/M", schedule_row="A", band_lo_m=0.0, band_hi_m=1.5)
    b = dict(bottom="3Ø16", top="2Ø12", stirrups="4Ø8/M", schedule_row="B", band_lo_m=1.51, band_hi_m=3.0)
    return [dict(a, opening_id="LA", decision="REQUIRED", width_m=1.20, bearing_m=0.25),
            dict(b, opening_id="LB", decision="REQUIRED", width_m=2.40, bearing_m=0.25),
            dict(a, opening_id="LC", decision="REQUIRED", width_m=0.90, bearing_m=None)]


def rows(doc):
    return {r["opening_id"]: r for r in doc["rows"]}


def comp(r, role, part):
    (c,) = [c for c in r["components"] if c["role"] == role and c["part"] == part]
    return c


def test_normal_case_by_hand():
    doc = T.ledger(villa())
    r = rows(doc)
    assert r["LA"]["at_least_kg"] == pytest.approx(488 / 162 * 1.2, abs=1e-6) == pytest.approx(3.614815, abs=1e-6)
    assert r["LB"]["at_least_kg"] == pytest.approx(15.644444, abs=1e-6)
    assert r["LC"]["at_least_kg"] == pytest.approx(2.711111, abs=1e-6)
    assert r["LA"]["ceiling_straight_kg_beside"] == pytest.approx(5.120988, abs=1e-6)
    assert r["LB"]["ceiling_straight_kg_beside"] == pytest.approx(18.903704, abs=1e-6)
    assert r["LC"]["ceiling_straight_kg_beside"] is None and r["LC"]["length_m"] is None
    assert (r["LA"]["links_over_L"], r["LA"]["links_over_span"]) == (9, 6)
    assert (r["LB"]["links_over_L"], r["LB"]["links_over_span"]) == (12, 10)
    assert (r["LC"]["links_over_L"], r["LC"]["links_over_span"]) == (None, 5)
    t = doc["total"]
    assert t["state"] == T.AT_LEAST
    assert t["at_least_kg"] == pytest.approx(21.970370, abs=1e-6)
    assert t["at_least_t"] == pytest.approx(0.021970, abs=1e-6)
    assert t["links_over_L"] == 21 and t["links_over_span"] == 21


def test_split_states_and_held_names():
    r = rows(T.ledger(villa()))
    for oid in ("LA", "LB"):
        assert comp(r[oid], "BOTTOM", "SPAN")["state"] == T.COMPUTED
        ib = comp(r[oid], "BOTTOM", "IN_BEARING")
        assert ib["state"] == T.HELD and ib["kg"] is None and ib["ceiling_kg_beside"] > 0
        assert comp(r[oid], "TOP", "END_BENDS")["state"] == T.HELD
        lap = comp(r[oid], "TOP", "LAPS")
        assert lap["state"] == T.NOT_REQUIRED and lap["kg"] == 0.0     # a genuine 0: run within the 12 m stock
        assert comp(r[oid], "LINKS", "LINKS")["kg"] is None
    lc = r["LC"]
    assert comp(lc, "BOTTOM", "IN_BEARING")["ceiling_kg_beside"] is None
    assert comp(lc, "BOTTOM", "LAPS")["state"] == T.HELD
    assert "BOTTOM IN_BEARING" in lc["held_parts"] and "LINKS LINKS" in lc["held_parts"]


def test_mirror_and_order_invariant():
    a = T.ledger(villa())["total"]
    b = T.ledger(list(reversed(villa())))["total"]
    assert a == b


def test_printed_cover_and_bend_compute():
    x = dict(villa()[0], end_cover_m=0.05, end_cover_m_source="PRINTED detail note", bend_m=0.10,
             bend_m_source="PRINTED BBS shape")
    r = T.lintel_bars(x)
    # in-bearing 2 x (0.25 - 0.05) = 0.40 m per bar: bottom 2 x 0.4 x 144/162, top 2 x 0.4 x 100/162
    assert comp(r, "BOTTOM", "IN_BEARING")["kg"] == pytest.approx(2 * 0.4 * 144 / 162, abs=1e-6)
    assert comp(r, "TOP", "END_BENDS")["kg"] == pytest.approx(2 * 2 * 0.1 * 100 / 162, abs=1e-6)
    assert r["at_least_kg"] == pytest.approx(488 / 162 * (1.2 + 0.4 + 0.2), abs=1e-6)


# --------------------------------------------------------------------------------------------- adverse
@pytest.mark.parametrize("key", ["end_cover_m", "bend_m", "hook_m", "cover_m"])
def test_bend_or_cover_length_defaulted_refused(key):
    x = dict(villa()[0], **{key: 0.025})
    with pytest.raises(T.LintelBarError, match="defaulted"):
        T.lintel_bars(x)


def test_held_summed_as_zero_refused():
    doc = T.ledger(villa())
    r = doc["rows"][0]
    for c in r["components"]:
        if c["state"] == T.HELD:
            c["kg"] = 0.0
            break
    with pytest.raises(T.LintelBarError, match="HELD summed"):
        T.total(doc["rows"])


def test_held_lintel_with_a_figure_refused():
    held = dict(villa()[0], opening_id="LH", decision="HELD", why="head not established")
    r = T.lintel_bars(held)
    assert r["state"] == T.HELD and r["at_least_kg"] is None
    assert r["if_built_span_kg_beside"] == pytest.approx(3.614815, abs=1e-6)
    r["at_least_kg"] = 0.0
    with pytest.raises(T.LintelBarError, match="HELD lintel"):
        T.check_row(r)
    t = T.total([T.lintel_bars(held)] + [T.lintel_bars(x) for x in villa()])
    assert t["lintels_held"] == ["LH"] and t["at_least_kg"] == pytest.approx(21.970370, abs=1e-6)


@pytest.mark.parametrize("w", [1200, 120, 0, -1.0, None])
def test_width_not_metres_refused(w):
    with pytest.raises(T.LintelBarError):
        T.lintel_bars(dict(villa()[0], width_m=w))


def test_width_outside_band_refused():
    with pytest.raises(T.LintelBarError, match="outside its printed band"):
        T.lintel_bars(dict(villa()[0], width_m=1.505))


@pytest.mark.parametrize("txt", ["2 bars 12", "Ø12", "2Ø", "", None])
def test_bad_bar_text_refused(txt):
    with pytest.raises(T.LintelBarError):
        T.lintel_bars(dict(villa()[0], bottom=txt))


def test_bad_link_text_refused():
    with pytest.raises(T.LintelBarError):
        T.lintel_bars(dict(villa()[0], stirrups="Ø8@200"))


def test_second_record_for_one_opening_refused():
    v = villa()
    with pytest.raises(T.LintelBarError, match="second lintel record"):
        T.ledger(v + [v[0]])


def test_lap_beyond_stock_is_held_with_count():
    # an invented 13.0 m opening (no band bound given): run 13.5 m > 12 m stock -> 1 splice per bar, 60 d (owner BEAM)
    x = dict(villa()[0], width_m=13.0, band_lo_m=None, band_hi_m=None)
    r = T.lintel_bars(x)
    lap = comp(r, "BOTTOM", "LAPS")
    assert lap["state"] == T.HELD and lap["laps_per_bar"] == 1 and lap["lap_m"] == pytest.approx(0.72)
    assert lap["kg"] is None and lap["kg_if_full_run_beside"] == pytest.approx(2 * 0.72 * 144 / 162, abs=1e-6)
