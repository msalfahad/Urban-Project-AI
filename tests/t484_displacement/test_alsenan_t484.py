"""T-484 development-villa records (no drawing needed: the committed summary / CSV of the own DXF re-measure)."""
from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parents[2] / "research" / "agents_t484"
S = json.loads((HERE / "summary_t484.json").read_text())
NECKS = list(csv.DictReader(open(HERE / "NECKS_T484.csv")))


def test_drawing_identity():
    assert S["dxf_sha8"] == "9f9d1179"


def test_neck_census_36():
    st = [r["status"] for r in NECKS]
    assert len(NECKS) == 36
    assert st.count("CALCULATED") == 29 and st.count("CONFLICT") == 1 and st.count("OTHER_ZONE") == 6
    calc = [r for r in NECKS if r["status"] == "CALCULATED"]
    assert sum(float(r["m3"]) for r in calc) == pytest.approx(S["necks"]["m3"], abs=1e-6)
    assert S["necks"]["m3"] == pytest.approx(5.154, abs=1e-6)
    # every calculated neck: schedule section x (1.50 - H) under S01, no part inside the pool envelope
    for r in calc:
        assert float(r["m3"]) == pytest.approx(float(r["schedule_m2"]) * (1.50 - float(r["H"])), abs=1e-6)
        assert float(r["in_env_m2"]) == 0.0 and float(r["env_clearance_m"]) > 0.30


def test_c8_conflict_range():
    assert S["c8_conflict_m3"] == [0.24, 0.27]


def test_strap_ends_agree_with_t350r2():
    assert S["strap_ends"]["m3"] == pytest.approx(0.179630, abs=5e-5)
    ends = [r for r in S["strap_ends"]["rows"] if r["zone"] == "PITS24"]
    assert len(ends) == 5


def test_backfill_narrowed_and_named():
    b = S["pits_backfill"]
    lo, hi = b["backfill_t484_m3"]
    assert lo < hi and b["width_m3"][1] < b["width_m3"][0]
    named = b["named_residual_range"]
    assert hi - lo == pytest.approx(sum(named.values()), abs=1e-5)


def test_beam_reconciliation_monotone():
    st = list(S["beam_solids"]["reconciliation_without_upper_gb_m3"].values())
    highs = [h for _, h in st]
    assert highs == sorted(highs, reverse=True)
    assert S["beam_solids"]["total_m3"][0] <= S["beam_solids"]["total_m3"][1]


def test_f10f_union_inside_outline():
    f = S["f10f"]
    assert f["F10_plus_F_union_plan_m2"][1] <= f["outline_plan_m2"] + 1e-9
    assert f["F10_plus_F_sum_plan_m2_T478"][0] > f["outline_plan_m2"]       # the sum counts the overlap twice
