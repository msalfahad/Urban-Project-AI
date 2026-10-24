"""T-253 Alsenan ledger (committed inputs only: ALSENAN_BOUNDARY_INPUT.json from 'ST7757 dxf.dxf' sha 9f9d1179, the
merged T-242 ledger). Re-runs the check without writing and pins the engineering results."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research" / "agents_t253"
sys.path.insert(0, str(HERE))
import t253_alsenan_check as C  # noqa: E402

ROWS, SUM = C.main(write=False)
INP = json.loads((HERE / "ALSENAN_BOUNDARY_INPUT.json").read_text(encoding="utf-8"))
BY = {r["item"]: r for r in ROWS}


def test_input_is_values_only():
    txt = (HERE / "ALSENAN_BOUNDARY_INPUT.json").read_text(encoding="utf-8")
    assert INP["source"]["structural_sha256"].startswith("9f9d1179")
    assert not re.search(r"\d{5,}\.\d", txt)


def test_boundary_runs_each_piece_once():
    runs = {r["run_id"]: r for b in INP["boundary_bands"] for r in b["runs"]}
    assert {k: v["length_m"] for k, v in runs.items()} == {"7FE#1": 31.37, "7FE#2": 8.1, "7FE#3": 2.25,
                                                           "7FC#1": 1.15, "810#1": 1.2}
    for b in INP["boundary_bands"]:
        assert b["band_area_from_runs_m2"] == pytest.approx(b["plan_m2"], abs=1e-4)
        assert b["overlap_columns_m2"] == 0.0 and b["overlap_pool_m2"] == 0.0
    assert INP["columns_drawn_in_bands"] == 0


def test_boundary_ends_are_members_met_in_3d():
    ends = {r["run_id"]: [e["kind"] for e in r["ends"]] for b in INP["boundary_bands"] for r in b["runs"]}
    assert ends["7FC#1"] == ["COLUMN", "POOL_WALL"]
    assert ends["7FE#2"][0].startswith("COLUMN") and ends["7FE#3"][0] == "POOL_WALL"
    assert "HELD" in BY["810#1"]["basis"]          # the annex-side face: 3-D member not shown, length unaffected


def test_boundary_volume_and_split():
    g = SUM["boundary_gb"]
    assert g["run_length_m"] == pytest.approx(44.07) and g["band_m3_physical"] == pytest.approx(3.5256)
    assert g["beam_line_status"] == "HELD" and g["beam_line_m3"] is None and g["column_each_m3"] == 0.024
    f = g["freelancer"]
    assert f["difference_m3"] == pytest.approx(f["section_part_m3"] + f["length_part_m3"], abs=1e-4)


def test_datum_main_and_annex():
    assert SUM["datum"]["status"] == "CALCULATED" and SUM["datum"]["datum_m"] == 0.0
    assert SUM["depth_main"]["value_m"] == pytest.approx(0.95)
    assert SUM["exterior_main_runs"] == 17 and SUM["exterior_main_m3"] == pytest.approx(15.96, abs=1e-4)
    a = SUM["depth_annex"]
    assert a["status"] == "CONFLICT" and a["value_m"] is None and a["literal_m"] == pytest.approx(0.25)
    assert SUM["annex_runs"] == 9 and SUM["annex_literal_m3"] == pytest.approx(2.228, abs=1e-4)


def test_main_runs_equal_the_t242_high_end():
    for r in ROWS:
        if r["component"].startswith("GB-EXTERIOR MAIN"):
            assert float(r["value_m3"]) == pytest.approx(float(r["high_m3"]), abs=1e-4)


def test_court_runs():
    c = {x["run"]: x for x in SUM["court"]}
    assert c["1811+1812#1"]["length_closed"] is True and "boundary band" in c["1811+1812#1"]["end_reading"]
    assert SUM["court_range_m3"] == [pytest.approx(0.627), pytest.approx(1.41)]
    assert all(BY[k]["status"] == "HELD" and BY[k]["value_m3"] == "" for k in c)


def test_consultant_rows_exact_runs():
    cr = SUM["consultant_rows"]
    assert len(cr["D-33"]["runs"]) == 17 and len(cr["D-34"]["runs"]) == 13
    assert len(cr["D-35 (annex only)"]["runs"]) == 9 and len(cr["M4"]["runs"]) == 5
    assert len(set(cr["D-33"]["runs"]) & set(cr["D-34"]["runs"])) == 5
    assert not set(cr["D-35 (annex only)"]["runs"]) & set(cr["D-35 (main house)"]["runs"])


def test_held_never_zero():
    for r in ROWS:
        if r["status"] in ("HELD", "CONFLICT"):
            assert r["value_m3"] in ("", None)
