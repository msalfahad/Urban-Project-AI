"""T-171: bar population at a printed rate / spacing (maximum spacing, edge bars at the cover, inside any enclosing
boxed-bar leg), on a synthetic fixture that is NOT any real villa. Every expected value is a hand calculation:

kg/m = d^2/162 (Urban project default R3): d10 0.617284, d12 0.888889, d14 1.209877, d16 1.580247.
L_eff = side - 2 cover - 2 d_enclosing - d;  N = ceil(L_eff / s) + 1;  bar = other side - 2 cover - 2 d_enclosing.

SQ  2.00 x 2.00, '8 ø 12/m', cover 70, no enclosing bar: L_eff 2000-140-12 = 1848; 1848/125 = 14.784 -> 15 + 1 = 16
    bars of 1.86 m per direction; 2 x 16 x 1.86 x 0.888889 = 52.906667 kg; achieved spacing 1848/15 = 123.2 mm <= 125.
EX  exact division: 1.75 x 1.75, '5 ø 10/m' (s 200), cover 70: L_eff 1750-140-10 = 1600 = 8 x 200 -> N = 9 (not 10).
    Knife edge: side 1751 -> L_eff 1601 -> 9 spaces -> N = 10; with a 1 mm enclosing bar L_eff 1599 -> N = 9.
OC  odd cover 75 mm, 2.30 x 2.30, 'ø 12 @ 15 cm': L_eff 2300-150-12 = 2138; 2138/150 = 14.253 -> 15 + 1 = 16.
CO  two layers, 5.00 x 2.00, TOP '6 ø 16/m', BOT '10 ø 16/m', cover 70, enclosing legs 12 mm:
    L_eff across L 5000-140-24-16 = 4820, across W 2000-180 = 1820; bars along W 2000-164 = 1.836 m, along L 4.836 m.
    TOP short 4820/166.67 = 28.92 -> 30 bars, 55.080 m, 87.040000 kg; TOP long 1820 x 6/1000 = 10.92 -> 12, 58.032 m,
    91.704889 kg; BOT short 48.2 -> 50, 91.800 m, 145.066667 kg; BOT long 18.2 -> 20, 96.720 m, 152.841481 kg;
    total 301.632 m x 1.580247 = 476.653037 kg. Rotated (2.00 x 5.00) and in mm / m units: the same total.
AD  area check, 1.90 side, '9 ø 14/m', cover 70: L_eff 1900-154 = 1746 x 9/1000 = 15.714 -> 17 bars; 9 x 1.90 = 17.1
    bars -> deficit 0.1 bar reported, N unchanged.
Adverse: enclosing diameter not printed (None) -> HELD, kg None; no cover -> HELD; 'ø 14/m' (no count), 'ø 14 @ 15'
(no unit), empty cell -> UNKNOWN; side too small (L_eff <= 0) -> UNKNOWN; a printed count '18 ø 12' is never
re-counted; any held row makes the footing total None, never 0.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

_PATH = Path(__file__).resolve().parents[2] / "research" / "agents_t171" / "t171_bar_population.py"
_spec = importlib.util.spec_from_file_location("t171_bar_population", _PATH)
bp = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(bp)


def test_square_rate_is_a_maximum_spacing_with_edge_bars():
    rows = bp.footing("SQ", 200, 200, 70, {"BOT": ("8 ø 12/m", "8 ø 12/m")}, 0)
    assert [r["n"] for r in rows] == [16, 16]
    assert rows[0]["l_eff_m"] == pytest.approx(1.848)
    assert rows[0]["achieved_spacing_mm"] == pytest.approx(123.2)
    assert rows[0]["achieved_spacing_mm"] <= rows[0]["printed_spacing_mm"]
    assert bp.total(rows) == pytest.approx(52.906667, abs=1e-5)


def test_exact_division_gives_k_plus_one_not_k_plus_two():
    r = bp.cell(1750, 1750, 70, "5 ø 10/m", 0)
    assert r["n"] == 9 and r["achieved_spacing_mm"] == pytest.approx(200.0)
    assert bp.cell(1751, 1751, 70, "5 ø 10/m", 0)["n"] == 10
    assert bp.cell(1751, 1751, 70, "5 ø 10/m", 1)["n"] == 9
    assert bp.threshold_enclosing_mm(1751, 70, "5 ø 10/m") == 1
    assert bp.cell(1750, 1750, 70, "5 ø 10/m", 1)["n"] == 9  # 1598 / 200 = 7.99 -> 8 + 1
    assert bp.threshold_enclosing_mm(1750, 70, "5 ø 10/m") is None  # needs L_eff <= 1400, i.e. a 100 mm leg


def test_odd_cover_and_spacing_notation():
    r = bp.cell(2300, 2300, 75, "ø 12 @ 15 cm", 0)
    assert r["n"] == 16 and r["l_eff_m"] == pytest.approx(2.138)
    assert bp.cell(2300, 2300, 75, "ø 12/15cm", 0)["n"] == 16
    assert bp.cell(2300, 2300, 75, "ø 12 @ 150 mm", 0)["n"] == 16


def test_two_layers_inside_enclosing_legs_rotation_and_units():
    lay = {"TOP": ("6 ø 16/m", "6 ø 16/m"), "BOT": ("10 ø 16/m", "10 ø 16/m")}
    rows = bp.footing("CO", 500, 200, 70, lay, 12)
    assert [r["n"] for r in rows] == [30, 12, 50, 20]
    assert [round(r["kg"], 6) for r in rows] == [87.04, 91.704889, 145.066667, 152.841481]
    assert bp.total(rows) == pytest.approx(476.653037, abs=1e-5)
    assert bp.total(bp.footing("CR", 200, 500, 70, lay, 12)) == pytest.approx(476.653037, abs=1e-5)
    assert bp.total(bp.footing("CM", 5000, 2000, 70, lay, 12, unit="mm")) == pytest.approx(476.653037, abs=1e-5)
    assert bp.total(bp.footing("CMm", 5, 2, 70, lay, 12, unit="m")) == pytest.approx(476.653037, abs=1e-5)


def test_area_check_is_reported_not_applied():
    r = bp.cell(1900, 1900, 70, "9 ø 14/m", 0)
    assert r["n"] == 17
    assert r["area_check_bars"] == pytest.approx(17.1) and r["area_deficit_bars"] == pytest.approx(0.1)


def test_missing_data_is_held_or_unknown_never_zero():
    assert bp.cell(2000, 2000, 70, "8 ø 12/m", None)["status"] == "HELD"
    assert bp.cell(2000, 2000, None, "8 ø 12/m", 0)["status"] == "HELD"
    for bad in ("ø 14/m", "ø 14 @ 15", "", None):
        r = bp.cell(2000, 2000, 70, bad, 0)
        assert r["status"] == "UNKNOWN" and r["kg"] is None
    small = bp.cell(150, 150, 70, "8 ø 12/m", 0)
    assert small["status"] == "UNKNOWN" and small["kg"] is None
    rows = bp.footing("MX", 200, 200, 70, {"BOT": ("8 ø 12/m", "ø 14/m")}, 0)
    assert bp.total(rows) is None
    assert bp.total(bp.footing("NE", 200, 200, 70, {"BOT": ("8 ø 12/m", "8 ø 12/m")}, None)) is None


def test_printed_count_is_never_recounted():
    rows = bp.footing("CN", 220, 200, 70, {"BOT": ("18 ø 12", "17 ø 12")}, 0)
    assert [r["n"] for r in rows] == [18, 17]
    assert bp.total(rows) == pytest.approx((18 * 1.86 + 17 * 2.06) * 144 / 162, abs=1e-6)
    held = bp.footing("CH", 220, 200, 70, {"BOT": ("18 ø 12", "17 ø 12")}, None)
    assert [r["n"] for r in held] == [18, 17] and bp.total(held) is None
