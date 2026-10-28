"""T-320 on the development villa (research/agents_t320; inputs are the merged research ledgers T-170, T-174 / T-230,
T-183 r2, T-189, T-204, T-205, T-233, T-242, T-253: values, DXF handles and coordinates only). Pins the closure of the
buried-structure displacement below the existing ground (zone Z1) against the merged figures, every component once."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t320"))
import displacement_ledger_v1 as X  # noqa: E402
import t320_alsenan_check as A  # noqa: E402


@pytest.fixture(scope="module")
def out():
    return A.run()


def test_closes_on_the_t170_net_figures(out):
    res, _ = out
    p = res["pits24_net_m3"]
    assert p["BLINDING"] == pytest.approx(12.9234375, abs=1e-6)       # F-T170-01 net (gross 12.957)
    assert p["UNDERLAY"] == pytest.approx(7.6895, abs=1e-6)           # = T-219 109.85 m2 x 0.07
    assert p["FOOTING"] == pytest.approx(52.919, abs=1e-6)            # F9 / FN 0.14 x 0.30 once
    assert res["totals"]["netted_m3"] == pytest.approx(0.0335625 + 0.0098 + 0.042, abs=1e-6)


def test_closes_on_the_t233_lines(out):
    res, _ = out
    c = res["t233_closure"]
    assert c["ours_24_plus_FF"] == pytest.approx(c["footing_line_m3"], abs=1e-6)             # 64.304
    assert c["ours_24_inside_plot_plus_FF"] == pytest.approx(c["blinding_line_m3"], abs=1e-6)  # 14.990438
    assert res["d14_beyond_plot_m3"] == pytest.approx(0.189)


def test_z1_established_and_family_sum(out):
    res, _ = out
    assert res["z1_established_m3"] == pytest.approx(105.162974, abs=1e-5)
    assert res["z1_by_family_sum_m3"] == pytest.approx(res["z1_established_m3"], abs=1e-6)
    f = res["z1_by_family_m3"]
    assert f["straps outside the footings (3)"] == pytest.approx(3.3905)
    assert f["upper boundary G.B at N.G. (5 runs)"] == pytest.approx(3.5256)
    assert f["main-house exterior ground-beam blinding (17 runs)"] == pytest.approx(15.96 / 0.95 / 0.30 * 0.05,
                                                                                    abs=2e-3)


def test_necks_bound_not_a_neck_quantity(out):
    res, led = out
    n = res["necks"]
    assert n["n"] == 36 and n["bounded"] == 29
    assert n["at_least_m3"] == pytest.approx(4.3278, abs=1e-6)
    assert n["coef_m3_per_m"] == pytest.approx(4.86, abs=1e-6)        # sum of the 29 printed sections
    held = dict(n["conflict_or_held"])
    assert sum(1 for v in held.values() if v == X.CONFLICT) == 1 and len(held) == 7    # C8 10E0; 4 lift; F10 / F x2
    for c in led["components"]:
        if c["kind"] == "NECK" and c["value_m3"] is not None:
            assert c["status"] == X.BOUND_AT_LEAST and "FORMATION_ONLY_A_LIMIT" in c["held"]


def test_pool_envelope_decomposes_and_matches_t183(out):
    res, _ = out
    d = res["pool_decomposition"]
    assert sum(d.values()) == pytest.approx(res["pool_envelope_m3"], abs=1e-5)
    assert res["pool_envelope_m3"] == pytest.approx(12.216759 * 1.50, abs=1e-5)
    rc = res["pool_rc_check_m3"]
    assert rc["base"] + rc["walls_full_1_20"] == pytest.approx(7.202, abs=1e-3)      # T-183 r2 VERIFIED RC
    assert d["walls_below_EG"] + rc["walls_above_EG_excluded"] == pytest.approx(rc["walls_full_1_20"])
    assert res["f8_pool"]["footprint_in_outer_m2"] == pytest.approx(1.2964, abs=1e-3)  # T-189 / T-183 interface 1
    assert res["f8_pool"]["env_area_numeric_m2"] == pytest.approx(12.216759, abs=1e-3)


def test_conflicts_and_holds_stay_open_never_zero(out):
    res, led = out
    conf = [x for x in led["shared"] if x["status"] == X.CONFLICT]
    assert len(conf) == 3 and all(x["value_m3"] is None for x in conf)
    assert res["totals"]["open_shared_range_m3"][1] >= 1.121 - 1e-3
    comp = {c["id"]: c for c in led["components"]}
    for cid, c in comp.items():
        if c["status"] in (X.HELD, X.CONFLICT):
            assert c["value_m3"] is None, cid
    assert comp["GB:LOWER_ROW_TWO_BEAM_DETAIL"]["value_m3"] is None
    assert res["backfill"] == (None, X.HELD) and res["disposal"] == (None, X.HELD)
    assert res["excavated"]["value_m3"] is None


def test_ground_beams_above_eg_contribute_zero_with_their_basis(out):
    _, led = out
    for c in led["components"]:
        if c["id"].startswith("GB:EXT-MAIN") and c["kind"] == "GROUND_BEAM":
            assert c["value_m3"] == 0.0 and c["above_ground_m3_excluded"] > 0      # bottom on N.G. +-0.00
        if c["status"] == X.ZERO_BY_BOUND:
            assert c["value_m3"] == 0.0 and c["held"] and c["held"][0].startswith("condition")
