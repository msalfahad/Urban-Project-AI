"""T-306 slab reinforcement bound rules on a hand-calculated NON-Alsenan villa (V306). Nothing here comes from a
client drawing.

Villa V306 (invented): two-way slab panel S1, 4.00 m (x) x 3.00 m (y) face to face on beams.
  bottom x: '16 ø 10' printed as a COUNT, bars 4.00 m drawn: 16 x 4.00 x 100 / 162 = 39.506173 kg  DRAWING_CONFIRMED
  bottom y: '5 ø 10/m' printed as a RATE over a 4.00 m width, bars 3.00 m:
            A = ceil(5 x 4.00) = 20 bars: 20 x 3.00 x 0.617284 = 37.037037 kg
            B = A + 1 = 21 bars:          21 x 3.00 x 0.617284 = 38.888889 kg            BOUND (count not printed)
  top over the support B1: '6 ø 12' printed, bars 1.60 m drawn: 6 x 1.60 x 144 / 162 = 8.533333 kg  DRAWING_CONFIRMED
  development of the y bars on note 9 (40 d .. 70 d), counts 20 .. 21:
            low 20 x 2 x 0.40 x 0.617284 = 9.876543; high 21 x 2 x 0.70 x 0.617284 = 18.148148 kg
            count part 1 x 0.80 x 0.617284 = 0.493827; 40 -> 70 d part 21 x 0.60 x 0.617284 = 7.777778 (sum 8.271605)
  top bars on the note-2 readings (kg): i 3.0 / 3.2, ii 6.0 / 6.4, p.15 5.5 / 5.9 (count A / B), crossing 0.5 / 0.6:
            low = i_A 3.0; high = ii_B 6.4 + 0.6 = 7.0; wording 3.0, note 2 vs p.15 0.0, count 0.4, crossing 0.6
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t306"))
import t306_slab_bounds as sb  # noqa: E402

U10, U12 = 100 / 162, 144 / 162


# ------------------------------------------------------------------------------------------------- normal
def test_printed_count_is_drawing_confirmed():
    c = sb.component("16ø10", 4.00, length_source="plan S1 x, face to face")
    assert c["status"] == "DRAWING_CONFIRMED"
    assert c["kg"] == pytest.approx(39.506173, abs=1e-6)


def test_top_bar_over_one_support_printed_is_drawing_confirmed():
    c = sb.component("6ø12", 1.60, length_source="section S1-S1, top bar 1.60 m")
    assert c["status"] == "DRAWING_CONFIRMED" and c["kg"] == pytest.approx(8.533333, abs=1e-6)


def test_rate_is_a_bound_A_B():
    c = sb.component("5ø10/m", 3.00, spread_m=4.00, length_source="plan S1 y")
    assert c["status"] == "BOUND" and c["counts"] == (20, 21)
    assert c["low"] == pytest.approx(37.037037, abs=1e-6) and c["high"] == pytest.approx(38.888889, abs=1e-6)


def test_exact_multiple_not_rounded_up_twice():
    assert sb.count_from_label("5ø10/m", 4.20) == ("BOUND", 21, 22)


def test_mirror_and_rotation_unchanged():
    a = sb.component("5ø10/m", 3.00, spread_m=4.00, length_source="x")
    b = sb.component("5ø10/m", 3.00, spread_m=4.00, length_source="mirrored")   # width and length invariant
    assert (a["low"], a["high"]) == (b["low"], b["high"])


def test_development_decomposition_closes():
    lo, hi = 20 * 0.80 * U10, 21 * 1.40 * U10
    c, out, _ = sb.decompose_dev("V306-DEV", round(lo, 3), round(hi, 3), 20, 21, 10, 1)
    assert c["COUNT_CONVENTION"] == pytest.approx(0.493827, abs=1e-6)
    assert c["ANCHORAGE_LENGTH"] == pytest.approx(7.777778, abs=1e-6)
    assert abs(c["STORAGE_ROUNDING"]) < 0.003 and out == []


def test_top_decomposition_closes():
    rd = {"i": (3.0, 3.2), "ii": (6.0, 6.4), "p15": (5.5, 5.9), "cross": (0.5, 0.6)}
    c, out, _ = sb.decompose_top("V306-TOP", 3.0, 7.0, rd)
    assert c["TOP_NOTE2_WORDING"] == pytest.approx(3.0) and c["COUNT_CONVENTION"] == pytest.approx(0.4)
    assert c["TOP_CROSSING"] == pytest.approx(0.6) and c.get("TOP_NOTE2_VS_P15", 0.0) == pytest.approx(0.0)
    assert out == []


def test_top_via_p15_when_it_governs():
    rd = {"i": (3.0, 3.2), "ii": (6.0, 6.4), "p15": (6.5, 6.9), "cross": (0.5, 0.6)}
    c, _, _ = sb.decompose_top("V306-TOP2", 3.0, 7.5, rd)
    assert c["TOP_NOTE2_WORDING"] == pytest.approx(3.0) and c["TOP_NOTE2_VS_P15"] == pytest.approx(0.5)
    assert c["COUNT_CONVENTION"] == pytest.approx(0.4)


def test_bare_label_carries_both_readings():
    lo5 = 5 * 3.0 * U10            # 5 bars in all
    a, b = 20 * 3.0 * U10, 21 * 3.0 * U10
    c, out, _ = sb.decompose_bottom("V306-BARE", lo5, b, 20 * 3.0 * U10, b, 0.0, 0.0, label_reading_kg=lo5)
    assert c["LABEL_MEANING"] == pytest.approx(a - lo5) and c["COUNT_CONVENTION"] == pytest.approx(b - a)
    assert out == []


# ------------------------------------------------------------------------------------------------- adverse
def test_rate_read_as_count_refused():
    with pytest.raises(ValueError, match="RATE_AS_COUNT_REFUSED"):
        sb.count_from_label("5ø10/m")
    with pytest.raises(ValueError, match="RATE_AS_COUNT_REFUSED"):
        sb.component("5ø10/m", 3.00, length_source="plan")


def test_two_layers_one_label_merged_refused():
    r = dict(element="SLAB:S1", part="x", layers=1, component="BOTTOM MESH", printed="5ø10/m")
    with pytest.raises(ValueError, match="DUPLICATE_RECORD_REFUSED"):
        sb.check_keys([r, dict(r)])
    with pytest.raises(ValueError, match="LAYER_MISMATCH_REFUSED"):
        sb.check_keys([dict(r, printed="5ø10/m (T&B)")])
    assert sb.check_keys([r, dict(r, layers=2, printed="5ø10/m (T&B)")])


def test_owner_lap_proposal_refused():
    with pytest.raises(ValueError, match="LAP_PROPOSAL_REFUSED"):
        sb.end_length("OWNER_40D_60D", 10)
    assert sb.end_length("NOTE9", 10)[0] == "BOUND"
    assert sb.end_length("DRAWN", 10, 0.36) == ("DRAWING_CONFIRMED", 0.36, 0.36)


def test_unprinted_extent_given_a_value_refused():
    with pytest.raises(ValueError, match="UNPRINTED_EXTENT_REFUSED"):
        sb.component("6ø12", 1.60, length_source="UNPRINTED")
    assert sb.component("6ø12", None)["status"] == "HELD"


def test_mm_width_refused():
    with pytest.raises(ValueError, match="UNIT_REFUSED"):
        sb.count_from_label("5ø10/m", 4000.0)


def test_non_closing_decomposition_refused():
    with pytest.raises(ValueError, match="do not close"):
        sb.close("V306-X", 10.0, 12.0, {"COUNT_CONVENTION": 1.5}, 2)
    with pytest.raises(ValueError, match="unknown cause"):
        sb.close("V306-X", 10.0, 12.0, {"MORE_STEEL": 2.0}, 2)


def test_bound_excluding_a_reading_is_named():
    rd = {"i": (3.0, 2.9), "ii": (6.0, 5.8), "p15": (5.5, 5.4), "cross": (0.5, 0.4)}   # skewed: B below A
    _, out, _ = sb.decompose_top("V306-SKEW", 3.0, 5.8 + 0.5, rd)
    names = {o["reading"] for o in out}
    assert "i_B" in names and "ii_A+cross" in names
    _, out, flags = sb.decompose_top("V306-TB", 3.0, 7.0, {"i": (3.0, 3.2), "ii": (6.0, 6.4), "p15": (5.5, 5.9),
                                                          "cross": (0.5, 0.6)}, tb_panel=True)
    assert [o["reading"] for o in out] == ["no_note2_bars_over_TB_mesh"] and flags == ["TB_PANEL_NOTE2_OPEN"]


def test_bar_end_by_support_kind():
    # V306: S1 bottom y bar meets B1 (continuous, slab S2 beyond) and the edge beam E1 0.25 m wide (non-continuous)
    assert sb.bar_end("CONTINUOUS", None, 10) == ("NOT_APPLICABLE", 0.0, 0.0)
    assert sb.bar_end("NON_CONTINUOUS", "DRAWN", 10, 0.25 - 0.04) == ("DRAWING_CONFIRMED", 0.21, 0.21)
    assert sb.bar_end("NON_CONTINUOUS", None, 10)[0] == "HELD"
    with pytest.raises(ValueError, match="CONTINUOUS_END_LENGTH_REFUSED"):
        sb.bar_end("CONTINUOUS", "NOTE9", 10)
    with pytest.raises(ValueError, match="LAP_PROPOSAL_REFUSED"):
        sb.bar_end("NON_CONTINUOUS", "OWNER_40D_60D", 10)
