"""T-241 Alsenan CONC.BEAM ledger from committed inputs only (T-110 register, T-229 summary, T-145 CB5 span 2, the
T-241 partition input extracted from Drive 'ST7757 dxf.dxf' sha 9f9d1179, route G registers, freelancer cells).
Re-runs the check without writing and pins the engineering results (development villa; not an accuracy claim)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research" / "agents_t241"
sys.path.insert(0, str(HERE))
import t241_alsenan_check as C  # noqa: E402

SUM, ROWS, MARKS, TOT, PART, REC, FR = C.build()


def test_every_run_once_and_line_totals():
    assert SUM["runs"] == 140 and len({r["run"] for r in ROWS}) == 140
    assert SUM["measured_m3"] == pytest.approx(66.016058, abs=1e-5)
    assert TOT["GF"]["measured_m3"] == pytest.approx(39.026985, abs=1e-5)
    assert TOT["1F"]["measured_m3"] == pytest.approx(22.690573, abs=1e-5)
    assert TOT["2F"]["measured_m3"] == pytest.approx(4.2985, abs=1e-5)
    assert SUM["conflict"][0] == pytest.approx(5.144829, abs=1e-5)
    assert SUM["conflict"][1] == pytest.approx(6.11101, abs=1e-5)


def test_held_never_zero_and_named():
    held = [r for r in ROWS if r["status"] == "HELD"]
    assert held and all(r["m3"] is None for r in held)
    assert set(SUM["held_no_value"]) == {"BM-GF-061", "BM-1F-037", "BM-1F-038", "BM-2F-019#2F-031"}
    for r in held:
        assert r["designer"] or r["reason"]


def test_conflicts_kept_as_ranges():
    conf = [r for r in ROWS if r["status"] == "CONFLICT"]
    assert len(conf) == 7 and all(r["m3"] is None and r["m3_low"] < r["m3_high"] for r in conf)


def test_every_t229_strip_and_double_used_once():
    assert SUM["t229_leftovers"] == {"short": [], "double": []}
    ded = sum(v for r in ROWS for _n, v in r["deducts"])
    assert ded == pytest.approx(0.2779, abs=2e-4)       # 6 GF columns + 1F C9 billed twice in released A (T-229)


def test_new_runs():
    by = {r["member"]: r for r in ROWS}
    assert by["BM-GF-035.2"]["status"] == "CALCULATED" and by["BM-GF-035.2"]["m3"] == pytest.approx(0.296)
    assert by["BM-GF-062"]["status"] == "HELD" and by["BM-GF-062"]["m3_low"] == pytest.approx(0.04)
    assert by["BM-2F-019"]["status"] == "HELD" and by["BM-2F-019"]["m3_low"] is None


def test_released_reconciled_per_storey_to_named_causes():
    for st in ("GF", "1F", "2F"):
        assert REC[st]["closed"], (st, REC[st])
    comps = dict(REC["GF"]["components"])
    assert comps["CB5 span 2 in no beam line (T-145; released bills its band 0.1184 as slab)"] == pytest.approx(0.296)
    assert REC["2F"]["diff"] == pytest.approx(0.0, abs=1e-6)


def test_partition_beam_slab_and_columns():
    for st in ("GF", "1F", "2F"):
        p = PART[st]
        # slab panels x route G bands: overlay-fit slivers only (< 0.01 m2 per panel), never a band in the slab
        assert p["slab_x_band_m2"] < 0.1
    gf = PART["GF"]
    solid = {h for _f, h, *_x in gf["double_solid_column"]}
    assert solid == {"347", "34A", "34D", "350", "356", "359"}      # = T-229 'billed through' columns, re-derived
    assert {h for _f, h, *_x in gf["carried_member_under_beam"]} == {"322"}
    assert gf["named_uncovered"]["GF-097"][1] == pytest.approx(0.74)     # CB5 span 2 band in no line
    assert abs(gf["end_residual_m2"]) < 0.3 and abs(PART["1F"]["end_residual_m2"]) < 0.1


def test_freelancer_cells_and_slip():
    assert FR == {"GF": 42.882875, "1F": 17.027, "2F": pytest.approx(6.056)}
    assert SUM["freelancer"]["f1_page_cell"] == pytest.approx(17.155)       # his own page sum keeps 1F B1 0.128
    missing = [m for m in MARKS if m["cls"] == "DRAWN_NOT_IN_HIS_SHEET_UNDER_THIS_MARK"]
    assert {(m["storey"], m["mark"]) for m in missing} == {("GF", "B27"), ("GF", "B28"), ("GF", "CA"),
                                                           ("1F", "B19"), ("1F", "B25"), ("1F", "B5")}
    assert sum(m["mine_low"] for m in missing) == pytest.approx(9.8825, abs=1e-3)


def test_committed_summary_matches_rebuild():
    committed = json.loads((HERE / "summary.json").read_text(encoding="utf-8"))
    assert committed["measured_m3"] == SUM["measured_m3"] and committed["runs"] == SUM["runs"]
    assert committed["conflict"] == list(SUM["conflict"]) and committed["held"] == list(SUM["held"])
