"""T-350 r4: the development-villa inputs (research/agents_t350r4/t350r4_inputs.py) are read from the sha-pinned merged
files: figures, statuses, closures and the ext-trench envelope reconciliation (no private file needed)."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research" / "agents_t350r4"))

import t350r4_inputs as T  # noqa: E402
from engine.source import arch_v3048 as A  # noqa: E402


@pytest.fixture(scope="module")
def z():
    d = A.load_inputs(T.build("p"), "p")
    return {(x["family"], x["element_id"].split(":")[-1]): x for x in d["_zones"]}


def test_values_and_statuses(z):
    p = z[("B1-02", "Z1-PITS-24")]
    assert (p["action"], p["_value"], p["_status"]) == ("VALUE", 208.164757, "ESTIMATED")
    assert "186.974333" in p["printed_minimum_bound"] and "195.699801" in p["sensitivity"]
    assert "0.458211" in p["held_items"] and "working space" in p["held_items"]
    q = z[("B1-02", "Z1-POOL")]
    assert (q["_value"], q["_status"]) == (17.776576, "DRAWING-CONFIRMED")
    b = z[("B1-03", "Z1-PITS-24")]
    assert (b["_lo"], b["_hi"], b["_status"]) == (119.963335, 128.643547, "PARTIALLY VERIFIED 6 / 8")
    assert b["_layers"]["count"] == 11
    assert b["_hi"] == pytest.approx(208.164757 - 71.925255 - 7.595955, abs=1e-6)
    assert b["_lo"] == pytest.approx(208.164757 - 71.925255 - 16.276167, abs=1e-6)
    f = z[("B1-02", "Z1-PIT-F10F")]
    assert (f["_lo"], f["_hi"]) == (7.2645, 8.39175)
    assert {k for k, x in z.items() if x["action"] == "ADD_HELD"} == {("B1-03", "Z1-PIT-F10F"), ("B1-03", "Z1-PIT-FF")}
    assert not any(x["_code"] == A.DSP for x in z.values())


def test_trench_envelope_holds_both_merged_readings(z):
    t = z[("B1-02", "Z1-TRENCH-EXT-GB-MAIN")]
    assert t["_status"] == "HELD"
    assert (t["_lo"], t["_hi"]) == (pytest.approx(1.432834 - 0.229565, abs=1e-6), 1.432834)
    assert t["_lo"] <= 1.391722 <= 1.418002 <= t["_hi"]


def test_edited_input_refused(monkeypatch):
    monkeypatch.setitem(T.PINS, T.FILL, "0" * 64)
    with pytest.raises(SystemExit, match="sha256"):
        T.build()
