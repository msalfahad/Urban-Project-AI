"""T-313 development-villa pins on the committed ledger (no drawing needed): every opening of the merged census once,
each side component once, the 27 candidate reveal lines each bound to exactly one window, nothing HELD carried as 0,
and the exterior reveal edge reconciliation to the merged corners ledger (T-162 r2) closing with named causes."""

import csv
import json
from collections import Counter
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / "research" / "agents_t313"


def _rows(name):
    with open(D / name, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_every_census_opening_once_and_each_component_once():
    led = _rows("REVEAL_LEDGER_T313.csv")
    inv = _rows("../agents_t249/OPENINGS_T249.csv")
    assert {r["opening"] for r in led} == {r["ID"] for r in inv}
    c = Counter((r["opening"], r["side"], r["component"]) for r in led)
    assert max(c.values()) == 1


def test_reveal_lines_each_one_window_and_all_27_bound():
    led = _rows("REVEAL_LEDGER_T313.csv")
    by_line = {}
    for r in led:
        if r["line_id"] != "NO_LINE":
            by_line.setdefault(r["line_id"], set()).add(r["opening"])
    assert len(by_line) == 27
    assert all(len(v) == 1 for v in by_line.values())
    assert not any(r["line_id"] != "NO_LINE" for r in led if r["component"] in ("JAMBS", "HEAD"))


def test_held_and_unresolved_never_zero():
    for r in _rows("REVEAL_LEDGER_T313.csv"):
        if r["state"] in ("HELD", "UNRESOLVED"):
            assert r["m2"] == "" and r["ml"] == ""
        if r["state"] == "NONE":
            assert float(r["m2"]) == 0.0


def test_measured_window_depths_close_to_the_wall_thickness():
    for r in _rows("WINDOW_DEPTHS_T313.csv"):
        if r["depth_in_m"] and r["depth_out_m"]:
            assert float(r["depth_in_m"]) + float(r["frame_band_m"]) + float(r["depth_out_m"]) == \
                pytest.approx(float(r["wall_t_plan_m"]), abs=1e-3)
            assert float(r["wall_t_plan_m"]) == pytest.approx(float(r["wall_t_t150_m"]), abs=1e-3)


def test_edge_reconciliation_to_t162_closes():
    s = json.loads((D / "summary.json").read_text(encoding="utf-8"))["edge_reconciliation"]
    rec = _rows("EDGE_RECONCILIATION_T313.csv")
    assert s["t162_r2_measured_ml"] == pytest.approx(137.110)
    assert s["r1_minus_r2"] == pytest.approx(52.520)          # the register's 189.630 is r1 (jambs counted twice)
    open_known = sum(float(r["t162_known_part_ml"]) for r in rec if r["t313_ml"] == "" and r["t162_status"] != "ASSUMED")
    assert s["t162_known_part_same_openings_ml"] + open_known == pytest.approx(137.110, abs=1e-6)
    jambs = sum(float(p.split("+")[1]) for r in rec for p in r["cause"].split("; ") if p.startswith("jambs newly"))
    no_sill = sum(float(p.split("-")[-1]) for r in rec for p in r["cause"].split("; ") if "no sill arris" in p)
    assert s["t162_known_part_same_openings_ml"] + jambs - no_sill == pytest.approx(s["t313_windows_measured_ml"],
                                                                                    abs=1e-6)
