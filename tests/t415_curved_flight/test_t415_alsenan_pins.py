"""T-415 development-villa pins on the committed ST-02 RS-C summary (research/agents_t415/summary_t415.json, built by
t415_alsenan.py from the private structural DXF by handle; re-derived here without private input)."""

import json
import math
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / "research" / "agents_t415"
S = json.loads((D / "summary_t415.json").read_text(encoding="utf-8"))
G, DV = S["geometry"], S["derived"]


def test_reproduces_from_committed_geometry():
    p = subprocess.run([sys.executable, "-I", str(D / "t415_alsenan.py"), "--check"], capture_output=True, text=True)
    assert p.returncode == 0 and "REPRODUCED" in p.stdout, p.stdout + p.stderr


def test_twelve_drawn_risers_and_lane():
    assert [r["id"] for r in G["risers"]] == ["2EA", "2E9", "2E8", "2E7", "2E6", "2E5", "2E4", "2E3", "2E2", "2E1",
                                              "2E0", "2DF"]
    assert all(abs(r["radial_offset"] - 0.05) < 1e-3 for r in G["risers"])
    assert G["lane"]["width"] == pytest.approx(1.25, abs=1e-6)
    assert G["dtheta_deg"]["max"] - G["dtheta_deg"]["min"] < 1e-4
    assert G["columns_touching_lane"] == []
    assert G["k_numeric_check_err_m2"] < 2e-4


def test_hand_tread_and_steps():
    # hand: 1/2 (2.780511^2 - 1.530511^2) x 7.790996 deg = 0.366379 m2 per unclipped curved tread
    d = math.radians(7.790996)
    a = 0.5 * (2.780511 ** 2 - 1.530511 ** 2) * d
    assert a == pytest.approx(0.366379, abs=1e-6)
    tr = {t["k"]: t for t in G["treads"]}
    for k in range(1, 11):
        assert tr[k]["area"] == pytest.approx(a, abs=2e-6)
    assert tr[11]["clipped_by_B3"] is True  # outer strip inside the 'B3 (With Stair)' band: the beam's, not the stair's
    area = sum(tr[k]["area"] for k in range(1, 13))
    assert DV["area_m2"] == pytest.approx(area, abs=1e-6)
    assert DV["steps_m3"] == pytest.approx(0.5 * 4.50 / 28 * area, abs=1e-6)
    # the foot zone below the first riser is floor (+1.00), never a step
    assert tr[0]["piece"].startswith("FOOT")


def test_waist_held_with_coefficient_and_bound():
    assert DV["waist"] is None and DV["waist_status"] == "HELD"
    assert DV["bound"] == dict(kind="AT_LEAST", low=DV["steps_m3"], high=None)
    assert DV["k_waist_m2"] > DV["area_m2"]  # sec(alpha) > 1 everywhere
    assert "not a quantity" in DV["scenario"]["label"]


def test_residual_split_closes_and_his_length_untraced():
    rec = DV["reconciliation"]
    assert rec["residual"] == pytest.approx(-3.974175, abs=1e-6)
    assert sum(t["m3"] for t in rec["terms"]) == pytest.approx(rec["residual"], abs=5e-6)
    kinds = {t["kind"] for t in rec["terms"]}
    assert kinds == {"THICKNESS_BASIS", "HELD_BINDING", "AREA_BEYOND_DRAWN"}
    assert DV["lengths"]["his_length_traced"] is False


def test_retired_tread_line_lane_reproduces_t258_information_figure():
    alt = S["retired_tread_line_lane"]["derived"]
    assert alt["area_m2"] == pytest.approx(4.1077, abs=1e-4)  # T-258 ledger note 'CAD tread areas 4.1077 m2'
    assert alt["steps_m3"] == pytest.approx(0.330, abs=5e-4)
    assert DV["area_m2"] - alt["area_m2"] == pytest.approx(0.335394, abs=1e-6)
