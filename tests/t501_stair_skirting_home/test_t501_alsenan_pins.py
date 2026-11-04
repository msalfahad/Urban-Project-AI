"""T-501 development-villa pins (committed tables; rebuilt here from the committed T-410 sides, no private input)."""
import csv
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / "research" / "agents_t501"
sys.path.insert(0, str(D))
import t501_alsenan as A  # noqa: E402
import t501_stair_skirting_home as K  # noqa: E402


def test_reproduces_without_private_input():
    p = subprocess.run([sys.executable, "-I", str(D / "t501_alsenan.py"), "--check"], capture_output=True, text=True)
    assert p.returncode == 0 and "REPRODUCED" in p.stdout, p.stdout + p.stderr


def test_shaft_binding_closes_on_the_t481_figures():
    tot = json.loads((D / "summary.json").read_text())["totals"]
    r = tot["retired_from_room_line"]
    assert r["certain_lm"] == pytest.approx(9.050) and r["held_range_lm"] == pytest.approx(2.200)
    assert r["residual_lm"] == pytest.approx(0.0, abs=1e-9)
    with open(D / "BINDING_T501.csv", newline="") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 7 and all(x["decision"].startswith("NOT_APPLICABLE") for x in rows)


def test_landing_and_form_totals_by_hand():
    tot = json.loads((D / "summary.json").read_text())["totals"]
    # MS1-LD.E 1.150 + MS2-LD (1.050 + 1.300 + 0.100 + 0.100 + 1.150 = 3.700) + RS-LD 0.650 + 0.600 = 6.100
    assert tot["landing_fin_skirting_confirmed_lm"] == pytest.approx(1.150 + 3.700 + 1.250)
    # T-410 form-held totals less MS1-U.E3b (0.300 + 0.166667 zigzag; 0.300 x hypot(3.3, 2.0) / 3.3 sloped)
    assert tot["flight_form_held"]["zigzag_lm"] == pytest.approx(23.767148 - 0.466667, abs=2e-6)
    assert tot["flight_form_held"]["sloped_lm"] == pytest.approx(17.359845 - 0.3 * (3.3 ** 2 + 2.0 ** 2) ** 0.5 / 3.3, abs=2e-6)
    assert tot["fin_skirting_certain_change_lm"] == pytest.approx(6.100 - 9.050)


def test_t410_positions_would_double_own():
    P = A.pieces()
    # (1) MS2-LD.E taken to A97 (1.200, the WEST lane's top nosing) overlaps MS2-U.E from 135B (1.150) at +7.684
    bad = [p for p in P if p.pid != "MS2-LD.E"] + [K.Piece("MS2-LD.E", "MS2-LD", A.E, K.LANDING, K.WALL, 0.0, 1.2,
                                                         7.684, 7.684)]
    with pytest.raises(K.RuleError, match="two owners"):
        K.check_one_owner(bad)
    # (2) MS1-U.E3 unsplit to s 4.450 overlaps the 1F room remainder from ABE (4.150) at +5.50
    e3a = next(p for p in P if p.pid == "MS1-U.E3a")
    whole = K.Piece("MS1-U.E3", "MS1-U", A.E, K.FLIGHT, K.WALL, 3.0, 4.45, e3a.level0, 5.50, 5, e3a.riser,
                    e3a.flight_run, e3a.flight_rise)
    bad = [p for p in P if p.pid not in ("MS1-U.E3a", "MS1-U.E3b")] + [whole]
    with pytest.raises(K.RuleError, match="two owners"):
        K.check_one_owner(bad)


def test_every_st01_wall_side_riser_once():
    with open(D / "LINES_T501.csv", newline="") as f:
        rows = list(csv.DictReader(f))
    st01 = [r for r in rows if r["element"] in ("MS1-L", "MS1-U", "MS2-L", "MS2-U", "D1")]
    # MS1-L 10 + MS1-U 12 + MS2-L 12 + MS2-U 12 + D1 4 = 50 flight risers on wall / held / conflict stretches
    assert sum(int(r["risers"]) for r in st01) == 50
    assert not any(r["status"] == "DRAWING-CONFIRMED" and r["family"].startswith("B7") for r in rows)
    assert all(r["value_lm"] == "" for r in rows if r["status"] not in ("DRAWING-CONFIRMED",))
