"""T-322 on the development villa (research/agents_t322; input = own-read values, handles and page references;
merged ledgers T-170 / T-204 / T-219 / T-233 / T-320 read only). Pins the FF / LIFT-01 component ledger and the
resolution of F-T320-03 (FF blinding: T-233 2.256 m3 on the p.13 typical offset vs T-170 HELD)."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t322"))
import lift_base_ledger_v1 as X  # noqa: E402
import t322_alsenan_check as A  # noqa: E402


@pytest.fixture(scope="module")
def out():
    return A.run()


def test_every_component_once_with_status(out):
    res, led = out
    ids = [c["id"] for c in led["components"]]
    assert len(ids) == len(set(ids))
    st = {c["id"]: c["status"] for c in led["components"]}
    assert st["RAFT"] == X.DC and st["BLINDING"] == X.AT_LEAST and st["PIT_WALL:CONC"] == X.HELD
    assert st["UNDERLAY:screed:VOL"] == X.DC and st["UNDERLAY:membrane:VOL"] == X.HELD
    for c in led["components"]:
        if c["status"] != X.DC:
            assert c["value"] is None                                   # HELD never a number, never 0


def test_raft_ring_screed_close_on_the_merged_ledgers(out):
    res, _ = out
    c = res["closure"]
    assert c["ledger_raft_m3"] == pytest.approx(11.385) and c["raft_residual_m3"] == 0.0          # T-233
    assert c["ledger_ring_net_m2"] == pytest.approx(1.100) and c["ring_residual_m2"] == 0.0       # T-204
    assert c["ledger_screed_m3"] == pytest.approx(1.035) and c["screed_residual_m3"] == 0.0       # T-219
    assert c["ledger_raft_plan_m2"] == pytest.approx(c["t219_screed_area_m2"])


def test_f_t320_03_cause_and_corrected_figure(out):
    res, _ = out
    f = res["F_T320_03"]
    assert f["t233_ff_blinding_m3"] == pytest.approx(2.256)                 # (4.60 + 0.20)(4.50 + 0.20) x 0.10
    assert f["corrected_value"] is None and f["corrected_status"] == X.AT_LEAST
    assert f["at_least_m3"] == pytest.approx(2.070)                         # 4.60 x 4.50 x 0.10
    assert f["readings_m3"][X.INHERITED] == pytest.approx(2.256)
    assert f["readings_m3"][X.SCALED] == pytest.approx(2.352)               # (4.60 + 0.30)(4.50 + 0.30) x 0.10
    assert "INHERITED OFFSET" in f["cause"]


def test_blinding_line_closure_against_t320(out):
    res, _ = out
    c = res["closure"]
    assert c["t233_blinding_measured_m3"] == pytest.approx(14.990438)
    assert c["blinding_measured_after_T322_m3"] == pytest.approx(12.734438)
    assert c["blinding_residual_vs_t320_m3"] == 0.0                          # T-320 24 pits inside the plot
    assert c["z1_change_m3"] == 0.0 and c["t320_z1_established_m3"] == pytest.approx(105.162974)


def test_p14_scale_proven_and_reading(out):
    res, _ = out
    sc = res["p14_scale"]
    assert sc["scale_ratio_1_to"] == pytest.approx(20.0, abs=0.1)           # 5 cm screed and 10 cm blinding agree
    assert sc["beyond_footing_face_m"] == [pytest.approx(0.150, abs=1e-3)] * 2
    assert sc["membrane_under_screed_m"] == pytest.approx(0.020, abs=1e-3)  # = p.13's printed '2'
