"""T-583: dome / ring / lift-wall bar components (research/agents_t583, R-T583-1 .. 6).
Hand villa "K583" (not the training villa): a 2.00 m wall between column faces, a 0.20 x 0.50 ring, closed hoops,
normal and adverse cases; then the committed development-villa table rebuilt from merged repository files."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t583"))
import t583_rebar as M  # noqa: E402
import t583_alsenan as A  # noqa: E402


# ---- R-T583-1: K583 wall 2.00 m between faces, s 0.20: readings 9 / 10 / 11, both 10 and 11 inside ---------------
def test_k583_wall_spacing_readings_by_hand():
    r = M.spacing_readings(2.00, 0.20)
    assert (r["both_supports"], r["one_end"], r["both_ends"]) == (9, 10, 11)
    assert r["low"] <= 10 <= r["high"] and r["low"] <= 11 <= r["high"]


def test_non_integer_span_and_floor_reading_inside():
    # 1.80 m at 6 per metre: L/s = 10.8 -> 10 / 11 / 12; floor(L/s) = 10 and 1 + floor = 11 both inside
    r = M.spacing_readings(1.80, 1 / 6)
    assert (r["low"], r["high"]) == (10, 12)


def test_mirror_and_zero_length():
    assert M.spacing_readings(1.2, 0.2) == M.spacing_readings(abs(-1.2), 0.2)
    assert M.spacing_readings(0.0, 0.2)["low"] == 0
    with pytest.raises(M.T583Error):
        M.spacing_readings(-1.0, 0.2)


def test_adverse_non_strict_low_refused():
    # the T-575 low 1 + floor(L/s) = 11 per 2.00 m face is above the admissible 9: refused as a stated low
    with pytest.raises(M.T583Error):
        M.assert_strict_low(11, [9, 10, 11])
    assert M.assert_strict_low(9, [9, 10, 11])


# ---- R-T583-2 rows over an unprinted height ----------------------------------------------------------------------
@pytest.mark.parametrize("h", [0.5, 1.0, 1.37, 2.0, 3.2])
def test_rows_bounds_contain_every_integer_reading(h):
    lo, hi = M.rows_bounds_continuous(6, h)
    import math
    c = math.ceil(6 * h - 1e-9)
    assert lo <= c - 1 + 1e-9 and c + 1 <= hi + 1e-9


# ---- R-T583-3 / -5 link path by hand: 0.20 x 0.50, cover 0.025, d8: 2 x (0.142 + 0.442) = 1.168 m ------------------
def test_link_path_high_by_hand_and_units():
    assert M.link_path_high(0.20, 0.50, 8, 0.025) == pytest.approx(1.168)
    with pytest.raises(M.T583Error):          # cover given in mm (25) instead of m: refused, never a silent value
        M.link_path_high(0.20, 0.50, 8, 25)


def test_link_floor_and_depth_floor_by_hand():
    layers = [{"role": "RING_TOP", "n": 3, "d_mm": 16}, {"role": "RING_BOTTOM", "n": 3, "d_mm": 18}]
    # inner 3 x 0.018 = 0.054 wide, 0.016 + 0.018 = 0.034 high, + d8: 2 x 0.062 + 2 x 0.042 = 0.208
    assert M.link_path_floor(layers, 8) == pytest.approx(0.208)
    assert M.depth_floor(layers, 8, 0.025) == pytest.approx(0.05 + 0.016 + 0.034)


# ---- R-T583-4 joints and laps -------------------------------------------------------------------------------------
def test_joint_counts():
    assert M.joints_closed_loop(10.0) == 1 and M.joints_closed_loop(13.85) == 2
    assert [M.joints_open_run(x) for x in (12.00, 12.01, 24.5)] == [0, 1, 2]


def test_printed_lap_by_hand_and_adverse_without_authority():
    # 3 joints x 40 d12 = 3 x 0.48 x 0.888889 = 1.28 kg with a PRINTED note governing the group
    assert M.lap_mass(3, 12, {"class": "PRINTED", "d_multiple": 40, "source": "K583 note"}) == pytest.approx(1.28)
    for bad in (None, {"class": "OWNER_PROPOSAL", "d_multiple": 60}, {"class": "TYPICAL", "m": 0.5}):
        with pytest.raises(M.T583Error):
            M.lap_mass(3, 12, bad)
    sc = M.lap_scenario(3, 12, 60, "proposal")
    assert sc["in_bound"] is False and sc["label"] == "OWNER_PROPOSAL_SCENARIO"


def test_kg_as_t_refused_and_missing_low_refused():
    with pytest.raises(M.T583Error):
        M.to_t(12.0, unit="t")
    with pytest.raises(M.T583Error):
        M.row_total([{"group": "X", "kg_low": None, "kg_high": None}])
    tot = M.row_total([{"group": "A", "kg_low": 1.0, "kg_high": 2.0}, {"group": "LAP", "kg_low": 0.0, "kg_high": None}])
    assert tot["high_status"] == "HELD_HIGH" and tot["high_excluding"] == ["LAP"] and tot["kg_low"] == 1.0


# ---- development villa rebuild from merged files ----------------------------------------------------------------------
def test_development_villa_rebuild_matches_committed():
    txt = json.dumps(A.build(), indent=1, sort_keys=True) + "\n"
    assert A.OUT.read_text(encoding="utf-8") == txt


def test_development_villa_strict_lows_and_nothing_valued():
    res = A.build()
    lift = next(r for r in res["rows"] if r["row_id"].startswith("LIFT_PIT"))
    assert lift["formula"]["A_t_per_m"][0] <= 0.156642 + 1e-9            # F-C-T575-1
    assert lift["formula"]["n_vertical"] == [62, 78] and lift["t_low"] is None
    for r in res["rows"]:
        if r.get("t_low") is not None:
            t575 = {"HL:DOME_SHELL": 0.287994}.get(r["row_id"][:13])
            if t575:
                assert r["t_low"] >= t575
            assert r["high_excluding"]                                       # laps / hooks / depth HELD by name
    assert res["totals"]["valued_t"] == 0.0 and res["totals"]["t_high"] is None
