"""T-434 development-villa pins on the committed turn reading (research/agents_t434/ALSENAN_TURN_T434.json, built by
t434_alsenan.py from the private DXFs by handle and the section raster; recomputed here without private input)."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / "research" / "agents_t434"


def data():
    return json.loads((D / "ALSENAN_TURN_T434.json").read_text())


def test_reproduces_from_committed_json():
    p = subprocess.run([sys.executable, "-I", str(D / "t434_alsenan.py"), "--check"], capture_output=True, text=True)
    assert p.returncode == 0 and "REPRODUCED" in p.stdout, p.stdout + p.stderr


def test_governing_count_and_rejections():
    g = data()["result"]["governing"]
    assert g["governing"] == "SECTION_A_A" and g["turn_risers"] == 5
    t = {r["reading"]: r for r in g["table"]}
    # hand: 2.50 / 15 = 0.166667; 2.50 / 14 = 0.178571; 2.50 / 16 = 0.15625
    assert t["SECTION_A_A"]["riser_m"] == pytest.approx(0.166667, abs=1e-6)
    assert t["ARCH_GF_PLAN"]["riser_m"] == pytest.approx(0.178571, abs=1e-6)
    assert t["ARCH_GF_PLAN"]["riser_check"] == "FAIL"
    assert t["ST_P4"]["riser_m"] == pytest.approx(0.15625) and t["ST_P4"]["riser_check"] == "PASS"
    assert set(t["ST_P4"]["rejected_because"]) == {"level_check", "foot_check"}
    assert t["SECTION_A_A"]["level_miss_m"] <= 0.003


def test_section_levels_and_cad_facts():
    d = data()
    lv = d["section"]["dashed_tread_levels_m"]
    # hand: 1.00 + k / 6 for k = 10 .. 13 = 2.6667 / 2.8333 / 3.0000 / 3.1667
    assert len(lv) == 4 and all(abs(a - (1.0 + k / 6)) <= 0.003 for a, k in zip(lv, range(10, 14)))
    c = d["cad"]
    assert c["arch_ms1l_front_s_m"][0] == pytest.approx(-2.7) and c["st_p4"]["face_foot_rel_486_m"] == pytest.approx(-3.3)
    # radial fronts by Pythagoras on the drawn ends: hypot(1.150, 0.5115) = 1.258652; hypot(1.150, 1.150) = 1.626346
    assert c["radial_fronts_m"] == {"4A2": pytest.approx(1.258652), "49E": pytest.approx(1.626346),
                                    "4A0": pytest.approx(1.258652)}
    assert c["st_p4"]["radials_m"]["2F4"] == pytest.approx(1.626346)


def test_turn_quantities():
    q = data()["result"]["turn"]
    assert q["nosing_pieces"] == 5 and q["winder_tread_pieces"] == 5
    assert q["landing_edge"]["status"] == "DRAWING-CONFIRMED" and q["landing_edge"]["lm"] == pytest.approx(1.15)
    assert q["winder_fronts"]["status"] == "HELD" and q["winder_fronts"]["lm"] is None
    assert q["winder_fronts"]["beside_lm"] == pytest.approx(1.258652 * 2 + 1.626346, abs=2e-6)
    # region front 485 .. front 2C6: 1.150 x 1.200 + 0.100 x 1.150 = 1.380 + 0.115 = 1.495
    assert q["tread_marble"]["status"] == "HELD" and q["tread_marble"]["m2"] is None
    assert q["tread_marble"]["beside_m2"] == pytest.approx(1.495, abs=1e-6)


def test_freelancer_not_a_drawn_reading():
    f = data()["result"]["freelancer"]
    assert f["reach_of_drawn_readings"] == [53, 59] and f["freelancer_pieces"] == 63
    assert f["verdict"] == "NOT_A_DRAWN_READING" and f["drawn_risers"] == 56
