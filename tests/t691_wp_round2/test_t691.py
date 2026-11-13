"""T-691 waterproofing round 2 (R-T691-1 .. -3): synthetic villa W691 by hand (normal + adverse) and the development
villa pinned to the committed outputs.

Villa W691 (synthetic, not the development villa), by hand:
  roof face inside the parapet / wall faces 12.00 x 8.00 = 96.000000 m2; one round skylight r 1.50 m
  pi r^2 = 7.068583 m2 -> membrane 88.931417 m2 (high, wall-face basis)
  a 0.05 x 3.00 band of unprinted meaning at a wall foot = 0.150 m2 -> low 88.781417 m2 (OPEN_BOUND)
  1 mm sagitta -> 87 chords (n = ceil(2 pi / 2 acos(1 - s / r))); the inscribed polygon under-deducts
  pi 2.25 - 87/2 x 2.25 x sin(2 pi / 87) = 0.006143 m2 (<= 4/3 pi r s = 0.006283): a released 88.937560 (polygon
  hole) sits 0.006143 above its own band
  wet rooms: bath FD 2 + W.C. 1 -> 2 .. 3 pcs; wash FD 1, no W.C. -> 1 (MEASURED); no drain printed -> HELD (never 0)
"""
import json
import math
import subprocess
import sys
from decimal import Decimal
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t691"))
import t691_rules as R  # noqa: E402

OUT = ROOT / "research" / "agents_t691" / "out" / "T691_WP_ROUND2.json"


def test_true_circle_deduction_normal():
    b = R.roof_band(96.0, [1.5])
    assert b["high_m2"] == Decimal("88.931417") and b["status"] == "MEASURED"


def test_open_band_is_a_range_not_a_choice():
    b = R.roof_band(96.0, [1.5], open_band_m2=0.15)
    assert (b["low_m2"], b["high_m2"], b["status"]) == (Decimal("88.781417"), Decimal("88.931417"), "OPEN_BOUND")


def test_chord_polygon_overstates_net_and_is_named():
    n = R.chords_for_sagitta(1.5, 0.001)
    assert n == 87
    res = R.chord_residual(1.5, n)
    assert round(res["area_m2"], 6) == 0.006143                   # pi 2.25 - 87/2 2.25 sin(2 pi/87), by hand
    assert res["area_m2"] <= 4 / 3 * math.pi * 1.5 * 0.001        # bound: real chord sagitta <= 1 mm
    assert res["ring_m"] > 0                                       # chords are shorter than the arc
    released = round(96.0 - R.circle_inscribed(1.5, n)["area_m2"], 6)
    c = R.check_inside_band(released, "88.781417", "88.931417", [("polygon hole", res["area_m2"])])
    assert c["inside"] is False and c["residual_within_rounding"] is True
    assert Decimal(c["excess"]) == Decimal("0.006143")


def test_released_inside_band_passes():
    assert R.check_inside_band("88.9", "88.781417", "88.931417", [])["inside"] is True


def test_adverse_hatch_on_parapet_line_adds_nothing():
    b = R.roof_band(96.0, [1.5], hatch_m2=88.931417, hatch_on_face_line=True)
    assert b["high_m2"] == Decimal("88.931417")
    assert any("HATCH_ON_FACE_LINE" in f for f in b["flags"])


def test_adverse_hatch_larger_than_face_is_flagged_not_used():
    b = R.roof_band(96.0, [1.5], hatch_m2=90.0)
    assert b["high_m2"] == Decimal("88.931417")
    assert any("HATCH_EXCEEDS_FACE" in f for f in b["flags"])


def test_adverse_units_and_missing():
    with pytest.raises(R.RuleError):
        R.circle_true(1500.0)                                       # mm read as m
    with pytest.raises(R.RuleError):
        R.membrane_net(None, [1.5])                                 # outline not measured: HELD, never 0
    with pytest.raises(R.RuleError):
        R.check_inside_band(None, "1", "2", [])                     # HELD is not a released 0
    with pytest.raises(R.RuleError):
        R.roof_band(96.0, [1.5], open_band_m2=-0.1)


def test_mirror_and_rotation_do_not_move_the_area():
    # the true-circle rule uses r only; a mirrored / rotated face of the same outline area gives the same membrane
    assert R.membrane_net(96.0, [1.5]) == R.membrane_net(8.0 * 12.0, [1.5])


def test_penetrations_normal_and_bound():
    assert R.penetration_bound({"drainage_read": True, "fd": 2, "wc": 1})["low"] == 2
    b = R.penetration_bound({"drainage_read": True, "fd": 2, "wc": 1})
    assert (b["low"], b["high"], b["status"]) == (2, 3, "OPEN_BOUND")
    m = R.penetration_bound({"drainage_read": True, "fd": 1, "wc": 0})
    assert (m["low"], m["high"], m["status"]) == (1, 1, "MEASURED")


def test_adverse_missing_drain_count_stays_at_least_never_zero():
    for room in ({"drainage_read": False, "fd": 1, "wc": 1}, {"drainage_read": True, "fd": None, "wc": 1},
                 {"drainage_read": True, "fd": 0, "wc": 0}):
        b = R.penetration_bound(room)
        assert b["status"] == "HELD" and b["low"] is None and b["low"] != 0
    u = R.penetration_bound({"drainage_read": True, "fd": 2, "wc": 1, "mapped": False, "pair_min": 1})
    assert (u["status"], u["low"], u["high"]) == ("OPEN_BOUND", 1, None)
    with pytest.raises(R.RuleError):
        R.penetration_bound({"drainage_read": True, "fd": -1, "wc": 0})


def test_twin_mapping_by_geometry():
    m = R.map_twin_cells({"cell A": 0.80, "cell B": 1.10}, {"room-1": 0.81, "room-2": 1.09})
    assert m == {"cell A": "room-1", "cell B": "room-2"}
    with pytest.raises(R.RuleError):
        R.map_twin_cells({"cell A": 0.95, "cell B": 0.951}, {"room-1": 0.95, "room-2": 0.951})


def test_development_villa_outputs_pinned():
    d = json.loads(OUT.read_text(encoding="utf-8"))
    roof = d["roof_F_V685_1"]
    assert roof["released_vs_band"]["inside"] is False and roof["released_vs_band"]["residual_within_rounding"]
    assert roof["dome"]["chords_engine"] == 105
    assert roof["corrected"]["value_m2"] == 115.81396
    p = d["penetrations"]
    assert (p["low_pcs"], p["high_pcs"]) == (19, 31) and len(p["rows"]) == 18
    assert all(r["after_low"] >= 1 for r in p["rows"])
    assert p["twin_map"]["EAST cell (C22 / C1C / C26 / C25)"] == "1F-R8BDA49"
    r = subprocess.run([sys.executable, "-I", str(ROOT / "research" / "agents_t691" / "t691_alsenan.py"), "--check"],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
