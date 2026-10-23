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
    assert s["gross_vs_t143"]["max_abs_diff_m2"] <= 0.01                   # only the 0.01 m rounding of piece lengths
    assert s["net_vs_t175"]["max_abs_diff_m2"] <= 0.01
    assert s["status_mismatch_vs_t175"] == []
    a = s["ALL"]
    assert a["walls"] == 75 and a["walls_with_net"] + a["walls_net_held"] == 75
    assert set(a["net_by_status"]) <= {"DRAWING-CONFIRMED", "ASSUMED — OWNER-APPROVED", "VERIFIED"}   # HELD never summed
    assert abs(a["net_by_status"]["DRAWING-CONFIRMED"]["m2"] - 271.594) < 0.01
    assert abs(a["net_by_status"]["ASSUMED — OWNER-APPROVED"]["m2"] - 86.469) < 0.01


def test_black_units_never_counted():
    import csv
    for r in csv.DictReader(open(HERE / "T108_BY_WALL.csv", encoding="utf-8")):
        if r["block_type"] == "BLACK":
            assert r["white_units_62.5x25"] == "" and r["units_status"] == "HELD"
        if r["net_status"] == "HELD":
            assert r["net_m2"] == "" and r["net_m3"] == ""
