"""T-575: dome shell / dome ring / lift-pit wall reinforcement by bar population (research/agents_t575, R-T575-1 .. 6).
Hand villa "K575" (not the training villa): a ring beam, a hemispherical dome and a pit, with normal and adverse cases;
then the committed development-villa table rebuilt from merged repository files."""
from __future__ import annotations

import json
import math
import sys
from decimal import Decimal
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t575"))
import t575_rebar as R  # noqa: E402
import t575_alsenan as A  # noqa: E402

D = Decimal


# ---- K575 ring beam (task row): mean circumference 10.00 m, 4 T16 mains, T10 links @ 200, 0.40 x 0.30, cover 0.04 --
#   mains 4 x 10.00 x 16^2/162 (1.580) = 63.21 kg (63.20 at 1.580); links N = 10.00 / 0.20 = 50 on a closed loop,
#   path printed in the fixture = core 2 x (0.32 + 0.22) = 1.08 + hooks 2 x 0.04 = 1.16 m; 50 x 1.16 x 0.617 = 35.79 kg
def test_k575_ring_mains_and_links_by_hand():
    r_c = 10.00 / (2 * math.pi)
    m = R.ring_mains([{"role": "MAIN", "n": 4, "d_mm": 16}],
                     [{"id": "K", "r_c": r_c, "width": 0.40, "inbay_area": 10.00 * 0.40}])
    assert m["kg"][0] == pytest.approx(m["kg"][1])
    assert m["kg"][1] == pytest.approx(63.20, abs=0.02)
    n = R.ring_link_count(1 / 0.20, 10.00)
    assert n == 50
    kg = R.link_mass(n, {"printed": True, "value": 2 * (0.32 + 0.22) + 2 * 0.04}, 10)
    assert kg == pytest.approx(35.79, abs=0.02)


def test_k575_ring_in_bay_is_lower_bound_and_mirror_invariant():
    r_c = 2.0
    rd = [{"id": "P", "r_c": r_c, "width": 0.2, "inbay_area": 0.2 * 6.0},
          {"id": "Q", "r_c": 1.8, "width": 0.2, "inbay_area": 0.2 * 9.0}]
    m = R.ring_mains([{"role": "T", "n": 3, "d_mm": 16}], rd)
    assert m["kg"][0] == pytest.approx(6.0 * 3 * 256 / 162)
    assert m["kg"][1] == pytest.approx(2 * math.pi * 2.0 * 3 * 256 / 162)
    assert R.ring_mains([{"role": "T", "n": 3, "d_mm": 16}], list(reversed(rd)))["kg"] == m["kg"]


# ---- K575 dome: hemisphere rho 2.00 (a = 0), d12 @ 0.50 -------------------------------------------------------------
#   S = pi; hoops at s = 0, 0.5 .. 3.0 (7): 4 pi cos(s / 2) = 12.566 + 12.177 + 11.028 + 9.194 + 6.790 + 3.962 + 0.889
#   = 56.607 m; meridional lower = 2 pi rho^2 / s = 50.265 m, upper = ceil(4 pi / 0.5) = 26 x pi = 81.681 m
def test_k575_hemisphere_hoops_and_meridians_by_hand():
    L = R.hoop_lengths(2.0, 0.0, 0.5)
    assert len(L) == 7
    hand = [12.566, 12.177, 11.028, 9.194, 6.790, 3.962, 0.889]
    assert L == pytest.approx(hand, abs=0.002)
    assert sum(L) == pytest.approx(56.607, abs=0.005)
    mb = R.meridional_bounds(2.0, 0.0, 0.5)
    assert mb["n_springing"] == 26
    assert mb["lower_m"] == pytest.approx(50.265, abs=0.001)
    assert mb["upper_m"] == pytest.approx(81.681, abs=0.001)


def test_k575_cap_from_chord_and_rise():
    sp = R.sphere_from_chord_rise(4.00, 2.00)  # hemisphere
    assert sp["R_out"] == pytest.approx(2.0) and sp["a"] == pytest.approx(0.0)
    sp = R.sphere_from_chord_rise(4.42, 1.90)
    assert sp["R_out"] == pytest.approx((4.42 ** 2 / 4 + 1.9 ** 2) / 3.8)


def test_k575_shell_range_contains_mid_surface_density():
    s = R.dome_shell(4.00, 2.00, 0.10, 12, 0.15)
    mid = 2 * math.pi * 1.95 ** 2 / 0.15  # hemisphere mid-surface area / s
    lo, hi = s["groups"]["SHELL_MERIDIONAL"]["m"]
    assert lo < mid < hi
    lo, hi = s["groups"]["SHELL_HOOP"]["m"]
    assert lo < mid * 1.05 and hi > mid * 0.95


# ---- K575 pit: 4 walls 1.50 m net, d12 6/m horizontal, d16 5/m vertical, each face ----------------------------------
#   verticals 2 faces x 4 x (1 + floor(1.50 / 0.20)) = 2 x 4 x 8 = 64; A_lo = 6 x 12.0 x 0.8889 + 64 x 1.5802 = 165.14
def test_k575_pit_walls_formula_by_hand():
    pw = R.pit_walls([1.5] * 4, {"d_mm": 12, "per_m": 6}, {"d_mm": 16, "per_m": 5}, {"n": 2, "d_mm": 12}, 0.5, 0.1,
                     [8.0, 7.2], 7.2)
    assert pw["n_vertical"] == 64
    assert pw["A_kg_per_m_height"][0] == pytest.approx(6 * 12.0 * 144 / 162 + 64 * 256 / 162)
    assert pw["A_kg_per_m_height"][0] == pytest.approx(165.14, abs=0.01)
    assert pw["A_kg_per_m_height"][1] > pw["A_kg_per_m_height"][0]


# ---- adverse ------------------------------------------------------------------------------------------------------
def test_adverse_flat_plan_length_for_dome_bar_refused():
    with pytest.raises(R.T575Error, match="flat plan"):
        R.dome_shell(4.42, 1.90, 0.10, 12, 0.15, length_basis="PLAN")


def test_adverse_unprinted_bar_given_value_refused():
    with pytest.raises(R.T575Error, match="not printed"):
        R.link_mass(50, {"printed": False, "value": 1.16}, 8)
    with pytest.raises(R.T575Error, match="not printed"):
        R.link_mass(50, None, 8)
    with pytest.raises(R.T575Error):
        R.ring_mains([{"role": "T", "n": None, "d_mm": 16}], [{"id": "x", "r_c": 2, "width": .2, "inbay_area": 1}])


def test_adverse_kg_reported_as_t_refused():
    assert R.to_t(1580.0) == D("1.580000")
    with pytest.raises(R.T575Error):
        R.to_t(1.58, "t")


def test_adverse_missing_wall_height_is_held_never_zero():
    with pytest.raises(R.T575Error, match="never 0"):
        R.pit_walls_value(None)
    with pytest.raises(R.T575Error):
        R.d6(None)


def test_adverse_inbay_longer_than_circle_refused():
    with pytest.raises(R.T575Error):
        R.ring_mains([{"role": "T", "n": 3, "d_mm": 16}], [{"id": "x", "r_c": 1.0, "width": 0.2, "inbay_area": 2.0}])


# ---- development villa (rebuild from merged repository files) ------------------------------------------------------
def test_dev_villa_rebuild_equals_committed():
    res = A.build()
    assert A.OUT.read_text(encoding="utf-8") == json.dumps(res, indent=1, sort_keys=True) + "\n"


def test_dev_villa_one_row_per_v8_row_and_no_value_without_bars():
    res = A.build()
    v8 = json.loads(A.V8.read_text(encoding="utf-8"))["rebar_omission"]["rows"]
    assert [r["row_id"] for r in res["rows"]] == [r["expected_after"]["element_id"] for r in v8]
    for r in res["rows"]:
        assert r["unit"] == "t"
        if r["status"] == "HELD_BLANK":
            assert r["t_low"] is None and r["t_high"] is None and r["missing"]
        else:
            assert 0 < r["t_low"] < r["t_high"]
    assert res["totals"]["valued_t"] == 0.0


def test_dev_villa_hand_checked_groups():
    rows = {r["row_id"].split(":")[2]: r for r in A.build()["rows"]}
    # west ring, B4 reading lower bound: (2 x 144 + 4 x 256) / 162 x 1.510513 / 0.20 = 61.166 kg
    w = rows["DOME-1F-W"]
    assert w["t_low"] == pytest.approx((2 * 144 + 4 * 256) / 162 * 1.510512768 / 0.2 / 1000, abs=1e-6)
    # both rings' upper bound: detail (3 x 256 + 3 x 324) / 162 x 2 pi x 2.311092 = 155.966 kg
    up = (3 * 256 + 3 * 324) / 162 * 2 * math.pi * 2.311091523536 / 1000
    assert w["t_high"] == pytest.approx(up, abs=1e-6) and rows["DOME-1F-E"]["t_high"] == pytest.approx(up, abs=1e-6)
    # lift walls: A_lo = 6 x 11.0 x 144/162 + 70 x 256/162 = 169.284 kg per m of height
    lift = [r for r in rows.values() if r["row_id"].startswith("LIFT")][0]
    assert lift["formula"]["A_t_per_m"][0] == pytest.approx((6 * 11.0 * 144 + 70 * 256) / 162 / 1000, abs=1e-6)
    assert lift["formula"]["net_wall_m"] == pytest.approx(5.5)  # = T-322 ring net 1.100 m2 / 0.20
