"""T-508: the development-villa inputs (research/agents_t508/t508_inputs.py, built only from the pinned merged T-501
table) validate under arch_v3056 with no private input: the 1F shaft stretches close (9.050 lm certain + 2.200 lm held
range, residual 0, level-aware), one riser per flight, landings 6.100 lm, HELD-FORM zigzag 23.300481 / sloped 17.009049
lm beside, the two earlier positions T-501 refused (MS2-LD.E to 1.200; E3 unsplit) refused here too."""
from __future__ import annotations

import copy
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t508"))

import t508_inputs as L  # noqa: E402
from engine.source import arch_v3056 as A  # noqa: E402

PID = "dev-villa"


def doc():
    return L.build(PID, dict(L.ROOM_EXPECT))


@pytest.fixture(scope="module")
def v():
    return A.load_inputs(doc(), PID)


def test_closure_and_risers(v):
    r = v["_retire"]
    assert (r["_certain"], r["_range"], r["_level"]) == (9.05, 2.2, 5.5)
    assert sum(1 for s in r["_segs"]) == 7
    assert v["_risers"] == {"MS1-L": 0.166667, "MS1-U": 0.166667, "MS2-L": 0.168, "MS2-U": 0.168, "D1": 0.175,
                            "RS-S": 0.160714, "E1": 0.17}
    assert v["_form"] is None


def test_hand_totals(v):
    ps = v["_pieces"]
    land = {}
    for p in ps:
        if p["kind"] == "LANDING" and p["cls"] == "WALL":
            land[p["element"]] = round(land.get(p["element"], 0) + p["_L"], 6)
    assert land == {"MS1-LD": 1.15, "MS2-LD": 3.7, "RS-LD": 1.25}            # 1.150 + 3.700 + 1.250 = 6.100
    wall = [p for p in ps if p["kind"] == "FLIGHT" and p["cls"] == "WALL"]
    assert len(wall) == 13
    assert round(sum(p["_zz"] for p in wall), 6) == 23.300481
    assert round(sum(p["_sl"] for p in wall), 6) == 17.009049
    assert sum(p["risers"] for p in wall) == 53
    assert sum(1 for p in ps if p["kind"] in ("FLIGHT", "STEP")) == 22      # 22 form pairs, 44 blank lines


def test_earlier_positions_refused():
    d = doc()
    for p in d["pieces"]:
        if p["pid"] == "MS2-LD.E":                         # T-410's 1.200 to the west lane's top nosing A97
            p["s1"], p["plan_lm"], p["value_lm"] = 1.2, 1.2, 1.2
    with pytest.raises(A.InputsError, match="two owners"):
        A.load_inputs(d, PID)


def test_pins_stop_an_edited_table(tmp_path, monkeypatch):
    f = tmp_path / "LINES_T501.csv"
    f.write_bytes(L.LINES.read_bytes().replace(b"0.733334", b"0.733335", 1))
    monkeypatch.setitem(L.PINS, f, L.PINS[L.LINES])
    monkeypatch.setattr(L, "LINES", f)
    with pytest.raises(SystemExit, match="sha256"):
        L.pieces()
