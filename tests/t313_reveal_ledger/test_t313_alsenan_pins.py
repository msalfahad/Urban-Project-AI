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


def test_lines_each_one_opening_27_window_and_22_door_lines_bound():
    led = _rows("REVEAL_LEDGER_T313.csv")
    by_line = {}
    for r in led:
        if r["line_id"] != "NO_LINE":
            by_line.setdefault(r["line_id"], set()).add(r["opening"])
    assert all(len(v) == 1 for v in by_line.values())
    win = {r["line_id"] for r in led if r["kind"] in ("WINDOW", "FLOOR_GLAZING") and r["line_id"] != "NO_LINE"}
    door = {r["line_id"] for r in led if r["kind"] == "DOOR" and r["line_id"] != "NO_LINE"}
    assert len(win) == 27 and len(door) == 22 and not win & door
    # window jambs / head: no line in any family; door jambs + head: both in the door's one FIN.PLASTER line
    assert not any(r["line_id"] != "NO_LINE" for r in led
                   if r["kind"] in ("WINDOW", "FLOOR_GLAZING") and r["component"] in ("JAMBS", "HEAD"))
    for d in {r["opening"] for r in led if r["line_id"] in door}:
        assert len({r["line_id"] for r in led if r["opening"] == d}) == 1


def test_door_plaster_lines_reconciled_per_door():
    rec = _rows("DOOR_PLASTER_RECONCILIATION_T313.csv")
    assert len(rec) == 22 and len({r["line_id"] for r in rec}) == 22
    fam = {r["line_id"]: r for r in _rows("FAMILY_SEARCH_T313.csv")}
    for r in rec:
        assert fam[r["line_id"]]["item_code"] == "FIN.PLASTER" and fam[r["line_id"]]["role"].startswith("BOUND")
        if r["verdict"] == "EQUAL":
            assert float(r["ledger_m2"]) == pytest.approx(float(r["line_m2"]), abs=1e-6)
        else:       # bounded line: the ledger inside [low, high]
            assert r["verdict"] == "WITHIN_BOUND"
            assert float(r["line_low"]) - 1e-6 <= float(r["ledger_m2"]) <= float(r["line_high"]) + 1e-6


def test_missing_scope_has_no_component_another_family_carries():
    s = json.loads((D / "summary.json").read_text(encoding="utf-8"))
    led = {(r["opening"], r["side"], r["component"]): r for r in _rows("REVEAL_LEDGER_T313.csv")}
    carried = {r["opening"] for r in _rows("FAMILY_SEARCH_T313.csv") if r["role"].startswith("BOUND")}
    total = 0.0
    for key, v in s["missing_scope"].items():
        kind, side, comp = key.split(":")
        for o in v["openings"]:
            assert led[(o, side, comp)]["line_id"] == "NO_LINE"
            assert not (kind == "DOOR" and o in carried)
        total += v["m2"]
    assert total == pytest.approx(s["missing_scope_m2"], abs=1e-6)


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
