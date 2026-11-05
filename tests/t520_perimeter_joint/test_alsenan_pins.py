"""T-520 on the development villa: committed outputs reproduce from the pinned merged inputs; the 0.20 m walls of the
candidate by hand; the drawing-read run ends; held walls stay blank by name; the cement / sand is its own key."""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research" / "agents_t520"
sys.path.insert(0, str(HERE))
import t520_alsenan as A  # noqa: E402

F20 = 0.92625 * 0.20 * 0.010


def _csv(name):
    return list(csv.DictReader((HERE / "out" / name).open(encoding="utf-8")))


def _w():
    return {r["wall_id"]: r for r in _csv("PERIMETER_BY_WALL_T520.csv")}


def test_committed_files_reproduce():
    assert A.main(["--check"]) == 0


def test_every_wall_once():
    rows = _csv("PERIMETER_BY_WALL_T520.csv")
    ids = [r["wall_id"] for r in rows]
    assert len(ids) == 24 and len(set(ids)) == 24


def test_gf_w01_by_hand():
    r = _w()["GF-W01"]
    # soffit 16.47 m; 4 segments between columns: 3 x 3.75 + (3.75 + 0.35 beside the CB1 drop); 5 top corners
    hand = 16.47 * F20 + (4 * 3.75 + 0.35) * F20 - 5 * F20 * 0.010
    assert float(r["perimeter_m3"]) == pytest.approx(hand, abs=1e-6)
    assert r["status"] == "COMPUTED"


def test_020_set_and_t498_stage():
    s = json.loads((HERE / "out" / "SUMMARY_T520.json").read_text(encoding="utf-8"))["computed_020"]
    assert s["walls"] == ["GF-W01", "1F-W02", "1F-W03", "1F-W09"]
    assert s["panel_m3"] == pytest.approx(1.269444, abs=1e-6)
    w = _w()
    tot = sum(float(w[k]["perimeter_m3"]) for k in s["walls"])
    assert s["perimeter_m3"] == pytest.approx(tot, abs=1e-6)
    # 1F-W03: two segments between columns (B7 3.45, B2 3.80), soffit 3.90 m, 2 corners
    assert float(w["1F-W03"]["perimeter_m3"]) == pytest.approx(3.90 * F20 + 7.25 * F20 - 2 * F20 * 0.01, abs=1e-6)
    # 1F-W09: the T_STEM end meets a column (drawing read, T-520): one segment column to column, 3.80
    assert float(w["1F-W09"]["perimeter_m3"]) == pytest.approx(1.80 * F20 + 3.80 * F20 - F20 * 0.01, abs=1e-6)
    assert s["t498_stage_plus_perimeter_m3"] == pytest.approx(1.269444 + tot, abs=1e-6)


def test_held_walls_blank_by_name():
    w = _w()
    for k in ("2F-W01", "2F-W05", "2F-W06", "2F-W08"):
        assert w[k]["status"] == "HELD" and w[k]["perimeter_m3"] == "" and "D-39" in w[k]["held"]
        assert "b_r" in w[k]["expression"]
    assert w["GF-W22"]["perimeter_m3"] == "" and "D-27" in w["GF-W22"]["held"]
    for k, r in w.items():
        if r["t_m"] == "0.15":
            assert r["perimeter_m3"] == "" and r["status"] == "HELD"          # 0.15 module not stated (T-506)
            assert r["perimeter_figure_m3"] != ""


def test_drawing_read_column_ends():
    E = {(r["wall_id"], r["end"]): r["class"] for r in _csv("END_CONDITIONS_T520.csv")}
    for k in ("1F-W09", "1F-W23", "2F-W01", "2F-W08"):
        assert E[(k, "0")] == "COLUMN"                                       # outside the T-274 run pieces
    assert E[("GF-W28", "0")] == "NONE" and E[("GF-W28", "1")] == "NONE"


def test_materials_own_producer_key():
    m = json.loads((HERE / "out" / "SUMMARY_T520.json").read_text(encoding="utf-8"))["materials_perimeter_020"]
    s = json.loads((HERE / "out" / "SUMMARY_T520.json").read_text(encoding="utf-8"))["computed_020"]
    assert m["cement_bags"] == pytest.approx(8.0 * s["perimeter_m3"], abs=1e-6)
    assert m["sand_m3"] == pytest.approx(1.1 * s["perimeter_m3"], abs=1e-6)
    assert "own key" in m["producer_key"] and "Q-78" in m["source"]


def test_no_drawing_coordinates_in_outputs():
    for r in _csv("JUNCTIONS_T520.csv"):
        assert 0 <= float(r["x0_m"]) <= 25 and 0 <= float(r["x1_m"]) <= 25   # stations along a run, not plan x / y
