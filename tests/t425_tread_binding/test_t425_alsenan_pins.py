"""T-425 development-villa pins on the committed binding (research/agents_t425/BINDING_T425.json, built by
t425_alsenan.py from the private DXF by handle and the V3.0.36 candidate run; recomputed here without private input)."""

import csv
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / "research" / "agents_t425"
sys.path.insert(0, str(D))
import t425_alsenan as A  # noqa: E402


def lines():
    with open(D / "LINE_TABLE_T425.csv", newline="", encoding="utf-8") as f:
        return {r["line_id"]: r for r in csv.DictReader(f)}


def test_reproduces_from_committed_binding():
    p = subprocess.run([sys.executable, "-I", str(D / "t425_alsenan.py"), "--check"], capture_output=True, text=True)
    assert p.returncode == 0 and "REPRODUCED" in p.stdout, p.stdout + p.stderr


def test_candidate_identity():
    b = json.loads((D / "BINDING_T425.json").read_text())
    assert b["candidate"] == "ARCH_TAKEOFF_V3.0.36" and len(b["readings"]) == 14


def test_totals_hand_checked():
    t = json.loads((D / "BINDING_T425.json").read_text())["totals"]
    # before: MS1-L 2.415 + D1 1.035 + RS-C 4.094413 + RS-S 2.07 + 1.035 + RS-A 1.035 + MS2-L 3.795 + MS1-U 3.45
    #         + turn 1.495 + MS2-L (2F) 3.45 + MS2-U 3.45
    assert t["B7-02"]["valued_before"] == pytest.approx(27.324413, abs=1e-6)
    # after: MS1-L 9 x 0.345 + D1 1.035 + RS-S 10 x 0.345 + RS-A 4 x 0.345 + MS2-L 11 x 0.345 + MS1-U 11 x 0.345
    #        + MS2-U 10 x 0.345 = 3.105 + 1.035 + 3.45 + 1.38 + 3.795 + 3.795 + 3.45 = 20.01
    assert t["B7-02"]["valued_after"] == pytest.approx(20.01, abs=1e-6)
    assert t["B7-02"]["double_count_removed"] == pytest.approx(3.45, abs=1e-6)
    assert t["B7-02"]["held_by_name"] == pytest.approx(4.094413 + 1.495, abs=1e-6)
    # step lm after: (9 + 3 + 10 + 4 + 11 + 11 + 11) x 1.15 = 59 x 1.15 = 67.85
    assert t["B7-06"]["valued_after"] == pytest.approx(59 * 1.15, abs=1e-6)
    assert t["B7-06"]["double_count_removed"] == pytest.approx(11.5, abs=1e-6)


def test_double_count_and_rebinding_pins():
    L = lines()
    assert L["L-79beb9688604887c59c5"]["action"] == "DOUBLE_COUNT" and L["L-79beb9688604887c59c5"]["flight"] == "MS2-L"
    assert L["L-1e88ac0d4ba0b4e8a950"]["action"] == "DOUBLE_COUNT"
    assert L["L-65806b4d02d476603bc5"]["action"] == "KEEP"            # MS2-L on 1F carries the flight once
    # 1F F5: the winder turn seen from 1F (T-412 had it UNBOUND): HELD, never 0
    assert L["L-b4660de0ddd98ad0ffc2"]["flight"] == "MS1-T" and L["L-b4660de0ddd98ad0ffc2"]["action"] == "HELD"
    assert L["L-b4660de0ddd98ad0ffc2"]["after"] == ""
    assert L["L-fa534ec5f9dc14947899"]["action"] == "HELD"            # RS-C, Q-50 A cond
    assert float(L["L-151d92470a81dd1c450b"]["after"]) == pytest.approx(9 * 0.345)
    assert float(L["L-07f00d5b0c4e1924aaf5"]["beside"]) == pytest.approx(0.345)


def test_freelancer_trace():
    tr = {r["riser_m"]: r for r in A.freelancer_trace()}
    assert tr[0.15]["sum_per_storey"] == 63 and tr[0.16]["sum_per_storey"] == 61 and tr[0.17]["sum_per_storey"] == 57
    assert sum(A.DRAWN_RISERS_ST01.values()) == 56
