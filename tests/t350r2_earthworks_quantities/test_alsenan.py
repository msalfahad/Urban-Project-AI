"""T-350 r2 on the development villa (research/agents_t350r2; inputs are merged research ledgers only: T-170 / T-347
pits, T-320 displacement, T-189 pool frame, T-183 r2 pool, T-253 ground-beam blinding, T-478 F10 + F scenarios).
Pins the S01 ESTIMATED earthworks quantities, their closure and the items that must stay HELD."""
from __future__ import annotations

import csv
import io
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t350r2"))
import t350r2_alsenan as A  # noqa: E402


@pytest.fixture(scope="module")
def res():
    return A.run()


def test_plan_closes_two_ways_and_corrects_the_v3043_bound(res):
    p = res["pits24"]["plan"]
    assert p["union_m2"] == pytest.approx(129.234375, abs=1e-6)          # T-347 verdict / T-445 (24 neat plans once)
    # own geometry (T-170 outlines + T-189 pool frame + plot rectangle) vs own route-G read of the DXF
    assert p["zone_plan_m2"] == pytest.approx(p["zone_plan_route_g_m2"], abs=1e-3)
    pi = res["pits24"]["pool_interfaces"]["pits_in_env"]
    f4 = next(v for v in pi.values() if v["type"] == "F4")
    fn = next(v for v in pi.values() if v["type"] == "FN")
    f8 = next(v for v in pi.values() if v["type"] == "F8")
    assert f8["neat_in_env_m2"] == pytest.approx(1.99957, abs=1e-5)    # T-320 f8_pool reproduced
    # V3.0.43 plan 125.344805 removed only F8's envelope part and removed F8's beyond-plot strip twice
    corr = -(f4["neat_in_env_m2"] + fn["neat_in_env_m2"] - f8["neat_in_env_beyond_plot_m2"])
    assert p["correction_m2"] == pytest.approx(corr, abs=1e-3)
    assert p["v3043_bound_plan_m2"] == pytest.approx(125.344805, abs=1e-6)
    assert res["pits24_printed_minimum_bound_m3"] == pytest.approx(p["zone_plan_m2"] * 1.50, abs=1e-6)
    assert res["pits24_printed_minimum_bound_m3"] < 188.017207          # the V3.0.43 AT_LEAST figure was high


def test_second_footing_pool_interface(res):
    f4 = next(v for v in res["pits24"]["pool_interfaces"]["pits_in_env"].values() if v["type"] == "F4")
    assert f4["footprint_in_outer_shell_plan_m2"] > 0.25                # F4 footing plan enters the pool shell plan
    assert f4["footprint_in_env_m2"] > f4["footprint_in_outer_shell_plan_m2"]


def test_s01_excavation_and_sensitivity(res):
    p = res["pits24"]
    A = p["plan"]["zone_plan_m2"]
    assert p["formation_m"] == pytest.approx(-1.67) and p["depth_m"] == pytest.approx(1.67)
    assert p["excavation_insitu_m3"] == pytest.approx(A * 1.67, abs=1e-5)
    s = res["pits24_sensitivity"]
    assert s["+0.10"]["excavation_insitu_m3"] - p["excavation_insitu_m3"] == pytest.approx(A * 0.10, abs=1e-5)
    assert p["excavation_insitu_m3"] - s["-0.10"]["excavation_insitu_m3"] == pytest.approx(A * 0.10, abs=1e-5)


def test_displacement_components_once(res):
    p = res["pits24"]
    d = p["displacement"]
    pi = p["pool_interfaces"]["pits_in_env"].values()
    fp_env = sum(v["footprint_in_env_m2"] for v in pi)
    assert d["blinding"] == pytest.approx(0.10 * p["plan"]["zone_plan_m2"], abs=1e-6)   # one layer
    assert d["blinding"] == pytest.approx(d["blinding_check_from_ledger"], abs=1e-4)      # T-320 ledger route
    assert d["underlay"] == pytest.approx(7.6895 - fp_env * 0.07, abs=1e-6)
    assert d["footings"] == pytest.approx(52.919 - sum(v["footprint_in_env_m2"] * v["H"] for v in pi), abs=1e-6)
    assert d["necks_29"] == pytest.approx(4.3278 + 4.86 * 0.17, abs=1e-3)    # less a 0.0003 m2 sliver of one CN
    assert d["neck_C8_conflict"] == pytest.approx([0.24, 0.27], abs=1e-6)
    assert d["strap_ends_in_projection_strip"] == pytest.approx(
        1.5925 / 4.55 * 0.1 + 2 * 1.1464 / 2.2927 * 0.1 * 1.01898 + 2 * 0.6516 / 3.258 * 0.1 * 1.06818, abs=1e-6)
    pre = p["backfill_before_beam_solids_m3"]
    assert pre[0] == pytest.approx(p["excavation_insitu_m3"] - d["total"][1], abs=1e-6)
    assert pre[1] - pre[0] == pytest.approx(0.03, abs=1e-6)                # only the C8 section conflict
    assert p["layers"] == 11                                               # 1.57 m / 0.15 OWNER-PROVISIONAL


def test_ground_beam_solids_over_the_pits(res):
    p = res["pits24"]
    b = p["beam_solids_in_zone"]["by_category_m3"]
    assert b["MAIN_INT_D"] == [0.0, 0.0]                                   # above EG (ZERO_BY_BOUND condition)
    assert 1.35 < b["MAIN_EXT"][0] <= b["MAIN_EXT"][1] < 1.45              # ext blinding run ends over the pits
    assert b["MAIN_EXT"][1] < 2.79956                                      # never more than the whole trench
    assert b["UPPER_BOUNDARY_GB"][0] == pytest.approx(0.40 * p["beam_solids_in_zone"]["upper_boundary_plan_over_zone_m2"], abs=1e-6)
    lo, hi = p["backfill_compacted_m3"]
    pre = p["backfill_before_beam_solids_m3"]
    assert lo == pytest.approx(pre[0] - b["total"][1], abs=1e-6) and hi == pytest.approx(pre[1] - b["total"][0], abs=1e-6)
    tr = res["gb_ext_main"]
    assert tr["excavation_outside_pits_m3"][0] == pytest.approx(2.79956 - b["MAIN_EXT"][1], abs=1e-6)


def test_lower_ground_beam_row_flips_inside_the_s01_sensitivity(res):
    lg = res["lower_gb_row"]
    assert lg["required"] == {"S01": False, "S01 -0.10": False, "S01 +0.10": True}


def test_f10f_scenarios_kept_apart(res):
    f = res["f10f"]
    assert set(f) == {"F10 alone", "F10 + F rows", "drawn outline"}
    assert f["F10 alone"]["footing_m3"] == pytest.approx(1.960)
    assert f["F10 + F rows"]["footing_m3"] == pytest.approx(2.176)
    assert f["drawn outline"]["footing_m3"] == pytest.approx(2.275)      # owner S02 range 1.960 .. 2.275
    assert f["F10 alone"]["excavation_in_plot_m3"][0] == pytest.approx(4.35 * 1.67)


def test_fill_rows_hold_what_is_held(res):
    rows = A.fill_rows(res)
    by = {r["row_id"]: r for r in rows}
    for k, r in by.items():
        if r["proposed_state"] in ("HELD", "UNCHANGED", "PROPOSED_NEW_LINE_HELD", "NOT_REQUIRED_UNDER_S01"):
            assert r["value_m3"] in ("", None), k                           # a held line never carries a value
    disp = by["B1-04 DISPOSAL|ALL ZONES"]
    assert disp["proposed_state"] == "HELD" and disp["value_m3"] == ""
    assert by["B1-02 EXCAVATION|Z1-PIT-FF (lift raft and pit)"]["proposed_state"] == "HELD"
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=A.FIELDS)
    w.writeheader()
    w.writerows(rows)
    assert len(rows) == 22                                       # 18 V3.0.43 zone lines + 4 coverage-gap rows
