"""T-176: the development villa's procurement ledger reproduces from the merged MASONRY_AREA_V1 r2 rows; the net
installed m2 is read, never re-derived; procurement, mortar, cement and sand stay HELD without named parameters;
held walls never count as 0; the sensitivity table is labelled NOT RELEASED; no 100 mm wall in the census."""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research" / "agents_t176"
sys.path.insert(0, str(HERE))

import alsenan_t176 as A                                                   # noqa: E402


def _csv(name):
    return list(csv.DictReader((HERE / name).open(encoding="utf-8")))


def test_committed_files_reproduce():
    assert A.main(["--check"]) == 0


def test_net_is_read_from_masonry_area_v1_r2():
    t108 = {r["row_id"]: r for r in csv.DictReader((ROOT / "research/agents_t108/T108_BY_WALL.csv").open(encoding="utf-8"))}
    for r in _csv("BLOCK_PROCUREMENT_BY_WALL.csv"):
        assert r["net_m2 (MASONRY_AREA_V1 r2)"] == t108[r["row_id"]]["net_m2"]
        assert r["net_status"] == t108[r["row_id"]]["net_status"]


def test_black_totals_by_thickness_and_status():
    s = json.loads((HERE / "summary.json").read_text(encoding="utf-8"))["black"]
    assert s["net_established_m2"] == 290.052 and s["installed_units"] == pytest.approx(3625.65)
    bt = s["by_t (net status of the area; units / mortar status ASSUMED — OWNER-APPROVED via Q-75)"]
    assert bt["0.15"]["DRAWING-CONFIRMED"]["net_m2"] == 103.332
    assert bt["0.15"]["ASSUMED — OWNER-APPROVED"]["net_m2"] == 79.005
    assert bt["0.20"]["DRAWING-CONFIRMED"]["net_m2"] == 107.715
    assert s["mortar_wet_m3"] == pytest.approx(182.337 * 0.0110625 + 107.715 * 0.01475, abs=1e-4)


def test_held_rows_carry_no_number_and_procurement_is_held():
    for r in _csv("BLOCK_PROCUREMENT_BY_WALL.csv"):
        if r["net_status"] in ("HELD", "UNKNOWN"):
            assert r.get("installed_units", "") == "" and r.get("mortar_wet_m3", "") == ""
        if r["product"]:
            assert r["procurement_units"] == "" and r["procurement_status"] in ("HELD", "UNKNOWN")
            assert r["cement_bags"] == "" and r["cement_sand_status"] == "HELD"


def test_sensitivity_is_labelled_and_named():
    rows = _csv("WASTE_SENSITIVITY.csv")
    assert rows and all(r["parameter_source"] for r in rows)
    assert any("NOT RELEASED" in k for k in rows[0])


def test_thickness_census_has_no_100_mm_and_d12_flagged():
    s = json.loads((HERE / "summary.json").read_text(encoding="utf-8"))
    assert set(s["thickness_census_gross_m2 (MASONRY_AREA_V1 rows)"]) == {"0.15", "0.20", "0.40"}
    flagged = {r["row_id"] for r in _csv("BLOCK_PROCUREMENT_BY_WALL.csv") if r["d12_flag"]}
    assert {"GF-W01", "GF-W28", "1F-W23"} <= flagged and len(flagged) == 20
