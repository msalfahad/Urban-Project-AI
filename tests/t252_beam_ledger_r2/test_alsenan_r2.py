"""T-252 Alsenan CONC.BEAM ledger r2 from committed inputs only (merged T-241 ledger, the T-252 derived input from
Drive 'ST7757 dxf.dxf' sha 9f9d1179, the merged T-234 slab ledger, the freelancer cells). Pins the engineering results
(development villa; not an accuracy claim; nothing wired or released)."""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research" / "agents_t252"
sys.path.insert(0, str(HERE))
import t252_alsenan_check as C  # noqa: E402

SUM, ROWS, MARKS = C.build()
BY = {r["run"]: r for r in ROWS}


def test_two_one_face_ends_on_the_b27_east_face():
    ch = {c["run"]: c for c in SUM["oblique_end_checks"]}
    b4, cb4 = ch["BM-GF-017#BAND0018"], ch["BM-GF-021#BAND0021.1"]
    assert b4["result"] == cb4["result"] == "ONE_FACE_END"
    assert b4["carrier"] == cb4["carrier"] == "325"          # an S-BEAM line, not a layer-1 edge
    assert (b4["La_m"], b4["Lb_m"]) == pytest.approx((2.89066, 3.03827), abs=1e-5)
    assert (cb4["La_m"], cb4["Lb_m"]) == pytest.approx((2.37438, 2.64537), abs=1e-5)
    assert b4["delta_m3"] == pytest.approx(0.007376, abs=2e-6)
    assert cb4["delta_m3"] == pytest.approx(0.013548, abs=2e-6)
    assert BY["BM-GF-017#BAND0018.r2"]["m3"] == pytest.approx(0.296446, abs=2e-6)
    assert BY["BM-GF-021#BAND0021.1.r2"]["m3"] == pytest.approx(0.250988, abs=2e-6)


def test_void_ring_from_its_drawn_edges_counted_once():
    r = SUM["void_ring"]
    assert r["area_m2"] == pytest.approx(0.666406, abs=1e-6)
    assert r["polygon_check_m2"] == pytest.approx(r["area_m2"], abs=1e-5)     # exact arcs vs densified polygon
    assert sum(r["parts_m2"]) == pytest.approx(r["area_m2"], abs=1e-4)
    assert r["replaced_band_m2"] == pytest.approx(0.37428, abs=1e-5)
    assert r["missed_m2"] == pytest.approx(0.29213, abs=1e-5)
    assert r["slab_ledger_in_ring_m2"] == 0                                    # T-234 bills none of the ring
    assert r["sliver_residual_m2"] < 0.01 * r["area_m2"]
    assert r["m3"] == pytest.approx(0.499805, abs=1e-6)
    assert r["delta_measured_m3"] == pytest.approx(0.283605, abs=1e-6)
    ring = BY["BM-GF-050.r2#RING-B7"]
    assert ring["status"] == "CALCULATED" and ring["depth_m"] == 0.75 and ring["b_drawn_m"] == 0.20
    for x in C.RING_R1:
        assert BY[x]["status"] == "SUPERSEDED_R2" and BY[x]["superseded_by"] == "BM-GF-050.r2#RING-B7"


def test_line_totals_r2():
    assert SUM["runs_r1"] == 140 and SUM["runs_live"] == 137
    assert SUM["measured_m3_r1"] == pytest.approx(66.016058, abs=1e-6)
    assert SUM["measured_m3"] == pytest.approx(66.320598, abs=1e-6)
    assert SUM["by_storey"]["GF"]["measured_m3"] == pytest.approx(39.331525, abs=1e-6)
    assert SUM["by_storey"]["1F"]["measured_m3"] == pytest.approx(22.690573, abs=1e-6)   # untouched storeys
    assert SUM["by_storey"]["2F"]["measured_m3"] == pytest.approx(4.2985, abs=1e-6)
    assert abs(SUM["residual_m3"]) < 2e-5        # r1 rounded m3 to 4 dp; the causes explain the rest
    assert SUM["conflict"] == pytest.approx((5.144829, 6.11101), abs=1e-6)              # unchanged
    assert SUM["held_r1"] == pytest.approx((4.1627, 8.6732), abs=1e-6)
    assert SUM["held"] == pytest.approx((4.1277, 8.5682), abs=1e-6)                     # BM-GF-060 left HELD
    assert set(SUM["held_no_value"]) == {"BM-GF-061", "BM-1F-037", "BM-1F-038", "BM-2F-019#2F-031"}


def test_r1_rows_carried_unchanged_and_r1_file_untouched():
    r1 = list(csv.DictReader(open(ROOT / "research/agents_t241/LEDGER_T241.csv", encoding="utf-8")))
    assert len(r1) == 140
    total = sum(float(r["m3"]) for r in r1 if r["status"] == "CALCULATED")
    assert total == pytest.approx(66.016058, abs=1e-6)
    sup = set(SUM["superseded"])
    assert sup == {"BM-GF-017#BAND0018", "BM-GF-021#BAND0021.1"} | set(C.RING_R1)
    for r in r1:
        if r["run"] in sup:
            continue
        assert BY[r["run"]]["status"] == r["status"]
        assert (BY[r["run"]]["m3"] or 0.0) == pytest.approx(float(r["m3"] or 0.0), abs=1e-9)


def test_held_never_zero_in_r2():
    for r in ROWS:
        if r["status"] == "HELD":
            assert r["m3"] is None


def test_by_mark_moves_only_the_corrected_marks():
    moved = {(m["storey"], m["mark"]): m for m in SUM["marks_moved"]}
    assert set(moved) == {("GF", "B4"), ("GF", "CB4"), ("GF", "B7")}
    assert moved[("GF", "B7")]["mine_low"] == pytest.approx(1.2175, abs=1e-4)
    assert moved[("GF", "B7")]["his_m3"] == pytest.approx(1.572, abs=1e-4)


def test_committed_outputs_match_a_rerun():
    s = json.load(open(HERE / "summary.json", encoding="utf-8"))
    assert s["measured_m3"] == SUM["measured_m3"] and s["held"] == list(SUM["held"])
    rows = list(csv.DictReader(open(HERE / "LEDGER_T252.csv", encoding="utf-8")))
    assert [r["run"] for r in rows] == [r["run"] for r in ROWS]
