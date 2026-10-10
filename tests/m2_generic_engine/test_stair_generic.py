"""M2 generic stair flight: hand-derived geometry and the library's marble rules; scenarios never choose."""

from __future__ import annotations

import math

import pytest

from engine.source import stair_generic as SG


def test_owner_worked_example_per_step():
    # UP-STAIR-003 worked example: width 1.20, tread 0.30, rise 0.16 -> tread 0.360 m2, visible riser 0.156 m2
    f = SG.flight(0.16 * 2, 2, 0.30, width_m=1.20)
    assert f["riser_m"] == pytest.approx(0.16)
    assert f["marble"]["tread_m2"] / f["treads"] == pytest.approx(0.360)
    assert f["marble"]["riser_m2"] / f["n_risers"] == pytest.approx(1.20 * (0.16 - 0.03))


def test_flight_geometry_by_hand():
    f = SG.flight(4.2, 27, 0.30)                     # 1F -> 2F, 27 counted risers, tread 300 (owner)
    R = 4.2 / 27
    assert f["riser_m"] == pytest.approx(R) and f["treads"] == 26 and f["run_m"] == pytest.approx(7.8)
    assert f["inclined_m"] == pytest.approx(math.hypot(7.8, 26 * R))
    lo = f["inclined_m"] * 0.15 + 26 * R * 0.30 / 2
    assert f["concrete_exposure_m3"]["low"] == pytest.approx(lo)
    assert f["concrete_exposure_m3"]["state"] == "UNRESOLVED_WAIST_NOT_ESTABLISHED"
    assert f["marble"]["step_commercial_lm"] == pytest.approx(27.0)          # UP-STAIR-008 lm, not an area


def test_scenarios_are_side_by_side_not_chosen():
    s = SG.scenarios(4.5, (27, 28), 0.30)
    assert [x["n_risers"] for x in s] == [27, 28]
    assert s[0]["riser_m"] == pytest.approx(4.5 / 27) and s[1]["riser_m"] == pytest.approx(4.5 / 28)
    assert all("chosen" not in x for x in s)


def test_sanity_range_is_a_diagnostic_only():
    f = SG.flight(4.5, 27, 0.30)                    # 0.1667 m: outside the 0.155-0.165 typical band
    assert f["sanity"] == "OUTSIDE_TYPICAL_RANGE" and f["riser_m"] == pytest.approx(4.5 / 27)
