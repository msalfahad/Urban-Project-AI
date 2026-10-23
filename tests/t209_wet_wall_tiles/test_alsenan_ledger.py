"""T-209: the development villa's wet-wall tile ledger reproduces from committed files; the two methods stay apart,
held rooms never count as 0, the reconciliation to the freelancer closes in units, the over-door band explains the Q-48
rough column, and the T-206 sunken panels hold the drawing-derived height of every room under one."""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research" / "agents_t209"
sys.path.insert(0, str(HERE))

import alsenan_t209 as A                                               # noqa: E402


def _rows():
    return {r["ROOM"]: r for r in csv.DictReader((HERE / "WET_WALL_TILES_T209.csv").open(encoding="utf-8"))}


def test_committed_files_reproduce():
    assert A.main(["--check"]) == 0


def test_summary_figures():
    s = json.loads((HERE / "summary.json").read_text(encoding="utf-8"))
    a = s["method_a"]
    assert s["rooms"] == 18 and a["net_m2"] == 340.4134 and len(a["rooms_assumed_owner_approved"]) == 12
    assert a["held_rooms"] == ["GF-02", "GF-03", "GF-05", "GF-06", "GF-10", "GF-11"]
    assert a["over_door_band_m2"] == 14.6675 and abs(a["net_m2"] - a["q48_rough_m2"] - a["over_door_band_m2"]) < 1e-3
    assert s["method_b"]["drawing_confirmed_rooms"] == ["1F-08"] and s["method_b"]["net_m2"] == [22.5466, 23.2006]
    lf = s["like_for_like"]
    assert lf["rooms"] == 11 and lf["own_a_m2"] == 308.0713 and lf["freelancer_m2"] == 295.44
    assert lf["max_abs_residual_m2"] <= 1e-4
    assert round(lf["freelancer_m2"] + lf["length_m2"] + lf["height_m2"] + lf["doors_m2"] + lf["windows_m2"], 3) == \
        round(lf["own_a_m2"], 3)
    assert s["freelancer"]["total_m2"] == s["freelancer"]["stated_total_m2"] == 433.83


def test_held_rooms_have_no_zero_quantity():
    rows = _rows()
    for rid in ("GF-10", "GF-11"):
        assert rows[rid]["A_NET_M2"] == "" and rows[rid]["A_STATUS"].startswith("HELD")
    for rid in ("GF-02", "GF-03", "GF-05", "GF-06"):
        assert rows[rid]["A_STATUS"].startswith("HELD") and float(rows[rid]["A_NET_M2"]) > 0


def test_sunken_panels_hold_the_drawing_derived_height():
    ov = json.loads((HERE / "SUNKEN_OVERLAY_T209.json").read_text(encoding="utf-8"))
    rows = _rows()
    under = [k for k, v in ov.items() if isinstance(v, dict) and "under_sunken_m2" in v and v["under_sunken_m2"] > 0.01]
    for rid in under:
        if rid in rows:
            assert rows[rid]["B_STATUS"].startswith("HELD"), rid
    # registration check: the 1F laundry has no sunken hatch (T-206), the 2F W.C. sits on its panel
    assert ov["own_floor"]["1F-07"]["on_sunken_m2"] == 0.0 and ov["own_floor"]["2F-02"]["share"] > 0.95
    assert ov["1F-07"]["under_sunken_m2"] > 5.0          # the laundry is under the 2F W.C. panel


def test_window_hosts_and_heads():
    rows = _rows()
    assert "W06" in rows["GF-13"]["WINDOWS"] and rows["GF-12"]["WINDOWS"] == ""
    assert rows["1F-12"]["A_WINDOWS_M2"] == "1.08"          # W18 0.50 x (3.00 - 0.84), printed
