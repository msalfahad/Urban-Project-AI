"""T-108: the committed development-villa ledger reproduces from repository files, and its invariants hold.
(Not an accuracy claim: it pins the arithmetic of MASONRY_AREA_V1 on the T-143 / T-175 inputs.)"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research/agents_t108"


def test_ledger_reproduces_byte_for_byte():
    r = subprocess.run([sys.executable, "-I", str(HERE / "alsenan_t108.py"), "--check"], capture_output=True,
                       text=True, cwd=ROOT)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "CHECK PASS" in r.stdout


def test_invariants():
    s = json.loads((HERE / "summary.json").read_text(encoding="utf-8"))
    assert s["height_recomputation"]["max_abs_diff_vs_t143_m"] == 0.0     # Q-60 A heights from the member depths
    # r2: the only status change vs T-175 is the run that now carries P-1F-01 (its head is HELD, T-201)
    assert s["status_mismatch_vs_t175"] == ["1F-W14 + 1F-W15"]
    a = s["ALL"]
    assert a["walls"] == 74 and a["walls_with_net"] + a["walls_net_held"] == 74
    assert set(a["net_by_status"]) <= {"DRAWING-CONFIRMED", "ASSUMED — OWNER-APPROVED", "VERIFIED"}   # HELD never summed
    assert abs(a["net_by_status"]["DRAWING-CONFIRMED"]["m2"] - 252.817) < 0.01
    assert abs(a["net_by_status"]["ASSUMED — OWNER-APPROVED"]["m2"] - 84.595) < 0.01
    assert s["r2_length_source"]["rows_by_source"] == {"PHYSICAL_MODULE": 71, "HAND": 3}


def _rows():
    import csv
    return list(csv.DictReader(open(HERE / "T108_BY_WALL.csv", encoding="utf-8")))


def test_length_is_the_physical_module_run_never_the_hand_run():
    """r2 regression (Checker 07:13, gate h): every row with a MASONRY_CENTRELINE_V2 run takes that run's Q-69 B length;
    a hand length is a comparison column. Adverse: the 2F partition the Checker re-measured (3.000 m to the face, not
    3.10 m to the centreline) and every T-stem row T-125 settled ENGINE_RIGHT."""
    import csv
    v2 = {(r["floor"], r["run_id"]): float(r["physical_q69b_m"])
          for r in csv.DictReader(open(HERE / "T108_V2_RUN_LENGTHS.csv", encoding="utf-8"))}
    for r in _rows():
        if r["length_source"] == "PHYSICAL_MODULE":
            want = sum(v2[(r["floor"], x)] for x in r["v2_runs"].split())
            assert abs(float(r["physical_length_m"]) - want) < 0.0006, r["row_id"]
        else:
            assert r["v2_runs"] == "" and r["net_status"] == "HELD" and r["gross_m2"] == "", r["row_id"]
    w = {r["row_id"]: r for r in _rows()}
    assert w["2F-W08"]["physical_length_m"] == "3.000" and w["2F-W08"]["gross_m2"] == "11.400"
    assert w["2F-W08"]["net_m2"] == "9.640"
    for rid in ("GF-W19", "GF-W22", "GF-W23", "GF-W24", "1F-W11", "1F-W12", "1F-W24", "2F-W05", "2F-W08"):
        assert float(w[rid]["d_length_vs_hand_m"]) < 0, rid                 # the stem stops on the face: shorter


def test_v2_lengths_reproduce_the_merged_t125_totals():
    """The per-run input sums to the merged, verified T-125 architectural runs per floor and wall family."""
    import csv
    want = {(r["floor"], r["family"]): float(r["v2_arch_run_m"]) for r in
            csv.DictReader(open(ROOT / "research/agents_t125/V2_TOTALS_BY_FLOOR_THICKNESS.csv", encoding="utf-8"))
            if r["family"] != "GLAZED"}
    got = {}
    for r in csv.DictReader(open(HERE / "T108_V2_RUN_LENGTHS.csv", encoding="utf-8")):
        got[(r["floor"], r["family"])] = got.get((r["floor"], r["family"]), 0.0) + float(r["arch_run_m"])
    for k, v in want.items():
        assert abs(got.get(k, 0.0) - v) < 0.002, (k, got.get(k), v)


def test_no_double_count_of_one_physical_run():
    """Two hand rows on one V2 run (1F-W14 / 1F-W15 either side of P-1F-01) are one ledger row, never two lengths."""
    runs = [x for r in _rows() for x in (r["floor"] + ":" + y for y in r["v2_runs"].split())]
    assert len(runs) == len(set(runs))


def test_black_units_never_counted():
    import csv
    for r in csv.DictReader(open(HERE / "T108_BY_WALL.csv", encoding="utf-8")):
        if r["block_type"] == "BLACK":
            assert r["white_units_62.5x25"] == "" and r["units_status"] == "HELD"
        if r["net_status"] == "HELD":
            assert r["net_m2"] == "" and r["net_m3"] == ""
