"""T-410 development-villa pins on the committed side table (research/agents_t410, built by t410_alsenan.py from the
private DXF by handle; the table is recomputed here from the committed ALSENAN_SIDES_T410.json, no private input)."""

import csv
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / "research" / "agents_t410"


def rows():
    with open(D / "SIDE_TABLE_T410.csv", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_reproduces_from_committed_sides():
    p = subprocess.run([sys.executable, "-I", str(D / "t410_alsenan.py"), "--check"], capture_output=True, text=True)
    assert p.returncode == 0 and "REPRODUCED" in p.stdout, p.stdout + p.stderr


def test_totals_hand_checked():
    s = json.loads((D / "summary.json").read_text())["totals_lm"]
    # hand: zigzag 2.650 + 3.900 + 3.594 + 5.316 + 1.600 + 2.050 + 3.125; sloped likewise; landings 1.15 + 0.65
    assert s["form_held_zigzag_lm"] == pytest.approx(22.235, abs=2e-5)
    assert s["form_held_sloped_lm"] == pytest.approx(16.181275, abs=2e-5)
    assert s["confirmed_horizontal_lm"] == pytest.approx(1.80, abs=1e-9)


def test_no_side_both_guarded_and_skirted_and_held_blank():
    for r in rows():
        if r["class"] == "OPEN":
            assert r["qty_lm"] == "0.000000" and r["railing_run"]
        if r["class"] in ("HELD", "UNKNOWN") or r["status"] == "HELD-FORM":
            assert r["qty_lm"] == ""
        if r["class"] in ("WALL", "HELD"):
            assert not r["railing_run"]
    keys = [(r["element"], r["side"]) for r in rows() if r["class"] == "OPEN"]
    wall = {(r["element"], r["side"]) for r in rows() if r["class"] in ("WALL", "HELD")}
    assert not wall & set(keys)


def test_every_st01_riser_has_one_wall_side():
    # ST-01 + D1: 10 + 5 winders + 12 + 12 + 1 closing + 12 + 4 = 56 risers; wall-side risers in flight stretches 50,
    # the 5 winders and the closing riser sit in the HELD corner / landing rows
    n = sum(int(r["risers_in"] or 0) for r in rows()
            if r["element"] in ("MS1-L", "MS1-U", "MS2-L", "MS2-U", "D1") and r["class"] in ("WALL", "HELD"))
    assert n == 10 + 12 + 12 + 12 + 4
