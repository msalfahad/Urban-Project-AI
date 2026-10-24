"""T-219 development-villa ledger (Alsenan; not an accuracy claim) from committed inputs only: the T-233 footing input
(Drive 'ST7757 dxf.dxf' sha 9f9d1179, Checker-verified outlines) and ALSENAN_T219_INPUT.json. Re-runs without writing
and pins the engineering results."""
from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research" / "agents_t219"
sys.path.insert(0, str(HERE))
import t219_alsenan_check as C  # noqa: E402

ROWS, SUM = C.main(write=False)
TOT = SUM["totals"]
TXT = (HERE / "ALSENAN_T219_INPUT.json").read_text(encoding="utf-8")


def test_inputs_values_only():
    assert SUM["sources"]["t233_input_sha_prefix"] == "9f9d1179"
    assert not re.search(r"\d{5,}\.\d", TXT)                     # no sheet coordinates


def test_population_every_outline_once_lift_apart():
    assert SUM["outlines"] == 25                                 # 26 outlines less FF (own detail, lift pit)
    els = [r["element"] for r in ROWS if r["item"] == "WP.FOOTING_MEMBRANE"]
    assert len(els) == len(set(els)) == 25
    assert "FTG:1B2B" not in els


def test_membrane_under_footings_by_type():
    bt = SUM["membrane_by_type"]
    assert bt["FN"] == [4, pytest.approx(3.86)]                  # 3 x 1.00 + 0.86 (180C clipped where F9 lies)
    assert bt["F9"] == [1, pytest.approx(9.18)] and bt["F12"] == [1, pytest.approx(14.08)]
    m = TOT["WP.FOOTING_MEMBRANE|m2"]
    assert m["measured"] == pytest.approx(109.85) and m["measured_n"] == 24
    assert (m["held_low"], m["held_high"]) == (pytest.approx(4.55), pytest.approx(4.64))   # F10 + F outline (Q-31 C)


def test_protection_screed():
    assert TOT["SCREED.FOOTING_PROTECTION|m2"]["measured"] == pytest.approx(109.85)
    assert TOT["SCREED.FOOTING_PROTECTION|m3"]["measured"] == pytest.approx(5.4925)        # 109.85 x 0.05
    s = TOT["SCREED.FOOTING_PROTECTION|m3"]
    assert (s["held_low"], s["held_high"]) == (pytest.approx(0.2275), pytest.approx(0.232))


def test_consistent_with_the_verified_blinding_plan():
    # T-233 (Checker-verified): 25 measured outlines grown 0.10 sum to 151.990 m2 = sum(A) + 0.10 x sum(P) + 25 x 0.04
    sides = {r["element"]: r for r in ROWS if r["item"] == "WP.FOOTING_SIDES" and r["element"] != "FTG:1B1B"}
    assert len(sides) == 24
    sum_p = sum(float(re.search(r"perimeter ([\d.]+)", r["basis"]).group(1)) for r in sides.values())
    assert sum_p == pytest.approx(186.2)
    assert 109.85 + 20.70 + 0.10 * (sum_p + 18.2) + 25 * 0.04 == pytest.approx(151.99)


def test_sides_held_with_both_detail_readings():
    s = TOT["WP.FOOTING_SIDES|m2"]
    assert s["measured_n"] == 0 and s["held_open"] is True        # 1B1B has no depth: the line's bound stays open
    r = SUM["side_readings_sum_m2"]
    # single: 82.23 gross - FN/F9 0.45 - SB1 0.35 - SB2 2 x 1.0190 x 0.50 - SB3 0.5341 x (0.40 + 0.30)
    assert r["single:LIQUID_2_LAYERS"] == pytest.approx(80.0372, abs=1e-3)
    assert r["double:SHEET_MEMBRANE"] == pytest.approx(93.0338, abs=1e-3)


def test_lift_pit():
    assert TOT["WP.LIFT_PIT_MEMBRANE_FIXED|m2"]["measured"] == pytest.approx(47.43)   # 20.70 + 18.20 x 0.60 + 15.81
    assert TOT["WP.LIFT_PIT_BOARD_FIXED|m2"]["measured"] == pytest.approx(26.73)
    assert TOT["SCREED.LIFT_PIT_BASE|m3"]["measured"] == pytest.approx(1.035)
    w = [r for r in ROWS if r["item"] == "WP.LIFT_PIT_MEMBRANE_WALLS"][0]
    assert w["status"] == "HELD" and w["qty"] is None and w["readings"]["per_m_height"] == pytest.approx(8.90)


def test_procurement_held_everywhere():
    p = TOT["WP.FOOTING_MEMBRANE_PROCUREMENT|rolls"]
    assert p["measured_n"] == 0 and len(p["held"]) == 25


def test_freelancer_has_no_row():
    assert SUM["freelancer"]["rows"] == []


def test_committed_ledger_and_summary_current():
    led = list(csv.DictReader((HERE / "LEDGER_T219.csv").open(encoding="utf-8")))
    assert len(led) == len(ROWS)
    for a, b in zip(led, ROWS):
        assert a["element"] == b["element"] and a["item"] == b["item"] and a["status"] == b["status"]
        assert (a["qty"] or None) == (None if b["qty"] is None else str(b["qty"]))
    committed = json.loads((HERE / "summary.json").read_text(encoding="utf-8"))
    assert json.dumps(committed, sort_keys=True) == json.dumps(json.loads(json.dumps(SUM)), sort_keys=True)
